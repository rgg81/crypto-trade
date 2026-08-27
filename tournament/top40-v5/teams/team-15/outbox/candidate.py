"""team-15 -- discovery candidate: regime-allocated ensemble.

Three cross-sectional sleeves on Binance USD-M perpetuals (carry, trend, short-horizon
reversal), blended by weights that are conditioned on an observable leverage-crowding state
and shrunk toward equal weight.  This is the configuration preregistered as the *default*
in ``lane/scouting/THESIS.md`` section 4 -- no knob has been moved after seeing data,
because no data has been seen.

The object is stateless by construction: every decision is recomputed from the past-only
rows carried by ``DecisionContext``.  ``seed`` is accepted and deliberately unused; there is
no randomness anywhere in this module.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# --- preregistered defaults (THESIS.md section 4).  Bars are 8h. ------------------------
H_CARRY = 3       # A: bars of funding smoothing (24h = one complete 00/08/16 UTC cycle)
H_TREND = 45      # A: bars of trailing return for the trend sleeve (15d)
H_REV = 1         # A: bars of trailing return for the reversal sleeve (8h)
W_REGIME = 180    # B: percentile lookback for the state variable (60d)
Q_SPLIT = 0.67    # B: state boundary quantile on the crowding percentile
H_DWELL = 3       # C: consecutive contrary readings required before a state switch
LAMBDA_EW = 0.50  # C: shrinkage of the state-conditional map toward equal weight
CAP = 0.10        # D: per-symbol gross cap (the contract's hard limit)

# --- fixed implementation guards.  Not search knobs; see RATIONALE.md. ------------------
GROSS = 0.99      # submitted gross, just inside the contract's sum(|w|) <= 1.0
NET_CAP = 0.24    # defensive net guard, just inside the contract's |sum(w)| <= 0.25
MAX_HIST = 1500   # tractability cap on the "expanding" allocation window (~500d)
MIN_XS = 8        # smallest cross-section from which a sleeve may be formed
MIN_OBS = 60      # per-state observations required before the map leaves equal weight
RET_CLIP = 0.50   # per-bar return clip, used ONLY when scoring sleeves, never when trading
FUND_FFILL = 3    # how many funding stamps a missing rate may be carried forward


def _to_naive(index):
    """UTC-naive view of a DatetimeIndex, so bars and funding can be aligned."""
    idx = pd.DatetimeIndex(index)
    try:
        if idx.tz is not None:
            idx = idx.tz_convert("UTC").tz_localize(None)
    except (TypeError, AttributeError):
        pass
    return idx


def _panel(bars, symbols, column):
    """Align one bar column across symbols into a time x symbol frame.

    Symbols differ in history length, so alignment is on the timestamp index when the
    frames carry one and on right-aligned position otherwise.  Nothing here reaches past
    the end of what the context supplied.
    """
    series_map = {}
    for sym in symbols:
        frame = bars.get(sym)
        if frame is None or len(frame) == 0:
            continue
        if column not in getattr(frame, "columns", ()):
            continue
        col = pd.to_numeric(frame[column], errors="coerce")
        if len(col) > MAX_HIST:
            col = col.iloc[-MAX_HIST:]
        if col.index.has_duplicates:
            col = col[~col.index.duplicated(keep="last")]
        series_map[sym] = col
    if not series_map:
        return None

    if all(isinstance(s.index, pd.DatetimeIndex) for s in series_map.values()):
        try:
            return pd.concat(series_map, axis=1).sort_index().iloc[-MAX_HIST:]
        except (ValueError, TypeError):
            pass

    width = max(len(s) for s in series_map.values())
    padded = {}
    for sym, col in series_map.items():
        arr = col.to_numpy(dtype=float)
        padded[sym] = np.concatenate([np.full(width - arr.size, np.nan), arr])
    return pd.DataFrame(padded).iloc[-MAX_HIST:]


def _stamp_column(columns):
    if "funding_time" in columns:
        return "funding_time"
    if "settlement_time" in columns:
        return "settlement_time"
    return None


def _funding_panel(funding, index, symbols):
    """Funding rates pivoted to time x symbol and forward-filled onto the bar clock.

    Only rows stamped at or before a bar label reach that bar, and the sleeve/state
    reconstruction lags this panel by a further full bar, so nothing is read early.
    """
    if funding is None or len(funding) == 0:
        return None
    columns = set(getattr(funding, "columns", ()))
    if "symbol" not in columns or "funding_rate" not in columns:
        return None
    stamp_column = _stamp_column(columns)
    if stamp_column is None or not isinstance(index, pd.DatetimeIndex):
        return None

    stamps = pd.to_datetime(funding[stamp_column], errors="coerce", utc=True)
    tidy = pd.DataFrame(
        {
            "_t": _to_naive(stamps),
            "_s": funding["symbol"].astype(str).to_numpy(),
            "_r": pd.to_numeric(funding["funding_rate"], errors="coerce").to_numpy(),
        }
    ).dropna(subset=["_t", "_r"])
    if tidy.empty:
        return None

    try:
        wide = tidy.pivot_table(index="_t", columns="_s", values="_r", aggfunc="last")
    except (ValueError, TypeError):
        return None
    wide = wide.sort_index().reindex(columns=list(symbols)).ffill(limit=FUND_FFILL)

    target = _to_naive(index)
    if not target.is_monotonic_increasing:
        return None
    aligned = wide.reindex(target, method="ffill")
    aligned.index = index
    return aligned


def _latest_funding(funding, symbols):
    """Degraded path: current smoothed funding only, when the panel cannot be built."""
    if funding is None or len(funding) == 0:
        return None
    columns = set(getattr(funding, "columns", ()))
    if "symbol" not in columns or "funding_rate" not in columns:
        return None
    tidy = pd.DataFrame(
        {
            "_s": funding["symbol"].astype(str).to_numpy(),
            "_r": pd.to_numeric(funding["funding_rate"], errors="coerce").to_numpy(),
        }
    )
    stamp_column = _stamp_column(columns)
    if stamp_column is not None:
        tidy["_t"] = pd.to_datetime(funding[stamp_column], errors="coerce", utc=True)
        tidy = tidy.sort_values("_t", kind="stable")
    tidy = tidy.dropna(subset=["_r"])
    if tidy.empty:
        return None
    tail = tidy.groupby("_s", sort=False)["_r"].apply(lambda s: s.iloc[-H_CARRY:].mean())
    return tail.reindex(list(symbols))


def _xs_book(signal):
    """Cross-sectional rank -> demeaned, unit-gross weights, one row per bar.

    Ranking makes every sleeve invariant to the units and the scale of its own signal, and
    demeaning makes each sleeve use both sides by construction rather than by luck.
    """
    ranks = signal.replace([np.inf, -np.inf], np.nan).rank(axis=1, pct=True)
    count = ranks.notna().sum(axis=1)
    centred = ranks.sub(ranks.mean(axis=1), axis=0)
    gross = centred.abs().sum(axis=1)
    book = centred.div(gross.where(gross > 0.0), axis=0)
    bad = ((count < MIN_XS) | ~(gross > 0.0)).to_numpy()
    return book.mask(np.repeat(bad[:, None], book.shape[1], axis=1))


def _rolling_pct(values, window):
    """Fraction of the trailing `window` observations strictly below the current one."""
    n = values.shape[0]
    out = np.full(n, np.nan)
    if n < window or window < 2:
        return out
    try:
        view = np.lib.stride_tricks.sliding_window_view(values, window)
    except (AttributeError, ValueError):
        view = None

    if view is not None:
        current = view[:, -1]
        finite = np.isfinite(view)
        below = np.where(finite & (view < current[:, None]), 1.0, 0.0).sum(axis=1)
        count = finite.sum(axis=1)
        usable = np.isfinite(current) & (count >= window // 2)
        out[window - 1:] = np.where(usable, below / np.maximum(count, 1), np.nan)
        return out

    for t in range(window - 1, n):
        chunk = values[t - window + 1: t + 1]
        current = chunk[-1]
        if not np.isfinite(current):
            continue
        finite = chunk[np.isfinite(chunk)]
        if finite.size < window // 2:
            continue
        out[t] = float((finite < current).mean())
    return out


def _dwell(raw, dwell):
    """Hysteresis: a state change is honoured only after `dwell` consecutive readings."""
    out = np.full(raw.shape[0], np.nan)
    current = np.nan
    pending = np.nan
    run = 0
    for t in range(raw.shape[0]):
        value = raw[t]
        if np.isfinite(value):
            if not np.isfinite(current):
                current, pending, run = value, np.nan, 0
            elif value == current:
                pending, run = np.nan, 0
            else:
                run = run + 1 if value == pending else 1
                pending = value
                if run >= dwell:
                    current, pending, run = value, np.nan, 0
        out[t] = current
    return out


def _finalize(weights):
    """Normalise to the submitted gross, then respect the contract's hard caps."""
    w = np.where(np.isfinite(weights), weights, 0.0)
    for _ in range(4):
        gross = float(np.abs(w).sum())
        if gross <= 0.0:
            return np.zeros_like(w)
        w = w * (GROSS / gross)
        if np.all(np.abs(w) <= CAP):
            break
        w = np.clip(w, -CAP, CAP)

    w = np.clip(w, -CAP, CAP)
    gross = float(np.abs(w).sum())
    if gross > GROSS:
        w = w * (GROSS / gross)

    net = float(w.sum())
    if abs(net) > NET_CAP and w.size:
        w = w - (net - np.sign(net) * NET_CAP * 0.9) / w.size
        w = np.clip(w, -CAP, CAP)
        gross = float(np.abs(w).sum())
        if gross > GROSS:
            w = w * (GROSS / gross)
    return w


class RegimeAllocatedEnsemble:
    """Blend carry, trend and reversal with weights conditioned on the crowding state."""

    def target_weights(self, context, *, seed):
        symbols = list(getattr(context, "eligible_symbols", ()) or ())
        if len(symbols) < MIN_XS:
            return {}

        bars = getattr(context, "bars", None) or {}
        closes = _panel(bars, symbols, "close")
        if closes is None or closes.shape[0] < H_TREND + 3 or closes.shape[1] < MIN_XS:
            return {}
        universe = list(closes.columns)

        # Returns are used only to score the sleeves, so an outlier bar from a thin or
        # newly listed name cannot dominate a state-conditional estimate.
        returns = closes.div(closes.shift(1)).sub(1.0).replace([np.inf, -np.inf], np.nan)
        returns = returns.clip(lower=-RET_CLIP, upper=RET_CLIP)

        funding = getattr(context, "funding", None)
        panel = _funding_panel(funding, closes.index, universe)
        smooth = None if panel is None else panel.rolling(H_CARRY, min_periods=1).mean()

        signals = {
            "trend": closes.div(closes.shift(H_TREND)).sub(1.0),
            "rev": -(closes.div(closes.shift(H_REV)).sub(1.0)),
        }
        if smooth is not None:
            # Short the names paying the most to be long; be long the names being paid.
            signals["carry"] = -smooth
        else:
            latest = _latest_funding(funding, universe)
            if latest is not None:
                degraded = pd.DataFrame(np.nan, index=closes.index, columns=universe)
                degraded.iloc[-1] = -latest.to_numpy(dtype=float)
                signals["carry"] = degraded

        books = {}
        scored = {}
        for name, signal in signals.items():
            book = _xs_book(signal)
            lagged = book.shift(1)
            books[name] = book
            scored[name] = (lagged.fillna(0.0) * returns.fillna(0.0)).sum(axis=1).where(
                lagged.notna().any(axis=1)
            )

        order = ("carry", "trend", "rev")
        active = [
            name
            for name in order
            if name in books and int(books[name].iloc[-1].notna().sum()) >= MIN_XS
        ]
        if not active:
            return {}

        # --- the state variable: where today's cross-sectional funding sits in its own
        # trailing distribution.  High = leverage demand is crowded and, per the thesis,
        # the crash hazard that carry is paid to bear is elevated.
        state = None
        if smooth is not None:
            axis = smooth.mean(axis=1).to_numpy(dtype=float)
            percentile = _rolling_pct(axis, W_REGIME)
            raw = np.where(
                np.isfinite(percentile), (percentile >= Q_SPLIT).astype(float), np.nan
            )
            state = _dwell(raw, H_DWELL)

        # --- the allocation map: per-state sleeve Sharpe over the expanding past,
        # positive part, renormalised, then shrunk halfway back to equal weight.
        count = len(active)
        allocation = np.full(count, 1.0 / count)
        if state is not None and np.isfinite(state[-1]):
            here = state[-1]
            previous = np.concatenate([[np.nan], state[:-1]])
            sharpes = []
            for name in active:
                series = scored[name].to_numpy(dtype=float)
                mask = np.isfinite(series) & (previous == here)
                sample = series[mask]
                if sample.size < MIN_OBS:
                    sharpes.append(np.nan)
                    continue
                spread = float(sample.std(ddof=1))
                sharpes.append(float(sample.mean()) / spread if spread > 0.0 else np.nan)
            sharpes = np.asarray(sharpes, dtype=float)
            if np.all(np.isfinite(sharpes)) and np.any(sharpes > 0.0):
                positive = np.maximum(sharpes, 0.0)
                allocation = LAMBDA_EW / count + (1.0 - LAMBDA_EW) * (
                    positive / positive.sum()
                )

        blended = np.zeros(len(universe), dtype=float)
        for share, name in zip(allocation, active):
            row = books[name].iloc[-1].to_numpy(dtype=float)
            blended += share * np.where(np.isfinite(row), row, 0.0)

        blended = _finalize(blended)
        return {
            sym: float(weight)
            for sym, weight in zip(universe, blended)
            if np.isfinite(weight) and abs(weight) > 1e-9
        }


def build_strategy():
    return RegimeAllocatedEnsemble()
