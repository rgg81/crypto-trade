"""Durable first-journal creation addendum for Top40 V3 Amendment 0002."""

from __future__ import annotations

import base64
import dataclasses
import hashlib
import json
import os
import re
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from crypto_trade.tournament import orchestrator_v3
from crypto_trade.tournament import top40_amendment_0002_validation as validation

SCHEMA_VERSION = 1
ADDENDUM_ID = "top40-v3-amendment-0002-first-journal-durability"
IMPLEMENTATION_PARENT_COMMIT = "f7d9e4913229e9626a8d710ee7a346956b720ece"
ADDENDUM_POLICY_PATH = "tournament/top40-v3/amendments/0002/DURABILITY-ADDENDUM.md"
DURABILITY_FREEZE_PATH = "tournament/top40-v3/amendments/0002/durability-freeze.json"
MODULE_PATH = "src/crypto_trade/tournament/top40_amendment_0002_durability.py"
SCRIPT_PATH = "scripts/top40_v3_amendment_0002_durability.py"
TEST_PATH = "tests/tournament/test_top40_amendment_0002_durability.py"
IMPLEMENTATION_PATHS = (MODULE_PATH, SCRIPT_PATH, TEST_PATH, ADDENDUM_POLICY_PATH)
PARENT_TEST_COMMAND = validation.AMENDMENT_TEST_COMMAND
ADDENDUM_TEST_COMMAND = (
    "env",
    "PYTHONPATH=src",
    "PYTHONDONTWRITEBYTECODE=1",
    "uv",
    "run",
    "--frozen",
    "pytest",
    "-q",
    TEST_PATH,
)
MAX_TEST_OUTPUT_BYTES = 4 * 1024 * 1024

_SHA256 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_FREEZE_KEYS = frozenset(
    {
        "schema_version",
        "addendum_id",
        "parent_activation",
        "implementation",
        "parent_tests",
        "addendum_tests",
        "record_sha256",
    }
)


class DurabilityAddendumError(orchestrator_v3.OrchestratorError):
    """The first-journal durability authority is absent or changed."""


@dataclasses.dataclass(frozen=True, slots=True)
class DurabilityAuthority:
    freeze_file_sha256: str
    freeze_commit: str
    record_sha256: str
    implementation_commit: str
    parent_activation_freeze_sha256: str


@dataclasses.dataclass(frozen=True, slots=True)
class ProvisionalDurabilityFreeze:
    freeze_file_sha256: str
    record_sha256: str
    implementation_commit: str
    activation: str = "pending-unique-freeze-commit"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(payload: object) -> bytes:
    try:
        return json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise DurabilityAddendumError("durability payload is not canonical JSON") from exc


def _pretty(payload: object) -> bytes:
    try:
        return (
            json.dumps(payload, allow_nan=False, indent=2, sort_keys=True).encode("ascii") + b"\n"
        )
    except (TypeError, ValueError) as exc:
        raise DurabilityAddendumError("durability payload is not pretty JSON") from exc


def _strict_json(payload: bytes, label: str) -> Mapping[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise DurabilityAddendumError(f"{label} contains a duplicate key")
            result[key] = value
        return result

    try:
        value = json.loads(payload.decode("ascii"), object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DurabilityAddendumError(f"{label} is not valid ASCII JSON") from exc
    if not isinstance(value, Mapping):
        raise DurabilityAddendumError(f"{label} must be an object")
    return value


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
        raise DurabilityAddendumError(f"{label} must be a full lowercase commit")
    resolved = _git(root, ["rev-parse", "--verify", f"{commit}^{{commit}}"])
    if resolved.returncode != 0 or resolved.stdout.decode("ascii", "replace").strip() != commit:
        raise DurabilityAddendumError(f"{label} is not a repository commit")
    if _git(root, ["merge-base", "--is-ancestor", commit, "HEAD"]).returncode != 0:
        raise DurabilityAddendumError(f"{label} is not in HEAD ancestry")


def _entries(root: Path) -> tuple[dict[str, object], ...]:
    entries: list[dict[str, object]] = []
    for relative in IMPLEMENTATION_PATHS:
        payload = orchestrator_v3._read_regular_bytes(root, relative)
        entries.append({"path": relative, "size": len(payload), "sha256": _sha256(payload)})
    return tuple(entries)


def _manifest(entries: Sequence[Mapping[str, object]]) -> str:
    return _sha256(_canonical([dict(entry) for entry in entries]))


def _verify_implementation(
    root: Path,
    implementation_commit: str,
    entries: Sequence[Mapping[str, object]],
) -> None:
    _verified_commit(root, implementation_commit, "implementation_commit")
    parent = _git(root, ["rev-parse", f"{implementation_commit}^"])
    if (
        parent.returncode != 0
        or parent.stdout.decode("ascii", "replace").strip() != IMPLEMENTATION_PARENT_COMMIT
    ):
        raise DurabilityAddendumError(
            "durability implementation must directly follow Amendment 0002 freeze"
        )
    delta = _git(
        root, ["diff-tree", "--no-commit-id", "--name-status", "-r", implementation_commit]
    )
    expected = sorted(f"A\t{relative}" for relative in IMPLEMENTATION_PATHS)
    if delta.returncode != 0 or sorted(delta.stdout.decode().splitlines()) != expected:
        raise DurabilityAddendumError("durability implementation commit has an unexpected delta")
    by_path = {str(entry["path"]): entry for entry in entries}
    for relative in IMPLEMENTATION_PATHS:
        additions = _git(root, ["log", "--diff-filter=A", "--format=%H", "--", relative])
        commits = [line for line in additions.stdout.decode().splitlines() if line]
        committed = _git(root, ["show", f"{implementation_commit}:{relative}"])
        expected_entry = by_path[relative]
        if (
            additions.returncode != 0
            or commits != [implementation_commit]
            or committed.returncode != 0
            or len(committed.stdout) != expected_entry["size"]
            or _sha256(committed.stdout) != expected_entry["sha256"]
        ):
            raise DurabilityAddendumError(f"durability implementation binding changed: {relative}")


def _run_tests(root: Path, command: Sequence[str], label: str) -> bytes:
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
        raise DurabilityAddendumError(f"{label} failed with exit code {completed.returncode}")
    if not isinstance(output, bytes) or not output or len(output) > MAX_TEST_OUTPUT_BYTES:
        raise DurabilityAddendumError(f"{label} output is missing or too large")
    orchestrator_v3._parse_passed_count(output)
    return output


def _evidence(command: Sequence[str], output: bytes) -> dict[str, object]:
    count = orchestrator_v3._parse_passed_count(output)
    return {
        "command": list(command),
        "collected": count,
        "passed": count,
        "output_size": len(output),
        "output_sha256": _sha256(output),
        "output_base64": base64.b64encode(output).decode("ascii"),
    }


def _verify_evidence(value: object, command: Sequence[str], label: str) -> None:
    keys = {"command", "collected", "passed", "output_size", "output_sha256", "output_base64"}
    if not isinstance(value, Mapping) or set(value) != keys:
        raise DurabilityAddendumError(f"{label} has invalid fields")
    if value["command"] != list(command) or value["passed"] != value["collected"]:
        raise DurabilityAddendumError(f"{label} command or counts changed")
    try:
        output = base64.b64decode(str(value["output_base64"]).encode(), validate=True)
    except Exception as exc:
        raise DurabilityAddendumError(f"{label} output encoding is invalid") from exc
    if (
        len(output) != value["output_size"]
        or _sha256(output) != value["output_sha256"]
        or orchestrator_v3._parse_passed_count(output) != value["collected"]
    ):
        raise DurabilityAddendumError(f"{label} output binding changed")


def freeze_durability(
    root: str | Path,
    *,
    implementation_commit: str,
) -> ProvisionalDurabilityFreeze:
    """Freeze the additive empty-journal durability transaction before it runs."""

    root_path = orchestrator_v3._trusted_root(root)
    with orchestrator_v3._result_command_lock(root_path):
        freeze_path = root_path / DURABILITY_FREEZE_PATH
        journal_path = root_path / validation.VALIDATION_JOURNAL_PATH
        private_path = root_path / validation.PRIVATE_VALIDATION_ROOT
        if freeze_path.exists() or freeze_path.is_symlink():
            raise DurabilityAddendumError("durability freeze already exists")
        if (
            journal_path.exists()
            or journal_path.is_symlink()
            or private_path.exists()
            or private_path.is_symlink()
        ):
            raise DurabilityAddendumError(
                "durability freeze requires unopened validation namespaces"
            )
        parent = validation.verify_activation(root_path)
        entries = _entries(root_path)
        _verify_implementation(root_path, implementation_commit, entries)
        parent_output = _run_tests(root_path, PARENT_TEST_COMMAND, "Amendment 0002 tests")
        addendum_output = _run_tests(root_path, ADDENDUM_TEST_COMMAND, "durability tests")
        if (
            validation.verify_activation(root_path) != parent
            or _entries(root_path) != entries
            or journal_path.exists()
            or journal_path.is_symlink()
            or private_path.exists()
            or private_path.is_symlink()
        ):
            raise DurabilityAddendumError("durability inputs changed during serial tests")
        body = {
            "schema_version": SCHEMA_VERSION,
            "addendum_id": ADDENDUM_ID,
            "parent_activation": dataclasses.asdict(parent),
            "implementation": {
                "commit": implementation_commit,
                "files": list(entries),
                "manifest_sha256": _manifest(entries),
            },
            "parent_tests": _evidence(PARENT_TEST_COMMAND, parent_output),
            "addendum_tests": _evidence(ADDENDUM_TEST_COMMAND, addendum_output),
        }
        record = {**body, "record_sha256": _sha256(_canonical(body))}
        orchestrator_v3._write_new_file(
            root_path,
            DURABILITY_FREEZE_PATH,
            _pretty(record),
            mode=0o444,
        )
        payload = orchestrator_v3._read_regular_bytes(root_path, DURABILITY_FREEZE_PATH)
        return ProvisionalDurabilityFreeze(
            freeze_file_sha256=_sha256(payload),
            record_sha256=str(record["record_sha256"]),
            implementation_commit=implementation_commit,
        )


def _verify_freeze_commit(root: Path, implementation_commit: str, payload: bytes) -> str:
    additions = _git(root, ["log", "--diff-filter=A", "--format=%H", "--", DURABILITY_FREEZE_PATH])
    commits = [line for line in additions.stdout.decode().splitlines() if line]
    if additions.returncode != 0 or len(commits) != 1:
        raise DurabilityAddendumError("durability freeze requires one unique commit")
    commit = commits[0]
    _verified_commit(root, commit, "durability freeze commit")
    parent = _git(root, ["rev-parse", f"{commit}^"])
    delta = _git(root, ["diff-tree", "--no-commit-id", "--name-status", "-r", commit])
    committed = _git(root, ["show", f"{commit}:{DURABILITY_FREEZE_PATH}"])
    if (
        parent.returncode != 0
        or parent.stdout.decode().strip() != implementation_commit
        or delta.returncode != 0
        or delta.stdout.decode().splitlines() != [f"A\t{DURABILITY_FREEZE_PATH}"]
        or committed.returncode != 0
        or committed.stdout != payload
    ):
        raise DurabilityAddendumError("durability freeze commit binding is invalid")
    return commit


def verify_durability(root: str | Path = ".") -> DurabilityAuthority:
    root_path = orchestrator_v3._trusted_root(root)
    payload = orchestrator_v3._read_regular_bytes(root_path, DURABILITY_FREEZE_PATH)
    record = _strict_json(payload, "durability freeze")
    if _pretty(record) != payload or set(record) != _FREEZE_KEYS:
        raise DurabilityAddendumError("durability freeze encoding or fields changed")
    body = {key: record[key] for key in _FREEZE_KEYS - {"record_sha256"}}
    if (
        record["schema_version"] != SCHEMA_VERSION
        or record["addendum_id"] != ADDENDUM_ID
        or record["record_sha256"] != _sha256(_canonical(body))
    ):
        raise DurabilityAddendumError("durability freeze identity is invalid")
    parent = validation.verify_activation(root_path)
    if record["parent_activation"] != dataclasses.asdict(parent):
        raise DurabilityAddendumError("parent validation activation changed")
    implementation = record["implementation"]
    if not isinstance(implementation, Mapping):
        raise DurabilityAddendumError("durability implementation is malformed")
    entries = _entries(root_path)
    if implementation.get("files") != list(entries) or implementation.get(
        "manifest_sha256"
    ) != _manifest(entries):
        raise DurabilityAddendumError("durability implementation bytes changed")
    implementation_commit = str(implementation.get("commit"))
    _verify_implementation(root_path, implementation_commit, entries)
    _verify_evidence(record["parent_tests"], PARENT_TEST_COMMAND, "parent tests")
    _verify_evidence(record["addendum_tests"], ADDENDUM_TEST_COMMAND, "addendum tests")
    freeze_commit = _verify_freeze_commit(root_path, implementation_commit, payload)
    return DurabilityAuthority(
        freeze_file_sha256=_sha256(payload),
        freeze_commit=freeze_commit,
        record_sha256=str(record["record_sha256"]),
        implementation_commit=implementation_commit,
        parent_activation_freeze_sha256=parent.freeze_file_sha256,
    )


_VERIFY_DURABILITY = verify_durability


def initialize_journal(root: str | Path = ".") -> dict[str, object]:
    """Durably create the empty validation journal and fsync its parent directory."""

    root_path = orchestrator_v3._trusted_root(root)
    with orchestrator_v3._result_command_lock(root_path):
        authority = _VERIFY_DURABILITY(root_path)
        journal_path = root_path / validation.VALIDATION_JOURNAL_PATH
        private_path = root_path / validation.PRIVATE_VALIDATION_ROOT
        if private_path.exists() or private_path.is_symlink():
            raise DurabilityAddendumError(
                "private validation output exists before journal initialization"
            )
        if journal_path.exists() or journal_path.is_symlink():
            payload = orchestrator_v3._read_regular_bytes(
                root_path, validation.VALIDATION_JOURNAL_PATH
            )
            if payload != b"":
                raise DurabilityAddendumError("validation journal is already nonempty")
            created = False
        else:
            orchestrator_v3._write_new_file(
                root_path,
                validation.VALIDATION_JOURNAL_PATH,
                b"",
                mode=0o600,
            )
            created = True
        payload = orchestrator_v3._read_regular_bytes(root_path, validation.VALIDATION_JOURNAL_PATH)
        if payload != b"" or validation.replay_validation_journal_bytes(payload).records:
            raise DurabilityAddendumError("initialized validation journal is not canonically empty")
        metadata = os.lstat(journal_path)
        if not stat_is_regular(metadata.st_mode) or stat_mode(metadata.st_mode) != 0o600:
            raise DurabilityAddendumError("initialized validation journal mode is unsafe")
        return {
            "addendum_id": ADDENDUM_ID,
            "command": "initialize-journal",
            "durability_freeze_sha256": authority.freeze_file_sha256,
            "journal_created": created,
            "journal_head_sha256": validation.GENESIS_SHA256,
            "ok": True,
        }


def stat_is_regular(mode: int) -> bool:
    return (mode & 0o170000) == 0o100000


def stat_mode(mode: int) -> int:
    return mode & 0o777


def validate(root: str | Path = ".") -> dict[str, object]:
    root_path = orchestrator_v3._trusted_root(root)
    with orchestrator_v3._result_command_lock(root_path):
        authority = _VERIFY_DURABILITY(root_path)
        path = root_path / validation.VALIDATION_JOURNAL_PATH
        initialized = path.exists() and not path.is_symlink()
        if initialized:
            validation._read_validation_journal(root_path)
        return {
            "addendum_id": ADDENDUM_ID,
            "command": "validate",
            "durability_freeze_commit": authority.freeze_commit,
            "durability_freeze_sha256": authority.freeze_file_sha256,
            "journal_initialized": initialized,
            "ok": True,
        }


__all__ = [
    "ADDENDUM_ID",
    "ADDENDUM_TEST_COMMAND",
    "DURABILITY_FREEZE_PATH",
    "DurabilityAddendumError",
    "DurabilityAuthority",
    "IMPLEMENTATION_PATHS",
    "ProvisionalDurabilityFreeze",
    "freeze_durability",
    "initialize_journal",
    "validate",
    "verify_durability",
]
