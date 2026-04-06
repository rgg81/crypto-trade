"""Iter 139: ETH standalone screening — ATR labeling 2.9x/1.45x.

Test ETH as standalone model matching Model A's ATR config.
Hypothesis: ETH's 55.9% pooled WR could be even higher standalone.
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 139


def main() -> None:
    print(f"Iter {ITERATION}: ETH STANDALONE — ATR LABELING 2.9x/1.45x")
    print("=" * 60)

    config = BacktestConfig(
        symbols=("ETHUSDT",), interval="8h", max_amount_usd=1000.0,
        stop_loss_pct=4.0, take_profit_pct=8.0, timeout_minutes=10080,
        fee_pct=0.1, data_dir=Path("data"), cooldown_candles=2,
    )
    strategy = LightGbmStrategy(
        training_months=24, n_trials=50, cv_splits=5,
        label_tp_pct=8.0, label_sl_pct=4.0, label_timeout_minutes=10080,
        fee_pct=0.1, features_dir="data/features", seed=42, verbose=1,
        atr_tp_multiplier=2.9, atr_sl_multiplier=1.45,
        use_atr_labeling=True,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=None,
    )
    start = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - start
    print(f"\nETH complete: {len(results)} trades in {elapsed:.0f}s")

    if not results:
        print("No trades.")
        sys.exit(1)

    report_dir = generate_iteration_reports(
        trades=results, iteration=ITERATION,
        features_dir="data/features", reports_dir="reports", interval="8h",
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
