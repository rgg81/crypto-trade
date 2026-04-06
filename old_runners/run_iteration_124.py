"""Iter 124: SOL with ATR labeling (meme-proven architecture).

Re-test SOL standalone with ATR-based labeling instead of static barriers.
Iter 123 showed IS WR 40.6% but IS Sharpe +0.055 with static 8%/4%.
ATR labeling should adapt to SOL's higher volatility (NATR ~5-8%).
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 124


def main() -> None:
    print(f"Iter {ITERATION}: SOL with ATR labeling (3.5x/1.75x)")
    print()

    config = BacktestConfig(
        symbols=("SOLUSDT",),
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
        data_dir=Path("data"),
        cooldown_candles=2,
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
        use_atr_labeling=True,  # KEY CHANGE: ATR-based labeling
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=None,  # auto-discovery (~185 features)
    )

    start = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - start
    print(f"\nSOL ATR model complete: {len(results)} trades in {elapsed:.0f}s")

    if not results:
        print("No trades.")
        sys.exit(1)

    report_dir = generate_iteration_reports(
        trades=results,
        iteration=ITERATION,
        features_dir="data/features",
        reports_dir="reports",
        interval="8h",
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
