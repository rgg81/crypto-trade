"""Iter 178: re-screen AAVE with R1+R2 active from the start.

AAVE was rejected in iter 164 (year-1 fail-fast, 2022 PnL -34.6%).
That iteration used no risk mitigations. With R1 (K=3 C=27) and R2
(t=7/a=15/f=0.33), AAVE may now survive year-1. Same Gate 3 protocol.
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import EarlyStopError, run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.live.models import BASELINE_FEATURE_COLUMNS
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 178
SYMBOL = "AAVEUSDT"


def main() -> None:
    print("=" * 60)
    print(f"ITER 178 — {SYMBOL} with R1+R2 active")
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
        risk_drawdown_scale_enabled=True,
        risk_drawdown_trigger_pct=7.0,
        risk_drawdown_scale_floor=0.33,
        risk_drawdown_scale_anchor_pct=15.0,
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
        feature_columns=list(BASELINE_FEATURE_COLUMNS),
    )
    t0 = time.time()
    try:
        results = run_backtest(config, strategy, yearly_pnl_check=True)
    except EarlyStopError as e:
        elapsed = time.time() - t0
        print(f"\n*** EARLY STOP ({elapsed:.0f}s) *** {e.reason}")
        results = e.results
        if not results:
            sys.exit(1)
    else:
        elapsed = time.time() - t0
        print(f"\n{SYMBOL} complete: {len(results)} trades in {elapsed:.0f}s")
    if not results:
        sys.exit(1)
    results.sort(key=lambda t: t.close_time)
    report_dir = generate_iteration_reports(
        trades=results,
        iteration=f"178_{SYMBOL.replace('USDT','').lower()}",
        features_dir="data/features",
        reports_dir="reports",
        interval="8h",
        n_trials=178,
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
