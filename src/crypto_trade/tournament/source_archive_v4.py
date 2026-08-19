"""Canonical, content-addressed source archives for Top40 V4 candidates.

The archive is organizer-owned evidence.  It contains every UTF-8 file which contributes to the
candidate source-bundle fingerprint, including non-executable research notes and tests.  A worker
still executes a staged copy, but the runner must prove that the live candidate boundary and the
staged boundary have the exact file manifest recorded here before it may launch that worker.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
import stat
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from crypto_trade.tournament.layout_v4 import TOP40_V4_LAYOUT

_SCHEMA_PREFIX = (
    TOP40_V4_LAYOUT.name if TOP40_V4_LAYOUT.name.endswith("-r2") else "top40-v4-r1"
)
SCHEMA_VERSION = f"{_SCHEMA_PREFIX}-candidate-source-archive-v1"
ARCHIVE_NAMESPACE = f"{TOP40_V4_LAYOUT.reports_root}/source-archives/sha256"
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024

_SHA256 = re.compile(r"[0-9a-f]{64}")
_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_ARCHIVE_KEYS = frozenset(
    {
        "schema_version",
        "team_id",
        "candidate_id",
        "candidate_root",
        "entrypoint",
        "source_bundle_sha256",
        "files",
    }
)
_FILE_KEYS = frozenset({"path", "size", "sha256", "content_base64"})


class SourceArchiveError(ValueError):
    """The candidate archive is unsafe, noncanonical, or inconsistent."""


@dataclass(frozen=True, slots=True)
class SourceFile:
    path: str
    size: int
    sha256: str
    content: bytes

    @property
    def manifest_entry(self) -> dict[str, object]:
        return {"path": self.path, "size": self.size, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class SourceArchive:
    path: str
    sha256: str
    team_id: str
    candidate_id: str
    candidate_root: str
    entrypoint: str
    source_bundle_sha256: str
    files: tuple[SourceFile, ...]

    @property
    def manifest_entries(self) -> tuple[dict[str, object], ...]:
        return tuple(item.manifest_entry for item in self.files)


def canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise SourceArchiveError("source archive is not canonical JSON") from exc


def bundle_fingerprint(entries: Iterable[Mapping[str, object]]) -> str:
    """Return the V4 source-bundle digest for a stable ordered file manifest."""

    normalized = [
        {
            "path": entry["path"],
            "size": entry["size"],
            "sha256": entry["sha256"],
        }
        for entry in entries
    ]
    encoded = json.dumps(normalized, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def archive_relative_path(archive_sha256: str) -> str:
    _require_hash(archive_sha256, "source_archive_sha256")
    return f"{ARCHIVE_NAMESPACE}/{archive_sha256}.json"


def _require_hash(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise SourceArchiveError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise SourceArchiveError(f"{label} must use the lowercase V4 identifier grammar")
    return value


def _relative_path(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise SourceArchiveError(f"{label} must be a nonempty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise SourceArchiveError(f"{label} must be a normalized POSIX relative path")
    if path.as_posix() != value:
        raise SourceArchiveError(f"{label} must be a normalized POSIX relative path")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SourceArchiveError(f"duplicate source archive key: {key}")
        result[key] = value
    return result


def _decode_archive(payload: bytes, *, relative_path: str, sha256: str) -> SourceArchive:
    if len(payload) > MAX_ARCHIVE_BYTES:
        raise SourceArchiveError("source archive exceeds 16 MiB")
    if not payload.endswith(b"\n") or payload == b"\n":
        raise SourceArchiveError("source archive must be one newline-terminated JSON object")
    raw = payload[:-1]
    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceArchiveError("source archive is not valid canonical JSON") from exc
    if not isinstance(value, dict) or set(value) != _ARCHIVE_KEYS:
        raise SourceArchiveError("source archive has missing or unknown fields")
    if canonical_json_bytes(value) != raw:
        raise SourceArchiveError("source archive JSON encoding is not canonical")
    if value["schema_version"] != SCHEMA_VERSION:
        raise SourceArchiveError("source archive schema_version is not V4")
    team_id = value["team_id"]
    if not isinstance(team_id, str) or team_id not in TOP40_V4_LAYOUT.team_ids:
        raise SourceArchiveError("source archive team_id is invalid")
    candidate_id = _require_identifier(value["candidate_id"], "candidate_id")
    candidate_root = _relative_path(value["candidate_root"], "candidate_root")
    required_prefix = f"{TOP40_V4_LAYOUT.tournament_root}/teams/{team_id}"
    if candidate_root != required_prefix and not candidate_root.startswith(required_prefix + "/"):
        raise SourceArchiveError("candidate_root is outside its V4 team namespace")
    entrypoint = _relative_path(value["entrypoint"], "entrypoint")
    if len(PurePosixPath(entrypoint).parts) != 1 or not entrypoint.endswith(".py"):
        raise SourceArchiveError("entrypoint must be a Python file directly in candidate_root")
    source_bundle_sha256 = _require_hash(value["source_bundle_sha256"], "source_bundle_sha256")
    raw_files = value["files"]
    if not isinstance(raw_files, list) or not raw_files:
        raise SourceArchiveError("source archive files must be a nonempty list")
    files: list[SourceFile] = []
    previous = ""
    for raw_file in raw_files:
        if not isinstance(raw_file, dict) or set(raw_file) != _FILE_KEYS:
            raise SourceArchiveError("source archive file has missing or unknown fields")
        path = _relative_path(raw_file["path"], "source file path")
        if path <= previous:
            raise SourceArchiveError("source archive files must be unique and path-sorted")
        previous = path
        size = raw_file["size"]
        if type(size) is not int or size < 0:
            raise SourceArchiveError("source archive file size must be a nonnegative integer")
        digest = _require_hash(raw_file["sha256"], f"source file {path} sha256")
        encoded = raw_file["content_base64"]
        if not isinstance(encoded, str):
            raise SourceArchiveError("source archive content_base64 must be a string")
        try:
            content = base64.b64decode(encoded.encode("ascii"), validate=True)
        except (UnicodeEncodeError, binascii.Error) as exc:
            raise SourceArchiveError(
                f"source archive file is not canonical base64: {path}"
            ) from exc
        if base64.b64encode(content).decode("ascii") != encoded:
            raise SourceArchiveError(f"source archive file base64 is not canonical: {path}")
        if len(content) != size or hashlib.sha256(content).hexdigest() != digest:
            raise SourceArchiveError(f"source archive file bytes differ from metadata: {path}")
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SourceArchiveError(f"source archive file is not UTF-8: {path}") from exc
        files.append(SourceFile(path=path, size=size, sha256=digest, content=content))
    if entrypoint not in {item.path for item in files}:
        raise SourceArchiveError("source archive does not contain its selected entrypoint")
    if bundle_fingerprint(item.manifest_entry for item in files) != source_bundle_sha256:
        raise SourceArchiveError("source archive does not match source_bundle_sha256")
    computed_sha256 = hashlib.sha256(payload).hexdigest()
    if computed_sha256 != sha256:
        raise SourceArchiveError("source archive bytes differ from source_archive_sha256")
    if archive_relative_path(sha256) != relative_path:
        raise SourceArchiveError("source archive path is not content-addressed by its bytes")
    return SourceArchive(
        path=relative_path,
        sha256=sha256,
        team_id=team_id,
        candidate_id=candidate_id,
        candidate_root=candidate_root,
        entrypoint=entrypoint,
        source_bundle_sha256=source_bundle_sha256,
        files=tuple(files),
    )


def build_archive_bytes(
    *,
    team_id: str,
    candidate_id: str,
    candidate_root: str,
    entrypoint: str,
    source_bundle_sha256: str,
    files: Iterable[SourceFile],
) -> bytes:
    """Build and self-validate the only accepted archive byte representation."""

    source_files = tuple(files)
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "team_id": team_id,
        "candidate_id": candidate_id,
        "candidate_root": candidate_root,
        "entrypoint": entrypoint,
        "source_bundle_sha256": source_bundle_sha256,
        "files": [
            {
                "path": item.path,
                "size": item.size,
                "sha256": item.sha256,
                "content_base64": base64.b64encode(item.content).decode("ascii"),
            }
            for item in source_files
        ],
    }
    encoded = canonical_json_bytes(payload) + b"\n"
    digest = hashlib.sha256(encoded).hexdigest()
    _decode_archive(encoded, relative_path=archive_relative_path(digest), sha256=digest)
    return encoded


def _stable_read(path: Path) -> bytes:
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise SourceArchiveError(f"cannot open source archive: {exc}") from exc
    try:
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise SourceArchiveError("source archive path must be a regular file")
            if before.st_size > MAX_ARCHIVE_BYTES:
                raise SourceArchiveError("source archive exceeds 16 MiB")
            payload = handle.read(MAX_ARCHIVE_BYTES + 1)
            after = os.fstat(handle.fileno())
        path_after = path.lstat()
    except OSError as exc:
        raise SourceArchiveError(f"cannot read source archive: {exc}") from exc
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    path_identity = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
    )
    if (
        identity_before != identity_after
        or identity_after != path_identity
        or not stat.S_ISREG(after.st_mode)
        or stat.S_ISLNK(path_after.st_mode)
    ):
        raise SourceArchiveError("source archive changed while being read")
    if len(payload) > MAX_ARCHIVE_BYTES:
        raise SourceArchiveError("source archive exceeds 16 MiB")
    return payload


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _resolved_archive_path(
    root: Path,
    relative_path: str,
    *,
    create_parent: bool = False,
) -> Path:
    relative = _relative_path(relative_path, "source_archive_path")
    if not relative.startswith(ARCHIVE_NAMESPACE + "/"):
        raise SourceArchiveError("source_archive_path is outside the V4 archive namespace")
    pure = PurePosixPath(relative)
    current = root
    for part in pure.parts[:-1]:
        child = current / part
        try:
            metadata = os.lstat(child)
        except FileNotFoundError:
            if not create_parent:
                raise SourceArchiveError("source archive parent is missing") from None
            try:
                os.mkdir(child, 0o700)
                _fsync_directory(current)
            except OSError as exc:
                raise SourceArchiveError(f"cannot create source archive directory: {exc}") from exc
            metadata = os.lstat(child)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise SourceArchiveError("source archive parent contains a symlink or non-directory")
        current = child
    try:
        current.resolve(strict=True).relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise SourceArchiveError("source_archive_path escapes the tournament root") from exc
    return current / pure.name


def read_source_archive(
    root: str | Path,
    relative_path: str,
    archive_sha256: str,
    *,
    expected_team_id: str | None = None,
    expected_candidate_id: str | None = None,
    expected_candidate_root: str | None = None,
    expected_entrypoint: str | None = None,
    expected_source_bundle_sha256: str | None = None,
) -> SourceArchive:
    """Read, rehash, and semantically verify one immutable archive."""

    root_path = Path(root).resolve()
    digest = _require_hash(archive_sha256, "source_archive_sha256")
    relative = _relative_path(relative_path, "source_archive_path")
    archive = _decode_archive(
        _stable_read(_resolved_archive_path(root_path, relative)),
        relative_path=relative,
        sha256=digest,
    )
    expectations = {
        "team_id": expected_team_id,
        "candidate_id": expected_candidate_id,
        "candidate_root": expected_candidate_root,
        "entrypoint": expected_entrypoint,
        "source_bundle_sha256": expected_source_bundle_sha256,
    }
    for field, expected in expectations.items():
        if expected is not None and getattr(archive, field) != expected:
            raise SourceArchiveError(f"source archive differs from expected {field}")
    return archive


def write_source_archive(
    root: str | Path,
    *,
    team_id: str,
    candidate_id: str,
    candidate_root: str,
    entrypoint: str,
    source_bundle_sha256: str,
    files: Iterable[SourceFile],
) -> SourceArchive:
    """Create or reuse an exact content-addressed archive, fsyncing before return."""

    root_path = Path(root).resolve()
    payload = build_archive_bytes(
        team_id=team_id,
        candidate_id=candidate_id,
        candidate_root=candidate_root,
        entrypoint=entrypoint,
        source_bundle_sha256=source_bundle_sha256,
        files=files,
    )
    digest = hashlib.sha256(payload).hexdigest()
    relative = archive_relative_path(digest)
    path = _resolved_archive_path(root_path, relative, create_parent=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{digest}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        try:
            with os.fdopen(descriptor, "wb") as handle:
                written = handle.write(payload)
                if written != len(payload):
                    raise OSError("short source archive write")
                handle.flush()
                os.fchmod(handle.fileno(), 0o444)
                os.fsync(handle.fileno())
            try:
                # A hard-link install is atomic and refuses replacement. Both paths are in the
                # same organizer-owned directory, so this is a portable no-replace publication.
                os.link(temporary, path, follow_symlinks=False)
            except FileExistsError:
                existing = _stable_read(path)
                if existing != payload:
                    raise SourceArchiveError("content-addressed source archive collision")
            else:
                _fsync_directory(path.parent)
        except SourceArchiveError:
            raise
        except OSError as exc:
            raise SourceArchiveError(f"cannot create source archive: {exc}") from exc
    finally:
        try:
            temporary.unlink()
            _fsync_directory(path.parent)
        except FileNotFoundError:
            pass
    # This post-fsync stable read is also the reuse verification path.
    archive = read_source_archive(
        root_path,
        relative,
        digest,
        expected_team_id=team_id,
        expected_candidate_id=candidate_id,
        expected_candidate_root=candidate_root,
        expected_entrypoint=entrypoint,
        expected_source_bundle_sha256=source_bundle_sha256,
    )
    if _stable_read(path) != payload:
        raise SourceArchiveError("source archive changed after durable verification")
    return archive


__all__ = [
    "ARCHIVE_NAMESPACE",
    "SCHEMA_VERSION",
    "SourceArchive",
    "SourceArchiveError",
    "SourceFile",
    "archive_relative_path",
    "build_archive_bytes",
    "bundle_fingerprint",
    "canonical_json_bytes",
    "read_source_archive",
    "write_source_archive",
]
