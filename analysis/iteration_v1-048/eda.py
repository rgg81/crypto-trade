"""
EDA for iter-v1/048 — Pre-launch ADF stationarity + IC orthogonality check.

Feature under test: trade_count_zscore_30
Axis: microstructure (UNUSED-primitive defense; cycle-6 feature-family EXPLORATION 3/10)

UNUSED-primitive rationale: ``trades`` (Binance number_of_trades kline field 8) has
ZERO feature-level descendants in V1_FEATURE_COLUMNS_PRUNED (44-col state at /047).
Defends against /047 NEG-CLEAN-PRE-EDA algebraic-sister failure (skew_zscore_21
|IC|=0.81 vs stat_skew_20) by choosing a primitive with no algebraic relatives in the
pruned set.

Checks:
  F4 — ADF stationarity per symbol (IS-only), PASS = all 5 symbols p < 0.05
  F5 — IC orthogonality (Pearson) on pooled IS data, PASS = max |IC| < 0.30
       ABORT trigger = max |IC| >= 0.60 (TIGHTENED per QR dispatch; prev 0.50/0.60)

Outputs:
  analysis/iteration_v1-048/eda.csv        — one row per check result
  analysis/iteration_v1-048/eda_summary.md — markdown table of results
  analysis/iteration_v1-048/feature_columns.json — 45-col V1_FEATURE_COLUMNS_PRUNED tuple
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OOS_CUTOFF_MS: int = 1742774400000  # 2025-03-24 00:00:00 UTC
FEATURES_DIR: Path = Path("data/features")
INTERVAL: str = "8h"
TARGET_FEATURE: str = "trade_count_zscore_30"

# F5 thresholds — TIGHTENED per QR dispatch for iter-v1/048
F5_PASS_THRESHOLD: float = 0.30  # max |IC| must be BELOW this to PASS
F5_ABORT_THRESHOLD: float = 0.60  # max |IC| >= this → ABORT pre-launch

V1_BASELINE_UNIVERSE: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
)

# 45-column V1_FEATURE_COLUMNS_PRUNED (iter-v1/048 state — 44+1 = 45)
# SOURCE: src/crypto_trade/features_v1/__init__.py V1_FEATURE_COLUMNS_PRUNED
V1_FEATURE_COLUMNS_PRUNED: tuple[str, ...] = (
    "cal_dow_norm",
    "cal_hour_norm",
    "funding_rate_zscore_30",  # iter-v1/023: NEW
    "funding_rate_zscore_90",  # iter-v1/023: NEW
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
    "oi_delta_30_z90",  # iter-v1/025: NEW
    "regime_momentum_signed_5d",  # iter-v1/040: composed momentum
    "stat_autocorr_lag5",
    "stat_kurtosis_20",
    "stat_log_return_1",
    "stat_return_5",
    "stat_skew_20",
    "trade_count_zscore_30",  # iter-v1/048: NEW (this EDA)
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

# Features other than the target (44 peers for IC computation)
OTHER_FEATURES: tuple[str, ...] = tuple(f for f in V1_FEATURE_COLUMNS_PRUNED if f != TARGET_FEATURE)
assert len(OTHER_FEATURES) == 44

# Output paths
OUT_DIR: Path = Path("analysis/iteration_v1-048")
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
            print(
                f"[EDA] ERROR: {TARGET_FEATURE} not found in {pq_path}. "
                "Regenerate parquets after iter-v1/048 Phase 6 impl."
            )
            sys.exit(1)
        per_sym[sym] = df
        n_is = len(df)
        print(f"[EDA] {sym}: {n_is} IS rows loaded")
    if len(per_sym) != len(V1_BASELINE_UNIVERSE):
        print(f"[EDA] ERROR: Expected {len(V1_BASELINE_UNIVERSE)} symbols, got {len(per_sym)}")
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
    print(f"\n  F4 OVERALL: {'PASS' if f4_pass else 'FAIL'} (all 5 symbols p < 0.05 required)")
    return pvals


# ---------------------------------------------------------------------------
# F5 — IC orthogonality (Pearson) on pooled IS data
# ---------------------------------------------------------------------------


def run_ic_orthogonality(per_sym: dict[str, pd.DataFrame]) -> dict[str, float]:
    """Compute Pearson IC of TARGET_FEATURE vs all 44 other pruned features on pooled IS data.

    Returns dict feature_name -> |Pearson IC|.

    F5 thresholds (TIGHTENED for iter-v1/048):
      PASS   : max |IC| < 0.30
      WARN   : max |IC| in [0.30, 0.60)  — Critic may downgrade but no auto-ABORT
      ABORT  : max |IC| >= 0.60          — pre-launch hard ABORT
    """
    print("\n=== F5: IC Orthogonality (Pearson) — pooled IS ===")
    print(f"  TIGHTENED thresholds: PASS < {F5_PASS_THRESHOLD}  |  ABORT >= {F5_ABORT_THRESHOLD}")
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
        n_valid = int(mask.sum())
        if n_valid < 30:
            print(f"  [WARNING] {feat}: only {n_valid} valid rows — skipping")
            continue
        pearson_r, _ = stats.pearsonr(target_series[mask], feat_series[mask])
        ic_abs[feat] = abs(float(pearson_r))

    # Sort by |IC| descending
    sorted_ic = sorted(ic_abs.items(), key=lambda x: x[1], reverse=True)

    max_ic_feat, max_ic_val = sorted_ic[0]

    print(f"\n  Max |IC|: {max_ic_val:.4f} vs '{max_ic_feat}'")
    print("\n  Top-10 |IC|:")
    for i, (feat, ic) in enumerate(sorted_ic[:10], 1):
        print(f"    {i:2d}. {feat:40s}  |IC| = {ic:.4f}")

    # Gate evaluation
    f5_pass = max_ic_val < F5_PASS_THRESHOLD
    warn = F5_PASS_THRESHOLD <= max_ic_val < F5_ABORT_THRESHOLD
    abort = max_ic_val >= F5_ABORT_THRESHOLD
    pass_label = "PASS" if f5_pass else "FAIL"
    warn_label = "WARN" if warn else "OK"
    abort_label = "ABORT" if abort else "OK"
    print(f"\n  F5 PASS  threshold: max |IC| < {F5_PASS_THRESHOLD}  → {pass_label}")
    print(
        f"  F5 WARN  band:      max |IC| in "
        f"[{F5_PASS_THRESHOLD}, {F5_ABORT_THRESHOLD}) → {warn_label}"
    )
    print(f"  F5 ABORT threshold: max |IC| >= {F5_ABORT_THRESHOLD} → {abort_label}")

    return ic_abs


# ---------------------------------------------------------------------------
# Distribution stats
# ---------------------------------------------------------------------------


def distribution_stats(per_sym: dict[str, pd.DataFrame]) -> dict[str, dict]:
    """Compute IS distribution stats for TARGET_FEATURE per symbol."""
    print(f"\n=== Distribution Stats ({TARGET_FEATURE} IS) ===")
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
        rows.append(
            {
                "check_type": "ADF",
                "symbol": sym,
                "feature": TARGET_FEATURE,
                "value": round(pval, 8),
                "threshold": 0.05,
                "pass": int(pval < 0.05),
                "note": "p < 0.05 required for stationarity",
            }
        )

    # IC rows — sorted descending
    sorted_ic = sorted(ic_abs.items(), key=lambda x: x[1], reverse=True)
    for feat, ic in sorted_ic:
        rows.append(
            {
                "check_type": "IC_pearson",
                "symbol": "pooled",
                "feature": feat,
                "value": round(ic, 6),
                "threshold": F5_PASS_THRESHOLD,
                "pass": int(ic < F5_PASS_THRESHOLD),
                "note": (
                    "ABORT_TRIGGER"
                    if ic >= F5_ABORT_THRESHOLD
                    else ("WARN" if ic >= F5_PASS_THRESHOLD else "")
                ),
            }
        )

    # Distribution rows
    for sym, st in dist_stats.items():
        rows.append(
            {
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
            }
        )

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
    f4_pass = all(p < 0.05 for p in adf_pvals.values())
    f5_pass = max_ic_val < F5_PASS_THRESHOLD
    warn = F5_PASS_THRESHOLD <= max_ic_val < F5_ABORT_THRESHOLD
    abort = max_ic_val >= F5_ABORT_THRESHOLD

    lines: list[str] = []
    lines.append("# EDA — iter-v1/048 Pre-launch Checks")
    lines.append("")
    lines.append(f"Feature under test: `{TARGET_FEATURE}`")
    lines.append(
        "Axis: microstructure — UNUSED-primitive defense (cycle-6 feature-family EXPLORATION 3/10)"
    )
    lines.append(f"IS cutoff: `OOS_CUTOFF_MS = {OOS_CUTOFF_MS}` (2025-03-24)")
    lines.append("")
    lines.append(
        "**F5 thresholds TIGHTENED for iter-v1/048**: "
        "PASS < 0.30 | WARN [0.30, 0.60) | ABORT >= 0.60"
    )
    lines.append("")

    # Gate summary
    lines.append("## Gate Summary")
    lines.append("")
    lines.append("| Gate | Status | Criterion |")
    lines.append("|------|--------|-----------|")
    lines.append(
        f"| F4 ADF stationarity | {'**PASS**' if f4_pass else '**FAIL**'} | all 5 p < 0.05 |"
    )
    if f5_pass:
        f5_status = "**PASS**"
    elif abort:
        f5_status = "**ABORT**"
    else:
        f5_status = "**WARN**"
    lines.append(f"| F5 IC orthogonality | {f5_status} | max |IC| < 0.30 (tightened) |")
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
    lines.append("")
    lines.append(
        f"PASS threshold: < {F5_PASS_THRESHOLD}  |  ABORT threshold: >= {F5_ABORT_THRESHOLD}"
    )
    lines.append("")
    lines.append("### Top-10 |IC| with trade_count_zscore_30")
    lines.append("")
    lines.append("| Rank | Feature | |Pearson IC| | Note |")
    lines.append("|------|---------|------------|------|")
    for i, (feat, ic) in enumerate(sorted_ic[:10], 1):
        if ic >= F5_ABORT_THRESHOLD:
            note = "ABORT_TRIGGER"
        elif ic >= F5_PASS_THRESHOLD:
            note = "WARN"
        else:
            note = ""
        lines.append(f"| {i} | `{feat}` | {ic:.4f} | {note} |")
    lines.append("")

    # Distribution table
    lines.append(f"## Distribution Stats — {TARGET_FEATURE} (IS-only)")
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
    lines.append("## VERDICT")
    lines.append("")
    if abort:
        lines.append(
            f"> **ABORT PRE-LAUNCH**: max |IC| = {max_ic_val:.4f} >= {F5_ABORT_THRESHOLD}. "
            f"`{TARGET_FEATURE}` is highly collinear with `{max_ic_feat}`. "
            "QR must review before backtest launch."
        )
    elif warn:
        lines.append(
            f"> **F5 WARN**: max |IC| = {max_ic_val:.4f} "
            f"in [{F5_PASS_THRESHOLD}, {F5_ABORT_THRESHOLD}). "
            "Collinearity concern; Critic may downgrade verdict but no auto-ABORT. "
            "QR review recommended."
        )
    elif not f4_pass:
        lines.append("> **F4 FAIL**: One or more symbols fail ADF stationarity (p >= 0.05).")
    else:
        lines.append(
            "> **PASS**: F4 + F5 both clear. "
            f"max |IC| = {max_ic_val:.4f} < {F5_PASS_THRESHOLD}. "
            "Proceed to backtest launch."
        )

    EDA_SUMMARY_MD.write_text("\n".join(lines) + "\n")
    print(f"[EDA] Written: {EDA_SUMMARY_MD}")


def write_feature_columns_json() -> None:
    """Write feature_columns.json with the 45-col tuple."""
    payload = {
        "feature_columns": list(V1_FEATURE_COLUMNS_PRUNED),
        "count": len(V1_FEATURE_COLUMNS_PRUNED),
        "iteration": "iter-v1/048",
        "note": (
            "V1_FEATURE_COLUMNS_PRUNED at iter-v1/048 state "
            "(44 -> 45 by adding trade_count_zscore_30)"
        ),
    }
    FEATURE_COLUMNS_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"[EDA] Written: {FEATURE_COLUMNS_JSON}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 70)
    print("iter-v1/048 Pre-launch EDA: F4 ADF + F5 IC Orthogonality")
    print(f"  Feature: {TARGET_FEATURE}")
    print(f"  F5 thresholds: PASS < {F5_PASS_THRESHOLD} | ABORT >= {F5_ABORT_THRESHOLD}")
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
    f4_pass = all(p < 0.05 for p in adf_pvals.values())
    f5_pass = max_ic_val < F5_PASS_THRESHOLD
    warn = F5_PASS_THRESHOLD <= max_ic_val < F5_ABORT_THRESHOLD
    abort = max_ic_val >= F5_ABORT_THRESHOLD

    print("\n" + "=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)
    f4_label = "PASS" if f4_pass else "FAIL"
    f5_label = "PASS" if f5_pass else ("WARN" if warn else "FAIL")
    abort_label2 = "ABORT" if abort else "OK"
    print(f"  F4 (ADF all p<0.05):          {f4_label}")
    print(f"  F5 (max |IC| < {F5_PASS_THRESHOLD}):    {f5_label}")
    print(f"  F5 ABORT (max |IC| >= {F5_ABORT_THRESHOLD}):  {abort_label2}")
    print(f"  Max |IC|:                     {max_ic_val:.4f} vs '{max_ic_feat}'")

    if abort:
        print("\n  *** ABORT PRE-LAUNCH ***")
        sys.exit(2)
    elif not (f4_pass and f5_pass) and not warn:
        print("\n  *** GATE FAIL — escalate to QR ***")
        sys.exit(1)
    elif warn:
        print(
            f"\n  F5 WARN: max |IC| = {max_ic_val:.4f} "
            f"in [{F5_PASS_THRESHOLD}, {F5_ABORT_THRESHOLD})."
        )
        print("  Critic may downgrade verdict. No auto-ABORT.")
    else:
        print("\n  All gates PASS. Proceed to backtest.")


if __name__ == "__main__":
    main()
