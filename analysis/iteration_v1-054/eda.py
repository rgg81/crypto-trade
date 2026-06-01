"""
EDA for iter-v1/054 — btc_funding_spread_30_90 (spread-only, 47-col stack).

After iter-v1/053 confirmed btc_funding_rate_8h_impulse is INERT (rank >30/48 in 3/3
outer seeds), /054 drops impulse and runs with spread-only: 48 → 47 cols.

This EDA is INFORMATIONAL per the pre-launch EDA rule: artifact existence is the gate
criterion. No ABORT on any threshold. All values reported regardless of magnitude.

Checks (BTCUSDT IS window only, close_time < OOS_CUTOFF_MS):
  ADF  — stationarity for btc_funding_spread_30_90 (idempotent re-run from /052)
  IC   — pairwise Pearson |IC| vs the 46 other V1_FEATURE_COLUMNS_PRUNED features
           (NOT vs itself; spread is the 47th column; peers are the remaining 46)
  dist — distribution statistics for btc_funding_spread_30_90

Parquet source: data/features/BTCUSDT_8h_features.parquet
IS barrier:     close_time < OOS_CUTOFF_MS (1742774400000 = 2025-03-24 00:00:00 UTC)

Outputs:
  analysis/iteration_v1-054/eda.csv  — one row per check result
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
TARGET_SYMBOL: str = "BTCUSDT"

# Single new feature under test (spread-only after impulse drop at /054)
NEW_FEATURE: str = "btc_funding_spread_30_90"

# Output paths
OUT_DIR: Path = Path("analysis/iteration_v1-054")
EDA_CSV: Path = OUT_DIR / "eda.csv"

# Informational thresholds — no ABORT on any result
F5_PASS_THRESHOLD: float = 0.30
F5_DOCUMENT_THRESHOLD: float = 0.60

# The 46 peer features (V1_FEATURE_COLUMNS_PRUNED 47-col list minus the new feature itself).
# SOURCE: src/crypto_trade/features_v1/__init__.py V1_FEATURE_COLUMNS_PRUNED (iter-v1/054 state)
PEER_FEATURES_46: tuple[str, ...] = (
    "cal_dow_norm",
    "cal_hour_norm",
    "dot_vs_btc_ret_ratio_30",
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

assert len(PEER_FEATURES_46) == 46, f"Expected 46 peer features, got {len(PEER_FEATURES_46)}"


# ---------------------------------------------------------------------------
# Data loading — IS-only (BTCUSDT only)
# ---------------------------------------------------------------------------


def load_btc_is_data() -> pd.DataFrame:
    """Load BTCUSDT IS-only parquet. Applies close_time < OOS_CUTOFF_MS barrier.

    Returns DataFrame with the new feature + 46 peer columns.
    """
    pq_path = FEATURES_DIR / f"{TARGET_SYMBOL}_{INTERVAL}_features.parquet"
    if not pq_path.exists():
        print(f"[EDA] ERROR: parquet not found: {pq_path}")
        sys.exit(1)

    df = pd.read_parquet(pq_path)

    # IS-only barrier — ONLY close_time < OOS_CUTOFF_MS (never >=)
    df = df[df["close_time"] < OOS_CUTOFF_MS].copy()

    n_is = len(df)
    print(f"[EDA] {TARGET_SYMBOL}: {n_is} IS rows (close_time < {OOS_CUTOFF_MS})")

    if NEW_FEATURE in df.columns:
        n_valid = int(df[NEW_FEATURE].notna().sum())
        n_nan = int(df[NEW_FEATURE].isna().sum())
        print(f"[EDA] {NEW_FEATURE}: {n_valid} valid rows, {n_nan} NaN (warmup bars)")
    else:
        print(f"[EDA] WARNING: {NEW_FEATURE} NOT FOUND in parquet")

    # Verify IS-window assertion — belt-and-suspenders
    assert df["close_time"].max() < OOS_CUTOFF_MS, (
        f"IS-window violation: max close_time {df['close_time'].max()} "
        f"is not below OOS_CUTOFF_MS {OOS_CUTOFF_MS}"
    )

    # Check peer features presence
    missing_peers = [f for f in PEER_FEATURES_46 if f not in df.columns]
    if missing_peers:
        print(f"[EDA] WARNING: missing peer features in parquet: {missing_peers}")

    return df


# ---------------------------------------------------------------------------
# ADF stationarity
# ---------------------------------------------------------------------------


def run_adf(df: pd.DataFrame) -> float:
    """Run ADF on btc_funding_spread_30_90 for BTCUSDT IS window.

    Returns p_value (float). Value is INFORMATIONAL — no BLOCK on result.
    Idempotent re-run from /052 (same feature, same IS barrier).
    """
    print("\n=== ADF Stationarity ===")
    print(f"  Feature: {NEW_FEATURE}")
    print(f"  Symbol: {TARGET_SYMBOL}")
    print("  Params: regression='c', maxlag=10")
    print("  NOTE: idempotent re-run from /052 — values are INFORMATIONAL — no BLOCK")

    if NEW_FEATURE not in df.columns:
        print(f"  {NEW_FEATURE}: NOT FOUND — assigning p=1.0")
        return 1.0

    series = df[NEW_FEATURE].dropna()

    if len(series) < 50:
        print(
            f"  {NEW_FEATURE}: insufficient data ({len(series)} non-NaN rows) — "
            "SKIP ADF, assigning p=1.0"
        )
        return 1.0

    adf_result = adfuller(series, regression="c", maxlag=10)
    pval = float(adf_result[1])
    adf_stat = float(adf_result[0])
    lag_used = int(adf_result[2])
    status = "PASS" if pval < 0.05 else "FAIL (informational)"

    print(
        f"  {NEW_FEATURE}: n={len(series)}  ADF stat={adf_stat:.4f}  "
        f"p-value={pval:.6e}  lag={lag_used}  [{status}]"
    )
    return pval


# ---------------------------------------------------------------------------
# IC orthogonality (Pearson) — vs 46 peer features
# ---------------------------------------------------------------------------


def run_ic_orthogonality(df: pd.DataFrame) -> list[dict]:
    """Compute Pearson |IC| between btc_funding_spread_30_90 and every peer feature.

    Values are INFORMATIONAL — no BLOCK on max |IC|.

    Returns list of {feature, ic_pearson, ic_abs, n_pairs, status}.
    """
    print("\n=== IC Orthogonality (Pearson, BTCUSDT IS) ===")
    print(f"  New feature: {NEW_FEATURE}")
    print(f"  Peers: {len(PEER_FEATURES_46)} features")
    print(f"  F5_PASS_THRESHOLD: {F5_PASS_THRESHOLD}  (informational only)")
    print(f"  F5_DOCUMENT_THRESHOLD: {F5_DOCUMENT_THRESHOLD}  (informational flag)")

    if NEW_FEATURE not in df.columns:
        print(f"  [{NEW_FEATURE}] NOT FOUND — skipping IC")
        return []

    print(f"\n  [{NEW_FEATURE}]")
    target_series = df[NEW_FEATURE]
    rows: list[dict] = []

    for peer in PEER_FEATURES_46:
        if peer not in df.columns:
            continue

        peer_series = df[peer]
        valid_mask = target_series.notna() & peer_series.notna()
        n_pairs = int(valid_mask.sum())

        if n_pairs < 30:
            ic_val = float("nan")
            ic_abs = float("nan")
        else:
            ic_val, _pval = stats.pearsonr(
                target_series[valid_mask].values,
                peer_series[valid_mask].values,
            )
            ic_val = float(ic_val)
            ic_abs = abs(ic_val)

        if ic_abs == ic_abs:  # not NaN
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

    valid_rows = [r for r in rows if r["ic_abs"] == r["ic_abs"]]
    if valid_rows:
        max_row = max(valid_rows, key=lambda r: r["ic_abs"])
        print(f"    Max |IC|: {max_row['ic_abs']:.4f} vs {max_row['feature']}")
        n_above_pass = sum(1 for r in valid_rows if r["ic_abs"] > F5_PASS_THRESHOLD)
        n_above_doc = sum(1 for r in valid_rows if r["ic_abs"] > F5_DOCUMENT_THRESHOLD)
        print(f"    Count > {F5_PASS_THRESHOLD}: {n_above_pass}")
        print(f"    Count > {F5_DOCUMENT_THRESHOLD}: {n_above_doc}")
        print("    [All values informational — no BLOCK]")

    return rows


# ---------------------------------------------------------------------------
# Distribution statistics
# ---------------------------------------------------------------------------


def run_dist_stats(df: pd.DataFrame) -> dict:
    """Compute distribution stats for btc_funding_spread_30_90 on BTCUSDT IS data."""
    print("\n=== Distribution Statistics ===")

    if NEW_FEATURE not in df.columns:
        print(f"  {NEW_FEATURE}: NOT FOUND — skipping dist stats")
        return {}

    series = df[NEW_FEATURE].dropna()

    if len(series) < 10:
        print(f"  {NEW_FEATURE}: insufficient data ({len(series)} rows) — skipping")
        return {}

    print(f"\n  [{NEW_FEATURE}]")
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
        "pct_nan": float(df[NEW_FEATURE].isna().mean()),
    }
    for k, v in d.items():
        print(f"    {k}: {v:.6g}")
    return d


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_eda_csv(
    adf_pval: float,
    ic_rows: list[dict],
    dist_stats: dict,
) -> None:
    """Write EDA results to CSV."""
    rows = []

    # ADF row
    rows.append(
        {
            "check": "ADF",
            "symbol": TARGET_SYMBOL,
            "feature": NEW_FEATURE,
            "metric": "p_value",
            "value": adf_pval,
            "status": "PASS" if adf_pval < 0.05 else "FAIL (informational)",
            "note": "informational — no BLOCK; idempotent re-run from /052",
        }
    )

    # IC rows — one per peer feature
    for r in ic_rows:
        rows.append(
            {
                "check": "IC_pearson",
                "symbol": TARGET_SYMBOL,
                "feature": f"{NEW_FEATURE} vs {r['feature']}",
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
                "feature": NEW_FEATURE,
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 70)
    print("EDA iter-v1/054: btc_funding_spread_30_90 (spread-only, 47-col stack)")
    print(f"  Symbol: {TARGET_SYMBOL} | IS barrier: OOS_CUTOFF_MS={OOS_CUTOFF_MS}")
    print("  All values are INFORMATIONAL — no ABORT on any result.")
    print("  ADF is idempotent re-run from /052 (same feature, same IS barrier).")
    print("=" * 70)

    df = load_btc_is_data()
    adf_pval = run_adf(df)
    ic_rows = run_ic_orthogonality(df)
    dist_stats = run_dist_stats(df)
    write_eda_csv(adf_pval, ic_rows, dist_stats)

    print("\n[EDA] Complete. iter-v1/054 EDA artifact committed for Phase 5.5 gate.")


if __name__ == "__main__":
    main()
