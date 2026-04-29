"""Probe whether the V2-NEAR catch-up freeze is a real hang or stdout buffering.

When V2-NEAR's 2026-04 training has reached its 5th ensemble seed and the
log has gone silent (no new "Trial X finished" line), this script samples:
  - utime over 30s   (>0 ⇒ active, =0 ⇒ hung)
  - state            (R=running, S=sleeping)
  - threads          (count)
  - WAL mtime delta  (>0 ⇒ DB writes still happening)
  - log size delta   (>0 ⇒ stdout flushing)

Usage (run when log goes silent):
    uv run python scripts/check_v2near_hang.py --log /tmp/baseline_reprod/dryrun_v2fix.log
"""
from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path


def _utime_jiffies(pid: int) -> int:
    try:
        with open(f"/proc/{pid}/stat") as fh:
            return int(fh.read().split()[13])
    except FileNotFoundError:
        return -1


def _state(pid: int) -> str:
    try:
        with open(f"/proc/{pid}/status") as fh:
            for line in fh:
                if line.startswith("State:"):
                    return line.split(":", 1)[1].strip()
        return "?"
    except FileNotFoundError:
        return "(dead)"


def _threads(pid: int) -> int:
    try:
        with open(f"/proc/{pid}/status") as fh:
            for line in fh:
                if line.startswith("Threads:"):
                    return int(line.split(":", 1)[1].strip())
        return -1
    except FileNotFoundError:
        return -1


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--log", required=True, type=str)
    p.add_argument("--db-wal", default="data/dry_run.db-wal", type=str)
    p.add_argument("--sample-secs", type=int, default=30)
    args = p.parse_args()

    pids = subprocess.check_output(
        ["pgrep", "-f", "crypto-trade live --track both"], text=True
    ).split()
    pids = [int(p) for p in pids if p.strip()]
    pyproc = None
    for pid in pids:
        try:
            with open(f"/proc/{pid}/comm") as fh:
                if "python" in fh.read():
                    pyproc = pid
                    break
        except FileNotFoundError:
            pass
    if pyproc is None:
        raise SystemExit(f"no python child crypto-trade process found (pgrep returned {pids})")

    print(f"PID = {pyproc}")
    print(f"State (t=0)        : {_state(pyproc)}")
    print(f"Threads (t=0)      : {_threads(pyproc)}")
    log_size_t0 = Path(args.log).stat().st_size
    wal_mtime_t0 = Path(args.db_wal).stat().st_mtime if Path(args.db_wal).exists() else 0
    utime_t0 = _utime_jiffies(pyproc)

    print(f"Log size (t=0)     : {log_size_t0:,} bytes")
    print(f"WAL mtime (t=0)    : {wal_mtime_t0}")
    print(f"utime (t=0)        : {utime_t0:,} jiffies")
    print(f"\nSampling for {args.sample_secs}s ...\n")
    time.sleep(args.sample_secs)

    state_after = _state(pyproc)
    threads_after = _threads(pyproc)
    log_size_t1 = Path(args.log).stat().st_size
    wal_mtime_t1 = Path(args.db_wal).stat().st_mtime if Path(args.db_wal).exists() else 0
    utime_t1 = _utime_jiffies(pyproc)

    delta_utime = utime_t1 - utime_t0
    delta_log = log_size_t1 - log_size_t0
    delta_wal = wal_mtime_t1 - wal_mtime_t0

    print(f"State (t={args.sample_secs})        : {state_after}")
    print(f"Threads (t={args.sample_secs})      : {threads_after}")
    print(f"Log size (t={args.sample_secs})     : {log_size_t1:,} bytes  (Δ={delta_log:+,} bytes)")
    print(f"WAL mtime (t={args.sample_secs})    : {wal_mtime_t1}  (Δ={delta_wal:+.2f}s)")
    print(f"utime delta over {args.sample_secs}s: {delta_utime:+,} jiffies (~{delta_utime/100:.2f} CPU-seconds)")

    print("\n--- VERDICT ---")
    if delta_utime > 1000:
        print("ACTIVE: process accumulated significant CPU time → NOT a hang, just buffered output.")
    elif delta_utime > 0 and delta_wal > 0:
        print("MAYBE WRITING: low CPU but DB getting writes → engine alive, possibly waiting on I/O.")
    elif delta_utime == 0 and delta_log == 0 and delta_wal == 0:
        print("HUNG: zero CPU, zero log writes, zero DB writes → real hang.")
    else:
        print("MIXED: investigate further. py-spy attach recommended.")


if __name__ == "__main__":
    main()
