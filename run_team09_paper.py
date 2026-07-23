#!/usr/bin/env python3
"""Team 09 exact-replay paper desk. This runner never places exchange orders."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import shutil
import sys
import time
import traceback
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from crypto_trade.team09.authority import (
    DeploymentAuthority,
    sha256_file,
    verify_deployment_authority,
)
from crypto_trade.team09.backtest import load_frozen_snapshot
from crypto_trade.team09.live import persist_paper_tick, run_live_replay
from crypto_trade.team09.live_data import (
    LiveMarketData,
    Team09PublicDataClient,
    build_live_market_data,
    current_boundary,
    exact_boundary,
    verify_live_cache_manifest,
)

DEFAULT_PAPER_DIR = Path("paper-team09")
DEFAULT_LAG_SECONDS = 25 * 60


class DeploymentChangedError(RuntimeError):
    """Signal that a running process must restart onto a new committed release."""


def _assert_process_deployment(expected: DeploymentAuthority) -> None:
    current = verify_deployment_authority()
    if current != expected:
        raise DeploymentChangedError(
            "Team 09 deployment changed while this process was running; restart required"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Team 09 paper-only exact replay (no exchange orders)"
    )
    parser.add_argument("--once", action="store_true", help="run one boundary and exit")
    parser.add_argument(
        "--boundary",
        help="exact UTC 8h boundary for a deterministic tick (default: current boundary)",
    )
    parser.add_argument(
        "--paper-dir",
        type=Path,
        default=DEFAULT_PAPER_DIR,
        help="paper output directory (default: paper-team09)",
    )
    parser.add_argument(
        "--no-refresh",
        action="store_true",
        help="replay from an already-populated append-invariant market cache",
    )
    parser.add_argument(
        "--lag-seconds",
        type=int,
        default=DEFAULT_LAG_SECONDS,
        help="loop-mode lag after each 8h boundary (default: 1500)",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=60,
        help="loop-mode poll cadence (default: 60)",
    )
    parser.add_argument(
        "--failure-retry-seconds",
        type=int,
        default=300,
        help="minimum retry delay after a failed tick (default: 300)",
    )
    return parser.parse_args()


def paper_tick(
    *,
    boundary: pd.Timestamp,
    paper_dir: Path,
    refresh: bool,
) -> dict[str, Path]:
    frozen = load_frozen_snapshot()
    if refresh:
        with Team09PublicDataClient() as client:
            live_data = _refresh_cache_generation(
                frozen,
                boundary=boundary,
                cache_root=paper_dir / "market-cache",
                client=client,
            )
    else:
        cache_dir = _current_cache_generation(
            paper_dir / "market-cache",
            required=True,
        )
        if cache_dir is None:
            raise RuntimeError("Team 09 current cache generation is unavailable")
        live_data = build_live_market_data(
            frozen,
            boundary=boundary,
            cache_dir=cache_dir,
            client=None,
        )
    tick = run_live_replay(live_data, boundary=boundary)
    return persist_paper_tick(tick, paper_dir)


def _refresh_cache_generation(
    frozen,
    *,
    boundary: pd.Timestamp,
    cache_root: Path,
    client: Team09PublicDataClient,
) -> LiveMarketData:
    cache_root.mkdir(parents=True, exist_ok=True)
    generations = cache_root / "generations"
    generations.mkdir(parents=True, exist_ok=True)
    current = _current_cache_generation(cache_root, required=False)
    staging = cache_root / (
        f".staging-{boundary.strftime('%Y%m%dT%H%M%SZ')}-"
        f"{os.getpid()}-{time.time_ns()}"
    )
    try:
        if current is None:
            staging.mkdir()
        else:
            shutil.copytree(current, staging, copy_function=_link_or_copy)
        live_data = build_live_market_data(
            frozen,
            boundary=boundary,
            cache_dir=staging,
            client=client,
        )
    except Exception:
        failed_root = cache_root / "failed"
        failed_root.mkdir(exist_ok=True)
        if staging.exists():
            os.replace(staging, failed_root / staging.name.removeprefix("."))
        _prune_directories(failed_root, keep=3)
        raise
    manifest_path = staging / "cache-manifest.json"
    verify_live_cache_manifest(staging)
    generation_name = (
        f"{boundary.strftime('%Y%m%dT%H%M%SZ')}-"
        f"{sha256_file(manifest_path)[:16]}"
    )
    generation = generations / generation_name
    if generation.exists():
        raise RuntimeError(f"Team 09 cache generation already exists: {generation}")
    os.replace(staging, generation)
    _write_text_atomic(
        generation.relative_to(cache_root).as_posix() + "\n",
        cache_root / "CURRENT",
    )
    _prune_directories(generations, keep=9, preserve={generation})
    return LiveMarketData(
        market_data=live_data.market_data,
        diagnostics=live_data.diagnostics,
        cache_dir=generation,
    )


def _current_cache_generation(
    cache_root: Path,
    *,
    required: bool,
) -> Path | None:
    pointer = cache_root / "CURRENT"
    if not pointer.is_file():
        if required:
            raise FileNotFoundError(f"Team 09 cache pointer is missing: {pointer}")
        return None
    relative = pointer.read_text(encoding="utf-8").strip()
    if (
        not relative
        or Path(relative).is_absolute()
        or ".." in Path(relative).parts
        or Path(relative).parts[:1] != ("generations",)
    ):
        raise RuntimeError("Team 09 cache CURRENT pointer is unsafe")
    generation = (cache_root / relative).resolve()
    if not generation.is_relative_to(cache_root.resolve()) or not generation.is_dir():
        raise RuntimeError("Team 09 cache CURRENT generation is missing")
    verify_live_cache_manifest(generation)
    return generation


@contextmanager
def single_engine_lock(paper_dir: Path):
    paper_dir.mkdir(parents=True, exist_ok=True)
    lock_path = paper_dir / "engine.lock"
    with lock_path.open("w", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("another Team 09 paper engine is already running") from None
        handle.write(f"{os.getpid()}\n")
        handle.flush()
        yield


def _run_one(
    args: argparse.Namespace,
    boundary: pd.Timestamp,
    process_deployment: DeploymentAuthority,
) -> None:
    started = pd.Timestamp.now(tz="UTC")
    _write_attempt(
        args.paper_dir.resolve(),
        status="RUNNING",
        boundary=boundary,
        started_at=started,
    )
    print(
        f"[team09-paper] boundary={boundary.isoformat()} refresh={not args.no_refresh} "
        "mode=PAPER_ONLY orders=DISABLED",
        flush=True,
    )
    try:
        _assert_process_deployment(process_deployment)
        paths = paper_tick(
            boundary=boundary,
            paper_dir=args.paper_dir.resolve(),
            refresh=not args.no_refresh,
        )
        _assert_process_deployment(process_deployment)
    except Exception as exc:
        _write_attempt(
            args.paper_dir.resolve(),
            status="FAIL",
            boundary=boundary,
            started_at=started,
            error=f"{type(exc).__name__}: {exc}",
            traceback_text=traceback.format_exc(),
        )
        raise
    elapsed = (pd.Timestamp.now(tz="UTC") - started).total_seconds()
    _write_attempt(
        args.paper_dir.resolve(),
        status="PASS",
        boundary=boundary,
        started_at=started,
        elapsed_seconds=elapsed,
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "boundary": boundary.isoformat(),
                "elapsed_seconds": elapsed,
                "artifacts": {name: str(path) for name, path in paths.items()},
            },
            indent=2,
            sort_keys=True,
        ),
        flush=True,
    )


def _last_successful_boundary(paper_dir: Path) -> pd.Timestamp | None:
    integrity_path = paper_dir / "integrity.json"
    if not integrity_path.is_file():
        return None
    try:
        payload = json.loads(integrity_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("status") != "PASS":
            return None
        return exact_boundary(payload["boundary"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _write_attempt(
    paper_dir: Path,
    *,
    status: str,
    boundary: pd.Timestamp,
    started_at: pd.Timestamp,
    elapsed_seconds: float | None = None,
    error: str | None = None,
    traceback_text: str | None = None,
) -> None:
    payload = {
        "schema_version": "team09-paper-attempt-v1",
        "status": status,
        "boundary": boundary.isoformat(),
        "started_at": started_at.isoformat(),
        "updated_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "elapsed_seconds": elapsed_seconds,
        "error": error,
        "traceback": traceback_text,
    }
    paper_dir.mkdir(parents=True, exist_ok=True)
    _write_text_atomic(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        paper_dir / "attempt.json",
    )


def _write_text_atomic(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def _link_or_copy(source: str, destination: str) -> str:
    try:
        os.link(source, destination)
    except OSError:
        return shutil.copy2(source, destination)
    return destination


def _prune_directories(
    root: Path,
    *,
    keep: int,
    preserve: set[Path] | None = None,
) -> None:
    protected = {path.resolve() for path in (preserve or set())}
    directories = sorted(
        (path for path in root.iterdir() if path.is_dir()),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    retained = 0
    for path in directories:
        if path.resolve() in protected or retained < keep:
            retained += 1
            continue
        shutil.rmtree(path)


def main() -> int:
    args = parse_args()
    if (
        args.lag_seconds < 0
        or args.poll_seconds < 1
        or args.failure_retry_seconds < 1
    ):
        raise SystemExit("lag must be nonnegative; poll/retry must be positive")
    requested = exact_boundary(args.boundary) if args.boundary else None
    if requested is not None and requested > current_boundary():
        raise SystemExit("cannot paper-trade a future boundary")
    process_deployment = verify_deployment_authority()
    with single_engine_lock(args.paper_dir.resolve()):
        if args.once or requested is not None:
            _run_one(args, requested or current_boundary(), process_deployment)
            return 0
        last_boundary = _last_successful_boundary(args.paper_dir.resolve())
        next_retry_at: pd.Timestamp | None = None
        while True:
            now = pd.Timestamp.now(tz="UTC")
            current = current_boundary(now)
            latest_ready = (
                current
                if now >= current + pd.Timedelta(seconds=args.lag_seconds)
                else current - pd.Timedelta(hours=8)
            )
            if last_boundary is None:
                boundary = latest_ready
            else:
                boundary = last_boundary + pd.Timedelta(hours=8)
            can_run = boundary <= latest_ready and (
                next_retry_at is None or now >= next_retry_at
            )
            if can_run:
                try:
                    _run_one(args, boundary, process_deployment)
                    last_boundary = boundary
                    next_retry_at = None
                except DeploymentChangedError:
                    raise
                except Exception:
                    traceback.print_exc()
                    next_retry_at = pd.Timestamp.now(tz="UTC") + pd.Timedelta(
                        seconds=args.failure_retry_seconds
                    )
            time.sleep(args.poll_seconds)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
