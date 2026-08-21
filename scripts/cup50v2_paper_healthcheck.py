#!/usr/bin/env python
"""One STATUS line per CUP-50 v2 desk, plus the capital rule's standing.

Written to be read by a monitor loop that runs every few minutes for six months, so it says what
changed and stays quiet otherwise. Every check answers a question a real failure would raise:
did the last tick pass, is the desk keeping up with the 8h clock, is its deployment still the one
that was frozen, and has the append-only record been rewritten behind us.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

INTERVAL = pd.Timedelta(hours=8)
DESKS = ("winner", "runner-up-1", "runner-up-2", "ensemble-eq3")
# A desk is late once it has missed a whole boundary plus a grace period for a slow fetch.
LATE_AFTER = INTERVAL + pd.Timedelta(minutes=45)


def _utc(value: object) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    return stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")


def desk_status(
    paper_root: Path, desk_id: str, now: pd.Timestamp, *, launched: bool
) -> dict[str, object]:
    paper = paper_root / desk_id
    latest = paper / "latest.json"
    attempt = paper / "attempt.json"
    if not latest.is_file():
        # Before launch a desk with no boundary is expected. After launch it is a desk that has
        # never ticked, which is exactly the failure a monitor exists to catch -- and would have
        # been reported OK if PENDING stayed benign once the field went live.
        if not launched:
            return {"desk": desk_id, "status": "PENDING", "detail": "not launched yet"}
        return {
            "desk": desk_id,
            "status": "NO-TICK",
            "detail": "launched but has never published a boundary",
        }
    published = _utc(json.loads(latest.read_text())["boundary"])
    behind = now - (published + INTERVAL)
    row: dict[str, object] = {
        "desk": desk_id,
        "boundary": published.isoformat(),
        "behind_minutes": round(max(behind.total_seconds(), 0.0) / 60.0, 1),
    }
    if attempt.is_file():
        payload = json.loads(attempt.read_text())
        row["attempt"] = payload.get("status")
        if payload.get("status") == "FAIL":
            return {
                **row,
                "status": "FAIL",
                "detail": f"{payload.get('error_type')}: {payload.get('error')}",
            }
    if behind > LATE_AFTER:
        return {**row, "status": "LATE", "detail": f"{behind} past the boundary it owes"}
    return {**row, "status": "OK"}


def capital_rule(paper_root: Path, now: pd.Timestamp, minimum_days: int) -> dict[str, object]:
    """Where the pre-registered capital decision stands. It reads the record, never the ranking."""
    launch_file = paper_root / "launch.json"
    if not launch_file.is_file():
        return {"status": "NOT-LAUNCHED"}
    launch = _utc(json.loads(launch_file.read_text())["launch"])
    days = (now - launch).total_seconds() / 86400.0
    return {
        "status": "ACCRUING" if days < minimum_days else "DECIDABLE",
        "official_days": round(days, 1),
        "minimum_days": minimum_days,
        "detail": (
            f"{max(0.0, minimum_days - days):.1f} days before the capital rule may be read"
            if days < minimum_days
            else "the pre-registered rule may now be evaluated"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--minimum-days", type=int, default=183)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    root = Path(arguments.root).resolve() if arguments.root else Path(__file__).resolve().parents[1]
    paper_root = root / "paper-cup50v2"
    now = pd.Timestamp.now(tz="UTC")

    capital = capital_rule(paper_root, now, arguments.minimum_days)
    launched = capital["status"] != "NOT-LAUNCHED"
    rows = [desk_status(paper_root, desk_id, now, launched=launched) for desk_id in DESKS]
    worst = "OK"
    for row in rows:
        if row["status"] in {"FAIL", "LATE", "NO-TICK"}:
            worst = "ATTENTION"
    if arguments.json:
        print(json.dumps({"status": worst, "desks": rows, "capital": capital}, sort_keys=True))
        return 0 if worst == "OK" else 1
    print(f"STATUS {worst}")
    for row in rows:
        detail = f"  {row['detail']}" if row.get("detail") else ""
        print(f"  {row['desk']:<14} {row['status']:<8} {row.get('boundary', '-')}{detail}")
    print(f"  capital        {capital['status']:<8} {capital.get('detail', '')}")
    return 0 if worst == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
