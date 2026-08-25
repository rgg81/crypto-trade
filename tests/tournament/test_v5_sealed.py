from __future__ import annotations

import pandas as pd
import pytest

from crypto_trade.tournament.v5 import sealed

DEV_START = "2020-08-02"
DEV_END = "2024-02-01"
RULE = {
    "block_days": 45,
    "stride": 7,
    "residues": (1, 4),
    "interleaved_count": 7,
    "terminal_block": True,
}
PURGE_DAYS = 5
EMBARGO_DAYS = 10

FROZEN_SCHEDULE = (
    ("2020-09-16", "2020-10-31"),
    ("2021-01-29", "2021-03-15"),
    ("2021-07-28", "2021-09-11"),
    ("2021-12-10", "2022-01-24"),
    ("2022-06-08", "2022-07-23"),
    ("2022-10-21", "2022-12-05"),
    ("2023-04-19", "2023-06-03"),
    ("2023-12-18", "2024-02-01"),
)


def _blocks() -> tuple[sealed.Interval, ...]:
    return sealed.sealed_blocks(start=DEV_START, end_exclusive=DEV_END, **RULE)


def _dev_index() -> pd.DatetimeIndex:
    return pd.date_range(
        DEV_START, pd.Timestamp(DEV_END) - pd.Timedelta(days=1), freq="D", tz="UTC"
    )


def _partition() -> sealed.SealedPartition:
    return sealed.partition(
        _dev_index(), _blocks(), purge_days=PURGE_DAYS, embargo_days=EMBARGO_DAYS
    )


def test_frozen_schedule_is_reproducible_from_the_charter_rule() -> None:
    """An authority nobody can re-derive is an authority nobody can audit."""

    generated = tuple(
        (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")) for start, end in _blocks()
    )
    assert generated == FROZEN_SCHEDULE
    sealed.assert_schedule_matches_rule(
        FROZEN_SCHEDULE, start=DEV_START, end_exclusive=DEV_END, **RULE
    )


def test_a_tampered_schedule_is_rejected() -> None:
    """Mutation guard: the bridge between rule and frozen intervals must actually bite."""

    tampered = (("2020-09-17", "2020-11-01"), *FROZEN_SCHEDULE[1:])
    with pytest.raises(sealed.SealedPartitionError, match="does not match the charter"):
        sealed.assert_schedule_matches_rule(
            tampered, start=DEV_START, end_exclusive=DEV_END, **RULE
        )


def test_partition_is_disjoint_and_exhaustive() -> None:
    partition = _partition()
    index = _dev_index()
    assert partition.total_days == len(index)
    union = partition.visible.union(partition.sealed).union(partition.excluded)
    assert len(union) == len(index)
    assert partition.visible.intersection(partition.sealed).empty
    assert partition.visible.intersection(partition.excluded).empty
    assert partition.sealed.intersection(partition.excluded).empty


def test_measured_budget_matches_the_charter() -> None:
    summary = _partition().summary()
    assert summary == {
        "block_count": 8,
        "visible_days": 808,
        "sealed_days": 360,
        "excluded_days": 110,
        "total_days": 1278,
    }


def test_every_sealed_day_lies_inside_a_declared_block() -> None:
    partition = _partition()
    for day in partition.sealed:
        assert any(start <= day < end for start, end in partition.blocks), day


def test_margin_brackets_every_block_on_both_sides() -> None:
    partition = _partition()
    excluded = set(partition.excluded)
    for start, end in partition.blocks:
        for offset in range(1, PURGE_DAYS + 1):
            day = start - pd.Timedelta(days=offset)
            if day >= partition.visible.min():
                assert day in excluded, f"purge day {day.date()} not withheld"
        for offset in range(EMBARGO_DAYS):
            day = end + pd.Timedelta(days=offset)
            if day <= partition.visible.max():
                assert day in excluded, f"embargo day {day.date()} not withheld"


def test_the_luna_collapse_is_visible_to_teams() -> None:
    """A May-2022-style collapse is exactly the event a real book has to survive.

    It stays in the data, unmodified, and it stays in the *visible* half so a team meets it
    during research rather than discovering it for the first time on sealed or holdout data.
    """

    partition = _partition()
    collapse = pd.Timestamp("2022-05-13", tz="UTC")
    assert collapse in partition.visible
    assert collapse not in partition.sealed
    assert collapse not in partition.excluded


def test_sealed_blocks_span_distinct_market_regimes() -> None:
    """Interleaving exists to stratify confirmation across regimes rather than sample one."""

    years = {start.year for start, _ in _blocks()}
    assert years == {2020, 2021, 2022, 2023}
    starts = [start for start, _ in _blocks()]
    assert len({start.weekday() for start in starts}) > 1, "schedule aliases with the week"


def test_terminal_block_ends_the_development_window() -> None:
    blocks = _blocks()
    assert blocks[-1][1] == pd.Timestamp(DEV_END, tz="UTC")


def test_blocks_never_overlap() -> None:
    blocks = _blocks()
    for (_, previous_end), (next_start, _) in zip(blocks, blocks[1:], strict=False):
        assert next_start >= previous_end


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"block_days": 0}, "must be positive"),
        ({"stride": 0}, "must be positive"),
        ({"residues": ()}, "at least one residue"),
        ({"residues": (0, 9)}, r"residue must lie"),
        ({"residues": (1, 1)}, "unique"),
        ({"interleaved_count": 99}, "fits only"),
    ],
)
def test_invalid_rules_are_rejected(overrides: dict[str, object], match: str) -> None:
    arguments = {**RULE, **overrides}
    with pytest.raises(sealed.SealedPartitionError, match=match):
        sealed.sealed_blocks(start=DEV_START, end_exclusive=DEV_END, **arguments)  # type: ignore[arg-type]


def test_empty_or_inverted_window_is_rejected() -> None:
    with pytest.raises(sealed.SealedPartitionError, match="non-empty"):
        sealed.sealed_blocks(start=DEV_END, end_exclusive=DEV_START, **RULE)


def test_overlapping_declared_blocks_are_rejected() -> None:
    overlapping = [("2021-01-01", "2021-03-01"), ("2021-02-01", "2021-04-01")]
    with pytest.raises(sealed.SealedPartitionError, match="overlap"):
        sealed.partition(_dev_index(), overlapping, purge_days=1, embargo_days=1)


def test_naive_index_is_rejected() -> None:
    naive = pd.date_range(DEV_START, periods=100, freq="D")
    with pytest.raises(sealed.SealedPartitionError, match="timezone-aware"):
        sealed.partition(naive, _blocks(), purge_days=1, embargo_days=1)


def test_summary_carries_no_returns_or_membership() -> None:
    """The organizer publishes the shape of the split; publishing which days are sealed
    before the release would hand a team the schedule it is not entitled to."""

    summary = _partition().summary()
    assert set(summary) == {
        "block_count",
        "visible_days",
        "sealed_days",
        "excluded_days",
        "total_days",
    }
    assert all(isinstance(value, int) for value in summary.values())
