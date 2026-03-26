"""Run iteration 041 (EXPLORATION): BTC+ETH, TP=5%/SL=2.5% with real fail-fast."""
import sys, time
from pathlib import Path
from crypto_trade.backtest import run_backtest, EarlyStopError
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 41
SYMBOLS = ("BTCUSDT", "ETHUSDT")

def main() -> None:
    print(f"Iteration 041 (EXPLORATION): BTC+ETH, TP=5% SL=2.5% + FAIL FAST")
    config = BacktestConfig(
        symbols=SYMBOLS, interval="8h", max_amount_usd=1000.0,
        stop_loss_pct=2.5, take_profit_pct=5.0, timeout_minutes=4320,
        fee_pct=0.1, data_dir=Path("data"),
    )
    strategy = LightGbmStrategy(
        training_months=12, n_trials=50, cv_splits=5,
        label_tp_pct=5.0, label_sl_pct=2.5, label_timeout_minutes=4320,
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
        print(f"Partial results: {len(results)} trades")

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
