"""Iter 191: LINK standalone with 130 features (pruned from 193).

Tests whether LINK benefits from displacing 63 low-MDI features (multi-seed
averaged importance). Samples/feature ratio improves from 22 to 28.
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 191
SYMBOL = "LINKUSDT"

FEATURE_FILE = Path(__file__).parent / "analysis/iteration_191/keep_top_130.txt"
FEATURE_COLUMNS = FEATURE_FILE.read_text().strip().splitlines()
assert len(FEATURE_COLUMNS) == 130, f"Expected 130 features, got {len(FEATURE_COLUMNS)}"

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
    print(f"ITER {ITERATION} — {SYMBOL} with 130 pruned features")
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
        iteration=f"{ITERATION}_link_pruned",
        features_dir="data/features",
        reports_dir="reports",
        interval="8h",
        n_trials=ITERATION,
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
