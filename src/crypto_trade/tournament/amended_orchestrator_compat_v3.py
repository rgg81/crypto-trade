"""Additive read-only status correction for the frozen Top-40 V2 adapter.

The frozen amended adapter remains the sole implementation for every result-bearing command.
Only ``research-status`` is intercepted here: its frozen implementation opens an edit context
despite being observational, which Amendment 0001 correctly refuses to transaction as a write.
This module performs the same journal and ledger validation without a recovery/write branch.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

from crypto_trade.tournament.amendment_integrity_v2 import system_utc_now
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT

_FROZEN_ADAPTER_SHA256 = "89ebd52bf5f0552476745605fb92c9665eef1668c2212ab62d5e8c03f577d172"
_RESEARCH_STATUS = "research-status"


def _regular_bytes(path: Path, label: str) -> bytes:
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
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _load_frozen_adapter() -> ModuleType:
    path = Path(__file__).resolve().with_name("amended_orchestrator_v2.py")
    payload = _regular_bytes(path, "frozen amended adapter")
    if hashlib.sha256(payload).hexdigest() != _FROZEN_ADAPTER_SHA256:
        raise ValueError("frozen amended adapter bytes differ from Amendment 0001")
    module = ModuleType(f"_top40_v2_amended_{_FROZEN_ADAPTER_SHA256[:16]}")
    module.__file__ = str(path)
    module.__package__ = "crypto_trade.tournament"
    exec(compile(payload, str(path), "exec"), module.__dict__)
    return module


def _locked_authority(adapter: ModuleType) -> Mapping[str, Any]:
    globals_map = adapter.read_amended_state.__globals__
    required = {
        "_state_lock",
        "_read_amended_state_locked",
        "_require_integration_ready",
        "assert_operation_permitted",
        "_legacy_projection",
    }
    if not required.issubset(globals_map):
        raise ValueError("Amendment 0001 locked-state authority is incomplete")
    return {name: globals_map[name] for name in required}


def _research_status_command(
    adapter: ModuleType,
    argv: Sequence[str],
    *,
    root: Path,
) -> int:
    legacy = adapter._load_frozen_orchestrator(root)
    args = legacy.build_parser().parse_args(list(argv))
    if args.command != _RESEARCH_STATUS:
        raise ValueError("status correction received a non-status command")
    if getattr(args, "json_out", None) is not None:
        raise ValueError("amended orchestration writes JSON to stdout only")
    config = adapter._canonical_config(root, getattr(args, "config", TOP40_V2_LAYOUT.config_path))
    authority = _locked_authority(adapter)
    with authority["_state_lock"](root):
        state, _state_bytes, _chain, _audit = authority["_read_amended_state_locked"](
            root,
            config,
            clock=system_utc_now,
        )
        authority["_require_integration_ready"](state, _RESEARCH_STATUS)
        authority["assert_operation_permitted"](state, _RESEARCH_STATUS)
        projection = authority["_legacy_projection"](state)
        effective_config = adapter._effective_config(config, state)
        journal = legacy._load_research_journal(
            root,
            effective_config,
            projection,
            recover_projection=False,
        )
        selected = legacy.TEAM_IDS if args.team_id is None else (args.team_id,)
        teams = {
            team_id: {
                "material_trial_count": journal.teams[team_id].material_trial_count,
                "cpu_hours": journal.teams[team_id].cpu_hours,
                "wall_clock_hours": journal.teams[team_id].wall_clock_hours,
                "pending_candidate_ids": list(journal.teams[team_id].pending_candidate_ids),
            }
            for team_id in selected
        }
    print(
        json.dumps(
            {
                "journal_head_sha256": journal.head_sha256,
                "journal_record_count": len(journal.records),
                "teams": teams,
            },
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def run(argv: Sequence[str] | None = None, *, root: str | Path | None = None) -> int:
    """Intercept read-only research status; delegate every other command unchanged."""

    working_root = Path.cwd().resolve()
    root_path = working_root if root is None else Path(root).resolve()
    if root_path != working_root:
        raise ValueError("current orchestration root must be the current working directory")
    values = list(sys.argv[1:] if argv is None else argv)
    adapter = _load_frozen_adapter()
    if values and values[0] == _RESEARCH_STATUS:
        return _research_status_command(adapter, values, root=root_path)
    return int(adapter.run(None if argv is None else values, root=root_path))


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"top40-v2-current: error: {exc}", file=sys.stderr)
        return 2
