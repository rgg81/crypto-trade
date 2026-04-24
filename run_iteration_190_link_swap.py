"""Iter 190: LINK standalone with feature REPLACEMENT (not augmentation).

Swap the 7 lowest-MDI baseline features for 7 xbtc features. Net feature
count stays at 193, so samples/feature ratio unchanged. Tests whether
xbtc features carry signal when not piled on top of the existing set.
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.live.models import BASELINE_FEATURE_COLUMNS, XBTC_FEATURE_COLUMNS
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 190
SYMBOL = "LINKUSDT"

# 7 lowest-MDI baseline features on LINK IS training data (from
# analysis/iteration_190/feature_importance.py). All had MDI = 0 — never
# used by LightGBM for splits, so safe to drop.
DROP_FEATURES = [
    "cal_hour_norm",
    "mom_rsi_7",
    "mr_rsi_extreme_21",
    "mr_rsi_extreme_14",
    "mr_dist_sma_10",
    "stat_return_1",
    "stat_log_return_10",
]

# Note: stat_return_1, mr_rsi_extreme_14, mr_rsi_extreme_21 are still used by
# R3 (Mahalanobis OOD). Dropping them from prediction features doesn't remove
# them from ood_features — they live in the parquet either way.

FEATURE_COLUMNS = [
    *[c for c in BASELINE_FEATURE_COLUMNS if c not in DROP_FEATURES],
    *XBTC_FEATURE_COLUMNS,
]
assert len(FEATURE_COLUMNS) == len(BASELINE_FEATURE_COLUMNS), (
    f"feature count mismatch: {len(FEATURE_COLUMNS)} vs {len(BASELINE_FEATURE_COLUMNS)}"
)

OOD_FEATURES = [
    "stat_return_1", "stat_return_2", "stat_return_5", "stat_return_10",
    "mr_rsi_extreme_7", "mr_rsi_extreme_14", "mr_rsi_extreme_21",
    "mr_bb_pctb_10", "mr_bb_pctb_20",
    "mom_stoch_k_5", "mom_stoch_k_9",
    "vol_atr_5", "vol_atr_7",
    "vol_bb_bandwidth_10",
    "vol_volume_pctchg_5", "vol_volume_pctchg_10",
]


def main() -> None:
    print("=" * 60)
    print(f"ITER {ITERATION} — {SYMBOL} with 7 xbtc features (swap, not add)")
    print(f"  dropped: {DROP_FEATURES}")
    print(f"  added:   {list(XBTC_FEATURE_COLUMNS)}")
    print(f"  total features: {len(FEATURE_COLUMNS)}")
    print("=" * 60)
    config = BacktestConfig(
        symbols=(SYMBOL,),
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
        data_dir=Path("data"),
        cooldown_candles=2,
        vol_targeting=True,
        vt_target_vol=0.3,
        vt_lookback_days=45,
        vt_min_scale=0.33,
        vt_max_scale=2.0,
        risk_consecutive_sl_limit=3,
        risk_consecutive_sl_cooldown_candles=27,
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
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        use_atr_labeling=True,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=FEATURE_COLUMNS,
        ood_enabled=True,
        ood_features=OOD_FEATURES,
        ood_cutoff_pct=0.70,
    )
    t0 = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - t0
    print(f"\n{SYMBOL} complete: {len(results)} trades in {elapsed:.0f}s")
    if not results:
        sys.exit(1)
    results.sort(key=lambda t: t.close_time)
    report_dir = generate_iteration_reports(
        trades=results,
        iteration=f"{ITERATION}_link_swap",
        features_dir="data/features",
        reports_dir="reports",
        interval="8h",
        n_trials=ITERATION,
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
