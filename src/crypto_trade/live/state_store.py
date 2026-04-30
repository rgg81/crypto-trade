"""SQLite persistence for live trades and engine state.

Uses WAL journal mode for crash safety. Separate DB files for live vs dry-run
to prevent accidental data mixing (following Freqtrade pattern).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from crypto_trade.live.models import LiveTrade


class StateStoreMigrationError(RuntimeError):
    """Raised when an existing DB cannot be opened because of legacy duplicates."""


_TRADES_DDL = """\
CREATE TABLE IF NOT EXISTS trades (
    id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    direction INTEGER NOT NULL,
    entry_price REAL NOT NULL,
    amount_usd REAL NOT NULL,
    weight_factor REAL NOT NULL,
    stop_loss_price REAL NOT NULL,
    take_profit_price REAL NOT NULL,
    open_time INTEGER NOT NULL,
    timeout_time INTEGER NOT NULL,
    signal_time INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    entry_order_id TEXT,
    sl_order_id TEXT,
    tp_order_id TEXT,
    exit_price REAL,
    exit_time INTEGER,
    exit_reason TEXT,
    created_at TEXT NOT NULL
)"""

_ENGINE_STATE_DDL = """\
CREATE TABLE IF NOT EXISTS engine_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
)"""

_TRADES_NATKEY_INDEX_DDL = """\
CREATE UNIQUE INDEX IF NOT EXISTS ux_trades_natkey
ON trades(model_name, symbol, open_time)
"""

_COUNT_NATKEY_DUPLICATES = """\
SELECT COUNT(*) FROM (
    SELECT model_name, symbol, open_time
    FROM trades
    GROUP BY 1, 2, 3
    HAVING COUNT(*) > 1
)
"""

_UPSERT_TRADE = """\
INSERT INTO trades (
    id, model_name, symbol, direction, entry_price, amount_usd, weight_factor,
    stop_loss_price, take_profit_price, open_time, timeout_time, signal_time,
    status, entry_order_id, sl_order_id, tp_order_id,
    exit_price, exit_time, exit_reason, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    status=excluded.status,
    entry_order_id=excluded.entry_order_id,
    sl_order_id=excluded.sl_order_id,
    tp_order_id=excluded.tp_order_id,
    exit_price=excluded.exit_price,
    exit_time=excluded.exit_time,
    exit_reason=excluded.exit_reason
"""

_TRADE_COLUMNS = (
    "id",
    "model_name",
    "symbol",
    "direction",
    "entry_price",
    "amount_usd",
    "weight_factor",
    "stop_loss_price",
    "take_profit_price",
    "open_time",
    "timeout_time",
    "signal_time",
    "status",
    "entry_order_id",
    "sl_order_id",
    "tp_order_id",
    "exit_price",
    "exit_time",
    "exit_reason",
    "created_at",
)


def _row_to_trade(row: tuple) -> LiveTrade:
    return LiveTrade(**dict(zip(_TRADE_COLUMNS, row)))


class StateStore:
    """SQLite-backed persistence for live trades and engine key-value state."""

    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(_TRADES_DDL)
        self._conn.execute(_ENGINE_STATE_DDL)
        try:
            self._conn.execute(_TRADES_NATKEY_INDEX_DDL)
        except sqlite3.IntegrityError as exc:
            n_dups = self._count_natural_key_duplicates()
            raise StateStoreMigrationError(
                f"DB at {db_path} has {n_dups} duplicate (model_name, symbol, "
                f"open_time) groups from prior runs. The new schema requires "
                f"uniqueness.\n\n"
                f"For dry_run/testnet DBs (no real money): rm {db_path} and re-seed.\n"
                f"For real-money live.db: run\n"
                f"  uv run python scripts/dedupe_trades.py --db {db_path}\n"
                f"(interactive — prints what would be removed for review before "
                f"applying)."
            ) from exc
        self._conn.commit()

    def _count_natural_key_duplicates(self) -> int:
        """Count (model_name, symbol, open_time) groups with >1 rows."""
        row = self._conn.execute(_COUNT_NATKEY_DUPLICATES).fetchone()
        return int(row[0]) if row else 0

    # -- Trades --

    def upsert_trade(self, trade: LiveTrade) -> None:
        self._conn.execute(
            _UPSERT_TRADE,
            (
                trade.id,
                trade.model_name,
                trade.symbol,
                trade.direction,
                trade.entry_price,
                trade.amount_usd,
                trade.weight_factor,
                trade.stop_loss_price,
                trade.take_profit_price,
                trade.open_time,
                trade.timeout_time,
                trade.signal_time,
                trade.status,
                trade.entry_order_id,
                trade.sl_order_id,
                trade.tp_order_id,
                trade.exit_price,
                trade.exit_time,
                trade.exit_reason,
                trade.created_at,
            ),
        )
        self._conn.commit()

    def get_open_trades(self, model_name: str | None = None) -> list[LiveTrade]:
        if model_name is not None:
            rows = self._conn.execute(
                "SELECT * FROM trades WHERE status = 'open' AND model_name = ?",
                (model_name,),
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM trades WHERE status = 'open'").fetchall()
        return [_row_to_trade(r) for r in rows]

    def get_trade(self, trade_id: str) -> LiveTrade | None:
        row = self._conn.execute("SELECT * FROM trades WHERE id = ?", (trade_id,)).fetchone()
        return _row_to_trade(row) if row else None

    def close_trade(
        self,
        trade_id: str,
        exit_price: float,
        exit_time: int,
        exit_reason: str,
    ) -> None:
        self._conn.execute(
            "UPDATE trades SET status='closed', exit_price=?, exit_time=?, exit_reason=? "
            "WHERE id=?",
            (exit_price, exit_time, exit_reason, trade_id),
        )
        self._conn.commit()

    def get_all_trades(self) -> list[LiveTrade]:
        rows = self._conn.execute("SELECT * FROM trades ORDER BY open_time").fetchall()
        return [_row_to_trade(r) for r in rows]

    # -- Engine state KV --

    def set_state(self, key: str, value: str) -> None:
        self._conn.execute(
            "INSERT INTO engine_state (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self._conn.commit()

    def get_state(self, key: str) -> str | None:
        row = self._conn.execute("SELECT value FROM engine_state WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    # -- Lifecycle --

    def close(self) -> None:
        self._conn.close()
