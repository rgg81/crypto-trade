"""team-01 discovery candidate: cross-sectional funding-carry harvest.

Stage A of the preregistered search protocol in ``lane/scouting/THESIS.md`` section 4.3: the
declared **control arm**, with the crowding overlay switched off (``lambda = 0``). This is the
deliberately simple, honest expression of the mandate. Falsifier F2 defines every later
crowding-overlay trial as an improvement *over this book*, so the control has to exist and be
measured before the overlay can be judged.

Mechanism, in one line: funding is a pure transfer between levered longs and the balance sheet
willing to warehouse them, so hold notional of the sign opposite to funding -- long the
most-negative-funding names, short the most-positive -- and collect the transfer.

Everything here is computed from the past-only rows streamed through ``DecisionContext``. No
persistent state, no fitted artifacts, no RNG, no symbol identity, no absolute dates, and no
price levels used as anything other than ratios.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

BAR_HOURS = 8

# --- THESIS 4.1: fixed by declaration, not searched -----------------------------------------
VOL_LOOKBACK = 63          # realised-vol window backing the carry-to-risk normalisation
BETA_LOOKBACK = 90         # beta window vs the equal-weight eligible universe
LIQUIDITY_LOOKBACK = 90    # trailing median quote volume used for universe selection
TARGET_GROSS = 1.0         # constant gross; gross timing is neutralised by the common risk unit
MAX_ABS_WEIGHT = 0.10      # contract cap, enforced here so the evaluator never has to clip

# --- THESIS 4.2 / 4.3 Stage A coordinates ---------------------------------------------------
UNIVERSE_SIZE = 75         # U
FUNDING_LOOKBACK = 3       # L, in 8h bars (24h)
LEG_FRACTION = 0.20        # q
TAIL_TRIM = 0.02           # T, dropped from each tail of raw funding before ranking
CROWDING_LAMBDA = 0.0      # control arm: no crowding overlay in this candidate

MIN_BARS = VOL_LOOKBACK + 1   # stricter than the declared 30-bar burn-in; forced by the vol window
MIN_VOL_OBS = VOL_LOOKBACK // 2
MIN_BETA_OBS = 30
MIN_UNIVERSE = 15
MIN_LEG_NAMES = 3
BETA_CLIP = 3.0


def _utc(stamp):
    """Coerce a timestamp to tz-aware UTC so it can be compared against funding stamps."""
    value = pd.Timestamp(stamp)
    if value.tzinfo is None:
        return value.tz_localize("UTC")
    return value.tz_convert("UTC")


def _numeric(frame, column):
    """Return a numeric view of ``column``, or ``None`` when the column is absent."""
    if frame is None or column not in frame.columns:
        return None
    return pd.to_numeric(frame[column], errors="coerce")


def _funding_per_bar(funding, decision_time, lookback_bars):
    """8h-equivalent funding accrual per symbol, in units of rate per 8h bar.

    THESIS 4.1 fixes this: sum every settlement falling inside the window and divide by the
    number of 8h bars the window spans. Summing is schedule-agnostic, which is the point --
    Binance settles 8h, 4h, or hourly depending on symbol and regime, and the crowded,
    cap-pinned names are exactly the fast-settling ones. A per-settlement mean would rank them
    systematically too low.

    Positive result means longs pay shorts, so the harvest signal is its negation.
    """
    if funding is None or len(funding) == 0:
        return {}
    if "symbol" not in funding.columns or "funding_rate" not in funding.columns:
        return {}

    stamp_column = None
    for name in ("funding_time", "settlement_time"):
        if name in funding.columns:
            stamp_column = name
            break

    if stamp_column is None:
        # Degraded path only; the protocol documents both stamp columns as present.
        rows = funding.groupby("symbol", sort=False).tail(lookback_bars)
    else:
        stamps = pd.to_datetime(funding[stamp_column], utc=True, errors="coerce")
        start = decision_time - pd.Timedelta(hours=BAR_HOURS * lookback_bars)
        rows = funding.loc[stamps.notna() & (stamps >= start) & (stamps < decision_time)]

    if len(rows) == 0:
        return {}

    rates = pd.to_numeric(rows["funding_rate"], errors="coerce")
    totals = rates.groupby(rows["symbol"].astype(str)).sum(min_count=1)

    accrual = {}
    for symbol, total in totals.items():
        value = float(total)
        if np.isfinite(value):
            accrual[symbol] = value / float(lookback_bars)
    return accrual


def _log_returns(prices):
    """Log returns of a price path, with non-positive and missing prices dropped."""
    path = np.asarray(prices, dtype=float)
    path = path[np.isfinite(path) & (path > 0.0)]
    if path.size < 2:
        return np.empty(0, dtype=float)
    return np.diff(np.log(path))


def _median_quote_volume(frame):
    """Trailing median quote volume, falling back to close * volume when the column is absent."""
    quote = _numeric(frame, "quote_volume")
    if quote is None:
        close = _numeric(frame, "close")
        volume = _numeric(frame, "volume")
        if close is None or volume is None:
            return None
        quote = close * volume
    tail = quote.to_numpy(dtype=float)[-LIQUIDITY_LOOKBACK:]
    tail = tail[np.isfinite(tail)]
    if tail.size == 0:
        return None
    return float(np.median(tail))


def _universe_betas(bars, names):
    """Beta of each name against the equal-weight return of the same set of names.

    Bars are aligned by position from the most recent row rather than by index label. Every
    eligible symbol has an executable open at the decision, so their last rows are the same bar;
    a symbol that stopped trading is absent from ``eligible_symbols`` rather than stale. Position
    alignment therefore holds without assuming anything about the index dtype.

    Any degeneracy leaves the name at beta 1.0, which makes the downstream residualisation a
    no-op rather than a source of scrambled signal.
    """
    count = len(names)
    width = BETA_LOOKBACK + 1
    matrix = np.full((width, count), np.nan, dtype=float)
    for position, symbol in enumerate(names):
        close = _numeric(bars[symbol], "close")
        if close is None:
            continue
        path = close.to_numpy(dtype=float)[-width:]
        if path.size:
            matrix[width - path.size:, position] = path

    matrix[~(matrix > 0.0)] = np.nan
    logs = np.log(matrix)
    returns = logs[1:] - logs[:-1]

    valid = np.isfinite(returns)
    per_row = valid.sum(axis=1)
    totals = np.where(valid, returns, 0.0).sum(axis=1)
    market = np.where(per_row > 0, totals / np.maximum(per_row, 1), np.nan)

    betas = np.ones(count, dtype=float)
    for position, symbol in enumerate(names):
        column = returns[:, position]
        usable = np.isfinite(column) & np.isfinite(market)
        if int(usable.sum()) < MIN_BETA_OBS:
            continue
        reference = market[usable]
        variance = float(np.var(reference, ddof=1))
        if not np.isfinite(variance) or variance <= 0.0:
            continue
        covariance = float(np.cov(column[usable], reference, ddof=1)[0, 1])
        beta = covariance / variance
        if np.isfinite(beta):
            betas[position] = float(np.clip(beta, -BETA_CLIP, BETA_CLIP))
    return betas


def _demeaned_rank(values):
    """Cross-sectional rank mapped to [-1, 1] with mean exactly zero."""
    count = values.size
    if count < 2:
        return np.zeros(count, dtype=float)
    order = np.argsort(values, kind="stable")
    ranks = np.empty(count, dtype=float)
    ranks[order] = np.arange(count, dtype=float)
    return 2.0 * (ranks / float(count - 1)) - 1.0


def _residualise(target, factor):
    """Strip the ``factor`` component out of ``target`` cross-sectionally."""
    centred_factor = factor - factor.mean()
    denominator = float(centred_factor @ centred_factor)
    centred_target = target - target.mean()
    if not np.isfinite(denominator) or denominator <= 0.0:
        return centred_target
    loading = float(centred_target @ centred_factor) / denominator
    return centred_target - loading * centred_factor


class FundingCarryHarvest:
    """Long the most-negative-funding names, short the most-positive, at equal risk.

    Stateless by construction: every decision is recomputed from the context it is handed.
    """

    def target_weights(self, context, *, seed):
        symbols = sorted({str(symbol) for symbol in context.eligible_symbols})
        if len(symbols) < MIN_UNIVERSE:
            return {}

        bars = context.bars
        decision_time = _utc(context.decision_time)
        accrual = _funding_per_bar(context.funding, decision_time, FUNDING_LOOKBACK)
        if not accrual:
            return {}

        # ---- eligibility: funded, seasoned, priced, and liquid -----------------------------
        candidates = []
        for symbol in symbols:
            if symbol not in accrual:
                continue
            frame = bars.get(symbol)
            if frame is None or len(frame) < MIN_BARS:
                continue
            close = _numeric(frame, "close")
            if close is None:
                continue
            returns = _log_returns(close.to_numpy(dtype=float)[-(VOL_LOOKBACK + 1):])
            if returns.size < MIN_VOL_OBS:
                continue
            volatility = float(np.std(returns, ddof=1))
            if not np.isfinite(volatility) or volatility <= 0.0:
                continue
            liquidity = _median_quote_volume(frame)
            if liquidity is None or not np.isfinite(liquidity) or liquidity <= 0.0:
                continue
            candidates.append((symbol, accrual[symbol], volatility, liquidity))

        if len(candidates) < MIN_UNIVERSE:
            return {}

        # ---- universe: top U by trailing median quote volume --------------------------------
        candidates.sort(key=lambda row: -row[3])
        candidates = candidates[:UNIVERSE_SIZE]

        # ---- tail trim on raw funding: cap-pinned prints are not tradeable carry ------------
        candidates.sort(key=lambda row: row[1])
        trim = int(np.floor(TAIL_TRIM * len(candidates)))
        if trim > 0 and len(candidates) > 4 * trim:
            candidates = candidates[trim:len(candidates) - trim]

        names = [row[0] for row in candidates]
        funding_rate = np.array([row[1] for row in candidates], dtype=float)
        volatility = np.array([row[2] for row in candidates], dtype=float)

        # ---- signal: carry-to-risk, ranked, then made orthogonal to universe beta -----------
        # Ranking corrects an exchange-mechanical bias as well as a statistical one: the funding
        # cap scales with the maintenance margin ratio, which is itself larger for riskier alts,
        # so a raw-funding sort mechanically overweights junk.
        carry_to_risk = -funding_rate / volatility
        signal = _demeaned_rank(carry_to_risk)
        signal = _residualise(signal, _universe_betas(bars, names))

        # ---- construction: rank weights inside each leg, exactly dollar-neutral -------------
        count = len(names)
        leg = int(round(LEG_FRACTION * count))
        if leg < MIN_LEG_NAMES:
            return {}

        order = np.argsort(signal, kind="stable")
        short_leg = order[:leg]
        long_leg = order[count - leg:]

        ramp = np.arange(1, leg + 1, dtype=float)
        ramp = ramp / ramp.sum()

        weights = np.zeros(count, dtype=float)
        weights[long_leg] = ramp             # ascending order, so the top-ranked name gets the most
        weights[short_leg] = -ramp[::-1]     # ascending order, so the bottom-ranked name gets the most

        weights = np.clip(weights * (TARGET_GROSS / 2.0), -MAX_ABS_WEIGHT, MAX_ABS_WEIGHT)
        gross = float(np.abs(weights).sum())
        if not np.isfinite(gross) or gross <= 0.0:
            return {}
        if gross > TARGET_GROSS:
            weights = weights * (TARGET_GROSS / gross)

        book = {}
        for position, symbol in enumerate(names):
            weight = float(weights[position])
            if weight != 0.0 and np.isfinite(weight):
                book[symbol] = weight
        return book


def build_strategy():
    return FundingCarryHarvest()
