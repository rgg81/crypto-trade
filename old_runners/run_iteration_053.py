"""Iter 053 (EXPLORATION): Test BNB+LINK as independent pair (separate portfolio).

If BNB+LINK also works at 8%/4% + 7d + 24mo, we have 2 independent profit streams.
Not pooled with BTC+ETH — completely separate model and trades.
"""
import sys, time
from pathlib import Path
from crypto_trade.backtest import run_backtest, EarlyStopError
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 53
SYMBOLS = ("BNBUSDT", "LINKUSDT")

def main() -> None:
    print(f"Iter 053 (EXPLORATION): BNB+LINK independent pair")
    config = BacktestConfig(
        symbols=SYMBOLS, interval="8h", max_amount_usd=1000.0,
        stop_loss_pct=4.0, take_profit_pct=8.0, timeout_minutes=10080,
        fee_pct=0.1, data_dir=Path("data"),
    )
    strategy = LightGbmStrategy(
        training_months=24, n_trials=50, cv_splits=5,
        label_tp_pct=8.0, label_sl_pct=4.0, label_timeout_minutes=10080,
        fee_pct=0.1, features_dir="data/features", seed=42, verbose=1,
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
        print("No trades."); sys.exit(1)
    report_dir = generate_iteration_reports(
        trades=list(results) if not isinstance(results, list) else results,
        iteration=ITERATION,
        features_dir="data/features", reports_dir="reports", interval="8h",
    )
    print(f"Reports: {report_dir}")

if __name__ == "__main__":
    main()
