"""Organizer authority for the two-round Top-40 V4 tournament."""

from __future__ import annotations

import contextlib
import dataclasses
import fcntl
import hashlib
import io
import json
import math
import os
import re
import shutil
import stat
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.tournament import (
    activation_v4,
    journal_v4,
    metrics_v3,
    runner_v4,
    scoring_v4,
    source_archive_v4,
    top40_v4,
)
from crypto_trade.tournament.layout_v4 import TOP40_V4_LAYOUT

CONFIG_PATH = TOP40_V4_LAYOUT.config_path
DATA_MANIFEST_PATH = "tournament/top40/data_manifest.json"
_SAFE_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_SAFE_TAG = re.compile(r"[a-z][a-z0-9-]{0,63}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_METADATA_KEYS = frozenset(
    {
        "schema_version",
        "team_id",
        "candidate_id",
        "parent_candidate_id",
        "mechanism",
        "hypothesis",
        "falsifier",
        "formation_horizon",
        "rebalance_horizon",
        "control_profile",
        "neighborhood_id",
        "neighborhood_coordinates",
        "tags",
        "material_parameters",
    }
)
_RELEASE_ARTIFACT_FILES = {
    "targets": "targets.parquet",
    "events": "events.parquet",
    "positions": "positions.parquet",
    "evaluator_returns": "bar_returns.csv",
    "double_cost_evaluator_returns": "double_cost_bar_returns.csv",
    "triple_cost_evaluator_returns": "triple_cost_bar_returns.csv",
    "daily_returns": "daily_returns.csv",
    "double_cost_daily_returns": "double_cost_daily_returns.csv",
    "triple_cost_daily_returns": "triple_cost_daily_returns.csv",
    "trades": "trades.csv",
}


class OrchestratorError(RuntimeError):
    """A V4 organizer command was refused without changing tournament semantics."""


class ResultCommandBusyError(OrchestratorError):
    """Another result-bearing V4 command owns the kernel lock."""


@dataclasses.dataclass(frozen=True, slots=True)
class CandidateAuthority:
    team_id: str
    candidate_id: str
    candidate_root: str
    entrypoint: str
    source_bundle_sha256: str
    source_archive_path: str
    source_archive_sha256: str
    strategy_sha256: str
    risk_policy_sha256: str
    config_sha256: str
    dependency_lock_sha256: str
    data_manifest_sha256: str
    evaluator_sha256: str

    def as_dict(self) -> dict[str, str]:
        return dataclasses.asdict(self)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _coordinate_vector_key(coordinates: Mapping[str, Any]) -> bytes:
    normalized = {
        key: 0.0 if float(coordinates[key]) == 0.0 else float(coordinates[key])
        for key in sorted(coordinates)
    }
    return _canonical(normalized)


def _sha256_file(path: Path) -> str:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise OrchestratorError("authority path is not a regular file")
            digest = hashlib.sha256()
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
            after = os.fstat(handle.fileno())
        path_after = path.lstat()
    except OSError as exc:
        raise OrchestratorError(f"cannot stably hash authority file: {path}") from exc
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    path_identity = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
    )
    if (
        before_identity != after_identity
        or after_identity != path_identity
        or stat.S_ISLNK(path_after.st_mode)
    ):
        raise OrchestratorError("authority file changed while being hashed")
    return digest.hexdigest()


def _stable_authority_bytes(path: Path, *, maximum: int = 64 * 1024 * 1024) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
                raise OrchestratorError("authority file is not a bounded regular file")
            payload = handle.read(maximum + 1)
            after = os.fstat(handle.fileno())
        path_after = path.lstat()
    except OSError as exc:
        raise OrchestratorError(f"cannot stably read authority file: {path}") from exc
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    path_identity = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
    )
    if (
        len(payload) > maximum
        or before_identity != after_identity
        or after_identity != path_identity
        or stat.S_ISLNK(path_after.st_mode)
    ):
        raise OrchestratorError("authority file changed while being read")
    return payload


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise OrchestratorError("organizer value is not canonical finite JSON") from exc


def _pretty(value: object) -> bytes:
    try:
        return json.dumps(value, allow_nan=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    except (TypeError, ValueError) as exc:
        raise OrchestratorError("organizer value is not finite JSON") from exc


def _safe_root(root: str | Path) -> Path:
    result = Path(root).resolve()
    if not result.is_dir():
        raise OrchestratorError(f"repository root is not a directory: {result}")
    return result


def _path(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise OrchestratorError(f"unsafe repository-relative path: {relative}")
    lexical = root
    for part in pure.parts:
        lexical = lexical / part
        if os.path.lexists(lexical) and lexical.is_symlink():
            raise OrchestratorError(f"path contains a symlink: {relative}")
    result = lexical.resolve()
    if not result.is_relative_to(root):
        raise OrchestratorError(f"path escapes repository: {relative}")
    return result


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _ensure_directory(root: Path, directory: Path) -> None:
    try:
        relative = directory.relative_to(root)
    except ValueError as exc:
        raise OrchestratorError("organizer directory escapes the repository") from exc
    current = root
    for part in relative.parts:
        child = current / part
        if os.path.lexists(child):
            if child.is_symlink() or not child.is_dir():
                raise OrchestratorError("organizer directory contains an unsafe component")
        else:
            child.mkdir(mode=0o700)
            _fsync_directory(current)
        current = child


def _write_atomic(root: Path, relative: str, payload: bytes, *, replace: bool) -> str:
    path = _path(root, relative)
    _ensure_directory(root, path.parent)
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise OrchestratorError(f"refusing unsafe organizer output: {relative}")
    if path.exists() and not replace:
        if path.read_bytes() != payload:
            raise OrchestratorError(f"immutable organizer output already differs: {relative}")
        return _sha256(payload)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            if handle.write(payload) != len(payload):
                raise OSError("short atomic write")
            handle.flush()
            os.fsync(handle.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            try:
                os.link(temporary, path, follow_symlinks=False)
            except FileExistsError as exc:
                if path.is_file() and not path.is_symlink() and path.read_bytes() == payload:
                    return _sha256(payload)
                raise OrchestratorError(
                    f"immutable organizer output already differs: {relative}"
                ) from exc
        _fsync_directory(path.parent)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()
            _fsync_directory(path.parent)
    return _sha256(payload)


def _strict_object_bytes(payload: bytes, relative: str) -> Mapping[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise OrchestratorError(f"duplicate JSON key in {relative}: {key}")
            value[key] = item
        return value

    def reject(value: str) -> None:
        raise OrchestratorError(f"nonfinite JSON value in {relative}: {value}")

    try:
        result = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=unique,
            parse_constant=reject,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OrchestratorError(f"invalid JSON file: {relative}") from exc
    if not isinstance(result, Mapping):
        raise OrchestratorError(f"JSON root must be an object: {relative}")
    return result


def _strict_object(root: Path, relative: str) -> Mapping[str, Any]:
    path = _path(root, relative)
    if not path.is_file() or path.is_symlink():
        raise OrchestratorError(f"required JSON file is missing or unsafe: {relative}")
    return _strict_object_bytes(_stable_authority_bytes(path), relative)


@contextlib.contextmanager
def _result_lock(root: Path) -> Iterator[None]:
    path = _path(root, TOP40_V4_LAYOUT.result_lock_path)
    _ensure_directory(root, path.parent)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ResultCommandBusyError("another V4 result command is active") from exc
        os.ftruncate(descriptor, 0)
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        os.fsync(descriptor)
        yield
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _journal_path(root: Path) -> Path:
    return _path(root, TOP40_V4_LAYOUT.journal_path)


def _validate_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise OrchestratorError(f"{label} is not a safe identifier")
    return value


def _validate_text(value: object, label: str, maximum: int = 2048) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > maximum
        or value != value.strip()
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise OrchestratorError(f"{label} must be bounded single-line text")
    return value


def _candidate_metadata(
    root: Path,
    config: Mapping[str, Any],
    team_id: str,
    entrypoint: str,
) -> tuple[Mapping[str, Any], str]:
    TOP40_V4_LAYOUT.require_team(team_id)
    entry = _path(root, entrypoint)
    team_root = _path(root, TOP40_V4_LAYOUT.team_root(team_id))
    try:
        candidate_parts = entry.relative_to(team_root).parts
    except ValueError:
        candidate_parts = ()
    if (
        not entry.is_file()
        or entry.is_symlink()
        or len(candidate_parts) != 3
        or candidate_parts[0] != "candidates"
        or candidate_parts[2] != "strategy.py"
        or _SAFE_ID.fullmatch(candidate_parts[1]) is None
    ):
        raise OrchestratorError(
            "candidate entrypoint must be candidates/<candidate-id>/strategy.py "
            "inside its team lane"
        )
    metadata_path = entry.parent / "candidate.json"
    relative = metadata_path.relative_to(root).as_posix()
    metadata = _strict_object(root, relative)
    if set(metadata) != _METADATA_KEYS or metadata.get("schema_version") != 1:
        raise OrchestratorError("candidate.json has missing or unexpected V4 fields")
    if metadata.get("team_id") != team_id:
        raise OrchestratorError("candidate metadata has the wrong team_id")
    candidate_id = _validate_identifier(metadata.get("candidate_id"), "candidate_id")
    if candidate_id != candidate_parts[1]:
        raise OrchestratorError("candidate_id must exactly match its candidate directory")
    parent = metadata.get("parent_candidate_id")
    if parent is not None:
        _validate_identifier(parent, "parent_candidate_id")
    mechanism = _validate_text(metadata.get("mechanism"), "mechanism", 256)
    expected_mechanism = str(config["mandates"][team_id])
    tags = metadata.get("tags")
    if (
        not isinstance(tags, list)
        or not tags
        or any(not isinstance(tag, str) or _SAFE_TAG.fullmatch(tag) is None for tag in tags)
        or len(set(tags)) != len(tags)
    ):
        raise OrchestratorError("candidate tags must be a unique nonempty safe list")
    if mechanism != expected_mechanism and "mechanism-pivot" not in tags:
        raise OrchestratorError("candidate mechanism differs from its lane without a pivot tag")
    for key in (
        "hypothesis",
        "falsifier",
        "formation_horizon",
        "rebalance_horizon",
        "control_profile",
    ):
        _validate_text(metadata.get(key), key)
    neighborhood = metadata.get("neighborhood_id")
    if neighborhood is not None:
        _validate_identifier(neighborhood, "neighborhood_id")
    coordinates = metadata.get("neighborhood_coordinates")
    if not isinstance(coordinates, Mapping):
        raise OrchestratorError("neighborhood_coordinates must be an object")
    for key, raw_value in coordinates.items():
        _validate_identifier(key, "neighborhood coordinate")
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
            raise OrchestratorError("neighborhood coordinates must be numeric")
        if not math.isfinite(float(raw_value)):
            raise OrchestratorError("neighborhood coordinates must be finite")
    parameters = metadata.get("material_parameters")
    if not isinstance(parameters, Mapping) or not parameters:
        raise OrchestratorError("material_parameters must be a nonempty object")
    _canonical(parameters)
    for key, raw_value in coordinates.items():
        material_value = parameters.get(key)
        if (
            isinstance(material_value, bool)
            or not isinstance(material_value, (int, float))
            or float(material_value) != float(raw_value)
        ):
            raise OrchestratorError(
                "every neighborhood coordinate must match a numeric material parameter"
            )
    return metadata, relative


def _derive_authority(
    root: Path,
    loaded: top40_v4.LoadedV4Config,
    team_id: str,
    entrypoint: str,
) -> tuple[CandidateAuthority, Mapping[str, Any]]:
    metadata, _metadata_path = _candidate_metadata(root, loaded.raw, team_id, entrypoint)
    candidate_id = str(metadata["candidate_id"])
    capture = runner_v4.capture_source_bundle(root, team_id, entrypoint)
    archive = source_archive_v4.write_source_archive(
        root,
        team_id=team_id,
        candidate_id=candidate_id,
        candidate_root=capture.candidate_root,
        entrypoint=capture.entrypoint,
        source_bundle_sha256=capture.sha256,
        files=capture.files,
    )
    entry_path = _path(root, entrypoint)
    risk_path = entry_path.parent / "risk_policy.json"
    authority = CandidateAuthority(
        team_id=team_id,
        candidate_id=candidate_id,
        candidate_root=capture.candidate_root,
        entrypoint=entrypoint,
        source_bundle_sha256=capture.sha256,
        source_archive_path=archive.path,
        source_archive_sha256=archive.sha256,
        strategy_sha256=_sha256_file(entry_path),
        risk_policy_sha256=_sha256_file(risk_path),
        config_sha256=loaded.sha256,
        dependency_lock_sha256=_sha256_file(root / "uv.lock"),
        data_manifest_sha256=_sha256_file(_path(root, DATA_MANIFEST_PATH)),
        evaluator_sha256=runner_v4._evaluator_authority_sha256(root),
    )
    return authority, metadata


def _validate_authority_current(
    root: Path,
    loaded: top40_v4.LoadedV4Config,
    expected: Mapping[str, Any],
) -> CandidateAuthority:
    authority, _metadata = _derive_authority(
        root,
        loaded,
        str(expected["team_id"]),
        str(expected["entrypoint"]),
    )
    if authority.as_dict() != dict(expected):
        raise OrchestratorError("candidate differs from its accepted immutable identity")
    return authority


def activate(root: str | Path) -> Mapping[str, Any]:
    root_path = _safe_root(root)
    with _result_lock(root_path):
        top40_v4.load_config(root=root_path)
        journal_v4.initialize(_journal_path(root_path))
        return activation_v4.activate(root_path)


def validate(root: str | Path, *, require_activation: bool = True) -> Mapping[str, Any]:
    root_path = _safe_root(root)
    loaded = top40_v4.load_config(root=root_path)
    activation = activation_v4.validate(root_path) if require_activation else None
    journal_path = _journal_path(root_path)
    state = journal_v4.read(journal_path) if journal_path.exists() else journal_v4.replay_bytes(b"")
    visible_head = state.head_sha256
    visible_records = state.record_count
    if state.selection is not None and state.release is None:
        # The sealed phase exposes one constant boundary, never per-finalist starts, terminals,
        # timing, or completion order.
        visible_head = str(state.selection_record_sha256)
        visible_records = next(
            int(record["sequence"])
            for record in state.records
            if record["record_sha256"] == state.selection_record_sha256
        )
    return {
        "ok": True,
        "tournament": TOP40_V4_LAYOUT.name,
        "config_sha256": loaded.sha256,
        "activation_record_sha256": activation.get("record_sha256") if activation else None,
        "journal_head_sha256": visible_head,
        "journal_records": visible_records,
    }


def status(root: str | Path) -> Mapping[str, Any]:
    root_path = _safe_root(root)
    loaded = top40_v4.load_config(root=root_path)
    activated = _path(root_path, TOP40_V4_LAYOUT.activation_freeze_path).exists()
    journal_path = _journal_path(root_path)
    state = journal_v4.read(journal_path) if journal_path.exists() else journal_v4.replay_bytes(b"")
    visible_head = state.head_sha256
    if state.selection is not None and state.release is None:
        visible_head = str(state.selection_record_sha256)
    release_integrity: bool | None = None
    if state.release is not None:
        public = str(state.release["release_path"])
        public_path = _path(root_path, public)
        if not public_path.exists():
            phase = "historical-oos-release-authorized-promotion-pending"
        else:
            try:
                _validate_staged_release(
                    root_path,
                    public,
                    manifest_sha256=str(state.release["manifest_sha256"]),
                    bundle_sha256=str(state.release["bundle_sha256"]),
                )
            except OrchestratorError:
                phase = "historical-oos-release-integrity-error"
                release_integrity = False
            else:
                phase = "historical-oos-released"
                release_integrity = True
    elif state.selection is not None:
        phase = "historical-oos-sealed-running"
    else:
        phase = "is-research"
    result: dict[str, Any] = {
        "tournament": TOP40_V4_LAYOUT.name,
        "phase": phase,
        "activated": activated,
        "config_sha256": loaded.sha256,
        "journal_head_sha256": visible_head,
    }
    if state.selection is None:
        result["teams"] = {
            team_id: {
                "accepted_trials": state.trials_by_team[team_id],
                "disposition": (
                    "nominated"
                    if team_id in state.nominations
                    else "retired"
                    if team_id in state.retired
                    else "researching"
                ),
            }
            for team_id in TOP40_V4_LAYOUT.team_ids
        }
    elif state.release is None:
        result["championship"] = {
            "finalist_count": len(state.selection["advancing"]),
            "interim_disclosure": False,
            "status": "sealed until atomic release",
        }
    else:
        result["release_path"] = state.release["release_path"]
        result["manifest_sha256"] = state.release["manifest_sha256"]
        result["release_integrity_valid"] = release_integrity
        result["promotion_pending"] = release_integrity is None
    return result


def _run_team(
    root: Path,
    authority: CandidateAuthority,
    *,
    stage: str,
    output: str,
) -> runner_v4.TeamWindowRunResult:
    return runner_v4.run_team(
        root,
        authority.team_id,
        authority.entrypoint,
        CONFIG_PATH,
        DATA_MANIFEST_PATH,
        stage=stage,
        _authorization=runner_v4._ORGANIZER_RUN_AUTHORIZATION,
        _output_relative=output,
        _candidate_id=authority.candidate_id,
        _source_archive_relative=authority.source_archive_path,
        _source_archive_sha256=authority.source_archive_sha256,
    )


def _close_interrupted_is_requests(root: Path) -> journal_v4.JournalState:
    """Convert requests left pending by process death into consumed failed trials."""

    state = journal_v4.read(_journal_path(root))
    pending = [
        (request_hash, request)
        for request_hash, request in state.is_requests.items()
        if request_hash not in state.is_terminals
    ]
    for request_hash, request in pending:
        event = request["payload"]
        journal_v4.append(
            _journal_path(root),
            "is_failed",
            {
                "team_id": event["team_id"],
                "run_id": event["run_id"],
                "candidate_id": event["candidate_id"],
                "request_sha256": request_hash,
                "failure": "interrupted-after-accepted-trial",
            },
        )
    return journal_v4.read(_journal_path(root))


def run_is(
    root: str | Path,
    team_id: str,
    entrypoint: str,
    *,
    purpose: str,
) -> Mapping[str, Any]:
    root_path = _safe_root(root)
    with _result_lock(root_path):
        # Candidate acceptance must be durable before any snapshot file is opened. The runner
        # performs the full frozen-universe audit after the accepted record is fsynced.
        activation_v4.validate(root_path, verify_universe_snapshot=False)
        loaded = top40_v4.load_config(root=root_path)
        state = _close_interrupted_is_requests(root_path)
        TOP40_V4_LAYOUT.require_team(team_id)
        if state.selection is not None:
            raise OrchestratorError("IS is closed")
        if team_id in state.nominations or team_id in state.retired:
            raise OrchestratorError("team already has a terminal IS disposition")
        maximum = int(loaded.raw["research"]["maximum_accepted_trials_per_team"])
        if state.trials_by_team[team_id] >= maximum:
            raise OrchestratorError("team exhausted its twelve accepted trials")
        _validate_text(purpose, "purpose")
        authority, metadata = _derive_authority(root_path, loaded, team_id, entrypoint)
        trial = state.trials_by_team[team_id] + 1
        run_id = f"{team_id.replace('-', '')}-is-{trial:02d}-{authority.source_bundle_sha256[:12]}"
        output = f"{TOP40_V4_LAYOUT.reports_root}/is/{team_id}/{run_id}"
        request = journal_v4.append(
            _journal_path(root_path),
            "is_accepted",
            {
                "team_id": team_id,
                "run_id": run_id,
                "trial_number": trial,
                "candidate_id": authority.candidate_id,
                "purpose": purpose,
                "metadata": dict(metadata),
                "authority": authority.as_dict(),
                "output_path": output,
            },
        )
        try:
            result = _run_team(root_path, authority, stage="is", output=output)
            summary = scoring_v4.summarize_run(root_path, result, loaded.raw, trial_count=trial)
            summary["candidate_id"] = authority.candidate_id
            summary["run_id"] = run_id
            summary_path = f"{output}/summary.json"
            summary_payload = _pretty(summary)
            summary_sha256 = _write_atomic(root_path, summary_path, summary_payload, replace=False)
            terminal = journal_v4.append(
                _journal_path(root_path),
                "is_succeeded",
                {
                    "team_id": team_id,
                    "run_id": run_id,
                    "candidate_id": authority.candidate_id,
                    "request_sha256": request["record_sha256"],
                    "summary_path": summary_path,
                    "summary_sha256": summary_sha256,
                },
            )
        except BaseException as exc:
            journal_v4.append(
                _journal_path(root_path),
                "is_failed",
                {
                    "team_id": team_id,
                    "run_id": run_id,
                    "candidate_id": authority.candidate_id,
                    "request_sha256": request["record_sha256"],
                    "failure": f"{type(exc).__name__}: {exc}"[:2048],
                },
            )
            raise
        return {
            "ok": True,
            "team_id": team_id,
            "candidate_id": authority.candidate_id,
            "trial_number": trial,
            "run_id": run_id,
            "summary_path": summary_path,
            "selection": summary["selection"],
            "journal_record_sha256": terminal["record_sha256"],
        }


def _verified_summary(root: Path, terminal: Mapping[str, Any]) -> Mapping[str, Any]:
    event = terminal["payload"]
    relative = str(event["summary_path"])
    path = _path(root, relative)
    if not path.is_file() or path.is_symlink():
        raise OrchestratorError("journal-bound summary is missing or unsafe")
    payload = _stable_authority_bytes(path)
    if _sha256(payload) != event["summary_sha256"]:
        raise OrchestratorError("journal-bound summary changed")
    return _strict_object_bytes(payload, relative)


def _candidate_success(
    state: journal_v4.JournalState, team_id: str, candidate_id: str
) -> tuple[str, Mapping[str, Any], str, Mapping[str, Any]]:
    matches: list[tuple[str, Mapping[str, Any], str, Mapping[str, Any]]] = []
    for success_hash, terminal in state.is_successes.items():
        event = terminal["payload"]
        if event["team_id"] == team_id and event["candidate_id"] == candidate_id:
            request_hash = str(event["request_sha256"])
            matches.append((success_hash, terminal, request_hash, state.is_requests[request_hash]))
    if len(matches) != 1:
        raise OrchestratorError("candidate must have exactly one successful IS observation")
    return matches[0]


def _certificate(
    root: Path,
    relative: str,
    *,
    state: journal_v4.JournalState,
    config: Mapping[str, Any],
    team_id: str,
    candidate_id: str,
    nominated_request_hash: str,
) -> tuple[Mapping[str, Any], str, dict[str, Any]]:
    required_prefix = f"{TOP40_V4_LAYOUT.tournament_root}/certificates/{team_id}/"
    if not relative.startswith(required_prefix):
        raise OrchestratorError("research certificate must remain inside its team namespace")
    certificate_payload = _stable_authority_bytes(_path(root, relative))
    certificate = _strict_object_bytes(certificate_payload, relative)
    if set(certificate) != {"schema_version", "team_id", "candidate_id", "evidence"}:
        raise OrchestratorError("research certificate has missing or unexpected fields")
    if (
        certificate["schema_version"] != 1
        or certificate["team_id"] != team_id
        or certificate["candidate_id"] != candidate_id
    ):
        raise OrchestratorError("research certificate identity is wrong")
    evidence = certificate["evidence"]
    required_tags = tuple(config["research"]["required_certificate_tags"])
    if not isinstance(evidence, Mapping) or set(evidence) != set(required_tags):
        raise OrchestratorError("research certificate evidence cells differ from policy")
    team_requests = {
        digest: record
        for digest, record in state.is_requests.items()
        if record["payload"]["team_id"] == team_id
    }
    cited_requests: set[str] = set()
    for tag in required_tags:
        digests = evidence[tag]
        if not isinstance(digests, list) or not digests or len(set(digests)) != len(digests):
            raise OrchestratorError(f"certificate cell {tag} must list unique trial records")
        for digest in digests:
            if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
                raise OrchestratorError(f"certificate cell {tag} contains an invalid hash")
            request = team_requests.get(digest)
            if request is None or tag not in request["payload"]["metadata"]["tags"]:
                raise OrchestratorError(f"certificate cell {tag} cites incompatible evidence")
            cited_requests.add(digest)
    if cited_requests != set(team_requests):
        raise OrchestratorError("research certificate must cover every accepted team trial")

    records = [record["payload"]["metadata"] for record in team_requests.values()]
    research = config["research"]
    if len({row["formation_horizon"] for row in records}) < int(
        research["minimum_distinct_formation_horizons"]
    ):
        raise OrchestratorError("research certificate lacks formation-horizon breadth")
    if len({row["rebalance_horizon"] for row in records}) < int(
        research["minimum_distinct_rebalance_horizons"]
    ):
        raise OrchestratorError("research certificate lacks rebalance-horizon breadth")
    if len({row["control_profile"] for row in records}) < int(
        research["minimum_distinct_control_profiles"]
    ):
        raise OrchestratorError("research certificate lacks control-profile breadth")
    if sum("mechanism-pivot" in row["tags"] for row in records) > int(
        research["maximum_mechanism_pivots_per_team"]
    ):
        raise OrchestratorError("team exceeded its mechanism-pivot allowance")

    finalist_metadata = team_requests[nominated_request_hash]["payload"]["metadata"]
    neighborhood_id = finalist_metadata["neighborhood_id"]
    finalist_coordinates = finalist_metadata["neighborhood_coordinates"]
    if neighborhood_id is None or not finalist_coordinates:
        raise OrchestratorError("finalist must declare a numeric local neighborhood")
    neighborhood_hashes = evidence["local-neighborhood"]
    if len(neighborhood_hashes) < int(research["minimum_neighborhood_points"]):
        raise OrchestratorError("research certificate has too few neighborhood points")
    neighborhood_summaries: list[Mapping[str, Any]] = []
    coordinates: list[Mapping[str, Any]] = []
    passes = 0
    double_sharpes: list[float] = []
    for request_hash in neighborhood_hashes:
        request = team_requests[request_hash]
        metadata = request["payload"]["metadata"]
        if metadata["neighborhood_id"] != neighborhood_id:
            raise OrchestratorError("certificate mixes different local neighborhoods")
        if set(metadata["neighborhood_coordinates"]) != set(finalist_coordinates):
            raise OrchestratorError("neighborhood coordinate schema is inconsistent")
        terminal = state.is_terminals.get(request_hash)
        if terminal is None or terminal["event_type"] != "is_succeeded":
            raise OrchestratorError("every local-neighborhood point must have succeeded")
        summary = _verified_summary(root, terminal)
        annual_return = float(summary["scored_window"]["base_metrics"]["annualized_return"])
        double_sharpe = float(summary["scored_window"]["double_cost_metrics"]["net_sharpe"])
        passes += annual_return > 0.0 and double_sharpe > 0.0
        double_sharpes.append(double_sharpe)
        neighborhood_summaries.append(summary)
        coordinates.append(metadata["neighborhood_coordinates"])
    coordinate_vectors = {_coordinate_vector_key(row) for row in coordinates}
    if len(coordinate_vectors) != len(coordinates):
        raise OrchestratorError("local-neighborhood coordinate vectors must be distinct")
    pass_fraction = passes / len(neighborhood_summaries)
    median_double = float(np.median(double_sharpes))
    if pass_fraction < float(research["minimum_neighborhood_pass_fraction"]):
        raise OrchestratorError("local-neighborhood pass fraction is below policy")
    if median_double < float(research["minimum_neighborhood_median_double_cost_sharpe"]):
        raise OrchestratorError("local-neighborhood median 2x Sharpe is below policy")
    for key, finalist_value in finalist_coordinates.items():
        values = [float(row[key]) for row in coordinates]
        if not min(values) < float(finalist_value) < max(values):
            raise OrchestratorError(
                f"local neighborhood does not bracket finalist coordinate {key}"
            )
    diagnostics = {
        "neighborhood_id": neighborhood_id,
        "points": len(neighborhood_summaries),
        "pass_fraction": float(pass_fraction),
        "median_double_cost_sharpe": median_double,
        "bracketed_coordinates": sorted(finalist_coordinates),
    }
    return certificate, _sha256(certificate_payload), diagnostics


def _write_nomination_registry(root: Path, state: journal_v4.JournalState) -> None:
    registry = {
        "schema_version": "top40-v4-r1-nomination-registry-v1",
        "journal_head_sha256": state.head_sha256,
        "teams": {
            team_id: dict(record["payload"])
            for team_id, record in sorted(state.nominations.items())
        },
    }
    _write_atomic(
        root,
        TOP40_V4_LAYOUT.nomination_registry_path,
        _pretty(registry),
        replace=True,
    )


def nominate(
    root: str | Path,
    team_id: str,
    candidate_id: str,
    certificate_path: str,
) -> Mapping[str, Any]:
    root_path = _safe_root(root)
    with _result_lock(root_path):
        activation_v4.validate(root_path)
        loaded = top40_v4.load_config(root=root_path)
        state = _close_interrupted_is_requests(root_path)
        if state.selection is not None:
            raise OrchestratorError("IS is closed")
        TOP40_V4_LAYOUT.require_team(team_id)
        if team_id in state.nominations:
            existing = state.nominations[team_id]["payload"]
            if existing["candidate_id"] != candidate_id:
                raise OrchestratorError("team is already nominated with another candidate")
            _verified_nomination(root_path, state.nominations[team_id])
            _write_nomination_registry(root_path, state)
            return {
                "ok": True,
                "already_nominated": True,
                "team_id": team_id,
                "candidate_id": candidate_id,
                "journal_record_sha256": state.nominations[team_id]["record_sha256"],
            }
        if team_id in state.retired:
            raise OrchestratorError("team already has a terminal IS disposition")
        minimum = int(loaded.raw["research"]["minimum_accepted_trials_before_nomination"])
        if state.trials_by_team.get(team_id, 0) < minimum:
            raise OrchestratorError("team must consume at least eight structured trials")
        success_hash, terminal, request_hash, request = _candidate_success(
            state, team_id, candidate_id
        )
        authority = _validate_authority_current(root_path, loaded, request["payload"]["authority"])
        summary = dict(_verified_summary(root_path, terminal))
        certificate, certificate_sha256, neighborhood = _certificate(
            root_path,
            certificate_path,
            state=state,
            config=loaded.raw,
            team_id=team_id,
            candidate_id=candidate_id,
            nominated_request_hash=request_hash,
        )
        selection = scoring_v4.assess_is(
            summary,
            loaded.raw,
            trial_count=state.trials_by_team[team_id],
            neighborhood_passed=True,
        )
        if not selection["eligible"]:
            failed = sorted(key for key, passed in selection["gates"].items() if not passed)
            raise OrchestratorError(f"candidate fails frozen IS gates: {', '.join(failed)}")
        nomination = {
            "schema_version": "top40-v4-r1-nomination-v1",
            "team_id": team_id,
            "candidate_id": candidate_id,
            "trial_count": state.trials_by_team[team_id],
            "request_record_sha256": request_hash,
            "success_record_sha256": success_hash,
            "authority": authority.as_dict(),
            "summary_path": terminal["payload"]["summary_path"],
            "summary_sha256": terminal["payload"]["summary_sha256"],
            "certificate_path": certificate_path,
            "certificate_sha256": certificate_sha256,
            "certificate": certificate,
            "neighborhood": neighborhood,
            "selection": selection,
        }
        nomination_path = (
            f"{TOP40_V4_LAYOUT.tournament_root}/nominations/{team_id}-{candidate_id}.json"
        )
        nomination_payload = _pretty(nomination)
        nomination_sha256 = _write_atomic(
            root_path, nomination_path, nomination_payload, replace=True
        )
        record = journal_v4.append(
            _journal_path(root_path),
            "nominated",
            {
                "team_id": team_id,
                "candidate_id": candidate_id,
                "success_record_sha256": success_hash,
                "certificate_path": certificate_path,
                "certificate_sha256": certificate_sha256,
                "nomination_path": nomination_path,
                "nomination_sha256": nomination_sha256,
            },
        )
        _write_nomination_registry(root_path, journal_v4.read(_journal_path(root_path)))
        return {
            "ok": True,
            "team_id": team_id,
            "candidate_id": candidate_id,
            "eligible": True,
            "selection": selection,
            "journal_record_sha256": record["record_sha256"],
        }


def retire(root: str | Path, team_id: str, *, reason: str) -> Mapping[str, Any]:
    root_path = _safe_root(root)
    with _result_lock(root_path):
        activation_v4.validate(root_path)
        loaded = top40_v4.load_config(root=root_path)
        state = _close_interrupted_is_requests(root_path)
        TOP40_V4_LAYOUT.require_team(team_id)
        if state.selection is not None:
            raise OrchestratorError("team cannot retire in its current lifecycle state")
        if team_id in state.retired:
            _write_nomination_registry(root_path, state)
            return {
                "ok": True,
                "already_retired": True,
                "team_id": team_id,
                "journal_record_sha256": state.retired[team_id]["record_sha256"],
            }
        if team_id in state.nominations:
            raise OrchestratorError("team cannot retire after nomination")
        minimum = int(loaded.raw["research"]["minimum_accepted_trials_before_nomination"])
        if state.trials_by_team[team_id] < minimum:
            raise OrchestratorError("retirement requires at least eight accepted research trials")
        _validate_text(reason, "reason")
        record = journal_v4.append(
            _journal_path(root_path), "retired", {"team_id": team_id, "reason": reason}
        )
        _write_nomination_registry(root_path, journal_v4.read(_journal_path(root_path)))
        return {"ok": True, "team_id": team_id, "journal_record_sha256": record["record_sha256"]}


def _verified_nomination(root: Path, record: Mapping[str, Any]) -> Mapping[str, Any]:
    event = record["payload"]
    path = _path(root, str(event["nomination_path"]))
    payload = _stable_authority_bytes(path)
    if _sha256(payload) != event["nomination_sha256"]:
        raise OrchestratorError("frozen nomination bytes changed")
    return _strict_object_bytes(payload, str(event["nomination_path"]))


def _daily_from_nomination(root: Path, nomination: Mapping[str, Any]) -> pd.Series:
    summary_path = str(nomination["summary_path"])
    summary_file = _path(root, summary_path)
    summary_payload = _stable_authority_bytes(summary_file)
    if _sha256(summary_payload) != nomination["summary_sha256"]:
        raise OrchestratorError("nominee summary authority changed")
    summary = _strict_object_bytes(summary_payload, summary_path)
    relative = summary["runner"]["artifacts"]["daily_returns"]
    expected = summary["runner"]["artifact_sha256"]["daily_returns"]
    path = _path(root, str(relative))
    daily_payload = _stable_authority_bytes(path)
    if _sha256(daily_payload) != expected:
        raise OrchestratorError("nominee daily-return authority changed")
    frame = pd.read_csv(io.BytesIO(daily_payload))
    if list(frame.columns) != ["date", "net_return"]:
        raise OrchestratorError("nominee daily-return schema changed")
    index = pd.DatetimeIndex(pd.to_datetime(frame["date"], utc=True, errors="coerce"))
    values = pd.to_numeric(frame["net_return"], errors="coerce")
    expected_index = pd.date_range(
        "2020-02-03T00:00:00Z",
        "2024-07-01T00:00:00Z",
        inclusive="left",
        freq="1D",
    )
    if (
        index.hasnans
        or not index.equals(expected_index)
        or values.isna().any()
        or not np.isfinite(values.to_numpy(dtype=float)).all()
    ):
        raise OrchestratorError("nominee daily returns are invalid")
    return pd.Series(values.to_numpy(dtype=float), index=index)


def _capped_inverse_vol_weights(
    root: Path, nominees: Sequence[Mapping[str, Any]], cap: float
) -> tuple[dict[str, float], float]:
    if not nominees:
        return {}, 1.0
    inverse: dict[str, float] = {}
    for nomination in nominees:
        daily = _daily_from_nomination(root, nomination)
        volatility = float(daily.std(ddof=1) * np.sqrt(365.0))
        if not math.isfinite(volatility) or volatility <= 1e-15:
            raise OrchestratorError("nominee has zero or invalid IS volatility")
        inverse[str(nomination["team_id"])] = 1.0 / volatility
    capacity = min(1.0, cap * len(inverse))
    remaining = capacity
    active = set(inverse)
    weights = {team_id: 0.0 for team_id in inverse}
    while active and remaining > 1e-15:
        denominator = sum(inverse[team_id] for team_id in active)
        provisional = {team_id: remaining * inverse[team_id] / denominator for team_id in active}
        capped = sorted(team_id for team_id, value in provisional.items() if value > cap)
        if not capped:
            for team_id, value in provisional.items():
                weights[team_id] += value
            remaining = 0.0
            break
        for team_id in capped:
            allocation = cap - weights[team_id]
            weights[team_id] = cap
            remaining -= allocation
            active.remove(team_id)
    cash = max(0.0, 1.0 - sum(weights.values()))
    return {team_id: float(weights[team_id]) for team_id in sorted(weights)}, float(cash)


def close_is(root: str | Path) -> Mapping[str, Any]:
    root_path = _safe_root(root)
    with _result_lock(root_path):
        activation = activation_v4.validate(root_path)
        loaded = top40_v4.load_config(root=root_path)
        state = _close_interrupted_is_requests(root_path)
        _write_nomination_registry(root_path, state)
        if state.selection is not None:
            freeze = _selection_freeze(root_path, state)
            return {
                "ok": True,
                "already_frozen": True,
                "advancing": [str(row["team_id"]) for row in freeze["advancing"]],
                "selection_freeze_path": state.selection["selection_freeze_path"],
            }
        if set(state.nominations) | set(state.retired) != set(TOP40_V4_LAYOUT.team_ids):
            unresolved = sorted(
                set(TOP40_V4_LAYOUT.team_ids) - set(state.nominations) - set(state.retired)
            )
            raise OrchestratorError(f"IS cannot close while teams are unresolved: {unresolved}")
        population: list[Mapping[str, Any]] = []
        for team_id, record in sorted(state.nominations.items()):
            nomination = _verified_nomination(root_path, record)
            if not nomination["selection"]["eligible"]:
                raise OrchestratorError("nomination registry contains an ineligible candidate")
            population.append(nomination)
        population.sort(key=lambda row: scoring_v4.is_ranking_key(row["selection"]))
        advance_count = int(loaded.raw["selection"]["ranking"]["advance_count"])
        finalists = population[:advance_count]
        advancing = [str(row["team_id"]) for row in finalists]
        weights, cash_weight = _capped_inverse_vol_weights(
            root_path,
            finalists,
            float(loaded.raw["ensemble"]["maximum_constituent_weight"]),
        )
        freeze = {
            "schema_version": "top40-v4-r1-selection-freeze-v1",
            "tournament": TOP40_V4_LAYOUT.name,
            "input_journal_head_sha256": state.head_sha256,
            "config_sha256": loaded.sha256,
            "activation_record_sha256": activation["record_sha256"],
            "population": [
                {
                    "rank": rank,
                    "team_id": row["team_id"],
                    "candidate_id": row["candidate_id"],
                    "nomination_sha256": state.nominations[row["team_id"]]["payload"][
                        "nomination_sha256"
                    ],
                    "selection": row["selection"],
                }
                for rank, row in enumerate(population, start=1)
            ],
            "retired": sorted(state.retired),
            "advancing": [
                {
                    "rank": rank,
                    "team_id": row["team_id"],
                    "candidate_id": row["candidate_id"],
                    "authority": row["authority"],
                    "trial_count": row["trial_count"],
                    "nomination_path": state.nominations[row["team_id"]]["payload"][
                        "nomination_path"
                    ],
                    "nomination_sha256": state.nominations[row["team_id"]]["payload"][
                        "nomination_sha256"
                    ],
                }
                for rank, row in enumerate(finalists, start=1)
            ],
            "ensemble": {
                "method": loaded.raw["ensemble"]["weight_method"],
                "constituent_weights": weights,
                "cash_weight": cash_weight,
                "failed_constituent_weight": "cash-no-redistribution",
                "oos_reweighting_allowed": False,
            },
        }
        freeze_payload = _pretty(freeze)
        freeze_sha256 = _write_atomic(
            root_path,
            TOP40_V4_LAYOUT.selection_freeze_path,
            freeze_payload,
            replace=False,
        )
        record = journal_v4.append(
            _journal_path(root_path),
            "selection_frozen",
            {
                "input_head_sha256": state.head_sha256,
                "advancing": advancing,
                "selection_freeze_path": TOP40_V4_LAYOUT.selection_freeze_path,
                "selection_freeze_sha256": freeze_sha256,
            },
        )
        return {
            "ok": True,
            "advancing": advancing,
            "ensemble": freeze["ensemble"],
            "selection_freeze_path": TOP40_V4_LAYOUT.selection_freeze_path,
            "selection_record_sha256": record["record_sha256"],
        }


def _selection_freeze(root: Path, state: journal_v4.JournalState) -> Mapping[str, Any]:
    if state.selection is None:
        raise OrchestratorError("IS selection has not been frozen")
    relative = str(state.selection["selection_freeze_path"])
    path = _path(root, relative)
    payload = _stable_authority_bytes(path)
    if _sha256(payload) != state.selection["selection_freeze_sha256"]:
        raise OrchestratorError("selection freeze changed after journal binding")
    result = _strict_object_bytes(payload, relative)
    if [row["team_id"] for row in result["advancing"]] != list(state.selection["advancing"]):
        raise OrchestratorError("selection freeze finalist order differs from the journal")
    return result


def _historical_summary_for_team(
    root: Path, state: journal_v4.JournalState, team_id: str
) -> Mapping[str, Any] | None:
    terminal = state.historical_terminals[team_id]
    if terminal["event_type"] == "historical_failed":
        return None
    return _verified_summary(root, terminal)


def _verified_finalist_packet(
    root: Path,
    state: journal_v4.JournalState,
    team_id: str,
    terminal: Mapping[str, Any],
    summary: Mapping[str, Any],
) -> tuple[tuple[Path, str, int, str], ...]:
    request = state.historical_requests[team_id]["payload"]
    output_relative = str(request["output_path"])
    summary_relative = str(terminal["payload"]["summary_path"])
    if summary_relative != f"{output_relative}/summary.json":
        raise OrchestratorError("historical summary is outside its accepted output directory")
    source = _path(root, output_relative)
    if not source.is_dir() or source.is_symlink():
        raise OrchestratorError("private finalist artifact directory is missing or unsafe")
    runner = summary.get("runner")
    if (
        not isinstance(runner, Mapping)
        or runner.get("team_id") != team_id
        or runner.get("stage") != "historical_oos"
        or runner.get("output_dir") != output_relative
    ):
        raise OrchestratorError("historical summary runner identity is invalid")
    artifacts = runner.get("artifacts")
    hashes = runner.get("artifact_sha256")
    sizes = runner.get("artifact_sizes")
    required = set(_RELEASE_ARTIFACT_FILES)
    if (
        not isinstance(artifacts, Mapping)
        or not isinstance(hashes, Mapping)
        or not isinstance(sizes, Mapping)
        or set(artifacts) != required
        or set(hashes) != required
        or set(sizes) != required
    ):
        raise OrchestratorError("historical summary artifact authority is incomplete")
    expected_names = set(_RELEASE_ARTIFACT_FILES.values()) | {"summary.json"}
    actual_names: set[str] = set()
    for path in source.iterdir():
        if path.is_symlink() or not path.is_file():
            raise OrchestratorError("private finalist directory contains an unsafe node")
        actual_names.add(path.name)
    if actual_names != expected_names:
        raise OrchestratorError("private finalist directory differs from the exact allowlist")
    packet: list[tuple[Path, str, int, str]] = []
    for logical_name, filename in _RELEASE_ARTIFACT_FILES.items():
        expected_relative = f"{output_relative}/{filename}"
        size = sizes[logical_name]
        digest = hashes[logical_name]
        if (
            artifacts[logical_name] != expected_relative
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size < 0
            or not isinstance(digest, str)
            or _SHA256.fullmatch(digest) is None
        ):
            raise OrchestratorError("historical artifact authority is malformed")
        path = _path(root, expected_relative)
        if (
            not path.is_file()
            or path.is_symlink()
            or path.stat().st_size != size
            or _sha256_file(path) != digest
        ):
            raise OrchestratorError("historical artifact changed after terminal success")
        packet.append((path, filename, size, digest))
    summary_path = _path(root, summary_relative)
    summary_digest = str(terminal["payload"]["summary_sha256"])
    packet.append((summary_path, "summary.json", summary_path.stat().st_size, summary_digest))
    return tuple(packet)


def _copy_verified_packet(packet: Sequence[tuple[Path, str, int, str]], destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for source, filename, size, digest in packet:
        target = destination / filename
        shutil.copyfile(source, target, follow_symlinks=False)
        if target.stat().st_size != size or _sha256_file(target) != digest:
            raise OrchestratorError("historical artifact changed while staging release")


def _write_stage_file(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        if handle.write(payload) != len(payload):
            raise OSError("short staging write")
        handle.flush()
        os.fsync(handle.fileno())


def _fsync_tree(directory: Path) -> None:
    """Durably flush every release file and directory before the atomic rename."""

    directories = [directory]
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise OrchestratorError("release staging contains a symlink")
        if path.is_file():
            descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        elif path.is_dir():
            directories.append(path)
        else:
            raise OrchestratorError("release staging contains a non-regular node")
    for path in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        _fsync_directory(path)


def _metrics_dict(values: pd.Series) -> dict[str, float]:
    result = metrics_v3.compute_window_metrics(values)
    return {field.name: float(getattr(result, field.name)) for field in dataclasses.fields(result)}


def _ensemble_release(
    root: Path,
    staging: Path,
    selection: Mapping[str, Any],
    state: journal_v4.JournalState,
) -> Mapping[str, Any]:
    oos_index = pd.date_range(
        "2024-07-01T00:00:00Z",
        "2026-07-01T00:00:00Z",
        inclusive="left",
        freq="1D",
    )
    weights = selection["ensemble"]["constituent_weights"]
    scenarios = {
        "base": "daily_returns",
        "double_cost": "double_cost_daily_returns",
        "triple_cost": "triple_cost_daily_returns",
    }
    packet: dict[str, Any] = {
        "schema_version": "top40-v4-r1-historical-oos-ensemble-v1",
        "role": "additional-reporting-portfolio",
        "constituent_weights": weights,
        "cash_weight": selection["ensemble"]["cash_weight"],
        "failed_constituent_weight": "cash-no-redistribution",
        "winner_eligible": False,
        "scenarios": {},
    }
    for scenario, artifact_name in scenarios.items():
        weighted: pd.Series | None = None
        for team_id, raw_weight in weights.items():
            summary = _historical_summary_for_team(root, state, team_id)
            if summary is None:
                continue
            relative = summary["runner"]["artifacts"][artifact_name]
            expected = summary["runner"]["artifact_sha256"][artifact_name]
            artifact = _path(root, str(relative))
            artifact_payload = _stable_authority_bytes(artifact)
            if _sha256(artifact_payload) != expected:
                raise OrchestratorError("historical sleeve artifact changed before release")
            frame = pd.read_csv(io.BytesIO(artifact_payload))
            if list(frame.columns) != ["date", "net_return"]:
                raise OrchestratorError("historical sleeve daily-return schema changed")
            index = pd.DatetimeIndex(pd.to_datetime(frame["date"], utc=True, errors="coerce"))
            values = pd.to_numeric(frame["net_return"], errors="coerce")
            if (
                index.hasnans
                or index.duplicated().any()
                or not index.is_monotonic_increasing
                or values.isna().any()
                or not np.isfinite(values.to_numpy(dtype=float)).all()
            ):
                raise OrchestratorError("historical sleeve daily returns are invalid")
            series = pd.Series(values.to_numpy(dtype=float), index=index).reindex(oos_index)
            if series.isna().any():
                raise OrchestratorError("historical sleeve does not cover the exact OOS window")
            contribution = float(raw_weight) * series
            weighted = (
                contribution if weighted is None else weighted.add(contribution, fill_value=0.0)
            )
        if weighted is None:
            weighted = pd.Series(0.0, index=oos_index)
        if not weighted.index.equals(oos_index):
            raise OrchestratorError("historical ensemble does not match the exact OOS window")
        frame = pd.DataFrame(
            {
                "date": weighted.index,
                "net_return": weighted.to_numpy(dtype=float),
            }
        )
        relative = f"ensemble/{scenario}_daily_returns.csv"
        _write_stage_file(staging / relative, frame.to_csv(index=False).encode("utf-8"))
        packet["scenarios"][scenario] = {
            "cumulative_return": float((1.0 + weighted).prod() - 1.0),
            "metrics": _metrics_dict(weighted),
            "daily_returns_path": relative,
        }
    _write_stage_file(staging / "ensemble/result.json", _pretty(packet))
    return packet


def _release_bundle(
    root: Path,
    selection: Mapping[str, Any],
    state: journal_v4.JournalState,
) -> tuple[str, str, str]:
    reports_root = _path(root, TOP40_V4_LAYOUT.reports_root)
    _ensure_directory(root, reports_root)
    staging_relative = f"{TOP40_V4_LAYOUT.reports_root}/.historical-oos-staging"
    staging = _path(root, staging_relative)
    release_relative = f"{TOP40_V4_LAYOUT.reports_root}/historical-oos"
    release = _path(root, release_relative)
    if release.exists():
        raise OrchestratorError("historical OOS release path already exists without authorization")
    temporary = Path(tempfile.mkdtemp(prefix=".historical-oos-build-", dir=reports_root))
    try:
        packets: dict[str, Mapping[str, Any] | None] = {}
        for finalist in selection["advancing"]:
            team_id = str(finalist["team_id"])
            terminal = state.historical_terminals[team_id]
            team_destination = temporary / "teams" / team_id
            if terminal["event_type"] == "historical_succeeded":
                summary = _verified_summary(root, terminal)
                packets[team_id] = summary
                packet = _verified_finalist_packet(root, state, team_id, terminal, summary)
                _copy_verified_packet(packet, team_destination)
            else:
                packets[team_id] = None
                _write_stage_file(
                    team_destination / "result.json",
                    _pretty(
                        {
                            "schema_version": "top40-v4-r1-historical-oos-dnf-v1",
                            "team_id": team_id,
                            "candidate_id": finalist["candidate_id"],
                            "status": "DNF",
                        }
                    ),
                )
        ensemble = _ensemble_release(root, temporary, selection, state)
        eligible = [
            packet
            for packet in packets.values()
            if packet is not None and packet["championship"]["winner_eligible"]
        ]
        eligible.sort(key=lambda packet: scoring_v4.historical_ranking_key(packet["championship"]))
        winner = None
        if eligible:
            winner = {
                "team_id": eligible[0]["team_id"],
                "candidate_id": eligible[0]["candidate_id"],
                "championship": eligible[0]["championship"],
            }
        file_entries: list[dict[str, Any]] = []
        for path in sorted(temporary.rglob("*"), key=lambda item: item.as_posix()):
            if path.is_file():
                relative = path.relative_to(temporary).as_posix()
                file_entries.append(
                    {"path": relative, "size": path.stat().st_size, "sha256": _sha256_file(path)}
                )
        bundle_sha256 = _sha256(_canonical({"files": file_entries}))
        manifest = {
            "schema_version": "top40-v4-r1-historical-oos-release-v1",
            "evidence_label": "candidate-relative-historical-oos-not-globally-pristine",
            "window": {"start": "2024-07-01T00:00:00Z", "end_exclusive": "2026-07-01T00:00:00Z"},
            "selection_record_sha256": state.selection_record_sha256,
            "terminal_record_sha256s": [
                state.historical_terminals[row["team_id"]]["record_sha256"]
                for row in selection["advancing"]
            ],
            "finalists": [
                {
                    "rank": row["rank"],
                    "team_id": row["team_id"],
                    "candidate_id": row["candidate_id"],
                    "status": "succeeded" if packets[row["team_id"]] is not None else "DNF",
                    "championship": packets[row["team_id"]]["championship"]
                    if packets[row["team_id"]] is not None
                    else None,
                }
                for row in selection["advancing"]
            ],
            "winner": winner,
            "ensemble": ensemble,
            "files": file_entries,
            "bundle_sha256": bundle_sha256,
        }
        manifest_payload = _pretty(manifest)
        _write_stage_file(temporary / "manifest.json", manifest_payload)
        manifest_sha256 = _sha256(manifest_payload)
        _fsync_tree(temporary)
        if staging.exists() and not staging.is_dir():
            raise OrchestratorError("historical OOS staging path is not a directory")
        if staging.exists():
            shutil.rmtree(staging)
        os.replace(temporary, staging)
        _fsync_directory(reports_root)
        return staging_relative, release_relative, manifest_sha256
    finally:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)


def _validate_staged_release(
    root: Path,
    relative: str,
    *,
    manifest_sha256: str,
    bundle_sha256: str,
) -> None:
    directory = _path(root, relative)
    manifest_path = directory / "manifest.json"
    if (
        not directory.is_dir()
        or directory.is_symlink()
        or not manifest_path.is_file()
        or manifest_path.is_symlink()
    ):
        raise OrchestratorError("authorized historical release bundle is missing")
    manifest_payload = _stable_authority_bytes(manifest_path)
    if _sha256(manifest_payload) != manifest_sha256:
        raise OrchestratorError("authorized historical release manifest changed")
    manifest = _strict_object_bytes(manifest_payload, f"{relative}/manifest.json")
    if manifest.get("bundle_sha256") != bundle_sha256:
        raise OrchestratorError("authorized historical release bundle identity changed")
    raw_files = manifest.get("files")
    if not isinstance(raw_files, list):
        raise OrchestratorError("authorized historical release inventory is malformed")
    entries: list[dict[str, Any]] = []
    listed_paths: set[str] = set()
    for row in raw_files:
        if not isinstance(row, Mapping) or set(row) != {"path", "size", "sha256"}:
            raise OrchestratorError("authorized historical release inventory is malformed")
        row_path = row["path"]
        pure = PurePosixPath(row_path) if isinstance(row_path, str) else None
        if (
            pure is None
            or pure.is_absolute()
            or any(part in {"", ".", ".."} for part in pure.parts)
            or row_path in listed_paths
            or isinstance(row["size"], bool)
            or not isinstance(row["size"], int)
            or row["size"] < 0
            or not isinstance(row["sha256"], str)
            or _SHA256.fullmatch(row["sha256"]) is None
        ):
            raise OrchestratorError("authorized historical release inventory has duplicate paths")
        listed_paths.add(row_path)
        path = _path(root, f"{relative}/{row_path}")
        if (
            not path.is_file()
            or path.is_symlink()
            or path.stat().st_size != row["size"]
            or _sha256_file(path) != row["sha256"]
        ):
            raise OrchestratorError("authorized historical release file changed")
        entries.append(dict(row))
    actual_paths: set[str] = set()
    for path in directory.rglob("*"):
        if path.is_symlink() or (not path.is_file() and not path.is_dir()):
            raise OrchestratorError("authorized historical release contains an unsafe node")
        if path.is_file():
            actual_paths.add(path.relative_to(directory).as_posix())
    if actual_paths != listed_paths | {"manifest.json"}:
        raise OrchestratorError("authorized historical release has unlisted or missing files")
    if _sha256(_canonical({"files": entries})) != bundle_sha256:
        raise OrchestratorError("authorized historical release file inventory changed")


def _promote_authorized(root: Path, release: Mapping[str, Any]) -> Mapping[str, Any]:
    staging = str(release["staging_path"])
    public = str(release["release_path"])
    public_path = _path(root, public)
    if public_path.exists():
        _validate_staged_release(
            root,
            public,
            manifest_sha256=str(release["manifest_sha256"]),
            bundle_sha256=str(release["bundle_sha256"]),
        )
        return {"ok": True, "release_path": public, "recovered": True}
    _validate_staged_release(
        root,
        staging,
        manifest_sha256=str(release["manifest_sha256"]),
        bundle_sha256=str(release["bundle_sha256"]),
    )
    os.replace(_path(root, staging), public_path)
    _fsync_directory(public_path.parent)
    return {"ok": True, "release_path": public, "recovered": False}


def _recover_authorized_release(
    root: Path,
    selection: Mapping[str, Any],
    state: journal_v4.JournalState,
) -> Mapping[str, Any]:
    if state.release is None:
        raise OrchestratorError("historical release recovery has no authorization")
    public = _path(root, str(state.release["release_path"]))
    if public.exists():
        return _promote_authorized(root, state.release)
    try:
        return _promote_authorized(root, state.release)
    except OrchestratorError:
        # If a crash lost only the private staging tree, rebuild it deterministically from the
        # journal-bound finalist packets and require byte-identical authorization hashes.
        staging, release, manifest_sha256 = _release_bundle(root, selection, state)
        manifest = _strict_object(root, f"{staging}/manifest.json")
        if (
            staging != state.release["staging_path"]
            or release != state.release["release_path"]
            or manifest_sha256 != state.release["manifest_sha256"]
            or manifest.get("bundle_sha256") != state.release["bundle_sha256"]
        ):
            raise OrchestratorError(
                "rebuilt historical release differs from its durable authorization"
            )
        _validate_staged_release(
            root,
            staging,
            manifest_sha256=manifest_sha256,
            bundle_sha256=str(manifest["bundle_sha256"]),
        )
        result = _promote_authorized(root, state.release)
        result["recovered"] = True
        return result


def historical_release(root: str | Path) -> Mapping[str, Any]:
    """Consume each finalist once, then authorize and atomically publish the complete bundle."""

    root_path = _safe_root(root)
    with _result_lock(root_path):
        # Validate frozen code without opening the time-varying snapshot. Every finalist identity
        # is durably accepted below before the first full universe audit or runner invocation.
        activation_v4.validate(root_path, verify_universe_snapshot=False)
        loaded = top40_v4.load_config(root=root_path)
        state = journal_v4.read(_journal_path(root_path))
        selection = _selection_freeze(root_path, state)
        if state.release is not None:
            result = _recover_authorized_release(root_path, selection, state)
            result["manifest_sha256"] = state.release["manifest_sha256"]
            return result

        # Phase 1 is data-blind and batch-accepts every frozen identity. A crash during this loop
        # leaves unstarted requests, which can safely resume after the missing acceptances land.
        for finalist in selection["advancing"]:
            team_id = str(finalist["team_id"])
            if team_id in state.historical_requests:
                continue
            authority = CandidateAuthority(**dict(finalist["authority"]))
            run_id = (
                f"{team_id.replace('-', '')}-historical-oos-{authority.source_bundle_sha256[:12]}"
            )
            output = f"{TOP40_V4_LAYOUT.tournament_root}/private/historical-oos/{team_id}/{run_id}"
            journal_v4.append(
                _journal_path(root_path),
                "historical_accepted",
                {
                    "team_id": team_id,
                    "candidate_id": authority.candidate_id,
                    "run_id": run_id,
                    "selection_record_sha256": state.selection_record_sha256,
                    "output_path": output,
                },
            )
            state = journal_v4.read(_journal_path(root_path))

        expected_finalists = {str(finalist["team_id"]) for finalist in selection["advancing"]}
        if set(state.historical_requests) != expected_finalists:
            raise OrchestratorError("not every finalist identity was durably accepted")

        # Only a started request can have touched the sealed snapshot. Interrupted starts are
        # terminal DNFs; accepted-but-unstarted finalists retain their one authorized observation.
        for team_id in list(state.historical_starts):
            if team_id in state.historical_terminals:
                continue
            request = state.historical_requests[team_id]
            event = request["payload"]
            journal_v4.append(
                _journal_path(root_path),
                "historical_failed",
                {
                    "team_id": team_id,
                    "candidate_id": event["candidate_id"],
                    "run_id": event["run_id"],
                    "request_sha256": request["record_sha256"],
                    "failure_code": "interrupted-after-started-observation",
                },
            )
        state = journal_v4.read(_journal_path(root_path))

        # This is the first snapshot-reading operation in the command, after all identities exist.
        activation_v4.validate(root_path)

        for finalist in selection["advancing"]:
            team_id = str(finalist["team_id"])
            if team_id in state.historical_terminals:
                continue
            authority = CandidateAuthority(**dict(finalist["authority"]))
            request = state.historical_requests[team_id]
            event = request["payload"]
            run_id = str(event["run_id"])
            output = str(event["output_path"])
            journal_v4.append(
                _journal_path(root_path),
                "historical_started",
                {
                    "team_id": team_id,
                    "candidate_id": authority.candidate_id,
                    "run_id": run_id,
                    "request_sha256": request["record_sha256"],
                },
            )
            try:
                authority = _validate_authority_current(root_path, loaded, finalist["authority"])
                result = _run_team(root_path, authority, stage="historical_oos", output=output)
                summary = scoring_v4.summarize_run(
                    root_path,
                    result,
                    loaded.raw,
                    trial_count=int(finalist["trial_count"]),
                )
                summary["candidate_id"] = authority.candidate_id
                summary["run_id"] = run_id
                summary_path = f"{output}/summary.json"
                summary_payload = _pretty(summary)
                summary_sha256 = _write_atomic(
                    root_path, summary_path, summary_payload, replace=False
                )
                journal_v4.append(
                    _journal_path(root_path),
                    "historical_succeeded",
                    {
                        "team_id": team_id,
                        "candidate_id": authority.candidate_id,
                        "run_id": run_id,
                        "request_sha256": request["record_sha256"],
                        "summary_path": summary_path,
                        "summary_sha256": summary_sha256,
                    },
                )
            except BaseException as exc:
                journal_v4.append(
                    _journal_path(root_path),
                    "historical_failed",
                    {
                        "team_id": team_id,
                        "candidate_id": authority.candidate_id,
                        "run_id": run_id,
                        "request_sha256": request["record_sha256"],
                        "failure_code": "candidate-execution-dnf",
                    },
                )
                if not isinstance(exc, Exception):
                    raise
            state = journal_v4.read(_journal_path(root_path))

        staging, release, manifest_sha256 = _release_bundle(root_path, selection, state)
        manifest = _strict_object(root_path, f"{staging}/manifest.json")
        _validate_staged_release(
            root_path,
            staging,
            manifest_sha256=manifest_sha256,
            bundle_sha256=str(manifest["bundle_sha256"]),
        )
        authorization = journal_v4.append(
            _journal_path(root_path),
            "release_authorized",
            {
                "selection_record_sha256": state.selection_record_sha256,
                "terminal_record_sha256s": [
                    state.historical_terminals[row["team_id"]]["record_sha256"]
                    for row in selection["advancing"]
                ],
                "staging_path": staging,
                "release_path": release,
                "manifest_sha256": manifest_sha256,
                "bundle_sha256": manifest["bundle_sha256"],
            },
        )
        promoted = _promote_authorized(root_path, authorization["payload"])
        promoted.update(
            {
                "manifest_sha256": manifest_sha256,
                "winner": manifest["winner"],
                "finalist_count": len(selection["advancing"]),
            }
        )
        return promoted


__all__ = [
    "CandidateAuthority",
    "OrchestratorError",
    "ResultCommandBusyError",
    "activate",
    "close_is",
    "historical_release",
    "nominate",
    "retire",
    "run_is",
    "status",
    "validate",
]
