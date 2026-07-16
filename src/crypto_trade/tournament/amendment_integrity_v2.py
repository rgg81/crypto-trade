"""Fail-closed integrity primitives for Top-40 V2 amendment 0001.

This module contains no score or diagnostic engine.  It verifies the existing Phase-0 authority,
provides bounded UTC timestamps, publishes small multi-file transactions through a recoverable
write-ahead intent, and validates organizer-private artifacts stored under a Git administrative
path rather than in the worktree.
"""

from __future__ import annotations

import base64
import dataclasses
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.top40_v2 import LoadedV2Config, validate_run_state

UtcClock = Callable[[], datetime]

TRANSACTION_WAL_GIT_PATH = "top40-v2-amendment-0001/transaction-intent.json"
PRIVATE_ARTIFACT_GIT_PATH = "top40-v2-private/amendment-0001"
MAX_TRANSACTION_BYTES = 32 * 1024 * 1024
MAX_PRIVATE_ARTIFACT_BYTES = 16 * 1024 * 1024
MAX_PRIVATE_RESULT_BYTES = 64 * 1024 * 1024

_SHA256 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_LOGICAL_NAME = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")


@dataclasses.dataclass(frozen=True)
class Phase0Authority:
    freeze: Mapping[str, Any]
    freeze_bytes: bytes
    freeze_sha256: str
    common_commit: str
    record_commit: str
    frozen_at_utc: str
    common_commit_time_utc: str
    record_commit_time_utc: str
    manifest_path: str
    manifest_sha256: str


@dataclasses.dataclass(frozen=True)
class TransactionChange:
    path: Path
    expected: bytes | None
    replacement: bytes


@dataclasses.dataclass(frozen=True)
class PrivateArtifact:
    logical_name: str
    path: Path
    sha256: str
    size: int


def system_utc_now() -> datetime:
    return datetime.now(UTC)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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


def strict_json_object(payload: bytes, label: str) -> Mapping[str, Any]:
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


def safe_relative(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a repository-relative path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"{label} must be a safe repository-relative path")
    normalized = pure.as_posix()
    if normalized != value:
        raise ValueError(f"{label} must be canonical")
    return normalized


def parse_utc(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO-8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"{label} must be timezone-aware UTC")
    return parsed.astimezone(UTC)


def parse_git_time(value: object, label: str) -> datetime:
    """Normalize Git's offset-aware commit timestamp to UTC.

    Git preserves the committer's numeric offset, so ``%cI`` is not necessarily
    spelled with ``Z`` even though it identifies one unambiguous instant.
    """

    if not isinstance(value, str):
        raise ValueError(f"{label} must be an offset-aware Git timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be an offset-aware Git timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must be an offset-aware Git timestamp")
    return parsed.astimezone(UTC)


def utc_text(value: object, label: str) -> str:
    return parse_utc(value, label).isoformat().replace("+00:00", "Z")


def trusted_now(clock: UtcClock) -> datetime:
    value = clock()
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("trusted UTC clock returned a naive or invalid datetime")
    if value.utcoffset() != UTC.utcoffset(value):
        raise ValueError("trusted UTC clock must return UTC")
    return value.astimezone(UTC)


def bounded_event_time(
    value: object,
    label: str,
    *,
    lower_bounds: Sequence[tuple[str, object]],
    clock: UtcClock,
) -> str:
    event = parse_utc(value, label)
    for lower_label, lower_value in lower_bounds:
        if event < parse_utc(lower_value, lower_label):
            raise ValueError(f"{label} cannot precede {lower_label}")
    if event > trusted_now(clock):
        raise ValueError(f"{label} cannot be in the future")
    return event.isoformat().replace("+00:00", "Z")


def _open_directory_chain(root: Path, parts: Sequence[str]) -> tuple[int, list[int]]:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    root_fd = os.open(root, flags)
    opened = [root_fd]
    current = root_fd
    try:
        for part in parts:
            descriptor = os.open(
                part,
                flags | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=current,
            )
            opened.append(descriptor)
            current = descriptor
    except BaseException:
        for descriptor in reversed(opened):
            os.close(descriptor)
        raise
    return current, opened


def read_repo_file(
    root: Path,
    relative: object,
    label: str,
    *,
    maximum_bytes: int = MAX_TRANSACTION_BYTES,
    require_single_link: bool = False,
    required_mode: int | None = None,
    required_owner: int | None = None,
) -> tuple[str, Path, bytes, os.stat_result]:
    normalized = safe_relative(relative, label)
    parts = PurePosixPath(normalized).parts
    parent_fd, opened = _open_directory_chain(root, parts[:-1])
    descriptor: int | None = None
    try:
        descriptor = os.open(
            parts[-1],
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"{label} must be a regular file")
        if require_single_link and before.st_nlink != 1:
            raise ValueError(f"{label} must not be hard-linked")
        if required_mode is not None and stat.S_IMODE(before.st_mode) != required_mode:
            raise ValueError(f"{label} permissions must be {required_mode:o}")
        if required_owner is not None and before.st_uid != required_owner:
            raise ValueError(f"{label} must be owned by the current organizer")
        if before.st_size < 0 or before.st_size > maximum_bytes:
            raise ValueError(f"{label} exceeds its size ceiling")
        chunks: list[bytes] = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise ValueError(f"{label} changed while it was read")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise ValueError(f"{label} grew while it was read")
        after = os.fstat(descriptor)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise ValueError(f"{label} changed while it was read")
        return normalized, root / normalized, b"".join(chunks), after
    except OSError as exc:
        raise ValueError(f"{label} is missing or unsafe: {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        for item in reversed(opened):
            os.close(item)


def _git(
    root: Path,
    *arguments: str,
    text: bool = False,
) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        text=text,
    )


def git_text(root: Path, *arguments: str, label: str) -> str:
    result = _git(root, *arguments, text=True)
    if result.returncode:
        raise ValueError(f"cannot verify {label}")
    return result.stdout.strip()


def git_bytes(root: Path, *arguments: str, label: str) -> bytes:
    result = _git(root, *arguments)
    if result.returncode:
        raise ValueError(f"cannot verify {label}")
    return result.stdout


def git_commit_time(root: Path, commit: str, label: str) -> datetime:
    value = git_text(root, "show", "-s", "--format=%cI", commit, label=label)
    return parse_git_time(value, label)


def _require_ancestor(root: Path, ancestor: str, descendant: str, label: str) -> None:
    result = _git(root, "merge-base", "--is-ancestor", ancestor, descendant)
    if result.returncode:
        raise ValueError(f"{label} is not an ancestor of {descendant}")


def unique_first_add_commit(
    root: Path,
    relative: str,
    current_bytes: bytes,
    *,
    require_direct_parent: str | None = None,
) -> str:
    path = safe_relative(relative, "first-add path")
    history = git_text(
        root,
        "log",
        "--all",
        "--format=%H",
        "--",
        path,
        label=f"Git history for {path}",
    ).splitlines()
    if len(history) != 1:
        raise ValueError(f"{path} must be uniquely first-added and never modified")
    commit = history[0]
    added = git_text(
        root,
        "log",
        "--all",
        "--diff-filter=A",
        "--format=%H",
        "--",
        path,
        label=f"Git first-add for {path}",
    ).splitlines()
    if added != [commit]:
        raise ValueError(f"{path} lacks one unique first-add commit")
    committed = git_bytes(root, "show", f"{commit}:{path}", label=f"committed {path}")
    if committed != current_bytes:
        raise ValueError(f"{path} differs from its first-add commit")
    parents = git_text(
        root,
        "rev-list",
        "--parents",
        "-n",
        "1",
        commit,
        label=f"parents for {path}",
    ).split()
    if len(parents) != 2 or parents[0] != commit:
        raise ValueError(f"{path} first-add commit must have exactly one parent")
    if require_direct_parent is not None and parents[1] != require_direct_parent:
        raise ValueError(f"{path} first-add commit has the wrong direct parent")
    _require_ancestor(root, commit, "HEAD", f"{path} first-add commit")
    return commit


def require_no_git_history(root: Path, relative: str) -> None:
    path = safe_relative(relative, "future first-add path")
    result = _git(root, "log", "--all", "--format=%H", "--", path, text=True)
    if result.returncode or result.stdout.strip():
        raise ValueError(f"future first-add path already exists in Git history: {path}")


def verify_phase0_authority(
    root: str | Path,
    state_projection: Mapping[str, Any],
    config: LoadedV2Config,
    frozen_file_paths: Sequence[str],
    *,
    clock: UtcClock = system_utc_now,
) -> Phase0Authority:
    root_path = Path(root).resolve()
    validate_run_state(state_projection, config)
    branch = git_text(root_path, "branch", "--show-current", label="current branch")
    if branch != TOP40_V2_LAYOUT.branch:
        raise ValueError(f"current branch must be {TOP40_V2_LAYOUT.branch}")

    _relative, _path, freeze_bytes, _stat = read_repo_file(
        root_path,
        TOP40_V2_LAYOUT.phase0_freeze_path,
        "Phase-0 freeze",
    )
    freeze = strict_json_object(freeze_bytes, "Phase-0 freeze")
    required = {
        "schema_version",
        "frozen_at_utc",
        "branch",
        "common_freeze_commit",
        "config_sha256",
        "shared_snapshot_manifest_path",
        "shared_snapshot_manifest_sha256",
        "frozen_files",
    }
    if set(freeze) != required or freeze.get("schema_version") != 2:
        raise ValueError("Phase-0 freeze has an invalid schema")
    if pretty_json_bytes(freeze) != freeze_bytes:
        raise ValueError("Phase-0 freeze is not canonical JSON")
    if freeze["branch"] != TOP40_V2_LAYOUT.branch:
        raise ValueError("Phase-0 branch binding is invalid")
    freeze_sha = sha256_bytes(freeze_bytes)
    binding = state_projection.get("phase0")
    if not isinstance(binding, Mapping) or dict(binding) != {
        "path": TOP40_V2_LAYOUT.phase0_freeze_path,
        "sha256": freeze_sha,
    }:
        raise ValueError("schema-2 projection differs from the Phase-0 record")
    if freeze["config_sha256"] != config.sha256:
        raise ValueError("config changed after Phase 0")

    common_commit = freeze["common_freeze_commit"]
    if not isinstance(common_commit, str) or _COMMIT.fullmatch(common_commit) is None:
        raise ValueError("Phase-0 common commit is invalid")
    exists = _git(root_path, "cat-file", "-e", f"{common_commit}^{{commit}}")
    if exists.returncode:
        raise ValueError("Phase-0 common commit does not exist")

    frozen = freeze["frozen_files"]
    if not isinstance(frozen, Mapping) or set(frozen) != set(frozen_file_paths):
        raise ValueError("Phase-0 frozen-file map is incomplete or unexpected")
    for relative in frozen_file_paths:
        expected = frozen[relative]
        if not isinstance(expected, str) or _SHA256.fullmatch(expected) is None:
            raise ValueError(f"Phase-0 hash is invalid: {relative}")
        normalized, _current_path, current, _current_stat = read_repo_file(
            root_path,
            relative,
            f"Phase-0 file {relative}",
        )
        if normalized != relative or sha256_bytes(current) != expected:
            raise ValueError(f"Phase-0 frozen file changed: {relative}")
        committed = git_bytes(
            root_path,
            "show",
            f"{common_commit}:{relative}",
            label=f"Phase-0 committed file {relative}",
        )
        if sha256_bytes(committed) != expected:
            raise ValueError(f"Phase-0 file differs from common commit: {relative}")

    manifest_relative = safe_relative(
        freeze["shared_snapshot_manifest_path"],
        "Phase-0 snapshot manifest path",
    )
    _manifest_relative, _manifest_path, manifest_bytes, _manifest_stat = read_repo_file(
        root_path,
        manifest_relative,
        "shared snapshot manifest",
        maximum_bytes=MAX_TRANSACTION_BYTES,
    )
    manifest_sha = freeze["shared_snapshot_manifest_sha256"]
    if not isinstance(manifest_sha, str) or _SHA256.fullmatch(manifest_sha) is None:
        raise ValueError("Phase-0 snapshot manifest SHA-256 is invalid")
    if sha256_bytes(manifest_bytes) != manifest_sha:
        raise ValueError("shared snapshot manifest changed after Phase 0")
    manifest = strict_json_object(manifest_bytes, "shared snapshot manifest")
    if pretty_json_bytes(manifest) != manifest_bytes:
        raise ValueError("shared snapshot manifest is not canonical JSON")
    committed_manifest = git_bytes(
        root_path,
        "show",
        f"{common_commit}:{manifest_relative}",
        label="Phase-0 committed snapshot manifest",
    )
    if committed_manifest != manifest_bytes:
        raise ValueError("shared snapshot manifest differs from the common commit")

    record_commit = unique_first_add_commit(
        root_path,
        TOP40_V2_LAYOUT.phase0_freeze_path,
        freeze_bytes,
        require_direct_parent=common_commit,
    )
    _require_ancestor(root_path, common_commit, "HEAD", "Phase-0 common commit")
    common_time = git_commit_time(root_path, common_commit, "Phase-0 common commit time")
    record_time = git_commit_time(root_path, record_commit, "Phase-0 record commit time")
    frozen_time = parse_utc(freeze["frozen_at_utc"], "Phase-0 freeze time")
    state_time = parse_utc(state_projection["created_at_utc"], "run-state creation time")
    now = trusted_now(clock)
    if not state_time <= common_time <= frozen_time <= record_time <= now:
        raise ValueError("Phase-0/state/commit chronology is invalid or future-dated")
    return Phase0Authority(
        freeze=freeze,
        freeze_bytes=freeze_bytes,
        freeze_sha256=freeze_sha,
        common_commit=common_commit,
        record_commit=record_commit,
        frozen_at_utc=utc_text(frozen_time.isoformat(), "Phase-0 freeze time"),
        common_commit_time_utc=utc_text(common_time.isoformat(), "common commit time"),
        record_commit_time_utc=utc_text(record_time.isoformat(), "record commit time"),
        manifest_path=manifest_relative,
        manifest_sha256=manifest_sha,
    )


def git_path(root: str | Path, relative: str) -> Path:
    root_path = Path(root).resolve()
    normalized = safe_relative(relative, "Git administrative path")
    value = git_text(
        root_path,
        "rev-parse",
        "--path-format=absolute",
        "--git-path",
        normalized,
        label=f"Git administrative path {normalized}",
    )
    path = Path(value)
    if not path.is_absolute():
        path = root_path / path
    path = Path(os.path.abspath(path))
    git_dir = Path(
        git_text(
            root_path,
            "rev-parse",
            "--path-format=absolute",
            "--git-dir",
            label="Git directory",
        )
    ).resolve()
    resolved = path.resolve(strict=False)
    if not resolved.is_relative_to(git_dir):
        raise ValueError("Git administrative path is outside the repository Git directory")
    return path


def fsync_directory(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def ensure_owner_directory(path: Path) -> None:
    if path.exists() or path.is_symlink():
        info = os.lstat(path)
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise ValueError(f"private administrative directory is unsafe: {path}")
        if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError(f"private administrative directory must be owner-only: {path}")
        return
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    os.mkdir(path, 0o700)
    fsync_directory(parent)


def atomic_write_bytes(path: Path, payload: bytes, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if os.path.exists(temporary):
            os.unlink(temporary)


def _absolute_regular_bytes(
    path: Path,
    label: str,
    *,
    owner_only: bool = False,
) -> bytes:
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        )
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise ValueError(f"{label} is unsafe: {exc}") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_TRANSACTION_BYTES:
            raise ValueError(f"{label} is not a bounded regular file")
        if owner_only and (
            info.st_nlink != 1 or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600
        ):
            raise ValueError(f"{label} must be owner-only and not hard-linked")
        chunks: list[bytes] = []
        remaining = info.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise ValueError(f"{label} changed while read")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _intent_path(root: Path) -> Path:
    return git_path(root, TRANSACTION_WAL_GIT_PATH)


def _transaction_relative(root: Path, path: Path) -> str:
    if not path.is_absolute():
        raise ValueError("transaction change path must be absolute")
    try:
        relative_path = path.relative_to(root)
    except ValueError as exc:
        raise ValueError("transaction change escapes the worktree") from exc
    relative = safe_relative(relative_path.as_posix(), "transaction path")
    if root / relative != path:
        raise ValueError("transaction change path must be canonical")
    current = root
    for part in PurePosixPath(relative).parts[:-1]:
        current /= part
        try:
            info = os.lstat(current)
        except OSError as exc:
            raise ValueError("transaction output parent is missing or unsafe") from exc
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise ValueError("transaction output parent is missing or unsafe")
    target = root / relative
    if target.exists() or target.is_symlink():
        info = os.lstat(target)
        if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or info.st_nlink != 1:
            raise ValueError("transaction output must be a regular, single-link file")
    return relative


def _encode_change(root: Path, change: TransactionChange) -> Mapping[str, Any]:
    relative = _transaction_relative(root, change.path)
    return {
        "path": relative,
        "expected_bytes_base64": (
            None if change.expected is None else base64.b64encode(change.expected).decode("ascii")
        ),
        "replacement_bytes_base64": base64.b64encode(change.replacement).decode("ascii"),
        "expected_sha256": (None if change.expected is None else sha256_bytes(change.expected)),
        "replacement_sha256": sha256_bytes(change.replacement),
    }


def prepare_transaction_intent(
    root: str | Path,
    changes: Sequence[TransactionChange],
) -> Path:
    root_path = Path(root).resolve()
    if not changes or len({change.path for change in changes}) != len(changes):
        raise ValueError("transaction changes must be nonempty with unique paths")
    encoded = [_encode_change(root_path, change) for change in changes]
    core = {
        "schema_version": 1,
        "recovery_policy": "rollback-to-expected-v1",
        "worktree": root_path.as_posix(),
        "changes": encoded,
    }
    intent = {**core, "transaction_id": sha256_bytes(canonical_json_bytes(core))}
    payload = pretty_json_bytes(intent)
    if len(payload) > MAX_TRANSACTION_BYTES:
        raise ValueError("transaction intent exceeds its size ceiling")
    path = _intent_path(root_path)
    ensure_owner_directory(path.parent)
    if path.exists() or path.is_symlink():
        raise ValueError("an unfinished amendment transaction already exists")
    atomic_write_bytes(path, payload)
    return path


def _decode_intent(root: Path, payload: bytes) -> list[TransactionChange]:
    raw = strict_json_object(payload, "transaction intent")
    if set(raw) != {
        "schema_version",
        "recovery_policy",
        "worktree",
        "changes",
        "transaction_id",
    }:
        raise ValueError("transaction intent has invalid keys")
    if (
        raw["schema_version"] != 1
        or raw["recovery_policy"] != "rollback-to-expected-v1"
        or raw["worktree"] != root.as_posix()
    ):
        raise ValueError("transaction intent identity is invalid")
    core = {key: value for key, value in raw.items() if key != "transaction_id"}
    if raw["transaction_id"] != sha256_bytes(canonical_json_bytes(core)):
        raise ValueError("transaction intent hash is invalid")
    rows = raw["changes"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("transaction intent requires changes")
    changes: list[TransactionChange] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {
            "path",
            "expected_bytes_base64",
            "replacement_bytes_base64",
            "expected_sha256",
            "replacement_sha256",
        }:
            raise ValueError("transaction intent change is malformed")
        relative = safe_relative(row["path"], "transaction path")
        if relative in seen:
            raise ValueError("transaction intent repeats a path")
        seen.add(relative)
        try:
            expected = (
                None
                if row["expected_bytes_base64"] is None
                else base64.b64decode(row["expected_bytes_base64"], validate=True)
            )
            replacement = base64.b64decode(row["replacement_bytes_base64"], validate=True)
        except (TypeError, ValueError) as exc:
            raise ValueError("transaction intent contains invalid base64") from exc
        if (
            (expected is None and row["expected_sha256"] is not None)
            or (expected is not None and row["expected_sha256"] != sha256_bytes(expected))
            or row["replacement_sha256"] != sha256_bytes(replacement)
        ):
            raise ValueError("transaction intent change hash is invalid")
        path = root / relative
        _transaction_relative(root, path)
        changes.append(TransactionChange(path, expected, replacement))
    return changes


def recover_transaction(root: str | Path) -> bool:
    root_path = Path(root).resolve()
    intent_path = _intent_path(root_path)
    if not intent_path.exists() and not intent_path.is_symlink():
        return False
    payload = _absolute_regular_bytes(
        intent_path,
        "transaction intent",
        owner_only=True,
    )
    changes = _decode_intent(root_path, payload)
    for change in reversed(changes):
        try:
            current = _absolute_regular_bytes(change.path, "transaction output")
        except FileNotFoundError:
            current = None
        if current == change.expected:
            continue
        if current != change.replacement:
            raise ValueError(
                f"cannot recover divergent amendment transaction output: {change.path}"
            )
        if change.expected is None:
            os.unlink(change.path)
            fsync_directory(change.path.parent)
        else:
            atomic_write_bytes(change.path, change.expected)
    os.unlink(intent_path)
    fsync_directory(intent_path.parent)
    return True


def publish_transaction(
    root: str | Path,
    changes: Sequence[TransactionChange],
) -> None:
    root_path = Path(root).resolve()
    recover_transaction(root_path)
    for change in changes:
        try:
            current = _absolute_regular_bytes(change.path, "transaction input")
        except FileNotFoundError:
            current = None
        if current != change.expected:
            raise ValueError(f"transaction input changed: {change.path}")
    prepare_transaction_intent(root_path, changes)
    try:
        for change in changes:
            atomic_write_bytes(change.path, change.replacement)
    except BaseException:
        recover_transaction(root_path)
        raise
    intent_path = _intent_path(root_path)
    os.unlink(intent_path)
    fsync_directory(intent_path.parent)


def private_artifact_directory(
    root: str | Path,
    team_id: str,
    diagnostic_id: str,
    *,
    create: bool,
) -> Path:
    for value, label in ((team_id, "team_id"), (diagnostic_id, "diagnostic_id")):
        if _LOGICAL_NAME.fullmatch(value) is None:
            raise ValueError(f"{label} is not a safe private-artifact component")
    base = git_path(root, PRIVATE_ARTIFACT_GIT_PATH)
    if create:
        ensure_owner_directory(base.parent)
    elif not base.parent.is_dir() or base.parent.is_symlink():
        raise ValueError("organizer-private Git-path root is missing or unsafe")
    parent_info = os.lstat(base.parent)
    if parent_info.st_uid != os.geteuid() or stat.S_IMODE(parent_info.st_mode) != 0o700:
        raise ValueError("organizer-private Git-path root is not owner-only")
    current = base
    for part in (team_id, diagnostic_id):
        if create:
            ensure_owner_directory(current)
        elif not current.is_dir() or current.is_symlink():
            raise ValueError("organizer-private artifact directory is missing or unsafe")
        info = os.lstat(current)
        if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError("organizer-private artifact directory is not owner-only")
        current /= part
    if create:
        ensure_owner_directory(current)
    elif not current.is_dir() or current.is_symlink():
        raise ValueError("organizer-private diagnostic directory is missing or unsafe")
    info = os.lstat(current)
    if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError("organizer-private diagnostic directory is not owner-only")
    return current


def validate_private_artifacts(
    root: str | Path,
    team_id: str,
    diagnostic_id: str,
    expected_hashes: Mapping[str, str],
    required_names: Sequence[str],
) -> tuple[PrivateArtifact, ...]:
    artifacts = collect_private_artifacts(
        root,
        team_id,
        diagnostic_id,
        required_names,
    )
    if set(expected_hashes) != set(required_names):
        raise ValueError("private result must contain exactly the required logical artifacts")
    for artifact in artifacts:
        expected = expected_hashes[artifact.logical_name]
        if not isinstance(expected, str) or _SHA256.fullmatch(expected) is None:
            raise ValueError("private artifact SHA-256 is invalid")
        if artifact.sha256 != expected:
            raise ValueError(f"private artifact hash differs: {artifact.logical_name}")
    return artifacts


def collect_private_artifacts(
    root: str | Path,
    team_id: str,
    diagnostic_id: str,
    required_names: Sequence[str],
) -> tuple[PrivateArtifact, ...]:
    """Read and hash the exact owner-only diagnostic artifact set."""

    if not required_names or tuple(sorted(required_names)) != tuple(required_names):
        raise ValueError("integration must declare sorted required private artifact names")
    if len(required_names) != len(set(required_names)):
        raise ValueError("integration declares duplicate private artifact names")
    directory = private_artifact_directory(root, team_id, diagnostic_id, create=False)
    directory_fd = os.open(
        directory,
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        observed_names = set(os.listdir(directory_fd))
    finally:
        os.close(directory_fd)
    if observed_names != set(required_names):
        raise ValueError("private diagnostic directory must contain exactly required artifacts")
    artifacts: list[PrivateArtifact] = []
    total = 0
    for logical_name in required_names:
        if _LOGICAL_NAME.fullmatch(logical_name) is None:
            raise ValueError("private artifact logical name is invalid")
        relative = (directory / logical_name).relative_to(directory.parent.parent.parent)
        _normalized, path, payload, info = read_repo_file(
            directory.parent.parent.parent,
            relative.as_posix(),
            f"private artifact {logical_name}",
            maximum_bytes=MAX_PRIVATE_ARTIFACT_BYTES,
            require_single_link=True,
            required_mode=0o600,
            required_owner=os.geteuid(),
        )
        observed = sha256_bytes(payload)
        total += info.st_size
        if total > MAX_PRIVATE_RESULT_BYTES:
            raise ValueError("private diagnostic result exceeds its total size ceiling")
        artifacts.append(PrivateArtifact(logical_name, path, observed, info.st_size))
    return tuple(artifacts)


def read_private_artifact_bytes(
    root: str | Path,
    team_id: str,
    diagnostic_id: str,
    logical_name: str,
) -> bytes:
    """Read one owner-only diagnostic artifact through the same no-link boundary."""

    if _LOGICAL_NAME.fullmatch(logical_name) is None:
        raise ValueError("private artifact logical name is invalid")
    directory = private_artifact_directory(root, team_id, diagnostic_id, create=False)
    relative = (directory / logical_name).relative_to(directory.parent.parent.parent)
    _normalized, _path, payload, _info = read_repo_file(
        directory.parent.parent.parent,
        relative.as_posix(),
        f"private artifact {logical_name}",
        maximum_bytes=MAX_PRIVATE_ARTIFACT_BYTES,
        require_single_link=True,
        required_mode=0o600,
        required_owner=os.geteuid(),
    )
    return payload
