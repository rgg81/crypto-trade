"""Integrity and parity for all four desks. Never performance.

The question this answers is always "can the record still be trusted", never "is the book doing
well". PnL, drawdown and turnover are test results, not operational alerts, and they live in the
digest.

Imports ``desk_parity()`` -- the same function the digest uses, not a second opinion about what
counts as a parity break.

Usage::

    uv run python scripts/top40v5_paper_healthcheck.py
    uv run python scripts/top40v5_paper_healthcheck.py --json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

from crypto_trade.tournament.v5.desk.ledger import read_ledger
from crypto_trade.tournament.v5.desk.parity import BROKEN, UNVERIFIED, desk_parity

REPO = Path(__file__).resolve().parents[1]
PAPER = REPO / "paper-top40v5"
INTERVAL = pd.Timedelta(hours=8)
# Grace after the owed bar closes, before a desk that has not published it counts as late. The
# watchdog fires at :13 past, so 45 minutes covers a normal tick plus its retry entry.
LATE_GRACE = pd.Timedelta(minutes=45)


def _owed_boundary(now: pd.Timestamp) -> pd.Timestamp:
    """The boundary the engine currently owes -- the same rule the engine itself uses.

    The engine publishes the PREVIOUS closed boundary, never the one now floors to, because the
    final boundary is provisional until a later bar exists. So a perfectly current desk always sits
    between 8h and 16h behind the wall clock.

    Comparing `now - published` against 8h45m therefore fires on a healthy desk for most of every
    cycle -- it read LATE(9h) on a field that had just published on time. A check that cries wolf
    on a healthy desk is worse than no check: the skill's own warning is that a noisy alarm is the
    one ignored on the day it matters, and this one sat next to a genuine LATE(40h).
    """

    return now.floor(f"{int(INTERVAL.total_seconds() // 3600)}h") - INTERVAL


def _classes(desk: str, spec: dict, launched: bool, now: pd.Timestamp) -> list[str]:
    root = PAPER / desk
    found: list[str] = []

    parity = desk_parity(root)
    if parity.state == BROKEN:
        found.append("PARITY-BROKEN")

    # Deployment drift: the desk must replay the bytes the manifest binds.
    for lane, bound in spec["bundle"].items():
        path = root / f"frozen-{lane}.py"
        if not path.is_file():
            found.append(f"DEPLOYMENT-DRIFT({lane} missing)")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != bound["sha256"]:
            found.append(f"DEPLOYMENT-DRIFT({lane})")

    boundary_path = root / "boundary.json"
    if not boundary_path.is_file():
        found.append("NO-TICK" if launched else "PENDING")
        return found

    record = json.loads(boundary_path.read_text(encoding="utf-8"))
    published = pd.Timestamp(record["boundary"])
    if published > now:
        found.append("BOUNDARY-SKEW(ahead of now)")
    if published.hour % 8 or published.minute or published.second:
        found.append("BOUNDARY-SKEW(off-grid)")
    owed = _owed_boundary(now)
    lag = owed - published
    # Late once a boundary has been missed outright, or once the owed one has been open long
    # enough for the watchdog and its retry to have run.
    if lag > INTERVAL or (lag > pd.Timedelta(0) and now - owed - INTERVAL > LATE_GRACE):
        found.append(f"LATE({lag.total_seconds() / 3600:.0f}h behind {owed})")

    attempt = root / "attempt.json"
    if attempt.is_file():
        status = json.loads(attempt.read_text(encoding="utf-8"))
        if status.get("status") == "FAILED" and "PARITY-BROKEN" not in found:
            found.append(f"FAIL({status.get('error_type', 'unknown')})")
        if status.get("status") == "RUNNING":
            found.append("RUNNING")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()

    manifest_path = PAPER / "deployment-manifest.json"
    if not manifest_path.is_file():
        print("no deployment manifest; the desks are not deployed")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    launch_path = PAPER / "launch.json"
    launched = launch_path.is_file()
    now = pd.Timestamp.now(tz="UTC")

    # A shared-cache staleness is one fault for the field, not four.
    shared = PAPER / "boundary.json"
    stale_hours = 0.0
    if shared.is_file():
        stale_hours = float(json.loads(shared.read_text(encoding="utf-8")).get("stale_hours", 0.0))

    report = {"launched": launched, "checked_at": str(now), "desks": {}, "field": {}}
    if stale_hours > 8.0:
        report["field"]["DATA-STALE"] = round(stale_hours, 1)

    worst = "OK"
    for desk, spec in sorted(manifest.items()):
        classes = _classes(desk, spec, launched, now)
        parity = desk_parity(PAPER / desk)
        ledger = read_ledger(PAPER / desk / "ledger" / "forward_returns.parquet")
        official = int(ledger["official"].sum()) if "official" in ledger.columns else 0
        report["desks"][desk] = {
            "classes": classes,
            "parity": parity.state,
            "verified_through": parity.verified_through,
            "parity_detail": parity.detail,
            "rows": int(len(ledger)),
            "official_bars": official,
        }
        if "PARITY-BROKEN" in classes:
            worst = "PARITY-BROKEN"
        elif classes and worst == "OK" and parity.state != UNVERIFIED:
            worst = "ATTENTION"

    # Official DAYS, not bars: three 8h bars make one day, and the capital rule counts days.
    official_days = max((d["official_bars"] for d in report["desks"].values()), default=0) // 3
    report["official_days"] = official_days
    report["capital"] = (
        ("ACCRUING" if launched else "NOT-LAUNCHED") if official_days < 365 else "READABLE"
    )
    report["status"] = worst

    if arguments.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print(
        f"STATUS {report['status']}    capital {report['capital']} "
        f"({official_days}/365 official days)"
    )
    if report["field"]:
        print(f"FIELD  {report['field']}")
    for desk, row in sorted(report["desks"].items()):
        classes = ", ".join(row["classes"]) if row["classes"] else "clean"
        print(
            f"  {desk:16s} {classes:34s} parity {row['parity']:<11}"
            f" through {row['verified_through'] or '—'}  rows {row['rows']}"
            f" (official {row['official_bars']})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
