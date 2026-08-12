"""Fail-closed append-only journal primitives for Top40 V3 train laboratories.

The public append functions lock, replay, validate, append one canonical JSONL
record, flush, and fsync before returning.  In particular,
``append_request_accepted`` must return successfully before a caller launches a
train process.  This module deliberately has no runner or V2 dependency.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import math
import os
import re
import stat
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, BinaryIO

SCHEMA_VERSION = "top40-v3-train-journal-v1"
GENESIS_SHA256 = "0" * 64
MAX_RECORD_BYTES = 1_048_576
FROZEN_TRAIN_WINDOW = MappingProxyType(
    {
        "start_utc": "2020-02-03T00:00:00Z",
        "end_exclusive_utc": "2022-07-01T00:00:00Z",
    }
)
FROZEN_COST_MODEL = MappingProxyType(
    {
        "taker_fee_bps_per_side": 5.0,
        "slippage_bps_per_side": 2.5,
        "funding_included": True,
        "funding_timing": "true_timestamps",
        "doubled_cost_multiplier": 2.0,
    }
)

_SHA256 = re.compile(r"[0-9a-f]{64}")
_TEAM_ID = re.compile(r"team-(?:0[1-9]|10)")
_SAFE_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_GATE_NAME = re.compile(r"[a-z][a-z0-9_]{0,63}")
_UTC_TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
_TERMINAL_TYPES = frozenset({"succeeded", "failed", "aborted"})

_CHAIN_KEYS = frozenset(
    {
        "schema_version",
        "event_sequence",
        "previous_sha256",
        "record_sha256",
        "event_type",
    }
)
_REQUEST_KEYS = _CHAIN_KEYS | frozenset(
    {
        "team_id",
        "run_sequence",
        "run_id",
        "candidate_id",
        "parent_candidate_id",
        "purpose",
        "accepted_at_utc",
        "source_bundle_sha256",
        "source_archive_path",
        "source_archive_sha256",
        "strategy_sha256",
        "dependency_lock_sha256",
        "config_sha256",
        "risk_policy_sha256",
        "data_authority_sha256",
        "evaluator_sha256",
        "seed",
        "material_parameters",
        "train_window",
        "cost_model",
        "output_path",
        "cumulative_material_trial_count",
    }
)
_TERMINAL_KEYS = _CHAIN_KEYS | frozenset(
    {
        "team_id",
        "run_sequence",
        "run_id",
        "candidate_id",
        "request_sha256",
        "completed_at_utc",
        "cpu_seconds",
        "wall_seconds",
        "gate_vector",
        "metric_packet_sha256",
        "artifact_hashes",
        "cumulative_material_trial_count",
        "failure_reason",
    }
)
_REQUEST_HASH_FIELDS = (
    "source_bundle_sha256",
    "source_archive_sha256",
    "strategy_sha256",
    "dependency_lock_sha256",
    "config_sha256",
    "risk_policy_sha256",
    "data_authority_sha256",
    "evaluator_sha256",
)


class JournalValidationError(ValueError):
    """Raised when a journal or proposed transition is not exactly valid."""


@dataclass(frozen=True, slots=True)
class JournalState:
    """Validated replay result.

    Mapping attributes are read-only snapshots.  ``records`` retains records in
    durable journal order; its final record hash is ``head_sha256``.
    """

    records: tuple[Mapping[str, Any], ...]
    head_sha256: str
    pending_request_sha256s: tuple[str, ...]
    terminal_request_sha256s: tuple[str, ...]
    team_run_sequences: Mapping[str, int]
    material_trial_counts: Mapping[str, int]

    @property
    def record_count(self) -> int:
        return len(self.records)


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    """Return the only accepted JSON representation for a journal object."""

    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise JournalValidationError("journal value is not canonical JSON") from exc


def _record_sha256(record: Mapping[str, Any]) -> str:
    unsigned = dict(record)
    unsigned.pop("record_sha256", None)
    return hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise JournalValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise JournalValidationError(f"non-finite JSON constant: {value}")


def _decode_canonical_line(line: bytes, line_number: int) -> dict[str, Any]:
    if not line.endswith(b"\n") or line == b"\n":
        raise JournalValidationError(f"journal line {line_number} is truncated or blank")
    raw = line[:-1]
    if len(raw) > MAX_RECORD_BYTES:
        raise JournalValidationError(f"journal line {line_number} is too large")
    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise JournalValidationError(f"journal line {line_number} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise JournalValidationError(f"journal line {line_number} is not an object")
    if canonical_json_bytes(value) != raw:
        raise JournalValidationError(f"journal line {line_number} is not canonical JSON")
    return value


def _integer(value: object, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise JournalValidationError(f"{label} must be an integer >= {minimum}")
    if value > 2**63 - 1:
        raise JournalValidationError(f"{label} exceeds the signed 64-bit range")
    return value


def _resource(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise JournalValidationError(f"{label} must be a finite non-negative number")
    number = float(value)
    if not math.isfinite(number) or number < 0.0:
        raise JournalValidationError(f"{label} must be a finite non-negative number")
    return number


def _hash(value: object, label: str, *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise JournalValidationError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise JournalValidationError(f"{label} is not a safe identifier")
    return value


def _team(value: object) -> str:
    if not isinstance(value, str) or _TEAM_ID.fullmatch(value) is None:
        raise JournalValidationError("team_id must be one of team-01 through team-10")
    return value


def _safe_text(value: object, label: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise JournalValidationError(f"{label} must be a non-empty bounded string")
    if value != value.strip() or any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise JournalValidationError(f"{label} contains unsafe whitespace or control characters")
    return value


def _timestamp(value: object, label: str) -> dt.datetime:
    if not isinstance(value, str) or _UTC_TIME.fullmatch(value) is None:
        raise JournalValidationError(f"{label} must be canonical UTC seconds")
    try:
        parsed = dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.UTC)
    except ValueError as exc:
        raise JournalValidationError(f"{label} is not a valid UTC timestamp") from exc
    if parsed.year < 1970:
        raise JournalValidationError(f"{label} predates the supported epoch")
    return parsed


def _relative_path(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 512 or "\\" in value:
        raise JournalValidationError(f"{label} must be a bounded POSIX relative path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or value != path.as_posix()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise JournalValidationError(f"{label} must be a normalized POSIX relative path")
    for part in path.parts:
        if any(ord(character) < 32 or ord(character) == 127 for character in part):
            raise JournalValidationError(f"{label} contains a control character")
    return value


def _json_tree(value: object, label: str, *, depth: int = 0) -> None:
    if depth > 20:
        raise JournalValidationError(f"{label} exceeds maximum JSON nesting")
    if value is None or isinstance(value, (bool, str)):
        return
    if isinstance(value, int) and not isinstance(value, bool):
        if not -(2**63) <= value <= 2**63 - 1:
            raise JournalValidationError(f"{label} contains an out-of-range integer")
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise JournalValidationError(f"{label} contains a non-finite number")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _json_tree(item, f"{label}[{index}]", depth=depth + 1)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise JournalValidationError(f"{label} contains a non-string key")
            _json_tree(item, f"{label}.{key}", depth=depth + 1)
        return
    raise JournalValidationError(f"{label} contains a non-JSON value")


def _validate_train_window(value: object) -> None:
    if not isinstance(value, dict) or value != dict(FROZEN_TRAIN_WINDOW):
        raise JournalValidationError("train_window differs from the frozen V3 train window")
    _timestamp(value["start_utc"], "train_window.start_utc")
    _timestamp(value["end_exclusive_utc"], "train_window.end_exclusive_utc")


def _validate_cost_model(value: object) -> None:
    if (
        not isinstance(value, dict)
        or canonical_json_bytes(value)
        != canonical_json_bytes(dict(FROZEN_COST_MODEL))
    ):
        raise JournalValidationError("cost_model differs from the frozen V3 cost model")


def _validate_gate_vector(value: object, *, require_nonempty: bool) -> None:
    if not isinstance(value, dict) or (require_nonempty and not value):
        raise JournalValidationError("gate_vector must be an object with the required gate outcomes")
    for name, outcome in value.items():
        if not isinstance(name, str) or _GATE_NAME.fullmatch(name) is None:
            raise JournalValidationError("gate_vector contains an unsafe gate name")
        if not isinstance(outcome, bool):
            raise JournalValidationError("gate_vector outcomes must be booleans")


def _validate_artifacts(value: object, *, require_nonempty: bool) -> None:
    if not isinstance(value, dict) or (require_nonempty and not value):
        raise JournalValidationError("artifact_hashes must contain successful run artifacts")
    for path, digest in value.items():
        _relative_path(path, "artifact path")
        _hash(digest, f"artifact_hashes[{path!r}]")


def _validate_request_shape(record: Mapping[str, Any]) -> None:
    if set(record) != _REQUEST_KEYS:
        raise JournalValidationError("request_accepted has missing or unknown keys")
    team_id = _team(record["team_id"])
    _integer(record["run_sequence"], "run_sequence", minimum=1)
    _identifier(record["run_id"], "run_id")
    candidate = _identifier(record["candidate_id"], "candidate_id")
    parent = record["parent_candidate_id"]
    if parent is not None:
        _identifier(parent, "parent_candidate_id")
        if parent == candidate:
            raise JournalValidationError("candidate_id cannot be its own parent")
    _safe_text(record["purpose"], "purpose", maximum=512)
    _timestamp(record["accepted_at_utc"], "accepted_at_utc")
    for field in _REQUEST_HASH_FIELDS:
        _hash(record[field], field)
    source_archive_path = _relative_path(
        record["source_archive_path"], "source_archive_path"
    )
    if source_archive_path != (
        "reports-top40-v3/source-archives/sha256/"
        f"{record['source_archive_sha256']}.json"
    ):
        raise JournalValidationError(
            "source_archive_path must be content-addressed by source_archive_sha256"
        )
    _integer(record["seed"], "seed")
    if not isinstance(record["material_parameters"], dict):
        raise JournalValidationError("material_parameters must be a JSON object")
    _json_tree(record["material_parameters"], "material_parameters")
    _validate_train_window(record["train_window"])
    _validate_cost_model(record["cost_model"])
    output_path = _relative_path(record["output_path"], "output_path")
    output_parts = PurePosixPath(output_path).parts
    if (
        len(output_parts) < 4
        or output_parts[:3] != ("reports-top40-v3", "labs", team_id)
    ):
        raise JournalValidationError(
            "output_path must be below reports-top40-v3/labs/<same team_id>/"
        )
    _integer(
        record["cumulative_material_trial_count"],
        "cumulative_material_trial_count",
        minimum=1,
    )


def _validate_terminal_shape(record: Mapping[str, Any]) -> None:
    if set(record) != _TERMINAL_KEYS:
        raise JournalValidationError("terminal event has missing or unknown keys")
    event_type = record["event_type"]
    if event_type not in _TERMINAL_TYPES:
        raise JournalValidationError("terminal event_type is invalid")
    _team(record["team_id"])
    _integer(record["run_sequence"], "run_sequence", minimum=1)
    _identifier(record["run_id"], "run_id")
    _identifier(record["candidate_id"], "candidate_id")
    _hash(record["request_sha256"], "request_sha256")
    _timestamp(record["completed_at_utc"], "completed_at_utc")
    _resource(record["cpu_seconds"], "cpu_seconds")
    _resource(record["wall_seconds"], "wall_seconds")
    _integer(
        record["cumulative_material_trial_count"],
        "cumulative_material_trial_count",
        minimum=1,
    )

    succeeded = event_type == "succeeded"
    _validate_gate_vector(record["gate_vector"], require_nonempty=succeeded)
    _hash(record["metric_packet_sha256"], "metric_packet_sha256", nullable=not succeeded)
    _validate_artifacts(record["artifact_hashes"], require_nonempty=succeeded)
    if succeeded:
        if record["failure_reason"] is not None:
            raise JournalValidationError("successful terminal event cannot have failure_reason")
    else:
        _safe_text(record["failure_reason"], "failure_reason", maximum=2_048)


def _event_time(record: Mapping[str, Any]) -> dt.datetime:
    if record["event_type"] == "request_accepted":
        return _timestamp(record["accepted_at_utc"], "accepted_at_utc")
    return _timestamp(record["completed_at_utc"], "completed_at_utc")


def replay_journal_bytes(payload: bytes) -> JournalState:
    """Validate and replay exact journal bytes, rejecting any ambiguity."""

    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")
    if payload and not payload.endswith(b"\n"):
        raise JournalValidationError("journal ends with a truncated line")

    records: list[dict[str, Any]] = []
    requests: dict[str, dict[str, Any]] = {}
    terminal_requests: set[str] = set()
    run_ids: set[str] = set()
    team_sequences: dict[str, int] = {}
    trial_counts: dict[str, int] = {}
    previous_hash = GENESIS_SHA256
    previous_time: dt.datetime | None = None

    for event_sequence, line in enumerate(payload.splitlines(keepends=True), start=1):
        record = _decode_canonical_line(line, event_sequence)
        event_type = record.get("event_type")
        if event_type == "request_accepted":
            _validate_request_shape(record)
        elif event_type in _TERMINAL_TYPES:
            _validate_terminal_shape(record)
        else:
            raise JournalValidationError(f"journal line {event_sequence} has unknown event_type")

        if record["schema_version"] != SCHEMA_VERSION:
            raise JournalValidationError("journal schema_version is unsupported")
        if _integer(record["event_sequence"], "event_sequence", minimum=1) != event_sequence:
            raise JournalValidationError("journal event_sequence has a gap or duplicate")
        if record["previous_sha256"] != previous_hash:
            raise JournalValidationError("journal hash-chain predecessor mismatch")
        _hash(record["record_sha256"], "record_sha256")
        expected_hash = _record_sha256(record)
        if record["record_sha256"] != expected_hash:
            raise JournalValidationError("journal record hash mismatch")

        event_time = _event_time(record)
        if previous_time is not None and event_time < previous_time:
            raise JournalValidationError("journal timestamps move backwards")

        if event_type == "request_accepted":
            team = record["team_id"]
            if set(requests) - terminal_requests:
                raise JournalValidationError(
                    "a request_accepted event is already pending globally"
                )
            expected_run_sequence = team_sequences.get(team, 0) + 1
            expected_trial_count = trial_counts.get(team, 0) + 1
            if record["run_sequence"] != expected_run_sequence:
                raise JournalValidationError("per-team run_sequence has a gap, duplicate, or reset")
            if record["cumulative_material_trial_count"] != expected_trial_count:
                raise JournalValidationError("cumulative material trial count has a gap or reset")
            if record["run_id"] in run_ids:
                raise JournalValidationError("run_id is not globally unique")
            run_ids.add(record["run_id"])
            team_sequences[team] = record["run_sequence"]
            trial_counts[team] = record["cumulative_material_trial_count"]
            requests[record["record_sha256"]] = record
        else:
            request_hash = record["request_sha256"]
            request = requests.get(request_hash)
            if request is None:
                raise JournalValidationError("terminal event has no accepted request")
            if request_hash in terminal_requests:
                raise JournalValidationError("accepted request has duplicate terminal events")
            for field in ("team_id", "run_sequence", "run_id", "candidate_id"):
                if record[field] != request[field]:
                    raise JournalValidationError(f"terminal {field} does not match its request")
            if (
                record["cumulative_material_trial_count"]
                != request["cumulative_material_trial_count"]
            ):
                raise JournalValidationError("terminal material trial count resets or mismatches")
            if event_time < _event_time(request):
                raise JournalValidationError("terminal predates its accepted request")
            terminal_requests.add(request_hash)

        records.append(record)
        previous_hash = expected_hash
        previous_time = event_time

    pending = tuple(sorted(set(requests) - terminal_requests))
    return JournalState(
        records=tuple(records),
        head_sha256=previous_hash,
        pending_request_sha256s=pending,
        terminal_request_sha256s=tuple(sorted(terminal_requests)),
        team_run_sequences=MappingProxyType(dict(sorted(team_sequences.items()))),
        material_trial_counts=MappingProxyType(dict(sorted(trial_counts.items()))),
    )


def _path_identity_matches(path: Path, descriptor_stat: os.stat_result) -> bool:
    try:
        path_stat = os.stat(path, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return (path_stat.st_dev, path_stat.st_ino) == (
        descriptor_stat.st_dev,
        descriptor_stat.st_ino,
    )


def _reject_unsafe_existing_path(path: Path) -> None:
    try:
        path_stat = os.lstat(path)
    except FileNotFoundError:
        return
    if stat.S_ISLNK(path_stat.st_mode):
        raise JournalValidationError("journal path is a symlink")
    if not stat.S_ISREG(path_stat.st_mode):
        raise JournalValidationError("journal path is not a regular file")


@contextlib.contextmanager
def exclusive_journal_lock(path: str | os.PathLike[str]) -> Iterator[BinaryIO]:
    """Open/create a regular journal and hold an advisory exclusive file lock.

    The context must not be nested with either append function for the same path.
    All cooperating writers must use this lock or the append functions.
    """

    journal_path = Path(path)
    _reject_unsafe_existing_path(journal_path)
    flags = os.O_APPEND | os.O_CREAT | os.O_RDWR
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(journal_path, flags, 0o600)
    except OSError as exc:
        raise JournalValidationError("cannot safely open journal") from exc

    handle: BinaryIO | None = None
    try:
        descriptor_stat = os.fstat(descriptor)
        if not stat.S_ISREG(descriptor_stat.st_mode):
            raise JournalValidationError("journal descriptor is not a regular file")
        handle = os.fdopen(descriptor, "r+b", buffering=0)
        descriptor = -1
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        descriptor_stat = os.fstat(handle.fileno())
        if not _path_identity_matches(journal_path, descriptor_stat):
            raise JournalValidationError("journal path changed while acquiring its lock")
        yield handle
    finally:
        if handle is not None:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()
        elif descriptor >= 0:
            os.close(descriptor)


def _read_locked(handle: BinaryIO) -> bytes:
    handle.seek(0)
    payload = handle.read()
    if not isinstance(payload, bytes):
        raise JournalValidationError("journal did not yield bytes")
    return payload


def _append_validated_record(
    path: str | os.PathLike[str], event: Mapping[str, Any]
) -> JournalState:
    with exclusive_journal_lock(path) as handle:
        current_bytes = _read_locked(handle)
        current = replay_journal_bytes(current_bytes)
        record = {
            "schema_version": SCHEMA_VERSION,
            "event_sequence": current.record_count + 1,
            "previous_sha256": current.head_sha256,
            **event,
        }
        record["record_sha256"] = _record_sha256(record)
        line = canonical_json_bytes(record) + b"\n"
        if len(line) - 1 > MAX_RECORD_BYTES:
            raise JournalValidationError("proposed journal record is too large")

        next_state = replay_journal_bytes(current_bytes + line)
        handle.seek(0, os.SEEK_END)
        written = handle.write(line)
        if written != len(line):
            raise OSError("short append left the journal fail-closed")
        handle.flush()
        os.fsync(handle.fileno())
        return next_state


def append_request_accepted(
    path: str | os.PathLike[str],
    *,
    team_id: str,
    run_sequence: int,
    run_id: str,
    candidate_id: str,
    parent_candidate_id: str | None,
    purpose: str,
    accepted_at_utc: str,
    source_bundle_sha256: str,
    source_archive_path: str,
    source_archive_sha256: str,
    strategy_sha256: str,
    dependency_lock_sha256: str,
    config_sha256: str,
    risk_policy_sha256: str,
    data_authority_sha256: str,
    evaluator_sha256: str,
    seed: int,
    material_parameters: Mapping[str, Any],
    train_window: Mapping[str, str],
    cost_model: Mapping[str, Any],
    output_path: str,
    cumulative_material_trial_count: int,
) -> JournalState:
    """Durably accept one run request and return only after its fsync.

    Callers must not start the requested execution until this function returns.
    The returned state's final record supplies the ``request_sha256`` required by
    ``append_terminal_event``.
    """

    event = {
        "event_type": "request_accepted",
        "team_id": team_id,
        "run_sequence": run_sequence,
        "run_id": run_id,
        "candidate_id": candidate_id,
        "parent_candidate_id": parent_candidate_id,
        "purpose": purpose,
        "accepted_at_utc": accepted_at_utc,
        "source_bundle_sha256": source_bundle_sha256,
        "source_archive_path": source_archive_path,
        "source_archive_sha256": source_archive_sha256,
        "strategy_sha256": strategy_sha256,
        "dependency_lock_sha256": dependency_lock_sha256,
        "config_sha256": config_sha256,
        "risk_policy_sha256": risk_policy_sha256,
        "data_authority_sha256": data_authority_sha256,
        "evaluator_sha256": evaluator_sha256,
        "seed": seed,
        "material_parameters": dict(material_parameters),
        "train_window": dict(train_window),
        "cost_model": dict(cost_model),
        "output_path": output_path,
        "cumulative_material_trial_count": cumulative_material_trial_count,
    }
    return _append_validated_record(path, event)


def append_terminal_event(
    path: str | os.PathLike[str],
    *,
    event_type: str,
    team_id: str,
    run_sequence: int,
    run_id: str,
    candidate_id: str,
    request_sha256: str,
    completed_at_utc: str,
    cpu_seconds: float,
    wall_seconds: float,
    gate_vector: Mapping[str, bool],
    metric_packet_sha256: str | None,
    artifact_hashes: Mapping[str, str],
    cumulative_material_trial_count: int,
    failure_reason: str | None,
) -> JournalState:
    """Durably append exactly one terminal outcome for an accepted request."""

    event = {
        "event_type": event_type,
        "team_id": team_id,
        "run_sequence": run_sequence,
        "run_id": run_id,
        "candidate_id": candidate_id,
        "request_sha256": request_sha256,
        "completed_at_utc": completed_at_utc,
        "cpu_seconds": float(cpu_seconds),
        "wall_seconds": float(wall_seconds),
        "gate_vector": dict(gate_vector),
        "metric_packet_sha256": metric_packet_sha256,
        "artifact_hashes": dict(artifact_hashes),
        "cumulative_material_trial_count": cumulative_material_trial_count,
        "failure_reason": failure_reason,
    }
    return _append_validated_record(path, event)


def replay_journal(path: str | os.PathLike[str]) -> JournalState:
    """Read and validate an existing regular, non-symlink journal."""

    journal_path = Path(path)
    _reject_unsafe_existing_path(journal_path)
    if not journal_path.exists():
        raise JournalValidationError("journal does not exist")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(journal_path, flags)
    except OSError as exc:
        raise JournalValidationError("cannot safely read journal") from exc
    try:
        descriptor_stat = os.fstat(descriptor)
        if not stat.S_ISREG(descriptor_stat.st_mode):
            raise JournalValidationError("journal descriptor is not a regular file")
        if not _path_identity_matches(journal_path, descriptor_stat):
            raise JournalValidationError("journal path changed while opening it")
        with os.fdopen(descriptor, "rb", buffering=0) as handle:
            descriptor = -1
            payload = handle.read()
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    return replay_journal_bytes(payload)


__all__ = [
    "FROZEN_COST_MODEL",
    "FROZEN_TRAIN_WINDOW",
    "GENESIS_SHA256",
    "JournalState",
    "JournalValidationError",
    "SCHEMA_VERSION",
    "append_request_accepted",
    "append_terminal_event",
    "canonical_json_bytes",
    "exclusive_journal_lock",
    "replay_journal",
    "replay_journal_bytes",
]
