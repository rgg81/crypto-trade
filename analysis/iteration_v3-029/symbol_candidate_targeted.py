"""iter-v3/029 targeted symbol candidate EDA — per-symbol feature signature prediction.

Purpose
-------
Phase 3 of iter-v3/029 EXPLORATION: pick ONE NEW symbol to add to V3_MODELS
(3 → 4) using a different selection criterion than iter-v3/021's "lowest raw
correlation" heuristic. iter-v3/021's HBAR+AVAX failure (combined -86% IS PnL,
NEGATIVE-clean) showed that lowest correlation captures price diversity NOT
signal diversity.

NEW criterion (informed by Phase 1 per_symbol_feature_analysis):

  Feature-signature alignment = the candidate's correlation profile with the
  SHARED top-7-features-across-all-3-symbols' driving factors. Specifically,
  the candidate must have:

  1. Acceptable raw return correlation with BCH/LDO/TRX (not too low; iter-v3/021
     proved low correlation = wrong feature signature)
  2. Similar volatility regime (NATR_21 within reasonable band)
  3. BTC-trend coupling (must have meaningful sym_vs_btc_ret_7d range; this
     is one of the SHARED features the existing 3 use)
  4. Range/realized-vol pattern compatible with range_realized_vol_50 + vwap_dev_20
     (the most-shared top-7 features per the Phase 1 signature analysis)

Single-axis discipline: ONE NEW symbol; V3_MODELS 3 → 4; REQUIRED_GAP 66 → 88.

Inputs (READ-ONLY)
------------------
- data/{SYMBOL}/8h.csv for incumbents + 7 candidates
  (HBARUSDT and AVAXUSDT skipped — closed dead-paths per iter-v3/021)

Outputs (committed)
-------------------
- analysis/iteration_v3-029/candidate_features_alignment.csv
- analysis/iteration_v3-029/candidate_targeted_ranking.csv
- analysis/iteration_v3-029/synthesis.md  (appends to Phase 1 synthesis)
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
ANALYSIS_DIR = REPO_ROOT / "analysis" / "iteration_v3-029"

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 UTC

# IS window: 2023-04-01 → 2025-03-24 (matches iter-v3/021 EDA boundaries
# minus the 8-month TRAINING_MONTHS=24 ramp-up; see iter-v3/021 brief).
IS_START_MS = int(datetime(2023, 4, 1, tzinfo=timezone.utc).timestamp() * 1000)
IS_END_MS = OOS_CUTOFF_MS

INCUMBENTS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

# Candidate pool: top-passing-Gate-1 candidates from iter-v3/021 ranking,
# EXCLUDING HBAR+AVAX (closed dead-paths per iter-v3/021 NEGATIVE-clean diary
# 92290fd). These are ranks 3-7 from the iter-v3/021 candidate ranking
# (composite score order). All 5 PASSED Gate 1 + Gate 2 in iter-v3/021.
CANDIDATES = ("ADAUSDT", "FILUSDT", "ALGOUSDT", "ATOMUSDT", "VETUSDT")

# Reasonable NATR_21 acceptance band for the 4-symbol universe (incumbent
# range: BCH ~3.5%, LDO ~6.8%, TRX ~3.0%). Acceptance band [3.0%, 7.0%].
NATR_BAND = (3.0, 7.0)

# Per Phase 1 finding: top-7-shared-across-all-3-symbols features are
# vwap_dev_20, range_realized_vol_50, ret_kurt_50, ret_skew_200. These
# capture SHARED-DRIVER signal — a candidate's compatibility with these
# four shared drivers is the dominant compatibility metric.
SHARED_TOP_FEATURES = (
    "vwap_dev_20",
    "range_realized_vol_50",
    "ret_kurt_50",
    "ret_skew_200",
)


# ---------------------------------------------------------------------------
# Loaders + computers
# ---------------------------------------------------------------------------


def load_klines(symbol: str) -> pd.DataFrame:
    p = DATA_DIR / symbol / "8h.csv"
    if not p.exists():
        raise FileNotFoundError(f"missing 8h.csv for {symbol}: {p}")
    df = pd.read_csv(p)
    needed = {"open_time", "close_time", "open", "high", "low", "close", "volume", "quote_volume"}
    missing = needed - set(df.columns)
    if missing:
        raise RuntimeError(f"{symbol}: missing kline columns {missing}")
    df["close_time"] = df["close_time"].astype(np.int64)
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["open"] = df["open"].astype(float)
    df["quote_volume"] = df["quote_volume"].astype(float)
    return df


def trim_is(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["close_time"] >= IS_START_MS) & (df["close_time"] < IS_END_MS)].copy()


def log_returns(df: pd.DataFrame) -> pd.Series:
    closes = df["close"].astype(float)
    rets = np.log(closes).diff()
    return rets


def natr_21(df: pd.DataFrame) -> float:
    """ATR / close, 21-bar, mean across IS. Same formula as iter-v3/021."""
    high = df["high"].astype(float).values
    low = df["low"].astype(float).values
    close = df["close"].astype(float).values
    prev_close = np.roll(close, 1)
    prev_close[0] = close[0]
    tr = np.maximum.reduce([high - low, np.abs(high - prev_close), np.abs(low - prev_close)])
    s_tr = pd.Series(tr).rolling(window=21, min_periods=21).mean()
    natr = (s_tr.values / close) * 100
    return float(np.nanmean(natr))


def range_realized_vol_50(df: pd.DataFrame) -> pd.Series:
    """Approximation of v3 feature: rolling stdev of log returns over 50 bars."""
    rets = log_returns(df)
    return rets.rolling(window=50, min_periods=50).std()


def vwap_dev_20(df: pd.DataFrame) -> pd.Series:
    """Approximation: % deviation of close from rolling VWAP over 20 bars."""
    pv = df["close"].astype(float) * df["quote_volume"].astype(float)
    cum_pv = pv.rolling(window=20, min_periods=20).sum()
    cum_v = df["quote_volume"].astype(float).rolling(window=20, min_periods=20).sum()
    vwap = cum_pv / cum_v.replace(0, np.nan)
    return (df["close"].astype(float) - vwap) / vwap


def ret_kurt_50(rets: pd.Series) -> pd.Series:
    return rets.rolling(window=50, min_periods=50).kurt()


def ret_skew_200(rets: pd.Series) -> pd.Series:
    return rets.rolling(window=200, min_periods=200).skew()


def sym_vs_btc_ret_7d(sym_df: pd.DataFrame, btc_df: pd.DataFrame) -> pd.Series:
    """Approximation: 7d log-return spread vs BTC, aligned on close_time."""
    sym_aligned = sym_df.set_index("close_time")["close"].astype(float)
    btc_aligned = btc_df.set_index("close_time")["close"].astype(float)
    common = sym_aligned.index.intersection(btc_aligned.index)
    sym_aligned = sym_aligned.loc[common]
    btc_aligned = btc_aligned.loc[common]
    sym_ret_7d = np.log(sym_aligned).diff(periods=21)  # 21 × 8h = 168h = 7d
    btc_ret_7d = np.log(btc_aligned).diff(periods=21)
    return (sym_ret_7d - btc_ret_7d).rename("sym_vs_btc_ret_7d")


# ---------------------------------------------------------------------------
# Per-symbol feature signature comparison
# ---------------------------------------------------------------------------


def feature_correlation_matrix(
    sym_df: pd.DataFrame, btc_df: pd.DataFrame
) -> dict[str, pd.Series]:
    """Compute the 4 SHARED-top features' time-series for one symbol on IS window."""
    rets = log_returns(sym_df)
    out = {
        "vwap_dev_20": vwap_dev_20(sym_df),
        "range_realized_vol_50": range_realized_vol_50(sym_df),
        "ret_kurt_50": ret_kurt_50(rets),
        "ret_skew_200": ret_skew_200(rets),
        "sym_vs_btc_ret_7d": sym_vs_btc_ret_7d(sym_df, btc_df),
    }
    return out


def compute_alignment_score(
    candidate_df: pd.DataFrame, incumbent_signatures: dict[str, dict[str, pd.Series]],
    btc_df: pd.DataFrame, candidate_symbol: str
) -> dict[str, float]:
    """For one candidate: how aligned is its feature time-series to the
    incumbents' signatures?

    For each of the 4 SHARED-top features:
      - compute candidate's feature time-series
      - compute Pearson correlation with each incumbent's same feature
      - mean abs correlation across the 3 incumbents = alignment_<feature>
    Higher = candidate's feature behaves like incumbents' → likely to USE the
    feature productively in LightGBM.
    """
    cand_sig = feature_correlation_matrix(candidate_df, btc_df)
    out: dict[str, float] = {}
    for feat in ("vwap_dev_20", "range_realized_vol_50", "ret_kurt_50", "ret_skew_200"):
        # Aligned correlations against all 3 incumbents
        cand_series = cand_sig[feat]
        cand_idx = pd.Series(cand_series.values, index=candidate_df["close_time"].values)
        cors = []
        for sym, sig in incumbent_signatures.items():
            inc_series = sig[feat]
            # Need to find inc_df close_time index. It's in the dict keys via different mech.
            # We need to align on close_time; rebuild.
            pass  # resolved below in main()
        out[f"align_{feat}"] = np.nan
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def feature_alignment_pearson(
    cand_close_time: np.ndarray, cand_feat: pd.Series,
    inc_close_time: np.ndarray, inc_feat: pd.Series,
) -> float:
    """Pearson correlation of two feature time-series aligned on close_time."""
    cand_idx = pd.Series(cand_feat.values, index=cand_close_time)
    inc_idx = pd.Series(inc_feat.values, index=inc_close_time)
    common = cand_idx.index.intersection(inc_idx.index)
    if len(common) < 200:
        return float("nan")
    a = cand_idx.loc[common].dropna()
    b = inc_idx.loc[common].dropna()
    common2 = a.index.intersection(b.index)
    if len(common2) < 200:
        return float("nan")
    a = a.loc[common2]
    b = b.loc[common2]
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(a.corr(b))


def main() -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    print("=== iter-v3/029 targeted candidate EDA (per-symbol feature signature) ===")
    print(f"Incumbents: {INCUMBENTS}")
    print(f"Candidates: {CANDIDATES}")
    print(f"  (HBAR+AVAX excluded per iter-v3/021 NEGATIVE-clean dead-path)")
    print()

    btc_df = load_klines("BTCUSDT")
    btc_df = trim_is(btc_df)

    # Build incumbent signatures
    incumbent_data: dict[str, pd.DataFrame] = {}
    incumbent_signatures: dict[str, dict[str, pd.Series]] = {}
    for sym in INCUMBENTS:
        df = trim_is(load_klines(sym))
        incumbent_data[sym] = df
        incumbent_signatures[sym] = feature_correlation_matrix(df, btc_df)

    # Build candidate alignment matrix
    rows: list[dict[str, object]] = []
    for cand in CANDIDATES:
        try:
            cand_df = trim_is(load_klines(cand))
        except FileNotFoundError as e:
            print(f"SKIP {cand}: {e}")
            continue
        if len(cand_df) < 1500:
            print(f"SKIP {cand}: too few IS bars ({len(cand_df)})")
            continue

        cand_sig = feature_correlation_matrix(cand_df, btc_df)
        cand_ct = cand_df["close_time"].values

        # Pearson alignment of candidate vs each incumbent for each shared-top feature
        per_feat_alignment: dict[str, dict[str, float]] = {feat: {} for feat in SHARED_TOP_FEATURES}
        for feat in SHARED_TOP_FEATURES:
            for inc in INCUMBENTS:
                inc_df = incumbent_data[inc]
                inc_ct = inc_df["close_time"].values
                rho = feature_alignment_pearson(
                    cand_ct, cand_sig[feat], inc_ct, incumbent_signatures[inc][feat]
                )
                per_feat_alignment[feat][inc] = rho

        # Aggregate: mean abs alignment per feature; mean across 4 shared features
        feat_means_abs: dict[str, float] = {}
        for feat in SHARED_TOP_FEATURES:
            vals = [v for v in per_feat_alignment[feat].values() if not np.isnan(v)]
            feat_means_abs[feat] = float(np.mean(np.abs(vals))) if vals else float("nan")
        overall_alignment = float(np.mean(list(feat_means_abs.values())))

        # Raw return correlation (for cross-reference with iter-v3/021 ranking)
        cand_rets = log_returns(cand_df)
        cand_rets_idx = pd.Series(cand_rets.values, index=cand_df["close_time"].values).dropna()
        raw_cors: dict[str, float] = {}
        for inc in INCUMBENTS:
            inc_df = incumbent_data[inc]
            inc_rets = log_returns(inc_df)
            inc_rets_idx = pd.Series(inc_rets.values, index=inc_df["close_time"].values).dropna()
            common = cand_rets_idx.index.intersection(inc_rets_idx.index)
            if len(common) < 200:
                raw_cors[inc] = float("nan")
                continue
            raw_cors[inc] = float(cand_rets_idx.loc[common].corr(inc_rets_idx.loc[common]))

        # NATR_21
        cand_natr = natr_21(cand_df)

        # Compatibility band check
        natr_band_ok = NATR_BAND[0] <= cand_natr <= NATR_BAND[1]

        # BTC coupling magnitude (key: symbols that are uncoupled from BTC will
        # have weaker sym_vs_btc_ret_7d signal; symbols that are over-coupled
        # also). Measure as stdev of sym_vs_btc_ret_7d.
        sym_vs_btc = sym_vs_btc_ret_7d(cand_df, btc_df)
        btc_coupling_std = float(sym_vs_btc.std()) if not sym_vs_btc.dropna().empty else float("nan")

        rows.append(
            {
                "symbol": cand,
                # Phase 1 alignment scores
                "align_vwap_dev_20": round(feat_means_abs["vwap_dev_20"], 4),
                "align_range_realized_vol_50": round(feat_means_abs["range_realized_vol_50"], 4),
                "align_ret_kurt_50": round(feat_means_abs["ret_kurt_50"], 4),
                "align_ret_skew_200": round(feat_means_abs["ret_skew_200"], 4),
                "alignment_score": round(overall_alignment, 4),
                # Raw correlation (iter-v3/021 mistake: this drove the ranking)
                "raw_corr_BCH": round(raw_cors["BCHUSDT"], 4),
                "raw_corr_LDO": round(raw_cors["LDOUSDT"], 4),
                "raw_corr_TRX": round(raw_cors["TRXUSDT"], 4),
                "raw_corr_mean_abs": round(np.mean([abs(v) for v in raw_cors.values()]), 4),
                # Volatility regime
                "natr_21_pct": round(cand_natr, 4),
                "natr_band_ok": natr_band_ok,
                # BTC coupling
                "btc_coupling_std": round(btc_coupling_std, 4),
                # IS bar count
                "is_n_klines": int(len(cand_df)),
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(ANALYSIS_DIR / "candidate_features_alignment.csv", index=False)

    # Composite ranking — alignment dominant (3x weight); NATR band PASS gate;
    # raw corr informational.
    # Composite = 0.65 alignment_score + 0.20 natr_band_ok_score + 0.15 btc_coupling_z
    # where btc_coupling_z normalizes std to [0,1] by min-max.
    cs_min = df["btc_coupling_std"].min()
    cs_max = df["btc_coupling_std"].max()
    df["btc_coupling_z"] = (
        (df["btc_coupling_std"] - cs_min) / (cs_max - cs_min) if cs_max > cs_min else 0.5
    )
    df["natr_band_score"] = df["natr_band_ok"].astype(int)
    df["composite"] = (
        0.65 * df["alignment_score"]
        + 0.20 * df["natr_band_score"]
        + 0.15 * df["btc_coupling_z"]
    )
    df = df.sort_values("composite", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    df.to_csv(ANALYSIS_DIR / "candidate_targeted_ranking.csv", index=False)

    # Console summary
    print("=== Candidate ranking (composite descending) ===\n")
    print(
        df[
            [
                "rank",
                "symbol",
                "composite",
                "alignment_score",
                "raw_corr_mean_abs",
                "natr_21_pct",
                "natr_band_ok",
                "btc_coupling_std",
            ]
        ].to_string(index=False)
    )
    print()
    print(
        "Note: iter-v3/021 ranked HBAR+AVAX top by raw_corr_mean_abs alone. The new "
        "criterion uses alignment_score (Pearson of SHARED-top-feature time-series "
        "vs incumbents' same-feature time-series) — which captures signal-driver "
        "compatibility, not raw price diversity."
    )

    # Append candidate analysis section to synthesis.md
    synth_path = ANALYSIS_DIR / "synthesis.md"
    if synth_path.exists():
        existing = synth_path.read_text(encoding="utf-8")
    else:
        existing = ""

    extra_lines: list[str] = []
    extra_lines.append("\n---\n")
    extra_lines.append("# iter-v3/029 — Candidate symbol ranking (Phase 3)\n")
    extra_lines.append("## Method\n")
    extra_lines.append(
        "Per-symbol feature signature alignment with incumbent BCH/LDO/TRX. The 4 "
        "SHARED-top features identified in Phase 1 are: vwap_dev_20, "
        "range_realized_vol_50, ret_kurt_50, ret_skew_200 (the only features in the "
        "top-7 of all 3 incumbents simultaneously). For each candidate, computes "
        "the Pearson correlation of each shared feature's time-series vs each "
        "incumbent's same feature time-series, takes mean abs across 3 incumbents, "
        "then mean across 4 features = alignment_score.\n\n"
        "Higher alignment_score = candidate's feature time-series behaves similarly "
        "to incumbents → LightGBM is likely to USE these features productively.\n\n"
        "Composite = 0.65·alignment_score + 0.20·natr_band_ok + 0.15·btc_coupling_z.\n\n"
        "**HBAR+AVAX excluded**: iter-v3/021 NEGATIVE-clean (combined -86% PnL); "
        "closed at catalog level. Candidate pool = ranks 3-7 of iter-v3/021 ranking "
        "(ADA, FIL, ALGO, ATOM, VET) — all PASSED Gate 1 + Gate 2.\n"
    )
    extra_lines.append("## Ranking\n")
    extra_lines.append(
        "| Rank | Symbol | composite | alignment_score | raw_corr_mean_abs | NATR_21% | NATR ok | btc_coupling_std |"
    )
    extra_lines.append("|---:|---|---:|---:|---:|---:|:---:|---:|")
    for _, r in df.iterrows():
        extra_lines.append(
            f"| {int(r['rank'])} | **{r['symbol']}** | {float(r['composite']):.4f} | "
            f"{float(r['alignment_score']):.4f} | {float(r['raw_corr_mean_abs']):.4f} | "
            f"{float(r['natr_21_pct']):.2f} | {'PASS' if r['natr_band_ok'] else 'FAIL'} | "
            f"{float(r['btc_coupling_std']):.4f} |"
        )
    extra_lines.append("")
    extra_lines.append("## Per-feature alignment detail\n")
    extra_lines.append(
        "| Symbol | align_vwap_dev_20 | align_range_realized_vol_50 | align_ret_kurt_50 | align_ret_skew_200 |"
    )
    extra_lines.append("|---|---:|---:|---:|---:|")
    for _, r in df.iterrows():
        extra_lines.append(
            f"| {r['symbol']} | {float(r['align_vwap_dev_20']):.4f} | "
            f"{float(r['align_range_realized_vol_50']):.4f} | "
            f"{float(r['align_ret_kurt_50']):.4f} | {float(r['align_ret_skew_200']):.4f} |"
        )
    extra_lines.append("")
    extra_lines.append("## QR Recommendation\n")
    top1 = df.iloc[0]
    extra_lines.append(
        f"**TOP CANDIDATE**: **{top1['symbol']}** (composite {top1['composite']:.4f}; "
        f"alignment_score {top1['alignment_score']:.4f}; NATR_21 {top1['natr_21_pct']:.2f}%).\n\n"
        f"This candidate has the highest feature-signature alignment with incumbent "
        f"BCH/LDO/TRX across the 4 SHARED-top features. Per Phase 1 finding, these "
        f"are the features any new symbol must be compatible with for LightGBM to "
        f"productively use the V3_FEATURE_COLUMNS set. iter-v3/021's mistake was "
        f"selecting on lowest raw correlation — the corrected criterion is highest "
        f"feature-signature alignment.\n"
    )
    extra_lines.append(
        "## Caveats\n\n"
        "- Alignment_score is computed on time-aligned feature series. It does NOT "
        "predict the candidate's per-symbol PnL contribution; that's the empirical "
        "question this EXPLORATION answers.\n"
        "- Single-axis discipline: ONE NEW symbol; V3_MODELS 3 → 4; REQUIRED_GAP "
        "66 → 88. KEEP all 14 features (including regime_momentum_signed_5d).\n"
        "- Falsifier (PATH B-DRAG): candidate's IS PnL is materially negative AND "
        "concentration drops below 60% — verifies dilution but at cost of edge "
        "drag (similar to iter-v3/021 HBAR+AVAX failure mode). Falsifier "
        "(PATH C-INERT): candidate trades but produces ~0% PnL; concentration drops "
        "but no signal added. Falsifier (PATH A): candidate produces positive "
        "PnL AND concentration drops AND IS+OOS preserved → PROMISING.\n"
    )

    synth_path.write_text(existing + "\n".join(extra_lines), encoding="utf-8")

    print(f"\n=== Top-1 candidate: {top1['symbol']} (composite {top1['composite']:.4f}) ===")
    print(f"\nWritten:")
    print(f"  {ANALYSIS_DIR / 'candidate_features_alignment.csv'}")
    print(f"  {ANALYSIS_DIR / 'candidate_targeted_ranking.csv'}")
    print(f"  {ANALYSIS_DIR / 'synthesis.md'} (appended)")


if __name__ == "__main__":
    main()
