"""Baseline v0.152: A+C+D portfolio with engine-integrated vol targeting.

Canonical reproduction script for the production baseline. Runs the same
3-model portfolio as iter 138 (Model A: BTC/ETH, Model C: LINK, Model D:
BNB) with the iter 152 VT parameters baked into BacktestConfig.

Expected metrics (from BASELINE.md):
  OOS Sharpe: +2.83, MaxDD: 21.81%, WR: 50.6%, PF: 1.76, Trades: 164
  IS  Sharpe: +1.33, MaxDD: 76.89%, WR: 44.5%, PF: 1.33, Trades: 652

VT config (iter 152):
  target_vol=0.3, lookback_days=45, min_scale=0.33, max_scale=2.0

Usage:
  uv run python run_baseline_v152.py
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.live.models import BASELINE_FEATURE_COLUMNS
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 152


def run_model(name, symbols, use_atr_labeling, atr_tp, atr_sl):
    print("=" * 60)
    print(f"MODEL {name}: {', '.join(symbols)}")
    print("=" * 60)
    config = BacktestConfig(
        symbols=symbols,
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
        data_dir=Path("data"),
        cooldown_candles=2,
        # Vol targeting (iter 152 production config)
        vol_targeting=True,
        vt_target_vol=0.3,
        vt_lookback_days=45,
        vt_min_scale=0.33,
        vt_max_scale=2.0,
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
        verbose=1,
        atr_tp_multiplier=atr_tp,
        atr_sl_multiplier=atr_sl,
        use_atr_labeling=use_atr_labeling,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=list(BASELINE_FEATURE_COLUMNS),
    )
    start = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - start
    print(f"\n{name} complete: {len(results)} trades in {elapsed:.0f}s")
    return results


def main() -> None:
    print(f"BASELINE v0.{ITERATION}: A+C+D portfolio with VT")
    print()

    # Model A: BTC/ETH with ATR labeling (iter 137 config)
    results_a = run_model("A (BTC/ETH ATR)", ("BTCUSDT", "ETHUSDT"), True, 2.9, 1.45)
    # Model C: LINK (iter 126 config)
    results_c = run_model("C (LINK)", ("LINKUSDT",), True, 3.5, 1.75)
    # Model D: BNB (iter 132 config)
    results_d = run_model("D (BNB)", ("BNBUSDT",), True, 3.5, 1.75)

    all_results = results_a + results_c + results_d
    all_results.sort(key=lambda t: t.close_time)
    print(
        f"\nCombined: {len(all_results)} trades "
        f"({len(results_a)} A + {len(results_c)} C + {len(results_d)} D)"
    )

    if not all_results:
        print("No trades.")
        sys.exit(1)

    report_dir = generate_iteration_reports(
        trades=all_results,
        iteration=ITERATION,
        features_dir="data/features",
        reports_dir="reports",
        interval="8h",
        n_trials=163,
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
