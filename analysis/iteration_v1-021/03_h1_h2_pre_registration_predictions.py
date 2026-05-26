"""iter-v1/021 EDA — H1/H2 pre-registration prediction table.

Computes expected magnitude of Optuna best-trial parameter delta + feature
importance signature divergence between pool and BTC-only, based on:
  - EDA script 02's Pearson=0.59/Spearman=0.26 best-trial-OOF correlation
  - LM Master Phase 7.4 §3 three-channel mechanism analysis
  - /020 Jaccard 0.084 trade-roster overlap evidence

Produces the falsifier table for brief Section 4 + the H1/H2 verdict-class
priors for brief Section 5.

OUTPUT: analysis/iteration_v1-021/h1_h2_pre_registration_predictions.csv

This is the QR's pre-registration of expected outcomes BEFORE the params-level
diagnostic runs. Brief Section 5 cites this table for the predicted verdict-class
priors.
"""

from __future__ import annotations

import csv
from pathlib import Path

OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    # Channel-by-channel prediction.  For each of LM Master Phase 7.4 §3's three
    # training-time pool-anchor channels, we predict (a) the expected magnitude of
    # impact on Optuna best_params and (b) the falsifier threshold for whether
    # H1 is confirmed.
    #
    # The three channels:
    #   C1 — Shared feature normalization at Optuna training time
    #   C2 — Label-timing co-location (joint IS loss surface integration)
    #   C3 — abs_pnl sample weighting integration
    #
    # Per-parameter expectation:
    #   confidence_threshold: most sensitive to label distribution
    #     (C2 + C3 expected to dominate); BTC-only narrower distribution may
    #     converge to LOWER threshold (less stringent — fewer high-quality
    #     signals when label volume is smaller).
    #   n_estimators, max_depth, num_leaves: capacity parameters; expected to
    #     SCALE DOWN with smaller training set (BTC-only ~113-130 IS labels
    #     vs pool 258 BTC+ETH joint labels).
    #   learning_rate: may go UP (smaller dataset → less risk of overfitting at
    #     higher lr) OR remain flat.
    #   subsample, colsample_bytree: less sensitive; C1 normalization-driven
    #     impact expected SMALL.
    #   min_child_samples: scales with training set size; expected to SCALE DOWN.
    #   reg_alpha, reg_lambda: regularization; expected to SCALE UP under
    #     smaller train set (more reg needed).

    rows = [
        {
            "parameter": "confidence_threshold",
            "expected_direction_btc_only_vs_pool": "lower (less stringent)",
            "expected_magnitude_pct_delta": "20-40%",
            "primary_channel": "C2+C3",
            "falsifier_threshold_pct": "|Δ| > 15%",
            "h1_supporting_evidence_if_breached": "yes — confidence basin reorganization at single-cohort label distribution",
        },
        {
            "parameter": "n_estimators",
            "expected_direction_btc_only_vs_pool": "lower (smaller capacity)",
            "expected_magnitude_pct_delta": "30-50%",
            "primary_channel": "C2",
            "falsifier_threshold_pct": "|Δ| > 25%",
            "h1_supporting_evidence_if_breached": "yes — capacity adapts to label volume",
        },
        {
            "parameter": "max_depth",
            "expected_direction_btc_only_vs_pool": "lower or flat",
            "expected_magnitude_pct_delta": "10-30%",
            "primary_channel": "C1+C2",
            "falsifier_threshold_pct": "|Δ| > 20%",
            "h1_supporting_evidence_if_breached": "yes — depth scales with feature joint distribution",
        },
        {
            "parameter": "num_leaves",
            "expected_direction_btc_only_vs_pool": "lower (smaller capacity)",
            "expected_magnitude_pct_delta": "20-40%",
            "primary_channel": "C1",
            "falsifier_threshold_pct": "|Δ| > 25%",
            "h1_supporting_evidence_if_breached": "yes — leaf count adapts to feature space volume",
        },
        {
            "parameter": "learning_rate",
            "expected_direction_btc_only_vs_pool": "higher (smaller set permits)",
            "expected_magnitude_pct_delta": "15-30%",
            "primary_channel": "C2",
            "falsifier_threshold_pct": "|Δ| > 20%",
            "h1_supporting_evidence_if_breached": "moderate — lr is multi-mechanism coupled",
        },
        {
            "parameter": "subsample",
            "expected_direction_btc_only_vs_pool": "indeterminate",
            "expected_magnitude_pct_delta": "5-15%",
            "primary_channel": "C1",
            "falsifier_threshold_pct": "|Δ| > 15%",
            "h1_supporting_evidence_if_breached": "weak — subsample is least channel-sensitive",
        },
        {
            "parameter": "colsample_bytree",
            "expected_direction_btc_only_vs_pool": "higher (fewer features needed for single cohort)",
            "expected_magnitude_pct_delta": "10-25%",
            "primary_channel": "C1",
            "falsifier_threshold_pct": "|Δ| > 15%",
            "h1_supporting_evidence_if_breached": "yes — feature selection adapts to single cohort label spectrum",
        },
        {
            "parameter": "min_child_samples",
            "expected_direction_btc_only_vs_pool": "lower (smaller set)",
            "expected_magnitude_pct_delta": "30-50%",
            "primary_channel": "C2+C3",
            "falsifier_threshold_pct": "|Δ| > 25%",
            "h1_supporting_evidence_if_breached": "yes — child-sample threshold scales with label volume",
        },
        {
            "parameter": "reg_alpha",
            "expected_direction_btc_only_vs_pool": "indeterminate (log-scale)",
            "expected_magnitude_pct_delta": "30-50%",
            "primary_channel": "C2",
            "falsifier_threshold_pct": "|log10(Δ)| > 0.5",
            "h1_supporting_evidence_if_breached": "moderate — log-scale param; high natural variance",
        },
        {
            "parameter": "reg_lambda",
            "expected_direction_btc_only_vs_pool": "indeterminate (log-scale)",
            "expected_magnitude_pct_delta": "30-50%",
            "primary_channel": "C2",
            "falsifier_threshold_pct": "|log10(Δ)| > 0.5",
            "h1_supporting_evidence_if_breached": "moderate — same as reg_alpha",
        },
    ]

    out_path = OUT / "h1_h2_pre_registration_predictions.csv"
    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {out_path}")

    # H1 + H2 verdict-class prior table
    h1_priors = [
        {
            "verdict_class": "DIAGNOSTIC-CONFIRMED",
            "definition": "≥50% of (sym, month) cells show |Δ|>threshold on ≥4 of 10 params AND ≥1 of {confidence_threshold, n_estimators, num_leaves, min_child_samples} param family shifted",
            "prior_pct": "55",
            "/022_routing": "/027 CONFIRMATION moved up with 2-specialist (LINK+ETH+gate) + BTC IN POOL bundle",
        },
        {
            "verdict_class": "DIAGNOSTIC-MIXED",
            "definition": "20-50% of (sym, month) cells show |Δ|>threshold OR shift confined to 1-2 param families",
            "prior_pct": "30",
            "/022_routing": "Selective cohort coverage; bundle ETH+gate +/- LINK only; LTC and DOT TBD per partial signature",
        },
        {
            "verdict_class": "DIAGNOSTIC-REFUTED",
            "definition": "<20% of (sym, month) cells show |Δ|>threshold OR LM Master §3 mechanism wrong",
            "prior_pct": "15",
            "/022_routing": "LTC-only specialization (LM Master Phase 4.5 §6 fallback); per-cohort axis viable for remaining cohorts under intrinsic-only mechanism",
        },
    ]

    out_path2 = OUT / "h1_verdict_class_priors.csv"
    fieldnames2 = list(h1_priors[0].keys())
    with open(out_path2, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames2)
        writer.writeheader()
        writer.writerows(h1_priors)
    print(f"Wrote {out_path2}")

    h2_priors = [
        {
            "verdict_class": "DIAGNOSTIC-CONFIRMED-H2",
            "definition": "≥3 features in top-10 importance differ between Model A pool (BTC slice) and Models C/G/H single-cohort",
            "prior_pct": "70",
        },
        {
            "verdict_class": "DIAGNOSTIC-MIXED-H2",
            "definition": "1-2 features in top-10 differ; or Spearman rank corr 0.5 ≤ ρ ≤ 0.8",
            "prior_pct": "20",
        },
        {
            "verdict_class": "DIAGNOSTIC-REFUTED-H2",
            "definition": "Spearman rank corr > 0.8 across model variants — same features used in similar order; per-cohort specialization is about different KNOBS not different features",
            "prior_pct": "10",
        },
    ]
    out_path3 = OUT / "h2_verdict_class_priors.csv"
    fieldnames3 = list(h2_priors[0].keys())
    with open(out_path3, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames3)
        writer.writeheader()
        writer.writerows(h2_priors)
    print(f"Wrote {out_path3}")

    print()
    print("H1 verdict-class priors:")
    for row in h1_priors:
        print(f"  {row['verdict_class']:24s} {row['prior_pct']:>3s}%  → /022 = {row['/022_routing']}")
    print()
    print("H2 verdict-class priors (independent of H1):")
    for row in h2_priors:
        print(f"  {row['verdict_class']:24s} {row['prior_pct']:>3s}%")


if __name__ == "__main__":
    main()
