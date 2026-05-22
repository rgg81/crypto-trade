"""Bottom-3 feature identification for iter-v3/041 (universal feature pruning).

EXPLORATION axis: drop the 3 lowest-importance features from V3_FEATURE_COLUMNS_TOP_N
to reduce Optuna search noise. Hypothesis: pruning low-importance columns frees
colsample_bytree picks for high-signal features and lifts IS Sharpe toward +1.0
without sacrificing OOS edge.

This script ranks features by LightGBM split-importance from the canonical multi-seed
baseline (iter-v3/028) and identifies the bottom-3 for removal. iter-v3/040
(post-revert anchor) is also reported for cross-verification.

Methodology
-----------
- Source: reports-v3/iteration_v3-028/in_sample/model_importance_last_month_portfolio.csv
  (multi-seed mean across the 4 v3 symbols at the last training month of IS).
- Cross-check: reports-v3/iteration_v3-040/in_sample/model_importance_last_month_portfolio.csv
  (single-seed cycle 3 anchor; same 14 features after iter-v3/028 mini-validation revert).
- Rank ascending; report rank, importance, percentile.
- Print bottom-3 candidates and the dropped-feature manifest for the brief.

Constraints
-----------
- IS-only (per Phase 5.5 gate Section 2 mandate; no peeking at OOS in EDA).
- regime_momentum_signed_5d MAY be in bottom-3 — the user-task brief explicitly
  authorizes pruning ALL bottom-3 by importance, overriding any prior MUST-be-present
  carve-out from feedback_v3_engineered_features_proven.md (which was established
  pre-iter-v3/041 when the feature was the only engineered candidate; iter-v3/041
  is a separate axis testing whether universal pruning lifts IS Sharpe).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
ITER_028 = REPO_ROOT / "reports-v3" / "iteration_v3-028" / "in_sample" / (
    "model_importance_last_month_portfolio.csv"
)
ITER_040 = REPO_ROOT / "reports-v3" / "iteration_v3-040" / "in_sample" / (
    "model_importance_last_month_portfolio.csv"
)
OUTPUT_DIR = REPO_ROOT / "analysis" / "iteration_v3-041"
OUTPUT_DIR.mkdir(exist_ok=True)


def _load_and_rank(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing importance CSV for {label}: {path}")
    df = pd.read_csv(path)
    df = df.sort_values("importance", ascending=False).reset_index(drop=True)
    df["rank_desc"] = df.index + 1
    df["rank_asc"] = len(df) - df.index
    df["pct_of_top"] = (df["importance"] / df["importance"].iloc[0] * 100).round(2)
    df["source"] = label
    return df


def main() -> None:
    print("=" * 78)
    print("iter-v3/041 EDA — bottom-3 feature identification")
    print("=" * 78)

    # Canonical multi-seed baseline (per task spec).
    df_028 = _load_and_rank(ITER_028, "iter-v3/028 (multi-seed)")
    df_040 = _load_and_rank(ITER_040, "iter-v3/040 (single-seed cycle 3 anchor)")

    print("\n--- iter-v3/028 portfolio ranking (DESCENDING importance) ---")
    print(df_028[["rank_desc", "feature", "importance", "pct_of_top"]].to_string(index=False))

    print("\n--- iter-v3/040 portfolio ranking (DESCENDING importance) ---")
    print(df_040[["rank_desc", "feature", "importance", "pct_of_top"]].to_string(index=False))

    # Bottom-3 from canonical iter-v3/028 (ascending importance).
    bottom3_028 = df_028.tail(3).iloc[::-1].reset_index(drop=True)
    print("\n--- iter-v3/028 BOTTOM-3 (canonical; to drop at iter-v3/041) ---")
    print(bottom3_028[["rank_desc", "feature", "importance", "pct_of_top"]].to_string(index=False))

    bottom3_040 = df_040.tail(3).iloc[::-1].reset_index(drop=True)
    print("\n--- iter-v3/040 BOTTOM-3 (cross-check; single-seed) ---")
    print(bottom3_040[["rank_desc", "feature", "importance", "pct_of_top"]].to_string(index=False))

    # Concordance check: how many features overlap between the two bottom-3 lists?
    set_028 = set(bottom3_028["feature"])
    set_040 = set(bottom3_040["feature"])
    overlap = set_028 & set_040
    only_028 = set_028 - set_040
    only_040 = set_040 - set_028

    print("\n--- Concordance ---")
    print(f"Bottom-3 from iter-v3/028 (canonical, MULTI-seed): {sorted(set_028)}")
    print(f"Bottom-3 from iter-v3/040 (single-seed cross-ref): {sorted(set_040)}")
    print(f"Overlap (both lists agree): {sorted(overlap)} (n={len(overlap)})")
    print(f"Only in 028: {sorted(only_028)}")
    print(f"Only in 040: {sorted(only_040)}")

    # Dropped-feature manifest for the brief.
    print("\n" + "=" * 78)
    print("DROP MANIFEST FOR iter-v3/041 (per user task spec — drop iter-v3/028 bottom-3)")
    print("=" * 78)
    for _, row in bottom3_028.iterrows():
        print(
            f"  DROP: {row['feature']:30s}  "
            f"importance={row['importance']:.1f}  "
            f"rank={int(row['rank_desc']):2d}/14  "
            f"pct_of_top={row['pct_of_top']:.2f}%"
        )

    kept = sorted(set(df_028["feature"]) - set_028)
    print(f"\nKept (11 features): {len(kept)}")
    for feat in kept:
        print(f"  KEEP: {feat}")
    assert len(kept) == 11, f"Expected 11 kept features after drop, got {len(kept)}"

    # Save manifest CSV for the brief Section 2 numerical table.
    manifest = pd.concat(
        [
            df_028[["rank_desc", "feature", "importance", "pct_of_top"]].assign(
                action="DROP" if False else "KEEP"
            )
        ]
    )
    manifest["action"] = manifest["feature"].apply(
        lambda f: "DROP" if f in set_028 else "KEEP"
    )
    manifest.to_csv(OUTPUT_DIR / "iter028_importance_with_actions.csv", index=False)
    print(f"\nSaved manifest CSV: {OUTPUT_DIR / 'iter028_importance_with_actions.csv'}")

    # Behavioral predictor warning (per feedback_v3_axis_saturation_predictor.md).
    print("\n--- Behavioral-Effect Predictor (Section 2.3) ---")
    print(
        "Predicted IS trade count delta vs iter-v3/040 anchor: -3% to +5%. "
        "LightGBM split-count proportional to importance: dropping 3 features whose "
        "combined importance is "
        f"{bottom3_028['importance'].sum():.1f} / {df_028['importance'].sum():.1f} = "
        f"{bottom3_028['importance'].sum() / df_028['importance'].sum() * 100:.1f}% "
        "of total redirects ~the same fraction of decision splits to other features. "
        "If observed |IS trade delta| > 30 trades, escalate."
    )


if __name__ == "__main__":
    main()
