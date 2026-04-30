"""Interactive trade-table dedupe for legacy DBs that pre-date the
(model_name, symbol, open_time) UNIQUE INDEX.

Usage:
    uv run python scripts/dedupe_trades.py --db data/dry_run.db
    uv run python scripts/dedupe_trades.py --db data/live.db --apply

Without --apply (default) the script only PRINTS what it would remove.
With --apply it executes the deletes in a single transaction.

Priority (highest first -- keeper):
    0  numeric entry_order_id   real Binance fill -- never delete
    1  entry_order_id IS NULL   seeded 'closed' row from CSV -- canonical
    2  SEEDED-*                 open seeded carry-over
    3  CATCHUP-* / DRY-*        engine-replayed paper rows -- deletable

Within a tier, oldest created_at wins (first arrival).
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

_PAPER_PREFIXES = ("SEEDED", "DRY-", "CATCHUP-")


def classify_priority(row: dict) -> int:
    """Lower number = higher priority = preferred keeper."""
    eoid = row.get("entry_order_id")
    if eoid is None:
        return 1  # seeded closed (canonical CSV row)
    s = str(eoid)
    if s.startswith(_PAPER_PREFIXES):
        # SEEDED open is priority 2; DRY-/CATCHUP- is priority 3
        if s == "SEEDED" or s.startswith("SEEDED-"):
            return 2
        return 3
    # numeric (real exchange order ID)
    return 0


def pick_keeper(rows: list[dict]) -> dict:
    """From a duplicate group, return the row to KEEP."""
    return min(
        rows,
        key=lambda r: (classify_priority(r), str(r.get("created_at") or "")),
    )


def _fetch_duplicate_groups(conn: sqlite3.Connection) -> list[tuple[str, str, int]]:
    return [
        tuple(row)
        for row in conn.execute(
            "SELECT model_name, symbol, open_time FROM trades "
            "GROUP BY 1, 2, 3 HAVING COUNT(*) > 1 "
            "ORDER BY 1, 2, 3"
        ).fetchall()
    ]


def _fetch_group_rows(
    conn: sqlite3.Connection, model_name: str, symbol: str, open_time: int
) -> list[dict]:
    cur = conn.execute(
        "SELECT * FROM trades WHERE model_name=? AND symbol=? AND open_time=?",
        (model_name, symbol, open_time),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row, strict=False)) for row in cur.fetchall()]


def plan_dedupe(db_path: Path, apply: bool = False) -> list[dict]:
    """Compute (and optionally apply) the dedupe plan.

    Returns a list of {group: (model, sym, ot), kept: row, removed: [row, ...]}
    """
    conn = sqlite3.connect(str(db_path))
    plan: list[dict] = []
    try:
        # Refuse to operate on files that don't look like a state_store DB.
        try:
            has_trades = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='trades'"
            ).fetchone()
        except sqlite3.DatabaseError as exc:
            raise RuntimeError(f"{db_path} is not a valid SQLite database ({exc})") from exc
        if not has_trades:
            raise RuntimeError(f"{db_path} has no 'trades' table -- is this the right DB?")
        for model_name, symbol, open_time in _fetch_duplicate_groups(conn):
            rows = _fetch_group_rows(conn, model_name, symbol, open_time)
            keeper = pick_keeper(rows)
            removed = [r for r in rows if r["id"] != keeper["id"]]
            plan.append(
                {
                    "group": (model_name, symbol, open_time),
                    "kept": keeper,
                    "removed": removed,
                }
            )
        if apply and plan:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = db_path.parent / f"{db_path.name}.bak.{ts}"
            # Close the connection so SQLite flushes WAL before copy.
            conn.close()
            shutil.copy2(db_path, backup_path)
            print(f"[dedupe] Backup written to {backup_path}")
            # Reopen for the destructive transaction.
            conn = sqlite3.connect(str(db_path))
            conn.execute("BEGIN")
            for entry in plan:
                for r in entry["removed"]:
                    conn.execute("DELETE FROM trades WHERE id=?", (r["id"],))
            conn.commit()
    finally:
        conn.close()
    return plan


def _format_row_summary(r: dict) -> str:
    return (
        f"id={r['id'][:8]}.. "
        f"entry_order_id={r.get('entry_order_id')} "
        f"created_at={r.get('created_at')} "
        f"status={r.get('status')} "
        f"exit_reason={r.get('exit_reason')} "
        f"exit_price={r.get('exit_price')}"
    )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=str,
        required=True,
        help="DB path. Must be typed explicitly (no glob).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the plan (delete rows). Default: dry-run only.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"ERROR: {db_path} does not exist", file=sys.stderr)
        return 2

    try:
        plan = plan_dedupe(db_path, apply=args.apply)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not plan:
        print(f"[dedupe] {db_path}: no duplicates found")
        return 0

    total_remove = sum(len(e["removed"]) for e in plan)
    print(
        f"[dedupe] {db_path}: {len(plan)} duplicate group(s), "
        f"{total_remove} row(s) would be removed"
    )
    for entry in plan:
        m, s, ot = entry["group"]
        print(f"\n  ({m}, {s}, {ot}):")
        print(f"    KEEP    {_format_row_summary(entry['kept'])}")
        for r in entry["removed"]:
            print(f"    REMOVE  {_format_row_summary(r)}")

    if args.apply:
        print(f"\n[dedupe] APPLIED -- {total_remove} rows deleted")
    else:
        print(
            f"\n[dedupe] DRY-RUN -- {total_remove} rows would be deleted. "
            f"Re-run with --apply to execute."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
