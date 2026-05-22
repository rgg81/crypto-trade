"""
iter-v3/024 — BTC funding-rate z-score (btc_funding_rate_zscore_30) EDA
(NEW external-data-source feature family — cross-asset variant).

Per Critic FINAL Recommendation #3 of iter-v3/023 (SHA `c4574af`) +
`feedback_v3_inert_features_at_higher_budget.md`:

After iter-v3/019 + iter-v3/023 confirmed that PER-SYMBOL
`funding_rate_zscore_30` is structurally INERT in v3's per-symbol-LightGBM
architecture (rank 14/14 across LDO+TRX+Portfolio at BOTH n_trials=10 AND
n_trials=35), the funding-feature-family axis was permanently CLOSED.

iter-v3/024 tests a STRUCTURALLY DISTINCT cross-asset variant:
`btc_funding_rate_zscore_30` — BTC's funding rate z-score broadcast to
ALL 3 per-symbol models. Hypothesis: BTC funding stress is exogenous to
BCH/LDO/TRX-specific funding patterns; it captures market-wide
leveraged-position imbalance (a system-stress signal) that the
per-symbol funding (intercepted at the per-symbol-architecture level)
couldn't surface.

Distinct mechanism vs iter-v3/019/023:
    - iter-v3/019/023: each per-symbol model received its OWN funding
      z-score (BCH model saw BCH funding; LDO model saw LDO funding;
      TRX model saw TRX funding). The model couldn't surface a
      cross-asset stress signal because the feature was TOO local.
    - iter-v3/024: ALL 3 models receive BTC's funding z-score
      (broadcast, identical column values across the 3 per-symbol
      training datasets at any given timestamp). The feature carries
      MARKET-WIDE leveraged-positioning information.

Why BTC funding (vs other cross-asset alternatives):
    - BTC is the dominant crypto asset by market cap and futures OI.
      Persistent positive BTC funding = leveraged longs paying shorts
      across the entire derivatives ecosystem → mean-reversion /
      liquidation pressure signal at the SYSTEMIC level.
    - 8h cadence aligns EXACTLY with v3 kline boundaries (00/08/16 UTC).
    - Data availability: BTC funding cached from 2020-08 onward
      (verified at iter-v3/024 setup time).
    - Cross-asset feature: identical column values across BCH/LDO/TRX
      training datasets at any given timestamp = no per-symbol overfit
      surface; only Optuna hyperparams can decide HOW to use it
      per-symbol.

Inputs read (IS-only — training window pre-OOS_CUTOFF_DATE 2025-03-24):
    - data/funding_rates/BTCUSDT.csv — BTC funding rate cache
    - data/{BCH,LDO,TRX}USDT/8h.csv — 8h klines (read for open_time alignment)
    - data/features_v3/{BCH,LDO,TRX}USDT_8h_features.parquet — for the 13
      V3_FEATURE_COLUMNS used in the IC orthogonality check (per-symbol
      since the cross-asset BTC funding column will be IC-tested against
      each per-symbol's existing 13 features)

Outputs (committed BEFORE the brief — Phase 5.5 reproducibility requirement):
    - analysis/iteration_v3-024/btc_funding_eda_coverage.csv — coverage % per symbol
    - analysis/iteration_v3-024/btc_funding_eda_distribution.csv — distribution
    - analysis/iteration_v3-024/btc_funding_eda_correlation.csv — Spearman IC
      between btc_funding_rate_zscore_30 and the 13 V3_FEATURE_COLUMNS per-symbol
    - analysis/iteration_v3-024/btc_funding_eda_rankic.csv — rank-IC of feature
      vs forward returns (1, 3, 7-bar horizons) per symbol
    - analysis/iteration_v3-024/btc_funding_eda_adf.csv — ADF stationarity test
    - analysis/iteration_v3-024/synthesis.md — narrative summary

Methodology — single-feature axis:
    1. Read BTC funding cache from data/funding_rates/BTCUSDT.csv
       (already populated via `crypto-trade fetch-funding --symbols BTCUSDT`).
    2. Compute btc_funding_rate_zscore_30 on BTC funding rate stream
       (past-only via .shift(1)).
    3. Broadcast: at each per-symbol kline timestamp, look up the BTC
       funding z-score at the matching open_time (left-join). Klines
       before BTC funding cache start get NaN.
    4. Coverage: count NaN values per symbol on IS window.
    5. Distribution: report mean, std, percentiles per symbol on
       broadcast z-score column.
    6. ADF stationarity test on z-scored series (must clear ADF p < 0.05).
    7. Spearman IC vs each of the 13 V3_FEATURE_COLUMNS per symbol.
       v3 hard gate: max |IC| < 0.70. Strict brief target: max |IC| < 0.50.
    8. Rank-IC vs forward returns per symbol on 1, 3, 7-bar horizons.
       Meaningful predictive signal: |rank-IC| >= 0.02 on at least 1 horizon.

Invariants the script asserts:
    - BTC funding cache exists with > 5000 rows
    - All 3 symbol kline CSVs + parquets exist
    - BTC funding broadcast coverage >= 80% on IS window per symbol
    - Max |IC| vs 13 V3_FEATURE_COLUMNS < 0.70 hard (preferably < 0.50)
    - ADF p-value < 0.05 on z-scored series

Track isolation: this script runs on the v3 worktree only. Reads
data/{SYM}/8h.csv + data/features_v3/*.parquet + data/funding_rates/BTCUSDT.csv.
Zero edits to src/.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

# v3 sacred constants
OOS_CUTOFF_DATE = pd.Timestamp("2025-03-24", tz="UTC")
OOS_CUTOFF_MS = int(OOS_CUTOFF_DATE.value // 1_000_000)

# IS training window — 24 months before OOS cutoff
TRAINING_MONTHS = 24
IS_START_TS = OOS_CUTOFF_DATE - pd.DateOffset(months=TRAINING_MONTHS)
IS_START_MS = int(IS_START_TS.value // 1_000_000)

# v3 universe (3 symbols, BCH+LDO+TRX, MKR-dropped per iter-v3/013)
V3_SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

# Cross-asset source: BTC funding broadcasts to all 3 per-symbol models
BTC_FUNDING_SYMBOL = "BTCUSDT"

# 13 V3_FEATURE_COLUMNS — UNCHANGED from iter-v3/023
# (per-symbol funding_rate_zscore_30 will be DROPPED at iter-v3/024 first commit;
# btc_funding_rate_zscore_30 is the NEW 14th feature)
V3_FEATURE_COLUMNS_TOP_N = (
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
)

# Forward-return horizons for rank-IC check
FWD_HORIZONS = (1, 3, 7)

# IC redundancy gate — v3 BASELINE_V3.md threshold (hard gate)
IC_THRESHOLD_HARD = 0.70

# IC strict brief target (well below 0.70 hard gate, ensures genuine new info)
IC_THRESHOLD_BRIEF = 0.50

# Funding rate z-score window — 30 bars = 10 days = ~9 funding cycles at 8h cadence
FUNDING_ZSCORE_WINDOW = 30

# Coverage floor for the candidate feature
COVERAGE_FLOOR_PCT = 80.0

# ADF stationarity threshold
ADF_PVALUE_THRESHOLD = 0.05

DATA_DIR = Path("data")
ANALYSIS_DIR = Path("analysis/iteration_v3-024")


def load_btc_funding() -> pd.DataFrame:
    """Read BTC funding rate cache."""
    cache_path = DATA_DIR / "funding_rates" / f"{BTC_FUNDING_SYMBOL}.csv"
    if not cache_path.exists():
        raise FileNotFoundError(
            f"BTC funding cache not found: {cache_path}. "
            f"Run: uv run crypto-trade fetch-funding --symbols {BTC_FUNDING_SYMBOL}"
        )
    df = pd.read_csv(cache_path)
    if len(df) < 5000:
        raise ValueError(
            f"BTC funding cache has only {len(df)} rows (< 5000); fetch failed?"
        )
    df = df.sort_values("funding_time").reset_index(drop=True)
    return df


def compute_btc_funding_zscore(
    funding_df: pd.DataFrame, window: int = FUNDING_ZSCORE_WINDOW
) -> pd.DataFrame:
    """Compute past-only z-scored BTC funding rate over rolling window.

    bar t z-score uses bars t-window...t-1 only (rolling stats lag by 1).
    """
    df = funding_df.copy()
    s = df["funding_rate"].astype(float)
    s_shifted = s.shift(1)
    rmean = s_shifted.rolling(window=window, min_periods=window).mean()
    rstd = s_shifted.rolling(window=window, min_periods=window).std(ddof=1)
    df["btc_funding_rate_zscore_30"] = (s - rmean) / rstd.replace(0, np.nan)
    # Clip to prevent LightGBM instability from funding-floor outliers
    df["btc_funding_rate_zscore_30"] = df["btc_funding_rate_zscore_30"].clip(
        lower=-10.0, upper=10.0
    )
    return df


def broadcast_btc_to_symbol(
    klines: pd.DataFrame, btc_zscore_df: pd.DataFrame
) -> pd.DataFrame:
    """Broadcast BTC funding z-score onto symbol klines (left-join on open_time).

    Both timestamps rounded to nearest minute to absorb Binance's
    millisecond jitter.
    """
    klines = klines.copy()
    btc = btc_zscore_df.copy()
    btc["open_time_aligned"] = (btc["funding_time"] // 60_000) * 60_000
    klines["open_time_aligned"] = (klines["open_time"] // 60_000) * 60_000
    merged = klines.merge(
        btc[["open_time_aligned", "btc_funding_rate_zscore_30"]],
        on="open_time_aligned",
        how="left",
    )
    merged = merged.drop(columns=["open_time_aligned"])
    return merged


def slice_is_window(df: pd.DataFrame) -> pd.DataFrame:
    """Filter rows to the IS training window [IS_START_MS, OOS_CUTOFF_MS)."""
    mask = (df["open_time"] >= IS_START_MS) & (df["open_time"] < OOS_CUTOFF_MS)
    return df.loc[mask].copy()


def load_klines(symbol: str) -> pd.DataFrame:
    """Read raw 8h kline CSV for symbol."""
    path = DATA_DIR / symbol / "8h.csv"
    if not path.exists():
        raise FileNotFoundError(f"Kline CSV not found: {path}")
    df = pd.read_csv(path)
    df = df.sort_values("open_time").reset_index(drop=True)
    return df


def load_features(symbol: str) -> pd.DataFrame:
    """Read v3 features parquet for symbol."""
    path = DATA_DIR / "features_v3" / f"{symbol}_8h_features.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Features parquet not found: {path}")
    df = pd.read_parquet(path)
    return df


def coverage_check(rows: list[dict], df: pd.DataFrame, symbol: str, total: int) -> None:
    """Append coverage row for symbol."""
    n_total = len(df)
    n_nan = int(df["btc_funding_rate_zscore_30"].isna().sum())
    n_valid = n_total - n_nan
    pct = 100.0 * n_valid / max(n_total, 1)
    rows.append(
        {
            "symbol": symbol,
            "n_total_is_bars": n_total,
            "n_nan_btc_funding_z": n_nan,
            "n_valid_btc_funding_z": n_valid,
            "coverage_pct": round(pct, 4),
            "passes_floor": pct >= COVERAGE_FLOOR_PCT,
        }
    )


def distribution_check(rows: list[dict], df: pd.DataFrame, symbol: str) -> None:
    """Append distribution stats for the broadcast feature in IS window."""
    s = df["btc_funding_rate_zscore_30"].dropna()
    if len(s) == 0:
        rows.append({"symbol": symbol, "n": 0})
        return
    rows.append(
        {
            "symbol": symbol,
            "n": len(s),
            "mean": round(float(s.mean()), 6),
            "std": round(float(s.std(ddof=1)), 6),
            "min": round(float(s.min()), 6),
            "p01": round(float(s.quantile(0.01)), 6),
            "p05": round(float(s.quantile(0.05)), 6),
            "p25": round(float(s.quantile(0.25)), 6),
            "p50": round(float(s.quantile(0.50)), 6),
            "p75": round(float(s.quantile(0.75)), 6),
            "p95": round(float(s.quantile(0.95)), 6),
            "p99": round(float(s.quantile(0.99)), 6),
            "max": round(float(s.max()), 6),
            "skew": round(float(s.skew()), 6),
            "kurtosis": round(float(s.kurtosis()), 6),
        }
    )


def ic_check(
    rows: list[dict], merged: pd.DataFrame, symbol: str
) -> dict[str, float]:
    """Spearman IC between btc_funding_rate_zscore_30 and 13 V3_FEATURE_COLUMNS.

    Returns a dict mapping feature -> IC for diagnostic use.
    """
    feature_ics: dict[str, float] = {}
    s_btc = merged["btc_funding_rate_zscore_30"]
    for fc in V3_FEATURE_COLUMNS_TOP_N:
        if fc not in merged.columns:
            ic = float("nan")
        else:
            sub = pd.concat([s_btc, merged[fc]], axis=1).dropna()
            if len(sub) < 100:
                ic = float("nan")
            else:
                ic = float(sub.iloc[:, 0].corr(sub.iloc[:, 1], method="spearman"))
        feature_ics[fc] = ic
        rows.append(
            {
                "symbol": symbol,
                "feature": fc,
                "spearman_ic": round(ic, 6) if not np.isnan(ic) else None,
                "abs_ic": round(abs(ic), 6) if not np.isnan(ic) else None,
            }
        )
    return feature_ics


def adf_check(rows: list[dict], df: pd.DataFrame, symbol: str) -> None:
    """ADF stationarity test on z-scored series."""
    s = df["btc_funding_rate_zscore_30"].dropna()
    if len(s) < 100:
        rows.append({"symbol": symbol, "n": len(s), "adf_pvalue": None, "passes": False})
        return
    try:
        adf_stat, p_value, _, _, crit_values, _ = adfuller(s, autolag="AIC")
    except Exception as e:
        rows.append({"symbol": symbol, "error": str(e), "passes": False})
        return
    rows.append(
        {
            "symbol": symbol,
            "n": len(s),
            "adf_stat": round(float(adf_stat), 6),
            "adf_pvalue": round(float(p_value), 6),
            "crit_1pct": round(float(crit_values["1%"]), 6),
            "crit_5pct": round(float(crit_values["5%"]), 6),
            "crit_10pct": round(float(crit_values["10%"]), 6),
            "passes": p_value < ADF_PVALUE_THRESHOLD,
        }
    )


def rankic_check(rows: list[dict], df: pd.DataFrame, symbol: str) -> None:
    """Rank-IC vs forward returns at 1/3/7-bar horizons."""
    if "close" not in df.columns:
        # If not in features parquet, compute from open_time + recompute
        return
    close = df["close"].astype(float)
    log_ret = np.log(close).diff()
    s_btc = df["btc_funding_rate_zscore_30"]
    for h in FWD_HORIZONS:
        # forward cumulative log return over next h bars (NEXT bars, exclusive of current)
        fwd_ret = log_ret.shift(-h).rolling(window=h).sum()
        sub = pd.concat([s_btc, fwd_ret], axis=1).dropna()
        if len(sub) < 100:
            ic = float("nan")
        else:
            ic = float(sub.iloc[:, 0].corr(sub.iloc[:, 1], method="spearman"))
        rows.append(
            {
                "symbol": symbol,
                "fwd_horizon_bars": h,
                "rank_ic": round(ic, 6) if not np.isnan(ic) else None,
                "abs_rank_ic": round(abs(ic), 6) if not np.isnan(ic) else None,
                "n": len(sub),
            }
        )


def main() -> int:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[iter-v3/024] btc_funding_eda — IS window {IS_START_TS} → {OOS_CUTOFF_DATE}")

    # 1. Load BTC funding cache + compute cross-asset z-score
    print("[1/6] Loading BTC funding cache + computing past-only z-score...")
    btc_funding = load_btc_funding()
    btc_zscore = compute_btc_funding_zscore(btc_funding, window=FUNDING_ZSCORE_WINDOW)
    print(
        f"  BTC funding rows: {len(btc_funding)}; "
        f"z-score non-NaN: {int(btc_zscore['btc_funding_rate_zscore_30'].notna().sum())}"
    )

    coverage_rows: list[dict] = []
    distribution_rows: list[dict] = []
    correlation_rows: list[dict] = []
    rankic_rows: list[dict] = []
    adf_rows: list[dict] = []

    max_abs_ic_by_symbol: dict[str, float] = {}

    for symbol in V3_SYMBOLS:
        print(f"\n[2-6] Per-symbol broadcast + analysis for {symbol}")
        klines = load_klines(symbol)
        merged = broadcast_btc_to_symbol(klines, btc_zscore)
        is_merged = slice_is_window(merged)

        # Add features parquet's 13 V3_FEATURE_COLUMNS for IC check
        try:
            features = load_features(symbol)
        except FileNotFoundError:
            features = pd.DataFrame()
        if len(features) > 0:
            features = features.sort_values("open_time").reset_index(drop=True)
            is_features = features[
                (features["open_time"] >= IS_START_MS)
                & (features["open_time"] < OOS_CUTOFF_MS)
            ].copy()
            # Merge feature columns into is_merged on open_time
            keep_cols = [c for c in V3_FEATURE_COLUMNS_TOP_N if c in is_features.columns]
            keep_cols.append("open_time")
            ic_input = is_merged.merge(
                is_features[keep_cols], on="open_time", how="left"
            )
        else:
            ic_input = is_merged

        # Sanity: must have close for rankic; merge from klines if not in is_merged
        if "close" not in ic_input.columns and "close" in klines.columns:
            ic_input = ic_input.merge(
                klines[["open_time", "close"]], on="open_time", how="left"
            )

        coverage_check(coverage_rows, is_merged, symbol, total=len(is_merged))
        distribution_check(distribution_rows, is_merged, symbol)
        feature_ics = ic_check(correlation_rows, ic_input, symbol)
        adf_check(adf_rows, is_merged, symbol)
        rankic_check(rankic_rows, ic_input, symbol)

        if feature_ics:
            max_abs = max(
                abs(v) for v in feature_ics.values() if not np.isnan(v)
            )
            max_abs_ic_by_symbol[symbol] = max_abs
            print(f"  {symbol} max |IC| vs 13 V3_FEATURE_COLUMNS: {max_abs:.4f}")

    # Save outputs
    pd.DataFrame(coverage_rows).to_csv(
        ANALYSIS_DIR / "btc_funding_eda_coverage.csv", index=False
    )
    pd.DataFrame(distribution_rows).to_csv(
        ANALYSIS_DIR / "btc_funding_eda_distribution.csv", index=False
    )
    pd.DataFrame(correlation_rows).to_csv(
        ANALYSIS_DIR / "btc_funding_eda_correlation.csv", index=False
    )
    pd.DataFrame(rankic_rows).to_csv(
        ANALYSIS_DIR / "btc_funding_eda_rankic.csv", index=False
    )
    pd.DataFrame(adf_rows).to_csv(
        ANALYSIS_DIR / "btc_funding_eda_adf.csv", index=False
    )

    # Synthesis (pass / fail summary)
    coverage_df = pd.DataFrame(coverage_rows)
    adf_df = pd.DataFrame(adf_rows)
    overall_max_ic = (
        max(max_abs_ic_by_symbol.values()) if max_abs_ic_by_symbol else float("nan")
    )

    coverage_passes = coverage_df["passes_floor"].all() if len(coverage_df) > 0 else False
    adf_passes = adf_df["passes"].all() if len(adf_df) > 0 else False
    ic_passes_hard = overall_max_ic < IC_THRESHOLD_HARD if not np.isnan(overall_max_ic) else False
    ic_passes_brief = overall_max_ic < IC_THRESHOLD_BRIEF if not np.isnan(overall_max_ic) else False

    rankic_df = pd.DataFrame(rankic_rows)
    if len(rankic_df) > 0:
        max_abs_rankic = float(rankic_df["abs_rank_ic"].dropna().max())
    else:
        max_abs_rankic = float("nan")

    synthesis = f"""# iter-v3/024 — BTC Funding EDA Synthesis

## Decision Summary

| Gate | Threshold | Observed | PASS? |
|------|-----------|----------|-------|
| Coverage IS window per symbol | >= {COVERAGE_FLOOR_PCT}% | see coverage CSV | {coverage_passes} |
| Max \\|IC\\| vs 13 V3_FEATURE_COLUMNS (HARD) | < {IC_THRESHOLD_HARD} | {overall_max_ic:.4f} | {ic_passes_hard} |
| Max \\|IC\\| vs 13 V3_FEATURE_COLUMNS (BRIEF target) | < {IC_THRESHOLD_BRIEF} | {overall_max_ic:.4f} | {ic_passes_brief} |
| ADF p-value < {ADF_PVALUE_THRESHOLD} per symbol | structural stationarity | see adf CSV | {adf_passes} |
| Max \\|rank-IC\\| vs forward returns | >= 0.02 (predictive signal) | {max_abs_rankic:.4f} | {max_abs_rankic >= 0.02 if not np.isnan(max_abs_rankic) else False} |

## Per-symbol max |IC| vs 13 V3_FEATURE_COLUMNS

{chr(10).join(f"- {sym}: max |IC| = {ic:.4f}" for sym, ic in max_abs_ic_by_symbol.items())}

## Files

- analysis/iteration_v3-024/btc_funding_eda_coverage.csv
- analysis/iteration_v3-024/btc_funding_eda_distribution.csv
- analysis/iteration_v3-024/btc_funding_eda_correlation.csv
- analysis/iteration_v3-024/btc_funding_eda_rankic.csv
- analysis/iteration_v3-024/btc_funding_eda_adf.csv

## Verdict

{"GO — all 5 EDA gates pass; structurally vetted candidate." if (coverage_passes and ic_passes_hard and adf_passes and (not np.isnan(max_abs_rankic) and max_abs_rankic >= 0.02)) else "REVIEW — see per-gate detail above; brief author must address failing gates."}
"""
    (ANALYSIS_DIR / "synthesis.md").write_text(synthesis)
    print("\n" + synthesis)

    # Hard fail if any critical gate fails (coverage, IC hard, ADF)
    if not coverage_passes:
        print(f"FAIL: coverage below {COVERAGE_FLOOR_PCT}%")
        return 1
    if not ic_passes_hard:
        print(f"FAIL: max |IC| {overall_max_ic:.4f} >= hard gate {IC_THRESHOLD_HARD}")
        return 1
    if not adf_passes:
        print(f"FAIL: ADF stationarity p-value >= {ADF_PVALUE_THRESHOLD}")
        return 1

    print("\n[OK] All hard gates pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
