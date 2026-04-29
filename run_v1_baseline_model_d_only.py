"""Fail-fast: run ONLY Model D (BNB, fastest ~1.5h) with schema-order features.

If D's trades match BASELINE exactly → hypothesis confirmed, run full A+C+D.
If D's trades differ even slightly → stop, investigate further.

Output: reports/iteration_152_core_D_only/
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.baseline_feature_columns import BASELINE_FEATURE_COLUMNS_V152
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy


def main() -> None:
    print(f"Iter 152_core_D_only: Model D BNB validation, {len(BASELINE_FEATURE_COLUMNS_V152)} schema-order features")
    print()

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
    strategy = LightGbmStrategy(
        training_months=24,
        n_trials=50,
        cv_splits=5,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir="data/features",
        seed=42,
        verbose=1,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        use_atr_labeling=True,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=None,  # auto-discovery — should return parquet schema order
    )

    start = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - start
    print(f"\nModel D complete: {len(results)} trades in {elapsed:.0f}s")

    if not results:
        print("No trades.")
        sys.exit(1)

    report_dir = generate_iteration_reports(
        trades=results,
        iteration="152_core_D_only",
        features_dir="data/features",
        reports_dir="reports",
        interval="8h",
        n_trials=163,
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
