"""Run iteration 004 backtest: top 50 symbols by IS quote volume."""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 4

# Top 50 symbols by average IS-period quote volume
TOP_50_SYMBOLS = (
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
    "1000PEPEUSDT", "LUNAUSDT", "BNBUSDT", "1000SHIBUSDT", "ADAUSDT",
    "SUIUSDT", "MATICUSDT", "GMTUSDT", "AVAXUSDT", "LINKUSDT",
    "LTCUSDT", "DOTUSDT", "APTUSDT", "ARBUSDT", "ETCUSDT",
    "FTMUSDT", "APEUSDT", "GALAUSDT", "SANDUSDT", "FILUSDT",
    "OPUSDT", "BCHUSDT", "NEARUSDT", "AXSUSDT", "EOSUSDT",
    "MANAUSDT", "DYDXUSDT", "CFXUSDT", "ATOMUSDT", "PEOPLEUSDT",
    "INJUSDT", "AAVEUSDT", "UNIUSDT", "1000FLOKIUSDT", "CRVUSDT",
    "FETUSDT", "CHZUSDT", "TRXUSDT", "TRBUSDT", "STXUSDT",
    "RNDRUSDT", "MASKUSDT", "XLMUSDT", "LDOUSDT", "WAVESUSDT",
)


def main() -> None:
    symbols = TOP_50_SYMBOLS
    print(f"Using top {len(symbols)} symbols by IS quote volume")

    config = BacktestConfig(
        symbols=symbols,
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=2.0,
        take_profit_pct=4.0,
        timeout_minutes=4320,
        fee_pct=0.1,
        data_dir=Path("data"),
    )

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

    print(f"\nIteration 004: top 50 symbols (from 201)")
    print(f"Backtest: {len(symbols)} symbols, 8h, TP=4% SL=2%")
    start = time.time()

    results = run_backtest(config, strategy)

    elapsed = time.time() - start
    print(f"\nBacktest complete: {len(results)} trades, "
          f"{results.total_signals} signals in {elapsed:.0f}s")

    if not results:
        print("No trades generated.")
        sys.exit(1)

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
