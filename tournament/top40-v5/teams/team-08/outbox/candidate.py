"""team-08 -- per-contract multi-horizon time-series trend, slow ladder.

Economic family: time-series trend. Mandate: the CTA transplant -- per-contract, volatility
scaled, multiple lookbacks.

Refinement candidate. Trial t01 (unmodified organizer seed) passed every structural gate --
effective breadth 21.4, mean gross 0.478, participation 1.0, long/short exposure 50.6/49.4,
turnover inside the band -- and failed exactly three: gross_edge_density, cost_share and
survives_triple_cost. Those three are one disease. The seed earned about 14.6 bps of gross edge
per unit turnover against a charge of about 7.4 bps at 1x, so it needs roughly 22.3 bps to break
even at 3x. Its signal is not the problem; the frequency at which it spends that signal is.

Two design consequences, both structural rather than parametric:

1. The preregistered no-trade band (THESIS 7.1) is a position-space control and cannot be
   implemented here. DecisionContext exposes no position and persistent state is forbidden, so
   turnover has to be designed into the signal path rather than filtered out afterwards. Every
   map below from data to weight is therefore continuous, and the weight path is smooth because
   the signal is smooth -- not because trades are suppressed.

2. Equal-weighting the eight preregistered rungs equalizes each rung's contribution to risk but
   not to cost. Under a random-walk null a rung-L z-score has per-bar innovation sqrt(2/L), so
   the fast four rungs {3,6,12,21} carry half the risk and about four fifths of the position
   innovation. Edge per unit turnover scales as sqrt(L) while per-market Sharpe is roughly flat
   in L, so the fast rungs are funded by the slow rungs' edge. Restricting the ladder to the
   declared SLOW(5-8) window predicts a turnover reduction of about 2.45x.

Construction, per contract and nothing else -- no cross-sectional rank, no relative strength, no
market-wide state variable, no volatility gate or exposure throttle (THESIS 0 and 5):

    z_L   = (log return over L bars - funding paid over L bars) / (sigma * sqrt(L))
    g     = mean over available rungs of tanh(z_L)
    w_raw = g / sigma
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

# --- Ladder: the declared Tier-1 window W = SLOW(5-8) of the preregistered 8-rung ladder.
# 8h bars, so {45, 90, 180, 360} bars ~ {15d, 30d, 60d, 120d}.
LADDER = (45, 90, 180, 360)

# Per-contract ex-ante volatility: EWMA of squared bar log returns (MOP form). Declared Tier-2
# estimator V = com 180 bars (~60d), matched to the centre of gravity of the slow ladder. A vol
# estimate faster than the signal injects weight churn that carries no directional information.
VOL_COM = 180.0
VOL_MAX_LAG = 1500

# Data adequacy: 200 bars makes rungs 45/90/180 available and gives the com-180 EWMA an
# effective sample of roughly 120 observations. Rung 360 is used when history allows.
MIN_BARS = 200
MIN_RUNGS = 2

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


def _ewma_last(values: np.ndarray, com: float, max_lag: int) -> float:
    """Final value of an adjusted EWMA over ``values``, computed without a Python loop."""
    n = values.size
    if n == 0:
        return float("nan")
    window = values[-max_lag:] if n > max_lag else values
    lam = com / (1.0 + com)
    ages = np.arange(window.size - 1, -1, -1, dtype=float)
    weights = lam**ages
    total = float(weights.sum())
    if not np.isfinite(total) or total <= 0.0:
        return float("nan")
    return float(np.dot(weights, window) / total)


def _clean_closes(frame: pd.DataFrame) -> np.ndarray | None:
    """Longest usable suffix of strictly positive, finite closes, or None."""
    if "close" not in frame.columns:
        return None
    close = _as_float_array(frame["close"])
    if close.size < MIN_BARS:
        return None
    good = np.isfinite(close) & (close > 0.0)
    if not bool(good[-1]):
        return None
    if not bool(good.all()):
        start = int(np.flatnonzero(~good)[-1]) + 1
        close = close[start:]
        if close.size < MIN_BARS:
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
            if frame is None or len(frame) < MIN_BARS:
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
            log_price = np.log(close)
            rets = np.diff(log_price)
            variance = _ewma_last(rets * rets, VOL_COM, VOL_MAX_LAG)
            if not np.isfinite(variance) or variance <= 0.0:
                continue
            sigma = math.sqrt(variance)
            if not np.isfinite(sigma) or sigma <= 0.0:
                continue

            carry = drag.get(symbol, 0.0)
            total = 0.0
            used = 0
            for rung in LADDER:
                if rets.size < rung:
                    continue
                # Signal on bar t's close; the engine fills at the next executable open.
                excess = float(log_price[-1] - log_price[-1 - rung]) - carry * rung
                z = excess / (sigma * math.sqrt(rung))
                if not np.isfinite(z):
                    continue
                # Declared Tier-1 transform T = tanh: bounded, saturating and everywhere
                # continuous, so no threshold crossing can manufacture a round trip.
                total += math.tanh(z)
                used += 1
            if used < MIN_RUNGS:
                continue

            weight = (total / used) / sigma
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
