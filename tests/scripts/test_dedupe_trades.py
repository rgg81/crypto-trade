"""Tests for scripts/dedupe_trades.py priority-based picker."""

from __future__ import annotations

import sqlite3
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from dedupe_trades import (  # type: ignore[import-not-found]  # noqa: E402
    classify_priority,
    pick_keeper,
    plan_dedupe,
)

_SCHEMA_SQL = (
    "CREATE TABLE trades ("
    "id TEXT PRIMARY KEY, model_name TEXT NOT NULL, symbol TEXT NOT NULL, "
    "direction INTEGER NOT NULL, entry_price REAL NOT NULL, "
    "amount_usd REAL NOT NULL, weight_factor REAL NOT NULL, "
    "stop_loss_price REAL NOT NULL, take_profit_price REAL NOT NULL, "
    "open_time INTEGER NOT NULL, timeout_time INTEGER NOT NULL, "
    "signal_time INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'open', "
    "entry_order_id TEXT, sl_order_id TEXT, tp_order_id TEXT, "
    "exit_price REAL, exit_time INTEGER, exit_reason TEXT, "
    "created_at TEXT NOT NULL"
    ")"
)


def test_classify_priority_real_money_highest():
    """Numeric entry_order_id (real Binance fill) gets the highest priority."""
    p = classify_priority({"entry_order_id": "1234567890", "created_at": "0"})
    assert p == 0  # 0 = highest


def test_classify_priority_seeded_closed():
    """entry_order_id IS NULL -> seeded 'closed' row from CSV (priority 1)."""
    p = classify_priority({"entry_order_id": None, "created_at": "0"})
    assert p == 1


def test_classify_priority_seeded_open():
    """SEEDED-* prefix (open seeded carry-over) -> priority 2."""
    p = classify_priority({"entry_order_id": "SEEDED", "created_at": "0"})
    assert p == 2


def test_classify_priority_catchup_lowest():
    """CATCHUP-* and DRY-* -> priority 3 (lowest, deletable)."""
    assert classify_priority({"entry_order_id": "CATCHUP-aaaa", "created_at": "0"}) == 3
    assert classify_priority({"entry_order_id": "DRY-aaaa", "created_at": "0"}) == 3


def test_pick_keeper_prefers_higher_priority():
    """Among a group, the row with the lowest priority (highest tier) wins."""
    rows = [
        {"id": "id-real", "entry_order_id": "9999", "created_at": "200"},
        {"id": "id-catchup", "entry_order_id": "CATCHUP-aaaa", "created_at": "100"},
    ]
    keeper = pick_keeper(rows)
    assert keeper["id"] == "id-real"


def test_pick_keeper_breaks_ties_by_created_at():
    """Same priority tier -> oldest created_at wins."""
    rows = [
        {"id": "id-newer", "entry_order_id": "CATCHUP-aaaa", "created_at": "200"},
        {"id": "id-older", "entry_order_id": "CATCHUP-bbbb", "created_at": "100"},
    ]
    keeper = pick_keeper(rows)
    assert keeper["id"] == "id-older"


def _build_legacy_db(db_path: Path, rows: list[tuple]) -> None:
    """Build a DB with the OLD schema (no UNIQUE INDEX). rows: list of
    (entry_order_id, created_at) tuples sharing the same (model, sym, ot)."""
    conn = sqlite3.connect(str(db_path))
    conn.execute(_SCHEMA_SQL)
    for entry_id, created in rows:
        conn.execute(
            "INSERT INTO trades VALUES (?, 'A', 'BTCUSDT', 1, 100.0, 1000.0, 1.0, 95.0, "
            "110.0, 1700000000000, 1700604800000, 1700000000000, 'closed', ?, NULL, "
            "NULL, 105.0, 1700100000000, 'take_profit', ?)",
            (uuid.uuid4().hex, entry_id, created),
        )
    conn.commit()
    conn.close()


def test_plan_dedupe_dry_run(tmp_path):
    """plan_dedupe (default apply=False) returns plan without modifying DB."""
    db_path = tmp_path / "legacy.db"
    _build_legacy_db(db_path, [("CATCHUP-aaa", "200"), (None, "100")])

    plan = plan_dedupe(db_path)
    assert len(plan) == 1  # one duplicate group
    group = plan[0]
    assert group["kept"]["entry_order_id"] is None  # seeded closed wins (priority 1)
    assert len(group["removed"]) == 1
    assert group["removed"][0]["entry_order_id"] == "CATCHUP-aaa"

    # DB unchanged
    conn = sqlite3.connect(str(db_path))
    n = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    conn.close()
    assert n == 2


def test_plan_dedupe_apply(tmp_path):
    """With apply=True, the lower-priority rows are deleted in a transaction."""
    db_path = tmp_path / "legacy.db"
    _build_legacy_db(db_path, [("CATCHUP-aaa", "200"), (None, "100")])

    plan_dedupe(db_path, apply=True)

    conn = sqlite3.connect(str(db_path))
    rows = conn.execute("SELECT entry_order_id FROM trades").fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0][0] is None  # seeded-closed (NULL) survived


def test_plan_dedupe_no_duplicates(tmp_path):
    """Empty plan when no duplicates exist."""
    db_path = tmp_path / "clean.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(_SCHEMA_SQL)
    conn.commit()
    conn.close()

    plan = plan_dedupe(db_path)
    assert plan == []


def test_plan_dedupe_raises_runtime_error_on_missing_trades_table(tmp_path):
    """If the DB exists but has no 'trades' table, plan_dedupe must raise
    a clear RuntimeError that mentions the file path."""
    db = tmp_path / "wrong.db"
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE other_table (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    with pytest.raises(RuntimeError, match="trades"):
        plan_dedupe(db)


def test_main_returns_2_on_missing_trades_table(tmp_path, capsys):
    """main() catches the RuntimeError and exits 2 with a stderr message."""
    from dedupe_trades import main  # type: ignore[import-not-found]

    db = tmp_path / "wrong.db"
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE other_table (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    rc = main(["--db", str(db)])
    assert rc == 2
    captured = capsys.readouterr()
    assert "trades" in captured.err.lower()


def test_plan_dedupe_apply_writes_backup(tmp_path):
    """--apply must copy the DB to <name>.bak.<timestamp> before deleting."""
    db_path = tmp_path / "with_dups.db"
    _build_legacy_db(db_path, [("CATCHUP-aaa", "200"), (None, "100")])

    plan_dedupe(db_path, apply=True)

    backups = list(tmp_path.glob(f"{db_path.name}.bak.*"))
    assert len(backups) == 1, f"Expected exactly 1 backup, got {len(backups)}"
    # The backup must contain BOTH original rows (pre-deletion state).
    conn = sqlite3.connect(str(backups[0]))
    n = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    conn.close()
    assert n == 2
