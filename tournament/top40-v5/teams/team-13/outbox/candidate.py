"""team-13 — universe inclusion and attention (discovery baseline).

The mandate is *event and state*: trade weekly membership entry and exit.

This book states that in its most direct form.

  * The **event** decides *who is in the book*. A weekly liquidity-ranked universe turns over
    because a symbol's trailing dollar volume crosses its peers. That crossing is reconstructed
    here from bars alone -- trailing-week notional rank versus its own three-week baseline rank --
    plus a listing-recency channel for names too young to have a baseline (a brand-new member is
    the purest entrant there is).

  * The **state** decides *the sign and the size*. Crowdedness of leveraged positioning going into
    the transition, proxied by the trailing-week funding level and by taker-buy aggressor skew,
    both standardised cross-sectionally. The book is short the crowded side of a transition and
    long the uncrowded side.

The entrant leg and the leaver leg use the same function, and that is the point. An entrant is an
excess-demand shock: if the crowd is paying to be long it must unwind, so fade it. A leaver is an
excess-supply shock: the forced closers are selling, funding goes negative, so buy it. "Short the
crowded side" produces the entrant/leaver mirror without a hand-flipped sign.

Everything is recomputed from ``DecisionContext`` at every decision. No persistent state, no RNG,
no absolute dates, no symbol identity, no price levels -- only ranks, ratios and rates.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# --- Structural constants (thesis §4.1, fixed rather than searched) -------------------------
BARS_PER_WEEK_FALLBACK = 21  # Binance funding settles every 8h -> 21 bars per week ([C10]).
FUNDING_ROWS_PER_WEEK = 21  # Funding prints are on the same 8h grid.
EVENT_HORIZON_WEEKS = 3  # Post-event holding horizon H (thesis §4.2 knob 1, upper level).
BASELINE_WEEKS = 3  # Rank baseline spans the three weeks preceding the trailing week.
Z_CLIP = 3.0  # Signal transform: clip standardised scores at ±3.

# --- Portfolio construction constants -------------------------------------------------------
GROSS_TARGET = 0.98  # Hard cap is sum(|w|) <= 1.0.
MAX_WEIGHT = 0.08  # Hard cap is |w| <= 0.10; the headroom forces breadth.
NET_LIMIT = 0.15  # Hard cap is |sum(w)| <= 0.25.
DUST_WEIGHT = 1e-3  # Below this a line is noise, not a position.
LIQUIDITY_FLOOR = 0.10  # Drop names below 10% of median trailing notional: untradeable, not cheap.
MIN_UNIVERSE = 10
MIN_BOOK = 6


def _bars_per_week(frames):
    """Infer bars per seven days from timestamp spacing, falling back to the 8h grid.

    Assuming the bar frequency would be a silent failure mode: every window in this file is
    expressed in weeks, so a wrong step size would quietly mis-scale every lookback.
    """
    for frame in frames:
        index = getattr(frame, "index", None)
        if not isinstance(index, pd.DatetimeIndex) or len(index) < 9:
            continue
        step = pd.Series(index[-9:]).diff().dt.total_seconds().median()
        if step is None or not np.isfinite(step) or step <= 0:
            continue
        return int(max(2, min(400, round(7.0 * 86400.0 / float(step)))))
    return BARS_PER_WEEK_FALLBACK


def _numeric(frame, column):
    """Return a float array for ``column``, or ``None`` when the column is absent."""
    if column not in frame.columns:
        return None
    values = np.asarray(frame[column].to_numpy(), dtype="float64")
    return values if values.size else None


def _notional(frame):
    """Per-bar quote (dollar) volume, with a close x volume fallback."""
    quote = _numeric(frame, "quote_volume")
    if quote is not None and np.nansum(quote) > 0.0:
        return quote
    close = _numeric(frame, "close")
    volume = _numeric(frame, "volume")
    if close is None or volume is None or close.size != volume.size:
        return None
    return close * volume


def _taker_skew(frame, window):
    """Aggressor buy share of the trailing window, centred on zero.

    The only independent order-flow direction signal in the dataset. It is a ratio, so it is
    invariant to any common rescaling of prices or of contract size.
    """
    for buy_col, all_col in (
        ("taker_buy_quote_volume", "quote_volume"),
        ("taker_buy_volume", "volume"),
    ):
        buys = _numeric(frame, buy_col)
        total = _numeric(frame, all_col)
        if buys is None or total is None or buys.size != total.size:
            continue
        denominator = float(np.nansum(total[-window:]))
        if not np.isfinite(denominator) or denominator <= 0.0:
            continue
        numerator = float(np.nansum(buys[-window:]))
        if not np.isfinite(numerator):
            continue
        return numerator / denominator - 0.5
    return np.nan


def _funding_means(funding, symbols, rows):
    """Mean funding rate over each symbol's last ``rows`` prints (its trailing week).

    Taking a tail count rather than filtering on a timestamp keeps this free of any absolute-date
    or dtype assumption; the frame is already restricted to rows strictly before the decision.
    """
    means = {}
    columns = getattr(funding, "columns", None)
    if columns is None or len(funding) == 0:
        return means
    if "symbol" not in columns or "funding_rate" not in columns:
        return means

    frame = funding[funding["symbol"].isin(set(symbols))]
    if len(frame) == 0:
        return means

    for time_column in ("funding_time", "settlement_time"):
        if time_column in columns:
            frame = frame.sort_values(time_column, kind="mergesort")
            break

    tail = frame.groupby("symbol", sort=False).tail(rows)
    for symbol, value in tail.groupby("symbol", sort=False)["funding_rate"].mean().items():
        rate = float(value)
        if np.isfinite(rate):
            means[symbol] = rate
    return means


def _pct_rank(values):
    """Tie-averaged percentile rank in [0, 1]. Rank-based, so scale- and level-invariant."""
    array = np.asarray(values, dtype="float64")
    size = array.size
    if size < 2:
        return np.full(size, 0.5, dtype="float64")
    ranks = np.zeros(size, dtype="float64")
    order = np.argsort(array, kind="mergesort")
    ordered = array[order]
    start = 0
    while start < size:
        stop = start
        while stop + 1 < size and ordered[stop + 1] == ordered[start]:
            stop += 1
        ranks[order[start : stop + 1]] = 0.5 * (start + stop)
        start = stop + 1
    return ranks / (size - 1)


def _robust_z(values):
    """Median/MAD cross-sectional score, clipped. Non-finite entries score zero."""
    array = np.asarray(values, dtype="float64")
    scores = np.zeros(array.size, dtype="float64")
    finite = np.isfinite(array)
    if int(finite.sum()) < 4:
        return scores
    sample = array[finite]
    deviation = sample - float(np.median(sample))
    scale = 1.4826 * float(np.median(np.abs(deviation)))
    if not np.isfinite(scale) or scale <= 0.0:
        scale = float(np.std(sample))
    if not np.isfinite(scale) or scale <= 0.0:
        return scores
    scores[finite] = np.clip(deviation / scale, -Z_CLIP, Z_CLIP)
    return scores


def _shape_book(scores, target, cap):
    """Water-fill to a gross of ``target`` with no line above ``cap``."""
    weights = np.asarray(scores, dtype="float64").copy()
    for _ in range(12):
        gross = float(np.abs(weights).sum())
        if gross <= 0.0:
            return weights
        weights = np.clip(weights * (target / gross), -cap, cap)
    return weights


def _cap_net(weights, limit):
    """Shrink the dominant side until net exposure is inside ``limit``."""
    net = float(weights.sum())
    if abs(net) <= limit:
        return weights
    dominant = weights > 0.0 if net > 0.0 else weights < 0.0
    side_gross = float(np.abs(weights[dominant]).sum())
    if side_gross <= 0.0:
        return weights
    factor = max(0.0, (side_gross - (abs(net) - limit)) / side_gross)
    adjusted = weights.copy()
    adjusted[dominant] = adjusted[dominant] * factor
    return adjusted


class InclusionAttentionBook:
    """Membership transition selects the names; leveraged crowding signs and sizes them."""

    def target_weights(self, context, *, seed):
        symbols = list(getattr(context, "eligible_symbols", ()) or ())
        bars = getattr(context, "bars", {}) or {}

        frames = {}
        for symbol in symbols:
            frame = bars.get(symbol)
            if frame is None or not hasattr(frame, "columns") or len(frame) == 0:
                continue
            frames[symbol] = frame
        if len(frames) < MIN_UNIVERSE:
            return {}

        week = _bars_per_week(frames.values())
        horizon = EVENT_HORIZON_WEEKS * week
        baseline_span = BASELINE_WEEKS * week

        names, recent_dv, baseline_dv, skew, age = [], [], [], [], []
        for symbol, frame in frames.items():
            notional = _notional(frame)
            if notional is None:
                continue
            recent = notional[-week:]
            if recent.size == 0:
                continue
            recent_mean = float(np.nansum(recent)) / recent.size
            if not np.isfinite(recent_mean) or recent_mean <= 0.0:
                continue

            # The baseline is the BASELINE_WEEKS window ending one week back; Python slicing
            # clamps it for young symbols, and short baselines are discarded below.
            baseline = notional[-(week + baseline_span) : -week]
            if baseline.size >= max(2, week // 2):
                baseline_mean = float(np.nansum(baseline)) / baseline.size
                if not np.isfinite(baseline_mean) or baseline_mean <= 0.0:
                    baseline_mean = np.nan
            else:
                baseline_mean = np.nan

            names.append(symbol)
            recent_dv.append(recent_mean)
            baseline_dv.append(baseline_mean)
            skew.append(_taker_skew(frame, week))
            age.append(float(len(frame)))

        if len(names) < MIN_UNIVERSE:
            return {}

        recent_dv = np.asarray(recent_dv, dtype="float64")
        baseline_dv = np.asarray(baseline_dv, dtype="float64")
        age = np.asarray(age, dtype="float64")

        # Names an order of magnitude below the median are not cheap, they are untradeable.
        keep = recent_dv >= LIQUIDITY_FLOOR * float(np.median(recent_dv))
        if int(keep.sum()) < MIN_UNIVERSE:
            return {}
        names = [name for name, alive in zip(names, keep) if alive]
        skew = [value for value, alive in zip(skew, keep) if alive]
        recent_dv, baseline_dv, age = recent_dv[keep], baseline_dv[keep], age[keep]

        # --- Event: the weekly membership transition, reconstructed from the tape ------------
        # Trailing-week notional rank minus the same symbol's rank over the preceding three
        # weeks. Positive means climbing into the universe, negative means falling out of it.
        rank_change = np.zeros(len(names), dtype="float64")
        has_baseline = np.isfinite(baseline_dv)
        indices = np.where(has_baseline)[0]
        if indices.size >= 4:
            rank_change[indices] = _pct_rank(recent_dv[indices]) - _pct_rank(baseline_dv[indices])

        # A symbol too young to have a baseline is a fresh member by construction. Its event
        # weight decays linearly to zero over the holding horizon.
        recency = np.clip(1.0 - age / float(horizon), 0.0, 1.0)

        intensity = np.maximum(np.abs(rank_change), recency)
        # Smooth top-half gate: zero weight and zero derivative at the median, so no name sits on
        # a threshold that a small perturbation could flip.
        event = np.clip((_pct_rank(intensity) - 0.5) * 2.0, 0.0, 1.0) ** 2

        # --- State: crowdedness of leveraged positioning -------------------------------------
        funding_means = _funding_means(
            getattr(context, "funding", None), names, FUNDING_ROWS_PER_WEEK
        )
        funding = np.asarray(
            [funding_means.get(name, np.nan) for name in names], dtype="float64"
        )
        crowding = 0.5 * _robust_z(funding) + 0.5 * _robust_z(np.asarray(skew, dtype="float64"))

        # --- Book: short the crowded side of a transition, long the uncrowded side ------------
        selected = np.where(event > 0.0)[0]
        if selected.size < MIN_BOOK:
            return {}

        scores = event[selected] * (-crowding[selected])
        scores = scores - float(scores.mean())
        if float(np.abs(scores).sum()) <= 0.0:
            return {}

        weights = _cap_net(_shape_book(scores, GROSS_TARGET, MAX_WEIGHT), NET_LIMIT)

        book = {}
        for position, weight in zip(selected, weights):
            value = float(weight)
            if np.isfinite(value) and abs(value) >= DUST_WEIGHT:
                book[names[position]] = value
        return book if len(book) >= MIN_BOOK else {}


def build_strategy():
    return InclusionAttentionBook()
