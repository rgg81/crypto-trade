"""iter-v1/085 GATE 2 PRIMARY — fast single-seed LightGBM probe for GRTUSDT.

Structure gate check: IS Sharpe >= +0.30 required for the coin to advance.

Methodology (IS-only, single seed=42, n_trials=10):
  - Uses V1_FEATURE_COLUMNS_PRUNED (48 cols) — NO new features (probes BASELINE structure).
  - Walk-forward on the IS window (open_time < OOS_CUTOFF_MS = 2025-03-24).
  - atr_tp=2.9, atr_sl=1.45 (matching /084 CRV cell; standard Model A vol-class config).
  - training_months=24 (SACRED CONSTANT — never changed).
  - n_trials=10, single seed=42 (fast probe budget).
  - specialist_mode=False (probe only; full 50-seed specialist fires only after gate passes).
  - IS Sharpe extracted from run_backtest results (monthly annualized).

GATE 2 PRIMARY: probe_is_sharpe >= +0.30 → gate2_pass = True.

IS-ONLY DISCIPLINE: BacktestConfig.end_time set to OOS_CUTOFF_MS so no OOS data leaks.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import math

import numpy as np

# Ensure we run from the worktree root
_WD = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_WD / "src"))

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.backtest_report import to_daily_returns_series
from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

SYMBOL = "GRTUSDT"
SEED = 42
N_TRIALS = 10
TRAINING_MONTHS = 24  # SACRED CONSTANT

# atr_tp=2.9, atr_sl=1.45 matches Model A ETH cell (vol-class match for GRT ~mid-vol)
ATR_TP = 2.9
ATR_SL = 1.45

OUTPUT_PATH = Path(__file__).parent / "probe_GRTUSDT_result.json"

# Sanity: V1_FEATURE_COLUMNS_PRUNED must be the global 48-col set; never modified here.
_FEATURE_COLUMNS = list(V1_FEATURE_COLUMNS_PRUNED)
assert len(_FEATURE_COLUMNS) == 48, (
    f"probe_GRTUSDT: expected 48 cols in V1_FEATURE_COLUMNS_PRUNED, got {len(_FEATURE_COLUMNS)}. "
    "Global V1_FEATURE_COLUMNS_PRUNED must not be mutated."
)


def compute_is_sharpe(results: list) -> float:
    """Daily-annualized Sharpe from IS trade results.

    Uses to_daily_returns_series() — the official iteration_report methodology:
      - Groups by close_time date (UTC), sums weighted_pnl per day.
      - Fills calendar gaps with 0.0.
      - Converts pct -> decimal (/ 100).
      - Annualizes as sqrt(365).
    This matches the Sharpe reported in comparison.csv exactly.
    """
    if not results:
        return float("nan")

    returns = to_daily_returns_series(results)
    if returns.empty or returns.std() == 0:
        return float("nan")
    mean_r = returns.mean()
    std_r = returns.std()
    if std_r == 0.0 or not np.isfinite(std_r):
        return float("nan")
    return float(mean_r / std_r * math.sqrt(365))


def main() -> None:
    print(f"=== GATE 2 PRIMARY PROBE — {SYMBOL} (IS-only) ===")
    print(f"  OOS_CUTOFF: 2025-03-24 (OOS_CUTOFF_MS={OOS_CUTOFF_MS})")
    print(f"  seed={SEED}, n_trials={N_TRIALS}, training_months={TRAINING_MONTHS}")
    print(f"  feature_columns=V1_FEATURE_COLUMNS_PRUNED ({len(_FEATURE_COLUMNS)} cols)")
    print(f"  atr_tp={ATR_TP}, atr_sl={ATR_SL}")
    print(f"  specialist_mode=False (probe only)")

    cfg = BacktestConfig(
        symbols=(SYMBOL,),
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=5.8,   # overridden by atr_sl_multiplier
        take_profit_pct=11.6,  # overridden by atr_tp_multiplier
        timeout_minutes=10080,  # 1 week timeout (matches Model A)
        fee_pct=0.1,
        data_dir=_WD / "data",
        cooldown_candles=2,
        vol_targeting=True,
        vt_target_vol=0.3,
        vt_lookback_days=45,
        vt_min_scale=0.33,
        vt_max_scale=2.0,
        risk_consecutive_sl_limit=0,   # R1=OFF (standard for specialist probes)
        risk_drawdown_scale_enabled=False,  # R2=OFF
        end_time=OOS_CUTOFF_MS,  # IS-ONLY: never touches OOS data
    )

    strat = LightGbmStrategy(
        training_months=TRAINING_MONTHS,
        n_trials=N_TRIALS,
        label_tp_pct=4.0,
        label_sl_pct=2.0,
        label_timeout_minutes=4320,  # 9 bars at 8h
        fee_pct=0.1,
        features_dir=str(_WD / "data" / "features"),
        verbose=0,
        atr_tp_multiplier=ATR_TP,
        atr_sl_multiplier=ATR_SL,
        ensemble_seeds=[SEED],
        feature_columns=_FEATURE_COLUMNS,
        label_mode="triple_barrier",
        bounds_profile="v1_pruned",
        use_atr_labeling=True,
        specialist_mode=False,
    )

    import time
    t0 = time.time()
    results = run_backtest(cfg, strat, yearly_pnl_check=False)
    elapsed = time.time() - t0

    n_trades = len(results)
    is_sharpe = compute_is_sharpe(results)
    gate2_pass = bool(np.isfinite(is_sharpe) and is_sharpe >= 0.30)

    pnl_total = sum(r.weighted_pnl for r in results) if results else 0.0
    n_long = sum(1 for r in results if r.direction == 1) if results else 0
    n_short = sum(1 for r in results if r.direction == -1) if results else 0

    print(f"\n=== RESULTS ===")
    print(f"  n_trades={n_trades}  long={n_long}  short={n_short}")
    print(f"  total_pnl={pnl_total:.2f}")
    print(f"  IS_Sharpe (daily ann.)={is_sharpe:.4f}")
    print(f"  gate2_pass={gate2_pass}  (threshold: >= +0.30)")
    print(f"  elapsed={elapsed:.0f}s ({elapsed/60:.1f}min)")

    result = {
        "coin": SYMBOL,
        "probe_is_sharpe": round(float(is_sharpe), 4) if np.isfinite(is_sharpe) else None,
        "gate2_pass": gate2_pass,
        "n_trades": n_trades,
        "pnl_total": round(pnl_total, 2),
        "elapsed_s": round(elapsed, 1),
        "seed": SEED,
        "n_trials": N_TRIALS,
        "feature_cols": len(_FEATURE_COLUMNS),
        "note": "single-seed=42, n_trials=10, IS-only, no new features, baseline structure probe",
    }
    OUTPUT_PATH.write_text(json.dumps(result, indent=2))
    print(f"\nWrote {OUTPUT_PATH}")
    print(f"\nGATE 2 PRIMARY: {'PASS' if gate2_pass else 'FAIL'} "
          f"(IS_Sharpe={is_sharpe:.4f} vs threshold=+0.30)")


if __name__ == "__main__":
    main()
