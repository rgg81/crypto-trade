"""Iter 163: Full retrain with entropy + CUSUM features (iter 162 addition).

Same A+C+D portfolio config as iter 138, but parquets now include 11 new
entropy/CUSUM features. LightGBM's _discover_feature_columns() will
automatically pick up ent_* and cusum_* columns from the regenerated
parquets.

VT is applied at report generation via n_trials for DSR reporting.
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 163


def run_model(name, symbols, use_atr_labeling, atr_tp, atr_sl):
    print("=" * 60)
    print(f"MODEL {name}: {', '.join(symbols)}")
    print("=" * 60)
    config = BacktestConfig(
        symbols=symbols, interval="8h", max_amount_usd=1000.0,
        stop_loss_pct=4.0, take_profit_pct=8.0, timeout_minutes=10080,
        fee_pct=0.1, data_dir=Path("data"), cooldown_candles=2,
        # VT integrated in engine (iter 150):
        vol_targeting=True,
        vt_target_vol=0.3, vt_lookback_days=45,
        vt_min_scale=0.33, vt_max_scale=2.0,
    )
    strategy = LightGbmStrategy(
        training_months=24, n_trials=50, cv_splits=5,
        label_tp_pct=8.0, label_sl_pct=4.0, label_timeout_minutes=10080,
        fee_pct=0.1, features_dir="data/features", seed=42, verbose=1,
        atr_tp_multiplier=atr_tp, atr_sl_multiplier=atr_sl,
        use_atr_labeling=use_atr_labeling,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=None,  # auto-discover (will include ent_/cusum_)
    )
    start = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - start
    print(f"\n{name} complete: {len(results)} trades in {elapsed:.0f}s")
    return results


def main() -> None:
    print(f"Iter {ITERATION}: A+C+D with entropy/CUSUM features")
    print()

    # Model A: BTC/ETH with ATR LABELING (same as iter 138)
    results_a = run_model("A (BTC/ETH ATR)", ("BTCUSDT", "ETHUSDT"), True, 2.9, 1.45)
    # Model C: LINK (same as iter 138)
    results_c = run_model("C (LINK)", ("LINKUSDT",), True, 3.5, 1.75)
    # Model D: BNB (same as iter 138)
    results_d = run_model("D (BNB)", ("BNBUSDT",), True, 3.5, 1.75)

    all_results = results_a + results_c + results_d
    all_results.sort(key=lambda t: t.close_time)
    print(f"\nCombined: {len(all_results)} trades "
          f"({len(results_a)} A + {len(results_c)} C + {len(results_d)} D)")

    if not all_results:
        print("No trades.")
        sys.exit(1)

    report_dir = generate_iteration_reports(
        trades=all_results, iteration=ITERATION,
        features_dir="data/features", reports_dir="reports", interval="8h",
        n_trials=163,  # DSR with full iteration count
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
