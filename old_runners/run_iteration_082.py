"""Iter 082: Ternary 2.0% + cooldown=0.

Same as iter 080 but cooldown_candles=0.
Tests if cooldown is redundant with ternary's noise filtering.
"""
import sys
import time
from pathlib import Path

from crypto_trade.backtest import EarlyStopError, run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 82
SYMBOLS = ("BTCUSDT", "ETHUSDT")


def main(seed: int = 42) -> None:
    print("Iter 082: ternary 2.0% + cooldown=0")
    config = BacktestConfig(
        symbols=SYMBOLS,
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
        data_dir=Path("data"),
        cooldown_candles=0,
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
        seed=seed,
        verbose=1,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        ensemble_seeds=[42, 123, 789],
        neutral_threshold_pct=2.0,
    )
    start = time.time()
    try:
        results = run_backtest(config, strategy, yearly_pnl_check=True)
        elapsed = time.time() - start
        print(f"\nBacktest complete: {len(results)} trades in {elapsed:.0f}s")
    except EarlyStopError as e:
        elapsed = time.time() - start
        results = e.results
        print(f"\n*** EARLY STOP: {e.reason} *** ({elapsed:.0f}s)")

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
