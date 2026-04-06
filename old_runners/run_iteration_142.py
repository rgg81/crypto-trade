"""Iter 142: Multi-symbol screening — AVAX, ATOM, DOGE.

Screen 3 new candidates for Model E using LINK/BNB template (ATR 3.5x/1.75x).
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 142


def screen_symbol(symbol: str) -> None:
    print("=" * 60)
    print(f"SCREENING: {symbol}")
    print("=" * 60)

    config = BacktestConfig(
        symbols=(symbol,), interval="8h", max_amount_usd=1000.0,
        stop_loss_pct=4.0, take_profit_pct=8.0, timeout_minutes=10080,
        fee_pct=0.1, data_dir=Path("data"), cooldown_candles=2,
    )
    strategy = LightGbmStrategy(
        training_months=24, n_trials=50, cv_splits=5,
        label_tp_pct=8.0, label_sl_pct=4.0, label_timeout_minutes=10080,
        fee_pct=0.1, features_dir="data/features", seed=42, verbose=1,
        atr_tp_multiplier=3.5, atr_sl_multiplier=1.75,
        use_atr_labeling=True,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=None,
    )
    start = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - start
    print(f"\n{symbol} complete: {len(results)} trades in {elapsed:.0f}s")

    if not results:
        print(f"{symbol}: No trades.")
        return

    # Per-symbol iteration reports (sub-directory per symbol)
    report_dir = generate_iteration_reports(
        trades=results, iteration=f"{ITERATION}_{symbol.replace('USDT', '')}",
        features_dir="data/features", reports_dir="reports", interval="8h",
    )
    print(f"{symbol} reports: {report_dir}")


def main() -> None:
    print(f"Iter {ITERATION}: MULTI-SYMBOL SCREENING — AVAX, ATOM, DOGE")
    print()

    for symbol in ["AVAXUSDT", "ATOMUSDT", "DOGEUSDT"]:
        screen_symbol(symbol)

    print("\n" + "=" * 60)
    print("All symbols screened. Check reports/iteration_142_*/")
    print("=" * 60)


if __name__ == "__main__":
    main()
