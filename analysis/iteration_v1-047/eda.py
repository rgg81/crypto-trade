"""
EDA for iter-v1/047 — Pre-launch ADF stationarity + IC orthogonality check.

Feature under test: skew_zscore_21
Algebraic sister (load-bearing LM concern): stat_skew_20

Checks:
  F4 — ADF stationarity per symbol (IS-only), PASS = all 5 symbols p < 0.05
  F5 — IC orthogonality (Pearson) on pooled IS data, PASS = max |IC| < 0.50
       ABORT trigger = max |IC| >= 0.60 (per LM advisor closing note)

Outputs:
  analysis/iteration_v1-047/eda.csv      — one row per check result
  analysis/iteration_v1-047/eda_summary.md — markdown table of results
  analysis/iteration_v1-047/feature_columns.json — 45-col V1_FEATURE_COLUMNS_PRUNED tuple
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OOS_CUTOFF_MS: int = 1742774400000  # 2025-03-24 00:00:00 UTC
FEATURES_DIR: Path = Path("data/features")
INTERVAL: str = "8h"
TARGET_FEATURE: str = "skew_zscore_21"
SISTER_FEATURE: str = "stat_skew_20"

V1_BASELINE_UNIVERSE: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
)

# 45-column V1_FEATURE_COLUMNS_PRUNED (iter-v1/047 state)
V1_FEATURE_COLUMNS_PRUNED: tuple[str, ...] = (
    "cal_dow_norm",
    "cal_hour_norm",
    "funding_rate_zscore_30",
    "funding_rate_zscore_90",
    "interact_natr_x_adx",
    "interact_ret1_x_natr",
    "interact_ret1_x_ret3",
    "interact_rsi_x_adx",
    "interact_rsi_x_natr",
    "interact_stoch_x_adx",
    "mom_macd_hist_12_26_9",
    "mom_macd_line_12_26_9",
    "mom_roc_10",
    "mom_rsi_14",
    "mom_stoch_d_14",
    "mom_stoch_k_14",
    "mom_willr_14",
    "mr_pct_from_high_20",
    "mr_pct_from_low_20",
    "mr_rsi_extreme_14",
    "oi_delta_30_z90",
    "regime_momentum_signed_5d",
    "skew_zscore_21",
    "stat_autocorr_lag5",
    "stat_kurtosis_20",
    "stat_log_return_1",
    "stat_return_5",
    "stat_skew_20",
    "trend_adx_14",
    "trend_aroon_osc_14",
    "trend_aroon_osc_50",
    "trend_ema_cross_5_12",
    "trend_minus_di_14",
    "trend_plus_di_14",
    "trend_supertrend_14_3",
    "vol_atr_14",
    "vol_bb_bandwidth_20",
    "vol_cmf_14",
    "vol_mfi_14",
    "vol_natr_14",
    "vol_range_spike_24",
    "vol_range_spike_72",
    "vol_taker_buy_ratio",
    "vol_volume_pctchg_5",
    "vol_volume_rel_20",
)

assert len(V1_FEATURE_COLUMNS_PRUNED) == 45, (
    f"Expected 45 features, got {len(V1_FEATURE_COLUMNS_PRUNED)}"
)

# Features other than the target (for IC computation)
OTHER_FEATURES: tuple[str, ...] = tuple(
    f for f in V1_FEATURE_COLUMNS_PRUNED if f != TARGET_FEATURE
)
assert len(OTHER_FEATURES) == 44

# Output paths
OUT_DIR: Path = Path("analysis/iteration_v1-047")
EDA_CSV: Path = OUT_DIR / "eda.csv"
EDA_SUMMARY_MD: Path = OUT_DIR / "eda_summary.md"
FEATURE_COLUMNS_JSON: Path = OUT_DIR / "feature_columns.json"

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_is_data() -> dict[str, pd.DataFrame]:
    """Load IS-only parquet for each symbol. Returns dict sym -> DataFrame."""
    per_sym: dict[str, pd.DataFrame] = {}
    for sym in V1_BASELINE_UNIVERSE:
        pq_path = FEATURES_DIR / f"{sym}_{INTERVAL}_features.parquet"
        if not pq_path.exists():
            print(f"[EDA] WARNING: parquet not found: {pq_path}")
            continue
        df = pd.read_parquet(pq_path)
        # IS-only filter
        if "open_time" in df.columns:
            df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
        # Verify target feature is present
        if TARGET_FEATURE not in df.columns:
            print(f"[EDA] ERROR: {TARGET_FEATURE} not found in {pq_path}. "
                  "Were parquets regenerated post Phase 6 impl?")
            sys.exit(1)
        per_sym[sym] = df
        n_is = len(df)
        print(f"[EDA] {sym}: {n_is} IS rows loaded")
    if len(per_sym) != len(V1_BASELINE_UNIVERSE):
        print(f"[EDA] ERROR: Expected {len(V1_BASELINE_UNIVERSE)} symbols, "
              f"got {len(per_sym)}")
        sys.exit(1)
    return per_sym


# ---------------------------------------------------------------------------
# F4 — ADF stationarity
# ---------------------------------------------------------------------------


def run_adf(per_sym: dict[str, pd.DataFrame]) -> dict[str, float]:
    """Run ADF per symbol on TARGET_FEATURE IS values. Returns sym -> p-value."""
    print("\n=== F4: ADF Stationarity ===")
    pvals: dict[str, float] = {}
    for sym, df in per_sym.items():
        series = df[TARGET_FEATURE].dropna()
        result = adfuller(series, regression="c", maxlag=10)
        pval = float(result[1])
        pvals[sym] = pval
        status = "PASS" if pval < 0.05 else "FAIL"
        print(f"  {sym}: ADF p-value = {pval:.6f}  [{status}]")
    f4_pass = all(p < 0.05 for p in pvals.values())
    print(f"\n  F4 OVERALL: {'PASS' if f4_pass else 'FAIL'} "
          f"(all 5 symbols p < 0.05 required)")
    return pvals


# ---------------------------------------------------------------------------
# F5 — IC orthogonality (Pearson) on pooled IS data
# ---------------------------------------------------------------------------


def run_ic_orthogonality(per_sym: dict[str, pd.DataFrame]) -> dict[str, float]:
    """Compute Pearson IC of TARGET_FEATURE vs all 44 other pruned features on pooled IS data.

    Returns dict feature_name -> |Pearson IC|.
    """
    print("\n=== F5: IC Orthogonality (Pearson) — pooled IS ===")
    # Concatenate all symbols
    dfs = list(per_sym.values())
    pooled = pd.concat(dfs, ignore_index=True)
    print(f"  Pooled IS rows: {len(pooled)}")

    target_series = pooled[TARGET_FEATURE]

    ic_abs: dict[str, float] = {}
    for feat in OTHER_FEATURES:
        if feat not in pooled.columns:
            print(f"  [WARNING] Feature {feat} not in pooled columns — skipping")
            continue
        feat_series = pooled[feat]
        # Drop rows where either is NaN
        mask = target_series.notna() & feat_series.notna()
        n_valid = mask.sum()
        if n_valid < 30:
            print(f"  [WARNING] {feat}: only {n_valid} valid rows — skipping")
            continue
        pearson_r, _ = stats.pearsonr(target_series[mask], feat_series[mask])
        ic_abs[feat] = abs(float(pearson_r))

    # Sort by |IC| descending
    sorted_ic = sorted(ic_abs.items(), key=lambda x: x[1], reverse=True)

    max_ic_feat, max_ic_val = sorted_ic[0]
    sister_ic = ic_abs.get(SISTER_FEATURE, float("nan"))

    print(f"\n  Max |IC|: {max_ic_val:.4f} vs '{max_ic_feat}'")
    print(f"  |IC| vs {SISTER_FEATURE} (algebraic sister): {sister_ic:.4f}")
    print("\n  Top-10 |IC|:")
    for i, (feat, ic) in enumerate(sorted_ic[:10], 1):
        marker = " <-- SISTER" if feat == SISTER_FEATURE else ""
        print(f"    {i:2d}. {feat:40s}  |IC| = {ic:.4f}{marker}")

    # Gate evaluation
    f5_pass = max_ic_val < 0.50
    abort = max_ic_val >= 0.60
    print(f"\n  F5 PASS  threshold: max |IC| < 0.50  → {'PASS' if f5_pass else 'FAIL'}")
    print(f"  F5 ABORT threshold: max |IC| >= 0.60 → {'ABORT' if abort else 'OK'}")

    return ic_abs


# ---------------------------------------------------------------------------
# Distribution stats
# ---------------------------------------------------------------------------


def distribution_stats(per_sym: dict[str, pd.DataFrame]) -> dict[str, dict]:
    """Compute IS distribution stats for TARGET_FEATURE per symbol."""
    print("\n=== Distribution Stats (skew_zscore_21 IS) ===")
    result: dict[str, dict] = {}
    for sym, df in per_sym.items():
        series = df[TARGET_FEATURE].dropna()
        q = series.quantile([0.25, 0.50, 0.75])
        stats_d = {
            "count": int(len(series)),
            "mean": float(series.mean()),
            "std": float(series.std()),
            "q25": float(q[0.25]),
            "median": float(q[0.50]),
            "q75": float(q[0.75]),
            "min": float(series.min()),
            "max": float(series.max()),
        }
        result[sym] = stats_d
        print(
            f"  {sym}: n={stats_d['count']}, mean={stats_d['mean']:.4f}, "
            f"std={stats_d['std']:.4f}, "
            f"q25={stats_d['q25']:.4f}, median={stats_d['median']:.4f}, "
            f"q75={stats_d['q75']:.4f}"
        )
    return result


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def write_eda_csv(
    adf_pvals: dict[str, float],
    ic_abs: dict[str, float],
    dist_stats: dict[str, dict],
) -> None:
    """Write eda.csv — one row per check."""
    rows: list[dict] = []

    # ADF rows
    for sym, pval in adf_pvals.items():
        rows.append({
            "check_type": "ADF",
            "symbol": sym,
            "feature": TARGET_FEATURE,
            "value": round(pval, 8),
            "threshold": 0.05,
            "pass": int(pval < 0.05),
            "note": "p < 0.05 required for stationarity",
        })

    # IC rows
    sorted_ic = sorted(ic_abs.items(), key=lambda x: x[1], reverse=True)
    for feat, ic in sorted_ic:
        note = ""
        if feat == SISTER_FEATURE:
            note = "ALGEBRAIC SISTER — load-bearing LM concern"
        rows.append({
            "check_type": "IC_pearson",
            "symbol": "pooled",
            "feature": feat,
            "value": round(ic, 6),
            "threshold": 0.50,
            "pass": int(ic < 0.50),
            "note": note,
        })

    # Distribution rows
    for sym, st in dist_stats.items():
        rows.append({
            "check_type": "dist_stats",
            "symbol": sym,
            "feature": TARGET_FEATURE,
            "value": round(st["mean"], 6),
            "threshold": float("nan"),
            "pass": 1,
            "note": (
                f"n={st['count']} mean={st['mean']:.4f} std={st['std']:.4f} "
                f"q25={st['q25']:.4f} median={st['median']:.4f} q75={st['q75']:.4f} "
                f"min={st['min']:.4f} max={st['max']:.4f}"
            ),
        })

    df = pd.DataFrame(rows)
    df.to_csv(EDA_CSV, index=False)
    print(f"\n[EDA] Written: {EDA_CSV} ({len(rows)} rows)")


def write_eda_summary_md(
    adf_pvals: dict[str, float],
    ic_abs: dict[str, float],
    dist_stats: dict[str, dict],
) -> None:
    """Write eda_summary.md — markdown tables."""
    sorted_ic = sorted(ic_abs.items(), key=lambda x: x[1], reverse=True)
    max_ic_feat, max_ic_val = sorted_ic[0]
    sister_ic = ic_abs.get(SISTER_FEATURE, float("nan"))
    f4_pass = all(p < 0.05 for p in adf_pvals.values())
    f5_pass = max_ic_val < 0.50
    abort = max_ic_val >= 0.60

    lines: list[str] = []
    lines.append("# EDA — iter-v1/047 Pre-launch Checks")
    lines.append("")
    lines.append(f"Feature under test: `{TARGET_FEATURE}`")
    lines.append(f"Algebraic sister (LM concern): `{SISTER_FEATURE}`")
    lines.append(f"IS cutoff: `OOS_CUTOFF_MS = {OOS_CUTOFF_MS}` (2025-03-24)")
    lines.append("")

    # Gate summary
    lines.append("## Gate Summary")
    lines.append("")
    lines.append("| Gate | Status | Criterion |")
    lines.append("|------|--------|-----------|")
    lines.append(f"| F4 ADF stationarity | {'**PASS**' if f4_pass else '**FAIL**'} | all 5 p < 0.05 |")
    lines.append(f"| F5 IC orthogonality | {'**PASS**' if f5_pass else '**FAIL**'} | max |IC| < 0.50 |")
    lines.append(f"| F5 ABORT trigger    | {'**ABORT**' if abort else 'OK'} | max |IC| >= 0.60 |")
    lines.append("")

    # ADF table
    lines.append("## F4 — ADF Stationarity (per symbol, IS-only)")
    lines.append("")
    lines.append("| Symbol | ADF p-value | Status |")
    lines.append("|--------|-------------|--------|")
    for sym, pval in adf_pvals.items():
        status = "PASS" if pval < 0.05 else "FAIL"
        lines.append(f"| {sym} | {pval:.6f} | {status} |")
    lines.append("")

    # IC table (top 10)
    lines.append("## F5 — IC Orthogonality (Pearson, pooled IS)")
    lines.append("")
    lines.append(f"Max |IC|: **{max_ic_val:.4f}** vs `{max_ic_feat}`")
    lines.append(f"|IC| vs `{SISTER_FEATURE}` (algebraic sister): **{sister_ic:.4f}**")
    lines.append("")
    lines.append("### Top-10 |IC| with skew_zscore_21")
    lines.append("")
    lines.append("| Rank | Feature | |Pearson IC| | Note |")
    lines.append("|------|---------|------------|------|")
    for i, (feat, ic) in enumerate(sorted_ic[:10], 1):
        note = "ALGEBRAIC SISTER" if feat == SISTER_FEATURE else ""
        lines.append(f"| {i} | `{feat}` | {ic:.4f} | {note} |")
    lines.append("")

    # Distribution table
    lines.append("## Distribution Stats — skew_zscore_21 (IS-only)")
    lines.append("")
    lines.append("| Symbol | N | Mean | Std | Q25 | Median | Q75 | Min | Max |")
    lines.append("|--------|---|------|-----|-----|--------|-----|-----|-----|")
    for sym, st in dist_stats.items():
        lines.append(
            f"| {sym} | {st['count']} | {st['mean']:.4f} | {st['std']:.4f} | "
            f"{st['q25']:.4f} | {st['median']:.4f} | {st['q75']:.4f} | "
            f"{st['min']:.4f} | {st['max']:.4f} |"
        )
    lines.append("")

    # Verdict
    if abort:
        lines.append("## VERDICT")
        lines.append("")
        lines.append(
            f"> **ABORT PRE-LAUNCH**: max |IC| = {max_ic_val:.4f} >= 0.60. "
            "skew_zscore_21 is nearly collinear with an existing feature. "
            "QR must review before backtest launch."
        )
    elif not f5_pass:
        lines.append("## VERDICT")
        lines.append("")
        lines.append(
            f"> **F5 FAIL**: max |IC| = {max_ic_val:.4f} >= 0.50 < 0.60. "
            "QR review required; no auto-abort but feature collinearity concern."
        )
    elif not f4_pass:
        lines.append("## VERDICT")
        lines.append("")
        lines.append("> **F4 FAIL**: One or more symbols fail ADF stationarity (p >= 0.05).")
    else:
        lines.append("## VERDICT")
        lines.append("")
        lines.append("> **PASS**: F4 + F5 both clear. Proceed to backtest launch.")

    EDA_SUMMARY_MD.write_text("\n".join(lines) + "\n")
    print(f"[EDA] Written: {EDA_SUMMARY_MD}")


def write_feature_columns_json() -> None:
    """Write feature_columns.json with the 45-col tuple."""
    payload = {
        "feature_columns": list(V1_FEATURE_COLUMNS_PRUNED),
        "count": len(V1_FEATURE_COLUMNS_PRUNED),
        "iteration": "iter-v1/047",
        "note": "V1_FEATURE_COLUMNS_PRUNED at iter-v1/047 state (44 -> 45 by adding skew_zscore_21)",
    }
    FEATURE_COLUMNS_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"[EDA] Written: {FEATURE_COLUMNS_JSON}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 70)
    print("iter-v1/047 Pre-launch EDA: F4 ADF + F5 IC Orthogonality")
    print("=" * 70)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load IS data
    per_sym = load_is_data()

    # F4: ADF stationarity
    adf_pvals = run_adf(per_sym)

    # F5: IC orthogonality
    ic_abs = run_ic_orthogonality(per_sym)

    # Distribution stats
    dist = distribution_stats(per_sym)

    # Write outputs
    write_eda_csv(adf_pvals, ic_abs, dist)
    write_eda_summary_md(adf_pvals, ic_abs, dist)
    write_feature_columns_json()

    # Final verdict
    sorted_ic = sorted(ic_abs.items(), key=lambda x: x[1], reverse=True)
    max_ic_feat, max_ic_val = sorted_ic[0]
    sister_ic = ic_abs.get(SISTER_FEATURE, float("nan"))
    f4_pass = all(p < 0.05 for p in adf_pvals.values())
    f5_pass = max_ic_val < 0.50
    abort = max_ic_val >= 0.60

    print("\n" + "=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)
    print(f"  F4 (ADF all p<0.05):            {'PASS' if f4_pass else 'FAIL'}")
    print(f"  F5 (max |IC| < 0.50):           {'PASS' if f5_pass else 'FAIL'}")
    print(f"  F5 ABORT (max |IC| >= 0.60):    {'ABORT' if abort else 'OK'}")
    print(f"  Max |IC|:                        {max_ic_val:.4f} vs '{max_ic_feat}'")
    print(f"  |IC| vs {SISTER_FEATURE}: {sister_ic:.4f}")
    if abort:
        print("\n  *** ABORT PRE-LAUNCH ***")
        sys.exit(2)
    elif not (f4_pass and f5_pass):
        print("\n  *** GATE FAIL — escalate to QR ***")
        sys.exit(1)
    else:
        print("\n  All gates PASS. Proceed to backtest.")


if __name__ == "__main__":
    main()
