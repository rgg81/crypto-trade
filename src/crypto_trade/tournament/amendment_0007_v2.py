"""Pending A7 superset dispatcher for the frozen-worker A5 protocol preload."""

from __future__ import annotations

import contextlib
import re
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from crypto_trade.tournament import (
    amendment_0005_integration_v2,
    amendment_0005_v2,
    amendment_integrity_v2,
    runner_schema3_compat_v4,
    runner_v2,
    score_adapter_protocol_v5,
    score_diagnostic_compat_v2,
)

AMENDMENT_ID = "top40-v2-amendment-0007-frozen-worker-a5-protocol-preload"
AMENDMENT_ROOT = "tournament/top40-v2/amendments/0007"
SPEC_PATH = f"{AMENDMENT_ROOT}/AMENDMENT.md"
DRAFT_PATH = f"{AMENDMENT_ROOT}/draft.json"
REVIEW_PATH = f"{AMENDMENT_ROOT}/REVIEW.json"
FREEZE_PATH = f"{AMENDMENT_ROOT}/freeze.json"
INTEGRATION_DRAFT_PATH = f"{AMENDMENT_ROOT}/integration-draft.json"
INTEGRATION_REVIEW_PATH = f"{AMENDMENT_ROOT}/INTEGRATION-REVIEW.json"
INTEGRATION_FREEZE_PATH = f"{AMENDMENT_ROOT}/integration-freeze.json"
ENTRYPOINT_PATH = "scripts/top40_v2_tournament_runtime_preload_v7.py"
WORKER_WRAPPER_PATH = "src/crypto_trade/tournament/_strategy_worker_preload_v7.py"
IMPLEMENTATION_MODULE_PATH = "src/crypto_trade/tournament/amendment_0007_v2.py"

_FROZEN_WORKER_MODULE = "crypto_trade.tournament._strategy_worker_v2"
_PRELOAD_WORKER_MODULE = "crypto_trade.tournament._strategy_worker_preload_v7"
_ELIGIBLE_PRELOAD_TEAMS = tuple(f"team-{index:02d}" for index in range(4, 11))
_MISSING = object()
_SHA256 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_CANDIDATE_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_JOURNAL_PATH = "tournament/top40-v2/organizer_research_journal.jsonl"
_A5_ACTIVATION_RECORD_COUNT = 25
_A5_ACTIVATION_HEAD_SHA256 = "2ebf302de21ced25bb299803be5aad2fb717c378b556853835b0c2a8ec4f328a"
_DELEGATED_A5_INTEGRATION = {
    "commit": "d2b95f610722aab65b4e67466b34efeaa3554101",
    "path": "tournament/top40-v2/amendments/0005/integration-freeze.json",
    "sha256": "b3b2b96245a479ccfff95b5cd5b5cd0aef3b2d0aac0fc9faf5367d3e6772958c",
}
_HISTORICAL_ENTRYPOINT = {
    "path": "scripts/top40_v2_tournament_score_diagnostics_v5.py",
    "sha256": "0dc9228f3b9c6fe41b2655055f766fc92f323a289a050e6bdf4e48a30b0105f4",
    "status": "superseded-unchanged",
}
_DISPATCH_SCOPE = {
    "all_other_argv_delegated_to_amendment_0005_unchanged": True,
    "eligible_development_teams": list(_ELIGIBLE_PRELOAD_TEAMS),
    "ordinary_score_capture_enabled": False,
    "patch_binding": "crypto_trade.tournament.runner_v2._strategy_worker_command",
    "replacement_module": _PRELOAD_WORKER_MODULE,
    "source_module": _FROZEN_WORKER_MODULE,
}
_IMPLEMENTATION_REVIEW_SCOPE = {
    "a5_a6_a4_delegation_chain_unchanged": True,
    "candidate_or_scientific_bytes_changed": False,
    "exact_one_token_command_replacement": True,
    "parent_authorities_exactly_pinned": True,
    "patch_scope_team_04_through_team_10_development_only": True,
    "private_and_final_execution_enabled": False,
    "real_repository_mask_smoke_passed": True,
    "restoration_after_every_baseexception": True,
    "score_capture_or_disclosure_added": False,
    "worker_sandbox_policy_changed": False,
}
_INTEGRATION_REVIEW_SCOPE = {
    "activation_journal_is_prospective": True,
    "active_entrypoint_and_module_exactly_bound": True,
    "amendment_freeze_unchanged": True,
    "delegated_a5_integration_unchanged": True,
    "historical_entrypoint_unchanged": True,
    "strict_commit_ancestry_verified": True,
}

PARENT_AUTHORITIES: Mapping[str, tuple[str, int, str]] = {
    "scripts/top40_v2_tournament_score_diagnostics_v5.py": (
        "0dc9228f3b9c6fe41b2655055f766fc92f323a289a050e6bdf4e48a30b0105f4",
        263,
        "Amendment 0005 active entrypoint",
    ),
    "src/crypto_trade/tournament/_strategy_worker_v2.py": (
        "fff67076592e337adb721b72c4c77326c3e40e396ba57217c387a8b5f58f2b5d",
        46_620,
        "Phase-0 frozen strategy worker",
    ),
    "src/crypto_trade/tournament/amendment_integrity_v2.py": (
        "e3a4f60aa955ebcf461026527da5b6b28b87e9e7ec057dd2e10a1e884612a8ab",
        34_451,
        "Amendment integrity helpers",
    ),
    "src/crypto_trade/tournament/amendment_0005_integration_v2.py": (
        "c9e0b0be288edebf86f8c7d441b4093843ae3d64f0cbac42dbadf21625f786f8",
        3_080,
        "Amendment 0005 active integration module",
    ),
    "src/crypto_trade/tournament/amendment_0005_v2.py": (
        "a61795b2e979bbcbbb44d4dd9e321b3db7190992c386b3129b832e1256a002bf",
        84_717,
        "Amendment 0005 authority module",
    ),
    "src/crypto_trade/tournament/runner_schema3_compat_v4.py": (
        "03006ea1ce391ef3c8da6244acb89aab19f7e63d1e0a617e2743894a575fd6cd",
        12_114,
        "Amendment 0004 active runner",
    ),
    "src/crypto_trade/tournament/score_diagnostic_compat_v2.py": (
        "fc70dbdb752c58857c5ed60a96e497324e93b9d5dc7e6afa0692bd3e02ad21aa",
        10_828,
        "Amendment 0002 shared patch authority",
    ),
    "src/crypto_trade/tournament/runner_v2.py": (
        "d4fc1c381f9e69c0dbdd5b7c6e5d273e43b39c5df16a082a99af1b4ef7310ec2",
        86_317,
        "Phase-0 frozen runner",
    ),
    "src/crypto_trade/tournament/score_adapter_protocol_v5.py": (
        "8f8f5db3be3069cce7c7c0605fb15b31c4f28af7c2e0f2e24d79d861a65ae4ff",
        1_037,
        "Amendment 0005 score protocol",
    ),
    "tournament/top40-v2/amendments/0005/freeze.json": (
        "0f112dc0e6452e29d691f46d42b8c19ea46482bda0b813143664acf056954c5f",
        5_477,
        "Amendment 0005 freeze",
    ),
    "tournament/top40-v2/amendments/0004/freeze.json": (
        "bfb9e82c0b9a0950ead9b94ae61fe9f6c091462b106e46bd51113894b6eb9465",
        1_865,
        "Amendment 0004 freeze",
    ),
    "tournament/top40-v2/amendments/0005/integration-freeze.json": (
        "b3b2b96245a479ccfff95b5cd5b5cd0aef3b2d0aac0fc9faf5367d3e6772958c",
        2_286,
        "Amendment 0005 integration freeze",
    ),
    "tournament/top40-v2/amendments/0006/integration-freeze.json": (
        "3e93bdfe031e2589888c3bbcaae583437bbd074fa9d86c6dc0a54187bc0f1e34",
        2_044,
        "Amendment 0006 integration freeze",
    ),
    "tournament/top40-v2/phase0_freeze.json": (
        "cc7484d0be2fe6b64b34b6f4c7ce76647af750b02c3df065c4b81e10f1396259",
        5_301,
        "Phase-0 freeze",
    ),
}

_WORKER_WRAPPER_SHA256 = "a90ff198d5c03e4f3b85bfda8e95f218627b631884154858f6d084537fdd70ac"
_WORKER_WRAPPER_SIZE = 7_351

IMPLEMENTATION_FILE_PATHS = (
    ENTRYPOINT_PATH,
    WORKER_WRAPPER_PATH,
    IMPLEMENTATION_MODULE_PATH,
    "tests/tournament/test_top40_v2_amendment_0007.py",
    SPEC_PATH,
    DRAFT_PATH,
)

_A5_INTEGRATION_MODULE = amendment_0005_integration_v2
_A5_INTEGRATION_RUN = _A5_INTEGRATION_MODULE.run
_A5_AUTHORITY_MODULE = amendment_0005_v2
_A5_AUTHORITY_VERIFY = _A5_AUTHORITY_MODULE.verify_parent_authorities
_A5_LOAD_ACTIVE_INTEGRATION = _A5_AUTHORITY_MODULE._load_active_integration
_A5_INTEGRATION_BINDINGS = {
    "_A5_MODULE": _A5_INTEGRATION_MODULE._A5_MODULE,
    "_A5_STATUS": _A5_INTEGRATION_MODULE._A5_STATUS,
    "_A5_RESERVE": _A5_INTEGRATION_MODULE._A5_RESERVE,
    "_A5_RUN": _A5_INTEGRATION_MODULE._A5_RUN,
    "_A5_ACTIVE_GUARD": _A5_INTEGRATION_MODULE._A5_ACTIVE_GUARD,
    "_A5_AUTHORIZATION": _A5_INTEGRATION_MODULE._A5_AUTHORIZATION,
    "_A6_RUN": _A5_INTEGRATION_MODULE._A6_RUN,
}
_A5_COMMANDS = _A5_INTEGRATION_MODULE.AMENDMENT_0005_COMMANDS
_A4_MODULE = runner_schema3_compat_v4
_A4_VERIFY = _A4_MODULE._verify_amendment_authorities
_PATCH_LOCK = _A4_MODULE._A2_PATCH_LOCK
_A2_MODULE = score_diagnostic_compat_v2
_A2_PATCH_LOCK = _A2_MODULE._PATCH_LOCK
_RUNNER_MODULE = runner_v2
_FROZEN_STRATEGY_WORKER_COMMAND = _RUNNER_MODULE._strategy_worker_command
_PROTOCOL_MODULE = score_adapter_protocol_v5
_PROTOCOL_SCORE_BOUNDARY = _PROTOCOL_MODULE.score_boundary
_READ_REPO_FILE = amendment_integrity_v2.read_repo_file
_SHA256_BYTES = amendment_integrity_v2.sha256_bytes
_PRETTY_JSON_BYTES = amendment_integrity_v2.pretty_json_bytes
_STRICT_JSON_OBJECT = amendment_integrity_v2.strict_json_object
_PARSE_UTC = amendment_integrity_v2.parse_utc
_UNIQUE_FIRST_ADD_COMMIT = amendment_integrity_v2.unique_first_add_commit
_GIT_BYTES = amendment_integrity_v2.git_bytes
_REQUIRE_ANCESTOR = amendment_integrity_v2._require_ancestor
_VALIDATE_JOURNAL_PREFIX = _A5_AUTHORITY_MODULE._validate_zero_based_journal_prefix


class _ActiveIntegrationAuthorization:
    """Private identity capability held only by the reviewed A7 entrypoint path."""


_ACTIVE_INTEGRATION_AUTHORIZATION = _ActiveIntegrationAuthorization()


class Amendment0007Error(ValueError):
    """The pending A7 compatibility boundary failed closed."""


def _bound_repo_bytes(
    root: Path,
    relative: str,
    expected_sha256: str,
    expected_size: int,
    label: str,
) -> bytes:
    try:
        observed, _path, payload, info = _READ_REPO_FILE(
            root,
            relative,
            label,
            maximum_bytes=expected_size,
            require_single_link=True,
        )
    except (OSError, ValueError) as exc:
        raise Amendment0007Error(f"cannot read {label}: {exc}") from exc
    if (
        observed != relative
        or info.st_size != expected_size
        or len(payload) != expected_size
        or _SHA256_BYTES(payload) != expected_sha256
    ):
        raise Amendment0007Error(f"{label} differs from frozen authority")
    return payload


def verify_parent_authorities(root: str | Path) -> None:
    """Pin the exact active A5/A6 chain and untouched Phase-0 worker boundary."""

    root_path = Path(root).resolve()
    if (
        Path(__file__).resolve()
        != (root_path / "src/crypto_trade/tournament/amendment_0007_v2.py").resolve()
    ):
        raise Amendment0007Error("loaded Amendment 0007 path differs from repository")
    expected_module_paths = {
        amendment_integrity_v2: (
            root_path / "src/crypto_trade/tournament/amendment_integrity_v2.py"
        ).resolve(),
        _A5_INTEGRATION_MODULE: (
            root_path / "src/crypto_trade/tournament/amendment_0005_integration_v2.py"
        ).resolve(),
        _A5_AUTHORITY_MODULE: (
            root_path / "src/crypto_trade/tournament/amendment_0005_v2.py"
        ).resolve(),
        _A4_MODULE: (
            root_path / "src/crypto_trade/tournament/runner_schema3_compat_v4.py"
        ).resolve(),
        _A2_MODULE: (
            root_path / "src/crypto_trade/tournament/score_diagnostic_compat_v2.py"
        ).resolve(),
        _RUNNER_MODULE: (root_path / "src/crypto_trade/tournament/runner_v2.py").resolve(),
        _PROTOCOL_MODULE: (
            root_path / "src/crypto_trade/tournament/score_adapter_protocol_v5.py"
        ).resolve(),
    }
    for module, expected_path in expected_module_paths.items():
        loaded = getattr(module, "__file__", None)
        if type(loaded) is not str or Path(loaded).resolve() != expected_path:
            raise Amendment0007Error("loaded parent authority path differs from repository")

    for relative, (expected_sha256, expected_size, label) in PARENT_AUTHORITIES.items():
        _bound_repo_bytes(root_path, relative, expected_sha256, expected_size, label)
    _bound_repo_bytes(
        root_path,
        WORKER_WRAPPER_PATH,
        _WORKER_WRAPPER_SHA256,
        _WORKER_WRAPPER_SIZE,
        "Amendment 0007 worker wrapper",
    )

    if _A5_INTEGRATION_MODULE.run is not _A5_INTEGRATION_RUN:
        raise Amendment0007Error("Amendment 0005 integration run identity changed")
    if any(
        getattr(_A5_INTEGRATION_MODULE, name, _MISSING) is not expected
        for name, expected in _A5_INTEGRATION_BINDINGS.items()
    ):
        raise Amendment0007Error("Amendment 0005 integration binding changed")
    if (
        _A5_INTEGRATION_MODULE.AMENDMENT_0005_COMMANDS != _A5_COMMANDS
        or _A5_AUTHORITY_MODULE.verify_parent_authorities is not _A5_AUTHORITY_VERIFY
        or _A5_AUTHORITY_MODULE._load_active_integration is not _A5_LOAD_ACTIVE_INTEGRATION
    ):
        raise Amendment0007Error("Amendment 0005 command authority changed")
    if (
        _A4_MODULE._verify_amendment_authorities is not _A4_VERIFY
        or _A4_MODULE._A2_PATCH_LOCK is not _PATCH_LOCK
        or _A2_MODULE._PATCH_LOCK is not _A2_PATCH_LOCK
        or _A2_PATCH_LOCK is not _PATCH_LOCK
    ):
        raise Amendment0007Error("Amendment 0004 patch authority changed")
    if _RUNNER_MODULE._strategy_worker_command is not _FROZEN_STRATEGY_WORKER_COMMAND:
        raise Amendment0007Error("frozen strategy-worker command was already replaced")
    if (
        _PROTOCOL_MODULE.score_boundary is not _PROTOCOL_SCORE_BOUNDARY
        or _PROTOCOL_MODULE.ADAPTER_ID != "top40-v2-declared-score-boundary-v1"
        or _PROTOCOL_MODULE.HOOK_QUALNAME != "strategy.score_boundary"
        or _PROTOCOL_MODULE.CAPTURE_BOUNDARY
        != "candidate-declared-post-transform-pre-selection-weight-cap-risk"
    ):
        raise Amendment0007Error("Amendment 0005 score protocol identity changed")
    if (
        amendment_integrity_v2.read_repo_file is not _READ_REPO_FILE
        or amendment_integrity_v2.sha256_bytes is not _SHA256_BYTES
        or amendment_integrity_v2.pretty_json_bytes is not _PRETTY_JSON_BYTES
        or amendment_integrity_v2.strict_json_object is not _STRICT_JSON_OBJECT
        or amendment_integrity_v2.parse_utc is not _PARSE_UTC
        or amendment_integrity_v2.unique_first_add_commit is not _UNIQUE_FIRST_ADD_COMMIT
        or amendment_integrity_v2.git_bytes is not _GIT_BYTES
        or amendment_integrity_v2._require_ancestor is not _REQUIRE_ANCESTOR
        or _A5_AUTHORITY_MODULE._validate_zero_based_journal_prefix is not _VALIDATE_JOURNAL_PREFIX
    ):
        raise Amendment0007Error("amendment integrity helper identity changed")
    _verify_delegated_a5_integration(root_path)
    _A4_VERIFY()


def _verify_delegated_a5_integration(root: Path) -> tuple[Mapping[str, Any], bytes, str]:
    try:
        integration, payload, commit = _A5_LOAD_ACTIVE_INTEGRATION(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise Amendment0007Error(f"cannot verify delegated A5 integration: {exc}") from exc
    if (
        commit != _DELEGATED_A5_INTEGRATION["commit"]
        or _SHA256_BYTES(payload) != _DELEGATED_A5_INTEGRATION["sha256"]
    ):
        raise Amendment0007Error("delegated A5 integration authority differs")
    return integration, payload, commit


def _read_pretty_json(
    root: Path, relative: str, label: str
) -> tuple[Mapping[str, Any], bytes, str]:
    try:
        observed, _path, payload, _info = _READ_REPO_FILE(
            root,
            relative,
            label,
            maximum_bytes=4 * 1024 * 1024,
            require_single_link=True,
        )
        raw = _STRICT_JSON_OBJECT(payload, label)
        if observed != relative or _PRETTY_JSON_BYTES(raw) != payload:
            raise ValueError(f"{label} is not canonical pretty JSON")
        commit = _UNIQUE_FIRST_ADD_COMMIT(root, relative, payload)
    except (OSError, ValueError) as exc:
        raise Amendment0007Error(f"cannot verify {label}: {exc}") from exc
    return raw, payload, commit


def _file_binding(path: str, payload: bytes) -> dict[str, str]:
    return {"path": path, "sha256": _SHA256_BYTES(payload)}


def _authority_binding(path: str, payload: bytes, commit: str) -> dict[str, str]:
    return {"commit": commit, "path": path, "sha256": _SHA256_BYTES(payload)}


def _parent_authority_records() -> dict[str, dict[str, object]]:
    return {
        path: {"sha256": sha256, "size": size}
        for path, (sha256, size, _label) in PARENT_AUTHORITIES.items()
    }


def _canonical_utc(value: object, label: str) -> datetime:
    if type(value) is not str or not value.endswith("Z"):
        raise Amendment0007Error(f"{label} must be canonical UTC text")
    try:
        parsed = _PARSE_UTC(value, label)
    except ValueError as exc:
        raise Amendment0007Error(f"{label} is invalid") from exc
    if parsed.isoformat().replace("+00:00", "Z") != value:
        raise Amendment0007Error(f"{label} is not canonical")
    return parsed


def _implementation_bytes(root: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for relative in IMPLEMENTATION_FILE_PATHS:
        try:
            observed, _path, payload, _info = _READ_REPO_FILE(
                root,
                relative,
                f"Amendment 0007 implementation file {relative}",
                maximum_bytes=4 * 1024 * 1024,
                require_single_link=True,
            )
        except (OSError, ValueError) as exc:
            raise Amendment0007Error(
                f"cannot read A7 implementation file {relative}: {exc}"
            ) from exc
        if observed != relative:
            raise Amendment0007Error("Amendment 0007 implementation path changed")
        result[relative] = payload
    return result


def _require_strict_ancestor(root: Path, ancestor: str, descendant: str, label: str) -> None:
    if (
        _COMMIT.fullmatch(ancestor) is None
        or _COMMIT.fullmatch(descendant) is None
        or ancestor == descendant
    ):
        raise Amendment0007Error(f"{label} must be strictly ordered")
    try:
        _REQUIRE_ANCESTOR(root, ancestor, descendant, label)
    except ValueError as exc:
        raise Amendment0007Error(f"{label} ancestry is invalid") from exc


def _require_commit_tree(
    root: Path,
    commit: str,
    expected: Mapping[str, bytes],
    label: str,
) -> None:
    for relative, payload in expected.items():
        try:
            committed = _GIT_BYTES(
                root,
                "show",
                f"{commit}:{relative}",
                label=f"{label} tree file {relative}",
            )
        except ValueError as exc:
            raise Amendment0007Error(f"cannot verify {label} tree") from exc
        if committed != payload:
            raise Amendment0007Error(f"{label} tree lacks exact authority bytes")


def _load_active_integration(
    root: Path,
) -> tuple[Mapping[str, Any], bytes, str]:
    """Validate A7's independently reviewed prospective activation chain."""

    verify_parent_authorities(root)
    implementation = _implementation_bytes(root)
    implementation_hashes = {
        relative: _SHA256_BYTES(payload) for relative, payload in implementation.items()
    }
    try:
        implementation_commits = {
            _UNIQUE_FIRST_ADD_COMMIT(root, relative, payload)
            for relative, payload in implementation.items()
        }
    except ValueError as exc:
        raise Amendment0007Error(f"A7 implementation history is invalid: {exc}") from exc
    if len(implementation_commits) != 1:
        raise Amendment0007Error("A7 implementation files lack one exact first-add commit")
    implementation_commit = next(iter(implementation_commits))
    _require_strict_ancestor(
        root,
        _DELEGATED_A5_INTEGRATION["commit"],
        implementation_commit,
        "A5 integration/A7 implementation",
    )
    parent_records = _parent_authority_records()

    review, review_bytes, review_commit = _read_pretty_json(
        root, REVIEW_PATH, "Amendment 0007 implementation review"
    )
    if set(review) != {
        "activation_authorized",
        "amendment_id",
        "decision",
        "implementation_commit",
        "implementation_files",
        "parent_authorities",
        "review_scope",
        "reviewed_at_utc",
        "reviewer_id",
        "schema_version",
        "validation",
    }:
        raise Amendment0007Error("Amendment 0007 implementation review has invalid keys")
    reviewed_at = _canonical_utc(review.get("reviewed_at_utc"), "A7 review timestamp")
    validation = review.get("validation")
    if (
        review.get("schema_version") != 1
        or review.get("amendment_id") != AMENDMENT_ID
        or review.get("decision") != "approved"
        or review.get("activation_authorized") is not False
        or review.get("implementation_commit") != implementation_commit
        or review.get("implementation_files") != implementation_hashes
        or review.get("parent_authorities") != parent_records
        or review.get("review_scope") != _IMPLEMENTATION_REVIEW_SCOPE
        or type(review.get("reviewer_id")) is not str
        or not str(review["reviewer_id"]).strip()
        or review["reviewer_id"] != str(review["reviewer_id"]).strip()
        or not isinstance(validation, Mapping)
        or set(validation)
        != {
            "a5_a6_a4_regression",
            "focused_a7",
            "frozen_worker_regression",
            "real_namespace_mask_smoke",
            "ruff",
        }
        or any(value != "passed" for value in validation.values())
    ):
        raise Amendment0007Error("Amendment 0007 implementation review differs")
    _require_strict_ancestor(root, implementation_commit, review_commit, "A7 implementation/review")

    freeze, freeze_bytes, freeze_commit = _read_pretty_json(
        root, FREEZE_PATH, "Amendment 0007 freeze"
    )
    review_binding = _authority_binding(REVIEW_PATH, review_bytes, review_commit)
    expected_freeze_files = dict(implementation_hashes)
    expected_freeze_files[REVIEW_PATH] = _SHA256_BYTES(review_bytes)
    if set(freeze) != {
        "activation_status",
        "amendment_id",
        "entrypoint_candidate",
        "files",
        "final_implementation_commit",
        "freeze_timestamp_utc",
        "parent_authorities",
        "review",
        "schema_version",
        "status",
    }:
        raise Amendment0007Error("Amendment 0007 freeze has invalid keys")
    frozen_at = _canonical_utc(freeze.get("freeze_timestamp_utc"), "A7 freeze timestamp")
    if (
        freeze.get("schema_version") != 1
        or freeze.get("amendment_id") != AMENDMENT_ID
        or freeze.get("status") != "frozen"
        or freeze.get("activation_status") != "pending-integration"
        or freeze.get("entrypoint_candidate")
        != _file_binding(ENTRYPOINT_PATH, implementation[ENTRYPOINT_PATH])
        or freeze.get("files") != expected_freeze_files
        or freeze.get("final_implementation_commit") != implementation_commit
        or freeze.get("parent_authorities") != parent_records
        or freeze.get("review") != review_binding
        or frozen_at < reviewed_at
    ):
        raise Amendment0007Error("Amendment 0007 freeze differs")
    _require_strict_ancestor(root, review_commit, freeze_commit, "A7 review/freeze")
    freeze_binding = _authority_binding(FREEZE_PATH, freeze_bytes, freeze_commit)

    entrypoint_binding = _file_binding(ENTRYPOINT_PATH, implementation[ENTRYPOINT_PATH])
    module_binding = _file_binding(
        IMPLEMENTATION_MODULE_PATH, implementation[IMPLEMENTATION_MODULE_PATH]
    )
    wrapper_binding: dict[str, object] = {
        "path": WORKER_WRAPPER_PATH,
        "sha256": _SHA256_BYTES(implementation[WORKER_WRAPPER_PATH]),
        "size": len(implementation[WORKER_WRAPPER_PATH]),
    }
    draft, integration_draft_bytes, integration_draft_commit = _read_pretty_json(
        root, INTEGRATION_DRAFT_PATH, "Amendment 0007 integration draft"
    )
    if set(draft) != {
        "active_entrypoint",
        "amendment_freeze",
        "amendment_id",
        "delegated_amendment_0005_integration",
        "dispatch_scope",
        "historical_entrypoint",
        "implementation_module",
        "proposed_at_utc",
        "schema_version",
        "status",
        "worker_wrapper",
    }:
        raise Amendment0007Error("Amendment 0007 integration draft has invalid keys")
    proposed_at = _canonical_utc(draft.get("proposed_at_utc"), "A7 integration proposal timestamp")
    if (
        draft.get("schema_version") != 1
        or draft.get("amendment_id") != AMENDMENT_ID
        or draft.get("status") != "draft"
        or draft.get("active_entrypoint") != entrypoint_binding
        or draft.get("amendment_freeze") != freeze_binding
        or draft.get("delegated_amendment_0005_integration") != _DELEGATED_A5_INTEGRATION
        or draft.get("dispatch_scope") != _DISPATCH_SCOPE
        or draft.get("historical_entrypoint") != _HISTORICAL_ENTRYPOINT
        or draft.get("implementation_module") != module_binding
        or draft.get("worker_wrapper") != wrapper_binding
        or proposed_at < frozen_at
    ):
        raise Amendment0007Error("Amendment 0007 integration draft differs")
    _require_strict_ancestor(
        root, freeze_commit, integration_draft_commit, "A7 freeze/integration draft"
    )
    integration_draft_binding = _authority_binding(
        INTEGRATION_DRAFT_PATH, integration_draft_bytes, integration_draft_commit
    )

    integration_review, integration_review_bytes, integration_review_commit = _read_pretty_json(
        root, INTEGRATION_REVIEW_PATH, "Amendment 0007 integration review"
    )
    if set(integration_review) != {
        "activation_authorized",
        "active_entrypoint",
        "amendment_freeze",
        "amendment_id",
        "decision",
        "delegated_amendment_0005_integration",
        "dispatch_scope",
        "historical_entrypoint",
        "implementation_module",
        "integration_draft",
        "review_scope",
        "reviewed_at_utc",
        "reviewer_id",
        "schema_version",
        "worker_wrapper",
    }:
        raise Amendment0007Error("Amendment 0007 integration review has invalid keys")
    integration_reviewed_at = _canonical_utc(
        integration_review.get("reviewed_at_utc"), "A7 integration review timestamp"
    )
    if (
        integration_review.get("schema_version") != 1
        or integration_review.get("amendment_id") != AMENDMENT_ID
        or integration_review.get("decision") != "approved"
        or integration_review.get("activation_authorized") is not True
        or integration_review.get("active_entrypoint") != entrypoint_binding
        or integration_review.get("amendment_freeze") != freeze_binding
        or integration_review.get("delegated_amendment_0005_integration")
        != _DELEGATED_A5_INTEGRATION
        or integration_review.get("dispatch_scope") != _DISPATCH_SCOPE
        or integration_review.get("historical_entrypoint") != _HISTORICAL_ENTRYPOINT
        or integration_review.get("implementation_module") != module_binding
        or integration_review.get("integration_draft") != integration_draft_binding
        or integration_review.get("review_scope") != _INTEGRATION_REVIEW_SCOPE
        or integration_review.get("worker_wrapper") != wrapper_binding
        or type(integration_review.get("reviewer_id")) is not str
        or not str(integration_review["reviewer_id"]).strip()
        or integration_review["reviewer_id"] != str(integration_review["reviewer_id"]).strip()
        or integration_review["reviewer_id"] == review["reviewer_id"]
        or integration_reviewed_at < proposed_at
    ):
        raise Amendment0007Error("Amendment 0007 integration review differs")
    _require_strict_ancestor(
        root,
        integration_draft_commit,
        integration_review_commit,
        "A7 integration draft/review",
    )
    integration_review_binding = _authority_binding(
        INTEGRATION_REVIEW_PATH, integration_review_bytes, integration_review_commit
    )

    integration, integration_bytes, integration_commit = _read_pretty_json(
        root, INTEGRATION_FREEZE_PATH, "Amendment 0007 integration freeze"
    )
    if set(integration) != {
        "activation_journal",
        "activation_timestamp_utc",
        "active_entrypoint",
        "amendment_freeze",
        "amendment_id",
        "delegated_amendment_0005_integration",
        "dispatch_scope",
        "historical_entrypoint",
        "implementation_module",
        "integration_draft",
        "integration_review",
        "schema_version",
        "status",
        "worker_wrapper",
    }:
        raise Amendment0007Error("Amendment 0007 integration freeze has invalid keys")
    activated_at = _canonical_utc(
        integration.get("activation_timestamp_utc"), "A7 activation timestamp"
    )
    activation = integration.get("activation_journal")
    if (
        integration.get("schema_version") != 1
        or integration.get("amendment_id") != AMENDMENT_ID
        or integration.get("status") != "active"
        or integration.get("active_entrypoint") != entrypoint_binding
        or integration.get("amendment_freeze") != freeze_binding
        or integration.get("delegated_amendment_0005_integration") != _DELEGATED_A5_INTEGRATION
        or integration.get("dispatch_scope") != _DISPATCH_SCOPE
        or integration.get("historical_entrypoint") != _HISTORICAL_ENTRYPOINT
        or integration.get("implementation_module") != module_binding
        or integration.get("integration_draft") != integration_draft_binding
        or integration.get("integration_review") != integration_review_binding
        or integration.get("worker_wrapper") != wrapper_binding
        or activated_at < integration_reviewed_at
        or not isinstance(activation, Mapping)
        or set(activation) != {"head_sha256", "path", "record_count"}
        or activation.get("path") != _JOURNAL_PATH
        or type(activation.get("record_count")) is not int
        or activation["record_count"] < _A5_ACTIVATION_RECORD_COUNT
        or type(activation.get("head_sha256")) is not str
        or _SHA256.fullmatch(activation["head_sha256"]) is None
    ):
        raise Amendment0007Error("Amendment 0007 integration freeze differs")
    _require_strict_ancestor(
        root,
        integration_review_commit,
        integration_commit,
        "A7 integration review/freeze",
    )

    governance = {
        REVIEW_PATH: review_bytes,
        FREEZE_PATH: freeze_bytes,
        INTEGRATION_DRAFT_PATH: integration_draft_bytes,
        INTEGRATION_REVIEW_PATH: integration_review_bytes,
        INTEGRATION_FREEZE_PATH: integration_bytes,
    }
    cumulative = dict(implementation)
    for commit, relative, label in (
        (review_commit, REVIEW_PATH, "A7 review"),
        (freeze_commit, FREEZE_PATH, "A7 freeze"),
        (integration_draft_commit, INTEGRATION_DRAFT_PATH, "A7 integration draft"),
        (integration_review_commit, INTEGRATION_REVIEW_PATH, "A7 integration review"),
        (integration_commit, INTEGRATION_FREEZE_PATH, "A7 integration freeze"),
    ):
        cumulative[relative] = governance[relative]
        _require_commit_tree(root, commit, cumulative, label)

    parent_bytes = {
        relative: _bound_repo_bytes(root, relative, sha256, size, label)
        for relative, (sha256, size, label) in PARENT_AUTHORITIES.items()
    }
    _require_commit_tree(root, integration_commit, parent_bytes, "A7 integration freeze")
    try:
        journal_at_activation = _GIT_BYTES(
            root,
            "show",
            f"{integration_commit}:{_JOURNAL_PATH}",
            label="A7 activation journal",
        )
        records = _VALIDATE_JOURNAL_PREFIX(
            journal_at_activation,
            activation["record_count"],
            activation["head_sha256"],
            "A7 activation journal",
        )
    except (OSError, ValueError) as exc:
        raise Amendment0007Error(f"A7 activation journal is invalid: {exc}") from exc
    if (
        len(records) < _A5_ACTIVATION_RECORD_COUNT
        or records[_A5_ACTIVATION_RECORD_COUNT - 1].get("record_sha256")
        != _A5_ACTIVATION_HEAD_SHA256
    ):
        raise Amendment0007Error("A7 activation journal does not extend A5 activation")
    return integration, integration_bytes, integration_commit


@contextlib.contextmanager
def _active_integration_guard(
    root: Path, *, _authorization: object | None = None
) -> Iterator[Mapping[str, Any]]:
    if _authorization is not _ACTIVE_INTEGRATION_AUTHORIZATION:
        raise PermissionError("Amendment 0007 requires active-entrypoint authority")
    _A7_VERIFY_LOADED_DISPATCH(root)
    before, before_bytes, before_commit = _load_active_integration(root)
    try:
        yield before
    finally:
        after, after_bytes, after_commit = _load_active_integration(root)
        _A7_VERIFY_LOADED_DISPATCH(root)
        if after != before or after_bytes != before_bytes or after_commit != before_commit:
            raise Amendment0007Error("Amendment 0007 integration changed during dispatch")


def _replace_worker_module(command: list[str]) -> list[str]:
    if type(command) is not list or any(type(token) is not str for token in command):
        raise Amendment0007Error("frozen worker command must be an exact string list")
    positions = [
        index
        for index in range(len(command) - 1)
        if command[index] == "-m" and command[index + 1] == _FROZEN_WORKER_MODULE
    ]
    if (
        len(positions) != 1
        or command.count(_FROZEN_WORKER_MODULE) != 1
        or _PRELOAD_WORKER_MODULE in command
    ):
        raise Amendment0007Error("frozen worker command module boundary is invalid")
    replaced = list(command)
    replaced[positions[0] + 1] = _PRELOAD_WORKER_MODULE
    return replaced


class _PreloadStrategyWorkerCommand:
    """One-run exact command-builder replacement with an auditable call count."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(
        self,
        root: Path,
        repository_parent: Path,
        bundle: Path,
        site_packages: Path,
        runtime_site_packages: Path,
        entrypoint: str,
        empty_dir: Path,
        empty_file: Path,
    ) -> list[str]:
        if getattr(_RUNNER_MODULE, "_strategy_worker_command", _MISSING) is not self:
            raise Amendment0007Error("A7 worker-command binding changed before invocation")
        self.calls += 1
        if self.calls != 1:
            raise Amendment0007Error("A7 worker command was invoked more than once")
        command = _FROZEN_STRATEGY_WORKER_COMMAND(
            root,
            repository_parent,
            bundle,
            site_packages,
            runtime_site_packages,
            entrypoint,
            empty_dir,
            empty_file,
        )
        if entrypoint != "strategy.py":
            raise Amendment0007Error("A7 worker preload requires exact root strategy.py")
        return _replace_worker_module(command)


def _verify_loaded_integration_dispatch(root: Path) -> None:
    module = sys.modules.get(__name__)
    loaded = None if module is None else getattr(module, "__file__", None)
    expected_path = (root / IMPLEMENTATION_MODULE_PATH).resolve()
    if module is None or type(loaded) is not str or Path(loaded).resolve() != expected_path:
        raise PermissionError("Amendment 0007 requires its active integration dispatcher")
    identities = {
        "_ACTIVE_INTEGRATION_AUTHORIZATION": _A7_AUTHORIZATION,
        "_A5_INTEGRATION_RUN": _A5_INTEGRATION_MODULE.run,
        "_FROZEN_STRATEGY_WORKER_COMMAND": _RUNNER_MODULE._strategy_worker_command,
        "_PATCH_LOCK": _A4_MODULE._A2_PATCH_LOCK,
        "_PreloadStrategyWorkerCommand": _A7_COMMAND_TYPE,
        "_active_integration_guard": _A7_ACTIVE_GUARD,
        "_load_active_integration": _A7_LOAD_ACTIVE_INTEGRATION,
        "_replace_worker_module": _A7_REPLACE_WORKER_MODULE,
        "_run_development_with_preload": _A7_RUN_DEVELOPMENT_WITH_PRELOAD,
        "_verified_delegate": _A7_VERIFIED_DELEGATE,
        "_verify_loaded_integration_dispatch": _A7_VERIFY_LOADED_DISPATCH,
        "main": _A7_MAIN,
        "run": _A7_RUN,
        "verify_parent_authorities": _A7_VERIFY_PARENT_AUTHORITIES,
    }
    if any(getattr(module, name, _MISSING) is not value for name, value in identities.items()):
        raise PermissionError("Amendment 0007 active integration identity changed")
    if (
        module.AMENDMENT_ID != "top40-v2-amendment-0007-frozen-worker-a5-protocol-preload"
        or module.ENTRYPOINT_PATH != "scripts/top40_v2_tournament_runtime_preload_v7.py"
        or module.WORKER_WRAPPER_PATH
        != "src/crypto_trade/tournament/_strategy_worker_preload_v7.py"
        or module._FROZEN_WORKER_MODULE != "crypto_trade.tournament._strategy_worker_v2"
        or module._PRELOAD_WORKER_MODULE != "crypto_trade.tournament._strategy_worker_preload_v7"
        or module._ELIGIBLE_PRELOAD_TEAMS != tuple(f"team-{index:02d}" for index in range(4, 11))
    ):
        raise PermissionError("Amendment 0007 active integration constants changed")


def _verified_delegate(root: Path, call: Callable[[], int]) -> int:
    verify_parent_authorities(root)
    result: int | None = None
    failure: BaseException | None = None
    try:
        result = int(call())
    except BaseException as exc:
        failure = exc
    try:
        verify_parent_authorities(root)
    except BaseException as integrity_failure:
        raise integrity_failure from failure
    if failure is not None:
        raise failure.with_traceback(failure.__traceback__)
    if result is None:
        raise Amendment0007Error("Amendment 0005 delegate returned no result")
    return result


def _run_development_with_preload(
    argv: Sequence[str] | None,
    *,
    root: Path,
) -> int:
    with _PATCH_LOCK:
        verify_parent_authorities(root)
        original = getattr(_RUNNER_MODULE, "_strategy_worker_command", _MISSING)
        if original is not _FROZEN_STRATEGY_WORKER_COMMAND:
            raise Amendment0007Error("frozen strategy-worker command was already replaced")

        result: int | None = None
        failure: BaseException | None = None
        observed: Any = _MISSING
        restored = False
        restoration_failure: BaseException | None = None
        replacement = _PreloadStrategyWorkerCommand()
        try:
            _RUNNER_MODULE._strategy_worker_command = replacement
            if _RUNNER_MODULE._strategy_worker_command is not replacement:
                raise Amendment0007Error("A7 worker-command patch could not be installed")
            result = int(_A5_INTEGRATION_RUN(argv, root=root))
        except BaseException as exc:
            failure = exc
        finally:
            observed = getattr(_RUNNER_MODULE, "_strategy_worker_command", _MISSING)
            try:
                _RUNNER_MODULE._strategy_worker_command = original
            except BaseException as exc:
                restoration_failure = exc
            restored = getattr(_RUNNER_MODULE, "_strategy_worker_command", _MISSING) is original

        try:
            if restoration_failure is not None:
                raise Amendment0007Error(
                    "frozen strategy-worker command restoration raised"
                ) from restoration_failure
            if observed is not replacement or not restored:
                raise Amendment0007Error(
                    "A7 worker-command binding changed or failed exact restoration"
                )
            if failure is None and replacement.calls != 1:
                raise Amendment0007Error(
                    "successful development run did not launch exactly one strategy worker"
                )
            verify_parent_authorities(root)
        except BaseException as integrity_failure:
            raise integrity_failure from failure
        if failure is not None:
            raise failure.with_traceback(failure.__traceback__)
        if result is None:
            raise Amendment0007Error("Amendment 0005 delegate returned no result")
        return result


def run(
    argv: Sequence[str] | None = None,
    *,
    root: str | Path | None = None,
    _authorization: object | None = None,
) -> int:
    """Delegate to exact A5, patching only ordinary development worker selection."""

    values = list(sys.argv[1:] if argv is None else argv)
    root_path = Path.cwd().resolve() if root is None else Path(root).resolve()
    with _active_integration_guard(root_path, _authorization=_authorization):
        if (
            len(values) == 4
            and values[0] == "run-window"
            and values[1] == "development"
            and values[2] in _ELIGIBLE_PRELOAD_TEAMS
            and _CANDIDATE_ID.fullmatch(values[3]) is not None
        ):
            return _run_development_with_preload(values, root=root_path)
        return _verified_delegate(
            root_path,
            lambda: int(_A5_INTEGRATION_RUN(values, root=root_path)),
        )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv, _authorization=_ACTIVE_INTEGRATION_AUTHORIZATION)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"top40-v2-amendment-0007: error: {exc}", file=sys.stderr)
        return 2


_A7_AUTHORIZATION = _ACTIVE_INTEGRATION_AUTHORIZATION
_A7_COMMAND_TYPE = _PreloadStrategyWorkerCommand
_A7_ACTIVE_GUARD = _active_integration_guard
_A7_LOAD_ACTIVE_INTEGRATION = _load_active_integration
_A7_REPLACE_WORKER_MODULE = _replace_worker_module
_A7_RUN_DEVELOPMENT_WITH_PRELOAD = _run_development_with_preload
_A7_VERIFIED_DELEGATE = _verified_delegate
_A7_VERIFY_LOADED_DISPATCH = _verify_loaded_integration_dispatch
_A7_VERIFY_PARENT_AUTHORITIES = verify_parent_authorities
_A7_RUN = run
_A7_MAIN = main
