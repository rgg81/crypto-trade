"""Point-in-time, hysteresis-stabilised top-20 membership."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

MEMBERSHIP_COLUMNS = ("reconstitution_time", "symbol", "liquidity_rank", "trailing_quote_volume")

# The ranking statistic, named rather than merely implemented. `crypto_trade.cup20.config` freezes
# the machine contract's `universe.liquidity_measure` against THIS constant, so a config that
# declares one statistic while the code computes another cannot load -- the exact charter-versus-
# config drift the activation freeze exists to catch, which slipped through once because the
# statistic lived only in a descriptive string in the acquisition config.
LIQUIDITY_MEASURE = "median-daily-quote-volume"


def weekly_reconstitution_times(
    start: pd.Timestamp, end: pd.Timestamp, *, weekday: int = 0
) -> tuple[pd.Timestamp, ...]:
    """Every UTC-midnight ``weekday`` boundary in ``[start, end)``."""
    start = _require_utc(start, "start")
    end = _require_utc(end, "end")
    days = pd.date_range(start.normalize(), end.normalize(), freq="D", tz="UTC", inclusive="left")
    return tuple(day for day in days if day.weekday() == weekday and day >= start)


def build_membership(
    daily_quote_volume: pd.DataFrame,
    *,
    eligible: pd.DataFrame,
    reconstitution_times: Sequence[pd.Timestamp],
    lookback_days: int = 180,
    target_size: int = 20,
    entry_rank: int = 20,
    exit_rank: int = 25,
    minimum_scored_members: int = 1,
) -> pd.DataFrame:
    """Build point-in-time membership from daily quote volume.

    A symbol is a candidate only when it has a *complete* ``lookback_days`` window of daily quote
    volume strictly before the boundary and is eligible on the boundary itself. The completeness
    requirement doubles as the minimum listing age. Incumbents survive to ``exit_rank``; new
    entrants require ``entry_rank``.

    Ranking is by the **median** daily quote volume over the window (``LIQUIDITY_MEASURE``), not
    the mean. The difference is the whole point of a "deliberately stable" universe: a launch-week
    volume spike lifts a 180-day mean enormously and a 180-day median barely at all, so the mean
    admits transient listings that the median rejects in favour of established names. Measured
    across the built snapshot's 207 in-sample reconstitutions, the mean produced 67 distinct members
    at 0.31 changes/week and the median 63 at 0.29 -- better on every axis of the stated objective.
    (In-sample figures only, deliberately: this file is readable alongside the charter, and the
    universe's size and turnover after the cutoff are facts about the holdout. The full-window
    measurement is in ``tournament/cup20/private/universe-summary.json``.)

    ``minimum_scored_members`` implements the charter's "a boundary with fewer than 8 members is not
    scored": a boundary whose membership falls below it emits NO rows, so nothing downstream can
    score a universe too thin to be one. It is a policy value in the machine contract
    (``universe.minimum_scored_members``), threaded in explicitly by the build script -- it was
    declared there and read by nothing at all until this became its reader. The default of 1 is the
    honest identity for a caller with no such policy (a boundary with zero members already emits
    nothing), not a disabled guard: production passes the contract's own 8. On the built snapshot
    the rule is inert by measurement -- every shipped boundary carries exactly 20 members -- so it
    is a guarantee against a future delisting wave, not a filter that shaped this artifact.
    """
    if lookback_days < 1 or target_size < 1:
        raise ValueError("lookback_days and target_size must be positive")
    if entry_rank < 1 or exit_rank < entry_rank:
        raise ValueError("exit_rank must be at least entry_rank")
    if minimum_scored_members < 1:
        raise ValueError("minimum_scored_members must be positive")
    volume = _require_utc_index(daily_quote_volume, "daily_quote_volume")
    eligibility = _require_utc_index(eligible, "eligible").astype(bool)
    window = pd.Timedelta(days=lookback_days)

    rows: list[dict[str, object]] = []
    previous: tuple[str, ...] = ()
    for raw_time in reconstitution_times:
        boundary = _require_utc(raw_time, "reconstitution_time")
        history = volume.loc[(volume.index >= boundary - window) & (volume.index < boundary)]
        complete = history.notna().sum() == lookback_days
        eligible_now = _eligibility_at(eligibility, boundary)
        # LIQUIDITY_MEASURE: median, never mean. See this function's docstring.
        medians = history.median()
        candidates = medians[complete & eligible_now].dropna()
        ordered = candidates.sort_values(ascending=False, kind="mergesort")
        ranks = {symbol: index + 1 for index, symbol in enumerate(ordered.index)}

        kept = [s for s in ordered.index if s in previous and ranks[s] <= exit_rank][:target_size]
        entrants = [s for s in ordered.index if s not in previous and ranks[s] <= entry_rank]
        members = kept + [s for s in entrants if s not in kept]
        members = members[:target_size]
        if len(members) < minimum_scored_members:
            # Not scored, so not emitted. `previous` still advances to the members that WOULD have
            # been held: hysteresis is a statement about what the index held at the last boundary,
            # and a boundary being too thin to score does not make the prior boundary's incumbents
            # stop being incumbents at the next one.
            previous = tuple(members)
            continue

        for symbol in members:
            rows.append(
                {
                    "reconstitution_time": boundary,
                    "symbol": symbol,
                    "liquidity_rank": ranks[symbol],
                    "trailing_quote_volume": float(ordered[symbol]),
                }
            )
        previous = tuple(members)

    if not rows:
        return pd.DataFrame(columns=list(MEMBERSHIP_COLUMNS))
    frame = pd.DataFrame(rows, columns=list(MEMBERSHIP_COLUMNS))
    return frame.sort_values(["reconstitution_time", "liquidity_rank"]).reset_index(drop=True)


def _eligibility_at(eligibility: pd.DataFrame, boundary: pd.Timestamp) -> pd.Series:
    past = eligibility.loc[eligibility.index <= boundary]
    if past.empty:
        return pd.Series(False, index=eligibility.columns)
    return past.iloc[-1]


def _require_utc(value: pd.Timestamp, label: str) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware UTC")
    return timestamp.tz_convert("UTC")


def _require_utc_index(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    index = pd.DatetimeIndex(frame.index)
    if index.tz is None:
        raise ValueError(f"{label} index must be timezone-aware UTC")
    result = frame.copy(deep=False)
    result.index = index.tz_convert("UTC")
    return result.sort_index()
