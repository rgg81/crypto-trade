"""Iter 095: Conservative pruning 185→145 + Sharpe overflow fix.

EXPLORATION iteration. Conservative approach after iter 094's aggressive
pruning (185→50) destroyed signal.

Changes from baseline (iter 093):
1. Remove 37 near-perfect duplicates (|Spearman r| >= 0.99)
2. Remove 3 harmful features (MDA < -0.01)
3. Fix Sharpe overflow in compute_sharpe_with_threshold (|Sharpe|>100 → -10)
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import EarlyStopError, run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 95
SYMBOLS = ("BTCUSDT", "ETHUSDT")

# 145 features: 185 baseline - 37 near-perfect duplicates - 3 harmful
FEATURE_COLUMNS = [
    "mom_macd_hist_12_26_9",
    "mom_macd_hist_5_13_3",
    "mom_macd_hist_8_21_5",
    "mom_macd_line_12_26_9",
    "mom_macd_line_5_13_3",
    "mom_macd_line_8_21_5",
    "mom_macd_signal_12_26_9",
    "mom_macd_signal_5_13_3",
    "mom_macd_signal_8_21_5",
    "mom_mom_10",
    "mom_mom_15",
    "mom_mom_20",
    "mom_mom_5",
    "mom_roc_10",
    "mom_roc_30",
    "mom_roc_5",
    "mom_rsi_14",
    "mom_rsi_21",
    "mom_rsi_30",
    "mom_rsi_5",
    "mom_rsi_9",
    "mom_stoch_d_14",
    "mom_stoch_d_21",
    "mom_stoch_d_5",
    "mom_stoch_d_9",
    "mom_stoch_k_14",
    "mom_stoch_k_21",
    "mom_stoch_k_5",
    "mom_stoch_k_9",
    "mom_willr_14",
    "mom_willr_21",
    "mom_willr_7",
    "mr_bb_pctb_20",
    "mr_bb_pctb_30",
    "mr_dist_sma_10",
    "mr_dist_sma_20",
    "mr_dist_sma_50",
    "mr_dist_vwap",
    "mr_pct_from_high_10",
    "mr_pct_from_high_100",
    "mr_pct_from_high_20",
    "mr_pct_from_high_5",
    "mr_pct_from_high_50",
    "mr_pct_from_low_10",
    "mr_pct_from_low_100",
    "mr_pct_from_low_20",
    "mr_pct_from_low_5",
    "mr_pct_from_low_50",
    "mr_rsi_extreme_14",
    "mr_rsi_extreme_21",
    "mr_rsi_extreme_7",
    "mr_zscore_100",
    "mr_zscore_50",
    "stat_autocorr_lag1",
    "stat_autocorr_lag10",
    "stat_autocorr_lag5",
    "stat_kurtosis_10",
    "stat_kurtosis_20",
    "stat_kurtosis_30",
    "stat_kurtosis_50",
    "stat_log_return_20",
    "stat_log_return_3",
    "stat_return_1",
    "stat_return_15",
    "stat_return_2",
    "stat_skew_10",
    "stat_skew_20",
    "stat_skew_30",
    "stat_skew_50",
    "trend_adx_14",
    "trend_adx_21",
    "trend_adx_7",
    "trend_aroon_down_14",
    "trend_aroon_down_25",
    "trend_aroon_down_50",
    "trend_aroon_osc_14",
    "trend_aroon_osc_25",
    "trend_aroon_up_14",
    "trend_aroon_up_25",
    "trend_aroon_up_50",
    "trend_ema_5",
    "trend_ema_cross_12_50",
    "trend_ema_cross_5_12",
    "trend_ema_cross_9_21",
    "trend_minus_di_14",
    "trend_minus_di_21",
    "trend_minus_di_7",
    "trend_plus_di_14",
    "trend_plus_di_21",
    "trend_plus_di_7",
    "trend_psar_af",
    "trend_psar_dir",
    "trend_sma_cross_10_50",
    "trend_sma_cross_20_50",
    "trend_supertrend_10_2",
    "trend_supertrend_14_3",
    "trend_supertrend_7_3",
    "vol_ad",
    "vol_atr_21",
    "vol_bb_bandwidth_10",
    "vol_bb_bandwidth_15",
    "vol_bb_bandwidth_20",
    "vol_bb_pctb_10",
    "vol_bb_pctb_15",
    "vol_cmf_10",
    "vol_cmf_14",
    "vol_cmf_20",
    "vol_garman_klass_20",
    "vol_garman_klass_50",
    "vol_hist_10",
    "vol_hist_20",
    "vol_hist_30",
    "vol_hist_5",
    "vol_hist_50",
    "vol_mfi_10",
    "vol_mfi_14",
    "vol_mfi_21",
    "vol_mfi_7",
    "vol_natr_21",
    "vol_natr_7",
    "vol_obv",
    "vol_parkinson_10",
    "vol_parkinson_30",
    "vol_range_spike_12",
    "vol_range_spike_24",
    "vol_range_spike_36",
    "vol_range_spike_48",
    "vol_range_spike_72",
    "vol_range_spike_96",
    "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_10",
    "vol_taker_buy_ratio_sma_20",
    "vol_taker_buy_ratio_sma_5",
    "vol_taker_buy_ratio_sma_50",
    "vol_volume_pctchg_10",
    "vol_volume_pctchg_15",
    "vol_volume_pctchg_20",
    "vol_volume_pctchg_3",
    "vol_volume_pctchg_30",
    "vol_volume_pctchg_5",
    "vol_volume_rel_10",
    "vol_volume_rel_20",
    "vol_volume_rel_5",
    "vol_volume_rel_50",
    "vol_vwap",
]


def main(seed: int = 42) -> None:
    print(f"Iter {ITERATION}: Conservative pruning (185→{len(FEATURE_COLUMNS)}) + Sharpe overflow fix")
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
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=FEATURE_COLUMNS,
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
