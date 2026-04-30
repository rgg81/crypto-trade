"""Seed `data/live.db` from backtest trade CSVs (Option B).

Imports v1 and/or v2 backtest trades into the live DB so that
`LiveEngine._rebuild_*` methods can reconstruct R1/R2/VT/cooldown state
without needing a multi-month catch-up replay. After seeding, the engine
can be launched with a short `--catch-up-days` (covering only the gap
since the last seeded trade) and still produce trades bit-identical to
the backtest.

Open vs closed split is driven by the CSV's `exit_reason` field:
rows whose `exit_reason == 'end_of_data'` were still open at the
backtest's data extent — they're inserted as `status='open'` with
`entry_order_id='SEEDED'` and full intended-exit info populated. Any
other `exit_reason` means the trade really closed in the backtest, so
it goes in as `status='closed'`.

For each (model, symbol), the seeder also writes the
`cooldown_<model>_<symbol>` engine_state key so the cooldown gate kicks
in correctly when catch-up starts, plus a
`seeded_through_<model>_<symbol>` boundary key so the engine knows
where seeded coverage ends.

Zero-`weight_factor` rows (BTC-killed v2 trades from the post-hoc filter)
are dropped — live's signal-time BTC filter (Task 7) kills these BEFORE
order entry, so they never appear in the live DB and would corrupt state
if seeded.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import pandas as pd

from crypto_trade.live.models import LiveConfig, LiveTrade, ModelConfig
from crypto_trade.live.state_store import StateStore


_CANDLE_8H_MS = 28_800_000


def _build_symbol_to_model(
    models: Iterable[ModelConfig],
) -> dict[str, str]:
    """Map symbol → owning ModelConfig.name."""
    out: dict[str, str] = {}
    for mc in models:
        for sym in mc.symbols:
            out[sym] = mc.name
    return out


def _resolve_cooldown_candles(
    models: Iterable[ModelConfig], live_config: LiveConfig
) -> dict[str, int]:
    """Map ModelConfig.name → resolved cooldown_candles (per-model override or LiveConfig)."""
    out: dict[str, int] = {}
    for mc in models:
        out[mc.name] = (
            mc.cooldown_candles if mc.cooldown_candles is not None else live_config.cooldown_candles
        )
    return out


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

    Returns:
        counts dict with keys "v1_closed", "v1_open", "v2_closed", "v2_open",
        "skipped_zero_weight", "skipped_unknown_symbol", "skipped_duplicate",
        "cooldown_keys", "boundary_keys".
    """
    sym_to_model = _build_symbol_to_model(live_config.models)
    cooldown_candles_for = _resolve_cooldown_candles(live_config.models, live_config)

    store = StateStore(db_path)
    counts = {
        "v1_closed": 0,
        "v1_open": 0,
        "v2_closed": 0,
        "v2_open": 0,
        "skipped_zero_weight": 0,
        "skipped_unknown_symbol": 0,
        "skipped_duplicate": 0,
        "cooldown_keys": 0,
        "boundary_keys": 0,
    }

    # latest close_time per (model, symbol) for cooldown seeding
    latest_close: dict[tuple[str, str], int] = defaultdict(int)
    # Tracks MAX close_time across ALL seeded rows for the pair (closed AND open),
    # used to write the seeded_through_<model>_<sym> boundary key.
    latest_close_any: dict[tuple[str, str], int] = defaultdict(int)

    def _ingest(csvs: list[Path], track: str) -> None:
        for csv_path in csvs:
            if not csv_path.exists():
                continue
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                sym = str(row["symbol"])
                if sym not in sym_to_model:
                    counts["skipped_unknown_symbol"] += 1
                    continue
                if float(row["weight_factor"]) <= 0.0:
                    counts["skipped_zero_weight"] += 1
                    continue
                model_name = sym_to_model[sym]
                trade = _row_to_trade(
                    row,
                    model_name=model_name,
                    timeout_minutes=live_config.timeout_minutes,
                    max_amount_usd=live_config.max_amount_usd,
                )
                if trade is None:
                    continue
                try:
                    store.upsert_trade(trade)
                except sqlite3.IntegrityError:
                    # Same (model, sym, open_time) already in DB. Idempotent
                    # re-seed: skip and keep the existing row.
                    counts["skipped_duplicate"] = counts.get("skipped_duplicate", 0) + 1
                    continue
                key = f"{track}_{trade.status}"
                counts[key] = counts.get(key, 0) + 1
                # Cooldown is keyed off the LAST close that finished before
                # the catch-up boundary. Open-at-cutoff trades close LATER, so
                # they don't drive the initial cooldown timestamp; only fully-
                # closed (status='closed') trades do.
                if trade.status == "closed" and trade.exit_time is not None:
                    k = (model_name, sym)
                    if trade.exit_time > latest_close[k]:
                        latest_close[k] = trade.exit_time
                # Boundary key tracks ALL seeded rows for the pair, regardless
                # of status. The key tells the engine where seeded coverage
                # ends so catch-up doesn't replay it.
                k_any = (model_name, sym)
                if trade.exit_time is not None and trade.exit_time > latest_close_any[k_any]:
                    latest_close_any[k_any] = trade.exit_time

    _ingest(v1_trades_csvs, "v1")
    _ingest(v2_trades_csvs, "v2")

    # Seed cooldown_<model>_<symbol> engine_state keys
    for (model_name, sym), close_time in latest_close.items():
        cd = cooldown_candles_for.get(model_name, live_config.cooldown_candles)
        if cd <= 0:
            continue
        cooldown_until = close_time + cd * _CANDLE_8H_MS
        store.set_state(f"cooldown_{model_name}_{sym}", str(cooldown_until))
        counts["cooldown_keys"] += 1

    # Seed seeded_through_<model>_<symbol> engine_state keys (boundary handshake).
    # Engine catch-up reads these to skip trade-creation in seeded territory.
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

    # Close the seeder's StateStore connection so subsequent readers
    # (LiveEngine in particular) see the seeded rows on a fresh connection.
    # Without this explicit close, SQLite WAL behavior leaves the engine
    # reading an inconsistent snapshot.
    store.close()

    return counts
