"""Seed `data/live.db` from backtest trade CSVs (Option B).

Imports v1 and/or v2 backtest trades into the live DB so that
`LiveEngine._rebuild_*` methods can reconstruct R1/R2/VT/cooldown state
without needing a multi-month catch-up replay. After seeding, the engine
can be launched with a short `--catch-up-days` (covering only the gap
since the last seeded trade) and still produce trades bit-identical to
the backtest.

Trades are inserted as `status='closed'` rows when their close_time is
before the `as_of` cutoff, and as `status='open'` rows when they were
still open at the cutoff. Trades that opened *after* the cutoff are
skipped — the live engine's catch-up will produce them.

For each (model, symbol), the seeder also writes the
`cooldown_<model>_<symbol>` engine_state key so the cooldown gate kicks
in correctly when catch-up starts.

Zero-`weight_factor` rows (BTC-killed v2 trades from the post-hoc filter)
are dropped — live's signal-time BTC filter (Task 7) kills these BEFORE
order entry, so they never appear in the live DB and would corrupt state
if seeded.
"""
from __future__ import annotations

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
            mc.cooldown_candles
            if mc.cooldown_candles is not None
            else live_config.cooldown_candles
        )
    return out


def _row_to_trade(
    row: pd.Series,
    model_name: str,
    as_of_ms: int | None,
    timeout_minutes: int,
    max_amount_usd: float,
) -> LiveTrade | None:
    """Convert a backtest CSV row to a LiveTrade. Returns None if the row should be skipped."""
    weight_factor = float(row["weight_factor"])
    if weight_factor <= 0.0:
        return None  # BTC-killed v2 row — never in live DB

    open_time = int(row["open_time"])
    close_time = int(row["close_time"])

    if as_of_ms is not None and open_time >= as_of_ms:
        return None  # opens after cutoff — let the engine replay it

    # If close_time is also before as_of, this trade is fully closed by then —
    # status='closed' with full exit info. cum_weighted_pnl / VT include it.
    #
    # If close_time is at or after as_of, this trade is "open at the catch-up
    # boundary" — status='open' but with intended-exit fields populated so the
    # engine's catch-up can close it deterministically at the seeded exit_time.
    spans_cutoff = as_of_ms is not None and close_time >= as_of_ms

    direction = int(row["direction"])
    entry_price = float(row["entry_price"])
    exit_price = float(row["exit_price"])

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
        status="open" if spans_cutoff else "closed",
        # Sentinel order IDs distinguish seeded open trades from genuine
        # live-opened ones in `_reconcile` and `_catch_up_model`.
        entry_order_id="SEEDED" if spans_cutoff else None,
        sl_order_id=None,
        tp_order_id=None,
        # Even for status='open' rows we populate exit_* with the backtest's
        # actual close. The engine's catch-up loop reads these to close the
        # trade exactly at exit_time — no SL/TP/timeout recomputation. For
        # closed rows these are the real exit (same fields, same meaning).
        exit_price=exit_price,
        exit_time=close_time,
        exit_reason=str(row["exit_reason"]),
    )


def seed_live_db_from_backtest(
    db_path: Path,
    v1_trades_csvs: list[Path],
    v2_trades_csvs: list[Path],
    live_config: LiveConfig,
    as_of_ms: int | None = None,
) -> dict[str, int]:
    """Seed `db_path` with backtest trades and cooldown keys.

    Args:
        db_path: target SQLite DB. Existing rows are NOT cleared — caller
            should `rm` the file first if a fresh seed is wanted.
        v1_trades_csvs: list of paths (e.g. IS + OOS CSVs).
        v2_trades_csvs: list of paths.
        live_config: drives the symbol → model mapping and cooldown_candles
            resolution. Pass `LiveConfig(models=COMBINED_MODELS)` for v1+v2.
        as_of_ms: cutoff. None ⇒ seed every trade. Otherwise, trades that
            opened after `as_of_ms` are skipped (engine will replay them);
            trades that were still open at `as_of_ms` are inserted as
            `status='open'`.

    Returns:
        counts dict with keys "v1_closed", "v1_open", "v2_closed", "v2_open",
        "skipped_zero_weight", "skipped_unknown_symbol", "skipped_after_cutoff",
        "cooldown_keys".
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
        "skipped_after_cutoff": 0,
        "cooldown_keys": 0,
    }

    # latest close_time per (model, symbol) for cooldown seeding
    latest_close: dict[tuple[str, str], int] = defaultdict(int)

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
                if as_of_ms is not None and int(row["open_time"]) >= as_of_ms:
                    counts["skipped_after_cutoff"] += 1
                    continue
                model_name = sym_to_model[sym]
                trade = _row_to_trade(
                    row,
                    model_name=model_name,
                    as_of_ms=as_of_ms,
                    timeout_minutes=live_config.timeout_minutes,
                    max_amount_usd=live_config.max_amount_usd,
                )
                if trade is None:
                    continue
                store.upsert_trade(trade)
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

    # Close the seeder's StateStore connection so subsequent readers
    # (LiveEngine in particular) see the seeded rows on a fresh connection.
    # Without this explicit close, SQLite WAL behavior leaves the engine
    # reading an inconsistent snapshot.
    store.close()

    return counts
