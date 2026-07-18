"""Fail-closed organizer entrypoint for the activated Top-40 V3 train laboratory.

Only policy validation, the one-time Phase-0 freeze, status projection, and transparent train
laboratories are reachable here.  Sealed validation, private, and final stages have no command or
public function in this module.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import fcntl
import hashlib
import json
import os
import re
import resource
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from crypto_trade.tournament import (
    coaching_v3,
    journal_v3,
    phase0_v3,
    pure_crypto_universe_v6,
    runner_v3,
    source_archive_v3,
    top40_v3,
)
from crypto_trade.tournament.qualification_v3 import CandidateIdentity

CONFIG_PATH = "tournament/top40-v3/config.toml"
PHASE0_TEST_OUTPUT_PATH = "tournament/top40-v3/phase0-targeted-tests.out"
RUN_STATE_PATH = "tournament/top40-v3/run_state.json"
LAB_JOURNAL_PATH = "tournament/top40-v3/organizer-lab-journal.jsonl"
RESULT_COMMAND_LOCK_PATH = "tournament/top40-v3/.result-command.lock"
DIAGNOSTIC_RUBRIC_PATH = "tournament/top40-v3/DIAGNOSTIC-RUBRIC.md"
DEPENDENCY_LOCK_PATH = "uv.lock"
DATA_MANIFEST_PATH = "tournament/top40/data_manifest.json"
CLI_PATH = "scripts/top40_v3_tournament.py"

_ACTIVE_POLICY_STATUS = "active"
_ACTIVE_ENTRYPOINT = CLI_PATH
_SCHEDULE_AUTHORITY = (
    "tournament/top40-v3/phase0-freeze.json#config-splits-labs-seeds"
)
_REQUIRED_ACTIVATION = {
    "run_evaluators_now": True,
    "requires_independent_implementation_review": True,
    "requires_hash_frozen_metric_schema": True,
    "requires_hash_frozen_diagnostic_rubric": True,
    "requires_hash_frozen_schedule_and_seeds": True,
    "requires_v3_only_active_entrypoint": True,
}
_JOURNAL_BINDING_FIELDS = frozenset(
    journal_v3._REQUEST_KEYS | journal_v3._TERMINAL_KEYS
)
_STATE_LOCK_PATHS = {
    "infrastructure": phase0_v3.PHASE0_RECORD_PATH,
    "schedule": CONFIG_PATH,
    "metric_schema": CONFIG_PATH,
    "diagnostic_rubric": DIAGNOSTIC_RUBRIC_PATH,
}
_SAFE_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_PYTEST_SUMMARY = re.compile(
    r"^(?P<passed>[1-9][0-9]*) passed"
    r"(?P<extra>(?:, [^\r\n]+)?) in [0-9]+(?:\.[0-9]+)?s$"
)
_FORBIDDEN_TEST_OUTCOMES = re.compile(
    r"(?:^|[^a-z])(failed|error|errors|skipped|xfailed|xpassed|deselected)(?:[^a-z]|$)",
    re.IGNORECASE,
)


class OrchestratorError(RuntimeError):
    """A concise, expected organizer-command refusal."""


class ResultCommandBusyError(OrchestratorError):
    """Another result-bearing organizer command owns the global lock."""


@dataclasses.dataclass(frozen=True, slots=True)
class CandidateAuthority:
    team_id: str
    entrypoint: str
    candidate_id: str
    parent_candidate_id: str | None
    purpose: str
    material_parameters: Mapping[str, Any]
    seed: int
    candidate_config_path: str
    risk_policy_path: str
    candidate_config_sha256: str
    tournament_config_sha256: str
    source_bundle_sha256: str
    source_archive_path: str
    source_archive_sha256: str
    strategy_sha256: str
    dependency_lock_sha256: str
    risk_policy_sha256: str
    data_authority_sha256: str
    evaluator_sha256: str
    pure_crypto_report_sha256: str


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _pretty_json_bytes(payload: object) -> bytes:
    try:
        return (
            json.dumps(payload, allow_nan=False, indent=2, sort_keys=True).encode("utf-8")
            + b"\n"
        )
    except (TypeError, ValueError) as exc:
        raise OrchestratorError("organizer payload is not finite canonical JSON") from exc


def _canonical_json_bytes(payload: object) -> bytes:
    try:
        return json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise OrchestratorError("organizer payload is not finite canonical JSON") from exc


def _strict_json_object(payload: bytes, label: str) -> Mapping[str, Any]:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise OrchestratorError(f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise OrchestratorError(f"{label} contains nonfinite number {value}")

    try:
        parsed = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OrchestratorError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(parsed, Mapping):
        raise OrchestratorError(f"{label} must be a JSON object")
    return parsed


def _safe_relative(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise OrchestratorError(f"{label} must be a nonempty POSIX relative path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise OrchestratorError(f"{label} is unsafe")
    return value


def _trusted_root(root: str | Path) -> Path:
    candidate = Path(root)
    if candidate.is_symlink():
        raise OrchestratorError("repository root cannot be a symlink")
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise OrchestratorError("repository root does not exist") from exc
    if not resolved.is_dir():
        raise OrchestratorError("repository root is not a directory")
    return resolved


def _path(root: Path, relative: str) -> Path:
    return root.joinpath(*PurePosixPath(_safe_relative(relative, "repository path")).parts)


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _read_regular_bytes(root: Path, relative: str) -> bytes:
    relative = _safe_relative(relative, "file path")
    current = root
    metadata: os.stat_result | None = None
    parts = PurePosixPath(relative).parts
    for index, part in enumerate(parts):
        current /= part
        try:
            metadata = os.lstat(current)
        except FileNotFoundError as exc:
            raise OrchestratorError(f"required file is missing: {relative}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise OrchestratorError(f"symlink is forbidden: {relative}")
        if index < len(parts) - 1 and not stat.S_ISDIR(metadata.st_mode):
            raise OrchestratorError(f"file parent is not a directory: {relative}")
    if metadata is None or not stat.S_ISREG(metadata.st_mode):
        raise OrchestratorError(f"required path is not a regular file: {relative}")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(current, flags)
    except OSError as exc:
        raise OrchestratorError(f"cannot safely open required file: {relative}") from exc
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
            raise OrchestratorError(f"file changed while opening: {relative}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        payload = b"".join(chunks)
        final = os.fstat(descriptor)
        if (
            final.st_size != len(payload)
            or final.st_mtime_ns != opened.st_mtime_ns
            or final.st_ctime_ns != opened.st_ctime_ns
        ):
            raise OrchestratorError(f"file changed while reading: {relative}")
        return payload
    finally:
        os.close(descriptor)


def _ensure_directory(root: Path, relative: str) -> Path:
    current = root
    for part in PurePosixPath(_safe_relative(relative, "directory path")).parts:
        parent = current
        current /= part
        try:
            metadata = os.lstat(current)
        except FileNotFoundError:
            os.mkdir(current, 0o700)
            _fsync_directory(parent)
            metadata = os.lstat(current)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise OrchestratorError(f"unsafe organizer directory: {relative}")
    return current


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_new_file(root: Path, relative: str, payload: bytes, *, mode: int) -> Path:
    relative = _safe_relative(relative, "new file path")
    destination = _path(root, relative)
    parent_relative = PurePosixPath(relative).parent.as_posix()
    parent = _ensure_directory(root, parent_relative)
    if _lexists(destination):
        raise OrchestratorError(f"refusing to overwrite existing file: {relative}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = -1
    created = False
    try:
        descriptor = os.open(destination, flags, mode)
        created = True
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short organizer file write")
            view = view[written:]
        os.fchmod(descriptor, mode)
        os.fsync(descriptor)
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
            descriptor = -1
        if created:
            with contextlib.suppress(OSError):
                destination.unlink()
        raise
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    _fsync_directory(parent)
    return destination


def _created_identity(path: Path) -> tuple[Path, int, int]:
    metadata = os.lstat(path)
    if not stat.S_ISREG(metadata.st_mode):
        raise OrchestratorError(f"new organizer authority is not regular: {path.name}")
    return path, metadata.st_dev, metadata.st_ino


def _rollback_created(created: list[tuple[Path, int, int]]) -> tuple[str, ...]:
    failures: list[str] = []
    for path, device, inode in reversed(created):
        try:
            metadata = os.lstat(path)
            if (
                stat.S_ISREG(metadata.st_mode)
                and (metadata.st_dev, metadata.st_ino) == (device, inode)
            ):
                path.unlink()
                _fsync_directory(path.parent)
        except FileNotFoundError:
            continue
        except OSError as exc:
            failures.append(f"{path.name}: {exc}")
    return tuple(failures)


def _atomic_projection(root: Path, relative: str, payload: bytes) -> None:
    relative = _safe_relative(relative, "projection path")
    destination = _path(root, relative)
    parent = _ensure_directory(root, PurePosixPath(relative).parent.as_posix())
    if _lexists(destination):
        metadata = os.lstat(destination)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise OrchestratorError(f"projection path is unsafe: {relative}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb", buffering=0) as handle:
            handle.write(payload)
            handle.flush()
            os.fchmod(handle.fileno(), 0o600)
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        _fsync_directory(parent)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()


@contextlib.contextmanager
def _result_command_lock(root: Path) -> Iterator[None]:
    path = _path(root, RESULT_COMMAND_LOCK_PATH)
    _ensure_directory(root, PurePosixPath(RESULT_COMMAND_LOCK_PATH).parent.as_posix())
    if _lexists(path):
        metadata = os.lstat(path)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise OrchestratorError("global result-command lock path is unsafe")
    flags = os.O_RDWR | os.O_CREAT
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise OrchestratorError("global result-command lock is not a regular file")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ResultCommandBusyError("another organizer result command is running") from exc
        current = os.lstat(path)
        if (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino):
            raise OrchestratorError("global result-command lock changed while acquiring it")
        yield
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _load_active_config(root: Path) -> top40_v3.LoadedV3Config:
    config = top40_v3.load_config(_path(root, CONFIG_PATH))
    raw = config.raw
    lifecycle = raw.get("lifecycle")
    activation = raw.get("activation")
    if raw.get("policy_status") != _ACTIVE_POLICY_STATUS:
        raise OrchestratorError("V3 policy is not activated")
    if not isinstance(lifecycle, Mapping) or (
        lifecycle.get("active_entrypoint") != _ACTIVE_ENTRYPOINT
        or lifecycle.get("schedule_authority") != _SCHEDULE_AUTHORITY
    ):
        raise OrchestratorError("V3 lifecycle activation authority is invalid")
    if not isinstance(activation, Mapping) or dict(activation) != _REQUIRED_ACTIVATION:
        raise OrchestratorError("V3 activation flags are incomplete or unexpected")
    journal_bindings = raw.get("labs", {}).get("required_journal_bindings", {})
    binding_fields = (
        journal_bindings.get("fields") if isinstance(journal_bindings, Mapping) else None
    )
    if (
        not isinstance(journal_bindings, Mapping)
        or not isinstance(binding_fields, list)
        or len(binding_fields) != len(set(binding_fields))
        or frozenset(binding_fields) != _JOURNAL_BINDING_FIELDS
    ):
        raise OrchestratorError("V3 journal binding field list differs from journal_v3")
    return config


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _phase0_authority(root: Path) -> phase0_v3.Phase0Authority:
    record = _read_regular_bytes(root, phase0_v3.PHASE0_RECORD_PATH)
    test_output = _read_regular_bytes(root, PHASE0_TEST_OUTPUT_PATH)
    try:
        return phase0_v3.verify_phase0_record(
            root,
            record,
            test_output_bytes=test_output,
        )
    except (TypeError, ValueError) as exc:
        raise OrchestratorError(f"Phase-0 verification failed: {exc}") from exc


def _parse_passed_count(output: bytes) -> int:
    try:
        lines = output.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise OrchestratorError("targeted test output is not UTF-8") from exc
    matches = [match for line in lines if (match := _PYTEST_SUMMARY.fullmatch(line.strip()))]
    if len(matches) != 1:
        raise OrchestratorError("targeted test output lacks one exact passing summary")
    extra = matches[0].group("extra")
    if extra and _FORBIDDEN_TEST_OUTCOMES.search(extra):
        raise OrchestratorError("targeted test output contains a non-passing outcome")
    return int(matches[0].group("passed"))


def _run_targeted_tests(root: Path) -> tuple[int, bytes]:
    completed = subprocess.run(
        list(phase0_v3.TARGETED_TEST_COMMAND),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode != 0:
        raise OrchestratorError(
            f"Phase-0 targeted tests failed with exit code {completed.returncode}"
        )
    if not isinstance(completed.stdout, bytes) or not completed.stdout:
        raise OrchestratorError("Phase-0 targeted tests produced no captured bytes")
    return _parse_passed_count(completed.stdout), completed.stdout


def _state_lock(
    root: Path,
    name: str,
    locked_at_utc: str,
    *,
    sha256_override: str | None = None,
) -> dict[str, str]:
    relative = _STATE_LOCK_PATHS[name]
    return {
        "path": relative,
        "sha256": sha256_override or _sha256(_read_regular_bytes(root, relative)),
        "locked_at_utc": locked_at_utc,
    }


def _project_state(
    root: Path,
    config: top40_v3.LoadedV3Config,
    journal: journal_v3.JournalState,
    *,
    created_at_utc: str,
    lock_hash_overrides: Mapping[str, str] | None = None,
) -> dict[str, object]:
    state = top40_v3.new_run_state(config, created_at_utc=created_at_utc)
    state["phase"] = "lab_open"
    locks = state["locks"]
    if not isinstance(locks, dict):  # pragma: no cover - new_run_state contract
        raise OrchestratorError("fresh V3 lock projection is malformed")
    for name in _STATE_LOCK_PATHS:
        override = None if lock_hash_overrides is None else lock_hash_overrides.get(name)
        locks[name] = _state_lock(
            root,
            name,
            created_at_utc,
            sha256_override=override,
        )
    teams = state["teams"]
    if not isinstance(teams, dict):  # pragma: no cover - new_run_state contract
        raise OrchestratorError("fresh V3 team projection is malformed")
    for team_id in top40_v3.TEAM_IDS:
        team = teams[team_id]
        team["lab_run_count"] = int(journal.team_run_sequences.get(team_id, 0))
        team["material_trial_count"] = int(journal.material_trial_counts.get(team_id, 0))
    top40_v3.validate_run_state(state, config)
    return state


def _read_state(root: Path, config: top40_v3.LoadedV3Config) -> Mapping[str, Any] | None:
    path = _path(root, RUN_STATE_PATH)
    if not _lexists(path):
        return None
    payload = _read_regular_bytes(root, RUN_STATE_PATH)
    state = _strict_json_object(payload, "V3 run state")
    if _pretty_json_bytes(state) != payload:
        raise OrchestratorError("V3 run state is not canonical pretty JSON")
    try:
        top40_v3.validate_run_state(state, config)
    except ValueError as exc:
        raise OrchestratorError(f"V3 run state is invalid: {exc}") from exc
    if state["phase"] != "lab_open":
        raise OrchestratorError("organizer train commands require lab_open state")
    return state


def _reconcile_state(
    root: Path,
    config: top40_v3.LoadedV3Config,
    journal: journal_v3.JournalState,
    *,
    default_created_at_utc: str | None = None,
) -> dict[str, object]:
    existing = _read_state(root, config)
    created = (
        str(existing["created_at_utc"])
        if existing is not None
        else (default_created_at_utc or _utc_now())
    )
    projected = _project_state(root, config, journal, created_at_utc=created)
    payload = _pretty_json_bytes(projected)
    if existing is None or _pretty_json_bytes(existing) != payload:
        _atomic_projection(root, RUN_STATE_PATH, payload)
    return projected


def _read_journal(root: Path) -> journal_v3.JournalState:
    try:
        return journal_v3.replay_journal(_path(root, LAB_JOURNAL_PATH))
    except (OSError, journal_v3.JournalValidationError) as exc:
        raise OrchestratorError(f"organizer lab journal is invalid: {exc}") from exc


def _cleanup_uncommitted_phase0_prefix(
    root: Path,
    config: top40_v3.LoadedV3Config,
) -> None:
    companions = (PHASE0_TEST_OUTPUT_PATH, LAB_JOURNAL_PATH, RUN_STATE_PATH)
    present = tuple(relative for relative in companions if _lexists(_path(root, relative)))
    if not present:
        return
    valid_prefixes = tuple(
        companions[:length] for length in range(1, len(companions) + 1)
    )
    if present not in valid_prefixes:
        raise OrchestratorError(
            f"non-prefix uncommitted Phase-0 files require review: {list(present)}"
        )
    output = _read_regular_bytes(root, PHASE0_TEST_OUTPUT_PATH)
    passed = _parse_passed_count(output)
    if (
        LAB_JOURNAL_PATH in present
        and _read_regular_bytes(root, LAB_JOURNAL_PATH) != b""
    ):
        raise OrchestratorError("uncommitted Phase-0 journal is not empty")
    if RUN_STATE_PATH in present:
        state_bytes = _read_regular_bytes(root, RUN_STATE_PATH)
        state = _strict_json_object(state_bytes, "uncommitted Phase-0 run state")
        if _pretty_json_bytes(state) != state_bytes:
            raise OrchestratorError("uncommitted Phase-0 run state is not canonical")
        try:
            top40_v3.validate_run_state(state, config)
        except ValueError as exc:
            raise OrchestratorError(
                f"uncommitted Phase-0 run state is invalid: {exc}"
            ) from exc
        if state["phase"] != "lab_open":
            raise OrchestratorError("uncommitted Phase-0 state is not lab_open")
        teams = state["teams"]
        if any(
            teams[team_id]["lab_run_count"] != 0
            or teams[team_id]["material_trial_count"] != 0
            for team_id in top40_v3.TEAM_IDS
        ):
            raise OrchestratorError("uncommitted Phase-0 state contains train counters")

        entries = phase0_v3.build_scope_entries(root)
        evidence = phase0_v3.create_targeted_test_evidence(
            scope_head_sha256=str(entries[-1]["entry_sha256"]),
            output_bytes=output,
            collected=passed,
        )
        report_bytes = pure_crypto_universe_v6.audit_report_bytes(root)
        record = phase0_v3.create_phase0_record(
            root,
            test_evidence=evidence,
            test_output_bytes=output,
            a6_report_bytes=report_bytes,
        )
        expected_record_file_sha256 = _sha256(phase0_v3.pretty_json_bytes(record))
        expected_state = _project_state(
            root,
            config,
            journal_v3.replay_journal_bytes(b""),
            created_at_utc=str(state["created_at_utc"]),
            lock_hash_overrides={"infrastructure": expected_record_file_sha256},
        )
        if state != expected_state:
            raise OrchestratorError(
                "uncommitted Phase-0 state does not match its reserved authority"
            )
    identities = [_created_identity(_path(root, relative)) for relative in present]
    failures = _rollback_created(identities)
    if failures:
        raise OrchestratorError(
            f"could not clean verified uncommitted Phase-0 prefix: {list(failures)}"
        )


def phase0_freeze(root: str | Path = ".") -> dict[str, object]:
    """Execute exact targeted tests and create the V3 authority files once."""

    root_path = _trusted_root(root)
    with _result_command_lock(root_path):
        config = _load_active_config(root_path)
        if not _lexists(_path(root_path, phase0_v3.PHASE0_RECORD_PATH)):
            _cleanup_uncommitted_phase0_prefix(root_path, config)
        fresh_paths = (
            phase0_v3.PHASE0_RECORD_PATH,
            PHASE0_TEST_OUTPUT_PATH,
            RUN_STATE_PATH,
            LAB_JOURNAL_PATH,
        )
        existing = [relative for relative in fresh_paths if _lexists(_path(root_path, relative))]
        if existing:
            raise OrchestratorError(f"Phase-0 requires clean absent authority paths: {existing}")

        before = phase0_v3.build_scope_entries(root_path)
        passed, output = _run_targeted_tests(root_path)
        after = phase0_v3.build_scope_entries(root_path)
        if after != before:
            raise OrchestratorError("Phase-0 scope changed while targeted tests ran")

        report_bytes = pure_crypto_universe_v6.audit_report_bytes(root_path)
        scope_head = str(before[-1]["entry_sha256"])
        evidence = phase0_v3.create_targeted_test_evidence(
            scope_head_sha256=scope_head,
            output_bytes=output,
            collected=passed,
        )
        record = phase0_v3.create_phase0_record(
            root_path,
            test_evidence=evidence,
            test_output_bytes=output,
            a6_report_bytes=report_bytes,
        )
        record_file_sha256 = _sha256(phase0_v3.pretty_json_bytes(record))

        created_files: list[tuple[Path, int, int]] = []
        try:
            output_path = _write_new_file(
                root_path,
                PHASE0_TEST_OUTPUT_PATH,
                output,
                mode=0o444,
            )
            created_files.append(_created_identity(output_path))
            journal_path = _write_new_file(root_path, LAB_JOURNAL_PATH, b"", mode=0o600)
            created_files.append(_created_identity(journal_path))
            empty_journal = journal_v3.replay_journal_bytes(b"")
            created = _utc_now()
            state = _project_state(
                root_path,
                config,
                empty_journal,
                created_at_utc=created,
                lock_hash_overrides={"infrastructure": record_file_sha256},
            )
            state_path = _write_new_file(
                root_path,
                RUN_STATE_PATH,
                _pretty_json_bytes(state),
                mode=0o600,
            )
            created_files.append(_created_identity(state_path))
            record_path = phase0_v3.write_phase0_record(root_path, record)
            created_files.append(_created_identity(record_path))
            if _sha256(_read_regular_bytes(root_path, phase0_v3.PHASE0_RECORD_PATH)) != (
                record_file_sha256
            ):
                raise OrchestratorError("published Phase-0 commit marker hash disagrees")
            _fsync_directory(record_path.parent)
        except BaseException as exc:
            rollback_failures = _rollback_created(created_files)
            if rollback_failures:
                raise OrchestratorError(
                    f"{_failure_reason(exc)}; rollback incomplete: {list(rollback_failures)}"
                ) from exc
            if isinstance(exc, OrchestratorError):
                raise
            raise OrchestratorError(f"Phase-0 authority transaction failed: {exc}") from exc
        return {
            "command": "phase0-freeze",
            "ok": True,
            "passed": passed,
            "phase": "lab_open",
            "record_sha256": record["record_sha256"],
            "scope_file_count": len(before),
        }


def validate(root: str | Path = ".") -> dict[str, object]:
    """Validate activation and any existing Phase-0 authorities without writing state."""

    root_path = _trusted_root(root)
    with _result_command_lock(root_path):
        config = _load_active_config(root_path)
        if not _lexists(_path(root_path, phase0_v3.PHASE0_RECORD_PATH)):
            return {
                "activation": "valid",
                "command": "validate",
                "config_sha256": config.sha256,
                "ok": True,
                "phase0_frozen": False,
            }
        authority = _phase0_authority(root_path)
        journal = _read_journal(root_path)
        state = _read_state(root_path, config)
        if state is None:
            raise OrchestratorError("Phase-0 exists but run_state.json is missing")
        return {
            "activation": "valid",
            "command": "validate",
            "config_sha256": config.sha256,
            "journal_head_sha256": journal.head_sha256,
            "ok": True,
            "phase": state["phase"],
            "phase0_frozen": True,
            "phase0_record_sha256": authority.record_sha256,
        }


def status(root: str | Path = ".") -> dict[str, object]:
    """Return nondisclosing status and repair a stale state projection from the journal."""

    root_path = _trusted_root(root)
    with _result_command_lock(root_path):
        config = _load_active_config(root_path)
        if not _lexists(_path(root_path, phase0_v3.PHASE0_RECORD_PATH)):
            unexpected = [
                relative
                for relative in (PHASE0_TEST_OUTPUT_PATH, RUN_STATE_PATH, LAB_JOURNAL_PATH)
                if _lexists(_path(root_path, relative))
            ]
            if unexpected:
                raise OrchestratorError(
                    f"pre-Phase0 repository contains unexpected authority files: {unexpected}"
                )
            return {
                "command": "status",
                "ok": True,
                "phase": "policy_defined",
                "phase0_frozen": False,
            }
        authority = _phase0_authority(root_path)
        journal = _read_journal(root_path)
        state = _reconcile_state(root_path, config, journal)
        counts = {
            team_id: {
                "lab_run_count": state["teams"][team_id]["lab_run_count"],
                "material_trial_count": state["teams"][team_id][
                    "material_trial_count"
                ],
            }
            for team_id in top40_v3.TEAM_IDS
        }
        return {
            "command": "status",
            "journal_head_sha256": journal.head_sha256,
            "ok": True,
            "pending_request_count": len(journal.pending_request_sha256s),
            "phase": state["phase"],
            "phase0_frozen": True,
            "phase0_record_sha256": authority.record_sha256,
            "teams": counts,
        }


def _safe_purpose(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 512 or value != value.strip():
        raise OrchestratorError("train purpose must be a nonempty bounded string")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise OrchestratorError("train purpose contains a control character")
    return value


def _safe_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or _SAFE_IDENTIFIER.fullmatch(value) is None:
        raise OrchestratorError(f"{label} is not a safe journal identifier")
    return value


def _derive_candidate_authority(
    root: Path,
    config: top40_v3.LoadedV3Config,
    team_id: str,
    entrypoint: str,
    purpose: str,
) -> CandidateAuthority:
    if team_id not in top40_v3.TEAM_IDS:
        raise OrchestratorError("team_id must be team-01 through team-10")
    entrypoint = _safe_relative(entrypoint, "team entrypoint")
    prefix = f"tournament/top40-v3/teams/{team_id}/"
    if not entrypoint.startswith(prefix) or not entrypoint.endswith(".py"):
        raise OrchestratorError(f"entrypoint must be an exact Python path below {prefix}")
    strategy_bytes = _read_regular_bytes(root, entrypoint)
    candidate_root = PurePosixPath(entrypoint).parent
    candidate_config_path = (candidate_root / "frozen_config.json").as_posix()
    risk_policy_path = (candidate_root / "risk_policy.json").as_posix()
    candidate_config_bytes = _read_regular_bytes(root, candidate_config_path)
    risk_policy_bytes = _read_regular_bytes(root, risk_policy_path)
    candidate = _strict_json_object(candidate_config_bytes, "candidate frozen_config.json")
    implementation = candidate.get("implementation")
    risk = candidate.get("risk_policy")
    parameters = candidate.get("parameters")
    if candidate.get("schema_version") != 1 or candidate.get("team_id") != team_id:
        raise OrchestratorError("candidate config identity does not match the selected team")
    if not isinstance(implementation, Mapping) or implementation.get("entrypoint") != Path(
        entrypoint
    ).name:
        raise OrchestratorError("candidate config entrypoint does not match the selected file")
    if not isinstance(risk, Mapping) or risk.get("path") != "risk_policy.json":
        raise OrchestratorError("candidate config does not bind its adjacent risk_policy.json")
    candidate_id = _safe_identifier(candidate.get("candidate_id"), "candidate_id")
    if not isinstance(parameters, Mapping):
        raise OrchestratorError("candidate config parameters must be an object")
    seed = candidate.get("seed")
    expected_seed = int(config.raw["labs"]["strategy_seed"])
    if type(seed) is not int or seed != expected_seed:
        raise OrchestratorError("candidate seed differs from the frozen tournament seed")
    parent: str | None = None
    parent_authorities = [
        (name, candidate.get(name))
        for name in ("v3_parent", "v2_parent")
        if candidate.get(name) is not None
    ]
    if len(parent_authorities) > 1:
        raise OrchestratorError("candidate config cannot declare both v3_parent and v2_parent")
    if parent_authorities:
        _parent_name, parent_authority = parent_authorities[0]
        if not isinstance(parent_authority, Mapping):
            raise OrchestratorError("candidate parent authority is malformed")
        parent = _safe_identifier(
            parent_authority.get("candidate_id"), "parent_candidate_id"
        )
        if parent == candidate_id:
            raise OrchestratorError("candidate_id cannot equal its parent_candidate_id")

    tournament_config_bytes = _read_regular_bytes(root, CONFIG_PATH)
    if _sha256(tournament_config_bytes) != config.sha256:
        raise OrchestratorError("loaded tournament config changed while deriving authority")
    manifest_bytes = _read_regular_bytes(root, DATA_MANIFEST_PATH)
    manifest_sha256 = _sha256(manifest_bytes)
    a6_authority = config.raw["universe"]["a6_authority"]
    if manifest_sha256 != a6_authority["data_manifest_sha256"]:
        raise OrchestratorError("data manifest differs from the configured A6 authority")
    try:
        source_capture = runner_v3.capture_source_bundle(
            root,
            team_id,
            entrypoint,
        )
        captured_by_path = {item.path: item for item in source_capture.files}
        expected_local_hashes = {
            Path(entrypoint).name: _sha256(strategy_bytes),
            "frozen_config.json": _sha256(candidate_config_bytes),
            "risk_policy.json": _sha256(risk_policy_bytes),
        }
        if any(
            name not in captured_by_path
            or captured_by_path[name].sha256 != expected_digest
            for name, expected_digest in expected_local_hashes.items()
        ):
            raise OrchestratorError(
                "candidate config, risk, or strategy changed before source archive creation"
            )
        source_archive = source_archive_v3.write_source_archive(
            root,
            team_id=team_id,
            candidate_id=candidate_id,
            candidate_root=source_capture.candidate_root,
            entrypoint=source_capture.entrypoint,
            source_bundle_sha256=source_capture.sha256,
            files=source_capture.files,
        )
        if runner_v3.capture_source_bundle(root, team_id, entrypoint) != source_capture:
            raise OrchestratorError("candidate tree changed while creating its source archive")
        evaluator_sha256 = runner_v3._evaluator_authority_sha256(root)
    except (OSError, TypeError, ValueError, runner_v3.StrategySandboxError) as exc:
        raise OrchestratorError(f"candidate authority derivation failed: {exc}") from exc
    return CandidateAuthority(
        team_id=team_id,
        entrypoint=entrypoint,
        candidate_id=candidate_id,
        parent_candidate_id=parent,
        purpose=_safe_purpose(purpose),
        material_parameters=dict(parameters),
        seed=seed,
        candidate_config_path=candidate_config_path,
        risk_policy_path=risk_policy_path,
        candidate_config_sha256=_sha256(candidate_config_bytes),
        tournament_config_sha256=config.sha256,
        source_bundle_sha256=source_capture.sha256,
        source_archive_path=source_archive.path,
        source_archive_sha256=source_archive.sha256,
        strategy_sha256=_sha256(strategy_bytes),
        dependency_lock_sha256=_sha256(_read_regular_bytes(root, DEPENDENCY_LOCK_PATH)),
        risk_policy_sha256=_sha256(risk_policy_bytes),
        data_authority_sha256=manifest_sha256,
        evaluator_sha256=evaluator_sha256,
        pure_crypto_report_sha256=str(a6_authority["audit_report_sha256"]),
    )


def _journal_timestamp(state: journal_v3.JournalState) -> str:
    current = _utc_now()
    if not state.records:
        return current
    last = state.records[-1]
    field = "accepted_at_utc" if last["event_type"] == "request_accepted" else "completed_at_utc"
    previous = str(last[field])
    return previous if current < previous else current


def _run_id(team_id: str, run_sequence: int, source_bundle_sha256: str) -> str:
    compact_team = team_id.replace("-", "")
    return f"v3-{compact_team}-lab-{run_sequence:06d}-{source_bundle_sha256[:12]}"


def _cpu_seconds() -> float:
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return float(own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime)


def _failure_reason(error: BaseException) -> str:
    text = f"{type(error).__name__}: {error}"
    cleaned = "".join(
        " " if ord(character) < 32 or ord(character) == 127 else character
        for character in text
    )
    cleaned = " ".join(cleaned.split())
    return (cleaned or "organizer train command failed")[:2048]


def _run_trusted_train(root: Path, authority: CandidateAuthority, output_path: str) -> Any:
    return runner_v3.run_team(
        root,
        authority.team_id,
        authority.entrypoint,
        CONFIG_PATH,
        DATA_MANIFEST_PATH,
        stage="train",
        _authorization=runner_v3._ORGANIZER_RUN_AUTHORIZATION,
        _output_relative=output_path,
        _candidate_id=authority.candidate_id,
        _source_archive_relative=authority.source_archive_path,
        _source_archive_sha256=authority.source_archive_sha256,
    )


def _gate_vector(result: Any) -> dict[str, bool]:
    scored_window = getattr(result, "scored_window")
    metrics = getattr(scored_window, "metrics")
    return {
        "train_annualized_return_positive": float(metrics.annualized_return) > 0.0,
        "train_double_cost_sharpe_positive": float(result.double_cost_sharpe) > 0.0,
        "train_net_sharpe_positive": float(metrics.net_sharpe) > 0.0,
        "train_window_complete": True,
    }


def _candidate_identity(authority: CandidateAuthority) -> CandidateIdentity:
    return CandidateIdentity(
        team_id=authority.team_id,
        candidate_id=authority.candidate_id,
        source_bundle_sha256=authority.source_bundle_sha256,
        strategy_sha256=authority.strategy_sha256,
        dependency_lock_sha256=authority.dependency_lock_sha256,
        config_sha256=authority.tournament_config_sha256,
        risk_policy_sha256=authority.risk_policy_sha256,
        data_authority_sha256=authority.data_authority_sha256,
        evaluator_sha256=authority.evaluator_sha256,
    )


def _validate_runner_result(
    root: Path,
    authority: CandidateAuthority,
    output_path: str,
    result: Any,
) -> tuple[dict[str, Any], dict[str, str]]:
    exact_fields = {
        "stage": "train",
        "team_id": authority.team_id,
        "entrypoint": authority.entrypoint,
        "seed": authority.seed,
        "data_manifest_sha256": authority.data_authority_sha256,
        "config_sha256": authority.tournament_config_sha256,
        "strategy_sha256": authority.strategy_sha256,
        "risk_policy_sha256": authority.risk_policy_sha256,
        "source_bundle_sha256": authority.source_bundle_sha256,
        "dependency_lock_sha256": authority.dependency_lock_sha256,
        "evaluator_sha256": authority.evaluator_sha256,
        "pure_crypto_report_sha256": authority.pure_crypto_report_sha256,
        "output_dir": output_path,
    }
    for field, expected in exact_fields.items():
        if getattr(result, field, None) != expected:
            raise OrchestratorError(f"runner result differs from request authority: {field}")
    artifacts = getattr(result, "artifacts", None)
    artifact_sha256 = getattr(result, "artifact_sha256", None)
    artifact_sizes = getattr(result, "artifact_sizes", None)
    if (
        not isinstance(artifacts, Mapping)
        or not artifacts
        or not isinstance(artifact_sha256, Mapping)
        or not isinstance(artifact_sizes, Mapping)
        or set(artifacts) != set(artifact_sha256)
        or set(artifacts) != set(artifact_sizes)
    ):
        raise OrchestratorError("runner artifact bindings are incomplete")
    terminal_artifacts: dict[str, str] = {}
    for name in sorted(artifacts):
        relative = _safe_relative(artifacts[name], f"runner artifact {name}")
        if not relative.startswith(output_path + "/"):
            raise OrchestratorError("runner artifact escaped its unique output directory")
        payload = _read_regular_bytes(root, relative)
        digest = _sha256(payload)
        if digest != artifact_sha256[name] or len(payload) != artifact_sizes[name]:
            raise OrchestratorError(f"runner artifact binding changed: {name}")
        terminal_artifacts[relative] = digest
    organizer_fields = getattr(result, "organizer_fields", None)
    if not callable(organizer_fields):
        raise OrchestratorError("runner result lacks its canonical organizer projection")
    fields = organizer_fields()
    if not isinstance(fields, Mapping):
        raise OrchestratorError("runner organizer projection is not an object")
    _canonical_json_bytes(fields)
    return dict(fields), terminal_artifacts


def _collect_output_artifacts(root: Path, output_path: str) -> dict[str, str]:
    directory = _path(root, output_path)
    if not _lexists(directory):
        return {}
    metadata = os.lstat(directory)
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise OrchestratorError("request output path is unsafe during failure accounting")
    artifacts: dict[str, str] = {}
    for path in sorted(directory.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        item = os.lstat(path)
        if stat.S_ISLNK(item.st_mode):
            raise OrchestratorError(f"orphan output contains symlink: {relative}")
        if stat.S_ISDIR(item.st_mode):
            continue
        if not stat.S_ISREG(item.st_mode):
            raise OrchestratorError(f"orphan output contains nonregular path: {relative}")
        artifacts[relative] = _sha256(_read_regular_bytes(root, relative))
    return artifacts


def _append_terminal(
    root: Path,
    *,
    event_type: str,
    request: Mapping[str, Any],
    completed_at_utc: str,
    cpu_seconds: float,
    wall_seconds: float,
    gate_vector: Mapping[str, bool],
    metric_packet_sha256: str | None,
    artifact_hashes: Mapping[str, str],
    failure_reason: str | None,
) -> journal_v3.JournalState:
    try:
        return journal_v3.append_terminal_event(
            _path(root, LAB_JOURNAL_PATH),
            event_type=event_type,
            team_id=str(request["team_id"]),
            run_sequence=int(request["run_sequence"]),
            run_id=str(request["run_id"]),
            candidate_id=str(request["candidate_id"]),
            request_sha256=str(request["record_sha256"]),
            completed_at_utc=completed_at_utc,
            cpu_seconds=cpu_seconds,
            wall_seconds=wall_seconds,
            gate_vector=gate_vector,
            metric_packet_sha256=metric_packet_sha256,
            artifact_hashes=artifact_hashes,
            cumulative_material_trial_count=int(
                request["cumulative_material_trial_count"]
            ),
            failure_reason=failure_reason,
        )
    except (OSError, journal_v3.JournalValidationError) as exc:
        raise OrchestratorError(f"cannot durably append terminal accounting: {exc}") from exc


def _recover_pending_request(
    root: Path,
    config: top40_v3.LoadedV3Config,
    state: journal_v3.JournalState,
) -> journal_v3.JournalState:
    if not state.pending_request_sha256s:
        return state
    if len(state.pending_request_sha256s) != 1:
        raise OrchestratorError("journal contains more than one pending request")
    request_sha256 = state.pending_request_sha256s[0]
    request = next(
        (
            record
            for record in state.records
            if record["event_type"] == "request_accepted"
            and record["record_sha256"] == request_sha256
        ),
        None,
    )
    if request is None:  # pragma: no cover - replay_journal proves this invariant
        raise OrchestratorError("pending journal request has no accepted record")
    archive_error: BaseException | None = None
    try:
        source_archive_v3.read_source_archive(
            root,
            str(request["source_archive_path"]),
            str(request["source_archive_sha256"]),
            expected_team_id=str(request["team_id"]),
            expected_candidate_id=str(request["candidate_id"]),
            expected_source_bundle_sha256=str(request["source_bundle_sha256"]),
        )
    except BaseException as exc:
        archive_error = exc
    output_path = str(request["output_path"])
    accounting_error: BaseException | None = None
    try:
        recovered_artifacts = _collect_output_artifacts(root, output_path)
    except BaseException as exc:
        recovered_artifacts = {}
        accounting_error = exc
    metric_path = f"{output_path}/metric_packet.json"
    recovered_metric_sha256 = recovered_artifacts.get(metric_path)
    reason = (
        "organizer restart recovery: accepted request had no terminal event; "
        "cpu_seconds and wall_seconds are unavailable and recorded as zero; "
        "its run_id and output path remain reserved for audit"
    )
    if accounting_error is not None:
        reason = (
            reason
            + "; orphan artifact accounting error: "
            + _failure_reason(accounting_error)
        )[:2048]
    if archive_error is not None:
        reason = (
            reason
            + "; immutable source archive verification error: "
            + _failure_reason(archive_error)
        )[:2048]
    recovered = _append_terminal(
        root,
        event_type="aborted",
        request=request,
        completed_at_utc=_journal_timestamp(state),
        cpu_seconds=0.0,
        wall_seconds=0.0,
        gate_vector={},
        metric_packet_sha256=recovered_metric_sha256,
        artifact_hashes=recovered_artifacts,
        failure_reason=reason,
    )
    _reconcile_state(root, config, recovered)
    return recovered


def train(
    root: str | Path,
    team_id: str,
    entrypoint: str,
    *,
    purpose: str = "organizer train laboratory evaluation",
) -> dict[str, object]:
    """Run one transparent train laboratory with journal-before-run accounting."""

    root_path = _trusted_root(root)
    with _result_command_lock(root_path):
        config = _load_active_config(root_path)
        phase0_authority = _phase0_authority(root_path)
        journal = _read_journal(root_path)
        state = _reconcile_state(root_path, config, journal)
        if state["phase"] != "lab_open":
            raise OrchestratorError("train requires the lab_open phase")
        journal = _recover_pending_request(root_path, config, journal)

        candidate = _derive_candidate_authority(
            root_path,
            config,
            team_id,
            entrypoint,
            purpose,
        )
        # Reverify after candidate traversal so no request can follow unnoticed Phase-0 drift.
        if _phase0_authority(root_path) != phase0_authority:
            raise OrchestratorError("Phase-0 authority changed while accepting train inputs")
        run_sequence = int(journal.team_run_sequences.get(team_id, 0)) + 1
        trial_count = int(journal.material_trial_counts.get(team_id, 0)) + 1
        run_id = _run_id(team_id, run_sequence, candidate.source_bundle_sha256)
        output_path = f"reports-top40-v3/labs/{team_id}/{run_id}"
        if _lexists(_path(root_path, output_path)):
            raise OrchestratorError("unique train output path already exists")
        accepted_at = _journal_timestamp(journal)
        try:
            request_state = journal_v3.append_request_accepted(
                _path(root_path, LAB_JOURNAL_PATH),
                team_id=team_id,
                run_sequence=run_sequence,
                run_id=run_id,
                candidate_id=candidate.candidate_id,
                parent_candidate_id=candidate.parent_candidate_id,
                purpose=candidate.purpose,
                accepted_at_utc=accepted_at,
                source_bundle_sha256=candidate.source_bundle_sha256,
                source_archive_path=candidate.source_archive_path,
                source_archive_sha256=candidate.source_archive_sha256,
                strategy_sha256=candidate.strategy_sha256,
                dependency_lock_sha256=candidate.dependency_lock_sha256,
                config_sha256=candidate.tournament_config_sha256,
                risk_policy_sha256=candidate.risk_policy_sha256,
                data_authority_sha256=candidate.data_authority_sha256,
                evaluator_sha256=candidate.evaluator_sha256,
                seed=candidate.seed,
                material_parameters=candidate.material_parameters,
                train_window=dict(journal_v3.FROZEN_TRAIN_WINDOW),
                cost_model=dict(journal_v3.FROZEN_COST_MODEL),
                output_path=output_path,
                cumulative_material_trial_count=trial_count,
            )
        except (OSError, journal_v3.JournalValidationError) as exc:
            raise OrchestratorError(f"cannot durably append accepted request: {exc}") from exc
        request = request_state.records[-1]
        start_wall = time.monotonic()
        start_cpu = _cpu_seconds()
        terminal_written = False
        packet: dict[str, Any] | None = None
        terminal_state: journal_v3.JournalState | None = None
        failure_artifacts: dict[str, str] = {}
        try:
            _reconcile_state(root_path, config, request_state)
            result = _run_trusted_train(root_path, candidate, output_path)
            failure_artifacts = _collect_output_artifacts(root_path, output_path)
            if _derive_candidate_authority(
                root_path,
                config,
                team_id,
                entrypoint,
                purpose,
            ) != candidate:
                raise OrchestratorError("candidate inputs changed during the train run")
            if _phase0_authority(root_path) != phase0_authority:
                raise OrchestratorError("Phase-0 authority changed during the train run")
            result_fields, terminal_artifacts = _validate_runner_result(
                root_path,
                candidate,
                output_path,
                result,
            )
            gates = _gate_vector(result)
            identity = _candidate_identity(candidate)
            try:
                packet = coaching_v3.build_training_metric_packet(result_fields, identity)
                packet_bytes = coaching_v3.canonical_packet_bytes(packet)
                packet_sha256 = coaching_v3.packet_sha256(packet)
            except (TypeError, ValueError) as exc:
                raise OrchestratorError(f"training coaching packet is invalid: {exc}") from exc
            if _sha256(packet_bytes) != packet_sha256:
                raise OrchestratorError("training coaching packet hash authority disagrees")
            metric_path = f"{output_path}/metric_packet.json"
            _write_new_file(root_path, metric_path, packet_bytes, mode=0o444)
            terminal_artifacts[metric_path] = packet_sha256
            terminal_state = _append_terminal(
                root_path,
                event_type="succeeded",
                request=request,
                completed_at_utc=_journal_timestamp(request_state),
                cpu_seconds=max(0.0, _cpu_seconds() - start_cpu),
                wall_seconds=max(0.0, time.monotonic() - start_wall),
                gate_vector=gates,
                metric_packet_sha256=packet_sha256,
                artifact_hashes=terminal_artifacts,
                failure_reason=None,
            )
            terminal_written = True
            _reconcile_state(root_path, config, terminal_state)
        except BaseException as error:
            if not terminal_written:
                accounting_error: BaseException | None = None
                try:
                    failure_artifacts = _collect_output_artifacts(root_path, output_path)
                except BaseException as exc:
                    accounting_error = exc
                event_type = (
                    "aborted"
                    if isinstance(error, (KeyboardInterrupt, SystemExit))
                    else "failed"
                )
                reason = _failure_reason(error)
                if accounting_error is not None:
                    reason = (
                        reason
                        + "; orphan artifact accounting error: "
                        + _failure_reason(accounting_error)
                    )[:2048]
                failure_state = _append_terminal(
                    root_path,
                    event_type=event_type,
                    request=request,
                    completed_at_utc=_journal_timestamp(request_state),
                    cpu_seconds=max(0.0, _cpu_seconds() - start_cpu),
                    wall_seconds=max(0.0, time.monotonic() - start_wall),
                    gate_vector={},
                    metric_packet_sha256=None,
                    artifact_hashes=failure_artifacts,
                    failure_reason=reason,
                )
                terminal_written = True
                with contextlib.suppress(Exception):
                    _reconcile_state(root_path, config, failure_state)
            if isinstance(error, OrchestratorError):
                raise
            raise OrchestratorError(_failure_reason(error)) from error
        if packet is None or terminal_state is None:  # pragma: no cover - defensive invariant
            raise OrchestratorError("successful train transaction lacks terminal disclosure")
        terminal = terminal_state.records[-1]
        return {
            "command": "train",
            "journal_terminal_sha256": terminal["record_sha256"],
            "metric_packet": packet,
            "ok": True,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Top-40 V3 organizer train-lab controls")
    parser.add_argument("--root", default=".", help="repository root")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="validate activation and frozen authorities")
    commands.add_parser("phase0-freeze", help="run targeted tests and freeze Phase 0 once")
    commands.add_parser("status", help="show nondisclosing journal-derived status")
    train_parser = commands.add_parser("train", help="run one transparent train laboratory")
    train_parser.add_argument("team_id")
    train_parser.add_argument("entrypoint")
    train_parser.add_argument(
        "--purpose",
        default="organizer train laboratory evaluation",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        if arguments.command == "validate":
            result = validate(arguments.root)
        elif arguments.command == "phase0-freeze":
            result = phase0_freeze(arguments.root)
        elif arguments.command == "status":
            result = status(arguments.root)
        elif arguments.command == "train":
            result = train(
                arguments.root,
                arguments.team_id,
                arguments.entrypoint,
                purpose=arguments.purpose,
            )
        else:  # pragma: no cover - argparse enforces the closed command set
            raise OrchestratorError("unknown organizer command")
    except (OrchestratorError, OSError, TypeError, ValueError) as exc:
        error = {"error": _failure_reason(exc), "ok": False}
        sys.stderr.buffer.write(_canonical_json_bytes(error) + b"\n")
        return 2
    sys.stdout.buffer.write(_canonical_json_bytes(result) + b"\n")
    return 0


__all__ = [
    "LAB_JOURNAL_PATH",
    "PHASE0_TEST_OUTPUT_PATH",
    "RESULT_COMMAND_LOCK_PATH",
    "RUN_STATE_PATH",
    "OrchestratorError",
    "ResultCommandBusyError",
    "build_parser",
    "main",
    "phase0_freeze",
    "status",
    "train",
    "validate",
]
