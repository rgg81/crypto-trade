"""Battle-test v1 baseline reproduction.

Runs v1 iter-152 with EXACTLY the same configuration as BASELINE.md but
with `feature_columns` pinned to the 196 core features (excluding the
11 entropy/CUSUM features added in iter-162 after the baseline was set).

This should reproduce BASELINE.md's +2.83 OOS Sharpe on the Feb 2026
window, and extend cleanly to the latest OOS data (Apr 2026).

Config mirror of run_baseline_v152.py:
- 3 models: A (BTC+ETH), C (LINK), D (BNB)
- max_amount_usd=1000, fee_pct=0.1, cooldown_candles=2
- Vol targeting: target=0.3, lookback=45d, min_scale=0.33, max_scale=2.0
- LightGBM: training=24mo, n_trials=50, cv_splits=5, timeout=10080min
- ATR labeling: A=2.9/1.45, C=3.5/1.75, D=3.5/1.75
- 5-seed ensemble: [42, 123, 456, 789, 1001]

Difference from run_baseline_v152.py:
- `feature_columns` is EXPLICITLY set to the 196 core v1 features
  (no entropy/CUSUM). v152 auto-discovers which picks up all 207
  features including the iter-162 additions.

Output: reports/iteration_152_core/ (doesn't clobber iter-152 run).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pyarrow.parquet as pq

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

ITERATION = "152_core"

# Build the 196 core feature set from the BTCUSDT parquet (all 4 v1 symbols
# now have identical feature schemas).
_META = {
    "open_time",
    "close_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "num_trades",
    "taker_buy_base",
    "taker_buy_quote",
    "quote_volume",
    "ignore",
}


def _load_core_features() -> list[str]:
    schema = pq.read_schema("data/features/BTCUSDT_8h_features.parquet").names
    feats = [c for c in schema if c not in _META and not c.startswith("__")]
    # Exclude the 11 entropy/CUSUM features (iter-162 additions).
    core = [c for c in feats if not (c.startswith("ent_") or c.startswith("cusum_"))]
    if len(core) != 196:
        raise RuntimeError(
            f"Expected 196 core features for BASELINE reproduction, got {len(core)}"
        )
    return core


V1_CORE_FEATURES = _load_core_features()


def run_model(name: str, symbols: tuple[str, ...], atr_tp: float, atr_sl: float) -> list:
    print("=" * 60)
    print(f"MODEL {name}: {', '.join(symbols)}")
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
        atr_tp_multiplier=atr_tp,
        atr_sl_multiplier=atr_sl,
        use_atr_labeling=True,
        ensemble_seeds=[42, 123, 456, 789, 1001],
        feature_columns=V1_CORE_FEATURES,  # ← the critical change
    )
    start = time.time()
    results = run_backtest(config, strategy, yearly_pnl_check=False)
    elapsed = time.time() - start
    print(f"\n{name} complete: {len(results)} trades in {elapsed:.0f}s")
    return results


def main() -> None:
    print(f"Iter {ITERATION}: v1 baseline reproduction with EXPLICIT 196 core features")
    print("  Excluding: entropy/CUSUM features (iter-162 additions)")
    print(f"  Feature count pinned at: {len(V1_CORE_FEATURES)}")
    print()

    results_a = run_model("A (BTC/ETH ATR)", ("BTCUSDT", "ETHUSDT"), 2.9, 1.45)
    results_c = run_model("C (LINK)", ("LINKUSDT",), 3.5, 1.75)
    results_d = run_model("D (BNB)", ("BNBUSDT",), 3.5, 1.75)

    all_results = results_a + results_c + results_d
    all_results.sort(key=lambda t: t.close_time)
    print(
        f"\nCombined: {len(all_results)} trades "
        f"({len(results_a)} A + {len(results_c)} C + {len(results_d)} D)"
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
        n_trials=163,
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
