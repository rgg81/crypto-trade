"""Run iteration 001 backtest: walk-forward LightGBM on all eligible symbols."""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy
from crypto_trade.strategies.ml.universe import select_symbols

ITERATION = 1


def main() -> None:
    # Select symbol universe per research brief
    print("Selecting symbol universe...")
    symbols = tuple(select_symbols())
    print(f"Selected {len(symbols)} symbols")

    # Configure backtest per research brief
    config = BacktestConfig(
        symbols=symbols,
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=2.0,
        take_profit_pct=4.0,
        timeout_minutes=4320,  # 3 days
        fee_pct=0.1,
        data_dir=Path("data"),
    )

    # Create strategy with research brief parameters
    strategy = LightGbmStrategy(
        training_months=12,
        n_trials=50,
        cv_splits=5,
        label_tp_pct=4.0,
        label_sl_pct=2.0,
        label_timeout_minutes=4320,
        fee_pct=0.1,
        features_dir="data/features",
        seed=42,
        verbose=1,
    )

    print(f"\nStarting backtest: {len(symbols)} symbols, 8h, "
          f"TP=4% SL=2% timeout=4320m fee=0.1%")
    print(f"Walk-forward: 12-month training, 50 Optuna trials, 5 CV splits")
    start = time.time()

    results = run_backtest(config, strategy)

    elapsed = time.time() - start
    print(f"\nBacktest complete: {len(results)} trades, "
          f"{results.total_signals} signals in {elapsed:.0f}s")

    if not results:
        print("No trades generated — check data and strategy.")
        sys.exit(1)

    # Generate IS/OOS split reports
    print("\nGenerating iteration reports...")
    report_dir = generate_iteration_reports(
        trades=list(results),
        iteration=ITERATION,
        features_dir="data/features",
        reports_dir="reports",
        interval="8h",
    )
    print(f"\nReports saved to {report_dir}")


if __name__ == "__main__":
    main()
