"""Additive activation authority for Top40 Amendment 0001.

The implementation modules remain outside the parent Phase-0 discovery grammar. One exact
discovered sentinel invalidates the historical Phase-0 command path, and the historical organizer
entrypoint is replaced by a fixed tombstone. The immutable parent record and evaluator remain
unchanged. One canonical integration freeze binds the exact parent, journal boundary,
implementation commit and bytes, serial test evidence, and A6 report before the UTC adapter can be
installed temporarily for validate/status/train delegation.
"""

from __future__ import annotations

import base64
import contextlib
import dataclasses
import hashlib
import json
import marshal
import re
import subprocess
import threading
import types
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

from crypto_trade.tournament import (
    journal_v3,
    orchestrator_v3,
    phase0_v3,
    pure_crypto_universe_v6,
    runner_v3,
    top40_amendment_0001,
)

SCHEMA_VERSION = 1
AMENDMENT_ID = top40_amendment_0001.AMENDMENT_ID
AMENDMENT_ROOT = "tournament/top40-v3/amendments/0001"
INTEGRATION_FREEZE_PATH = f"{AMENDMENT_ROOT}/integration-freeze.json"
ACTIVATION_SENTINEL_PATH = "tournament/top40-v3/AMENDMENT-0001-ACTIVE.md"
AMENDMENT_POLICY_PATH = f"{AMENDMENT_ROOT}/AMENDMENT.md"
INCIDENT_PATH = f"{AMENDMENT_ROOT}/INCIDENT.md"
REVIEW_PATH = f"{AMENDMENT_ROOT}/REVIEW.md"
ACTIVATION_JOURNAL_SEQUENCE = 2
ACTIVATION_JOURNAL_HEAD_SHA256 = (
    "1737d4431198669b1d5d64962e6d04052620a6e69175eb8f20b029f89b539d64"
)
MAX_TEST_OUTPUT_BYTES = 4 * 1024 * 1024
HISTORICAL_EVIDENCE_COMMIT = "d1b4f7e233efbdc5cf85d6fff58c2606e40bee8f"
PARENT_PHASE0_FILE_SHA256 = (
    "a4e9b4a0593c65bc94b5eb96858a8e809da803131f103e7ee881e2a13a9cde07"
)
PARENT_PHASE0_RECORD_SHA256 = (
    "4de6efcfb10cab132d3f6430edbaeee7c3070998babec59e009e0175bdc4062f"
)
INCIDENT_SOURCE_ARCHIVE_PATH = (
    "reports-top40-v3/source-archives/sha256/"
    "5f9fe7938315dfc59583cf1265d79c453065b1d8202c12984261fc21e08df60f.json"
)
INCIDENT_SOURCE_ARCHIVE_SHA256 = (
    "5f9fe7938315dfc59583cf1265d79c453065b1d8202c12984261fc21e08df60f"
)
HISTORICAL_ENTRYPOINT_PATH = "scripts/top40_v3_tournament.py"
HISTORICAL_ENTRYPOINT_TOMBSTONE_SHA256 = (
    "b6df7d9ff2179fcc272588d9e89816abf85954d7f11e7ab592ad8236ada14113"
)

INTEGRATION_MODULE_PATH = (
    "src/crypto_trade/tournament/top40_amendment_0001_integration.py"
)
ADAPTER_MODULE_PATH = "src/crypto_trade/tournament/top40_amendment_0001.py"
ACTIVE_SCRIPT_PATH = "scripts/top40_v3_amendment_0001.py"
UTC_TEST_PATH = "tests/tournament/test_top40_amendment_0001_utc_bounds.py"
INTEGRATION_TEST_PATH = "tests/tournament/test_top40_amendment_0001_integration.py"
ADDITIVE_IMPLEMENTATION_PATHS = (
    ADAPTER_MODULE_PATH,
    INTEGRATION_MODULE_PATH,
    ACTIVE_SCRIPT_PATH,
    UTC_TEST_PATH,
    INTEGRATION_TEST_PATH,
    ACTIVATION_SENTINEL_PATH,
    AMENDMENT_POLICY_PATH,
    INCIDENT_PATH,
    REVIEW_PATH,
)
REPLACED_IMPLEMENTATION_PATHS = (HISTORICAL_ENTRYPOINT_PATH,)
IMPLEMENTATION_PATHS = (
    *REPLACED_IMPLEMENTATION_PATHS,
    *ADDITIVE_IMPLEMENTATION_PATHS,
)
EVIDENCE_PATHS = (
    phase0_v3.PHASE0_RECORD_PATH,
    orchestrator_v3.PHASE0_TEST_OUTPUT_PATH,
    orchestrator_v3.LAB_JOURNAL_PATH,
    orchestrator_v3.RUN_STATE_PATH,
    INCIDENT_SOURCE_ARCHIVE_PATH,
    HISTORICAL_ENTRYPOINT_PATH,
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
    UTC_TEST_PATH,
    INTEGRATION_TEST_PATH,
)

_SHA256 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_RECORD_KEYS = frozenset(
    {
        "schema_version",
        "amendment_id",
        "parent_phase0",
        "historical_evidence",
        "activation_journal",
        "config",
        "implementation",
        "base_suite",
        "amendment_tests",
        "a6_report_sha256",
        "record_sha256",
    }
)
_PARENT_KEYS = frozenset(
    {
        "path",
        "file_sha256",
        "record_sha256",
        "chain_head_sha256",
        "scope_head_sha256",
        "scope_file_count",
    }
)
_JOURNAL_KEYS = frozenset(
    {"path", "event_sequence", "head_sha256", "prefix_sha256"}
)
_CONFIG_KEYS = frozenset({"path", "sha256"})
_IMPLEMENTATION_KEYS = frozenset(
    {"commit", "files", "manifest_sha256"}
)
_EVIDENCE_KEYS = frozenset({"commit", "files", "manifest_sha256"})
_FILE_KEYS = frozenset({"path", "size", "sha256"})
_TEST_KEYS = frozenset(
    {
        "command",
        "collected",
        "passed",
        "output_size",
        "output_sha256",
        "output_base64",
    }
)

_PARENT_EVALUATOR_AUTHORITY = top40_amendment_0001.evaluator_authority_sha256
_AMENDED_COMPUTE_METRICS = top40_amendment_0001.compute_metrics_with_utc_bounds
_AMENDED_ADAPTER_EVALUATOR = top40_amendment_0001.evaluator_authority_sha256
_AMENDED_EXPLICIT_UTC = top40_amendment_0001._explicit_utc
_AMENDED_DATE_ONLY = top40_amendment_0001._date_only
_AMENDED_SHA256_FILE = top40_amendment_0001._sha256_file
_FROZEN_AS_UTC_TIMESTAMP = runner_v3._as_utc_timestamp
_READ_REGULAR_BYTES = orchestrator_v3._read_regular_bytes
_FROZEN_PHASE0_AUTHORITY = orchestrator_v3._phase0_authority
_FROZEN_DISCOVERY = phase0_v3._discover_repository_scope
_FROZEN_COMPUTE_METRICS = top40_amendment_0001._PARENT_COMPUTE_METRICS
_FROZEN_EVALUATOR_AUTHORITY = (
    top40_amendment_0001._PARENT_EVALUATOR_AUTHORITY_SHA256
)
_RUNTIME_LOCK = threading.RLock()
_RUNTIME_LOCAL = threading.local()
_RUNTIME_CAPABILITY = object()
_FROZEN_PHASE0_AUTHORITY_CODE_SHA256 = (
    "2c62136da08a9a981ee950ff66d63ed682a40418657cde1dd87dfd25a6a05206"
)
_FROZEN_COMPUTE_METRICS_CODE_SHA256 = (
    "83f4fb0077c32bbfa783737221548fa873973b8729f6de784c12bdb5605bfc4e"
)
_FROZEN_EVALUATOR_AUTHORITY_CODE_SHA256 = (
    "20054b17bfea25f40c1f1d0bddf21d9db285fdc2bc29be996a013a26c7177ed3"
)
_FROZEN_DISCOVERY_CODE_SHA256 = (
    "b75cf742bfa5fd79c5c0f0f3bec54f28ce600114a8634b6d7089f89846bcdbf0"
)
_FROZEN_AS_UTC_TIMESTAMP_CODE_SHA256 = (
    "dabc0f72f5c8f294b4635433a436a5e62ee514ceb351fd09d828d9e404b36276"
)
_AMENDED_COMPUTE_METRICS_CODE_SHA256 = (
    "713a0debb4988c1753a79af2cf659f6d8f215379b61ccb6a074ed17a0f1f3eb6"
)
_AMENDED_ADAPTER_EVALUATOR_CODE_SHA256 = (
    "2d158eb1f119a0446788a53b90652da70147fe5396bcf767fe537cf0e48b8eb2"
)
_AMENDED_EXPLICIT_UTC_CODE_SHA256 = (
    "ef6d6681a5735f87fcadd622d4ca5eebaf859da78a2f02a498458d1f8657c78e"
)
_AMENDED_DATE_ONLY_CODE_SHA256 = (
    "f0469301697a3b53cee2ea9b7ae6187f4db83abc6233b7c4bc75ba4bfbfa6fb0"
)
_AMENDED_SHA256_FILE_CODE_SHA256 = (
    "6b771af8b5a3f140284481deaf0e0d371fd13e5c76e175315b807b4d86f4daa7"
)
_INTEGRATION_EVALUATOR_CODE_SHA256 = (
    "cb49bcd603574ad00d600ff32bd31db2d30eddbd1d2dfe5a7d4da529343697d7"
)
_AMENDED_PHASE0_AUTHORITY_CODE_SHA256 = (
    "dd056978121686c128a58bbb67ec29fef66fd1f152707428390250246a691098"
)
_VERIFY_INTEGRATION_CODE_SHA256 = (
    "4fa5d4eb456385fbb39c144e5160200c81ad723eca8ce5232d454edb1784c793"
)
_HISTORICAL_PHASE0_AUTHORITY_CODE_SHA256 = (
    "9e6bc71301509f1db1587cc1c7bca6b5c66ef2ec794b314139e352d192432573"
)
_SHA256_FUNCTION_CODE_SHA256 = (
    "60087a57a1cf582ab101b7528f397ba45f0fad842c6753843681b0c8001cf985"
)
_CANONICAL_BYTES_FUNCTION_CODE_SHA256 = (
    "a650b7105920e423432dd3f142d68b17d9b7c8957473b3c827257ad9b14a2ee4"
)
_READ_REGULAR_BYTES_CODE_SHA256 = (
    "8c81b7628990605bf234dde98e31fa2c7daed522bf416468573692cfad2760cf"
)


class Amendment0001IntegrationError(orchestrator_v3.OrchestratorError):
    """The amendment integration authority is absent, changed, or incomplete."""


@dataclasses.dataclass(frozen=True, slots=True)
class IntegrationAuthority:
    freeze_file_sha256: str
    freeze_commit: str
    record_sha256: str
    implementation_commit: str
    config_sha256: str
    parent_phase0_record_sha256: str
    activation_journal_head_sha256: str


@dataclasses.dataclass(frozen=True, slots=True)
class ProvisionalIntegrationFreeze:
    freeze_file_sha256: str
    record_sha256: str
    implementation_commit: str
    activation: str = "pending-unique-freeze-commit"


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
        raise Amendment0001IntegrationError(
            "integration payload is not finite canonical JSON"
        ) from exc


_SHA256_FUNCTION = _sha256
_CANONICAL_BYTES_FUNCTION = _canonical_bytes


def _exact_mapping(value: object, keys: frozenset[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != set(keys):
        raise Amendment0001IntegrationError(f"{label} has missing or unknown fields")
    return value


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise Amendment0001IntegrationError(f"{label} must be a lowercase SHA-256")
    return value


def _historically_discovered(relative: str) -> bool:
    path = PurePosixPath(relative)
    parent = path.parent.as_posix()
    name = path.name
    if parent == "tournament/top40-v3":
        return name.endswith(".md") or name == "config.toml"
    if parent == "src/crypto_trade/tournament":
        return name.endswith("_v3.py") and name != "amended_orchestrator_compat_v3.py"
    if parent == "tests/tournament":
        return name.endswith(".py") and "v3" in name
    return False


def _historical_phase0_authority(root: Path) -> phase0_v3.Phase0Authority:
    """Verify the parent record plus the exact sentinel and entrypoint-tombstone delta."""

    payload = orchestrator_v3._read_regular_bytes(root, phase0_v3.PHASE0_RECORD_PATH)
    output = orchestrator_v3._read_regular_bytes(
        root, orchestrator_v3.PHASE0_TEST_OUTPUT_PATH
    )
    if _sha256(payload) != PARENT_PHASE0_FILE_SHA256:
        raise Amendment0001IntegrationError("historical Phase-0 file hash changed")
    record = orchestrator_v3._strict_json_object(payload, "historical Phase-0 record")
    if orchestrator_v3._pretty_json_bytes(record) != payload:
        raise Amendment0001IntegrationError("historical Phase-0 record is not canonical")
    if record.get("record_sha256") != PARENT_PHASE0_RECORD_SHA256:
        raise Amendment0001IntegrationError("historical Phase-0 internal hash changed")
    raw_entries = record.get("scope_entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise Amendment0001IntegrationError("historical Phase-0 scope is missing")
    if len(raw_entries) != 54 or not all(isinstance(entry, Mapping) for entry in raw_entries):
        raise Amendment0001IntegrationError("historical Phase-0 scope entries are malformed")
    recorded_paths = tuple(str(entry["path"]) for entry in raw_entries)
    historical_discovery = tuple(
        path for path in recorded_paths if _historically_discovered(path)
    )
    live_discovery = tuple(_FROZEN_DISCOVERY(root))
    if set(live_discovery) != set((*historical_discovery, ACTIVATION_SENTINEL_PATH)):
        raise Amendment0001IntegrationError(
            "live Phase-0 discovery differs from the historical scope plus activation sentinel"
        )
    tombstone = orchestrator_v3._read_regular_bytes(root, HISTORICAL_ENTRYPOINT_PATH)
    if _sha256(tombstone) != HISTORICAL_ENTRYPOINT_TOMBSTONE_SHA256:
        raise Amendment0001IntegrationError("historical entrypoint tombstone changed")
    historical_entrypoint = _git(
        root,
        ["show", f"{HISTORICAL_EVIDENCE_COMMIT}:{HISTORICAL_ENTRYPOINT_PATH}"],
    )
    if historical_entrypoint.returncode != 0:
        raise Amendment0001IntegrationError(
            "historical evidence commit has no parent organizer entrypoint"
        )

    for entry in raw_entries:
        relative = str(entry["path"])
        expected_size = entry.get("size")
        expected_sha256 = entry.get("sha256")
        current = (
            historical_entrypoint.stdout
            if relative == HISTORICAL_ENTRYPOINT_PATH
            else orchestrator_v3._read_regular_bytes(root, relative)
        )
        if len(current) != expected_size or _sha256(current) != expected_sha256:
            raise Amendment0001IntegrationError(
                f"historical Phase-0 scoped bytes changed: {relative}"
            )

    targeted = record.get("targeted_tests")
    expected_output_sha256 = (
        targeted.get("payload", {}).get("output_sha256")
        if isinstance(targeted, Mapping)
        else None
    )
    if _sha256(output) != expected_output_sha256:
        raise Amendment0001IntegrationError("historical Phase-0 test output changed")
    a6 = record.get("a6_audit")
    expected_a6_sha256 = a6.get("report_sha256") if isinstance(a6, Mapping) else None
    live_a6 = pure_crypto_universe_v6.audit_report_bytes(root)
    if _sha256(live_a6) != expected_a6_sha256:
        raise Amendment0001IntegrationError("historical Phase-0 A6 authority changed")

    return phase0_v3.Phase0Authority(
        record_sha256=str(record["record_sha256"]),
        chain_head_sha256=_require_sha256(
            record.get("chain_head_sha256"), "historical chain_head_sha256"
        ),
        scope_head_sha256=_require_sha256(
            record.get("scope_head_sha256"), "historical scope_head_sha256"
        ),
        scope_file_count=len(raw_entries),
    )


_HISTORICAL_PHASE0_AUTHORITY = _historical_phase0_authority


def _parent_phase0(root: Path) -> dict[str, object]:
    authority = _HISTORICAL_PHASE0_AUTHORITY(root)
    payload = orchestrator_v3._read_regular_bytes(root, phase0_v3.PHASE0_RECORD_PATH)
    return {
        "path": phase0_v3.PHASE0_RECORD_PATH,
        "file_sha256": _sha256(payload),
        "record_sha256": authority.record_sha256,
        "chain_head_sha256": authority.chain_head_sha256,
        "scope_head_sha256": authority.scope_head_sha256,
        "scope_file_count": authority.scope_file_count,
    }


def _journal_boundary(root: Path, *, require_exact_boundary: bool) -> dict[str, object]:
    payload = orchestrator_v3._read_regular_bytes(root, orchestrator_v3.LAB_JOURNAL_PATH)
    lines = payload.splitlines(keepends=True)
    if len(lines) < ACTIVATION_JOURNAL_SEQUENCE:
        raise Amendment0001IntegrationError("train journal predates the activation boundary")
    prefix = b"".join(lines[:ACTIVATION_JOURNAL_SEQUENCE])
    try:
        prefix_state = journal_v3.replay_journal_bytes(prefix)
        full_state = journal_v3.replay_journal_bytes(payload)
    except journal_v3.JournalValidationError as exc:
        raise Amendment0001IntegrationError(f"train journal is invalid: {exc}") from exc
    if (
        prefix_state.record_count != ACTIVATION_JOURNAL_SEQUENCE
        or prefix_state.head_sha256 != ACTIVATION_JOURNAL_HEAD_SHA256
    ):
        raise Amendment0001IntegrationError(
            "train journal no longer has the exact Amendment 0001 activation prefix"
        )
    first, second = prefix_state.records
    if (
        first.get("record_sha256")
        != "68ec70faf91c82a7f689484f3cd0106e4570569d15bf02823c7cf8aafe59f08f"
        or first.get("event_type") != "request_accepted"
        or first.get("team_id") != "team-04"
        or first.get("source_archive_path") != INCIDENT_SOURCE_ARCHIVE_PATH
        or first.get("source_archive_sha256") != INCIDENT_SOURCE_ARCHIVE_SHA256
        or second.get("record_sha256") != ACTIVATION_JOURNAL_HEAD_SHA256
        or second.get("event_type") != "failed"
        or second.get("request_sha256") != first.get("record_sha256")
        or second.get("metric_packet_sha256") is not None
        or second.get("gate_vector") != {}
        or second.get("artifact_hashes") != {}
        or prefix_state.pending_request_sha256s
        or prefix_state.team_run_sequences != {"team-04": 1}
        or prefix_state.material_trial_counts != {"team-04": 1}
    ):
        raise Amendment0001IntegrationError(
            "activation prefix is not the exact nondisclosing Team 04 infrastructure incident"
        )
    if require_exact_boundary and (
        full_state.record_count != ACTIVATION_JOURNAL_SEQUENCE
        or full_state.head_sha256 != ACTIVATION_JOURNAL_HEAD_SHA256
    ):
        raise Amendment0001IntegrationError(
            "integration freeze requires the untouched activation journal boundary"
        )
    if require_exact_boundary:
        committed_state = _git(
            root,
            [
                "show",
                f"{HISTORICAL_EVIDENCE_COMMIT}:{orchestrator_v3.RUN_STATE_PATH}",
            ],
        )
        live_state = orchestrator_v3._read_regular_bytes(
            root, orchestrator_v3.RUN_STATE_PATH
        )
        if committed_state.returncode != 0 or committed_state.stdout != live_state:
            raise Amendment0001IntegrationError(
                "integration freeze requires the committed activation run-state projection"
            )
    return {
        "path": orchestrator_v3.LAB_JOURNAL_PATH,
        "event_sequence": ACTIVATION_JOURNAL_SEQUENCE,
        "head_sha256": ACTIVATION_JOURNAL_HEAD_SHA256,
        "prefix_sha256": _sha256(prefix),
    }


def _config_authority(root: Path) -> tuple[Any, dict[str, str]]:
    config = orchestrator_v3._load_active_config(root)
    return config, {"path": orchestrator_v3.CONFIG_PATH, "sha256": config.sha256}


def _implementation_entries(root: Path) -> tuple[dict[str, object], ...]:
    entries: list[dict[str, object]] = []
    for relative in IMPLEMENTATION_PATHS:
        payload = orchestrator_v3._read_regular_bytes(root, relative)
        entries.append({"path": relative, "size": len(payload), "sha256": _sha256(payload)})
    return tuple(entries)


def _implementation_manifest_sha256(entries: Sequence[Mapping[str, object]]) -> str:
    return _sha256(_canonical_bytes(list(entries)))


def _git(
    root: Path,
    arguments: Sequence[str],
    *,
    capture_stdout: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )


def _verified_commit(root: Path, commit: str, label: str) -> None:
    if not isinstance(commit, str) or _COMMIT.fullmatch(commit) is None:
        raise Amendment0001IntegrationError(f"{label} must be a full lowercase 40-hex commit")
    resolved = _git(root, ["rev-parse", "--verify", f"{commit}^{{commit}}"]).stdout
    if resolved.decode("ascii", "replace").strip() != commit:
        raise Amendment0001IntegrationError(f"{label} is not a repository commit")
    ancestor = _git(
        root,
        ["merge-base", "--is-ancestor", commit, "HEAD"],
        capture_stdout=False,
    )
    if ancestor.returncode != 0:
        raise Amendment0001IntegrationError(f"{label} is not in current HEAD ancestry")


def _commit_entries(
    root: Path,
    commit: str,
    paths: Sequence[str],
) -> tuple[dict[str, object], ...]:
    _verified_commit(root, commit, "historical evidence commit")
    entries: list[dict[str, object]] = []
    for relative in paths:
        blob = _git(root, ["show", f"{commit}:{relative}"])
        if blob.returncode != 0:
            raise Amendment0001IntegrationError(
                f"historical evidence commit does not contain {relative}"
            )
        entries.append(
            {"path": relative, "size": len(blob.stdout), "sha256": _sha256(blob.stdout)}
        )
    return tuple(entries)


def _historical_evidence(root: Path) -> dict[str, object]:
    entries = _commit_entries(root, HISTORICAL_EVIDENCE_COMMIT, EVIDENCE_PATHS)
    by_path = {str(entry["path"]): entry for entry in entries}
    if by_path[phase0_v3.PHASE0_RECORD_PATH]["sha256"] != PARENT_PHASE0_FILE_SHA256:
        raise Amendment0001IntegrationError("evidence commit has the wrong Phase-0 record")
    if (
        by_path[INCIDENT_SOURCE_ARCHIVE_PATH]["sha256"]
        != INCIDENT_SOURCE_ARCHIVE_SHA256
    ):
        raise Amendment0001IntegrationError("evidence commit has the wrong source archive")
    for relative in (
        phase0_v3.PHASE0_RECORD_PATH,
        orchestrator_v3.PHASE0_TEST_OUTPUT_PATH,
        INCIDENT_SOURCE_ARCHIVE_PATH,
    ):
        live = orchestrator_v3._read_regular_bytes(root, relative)
        if len(live) != by_path[relative]["size"] or _sha256(live) != by_path[relative]["sha256"]:
            raise Amendment0001IntegrationError(
                f"immutable historical evidence changed: {relative}"
            )
    committed_journal = _git(
        root,
        ["show", f"{HISTORICAL_EVIDENCE_COMMIT}:{orchestrator_v3.LAB_JOURNAL_PATH}"],
    ).stdout
    live_journal = orchestrator_v3._read_regular_bytes(root, orchestrator_v3.LAB_JOURNAL_PATH)
    live_prefix = b"".join(
        live_journal.splitlines(keepends=True)[:ACTIVATION_JOURNAL_SEQUENCE]
    )
    if committed_journal != live_prefix:
        raise Amendment0001IntegrationError(
            "live journal is not an append-only extension of committed incident evidence"
        )
    return {
        "commit": HISTORICAL_EVIDENCE_COMMIT,
        "files": list(entries),
        "manifest_sha256": _implementation_manifest_sha256(entries),
    }


def _verify_implementation_commit(
    root: Path,
    commit: str,
    entries: Sequence[Mapping[str, object]],
) -> None:
    _verified_commit(root, commit, "implementation_commit")
    parent = _git(root, ["rev-parse", f"{commit}^"])
    if (
        parent.returncode != 0
        or parent.stdout.decode("ascii", "replace").strip()
        != HISTORICAL_EVIDENCE_COMMIT
    ):
        raise Amendment0001IntegrationError(
            "implementation_commit must directly follow the historical evidence commit"
        )
    changed = _git(root, ["diff-tree", "--no-commit-id", "--name-status", "-r", commit])
    if changed.returncode != 0:
        raise Amendment0001IntegrationError("cannot inspect implementation_commit delta")
    observed_delta: dict[str, str] = {}
    for line in changed.stdout.decode("utf-8", "replace").splitlines():
        status, separator, relative = line.partition("\t")
        if not separator or relative in observed_delta:
            raise Amendment0001IntegrationError("implementation_commit delta is malformed")
        observed_delta[relative] = status
    expected_delta = {
        **{relative: "M" for relative in REPLACED_IMPLEMENTATION_PATHS},
        **{relative: "A" for relative in ADDITIVE_IMPLEMENTATION_PATHS},
    }
    if observed_delta != expected_delta:
        raise Amendment0001IntegrationError(
            "implementation_commit contains bytes outside the exact Amendment 0001 delta"
        )
    entry_by_path = {str(entry["path"]): entry for entry in entries}
    for relative in IMPLEMENTATION_PATHS:
        if relative in ADDITIVE_IMPLEMENTATION_PATHS:
            first_add = _git(
                root,
                ["log", "--diff-filter=A", "--format=%H", "--", relative],
            )
            additions = [
                line
                for line in first_add.stdout.decode("ascii", "replace").splitlines()
                if line
            ]
            if first_add.returncode != 0 or additions != [commit]:
                raise Amendment0001IntegrationError(
                    "implementation path was not first-added exactly at "
                    f"implementation_commit: {relative}"
                )
        committed = _git(root, ["show", f"{commit}:{relative}"])
        if committed.returncode != 0:
            raise Amendment0001IntegrationError(
                f"implementation_commit does not contain {relative}"
            )
        expected = entry_by_path[relative]
        if (
            len(committed.stdout) != expected["size"]
            or _sha256(committed.stdout) != expected["sha256"]
        ):
            raise Amendment0001IntegrationError(
                f"live implementation differs from implementation_commit: {relative}"
            )


def _verify_freeze_commit(
    root: Path,
    *,
    implementation_commit: str,
    freeze_bytes: bytes,
) -> str:
    first_add = _git(
        root,
        ["log", "--diff-filter=A", "--format=%H", "--", INTEGRATION_FREEZE_PATH],
    )
    additions = [
        line
        for line in first_add.stdout.decode("ascii", "replace").splitlines()
        if line
    ]
    if first_add.returncode != 0 or len(additions) != 1:
        raise Amendment0001IntegrationError(
            "integration freeze is not active until one unique first-add commit exists"
        )
    freeze_commit = additions[0]
    _verified_commit(root, freeze_commit, "integration freeze commit")
    parent = _git(root, ["rev-parse", f"{freeze_commit}^"])
    if (
        parent.returncode != 0
        or parent.stdout.decode("ascii", "replace").strip() != implementation_commit
    ):
        raise Amendment0001IntegrationError(
            "integration freeze commit must directly follow implementation_commit"
        )
    changed = _git(
        root,
        ["diff-tree", "--no-commit-id", "--name-status", "-r", freeze_commit],
    )
    if (
        changed.returncode != 0
        or changed.stdout.decode("utf-8", "replace").splitlines()
        != [f"A\t{INTEGRATION_FREEZE_PATH}"]
    ):
        raise Amendment0001IntegrationError(
            "integration freeze commit contains an unexpected repository delta"
        )
    committed = _git(root, ["show", f"{freeze_commit}:{INTEGRATION_FREEZE_PATH}"])
    if committed.returncode != 0 or committed.stdout != freeze_bytes:
        raise Amendment0001IntegrationError(
            "live integration freeze differs from its activation commit"
        )
    return freeze_commit


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
        raise Amendment0001IntegrationError(
            f"{label} failed with exit code {completed.returncode}"
        )
    if not isinstance(output, bytes) or not output or len(output) > MAX_TEST_OUTPUT_BYTES:
        raise Amendment0001IntegrationError(f"{label} output is missing or too large")
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


def _decode_test_evidence(
    value: object,
    *,
    expected_command: Sequence[str],
    label: str,
) -> bytes:
    evidence = _exact_mapping(value, _TEST_KEYS, label)
    if evidence["command"] != list(expected_command):
        raise Amendment0001IntegrationError(f"{label} command differs from canonical command")
    if (
        type(evidence["collected"]) is not int
        or evidence["collected"] <= 0
        or evidence["passed"] != evidence["collected"]
        or type(evidence["output_size"]) is not int
        or evidence["output_size"] <= 0
    ):
        raise Amendment0001IntegrationError(f"{label} counts are invalid")
    _require_sha256(evidence["output_sha256"], f"{label}.output_sha256")
    encoded = evidence["output_base64"]
    if not isinstance(encoded, str):
        raise Amendment0001IntegrationError(f"{label}.output_base64 is invalid")
    try:
        output = base64.b64decode(encoded.encode("ascii"), validate=True)
    except Exception as exc:
        raise Amendment0001IntegrationError(f"{label}.output_base64 is invalid") from exc
    if (
        base64.b64encode(output).decode("ascii") != encoded
        or len(output) != evidence["output_size"]
        or _sha256(output) != evidence["output_sha256"]
        or orchestrator_v3._parse_passed_count(output) != evidence["collected"]
    ):
        raise Amendment0001IntegrationError(f"{label} output binding is invalid")
    return output


def _a6_report_sha256(root: Path, config: Any) -> str:
    report = pure_crypto_universe_v6.audit_report_bytes(root)
    digest = _sha256(report)
    expected = config.raw["universe"]["a6_authority"]["audit_report_sha256"]
    if digest != expected:
        raise Amendment0001IntegrationError("A6 report differs from the active config authority")
    return digest


def _record_body(
    *,
    parent_phase0: Mapping[str, object],
    historical_evidence: Mapping[str, object],
    journal: Mapping[str, object],
    config: Mapping[str, object],
    implementation_commit: str,
    implementation_entries: Sequence[Mapping[str, object]],
    base_output: bytes,
    amendment_output: bytes,
    a6_report_sha256: str,
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "amendment_id": AMENDMENT_ID,
        "parent_phase0": dict(parent_phase0),
        "historical_evidence": dict(historical_evidence),
        "activation_journal": dict(journal),
        "config": dict(config),
        "implementation": {
            "commit": implementation_commit,
            "files": [dict(entry) for entry in implementation_entries],
            "manifest_sha256": _implementation_manifest_sha256(implementation_entries),
        },
        "base_suite": _test_evidence(phase0_v3.TARGETED_TEST_COMMAND, base_output),
        "amendment_tests": _test_evidence(AMENDMENT_TEST_COMMAND, amendment_output),
        "a6_report_sha256": a6_report_sha256,
    }


def _authority_from_record(
    record: Mapping[str, Any],
    freeze_bytes: bytes,
    freeze_commit: str,
) -> IntegrationAuthority:
    return IntegrationAuthority(
        freeze_file_sha256=_sha256(freeze_bytes),
        freeze_commit=freeze_commit,
        record_sha256=str(record["record_sha256"]),
        implementation_commit=str(record["implementation"]["commit"]),
        config_sha256=str(record["config"]["sha256"]),
        parent_phase0_record_sha256=str(record["parent_phase0"]["record_sha256"]),
        activation_journal_head_sha256=str(record["activation_journal"]["head_sha256"]),
    )


def verify_integration(root: str | Path = ".") -> IntegrationAuthority:
    """Verify the immutable integration freeze against all live parent authorities."""

    root_path = orchestrator_v3._trusted_root(root)
    freeze_bytes = orchestrator_v3._read_regular_bytes(root_path, INTEGRATION_FREEZE_PATH)
    record = orchestrator_v3._strict_json_object(freeze_bytes, "Amendment 0001 integration freeze")
    if orchestrator_v3._pretty_json_bytes(record) != freeze_bytes:
        raise Amendment0001IntegrationError("integration freeze is not canonical pretty JSON")
    record = _exact_mapping(record, _RECORD_KEYS, "integration freeze")
    body = {key: record[key] for key in _RECORD_KEYS - {"record_sha256"}}
    if (
        record["schema_version"] != SCHEMA_VERSION
        or record["amendment_id"] != AMENDMENT_ID
        or _require_sha256(record["record_sha256"], "record_sha256")
        != _sha256(_canonical_bytes(body))
    ):
        raise Amendment0001IntegrationError("integration freeze identity or hash is invalid")

    parent = _exact_mapping(record["parent_phase0"], _PARENT_KEYS, "parent_phase0")
    if dict(parent) != _parent_phase0(root_path):
        raise Amendment0001IntegrationError("parent Phase-0 authority changed")
    evidence = _exact_mapping(
        record["historical_evidence"], _EVIDENCE_KEYS, "historical_evidence"
    )
    live_evidence = _historical_evidence(root_path)
    if dict(evidence) != live_evidence:
        raise Amendment0001IntegrationError("historical incident evidence changed")
    journal = _exact_mapping(
        record["activation_journal"], _JOURNAL_KEYS, "activation_journal"
    )
    if dict(journal) != _journal_boundary(root_path, require_exact_boundary=False):
        raise Amendment0001IntegrationError("activation journal prefix changed")
    config, config_authority = _config_authority(root_path)
    frozen_config = _exact_mapping(record["config"], _CONFIG_KEYS, "config")
    if dict(frozen_config) != config_authority:
        raise Amendment0001IntegrationError("active config changed after integration freeze")

    implementation = _exact_mapping(
        record["implementation"], _IMPLEMENTATION_KEYS, "implementation"
    )
    files = implementation["files"]
    if not isinstance(files, list) or len(files) != len(IMPLEMENTATION_PATHS):
        raise Amendment0001IntegrationError("implementation file list is invalid")
    normalized_files = [
        dict(_exact_mapping(item, _FILE_KEYS, "implementation file")) for item in files
    ]
    if [item["path"] for item in normalized_files] != list(IMPLEMENTATION_PATHS):
        raise Amendment0001IntegrationError("implementation file order or paths changed")
    live_entries = _implementation_entries(root_path)
    if normalized_files != list(live_entries):
        raise Amendment0001IntegrationError("implementation bytes changed after integration freeze")
    if implementation["manifest_sha256"] != _implementation_manifest_sha256(live_entries):
        raise Amendment0001IntegrationError("implementation manifest hash is invalid")
    _verify_implementation_commit(root_path, implementation["commit"], live_entries)

    _decode_test_evidence(
        record["base_suite"],
        expected_command=phase0_v3.TARGETED_TEST_COMMAND,
        label="base_suite",
    )
    _decode_test_evidence(
        record["amendment_tests"],
        expected_command=AMENDMENT_TEST_COMMAND,
        label="amendment_tests",
    )
    expected_a6 = config.raw["universe"]["a6_authority"]["audit_report_sha256"]
    if record["a6_report_sha256"] != expected_a6:
        raise Amendment0001IntegrationError("frozen A6 report hash changed")
    freeze_commit = _verify_freeze_commit(
        root_path,
        implementation_commit=str(implementation["commit"]),
        freeze_bytes=freeze_bytes,
    )
    return _authority_from_record(record, freeze_bytes, freeze_commit)


_VERIFY_INTEGRATION = verify_integration
_VERIFY_INTEGRATION_LOCAL_BINDINGS = (
    ("_exact_mapping", _exact_mapping),
    ("_require_sha256", _require_sha256),
    ("_sha256", _SHA256_FUNCTION),
    ("_canonical_bytes", _CANONICAL_BYTES_FUNCTION),
    ("_parent_phase0", _parent_phase0),
    ("_historical_evidence", _historical_evidence),
    ("_journal_boundary", _journal_boundary),
    ("_config_authority", _config_authority),
    ("_implementation_entries", _implementation_entries),
    ("_implementation_manifest_sha256", _implementation_manifest_sha256),
    ("_verify_implementation_commit", _verify_implementation_commit),
    ("_decode_test_evidence", _decode_test_evidence),
    ("_verify_freeze_commit", _verify_freeze_commit),
    ("_authority_from_record", _authority_from_record),
)
_VERIFY_INTEGRATION_ORCHESTRATOR_BINDINGS = (
    ("_trusted_root", orchestrator_v3._trusted_root),
    ("_read_regular_bytes", _READ_REGULAR_BYTES),
    ("_strict_json_object", orchestrator_v3._strict_json_object),
    ("_pretty_json_bytes", orchestrator_v3._pretty_json_bytes),
)


def freeze_integration(
    root: str | Path,
    *,
    implementation_commit: str,
) -> ProvisionalIntegrationFreeze:
    """Run serial evidence and write the canonical integration freeze exactly once."""

    root_path = orchestrator_v3._trusted_root(root)
    with orchestrator_v3._result_command_lock(root_path):
        freeze_path = root_path / INTEGRATION_FREEZE_PATH
        if freeze_path.exists() or freeze_path.is_symlink():
            raise Amendment0001IntegrationError(
                "integration freeze already exists and cannot be replaced or replayed"
            )

        parent_before = _parent_phase0(root_path)
        evidence_before = _historical_evidence(root_path)
        journal_before = _journal_boundary(root_path, require_exact_boundary=True)
        config, config_before = _config_authority(root_path)
        implementation_before = _implementation_entries(root_path)
        _verify_implementation_commit(
            root_path, implementation_commit, implementation_before
        )

        base_output = _run_test_command(
            root_path, phase0_v3.TARGETED_TEST_COMMAND, "canonical base suite"
        )
        if _parent_phase0(root_path) != parent_before:
            raise Amendment0001IntegrationError("parent Phase-0 changed during base suite")
        amendment_output = _run_test_command(
            root_path, AMENDMENT_TEST_COMMAND, "Amendment 0001 tests"
        )
        a6_sha256 = _a6_report_sha256(root_path, config)

        if (
            _parent_phase0(root_path) != parent_before
            or _historical_evidence(root_path) != evidence_before
            or _journal_boundary(root_path, require_exact_boundary=True) != journal_before
            or _config_authority(root_path)[1] != config_before
            or _implementation_entries(root_path) != implementation_before
        ):
            raise Amendment0001IntegrationError(
                "parent scope or amendment inputs changed during integration freeze"
            )
        body = _record_body(
            parent_phase0=parent_before,
            historical_evidence=evidence_before,
            journal=journal_before,
            config=config_before,
            implementation_commit=implementation_commit,
            implementation_entries=implementation_before,
            base_output=base_output,
            amendment_output=amendment_output,
            a6_report_sha256=a6_sha256,
        )
        record = {**body, "record_sha256": _sha256(_canonical_bytes(body))}
        try:
            orchestrator_v3._write_new_file(
                root_path,
                INTEGRATION_FREEZE_PATH,
                orchestrator_v3._pretty_json_bytes(record),
                mode=0o444,
            )
        except (OSError, orchestrator_v3.OrchestratorError) as exc:
            raise Amendment0001IntegrationError(
                f"cannot durably write integration freeze: {exc}"
            ) from exc
        freeze_bytes = orchestrator_v3._read_regular_bytes(
            root_path, INTEGRATION_FREEZE_PATH
        )
        return ProvisionalIntegrationFreeze(
            freeze_file_sha256=_sha256(freeze_bytes),
            record_sha256=str(record["record_sha256"]),
            implementation_commit=implementation_commit,
        )


def evaluator_authority_sha256(root: Path) -> str:
    """Composite evaluator identity for every post-activation run."""

    authority = _VERIFY_INTEGRATION(root)
    parent_evaluator = _PARENT_EVALUATOR_AUTHORITY(root)
    payload = {
        "amendment_id": AMENDMENT_ID,
        "adapter_evaluator_sha256": parent_evaluator,
        "integration_freeze_sha256": authority.freeze_file_sha256,
        "integration_module_sha256": _SHA256_FUNCTION(
            _READ_REGULAR_BYTES(root, INTEGRATION_MODULE_PATH)
        ),
    }
    return _SHA256_FUNCTION(_CANONICAL_BYTES_FUNCTION(payload))


def _normalized_code(code: types.CodeType) -> types.CodeType:
    return code.replace(
        co_filename="<frozen>",
        co_firstlineno=1,
        co_consts=tuple(
            _normalized_code(value) if isinstance(value, types.CodeType) else value
            for value in code.co_consts
        ),
    )


def _code_sha256(code: types.CodeType) -> str:
    return _sha256(marshal.dumps(_normalized_code(code)))


def _verify_callable(
    value: object,
    *,
    module: str,
    name: str,
    path: Path,
    code_sha256: str,
    globals_dict: Mapping[str, object],
    defaults: tuple[object, ...] | None = None,
    kwdefaults: Mapping[str, object] | None = None,
) -> None:
    code = getattr(value, "__code__", None)
    code_path = Path(getattr(code, "co_filename", "")).resolve()
    if (
        getattr(value, "__module__", None) != module
        or getattr(value, "__name__", None) != name
        or not isinstance(code, types.CodeType)
        or code_path != path.resolve()
        or _code_sha256(code) != code_sha256
        or getattr(value, "__globals__", None) is not globals_dict
        or getattr(value, "__defaults__", None) != defaults
        or getattr(value, "__kwdefaults__", None) != kwdefaults
        or getattr(value, "__closure__", None) is not None
    ):
        raise Amendment0001IntegrationError(
            f"frozen callable authority is invalid: {module}.{name}"
        )


def _verify_frozen_runtime_bindings() -> None:
    _verify_callable(
        _FROZEN_PHASE0_AUTHORITY,
        module=orchestrator_v3.__name__,
        name="_phase0_authority",
        path=Path(orchestrator_v3.__file__),
        code_sha256=_FROZEN_PHASE0_AUTHORITY_CODE_SHA256,
        globals_dict=vars(orchestrator_v3),
    )
    _verify_callable(
        _FROZEN_COMPUTE_METRICS,
        module=runner_v3.__name__,
        name="_compute_metrics",
        path=Path(runner_v3.__file__),
        code_sha256=_FROZEN_COMPUTE_METRICS_CODE_SHA256,
        globals_dict=vars(runner_v3),
    )
    _verify_callable(
        _FROZEN_EVALUATOR_AUTHORITY,
        module=runner_v3.__name__,
        name="_evaluator_authority_sha256",
        path=Path(runner_v3.__file__),
        code_sha256=_FROZEN_EVALUATOR_AUTHORITY_CODE_SHA256,
        globals_dict=vars(runner_v3),
    )
    _verify_callable(
        _FROZEN_DISCOVERY,
        module=phase0_v3.__name__,
        name="_discover_repository_scope",
        path=Path(phase0_v3.__file__),
        code_sha256=_FROZEN_DISCOVERY_CODE_SHA256,
        globals_dict=vars(phase0_v3),
    )
    _verify_callable(
        _FROZEN_AS_UTC_TIMESTAMP,
        module=runner_v3.__name__,
        name="_as_utc_timestamp",
        path=Path(runner_v3.__file__),
        code_sha256=_FROZEN_AS_UTC_TIMESTAMP_CODE_SHA256,
        globals_dict=vars(runner_v3),
    )
    if (
        orchestrator_v3._phase0_authority is not _FROZEN_PHASE0_AUTHORITY
        or runner_v3._compute_metrics is not _FROZEN_COMPUTE_METRICS
        or runner_v3._evaluator_authority_sha256 is not _FROZEN_EVALUATOR_AUTHORITY
        or runner_v3._as_utc_timestamp is not _FROZEN_AS_UTC_TIMESTAMP
        or phase0_v3._discover_repository_scope is not _FROZEN_DISCOVERY
    ):
        raise Amendment0001IntegrationError(
            "frozen runtime globals were replaced before Amendment 0001 activation"
        )


def _amended_phase0_authority(root: Path) -> phase0_v3.Phase0Authority:
    if getattr(_RUNTIME_LOCAL, "capability", None) is not _RUNTIME_CAPABILITY:
        raise Amendment0001IntegrationError(
            "amended Phase-0 authority was called outside the private integration transaction"
        )
    _VERIFY_INTEGRATION(root)
    return _HISTORICAL_PHASE0_AUTHORITY(root)


_AMENDED_PHASE0_AUTHORITY = _amended_phase0_authority
_INTEGRATION_EVALUATOR = evaluator_authority_sha256


def _verify_amended_runtime_bindings() -> None:
    adapter_globals = vars(top40_amendment_0001)
    integration_globals = globals()
    adapter_path = Path(top40_amendment_0001.__file__)
    integration_path = Path(__file__)
    for value, name, digest in (
        (
            _AMENDED_COMPUTE_METRICS,
            "compute_metrics_with_utc_bounds",
            _AMENDED_COMPUTE_METRICS_CODE_SHA256,
        ),
        (
            _AMENDED_ADAPTER_EVALUATOR,
            "evaluator_authority_sha256",
            _AMENDED_ADAPTER_EVALUATOR_CODE_SHA256,
        ),
        (_AMENDED_EXPLICIT_UTC, "_explicit_utc", _AMENDED_EXPLICIT_UTC_CODE_SHA256),
        (_AMENDED_DATE_ONLY, "_date_only", _AMENDED_DATE_ONLY_CODE_SHA256),
        (_AMENDED_SHA256_FILE, "_sha256_file", _AMENDED_SHA256_FILE_CODE_SHA256),
    ):
        _verify_callable(
            value,
            module=top40_amendment_0001.__name__,
            name=name,
            path=adapter_path,
            code_sha256=digest,
            globals_dict=adapter_globals,
        )
    _verify_callable(
        _INTEGRATION_EVALUATOR,
        module=__name__,
        name="evaluator_authority_sha256",
        path=integration_path,
        code_sha256=_INTEGRATION_EVALUATOR_CODE_SHA256,
        globals_dict=integration_globals,
    )
    _verify_callable(
        _AMENDED_PHASE0_AUTHORITY,
        module=__name__,
        name="_amended_phase0_authority",
        path=integration_path,
        code_sha256=_AMENDED_PHASE0_AUTHORITY_CODE_SHA256,
        globals_dict=integration_globals,
    )
    _verify_callable(
        _VERIFY_INTEGRATION,
        module=__name__,
        name="verify_integration",
        path=integration_path,
        code_sha256=_VERIFY_INTEGRATION_CODE_SHA256,
        globals_dict=integration_globals,
        defaults=(".",),
    )
    _verify_callable(
        _HISTORICAL_PHASE0_AUTHORITY,
        module=__name__,
        name="_historical_phase0_authority",
        path=integration_path,
        code_sha256=_HISTORICAL_PHASE0_AUTHORITY_CODE_SHA256,
        globals_dict=integration_globals,
    )
    _verify_callable(
        _SHA256_FUNCTION,
        module=__name__,
        name="_sha256",
        path=integration_path,
        code_sha256=_SHA256_FUNCTION_CODE_SHA256,
        globals_dict=integration_globals,
    )
    _verify_callable(
        _CANONICAL_BYTES_FUNCTION,
        module=__name__,
        name="_canonical_bytes",
        path=integration_path,
        code_sha256=_CANONICAL_BYTES_FUNCTION_CODE_SHA256,
        globals_dict=integration_globals,
    )
    _verify_callable(
        _READ_REGULAR_BYTES,
        module=orchestrator_v3.__name__,
        name="_read_regular_bytes",
        path=Path(orchestrator_v3.__file__),
        code_sha256=_READ_REGULAR_BYTES_CODE_SHA256,
        globals_dict=vars(orchestrator_v3),
    )
    if any(
        integration_globals.get(name) is not value
        for name, value in _VERIFY_INTEGRATION_LOCAL_BINDINGS
    ):
        raise Amendment0001IntegrationError(
            "integration verification helper binding changed"
        )
    if any(
        getattr(orchestrator_v3, name, None) is not value
        for name, value in _VERIFY_INTEGRATION_ORCHESTRATOR_BINDINGS
    ):
        raise Amendment0001IntegrationError(
            "parent organizer verification helper binding changed"
        )
    if (
        top40_amendment_0001.compute_metrics_with_utc_bounds
        is not _AMENDED_COMPUTE_METRICS
        or top40_amendment_0001.evaluator_authority_sha256
        is not _AMENDED_ADAPTER_EVALUATOR
        or top40_amendment_0001._explicit_utc is not _AMENDED_EXPLICIT_UTC
        or top40_amendment_0001._date_only is not _AMENDED_DATE_ONLY
        or top40_amendment_0001._sha256_file is not _AMENDED_SHA256_FILE
        or top40_amendment_0001._PARENT_COMPUTE_METRICS
        is not _FROZEN_COMPUTE_METRICS
        or top40_amendment_0001._PARENT_EVALUATOR_AUTHORITY_SHA256
        is not _FROZEN_EVALUATOR_AUTHORITY
        or top40_amendment_0001.runner_v3 is not runner_v3
        or top40_amendment_0001.dataclasses is not dataclasses
        or top40_amendment_0001.hashlib is not hashlib
        or top40_amendment_0001.json is not json
        or top40_amendment_0001.Path is not Path
        or top40_amendment_0001.AMENDMENT_ID != AMENDMENT_ID
        or _PARENT_EVALUATOR_AUTHORITY is not _AMENDED_ADAPTER_EVALUATOR
        or verify_integration is not _VERIFY_INTEGRATION
        or _historical_phase0_authority is not _HISTORICAL_PHASE0_AUTHORITY
        or _sha256 is not _SHA256_FUNCTION
        or _canonical_bytes is not _CANONICAL_BYTES_FUNCTION
        or evaluator_authority_sha256 is not _INTEGRATION_EVALUATOR
        or _amended_phase0_authority is not _AMENDED_PHASE0_AUTHORITY
    ):
        raise Amendment0001IntegrationError(
            "amended runtime callable globals or module bindings changed"
        )


@contextlib.contextmanager
def _activated_runtime(root: str | Path) -> Iterator[IntegrationAuthority]:
    """Install the exact delta only for one delegated command, then restore on every exit."""

    root_path = orchestrator_v3._trusted_root(root)
    with _RUNTIME_LOCK:
        authority = _VERIFY_INTEGRATION(root_path)
        _verify_frozen_runtime_bindings()
        _verify_amended_runtime_bindings()
        _RUNTIME_LOCAL.capability = _RUNTIME_CAPABILITY
        orchestrator_v3._phase0_authority = _AMENDED_PHASE0_AUTHORITY
        runner_v3._compute_metrics = _AMENDED_COMPUTE_METRICS
        runner_v3._evaluator_authority_sha256 = _INTEGRATION_EVALUATOR
        try:
            if (
                orchestrator_v3._phase0_authority is not _AMENDED_PHASE0_AUTHORITY
                or runner_v3._compute_metrics is not _AMENDED_COMPUTE_METRICS
                or runner_v3._evaluator_authority_sha256 is not _INTEGRATION_EVALUATOR
            ):
                raise Amendment0001IntegrationError(
                    "Amendment 0001 runtime substitution did not install exactly"
                )
            yield authority
        finally:
            post_error: BaseException | None = None
            try:
                if (
                    getattr(_RUNTIME_LOCAL, "capability", None)
                    is not _RUNTIME_CAPABILITY
                    or orchestrator_v3._phase0_authority
                    is not _AMENDED_PHASE0_AUTHORITY
                    or runner_v3._compute_metrics is not _AMENDED_COMPUTE_METRICS
                    or runner_v3._evaluator_authority_sha256
                    is not _INTEGRATION_EVALUATOR
                    or phase0_v3._discover_repository_scope is not _FROZEN_DISCOVERY
                ):
                    raise Amendment0001IntegrationError(
                        "Amendment 0001 runtime bindings changed during delegated command"
                    )
                _verify_amended_runtime_bindings()
                if _VERIFY_INTEGRATION(root_path) != authority:
                    raise Amendment0001IntegrationError(
                        "Amendment 0001 authority changed during delegated command"
                    )
            except BaseException as exc:
                post_error = exc
            orchestrator_v3._phase0_authority = _FROZEN_PHASE0_AUTHORITY
            runner_v3._compute_metrics = _FROZEN_COMPUTE_METRICS
            runner_v3._evaluator_authority_sha256 = _FROZEN_EVALUATOR_AUTHORITY
            phase0_v3._discover_repository_scope = _FROZEN_DISCOVERY
            with contextlib.suppress(AttributeError):
                del _RUNTIME_LOCAL.capability
            try:
                _verify_frozen_runtime_bindings()
                _verify_amended_runtime_bindings()
                _HISTORICAL_PHASE0_AUTHORITY(root_path)
            except BaseException as exc:
                if post_error is None:
                    post_error = exc
            if post_error is not None:
                raise post_error


def _annotate(result: Mapping[str, object], authority: IntegrationAuthority) -> dict[str, object]:
    return {
        **dict(result),
        "amendment_id": AMENDMENT_ID,
        "integration_freeze_commit": authority.freeze_commit,
        "integration_freeze_sha256": authority.freeze_file_sha256,
    }


def validate(root: str | Path = ".") -> dict[str, object]:
    with _activated_runtime(root) as authority:
        result = orchestrator_v3.validate(root)
    return _annotate(result, authority)


def status(root: str | Path = ".") -> dict[str, object]:
    with _activated_runtime(root) as authority:
        result = orchestrator_v3.status(root)
    return _annotate(result, authority)


def train(
    root: str | Path,
    team_id: str,
    entrypoint: str,
    *,
    purpose: str = "organizer train laboratory evaluation",
) -> dict[str, object]:
    with _activated_runtime(root) as authority:
        result = orchestrator_v3.train(
            root,
            team_id,
            entrypoint,
            purpose=purpose,
        )
    return _annotate(result, authority)


__all__ = [
    "ACTIVATION_JOURNAL_HEAD_SHA256",
    "ACTIVATION_JOURNAL_SEQUENCE",
    "AMENDMENT_ID",
    "AMENDMENT_TEST_COMMAND",
    "Amendment0001IntegrationError",
    "INTEGRATION_FREEZE_PATH",
    "IMPLEMENTATION_PATHS",
    "IntegrationAuthority",
    "ProvisionalIntegrationFreeze",
    "evaluator_authority_sha256",
    "freeze_integration",
    "status",
    "train",
    "validate",
    "verify_integration",
]
