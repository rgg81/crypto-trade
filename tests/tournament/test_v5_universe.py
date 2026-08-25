from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence

import pandas as pd
import pytest

from crypto_trade.tournament.v5 import universe

BARS_PER_DAY = 3
FIRST_MONDAY = pd.Timestamp("2021-01-04", tz="UTC")

# Small parameters keep the fixtures readable; every rule under test is the production rule.
SMALL = {
    "size": 3,
    "trailing_days": 10,
    "minimum_history_days": 10,
    "persistence_rank": 5,
    "persistence_window_weeks": 3,
    "persistence_minimum_weeks": 2,
    "minimum_completeness": 1.0,
    "bars_per_day": BARS_PER_DAY,
}


def _bars(
    listings: Mapping[str, tuple[pd.Timestamp, float | Callable[[pd.Timestamp], float]]],
    *,
    through: pd.Timestamp,
    skip_days: Mapping[str, Sequence[pd.Timestamp]] | None = None,
) -> pd.DataFrame:
    """Continuous 8h bars per symbol from its listing date through ``through`` inclusive.

    Daily volume may be a constant or a function of the day, which lets a test give a
    long-listed contract a late volume spike — the only way to make pool entry late while
    leaving maturity and completeness trivially satisfied.
    """

    skipped = {symbol: set(days) for symbol, days in (skip_days or {}).items()}
    rows: list[dict[str, object]] = []
    for symbol, (listed, volume) in listings.items():
        for day in pd.date_range(listed, through, freq="D", tz="UTC"):
            if day in skipped.get(symbol, ()):
                continue
            daily = volume(day) if callable(volume) else volume
            for slot in range(BARS_PER_DAY):
                rows.append(
                    {
                        "open_time": day + pd.Timedelta(hours=8 * slot),
                        "symbol": symbol,
                        "quote_volume": daily / BARS_PER_DAY,
                    }
                )
    return pd.DataFrame(rows)


def _metadata(symbols: Iterable[str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": symbol,
                "contract_type": "PERPETUAL",
                "quote_asset": "USDT",
                "margin_asset": "USDT",
                "is_crypto": True,
                "onboard_date": pd.Timestamp("2019-01-01", tz="UTC"),
                "delivery_date": pd.NaT,
            }
            for symbol in symbols
        ]
    )


def _weeks(count: int, start: pd.Timestamp = FIRST_MONDAY) -> list[pd.Timestamp]:
    return list(pd.date_range(start, periods=count, freq="7D", tz="UTC"))


def _members(membership: pd.DataFrame, week: pd.Timestamp) -> list[str]:
    rows = membership[membership["reconstitution_time"] == week]
    return list(rows.sort_values("liquidity_rank")["symbol"])


def _run(listings, weeks, **overrides):  # type: ignore[no-untyped-def]
    skip_days = overrides.pop("skip_days", None)
    settings = {**SMALL, **overrides}
    through = weeks[-1] - pd.Timedelta(days=1)
    bars = _bars(listings, through=through, skip_days=skip_days)
    return universe.seasoned_membership(bars, _metadata(listings), weeks, **settings)


# -- completeness arithmetic ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("trailing", "completeness", "expected"),
    [(90, 0.95, 86), (90, 1.0, 90), (30, 0.95, 29), (10, 0.95, 10), (100, 0.5, 50)],
)
def test_required_complete_days(trailing: int, completeness: float, expected: int) -> None:
    assert universe.required_complete_days(trailing, completeness) == expected


def test_required_complete_days_rejects_impossible_settings() -> None:
    with pytest.raises(universe.SeasonedUniverseError, match="trailing_days must be positive"):
        universe.required_complete_days(0, 0.95)
    with pytest.raises(universe.SeasonedUniverseError, match="minimum_completeness"):
        universe.required_complete_days(90, 0.0)
    with pytest.raises(universe.SeasonedUniverseError, match="minimum_completeness"):
        universe.required_complete_days(90, 1.5)


# -- the three named rules ------------------------------------------------------------------


def test_a_mature_complete_persistent_contract_is_admitted() -> None:
    listed = FIRST_MONDAY - pd.Timedelta(days=60)
    listings = {
        "AAAUSDT": (listed, 900.0),
        "BBBUSDT": (listed, 800.0),
        "CCCUSDT": (listed, 700.0),
        "DDDUSDT": (listed, 600.0),
    }
    weeks = _weeks(5)
    membership = _run(listings, weeks)
    assert _members(membership, weeks[-1]) == ["AAAUSDT", "BBBUSDT", "CCCUSDT"]


def test_a_brand_new_high_volume_contract_is_excluded_by_maturity() -> None:
    """The RIVER case: entering the liquidity ranking at the top must not buy membership.

    The newcomer is given enough days to clear the ranking window's completeness threshold, so
    that maturity is the *only* rule standing between it and the top of the book. A shorter
    listing would be rejected by completeness first and the test would prove nothing.
    """

    listed = FIRST_MONDAY - pd.Timedelta(days=60)
    weeks = _weeks(5)
    newcomer_listed = weeks[-1] - pd.Timedelta(days=15)
    listings = {
        "AAAUSDT": (listed, 500.0),
        "BBBUSDT": (listed, 400.0),
        "CCCUSDT": (listed, 300.0),
        "NEWUSDT": (newcomer_listed, 99_000.0),
    }
    # Persistence is exempted on both runs (the window exceeds the available prior weeks), so
    # maturity is the only rule that differs between them.
    exempt = {"persistence_window_weeks": len(weeks) + 1}
    membership = _run(listings, weeks, minimum_history_days=30, **exempt)
    assert "NEWUSDT" not in _members(membership, weeks[-1])

    # Mutation: drop maturity below the newcomer's age and it takes rank 1 on volume alone.
    relaxed = _run(listings, weeks, minimum_history_days=10, **exempt)
    assert relaxed[relaxed["reconstitution_time"] == weeks[-1]].iloc[0]["symbol"] == "NEWUSDT"


def test_an_incomplete_contract_is_excluded_by_the_completeness_rule() -> None:
    listed = FIRST_MONDAY - pd.Timedelta(days=60)
    weeks = _weeks(5)
    gaps = [weeks[-1] - pd.Timedelta(days=offset) for offset in (2, 4, 6)]
    listings = {
        "AAAUSDT": (listed, 500.0),
        "BBBUSDT": (listed, 400.0),
        "CCCUSDT": (listed, 300.0),
        "GAPUSDT": (listed, 99_000.0),
    }
    through = weeks[-1] - pd.Timedelta(days=1)
    bars = _bars(listings, through=through, skip_days={"GAPUSDT": gaps})
    strict = universe.seasoned_membership(bars, _metadata(listings), weeks, **SMALL)
    assert "GAPUSDT" not in _members(strict, weeks[-1])

    # Mutation: relaxing completeness admits it, so the rule is doing the work.
    relaxed = universe.seasoned_membership(
        bars, _metadata(listings), weeks, **{**SMALL, "minimum_completeness": 0.6}
    )
    assert relaxed[relaxed["reconstitution_time"] == weeks[-1]].iloc[0]["symbol"] == "GAPUSDT"


def test_persistence_excludes_a_contract_that_only_just_entered_the_liquid_pool() -> None:
    """Volume that arrives in one week must not be enough; the pool membership must persist."""

    listed = FIRST_MONDAY - pd.Timedelta(days=200)
    weeks = _weeks(8)
    listings: dict[str, tuple[pd.Timestamp, object]] = {
        f"SYM{index:02d}USDT": (listed, 1_000.0 - index) for index in range(6)
    }
    # SPIKE has been listed as long as everyone else, so maturity and completeness are trivially
    # satisfied. It is dormant until six days before the final reconstitution, which is enough to
    # lift its trailing *median* above the field there and nowhere earlier. Late pool entry is
    # therefore the only thing that distinguishes it.
    spike_from = weeks[-1] - pd.Timedelta(days=6)
    listings["SPIKEUSDT"] = (listed, lambda day: 99_000.0 if day >= spike_from else 1.0)

    membership = _run(listings, weeks)
    assert "SPIKEUSDT" not in _members(membership, weeks[-1])

    # Mutation: exempt persistence (window exceeds available prior weeks) and the spike alone
    # buys rank 1, proving persistence is what rejected it.
    permissive = _run(listings, weeks, persistence_window_weeks=len(weeks) + 1)
    assert _members(permissive, weeks[-1])[0] == "SPIKEUSDT"


def test_persistence_is_exempt_until_a_full_prior_window_exists() -> None:
    """Judging a week against history that does not exist would empty the early universe."""

    listed = FIRST_MONDAY - pd.Timedelta(days=60)
    listings = {name: (listed, volume) for name, volume in (("AAAUSDT", 900.0),)}
    weeks = _weeks(3)
    membership = _run(listings, weeks)
    assert _members(membership, weeks[0]) == ["AAAUSDT"]


# -- shape and determinism ------------------------------------------------------------------


def test_missing_slots_are_never_backfilled() -> None:
    """A short universe is a truthful statement about the venue; padding it looks ahead."""

    listed = FIRST_MONDAY - pd.Timedelta(days=60)
    listings = {"AAAUSDT": (listed, 900.0), "BBBUSDT": (listed, 800.0)}
    weeks = _weeks(5)
    membership = _run(listings, weeks, size=10, persistence_rank=20)
    assert _members(membership, weeks[-1]) == ["AAAUSDT", "BBBUSDT"]
    assert universe.membership_shape(membership, size=10)["short_slots"] == len(weeks)


def test_ties_resolve_by_symbol_so_membership_is_deterministic() -> None:
    listed = FIRST_MONDAY - pd.Timedelta(days=60)
    listings = {name: (listed, 500.0) for name in ("CCCUSDT", "AAAUSDT", "BBBUSDT", "DDDUSDT")}
    weeks = _weeks(5)
    first = _run(listings, weeks)
    second = _run(dict(reversed(list(listings.items()))), weeks)
    assert _members(first, weeks[-1]) == ["AAAUSDT", "BBBUSDT", "CCCUSDT"]
    assert _members(first, weeks[-1]) == _members(second, weeks[-1])


def test_ranks_are_contiguous_and_ordered_by_volume() -> None:
    listed = FIRST_MONDAY - pd.Timedelta(days=60)
    listings = {
        "AAAUSDT": (listed, 300.0),
        "BBBUSDT": (listed, 900.0),
        "CCCUSDT": (listed, 600.0),
    }
    weeks = _weeks(5)
    membership = _run(listings, weeks)
    week = membership[membership["reconstitution_time"] == weeks[-1]].sort_values("liquidity_rank")
    assert list(week["liquidity_rank"]) == [1, 2, 3]
    assert list(week["symbol"]) == ["BBBUSDT", "CCCUSDT", "AAAUSDT"]
    assert list(week["trailing_quote_volume"]) == sorted(
        week["trailing_quote_volume"], reverse=True
    )


def test_membership_shape_reports_an_empty_universe_without_raising() -> None:
    empty = pd.DataFrame(columns=list(universe.MEMBERSHIP_COLUMNS))
    assert universe.membership_shape(empty) == {
        "reconstitutions": 0,
        "full_slots": 0,
        "short_slots": 0,
        "minimum_members": 0,
    }


# -- configuration validation ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"size": 0}, "size must be positive"),
        ({"persistence_rank": 2}, "persistence_rank must be at least"),
        ({"minimum_history_days": 0}, "minimum_history_days must be positive"),
        ({"persistence_window_weeks": 0}, "persistence_window_weeks must be positive"),
        ({"persistence_minimum_weeks": 0}, "persistence_minimum_weeks must lie"),
        ({"persistence_minimum_weeks": 99}, "persistence_minimum_weeks must lie"),
    ],
)
def test_invalid_settings_are_rejected(overrides: dict[str, object], match: str) -> None:
    listings = {"AAAUSDT": (FIRST_MONDAY - pd.Timedelta(days=60), 500.0)}
    with pytest.raises(universe.SeasonedUniverseError, match=match):
        _run(listings, _weeks(3), **overrides)
