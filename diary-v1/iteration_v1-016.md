---
iteration: iter-v1/016
date: 2026-05-26
verdict: EXPLORATION-NEGATIVE
subtype: catastrophic
axis_family: sample-weighting (NEW family — never used in v1)
cadence_position: cycle-3 EXPLORATION (#1 of 10; cycle-3 begins here)
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c) — UNCHANGED
merge_decision: NO-MERGE (EXPLORATION-NEGATIVE catastrophic; F1 OOS Δ -1.6690 + F3 IS Δ -0.5884; F-AXIS-MECHANISM PASS-by-construction = wiring test, not edge test; BASELINE_V1 update NOT triggered)
---

# Iteration iter-v1/016 — Diary

## Decision: NO-MERGE

EXPLORATION-NEGATIVE catastrophic. Sample-weighting axis CLOSED at v1 after one pass on `uniform` mode. v1 BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`).

## One-Line Outcome

At v1 EXPLORATION budget (ENSEMBLE_SIZE=3 + n_trials=18 + V1_FEATURE_COLUMNS_PRUNED + full 5-symbol universe + 8h candles + `sample_weight_mode="uniform"` + `bounds_profile="v1_pruned_axis016"`) replacing the baseline `abs(labeled_pnl)` weighting with pure uniform weights produced **IS Sharpe -0.3055** (Δ **-0.5884** NEGATIVE-catastrophic; below F3 catastrophic floor -0.30 by 0.29) + **OOS Sharpe -1.0053** (Δ **-1.6690** catastrophic-extreme; below F1 catastrophic floor -0.55 by 3.04× the boundary) + **F-AXIS-MECHANISM PASS-by-construction** (Kish=1.0 / Model A balance 0.500/0.500 / timeout=0.0 — all three sub-checks PASS by mathematical inevitability under uniform weights) + **n_eff_per_cell_median = 9** (BELOW LM Master Phase 4.5 predicted [10, 20] band — REFUTED; NEW weight-distribution driver discovered) + **ETH OOS catastrophic -51.46** (third consecutive axis producing ETH OOS ≤ -23 across /014/015/016 — STRUCTURAL drag at universe level) + **wall-clock ~50min** (75% margin against 2h cap — FIRST cycle-3 empirical anchor) — sample-weighting axis CLOSED at v1 baseline-labels; closes by inheritance on `uniqueness_only` per QR EDA Spearman 0.997 with uniform; /017 advances to universe expansion (PRIMARY per LM Master + Critic Path Forward).

## What Worked

### Wall-clock discipline empirically validated — FIRST cycle-3 datapoint

Predicted band 1.50-1.75h with LM Master Phase 4.5 Rec #1 pre-emptive n_trials=18 compression. **Observed ~50 minutes total — 75% margin against the 2h EXPLORATION cap.** Forecast overstated actual by ~2-3×. The wall-clock model at the current configuration (ENSEMBLE_SIZE=3, n_trials=18, V1_FEATURE_COLUMNS_PRUNED, 5-symbol, 8h) is empirically CONSERVATIVE. Headroom available for /017's 6-7 symbol universe expansion without further compression. Skill update proposal noted in engineering report §6.2.

### F-AXIS-MECHANISM wiring test PASSed exactly as predicted

LM Master Phase 4.5 Risk #1 ("F-AXIS-MECHANISM false-PASS risk: all three sub-checks PASS by CONSTRUCTION under uniform weighting") vindicated:
- Kish n_eff ratio = 1.0000 (every cell — math identity under uniform)
- Model A per-symbol balance = 0.500 / 0.500 (every cell — by construction with equal BTC/ETH row counts)
- timeout_fallback_share = 0.0000 every cell (labels untouched)

The implementation was structurally correct; the brief's mechanism prediction was simply refuted by the data.

### LM Master mechanism-level prediction track advanced (refuted + confirmed)

- **CONFIRMED**: F-AXIS-MECHANISM PASS by construction does NOT imply edge — definitively proven at OOS Sharpe -1.0053. Canonical exemplar of "wiring test ≠ edge test" for future briefs (Critic Check 8 catalog).
- **REFUTED**: "n_eff_per_cell is loss-surface-shape-bound, not weight-bound" (Phase 4.5 Rec #3). Observed n_eff = 9 outside [10, 20] band. Weight-distribution is a second driver of n_eff_per_cell.

### Engineering report 5th-strike fix delivered

Phase 7 engineering report retroactively closes the `--no-engineering-report` opt-out gap from Phase 6 dispatch. Deliverable at `reports-v1/iteration_v1-016/engineering_report.md` (HEAD `b35446a`).

## What Failed

### F1 OOS catastrophic (Δ -1.6690; 3.04× the catastrophic floor)

OOS Sharpe collapsed from baseline +0.6637 to /016 -1.0053 = **largest single-iteration OOS drop in cycle-3 so far** (and tied with /015's catastrophic on relative scale). Falls outside the pre-registered FLAT band [-0.30, +0.30] by 5.6× the boundary. The hypothesis "uniform weighting will produce multi-seed mean OOS within [-0.30, +0.30]" was empirically refuted by orders of magnitude.

### F3 IS catastrophic (Δ -0.5884; below floor by 0.29)

IS Sharpe collapsed from baseline +0.2829 to /016 -0.3055. Bilateral catastrophic on IS+OOS — both halves outside any pre-registered band. The `abs(labeled_pnl)` weighting is **structural to v1's edge**, not removable artifact.

### Mechanism call REFUTED — n_eff_per_cell has a second driver

Predicted [10, 20] reasoning was "n_eff_per_cell is loss-surface-shape-bound, not weight-bound." **Observed median 9** across all 5 symbols (BTC=10, DOT=9, ETH=10, LINK=9, LTC=9). LM Master Phase 7.4 §2 mechanism revision (verbatim): "weight-magnitude variation itself contributes to per-cell loss-surface diversity. Compressing weight range [1, 10] → [1, 1] made Optuna's per-trial loss surfaces MORE similar across trials → PCA-on-trial-returns substrate collapsed."

**Revised model**: `n_eff_per_cell ← f(label_shape, weight_distribution)`. Codified into `feedback_v1_abs_pnl_weighting_structural.md`.

### ETH OOS catastrophic continues — STRUCTURAL across 3 axes

| Iteration | Axis | ETH OOS |
|---|---|---|
| /014 | labeling (σ_t LABEL-only) | -41.18 |
| /015 | labeling (σ_t symmetric, C1 FIX, multi-seed) | -23.29 |
| /016 | sample-weighting (uniform) | **-51.46** |

Three different axes, three catastrophic ETH OOS readings. The drag is **STRUCTURAL** (regime-conditioned), not iteration-specific. Forward concern for /017+ (Critic Phase 7.5 Rec #2 — non-renegotiable).

### Engineering report opt-out re-fired (5th strike)

QE Phase 6 dispatched with `--no-engineering-report` flag at HEAD `4e797e8`. Procedurally legal (the flag exists) but recurs the same forensic gap from /014 and /015. Critic Phase 7.5 Check 7 WARN with Rec #1 codifying skill update proposal for /017+ orchestrator. Phase 7 retroactively closes /016's gap; permanent fix at orchestrator/skill layer is the right scope.

## Path Forward (from Critic Phase 7.5)

Verbatim from `briefs-v1/iteration_v1-016/review.md` §"Path Forward":

> Per cycle-3 §0.6 rotation discipline (prior 5: risk-primitive ×2, methodology-substrate-test ×2, labeling ×1):
>
> 1. **Universe expansion** — `universe` family (UNUSED since /006; never tested in cycle-2 or cycle-3). Add 1-2 symbols from V1_EXCLUDED_SYMBOLS (SOLUSDT preferred for cycle-2 OOS-rich profile non-correlated-with-BTC; XRPUSDT alternate). 6-symbol universe at ENSEMBLE_SIZE=3 + n_trials=18 estimated 1.7-1.8h. Mechanism: dilute ETH's catastrophic weight in portfolio Sharpe denominator AND test whether basin-lock is universe-bound vs regime-bound. **PRIMARY** per LM Master Phase 7.4 §6.
>
> 2. **Model architecture (XGBoost)** — `model-arch` family (UNUSED in v1; matches v3/016 axis priority precedent). Head-to-head LightGBM vs XGBoost on identical V1_FEATURE_COLUMNS_PRUNED + abs_pnl weighting baseline. **Deferred to /018+** per user XGBoost-slower flag; needs wall-clock smoke test characterization first. SECONDARY.
>
> 3. **ETH-specific regime kill switch / per-symbol drawdown brake** — `risk-primitive` family-variant. IF /017 universe expansion does NOT reshape ETH drag, /018 pivots to ETH-conditional kill (regime-bound gate, not threshold-tuning). TERTIARY — conditional on /017 outcome.

(With the LM Master Phase 7.4 §6 "RECOMMEND UNIVERSE EXPANSION at /017" call aligning with Critic Path Forward #1, /017 = universe expansion is PRIMARY.)

## Critic Review Summary (briefs-v1/iteration_v1-016/review.md, HEAD `892b748`)

- Check 1 (Look-Ahead): PASS — no code change touches labeling.py, walk_forward.py, or feature pipeline; only lgbm.py sample_weight branch + bounds_profile pin
- Check 2 (Embargo): PASS — foundation untouched; `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`; 4 regression tests present
- Check 3 (DSR/PBO/PSR): FAIL informational for EXPLORATION — DSR_IS=-62.30, DSR_OOS=-38.24, PSR_monthly_vs_0 IS=0.289/OOS=0.125; all below thresholds; n_eff = 9 below LM Master predicted [10, 20] band
- Check 4 (IC): PASS — no feature change; identical to /015 baseline
- Check 5 (ADF): PASS — no feature change
- Check 6 (Pareto): N/A — single-seed EXPLORATION
- Check 7 (Reproducibility): **WARN** — `engineering_report.md` MISSING via `--no-engineering-report` opt-out (5th strike); brief §10.2 explicitly stated "engineering_report.md MUST exist"; NOT FAIL because comparison.csv + f_axis_mechanism.csv consistent + HEAD `4e797e8` stable + feature_columns + ensemble_seeds explicit; Phase 7 retroactive closure at `b35446a`
- Check 8 (Hypothesis-Implementation Alignment): **PASS-by-construction-WITH-CRITICAL-NOTE** — F-AXIS-MECHANISM compound falsifier PASSes all three sub-checks by mathematical construction; canonical "wiring test ≠ edge test" exemplar; add to Check 8 catalog as v1 reference case
- Check 13 (Anti-Patterns): PASS — A1/A2/A3/A4-A11/A12/A13/A14 all clean
- Check 14 (Axis Family): PASS — `sample-weighting` declared NEW; src/ diff exclusively in lgbm.py sample_weight branch + optimization.py v1_pruned_axis016 bounds pin; rotation VALID (prior 5: risk-primitive ×2, methodology-substrate-test ×2, labeling ×1)
- **OVERALL: EXPLORATION-NEGATIVE catastrophic**

## Pre-Registered Failure-Mode vs Reality

From brief Section 7:
> "Modal /016 NULL with F-AXIS-MECHANISM CLEAN PASS — closing the axis at uniform after one shot."

(LM Master Phase 4.5 Closing Note: 40% net-helpful / 35% net-harmful / 25% net-no-op; verdict-class FLAT 33/33/34.)

**Actual**: NEGATIVE-catastrophic bilateral on F1 AND F3. The NET-HARMFUL bucket fired; LM Master Phase 4.5 §3 closing line ("weight-removal at LEAST as likely to HURT IS Sharpe as help it") landed in catastrophic direction.

**Match**: Directionally PARTIAL (NET-HARMFUL bucket fired as one of three possibilities at 35%) — magnitude UNDERSTATED by LM Master (-1.67 vs implied modal -0.30 net-harmful range). The F-AXIS-MECHANISM wiring PASS-by-construction call was **explicitly correct** (Phase 4.5 §1 Risk #1 vindicated at Phase 7.4 §3). The n_eff_per_cell prediction band [10, 20] was REFUTED at observed 9 — second driver discovered.

## 5 LESSONS for v1 Cycle-3 Catalog

### LESSON #1: abs(labeled_pnl) weighting is STRUCTURAL to v1's edge — sample-weighting axis CLOSED at v1

The baseline `abs(labeled_pnl)` weighting (range [1, 10] via `1 + abs(pnl)/max × 9`) was treated by the brief as a "per-symbol asymmetry source" needing correction (BTC under-weighted 4.9% / ETH over-weighted 4.9% in Model A; LTC/DOT high-PnL outliers dominating). **The asymmetry was load-bearing, not noise.** High-magnitude trades (LINK 74.70%, ETH 47.46%, DOT 44.43%) carry **genuine forward signal** that the gradient needs to upweight. Removing the Bayesian prior collapsed both IS (Δ -0.59) and OOS (Δ -1.67) catastrophically.

**Codified rule**: sample-weighting axis CLOSED at v1 for both `uniform` (tested at /016) AND `uniqueness_only` (Spearman 0.997 with uniform per QR EDA — closes by inheritance). No re-entry without explicit new evidence on a weighting mechanism orthogonal to uniformization (e.g., past-realized-vol inverse weighting that does NOT compress range to [1, 1]). Codified into `feedback_v1_abs_pnl_weighting_structural.md`.

### LESSON #2: F-AXIS-MECHANISM PASS by construction = canonical "wiring test ≠ edge test"

All three F-AXIS-MECHANISM sub-checks (Kish=1.0, Model A balance 0.500/0.500, timeout=0.0) PASSed by mathematical inevitability under uniform weighting — they cannot fail. Yet OOS Sharpe -1.0053. **F-AXIS-MECHANISM PASS by construction does NOT imply edge.**

LM Master Phase 4.5 §1 Risk #1 ("F-AXIS-MECHANISM false-PASS risk") flagged this in advance; Phase 7.4 §3 vindicated; Critic Phase 7.5 Check 8 endorses adding /016 as the **v1 reference case** for future briefs.

**Codified rule**: any axis whose wiring-mechanism falsifier PASSes by mathematical construction (uniform-anything, identity-anything, by-design-feature-engineering) must include an **independent edge-attribution sub-check** that does not reduce to the wiring identity. The leading candidate is n_eff_per_cell (see LESSON #3).

### LESSON #3: n_eff_per_cell has TWO drivers — label-shape AND weight-distribution

Strongest mechanism finding of cycle-3 #1. Cycle-2 /015 established n_eff as a CURVE in barrier-magnitude space (label-shape driver: at 7.82% labels timeout_fallback dominance → n_eff = 3). /016 adds the second driver:

| Iteration | Labels | Weights | n_eff_per_cell_median |
|---|---|---|---|
| /014 | σ_t × k × √timeout LABEL-only (1.70% effective) | abs(labeled_pnl) range [1, 10] | 19 |
| /015 | σ_t × k × √timeout symmetric (7.82% barriers) | abs(labeled_pnl) range [1, 10] | **3** (label-shape collapse) |
| /016 | baseline ATR labels | uniform range [1, 1] | **9** (weight-distribution moderate collapse) |
| BASELINE | baseline ATR labels | abs(labeled_pnl) range [1, 10] | 13 |

**Revised mental model**: `n_eff_per_cell ← f(label_shape, weight_distribution)`. Two driver layers. Compressing weight range [1, 10] → [1, 1] made Optuna's per-trial loss surfaces MORE similar across trials → PCA-on-trial-returns substrate collapsed moderately (13 → 9).

**Codified rule**: any future "uniform-anything" or "identity-anything" axis MUST pre-register n_eff_per_cell as an F-AXIS-MECHANISM sub-check with an explicit band prediction. Codified into `feedback_v1_abs_pnl_weighting_structural.md`.

### LESSON #4: ETH OOS catastrophic is STRUCTURAL across 3 axes — forward concern at universe level

| Iteration | Axis (mechanism layer) | ETH OOS PnL |
|---|---|---|
| /014 | labeling — σ_t × k × √timeout LABEL-only | -41.18 |
| /015 | labeling — C1 FIX symmetric σ_t × k × √timeout (multi-seed n=10) | -23.29 |
| /016 | sample-weighting — uniform weights | **-51.46** |

Three different axes operating on **disjoint mechanisms** (label distribution shape vs sample-weight magnitude). All three produce ETH OOS catastrophic. The drag is **STRUCTURAL** at the universe level — regime-conditioned, likely 2025-Q1 to 2026-Q1 ETH-specific weakness.

**Forward mandate (Critic Phase 7.5 Rec #2)**: /017+ briefs MUST explicitly acknowledge ETH structural drag in Section 2 EDA AND pre-register either (a) universe-expansion-as-dilution test OR (b) ETH-specific regime kill switch. If /017 universe expansion does NOT reshape ETH drag, /018 pivots to ETH-conditional kill (regime-bound gate, NOT threshold-tuning).

### LESSON #5: Wall-clock discipline empirically validated — cycle-3 model is CONSERVATIVE

- **Predicted (brief §3.6.3)**: 1.50-1.75h
- **Pre-emptive compression (LM Master Phase 4.5 Rec #1)**: n_trials 20 → 18 for ≥20% margin
- **Observed**: ~50 minutes
- **Margin realized**: **75%** (50min / 120min cap)
- **Forecast error**: prediction band overstated actual by 2-3×

The current QR wall-clock model at ENSEMBLE_SIZE=3 + n_trials=18 + V1_FEATURE_COLUMNS_PRUNED + 5-symbol + 8h candles is **empirically CONSERVATIVE**. Headroom available for /017's 6-7 symbol universe expansion at the same configuration without further compression — linear scaling to 7 symbols ≈ 70min (~40% margin).

**Skill update proposal (informational)**: amend `feedback_v1_wall_clock_discipline_enforced.md` with empirical datapoint "5-symbol PRUNED-feature ENSEMBLE_SIZE=3 n_trials=18 8h candles → ~50min observed (75% margin)." Permits /017 universe expansion at 6-7 symbols within 2h cap empirically validated.

## Cycle-3 Cadence Status (after /016)

- Cycle-3 EXPLORATION count: **1 of 10**
- CONFIRMATION earliest: /026 (assuming sequential EXPLORATIONs; pre-committed conditional unchanged)
- Edge ingredients merged this cycle: **0**
- Verdict distribution cycle-3 so far: 1 EXPLORATION-NEGATIVE catastrophic
- BASELINE_V1.md unchanged at `v0.v1-baseline-corrected` (`f8bc12c`)

## Axis Rotation Status (v1-only)

- **This iter's family**: `sample-weighting` (NEW family; never used in v1; now CLOSED)
- **Prior 5 EXPLORATION families**: `risk-primitive` (/010), `risk-primitive` (/011), `methodology-substrate-test` (/012), `methodology-substrate-test` (/013), `labeling` (/014)
- **Rotation honored**: YES — `sample-weighting` is NEW, distinct from the prior 5 (all in 3 closed families)
- **Updated prior 5 going into /017**: `methodology-substrate-test` (/012), `methodology-substrate-test` (/013), `labeling` (/014), `labeling` CONFIRMATION (/015 — N/A but family-tagged), `sample-weighting` (/016)
- **/017 first 5 EXPLORATION families MUST exclude**: `methodology-substrate-test`, `labeling`, `sample-weighting` (the prior 5 from /012-/016)
- **PRIMARY /017 family per Critic Path Forward**: `universe` (UNUSED since /006; rotation VALID)

## Next Iteration Ideas (cycle-3 second EXPLORATION = /017)

Ranked by expected impact within the 2h EXPLORATION wall-clock cap and rotation discipline:

1. **Universe expansion to 6-7 symbols** (`universe` UNUSED since /006) — Critic Path Forward #1 + LM Master Phase 7.4 §6 "RECOMMEND UNIVERSE EXPANSION at /017". Add 1-2 from V1_EXCLUDED_SYMBOLS (SOLUSDT preferred; XRPUSDT alternate; both not BTC-correlated to test denominator dilution). Mechanism: dilute ETH's catastrophic weight in portfolio Sharpe denominator AND test whether basin-lock is universe-bound vs regime-bound. Wall-clock: 6 symbols × ENSEMBLE_SIZE=3 × n_trials=18 ≈ 70min from /016 50min anchor (40% margin). **PRIMARY.**

2. **Multi-feature engineered composites** (`feature-family` UNUSED in cycle-2 since /009; cycle-2 /007/009 catalog entries were single-feature-family) — orthogonal axis to /017 PRIMARY if QR diagnoses ETH drag as feature-driven rather than universe-bound. Specific candidates: regime × momentum interactions, volume × volatility composites. Deferred to /018+ as alternate.

3. **ETH-specific regime kill switch / per-symbol drawdown brake** (`risk-primitive` family-variant) — Critic Path Forward #3, conditional on /017 outcome. IF /017 universe expansion does NOT reshape ETH drag, /018 pivots here. NOT proportional cap (v3/020 closed that). NOT static threshold (v3/054 deadlock pattern). Regime-conditional (e.g., BTC trend filter OR ETH-specific ATR-bandwidth gate).

All three from UNUSED-or-rotation-eligible families. Cycle-3 second EXPLORATION QR EDA-justifies one (PRIMARY = universe expansion per Critic + LM Master alignment) and proposes remaining two as alternates per Section 11 template under 2h wall-clock discipline.

## Files & Commits on Branch

- Branch: `iteration-v1/016` from `iter-v1/015` closeout commit (tag `v0.v1-015`)
- HEAD at brief approval (Phase 5.5 PASS): `5811b69`
- HEAD at QE implementation: `3a10b14` → tests `d6547f3` → Critic Phase 6.0 `1a64daa` → axis isolation fix `279635b` → subsample KeyError fix `b0f5717`
- HEAD at backtest completion: `4e797e8`
- HEAD at LM Master Phase 7.4: `4e797e8`
- HEAD at Critic Phase 7.5 verdict (EXPLORATION-NEGATIVE catastrophic): `892b748`
- HEAD at Phase 7 engineering report (5th-strike fix): `b35446a`
- HEAD at Phase 8 closeout (THIS COMMIT): TBD

Key commits in /016:
- `a273c94` — LM Master Phase 4.5 pre-design advisory
- `0991493` — brief Section 3.5 LM Master Phase 4.5 responses
- `5811b69` — Phase 5.5 gate PASS
- `3a10b14` — feat: NEW sample_weight_mode parameter (abs_pnl|uniform|uniqueness_only)
- `d6547f3` — test: sample_weight_mode tests + Kish n_eff math + CLI dispatch
- `1a64daa` — Critic Phase 6.0 pre-flight PASS
- `279635b` — fix: sample-weighting axis isolation — auto-disable BOTH R5 axes
- `b0f5717` — fix: subsample KeyError when v1_pruned_axis016 pins it
- (Backtest dispatched; comparison.csv + reports artifacts in `reports-v1/iteration_v1-016/`)
- `4e797e8` — LM Master Phase 7.4 post-mortem
- `892b748` — Phase 7.5 Critic review — EXPLORATION-NEGATIVE catastrophic
- `b35446a` — Phase 7 evaluation + engineering report (5th-strike fix)
- (THIS COMMIT) — Phase 8 diary + catalog + abs_pnl structural memory

**Trunk merge**: NONE. EXPLORATION-NEGATIVE catastrophic never updates BASELINE_V1.md. Sample-weighting axis CLOSED at v1 for both `uniform` AND `uniqueness_only` (Spearman 0.997 inheritance closure). No re-entry without orthogonal-mechanism new evidence.

**Tag**: `v0.v1-016` (applied after this Phase 8 closeout commit).
