"""team-15 -- regime-allocated ensemble of carry, trend and short-horizon reversal.

Three cross-sectional sleeves on Binance USD-M perpetuals, combined by a soft state variable
built from the cross-sectional level of funding.  The allocator scores each sleeve on its own
reconstructed, past-only, turnover-charged return path, so a sleeve that cannot pay for its own
trading is pushed to its shrinkage floor rather than being carried by gross performance.

Everything is recomputed from the rows streamed in ``DecisionContext``; no state survives a call,
no absolute date, symbol identity or price level is referenced, and every transform is a smooth
function of cross-sectional ranks.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# --- history retained per decision -------------------------------------------------------------
MAX_HISTORY = 720          # bars (8h) -> 240 days; bounds the per-decision cost of the rebuild
MIN_PANEL_ROWS = 30        # below this nothing is tradable

# --- sleeve primitives (Phase-S surface, Block A) ----------------------------------------------
H_CARRY = 21               # bars, mean funding (7 days)
H_TREND = 45               # bars, trailing return (15 days)
H_REV = 3                  # bars, trailing return (1 day)

# --- turnover governor -------------------------------------------------------------------------
H_TARGET = 15              # bars; every sleeve is smoothed toward this common effective horizon

# --- regime definition (Block B) ---------------------------------------------------------------
W_REGIME = 180             # bars, trailing window for the state variable (60 days)
REGIME_MIN = 90            # observations required before the state is anything but neutral
STATE_SLOPE = 2.0          # logistic slope in inter-quartile units; ~0.73 membership at Q3

# --- allocation map (Block C) ------------------------------------------------------------------
ALLOC_MIN_OBS = 200        # bars of reconstructed sleeve history before the allocator is trusted
LAMBDA_EW = 0.50           # shrinkage toward equal weight
COST_PER_TURNOVER = 0.0015  # 15 bps per unit of |dw|, ~2x the venue's 1x charge (see RATIONALE)

# --- book construction (Block D) ---------------------------------------------------------------
MIN_NAMES = 5              # cross-section below this is not a portfolio
PER_SYMBOL_CAP = 0.10
TARGET_GROSS = 1.0
MAX_ABS_NET = 0.20
N_SLEEVES = 3


def _epoch_ns(values) -> np.ndarray:
    """Timestamps -> UTC nanoseconds, so bars and funding align on one integer key."""
    idx = pd.DatetimeIndex(pd.to_datetime(np.asarray(values), utc=True, errors="coerce"))
    return np.asarray(idx.tz_localize(None), dtype="datetime64[ns]").astype("int64")


def _bar_panel(bars, column: str, max_rows: int) -> pd.DataFrame:
    """Per-symbol frames -> one wide panel keyed on ``open_time`` (never the positional index)."""
    columns = {}
    for symbol in bars:
        frame = bars[symbol]
        if frame is None or len(frame) == 0:
            continue
        if column not in frame.columns or "open_time" not in frame.columns:
            continue
        tail = frame.iloc[-max_rows:]
        key = _epoch_ns(tail["open_time"].to_numpy())
        values = pd.to_numeric(tail[column], errors="coerce").to_numpy(dtype=float)
        series = pd.Series(values, index=pd.Index(key))
        series = series[~series.index.duplicated(keep="last")]
        columns[symbol] = series
    if not columns:
        return pd.DataFrame()
    return pd.concat(columns, axis=1).sort_index()


def _funding_panel(funding, index: pd.Index, symbols) -> pd.DataFrame:
    """Funding rows -> panel on the bar clock.  Column is ``funding_rate``, not the raw Binance name."""
    blank = pd.DataFrame(np.nan, index=index, columns=list(symbols))
    if funding is None or len(funding) == 0:
        return blank
    if not {"symbol", "funding_rate", "funding_time"}.issubset(set(funding.columns)):
        return blank
    rows = funding.loc[:, ["symbol", "funding_rate", "funding_time"]]
    tidy = pd.DataFrame(
        {
            "t": _epoch_ns(rows["funding_time"].to_numpy()),
            "symbol": rows["symbol"].to_numpy(),
            "rate": pd.to_numeric(rows["funding_rate"], errors="coerce").to_numpy(dtype=float),
        }
    ).dropna()
    tidy = tidy[tidy["symbol"].isin(list(symbols))]
    if len(tidy) == 0:
        return blank
    wide = tidy.pivot_table(index="t", columns="symbol", values="rate", aggfunc="last").sort_index()
    wide = wide.reindex(wide.index.union(index)).sort_index().ffill(limit=3).reindex(index)
    return wide.reindex(columns=list(symbols))


def _row_rank_pct(values: np.ndarray) -> np.ndarray:
    """Average-rank percentile within each row over finite entries; NaN elsewhere.

    Ties take the average rank, so the map is invariant to the order of the columns -- a plain
    argsort would break symbol pseudonymisation whenever two names share a funding rate, which at
    the 0.01% baseline happens constantly.
    """
    finite = np.isfinite(values)
    count = finite.sum(axis=1)
    n_cols = values.shape[1]
    padded = np.where(finite, values, np.inf)
    order = np.argsort(padded, axis=1, kind="mergesort")
    ordered = np.take_along_axis(padded, order, axis=1)

    starts = np.ones(values.shape, dtype=bool)
    starts[:, 1:] = ordered[:, 1:] != ordered[:, :-1]
    ends = np.ones(values.shape, dtype=bool)
    ends[:, :-1] = starts[:, 1:]

    positions = np.broadcast_to(np.arange(n_cols), values.shape)
    first = np.maximum.accumulate(np.where(starts, positions, -1), axis=1)
    last = np.minimum.accumulate(np.where(ends, positions, n_cols)[:, ::-1], axis=1)[:, ::-1]

    ranks = np.empty(values.shape, dtype=float)
    np.put_along_axis(ranks, order, (first + last) / 2.0 + 1.0, axis=1)
    ranks = np.where(finite, ranks, np.nan)
    return ranks / np.where(count > 0, count, 1)[:, None]


def _rank_weights(scores: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional scores -> demeaned unit-gross weights, one row per bar.

    A linear map of the rank percentile rather than a top-k selection: every eligible name carries
    weight, which keeps effective breadth high and makes the book move continuously as ranks shuffle
    instead of jumping whenever a name crosses a selection boundary.
    """
    raw = scores.to_numpy(dtype=float)
    if raw.size == 0:
        return pd.DataFrame(raw, index=scores.index, columns=scores.columns)
    tilt = 2.0 * _row_rank_pct(raw) - 1.0
    finite = np.isfinite(tilt)
    tilt = np.where(finite, tilt, 0.0)
    count = finite.sum(axis=1).astype(float)
    tilt = (tilt - (tilt.sum(axis=1) / np.where(count > 0, count, 1.0))[:, None]) * finite
    gross = np.abs(tilt).sum(axis=1)
    tilt = tilt / np.where(gross > 0.0, gross, 1.0)[:, None]
    tilt[count < MIN_NAMES] = 0.0
    return pd.DataFrame(tilt, index=scores.index, columns=scores.columns)


def _smoothing_window(horizon: int) -> int:
    """Bars of target averaging that bring a sleeve of this signal horizon to ``H_TARGET``."""
    return int(max(3, H_TARGET - horizon + 1))


def _sleeve_net_returns(
    weights: pd.DataFrame, forward_price: np.ndarray, forward_funding: np.ndarray
) -> np.ndarray:
    """Past-only return path of a sleeve, charged for the turnover it actually generates."""
    held = weights.to_numpy(dtype=float)
    gross = (held * forward_price).sum(axis=1) - (held * forward_funding).sum(axis=1)
    turnover = np.full(held.shape[0], np.nan)
    if held.shape[0] > 1:
        turnover[1:] = np.abs(np.diff(held, axis=0)).sum(axis=1)
    return gross - COST_PER_TURNOVER * turnover


def _state_allocation(information_ratios: np.ndarray) -> np.ndarray:
    """Conditional sleeve IRs -> allocation, shrunk toward equal weight by ``LAMBDA_EW``."""
    scores = np.where(np.isfinite(information_ratios), information_ratios, 0.0)
    positive = np.clip(scores, 0.0, None)
    total = positive.sum()
    n = float(scores.size)
    base = positive / total if total > 0.0 else np.full(scores.size, 1.0 / n)
    return LAMBDA_EW / n + (1.0 - LAMBDA_EW) * base


def _finalise(raw: pd.Series, eligible) -> dict:
    """Restrict to tradable names and enforce gross, net and per-symbol limits."""
    names = [s for s in eligible if s in raw.index]
    if len(names) < MIN_NAMES:
        return {}
    book = raw.reindex(names).to_numpy(dtype=float)
    book = np.where(np.isfinite(book), book, 0.0)
    if np.abs(book).sum() <= 0.0:
        return {}
    for _ in range(3):
        book = book - book.mean()
        gross = np.abs(book).sum()
        if gross <= 0.0:
            return {}
        book = np.clip(book * (TARGET_GROSS / gross), -PER_SYMBOL_CAP, PER_SYMBOL_CAP)
    book = np.clip(book - book.mean(), -PER_SYMBOL_CAP, PER_SYMBOL_CAP)
    if abs(book.sum()) > MAX_ABS_NET:
        book = np.clip(book - book.mean(), -PER_SYMBOL_CAP, PER_SYMBOL_CAP)
    gross = np.abs(book).sum()
    if gross > TARGET_GROSS:
        book = book * (TARGET_GROSS / gross)
    if not np.isfinite(book).all():
        return {}
    return {name: float(weight) for name, weight in zip(names, book)}


class RegimeAllocatedEnsemble:
    """Carry, trend and reversal, allocated by a soft funding-crowding state."""

    def target_weights(self, context, *, seed):
        bars = context.bars
        eligible = list(context.eligible_symbols)
        if not bars or len(eligible) < MIN_NAMES:
            return {}

        close = _bar_panel(bars, "close", MAX_HISTORY)
        if close.empty or len(close.index) < MIN_PANEL_ROWS:
            return {}
        close = close.where(close > 0.0)
        alive = close.notna()

        funding = _funding_panel(context.funding, close.index, close.columns)

        # --- sleeve signals -------------------------------------------------------------------
        log_price = np.log(close)
        smoothed_funding = funding.rolling(H_CARRY, min_periods=5).mean()
        carry_signal = (-smoothed_funding).where(alive)
        trend_signal = log_price.diff(H_TREND).where(alive)
        reversal_signal = (-log_price.diff(H_REV)).where(alive)

        sleeves = []
        for signal, horizon in (
            (carry_signal, H_CARRY),
            (trend_signal, H_TREND),
            (reversal_signal, H_REV),
        ):
            window = _smoothing_window(horizon)
            # Averaging the target vector, not renormalising it: a sleeve whose direction does not
            # persist shrinks in magnitude, which is the correct price for a signal that would
            # otherwise spend the whole cost budget.
            sleeves.append(_rank_weights(signal).rolling(window, min_periods=1).mean())

        # --- realised, past-only forward returns ------------------------------------------------
        forward_price_raw = log_price.diff().shift(-1).to_numpy(dtype=float)
        forward_price = np.where(np.isfinite(forward_price_raw), forward_price_raw, 0.0)
        forward_funding = funding.shift(-1).to_numpy(dtype=float)
        forward_funding = np.where(np.isfinite(forward_funding), forward_funding, 0.0)

        # --- soft state: where the cross-sectional level of funding sits in its own history -----
        cross_funding = funding.mean(axis=1).rolling(H_CARRY, min_periods=5).mean()
        trailing = cross_funding.rolling(W_REGIME, min_periods=REGIME_MIN)
        median = trailing.median()
        spread = trailing.quantile(0.75) - trailing.quantile(0.25)
        standardised = (cross_funding - median) / spread.where(spread > 0.0)
        crowded = 1.0 / (1.0 + np.exp(-STATE_SLOPE * standardised.clip(-4.0, 4.0)))
        crowded = crowded.fillna(0.5).to_numpy(dtype=float)

        # --- state-conditional allocation -------------------------------------------------------
        nets = np.column_stack(
            [_sleeve_net_returns(w, forward_price, forward_funding) for w in sleeves]
        )
        coverage = np.isfinite(forward_price_raw).sum(axis=1)
        # A sleeve that is not yet computable returns a flat book, whose net return is a real 0.0
        # rather than a NaN.  Scoring those rows would drag that sleeve's conditional mean toward
        # zero for as long as its lookback takes to fill, so require all three to be carrying risk.
        carrying = np.column_stack(
            [np.abs(w.to_numpy(dtype=float)).sum(axis=1) > 0.0 for w in sleeves]
        ).all(axis=1)
        usable = np.isfinite(nets).all(axis=1) & (coverage >= MIN_NAMES) & carrying

        equal = np.full(N_SLEEVES, 1.0 / N_SLEEVES)
        if int(usable.sum()) >= ALLOC_MIN_OBS:
            sample = nets[usable]
            weight_hi = crowded[usable]
            weight_lo = 1.0 - weight_hi
            deviation = sample.std(axis=0)
            deviation = np.where(deviation > 0.0, deviation, np.nan)
            mean_hi = (sample * weight_hi[:, None]).sum(axis=0) / max(weight_hi.sum(), 1e-9)
            mean_lo = (sample * weight_lo[:, None]).sum(axis=0) / max(weight_lo.sum(), 1e-9)
            alloc_hi = _state_allocation(mean_hi / deviation)
            alloc_lo = _state_allocation(mean_lo / deviation)
        else:
            alloc_hi = equal
            alloc_lo = equal

        now = float(crowded[-1])
        allocation = now * alloc_hi + (1.0 - now) * alloc_lo

        book = sleeves[0].iloc[-1] * allocation[0]
        for share, sleeve in zip(allocation[1:], sleeves[1:]):
            book = book + sleeve.iloc[-1] * share
        return _finalise(book, eligible)


def build_strategy():
    return RegimeAllocatedEnsemble()
