"""team-13 — universe inclusion and attention.

Weekly membership entry and exit, expressed as a cross-sectional interaction between
inclusion/attention intensity and the crowdedness of leveraged positioning:

    score = - (inclusion/attention intensity) x (crowding state)

which is exactly the preregistered sign, quadrant by quadrant --

    entrant  x crowded    -> short   (sell immediacy to the attention crowd)
    entrant  x uncrowded  -> long    (genuine liquidity migration, continues)
    leaver   x crowded    -> long    (buy from forced closers of long inventory)
    leaver   x uncrowded  -> short   (sell to forced closers of short inventory)

because -(E)(C) with E = entrant_intensity - leaver_intensity reproduces the two legs
additively.

The book is stateless. Membership history is not carried in ``DecisionContext``, so the
membership event is reconstructed at every decision from past-only rows: a trailing
dollar-volume rank crossing, a dollar-volume surge, and contract seasoning (bars of
available history, i.e. how newly the name exists at all).

Cost discipline is structural rather than incidental. The event position is held with a
linear three-week decay, implemented statelessly as a lag-weighted average of the signal
recomputed at each historical offset; the crowding state is measured over three weeks; the
book is weighted toward the tradeable half of the cross-section; and low-conviction names
are soft-thresholded to exactly zero so that turnover is spent only where the signal is.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

__all__ = ["build_strategy"]

# --- structural constants (declared surface; none is fitted to a result) -------------
_WEEK_NS = 7 * 24 * 3600 * 1_000_000_000
_DEFAULT_WEEK_BARS = 21          # 8h bars: one week, one funding settlement per bar
_MIN_WEEK_BARS = 3
_MAX_WEEK_BARS = 84
_HORIZON_WEEKS = 3               # H: post-event holding horizon (declared knob 1, level 3)
_STATE_WEEKS = 3                 # L_z: crowding lookback (declared knob 2, level 2)
_LAG_NODES_PER_WEEK = 7          # sampling density of the linear-decay holding kernel
_MIN_FUNDING_OBS = 3
_MIN_NAMES = 10
_TARGET_NAMES = 30               # breadth floor enforced through an adaptive threshold
_SOFT_THRESHOLD = 0.40           # in cross-sectional sigma of the final score
_LIQ_FLOOR = 0.25
_MAX_WEIGHT = 0.10
_MAX_NET = 0.20
_DUST = 1e-6
_NAT = np.iinfo(np.int64).min
_EMPTY_TIMES = np.zeros(0, dtype="int64")
_EMPTY_CUM = np.zeros(1, dtype=float)


# --- pure helpers --------------------------------------------------------------------
def _epoch_ns(values) -> np.ndarray:
    """Monotone integer time key. Any consistent unit works; only ordering is used."""
    stamps = pd.to_datetime(pd.Series(np.asarray(values)), utc=True, errors="coerce")
    return stamps.dt.tz_localize(None).to_numpy().astype("int64")


def _csum(values: np.ndarray) -> np.ndarray:
    """Prefix sums with a leading zero, so any window sum is one subtraction."""
    return np.concatenate((np.zeros(1, dtype=float), np.cumsum(values)))


def _rank_unit(values: np.ndarray) -> np.ndarray:
    """Cross-sectional rank mapped to [-1, 1]. Non-finite entries map to 0 (neutral).

    Rank rather than z is used deliberately: alt-perp volume and funding cross-sections
    carry outliers that would otherwise set the scale of every other name, and a bounded
    score keeps the product of two components bounded.
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


def _numeric_column(view: pd.DataFrame, name: str, fallback: str, order) -> np.ndarray | None:
    column = name if name in view.columns else (fallback if fallback in view.columns else None)
    if column is None:
        return None
    values = pd.to_numeric(view[column], errors="coerce").to_numpy(dtype=float)
    if order is not None:
        values = values[order]
    return values


def _infer_week_bars(frames) -> tuple[int, float]:
    """Bars per week, read off the data rather than assumed, so the book is
    equivariant to a calendar shift or a different bar cadence."""
    ordered = sorted(((int(frame.shape[0]), idx) for idx, (_, frame) in enumerate(frames)),
                     reverse=True)
    spacings = []
    for _, idx in ordered[:8]:
        stamps = _epoch_ns(frames[idx][1]["open_time"].iloc[-65:])
        gaps = np.diff(stamps)
        gaps = gaps[gaps > 0]
        if gaps.size >= 8:
            spacings.append(float(np.median(gaps)))
    if not spacings:
        return _DEFAULT_WEEK_BARS, float(_WEEK_NS) / _DEFAULT_WEEK_BARS
    spacing = float(np.median(spacings))
    if not spacing > 0.0:
        return _DEFAULT_WEEK_BARS, float(_WEEK_NS) / _DEFAULT_WEEK_BARS
    week = int(round(_WEEK_NS / spacing))
    return max(_MIN_WEEK_BARS, min(_MAX_WEEK_BARS, week)), spacing


def _prepare_symbol(frame: pd.DataFrame, tail: int) -> dict | None:
    """Per-symbol prefix sums over just the window the book can reach."""
    n_full = int(frame.shape[0])
    if n_full < 8:
        return None
    view = frame.iloc[n_full - tail:] if n_full > tail else frame
    stamps = _epoch_ns(view["open_time"])
    length = int(stamps.shape[0])
    if length < 8 or bool(np.any(stamps == _NAT)):
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
    return {
        "n_full": n_full,
        "m": length,
        "t": stamps,
        "cq": _csum(quote),
        "ctb": _csum(np.where(taker_ok, taker, 0.0)),
        "cqt": _csum(np.where(taker_ok, quote, 0.0)),
        "ft": _EMPTY_TIMES,
        "fc": _EMPTY_CUM,
    }


def _funding_map(funding, min_time: int) -> dict:
    """Per-symbol funding times and prefix-summed rates, truncated to the reachable window."""
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


def _features_at(prep: dict, end: int, week: int, state_win: int):
    """Inclusion and crowding measurements as of ``end`` bars into this symbol's history.

    Every quantity is a ratio or a rank input, so the book is invariant to a uniform
    rescaling of prices and volumes.
    """
    cum_q = prep["cq"]
    short_lo = end - week
    short_total = cum_q[end] - cum_q[short_lo]
    if not short_total > 0.0:
        return None
    mean_short = short_total / float(week)

    prior_lo = max(0, end - _HORIZON_WEEKS * week)
    prior_hi = short_lo
    prior_n = prior_hi - prior_lo
    if prior_n < 1:
        return None
    mean_prior = (cum_q[prior_hi] - cum_q[prior_lo]) / float(prior_n)

    if mean_prior > 0.0:
        surge = math.log(mean_short / mean_prior)
    else:
        surge = float("nan")

    state_lo = max(0, end - state_win)
    taker_total = prep["ctb"][end] - prep["ctb"][state_lo]
    quote_total = prep["cqt"][end] - prep["cqt"][state_lo]
    if quote_total > 0.0:
        taker = taker_total / quote_total - 0.5
    else:
        taker = float("nan")

    liquidity = (cum_q[end] - cum_q[state_lo]) / float(end - state_lo)

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

    return surge, mean_short, mean_prior, taker, funding, liquidity


# --- strategy ------------------------------------------------------------------------
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
                and frame.shape[0] >= 8
                and "open_time" in frame.columns
            ):
                frames.append((symbol, frame))
        if len(frames) < _MIN_NAMES:
            return {}

        week, spacing = _infer_week_bars(frames)
        horizon = _HORIZON_WEEKS * week
        state_win = _STATE_WEEKS * week
        step = max(1, week // _LAG_NODES_PER_WEEK)
        lags = range(0, horizon, step)
        tail = horizon + state_win + 4

        prepared = []
        for symbol, frame in frames:
            prep = _prepare_symbol(frame, tail)
            if prep is not None and prep["m"] >= 2 * week:
                prep["symbol"] = symbol
                prepared.append(prep)
        if len(prepared) < _MIN_NAMES:
            return {}

        latest = max(int(prep["t"][-1]) for prep in prepared)
        funding = _funding_map(
            getattr(context, "funding", None), latest - int((tail + 8) * spacing)
        )
        for prep in prepared:
            times, cumulative = funding.get(prep["symbol"], (_EMPTY_TIMES, _EMPTY_CUM))
            prep["ft"] = times
            prep["fc"] = cumulative

        count = len(prepared)
        numerator = np.zeros(count)
        denominator = np.zeros(count)
        liquidity = np.full(count, np.nan)

        # Linear-decay holding kernel: the book at each decision is the decayed average of
        # the books the same rules would have chosen over the past H weeks. Recomputed from
        # scratch every time, so it carries no state and cannot see forward.
        for lag in lags:
            kernel = 1.0 - lag / float(horizon)
            if kernel <= 0.0:
                continue
            surge = np.full(count, np.nan)
            level_now = np.full(count, np.nan)
            level_prior = np.full(count, np.nan)
            seasoning = np.full(count, np.nan)
            taker = np.full(count, np.nan)
            carry = np.full(count, np.nan)
            present = np.zeros(count, dtype=bool)

            for i, prep in enumerate(prepared):
                end = prep["m"] - lag
                if end < 2 * week:
                    continue
                measured = _features_at(prep, end, week, state_win)
                if measured is None:
                    continue
                present[i] = True
                surge[i], level_now[i], level_prior[i], taker[i], carry[i], liq = measured
                seasoning[i] = -float(prep["n_full"] - lag)
                if lag == 0:
                    liquidity[i] = liq

            if int(present.sum()) < _MIN_NAMES:
                continue

            # Inclusion / attention intensity: rank crossing, dollar-volume surge, and how
            # newly the contract exists at all. High = entrant, low = leaver.
            event = (
                _rank_unit(surge)
                + _rank_unit(_rank_crossing(level_now, level_prior))
                + _rank_unit(seasoning)
            ) / 3.0
            event = _rank_unit(np.where(present, event, np.nan))

            # Crowdedness of leveraged positioning: what the crowd pays to hold the
            # position, and which side is lifting. High = crowd is levered long.
            crowd = (_rank_unit(carry) + _rank_unit(taker)) / 2.0
            crowd = _rank_unit(np.where(present, crowd, np.nan))

            numerator += np.where(present, kernel * (-event * crowd), 0.0)
            denominator += np.where(present, kernel, 0.0)

        active = denominator > 0.0
        if int(active.sum()) < _MIN_NAMES:
            return {}
        score = np.zeros(count)
        score[active] = numerator[active] / denominator[active]

        # Tilt the book toward the half of the cross-section that can absorb it. Entrants
        # and leavers are the widest names in the universe; this is where the cost gate is
        # won or lost.
        liquid = (_rank_unit(liquidity) + 1.0) / 2.0
        raw = score * (_LIQ_FLOOR + (1.0 - _LIQ_FLOOR) * liquid)

        index = np.flatnonzero(active)
        book = raw[index]
        book = book - book.mean()
        spread = float(book.std())
        if not spread > 0.0:
            return {}
        book = book / spread

        # Soft threshold: spend turnover only on conviction, and do it continuously so
        # small perturbations move weights smoothly instead of flipping names in and out.
        magnitude = np.abs(book)
        keep = min(book.size, _TARGET_NAMES)
        floor = float(np.sort(magnitude)[-keep])
        cut = min(_SOFT_THRESHOLD, floor)
        book = np.sign(book) * np.maximum(magnitude - cut, 0.0)

        longs = float(book[book > 0.0].sum())
        shorts = float(-book[book < 0.0].sum())
        if not longs > 0.0 or not shorts > 0.0:
            return {}
        if longs > shorts:
            book[book > 0.0] *= shorts / longs
        elif shorts > longs:
            book[book < 0.0] *= longs / shorts

        gross = float(np.abs(book).sum())
        if not gross > 0.0:
            return {}
        weights = np.clip(book / gross, -_MAX_WEIGHT, _MAX_WEIGHT)

        total = float(np.abs(weights).sum())
        if not total > 0.0:
            return {}
        if total > 1.0:
            weights = weights / total
        net = float(weights.sum())
        if abs(net) > _MAX_NET:
            side = weights > 0.0 if net > 0.0 else weights < 0.0
            heavy = float(np.abs(weights[side]).sum())
            if heavy > 0.0:
                weights[side] *= max(0.0, 1.0 - (abs(net) - _MAX_NET) / heavy)

        targets = {}
        for position, i in enumerate(index):
            weight = float(weights[position])
            if np.isfinite(weight) and abs(weight) > _DUST:
                targets[prepared[i]["symbol"]] = weight
        if len(targets) < _MIN_NAMES:
            return {}
        return targets


def build_strategy():
    return InclusionAttentionBook()
