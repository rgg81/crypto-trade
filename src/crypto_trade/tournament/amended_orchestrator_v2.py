"""Amendment-aware adapter for the byte-frozen Top-40 V2 orchestrator.

The Phase-0 orchestrator remains the sole implementation of ordinary tournament commands.
This module loads those reviewed bytes, replaces only their state/config I/O boundary, and
publishes each legacy schema-2 projection change inside the amendment's recoverable schema-3
transaction.  It never rewrites a Phase-0-frozen file.
"""

from __future__ import annotations

import argparse
import contextlib
import contextvars
import copy
import hashlib
import json
import os
import stat
import sys
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

from crypto_trade.tournament.amendment_integrity_v2 import TransactionChange
from crypto_trade.tournament.amendment_v2 import (
    LEGACY_STATE_KEYS,
    amendment_aware_legacy_state_edit,
    assert_operation_permitted,
    effective_research_deadline,
    read_amended_state,
    read_amendment_aware_legacy_state,
)
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.top40_v2 import LoadedV2Config, load_config, validate_run_state

_FORBIDDEN_LEGACY_COMMANDS = frozenset({"init-teams", "freeze-phase0"})
_READ_ONLY_LEGACY_COMMANDS = frozenset(
    {"validate-config", "validate-risk-policy", "research-status", "verify-winner-freeze"}
)
_ACTIVE_STAGING: contextvars.ContextVar[_StagedWrites | None] = contextvars.ContextVar(
    "top40_v2_amended_staging",
    default=None,
)


def _legacy_projection(state: Mapping[str, Any]) -> dict[str, Any]:
    projection = {key: copy.deepcopy(state[key]) for key in LEGACY_STATE_KEYS}
    projection["schema_version"] = 2
    return projection


def _canonical_config(root: Path, value: str | Path) -> LoadedV2Config:
    candidate = Path(value)
    path = (candidate if candidate.is_absolute() else root / candidate).resolve()
    expected = (root / TOP40_V2_LAYOUT.config_path).resolve()
    if path != expected:
        raise ValueError(f"amended orchestration requires {TOP40_V2_LAYOUT.config_path}")
    return load_config(path)


def _effective_config(
    config: LoadedV2Config,
    state: Mapping[str, Any],
) -> LoadedV2Config:
    raw = copy.deepcopy(dict(config.raw))
    research = raw.get("research_budget")
    if not isinstance(research, dict):
        raise ValueError("canonical research budget is not mutable in the adapter copy")
    research["deadline_utc"] = (
        effective_research_deadline(state).isoformat().replace("+00:00", "Z")
    )
    return LoadedV2Config(path=config.path, sha256=config.sha256, raw=raw)


def _load_frozen_orchestrator(root: Path) -> ModuleType:
    path = (root / TOP40_V2_LAYOUT.orchestrator_script).resolve()
    if not path.is_relative_to(root) or not path.is_file() or path.is_symlink():
        raise ValueError("frozen V2 orchestrator is missing or unsafe")
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()[:16]
    name = f"_crypto_trade_top40_v2_frozen_{digest}"
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    exec(compile(payload, str(path), "exec"), module.__dict__)
    return module


class _StagedWrites:
    """Overlay legacy file writes until the amendment transaction publishes them."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.changes: list[TransactionChange] = []
        self._indices: dict[Path, int] = {}
        self._replacement: dict[Path, bytes] = {}

    def _path(self, raw: str | Path) -> Path:
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        candidate = Path(os.path.abspath(candidate))
        if not candidate.is_relative_to(self.root):
            raise ValueError("legacy staged write escapes the tournament worktree")
        current = self.root
        for part in candidate.relative_to(self.root).parts[:-1]:
            current /= part
            try:
                info = os.lstat(current)
            except FileNotFoundError:
                os.mkdir(current, 0o755)
                info = os.lstat(current)
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise ValueError("legacy staged-write parent is unsafe")
        return candidate

    @staticmethod
    def _disk_bytes(path: Path, label: str) -> bytes:
        try:
            descriptor = os.open(
                path,
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0),
            )
        except OSError as exc:
            raise ValueError(f"{label} is missing or unsafe: {exc}") from exc
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError(f"{label} must be a regular single-link file")
            chunks: list[bytes] = []
            remaining = info.st_size
            while remaining:
                chunk = os.read(descriptor, min(remaining, 1024 * 1024))
                if not chunk:
                    raise ValueError(f"{label} changed while read")
                chunks.append(chunk)
                remaining -= len(chunk)
            if os.read(descriptor, 1):
                raise ValueError(f"{label} grew while read")
            return b"".join(chunks)
        finally:
            os.close(descriptor)

    def read(self, raw: str | Path, label: str) -> bytes:
        path = self._path(raw)
        replacement = self._replacement.get(path)
        return replacement if replacement is not None else self._disk_bytes(path, label)

    def write(self, raw: str | Path, payload: bytes) -> None:
        if not isinstance(payload, bytes):
            raise TypeError("legacy staged writes require bytes")
        path = self._path(raw)
        index = self._indices.get(path)
        if index is None:
            if path.exists() or path.is_symlink():
                expected = self._disk_bytes(path, "legacy transaction input")
            else:
                expected = None
            index = len(self.changes)
            self._indices[path] = index
            self.changes.append(TransactionChange(path, expected, payload))
        else:
            original = self.changes[index]
            self.changes[index] = TransactionChange(path, original.expected, payload)
        self._replacement[path] = payload


@contextlib.contextmanager
def _patch_legacy_module(
    legacy: ModuleType,
    *,
    root: Path,
    config: LoadedV2Config,
    effective_config: LoadedV2Config,
    operation: str,
) -> Iterator[None]:
    original = {
        name: getattr(legacy, name)
        for name in (
            "_atomic_write_bytes",
            "_config",
            "_edit_state",
            "_read_json",
            "_safe_regular_bytes",
            "read_run_state",
        )
    }

    def patched_config(candidate_root: Path, value: str | Path) -> LoadedV2Config:
        if Path(candidate_root).resolve() != root:
            raise ValueError("legacy command changed the tournament root")
        loaded = _canonical_config(root, value)
        if loaded.sha256 != config.sha256:
            raise ValueError("legacy command changed the canonical config")
        return effective_config

    def patched_read_run_state(
        candidate_root: str | Path,
        _candidate_config: LoadedV2Config,
    ) -> dict[str, Any]:
        if Path(candidate_root).resolve() != root:
            raise ValueError("legacy state read changed the tournament root")
        projection = read_amendment_aware_legacy_state(
            root,
            config,
            operation=operation,
        )
        validate_run_state(projection, config)
        return projection

    @contextlib.contextmanager
    def patched_edit_state(
        candidate_root: Path,
        _candidate_config: LoadedV2Config,
    ) -> Iterator[dict[str, Any]]:
        if Path(candidate_root).resolve() != root:
            raise ValueError("legacy state edit changed the tournament root")
        if _ACTIVE_STAGING.get() is not None:
            raise ValueError("nested legacy state edits are forbidden")
        current = read_amended_state(root, config)
        assert_operation_permitted(current, operation)
        staging = _StagedWrites(root)
        token = _ACTIVE_STAGING.set(staging)
        try:
            if current["administrative_hold"]["active"] is True:
                if operation not in _READ_ONLY_LEGACY_COMMANDS:
                    raise ValueError("the administrative hold blocks legacy state mutation")
                projection = _legacy_projection(current)
                baseline = copy.deepcopy(projection)
                yield projection
                if projection != baseline or staging.changes:
                    raise ValueError("read-only legacy command attempted a held-state mutation")
                validate_run_state(projection, config)
            else:
                with amendment_aware_legacy_state_edit(
                    root,
                    config,
                    operation=operation,
                    staged_changes=staging.changes,
                ) as projection:
                    yield projection
        finally:
            _ACTIVE_STAGING.reset(token)

    def patched_write(path: Path, payload: bytes) -> None:
        staging = _ACTIVE_STAGING.get()
        if staging is None:
            original["_atomic_write_bytes"](path, payload)
        else:
            staging.write(path, payload)

    def patched_safe_bytes(path: Path, label: str) -> bytes:
        staging = _ACTIVE_STAGING.get()
        return (
            original["_safe_regular_bytes"](path, label)
            if staging is None
            else staging.read(path, label)
        )

    def patched_read_json(path: str | Path, label: str) -> tuple[dict[str, Any], bytes]:
        staging = _ACTIVE_STAGING.get()
        if staging is None:
            return original["_read_json"](path, label)
        payload = staging.read(path, label)
        try:
            raw = json.loads(payload.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid {label}: {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError(f"{label} root must be a JSON object")
        return raw, payload

    replacements = {
        "_atomic_write_bytes": patched_write,
        "_config": patched_config,
        "_edit_state": patched_edit_state,
        "_read_json": patched_read_json,
        "_safe_regular_bytes": patched_safe_bytes,
        "read_run_state": patched_read_run_state,
    }
    try:
        for name, value in replacements.items():
            setattr(legacy, name, value)
        yield
    finally:
        for name, value in original.items():
            setattr(legacy, name, value)


def _dispatch(legacy: ModuleType, args: argparse.Namespace) -> int:
    commands = {
        "validate-config": legacy._validate_config_command,
        "validate-risk-policy": legacy._validate_risk_policy,
        "assess-qualification": legacy._assess_qualification,
        "register-family": lambda value: legacy._register_family(value, pivot=False),
        "pivot-team": lambda value: legacy._register_family(value, pivot=True),
        "register-trial": legacy._register_trial,
        "record-trial-result": legacy._record_trial_result,
        "research-status": legacy._research_status,
        "run-window": legacy._run_window,
        "record-development-assessment": legacy._record_development_assessment,
        "record-private-assessment": legacy._record_private_assessment,
        "withdraw-team": legacy._withdraw_team,
        "close-qualification": legacy._close_qualification,
        "lock-finalist-cohort": legacy._lock_finalist_cohort,
        "run-finalist": legacy._run_finalist,
        "lock-final-oos": legacy._lock_final_oos,
        "lock-objective": legacy._lock_objective,
        "lock-critic": legacy._lock_critic,
        "lock-critic-confirmations": legacy._lock_critic_confirmations,
        "lock-user-ballot": legacy._lock_user_ballot,
        "lock-selection": legacy._lock_selection,
        "freeze-winner": legacy._freeze_winner,
        "verify-winner-freeze": legacy._verify_winner_freeze,
    }
    command = str(args.command)
    if command in _FORBIDDEN_LEGACY_COMMANDS or command not in commands:
        raise ValueError(f"{command!r} is unavailable through amended orchestration")
    return int(commands[command](args))


def run(argv: Sequence[str] | None = None, *, root: str | Path | None = None) -> int:
    working_root = Path.cwd().resolve()
    root_path = working_root if root is None else Path(root).resolve()
    if root_path != working_root:
        raise ValueError("amended orchestration root must be the current working directory")
    # Validate the full amendment and Phase-0 authority before executing any byte of the
    # dynamically loaded legacy orchestrator. The canonical config is fixed by the layout.
    config = _canonical_config(root_path, TOP40_V2_LAYOUT.config_path)
    state = read_amended_state(root_path, config)
    legacy = _load_frozen_orchestrator(root_path)
    parser = legacy.build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if getattr(args, "json_out", None) is not None:
        raise ValueError("amended orchestration writes JSON to stdout only")
    config_value = getattr(args, "config", TOP40_V2_LAYOUT.config_path)
    requested_config = _canonical_config(root_path, config_value)
    if requested_config.sha256 != config.sha256:
        raise ValueError("amended command changed the canonical config binding")
    command = str(args.command)
    if command in _FORBIDDEN_LEGACY_COMMANDS:
        raise ValueError(f"{command!r} cannot run after Phase 0")
    assert_operation_permitted(state, command)
    adapted_config = _effective_config(config, state)
    with _patch_legacy_module(
        legacy,
        root=root_path,
        config=config,
        effective_config=adapted_config,
        operation=command,
    ):
        return _dispatch(legacy, args)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"top40-v2-amended: error: {exc}", file=sys.stderr)
        return 2
