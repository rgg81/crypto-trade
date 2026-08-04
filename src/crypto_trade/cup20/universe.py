"""Point-in-time, hysteresis-stabilised top-20 membership."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

MEMBERSHIP_COLUMNS = ("reconstitution_time", "symbol", "liquidity_rank", "trailing_quote_volume")


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
) -> pd.DataFrame:
    """Build point-in-time membership from daily quote volume.

    A symbol is a candidate only when it has a *complete* ``lookback_days`` window of daily quote
    volume strictly before the boundary and is eligible on the boundary itself. The completeness
    requirement doubles as the minimum listing age. Incumbents survive to ``exit_rank``; new
    entrants require ``entry_rank``.
    """
    if lookback_days < 1 or target_size < 1:
        raise ValueError("lookback_days and target_size must be positive")
    if entry_rank < 1 or exit_rank < entry_rank:
        raise ValueError("exit_rank must be at least entry_rank")
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
        averages = history.mean()
        candidates = averages[complete & eligible_now].dropna()
        ordered = candidates.sort_values(ascending=False, kind="mergesort")
        ranks = {symbol: index + 1 for index, symbol in enumerate(ordered.index)}

        kept = [s for s in ordered.index if s in previous and ranks[s] <= exit_rank][:target_size]
        entrants = [s for s in ordered.index if s not in previous and ranks[s] <= entry_rank]
        members = kept + [s for s in entrants if s not in kept]
        members = members[:target_size]

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
