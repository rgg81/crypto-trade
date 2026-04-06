"""Iter 119: Combined portfolio — BTC/ETH (iter 093 baseline) + DOGE/SHIB (iter 118 meme).

Two independent LightGBM models running side-by-side. Trades concatenated
for combined portfolio reporting. Tests whether combined Sharpe beats +1.01.
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 119

# Iter 118's 45 pruned meme features
MEME_FEATURES = [
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


def run_model_a():
    """Model A: BTC+ETH baseline (iter 093 config)."""
    print("=" * 60)
    print("MODEL A: BTC+ETH (iter 093 baseline config)")
    print("=" * 60)
    config = BacktestConfig(
        symbols=("BTCUSDT", "ETHUSDT"),
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
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        use_atr_labeling=False,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=None,  # auto-discovery (185 features)
    )
    start = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - start
    print(f"\nModel A complete: {len(results)} trades in {elapsed:.0f}s")
    return results


def run_model_b():
    """Model B: DOGE+SHIB meme (iter 118 config)."""
    print("=" * 60)
    print("MODEL B: DOGE+SHIB (iter 118 meme config)")
    print("=" * 60)
    config = BacktestConfig(
        symbols=("DOGEUSDT", "1000SHIBUSDT"),
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
        feature_columns=MEME_FEATURES,
    )
    start = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - start
    print(f"\nModel B complete: {len(results)} trades in {elapsed:.0f}s")
    return results


def main() -> None:
    print(f"Iter {ITERATION}: Combined portfolio — BTC/ETH + DOGE/SHIB")
    print()

    # Run both models sequentially
    results_a = run_model_a()
    results_b = run_model_b()

    # Combine trades
    all_results = results_a + results_b
    all_results.sort(key=lambda t: t.close_time)
    print(f"\nCombined: {len(all_results)} trades ({len(results_a)} BTC/ETH + {len(results_b)} DOGE/SHIB)")

    if not all_results:
        print("No trades.")
        sys.exit(1)

    report_dir = generate_iteration_reports(
        trades=all_results,
        iteration=ITERATION,
        features_dir="data/features",
        reports_dir="reports",
        interval="8h",
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
