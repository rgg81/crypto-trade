"""Iter 118: Meme model — wider ATR barriers (3.5x/1.75x, was 2.9x/1.45x).

Single variable change from iter 117. Wider barriers give meme coins more
room for wicks before stopping out, while maintaining 2:1 TP/SL ratio.
Uses iter 117's pruned 45-feature set.
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import EarlyStopError, run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 118
SYMBOLS = ("DOGEUSDT", "1000SHIBUSDT")

# 45 pruned features (same as iter 117)
PRUNED_FEATURES = [
    # Volume & Microstructure (8)
    "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_10",
    "vol_volume_pctchg_5",
    "vol_volume_pctchg_10",
    "vol_volume_rel_10",
    "vol_cmf_14",
    "vol_mfi_7",
    "vol_mfi_14",
    # Volatility (5)
    "vol_natr_14",
    "vol_bb_bandwidth_20",
    "vol_garman_klass_10",
    "vol_range_spike_12",
    "vol_range_spike_24",
    # Mean Reversion (5)
    "mr_zscore_20",
    "mr_zscore_50",
    "mr_bb_pctb_20",
    "mr_pct_from_high_20",
    "mr_pct_from_low_20",
    # Momentum (6)
    "mom_rsi_5",
    "mom_rsi_14",
    "mom_roc_5",
    "mom_roc_10",
    "mom_stoch_k_5",
    "stat_return_1",
    # Statistical (3)
    "stat_return_5",
    "stat_autocorr_lag1",
    "stat_skew_10",
    # Trend (2)
    "trend_adx_14",
    "trend_psar_dir",
    # Microstructure (9)
    "meme_body_ratio",
    "meme_upper_shadow",
    "meme_lower_shadow",
    "meme_vol_spike_3",
    "meme_vol_spike_10",
    "meme_taker_imbalance",
    "meme_range_position",
    "meme_consec_dir",
    "meme_indecision",
    # Meme Trend (5)
    "meme_cum_ret_10",
    "meme_cum_ret_30",
    "meme_new_high_20",
    "meme_range_pos_50",
    "meme_rsi_slope_5",
    # Cross-Asset (3)
    "xbtc_return_1",
    "xbtc_return_5",
    "xbtc_natr_14",
]


def main(seed: int = 42) -> None:
    print(f"Iter {ITERATION}: meme model, wider ATR barriers 3.5x/1.75x (was 2.9x/1.45x)")
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
        atr_tp_multiplier=3.5,   # was 2.9
        atr_sl_multiplier=1.75,  # was 1.45
        use_atr_labeling=True,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=PRUNED_FEATURES,
    )
    start = time.time()
    try:
        results = run_backtest(config, strategy, yearly_pnl_check=False)
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
