# Seed/catch-up Handshake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate the duplicate-trade failure mode in the `seed-live-db` + `live` flow by introducing a per-(model, symbol) boundary key that the seeder writes and the engine reads, plus a `(model_name, symbol, open_time)` UNIQUE INDEX as defense-in-depth.

**Architecture:** Two coupled mechanisms. (1) Boundary handshake: seeder writes `seeded_through_<model>_<sym>` engine_state keys; catch-up reads them and skips trade-creation in seeded territory. (2) UNIQUE INDEX `ux_trades_natkey ON trades(model_name, symbol, open_time)`; catch-up wraps insertion in `try/except IntegrityError`; seeder uses `INSERT OR IGNORE` semantics; existing DBs with duplicates abort on open with a pointer to `scripts/dedupe_trades.py`.

**Tech Stack:** Python 3.13, sqlite3 (stdlib), pytest, argparse, pandas (for CSV parsing in seeder).

**Spec:** `docs/superpowers/specs/2026-04-30-seed-catchup-handshake-design.md`

---

## File map

**Create:**
- `scripts/dedupe_trades.py` — interactive legacy-DB dedupe tool
- `tests/live/test_state_store_natkey.py` — uniqueness/migration tests
- `tests/live/test_catchup_safety.py` — safety regression (no signed endpoints from catch-up)

**Modify:**
- `src/crypto_trade/live/state_store.py` — add UNIQUE INDEX, `StateStoreMigrationError`, `_count_natural_key_duplicates`
- `src/crypto_trade/live/db_seeder.py` — write `seeded_through_*` keys, idempotent re-run, exit-reason-driven open/closed split, `--reseed` semantics, drop `as_of_ms` parameter
- `src/crypto_trade/live/engine.py` — pre-load `seeded_through` and `cooldown_until` dicts in `_catch_up_model`, add boundary check in trade-creation block, wrap upsert in try/except
- `src/crypto_trade/main.py` — drop `--as-of`, `--catch-up-from`, `--catch-up-days`; add `--reseed`
- `tests/live/test_db_seeder.py` — update existing tests, add new tests for boundary keys, exit_reason split, idempotency, `--reseed`
- `tests/live/test_engine_v2.py` — delete CLI tests for removed flags, add boundary + cooldown pre-load tests
- `CLAUDE.md` — drop date flags, document boundary handshake

---

## Task ordering rationale

1. Lock in the existing safety property (catch-up never calls signed endpoints) FIRST so subsequent edits can't regress it silently.
2. Land schema + collision handling TOGETHER — the unique index alone would crash the engine on a no-seed restart, because catch-up re-creates trades each run today. The wrapped upsert makes restart graceful.
3. Seeder boundary writing (engine still ignores keys) → engine boundary reading (handshake live) → CLI cleanup → migration tooling → docs.

Each task is committable on its own and leaves the system in a working state.

---

## Task 1: Lock in catch-up safety regression tests

**Goal:** Add tests asserting that `engine._catch_up_model` (a) does not call signed Binance endpoints and (b) contains no `self._auth` reference. No code change.

**Files:**
- Create: `tests/live/test_catchup_safety.py`

- [ ] **Step 1: Write the mock-based safety test**

Create `tests/live/test_catchup_safety.py`:

```python
"""Catch-up safety regression tests.

Property: regardless of dry_run/testnet/live mode, _catch_up_model must never
place real Binance orders. The first real order happens only after catch-up
returns and the live tick loop opens a position via OrderManager.open_trade.
"""
from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from crypto_trade.live.engine import LiveEngine
from crypto_trade.live.models import COMBINED_MODELS, LiveConfig


@pytest.mark.parity
def test_catch_up_never_calls_signed_endpoints(tmp_path):
    """_catch_up_model in dry_run=False mode must not place Binance orders."""
    cfg = LiveConfig(
        models=COMBINED_MODELS,
        dry_run=False,                 # live mode
        db_path=tmp_path / "safety.db",
        data_dir=Path("data"),
        catch_up_lookback_days=30,     # short window — even an empty replay must not call _auth
    )
    engine = LiveEngine(cfg)
    auth_mock = MagicMock()
    engine._auth_client = auth_mock
    engine._order_mgr._auth = auth_mock

    engine.catch_up_only()

    auth_mock.place_market_order.assert_not_called()
    auth_mock.place_stop_market_order.assert_not_called()
    auth_mock.place_take_profit_market_order.assert_not_called()


def test_catch_up_source_has_no_auth_reference():
    """Drift guard: _catch_up_model body must not reference self._auth.

    A regex source-anchor — same style as the dba16ec paper-trade SL/TP fix
    test. If a future refactor pipes order placement through catch-up, this
    test fails before that change can land.
    """
    src = Path("src/crypto_trade/live/engine.py").read_text()
    # Match `def _catch_up_model(...)` body up to the next top-level def or
    # a clear section delimiter (`def _tick(`).
    match = re.search(
        r"def _catch_up_model\(self.*?\n    def (?:_tick|_shutdown)\(",
        src,
        flags=re.DOTALL,
    )
    assert match is not None, "Could not locate _catch_up_model in engine.py"
    body = match.group(0)
    assert "self._auth" not in body, (
        "_catch_up_model body must not reference self._auth. "
        "Catch-up creates CATCHUP-* paper rows directly via state.upsert_trade. "
        "Real order placement is the live tick's job (OrderManager.open_trade)."
    )
```

- [ ] **Step 2: Run tests to verify both pass**

Run: `uv run pytest tests/live/test_catchup_safety.py -v`
Expected: both PASS. (The property already holds in the current code; these tests lock it in.)

If `test_catch_up_never_calls_signed_endpoints` fails because data is missing for default symbols, set `catch_up_lookback_days=0` and verify no calls — the test's purpose is to catch any signed call regardless of how many candles are replayed.

- [ ] **Step 3: Commit**

```bash
git add tests/live/test_catchup_safety.py
git commit -m "test(live): regression tests for catch-up signed-endpoint safety"
```

---

## Task 2: UNIQUE INDEX + migration error + collision handling

**Goal:** Add `(model_name, symbol, open_time)` uniqueness to the trades table. Add `StateStoreMigrationError` for legacy DBs that already contain duplicates. Wrap `_catch_up_model`'s trade insertion in `try/except IntegrityError` so restart in catch-up is safe. Schema and engine handler ship together — the index alone would crash the engine on restart.

**Files:**
- Modify: `src/crypto_trade/live/state_store.py:14-99`
- Modify: `src/crypto_trade/live/engine.py:880-897` (the catch-up trade-creation block)
- Create: `tests/live/test_state_store_natkey.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/live/test_state_store_natkey.py`:

```python
"""Tests for trades(model_name, symbol, open_time) uniqueness and migration."""
from __future__ import annotations

import sqlite3
import time
import uuid
from pathlib import Path

import pytest

from crypto_trade.live.models import LiveTrade
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
    assert "1 duplicate" in msg or "1 group" in msg or "1 pair" in msg
    assert "dedupe_trades.py" in msg


def test_count_natural_key_duplicates_returns_zero_for_clean_db(tmp_path):
    store = StateStore(tmp_path / "clean.db")
    assert store._count_natural_key_duplicates() == 0


def test_count_natural_key_duplicates_after_legacy_setup(tmp_path):
    """The helper counts groups, not rows — two duplicate rows = 1 group."""
    db_path = tmp_path / "counted.db"
    # Same legacy-DB setup as test_db_open_aborts_on_existing_duplicates,
    # but bypass the index by inserting before opening via StateStore.
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
    for ot in (1_700_000_000_000, 1_700_000_000_000, 1_700_000_028_800_000):
        conn.execute(
            "INSERT INTO trades VALUES (?, 'A', 'BTCUSDT', 1, 100.0, 1000.0, 1.0, 95.0, "
            "110.0, ?, ?, ?, 'closed', NULL, NULL, NULL, 105.0, ?, 'take_profit', '0')",
            (uuid.uuid4().hex, ot, ot + 7 * 24 * 3600 * 1000, ot, ot + 100000),
        )
    conn.commit()
    conn.close()

    # Cannot open via StateStore (would raise). Verify the count helper directly
    # by attaching to the raw connection.
    conn = sqlite3.connect(str(db_path))
    n = conn.execute(
        "SELECT COUNT(*) FROM (SELECT model_name, symbol, open_time "
        "FROM trades GROUP BY 1, 2, 3 HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    conn.close()
    assert n == 1


def test_catch_up_handles_unique_collision_gracefully(tmp_path, monkeypatch):
    """Pre-insert a (model, sym, open_time) row, drive catch-up over that period,
    assert: catch-up does NOT raise, no duplicate is created, n_trades_opened
    does not increment for that candle."""
    pytest.skip(
        "Driven by Task 4 once boundary mechanism lands; placeholder for the "
        "engine-level collision integration test."
    )
```

- [ ] **Step 2: Run tests and confirm they fail**

Run: `uv run pytest tests/live/test_state_store_natkey.py -v`
Expected: imports of `StateStoreMigrationError` from `state_store` fail (NameError) → all tests error out at collection. Good — they pin the API we're about to add.

- [ ] **Step 3: Implement the schema change in state_store.py**

Edit `src/crypto_trade/live/state_store.py`:

Add after the existing imports:

```python
class StateStoreMigrationError(RuntimeError):
    """Raised when an existing DB cannot be opened because of legacy duplicates."""
```

Add after `_ENGINE_STATE_DDL`:

```python
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
```

Modify `StateStore.__init__` to attempt the index and raise on conflict. Replace lines 92-99:

```python
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
```

- [ ] **Step 4: Run state_store tests to verify they pass**

Run: `uv run pytest tests/live/test_state_store_natkey.py -v -k "not collision"`
Expected: 5 passed (the collision integration test is skipped).

- [ ] **Step 5: Run the existing state_store / db_seeder tests to confirm no regression**

Run: `uv run pytest tests/live/test_db_seeder.py -v`
Expected: all existing tests still pass — schema change is additive on fresh DBs.

- [ ] **Step 6: Wrap catch-up upsert in try/except IntegrityError**

Edit `src/crypto_trade/live/engine.py`. Add `import sqlite3` at the top of the imports (if not already there). Locate the `_catch_up_model` trade-creation block (around line 884-893) and replace:

```python
                    self._state.upsert_trade(trade)
                    self._logger.log_open(trade)
                    open_trades[sym] = trade
                    n_trades_opened += 1
```

with:

```python
                    try:
                        self._state.upsert_trade(trade)
                    except sqlite3.IntegrityError:
                        # Defense-in-depth: the boundary handshake (Task 4) is
                        # the primary mechanism for avoiding duplicates. If a
                        # row with this (model, sym, open_time) already exists
                        # (e.g., a stale CATCHUP-* from a prior run, or a
                        # SEEDED- carry-over), keep the existing row and skip.
                        print(
                            f"[live] catch-up duplicate suppressed: "
                            f"model={runner.model_config.name} sym={sym} ot={ot}"
                        )
                        continue
                    self._logger.log_open(trade)
                    open_trades[sym] = trade
                    n_trades_opened += 1
```

- [ ] **Step 7: Update the integration test in test_state_store_natkey.py**

Replace the `test_catch_up_handles_unique_collision_gracefully` test body with:

```python
def test_catch_up_handles_unique_collision_gracefully(tmp_path, monkeypatch):
    """Pre-insert a (model, sym, open_time) row that will collide with what
    catch-up wants to insert — assert catch-up logs and continues, no extra row."""
    import pandas as pd
    from crypto_trade.live.engine import LiveEngine, ModelRunner
    from crypto_trade.live.models import LiveConfig, ModelConfig

    db_path = tmp_path / "collision.db"
    cfg = LiveConfig(
        models=(ModelConfig(name="A", symbols=("BTCUSDT",)),),
        dry_run=True,
        db_path=db_path,
        data_dir=tmp_path,
        catch_up_lookback_days=1,
    )
    # Pre-seed a row that the catch-up's mocked-master would collide with.
    store = StateStore(db_path)
    store.upsert_trade(_make_trade(model_name="A", symbol="BTCUSDT",
                                    open_time=1_800_000_000_000, entry_order_id=None))
    store.close()

    # Drive catch-up using a tiny synthetic master DF that includes that exact
    # (sym, open_time). We construct a runner with a stub strategy that
    # returns a positive signal for that candle.
    engine = LiveEngine(cfg)
    runner = engine._runners[0]

    class _StubStrategy:
        def compute_features(self, master): pass
        def get_signal(self, sym, ot):
            from crypto_trade.backtest_models import Signal
            return Signal(direction=1, weight=100)

    runner.strategy = _StubStrategy()
    runner._inner_strategy = _StubStrategy()
    runner._master = pd.DataFrame({
        "symbol": ["BTCUSDT"],
        "open_time": [1_800_000_000_000],
        "close_time": [1_800_000_000_000 + 28_800_000 - 1],
        "open": [100.0], "high": [100.0], "low": [100.0], "close": [100.0],
    })

    # Should not raise.
    engine._catch_up_model(runner)

    # DB should still have exactly one row.
    store2 = StateStore(db_path)
    rows = store2.get_all_trades()
    store2.close()
    assert len(rows) == 1, f"Expected 1 row after collision, got {len(rows)}"
```

- [ ] **Step 8: Run the full integration test**

Run: `uv run pytest tests/live/test_state_store_natkey.py -v`
Expected: 6 passed.

- [ ] **Step 9: Commit**

```bash
git add src/crypto_trade/live/state_store.py src/crypto_trade/live/engine.py tests/live/test_state_store_natkey.py
git commit -m "feat(live): UNIQUE INDEX on trades natural key + catch-up collision handler

Adds CREATE UNIQUE INDEX ux_trades_natkey ON trades(model_name, symbol, open_time)
to the schema. New StateStoreMigrationError surfaces a clear message when
opening a legacy DB with existing duplicates, pointing at scripts/dedupe_trades.py.

Engine's _catch_up_model wraps trade insertion in try/except IntegrityError so
a no-seed restart (catch-up replays the same window twice) keeps the existing
row and continues, instead of crashing.

Restart-safe even before the boundary handshake (Task 4) lands."
```

---

## Task 3: Seeder writes `seeded_through_*` boundary keys, idempotent re-runs

**Goal:** After ingesting CSVs, write a `seeded_through_<model>_<sym>` engine_state key per pair = `MAX(close_time)` across seeded rows for that pair. Re-running the seeder is safe (rows that already exist are skipped via `INSERT OR IGNORE` semantics; boundary keys advance monotonically). The engine still ignores the keys at this point — Task 4 wires up the read side.

**Files:**
- Modify: `src/crypto_trade/live/db_seeder.py`
- Modify: `tests/live/test_db_seeder.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/live/test_db_seeder.py`:

```python
def test_seed_writes_boundary_keys(tmp_path):
    """After seeding, seeded_through_<model>_<sym> = MAX(close_time) per pair."""
    csv = tmp_path / "v1.csv"
    _toy_trades_csv(csv, [
        _row("BTCUSDT", 1, 1_700_000_000_000, 1_700_086_400_000, exit_reason="take_profit"),
        _row("BTCUSDT", 1, 1_700_172_800_000, 1_700_259_200_000, exit_reason="stop_loss"),
        _row("ETHUSDT", -1, 1_700_000_000_000, 1_700_086_400_000, exit_reason="timeout"),
    ])
    cfg = LiveConfig(models=BASELINE_MODELS, data_dir=tmp_path)
    db = tmp_path / "seed.db"

    seed_live_db_from_backtest(db, [csv], [], cfg)

    store = StateStore(db)
    # MAX close_time for (A, BTCUSDT) = 1_700_259_200_000
    assert store.get_state("seeded_through_A_BTCUSDT") == "1700259200000"
    # MAX close_time for (A, ETHUSDT) = 1_700_086_400_000
    assert store.get_state("seeded_through_A_ETHUSDT") == "1700086400000"


def test_seed_advances_boundary_monotonically(tmp_path):
    """Re-running with a CSV that extends further must advance the key."""
    csv1 = tmp_path / "v1a.csv"
    _toy_trades_csv(csv1, [
        _row("BTCUSDT", 1, 1_700_000_000_000, 1_700_086_400_000, exit_reason="take_profit"),
    ])
    csv2 = tmp_path / "v1b.csv"
    _toy_trades_csv(csv2, [
        _row("BTCUSDT", 1, 1_700_172_800_000, 1_700_259_200_000, exit_reason="stop_loss"),
    ])
    cfg = LiveConfig(models=BASELINE_MODELS, data_dir=tmp_path)
    db = tmp_path / "seed.db"

    seed_live_db_from_backtest(db, [csv1], [], cfg)
    seed_live_db_from_backtest(db, [csv2], [], cfg)

    store = StateStore(db)
    assert store.get_state("seeded_through_A_BTCUSDT") == "1700259200000"


def test_seed_does_not_regress_boundary_without_reseed(tmp_path):
    """Re-running with an EARLIER-extent CSV must NOT lower the boundary."""
    csv_late = tmp_path / "late.csv"
    _toy_trades_csv(csv_late, [
        _row("BTCUSDT", 1, 1_700_172_800_000, 1_700_259_200_000, exit_reason="stop_loss"),
    ])
    csv_early = tmp_path / "early.csv"
    _toy_trades_csv(csv_early, [
        _row("BTCUSDT", 1, 1_700_000_000_000, 1_700_086_400_000, exit_reason="take_profit"),
    ])
    cfg = LiveConfig(models=BASELINE_MODELS, data_dir=tmp_path)
    db = tmp_path / "seed.db"

    seed_live_db_from_backtest(db, [csv_late], [], cfg)
    seed_live_db_from_backtest(db, [csv_early], [], cfg)

    store = StateStore(db)
    # Late boundary preserved; early CSV's MAX didn't beat it.
    assert store.get_state("seeded_through_A_BTCUSDT") == "1700259200000"


def test_seed_idempotent_on_repeat(tmp_path):
    """Re-seeding the same CSV is a no-op for trade rows; result.skipped_duplicate > 0."""
    csv = tmp_path / "v1.csv"
    _toy_trades_csv(csv, [
        _row("BTCUSDT", 1, 1_700_000_000_000, 1_700_086_400_000, exit_reason="take_profit"),
        _row("BTCUSDT", 1, 1_700_172_800_000, 1_700_259_200_000, exit_reason="stop_loss"),
    ])
    cfg = LiveConfig(models=BASELINE_MODELS, data_dir=tmp_path)
    db = tmp_path / "seed.db"

    seed_live_db_from_backtest(db, [csv], [], cfg)
    counts2 = seed_live_db_from_backtest(db, [csv], [], cfg)

    store = StateStore(db)
    rows = store.get_all_trades()
    assert len(rows) == 2, f"Expected 2 rows after dedupe, got {len(rows)}"
    assert counts2.get("skipped_duplicate", 0) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/live/test_db_seeder.py::test_seed_writes_boundary_keys -v`
Expected: FAIL — `seeded_through_A_BTCUSDT` key does not exist (the seeder doesn't write it yet).

- [ ] **Step 3: Implement the boundary-key writes and idempotent insert**

Edit `src/crypto_trade/live/db_seeder.py`. Add to imports near top:

```python
import sqlite3
```

Modify the `_ingest` inner function to track BOTH `latest_close` (existing — only counts `closed` trades) and a new `latest_close_any: dict[(str, str), int]` that counts *all* seeded rows including `open` ones. Replace the `latest_close` definition (line 164) with:

```python
    latest_close: dict[tuple[str, str], int] = defaultdict(int)
    latest_close_any: dict[tuple[str, str], int] = defaultdict(int)
```

Inside `_ingest`, after the existing `if trade.status == "closed" ...` block (line 199-202), add:

```python
                # Boundary key tracks ALL seeded rows for the pair, regardless
                # of status. The key tells the engine where seeded coverage
                # ends so catch-up doesn't replay it.
                k_any = (model_name, sym)
                if trade.exit_time is not None and trade.exit_time > latest_close_any[k_any]:
                    latest_close_any[k_any] = trade.exit_time
```

Wrap `store.upsert_trade(trade)` in a try/except for idempotency. Replace line 192:

```python
                store.upsert_trade(trade)
                key = f"{track}_{trade.status}"
                counts[key] = counts.get(key, 0) + 1
```

with:

```python
                try:
                    store.upsert_trade(trade)
                except sqlite3.IntegrityError:
                    # Same (model, sym, open_time) already in DB. Idempotent
                    # re-seed: skip and keep the existing row.
                    counts["skipped_duplicate"] = counts.get("skipped_duplicate", 0) + 1
                    continue
                key = f"{track}_{trade.status}"
                counts[key] = counts.get(key, 0) + 1
```

Add `"skipped_duplicate": 0` to the `counts` dict initializer (around line 152).

After the cooldown-key write loop (around line 214), add the boundary-key write block:

```python
    # Seed seeded_through_<model>_<symbol> engine_state keys (boundary handshake).
    # Engine catch-up reads these to skip trade-creation in seeded territory.
    for (model_name, sym), max_close in latest_close_any.items():
        if max_close <= 0:
            continue
        key = f"seeded_through_{model_name}_{sym}"
        existing_raw = store.get_state(key)
        existing = int(existing_raw) if existing_raw else 0
        # Monotonic advance — re-running with an earlier CSV does NOT regress.
        new_value = max(existing, max_close)
        store.set_state(key, str(new_value))
        counts["boundary_keys"] = counts.get("boundary_keys", 0) + 1
```

Also add `"boundary_keys": 0` to the counts initializer.

- [ ] **Step 4: Run new tests to verify they pass**

Run: `uv run pytest tests/live/test_db_seeder.py -v -k "boundary or idempotent or monotonic or regress"`
Expected: 4 passed (the 4 new tests).

- [ ] **Step 5: Run all seeder tests to confirm no regression**

Run: `uv run pytest tests/live/test_db_seeder.py -v`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/crypto_trade/live/db_seeder.py tests/live/test_db_seeder.py
git commit -m "feat(seeder): write seeded_through_* boundary keys + idempotent re-seed

After ingesting all CSV rows, the seeder writes one
seeded_through_<model>_<sym> engine_state key per pair, equal to
MAX(close_time) across seeded rows. Re-running the seeder takes
MAX(existing, new) so the boundary advances monotonically.

Trade-row inserts wrapped in try/except IntegrityError: re-running
on an existing DB skips already-seeded rows (counts.skipped_duplicate
surfaces the count). The engine ignores the boundary keys at this
point — Task 4 wires up the read side."
```

---

## Task 4: Engine catch-up reads boundary keys + pre-loads cooldown_until

**Goal:** Catch-up's `_catch_up_model` pre-loads two dicts at the top: `seeded_through` (from boundary keys) and `cooldown_until` (from the `cooldown_<model>_<sym>` keys the seeder already writes). The trade-creation block gets one more guard: `ot > seeded_through.get(sym, 0)`. Together these eliminate the duplicate-trade scenario in the seeded period AND respect cooldowns extending past the boundary.

**Files:**
- Modify: `src/crypto_trade/live/engine.py:738-845` (the catch-up function)
- Modify: `tests/live/test_engine_v2.py` (add tests)

- [ ] **Step 1: Write the failing tests**

Add to `tests/live/test_engine_v2.py` (at the end of file):

```python
# ----------------------------- Boundary handshake (Task 4) ------------------


def _build_minimal_engine(tmp_path, models, dry_run=True):
    """Helper: spin up a LiveEngine with the smallest possible config for
    catch-up unit tests. Caller must populate the master DF on each runner."""
    from crypto_trade.live.engine import LiveEngine
    from crypto_trade.live.models import LiveConfig

    cfg = LiveConfig(
        models=models,
        dry_run=dry_run,
        db_path=tmp_path / "engine_test.db",
        data_dir=tmp_path,
        catch_up_lookback_days=400,  # broad — let the master DF dictate range
    )
    return LiveEngine(cfg)


def test_catch_up_skips_seeded_territory(tmp_path):
    """Pre-write seeded_through_A_BTCUSDT; assert catch-up does not open a
    CATCHUP-* trade for any candle whose open_time <= boundary."""
    import pandas as pd
    from crypto_trade.backtest_models import Signal
    from crypto_trade.live.models import ModelConfig
    from crypto_trade.live.state_store import StateStore

    boundary_ms = 1_800_000_000_000
    cfg_models = (ModelConfig(name="A", symbols=("BTCUSDT",)),)
    db = tmp_path / "engine_test.db"

    # Pre-write the boundary
    store = StateStore(db)
    store.set_state("seeded_through_A_BTCUSDT", str(boundary_ms))
    store.close()

    engine = _build_minimal_engine(tmp_path, cfg_models)
    runner = engine._runners[0]

    class _StubStrategy:
        def compute_features(self, master): pass
        def get_signal(self, sym, ot): return Signal(direction=1, weight=100)

    runner.strategy = _StubStrategy()
    runner._inner_strategy = _StubStrategy()
    # Master DF: one candle BEFORE the boundary, one AT the boundary, one AFTER
    runner._master = pd.DataFrame({
        "symbol": ["BTCUSDT"] * 3,
        "open_time": [boundary_ms - 28_800_000, boundary_ms, boundary_ms + 28_800_000],
        "close_time": [
            boundary_ms - 1,
            boundary_ms + 28_800_000 - 1,
            boundary_ms + 2 * 28_800_000 - 1,
        ],
        "open": [100.0] * 3,
        "high": [100.0] * 3,
        "low": [100.0] * 3,
        "close": [100.0] * 3,
    })

    engine._catch_up_model(runner)

    store = StateStore(db)
    trades = store.get_all_trades()
    store.close()
    # Only one trade allowed: the one at boundary_ms + 28_800_000 (post-boundary).
    assert len(trades) == 1, f"Expected 1 post-boundary trade, got {len(trades)}"
    assert trades[0].open_time == boundary_ms + 28_800_000


def test_catch_up_preloads_cooldown_keys(tmp_path):
    """A seeded cooldown_<model>_<sym> key extending past the boundary must be
    honored by catch-up — no trade opens during the cooldown window."""
    import pandas as pd
    from crypto_trade.backtest_models import Signal
    from crypto_trade.live.models import ModelConfig
    from crypto_trade.live.state_store import StateStore

    candle_ms = 28_800_000
    boundary_ms = 1_800_000_000_000
    # Cooldown extends 2 candles past the boundary
    cooldown_until = boundary_ms + 2 * candle_ms
    cfg_models = (ModelConfig(name="A", symbols=("BTCUSDT",)),)
    db = tmp_path / "engine_test.db"

    store = StateStore(db)
    store.set_state("seeded_through_A_BTCUSDT", str(boundary_ms))
    store.set_state("cooldown_A_BTCUSDT", str(cooldown_until))
    store.close()

    engine = _build_minimal_engine(tmp_path, cfg_models)
    runner = engine._runners[0]

    class _StubStrategy:
        def compute_features(self, master): pass
        def get_signal(self, sym, ot): return Signal(direction=1, weight=100)

    runner.strategy = _StubStrategy()
    runner._inner_strategy = _StubStrategy()
    runner._master = pd.DataFrame({
        "symbol": ["BTCUSDT"] * 3,
        "open_time": [
            boundary_ms + candle_ms,        # post-boundary, BUT inside cooldown
            boundary_ms + 2 * candle_ms,    # post-boundary, AT cooldown end
            boundary_ms + 3 * candle_ms,    # post-boundary, post-cooldown
        ],
        "close_time": [
            boundary_ms + 2 * candle_ms - 1,
            boundary_ms + 3 * candle_ms - 1,
            boundary_ms + 4 * candle_ms - 1,
        ],
        "open": [100.0] * 3,
        "high": [100.0] * 3,
        "low": [100.0] * 3,
        "close": [100.0] * 3,
    })

    engine._catch_up_model(runner)

    store = StateStore(db)
    trades = store.get_all_trades()
    store.close()
    # Only the 3rd candle (post-cooldown) may produce a trade.
    assert len(trades) == 1, f"Expected 1 trade post-cooldown, got {len(trades)}"
    assert trades[0].open_time == boundary_ms + 3 * candle_ms


def test_catch_up_with_no_seeded_keys_replays_normally(tmp_path):
    """No boundary key → behavior matches today's no-seed start. All in-window
    candles produce trades."""
    import pandas as pd
    from crypto_trade.backtest_models import Signal
    from crypto_trade.live.models import ModelConfig

    candle_ms = 28_800_000
    base = 1_800_000_000_000
    cfg_models = (ModelConfig(name="A", symbols=("BTCUSDT",)),)

    engine = _build_minimal_engine(tmp_path, cfg_models)
    runner = engine._runners[0]

    class _StubStrategy:
        def compute_features(self, master): pass
        def get_signal(self, sym, ot): return Signal(direction=1, weight=100)

    runner.strategy = _StubStrategy()
    runner._inner_strategy = _StubStrategy()
    runner._master = pd.DataFrame({
        "symbol": ["BTCUSDT"] * 2,
        "open_time": [base, base + candle_ms],
        "close_time": [base + candle_ms - 1, base + 2 * candle_ms - 1],
        "open": [100.0] * 2,
        "high": [100.0] * 2,
        "low": [100.0] * 2,
        "close": [100.0] * 2,
    })

    engine._catch_up_model(runner)

    from crypto_trade.live.state_store import StateStore
    store = StateStore(tmp_path / "engine_test.db")
    trades = store.get_all_trades()
    store.close()
    # First candle opens a trade. Second candle is blocked by the catch-up's
    # local "sym in open_trades" guard (a trade is currently open on candle 1).
    # That's existing behavior — no boundary involved.
    assert len(trades) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/live/test_engine_v2.py::test_catch_up_skips_seeded_territory -v`
Expected: FAIL — without the boundary check, both pre-boundary and post-boundary candles would generate trades. Test asserts only 1 post-boundary trade.

- [ ] **Step 3: Implement boundary + cooldown pre-load**

Edit `src/crypto_trade/live/engine.py`. In `_catch_up_model`, locate the `cooldown_until: dict[str, int] = {}` line (around line 773) and the surrounding init block. Replace:

```python
        cooldown_until: dict[str, int] = {}
        n_signals = 0
        n_trades_opened = 0
        n_trades_closed = 0
```

with:

```python
        # Pre-load both dicts from engine_state so the seeder's boundary keys
        # and post-trade cooldown keys are honored from the very first candle.
        cooldown_until: dict[str, int] = {}
        seeded_through: dict[str, int] = {}
        for sym in runner.model_config.symbols:
            cd_raw = self._state.get_state(
                f"cooldown_{runner.model_config.name}_{sym}"
            )
            if cd_raw:
                cooldown_until[sym] = int(cd_raw)
            sb_raw = self._state.get_state(
                f"seeded_through_{runner.model_config.name}_{sym}"
            )
            if sb_raw:
                seeded_through[sym] = int(sb_raw)
        if seeded_through or cooldown_until:
            print(
                f"[live] Model {runner.model_config.name} catch-up boundary: "
                f"{len(seeded_through)} seeded keys, {len(cooldown_until)} cooldown keys"
            )

        n_signals = 0
        n_trades_opened = 0
        n_trades_closed = 0
```

Locate the trade-creation gate (around line 854-859). Replace:

```python
            sig = runner.strategy.get_signal(sym, ot)
            if sig.direction != 0 and sig.weight > 0:
                n_signals += 1
                if (
                    sym not in open_trades
                    and ot >= cooldown_until.get(sym, 0)
                    and ot >= self._risk_cooldown_until.get(sym, 0)
                ):
```

with:

```python
            sig = runner.strategy.get_signal(sym, ot)
            if sig.direction != 0 and sig.weight > 0:
                n_signals += 1
                if (
                    sym not in open_trades
                    and ot >= cooldown_until.get(sym, 0)
                    and ot >= self._risk_cooldown_until.get(sym, 0)
                    and ot > seeded_through.get(sym, 0)
                ):
```

- [ ] **Step 4: Run new tests to verify they pass**

Run: `uv run pytest tests/live/test_engine_v2.py -v -k "boundary or seeded or catch_up_preloads or no_seeded"`
Expected: all 3 new tests pass.

- [ ] **Step 5: Run the full engine test suite to confirm no regression**

Run: `uv run pytest tests/live/test_engine_v2.py -v`
Expected: all pass (including pre-existing tests).

- [ ] **Step 6: Commit**

```bash
git add src/crypto_trade/live/engine.py tests/live/test_engine_v2.py
git commit -m "feat(live): catch-up reads boundary + cooldown engine_state keys

_catch_up_model pre-loads two dicts from engine_state at the top:
- seeded_through_<model>_<sym> (written by db_seeder.seed_live_db_from_backtest)
- cooldown_<model>_<sym> (the standard 2-candle post-trade cooldown)

The trade-creation gate gains one more condition:
    ot > seeded_through.get(sym, 0)

This is the primary mechanism preventing duplicate trades in the
seeded period. The UNIQUE INDEX from Task 2 remains the safety net
for any case the boundary mechanism doesn't cover (e.g., restart
in catch-up of a no-seed run)."
```

---

## Task 5: Seeder uses `exit_reason='end_of_data'` for open/closed split; remove `--as-of`; add `--reseed`

**Goal:** Drop the `as_of_ms` parameter from `seed_live_db_from_backtest`. Seeder always ingests every CSV row; trades with `exit_reason='end_of_data'` become `status='open'` with `entry_order_id='SEEDED'` and full intended-exit info, everything else becomes `status='closed'`. Remove `--as-of` from the CLI. Add `--reseed` flag that overwrites existing `seeded_through_*` keys (instead of monotonic advance) — useful for "I changed my CSVs and want a fresh boundary".

**Files:**
- Modify: `src/crypto_trade/live/db_seeder.py`
- Modify: `src/crypto_trade/main.py`
- Modify: `tests/live/test_db_seeder.py`

- [ ] **Step 1: Update / write tests**

Edit `tests/live/test_db_seeder.py`:

Delete `test_seed_as_of_splits_open_vs_closed` (around lines 147-185).

Add the replacement and `--reseed` tests at the end:

```python
def test_seed_split_uses_exit_reason(tmp_path):
    """exit_reason='end_of_data' → SEEDED open. Everything else → closed."""
    csv = tmp_path / "v1.csv"
    _toy_trades_csv(csv, [
        _row("BTCUSDT", 1, 1_700_000_000_000, 1_700_086_400_000, exit_reason="take_profit"),
        _row("BTCUSDT", 1, 1_700_172_800_000, 1_700_259_200_000, exit_reason="stop_loss"),
        _row("ETHUSDT", -1, 1_700_300_000_000, 1_700_400_000_000, exit_reason="end_of_data"),
    ])
    cfg = LiveConfig(models=BASELINE_MODELS, data_dir=tmp_path)
    db = tmp_path / "seed.db"

    seed_live_db_from_backtest(db, [csv], [], cfg)

    store = StateStore(db)
    rows = store.get_all_trades()
    by_sym = {r.symbol: r for r in rows}
    assert by_sym["ETHUSDT"].status == "open"
    assert by_sym["ETHUSDT"].entry_order_id == "SEEDED"
    assert by_sym["ETHUSDT"].exit_time == 1_700_400_000_000  # intended exit
    assert by_sym["ETHUSDT"].exit_reason == "end_of_data"
    # The two BTC trades — the second is the latest, status='closed'
    btc_closed = [r for r in rows if r.symbol == "BTCUSDT"]
    assert all(r.status == "closed" for r in btc_closed)


def test_seed_reseed_overwrites_boundary(tmp_path):
    """reseed=True must replace the boundary key, even if the new value is lower."""
    csv_late = tmp_path / "late.csv"
    _toy_trades_csv(csv_late, [
        _row("BTCUSDT", 1, 1_700_172_800_000, 1_700_259_200_000, exit_reason="stop_loss"),
    ])
    csv_early = tmp_path / "early.csv"
    _toy_trades_csv(csv_early, [
        _row("BTCUSDT", 1, 1_700_000_000_000, 1_700_086_400_000, exit_reason="take_profit"),
    ])
    cfg = LiveConfig(models=BASELINE_MODELS, data_dir=tmp_path)
    db = tmp_path / "seed.db"

    seed_live_db_from_backtest(db, [csv_late], [], cfg)
    seed_live_db_from_backtest(db, [csv_early], [], cfg, reseed=True)

    store = StateStore(db)
    assert store.get_state("seeded_through_A_BTCUSDT") == "1700086400000"


def test_seed_signature_no_as_of_kwarg():
    """Smoke check: as_of_ms is no longer a valid kwarg."""
    import inspect
    sig = inspect.signature(seed_live_db_from_backtest)
    assert "as_of_ms" not in sig.parameters
    assert "reseed" in sig.parameters
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/live/test_db_seeder.py -v -k "exit_reason or reseed_overwrites or no_as_of"`
Expected: FAIL — `as_of_ms` still in signature, `reseed` not yet.

- [ ] **Step 3: Modify the seeder**

Edit `src/crypto_trade/live/db_seeder.py`. Modify `_row_to_trade` (lines 64-122). Drop the `as_of_ms` parameter; replace the open/closed split logic. Replace the function with:

```python
def _row_to_trade(
    row: pd.Series,
    model_name: str,
    timeout_minutes: int,
    max_amount_usd: float,
) -> LiveTrade | None:
    """Convert a backtest CSV row to a LiveTrade. Returns None if the row should be skipped.

    Open vs closed: a row whose exit_reason is 'end_of_data' represents a
    trade that was still open at the CSV's data extent — the live engine
    inherits it as a SEEDED open and re-evaluates SL/TP/timeout against
    new candles. Any other exit_reason means the trade really closed.
    """
    weight_factor = float(row["weight_factor"])
    if weight_factor <= 0.0:
        return None  # BTC-killed v2 row — never in live DB

    open_time = int(row["open_time"])
    close_time = int(row["close_time"])
    direction = int(row["direction"])
    entry_price = float(row["entry_price"])
    exit_price = float(row["exit_price"])
    exit_reason = str(row["exit_reason"])

    is_still_open = exit_reason == "end_of_data"

    return LiveTrade(
        model_name=model_name,
        symbol=str(row["symbol"]),
        direction=direction,
        entry_price=entry_price,
        amount_usd=weight_factor * max_amount_usd,
        weight_factor=weight_factor,
        stop_loss_price=entry_price,
        take_profit_price=entry_price,
        open_time=open_time,
        timeout_time=open_time + timeout_minutes * 60 * 1000,
        signal_time=open_time,
        status="open" if is_still_open else "closed",
        # Sentinel order IDs distinguish seeded open trades from genuine
        # live-opened ones in `_reconcile` and `_catch_up_model`.
        entry_order_id="SEEDED" if is_still_open else None,
        sl_order_id=None,
        tp_order_id=None,
        exit_price=exit_price,
        exit_time=close_time,
        exit_reason=exit_reason,
    )
```

Modify `seed_live_db_from_backtest` signature and body. Replace the function definition (line 122) and remove the `as_of_ms` skip:

```python
def seed_live_db_from_backtest(
    db_path: Path,
    v1_trades_csvs: list[Path],
    v2_trades_csvs: list[Path],
    live_config: LiveConfig,
    reseed: bool = False,
) -> dict[str, int]:
    """Seed `db_path` with backtest trades, cooldown keys, and boundary keys.

    Args:
        db_path: target SQLite DB. Existing rows kept; UNIQUE constraint
            makes re-running idempotent (skipped_duplicate count surfaces
            already-seeded rows).
        v1_trades_csvs / v2_trades_csvs: paths to backtest CSVs.
        live_config: drives symbol → model mapping and cooldown_candles.
        reseed: if True, overwrite seeded_through_* keys with the new
            CSV's boundary, even if the new value is lower than what's
            already in the DB. Default (False) advances boundaries
            monotonically (MAX(existing, new)).
    """
```

Inside `_ingest`, drop the `if as_of_ms is not None and int(row["open_time"]) >= as_of_ms:` skip block (around line 179-181) entirely. Drop the `as_of_ms` argument when calling `_row_to_trade` (line 186) — the simplified signature no longer takes it.

Also drop `"skipped_after_cutoff": 0` from the counts initializer.

In the boundary-key write loop (added in Task 3), use `reseed` to short-circuit the monotonic check:

```python
    for (model_name, sym), max_close in latest_close_any.items():
        if max_close <= 0:
            continue
        key = f"seeded_through_{model_name}_{sym}"
        if reseed:
            new_value = max_close
        else:
            existing_raw = store.get_state(key)
            existing = int(existing_raw) if existing_raw else 0
            new_value = max(existing, max_close)
        store.set_state(key, str(new_value))
        counts["boundary_keys"] = counts.get("boundary_keys", 0) + 1
```

- [ ] **Step 4: Modify the CLI**

Edit `src/crypto_trade/main.py`. Locate the `seed-live-db` argparse setup (around lines 300-340). Delete the `--as-of` argument:

```python
    seed_parser.add_argument(
        "--as-of",
        type=str,
        default=None,
        help=...,
    )
```

(Lines 336-343, the `--as-of` block — delete it entirely.)

Add immediately after the existing `--track` arg block:

```python
    seed_parser.add_argument(
        "--reseed",
        action="store_true",
        help=(
            "Overwrite seeded_through_* boundary keys with this CSV's "
            "data extent, even if existing keys are higher. Default is "
            "monotonic advance (MAX(existing, new))."
        ),
    )
```

In `_cmd_seed_live_db` (around line 930-1000), drop the `as_of_ms` derivation block (around line 967-970):

```python
    as_of_ms = None
    if args.as_of is not None:
        as_of_ms = int(pd.Timestamp(args.as_of, tz="UTC").value // 1_000_000)
```

(Delete the block.)

In the call to `seed_live_db_from_backtest` (around line 979), drop `as_of_ms=as_of_ms,` and add `reseed=args.reseed,`:

```python
    counts = seed_live_db_from_backtest(
        db_path=db_path,
        v1_trades_csvs=v1_paths,
        v2_trades_csvs=v2_paths,
        live_config=cfg,
        reseed=args.reseed,
    )
```

Drop the `if as_of_ms is not None: print(f"[seed] as-of cutoff: ...")` block (around line 974-977).

- [ ] **Step 5: Run all seeder tests**

Run: `uv run pytest tests/live/test_db_seeder.py -v`
Expected: all pass, including the new exit_reason / reseed / no-as-of tests.

- [ ] **Step 6: Run all CLI / engine tests**

Run: `uv run pytest tests/live/ -v`
Expected: all pass except possibly tests that referenced `--as-of` directly. If any fail, those are removed in this same task — update the assertions or delete obsolete test cases.

- [ ] **Step 7: Commit**

```bash
git add src/crypto_trade/live/db_seeder.py src/crypto_trade/main.py tests/live/test_db_seeder.py
git commit -m "feat(seeder): exit_reason-driven open/closed split; --as-of removed; --reseed added

Drops the seeder's as_of_ms parameter. The open/closed split now
uses the CSV's exit_reason field directly: 'end_of_data' rows
become SEEDED open with intended-exit info; any other exit_reason
becomes status='closed'. This is the natural signal that a backtest
trade was still open at data extent.

CLI: --as-of removed from seed-live-db. New --reseed flag
overwrites seeded_through_* keys (vs default monotonic advance)
for the 'I changed my CSVs and want fresh boundaries' case."
```

---

## Task 6: Remove `--catch-up-from` and `--catch-up-days` CLI flags

**Goal:** Drop both CLI flags from `live`. `LiveConfig.catch_up_lookback_days` keeps its default of 90 and remains tunable via `LiveConfig(...)` for parity tests and scripts that import the engine directly.

**Files:**
- Modify: `src/crypto_trade/main.py`
- Modify: `tests/live/test_engine_v2.py`

- [ ] **Step 1: Identify and delete the CLI tests**

Edit `tests/live/test_engine_v2.py`. Delete the following tests (search for the names):
- `test_cli_live_catch_up_from_flag`
- `test_cli_live_catch_up_days_flag` (if present)
- The mutually-exclusive group test (it tests `["live", "--catch-up-days", "60", "--catch-up-from", "2025-03-24"]` raises SystemExit)
- `test_cmd_live_propagates_catch_up_from_to_config`
- `test_cli_live_catch_up_from_default_none` (tests `args.catch_up_from is None`)

- [ ] **Step 2: Modify the CLI**

Edit `src/crypto_trade/main.py`. Locate the `live` argparse setup (around lines 280-298). Delete the entire mutually-exclusive group:

```python
    catch_up_group = live_parser.add_mutually_exclusive_group()
    catch_up_group.add_argument("--catch-up-days", ...)
    catch_up_group.add_argument("--catch-up-from", ...)
```

(Lines 280-298 — delete the group setup entirely.)

In `_cmd_live` (around lines 803-905), drop the `catch_up_kwargs` construction (around lines 825-845):

```python
    catch_up_kwargs: dict = {}
    if args.catch_up_days is not None:
        ...
    elif args.catch_up_from is not None:
        ...
```

(Delete the whole block.)

In the `LiveConfig(...)` call (around line 875-890), drop `**catch_up_kwargs,`:

```python
    config = LiveConfig(
        models=selected_models,
        ...
        testnet=testnet,
    )
```

- [ ] **Step 3: Run all tests**

Run: `uv run pytest tests/live/ -v`
Expected: all pass. The tests we deleted are gone; remaining tests don't depend on the flags.

- [ ] **Step 4: Commit**

```bash
git add src/crypto_trade/main.py tests/live/test_engine_v2.py
git commit -m "feat(live): remove --catch-up-from and --catch-up-days CLI flags

The boundary handshake (Task 4) makes manual catch-up date alignment
unnecessary. LiveConfig.catch_up_lookback_days keeps its 90-day default
and remains tunable for parity tests / direct LiveConfig() callers."
```

---

## Task 7: Add `scripts/dedupe_trades.py` for legacy DB migration

**Goal:** A standalone script that surfaces duplicate-key groups in a legacy DB and removes the lower-priority ones, with a dry-run-by-default flow. Priority order (highest first): real Binance fills (numeric `entry_order_id`), seeded `closed` rows (`entry_order_id IS NULL`), `SEEDED-*`, then `CATCHUP-*` / `DRY-*`.

**Files:**
- Create: `scripts/dedupe_trades.py`
- Create: `tests/scripts/test_dedupe_trades.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/scripts/__init__.py` (empty — marks as package).

Create `tests/scripts/test_dedupe_trades.py`:

```python
"""Tests for scripts/dedupe_trades.py priority-based picker."""
from __future__ import annotations

import sqlite3
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from dedupe_trades import (  # type: ignore[import-not-found]
    classify_priority,
    pick_keeper,
    plan_dedupe,
)


def test_classify_priority_real_money_highest():
    """Numeric entry_order_id (real Binance fill) gets the highest priority."""
    p = classify_priority({"entry_order_id": "1234567890", "created_at": "0"})
    assert p == 0  # 0 = highest


def test_classify_priority_seeded_closed():
    """entry_order_id IS NULL → seeded 'closed' row from CSV (priority 1)."""
    p = classify_priority({"entry_order_id": None, "created_at": "0"})
    assert p == 1


def test_classify_priority_seeded_open():
    """SEEDED-* prefix (open seeded carry-over) → priority 2."""
    p = classify_priority({"entry_order_id": "SEEDED", "created_at": "0"})
    assert p == 2


def test_classify_priority_catchup_lowest():
    """CATCHUP-* and DRY-* → priority 3 (lowest, deletable)."""
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
    """Same priority tier → oldest created_at wins."""
    rows = [
        {"id": "id-newer", "entry_order_id": "CATCHUP-aaaa", "created_at": "200"},
        {"id": "id-older", "entry_order_id": "CATCHUP-bbbb", "created_at": "100"},
    ]
    keeper = pick_keeper(rows)
    assert keeper["id"] == "id-older"


def test_plan_dedupe_dry_run(tmp_path):
    """plan_dedupe (no --apply) returns the list of (group, kept_id, removed_ids)
    without touching the DB."""
    db_path = tmp_path / "legacy.db"
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
    # Two duplicate rows: a CATCHUP-* and a seeded-closed (NULL entry_order_id)
    for entry_id, created in [("CATCHUP-aaa", "200"), (None, "100")]:
        conn.execute(
            "INSERT INTO trades VALUES (?, 'A', 'BTCUSDT', 1, 100.0, 1000.0, 1.0, 95.0, "
            "110.0, 1700000000000, 1700604800000, 1700000000000, 'closed', ?, NULL, "
            "NULL, 105.0, 1700100000000, 'take_profit', ?)",
            (uuid.uuid4().hex, entry_id, created),
        )
    conn.commit()
    conn.close()

    plan = plan_dedupe(db_path)
    assert len(plan) == 1  # one duplicate group
    group = plan[0]
    assert group["kept"]["entry_order_id"] is None  # seeded closed wins (priority 1)
    assert len(group["removed"]) == 1
    assert group["removed"][0]["entry_order_id"] == "CATCHUP-aaa"

    # DB unchanged (dry-run by default)
    conn = sqlite3.connect(str(db_path))
    n = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    conn.close()
    assert n == 2


def test_plan_dedupe_apply(tmp_path):
    """With apply=True, the lower-priority rows are deleted in a transaction."""
    db_path = tmp_path / "legacy.db"
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
    for entry_id, created in [("CATCHUP-aaa", "200"), (None, "100")]:
        conn.execute(
            "INSERT INTO trades VALUES (?, 'A', 'BTCUSDT', 1, 100.0, 1000.0, 1.0, 95.0, "
            "110.0, 1700000000000, 1700604800000, 1700000000000, 'closed', ?, NULL, "
            "NULL, 105.0, 1700100000000, 'take_profit', ?)",
            (uuid.uuid4().hex, entry_id, created),
        )
    conn.commit()
    conn.close()

    plan_dedupe(db_path, apply=True)

    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        "SELECT entry_order_id FROM trades"
    ).fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0][0] is None  # seeded-closed (NULL) survived
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/scripts/test_dedupe_trades.py -v`
Expected: FAIL — `scripts/dedupe_trades` module doesn't exist yet.

- [ ] **Step 3: Implement the script**

Create `scripts/dedupe_trades.py`:

```python
"""Interactive trade-table dedupe for legacy DBs that pre-date the
(model_name, symbol, open_time) UNIQUE INDEX.

Usage:
    uv run python scripts/dedupe_trades.py --db data/dry_run.db
    uv run python scripts/dedupe_trades.py --db data/live.db --apply

Without --apply (default) the script only PRINTS what it would remove.
With --apply it executes the deletes in a single transaction.

Priority (highest first — keeper):
    0  numeric entry_order_id   real Binance fill — never delete
    1  entry_order_id IS NULL   seeded 'closed' row from CSV — canonical
    2  SEEDED-*                 open seeded carry-over
    3  CATCHUP-* / DRY-*        engine-replayed paper rows — deletable

Within a tier, oldest created_at wins (first arrival).
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Iterable


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
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def plan_dedupe(db_path: Path, apply: bool = False) -> list[dict]:
    """Compute (and optionally apply) the dedupe plan.

    Returns a list of {group: (model, sym, ot), kept: row, removed: [row, ...]}
    """
    conn = sqlite3.connect(str(db_path))
    plan: list[dict] = []
    try:
        for model_name, symbol, open_time in _fetch_duplicate_groups(conn):
            rows = _fetch_group_rows(conn, model_name, symbol, open_time)
            keeper = pick_keeper(rows)
            removed = [r for r in rows if r["id"] != keeper["id"]]
            plan.append({
                "group": (model_name, symbol, open_time),
                "kept": keeper,
                "removed": removed,
            })
        if apply and plan:
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
        f"weighted_pnl={r.get('exit_price')}"
    )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db", type=str, required=True,
        help="DB path. Must be typed explicitly (no glob).",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Apply the plan (delete rows). Default: dry-run only.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"ERROR: {db_path} does not exist", file=sys.stderr)
        return 2

    plan = plan_dedupe(db_path, apply=args.apply)
    if not plan:
        print(f"[dedupe] {db_path}: no duplicates found")
        return 0

    print(f"[dedupe] {db_path}: {len(plan)} duplicate group(s)")
    for entry in plan:
        m, s, ot = entry["group"]
        print(f"\n  ({m}, {s}, {ot}):")
        print(f"    KEEP    {_format_row_summary(entry['kept'])}")
        for r in entry["removed"]:
            print(f"    REMOVE  {_format_row_summary(r)}")

    if args.apply:
        print(f"\n[dedupe] APPLIED — {sum(len(e['removed']) for e in plan)} rows deleted")
    else:
        print("\n[dedupe] DRY-RUN — no changes made. Re-run with --apply to execute.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/scripts/test_dedupe_trades.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/dedupe_trades.py tests/scripts/__init__.py tests/scripts/test_dedupe_trades.py
git commit -m "feat(scripts): dedupe_trades.py for legacy DBs with duplicate keys

Interactive (dry-run by default) cleanup tool for DBs that pre-date
the trades(model_name, symbol, open_time) UNIQUE INDEX. Picks a
keeper per duplicate group using priority order:
  0 numeric entry_order_id (real Binance fill — never deleted)
  1 NULL entry_order_id (seeded 'closed' row — canonical CSV row)
  2 SEEDED-* (open seeded carry-over)
  3 CATCHUP-* / DRY-* (engine-replayed paper — deletable)
Ties broken by oldest created_at."
```

---

## Task 8: Update CLAUDE.md to reflect the new flow

**Goal:** Drop `--as-of` and `--catch-up-from` from the testnet recipe in CLAUDE.md. Replace with one paragraph explaining the boundary handshake. Add the expected `[live] ... boundary: N seeded keys, M cooldown keys` log line to the startup expectations.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Read the current state**

Run: `head -160 CLAUDE.md`
Expected: see the existing "seed-live-db" and "Testnet workflow" sections. Identify the lines containing `--as-of` and `--catch-up-from`.

- [ ] **Step 2: Edit CLAUDE.md — drop date flags from the recipe**

In the `### \`seed-live-db\` — Import backtest trades to recover R1/R2/VT/cooldown state` section, locate the seeder command block:

```
uv run crypto-trade seed-live-db \
  --db data/<target>.db \
  --track both \
  --v1-trades reports/iteration_186/in_sample/trades.csv \
  --v1-trades reports/iteration_186/out_of_sample/trades.csv \
  --v2-trades reports-v2/iteration_v2-069/in_sample/trades.csv \
  --v2-trades reports-v2/iteration_v2-069/out_of_sample/trades.csv \
  [--as-of YYYY-MM-DD]
```

Remove the trailing `[--as-of YYYY-MM-DD]` line. Append `[--reseed]` instead:

```
uv run crypto-trade seed-live-db \
  --db data/<target>.db \
  --track both \
  --v1-trades reports/iteration_186/in_sample/trades.csv \
  --v1-trades reports/iteration_186/out_of_sample/trades.csv \
  --v2-trades reports-v2/iteration_v2-069/in_sample/trades.csv \
  --v2-trades reports-v2/iteration_v2-069/out_of_sample/trades.csv \
  [--reseed]
```

Below it, replace the "Behavior" bullets to reflect the new logic:

```
Behavior:
- Inserts each CSV row as a `trades` table row. Trades whose `exit_reason` is
  `end_of_data` become `status='open'` with `entry_order_id='SEEDED'` and
  full intended-exit info; everything else is `status='closed'`.
- Writes `seeded_through_<model>_<sym>` engine_state keys equal to
  `MAX(close_time)` per pair. Catch-up reads these to skip trade-creation
  in seeded territory — no `--as-of` or `--catch-up-from` needed.
- Re-runs are idempotent: `(model_name, symbol, open_time)` UNIQUE INDEX
  blocks duplicate inserts. Boundary keys advance monotonically by default;
  `--reseed` overrides with the new CSV's extent (even if lower).
- Drops zero-`weight_factor` rows (BTC-killed v2 trades).
- Sets per-`(model, symbol)` `cooldown_<model>_<symbol>` engine_state keys
  for the standard 2-candle post-trade cooldown.
```

Replace the "Pair the seeder's `--as-of` with the engine's `--catch-up-from`..." paragraph with:

```
After seeding, just launch `live`. The catch-up loop reads the boundary
keys per `(model, symbol)` and replays only the gap between the seeded
extent and now. Zero date-flag alignment to think about.
```

- [ ] **Step 3: Edit the testnet recipe — drop `--catch-up-from`**

In the `### Testnet workflow — end-to-end` section, locate Step 5:

```
**Step 5 — launch on testnet.** Default 90-day catch-up is fine when the seeder covered everything; otherwise pass `--catch-up-from <day-after-last-seeded-close>` to bound the replay precisely.

```
uv run crypto-trade live --testnet --track both --amount 100 --leverage 1
```
```

Replace with:

```
**Step 5 — launch on testnet.** No date flags — the boundary handshake (seeder writes `seeded_through_<model>_<sym>` engine_state keys; catch-up reads them) automatically resumes from the seeded extent.

```
uv run crypto-trade live --testnet --track both --amount 100 --leverage 1
```
```

In the "What you should see at startup" list, add a new bullet after the rebuilt-state lines:

```
- `[live] Model <name> catch-up boundary: <N> seeded keys, <M> cooldown keys`
  (one line per model with seeded data — confirms the handshake fired).
```

- [ ] **Step 4: Sanity-check the file**

Run: `grep -nE "as-of|catch-up-from|catch-up-days" CLAUDE.md`
Expected: zero matches except inside a code-quote block describing the *removed* flags or in a "what's NOT changing" historical note.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude): drop --as-of and --catch-up-from from testnet recipe

The boundary handshake (seeded_through_<model>_<sym> engine_state keys)
makes manual date alignment unnecessary. Recipe is reduced to:
  fetch → features → (optional) backtest → seed → live.

Adds the expected '[live] ... boundary: N seeded keys, M cooldown keys'
startup log line so operators can confirm the handshake fired."
```

---

## Self-review

**Spec coverage check** (cross-reference each spec section to a task):

- "Boundary handshake" (spec §1) → Task 3 (write keys) + Task 4 (read keys). ✓
- "Natural-key uniqueness" (spec §2) → Task 2. ✓
- "Catch-up cooldown pre-load" (spec §3) → Task 4. ✓
- "CLI surface changes" (spec §4) → Task 5 (`--as-of` removal + `--reseed`) and Task 6 (`--catch-up-from`/`--catch-up-days` removal). ✓
- "Migration" (spec §5) → Task 2 (`StateStoreMigrationError` + index attempt) + Task 7 (`dedupe_trades.py`). ✓
- "Test plan" (spec) → covered across Tasks 1-7; specifically:
  - test_seed_writes_boundary_keys → Task 3 ✓
  - test_seed_advances_boundary_monotonically → Task 3 ✓
  - test_reseed_overwrites_boundary → Task 5 ✓
  - test_seed_idempotent_on_repeat → Task 3 ✓
  - test_catch_up_skips_seeded_territory → Task 4 ✓
  - test_catch_up_resumes_at_boundary → covered by test_catch_up_skips_seeded_territory (asserts only post-boundary trade exists) ✓
  - test_catch_up_preloads_cooldown_keys → Task 4 ✓
  - test_unique_index_blocks_duplicate_insert → Task 2 ✓
  - test_db_open_aborts_on_existing_duplicates → Task 2 ✓
  - test_catch_up_handles_unique_collision_gracefully → Task 2 ✓
  - test_catch_up_never_calls_signed_endpoints → Task 1 ✓
  - test_catch_up_source_anchor_no_auth_calls → Task 1 ✓
- "Acceptance criteria" → covered by tests + manual verification post-merge.

**Placeholder scan:** none — every code block is concrete, every test has a body, every grep target is specific.

**Type / API consistency:**
- `seed_live_db_from_backtest` signature transitions: Task 3 leaves `as_of_ms` in place; Task 5 removes it and adds `reseed`. The Task 5 test `test_seed_signature_no_as_of_kwarg` explicitly verifies the final shape.
- `StateStoreMigrationError` introduced in Task 2, imported in tests and used in Task 7's planning (script does NOT use the error — it's standalone).
- `_count_natural_key_duplicates` defined in Task 2; used only in `StateStore.__init__` error message construction.
- `seeded_through_<model>_<sym>` key format consistent across Task 3 (writer) and Task 4 (reader).

---

Plan complete and saved to `docs/superpowers/plans/2026-04-30-seed-catchup-handshake.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
