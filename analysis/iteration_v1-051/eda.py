"""
EDA for iter-v1/051 — Multi-seed re-validation of /050's dot_vs_btc_ret_ratio_30.

This script mirrors analysis/iteration_v1-050/eda.py exactly — same feature, same IS
data, same checks.  iter-v1/051 adds no new feature; it validates /050's feature at
additional outer seeds.  This artifact is authored for Phase 5.5 gate completeness per
skill requirement (Section 2 committed EDA script mandatory).

Feature under test: dot_vs_btc_ret_ratio_30  (UNCHANGED from /050)
Axis: validation (multi-seed re-validation sub-type; no new feature or model-arch change)
      cycle-6 EXPLORATION 6/10

NOTE (per rule bf2c812/a6269df): EDA VALUES are INFORMATIONAL only.
No ABORT trigger on any EDA threshold — artifact existence is what Phase 5.5 requires.
All values reported regardless of magnitude.

Checks:
  ADF — stationarity on DOTUSDT IS window (close_time < OOS_CUTOFF_MS)
  IC_pearson — Pearson correlation of dot_vs_btc_ret_ratio_30 vs each of the 45
               other V1_FEATURE_COLUMNS_PRUNED features on DOTUSDT IS data
  dist_stats — distribution statistics on DOTUSDT IS window (overall)

Parquet source: data/features/DOTUSDT_8h_features.parquet
IS barrier: close_time < OOS_CUTOFF_MS (1742774400000 = 2025-03-24 00:00:00 UTC)

Outputs:
  analysis/iteration_v1-051/eda.csv         — one row per check result
  analysis/iteration_v1-051/eda_summary.md  — markdown table summary
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
OUT_DIR: Path = Path("analysis/iteration_v1-051")
EDA_CSV: Path = OUT_DIR / "eda.csv"
EDA_SUMMARY_MD: Path = OUT_DIR / "eda_summary.md"

# NOTE: Values are INFORMATIONAL (per rule bf2c812/a6269df).
# These thresholds are documented only — no hard ABORT on any threshold.
F5_PASS_THRESHOLD: float = 0.30
F5_DOCUMENT_THRESHOLD: float = 0.60

# The 45 peer features (V1_FEATURE_COLUMNS_PRUNED at iter-v1/050 state,
# i.e. the 46-col list minus dot_vs_btc_ret_ratio_30 itself).
# SOURCE: src/crypto_trade/features_v1/__init__.py V1_FEATURE_COLUMNS_PRUNED
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
    """Load DOTUSDT IS-only parquet.  Applies close_time < OOS_CUTOFF_MS barrier.

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
    Values are INFORMATIONAL (per rule bf2c812/a6269df) — no BLOCK on any result.
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


def run_ic_orthogonality(df: pd.DataFrame) -> list[dict]:
    """Compute Pearson |IC| between dot_vs_btc_ret_ratio_30 and each peer feature.

    All 45 pairs tested.  Values are INFORMATIONAL (per rule bf2c812/a6269df).
    No BLOCK on max |IC| — artifact existence is what Phase 5.5 requires.

    Returns list of dicts: {feature, ic_pearson, ic_abs, n_pairs, status}.
    """
    print("\n=== IC Orthogonality (Pearson, DOTUSDT IS) ===")
    print(f"  Feature: {TARGET_FEATURE}")
    print(f"  Peers: {len(PEER_FEATURES_45)} features")
    print(f"  F5_PASS_THRESHOLD: {F5_PASS_THRESHOLD}  (informational only)")
    print(f"  F5_DOCUMENT_THRESHOLD: {F5_DOCUMENT_THRESHOLD}  (informational flag)")

    target_series = df[TARGET_FEATURE]
    rows: list[dict] = []

    for peer in PEER_FEATURES_45:
        if peer not in df.columns:
            print(f"  [SKIP] {peer} not in parquet")
            continue

        peer_series = df[peer]
        valid_mask = target_series.notna() & peer_series.notna()
        n_pairs = int(valid_mask.sum())

        if n_pairs < 30:
            print(f"  [SKIP] {peer}: only {n_pairs} valid pairs (< 30)")
            ic_val = float("nan")
            ic_abs = float("nan")
        else:
            ic_val, _pval = stats.pearsonr(
                target_series[valid_mask].values,
                peer_series[valid_mask].values,
            )
            ic_val = float(ic_val)
            ic_abs = abs(ic_val)

        if not (ic_abs != ic_abs):  # not NaN
            if ic_abs > F5_DOCUMENT_THRESHOLD:
                status = f"HIGH_IC (informational) abs={ic_abs:.4f}"
            elif ic_abs > F5_PASS_THRESHOLD:
                status = f"MODERATE_IC (informational) abs={ic_abs:.4f}"
            else:
                status = "PASS"
        else:
            status = "SKIP"

        rows.append(
            {
                "feature": peer,
                "ic_pearson": ic_val,
                "ic_abs": ic_abs,
                "n_pairs": n_pairs,
                "status": status,
            }
        )

    # Print summary
    valid_rows = [r for r in rows if r["ic_abs"] == r["ic_abs"]]  # non-NaN
    if valid_rows:
        max_row = max(valid_rows, key=lambda r: r["ic_abs"])
        print(f"\n  Max |IC|: {max_row['ic_abs']:.4f} vs {max_row['feature']}")
        n_above_pass = sum(1 for r in valid_rows if r["ic_abs"] > F5_PASS_THRESHOLD)
        n_above_doc = sum(1 for r in valid_rows if r["ic_abs"] > F5_DOCUMENT_THRESHOLD)
        print(f"  Count > {F5_PASS_THRESHOLD}: {n_above_pass}")
        print(f"  Count > {F5_DOCUMENT_THRESHOLD}: {n_above_doc}")
        print("  [All values informational — no BLOCK]")

    return rows


# ---------------------------------------------------------------------------
# Distribution statistics
# ---------------------------------------------------------------------------


def run_dist_stats(df: pd.DataFrame) -> dict:
    """Compute distribution stats for dot_vs_btc_ret_ratio_30 on DOTUSDT IS data."""
    print("\n=== Distribution Statistics ===")
    series = df[TARGET_FEATURE].dropna()

    if len(series) < 10:
        print(f"  Insufficient data ({len(series)} rows). Skipping.")
        return {}

    d = {
        "n": len(series),
        "mean": float(series.mean()),
        "std": float(series.std()),
        "min": float(series.min()),
        "p25": float(series.quantile(0.25)),
        "median": float(series.median()),
        "p75": float(series.quantile(0.75)),
        "max": float(series.max()),
        "skew": float(series.skew()),
        "kurt": float(series.kurtosis()),
        "pct_nan": float(df[TARGET_FEATURE].isna().mean()),
    }
    for k, v in d.items():
        print(f"  {k}: {v:.6g}")
    return d


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_eda_csv(
    adf_results: dict,
    ic_rows: list[dict],
    dist_stats: dict,
) -> None:
    """Write EDA results to CSV and markdown summary."""
    rows = []

    # ADF rows
    for sym, pval in adf_results.items():
        rows.append(
            {
                "check": "ADF",
                "symbol": sym,
                "feature": TARGET_FEATURE,
                "metric": "p_value",
                "value": pval,
                "status": "PASS" if pval < 0.05 else "FAIL (informational)",
                "note": "informational — no BLOCK",
            }
        )

    # IC rows
    for r in ic_rows:
        rows.append(
            {
                "check": "IC_pearson",
                "symbol": TARGET_SYMBOL,
                "feature": r["feature"],
                "metric": "ic_abs",
                "value": r["ic_abs"],
                "status": r["status"],
                "note": "informational — no BLOCK",
            }
        )

    # Dist stats rows
    for k, v in dist_stats.items():
        rows.append(
            {
                "check": "dist_stats",
                "symbol": TARGET_SYMBOL,
                "feature": TARGET_FEATURE,
                "metric": k,
                "value": v,
                "status": "INFO",
                "note": "informational",
            }
        )

    df_out = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(EDA_CSV, index=False)
    print(f"\n[EDA] Written: {EDA_CSV} ({len(df_out)} rows)")

    # Markdown summary
    with EDA_SUMMARY_MD.open("w") as f:
        f.write(f"# EDA Summary — iter-v1/051 — {TARGET_FEATURE}\n\n")
        f.write(
            "All values are INFORMATIONAL (per rule bf2c812/a6269df). "
            "No BLOCK on any EDA result — artifact existence is the gate criterion.\n\n"
        )
        f.write("## ADF Stationarity\n\n")
        f.write("| Symbol | p-value | Status |\n|---|---|---|\n")
        for sym, pval in adf_results.items():
            status = "PASS" if pval < 0.05 else "FAIL (informational)"
            f.write(f"| {sym} | {pval:.6e} | {status} |\n")
        f.write("\n## IC Orthogonality (top 10 by |IC|)\n\n")
        f.write("| Peer Feature | |IC| | n_pairs | Status |\n|---|---|---|---|\n")
        valid_ic = [r for r in ic_rows if r["ic_abs"] == r["ic_abs"]]
        for r in sorted(valid_ic, key=lambda x: x["ic_abs"], reverse=True)[:10]:
            f.write(f"| {r['feature']} | {r['ic_abs']:.4f} | {r['n_pairs']} | {r['status']} |\n")
        f.write("\n## Distribution Stats\n\n")
        f.write("| Metric | Value |\n|---|---|\n")
        for k, v in dist_stats.items():
            f.write(f"| {k} | {v:.6g} |\n")
    print(f"[EDA] Written: {EDA_SUMMARY_MD}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 70)
    print(f"EDA iter-v1/051: multi-seed re-validation of /050's {TARGET_FEATURE}")
    print(f"  Symbol: {TARGET_SYMBOL} | IS barrier: OOS_CUTOFF_MS={OOS_CUTOFF_MS}")
    print("  NOTE: This EDA mirrors iter-v1/050 eda.py. Same feature, same IS data.")
    print("  All values are INFORMATIONAL — no BLOCK on any result.")
    print("=" * 70)

    df = load_dot_is_data()
    adf_results = run_adf(df)
    ic_rows = run_ic_orthogonality(df)
    dist_stats = run_dist_stats(df)
    write_eda_csv(adf_results, ic_rows, dist_stats)

    print("\n[EDA] Complete. iter-v1/051 EDA artifact committed for Phase 5.5 gate.")


if __name__ == "__main__":
    main()
