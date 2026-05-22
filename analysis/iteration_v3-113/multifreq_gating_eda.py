"""iter-v3/113 — multi-frequency feature gating EDA (cycle-6 EXPLORATION #4).

GO/NO-GO question
-----------------
Does adding a COARSER-frequency (1d / daily) feature family to the 8h model's
14-feature stack carry HELD-OUT directional predictive signal that the 8h-only
stack LACKS — on the canonical BCH/LDO/TRX universe, on the /059-faithful
triple-barrier directional label?

Why this axis (carried from the /112 diary + /109 §3): v3 has run all 112
iterations on 8h candles with 8h-derived features. The /105->/109 chain proved
the 14-feature *8h* representation carries no IS-detectable directional signal
to a 100-shuffle permutation test (/109 AUC 0.497, p=0.64). That null is a
property of the 8h representation. A coarser bar frequency is a genuinely
different signal-to-noise regime — daily bars smooth the 8h microstructure
noise the null is built on. This EDA is the decisive Phase-1 design gate: it
measures whether the daily features beat the 8h-only null.

Methodology — walk-forward-faithful, strictly IS-only
-----------------------------------------------------
Per feedback_v3_eda_walkforward_faithful.md, the EDA must replicate the
runner's walk-forward segmentation, NOT score the full IS panel as one block.
The runner trades the post-24-month-training span; the EDA's held-out AUC is
measured on expanding-window walk-forward folds inside the IS window so the
number is a faithful runner-fidelity target.

Test design (8 tables):
  T1  walk-forward held-out AUC: 8h-only stack vs 8h+daily stack (per symbol +
      pooled). The headline horse race.
  T2  the aggregate GO/NO-GO verdict line.
  T3  per-symbol AUC lift breakdown (which symbols, if any, the daily family
      helps).
  T4  permutation null: shuffle the label, re-fit the 8h+daily stack 100x; is
      the observed 8h+daily AUC above the no-signal q95? This is the /109-style
      decisive test applied to the COARSER representation.
  T5  marginal contribution: held-out AUC of a daily-ONLY model (the 8 daily
      features alone, no 8h features) vs its own permutation null — does the
      daily representation carry standalone signal?
  T6  per-daily-feature univariate held-out AUC + walk-forward LightGBM gain
      rank when stacked (importance the 8h-only stack cannot already supply).
  T7  IC of each daily feature against the closest-mechanism 8h feature
      (redundancy screen — per the v3 IC<0.70 family gate).
  T8  gated-tail hit rate: in the top-decile-confidence 8h+daily predictions,
      is the directional hit rate above the 8h-only stack's top-decile hit
      rate? (the production proxy — the 7-gate stack only trades high-confidence
      signals).

Every number is computed on IS data only (close_time < 2025-03-24). No OOS row
is ever read. Output: T1..T8 CSVs in analysis/iteration_v3-113/.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import (  # noqa: E402
    DAILY_FEATURES,
    SYMBOLS,
    V3_FEATURE_COLUMNS,
    load_labeled_is,
)

try:
    import lightgbm as lgb
except ImportError:
    print("ERROR: lightgbm not installed; run `uv sync` first.")
    sys.exit(1)

from sklearn.metrics import roc_auc_score  # noqa: E402

OUT = Path(__file__).resolve().parent
SEED = 42
RNG = np.random.default_rng(SEED)
N_PERM = 100

# Walk-forward fold geometry: expanding window inside the IS span. 5 folds — the
# first fold trains on the earliest ~40% of the IS rows and tests on the next
# chunk; each subsequent fold expands the train window. An embargo of 22 candles
# (the /059 walk-forward embargo) is purged between train and test.
N_FOLDS = 5
EMBARGO = 22

# A deliberately shallow LightGBM matching the v3 depth-3-5 production regime —
# the EDA must not use a deeper model than the runner or the AUC is not a
# faithful fidelity target.
LGB_PARAMS = dict(
    objective="binary",
    n_estimators=120,
    num_leaves=15,
    max_depth=4,
    learning_rate=0.05,
    min_child_samples=30,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    random_state=SEED,
    n_jobs=2,
    verbosity=-1,
)


def _walk_forward_folds(n: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Expanding-window folds with a 22-candle embargo purged before each test.

    Returns a list of (train_idx, test_idx). The earliest 40% of rows seeds the
    first train window; the remaining 60% is split into N_FOLDS test chunks.
    """
    start = int(n * 0.40)
    test_span = n - start
    chunk = test_span // N_FOLDS
    folds = []
    for k in range(N_FOLDS):
        test_lo = start + k * chunk
        test_hi = start + (k + 1) * chunk if k < N_FOLDS - 1 else n
        train_hi = max(0, test_lo - EMBARGO)
        train_idx = np.arange(0, train_hi)
        test_idx = np.arange(test_lo, test_hi)
        if len(train_idx) >= 200 and len(test_idx) >= 50:
            folds.append((train_idx, test_idx))
    return folds


def _wf_auc(
    X: pd.DataFrame, y: np.ndarray, folds: list[tuple[np.ndarray, np.ndarray]]
) -> tuple[float, list[float]]:
    """Pooled walk-forward held-out AUC over the folds (+ per-fold list)."""
    oof_pred, oof_true = [], []
    per_fold = []
    for tr, te in folds:
        ytr = y[tr]
        if len(np.unique(ytr)) < 2:
            continue
        model = lgb.LGBMClassifier(**LGB_PARAMS)
        model.fit(X.iloc[tr], ytr)
        p = model.predict_proba(X.iloc[te])[:, 1]
        yte = y[te]
        oof_pred.append(p)
        oof_true.append(yte)
        if len(np.unique(yte)) >= 2:
            per_fold.append(float(roc_auc_score(yte, p)))
    if not oof_pred:
        return float("nan"), []
    allp = np.concatenate(oof_pred)
    allt = np.concatenate(oof_true)
    pooled = float(roc_auc_score(allt, allp)) if len(np.unique(allt)) >= 2 else float("nan")
    return pooled, per_fold


def _gated_hit_rate(
    X: pd.DataFrame, y: np.ndarray, folds: list[tuple[np.ndarray, np.ndarray]], decile: float
) -> float:
    """Directional hit rate in the top/bottom-confidence tail of OOF predictions.

    The production 7-gate stack only trades high-confidence signals. This proxy
    keeps the OOF predictions whose proba is in the top `decile` (long-confident)
    or bottom `decile` (short-confident) and measures the directional hit rate.
    """
    oof_pred, oof_true = [], []
    for tr, te in folds:
        ytr = y[tr]
        if len(np.unique(ytr)) < 2:
            continue
        model = lgb.LGBMClassifier(**LGB_PARAMS)
        model.fit(X.iloc[tr], ytr)
        oof_pred.append(model.predict_proba(X.iloc[te])[:, 1])
        oof_true.append(y[te])
    if not oof_pred:
        return float("nan")
    p = np.concatenate(oof_pred)
    t = np.concatenate(oof_true)
    hi = np.quantile(p, 1.0 - decile)
    lo = np.quantile(p, decile)
    long_mask = p >= hi
    short_mask = p <= lo
    # long-confident correct = label 1; short-confident correct = label 0
    correct = np.concatenate([t[long_mask] == 1, t[short_mask] == 0])
    return float(correct.mean()) if len(correct) else float("nan")


def main() -> None:
    print("=" * 72)
    print("iter-v3/113 — multi-frequency (1d coarser) feature gating EDA")
    print("=" * 72)

    # ------------------------------------------------------------------
    # Load + label all three symbols (strictly IS-only).
    # ------------------------------------------------------------------
    data: dict[str, pd.DataFrame] = {}
    for s in SYMBOLS:
        df = load_labeled_is(s)
        df = df[df["label_valid"]].copy()
        # require both feature sets fully present
        need = V3_FEATURE_COLUMNS + DAILY_FEATURES
        df = df.dropna(subset=need).reset_index(drop=True)
        data[s] = df
        print(
            f"  {s}: {len(df)} labeled IS rows after NaN-drop "
            f"(label mean {df['label'].mean():.3f})"
        )

    # ==================================================================
    # T1 / T3 — walk-forward held-out AUC: 8h-only vs 8h+daily
    # ==================================================================
    t1_rows, t3_rows = [], []
    pooled_frames = []
    for s in SYMBOLS:
        df = data[s]
        folds = _walk_forward_folds(len(df))
        y = df["label"].to_numpy()
        X8 = df[V3_FEATURE_COLUMNS]
        Xboth = df[V3_FEATURE_COLUMNS + DAILY_FEATURES]
        auc8, pf8 = _wf_auc(X8, y, folds)
        aucb, pfb = _wf_auc(Xboth, y, folds)
        t1_rows.append(
            dict(
                symbol=s,
                n_rows=len(df),
                n_folds=len(folds),
                auc_8h_only=round(auc8, 4),
                auc_8h_plus_daily=round(aucb, 4),
                auc_lift=round(aucb - auc8, 4),
                per_fold_lift=";".join(
                    f"{b - a:+.3f}" for a, b in zip(pf8, pfb, strict=False)
                ),
            )
        )
        t3_rows.append(
            dict(
                symbol=s,
                auc_8h_only=round(auc8, 4),
                auc_8h_plus_daily=round(aucb, 4),
                auc_lift=round(aucb - auc8, 4),
                lift_positive=bool(aucb - auc8 > 0),
            )
        )
        pooled_frames.append(df)

    # pooled across the 3 symbols (one combined walk-forward)
    pooled = pd.concat(pooled_frames, ignore_index=True).sort_values("open_time")
    pooled = pooled.reset_index(drop=True)
    pfolds = _walk_forward_folds(len(pooled))
    yp = pooled["label"].to_numpy()
    auc8_p, _ = _wf_auc(pooled[V3_FEATURE_COLUMNS], yp, pfolds)
    aucb_p, _ = _wf_auc(pooled[V3_FEATURE_COLUMNS + DAILY_FEATURES], yp, pfolds)
    t1_rows.append(
        dict(
            symbol="POOLED",
            n_rows=len(pooled),
            n_folds=len(pfolds),
            auc_8h_only=round(auc8_p, 4),
            auc_8h_plus_daily=round(aucb_p, 4),
            auc_lift=round(aucb_p - auc8_p, 4),
            per_fold_lift="",
        )
    )
    t3_rows.append(
        dict(
            symbol="POOLED",
            auc_8h_only=round(auc8_p, 4),
            auc_8h_plus_daily=round(aucb_p, 4),
            auc_lift=round(aucb_p - auc8_p, 4),
            lift_positive=bool(aucb_p - auc8_p > 0),
        )
    )
    pd.DataFrame(t1_rows).to_csv(OUT / "T1_walkforward_auc.csv", index=False)
    pd.DataFrame(t3_rows).to_csv(OUT / "T3_per_symbol_auc_lift.csv", index=False)
    print("\n[T1] walk-forward held-out AUC (8h-only vs 8h+daily):")
    print(pd.DataFrame(t1_rows).to_string(index=False))

    # ==================================================================
    # T4 — permutation null on the POOLED 8h+daily stack
    #   Shuffle the label N_PERM times; re-fit; the observed AUC must clear q95.
    # ==================================================================
    perm_aucs = []
    Xboth_p = pooled[V3_FEATURE_COLUMNS + DAILY_FEATURES]
    for i in range(N_PERM):
        y_shuf = RNG.permutation(yp)
        a, _ = _wf_auc(Xboth_p, y_shuf, pfolds)
        if not np.isnan(a):
            perm_aucs.append(a)
    perm_aucs = np.array(perm_aucs)
    q50 = float(np.quantile(perm_aucs, 0.50))
    q95 = float(np.quantile(perm_aucs, 0.95))
    p_value = float((perm_aucs >= aucb_p).mean())
    t4 = pd.DataFrame(
        [
            dict(
                model="8h+daily POOLED",
                observed_auc=round(aucb_p, 4),
                null_q50=round(q50, 4),
                null_q95=round(q95, 4),
                p_value=round(p_value, 4),
                clears_q95=bool(aucb_p > q95),
                n_perm=len(perm_aucs),
            )
        ]
    )
    t4.to_csv(OUT / "T4_permutation_null.csv", index=False)
    print("\n[T4] permutation null (pooled 8h+daily):")
    print(t4.to_string(index=False))

    # ==================================================================
    # T5 — daily-ONLY model: do the 8 daily features carry standalone signal?
    #   Held-out AUC of the daily-only stack vs its own permutation null.
    # ==================================================================
    Xd_p = pooled[DAILY_FEATURES]
    aucd_p, _ = _wf_auc(Xd_p, yp, pfolds)
    perm_d = []
    for i in range(N_PERM):
        a, _ = _wf_auc(Xd_p, RNG.permutation(yp), pfolds)
        if not np.isnan(a):
            perm_d.append(a)
    perm_d = np.array(perm_d)
    qd95 = float(np.quantile(perm_d, 0.95))
    pd_value = float((perm_d >= aucd_p).mean())
    t5 = pd.DataFrame(
        [
            dict(
                model="daily-ONLY POOLED",
                observed_auc=round(aucd_p, 4),
                null_q50=round(float(np.quantile(perm_d, 0.50)), 4),
                null_q95=round(qd95, 4),
                p_value=round(pd_value, 4),
                clears_q95=bool(aucd_p > qd95),
                n_perm=len(perm_d),
            )
        ]
    )
    t5.to_csv(OUT / "T5_daily_only_signal.csv", index=False)
    print("\n[T5] daily-ONLY standalone signal (pooled):")
    print(t5.to_string(index=False))

    # ==================================================================
    # T6 — per-daily-feature univariate held-out AUC + stacked gain rank
    # ==================================================================
    t6_rows = []
    # stacked gain ranks: fit one LightGBM on the full 8h+daily stack per symbol,
    # average the daily features' gain rank across symbols
    rank_accum = {f: [] for f in DAILY_FEATURES}
    for s in SYMBOLS:
        df = data[s]
        folds = _walk_forward_folds(len(df))
        y = df["label"].to_numpy()
        model = lgb.LGBMClassifier(**LGB_PARAMS)
        # train on all-but-last fold's train, importance is a stable IS quantity
        tr = folds[-1][0]
        model.fit(df[V3_FEATURE_COLUMNS + DAILY_FEATURES].iloc[tr], y[tr])
        gains = pd.Series(
            model.booster_.feature_importance(importance_type="gain"),
            index=V3_FEATURE_COLUMNS + DAILY_FEATURES,
        )
        ranks = gains.rank(ascending=False)
        for f in DAILY_FEATURES:
            rank_accum[f].append(float(ranks[f]))
    for f in DAILY_FEATURES:
        # univariate AUC on the pooled walk-forward
        auc_uni, _ = _wf_auc(pooled[[f]], yp, pfolds)
        t6_rows.append(
            dict(
                daily_feature=f,
                univariate_pooled_auc=round(auc_uni, 4),
                mean_stacked_gain_rank=round(float(np.mean(rank_accum[f])), 2),
                rank_of_total=len(V3_FEATURE_COLUMNS) + len(DAILY_FEATURES),
            )
        )
    t6 = pd.DataFrame(t6_rows).sort_values("mean_stacked_gain_rank")
    t6.to_csv(OUT / "T6_per_daily_feature.csv", index=False)
    print("\n[T6] per-daily-feature univariate AUC + stacked gain rank:")
    print(t6.to_string(index=False))

    # ==================================================================
    # T7 — IC redundancy screen: each daily feature vs closest-mechanism 8h feat
    # ==================================================================
    # mechanism map: each daily feature paired with the nearest 8h-stack analogue
    mech_map = {
        "d_ret_5d": "regime_momentum_signed_5d",
        "d_ret_10d": "regime_momentum_signed_5d",
        "d_trend_slope_10": "ema_spread_atr_20",
        "d_realvol_10": "range_realized_vol_50",
        "d_realvol_ratio": "range_realized_vol_50",
        "d_atr_pctrank_60": "range_realized_vol_50",
        "d_efficiency_10": "hurst_100",
        "d_close_pos_20": "vwap_dev_20",
    }
    t7_rows = []
    for f, base in mech_map.items():
        ic = float(pooled[f].corr(pooled[base]))
        # also the max |IC| against the entire 8h stack
        ics = pooled[V3_FEATURE_COLUMNS].corrwith(pooled[f]).abs()
        t7_rows.append(
            dict(
                daily_feature=f,
                nearest_8h_feature=base,
                ic_vs_nearest=round(ic, 4),
                max_abs_ic_vs_8h_stack=round(float(ics.max()), 4),
                max_ic_partner=str(ics.idxmax()),
                redundant_ic_gt_070=bool(ics.max() > 0.70),
            )
        )
    t7 = pd.DataFrame(t7_rows)
    t7.to_csv(OUT / "T7_ic_redundancy.csv", index=False)
    print("\n[T7] IC redundancy screen (daily feature vs 8h stack):")
    print(t7.to_string(index=False))

    # ==================================================================
    # T8 — gated-tail hit rate: 8h+daily vs 8h-only in the confident tail
    # ==================================================================
    t8_rows = []
    for s in SYMBOLS:
        df = data[s]
        folds = _walk_forward_folds(len(df))
        y = df["label"].to_numpy()
        hr8 = _gated_hit_rate(df[V3_FEATURE_COLUMNS], y, folds, 0.10)
        hrb = _gated_hit_rate(df[V3_FEATURE_COLUMNS + DAILY_FEATURES], y, folds, 0.10)
        t8_rows.append(
            dict(
                symbol=s,
                gated_hit_8h_only=round(hr8, 4),
                gated_hit_8h_plus_daily=round(hrb, 4),
                gated_hit_lift=round(hrb - hr8, 4),
            )
        )
    hr8_p = _gated_hit_rate(pooled[V3_FEATURE_COLUMNS], yp, pfolds, 0.10)
    hrb_p = _gated_hit_rate(pooled[V3_FEATURE_COLUMNS + DAILY_FEATURES], yp, pfolds, 0.10)
    t8_rows.append(
        dict(
            symbol="POOLED",
            gated_hit_8h_only=round(hr8_p, 4),
            gated_hit_8h_plus_daily=round(hrb_p, 4),
            gated_hit_lift=round(hrb_p - hr8_p, 4),
        )
    )
    t8 = pd.DataFrame(t8_rows)
    t8.to_csv(OUT / "T8_gated_tail_hit_rate.csv", index=False)
    print("\n[T8] gated-tail (top-decile-confidence) hit rate:")
    print(t8.to_string(index=False))

    # ==================================================================
    # T2 — aggregate GO / NO-GO verdict
    # ==================================================================
    # GO criteria (a "sharpened-GO" still proceeds to a brief per THE PRIME
    # DIRECTIVE; the verdict only shapes the brief's expected-impact interval):
    #   C1  pooled 8h+daily AUC lift vs 8h-only > 0
    #   C2  pooled 8h+daily clears its permutation q95 (a real-signal stack)
    #   C3  >= 2 of 3 symbols show a positive AUC lift
    #   C4  pooled gated-tail hit-rate lift > 0
    c1 = bool(aucb_p - auc8_p > 0)
    c2 = bool(aucb_p > q95)
    n_pos = sum(1 for r in t3_rows if r["symbol"] != "POOLED" and r["lift_positive"])
    c3 = bool(n_pos >= 2)
    c4 = bool(hrb_p - hr8_p > 0)
    n_clear = sum([c1, c2, c3, c4])
    if n_clear >= 3:
        verdict = "GO"
    elif n_clear == 2:
        verdict = "SHARPENED-GO"
    else:
        verdict = "NO-GO"
    t2 = pd.DataFrame(
        [
            dict(
                C1_pooled_auc_lift_positive=c1,
                C2_pooled_clears_perm_q95=c2,
                C3_majority_symbols_positive=c3,
                C4_pooled_gated_hit_lift_positive=c4,
                n_criteria_cleared=n_clear,
                pooled_auc_8h_only=round(auc8_p, 4),
                pooled_auc_8h_plus_daily=round(aucb_p, 4),
                pooled_perm_q95=round(q95, 4),
                verdict=verdict,
            )
        ]
    )
    t2.to_csv(OUT / "T2_go_nogo_verdict.csv", index=False)
    print("\n[T2] AGGREGATE GO/NO-GO VERDICT:")
    print(t2.to_string(index=False))
    print("\n" + "=" * 72)
    print(f"EDA COMPLETE — verdict: {verdict} ({n_clear}/4 criteria cleared)")
    print("=" * 72)


if __name__ == "__main__":
    main()
