"""Additive lifecycle and organizer-audit controls for Top-40 V2 amendment 0001.

The original Phase-0 record and every file it froze remain authoritative and unchanged.  Draft
activation atomically migrates the mutable run state from exact schema v2 to an amendment-aware
schema v3.  Frozen v2 lifecycle code therefore rejects the state instead of silently ignoring the
administrative hold or the tolled deadline.  This module is the only writer for amendment state.

No score is calculated here.  Diagnostic backfills are organizer-private, non-material audit
events.  Their CPU/wall overhead is accounted separately and never mutates team trial or resource
budgets.
"""

from __future__ import annotations

import copy
import dataclasses
import fcntl
import hashlib
import json
import math
import os
import re
import stat
import subprocess
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any

from crypto_trade.tournament.amendment_integrity_v2 import (
    Phase0Authority,
    TransactionChange,
    UtcClock,
    bounded_event_time,
    collect_private_artifacts,
    ensure_owner_directory,
    git_bytes,
    git_commit_time,
    git_path,
    git_text,
    pretty_json_bytes,
    private_artifact_directory,
    publish_transaction,
    read_private_artifact_bytes,
    read_repo_file,
    recover_transaction,
    require_no_git_history,
    system_utc_now,
    trusted_now,
    unique_first_add_commit,
    verify_phase0_authority,
)
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.research_v2 import (
    JournalState,
    ResearchPolicy,
    validate_journal_bytes,
    validate_team_ledger_bytes,
)
from crypto_trade.tournament.top40_v2 import (
    PHASE0_FROZEN_FILES,
    TEAM_IDS,
    LoadedV2Config,
    validate_run_state,
)

AMENDMENT_ID = "top40-v2-amendment-0001-organizer-private-score-diagnostics"
AMENDMENT_ROOT = f"{TOP40_V2_LAYOUT.tournament_root}/amendments/0001"
HOLD_NOTICE_PATH = f"{AMENDMENT_ROOT}/HOLD-NOTICE.json"
AMENDMENT_REVIEW_PATH = f"{AMENDMENT_ROOT}/REVIEW.json"
AMENDMENT_DRAFT_PATH = f"{AMENDMENT_ROOT}/draft.json"
AMENDMENT_FREEZE_PATH = f"{AMENDMENT_ROOT}/freeze.json"
AMENDMENT_CHAIN_PATH = f"{AMENDMENT_ROOT}/chain.jsonl"
ORGANIZER_AUDIT_PATH = f"{AMENDMENT_ROOT}/organizer_audit.jsonl"
INTEGRATION_MANIFEST_PATH = f"{AMENDMENT_ROOT}/integration-freeze.json"
DIAGNOSTIC_LOCK_GIT_ROOT = "top40-v2-amendment-0001/diagnostic-locks"
DRAFT_LIFECYCLE_STATUS = "draft_hold"
FROZEN_LIFECYCLE_STATUS = "frozen_ready"
DEVELOPMENT_TARGET_FILENAME = "targets.parquet"
REQUIRED_PRIVATE_ARTIFACT_NAMES = (
    "diagnostic-summary.json",
    "labeled-score-panel.parquet",
    "replay-1-scores.parquet",
    "replay-1-targets.parquet",
    "replay-2-scores.parquet",
    "replay-2-targets.parquet",
)
REQUIRED_BACKFILL_CANDIDATES = (
    ("team-01", "rdf-core-h21-k3-g10"),
    ("team-01", "rdf-ref-001"),
)
DIAGNOSTIC_OUTCOME_FIELDS = (
    "canonical_targets_exact",
    "deterministic_replays_passed",
    "four_of_six_fold_ics_positive",
    "pooled_ic_positive",
    "score_ic_gate_passed",
)

AMENDMENT_STATE_SCHEMA_VERSION = 3
AMENDMENT_STATE_SCHEMA_ID = "top40-v2-amendment-aware-state-v1"
AMENDMENT_CHAIN_ID = "top40-v2-amendment-chain-v1"
ORGANIZER_AUDIT_ID = "top40-v2-organizer-diagnostic-audit-v1"
DIAGNOSTIC_KIND = "organizer-private-score-diagnostics-backfill-v1"

SCAFFOLD_FILE_PATHS = (
    "src/crypto_trade/tournament/amendment_integrity_v2.py",
    "src/crypto_trade/tournament/amendment_v2.py",
    "scripts/top40_v2_amendment_0001.py",
    f"{AMENDMENT_ROOT}/AMENDMENT-DRAFT.md",
    f"{AMENDMENT_ROOT}/templates/amendment-review.schema.json",
    f"{AMENDMENT_ROOT}/templates/hold-notice.schema.json",
    f"{AMENDMENT_ROOT}/templates/integration-manifest.schema.json",
    f"{AMENDMENT_ROOT}/templates/diagnostic-backfill-reservation.schema.json",
    f"{AMENDMENT_ROOT}/templates/diagnostic-backfill-result.schema.json",
    "tests/tournament/test_top40_v2_amendment_0001.py",
)
DIAGNOSTIC_ENGINE_FILE_PATHS = (
    "src/crypto_trade/tournament/score_diagnostics_v2.py",
    "src/crypto_trade/tournament/_score_worker_v2.py",
    "src/crypto_trade/tournament/score_adapters/team01_rdf_v1.py",
    f"{AMENDMENT_ROOT}/SCORE-DIAGNOSTIC-SPEC.md",
    "tests/tournament/test_top40_v2_score_diagnostics.py",
    "tests/tournament/test_top40_v2_score_worker.py",
)
AMENDED_ORCHESTRATOR_FILE_PATHS = (
    "scripts/crypto_trade/__init__.py",
    "src/crypto_trade/tournament/amended_orchestrator_v2.py",
    "scripts/top40_v2_amended_tournament.py",
    "tests/tournament/test_top40_v2_amended_orchestrator.py",
)
INTEGRATION_FILE_PATHS = DIAGNOSTIC_ENGINE_FILE_PATHS + AMENDED_ORCHESTRATOR_FILE_PATHS
AMENDMENT_FILE_PATHS = (
    SCAFFOLD_FILE_PATHS + INTEGRATION_FILE_PATHS
)

LEGACY_STATE_KEYS = frozenset(
    {
        "schema_version",
        "tournament",
        "phase",
        "created_at_utc",
        "config_path",
        "config_sha256",
        "research_journal",
        "phase0",
        "qualification_lock",
        "finalist_cohort_lock",
        "objective_lock",
        "final_oos_lock",
        "critic_lock",
        "critic_confirmation_lock",
        "user_ballot_lock",
        "selection_lock",
        "winner_freeze",
        "teams",
    }
)
AMENDMENT_STATE_KEYS = LEGACY_STATE_KEYS | {
    "state_schema",
    "legacy_state_sha256",
    "legacy_projection_sha256",
    "amendment",
    "administrative_hold",
    "organizer_audit",
}

READ_ONLY_OPERATIONS = frozenset(
    {
        "status",
        "validate",
        "documentation",
        "validate-config",
        "validate-risk-policy",
        "research-status",
        "verify-winner-freeze",
    }
)
AMENDMENT_ADMIN_OPERATIONS = frozenset(
    {
        "freeze-amendment",
        "reserve-diagnostic-backfill",
        "run-diagnostic-backfill",
        "resume-amendment",
    }
)
RESULT_BEARING_OPERATIONS = frozenset(
    {
        "init-teams",
        "freeze-phase0",
        "assess-qualification",
        "register-family",
        "pivot-team",
        "register-trial",
        "record-trial-result",
        "run-window",
        "record-development-assessment",
        "record-private-assessment",
        "withdraw-team",
        "close-qualification",
        "lock-finalist-cohort",
        "run-finalist",
        "lock-final-oos",
        "lock-objective",
        "lock-critic",
        "lock-critic-confirmations",
        "lock-user-ballot",
        "lock-selection",
        "freeze-winner",
        "result-release",
    }
)

_SHA256 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_DIAGNOSTIC_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_CHAIN_EVENT_TYPES = {
    "amendment_drafted",
    "amendment_frozen",
    "administrative_hold_resumed",
}
_AUDIT_EVENT_TYPES = {
    "audit_genesis",
    "diagnostic_backfill_reserved",
    "diagnostic_backfill_recorded",
}


@dataclasses.dataclass(frozen=True)
class IntegrationBoundary:
    integration_manifest_path: str
    diagnostic_engine_file_paths: tuple[str, ...]
    amended_orchestrator_file_paths: tuple[str, ...]
    development_target_filename: str
    required_private_artifact_names: tuple[str, ...]
    state_schema: str
    effective_deadline_field: str
    edit_adapter_api: str
    read_adapter_api: str


CURRENT_INTEGRATION_BOUNDARY = IntegrationBoundary(
    integration_manifest_path=INTEGRATION_MANIFEST_PATH,
    diagnostic_engine_file_paths=DIAGNOSTIC_ENGINE_FILE_PATHS,
    amended_orchestrator_file_paths=AMENDED_ORCHESTRATOR_FILE_PATHS,
    development_target_filename=DEVELOPMENT_TARGET_FILENAME,
    required_private_artifact_names=REQUIRED_PRIVATE_ARTIFACT_NAMES,
    state_schema=AMENDMENT_STATE_SCHEMA_ID,
    effective_deadline_field="administrative_hold.effective_research_deadline_utc",
    edit_adapter_api="amendment_aware_legacy_state_edit",
    read_adapter_api="read_amendment_aware_legacy_state",
)


def _require_integration_ready(state: Mapping[str, Any], operation: str) -> None:
    amendment = state.get("amendment")
    if (
        not isinstance(amendment, Mapping)
        or amendment.get("status") != "frozen"
        or amendment.get("lifecycle_status") != FROZEN_LIFECYCLE_STATUS
        or amendment.get("score_calculation_implemented") is not True
        or not isinstance(amendment.get("integration_manifest_sha256"), str)
    ):
        raise ValueError(
            f"{operation} requires the reviewed, hash-bound diagnostic-engine and "
            "amended-orchestrator integration freeze"
        )


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(payload: object) -> bytes:
    return json.dumps(payload, allow_nan=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _record_sha256(record: Mapping[str, Any]) -> str:
    unsigned = {key: value for key, value in record.items() if key != "record_sha256"}
    return _sha256_bytes(_canonical_json_bytes(unsigned))


def _journal_line(record: Mapping[str, Any]) -> bytes:
    return _canonical_json_bytes(record) + b"\n"


def _exact_object(raw: Any, keys: set[str] | frozenset[str], label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping) or set(raw) != set(keys):
        missing = sorted(set(keys) - set(raw)) if isinstance(raw, Mapping) else sorted(keys)
        extra = sorted(set(raw) - set(keys)) if isinstance(raw, Mapping) else []
        raise ValueError(f"{label} has invalid keys; missing={missing}, extra={extra}")
    return raw


def _sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be 64 lowercase hexadecimal characters")
    return value


def _integer(value: object, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def _finite_nonnegative(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{label} must be finite and nonnegative")
    return result


def _nonempty(value: object, label: str, *, maximum: int = 2000) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > maximum
    ):
        raise ValueError(f"{label} must be a trimmed nonempty string <= {maximum} chars")
    return value


def _utc(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO-8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"{label} must be timezone-aware UTC")
    return parsed.astimezone(UTC)


def _utc_text(value: object, label: str) -> str:
    return _utc(value, label).isoformat().replace("+00:00", "Z")


def _duration_microseconds(start: datetime, end: datetime) -> int:
    if end < start:
        raise ValueError("hold resume time cannot precede hold start")
    delta = end - start
    return delta.days * 86_400_000_000 + delta.seconds * 1_000_000 + delta.microseconds


def _strict_json_bytes(payload: bytes, label: str) -> Mapping[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"{label} contains non-finite JSON number {value}")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{label} contains duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        raw = json.loads(
            payload.decode("utf-8"),
            parse_constant=reject_constant,
            object_pairs_hook=unique_object,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid {label}: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError(f"{label} root must be a JSON object")
    return raw


def read_json_file(path: str | Path, label: str) -> tuple[Mapping[str, Any], bytes]:
    source = Path(path)
    try:
        payload = source.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read {label}: {exc}") from exc
    return _strict_json_bytes(payload, label), payload


def _safe_relative(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a repository-relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{label} must be a safe repository-relative path")
    normalized = path.as_posix()
    if normalized != value:
        raise ValueError(f"{label} must be canonical")
    return normalized


def _safe_file(root: Path, relative: object, label: str) -> tuple[str, Path]:
    normalized = _safe_relative(relative, label)
    current = root
    for part in PurePosixPath(normalized).parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"{label} contains a symlink component")
    resolved = current.resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError(f"{label} is missing or unsafe")
    return normalized, resolved


_Change = TransactionChange


def _publish_transaction(root: Path, changes: Sequence[_Change]) -> None:
    """Publish through the recoverable Git-path transaction intent."""

    publish_transaction(root, changes)


def _state_lock_path(root: Path) -> Path:
    return git_path(root, "top40-v2-run-state.lock")


@contextmanager
def _state_lock(root: Path) -> Iterator[None]:
    path = _state_lock_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(
            path,
            os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
            0o600,
        )
    except OSError as exc:
        raise ValueError(f"state lock is missing or unsafe: {exc}") from exc
    info = os.fstat(descriptor)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.geteuid():
        os.close(descriptor)
        raise ValueError("state lock must be an organizer-owned single-link regular file")
    with os.fdopen(descriptor, "a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        recover_transaction(root)
        yield


@contextmanager
def _diagnostic_execution_lock(root: Path, diagnostic_id: str) -> Iterator[None]:
    """Serialize one diagnostic across its unlocked, long-running replay section."""

    if _DIAGNOSTIC_ID.fullmatch(diagnostic_id) is None:
        raise ValueError("diagnostic_id must be lowercase safe text of at most 128 chars")
    directory = git_path(root, DIAGNOSTIC_LOCK_GIT_ROOT)
    ensure_owner_directory(directory.parent)
    ensure_owner_directory(directory)
    path = directory / f"{diagnostic_id}.lock"
    try:
        descriptor = os.open(
            path,
            os.O_RDWR
            | os.O_CREAT
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
            0o600,
        )
    except OSError as exc:
        raise ValueError(f"diagnostic execution lock is missing or unsafe: {exc}") from exc
    info = os.fstat(descriptor)
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) != 0o600
    ):
        os.close(descriptor)
        raise ValueError("diagnostic execution lock must be owner-only and single-linked")
    with os.fdopen(descriptor, "a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield


def _research_policy(config: LoadedV2Config) -> ResearchPolicy:
    budget = config.raw["research_budget"]
    return ResearchPolicy(
        tournament_id=TOP40_V2_LAYOUT.name,
        team_ids=TEAM_IDS,
        maximum_material_configurations_per_team=int(
            budget["maximum_material_configurations_per_team"]
        ),
        maximum_cpu_hours_per_team=float(budget["maximum_cpu_hours_per_team"]),
        maximum_wall_clock_hours_per_team=float(budget["maximum_wall_clock_hours_per_team"]),
    )


def _legacy_projection(state: Mapping[str, Any]) -> dict[str, Any]:
    projection = {key: copy.deepcopy(state[key]) for key in LEGACY_STATE_KEYS}
    projection["schema_version"] = 2
    return projection


def _binding(
    *, path: str, genesis_sha256: str, head_sha256: str, record_count: int
) -> dict[str, object]:
    return {
        "path": path,
        "genesis_sha256": genesis_sha256,
        "head_sha256": head_sha256,
        "record_count": record_count,
    }


@dataclasses.dataclass(frozen=True)
class AmendmentChainState:
    records: tuple[Mapping[str, Any], ...]
    genesis_sha256: str
    head_sha256: str

    @property
    def binding(self) -> dict[str, object]:
        return _binding(
            path=AMENDMENT_CHAIN_PATH,
            genesis_sha256=self.genesis_sha256,
            head_sha256=self.head_sha256,
            record_count=len(self.records),
        )


@dataclasses.dataclass(frozen=True)
class OrganizerAuditState:
    records: tuple[Mapping[str, Any], ...]
    genesis_sha256: str
    head_sha256: str
    reservations: Mapping[str, Mapping[str, Any]]
    results: Mapping[str, Mapping[str, Any]]
    organizer_cpu_hours: float
    organizer_wall_clock_hours: float

    @property
    def binding(self) -> dict[str, object]:
        return {
            **_binding(
                path=ORGANIZER_AUDIT_PATH,
                genesis_sha256=self.genesis_sha256,
                head_sha256=self.head_sha256,
                record_count=len(self.records),
            ),
            "reservation_count": len(self.reservations),
            "result_count": len(self.results),
            "organizer_cpu_hours": self.organizer_cpu_hours,
            "organizer_wall_clock_hours": self.organizer_wall_clock_hours,
        }


def _journal_records(payload: bytes, label: str) -> list[Mapping[str, Any]]:
    if not payload or not payload.endswith(b"\n"):
        raise ValueError(f"{label} must be nonempty canonical JSONL ending in a newline")
    records: list[Mapping[str, Any]] = []
    for index, line in enumerate(payload.splitlines(), start=1):
        if not line:
            raise ValueError(f"{label} contains an empty line")
        raw = _strict_json_bytes(line, f"{label} line {index}")
        if _journal_line(raw) != line + b"\n":
            raise ValueError(f"{label} line {index} is not canonical JSONL")
        records.append(raw)
    return records


def _validate_envelope(
    record: Mapping[str, Any],
    *,
    index: int,
    previous_sha256: str | None,
    journal_key: str,
    journal_id: str,
    event_types: set[str],
    label: str,
) -> tuple[str, datetime, Mapping[str, Any]]:
    _exact_object(
        record,
        {
            "schema_version",
            journal_key,
            "sequence",
            "event_type",
            "timestamp_utc",
            "previous_record_sha256",
            "amendment_id",
            "payload",
            "record_sha256",
        },
        f"{label} record {index}",
    )
    if (
        record["schema_version"] != 1
        or record[journal_key] != journal_id
        or record["sequence"] != index
        or record["event_type"] not in event_types
        or record["amendment_id"] != AMENDMENT_ID
        or record["previous_record_sha256"] != previous_sha256
    ):
        raise ValueError(f"{label} record {index} envelope is invalid")
    observed_sha = _sha256(record["record_sha256"], f"{label} record_sha256")
    if observed_sha != _record_sha256(record):
        raise ValueError(f"{label} record {index} hash is invalid")
    timestamp = _utc(record["timestamp_utc"], f"{label} timestamp")
    payload = record["payload"]
    if not isinstance(payload, Mapping):
        raise ValueError(f"{label} record {index} payload must be an object")
    return observed_sha, timestamp, payload


def validate_amendment_chain_bytes(payload: bytes) -> AmendmentChainState:
    records = _journal_records(payload, "amendment chain")
    if not records:
        raise ValueError("amendment chain requires a draft genesis")
    previous: str | None = None
    previous_time: datetime | None = None
    seen_types: list[str] = []
    for index, record in enumerate(records, start=1):
        observed_sha, timestamp, body = _validate_envelope(
            record,
            index=index,
            previous_sha256=previous,
            journal_key="chain_id",
            journal_id=AMENDMENT_CHAIN_ID,
            event_types=_CHAIN_EVENT_TYPES,
            label="amendment chain",
        )
        if previous_time is not None and timestamp < previous_time:
            raise ValueError("amendment chain timestamps must be monotonic")
        event_type = str(record["event_type"])
        if event_type == "amendment_drafted":
            _exact_object(
                body,
                {
                    "phase0_freeze_sha256",
                    "draft_path",
                    "draft_sha256",
                    "hold_notice_sha256",
                    "hold_notice_commit",
                    "legacy_projection_sha256",
                    "hold_started_at_utc",
                    "hold_reason",
                },
                "amendment draft chain payload",
            )
            if index != 1 or body["draft_path"] != AMENDMENT_DRAFT_PATH:
                raise ValueError("amendment draft must be the chain genesis")
            _sha256(body["phase0_freeze_sha256"], "chain phase0_freeze_sha256")
            _sha256(body["draft_sha256"], "chain draft_sha256")
            _sha256(body["hold_notice_sha256"], "chain hold_notice_sha256")
            _sha256(body["legacy_projection_sha256"], "chain legacy_projection_sha256")
            if (
                not isinstance(body["hold_notice_commit"], str)
                or _COMMIT.fullmatch(body["hold_notice_commit"]) is None
            ):
                raise ValueError("chain hold_notice_commit is invalid")
            _utc(body["hold_started_at_utc"], "chain hold_started_at_utc")
            _nonempty(body["hold_reason"], "chain hold_reason")
        elif event_type == "amendment_frozen":
            _exact_object(
                body,
                {
                    "draft_sha256",
                    "freeze_path",
                    "freeze_sha256",
                    "amendment_commit",
                    "review_sha256",
                    "integration_manifest_sha256",
                    "score_calculation_implemented",
                },
                "amendment freeze chain payload",
            )
            if seen_types != ["amendment_drafted"]:
                raise ValueError("amendment freeze must directly follow its draft")
            _sha256(body["draft_sha256"], "chain draft_sha256")
            _sha256(body["freeze_sha256"], "chain freeze_sha256")
            _sha256(body["review_sha256"], "chain review_sha256")
            _sha256(
                body["integration_manifest_sha256"],
                "chain integration_manifest_sha256",
            )
            if (
                body["freeze_path"] != AMENDMENT_FREEZE_PATH
                or not isinstance(body["amendment_commit"], str)
                or _COMMIT.fullmatch(body["amendment_commit"]) is None
                or body["score_calculation_implemented"] is not True
            ):
                raise ValueError("amendment freeze chain binding is invalid")
        else:
            _exact_object(
                body,
                {
                    "freeze_sha256",
                    "hold_duration_microseconds",
                    "effective_research_deadline_utc",
                },
                "hold resume chain payload",
            )
            if seen_types != ["amendment_drafted", "amendment_frozen"]:
                raise ValueError("hold resume must directly follow the amendment freeze")
            _sha256(body["freeze_sha256"], "resume freeze_sha256")
            _integer(
                body["hold_duration_microseconds"],
                "hold_duration_microseconds",
                minimum=1,
            )
            _utc(body["effective_research_deadline_utc"], "effective deadline")
        seen_types.append(event_type)
        previous = observed_sha
        previous_time = timestamp
    if seen_types not in (
        ["amendment_drafted"],
        ["amendment_drafted", "amendment_frozen"],
        ["amendment_drafted", "amendment_frozen", "administrative_hold_resumed"],
    ):
        raise ValueError("amendment chain lifecycle is invalid")
    return AmendmentChainState(tuple(records), str(records[0]["record_sha256"]), str(previous))


def validate_organizer_audit_bytes(payload: bytes) -> OrganizerAuditState:
    records = _journal_records(payload, "organizer audit journal")
    if not records:
        raise ValueError("organizer audit journal requires a genesis")
    previous: str | None = None
    previous_time: datetime | None = None
    reservations: dict[str, Mapping[str, Any]] = {}
    reservation_keys: set[str] = set()
    results: dict[str, Mapping[str, Any]] = {}
    cpu_values: list[float] = []
    wall_values: list[float] = []
    for index, record in enumerate(records, start=1):
        observed_sha, timestamp, body = _validate_envelope(
            record,
            index=index,
            previous_sha256=previous,
            journal_key="journal_id",
            journal_id=ORGANIZER_AUDIT_ID,
            event_types=_AUDIT_EVENT_TYPES,
            label="organizer audit journal",
        )
        if previous_time is not None and timestamp < previous_time:
            raise ValueError("organizer audit timestamps must be monotonic")
        event_type = record["event_type"]
        if event_type == "audit_genesis":
            _exact_object(
                body,
                {
                    "phase0_freeze_sha256",
                    "draft_sha256",
                    "hold_notice_sha256",
                    "non_material_diagnostics_only",
                    "charges_team_trial_budget",
                },
                "organizer audit genesis payload",
            )
            if (
                index != 1
                or body["non_material_diagnostics_only"] is not True
                or body["charges_team_trial_budget"] is not False
            ):
                raise ValueError("organizer audit genesis contract is invalid")
            _sha256(body["phase0_freeze_sha256"], "audit phase0_freeze_sha256")
            _sha256(body["draft_sha256"], "audit draft_sha256")
            _sha256(body["hold_notice_sha256"], "audit hold_notice_sha256")
        elif event_type == "diagnostic_backfill_reserved":
            _validate_reservation_payload(body)
            diagnostic_id = str(body["diagnostic_id"])
            reservation_key = str(body["reservation_key_sha256"])
            if diagnostic_id in reservations or reservation_key in reservation_keys:
                raise ValueError("diagnostic backfill reservation is not one-shot")
            reservations[diagnostic_id] = record
            reservation_keys.add(reservation_key)
        else:
            _validate_result_payload(body)
            diagnostic_id = str(body["diagnostic_id"])
            reservation = reservations.get(diagnostic_id)
            if reservation is None or diagnostic_id in results:
                raise ValueError("diagnostic result lacks one unused reservation")
            if body["reservation_sha256"] != reservation["record_sha256"]:
                raise ValueError("diagnostic result reservation hash differs")
            results[diagnostic_id] = record
            cpu_values.append(float(body["organizer_cpu_hours"]))
            wall_values.append(float(body["organizer_wall_clock_hours"]))
        previous = observed_sha
        previous_time = timestamp
    if records[0]["event_type"] != "audit_genesis":
        raise ValueError("organizer audit genesis must be first")
    return OrganizerAuditState(
        records=tuple(records),
        genesis_sha256=str(records[0]["record_sha256"]),
        head_sha256=str(previous),
        reservations=reservations,
        results=results,
        organizer_cpu_hours=round(math.fsum(cpu_values), 12),
        organizer_wall_clock_hours=round(math.fsum(wall_values), 12),
    )


def _validate_reservation_payload(body: Mapping[str, Any]) -> None:
    _exact_object(
        body,
        {
            "diagnostic_id",
            "diagnostic_kind",
            "team_id",
            "candidate_id",
            "candidate_registration_sha256",
            "strategy_sha256",
            "source_bundle_sha256",
            "risk_policy_sha256",
            "config_sha256",
            "candidate_seed",
            "runner_seed",
            "snapshot_manifest_path",
            "snapshot_manifest_sha256",
            "trial_result_record_sha256",
            "development_target_path",
            "development_target_sha256",
            "runner_record_path",
            "runner_record_sha256",
            "amendment_freeze_sha256",
            "reservation_key_sha256",
            "non_material",
            "charges_team_trial_budget",
        },
        "diagnostic reservation payload",
    )
    if (
        not isinstance(body["diagnostic_id"], str)
        or _DIAGNOSTIC_ID.fullmatch(body["diagnostic_id"]) is None
        or body["diagnostic_kind"] != DIAGNOSTIC_KIND
        or body["team_id"] not in TEAM_IDS
        or not isinstance(body["candidate_id"], str)
        or not body["candidate_id"]
        or body["non_material"] is not True
        or body["charges_team_trial_budget"] is not False
    ):
        raise ValueError("diagnostic reservation identity or accounting is invalid")
    for field in (
        "candidate_registration_sha256",
        "strategy_sha256",
        "source_bundle_sha256",
        "risk_policy_sha256",
        "config_sha256",
        "snapshot_manifest_sha256",
        "trial_result_record_sha256",
        "development_target_sha256",
        "runner_record_sha256",
        "amendment_freeze_sha256",
        "reservation_key_sha256",
    ):
        _sha256(body[field], f"diagnostic reservation {field}")
    _integer(body["candidate_seed"], "candidate_seed")
    _integer(body["runner_seed"], "runner_seed")
    _safe_relative(body["snapshot_manifest_path"], "snapshot_manifest_path")
    _safe_relative(body["development_target_path"], "development_target_path")
    _safe_relative(body["runner_record_path"], "runner_record_path")
    identity = {
        "diagnostic_kind": body["diagnostic_kind"],
        "team_id": body["team_id"],
        "candidate_id": body["candidate_id"],
        "amendment_freeze_sha256": body["amendment_freeze_sha256"],
    }
    if body["reservation_key_sha256"] != _sha256_bytes(_canonical_json_bytes(identity)):
        raise ValueError("diagnostic reservation one-shot key is invalid")


def _validate_result_payload(body: Mapping[str, Any]) -> None:
    _exact_object(
        body,
        {
            "diagnostic_id",
            "reservation_sha256",
            "status",
            "failure_reason",
            "artifact_hashes",
            "diagnostic_outcomes",
            "organizer_cpu_hours",
            "organizer_wall_clock_hours",
            "non_material",
            "team_material_trial_delta",
            "team_cpu_hours_delta",
            "team_wall_clock_hours_delta",
        },
        "diagnostic result payload",
    )
    if (
        not isinstance(body["diagnostic_id"], str)
        or _DIAGNOSTIC_ID.fullmatch(body["diagnostic_id"]) is None
        or body["status"] not in {"completed", "failed", "interrupted"}
        or body["non_material"] is not True
        or isinstance(body["team_material_trial_delta"], bool)
        or not isinstance(body["team_material_trial_delta"], (int, float))
        or float(body["team_material_trial_delta"]) != 0.0
        or isinstance(body["team_cpu_hours_delta"], bool)
        or not isinstance(body["team_cpu_hours_delta"], (int, float))
        or float(body["team_cpu_hours_delta"]) != 0.0
        or isinstance(body["team_wall_clock_hours_delta"], bool)
        or not isinstance(body["team_wall_clock_hours_delta"], (int, float))
        or float(body["team_wall_clock_hours_delta"]) != 0.0
    ):
        raise ValueError("diagnostic result status or budget accounting is invalid")
    _sha256(body["reservation_sha256"], "diagnostic reservation_sha256")
    _finite_nonnegative(body["organizer_cpu_hours"], "organizer_cpu_hours")
    _finite_nonnegative(body["organizer_wall_clock_hours"], "organizer_wall_clock_hours")
    artifacts = body["artifact_hashes"]
    if not isinstance(artifacts, Mapping):
        raise ValueError("diagnostic artifact_hashes must be a mapping")
    if body["status"] == "completed" and set(artifacts) != set(
        REQUIRED_PRIVATE_ARTIFACT_NAMES
    ):
        raise ValueError("completed diagnostic must bind the exact six private artifacts")
    for logical_name, digest in artifacts.items():
        if not isinstance(logical_name, str) or _DIAGNOSTIC_ID.fullmatch(logical_name) is None:
            raise ValueError("diagnostic artifact key must be an exact logical name")
        _sha256(digest, "diagnostic artifact sha256")
    failure = body["failure_reason"]
    if body["status"] == "completed":
        if failure is not None or not artifacts:
            raise ValueError("completed diagnostics require artifacts and no failure reason")
        outcomes = _exact_object(
            body["diagnostic_outcomes"],
            set(DIAGNOSTIC_OUTCOME_FIELDS),
            "diagnostic public outcomes",
        )
        if any(type(value) is not bool for value in outcomes.values()):
            raise ValueError("diagnostic public outcomes must be derived booleans")
    elif (
        not isinstance(failure, str)
        or not failure.strip()
        or failure != failure.strip()
        or len(failure) > 8000
        or artifacts
        or body["diagnostic_outcomes"] is not None
    ):
        raise ValueError(
            "failed/interrupted diagnostics require a failure reason and no artifacts/outcomes"
        )


def _new_envelope(
    *,
    journal_key: str,
    journal_id: str,
    sequence: int,
    event_type: str,
    timestamp_utc: str,
    previous_record_sha256: str | None,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema_version": 1,
        journal_key: journal_id,
        "sequence": sequence,
        "event_type": event_type,
        "timestamp_utc": _utc_text(timestamp_utc, "event timestamp"),
        "previous_record_sha256": previous_record_sha256,
        "amendment_id": AMENDMENT_ID,
        "payload": dict(payload),
    }
    record["record_sha256"] = _record_sha256(record)
    return record


def _append_chain(
    current: bytes,
    *,
    event_type: str,
    timestamp_utc: str,
    payload: Mapping[str, Any],
) -> tuple[bytes, AmendmentChainState, Mapping[str, Any]]:
    state = validate_amendment_chain_bytes(current)
    record = _new_envelope(
        journal_key="chain_id",
        journal_id=AMENDMENT_CHAIN_ID,
        sequence=len(state.records) + 1,
        event_type=event_type,
        timestamp_utc=timestamp_utc,
        previous_record_sha256=state.head_sha256,
        payload=payload,
    )
    replacement = current + _journal_line(record)
    return replacement, validate_amendment_chain_bytes(replacement), record


def _append_audit(
    current: bytes,
    *,
    event_type: str,
    timestamp_utc: str,
    payload: Mapping[str, Any],
) -> tuple[bytes, OrganizerAuditState, Mapping[str, Any]]:
    state = validate_organizer_audit_bytes(current)
    record = _new_envelope(
        journal_key="journal_id",
        journal_id=ORGANIZER_AUDIT_ID,
        sequence=len(state.records) + 1,
        event_type=event_type,
        timestamp_utc=timestamp_utc,
        previous_record_sha256=state.head_sha256,
        payload=payload,
    )
    replacement = current + _journal_line(record)
    return replacement, validate_organizer_audit_bytes(replacement), record


def validate_amended_run_state(state: Mapping[str, Any], config: LoadedV2Config) -> None:
    if set(state) != AMENDMENT_STATE_KEYS:
        missing = sorted(AMENDMENT_STATE_KEYS - set(state))
        extra = sorted(set(state) - AMENDMENT_STATE_KEYS)
        raise ValueError(
            f"amendment-aware run state has invalid keys; missing={missing}, extra={extra}"
        )
    if (
        state.get("schema_version") != AMENDMENT_STATE_SCHEMA_VERSION
        or state.get("state_schema") != AMENDMENT_STATE_SCHEMA_ID
    ):
        raise ValueError("amendment-aware run state has an invalid or mixed schema version")
    _sha256(state.get("legacy_state_sha256"), "legacy_state_sha256")
    projection = _legacy_projection(state)
    validate_run_state(projection, config)
    projection_sha = _sha256_bytes(_json_bytes(projection))
    if state.get("legacy_projection_sha256") != projection_sha:
        raise ValueError("legacy projection changed without an exact current SHA-256 update")

    amendment = _exact_object(
        state["amendment"],
        {
            "amendment_id",
            "status",
            "lifecycle_status",
            "phase0_freeze_path",
            "phase0_freeze_sha256",
            "phase0_common_commit",
            "phase0_record_commit",
            "implementation_commit",
            "baseline_research_journal",
            "hold_notice_path",
            "hold_notice_sha256",
            "hold_notice_commit",
            "draft_path",
            "draft_sha256",
            "review_path",
            "review_sha256",
            "review_commit",
            "freeze_path",
            "freeze_sha256",
            "integration_manifest_path",
            "integration_manifest_sha256",
            "score_calculation_implemented",
            "chain",
        },
        "run-state amendment binding",
    )
    if (
        amendment["amendment_id"] != AMENDMENT_ID
        or amendment["status"] not in {"draft", "frozen"}
        or amendment["phase0_freeze_path"] != TOP40_V2_LAYOUT.phase0_freeze_path
        or amendment["hold_notice_path"] != HOLD_NOTICE_PATH
        or amendment["draft_path"] != AMENDMENT_DRAFT_PATH
        or amendment["review_path"] != AMENDMENT_REVIEW_PATH
        or amendment["integration_manifest_path"] != INTEGRATION_MANIFEST_PATH
        or amendment["score_calculation_implemented"] is not True
    ):
        raise ValueError("run-state amendment identity is invalid")
    _validate_baseline_research_binding(amendment["baseline_research_journal"])
    _sha256(amendment["phase0_freeze_sha256"], "amendment phase0_freeze_sha256")
    _sha256(amendment["draft_sha256"], "amendment draft_sha256")
    _sha256(amendment["hold_notice_sha256"], "amendment hold_notice_sha256")
    for field in (
        "phase0_common_commit",
        "phase0_record_commit",
        "implementation_commit",
        "hold_notice_commit",
    ):
        if not isinstance(amendment[field], str) or _COMMIT.fullmatch(amendment[field]) is None:
            raise ValueError(f"amendment {field} is invalid")
    if amendment["status"] == "draft":
        if (
            amendment["lifecycle_status"] != DRAFT_LIFECYCLE_STATUS
            or amendment["review_sha256"] is not None
            or amendment["review_commit"] is not None
            or amendment["freeze_path"] is not None
            or amendment["freeze_sha256"] is not None
            or amendment["integration_manifest_sha256"] is not None
        ):
            raise ValueError("draft amendment cannot claim a freeze")
    elif (
        amendment["lifecycle_status"] != FROZEN_LIFECYCLE_STATUS
        or amendment["freeze_path"] != AMENDMENT_FREEZE_PATH
        or not isinstance(amendment["freeze_sha256"], str)
        or _SHA256.fullmatch(amendment["freeze_sha256"]) is None
        or not isinstance(amendment["review_sha256"], str)
        or _SHA256.fullmatch(amendment["review_sha256"]) is None
        or not isinstance(amendment["review_commit"], str)
        or _COMMIT.fullmatch(amendment["review_commit"]) is None
        or not isinstance(amendment["integration_manifest_sha256"], str)
        or _SHA256.fullmatch(amendment["integration_manifest_sha256"]) is None
    ):
        raise ValueError("frozen amendment lacks exact review/freeze/integration bindings")
    _validate_journal_binding(amendment["chain"], AMENDMENT_CHAIN_PATH, "amendment chain")

    hold = _exact_object(
        state["administrative_hold"],
        {
            "active",
            "started_at_utc",
            "reason",
            "resumed_at_utc",
            "hold_duration_microseconds",
            "cumulative_toll_microseconds",
            "baseline_research_deadline_utc",
            "effective_research_deadline_utc",
        },
        "administrative hold",
    )
    if not isinstance(hold["active"], bool):
        raise ValueError("administrative hold active must be boolean")
    started = _utc(hold["started_at_utc"], "hold started_at_utc")
    _nonempty(hold["reason"], "hold reason")
    baseline_text = _utc_text(
        config.raw["research_budget"]["deadline_utc"], "config research deadline"
    )
    if hold["baseline_research_deadline_utc"] != baseline_text:
        raise ValueError("hold baseline deadline differs from the frozen config")
    cumulative = _integer(hold["cumulative_toll_microseconds"], "cumulative_toll_microseconds")
    expected_deadline = (
        (_utc(baseline_text, "baseline deadline") + timedelta(microseconds=cumulative))
        .isoformat()
        .replace("+00:00", "Z")
    )
    if hold["effective_research_deadline_utc"] != expected_deadline:
        raise ValueError("effective deadline does not equal the exact hold toll")
    if hold["active"]:
        if (
            hold["resumed_at_utc"] is not None
            or hold["hold_duration_microseconds"] is not None
            or cumulative != 0
        ):
            raise ValueError("active amendment hold has premature resume/toll fields")
        if projection_sha != state["legacy_state_sha256"]:
            raise ValueError("legacy projection mutated during the administrative hold")
        baseline_journal = amendment["baseline_research_journal"]
        current_journal = state["research_journal"]
        expected_current = {
            key: baseline_journal[key]
            for key in ("path", "genesis_sha256", "head_sha256", "record_count")
        }
        if current_journal != expected_current:
            raise ValueError("research journal advanced during the administrative hold")
    else:
        resumed = _utc(hold["resumed_at_utc"], "hold resumed_at_utc")
        duration = _integer(
            hold["hold_duration_microseconds"],
            "hold_duration_microseconds",
            minimum=1,
        )
        if duration != _duration_microseconds(started, resumed) or cumulative != duration:
            raise ValueError("hold duration/toll differs from exact start-to-resume time")
        if amendment["status"] != "frozen":
            raise ValueError("an amendment hold can resume only after freeze")

    audit = state["organizer_audit"]
    _validate_journal_binding(
        audit,
        ORGANIZER_AUDIT_PATH,
        "organizer audit",
        extra={
            "reservation_count",
            "result_count",
            "organizer_cpu_hours",
            "organizer_wall_clock_hours",
        },
    )
    if not isinstance(audit, Mapping):  # pragma: no cover - helper already rejects
        raise ValueError("organizer audit binding is malformed")
    _integer(audit["reservation_count"], "organizer audit reservation_count")
    _integer(audit["result_count"], "organizer audit result_count")
    _finite_nonnegative(audit["organizer_cpu_hours"], "organizer audit CPU hours")
    _finite_nonnegative(audit["organizer_wall_clock_hours"], "organizer audit wall hours")


def _validate_journal_binding(
    raw: object,
    expected_path: str,
    label: str,
    *,
    extra: set[str] | None = None,
) -> None:
    keys = {"path", "genesis_sha256", "head_sha256", "record_count"} | (extra or set())
    binding = _exact_object(raw, keys, f"{label} binding")
    if binding["path"] != expected_path:
        raise ValueError(f"{label} path is noncanonical")
    _sha256(binding["genesis_sha256"], f"{label} genesis_sha256")
    _sha256(binding["head_sha256"], f"{label} head_sha256")
    _integer(binding["record_count"], f"{label} record_count", minimum=1)


def _validate_baseline_research_binding(raw: object) -> None:
    binding = _exact_object(
        raw,
        {
            "path",
            "genesis_sha256",
            "head_sha256",
            "record_count",
            "latest_timestamp_utc",
        },
        "baseline research journal binding",
    )
    if binding["path"] != TOP40_V2_LAYOUT.organizer_journal_path:
        raise ValueError("baseline research journal path is noncanonical")
    _sha256(binding["genesis_sha256"], "baseline research journal genesis")
    _sha256(binding["head_sha256"], "baseline research journal head")
    _integer(binding["record_count"], "baseline research journal record_count", minimum=1)
    _utc(binding["latest_timestamp_utc"], "baseline research journal latest timestamp")


def _validate_baseline_research_prefix(
    research: JournalState,
    baseline_research: Mapping[str, Any],
) -> None:
    """Require every current journal to retain the exact activation-time prefix."""

    _validate_baseline_research_binding(baseline_research)
    baseline_count = int(baseline_research["record_count"])
    if (
        research.genesis_sha256 != baseline_research["genesis_sha256"]
        or len(research.records) < baseline_count
        or research.records[baseline_count - 1]["record_sha256"]
        != baseline_research["head_sha256"]
        or research.records[baseline_count - 1]["timestamp_utc"]
        != baseline_research["latest_timestamp_utc"]
    ):
        raise ValueError("current research journal is not an exact extension of the hold baseline")


def _phase0_record(
    root: Path,
    state: Mapping[str, Any],
    config: LoadedV2Config,
    *,
    clock: UtcClock = system_utc_now,
) -> Mapping[str, Any]:
    return _phase0_authority(root, state, config, clock=clock).freeze


def _phase0_authority(
    root: Path,
    state: Mapping[str, Any],
    config: LoadedV2Config,
    *,
    clock: UtcClock = system_utc_now,
) -> Phase0Authority:
    return verify_phase0_authority(
        root,
        state,
        config,
        PHASE0_FROZEN_FILES,
        clock=clock,
    )


def _amendment_file_hashes(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in AMENDMENT_FILE_PATHS:
        normalized, _path, payload, _stat = read_repo_file(
            root,
            relative,
            f"amendment file {relative}",
        )
        if normalized != relative:
            raise ValueError(f"amendment file path is noncanonical: {relative}")
        result[relative] = _sha256_bytes(payload)
    return result


def _committed_amendment_files(
    root: Path,
    expected: Mapping[str, str],
    authority: Phase0Authority,
    *,
    clock: UtcClock = system_utc_now,
) -> str:
    if set(expected) != set(AMENDMENT_FILE_PATHS):
        raise ValueError("amendment implementation manifest is incomplete or unexpected")
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", *AMENDMENT_FILE_PATHS],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if status.returncode or status.stdout.strip():
        raise ValueError("commit every reviewed amendment file before freezing amendment 0001")
    branch = git_text(root, "branch", "--show-current", label="amendment branch")
    if branch != TOP40_V2_LAYOUT.branch:
        raise ValueError(f"amendment branch must be {TOP40_V2_LAYOUT.branch}")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    commit = head.stdout.strip()
    if head.returncode or _COMMIT.fullmatch(commit) is None:
        raise ValueError("amendment freeze requires a full committed Git HEAD")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", authority.record_commit, commit],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if ancestry.returncode:
        raise ValueError("amendment commit must descend from the Phase-0 record commit")
    first_add_commits: set[str] = set()
    for relative, digest in expected.items():
        shown = subprocess.run(
            ["git", "show", f"{commit}:{relative}"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if shown.returncode or _sha256_bytes(shown.stdout) != digest:
            raise ValueError(f"amendment file is not committed at HEAD: {relative}")
        first_add_commits.add(unique_first_add_commit(root, relative, shown.stdout))
    if len(first_add_commits) != 1:
        raise ValueError("all amendment implementation files must share one first-add commit")
    implementation_commit = next(iter(first_add_commits))
    if implementation_commit != commit:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", implementation_commit, commit],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if ancestor.returncode:
            raise ValueError("amendment implementation commit is not an ancestor of HEAD")
    implementation_time = git_commit_time(
        root,
        implementation_commit,
        "amendment implementation commit time",
    )
    if implementation_time < _utc(authority.record_commit_time_utc, "Phase-0 record commit time"):
        raise ValueError("amendment implementation commit predates the Phase-0 record")
    if implementation_time > trusted_now(clock):
        raise ValueError("amendment implementation commit cannot be future-dated")
    head_time = git_commit_time(root, commit, "amendment Git HEAD time")
    if head_time < implementation_time:
        raise ValueError("amendment Git HEAD predates its implementation ancestor")
    if head_time > trusted_now(clock):
        raise ValueError("amendment Git HEAD cannot be future-dated")
    return implementation_commit


def _validate_draft(raw: Mapping[str, Any]) -> None:
    _exact_object(
        raw,
        {
            "schema_version",
            "amendment_id",
            "status",
            "created_at_utc",
            "phase0_freeze_path",
            "phase0_freeze_sha256",
            "phase0_common_commit",
            "baseline_config_sha256",
            "baseline_legacy_state_sha256",
            "baseline_legacy_projection_sha256",
            "baseline_research_journal",
            "baseline_research_deadline_utc",
            "hold_notice_path",
            "hold_notice_sha256",
            "hold_notice_commit",
            "hold_started_at_utc",
            "hold_reason",
            "implementation_commit",
            "lifecycle_status",
            "integration_manifest_path",
            "integration_ready_for_review",
            "authorized_scope",
            "amendment_files",
            "score_calculation_implemented",
            "claims_frozen",
        },
        "amendment draft",
    )
    if (
        raw["schema_version"] != 1
        or raw["amendment_id"] != AMENDMENT_ID
        or raw["status"] != "draft"
        or raw["phase0_freeze_path"] != TOP40_V2_LAYOUT.phase0_freeze_path
        or raw["hold_notice_path"] != HOLD_NOTICE_PATH
        or raw["lifecycle_status"] != DRAFT_LIFECYCLE_STATUS
        or raw["integration_manifest_path"] != INTEGRATION_MANIFEST_PATH
        or raw["integration_ready_for_review"] is not True
        or raw["score_calculation_implemented"] is not True
        or raw["claims_frozen"] is not False
    ):
        raise ValueError("amendment draft identity or non-frozen status is invalid")
    _utc(raw["created_at_utc"], "draft created_at_utc")
    _utc(raw["hold_started_at_utc"], "draft hold_started_at_utc")
    _utc(raw["baseline_research_deadline_utc"], "draft baseline deadline")
    _validate_baseline_research_binding(raw["baseline_research_journal"])
    _nonempty(raw["hold_reason"], "draft hold reason")
    if not isinstance(raw["authorized_scope"], list) or raw["authorized_scope"] != [
        "global administrative hold with exact research-deadline toll",
        "reviewed score diagnostics with organizer-private numeric artifacts",
        "exact required pre-resume backfills plus post-resume one-shot diagnostics",
        "amendment-aware ordinary orchestration after exact hold toll",
        "no scoring-formula, ranking, qualification, finalist, or result-release change",
    ]:
        raise ValueError("amendment draft scope differs from the narrow authorized scope")
    for field in (
        "phase0_freeze_sha256",
        "baseline_config_sha256",
        "baseline_legacy_state_sha256",
        "baseline_legacy_projection_sha256",
        "hold_notice_sha256",
    ):
        _sha256(raw[field], f"draft {field}")
    for field in ("phase0_common_commit", "hold_notice_commit", "implementation_commit"):
        if not isinstance(raw[field], str) or _COMMIT.fullmatch(raw[field]) is None:
            raise ValueError(f"draft {field} is invalid")
    files = raw["amendment_files"]
    if not isinstance(files, Mapping) or set(files) != set(AMENDMENT_FILE_PATHS):
        raise ValueError("draft amendment-file manifest is incomplete")
    for path, digest in files.items():
        _safe_relative(path, "draft amendment file")
        _sha256(digest, f"draft amendment hash {path}")


def _required_diagnostic_id(team_id: str, candidate_id: str) -> str:
    value = f"score-ic-{team_id}-{candidate_id}"
    if _DIAGNOSTIC_ID.fullmatch(value) is None:
        raise ValueError("required diagnostic identity is not canonical")
    return value


def _required_backfill_bindings(
    root: Path,
    journal: JournalState,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for team_id, candidate_id in REQUIRED_BACKFILL_CANDIDATES:
        accounting = journal.teams[team_id]
        registration = accounting.registrations.get(candidate_id)
        registration_sha = accounting.registration_sha256.get(candidate_id)
        if not isinstance(registration, Mapping) or not isinstance(registration_sha, str):
            raise ValueError(
                f"required backfill candidate is not registered: {team_id}/{candidate_id}"
            )
        development = _canonical_development_bindings(root, journal, team_id, candidate_id)
        rows.append(
            {
                "diagnostic_id": _required_diagnostic_id(team_id, candidate_id),
                "team_id": team_id,
                "candidate_id": candidate_id,
                "candidate_registration_sha256": registration_sha,
                "trial_result_record_sha256": development["trial_result_record_sha256"],
                "strategy_sha256": registration["strategy_sha256"],
                "source_bundle_sha256": registration["source_bundle_sha256"],
                "risk_policy_sha256": registration["risk_config_sha256"],
                "config_sha256": registration["config_sha256"],
                "candidate_seed": registration["seed"],
                "development_target_path": development["development_target_path"],
                "development_target_sha256": development["development_target_sha256"],
                "runner_record_path": development["runner_record_path"],
                "runner_record_sha256": development["runner_record_sha256"],
            }
        )
    _validate_required_backfills(rows)
    return rows


def _validate_required_backfills(raw: object) -> None:
    if not isinstance(raw, list) or not raw:
        raise ValueError("integration requires a nonempty required_backfills list")
    expected_pairs = list(REQUIRED_BACKFILL_CANDIDATES)
    observed_pairs: list[tuple[str, str]] = []
    diagnostic_ids: set[str] = set()
    for index, item in enumerate(raw):
        binding = _exact_object(
            item,
            {
                "diagnostic_id",
                "team_id",
                "candidate_id",
                "candidate_registration_sha256",
                "trial_result_record_sha256",
                "strategy_sha256",
                "source_bundle_sha256",
                "risk_policy_sha256",
                "config_sha256",
                "candidate_seed",
                "development_target_path",
                "development_target_sha256",
                "runner_record_path",
                "runner_record_sha256",
            },
            f"required backfill {index}",
        )
        team_id = str(binding["team_id"])
        candidate_id = str(binding["candidate_id"])
        if team_id not in TEAM_IDS or not candidate_id:
            raise ValueError("required backfill candidate identity is invalid")
        diagnostic_id = str(binding["diagnostic_id"])
        if diagnostic_id != _required_diagnostic_id(team_id, candidate_id):
            raise ValueError("required backfill diagnostic_id is noncanonical")
        if diagnostic_id in diagnostic_ids:
            raise ValueError("required backfill diagnostic_id is duplicated")
        diagnostic_ids.add(diagnostic_id)
        observed_pairs.append((team_id, candidate_id))
        for field in (
            "candidate_registration_sha256",
            "trial_result_record_sha256",
            "strategy_sha256",
            "source_bundle_sha256",
            "risk_policy_sha256",
            "config_sha256",
            "development_target_sha256",
            "runner_record_sha256",
        ):
            _sha256(binding[field], f"required backfill {field}")
        _integer(binding["candidate_seed"], "required backfill candidate_seed")
        _safe_relative(binding["development_target_path"], "required development target")
        _safe_relative(binding["runner_record_path"], "required runner record")
    if observed_pairs != sorted(observed_pairs) or observed_pairs != expected_pairs:
        raise ValueError("required_backfills must be the exact sorted organizer-approved set")


def _integration_manifest(
    *,
    authority: Phase0Authority,
    draft_sha256: str,
    implementation_commit: str,
    amendment_files: Mapping[str, str],
    required_backfills: list[dict[str, Any]],
) -> dict[str, Any]:
    boundary = CURRENT_INTEGRATION_BOUNDARY
    manifest = {
        "schema_version": 1,
        "amendment_id": AMENDMENT_ID,
        "status": "ready_for_review",
        "phase0_freeze_sha256": authority.freeze_sha256,
        "draft_sha256": draft_sha256,
        "implementation_commit": implementation_commit,
        "amendment_files": dict(amendment_files),
        "required_backfills": copy.deepcopy(required_backfills),
        "diagnostic_engine": {
            "files": {
                path: amendment_files[path]
                for path in boundary.diagnostic_engine_file_paths
            },
            "diagnostic_kind": DIAGNOSTIC_KIND,
            "runner_api": "run_reserved_score_diagnostic",
            "development_target_filename": boundary.development_target_filename,
            "required_private_artifact_names": list(
                boundary.required_private_artifact_names
            ),
            "score_calculation_implemented": True,
        },
        "amended_orchestrator": {
            "files": {
                path: amendment_files[path]
                for path in boundary.amended_orchestrator_file_paths
            },
            "state_schema": boundary.state_schema,
            "effective_deadline_field": boundary.effective_deadline_field,
            "edit_adapter_api": boundary.edit_adapter_api,
            "read_adapter_api": boundary.read_adapter_api,
        },
        "score_calculation_implemented": True,
    }
    _validate_integration_manifest(manifest)
    return manifest


def _validate_integration_manifest(raw: Mapping[str, Any]) -> None:
    manifest = _exact_object(
        raw,
        {
            "schema_version",
            "amendment_id",
            "status",
            "phase0_freeze_sha256",
            "draft_sha256",
            "implementation_commit",
            "amendment_files",
            "required_backfills",
            "diagnostic_engine",
            "amended_orchestrator",
            "score_calculation_implemented",
        },
        "integration manifest",
    )
    if (
        manifest["schema_version"] != 1
        or manifest["amendment_id"] != AMENDMENT_ID
        or manifest["status"] != "ready_for_review"
        or manifest["score_calculation_implemented"] is not True
    ):
        raise ValueError("integration manifest identity/readiness is invalid")
    _sha256(manifest["phase0_freeze_sha256"], "integration Phase-0 SHA-256")
    _sha256(manifest["draft_sha256"], "integration draft SHA-256")
    if not isinstance(manifest["implementation_commit"], str) or _COMMIT.fullmatch(
        manifest["implementation_commit"]
    ) is None:
        raise ValueError("integration implementation_commit is invalid")
    files = manifest["amendment_files"]
    if not isinstance(files, Mapping) or set(files) != set(AMENDMENT_FILE_PATHS):
        raise ValueError("integration amendment_files is incomplete")
    for path, digest in files.items():
        _safe_relative(path, "integration amendment path")
        _sha256(digest, f"integration amendment hash {path}")
    _validate_required_backfills(manifest["required_backfills"])
    engine = _exact_object(
        manifest["diagnostic_engine"],
        {
            "files",
            "diagnostic_kind",
            "runner_api",
            "development_target_filename",
            "required_private_artifact_names",
            "score_calculation_implemented",
        },
        "diagnostic engine integration",
    )
    expected_engine_files = {
        path: files[path] for path in DIAGNOSTIC_ENGINE_FILE_PATHS
    }
    if (
        engine["files"] != expected_engine_files
        or engine["diagnostic_kind"] != DIAGNOSTIC_KIND
        or engine["runner_api"] != "run_reserved_score_diagnostic"
        or engine["development_target_filename"] != DEVELOPMENT_TARGET_FILENAME
        or engine["required_private_artifact_names"]
        != list(REQUIRED_PRIVATE_ARTIFACT_NAMES)
        or engine["score_calculation_implemented"] is not True
    ):
        raise ValueError("diagnostic engine integration boundary is invalid")
    orchestrator = _exact_object(
        manifest["amended_orchestrator"],
        {
            "files",
            "state_schema",
            "effective_deadline_field",
            "edit_adapter_api",
            "read_adapter_api",
        },
        "amended orchestrator integration",
    )
    expected_orchestrator_files = {
        path: files[path] for path in AMENDED_ORCHESTRATOR_FILE_PATHS
    }
    if (
        orchestrator["files"] != expected_orchestrator_files
        or orchestrator["state_schema"] != AMENDMENT_STATE_SCHEMA_ID
        or orchestrator["effective_deadline_field"]
        != "administrative_hold.effective_research_deadline_utc"
        or orchestrator["edit_adapter_api"] != "amendment_aware_legacy_state_edit"
        or orchestrator["read_adapter_api"] != "read_amendment_aware_legacy_state"
    ):
        raise ValueError("amended orchestrator integration boundary is invalid")


def _validate_freeze(raw: Mapping[str, Any]) -> None:
    _exact_object(
        raw,
        {
            "schema_version",
            "amendment_id",
            "status",
            "frozen_at_utc",
            "phase0_freeze_path",
            "phase0_freeze_sha256",
            "phase0_common_commit",
            "draft_path",
            "draft_sha256",
            "chain_parent_sha256",
            "amendment_commit",
            "amendment_files",
            "integration_manifest_path",
            "integration_manifest_sha256",
            "required_backfills",
            "review_path",
            "review_commit",
            "review",
            "review_input_sha256",
            "score_calculation_implemented",
        },
        "amendment freeze",
    )
    if (
        raw["schema_version"] != 1
        or raw["amendment_id"] != AMENDMENT_ID
        or raw["status"] != "frozen"
        or raw["phase0_freeze_path"] != TOP40_V2_LAYOUT.phase0_freeze_path
        or raw["draft_path"] != AMENDMENT_DRAFT_PATH
        or raw["integration_manifest_path"] != INTEGRATION_MANIFEST_PATH
        or raw["review_path"] != AMENDMENT_REVIEW_PATH
        or raw["score_calculation_implemented"] is not True
    ):
        raise ValueError("amendment freeze identity is invalid")
    _utc(raw["frozen_at_utc"], "freeze frozen_at_utc")
    for field in (
        "phase0_freeze_sha256",
        "draft_sha256",
        "chain_parent_sha256",
        "integration_manifest_sha256",
        "review_input_sha256",
    ):
        _sha256(raw[field], f"freeze {field}")
    for field in ("phase0_common_commit", "amendment_commit", "review_commit"):
        if not isinstance(raw[field], str) or _COMMIT.fullmatch(raw[field]) is None:
            raise ValueError(f"freeze {field} is invalid")
    files = raw["amendment_files"]
    if not isinstance(files, Mapping) or set(files) != set(AMENDMENT_FILE_PATHS):
        raise ValueError("freeze amendment-file manifest is incomplete")
    for path, digest in files.items():
        _safe_relative(path, "freeze amendment file")
        _sha256(digest, f"freeze amendment hash {path}")
    _validate_required_backfills(raw["required_backfills"])
    _validate_review(raw["review"])
    review = raw["review"]
    if (
        review["draft_sha256"] != raw["draft_sha256"]
        or review["phase0_freeze_sha256"] != raw["phase0_freeze_sha256"]
        or dict(review["amendment_files"]) != dict(files)
        or review["integration_manifest_sha256"]
        != raw["integration_manifest_sha256"]
        or review["required_backfills"] != raw["required_backfills"]
        or review["score_calculation_implemented"] is not True
        or _utc(raw["frozen_at_utc"], "freeze time")
        < _utc(review["reviewed_at_utc"], "review time")
    ):
        raise ValueError("amendment freeze differs from its embedded organizer review")


def _validate_review(raw: object) -> None:
    review = _exact_object(
        raw,
        {
            "schema_version",
            "amendment_id",
            "decision",
            "decision_scope",
            "decision_data",
            "authorized_by",
            "reviewed_at_utc",
            "draft_sha256",
            "phase0_freeze_sha256",
            "amendment_files",
            "integration_manifest_path",
            "integration_manifest_sha256",
            "required_backfills",
            "score_calculation_implemented",
            "notes",
        },
        "amendment review",
    )
    if (
        review["schema_version"] != 1
        or review["amendment_id"] != AMENDMENT_ID
        or review["decision"] != "approve"
        or review["decision_scope"]
        != "freeze-amendment-0001-integration-and-required-backfills"
        or review["integration_manifest_path"] != INTEGRATION_MANIFEST_PATH
        or review["score_calculation_implemented"] is not True
    ):
        raise ValueError("amendment review must explicitly approve amendment 0001")
    _nonempty(review["authorized_by"], "review authorized_by", maximum=1000)
    _nonempty(review["notes"], "review notes", maximum=20_000)
    _utc(review["reviewed_at_utc"], "review reviewed_at_utc")
    _sha256(review["draft_sha256"], "review draft_sha256")
    _sha256(review["phase0_freeze_sha256"], "review phase0_freeze_sha256")
    _sha256(review["integration_manifest_sha256"], "review integration manifest SHA-256")
    decision_data = _exact_object(
        review["decision_data"],
        {
            "reviewed_exact_implementation_bytes",
            "reviewed_required_backfills",
            "approved_private_numeric_disclosure_boundary",
            "approved_hold_toll_and_resume",
        },
        "review decision_data",
    )
    if any(value is not True for value in decision_data.values()):
        raise ValueError("review decision_data must explicitly approve every boundary")
    _validate_required_backfills(review["required_backfills"])
    files = review["amendment_files"]
    if not isinstance(files, Mapping) or set(files) != set(AMENDMENT_FILE_PATHS):
        raise ValueError("review amendment_files manifest is incomplete")
    for path, digest in files.items():
        _safe_relative(path, "review amendment path")
        _sha256(digest, f"review amendment hash {path}")


def _validate_hold_notice(raw: Mapping[str, Any]) -> None:
    _exact_object(
        raw,
        {
            "schema_version",
            "amendment_id",
            "notice_status",
            "phase0_freeze_path",
            "phase0_freeze_sha256",
            "legacy_state_sha256",
            "research_journal_path",
            "research_journal_head_sha256",
            "research_journal_record_count",
            "research_journal_latest_timestamp_utc",
            "hold_started_at_utc",
            "hold_reason",
        },
        "administrative hold notice",
    )
    if (
        raw["schema_version"] != 1
        or raw["amendment_id"] != AMENDMENT_ID
        or raw["notice_status"] != "administrative_hold"
        or raw["phase0_freeze_path"] != TOP40_V2_LAYOUT.phase0_freeze_path
        or raw["research_journal_path"] != TOP40_V2_LAYOUT.organizer_journal_path
    ):
        raise ValueError("administrative hold notice identity is invalid")
    for field in (
        "phase0_freeze_sha256",
        "legacy_state_sha256",
        "research_journal_head_sha256",
    ):
        _sha256(raw[field], f"hold notice {field}")
    _integer(
        raw["research_journal_record_count"],
        "hold notice research journal record count",
        minimum=1,
    )
    _utc(raw["research_journal_latest_timestamp_utc"], "hold notice research head time")
    _utc(raw["hold_started_at_utc"], "hold notice start")
    _nonempty(raw["hold_reason"], "hold notice reason")


def _load_hold_notice(
    root: Path,
    *,
    authority: Phase0Authority,
    baseline_state_created_at_utc: str,
    baseline_legacy_state_sha256: str,
    baseline_research_journal: Mapping[str, Any],
    implementation_commit: str,
    clock: UtcClock,
) -> tuple[Mapping[str, Any], bytes, str]:
    _relative, _path, notice_bytes, _stat = read_repo_file(
        root,
        HOLD_NOTICE_PATH,
        "administrative hold notice",
        maximum_bytes=256 * 1024,
        require_single_link=True,
    )
    notice = _strict_json_bytes(notice_bytes, "administrative hold notice")
    _validate_hold_notice(notice)
    if pretty_json_bytes(notice) != notice_bytes:
        raise ValueError("administrative hold notice must be canonical JSON")
    expected = {
        "phase0_freeze_sha256": authority.freeze_sha256,
        "legacy_state_sha256": baseline_legacy_state_sha256,
        "research_journal_head_sha256": baseline_research_journal["head_sha256"],
        "research_journal_record_count": baseline_research_journal["record_count"],
        "research_journal_latest_timestamp_utc": baseline_research_journal[
            "latest_timestamp_utc"
        ],
    }
    if any(notice[field] != value for field, value in expected.items()):
        raise ValueError("administrative hold notice differs from activation baselines")
    started = bounded_event_time(
        notice["hold_started_at_utc"],
        "administrative hold start",
        lower_bounds=(
            ("Phase-0 freeze time", authority.frozen_at_utc),
            ("Phase-0 record commit time", authority.record_commit_time_utc),
            ("run-state creation time", baseline_state_created_at_utc),
            (
                "baseline research journal head time",
                baseline_research_journal["latest_timestamp_utc"],
            ),
        ),
        clock=clock,
    )
    if notice["hold_started_at_utc"] != started:
        raise ValueError("administrative hold notice start is noncanonical")
    notice_commit = unique_first_add_commit(
        root,
        HOLD_NOTICE_PATH,
        notice_bytes,
        require_direct_parent=implementation_commit,
    )
    notice_commit_time = git_commit_time(root, notice_commit, "hold notice commit time")
    implementation_commit_time = git_commit_time(
        root,
        implementation_commit,
        "amendment implementation commit time",
    )
    if notice_commit_time < _utc(started, "hold start"):
        raise ValueError("hold notice commit cannot precede the declared hold start")
    if notice_commit_time < implementation_commit_time:
        raise ValueError("hold notice commit cannot predate its implementation parent")
    if notice_commit_time > trusted_now(clock):
        raise ValueError("hold notice commit cannot be in the future")
    return notice, notice_bytes, notice_commit


def _load_committed_review(
    root: Path,
    *,
    draft_commit: str,
    clock: UtcClock,
) -> tuple[Mapping[str, Any], bytes, str]:
    _relative, _path, review_bytes, _stat = read_repo_file(
        root,
        AMENDMENT_REVIEW_PATH,
        "committed amendment review",
        maximum_bytes=4 * 1024 * 1024,
        require_single_link=True,
    )
    review = _strict_json_bytes(review_bytes, "committed amendment review")
    _validate_review(review)
    if pretty_json_bytes(review) != review_bytes:
        raise ValueError("committed amendment review must be canonical JSON")
    review_commit = unique_first_add_commit(
        root,
        AMENDMENT_REVIEW_PATH,
        review_bytes,
        require_direct_parent=draft_commit,
    )
    review_commit_time = git_commit_time(root, review_commit, "amendment review commit time")
    if review_commit_time < _utc(review["reviewed_at_utc"], "review decision time"):
        raise ValueError("amendment review commit cannot predate its decision time")
    if review_commit_time > trusted_now(clock):
        raise ValueError("amendment review commit cannot be future-dated")
    return review, review_bytes, review_commit


def _load_integration_manifest(
    root: Path,
    *,
    authority: Phase0Authority,
    draft_sha256: str,
    implementation_commit: str,
    amendment_files: Mapping[str, str],
    research: JournalState,
) -> tuple[Mapping[str, Any], bytes]:
    _relative, _path, manifest_bytes, _stat = read_repo_file(
        root,
        INTEGRATION_MANIFEST_PATH,
        "integration manifest",
        maximum_bytes=4 * 1024 * 1024,
        require_single_link=True,
    )
    manifest = _strict_json_bytes(manifest_bytes, "integration manifest")
    _validate_integration_manifest(manifest)
    if pretty_json_bytes(manifest) != manifest_bytes:
        raise ValueError("integration manifest must be canonical JSON")
    expected_backfills = _required_backfill_bindings(root, research)
    if (
        manifest["phase0_freeze_sha256"] != authority.freeze_sha256
        or manifest["draft_sha256"] != draft_sha256
        or manifest["implementation_commit"] != implementation_commit
        or manifest["amendment_files"] != dict(amendment_files)
        or manifest["required_backfills"] != expected_backfills
    ):
        raise ValueError("integration manifest differs from current reviewed authorities")
    return manifest, manifest_bytes


def _read_amended_state_locked(
    root: Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock = system_utc_now,
) -> tuple[dict[str, Any], bytes, AmendmentChainState, OrganizerAuditState]:
    _relative, _path, state_bytes, _stat = read_repo_file(
        root,
        TOP40_V2_LAYOUT.state_path,
        "amendment-aware run state",
    )
    state = dict(_strict_json_bytes(state_bytes, "amendment-aware run state"))
    validate_amended_run_state(state, config)
    amendment = state["amendment"]
    projection = _legacy_projection(state)
    authority = _phase0_authority(root, projection, config, clock=clock)
    if (
        authority.freeze_sha256 != amendment["phase0_freeze_sha256"]
        or authority.common_commit != amendment["phase0_common_commit"]
        or authority.record_commit != amendment["phase0_record_commit"]
    ):
        raise ValueError("Phase-0 authority differs from amendment state")

    research = _load_bound_research_journal(root, config, state)
    baseline_research = amendment["baseline_research_journal"]
    _validate_baseline_research_prefix(research, baseline_research)
    current_research_time = bounded_event_time(
        research.last_timestamp_utc,
        "current research journal head time",
        lower_bounds=(
            (
                "baseline research journal head time",
                baseline_research["latest_timestamp_utc"],
            ),
        ),
        clock=clock,
    )
    if current_research_time != research.last_timestamp_utc:
        raise ValueError("current research journal head time is noncanonical")
    files = _amendment_file_hashes(root)
    implementation_commit = _committed_amendment_files(
        root,
        files,
        authority,
        clock=clock,
    )
    notice, notice_bytes, notice_commit = _load_hold_notice(
        root,
        authority=authority,
        baseline_state_created_at_utc=projection["created_at_utc"],
        baseline_legacy_state_sha256=state["legacy_state_sha256"],
        baseline_research_journal=baseline_research,
        implementation_commit=implementation_commit,
        clock=clock,
    )
    if (
        amendment["implementation_commit"] != implementation_commit
        or amendment["hold_notice_sha256"] != _sha256_bytes(notice_bytes)
        or amendment["hold_notice_commit"] != notice_commit
    ):
        raise ValueError("implementation/hold notice differs from amendment state")

    _draft_relative, _draft_path, draft_bytes, _draft_stat = read_repo_file(
        root,
        AMENDMENT_DRAFT_PATH,
        "amendment draft",
    )
    draft = _strict_json_bytes(draft_bytes, "amendment draft")
    _validate_draft(draft)
    hold = state["administrative_hold"]
    if (
        _sha256_bytes(draft_bytes) != amendment["draft_sha256"]
        or draft["phase0_freeze_sha256"] != authority.freeze_sha256
        or draft["phase0_common_commit"] != authority.common_commit
        or draft["baseline_config_sha256"] != config.sha256
        or draft["baseline_legacy_state_sha256"] != state["legacy_state_sha256"]
        or draft["baseline_legacy_projection_sha256"] != state["legacy_state_sha256"]
        or draft["baseline_research_journal"] != baseline_research
        or draft["baseline_research_deadline_utc"] != hold["baseline_research_deadline_utc"]
        or draft["hold_notice_sha256"] != amendment["hold_notice_sha256"]
        or draft["hold_notice_commit"] != notice_commit
        or draft["implementation_commit"] != implementation_commit
        or draft["created_at_utc"] != hold["started_at_utc"]
        or draft["hold_started_at_utc"] != hold["started_at_utc"]
        or draft["hold_reason"] != hold["reason"]
        or notice["hold_reason"] != hold["reason"]
        or notice["hold_started_at_utc"] != hold["started_at_utc"]
        or files != dict(draft["amendment_files"])
    ):
        raise ValueError("amendment draft differs from current authorities")
    if hold["active"] is True and state["legacy_projection_sha256"] != state[
        "legacy_state_sha256"
    ]:
        raise ValueError("legacy fields mutated during the administrative hold")

    _chain_relative, _chain_path, chain_bytes, _chain_stat = read_repo_file(
        root,
        AMENDMENT_CHAIN_PATH,
        "amendment chain",
    )
    chain = validate_amendment_chain_bytes(chain_bytes)
    _audit_relative, _audit_path, audit_bytes, _audit_stat = read_repo_file(
        root,
        ORGANIZER_AUDIT_PATH,
        "organizer audit",
    )
    audit = validate_organizer_audit_bytes(audit_bytes)
    if chain.binding != amendment["chain"] or audit.binding != state["organizer_audit"]:
        raise ValueError("amendment journals differ from run-state bindings")
    now = trusted_now(clock)
    if any(
        _utc(record["timestamp_utc"], "amendment event time") > now
        for record in (*chain.records, *audit.records)
    ):
        raise ValueError("amendment journal contains a future-dated event")
    draft_event = chain.records[0]["payload"]
    audit_genesis = audit.records[0]["payload"]
    if (
        chain.records[0]["timestamp_utc"] != hold["started_at_utc"]
        or audit.records[0]["timestamp_utc"] != hold["started_at_utc"]
        or draft_event["phase0_freeze_sha256"] != authority.freeze_sha256
        or draft_event["draft_sha256"] != amendment["draft_sha256"]
        or draft_event["hold_notice_sha256"] != amendment["hold_notice_sha256"]
        or draft_event["hold_notice_commit"] != notice_commit
        or draft_event["legacy_projection_sha256"] != state["legacy_state_sha256"]
        or draft_event["hold_started_at_utc"] != hold["started_at_utc"]
        or draft_event["hold_reason"] != hold["reason"]
        or audit_genesis["phase0_freeze_sha256"] != authority.freeze_sha256
        or audit_genesis["draft_sha256"] != amendment["draft_sha256"]
        or audit_genesis["hold_notice_sha256"] != amendment["hold_notice_sha256"]
    ):
        raise ValueError("amendment genesis journals differ from current authorities")

    expected_chain_length = 1 if amendment["status"] == "draft" else 2
    if hold["active"] is False:
        expected_chain_length = 3
    if len(chain.records) != expected_chain_length:
        raise ValueError("amendment chain lifecycle differs from run state")
    if amendment["status"] == "frozen":
        draft_commit = unique_first_add_commit(
            root,
            AMENDMENT_DRAFT_PATH,
            draft_bytes,
            require_direct_parent=notice_commit,
        )
        review, review_bytes, review_commit = _load_committed_review(
            root,
            draft_commit=draft_commit,
            clock=clock,
        )
        integration, integration_bytes = _load_integration_manifest(
            root,
            authority=authority,
            draft_sha256=amendment["draft_sha256"],
            implementation_commit=implementation_commit,
            amendment_files=files,
            research=research,
        )
        _freeze_relative, _freeze_path, freeze_bytes, _freeze_stat = read_repo_file(
            root,
            AMENDMENT_FREEZE_PATH,
            "amendment freeze",
        )
        freeze = _strict_json_bytes(freeze_bytes, "amendment freeze")
        _validate_freeze(freeze)
        freeze_event = chain.records[1]
        review_time = bounded_event_time(
            review["reviewed_at_utc"],
            "organizer review time",
            lower_bounds=(
                ("hold start", hold["started_at_utc"]),
                ("draft creation time", draft["created_at_utc"]),
                (
                    "baseline research journal head time",
                    baseline_research["latest_timestamp_utc"],
                ),
                ("Phase-0 record commit time", authority.record_commit_time_utc),
            ),
            clock=clock,
        )
        freeze_time = bounded_event_time(
            freeze["frozen_at_utc"],
            "amendment freeze time",
            lower_bounds=(
                ("hold start", hold["started_at_utc"]),
                ("organizer review time", review_time),
                ("amendment draft event time", chain.records[0]["timestamp_utc"]),
                ("organizer audit genesis time", audit.records[0]["timestamp_utc"]),
                (
                    "baseline research journal head time",
                    baseline_research["latest_timestamp_utc"],
                ),
                ("Phase-0 record commit time", authority.record_commit_time_utc),
            ),
            clock=clock,
        )
        freeze_commit = unique_first_add_commit(
            root,
            AMENDMENT_FREEZE_PATH,
            freeze_bytes,
            require_direct_parent=review_commit,
        )
        integration_commit = unique_first_add_commit(
            root,
            INTEGRATION_MANIFEST_PATH,
            integration_bytes,
            require_direct_parent=review_commit,
        )
        if freeze_commit != integration_commit:
            raise ValueError("freeze and integration manifest require one exact first-add commit")
        freeze_commit_time = git_commit_time(
            root,
            freeze_commit,
            "amendment freeze record commit time",
        )
        if freeze_commit_time < _utc(freeze_time, "amendment freeze time"):
            raise ValueError("amendment freeze record commit cannot predate the freeze event")
        if freeze_commit_time > trusted_now(clock):
            raise ValueError("amendment freeze record commit cannot be future-dated")
        freeze_chain_bytes = b"".join(
            _journal_line(record) for record in chain.records[:2]
        )
        freeze_chain = validate_amendment_chain_bytes(freeze_chain_bytes)
        committed_chain_bytes = git_bytes(
            root,
            "show",
            f"{freeze_commit}:{AMENDMENT_CHAIN_PATH}",
            label="committed amendment freeze chain",
        )
        if committed_chain_bytes != freeze_chain_bytes:
            raise ValueError("freeze record commit lacks the exact two-event amendment chain")
        committed_state_bytes = git_bytes(
            root,
            "show",
            f"{freeze_commit}:{TOP40_V2_LAYOUT.state_path}",
            label="committed amendment freeze state",
        )
        committed_state = dict(
            _strict_json_bytes(committed_state_bytes, "committed amendment freeze state")
        )
        if _json_bytes(committed_state) != committed_state_bytes:
            raise ValueError("committed amendment freeze state is not canonical JSON")
        validate_amended_run_state(committed_state, config)
        genesis_audit = validate_organizer_audit_bytes(_journal_line(audit.records[0]))
        expected_frozen_amendment = copy.deepcopy(state["amendment"])
        expected_frozen_amendment["chain"] = freeze_chain.binding
        expected_frozen_hold = copy.deepcopy(state["administrative_hold"])
        expected_frozen_hold.update(
            {
                "active": True,
                "resumed_at_utc": None,
                "hold_duration_microseconds": None,
                "cumulative_toll_microseconds": 0,
                "effective_research_deadline_utc": expected_frozen_hold[
                    "baseline_research_deadline_utc"
                ],
            }
        )
        if (
            committed_state["legacy_state_sha256"] != state["legacy_state_sha256"]
            or committed_state["legacy_projection_sha256"]
            != state["legacy_state_sha256"]
            or committed_state["amendment"] != expected_frozen_amendment
            or committed_state["administrative_hold"] != expected_frozen_hold
            or committed_state["organizer_audit"] != genesis_audit.binding
        ):
            raise ValueError("freeze record commit lacks the exact schema-3 freeze state")
        if (
            _sha256_bytes(freeze_bytes) != amendment["freeze_sha256"]
            or freeze["phase0_freeze_sha256"] != authority.freeze_sha256
            or freeze["phase0_common_commit"] != authority.common_commit
            or freeze["draft_sha256"] != amendment["draft_sha256"]
            or freeze["amendment_files"] != files
            or freeze["amendment_commit"] != implementation_commit
            or freeze["review"] != review
            or freeze["review_input_sha256"] != _sha256_bytes(review_bytes)
            or freeze["review_commit"] != review_commit
            or freeze["integration_manifest_sha256"]
            != _sha256_bytes(integration_bytes)
            or freeze["required_backfills"] != integration["required_backfills"]
            or amendment["review_sha256"] != _sha256_bytes(review_bytes)
            or amendment["review_commit"] != review_commit
            or amendment["integration_manifest_sha256"]
            != _sha256_bytes(integration_bytes)
            or freeze["chain_parent_sha256"] != chain.records[0]["record_sha256"]
            or freeze_event["previous_record_sha256"] != freeze["chain_parent_sha256"]
            or freeze_event["timestamp_utc"] != freeze_time
            or freeze_event["payload"]["freeze_sha256"] != amendment["freeze_sha256"]
            or freeze_event["payload"]["review_sha256"]
            != amendment["review_sha256"]
            or freeze_event["payload"]["integration_manifest_sha256"]
            != amendment["integration_manifest_sha256"]
            or freeze_event["payload"]["score_calculation_implemented"] is not True
        ):
            raise ValueError("freeze chain parent or freeze binding is invalid")
        for diagnostic_id, reservation in audit.reservations.items():
            _validate_reservation_authority(
                root,
                config,
                state,
                research,
                reservation["payload"],
            )
            result = audit.results.get(diagnostic_id)
            if result is not None and result["payload"]["status"] == "completed":
                observed_hashes, observed_outcomes = _completed_diagnostic_evidence(
                    root,
                    reservation,
                )
                if (
                    result["payload"]["artifact_hashes"] != observed_hashes
                    or result["payload"]["diagnostic_outcomes"] != observed_outcomes
                ):
                    raise ValueError(
                        "completed diagnostic audit differs from trusted private evidence"
                    )
        if hold["active"] is False:
            resume_event = chain.records[2]
            resumed_time = bounded_event_time(
                hold["resumed_at_utc"],
                "administrative hold resume time",
                lower_bounds=(
                    ("hold start", hold["started_at_utc"]),
                    ("amendment freeze time", freeze_time),
                    (
                        "baseline research journal head time",
                        baseline_research["latest_timestamp_utc"],
                    ),
                ),
                clock=clock,
            )
            if (
                resume_event["timestamp_utc"] != resumed_time
                or resume_event["payload"]["freeze_sha256"] != amendment["freeze_sha256"]
                or resume_event["payload"]["hold_duration_microseconds"]
                != hold["hold_duration_microseconds"]
                or resume_event["payload"]["effective_research_deadline_utc"]
                != hold["effective_research_deadline_utc"]
            ):
                raise ValueError("hold resume chain event differs from run state")
    elif audit.reservations or audit.results:
        raise ValueError("draft amendment cannot contain diagnostic audit events")
    return state, state_bytes, chain, audit


def read_amended_state(
    root: str | Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock = system_utc_now,
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    with _state_lock(root_path):
        return _read_amended_state_locked(root_path, config, clock=clock)[0]


def _require_ordinary_operation(operation: str) -> None:
    if operation not in READ_ONLY_OPERATIONS and operation not in RESULT_BEARING_OPERATIONS:
        raise ValueError(f"unknown amendment-aware ordinary operation: {operation!r}")


def read_amendment_aware_legacy_state(
    root: str | Path,
    config: LoadedV2Config,
    *,
    operation: str,
    clock: UtcClock = system_utc_now,
) -> dict[str, Any]:
    """Return a validated schema-v2 projection for one ordinary operation."""

    _require_ordinary_operation(operation)
    root_path = Path(root).resolve()
    with _state_lock(root_path):
        state, _state_bytes, _chain, _audit = _read_amended_state_locked(
            root_path,
            config,
            clock=clock,
        )
        _require_integration_ready(state, operation)
        assert_operation_permitted(state, operation)
        return _legacy_projection(state)


def _staged_relative(root: Path, change: TransactionChange) -> str:
    if not isinstance(change, TransactionChange):
        raise ValueError("staged legacy changes must be TransactionChange values")
    raw_path = Path(change.path)
    candidate = Path(
        os.path.abspath(raw_path if raw_path.is_absolute() else root / raw_path)
    )
    if not candidate.is_relative_to(root):
        raise ValueError("staged legacy change escapes the tournament worktree")
    relative = candidate.relative_to(root).as_posix()
    _safe_relative(relative, "staged legacy change path")
    current = root
    for part in PurePosixPath(relative).parts[:-1]:
        current /= part
        try:
            info = os.lstat(current)
        except FileNotFoundError as exc:
            raise ValueError("staged legacy change parent is missing") from exc
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise ValueError("staged legacy change parent is unsafe")
    if candidate.exists() or candidate.is_symlink():
        info = os.lstat(candidate)
        if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or info.st_nlink != 1:
            raise ValueError("staged legacy change target is unsafe")
    if change.expected is not None and not isinstance(change.expected, bytes):
        raise ValueError("staged legacy expected bytes must be bytes or null")
    if not isinstance(change.replacement, bytes):
        raise ValueError("staged legacy replacement must be bytes")
    return relative


def _validate_staged_legacy_changes(
    root: Path,
    changes: Sequence[TransactionChange],
) -> tuple[list[TransactionChange], TransactionChange | None]:
    protected = {
        TOP40_V2_LAYOUT.state_path,
        TOP40_V2_LAYOUT.phase0_freeze_path,
        HOLD_NOTICE_PATH,
        AMENDMENT_DRAFT_PATH,
        AMENDMENT_REVIEW_PATH,
        AMENDMENT_FREEZE_PATH,
        INTEGRATION_MANIFEST_PATH,
        AMENDMENT_CHAIN_PATH,
        ORGANIZER_AUDIT_PATH,
        *PHASE0_FROZEN_FILES,
        *AMENDMENT_FILE_PATHS,
    }
    team_ledger_outputs = {
        f"{TOP40_V2_LAYOUT.team_root(team_id)}/experiments.jsonl"
        for team_id in TEAM_IDS
    } | {
        f"{TOP40_V2_LAYOUT.team_root(team_id)}/families.jsonl"
        for team_id in TEAM_IDS
    }
    seen: set[str] = set()
    normalized: list[TransactionChange] = []
    journal_change: TransactionChange | None = None
    for change in changes:
        relative = _staged_relative(root, change)
        if relative in seen:
            raise ValueError(f"duplicate staged legacy path: {relative}")
        seen.add(relative)
        parts = PurePosixPath(relative).parts
        inside_team_source = relative.startswith(
            f"{TOP40_V2_LAYOUT.tournament_root}/teams/"
        )
        if (
            not parts
            or parts[0] == ".git"
            or relative in protected
            or (inside_team_source and relative not in team_ledger_outputs)
            or not (
                relative.startswith(f"{TOP40_V2_LAYOUT.tournament_root}/")
                or relative.startswith(f"{TOP40_V2_LAYOUT.reports_root}/")
            )
        ):
            raise ValueError(f"staged legacy path is protected or outside outputs: {relative}")
        candidate = root / relative
        try:
            current = candidate.read_bytes()
        except FileNotFoundError:
            current = None
        except OSError as exc:
            raise ValueError(f"cannot read staged legacy input {relative}: {exc}") from exc
        if current != change.expected:
            raise ValueError(f"staged legacy expected bytes differ: {relative}")
        normalized_change = _Change(candidate, change.expected, change.replacement)
        if relative == TOP40_V2_LAYOUT.organizer_journal_path:
            journal_change = normalized_change
        normalized.append(normalized_change)
    return normalized, journal_change


@contextmanager
def amendment_aware_legacy_state_edit(
    root: str | Path,
    config: LoadedV2Config,
    *,
    operation: str,
    staged_changes: list[TransactionChange] | None = None,
    clock: UtcClock = system_utc_now,
) -> Iterator[dict[str, Any]]:
    """Atomically publish one validated legacy transition inside schema-v3 state."""

    _require_ordinary_operation(operation)
    if operation not in RESULT_BEARING_OPERATIONS:
        raise ValueError(f"read-only operation {operation!r} cannot edit legacy state")
    supplied_changes = [] if staged_changes is None else staged_changes
    if not isinstance(supplied_changes, list):
        raise ValueError("staged_changes must be a list of TransactionChange values")
    root_path = Path(root).resolve()
    with _state_lock(root_path):
        state, state_bytes, _chain, _audit = _read_amended_state_locked(
            root_path,
            config,
            clock=clock,
        )
        _require_integration_ready(state, operation)
        assert_operation_permitted(state, operation)
        if state["administrative_hold"]["active"] is not False:
            raise ValueError("legacy state edits require the resumed amendment hold")
        before = _legacy_projection(state)
        projection = copy.deepcopy(before)
        yield projection
        validate_run_state(projection, config)
        for field in (
            "schema_version",
            "tournament",
            "created_at_utc",
            "config_path",
            "config_sha256",
            "phase0",
        ):
            if projection[field] != before[field]:
                raise ValueError(f"legacy transition changed immutable field {field!r}")
        changes, journal_change = _validate_staged_legacy_changes(
            root_path,
            tuple(supplied_changes),
        )
        current_journal = _load_bound_research_journal(root_path, config, state)
        next_journal = current_journal
        if journal_change is not None:
            if journal_change.expected != current_journal.journal_bytes:
                raise ValueError("staged research journal expected bytes differ from authority")
            if (
                journal_change.replacement == current_journal.journal_bytes
                or not journal_change.replacement.startswith(current_journal.journal_bytes)
            ):
                raise ValueError("staged research journal must append exact current bytes")
            next_journal = validate_journal_bytes(
                journal_change.replacement,
                _research_policy(config),
            )
        changes_by_relative = {
            change.path.relative_to(root_path).as_posix(): change for change in changes
        }
        for team_id in TEAM_IDS:
            ledger_relative = f"{TOP40_V2_LAYOUT.team_root(team_id)}/experiments.jsonl"
            ledger_change = changes_by_relative.get(ledger_relative)
            if ledger_change is None:
                _ledger_relative, _ledger_path, ledger_bytes, _ledger_stat = read_repo_file(
                    root_path,
                    ledger_relative,
                    f"{team_id} trial ledger",
                    maximum_bytes=32 * 1024 * 1024,
                    require_single_link=True,
                )
            else:
                ledger_bytes = ledger_change.replacement
            validate_team_ledger_bytes(ledger_bytes, next_journal, team_id)
        expected_binding = {
            "path": TOP40_V2_LAYOUT.organizer_journal_path,
            "genesis_sha256": next_journal.genesis_sha256,
            "head_sha256": next_journal.head_sha256,
            "record_count": len(next_journal.records),
        }
        if projection["research_journal"] != expected_binding:
            raise ValueError("legacy projection differs from replacement research journal")
        for team_id in TEAM_IDS:
            if (
                projection["teams"][team_id]["trial_count"]
                != next_journal.teams[team_id].material_trial_count
            ):
                raise ValueError("legacy team trial counts differ from replacement journal")
        replacement_state = copy.deepcopy(state)
        for key in LEGACY_STATE_KEYS:
            replacement_state[key] = copy.deepcopy(projection[key])
        replacement_state["schema_version"] = AMENDMENT_STATE_SCHEMA_VERSION
        replacement_state["legacy_projection_sha256"] = _sha256_bytes(
            _json_bytes(projection)
        )
        validate_amended_run_state(replacement_state, config)
        _publish_transaction(
            root_path,
            (
                *changes,
                _Change(
                    root_path / TOP40_V2_LAYOUT.state_path,
                    state_bytes,
                    _json_bytes(replacement_state),
                ),
            ),
        )


def assert_operation_permitted(state: Mapping[str, Any], operation: str) -> None:
    """Enforce the administrative hold for every amendment-aware operation."""

    if operation in READ_ONLY_OPERATIONS:
        return
    hold = state.get("administrative_hold")
    if not isinstance(hold, Mapping):
        raise ValueError("operation requires an amendment-aware run state")
    if hold.get("active") is True:
        if operation in AMENDMENT_ADMIN_OPERATIONS:
            return
        raise ValueError(
            f"global administrative hold blocks {operation!r}; only read-only status, "
            "non-result documentation, and amendment administration are allowed"
        )
    if operation in {"freeze-amendment", "resume-amendment"}:
        raise ValueError(f"{operation!r} is closed after the amendment hold resumes")


def effective_research_deadline(state: Mapping[str, Any]) -> datetime:
    hold = state.get("administrative_hold")
    if not isinstance(hold, Mapping):
        raise ValueError("effective deadline requires an amendment-aware run state")
    return _utc(hold.get("effective_research_deadline_utc"), "effective deadline")


def activate_amendment_draft(
    root: str | Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock = system_utc_now,
) -> Mapping[str, Any]:
    """Activate only the hold/draft from the committed, immutable hold notice."""

    root_path = Path(root).resolve()
    state_path = root_path / TOP40_V2_LAYOUT.state_path
    with _state_lock(root_path):
        _relative, _path, legacy_bytes, _stat = read_repo_file(
            root_path,
            TOP40_V2_LAYOUT.state_path,
            "legacy V2 run state",
        )
        legacy_raw = _strict_json_bytes(legacy_bytes, "legacy V2 run state")
        legacy = dict(legacy_raw)
        if legacy.get("schema_version") != 2 or set(legacy) != LEGACY_STATE_KEYS:
            raise ValueError("amendment activation requires one exact legacy schema-v2 state")
        if _json_bytes(legacy) != legacy_bytes:
            raise ValueError("legacy V2 run state must be canonical JSON before activation")
        validate_run_state(legacy, config)
        if legacy.get("phase") != "research":
            raise ValueError("amendment 0001 draft may activate only during research")
        authority = _phase0_authority(root_path, legacy, config, clock=clock)
        journal = _load_bound_research_journal(root_path, config, legacy)
        files = _amendment_file_hashes(root_path)
        implementation_commit = _committed_amendment_files(
            root_path,
            files,
            authority,
            clock=clock,
        )
        baseline_research = {
            "path": TOP40_V2_LAYOUT.organizer_journal_path,
            "genesis_sha256": journal.genesis_sha256,
            "head_sha256": journal.head_sha256,
            "record_count": len(journal.records),
            "latest_timestamp_utc": journal.last_timestamp_utc,
        }
        _validate_baseline_research_binding(baseline_research)
        for relative in (
            AMENDMENT_DRAFT_PATH,
            AMENDMENT_FREEZE_PATH,
            AMENDMENT_CHAIN_PATH,
            ORGANIZER_AUDIT_PATH,
            AMENDMENT_REVIEW_PATH,
            INTEGRATION_MANIFEST_PATH,
        ):
            require_no_git_history(root_path, relative)
            path = root_path / relative
            if path.exists() or path.is_symlink():
                raise ValueError(f"amendment 0001 is one-shot; path already exists: {relative}")
        notice, notice_bytes, notice_commit = _load_hold_notice(
            root_path,
            authority=authority,
            baseline_state_created_at_utc=legacy["created_at_utc"],
            baseline_legacy_state_sha256=_sha256_bytes(legacy_bytes),
            baseline_research_journal=baseline_research,
            implementation_commit=implementation_commit,
            clock=clock,
        )
        started_text = str(notice["hold_started_at_utc"])
        reason = str(notice["hold_reason"])
        phase0 = authority.freeze
        phase0_sha = authority.freeze_sha256
        legacy_sha = _sha256_bytes(legacy_bytes)
        legacy_projection_sha = _sha256_bytes(_json_bytes(legacy))
        notice_sha = _sha256_bytes(notice_bytes)
        baseline_deadline = _utc_text(
            config.raw["research_budget"]["deadline_utc"], "research deadline"
        )
        if _utc(started_text, "hold start") > _utc(baseline_deadline, "research deadline"):
            raise ValueError("administrative hold cannot start after the research deadline")
        draft: dict[str, Any] = {
            "schema_version": 1,
            "amendment_id": AMENDMENT_ID,
            "status": "draft",
            "created_at_utc": started_text,
            "phase0_freeze_path": TOP40_V2_LAYOUT.phase0_freeze_path,
            "phase0_freeze_sha256": phase0_sha,
            "phase0_common_commit": phase0["common_freeze_commit"],
            "baseline_config_sha256": config.sha256,
            "baseline_legacy_state_sha256": legacy_sha,
            "baseline_legacy_projection_sha256": legacy_projection_sha,
            "baseline_research_journal": baseline_research,
            "baseline_research_deadline_utc": baseline_deadline,
            "hold_notice_path": HOLD_NOTICE_PATH,
            "hold_notice_sha256": notice_sha,
            "hold_notice_commit": notice_commit,
            "hold_started_at_utc": started_text,
            "hold_reason": reason,
            "implementation_commit": implementation_commit,
            "lifecycle_status": DRAFT_LIFECYCLE_STATUS,
            "integration_manifest_path": INTEGRATION_MANIFEST_PATH,
            "integration_ready_for_review": True,
            "authorized_scope": [
                "global administrative hold with exact research-deadline toll",
                "reviewed score diagnostics with organizer-private numeric artifacts",
                "exact required pre-resume backfills plus post-resume one-shot diagnostics",
                "amendment-aware ordinary orchestration after exact hold toll",
                "no scoring-formula, ranking, qualification, finalist, or result-release change",
            ],
            "amendment_files": files,
            "score_calculation_implemented": True,
            "claims_frozen": False,
        }
        _validate_draft(draft)
        draft_bytes = _json_bytes(draft)
        draft_sha = _sha256_bytes(draft_bytes)
        chain_record = _new_envelope(
            journal_key="chain_id",
            journal_id=AMENDMENT_CHAIN_ID,
            sequence=1,
            event_type="amendment_drafted",
            timestamp_utc=started_text,
            previous_record_sha256=None,
            payload={
                "phase0_freeze_sha256": phase0_sha,
                "draft_path": AMENDMENT_DRAFT_PATH,
                "draft_sha256": draft_sha,
                "hold_notice_sha256": notice_sha,
                "hold_notice_commit": notice_commit,
                "legacy_projection_sha256": legacy_projection_sha,
                "hold_started_at_utc": started_text,
                "hold_reason": reason,
            },
        )
        chain_bytes = _journal_line(chain_record)
        chain = validate_amendment_chain_bytes(chain_bytes)
        audit_record = _new_envelope(
            journal_key="journal_id",
            journal_id=ORGANIZER_AUDIT_ID,
            sequence=1,
            event_type="audit_genesis",
            timestamp_utc=started_text,
            previous_record_sha256=None,
            payload={
                "phase0_freeze_sha256": phase0_sha,
                "draft_sha256": draft_sha,
                "hold_notice_sha256": notice_sha,
                "non_material_diagnostics_only": True,
                "charges_team_trial_budget": False,
            },
        )
        audit_bytes = _journal_line(audit_record)
        audit = validate_organizer_audit_bytes(audit_bytes)
        amended = copy.deepcopy(legacy)
        amended.update(
            {
                "schema_version": AMENDMENT_STATE_SCHEMA_VERSION,
                "state_schema": AMENDMENT_STATE_SCHEMA_ID,
                "legacy_state_sha256": legacy_sha,
                "legacy_projection_sha256": legacy_projection_sha,
                "amendment": {
                    "amendment_id": AMENDMENT_ID,
                    "status": "draft",
                    "lifecycle_status": DRAFT_LIFECYCLE_STATUS,
                    "phase0_freeze_path": TOP40_V2_LAYOUT.phase0_freeze_path,
                    "phase0_freeze_sha256": phase0_sha,
                    "phase0_common_commit": phase0["common_freeze_commit"],
                    "phase0_record_commit": authority.record_commit,
                    "implementation_commit": implementation_commit,
                    "baseline_research_journal": baseline_research,
                    "hold_notice_path": HOLD_NOTICE_PATH,
                    "hold_notice_sha256": notice_sha,
                    "hold_notice_commit": notice_commit,
                    "draft_path": AMENDMENT_DRAFT_PATH,
                    "draft_sha256": draft_sha,
                    "review_path": AMENDMENT_REVIEW_PATH,
                    "review_sha256": None,
                    "review_commit": None,
                    "freeze_path": None,
                    "freeze_sha256": None,
                    "integration_manifest_path": INTEGRATION_MANIFEST_PATH,
                    "integration_manifest_sha256": None,
                    "score_calculation_implemented": True,
                    "chain": chain.binding,
                },
                "administrative_hold": {
                    "active": True,
                    "started_at_utc": started_text,
                    "reason": reason,
                    "resumed_at_utc": None,
                    "hold_duration_microseconds": None,
                    "cumulative_toll_microseconds": 0,
                    "baseline_research_deadline_utc": baseline_deadline,
                    "effective_research_deadline_utc": baseline_deadline,
                },
                "organizer_audit": audit.binding,
            }
        )
        validate_amended_run_state(amended, config)
        _publish_transaction(
            root_path,
            (
                _Change(root_path / AMENDMENT_DRAFT_PATH, None, draft_bytes),
                _Change(root_path / AMENDMENT_CHAIN_PATH, None, chain_bytes),
                _Change(root_path / ORGANIZER_AUDIT_PATH, None, audit_bytes),
                _Change(state_path, legacy_bytes, _json_bytes(amended)),
            ),
        )
    return draft


def integration_review_material(
    root: str | Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock = system_utc_now,
) -> Mapping[str, Any]:
    """Return stable manifest/review material without writing organizer decision bytes."""

    root_path = Path(root).resolve()
    with _state_lock(root_path):
        state, _state_bytes, _chain, _audit = _read_amended_state_locked(
            root_path,
            config,
            clock=clock,
        )
        if state["amendment"]["status"] != "draft":
            raise ValueError("integration review material is available only for the draft")
        authority = _phase0_authority(
            root_path,
            _legacy_projection(state),
            config,
            clock=clock,
        )
        _relative, _path, draft_bytes, _stat = read_repo_file(
            root_path,
            AMENDMENT_DRAFT_PATH,
            "amendment draft",
        )
        draft = _strict_json_bytes(draft_bytes, "amendment draft")
        _validate_draft(draft)
        unique_first_add_commit(
            root_path,
            AMENDMENT_DRAFT_PATH,
            draft_bytes,
            require_direct_parent=state["amendment"]["hold_notice_commit"],
        )
        files = _amendment_file_hashes(root_path)
        implementation_commit = _committed_amendment_files(
            root_path,
            files,
            authority,
            clock=clock,
        )
        research = _load_bound_research_journal(root_path, config, state)
        required_backfills = _required_backfill_bindings(root_path, research)
        manifest = _integration_manifest(
            authority=authority,
            draft_sha256=_sha256_bytes(draft_bytes),
            implementation_commit=implementation_commit,
            amendment_files=files,
            required_backfills=required_backfills,
        )
        manifest_bytes = _json_bytes(manifest)
        return {
            "integration_manifest_path": INTEGRATION_MANIFEST_PATH,
            "integration_manifest": manifest,
            "integration_manifest_sha256": _sha256_bytes(manifest_bytes),
            "required_backfills": required_backfills,
            "review_path": AMENDMENT_REVIEW_PATH,
            "decision_scope": "freeze-amendment-0001-integration-and-required-backfills",
            "score_calculation_implemented": True,
        }


def freeze_amendment(
    root: str | Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock = system_utc_now,
) -> Mapping[str, Any]:
    """Freeze exact integration/review bytes using the trusted UTC clock."""

    root_path = Path(root).resolve()
    with _state_lock(root_path):
        state, state_bytes, chain, audit = _read_amended_state_locked(
            root_path,
            config,
            clock=clock,
        )
        assert_operation_permitted(state, "freeze-amendment")
        amendment = state["amendment"]
        if amendment["status"] != "draft":
            raise ValueError("amendment 0001 is already frozen")
        authority = _phase0_authority(
            root_path,
            _legacy_projection(state),
            config,
            clock=clock,
        )
        phase0 = authority.freeze
        research = _load_bound_research_journal(root_path, config, state)
        draft, draft_bytes = read_json_file(root_path / AMENDMENT_DRAFT_PATH, "amendment draft")
        _validate_draft(draft)
        draft_sha = _sha256_bytes(draft_bytes)
        draft_commit = unique_first_add_commit(
            root_path,
            AMENDMENT_DRAFT_PATH,
            draft_bytes,
            require_direct_parent=state["amendment"]["hold_notice_commit"],
        )
        draft_commit_time = git_commit_time(root_path, draft_commit, "amendment draft commit time")
        if draft_commit_time < _utc(draft["created_at_utc"], "draft creation time"):
            raise ValueError("amendment draft commit cannot predate draft activation")
        if draft_commit_time > trusted_now(clock):
            raise ValueError("amendment draft commit cannot be future-dated")
        files = _amendment_file_hashes(root_path)
        if files != draft["amendment_files"]:
            raise ValueError("amendment draft bytes changed before organizer review/freeze")
        amendment_commit = _committed_amendment_files(
            root_path,
            files,
            authority,
            clock=clock,
        )
        required_backfills = _required_backfill_bindings(root_path, research)
        integration = _integration_manifest(
            authority=authority,
            draft_sha256=draft_sha,
            implementation_commit=amendment_commit,
            amendment_files=files,
            required_backfills=required_backfills,
        )
        integration_bytes = _json_bytes(integration)
        integration_sha = _sha256_bytes(integration_bytes)
        review, review_bytes, review_commit = _load_committed_review(
            root_path,
            draft_commit=draft_commit,
            clock=clock,
        )
        if (
            review["draft_sha256"] != draft_sha
            or review["phase0_freeze_sha256"] != amendment["phase0_freeze_sha256"]
            or dict(review["amendment_files"]) != files
            or review["integration_manifest_sha256"] != integration_sha
            or review["required_backfills"] != required_backfills
            or review["score_calculation_implemented"] is not True
        ):
            raise ValueError(
                "organizer review differs from exact draft/Phase-0/integration/backfill bytes"
            )
        reviewed_at = _utc(review["reviewed_at_utc"], "review time")
        if reviewed_at < _utc(draft["created_at_utc"], "draft creation time"):
            raise ValueError("organizer review cannot precede the amendment draft")
        if reviewed_at > trusted_now(clock):
            raise ValueError("organizer review cannot be future-dated")
        frozen_now = trusted_now(clock).isoformat().replace("+00:00", "Z")
        frozen_text = bounded_event_time(
            frozen_now,
            "amendment freeze time",
            lower_bounds=(
                ("hold start", state["administrative_hold"]["started_at_utc"]),
                ("organizer review time", review["reviewed_at_utc"]),
                ("amendment chain head time", chain.records[-1]["timestamp_utc"]),
                ("organizer audit head time", audit.records[-1]["timestamp_utc"]),
                ("research journal head time", research.last_timestamp_utc),
                ("Phase-0 record commit time", authority.record_commit_time_utc),
            ),
            clock=clock,
        )
        for relative in (INTEGRATION_MANIFEST_PATH, AMENDMENT_FREEZE_PATH):
            require_no_git_history(root_path, relative)
            path = root_path / relative
            if path.exists() or path.is_symlink():
                raise ValueError(f"amendment freeze path already exists: {relative}")
        freeze: dict[str, Any] = {
            "schema_version": 1,
            "amendment_id": AMENDMENT_ID,
            "status": "frozen",
            "frozen_at_utc": frozen_text,
            "phase0_freeze_path": TOP40_V2_LAYOUT.phase0_freeze_path,
            "phase0_freeze_sha256": amendment["phase0_freeze_sha256"],
            "phase0_common_commit": phase0["common_freeze_commit"],
            "draft_path": AMENDMENT_DRAFT_PATH,
            "draft_sha256": draft_sha,
            "chain_parent_sha256": chain.head_sha256,
            "amendment_commit": amendment_commit,
            "amendment_files": files,
            "integration_manifest_path": INTEGRATION_MANIFEST_PATH,
            "integration_manifest_sha256": integration_sha,
            "required_backfills": required_backfills,
            "review_path": AMENDMENT_REVIEW_PATH,
            "review_commit": review_commit,
            "review": dict(review),
            "review_input_sha256": _sha256_bytes(review_bytes),
            "score_calculation_implemented": True,
        }
        _validate_freeze(freeze)
        freeze_bytes = _json_bytes(freeze)
        freeze_sha = _sha256_bytes(freeze_bytes)
        chain_path = root_path / AMENDMENT_CHAIN_PATH
        chain_bytes = chain_path.read_bytes()
        replacement_chain, new_chain, _event = _append_chain(
            chain_bytes,
            event_type="amendment_frozen",
            timestamp_utc=frozen_text,
            payload={
                "draft_sha256": draft_sha,
                "freeze_path": AMENDMENT_FREEZE_PATH,
                "freeze_sha256": freeze_sha,
                "amendment_commit": amendment_commit,
                "review_sha256": _sha256_bytes(review_bytes),
                "integration_manifest_sha256": integration_sha,
                "score_calculation_implemented": True,
            },
        )
        replacement_state = copy.deepcopy(state)
        replacement_state["amendment"].update(
            {
                "status": "frozen",
                "lifecycle_status": FROZEN_LIFECYCLE_STATUS,
                "review_sha256": _sha256_bytes(review_bytes),
                "review_commit": review_commit,
                "freeze_path": AMENDMENT_FREEZE_PATH,
                "freeze_sha256": freeze_sha,
                "integration_manifest_sha256": integration_sha,
                "chain": new_chain.binding,
            }
        )
        validate_amended_run_state(replacement_state, config)
        _publish_transaction(
            root_path,
            (
                _Change(
                    root_path / INTEGRATION_MANIFEST_PATH,
                    None,
                    integration_bytes,
                ),
                _Change(root_path / AMENDMENT_FREEZE_PATH, None, freeze_bytes),
                _Change(chain_path, chain_bytes, replacement_chain),
                _Change(
                    root_path / TOP40_V2_LAYOUT.state_path,
                    state_bytes,
                    _json_bytes(replacement_state),
                ),
            ),
        )
    return freeze


def _load_bound_research_journal(
    root: Path, config: LoadedV2Config, state: Mapping[str, Any]
) -> JournalState:
    binding = state.get("research_journal")
    if not isinstance(binding, Mapping):
        raise ValueError("diagnostic reservation requires the organizer research journal")
    relative = binding.get("path")
    if relative != TOP40_V2_LAYOUT.organizer_journal_path:
        raise ValueError("research journal path is noncanonical")
    _normalized, _path, journal_bytes, _stat = read_repo_file(
        root,
        relative,
        "organizer research journal",
        maximum_bytes=32 * 1024 * 1024,
    )
    journal = validate_journal_bytes(journal_bytes, _research_policy(config))
    expected = {
        "path": TOP40_V2_LAYOUT.organizer_journal_path,
        "genesis_sha256": journal.genesis_sha256,
        "head_sha256": journal.head_sha256,
        "record_count": len(journal.records),
    }
    if dict(binding) != expected:
        raise ValueError("research journal differs from run-state binding")
    for team_id in TEAM_IDS:
        if state["teams"][team_id]["trial_count"] != journal.teams[team_id].material_trial_count:
            raise ValueError("team trial counts differ from organizer research accounting")
        ledger_relative = f"{TOP40_V2_LAYOUT.team_root(team_id)}/experiments.jsonl"
        _ledger_relative, _ledger_path, ledger_bytes, _ledger_stat = read_repo_file(
            root,
            ledger_relative,
            f"{team_id} trial ledger",
            maximum_bytes=32 * 1024 * 1024,
            require_single_link=True,
        )
        validate_team_ledger_bytes(ledger_bytes, journal, team_id)
    return journal


def _trial_result_record_sha256(
    journal: JournalState,
    team_id: str,
    candidate_id: str,
) -> str:
    matches = [
        record
        for record in journal.records
        if record["event_type"] == "trial_result"
        and record["payload"]["team_id"] == team_id
        and record["payload"]["candidate_id"] == candidate_id
    ]
    if len(matches) != 1:
        raise ValueError("completed candidate must have one exact trial-result journal record")
    return _sha256(matches[0]["record_sha256"], "trial-result record SHA-256")


def _canonical_development_bindings(
    root: Path,
    journal: JournalState,
    team_id: str,
    candidate_id: str,
) -> Mapping[str, Any]:
    target_filename = CURRENT_INTEGRATION_BOUNDARY.development_target_filename
    if target_filename is None or PurePosixPath(target_filename).name != target_filename:
        raise ValueError("diagnostic engine has no frozen canonical development target name")
    accounting = journal.teams[team_id]
    result = accounting.results.get(candidate_id)
    if not isinstance(result, Mapping) or result.get("status") != "completed":
        raise ValueError("diagnostic candidate has no completed development result")
    artifacts = result.get("artifact_hashes")
    if not isinstance(artifacts, Mapping):
        raise ValueError("completed development result lacks artifact hashes")
    target_path = (
        f"{TOP40_V2_LAYOUT.report_root(team_id)}/development-runs/{candidate_id}/{target_filename}"
    )
    runner_path = (
        f"{TOP40_V2_LAYOUT.report_root(team_id)}/qualification-attempts/"
        f"{candidate_id}.runner-record.json"
    )
    for relative, label in (
        (target_path, "canonical development target"),
        (runner_path, "canonical development runner record"),
    ):
        expected = artifacts.get(relative)
        if not isinstance(expected, str) or _SHA256.fullmatch(expected) is None:
            raise ValueError(f"completed result does not bind its {label}")
        _normalized, _path, payload, _stat = read_repo_file(root, relative, label)
        if _sha256_bytes(payload) != expected:
            raise ValueError(f"{label} differs from completed result artifact hashes")
    return {
        "trial_result_record_sha256": _trial_result_record_sha256(
            journal,
            team_id,
            candidate_id,
        ),
        "development_target_path": target_path,
        "development_target_sha256": artifacts[target_path],
        "runner_record_path": runner_path,
        "runner_record_sha256": artifacts[runner_path],
    }


def _validate_reservation_authority(
    root: Path,
    config: LoadedV2Config,
    state: Mapping[str, Any],
    journal: JournalState,
    payload: Mapping[str, Any],
) -> None:
    team_id = str(payload["team_id"])
    candidate_id = str(payload["candidate_id"])
    accounting = journal.teams[team_id]
    registration = accounting.registrations.get(candidate_id)
    result = accounting.results.get(candidate_id)
    registration_sha = accounting.registration_sha256.get(candidate_id)
    if (
        not isinstance(registration, Mapping)
        or not isinstance(result, Mapping)
        or result.get("status") != "completed"
        or not isinstance(registration_sha, str)
    ):
        raise ValueError("diagnostic reservation candidate is no longer authoritative")
    _phase0_relative, _phase0_path, phase0_bytes, _phase0_stat = read_repo_file(
        root,
        TOP40_V2_LAYOUT.phase0_freeze_path,
        "Phase-0 freeze",
    )
    phase0 = _strict_json_bytes(phase0_bytes, "Phase-0 freeze")
    development = _canonical_development_bindings(
        root,
        journal,
        team_id,
        candidate_id,
    )
    expected = {
        "candidate_registration_sha256": registration_sha,
        "strategy_sha256": registration["strategy_sha256"],
        "source_bundle_sha256": registration["source_bundle_sha256"],
        "risk_policy_sha256": registration["risk_config_sha256"],
        "config_sha256": config.sha256,
        "candidate_seed": registration["seed"],
        "runner_seed": config.raw["research_budget"]["strategy_seed"],
        "snapshot_manifest_path": phase0["shared_snapshot_manifest_path"],
        "snapshot_manifest_sha256": phase0["shared_snapshot_manifest_sha256"],
        **development,
        "amendment_freeze_sha256": state["amendment"]["freeze_sha256"],
    }
    if any(payload[field] != value for field, value in expected.items()):
        raise ValueError("diagnostic reservation differs from its authoritative bindings")


def reserve_diagnostic_backfill(
    root: str | Path,
    config: LoadedV2Config,
    *,
    diagnostic_id: str,
    team_id: str,
    candidate_id: str,
    clock: UtcClock = system_utc_now,
) -> Mapping[str, Any]:
    """Append one non-material, organizer-private, one-shot reservation."""

    root_path = Path(root).resolve()
    if _DIAGNOSTIC_ID.fullmatch(diagnostic_id) is None:
        raise ValueError("diagnostic_id must be lowercase safe text of at most 128 chars")
    TOP40_V2_LAYOUT.require_team(team_id)
    candidate = _nonempty(candidate_id, "candidate_id", maximum=128)
    with _state_lock(root_path):
        state, state_bytes, chain, audit = _read_amended_state_locked(
            root_path,
            config,
            clock=clock,
        )
        _require_integration_ready(state, "reserve-diagnostic-backfill")
        assert_operation_permitted(state, "reserve-diagnostic-backfill")
        if state["amendment"]["status"] != "frozen":
            raise ValueError("diagnostic reservations require the reviewed amendment freeze")
        if state["phase"] != "research":
            raise ValueError("diagnostic backfill amendment applies only to the research phase")
        journal = _load_bound_research_journal(root_path, config, state)
        accounting = journal.teams[team_id]
        registration = accounting.registrations.get(candidate)
        result = accounting.results.get(candidate)
        registration_sha = accounting.registration_sha256.get(candidate)
        if (
            not isinstance(registration, Mapping)
            or not isinstance(result, Mapping)
            or result.get("status") != "completed"
            or not isinstance(registration_sha, str)
        ):
            raise ValueError("diagnostic backfill requires one completed registered candidate")
        if registration["config_sha256"] != config.sha256:
            raise ValueError("diagnostic candidate differs from the frozen V2 config")
        freeze, _freeze_bytes = read_json_file(
            root_path / AMENDMENT_FREEZE_PATH, "amendment freeze"
        )
        requested_time = trusted_now(clock).isoformat().replace("+00:00", "Z")
        timestamp = bounded_event_time(
            requested_time,
            "diagnostic reservation time",
            lower_bounds=(
                ("amendment freeze time", freeze["frozen_at_utc"]),
                ("amendment chain head time", chain.records[-1]["timestamp_utc"]),
                ("organizer audit head time", audit.records[-1]["timestamp_utc"]),
                ("research journal head time", journal.last_timestamp_utc),
                ("administrative hold start", state["administrative_hold"]["started_at_utc"]),
            ),
            clock=clock,
        )
        _phase0_relative, _phase0_path, phase0_bytes, _phase0_stat = read_repo_file(
            root_path,
            TOP40_V2_LAYOUT.phase0_freeze_path,
            "Phase-0 freeze",
        )
        phase0 = _strict_json_bytes(phase0_bytes, "Phase-0 freeze")
        development = _canonical_development_bindings(
            root_path,
            journal,
            team_id,
            candidate,
        )
        identity = {
            "diagnostic_kind": DIAGNOSTIC_KIND,
            "team_id": team_id,
            "candidate_id": candidate,
            "amendment_freeze_sha256": state["amendment"]["freeze_sha256"],
        }
        reservation_key = _sha256_bytes(_canonical_json_bytes(identity))
        if diagnostic_id in audit.reservations or any(
            event["payload"]["reservation_key_sha256"] == reservation_key
            for event in audit.reservations.values()
        ):
            raise ValueError("candidate already has a one-shot diagnostic reservation")
        payload = {
            "diagnostic_id": diagnostic_id,
            "diagnostic_kind": DIAGNOSTIC_KIND,
            "team_id": team_id,
            "candidate_id": candidate,
            "candidate_registration_sha256": registration_sha,
            "strategy_sha256": registration["strategy_sha256"],
            "source_bundle_sha256": registration["source_bundle_sha256"],
            "risk_policy_sha256": registration["risk_config_sha256"],
            "config_sha256": registration["config_sha256"],
            "candidate_seed": registration["seed"],
            "runner_seed": config.raw["research_budget"]["strategy_seed"],
            "snapshot_manifest_path": phase0["shared_snapshot_manifest_path"],
            "snapshot_manifest_sha256": phase0["shared_snapshot_manifest_sha256"],
            **development,
            "amendment_freeze_sha256": state["amendment"]["freeze_sha256"],
            "reservation_key_sha256": reservation_key,
            "non_material": True,
            "charges_team_trial_budget": False,
        }
        _validate_reservation_payload(payload)
        integration = _bound_integration_manifest(root_path, state)
        if state["administrative_hold"]["active"] is True:
            required = {
                str(item["diagnostic_id"]): item
                for item in integration["required_backfills"]
            }
            expected = required.get(diagnostic_id)
            if expected is None:
                raise ValueError(
                    "while the hold is active, only an exact required backfill may be reserved"
                )
            for field, value in expected.items():
                if payload[field] != value:
                    raise ValueError(
                        "required diagnostic reservation differs from the integration freeze"
                    )
        audit_path = root_path / ORGANIZER_AUDIT_PATH
        _audit_relative, _audit_safe_path, audit_bytes, _audit_stat = read_repo_file(
            root_path,
            ORGANIZER_AUDIT_PATH,
            "organizer audit",
        )
        replacement_audit, new_audit, event = _append_audit(
            audit_bytes,
            event_type="diagnostic_backfill_reserved",
            timestamp_utc=timestamp,
            payload=payload,
        )
        replacement_state = copy.deepcopy(state)
        replacement_state["organizer_audit"] = new_audit.binding
        validate_amended_run_state(replacement_state, config)
        _publish_transaction(
            root_path,
            (
                _Change(audit_path, audit_bytes, replacement_audit),
                _Change(
                    root_path / TOP40_V2_LAYOUT.state_path,
                    state_bytes,
                    _json_bytes(replacement_state),
                ),
            ),
        )
    return event


def _bound_integration_manifest(
    root: Path,
    state: Mapping[str, Any],
) -> Mapping[str, Any]:
    _relative, _path, payload, _stat = read_repo_file(
        root,
        INTEGRATION_MANIFEST_PATH,
        "bound integration manifest",
        maximum_bytes=4 * 1024 * 1024,
        require_single_link=True,
    )
    manifest = _strict_json_bytes(payload, "bound integration manifest")
    _validate_integration_manifest(manifest)
    if (
        pretty_json_bytes(manifest) != payload
        or _sha256_bytes(payload) != state["amendment"]["integration_manifest_sha256"]
    ):
        raise ValueError("integration manifest differs from frozen amendment state")
    return manifest


def _normalize_trusted_runner_result(raw: object) -> dict[str, Any]:
    result = _exact_object(
        raw,
        {
            "status",
            "failure_reason",
            "organizer_cpu_hours",
            "organizer_wall_clock_hours",
        },
        "trusted diagnostic runner result",
    )
    status = result["status"]
    failure = result["failure_reason"]
    if status not in {"completed", "failed", "interrupted"}:
        raise ValueError("trusted diagnostic runner returned an invalid status")
    if status == "completed":
        if failure is not None:
            raise ValueError("completed trusted diagnostic run cannot claim a failure")
    elif (
        not isinstance(failure, str)
        or not failure.strip()
        or failure != failure.strip()
        or len(failure) > 8000
    ):
        raise ValueError("failed trusted diagnostic run requires a bounded reason")
    return {
        "status": status,
        "failure_reason": failure,
        "organizer_cpu_hours": _finite_nonnegative(
            result["organizer_cpu_hours"],
            "trusted organizer_cpu_hours",
        ),
        "organizer_wall_clock_hours": _finite_nonnegative(
            result["organizer_wall_clock_hours"],
            "trusted organizer_wall_clock_hours",
        ),
    }


def _completed_diagnostic_evidence(
    root: Path,
    reservation: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, bool]]:
    reservation_payload = reservation["payload"]
    team_id = str(reservation_payload["team_id"])
    diagnostic_id = str(reservation_payload["diagnostic_id"])
    artifacts = collect_private_artifacts(
        root,
        team_id,
        diagnostic_id,
        REQUIRED_PRIVATE_ARTIFACT_NAMES,
    )
    hashes = {artifact.logical_name: artifact.sha256 for artifact in artifacts}
    summary_bytes = read_private_artifact_bytes(
        root,
        team_id,
        diagnostic_id,
        "diagnostic-summary.json",
    )
    if _sha256_bytes(summary_bytes) != hashes["diagnostic-summary.json"]:
        raise ValueError("private diagnostic summary changed while it was read")
    summary = _strict_json_bytes(summary_bytes, "private diagnostic summary")
    _exact_object(
        summary,
        {
            "schema_version",
            "diagnostic_id",
            "reservation_sha256",
            "status",
            "replay",
            "score_ic",
        },
        "private diagnostic summary",
    )
    if (
        pretty_json_bytes(summary) != summary_bytes
        or summary["schema_version"] != 1
        or summary["diagnostic_id"] != diagnostic_id
        or summary["reservation_sha256"] != reservation["record_sha256"]
        or summary["status"] != "completed"
    ):
        raise ValueError("private diagnostic summary identity or encoding is invalid")
    # Keep one reviewed derivation/validation implementation for the public disclosure. This
    # rejects out-of-range correlations and inconsistent null/count combinations before the
    # lifecycle commits any result booleans.
    from crypto_trade.tournament.score_diagnostics_v2 import trusted_boolean_verdict

    outcomes = dict(trusted_boolean_verdict(summary_bytes))
    if set(outcomes) != set(DIAGNOSTIC_OUTCOME_FIELDS) or any(
        type(value) is not bool for value in outcomes.values()
    ):
        raise ValueError("trusted score diagnostic returned invalid public outcomes")
    return hashes, outcomes


def _run_diagnostic_backfill_once(
    root: str | Path,
    config: LoadedV2Config,
    *,
    diagnostic_id: str,
    clock: UtcClock = system_utc_now,
) -> Mapping[str, Any]:
    """Run one reservation and record only trusted accounting and derived booleans."""

    root_path = Path(root).resolve()
    with _state_lock(root_path):
        state, _state_bytes, _chain, audit = _read_amended_state_locked(
            root_path,
            config,
            clock=clock,
        )
        _require_integration_ready(state, "run-diagnostic-backfill")
        assert_operation_permitted(state, "run-diagnostic-backfill")
        reservation = audit.reservations.get(diagnostic_id)
        if reservation is None or diagnostic_id in audit.results:
            raise ValueError("diagnostic run requires one unused reservation")
        research = _load_bound_research_journal(root_path, config, state)
        _validate_reservation_authority(
            root_path,
            config,
            state,
            research,
            reservation["payload"],
        )
        trusted_reservation = copy.deepcopy(reservation)
        private_output_dir = private_artifact_directory(
            root_path,
            str(reservation["payload"]["team_id"]),
            diagnostic_id,
            create=True,
        )
    from crypto_trade.tournament.score_diagnostics_v2 import (
        run_reserved_score_diagnostic,
    )

    runner_result = _normalize_trusted_runner_result(
        run_reserved_score_diagnostic(
            root=root_path,
            reservation=trusted_reservation,
            private_output_dir=private_output_dir,
        )
    )
    with _state_lock(root_path):
        state, state_bytes, chain, audit = _read_amended_state_locked(
            root_path,
            config,
            clock=clock,
        )
        _require_integration_ready(state, "run-diagnostic-backfill")
        assert_operation_permitted(state, "run-diagnostic-backfill")
        reservation = audit.reservations.get(diagnostic_id)
        if (
            reservation is None
            or diagnostic_id in audit.results
            or reservation["record_sha256"] != trusted_reservation["record_sha256"]
        ):
            raise ValueError("diagnostic reservation changed while its trusted runner executed")
        research = _load_bound_research_journal(root_path, config, state)
        _validate_reservation_authority(
            root_path,
            config,
            state,
            research,
            reservation["payload"],
        )
        recorded_now = trusted_now(clock).isoformat().replace("+00:00", "Z")
        timestamp = bounded_event_time(
            recorded_now,
            "diagnostic result time",
            lower_bounds=(
                ("diagnostic reservation time", reservation["timestamp_utc"]),
                ("amendment chain head time", chain.records[-1]["timestamp_utc"]),
                ("organizer audit head time", audit.records[-1]["timestamp_utc"]),
                ("research journal head time", research.last_timestamp_utc),
                ("administrative hold start", state["administrative_hold"]["started_at_utc"]),
            ),
            clock=clock,
        )
        if runner_result["status"] == "completed":
            artifact_hashes, diagnostic_outcomes = _completed_diagnostic_evidence(
                root_path,
                reservation,
            )
        else:
            artifact_hashes = {}
            diagnostic_outcomes = None
        payload = {
            "diagnostic_id": diagnostic_id,
            "reservation_sha256": reservation["record_sha256"],
            "status": runner_result["status"],
            "failure_reason": runner_result["failure_reason"],
            "artifact_hashes": artifact_hashes,
            "diagnostic_outcomes": diagnostic_outcomes,
            "organizer_cpu_hours": runner_result["organizer_cpu_hours"],
            "organizer_wall_clock_hours": runner_result["organizer_wall_clock_hours"],
            "non_material": True,
            "team_material_trial_delta": 0,
            "team_cpu_hours_delta": 0.0,
            "team_wall_clock_hours_delta": 0.0,
        }
        _validate_result_payload(payload)
        audit_path = root_path / ORGANIZER_AUDIT_PATH
        _audit_relative, _audit_safe_path, audit_bytes, _audit_stat = read_repo_file(
            root_path,
            ORGANIZER_AUDIT_PATH,
            "organizer audit",
        )
        replacement_audit, new_audit, event = _append_audit(
            audit_bytes,
            event_type="diagnostic_backfill_recorded",
            timestamp_utc=timestamp,
            payload=payload,
        )
        before_teams = _canonical_json_bytes(state["teams"])
        before_research = _canonical_json_bytes(state["research_journal"])
        replacement_state = copy.deepcopy(state)
        replacement_state["organizer_audit"] = new_audit.binding
        if (
            _canonical_json_bytes(replacement_state["teams"]) != before_teams
            or _canonical_json_bytes(replacement_state["research_journal"]) != before_research
        ):
            raise AssertionError("diagnostic accounting mutated team research budgets")
        validate_amended_run_state(replacement_state, config)
        _publish_transaction(
            root_path,
            (
                _Change(audit_path, audit_bytes, replacement_audit),
                _Change(
                    root_path / TOP40_V2_LAYOUT.state_path,
                    state_bytes,
                    _json_bytes(replacement_state),
                ),
            ),
        )
    return event


def run_diagnostic_backfill(
    root: str | Path,
    config: LoadedV2Config,
    *,
    diagnostic_id: str,
    clock: UtcClock = system_utc_now,
) -> Mapping[str, Any]:
    """Serialize, run, and record one trusted diagnostic reservation."""

    root_path = Path(root).resolve()
    with _diagnostic_execution_lock(root_path, diagnostic_id):
        return _run_diagnostic_backfill_once(
            root_path,
            config,
            diagnostic_id=diagnostic_id,
            clock=clock,
        )


def resume_amendment_hold(
    root: str | Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock = system_utc_now,
) -> Mapping[str, Any]:
    """Resume after review/backfills and toll the common deadline by the exact hold duration."""

    root_path = Path(root).resolve()
    with _state_lock(root_path):
        state, state_bytes, chain, audit = _read_amended_state_locked(
            root_path,
            config,
            clock=clock,
        )
        _require_integration_ready(state, "resume-amendment")
        assert_operation_permitted(state, "resume-amendment")
        if state["amendment"]["status"] != "frozen":
            raise ValueError("hold resume requires the reviewed amendment freeze")
        if state["administrative_hold"]["active"] is not True:
            raise ValueError("amendment hold has already resumed")
        pending = sorted(set(audit.reservations) - set(audit.results))
        if pending:
            raise ValueError(f"hold cannot resume with open diagnostic reservations: {pending}")
        integration = _bound_integration_manifest(root_path, state)
        required_ids = {
            str(item["diagnostic_id"]) for item in integration["required_backfills"]
        }
        missing_reservations = sorted(required_ids - set(audit.reservations))
        missing_results = sorted(required_ids - set(audit.results))
        if missing_reservations or missing_results:
            raise ValueError(
                "hold cannot resume before every integration-bound required backfill is "
                f"terminal; missing_reservations={missing_reservations}, "
                f"missing_results={missing_results}"
            )
        hold = state["administrative_hold"]
        start = _utc(hold["started_at_utc"], "hold start")
        research = _load_bound_research_journal(root_path, config, state)
        resumed_now = trusted_now(clock).isoformat().replace("+00:00", "Z")
        resumed_text = bounded_event_time(
            resumed_now,
            "hold resume time",
            lower_bounds=(
                ("hold start", hold["started_at_utc"]),
                ("amendment chain head time", chain.records[-1]["timestamp_utc"]),
                ("organizer audit head time", audit.records[-1]["timestamp_utc"]),
                ("research journal head time", research.last_timestamp_utc),
            ),
            clock=clock,
        )
        resumed = _utc(resumed_text, "hold resume")
        audit_head_time = _utc(audit.records[-1]["timestamp_utc"], "organizer audit head time")
        if resumed < audit_head_time:
            raise ValueError("hold resume cannot precede the organizer audit head")
        duration = _duration_microseconds(start, resumed)
        if duration < 1:
            raise ValueError("administrative hold duration must be positive")
        baseline = _utc(hold["baseline_research_deadline_utc"], "baseline deadline")
        effective = (baseline + timedelta(microseconds=duration)).isoformat().replace("+00:00", "Z")
        chain_path = root_path / AMENDMENT_CHAIN_PATH
        chain_bytes = chain_path.read_bytes()
        replacement_chain, new_chain, event = _append_chain(
            chain_bytes,
            event_type="administrative_hold_resumed",
            timestamp_utc=resumed_text,
            payload={
                "freeze_sha256": state["amendment"]["freeze_sha256"],
                "hold_duration_microseconds": duration,
                "effective_research_deadline_utc": effective,
            },
        )
        replacement_state = copy.deepcopy(state)
        replacement_state["amendment"]["chain"] = new_chain.binding
        replacement_state["administrative_hold"].update(
            {
                "active": False,
                "resumed_at_utc": resumed_text,
                "hold_duration_microseconds": duration,
                "cumulative_toll_microseconds": duration,
                "effective_research_deadline_utc": effective,
            }
        )
        validate_amended_run_state(replacement_state, config)
        _publish_transaction(
            root_path,
            (
                _Change(chain_path, chain_bytes, replacement_chain),
                _Change(
                    root_path / TOP40_V2_LAYOUT.state_path,
                    state_bytes,
                    _json_bytes(replacement_state),
                ),
            ),
        )
    return {
        "event": event,
        "hold_duration_microseconds": duration,
        "effective_research_deadline_utc": effective,
    }


def amendment_status(
    root: str | Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock = system_utc_now,
) -> Mapping[str, Any]:
    """Read-only status for legacy-before-draft or amendment-aware state."""

    root_path = Path(root).resolve()
    with _state_lock(root_path):
        _relative, _path, state_bytes, _stat = read_repo_file(
            root_path,
            TOP40_V2_LAYOUT.state_path,
            "Top-40 V2 run state",
        )
        raw = _strict_json_bytes(state_bytes, "Top-40 V2 run state")
        if raw.get("schema_version") == 2:
            if set(raw) != LEGACY_STATE_KEYS:
                raise ValueError("legacy run state has mixed-version keys")
            validate_run_state(raw, config)
            if _utc(raw["created_at_utc"], "run-state creation time") > trusted_now(clock):
                raise ValueError("run-state creation time cannot be future-dated")
            if raw["phase0"] is not None:
                _phase0_authority(root_path, raw, config, clock=clock)
                journal = _load_bound_research_journal(root_path, config, raw)
                if _utc(journal.last_timestamp_utc, "research journal head time") > trusted_now(
                    clock
                ):
                    raise ValueError("research journal head cannot be future-dated")
            return {
                "state_schema": "legacy-v2",
                "phase": raw["phase"],
                "amendment_activated": False,
                "administrative_hold_active": False,
                "lifecycle_status": "not_activated",
                "hold_notice_required": True,
                "post_draft_operations_enabled": False,
                "baseline_research_deadline_utc": _utc_text(
                    config.raw["research_budget"]["deadline_utc"], "research deadline"
                ),
            }
        state = _read_amended_state_locked(root_path, config, clock=clock)[0]
    hold = state["administrative_hold"]
    audit = state["organizer_audit"]
    return {
        "state_schema": AMENDMENT_STATE_SCHEMA_ID,
        "phase": state["phase"],
        "amendment_activated": True,
        "amendment_status": state["amendment"]["status"],
        "lifecycle_status": state["amendment"]["lifecycle_status"],
        "post_draft_operations_enabled": (
            state["amendment"]["status"] == "frozen" and hold["active"] is False
        ),
        "administrative_hold_active": hold["active"],
        "hold_started_at_utc": hold["started_at_utc"],
        "hold_reason": hold["reason"],
        "effective_research_deadline_utc": hold["effective_research_deadline_utc"],
        "diagnostic_reservation_count": audit["reservation_count"],
        "diagnostic_result_count": audit["result_count"],
        "organizer_cpu_hours": audit["organizer_cpu_hours"],
        "organizer_wall_clock_hours": audit["organizer_wall_clock_hours"],
    }
