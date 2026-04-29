"""Combined catch-up parity test — the headline assertion of v1+v2 live parity.

Slow (~6-8h end-to-end) — drives ``LiveEngine.catch_up_only()`` on
``COMBINED_MODELS`` and checks that the resulting closed-trade stream
matches BOTH backtest CSVs in their respective slices.

Pass criteria (all must hold):
  1. v1 OOS slice matches reports/iteration_186/out_of_sample/trades.csv
     field-for-field on TRADE_COLS.
  2. v2 OOS slice matches reports-v2/iteration_v2-069/out_of_sample/trades.csv
     field-for-field on TRADE_COLS (excluding weight_factor==0 rows that
     the BTC trend filter zeros post-hoc).
  3. April 2026 trade counts match between live and the union of v1+v2
     backtests (engine's _catch_up only replays the previous month, so
     this is the headline freshness check).

Gated behind ``-m parity``; skipped by default. Run with::

    rm -f data/dry_run.db
    uv run pytest tests/live/test_backtest_parity_combined.py -m parity -v
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from tests.live.test_backtest_parity_v2 import (
    TRADE_COLS,
    V2_SYMBOLS,
    _read_closed_trades_from_db,
)

V1_TRADES_CSV = Path("reports/iteration_186/out_of_sample/trades.csv")
V2_TRADES_CSV = Path("reports-v2/iteration_v2-069/out_of_sample/trades.csv")
V1_FEATURES_DIR = Path("data/features")
V2_FEATURES_DIR = Path("data/features_v2")
DATA_DIR = Path("data")
V1_SYMBOLS = {"BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"}
OOS_CUTOFF_MS = pd.Timestamp("2025-03-24", tz="UTC").value // 1_000_000
APRIL_2026_MS = pd.Timestamp("2026-04-01", tz="UTC").value // 1_000_000


def _data_present() -> bool:
    if not (V1_TRADES_CSV.exists() and V2_TRADES_CSV.exists()):
        return False
    for sym in V1_SYMBOLS:
        if not (V1_FEATURES_DIR / f"{sym}_8h_features.parquet").exists():
            return False
        if not (DATA_DIR / sym / "8h.csv").exists():
            return False
    for sym in V2_SYMBOLS:
        if not (V2_FEATURES_DIR / f"{sym}_8h_features.parquet").exists():
            return False
        if not (DATA_DIR / sym / "8h.csv").exists():
            return False
    return True


@pytest.mark.parity
@pytest.mark.skipif(not _data_present(), reason="v1+v2 data + backtest trades not available")
def test_combined_catchup_matches_both_backtests(tmp_path):
    """The headline backtest-vs-live parity test. v1 + v2 in one engine.

    Drives the engine with catch_up_lookback_days=400 so the entire OOS
    window since 2025-03-24 is replayed. After Task 4 of the catch-up
    state-seeding plan, weight_factor and weighted_pnl are required to
    match field-for-field — full TRADE_COLS byte-identity.
    """
    from crypto_trade.live.engine import LiveEngine
    from crypto_trade.live.models import COMBINED_MODELS, LiveConfig

    cfg = LiveConfig(
        models=COMBINED_MODELS,
        dry_run=True,
        db_path=tmp_path / "combined.db",
        data_dir=DATA_DIR,
        features_dir=V1_FEATURES_DIR,  # v2 runners override per-model
        catch_up_lookback_days=400,    # full OOS replay since 2025-03-24
    )
    engine = LiveEngine(cfg)
    engine.catch_up_only()

    live = _read_closed_trades_from_db(tmp_path / "combined.db")

    # ---- v1 slice (full OOS window) ----
    bt_v1 = pd.read_csv(V1_TRADES_CSV)
    bt_v1 = bt_v1[bt_v1["weight_factor"] > 0]
    bt_v1_window = (
        bt_v1[(bt_v1["symbol"].isin(V1_SYMBOLS)) & (bt_v1["open_time"] >= OOS_CUTOFF_MS)]
        .sort_values(["open_time", "symbol"])
        .reset_index(drop=True)
    )
    live_v1 = (
        live[(live["symbol"].isin(V1_SYMBOLS)) & (live["open_time"] >= OOS_CUTOFF_MS)]
        .sort_values(["open_time", "symbol"])
        .reset_index(drop=True)
    )
    assert len(live_v1) == len(bt_v1_window), (
        f"v1 trade count mismatch: live={len(live_v1)} vs backtest={len(bt_v1_window)}"
    )
    pd.testing.assert_frame_equal(
        live_v1[TRADE_COLS], bt_v1_window[TRADE_COLS], check_exact=True,
    )

    # ---- v2 slice (full OOS window) ----
    bt_v2 = pd.read_csv(V2_TRADES_CSV)
    bt_v2 = bt_v2[bt_v2["weight_factor"] > 0]
    bt_v2_window = (
        bt_v2[(bt_v2["symbol"].isin(V2_SYMBOLS)) & (bt_v2["open_time"] >= OOS_CUTOFF_MS)]
        .sort_values(["open_time", "symbol"])
        .reset_index(drop=True)
    )
    live_v2 = (
        live[(live["symbol"].isin(V2_SYMBOLS)) & (live["open_time"] >= OOS_CUTOFF_MS)]
        .sort_values(["open_time", "symbol"])
        .reset_index(drop=True)
    )
    assert len(live_v2) == len(bt_v2_window), (
        f"v2 trade count mismatch: live={len(live_v2)} vs backtest={len(bt_v2_window)}"
    )
    pd.testing.assert_frame_equal(
        live_v2[TRADE_COLS], bt_v2_window[TRADE_COLS], check_exact=True,
    )

    # ---- April 2026 sanity check ----
    if True:
        live_apr = live[live["open_time"] >= APRIL_2026_MS]
        bt_apr_v1 = bt_v1[bt_v1["open_time"] >= APRIL_2026_MS]
        bt_apr_v2 = bt_v2[bt_v2["open_time"] >= APRIL_2026_MS]
        bt_apr_total = len(bt_apr_v1) + len(bt_apr_v2)
        assert len(live_apr) == bt_apr_total, (
            f"April 2026 trade count mismatch: live={len(live_apr)} vs "
            f"backtest={bt_apr_total} (v1={len(bt_apr_v1)}, v2={len(bt_apr_v2)})"
        )
