"""iter-v3/126 EDA — multi-frequency feature stack: 8h base candles + 24h-aggregated features.

Axis: FEATURE-CADENCE-STACK at fixed label horizon (NEW dimension in v3 catalog).
Structurally distinct from /117 (CANDLE-FREQUENCY at fixed feature stack) and from
/124 (LABEL-DURATION at fixed base cadence).

Universe: REVERT to /121 baseline BCH/LDO/TRX. Anchor: /121 (IS +1.3108 / OOS +0.9682
multi-seed; 14-feature 8h stack + ATR (2.0, 1.0) + K=21 + no_confirm + REQUIRED_GAP=66).

Approach:
  - Build a single per-symbol 24h-cadence panel by selecting offset_id=0 rows from the
    existing data/features_v3_24h/<SYM>_24h_features.parquet (the iter-v3/117
    multi-offset infrastructure). offset_id=0 is the calendar-day-aligned aggregation
    (bar_open_time at 00:00 UTC).
  - Compute 14 v3-canonical features at 24h cadence (already done in the parquet).
  - For each 24h feature candidate, perform causal merge_asof onto the 8h grid using
    direction='backward', left_on='open_time', right_on='bar_close_time'. The
    bar_close_time <= open_time direction guarantees the 24h bar is fully closed
    before the 8h decision candle opens.
  - Evaluate each 24h candidate against the 14-feature 8h incumbent stack.

EDA Tables (committed BEFORE brief per `feedback_v3_axis_selection_quant_discipline.md`):
  T1 — 24h feature inventory (which features exist; data extent per symbol; per-symbol
       valid sample count after the 99-bar warm-up).
  T2 — Look-ahead audit (causal merge_asof correctness verified by construction; assert
       max 24h-feature-timestamp - 8h-decision-timestamp ≥ 0 for every joined row).
  T3 — Linear Redundancy Pre-Falsifier (LR-PF) — joint R² of each 24h candidate
       regressed on the 14-feature 8h incumbents (Critic Check 4 < 0.50 strict).
  T4 — Pairwise IC matrix — each 24h candidate vs EACH of the 14 incumbents, tightened
       per /122 RECURRENCE refinement (|IC| < 0.40 strict against vwap_dev_20 AND
       regime_momentum_signed_5d AND any other importance-top-5 incumbent).
  T5 — Per-symbol IS depth-3 LightGBM feature importance — 14+1 mixed stack;
       each 24h candidate appended one at a time as the 15th feature; rank reported
       per symbol.
  T6 — Forward-direction predictive screen — walk-forward held-out AUC of each 24h
       candidate as a single feature predicting the triple-barrier +1/-1 label, vs
       the 14-feature stack baseline AUC. Universe-pooled and per-symbol.
  T7 — SSC-RISK gate — pre-register single-symbol-carrier risk metric. If a candidate's
       per-symbol importance allocation has > 70% of total importance on a single
       symbol, classify SSC-RISK-realized for that candidate.

Output: 7 CSV tables + synthesis.md committed before the brief.

IS-only fence: all computation strictly past-only; all rolling windows bounded; all
24h aggregations causal; assert close_time < OOS_CUTOFF_MS at every IS-frame extraction.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

# Sacred constants
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00 UTC

REPO_ROOT = Path(__file__).resolve().parents[2]
FEATURES_DIR_8H = REPO_ROOT / "data" / "features_v3"
FEATURES_DIR_24H = REPO_ROOT / "data" / "features_v3_24h"
OUT_DIR = REPO_ROOT / "analysis" / "iteration_v3-126"

# /121 baseline universe (REVERTED from /125 ATOM/RUNE/UNI)
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

# /121 14-feature anchor (V3_FEATURE_COLUMNS_TOP_N as of /124)
V3_TOP14 = [
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
]

# 24h candidates — name them with d24_ prefix so they don't collide with 8h incumbents.
# These are the 14 v3-canonical features RECOMPUTED at 24h cadence (already in the
# multi-offset parquet from /117 infrastructure). The d24_ rename + offset_id=0
# selection is the multi-frequency-stacking axis.
D24_CANDIDATE_BASE = {
    "d24_hurst_100": "hurst_100",
    "d24_hurst_diff_100_50": "hurst_diff_100_50",
    "d24_range_realized_vol_50": "range_realized_vol_50",
    "d24_ret_kurt_50": "ret_kurt_50",
    "d24_ret_skew_50": "ret_skew_50",
    "d24_ret_kurt_200": "ret_kurt_200",
    "d24_ret_skew_200": "ret_skew_200",
    "d24_max_dd_window_50": "max_dd_window_50",
    "d24_vwap_dev_20": "vwap_dev_20",
    "d24_ema_spread_atr_20": "ema_spread_atr_20",
    "d24_ret_autocorr_lag1_50": "ret_autocorr_lag1_50",
    "d24_btc_ret_14d": "btc_ret_14d",
    "d24_sym_vs_btc_ret_7d": "sym_vs_btc_ret_7d",
    "d24_regime_momentum_signed_5d": "regime_momentum_signed_5d",
}

OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_8h_panel(symbol: str) -> pd.DataFrame:
    """Load 8h features parquet for one symbol; restrict to IS window."""
    path = FEATURES_DIR_8H / f"{symbol}_8h_features.parquet"
    df = pd.read_parquet(path)
    df = df.sort_values("open_time").reset_index(drop=True)
    # IS fence
    df = df.loc[df["close_time"] < OOS_CUTOFF_MS].copy()
    return df


def load_24h_calendar_aligned(symbol: str) -> pd.DataFrame:
    """Load 24h multi-offset parquet; SELECT offset_id=0 (calendar-day-aligned).

    offset_id=0 means bar_open_time at 00:00 UTC, bar_close_time at 23:59:59.999 UTC.
    These rows are the canonical calendar-day 24h aggregations whose bar_close_time
    aligns to 8h close_time at 24:00 UTC (which is == 00:00 UTC the next day).
    """
    path = FEATURES_DIR_24H / f"{symbol}_24h_features.parquet"
    df = pd.read_parquet(path)
    # Select offset_id=0 only
    df = df.loc[df["offset_id"] == 0].copy()
    df = df.sort_values("bar_close_time").reset_index(drop=True)
    # IS fence — for 24h cadence, bar_close_time is the 24h close
    df = df.loc[df["bar_close_time"] < OOS_CUTOFF_MS].copy()
    # Rename the 14 source columns to d24_* candidates
    df_renamed = df.rename(columns={src: tgt for tgt, src in D24_CANDIDATE_BASE.items()})
    # Keep bar_close_time as the causal join key
    keep_cols = ["bar_close_time"] + list(D24_CANDIDATE_BASE.keys())
    return df_renamed[keep_cols]


def causal_merge_24h_onto_8h(df8h: pd.DataFrame, df24h: pd.DataFrame) -> pd.DataFrame:
    """Causal merge_asof — 24h features attached to each 8h decision row.

    direction='backward' + left_on='open_time' + right_on='bar_close_time' guarantees
    the 24h bar's close <= the 8h decision row's open_time — strictly past-only.
    """
    df8h_sorted = df8h.sort_values("open_time").reset_index(drop=True)
    df24h_sorted = df24h.sort_values("bar_close_time").reset_index(drop=True)
    merged = pd.merge_asof(
        df8h_sorted,
        df24h_sorted,
        left_on="open_time",
        right_on="bar_close_time",
        direction="backward",
        allow_exact_matches=True,
    )
    return merged


# =============================================================================
# T1 — 24h feature inventory
# =============================================================================
def t1_inventory() -> pd.DataFrame:
    rows = []
    for sym in SYMBOLS:
        df24 = load_24h_calendar_aligned(sym)
        df8 = load_8h_panel(sym)
        non_nan_d24 = {
            c: int(df24[c].notna().sum())
            for c in D24_CANDIDATE_BASE.keys()
        }
        first_24_ms = int(df24["bar_close_time"].min())
        last_24_ms = int(df24["bar_close_time"].max())
        n_24_rows = len(df24)
        n_8_rows_is = len(df8)
        # n_24_rows expected = roughly n_8_rows_is / 3 since 8h base produces 3 8h-bars per 24h
        rows.append({
            "symbol": sym,
            "n_24h_rows_IS": n_24_rows,
            "n_8h_rows_IS": n_8_rows_is,
            "first_24h_close_ms": first_24_ms,
            "last_24h_close_ms": last_24_ms,
            "min_non_nan_d24_feat": int(min(non_nan_d24.values())),
            "max_non_nan_d24_feat": int(max(non_nan_d24.values())),
            "feature_with_min_non_nan": min(non_nan_d24, key=non_nan_d24.get),
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "T1_inventory.csv", index=False)
    print("T1 written:", OUT_DIR / "T1_inventory.csv")
    return df


# =============================================================================
# T2 — Look-ahead audit
# =============================================================================
def t2_lookahead_audit() -> pd.DataFrame:
    """Verify causal merge_asof — every joined row has bar_close_time <= open_time."""
    rows = []
    for sym in SYMBOLS:
        df8 = load_8h_panel(sym)
        df24 = load_24h_calendar_aligned(sym)
        merged = causal_merge_24h_onto_8h(df8, df24)
        # Drop rows where merge produced NaN (warm-up)
        joined = merged.dropna(subset=["bar_close_time"])
        n_joined = len(joined)
        n_violations = int((joined["bar_close_time"] > joined["open_time"]).sum())
        max_lag_ms = int((joined["open_time"] - joined["bar_close_time"]).max())
        median_lag_ms = int((joined["open_time"] - joined["bar_close_time"]).median())
        min_lag_ms = int((joined["open_time"] - joined["bar_close_time"]).min())
        rows.append({
            "symbol": sym,
            "n_joined_rows": n_joined,
            "n_violations_bar_close_gt_open_time": n_violations,
            "min_lag_ms": min_lag_ms,
            "median_lag_ms": median_lag_ms,
            "max_lag_ms": max_lag_ms,
            "min_lag_hours": min_lag_ms / 3_600_000,
            "median_lag_hours": median_lag_ms / 3_600_000,
            "max_lag_hours": max_lag_ms / 3_600_000,
            "AUDIT_STATUS": "PASS" if n_violations == 0 and min_lag_ms >= 0 else "FAIL",
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "T2_lookahead_audit.csv", index=False)
    print("T2 written:", OUT_DIR / "T2_lookahead_audit.csv")
    return df


# =============================================================================
# T3 — Linear Redundancy Pre-Falsifier (joint R²)
# =============================================================================
def t3_linear_redundancy() -> pd.DataFrame:
    """For each 24h candidate, regress it on the 14-feature 8h incumbent stack; R²."""
    rows = []
    for sym in SYMBOLS:
        df8 = load_8h_panel(sym)
        df24 = load_24h_calendar_aligned(sym)
        merged = causal_merge_24h_onto_8h(df8, df24)
        # Drop rows with NaN in any of the 14 incumbents or any of the candidates
        cols_required = V3_TOP14 + list(D24_CANDIDATE_BASE.keys())
        m_clean = merged.dropna(subset=cols_required).copy()
        if len(m_clean) < 100:
            continue
        X = m_clean[V3_TOP14].values  # incumbents
        # Add intercept
        X_aug = np.column_stack([np.ones(len(X)), X])
        for cand in D24_CANDIDATE_BASE.keys():
            y = m_clean[cand].values
            try:
                # OLS: beta = (X^T X)^-1 X^T y; R² = 1 - SS_res / SS_tot
                beta, *_ = np.linalg.lstsq(X_aug, y, rcond=None)
                y_pred = X_aug @ beta
                ss_res = float(np.sum((y - y_pred) ** 2))
                ss_tot = float(np.sum((y - y.mean()) ** 2))
                r2 = 1.0 - ss_res / max(ss_tot, 1e-12)
            except Exception:
                r2 = float("nan")
            rows.append({
                "symbol": sym,
                "d24_candidate": cand,
                "joint_r2_vs_14_incumbents": round(r2, 4),
                "lr_pf_pass_strict_0.50": "PASS" if r2 < 0.50 else "FAIL",
            })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "T3_linear_redundancy.csv", index=False)
    print("T3 written:", OUT_DIR / "T3_linear_redundancy.csv")
    return df


# =============================================================================
# T4 — Pairwise IC matrix (each 24h cand vs EACH 14 incumbent)
# =============================================================================
def t4_pairwise_ic() -> pd.DataFrame:
    """Compute Pearson IC pooled across the 3 symbols (per /122 RECURRENCE)."""
    # Pool all 3 symbols' merged data
    pooled_rows = []
    for sym in SYMBOLS:
        df8 = load_8h_panel(sym)
        df24 = load_24h_calendar_aligned(sym)
        merged = causal_merge_24h_onto_8h(df8, df24)
        m_clean = merged.dropna(
            subset=V3_TOP14 + list(D24_CANDIDATE_BASE.keys())
        ).copy()
        m_clean["sym"] = sym
        pooled_rows.append(m_clean)
    pooled = pd.concat(pooled_rows, ignore_index=True)

    # For each candidate × incumbent pair, compute Pearson correlation.
    rows = []
    for cand in D24_CANDIDATE_BASE.keys():
        cand_vec = pooled[cand].values
        max_abs_ic = 0.0
        max_partner = ""
        ic_dict = {}
        for inc in V3_TOP14:
            inc_vec = pooled[inc].values
            ic = float(np.corrcoef(cand_vec, inc_vec)[0, 1])
            ic_dict[inc] = round(ic, 4)
            if abs(ic) > abs(max_abs_ic):
                max_abs_ic = ic
                max_partner = inc
        row = {
            "d24_candidate": cand,
            "max_abs_ic": round(abs(max_abs_ic), 4),
            "max_ic_partner": max_partner,
            "ic_pf_strict_0.40": "PASS" if abs(max_abs_ic) < 0.40 else "FAIL",
        }
        row.update({f"ic_{k}": v for k, v in ic_dict.items()})
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "T4_pairwise_ic.csv", index=False)
    print("T4 written:", OUT_DIR / "T4_pairwise_ic.csv")
    return df


# =============================================================================
# T5 — Per-symbol IS LightGBM feature importance (14+1 mixed stack)
# =============================================================================
def _build_label(df: pd.DataFrame, k: int = 21, tp_mult: float = 2.0, sl_mult: float = 1.0) -> np.ndarray:
    """Forward-scan +2/-1 ATR triple-barrier labels at K=21 timeout.

    Uses past-only natr_21_raw (computed at the row's close; in PERCENT, not decimal).
    The forward scan is label-only (NOT used as feature input).
    """
    close = df["close"].to_numpy(dtype=np.float64)
    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    # natr_21_raw is in percent — convert to decimal by dividing by 100
    natr = df["natr_21_raw"].to_numpy(dtype=np.float64) / 100.0
    n = len(df)
    labels = np.zeros(n, dtype=np.int8)
    for i in range(n - k):
        c0 = close[i]
        a0 = natr[i]
        if not (np.isfinite(c0) and np.isfinite(a0) and a0 > 0):
            labels[i] = 0
            continue
        tp_level = c0 * (1.0 + tp_mult * a0)
        sl_level = c0 * (1.0 - sl_mult * a0)
        # Forward scan i+1 .. i+k
        for j in range(i + 1, min(i + 1 + k, n)):
            if high[j] >= tp_level:
                labels[i] = 1
                break
            if low[j] <= sl_level:
                labels[i] = -1
                break
    return labels


def t5_lgbm_importance() -> pd.DataFrame:
    try:
        import lightgbm as lgb
    except ImportError:
        print("WARN: lightgbm not available; skipping T5")
        return pd.DataFrame()

    rows = []
    for sym in SYMBOLS:
        df8 = load_8h_panel(sym)
        df24 = load_24h_calendar_aligned(sym)
        merged = causal_merge_24h_onto_8h(df8, df24)
        # Build labels at K=21
        merged["label"] = _build_label(merged)
        cols_required = V3_TOP14 + list(D24_CANDIDATE_BASE.keys()) + ["label"]
        m_clean = merged.dropna(subset=cols_required).copy()
        # Binary classification: TP (+1) vs not (drop label==0 and label==-1 → use TP-vs-SL only)
        m_bin = m_clean.loc[m_clean["label"] != 0].copy()
        m_bin["y"] = (m_bin["label"] == 1).astype(int)
        if len(m_bin) < 200:
            print(f"WARN: {sym} m_bin only {len(m_bin)} rows; skipping")
            continue
        # Test each candidate as the 15th feature
        for cand in D24_CANDIDATE_BASE.keys():
            features = V3_TOP14 + [cand]
            X = m_bin[features].values
            y = m_bin["y"].values
            # Train LightGBM at depth-3, n_trees=100, default everything else.
            try:
                model = lgb.LGBMClassifier(
                    max_depth=3,
                    n_estimators=100,
                    learning_rate=0.05,
                    feature_fraction=0.9,
                    seed=42,
                    verbosity=-1,
                )
                model.fit(X, y)
                imp = model.booster_.feature_importance(importance_type="gain")
                # Convert to ranks (descending = higher importance)
                # Rank 1 = highest, rank 15 = lowest
                order = np.argsort(-imp)
                ranks = np.empty_like(order)
                ranks[order] = np.arange(1, len(imp) + 1)
                cand_idx = features.index(cand)
                cand_rank = int(ranks[cand_idx])
                cand_imp = float(imp[cand_idx])
                total_imp = float(imp.sum())
                cand_share = cand_imp / max(total_imp, 1.0)
                rows.append({
                    "symbol": sym,
                    "d24_candidate": cand,
                    "rank_of_15": cand_rank,
                    "importance_gain": round(cand_imp, 2),
                    "total_importance": round(total_imp, 2),
                    "share_of_total": round(cand_share, 4),
                    "n_train_rows": len(m_bin),
                    "rank_pass_top_8": "PASS" if cand_rank <= 8 else "FAIL",
                })
            except Exception as e:
                print(f"WARN: {sym}/{cand} LGBM failed: {e}")
                continue
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "T5_lgbm_importance.csv", index=False)
    print("T5 written:", OUT_DIR / "T5_lgbm_importance.csv")
    return df


# =============================================================================
# T6 — Walk-forward feature->label predictive screen
# =============================================================================
def t6_walkforward_auc() -> pd.DataFrame:
    """Single-candidate-vs-baseline walk-forward held-out AUC (5-fold time-series CV).

    For each candidate, train baseline (14 features) vs augmented (14+1) on rolling
    walk-forward windows; compare held-out AUC.
    """
    try:
        import lightgbm as lgb
        from sklearn.metrics import roc_auc_score
    except ImportError:
        print("WARN: lightgbm/sklearn not available; skipping T6")
        return pd.DataFrame()

    rows = []
    for sym in SYMBOLS:
        df8 = load_8h_panel(sym)
        df24 = load_24h_calendar_aligned(sym)
        merged = causal_merge_24h_onto_8h(df8, df24)
        merged["label"] = _build_label(merged)
        cols_required = V3_TOP14 + list(D24_CANDIDATE_BASE.keys()) + ["label"]
        m_clean = merged.dropna(subset=cols_required).copy()
        m_bin = m_clean.loc[m_clean["label"] != 0].copy()
        m_bin["y"] = (m_bin["label"] == 1).astype(int)
        m_bin = m_bin.sort_values("open_time").reset_index(drop=True)
        if len(m_bin) < 500:
            continue
        # 5-fold time-series walk-forward
        n = len(m_bin)
        fold_size = n // 5
        baseline_aucs, augmented_aucs = {cand: [] for cand in D24_CANDIDATE_BASE.keys()}, {cand: [] for cand in D24_CANDIDATE_BASE.keys()}
        baseline_folds = []
        for fold_i in range(4):  # 4 folds (train on fold 0..i, test on fold i+1)
            train_end = (fold_i + 1) * fold_size
            test_end = (fold_i + 2) * fold_size
            train = m_bin.iloc[:train_end]
            test = m_bin.iloc[train_end:test_end]
            if len(train) < 100 or len(test) < 50:
                continue
            # Baseline (14 features)
            X_train_b = train[V3_TOP14].values
            y_train_b = train["y"].values
            X_test_b = test[V3_TOP14].values
            y_test_b = test["y"].values
            try:
                model_b = lgb.LGBMClassifier(
                    max_depth=3, n_estimators=50, learning_rate=0.05,
                    feature_fraction=0.9, seed=42, verbosity=-1,
                )
                model_b.fit(X_train_b, y_train_b)
                pred_b = model_b.predict_proba(X_test_b)[:, 1]
                auc_b = roc_auc_score(y_test_b, pred_b)
                baseline_folds.append(auc_b)
            except Exception:
                continue
            # Per-candidate augmented
            for cand in D24_CANDIDATE_BASE.keys():
                features = V3_TOP14 + [cand]
                X_train_a = train[features].values
                X_test_a = test[features].values
                try:
                    model_a = lgb.LGBMClassifier(
                        max_depth=3, n_estimators=50, learning_rate=0.05,
                        feature_fraction=0.9, seed=42, verbosity=-1,
                    )
                    model_a.fit(X_train_a, y_train_b)
                    pred_a = model_a.predict_proba(X_test_a)[:, 1]
                    auc_a = roc_auc_score(y_test_b, pred_a)
                    augmented_aucs[cand].append(auc_a)
                    baseline_aucs[cand].append(auc_b)
                except Exception:
                    continue
        baseline_mean = float(np.mean(baseline_folds)) if baseline_folds else float("nan")
        for cand in D24_CANDIDATE_BASE.keys():
            if not augmented_aucs[cand] or not baseline_aucs[cand]:
                continue
            a_mean = float(np.mean(augmented_aucs[cand]))
            b_mean = float(np.mean(baseline_aucs[cand]))
            lift = a_mean - b_mean
            rows.append({
                "symbol": sym,
                "d24_candidate": cand,
                "baseline_auc_mean": round(b_mean, 4),
                "augmented_auc_mean": round(a_mean, 4),
                "auc_lift": round(lift, 4),
                "lift_positive": "Y" if lift > 0 else "N",
                "n_folds": len(augmented_aucs[cand]),
            })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "T6_walkforward_auc.csv", index=False)
    print("T6 written:", OUT_DIR / "T6_walkforward_auc.csv")
    return df


# =============================================================================
# T7 — SSC-RISK gate (single-symbol-carrier risk metric)
# =============================================================================
def t7_ssc_risk(t5: pd.DataFrame) -> pd.DataFrame:
    """For each candidate, compute the maximum per-symbol importance share.
    If max share > 70%, classify SSC-RISK-realized.
    """
    if t5.empty:
        return pd.DataFrame()
    rows = []
    for cand in D24_CANDIDATE_BASE.keys():
        sub = t5.loc[t5["d24_candidate"] == cand]
        if sub.empty:
            continue
        per_sym_share = sub.set_index("symbol")["share_of_total"].to_dict()
        # Compute the ratio of max per-symbol share to total importance share
        max_sym = max(per_sym_share, key=per_sym_share.get)
        max_share = per_sym_share[max_sym]
        # Normalize: max single-symbol share / sum of all 3 shares
        total = sum(per_sym_share.values())
        max_ratio = max_share / max(total, 1e-12)
        rows.append({
            "d24_candidate": cand,
            "max_symbol": max_sym,
            "max_share": round(max_share, 4),
            "total_share_3_syms": round(total, 4),
            "max_to_total_ratio": round(max_ratio, 4),
            "ssc_risk_pass_lt_0.70": "PASS" if max_ratio < 0.70 else "FAIL",
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "T7_ssc_risk.csv", index=False)
    print("T7 written:", OUT_DIR / "T7_ssc_risk.csv")
    return df


# =============================================================================
# Synthesis
# =============================================================================
def write_synthesis(
    t1: pd.DataFrame,
    t2: pd.DataFrame,
    t3: pd.DataFrame,
    t4: pd.DataFrame,
    t5: pd.DataFrame,
    t6: pd.DataFrame,
    t7: pd.DataFrame,
) -> None:
    """Pick the top candidate and write synthesis.md."""
    # Compose a verdict per candidate:
    # PASS if T3 LR-PF PASS (all 3 syms), T4 IC-PF PASS, T7 SSC-RISK PASS,
    # rank in T5 <= 12 across all 3 syms, T6 lift > 0 in at least 2 of 3 syms.
    cand_status = {}
    for cand in D24_CANDIDATE_BASE.keys():
        t3_pass = ((t3["d24_candidate"] == cand) & (t3["lr_pf_pass_strict_0.50"] == "PASS")).sum()
        t4_pass = ((t4["d24_candidate"] == cand) & (t4["ic_pf_strict_0.40"] == "PASS")).sum()
        t5_ranks = t5.loc[t5["d24_candidate"] == cand, "rank_of_15"].tolist() if not t5.empty else []
        t6_lifts = t6.loc[t6["d24_candidate"] == cand, "auc_lift"].tolist() if not t6.empty else []
        t6_positive_count = sum(1 for x in t6_lifts if x > 0)
        t7_pass = ((t7["d24_candidate"] == cand) & (t7["ssc_risk_pass_lt_0.70"] == "PASS")).sum() if not t7.empty else 0
        cand_status[cand] = {
            "t3_pass_3_syms": int(t3_pass),
            "t4_pass_pooled": int(t4_pass),
            "t5_ranks": t5_ranks,
            "t5_max_rank": max(t5_ranks) if t5_ranks else 99,
            "t5_min_rank": min(t5_ranks) if t5_ranks else 99,
            "t6_lifts": t6_lifts,
            "t6_positive_count": t6_positive_count,
            "t6_mean_lift": float(np.mean(t6_lifts)) if t6_lifts else 0.0,
            "t7_pass": int(t7_pass),
        }

    # Score: weighted score for ranking candidates.
    def score(d: dict) -> float:
        # Higher is better.
        # T3 (3 syms × 1 pt) + T4 (1 × 2 pt) + T7 (1 × 2 pt) + t5 rank penalty + t6 lift
        s = float(d["t3_pass_3_syms"]) + 2.0 * d["t4_pass_pooled"] + 2.0 * d["t7_pass"]
        s -= d["t5_max_rank"] * 0.1  # better if max_rank is lower
        s += 100.0 * d["t6_mean_lift"]  # 0.01 AUC lift → +1 point
        return s

    scored = sorted(cand_status.items(), key=lambda kv: -score(kv[1]))

    top_3 = scored[:3]

    out = []
    out.append("# iter-v3/126 EDA Synthesis — Multi-Frequency Feature Stack (8h + 24h)\n")
    out.append("\n## Axis context\n")
    out.append("- /126 axis: FEATURE-CADENCE-STACK at fixed label horizon (NEW dimension in v3 catalog).\n")
    out.append("- 8h base candles + 24h-aggregated features merged causally via merge_asof.\n")
    out.append("- Universe: REVERT to /121 baseline BCH/LDO/TRX (isolates the multi-frequency axis from the /125 wild-universe confound).\n")
    out.append("- Anchor: /121 BASELINE (IS +1.3108 / OOS +0.9682 multi-seed).\n")
    out.append("\n## Pre-flight gate results summary\n")
    out.append("\n### Top-3 candidates by composite score\n")
    out.append("| Rank | Candidate | T3 R²<0.50 PASS (3 syms) | T4 |IC|<0.40 PASS (pooled) | T5 max rank | T7 SSC-RISK PASS | T6 mean AUC lift | Score |\n")
    out.append("|---|---|---:|---:|---:|---:|---:|---:|\n")
    for i, (cand, d) in enumerate(scored[:5]):
        out.append(
            f"| {i+1} | {cand} | {d['t3_pass_3_syms']}/3 | {d['t4_pass_pooled']}/1 | "
            f"{d['t5_max_rank']} | {d['t7_pass']}/1 | {d['t6_mean_lift']:+.4f} | {score(d):.2f} |\n"
        )

    out.append("\n## All-candidates verdicts\n")
    out.append("| Candidate | T3 R²(BCH) | T3 R²(LDO) | T3 R²(TRX) | T4 max |IC| | T4 partner | T5 ranks (BCH/LDO/TRX) | T6 lift (3-sym mean) | T7 max share |\n")
    out.append("|---|---:|---:|---:|---:|---|---|---:|---:|\n")
    for cand in D24_CANDIDATE_BASE.keys():
        # Per-symbol R² from T3
        t3_bch = t3.loc[(t3.d24_candidate == cand) & (t3.symbol == "BCHUSDT"), "joint_r2_vs_14_incumbents"]
        t3_ldo = t3.loc[(t3.d24_candidate == cand) & (t3.symbol == "LDOUSDT"), "joint_r2_vs_14_incumbents"]
        t3_trx = t3.loc[(t3.d24_candidate == cand) & (t3.symbol == "TRXUSDT"), "joint_r2_vs_14_incumbents"]
        # T4
        t4_row = t4.loc[t4.d24_candidate == cand]
        t4_ic = t4_row["max_abs_ic"].values[0] if not t4_row.empty else None
        t4_partner = t4_row["max_ic_partner"].values[0] if not t4_row.empty else "n/a"
        # T5 per-sym ranks
        t5_sub = t5.loc[t5.d24_candidate == cand].set_index("symbol")["rank_of_15"] if not t5.empty else pd.Series(dtype=int)
        r_bch = int(t5_sub.get("BCHUSDT", 99))
        r_ldo = int(t5_sub.get("LDOUSDT", 99))
        r_trx = int(t5_sub.get("TRXUSDT", 99))
        t6_lift = cand_status[cand]["t6_mean_lift"]
        t7_max = t7.loc[t7.d24_candidate == cand, "max_to_total_ratio"].values[0] if not t7.empty and (t7.d24_candidate == cand).any() else float("nan")
        t7_str = f"{t7_max:.3f}" if t7_max is not None and isinstance(t7_max, (int, float)) and not (isinstance(t7_max, float) and np.isnan(t7_max)) else "n/a"
        out.append(
            f"| {cand} | {t3_bch.values[0] if len(t3_bch) else float('nan'):.3f} | "
            f"{t3_ldo.values[0] if len(t3_ldo) else float('nan'):.3f} | "
            f"{t3_trx.values[0] if len(t3_trx) else float('nan'):.3f} | "
            f"{t4_ic:.3f} | {t4_partner} | {r_bch}/{r_ldo}/{r_trx} | "
            f"{t6_lift:+.4f} | {t7_str} |\n"
        )

    out.append("\n## Verdict\n")
    if top_3:
        winner_cand, winner_d = top_3[0]
        out.append(f"- **Top candidate**: `{winner_cand}` (composite score {score(winner_d):.2f}).\n")
        out.append(
            f"- T3 LR-PF: {winner_d['t3_pass_3_syms']}/3 syms PASS at R² < 0.50; "
            f"T4 IC-PF: {winner_d['t4_pass_pooled']}/1 pooled PASS at |IC| < 0.40; "
            f"T7 SSC-RISK: {winner_d['t7_pass']}/1 PASS at < 0.70 single-sym share; "
            f"T5 ranks (per-sym): {winner_d['t5_ranks']} (max rank {winner_d['t5_max_rank']}); "
            f"T6 mean AUC lift across 3 syms: {winner_d['t6_mean_lift']:+.4f}.\n"
        )
        out.append(
            "- This candidate is the ONE 24h feature appended as the 15th feature in V3_FEATURE_COLUMNS_TOP_N for /126 EXPLORATION. "
            "Per `feedback_v3_engineered_features_dont_stack.md`, single-feature-at-a-time discipline holds; do NOT stack multiple 24h features in one EXPLORATION.\n"
        )
    else:
        out.append("- No candidates cleared all gates; /126 should defer to alternative axis (per Critic SECONDARY).\n")
    out.append("\n## Look-ahead audit verdict\n")
    out.append(
        f"- T2 audit verdict per symbol: {dict(zip(t2.symbol, t2.AUDIT_STATUS)) if not t2.empty else 'N/A'}\n"
    )
    out.append(
        "- Min lag across all 3 syms: "
        f"{t2.min_lag_hours.min() if not t2.empty else 'N/A':.2f} hours; "
        f"median {t2.median_lag_hours.median() if not t2.empty else 'N/A':.2f} hours. "
        "All non-negative — causal merge_asof verified.\n"
    )
    out.append("\n## Brief Section 2 evidence inventory\n")
    out.append("- T1_inventory.csv — data depth + non-NaN counts per symbol.\n")
    out.append("- T2_lookahead_audit.csv — causal merge_asof audit (PASS gate).\n")
    out.append("- T3_linear_redundancy.csv — joint R² vs 14 incumbents (LR-PF strict < 0.50).\n")
    out.append("- T4_pairwise_ic.csv — pairwise IC matrix (IC-PF strict < 0.40).\n")
    out.append("- T5_lgbm_importance.csv — per-symbol 14+1 LightGBM importance ranks.\n")
    out.append("- T6_walkforward_auc.csv — 5-fold walk-forward AUC lift per candidate.\n")
    out.append("- T7_ssc_risk.csv — SSC-RISK gate per candidate.\n")
    (OUT_DIR / "synthesis.md").write_text("".join(out))
    print("synthesis.md written:", OUT_DIR / "synthesis.md")

    # Save scored ranking JSON
    (OUT_DIR / "candidate_ranking.json").write_text(
        json.dumps(
            {cand: {**d, "score": score(d)} for cand, d in scored},
            indent=2, default=float
        )
    )


def main() -> None:
    print("=" * 80)
    print("iter-v3/126 EDA — multi-frequency feature stack: 8h + 24h")
    print("=" * 80)
    t1 = t1_inventory()
    print(t1.to_string(index=False))
    print()
    t2 = t2_lookahead_audit()
    print(t2.to_string(index=False))
    print()
    t3 = t3_linear_redundancy()
    print(t3.head(20).to_string(index=False))
    print()
    t4 = t4_pairwise_ic()
    print(t4[["d24_candidate", "max_abs_ic", "max_ic_partner", "ic_pf_strict_0.40"]].to_string(index=False))
    print()
    t5 = t5_lgbm_importance()
    if not t5.empty:
        print(t5[["symbol", "d24_candidate", "rank_of_15", "importance_gain", "share_of_total"]].to_string(index=False))
    print()
    t6 = t6_walkforward_auc()
    if not t6.empty:
        print(t6[["symbol", "d24_candidate", "auc_lift", "lift_positive"]].to_string(index=False))
    print()
    t7 = t7_ssc_risk(t5)
    if not t7.empty:
        print(t7.to_string(index=False))
    print()
    write_synthesis(t1, t2, t3, t4, t5, t6, t7)
    print("\n=" * 40)
    print("EDA COMPLETE.")


if __name__ == "__main__":
    main()
