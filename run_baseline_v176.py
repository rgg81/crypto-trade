"""Baseline v0.176 — A + C(R1) + LTC(R1) + DOT(R1, R2).

Adds DOT as Model E with combined R1 (consecutive-SL cool-down) and R2
(drawdown-triggered position scaling). The R2 parameters are calibrated
on DOT's IS trade stream to reduce drawdown contribution while preserving
OOS Sharpe.

Expected metrics (from iter-176 post-hoc simulation, exact for per-symbol
R1+R2 since both operate on trade outputs within a single-symbol model):

    IS  Sharpe +1.338, MaxDD 45.57%, PnL +221%
    OOS Sharpe +1.414, MaxDD 27.20%, PnL +83.75%
"""

import sys
import time
from pathlib import Path

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.live.models import BASELINE_FEATURE_COLUMNS
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = 176


def run_model(
    name: str,
    symbols: tuple[str, ...],
    use_atr_labeling: bool,
    atr_tp: float,
    atr_sl: float,
    *,
    apply_r1: bool,
    apply_r2: bool = False,
):
    print("=" * 60)
    print(f"MODEL {name}: {', '.join(symbols)} (R1={apply_r1} R2={apply_r2})")
    print("=" * 60)
    config = BacktestConfig(
        symbols=symbols,
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
        # R1 (iter 173): cool-down after 3 consecutive SLs.
        risk_consecutive_sl_limit=3 if apply_r1 else None,
        risk_consecutive_sl_cooldown_candles=27 if apply_r1 else 0,
        # R2 (iter 175): drawdown-triggered position scaling.
        risk_drawdown_scale_enabled=apply_r2,
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
        atr_tp_multiplier=atr_tp,
        atr_sl_multiplier=atr_sl,
        use_atr_labeling=use_atr_labeling,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=list(BASELINE_FEATURE_COLUMNS),
    )
    t0 = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - t0
    print(f"\n{name} complete: {len(results)} trades in {elapsed:.0f}s")
    return results


def main() -> None:
    print(f"BASELINE v0.{ITERATION}: A + C(R1) + LTC(R1) + DOT(R1,R2)")
    print()

    results_a = run_model("A (BTC/ETH ATR)", ("BTCUSDT", "ETHUSDT"), True, 2.9, 1.45, apply_r1=False)
    results_c = run_model("C (LINK + R1)", ("LINKUSDT",), True, 3.5, 1.75, apply_r1=True)
    results_d = run_model("D (LTC + R1)", ("LTCUSDT",), True, 3.5, 1.75, apply_r1=True)
    results_e = run_model("E (DOT + R1 + R2)", ("DOTUSDT",), True, 3.5, 1.75, apply_r1=True, apply_r2=True)

    all_results = results_a + results_c + results_d + results_e
    all_results.sort(key=lambda t: t.close_time)
    print(
        f"\nCombined: {len(all_results)} trades "
        f"({len(results_a)} A + {len(results_c)} C + {len(results_d)} D + {len(results_e)} E)"
    )
    if not all_results:
        print("No trades.")
        sys.exit(1)

    report_dir = generate_iteration_reports(
        trades=all_results,
        iteration=ITERATION,
        features_dir="data/features",
        reports_dir="reports",
        interval="8h",
        n_trials=176,
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
