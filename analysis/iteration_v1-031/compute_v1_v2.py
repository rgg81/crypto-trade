"""Validation 1 (cross-seed Sharpe std/mean) + Validation 2 (per-cell best-param Spearman).

V1 PASS: median std/mean across cells ≤ 0.25
V1 FAIL: median > 0.40 (NEG-BASIN-RELOCATION reclassification)

V2 PASS: median Spearman ≥ 0.50
V2 FAIL: median < 0.30
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

REPO_ROOT = Path(__file__).resolve().parents[2]
PARQUET = REPO_ROOT / "data" / "v1_iter_v1-031_optuna_trials.parquet"
OUT_V1_CSV = REPO_ROOT / "analysis" / "iteration_v1-031" / "v1_cross_seed_dispersion.csv"
OUT_V2_CSV = REPO_ROOT / "analysis" / "iteration_v1-031" / "v2_best_param_spearman.csv"

HP_KEYS = ["num_leaves", "learning_rate", "min_child_samples"]


def validation_1(df: pd.DataFrame) -> pd.DataFrame:
    """For each (model, month) cell, compute std/mean of best-seed Sharpes.

    Best Sharpe per (model, month, seed) → 5 values per cell → std/mean.
    Use ABSOLUTE mean (negative Sharpes flip sign meaning); per Critic spec.
    """
    best_per_seed = (
        df.groupby(["model", "month", "inner_seed"])["sharpe"].max().reset_index()
    )
    rows = []
    for (model, month), grp in best_per_seed.groupby(["model", "month"]):
        seeds_count = grp["inner_seed"].nunique()
        if seeds_count < 5:
            continue
        sharpes = grp["sharpe"].values
        mean_sr = sharpes.mean()
        std_sr = sharpes.std(ddof=1)
        # Use abs(mean) to avoid divide-by-near-zero artifacts when seeds straddle 0.
        # Critic spec asks for std/mean across cells; when mean is near 0 (axis-edge
        # plausibly small at single-cell level), ratio explodes. Standard practice:
        # report std/|mean|, also keep raw std and raw mean for inspection.
        denom = abs(mean_sr) if abs(mean_sr) > 1e-9 else np.nan
        cv = std_sr / denom if denom == denom else np.nan
        rows.append(
            {
                "model": model,
                "month": month,
                "seeds_present": seeds_count,
                "mean_sharpe": mean_sr,
                "std_sharpe": std_sr,
                "std_over_abs_mean": cv,
            }
        )
    return pd.DataFrame(rows)


def validation_2(df: pd.DataFrame) -> pd.DataFrame:
    """For each cell, compute per-seed best-trial hyperparam vector → pairwise Spearman.

    For each pair of seeds (10 pairs from 5 seeds), Spearman rank-correlation across
    the 3-element vector [num_leaves, learning_rate, min_child_samples] of best-trial
    hyperparams. Median across pairs reported per cell.

    NOTE: With a 3-element vector, Spearman can take only a small set of values:
    {-1.0, -0.5, 0.5, 1.0} (and NaN when there's a tie). This is intentional per
    Critic spec — purpose is to detect whether best-trial hyperparams agree across
    seeds at the BEST-PARAM level.
    """
    # Best trial per (model, month, seed)
    idx = df.groupby(["model", "month", "inner_seed"])["sharpe"].idxmax()
    best = df.loc[idx, ["model", "month", "inner_seed"] + HP_KEYS].reset_index(drop=True)

    rows = []
    for (model, month), grp in best.groupby(["model", "month"]):
        if grp["inner_seed"].nunique() < 5:
            continue
        # 5-seed hyperparam matrix
        grp_sorted = grp.sort_values("inner_seed").reset_index(drop=True)
        # Pairwise Spearman across the 3-element vectors
        pair_rhos = []
        for (i, j) in combinations(range(len(grp_sorted)), 2):
            vi = grp_sorted.loc[i, HP_KEYS].astype(float).values
            vj = grp_sorted.loc[j, HP_KEYS].astype(float).values
            with np.errstate(invalid="ignore"):
                rho, _ = spearmanr(vi, vj)
            # spearmanr returns NaN if a series is constant; treat as 0 (no rank info)
            if np.isnan(rho):
                rho = 0.0
            pair_rhos.append(rho)
        med = float(np.median(pair_rhos))
        rows.append(
            {
                "model": model,
                "month": month,
                "median_pair_spearman": med,
                "n_pairs": len(pair_rhos),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    print(f"[v1_v2] Reading {PARQUET}")
    df = pd.read_parquet(PARQUET)
    print(f"[v1_v2] {len(df):,} trial rows")

    # V1
    print("\n[V1] Cross-seed Sharpe std/mean dispersion")
    v1 = validation_1(df)
    v1.to_csv(OUT_V1_CSV, index=False)
    print(f"  Cells with 5 seeds: {len(v1)}")

    abs_cv = v1["std_over_abs_mean"].dropna()
    print(f"  std/|mean| distribution across cells:")
    print(f"    n={len(abs_cv)}")
    print(f"    median={abs_cv.median():.4f}")
    print(f"    p25={abs_cv.quantile(0.25):.4f}")
    print(f"    p75={abs_cv.quantile(0.75):.4f}")
    print(f"    max={abs_cv.max():.4f}")
    print(f"    mean={abs_cv.mean():.4f}")

    v1_median = abs_cv.median()
    if v1_median <= 0.25:
        v1_verdict = "PASS"
    elif v1_median > 0.40:
        v1_verdict = "FAIL (NEG-BASIN-RELOCATION reclassification)"
    else:
        v1_verdict = "BORDERLINE (between 0.25 and 0.40)"
    print(f"  V1 VERDICT: median std/|mean| = {v1_median:.4f} → {v1_verdict}")

    # Per-model breakdown
    print("\n  V1 per-model median:")
    print(v1.groupby("model")["std_over_abs_mean"].median().to_string())

    # V2
    print("\n[V2] Per-cell best-param Spearman across 5 seeds")
    v2 = validation_2(df)
    v2.to_csv(OUT_V2_CSV, index=False)
    print(f"  Cells with 5 seeds: {len(v2)}")
    rhos = v2["median_pair_spearman"]
    print(f"  median_pair_spearman across cells:")
    print(f"    n={len(rhos)}")
    print(f"    median={rhos.median():.4f}")
    print(f"    p25={rhos.quantile(0.25):.4f}")
    print(f"    p75={rhos.quantile(0.75):.4f}")
    print(f"    min={rhos.min():.4f}")
    print(f"    mean={rhos.mean():.4f}")

    v2_median = rhos.median()
    if v2_median >= 0.50:
        v2_verdict = "PASS"
    elif v2_median < 0.30:
        v2_verdict = "FAIL (NEG-BASIN-RELOCATION reclassification)"
    else:
        v2_verdict = "BORDERLINE (between 0.30 and 0.50)"
    print(f"  V2 VERDICT: median = {v2_median:.4f} → {v2_verdict}")

    print("\n  V2 per-model median:")
    print(v2.groupby("model")["median_pair_spearman"].median().to_string())

    print(f"\n[v1_v2] Wrote {OUT_V1_CSV}")
    print(f"[v1_v2] Wrote {OUT_V2_CSV}")


if __name__ == "__main__":
    main()
