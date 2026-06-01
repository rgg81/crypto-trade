"""
EDA for iter-v1/049 — Pre-launch ADF stationarity + IC orthogonality check.

Feature under test: long_short_zscore_30
Axis: feature-family — NON-KLINE-CLASS defense (cycle-6 EXPLORATION 4/10)

Top-trader long/short ratio (sum_toptrader_long_short_ratio) is an account-NOTIONAL
positioning sentiment primitive already cached at 8h cadence in
data/open_interest/<SYMBOL>/8h.csv by the fetch-oi subcommand. It is structurally
orthogonal to all 44 existing V1_FEATURE_COLUMNS_PRUNED features, which are functions
of {OHLCV, funding_rate, open_interest, calendar}.

Checks:
  F4 — ADF stationarity per symbol (IS-only), PASS = all 5 symbols p < 0.05
  F5 — IC orthogonality (Pearson) on pooled IS data, PASS = max |IC| < 0.30
       DOCUMENT band = max |IC| in [0.30, 0.60)
       ABORT trigger = max |IC| >= 0.60 (TIGHTENED, third consecutive codification)

Note: long_short_zscore_30 is NOT in the parquets yet (requires Phase 6 parquet regen).
This EDA computes it directly from data/open_interest/<SYMBOL>/8h.csv and joins to
the kline parquet on open_time — IS-only (open_time < OOS_CUTOFF_MS).

Outputs:
  analysis/iteration_v1-049/eda.csv         — one row per check result
  analysis/iteration_v1-049/eda_summary.md  — markdown tables of results
  analysis/iteration_v1-049/feature_columns.json — 45-col V1_FEATURE_COLUMNS_PRUNED
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
OOS_CUTOFF_MS: int = 1742774400000  # 2025-03-24 00:00:00 UTC  (IMMUTABLE)

FEATURES_DIR: Path = Path("data/features")
OI_DIR: Path = Path("data/open_interest")
INTERVAL: str = "8h"
TARGET_FEATURE: str = "long_short_zscore_30"
LSR_SOURCE_COLUMN: str = "sum_toptrader_long_short_ratio"
LSR_ZSCORE_WINDOW: int = 30
LSR_ZSCORE_CLIP: float = 10.0

# F5 thresholds — TIGHTENED per brief Section 4 (third consecutive codification)
F5_PASS_THRESHOLD: float = 0.30   # max |IC| must be BELOW this to PASS (IDEAL)
F5_DOCUMENT_THRESHOLD: float = 0.60  # max |IC| [0.30, 0.60) = DOCUMENT (not auto-ABORT)
F5_ABORT_THRESHOLD: float = 0.60  # max |IC| >= this → ABORT pre-launch

V1_BASELINE_UNIVERSE: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
)

# 44 peer features (V1_FEATURE_COLUMNS_PRUNED at /048 state, before /049 adds long_short_zscore_30)
# SOURCE: src/crypto_trade/features_v1/__init__.py V1_FEATURE_COLUMNS_PRUNED (minus new feature)
PEER_FEATURES_44: tuple[str, ...] = (
    "cal_dow_norm",
    "cal_hour_norm",
    "funding_rate_zscore_30",   # iter-v1/023: NEW
    "funding_rate_zscore_90",   # iter-v1/023: NEW
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
    "oi_delta_30_z90",          # iter-v1/025: NEW
    "regime_momentum_signed_5d", # iter-v1/040: composed momentum
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

assert len(PEER_FEATURES_44) == 44, f"Expected 44 peer features, got {len(PEER_FEATURES_44)}"

# Full 45-col V1_FEATURE_COLUMNS_PRUNED at /049 state (peers + new feature)
V1_FEATURE_COLUMNS_PRUNED_45: tuple[str, ...] = (
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
    "long_short_zscore_30",     # iter-v1/049: NEW (this EDA validates it)
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

assert len(V1_FEATURE_COLUMNS_PRUNED_45) == 45, (
    f"Expected 45 features, got {len(V1_FEATURE_COLUMNS_PRUNED_45)}"
)

# Output paths
OUT_DIR: Path = Path("analysis/iteration_v1-049")
EDA_CSV: Path = OUT_DIR / "eda.csv"
EDA_SUMMARY_MD: Path = OUT_DIR / "eda_summary.md"
FEATURE_COLUMNS_JSON: Path = OUT_DIR / "feature_columns.json"


# ---------------------------------------------------------------------------
# Feature computation
# ---------------------------------------------------------------------------


def compute_long_short_zscore(
    lsr_series: pd.Series,
    window: int = LSR_ZSCORE_WINDOW,
    clip: float = LSR_ZSCORE_CLIP,
) -> pd.Series:
    """Compute rolling z-score of a long/short ratio series (past-only).

    At bar t: uses lsr[t-window+1] ... lsr[t] (min_periods=window).
    First window-1 bars are NaN. Output clipped to [-clip, clip].
    """
    lsr = lsr_series.astype(float)
    rmean = lsr.rolling(window=window, min_periods=window).mean()
    rstd = lsr.rolling(window=window, min_periods=window).std(ddof=1)
    zscore = (lsr - rmean) / rstd.replace(0, np.nan)
    return zscore.clip(-clip, clip)


def load_and_compute_target(sym: str) -> pd.Series | None:
    """Load OI cache for sym, compute long_short_zscore_30 (IS-only).

    Returns a Series indexed by integer position aligned to the IS kline rows,
    or None if OI data is unavailable.
    """
    oi_path = OI_DIR / sym / f"{INTERVAL}.csv"
    if not oi_path.exists():
        print(f"[EDA] WARNING: OI cache not found for {sym}: {oi_path}")
        return None

    oi_df = pd.read_csv(oi_path)
    if len(oi_df) == 0:
        print(f"[EDA] WARNING: OI cache empty for {sym}")
        return None

    if LSR_SOURCE_COLUMN not in oi_df.columns:
        print(f"[EDA] ERROR: column '{LSR_SOURCE_COLUMN}' not in {oi_path}")
        print(f"  Available: {list(oi_df.columns)}")
        return None

    # IS-only filter
    oi_df = oi_df[oi_df["open_time"] < OOS_CUTOFF_MS].copy()
    oi_df = oi_df.sort_values("open_time").reset_index(drop=True)

    if len(oi_df) == 0:
        print(f"[EDA] WARNING: No OI IS rows for {sym} after cutoff filter")
        return None

    n_is = len(oi_df)
    print(f"[EDA] {sym}: {n_is} OI IS rows (from {oi_df['open_time'].min()} to "
          f"{oi_df['open_time'].max()})")

    lsr_raw = oi_df[LSR_SOURCE_COLUMN].astype(float)
    zscore = compute_long_short_zscore(lsr_raw)
    return zscore


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_is_data() -> dict[str, pd.DataFrame]:
    """Load IS-only parquet for each symbol and attach long_short_zscore_30.

    Returns dict sym -> DataFrame with both 44 peer features AND the new
    long_short_zscore_30 column (computed from OI CSV, joined on open_time).
    """
    per_sym: dict[str, pd.DataFrame] = {}

    for sym in V1_BASELINE_UNIVERSE:
        pq_path = FEATURES_DIR / f"{sym}_{INTERVAL}_features.parquet"
        if not pq_path.exists():
            print(f"[EDA] WARNING: parquet not found: {pq_path}")
            continue

        df = pd.read_parquet(pq_path)

        # IS-only filter (IMMUTABLE gate — never touch OOS data)
        if "open_time" in df.columns:
            df = df[df["open_time"] < OOS_CUTOFF_MS].copy()

        # Verify IS-window assertion
        assert df["open_time"].max() < OOS_CUTOFF_MS, "IS-window violation"

        # Check peer features are present
        missing_peers = [f for f in PEER_FEATURES_44 if f not in df.columns]
        if missing_peers:
            print(f"[EDA] WARNING: {sym} missing peer features: {missing_peers}")

        # Load and compute long_short_zscore_30 from OI cache
        oi_path = OI_DIR / sym / f"{INTERVAL}.csv"
        if not oi_path.exists():
            print(f"[EDA] ERROR: OI cache not found for {sym}: {oi_path}")
            sys.exit(1)

        oi_df = pd.read_csv(oi_path)
        oi_df = oi_df[oi_df["open_time"] < OOS_CUTOFF_MS].copy()
        oi_df = oi_df.sort_values("open_time").reset_index(drop=True)

        if LSR_SOURCE_COLUMN not in oi_df.columns:
            print(f"[EDA] ERROR: '{LSR_SOURCE_COLUMN}' not in {oi_path}")
            sys.exit(1)

        # Join OI to kline frame on open_time (ms int, exact match)
        df = df.sort_values("open_time").reset_index(drop=True)
        df["_oi_merge_key"] = df["open_time"].astype("int64")

        oi_keyed = oi_df[["open_time", LSR_SOURCE_COLUMN]].copy()
        oi_keyed["_oi_merge_key"] = oi_keyed["open_time"].astype("int64")

        merged = df.merge(
            oi_keyed[["_oi_merge_key", LSR_SOURCE_COLUMN]],
            on="_oi_merge_key",
            how="left",
        ).drop(columns=["_oi_merge_key"])
        merged.index = df.index
        df = df.drop(columns=["_oi_merge_key"])

        lsr_series = merged[LSR_SOURCE_COLUMN].astype(float)
        df[TARGET_FEATURE] = compute_long_short_zscore(lsr_series).values

        n_is = len(df)
        n_valid = int(df[TARGET_FEATURE].notna().sum())
        n_nan = int(df[TARGET_FEATURE].isna().sum())
        print(
            f"[EDA] {sym}: {n_is} IS kline rows | {n_valid} valid {TARGET_FEATURE} "
            f"| {n_nan} NaN (warmup={LSR_ZSCORE_WINDOW-1} bars)"
        )

        per_sym[sym] = df

    if len(per_sym) != len(V1_BASELINE_UNIVERSE):
        print(
            f"[EDA] ERROR: Expected {len(V1_BASELINE_UNIVERSE)} symbols, "
            f"got {len(per_sym)}"
        )
        sys.exit(1)

    return per_sym


# ---------------------------------------------------------------------------
# F4 — ADF stationarity
# ---------------------------------------------------------------------------


def run_adf(per_sym: dict[str, pd.DataFrame]) -> dict[str, float]:
    """Run ADF per symbol on TARGET_FEATURE IS values. Returns sym -> p-value."""
    print("\n=== F4: ADF Stationarity ===")
    print(f"  Feature: {TARGET_FEATURE}")
    print("  Params: regression='c', maxlag=10")
    pvals: dict[str, float] = {}

    for sym, df in per_sym.items():
        series = df[TARGET_FEATURE].dropna()
        if len(series) < 50:
            print(f"  {sym}: insufficient data ({len(series)} non-NaN rows) — SKIP")
            pvals[sym] = 1.0
            continue

        result = adfuller(series, regression="c", maxlag=10)
        pval = float(result[1])
        adf_stat = float(result[0])
        lag_used = int(result[2])
        pvals[sym] = pval
        status = "PASS" if pval < 0.05 else "FAIL"
        print(
            f"  {sym}: n={len(series)}  ADF stat={adf_stat:.4f}  "
            f"p-value={pval:.6e}  lag={lag_used}  [{status}]"
        )

    f4_pass = all(p < 0.05 for p in pvals.values())
    print(f"\n  F4 OVERALL: {'PASS' if f4_pass else 'FAIL'} (all 5 symbols p < 0.05 required)")
    return pvals


# ---------------------------------------------------------------------------
# F5 — IC orthogonality (Pearson) on pooled IS data
# ---------------------------------------------------------------------------


def run_ic_orthogonality(per_sym: dict[str, pd.DataFrame]) -> dict[str, float]:
    """Compute Pearson IC of TARGET_FEATURE vs all 44 peer features on pooled IS data.

    Returns dict feature_name -> |Pearson IC|.

    F5 thresholds (TIGHTENED, third consecutive codification for iter-v1/049):
      PASS     : max |IC| < 0.30 (IDEAL)
      DOCUMENT : max |IC| in [0.30, 0.60) — proceed but note correlation concern
      ABORT    : max |IC| >= 0.60          — pre-launch hard ABORT
    """
    print("\n=== F5: IC Orthogonality (Pearson) — pooled IS ===")
    print(f"  TIGHTENED thresholds: PASS < {F5_PASS_THRESHOLD} | "
          f"DOCUMENT [{F5_PASS_THRESHOLD}, {F5_ABORT_THRESHOLD}) | "
          f"ABORT >= {F5_ABORT_THRESHOLD}")

    # Pool all symbols
    pooled = pd.concat(list(per_sym.values()), ignore_index=True)
    print(f"  Pooled IS rows: {len(pooled)}")

    target_series = pooled[TARGET_FEATURE]
    n_target_valid = int(target_series.notna().sum())
    print(f"  Valid {TARGET_FEATURE} rows: {n_target_valid}")

    ic_abs: dict[str, float] = {}

    for feat in PEER_FEATURES_44:
        if feat not in pooled.columns:
            print(f"  [WARNING] Feature {feat} not in pooled columns — skipping")
            continue

        feat_series = pooled[feat]
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
    print("\n  Top-15 |IC|:")
    for i, (feat, ic) in enumerate(sorted_ic[:15], 1):
        if ic >= F5_ABORT_THRESHOLD:
            label = "  *** ABORT ***"
        elif ic >= F5_PASS_THRESHOLD:
            label = "  [DOCUMENT]"
        else:
            label = ""
        print(f"    {i:2d}. {feat:45s}  |IC| = {ic:.4f}{label}")

    # Gate evaluation
    f5_pass = max_ic_val < F5_PASS_THRESHOLD
    document = F5_PASS_THRESHOLD <= max_ic_val < F5_ABORT_THRESHOLD
    abort = max_ic_val >= F5_ABORT_THRESHOLD

    print(f"\n  F5 PASS      (max |IC| < {F5_PASS_THRESHOLD}):     "
          f"{'PASS' if f5_pass else 'FAIL'}")
    print(f"  F5 DOCUMENT  (max |IC| in [{F5_PASS_THRESHOLD}, {F5_ABORT_THRESHOLD})): "
          f"{'YES' if document else 'NO'}")
    print(f"  F5 ABORT     (max |IC| >= {F5_ABORT_THRESHOLD}):    "
          f"{'*** ABORT ***' if abort else 'OK'}")

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
        if len(series) == 0:
            print(f"  {sym}: no valid rows — SKIP")
            continue

        q = series.quantile([0.05, 0.25, 0.50, 0.75, 0.95])
        stats_d = {
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
        result[sym] = stats_d
        print(
            f"  {sym}: n={stats_d['count']} mean={stats_d['mean']:.4f} "
            f"std={stats_d['std']:.4f} skew={stats_d['skew']:.4f} "
            f"kurt={stats_d['kurtosis']:.4f} "
            f"p05={stats_d['p05']:.4f} p95={stats_d['p95']:.4f}"
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
                "value": round(pval, 10),
                "threshold": 0.05,
                "pass": int(pval < 0.05),
                "note": "p < 0.05 required for stationarity (ADF regression=c maxlag=10)",
            }
        )

    # IC rows — sorted descending
    sorted_ic = sorted(ic_abs.items(), key=lambda x: x[1], reverse=True)
    for feat, ic in sorted_ic:
        if ic >= F5_ABORT_THRESHOLD:
            note = "ABORT_TRIGGER"
        elif ic >= F5_PASS_THRESHOLD:
            note = "DOCUMENT"
        else:
            note = ""
        rows.append(
            {
                "check_type": "IC_pearson",
                "symbol": "pooled",
                "feature": feat,
                "value": round(ic, 6),
                "threshold": F5_PASS_THRESHOLD,
                "pass": int(ic < F5_PASS_THRESHOLD),
                "note": note,
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
                    f"skew={st['skew']:.4f} kurt={st['kurtosis']:.4f} "
                    f"p05={st['p05']:.4f} p95={st['p95']:.4f} "
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
    document = F5_PASS_THRESHOLD <= max_ic_val < F5_ABORT_THRESHOLD
    abort = max_ic_val >= F5_ABORT_THRESHOLD

    lines: list[str] = []
    lines.append("# EDA — iter-v1/049 Pre-launch Checks")
    lines.append("")
    lines.append(f"Feature under test: `{TARGET_FEATURE}`")
    lines.append(
        "Axis: feature-family — NON-KLINE-CLASS defense, top-trader positioning sentiment "
        "(cycle-6 EXPLORATION 4/10)"
    )
    lines.append(f"IS cutoff: `OOS_CUTOFF_MS = {OOS_CUTOFF_MS}` (2025-03-24)")
    lines.append("")
    lines.append(
        "**F5 thresholds TIGHTENED for iter-v1/049** (third consecutive codification): "
        "PASS < 0.30 (IDEAL) | DOCUMENT [0.30, 0.60) | ABORT >= 0.60"
    )
    lines.append("")

    # Gate summary
    lines.append("## Gate Summary")
    lines.append("")
    lines.append("| Gate | Status | Criterion |")
    lines.append("|------|--------|-----------|")
    lines.append(
        f"| F4 ADF stationarity | {'**PASS**' if f4_pass else '**FAIL**'} | "
        "all 5 symbols p < 0.05 |"
    )
    if f5_pass:
        f5_status = "**PASS** (IDEAL)"
    elif abort:
        f5_status = "**ABORT**"
    else:
        f5_status = "**DOCUMENT**"
    lines.append(
        f"| F5 IC orthogonality | {f5_status} | "
        f"max |IC| = {max_ic_val:.4f} vs `{max_ic_feat}` |"
    )
    lines.append(
        f"| F5 ABORT trigger | {'**ABORT**' if abort else 'OK'} | "
        f"max |IC| >= {F5_ABORT_THRESHOLD} |"
    )
    lines.append("")

    # ADF table
    lines.append("## F4 — ADF Stationarity (per symbol, IS-only)")
    lines.append("")
    lines.append("| Symbol | ADF p-value | Status |")
    lines.append("|--------|-------------|--------|")
    for sym, pval in adf_pvals.items():
        status = "PASS" if pval < 0.05 else "FAIL"
        lines.append(f"| {sym} | {pval:.6e} | {status} |")
    lines.append("")

    # IC table (top 15)
    lines.append("## F5 — IC Orthogonality (Pearson, pooled IS)")
    lines.append("")
    lines.append(f"Max |IC|: **{max_ic_val:.4f}** vs `{max_ic_feat}`")
    lines.append("")
    lines.append(
        f"PASS threshold: < {F5_PASS_THRESHOLD}  |  "
        f"DOCUMENT band: [{F5_PASS_THRESHOLD}, {F5_ABORT_THRESHOLD})  |  "
        f"ABORT threshold: >= {F5_ABORT_THRESHOLD}"
    )
    lines.append("")
    lines.append(f"### Top-15 |IC| with `{TARGET_FEATURE}`")
    lines.append("")
    lines.append("| Rank | Feature | |Pearson IC| | Note |")
    lines.append("|------|---------|------------|------|")
    for i, (feat, ic) in enumerate(sorted_ic[:15], 1):
        if ic >= F5_ABORT_THRESHOLD:
            note = "ABORT_TRIGGER"
        elif ic >= F5_PASS_THRESHOLD:
            note = "DOCUMENT"
        else:
            note = ""
        lines.append(f"| {i} | `{feat}` | {ic:.4f} | {note} |")
    lines.append("")

    # Distribution table
    lines.append(f"## Distribution Stats — `{TARGET_FEATURE}` (IS-only)")
    lines.append("")
    lines.append("| Symbol | N | Mean | Std | Skew | Kurt | P05 | P95 | Min | Max |")
    lines.append("|--------|---|------|-----|------|------|-----|-----|-----|-----|")
    for sym, st in dist_stats.items():
        lines.append(
            f"| {sym} | {st['count']} | {st['mean']:.4f} | {st['std']:.4f} | "
            f"{st['skew']:.4f} | {st['kurtosis']:.4f} | "
            f"{st['p05']:.4f} | {st['p95']:.4f} | "
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
            "iter-v1/049 closes as NEG-CLEAN-PRE-EDA. "
            "iter-v1/050 MUST rotate axis family per three-consecutive-feature-family rule."
        )
    elif document:
        lines.append(
            f"> **F5 DOCUMENT**: max |IC| = {max_ic_val:.4f} "
            f"in [{F5_PASS_THRESHOLD}, {F5_ABORT_THRESHOLD}). "
            "Correlated with `" + max_ic_feat + "` but below ABORT threshold. "
            "Proceed to Phase 6 backtest with PROMISING-WITH-CORRELATED-PRIMITIVE "
            "subtype if F1 PASS."
        )
        if not f4_pass:
            lines.append(
                "> **ALSO F4 FAIL**: One or more symbols fail ADF stationarity (p >= 0.05). "
                "Review before launch."
            )
    elif not f4_pass:
        lines.append("> **F4 FAIL**: One or more symbols fail ADF stationarity (p >= 0.05). "
                     "Review before launch.")
    else:
        lines.append(
            f"> **PASS** (F4 + F5 both clear): "
            f"max |IC| = {max_ic_val:.4f} < {F5_PASS_THRESHOLD} (IDEAL). "
            "Proceed to backtest launch. PROMISING-CLEAN-eligible."
        )

    EDA_SUMMARY_MD.write_text("\n".join(lines) + "\n")
    print(f"[EDA] Written: {EDA_SUMMARY_MD}")


def write_feature_columns_json() -> None:
    """Write feature_columns.json with the 45-col V1_FEATURE_COLUMNS_PRUNED tuple."""
    payload = {
        "feature_columns": list(V1_FEATURE_COLUMNS_PRUNED_45),
        "count": len(V1_FEATURE_COLUMNS_PRUNED_45),
        "iteration": "iter-v1/049",
        "note": (
            "V1_FEATURE_COLUMNS_PRUNED at iter-v1/049 state "
            "(44 -> 45 by adding long_short_zscore_30; "
            "top-trader long/short ratio z-score from data/open_interest/<SYMBOL>/8h.csv)"
        ),
    }
    FEATURE_COLUMNS_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"[EDA] Written: {FEATURE_COLUMNS_JSON}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 70)
    print("iter-v1/049 Pre-launch EDA: F4 ADF + F5 IC Orthogonality")
    print(f"  Feature under test: {TARGET_FEATURE}")
    print(f"  Source: {LSR_SOURCE_COLUMN} from data/open_interest/<SYMBOL>/8h.csv")
    print(f"  IS cutoff: {OOS_CUTOFF_MS} (2025-03-24)")
    print(f"  F5 thresholds: PASS < {F5_PASS_THRESHOLD} | "
          f"DOCUMENT [{F5_PASS_THRESHOLD}, {F5_ABORT_THRESHOLD}) | "
          f"ABORT >= {F5_ABORT_THRESHOLD}")
    print("=" * 70)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load IS data (parquets for 44 peers + OI CSV for new feature)
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
    f4_pass_all = all(p < 0.05 for p in adf_pvals.values())
    f5_pass = max_ic_val < F5_PASS_THRESHOLD
    document = F5_PASS_THRESHOLD <= max_ic_val < F5_ABORT_THRESHOLD
    abort = max_ic_val >= F5_ABORT_THRESHOLD

    print("\n" + "=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)
    print(f"  F4 (ADF all p<0.05):                    {'PASS' if f4_pass_all else 'FAIL'}")
    print(f"  F5 (max |IC| < {F5_PASS_THRESHOLD}):               "
          f"{'PASS (IDEAL)' if f5_pass else 'FAIL'}")
    print(f"  F5 DOCUMENT (max |IC| [{F5_PASS_THRESHOLD}, {F5_ABORT_THRESHOLD})): "
          f"{'YES' if document else 'NO'}")
    print(f"  F5 ABORT (max |IC| >= {F5_ABORT_THRESHOLD}):       "
          f"{'*** ABORT ***' if abort else 'OK'}")
    print(f"  Max |IC|: {max_ic_val:.4f} vs '{max_ic_feat}'")

    if abort:
        print("\n  *** ABORT PRE-LAUNCH ***")
        print("  iter-v1/049 closes as NEG-CLEAN-PRE-EDA.")
        print("  iter-v1/050 MUST rotate axis family.")
        sys.exit(2)
    elif document:
        print(f"\n  F5 DOCUMENT: max |IC| = {max_ic_val:.4f} in "
              f"[{F5_PASS_THRESHOLD}, {F5_ABORT_THRESHOLD}).")
        print("  Correlation concern documented. No auto-ABORT.")
        print("  Proceed to Phase 6 with PROMISING-WITH-CORRELATED-PRIMITIVE subtype if F1 PASS.")
    elif not f4_pass_all:
        print("\n  F4 FAIL: review ADF failing symbols before launch.")
        sys.exit(1)
    else:
        print("\n  All gates PASS (IDEAL). Proceed to Phase 6 backtest.")
        print("  PROMISING-CLEAN-eligible on F1 PASS.")


if __name__ == "__main__":
    main()
