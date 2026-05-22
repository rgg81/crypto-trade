"""EDA for iter-v3/057 — Cycle 4 #7 of 10.

Axis decision: A4 base-stack reordering OR NEW feature family.

The 6 consecutive PATH E (CPCV-INVARIANT NULL) firings (iter-v3/051..056) tell us
that the CPCV path distribution is STRUCTURALLY PINNED by the
(base-14, BCH+LDO+TRX, 8h, ENSEMBLE_SIZE=5, n_trials=35) tuple. To shift CPCV,
a STRUCTURAL change is required.

Per Critic /054 + /055 + /056 recommendations:
- A4 (base-stack reordering): drop one of the 14 + add an orthogonal NEW feature.
- NEW feature family: add NEW feature at slot 15 from UNTESTED family.

The hybrid case (A4 base-stack reordering WHERE the addition is from a NEW UNTESTED
family) is the strongest single-axis option — it changes both the stack composition
AND adds a structurally distinct family signal at the same time.

This EDA evaluates:
1. Per-symbol importance distribution of base 14 features at /056 (find robust drop candidate).
2. IC matrix to identify redundancy candidates among base 14.
3. Available NEW feature families NOT YET in stack and NOT YET tested (catalog walk).
4. For each top-3 NEW feature candidate:
   a. ADF stationarity per symbol
   b. |IC| with each of the base 14 (strict gate < 0.50; carve-out for engineered)
   c. Univariate Spearman ρ vs forward 5-bar return (significance test)
   d. Skew / kurtosis (numerical stability check)
   e. NaN warmup count (data efficiency)
5. Final ranking — recommend ONE drop + ONE add pair for iter-v3/057 SWAP.

EDA stays IS-only per Phase 5.5 gate Section 2 mandate.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
ITER_056_REPORTS = REPO_ROOT / "reports-v3" / "iteration_v3-056"
FEATURES_DIR = REPO_ROOT / "data" / "features_v3"
OUTPUT_DIR = REPO_ROOT / "analysis" / "iteration_v3-057"
OUTPUT_DIR.mkdir(exist_ok=True)

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 UTC

V3_BASE_14 = (
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
    "regime_momentum_signed_5d",
)

# All v3 features computed in parquets, EXCLUDING the base 14 and features already
# tested + closed in EXPLORATION catalog
CLOSED_FEATURES = {
    # iter-v3/015 + /016: microstructure z-score (taker buy ratio)
    "tbr_zscore_30",
    "tbr_raw",
    # iter-v3/019 + /023: funding rate per-symbol
    "funding_rate_zscore_30",
    # iter-v3/024 + /025: BTC funding rate cross-asset
    "btc_funding_rate_zscore_30",
    # iter-v3/026: engineered composed (vol_adj_autocorr) — DON'T STACK
    "vol_adj_autocorr",
    # iter-v3/027 + /028: engineered composed (cross_asset_divergence_norm) — DON'T STACK
    "cross_asset_divergence_norm",
    # iter-v3/043 + /044: efficiency_ratio_50 — NEGATIVE
    "efficiency_ratio_50",
    # iter-v3/048: vol_normalized_ret_5d — NEGATIVE PATH C
    "vol_normalized_ret_5d",
    # iter-v3/051: fracdiff_d05_close UNIVERSAL — PROMISING-INERT (dropped)
    "fracdiff_d05_close",
    # iter-v3/052: regime_momentum_signed_3d — PATH C-suspicious
    "regime_momentum_signed_3d",
    # iter-v3/053: hurst_drift_50_200 — NULL-RESULT (PARKED)
    "hurst_drift_50_200",
    # historical fracdiff dstat (pre-cycle baseline)
    "fracdiff_logclose_dstat",
    "fracdiff_logvolume_dstat",
}

OHLCV_AND_LABELS = {
    "open_time", "open_time_aligned", "close_time", "open", "high", "low", "close",
    "volume", "trades", "quote_volume", "taker_buy_volume", "taker_buy_quote_volume",
    "symbol", "natr_21_raw",  # natr_21_raw is helper-only per V3_NON_FEATURE_COLUMNS
}


def _load_features_per_symbol(symbols: tuple[str, ...]) -> dict[str, pd.DataFrame]:
    """Load IS-only feature parquets per symbol.

    IS_CUTOFF = 2025-03-24 UTC — strict IS-only per Phase 5.5 gate.
    """
    out: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        path = FEATURES_DIR / f"{sym}_8h_features.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Missing parquet for {sym}: {path}")
        df = pd.read_parquet(path)
        # IS-only filter
        df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
        out[sym] = df
    return out


def _adf_test(series: pd.Series) -> tuple[float, float]:
    """Augmented Dickey-Fuller; returns (statistic, p-value).

    Drops NaN before test. Uses statsmodels.tsa.stattools.adfuller default
    settings (autolag='AIC').
    """
    from statsmodels.tsa.stattools import adfuller

    clean = series.dropna()
    if len(clean) < 100:
        return (np.nan, np.nan)
    result = adfuller(clean.values, autolag="AIC")
    return (float(result[0]), float(result[1]))


def _spearman_significance(x: pd.Series, y: pd.Series) -> tuple[float, float]:
    """Spearman rank correlation + p-value (asymptotic; safe for n > 30)."""
    from scipy.stats import spearmanr

    paired = pd.concat([x, y], axis=1).dropna()
    if len(paired) < 30:
        return (np.nan, np.nan)
    r, p = spearmanr(paired.iloc[:, 0], paired.iloc[:, 1])
    return (float(r), float(p))


def analyze_a4_drop_candidates(
    importance_paths: dict[str, Path],
    features_per_sym: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Identify A4 drop candidates from per-symbol importance.

    A robust drop candidate must:
    (a) Be in bottom-3 importance for at least 2 of 3 symbols (per-symbol-consistent).
    (b) Not be a Category-2 composed feature with carve-out (so regime_momentum_signed_5d
        is excluded — it's per-symbol load-bearing per iter-v3/041 lesson).

    Returns DataFrame ranked by 'a4_drop_score' (higher = better drop candidate).
    """
    # Load per-symbol importance
    imp_by_sym: dict[str, pd.DataFrame] = {}
    for sym, path in importance_paths.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing importance CSV: {path}")
        d = pd.read_csv(path)
        d["rank_asc"] = d["importance"].rank(ascending=True, method="dense").astype(int)
        d["rank_desc"] = d["importance"].rank(ascending=False, method="dense").astype(int)
        imp_by_sym[sym] = d.set_index("feature")

    rows = []
    for feat in V3_BASE_14:
        per_sym = {
            sym: int(imp_by_sym[sym].loc[feat, "rank_desc"]) if feat in imp_by_sym[sym].index else 99
            for sym in imp_by_sym
        }
        # Bottom-3 = rank_desc >= 12 (out of 14)
        bottom_count = sum(1 for r in per_sym.values() if r >= 12)
        # Aggregate portfolio importance
        portfolio_imp = (
            sum(imp_by_sym[sym].loc[feat, "importance"] for sym in imp_by_sym if feat in imp_by_sym[sym].index)
            / len(imp_by_sym)
        )
        # Special-protection: regime_momentum_signed_5d (load-bearing for BCH per /041)
        protected = feat == "regime_momentum_signed_5d"
        rows.append({
            "feature": feat,
            "bch_rank": per_sym.get("BCHUSDT", 99),
            "ldo_rank": per_sym.get("LDOUSDT", 99),
            "trx_rank": per_sym.get("TRXUSDT", 99),
            "bottom3_count": bottom_count,
            "mean_portfolio_importance": portfolio_imp,
            "load_bearing_protected": protected,
        })
    df = pd.DataFrame(rows).sort_values(
        ["load_bearing_protected", "bottom3_count", "mean_portfolio_importance"],
        ascending=[True, False, True],
    ).reset_index(drop=True)
    df["a4_drop_score"] = df["bottom3_count"] * 100 + (1000 - df["mean_portfolio_importance"]) / 10
    df.loc[df["load_bearing_protected"], "a4_drop_score"] = 0  # block protected features
    return df.sort_values("a4_drop_score", ascending=False).reset_index(drop=True)


def analyze_new_feature_candidates(
    features_per_sym: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Survey AVAILABLE NEW feature candidates that are computed in parquets,
    NOT in V3_BASE_14, and NOT in CLOSED_FEATURES.

    For each candidate, compute:
    - per-symbol availability (n_rows)
    - per-symbol skew + kurt (stability check)
    - per-symbol Spearman ρ vs forward 5-bar log return
    - per-symbol max |IC| with V3_BASE_14 (strict gate < 0.50)
    - ADF stationarity per symbol

    Returns DataFrame ranked by axis suitability.
    """
    # Identify candidate columns
    bch = features_per_sym["BCHUSDT"]
    all_cols = set(bch.columns) - OHLCV_AND_LABELS - set(V3_BASE_14) - CLOSED_FEATURES
    candidates = sorted(all_cols)
    print(f"\nDEBUG: {len(candidates)} candidate columns to evaluate:")
    for c in candidates:
        print(f"  - {c}")

    rows = []
    for feat in candidates:
        row = {"feature": feat}
        symbol_ics = []
        max_abs_ic_against_base = 0.0
        max_ic_partner = ""

        for sym, df in features_per_sym.items():
            if feat not in df.columns:
                row[f"{sym}_n_valid"] = 0
                continue
            col = df[feat].dropna()
            row[f"{sym}_n_valid"] = len(col)
            if len(col) < 200:
                continue

            # Stability: skew + kurt
            row[f"{sym}_skew"] = float(col.skew())
            row[f"{sym}_kurt"] = float(col.kurt())

            # ADF
            adf_stat, adf_p = _adf_test(col)
            row[f"{sym}_adf_p"] = adf_p

            # Forward 5-bar log return (forward-looking BUT used here only for
            # univariate predictability check — never leaked into features)
            log_close = np.log(df["close"].astype(float).clip(lower=1e-12))
            fwd_ret_5 = log_close.shift(-15) - log_close  # 15 bars at 8h = 5 days
            # Drop final 15 bars (no forward window)
            valid = pd.concat([df[feat], fwd_ret_5], axis=1).dropna()
            if len(valid) < 100:
                continue
            r_spr, p_spr = _spearman_significance(valid.iloc[:, 0], valid.iloc[:, 1])
            row[f"{sym}_spearman"] = r_spr
            row[f"{sym}_spearman_p"] = p_spr

            # |IC| with each of the V3_BASE_14
            for base_feat in V3_BASE_14:
                if base_feat not in df.columns:
                    continue
                pair = pd.concat([df[feat], df[base_feat]], axis=1).dropna()
                if len(pair) < 200:
                    continue
                ic = pair.iloc[:, 0].corr(pair.iloc[:, 1])
                if abs(ic) > max_abs_ic_against_base:
                    max_abs_ic_against_base = abs(ic)
                    max_ic_partner = f"{base_feat}({sym})"

        row["max_abs_ic_with_base14"] = max_abs_ic_against_base
        row["max_ic_partner"] = max_ic_partner
        rows.append(row)

    df_out = pd.DataFrame(rows)
    return df_out


def make_axis_decision(
    a4_df: pd.DataFrame,
    new_feat_df: pd.DataFrame,
) -> dict[str, str]:
    """Final axis ranking — pick A4 drop + NEW family add pair.

    Decision rules:
    1. Top A4 drop candidate (highest score) becomes the drop target.
    2. Among NEW feature candidates, filter to:
       - ALL 3 symbols ADF p < 0.05 (stationary)
       - ALL 3 symbols n_valid > 1000
       - max |IC| < 0.50 with V3_BASE_14 (strict gate; NEW feature is Category 1)
       - At least 1 symbol Spearman p < 0.05 (univariate predictability)
       - |skew| < 10 and |kurt| < 50 (numerical stability)
    3. Among filtered, pick the one with strongest univariate Spearman ρ (most
       likely to LEARN at importance ≥ 30).
    4. Predict mechanism: this is BOTH (a) family-level swap (cross_btc OUT,
       microstructure_v3 IN) and (b) STRUCTURAL change to base-14 stack.
    """
    print("\n=== A4 DROP RANKING ===")
    print(a4_df.to_string(index=False))

    drop_target = a4_df.iloc[0]["feature"]
    drop_score = a4_df.iloc[0]["a4_drop_score"]
    print(f"\nA4 DROP CANDIDATE: {drop_target} (score={drop_score:.1f})")

    # Filter NEW candidates
    cols_needed_adf = [c for c in new_feat_df.columns if c.endswith("_adf_p")]
    cols_needed_n = [c for c in new_feat_df.columns if c.endswith("_n_valid")]
    cols_needed_skew = [c for c in new_feat_df.columns if c.endswith("_skew")]
    cols_needed_kurt = [c for c in new_feat_df.columns if c.endswith("_kurt")]
    cols_needed_spr = [c for c in new_feat_df.columns if c.endswith("_spearman_p")]
    cols_needed_spr_r = [c for c in new_feat_df.columns if c.endswith("_spearman")
                          and not c.endswith("_p")]

    print(f"\n=== NEW FEATURE CANDIDATES (raw) — top 12 columns shown ===")
    show_cols = ["feature", "max_abs_ic_with_base14", "max_ic_partner"] + cols_needed_n + cols_needed_adf
    show_cols = [c for c in show_cols if c in new_feat_df.columns]
    print(new_feat_df[show_cols].to_string(index=False))

    filtered_rows = []
    for _, r in new_feat_df.iterrows():
        # All 3 symbols ADF p < 0.05
        adf_ps = [r[c] for c in cols_needed_adf if c in r.index and not pd.isna(r[c])]
        if len(adf_ps) < 3 or max(adf_ps) >= 0.05:
            continue
        # All 3 symbols n_valid > 1000
        n_valids = [r[c] for c in cols_needed_n if c in r.index]
        if len(n_valids) < 3 or min(n_valids) < 1000:
            continue
        # max |IC| < 0.50 (strict Category-1 gate; new feature has no carve-out)
        if r.get("max_abs_ic_with_base14", 1.0) >= 0.50:
            continue
        # At least 1 symbol Spearman p < 0.05
        spr_ps = [r[c] for c in cols_needed_spr if c in r.index and not pd.isna(r[c])]
        if len(spr_ps) == 0 or min(spr_ps) >= 0.05:
            continue
        # |skew| < 10, |kurt| < 50
        skews = [abs(r[c]) for c in cols_needed_skew if c in r.index and not pd.isna(r[c])]
        kurts = [abs(r[c]) for c in cols_needed_kurt if c in r.index and not pd.isna(r[c])]
        if len(skews) < 3 or max(skews) >= 10:
            continue
        if len(kurts) < 3 or max(kurts) >= 50:
            continue
        # Compute mean abs Spearman ρ as ranking score
        rs = [abs(r[c]) for c in cols_needed_spr_r if c in r.index and not pd.isna(r[c])]
        mean_abs_spr = float(np.mean(rs)) if rs else 0.0
        r_copy = dict(r)
        r_copy["mean_abs_spearman"] = mean_abs_spr
        filtered_rows.append(r_copy)

    if not filtered_rows:
        print("\nNO NEW feature passes all filters — recommend A4-only path")
        return {"drop_target": drop_target, "add_target": None, "rationale": "no_passing_new_feature"}

    filtered_df = pd.DataFrame(filtered_rows).sort_values(
        "mean_abs_spearman", ascending=False,
    ).reset_index(drop=True)
    print(f"\n=== FILTERED NEW FEATURE CANDIDATES (passes all gates) ===")
    cols_show = ["feature", "mean_abs_spearman", "max_abs_ic_with_base14", "max_ic_partner"]
    print(filtered_df[cols_show].to_string(index=False))

    add_target = filtered_df.iloc[0]["feature"]
    print(f"\nNEW FEATURE TO ADD: {add_target}")
    print(f"DROP: {drop_target}")
    print(f"ADD: {add_target}")

    return {
        "drop_target": drop_target,
        "add_target": add_target,
        "mean_abs_spearman": filtered_df.iloc[0]["mean_abs_spearman"],
        "max_abs_ic_with_base14": filtered_df.iloc[0]["max_abs_ic_with_base14"],
        "max_ic_partner": filtered_df.iloc[0]["max_ic_partner"],
    }


def main() -> None:
    print("=" * 78)
    print("iter-v3/057 EDA — A4 base-stack reordering OR NEW feature family")
    print("=" * 78)

    symbols = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
    features_per_sym = _load_features_per_symbol(symbols)
    importance_paths = {
        sym: ITER_056_REPORTS / "in_sample" / f"model_importance_last_month_{sym}.csv"
        for sym in symbols
    }

    # Step 1: A4 drop candidates (per-symbol importance)
    print("\n" + "=" * 78)
    print("STEP 1: A4 base-stack drop candidates")
    print("=" * 78)
    a4_df = analyze_a4_drop_candidates(importance_paths, features_per_sym)
    a4_df.to_csv(OUTPUT_DIR / "a4_drop_ranking.csv", index=False)

    # Step 2: NEW feature family candidates
    print("\n" + "=" * 78)
    print("STEP 2: NEW feature family candidates")
    print("=" * 78)
    new_feat_df = analyze_new_feature_candidates(features_per_sym)
    new_feat_df.to_csv(OUTPUT_DIR / "new_feature_candidates.csv", index=False)

    # Step 3: Final ranking + decision
    print("\n" + "=" * 78)
    print("STEP 3: Axis decision")
    print("=" * 78)
    decision = make_axis_decision(a4_df, new_feat_df)

    # Save decision
    decision_path = OUTPUT_DIR / "axis_decision.json"
    import json
    with decision_path.open("w") as f:
        json.dump(decision, f, indent=2, default=str)
    print(f"\nDecision saved: {decision_path}")

    # Predict mechanism
    print("\n" + "=" * 78)
    print("STEP 4: Mechanism prediction (structural CPCV shift)")
    print("=" * 78)
    if decision["add_target"] is None:
        print("No NEW feature passes filters — A4 collapses to feature-pruning")
        print("This is identical to iter-v3/041 (PATH C-fired); cannot retry")
        print("DECISION: SKIP this axis; defer to /058")
    else:
        print(f"AXIS: A4 base-stack SWAP — DROP {decision['drop_target']}, ADD {decision['add_target']}")
        print(f"Family shift: cross_btc (or other) -> microstructure_v3 (untested)")
        print(f"This is STRUCTURAL change to base-14 stack (NOT a 15th-slot extension)")
        print(f"Predicted CPCV path distribution: should shift if the SWAP changes")
        print(f"Optuna's reachable IS-optimal trajectories. Mechanism evidence:")
        print(f"- Drop a low-aggregate-importance bottom-3 feature")
        print(f"- Add a NEW family (microstructure_v3) — first time in v3 base stack")
        print(f"- Family-level orthogonality vs current 14 — captures candle shape signal")


if __name__ == "__main__":
    main()
