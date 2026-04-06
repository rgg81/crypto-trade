"""Iter 084: Aggressive feature pruning — 198→49 features.

Tests whether pruning from 198 (symbol-scoped) to 49 features improves
model stability and OOS generalization. All other config identical to
baseline iter 068.

Key change: feature_columns restricts the model to 49 pruned features
selected by importance + correlation dedup + stability analysis.
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import EarlyStopError, run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 84
SYMBOLS = ("BTCUSDT", "ETHUSDT")

# 49 features selected by A1 pruning protocol:
# - Started with 198 (symbol-scoped discovery for BTC+ETH)
# - Correlation dedup (|Spearman| > 0.90) removed 82
# - Top 50 by gain importance (82.9% of total)
# - 1 unstable feature removed (vol_taker_buy_ratio_sma_20)
PRUNED_FEATURES = [
    "vol_taker_buy_ratio_sma_50",
    "vol_vwap",
    "vol_ad",
    "mr_dist_vwap",
    "vol_obv",
    "trend_adx_21",
    "stat_autocorr_lag10",
    "stat_autocorr_lag1",
    "stat_autocorr_lag5",
    "mr_pct_from_low_100",
    "xbtc_natr_21",
    "xbtc_adx_14",
    "trend_sma_cross_20_100",
    "stat_kurtosis_20",
    "stat_skew_50",
    "stat_skew_30",
    "vol_garman_klass_50",
    "trend_sma_cross_20_50",
    "stat_skew_20",
    "stat_kurtosis_30",
    "vol_hist_30",
    "mr_pct_from_high_100",
    "stat_kurtosis_50",
    "mr_zscore_100",
    "trend_aroon_up_50",
    "trend_aroon_osc_50",
    "stat_skew_10",
    "mom_macd_signal_12_26_9",
    "vol_mfi_10",
    "trend_plus_di_21",
    "trend_aroon_osc_25",
    "mr_pct_from_high_50",
    "vol_garman_klass_10",
    "vol_cmf_10",
    "vol_cmf_20",
    "mom_roc_30",
    "mr_pct_from_low_50",
    "vol_mfi_7",
    "trend_adx_14",
    "interact_natr_x_adx",
    "vol_mfi_14",
    "vol_cmf_14",
    "trend_aroon_down_50",
    "vol_atr_21",
    "vol_bb_bandwidth_20",
    "vol_bb_bandwidth_30",
    "stat_kurtosis_10",
    "mr_pct_from_low_20",
    "trend_aroon_osc_14",
]


def main(seed: int = 42) -> None:
    print(f"Iter 084: feature pruning 198→{len(PRUNED_FEATURES)} features")
    config = BacktestConfig(
        symbols=SYMBOLS,
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
        data_dir=Path("data"),
        cooldown_candles=2,
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
        seed=seed,
        verbose=1,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        ensemble_seeds=[42, 123, 789],
        feature_columns=PRUNED_FEATURES,
        trading_symbols=list(SYMBOLS),
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
        print("No trades.")
        sys.exit(1)
    report_dir = generate_iteration_reports(
        trades=results,
        iteration=ITERATION,
        features_dir="data/features",
        reports_dir="reports",
        interval="8h",
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
