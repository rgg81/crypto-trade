"""Freeze, one-shot observation, integrity review, and atomic publication."""

from __future__ import annotations

import dataclasses
import hashlib
import hmac
import json
import os
import shutil
import tempfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from crypto_trade.cup50.config import TEAM_IDS
from crypto_trade.cup50.journal import append_record, read_records
from crypto_trade.cup50.scoring import (
    RankedEntry,
    rank_entries,
    round_half_even,
    rounded_neighbourhood,
    score_neighbourhood,
)


class CandidateFailureError(RuntimeError):
    """A candidate-caused terminal failure; its point receives zero."""


class OrganizerFailureError(RuntimeError):
    """A data/evaluator failure; observation pauses and scoring is not amended."""


def _canonical(payload: object) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _digest(payload: object) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def freeze_field(
    destination: str | Path,
    *,
    dispositions: Mapping[str, Mapping[str, object]],
    observation_order: Sequence[str],
    activation_sha256: str,
    signing_key: bytes,
) -> Mapping[str, object]:
    """Freeze all twelve lane dispositions and order before sealed data is restored."""
    path = Path(destination)
    if path.exists():
        raise FileExistsError("CUP-50 field has already closed")
    if set(dispositions) != set(TEAM_IDS):
        raise ValueError("field close requires exactly twelve lane dispositions")
    if (
        tuple(sorted(observation_order)) != tuple(sorted(TEAM_IDS))
        or len(set(observation_order)) != 12
    ):
        raise ValueError("observation order must contain every team exactly once")
    for team_id, disposition in dispositions.items():
        state = disposition.get("state")
        if state not in {"nominated", "dnf"}:
            raise ValueError(f"invalid disposition for {team_id}")
        if state == "nominated" and not disposition.get("nomination_sha256"):
            raise ValueError(f"nominated lane {team_id} lacks its nomination binding")
        if state == "nominated":
            point_ids = disposition.get("point_ids")
            if (
                not isinstance(point_ids, list)
                or not point_ids
                or len(point_ids) != len(set(map(str, point_ids)))
            ):
                raise ValueError(f"nominated lane {team_id} lacks unique frozen point_ids")
        if state == "dnf" and not disposition.get("reason"):
            raise ValueError(f"DNF lane {team_id} lacks a reason")
    body: dict[str, object] = {
        "schema_version": 1,
        "namespace": "cup50",
        "activation_sha256": activation_sha256,
        "dispositions": {team: dict(dispositions[team]) for team in TEAM_IDS},
        "observation_order": list(observation_order),
    }
    signature = hmac.new(signing_key, _canonical(body), hashlib.sha256).hexdigest()
    record = {**body, "field_sha256": _digest(body), "hmac_sha256": signature}
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical(record))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return record


def verify_field(path: str | Path, *, signing_key: bytes) -> Mapping[str, object]:
    record = json.loads(Path(path).read_text())
    signature = record.pop("hmac_sha256", None)
    digest = record.pop("field_sha256", None)
    if digest != _digest(record):
        raise ValueError("field close digest mismatch")
    expected = hmac.new(signing_key, _canonical(record), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(str(signature), expected):
        raise ValueError("field close authentication failed")
    return {**record, "field_sha256": digest, "hmac_sha256": signature}


def start_observation_batch(
    journal_path: str | Path,
    *,
    field_sha256: str,
    sealed_manifest_sha256: str,
    observation_order: Sequence[str] = (),
    expected_points: Mapping[str, Sequence[str]] | None = None,
) -> Mapping[str, object]:
    if read_records(journal_path):
        raise ValueError("historical observation is one-shot and has already started")
    for label, value in (
        ("field_sha256", field_sha256),
        ("sealed_manifest_sha256", sealed_manifest_sha256),
    ):
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError(f"{label} must be a lowercase SHA-256")
    # fsync happens inside append_record.  Only after this function returns may a sealed loader run.
    return append_record(
        journal_path,
        "observation-batch-start",
        {
            "field_sha256": field_sha256,
            "sealed_manifest_sha256": sealed_manifest_sha256,
            "observation_order": list(observation_order),
            "expected_points": {
                str(team): list(points) for team, points in (expected_points or {}).items()
            },
        },
    )


def recover_interrupted_points(journal_path: str | Path) -> tuple[str, ...]:
    """Make every start without a terminal record a permanent zero, without rereading data."""
    records = read_records(journal_path)
    started: dict[str, Mapping[str, object]] = {}
    terminal: set[str] = set()
    organizer_paused: set[str] = set()
    for record in records:
        payload = record["payload"]
        if record["event"] == "point-start":
            started[str(payload["point_id"])] = payload
        elif record["event"] == "point-terminal":
            terminal.add(str(payload["point_id"]))
        elif record["event"] == "observation-paused":
            organizer_paused.add(str(payload["point_id"]))
        elif record["event"] == "point-resume":
            organizer_paused.discard(str(payload["point_id"]))
    interrupted = tuple(sorted(set(started) - terminal - organizer_paused))
    for point_id in interrupted:
        append_record(
            journal_path,
            "point-terminal",
            {
                "point_id": point_id,
                "team_id": started[point_id]["team_id"],
                "status": "dnf",
                "score": 0.0,
                "reason": "interrupted-after-durable-start",
            },
        )
    return interrupted


def observe_point(
    journal_path: str | Path,
    *,
    team_id: str,
    point_id: str,
    nomination_sha256: str,
    evaluator: Callable[[], Mapping[str, object]],
    private_stage: str | Path,
    resume_organizer_failure: bool = False,
) -> Mapping[str, object]:
    """Start durably, evaluate silently, and write exactly one permanent terminal record."""
    records = read_records(journal_path)
    if not records or records[0]["event"] != "observation-batch-start":
        raise ValueError("batch marker must be durable before the first point")
    if records[-1]["event"] == "observation-paused" and (
        not resume_organizer_failure or records[-1]["payload"].get("point_id") != point_id
    ):
        raise ValueError("observation is paused pending organizer recovery")
    order = [str(value) for value in records[0]["payload"].get("observation_order", [])]
    expected = records[0]["payload"].get("expected_points", {})
    if expected and point_id not in set(map(str, expected.get(team_id, []))):
        raise ValueError("point is not in the frozen nomination point set")
    started_teams = [
        str(record["payload"]["team_id"]) for record in records if record["event"] == "point-start"
    ]
    if order:
        if team_id not in order:
            raise ValueError("point team is not in the frozen observation order")
        if not started_teams and team_id != order[0]:
            raise ValueError("point violates the frozen observation order")
        if started_teams and team_id != started_teams[-1]:
            previous_index = order.index(started_teams[-1])
            if previous_index + 1 >= len(order) or team_id != order[previous_index + 1]:
                raise ValueError("point violates the frozen observation order")
    point_records = [record for record in records if record["payload"].get("point_id") == point_id]
    if point_records:
        resumable = (
            resume_organizer_failure
            and point_records[0]["event"] == "point-start"
            and point_records[-1]["event"] == "observation-paused"
            and not any(record["event"] == "point-terminal" for record in point_records)
        )
        if not resumable:
            raise ValueError("a historical point can never be retried")
        append_record(
            journal_path,
            "point-resume",
            {"team_id": team_id, "point_id": point_id, "reason": "organizer-recovery"},
        )
    else:
        if resume_organizer_failure:
            raise ValueError("cannot resume a point that never started")
        append_record(
            journal_path,
            "point-start",
            {
                "team_id": team_id,
                "point_id": point_id,
                "nomination_sha256": nomination_sha256,
            },
        )
    try:
        evidence = dict(evaluator())
    except CandidateFailureError as error:
        terminal = {
            "team_id": team_id,
            "point_id": point_id,
            "status": "dnf",
            "score": 0.0,
            "reason": str(error) or "candidate-failure",
        }
        append_record(journal_path, "point-terminal", terminal)
        return terminal
    except Exception as error:
        append_record(
            journal_path,
            "observation-paused",
            {"point_id": point_id, "reason": type(error).__name__},
        )
        raise OrganizerFailureError(
            "organizer data/evaluator failure; tournament paused"
        ) from error

    evidence_bytes = _canonical(evidence)
    stage = Path(private_stage)
    stage.mkdir(parents=True, exist_ok=True)
    evidence_path = stage / f"{point_id}.json"
    if evidence_path.exists():
        raise ValueError("private point evidence already exists")
    with evidence_path.open("xb") as handle:
        handle.write(evidence_bytes)
        handle.flush()
        os.fsync(handle.fileno())
    terminal = {
        "team_id": team_id,
        "point_id": point_id,
        "status": "succeeded",
        "evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
    }
    append_record(journal_path, "point-terminal", terminal)
    return terminal


def private_bundle_digest(root: str | Path) -> str:
    base = Path(root)
    entries: list[dict[str, str]] = []
    for path in sorted(candidate for candidate in base.rglob("*") if candidate.is_file()):
        entries.append(
            {
                "path": path.relative_to(base).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return _digest(entries)


def integrity_review(
    *,
    field: Mapping[str, object],
    journal_path: str | Path,
    private_stage: str | Path,
) -> Mapping[str, object]:
    records = read_records(journal_path)
    if not records or records[0]["event"] != "observation-batch-start":
        raise ValueError("observation batch lacks a durable start marker")
    for index, record in enumerate(records):
        if record["event"] != "observation-paused":
            continue
        point_id = record["payload"]["point_id"]
        resolved = any(
            later["event"] == "point-terminal" and later["payload"].get("point_id") == point_id
            for later in records[index + 1 :]
        )
        if not resolved:
            raise ValueError("integrity review cannot pass an unresolved organizer pause")
    recover_interrupted_points(journal_path)
    records = read_records(journal_path)
    starts = [record for record in records if record["event"] == "point-start"]
    terminals = [record for record in records if record["event"] == "point-terminal"]
    if len(starts) != len(terminals):
        raise ValueError("every observed point must have exactly one terminal record")
    expected_points = {
        str(point_id)
        for disposition in field["dispositions"].values()
        if disposition["state"] == "nominated"
        for point_id in disposition["point_ids"]
    }
    terminal_points = {str(record["payload"]["point_id"]) for record in terminals}
    if terminal_points != expected_points:
        raise ValueError("observation terminals do not cover the exact frozen point field")
    for start, terminal in zip(starts, terminals, strict=True):
        if start["payload"]["point_id"] != terminal["payload"]["point_id"]:
            raise ValueError("point terminal ordering differs from durable start ordering")
    review = {
        "status": "passed",
        "field_sha256": field["field_sha256"],
        "points_started": len(starts),
        "points_terminal": len(terminals),
        "private_bundle_sha256": private_bundle_digest(private_stage),
        "journal_tail_sha256": records[-1]["record_sha256"],
    }
    return {**review, "review_sha256": _digest(review)}


def compile_leaderboard(
    *,
    field: Mapping[str, object],
    journal_path: str | Path,
    private_stage: str | Path,
) -> Mapping[str, object]:
    """Verify private point evidence and apply the frozen neighbourhood/tie ordering."""
    records = read_records(journal_path)
    terminals = {
        str(record["payload"]["point_id"]): record["payload"]
        for record in records
        if record["event"] == "point-terminal"
    }
    stage = Path(private_stage)
    entries: list[RankedEntry] = []
    for team_id in TEAM_IDS:
        disposition = field["dispositions"][team_id]
        candidate_id = str(disposition.get("candidate_id", "dnf"))
        bundle_sha256 = str(disposition.get("source_bundle_sha256", "f" * 64))
        if disposition["state"] == "dnf":
            entries.append(
                RankedEntry(
                    team_id,
                    candidate_id,
                    False,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    bundle_sha256,
                    str(disposition["reason"]),
                )
            )
            continue

        point_ids = [str(value) for value in disposition["point_ids"]]
        point_scores: list[float] = []
        evidence_by_point: dict[str, Mapping[str, object]] = {}
        failed_reason = ""
        for point_id in point_ids:
            terminal = terminals.get(point_id)
            if terminal is None:
                raise ValueError(f"leaderboard lacks terminal evidence for {point_id}")
            if terminal.get("status") != "succeeded":
                failed_reason = str(terminal.get("reason", "candidate-point-failure"))
                break
            evidence_path = stage / f"{point_id}.json"
            payload = evidence_path.read_bytes()
            if hashlib.sha256(payload).hexdigest() != terminal.get("evidence_sha256"):
                raise ValueError(f"private point evidence drifted: {point_id}")
            evidence = json.loads(payload)
            if evidence.get("team_id") != team_id or evidence.get("point_id") != point_id:
                raise ValueError(f"private point identity differs from field: {point_id}")
            if evidence.get("source_bundle_sha256") != bundle_sha256:
                raise ValueError(f"private point source differs from field: {point_id}")
            score = float(evidence["score"]["score"])
            point_scores.append(score)
            evidence_by_point[point_id] = evidence
        if failed_reason:
            entries.append(
                RankedEntry(
                    team_id,
                    candidate_id,
                    False,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    bundle_sha256,
                    failed_reason,
                )
            )
            continue

        centre_index = int(disposition.get("centre_index", 0))
        neighbourhood = rounded_neighbourhood(
            score_neighbourhood(point_scores, centre_index=centre_index)
        )
        centre = evidence_by_point[point_ids[centre_index]]
        centre_score = centre["score"]
        fold_3x = min(
            float(cells["3"]["q"])
            for cells in centre_score["fold_cost_cells"].values()
        )
        drawdown_3x = float(centre_score["all_cost_cells"]["3"]["drawdown"])
        turnover = float(centre["centre_turnover"])
        entries.append(
            RankedEntry(
                team_id=team_id,
                candidate_id=candidate_id,
                valid=True,
                official_score=neighbourhood.official_score,
                lower_quartile_score=neighbourhood.lower_quartile_score,
                minimum_point_score=neighbourhood.minimum_score,
                centre_score=neighbourhood.centre_score,
                centre_worst_fold_3x_score=round_half_even(fold_3x),
                centre_3x_drawdown=round_half_even(drawdown_3x),
                centre_turnover=round_half_even(turnover),
                bundle_sha256=bundle_sha256,
            )
        )
    ordered = rank_entries(entries)
    winner = next((entry.team_id for entry in ordered if entry.valid), None)
    return {
        "entries": [dataclasses.asdict(entry) for entry in ordered],
        "winner_team_id": winner,
    }


def atomic_release(
    destination: str | Path,
    *,
    leaderboard: Mapping[str, object],
    integrity: Mapping[str, object],
) -> Mapping[str, object]:
    """Publish the complete leaderboard in one rename; no partial team result is visible."""
    path = Path(destination)
    if path.exists():
        raise FileExistsError("CUP-50 leaderboard is already released")
    if integrity.get("status") != "passed" or not integrity.get("review_sha256"):
        raise ValueError("atomic release requires a passed, hash-bound integrity review")
    entries = leaderboard.get("entries")
    if not isinstance(entries, list) or len(entries) != len(TEAM_IDS):
        raise ValueError("leaderboard must publish all twelve lane dispositions at once")
    published_teams = [str(entry.get("team_id")) for entry in entries if isinstance(entry, Mapping)]
    if sorted(published_teams) != sorted(TEAM_IDS):
        raise ValueError("leaderboard does not contain each CUP-50 team exactly once")
    body = {
        "schema_version": 1,
        "namespace": "cup50",
        "integrity_review_sha256": integrity["review_sha256"],
        "leaderboard": dict(leaderboard),
    }
    record = {**body, "release_sha256": _digest(body)}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_dir = Path(tempfile.mkdtemp(prefix=".cup50-release.", dir=path.parent))
    try:
        staged = temporary_dir / path.name
        with staged.open("xb") as handle:
            handle.write(_canonical(record))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staged, path)
    finally:
        shutil.rmtree(temporary_dir, ignore_errors=True)
    return record
