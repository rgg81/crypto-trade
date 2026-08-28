"""team-08 -- per-contract multi-horizon time-series trend, slow ladder, day-averaged book.

Economic family: time-series trend. Mandate: the CTA transplant -- per-contract, volatility
scaled, multiple lookbacks.

Nomination. This is the trial-t02 mechanism with two changes, both aimed at the cost gates rather
than at Sharpe, and both inside the sealed parameter surface in ``lane/scouting/THESIS.md``.

The evidence is two packets. The seed (t01) traded at 130.5x turnover, earned 14.6 bps of gross
edge per unit of it against a charge of ~7.4-8.0 bps, and failed gross_edge_density, cost_share
and survives_triple_cost. Restricting the ladder to the declared SLOW(5-8) window (t02) cut
turnover 2.54x for only 16% of gross Sharpe (1.56 -> 1.31) and cleared every gate. The two packets
agree on the cost schedule to within 1%, so the trade-off between turnover and edge is the one
quantity here that is measured rather than assumed.

What that measurement says about t02 is that its remaining margin is thin exactly where the seed
died: +2.6% annualised at triple cost, and a density of 28.7 bps against a triple-cost break-even
of ~24. Both are re-enforced on blocks I never see. So the two changes below spend a small,
bounded amount of gross Sharpe to buy margin on those two gates:

1. **The ladder is sampled at sqrt(2) inside the same declared span** -- seven rungs from 45 to
   360 bars instead of four. The mean rung innovation 1/sqrt(L) moves 0.09543 -> 0.09403, so this
   is turnover-neutral by construction. It is a variance-reduction move, not a selection move: no
   per-rung result exists in either packet, so it cannot express hindsight about which lookback
   worked. What it removes is the possibility that a quarter of the book rests on one lucky rung.

2. **The submitted book is the mean of the books this construction would have formed at the last
   three bars** -- one day on an 8h clock. This is the declared Tier-2 cadence R = "every 3 bars
   (daily)" expressed continuously rather than as a discrete schedule. A discrete daily rebalance
   would be calendar-anchored and would trade in lumps; the running mean is calendar-shift
   equivariant, has no threshold, and reduces per-bar position innovation by ~1/sqrt(3) while
   costing a mean lag of one bar on a 45-360 bar signal. A signal with a 15-120 day horizon has no
   business re-trading three times a day; the extra two decisions are close to pure noise-trading.

Every recomputation reads only rows at or before its own anchor bar, so the average is over past
books and introduces no look-ahead; the funding drag and the universe are held at the decision
bar, which is information available at the decision.

Construction, per contract and nothing else -- no cross-sectional rank, no relative strength, no
market-wide state variable, no volatility gate or exposure throttle (THESIS 0 and 5):

    z_L,j = (log return over L bars ending at t-j - funding paid over L bars) / (sigma_j * sqrt(L))
    g_j   = mean over available rungs of tanh(z_L,j)
    w_raw = mean over j in {0,1,2} of g_j / sigma_j
    w     = w_raw normalised to gross, concentration-capped, net-capped

Because the design is strictly per-contract it never builds a cross-symbol panel, so the
positional-RangeIndex alignment trap in RULES.md does not arise: every read is positional inside
a single symbol's frame, whose rows are ordered oldest to newest and truncated at the boundary.

Statelessness: the strategy object holds no attributes and every call is a pure function of the
context. No RNG, no absolute dates, no symbol identity, no price levels -- only log returns,
z-scores and volume ranks, all invariant to a magnitude rescale.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# --- Ladder: the declared Tier-1 window W = SLOW(5-8), sampled at sqrt(2) inside the same span.
# 8h bars, so {45 ... 360} bars ~ {15 ... 120} days. Same endpoints as the declared window; the
# added rungs are interpolations of it, chosen by spacing rule and not by any measured result.
LADDER = (45, 64, 90, 127, 180, 254, 360)

# Book smoothing: the mean of the books formed at the last SMOOTH_LAGS bars = one day on an 8h
# clock. Declared Tier-2 cadence R = daily, expressed as a running mean rather than a schedule.
SMOOTH_LAGS = 3

# Per-contract ex-ante volatility: EWMA of squared bar log returns (MOP form). Declared Tier-2
# estimator V = com 180 bars (~60d), matched to the centre of gravity of the slow ladder. A vol
# estimate faster than the signal injects weight churn that carries no directional information.
VOL_COM = 180.0
VOL_MAX_LAG = 1500
MIN_VOL_OBS = 60

# Data adequacy: 200 usable bars at every smoothing lag, so MIN_HISTORY carries the extra lags.
# 200 bars makes rungs 45/64/90/127/180 available and gives the com-180 EWMA an effective sample
# of roughly 120 observations. The two longest rungs are used when history allows.
MIN_BARS = 200
MIN_HISTORY = MIN_BARS + SMOOTH_LAGS - 1
MIN_RUNGS = 4

# Universe: declared Tier-1 breadth axis N = 30, ranked on a long trailing median of quote
# volume so that the membership edge is stable and does not churn positions on its own.
LIQ_WINDOW = 270
UNIVERSE_N = 30
MIN_UNIVERSE = 5

# Book constraints. Gross 1.0 is the submitted shape; the organizer owns the ex-ante risk unit
# and rescales before re-applying caps, so the submitted level only matters through the caps.
GROSS = 1.0
NET_CAP = 0.20          # inside the hard |net| <= 0.25
MAX_WEIGHT = 0.09       # inside the hard per-symbol |w| <= 0.10
CONC_MULT = 3.0         # THESIS 7.1 concentration cap: 3x median contract weight
DUST = 1e-4

DEFAULT_BAR_HOURS = 8.0
DEFAULT_FUNDING_HOURS = 8.0
MIN_HOURS = 0.05
MAX_HOURS = 168.0
RESERVED_PREFIX = "__"


def _as_float_array(col: pd.Series) -> np.ndarray:
    """Return ``col`` as a float ndarray without assuming its stored dtype."""
    arr = col.to_numpy(copy=False)
    if arr.dtype.kind == "f":
        return arr
    return pd.to_numeric(col, errors="coerce").to_numpy(dtype=float, copy=False)


def _epoch_ns(col: pd.Series) -> np.ndarray | None:
    """Nanoseconds since epoch for a timestamp column, tz-aware or naive, or None.

    Total by construction: the bar-spacing caller has a declared fallback and is not otherwise
    guarded, so any dtype surprise here must degrade to that fallback rather than abort the
    decision and leave the book flat.
    """
    try:
        dtype = col.dtype
        if isinstance(dtype, pd.DatetimeTZDtype):
            return col.dt.tz_convert("UTC").astype("int64").to_numpy(copy=False)
        if dtype.kind == "M":
            return col.astype("int64").to_numpy(copy=False)
        conv = pd.to_datetime(col, errors="coerce", utc=True)
        if conv.isna().all():
            return None
        return conv.astype("int64").to_numpy(copy=False)
    except Exception:
        return None


def _median_spacing_hours(col: pd.Series, default: float) -> float:
    """Median positive spacing of a timestamp column, in hours, with a declared fallback."""
    tail = col.iloc[-65:] if len(col) > 65 else col
    if len(tail) < 3:
        return default
    ns = _epoch_ns(tail)
    if ns is None:
        return default
    gaps = np.diff(ns)
    gaps = gaps[gaps > 0]
    if gaps.size == 0:
        return default
    hours = float(np.median(gaps)) / 3.6e12
    if not (MIN_HOURS <= hours <= MAX_HOURS):
        return default
    return hours


def _decay_weights(size: int, com: float) -> np.ndarray:
    """Adjusted-EWMA weights for a window of ``size`` observations, oldest first.

    The weights of a shorter window are exactly the tail of those of a longer one, so a caller
    that evaluates the same EWMA at several nearby anchors builds this array once and slices it.
    """
    lam = com / (1.0 + com)
    ages = np.arange(size - 1, -1, -1, dtype=float)
    return lam**ages


def _ewma_last(values: np.ndarray, weights: np.ndarray) -> float:
    """Final value of an adjusted EWMA over ``values``, computed without a Python loop."""
    n = values.size
    if n == 0:
        return float("nan")
    window = values[-weights.size :] if n > weights.size else values
    tail = weights[-window.size :]
    total = float(tail.sum())
    if not np.isfinite(total) or total <= 0.0:
        return float("nan")
    return float(np.dot(tail, window) / total)


def _clean_closes(frame: pd.DataFrame) -> np.ndarray | None:
    """Longest usable suffix of strictly positive, finite closes, or None.

    The length floor is ``MIN_HISTORY`` rather than ``MIN_BARS`` so that every smoothing lag sees
    at least ``MIN_BARS`` usable observations and all three books rest on the same ladder depth.
    """
    if "close" not in frame.columns:
        return None
    close = _as_float_array(frame["close"])
    if close.size < MIN_HISTORY:
        return None
    good = np.isfinite(close) & (close > 0.0)
    if not bool(good[-1]):
        return None
    if not bool(good.all()):
        start = int(np.flatnonzero(~good)[-1]) + 1
        close = close[start:]
        if close.size < MIN_HISTORY:
            return None
    return close


def _liquidity(frame: pd.DataFrame) -> float:
    """Trailing median quote volume; the universe rank is computed on a past-only window."""
    if "quote_volume" not in frame.columns:
        return float("nan")
    vol = _as_float_array(frame["quote_volume"])
    vol = vol[-LIQ_WINDOW:]
    vol = vol[np.isfinite(vol)]
    if vol.size == 0:
        return float("nan")
    return float(np.median(vol))


def _funding_drag(
    funding: pd.DataFrame,
    chosen: list[str],
    decision_ns: int,
    span_ns: int,
    bar_hours: float,
) -> dict[str, float]:
    """Per-symbol funding paid by a long, per bar, over the trailing ladder span.

    THESIS 1.6: a perpetual long pays funding three times a day by contract design, so the
    tradeable return of a long is the price return net of funding. This is the declared Tier-2
    signal basis B = funding-inclusive total return -- funding as a property of the return being
    measured, never as a carry signal (THESIS 5). Any malformation degrades to price-only rather
    than to an empty book.

    Held fixed across the smoothing lags: it is a trailing mean over the full ladder span, so
    re-anchoring it one or two bars back would move it by far less than the noise it carries, and
    holding it fixed keeps it from contributing any turnover at all.
    """
    empty: dict[str, float] = {}
    if not isinstance(funding, pd.DataFrame) or len(funding) == 0:
        return empty
    if not {"symbol", "funding_rate", "funding_time"}.issubset(funding.columns):
        return empty
    try:
        stamps = _epoch_ns(funding["funding_time"])
        if stamps is None:
            return empty
        recent = funding.loc[stamps >= decision_ns - span_ns]
        if len(recent) == 0:
            return empty
        recent = recent.loc[recent["symbol"].isin(chosen)]
        if len(recent) == 0:
            return empty

        head = recent.loc[recent["symbol"] == chosen[0], "funding_time"]
        funding_hours = _median_spacing_hours(head, DEFAULT_FUNDING_HOURS)
        per_bar = bar_hours / funding_hours
        if not (0.02 <= per_bar <= 48.0):
            per_bar = 1.0

        rates = pd.to_numeric(recent["funding_rate"], errors="coerce")
        means = rates.groupby(recent["symbol"], sort=False).mean()
        drag: dict[str, float] = {}
        for symbol, value in means.items():
            rate = float(value)
            if np.isfinite(rate):
                drag[str(symbol)] = rate * per_bar
        return drag
    except Exception:
        return empty


def _smoothed_raw_weight(close: np.ndarray, carry: float) -> float:
    """Mean over the last ``SMOOTH_LAGS`` bars of the inverse-vol-scaled ladder blend.

    Each lag ``j`` is a self-contained rebuild of the per-contract weight using only rows at or
    before bar ``t-j``: its own EWMA volatility, its own rung returns. Returns NaN unless every
    lag is supportable, so a contract is never carried on an unevenly-anchored average.
    """
    log_price = np.log(close)
    rets = np.diff(log_price)
    squared = rets * rets
    # One weight vector for all lags: the lagged windows are nested, so the shorter ones slice it.
    weights = _decay_weights(min(rets.size, VOL_MAX_LAG), VOL_COM)

    accumulated = 0.0
    for lag in range(SMOOTH_LAGS):
        end = rets.size - lag
        if end < MIN_VOL_OBS:
            return float("nan")
        variance = _ewma_last(squared[:end], weights)
        if not np.isfinite(variance) or variance <= 0.0:
            return float("nan")
        sigma = math.sqrt(variance)
        if not np.isfinite(sigma) or sigma <= 0.0:
            return float("nan")

        anchor = log_price.size - 1 - lag
        total = 0.0
        used = 0
        for rung in LADDER:
            if anchor - rung < 0:
                continue
            # Signal on bar (t-lag)'s close; the engine fills at the next executable open.
            excess = float(log_price[anchor] - log_price[anchor - rung]) - carry * rung
            z = excess / (sigma * math.sqrt(rung))
            if not np.isfinite(z):
                continue
            # Declared Tier-1 transform T = tanh: bounded, saturating and everywhere continuous,
            # so no threshold crossing can manufacture a round trip.
            total += math.tanh(z)
            used += 1
        if used < MIN_RUNGS:
            return float("nan")

        accumulated += (total / used) / sigma

    return accumulated / float(SMOOTH_LAGS)


class SlowLadderTrend:
    """Per-contract, volatility-scaled trend over the slow half of a fixed log-spaced ladder."""

    def target_weights(self, context, *, seed):
        bars = getattr(context, "bars", None)
        raw_symbols = getattr(context, "eligible_symbols", None)
        if bars is None or not raw_symbols:
            return None
        symbols = [s for s in raw_symbols if not str(s).startswith(RESERVED_PREFIX)]
        if not symbols:
            return None

        # --- universe: stable trailing-liquidity rank, past-only, no symbol identity ---
        ranked: list[tuple[float, str]] = []
        for symbol in symbols:
            frame = bars.get(symbol)
            if frame is None or len(frame) < MIN_HISTORY:
                continue
            liquidity = _liquidity(frame)
            if np.isfinite(liquidity) and liquidity > 0.0:
                ranked.append((liquidity, symbol))
        if len(ranked) < MIN_UNIVERSE:
            return None
        # Stable sort on liquidity alone: ties keep organizer order, never symbol identity.
        ranked.sort(key=lambda pair: -pair[0])
        chosen = [symbol for _, symbol in ranked[:UNIVERSE_N]]

        reference = bars[chosen[0]]
        bar_hours = DEFAULT_BAR_HOURS
        if "open_time" in reference.columns:
            bar_hours = _median_spacing_hours(reference["open_time"], DEFAULT_BAR_HOURS)

        drag: dict[str, float] = {}
        moment = getattr(context, "decision_time", None)
        if moment is not None:
            try:
                stamp = pd.Timestamp(moment)
                stamp = stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp
                span_ns = int(bar_hours * max(LADDER) * 3.6e12)
                drag = _funding_drag(
                    getattr(context, "funding", None),
                    chosen,
                    int(stamp.value),
                    span_ns,
                    bar_hours,
                )
            except Exception:
                drag = {}

        # --- per-contract signal: nothing here reads any other contract ---
        names: list[str] = []
        weights: list[float] = []
        for symbol in chosen:
            close = _clean_closes(bars[symbol])
            if close is None:
                continue
            weight = _smoothed_raw_weight(close, drag.get(symbol, 0.0))
            if np.isfinite(weight):
                names.append(symbol)
                weights.append(weight)

        if len(names) < MIN_UNIVERSE:
            return None

        book = np.asarray(weights, dtype=float)
        gross = float(np.abs(book).sum())
        if not np.isfinite(gross) or gross <= 0.0:
            return None
        book *= GROSS / gross

        # --- concentration cap: 3x median contract weight (THESIS 7.1, risk hygiene) ---
        # Floored at the equal-weight level: a concentration cap can never sensibly sit below the
        # weight every name would carry if the book were flat, and the floor also keeps the
        # renormalisation feasible (cap * n >= GROSS) when the cross-section is degenerate.
        median_weight = float(np.median(np.abs(book)))
        cap = min(MAX_WEIGHT, max(CONC_MULT * median_weight, GROSS / book.size))
        book = np.clip(book, -cap, cap)
        gross = float(np.abs(book).sum())
        if gross <= 0.0:
            return None
        book *= GROSS / gross
        book = np.clip(book, -MAX_WEIGHT, MAX_WEIGHT)

        # --- net cap: shrink the dominant side proportionally, continuously at the boundary ---
        longs = book > 0.0
        shorts = book < 0.0
        long_sum = float(book[longs].sum())
        short_sum = float(-book[shorts].sum())
        net = long_sum - short_sum
        # Solving f * long_sum - short_sum = +NET_CAP (or long_sum - f * short_sum = -NET_CAP)
        # gives f in (0, 1) exactly when the cap binds, so f -> 1 as net -> the boundary.
        if net > NET_CAP and long_sum > 0.0:
            book[longs] *= (short_sum + NET_CAP) / long_sum
        elif net < -NET_CAP and short_sum > 0.0:
            book[shorts] *= (long_sum + NET_CAP) / short_sum

        # --- emit ---
        targets: dict[str, float] = {}
        for symbol, value in zip(names, book):
            weight = float(value)
            if np.isfinite(weight) and abs(weight) >= DUST:
                targets[symbol] = weight
        if not targets:
            return None

        gross = sum(abs(w) for w in targets.values())
        if gross > 1.0:
            targets = {k: v / gross for k, v in targets.items()}
        # Belt and braces: NET_CAP and the gross cap already imply |net| <= 0.20, so this only
        # ever fires on an arithmetic surprise. Scale the whole book rather than one side, which
        # lands on the limit exactly and cannot raise gross.
        net = sum(targets.values())
        if abs(net) > 0.25:
            shrink = 0.25 / abs(net)
            targets = {k: v * shrink for k, v in targets.items()}
        return targets


def build_strategy():
    """Factory: one clean, attribute-free instance per run."""
    return SlowLadderTrend()
