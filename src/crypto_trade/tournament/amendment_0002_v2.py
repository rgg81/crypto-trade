"""Immutable corrective authority for schema-3 score-diagnostic execution.

Amendment 0002 changes no scientific input and no Top-40 V2 state schema.  It authorizes one
retry of the Team01 core diagnostic that failed before replay, then supplies the same narrow
schema-3 compatibility boundary to Amendment 0001's still-unspent reference reservation.
"""

from __future__ import annotations

import copy
import math
import re
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from crypto_trade.tournament import amendment_v2, score_diagnostics_v2
from crypto_trade.tournament.amendment_integrity_v2 import (
    TransactionChange,
    UtcClock,
    bounded_event_time,
    git_bytes,
    git_commit_time,
    git_text,
    parse_utc,
    pretty_json_bytes,
    private_artifact_directory,
    publish_transaction,
    read_repo_file,
    require_no_git_history,
    sha256_bytes,
    strict_json_object,
    system_utc_now,
    trusted_now,
    unique_first_add_commit,
)
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.score_diagnostic_compat_v2 import (
    run_score_diagnostic_with_schema3_compatibility,
)
from crypto_trade.tournament.top40_v2 import LoadedV2Config

AMENDMENT_ID = "top40-v2-amendment-0002-schema3-score-diagnostic-compatibility"
AMENDMENT_ROOT = "tournament/top40-v2/amendments/0002"
SPEC_PATH = f"{AMENDMENT_ROOT}/AMENDMENT.md"
REVIEW_PATH = f"{AMENDMENT_ROOT}/REVIEW.json"
INTEGRATION_PATH = f"{AMENDMENT_ROOT}/integration-freeze.json"
FREEZE_PATH = f"{AMENDMENT_ROOT}/freeze.json"
RESULT_PATH = f"{AMENDMENT_ROOT}/core-retry-result.json"

CORE_DIAGNOSTIC_ID = "score-ic-team-01-rdf-core-h21-k3-g10"
CORE_RETRY_DIAGNOSTIC_ID = "score-ic-team-01-rdf-core-h21-k3-g10-retry-0002"
REFERENCE_DIAGNOSTIC_ID = "score-ic-team-01-rdf-ref-001"
CORE_RESERVATION_SHA256 = "308d640cb382d9453913dcdb586267850eb611e205b6e5055dde2a6d02f3842c"
CORE_FAILURE_RESULT_SHA256 = "e5bc180a85acf3429d727a16c77789344dcd99f8ce5dd6153f02cf9a8c1d66f6"
CORE_FAILURE_REASON = "ValueError: run state has an invalid schema"

IMPLEMENTATION_FILE_PATHS = (
    "scripts/top40_v2_amendment_0002.py",
    "src/crypto_trade/tournament/amendment_0002_v2.py",
    "src/crypto_trade/tournament/score_diagnostic_compat_v2.py",
    "tests/tournament/test_top40_v2_amendment_0002.py",
    "tests/tournament/test_top40_v2_score_diagnostic_compat.py",
    SPEC_PATH,
)

_SHA256 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_RUNNER_PATCH_LOCK = threading.RLock()
_CANONICAL_RESERVED_RUNNER = score_diagnostics_v2.run_reserved_score_diagnostic
_DECISION_SCOPE = "one-core-infrastructure-retry-and-schema3-compatible-reference-run"
_DECISION_FIELDS = {
    "reviewed_exact_implementation_bytes",
    "confirmed_core_failure_preceded_replay_and_disclosed_no_scores",
    "approved_one_nonmaterial_core_retry",
    "approved_schema3_compatible_reference_execution",
}
_OUTCOME_FIELDS = set(amendment_v2.DIAGNOSTIC_OUTCOME_FIELDS)


def _exact_object(raw: object, keys: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping) or set(raw) != keys:
        raise ValueError(f"{label} has invalid keys")
    return raw


def _sha(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def _commit(value: object, label: str) -> str:
    if not isinstance(value, str) or _COMMIT.fullmatch(value) is None:
        raise ValueError(f"{label} must be a full Git commit")
    return value


def _nonempty(value: object, label: str, *, maximum: int = 20_000) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > maximum
    ):
        raise ValueError(f"{label} must be trimmed nonempty text")
    return value


def _finite_nonnegative(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{label} must be finite and nonnegative")
    return result


def _read_json(root: Path, relative: str, label: str) -> tuple[Mapping[str, Any], bytes]:
    _relative, _path, payload, _stat = read_repo_file(
        root,
        relative,
        label,
        maximum_bytes=8 * 1024 * 1024,
        require_single_link=True,
    )
    raw = strict_json_object(payload, label)
    if pretty_json_bytes(raw) != payload:
        raise ValueError(f"{label} must be canonical pretty JSON")
    return raw, payload


def _implementation_binding(root: Path) -> tuple[str, str, dict[str, str]]:
    commits: set[str] = set()
    hashes: dict[str, str] = {}
    for relative in IMPLEMENTATION_FILE_PATHS:
        _path, _safe, payload, _stat = read_repo_file(
            root,
            relative,
            f"Amendment 0002 implementation file {relative}",
            maximum_bytes=8 * 1024 * 1024,
            require_single_link=True,
        )
        hashes[relative] = sha256_bytes(payload)
        commits.add(unique_first_add_commit(root, relative, payload))
    if len(commits) != 1:
        raise ValueError("Amendment 0002 implementation files require one immutable commit")
    implementation_commit = commits.pop()
    parent_fields = git_text(
        root,
        "rev-list",
        "--parents",
        "-n",
        "1",
        implementation_commit,
        label="Amendment 0002 implementation parent",
    ).split()
    if len(parent_fields) != 2 or parent_fields[0] != implementation_commit:
        raise ValueError("Amendment 0002 implementation commit requires one parent")
    return implementation_commit, parent_fields[1], hashes


def _validate_core_failure(
    audit: amendment_v2.OrganizerAuditState,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    reservation = audit.reservations.get(CORE_DIAGNOSTIC_ID)
    result = audit.results.get(CORE_DIAGNOSTIC_ID)
    if reservation is None or result is None:
        raise ValueError("Amendment 0002 requires the exact recorded core infrastructure failure")
    if reservation.get("record_sha256") != CORE_RESERVATION_SHA256:
        raise ValueError("core diagnostic reservation SHA-256 differs")
    payload = result.get("payload")
    if (
        result.get("record_sha256") != CORE_FAILURE_RESULT_SHA256
        or not isinstance(payload, Mapping)
        or payload.get("diagnostic_id") != CORE_DIAGNOSTIC_ID
        or payload.get("reservation_sha256") != CORE_RESERVATION_SHA256
        or payload.get("status") != "failed"
        or payload.get("failure_reason") != CORE_FAILURE_REASON
        or payload.get("artifact_hashes") != {}
        or payload.get("diagnostic_outcomes") is not None
        or payload.get("non_material") is not True
        or payload.get("team_material_trial_delta") != 0
        or payload.get("team_cpu_hours_delta") != 0.0
        or payload.get("team_wall_clock_hours_delta") != 0.0
    ):
        raise ValueError("core diagnostic failure is not the exact pre-replay failure")
    return reservation, result


def _current_core_failure(
    root: Path,
) -> tuple[Mapping[str, Any], Mapping[str, Any], bytes]:
    _relative, _path, audit_bytes, _stat = read_repo_file(
        root,
        amendment_v2.ORGANIZER_AUDIT_PATH,
        "Amendment 0001 organizer audit",
        maximum_bytes=32 * 1024 * 1024,
        require_single_link=True,
    )
    audit = amendment_v2.validate_organizer_audit_bytes(audit_bytes)
    reservation, result = _validate_core_failure(audit)
    return reservation, result, audit_bytes


def _retry_reservation(original: Mapping[str, Any]) -> Mapping[str, Any]:
    original_payload = original.get("payload")
    if not isinstance(original_payload, Mapping):
        raise ValueError("core reservation payload is invalid")
    payload = copy.deepcopy(dict(original_payload))
    payload.pop("reservation_key_sha256", None)
    payload["diagnostic_id"] = CORE_RETRY_DIAGNOSTIC_ID
    payload["correction_amendment_id"] = AMENDMENT_ID
    payload["corrects_reservation_sha256"] = CORE_RESERVATION_SHA256
    payload["corrects_failure_result_sha256"] = CORE_FAILURE_RESULT_SHA256
    core = {
        "schema_version": 1,
        "amendment_id": AMENDMENT_ID,
        "event_type": "infrastructure_corrective_retry_reserved",
        "diagnostic_id": CORE_RETRY_DIAGNOSTIC_ID,
        "corrects_diagnostic_id": CORE_DIAGNOSTIC_ID,
        "corrects_reservation_sha256": CORE_RESERVATION_SHA256,
        "corrects_failure_result_sha256": CORE_FAILURE_RESULT_SHA256,
        "payload": payload,
    }
    return {**core, "record_sha256": sha256_bytes(amendment_v2._canonical_json_bytes(core))}


def _integration_manifest(
    root: Path,
    config: LoadedV2Config,
) -> tuple[dict[str, Any], str, str, Mapping[str, Any], Mapping[str, Any]]:
    status = amendment_v2.amendment_status(root, config)
    if (
        status.get("amendment_activated") is not True
        or status.get("amendment_status") != "frozen"
    ):
        raise ValueError("Amendment 0002 requires frozen Amendment 0001 authority")
    implementation_commit, implementation_parent, implementation_files = (
        _implementation_binding(root)
    )
    original, failure, _audit_bytes = _current_core_failure(root)
    freeze, freeze_bytes = _read_json(
        root, amendment_v2.AMENDMENT_FREEZE_PATH, "Amendment 0001 freeze"
    )
    _integration, integration_bytes = _read_json(
        root, amendment_v2.INTEGRATION_MANIFEST_PATH, "Amendment 0001 integration manifest"
    )
    if (
        freeze.get("integration_manifest_sha256") != sha256_bytes(integration_bytes)
        or freeze.get("integration_manifest_path") != amendment_v2.INTEGRATION_MANIFEST_PATH
    ):
        raise ValueError("Amendment 0001 freeze/integration binding differs")
    parent_audit = git_bytes(
        root,
        "show",
        f"{implementation_parent}:{amendment_v2.ORGANIZER_AUDIT_PATH}",
        label="Amendment 0002 parent organizer audit",
    )
    parent_state = git_bytes(
        root,
        "show",
        f"{implementation_parent}:{TOP40_V2_LAYOUT.state_path}",
        label="Amendment 0002 parent run state",
    )
    parent_audit_state = amendment_v2.validate_organizer_audit_bytes(parent_audit)
    _validate_core_failure(parent_audit_state)
    parent_state_raw = strict_json_object(parent_state, "Amendment 0002 parent run state")
    if pretty_json_bytes(parent_state_raw) != parent_state:
        raise ValueError("Amendment 0002 parent run state is not canonical pretty JSON")
    amendment_v2.validate_amended_run_state(parent_state_raw, config)
    parent_amendment = parent_state_raw["amendment"]
    if (
        parent_state_raw["organizer_audit"] != parent_audit_state.binding
        or parent_state_raw["administrative_hold"]["active"] is not True
        or parent_amendment["status"] != "frozen"
        or parent_amendment["freeze_path"] != amendment_v2.AMENDMENT_FREEZE_PATH
        or parent_amendment["freeze_sha256"] != sha256_bytes(freeze_bytes)
        or parent_amendment["integration_manifest_path"]
        != amendment_v2.INTEGRATION_MANIFEST_PATH
        or parent_amendment["integration_manifest_sha256"] != sha256_bytes(integration_bytes)
    ):
        raise ValueError(
            "Amendment 0002 parent state is not bound to the exact active failure authority"
        )
    manifest = {
        "schema_version": 1,
        "amendment_id": AMENDMENT_ID,
        "status": "ready_for_review",
        "decision_scope": _DECISION_SCOPE,
        "implementation_commit": implementation_commit,
        "implementation_parent_commit": implementation_parent,
        "implementation_files": implementation_files,
        "baseline_organizer_audit_sha256": sha256_bytes(parent_audit),
        "baseline_run_state_sha256": sha256_bytes(parent_state),
        "amendment_0001_freeze_path": amendment_v2.AMENDMENT_FREEZE_PATH,
        "amendment_0001_freeze_sha256": sha256_bytes(freeze_bytes),
        "amendment_0001_integration_path": amendment_v2.INTEGRATION_MANIFEST_PATH,
        "amendment_0001_integration_sha256": sha256_bytes(integration_bytes),
        "core_reservation_sha256": CORE_RESERVATION_SHA256,
        "core_failure_result_sha256": CORE_FAILURE_RESULT_SHA256,
        "core_failure_reason": CORE_FAILURE_REASON,
        "core_failure_timestamp_utc": failure["timestamp_utc"],
        "compatibility_api": "run_score_diagnostic_with_schema3_compatibility",
        "retry_reservation": _retry_reservation(original),
        "reference_diagnostic_id": REFERENCE_DIAGNOSTIC_ID,
        "non_material": True,
    }
    return (
        manifest,
        sha256_bytes(pretty_json_bytes(manifest)),
        implementation_commit,
        original,
        failure,
    )


def correction_review_material(root: str | Path, config: LoadedV2Config) -> Mapping[str, Any]:
    root_path = Path(root).resolve()
    manifest, digest, _commit_value, _reservation, _failure = _integration_manifest(
        root_path, config
    )
    return {
        "decision_scope": _DECISION_SCOPE,
        "decision_fields": sorted(_DECISION_FIELDS),
        "integration_manifest_path": INTEGRATION_PATH,
        "integration_manifest_sha256": digest,
        "integration_manifest": manifest,
        "review_path": REVIEW_PATH,
    }


def _require_active_hold(
    root: Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock,
) -> None:
    status = amendment_v2.amendment_status(root, config, clock=clock)
    if status.get("administrative_hold_active") is not True:
        raise ValueError("Amendment 0002 execution requires the active Amendment 0001 hold")


def _require_active_state_locked(
    root: Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock,
) -> None:
    state, _state_bytes, _chain, _audit = amendment_v2._read_amended_state_locked(
        root, config, clock=clock
    )
    if (
        state["amendment"]["status"] != "frozen"
        or state["administrative_hold"]["active"] is not True
    ):
        raise ValueError("Amendment 0002 requires the active frozen Amendment 0001 state")


def _validate_review(raw: object) -> Mapping[str, Any]:
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
            "implementation_commit",
            "implementation_files",
            "integration_manifest_path",
            "integration_manifest_sha256",
            "amendment_0001_freeze_sha256",
            "amendment_0001_integration_sha256",
            "core_reservation_sha256",
            "core_failure_result_sha256",
            "notes",
        },
        "Amendment 0002 review",
    )
    if (
        review["schema_version"] != 1
        or review["amendment_id"] != AMENDMENT_ID
        or review["decision"] != "approve"
        or review["decision_scope"] != _DECISION_SCOPE
        or review["integration_manifest_path"] != INTEGRATION_PATH
        or review["core_reservation_sha256"] != CORE_RESERVATION_SHA256
        or review["core_failure_result_sha256"] != CORE_FAILURE_RESULT_SHA256
    ):
        raise ValueError("Amendment 0002 review identity is invalid")
    decision = _exact_object(review["decision_data"], _DECISION_FIELDS, "review decision_data")
    if any(value is not True for value in decision.values()):
        raise ValueError("Amendment 0002 review must approve every boundary")
    _nonempty(review["authorized_by"], "review authorized_by", maximum=1000)
    _nonempty(review["notes"], "review notes")
    parse_utc(review["reviewed_at_utc"], "reviewed_at_utc")
    _commit(review["implementation_commit"], "review implementation_commit")
    _sha(review["integration_manifest_sha256"], "review integration manifest SHA-256")
    _sha(review["amendment_0001_freeze_sha256"], "review Amendment 0001 freeze SHA-256")
    _sha(
        review["amendment_0001_integration_sha256"],
        "review Amendment 0001 integration SHA-256",
    )
    files = review["implementation_files"]
    if not isinstance(files, Mapping) or set(files) != set(IMPLEMENTATION_FILE_PATHS):
        raise ValueError("review implementation file manifest is incomplete")
    for relative, digest in files.items():
        if relative not in IMPLEMENTATION_FILE_PATHS:
            raise ValueError("review implementation path is unexpected")
        _sha(digest, f"review implementation hash {relative}")
    return review


def _load_review(
    root: Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock,
) -> tuple[Mapping[str, Any], bytes, str, Mapping[str, Any], str]:
    material = correction_review_material(root, config)
    manifest = material["integration_manifest"]
    review, review_bytes = _read_json(root, REVIEW_PATH, "Amendment 0002 review")
    _validate_review(review)
    expected = {
        "decision_scope": material["decision_scope"],
        "implementation_commit": manifest["implementation_commit"],
        "implementation_files": manifest["implementation_files"],
        "integration_manifest_path": material["integration_manifest_path"],
        "integration_manifest_sha256": material["integration_manifest_sha256"],
        "amendment_0001_freeze_sha256": manifest["amendment_0001_freeze_sha256"],
        "amendment_0001_integration_sha256": manifest[
            "amendment_0001_integration_sha256"
        ],
        "core_reservation_sha256": CORE_RESERVATION_SHA256,
        "core_failure_result_sha256": CORE_FAILURE_RESULT_SHA256,
    }
    if any(review[field] != value for field, value in expected.items()):
        raise ValueError("Amendment 0002 review differs from exact integration authority")
    review_commit = unique_first_add_commit(
        root,
        REVIEW_PATH,
        review_bytes,
        require_direct_parent=str(manifest["implementation_commit"]),
    )
    reviewed_at = parse_utc(review["reviewed_at_utc"], "review time")
    failure_time = parse_utc(manifest["core_failure_timestamp_utc"], "core failure time")
    implementation_time = git_commit_time(
        root,
        str(manifest["implementation_commit"]),
        "Amendment 0002 implementation commit time",
    )
    if (
        implementation_time < failure_time
        or implementation_time > trusted_now(clock)
        or reviewed_at < implementation_time
        or reviewed_at > trusted_now(clock)
    ):
        raise ValueError("Amendment 0002 review time is outside its authority interval")
    commit_time = git_commit_time(root, review_commit, "Amendment 0002 review commit time")
    if commit_time < reviewed_at or commit_time > trusted_now(clock):
        raise ValueError("Amendment 0002 review commit time is invalid")
    return (
        review,
        review_bytes,
        review_commit,
        manifest,
        str(material["integration_manifest_sha256"]),
    )


def freeze_correction(
    root: str | Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock = system_utc_now,
) -> Mapping[str, Any]:
    root_path = Path(root).resolve()
    _require_active_hold(root_path, config, clock=clock)
    review, review_bytes, review_commit, manifest, manifest_sha = _load_review(
        root_path, config, clock=clock
    )
    with amendment_v2._state_lock(root_path):
        _require_active_state_locked(root_path, config, clock=clock)
        for relative in (INTEGRATION_PATH, FREEZE_PATH):
            require_no_git_history(root_path, relative)
            if (root_path / relative).exists() or (root_path / relative).is_symlink():
                raise ValueError(f"Amendment 0002 freeze output already exists: {relative}")
        frozen_text = bounded_event_time(
            trusted_now(clock).isoformat().replace("+00:00", "Z"),
            "Amendment 0002 freeze time",
            lower_bounds=(
                ("review time", review["reviewed_at_utc"]),
                ("core failure time", manifest["core_failure_timestamp_utc"]),
            ),
            clock=clock,
        )
        freeze = {
            "schema_version": 1,
            "amendment_id": AMENDMENT_ID,
            "status": "frozen",
            "frozen_at_utc": frozen_text,
            "implementation_commit": manifest["implementation_commit"],
            "implementation_files": manifest["implementation_files"],
            "integration_manifest_path": INTEGRATION_PATH,
            "integration_manifest_sha256": manifest_sha,
            "amendment_0001_freeze_sha256": manifest["amendment_0001_freeze_sha256"],
            "amendment_0001_integration_sha256": manifest[
                "amendment_0001_integration_sha256"
            ],
            "core_reservation_sha256": CORE_RESERVATION_SHA256,
            "core_failure_result_sha256": CORE_FAILURE_RESULT_SHA256,
            "retry_reservation": manifest["retry_reservation"],
            "reference_diagnostic_id": REFERENCE_DIAGNOSTIC_ID,
            "review_path": REVIEW_PATH,
            "review_sha256": sha256_bytes(review_bytes),
            "review_commit": review_commit,
        }
        _validate_freeze(freeze)
        publish_transaction(
            root_path,
            (
                TransactionChange(
                    root_path / INTEGRATION_PATH, None, pretty_json_bytes(manifest)
                ),
                TransactionChange(root_path / FREEZE_PATH, None, pretty_json_bytes(freeze)),
            ),
        )
    return freeze


def _validate_freeze(raw: object) -> Mapping[str, Any]:
    freeze = _exact_object(
        raw,
        {
            "schema_version",
            "amendment_id",
            "status",
            "frozen_at_utc",
            "implementation_commit",
            "implementation_files",
            "integration_manifest_path",
            "integration_manifest_sha256",
            "amendment_0001_freeze_sha256",
            "amendment_0001_integration_sha256",
            "core_reservation_sha256",
            "core_failure_result_sha256",
            "retry_reservation",
            "reference_diagnostic_id",
            "review_path",
            "review_sha256",
            "review_commit",
        },
        "Amendment 0002 freeze",
    )
    if (
        freeze["schema_version"] != 1
        or freeze["amendment_id"] != AMENDMENT_ID
        or freeze["status"] != "frozen"
        or freeze["integration_manifest_path"] != INTEGRATION_PATH
        or freeze["review_path"] != REVIEW_PATH
        or freeze["core_reservation_sha256"] != CORE_RESERVATION_SHA256
        or freeze["core_failure_result_sha256"] != CORE_FAILURE_RESULT_SHA256
        or freeze["reference_diagnostic_id"] != REFERENCE_DIAGNOSTIC_ID
    ):
        raise ValueError("Amendment 0002 freeze identity is invalid")
    parse_utc(freeze["frozen_at_utc"], "Amendment 0002 freeze time")
    _commit(freeze["implementation_commit"], "freeze implementation commit")
    _commit(freeze["review_commit"], "freeze review commit")
    for field in (
        "integration_manifest_sha256",
        "amendment_0001_freeze_sha256",
        "amendment_0001_integration_sha256",
        "review_sha256",
    ):
        _sha(freeze[field], f"freeze {field}")
    if not isinstance(freeze["implementation_files"], Mapping):
        raise ValueError("freeze implementation files are invalid")
    retry = freeze["retry_reservation"]
    if not isinstance(retry, Mapping) or retry.get("diagnostic_id") != CORE_RETRY_DIAGNOSTIC_ID:
        raise ValueError("freeze retry reservation is invalid")
    core = {key: value for key, value in retry.items() if key != "record_sha256"}
    if retry.get("record_sha256") != sha256_bytes(amendment_v2._canonical_json_bytes(core)):
        raise ValueError("freeze retry reservation record SHA-256 is invalid")
    return freeze


def _load_frozen_authority(
    root: Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock,
) -> tuple[Mapping[str, Any], bytes, str, Mapping[str, Any]]:
    review, review_bytes, review_commit, expected_manifest, manifest_sha = _load_review(
        root, config, clock=clock
    )
    manifest, manifest_bytes = _read_json(
        root, INTEGRATION_PATH, "Amendment 0002 integration manifest"
    )
    if manifest != expected_manifest or sha256_bytes(manifest_bytes) != manifest_sha:
        raise ValueError("Amendment 0002 integration manifest differs from reviewed bytes")
    freeze, freeze_bytes = _read_json(root, FREEZE_PATH, "Amendment 0002 freeze")
    _validate_freeze(freeze)
    expected_freeze = {
        "implementation_commit": expected_manifest["implementation_commit"],
        "implementation_files": expected_manifest["implementation_files"],
        "integration_manifest_sha256": manifest_sha,
        "amendment_0001_freeze_sha256": expected_manifest["amendment_0001_freeze_sha256"],
        "amendment_0001_integration_sha256": expected_manifest[
            "amendment_0001_integration_sha256"
        ],
        "retry_reservation": expected_manifest["retry_reservation"],
        "review_sha256": sha256_bytes(review_bytes),
        "review_commit": review_commit,
    }
    if any(freeze[field] != value for field, value in expected_freeze.items()):
        raise ValueError("Amendment 0002 freeze differs from exact reviewed authority")
    integration_commit = unique_first_add_commit(
        root, INTEGRATION_PATH, manifest_bytes, require_direct_parent=review_commit
    )
    freeze_commit = unique_first_add_commit(
        root, FREEZE_PATH, freeze_bytes, require_direct_parent=review_commit
    )
    if integration_commit != freeze_commit:
        raise ValueError("Amendment 0002 integration and freeze require one commit")
    frozen_at = parse_utc(freeze["frozen_at_utc"], "Amendment 0002 freeze time")
    if frozen_at < parse_utc(review["reviewed_at_utc"], "review time"):
        raise ValueError("Amendment 0002 freeze precedes its review")
    freeze_commit_time = git_commit_time(root, freeze_commit, "Amendment 0002 freeze commit time")
    if freeze_commit_time < frozen_at or freeze_commit_time > trusted_now(clock):
        raise ValueError("Amendment 0002 freeze commit time is invalid")
    return freeze, freeze_bytes, freeze_commit, expected_manifest


def _validate_result(
    raw: object,
    freeze: Mapping[str, Any],
    freeze_bytes: bytes,
) -> Mapping[str, Any]:
    result = _exact_object(
        raw,
        {
            "schema_version",
            "amendment_id",
            "diagnostic_id",
            "status",
            "failure_reason",
            "recorded_at_utc",
            "retry_reservation_sha256",
            "amendment_0002_freeze_sha256",
            "corrects_failure_result_sha256",
            "artifact_hashes",
            "diagnostic_outcomes",
            "organizer_cpu_hours",
            "organizer_wall_clock_hours",
            "non_material",
            "team_material_trial_delta",
            "team_cpu_hours_delta",
            "team_wall_clock_hours_delta",
        },
        "Amendment 0002 core retry result",
    )
    retry = freeze["retry_reservation"]
    if (
        result["schema_version"] != 1
        or result["amendment_id"] != AMENDMENT_ID
        or result["diagnostic_id"] != CORE_RETRY_DIAGNOSTIC_ID
        or result["retry_reservation_sha256"] != retry["record_sha256"]
        or result["amendment_0002_freeze_sha256"] != sha256_bytes(freeze_bytes)
        or result["corrects_failure_result_sha256"] != CORE_FAILURE_RESULT_SHA256
        or result["non_material"] is not True
    ):
        raise ValueError("Amendment 0002 core retry result identity is invalid")
    if type(result["team_material_trial_delta"]) is not int or result[
        "team_material_trial_delta"
    ] != 0:
        raise ValueError("core retry material trial delta must be integer zero")
    for field in ("team_cpu_hours_delta", "team_wall_clock_hours_delta"):
        value = result[field]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) != 0.0
        ):
            raise ValueError(f"core retry {field} must be numeric zero")
    recorded_at = parse_utc(result["recorded_at_utc"], "core retry result time")
    if recorded_at < parse_utc(freeze["frozen_at_utc"], "Amendment 0002 freeze time"):
        raise ValueError("core retry result precedes the Amendment 0002 freeze")
    _finite_nonnegative(result["organizer_cpu_hours"], "retry organizer CPU hours")
    _finite_nonnegative(result["organizer_wall_clock_hours"], "retry organizer wall hours")
    if result["status"] == "completed":
        if result["failure_reason"] is not None:
            raise ValueError("completed retry cannot include a failure reason")
        hashes = result["artifact_hashes"]
        outcomes = result["diagnostic_outcomes"]
        if (
            not isinstance(hashes, Mapping)
            or set(hashes) != set(amendment_v2.REQUIRED_PRIVATE_ARTIFACT_NAMES)
            or any(
                not isinstance(value, str) or _SHA256.fullmatch(value) is None
                for value in hashes.values()
            )
            or not isinstance(outcomes, Mapping)
            or set(outcomes) != _OUTCOME_FIELDS
            or any(type(value) is not bool for value in outcomes.values())
        ):
            raise ValueError("completed retry evidence is invalid")
    elif result["status"] in {"failed", "interrupted"}:
        _nonempty(result["failure_reason"], "retry failure reason", maximum=8000)
        if result["artifact_hashes"] != {} or result["diagnostic_outcomes"] is not None:
            raise ValueError("failed retry cannot publish evidence")
    else:
        raise ValueError("retry result status is invalid")
    return result


def _run_core_retry_once(
    root: str | Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock = system_utc_now,
) -> Mapping[str, Any]:
    root_path = Path(root).resolve()
    _require_active_hold(root_path, config, clock=clock)
    freeze, freeze_bytes, _freeze_commit, manifest = _load_frozen_authority(
        root_path, config, clock=clock
    )
    result_path = root_path / RESULT_PATH
    with amendment_v2._state_lock(root_path):
        _require_active_state_locked(root_path, config, clock=clock)
        if result_path.exists() or result_path.is_symlink():
            result, _result_bytes = _read_json(root_path, RESULT_PATH, "core retry result")
            validated = _validate_result(result, freeze, freeze_bytes)
            if validated["status"] == "completed":
                expected_hashes, expected_outcomes = (
                    amendment_v2._completed_diagnostic_evidence(
                        root_path, freeze["retry_reservation"]
                    )
                )
                if (
                    validated["artifact_hashes"] != expected_hashes
                    or validated["diagnostic_outcomes"] != expected_outcomes
                ):
                    raise ValueError("existing core retry result differs from private evidence")
            return validated
        require_no_git_history(root_path, RESULT_PATH)
    if score_diagnostics_v2.run_reserved_score_diagnostic is not _CANONICAL_RESERVED_RUNNER:
        raise ValueError("core retry runner binding is not the frozen Amendment 0001 function")
    retry = copy.deepcopy(dict(manifest["retry_reservation"]))
    output_dir = private_artifact_directory(
        root_path, "team-01", CORE_RETRY_DIAGNOSTIC_ID, create=True
    )
    runner_result = run_score_diagnostic_with_schema3_compatibility(
        root=root_path,
        runner_call=lambda: score_diagnostics_v2.run_reserved_score_diagnostic(
            root=root_path,
            reservation=retry,
            private_output_dir=output_dir,
        ),
    )
    if runner_result["status"] == "completed":
        artifact_hashes, outcomes = amendment_v2._completed_diagnostic_evidence(
            root_path, retry
        )
    else:
        artifact_hashes, outcomes = {}, None
    _require_active_hold(root_path, config, clock=clock)
    post_freeze, post_freeze_bytes, _post_commit, post_manifest = _load_frozen_authority(
        root_path, config, clock=clock
    )
    if (
        post_freeze != freeze
        or post_freeze_bytes != freeze_bytes
        or post_manifest != manifest
    ):
        raise ValueError("Amendment 0002 authority changed during the corrective replay")
    recorded = bounded_event_time(
        trusted_now(clock).isoformat().replace("+00:00", "Z"),
        "core retry result time",
        lower_bounds=(
            ("Amendment 0002 freeze time", freeze["frozen_at_utc"]),
            ("core failure time", manifest["core_failure_timestamp_utc"]),
        ),
        clock=clock,
    )
    result = {
        "schema_version": 1,
        "amendment_id": AMENDMENT_ID,
        "diagnostic_id": CORE_RETRY_DIAGNOSTIC_ID,
        "status": runner_result["status"],
        "failure_reason": runner_result["failure_reason"],
        "recorded_at_utc": recorded,
        "retry_reservation_sha256": retry["record_sha256"],
        "amendment_0002_freeze_sha256": sha256_bytes(freeze_bytes),
        "corrects_failure_result_sha256": CORE_FAILURE_RESULT_SHA256,
        "artifact_hashes": artifact_hashes,
        "diagnostic_outcomes": outcomes,
        "organizer_cpu_hours": runner_result["organizer_cpu_hours"],
        "organizer_wall_clock_hours": runner_result["organizer_wall_clock_hours"],
        "non_material": True,
        "team_material_trial_delta": 0,
        "team_cpu_hours_delta": 0.0,
        "team_wall_clock_hours_delta": 0.0,
    }
    _validate_result(result, freeze, freeze_bytes)
    with amendment_v2._state_lock(root_path):
        _require_active_state_locked(root_path, config, clock=clock)
        if result_path.exists() or result_path.is_symlink():
            raise ValueError("core retry result appeared during the corrective replay")
        require_no_git_history(root_path, RESULT_PATH)
        publish_transaction(
            root_path,
            (TransactionChange(result_path, None, pretty_json_bytes(result)),),
        )
    return result


def run_core_retry(
    root: str | Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock = system_utc_now,
) -> Mapping[str, Any]:
    """Serialize and execute the sole immutable infrastructure-corrective retry."""

    root_path = Path(root).resolve()
    with amendment_v2._diagnostic_execution_lock(root_path, CORE_RETRY_DIAGNOSTIC_ID):
        return _run_core_retry_once(root_path, config, clock=clock)


def _load_committed_successful_retry(
    root: Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    freeze, freeze_bytes, freeze_commit, _manifest = _load_frozen_authority(
        root, config, clock=clock
    )
    result, result_bytes = _read_json(root, RESULT_PATH, "committed core retry result")
    _validate_result(result, freeze, freeze_bytes)
    if result["status"] != "completed":
        raise ValueError("reference diagnostic requires a successful core corrective retry")
    result_commit = unique_first_add_commit(
        root, RESULT_PATH, result_bytes, require_direct_parent=freeze_commit
    )
    result_commit_time = git_commit_time(root, result_commit, "core retry result commit time")
    if (
        result_commit_time < parse_utc(result["recorded_at_utc"], "core retry result time")
        or result_commit_time > trusted_now(clock)
    ):
        raise ValueError("core retry result commit time is invalid")
    expected_hashes, expected_outcomes = amendment_v2._completed_diagnostic_evidence(
        root, freeze["retry_reservation"]
    )
    if (
        result["artifact_hashes"] != expected_hashes
        or result["diagnostic_outcomes"] != expected_outcomes
    ):
        raise ValueError("committed core retry differs from organizer-private evidence")
    return freeze, result


def run_reference_diagnostic(
    root: str | Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock = system_utc_now,
) -> Mapping[str, Any]:
    root_path = Path(root).resolve()
    _require_active_hold(root_path, config, clock=clock)
    _load_committed_successful_retry(root_path, config, clock=clock)
    with _RUNNER_PATCH_LOCK:
        original = score_diagnostics_v2.run_reserved_score_diagnostic
        if original is not _CANONICAL_RESERVED_RUNNER:
            raise ValueError("reference runner binding is not the frozen Amendment 0001 function")
        call_count = 0

        def compatible_runner(**kwargs: Any) -> Mapping[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count != 1 or Path(kwargs.get("root", "")).resolve() != root_path:
                raise ValueError("reference compatibility runner invocation is invalid")
            return run_score_diagnostic_with_schema3_compatibility(
                root=root_path,
                runner_call=lambda: original(**kwargs),
            )

        try:
            score_diagnostics_v2.run_reserved_score_diagnostic = compatible_runner
            event = amendment_v2.run_diagnostic_backfill(
                root_path,
                config,
                diagnostic_id=REFERENCE_DIAGNOSTIC_ID,
                clock=clock,
            )
        finally:
            observed = score_diagnostics_v2.run_reserved_score_diagnostic
            score_diagnostics_v2.run_reserved_score_diagnostic = original
            if observed is not compatible_runner:
                raise ValueError("reference diagnostic runner binding changed during execution")
        if call_count != 1:
            raise ValueError(
                "reference diagnostic did not invoke the reviewed compatibility runner"
            )
        return event


def correction_status(
    root: str | Path,
    config: LoadedV2Config,
    *,
    clock: UtcClock = system_utc_now,
) -> Mapping[str, Any]:
    root_path = Path(root).resolve()
    freeze, freeze_bytes, freeze_commit, _manifest = _load_frozen_authority(
        root_path, config, clock=clock
    )
    result_status = "not_run"
    result_committed = False
    if (root_path / RESULT_PATH).exists() or (root_path / RESULT_PATH).is_symlink():
        result, result_bytes = _read_json(root_path, RESULT_PATH, "core retry result")
        _validate_result(result, freeze, freeze_bytes)
        result_status = str(result["status"])
        try:
            unique_first_add_commit(
                root_path, RESULT_PATH, result_bytes, require_direct_parent=freeze_commit
            )
            result_committed = True
        except ValueError:
            result_committed = False
        if result_committed and result_status == "completed":
            _load_committed_successful_retry(root_path, config, clock=clock)
    _original, _failure, audit_bytes = _current_core_failure(root_path)
    audit = amendment_v2.validate_organizer_audit_bytes(audit_bytes)
    amendment1 = amendment_v2.amendment_status(root_path, config, clock=clock)
    return {
        "amendment_id": AMENDMENT_ID,
        "status": "frozen",
        "core_retry_status": result_status,
        "core_retry_committed": result_committed,
        "reference_result_recorded": REFERENCE_DIAGNOSTIC_ID in audit.results,
        "administrative_hold_active": amendment1["administrative_hold_active"],
    }
