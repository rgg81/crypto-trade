"""v2 catch-up parity test: live engine reproduces run_baseline_v2 OOS trades.

Slow (~2-3h) — runs full Optuna training × 5 seeds for each of the 4 v2
models. Gated behind ``-m parity`` so it only fires on explicit request.

The assertion is a field-for-field equality on the OOS trade rows produced by
the live engine's catch-up phase against ``reports-v2/iteration_v2-069/
out_of_sample/trades.csv`` (the canonical v2 backtest output).

Comparison rules:
  - ignore zero-weight rows from the backtest (BTC trend filter post-hoc
    zeros them; the live engine never opens them in the first place)
  - filter both streams to ``open_time >= 2025-03-24`` (OOS cutoff)
  - sort by (open_time, symbol) before assert_frame_equal
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

V2_TRADES_CSV = Path("reports-v2/iteration_v2-069/out_of_sample/trades.csv")
V2_FEATURES_DIR = Path("data/features_v2")
V1_FEATURES_DIR = Path("data/features")
DATA_DIR = Path("data")
OOS_CUTOFF_MS = pd.Timestamp("2025-03-24", tz="UTC").value // 1_000_000

# Columns to compare exactly. Skip pnl_pct/exit_price for floating tolerance.
TRADE_COLS = [
    "symbol",
    "direction",
    "entry_price",
    "exit_price",
    "weight_factor",
    "open_time",
    "close_time",
    "exit_reason",
    "pnl_pct",
    "fee_pct",
    "net_pnl_pct",
    "weighted_pnl",
]

V2_SYMBOLS = {"DOGEUSDT", "SOLUSDT", "XRPUSDT", "NEARUSDT"}


def _data_present() -> bool:
    if not V2_TRADES_CSV.exists():
        return False
    for sym in V2_SYMBOLS:
        if not (V2_FEATURES_DIR / f"{sym}_8h_features.parquet").exists():
            return False
        if not (DATA_DIR / sym / "8h.csv").exists():
            return False
    if not (DATA_DIR / "BTCUSDT" / "8h.csv").exists():
        return False
    return True


def _read_closed_trades_from_db(db_path: Path) -> pd.DataFrame:
    """Read closed trades from the live DB into a DataFrame matching trades.csv shape."""
    from crypto_trade.live.state_store import StateStore
    from crypto_trade.live.trade_logger import to_trade_result

    store = StateStore(db_path)
    rows: list[dict] = []
    for trade in store.get_all_trades():
        if trade.status != "closed":
            continue
        result = to_trade_result(trade, fee_pct=0.1)
        if result is None:
            continue
        rows.append(
            {
                "symbol": result.symbol,
                "direction": result.direction,
                "entry_price": result.entry_price,
                "exit_price": result.exit_price,
                "weight_factor": result.weight_factor,
                "open_time": result.open_time,
                "close_time": result.close_time,
                "exit_reason": result.exit_reason,
                "pnl_pct": result.pnl_pct,
                "fee_pct": result.fee_pct,
                "net_pnl_pct": result.net_pnl_pct,
                "weighted_pnl": result.weighted_pnl,
            }
        )
    return pd.DataFrame(rows, columns=TRADE_COLS)


@pytest.mark.parity
@pytest.mark.skipif(not _data_present(), reason="v2 data + backtest trades not available")
def test_v2_live_catchup_matches_backtest(tmp_path):
    """Live engine catch-up on V2_BASELINE_MODELS reproduces the v2 backtest OOS trades.

    NOTE: the live engine's _catch_up only replays the previous month, so this
    test asserts the slice of OOS trades that fall within that month, not the
    full OOS history. For the full headline assertion see
    test_backtest_parity_combined.py and run with the engine in dry-run mode
    overnight.
    """
    from crypto_trade.live.engine import LiveEngine
    from crypto_trade.live.models import LiveConfig, V2_BASELINE_MODELS

    cfg = LiveConfig(
        models=V2_BASELINE_MODELS,
        dry_run=True,
        db_path=tmp_path / "v2.db",
        data_dir=DATA_DIR,
        features_dir=V1_FEATURES_DIR,  # ignored for v2 runners (per-model override)
    )
    engine = LiveEngine(cfg)
    engine.catch_up_only()

    live = _read_closed_trades_from_db(tmp_path / "v2.db")
    backtest = pd.read_csv(V2_TRADES_CSV)
    backtest = backtest[backtest["weight_factor"] > 0]  # drop BTC-zeroed rows

    # Filter both streams to the catch-up window: previous-month boundary in ms.
    # The engine's _catch_up starts at _previous_month_start_ms(now), so we
    # restrict the backtest comparison to the same range.
    catchup_floor = int(live["open_time"].min()) if not live.empty else OOS_CUTOFF_MS
    bt_window = backtest[
        backtest["open_time"] >= catchup_floor
    ].sort_values(["open_time", "symbol"]).reset_index(drop=True)
    live_window = live.sort_values(["open_time", "symbol"]).reset_index(drop=True)

    # Trade count must match exactly within the catch-up window.
    assert len(live_window) == len(bt_window), (
        f"trade count mismatch: live={len(live_window)} vs backtest={len(bt_window)}"
    )
    pd.testing.assert_frame_equal(
        live_window[TRADE_COLS], bt_window[TRADE_COLS], check_exact=True,
    )
