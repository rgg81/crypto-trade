"""Additive read-only compatibility layer for the frozen Top-40 V2 adapter.

Amendment 0001's adapter correctly transactions result-bearing legacy commands, but after
the administrative hold resumed it routed legacy read-only commands that happen to open
``_edit_state`` through the result-bearing transaction API. That API deliberately rejects
read-only operations. This module executes a fresh, hash-pinned copy of the frozen adapter and
replaces only that private copy's state-edit binding for the duration of one command.
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import os
import stat
import sys
import tempfile
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from crypto_trade.tournament.amendment_integrity_v2 import (
    TransactionChange,
    UtcClock,
    system_utc_now,
)
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.top40_v2 import LoadedV2Config

_FROZEN_ADAPTER_SHA256 = "89ebd52bf5f0552476745605fb92c9665eef1668c2212ab62d5e8c03f577d172"
_READ_ONLY_OPERATIONS = frozenset(
    {"validate-config", "validate-risk-policy", "research-status", "verify-winner-freeze"}
)
_TEAM_LEDGER_NAMES = frozenset({"experiments.jsonl", "families.jsonl"})


@dataclass(frozen=True)
class _FileImage:
    payload: bytes
    mode: int


def _regular_bytes(path: Path, label: str) -> tuple[bytes, int]:
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
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
        return b"".join(chunks), stat.S_IMODE(info.st_mode)
    finally:
        os.close(descriptor)


def _load_frozen_adapter() -> ModuleType:
    path = Path(__file__).resolve().with_name("amended_orchestrator_v2.py")
    payload, _mode = _regular_bytes(path, "frozen amended adapter")
    if hashlib.sha256(payload).hexdigest() != _FROZEN_ADAPTER_SHA256:
        raise ValueError("frozen amended adapter bytes differ from Amendment 0001")
    module = ModuleType(f"_top40_v2_amended_{_FROZEN_ADAPTER_SHA256[:16]}")
    module.__file__ = str(path)
    module.__package__ = "crypto_trade.tournament"
    exec(compile(payload, str(path), "exec"), module.__dict__)
    if module._READ_ONLY_LEGACY_COMMANDS != _READ_ONLY_OPERATIONS:
        raise ValueError("frozen amended adapter read-only command set differs")
    return module


def _protected_relative(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    parts = relative.parts
    tournament_parts = Path(TOP40_V2_LAYOUT.tournament_root).parts
    report_parts = Path(TOP40_V2_LAYOUT.reports_root).parts
    if parts[: len(report_parts)] == report_parts:
        return True
    if parts[: len(tournament_parts)] != tournament_parts:
        return False
    tail = parts[len(tournament_parts) :]
    if len(tail) >= 2 and tail[0] == "teams":
        return len(tail) == 3 and tail[2] in _TEAM_LEDGER_NAMES
    return True


def _read_only_snapshot(root: Path) -> dict[str, _FileImage]:
    snapshot: dict[str, _FileImage] = {}
    for relative_root in (
        TOP40_V2_LAYOUT.tournament_root,
        TOP40_V2_LAYOUT.reports_root,
    ):
        base = root / relative_root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not _protected_relative(path, root):
                continue
            info = os.lstat(path)
            if stat.S_ISDIR(info.st_mode):
                continue
            if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise ValueError("read-only protected output contains an unsafe entry")
            payload, mode = _regular_bytes(path, "read-only protected output")
            snapshot[path.relative_to(root).as_posix()] = _FileImage(payload, mode)
    return snapshot


def _atomic_restore(path: Path, image: _FileImage) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        offset = 0
        while offset < len(image.payload):
            offset += os.write(descriptor, image.payload[offset:])
        os.fchmod(descriptor, image.mode)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def _restore_read_only_snapshot(
    root: Path,
    before: dict[str, _FileImage],
    after: dict[str, _FileImage],
) -> None:
    for relative in sorted(set(after) - set(before), reverse=True):
        path = root / relative
        info = os.lstat(path)
        if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise RuntimeError("cannot remove unsafe read-only mutation")
        path.unlink()
    for relative, image in before.items():
        if after.get(relative) != image:
            _atomic_restore(root / relative, image)
    if _read_only_snapshot(root) != before:
        raise RuntimeError("failed to restore read-only protected bytes")


def _make_compatible_edit(
    adapter: ModuleType,
) -> Callable[..., contextlib.AbstractContextManager[dict[str, Any]]]:
    frozen_edit = adapter.amendment_aware_legacy_state_edit
    read_legacy_state = adapter.read_amendment_aware_legacy_state
    validate_legacy_state = adapter.validate_run_state

    @contextlib.contextmanager
    def compatible_edit(
        root: str | Path,
        config: LoadedV2Config,
        *,
        operation: str,
        staged_changes: list[TransactionChange] | None = None,
        clock: UtcClock = system_utc_now,
    ) -> Iterator[dict[str, Any]]:
        if operation not in _READ_ONLY_OPERATIONS:
            with frozen_edit(
                root,
                config,
                operation=operation,
                staged_changes=staged_changes,
                clock=clock,
            ) as projection:
                yield projection
            return

        changes = [] if staged_changes is None else staged_changes
        if not isinstance(changes, list):
            raise ValueError("staged_changes must be a list of TransactionChange values")
        if changes:
            raise ValueError("read-only legacy command received pre-staged output")
        root_path = Path(root).resolve()
        before_files = _read_only_snapshot(root_path)
        projection = read_legacy_state(
            root_path,
            config,
            operation=operation,
            clock=clock,
        )
        baseline = copy.deepcopy(projection)
        try:
            yield projection
        finally:
            violations: list[str] = []
            try:
                validate_legacy_state(projection, config)
            except (OSError, RuntimeError, ValueError) as exc:
                violations.append(f"invalid state projection: {exc}")
            if projection != baseline:
                violations.append("state mutation")
            if changes:
                violations.append("staged file mutation")
            after_files = _read_only_snapshot(root_path)
            if after_files != before_files:
                _restore_read_only_snapshot(root_path, before_files, after_files)
                violations.append("protected file mutation")
            if violations:
                raise ValueError(
                    "read-only legacy command attempted " + ", ".join(violations)
                )

    return compatible_edit


def run(argv: Sequence[str] | None = None, *, root: str | Path | None = None) -> int:
    """Run one isolated, hash-pinned copy of the frozen amended adapter."""

    adapter = _load_frozen_adapter()
    original_edit = adapter.amendment_aware_legacy_state_edit
    original_authority = {
        "run": adapter.run,
        "read_amendment_aware_legacy_state": adapter.read_amendment_aware_legacy_state,
        "validate_run_state": adapter.validate_run_state,
        "read_only_operations": adapter._READ_ONLY_LEGACY_COMMANDS,
    }
    compatible_edit = _make_compatible_edit(adapter)
    adapter.amendment_aware_legacy_state_edit = compatible_edit
    result: int | None = None
    failure: BaseException | None = None
    try:
        result = int(original_authority["run"](argv, root=root))
    except BaseException as exc:  # restore and audit even on interrupts
        failure = exc
    tampered = (
        adapter.amendment_aware_legacy_state_edit is not compatible_edit
        or adapter.run is not original_authority["run"]
        or adapter.read_amendment_aware_legacy_state
        is not original_authority["read_amendment_aware_legacy_state"]
        or adapter.validate_run_state is not original_authority["validate_run_state"]
        or adapter._READ_ONLY_LEGACY_COMMANDS is not original_authority["read_only_operations"]
    )
    adapter.amendment_aware_legacy_state_edit = original_edit
    if tampered:
        raise RuntimeError(
            "isolated amended adapter authority changed during execution"
        ) from failure
    if failure is not None:
        raise failure.with_traceback(failure.__traceback__)
    if result is None:
        raise RuntimeError("isolated amended adapter returned no result")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"top40-v2-current: error: {exc}", file=sys.stderr)
        return 2
