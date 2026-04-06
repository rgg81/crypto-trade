"""Iter 112: DOGE+SHIB — trend features + 12-month training window.

Two changes from iter 111:
1. Add 8 trend-following features (breakout, cumulative momentum, RSI slope, HH/LL)
   to balance the mean-reversion bias that caused 2024 losses
2. Reduce training_months from 24 to 12 — faster regime adaptation
   (24mo trains on 2022 bear when predicting 2024 bull → regime mismatch)

62 total features. Ratio with 12mo: ~2200/62 = 35.5 (acceptable for exploration).
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import EarlyStopError, run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 112
SYMBOLS = ("DOGEUSDT", "1000SHIBUSDT")

# 42 base + 12 microstructure (iter 111) + 8 trend-following (new)
BASE_FEATURES = [
    "vol_taker_buy_ratio", "vol_taker_buy_ratio_sma_5", "vol_taker_buy_ratio_sma_10",
    "vol_volume_pctchg_3", "vol_volume_pctchg_5", "vol_volume_pctchg_10",
    "vol_volume_rel_5", "vol_volume_rel_10",
    "vol_cmf_10", "vol_cmf_14", "vol_mfi_7", "vol_mfi_14",
    "vol_natr_7", "vol_natr_14", "vol_natr_21",
    "vol_bb_bandwidth_10", "vol_bb_bandwidth_20",
    "vol_garman_klass_10", "vol_range_spike_12", "vol_range_spike_24",
    "mr_zscore_10", "mr_zscore_20", "mr_zscore_50",
    "mr_bb_pctb_10", "mr_bb_pctb_20",
    "mr_pct_from_high_5", "mr_pct_from_high_20", "mr_pct_from_low_20",
    "mom_rsi_5", "mom_rsi_14", "mom_roc_3", "mom_roc_5", "mom_roc_10",
    "mom_stoch_k_5", "mom_stoch_d_5", "stat_return_1",
    "stat_return_3", "stat_return_5", "stat_autocorr_lag1", "stat_skew_10",
    "trend_adx_14", "trend_psar_dir",
]

MICROSTRUCTURE_FEATURES = [
    "meme_body_ratio", "meme_upper_shadow", "meme_lower_shadow",
    "meme_vol_spike_3", "meme_vol_spike_10", "meme_taker_imbalance",
    "meme_range_position", "meme_consec_dir", "meme_vol_body",
    "meme_indecision", "meme_body_expansion", "meme_taker_accel",
]

TREND_FEATURES = [
    "meme_cum_ret_10",    # 3.3-day cumulative return
    "meme_cum_ret_30",    # 10-day cumulative return
    "meme_new_high_20",   # breakout: at 20-period high
    "meme_new_low_20",    # breakdown: at 20-period low
    "meme_range_pos_50",  # position in 50-candle range
    "meme_rsi_slope_5",   # RSI momentum acceleration
    "meme_hh_ll_5",       # higher highs / lower lows structure
    "meme_vol_trend",     # volume increasing with trend
]

ALL_FEATURES = BASE_FEATURES + MICROSTRUCTURE_FEATURES + TREND_FEATURES


def main(seed: int = 42) -> None:
    print(f"Iter 112b: DOGE+SHIB, 62 feat, 24mo window, trend features")
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
        training_months=24,  # CHANGED: 12 months (was 24)
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
        feature_columns=ALL_FEATURES,
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
