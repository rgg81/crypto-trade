from __future__ import annotations

from collections.abc import Iterable, Mapping

import pandas as pd
import pytest

from crypto_trade.tournament import snapshot
from crypto_trade.tournament.data import point_in_time_top40

BARS_PER_DAY = 3
EVALUATION_START = pd.Timestamp("2021-04-05", tz="UTC")
HARD_END = pd.Timestamp("2021-05-03", tz="UTC")
WARMUP_START = pd.Timestamp("2020-01-01", tz="UTC")

LEGACY_CONFIG = {"size": 3, "trailing_days": 10, "minimum_history_days": 10}
SEASONED_CONFIG = {
    "rule": snapshot.SEASONED_MEMBERSHIP_RULE,
    "size": 3,
    "trailing_days": 10,
    "minimum_history_days": 120,
    "persistence_rank": 5,
    "persistence_window_weeks": 2,
    "persistence_minimum_weeks": 2,
    "minimum_completeness": 1.0,
}


def _bars(listings: Mapping[str, tuple[pd.Timestamp, float]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for symbol, (listed, volume) in listings.items():
        for day in pd.date_range(listed, HARD_END, freq="D", tz="UTC"):
            for slot in range(BARS_PER_DAY):
                rows.append(
                    {
                        "open_time": day + pd.Timedelta(hours=8 * slot),
                        "symbol": symbol,
                        "quote_volume": volume / BARS_PER_DAY,
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


def _build(listings, universe_config):  # type: ignore[no-untyped-def]
    return snapshot._build_membership(
        _bars(listings),
        _metadata(listings),
        evaluation_start=EVALUATION_START,
        hard_end=HARD_END,
        universe_config=dict(universe_config),
        warmup_start=WARMUP_START,
    )


def _mature_field() -> dict[str, tuple[pd.Timestamp, float]]:
    listed = EVALUATION_START - pd.Timedelta(days=300)
    return {
        "AAAUSDT": (listed, 900.0),
        "BBBUSDT": (listed, 800.0),
        "CCCUSDT": (listed, 700.0),
        "DDDUSDT": (listed, 600.0),
    }


def test_the_default_rule_is_the_legacy_rule_and_is_unchanged() -> None:
    """A snapshot built without a rule key must behave exactly as it did before V5 existed."""

    listings = _mature_field()
    built = _build(listings, LEGACY_CONFIG)

    first = EVALUATION_START.floor("D") - pd.Timedelta(days=EVALUATION_START.weekday())
    last_day = (HARD_END - pd.Timedelta(nanoseconds=1)).floor("D")
    last = last_day - pd.Timedelta(days=last_day.weekday())
    expected = (
        point_in_time_top40(
            _bars(listings),
            _metadata(listings),
            pd.date_range(first, last, freq="7D", tz="UTC"),
            top_n=LEGACY_CONFIG["size"],
            trailing_days=LEGACY_CONFIG["trailing_days"],
            min_history_days=LEGACY_CONFIG["minimum_history_days"],
            bars_per_day=BARS_PER_DAY,
        )
        .sort_values(["reconstitution_time", "liquidity_rank"])
        .reset_index(drop=True)
    )

    pd.testing.assert_frame_equal(built, expected)


def test_naming_the_legacy_rule_explicitly_is_identical_to_omitting_it() -> None:
    listings = _mature_field()
    implicit = _build(listings, LEGACY_CONFIG)
    explicit = _build(listings, {**LEGACY_CONFIG, "rule": snapshot.LEGACY_MEMBERSHIP_RULE})
    pd.testing.assert_frame_equal(implicit, explicit)


def test_the_seasoned_rule_admits_a_mature_field() -> None:
    membership = _build(_mature_field(), SEASONED_CONFIG)
    last_week = membership["reconstitution_time"].max()
    members = membership[membership["reconstitution_time"] == last_week]
    assert list(members.sort_values("liquidity_rank")["symbol"]) == [
        "AAAUSDT",
        "BBBUSDT",
        "CCCUSDT",
    ]


def test_the_two_rules_disagree_where_seasoning_matters() -> None:
    """Mutation guard: a dispatch that never changes the answer is not a dispatch.

    The newcomer is the most liquid contract in the field and has enough days to clear the
    ranking window, so the legacy rule takes it at rank 1 and only seasoning rejects it.
    """

    listings = _mature_field()
    listings["NEWUSDT"] = (EVALUATION_START - pd.Timedelta(days=20), 99_000.0)

    legacy = _build(listings, LEGACY_CONFIG)
    seasoned = _build(listings, SEASONED_CONFIG)
    last_week = legacy["reconstitution_time"].max()

    legacy_members = set(legacy[legacy["reconstitution_time"] == last_week]["symbol"])
    seasoned_members = set(seasoned[seasoned["reconstitution_time"] == last_week]["symbol"])
    assert "NEWUSDT" in legacy_members
    assert "NEWUSDT" not in seasoned_members


def test_an_unknown_rule_is_rejected_rather_than_defaulted() -> None:
    """Failing closed matters here: silently defaulting would build a snapshot whose funding
    coverage does not match the rule the charter declares."""

    with pytest.raises(ValueError, match="unknown universe membership rule"):
        _build(_mature_field(), {**LEGACY_CONFIG, "rule": "something-else"})


def test_an_empty_reconstitution_is_rejected() -> None:
    """A week with no tradable universe must stop the build, not produce a silent hole."""

    listings = {"AAAUSDT": (EVALUATION_START - pd.Timedelta(days=2), 100.0)}
    with pytest.raises(ValueError, match="empty point-in-time universe"):
        _build(listings, LEGACY_CONFIG)


def test_the_seasoned_grid_is_armed_before_the_first_scored_week() -> None:
    """Persistence judged against prior weeks must have prior weeks to judge against.

    A grid beginning at the first scored week exempts its own opening weeks and silently runs a
    laxer rule there. Extending backwards into warmup and discarding the extension makes every
    scored week judged identically -- and the returned frame must still start where scoring does.
    """

    listed = EVALUATION_START - pd.Timedelta(days=300)
    listings = {f"SYM{index:02d}USDT": (listed, 1_000.0 - index) for index in range(6)}
    membership = _build(listings, SEASONED_CONFIG)

    first_scored = EVALUATION_START.floor("D") - pd.Timedelta(days=EVALUATION_START.weekday())
    assert membership["reconstitution_time"].min() == first_scored

    # Every scored week, including the first, must survive the persistence rule rather than be
    # exempted from it: with a stable field that means the full membership is present throughout.
    counts = membership.groupby("reconstitution_time")["symbol"].nunique()
    assert set(counts) == {SEASONED_CONFIG["size"]}


def test_a_warmup_too_short_to_arm_persistence_is_rejected() -> None:
    """Failing loudly beats quietly scoring the opening weeks under a different rule."""

    listings = {"AAAUSDT": (EVALUATION_START - pd.Timedelta(days=300), 900.0)}
    with pytest.raises(ValueError, match="warmup is too short to arm the persistence window"):
        snapshot._build_membership(
            _bars(listings),
            _metadata(listings),
            evaluation_start=EVALUATION_START,
            hard_end=HARD_END,
            universe_config=dict(SEASONED_CONFIG),
            warmup_start=EVALUATION_START - pd.Timedelta(days=5),
        )


def test_the_seasoned_rule_requires_a_warmup_start() -> None:
    listings = {"AAAUSDT": (EVALUATION_START - pd.Timedelta(days=300), 900.0)}
    with pytest.raises(ValueError, match="requires warmup_start"):
        snapshot._build_membership(
            _bars(listings),
            _metadata(listings),
            evaluation_start=EVALUATION_START,
            hard_end=HARD_END,
            universe_config=dict(SEASONED_CONFIG),
        )
