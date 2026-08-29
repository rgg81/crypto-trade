"""team-14 — market state from cross-sectional breadth and dispersion.

The book is a slow, cost-aware cross-sectional core carrying a bounded directional tilt whose
size and sign are timed by the breadth / dispersion state of the live perpetual universe.

Two legs, built from the same cross-section:

  * a neutral core  ``n``  (sum(n) = 0, sum(|n|) = 1) from the cross-sectional rank of a
    volatility-normalised trend primitive and of trailing funding crowding;
  * a directional tilt ``tau`` in [-0.25, 0.25] from the *moments* of that same cross-section
    -- breadth, taker-flow breadth, dispersion and mean funding crowding.

  w = (1 - |tau|) * n  +  tau * v          with v an inverse-volatility long distribution

so ``sum(w) = tau`` by construction and ``sum(|w|) <= 1``.

Each leg is the average of its last ``M`` recomputations on strictly past data. That averaging
is the cost control: it divides realised turnover by about ``sqrt(M)`` while costing only
``(M-1)/2`` bars of lag, and it changes no signal definition.

No persistent state, no randomness, no embedded data. Every number below is a declared
configuration constant; each decision is recomputed from the past-only rows in ``context``.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

# --- universe -----------------------------------------------------------------------------
UNIVERSE_K = 60             # top-K by trailing median quote volume
VOLUME_WINDOW = 30          # bars used for the liquidity median
MIN_CROSS_SECTION = 12      # fewest names that make a cross-sectional statistic meaningful
MIN_ACTIVE = 8              # fewest non-zero names in the neutral core

# --- per-symbol primitive -----------------------------------------------------------------
TREND_LOOKBACK = 90         # L_b, bars (30 days)
VOL_WINDOW = 45             # sigma, bars
CARRY_LOOKBACK = 21         # per-symbol funding crowding, bars (7 days)

# --- state moments ------------------------------------------------------------------------
STATE_LOOKBACK = 9          # L_d, bars (3 days) -- dispersion / flow / mean funding
ZSCORE_WINDOW = 360         # W, bars (120 days), causal
ZSCORE_MIN = 60
ZSCORE_CLIP = 3.0

# --- exposure map -------------------------------------------------------------------------
W_FLOW = 0.5                # w_f, taker-flow breadth, sign fixed +
W_DISPERSION = 0.5          # w_d, dispersion, sign fixed -
W_CROWDING = 0.5            # w_c, funding crowding, sign fixed -
TANH_SCALE = 1.0            # kappa
LONG_TILT = 0.5             # b, unconditional crypto risk-premium prior
NET_CAP = 0.25
NET_FLOOR = 0.05

# --- cost controls ------------------------------------------------------------------------
# Two averaging depths, because the two legs have different information horizons and very
# different turnover elasticities. The core reshuffles the whole book and is slow, so it is
# averaged hard. The tilt moves a bounded scalar and is the mandate itself, so it is averaged
# only enough to stop it whipsawing.
CORE_SMOOTH = 24            # M_core, bars (8 days)
TILT_SMOOTH = 9             # M_tilt, bars (3 days)
SCORE_FLOOR = 0.25          # theta, soft threshold on the combined rank score
TREND_SHARE = 0.60
CARRY_SHARE = 0.40
DUST = 2e-4                 # below this a target is not worth an order

# --- hard caps and shapes -----------------------------------------------------------------
MAX_WEIGHT = 0.08           # inside the 0.10 rule cap
GROSS_CAP = 1.0
VOL_FLOOR = 1e-4
EPS = 1e-12
MIN_HISTORY = TREND_LOOKBACK + CORE_SMOOTH + 10
PANEL_BARS = ZSCORE_WINDOW + TREND_LOOKBACK + VOL_WINDOW + CORE_SMOOTH + 5


def _median_quote_volume(frame: pd.DataFrame) -> float:
    """Trailing median quote volume, computed on the symbol's own tail (no alignment needed)."""
    values = frame["quote_volume"].to_numpy(dtype=float)[-VOLUME_WINDOW:]
    if values.size == 0:
        return 0.0
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return 0.0
    return float(np.median(finite))


def _align(tails: Mapping[str, pd.DataFrame], symbols, column: str) -> pd.DataFrame:
    """Build a time x symbol panel keyed on ``open_time`` -- the only correct alignment key."""
    objs = []
    keys = []
    for symbol in symbols:
        frame = tails[symbol]
        series = pd.Series(
            frame[column].to_numpy(dtype=float),
            index=pd.Index(frame["open_time"]),
        )
        series = series[~series.index.duplicated(keep="last")]
        objs.append(series)
        keys.append(symbol)
    panel = pd.concat(objs, axis=1, keys=keys).sort_index()
    return panel.iloc[-PANEL_BARS:]


def _funding_per_bar(funding: pd.DataFrame, symbols, index: pd.Index) -> pd.DataFrame | None:
    """Total funding rate settled inside each bar, per symbol.

    Settlement frequency changed over the sample (8h, then 4h for many contracts, 1h while a
    rate sits at its cap), so a *count* of funding rows is not comparable across time or across
    symbols. Summing the rate inside a bar is, because it is the funding actually paid over that
    bar. Rows are attached to the latest bar whose ``open_time`` is at or before the settlement,
    by relative position only -- no absolute calendar anchor.
    """
    if funding is None or len(funding) == 0:
        return None
    for required in ("symbol", "funding_rate", "funding_time"):
        if required not in funding.columns:
            return None

    # Compare in integer UTC nanoseconds rather than as timestamps: the two frames need not
    # agree on tz-awareness, and a raised comparison here would silently cost the carry leg.
    bar_ns = pd.DatetimeIndex(index).asi8
    stamp_ns = pd.DatetimeIndex(funding["funding_time"]).asi8
    mask = (stamp_ns >= bar_ns[0]) & funding["symbol"].isin(set(symbols)).to_numpy()
    if not bool(mask.any()):
        return None
    rows = funding[mask]

    positions = np.searchsorted(bar_ns, stamp_ns[mask], side="right") - 1
    rates = rows["funding_rate"].to_numpy(dtype=float)
    column_of = {symbol: i for i, symbol in enumerate(symbols)}
    columns = rows["symbol"].map(column_of).to_numpy(dtype=float)

    keep = (
        (positions >= 0)
        & (positions < len(index))
        & np.isfinite(rates)
        & np.isfinite(columns)
    )
    if not bool(keep.any()):
        return None

    matrix = np.zeros((len(index), len(symbols)), dtype=float)
    np.add.at(
        matrix,
        (positions[keep].astype(int), columns[keep].astype(int)),
        rates[keep],
    )
    return pd.DataFrame(matrix, index=index, columns=list(symbols))


def _zscore(series: pd.Series) -> np.ndarray:
    """Causal rolling z-score; zero wherever there is not yet enough history to say anything."""
    mean = series.rolling(ZSCORE_WINDOW, min_periods=ZSCORE_MIN).mean()
    std = series.rolling(ZSCORE_WINDOW, min_periods=ZSCORE_MIN).std()
    z = (series - mean) / std.where(std > EPS)
    return z.clip(-ZSCORE_CLIP, ZSCORE_CLIP).fillna(0.0).to_numpy(dtype=float)


def _cross_rank(values: np.ndarray) -> np.ndarray:
    """Symmetric average-rank score in [-1, 1]; ties share a rank, so the map does not depend
    on the order symbols happen to arrive in. Missing names score 0 (mid-pack)."""
    series = pd.Series(values, dtype=float)
    ranks = series.rank(method="average")
    count = int(ranks.notna().sum())
    if count < 3:
        return np.zeros(series.shape[0], dtype=float)
    scaled = 2.0 * (ranks - 1.0) / (count - 1.0) - 1.0
    return scaled.fillna(0.0).to_numpy(dtype=float)


def _neutral_core(trend_row: np.ndarray, carry_row: np.ndarray) -> np.ndarray | None:
    """One snapshot of the dollar-neutral core: sum = 0, sum of absolute values = 1."""
    valid = np.isfinite(trend_row)
    if int(valid.sum()) < MIN_CROSS_SECTION:
        return None

    trend_rank = _cross_rank(np.where(valid, trend_row, np.nan))
    carry_valid = valid & np.isfinite(carry_row)
    if int(carry_valid.sum()) >= MIN_CROSS_SECTION:
        carry_rank = _cross_rank(np.where(carry_valid, carry_row, np.nan))
    else:
        carry_rank = np.zeros_like(trend_rank)

    score = TREND_SHARE * trend_rank - CARRY_SHARE * carry_rank
    score = np.where(valid, score, 0.0)
    score = np.where(valid, score - float(score[valid].mean()), 0.0)

    # Soft threshold: mid-pack names carry almost no conviction and almost all of the rank
    # churn, so they are held flat rather than traded around.
    core = np.sign(score) * np.maximum(np.abs(score) - SCORE_FLOOR, 0.0)
    active = np.abs(core) > 0.0
    if int(active.sum()) < MIN_ACTIVE:
        return None

    core[active] = core[active] - float(core[active].mean())
    gross = float(np.abs(core).sum())
    if gross <= EPS:
        return None
    return core / gross


def _finalise(weights: np.ndarray) -> np.ndarray:
    """Apply the per-symbol, gross and net caps, then use the gross budget that is left."""
    weights = np.clip(weights, -MAX_WEIGHT, MAX_WEIGHT)

    gross = float(np.abs(weights).sum())
    if gross > GROSS_CAP:
        weights = weights * (GROSS_CAP / gross)

    net = float(weights.sum())
    if abs(net) > NET_CAP:
        weights = weights * (NET_CAP / abs(net))

    gross = float(np.abs(weights).sum())
    if gross <= EPS:
        return weights
    scale = GROSS_CAP / gross
    net = abs(float(weights.sum()))
    if net > EPS:
        scale = min(scale, NET_CAP / net)
    peak = float(np.abs(weights).max())
    if peak > EPS:
        scale = min(scale, MAX_WEIGHT / peak)
    if scale > 1.0:
        weights = weights * scale
    return weights


class BreadthStateStrategy:
    """Bounded directional tilt, timed on the moments of the cross-section it trades."""

    def target_weights(self, context, *, seed: int):
        bars = context.bars

        # ---- universe: liquid, and old enough that its trend primitive exists --------------
        candidates = []
        for symbol in context.eligible_symbols:
            if symbol not in bars:
                continue
            frame = bars[symbol]
            if len(frame) < MIN_HISTORY:
                continue
            volume = _median_quote_volume(frame)
            if volume > 0.0:
                candidates.append((volume, symbol))
        if len(candidates) < MIN_CROSS_SECTION:
            return None
        candidates.sort(key=lambda item: item[0], reverse=True)
        symbols = [symbol for _, symbol in candidates[:UNIVERSE_K]]

        tails = {symbol: bars[symbol].iloc[-PANEL_BARS:] for symbol in symbols}
        close = _align(tails, symbols, "close")
        close = close.where(close > 0.0)
        if len(close) < MIN_HISTORY:
            return None
        quote_volume = _align(tails, symbols, "quote_volume")
        taker_buy = _align(tails, symbols, "taker_buy_quote_volume")

        # ---- per-symbol primitive ---------------------------------------------------------
        log_return = np.log(close).diff()
        sigma = log_return.rolling(
            VOL_WINDOW, min_periods=int(VOL_WINDOW * 0.8)
        ).std().clip(lower=VOL_FLOOR)
        sma = close.rolling(
            TREND_LOOKBACK, min_periods=int(TREND_LOOKBACK * 0.8)
        ).mean()
        trend = (close / sma.where(sma > 0.0) - 1.0) / sigma

        # Funding is an optional enrichment: if the frame is absent, empty or carries a
        # timestamp convention this code cannot align, the book falls back to trend alone
        # rather than failing to trade.
        try:
            funding_bar = _funding_per_bar(context.funding, symbols, close.index)
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            funding_bar = None
        if funding_bar is not None:
            funding_bar = funding_bar.where(close.notna())
            carry = funding_bar.rolling(
                CARRY_LOOKBACK, min_periods=max(2, CARRY_LOOKBACK // 2)
            ).sum()
            crowding = funding_bar.rolling(
                STATE_LOOKBACK, min_periods=max(2, STATE_LOOKBACK // 2)
            ).sum().mean(axis=1)
        else:
            carry = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
            crowding = pd.Series(0.0, index=close.index)

        # ---- state moments of the same cross-section --------------------------------------
        live = trend.notna().sum(axis=1)
        breadth = np.sign(trend).mean(axis=1).where(live >= MIN_CROSS_SECTION)

        horizon_return = np.log(close).diff(STATE_LOOKBACK)
        scale = sigma.mean(axis=1) * math.sqrt(STATE_LOOKBACK)
        dispersion = (
            horizon_return.std(axis=1) / scale.where(scale > EPS)
        ).where(horizon_return.notna().sum(axis=1) >= MIN_CROSS_SECTION)

        taker_sum = taker_buy.rolling(
            STATE_LOOKBACK, min_periods=STATE_LOOKBACK
        ).sum()
        volume_sum = quote_volume.rolling(
            STATE_LOOKBACK, min_periods=STATE_LOOKBACK
        ).sum()
        ratio = taker_sum / volume_sum.where(volume_sum > EPS)
        buy_side = (ratio > 0.5).astype(float).where(ratio.notna())
        flow = (2.0 * buy_side.mean(axis=1) - 1.0).where(
            ratio.notna().sum(axis=1) >= MIN_CROSS_SECTION
        )

        z_breadth = _zscore(breadth)
        z_flow = _zscore(flow)
        z_dispersion = _zscore(dispersion)
        z_crowding = _zscore(crowding)

        state = (
            z_breadth
            + W_FLOW * z_flow
            - W_DISPERSION * z_dispersion
            - W_CROWDING * z_crowding
        )
        tilt = NET_CAP * np.tanh((state + LONG_TILT) / TANH_SCALE)

        # ---- average the last M recomputations of each leg ---------------------------------
        # Each snapshot is the same formula evaluated on strictly past data, so the average is
        # still a past-only function. Averaging M target vectors divides turnover by about
        # sqrt(M) while costing only (M-1)/2 bars of lag.
        trend_values = trend.to_numpy(dtype=float)
        carry_values = carry.to_numpy(dtype=float)
        core_sum = np.zeros(len(symbols), dtype=float)
        used = 0
        for offset in range(1, min(CORE_SMOOTH, len(close)) + 1):
            core = _neutral_core(trend_values[-offset], carry_values[-offset])
            if core is None:
                continue
            core_sum += core
            used += 1
        if used == 0:
            return None
        core = core_sum / used

        tilt_depth = min(TILT_SMOOTH, len(close))
        recent = tilt[-tilt_depth:]
        recent = recent[np.isfinite(recent)]
        net = float(recent.mean()) if recent.size else 0.0
        if not np.isfinite(net):
            net = 0.0
        net = float(np.clip(net, -NET_CAP, NET_CAP))
        # The mandate requires a non-zero net; the floor is what makes that true in every state.
        if abs(net) < NET_FLOOR:
            net = NET_FLOOR if net >= 0.0 else -NET_FLOOR

        # ---- directional leg: inverse volatility across the live universe -----------------
        last_sigma = sigma.to_numpy(dtype=float)[-1]
        usable = np.isfinite(last_sigma) & (last_sigma > 0.0) & np.isfinite(core)
        if int(usable.sum()) < MIN_CROSS_SECTION:
            return None
        inverse_vol = np.where(usable, 1.0 / np.maximum(last_sigma, VOL_FLOOR), 0.0)
        total = float(inverse_vol.sum())
        if total <= EPS:
            return None
        inverse_vol = inverse_vol / total

        # Demean over the tradable set first, normalise second: sum(core) = 0 and
        # sum(|core|) = 1 together are what make sum(w) equal the intended tilt exactly.
        core = np.where(usable, core, 0.0)
        core = np.where(usable, core - float(core[usable].mean()), 0.0)
        gross = float(np.abs(core).sum())
        if gross <= EPS:
            return None
        core = core / gross

        weights = (1.0 - abs(net)) * core + net * inverse_vol
        weights = np.where(np.isfinite(weights), weights, 0.0)
        weights = _finalise(weights)

        book = {}
        for i, symbol in enumerate(symbols):
            value = float(weights[i])
            if np.isfinite(value) and abs(value) >= DUST:
                book[symbol] = value
        if len(book) < MIN_ACTIVE:
            return None
        return book


def build_strategy() -> BreadthStateStrategy:
    return BreadthStateStrategy()
