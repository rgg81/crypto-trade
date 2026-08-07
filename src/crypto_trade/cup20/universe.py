"""Point-in-time, hysteresis-stabilised top-20 membership."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
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
    fillable: pd.DataFrame,
    markable: pd.DataFrame,
    reconstitution_times: Sequence[pd.Timestamp],
    lookback_days: int = 180,
    target_size: int = 20,
    entry_rank: int = 20,
    exit_rank: int = 25,
    minimum_scored_members: int = 1,
) -> pd.DataFrame:
    """Build point-in-time membership from daily quote volume.

    A symbol is a candidate only when it has a *complete* ``lookback_days`` window of daily quote
    volume strictly before the boundary, is eligible on the boundary itself, and can be MARKED at
    every decision boundary the membership decision commits it to (see below). The completeness
    requirement doubles as the minimum listing age. Incumbents survive to ``exit_rank``; new
    entrants require ``entry_rank``.

    **Mark coverage, and why it is the membership period rather than the boundary or the lookback.**
    ``evaluate_targets`` raises ``missing current mark for eligible symbols`` at any decision
    boundary where a member has an executable bar open and no mark price. That raise fires on the
    ELIGIBLE set, before a single line of strategy code runs, so a member the evaluator cannot mark
    crashes *every* candidate regardless of what it trades. A symbol the evaluator cannot mark is
    not tradeable, so mark coverage is an eligibility criterion, exactly like bar coverage.

    Three shapes were measured on the built acquisition before this one was adopted:

    * *a mark at the reconstitution boundary itself* -- point-in-time and minimal, but it says
      nothing about the 20 intra-week decision boundaries that follow, so it guarantees nothing;
    * *a complete ``lookback_days`` window of marks*, symmetric with the bar rule -- which would be
      the tidy answer and is wrong here: Binance's mark-price archive begins 2020-06-29 for every
      symbol at once, so a 180-day trailing mark requirement admits nobody until 2020-12-26 and
      drags ``IS_START`` (a computed, frozen tournament parameter) four months later. Mark history
      is an archive property, not a listing-age one, and borrowing the listing-age rule for it
      penalises the wrong thing;
    * **the membership period** -- adopted. A decision at boundary ``t_i`` commits the symbol to be
      a member for ``[t_i, t_{i+1})``, and the evaluator will demand a mark at every 8h decision
      boundary in that interval at which the symbol is fillable. The criterion is therefore exactly
      co-extensive with what the decision commits to: no wider, and never narrower than the
      guarantee it has to make.

    ``fillable`` and ``markable`` are boolean frames on the evaluator's own decision grid: True
    where the symbol has an executable bar open, and True where a mark price exists. A symbol is
    admissible at ``t_i`` only when ``fillable & ~markable`` is empty for it across
    ``[t_i, t_{i+1})`` (the final boundary's period runs to the end of the grid). Both are required
    arguments, not optional ones: a default would let a caller rebuild the universe without saying
    where the evaluator can mark, which is the exact omission that shipped this defect.

    Adopting it cost one name. Measured against the previous membership over the built snapshot it
    removed 28 rows and added 28: IOTAUSDT and SUIUSDT lose the seats they could not be marked in,
    and NEOUSDT, 1000PEPEUSDT, TRBUSDT and MASKUSDT take them. Only IOTAUSDT leaves the universe
    outright -- the other five keep seats at boundaries where they are markable -- so the in-sample
    universe holds 62 distinct names rather than 63. ``IS_START`` is unchanged at 2020-08-17 and
    every boundary still carries exactly 20 members. On this data the boundary-only rule would have
    produced the identical membership: the stronger criterion is free here, which is the reason to
    take it rather than a reason to skip it.

    **The one gap, stated rather than left to be found.** A boundary that emits nothing (below
    ``minimum_scored_members``) leaves the PREVIOUS boundary's members in force past the period
    their coverage was checked over. That case cannot be closed from inside this function without
    reading the future of its own decisions, so it is closed downstream instead:
    :func:`unmarkable_member_boundaries` re-derives the property over the built membership and
    ``scripts/cup20_build_snapshot.py`` fails the build on it. Anything that ships has the
    guarantee; the degenerate case fails loudly at build time rather than at a team's first run.

    Ranking is by the **median** daily quote volume over the window (``LIQUIDITY_MEASURE``), not
    the mean. The difference is the whole point of a "deliberately stable" universe: a launch-week
    volume spike lifts a 180-day mean enormously and a 180-day median barely at all, so the mean
    admits transient listings that the median rejects in favour of established names. Measured
    across the built snapshot's 207 in-sample reconstitutions, the mean produced 66 distinct members
    at 0.30 changes/week and the median 62 at 0.28 -- better on every axis of the stated objective.
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
    eligibility = _require_boolean(_require_utc_index(eligible, "eligible"), "eligible")
    boundaries = _require_ascending(reconstitution_times)
    blocked_at = _mark_coverage_gaps(fillable, markable, boundaries, list(volume.columns))
    window = pd.Timedelta(days=lookback_days)

    rows: list[dict[str, object]] = []
    previous: tuple[str, ...] = ()
    for position, boundary in enumerate(boundaries):
        history = volume.loc[(volume.index >= boundary - window) & (volume.index < boundary)]
        complete = history.notna().sum() == lookback_days
        eligible_now = _eligibility_at(eligibility, boundary)
        # A symbol the evaluator cannot mark is not tradeable, so it is not eligible. See this
        # function's docstring for why the window checked is the membership period.
        markable_now = ~blocked_at[position]
        # LIQUIDITY_MEASURE: median, never mean. See this function's docstring.
        medians = history.median()
        candidates = medians[complete & eligible_now & markable_now].dropna()
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


def unmarkable_member_boundaries(
    membership: pd.DataFrame, *, fillable: pd.DataFrame, markable: pd.DataFrame
) -> list[tuple[pd.Timestamp, str]]:
    """Every ``(decision boundary, member)`` pair the evaluator would refuse to mark.

    The post-condition half of the eligibility rule, and the direct statement of the property the
    whole change exists to guarantee: at every 8h decision boundary, every symbol
    ``eligible_at(membership, t)`` returns that has an executable bar open has a mark price. It
    replays exactly the evaluator's own test -- ``fillable & ~markable`` over the members in force
    -- rather than re-deriving membership, so it is capable of disagreeing with
    :func:`build_membership` instead of merely restating it.

    It is not decoration over that function's own criterion. Two things reach here that cannot
    reach it: a boundary that emitted no rows (below ``minimum_scored_members``) silently extends
    the previous boundary's members past the period their coverage was checked over, and a
    membership frame that was filtered, edited or hand-assembled after the build has no criterion
    behind it at all. Returns the pairs rather than raising, so the caller decides whether this is
    a build failure (it is) or a report.
    """
    grid, gaps = _coverage_grid(fillable, markable)
    if membership.empty:
        return []
    times = pd.to_datetime(membership["reconstitution_time"], utc=True)
    symbols = membership["symbol"].astype(str)
    columns = {name: index for index, name in enumerate(gaps.columns)}
    values = gaps.to_numpy(dtype=bool)
    ordered = sorted(times.unique())
    if len(grid) == 0 or ordered[-1] > grid[-1]:
        # Every boundary past the end of the grid would scan an empty slice and report nothing --
        # a membership the coverage frames cannot speak about, returned as if it were clean.
        raise ValueError(
            f"membership reaches {ordered[-1]} but the coverage grid ends at "
            f"{grid[-1] if len(grid) else None}; boundaries past it would be reported clean "
            "without a single cell having been read"
        )
    starts = grid.searchsorted(pd.DatetimeIndex(ordered), side="left")
    findings: list[tuple[pd.Timestamp, str]] = []
    for position, boundary in enumerate(ordered):
        start = int(starts[position])
        stop = int(starts[position + 1]) if position + 1 < len(ordered) else len(grid)
        members = sorted(set(symbols[times == boundary]))
        for symbol in members:
            column = columns.get(symbol)
            if column is None:
                # A member with no coverage column at all is unmarkable everywhere it is held.
                findings.extend((grid[row], symbol) for row in range(start, stop))
                continue
            offending = np.flatnonzero(values[start:stop, column])
            findings.extend((grid[start + int(row)], symbol) for row in offending)
    return sorted(findings)


def _require_ascending(reconstitution_times: Sequence[pd.Timestamp]) -> tuple[pd.Timestamp, ...]:
    """Parse the boundary schedule, requiring a total order.

    The mark-coverage criterion reads ``[t_i, t_{i+1})``, so an unsorted or duplicated schedule
    would check a symbol's coverage over an interval that is empty or runs backwards -- and an
    empty interval admits everything, which is a fail-open. Hysteresis reads the same order.
    """
    boundaries = tuple(_require_utc(time, "reconstitution_time") for time in reconstitution_times)
    if list(boundaries) != sorted(boundaries):
        raise ValueError("reconstitution_times must be sorted ascending")
    if len(set(boundaries)) != len(boundaries):
        raise ValueError("reconstitution_times must not contain duplicate timestamps")
    return boundaries


def _coverage_grid(
    fillable: pd.DataFrame, markable: pd.DataFrame
) -> tuple[pd.DatetimeIndex, pd.DataFrame]:
    """The decision grid and ``fillable & ~markable`` on it: where a mark is demanded and absent."""
    fills = _require_boolean(_require_utc_index(fillable, "fillable"), "fillable")
    marks = _require_boolean(_require_utc_index(markable, "markable"), "markable")
    if not fills.index.equals(marks.index):
        raise ValueError("fillable and markable must share one decision grid")
    if set(fills.columns) != set(marks.columns):
        raise ValueError("fillable and markable must cover the same symbols")
    marks = marks.reindex(columns=fills.columns)
    return pd.DatetimeIndex(fills.index), fills & ~marks


def _mark_coverage_gaps(
    fillable: pd.DataFrame,
    markable: pd.DataFrame,
    boundaries: Sequence[pd.Timestamp],
    symbols: Sequence[str],
) -> list[pd.Series]:
    """Per boundary, which ``symbols`` have an unmarkable moment inside their membership period."""
    grid, gaps = _coverage_grid(fillable, markable)
    missing = sorted(set(symbols) - set(gaps.columns))
    if missing:
        raise ValueError(
            "fillable/markable do not cover every ranked symbol, so mark coverage cannot be "
            f"decided for {missing}; supply a column for each (all-False is a claim, not a gap)"
        )
    outside = [time for time in boundaries if time not in grid]
    if outside:
        raise ValueError(
            f"reconstitution boundaries are absent from the decision grid: {outside[:5]}; a "
            "boundary off the grid would be checked over an empty period and admit everything"
        )
    values = gaps.reindex(columns=list(symbols)).to_numpy(dtype=bool)
    starts = grid.searchsorted(pd.DatetimeIndex(boundaries), side="left")
    result: list[pd.Series] = []
    for position in range(len(boundaries)):
        start = int(starts[position])
        stop = int(starts[position + 1]) if position + 1 < len(boundaries) else len(grid)
        result.append(pd.Series(values[start:stop].any(axis=0), index=list(symbols)))
    return result


def _require_boolean(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    """Reject anything but a genuinely Boolean frame.

    ``astype(bool)`` is the trap this exists to avoid: it maps ``NaN`` to **True**, so a coverage
    or eligibility frame carrying missing values would silently declare every one of them
    satisfied. That is a fail-open on exactly the cells that are unknown. Requiring the caller to
    have already decided each cell is the fail-closed alternative, and it is one line at each call
    site (``notna()`` produces a Boolean frame directly).
    """
    offending = [
        str(name) for name, dtype in frame.dtypes.items() if not pd.api.types.is_bool_dtype(dtype)
    ]
    if offending:
        raise ValueError(
            f"{label} must be a Boolean frame; columns {offending[:5]} are not. Converting here "
            "would map NaN to True and declare unknown cells satisfied."
        )
    return frame


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
