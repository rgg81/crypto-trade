"""Canonical, fail-closed Phase-0 freeze contract for Top-40 V3.

This module hashes bytes and validates supplied organizer evidence.  It does not import or execute
any evaluator, V2 lifecycle/state authority, test runner, or pure-crypto audit implementation.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import stat
import tomllib
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path, PurePosixPath
from typing import Any

PHASE0_RECORD_PATH = "tournament/top40-v3/phase0-freeze.json"
TOURNAMENT_ID = "quant-portfolio-blind-top40-v3"
SCHEMA_VERSION = 1
GENESIS_SHA256 = "0" * 64
TEAM_IDS = tuple(f"team-{number:02d}" for number in range(1, 11))

_DOC_PATHS = (
    "TOURNAMENT-CHARTER-TOP40-V3.md",
    "tournament/top40-v3/ARCHITECTURE.md",
    "tournament/top40-v3/DIAGNOSTIC-RUBRIC.md",
    "tournament/top40-v3/IMPLEMENTATION-REVIEW.md",
    "tournament/top40-v3/INCUMBENT-CHALLENGER-POLICY.md",
    "tournament/top40-v3/ORCHESTRATOR-PROTOCOL.md",
    "tournament/top40-v3/PHASE0-POLICY.md",
    "tournament/top40-v3/PURE-CRYPTO-POLICY.md",
    "tournament/top40-v3/README.md",
    "tournament/top40-v3/RESEARCH-SCOUTING-2026.md",
    "tournament/top40-v3/TEAM-MANDATES.md",
    "tournament/top40-v3/TEAM-PLAYBOOK.md",
    "tournament/top40-v3/V2-CALIBRATION.md",
    "tournament/top40-v3/config.toml",
)
_SHARED_V3_CODE_PATHS = (
    "src/crypto_trade/tournament/_strategy_worker_v3.py",
    "src/crypto_trade/tournament/coaching_v3.py",
    "src/crypto_trade/tournament/journal_v3.py",
    "src/crypto_trade/tournament/lab_v3.py",
    "src/crypto_trade/tournament/layout_v3.py",
    "src/crypto_trade/tournament/metrics_v3.py",
    "src/crypto_trade/tournament/orchestrator_v3.py",
    "src/crypto_trade/tournament/phase0_v3.py",
    "src/crypto_trade/tournament/qualification_v3.py",
    "src/crypto_trade/tournament/runner_v3.py",
    "src/crypto_trade/tournament/sandbox_canary_v3.py",
    "src/crypto_trade/tournament/source_archive_v3.py",
    "src/crypto_trade/tournament/top40_v3.py",
)
_SANDBOX_CANARY_TEST_PATH = "tests/tournament/test_sandbox_canary_v3.py"
_SHARED_V3_TEST_PATHS = (
    "tests/tournament/test_coaching_v3.py",
    "tests/tournament/test_journal_v3.py",
    "tests/tournament/test_lab_v3.py",
    "tests/tournament/test_layout_v3.py",
    "tests/tournament/test_metrics_v3.py",
    "tests/tournament/test_orchestrator_v3.py",
    "tests/tournament/test_phase0_v3.py",
    "tests/tournament/test_qualification_v3.py",
    "tests/tournament/test_runner_v3_contract.py",
    _SANDBOX_CANARY_TEST_PATH,
    "tests/tournament/test_source_archive_v3.py",
    "tests/tournament/test_top40_v3_contract.py",
    "tests/tournament/test_v3_team_bundles.py",
)
_SANDBOX_CANARY_FIXTURE_PATHS = (
    "tournament/top40-v3/teams/team-01/fixtures/sandbox-canary/strategy.py",
)
_SHARED_EVALUATOR_PATHS = (
    "src/crypto_trade/tournament/data.py",
    "src/crypto_trade/tournament/engine_v2.py",
    "src/crypto_trade/tournament/layout.py",
    "src/crypto_trade/tournament/protocol.py",
    "src/crypto_trade/tournament/risk_policy.py",
)
_A6_CODE_PATHS = (
    "src/crypto_trade/tournament/amendment_integrity_v2.py",
    "src/crypto_trade/tournament/pure_crypto_universe_v6.py",
    "src/crypto_trade/tournament/top40_v2.py",
)
_ROOT_AUTHORITY_PATHS = (
    ".python-version",
    "pyproject.toml",
    "scripts/top40_v3_tournament.py",
    "tournament/top40/data_manifest.json",
    "uv.lock",
)
_INCUMBENT_TARGETED_TEST_PATHS = (
    "tournament/top40-v3/teams/team-04/incumbents/"
    "team-04-utc-reference-001-v3-port/test_team04_utc_incumbent.py",
    "tournament/top40-v3/teams/team-05/incumbents/"
    "team05-crtr-ab-dd-v3-port/test_team05_crtr_ab_dd_incumbent.py",
    "tournament/top40-v3/teams/team-07/incumbents/"
    "t07-two-tape-rank-durability-v1-base-v3-port/test_team07_two_tape_incumbent.py",
    "tournament/top40-v3/teams/team-09/incumbents/"
    "team09-drp-pivot02-v1-v3-port/test_team09_drp_incumbent.py",
)
_OTHER_TARGETED_TESTS = tuple(
    sorted(
        path
        for path in (
            *_SHARED_V3_TEST_PATHS,
            *_INCUMBENT_TARGETED_TEST_PATHS,
            *(
                f"tournament/top40-v3/teams/team-{number:02d}/test_team{number:02d}_strategy.py"
                for number in range(1, 11)
            ),
        )
        if path != _SANDBOX_CANARY_TEST_PATH
    )
)
REQUIRED_TARGETED_TESTS = (_SANDBOX_CANARY_TEST_PATH, *_OTHER_TARGETED_TESTS)
TARGETED_TEST_COMMAND = (
    "env",
    "PYTHONPATH=src",
    "PYTHONDONTWRITEBYTECODE=1",
    "uv",
    "run",
    "--frozen",
    "pytest",
    "-q",
    *REQUIRED_TARGETED_TESTS,
)

_A6_AUTHORITY_KEYS = {
    "policy_id",
    "policy_sha256",
    "audit_module_path",
    "audit_module_sha256",
    "audit_dependency_path",
    "audit_dependency_sha256",
    "audit_report_sha256",
    "data_manifest_path",
    "data_manifest_sha256",
    "membership_sha256",
    "contract_metadata_sha256",
    "exchange_info_sha256",
    "required_before_and_after_every_result_command",
    "expected_contract_metadata_symbols",
    "expected_distinct_membership_symbols",
    "expected_membership_rows",
    "expected_violations",
    "expected_audit_status",
}
_A6_AUTHORITY_PATHS = {
    "audit_module_path": "src/crypto_trade/tournament/pure_crypto_universe_v6.py",
    "audit_dependency_path": "src/crypto_trade/tournament/amendment_integrity_v2.py",
    "data_manifest_path": "tournament/top40/data_manifest.json",
}
_A6_AUTHORITY_SHA_KEYS = (
    "policy_sha256",
    "audit_module_sha256",
    "audit_dependency_sha256",
    "audit_report_sha256",
    "data_manifest_sha256",
    "membership_sha256",
    "contract_metadata_sha256",
    "exchange_info_sha256",
)
_A6_REPORT_KEYS = {
    "schema_version",
    "amendment_id",
    "policy_id",
    "policy_sha256",
    "status",
    "authorities",
    "counts",
    "accepted_symbol_sets",
    "classifications",
    "archive_only_symbols",
    "violations",
}
_FILE_ENTRY_KEYS = {
    "sequence",
    "type",
    "path",
    "size",
    "sha256",
    "previous_sha256",
    "entry_sha256",
}
_EVIDENCE_KEYS = {
    "schema_version",
    "command",
    "test_files",
    "scope_head_sha256",
    "completed",
    "exit_code",
    "collected",
    "passed",
    "failed",
    "skipped",
    "output_size",
    "output_sha256",
    "attestation_sha256",
}
_TEST_SECTION_KEYS = {
    "payload",
    "payload_sha256",
    "previous_sha256",
    "entry_sha256",
}
_A6_SECTION_KEYS = {
    "authority",
    "report",
    "report_size",
    "report_sha256",
    "previous_sha256",
    "entry_sha256",
}
_RECORD_KEYS = {
    "schema_version",
    "tournament_id",
    "scope_entries",
    "scope_head_sha256",
    "targeted_tests",
    "a6_audit",
    "chain_head_sha256",
    "record_sha256",
}


@dataclasses.dataclass(frozen=True)
class Phase0Authority:
    record_sha256: str
    chain_head_sha256: str
    scope_head_sha256: str
    scope_file_count: int


def canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def pretty_json_bytes(payload: object) -> bytes:
    return json.dumps(payload, allow_nan=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _exact_mapping(raw: object, keys: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{label} must be an object")
    actual = set(raw)
    if actual != keys:
        raise ValueError(
            f"{label} has unexpected record keys; missing={sorted(keys - actual)}, "
            f"extra={sorted(actual - keys, key=repr)}"
        )
    return raw


def _strict_json_object(payload: bytes, label: str) -> Mapping[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"{label} contains nonfinite JSON number {value}")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    try:
        parsed = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} must be valid UTF-8 JSON") from exc
    if not isinstance(parsed, Mapping):
        raise ValueError(f"{label} must be a JSON object")
    return parsed


def _safe_relative(relative: object, label: str) -> str:
    if not isinstance(relative, str) or not relative:
        raise ValueError(f"{label} must be a nonempty relative path")
    if "\\" in relative or relative.startswith("/"):
        raise ValueError(f"{label} is an unsafe path")
    raw_parts = relative.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise ValueError(f"{label} is an unsafe path")
    normalized = PurePosixPath(relative).as_posix()
    if normalized != relative:
        raise ValueError(f"{label} is not canonical")
    return normalized


def _trusted_root(root: str | Path) -> Path:
    candidate = Path(root)
    if candidate.is_symlink():
        raise ValueError("repository root cannot be a symlink")
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError("repository root is missing") from exc
    if not resolved.is_dir():
        raise ValueError("repository root must be a directory")
    return resolved


def _read_regular_file(root: Path, relative: str) -> tuple[bytes, os.stat_result]:
    current = root
    parts = PurePosixPath(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        try:
            metadata = os.lstat(current)
        except FileNotFoundError as exc:
            raise ValueError(f"Phase-0 scoped file is missing: {relative}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"Phase-0 scope rejects symlink: {relative}")
        if index < len(parts) - 1 and not stat.S_ISDIR(metadata.st_mode):
            raise ValueError(f"Phase-0 scoped parent is not a directory: {relative}")
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"Phase-0 scoped path is not a regular file: {relative}")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise ValueError(f"Phase-0 scoped path escapes repository root: {relative}") from exc
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(current, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev,
            opened.st_ino,
        ) != (metadata.st_dev, metadata.st_ino):
            raise ValueError(f"Phase-0 scoped file changed while opening: {relative}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        payload = b"".join(chunks)
        final = os.fstat(descriptor)
        if final.st_size != len(payload) or (final.st_mtime_ns, final.st_ctime_ns) != (
            opened.st_mtime_ns,
            opened.st_ctime_ns,
        ):
            raise ValueError(f"Phase-0 scoped file changed while hashing: {relative}")
        return payload, final
    finally:
        os.close(descriptor)


def _trusted_directory(root: Path, relative: str) -> Path:
    current = root
    for part in PurePosixPath(_safe_relative(relative, "Phase-0 directory")).parts:
        current = current / part
        try:
            metadata = os.lstat(current)
        except FileNotFoundError as exc:
            raise ValueError(f"Phase-0 scoped directory is missing: {relative}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"Phase-0 scope rejects symlink: {relative}")
        if not stat.S_ISDIR(metadata.st_mode):
            raise ValueError(f"Phase-0 scoped directory is not a directory: {relative}")
    try:
        current.resolve(strict=True).relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise ValueError(f"Phase-0 scoped directory escapes repository root: {relative}") from exc
    return current


def _assert_text(payload: bytes, relative: str) -> None:
    try:
        decoded = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Phase-0 discovered file is not UTF-8 text: {relative}") from exc
    if "\x00" in decoded:
        raise ValueError(f"Phase-0 discovered file contains NUL: {relative}")


def _discover_direct_text_files(
    root: Path,
    directory: str,
    *,
    include_name: Callable[[str], bool],
) -> tuple[str, ...]:
    base = _trusted_directory(root, directory)
    discovered: list[str] = []
    for child in sorted(base.iterdir(), key=lambda path: path.name):
        if not include_name(child.name):
            continue
        relative = child.relative_to(root).as_posix()
        payload, _ = _read_regular_file(root, relative)
        _assert_text(payload, relative)
        discovered.append(relative)
    return tuple(discovered)


def _discover_repository_scope(root: Path) -> tuple[str, ...]:
    top_level_docs = _discover_direct_text_files(
        root,
        "tournament/top40-v3",
        include_name=lambda name: name.endswith(".md") or name == "config.toml",
    )
    shared_source = _discover_direct_text_files(
        root,
        "src/crypto_trade/tournament",
        include_name=lambda name: (
            name.endswith("_v3.py") and name != "amended_orchestrator_compat_v3.py"
        ),
    )
    shared_tests = _discover_direct_text_files(
        root,
        "tests/tournament",
        include_name=lambda name: name.endswith(".py") and "v3" in name,
    )
    return (*top_level_docs, *shared_source, *shared_tests)


def canonical_scope_paths(root: str | Path | None = None) -> tuple[str, ...]:
    required = (
        *_DOC_PATHS,
        *_SHARED_V3_CODE_PATHS,
        *_SHARED_V3_TEST_PATHS,
        *_SANDBOX_CANARY_FIXTURE_PATHS,
        *_SHARED_EVALUATOR_PATHS,
        *_A6_CODE_PATHS,
        *_ROOT_AUTHORITY_PATHS,
    )
    if len(required) != len(set(required)):
        raise RuntimeError("canonical Phase-0 scope contains duplicate required paths")
    discovered: tuple[str, ...] = ()
    if root is not None:
        discovered = _discover_repository_scope(_trusted_root(root))
    paths = tuple(sorted(set((*required, *discovered))))
    if PHASE0_RECORD_PATH in paths:
        raise RuntimeError("Phase-0 record cannot freeze itself")
    return paths


def _assert_complete_v3_scope(root: Path, expected: set[str]) -> None:
    required = set(canonical_scope_paths())
    if not expected.issuperset(required):
        raise RuntimeError("internal canonical scope omits a required path")
    discovered = set(_discover_repository_scope(root))
    if not expected.issuperset(discovered):
        raise ValueError("Phase-0 repository scope changed during discovery")


def build_scope_entries(
    root: str | Path,
    paths: Iterable[str] | None = None,
) -> tuple[dict[str, object], ...]:
    """Hash an explicit scope into canonical regular-file entries and a stable chain."""

    root_path = _trusted_root(root)
    selected = canonical_scope_paths(root_path) if paths is None else tuple(paths)
    normalized = tuple(_safe_relative(path, "Phase-0 scope path") for path in selected)
    if not normalized:
        raise ValueError("Phase-0 scope cannot be empty")
    if len(normalized) != len(set(normalized)):
        raise ValueError("Phase-0 scope contains duplicate paths")
    normalized = tuple(sorted(normalized))
    if paths is None:
        _assert_complete_v3_scope(root_path, set(normalized))

    previous = GENESIS_SHA256
    entries: list[dict[str, object]] = []
    for sequence, relative in enumerate(normalized, start=1):
        payload, metadata = _read_regular_file(root_path, relative)
        body: dict[str, object] = {
            "sequence": sequence,
            "type": "regular-file",
            "path": relative,
            "size": metadata.st_size,
            "sha256": _sha256(payload),
            "previous_sha256": previous,
        }
        entry = {**body, "entry_sha256": _sha256(canonical_json_bytes(body))}
        entries.append(entry)
        previous = str(entry["entry_sha256"])
    return tuple(entries)


def _scope_index(entries: Iterable[Mapping[str, object]]) -> dict[str, Mapping[str, object]]:
    return {str(entry["path"]): entry for entry in entries}


def create_targeted_test_evidence(
    *,
    scope_head_sha256: str,
    output_bytes: bytes,
    collected: int,
) -> dict[str, object]:
    """Build a deterministic attestation for a completed, all-passing targeted test command."""

    if not _is_sha256(scope_head_sha256):
        raise ValueError("test evidence scope head must be a SHA-256")
    if not isinstance(output_bytes, bytes) or not output_bytes:
        raise ValueError("test evidence output must be nonempty bytes")
    if type(collected) is not int or collected <= 0:
        raise ValueError("test evidence collected count must be positive")
    body: dict[str, object] = {
        "schema_version": 1,
        "command": list(TARGETED_TEST_COMMAND),
        "test_files": list(REQUIRED_TARGETED_TESTS),
        "scope_head_sha256": scope_head_sha256,
        "completed": True,
        "exit_code": 0,
        "collected": collected,
        "passed": collected,
        "failed": 0,
        "skipped": 0,
        "output_size": len(output_bytes),
        "output_sha256": _sha256(output_bytes),
    }
    return {**body, "attestation_sha256": _sha256(canonical_json_bytes(body))}


def _validate_test_evidence(
    raw: object,
    *,
    scope_head_sha256: str,
    output_bytes: bytes | None,
) -> Mapping[str, Any]:
    evidence = _exact_mapping(raw, _EVIDENCE_KEYS, "targeted test evidence")
    if evidence["schema_version"] != 1:
        raise ValueError("targeted test evidence schema is invalid")
    if evidence["command"] != list(TARGETED_TEST_COMMAND):
        raise ValueError("targeted test evidence command is not canonical")
    if evidence["test_files"] != list(REQUIRED_TARGETED_TESTS):
        raise ValueError("targeted test evidence file set is not canonical")
    if evidence["scope_head_sha256"] != scope_head_sha256:
        raise ValueError("targeted test evidence is bound to a different scope")
    integer_fields = ("exit_code", "collected", "passed", "failed", "skipped", "output_size")
    if any(
        type(evidence[field]) is not int or int(evidence[field]) < 0
        for field in integer_fields
    ):
        raise ValueError("targeted test evidence counts must be nonnegative integers")
    if (
        evidence["completed"] is not True
        or evidence["exit_code"] != 0
        or evidence["collected"] <= 0
        or evidence["passed"] != evidence["collected"]
        or evidence["failed"] != 0
        or evidence["skipped"] != 0
    ):
        raise ValueError("targeted tests are not complete and all-passing")
    if not _is_sha256(evidence["output_sha256"]) or evidence["output_size"] <= 0:
        raise ValueError("targeted test output binding is invalid")
    body = {key: evidence[key] for key in _EVIDENCE_KEYS - {"attestation_sha256"}}
    expected_attestation = _sha256(canonical_json_bytes(body))
    if evidence["attestation_sha256"] != expected_attestation:
        raise ValueError("targeted test evidence attestation is invalid")
    if output_bytes is not None:
        if not isinstance(output_bytes, bytes) or (
            len(output_bytes) != evidence["output_size"]
            or _sha256(output_bytes) != evidence["output_sha256"]
        ):
            raise ValueError("targeted test output differs from its evidence")
    return evidence


def _load_a6_authority(root: Path) -> Mapping[str, Any]:
    config_bytes, _ = _read_regular_file(root, "tournament/top40-v3/config.toml")
    try:
        config = tomllib.loads(config_bytes.decode("utf-8"))
        authority = config["universe"]["a6_authority"]
    except (UnicodeDecodeError, tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        raise ValueError("V3 config lacks a valid A6 authority") from exc
    authority = _exact_mapping(authority, _A6_AUTHORITY_KEYS, "V3 config A6 authority")
    if not isinstance(authority["policy_id"], str) or not authority["policy_id"]:
        raise ValueError("V3 config A6 policy ID is invalid")
    if any(not _is_sha256(authority[key]) for key in _A6_AUTHORITY_SHA_KEYS):
        raise ValueError("V3 config A6 SHA-256 authority is invalid")
    for key, expected in _A6_AUTHORITY_PATHS.items():
        if authority[key] != expected:
            raise ValueError(f"V3 config A6 path authority differs for {key}")
    count_keys = (
        "expected_contract_metadata_symbols",
        "expected_distinct_membership_symbols",
        "expected_membership_rows",
        "expected_violations",
    )
    if any(type(authority[key]) is not int or authority[key] < 0 for key in count_keys):
        raise ValueError("V3 config A6 expected counts are invalid")
    if (
        authority["required_before_and_after_every_result_command"] is not True
        or authority["expected_audit_status"] != "passed"
        or authority["expected_violations"] != 0
    ):
        raise ValueError("V3 config does not require a zero-violation A6 pass")
    return authority


def _validate_a6_report(
    root: Path,
    report_bytes: bytes,
    scope_entries: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    if not isinstance(report_bytes, bytes) or not report_bytes:
        raise ValueError("A6 audit report must be nonempty bytes")
    report = _exact_mapping(
        _strict_json_object(report_bytes, "A6 audit report"),
        _A6_REPORT_KEYS,
        "A6 audit report",
    )
    if pretty_json_bytes(report) != report_bytes:
        raise ValueError("A6 audit report is not canonical pretty JSON")
    authority = _load_a6_authority(root)
    if (
        report["schema_version"] != 1
        or report["status"] != "passed"
        or report["violations"] != []
        or not isinstance(report["counts"], Mapping)
        or report["counts"].get("violations") != 0
    ):
        raise ValueError("A6 audit report is not an exact zero-violation pass")
    if report["policy_id"] != authority["policy_id"] or report["policy_sha256"] != authority[
        "policy_sha256"
    ]:
        raise ValueError("A6 report policy differs from config authority")
    if authority["expected_audit_status"] != "passed" or authority["expected_violations"] != 0:
        raise ValueError("V3 config does not require a zero-violation A6 pass")
    if (
        report["counts"].get("contract_metadata_symbols")
        != authority["expected_contract_metadata_symbols"]
        or report["counts"].get("membership_symbols")
        != authority["expected_distinct_membership_symbols"]
        or report["counts"].get("membership_rows") != authority["expected_membership_rows"]
    ):
        raise ValueError("A6 report counts differ from config authority")
    report_authorities = report["authorities"]
    if not isinstance(report_authorities, Mapping):
        raise ValueError("A6 report authorities are missing")
    authority_checks = {
        "data_manifest": ("data_manifest_path", "data_manifest_sha256"),
        "contract_metadata": (None, "contract_metadata_sha256"),
        "exchange_info": (None, "exchange_info_sha256"),
        "membership": (None, "membership_sha256"),
    }
    for name, (path_key, sha_key) in authority_checks.items():
        item = report_authorities.get(name)
        if not isinstance(item, Mapping) or item.get("sha256") != authority[sha_key]:
            raise ValueError(f"A6 report {name} authority differs from config")
        if path_key is not None and item.get("path") != authority[path_key]:
            raise ValueError(f"A6 report {name} path differs from config")
    report_sha256 = _sha256(report_bytes)
    if report_sha256 != authority["audit_report_sha256"]:
        raise ValueError("A6 audit report SHA-256 differs from config authority")
    scope = _scope_index(scope_entries)
    bound_paths = (
        ("audit_module_path", "audit_module_sha256"),
        ("audit_dependency_path", "audit_dependency_sha256"),
        ("data_manifest_path", "data_manifest_sha256"),
    )
    for path_key, sha_key in bound_paths:
        path = authority[path_key]
        if path not in scope or scope[path]["sha256"] != authority[sha_key]:
            raise ValueError(f"A6 scoped authority differs for {path}")
    if authority["required_before_and_after_every_result_command"] is not True:
        raise ValueError("A6 pre/post result-command enforcement is not required")
    return {
        "authority": dict(authority),
        "report": dict(report),
        "report_size": len(report_bytes),
        "report_sha256": report_sha256,
    }


def _section_entry_sha256(payload: Mapping[str, object]) -> str:
    return _sha256(canonical_json_bytes(payload))


def create_phase0_record(
    root: str | Path,
    *,
    test_evidence: Mapping[str, object],
    test_output_bytes: bytes,
    a6_report_bytes: bytes,
) -> dict[str, object]:
    """Create, but do not write, the exact deterministic Phase-0 record."""

    root_path = _trusted_root(root)
    scope_entries = build_scope_entries(root_path)
    scope_head = str(scope_entries[-1]["entry_sha256"])
    evidence = _validate_test_evidence(
        test_evidence,
        scope_head_sha256=scope_head,
        output_bytes=test_output_bytes,
    )
    evidence_payload_sha256 = _sha256(canonical_json_bytes(evidence))
    test_body: dict[str, object] = {
        "payload": dict(evidence),
        "payload_sha256": evidence_payload_sha256,
        "previous_sha256": scope_head,
    }
    test_section = {**test_body, "entry_sha256": _section_entry_sha256(test_body)}

    a6_payload = _validate_a6_report(root_path, a6_report_bytes, scope_entries)
    a6_body: dict[str, object] = {
        **a6_payload,
        "previous_sha256": test_section["entry_sha256"],
    }
    a6_section = {**a6_body, "entry_sha256": _section_entry_sha256(a6_body)}
    record_body: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "tournament_id": TOURNAMENT_ID,
        "scope_entries": list(scope_entries),
        "scope_head_sha256": scope_head,
        "targeted_tests": test_section,
        "a6_audit": a6_section,
        "chain_head_sha256": a6_section["entry_sha256"],
    }
    record = {**record_body, "record_sha256": _sha256(canonical_json_bytes(record_body))}
    verify_phase0_record(root_path, record, test_output_bytes=test_output_bytes)
    return record


def _record_mapping(raw: Mapping[str, object] | bytes) -> Mapping[str, Any]:
    if isinstance(raw, bytes):
        record = _strict_json_object(raw, "Phase-0 record")
        if pretty_json_bytes(record) != raw:
            raise ValueError("Phase-0 record bytes are not canonical pretty JSON")
        return record
    return _exact_mapping(raw, _RECORD_KEYS, "Phase-0 record")


def verify_phase0_record(
    root: str | Path,
    raw_record: Mapping[str, object] | bytes,
    *,
    test_output_bytes: bytes | None = None,
) -> Phase0Authority:
    """Recompute every scoped byte, authority, link, and record hash."""

    root_path = _trusted_root(root)
    record = _exact_mapping(_record_mapping(raw_record), _RECORD_KEYS, "Phase-0 record")
    if record["schema_version"] != SCHEMA_VERSION or record["tournament_id"] != TOURNAMENT_ID:
        raise ValueError("Phase-0 record schema or tournament binding is invalid")
    current_entries = build_scope_entries(root_path)
    raw_entries = record["scope_entries"]
    if not isinstance(raw_entries, list) or len(raw_entries) != len(current_entries):
        raise ValueError("Phase-0 scope entry count is invalid")
    for raw_entry in raw_entries:
        _exact_mapping(raw_entry, _FILE_ENTRY_KEYS, "Phase-0 file entry")
    if raw_entries != list(current_entries):
        raise ValueError("Phase-0 scoped bytes changed")
    scope_head = str(current_entries[-1]["entry_sha256"])
    if record["scope_head_sha256"] != scope_head:
        raise ValueError("Phase-0 scope head is invalid")

    test_section = _exact_mapping(
        record["targeted_tests"],
        _TEST_SECTION_KEYS,
        "Phase-0 targeted-test section",
    )
    evidence = _validate_test_evidence(
        test_section["payload"],
        scope_head_sha256=scope_head,
        output_bytes=test_output_bytes,
    )
    if test_section["payload_sha256"] != _sha256(canonical_json_bytes(evidence)):
        raise ValueError("Phase-0 targeted-test payload hash is invalid")
    test_body = {key: test_section[key] for key in _TEST_SECTION_KEYS - {"entry_sha256"}}
    if (
        test_section["previous_sha256"] != scope_head
        or test_section["entry_sha256"] != _section_entry_sha256(test_body)
    ):
        raise ValueError("Phase-0 targeted-test chain link is invalid")

    a6_section = _exact_mapping(record["a6_audit"], _A6_SECTION_KEYS, "Phase-0 A6 section")
    report_bytes = pretty_json_bytes(a6_section["report"])
    expected_a6 = _validate_a6_report(root_path, report_bytes, current_entries)
    for key in ("authority", "report", "report_size", "report_sha256"):
        if a6_section[key] != expected_a6[key]:
            raise ValueError(f"Phase-0 A6 {key} binding is invalid")
    a6_body = {key: a6_section[key] for key in _A6_SECTION_KEYS - {"entry_sha256"}}
    if (
        a6_section["previous_sha256"] != test_section["entry_sha256"]
        or a6_section["entry_sha256"] != _section_entry_sha256(a6_body)
        or record["chain_head_sha256"] != a6_section["entry_sha256"]
    ):
        raise ValueError("Phase-0 A6 chain link is invalid")
    record_body = {key: record[key] for key in _RECORD_KEYS - {"record_sha256"}}
    expected_record_sha256 = _sha256(canonical_json_bytes(record_body))
    if record["record_sha256"] != expected_record_sha256:
        raise ValueError("Phase-0 record SHA-256 is invalid")
    return Phase0Authority(
        record_sha256=expected_record_sha256,
        chain_head_sha256=str(record["chain_head_sha256"]),
        scope_head_sha256=scope_head,
        scope_file_count=len(current_entries),
    )


def write_phase0_record(
    root: str | Path,
    record: Mapping[str, object],
) -> Path:
    """Write the canonical record exactly once; an existing path is never replaced."""

    root_path = _trusted_root(root)
    verify_phase0_record(root_path, record)
    relative = _safe_relative(PHASE0_RECORD_PATH, "Phase-0 record path")
    parent_relative = PurePosixPath(relative).parent.as_posix()
    current = root_path
    for part in PurePosixPath(parent_relative).parts:
        current = current / part
        metadata = os.lstat(current)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise ValueError("Phase-0 record parent is unsafe")
    destination = root_path / relative
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(destination, flags, 0o444)
    except FileExistsError as exc:
        raise ValueError("Phase-0 record already exists and cannot be overwritten") from exc
    try:
        payload = pretty_json_bytes(record)
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short write while creating Phase-0 record")
            view = view[written:]
        os.fchmod(descriptor, 0o444)
        os.fsync(descriptor)
    except BaseException:
        os.close(descriptor)
        try:
            destination.unlink()
        except OSError:
            pass
        raise
    else:
        os.close(descriptor)
    return destination
