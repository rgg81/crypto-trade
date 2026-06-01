"""
EDA for iter-v1/050 — Pre-launch ADF stationarity + IC orthogonality check.

Feature under test: dot_vs_btc_ret_ratio_30
Axis: feature-family — DOT-only specialist cross-asset idiosyncratic return signal
      (cycle-6 EXPLORATION 5/10)

dot_vs_btc_ret_ratio_30 is the z-scored ratio of DOTUSDT's 30-bar rolling return
vs BTCUSDT's concurrent return, capturing DOT idiosyncratic momentum vs market leader.
It is DOT-only (NaN for all other symbols) and is already computed in the parquet
via the Phase 6 parquet regeneration (feat(iter-v1/034): basis_zscore_30 → new feat).

NOTE (per new rule bf2c812): EDA VALUES are INFORMATIONAL only.
No ABORT trigger on max |IC| — artifact existence is what Phase 5.5 requires.
All values reported regardless of magnitude.

Checks:
  ADF — stationarity on DOTUSDT IS window (close_time < OOS_CUTOFF_MS)
  IC_pearson — Pearson correlation of dot_vs_btc_ret_ratio_30 vs each of the 45
               other V1_FEATURE_COLUMNS_PRUNED features on DOTUSDT IS data
  dist_stats — distribution statistics on DOTUSDT IS window (overall)

Parquet source: data/features/DOTUSDT_8h_features.parquet
IS barrier: close_time < OOS_CUTOFF_MS (1742774400000 = 2025-03-24 00:00:00 UTC)

Outputs:
  analysis/iteration_v1-050/eda.csv         — one row per check result
  analysis/iteration_v1-050/eda_summary.md  — markdown table summary
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller

# ---------------------------------------------------------------------------
# Constants — IMMUTABLE
# ---------------------------------------------------------------------------
OOS_CUTOFF_MS: int = 1742774400000  # 2025-03-24 00:00:00 UTC (SACRED — DO NOT CHANGE)

FEATURES_DIR: Path = Path("data/features")
INTERVAL: str = "8h"
TARGET_SYMBOL: str = "DOTUSDT"
TARGET_FEATURE: str = "dot_vs_btc_ret_ratio_30"

# Output paths
OUT_DIR: Path = Path("analysis/iteration_v1-050")
EDA_CSV: Path = OUT_DIR / "eda.csv"
EDA_SUMMARY_MD: Path = OUT_DIR / "eda_summary.md"

# NOTE: Values are INFORMATIONAL (per new rule bf2c812).
# These thresholds are documented only — no hard ABORT on any threshold.
F5_PASS_THRESHOLD: float = 0.30
F5_DOCUMENT_THRESHOLD: float = 0.60

# The 45 peer features (V1_FEATURE_COLUMNS_PRUNED at iter-v1/049 state,
# i.e. the 45 features that are peers to dot_vs_btc_ret_ratio_30).
# SOURCE: src/crypto_trade/features_v1/__init__.py V1_FEATURE_COLUMNS_PRUNED
# (the 46-col list, minus the new feature dot_vs_btc_ret_ratio_30 itself).
PEER_FEATURES_45: tuple[str, ...] = (
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
    "long_short_zscore_30",
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

assert len(PEER_FEATURES_45) == 45, f"Expected 45 peer features, got {len(PEER_FEATURES_45)}"


# ---------------------------------------------------------------------------
# Data loading — IS-only (DOTUSDT only)
# ---------------------------------------------------------------------------


def load_dot_is_data() -> pd.DataFrame:
    """Load DOTUSDT IS-only parquet. Applies close_time < OOS_CUTOFF_MS barrier.

    Returns DataFrame with dot_vs_btc_ret_ratio_30 + 45 peer columns.
    """
    pq_path = FEATURES_DIR / f"{TARGET_SYMBOL}_{INTERVAL}_features.parquet"
    if not pq_path.exists():
        print(f"[EDA] ERROR: parquet not found: {pq_path}")
        sys.exit(1)

    df = pd.read_parquet(pq_path)

    # IS-only barrier — ONLY close_time < OOS_CUTOFF_MS (never >=)
    df = df[df["close_time"] < OOS_CUTOFF_MS].copy()

    n_is = len(df)
    n_target_valid = int(df[TARGET_FEATURE].notna().sum())
    n_target_nan = int(df[TARGET_FEATURE].isna().sum())

    print(f"[EDA] {TARGET_SYMBOL}: {n_is} IS rows (close_time < {OOS_CUTOFF_MS})")
    print(f"[EDA] {TARGET_FEATURE}: {n_target_valid} valid rows, {n_target_nan} NaN (warmup bars)")

    # Verify IS-window assertion — belt-and-suspenders
    assert df["close_time"].max() < OOS_CUTOFF_MS, (
        f"IS-window violation: max close_time {df['close_time'].max()} "
        f"is not below OOS_CUTOFF_MS {OOS_CUTOFF_MS}"
    )

    # Check all peer features are present
    missing_peers = [f for f in PEER_FEATURES_45 if f not in df.columns]
    if missing_peers:
        print(f"[EDA] WARNING: missing peer features in parquet: {missing_peers}")

    return df


# ---------------------------------------------------------------------------
# ADF stationarity
# ---------------------------------------------------------------------------


def run_adf(df: pd.DataFrame) -> dict[str, float]:
    """Run ADF on dot_vs_btc_ret_ratio_30 for DOTUSDT IS window.

    Returns dict {TARGET_SYMBOL: p-value}.
    Values are INFORMATIONAL (per rule bf2c812) — no BLOCK on any result.
    """
    print("\n=== ADF Stationarity ===")
    print(f"  Feature: {TARGET_FEATURE}")
    print(f"  Symbol: {TARGET_SYMBOL} (DOT-only specialist feature)")
    print("  Params: regression='c', maxlag=10")
    print("  NOTE: values are INFORMATIONAL — no BLOCK on result")

    series = df[TARGET_FEATURE].dropna()

    if len(series) < 50:
        print(
            f"  {TARGET_SYMBOL}: insufficient data ({len(series)} non-NaN rows) — "
            "SKIP ADF, assigning p=1.0"
        )
        return {TARGET_SYMBOL: 1.0}

    result = adfuller(series, regression="c", maxlag=10)
    pval = float(result[1])
    adf_stat = float(result[0])
    lag_used = int(result[2])
    status = "PASS" if pval < 0.05 else "FAIL (informational)"

    print(
        f"  {TARGET_SYMBOL}: n={len(series)}  ADF stat={adf_stat:.4f}  "
        f"p-value={pval:.6e}  lag={lag_used}  [{status}]"
    )

    return {TARGET_SYMBOL: pval}


# ---------------------------------------------------------------------------
# IC orthogonality (Pearson) — DOTUSDT IS data only
# ---------------------------------------------------------------------------


def run_ic_orthogonality(df: pd.DataFrame) -> dict[str, float]:
    """Compute Pearson IC of dot_vs_btc_ret_ratio_30 vs all 45 peer features.

    Uses DOTUSDT IS data only (DOT-only feature — NaN for all other symbols).
    Returns dict feature_name -> |Pearson IC|.

    NOTE: values are INFORMATIONAL (per rule bf2c812).
    All values reported regardless of magnitude — no ABORT trigger.
    """
    print("\n=== IC Orthogonality (Pearson) — DOTUSDT IS ===")
    print(f"  Target feature: {TARGET_FEATURE}")
    print(f"  Peers: {len(PEER_FEATURES_45)} features")
    print(
        f"  Informational thresholds (no ABORT): "
        f"PASS < {F5_PASS_THRESHOLD} | DOCUMENT >= {F5_DOCUMENT_THRESHOLD}"
    )
    print("  NOTE: values are INFORMATIONAL — all reported regardless of magnitude")

    target_series = df[TARGET_FEATURE]
    n_is = len(df)
    n_target_valid = int(target_series.notna().sum())
    print(f"  DOTUSDT IS rows: {n_is} | valid {TARGET_FEATURE}: {n_target_valid}")

    ic_abs: dict[str, float] = {}

    for feat in PEER_FEATURES_45:
        if feat not in df.columns:
            print(f"  [WARNING] Feature {feat} not in parquet — skipping")
            continue

        feat_series = df[feat]
        mask = target_series.notna() & feat_series.notna()
        n_valid = int(mask.sum())

        if n_valid < 30:
            print(f"  [WARNING] {feat}: only {n_valid} valid rows — skipping")
            continue

        pearson_r, _ = stats.pearsonr(target_series[mask], feat_series[mask])
        ic_abs[feat] = abs(float(pearson_r))

    # Sort by |IC| descending
    sorted_ic = sorted(ic_abs.items(), key=lambda x: x[1], reverse=True)

    if not sorted_ic:
        print("  [ERROR] No valid IC pairs computed")
        return ic_abs

    max_ic_feat, max_ic_val = sorted_ic[0]
    print(f"\n  Max |IC|: {max_ic_val:.4f} vs '{max_ic_feat}' (INFORMATIONAL)")
    print("\n  Top-15 |IC|:")
    for i, (feat, ic) in enumerate(sorted_ic[:15], 1):
        if ic >= F5_DOCUMENT_THRESHOLD:
            label = "  [DOCUMENT — informational]"
        elif ic >= F5_PASS_THRESHOLD:
            label = "  [note corr]"
        else:
            label = ""
        print(f"    {i:2d}. {feat:45s}  |IC| = {ic:.4f}{label}")

    return ic_abs


# ---------------------------------------------------------------------------
# Distribution stats — DOTUSDT IS
# ---------------------------------------------------------------------------


def distribution_stats(df: pd.DataFrame) -> dict:
    """Compute IS distribution stats for dot_vs_btc_ret_ratio_30 on DOTUSDT."""
    print(f"\n=== Distribution Stats ({TARGET_FEATURE} — {TARGET_SYMBOL} IS) ===")

    series = df[TARGET_FEATURE].dropna()
    if len(series) == 0:
        print(f"  {TARGET_SYMBOL}: no valid rows — SKIP")
        return {}

    q = series.quantile([0.05, 0.25, 0.50, 0.75, 0.95])
    st = {
        "count": int(len(series)),
        "mean": float(series.mean()),
        "std": float(series.std()),
        "skew": float(series.skew()),
        "kurtosis": float(series.kurtosis()),
        "p05": float(q[0.05]),
        "q25": float(q[0.25]),
        "median": float(q[0.50]),
        "q75": float(q[0.75]),
        "p95": float(q[0.95]),
        "min": float(series.min()),
        "max": float(series.max()),
    }

    print(
        f"  {TARGET_SYMBOL}: n={st['count']} mean={st['mean']:.4f} "
        f"std={st['std']:.4f} skew={st['skew']:.4f} "
        f"kurt={st['kurtosis']:.4f} "
        f"p05={st['p05']:.4f} p95={st['p95']:.4f} "
        f"min={st['min']:.4f} max={st['max']:.4f}"
    )

    return st


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def write_eda_csv(
    adf_pvals: dict[str, float],
    ic_abs: dict[str, float],
    dist_st: dict,
) -> int:
    """Write eda.csv — one row per check. Returns total row count."""
    rows: list[dict] = []

    # ADF rows
    for sym, pval in adf_pvals.items():
        rows.append(
            {
                "check_type": "ADF",
                "symbol": sym,
                "feature": TARGET_FEATURE,
                "value": round(pval, 10),
                "threshold": 0.05,
                "pass": int(pval < 0.05),
                "note": (
                    "INFORMATIONAL — p < 0.05 stationary; "
                    "no BLOCK on result (rule bf2c812); "
                    "ADF regression=c maxlag=10"
                ),
            }
        )

    # IC rows — sorted descending
    sorted_ic = sorted(ic_abs.items(), key=lambda x: x[1], reverse=True)
    for feat, ic in sorted_ic:
        if ic >= F5_DOCUMENT_THRESHOLD:
            note = "DOCUMENT (informational — no abort)"
        elif ic >= F5_PASS_THRESHOLD:
            note = "note_corr (informational)"
        else:
            note = "ok"
        rows.append(
            {
                "check_type": "IC_pearson",
                "symbol": TARGET_SYMBOL,
                "feature": feat,
                "value": round(ic, 6),
                "threshold": F5_PASS_THRESHOLD,
                "pass": int(ic < F5_PASS_THRESHOLD),
                "note": note,
            }
        )

    # Distribution row
    if dist_st:
        rows.append(
            {
                "check_type": "dist_stats",
                "symbol": TARGET_SYMBOL,
                "feature": TARGET_FEATURE,
                "value": round(dist_st["mean"], 6),
                "threshold": float("nan"),
                "pass": 1,
                "note": (
                    f"n={dist_st['count']} mean={dist_st['mean']:.4f} "
                    f"std={dist_st['std']:.4f} skew={dist_st['skew']:.4f} "
                    f"kurt={dist_st['kurtosis']:.4f} "
                    f"p05={dist_st['p05']:.4f} p95={dist_st['p95']:.4f} "
                    f"min={dist_st['min']:.4f} max={dist_st['max']:.4f}"
                ),
            }
        )

    df_out = pd.DataFrame(rows)
    df_out.to_csv(EDA_CSV, index=False)
    print(f"\n[EDA] Written: {EDA_CSV} ({len(rows)} rows)")
    return len(rows)


def write_eda_summary_md(
    adf_pvals: dict[str, float],
    ic_abs: dict[str, float],
    dist_st: dict,
) -> None:
    """Write eda_summary.md — markdown table summary."""
    sorted_ic = sorted(ic_abs.items(), key=lambda x: x[1], reverse=True)
    max_ic_feat, max_ic_val = sorted_ic[0] if sorted_ic else ("N/A", float("nan"))
    adf_pval = adf_pvals.get(TARGET_SYMBOL, 1.0)
    f4_pass = adf_pval < 0.05

    lines: list[str] = []
    lines.append("# EDA — iter-v1/050 Pre-launch Checks")
    lines.append("")
    lines.append(f"Feature under test: `{TARGET_FEATURE}`")
    lines.append(
        "Axis: feature-family — DOT-only specialist cross-asset idiosyncratic return "
        "vs BTC 30d z-scored (cycle-6 EXPLORATION 5/10)"
    )
    lines.append(f"IS cutoff: `OOS_CUTOFF_MS = {OOS_CUTOFF_MS}` (2025-03-24)")
    lines.append(f"Symbol scope: `{TARGET_SYMBOL}` only (DOT-only specialist feature)")
    lines.append("")
    lines.append(
        "**NOTE (rule bf2c812): EDA values are INFORMATIONAL. "
        "No ABORT trigger on any threshold. Artifact existence is the Phase 5.5 requirement.**"
    )
    lines.append("")

    # Gate summary
    lines.append("## Check Summary (Informational)")
    lines.append("")
    lines.append("| Check | Result | Value | Note |")
    lines.append("|-------|--------|-------|------|")
    lines.append(
        f"| ADF stationarity ({TARGET_SYMBOL}) | "
        f"{'PASS' if f4_pass else 'FAIL'} (informational) | "
        f"p={adf_pval:.6e} | No block on result |"
    )
    lines.append(
        f"| IC max |Pearson| | informational | "
        f"{max_ic_val:.4f} vs `{max_ic_feat}` | All values reported |"
    )
    lines.append("")

    # ADF table
    lines.append(f"## ADF Stationarity — `{TARGET_FEATURE}` ({TARGET_SYMBOL} IS-only)")
    lines.append("")
    lines.append("| Symbol | ADF p-value | Stationary (p<0.05) | Note |")
    lines.append("|--------|-------------|---------------------|------|")
    lines.append(
        f"| {TARGET_SYMBOL} | {adf_pval:.6e} | {'YES' if f4_pass else 'NO'} | INFORMATIONAL |"
    )
    lines.append("")

    # IC table (all 45 peers, top 15 shown in detail)
    lines.append(
        f"## IC Orthogonality — `{TARGET_FEATURE}` vs 45 peer features ({TARGET_SYMBOL} IS)"
    )
    lines.append("")
    lines.append(
        f"Max |IC|: **{max_ic_val:.4f}** vs `{max_ic_feat}` (INFORMATIONAL — no ABORT trigger)"
    )
    lines.append("")
    lines.append(
        f"Informational thresholds: "
        f"clean < {F5_PASS_THRESHOLD} | "
        f"document >= {F5_DOCUMENT_THRESHOLD}"
    )
    lines.append("")
    lines.append("### Top-15 |IC|")
    lines.append("")
    lines.append("| Rank | Feature | |Pearson IC| | Band |")
    lines.append("|------|---------|------------|------|")
    for i, (feat, ic) in enumerate(sorted_ic[:15], 1):
        if ic >= F5_DOCUMENT_THRESHOLD:
            band = "document (informational)"
        elif ic >= F5_PASS_THRESHOLD:
            band = "note_corr"
        else:
            band = "clean"
        lines.append(f"| {i} | `{feat}` | {ic:.4f} | {band} |")
    lines.append("")

    # Distribution table
    lines.append(f"## Distribution Stats — `{TARGET_FEATURE}` ({TARGET_SYMBOL} IS-only)")
    lines.append("")
    if dist_st:
        lines.append("| Symbol | N | Mean | Std | Skew | Kurt | P05 | Median | P95 | Min | Max |")
        lines.append("|--------|---|------|-----|------|------|-----|--------|-----|-----|-----|")
        lines.append(
            f"| {TARGET_SYMBOL} | {dist_st['count']} | {dist_st['mean']:.4f} | "
            f"{dist_st['std']:.4f} | {dist_st['skew']:.4f} | "
            f"{dist_st['kurtosis']:.4f} | {dist_st['p05']:.4f} | "
            f"{dist_st['median']:.4f} | {dist_st['p95']:.4f} | "
            f"{dist_st['min']:.4f} | {dist_st['max']:.4f} |"
        )
    else:
        lines.append("No distribution stats (insufficient data).")
    lines.append("")

    # Verdict
    lines.append("## VERDICT")
    lines.append("")
    lines.append(
        "> **INFORMATIONAL ONLY** (rule bf2c812): EDA artifact committed for Phase 5.5 "
        "compliance. Values do not block Phase 6 launch. "
        f"ADF p={adf_pval:.4e} ({'stationary' if f4_pass else 'non-stationary — informational'}). "
        f"Max |IC| = {max_ic_val:.4f} vs `{max_ic_feat}`."
    )

    EDA_SUMMARY_MD.write_text("\n".join(lines) + "\n")
    print(f"[EDA] Written: {EDA_SUMMARY_MD}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 70)
    print("iter-v1/050 Pre-launch EDA: ADF + IC Orthogonality (Informational)")
    print(f"  Feature under test: {TARGET_FEATURE}")
    print(f"  Symbol scope: {TARGET_SYMBOL} only (DOT-only specialist feature)")
    print(f"  Parquet: data/features/{TARGET_SYMBOL}_{INTERVAL}_features.parquet")
    print(f"  IS barrier: close_time < {OOS_CUTOFF_MS} (2025-03-24)")
    print("  NOTE: values INFORMATIONAL per rule bf2c812 — no ABORT trigger")
    print("=" * 70)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load IS data (DOTUSDT only)
    df = load_dot_is_data()

    # ADF stationarity
    adf_pvals = run_adf(df)

    # IC orthogonality
    ic_abs = run_ic_orthogonality(df)

    # Distribution stats
    dist_st = distribution_stats(df)

    # Write outputs
    n_rows = write_eda_csv(adf_pvals, ic_abs, dist_st)
    write_eda_summary_md(adf_pvals, ic_abs, dist_st)

    # Final summary
    sorted_ic = sorted(ic_abs.items(), key=lambda x: x[1], reverse=True)
    max_ic_feat, max_ic_val = sorted_ic[0] if sorted_ic else ("N/A", float("nan"))
    adf_pval = adf_pvals.get(TARGET_SYMBOL, 1.0)

    print("\n" + "=" * 70)
    print("FINAL SUMMARY (INFORMATIONAL — no BLOCK)")
    print("=" * 70)
    print(
        f"  ADF p-value ({TARGET_SYMBOL}): {adf_pval:.6e} "
        f"({'stationary' if adf_pval < 0.05 else 'non-stationary — informational'})"
    )
    print(f"  Max |IC| (Pearson): {max_ic_val:.4f} vs '{max_ic_feat}' (INFORMATIONAL)")
    print(f"  Total CSV rows: {n_rows}")
    print("  All values informational — Phase 6 launch proceeds regardless of values.")
    print(f"  Outputs: {EDA_CSV}, {EDA_SUMMARY_MD}")


if __name__ == "__main__":
    main()
