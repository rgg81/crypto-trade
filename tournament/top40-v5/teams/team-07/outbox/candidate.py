"""team-07 — cointegration convergence as a cross-sectional residual book.

Mandate: rolling pairwise cointegration on log prices, a preregistered half-life, a divergence
stop.

The pair is the *estimator*, not the position. At every decision each eligible symbol is regressed
(Engle-Granger, with intercept, on log closes over a rolling 180-bar window) against its top-5
return-correlated partners. Each pair yields a standardised residual z and a set of continuous
quality multipliers. A symbol's score is the evidence-weighted mean of the residuals it appears
in, signed so that a symbol trading rich to its cointegrated peers is sold. The book is that score
demeaned across the cross-section, soft-thresholded, gross-normalised and per-name capped.

Every screen is a multiplier in [0, 1] rather than an admission test, and the response to z is
linear rather than gated, so the target weight is Lipschitz in every input: a pair whose ADF
t-statistic or z drifts across a nominal boundary changes size by a few percent instead of
round-tripping two legs.

Stateless by construction. Nothing persists between decisions; every quantity, including the
excursion clock, is a function of the rolling window alone.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

# --- Tier 0: fixed by preregistration -------------------------------------------------------
HALF_LIFE = 30              # H, in 8h bars (10 days) — preregistered, never fitted per pair
WINDOW = 6 * HALF_LIFE      # W >= 6H is the declared window/half-life coupling
SMOOTH = max(2, HALF_LIFE // 5)   # trailing span used to measure the residual (see RATIONALE)

# --- the divergence stop, as a shape rather than an event -----------------------------------
Z_STOP = 3.0                # response peaks here; beyond it the position is being wound down
Z_KILL = 4.0                # and is fully flat here
AGE_STOP = 3 * HALF_LIFE    # k*H excursion-age stop (model invalidation), k = 3
AGE_KILL = 2 * AGE_STOP

# --- continuous replacements for the hard screens -------------------------------------------
ADF_LO, ADF_HI = 1.8, 3.2         # ramp on -t_adf, bracketing the declared tau band
CORR_LO, CORR_HI = 0.20, 0.50     # ramp on partner return correlation
BETA_HARD_LO, BETA_SOFT_LO = 0.20, 0.40
BETA_SOFT_HI, BETA_HARD_HI = 2.50, 4.00
EVENT_LO, EVENT_HI = 5.0, 8.0     # idiosyncratic-event veto, in trailing leg dispersion
EVENT_BARS = 3
FUND_BARS = 90                    # funding rows averaged per symbol (~30 days)
FUND_SPAN = pd.Timedelta(days=45)  # relative span used to bound the funding scan

# --- book construction ----------------------------------------------------------------------
PARTNERS = 5                # m: correlation-ranked partners tested per symbol
SHRINK = 1.0                # evidence shrinkage on the per-symbol weighted mean
SOFT_FLOOR = 0.20           # soft threshold, as a fraction of the 95th pctile of |score|
MAX_WEIGHT = 0.030          # per-name cap, well inside the 0.10 hard cap
LIQ_FLOOR = 0.25            # drop the bottom quartile by trailing median quote volume
MAX_UNIVERSE = 400          # compute guard, applied by liquidity
MIN_NAMES = 20              # below this the cross-section is not a portfolio

EPS = 1e-12


def _ramp(x, lo, hi):
    """0 below ``lo``, 1 above ``hi``, linear in between."""
    if hi <= lo:
        return np.where(np.asarray(x) >= hi, 1.0, 0.0)
    return np.clip((np.asarray(x, dtype=float) - lo) / (hi - lo), 0.0, 1.0)


def _band(x, hard_lo, soft_lo, soft_hi, hard_hi):
    """1 on ``[soft_lo, soft_hi]``, ramping to 0 at ``hard_lo`` and ``hard_hi``."""
    return np.minimum(_ramp(x, hard_lo, soft_lo), 1.0 - _ramp(x, soft_hi, hard_hi))


def _column_panel(bars, symbols, column, tail):
    """Align a per-symbol column on ``open_time``, which is the only correct alignment key.

    Each frame is sliced to its last ``tail`` rows *before* reindexing: symbols carry thousands of
    bars and only the window is ever read.
    """
    keys = []
    series = []
    for symbol in symbols:
        frame = bars.get(symbol)
        if frame is None or len(frame) == 0:
            continue
        columns = list(frame.columns)
        if "open_time" not in columns or column not in columns:
            continue
        recent = frame.iloc[-tail:]
        panel_series = pd.Series(
            recent[column].to_numpy(), index=pd.Index(recent["open_time"].to_numpy())
        )
        panel_series = panel_series[~panel_series.index.duplicated(keep="last")]
        keys.append(symbol)
        series.append(panel_series)
    if not keys:
        return pd.DataFrame()
    return pd.concat(series, axis=1, keys=keys).sort_index()


def _mean_funding(funding, lookback):
    """Trailing mean 8h funding rate per symbol; missing symbols simply carry no view."""
    empty = {}
    if funding is None or len(funding) == 0:
        return empty
    columns = list(funding.columns)
    if "symbol" not in columns or "funding_rate" not in columns:
        return empty
    frame = funding
    if "funding_time" in columns:
        # A relative span, never an absolute date: bound the sort without touching the calendar.
        times = frame["funding_time"]
        latest = times.max()
        if pd.notna(latest):
            frame = frame[times >= latest - FUND_SPAN]
        frame = frame.sort_values("funding_time")
    frame = frame[["symbol", "funding_rate"]].dropna()
    if len(frame) == 0:
        return empty
    tail = frame.groupby("symbol", sort=False).tail(lookback)
    means = tail.groupby("symbol", sort=False)["funding_rate"].mean()
    out = {}
    for symbol, value in means.items():
        rate = float(value)
        if np.isfinite(rate):
            out[symbol] = rate
    return out


def _liquid_universe(bars, index, symbols):
    """Keep names above the ``LIQ_FLOOR`` percentile of trailing median quote volume."""
    volume = _column_panel(bars, symbols, "quote_volume", WINDOW + 4)
    if volume.empty:
        return symbols
    volume = volume.reindex(index=index, columns=symbols)
    median = volume.median(axis=0, skipna=True).to_numpy(dtype=float)
    usable = np.isfinite(median) & (median > 0.0)
    if usable.sum() < max(MIN_NAMES, len(symbols) // 2):
        return symbols
    threshold = np.quantile(median[usable], LIQ_FLOOR)
    keep = usable & (median >= threshold)
    if keep.sum() < MIN_NAMES:
        return symbols
    kept = [symbols[i] for i in np.flatnonzero(keep)]
    if len(kept) > MAX_UNIVERSE:
        ranked = np.argsort(-median[keep])[:MAX_UNIVERSE]
        kept = [kept[i] for i in sorted(ranked.tolist())]
    return kept


def _pair_index(corr, partners):
    """Top-``partners`` return-correlated counterparts for every symbol."""
    scored = corr.copy()
    np.fill_diagonal(scored, -np.inf)
    take = min(partners, scored.shape[1] - 1)
    if take <= 0:
        return np.empty(0, dtype=int), np.empty(0, dtype=int)
    order = np.argsort(-scored, axis=1)[:, :take]
    dependent = np.repeat(np.arange(scored.shape[0]), take)
    regressor = order.reshape(-1)
    live = np.isfinite(scored[dependent, regressor]) & (scored[dependent, regressor] > CORR_LO)
    return dependent[live], regressor[live]


def _excursion_age(residual):
    """Bars since the residual last crossed its in-window mean. Stateless by construction."""
    same_side = (residual * residual[-1][None, :]) > 0.0
    reversed_side = same_side[::-1]
    age = np.argmin(reversed_side, axis=0).astype(float)
    never_crossed = reversed_side.all(axis=0)
    return np.where(never_crossed, float(residual.shape[0]), age)


def _adf_t(residual):
    """t-statistic of phi in dE_t = phi * E_{t-1} + u, the Engle-Granger residual ADF screen."""
    lagged = residual[:-1]
    change = np.diff(residual, axis=0)
    lag_ss = (lagged * lagged).sum(axis=0) + EPS
    cross = (lagged * change).sum(axis=0)
    phi = cross / lag_ss
    residual_ss = np.maximum((change * change).sum(axis=0) - phi * cross, 0.0)
    dof = max(residual.shape[0] - 2, 1)
    stderr = np.sqrt(residual_ss / dof / lag_ss) + EPS
    return phi / stderr


def _book(score, symbols):
    """Demean, soft-threshold, cap and gross-normalise the cross-section into a target book."""
    centred = score - score.mean()
    magnitude = np.abs(centred)
    if not np.isfinite(magnitude).any() or magnitude.max() <= EPS:
        return {}

    high = float(np.quantile(magnitude, 0.95))
    if high <= EPS:
        return {}
    clipped = np.clip(centred, -high, high)
    floor = SOFT_FLOOR * high
    weight = np.sign(clipped) * np.maximum(np.abs(clipped) - floor, 0.0)

    gross = np.abs(weight).sum()
    if gross <= EPS:
        return {}
    weight = weight / gross

    for _ in range(6):
        weight = weight - weight.mean()
        weight = np.clip(weight, -MAX_WEIGHT, MAX_WEIGHT)
        gross = np.abs(weight).sum()
        if gross <= EPS:
            return {}
        weight = weight / gross

    weight = np.clip(weight - weight.mean(), -MAX_WEIGHT, MAX_WEIGHT)
    gross = np.abs(weight).sum()
    if gross > 1.0:
        weight = weight / gross
    net = weight.sum()
    if abs(net) > 0.25:
        weight = weight - net / weight.size

    live = np.flatnonzero(np.abs(weight) > 1e-5)
    if live.size < MIN_NAMES:
        return {}
    return {symbols[i]: float(weight[i]) for i in live}


def _target_weights(context):
    eligible = [str(s) for s in context.eligible_symbols]
    if len(eligible) < MIN_NAMES:
        return {}

    closes = _column_panel(context.bars, eligible, "close", WINDOW + 4)
    if closes.empty or closes.shape[0] < WINDOW:
        return {}
    closes = closes.iloc[-(WINDOW + 4):].ffill(limit=2).iloc[-WINDOW:]
    closes = closes.dropna(axis=1, how="any")
    closes = closes.loc[:, (closes > 0.0).all(axis=0)]
    if closes.shape[1] < MIN_NAMES:
        return {}

    symbols = _liquid_universe(context.bars, closes.index, list(closes.columns))
    if len(symbols) < MIN_NAMES:
        return {}
    closes = closes.loc[:, symbols]

    log_price = np.log(closes.to_numpy(dtype=float))
    if not np.isfinite(log_price).all():
        return {}
    # Centring absorbs the Engle-Granger intercept, which is what makes the whole book
    # invariant to any common rescaling of price levels.
    centred = log_price - log_price.mean(axis=0)
    returns = np.diff(log_price, axis=0)

    demeaned = returns - returns.mean(axis=0)
    scale = np.sqrt((demeaned * demeaned).sum(axis=0)) + EPS
    corr = (demeaned.T @ demeaned) / np.outer(scale, scale)

    dependent, regressor = _pair_index(corr, PARTNERS)
    if dependent.size == 0:
        return {}

    moment = centred.T @ centred
    variance = np.diag(moment)
    beta = moment[dependent, regressor] / (variance[regressor] + EPS)
    beta = np.nan_to_num(beta, nan=0.0, posinf=0.0, neginf=0.0)

    residual = centred[:, dependent] - beta[None, :] * centred[:, regressor]
    spread_sd = np.sqrt((residual * residual).sum(axis=0) / max(WINDOW - 2, 1)) + EPS
    # The residual is averaged over SMOOTH bars before standardising: the frozen-beta spread is
    # measured, not sampled, so bar-to-bar noise does not become turnover.
    z = residual[-SMOOTH:].mean(axis=0) / spread_sd

    quality = _ramp(-_adf_t(residual), ADF_LO, ADF_HI)
    quality = quality * _band(beta, BETA_HARD_LO, BETA_SOFT_LO, BETA_SOFT_HI, BETA_HARD_HI)
    quality = quality * _ramp(corr[dependent, regressor], CORR_LO, CORR_HI)
    quality = quality * (1.0 - _ramp(_excursion_age(residual), AGE_STOP, AGE_KILL))

    dispersion = returns.std(axis=0) + EPS
    shock = np.abs(returns[-EVENT_BARS:]).max(axis=0) / dispersion
    calm = 1.0 - _ramp(shock, EVENT_LO, EVENT_HI)
    quality = quality * np.minimum(calm[dependent], calm[regressor])

    # Divergence stop as a shape: the response grows with |z| up to Z_STOP, then winds down to
    # flat at Z_KILL. A broken relationship is exited; it is never exited by a step.
    response = -np.clip(z, -Z_STOP, Z_STOP) * (1.0 - _ramp(np.abs(z), Z_STOP, Z_KILL))

    denominator = 1.0 + np.abs(beta)
    dependent_leg = 1.0 / denominator
    regressor_leg = -beta / denominator

    funding = _mean_funding(context.funding, FUND_BARS)
    rate = np.array([funding.get(s, 0.0) for s in symbols], dtype=float)
    direction = np.sign(response)
    carry = -direction * (dependent_leg * rate[dependent] + regressor_leg * rate[regressor])
    expected = 0.5 * np.abs(z) * spread_sd + EPS
    # Funding is a veto, never an alpha: this multiplier can only reduce a pair's size.
    quality = quality * np.clip(1.0 + HALF_LIFE * carry / expected, 0.0, 1.0)

    signal = np.nan_to_num(quality * response, nan=0.0, posinf=0.0, neginf=0.0)

    numerator = np.zeros(len(symbols), dtype=float)
    evidence = np.zeros(len(symbols), dtype=float)
    np.add.at(numerator, dependent, signal * dependent_leg)
    np.add.at(numerator, regressor, signal * regressor_leg)
    np.add.at(evidence, dependent, quality * np.abs(dependent_leg))
    np.add.at(evidence, regressor, quality * np.abs(regressor_leg))
    score = numerator / (evidence + SHRINK)

    return _book(np.nan_to_num(score, nan=0.0, posinf=0.0, neginf=0.0), symbols)


class CointegrationConvergence:
    """Cross-sectional book over rolling pairwise Engle-Granger residuals."""

    def target_weights(self, context, *, seed) -> Mapping[str, float] | None:
        return _target_weights(context)


def build_strategy() -> CointegrationConvergence:
    return CointegrationConvergence()
