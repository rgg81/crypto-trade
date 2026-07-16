"""Canonical-script guard for a schema-3 Top-40 V2 run.

Python places the directory containing an executed script first on ``sys.path``.  This tiny
namespace shim therefore runs before the byte-frozen legacy entrypoint can import tournament code
under the supported canonical Python invocation. Once amendment 0001 has migrated the canonical
state away from schema 2, that ordinary old-entrypoint invocation is refused. The reviewed amended
entrypoint remains able to load and adapt the exact frozen bytes in-process.
"""

from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path
from pkgutil import extend_path
from typing import Any

__path__ = extend_path(__path__, __name__)

_LEGACY_ENTRYPOINT = "top40_v2_tournament.py"
_STATE_RELATIVE = Path("tournament/top40-v2/run_state.json")
_MAX_STATE_BYTES = 16 * 1024 * 1024
_LEGACY_STATE_KEYS = {
    "schema_version",
    "tournament",
    "phase",
    "created_at_utc",
    "config_path",
    "config_sha256",
    "research_journal",
    "phase0",
    "qualification_lock",
    "finalist_cohort_lock",
    "objective_lock",
    "final_oos_lock",
    "critic_lock",
    "critic_confirmation_lock",
    "user_ballot_lock",
    "selection_lock",
    "winner_freeze",
    "teams",
}


def _strict_object(payload: bytes) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number {value}")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key {key!r}")
            result[key] = value
        return result

    raw = json.loads(
        payload.decode("utf-8"),
        parse_constant=reject_constant,
        object_pairs_hook=unique_object,
    )
    if not isinstance(raw, dict):
        raise ValueError("run-state root is not an object")
    return raw


def _legacy_state_is_exact_schema_two(root: Path) -> bool:
    path = root / _STATE_RELATIVE
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        )
    except FileNotFoundError:
        return True
    except OSError:
        return False
    try:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_size < 0
            or info.st_size > _MAX_STATE_BYTES
        ):
            return False
        chunks: list[bytes] = []
        remaining = info.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                return False
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            return False
    finally:
        os.close(descriptor)
    try:
        state = _strict_object(b"".join(chunks))
    except (UnicodeError, ValueError, json.JSONDecodeError):
        return False
    return (
        set(state) == _LEGACY_STATE_KEYS
        and type(state.get("schema_version")) is int
        and state["schema_version"] == 2
    )


def _guard_frozen_entrypoint() -> None:
    entrypoint = Path(sys.argv[0]).resolve()
    if entrypoint.name != _LEGACY_ENTRYPOINT or entrypoint.parent.name != "scripts":
        return
    root = entrypoint.parent.parent.resolve()
    if _legacy_state_is_exact_schema_two(root):
        return
    sys.stderr.write(
        "top40-v2: direct frozen entrypoint is disabled for amendment-aware state; "
        "use scripts/top40_v2_amended_tournament.py\n"
    )
    raise SystemExit(2)


_guard_frozen_entrypoint()
