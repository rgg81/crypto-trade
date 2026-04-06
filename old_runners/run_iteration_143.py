"""Iter 143: A+C+D+E portfolio — BTC/ETH + LINK + BNB + DOGE.

Model A: BTC/ETH with ATR labeling 2.9x/1.45x (iter 138 config)
Model C: LINK with ATR labeling 3.5x/1.75x (iter 126 config)
Model D: BNB with ATR labeling 3.5x/1.75x (iter 132 config)
Model E: DOGE with ATR labeling 3.5x/1.75x (iter 142 screening PASS)
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 143


def run_model(name, symbols, atr_tp, atr_sl):
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
        use_atr_labeling=True,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=None,
    )
    start = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - start
    print(f"\n{name} complete: {len(results)} trades in {elapsed:.0f}s")
    return results


def main() -> None:
    print(f"Iter {ITERATION}: A+C+D+E PORTFOLIO — BTC/ETH + LINK + BNB + DOGE")
    print()

    results_a = run_model("A (BTC/ETH ATR)", ("BTCUSDT", "ETHUSDT"), 2.9, 1.45)
    results_c = run_model("C (LINK)", ("LINKUSDT",), 3.5, 1.75)
    results_d = run_model("D (BNB)", ("BNBUSDT",), 3.5, 1.75)
    results_e = run_model("E (DOGE)", ("DOGEUSDT",), 3.5, 1.75)

    all_results = results_a + results_c + results_d + results_e
    all_results.sort(key=lambda t: t.close_time)
    print(f"\nCombined: {len(all_results)} trades "
          f"({len(results_a)} A + {len(results_c)} C + {len(results_d)} D + {len(results_e)} E)")

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
