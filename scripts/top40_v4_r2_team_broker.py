#!/usr/bin/env python3
"""Offline sequential research broker for the 15-team Top-40 V4 edition 2 field."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from crypto_trade.tournament.layout_v4 import select_v4_layout

select_v4_layout("r2")

from crypto_trade.tournament import (  # noqa: E402
    activation_v4,
    journal_v4,
    orchestrator_v4,
    research_runtime_v4,
    top40_v4,
)
from crypto_trade.tournament.layout_v4 import TOP40_V4_LAYOUT  # noqa: E402

_SAFE_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


class BrokerError(RuntimeError):
    """A team-to-organizer message or sequential broker transition is invalid."""


def _pretty(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    ).encode("ascii") + b"\n"


def _write_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
            0o600,
        )
    except FileExistsError:
        if research_runtime_v4._stable_bytes(path) != payload:  # noqa: SLF001
            raise BrokerError("immutable broker output already differs")
        return
    with os.fdopen(descriptor, "wb") as handle:
        if handle.write(payload) != len(payload):
            raise BrokerError("short broker write")
        handle.flush()
        os.fsync(handle.fileno())
    directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _read_request(root: Path, team_id: str, phase: str) -> tuple[Mapping[str, Any], Path, bytes]:
    name = {"discovery": "batch-1.json", "refinement": "batch-2.json", "decision": "decision.json"}[
        phase
    ]
    path = root / TOP40_V4_LAYOUT.team_root(team_id) / "outbox" / name
    payload = research_runtime_v4._stable_bytes(path)  # noqa: SLF001 - same frozen broker.
    try:
        request = json.loads(payload)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise BrokerError("team outbox is invalid JSON") from exc
    if not isinstance(request, Mapping):
        raise BrokerError("team outbox must be an object")
    return request, path, payload


def _archive_outbox(root: Path, team_id: str, phase: str, path: Path, payload: bytes) -> str:
    digest = hashlib.sha256(payload).hexdigest()
    relative = (
        f"tournament/top40-v4-r2/research-sessions/outboxes/{team_id}/"
        f"{phase}-{digest}.json"
    )
    research_runtime_v4._write_immutable(root / relative, payload)  # noqa: SLF001
    archive = _phase_archive(root, team_id, phase)
    if archive is None or archive.relative_to(root).as_posix() != relative:
        raise BrokerError("immutable outbox archive authority differs")
    path.unlink()
    return relative


def _normalize_batch_request(
    root: Path,
    team_id: str,
    phase: str,
    request: Mapping[str, Any],
) -> list[Mapping[str, str]]:
    expected_count = 8 if phase == "discovery" else 4
    rows = request.get("requests")
    if (
        set(request) != {"schema_version", "operation", "requests"}
        or request.get("schema_version") != 1
        or request.get("operation") != "is-batch"
        or not isinstance(rows, list)
        or len(rows) != expected_count
    ):
        raise BrokerError(f"{phase} must contain exactly {expected_count} IS requests")
    normalized: list[Mapping[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {"candidate_id", "entrypoint", "purpose"}:
            raise BrokerError("IS request schema differs")
        candidate_id = row.get("candidate_id")
        purpose = row.get("purpose")
        entrypoint = row.get("entrypoint")
        if (
            not isinstance(candidate_id, str)
            or _SAFE_ID.fullmatch(candidate_id) is None
            or candidate_id in seen
            or not research_runtime_v4._is_bounded_single_line(purpose)  # noqa: SLF001
        ):
            raise BrokerError("IS request identity or purpose is invalid")
        expected = f"candidates/{candidate_id}/strategy.py"
        if entrypoint != expected:
            raise BrokerError("IS entrypoint differs from its candidate identity")
        absolute = root / TOP40_V4_LAYOUT.team_root(team_id) / expected
        if PurePosixPath(expected).parts[:1] != ("candidates",) or not absolute.is_file():
            raise BrokerError("IS entrypoint is missing")
        seen.add(candidate_id)
        normalized.append(
            {"candidate_id": candidate_id, "entrypoint": str(entrypoint), "purpose": purpose}
        )
    return normalized


def _validate_batch(
    root: Path, team_id: str, phase: str
) -> tuple[list[Mapping[str, str]], Path, bytes]:
    request, path, payload = _read_request(root, team_id, phase)
    return _normalize_batch_request(root, team_id, phase, request), path, payload


def _reject_failed_preflight(
    root: Path,
    team_id: str,
    phase: str,
    error: orchestrator_v4.CandidateBatchRejectedError,
) -> Mapping[str, Any]:
    name = "batch-1.json" if phase == "discovery" else "batch-2.json"
    path = root / TOP40_V4_LAYOUT.team_root(team_id) / "outbox" / name
    payload = research_runtime_v4._stable_bytes(path)  # noqa: SLF001
    rejected = orchestrator_v4.reject_batch_before_evaluation(root, error)
    archive = _archive_outbox(root, team_id, phase, path, payload)
    result: Mapping[str, Any] = {
        **rejected,
        "outbox_sha256": hashlib.sha256(payload).hexdigest(),
        "outbox_archive_path": archive,
    }
    if phase == "refinement" and _team_has_success(root, team_id):
        representative = _finalize_team_representative(root, team_id)
        result = {
            **result,
            "retired": False,
            "research_truncated": True,
            "representative": representative,
        }
    return result


def _accepted_record(
    root: Path, team_id: str, candidate_id: str
) -> tuple[str, Mapping[str, Any], Mapping[str, Any] | None]:
    state = journal_v4.read(root / TOP40_V4_LAYOUT.journal_path)
    matches = [
        (digest, record)
        for digest, record in state.is_requests.items()
        if record["payload"]["team_id"] == team_id
        and record["payload"]["candidate_id"] == candidate_id
    ]
    if len(matches) != 1:
        raise BrokerError("candidate has no unique accepted trial record")
    digest, request = matches[0]
    return digest, request, state.is_terminals.get(digest)


def _maybe_accepted_record(
    root: Path, team_id: str, candidate_id: str
) -> tuple[str, Mapping[str, Any], Mapping[str, Any] | None] | None:
    try:
        return _accepted_record(root, team_id, candidate_id)
    except BrokerError:
        return None


def _feedback_row(root: Path, team_id: str, candidate_id: str) -> Mapping[str, Any]:
    request_hash, request, terminal = _accepted_record(root, team_id, candidate_id)
    if terminal is None:
        raise BrokerError("accepted trial has no terminal record")
    base: dict[str, Any] = {
        "candidate_id": candidate_id,
        "request_record_sha256": request_hash,
        "terminal_status": terminal["event_type"],
        "trial_number": request["payload"]["trial_number"],
    }
    if terminal["event_type"] == "is_failed":
        base["failure"] = str(terminal["payload"]["failure"])
        return base
    summary = orchestrator_v4._verified_summary(root, terminal)  # noqa: SLF001
    base["summary"] = {
        "bootstrap_probability_positive_mean": summary["bootstrap_probability_positive_mean"],
        "diagnostics": summary["diagnostics"],
        "folds": summary["folds"],
        "regime_sharpe": summary["regime_sharpe"],
        "scored_window": summary["scored_window"],
        "selection": summary["selection"],
    }
    return base


def _phase_archive(root: Path, team_id: str, phase: str) -> Path | None:
    directory = root / "tournament/top40-v4-r2/research-sessions/outboxes" / team_id
    if not directory.exists():
        return None
    directory_stat = directory.lstat()
    if (
        not stat.S_ISDIR(directory_stat.st_mode)
        or directory_stat.st_uid != os.geteuid()
        or directory_stat.st_mode & 0o077
    ):
        raise BrokerError("broker outbox archive directory is unsafe")
    matches = []
    for path in directory.iterdir():
        prefix = f"{phase}-"
        if not path.name.startswith(prefix) or not path.name.endswith(".json"):
            continue
        digest = path.name[len(prefix) : -len(".json")]
        if _SHA256.fullmatch(digest) is None:
            raise BrokerError("broker outbox archive name is invalid")
        matches.append(path)
    if len(matches) > 1:
        raise BrokerError("broker phase has multiple archived outboxes")
    if not matches:
        return None
    path = matches[0]
    try:
        before = path.lstat()
        payload = research_runtime_v4._stable_bytes(path)  # noqa: SLF001
        after = path.lstat()
    except (OSError, research_runtime_v4.ResearchRuntimeError) as exc:
        raise BrokerError("broker outbox archive file is unsafe") from exc
    if (
        not stat.S_ISREG(before.st_mode)
        or not stat.S_ISREG(after.st_mode)
        or before.st_uid != os.geteuid()
        or after.st_uid != os.geteuid()
        or before.st_nlink != 1
        or after.st_nlink != 1
        or before.st_mode & 0o077
        or after.st_mode & 0o077
        or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    ):
        raise BrokerError("broker outbox archive file is unsafe")
    digest = hashlib.sha256(payload).hexdigest()
    if path.name != f"{phase}-{digest}.json":
        raise BrokerError("broker outbox archive digest differs")
    return path


def _validate_completed_phase(root: Path, team_id: str, phase: str) -> Mapping[str, Any]:
    team = root / TOP40_V4_LAYOUT.team_root(team_id)
    feedback_path = team / "feedback" / f"{phase}.json"
    try:
        feedback_payload = research_runtime_v4._stable_bytes(feedback_path)  # noqa: SLF001
        feedback = json.loads(feedback_payload)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise BrokerError("completed phase feedback is invalid JSON") from exc
    archive = _phase_archive(root, team_id, phase)
    if archive is None:
        raise BrokerError("completed phase lacks its immutable outbox archive")
    archive_payload = research_runtime_v4._stable_bytes(archive)  # noqa: SLF001
    digest = hashlib.sha256(archive_payload).hexdigest()
    if archive.name != f"{phase}-{digest}.json":
        raise BrokerError("completed phase outbox archive digest differs")
    try:
        request = json.loads(archive_payload)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise BrokerError("completed phase outbox archive is invalid JSON") from exc
    if not isinstance(request, Mapping):
        raise BrokerError("completed phase outbox archive must be an object")
    rows = _normalize_batch_request(root, team_id, phase, request)
    expected_results = [
        _feedback_row(root, team_id, row["candidate_id"])
        for row in rows
    ]
    first_trial = 1 if phase == "discovery" else 9
    expected_trials = list(range(first_trial, first_trial + len(rows)))
    if [row["trial_number"] for row in expected_results] != expected_trials:
        raise BrokerError("completed phase journal trial sequence differs")
    expected_feedback = {
        "schema_version": 1,
        "tournament": TOP40_V4_LAYOUT.name,
        "team_id": team_id,
        "phase": phase,
        "interim_field_disclosure": False,
        "results": expected_results,
    }
    if feedback != expected_feedback:
        raise BrokerError("completed phase feedback differs from journal and outbox authority")
    return {
        "feedback_sha256": hashlib.sha256(feedback_payload).hexdigest(),
        "outbox_archive_path": archive.relative_to(root).as_posix(),
        "outbox_sha256": digest,
        "trials": len(rows),
    }


def _validate_launch_transition(root: Path, team_id: str, phase: str) -> None:
    state = journal_v4.read(root / TOP40_V4_LAYOUT.journal_path)
    if state.selection is not None:
        raise BrokerError("research launch is forbidden after IS selection is sealed")
    if team_id in state.nominations or team_id in state.retired:
        raise BrokerError("research launch is forbidden after the lane is terminal")
    trial_count = state.trials_by_team.get(team_id, 0)
    if _phase_archive(root, team_id, phase) is not None:
        raise BrokerError("research phase already has an archived outbox")
    if phase == "discovery":
        if trial_count != 0:
            raise BrokerError("discovery launch requires an untouched lane")
        return
    _validate_completed_phase(root, team_id, "discovery")
    if phase == "refinement":
        if trial_count != 8:
            raise BrokerError("refinement launch requires exactly eight discovery trials")
        return
    _validate_completed_phase(root, team_id, "refinement")
    if trial_count != 12:
        raise BrokerError("decision launch requires exactly twelve completed trials")


def _validate_consume_transition(
    root: Path,
    team_id: str,
    phase: str,
    requests: list[Mapping[str, str]],
) -> None:
    state = journal_v4.read(root / TOP40_V4_LAYOUT.journal_path)
    if state.selection is not None:
        raise BrokerError("research batch consume is forbidden after IS selection is sealed")
    if team_id in state.nominations or team_id in state.retired:
        raise BrokerError("research batch consume is forbidden after the lane is terminal")
    research_runtime_v4.validate_launch_authority(root, team_id, phase)
    if phase == "refinement":
        _validate_completed_phase(root, team_id, "discovery")
    start = 1 if phase == "discovery" else 9
    end = start + len(requests) - 1
    accepted = sorted(
        (
            record["payload"]
            for record in state.is_requests.values()
            if record["payload"]["team_id"] == team_id
        ),
        key=lambda payload: payload["trial_number"],
    )
    trial_numbers = [payload["trial_number"] for payload in accepted]
    if trial_numbers != list(range(1, len(accepted) + 1)) or not start - 1 <= len(
        accepted
    ) <= end:
        raise BrokerError("research batch journal trial range is out of phase")
    current = accepted[start - 1 :]
    expected_prefix = [request["candidate_id"] for request in requests[: len(current)]]
    if [payload["candidate_id"] for payload in current] != expected_prefix:
        raise BrokerError("research batch differs from its accepted journal prefix")
    archive = _phase_archive(root, team_id, phase)
    feedback = root / TOP40_V4_LAYOUT.team_root(team_id) / "feedback" / f"{phase}.json"
    if archive is not None and not feedback.exists():
        raise BrokerError("archived research batch lacks completed feedback authority")


def _restore_lane_markers_before_authority(root: Path, team_id: str) -> tuple[str, ...]:
    """Normalize only crash-missing writable markers while the broker lease is held."""

    TOP40_V4_LAYOUT.require_team(team_id)
    return research_runtime_v4._restore_writable_lane_markers_before_activation(  # noqa: SLF001
        root, team_id
    )


@research_runtime_v4.serialized_r2_command
def consume_batch(root: Path, team_id: str, phase: str) -> Mapping[str, Any]:
    _restore_lane_markers_before_authority(root, team_id)
    activation_v4.validate(root)
    TOP40_V4_LAYOUT.require_team(team_id)
    outbox_name = "batch-1.json" if phase == "discovery" else "batch-2.json"
    outbox = root / TOP40_V4_LAYOUT.team_root(team_id) / "outbox" / outbox_name
    if (
        not os.path.lexists(outbox)
        and research_runtime_v4.missing_batch_exhaustion_may_exist(
            root, team_id, phase
        )
    ):
        result = orchestrator_v4.abandon_missing_batch_before_evaluation(
            root, team_id, phase
        )
        if phase == "refinement" and _team_has_success(root, team_id):
            representative = _finalize_team_representative(root, team_id)
            return {
                **dict(result),
                "retired": False,
                "research_truncated": True,
                "representative": representative,
            }
        return result
    try:
        orchestrator_v4.preflight_is_batch(
            root, team_id, phase, require_receipts=False
        )
    except orchestrator_v4.CandidateBatchRejectedError as exc:
        return _reject_failed_preflight(root, team_id, phase, exc)
    requests, path, payload = _validate_batch(root, team_id, phase)
    _validate_consume_transition(root, team_id, phase, requests)
    try:
        capability = orchestrator_v4.preflight_is_batch(root, team_id, phase)
    except orchestrator_v4.CandidateBatchRejectedError as exc:
        return _reject_failed_preflight(root, team_id, phase, exc)
    if capability is None:
        raise BrokerError("batch preflight did not issue an evaluation capability")
    rows: list[Mapping[str, Any]] = []
    for request in requests:
        entrypoint = f"{TOP40_V4_LAYOUT.team_root(team_id)}/{request['entrypoint']}"
        accepted = _maybe_accepted_record(root, team_id, request["candidate_id"])
        if accepted is not None and accepted[2] is None:
            orchestrator_v4._close_interrupted_is_requests(root)  # noqa: SLF001
            accepted = _accepted_record(root, team_id, request["candidate_id"])
        if accepted is None:
            try:
                orchestrator_v4.run_is(
                    root,
                    team_id,
                    entrypoint,
                    purpose=request["purpose"],
                    _batch_capability=capability,
                )
            except Exception:
                # Runtime failures are already terminal and consume a trial. Admission failures
                # have no accepted authority and must preserve the original actionable error.
                # Never fabricate trial evidence, and never mask an interrupted infrastructure
                # failure whose accepted request still lacks a durable terminal record.
                admitted = _maybe_accepted_record(root, team_id, request["candidate_id"])
                if admitted is None or admitted[2] is None:
                    raise
        rows.append(_feedback_row(root, team_id, request["candidate_id"]))
    feedback = {
        "schema_version": 1,
        "tournament": TOP40_V4_LAYOUT.name,
        "team_id": team_id,
        "phase": phase,
        "interim_field_disclosure": False,
        "results": rows,
    }
    feedback_path = root / TOP40_V4_LAYOUT.team_root(team_id) / "feedback" / f"{phase}.json"
    _write_exclusive(feedback_path, _pretty(feedback))
    archive = _archive_outbox(root, team_id, phase, path, payload)
    return {
        "ok": True,
        "team_id": team_id,
        "phase": phase,
        "trials": len(rows),
        "feedback_path": feedback_path.relative_to(root).as_posix(),
        "outbox_archive_path": archive,
    }


def _team_has_success(root: Path, team_id: str) -> bool:
    state = journal_v4.read(root / TOP40_V4_LAYOUT.journal_path)
    return any(
        terminal["payload"]["team_id"] == team_id
        for terminal in state.is_successes.values()
    )


def _finalize_team_representative(root: Path, team_id: str) -> Mapping[str, Any]:
    """Compile the frozen certificate and disposition without a fallible decision session."""

    unexpected_outbox = research_runtime_v4._unexpected_outbox_entries(  # noqa: SLF001
        root, team_id, allowed=set()
    )
    if unexpected_outbox:
        raise BrokerError("automatic finalization found unexpected team outbox residue")
    state = journal_v4.read(root / TOP40_V4_LAYOUT.journal_path)
    trial_count = state.trials_by_team.get(team_id, 0)
    truncated_refinement = orchestrator_v4._successful_truncated_refinement(  # noqa: SLF001
        state, team_id
    )
    if trial_count != TOP40_V4_LAYOUT.maximum_trials and not truncated_refinement:
        raise BrokerError(
            "automatic representative selection requires twelve trials or a bound "
            "score-blind refinement truncation"
        )
    _validate_completed_phase(root, team_id, "discovery")
    if truncated_refinement:
        orchestrator_v4._validate_retired_research_authorities(  # noqa: SLF001
            root, state
        )
    else:
        _validate_completed_phase(root, team_id, "refinement")
    if not _team_has_success(root, team_id):
        result = orchestrator_v4.retire(
            root,
            team_id,
            reason="all twelve accepted candidates failed before representative selection",
        )
        return {**dict(result), "automatic_disposition": True}

    loaded = top40_v4.load_config(root=root)
    candidate_id = orchestrator_v4._strongest_successful_candidate(  # noqa: SLF001
        root, state, loaded.raw, team_id
    )
    _request_hash, accepted, terminal = _accepted_record(root, team_id, candidate_id)
    if terminal is None or terminal["event_type"] != "is_succeeded":
        raise BrokerError("automatic representative lacks a successful terminal authority")
    source_sha256 = str(accepted["payload"]["authority"]["source_bundle_sha256"])
    orchestrator_v4._validated_preflight_source_review(  # noqa: SLF001
        root,
        state,
        team_id=team_id,
        candidate_id=candidate_id,
        source_bundle_sha256=source_sha256,
        trial_number=int(accepted["payload"]["trial_number"]),
    )
    required_tags = tuple(loaded.raw["research"]["required_certificate_tags"])
    evidence: dict[str, list[str]] = {tag: [] for tag in required_tags}
    requests = sorted(
        (
            (digest, record["payload"])
            for digest, record in state.is_requests.items()
            if record["payload"]["team_id"] == team_id
        ),
        key=lambda row: int(row[1]["trial_number"]),
    )
    for digest, request in requests:
        for tag in required_tags:
            if tag in request["metadata"]["tags"]:
                evidence[tag].append(digest)
    certificate = {
        "schema_version": 1,
        "team_id": team_id,
        "candidate_id": candidate_id,
        "evidence": evidence,
    }
    certificate_relative = (
        f"{TOP40_V4_LAYOUT.tournament_root}/certificates/{team_id}/{candidate_id}.json"
    )
    orchestrator_v4._write_atomic(  # noqa: SLF001
        root, certificate_relative, _pretty(certificate), replace=False
    )
    result = orchestrator_v4.nominate(
        root, team_id, candidate_id, certificate_relative
    )
    return {
        **dict(result),
        "automatic_disposition": True,
        "selection_basis": "frozen-robust-is-ranking",
    }


@research_runtime_v4.serialized_r2_command
def consume_decision(root: Path, team_id: str) -> Mapping[str, Any]:
    _restore_lane_markers_before_authority(root, team_id)
    activation_v4.validate(root)
    TOP40_V4_LAYOUT.require_team(team_id)
    raise BrokerError("R2 decision consumption is disabled; selection is automatic")


def _prompt(team_id: str, phase: str) -> str:
    return research_runtime_v4.team_phase_prompt(team_id, phase)


@research_runtime_v4.serialized_r2_command
def launch_phase(root: Path, team_id: str, phase: str) -> Mapping[str, Any]:
    _restore_lane_markers_before_authority(root, team_id)
    activation_v4.validate(root)
    TOP40_V4_LAYOUT.require_team(team_id)
    if phase == "decision":
        raise BrokerError("R2 representative selection is automatic after refinement")
    _validate_launch_transition(root, team_id, phase)
    return research_runtime_v4.launch_team_phase(root, team_id, phase)


@research_runtime_v4.serialized_r2_command
def run_team(root: Path, team_id: str) -> Mapping[str, Any]:
    _restore_lane_markers_before_authority(root, team_id)
    activation_v4.validate(root)
    results: list[Mapping[str, Any]] = []
    state = journal_v4.read(root / TOP40_V4_LAYOUT.journal_path)
    if team_id in state.nominations or team_id in state.retired:
        retired = state.retired.get(team_id)
        if retired is not None and retired["event_type"] == "batch_rejected":
            event = retired["payload"]
            phase = str(event["phase"])
            name = "batch-1.json" if phase == "discovery" else "batch-2.json"
            outbox = root / TOP40_V4_LAYOUT.team_root(team_id) / "outbox" / name
            if outbox.exists():
                payload = research_runtime_v4._stable_bytes(outbox)  # noqa: SLF001
                if hashlib.sha256(payload).hexdigest() != event["outbox_sha256"]:
                    raise BrokerError("rejected batch outbox differs from journal authority")
                _archive_outbox(root, team_id, phase, outbox, payload)
            archive = _phase_archive(root, team_id, phase)
            if archive is None or archive.name != (
                f"{phase}-{event['outbox_sha256']}.json"
            ):
                raise BrokerError("rejected batch lacks its immutable outbox archive")
        elif retired is not None and retired["event_type"] == "batch_abandoned":
            event = retired["payload"]
            phase = str(event["phase"])
            name = "batch-1.json" if phase == "discovery" else "batch-2.json"
            outbox = root / TOP40_V4_LAYOUT.team_root(team_id) / "outbox" / name
            if os.path.lexists(outbox) or _phase_archive(root, team_id, phase) is not None:
                raise BrokerError("abandoned missing batch gained an outbox authority")
            evidence = research_runtime_v4.validate_missing_batch_exhaustion(
                root, team_id, phase
            )
            if (
                evidence["path"] != event["admission_attempt_path"]
                or evidence["sha256"] != event["admission_attempt_sha256"]
            ):
                raise BrokerError("abandoned batch evidence differs from journal authority")
        if (
            retired is not None
            and retired["event_type"] in {"batch_rejected", "batch_abandoned"}
            and retired["payload"]["phase"] == "refinement"
            and _team_has_success(root, team_id)
        ):
            representative = _finalize_team_representative(root, team_id)
            return {
                "ok": True,
                "team_id": team_id,
                "research_truncated": True,
                "steps": [representative],
            }
        unexpected_outbox = research_runtime_v4._unexpected_outbox_entries(  # noqa: SLF001
            root, team_id, allowed=set()
        )
        if unexpected_outbox:
            raise BrokerError("terminal lane contains unexpected team outbox residue")
        return {"ok": True, "team_id": team_id, "already_terminal": True, "steps": []}
    for phase in ("discovery", "refinement"):
        team = root / TOP40_V4_LAYOUT.team_root(team_id)
        outbox_name = "batch-1.json" if phase == "discovery" else "batch-2.json"
        outbox = team / "outbox" / outbox_name
        feedback = team / "feedback" / f"{phase}.json"
        if not feedback.exists():
            state = journal_v4.read(root / TOP40_V4_LAYOUT.journal_path)
            phase_start = 0 if phase == "discovery" else 8
            trial_count = state.trials_by_team.get(team_id, 0)
            if trial_count == phase_start:
                try:
                    results.append(launch_phase(root, team_id, phase))
                except research_runtime_v4.CandidateRepairExhaustedError as exc:
                    # The exact invalid batch remains live so the broker-held preflight can
                    # durably retire it without opening scores. Infrastructure failures are not
                    # caught here and remain restart-resumable.
                    results.append(
                        {
                            "ok": False,
                            "team_id": team_id,
                            "phase": phase,
                            "repair_exhausted": True,
                            "reason": str(exc),
                        }
                    )
            elif not outbox.exists():
                raise BrokerError("accepted batch prefix has no live outbox authority")
            results.append(consume_batch(root, team_id, phase))
        elif outbox.exists():
            results.append(consume_batch(root, team_id, phase))
        else:
            authority = _validate_completed_phase(root, team_id, phase)
            results.append(
                {
                    "ok": True,
                    "team_id": team_id,
                    "phase": phase,
                    "resumed": True,
                    "authority": authority,
                }
            )
        state = journal_v4.read(root / TOP40_V4_LAYOUT.journal_path)
        if team_id in state.retired:
            return {
                "ok": True,
                "team_id": team_id,
                "terminal": "retired",
                "steps": results,
            }
    state = journal_v4.read(root / TOP40_V4_LAYOUT.journal_path)
    if team_id not in state.nominations and team_id not in state.retired:
        results.append(_finalize_team_representative(root, team_id))
    return {"ok": True, "team_id": team_id, "steps": results}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    commands = parser.add_subparsers(dest="command", required=True)
    probe = commands.add_parser("probe")
    probe.add_argument("team_id")
    launch = commands.add_parser("launch")
    launch.add_argument("team_id")
    launch.add_argument("phase", choices=("discovery", "refinement"))
    consume = commands.add_parser("consume")
    consume.add_argument("team_id")
    consume.add_argument("phase", choices=("discovery", "refinement"))
    run = commands.add_parser("run-team")
    run.add_argument("team_id")
    commands.add_parser("run-all")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    root = Path(arguments.root).resolve()
    try:
        with research_runtime_v4.broker_lease(root):
            if arguments.command == "probe":
                result = research_runtime_v4.run_profile_probes(root, arguments.team_id)
            elif arguments.command == "launch":
                result = launch_phase(root, arguments.team_id, arguments.phase)
            elif arguments.command == "consume":
                result = consume_batch(root, arguments.team_id, arguments.phase)
            elif arguments.command == "run-team":
                result = run_team(root, arguments.team_id)
            elif arguments.command == "run-all":
                rows = []
                for team_id in TOP40_V4_LAYOUT.team_ids:
                    rows.append(run_team(root, team_id))
                result = {"ok": True, "teams": rows, "execution": "strictly-serial"}
            else:  # pragma: no cover
                raise AssertionError(arguments.command)
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        sys.stderr.write(f"top40-v4-r2-broker: {exc}\n")
        return 2
    sys.stdout.write(json.dumps(result, allow_nan=False, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
