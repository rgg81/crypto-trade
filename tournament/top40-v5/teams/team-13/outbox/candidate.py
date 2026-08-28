"""team-13 -- universe inclusion and attention (nomination).

Mandate: trade weekly membership entry and exit. Family: event and state.

    score = - (inclusion / attention intensity) x (crowdedness of leveraged positioning)

which is the sign preregistered in the sealed thesis, quadrant by quadrant:

    entrant x crowded    -> short   sell immediacy to the attention crowd, collect funding
    entrant x uncrowded  -> long    genuine liquidity migration, not an attention shock
    leaver  x crowded    -> long    buy inventory from holders facing an exit clock
    leaver  x uncrowded  -> short   sell to forced short-coverers into the same clock

``DecisionContext`` carries no membership history, so the event is reconstructed at every
decision from past-only rows: contract seasoning (how newly the name exists at all -- the
one unambiguous membership observable) and a trailing dollar-volume rank crossing.

Three things separate this from the earlier trial, and all three come from one measured
fact: this lane charges roughly 7.3 bps per unit of annualised turnover, so every unit of
turnover must carry ~22 bps of gross edge to survive triple cost.

  1. The holding kernel runs six weeks rather than three. Turnover is the denominator of
     every gate that is failing; doubling the hold roughly doubles edge density.
  2. Weights are ceilinged by each name's own share of tradeable volume. Entrants and
     leavers are the thinnest names in the universe; asking for size the tape cannot
     absorb is paid for twice, once in impact and once in turnover spent re-requesting a
     target the evaluator truncates.
  3. Crowding is measured as the residual of funding and taker skew on cross-sectional
     volatility. Funding is the price of leverage and that price rises with the
     volatility of the underlying, so raw funding rank is a volatility rank wearing a
     crowding costume -- and a book short the high-funding names is then structurally
     short the high-volatility names, which is preregistered failure mode #3.

A contract's size ramps in linearly over the holding horizon, because the kernel divides
by its full mass rather than by the mass the name was present for. The book is therefore
tilted toward young names by signal and bounded in them by size -- the mandate asks for
the inclusion effect to be modelled explicitly rather than discovered by accident.

Stateless. Every number is recomputed from the context at every decision.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

__all__ = ["build_strategy"]

# --- calendar inference ---------------------------------------------------------------
_WEEK_NS = 7 * 24 * 3600 * 1_000_000_000
_DEFAULT_WEEK_BARS = 21  # 8h bars: one week, one funding settlement per bar
_MIN_WEEK_BARS = 4
_MAX_WEEK_BARS = 84

# --- declared windows -----------------------------------------------------------------
_HORIZON_WEEKS = 6  # H: length of the linear-decay holding kernel
_BASELINE_WEEKS = 3  # rank crossing compares the last week with the preceding two
_STATE_WEEKS = 3  # L_z = 63 bars, the declared slow crowding lookback
_LAG_NODES_PER_WEEK = 3  # sampling density of the kernel

# --- construction ---------------------------------------------------------------------
_MIN_FUNDING_OBS = 3
_MIN_NAMES = 10
_SOFT_THRESHOLD = 0.40  # in cross-sectional sigma of the final score
_CAP_FLOOR = 0.15  # thinnest names keep 15% of the per-name ceiling, not zero
_MAX_WEIGHT = 0.10  # hard limit
_MAX_NET = 0.20  # hard limit is 0.25
_GROSS_TARGET = 0.98  # hard limit is 1.0
_DUST = 1e-6

_NAT = np.iinfo(np.int64).min
_EMPTY_TIMES = np.zeros(0, dtype="int64")
_EMPTY_CUM = np.zeros(1, dtype=float)


# --- pure helpers ---------------------------------------------------------------------
def _epoch_ns(values) -> np.ndarray:
    """Monotone integer time key. Only ordering and spacing are ever used."""
    stamps = pd.to_datetime(pd.Series(np.asarray(values)), utc=True, errors="coerce")
    return stamps.dt.tz_localize(None).to_numpy().astype("int64")


def _csum(values: np.ndarray) -> np.ndarray:
    """Prefix sums with a leading zero, so any window sum is one subtraction."""
    return np.concatenate((np.zeros(1, dtype=float), np.cumsum(values)))


def _rank_unit(values: np.ndarray) -> np.ndarray:
    """Cross-sectional rank mapped to [-1, 1]. Non-finite entries map to 0 (neutral).

    Rank rather than z deliberately: alt-perp volume and funding cross-sections carry
    outliers that would otherwise set the scale for every other name, and a bounded score
    keeps the product of two components bounded.
    """
    out = np.zeros(values.shape[0], dtype=float)
    usable = np.isfinite(values)
    count = int(usable.sum())
    if count < 3:
        return out
    ranks = pd.Series(values[usable]).rank(method="average").to_numpy()
    out[usable] = 2.0 * (ranks - 0.5) / float(count) - 1.0
    return out


def _rank_crossing(now: np.ndarray, prior: np.ndarray) -> np.ndarray:
    """Change in cross-sectional liquidity rank: the inclusion-threshold proxy."""
    out = np.full(now.shape[0], np.nan)
    usable = np.isfinite(now) & np.isfinite(prior)
    if int(usable.sum()) < 3:
        return out
    high = _rank_unit(np.where(usable, now, np.nan))
    low = _rank_unit(np.where(usable, prior, np.nan))
    out[usable] = high[usable] - low[usable]
    return out


def _residualise(target: np.ndarray, control: np.ndarray, usable: np.ndarray) -> np.ndarray:
    """Cross-sectional residual of ``target`` on ``control``, over ``usable`` names only.

    Used to strip the volatility component out of the crowding measurement: what the crowd
    pays *beyond* what the name's own volatility already justifies.
    """
    out = np.array(target, dtype=float, copy=True)
    if int(usable.sum()) < 6:
        return out
    y = target[usable] - float(target[usable].mean())
    x = control[usable] - float(control[usable].mean())
    denominator = float(np.dot(x, x))
    if not denominator > 0.0:
        return out
    out[usable] = y - (float(np.dot(x, y)) / denominator) * x
    return out


def _numeric_column(view: pd.DataFrame, name: str, fallback: str, order) -> np.ndarray | None:
    column = name if name in view.columns else (fallback if fallback in view.columns else None)
    if column is None:
        return None
    values = pd.to_numeric(view[column], errors="coerce").to_numpy(dtype=float)
    if order is not None:
        values = values[order]
    return values


def _infer_week_bars(frames) -> tuple[int, float]:
    """Bars per week, read off ``open_time`` rather than assumed.

    A wrong step size would silently mis-scale every window in this file, so an inference
    that lands outside a sane range falls back to the 8h grid instead of being clipped
    onto its boundary.
    """
    ordered = sorted(
        ((int(frame.shape[0]), idx) for idx, (_, frame) in enumerate(frames)), reverse=True
    )
    spacings = []
    for _, idx in ordered[:8]:
        stamps = _epoch_ns(frames[idx][1]["open_time"].iloc[-65:])
        gaps = np.diff(stamps)
        gaps = gaps[gaps > 0]
        if gaps.size >= 8:
            spacings.append(float(np.median(gaps)))
    if spacings:
        spacing = float(np.median(spacings))
        if spacing > 0.0:
            week = int(round(_WEEK_NS / spacing))
            if _MIN_WEEK_BARS <= week <= _MAX_WEEK_BARS:
                return week, spacing
    return _DEFAULT_WEEK_BARS, float(_WEEK_NS) / _DEFAULT_WEEK_BARS


def _prepare_symbol(frame: pd.DataFrame, tail: int, min_len: int) -> dict | None:
    """Per-symbol prefix sums over just the window the book can reach.

    ``n_full`` is taken before truncation: it is the contract's true seasoning, which is
    the one membership observable that needs no cross-sectional estimate at all.
    """
    n_full = int(frame.shape[0])
    if n_full < 12:
        return None
    view = frame.iloc[n_full - tail:] if n_full > tail else frame
    stamps = _epoch_ns(view["open_time"])
    length = int(stamps.shape[0])
    if length < min_len or bool(np.any(stamps == _NAT)):
        return None

    order = None
    if bool(np.any(np.diff(stamps) <= 0)):
        order = np.argsort(stamps, kind="stable")
        stamps = stamps[order]

    quote = _numeric_column(view, "quote_volume", "volume", order)
    if quote is None:
        return None
    quote = np.where(np.isfinite(quote) & (quote > 0.0), quote, 0.0)

    taker = _numeric_column(view, "taker_buy_quote_volume", "taker_buy_volume", order)
    if taker is None:
        taker = np.full(length, np.nan)
    taker_ok = np.isfinite(taker) & (taker >= 0.0) & (quote > 0.0)

    step = np.zeros(length, dtype=float)
    close = _numeric_column(view, "close", "open", order)
    if close is not None:
        good = np.isfinite(close) & (close > 0.0)
        logged = np.where(good, np.log(np.where(good, close, 1.0)), np.nan)
        changes = np.diff(logged)
        step[1:] = np.where(np.isfinite(changes), changes, 0.0)

    return {
        "n_full": n_full,
        "m": length,
        "t": stamps,
        "cq": _csum(quote),
        "ctb": _csum(np.where(taker_ok, taker, 0.0)),
        "cqt": _csum(np.where(taker_ok, quote, 0.0)),
        "cr": _csum(step),
        "cr2": _csum(step * step),
        "ft": _EMPTY_TIMES,
        "fc": _EMPTY_CUM,
    }


def _funding_map(funding, min_time: int) -> dict:
    """Per-symbol funding times and prefix-summed rates, truncated to the reachable window.

    The rate column is ``funding_rate``, not the raw venue field name.
    """
    out: dict = {}
    if not isinstance(funding, pd.DataFrame) or funding.shape[0] == 0:
        return out
    columns = funding.columns
    if "symbol" not in columns or "funding_rate" not in columns or "funding_time" not in columns:
        return out
    times = _epoch_ns(funding["funding_time"])
    rates = pd.to_numeric(funding["funding_rate"], errors="coerce").to_numpy(dtype=float)
    keep = (times != _NAT) & np.isfinite(rates) & (times >= min_time)
    if not bool(keep.any()):
        return out
    table = pd.DataFrame(
        {"sym": funding["symbol"].to_numpy()[keep], "t": times[keep], "r": rates[keep]}
    ).sort_values(["sym", "t"], kind="stable")
    for symbol, group in table.groupby("sym", sort=False):
        out[str(symbol)] = (group["t"].to_numpy(), _csum(group["r"].to_numpy()))
    return out


def _features_at(prep: dict, end: int, week: int, baseline_win: int, state_win: int):
    """Inclusion and crowding measurements as of ``end`` bars into this symbol's history.

    Every quantity returned is a ratio, a rate, a count or a rank input, so the book is
    invariant to a uniform rescaling of prices and volumes.
    """
    cum_q = prep["cq"]
    short_lo = end - week
    if short_lo < 0:
        return None
    short_total = cum_q[end] - cum_q[short_lo]
    if not short_total > 0.0:
        return None
    mean_short = short_total / float(week)

    # Rank-crossing baseline: the two weeks preceding the trailing week. A contract too
    # young to have one scores neutral on this axis and is carried by seasoning alone.
    prior_lo = max(0, end - baseline_win)
    prior_hi = short_lo
    prior_n = prior_hi - prior_lo
    if prior_n >= max(2, week // 3):
        mean_prior = (cum_q[prior_hi] - cum_q[prior_lo]) / float(prior_n)
        if not mean_prior > 0.0:
            mean_prior = float("nan")
    else:
        mean_prior = float("nan")

    state_lo = max(0, end - state_win)
    state_n = end - state_lo
    taker_total = prep["ctb"][end] - prep["ctb"][state_lo]
    quote_total = prep["cqt"][end] - prep["cqt"][state_lo]
    if quote_total > 0.0:
        taker = taker_total / quote_total - 0.5
    else:
        taker = float("nan")

    # Capacity: the more conservative of the trailing week and the trailing state window,
    # so a name whose volume has just collapsed is sized off the collapse, not the memory.
    mean_state = (cum_q[end] - cum_q[state_lo]) / float(state_n)
    capacity = min(mean_short, mean_state)

    volatility = float("nan")
    if state_n >= 8:
        first = (prep["cr"][end] - prep["cr"][state_lo]) / float(state_n)
        second = (prep["cr2"][end] - prep["cr2"][state_lo]) / float(state_n)
        variance = second - first * first
        if np.isfinite(variance) and variance > 0.0:
            volatility = float(np.sqrt(variance))

    funding = float("nan")
    times = prep["ft"]
    if times.shape[0] > 0:
        stamps = prep["t"]
        cutoff = stamps[end - 1]
        window_start = stamps[state_lo] if state_lo < end else stamps[0]
        hi = int(np.searchsorted(times, cutoff, side="right"))
        lo = int(np.searchsorted(times, window_start, side="left"))
        if hi - lo >= _MIN_FUNDING_OBS:
            funding = float((prep["fc"][hi] - prep["fc"][lo]) / float(hi - lo))

    return mean_short, mean_prior, taker, funding, capacity, volatility


# --- strategy -------------------------------------------------------------------------
class InclusionAttentionBook:
    """Stateless cross-sectional inclusion x crowding book."""

    def target_weights(self, context, *, seed):
        del seed  # nothing here is random; the book is a pure function of the context

        bars = getattr(context, "bars", None)
        eligible = getattr(context, "eligible_symbols", None)
        if not isinstance(bars, Mapping) or eligible is None:
            return {}

        frames = []
        for symbol in sorted(dict.fromkeys(str(name) for name in eligible)):
            frame = bars.get(symbol)
            if (
                isinstance(frame, pd.DataFrame)
                and frame.shape[0] >= 12
                and "open_time" in frame.columns
            ):
                frames.append((symbol, frame))
        if len(frames) < _MIN_NAMES:
            return {}

        week, spacing = _infer_week_bars(frames)
        horizon = _HORIZON_WEEKS * week
        baseline_win = _BASELINE_WEEKS * week
        state_win = _STATE_WEEKS * week
        step = max(1, week // _LAG_NODES_PER_WEEK)
        lags = range(0, horizon, step)
        tail = horizon + max(baseline_win, state_win) + 4
        min_len = week + 3

        prepared = []
        for symbol, frame in frames:
            prep = _prepare_symbol(frame, tail, min_len)
            if prep is not None:
                prep["symbol"] = symbol
                prepared.append(prep)
        if len(prepared) < _MIN_NAMES:
            return {}

        latest = max(int(prep["t"][-1]) for prep in prepared)
        funding_rows = _funding_map(
            getattr(context, "funding", None), latest - int((tail + 8) * spacing)
        )
        for prep in prepared:
            times, cumulative = funding_rows.get(prep["symbol"], (_EMPTY_TIMES, _EMPTY_CUM))
            prep["ft"] = times
            prep["fc"] = cumulative

        count = len(prepared)
        numerator = np.zeros(count)
        capacity = np.full(count, np.nan)
        tradable = np.zeros(count, dtype=bool)
        kernel_mass = 0.0

        # Linear-decay holding kernel over H weeks. The book at each decision is the
        # decayed average of the books these rules would have chosen over the past H
        # weeks, recomputed from scratch every time, so it carries no state and cannot see
        # forward. Dividing by the *full* kernel mass rather than by the mass a name was
        # present for gives every contract a linear size ramp over its first H weeks.
        for lag in lags:
            weight = 1.0 - lag / float(horizon)
            if weight <= 0.0:
                continue
            kernel_mass += weight

            level_now = np.full(count, np.nan)
            level_prior = np.full(count, np.nan)
            seasoning = np.full(count, np.nan)
            taker = np.full(count, np.nan)
            carry = np.full(count, np.nan)
            volatility = np.full(count, np.nan)
            present = np.zeros(count, dtype=bool)

            for i, prep in enumerate(prepared):
                end = prep["m"] - lag
                if end < min_len:
                    continue
                measured = _features_at(prep, end, week, baseline_win, state_win)
                if measured is None:
                    continue
                present[i] = True
                level_now[i], level_prior[i], taker[i], carry[i], liq, volatility[i] = measured
                seasoning[i] = -float(prep["n_full"] - lag)
                if lag == 0:
                    tradable[i] = True
                    capacity[i] = liq

            if int(present.sum()) < _MIN_NAMES:
                continue

            # Event: inclusion / attention intensity. High = entrant, low = leaver.
            # Seasoning is how newly the contract exists at all -- definitionally a new
            # member, and the only membership fact needing no cross-sectional estimate.
            event = 0.5 * _rank_unit(seasoning) + 0.5 * _rank_unit(
                _rank_crossing(level_now, level_prior)
            )
            event = _rank_unit(np.where(present, event, np.nan))

            # State: crowdedness of leveraged positioning, net of volatility. Funding is
            # the price of leverage and that price rises with the volatility of the
            # underlying, so the raw rank is part crowding and part a volatility rank.
            crowd = 0.5 * _rank_unit(carry) + 0.5 * _rank_unit(taker)
            crowd = _residualise(crowd, _rank_unit(volatility), present)
            crowd = _rank_unit(np.where(present, crowd, np.nan))

            numerator += np.where(present, weight * (-event * crowd), 0.0)

        if not kernel_mass > 0.0 or int(tradable.sum()) < _MIN_NAMES:
            return {}

        index = np.flatnonzero(tradable)
        raw = numerator[index] / kernel_mass
        raw = raw - raw.mean()
        spread = float(raw.std())
        if not spread > 0.0:
            return {}
        raw = raw / spread

        # Soft threshold: spend turnover only on conviction. Continuous, so a name entering
        # the book enters at zero size and grows -- no round trip on a crossing.
        book = np.sign(raw) * np.maximum(np.abs(raw) - _SOFT_THRESHOLD, 0.0)
        if int(np.count_nonzero(book)) < _MIN_NAMES:
            book = raw.copy()

        # Dollar-balance the two sides before sizing, so both are genuinely used on
        # exposure rather than only in the P&L.
        longs = float(book[book > 0.0].sum())
        shorts = float(-book[book < 0.0].sum())
        if not longs > 0.0 or not shorts > 0.0:
            return {}
        if longs > shorts:
            book[book > 0.0] *= shorts / longs
        elif shorts > longs:
            book[book < 0.0] *= longs / shorts

        # Participation-aware ceiling: a name's weight is bounded by its own share of
        # tradeable volume, measured against the cross-sectional median so the rule is
        # free of any absolute currency scale. Entrants and leavers are the thinnest names
        # in the universe; this is where the cost gate is won or lost.
        room = capacity[index]
        usable = np.isfinite(room) & (room > 0.0)
        ceiling = np.full(index.shape[0], _MAX_WEIGHT)
        if int(usable.sum()) >= 3:
            reference = float(np.median(room[usable]))
            if reference > 0.0:
                ratio = np.where(usable, room / reference, _CAP_FLOOR)
                ceiling = _MAX_WEIGHT * np.clip(ratio, _CAP_FLOOR, 1.0)

        weights = book
        for _ in range(16):
            gross = float(np.abs(weights).sum())
            if not gross > 0.0:
                return {}
            weights = np.clip(weights * (_GROSS_TARGET / gross), -ceiling, ceiling)

        weights = np.clip(weights, -_MAX_WEIGHT, _MAX_WEIGHT)
        gross = float(np.abs(weights).sum())
        if not gross > 0.0:
            return {}
        if gross > 1.0:
            weights = weights / gross

        net = float(weights.sum())
        if abs(net) > _MAX_NET:
            side = weights > 0.0 if net > 0.0 else weights < 0.0
            heavy = float(np.abs(weights[side]).sum())
            if heavy > 0.0:
                weights[side] *= max(0.0, 1.0 - (abs(net) - _MAX_NET) / heavy)

        targets = {}
        for position, i in enumerate(index):
            value = float(weights[position])
            if np.isfinite(value) and abs(value) > _DUST:
                targets[prepared[i]["symbol"]] = value
        if len(targets) < _MIN_NAMES:
            return {}
        return targets


def build_strategy():
    return InclusionAttentionBook()
