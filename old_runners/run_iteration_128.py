"""Iter 128: MILESTONE — Three-model portfolio A+B+C.

Model A: BTC/ETH (iter 093 baseline config)
Model B: DOGE/SHIB (iter 118 meme config)
Model C: LINK (iter 126 config — ATR labeling, auto-discovery)
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 128

MEME_FEATURES = [
    "vol_taker_buy_ratio", "vol_taker_buy_ratio_sma_10", "vol_volume_pctchg_5",
    "vol_volume_pctchg_10", "vol_volume_rel_10", "vol_cmf_14", "vol_mfi_7", "vol_mfi_14",
    "vol_natr_14", "vol_bb_bandwidth_20", "vol_garman_klass_10", "vol_range_spike_12",
    "vol_range_spike_24", "mr_zscore_20", "mr_zscore_50", "mr_bb_pctb_20",
    "mr_pct_from_high_20", "mr_pct_from_low_20", "mom_rsi_5", "mom_rsi_14",
    "mom_roc_5", "mom_roc_10", "mom_stoch_k_5", "stat_return_1", "stat_return_5",
    "stat_autocorr_lag1", "stat_skew_10", "trend_adx_14", "trend_psar_dir",
    "meme_body_ratio", "meme_upper_shadow", "meme_lower_shadow", "meme_vol_spike_3",
    "meme_vol_spike_10", "meme_taker_imbalance", "meme_range_position", "meme_consec_dir",
    "meme_indecision", "meme_cum_ret_10", "meme_cum_ret_30", "meme_new_high_20",
    "meme_range_pos_50", "meme_rsi_slope_5", "xbtc_return_1", "xbtc_return_5", "xbtc_natr_14",
]


def run_model(name, symbols, feature_columns, use_atr_labeling, atr_tp, atr_sl):
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
        use_atr_labeling=use_atr_labeling,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=feature_columns,
    )
    start = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - start
    print(f"\n{name} complete: {len(results)} trades in {elapsed:.0f}s")
    return results


def main() -> None:
    print(f"Iter {ITERATION}: THREE-MODEL PORTFOLIO — A(BTC/ETH) + B(DOGE/SHIB) + C(LINK)")
    print()

    results_a = run_model("A (BTC/ETH)", ("BTCUSDT", "ETHUSDT"),
                          None, False, 2.9, 1.45)
    results_b = run_model("B (DOGE/SHIB)", ("DOGEUSDT", "1000SHIBUSDT"),
                          MEME_FEATURES, True, 3.5, 1.75)
    results_c = run_model("C (LINK)", ("LINKUSDT",),
                          None, True, 3.5, 1.75)

    all_results = results_a + results_b + results_c
    all_results.sort(key=lambda t: t.close_time)
    print(f"\nCombined: {len(all_results)} trades "
          f"({len(results_a)} A + {len(results_b)} B + {len(results_c)} C)")

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
