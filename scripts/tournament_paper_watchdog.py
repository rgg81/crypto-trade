"""crypto-cup-01 paper-desk WATCHDOG — auto-recover a dead OR hung engine (keep-DB).

Two proven failure modes for this desk (both 2026-07): the process gets REAPED when its
launching session shell dies, and it HANGS on a bad socket during a Binance 418 storm
(alive but stuck in poll_schedule_timeout, missing rebalances). This watchdog recovers both
without manual intervention, and — crucially — WITHOUT thrashing a healthy engine that is
merely retrying through a rate-limit ban.

Decision logic (run me every ~20-30 min via cron):
  - no python engine child            -> DEAD  -> relaunch (keep DB)
  - child alive, log advancing (<20m) -> HEALTHY (even if retrying a 418 ban) -> no-op
  - child alive, log STALE (>=20m)     \
    AND newest rebalance >10h old       > -> HUNG -> kill tree + relaunch (keep DB)
  - child alive, log stale, rebalance recent -> quiet window between candles -> no-op

The relaunch is detached with start_new_session=True (setsid) so the new engine is NOT
parented to this watchdog/cron shell — closing the reap hole for relaunched processes.
PAPER-ONLY + keep-DB, so recovery is always safe (never trades, never loses book state).

  uv run python scripts/tournament_paper_watchdog.py [--force-relaunch]
"""

import argparse
import os
import re
import signal
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
LOG = _ROOT / "logs" / "portfolio_tournament_paper.log"
RUNNER = "run_portfolio_tournament_paper.py"
STALE_MIN = 20.0  # log silent this long => not even retrying => hung (vs healthy 60s retries)
MISS_H = 10.0  # newest rebalance older than this => missed-rebalance territory


def _procs() -> tuple[list[int], list[int]]:
    """(all matching pids, python-child pids) for the desk runner."""
    out = subprocess.run(["pgrep", "-fa", RUNNER], capture_output=True, text=True).stdout
    allp, child = [], []
    for ln in out.splitlines():
        if "pgrep" in ln or "watchdog" in ln or "shell-snapshot" in ln or "eval " in ln:
            continue
        pid = int(ln.split()[0])
        allp.append(pid)
        if "python3 " in ln or ".venv" in ln:
            child.append(pid)
    return allp, child


def _log_age_min() -> float:
    return (time.time() - LOG.stat().st_mtime) / 60 if LOG.exists() else 1e9


def _rebalance_age_h() -> float:
    if not LOG.exists():
        return 1e9
    stamps = re.findall(
        r"rebalance plan as_of=(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", LOG.read_text()
    )
    if not stamps:
        return 1e9
    last = datetime.strptime(stamps[-1], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    return (datetime.now(UTC) - last).total_seconds() / 3600


def _note(msg: str) -> None:
    line = f"[watchdog] {datetime.now(UTC):%Y-%m-%d %H:%M UTC} — {msg}"
    print(line)
    with LOG.open("a") as f:
        f.write(line + "\n")


def _kill(pids: list[int]) -> None:
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for p in pids:
            try:
                os.kill(p, sig)
            except ProcessLookupError:
                pass
        time.sleep(3)


def _relaunch() -> None:
    # Detached (setsid) so the engine is not parented to this shell — closes the reap hole.
    with LOG.open("a") as f:
        subprocess.Popen(
            ["uv", "run", "python", RUNNER],
            cwd=str(_ROOT),
            stdout=f,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
    time.sleep(12)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force-relaunch", action="store_true")
    args = ap.parse_args()

    allp, child = _procs()
    log_age = _log_age_min()
    rb_age = _rebalance_age_h()

    if args.force_relaunch:
        _note(f"force-relaunch requested; killing {allp or 'none'}")
        _kill(allp)
        _relaunch()
        return 0

    if not child:
        _note(f"engine DOWN (no python child; matches={allp}); relaunching keep-DB")
        _kill(allp)  # clear any orphan wrapper
        _relaunch()
        _note("relaunched (detached)")
        return 0

    if log_age >= STALE_MIN and rb_age > MISS_H:
        _note(
            f"engine HUNG (child={child}, log stale {log_age:.0f}m, last rebalance {rb_age:.1f}h "
            f"ago); killing + relaunching keep-DB"
        )
        _kill(allp)
        _relaunch()
        _note("relaunched (detached)")
        return 0

    # healthy — including the healthy-retrying-through-a-418-ban case (log advancing)
    state = "retrying/ban" if rb_age > MISS_H else "nominal"
    print(
        f"[watchdog] OK — child={child}, log {log_age:.0f}m, last rebalance {rb_age:.1f}h ({state})"
    )
    _print_stats()  # basic P&L pulse — best-effort, AFTER the liveness verdict
    return 0


def _print_stats() -> None:
    """Compact P&L pulse. Best-effort and lazily imported so a slow/failing recompute can NEVER
    block or break the watchdog's liveness+recovery job (which already ran above)."""
    try:
        import tournament_paper_pnl as pnl  # scripts/ is on sys.path[0]; import runs the SHA check

        print(f"[watchdog] stats — {pnl.oneline(pnl.compute_stats())}")
    except Exception as e:  # noqa: BLE001 — stats are informational; never fail the watchdog
        print(f"[watchdog] stats — n/a ({type(e).__name__}: {e})")


if __name__ == "__main__":
    raise SystemExit(main())
