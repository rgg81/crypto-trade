"""team-03 — discovery baseline: defensive, beta-controlled allocation.

Long low realized volatility members, short high realized volatility members, rank-weighted
across a liquidity-screened universe of point-in-time members, then tilted toward the
equal-weight member index until the book's shrunk beta is neutral -- or until the
net-exposure budget binds, whichever comes first.

Every constant below is declared ex ante in lane/scouting/THESIS.md section 4. Nothing here is
fitted from data, cached, or carried between decisions: each call reads only the past-only rows
in the context it is handed.

Deliberately NOT in this baseline (thesis knobs held at their tie-break-preferred settings):
the junk/illiquidity leg (`junk_leg = off`) and the funding tilt (`funding_tilt = off`).
Funding is still the mechanism -- it is harvested by being short the crowded high-volatility
names, not by signalling on it. See RATIONALE.md.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

# --- declared parameters (THESIS section 4); none of these are fitted -------------------------
VOL_LOOKBACK = 63           # bars (21d): midpoint of the declared {21, 63, 189} grid
CORR_WINDOW = 378           # bars (126d): fixed by declaration; FP keeps corr window > vol window
BETA_SHRINK = 0.6           # beta = 0.6 * beta_hat + 0.4 * 1.0  (Frazzini-Pedersen shrinkage)
LIQUIDITY_KEEP = 0.70       # keep the top 70% of the universe by trailing median quote volume
NAME_CAP = 0.05             # 5% of gross per name (inside the organizer's 10%)
NET_CAP = 0.23              # 23% of gross net; the organizer's 25% is the hard wall. Uniform
                            # risk-unit rescaling preserves net/gross, so 0.23 stays compliant
                            # even if the book is scaled up to full gross.
GROSS_TARGET = 0.98         # inside the organizer's 1.0
HISTORY_LADDER = (252, 126, 63)   # declared step-down if the shorter windows cannot be supported
MIN_NAMES = 10
MIN_CORR_OBS = 30
MIN_VOL_OBS = 21
BETA_HAT_FLOOR = -1.0
BETA_HAT_CEIL = 5.0
TILT_BISECTIONS = 40


def _log_returns(close: np.ndarray) -> np.ndarray:
    """Bar-over-bar log returns, NaN wherever either close is missing or non-positive."""
    c = np.asarray(close, dtype=float)
    if c.size < 2:
        return np.empty(0, dtype=float)
    prev = c[:-1]
    cur = c[1:]
    out = np.full(prev.size, np.nan, dtype=float)
    ok = np.isfinite(prev) & np.isfinite(cur) & (prev > 0.0) & (cur > 0.0)
    out[ok] = np.log(cur[ok] / prev[ok])
    return out


def _panel_by_time(bars: Mapping[str, pd.DataFrame], symbols: list) -> np.ndarray:
    """Align returns on the frame index. Correct when members share a clock but not a start."""
    pieces = {}
    for s in symbols:
        frame = bars[s]
        take = min(len(frame), CORR_WINDOW + 1)
        sub = frame.iloc[-take:]
        series = pd.Series(
            _log_returns(sub["close"].to_numpy(dtype=float)), index=sub.index[1:]
        )
        pieces[s] = series[~series.index.duplicated(keep="last")]
    panel = pd.concat(pieces, axis=1).sort_index().reindex(columns=symbols)
    return panel.iloc[-CORR_WINDOW:].to_numpy(dtype=float)


def _panel_by_position(bars: Mapping[str, pd.DataFrame], symbols: list) -> np.ndarray:
    """Align returns on the tail, front-padded with NaN. Used when the index is not time-typed."""
    columns = []
    for s in symbols:
        frame = bars[s]
        take = min(len(frame), CORR_WINDOW + 1)
        rets = _log_returns(frame["close"].to_numpy(dtype=float)[-take:])
        pad = np.full(max(0, CORR_WINDOW - rets.size), np.nan, dtype=float)
        columns.append(np.concatenate([pad, rets[-CORR_WINDOW:]]))
    return np.column_stack(columns)


def _return_panel(bars: Mapping[str, pd.DataFrame], symbols: list) -> np.ndarray:
    """Time-aligned (rows = bars, cols = symbols) log-return panel, newest row last.

    Symbols have different history lengths, so positional alignment is only correct when every
    member shares the clock. Prefer index alignment; fall back to tail alignment rather than
    raise, because an exception here would silently cost the whole window rather than one bar.
    """
    if all(isinstance(bars[s].index, pd.DatetimeIndex) for s in symbols):
        try:
            return _panel_by_time(bars, symbols)
        except Exception:
            return _panel_by_position(bars, symbols)
    return _panel_by_position(bars, symbols)


def _equal_weight_index(panel: np.ndarray) -> np.ndarray:
    """Equal-weight member index return per bar, over whichever members exist in that bar."""
    finite = np.isfinite(panel)
    counts = finite.sum(axis=1)
    totals = np.where(finite, panel, 0.0).sum(axis=1)
    out = np.full(panel.shape[0], np.nan, dtype=float)
    live = counts > 0
    out[live] = totals[live] / counts[live]
    return out


def _parkinson_vol(frame: pd.DataFrame) -> float:
    """Parkinson high-low realized volatility over the vol lookback; NaN if unusable."""
    take = min(len(frame), VOL_LOOKBACK)
    sub = frame.iloc[-take:]
    high = sub["high"].to_numpy(dtype=float)
    low = sub["low"].to_numpy(dtype=float)
    ok = np.isfinite(high) & np.isfinite(low) & (low > 0.0) & (high >= low)
    if int(ok.sum()) < MIN_VOL_OBS:
        return float("nan")
    span = np.log(high[ok] / low[ok])
    value = math.sqrt(float(np.mean(span * span)) / (4.0 * math.log(2.0)))
    if not math.isfinite(value) or value <= 0.0:
        return float("nan")
    return value


def _median_quote_volume(frame: pd.DataFrame) -> float:
    take = min(len(frame), VOL_LOOKBACK)
    vol = frame["quote_volume"].to_numpy(dtype=float)[-take:]
    vol = vol[np.isfinite(vol)]
    if vol.size == 0:
        return float("nan")
    return float(np.median(vol))


def _correlation(a: np.ndarray, b: np.ndarray) -> float:
    both = np.isfinite(a) & np.isfinite(b)
    if int(both.sum()) < MIN_CORR_OBS:
        return float("nan")
    x = a[both] - a[both].mean()
    y = b[both] - b[both].mean()
    denom = math.sqrt(float(np.dot(x, x)) * float(np.dot(y, y)))
    if denom <= 0.0:
        return float("nan")
    return float(np.dot(x, y)) / denom


def _tail_std(series: np.ndarray) -> float:
    tail = series[-VOL_LOOKBACK:]
    tail = tail[np.isfinite(tail)]
    if tail.size < MIN_VOL_OBS:
        return float("nan")
    return float(np.std(tail))


def _shrunk_betas(panel: np.ndarray, index_returns: np.ndarray, columns: list) -> np.ndarray:
    """Frazzini-Pedersen beta: rho * sigma_i / sigma_m, shrunk toward the index beta of 1."""
    sigma_m = _tail_std(index_returns)
    betas = np.ones(len(columns), dtype=float)
    if not math.isfinite(sigma_m) or sigma_m <= 0.0:
        return betas
    for j in range(len(columns)):
        column = panel[:, j]
        sigma_i = _tail_std(column)
        rho = _correlation(column, index_returns)
        if not math.isfinite(sigma_i) or not math.isfinite(rho):
            continue
        beta_hat = min(BETA_HAT_CEIL, max(BETA_HAT_FLOOR, rho * sigma_i / sigma_m))
        betas[j] = BETA_SHRINK * beta_hat + (1.0 - BETA_SHRINK)
    return betas


def _rank_weights(values: np.ndarray) -> np.ndarray:
    """Rank-weighted spread: long the low end, short the high end. Gross 1, net 0."""
    n = values.size
    order = np.argsort(values, kind="stable")
    ranks = np.empty(n, dtype=float)
    ranks[order] = np.arange(1.0, n + 1.0)
    deviation = float(ranks.mean()) - ranks
    scale = float(np.abs(deviation).sum())
    if scale <= 0.0:
        return np.zeros(n, dtype=float)
    return deviation / scale


def _net_ratio(weights: np.ndarray, unit: np.ndarray, lam: float) -> float:
    tilted = weights + lam * unit
    gross = float(np.abs(tilted).sum())
    if gross <= 0.0:
        return 0.0
    return abs(float(tilted.sum())) / gross


def _beta_tilt(weights: np.ndarray, betas: np.ndarray) -> np.ndarray:
    """Add as much equal-weight index as beta neutrality wants, or as the net cap allows.

    The spread is short beta by construction (low-vol long leg, high-vol short leg), so
    neutralising it means going net long the index. That is the classic BAB shape and it can
    exceed the net-exposure budget; when it does, take the largest hedge the budget permits and
    carry the residual short-beta knowingly rather than let the evaluator clip it arbitrarily.
    """
    n = weights.size
    unit = np.full(n, 1.0 / n, dtype=float)
    portfolio_beta = float(np.dot(weights, betas))
    full = -portfolio_beta
    if not math.isfinite(full) or full == 0.0:
        return weights
    sign = 1.0 if full > 0.0 else -1.0
    high = abs(full)
    if _net_ratio(weights, sign * unit, high) <= NET_CAP:
        return weights + sign * high * unit
    low = 0.0
    for _ in range(TILT_BISECTIONS):
        mid = 0.5 * (low + high)
        if _net_ratio(weights, sign * unit, mid) <= NET_CAP:
            low = mid
        else:
            high = mid
    return weights + sign * low * unit


def _finalize(weights: np.ndarray) -> np.ndarray:
    """Scale to the gross budget, then enforce the per-name cap, then the net cap.

    Order matters and is chosen so each step preserves the previous invariant: clipping
    enforces the name cap; the net fix only ever scales one side *down*, so the name cap
    survives it; and nothing after that scales anything up.
    """
    w = np.where(np.isfinite(weights), weights, 0.0)
    gross = float(np.abs(w).sum())
    if gross <= 0.0:
        return w
    w = w * (GROSS_TARGET / gross)
    w = np.clip(w, -NAME_CAP, NAME_CAP)

    positive = w > 0.0
    negative = w < 0.0
    long_side = float(w[positive].sum())
    short_side = float(-w[negative].sum())
    gross = long_side + short_side
    if gross <= 0.0:
        return np.zeros_like(w)
    net = long_side - short_side
    if abs(net) > NET_CAP * gross:
        if net > 0.0 and long_side > 0.0:
            w[positive] *= min(
                1.0, short_side * (1.0 + NET_CAP) / (long_side * (1.0 - NET_CAP))
            )
        elif net < 0.0 and short_side > 0.0:
            w[negative] *= min(
                1.0, long_side * (1.0 + NET_CAP) / (short_side * (1.0 - NET_CAP))
            )
    return w


class DefensiveBetaControlled:
    """Stateless: every decision is a pure function of the context it is given."""

    def target_weights(self, context, *, seed):
        bars = context.bars
        eligible = [s for s in context.eligible_symbols if s in bars]
        if len(eligible) < MIN_NAMES:
            return None

        # Seasoning screen, with the declared step-down if the longer window starves the book.
        lengths = {s: len(bars[s]) for s in eligible}
        base = []
        for required in HISTORY_LADDER:
            base = [s for s in eligible if lengths[s] >= required]
            if len(base) >= MIN_NAMES:
                break
        if len(base) < MIN_NAMES:
            return None
        base.sort()

        # Liquidity screen: keep the top 70% by trailing median quote volume. This is the
        # Novy-Marx/Velikov guard -- rank weighting is effectively equal weighting, and equal
        # weighting piles into the thinnest contracts where impact eats the spread.
        liquidity = np.array([_median_quote_volume(bars[s]) for s in base], dtype=float)
        usable = np.isfinite(liquidity)
        if int(usable.sum()) < MIN_NAMES:
            return None
        candidates = [base[i] for i in range(len(base)) if usable[i]]
        candidate_liquidity = liquidity[usable]
        keep = max(MIN_NAMES, int(math.ceil(LIQUIDITY_KEEP * len(candidates))))
        keep = min(keep, len(candidates))
        order = np.argsort(-candidate_liquidity, kind="stable")[:keep]
        screened = sorted(candidates[i] for i in order)
        if len(screened) < MIN_NAMES:
            return None

        # The index the mandate names: equal weight over the seasoned member universe, not over
        # the screened subset -- neutrality is defined against membership, not against my screen.
        panel = _return_panel(bars, base)
        index_returns = _equal_weight_index(panel)
        position = {s: i for i, s in enumerate(base)}
        screened_panel = panel[:, [position[s] for s in screened]]

        volatility = np.array([_parkinson_vol(bars[s]) for s in screened], dtype=float)
        good = np.isfinite(volatility)
        if int(good.sum()) < MIN_NAMES:
            return None
        tradable = [screened[i] for i in range(len(screened)) if good[i]]
        screened_panel = screened_panel[:, good]
        volatility = volatility[good]

        betas = _shrunk_betas(screened_panel, index_returns, tradable)
        weights = _finalize(_beta_tilt(_rank_weights(volatility), betas))

        book = {s: float(w) for s, w in zip(tradable, weights) if abs(float(w)) > 1e-6}
        if not book:
            return None
        return book


def build_strategy():
    return DefensiveBetaControlled()
