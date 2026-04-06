"""Iter 109: DOGE-only model — remove SHIB drag from iter 108.

Single variable change: SYMBOLS = ("DOGEUSDT",) instead of ("DOGEUSDT", "1000SHIBUSDT").
Everything else identical to iter 108: 42 curated features, dynamic ATR labeling.
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import EarlyStopError, run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 109
SYMBOLS = ("DOGEUSDT",)

# Same 42 curated features from iter 108
MEME_FEATURES = [
    # Volume & Microstructure (12)
    "vol_taker_buy_ratio", "vol_taker_buy_ratio_sma_5", "vol_taker_buy_ratio_sma_10",
    "vol_volume_pctchg_3", "vol_volume_pctchg_5", "vol_volume_pctchg_10",
    "vol_volume_rel_5", "vol_volume_rel_10",
    "vol_cmf_10", "vol_cmf_14", "vol_mfi_7", "vol_mfi_14",
    # Volatility Regime (8)
    "vol_natr_7", "vol_natr_14", "vol_natr_21",
    "vol_bb_bandwidth_10", "vol_bb_bandwidth_20",
    "vol_garman_klass_10", "vol_range_spike_12", "vol_range_spike_24",
    # Mean Reversion (8)
    "mr_zscore_10", "mr_zscore_20", "mr_zscore_50",
    "mr_bb_pctb_10", "mr_bb_pctb_20",
    "mr_pct_from_high_5", "mr_pct_from_high_20", "mr_pct_from_low_20",
    # Momentum (8)
    "mom_rsi_5", "mom_rsi_14", "mom_roc_3", "mom_roc_5", "mom_roc_10",
    "mom_stoch_k_5", "mom_stoch_d_5", "stat_return_1",
    # Statistical (4)
    "stat_return_3", "stat_return_5", "stat_autocorr_lag1", "stat_skew_10",
    # Trend (2)
    "trend_adx_14", "trend_psar_dir",
]


def main(seed: int = 42) -> None:
    print(f"Iter {ITERATION}: DOGE-only, {len(MEME_FEATURES)} curated features")
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
        use_atr_labeling=True,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=MEME_FEATURES,
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
