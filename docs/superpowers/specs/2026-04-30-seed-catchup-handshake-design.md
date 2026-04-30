# Seed/catch-up handshake — design spec

**Date:** 2026-04-30
**Status:** Approved
**Owner:** Roberto

## Problem

The current `seed-live-db` + `live` flow requires the user to manually align two date flags (`--as-of` and `--catch-up-from`) to avoid duplicate trades. Misalignment is silent and produces duplicates in the trades table:

- `seed-live-db` ingests backtest CSVs and writes `closed`/`open` rows for trades up to `--as-of`. With no `--as-of`, it ingests every trade in the CSV up to data extent.
- `live` runs catch-up over `[now − catch_up_lookback_days, now]` (default 90 days) and creates `CATCHUP-*` rows for every signal that fires.
- If the catch-up window overlaps the seeded period (the common case with default flags), every signal in the overlap creates a duplicate row in the `trades` table — same `(model_name, symbol, open_time)` but a fresh UUID `id`. The schema has no natural-key uniqueness, so duplicates persist silently.
- R1/R2/VT recovery is unaffected (rebuilt only from `status='closed'` rows seeded *before* catch-up). Trade-log aggregations and downstream PnL accounting are wrong.

Real money is at stake. The system must be safe under default flag values.

## Goals

1. Eliminate the duplicate failure mode entirely without requiring the user to align two dates.
2. Reduce the user-facing CLI surface — the seeder and the engine should agree on a boundary automatically.
3. Add defense-in-depth so even a misconfigured or partially-rerun seed cannot produce duplicates.
4. Preserve the existing safety property: catch-up never places real Binance orders, regardless of mode.

## Non-goals

- Restructuring the seeder/engine architecture beyond what these goals require.
- Changing R1/R2/R3/VT recovery logic.
- Changing LightGbmStrategy lazy training, reconciler, or order manager beyond migration.
- Allowing real-money DB auto-dedupe — destructive cleanup is always opt-in.

## Design

Two coupled mechanisms — a **boundary handshake** as the primary correctness layer, and a **natural-key uniqueness constraint** as the safety net.

### 1. Boundary handshake (primary)

A new engine_state key family records, per `(model_name, symbol)`, the latest `close_time` of any seeded trade for that pair:

```
seeded_through_<model_name>_<symbol> = <close_time_ms>
```

**Seeder writes the keys.** After ingesting all CSV rows, for each `(model_name, symbol)` pair the seeder computes `MAX(close_time)` across the trades it inserted (status `closed` or `open` — both count) and writes the corresponding `seeded_through_*` key. If a key already exists for that pair, the seeder takes `MAX(existing, new)` so re-running with newer CSVs only ever advances the boundary.

**Catch-up reads the keys.** At the start of `_catch_up_model`, the engine pre-loads a `seeded_through: dict[str, int]` map (one entry per symbol the model trades). Inside the per-candle loop, before opening a `CATCHUP-*` trade, the engine checks `ot > seeded_through.get(sym, 0)`. If the candle is in seeded territory, trade-creation is skipped. Open-trade exit handling — closing `SEEDED` rows at their seeded `exit_time` — still runs unconditionally because the seeded data carries that information for the engine to apply.

**Why `close_time` and not `open_time`:** A trade entering at candle X and exiting at candle Y > X means the position is active across `[X, Y]`. Using `MAX(close_time)` as the boundary means catch-up resumes from the candle *after* the last seeded position settles, with no risk of opening a fresh trade for the same symbol while a seeded trade is still notionally open.

**Empty / no-seed case:** No `seeded_through_*` keys exist → `seeded_through.get(sym, 0)` returns 0 → every candle is treated as non-seeded → behavior identical to today's no-seed start. 90-day catch-up replays everything as before.

### 2. Natural-key uniqueness (defense-in-depth)

Add a unique index on `trades(model_name, symbol, open_time)`:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS ux_trades_natkey
ON trades(model_name, symbol, open_time);
```

**Effect on catch-up:** When `_catch_up_model` calls `self._state.upsert_trade(trade)` for a fresh `CATCHUP-*` row that collides on the natural key (e.g., because boundary protection failed for any reason), SQLite raises `IntegrityError`. Catch-up wraps this insertion in `try/except IntegrityError`, logs a warning ("[catchup] duplicate suppressed: model=... sym=... open_time=..."), and continues. The local `open_trades[sym]` is **not** updated, so subsequent iterations won't fall into "I have an open trade" logic for a row the DB rejected.

**Effect on seeder:** Re-running the seeder with the same CSV is a no-op for each row that already exists. Re-running with overlapping CSVs (e.g., a refreshed `out_of_sample/trades.csv` overlapping the prior version) inserts only new rows. No `INSERT OR REPLACE`, no destructive overwrites of past data.

**Effect on `OrderManager.open_trade`:** Same protection — if a live tick attempts to open a trade for a `(model, sym, open_time)` already in the DB (e.g., from a stale seeded row that wasn't reconciled), `IntegrityError` aborts the insert. The order manager re-raises as a hard error because the live tick is the one place where a natural-key collision indicates a real bug, not a benign retry. Ops should investigate before retrying.

### 3. Catch-up cooldown pre-load

Catch-up's local `cooldown_until: dict[str, int]` currently starts empty (`engine.py:773`) and is populated only as catch-up itself closes trades. The seeder writes `cooldown_<model>_<sym>` engine_state keys representing the standard 2-candle post-trade cooldown for the latest seeded close, but catch-up doesn't read them today.

**Fix:** At the start of `_catch_up_model`, pre-load `cooldown_until` from the seeded keys:

```python
for sym in runner.model_config.symbols:
    raw = self._state.get_state(f"cooldown_{runner.model_config.name}_{sym}")
    if raw:
        cooldown_until[sym] = int(raw)
```

This closes the gap where a seeded trade closing close to the boundary leaves a cooldown extending into post-boundary territory — without the pre-load, catch-up could open a fresh trade inside that cooldown window.

### 4. CLI surface changes

**Removed flags:**

- `seed-live-db --as-of YYYY-MM-DD` — gone. Seeder always ingests every CSV row up to data extent. Boundary key recorded automatically per `(model, symbol)`.
- `live --catch-up-from YYYY-MM-DD` — gone.
- `live --catch-up-days N` — gone.

**Added flag:**

- `seed-live-db --reseed` — when present, the seeder removes all existing `seeded_through_*` engine_state keys for the affected `(model, symbol)` pairs before inserting. Without `--reseed`, the seeder takes `MAX(existing, new)` for each pair (advances boundary monotonically). `--reseed` is for the "I changed my mind about the seed CSVs and want to start over" case; it does NOT delete trade rows (the unique index makes that a separate, deliberate operation via `scripts/dedupe_trades.py`).

**Internal config field stays:**

- `LiveConfig.catch_up_lookback_days: int | None = 90` — still tunable for tests and parity scripts (which set it directly via `LiveConfig(catch_up_lookback_days=400)` for full-OOS replay). Not exposed via CLI.

### 5. Migration

On `StateStore.__init__` (after `CREATE TABLE IF NOT EXISTS trades(...)`), attempt to create the unique index:

```python
try:
    self._conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_trades_natkey "
        "ON trades(model_name, symbol, open_time)"
    )
except sqlite3.IntegrityError as exc:
    # Existing rows violate uniqueness — surface a clear error and abort.
    dups = self._count_natural_key_duplicates()
    raise StateStoreMigrationError(
        f"DB at {db_path} has {dups} duplicate (model_name, symbol, open_time) "
        f"groups from prior runs. The new schema requires uniqueness.\n\n"
        f"For dry_run/testnet DBs (no real money): rm {db_path} and re-seed.\n"
        f"For real-money live.db: run "
        f"`uv run python scripts/dedupe_trades.py --db {db_path}` (interactive — "
        f"prints what would be removed for review before applying).\n"
    ) from exc
```

A new helper `_count_natural_key_duplicates()` returns the number of natural-key groups with `COUNT(*) > 1`.

A new script `scripts/dedupe_trades.py`:
- Accepts `--db <path>` and `--apply` (default: dry-run, prints plan only).
- For each `(model_name, symbol, open_time)` group with multiple rows, picks one to keep by this priority:
  1. Numeric `entry_order_id` (real Binance trade) — never delete a real-money fill.
  2. `entry_order_id IS NULL` (seeded `closed` row from CSV — canonical source).
  3. `SEEDED-*` (open seeded carry-over).
  4. `CATCHUP-*` / `DRY-*` (engine-replayed paper rows — lowest priority, deletable).
  Within the same priority tier, oldest `created_at` wins (first arrival).
- Prints the candidate group + proposed kept row + proposed deletions, including direction, entry/exit prices, exit_reason, weighted_pnl, so the user can sanity-check.
- With `--apply`, executes the deletes inside a transaction. Without `--apply`, only prints.
- Refuses to run on `data/live.db` without `--db data/live.db` explicitly typed (no glob matching).

For new DBs (the common case after this change), the index creates silently on first open; no migration step is visible to the user.

## Architecture changes (file-level)

### `src/crypto_trade/live/state_store.py`
- Add unique index DDL alongside trades-table DDL.
- Add `_count_natural_key_duplicates() -> int` helper.
- Add `StateStoreMigrationError` exception class (re-exported from `live/models.py` for engine code).
- Existing `upsert_trade` keeps its `INSERT … ON CONFLICT(id) DO UPDATE` semantics (id-based update for the SEEDED→closed transition).

### `src/crypto_trade/live/db_seeder.py`
- Track `latest_close: dict[(model_name, symbol), int]` during ingest (already exists for cooldown keys).
- After ingest, for each pair, write `seeded_through_<model>_<sym> = <latest_close_ms>`. If a key already exists, take `MAX(old, new)` unless `reseed=True`, in which case overwrite.
- Add `reseed: bool` parameter to `seed_live_db_from_backtest`.
- Use `INSERT OR IGNORE` for trade rows (idempotent re-seed). Returned counts gain `skipped_duplicate` so the user sees what was already there.
- `as_of_ms` parameter removed from public signature.

### `src/crypto_trade/main.py`
- Drop the `--as-of` argparse arg from `seed-live-db`. Drop the `--catch-up-from` and `--catch-up-days` mutually-exclusive group from `live`.
- Add `--reseed` flag to `seed-live-db`.
- `_cmd_seed_live_db` no longer parses `as_of`.
- `_cmd_live` no longer constructs `catch_up_kwargs` from CLI args; it passes `LiveConfig(...)` with the default `catch_up_lookback_days=90` (unless tests override).

### `src/crypto_trade/live/engine.py`
- `_catch_up_model`: at the top, pre-load both `seeded_through: dict[str, int]` and `cooldown_until: dict[str, int]` from engine_state.
- Inside the trade-creation block, add the boundary check:
  ```python
  if (
      sym not in open_trades
      and ot >= cooldown_until.get(sym, 0)
      and ot >= self._risk_cooldown_until.get(sym, 0)
      and ot > seeded_through.get(sym, 0)         # NEW
  ):
      ...
  ```
- Wrap the `self._state.upsert_trade(trade)` line for fresh CATCHUP-* inserts in `try/except sqlite3.IntegrityError`. On collision: log warning, do not update local `open_trades[sym]`, do not increment `n_trades_opened`.

### `tests/`
- Delete `test_cli_live_catch_up_from_flag` and the mutually-exclusive test.
- Rewrite `test_seed_as_of_splits_open_vs_closed` → `test_seed_splits_open_vs_closed_at_data_extent`. Without `--as-of`, the boundary is the CSV's last close_time; trades whose `close_time == data_extent_max` and whose status semantics imply still-open become `SEEDED open`.
- Add new tests (see Test Plan below).

### `scripts/`
- Add `dedupe_trades.py` (interactive cleanup for legacy DBs).

### Documentation
- Update `CLAUDE.md` Step 4 + Step 5 wording — drop `--as-of` and `--catch-up-from` from examples; explain the boundary handshake in one paragraph; remove the "must align dates" warning entirely.
- Update the "Step 5 — launch on testnet" log expectations: add a line `[live] Catch-up: <N> seeded boundary keys loaded`.

## Test plan

### New tests

1. **`test_seed_writes_boundary_keys`** (db_seeder)
   Seed two CSVs (v1 + v2). Assert each `(model, sym)` has a `seeded_through_*` engine_state key equal to `MAX(close_time)` across the seeded rows for that pair.

2. **`test_seed_advances_boundary_monotonically`** (db_seeder)
   Seed CSV A (data extent T1). Re-seed CSV B (extends to T2 > T1). Assert keys updated to T2 for every pair where B extended; unchanged for pairs B did not touch.

3. **`test_reseed_overwrites_boundary`** (db_seeder)
   Seed CSV A. Re-seed CSV C (extent T3 < T1) with `reseed=True`. Assert keys reflect T3 (or are deleted for pairs not in C).

4. **`test_seed_idempotent_on_repeat`** (db_seeder)
   Seed CSV A twice. Assert trade row count unchanged after second run (`INSERT OR IGNORE` swallows duplicates), `skipped_duplicate` count > 0 in the result.

5. **`test_catch_up_skips_seeded_territory`** (engine)
   Seed a DB through 2026-04-29. Run `engine.catch_up_only()` with default 90-day window. Assert no `CATCHUP-*` trades exist in DB with `open_time <= 2026-04-29`.

6. **`test_catch_up_resumes_at_boundary`** (engine)
   Seed through 2026-04-29 (one trade per symbol). Mock master DF to extend to 2026-05-05. Run catch-up. Assert any new `CATCHUP-*` rows have `open_time > 2026-04-29`.

7. **`test_catch_up_preloads_cooldown_keys`** (engine)
   Seed a DB so that `cooldown_<model>_<sym>` extends past the boundary. Mock master to provide a candle in the cooldown window. Assert no trade is opened for that candle.

8. **`test_unique_index_blocks_duplicate_insert`** (state_store)
   Insert a trade. Attempt to insert another with same `(model_name, symbol, open_time)` but different `id`. Assert `IntegrityError`.

9. **`test_db_open_aborts_on_existing_duplicates`** (state_store)
   Pre-create a DB without the index, insert two duplicate rows, close. Reopen. Assert `StateStoreMigrationError` with a message that names the count and the cleanup script.

10. **`test_catch_up_handles_unique_collision_gracefully`** (engine)
    Manually pre-insert a `(model, sym, open_time)` row. Drive catch-up over a period where a signal would fire on that exact candle. Assert: catch-up does NOT raise, logs a warning, the local `open_trades[sym]` was NOT updated, `n_trades_opened` did NOT increment.

11. **`test_catch_up_never_calls_signed_endpoints`** (engine — safety regression)
    Configure `LiveConfig(dry_run=False)` with `auth_base_url` pointing at testnet. Inject a mock `_auth_client`. Run `engine.catch_up_only()`. Assert `place_market_order`, `place_stop_market_order`, `place_take_profit_market_order` were never called. (Set leverage may be called from `_initial_setup`; that's OK and expected.)

12. **`test_catch_up_source_anchor_no_auth_calls`** (regex drift guard, mirrors the `dba16ec` test)
    Read `engine.py`, locate the body of `_catch_up_model` via regex, assert the body contains no `self._auth` reference. Drift guard against future refactors that accidentally route order placement through catch-up.

### Removed tests

- `test_cli_live_catch_up_from_flag` (`tests/live/test_engine_v2.py:482`)
- The associated mutually-exclusive group test (line ~497)
- `test_seed_as_of_splits_open_vs_closed` rewritten as above

### Updated tests

- Parity tests (`test_backtest_parity_combined.py`, `test_backtest_parity_v2.py`): they pass `LiveConfig(catch_up_lookback_days=400)` directly, so they keep working. No change needed.

## Acceptance criteria

1. `uv run pytest tests/live/` passes.
2. Running `seed-live-db` with no `--as-of` and `live` with no `--catch-up-from` produces zero duplicates as detected by `SELECT model_name, symbol, open_time, COUNT(*) FROM trades GROUP BY 1,2,3 HAVING COUNT(*) > 1` (returns 0 rows).
3. `scripts/reconcile_full_oos.py` produces zero divergences after a seed → live → catchup → DB-compare cycle (modulo the known data-extent artifact for `end_of_data`/`timeout` differences).
4. `engine.catch_up_only()` invoked with `dry_run=False` and a mock `_auth_client` triggers zero `place_*_order` calls.
5. Existing DBs with no duplicates auto-migrate (index created silently). Existing DBs with duplicates raise `StateStoreMigrationError` with cleanup instructions.
6. `CLAUDE.md` testnet recipe is reduced to: keys → fetch → features → (optional) backtest → seed → live, with no date flags anywhere.

## Open implementation decisions

- **Logging verbosity for boundary loads.** Print `[live] Boundary loaded: <N> seeded_through keys, <M> cooldown keys` once at start of catch-up so operators can confirm the seed handshake fired. Yes.
- **Should `--reseed` also delete existing trade rows?** No. Trade-row cleanup goes through `dedupe_trades.py` exclusively. `--reseed` only resets boundary keys.
- **Should the migration auto-dedupe for non-`live.db` paths?** No. Even for dry_run/testnet, silently deleting historical state is bad form. Always require user opt-in via the dedupe script.

## Risk assessment

- **Low**: removing CLI flags is backwards-incompatible. Mitigation: documented in the commit, CLAUDE.md updated, parity tests don't depend on these flags.
- **Low**: unique index migration error on existing DBs. Mitigation: the dedupe script + clear error message direct users to the safe path.
- **Negligible**: catch-up performance — the boundary check is a dict lookup inside an already-tight loop. Pre-loading cooldown_until is one extra `get_state` call per symbol at start.
- **Negligible**: changes touch only files already covered by tests, with new tests added for the new mechanisms.
