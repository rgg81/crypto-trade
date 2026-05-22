"""iter-v3/128 — WILD axis EDA: 6-symbol sector-pure L1 universe at 8h with rolling-endpoint methodology fix.

Tables produced (committed before brief per `feedback_v3_axis_selection_quant_discipline.md`):
- T1: Universe + frequency + feature stack catalog
- T2: Universe-feature-distribution audit (intra-universe ret_corr; ADF stationarity)
- T3: Walk-forward feature->label predictive screen WITH rolling-endpoint methodology (3 IS-endpoint slices)
- T4: Per-symbol AUC + rank stability across endpoint slices
- T5: ADF + IC checks against /121 14-feature stack incumbents
- T6: Pre-flight gate decision

The rolling-endpoint methodology fix (per `feedback_v3_eda_methodology_falsified.md`):
- The single-window EDA importance + 5-fold walk-forward AUC methodology has been FALSIFIED at 3-occurrence
  pattern in cycle-7 (/122 + /123 + /126) for NEW-feature axes.
- /128 is a UNIVERSE axis (not a NEW-feature axis), so the FORBIDDEN ban does NOT apply.
- BUT per user mandate point 6: bake rolling-endpoint methodology INTO the EDA pre-flight gates.
- We compute AUC + importance rank at 3 IS endpoint slices: 2023-Q1, 2024-Q1, 2025-Q1.
- A symbol whose AUC range > 0.05 across slices is HIGH-RISK.
- A symbol whose top-3 importance rank shifts > 5 positions is HIGH-RISK.

USAGE:
    uv run python analysis/iteration_v3-128/eda.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import roc_auc_score
from statsmodels.tsa.stattools import adfuller

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
THIS_DIR = Path(__file__).parent
REPO_ROOT = THIS_DIR.parent.parent
FEATURES_DIR = REPO_ROOT / "data" / "features_v3"

# Chosen WILD universe: 6-symbol sector-pure L1 chains
CANDIDATE_SYMBOLS = (
    "ATOMUSDT",
    "RUNEUSDT",
    "AVAXUSDT",
    "HBARUSDT",
    "ICPUSDT",
    "ALGOUSDT",
)

# /121-canonical 14-feature stack
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
    "regime_momentum_signed_5d",
)

# OOS_CUTOFF
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00 UTC

# IS endpoint slices for rolling-endpoint methodology fix
# Each slice's training end is set to a different IS quarter; OOS start same.
# This simulates the EDA-vs-runner walk-forward bias finding from /122/123/126.
IS_ENDPOINT_SLICES = (
    ("slice_2023Q1", "2023-03-31T23:59:59Z"),
    ("slice_2024Q1", "2024-03-31T23:59:59Z"),
    ("slice_2025Q1", "2025-02-28T23:59:59Z"),  # right before OOS_CUTOFF
)

# Triple-barrier label parameters (/121-canonical K=21, +2/-1 ATR)
LABEL_TIMEOUT_CANDLES = 21
ATR_TP = 2.0
ATR_SL = 1.0

# ATR lookback for labeling (matching v3 default)
ATR_WINDOW = 14


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------
def load_feature_panel(symbol: str) -> pd.DataFrame:
    """Load 8h feature parquet for one symbol."""
    path = FEATURES_DIR / f"{symbol}_8h_features.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Missing feature parquet: {path}")
    df = pd.read_parquet(path)
    # Sanity: 14 anchor features present
    missing = [c for c in V3_FEATURE_COLUMNS_TOP_N if c not in df.columns]
    if missing:
        raise ValueError(f"{symbol}: missing anchor features: {missing}")
    df = df.sort_values("open_time").reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Past-only triple-barrier labels (matching v3 production labeling)
# ---------------------------------------------------------------------------
def compute_atr_past_only(df: pd.DataFrame, window: int = ATR_WINDOW) -> pd.Series:
    """Past-only ATR (Wilder) — at time t, uses only data up to and including t."""
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    # Wilder EMA: alpha = 1/window
    atr = tr.ewm(alpha=1.0 / window, adjust=False).mean()
    return atr


def compute_triple_barrier_labels(
    df: pd.DataFrame,
    timeout_candles: int = LABEL_TIMEOUT_CANDLES,
    atr_tp: float = ATR_TP,
    atr_sl: float = ATR_SL,
) -> pd.Series:
    """Triple-barrier label: +1 if TP hit first, -1 if SL hit first, 0 if timeout.

    Past-only ATR computed at bar t; barriers projected forward over [t+1, t+K].
    Used for predictive screen — directional sign(label) is the binary target.
    """
    n = len(df)
    atr = compute_atr_past_only(df).to_numpy()
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)

    labels = np.zeros(n, dtype=np.int8)
    for i in range(n):
        if np.isnan(atr[i]) or atr[i] <= 0:
            labels[i] = 0
            continue
        entry = close[i]
        tp_long = entry + atr_tp * atr[i]
        sl_long = entry - atr_sl * atr[i]
        # Default to timeout (label=0)
        decided = 0
        end = min(i + 1 + timeout_candles, n)
        for j in range(i + 1, end):
            if high[j] >= tp_long:
                decided = 1
                break
            if low[j] <= sl_long:
                decided = -1
                break
        labels[i] = decided
    return pd.Series(labels, index=df.index, name="tb_label")


# ---------------------------------------------------------------------------
# EDA Tables
# ---------------------------------------------------------------------------
def t1_universe_catalog() -> pd.DataFrame:
    """T1 — Universe + frequency + feature stack catalog."""
    rows = []
    for sym in CANDIDATE_SYMBOLS:
        df = load_feature_panel(sym)
        first_ms = int(df["open_time"].min())
        last_ms = int(df["open_time"].max())
        first_dt = datetime.fromtimestamp(first_ms / 1000, tz=timezone.utc)
        last_dt = datetime.fromtimestamp(last_ms / 1000, tz=timezone.utc)
        is_rows = len(df[df["open_time"] < OOS_CUTOFF_MS])
        oos_rows = len(df[df["open_time"] >= OOS_CUTOFF_MS])
        # IS months evaluable
        is_df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
        is_df["month"] = pd.to_datetime(is_df["open_time"], unit="ms").dt.to_period("M")
        is_months = is_df["month"].nunique()
        rows.append({
            "symbol": sym,
            "first_bar_utc": first_dt.strftime("%Y-%m-%d"),
            "last_bar_utc": last_dt.strftime("%Y-%m-%d"),
            "total_bars": len(df),
            "IS_bars": is_rows,
            "OOS_bars": oos_rows,
            "IS_months": is_months,
        })
    out = pd.DataFrame(rows)
    out.to_csv(THIS_DIR / "T1_universe_catalog.csv", index=False)
    print("[T1] Universe catalog written")
    print(out.to_string(index=False))
    return out


def t2_intra_universe_correlation() -> pd.DataFrame:
    """T2 — Intra-universe close-return correlation matrix + ADF stationarity check."""
    panels = {}
    for sym in CANDIDATE_SYMBOLS:
        df = load_feature_panel(sym)
        df = df[df["open_time"] < OOS_CUTOFF_MS]  # IS only
        ret = np.log(df["close"].astype(float)).diff().dropna()
        panels[sym] = ret
    # Align on common time index — use intersection of bars
    aligned = pd.DataFrame(panels)
    corr = aligned.corr()
    corr.to_csv(THIS_DIR / "T2_intra_universe_ret_corr.csv")
    print("\n[T2] Intra-universe IS log-return correlation matrix")
    print(corr.round(3).to_string())

    # ADF stationarity per symbol's IS return series
    adf_rows = []
    for sym, ret in panels.items():
        if len(ret) < 50:
            adf_rows.append({"symbol": sym, "n_obs": len(ret), "adf_stat": np.nan, "p_value": np.nan, "stationary": False})
            continue
        try:
            stat, pval = adfuller(ret.dropna(), autolag="AIC")[:2]
            adf_rows.append({"symbol": sym, "n_obs": len(ret), "adf_stat": stat, "p_value": pval, "stationary": pval < 1e-3})
        except Exception as e:
            adf_rows.append({"symbol": sym, "n_obs": len(ret), "adf_stat": np.nan, "p_value": np.nan, "stationary": False, "error": str(e)})
    adf = pd.DataFrame(adf_rows)
    adf.to_csv(THIS_DIR / "T2_adf_intra_universe.csv", index=False)
    print("\n[T2] ADF stationarity per symbol IS log-returns")
    print(adf.to_string(index=False))
    # Max pairwise correlation
    upper = corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1))
    max_corr = float(upper.abs().max().max())
    print(f"\n[T2] Max pairwise |ret_corr| = {max_corr:.3f}  (G2 gate: < 0.85)")
    return corr


def _slice_endpoint_ms(label: str) -> int:
    """Convert ISO datetime to millisecond timestamp."""
    dt_str = dict(IS_ENDPOINT_SLICES)[label]
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)


def _fit_predict_lgbm(
    train_X: pd.DataFrame,
    train_y: pd.Series,
    test_X: pd.DataFrame,
    test_y: pd.Series,
) -> tuple[float, np.ndarray]:
    """Fit LightGBM at production-like depth-3, return (AUC, feature_importances)."""
    # Use depth-3 / 100 trees / colsample 0.7 — production-like minimal config.
    # Filter to binary (+1 vs -1; drop timeout=0 for clean directional prediction).
    train_mask = train_y.isin([-1, 1])
    test_mask = test_y.isin([-1, 1])
    if train_mask.sum() < 50 or test_mask.sum() < 20:
        return np.nan, np.zeros(train_X.shape[1])
    train_y_bin = (train_y[train_mask] == 1).astype(int)
    test_y_bin = (test_y[test_mask] == 1).astype(int)
    model = LGBMClassifier(
        n_estimators=100,
        max_depth=3,
        num_leaves=8,
        learning_rate=0.05,
        colsample_bytree=0.7,
        random_state=42,
        verbose=-1,
    )
    model.fit(train_X[train_mask], train_y_bin)
    preds = model.predict_proba(test_X[test_mask])[:, 1]
    # Handle constant-prediction degenerate
    if test_y_bin.nunique() < 2:
        return np.nan, model.feature_importances_
    try:
        auc = roc_auc_score(test_y_bin, preds)
    except Exception:
        auc = np.nan
    return float(auc), model.feature_importances_


def t3_t4_rolling_endpoint_auc_per_symbol() -> tuple[pd.DataFrame, pd.DataFrame]:
    """T3 + T4 — Rolling-endpoint AUC + importance rank stability across 3 IS slices.

    For each of the 3 IS endpoint slices (2023-Q1, 2024-Q1, 2025-Q1):
      - Train LightGBM on data [start, slice_end - 6 months]
      - Test on holdout [slice_end - 6 months, slice_end] (6-month forward window)
      - Record AUC + feature_importance ranks for 14 anchor features
    Compute per-symbol AUC range (max - min) and top-3 rank-shift range.
    """
    auc_rows = []
    importance_rows = []
    for sym in CANDIDATE_SYMBOLS:
        df = load_feature_panel(sym)
        df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
        # Compute labels on this symbol's IS data
        df["tb_label"] = compute_triple_barrier_labels(df)
        # Strip rows where features have NaN (warmup) — the longest warmup is ret_skew_200 ≈ 200 bars
        feat_cols = list(V3_FEATURE_COLUMNS_TOP_N)
        df = df.dropna(subset=feat_cols).reset_index(drop=True)

        for slice_label, _slice_dt_str in IS_ENDPOINT_SLICES:
            slice_end_ms = _slice_endpoint_ms(slice_label)
            holdout_start_ms = slice_end_ms - 6 * 30 * 86400 * 1000  # 6 months back
            train_df = df[df["open_time"] < holdout_start_ms]
            test_df = df[(df["open_time"] >= holdout_start_ms) & (df["open_time"] < slice_end_ms)]
            if len(train_df) < 200 or len(test_df) < 50:
                auc_rows.append({
                    "symbol": sym, "slice": slice_label,
                    "train_n": len(train_df), "test_n": len(test_df),
                    "auc": np.nan, "tb_long": np.nan, "tb_short": np.nan,
                })
                continue
            train_X = train_df[feat_cols]
            train_y = train_df["tb_label"]
            test_X = test_df[feat_cols]
            test_y = test_df["tb_label"]
            auc, importances = _fit_predict_lgbm(train_X, train_y, test_X, test_y)
            auc_rows.append({
                "symbol": sym, "slice": slice_label,
                "train_n": len(train_df), "test_n": len(test_df),
                "auc": auc,
                "tb_long": int((train_y == 1).sum()),
                "tb_short": int((train_y == -1).sum()),
                "tb_timeout": int((train_y == 0).sum()),
            })
            # Importance ranks
            imp_series = pd.Series(importances, index=feat_cols).sort_values(ascending=False)
            ranks = imp_series.rank(ascending=False).astype(int)
            for feat in feat_cols:
                importance_rows.append({
                    "symbol": sym, "slice": slice_label, "feature": feat,
                    "importance": float(imp_series.get(feat, 0)),
                    "rank": int(ranks.get(feat, 0)),
                })

    auc_df = pd.DataFrame(auc_rows)
    auc_df.to_csv(THIS_DIR / "T3_rolling_endpoint_auc.csv", index=False)
    print("\n[T3] Rolling-endpoint AUC across 3 IS slices")
    print(auc_df.to_string(index=False))

    # Compute per-symbol AUC range
    summary_rows = []
    for sym in CANDIDATE_SYMBOLS:
        sub = auc_df[auc_df["symbol"] == sym].copy()
        valid = sub.dropna(subset=["auc"])
        if len(valid) == 0:
            summary_rows.append({"symbol": sym, "auc_min": np.nan, "auc_max": np.nan, "auc_range": np.nan, "auc_mean": np.nan, "g4_stability": "NO_DATA"})
            continue
        auc_min = float(valid["auc"].min())
        auc_max = float(valid["auc"].max())
        auc_range = auc_max - auc_min
        g4_pass = auc_range < 0.05
        summary_rows.append({
            "symbol": sym,
            "auc_min": auc_min,
            "auc_max": auc_max,
            "auc_range": auc_range,
            "auc_mean": float(valid["auc"].mean()),
            "g4_stability": "PASS" if g4_pass else "HIGH_RISK",
        })
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(THIS_DIR / "T4_per_symbol_auc_stability.csv", index=False)
    print("\n[T4] Per-symbol AUC stability summary (G4: range < 0.05)")
    print(summary.to_string(index=False))

    # Importance ranks → rank stability
    imp_df = pd.DataFrame(importance_rows)
    if len(imp_df) > 0:
        imp_df.to_csv(THIS_DIR / "T4_importance_ranks_per_slice.csv", index=False)

        # Top-3 rank shift per symbol — pick the 3 features that are most consistently top across slices
        rank_shift_rows = []
        for sym in CANDIDATE_SYMBOLS:
            sub = imp_df[imp_df["symbol"] == sym].copy()
            if len(sub) == 0:
                rank_shift_rows.append({"symbol": sym, "top3_max_shift": np.nan, "g5_stability": "NO_DATA"})
                continue
            # Per-feature mean rank
            mean_rank = sub.groupby("feature")["rank"].mean().sort_values()
            top3_features = mean_rank.head(3).index.tolist()
            shifts = []
            for feat in top3_features:
                ranks = sub[sub["feature"] == feat]["rank"].astype(int).tolist()
                if len(ranks) >= 2:
                    shifts.append(max(ranks) - min(ranks))
            max_shift = max(shifts) if shifts else np.nan
            g5_pass = (not np.isnan(max_shift)) and (max_shift < 5)
            rank_shift_rows.append({
                "symbol": sym,
                "top3_features": ",".join(top3_features),
                "top3_max_shift": max_shift,
                "g5_stability": "PASS" if g5_pass else "HIGH_RISK",
            })
        rank_shifts = pd.DataFrame(rank_shift_rows)
        rank_shifts.to_csv(THIS_DIR / "T4_rank_stability.csv", index=False)
        print("\n[T4] Per-symbol top-3 importance rank stability (G5: max shift < 5 positions)")
        print(rank_shifts.to_string(index=False))
    return auc_df, summary


def t5_ic_check_against_incumbents() -> pd.DataFrame:
    """T5 — IC distribution check: per-symbol Spearman IC of label against the 14 anchor features.

    For each symbol, compute Spearman IC of triple-barrier label against each of the 14
    anchor features over IS. Used as a sanity-check that the 14-feature stack carries
    measurable signal in the new universe at all (per-symbol).
    """
    rows = []
    feat_cols = list(V3_FEATURE_COLUMNS_TOP_N)
    for sym in CANDIDATE_SYMBOLS:
        df = load_feature_panel(sym)
        df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
        df["tb_label"] = compute_triple_barrier_labels(df)
        df = df.dropna(subset=feat_cols + ["tb_label"]).reset_index(drop=True)
        if len(df) < 200:
            continue
        # IC against binary direction (drop timeout)
        directional = df[df["tb_label"].isin([-1, 1])].copy()
        for feat in feat_cols:
            if directional[feat].std() == 0:
                ic = 0.0
                pval = 1.0
            else:
                from scipy.stats import spearmanr
                ic, pval = spearmanr(directional[feat], directional["tb_label"])
                if np.isnan(ic):
                    ic, pval = 0.0, 1.0
            rows.append({
                "symbol": sym, "feature": feat,
                "n": len(directional),
                "ic": float(ic),
                "p_value": float(pval),
                "abs_ic": abs(float(ic)),
            })
    out = pd.DataFrame(rows)
    out.to_csv(THIS_DIR / "T5_per_symbol_ic.csv", index=False)
    print("\n[T5] Per-symbol IC distribution against 14 anchor features (summary):")
    summary = out.groupby("symbol").agg(
        ic_mean_abs=("abs_ic", "mean"),
        ic_max_abs=("abs_ic", "max"),
        n_significant_p_lt_05=("p_value", lambda s: (s < 0.05).sum()),
    ).reset_index()
    print(summary.to_string(index=False))
    summary.to_csv(THIS_DIR / "T5_ic_summary.csv", index=False)
    return out


def t6_preflight_gate_decision(t1: pd.DataFrame, t2_corr: pd.DataFrame, t4_auc: pd.DataFrame) -> dict:
    """T6 — Pre-flight gate aggregation + GO/NO-GO decision."""
    gates = {}

    # G1: data depth ≥ 30 IS months per symbol
    g1_results = []
    for _, r in t1.iterrows():
        is_months = int(r["IS_months"])
        g1_results.append({"symbol": r["symbol"], "is_months": is_months, "g1_pass": is_months >= 30})
    g1_all_pass = all(x["g1_pass"] for x in g1_results)
    gates["G1_data_depth_30mo"] = {
        "pass": g1_all_pass,
        "per_symbol": g1_results,
    }

    # G2: pairwise correlation < 0.85
    upper = t2_corr.where(np.triu(np.ones(t2_corr.shape, dtype=bool), k=1))
    max_corr = float(upper.abs().max().max())
    g2_pass = max_corr < 0.85
    gates["G2_max_pairwise_ret_corr_lt_085"] = {
        "pass": g2_pass,
        "max_pairwise_abs_corr": max_corr,
    }

    # G3 will use ADF results - we already wrote T2_adf
    adf_path = THIS_DIR / "T2_adf_intra_universe.csv"
    g3_results = []
    if adf_path.exists():
        adf_df = pd.read_csv(adf_path)
        for _, r in adf_df.iterrows():
            stat_pass = bool(r["stationary"]) if not pd.isna(r["p_value"]) else False
            g3_results.append({"symbol": r["symbol"], "p_value": r["p_value"], "stationary": stat_pass})
    g3_all_pass = all(x["stationary"] for x in g3_results)
    gates["G3_adf_stationary_p_lt_e-3"] = {
        "pass": g3_all_pass,
        "per_symbol": g3_results,
    }

    # G4: AUC stability range < 0.05 (INFORMATIONAL, not pass-required)
    g4_results = []
    for _, r in t4_auc.iterrows():
        g4_pass = (not pd.isna(r["auc_range"])) and r["auc_range"] < 0.05
        g4_results.append({
            "symbol": r["symbol"],
            "auc_mean": r["auc_mean"] if not pd.isna(r["auc_mean"]) else None,
            "auc_range": r["auc_range"] if not pd.isna(r["auc_range"]) else None,
            "g4_informational_pass": g4_pass,
        })
    g4_all_pass = all(x["g4_informational_pass"] for x in g4_results)
    gates["G4_auc_stability_range_lt_005"] = {
        "informational_pass": g4_all_pass,
        "per_symbol": g4_results,
    }

    # G5 will come from T4_rank_stability if file exists
    rank_path = THIS_DIR / "T4_rank_stability.csv"
    g5_results = []
    if rank_path.exists():
        rank_df = pd.read_csv(rank_path)
        for _, r in rank_df.iterrows():
            g5_pass = (not pd.isna(r["top3_max_shift"])) and r["top3_max_shift"] < 5
            g5_results.append({
                "symbol": r["symbol"],
                "top3_max_shift": int(r["top3_max_shift"]) if not pd.isna(r["top3_max_shift"]) else None,
                "g5_informational_pass": g5_pass,
            })
    g5_all_pass = all(x["g5_informational_pass"] for x in g5_results) if g5_results else False
    gates["G5_top3_rank_shift_lt_5"] = {
        "informational_pass": g5_all_pass,
        "per_symbol": g5_results,
    }

    # G6: universe-pooled AUC mean > 0.51 (INFORMATIONAL)
    valid_auc = t4_auc.dropna(subset=["auc_mean"])
    pool_auc_mean = float(valid_auc["auc_mean"].mean()) if len(valid_auc) > 0 else np.nan
    g6_pass = (not np.isnan(pool_auc_mean)) and pool_auc_mean > 0.51
    gates["G6_universe_pooled_auc_gt_051"] = {
        "informational_pass": g6_pass,
        "universe_pooled_auc_mean": pool_auc_mean,
    }

    # GO/NO-GO Decision
    hard_gates_pass = g1_all_pass and g2_pass and g3_all_pass
    informational_pass_count = sum([g4_all_pass, g5_all_pass, g6_pass])
    decision = "GO" if hard_gates_pass else "NO-GO"
    gates["decision"] = {
        "hard_gates_g1_g2_g3_pass": hard_gates_pass,
        "informational_gates_pass_count": informational_pass_count,
        "informational_gates_total": 3,
        "go_no_go": decision,
        "note": (
            "GO decision requires hard gates G1+G2+G3 ALL PASS. Informational gates G4+G5+G6 "
            "report rolling-endpoint methodology-fix flags. A GO with low informational-gate "
            "pass count signals HIGH-RISK posture (the rolling-endpoint EDA flags symbols "
            "whose AUC/rank-stability is unstable across 3 IS endpoint slices) — brief Section "
            "6 must address."
        ),
    }

    # Write JSON summary
    with open(THIS_DIR / "T6_preflight_gates.json", "w") as f:
        json.dump(gates, f, indent=2, default=str)

    print("\n[T6] Pre-flight gate decision:")
    print(json.dumps(gates, indent=2, default=str))
    return gates


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"iter-v3/128 — WILD axis EDA — 6-symbol sector-pure L1 universe at 8h")
    print(f"Universe: {', '.join(CANDIDATE_SYMBOLS)}")
    print(f"Rolling-endpoint methodology fix: 3 IS slices = {[s for s, _ in IS_ENDPOINT_SLICES]}")
    print(f"Anchor stack: {len(V3_FEATURE_COLUMNS_TOP_N)} features (/121 canonical)")
    print("=" * 80)

    t1 = t1_universe_catalog()
    t2_corr = t2_intra_universe_correlation()
    t3_t4_auc, t4_summary = t3_t4_rolling_endpoint_auc_per_symbol()
    _t5 = t5_ic_check_against_incumbents()
    gates = t6_preflight_gate_decision(t1, t2_corr, t4_summary)
    print("\n" + "=" * 80)
    print(f"FINAL DECISION: {gates['decision']['go_no_go']}")


if __name__ == "__main__":
    main()
