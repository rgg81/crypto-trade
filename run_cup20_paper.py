#!/usr/bin/env python3
"""The CUP-20 winner's forward paper desk. This runner cannot place an exchange order.

It is the operational shell around :mod:`crypto_trade.cup20_desk`: acquire the engine lock, verify
the deployment authority, refresh the append-invariant market cache, and hand one boundary to
:func:`crypto_trade.cup20_desk.tick.run_tick`, which replays the frozen winner through the
tournament's own evaluator. Nothing about execution happens here -- no fill, no fee, no slippage,
no funding, no position size. ``tests/cup20_desk/test_healthcheck.py`` asserts that by inspection,
and the only network client in the import graph is
:class:`~crypto_trade.cup20_desk.live_data.PublicMarketDataClient`, which refuses any endpoint
outside four public market-data paths.

**A boundary is ready only once its own bar has CLOSED, plus a publication lag.** This is the one
place the desk departs from the shape of the team-09 runner, and it is not a preference. The
tournament's evaluator reads the fill bar's own quote volume for the ``max_bar_participation`` cap
and its own close for the mark to market, so a boundary whose 8h bar is still forming produces
fills and returns that CHANGE when the bar completes. The desk records fills at the boundary it
ticks; recording them off a forming bar would make every subsequent tick abort on append
invariance -- correctly, and forever. So ``ready_boundary`` is ``floor_8h(now - lag) - 8h``: the
newest boundary whose bar has fully closed and then sat unrevised for the lag. The desk therefore
publishes a decision roughly 8h25m after the instant it is stamped with, which for a weekly
rebalance is immaterial and is the only reading that is arithmetically safe.

**The cache holds the WIDE cross-section and its own contract metadata.** The universe ranks a
symbol against every eligible perpetual over a trailing 180 days, so a cache scoped to the current
twenty members cannot reconstitute anything (operational fact 1). And four of today's members have
no metadata row in either sealed snapshot, so the desk fetches ``exchangeInfo`` itself every tick
(fact 2). Symbols already cached are refetched only from their last recorded bar -- which
deliberately re-reads rows already on disk, because that overlap is what exercises append
invariance -- while a symbol the desk has never seen is fetched back a complete lookback window.

**Two ticks must never overlap** (fact 9: one tick costs ~410 s against the real window). The
``fcntl`` lock is what prevents it. A leftover lock FILE is not a stale lock: ``flock`` lives on an
open file description and the kernel drops it when the holder dies, so a crashed engine leaves a
file whose lock is free. What must not be trusted is the pid inside a file nobody holds, so the pid
line is rewritten only AFTER the lock is taken -- opening the file with ``"w"`` would truncate the
live holder's pid before the losing process discovered it had lost.

Every failure is logged with the boundary named and then re-raised. A traceback is never silent:
it reaches ``logs/cup20_paper.log``, ``attempt.json`` and the caller.
"""

from __future__ import annotations

import argparse
import dataclasses
import fcntl
import json
import logging
import os
import sys
import time
import traceback
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_trade.cup20.config import load_config
from crypto_trade.cup20_desk.authority import (
    DeploymentChangedError,
    DeskAuthority,
    config_path,
    current_desk_authority,
    repository_root,
    verify_desk_authority,
)
from crypto_trade.cup20_desk.live_data import (
    FUNDING,
    INTERVAL_HOURS,
    SNAPSHOT_FRAMES,
    AppendResult,
    PublicMarketDataClient,
    append_frame,
    fetch_forward,
)
from crypto_trade.cup20_desk.snapshot_forward import CACHE_DIRNAME
from crypto_trade.cup20_desk.tick import SEAM, persist_tick, run_tick
from crypto_trade.tournament.snapshot import _utc as utc

DEFAULT_DESK_DIR = repository_root() / "paper-cup20"
DEFAULT_LOG_PATH = repository_root() / "logs" / "cup20_paper.log"
"""Anchored to the worktree, not to the working directory. A cron entry or a systemd unit runs from
somewhere else, and a relative default there would quietly create a SECOND desk -- one with its own
pins, its own ledgers and no relationship to the record the healthcheck reads."""

DEFAULT_LAG_SECONDS = 25 * 60
"""How long a closed bar must stand before the desk treats it as final."""

INTERVAL = pd.Timedelta(hours=INTERVAL_HOURS)

HISTORY_SLACK_DAYS = 21
"""Fetched on top of the universe's own lookback. Two weeks of forward reconstitutions each need a
complete trailing window ENDING at their own boundary, and the extra week absorbs a desk that has
been down for a few days without leaving the first boundary back unscored."""

ENGINE_LOCK = "engine.lock"
ATTEMPT_JSON = "attempt.json"
INTEGRITY_JSON = "integrity.json"
ATTEMPT_SCHEMA_VERSION = "cup20-desk-attempt-v1"

LOGGER_NAME = "cup20-paper"


class EngineLockError(RuntimeError):
    """Another CUP-20 paper engine already holds this desk."""


class DeskTickError(RuntimeError):
    """One boundary failed. Always raised ``from`` the original, with the boundary named."""


class DeploymentMovedError(RuntimeError):
    """The deployment changed underneath a running process; it must restart onto the new one."""


# ------------------------------------------------------------------------------------------------
# the grid
# ------------------------------------------------------------------------------------------------


def floor_boundary(moment: object) -> pd.Timestamp:
    """The 8h decision boundary at or before ``moment``."""
    return utc(moment).floor(INTERVAL)


def exact_boundary(value: object) -> pd.Timestamp:
    moment = utc(value)
    if moment != floor_boundary(moment):
        raise ValueError(f"{moment} is not an exact {INTERVAL_HOURS}h UTC boundary")
    return moment


def ready_boundary(now: object, lag_seconds: int = DEFAULT_LAG_SECONDS) -> pd.Timestamp:
    """The newest boundary whose own bar has closed and then stood unrevised for the lag.

    See the module docstring: a boundary whose bar is still forming is one the exchange may still
    revise, and one the evaluator would read a changing volume and close out of.
    """
    if lag_seconds < 0:
        raise ValueError("the publication lag cannot be negative")
    return floor_boundary(utc(now) - pd.Timedelta(seconds=lag_seconds)) - INTERVAL


def history_start(boundary: object, *, lookback_days: int) -> pd.Timestamp:
    """The first instant the wide cache must reach back to for ``boundary`` to be scoreable."""
    moment = utc(boundary)
    return floor_boundary(moment - pd.Timedelta(days=lookback_days + HISTORY_SLACK_DAYS))


def universe_lookback_days(config: str | Path | None = None) -> int:
    """The frozen contract's own liquidity lookback. Never a constant repeated here."""
    return int(load_config(config or config_path()).raw["universe"]["lookback_days"])


# ------------------------------------------------------------------------------------------------
# the cross-section
# ------------------------------------------------------------------------------------------------


def tradable_symbols(payload: Mapping[str, Any]) -> tuple[str, ...]:
    """Every live USD-M perpetual the tournament's eligibility rule could admit.

    The predicate is the acquisition's own (``scripts/cup20_build_snapshot.py:eligibility``):
    ``PERPETUAL`` with USDT quote and margin. ``underlyingType == "COIN"`` is added because the
    acquisition's ``_contract_metadata`` REFUSES to build a frame containing a non-crypto contract,
    so an index perpetual reaching the fetch would abort the tick rather than be filtered later.
    """
    symbols = payload.get("symbols")
    if not isinstance(symbols, list):
        raise ValueError("exchangeInfo response has no symbols array")
    return tuple(
        sorted(
            {
                str(item["symbol"])
                for item in symbols
                if isinstance(item, Mapping)
                and item.get("symbol")
                and item.get("status") == "TRADING"
                and item.get("contractType") == "PERPETUAL"
                and item.get("quoteAsset") == "USDT"
                and item.get("marginAsset") == "USDT"
                and item.get("underlyingType") == "COIN"
            }
        )
    )


@dataclasses.dataclass(frozen=True, slots=True)
class CacheRefresh:
    """What one cache refresh acquired, in the terms the append-invariant record uses."""

    boundary: pd.Timestamp
    cross_section: int
    first_seen: int
    window_start: pd.Timestamp
    appended: Mapping[str, int]
    transitioned: Mapping[str, int]
    rows: Mapping[str, int]

    def summary(self) -> dict[str, Any]:
        return {
            "boundary": self.boundary.isoformat(),
            "cross_section": self.cross_section,
            "first_seen": self.first_seen,
            "window_start": self.window_start.isoformat(),
            "appended": dict(self.appended),
            "transitioned": dict(self.transitioned),
            "rows": dict(self.rows),
        }


def refresh_cache(
    desk_root: str | Path,
    boundary: object,
    *,
    client: PublicMarketDataClient,
    lookback_days: int,
    seam: object = SEAM,
    logger: logging.Logger | None = None,
) -> CacheRefresh:
    """Bring the desk's own market cache up to ``boundary``, appending only genuinely new rows.

    Two fetch passes, for two different reasons. Symbols the cache already carries are refetched
    from their last recorded bar, so the overlap re-reads rows already on disk and
    :func:`~crypto_trade.cup20_desk.live_data.append_frame` compares them value by value -- that
    overlap IS the revision check, and dropping it to save a request would make the desk blind to
    Binance rewriting recent history. A symbol the desk has never seen is fetched back a complete
    liquidity lookback, because the universe cannot rank a symbol whose trailing window it lacks.

    **The desk records no funding the tournament already sealed.** Bars and marks must reach back a
    complete lookback -- the ranking and the coverage rule need them -- but funding does not: the
    universe rule never reads it, and every instant before the seam already has a funding row in the
    sealed snapshot. Keeping the desk's own copy of those instants would be worse than redundant.
    Binance's monthly archives publish ``funding_interval_hours`` as the CONTRACTUAL schedule, while
    the REST endpoint publishes no interval at all and the desk must derive it from the spacing
    between settlements -- and when the venue skips a settlement the two disagree honestly: measured
    over 12 members and 50 days of the sealed window, ``HYPEUSDT`` and one other missed their
    2026-06-24 04:00 event, so the archive says 4.0 and the observed spacing says 8.0. Neither is
    wrong; they are different questions. Where the tournament has already answered one, its answer
    stands, and the desk simply does not record a second.
    """
    log = logger or logging.getLogger(LOGGER_NAME)
    moment = exact_boundary(boundary)
    cache = Path(desk_root) / CACHE_DIRNAME
    cache.mkdir(parents=True, exist_ok=True)
    window_end = moment + INTERVAL
    beginning = history_start(moment, lookback_days=lookback_days)
    recorded_through = utc(seam)

    cross_section = tradable_symbols(client.exchange_info())
    if not cross_section:
        raise RuntimeError("exchangeInfo published no eligible USD-M perpetual")
    recorded = _cached_symbols(cache)
    carried = tuple(symbol for symbol in cross_section if symbol in recorded)
    first_seen = tuple(symbol for symbol in cross_section if symbol not in recorded)
    resume = _cached_through(cache)

    passes: list[tuple[tuple[str, ...], pd.Timestamp]] = []
    if carried:
        anchor = beginning if resume is None else min(max(resume, beginning), moment)
        passes.append((carried, anchor))
    if first_seen:
        passes.append((first_seen, beginning))

    appended: dict[str, int] = dict.fromkeys(SNAPSHOT_FRAMES, 0)
    transitioned: dict[str, int] = dict.fromkeys(SNAPSHOT_FRAMES, 0)
    rows: dict[str, int] = dict.fromkeys(SNAPSHOT_FRAMES, 0)
    for symbols, start in passes:
        log.info(
            "fetching %d symbols over [%s, %s)",
            len(symbols),
            start.isoformat(),
            window_end.isoformat(),
        )
        frames = fetch_forward(symbols, start, window_end, client=client)
        frames[FUNDING] = frames[FUNDING].loc[frames[FUNDING]["funding_time"] >= recorded_through]
        for name in SNAPSHOT_FRAMES:
            result: AppendResult = append_frame(cache / f"{name}.parquet", frames[name], name=name)
            appended[name] += result.appended
            transitioned[name] += result.transitioned
            rows[name] = result.total
            if result.transitioned:
                log.info("%s: %d declared lifecycle transitions", name, result.transitioned)
    refresh = CacheRefresh(
        boundary=moment,
        cross_section=len(cross_section),
        first_seen=len(first_seen),
        window_start=min((start for _, start in passes), default=beginning),
        appended=appended,
        transitioned=transitioned,
        rows=rows,
    )
    log.info("cache refreshed: %s", json.dumps(refresh.summary(), sort_keys=True))
    return refresh


def _cached_symbols(cache: Path) -> frozenset[str]:
    path = cache / "bars.parquet"
    if not path.is_file():
        return frozenset()
    return frozenset(pd.read_parquet(path, columns=["symbol"])["symbol"].astype(str))


def _cached_through(cache: Path) -> pd.Timestamp | None:
    """The newest bar already recorded, which is where the re-verification overlap starts."""
    path = cache / "bars.parquet"
    if not path.is_file():
        return None
    times = pd.read_parquet(path, columns=["open_time"])["open_time"]
    if times.empty:
        return None
    return floor_boundary(times.max())


# ------------------------------------------------------------------------------------------------
# one boundary
# ------------------------------------------------------------------------------------------------


def paper_tick(
    boundary: object,
    *,
    desk_root: str | Path,
    authority: DeskAuthority,
    refresh: bool = True,
    client: PublicMarketDataClient | None = None,
    lookback_days: int | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Path]:
    """Refresh, replay, persist. Every number written was produced by the tournament's evaluator.

    No window override is ever passed to :func:`run_tick`: ``integrity.json`` pins ``seam``,
    ``is_start`` and ``official_start``, and the tick reads them back (operational fact 8). A runner
    that supplied its own would be able to move a window the desk has already published under.
    """
    log = logger or logging.getLogger(LOGGER_NAME)
    moment = exact_boundary(boundary)
    root = Path(desk_root)
    verify_desk_authority(authority)
    if refresh:
        owned = client is None
        reader = client if client is not None else PublicMarketDataClient()
        try:
            refresh_cache(
                root,
                moment,
                client=reader,
                lookback_days=(
                    lookback_days if lookback_days is not None else universe_lookback_days()
                ),
                logger=log,
            )
        finally:
            if owned:
                reader.close()
    else:
        log.info("replaying from the recorded cache; no market data was fetched")
    result = run_tick(moment, desk_root=root, authority=authority)
    log.info(
        "replayed %d decisions: phase=%s rebalance=%s members=%d",
        result.decisions,
        result.phase,
        result.rebalance,
        len(result.membership),
    )
    return persist_tick(result, root)


# ------------------------------------------------------------------------------------------------
# the engine lock
# ------------------------------------------------------------------------------------------------


@contextmanager
def single_engine_lock(desk_root: str | Path):
    """Hold the desk exclusively, or refuse. See the module docstring on stale locks."""
    root = Path(desk_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / ENGINE_LOCK
    handle = path.open("a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.seek(0)
            holder = handle.read().strip() or "unknown"
            raise EngineLockError(
                f"another CUP-20 paper engine holds {path} (pid {holder}); two ticks must never "
                "overlap, so this process is refusing to start"
            ) from None
        handle.seek(0)
        handle.truncate()
        handle.write(f"{os.getpid()}\n")
        handle.flush()
        yield path
    finally:
        handle.close()


# ------------------------------------------------------------------------------------------------
# logging and the attempt marker
# ------------------------------------------------------------------------------------------------


def configure_logging(log_path: str | Path, *, level: int = logging.INFO) -> logging.Logger:
    """Structured logging to stdout and to the desk's log file, flushed on every record.

    This repository has been bitten by block-buffered logs: a redirected stdout buffers, the file
    mtime stops moving, and a healthy multi-minute replay is indistinguishable from a hung process.
    ``logging``'s stream handlers flush on every emit and stdout is put in line-buffered mode, so
    the log's mtime tracks real progress whether or not ``PYTHONUNBUFFERED`` is set.
    """
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [cup20-paper] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    formatter.converter = time.gmtime
    for handler in (logging.StreamHandler(sys.stdout), logging.FileHandler(path, encoding="utf-8")):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(line_buffering=True)
    return logger


def write_attempt(
    desk_root: str | Path,
    *,
    status: str,
    boundary: pd.Timestamp,
    started_at: pd.Timestamp,
    elapsed_seconds: float | None = None,
    error: str | None = None,
    traceback_text: str | None = None,
) -> Path:
    """The last thing this engine tried, so a healthcheck can tell RUNNING from FAILED."""
    payload = {
        "schema_version": ATTEMPT_SCHEMA_VERSION,
        "status": status,
        "paper_only": True,
        "boundary": boundary.isoformat(),
        "started_at": started_at.isoformat(),
        "updated_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "elapsed_seconds": elapsed_seconds,
        "error": error,
        "traceback": traceback_text,
        "pid": os.getpid(),
    }
    root = Path(desk_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / ATTEMPT_JSON
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    return path


def last_published_boundary(desk_root: str | Path) -> pd.Timestamp | None:
    """The newest boundary the desk successfully published, or ``None`` before its first tick."""
    path = Path(desk_root) / INTEGRITY_JSON
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping) or payload.get("status") != "PASS":
            return None
        return exact_boundary(payload["boundary"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


# ------------------------------------------------------------------------------------------------
# the run
# ------------------------------------------------------------------------------------------------


def run_boundary(
    boundary: pd.Timestamp,
    *,
    desk_root: Path,
    authority: DeskAuthority,
    refresh: bool,
    logger: logging.Logger,
) -> dict[str, Path]:
    """One boundary, with its attempt marker and its traceback. Failures name the boundary."""
    started = pd.Timestamp.now(tz="UTC")
    write_attempt(desk_root, status="RUNNING", boundary=boundary, started_at=started)
    logger.info("tick start: boundary=%s refresh=%s mode=PAPER_ONLY", boundary.isoformat(), refresh)
    try:
        _assert_deployment_unchanged(authority)
        written = paper_tick(
            boundary,
            desk_root=desk_root,
            authority=authority,
            refresh=refresh,
            logger=logger,
        )
        _assert_deployment_unchanged(authority)
    except Exception as exc:
        detail = traceback.format_exc()
        logger.error("tick FAILED at boundary=%s: %s", boundary.isoformat(), exc)
        logger.error("%s", detail)
        write_attempt(
            desk_root,
            status="FAIL",
            boundary=boundary,
            started_at=started,
            error=f"{type(exc).__name__}: {exc}",
            traceback_text=detail,
        )
        raise DeskTickError(
            f"CUP-20 paper tick failed at boundary {boundary.isoformat()}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    elapsed = (pd.Timestamp.now(tz="UTC") - started).total_seconds()
    write_attempt(
        desk_root,
        status="PASS",
        boundary=boundary,
        started_at=started,
        elapsed_seconds=elapsed,
    )
    logger.info(
        "tick PASS: %s",
        json.dumps(
            {
                "boundary": boundary.isoformat(),
                "elapsed_seconds": elapsed,
                "artifacts": {name: str(path) for name, path in sorted(written.items())},
            },
            sort_keys=True,
        ),
    )
    return written


def _assert_deployment_unchanged(pinned: DeskAuthority) -> None:
    """A release that moves under a running process must restart, not keep publishing."""
    try:
        verify_desk_authority(pinned)
    except DeploymentChangedError as exc:
        raise DeploymentMovedError(
            f"the CUP-20 deployment changed while this engine was running: {exc}"
        ) from exc


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CUP-20 winner forward paper desk (paper only; places no orders)"
    )
    parser.add_argument("--once", action="store_true", help="run one boundary and exit")
    parser.add_argument("--boundary", help="an exact UTC 8h boundary; default: the newest ready")
    parser.add_argument("--desk-dir", type=Path, default=DEFAULT_DESK_DIR)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG_PATH)
    parser.add_argument(
        "--no-refresh",
        action="store_true",
        help="replay from the recorded cache without touching the network",
    )
    parser.add_argument("--lag-seconds", type=int, default=DEFAULT_LAG_SECONDS)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--failure-retry-seconds", type=int, default=600)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.lag_seconds < 0 or args.poll_seconds < 1 or args.failure_retry_seconds < 1:
        raise SystemExit("the lag must be non-negative; poll and retry must be positive")
    logger = configure_logging(args.log)
    desk_root = args.desk_dir.resolve()

    # Authority first, before the lock, the network or a single byte of output. A desk running
    # against a changed strategy, risk policy, config, selection freeze or evaluator is producing a
    # record that is not comparable to the holdout result it follows.
    try:
        authority = current_desk_authority()
    except Exception as exc:
        logger.error("DEPLOYMENT AUTHORITY REFUSED: %s", exc)
        logger.error("%s", traceback.format_exc())
        raise
    logger.info("authority verified: %s", json.dumps(authority.to_dict(), sort_keys=True))

    requested = exact_boundary(args.boundary) if args.boundary else None
    if requested is not None and requested > ready_boundary(
        pd.Timestamp.now(tz="UTC"), args.lag_seconds
    ):
        raise SystemExit(
            f"{requested.isoformat()} is not final yet: its bar has not closed and stood for the "
            f"{args.lag_seconds}s publication lag"
        )

    with single_engine_lock(desk_root):
        logger.info("engine lock held: %s", desk_root / ENGINE_LOCK)
        if args.once or requested is not None:
            boundary = requested or ready_boundary(pd.Timestamp.now(tz="UTC"), args.lag_seconds)
            run_boundary(
                boundary,
                desk_root=desk_root,
                authority=authority,
                refresh=not args.no_refresh,
                logger=logger,
            )
            return 0
        published = last_published_boundary(desk_root)
        retry_at: pd.Timestamp | None = None
        logger.info("entering the poll loop every %ds", args.poll_seconds)
        while True:
            now = pd.Timestamp.now(tz="UTC")
            ready = ready_boundary(now, args.lag_seconds)
            boundary = ready if published is None else published + INTERVAL
            due = boundary <= ready and (retry_at is None or now >= retry_at)
            if due:
                try:
                    run_boundary(
                        boundary,
                        desk_root=desk_root,
                        authority=authority,
                        refresh=not args.no_refresh,
                        logger=logger,
                    )
                    published = boundary
                    retry_at = None
                except DeploymentMovedError:
                    raise
                except Exception:
                    retry_at = pd.Timestamp.now(tz="UTC") + pd.Timedelta(
                        seconds=args.failure_retry_seconds
                    )
                    logger.error("retrying no earlier than %s", retry_at.isoformat())
            time.sleep(args.poll_seconds)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
