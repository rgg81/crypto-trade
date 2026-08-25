"""Seasoned point-in-time Top-40 membership.

V4 ranked on a 30-day median quote volume and required 30 days of history, which is short enough
for a newly listed, event-driven contract to enter the universe in the same week a strategy first
trades it. RIVER did exactly that on 2026-01-05 — it entered at rank 31 with zero prior membership
and went on to supply roughly 84% of that month's gross contribution for the V4-R9 winner.

The seasoning rule here is general, not an after-the-fact exclusion of one symbol. Three separate
requirements have to hold, and each is named so it can be tested on its own:

* **maturity** — the contract has existed for at least ``minimum_history_days``;
* **completeness** — at least ``minimum_completeness`` of the expected bars in the ranking window
  are actually present, so a half-traded contract cannot rank on a thin sample;
* **persistence** — the contract has been in the liquid pool for most of the recent past, so a
  single week of promotional volume cannot buy membership.

A contract that fails any of them is simply absent. Missing slots are held as cash and are never
backfilled with an immature contract merely to reach ``size``: a short universe is a truthful
statement about the venue at that date, and padding it would be a silent look-ahead into which
contracts later turned out to be tradable.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import pandas as pd

from crypto_trade.tournament.data import point_in_time_top40


class SeasonedUniverseError(ValueError):
    """Raised when a seasoned-universe request is internally inconsistent."""


MEMBERSHIP_COLUMNS = (
    "reconstitution_time",
    "symbol",
    "liquidity_rank",
    "trailing_quote_volume",
)


def required_complete_days(trailing_days: int, minimum_completeness: float) -> int:
    """Expected-bar threshold for the ranking window.

    ``point_in_time_top40`` counts distinct dates on which a symbol produced a *full* set of bars,
    so passing ``trailing_days`` itself would demand 100% completeness and drop any contract that
    saw a single venue outage. The completeness fraction is applied here instead.
    """

    if trailing_days < 1:
        raise SeasonedUniverseError("trailing_days must be positive")
    if not 0.0 < minimum_completeness <= 1.0:
        raise SeasonedUniverseError("minimum_completeness must lie in (0, 1]")
    return max(1, math.ceil(minimum_completeness * trailing_days))


def _first_observed_date(bars: pd.DataFrame, bars_per_day: int) -> pd.Series:
    """Earliest fully observed UTC date per symbol.

    Maturity is measured from the first *complete* day rather than the first bar, so a contract
    that listed mid-day does not get credited with a day it only partly traded.
    """

    frame = bars.loc[:, ["open_time", "symbol"]].copy()
    frame["open_time"] = pd.to_datetime(frame["open_time"], utc=True)
    frame["date"] = frame["open_time"].dt.floor("D")
    counts = frame.groupby(["symbol", "date"], observed=True)["open_time"].nunique()
    complete = counts[counts == bars_per_day]
    if complete.empty:
        return pd.Series(dtype="datetime64[ns, UTC]")
    return complete.reset_index().groupby("symbol", observed=True)["date"].min()


def seasoned_membership(
    bars: pd.DataFrame,
    contract_metadata: pd.DataFrame,
    reconstitution_times: Sequence[pd.Timestamp],
    *,
    size: int = 40,
    trailing_days: int = 90,
    minimum_history_days: int = 90,
    persistence_rank: int = 60,
    persistence_window_weeks: int = 10,
    persistence_minimum_weeks: int = 8,
    minimum_completeness: float = 0.95,
    bars_per_day: int = 3,
) -> pd.DataFrame:
    """Build weekly seasoned Top-``size`` membership from completed prior days only.

    The liquid pool is the point-in-time Top-``persistence_rank`` by trailing median quote volume.
    Maturity and persistence then select the final membership from that pool. Persistence is
    measured over *strictly prior* reconstitutions, so a week never counts toward its own
    admission, and the first ``persistence_window_weeks`` reconstitutions are exempt because no
    prior history exists to judge them against.
    """

    if size < 1:
        raise SeasonedUniverseError("size must be positive")
    if persistence_rank < size:
        raise SeasonedUniverseError("persistence_rank must be at least the membership size")
    if minimum_history_days < 1:
        raise SeasonedUniverseError("minimum_history_days must be positive")
    if persistence_window_weeks < 1:
        raise SeasonedUniverseError("persistence_window_weeks must be positive")
    if not 1 <= persistence_minimum_weeks <= persistence_window_weeks:
        raise SeasonedUniverseError(
            "persistence_minimum_weeks must lie in [1, persistence_window_weeks]"
        )

    complete_days = required_complete_days(trailing_days, minimum_completeness)
    ordered_times = sorted(pd.to_datetime(list(reconstitution_times), utc=True))

    pool = point_in_time_top40(
        bars,
        contract_metadata,
        ordered_times,
        top_n=persistence_rank,
        trailing_days=trailing_days,
        min_history_days=complete_days,
        bars_per_day=bars_per_day,
    )
    if pool.empty:
        return pd.DataFrame(columns=MEMBERSHIP_COLUMNS)

    pool_times = pd.to_datetime(pool["reconstitution_time"], utc=True)
    pool_by_time = {
        timestamp: group for timestamp, group in pool.groupby(pool_times, sort=True, observed=True)
    }
    pool_symbols = {timestamp: set(group["symbol"]) for timestamp, group in pool_by_time.items()}
    first_seen = _first_observed_date(bars, bars_per_day)

    rows: list[dict[str, object]] = []
    for index, as_of in enumerate(ordered_times):
        candidates = pool_by_time.get(as_of)
        if candidates is None or candidates.empty:
            continue

        matured_on_or_before = as_of.floor("D") - pd.Timedelta(days=minimum_history_days)
        listed = first_seen.reindex(candidates["symbol"])
        mature = listed.notna().to_numpy() & (listed <= matured_on_or_before).to_numpy()
        candidates = candidates.loc[mature]
        if candidates.empty:
            continue

        prior_times = ordered_times[max(0, index - persistence_window_weeks) : index]
        if len(prior_times) >= persistence_window_weeks:
            appearances = candidates["symbol"].map(
                lambda symbol: sum(symbol in pool_symbols.get(t, ()) for t in prior_times)
            )
            candidates = candidates.loc[appearances.to_numpy() >= persistence_minimum_weeks]
        if candidates.empty:
            continue

        selected = candidates.sort_values(
            ["trailing_quote_volume", "symbol"], ascending=[False, True], kind="mergesort"
        ).head(size)
        for rank, record in enumerate(selected.itertuples(index=False), start=1):
            rows.append(
                {
                    "reconstitution_time": as_of,
                    "symbol": record.symbol,
                    "liquidity_rank": rank,
                    "trailing_quote_volume": float(record.trailing_quote_volume),
                }
            )

    return pd.DataFrame(rows, columns=list(MEMBERSHIP_COLUMNS))


def membership_shape(membership: pd.DataFrame, size: int = 40) -> dict[str, object]:
    """Per-reconstitution slot occupancy, for the snapshot manifest and the charter.

    A universe that is routinely short is a fact about the venue that the charter has to state,
    not something to discover mid-tournament when a breadth floor starts failing.
    """

    if membership.empty:
        return {"reconstitutions": 0, "full_slots": 0, "short_slots": 0, "minimum_members": 0}
    counts = membership.groupby("reconstitution_time", observed=True)["symbol"].nunique()
    return {
        "reconstitutions": int(counts.size),
        "full_slots": int((counts >= size).sum()),
        "short_slots": int((counts < size).sum()),
        "minimum_members": int(counts.min()),
    }


__all__ = [
    "MEMBERSHIP_COLUMNS",
    "SeasonedUniverseError",
    "membership_shape",
    "required_complete_days",
    "seasoned_membership",
]
