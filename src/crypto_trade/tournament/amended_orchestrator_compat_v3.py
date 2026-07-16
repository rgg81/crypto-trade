"""Additive read-only compatibility layer for the frozen Top-40 V2 adapter.

Amendment 0001's adapter correctly transactions result-bearing legacy commands, but after
the administrative hold resumed it routed legacy read-only commands that happen to open
``_edit_state`` through the result-bearing transaction API.  That API deliberately rejects
read-only operations.  This module leaves every frozen byte untouched and substitutes only
that context-manager binding while one amended command is executing.
"""

from __future__ import annotations

import contextlib
import copy
import sys
import threading
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import crypto_trade.tournament.amended_orchestrator_v2 as frozen_adapter
from crypto_trade.tournament.amendment_integrity_v2 import (
    TransactionChange,
    UtcClock,
    system_utc_now,
)
from crypto_trade.tournament.amendment_v2 import read_amendment_aware_legacy_state
from crypto_trade.tournament.top40_v2 import LoadedV2Config, validate_run_state

_FROZEN_EDIT = frozen_adapter.amendment_aware_legacy_state_edit
_FROZEN_RUN = frozen_adapter.run
_PATCH_LOCK = threading.RLock()


@contextlib.contextmanager
def _compatible_legacy_state_edit(
    root: str | Path,
    config: LoadedV2Config,
    *,
    operation: str,
    staged_changes: list[TransactionChange] | None = None,
    clock: UtcClock = system_utc_now,
) -> Iterator[dict[str, Any]]:
    """Permit an unchanged schema-2 view for legacy read-only commands only."""

    if operation not in frozen_adapter._READ_ONLY_LEGACY_COMMANDS:
        with _FROZEN_EDIT(
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
    projection = read_amendment_aware_legacy_state(
        root,
        config,
        operation=operation,
        clock=clock,
    )
    baseline = copy.deepcopy(projection)
    yield projection
    validate_run_state(projection, config)
    if projection != baseline:
        raise ValueError("read-only legacy command attempted a state mutation")
    if changes:
        raise ValueError("read-only legacy command attempted a staged file mutation")


def run(argv: Sequence[str] | None = None, *, root: str | Path | None = None) -> int:
    """Run the frozen amended adapter with the reviewed read-only correction installed."""

    with _PATCH_LOCK:
        if frozen_adapter.amendment_aware_legacy_state_edit is not _FROZEN_EDIT:
            raise RuntimeError("frozen amended adapter binding changed before correction")
        frozen_adapter.amendment_aware_legacy_state_edit = _compatible_legacy_state_edit
        try:
            result = _FROZEN_RUN(argv, root=root)
            if (
                frozen_adapter.amendment_aware_legacy_state_edit
                is not _compatible_legacy_state_edit
            ):
                raise RuntimeError("read-only compatibility binding changed during execution")
            return result
        finally:
            frozen_adapter.amendment_aware_legacy_state_edit = _FROZEN_EDIT


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"top40-v2-current: error: {exc}", file=sys.stderr)
        return 2
