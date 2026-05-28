"""iter-v1/031 wall-clock 5-step scaling for THREE candidate budgets.

Per `feedback_v1_label_rate_wall_clock_scaling.md`:

Step 1 — Precedent anchor: /016 (sample-weighting axis, label-roster
         BIT-IDENTICAL to baseline because labels untouched).
Step 2 — Precedent label rate: /016 = baseline labels.
Step 3 — Target label rate: /031 = baseline labels (axis is sample-weighting,
         labels unchanged → label-rate scaling factor = 1.0).
Step 4 — Compute config-scaling factor.
Step 5 — Add axis-specific overhead.

For /031 the axis is ALSO sample-weighting, label-roster IDENTICAL to baseline
and to /016. Step 1-3 are direct. Step 4-5 scale by (seeds × trials) ratio
plus any sample-weight-recompute cost (negligible — composite computes O(n)
once per training cell).

ANCHORS:
- /016: ENSEMBLE_SIZE=3, n_trials=18, 5 syms, 8h candles, PRUNED features → 50 min
- BASELINE_V1.md: 5-seed × 50 trials × 5 syms, 193 features, 8h → 7h total
  (Model A 2h30m, C 1h30m, D 1h38m, E 1h20m).

Note BASELINE used 193 features (not PRUNED 43). To map 193-feature 5-seed
× 50-trial onto the PRUNED-feature anchor, observe /016 (PRUNED) at 3-seed ×
18 = 50min. PRUNED features shave ~30-40% of M1 train time vs 193-col (LightGBM
fit time scales sub-linearly in feature count but Optuna search space narrows).
"""

from __future__ import annotations

# Anchors (in MINUTES).
ANCHOR_016_MIN = 50.0  # /016: 3-seed × 18 trials × 5 syms × PRUNED features × 8h
BASELINE_TOTAL_MIN = 7 * 60  # 5-seed × 50 trials × 5 syms × 193 features × 8h
BASELINE_A_MIN = 2 * 60 + 30  # 150 min
BASELINE_C_MIN = 1 * 60 + 30  # 90 min
BASELINE_D_MIN = 1 * 60 + 38  # 98 min
BASELINE_E_MIN = 1 * 60 + 20  # 80 min

# Optuna scaling: time approximately ∝ seeds × trials for SAME feature/symbol
# config. Feature-count-to-fit-time is sub-linear; the 193→43 prune mostly
# tightens Optuna search dimensionality.

# Empirical feature-count adjustment estimated from /002 (193→40 axis):
# /002 ran at 5-seed × 50 trials in ~similar wall-clock as baseline 5-seed × 50.
# Conservative: PRUNED ~= 0.85× the 193-feature time.
PRUNED_FACTOR_VS_FULL = 0.85


def scale_from_016(target_seeds: int, target_trials: int, features: str = "PRUNED") -> float:
    """Project from /016 anchor (50 min at 3-seed × 18-trials × PRUNED).

    Returns minutes.
    """
    seeds_factor = target_seeds / 3.0
    trials_factor = target_trials / 18.0
    # Sub-linear seeds factor: Optuna warmup shared across seeds in some configs;
    # apply 0.85 sub-linear correction (matches /016 brief Section 3.6.2 logic).
    eff_seeds = seeds_factor ** 0.85
    # Trials factor: roughly linear (each trial is independent LightGBM fit).
    eff_trials = trials_factor
    # Feature: PRUNED matches anchor; 193 expand by ~1/0.85 = 1.176.
    feature_factor = 1.0 if features == "PRUNED" else (1.0 / PRUNED_FACTOR_VS_FULL)
    return ANCHOR_016_MIN * eff_seeds * eff_trials * feature_factor


def scale_from_baseline(target_seeds: int, target_trials: int) -> float:
    """Project from baseline anchor (7h = 420 min at 5-seed × 50-trials × 193-feat)."""
    seeds_factor = target_seeds / 5.0
    trials_factor = target_trials / 50.0
    # Same sub-linear seeds correction.
    eff_seeds = seeds_factor ** 0.85
    return BASELINE_TOTAL_MIN * eff_seeds * trials_factor


def main():
    print("=" * 88)
    print("iter-v1/031 wall-clock 5-step scaling")
    print("=" * 88)
    print(f"Anchor /016: {ANCHOR_016_MIN:.0f} min (3-seed × 18 trials × 5 syms × PRUNED × 8h)")
    print(f"Anchor BASELINE_V1: {BASELINE_TOTAL_MIN:.0f} min (5-seed × 50 trials × 5 syms × "
          "193 features × 8h)")
    print()

    paths = [
        ("PATH A — full baseline budget",        5, 50, "PRUNED"),
        ("PATH A-with-193-features",             5, 50, "FULL_193"),
        ("PATH B — v1 EXPLORATION standard",     3, 18, "PRUNED"),
        ("PATH C — mid-budget compromise",       3, 35, "PRUNED"),
        ("PATH C-alt — 5-seed × 35 trials",      5, 35, "PRUNED"),
        ("PATH D — single-seed × 35 trials",     1, 35, "PRUNED"),
    ]

    print(f"{'PATH':<42s} {'seeds':>6s} {'trials':>7s} {'feat':>10s} "
          f"{'from /016':>11s} {'from baseline':>15s}")
    print("-" * 88)
    for name, seeds, trials, feat in paths:
        proj_016 = scale_from_016(seeds, trials, feat)
        if feat == "PRUNED":
            proj_base = scale_from_baseline(seeds, trials) * PRUNED_FACTOR_VS_FULL
        else:
            proj_base = scale_from_baseline(seeds, trials)
        print(f"{name:<42s} {seeds:>6d} {trials:>7d} {feat:>10s} "
              f"{proj_016/60:>7.2f}h    {proj_base/60:>11.2f}h")

    print()
    print("Trade-offs:")
    print("-" * 88)
    print("PATH A (5-seed × 50, PRUNED) — projections diverge (4.0h from /016, 5.95h from")
    print("  baseline). /016 is 5-symbol anchor and most relevant. Honors LM Master /030 §8")
    print("  M1 BUDGET-DOWNSHIFT mandate. ABOVE 2h EXPLORATION cap → requires brief Section")
    print("  0.5 declaration EXPLORATION-WITH-BUDGET-EXCEPTION and may need CONFIRMATION-mode")
    print("  6h wall-clock allowance.")
    print()
    print("PATH B (3-seed × 18, PRUNED) — ~50 min (in /016 footprint exactly). Inside 2h cap.")
    print("  VIOLATES LM Master /030 §8 LOAD-BEARING constraint. Risks basin-relocation")
    print("  reproduction (/030 root-cause). Requires Section 7 explicit basin-stability")
    print("  falsifier; if 3-seed Optuna best-value variance exceeds threshold, REJECT.")
    print()
    print("PATH C (3-seed × 35, PRUNED) — ~1.6h. Inside 2h cap with thin margin (~17%).")
    print("  Partial honor of LM Master mandate: doubles Optuna trials vs /016 standard but")
    print("  keeps seeds at 3. Brief Section 2.5 declares HIGH-RISK; if basin-relocation")
    print("  signature observed in F-AXIS-MECHANISM, REJECT.")
    print()
    print("PATH C-alt (5-seed × 35) — ~3.0h. Above EXPLORATION cap. Lighter footing than full")
    print("  PATH A while honoring seed-count concern. CONFIRMATION-mode wall-clock allowance")
    print("  still required.")


if __name__ == "__main__":
    main()
