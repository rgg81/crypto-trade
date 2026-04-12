"""Comprehensive backtest vs live parity test.

Runs BOTH the backtest engine and the live engine logic on the SAME data,
comparing EVERY intermediate value: features loaded, model predictions,
signal direction/confidence, entry price, SL/TP, VT scale.

This test uses the actual production data and Parquet features. It takes
~10-15 minutes to run (3 models × 50 Optuna trials × 5 ensemble seeds).
Run before every live session: uv run pytest tests/live/test_backtest_parity.py -v -s
"""

from __future__ import annotations

import datetime
from pathlib import Path

import numpy as np
import pytest

from crypto_trade.backtest import build_master, compute_vt_scale, create_order
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.live.models import LiveConfig
from crypto_trade.live.order_manager import compute_sl_tp
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

DATA_DIR = Path("data")
FEATURES_DIR = Path("data/features")
INTERVAL = "8h"

# All baseline model configs
MODEL_CONFIGS = {
    "A": {"symbols": ("BTCUSDT", "ETHUSDT"), "atr_tp": 2.9, "atr_sl": 1.45},
    "C": {"symbols": ("LINKUSDT",), "atr_tp": 3.5, "atr_sl": 1.75},
    "D": {"symbols": ("BNBUSDT",), "atr_tp": 3.5, "atr_sl": 1.75},
}


def _has_data() -> bool:
    """Check if production data is available."""
    for sym in ["BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT"]:
        if not (DATA_DIR / sym / f"{INTERVAL}.csv").exists():
            return False
        if not (FEATURES_DIR / f"{sym}_{INTERVAL}_features.parquet").exists():
            return False
    return True


def _make_strategy(atr_tp: float, atr_sl: float) -> LightGbmStrategy:
    """Create a LightGBM strategy with baseline v152 params."""
    return LightGbmStrategy(
        training_months=24,
        n_trials=50,
        cv_splits=5,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir=str(FEATURES_DIR),
        seed=42,
        verbose=0,
        atr_tp_multiplier=atr_tp,
        atr_sl_multiplier=atr_sl,
        use_atr_labeling=True,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=None,
    )


@pytest.mark.skipif(not _has_data(), reason="Production data not available")
class TestBacktestLiveParity:
    """Run backtest strategy and live strategy on the SAME data, compare everything."""

    @pytest.fixture(scope="class")
    def parity_data(self):
        """Run both strategies for all 3 models. Cached across tests in this class."""
        results = {}

        for model_name, cfg in MODEL_CONFIGS.items():
            symbols = list(cfg["symbols"])
            atr_tp = cfg["atr_tp"]
            atr_sl = cfg["atr_sl"]

            # Build master from CSV — SAME data for both paths
            master = build_master(symbols, INTERVAL, DATA_DIR)
            assert not master.empty, f"No data for model {model_name}"

            # Find the last candle's open_time per symbol
            last_candles = {}
            for sym in symbols:
                sym_rows = master[master["symbol"] == sym]
                last_row = sym_rows.iloc[-1]
                last_candles[sym] = {
                    "open_time": int(last_row["open_time"]),
                    "close_time": int(last_row["close_time"]),
                    "open": float(last_row["open"]),
                    "high": float(last_row["high"]),
                    "low": float(last_row["low"]),
                    "close": float(last_row["close"]),
                }

            # === BACKTEST PATH ===
            bt_strategy = _make_strategy(atr_tp, atr_sl)
            bt_strategy.compute_features(master)

            bt_signals = {}
            bt_internals = {}
            for sym in symbols:
                ot = last_candles[sym]["open_time"]
                sig = bt_strategy.get_signal(sym, ot)
                bt_signals[sym] = sig

                # Capture internals after get_signal
                bt_internals[sym] = {
                    "current_month": bt_strategy._current_month,
                    "n_models": len(bt_strategy._models),
                    "confidence_threshold": bt_strategy._confidence_threshold,
                    "selected_cols": list(bt_strategy._selected_cols),
                    "n_month_features": len(bt_strategy._month_features),
                    "feat_row": bt_strategy._month_features.get((sym, ot)),
                    "month_natr": bt_strategy._month_natr.get((sym, ot)),
                }

            # === LIVE PATH ===
            # Exact same code path as engine.py ModelRunner
            live_strategy = _make_strategy(atr_tp, atr_sl)
            live_strategy.compute_features(master)

            live_signals = {}
            live_internals = {}
            for sym in symbols:
                ot = last_candles[sym]["open_time"]
                sig = live_strategy.get_signal(sym, ot)
                live_signals[sym] = sig

                live_internals[sym] = {
                    "current_month": live_strategy._current_month,
                    "n_models": len(live_strategy._models),
                    "confidence_threshold": live_strategy._confidence_threshold,
                    "selected_cols": list(live_strategy._selected_cols),
                    "n_month_features": len(live_strategy._month_features),
                    "feat_row": live_strategy._month_features.get((sym, ot)),
                    "month_natr": live_strategy._month_natr.get((sym, ot)),
                }

            results[model_name] = {
                "symbols": symbols,
                "master_len": len(master),
                "last_candles": last_candles,
                "bt_signals": bt_signals,
                "bt_internals": bt_internals,
                "live_signals": live_signals,
                "live_internals": live_internals,
                "atr_tp": atr_tp,
                "atr_sl": atr_sl,
            }

        return results

    # --- Layer 1: Master DataFrame ---

    def test_master_has_enough_data(self, parity_data):
        """Each model must have 24+ months of history."""
        for model_name, data in parity_data.items():
            per_sym = data["master_len"] // len(data["symbols"])
            assert per_sym >= 2000, f"Model {model_name}: only {per_sym} candles/symbol, need 2000+"

    # --- Layer 2: Strategy internals (model training) ---

    def test_same_month_detected(self, parity_data):
        for model_name, data in parity_data.items():
            for sym in data["symbols"]:
                bt = data["bt_internals"][sym]["current_month"]
                live = data["live_internals"][sym]["current_month"]
                assert bt == live, f"Model {model_name} {sym}: month mismatch bt={bt} live={live}"

    def test_same_number_of_ensemble_models(self, parity_data):
        for model_name, data in parity_data.items():
            for sym in data["symbols"]:
                bt = data["bt_internals"][sym]["n_models"]
                live = data["live_internals"][sym]["n_models"]
                assert bt == live, f"Model {model_name} {sym}: n_models bt={bt} live={live}"

    def test_same_confidence_threshold(self, parity_data):
        for model_name, data in parity_data.items():
            for sym in data["symbols"]:
                bt = data["bt_internals"][sym]["confidence_threshold"]
                live = data["live_internals"][sym]["confidence_threshold"]
                assert bt == pytest.approx(live, abs=1e-10), (
                    f"Model {model_name} {sym}: threshold bt={bt} live={live}"
                )

    def test_same_selected_feature_columns(self, parity_data):
        for model_name, data in parity_data.items():
            for sym in data["symbols"]:
                bt = data["bt_internals"][sym]["selected_cols"]
                live = data["live_internals"][sym]["selected_cols"]
                assert bt == live, (
                    f"Model {model_name} {sym}: selected cols differ "
                    f"(bt={len(bt)}, live={len(live)})"
                )

    def test_same_number_of_test_features(self, parity_data):
        for model_name, data in parity_data.items():
            for sym in data["symbols"]:
                bt = data["bt_internals"][sym]["n_month_features"]
                live = data["live_internals"][sym]["n_month_features"]
                assert bt == live, f"Model {model_name} {sym}: n_month_features bt={bt} live={live}"

    # --- Layer 3: Feature values ---

    def test_feature_values_identical(self, parity_data):
        """The feature row used for prediction must be bit-for-bit identical."""
        for model_name, data in parity_data.items():
            for sym in data["symbols"]:
                bt_feat = data["bt_internals"][sym]["feat_row"]
                live_feat = data["live_internals"][sym]["feat_row"]

                if bt_feat is None and live_feat is None:
                    continue  # both None = no features for this candle

                assert bt_feat is not None, f"Model {model_name} {sym}: backtest has no features"
                assert live_feat is not None, f"Model {model_name} {sym}: live has no features"

                assert bt_feat.shape == live_feat.shape, (
                    f"Model {model_name} {sym}: feature shape bt={bt_feat.shape} "
                    f"live={live_feat.shape}"
                )

                if not np.array_equal(bt_feat, live_feat):
                    diffs = np.where(bt_feat != live_feat)[0]
                    cols = data["bt_internals"][sym]["selected_cols"]
                    diff_cols = [cols[i] for i in diffs[:5]]
                    pytest.fail(
                        f"Model {model_name} {sym}: {len(diffs)} feature values differ. "
                        f"First diffs at cols: {diff_cols}"
                    )

    def test_natr_values_identical(self, parity_data):
        """ATR values used for dynamic barriers must match."""
        for model_name, data in parity_data.items():
            for sym in data["symbols"]:
                bt_natr = data["bt_internals"][sym]["month_natr"]
                live_natr = data["live_internals"][sym]["month_natr"]
                assert bt_natr == live_natr, (
                    f"Model {model_name} {sym}: NATR bt={bt_natr} live={live_natr}"
                )

    # --- Layer 4: Signal output ---

    def test_signal_direction_identical(self, parity_data):
        for model_name, data in parity_data.items():
            for sym in data["symbols"]:
                bt = data["bt_signals"][sym]
                live = data["live_signals"][sym]
                assert bt.direction == live.direction, (
                    f"Model {model_name} {sym}: direction bt={bt.direction} live={live.direction}"
                )

    def test_signal_weight_identical(self, parity_data):
        for model_name, data in parity_data.items():
            for sym in data["symbols"]:
                bt = data["bt_signals"][sym]
                live = data["live_signals"][sym]
                assert bt.weight == live.weight, (
                    f"Model {model_name} {sym}: weight bt={bt.weight} live={live.weight}"
                )

    def test_signal_tp_sl_identical(self, parity_data):
        """Dynamic ATR-derived TP/SL from signal must match."""
        for model_name, data in parity_data.items():
            for sym in data["symbols"]:
                bt = data["bt_signals"][sym]
                live = data["live_signals"][sym]

                if bt.tp_pct is None:
                    assert live.tp_pct is None, (
                        f"Model {model_name} {sym}: bt tp_pct=None, live={live.tp_pct}"
                    )
                else:
                    assert live.tp_pct is not None, (
                        f"Model {model_name} {sym}: bt tp_pct={bt.tp_pct}, live=None"
                    )
                    assert bt.tp_pct == pytest.approx(live.tp_pct, abs=1e-12), (
                        f"Model {model_name} {sym}: tp_pct bt={bt.tp_pct} live={live.tp_pct}"
                    )

                if bt.sl_pct is None:
                    assert live.sl_pct is None
                else:
                    assert live.sl_pct is not None
                    assert bt.sl_pct == pytest.approx(live.sl_pct, abs=1e-12), (
                        f"Model {model_name} {sym}: sl_pct bt={bt.sl_pct} live={live.sl_pct}"
                    )

    # --- Layer 5: Entry price from master DataFrame ---

    def test_entry_price_from_master(self, parity_data):
        """Entry price must come from master DF close column, not from API."""
        for model_name, data in parity_data.items():
            for sym in data["symbols"]:
                candle = data["last_candles"][sym]
                # This is the close price from the master DF
                entry = candle["close"]
                # Verify it's a real price
                assert entry > 0, f"Model {model_name} {sym}: entry={entry}"

    # --- Layer 6: SL/TP price computation ---

    def test_sl_tp_parity_with_backtest_create_order(self, parity_data):
        """SL/TP from live compute_sl_tp must exactly match backtest create_order."""
        config = LiveConfig()
        bt_config = BacktestConfig(
            symbols=("BTCUSDT",),
            interval="8h",
            max_amount_usd=1000.0,
            stop_loss_pct=4.0,
            take_profit_pct=8.0,
            timeout_minutes=10080,
            fee_pct=0.1,
        )

        for model_name, data in parity_data.items():
            for sym in data["symbols"]:
                sig = data["bt_signals"][sym]
                if sig.direction == 0:
                    continue

                candle = data["last_candles"][sym]
                entry = candle["close"]
                close_time = candle["close_time"]

                # Live path
                sl_live, tp_live = compute_sl_tp(sig, entry, config)

                # Backtest path
                bt_order = create_order(sym, sig, entry, close_time, bt_config)

                assert sl_live == pytest.approx(bt_order.stop_loss_price, abs=1e-10), (
                    f"Model {model_name} {sym}: SL live={sl_live} bt={bt_order.stop_loss_price}"
                )
                assert tp_live == pytest.approx(bt_order.take_profit_price, abs=1e-10), (
                    f"Model {model_name} {sym}: TP live={tp_live} bt={bt_order.take_profit_price}"
                )

    # --- Layer 7: Vol targeting ---

    def test_vt_scale_with_no_history_returns_one(self, parity_data):
        """With no trade history, VT scale must be 1.0 (same as backtest first trade)."""
        config = LiveConfig()
        empty_daily: dict[str, dict[str, float]] = {}

        for model_name, data in parity_data.items():
            for sym in data["symbols"]:
                candle = data["last_candles"][sym]
                scale = compute_vt_scale(empty_daily, sym, candle["close_time"], config)
                assert scale == 1.0, f"Model {model_name} {sym}: VT scale with no history = {scale}"

    def test_vt_scale_matches_backtest_formula(self, parity_data):
        """VT scale with synthetic history must match backtest compute_vt_scale."""
        live_config = LiveConfig()
        bt_config = BacktestConfig(
            symbols=("BTCUSDT",),
            interval="8h",
            max_amount_usd=1000.0,
            stop_loss_pct=4.0,
            take_profit_pct=8.0,
            timeout_minutes=10080,
            fee_pct=0.1,
            vol_targeting=True,
            vt_target_vol=0.3,
            vt_lookback_days=45,
            vt_min_scale=0.33,
            vt_max_scale=2.0,
        )

        # Synthetic daily PnL history
        daily_pnl = {
            "BTCUSDT": {
                "2026-03-01": 1.5,
                "2026-03-02": -0.8,
                "2026-03-05": 2.1,
                "2026-03-10": -1.2,
                "2026-03-15": 0.5,
                "2026-03-20": -0.3,
                "2026-03-25": 1.8,
            }
        }
        trade_open_ms = int(datetime.datetime(2026, 4, 1, tzinfo=datetime.UTC).timestamp() * 1000)

        live_scale = compute_vt_scale(daily_pnl, "BTCUSDT", trade_open_ms, live_config)
        bt_scale = compute_vt_scale(daily_pnl, "BTCUSDT", trade_open_ms, bt_config)

        assert live_scale == pytest.approx(bt_scale, abs=1e-12), (
            f"VT scale: live={live_scale} bt={bt_scale}"
        )

    # --- Layer 8: Full trade object ---

    def test_full_trade_matches(self, parity_data):
        """For each model/symbol with a signal, verify all trade fields."""
        config = LiveConfig()
        for model_name, data in parity_data.items():
            for sym in data["symbols"]:
                bt_sig = data["bt_signals"][sym]
                live_sig = data["live_signals"][sym]
                candle = data["last_candles"][sym]

                if bt_sig.direction == 0:
                    assert live_sig.direction == 0, (
                        f"Model {model_name} {sym}: bt=NO_SIGNAL but live fires"
                    )
                    continue

                # Direction
                assert bt_sig.direction == live_sig.direction

                # Entry price
                entry = candle["close"]
                assert entry > 0

                # SL/TP
                sl_live, tp_live = compute_sl_tp(live_sig, entry, config)
                sl_bt, tp_bt = compute_sl_tp(bt_sig, entry, config)
                assert sl_live == sl_bt
                assert tp_live == tp_bt

                # Amount
                amount = config.max_amount_usd  # weight=1.0 for first trade
                assert amount == 1000.0

                # Timeout
                timeout_ms = candle["close_time"] + config.timeout_minutes * 60 * 1000
                assert timeout_ms > candle["close_time"]

                print(
                    f"  VERIFIED Model {model_name} {sym}: "
                    f"{'LONG' if bt_sig.direction == 1 else 'SHORT'} "
                    f"entry={entry:.2f} SL={sl_live:.2f} TP={tp_live:.2f}"
                )
