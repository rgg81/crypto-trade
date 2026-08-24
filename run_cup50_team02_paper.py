#!/usr/bin/env python3
"""CUP-50 Team-02 exact-replay paper desk. No exchange order path exists here."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import time
import traceback
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from crypto_trade.cup50_desk.authority import paper_root, repository_root, verify_deployment
from crypto_trade.cup50_desk.live_data import PublicMarketDataClient, refresh_generation
from crypto_trade.cup50_desk.schedule import DEFAULT_LAG_SECONDS, ready_boundary
from crypto_trade.cup50_desk.snapshot_forward import derive_forward_membership
from crypto_trade.cup50_desk.tick import INTERVAL, LATEST, persist_tick

DEFAULT_POLL_SECONDS = 60
ATTEMPT = "attempt.json"
KLINES_PROXY_BASE_URL = "http://127.0.0.1:8000"


class EngineLockError(RuntimeError):
    """Another process already owns this exact paper lineage."""


def _utc(value: object) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        raise ValueError("paper timestamps must be timezone-aware UTC")
    return stamp.tz_convert("UTC")


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


@contextmanager
def engine_lock(paper: Path):
    paper.mkdir(parents=True, exist_ok=True)
    path = paper / "engine.lock"
    handle = path.open("a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.seek(0)
            raise EngineLockError(
                f"another Team-02 paper engine holds {path} (pid {handle.read().strip()})"
            ) from None
        handle.seek(0)
        handle.truncate()
        handle.write(f"{os.getpid()}\n")
        handle.flush()
        yield
    finally:
        handle.close()


def next_boundary(paper: Path, launch: pd.Timestamp) -> pd.Timestamp:
    latest = paper / LATEST
    if not latest.is_file():
        return launch
    payload = json.loads(latest.read_text())
    return _utc(payload["boundary"]) + INTERVAL


def run_boundary(boundary: pd.Timestamp, *, root: Path, paper: Path) -> dict[str, object]:
    started = pd.Timestamp.now(tz="UTC")
    attempt = {
        "schema_version": 1,
        "namespace": "cup50-team02-paper-attempt",
        "boundary": boundary.isoformat(),
        "started_at": started.isoformat(),
        "status": "RUNNING",
    }
    _atomic_json(paper / ATTEMPT, attempt)
    try:
        # Klines are a hard dependency on the local coalescing/cache proxy. There is deliberately
        # no direct-Binance fallback: bypassing the shared limiter would recreate the IP-wide 418
        # bans this desk has already recorded. The other three allowlisted public endpoints retain
        # their direct point-in-time semantics.
        with PublicMarketDataClient(klines_base_url=KLINES_PROXY_BASE_URL) as client:
            generation, membership = refresh_generation(
                paper / "market-cache",
                boundary=boundary,
                resolve_membership=lambda path, edge: derive_forward_membership(
                    path, edge, root=root
                ),
                client=client,
            )
        result = dict(
            persist_tick(
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
        raise
    _atomic_json(
        paper / ATTEMPT,
        {
            **attempt,
            "finished_at": pd.Timestamp.now(tz="UTC").isoformat(),
            "status": "PASS",
            "record_sha256": result["record_sha256"],
        },
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CUP-50 Team-02 paper-only exact replay (never places orders)"
    )
    parser.add_argument("--once", action="store_true", help="run one ready boundary and exit")
    parser.add_argument("--boundary", help="explicit completed 8-hour decision boundary")
    parser.add_argument("--lag-seconds", type=int, default=DEFAULT_LAG_SECONDS)
    parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--failure-retry-seconds", type=int, default=300)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repository_root()
    paper = paper_root(root)
    deployment = verify_deployment(root)
    authority = json.loads((paper / "authority.json").read_text())
    launch = _utc(authority["launch_time"])
    if args.boundary and not args.once:
        raise ValueError("--boundary requires --once")
    with engine_lock(paper):
        print(
            f"Team-02 paper engine pid={os.getpid()} lineage={authority['lineage_sha256']} "
            f"deployment={deployment['manifest_sha256']}",
            flush=True,
        )
        while True:
            boundary = _utc(args.boundary) if args.boundary else next_boundary(paper, launch)
            ready = ready_boundary(pd.Timestamp.now(tz="UTC"), lag_seconds=args.lag_seconds)
            if boundary > ready:
                if args.once:
                    print(
                        f"not ready: requested={boundary.isoformat()} ready={ready.isoformat()}",
                        flush=True,
                    )
                    return 2
                print(
                    f"waiting: next={boundary.isoformat()} ready={ready.isoformat()}",
                    flush=True,
                )
                time.sleep(max(1, args.poll_seconds))
                continue
            try:
                result = run_boundary(boundary, root=root, paper=paper)
                print(
                    f"PASS boundary={boundary.isoformat()} equity={result['equity']:.8f} "
                    f"members={result['membership_count']}",
                    flush=True,
                )
            except Exception:
                traceback.print_exc()
                if args.once:
                    return 1
                time.sleep(max(1, args.failure_retry_seconds))
                continue
            if args.once:
                return 0


if __name__ == "__main__":
    sys.exit(main())
