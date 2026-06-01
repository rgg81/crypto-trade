# Phase 7.5 Critic Review — iter-v1/030

OVERALL: EXPLORATION-NEGATIVE-CATASTROPHIC — F1 OOS Δ -0.81 = NEGATIVE-CATASTROPHIC; F-AXIS #3 M2-pass OOS WR 38.3% FAIL (anti-discriminates BELOW baseline 40.2%); meta-labeling axis CLOSED at v1 by 2-iteration precedent (v3/017 + v1/030).

## Iteration Type
TYPE: EXPLORATION cycle-4 #3/10 — meta-labeling axis (NEW family)

## Verdict Cell Determination (binding per brief Section 4)

| F-AXIS | Pre-registered band | Observed | Disposition |
|---|---|---|---|
| F1 OOS Δ | [-0.40, -0.10] = NEG-OVER; < -0.40 = NEG-CAT | **-0.81** | NEGATIVE-CATASTROPHIC (Row 8) |
| F-AXIS #1 M2-trained cells | ≥ 80 of 159 | 159 of 159 (100%) | PASS |
| F-AXIS #2 OOS trade count | ≥ 90 | 204 (M2-filtered: 154, Model E pass-through: 50) | PASS (not OVER-FILTER cap) |
| F-AXIS #3 M2-pass OOS WR | ≥ 48% PASS; < 42% FAIL | **38.3%** | **FAIL** — M2 anti-discriminates (-1.9pp BELOW baseline 40.2%) |
| F-AXIS #5 OOS TP-exit count | ≥ 15 (Portfolio); ≥ 3 (Model D) | 35 (A=21, C=8, D=6) | PASS on both |

Two binding adjudications fire simultaneously: F1 binary in catastrophic territory + F-AXIS #3 anti-discrimination cap. Verdict cell is **NEGATIVE-CATASTROPHIC** under F1 AND simultaneously cap-confirmed at NEG-OVER-FILTER under F-AXIS #3.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Foundation embargo intact at `walk_forward.py:113`. M2 labels derived ex-post inside training window only (`metalabeling.py:580-617`). M2 input dim = 45 — no future-data contamination.

### Check 2 — Embargo Width: PASS
4 regression tests at `tests/test_lookahead_embargo.py` all PASS.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
DSR IS -66.62 / OOS -47.35 (catastrophic). PSR_monthly_vs_0 = 0.2171 IS / 0.4455 OOS. PSR_monthly_vs_1 = 0.0057 IS / 0.1090 OOS. PBO = null (single-seed). EXPLORATION carve-out applies; informational not BLOCK-triggering.

### Check 4 — IC Correlation: PASS (vacuous; no new features)
M2 introduced no new V1_FEATURE_COLUMNS_PRUNED entry; M2 inputs are m1_confidence + m1_direction derived ex-post.

### Check 5 — ADF Stationarity: PASS
193 features / 42 declared exceptions. No new features → no new ADF rows.

### Check 6 — Pareto Dominance: N/A (single-seed=42 EXPLORATION)

### Check 7 — Reproducibility: PASS
HEAD `a944c87`. Iter-stamped OOF parquet + M2 params parquet. Seed=42 single-seed declared. Feature columns explicit V1_FEATURE_COLUMNS_PRUNED (43).

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief H1 (M2 filtering improves OOS) ↔ implementation 1:1. M2 fired 159/159. **The mechanism failed empirically — the SCIENTIFIC outcome, not a hypothesis-implementation mismatch.**

### Check 13 — Anti-Pattern Static Scan: PASS
A1-A14 clean in committed code at `a944c87`. The 2 Phase 6 defects (silent-fallback baseline; atr_column mismatch) were fixed mid-cycle.

### Check 14 — Axis Family Validation (v1-only): PASS
`meta-labeling` family declared in brief Section 0.6. NEW NINTH family designation. Prior 5 EXPLORATIONs (/023 feature-family, /024 model-arch, /025 feature-family, /028 per-cohort, /029 per-cohort) disperse across 3 families. Rotation status VALID.

## Structural Finding (load-bearing for cycle-4)

**Meta-labeling axis CLOSED at v1 by 2-iteration precedent.** v3/017 NEGATIVE-clean over-filter + v1/030 NEGATIVE-CATASTROPHIC. The /030 result is mechanically WORSE than v3/017's:
- v3/017: M2 active filtering, NO quality lift on retained trades (NEGATIVE-clean)
- v1/030: M2 active filtering at 100% dispatch, **ANTI-quality on retained trades** (-1.9pp WR drag), **AND catastrophic headline drift** (-0.81 OOS Δ)

**Per LM Master /030 Phase 7.4 §2**: actual mechanism is **M1 BUDGET-DOWNSHIFT BASIN RELOCATION**, not M2 over-filter. M2 fired 100% pass-through (never gated). DOT (no M2) shows 24% baseline overlap with -14.17pp PnL collapse — proves the mechanism affects symbols WITHOUT M2. The 62% M1 compute reduction (3-seed × 18-trials vs baseline 5-seed × 50-trials, absorbed to fit M2 wall-clock cost) destroyed cross-symbol basin stability.

**The closure rationale**: two precedents on a methodologically expensive architectural axis at single-seed EXPLORATION is sufficient to retire it. Further EXPLORATIONs would test the same mechanism at different parameter regions — knob-tuning trap territory.

**Model A pooled BTC+ETH IS catastrophe** (BTC IS -44.5%, ETH IS -148.3%) contradicts LM Master §1 Fact 1's expectation that A's 206 cumulative M1-pos would be adequate — even the largest cohort cell broke under M2 at 45-feature × 18-trial × single-seed configuration.

## Recommendations to QR (process-level)

1. **Two-iteration precedent rule for architectural axes**: when an axis family fails NEGATIVE on two distinct tracks/iterations, CLOSE the family regardless of remaining theoretical configurations.

2. **F-AXIS #3 anti-discrimination test should generalize**: future post-prediction filters should require `filtered_WR > baseline_WR + epsilon` as hard floor, not just `filtered_WR ≥ baseline_WR - epsilon`.

3. **Sample-size adequacy is not sufficient at single-seed EXPLORATION**: future architectural-axis EXPLORATIONs should consider 3-seed mini-ensemble at cost of fewer Optuna trials (e.g., n_trials=10 × seed=3 vs n_trials=18 × seed=1).

## Path Forward (mandatory on BLOCK/NEGATIVE verdict)

Meta-labeling axis CLOSED. Per brief Section 3.4 §7 PRE-COMMIT, /031 = NEW funding-rate-z-scores was the pre-committed routing. **The pre-commit must be RE-EVALUATED** because funding-rate family already fired LEARNED-NEG-clean at /023, and Pool-A NEW-feature single-seed is STRUCTURALLY BLOCKED per `feedback_v1_pool_a_new_feature_lneg.md`.

Three alternative axes for /031 from families NOT used in the prior 5 EXPLORATIONs:

1. **Sample-weighting composite (AFML Ch.4 §4.6 `triple_uniqueness × inverse_concurrency`)** — family: **sample-weighting** (structurally orthogonal to /016 `uniqueness_only` closure). Mechanism: down-weight bars where multiple labels overlap AND uniqueness is low. **TOP RECOMMENDATION.** Aligns with LM Master /030 §4 binding mandate. Single-axis discipline preserved; compute-cheap; independent of M1 basin stability.

2. **Trend-scanning labels (AFML Ch.5 §5.5)** — family: **labeling** (NEW labeling sub-type). Cap trend-scan window at 21 bars to guarantee label-count parity with baseline. Expected mechanism: capture statistical-significance of trend direction rather than barrier-hit binary.

3. **Vol-targeting at per-trade weight (per /010 R5 closure follow-up)** — family: **risk-primitive** (PARTIALLY used at /010 per-symbol-vol; per-trade-vol is AFML §10 standard, structurally different mechanism class).

## /031 Routing Recommendation

**/031 axis = Sample-weighting composite (AFML Ch.4 §4.6 `triple_uniqueness × inverse_concurrency`)** — primary recommendation.

**CRITICAL LM Master §8 LOAD-BEARING constraint**: /031 MUST use FULL baseline M1 compute budget (5-seed × 50 trials minimum) per LM Master /030 §8 mandate. The /030 root-cause was M1 budget downshift basin relocation. Single-seed × n_trials=18 + 3-seed inner ensemble destroyed cross-symbol basin stability. Repeating this compute compromise on /031 will produce another NEG-CAT regardless of axis chosen.

Cycle-4 status after /030: /028 PROMISING, /029 TF, /030 NEG-CAT — 7 EXPLORATIONs remain. Earliest CONFIRMATION at /037 conditional on 10 cumulative EXPLORATIONs since /028.

## NEW Phase 6.0 Critic Checks Recommended

Cycle-4 Phase 6 defect record: 5 defects in 4 iterations (silent zero-mask /024, defective hard-assert /027, wall-clock breach /029, dispatch elif /030, atr_column mismatch /030). Three new Phase 6.0 Critic mini-checks recommended for v1 (NOT v3):

**Mini-Check J — Dispatch graph integration smoke test**. For every NEW `elif iteration_label == "v1-NNN"` branch added in `run_baseline_v1.py`, verify the branch is REACHABLE from `main()` at the actual CLI invocation. /030's dispatch elif was syntactically present but masked by upstream baseline catch-all.

**Mini-Check K — Strategy attribute symmetry against wrapping classes**. When a NEW strategy wraps existing strategy, grep every attribute access the WRAPPER makes on the WRAPPED class and confirm each attribute exists. /030's `atr_column` mismatch (MetaLabelingStrategy default `natr_21_raw` vs LightGbmStrategy default `vol_natr_21`) is structurally identical to /027's `r.model_name` defect.

**Mini-Check L — Wall-clock estimate validation against precedent ratios**. Brief 5-step scaling computation MUST be validated against PRIOR ITERATION's actual wall-clock at the same configuration; tolerance `predicted ∈ [observed_prior × 0.5, observed_prior × 1.5]`. /029 wall-clock breach was in-band per scaling computation but empirically wrong by >100%.

These checks are additive, pure read-only grep + structural analysis, preserving Critic's read-only invariant. Would have flagged 3 of 5 cycle-4 defects.

## Verdict: EXPLORATION-NEGATIVE-CATASTROPHIC

NO-MERGE (EXPLORATION; only CONFIRMATION-MERGE updates baseline). Axis closure: meta-labeling CLOSED for v1 at n=2 (v3/017 + v1/030). BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` `f8bc12c`.

## Cycle-4 Cumulative

After /030: /028 PROMISING + /029 TF + /030 NEG-CAT. 3 of 10 EXPLORATIONs spent. 1 PROMISING. Cycle-4 trajectory undershoots cycle-3 by 50% at iteration 3 — but cause is M1-budget mis-allocation (/029 wall-clock, /030 basin relocation), not signal-axis exhaustion. Strategic call: maintain axis diversity; mandate baseline M1 compute budget for /031+.
