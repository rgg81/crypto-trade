"""Test if LGBM is deterministic on REAL crypto training data (not synthetic).

Trains the same BNB Feb 2022 walk-forward split twice with identical inputs.
If predictions differ, LightGBM is non-deterministic on real data.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from crypto_trade.backtest import _build_master
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy


def train_and_get_model(seed_offset: int = 0):
    """Train Model D on BNB for Feb 2022 walk-forward split. Return first prediction."""
    config = BacktestConfig(
        symbols=("BNBUSDT",),
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
        data_dir=Path("data"),
        cooldown_candles=2,
        vol_targeting=True,
        vt_target_vol=0.3,
        vt_lookback_days=45,
        vt_min_scale=0.33,
        vt_max_scale=2.0,
    )
    strat = LightGbmStrategy(
        training_months=24,
        n_trials=50,
        cv_splits=5,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir="data/features",
        seed=42,
        verbose=0,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        use_atr_labeling=True,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=None,  # auto-discovery, same as BASELINE
    )
    master = _build_master(config)
    strat.compute_features(master)

    # Train for Feb 2022
    target_month = "2022-02"
    if target_month not in strat._split_map:
        print(f"Target month {target_month} not in splits")
        return None
    start = time.time()
    strat._train_for_month(target_month)
    elapsed = time.time() - start
    print(f"  Training took {elapsed:.1f}s, {len(strat._models)} ensemble models trained")

    return {
        "n_models": len(strat._models),
        "threshold": strat._confidence_threshold,
        "selected_cols": list(strat._selected_cols[:10]),
    }


def main() -> None:
    print("=== RUN 1: BNB Feb 2022 training ===")
    r1 = train_and_get_model()
    print(f"  Result: {r1}")
    print()
    print("=== RUN 2: BNB Feb 2022 training (same inputs) ===")
    r2 = train_and_get_model()
    print(f"  Result: {r2}")
    print()
    print("=== Comparison ===")
    if r1 and r2:
        print(f"Same threshold? {r1['threshold'] == r2['threshold']}")
        print(f"Threshold run1: {r1['threshold']}, run2: {r2['threshold']}")


if __name__ == "__main__":
    main()
