"""Restarting after a hard interruption, without making candidate failures retryable.

An in-process organizer error already pauses and resumes. A hard kill -- OOM, power, Ctrl-C --
journals nothing, and recover_interrupted_points then makes the in-flight point a permanent zero.
That rule guards against an organizer who sees a bad partial result and retries; observation is
silent, so there is no partial result to see, and the guard was costing a rerun it never bought.

What must NOT become retryable is a candidate failure, which is the case the guard actually exists
for. These tests assert both directions.
"""

from __future__ import annotations

import json
from pathlib import Path

from crypto_trade.cup50v2.lifecycle import (
    CandidateFailureError,
    append_record,
    observe_point,
    read_records,
    recover_interrupted_points,
    restart_interrupted_points,
)


def _started(journal: Path, point_id: str, team_id: str = "team-03") -> None:
    append_record(
        journal,
        "point-start",
        {"team_id": team_id, "point_id": point_id, "nomination_sha256": "d" * 64},
    )


def test_a_hard_interruption_becomes_resumable_not_a_zero(tmp_path: Path) -> None:
    journal = tmp_path / "journal.jsonl"
    stage = tmp_path / "stage"
    stage.mkdir()
    _started(journal, "p1")

    outcome = restart_interrupted_points(journal, private_stage=stage)
    assert outcome["resumable"] == ("p1",)
    assert outcome["completed"] == ()

    events = [record["event"] for record in read_records(journal)]
    assert "observation-paused" in events
    assert "point-terminal" not in events, "a restart must not settle the point"

    # recover must now leave it alone -- it is paused, not silently interrupted.
    assert recover_interrupted_points(journal) == ()


def test_a_point_that_finished_before_dying_is_completed_not_rerun(tmp_path: Path) -> None:
    """Evidence on disk means the work was done; re-running would read sealed data twice."""
    journal = tmp_path / "journal.jsonl"
    stage = tmp_path / "stage"
    stage.mkdir()
    _started(journal, "p2")
    (stage / "p2.json").write_bytes(json.dumps({"score": "irrelevant"}).encode())

    outcome = restart_interrupted_points(journal, private_stage=stage)
    assert outcome["completed"] == ("p2",)
    assert outcome["resumable"] == ()

    terminal = [r for r in read_records(journal) if r["event"] == "point-terminal"]
    assert len(terminal) == 1
    assert terminal[0]["payload"]["status"] == "succeeded"
    assert terminal[0]["payload"]["evidence_sha256"]


def test_a_candidate_failure_is_never_made_retryable(tmp_path: Path) -> None:
    """The distinction the guard actually carries.

    A strategy that blows up must stay a terminal zero no matter how often the run restarts,
    otherwise a lane could be retried until it survived. observe_point settles it before any
    interruption can occur, so it is never in the interrupted set.
    """
    journal = tmp_path / "journal.jsonl"
    stage = tmp_path / "stage"
    stage.mkdir()

    def blows_up():
        raise CandidateFailureError("equity reached zero")

    append_record(
        journal,
        "observation-batch-start",
        {"observation_order": ["team-03"], "expected_points": {"team-03": ["p3"]}},
    )
    terminal = observe_point(
        journal,
        team_id="team-03",
        point_id="p3",
        nomination_sha256="d" * 64,
        evaluator=blows_up,
        private_stage=stage,
    )
    assert terminal["status"] == "dnf" and terminal["score"] == 0.0

    outcome = restart_interrupted_points(journal, private_stage=stage)
    assert outcome == {
        "completed": (),
        "resumable": (),
    }, "candidate failure must not be restartable"

    settled = [r for r in read_records(journal) if r["event"] == "point-terminal"]
    assert len(settled) == 1 and settled[0]["payload"]["score"] == 0.0
