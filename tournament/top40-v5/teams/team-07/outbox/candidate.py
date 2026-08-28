"""team-07 - cointegration convergence. Nomination candidate.

Rolling pairwise Engle-Granger cointegration on log close prices, a preregistered
half-life, and the three-part stop of section 4 of lane/scouting/THESIS.md.

The book is a set of beta-hedged pair spreads, never a cross-sectionally demeaned
symbol score. The pair is the position, not merely the estimator: a symbol's weight
is the sum of the hedged legs it carries and is never recentred against the universe.

Three things differ from the discovery baseline, each traceable to a gate that failed:

  1. The screen is loosened along declared Tier-2 knobs (tau, m, m_max) whose opening
     triggers were met by the breadth and cost-share failures, so the book holds tens
     of pairs instead of two. The marginal pair is then 1/30 of the book rather than
     half of it, which removes most set-churn turnover.
  2. Every gate is a Lipschitz taper rather than a step, so a pair drifting across a
     nominal boundary changes size by a few percent instead of round-tripping two legs.
  3. Positions are re-marked on a scheduled cadence and held with ``None`` in between.
     A ten-day convergence trade does not need to be re-hedged every eight hours, and
     re-hedging it is what made the discovery book uneconomic.

State: none. Every quantity, including the excursion clock and the rebalance clock,
is a pure function of the past-only rows in the window. Nothing is remembered.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Tier 0 - fixed by preregistration, never searched.
#   price transform      log(close)
#   method               Engle-Granger, log P_dep ~ 1 + log P_ind, ADF on residual
#   z basis              in-window residual mean and sd, past-only, no embargo
#   excursion clock      bars since the residual last crossed its in-window mean
#   leg sizing           beta-weighted, pair gross normalised
#   pair weighting       equal per pair
#   volatility targeting none; the ex-ante risk unit is the engine's
# ---------------------------------------------------------------------------

# --- Tier 1 - declared grid -------------------------------------------------
HALF_LIFE = 30      # H, 8h bars (10 days).      declared {6, 15, 30}
K_AGE = 2           # excursion-age stop, in H.  declared {1, 2, 3, off}; centre
Z_IN = 2.0          # entry threshold, in sigma. declared {1.5, 2.0, 2.5}; centre
Z_STOP = 3.5        # divergence stop, in sigma. declared {2.5,3,3.5,4,off}; centre
N_PAIRS = 30        # pairs held.                declared {12, 20, 30}

# --- Tier 2 - declared contingencies ---------------------------------------
WINDOW = 180        # W, 8h bars (60 days); W = 6H exactly.  declared {90,180,270}
ADF_TAU = -2.6      # residual ADF t screen.     declared {-3.4, -3.0, -2.6}
Z_OUT = 0.25        # take profit, in sigma.     declared {0.0, 0.25, 0.5}
M_PARTNERS = 10     # partners tested per symbol declared {3, 5, 10}
M_MAX = 3           # pairs one symbol may join. declared {1, 2, 3}
EVENT_E = 8.0       # idiosyncratic-event veto.  declared {6, 8, off}
BETA_DRIFT = 0.50   # beta-drift invalidation.   declared {0.25, 0.50, off}
LIQ_FLOOR = 0.25    # universe percentile floor. declared {0.00, 0.25, 0.50}
FUNDING_VETO = True # declared {off, on}

# --- Not on the declared surface; recorded as a preregistration gap ---------
# See lane/outbox/RATIONALE.md, "An admitted gap in the preregistration".
REBALANCE_EVERY = 6   # scheduled re-mark cadence, in bars (2 days)
SAFETY_MODULUS = 97   # second, deliberately rare clock; see RATIONALE

# --- Implementation fixtures: the simplest admissible value, not knobs ------
ADF_LAGS = 1              # augmenting lags in the residual Dickey-Fuller regression
ENTRY_LO = Z_IN - 0.25    # lower edge of the entry taper
EXIT_HI = Z_OUT + 0.25    # upper edge of the take-profit taper
Z_KILL = Z_STOP + 0.5     # the divergence stop is fully binding here
AGE_STOP = K_AGE * HALF_LIFE
AGE_KILL = AGE_STOP + HALF_LIFE
ADF_LO = -ADF_TAU - 0.4   # lower edge of the cointegration taper
BETA_LO, BETA_HI = 0.20, 5.00     # hedge ratios outside this are not a hedge
CORR_MIN = 0.20           # a pair with no common trend has no residual worth trading
DRIFT_KILL = BETA_DRIFT + 0.25
FUND_ROWS = 3 * HALF_LIFE # funding rows averaged per symbol (~30 days)
GROSS = 1.0
MAX_WEIGHT = 0.05         # per-name, well inside the 0.10 hard cap
MAX_NET = 0.20            # inside the 0.25 hard cap
MIN_SYMBOLS = 12
MIN_HELD_PAIRS = 5
MAX_PAIRS = 3000          # compute guard, applied by correlation
EPS = 1e-12


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _ramp(values, lo: float, hi: float) -> np.ndarray:
    """0 at or below ``lo``, 1 at or above ``hi``, linear in between."""
    array = np.asarray(values, dtype=float)
    if hi <= lo:
        return (array >= hi).astype(float)
    return np.clip((array - lo) / (hi - lo), 0.0, 1.0)


def _band(values, hard_lo: float, soft_lo: float, soft_hi: float, hard_hi: float) -> np.ndarray:
    """1 on ``[soft_lo, soft_hi]``, tapering to 0 at ``hard_lo`` and ``hard_hi``."""
    return np.minimum(_ramp(values, hard_lo, soft_lo), 1.0 - _ramp(values, soft_hi, hard_hi))


def _bar_clock(bars: Mapping[str, pd.DataFrame], eligible) -> tuple[int, int]:
    """Two row-count clocks, both invariant to renaming, rescaling and calendar shift.

    ``longest`` is the history length of the longest-listed symbol that is *still
    trading*, so it advances by exactly one per decision; a delisted frame frozen at
    its final length cannot stall it. That is the schedule this strategy wants.

    ``total`` is a second, deliberately coarse clock that exists only so the schedule
    can never be degenerate. If per-symbol history were ever truncated at both ends to
    a constant length, ``longest`` would freeze and a modulus test on it alone could
    silence the book permanently; ``total`` still advances and forces a periodic
    re-mark. Neither clock reads a timestamp, so neither can target an absolute date.
    """
    longest = 0
    for symbol in eligible:
        frame = bars.get(symbol)
        if frame is not None:
            rows = len(frame)
            if rows > longest:
                longest = rows
    total = 0
    for frame in bars.values():
        total += len(frame)
    return longest, total


def _close_panel(bars: Mapping[str, pd.DataFrame], symbols, window: int):
    """Close panel aligned on ``open_time``, which is the only correct alignment key.

    Each frame is sliced to its own last ``window`` rows before alignment. A symbol
    whose rows do not land on the common grid is dropped rather than forward filled:
    a gap means the spread was not observable, not that it was unchanged.
    """
    keys = []
    series = []
    for symbol in symbols:
        frame = bars.get(symbol)
        if frame is None or len(frame) < window:
            continue
        columns = frame.columns
        if "open_time" not in columns or "close" not in columns:
            continue
        tail = frame.iloc[-window:]
        stamps = pd.Index(tail["open_time"].to_numpy())
        if stamps.hasnans or stamps.has_duplicates:
            continue
        keys.append(symbol)
        series.append(pd.Series(tail["close"].to_numpy(dtype=float), index=stamps))
    if len(keys) < MIN_SYMBOLS:
        return None
    panel = pd.concat(series, axis=1, keys=keys).sort_index()
    if panel.shape[0] < window:
        return None
    panel = panel.iloc[-window:].dropna(axis=1, how="any")
    if panel.shape[1] < MIN_SYMBOLS:
        return None
    panel = panel.loc[:, (panel.to_numpy(dtype=float) > 0.0).all(axis=0)]
    if panel.shape[1] < MIN_SYMBOLS:
        return None
    return panel


def _median_quote_volume(bars: Mapping[str, pd.DataFrame], symbols, window: int) -> np.ndarray:
    """Trailing median quote volume per symbol; 0 where the field is unusable."""
    out = np.zeros(len(symbols), dtype=float)
    for position, symbol in enumerate(symbols):
        frame = bars.get(symbol)
        if frame is None or "quote_volume" not in frame.columns:
            continue
        values = frame["quote_volume"].to_numpy(dtype=float)[-window:]
        values = values[np.isfinite(values)]
        if values.size:
            out[position] = float(np.median(values))
    return out


def _mean_funding(funding: pd.DataFrame, lookback: int) -> dict:
    """Trailing mean 8h funding rate per symbol.

    Never compares a funding timestamp with a bar timestamp, so it cannot be silenced
    by the two clocks carrying different dtypes. A symbol absent here simply carries
    no funding view, which makes the veto inert for it rather than wrong.
    """
    if funding is None or len(funding) == 0:
        return {}
    columns = funding.columns
    if "symbol" not in columns or "funding_rate" not in columns:
        return {}
    wanted = ["symbol", "funding_rate"]
    if "funding_time" in columns:
        wanted.append("funding_time")
    frame = funding.loc[:, wanted].dropna(subset=["funding_rate"])
    if len(frame) == 0:
        return {}
    if "funding_time" in frame.columns:
        frame = frame.sort_values("funding_time", kind="stable")
    tail = frame.groupby("symbol", sort=False).tail(lookback)
    means = tail.groupby("symbol", sort=False)["funding_rate"].mean()
    out = {}
    for symbol, value in means.items():
        rate = float(value)
        if np.isfinite(rate):
            out[str(symbol)] = rate
    return out


def _ols_slope(dependent: np.ndarray, regressor: np.ndarray) -> np.ndarray:
    """Column-wise slope of a univariate regression with intercept.

    Centring absorbs the Engle-Granger intercept. That is what makes every quantity
    downstream invariant to any common rescaling of a symbol's price level: P -> cP
    shifts log P by log c, the shift lands entirely in the intercept, and beta and the
    residual are untouched.
    """
    dep = dependent - dependent.mean(axis=0)
    ind = regressor - regressor.mean(axis=0)
    denominator = (ind * ind).sum(axis=0)
    safe = np.where(denominator > EPS, denominator, np.nan)
    return (dep * ind).sum(axis=0) / safe


def _df_tstat(resid: np.ndarray, lags: int) -> np.ndarray:
    """Dickey-Fuller t-statistic on each column of ``resid``.

    The Engle-Granger residual is mean-zero by construction, so the test regression
    carries no intercept:  d u_t = rho * u_{t-1} + phi * d u_{t-1} + e_t.
    """
    du = np.diff(resid, axis=0)
    response = du[lags:]
    ylag = resid[lags:-1]
    if lags <= 0:
        s11 = (ylag * ylag).sum(axis=0)
        safe = np.where(s11 > EPS, s11, np.nan)
        rho = (ylag * response).sum(axis=0) / safe
        error = response - rho * ylag
        dof = max(response.shape[0] - 1, 1)
        variance = (error * error).sum(axis=0) / dof / safe
    else:
        dlag = du[:-lags]
        s11 = (ylag * ylag).sum(axis=0)
        s12 = (ylag * dlag).sum(axis=0)
        s22 = (dlag * dlag).sum(axis=0)
        b1 = (ylag * response).sum(axis=0)
        b2 = (dlag * response).sum(axis=0)
        determinant = s11 * s22 - s12 * s12
        safe = np.where(np.abs(determinant) > EPS, determinant, np.nan)
        rho = (b1 * s22 - b2 * s12) / safe
        phi = (s11 * b2 - s12 * b1) / safe
        error = response - rho * ylag - phi * dlag
        dof = max(response.shape[0] - 2, 1)
        variance = (error * error).sum(axis=0) / dof * s22 / safe
    return rho / np.sqrt(np.where(variance > EPS, variance, np.nan))


def _excursion_age(resid: np.ndarray) -> np.ndarray:
    """Bars in the residual's current run on one side of its in-window mean.

    Commitment C4: the clock is "bars since the residual last crossed its mean", not
    "bars since I entered". A stateless stop cannot drift out of sync with the book.
    """
    side = resid > 0.0
    same = side == side[-1][None, :]
    reversed_same = same[::-1]
    age = np.argmin(reversed_same, axis=0).astype(float)
    return np.where(reversed_same.all(axis=0), float(resid.shape[0]), age)


def _finalise(raw: dict) -> dict:
    """Per-name cap, then gross, then net. Reductions only, in that order."""
    if not raw:
        return {}
    names = sorted(raw)
    vector = np.array([raw[name] for name in names], dtype=float)
    vector = np.where(np.isfinite(vector), vector, 0.0)
    vector = np.clip(vector, -MAX_WEIGHT, MAX_WEIGHT)

    gross = np.abs(vector).sum()
    if gross <= EPS:
        return {}
    if gross > GROSS:
        vector = vector * (GROSS / gross)

    net = float(vector.sum())
    if abs(net) > MAX_NET:
        longs = float(vector[vector > 0.0].sum())
        shorts = float(-vector[vector < 0.0].sum())
        if net > 0.0 and longs > EPS:
            vector = np.where(vector > 0.0, vector * ((shorts + MAX_NET) / longs), vector)
        elif net < 0.0 and shorts > EPS:
            vector = np.where(vector < 0.0, vector * ((longs + MAX_NET) / shorts), vector)

    return {name: float(w) for name, w in zip(names, vector) if abs(w) > 1e-6}


# ---------------------------------------------------------------------------
# The book
# ---------------------------------------------------------------------------


def _pair_book(context) -> dict:
    eligible = [str(s) for s in context.eligible_symbols]
    if len(eligible) < MIN_SYMBOLS:
        return {}

    panel = _close_panel(context.bars, eligible, WINDOW)
    if panel is None:
        return {}

    symbols = [str(c) for c in panel.columns]
    log_price = np.log(panel.to_numpy(dtype=float))
    if not np.isfinite(log_price).all():
        return {}

    returns = np.diff(log_price, axis=0)
    dispersion = returns.std(axis=0)
    keep = np.isfinite(dispersion) & (dispersion > EPS)
    if keep.sum() < MIN_SYMBOLS:
        return {}

    # --- universe floor: the cheapest defence against paying a wide spread ---------
    if LIQ_FLOOR > 0.0:
        volume = _median_quote_volume(context.bars, symbols, WINDOW)
        usable = keep & (volume > 0.0)
        if usable.sum() >= MIN_SYMBOLS:
            threshold = float(np.quantile(volume[usable], LIQ_FLOOR))
            candidate = usable & (volume >= threshold)
            if candidate.sum() >= MIN_SYMBOLS:
                keep = candidate
    index = np.flatnonzero(keep)
    if index.size < MIN_SYMBOLS:
        return {}

    symbols = [symbols[i] for i in index]
    log_price = log_price[:, index]
    returns = returns[:, index]
    dispersion = dispersion[index]
    n_symbols = len(symbols)

    # --- C6: bounded candidate generation, top-m return-correlated partners --------
    centred = returns - returns.mean(axis=0)
    norm = np.sqrt((centred * centred).sum(axis=0))
    with np.errstate(invalid="ignore", divide="ignore"):
        corr = (centred.T @ centred) / np.outer(norm, norm)
    corr = np.nan_to_num(corr, nan=-1.0, posinf=-1.0, neginf=-1.0)
    np.fill_diagonal(corr, -1.0)

    take = min(M_PARTNERS, n_symbols - 1)
    if take <= 0:
        return {}
    order = np.argsort(-corr, axis=1, kind="stable")[:, :take]

    unordered = {}
    for i in range(n_symbols):
        for raw_j in order[i]:
            j = int(raw_j)
            rho = float(corr[i, j])
            if rho < CORR_MIN:
                continue
            key = (i, j) if i < j else (j, i)
            unordered[key] = rho
    if not unordered:
        return {}

    pair_keys = sorted(unordered)
    if len(pair_keys) > MAX_PAIRS:
        pair_keys.sort(key=lambda k: (-unordered[k], k))
        pair_keys = sorted(pair_keys[:MAX_PAIRS])
    left = np.array([a for a, _ in pair_keys], dtype=int)
    right = np.array([b for _, b in pair_keys], dtype=int)
    pair_corr = np.array([unordered[k] for k in pair_keys], dtype=float)

    # The higher-return-variance leg is the regressand. Symmetric under renaming, and
    # it avoids testing both directions and keeping the better one, which would be a
    # second selection channel on top of the ADF screen.
    swap = dispersion[left] < dispersion[right]
    dep_i = np.where(swap, right, left)
    ind_i = np.where(swap, left, right)

    # --- Engle-Granger on log levels ----------------------------------------------
    y = log_price[:, dep_i]
    x = log_price[:, ind_i]
    beta = _ols_slope(y, x)
    resid = (y - y.mean(axis=0)) - beta * (x - x.mean(axis=0))
    sigma = resid.std(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        zpath = resid / np.where(sigma > EPS, sigma, np.nan)
    z_now = zpath[-1]

    tstat = _df_tstat(resid, ADF_LAGS)

    half = WINDOW // 2
    beta_recent = _ols_slope(y[-half:], x[-half:])
    drift = np.abs(beta_recent - beta) / np.maximum(np.abs(beta), EPS)

    age = _excursion_age(resid)
    start = (WINDOW - age).astype(int)
    rows = np.arange(WINDOW)[:, None]
    in_run = rows >= start[None, :]
    peak = np.where(in_run, np.nan_to_num(np.abs(zpath), nan=-1.0), -1.0).max(axis=0)

    # --- idiosyncratic-event veto: news is a break, not an excursion ---------------
    # Measured against a median absolute deviation, which the jump itself does not
    # inflate: an 8-sigma bar raises an ordinary standard deviation enough that an
    # e*std rule would need a ten-sigma move to fire and would sit inert.
    scale = 1.4826 * np.median(np.abs(returns - np.median(returns, axis=0)), axis=0)
    scale = np.where(scale > EPS, scale, dispersion)
    jumped = np.abs(returns) > (EVENT_E * scale[None, :])
    pair_jump = jumped[:, dep_i] | jumped[:, ind_i]
    return_rows = np.arange(WINDOW - 1)[:, None]
    jump_start = np.maximum(start - 1, 0)[None, :]
    news = np.where(return_rows >= jump_start, pair_jump, False).any(axis=0)

    # --- the screen and the three stops, every one of them a taper -----------------
    # S3, the divergence stop, and the entry threshold are a single function of the
    # excursion peak: zero below ENTRY_LO, one across [Z_IN, Z_STOP], zero above
    # Z_KILL. That is Leung and Li's result stated as code - the entry region is a
    # bounded interval lying strictly above the stop, not a rule with a stop bolted on.
    strength = _band(peak, ENTRY_LO, Z_IN, Z_STOP, Z_KILL)
    strength = strength * _ramp(np.abs(z_now), Z_OUT, EXIT_HI)          # take profit
    strength = strength * (1.0 - _ramp(age, AGE_STOP, AGE_KILL))        # S1, primary
    strength = strength * (1.0 - _ramp(drift, BETA_DRIFT, DRIFT_KILL))  # S2
    strength = strength * _ramp(-tstat, ADF_LO, -ADF_TAU)               # cointegration
    strength = strength * _band(beta, 0.5 * BETA_LO, BETA_LO, BETA_HI, 1.2 * BETA_HI)
    strength = strength * _ramp(pair_corr, CORR_MIN, 2.0 * CORR_MIN)
    strength = np.where(news, 0.0, strength)

    side = -np.sign(z_now)

    if FUNDING_VETO:
        rates = _mean_funding(context.funding, FUND_ROWS)
        per_symbol = np.array([rates.get(s, 0.0) for s in symbols], dtype=float)
        # Legs are w_dep = side and w_ind = -side * beta per unit of dependent-leg
        # notional, and a long pays funding, so carry per bar is the expression below.
        carry = -side * (per_symbol[dep_i] - beta * per_symbol[ind_i])
        gain = np.maximum(np.abs(z_now) - Z_OUT, 0.0) * sigma + 1e-4
        with np.errstate(invalid="ignore", divide="ignore"):
            haircut = 1.0 + HALF_LIFE * np.minimum(carry, 0.0) / gain
        strength = strength * np.clip(np.nan_to_num(haircut, nan=0.0), 0.0, 1.0)

    strength = np.nan_to_num(strength, nan=0.0, posinf=0.0, neginf=0.0)
    live = np.isfinite(beta) & np.isfinite(z_now) & np.isfinite(tstat) & (sigma > EPS)
    strength = np.where(live & (side != 0.0), strength, 0.0)

    chosen = np.flatnonzero(strength > 1e-3)
    if chosen.size == 0:
        return {}

    # --- rank, then cap how often one symbol may be reused -------------------------
    # The rank key is the product of cointegration strength and how fully the pair is
    # switched on. The ADF statistic moves slowly over a 180-bar window, so the held
    # set is stable from bar to bar; that stability is where the turnover saving is.
    rank = strength[chosen] * np.abs(np.nan_to_num(tstat[chosen], nan=0.0))
    chosen = chosen[np.argsort(-rank, kind="stable")]

    used: dict = {}
    held = []
    for candidate in chosen:
        pair = int(candidate)
        a = int(dep_i[pair])
        b = int(ind_i[pair])
        if used.get(a, 0) >= M_MAX or used.get(b, 0) >= M_MAX:
            continue
        used[a] = used.get(a, 0) + 1
        used[b] = used.get(b, 0) + 1
        held.append(pair)
        if len(held) >= N_PAIRS:
            break
    if len(held) < MIN_HELD_PAIRS:
        return {}

    # --- equal gross per pair, beta-weighted legs ---------------------------------
    # The per-pair budget is fixed at GROSS / N_PAIRS rather than divided among the
    # pairs actually held. A book with fewer live opportunities is simply smaller; it
    # is not levered back up to a constant gross. That removes the rescaling ripple
    # that turns every change in the opportunity count into turnover on every name,
    # and the engine's ex-ante risk unit sets the scale that matters anyway.
    budget = GROSS / N_PAIRS
    raw: dict = {}
    for pair in held:
        b = float(beta[pair])
        unit = float(strength[pair]) * budget / (1.0 + b)
        s = float(side[pair])
        dep_symbol = symbols[int(dep_i[pair])]
        ind_symbol = symbols[int(ind_i[pair])]
        raw[dep_symbol] = raw.get(dep_symbol, 0.0) + s * unit
        raw[ind_symbol] = raw.get(ind_symbol, 0.0) - s * unit * b

    return _finalise(raw)


class CointegrationConvergence:
    """A book of beta-hedged cointegrated pair spreads, re-marked on a slow clock."""

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        del seed  # nothing in this strategy is random

        bars = context.bars
        if bars is None or len(bars) == 0:
            return {}

        eligible = [str(s) for s in context.eligible_symbols]
        longest, total = _bar_clock(bars, eligible)
        due = (longest % REBALANCE_EVERY == 0) or (total % SAFETY_MODULUS == 0)
        if not due:
            # Hold current quantities. A convergence trade with a ten-day half-life is
            # not improved by being re-hedged every eight hours, and re-hedging it to a
            # constant weight means adding to the diverging leg - which is the way a
            # pairs book actually fails. Membership and delisting exits, participation
            # limits and exposure reductions remain the evaluator's, not mine.
            return None

        return _pair_book(context)


def build_strategy() -> CointegrationConvergence:
    return CointegrationConvergence()
