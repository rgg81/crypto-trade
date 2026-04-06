"""Iter 129: A+C portfolio — BTC/ETH + LINK (drop meme model).

Model A: BTC/ETH (iter 093 baseline config)
Model C: LINK (iter 126 config — ATR labeling, auto-discovery)
No Model B (meme) — unstable, lost -43% OOS in iter 128.
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 129


def run_model(name, symbols, use_atr_labeling, atr_tp, atr_sl):
    print("=" * 60)
    print(f"MODEL {name}: {', '.join(symbols)}")
    print("=" * 60)
    config = BacktestConfig(
        symbols=symbols, interval="8h", max_amount_usd=1000.0,
        stop_loss_pct=4.0, take_profit_pct=8.0, timeout_minutes=10080,
        fee_pct=0.1, data_dir=Path("data"), cooldown_candles=2,
    )
    strategy = LightGbmStrategy(
        training_months=24, n_trials=50, cv_splits=5,
        label_tp_pct=8.0, label_sl_pct=4.0, label_timeout_minutes=10080,
        fee_pct=0.1, features_dir="data/features", seed=42, verbose=1,
        atr_tp_multiplier=atr_tp, atr_sl_multiplier=atr_sl,
        use_atr_labeling=use_atr_labeling,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=None,
    )
    start = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - start
    print(f"\n{name} complete: {len(results)} trades in {elapsed:.0f}s")
    return results


def main() -> None:
    print(f"Iter {ITERATION}: A+C PORTFOLIO — BTC/ETH + LINK (no meme)")
    print()

    results_a = run_model("A (BTC/ETH)", ("BTCUSDT", "ETHUSDT"), False, 2.9, 1.45)
    results_c = run_model("C (LINK)", ("LINKUSDT",), True, 3.5, 1.75)

    all_results = results_a + results_c
    all_results.sort(key=lambda t: t.close_time)
    print(f"\nCombined: {len(all_results)} trades ({len(results_a)} A + {len(results_c)} C)")

    if not all_results:
        print("No trades.")
        sys.exit(1)

    report_dir = generate_iteration_reports(
        trades=all_results, iteration=ITERATION,
        features_dir="data/features", reports_dir="reports", interval="8h",
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
