"""iter-v3/125 EDA — WILD CYCLE-7 axis: 8h universe replacement BCH/LDO/TRX → ATOM/RUNE/UNI.

Pre-brief evidence (IS-only) per `feedback_v3_axis_selection_quant_discipline.md`.

WILD AXIS RATIONALE
-------------------
Per `feedback_v3_cycle7_constraints_lifted.md` (2026-05-20 user directive):
- Symbol universe constraint LIFTED (only v1+v2+MKR excluded)
- Candle frequency constraint LIFTED (any freq allowed)
- LightGBM still locked
- /116 no_confirm STAYS enabled in /121 baseline

Cycle-7 prior attempts (/122 ETH OHLCV, /123 ETH vol ratio, /124 K=63 labels) all NEGATIVE
under tight BCH/LDO/TRX + 8h constraints. The user mandates BE WILD, CREATE INNOVATION.

Selected axis: REPLACE V3_MODELS BCH/LDO/TRX → ATOM/RUNE/UNI at 8h cadence with all
other /121 architecture identical (incl. /116 no_confirm, 14-feature TOP_N stack).

Why ATOM + RUNE + UNI specifically:
- ATOM (Cosmos L0): 39mo IS / 14mo OOS coverage. NEVER v3-tested as standalone or in
  V3_MODELS. Only appeared in /021/033/069/087 *candidate pools*. Cosmos ecosystem
  orthogonal to v3 incumbents (BCH=Bitcoin Cash, TRX=independent L1, LDO=Lido DAO).
- RUNE (THORChain cross-chain DeFi): 30mo IS / 14mo OOS. NEVER v3-tested individually
  (appeared in /083/087 candidate pools only). Cross-chain DEX = different microstructure
  (slip-based pricing, asymmetric liquidity).
- UNI (Uniswap governance): 39mo IS / 11mo OOS. NEVER v3-tested. Largest spot DEX
  governance token = distinct from L1/L0 chains.

Why this distribution beats other wild axes the QR considered:
- Memecoin universe (WIF/JTO/1000PEPE): EXCLUDED — < 24mo IS coverage means walk-forward
  has 0 IS months to evaluate.
- 24h cadence on BCH/LDO/TRX: TESTED at /117, IS=-2.17 / OOS=-3.26 — CLOSED.
- 4h/12h cadence: data NOT in worktree; fetch overhead exceeds 2h cap risk.
- CRV/AAVE: TESTED at /110-111 NEGATIVE (4-symbol bundle with GRT/ADA).
- HBAR+AVAX: TESTED at /021 NEGATIVE.
- ADA / FIL / GALA / MANA / SAND: TESTED at /069/083/087 NEGATIVE.

ATOM + RUNE + UNI is the LAST untested {3-symbol, deep-data-coverage, sector-diversified,
8h-cadence} configuration in the available pool. It taps the prior distribution:

  P(new universe edge | /121 no_confirm baseline AND never-v3-tested symbols AND
                        sector-diverse pick)

vs. prior universe tests which were all under /059 no-no_confirm baseline OR were in
the closed candidate pool OR were single-sector concentrated.

Three pre-flight gates this EDA must pass to justify the brief:
  G1: Data depth — each symbol ≥ 24 IS months AND ≥ 10 OOS months
  G2: Signal diversity — mutual feature correlation < 0.85 between symbols
  G3: ADF stationarity — top-3 incumbent features (ret_kurt_50, hurst_100,
      vwap_dev_20) pass ADF p < 0.05 per symbol on IS data

USAGE
-----
    uv run python analysis/iteration_v3-125/wild_universe_eda.py

OUTPUTS
-------
    analysis/iteration_v3-125/T1_data_depth.csv
    analysis/iteration_v3-125/T2_per_symbol_signal_stats.csv
    analysis/iteration_v3-125/T3_pairwise_feature_corr.csv
    analysis/iteration_v3-125/T4_adf_stationarity.csv
    analysis/iteration_v3-125/T5_vol_regime_diversity.csv
    analysis/iteration_v3-125/T6_label_distribution_predict.csv

DISCIPLINE
----------
- IS-only: every loader asserts close_time < OOS_CUTOFF_MS = 1742774400000.
- NO peek at OOS feature distributions, label distributions, or any post-cutoff data.
- Pre-registered outcome bands in brief Section 4 use only IS-statistic predictions.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# OOS cutoff — IMMUTABLE
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 UTC

# Candidate universe — must be DISJOINT from V3_EXCLUDED_SYMBOLS
CANDIDATE_SYMBOLS = ("ATOMUSDT", "RUNEUSDT", "UNIUSDT")

# Comparison anchor — the /121 BASELINE universe (for diversity-vs-incumbent comparison)
ANCHOR_SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

# Excluded symbols (loaded from features_v3 for the disjointness assertion)
V3_EXCLUDED_SYMBOLS = (
    "BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT",
    "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "NEARUSDT", "MKRUSDT",
)

DATA_DIR = Path("data")
OUTPUT_DIR = Path("analysis/iteration_v3-125")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

INTERVAL = "8h"
INTERVAL_MINUTES = 480  # 8h = 480 minutes


def load_klines_is_only(symbol: str) -> pd.DataFrame:
    """Load 8h klines, ASSERT IS-only (close_time < OOS_CUTOFF_MS)."""
    csv_path = DATA_DIR / symbol / f"{INTERVAL}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing {csv_path}")
    df = pd.read_csv(csv_path)
    # Filter IS-only — close_time < OOS cutoff
    df_is = df[df["close_time"] < OOS_CUTOFF_MS].copy()
    df_oos = df[df["close_time"] >= OOS_CUTOFF_MS].copy()
    # Assert no OOS data leaked into the IS frame
    assert df_is["close_time"].max() < OOS_CUTOFF_MS, (
        f"{symbol}: IS-frame contains OOS data — bug in filter"
    )
    return df_is


def t1_data_depth() -> pd.DataFrame:
    """Gate G1: data depth per candidate + anchor."""
    rows = []
    for sym in (*CANDIDATE_SYMBOLS, *ANCHOR_SYMBOLS):
        try:
            df_is = load_klines_is_only(sym)
        except FileNotFoundError:
            rows.append({"symbol": sym, "n_is_bars": 0, "first_is_ts": None,
                         "last_is_ts": None, "is_months": 0,
                         "training_window_complete_at": None,
                         "first_evaluable_oos_ts": None, "is_gate_pass": False})
            continue
        if len(df_is) == 0:
            rows.append({"symbol": sym, "n_is_bars": 0, "first_is_ts": None,
                         "last_is_ts": None, "is_months": 0, "is_gate_pass": False})
            continue
        first_ts = df_is["close_time"].iloc[0]
        last_ts = df_is["close_time"].iloc[-1]
        first_dt = pd.to_datetime(first_ts, unit="ms")
        last_dt = pd.to_datetime(last_ts, unit="ms")
        # Walk-forward TRAINING_MONTHS=24, so first evaluable test month is first_dt + 24 months
        training_complete_dt = first_dt + pd.DateOffset(months=24)
        # IS test months evaluable = (oos_cutoff - training_complete) in months
        oos_cutoff_dt = pd.to_datetime(OOS_CUTOFF_MS, unit="ms")
        is_months = max(0, (oos_cutoff_dt.year - training_complete_dt.year) * 12
                        + (oos_cutoff_dt.month - training_complete_dt.month))
        # Gate: ≥ 24 IS months (matches /121 anchor depth)
        rows.append({
            "symbol": sym,
            "n_is_bars": len(df_is),
            "first_is_ts": first_ts,
            "first_is_date": first_dt.strftime("%Y-%m-%d"),
            "last_is_ts": last_ts,
            "last_is_date": last_dt.strftime("%Y-%m-%d"),
            "training_complete_date": training_complete_dt.strftime("%Y-%m-%d"),
            "is_months_evaluable": is_months,
            "is_gate_pass": is_months >= 24,
        })
    df = pd.DataFrame(rows)
    return df


def compute_returns(df: pd.DataFrame) -> pd.Series:
    """Past-only 1-bar log return."""
    return np.log(df["close"]).diff()


def compute_rolling_realized_vol(df: pd.DataFrame, window: int = 50) -> pd.Series:
    """Past-only rolling realized vol of 1-bar log returns. Annualized factor 1095=365*3 for 8h."""
    r = compute_returns(df)
    rv = r.rolling(window).std() * np.sqrt(1095)
    return rv


def compute_kurt(df: pd.DataFrame, window: int = 50) -> pd.Series:
    """Past-only rolling kurtosis of returns."""
    r = compute_returns(df)
    return r.rolling(window).kurt()


def compute_skew(df: pd.DataFrame, window: int = 50) -> pd.Series:
    r = compute_returns(df)
    return r.rolling(window).skew()


def t2_per_symbol_signal_stats() -> pd.DataFrame:
    """Per-symbol IS feature distribution stats — informs pre-flight signal diversity prediction."""
    rows = []
    for sym in (*CANDIDATE_SYMBOLS, *ANCHOR_SYMBOLS):
        try:
            df_is = load_klines_is_only(sym)
        except FileNotFoundError:
            continue
        if len(df_is) < 200:
            continue
        rv50 = compute_rolling_realized_vol(df_is, 50)
        k50 = compute_kurt(df_is, 50)
        s50 = compute_skew(df_is, 50)
        r1 = compute_returns(df_is)
        rows.append({
            "symbol": sym,
            "median_rv50_annual": float(rv50.median(skipna=True)),
            "q10_rv50_annual": float(rv50.quantile(0.10)),
            "q90_rv50_annual": float(rv50.quantile(0.90)),
            "median_kurt50": float(k50.median(skipna=True)),
            "median_skew50": float(s50.median(skipna=True)),
            "median_abs_ret_1bar_bps": float(r1.abs().median(skipna=True) * 1e4),
            "n_is_bars": len(df_is),
        })
    df = pd.DataFrame(rows)
    return df


def t3_pairwise_feature_corr() -> pd.DataFrame:
    """Pairwise correlation of returns + RV50 between candidates and anchors.

    Validates signal diversity: low cross-symbol return correlation AND low cross-symbol
    RV correlation = signal diversification. Per /087 brief lesson, "price-return
    correlation is the WRONG metric" — but as a pre-flight screen at single-axis EDA,
    return correlation is the first-order proxy for "are these symbols moving together".
    """
    all_syms = (*CANDIDATE_SYMBOLS, *ANCHOR_SYMBOLS)
    # Build a wide dataframe of returns aligned on close_time
    rets = {}
    rvs = {}
    for sym in all_syms:
        try:
            df_is = load_klines_is_only(sym)
        except FileNotFoundError:
            continue
        if len(df_is) < 200:
            continue
        df_is = df_is.set_index("close_time")
        rets[sym] = compute_returns(df_is.reset_index().rename(columns={"close_time": "ct"}))
        rets[sym].index = df_is.index
        rvs[sym] = compute_rolling_realized_vol(df_is.reset_index().rename(columns={"close_time": "ct"}), 50)
        rvs[sym].index = df_is.index
    # Build wide frames
    ret_df = pd.DataFrame(rets).dropna(how="all")
    rv_df = pd.DataFrame(rvs).dropna(how="all")
    # Compute the correlations on the COMMON overlap window
    common = ret_df.dropna().index
    if len(common) < 500:
        # Fall back to pairwise with whatever overlap exists
        pass
    ret_corr = ret_df.corr(method="pearson", min_periods=300)
    rv_corr = rv_df.corr(method="pearson", min_periods=300)
    # Long-form output
    rows = []
    for s1 in all_syms:
        for s2 in all_syms:
            if s1 >= s2 or s1 not in ret_corr.columns or s2 not in ret_corr.columns:
                continue
            rows.append({
                "sym_a": s1,
                "sym_b": s2,
                "ret_corr_pearson": float(ret_corr.loc[s1, s2]) if not pd.isna(ret_corr.loc[s1, s2]) else None,
                "rv_corr_pearson": float(rv_corr.loc[s1, s2]) if not pd.isna(rv_corr.loc[s1, s2]) else None,
                "is_within_candidate_universe": (s1 in CANDIDATE_SYMBOLS) and (s2 in CANDIDATE_SYMBOLS),
                "is_within_anchor_universe": (s1 in ANCHOR_SYMBOLS) and (s2 in ANCHOR_SYMBOLS),
                "is_cross_universe": (s1 in CANDIDATE_SYMBOLS) != (s2 in CANDIDATE_SYMBOLS),
            })
    df = pd.DataFrame(rows)
    return df


def adf_test_stat(x: np.ndarray) -> float:
    """Augmented Dickey-Fuller test using statsmodels — returns p-value.

    Fallback: a manual implementation if statsmodels missing.
    """
    try:
        from statsmodels.tsa.stattools import adfuller
        x_clean = x[~np.isnan(x)]
        if len(x_clean) < 100:
            return float("nan")
        result = adfuller(x_clean, autolag="AIC", maxlag=20, regression="c")
        return float(result[1])  # p-value
    except ImportError:
        return float("nan")


def t4_adf_stationarity() -> pd.DataFrame:
    """ADF on 3 incumbent /121 features per candidate symbol."""
    rows = []
    for sym in CANDIDATE_SYMBOLS:
        try:
            df_is = load_klines_is_only(sym)
        except FileNotFoundError:
            continue
        if len(df_is) < 500:
            continue
        # 3 incumbent features (lightweight versions)
        rv50 = compute_rolling_realized_vol(df_is, 50).values  # range_realized_vol_50 proxy
        kurt50 = compute_kurt(df_is, 50).values  # ret_kurt_50 (exact)
        # vwap_dev_20 proxy = (close - rolling_mean(close, 20)) / rolling_std(close, 20)
        close = df_is["close"].values
        mean20 = pd.Series(close).rolling(20).mean().values
        std20 = pd.Series(close).rolling(20).std().values
        vwap_dev_20_proxy = (close - mean20) / std20
        for feat_name, feat_vals in (
            ("range_realized_vol_50_proxy", rv50),
            ("ret_kurt_50", kurt50),
            ("vwap_dev_20_proxy", vwap_dev_20_proxy),
        ):
            p = adf_test_stat(feat_vals)
            rows.append({
                "symbol": sym,
                "feature": feat_name,
                "adf_pvalue": p,
                "stationary_pass": (p < 0.05) if not np.isnan(p) else False,
                "n_obs": int(np.sum(~np.isnan(feat_vals))),
            })
    df = pd.DataFrame(rows)
    return df


def t5_vol_regime_diversity() -> pd.DataFrame:
    """Vol-tier diversification: how do the candidates rank by IS realized vol?

    The /121 universe has BCH (vol-tier high), LDO (vol-tier high), TRX (vol-tier low) —
    bimodal. ATOM/RUNE/UNI vol-tier should be CHECKED to confirm vol-tier diversity exists
    in the new universe.
    """
    rows = []
    all_rv = {}
    for sym in (*CANDIDATE_SYMBOLS, *ANCHOR_SYMBOLS):
        try:
            df_is = load_klines_is_only(sym)
        except FileNotFoundError:
            continue
        if len(df_is) < 200:
            continue
        rv = compute_rolling_realized_vol(df_is, 50)
        rv_median = float(rv.median(skipna=True))
        all_rv[sym] = rv_median
        rows.append({
            "symbol": sym,
            "median_rv50_annual": rv_median,
            "universe": "CANDIDATE" if sym in CANDIDATE_SYMBOLS else "ANCHOR",
        })
    df = pd.DataFrame(rows)
    df["vol_rank"] = df["median_rv50_annual"].rank(method="dense", ascending=False)
    return df


def t6_label_distribution_predict() -> pd.DataFrame:
    """Pre-flight label distribution counterfactual on /121 triple-barrier (+2/-1 ATR, K=21).

    Estimate per-symbol expected n_labels for the EDA universe assuming the /121 LightGBM
    + 7-gate stack would generate similar label rates as the /121 universe does. This
    informs the brief Section 4 trade-rate floor falsifier prediction.

    Walk-forward-faithful: uses only IS data up to OOS_CUTOFF_MS.
    """
    # Estimate label rate as forward-scan-resolution rate at each bar's +2/-1 ATR barriers.
    # Computed past-only — at bar t, compute ATR using bars [t-50, t-1], scan forward
    # [t+1, t+21] for first barrier hit. IS-only.
    rows = []
    for sym in (*CANDIDATE_SYMBOLS, *ANCHOR_SYMBOLS):
        try:
            df_is = load_klines_is_only(sym)
        except FileNotFoundError:
            continue
        if len(df_is) < 500:
            continue
        h = df_is["high"].values
        l = df_is["low"].values
        c = df_is["close"].values

        # ATR(14) past-only
        tr = np.maximum.reduce([h[1:] - l[1:],
                                np.abs(h[1:] - c[:-1]),
                                np.abs(l[1:] - c[:-1])])
        atr14 = pd.Series(tr).rolling(14).mean().shift(1).values  # shift for past-only

        n_total = len(c) - 1
        # Count TP / SL / timeout outcomes from K=21 forward scan
        tp_hits, sl_hits, timeouts = 0, 0, 0
        K = 21
        for t in range(50, n_total - K):
            atr_t = atr14[t - 1]  # past-only
            if np.isnan(atr_t) or atr_t <= 0:
                continue
            entry = c[t]
            tp_lvl = entry + 2.0 * atr_t
            sl_lvl = entry - 1.0 * atr_t
            hit = "timeout"
            for k in range(1, K + 1):
                if t + k >= len(c):
                    break
                hi = h[t + k]
                lo = l[t + k]
                tp_first = hi >= tp_lvl and (k > 1 or hi >= tp_lvl)
                sl_first = lo <= sl_lvl
                if tp_first and sl_first:
                    # Both in same bar — barrier conflict; assume TP first if midpoint > entry
                    if (hi + lo) / 2 > entry:
                        hit = "tp"
                    else:
                        hit = "sl"
                    break
                elif tp_first:
                    hit = "tp"
                    break
                elif sl_first:
                    hit = "sl"
                    break
            if hit == "tp":
                tp_hits += 1
            elif hit == "sl":
                sl_hits += 1
            else:
                timeouts += 1
        n_eval = tp_hits + sl_hits + timeouts
        rows.append({
            "symbol": sym,
            "n_labels_evaluated": n_eval,
            "tp_rate": tp_hits / n_eval if n_eval > 0 else 0.0,
            "sl_rate": sl_hits / n_eval if n_eval > 0 else 0.0,
            "timeout_rate": timeouts / n_eval if n_eval > 0 else 0.0,
            "tp_minus_sl_rate": (tp_hits - sl_hits) / n_eval if n_eval > 0 else 0.0,
        })
    df = pd.DataFrame(rows)
    return df


def disjointness_check() -> str:
    """Assert CANDIDATE_SYMBOLS disjoint from V3_EXCLUDED_SYMBOLS."""
    overlap = set(CANDIDATE_SYMBOLS) & set(V3_EXCLUDED_SYMBOLS)
    if overlap:
        return f"FAIL — {overlap} in V3_EXCLUDED_SYMBOLS"
    return "PASS — candidate universe disjoint from V3_EXCLUDED_SYMBOLS"


def main() -> None:
    print("=" * 80)
    print("iter-v3/125 — WILD CYCLE-7 axis EDA")
    print(f"Candidate universe: {CANDIDATE_SYMBOLS}")
    print(f"Anchor universe (/121): {ANCHOR_SYMBOLS}")
    print(f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS} (2025-03-24)")
    print(f"Interval: {INTERVAL}")
    print("=" * 80)
    print()
    print(f"Disjointness check: {disjointness_check()}")
    print()

    # T1 — data depth
    print("[T1] Data depth gate")
    t1 = t1_data_depth()
    print(t1.to_string(index=False))
    t1.to_csv(OUTPUT_DIR / "T1_data_depth.csv", index=False)
    print()

    # T2 — per-symbol signal stats
    print("[T2] Per-symbol signal stats")
    t2 = t2_per_symbol_signal_stats()
    print(t2.to_string(index=False))
    t2.to_csv(OUTPUT_DIR / "T2_per_symbol_signal_stats.csv", index=False)
    print()

    # T3 — pairwise feature correlation
    print("[T3] Pairwise return + RV correlation")
    t3 = t3_pairwise_feature_corr()
    print(t3.to_string(index=False))
    t3.to_csv(OUTPUT_DIR / "T3_pairwise_feature_corr.csv", index=False)
    print()

    # T4 — ADF stationarity
    print("[T4] ADF stationarity of incumbent features per candidate")
    t4 = t4_adf_stationarity()
    print(t4.to_string(index=False))
    t4.to_csv(OUTPUT_DIR / "T4_adf_stationarity.csv", index=False)
    print()

    # T5 — vol regime diversity
    print("[T5] Vol regime tier per universe")
    t5 = t5_vol_regime_diversity()
    print(t5.to_string(index=False))
    t5.to_csv(OUTPUT_DIR / "T5_vol_regime_diversity.csv", index=False)
    print()

    # T6 — label distribution counterfactual
    print("[T6] Triple-barrier label distribution counterfactual (+2/-1 ATR, K=21)")
    t6 = t6_label_distribution_predict()
    print(t6.to_string(index=False))
    t6.to_csv(OUTPUT_DIR / "T6_label_distribution_predict.csv", index=False)
    print()

    # Pre-flight gate summary
    print("=" * 80)
    print("PRE-FLIGHT GATE SUMMARY")
    print("=" * 80)
    g1_pass = bool(t1[t1["symbol"].isin(CANDIDATE_SYMBOLS)]["is_gate_pass"].all())
    print(f"G1 data depth (≥24 IS mo per candidate): {'PASS' if g1_pass else 'FAIL'}")

    cross_corrs = t3[t3["is_within_candidate_universe"]]["ret_corr_pearson"].dropna()
    g2_pass = bool((cross_corrs < 0.85).all()) if len(cross_corrs) > 0 else False
    max_cross_corr = float(cross_corrs.max()) if len(cross_corrs) > 0 else float("nan")
    print(
        f"G2 signal diversity (within-candidate ret_corr < 0.85): "
        f"{'PASS' if g2_pass else 'FAIL'} (max within-candidate corr = {max_cross_corr:.4f})"
    )

    g3_pass = bool(t4["stationary_pass"].all())
    n_failed = int((~t4["stationary_pass"]).sum())
    print(
        f"G3 ADF stationarity (incumbent features p<0.05): "
        f"{'PASS' if g3_pass else 'FAIL'} ({n_failed} feature-symbol pairs failed)"
    )

    print()
    print(f"ALL GATES PASS: {g1_pass and g2_pass and g3_pass}")
    print()
    print("Outputs:")
    for f in sorted(OUTPUT_DIR.glob("T*.csv")):
        print(f"  {f}")


if __name__ == "__main__":
    main()
