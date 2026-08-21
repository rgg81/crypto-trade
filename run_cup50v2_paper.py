#!/usr/bin/env python
"""Tick every CUP-50 v2 paper desk from one shared market-cache generation.

Four desks run in parallel -- the winner, two runners-up and the equal-risk ensemble -- because six
editions have shown that in-sample rank carries almost no information about out-of-sample rank at
the top, and CUP-20 measured a forward rank correlation of -1 against its own leaderboard. The
capital decision reads the forward record, not the ranking.

One process, one cache. Four desks fetching the same public endpoints independently would be four
times the request rate for identical bytes and an easy way to earn a 418. The generation is built
once per boundary and every desk replays against those exact bytes, which also makes the desks
comparable: a difference between two desks is a difference between two strategies, never between
two fetches.

A desk that fails does not stop the others. The whole point of running four is that they are
independent bets; letting one bad tick halt the rest would couple them precisely where they are
supposed to be uncoupled. Each desk records its own attempt, and the process exits non-zero if any
desk failed, so the watchdog still sees it.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import sys
import traceback
from pathlib import Path

import pandas as pd

from crypto_trade.cup50v2_desk.authority import load_desk, repository_root
from crypto_trade.cup50v2_desk.live_data import PublicMarketDataClient, refresh_generation
from crypto_trade.cup50v2_desk.snapshot_forward import derive_forward_membership
from crypto_trade.cup50v2_desk.tick import INTERVAL, LATEST, persist_tick

ATTEMPT = "attempt.json"
DESKS = ("winner", "runner-up-1", "runner-up-2", "ensemble-eq3")


class EngineLockError(RuntimeError):
    """Another CUP-50 v2 paper engine is already running."""


def _utc(value: object) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    return stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


@contextlib.contextmanager
def engine_lock(root: Path):
    """One engine for all four desks, held at the shared root rather than per desk."""
    root.mkdir(parents=True, exist_ok=True)
    path = root / "engine.lock"
    handle = path.open("a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.seek(0)
            raise EngineLockError(
                f"another CUP-50 v2 paper engine holds {path} (pid {handle.read().strip()})"
            ) from None
        handle.seek(0)
        handle.truncate()
        handle.write(f"{os.getpid()}\n")
        handle.flush()
        yield
    finally:
        handle.close()


def next_boundary(paper_root: Path, desk_ids: tuple[str, ...], launch: pd.Timestamp):
    """The earliest boundary any desk still owes.

    Desks are ticked together and should never diverge, but if one is behind -- a desk added late,
    or a desk recovered from a failed tick -- the engine catches it up rather than skipping ahead
    with the others.
    """
    owed = []
    for desk_id in desk_ids:
        latest = paper_root / desk_id / LATEST
        if not latest.is_file():
            owed.append(launch)
            continue
        owed.append(_utc(json.loads(latest.read_text())["boundary"]) + INTERVAL)
    return min(owed)


def tick_desk(desk_id: str, boundary, *, generation, membership, root: Path, paper_root: Path):
    desk = load_desk(desk_id, root)
    paper = paper_root / desk_id
    latest = paper / LATEST
    if latest.is_file() and _utc(json.loads(latest.read_text())["boundary"]) >= boundary:
        return {"desk_id": desk_id, "status": "ALREADY", "boundary": boundary.isoformat()}
    started = pd.Timestamp.now(tz="UTC")
    attempt = {
        "schema_version": 1,
        "namespace": f"cup50v2-{desk_id}-paper-attempt",
        "desk_id": desk_id,
        "boundary": boundary.isoformat(),
        "started_at": started.isoformat(),
        "status": "RUNNING",
    }
    _atomic_json(paper / ATTEMPT, attempt)
    try:
        result = dict(
            persist_tick(
                desk,
                boundary=boundary,
                generation=generation,
                membership=membership,
                root=root,
            )
        )
    except Exception as exc:
        _atomic_json(
            paper / ATTEMPT,
            {
                **attempt,
                "finished_at": pd.Timestamp.now(tz="UTC").isoformat(),
                "status": "FAIL",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        return {"desk_id": desk_id, "status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    _atomic_json(
        paper / ATTEMPT,
        {
            **attempt,
            "finished_at": pd.Timestamp.now(tz="UTC").isoformat(),
            "status": "PASS",
            "record_sha256": result["record_sha256"],
        },
    )
    return {"desk_id": desk_id, "status": "PASS", "record_sha256": result["record_sha256"]}


def run_boundary(boundary, *, root: Path, paper_root: Path, desk_ids: tuple[str, ...]):
    """Build the shared generation once, then replay every desk against those exact bytes."""
    with PublicMarketDataClient() as client:
        generation, membership = refresh_generation(
            paper_root / "market-cache",
            boundary=boundary,
            resolve_membership=lambda path, edge: derive_forward_membership(path, edge, root=root),
            client=client,
        )
    outcomes = [
        tick_desk(
            desk_id,
            boundary,
            generation=generation,
            membership=membership,
            root=root,
            paper_root=paper_root,
        )
        for desk_id in desk_ids
    ]
    _atomic_json(
        paper_root / "boundary.json",
        {
            "schema_version": 1,
            "namespace": "cup50v2-paper-boundary",
            "boundary": boundary.isoformat(),
            "generation": Path(generation).name,
            "desks": outcomes,
        },
    )
    return outcomes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--desk", action="append", default=None, help="default: all four")
    parser.add_argument("--launch", required=True, help="first boundary, ISO-8601 UTC")
    parser.add_argument("--max-boundaries", type=int, default=8)
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    root = Path(arguments.root).resolve() if arguments.root else repository_root()
    paper_root = root / "paper-cup50v2"
    desk_ids = tuple(arguments.desk) if arguments.desk else DESKS
    launch = _utc(arguments.launch)
    failures = 0
    with engine_lock(paper_root):
        for _ in range(max(1, arguments.max_boundaries)):
            boundary = next_boundary(paper_root, desk_ids, launch)
            if boundary > pd.Timestamp.now(tz="UTC"):
                break
            outcomes = run_boundary(
                boundary, root=root, paper_root=paper_root, desk_ids=desk_ids
            )
            for outcome in outcomes:
                print(json.dumps(outcome, sort_keys=True), flush=True)
                failures += outcome["status"] == "FAIL"
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
