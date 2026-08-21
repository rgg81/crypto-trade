"""Integrity review verifies the start/terminal relation, not the order they happen to land in.

The original check paired the i-th start with the i-th terminal, which holds only when points are
observed strictly one at a time. Observing six points concurrently inside one lane -- legal, since
observe_point enforces order per lane and not per point -- makes terminals land in completion order
and the pairing fail while nothing is actually wrong. Amendment A14 replaced it with the property
it stood in for.

These tests exist to show the replacement is stronger and not merely more permissive: it now
rejects things the positional check never looked at.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from crypto_trade.cup50v2.journal import append_record
from crypto_trade.cup50v2.lifecycle import integrity_review

FIELD = {
    "field_sha256": "f" * 64,
    "observation_order": ["team-01", "team-02"],
    "dispositions": {
        "team-01": {"state": "nominated", "point_ids": ["team-01-p00", "team-01-p01"]},
        "team-02": {"state": "nominated", "point_ids": ["team-02-p00"]},
    },
}


def _journal(tmp_path: Path, events: list[tuple[str, str, str]]) -> Path:
    path = tmp_path / "journal.jsonl"
    append_record(path, "observation-batch-start", {"observation_order": ["team-01", "team-02"]})
    for event, team_id, point_id in events:
        append_record(path, event, {"team_id": team_id, "point_id": point_id})
    return path


def _stage(tmp_path: Path, point_ids: list[str]) -> Path:
    stage = tmp_path / "points"
    stage.mkdir(parents=True, exist_ok=True)
    for point_id in point_ids:
        (stage / f"{point_id}.json").write_text(json.dumps({"point": point_id}))
    return stage


def test_interleaved_completion_inside_a_lane_passes(tmp_path: Path) -> None:
    """The shape the real run produced: starts A,B then terminals B,A."""
    journal = _journal(
        tmp_path,
        [
            ("point-start", "team-01", "team-01-p00"),
            ("point-start", "team-01", "team-01-p01"),
            ("point-terminal", "team-01", "team-01-p01"),   # finished second, landed first
            ("point-terminal", "team-01", "team-01-p00"),
            ("point-start", "team-02", "team-02-p00"),
            ("point-terminal", "team-02", "team-02-p00"),
        ],
    )
    stage = _stage(tmp_path, ["team-01-p00", "team-01-p01", "team-02-p00"])
    review = integrity_review(field=FIELD, journal_path=journal, private_stage=stage)
    assert review["status"] == "passed"


def test_a_terminal_that_precedes_its_own_start_is_refused(tmp_path: Path) -> None:
    """Counts and sets both match here, so only the relation can catch it.

    The earlier count and set checks fire first on cruder damage; this fixture keeps three starts
    and three terminals covering exactly the frozen field, and corrupts only the order of one pair.
    """
    journal = _journal(
        tmp_path,
        [
            ("point-terminal", "team-01", "team-01-p01"),   # lands before its own start
            ("point-start", "team-01", "team-01-p00"),
            ("point-terminal", "team-01", "team-01-p00"),
            ("point-start", "team-01", "team-01-p01"),
            ("point-start", "team-02", "team-02-p00"),
            ("point-terminal", "team-02", "team-02-p00"),
        ],
    )
    stage = _stage(tmp_path, ["team-01-p00", "team-01-p01", "team-02-p00"])
    with pytest.raises(ValueError, match="terminated without a durable start"):
        integrity_review(field=FIELD, journal_path=journal, private_stage=stage)


def test_a_lane_resumed_after_another_began_is_refused(tmp_path: Path) -> None:
    """Concurrency is permitted inside one lane, never across lanes."""
    journal = _journal(
        tmp_path,
        [
            ("point-start", "team-01", "team-01-p00"),
            ("point-terminal", "team-01", "team-01-p00"),
            ("point-start", "team-02", "team-02-p00"),
            ("point-terminal", "team-02", "team-02-p00"),
            ("point-start", "team-01", "team-01-p01"),      # lane reopened
            ("point-terminal", "team-01", "team-01-p01"),
        ],
    )
    stage = _stage(tmp_path, ["team-01-p00", "team-01-p01", "team-02-p00"])
    with pytest.raises(ValueError, match="resumed after another lane began"):
        integrity_review(field=FIELD, journal_path=journal, private_stage=stage)


def test_lanes_out_of_the_frozen_order_are_refused(tmp_path: Path) -> None:
    """Something the positional check never looked at."""
    journal = _journal(
        tmp_path,
        [
            ("point-start", "team-02", "team-02-p00"),      # frozen order says team-01 first
            ("point-terminal", "team-02", "team-02-p00"),
            ("point-start", "team-01", "team-01-p00"),
            ("point-terminal", "team-01", "team-01-p00"),
            ("point-start", "team-01", "team-01-p01"),
            ("point-terminal", "team-01", "team-01-p01"),
        ],
    )
    stage = _stage(tmp_path, ["team-01-p00", "team-01-p01", "team-02-p00"])
    with pytest.raises(ValueError, match="not observed in the order the field froze"):
        integrity_review(field=FIELD, journal_path=journal, private_stage=stage)
