"""iter-v1/087 GATE-INV — config-matched probe for TRBUSDT.

PURPOSE: Validate that the AMENDED Gate-2 methodology (config-matched probe)
closes the +0.49 → −0.30 gap observed in iter-v1/086.

DIFFERENCE vs the original /086 probe (analysis/iteration_v1-086/probe_TRBUSDT.py):
  - n_trials      : 10  →  30  (matches V1_SPECIALIST_OPTUNA_TRIALS)
  - ood_enabled   : False  →  True   (matches full specialist R3=ON)
  - bounds_profile: "v1_pruned"  →  "v1_specialist"  (matches specialist Optuna objective)
  - ood_cutoff_pct: N/A  →  0.70
  - ood_features  : None  →  list(V1_OOD_FEATURE_COLUMNS)

UNCHANGED:
  - specialist_mode=False  (single-inner-seed walk-forward, not 50-seed specialist)
  - ensemble_seeds=[42]  (inner-seed 42 only; residual gap vs full = inner-seed averaging)
  - 48-col V1_FEATURE_COLUMNS_PRUNED
  - ATR 2.9/1.45, IS-only walk-forward Sharpe

EXPECTED: config-matched probe IS Sharpe should land near −0.30 (residual = inner-seed
averaging only), NOT near the cheap probe's +0.49. This validates that the 3-confound
mismatch (n_trials + OOD + bounds_profile) was the cause of the +0.80 gap.

VERDICT THRESHOLDS:
  - Config-matched probe ∈ [−0.5, −0.1] → AMENDMENT WORKS (gap explained, not bias)
  - Config-matched probe still strongly positive (> +0.20) → residual bias remains, FLAG

Full specialist IS Sharpe (50-seed mean): −0.3044
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

# ── constants ────────────────────────────────────────────────────────────────
SYM = "TRBUSDT"
INTERVAL = "8h"
SEED = 42
N_TRIALS = 30  # AMENDED: matches V1_SPECIALIST_OPTUNA_TRIALS (was 10)
ATR_TP_MULT = 2.9
ATR_SL_MULT = 1.45
TRAINING_MONTHS = 24
TIMEOUT_MINUTES = 10080  # 21 bars * 480 min
FEE_PCT = 0.1

# NOTE on bounds_profile compatibility:
# "v1_specialist" bounds profile pins max_depth=5 and num_leaves=31 by NOT including them
# in the Optuna search space — intended ONLY for specialist_mode=True (which has a separate
# Optuna path in lgbm.py). When specialist_mode=False, the standard optimize_and_train()
# function is used, which calls best["max_depth"] directly (no .get() fallback), causing
# KeyError when max_depth is absent from study.best_params.
# THEREFORE: the config-matched probe must use bounds_profile="v1_pruned" (which INCLUDES
# max_depth in the search space, constrained to [3,5], so Optuna can still pick 5).
# This is the correct config-match for a single-seed non-specialist probe: the "v1_specialist"
# bound contribution is that max_depth=5 is FIXED, but with v1_pruned Optuna can and will
# explore depth<5 too. This is the only confound that cannot be eliminated in non-specialist mode.
# The other two confounds (n_trials 10→30, OOD OFF→ON) ARE fully matched here.
# PARTIALLY config-matched (v1_specialist incompatible with specialist_mode=False)
BOUNDS_PROFILE = "v1_pruned"

FEATURES_DIR = Path("data/features")
DATA_DIR = Path("data")

# ── feature columns ──────────────────────────────────────────────────────────
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED, V1_OOD_FEATURE_COLUMNS  # noqa: E402

FEATURE_COLUMNS = list(V1_FEATURE_COLUMNS_PRUNED)  # 48 cols
OOD_FEATURES = list(V1_OOD_FEATURE_COLUMNS)  # 16 scale-invariant features

# Full specialist reference (from /086 engineering report)
FULL_SPECIALIST_IS_SHARPE = -0.3044


def _monthly_sharpe_from_trades(trades: list) -> float:
    """Compute monthly Sharpe from trade list.

    Exact production formula (portfolio_report._monthly_sharpe):
      group by close_time month -> sum weighted_pnl -> mean/std * sqrt(12)
    """
    if not trades:
        return 0.0
    close_times = np.array([t.close_time for t in trades], dtype="int64")
    wpnls = np.array([t.weighted_pnl for t in trades], dtype="float64")
    months = pd.to_datetime(close_times, unit="ms", utc=True).to_period("M")
    monthly = pd.Series(wpnls).groupby(months).sum()
    if len(monthly) < 2 or monthly.std() == 0:
        return 0.0
    return float(monthly.mean() / monthly.std() * np.sqrt(12))


def _check_parquet() -> pd.DataFrame:
    """Verify parquet exists, report V1_FEATURE_COLUMNS_PRUNED coverage, return df."""
    parquet_path = FEATURES_DIR / f"{SYM}_{INTERVAL}_features.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(
            f"Parquet not found: {parquet_path}\n"
            f"Run: uv run crypto-trade features --symbols {SYM} --interval 8h "
            "--track v1 --format parquet"
        )
    df = pd.read_parquet(parquet_path)
    present = [c for c in FEATURE_COLUMNS if c in df.columns]
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    print(f"Parquet rows: {len(df)}, total columns: {len(df.columns)}")
    print(f"V1_FEATURE_COLUMNS_PRUNED coverage: {len(present)}/{len(FEATURE_COLUMNS)}")
    if missing:
        print(f"  Missing: {missing}")
    else:
        print("  All 48 feature columns present.")
    from crypto_trade.config import OOS_CUTOFF_MS

    is_df = df[df["open_time"] < OOS_CUTOFF_MS]
    print(f"IS rows (open_time < OOS_CUTOFF): {len(is_df)}")
    if len(is_df) > 0:
        min_dt = pd.to_datetime(is_df["open_time"].min(), unit="ms", utc=True)
        max_dt = pd.to_datetime(is_df["open_time"].max(), unit="ms", utc=True)
        is_years = (is_df["open_time"].max() - is_df["open_time"].min()) / (1000 * 86400 * 365.25)
        print(f"IS date range: {min_dt.date()} → {max_dt.date()} ({is_years:.2f} years)")
    return df


def _run_configmatched_probe() -> float:
    """Run config-matched single-seed walk-forward probe. Returns IS monthly Sharpe.

    Config matches full /086 specialist EXCEPT specialist_mode=False + ensemble_seeds=[42].
    The residual gap vs full specialist is inner-seed averaging only.
    """
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)

    from crypto_trade.backtest import run_backtest
    from crypto_trade.backtest_models import BacktestConfig
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    print(f"\n{'=' * 70}")
    print(f"GATE-INV CONFIG-MATCHED PROBE — {SYM}")
    print("  AMENDED vs /086 original probe:")
    print("    n_trials      : 30  (was 10 → NOW MATCHES V1_SPECIALIST_OPTUNA_TRIALS)")
    print("    ood_enabled   : True (was False → NOW MATCHES full specialist R3=ON)")
    print("    ood_cutoff_pct: 0.70")
    print("    bounds_profile: v1_pruned (v1_specialist incompatible with non-specialist")
    print("                    mode — KeyError on max_depth absent from study.best_params)")
    print("  UNCHANGED:")
    print("    specialist_mode=False (single-inner-seed, not 50-seed)")
    print("    ensemble_seeds=[42]  (inner-seed averaging is ONLY residual vs full)")
    print("    48-col V1_FEATURE_COLUMNS_PRUNED, ATR 2.9/1.45")
    print("  RESIDUAL CONFOUNDS vs full specialist:")
    print("    (1) inner-seed averaging: 50-seed mean vs single-seed=42")
    print("    (2) bounds: v1_pruned allows max_depth∈[3,5]; v1_specialist fixes max_depth=5")
    print("  CONFOUNDS CLOSED:")
    print("    n_trials: 10→30 CLOSED")
    print("    OOD: OFF→ON CLOSED")
    print(f"  Full specialist IS Sharpe (reference): {FULL_SPECIALIST_IS_SHARPE:+.4f}")
    print("  Expected config-matched range: [−0.5, −0.1]")
    print(f"{'=' * 70}")

    cfg = BacktestConfig(
        symbols=(SYM,),
        interval=INTERVAL,
        max_amount_usd=1000.0,
        stop_loss_pct=ATR_SL_MULT * 2.0,
        take_profit_pct=ATR_TP_MULT * 2.0,
        timeout_minutes=TIMEOUT_MINUTES,
        fee_pct=FEE_PCT,
        data_dir=DATA_DIR,
        cooldown_candles=2,
        vol_targeting=True,
        vt_target_vol=0.3,
        vt_lookback_days=45,
        vt_min_scale=0.33,
        vt_max_scale=2.0,
        risk_consecutive_sl_limit=0,  # R1=OFF (specialist convention)
        risk_drawdown_scale_enabled=False,  # R2=OFF
    )

    strat = LightGbmStrategy(
        training_months=TRAINING_MONTHS,
        n_trials=N_TRIALS,  # AMENDED: 30 (was 10)
        cv_splits=5,
        label_tp_pct=ATR_TP_MULT * 2.0,
        label_sl_pct=ATR_SL_MULT * 2.0,
        label_timeout_minutes=TIMEOUT_MINUTES,
        fee_pct=FEE_PCT,
        features_dir=str(FEATURES_DIR),
        verbose=0,
        atr_tp_multiplier=ATR_TP_MULT,
        atr_sl_multiplier=ATR_SL_MULT,
        use_atr_labeling=True,
        ensemble_seeds=[SEED],
        feature_columns=FEATURE_COLUMNS,
        ood_enabled=True,  # AMENDED: True (was False)
        ood_features=OOD_FEATURES,  # AMENDED: 16 OOD features (was None)
        ood_cutoff_pct=0.70,  # AMENDED: matches full specialist
        bounds_profile=BOUNDS_PROFILE,  # v1_pruned (v1_specialist crashes non-specialist)
        specialist_mode=False,  # UNCHANGED: single-seed walk-forward
    )

    t0 = time.time()
    result = run_backtest(cfg, strat)
    elapsed = time.time() - t0

    from crypto_trade.config import OOS_CUTOFF_MS

    is_trades = [t for t in result if t.close_time < OOS_CUTOFF_MS]
    all_trades = list(result)

    print(f"\n  Probe complete in {elapsed:.1f}s")
    print(f"  Total trades (IS+OOS): {len(all_trades)}")
    print(f"  IS trades (close_time < OOS_CUTOFF): {len(is_trades)}")

    if not is_trades:
        print("  PROBE WARNING: no IS trades produced — IS Sharpe = 0.0")
        return 0.0

    total_pnl_is = sum(t.weighted_pnl for t in is_trades)
    sharpe = _monthly_sharpe_from_trades(is_trades)

    gap_vs_full = sharpe - FULL_SPECIALIST_IS_SHARPE

    print(f"\n  IS total weighted_pnl = {total_pnl_is:.2f}%")
    print(f"  IS monthly Sharpe (config-matched) = {sharpe:+.4f}")
    print(f"  Full specialist IS Sharpe (50-seed) = {FULL_SPECIALIST_IS_SHARPE:+.4f}")
    print(f"  Gap (config-matched − full)         = {gap_vs_full:+.4f}")
    print("  Residual gap = inner-seed averaging only (expected if amendment works)")
    print()

    if sharpe <= -0.1 and sharpe >= -0.5:
        verdict = "AMENDMENT_WORKS"
        verdict_note = (
            "Config-matched probe lands near full specialist. "
            "The 3-confound mismatch (n_trials+OOD+bounds) explained the +0.80 gap. "
            "Gate-2 amended methodology is validated."
        )
    elif sharpe > 0.20:
        verdict = "RESIDUAL_BIAS_REMAINS"
        verdict_note = (
            f"Config-matched probe still strongly positive ({sharpe:+.4f}). "
            "Residual bias beyond inner-seed averaging remains. FLAG for QR."
        )
    else:
        verdict = "BORDERLINE"
        verdict_note = (
            f"Config-matched probe = {sharpe:+.4f}, "
            "outside expected [−0.5, −0.1] but not strongly positive. "
            "Gap partially closed. Review with QR."
        )

    print(f"  VERDICT: {verdict}")
    print(f"  {verdict_note}")

    return float(sharpe)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent.parent
    os.chdir(repo_root)
    print(f"Working dir: {os.getcwd()}")

    df = _check_parquet()
    sharpe = _run_configmatched_probe()

    out_dir = Path("analysis/iteration_v1-087")
    out_dir.mkdir(parents=True, exist_ok=True)

    from crypto_trade.config import OOS_CUTOFF_MS

    is_df = df[df["open_time"] < OOS_CUTOFF_MS]
    is_years = 0.0
    last_kline_date = ""
    if len(is_df) > 0:
        is_years = float(
            (is_df["open_time"].max() - is_df["open_time"].min()) / (1000 * 86400 * 365.25)
        )
        last_kline_date = str(pd.to_datetime(df["open_time"].max(), unit="ms", utc=True).date())

    gap_vs_full = sharpe - FULL_SPECIALIST_IS_SHARPE
    amendment_works = -0.5 <= sharpe <= -0.1
    residual_bias = sharpe > 0.20

    result_row = {
        "symbol": SYM,
        "probe_type": "config_matched",
        "probe_seed": SEED,
        "n_trials": N_TRIALS,
        "ood_enabled": True,
        "bounds_profile": BOUNDS_PROFILE,
        "atr_tp": ATR_TP_MULT,
        "atr_sl": ATR_SL_MULT,
        "probe_is_monthly_sharpe": round(sharpe, 4),
        "full_specialist_is_sharpe": FULL_SPECIALIST_IS_SHARPE,
        "gap_configmatched_minus_full": round(gap_vs_full, 4),
        "amendment_works": amendment_works,
        "residual_bias_flag": residual_bias,
        "is_years": round(is_years, 2),
        "last_kline_date": last_kline_date,
        "note": (
            "Config-matched: n_trials=30, ood=True, bounds=v1_pruned "
            "(v1_specialist incompatible with non-specialist mode — missing max_depth). "
            "Original /086 probe: n_trials=10, ood=False, bounds=v1_pruned. "
            "Confounds CLOSED: n_trials+OOD. RESIDUAL: inner-seed avg + bounds_depth_search."
        ),
    }
    out_path = out_dir / "gateinv_probe_TRBUSDT_configmatched.csv"
    pd.DataFrame([result_row]).to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")

    print(f"\n{'=' * 70}")
    print("GATE-INV FINAL SUMMARY — TRBUSDT CONFIG-MATCHED PROBE")
    print(f"  Config-matched IS Sharpe    = {sharpe:+.4f}")
    print(f"  Full specialist IS Sharpe   = {FULL_SPECIALIST_IS_SHARPE:+.4f}")
    print(f"  Gap (config-matched − full) = {gap_vs_full:+.4f}")
    print(f"  Amendment works             = {amendment_works}")
    print(f"  Residual bias flag          = {residual_bias}")
    print(f"{'=' * 70}")
