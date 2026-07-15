"""Strict, journal-first research accounting primitives for tournament V2.

The organizer journal is the source of truth.  A caller first atomically publishes the
``replacement_journal_bytes`` from a :class:`PlannedJournalAppend`, then projects the exact
team-ledger bytes recorded in that journal.  If the process stops between those operations,
``plan_team_ledger_projection`` supplies the only accepted recovery bytes.

This module deliberately performs no file writes.  Path helpers validate regular files, while
plans bind the expected old size and SHA-256 so a future CLI can lock, recheck, and atomically
replace files without relying on an unsafe in-place append.
"""

from __future__ import annotations

import base64
import dataclasses
import hashlib
import json
import math
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
ZERO_SHA256 = "0" * 64

_HEX_SHA256 = re.compile(r"[0-9a-f]{64}")
_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_MAX_EVENT_BYTES = 256 * 1024
_MAX_TEXT_LENGTH = 8 * 1024
_MAX_JSON_DEPTH = 32

_REGISTRATION_KEYS = frozenset(
    {
        "schema_version",
        "event_type",
        "timestamp_utc",
        "team_id",
        "family_id",
        "candidate_id",
        "strategy_sha256",
        "source_bundle_sha256",
        "risk_config_sha256",
        "config_sha256",
        "parameters",
        "seed",
        "thesis",
        "falsifier",
    }
)
_RESULT_KEYS = frozenset(
    {
        "schema_version",
        "event_type",
        "timestamp_utc",
        "team_id",
        "family_id",
        "candidate_id",
        "registration_sha256",
        "status",
        "failure_reason",
        "artifact_hashes",
        "metrics_summary",
        "cpu_hours",
        "wall_clock_hours",
    }
)
_JOURNAL_RECORD_KEYS = frozenset(
    {
        "schema_version",
        "sequence",
        "event_type",
        "timestamp_utc",
        "previous_record_sha256",
        "payload",
        "record_sha256",
    }
)
_GENESIS_PAYLOAD_KEYS = frozenset(
    {
        "tournament_id",
        "team_ids",
        "maximum_material_configurations_per_team",
        "maximum_cpu_hours_per_team",
        "maximum_wall_clock_hours_per_team",
    }
)
_REGISTRATION_PAYLOAD_KEYS = frozenset(
    {
        "team_id",
        "family_id",
        "candidate_id",
        "ledger_event_bytes_base64",
        "ledger_event_sha256",
        "cumulative_material_trial_count",
        "cumulative_cpu_hours",
        "cumulative_wall_clock_hours",
    }
)
_RESULT_PAYLOAD_KEYS = _REGISTRATION_PAYLOAD_KEYS | {
    "registration_sha256",
    "status",
}
_RESULT_STATUSES = frozenset({"completed", "failed", "interrupted"})


class ResearchAccountingError(ValueError):
    """Raised when research evidence cannot be accepted without weakening accounting."""


@dataclasses.dataclass(frozen=True)
class ResearchPolicy:
    """Immutable identities and per-team budgets bound into journal genesis."""

    tournament_id: str
    team_ids: tuple[str, ...]
    maximum_material_configurations_per_team: int
    maximum_cpu_hours_per_team: float
    maximum_wall_clock_hours_per_team: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_ids", tuple(self.team_ids))
        _validate_identifier(self.tournament_id, "tournament_id")
        if not self.team_ids or len(self.team_ids) != len(set(self.team_ids)):
            raise ResearchAccountingError("team_ids must be a non-empty unique sequence")
        for index, team_id in enumerate(self.team_ids):
            _validate_identifier(team_id, f"team_ids[{index}]")
        count = self.maximum_material_configurations_per_team
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            raise ResearchAccountingError(
                "maximum_material_configurations_per_team must be a positive integer"
            )
        _positive_number(self.maximum_cpu_hours_per_team, "maximum_cpu_hours_per_team")
        _positive_number(
            self.maximum_wall_clock_hours_per_team, "maximum_wall_clock_hours_per_team"
        )


@dataclasses.dataclass(frozen=True)
class TeamAccounting:
    """Replayed organizer authority for one team's material trials."""

    material_trial_count: int
    cpu_hours: float
    wall_clock_hours: float
    registrations: Mapping[str, Mapping[str, Any]]
    registration_sha256: Mapping[str, str]
    results: Mapping[str, Mapping[str, Any]]
    ledger_bytes: bytes

    @property
    def pending_candidate_ids(self) -> tuple[str, ...]:
        return tuple(candidate for candidate in self.registrations if candidate not in self.results)


@dataclasses.dataclass(frozen=True)
class JournalState:
    """A fully validated replay of canonical organizer journal bytes."""

    records: tuple[Mapping[str, Any], ...]
    journal_bytes: bytes
    journal_sha256: str
    genesis_sha256: str
    head_sha256: str
    last_timestamp_utc: str
    teams: Mapping[str, TeamAccounting]


@dataclasses.dataclass(frozen=True)
class PlannedJournalAppend:
    """CAS-style preconditions and complete atomic replacement bytes for one journal event."""

    expected_journal_size: int
    expected_journal_sha256: str
    expected_head_sha256: str
    record: Mapping[str, Any]
    record_bytes: bytes
    replacement_journal_bytes: bytes
    new_head_sha256: str
    team_id: str | None
    expected_team_ledger_size: int | None
    expected_team_ledger_sha256: str | None
    team_ledger_append_bytes: bytes
    replacement_team_ledger_bytes: bytes | None


@dataclasses.dataclass(frozen=True)
class LedgerProjectionPlan:
    """Exact journal-authorized bytes needed to repair a missing ledger suffix."""

    team_id: str
    journal_sha256: str
    journal_head_sha256: str
    expected_current_size: int
    expected_current_sha256: str
    append_bytes: bytes
    replacement_ledger_bytes: bytes


def canonical_json_bytes(value: object) -> bytes:
    """Encode one JSON value in the only accepted canonical representation."""

    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ResearchAccountingError("value is not finite canonical JSON") from exc


def canonical_json_line(value: object) -> bytes:
    """Encode one newline-terminated canonical JSONL record."""

    return canonical_json_bytes(value) + b"\n"


def build_trial_registration(
    *,
    timestamp_utc: str,
    team_id: str,
    family_id: str,
    candidate_id: str,
    strategy_sha256: str,
    source_bundle_sha256: str,
    risk_config_sha256: str,
    config_sha256: str,
    parameters: Mapping[str, object],
    seed: int,
    thesis: str,
    falsifier: str,
) -> bytes:
    """Build and self-validate an exact preregistration ledger line."""

    event = {
        "schema_version": SCHEMA_VERSION,
        "event_type": "trial_registration",
        "timestamp_utc": timestamp_utc,
        "team_id": team_id,
        "family_id": family_id,
        "candidate_id": candidate_id,
        "strategy_sha256": strategy_sha256,
        "source_bundle_sha256": source_bundle_sha256,
        "risk_config_sha256": risk_config_sha256,
        "config_sha256": config_sha256,
        "parameters": dict(parameters),
        "seed": seed,
        "thesis": thesis,
        "falsifier": falsifier,
    }
    line = canonical_json_line(event)
    validate_trial_registration_bytes(line)
    return line


def build_trial_result(
    *,
    timestamp_utc: str,
    team_id: str,
    family_id: str,
    candidate_id: str,
    registration_sha256: str,
    status: str,
    failure_reason: str | None,
    artifact_hashes: Mapping[str, str],
    metrics_summary: Mapping[str, object],
    cpu_hours: float,
    wall_clock_hours: float,
) -> bytes:
    """Build and self-validate an exact material-trial result ledger line."""

    event = {
        "schema_version": SCHEMA_VERSION,
        "event_type": "trial_result",
        "timestamp_utc": timestamp_utc,
        "team_id": team_id,
        "family_id": family_id,
        "candidate_id": candidate_id,
        "registration_sha256": registration_sha256,
        "status": status,
        "failure_reason": failure_reason,
        "artifact_hashes": dict(artifact_hashes),
        "metrics_summary": dict(metrics_summary),
        "cpu_hours": cpu_hours,
        "wall_clock_hours": wall_clock_hours,
    }
    line = canonical_json_line(event)
    validate_trial_result_bytes(line)
    return line


def validate_trial_registration_bytes(
    raw_line: bytes, policy: ResearchPolicy | None = None
) -> dict[str, Any]:
    """Validate one canonical preregistration, optionally against allowed teams."""

    event = _decode_canonical_line(raw_line, "trial registration")
    if set(event) != _REGISTRATION_KEYS:
        raise ResearchAccountingError("trial registration has an invalid schema")
    if event["schema_version"] != SCHEMA_VERSION or event["event_type"] != "trial_registration":
        raise ResearchAccountingError("trial registration version/type is invalid")
    _validate_timestamp(event["timestamp_utc"], "trial registration timestamp_utc")
    for field in ("team_id", "family_id", "candidate_id"):
        _validate_identifier(event[field], f"trial registration {field}")
    if policy is not None and event["team_id"] not in policy.team_ids:
        raise ResearchAccountingError("trial registration team_id is not in policy")
    for field in (
        "strategy_sha256",
        "source_bundle_sha256",
        "risk_config_sha256",
        "config_sha256",
    ):
        _validate_sha256(event[field], f"trial registration {field}")
    if not isinstance(event["parameters"], dict):
        raise ResearchAccountingError("trial registration parameters must be an object")
    _validate_json_tree(event["parameters"], "trial registration parameters")
    seed = event["seed"]
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**63:
        raise ResearchAccountingError("trial registration seed must be a non-negative int64")
    _validate_text(event["thesis"], "trial registration thesis")
    _validate_text(event["falsifier"], "trial registration falsifier")
    return event


def validate_trial_result_bytes(
    raw_line: bytes, policy: ResearchPolicy | None = None
) -> dict[str, Any]:
    """Validate one canonical result, optionally against allowed teams."""

    event = _decode_canonical_line(raw_line, "trial result")
    if set(event) != _RESULT_KEYS:
        raise ResearchAccountingError("trial result has an invalid schema")
    if event["schema_version"] != SCHEMA_VERSION or event["event_type"] != "trial_result":
        raise ResearchAccountingError("trial result version/type is invalid")
    _validate_timestamp(event["timestamp_utc"], "trial result timestamp_utc")
    for field in ("team_id", "family_id", "candidate_id"):
        _validate_identifier(event[field], f"trial result {field}")
    if policy is not None and event["team_id"] not in policy.team_ids:
        raise ResearchAccountingError("trial result team_id is not in policy")
    _validate_sha256(event["registration_sha256"], "trial result registration_sha256")
    status = event["status"]
    if not isinstance(status, str) or status not in _RESULT_STATUSES:
        raise ResearchAccountingError("trial result status is invalid")
    failure_reason = event["failure_reason"]
    if status == "completed":
        if failure_reason is not None:
            raise ResearchAccountingError("a completed trial cannot have a failure_reason")
    else:
        _validate_text(failure_reason, "trial result failure_reason")
    artifacts = event["artifact_hashes"]
    if not isinstance(artifacts, dict):
        raise ResearchAccountingError("trial result artifact_hashes must be an object")
    if status == "completed" and not artifacts:
        raise ResearchAccountingError("a completed trial must bind at least one artifact")
    for name, digest in artifacts.items():
        _validate_artifact_name(name)
        _validate_sha256(digest, f"trial result artifact_hashes.{name}")
    metrics = event["metrics_summary"]
    if not isinstance(metrics, dict):
        raise ResearchAccountingError("trial result metrics_summary must be an object")
    if status == "completed" and not metrics:
        raise ResearchAccountingError("a completed trial must bind a metrics summary")
    _validate_json_tree(metrics, "trial result metrics_summary")
    _nonnegative_number(event["cpu_hours"], "trial result cpu_hours")
    _nonnegative_number(event["wall_clock_hours"], "trial result wall_clock_hours")
    return event


def plan_genesis(*, timestamp_utc: str, policy: ResearchPolicy) -> PlannedJournalAppend:
    """Plan the only valid first organizer-journal record."""

    _validate_timestamp(timestamp_utc, "journal genesis timestamp_utc")
    payload = {
        "tournament_id": policy.tournament_id,
        "team_ids": list(policy.team_ids),
        "maximum_material_configurations_per_team": (
            policy.maximum_material_configurations_per_team
        ),
        "maximum_cpu_hours_per_team": policy.maximum_cpu_hours_per_team,
        "maximum_wall_clock_hours_per_team": policy.maximum_wall_clock_hours_per_team,
    }
    record, line = _build_journal_record(
        sequence=0,
        event_type="genesis",
        timestamp_utc=timestamp_utc,
        previous_record_sha256=ZERO_SHA256,
        payload=payload,
    )
    validate_journal_bytes(line, policy)
    return PlannedJournalAppend(
        expected_journal_size=0,
        expected_journal_sha256=_sha256(b""),
        expected_head_sha256=ZERO_SHA256,
        record=record,
        record_bytes=line,
        replacement_journal_bytes=line,
        new_head_sha256=str(record["record_sha256"]),
        team_id=None,
        expected_team_ledger_size=None,
        expected_team_ledger_sha256=None,
        team_ledger_append_bytes=b"",
        replacement_team_ledger_bytes=None,
    )


def plan_registration_append(
    journal_bytes: bytes,
    registration_bytes: bytes,
    team_ledger_bytes: bytes,
    *,
    policy: ResearchPolicy,
) -> PlannedJournalAppend:
    """Plan a journal-first material-trial registration append."""

    event = validate_trial_registration_bytes(registration_bytes, policy)
    return _plan_event_append(
        journal_bytes,
        registration_bytes,
        team_ledger_bytes,
        event=event,
        policy=policy,
    )


def plan_result_append(
    journal_bytes: bytes,
    result_bytes: bytes,
    team_ledger_bytes: bytes,
    *,
    policy: ResearchPolicy,
) -> PlannedJournalAppend:
    """Plan a journal-first result append and account all consumed resources."""

    event = validate_trial_result_bytes(result_bytes, policy)
    return _plan_event_append(
        journal_bytes,
        result_bytes,
        team_ledger_bytes,
        event=event,
        policy=policy,
    )


def validate_journal_bytes(raw: bytes, policy: ResearchPolicy) -> JournalState:
    """Fail closed unless all organizer records and replayed accounting are exact."""

    if not isinstance(raw, bytes) or not raw:
        raise ResearchAccountingError("organizer journal must be non-empty bytes")
    raw_lines = raw.splitlines(keepends=True)
    if not raw_lines or any(not line.endswith(b"\n") for line in raw_lines):
        raise ResearchAccountingError("organizer journal records must be newline terminated")

    records: list[dict[str, Any]] = []
    mutable_teams: dict[str, dict[str, Any]] = {
        team_id: {
            "material_trial_count": 0,
            "cpu_hours": 0.0,
            "wall_clock_hours": 0.0,
            "registrations": {},
            "registration_sha256": {},
            "results": {},
            "ledger_lines": [],
        }
        for team_id in policy.team_ids
    }
    previous_hash = ZERO_SHA256
    previous_timestamp: datetime | None = None
    genesis_sha256 = ""

    for expected_sequence, raw_line in enumerate(raw_lines):
        record = _decode_canonical_line(raw_line, f"journal record {expected_sequence}")
        if set(record) != _JOURNAL_RECORD_KEYS:
            raise ResearchAccountingError(f"journal record {expected_sequence} has invalid schema")
        if record["schema_version"] != SCHEMA_VERSION:
            raise ResearchAccountingError(f"journal record {expected_sequence} version is invalid")
        sequence = record["sequence"]
        if isinstance(sequence, bool) or sequence != expected_sequence:
            raise ResearchAccountingError("organizer journal sequence is not contiguous")
        _validate_sha256(
            record["previous_record_sha256"],
            f"journal record {expected_sequence} previous_record_sha256",
        )
        _validate_sha256(
            record["record_sha256"], f"journal record {expected_sequence} record_sha256"
        )
        core = {key: value for key, value in record.items() if key != "record_sha256"}
        digest = _sha256(canonical_json_bytes(core))
        if record["previous_record_sha256"] != previous_hash or record["record_sha256"] != digest:
            raise ResearchAccountingError(
                f"organizer journal hash chain breaks at record {expected_sequence}"
            )
        timestamp = _validate_timestamp(
            record["timestamp_utc"], f"journal record {expected_sequence} timestamp_utc"
        )
        if previous_timestamp is not None and timestamp < previous_timestamp:
            raise ResearchAccountingError("organizer journal timestamps are not monotonic")
        previous_timestamp = timestamp
        payload = record["payload"]
        if not isinstance(payload, dict):
            raise ResearchAccountingError(
                f"journal record {expected_sequence} payload is not an object"
            )

        if expected_sequence == 0:
            _validate_genesis_record(record, payload, policy)
            genesis_sha256 = digest
        elif record["event_type"] == "trial_registration":
            _replay_registration(record, payload, mutable_teams, policy)
        elif record["event_type"] == "trial_result":
            _replay_result(record, payload, mutable_teams, policy)
        else:
            raise ResearchAccountingError(
                f"journal record {expected_sequence} has an invalid event_type"
            )
        previous_hash = digest
        records.append(record)

    teams = {
        team_id: TeamAccounting(
            material_trial_count=int(team["material_trial_count"]),
            cpu_hours=float(team["cpu_hours"]),
            wall_clock_hours=float(team["wall_clock_hours"]),
            registrations=dict(team["registrations"]),
            registration_sha256=dict(team["registration_sha256"]),
            results=dict(team["results"]),
            ledger_bytes=b"".join(team["ledger_lines"]),
        )
        for team_id, team in mutable_teams.items()
    }
    return JournalState(
        records=tuple(records),
        journal_bytes=raw,
        journal_sha256=_sha256(raw),
        genesis_sha256=genesis_sha256,
        head_sha256=previous_hash,
        last_timestamp_utc=str(records[-1]["timestamp_utc"]),
        teams=teams,
    )


def validate_journal_path(path: Path, policy: ResearchPolicy) -> JournalState:
    """Read and validate a regular, non-symlink organizer journal."""

    return validate_journal_bytes(_read_regular_file(path, "organizer journal"), policy)


def expected_team_ledger_bytes(state: JournalState, team_id: str) -> bytes:
    """Return the exact per-team ledger projection authorized by the journal."""

    try:
        return state.teams[team_id].ledger_bytes
    except KeyError as exc:
        raise ResearchAccountingError(f"unknown team_id: {team_id}") from exc


def validate_team_ledger_bytes(raw: bytes, state: JournalState, team_id: str) -> None:
    """Require byte-for-byte equality with the journal's complete team projection."""

    expected = expected_team_ledger_bytes(state, team_id)
    if not isinstance(raw, bytes) or raw != expected:
        raise ResearchAccountingError(f"{team_id} ledger diverges from organizer journal")


def validate_team_ledger_path(path: Path, state: JournalState, team_id: str) -> None:
    """Validate a regular ledger file against its complete journal projection."""

    validate_team_ledger_bytes(_read_regular_file(path, f"{team_id} ledger"), state, team_id)


def plan_team_ledger_projection(
    current_ledger_bytes: bytes,
    state: JournalState,
    team_id: str,
) -> LedgerProjectionPlan:
    """Plan recovery only when the current ledger is an exact whole-record prefix."""

    if not isinstance(current_ledger_bytes, bytes):
        raise ResearchAccountingError("current team ledger must be bytes")
    expected = expected_team_ledger_bytes(state, team_id)
    boundaries = {0}
    position = 0
    for line in expected.splitlines(keepends=True):
        position += len(line)
        boundaries.add(position)
    if (
        len(current_ledger_bytes) not in boundaries
        or not expected.startswith(current_ledger_bytes)
    ):
        raise ResearchAccountingError(
            f"{team_id} ledger is not a complete journal-authorized prefix"
        )
    return LedgerProjectionPlan(
        team_id=team_id,
        journal_sha256=state.journal_sha256,
        journal_head_sha256=state.head_sha256,
        expected_current_size=len(current_ledger_bytes),
        expected_current_sha256=_sha256(current_ledger_bytes),
        append_bytes=expected[len(current_ledger_bytes) :],
        replacement_ledger_bytes=expected,
    )


def _plan_event_append(
    journal_bytes: bytes,
    event_bytes: bytes,
    team_ledger_bytes: bytes,
    *,
    event: dict[str, Any],
    policy: ResearchPolicy,
) -> PlannedJournalAppend:
    state = validate_journal_bytes(journal_bytes, policy)
    team_id = str(event["team_id"])
    validate_team_ledger_bytes(team_ledger_bytes, state, team_id)
    team = state.teams[team_id]
    timestamp = _validate_timestamp(event["timestamp_utc"], "planned event timestamp_utc")
    if timestamp < _validate_timestamp(state.last_timestamp_utc, "journal last timestamp_utc"):
        raise ResearchAccountingError("planned event timestamp precedes journal head")

    candidate_id = str(event["candidate_id"])
    event_digest = _sha256(event_bytes)
    if event["event_type"] == "trial_registration":
        if candidate_id in team.registrations:
            raise ResearchAccountingError(f"candidate already registered: {team_id}/{candidate_id}")
        count = team.material_trial_count + 1
        if count > policy.maximum_material_configurations_per_team:
            raise ResearchAccountingError(f"{team_id} exceeds its material-trial budget")
        cpu_hours = team.cpu_hours
        wall_clock_hours = team.wall_clock_hours
        payload: dict[str, Any] = {
            "team_id": team_id,
            "family_id": event["family_id"],
            "candidate_id": candidate_id,
            "ledger_event_bytes_base64": base64.b64encode(event_bytes).decode("ascii"),
            "ledger_event_sha256": event_digest,
            "cumulative_material_trial_count": count,
            "cumulative_cpu_hours": cpu_hours,
            "cumulative_wall_clock_hours": wall_clock_hours,
        }
    else:
        registration = team.registrations.get(candidate_id)
        if registration is None:
            raise ResearchAccountingError(
                f"trial result has no prior registration: {team_id}/{candidate_id}"
            )
        if candidate_id in team.results:
            raise ResearchAccountingError(f"trial result is a replay: {team_id}/{candidate_id}")
        if event["family_id"] != registration["family_id"]:
            raise ResearchAccountingError("trial result family differs from registration")
        registration_digest = team.registration_sha256[candidate_id]
        if event["registration_sha256"] != registration_digest:
            raise ResearchAccountingError("trial result does not bind the exact registration bytes")
        count = team.material_trial_count
        cpu_hours = team.cpu_hours + float(event["cpu_hours"])
        wall_clock_hours = team.wall_clock_hours + float(event["wall_clock_hours"])
        _enforce_resource_budgets(team_id, cpu_hours, wall_clock_hours, policy)
        payload = {
            "team_id": team_id,
            "family_id": event["family_id"],
            "candidate_id": candidate_id,
            "registration_sha256": registration_digest,
            "status": event["status"],
            "ledger_event_bytes_base64": base64.b64encode(event_bytes).decode("ascii"),
            "ledger_event_sha256": event_digest,
            "cumulative_material_trial_count": count,
            "cumulative_cpu_hours": cpu_hours,
            "cumulative_wall_clock_hours": wall_clock_hours,
        }

    record, record_line = _build_journal_record(
        sequence=len(state.records),
        event_type=str(event["event_type"]),
        timestamp_utc=str(event["timestamp_utc"]),
        previous_record_sha256=state.head_sha256,
        payload=payload,
    )
    replacement_journal = journal_bytes + record_line
    replacement_ledger = team_ledger_bytes + event_bytes
    replayed = validate_journal_bytes(replacement_journal, policy)
    validate_team_ledger_bytes(replacement_ledger, replayed, team_id)
    return PlannedJournalAppend(
        expected_journal_size=len(journal_bytes),
        expected_journal_sha256=_sha256(journal_bytes),
        expected_head_sha256=state.head_sha256,
        record=record,
        record_bytes=record_line,
        replacement_journal_bytes=replacement_journal,
        new_head_sha256=str(record["record_sha256"]),
        team_id=team_id,
        expected_team_ledger_size=len(team_ledger_bytes),
        expected_team_ledger_sha256=_sha256(team_ledger_bytes),
        team_ledger_append_bytes=event_bytes,
        replacement_team_ledger_bytes=replacement_ledger,
    )


def _validate_genesis_record(
    record: Mapping[str, Any], payload: Mapping[str, Any], policy: ResearchPolicy
) -> None:
    if record["event_type"] != "genesis" or record["previous_record_sha256"] != ZERO_SHA256:
        raise ResearchAccountingError("organizer journal has an invalid genesis record")
    if set(payload) != _GENESIS_PAYLOAD_KEYS:
        raise ResearchAccountingError("organizer journal genesis payload has an invalid schema")
    count = payload["maximum_material_configurations_per_team"]
    if isinstance(count, bool) or not isinstance(count, int):
        raise ResearchAccountingError("organizer journal genesis trial budget is invalid")
    _positive_number(
        payload["maximum_cpu_hours_per_team"], "organizer journal genesis CPU budget"
    )
    _positive_number(
        payload["maximum_wall_clock_hours_per_team"],
        "organizer journal genesis wall-clock budget",
    )
    expected = {
        "tournament_id": policy.tournament_id,
        "team_ids": list(policy.team_ids),
        "maximum_material_configurations_per_team": (
            policy.maximum_material_configurations_per_team
        ),
        "maximum_cpu_hours_per_team": policy.maximum_cpu_hours_per_team,
        "maximum_wall_clock_hours_per_team": policy.maximum_wall_clock_hours_per_team,
    }
    if payload != expected:
        raise ResearchAccountingError("organizer journal genesis differs from policy")


def _replay_registration(
    record: Mapping[str, Any],
    payload: Mapping[str, Any],
    teams: dict[str, dict[str, Any]],
    policy: ResearchPolicy,
) -> None:
    if set(payload) != _REGISTRATION_PAYLOAD_KEYS:
        raise ResearchAccountingError("journal registration payload has an invalid schema")
    event_bytes = _event_bytes_from_payload(payload, "journal registration")
    event = validate_trial_registration_bytes(event_bytes, policy)
    _validate_journal_event_identity(record, payload, event)
    team = teams[str(event["team_id"])]
    candidate_id = str(event["candidate_id"])
    if candidate_id in team["registrations"]:
        raise ResearchAccountingError(
            f"duplicate candidate registration: {event['team_id']}/{candidate_id}"
        )
    expected_count = int(team["material_trial_count"]) + 1
    recorded_count = payload["cumulative_material_trial_count"]
    if (
        isinstance(recorded_count, bool)
        or not isinstance(recorded_count, int)
        or recorded_count != expected_count
    ):
        raise ResearchAccountingError("journal cumulative material-trial count is invalid")
    _require_cumulative_resource(payload, "cumulative_cpu_hours", team["cpu_hours"])
    _require_cumulative_resource(
        payload, "cumulative_wall_clock_hours", team["wall_clock_hours"]
    )
    if expected_count > policy.maximum_material_configurations_per_team:
        raise ResearchAccountingError(f"{event['team_id']} exceeds its material-trial budget")
    team["material_trial_count"] = expected_count
    team["registrations"][candidate_id] = event
    team["registration_sha256"][candidate_id] = _sha256(event_bytes)
    team["ledger_lines"].append(event_bytes)


def _replay_result(
    record: Mapping[str, Any],
    payload: Mapping[str, Any],
    teams: dict[str, dict[str, Any]],
    policy: ResearchPolicy,
) -> None:
    if set(payload) != _RESULT_PAYLOAD_KEYS:
        raise ResearchAccountingError("journal result payload has an invalid schema")
    event_bytes = _event_bytes_from_payload(payload, "journal result")
    event = validate_trial_result_bytes(event_bytes, policy)
    _validate_journal_event_identity(record, payload, event)
    team = teams[str(event["team_id"])]
    candidate_id = str(event["candidate_id"])
    registration = team["registrations"].get(candidate_id)
    if registration is None:
        raise ResearchAccountingError("journal result does not follow a registration")
    if candidate_id in team["results"]:
        raise ResearchAccountingError("journal contains a replayed trial result")
    registration_digest = team["registration_sha256"][candidate_id]
    if (
        event["family_id"] != registration["family_id"]
        or event["registration_sha256"] != registration_digest
        or payload["registration_sha256"] != registration_digest
        or payload["status"] != event["status"]
    ):
        raise ResearchAccountingError("journal result differs from its exact registration")
    recorded_count = payload["cumulative_material_trial_count"]
    if (
        isinstance(recorded_count, bool)
        or not isinstance(recorded_count, int)
        or recorded_count != team["material_trial_count"]
    ):
        raise ResearchAccountingError("journal result changes cumulative material-trial count")
    cpu_hours = float(team["cpu_hours"]) + float(event["cpu_hours"])
    wall_clock_hours = float(team["wall_clock_hours"]) + float(event["wall_clock_hours"])
    _require_cumulative_resource(payload, "cumulative_cpu_hours", cpu_hours)
    _require_cumulative_resource(payload, "cumulative_wall_clock_hours", wall_clock_hours)
    _enforce_resource_budgets(str(event["team_id"]), cpu_hours, wall_clock_hours, policy)
    team["cpu_hours"] = cpu_hours
    team["wall_clock_hours"] = wall_clock_hours
    team["results"][candidate_id] = event
    team["ledger_lines"].append(event_bytes)


def _validate_journal_event_identity(
    record: Mapping[str, Any], payload: Mapping[str, Any], event: Mapping[str, Any]
) -> None:
    if (
        record["timestamp_utc"] != event["timestamp_utc"]
        or record["event_type"] != event["event_type"]
        or payload["team_id"] != event["team_id"]
        or payload["family_id"] != event["family_id"]
        or payload["candidate_id"] != event["candidate_id"]
    ):
        raise ResearchAccountingError("journal event identity differs from its ledger bytes")


def _event_bytes_from_payload(payload: Mapping[str, Any], label: str) -> bytes:
    encoded = payload.get("ledger_event_bytes_base64")
    try:
        event_bytes = base64.b64decode(encoded, validate=True)
    except (TypeError, ValueError) as exc:
        raise ResearchAccountingError(f"{label} ledger bytes are not valid base64") from exc
    digest = payload.get("ledger_event_sha256")
    _validate_sha256(digest, f"{label} ledger_event_sha256")
    if _sha256(event_bytes) != digest:
        raise ResearchAccountingError(f"{label} ledger bytes differ from their SHA-256")
    return event_bytes


def _require_cumulative_resource(
    payload: Mapping[str, Any], field: str, expected: float
) -> None:
    value = _nonnegative_number(payload.get(field), f"journal {field}")
    if value != expected:
        raise ResearchAccountingError(f"journal {field} is invalid")


def _enforce_resource_budgets(
    team_id: str, cpu_hours: float, wall_clock_hours: float, policy: ResearchPolicy
) -> None:
    if cpu_hours > policy.maximum_cpu_hours_per_team:
        raise ResearchAccountingError(f"{team_id} exceeds its CPU-hour budget")
    if wall_clock_hours > policy.maximum_wall_clock_hours_per_team:
        raise ResearchAccountingError(f"{team_id} exceeds its wall-clock budget")


def _build_journal_record(
    *,
    sequence: int,
    event_type: str,
    timestamp_utc: str,
    previous_record_sha256: str,
    payload: Mapping[str, object],
) -> tuple[dict[str, Any], bytes]:
    core: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "sequence": sequence,
        "event_type": event_type,
        "timestamp_utc": timestamp_utc,
        "previous_record_sha256": previous_record_sha256,
        "payload": dict(payload),
    }
    record = {**core, "record_sha256": _sha256(canonical_json_bytes(core))}
    return record, canonical_json_line(record)


def _decode_canonical_line(raw_line: bytes, label: str) -> dict[str, Any]:
    if not isinstance(raw_line, bytes):
        raise ResearchAccountingError(f"{label} must be bytes")
    if (
        not raw_line.endswith(b"\n")
        or raw_line.count(b"\n") != 1
        or len(raw_line) > _MAX_EVENT_BYTES * 2
    ):
        raise ResearchAccountingError(f"{label} must be one bounded newline-terminated record")

    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ResearchAccountingError(f"{label} contains a duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ResearchAccountingError(f"{label} contains non-finite JSON: {value}")

    try:
        decoded = json.loads(
            raw_line[:-1].decode("utf-8"),
            object_pairs_hook=object_pairs,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResearchAccountingError(f"{label} is malformed JSON") from exc
    if not isinstance(decoded, dict):
        raise ResearchAccountingError(f"{label} must be a JSON object")
    if canonical_json_line(decoded) != raw_line:
        raise ResearchAccountingError(f"{label} is not canonically encoded")
    return decoded


def _validate_json_tree(value: object, label: str, depth: int = 0) -> None:
    if depth > _MAX_JSON_DEPTH:
        raise ResearchAccountingError(f"{label} exceeds the maximum JSON depth")
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ResearchAccountingError(f"{label} contains a non-finite number")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_tree(item, f"{label}[{index}]", depth + 1)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise ResearchAccountingError(f"{label} contains an invalid object key")
            _validate_json_tree(item, f"{label}.{key}", depth + 1)
        return
    raise ResearchAccountingError(f"{label} contains a non-JSON value")


def _validate_timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ResearchAccountingError(f"{label} must be canonical UTC ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ResearchAccountingError(f"{label} is invalid") from exc
    normalized = parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if parsed.utcoffset() is None or normalized != value:
        raise ResearchAccountingError(f"{label} is not canonical UTC")
    return parsed


def _validate_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ResearchAccountingError(f"{label} is not a valid identifier")
    return value


def _validate_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _HEX_SHA256.fullmatch(value) is None:
        raise ResearchAccountingError(f"{label} must be a lowercase SHA-256")
    return value


def _validate_text(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > _MAX_TEXT_LENGTH
        or any(ord(character) < 32 and character not in "\n\t" for character in value)
    ):
        raise ResearchAccountingError(f"{label} must be non-empty normalized text")
    return value


def _validate_artifact_name(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > 512
        or any(ord(character) < 32 for character in value)
    ):
        raise ResearchAccountingError("trial result contains an invalid artifact name")
    return value


def _nonnegative_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ResearchAccountingError(f"{label} must be a finite non-negative number")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ResearchAccountingError(f"{label} must be a finite non-negative number") from exc
    if not math.isfinite(result) or result < 0.0:
        raise ResearchAccountingError(f"{label} must be a finite non-negative number")
    return result


def _positive_number(value: object, label: str) -> float:
    result = _nonnegative_number(value, label)
    if result <= 0.0:
        raise ResearchAccountingError(f"{label} must be positive")
    return result


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_regular_file(path: Path, label: str) -> bytes:
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ResearchAccountingError(f"{label} is missing or not a safe regular file")
    return path.read_bytes()
