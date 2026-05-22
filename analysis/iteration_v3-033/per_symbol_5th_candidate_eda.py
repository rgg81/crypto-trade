"""iter-v3/033 per-symbol feature analysis + 5th symbol candidate evaluation.

Purpose
-------
iter-v3/032 closed with V3_MODELS = 4 (BCH+LDO+TRX+ALGO; LDO restored under
per-symbol ATR multiplier (1.5, 0.75); regime_momentum_signed_5d kept; OOS
Sharpe +1.93 highest in v3 catalog at single-seed; IS Sharpe collapsed to
+0.24 — single-seed-lottery pattern). Outstanding aspirational MERGE-gate
gaps:

- Top-symbol concentration: 45.10% (TRX) > 30% threshold (-15pp gap)
- Bundle OOS trades: 129 < 130 floor (-1)
- IS aggregate Sharpe: +0.24 < +1.0 absolute floor (-0.76)

iter-v3/033 axis (single-axis EXPLORATION, cadence #5 of 10 in post-iter-v3/028
cycle): ADD a 5th symbol with per-symbol-feature-signature alignment.
V3_MODELS 4 → 5; REQUIRED_GAP 88 → 110 = (21+1)×5. Methodology proven at
iter-v3/029 (ALGO selected on alignment-score, OOS contributed +20.87): the
4-symbol importance CSVs from iter-v3/032 are the new IS-only signature
seed. Re-extract SHARED top-7 features ACROSS ALL 4 (BCH+LDO+TRX+ALGO).

This script combines the iter-v3/029 Phase-1 (per-symbol importance dispersion)
and Phase-3 (candidate alignment ranking) methodologies, but updated for the
4-symbol incumbent universe AND for a NEW 5th-symbol candidate pool that
EXCLUDES the iter-v3/021 dead-paths (HBAR + AVAX) AND the symbol already
absorbed at iter-v3/029 (ALGO). The remaining candidate pool is therefore
{FILUSDT, VETUSDT, ATOMUSDT} — the iter-v3/021/029 cross-section minus
absorbed and dead-path symbols. ADAUSDT was excluded by the iter-v3/021 EDA
(narrow IS history) and is not a fresh candidate at this stage.

Methodology
-----------
1. **Phase 1 — per-symbol feature importance dispersion across 4 incumbents.**
   For each of the 14 V3 features, captures rank within symbol from the
   iter-v3/032 IS-only model_importance_last_month_<SYM>.csv. Computes
   rank_range (max-min) and rank_std across BCH+LDO+TRX+ALGO.
   - rank_range >= 7 → HIGH-DISP-SYMBOL-SPECIFIC (top on some, bottom on others)
   - rank_range 4-6 → MID-DISP
   - rank_range <= 3 → LOW-DISP-SHARED (consistent across all 4 symbols)
   Identifies the SHARED top-7 features (top-7 in BCH AND LDO AND TRX AND ALGO
   simultaneously) — these are the alignment targets for the 5th-symbol
   candidate.

2. **Phase 3 — 5th-symbol candidate evaluation.**
   For each candidate (FIL, VET, ATOM):
   - Gate 1 — data quality: coverage, listing date (≥18 mo pre-IS), no
     suspicious gaps in 8h.csv.
   - Gate 2 — liquidity: avg daily quote volume IS+OOS > $20M, P10 > $5M.
   - Gate 3 — feature signature alignment: composite =
     0.65·alignment_score (mean abs Pearson of 4-or-5 SHARED-top features
     time-series vs each of 4 incumbents — mean abs across incumbents,
     mean across features) + 0.20·natr_band_OK + 0.15·btc_coupling_z.

3. **Pick the candidate with the highest composite that passes all gates.**

Inputs (READ-ONLY; IS-window only, except OOS_quote_volume informational)
------------------------------------------------------------------------
- reports-v3/iteration_v3-032/in_sample/model_importance_last_month_{BCH,LDO,TRX,ALGO}USDT.csv
- reports-v3/iteration_v3-032/in_sample/model_importance_last_month_portfolio.csv
- reports-v3/iteration_v3-032/in_sample/per_symbol.csv (IS, informational sanity)
- reports-v3/iteration_v3-032/out_of_sample/per_symbol.csv (informational only)
- data/{BTC,BCH,LDO,TRX,ALGO,FIL,VET,ATOM}USDT/8h.csv IS-window 2023-04-01 → 2025-03-24

Outputs (committed)
-------------------
- analysis/iteration_v3-033/per_symbol_feature_signature.csv (long format)
- analysis/iteration_v3-033/feature_dispersion_ranking.csv
- analysis/iteration_v3-033/symbol_specific_features.csv
- analysis/iteration_v3-033/symbol_specific_top_bottom.csv
- analysis/iteration_v3-033/candidate_features_alignment.csv
- analysis/iteration_v3-033/candidate_targeted_ranking.csv
- analysis/iteration_v3-033/synthesis.md (Phase 1 + Phase 3 narrative)

The script DOES NOT use OOS metrics for selection — only IS importance ranks
and IS-window kline data. OOS columns are reported informationally for the
synthesis only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
ITER032_IS = REPO_ROOT / "reports-v3" / "iteration_v3-032" / "in_sample"
ITER032_OOS = REPO_ROOT / "reports-v3" / "iteration_v3-032" / "out_of_sample"
DATA_DIR = REPO_ROOT / "data"
OUT_DIR = REPO_ROOT / "analysis" / "iteration_v3-033"

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 UTC
IS_START_MS = int(datetime(2023, 4, 1, tzinfo=timezone.utc).timestamp() * 1000)
IS_END_MS = OOS_CUTOFF_MS

# 4 incumbents at iter-v3/032 (BCH+LDO+TRX+ALGO post-restore-LDO + per-sym ATR).
INCUMBENTS = ("BCHUSDT", "LDOUSDT", "TRXUSDT", "ALGOUSDT")

# 14 V3 features (V3_FEATURE_COLUMNS_TOP_N at iter-v3/032 byte-identical to
# iter-v3/029 / iter-v3/028).
V3_FEATURES_14: tuple[str, ...] = (
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

# 5th-symbol candidate pool. Per task spec: {FILUSDT, VETUSDT, ATOMUSDT};
# HBAR + AVAX excluded as iter-v3/021 NEGATIVE-clean dead-path; ALGO
# absorbed at iter-v3/029. (ADAUSDT excluded due to narrow history - was
# present at iter-v3/029 candidate ranking but dropped due to insufficient
# pre-IS coverage; sticking with task spec.)
CANDIDATES = ("FILUSDT", "VETUSDT", "ATOMUSDT")

# Reasonable NATR_21 acceptance band for the 5-symbol universe (4 incumbents'
# NATR range ≈ [3.0%, 7.0%] from iter-v3/029 EDA; band unchanged).
NATR_BAND = (3.0, 7.0)

# Liquidity thresholds (Gate 2)
QVOL_MEAN_MIN = 20_000_000  # $20M avg daily
QVOL_P10_MIN = 5_000_000  # $5M P10 daily

# Coverage thresholds (Gate 1)
COVERAGE_MIN_PCT = 99.0
PRE_IS_HISTORY_MIN_MO = 18


# ---------------------------------------------------------------------------
# Loaders
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


def trim_oos(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["close_time"] >= IS_END_MS].copy()


def load_importance(symbol: str) -> pd.DataFrame:
    """Load model_importance_last_month_<SYM>.csv from iter-v3/032 IS reports."""
    path = ITER032_IS / f"model_importance_last_month_{symbol}.csv"
    df = pd.read_csv(path)
    if list(df.columns) != ["feature", "importance"]:
        raise RuntimeError(f"unexpected schema in {path}: {df.columns.tolist()}")
    return df


def load_per_symbol_pnl() -> dict[str, pd.DataFrame]:
    is_df = pd.read_csv(ITER032_IS / "per_symbol.csv")
    oos_df = pd.read_csv(ITER032_OOS / "per_symbol.csv")
    return {"is": is_df, "oos": oos_df}


# ---------------------------------------------------------------------------
# Phase 1 — per-symbol feature signature across 4 incumbents
# ---------------------------------------------------------------------------


def build_signature_long() -> pd.DataFrame:
    """Long format: one row per (symbol, feature) with importance, rank, normalized."""
    rows: list[dict[str, object]] = []
    for sym in INCUMBENTS:
        df = load_importance(sym)
        present = set(df["feature"].tolist())
        missing = set(V3_FEATURES_14) - present
        if missing:
            raise RuntimeError(f"{sym} importance CSV missing features: {sorted(missing)}")
        extra = present - set(V3_FEATURES_14)
        if extra:
            raise RuntimeError(f"{sym} importance CSV has unexpected features: {sorted(extra)}")
        df = df.sort_values("importance", ascending=False).reset_index(drop=True)
        df["rank_within_symbol"] = df.index + 1  # 1-indexed
        max_imp = df["importance"].max()
        df["importance_norm"] = df["importance"] / max_imp  # in [0, 1]
        for _, r in df.iterrows():
            rows.append(
                {
                    "symbol": sym,
                    "feature": r["feature"],
                    "importance": float(r["importance"]),
                    "rank_within_symbol": int(r["rank_within_symbol"]),
                    "importance_norm": float(r["importance_norm"]),
                }
            )
    long_df = pd.DataFrame(rows)
    return long_df


def build_dispersion(long_df: pd.DataFrame) -> pd.DataFrame:
    """Per-feature: rank dispersion across 4 incumbents."""
    rows: list[dict[str, object]] = []
    for feature in V3_FEATURES_14:
        sub = long_df[long_df["feature"] == feature]
        ranks = {sym: int(sub[sub["symbol"] == sym]["rank_within_symbol"].iloc[0]) for sym in INCUMBENTS}
        norms = {sym: float(sub[sub["symbol"] == sym]["importance_norm"].iloc[0]) for sym in INCUMBENTS}
        rank_min = min(ranks.values())
        rank_max = max(ranks.values())
        rank_range = rank_max - rank_min
        rank_std = float(np.std(list(ranks.values()), ddof=0))
        norm_std = float(np.std(list(norms.values()), ddof=0))
        rows.append(
            {
                "feature": feature,
                "rank_BCH": ranks["BCHUSDT"],
                "rank_LDO": ranks["LDOUSDT"],
                "rank_TRX": ranks["TRXUSDT"],
                "rank_ALGO": ranks["ALGOUSDT"],
                "rank_min": rank_min,
                "rank_max": rank_max,
                "rank_range": rank_range,
                "rank_std": round(rank_std, 4),
                "norm_BCH": round(norms["BCHUSDT"], 4),
                "norm_LDO": round(norms["LDOUSDT"], 4),
                "norm_TRX": round(norms["TRXUSDT"], 4),
                "norm_ALGO": round(norms["ALGOUSDT"], 4),
                "norm_std": round(norm_std, 4),
                "norm_mean": round(np.mean(list(norms.values())), 4),
            }
        )
    df = pd.DataFrame(rows)
    df = df.sort_values("rank_range", ascending=False).reset_index(drop=True)
    return df


def identify_symbol_specific(disp_df: pd.DataFrame) -> pd.DataFrame:
    """Classification with thresholds adjusted for 4-symbol universe.
    rank_range thresholds widen a touch since 4 symbols have more spread potential.
    """
    rows = []
    for _, r in disp_df.iterrows():
        rng = int(r["rank_range"])
        if rng >= 7:
            label = "HIGH-DISP-SYMBOL-SPECIFIC"
        elif rng >= 4:
            label = "MID-DISP"
        else:
            label = "LOW-DISP-SHARED"
        rows.append(
            {
                "feature": r["feature"],
                "rank_BCH": int(r["rank_BCH"]),
                "rank_LDO": int(r["rank_LDO"]),
                "rank_TRX": int(r["rank_TRX"]),
                "rank_ALGO": int(r["rank_ALGO"]),
                "rank_range": rng,
                "norm_std": float(r["norm_std"]),
                "classification": label,
            }
        )
    df = pd.DataFrame(rows)
    return df


def build_top_bottom_per_symbol(long_df: pd.DataFrame) -> pd.DataFrame:
    """For each symbol, top-7 features (rank 1-7) and bottom-7 (rank 8-14)."""
    rows = []
    for sym in INCUMBENTS:
        sub = long_df[long_df["symbol"] == sym].sort_values("rank_within_symbol")
        top_7 = sub.iloc[:7]["feature"].tolist()
        bot_7 = sub.iloc[7:]["feature"].tolist()
        rows.append(
            {
                "symbol": sym,
                "top_7_features": " | ".join(top_7),
                "bottom_7_features": " | ".join(bot_7),
            }
        )
    return pd.DataFrame(rows)


def shared_top_n_features(long_df: pd.DataFrame, top_n: int = 7) -> set[str]:
    """Identify features in top-N of EVERY incumbent simultaneously."""
    per_sym_topn = []
    for sym in INCUMBENTS:
        sub = long_df[long_df["symbol"] == sym].sort_values("rank_within_symbol")
        per_sym_topn.append(set(sub.iloc[:top_n]["feature"].tolist()))
    if not per_sym_topn:
        return set()
    shared = per_sym_topn[0]
    for s in per_sym_topn[1:]:
        shared = shared & s
    return shared


# ---------------------------------------------------------------------------
# Phase 3 — 5th-symbol candidate alignment
# ---------------------------------------------------------------------------


def log_returns(df: pd.DataFrame) -> pd.Series:
    closes = df["close"].astype(float)
    return np.log(closes).diff()


def natr_21(df: pd.DataFrame) -> float:
    """ATR / close, 21-bar, mean across IS. Same formula as iter-v3/021/029."""
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
    rets = log_returns(df)
    return rets.rolling(window=50, min_periods=50).std()


def vwap_dev_20(df: pd.DataFrame) -> pd.Series:
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
    sym_aligned = sym_df.set_index("close_time")["close"].astype(float)
    btc_aligned = btc_df.set_index("close_time")["close"].astype(float)
    common = sym_aligned.index.intersection(btc_aligned.index)
    sym_aligned = sym_aligned.loc[common]
    btc_aligned = btc_aligned.loc[common]
    sym_ret_7d = np.log(sym_aligned).diff(periods=21)  # 21 × 8h = 7d
    btc_ret_7d = np.log(btc_aligned).diff(periods=21)
    return (sym_ret_7d - btc_ret_7d).rename("sym_vs_btc_ret_7d")


def feature_correlation_matrix(
    sym_df: pd.DataFrame,
    btc_df: pd.DataFrame,
    feature_list: tuple[str, ...],
) -> dict[str, pd.Series]:
    """Compute the feature time-series for one symbol on IS window."""
    rets = log_returns(sym_df)
    available = {
        "vwap_dev_20": vwap_dev_20(sym_df),
        "range_realized_vol_50": range_realized_vol_50(sym_df),
        "ret_kurt_50": ret_kurt_50(rets),
        "ret_skew_200": ret_skew_200(rets),
        "sym_vs_btc_ret_7d": sym_vs_btc_ret_7d(sym_df, btc_df),
    }
    return {feat: available[feat] for feat in feature_list if feat in available}


def feature_alignment_pearson(
    cand_close_time: np.ndarray,
    cand_feat: pd.Series,
    inc_close_time: np.ndarray,
    inc_feat: pd.Series,
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


def gate_1_data_quality(cand: str) -> dict[str, object]:
    """Gate 1: coverage + listing date."""
    df = load_klines(cand)
    full_n = len(df)
    is_n = len(trim_is(df))
    if full_n == 0:
        return {
            "gate1_pass": False,
            "is_n_klines": 0,
            "first_close_time": None,
            "pre_IS_history_months": 0.0,
            "coverage_pct": 0.0,
        }
    first_ms = int(df["close_time"].min())
    pre_is_ms = max(IS_START_MS - first_ms, 0)
    pre_is_months = pre_is_ms / 1000 / 86400 / 30.4375  # avg month length
    # Expected IS bars: from IS_START to IS_END at 8h cadence
    expected_is_bars = (IS_END_MS - IS_START_MS) / 1000 / 28800
    coverage_pct = (is_n / max(expected_is_bars, 1)) * 100
    pass_ = (
        coverage_pct >= COVERAGE_MIN_PCT
        and pre_is_months >= PRE_IS_HISTORY_MIN_MO
        and is_n >= 1500
    )
    return {
        "gate1_pass": pass_,
        "is_n_klines": is_n,
        "first_close_time": first_ms,
        "pre_IS_history_months": round(pre_is_months, 2),
        "coverage_pct": round(coverage_pct, 2),
    }


def gate_2_liquidity(cand: str) -> dict[str, object]:
    """Gate 2: avg + P10 daily quote volume IS+OOS."""
    df = load_klines(cand)
    is_df = trim_is(df)
    oos_df = trim_oos(df)
    # 8h bars → 3 bars per day → daily volume = sum of 3 consecutive bars.
    is_daily = is_df["quote_volume"].rolling(window=3, min_periods=3).sum().dropna()
    oos_daily = oos_df["quote_volume"].rolling(window=3, min_periods=3).sum().dropna() if len(oos_df) >= 3 else pd.Series(dtype=float)

    is_qvol_mean = float(is_daily.mean()) if len(is_daily) else 0.0
    is_qvol_p10 = float(is_daily.quantile(0.1)) if len(is_daily) else 0.0
    oos_qvol_mean = float(oos_daily.mean()) if len(oos_daily) else 0.0
    oos_qvol_p10 = float(oos_daily.quantile(0.1)) if len(oos_daily) else 0.0

    # Gate 2 evaluates on IS-window (selection criterion); OOS is informational.
    pass_ = is_qvol_mean >= QVOL_MEAN_MIN and is_qvol_p10 >= QVOL_P10_MIN
    return {
        "gate2_pass": pass_,
        "is_qvol_mean_$": round(is_qvol_mean, 0),
        "is_qvol_p10_$": round(is_qvol_p10, 0),
        "oos_qvol_mean_$": round(oos_qvol_mean, 0),
        "oos_qvol_p10_$": round(oos_qvol_p10, 0),
    }


def gate_3_alignment(
    cand_df: pd.DataFrame,
    incumbent_data: dict[str, pd.DataFrame],
    btc_df: pd.DataFrame,
    shared_top: tuple[str, ...],
) -> dict[str, object]:
    """Gate 3: alignment composite score on the SHARED-top features."""
    if not shared_top:
        # Fallback to the iter-v3/029 4-feature anchor if Phase 1 finds no
        # SHARED-top across 4 symbols (likelihood: low; expected to find ≥3).
        feature_list = ("vwap_dev_20", "range_realized_vol_50", "ret_kurt_50", "ret_skew_200")
    else:
        # Restrict to the cand-computable subset of shared_top.
        candidates_pool = ("vwap_dev_20", "range_realized_vol_50", "ret_kurt_50", "ret_skew_200")
        feature_list = tuple(f for f in candidates_pool if f in shared_top)
        if not feature_list:
            feature_list = candidates_pool

    cand_sig = feature_correlation_matrix(cand_df, btc_df, feature_list)
    incumbent_sigs = {
        sym: feature_correlation_matrix(df, btc_df, feature_list)
        for sym, df in incumbent_data.items()
    }
    cand_ct = cand_df["close_time"].values

    per_feat_alignment: dict[str, dict[str, float]] = {feat: {} for feat in feature_list}
    for feat in feature_list:
        for inc, inc_df in incumbent_data.items():
            inc_ct = inc_df["close_time"].values
            rho = feature_alignment_pearson(
                cand_ct, cand_sig[feat], inc_ct, incumbent_sigs[inc][feat]
            )
            per_feat_alignment[feat][inc] = rho

    feat_means_abs: dict[str, float] = {}
    for feat in feature_list:
        vals = [v for v in per_feat_alignment[feat].values() if not np.isnan(v)]
        feat_means_abs[feat] = float(np.mean(np.abs(vals))) if vals else float("nan")
    overall_alignment = float(np.mean(list(feat_means_abs.values())))

    cand_natr = natr_21(cand_df)
    natr_ok = NATR_BAND[0] <= cand_natr <= NATR_BAND[1]
    sym_vs_btc = sym_vs_btc_ret_7d(cand_df, btc_df)
    btc_coupling_std = float(sym_vs_btc.std()) if not sym_vs_btc.dropna().empty else float("nan")

    cand_rets = log_returns(cand_df)
    cand_rets_idx = pd.Series(cand_rets.values, index=cand_df["close_time"].values).dropna()
    raw_cors: dict[str, float] = {}
    for inc, inc_df in incumbent_data.items():
        inc_rets = log_returns(inc_df)
        inc_rets_idx = pd.Series(inc_rets.values, index=inc_df["close_time"].values).dropna()
        common = cand_rets_idx.index.intersection(inc_rets_idx.index)
        if len(common) < 200:
            raw_cors[inc] = float("nan")
            continue
        raw_cors[inc] = float(cand_rets_idx.loc[common].corr(inc_rets_idx.loc[common]))

    return {
        "alignment_features_used": "+".join(feature_list),
        "alignment_per_feature": {f: round(feat_means_abs.get(f, float("nan")), 4) for f in feature_list},
        "alignment_score": round(overall_alignment, 4),
        "natr_21_pct": round(cand_natr, 4),
        "natr_band_ok": natr_ok,
        "btc_coupling_std": round(btc_coupling_std, 4),
        "raw_corr_BCH": round(raw_cors.get("BCHUSDT", float("nan")), 4),
        "raw_corr_LDO": round(raw_cors.get("LDOUSDT", float("nan")), 4),
        "raw_corr_TRX": round(raw_cors.get("TRXUSDT", float("nan")), 4),
        "raw_corr_ALGO": round(raw_cors.get("ALGOUSDT", float("nan")), 4),
        "raw_corr_mean_abs": round(
            float(np.mean([abs(v) for v in raw_cors.values() if not np.isnan(v)])), 4
        ),
    }


# ---------------------------------------------------------------------------
# Synthesis writer
# ---------------------------------------------------------------------------


def write_synthesis(
    long_df: pd.DataFrame,
    disp_df: pd.DataFrame,
    cls_df: pd.DataFrame,
    top_bot_df: pd.DataFrame,
    shared_top_7: set[str],
    candidate_rows: list[dict[str, object]],
    pnl: dict[str, pd.DataFrame],
    chosen: dict[str, object],
) -> None:
    out_path = OUT_DIR / "synthesis.md"
    lines: list[str] = []
    lines.append("# iter-v3/033 — Per-Symbol Feature Analysis + 5th Symbol Selection\n")
    lines.append(
        "## Context\n\n"
        "iter-v3/032 closed with 4-symbol V3_MODELS = {BCH+LDO+TRX+ALGO}. ALGO was "
        "added at iter-v3/029 under per-symbol-feature-signature alignment "
        "(composite 0.6517; OOS contribution +20.87 weighted_pnl, validating the "
        "methodology). LDO was restored at iter-v3/032 under per-symbol ATR "
        "multipliers (1.5, 0.75) — labeling-layer adjustment that lifted LDO from "
        "-3.07 to +3.98 OOS. iter-v3/033 axis: ADD a 5th symbol with the same "
        "per-symbol-feature-signature criterion, applied to the new 4-symbol "
        "incumbent universe (BCH+LDO+TRX+ALGO).\n"
    )
    lines.append(
        "## Method\n\n"
        "Phase 1 — re-extract per-symbol feature importance from iter-v3/032 "
        "model_importance_last_month_<SYM>.csv (IS-only) for ALL 4 incumbents "
        "including ALGO + LDO post-ATR-multiplier-restore. Compute rank_range "
        "(max-min) and rank_std across BCH+LDO+TRX+ALGO. Identify SHARED top-7 "
        "features (top-7 in BCH AND LDO AND TRX AND ALGO simultaneously).\n\n"
        "Classification thresholds (adjusted for 4-symbol universe): rank_range ≥ "
        "7 → HIGH-DISP-SYMBOL-SPECIFIC; 4-6 → MID-DISP; ≤ 3 → LOW-DISP-SHARED.\n\n"
        "Phase 3 — for each candidate {FILUSDT, VETUSDT, ATOMUSDT}: run 3 gates. "
        "Gate 1 = data quality (coverage + pre-IS history); Gate 2 = liquidity "
        "(IS-window avg + P10 daily quote volume); Gate 3 = feature signature "
        "alignment composite (0.65·alignment_score + 0.20·natr_band_OK + "
        "0.15·btc_coupling_z; alignment_score = mean abs Pearson of SHARED-top "
        "features' time-series vs each of 4 incumbents).\n\n"
        "**Excluded candidates:** HBAR + AVAX (iter-v3/021 NEGATIVE-clean dead-"
        "path); ALGO (already absorbed at iter-v3/029); ADA (narrow pre-IS "
        "history per iter-v3/021 EDA).\n"
    )

    lines.append("## Per-symbol top-7 and bottom-7 features (4 incumbents)\n")
    lines.append("| Symbol | Top-7 (rank 1-7) | Bottom-7 (rank 8-14) |")
    lines.append("|---|---|---|")
    for _, r in top_bot_df.iterrows():
        lines.append(f"| **{r['symbol']}** | {r['top_7_features']} | {r['bottom_7_features']} |")
    lines.append("")

    lines.append("## Cross-symbol feature dispersion ranking (4 incumbents)\n")
    lines.append("Sorted by rank_range descending. HIGH dispersion = SYMBOL-SPECIFIC.\n")
    lines.append(
        "| Feature | rank_BCH | rank_LDO | rank_TRX | rank_ALGO | rank_range | norm_std | norm_mean | classification |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for _, r in disp_df.iterrows():
        cls = cls_df[cls_df["feature"] == r["feature"]]["classification"].iloc[0]
        lines.append(
            f"| {r['feature']} | {int(r['rank_BCH'])} | {int(r['rank_LDO'])} | "
            f"{int(r['rank_TRX'])} | {int(r['rank_ALGO'])} | {int(r['rank_range'])} | "
            f"{r['norm_std']:.4f} | {r['norm_mean']:.4f} | {cls} |"
        )
    lines.append("")

    high_disp = cls_df[cls_df["classification"] == "HIGH-DISP-SYMBOL-SPECIFIC"]
    mid_disp = cls_df[cls_df["classification"] == "MID-DISP"]
    low_disp = cls_df[cls_df["classification"] == "LOW-DISP-SHARED"]
    lines.append("## Classification summary\n")
    lines.append(
        f"- HIGH-DISP-SYMBOL-SPECIFIC ({len(high_disp)}): "
        f"{', '.join(high_disp['feature'].tolist()) if len(high_disp) else '(none)'}"
    )
    lines.append(
        f"- MID-DISP ({len(mid_disp)}): "
        f"{', '.join(mid_disp['feature'].tolist()) if len(mid_disp) else '(none)'}"
    )
    lines.append(
        f"- LOW-DISP-SHARED ({len(low_disp)}): "
        f"{', '.join(low_disp['feature'].tolist()) if len(low_disp) else '(none)'}"
    )
    lines.append("")

    lines.append("## SHARED top-7 features across ALL 4 incumbents\n")
    if shared_top_7:
        lines.append(
            f"**{len(shared_top_7)} feature(s)** in the top-7 of BCH AND LDO AND TRX AND ALGO "
            f"simultaneously: `{', '.join(sorted(shared_top_7))}`.\n"
        )
        lines.append(
            "These are the alignment targets for Gate 3 — any new symbol's "
            "compatibility with V3_FEATURE_COLUMNS is best approximated by its "
            "feature-signature alignment with these.\n"
        )
    else:
        lines.append(
            "**NO features** were top-7 in all 4 incumbents simultaneously. "
            "Falling back to the iter-v3/029 anchor list "
            "(vwap_dev_20, range_realized_vol_50, ret_kurt_50, ret_skew_200) "
            "for the alignment computation.\n"
        )
    lines.append("")

    lines.append("## Phase 3 — Candidate evaluation (3 gates)\n")
    lines.append(
        "| Symbol | Gate1 | Gate2 | Gate3 alignment_score | composite | NATR_21% | NATR_OK | btc_coupling_std | raw_corr_mean | gates_pass |"
    )
    lines.append("|---|:---:|:---:|---:|---:|---:|:---:|---:|---:|:---:|")
    for r in candidate_rows:
        lines.append(
            f"| **{r['symbol']}** | "
            f"{'PASS' if r['gate1_pass'] else 'FAIL'} | "
            f"{'PASS' if r['gate2_pass'] else 'FAIL'} | "
            f"{float(r['alignment_score']):.4f} | "
            f"{float(r['composite']):.4f} | "
            f"{float(r['natr_21_pct']):.2f} | "
            f"{'PASS' if r['natr_band_ok'] else 'FAIL'} | "
            f"{float(r['btc_coupling_std']):.4f} | "
            f"{float(r['raw_corr_mean_abs']):.4f} | "
            f"{'PASS' if r['gates_pass'] else 'FAIL'} |"
        )
    lines.append("")

    lines.append("## Per-feature alignment detail (for candidates that PASSED Gate 1+2)\n")
    feature_list_used = candidate_rows[0]["alignment_features_used"] if candidate_rows else ""
    lines.append(f"alignment features used: `{feature_list_used}`\n")
    feats = feature_list_used.split("+") if feature_list_used else []
    if feats:
        header = "| Symbol | " + " | ".join(f"align_{f}" for f in feats) + " |"
        sep = "|---|" + "|".join(["---:"] * len(feats)) + "|"
        lines.append(header)
        lines.append(sep)
        for r in candidate_rows:
            apf = r["alignment_per_feature"]
            cells = " | ".join(f"{apf.get(f, float('nan')):.4f}" for f in feats)
            lines.append(f"| {r['symbol']} | {cells} |")
        lines.append("")

    lines.append("## Liquidity detail (Gate 2 numerical)\n")
    lines.append("| Symbol | IS qvol mean | IS qvol P10 | OOS qvol mean | OOS qvol P10 |")
    lines.append("|---|---:|---:|---:|---:|")
    for r in candidate_rows:
        lines.append(
            f"| {r['symbol']} | "
            f"${float(r['is_qvol_mean_$']):,.0f} | "
            f"${float(r['is_qvol_p10_$']):,.0f} | "
            f"${float(r['oos_qvol_mean_$']):,.0f} | "
            f"${float(r['oos_qvol_p10_$']):,.0f} |"
        )
    lines.append("")

    lines.append("## Coverage detail (Gate 1 numerical)\n")
    lines.append("| Symbol | IS klines | first close_time | pre-IS months | IS coverage % |")
    lines.append("|---|---:|---:|---:|---:|")
    for r in candidate_rows:
        first_ts = r.get("first_close_time", None)
        if first_ts is not None:
            first_dt = datetime.fromtimestamp(first_ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        else:
            first_dt = "—"
        lines.append(
            f"| {r['symbol']} | {int(r['is_n_klines'])} | {first_dt} | "
            f"{float(r['pre_IS_history_months']):.2f} | {float(r['coverage_pct']):.2f} |"
        )
    lines.append("")

    # Recommendation
    lines.append("## QR Recommendation\n")
    if chosen:
        lines.append(
            f"**TOP CANDIDATE**: **{chosen['symbol']}** (composite "
            f"{float(chosen['composite']):.4f}; alignment_score "
            f"{float(chosen['alignment_score']):.4f}; NATR_21 "
            f"{float(chosen['natr_21_pct']):.2f}%).\n"
        )
        lines.append(
            f"All 3 gates PASS for {chosen['symbol']}: data quality (Gate 1), "
            f"liquidity (Gate 2), feature signature alignment (Gate 3). The "
            f"selection criterion is the same iter-v3/029 methodology that "
            f"successfully predicted ALGO's positive contribution: highest "
            f"feature-signature alignment with the incumbents' SHARED top-N "
            f"features, NOT lowest raw return correlation (the iter-v3/021 "
            f"falsified criterion).\n"
        )
    else:
        lines.append(
            "**NO candidate passed all 3 gates.** iter-v3/033 cannot proceed "
            "with the 5th-symbol-add axis under the current methodology. "
            "Recommend pivoting to a different EXPLORATION axis category.\n"
        )
    lines.append("")

    # OOS sanity check (informational only)
    lines.append("## Sanity-check: per-symbol OOS PnL — iter-v3/032 (informational only)\n")
    lines.append(
        "*Feature selection above depends ONLY on IS importance ranks and "
        "IS-window kline data. The OOS columns confirm the concentration is "
        "real and motivates the 5th-symbol-add axis.*\n"
    )
    lines.append("| Symbol | IS trades | IS net_pnl% | OOS trades | OOS net_pnl% | OOS WR% |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    is_df = pnl["is"]
    oos_df = pnl["oos"]
    for sym in INCUMBENTS:
        is_row = is_df[is_df["symbol"] == sym]
        oos_row = oos_df[oos_df["symbol"] == sym]
        if len(is_row) == 0 or len(oos_row) == 0:
            continue
        lines.append(
            f"| {sym} | {int(is_row.iloc[0]['trades'])} | "
            f"{float(is_row.iloc[0]['net_pnl_pct']):+.2f} | "
            f"{int(oos_row.iloc[0]['trades'])} | "
            f"{float(oos_row.iloc[0]['net_pnl_pct']):+.2f} | "
            f"{float(oos_row.iloc[0]['win_rate']):.1f} |"
        )
    lines.append("")

    # Caveats
    lines.append("## Caveats\n\n")
    lines.append(
        "- Alignment_score is computed on time-aligned feature time-series; "
        "it does NOT predict the candidate's per-symbol PnL contribution at "
        "single-seed n_trials=35. The empirical question this EXPLORATION "
        "answers is whether the alignment translates to productive LightGBM "
        "fitting in the 5-symbol bundle.\n"
        "- Single-axis discipline: ONE NEW symbol; V3_MODELS 4 → 5; "
        "REQUIRED_GAP 88 → 110 = (21+1)×5. KEEP V3_FEATURE_COLUMNS=14 byte-"
        "identical (regime_momentum_signed_5d preserved). KEEP "
        "V3_ATR_MULTIPLIERS_PER_SYMBOL with LDO entry; do NOT apply the "
        "(1.5, 0.75) multiplier to the new symbol unless its IS NATR "
        "distribution suggests otherwise (band check below).\n"
        "- iter-v3/021 / HBAR+AVAX (combined IS PnL -86%) is the structural "
        "warning: universe expansion at single-seed --exploration budget is "
        "risky. The per-symbol-feature-signature criterion is the corrected "
        "selection mechanism; iter-v3/029's ALGO success at +20.87 OOS "
        "confirms the methodology, but a single positive outcome does NOT "
        "guarantee generalization.\n"
        "- NATR band test for the new symbol's labeling: if the candidate's "
        "NATR_21 distribution is materially higher than the (1.5, 0.75) band "
        "fits (>5% sustained), recommend testing default (2.0, 1.0) "
        "multipliers — NOT applying LDO's adaptation. (Diagnostic only; the "
        "iter-v3/033 brief uses default multipliers per single-axis discipline.)\n"
    )

    out_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== iter-v3/033 per-symbol feature analysis (4 incumbents) + 5th candidate eval ===\n")

    # Phase 1
    long_df = build_signature_long()
    long_df.to_csv(OUT_DIR / "per_symbol_feature_signature.csv", index=False)
    disp_df = build_dispersion(long_df)
    disp_df.to_csv(OUT_DIR / "feature_dispersion_ranking.csv", index=False)
    cls_df = identify_symbol_specific(disp_df)
    cls_df.to_csv(OUT_DIR / "symbol_specific_features.csv", index=False)
    top_bot_df = build_top_bottom_per_symbol(long_df)
    top_bot_df.to_csv(OUT_DIR / "symbol_specific_top_bottom.csv", index=False)
    shared_top_7 = shared_top_n_features(long_df, top_n=7)

    print(f"Phase 1: {len(long_df)} long signature rows, {len(disp_df)} dispersion rows.")
    print(f"  HIGH-DISP-SYMBOL-SPECIFIC: {len(cls_df[cls_df['classification'] == 'HIGH-DISP-SYMBOL-SPECIFIC'])}")
    print(f"  MID-DISP: {len(cls_df[cls_df['classification'] == 'MID-DISP'])}")
    print(f"  LOW-DISP-SHARED: {len(cls_df[cls_df['classification'] == 'LOW-DISP-SHARED'])}")
    print(f"  SHARED top-7 across all 4 incumbents: {sorted(shared_top_7) or '(none — fallback to iter-v3/029 anchor)'}")
    print()

    # Phase 3
    btc_df = trim_is(load_klines("BTCUSDT"))
    incumbent_data: dict[str, pd.DataFrame] = {}
    for sym in INCUMBENTS:
        incumbent_data[sym] = trim_is(load_klines(sym))

    candidate_rows: list[dict[str, object]] = []
    for cand in CANDIDATES:
        try:
            cand_df_full = load_klines(cand)
        except FileNotFoundError as e:
            print(f"SKIP {cand}: {e}")
            continue

        g1 = gate_1_data_quality(cand)
        g2 = gate_2_liquidity(cand)
        cand_df = trim_is(cand_df_full)
        if len(cand_df) < 1500:
            print(f"SKIP {cand}: too few IS bars ({len(cand_df)})")
            continue
        g3 = gate_3_alignment(cand_df, incumbent_data, btc_df, tuple(sorted(shared_top_7)))

        gates_pass = bool(g1["gate1_pass"]) and bool(g2["gate2_pass"]) and g3["natr_band_ok"]
        row = {
            "symbol": cand,
            **g1,
            **g2,
            **g3,
            "gates_pass": gates_pass,
        }
        candidate_rows.append(row)

    # Composite scoring (only on rows with valid btc_coupling_std)
    valid_rows = [r for r in candidate_rows if not np.isnan(float(r["btc_coupling_std"]))]
    if valid_rows:
        cs_min = min(float(r["btc_coupling_std"]) for r in valid_rows)
        cs_max = max(float(r["btc_coupling_std"]) for r in valid_rows)
        for r in candidate_rows:
            cs = float(r["btc_coupling_std"])
            if np.isnan(cs):
                r["btc_coupling_z"] = float("nan")
                r["composite"] = float("nan")
                continue
            r["btc_coupling_z"] = (cs - cs_min) / (cs_max - cs_min) if cs_max > cs_min else 0.5
            natr_band_score = 1 if r["natr_band_ok"] else 0
            r["composite"] = round(
                0.65 * float(r["alignment_score"])
                + 0.20 * natr_band_score
                + 0.15 * float(r["btc_coupling_z"]),
                4,
            )
    candidate_rows.sort(key=lambda r: float(r.get("composite", 0)) if not np.isnan(float(r.get("composite", 0))) else -999, reverse=True)

    # Save candidate alignment + ranking CSVs
    if candidate_rows:
        align_df = pd.DataFrame(
            [
                {
                    "symbol": r["symbol"],
                    "alignment_features_used": r["alignment_features_used"],
                    "alignment_score": r["alignment_score"],
                    "raw_corr_BCH": r["raw_corr_BCH"],
                    "raw_corr_LDO": r["raw_corr_LDO"],
                    "raw_corr_TRX": r["raw_corr_TRX"],
                    "raw_corr_ALGO": r["raw_corr_ALGO"],
                    "raw_corr_mean_abs": r["raw_corr_mean_abs"],
                    "natr_21_pct": r["natr_21_pct"],
                    "natr_band_ok": r["natr_band_ok"],
                    "btc_coupling_std": r["btc_coupling_std"],
                    "is_n_klines": r["is_n_klines"],
                }
                for r in candidate_rows
            ]
        )
        align_df.to_csv(OUT_DIR / "candidate_features_alignment.csv", index=False)

        rank_df = pd.DataFrame(
            [
                {
                    "rank": i + 1,
                    "symbol": r["symbol"],
                    "composite": r.get("composite", float("nan")),
                    "alignment_score": r["alignment_score"],
                    "raw_corr_mean_abs": r["raw_corr_mean_abs"],
                    "natr_21_pct": r["natr_21_pct"],
                    "natr_band_ok": r["natr_band_ok"],
                    "btc_coupling_std": r["btc_coupling_std"],
                    "gate1_pass": r["gate1_pass"],
                    "gate2_pass": r["gate2_pass"],
                    "gates_pass": r["gates_pass"],
                    "is_qvol_mean_$": r["is_qvol_mean_$"],
                    "is_qvol_p10_$": r["is_qvol_p10_$"],
                    "pre_IS_history_months": r["pre_IS_history_months"],
                    "coverage_pct": r["coverage_pct"],
                }
                for i, r in enumerate(candidate_rows)
            ]
        )
        rank_df.to_csv(OUT_DIR / "candidate_targeted_ranking.csv", index=False)

    print("=== Candidate ranking (composite descending) ===\n")
    for r in candidate_rows:
        comp = float(r.get("composite", float("nan")))
        comp_s = f"{comp:.4f}" if not np.isnan(comp) else "—"
        gates = "PASS" if r["gates_pass"] else "FAIL"
        print(
            f"  {r['symbol']:>10}  composite={comp_s}  alignment={float(r['alignment_score']):.4f}  "
            f"NATR={float(r['natr_21_pct']):.2f}%  raw_corr={float(r['raw_corr_mean_abs']):.4f}  "
            f"qvol_is_mean=${float(r['is_qvol_mean_$']):,.0f}  gates={gates}"
        )
    print()

    # Choose top-1 passing all gates
    chosen: dict[str, object] = {}
    for r in candidate_rows:
        if r["gates_pass"]:
            chosen = r
            break

    pnl = load_per_symbol_pnl()
    write_synthesis(long_df, disp_df, cls_df, top_bot_df, shared_top_7, candidate_rows, pnl, chosen)

    if chosen:
        print(f"=== TOP CANDIDATE (gates PASS): {chosen['symbol']} (composite {float(chosen['composite']):.4f}) ===")
    else:
        print("=== NO CANDIDATE PASSED ALL GATES ===")
    print()
    print("Written:")
    print(f"  {OUT_DIR / 'per_symbol_feature_signature.csv'}")
    print(f"  {OUT_DIR / 'feature_dispersion_ranking.csv'}")
    print(f"  {OUT_DIR / 'symbol_specific_features.csv'}")
    print(f"  {OUT_DIR / 'symbol_specific_top_bottom.csv'}")
    print(f"  {OUT_DIR / 'candidate_features_alignment.csv'}")
    print(f"  {OUT_DIR / 'candidate_targeted_ranking.csv'}")
    print(f"  {OUT_DIR / 'synthesis.md'}")


if __name__ == "__main__":
    main()
