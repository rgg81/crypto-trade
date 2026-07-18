"""Prospective sealed-validation activation for Top40 V3 Amendment 0002.

The parent organizer intentionally exposes no validation command.  This additive layer binds the
four GREEN IS candidates to their immutable training archives, consumes one opening validation
probe before any snapshot access, rehydrates the archived bytes into an organizer-only staging
root, and releases only fixed aggregate packets after the complete four-team cohort is terminal.
"""

from __future__ import annotations

import base64
import contextlib
import csv
import dataclasses
import datetime as dt
import hashlib
import io
import json
import math
import os
import re
import resource
import shutil
import stat
import subprocess
import time
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any

from crypto_trade.tournament import (
    coaching_v3,
    journal_v3,
    lab_v3,
    orchestrator_v3,
    phase0_v3,
    pure_crypto_universe_v6,
    runner_v3,
    source_archive_v3,
)
from crypto_trade.tournament import top40_amendment_0001_integration as amendment_0001
from crypto_trade.tournament.qualification_v3 import CandidateIdentity

SCHEMA_VERSION = 1
AMENDMENT_ID = "top40-v3-amendment-0002-sealed-validation"
AMENDMENT_ROOT = "tournament/top40-v3/amendments/0002"
AMENDMENT_POLICY_PATH = f"{AMENDMENT_ROOT}/AMENDMENT.md"
INTEGRATION_FREEZE_PATH = f"{AMENDMENT_ROOT}/integration-freeze.json"
COHORT_FREEZE_PATH = "tournament/top40-v3/is-cohort-freeze.json"
COHORT_FREEZE_SHA256 = "a32e0fe862e9a4579f51e7a13b21eb7a854e761f76e0524a591c424faf3e6365"
COHORT_FREEZE_COMMIT = "e69bf5ee5250c0e5776b68120e8ab4df601f4b97"
PARENT_INTEGRATION_FREEZE_SHA256 = (
    "563e3dbd6de3439c93cbf19c3efc14ec72ed1e322292becaf27b8b4beeb278be"
)
PARENT_INTEGRATION_FREEZE_COMMIT = "3bee33ae5ec074bb3f0cd769485584996dc0ac2e"
VALIDATION_JOURNAL_PATH = "tournament/top40-v3/validation-probe-journal.jsonl"
PRIVATE_VALIDATION_ROOT = "tournament/top40-v3/private/validation"
ACTIVE_SCRIPT_PATH = "scripts/top40_v3_amendment_0002.py"
INTEGRATION_MODULE_PATH = "src/crypto_trade/tournament/top40_amendment_0002_validation.py"
INTEGRATION_TEST_PATH = "tests/tournament/test_top40_amendment_0002_validation.py"
IMPLEMENTATION_PATHS = (
    INTEGRATION_MODULE_PATH,
    ACTIVE_SCRIPT_PATH,
    INTEGRATION_TEST_PATH,
    AMENDMENT_POLICY_PATH,
)
AMENDMENT_TEST_COMMAND = (
    "env",
    "PYTHONPATH=src",
    "PYTHONDONTWRITEBYTECODE=1",
    "uv",
    "run",
    "--frozen",
    "pytest",
    "-q",
    INTEGRATION_TEST_PATH,
)
OBSOLETE_PRETOURNAMENT_BUNDLE_TEST = "tests/tournament/test_v3_team_bundles.py"
BASE_TEST_COMMAND = tuple(
    item for item in phase0_v3.TARGETED_TEST_COMMAND if item != OBSOLETE_PRETOURNAMENT_BUNDLE_TEST
)
PARENT_AMENDMENT_TEST_COMMAND = tuple(
    item
    for item in amendment_0001.AMENDMENT_TEST_COMMAND
    if item != amendment_0001.INTEGRATION_TEST_PATH
)
VALIDATION_WINDOW = MappingProxyType(
    {
        "start_utc": "2022-07-01T00:00:00Z",
        "end_exclusive_utc": "2023-07-01T00:00:00Z",
    }
)
PACKET_SCHEMA_VERSION = "top40-v3-validation-aggregate-packet-v1"
JOURNAL_SCHEMA_VERSION = "top40-v3-validation-journal-v1"
GENESIS_SHA256 = "0" * 64
MAX_RECORD_BYTES = 1_048_576
MAX_TEST_OUTPUT_BYTES = 4 * 1024 * 1024

_SHA256 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_TEAM_ID = re.compile(r"team-(?:0[1-9]|10)")
_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
_TERMINAL_TYPES = frozenset({"succeeded", "failed", "aborted"})
_AUTHORIZATION_KEYS = frozenset(
    {
        "sequence",
        "team_id",
        "candidate_identity_sha256",
        "round_name",
        "team_round_probe_number",
        "team_total_probe_number",
        "comeback_eligible",
        "previous_record_sha256",
        "record_sha256",
    }
)
_IDENTITY_KEYS = frozenset(
    {
        "team_id",
        "candidate_id",
        "candidate_identity_sha256",
        "source_bundle_sha256",
        "strategy_sha256",
        "dependency_lock_sha256",
        "config_sha256",
        "risk_policy_sha256",
        "data_authority_sha256",
        "evaluator_sha256",
    }
)
_CHAIN_KEYS = frozenset(
    {
        "schema_version",
        "event_sequence",
        "previous_sha256",
        "record_sha256",
        "event_type",
    }
)
_ACCEPTED_KEYS = _CHAIN_KEYS | frozenset(
    {
        "team_id",
        "run_id",
        "candidate_id",
        "candidate_identity_sha256",
        "accepted_at_utc",
        "authorization",
        "cohort_freeze_sha256",
        "train_metric_packet_path",
        "train_metric_packet_sha256",
        "original_source_archive_path",
        "original_source_archive_sha256",
        "staging_source_archive_path",
        "staging_source_archive_sha256",
        "staging_candidate_root",
        "staging_entrypoint",
        "source_bundle_sha256",
        "strategy_sha256",
        "dependency_lock_sha256",
        "config_sha256",
        "risk_policy_sha256",
        "data_authority_sha256",
        "evaluator_sha256",
        "seed",
        "validation_window",
        "output_path",
        "replay_output_path",
    }
)
_TERMINAL_KEYS = _CHAIN_KEYS | frozenset(
    {
        "team_id",
        "run_id",
        "candidate_id",
        "candidate_identity_sha256",
        "request_sha256",
        "completed_at_utc",
        "cpu_seconds",
        "wall_seconds",
        "gate_vector",
        "aggregate_packet_path",
        "aggregate_packet_sha256",
        "artifact_hashes",
        "failure_reason",
    }
)
_RELEASE_KEYS = _CHAIN_KEYS | frozenset(
    {
        "released_at_utc",
        "cohort_freeze_sha256",
        "terminal_journal_head_sha256",
        "packet_sha256_by_team",
    }
)
_ADVANCER_KEYS = frozenset(
    {
        "rank",
        "team_id",
        "candidate_id",
        "candidate_identity_sha256",
        "source_bundle_sha256",
        "source_archive_path",
        "source_archive_sha256",
        "entrypoint",
        "train_run_id",
        "train_metric_packet_path",
        "train_metric_packet_sha256",
        "robustness_score",
        "train_metrics",
        "regime_sharpe",
    }
)
_COHORT_KEYS = frozenset(
    {
        "schema_version",
        "selected_at_utc",
        "selection_commit",
        "selection_rule",
        "authorities",
        "validation_source_policy",
        "advancers",
        "reserves",
    }
)
_FREEZE_KEYS = frozenset(
    {
        "schema_version",
        "amendment_id",
        "parent_amendment",
        "cohort",
        "train_boundary",
        "implementation",
        "base_suite",
        "parent_amendment_tests",
        "amendment_tests",
        "a6_report_sha256",
        "record_sha256",
    }
)


class Amendment0002ValidationError(orchestrator_v3.OrchestratorError):
    """The sealed-validation authority is absent, changed, or unsafe."""


@dataclasses.dataclass(frozen=True, slots=True)
class CohortCandidate:
    rank: int
    identity: CandidateIdentity
    entrypoint: str
    train_run_id: str
    train_metric_packet_path: str
    train_metric_packet_sha256: str
    source_archive_path: str
    source_archive_sha256: str
    source_archive: source_archive_v3.SourceArchive


@dataclasses.dataclass(frozen=True, slots=True)
class CohortAuthority:
    file_sha256: str
    commit: str
    selected_at_utc: str
    lab_journal_head_sha256: str
    candidates: tuple[CohortCandidate, ...]

    @property
    def by_team(self) -> Mapping[str, CohortCandidate]:
        return MappingProxyType(
            {candidate.identity.team_id: candidate for candidate in self.candidates}
        )


@dataclasses.dataclass(frozen=True, slots=True)
class ActivationAuthority:
    freeze_file_sha256: str
    freeze_commit: str
    record_sha256: str
    implementation_commit: str
    cohort_freeze_sha256: str
    cohort_freeze_commit: str


@dataclasses.dataclass(frozen=True, slots=True)
class ProvisionalActivationFreeze:
    freeze_file_sha256: str
    record_sha256: str
    implementation_commit: str
    activation: str = "pending-unique-freeze-commit"


@dataclasses.dataclass(frozen=True, slots=True)
class ValidationJournalState:
    records: tuple[Mapping[str, Any], ...]
    head_sha256: str
    ledger: lab_v3.ValidationLedgerState
    pending_request_sha256s: tuple[str, ...]
    terminal_request_sha256s: tuple[str, ...]
    release_record: Mapping[str, Any] | None

    @property
    def accepted_records(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(record for record in self.records if record["event_type"] == "probe_accepted")

    @property
    def terminal_records(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(record for record in self.records if record["event_type"] in _TERMINAL_TYPES)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_bytes(payload: object) -> bytes:
    try:
        return json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise Amendment0002ValidationError("payload is not finite canonical JSON") from exc


def _pretty_bytes(payload: object) -> bytes:
    try:
        return (
            json.dumps(payload, allow_nan=False, indent=2, sort_keys=True).encode("ascii") + b"\n"
        )
    except (TypeError, ValueError) as exc:
        raise Amendment0002ValidationError("payload is not finite pretty JSON") from exc


def _exact_mapping(value: object, keys: frozenset[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != set(keys):
        raise Amendment0002ValidationError(f"{label} has missing or unknown fields")
    return value


def _hash(value: object, label: str, *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise Amendment0002ValidationError(f"{label} must be a lowercase SHA-256")
    return value


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise Amendment0002ValidationError(f"{label} is not a safe identifier")
    return value


def _team(value: object) -> str:
    if not isinstance(value, str) or _TEAM_ID.fullmatch(value) is None:
        raise Amendment0002ValidationError("team_id must be team-01 through team-10")
    return value


def _safe_relative(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise Amendment0002ValidationError(f"{label} must be a POSIX relative path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise Amendment0002ValidationError(f"{label} is unsafe")
    return value


def _finite(value: object, label: str, *, nonnegative: bool = False) -> float:
    if isinstance(value, bool):
        raise Amendment0002ValidationError(f"{label} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise Amendment0002ValidationError(f"{label} must be numeric") from exc
    if not math.isfinite(result) or (nonnegative and result < 0.0):
        raise Amendment0002ValidationError(f"{label} is not a valid finite number")
    return result


def _timestamp(value: object, label: str) -> dt.datetime:
    if not isinstance(value, str) or _UTC.fullmatch(value) is None:
        raise Amendment0002ValidationError(f"{label} must be canonical UTC seconds")
    try:
        return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.UTC)
    except ValueError as exc:
        raise Amendment0002ValidationError(f"{label} is not a valid timestamp") from exc


def _utc_now() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _record_sha256(record: Mapping[str, Any]) -> str:
    unsigned = dict(record)
    unsigned.pop("record_sha256", None)
    return _sha256(_canonical_bytes(unsigned))


def _strict_json(payload: bytes, label: str) -> Mapping[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise Amendment0002ValidationError(f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    def reject(value: str) -> None:
        raise Amendment0002ValidationError(f"{label} contains nonfinite value {value}")

    try:
        value = json.loads(
            payload.decode("ascii"),
            object_pairs_hook=unique,
            parse_constant=reject,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Amendment0002ValidationError(f"{label} is not valid ASCII JSON") from exc
    if not isinstance(value, Mapping):
        raise Amendment0002ValidationError(f"{label} must be a JSON object")
    return value


def _identity_mapping(identity: CandidateIdentity) -> dict[str, str]:
    return {
        "team_id": identity.team_id,
        "candidate_id": identity.candidate_id,
        "candidate_identity_sha256": identity.sha256,
        "source_bundle_sha256": identity.source_bundle_sha256,
        "strategy_sha256": identity.strategy_sha256,
        "dependency_lock_sha256": identity.dependency_lock_sha256,
        "config_sha256": identity.config_sha256,
        "risk_policy_sha256": identity.risk_policy_sha256,
        "data_authority_sha256": identity.data_authority_sha256,
        "evaluator_sha256": identity.evaluator_sha256,
    }


def _identity_from_mapping(value: object, label: str) -> CandidateIdentity:
    raw = _exact_mapping(value, _IDENTITY_KEYS, label)
    identity = CandidateIdentity(
        team_id=_team(raw["team_id"]),
        candidate_id=_identifier(raw["candidate_id"], f"{label}.candidate_id"),
        source_bundle_sha256=str(_hash(raw["source_bundle_sha256"], "source_bundle_sha256")),
        strategy_sha256=str(_hash(raw["strategy_sha256"], "strategy_sha256")),
        dependency_lock_sha256=str(_hash(raw["dependency_lock_sha256"], "dependency_lock_sha256")),
        config_sha256=str(_hash(raw["config_sha256"], "config_sha256")),
        risk_policy_sha256=str(_hash(raw["risk_policy_sha256"], "risk_policy_sha256")),
        data_authority_sha256=str(_hash(raw["data_authority_sha256"], "data_authority_sha256")),
        evaluator_sha256=str(_hash(raw["evaluator_sha256"], "evaluator_sha256")),
    )
    if raw["candidate_identity_sha256"] != identity.sha256:
        raise Amendment0002ValidationError(f"{label} candidate identity hash is invalid")
    return identity


def _authorization_mapping(
    authorization: lab_v3.ValidationProbeAuthorization,
) -> dict[str, object]:
    return {
        "sequence": authorization.sequence,
        "team_id": authorization.team_id,
        "candidate_identity_sha256": authorization.candidate_identity_sha256,
        "round_name": authorization.round_name,
        "team_round_probe_number": authorization.team_round_probe_number,
        "team_total_probe_number": authorization.team_total_probe_number,
        "comeback_eligible": authorization.comeback_eligible,
        "previous_record_sha256": authorization.previous_record_sha256,
        "record_sha256": authorization.record_sha256,
    }


def _git(root: Path, arguments: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )


def _verified_commit(root: Path, commit: str, label: str) -> None:
    if not isinstance(commit, str) or _COMMIT.fullmatch(commit) is None:
        raise Amendment0002ValidationError(f"{label} must be a full lowercase commit")
    resolved = _git(root, ["rev-parse", "--verify", f"{commit}^{{commit}}"])
    if resolved.returncode != 0 or resolved.stdout.decode("ascii", "replace").strip() != commit:
        raise Amendment0002ValidationError(f"{label} is not a repository commit")
    if _git(root, ["merge-base", "--is-ancestor", commit, "HEAD"]).returncode != 0:
        raise Amendment0002ValidationError(f"{label} is not in current HEAD ancestry")


def _file_entry(root: Path, relative: str) -> dict[str, object]:
    payload = orchestrator_v3._read_regular_bytes(root, relative)
    return {"path": relative, "size": len(payload), "sha256": _sha256(payload)}


def _manifest_sha256(entries: Sequence[Mapping[str, object]]) -> str:
    return _sha256(_canonical_bytes([dict(entry) for entry in entries]))


def _implementation_entries(root: Path) -> tuple[dict[str, object], ...]:
    return tuple(_file_entry(root, relative) for relative in IMPLEMENTATION_PATHS)


def _verify_implementation_commit(
    root: Path,
    implementation_commit: str,
    entries: Sequence[Mapping[str, object]],
) -> None:
    _verified_commit(root, implementation_commit, "implementation_commit")
    parent = _git(root, ["rev-parse", f"{implementation_commit}^"])
    if (
        parent.returncode != 0
        or parent.stdout.decode("ascii", "replace").strip() != COHORT_FREEZE_COMMIT
    ):
        raise Amendment0002ValidationError(
            "implementation_commit must directly follow the cohort-freeze commit"
        )
    changed = _git(
        root, ["diff-tree", "--no-commit-id", "--name-status", "-r", implementation_commit]
    )
    expected = [f"A\t{relative}" for relative in sorted(IMPLEMENTATION_PATHS)]
    observed = sorted(changed.stdout.decode("utf-8", "replace").splitlines())
    if changed.returncode != 0 or observed != expected:
        raise Amendment0002ValidationError(
            "implementation_commit contains bytes outside the exact Amendment 0002 delta"
        )
    by_path = {str(entry["path"]): entry for entry in entries}
    for relative in IMPLEMENTATION_PATHS:
        additions = _git(root, ["log", "--diff-filter=A", "--format=%H", "--", relative])
        commits = [
            line for line in additions.stdout.decode("ascii", "replace").splitlines() if line
        ]
        if additions.returncode != 0 or commits != [implementation_commit]:
            raise Amendment0002ValidationError(
                f"implementation path was not uniquely added at implementation_commit: {relative}"
            )
        committed = _git(root, ["show", f"{implementation_commit}:{relative}"])
        expected_entry = by_path[relative]
        if (
            committed.returncode != 0
            or len(committed.stdout) != expected_entry["size"]
            or _sha256(committed.stdout) != expected_entry["sha256"]
        ):
            raise Amendment0002ValidationError(
                f"live implementation differs from implementation_commit: {relative}"
            )


def _verify_cohort_commit(root: Path, payload: bytes) -> None:
    _verified_commit(root, COHORT_FREEZE_COMMIT, "cohort freeze commit")
    additions = _git(root, ["log", "--diff-filter=A", "--format=%H", "--", COHORT_FREEZE_PATH])
    commits = [line for line in additions.stdout.decode("ascii", "replace").splitlines() if line]
    if additions.returncode != 0 or commits != [COHORT_FREEZE_COMMIT]:
        raise Amendment0002ValidationError("cohort freeze lacks one unique first-add commit")
    delta = _git(root, ["diff-tree", "--no-commit-id", "--name-status", "-r", COHORT_FREEZE_COMMIT])
    if delta.returncode != 0 or delta.stdout.decode("utf-8", "replace").splitlines() != [
        f"A\t{COHORT_FREEZE_PATH}"
    ]:
        raise Amendment0002ValidationError("cohort freeze commit has an unexpected delta")
    committed = _git(root, ["show", f"{COHORT_FREEZE_COMMIT}:{COHORT_FREEZE_PATH}"])
    if committed.returncode != 0 or committed.stdout != payload:
        raise Amendment0002ValidationError("live cohort freeze differs from its commit")


def _archive_file(archive: source_archive_v3.SourceArchive, relative: str) -> bytes:
    match = next((item for item in archive.files if item.path == relative), None)
    if match is None:
        raise Amendment0002ValidationError(f"source archive lacks required file: {relative}")
    return match.content


def _load_train_identity(packet: Mapping[str, Any]) -> CandidateIdentity:
    identity = _identity_from_mapping(packet.get("identity"), "training packet identity")
    if packet.get("schema_version") != coaching_v3.PACKET_SCHEMA_VERSION:
        raise Amendment0002ValidationError("training packet schema changed")
    if (
        packet.get("stage") != "train"
        or packet.get("packet_kind") != "train_coaching_metric_packet"
    ):
        raise Amendment0002ValidationError("selected packet is not a train coaching packet")
    return identity


def _verify_train_journal_binding(
    journal: journal_v3.JournalState,
    advancer: Mapping[str, Any],
    identity: CandidateIdentity,
) -> None:
    requests = [
        record
        for record in journal.records
        if record["event_type"] == "request_accepted"
        and record["run_id"] == advancer["train_run_id"]
    ]
    if len(requests) != 1:
        raise Amendment0002ValidationError("selected train run has no unique accepted request")
    request = requests[0]
    terminals = [
        record
        for record in journal.records
        if record["event_type"] == "succeeded"
        and record.get("request_sha256") == request["record_sha256"]
    ]
    expected_request = {
        "team_id": identity.team_id,
        "candidate_id": identity.candidate_id,
        "source_bundle_sha256": identity.source_bundle_sha256,
        "source_archive_path": advancer["source_archive_path"],
        "source_archive_sha256": advancer["source_archive_sha256"],
        "strategy_sha256": identity.strategy_sha256,
        "dependency_lock_sha256": identity.dependency_lock_sha256,
        "config_sha256": identity.config_sha256,
        "risk_policy_sha256": identity.risk_policy_sha256,
        "data_authority_sha256": identity.data_authority_sha256,
        "evaluator_sha256": identity.evaluator_sha256,
    }
    if any(request[field] != expected for field, expected in expected_request.items()):
        raise Amendment0002ValidationError("selected train request differs from candidate identity")
    if (
        len(terminals) != 1
        or terminals[0]["metric_packet_sha256"] != advancer["train_metric_packet_sha256"]
    ):
        raise Amendment0002ValidationError(
            "selected train request lacks its exact success terminal"
        )


def load_cohort(root: str | Path = ".") -> CohortAuthority:
    """Verify the immutable four-candidate IS cohort and all selected train evidence."""

    root_path = orchestrator_v3._trusted_root(root)
    parent = amendment_0001.verify_integration(root_path)
    if (
        parent.freeze_file_sha256 != PARENT_INTEGRATION_FREEZE_SHA256
        or parent.freeze_commit != PARENT_INTEGRATION_FREEZE_COMMIT
    ):
        raise Amendment0002ValidationError("parent Amendment 0001 authority changed")
    payload = orchestrator_v3._read_regular_bytes(root_path, COHORT_FREEZE_PATH)
    if _sha256(payload) != COHORT_FREEZE_SHA256:
        raise Amendment0002ValidationError("IS cohort freeze bytes changed")
    _verify_cohort_commit(root_path, payload)
    raw = _strict_json(payload, "IS cohort freeze")
    raw = _exact_mapping(raw, _COHORT_KEYS, "IS cohort freeze")
    if raw["schema_version"] != "top40-v3-is-cohort-freeze-v1":
        raise Amendment0002ValidationError("IS cohort schema is unsupported")
    _timestamp(raw["selected_at_utc"], "selected_at_utc")
    authorities = raw["authorities"]
    if not isinstance(authorities, Mapping):
        raise Amendment0002ValidationError("IS cohort authorities are malformed")
    exact_live_hashes = {
        "amendment_0001_integration_freeze_sha256": parent.freeze_file_sha256,
        "data_manifest_sha256": _sha256(
            orchestrator_v3._read_regular_bytes(root_path, orchestrator_v3.DATA_MANIFEST_PATH)
        ),
        "dependency_lock_sha256": _sha256(
            orchestrator_v3._read_regular_bytes(root_path, orchestrator_v3.DEPENDENCY_LOCK_PATH)
        ),
        "organizer_lab_journal_file_sha256": _sha256(
            orchestrator_v3._read_regular_bytes(root_path, orchestrator_v3.LAB_JOURNAL_PATH)
        ),
        "run_state_sha256": _sha256(
            orchestrator_v3._read_regular_bytes(root_path, orchestrator_v3.RUN_STATE_PATH)
        ),
        "tournament_config_sha256": _sha256(
            orchestrator_v3._read_regular_bytes(root_path, orchestrator_v3.CONFIG_PATH)
        ),
        "pure_crypto_audit_report_sha256": _sha256(
            pure_crypto_universe_v6.audit_report_bytes(root_path)
        ),
        "evaluator_sha256": amendment_0001.evaluator_authority_sha256(root_path),
    }
    if any(authorities.get(field) != digest for field, digest in exact_live_hashes.items()):
        raise Amendment0002ValidationError("IS cohort live authority binding changed")
    train_journal = journal_v3.replay_journal(root_path / orchestrator_v3.LAB_JOURNAL_PATH)
    if train_journal.pending_request_sha256s:
        raise Amendment0002ValidationError(
            "train journal has a pending request at validation activation"
        )
    if train_journal.head_sha256 != authorities.get("organizer_lab_journal_head_sha256"):
        raise Amendment0002ValidationError("IS cohort train-journal head changed")
    advancers = raw["advancers"]
    if not isinstance(advancers, list) or len(advancers) != 4:
        raise Amendment0002ValidationError("IS cohort must contain exactly four advancers")
    candidates: list[CohortCandidate] = []
    observed_teams: set[str] = set()
    for expected_rank, value in enumerate(advancers, start=1):
        advancer = _exact_mapping(value, _ADVANCER_KEYS, "IS cohort advancer")
        team_id = _team(advancer["team_id"])
        if advancer["rank"] != expected_rank or team_id in observed_teams:
            raise Amendment0002ValidationError("IS cohort rank or team uniqueness is invalid")
        observed_teams.add(team_id)
        packet_path = _safe_relative(advancer["train_metric_packet_path"], "train metric packet")
        packet_bytes = orchestrator_v3._read_regular_bytes(root_path, packet_path)
        if _sha256(packet_bytes) != advancer["train_metric_packet_sha256"]:
            raise Amendment0002ValidationError("selected train metric packet hash changed")
        packet = _strict_json(packet_bytes, "train metric packet")
        if coaching_v3.canonical_packet_bytes(packet) != packet_bytes:
            raise Amendment0002ValidationError("selected train metric packet is not canonical")
        identity = _load_train_identity(packet)
        packet_metrics = packet.get("scored_window", {}).get("metrics", {})
        expected_train_metrics = advancer["train_metrics"]
        if (
            identity.team_id != team_id
            or identity.candidate_id != advancer["candidate_id"]
            or identity.sha256 != advancer["candidate_identity_sha256"]
            or identity.source_bundle_sha256 != advancer["source_bundle_sha256"]
            or not isinstance(packet_metrics, Mapping)
            or any(
                packet_metrics.get(field) != expected_train_metrics[field]
                for field in (
                    "net_sharpe",
                    "annualized_return",
                    "max_drawdown",
                    "positive_quarter_fraction",
                )
            )
            or packet.get("double_cost_sharpe") != expected_train_metrics["double_cost_sharpe"]
            or not isinstance(packet.get("regime_sharpe"), Mapping)
            or any(
                abs(
                    float(packet["regime_sharpe"][regime])
                    - float(advancer["regime_sharpe"][regime])
                )
                > 1e-9
                for regime in ("bull", "bear", "chop", "stress")
            )
            or packet.get("training_assessment", {}).get("robustness_score")
            != advancer["robustness_score"]
            or packet.get("training_assessment", {}).get("status") != "GREEN"
        ):
            raise Amendment0002ValidationError("IS cohort differs from its train packet")
        archive = source_archive_v3.read_source_archive(
            root_path,
            _safe_relative(advancer["source_archive_path"], "source archive path"),
            str(_hash(advancer["source_archive_sha256"], "source archive sha256")),
            expected_team_id=team_id,
            expected_candidate_id=identity.candidate_id,
            expected_candidate_root=PurePosixPath(str(advancer["entrypoint"])).parent.as_posix(),
            expected_entrypoint=PurePosixPath(str(advancer["entrypoint"])).name,
            expected_source_bundle_sha256=identity.source_bundle_sha256,
        )
        if (
            _sha256(_archive_file(archive, archive.entrypoint)) != identity.strategy_sha256
            or _sha256(_archive_file(archive, "risk_policy.json")) != identity.risk_policy_sha256
        ):
            raise Amendment0002ValidationError(
                "source archive executable hashes differ from identity"
            )
        frozen_config = _strict_json(
            _archive_file(archive, "frozen_config.json"), "archived config"
        )
        if (
            frozen_config.get("team_id") != team_id
            or frozen_config.get("candidate_id") != identity.candidate_id
            or frozen_config.get("seed") != 20260718
            or not isinstance(frozen_config.get("implementation"), Mapping)
            or frozen_config["implementation"].get("entrypoint") != archive.entrypoint
        ):
            raise Amendment0002ValidationError("archived candidate config is inconsistent")
        _verify_train_journal_binding(train_journal, advancer, identity)
        candidates.append(
            CohortCandidate(
                rank=expected_rank,
                identity=identity,
                entrypoint=str(advancer["entrypoint"]),
                train_run_id=str(advancer["train_run_id"]),
                train_metric_packet_path=packet_path,
                train_metric_packet_sha256=str(advancer["train_metric_packet_sha256"]),
                source_archive_path=archive.path,
                source_archive_sha256=archive.sha256,
                source_archive=archive,
            )
        )
    if observed_teams != {"team-04", "team-05", "team-06", "team-09"}:
        raise Amendment0002ValidationError("IS cohort team set changed")
    return CohortAuthority(
        file_sha256=COHORT_FREEZE_SHA256,
        commit=COHORT_FREEZE_COMMIT,
        selected_at_utc=str(raw["selected_at_utc"]),
        lab_journal_head_sha256=train_journal.head_sha256,
        candidates=tuple(candidates),
    )


def _decode_journal_line(line: bytes, number: int) -> Mapping[str, Any]:
    if not line.endswith(b"\n") or line == b"\n" or len(line) - 1 > MAX_RECORD_BYTES:
        raise Amendment0002ValidationError(f"validation journal line {number} is invalid")
    record = _strict_json(line[:-1], f"validation journal line {number}")
    if _canonical_bytes(record) != line[:-1]:
        raise Amendment0002ValidationError("validation journal is not canonical JSONL")
    return record


def _accepted_identity(record: Mapping[str, Any]) -> CandidateIdentity:
    mapping = {
        "team_id": record["team_id"],
        "candidate_id": record["candidate_id"],
        "candidate_identity_sha256": record["candidate_identity_sha256"],
        "source_bundle_sha256": record["source_bundle_sha256"],
        "strategy_sha256": record["strategy_sha256"],
        "dependency_lock_sha256": record["dependency_lock_sha256"],
        "config_sha256": record["config_sha256"],
        "risk_policy_sha256": record["risk_policy_sha256"],
        "data_authority_sha256": record["data_authority_sha256"],
        "evaluator_sha256": record["evaluator_sha256"],
    }
    return _identity_from_mapping(mapping, "validation accepted identity")


def _validate_accepted(record: Mapping[str, Any]) -> CandidateIdentity:
    _exact_mapping(record, _ACCEPTED_KEYS, "probe_accepted")
    identity = _accepted_identity(record)
    _identifier(record["run_id"], "run_id")
    _timestamp(record["accepted_at_utc"], "accepted_at_utc")
    if record["cohort_freeze_sha256"] != COHORT_FREEZE_SHA256:
        raise Amendment0002ValidationError("accepted probe uses the wrong cohort freeze")
    for field in (
        "train_metric_packet_sha256",
        "original_source_archive_sha256",
        "staging_source_archive_sha256",
    ):
        _hash(record[field], field)
    for field in (
        "train_metric_packet_path",
        "original_source_archive_path",
        "staging_source_archive_path",
        "staging_candidate_root",
        "staging_entrypoint",
        "output_path",
        "replay_output_path",
    ):
        _safe_relative(record[field], field)
    if record["validation_window"] != dict(VALIDATION_WINDOW) or record["seed"] != 20260718:
        raise Amendment0002ValidationError("accepted probe window or seed changed")
    output_prefix = f"tournament/top40-v3/private/validation/{identity.team_id}/"
    if (
        not str(record["output_path"]).startswith(output_prefix)
        or not str(record["replay_output_path"]).startswith(output_prefix)
        or record["replay_output_path"] == record["output_path"]
    ):
        raise Amendment0002ValidationError("validation output escaped its private namespace")
    staging_prefix = f"tournament/top40-v3/teams/{identity.team_id}/.sealed-validation/"
    if not str(record["staging_candidate_root"]).startswith(staging_prefix):
        raise Amendment0002ValidationError("validation staging root escaped its team namespace")
    expected_entrypoint = (
        PurePosixPath(str(record["staging_candidate_root"]))
        / PurePosixPath(str(record["staging_entrypoint"])).name
    ).as_posix()
    if record["staging_entrypoint"] != expected_entrypoint:
        raise Amendment0002ValidationError("validation staging entrypoint is not adjacent")
    return identity


def _validate_terminal(record: Mapping[str, Any]) -> None:
    _exact_mapping(record, _TERMINAL_KEYS, "validation terminal")
    _team(record["team_id"])
    _identifier(record["candidate_id"], "candidate_id")
    _identifier(record["run_id"], "run_id")
    for field in ("candidate_identity_sha256", "request_sha256"):
        _hash(record[field], field)
    _timestamp(record["completed_at_utc"], "completed_at_utc")
    _finite(record["cpu_seconds"], "cpu_seconds", nonnegative=True)
    _finite(record["wall_seconds"], "wall_seconds", nonnegative=True)
    if not isinstance(record["gate_vector"], Mapping):
        raise Amendment0002ValidationError("validation gate_vector must be an object")
    if not isinstance(record["artifact_hashes"], Mapping):
        raise Amendment0002ValidationError("artifact_hashes must be an object")
    for path, digest in record["artifact_hashes"].items():
        _safe_relative(path, "artifact path")
        _hash(digest, "artifact hash")
    succeeded = record["event_type"] == "succeeded"
    if succeeded:
        _safe_relative(record["aggregate_packet_path"], "aggregate packet path")
        _hash(record["aggregate_packet_sha256"], "aggregate packet sha256")
        if (
            not record["gate_vector"]
            or not record["artifact_hashes"]
            or record["failure_reason"] is not None
        ):
            raise Amendment0002ValidationError("successful validation terminal is incomplete")
    else:
        if (
            record["aggregate_packet_path"] is not None
            or record["aggregate_packet_sha256"] is not None
        ):
            raise Amendment0002ValidationError(
                "failed validation terminal cannot disclose a packet"
            )
        reason = record["failure_reason"]
        if not isinstance(reason, str) or not reason or len(reason) > 2048:
            raise Amendment0002ValidationError("failed validation terminal lacks a reason")


def _validate_release(record: Mapping[str, Any]) -> None:
    _exact_mapping(record, _RELEASE_KEYS, "packet_released")
    _timestamp(record["released_at_utc"], "released_at_utc")
    if record["cohort_freeze_sha256"] != COHORT_FREEZE_SHA256:
        raise Amendment0002ValidationError("packet release uses the wrong cohort freeze")
    _hash(record["terminal_journal_head_sha256"], "terminal_journal_head_sha256")
    packets = record["packet_sha256_by_team"]
    if not isinstance(packets, Mapping) or set(packets) != {
        "team-04",
        "team-05",
        "team-06",
        "team-09",
    }:
        raise Amendment0002ValidationError("packet release must bind the exact four-team cohort")
    for team_id, digest in packets.items():
        _team(team_id)
        _hash(digest, f"packet_sha256_by_team.{team_id}", nullable=True)


def replay_validation_journal_bytes(payload: bytes) -> ValidationJournalState:
    """Replay the durable validation chain and canonical lab authorization ledger."""

    if not isinstance(payload, bytes) or (payload and not payload.endswith(b"\n")):
        raise Amendment0002ValidationError("validation journal bytes are truncated")
    records: list[Mapping[str, Any]] = []
    requests: dict[str, Mapping[str, Any]] = {}
    terminal_requests: set[str] = set()
    identities: set[str] = set()
    run_ids: set[str] = set()
    previous = GENESIS_SHA256
    previous_time: dt.datetime | None = None
    ledger = lab_v3.new_validation_ledger()
    release_record: Mapping[str, Any] | None = None
    for number, line in enumerate(payload.splitlines(keepends=True), start=1):
        record = _decode_journal_line(line, number)
        event_type = record.get("event_type")
        if event_type == "probe_accepted":
            identity = _validate_accepted(record)
        elif event_type in _TERMINAL_TYPES:
            _validate_terminal(record)
            identity = None
        elif event_type == "packet_released":
            _validate_release(record)
            identity = None
        else:
            raise Amendment0002ValidationError("validation journal contains an unknown event")
        if (
            record.get("schema_version") != JOURNAL_SCHEMA_VERSION
            or record.get("event_sequence") != number
            or record.get("previous_sha256") != previous
            or record.get("record_sha256") != _record_sha256(record)
        ):
            raise Amendment0002ValidationError("validation journal chain is invalid")
        event_time = _timestamp(
            (
                record["accepted_at_utc"]
                if event_type == "probe_accepted"
                else (
                    record["released_at_utc"]
                    if event_type == "packet_released"
                    else record["completed_at_utc"]
                )
            ),
            "validation journal event time",
        )
        if previous_time is not None and event_time < previous_time:
            raise Amendment0002ValidationError("validation journal timestamps move backwards")
        if event_type == "probe_accepted":
            if release_record is not None:
                raise Amendment0002ValidationError(
                    "a probe cannot be accepted after packet release"
                )
            if set(requests) - terminal_requests:
                raise Amendment0002ValidationError(
                    "a validation request is already pending globally"
                )
            assert identity is not None
            if identity.sha256 in identities or record["run_id"] in run_ids:
                raise Amendment0002ValidationError("validation identity or run_id was reused")
            next_ledger, authorization = lab_v3.authorize_validation_probe(
                ledger, identity, round_name="opening"
            )
            auth_raw = _exact_mapping(record["authorization"], _AUTHORIZATION_KEYS, "authorization")
            if dict(auth_raw) != _authorization_mapping(authorization):
                raise Amendment0002ValidationError(
                    "persisted validation authorization is not canonical"
                )
            ledger = next_ledger
            identities.add(identity.sha256)
            run_ids.add(str(record["run_id"]))
            requests[str(record["record_sha256"])] = record
        elif event_type in _TERMINAL_TYPES:
            if release_record is not None:
                raise Amendment0002ValidationError("a terminal cannot follow packet release")
            request_hash = str(record["request_sha256"])
            request = requests.get(request_hash)
            if request is None or request_hash in terminal_requests:
                raise Amendment0002ValidationError(
                    "validation terminal has no unique accepted request"
                )
            for field in ("team_id", "run_id", "candidate_id", "candidate_identity_sha256"):
                if record[field] != request[field]:
                    raise Amendment0002ValidationError(f"validation terminal {field} mismatch")
            terminal_requests.add(request_hash)
        else:
            if release_record is not None:
                raise Amendment0002ValidationError("validation packets may be released only once")
            if (
                len(requests) != 4
                or terminal_requests != set(requests)
                or record["terminal_journal_head_sha256"] != previous
            ):
                raise Amendment0002ValidationError(
                    "packet release requires four completed accepted probes"
                )
            terminal_by_team = {
                str(item["team_id"]): item
                for item in records
                if item["event_type"] in _TERMINAL_TYPES
            }
            expected_packets = {
                team_id: terminal_by_team[team_id]["aggregate_packet_sha256"]
                for team_id in ("team-04", "team-05", "team-06", "team-09")
            }
            if record["packet_sha256_by_team"] != expected_packets:
                raise Amendment0002ValidationError(
                    "packet release differs from sealed terminal packets"
                )
            release_record = record
        records.append(record)
        previous = str(record["record_sha256"])
        previous_time = event_time
    return ValidationJournalState(
        records=tuple(records),
        head_sha256=previous,
        ledger=ledger,
        pending_request_sha256s=tuple(sorted(set(requests) - terminal_requests)),
        terminal_request_sha256s=tuple(sorted(terminal_requests)),
        release_record=release_record,
    )


def _read_validation_journal(root: Path) -> ValidationJournalState:
    path = root / VALIDATION_JOURNAL_PATH
    if not path.exists() and not path.is_symlink():
        return replay_validation_journal_bytes(b"")
    payload = orchestrator_v3._read_regular_bytes(root, VALIDATION_JOURNAL_PATH)
    return replay_validation_journal_bytes(payload)


def _append_journal_event(root: Path, event: Mapping[str, Any]) -> ValidationJournalState:
    path = root / VALIDATION_JOURNAL_PATH
    with journal_v3.exclusive_journal_lock(path) as handle:
        handle.seek(0)
        current_bytes = handle.read()
        current = replay_validation_journal_bytes(current_bytes)
        record: dict[str, Any] = {
            "schema_version": JOURNAL_SCHEMA_VERSION,
            "event_sequence": len(current.records) + 1,
            "previous_sha256": current.head_sha256,
            **dict(event),
        }
        record["record_sha256"] = _record_sha256(record)
        line = _canonical_bytes(record) + b"\n"
        if len(line) - 1 > MAX_RECORD_BYTES:
            raise Amendment0002ValidationError("validation journal record is too large")
        next_state = replay_validation_journal_bytes(current_bytes + line)
        handle.seek(0, os.SEEK_END)
        if handle.write(line) != len(line):
            raise OSError("short validation journal append")
        handle.flush()
        os.fsync(handle.fileno())
        return next_state


def _journal_timestamp(state: ValidationJournalState) -> str:
    current = _utc_now()
    if not state.records:
        return current
    last = state.records[-1]
    field = (
        "accepted_at_utc"
        if last["event_type"] == "probe_accepted"
        else ("released_at_utc" if last["event_type"] == "packet_released" else "completed_at_utc")
    )
    return max(current, str(last[field]))


def _verify_journal_cohort(state: ValidationJournalState, cohort: CohortAuthority) -> None:
    by_team = cohort.by_team
    for record in state.accepted_records:
        candidate = by_team.get(str(record["team_id"]))
        if candidate is None:
            raise Amendment0002ValidationError("validation journal contains a non-cohort team")
        expected = candidate.identity
        if (
            record["candidate_identity_sha256"] != expected.sha256
            or record["candidate_id"] != expected.candidate_id
            or record["original_source_archive_path"] != candidate.source_archive_path
            or record["original_source_archive_sha256"] != candidate.source_archive_sha256
            or record["train_metric_packet_path"] != candidate.train_metric_packet_path
            or record["train_metric_packet_sha256"] != candidate.train_metric_packet_sha256
        ):
            raise Amendment0002ValidationError("validation journal differs from frozen cohort")


def _run_test_command(root: Path, command: Sequence[str], label: str) -> bytes:
    completed = subprocess.run(
        list(command),
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = completed.stdout
    if completed.returncode != 0:
        raise Amendment0002ValidationError(f"{label} failed with exit code {completed.returncode}")
    if not isinstance(output, bytes) or not output or len(output) > MAX_TEST_OUTPUT_BYTES:
        raise Amendment0002ValidationError(f"{label} output is missing or too large")
    orchestrator_v3._parse_passed_count(output)
    return output


def _test_evidence(command: Sequence[str], output: bytes) -> dict[str, object]:
    count = orchestrator_v3._parse_passed_count(output)
    return {
        "command": list(command),
        "collected": count,
        "passed": count,
        "output_size": len(output),
        "output_sha256": _sha256(output),
        "output_base64": base64.b64encode(output).decode("ascii"),
    }


def _verify_test_evidence(value: object, command: Sequence[str], label: str) -> None:
    keys = frozenset(
        {"command", "collected", "passed", "output_size", "output_sha256", "output_base64"}
    )
    raw = _exact_mapping(value, keys, label)
    if raw["command"] != list(command) or raw["passed"] != raw["collected"]:
        raise Amendment0002ValidationError(f"{label} command or counts changed")
    try:
        output = base64.b64decode(str(raw["output_base64"]).encode("ascii"), validate=True)
    except Exception as exc:
        raise Amendment0002ValidationError(f"{label} output encoding is invalid") from exc
    if (
        len(output) != raw["output_size"]
        or _sha256(output) != raw["output_sha256"]
        or orchestrator_v3._parse_passed_count(output) != raw["collected"]
    ):
        raise Amendment0002ValidationError(f"{label} output binding is invalid")


def _freeze_body(
    root: Path,
    cohort: CohortAuthority,
    implementation_commit: str,
    entries: Sequence[Mapping[str, object]],
    base_output: bytes,
    parent_amendment_output: bytes,
    amendment_output: bytes,
) -> dict[str, object]:
    parent = amendment_0001.verify_integration(root)
    return {
        "schema_version": SCHEMA_VERSION,
        "amendment_id": AMENDMENT_ID,
        "parent_amendment": dataclasses.asdict(parent),
        "cohort": {
            "path": COHORT_FREEZE_PATH,
            "file_sha256": cohort.file_sha256,
            "commit": cohort.commit,
            "candidate_identity_sha256": [
                candidate.identity.sha256 for candidate in cohort.candidates
            ],
        },
        "train_boundary": {
            "path": orchestrator_v3.LAB_JOURNAL_PATH,
            "head_sha256": cohort.lab_journal_head_sha256,
            "file_sha256": _sha256(
                orchestrator_v3._read_regular_bytes(root, orchestrator_v3.LAB_JOURNAL_PATH)
            ),
        },
        "implementation": {
            "commit": implementation_commit,
            "files": [dict(entry) for entry in entries],
            "manifest_sha256": _manifest_sha256(entries),
        },
        "base_suite": _test_evidence(BASE_TEST_COMMAND, base_output),
        "parent_amendment_tests": _test_evidence(
            PARENT_AMENDMENT_TEST_COMMAND, parent_amendment_output
        ),
        "amendment_tests": _test_evidence(AMENDMENT_TEST_COMMAND, amendment_output),
        "a6_report_sha256": _sha256(pure_crypto_universe_v6.audit_report_bytes(root)),
    }


def freeze_activation(
    root: str | Path,
    *,
    implementation_commit: str,
) -> ProvisionalActivationFreeze:
    """Run serial evidence and write the prospective activation freeze exactly once."""

    root_path = orchestrator_v3._trusted_root(root)
    with orchestrator_v3._result_command_lock(root_path):
        freeze_path = root_path / INTEGRATION_FREEZE_PATH
        if freeze_path.exists() or freeze_path.is_symlink():
            raise Amendment0002ValidationError("Amendment 0002 integration freeze already exists")
        journal_path = root_path / VALIDATION_JOURNAL_PATH
        if journal_path.exists() or journal_path.is_symlink():
            raise Amendment0002ValidationError(
                "validation journal must be absent before activation"
            )
        private_validation_root = root_path / PRIVATE_VALIDATION_ROOT
        if private_validation_root.exists() or private_validation_root.is_symlink():
            raise Amendment0002ValidationError(
                "private validation output root must be absent before activation"
            )
        cohort_before = load_cohort(root_path)
        entries_before = _implementation_entries(root_path)
        _verify_implementation_commit(root_path, implementation_commit, entries_before)
        parent_before = amendment_0001.verify_integration(root_path)
        base_output = _run_test_command(root_path, BASE_TEST_COMMAND, "current base suite")
        parent_amendment_output = _run_test_command(
            root_path,
            PARENT_AMENDMENT_TEST_COMMAND,
            "Amendment 0001 suite",
        )
        amendment_output = _run_test_command(
            root_path, AMENDMENT_TEST_COMMAND, "Amendment 0002 tests"
        )
        if (
            load_cohort(root_path) != cohort_before
            or amendment_0001.verify_integration(root_path) != parent_before
            or _implementation_entries(root_path) != entries_before
            or journal_path.exists()
            or journal_path.is_symlink()
            or private_validation_root.exists()
            or private_validation_root.is_symlink()
        ):
            raise Amendment0002ValidationError("activation inputs changed during serial evidence")
        body = _freeze_body(
            root_path,
            cohort_before,
            implementation_commit,
            entries_before,
            base_output,
            parent_amendment_output,
            amendment_output,
        )
        record = {**body, "record_sha256": _sha256(_canonical_bytes(body))}
        orchestrator_v3._write_new_file(
            root_path,
            INTEGRATION_FREEZE_PATH,
            _pretty_bytes(record),
            mode=0o444,
        )
        freeze_bytes = orchestrator_v3._read_regular_bytes(root_path, INTEGRATION_FREEZE_PATH)
        return ProvisionalActivationFreeze(
            freeze_file_sha256=_sha256(freeze_bytes),
            record_sha256=str(record["record_sha256"]),
            implementation_commit=implementation_commit,
        )


def _verify_freeze_commit(root: Path, implementation_commit: str, freeze_bytes: bytes) -> str:
    additions = _git(root, ["log", "--diff-filter=A", "--format=%H", "--", INTEGRATION_FREEZE_PATH])
    commits = [line for line in additions.stdout.decode("ascii", "replace").splitlines() if line]
    if additions.returncode != 0 or len(commits) != 1:
        raise Amendment0002ValidationError("activation requires one unique freeze commit")
    freeze_commit = commits[0]
    _verified_commit(root, freeze_commit, "freeze commit")
    parent = _git(root, ["rev-parse", f"{freeze_commit}^"])
    if (
        parent.returncode != 0
        or parent.stdout.decode("ascii", "replace").strip() != implementation_commit
    ):
        raise Amendment0002ValidationError(
            "freeze commit must directly follow implementation_commit"
        )
    delta = _git(root, ["diff-tree", "--no-commit-id", "--name-status", "-r", freeze_commit])
    if delta.returncode != 0 or delta.stdout.decode("utf-8", "replace").splitlines() != [
        f"A\t{INTEGRATION_FREEZE_PATH}"
    ]:
        raise Amendment0002ValidationError("freeze commit has an unexpected repository delta")
    committed = _git(root, ["show", f"{freeze_commit}:{INTEGRATION_FREEZE_PATH}"])
    if committed.returncode != 0 or committed.stdout != freeze_bytes:
        raise Amendment0002ValidationError("live activation freeze differs from its commit")
    return freeze_commit


def verify_activation(root: str | Path = ".") -> ActivationAuthority:
    """Verify the prospective freeze, parent amendment, cohort, and implementation."""

    root_path = orchestrator_v3._trusted_root(root)
    freeze_bytes = orchestrator_v3._read_regular_bytes(root_path, INTEGRATION_FREEZE_PATH)
    record = _strict_json(freeze_bytes, "Amendment 0002 integration freeze")
    if _pretty_bytes(record) != freeze_bytes:
        raise Amendment0002ValidationError("activation freeze is not canonical pretty JSON")
    record = _exact_mapping(record, _FREEZE_KEYS, "activation freeze")
    body = {key: record[key] for key in _FREEZE_KEYS - {"record_sha256"}}
    if (
        record["schema_version"] != SCHEMA_VERSION
        or record["amendment_id"] != AMENDMENT_ID
        or record["record_sha256"] != _sha256(_canonical_bytes(body))
    ):
        raise Amendment0002ValidationError("activation freeze identity or hash is invalid")
    parent = amendment_0001.verify_integration(root_path)
    if record["parent_amendment"] != dataclasses.asdict(parent):
        raise Amendment0002ValidationError("parent Amendment 0001 authority changed")
    cohort = load_cohort(root_path)
    expected_cohort = {
        "path": COHORT_FREEZE_PATH,
        "file_sha256": cohort.file_sha256,
        "commit": cohort.commit,
        "candidate_identity_sha256": [candidate.identity.sha256 for candidate in cohort.candidates],
    }
    if record["cohort"] != expected_cohort:
        raise Amendment0002ValidationError("frozen IS cohort changed")
    expected_boundary = {
        "path": orchestrator_v3.LAB_JOURNAL_PATH,
        "head_sha256": cohort.lab_journal_head_sha256,
        "file_sha256": _sha256(
            orchestrator_v3._read_regular_bytes(root_path, orchestrator_v3.LAB_JOURNAL_PATH)
        ),
    }
    if record["train_boundary"] != expected_boundary:
        raise Amendment0002ValidationError("train-journal activation boundary changed")
    implementation = record["implementation"]
    if not isinstance(implementation, Mapping):
        raise Amendment0002ValidationError("activation implementation is malformed")
    entries = _implementation_entries(root_path)
    if implementation.get("files") != list(entries) or implementation.get(
        "manifest_sha256"
    ) != _manifest_sha256(entries):
        raise Amendment0002ValidationError("activation implementation bytes changed")
    implementation_commit = str(implementation.get("commit"))
    _verify_implementation_commit(root_path, implementation_commit, entries)
    _verify_test_evidence(record["base_suite"], BASE_TEST_COMMAND, "base suite")
    _verify_test_evidence(
        record["parent_amendment_tests"],
        PARENT_AMENDMENT_TEST_COMMAND,
        "parent amendment tests",
    )
    _verify_test_evidence(record["amendment_tests"], AMENDMENT_TEST_COMMAND, "amendment tests")
    if record["a6_report_sha256"] != _sha256(pure_crypto_universe_v6.audit_report_bytes(root_path)):
        raise Amendment0002ValidationError("frozen A6 report changed")
    freeze_commit = _verify_freeze_commit(root_path, implementation_commit, freeze_bytes)
    return ActivationAuthority(
        freeze_file_sha256=_sha256(freeze_bytes),
        freeze_commit=freeze_commit,
        record_sha256=str(record["record_sha256"]),
        implementation_commit=implementation_commit,
        cohort_freeze_sha256=cohort.file_sha256,
        cohort_freeze_commit=cohort.commit,
    )


def _staging_paths(candidate: CohortCandidate) -> tuple[str, str]:
    team_id = candidate.identity.team_id
    root = (
        PurePosixPath("tournament/top40-v3/teams")
        / team_id
        / ".sealed-validation"
        / candidate.identity.sha256
    ).as_posix()
    return root, (PurePosixPath(root) / candidate.source_archive.entrypoint).as_posix()


def _remove_staging(root: Path, relative: str) -> None:
    relative = _safe_relative(relative, "staging root")
    required = "tournament/top40-v3/teams/"
    if not relative.startswith(required) or "/.sealed-validation/" not in relative:
        raise Amendment0002ValidationError("refusing to remove a non-staging path")
    path = root / relative
    if not path.exists() and not path.is_symlink():
        return
    current = root
    for part in PurePosixPath(relative).parts:
        current /= part
        metadata = os.lstat(current)
        if stat.S_ISLNK(metadata.st_mode):
            raise Amendment0002ValidationError("staging path contains a symlink")
    if not path.is_dir():
        raise Amendment0002ValidationError("staging root is not a directory")
    shutil.rmtree(path)
    parent = path.parent
    with contextlib.suppress(OSError):
        parent.rmdir()


def _rehydrate_candidate(
    root: Path,
    candidate: CohortCandidate,
) -> tuple[str, str, source_archive_v3.SourceArchive]:
    staging_root, staging_entrypoint = _staging_paths(candidate)
    path = root / staging_root
    if path.exists() or path.is_symlink():
        _remove_staging(root, staging_root)
    orchestrator_v3._ensure_directory(root, staging_root)
    try:
        for item in candidate.source_archive.files:
            destination = (PurePosixPath(staging_root) / item.path).as_posix()
            orchestrator_v3._write_new_file(root, destination, item.content, mode=0o444)
        capture = runner_v3.capture_source_bundle(
            root, candidate.identity.team_id, staging_entrypoint
        )
        if (
            capture.sha256 != candidate.identity.source_bundle_sha256
            or capture.manifest_entries != candidate.source_archive.manifest_entries
        ):
            raise Amendment0002ValidationError(
                "rehydrated source differs from frozen train archive"
            )
        staging_archive = source_archive_v3.write_source_archive(
            root,
            team_id=candidate.identity.team_id,
            candidate_id=candidate.identity.candidate_id,
            candidate_root=staging_root,
            entrypoint=candidate.source_archive.entrypoint,
            source_bundle_sha256=candidate.identity.source_bundle_sha256,
            files=candidate.source_archive.files,
        )
        return staging_root, staging_entrypoint, staging_archive
    except BaseException:
        with contextlib.suppress(Exception):
            _remove_staging(root, staging_root)
        raise


def _cpu_seconds() -> float:
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return float(own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime)


def _failure_reason(error: BaseException) -> str:
    text = f"{type(error).__name__}: {error}"
    cleaned = " ".join(
        "".join(
            " " if ord(character) < 32 or ord(character) == 127 else character for character in text
        ).split()
    )
    return (cleaned or "sealed validation failed")[:2048]


def _run_id(candidate: CohortCandidate, authorization: lab_v3.ValidationProbeAuthorization) -> str:
    compact = candidate.identity.team_id.replace("-", "")
    return (
        f"v3-{compact}-validation-{authorization.team_total_probe_number:06d}-"
        f"{candidate.identity.source_bundle_sha256[:12]}"
    )


def _collect_artifacts(root: Path, output_path: str) -> dict[str, str]:
    return orchestrator_v3._collect_output_artifacts(root, output_path)


def _validate_runner_result(
    root: Path,
    candidate: CohortCandidate,
    staging_entrypoint: str,
    output_path: str,
    result: runner_v3.TeamWindowRunResult,
) -> tuple[dict[str, Any], dict[str, str]]:
    identity = candidate.identity
    exact = {
        "stage": "validation",
        "team_id": identity.team_id,
        "entrypoint": staging_entrypoint,
        "seed": 20260718,
        "data_manifest_sha256": identity.data_authority_sha256,
        "config_sha256": identity.config_sha256,
        "strategy_sha256": identity.strategy_sha256,
        "risk_policy_sha256": identity.risk_policy_sha256,
        "source_bundle_sha256": identity.source_bundle_sha256,
        "dependency_lock_sha256": identity.dependency_lock_sha256,
        "evaluator_sha256": identity.evaluator_sha256,
        "pure_crypto_report_sha256": (
            "b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b"
        ),
        "output_dir": output_path,
    }
    for field, expected in exact.items():
        if getattr(result, field, None) != expected:
            raise Amendment0002ValidationError(f"validation runner differs from identity: {field}")
    fields = result.organizer_fields()
    if (
        fields["scored_window"]["start"] != "2022-07-01"
        or fields["scored_window"]["end"] != "2023-06-30"
    ):
        raise Amendment0002ValidationError("validation runner used the wrong scored window")
    artifacts: dict[str, str] = {}
    for name, relative in result.artifacts.items():
        relative = _safe_relative(relative, f"runner artifact {name}")
        if not relative.startswith(output_path + "/"):
            raise Amendment0002ValidationError("validation artifact escaped private output")
        payload = orchestrator_v3._read_regular_bytes(root, relative)
        digest = _sha256(payload)
        if digest != result.artifact_sha256[name] or len(payload) != result.artifact_sizes[name]:
            raise Amendment0002ValidationError("validation artifact binding changed")
        artifacts[relative] = digest
    return fields, artifacts


def _logical_result_projection(fields: Mapping[str, Any]) -> dict[str, Any]:
    projection = dict(fields)
    projection.pop("output_dir", None)
    projection.pop("artifacts", None)
    return projection


def _csv_rows(root: Path, relative: str, label: str) -> list[dict[str, str]]:
    payload = orchestrator_v3._read_regular_bytes(root, _safe_relative(relative, label))
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Amendment0002ValidationError(f"{label} is not UTF-8 CSV") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise Amendment0002ValidationError(f"{label} has an invalid CSV header")
    return [dict(row) for row in reader]


def _validation_artifact_aggregates(
    root: Path,
    result: runner_v3.TeamWindowRunResult,
) -> dict[str, object]:
    start_day = "2022-07-01"
    end_day = "2023-07-01"
    start_time = "2022-07-01T00:00:00Z"
    end_time = "2023-07-01T00:00:00Z"
    trade_rows = _csv_rows(root, result.artifacts["trades"], "validation trades")
    validation_trade_count = 0
    for row in trade_rows:
        timestamp = row.get("timestamp")
        if not isinstance(timestamp, str):
            raise Amendment0002ValidationError("validation trades lack timestamp")
        if start_time <= timestamp < end_time:
            validation_trade_count += 1

    def daily_values(logical_name: str) -> list[tuple[str, float]]:
        rows = _csv_rows(root, result.artifacts[logical_name], logical_name)
        selected: list[tuple[str, float]] = []
        for row in rows:
            day = row.get("date")
            if isinstance(day, str) and start_day <= day < end_day:
                selected.append((day, _finite(row.get("net_return"), f"{logical_name}.net_return")))
        if len(selected) != 365 or len({day for day, _value in selected}) != 365:
            raise Amendment0002ValidationError(
                f"{logical_name} does not contain the exact 365-day validation slice"
            )
        if [day for day, _value in selected] != sorted(day for day, _value in selected):
            raise Amendment0002ValidationError(f"{logical_name} validation dates are not sorted")
        return selected

    base = daily_values("daily_returns")
    doubled = daily_values("double_cost_daily_returns")

    def compound(values: Sequence[float]) -> float:
        equity = 1.0
        for value in values:
            if value <= -1.0:
                raise Amendment0002ValidationError("daily return violates solvency")
            equity *= 1.0 + value
        return float(equity - 1.0)

    quarters: dict[str, list[float]] = {
        "2022Q3": [],
        "2022Q4": [],
        "2023Q1": [],
        "2023Q2": [],
    }
    for day, value in base:
        year = int(day[:4])
        month = int(day[5:7])
        quarter = (month - 1) // 3 + 1
        key = f"{year}Q{quarter}"
        if key not in quarters:
            raise Amendment0002ValidationError("validation daily return escaped its quarter set")
        quarters[key].append(value)
    if any(not values for values in quarters.values()):
        raise Amendment0002ValidationError("validation quarter aggregate is incomplete")
    return {
        "validation_trade_count": validation_trade_count,
        "cumulative_net_return": compound([value for _day, value in base]),
        "cumulative_double_cost_return": compound([value for _day, value in doubled]),
        "quarter_returns": {key: compound(values) for key, values in quarters.items()},
    }


def _protect_private_output(root: Path, relative: str) -> None:
    relative = _safe_relative(relative, "private output")
    if not relative.startswith("tournament/top40-v3/private/validation/"):
        raise Amendment0002ValidationError("refusing to chmod a non-validation output")
    path = root / relative
    if not path.is_dir() or path.is_symlink():
        raise Amendment0002ValidationError("private validation output is unsafe")
    for item in sorted(path.rglob("*"), key=lambda value: value.as_posix(), reverse=True):
        metadata = os.lstat(item)
        if stat.S_ISLNK(metadata.st_mode):
            raise Amendment0002ValidationError("private validation output contains a symlink")
        if stat.S_ISDIR(metadata.st_mode):
            os.chmod(item, 0o700)
        elif stat.S_ISREG(metadata.st_mode):
            os.chmod(item, 0o600)
        else:
            raise Amendment0002ValidationError("private validation output is not regular")
    os.chmod(path, 0o700)


def build_validation_aggregate_packet(
    result_fields: Mapping[str, Any],
    candidate: CohortCandidate,
    authorization: lab_v3.ValidationProbeAuthorization,
    *,
    activation: ActivationAuthority,
    artifact_aggregates: Mapping[str, object],
    evidence_manifest_sha256: str,
) -> dict[str, object]:
    """Build the fixed aggregate-only packet; raw artifact paths are deliberately absent."""

    identity = candidate.identity
    window = result_fields["scored_window"]
    metrics = window["metrics"]
    regimes = result_fields["regime_sharpe"]
    confidence = result_fields["confidence_intervals"]
    packet: dict[str, object] = {
        "schema_version": PACKET_SCHEMA_VERSION,
        "packet_kind": "sealed-validation-fixed-aggregate",
        "stage": "validation",
        "identity": _identity_mapping(identity),
        "authorization": {
            "record_sha256": authorization.record_sha256,
            "round_name": authorization.round_name,
            "team_round_probe_number": authorization.team_round_probe_number,
            "team_total_probe_number": authorization.team_total_probe_number,
        },
        "scored_window": {
            "start": window["start"],
            "end": window["end"],
            "metrics": {
                "net_sharpe": _finite(metrics["net_sharpe"], "net_sharpe"),
                "net_sortino": _finite(metrics["net_sortino"], "net_sortino"),
                "calmar": _finite(metrics["calmar"], "calmar"),
                "annualized_return": _finite(metrics["annualized_return"], "annualized_return"),
                "max_drawdown": _finite(metrics["max_drawdown"], "max_drawdown", nonnegative=True),
                "positive_quarter_fraction": _finite(
                    metrics["positive_quarter_fraction"],
                    "positive_quarter_fraction",
                    nonnegative=True,
                ),
            },
        },
        "double_cost_sharpe": _finite(result_fields["double_cost_sharpe"], "double_cost_sharpe"),
        "regime_sharpe": {
            name: _finite(regimes[name], f"regime_sharpe.{name}")
            for name in ("bull", "bear", "chop", "stress")
        },
        "confidence_intervals": {
            "net_sharpe_95": [
                _finite(value, "net_sharpe_95") for value in confidence["net_sharpe_95"]
            ],
            "double_cost_sharpe_95": [
                _finite(value, "double_cost_sharpe_95")
                for value in confidence["double_cost_sharpe_95"]
            ],
        },
        "validation_aggregates": {
            "cumulative_net_return": _finite(
                artifact_aggregates["cumulative_net_return"], "cumulative_net_return"
            ),
            "cumulative_double_cost_return": _finite(
                artifact_aggregates["cumulative_double_cost_return"],
                "cumulative_double_cost_return",
            ),
            "trade_count": int(artifact_aggregates["validation_trade_count"]),
            "quarter_returns": {
                key: _finite(value, f"quarter_returns.{key}")
                for key, value in dict(artifact_aggregates["quarter_returns"]).items()
            },
        },
        "structural_hard_gates": {
            "reproducible": True,
            "data_authority": True,
            "universe_compliant": True,
            "causal": True,
            "execution_compliant": True,
            "solvent": True,
            "window_complete": True,
        },
        "readiness": {
            "validation_positive": (
                float(metrics["net_sharpe"]) > 0.0
                and float(metrics["annualized_return"]) > 0.0
                and float(result_fields["double_cost_sharpe"]) > 0.0
            ),
            "nomination_ready": False,
            "public_stitched_assessment_pending": True,
        },
        "provenance": {
            "activation_freeze_sha256": activation.freeze_file_sha256,
            "cohort_freeze_sha256": COHORT_FREEZE_SHA256,
            "train_source_archive_sha256": candidate.source_archive_sha256,
            "sealed_evidence_manifest_sha256": str(
                _hash(evidence_manifest_sha256, "sealed evidence manifest")
            ),
        },
    }
    encoded = _canonical_bytes(packet)
    forbidden = (
        b"targets",
        b"positions",
        b"daily_returns",
        b"trades.csv",
        b"artifact",
        b"output_dir",
    )
    if any(token in encoded for token in forbidden):
        raise Amendment0002ValidationError("aggregate packet contains a forbidden raw-data field")
    return packet


def _append_terminal(
    root: Path,
    *,
    event_type: str,
    request: Mapping[str, Any],
    completed_at_utc: str,
    cpu_seconds: float,
    wall_seconds: float,
    gate_vector: Mapping[str, bool],
    aggregate_packet_path: str | None,
    aggregate_packet_sha256: str | None,
    artifact_hashes: Mapping[str, str],
    failure_reason: str | None,
) -> ValidationJournalState:
    return _append_journal_event(
        root,
        {
            "event_type": event_type,
            "team_id": request["team_id"],
            "run_id": request["run_id"],
            "candidate_id": request["candidate_id"],
            "candidate_identity_sha256": request["candidate_identity_sha256"],
            "request_sha256": request["record_sha256"],
            "completed_at_utc": completed_at_utc,
            "cpu_seconds": float(cpu_seconds),
            "wall_seconds": float(wall_seconds),
            "gate_vector": dict(gate_vector),
            "aggregate_packet_path": aggregate_packet_path,
            "aggregate_packet_sha256": aggregate_packet_sha256,
            "artifact_hashes": dict(artifact_hashes),
            "failure_reason": failure_reason,
        },
    )


def _recover_pending(
    root: Path,
    state: ValidationJournalState,
) -> ValidationJournalState:
    if not state.pending_request_sha256s:
        return state
    if len(state.pending_request_sha256s) != 1:
        raise Amendment0002ValidationError("multiple validation requests are pending")
    request_sha = state.pending_request_sha256s[0]
    request = next(
        record for record in state.accepted_records if record["record_sha256"] == request_sha
    )
    errors: list[str] = []
    try:
        artifacts = _collect_artifacts(root, str(request["output_path"]))
        artifacts.update(_collect_artifacts(root, str(request["replay_output_path"])))
    except BaseException as exc:
        artifacts = {}
        errors.append(_failure_reason(exc))
    try:
        _remove_staging(root, str(request["staging_candidate_root"]))
    except BaseException as exc:
        errors.append(_failure_reason(exc))
    reason = (
        "organizer restart recovery: accepted validation probe had no terminal event; "
        "the probe remains consumed and no aggregate metrics were disclosed"
    )
    if errors:
        reason = (reason + "; recovery errors: " + "; ".join(errors))[:2048]
    return _append_terminal(
        root,
        event_type="aborted",
        request=request,
        completed_at_utc=_journal_timestamp(state),
        cpu_seconds=0.0,
        wall_seconds=0.0,
        gate_vector={},
        aggregate_packet_path=None,
        aggregate_packet_sha256=None,
        artifact_hashes=artifacts,
        failure_reason=reason,
    )


def probe(root: str | Path, team_id: str) -> dict[str, object]:
    """Consume and run one frozen opening probe, returning no OOS metric before cohort release."""

    root_path = orchestrator_v3._trusted_root(root)
    with orchestrator_v3._result_command_lock(root_path):
        activation = verify_activation(root_path)
        cohort = load_cohort(root_path)
        candidate = cohort.by_team.get(team_id)
        if candidate is None:
            raise Amendment0002ValidationError("team is not in the frozen GREEN validation cohort")
        state = _read_validation_journal(root_path)
        _verify_journal_cohort(state, cohort)
        state = _recover_pending(root_path, state)
        if any(record["team_id"] == team_id for record in state.accepted_records):
            raise Amendment0002ValidationError("this frozen candidate already consumed its probe")
        staging_root, staging_entrypoint, staging_archive = _rehydrate_candidate(
            root_path, candidate
        )
        next_ledger, authorization = lab_v3.authorize_validation_probe(
            state.ledger, candidate.identity, round_name="opening"
        )
        run_id = _run_id(candidate, authorization)
        output_path = f"tournament/top40-v3/private/validation/{team_id}/{run_id}"
        replay_output_path = f"{output_path}-exact-replay"
        if any(
            (root_path / relative).exists() or (root_path / relative).is_symlink()
            for relative in (output_path, replay_output_path)
        ):
            _remove_staging(root_path, staging_root)
            raise Amendment0002ValidationError("unique validation output path already exists")
        accepted = _append_journal_event(
            root_path,
            {
                "event_type": "probe_accepted",
                "team_id": team_id,
                "run_id": run_id,
                "candidate_id": candidate.identity.candidate_id,
                "candidate_identity_sha256": candidate.identity.sha256,
                "accepted_at_utc": _journal_timestamp(state),
                "authorization": _authorization_mapping(authorization),
                "cohort_freeze_sha256": COHORT_FREEZE_SHA256,
                "train_metric_packet_path": candidate.train_metric_packet_path,
                "train_metric_packet_sha256": candidate.train_metric_packet_sha256,
                "original_source_archive_path": candidate.source_archive_path,
                "original_source_archive_sha256": candidate.source_archive_sha256,
                "staging_source_archive_path": staging_archive.path,
                "staging_source_archive_sha256": staging_archive.sha256,
                "staging_candidate_root": staging_root,
                "staging_entrypoint": staging_entrypoint,
                "source_bundle_sha256": candidate.identity.source_bundle_sha256,
                "strategy_sha256": candidate.identity.strategy_sha256,
                "dependency_lock_sha256": candidate.identity.dependency_lock_sha256,
                "config_sha256": candidate.identity.config_sha256,
                "risk_policy_sha256": candidate.identity.risk_policy_sha256,
                "data_authority_sha256": candidate.identity.data_authority_sha256,
                "evaluator_sha256": candidate.identity.evaluator_sha256,
                "seed": 20260718,
                "validation_window": dict(VALIDATION_WINDOW),
                "output_path": output_path,
                "replay_output_path": replay_output_path,
            },
        )
        if accepted.ledger != next_ledger:
            raise Amendment0002ValidationError(
                "durable probe authorization differs from preregistration"
            )
        request = accepted.records[-1]
        start_wall = time.monotonic()
        start_cpu = _cpu_seconds()
        terminal_written = False
        try:
            with amendment_0001._activated_runtime(root_path):
                result = runner_v3.run_team(
                    root_path,
                    team_id,
                    staging_entrypoint,
                    orchestrator_v3.CONFIG_PATH,
                    orchestrator_v3.DATA_MANIFEST_PATH,
                    stage="validation",
                    _authorization=runner_v3._ORGANIZER_RUN_AUTHORIZATION,
                    _output_relative=output_path,
                    _candidate_id=candidate.identity.candidate_id,
                    _source_archive_relative=staging_archive.path,
                    _source_archive_sha256=staging_archive.sha256,
                )
                replay_result = runner_v3.run_team(
                    root_path,
                    team_id,
                    staging_entrypoint,
                    orchestrator_v3.CONFIG_PATH,
                    orchestrator_v3.DATA_MANIFEST_PATH,
                    stage="validation",
                    _authorization=runner_v3._ORGANIZER_RUN_AUTHORIZATION,
                    _output_relative=replay_output_path,
                    _candidate_id=candidate.identity.candidate_id,
                    _source_archive_relative=staging_archive.path,
                    _source_archive_sha256=staging_archive.sha256,
                )
            result_fields, artifacts = _validate_runner_result(
                root_path, candidate, staging_entrypoint, output_path, result
            )
            replay_fields, replay_artifacts = _validate_runner_result(
                root_path,
                candidate,
                staging_entrypoint,
                replay_output_path,
                replay_result,
            )
            if _logical_result_projection(result_fields) != _logical_result_projection(
                replay_fields
            ):
                raise Amendment0002ValidationError(
                    "exact validation replay differs from the primary logical result"
                )
            artifacts.update(replay_artifacts)
            artifact_aggregates = _validation_artifact_aggregates(root_path, result)
            evidence_manifest_sha256 = _sha256(
                _canonical_bytes(
                    {
                        "candidate_identity_sha256": candidate.identity.sha256,
                        "primary_logical_artifact_sha256": dict(result.artifact_sha256),
                        "replay_logical_artifact_sha256": dict(replay_result.artifact_sha256),
                        "logical_result": _logical_result_projection(result_fields),
                    }
                )
            )
            packet = build_validation_aggregate_packet(
                result_fields,
                candidate,
                authorization,
                activation=activation,
                artifact_aggregates=artifact_aggregates,
                evidence_manifest_sha256=evidence_manifest_sha256,
            )
            packet_bytes = _canonical_bytes(packet)
            packet_sha = _sha256(packet_bytes)
            packet_path = f"{output_path}/aggregate_packet.json"
            orchestrator_v3._write_new_file(root_path, packet_path, packet_bytes, mode=0o444)
            artifacts[packet_path] = packet_sha
            _protect_private_output(root_path, output_path)
            _protect_private_output(root_path, replay_output_path)
            _remove_staging(root_path, staging_root)
            gates = {
                "validation_exact_replay": True,
                "validation_annualized_return_positive": float(
                    result.scored_window.metrics.annualized_return
                )
                > 0.0,
                "validation_double_cost_sharpe_positive": float(result.double_cost_sharpe) > 0.0,
                "validation_net_sharpe_positive": float(result.scored_window.metrics.net_sharpe)
                > 0.0,
                "validation_window_complete": True,
            }
            terminal = _append_terminal(
                root_path,
                event_type="succeeded",
                request=request,
                completed_at_utc=_journal_timestamp(accepted),
                cpu_seconds=max(0.0, _cpu_seconds() - start_cpu),
                wall_seconds=max(0.0, time.monotonic() - start_wall),
                gate_vector=gates,
                aggregate_packet_path=packet_path,
                aggregate_packet_sha256=packet_sha,
                artifact_hashes=artifacts,
                failure_reason=None,
            )
            terminal_written = True
            return {
                "amendment_id": AMENDMENT_ID,
                "command": "probe",
                "team_id": team_id,
                "candidate_identity_sha256": candidate.identity.sha256,
                "journal_terminal_sha256": terminal.records[-1]["record_sha256"],
                "aggregate_packet_sha256": packet_sha,
                "metrics_sealed": True,
                "cohort_release_ready": len(terminal.terminal_records) == len(cohort.candidates),
                "ok": True,
            }
        except BaseException as error:
            if not terminal_written:
                accounting_error: BaseException | None = None
                try:
                    artifacts = _collect_artifacts(root_path, output_path)
                    artifacts.update(_collect_artifacts(root_path, replay_output_path))
                except BaseException as exc:
                    artifacts = {}
                    accounting_error = exc
                with contextlib.suppress(Exception):
                    _remove_staging(root_path, staging_root)
                reason = _failure_reason(error)
                if accounting_error is not None:
                    reason = (
                        reason + "; artifact accounting: " + _failure_reason(accounting_error)
                    )[:2048]
                event_type = (
                    "aborted" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "failed"
                )
                _append_terminal(
                    root_path,
                    event_type=event_type,
                    request=request,
                    completed_at_utc=_journal_timestamp(accepted),
                    cpu_seconds=max(0.0, _cpu_seconds() - start_cpu),
                    wall_seconds=max(0.0, time.monotonic() - start_wall),
                    gate_vector={},
                    aggregate_packet_path=None,
                    aggregate_packet_sha256=None,
                    artifact_hashes=artifacts,
                    failure_reason=reason,
                )
            if isinstance(error, Amendment0002ValidationError):
                raise
            raise Amendment0002ValidationError(_failure_reason(error)) from error


def _read_released_packet(root: Path, terminal: Mapping[str, Any]) -> Mapping[str, Any]:
    path = _safe_relative(terminal["aggregate_packet_path"], "aggregate packet path")
    payload = orchestrator_v3._read_regular_bytes(root, path)
    if _sha256(payload) != terminal["aggregate_packet_sha256"]:
        raise Amendment0002ValidationError("aggregate packet changed after validation terminal")
    packet = _strict_json(payload, "validation aggregate packet")
    if _canonical_bytes(packet) != payload or packet.get("schema_version") != PACKET_SCHEMA_VERSION:
        raise Amendment0002ValidationError("aggregate packet encoding or schema is invalid")
    return packet


def report(root: str | Path = ".") -> dict[str, object]:
    """Simultaneously release fixed packets only after all four probes are terminal."""

    root_path = orchestrator_v3._trusted_root(root)
    with orchestrator_v3._result_command_lock(root_path):
        activation = verify_activation(root_path)
        cohort = load_cohort(root_path)
        state = _read_validation_journal(root_path)
        _verify_journal_cohort(state, cohort)
        if state.pending_request_sha256s or len(state.accepted_records) != len(cohort.candidates):
            raise Amendment0002ValidationError(
                "cohort report remains sealed until all four probes are terminal"
            )
        terminal_by_team = {str(record["team_id"]): record for record in state.terminal_records}
        results: list[dict[str, object]] = []
        packet_sha256_by_team: dict[str, str | None] = {}
        for candidate in cohort.candidates:
            terminal = terminal_by_team.get(candidate.identity.team_id)
            if terminal is None:
                raise Amendment0002ValidationError("cohort terminal set is incomplete")
            item: dict[str, object] = {
                "rank": candidate.rank,
                "team_id": candidate.identity.team_id,
                "candidate_id": candidate.identity.candidate_id,
                "candidate_identity_sha256": candidate.identity.sha256,
                "terminal_status": terminal["event_type"],
            }
            if terminal["event_type"] == "succeeded":
                item["validation_packet"] = dict(_read_released_packet(root_path, terminal))
                packet_sha256_by_team[candidate.identity.team_id] = str(
                    terminal["aggregate_packet_sha256"]
                )
            else:
                item["validation_packet"] = None
                item["failure_code"] = "validation_dnf"
                packet_sha256_by_team[candidate.identity.team_id] = None
            results.append(item)
        if state.release_record is None:
            state = _append_journal_event(
                root_path,
                {
                    "event_type": "packet_released",
                    "released_at_utc": _journal_timestamp(state),
                    "cohort_freeze_sha256": COHORT_FREEZE_SHA256,
                    "terminal_journal_head_sha256": state.head_sha256,
                    "packet_sha256_by_team": packet_sha256_by_team,
                },
            )
        elif state.release_record["packet_sha256_by_team"] != packet_sha256_by_team:
            raise Amendment0002ValidationError("durable packet release binding changed")
        return {
            "amendment_id": AMENDMENT_ID,
            "command": "report",
            "activation_freeze_sha256": activation.freeze_file_sha256,
            "cohort_freeze_sha256": cohort.file_sha256,
            "validation_journal_head_sha256": state.head_sha256,
            "packet_release_sha256": state.release_record["record_sha256"],
            "cohort_complete": True,
            "results": results,
            "ok": True,
        }


def validate(root: str | Path = ".") -> dict[str, object]:
    root_path = orchestrator_v3._trusted_root(root)
    with orchestrator_v3._result_command_lock(root_path):
        activation = verify_activation(root_path)
        cohort = load_cohort(root_path)
        state = _read_validation_journal(root_path)
        _verify_journal_cohort(state, cohort)
        return {
            "amendment_id": AMENDMENT_ID,
            "command": "validate",
            "activation_freeze_commit": activation.freeze_commit,
            "activation_freeze_sha256": activation.freeze_file_sha256,
            "cohort_freeze_sha256": cohort.file_sha256,
            "validation_journal_head_sha256": state.head_sha256,
            "ok": True,
        }


def status(root: str | Path = ".") -> dict[str, object]:
    """Return nondisclosing validation progress; never return aggregate metrics."""

    root_path = orchestrator_v3._trusted_root(root)
    with orchestrator_v3._result_command_lock(root_path):
        activation = verify_activation(root_path)
        cohort = load_cohort(root_path)
        state = _read_validation_journal(root_path)
        _verify_journal_cohort(state, cohort)
        accepted = {str(record["team_id"]): record for record in state.accepted_records}
        terminals = {str(record["team_id"]): record for record in state.terminal_records}
        teams = {
            candidate.identity.team_id: {
                "probe_consumed": candidate.identity.team_id in accepted,
                "terminal": terminals.get(candidate.identity.team_id, {}).get("event_type"),
            }
            for candidate in cohort.candidates
        }
        return {
            "amendment_id": AMENDMENT_ID,
            "command": "status",
            "activation_freeze_sha256": activation.freeze_file_sha256,
            "cohort_size": len(cohort.candidates),
            "accepted_count": len(accepted),
            "terminal_count": len(terminals),
            "pending_count": len(state.pending_request_sha256s),
            "metrics_sealed": state.release_record is None,
            "teams": teams,
            "ok": True,
        }


__all__ = [
    "ACTIVE_SCRIPT_PATH",
    "AMENDMENT_ID",
    "AMENDMENT_TEST_COMMAND",
    "BASE_TEST_COMMAND",
    "Amendment0002ValidationError",
    "ActivationAuthority",
    "COHORT_FREEZE_PATH",
    "COHORT_FREEZE_SHA256",
    "CohortAuthority",
    "CohortCandidate",
    "IMPLEMENTATION_PATHS",
    "INTEGRATION_FREEZE_PATH",
    "PACKET_SCHEMA_VERSION",
    "ProvisionalActivationFreeze",
    "VALIDATION_JOURNAL_PATH",
    "ValidationJournalState",
    "build_validation_aggregate_packet",
    "freeze_activation",
    "load_cohort",
    "probe",
    "replay_validation_journal_bytes",
    "report",
    "status",
    "validate",
    "verify_activation",
]
