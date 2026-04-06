"""Run iteration 016: BTC+ETH, confidence threshold 0.50-0.85."""
import sys, time
from pathlib import Path
from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 16
SYMBOLS = ("BTCUSDT", "ETHUSDT")

def main() -> None:
    print(f"Iteration 016: BTC+ETH, confidence 0.50-0.85")
    config = BacktestConfig(
        symbols=SYMBOLS, interval="8h", max_amount_usd=1000.0,
        stop_loss_pct=2.0, take_profit_pct=4.0, timeout_minutes=4320,
        fee_pct=0.1, data_dir=Path("data"),
    )
    strategy = LightGbmStrategy(
        training_months=12, n_trials=50, cv_splits=5,
        label_tp_pct=4.0, label_sl_pct=2.0, label_timeout_minutes=4320,
        fee_pct=0.1, features_dir="data/features", seed=42, verbose=1,
    )
    start = time.time()
    results = run_backtest(config, strategy)
    elapsed = time.time() - start
    print(f"\nBacktest: {len(results)} trades, {results.total_signals} signals in {elapsed:.0f}s")
    if not results:
        print("No trades."); sys.exit(1)
    report_dir = generate_iteration_reports(
        trades=list(results), iteration=ITERATION,
        features_dir="data/features", reports_dir="reports", interval="8h",
    )
    print(f"Reports: {report_dir}")

if __name__ == "__main__":
    main()
