"""Supplementary V2 — per-hyperparam coefficient of variation across seeds.

Critic spec asks for per-cell median Spearman on the 3-element vector
[num_leaves, learning_rate, min_child_samples]. With only 3 elements, the
Spearman statistic can only take values in {-1.0, -0.5, 0, +0.5, +0.866, +1.0}.
This is statistically WEAK and may not discriminate cells where the 3 hyperparams
happen to be ordered consistently but at WILDLY different absolute values.

Supplementary check: compute coefficient of variation (CV = std/|mean|) of each
hyperparam ACROSS the 5 best-seed values per cell. High CV ⇒ seeds disagree on
absolute hyperparam values; low CV ⇒ true agreement.

A robust V2 PASS requires BOTH (a) per-cell median Spearman ≥ 0.50 (Critic spec)
AND (b) per-hyperparam median CV ≤ 0.50 (supplementary).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PARQUET = REPO_ROOT / "data" / "v1_iter_v1-031_optuna_trials.parquet"
OUT_CSV = REPO_ROOT / "analysis" / "iteration_v1-031" / "v2_supplementary_hp_cv.csv"

HP_KEYS = ["num_leaves", "learning_rate", "min_child_samples"]


def main() -> None:
    df = pd.read_parquet(PARQUET)
    idx = df.groupby(["model", "month", "inner_seed"])["sharpe"].idxmax()
    best = df.loc[idx, ["model", "month", "inner_seed"] + HP_KEYS].reset_index(drop=True)

    rows = []
    for (model, month), grp in best.groupby(["model", "month"]):
        if grp["inner_seed"].nunique() < 5:
            continue
        row = {"model": model, "month": month}
        for hp in HP_KEYS:
            vals = grp[hp].astype(float).values
            m = vals.mean()
            s = vals.std(ddof=1)
            denom = abs(m) if abs(m) > 1e-9 else np.nan
            row[f"{hp}_mean"] = m
            row[f"{hp}_std"] = s
            row[f"{hp}_cv"] = s / denom if denom == denom else np.nan
        rows.append(row)

    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT_CSV, index=False)

    print(f"[v2_supp] Cells: {len(df_out)}")
    for hp in HP_KEYS:
        cv = df_out[f"{hp}_cv"].dropna()
        print(f"\n[v2_supp] {hp} CV across seeds:")
        print(f"  median={cv.median():.4f} p25={cv.quantile(0.25):.4f} p75={cv.quantile(0.75):.4f} max={cv.max():.4f}")

    # Overall: max CV per cell across the 3 hyperparams
    max_cv = df_out[[f"{hp}_cv" for hp in HP_KEYS]].max(axis=1)
    print("\n[v2_supp] max CV per cell across 3 hyperparams:")
    print(f"  median={max_cv.median():.4f} p25={max_cv.quantile(0.25):.4f} p75={max_cv.quantile(0.75):.4f}")
    if max_cv.median() > 0.50:
        print("  → SEEDS DISAGREE ON ABSOLUTE HYPERPARAM VALUES (supplementary V2 FAIL)")
    else:
        print("  → seeds agree on absolute hyperparam values (supplementary V2 PASS)")

    print(f"\n[v2_supp] Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
