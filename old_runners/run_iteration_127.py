"""Iter 127: LINK with pruned features (45 curated, meme model architecture).

Iter 126 showed LINK has signal (IS +0.45, OOS +1.20) with 185 features.
Feature pruning to ~45 should strengthen signal (meme: OOS doubled after pruning).
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 127

LINK_FEATURES = [
    # Volume & Microstructure (8)
    "vol_taker_buy_ratio", "vol_taker_buy_ratio_sma_10", "vol_volume_pctchg_5",
    "vol_volume_pctchg_10", "vol_volume_rel_10", "vol_cmf_14", "vol_mfi_7", "vol_mfi_14",
    # Volatility (5)
    "vol_natr_14", "vol_bb_bandwidth_20", "vol_garman_klass_10",
    "vol_range_spike_12", "vol_range_spike_24",
    # Mean Reversion (5)
    "mr_zscore_20", "mr_zscore_50", "mr_bb_pctb_20",
    "mr_pct_from_high_20", "mr_pct_from_low_20",
    # Momentum (6)
    "mom_rsi_5", "mom_rsi_14", "mom_roc_5", "mom_roc_10",
    "mom_stoch_k_5", "stat_return_1",
    # Statistical (3)
    "stat_return_5", "stat_autocorr_lag1", "stat_skew_10",
    # Trend (2)
    "trend_adx_14", "trend_psar_dir",
    # Additional momentum (4)
    "mom_stoch_d_5", "mom_macd_hist_8_21_5", "mom_roc_20", "mom_rsi_21",
    # Additional volatility (3)
    "vol_natr_21", "vol_natr_7", "vol_bb_bandwidth_30",
    # Additional mean reversion (3)
    "mr_zscore_100", "mr_pct_from_high_50", "mr_pct_from_low_50",
    # Additional trend (3)
    "trend_aroon_osc_14", "trend_adx_21", "trend_aroon_osc_25",
    # Additional statistical (3)
    "stat_return_10", "stat_log_return_5", "stat_kurtosis_20",
]

assert len(LINK_FEATURES) == 45, f"Expected 45, got {len(LINK_FEATURES)}"


def main() -> None:
    print(f"Iter {ITERATION}: LINK with 45 pruned features")
    config = BacktestConfig(
        symbols=("LINKUSDT",),
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
        seed=42,
        verbose=1,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        use_atr_labeling=True,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=LINK_FEATURES,
    )
    start = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - start
    print(f"\nLINK pruned model complete: {len(results)} trades in {elapsed:.0f}s")
    if not results:
        print("No trades.")
        sys.exit(1)
    report_dir = generate_iteration_reports(
        trades=results, iteration=ITERATION, features_dir="data/features",
        reports_dir="reports", interval="8h",
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
