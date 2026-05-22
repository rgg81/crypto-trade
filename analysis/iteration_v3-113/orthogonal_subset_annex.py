"""iter-v3/113 — orthogonal-subset annex to the multi-frequency gating EDA.

The main EDA (multifreq_gating_eda.py) found:
  - T5: the daily-ONLY 8-feature stack carries permutation-validated standalone
    signal (pooled AUC 0.5275, clears q95 0.5093, p=0.0) — a genuine coarser
    representation the saturated 8h stack cannot supply.
  - T4: the FULL 8h+daily-8 stack does NOT clear its permutation q95 (p=0.39).
  - T7: 4 of the 8 daily features are redundant with the 8h stack (|IC|>0.70):
      d_ret_5d (0.85), d_ret_10d (0.77), d_realvol_10 (0.81), d_close_pos_20
      (0.85). The redundant features steal LightGBM colsample picks; they add
      no information the 8h stack lacks but dilute the search.

This annex tests the EDA-prescribed refinement: stack ONLY the 4 ORTHOGONAL
daily features (max |IC| vs the 8h stack < 0.30) on top of the 14-feature 8h
anchor. Question: does the orthogonal-only subset clear the permutation q95
that the full daily-8 stack failed — i.e. is the redundancy dilution the
mechanism, and does pruning it recover the daily signal inside the combined
stack?

T9   walk-forward held-out AUC: 8h-only vs 8h + orthogonal-4-daily (per symbol
     + pooled).
T10  permutation null on the pooled 8h + orthogonal-4 stack.
T11  gated-tail hit-rate: 8h + orthogonal-4 vs 8h-only.
T12  the refined GO/NO-GO + the precise feature recommendation for the brief.

Strictly IS-only — every row has close_time < 2025-03-24.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import SYMBOLS, V3_FEATURE_COLUMNS, load_labeled_is  # noqa: E402

import lightgbm as lgb  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

# Mirror the main-EDA imports for fold geometry + model params + helpers.
from multifreq_gating_eda import (  # noqa: E402
    LGB_PARAMS,
    N_PERM,
    _gated_hit_rate,
    _walk_forward_folds,
    _wf_auc,
)

OUT = Path(__file__).resolve().parent
RNG = np.random.default_rng(42)

# The 4 orthogonal daily features (T7: max |IC| vs the 8h stack < 0.30).
# d_trend_slope_10 (0.05), d_realvol_ratio (0.18), d_atr_pctrank_60 (0.21),
# d_efficiency_10 (0.11). The redundant 4 (d_ret_5d/10d, d_realvol_10,
# d_close_pos_20) are dropped — they carry no signal the 8h stack lacks.
ORTHO_DAILY = ["d_trend_slope_10", "d_realvol_ratio", "d_atr_pctrank_60", "d_efficiency_10"]


def main() -> None:
    print("=" * 72)
    print("iter-v3/113 — orthogonal-subset annex (4 non-redundant daily features)")
    print("=" * 72)
    print(f"  orthogonal daily subset: {ORTHO_DAILY}")

    data: dict[str, pd.DataFrame] = {}
    for s in SYMBOLS:
        df = load_labeled_is(s)
        df = df[df["label_valid"]].copy()
        df = df.dropna(subset=V3_FEATURE_COLUMNS + ORTHO_DAILY).reset_index(drop=True)
        data[s] = df
        print(f"  {s}: {len(df)} labeled IS rows after NaN-drop")

    # ------------------------------------------------------------------
    # T9 — walk-forward AUC: 8h-only vs 8h + orthogonal-4
    # ------------------------------------------------------------------
    t9_rows, pooled_frames = [], []
    for s in SYMBOLS:
        df = data[s]
        folds = _walk_forward_folds(len(df))
        y = df["label"].to_numpy()
        auc8, pf8 = _wf_auc(df[V3_FEATURE_COLUMNS], y, folds)
        auco, pfo = _wf_auc(df[V3_FEATURE_COLUMNS + ORTHO_DAILY], y, folds)
        t9_rows.append(
            dict(
                symbol=s,
                n_rows=len(df),
                auc_8h_only=round(auc8, 4),
                auc_8h_plus_ortho4=round(auco, 4),
                auc_lift=round(auco - auc8, 4),
                lift_positive=bool(auco - auc8 > 0),
                per_fold_lift=";".join(
                    f"{b - a:+.3f}" for a, b in zip(pf8, pfo, strict=False)
                ),
            )
        )
        pooled_frames.append(df)

    pooled = pd.concat(pooled_frames, ignore_index=True).sort_values("open_time")
    pooled = pooled.reset_index(drop=True)
    pfolds = _walk_forward_folds(len(pooled))
    yp = pooled["label"].to_numpy()
    auc8_p, _ = _wf_auc(pooled[V3_FEATURE_COLUMNS], yp, pfolds)
    auco_p, _ = _wf_auc(pooled[V3_FEATURE_COLUMNS + ORTHO_DAILY], yp, pfolds)
    t9_rows.append(
        dict(
            symbol="POOLED",
            n_rows=len(pooled),
            auc_8h_only=round(auc8_p, 4),
            auc_8h_plus_ortho4=round(auco_p, 4),
            auc_lift=round(auco_p - auc8_p, 4),
            lift_positive=bool(auco_p - auc8_p > 0),
            per_fold_lift="",
        )
    )
    pd.DataFrame(t9_rows).to_csv(OUT / "T9_ortho_subset_auc.csv", index=False)
    print("\n[T9] walk-forward AUC (8h-only vs 8h + orthogonal-4-daily):")
    print(pd.DataFrame(t9_rows).to_string(index=False))

    # ------------------------------------------------------------------
    # T10 — permutation null on the pooled 8h + orthogonal-4 stack
    # ------------------------------------------------------------------
    Xo_p = pooled[V3_FEATURE_COLUMNS + ORTHO_DAILY]
    perm = []
    for _ in range(N_PERM):
        a, _ = _wf_auc(Xo_p, RNG.permutation(yp), pfolds)
        if not np.isnan(a):
            perm.append(a)
    perm = np.array(perm)
    q95 = float(np.quantile(perm, 0.95))
    p_value = float((perm >= auco_p).mean())
    t10 = pd.DataFrame(
        [
            dict(
                model="8h+ortho4 POOLED",
                observed_auc=round(auco_p, 4),
                null_q50=round(float(np.quantile(perm, 0.50)), 4),
                null_q95=round(q95, 4),
                p_value=round(p_value, 4),
                clears_q95=bool(auco_p > q95),
                n_perm=len(perm),
            )
        ]
    )
    t10.to_csv(OUT / "T10_ortho_permutation_null.csv", index=False)
    print("\n[T10] permutation null (pooled 8h + orthogonal-4):")
    print(t10.to_string(index=False))

    # ------------------------------------------------------------------
    # T11 — gated-tail hit-rate: 8h + orthogonal-4 vs 8h-only
    # ------------------------------------------------------------------
    t11_rows = []
    for s in SYMBOLS:
        df = data[s]
        folds = _walk_forward_folds(len(df))
        y = df["label"].to_numpy()
        hr8 = _gated_hit_rate(df[V3_FEATURE_COLUMNS], y, folds, 0.10)
        hro = _gated_hit_rate(df[V3_FEATURE_COLUMNS + ORTHO_DAILY], y, folds, 0.10)
        t11_rows.append(
            dict(
                symbol=s,
                gated_hit_8h_only=round(hr8, 4),
                gated_hit_8h_plus_ortho4=round(hro, 4),
                gated_hit_lift=round(hro - hr8, 4),
            )
        )
    hr8_p = _gated_hit_rate(pooled[V3_FEATURE_COLUMNS], yp, pfolds, 0.10)
    hro_p = _gated_hit_rate(pooled[V3_FEATURE_COLUMNS + ORTHO_DAILY], yp, pfolds, 0.10)
    t11_rows.append(
        dict(
            symbol="POOLED",
            gated_hit_8h_only=round(hr8_p, 4),
            gated_hit_8h_plus_ortho4=round(hro_p, 4),
            gated_hit_lift=round(hro_p - hr8_p, 4),
        )
    )
    t11 = pd.DataFrame(t11_rows)
    t11.to_csv(OUT / "T11_ortho_gated_tail.csv", index=False)
    print("\n[T11] gated-tail hit rate (8h + orthogonal-4 vs 8h-only):")
    print(t11.to_string(index=False))

    # ------------------------------------------------------------------
    # T12 — refined GO/NO-GO + the precise feature recommendation
    # ------------------------------------------------------------------
    c1 = bool(auco_p - auc8_p > 0)
    c2 = bool(auco_p > q95)
    n_pos = sum(1 for r in t9_rows if r["symbol"] != "POOLED" and r["lift_positive"])
    c3 = bool(n_pos >= 2)
    c4 = bool(hro_p - hr8_p > 0)
    n_clear = sum([c1, c2, c3, c4])
    verdict = "GO" if n_clear >= 3 else ("SHARPENED-GO" if n_clear == 2 else "NO-GO")
    t12 = pd.DataFrame(
        [
            dict(
                recommended_features=";".join(ORTHO_DAILY),
                C1_auc_lift_positive=c1,
                C2_clears_perm_q95=c2,
                C3_majority_symbols_positive=c3,
                C4_gated_hit_lift_positive=c4,
                n_criteria_cleared=n_clear,
                pooled_auc_8h_only=round(auc8_p, 4),
                pooled_auc_8h_plus_ortho4=round(auco_p, 4),
                pooled_perm_q95=round(q95, 4),
                verdict=verdict,
            )
        ]
    )
    t12.to_csv(OUT / "T12_refined_verdict.csv", index=False)
    print("\n[T12] REFINED GO/NO-GO + feature recommendation:")
    print(t12.to_string(index=False))
    print("\n" + "=" * 72)
    print(f"ANNEX COMPLETE — orthogonal-4 verdict: {verdict} ({n_clear}/4)")
    print("=" * 72)


if __name__ == "__main__":
    main()
