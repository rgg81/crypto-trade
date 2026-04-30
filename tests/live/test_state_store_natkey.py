"""Tests for trades(model_name, symbol, open_time) uniqueness and migration."""

from __future__ import annotations

import sqlite3
import time
import uuid

import pandas as pd
import pytest

from crypto_trade.backtest_models import Signal
from crypto_trade.live.engine import LiveEngine
from crypto_trade.live.models import LiveConfig, LiveTrade, ModelConfig
from crypto_trade.live.state_store import StateStore, StateStoreMigrationError


def _make_trade(
    model_name: str = "A",
    symbol: str = "BTCUSDT",
    open_time: int = 1_700_000_000_000,
    entry_order_id: str | None = None,
) -> LiveTrade:
    return LiveTrade(
        id=uuid.uuid4().hex,
        model_name=model_name,
        symbol=symbol,
        direction=1,
        entry_price=100.0,
        amount_usd=1000.0,
        weight_factor=1.0,
        stop_loss_price=95.0,
        take_profit_price=110.0,
        open_time=open_time,
        timeout_time=open_time + 7 * 24 * 3600 * 1000,
        signal_time=open_time,
        status="open",
        entry_order_id=entry_order_id,
        sl_order_id=None,
        tp_order_id=None,
        exit_price=None,
        exit_time=None,
        exit_reason=None,
        created_at=str(int(time.time() * 1000)),
    )


def test_unique_index_blocks_duplicate_insert(tmp_path):
    """Two trades with same (model_name, symbol, open_time) → second insert fails."""
    store = StateStore(tmp_path / "ux.db")
    store.upsert_trade(_make_trade(entry_order_id="SEEDED"))
    with pytest.raises(sqlite3.IntegrityError):
        store.upsert_trade(_make_trade(entry_order_id="CATCHUP-aaaa"))


def test_unique_index_allows_same_id_update(tmp_path):
    """upsert_trade with same id must still update the existing row (id-based ON CONFLICT)."""
    store = StateStore(tmp_path / "update.db")
    t = _make_trade(entry_order_id="SEEDED")
    store.upsert_trade(t)
    # Update — same id, status change to closed
    t2 = LiveTrade(**{**t.__dict__, "status": "closed", "exit_reason": "stop_loss"})
    store.upsert_trade(t2)
    fetched = store.get_trade(t.id)
    assert fetched.status == "closed"
    assert fetched.exit_reason == "stop_loss"


def test_unique_index_allows_different_open_time(tmp_path):
    """Same model_name, symbol, but different open_time → both inserts succeed."""
    store = StateStore(tmp_path / "diff_ot.db")
    store.upsert_trade(_make_trade(open_time=1_700_000_000_000))
    store.upsert_trade(_make_trade(open_time=1_700_000_000_000 + 28_800_000))
    assert len(store.get_all_trades()) == 2


def test_db_open_aborts_on_existing_duplicates(tmp_path):
    """Pre-create a DB without the index, insert duplicates, reopen → migration error."""
    db_path = tmp_path / "legacy.db"
    # Build a DB with the OLD schema (no unique index)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """CREATE TABLE trades (
            id TEXT PRIMARY KEY, model_name TEXT NOT NULL, symbol TEXT NOT NULL,
            direction INTEGER NOT NULL, entry_price REAL NOT NULL,
            amount_usd REAL NOT NULL, weight_factor REAL NOT NULL,
            stop_loss_price REAL NOT NULL, take_profit_price REAL NOT NULL,
            open_time INTEGER NOT NULL, timeout_time INTEGER NOT NULL,
            signal_time INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'open',
            entry_order_id TEXT, sl_order_id TEXT, tp_order_id TEXT,
            exit_price REAL, exit_time INTEGER, exit_reason TEXT,
            created_at TEXT NOT NULL
        )"""
    )
    conn.execute("CREATE TABLE engine_state (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    # Insert two rows with identical (model_name, symbol, open_time)
    for _ in range(2):
        conn.execute(
            "INSERT INTO trades VALUES (?, 'A', 'BTCUSDT', 1, 100.0, 1000.0, 1.0, 95.0, "
            "110.0, 1700000000000, 1700604800000, 1700000000000, 'closed', NULL, NULL, "
            "NULL, 105.0, 1700100000000, 'take_profit', '0')",
            (uuid.uuid4().hex,),
        )
    conn.commit()
    conn.close()

    with pytest.raises(StateStoreMigrationError) as excinfo:
        StateStore(db_path)
    msg = str(excinfo.value)
    assert "1 duplicate" in msg
    assert "dedupe_trades.py" in msg


def test_count_natural_key_duplicates_returns_zero_for_clean_db(tmp_path):
    store = StateStore(tmp_path / "clean.db")
    assert store._count_natural_key_duplicates() == 0


def test_count_natural_key_duplicates_after_legacy_setup(tmp_path):
    """The helper counts groups, not rows — two duplicate rows = 1 group."""
    db_path = tmp_path / "counted.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """CREATE TABLE trades (
            id TEXT PRIMARY KEY, model_name TEXT NOT NULL, symbol TEXT NOT NULL,
            direction INTEGER NOT NULL, entry_price REAL NOT NULL,
            amount_usd REAL NOT NULL, weight_factor REAL NOT NULL,
            stop_loss_price REAL NOT NULL, take_profit_price REAL NOT NULL,
            open_time INTEGER NOT NULL, timeout_time INTEGER NOT NULL,
            signal_time INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'open',
            entry_order_id TEXT, sl_order_id TEXT, tp_order_id TEXT,
            exit_price REAL, exit_time INTEGER, exit_reason TEXT,
            created_at TEXT NOT NULL
        )"""
    )
    conn.execute("CREATE TABLE engine_state (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    # Insert 3 rows: two duplicates of (A, BTC, T1), one unique (A, BTC, T2)
    for ot in (1_700_000_000_000, 1_700_000_000_000, 1_700_000_000_000 + 28_800_000):
        conn.execute(
            "INSERT INTO trades VALUES (?, 'A', 'BTCUSDT', 1, 100.0, 1000.0, 1.0, 95.0, "
            "110.0, ?, ?, ?, 'closed', NULL, NULL, NULL, 105.0, ?, 'take_profit', '0')",
            (uuid.uuid4().hex, ot, ot + 7 * 24 * 3600 * 1000, ot, ot + 100000),
        )
    conn.commit()
    conn.close()

    # Cannot open via StateStore (would raise). Verify count by attaching directly.
    conn = sqlite3.connect(str(db_path))
    n = conn.execute(
        "SELECT COUNT(*) FROM (SELECT model_name, symbol, open_time "
        "FROM trades GROUP BY 1, 2, 3 HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    conn.close()
    assert n == 1


def test_catch_up_handles_unique_collision_gracefully(tmp_path):
    """Pre-insert a closed (model, sym, open_time) row that collides with what
    catch-up wants to insert; assert catch-up logs 'duplicate suppressed' and
    leaves the row count unchanged."""
    import io
    from contextlib import redirect_stdout

    candle_ms = 28_800_000
    # Pick a recent-past candle so it falls in the catch-up window AND its
    # close_time is in the past (engine breaks on `ct > now_ms`).
    ot = (int(time.time() * 1000) // candle_ms) * candle_ms - candle_ms
    ct = ot + candle_ms - 1

    # When dry_run=True the engine ignores cfg.db_path and uses
    # `data_dir / "dry_run.db"` (engine.py:241-247). Pre-seed there.
    db_path = tmp_path / "dry_run.db"
    cfg = LiveConfig(
        models=(
            ModelConfig(
                name="A",
                symbols=("BTCUSDT",),
                use_atr_labeling=True,
                atr_tp_multiplier=2.9,
                atr_sl_multiplier=1.45,
                ood_enabled=False,  # avoid Mahalanobis covariance fitting in the stub
            ),
        ),
        dry_run=True,
        db_path=db_path,
        data_dir=tmp_path,
        catch_up_lookback_days=1,
    )

    # Pre-seed a CLOSED row at this (model, sym, open_time). status='closed'
    # ensures it doesn't pre-load into open_trades; the catch-up loop will
    # call get_signal, attempt to upsert a new CATCHUP-* row, hit the unique
    # index, and exercise the handler.
    #
    # The catch-up loop sets the new trade's open_time to the candle's
    # close_time (engine.py:882), so to force a collision we pre-seed at
    # open_time=ct.
    store = StateStore(db_path)
    closed_row = LiveTrade(
        id=uuid.uuid4().hex,
        model_name="A",
        symbol="BTCUSDT",
        direction=1,
        entry_price=100.0,
        amount_usd=1000.0,
        weight_factor=1.0,
        stop_loss_price=95.0,
        take_profit_price=110.0,
        open_time=ct,
        timeout_time=ct + 7 * 24 * 3600 * 1000,
        signal_time=ot,
        status="closed",
        entry_order_id=None,
        sl_order_id=None,
        tp_order_id=None,
        exit_price=105.0,
        exit_time=ct + 1000,
        exit_reason="take_profit",
        created_at=str(int(time.time() * 1000)),
    )
    store.upsert_trade(closed_row)
    store.close()

    engine = LiveEngine(cfg)
    runner = engine._runners[0]

    class _StubStrategy:
        def compute_features(self, master):
            pass

        def get_signal(self, sym, open_time):
            return Signal(direction=1, weight=100)

    runner.strategy = _StubStrategy()
    runner._inner_strategy = _StubStrategy()
    runner._master = pd.DataFrame(
        {
            "symbol": ["BTCUSDT"],
            "open_time": [ot],
            "close_time": [ct],
            "open": [100.0],
            "high": [100.0],
            "low": [100.0],
            "close": [100.0],
        }
    )

    buf = io.StringIO()
    with redirect_stdout(buf):
        engine._catch_up_model(runner)
    out = buf.getvalue()

    # The handler should have printed the suppression message.
    assert "catch-up duplicate suppressed" in out, (
        f"Expected 'catch-up duplicate suppressed' in stdout, got:\n{out}"
    )

    # And no extra row should exist.
    store2 = StateStore(db_path)
    rows = store2.get_all_trades()
    store2.close()
    assert len(rows) == 1, f"Expected 1 row after collision, got {len(rows)}"
