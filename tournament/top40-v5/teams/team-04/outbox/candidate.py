"""team-04 -- residual cross-sectional momentum on Binance USD-M perpetuals.

Signal
    8h log returns orthogonalised to an equal-weighted cross-sectional market
    factor using a winsorised, shrunk rolling beta; the residual series is
    accumulated over a lookback window and divided by its own residual
    volatility over that window.

Book
    Cross-sectional linear rank scores, averaged over every overlapping
    formation lag inside the holding period (Jegadeesh-Titman construction),
    then projected orthogonal to {1, beta} so the submitted book is dollar-
    and beta-neutral by construction.

Everything is recomputed from the past-only rows in ``DecisionContext``.  The
object carries no state across decisions, reads no clock, and never references
a symbol by name.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# --- residualisation ---------------------------------------------------------
BETA_WINDOW = 270          # W: 90 days of 8h bars
BETA_MIN_OBS = 60          # do not trust a beta fitted on less than 20 days
BETA_SHRINK = 0.5          # lambda: beta_hat = (1-l) * ols + l * 1.0
BETA_LO = -1.0             # OLS winsorisation before shrinkage
BETA_HI = 3.0

# --- signal ------------------------------------------------------------------
LOOKBACKS = (45, 90)       # L: 15 and 30 days, blended with equal weight
HOLD = 63                  # H: overlapping formation lags = 21 days

# --- universe ----------------------------------------------------------------
UNIVERSE_CAP = 150         # top-N by trailing median 8h quote volume
LIQ_WINDOW = 90            # bars behind the liquidity median
MIN_HISTORY = 66           # shortest trailing run of clean bars we will use
MIN_NAMES = 12             # below this a cross-section is not a portfolio
MIN_MARKET_NAMES = 5       # names needed before a market factor row is usable

# --- book --------------------------------------------------------------------
MAX_WEIGHT = 0.10
GROSS_TARGET = 1.0
RETURN_CLIP = 0.5          # log-return hygiene bound; scale-free
PANEL_ROWS = 440           # BETA_WINDOW + max(LOOKBACKS) + HOLD + margin
EPS = 1e-12


def _select_universe(bars, symbols, window, cap):
    """Point-in-time liquidity screen. Volume enters here and nowhere else."""
    names = []
    scores = []
    for sym in symbols:
        frame = bars.get(sym)
        if frame is None or len(frame) < 2:
            continue
        columns = frame.columns
        if "close" not in columns or "open_time" not in columns:
            continue
        liq = 0.0
        if "quote_volume" in columns:
            vol = np.asarray(frame["quote_volume"].to_numpy()[-window:], dtype=float)
            vol = vol[np.isfinite(vol)]
            if vol.size:
                liq = float(np.median(vol))
        names.append(sym)
        scores.append(liq)
    if len(names) <= cap:
        return names
    order = np.argsort(-np.asarray(scores, dtype=float), kind="stable")[:cap]
    return [names[i] for i in sorted(int(j) for j in order)]


def _tail_panel(bars, symbols, rows):
    """Align close prices on ``open_time`` -- the only correct alignment key."""
    columns = {}
    for sym in symbols:
        frame = bars.get(sym)
        if frame is None or len(frame) < 2:
            continue
        tail = frame.iloc[-rows:]
        index = pd.Index(np.asarray(tail["open_time"]))
        series = pd.Series(np.asarray(tail["close"], dtype=float), index=index)
        series = series[~series.index.duplicated(keep="last")]
        columns[sym] = series
    if not columns:
        return [], None
    panel = pd.DataFrame(columns).sort_index()
    return list(panel.columns), panel.to_numpy(dtype=float)


def _log_returns(prices, clip):
    with np.errstate(divide="ignore", invalid="ignore"):
        safe = np.where(prices > 0.0, prices, np.nan)
        rets = np.log(safe[1:] / safe[:-1])
    rets = np.where(np.isfinite(rets), rets, np.nan)
    return np.clip(rets, -clip, clip)


def _trailing_run(mask):
    """Length of the unbroken run of valid observations ending at the last row."""
    reversed_mask = mask[::-1]
    first_gap = np.argmin(reversed_mask, axis=0)
    complete = reversed_mask.all(axis=0)
    return np.where(complete, reversed_mask.shape[0], first_gap).astype(np.int64)


def _cumsum0(values):
    out = np.zeros((values.shape[0] + 1, values.shape[1]), dtype=float)
    out[1:] = np.cumsum(values, axis=0)
    return out


def _average_rank(values):
    """Tie-aware average ranks, so the book does not depend on symbol order."""
    n = values.size
    order = np.argsort(values, kind="stable")
    sorted_values = values[order]
    positions = np.arange(1.0, n + 1.0)
    fresh = np.empty(n, dtype=bool)
    fresh[0] = True
    if n > 1:
        fresh[1:] = sorted_values[1:] != sorted_values[:-1]
    group = np.cumsum(fresh) - 1
    sums = np.bincount(group, weights=positions)
    counts = np.bincount(group)
    averaged = (sums / counts)[group]
    ranks = np.empty(n, dtype=float)
    ranks[order] = averaged
    return ranks


def _rank_score(values):
    """Standardised rank on [-1, 1] with zero mean -- linear in rank."""
    n = values.size
    if n < 2:
        return np.zeros(n, dtype=float)
    return (2.0 * _average_rank(values) - (n + 1.0)) / (n - 1.0)


def _shrunk_beta(cum, run, n_rows):
    """Winsorised OLS beta on the longest available window, shrunk toward 1."""
    count, sum_r, sum_m, sum_rm, sum_mm = cum
    index = np.arange(run.size)
    width = np.minimum(BETA_WINDOW, run)
    start = n_rows - width
    obs = count[n_rows] - count[start, index]
    s_r = sum_r[n_rows] - sum_r[start, index]
    s_m = sum_m[n_rows] - sum_m[start, index]
    s_rm = sum_rm[n_rows] - sum_rm[start, index]
    s_mm = sum_mm[n_rows] - sum_mm[start, index]
    safe_obs = np.maximum(obs, 1.0)
    covariance = s_rm - s_r * s_m / safe_obs
    variance = s_mm - s_m * s_m / safe_obs
    usable = (obs >= BETA_MIN_OBS) & (variance > EPS)
    ols = np.where(usable, covariance / np.where(usable, variance, 1.0), 1.0)
    ols = np.clip(ols, BETA_LO, BETA_HI)
    return (1.0 - BETA_SHRINK) * ols + BETA_SHRINK


def _neutralise(score, beta):
    """Residual of ``score`` on {1, beta}: sum(w) = 0 and sum(w * beta) = 0."""
    centred = score - score.mean()
    beta_centred = beta - beta.mean()
    denominator = float(beta_centred @ beta_centred)
    if denominator > EPS * max(beta.size, 1):
        centred = centred - (float(centred @ beta_centred) / denominator) * beta_centred
    return centred - centred.mean()


def _to_book(weights, names):
    gross = float(np.abs(weights).sum())
    if not np.isfinite(gross) or gross <= EPS:
        return None
    weights = weights / gross
    for _ in range(4):
        weights = np.clip(weights, -MAX_WEIGHT, MAX_WEIGHT)
        gross = float(np.abs(weights).sum())
        if gross <= EPS:
            return None
        weights = weights * (GROSS_TARGET / gross)
    weights = np.clip(weights, -MAX_WEIGHT, MAX_WEIGHT)
    gross = float(np.abs(weights).sum())
    net = float(weights.sum())
    if gross > EPS and abs(net) > 0.20 * gross:
        weights = np.clip(weights - net / weights.size, -MAX_WEIGHT, MAX_WEIGHT)
    book = {}
    for name, weight in zip(names, weights):
        value = float(weight)
        if np.isfinite(value) and abs(value) > 1e-6:
            book[name] = value
    return book or None


class ResidualCrossSectionalMomentum:
    """Stateless residual momentum book, refitted from scratch each decision."""

    __slots__ = ()

    def target_weights(self, context, *, seed):
        eligible = context.eligible_symbols
        bars = context.bars
        if eligible is None or bars is None:
            return None
        symbols = list(eligible)
        if len(symbols) < MIN_NAMES or len(bars) == 0:
            return None

        universe = _select_universe(bars, symbols, LIQ_WINDOW, UNIVERSE_CAP)
        if len(universe) < MIN_NAMES:
            return None

        names, prices = _tail_panel(bars, universe, PANEL_ROWS)
        if prices is None or prices.shape[0] < MIN_HISTORY + 2:
            return None

        rets = _log_returns(prices, RETURN_CLIP)
        run = _trailing_run(np.isfinite(rets))
        keep = run >= MIN_HISTORY
        if int(keep.sum()) < MIN_NAMES:
            return None
        names = [name for name, flag in zip(names, keep) if flag]
        rets = rets[:, keep]
        run = run[keep]
        n_rows, n_names = rets.shape

        # Equal-weighted market factor over the surviving cross-section.
        valid = np.isfinite(rets)
        filled = np.where(valid, rets, 0.0)
        per_row = valid.sum(axis=1)
        market = np.where(per_row > 0, filled.sum(axis=1) / np.maximum(per_row, 1), 0.0)
        market = np.where(per_row >= MIN_MARKET_NAMES, market, 0.0)

        observed = valid & (per_row >= MIN_MARKET_NAMES)[:, None]
        r_obs = np.where(observed, filled, 0.0)
        m_obs = np.where(observed, market[:, None], 0.0)
        beta = _shrunk_beta(
            (
                _cumsum0(observed.astype(float)),
                _cumsum0(r_obs),
                _cumsum0(m_obs),
                _cumsum0(r_obs * m_obs),
                _cumsum0(m_obs * m_obs),
            ),
            run,
            n_rows,
        )

        # One coherent residual series per contract, then windowed statistics.
        residual = np.where(valid, rets - market[:, None] * beta[None, :], 0.0)
        cum_e = _cumsum0(residual)
        cum_e2 = _cumsum0(residual * residual)

        total = np.zeros(n_names, dtype=float)
        components = 0
        for lookback in LOOKBACKS:
            for lag in range(HOLD):
                end = n_rows - lag
                begin = end - lookback
                if begin < 0:
                    continue
                fitted = run >= (lag + lookback)
                if int(fitted.sum()) < MIN_NAMES:
                    continue
                total_e = cum_e[end] - cum_e[begin]
                total_e2 = cum_e2[end] - cum_e2[begin]
                mean_e = total_e / lookback
                variance = total_e2 / lookback - mean_e * mean_e
                deviation = np.sqrt(np.maximum(variance, 0.0))
                usable = fitted & (deviation > EPS)
                if int(usable.sum()) < MIN_NAMES:
                    continue
                total[usable] += _rank_score(total_e[usable] / deviation[usable])
                components += 1
        if components == 0:
            return None

        weights = _neutralise(total / components, beta)
        return _to_book(weights, names)


def build_strategy():
    return ResidualCrossSectionalMomentum()
