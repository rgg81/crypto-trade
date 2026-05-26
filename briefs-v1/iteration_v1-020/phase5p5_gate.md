# Phase 5.5 Gate — iter-v1/020

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION
Cadence position: cycle-3 #5 of 10 (CONFIRMATION earliest at /027).

Prior cycle-3 EXPLORATIONs from catalog:
- iter-v1/016: sample-weighting (NEGATIVE-catastrophic)
- iter-v1/017: universe (NEGATIVE-anti-direction-INERT)
- iter-v1/018: per-cohort-specialization-LINK (PROMISING-INERT favorable)
- iter-v1/019: per-cohort-specialization-ETH (PROMISING)
Cycle-3 ledger: 2 PROMISING / 2 NEGATIVE / 0 merges.

## Axis Family + Rotation Status (v1 mandatory)
FAMILY: per-cohort-specialization-BTC (NEW 11th axis family; FIRST usage)
ROTATION_STATUS: VALID

Prior 5 entries in `briefs-v1/exploration_catalog.md` (verified):
- iter-v1/015: labeling (CONFIRMATION-spec; rotation N/A)
- iter-v1/016: sample-weighting
- iter-v1/017: universe
- iter-v1/018: per-cohort-specialization-LINK
- iter-v1/019: per-cohort-specialization-ETH

`per-cohort-specialization-BTC` does not match any of the prior 5 families.
Brief Section 0.6 declares orthogonality on three dimensions: different cohort (BTC vs
LINK and ETH), different specialization scope (NO gate/feature/labeling — pure isolation
control vs /018 isolation and /019 isolation+gate), and different structural prior (BTC =
IS-NEG/OOS-POS asymmetric rotation vs LINK IS+OOS positive vs ETH IS-NEG/OOS-NEG through
cycle-3). LM Master Phase 4.5 advisory (lgbm_advisor.md, line 8) independently treats this
as a structurally-distinct BTC-specific diagnostic. Rotation VALID.

NEW family declaration: per /012 Critic Phase 7.5 precedent, new family declarations require
Critic + LM Master + QR convergence on orthogonality. Brief Section 0.6 cites Critic /019
Phase 7.5 Path Forward #1 + LM Master Phase 7.4 §7 + QR as the 3-way convergence basis.
Satisfied.

## HIGH-RISK Declaration (v1 mandatory)
HIGH-RISK: YES
Reason: dropping Models A/C/D/E from the dispatch is a structural change to Optuna's
training-objective domain (universe goes from 5 symbols to 1 BTC-only with no ETH partner),
and BTC's structural prior is unique (5/5 IS-NEGATIVE + 4/5 OOS-POSITIVE asymmetric rotation).
Mitigation opted in: NONE — single-seed-style EXPLORATION at ENSEMBLE_SIZE=3 inner seeds.
/027 multi-seed dissolves basin-lottery uncertainty.

HIGH-RISK cumulative tracker: /016 catastrophic / /017 INERT / /018 PROMISING-INERT / /019
PROMISING. Net: 0 consecutive negatives — no 3-consecutive HIGH-RISK catastrophic trigger.
No mandatory multi-seed required for /020.

## LM Master Response Verification (v1 mandatory)
- briefs-v1/iteration_v1-020/lgbm_advisor.md exists (commit 9c6c32f): PASS
- lgbm_advisor.md has Phase 4.5 section with numbered recommendations: PASS
- Brief Section 3.4 addresses each LM Master recommendation: PASS

  Verification against lgbm_advisor.md sections:
  - §1 (adjusted priors PROMISING 20% / INERT 60% / NEGATIVE 20% + INERT-no-effect /
    INERT-preserved-asymmetric subtype split + mechanism distinction): ADOPTED
  - §2 (F-AXIS-MECHANISM #2 trade-count tighter sub-bands IS [79,147] point ~105 /
    OOS [25,46] point ~34 — INFORMATIONAL not blocking): ADOPTED
  - §3 (n_eff_per_cell band [7,10] point estimate 9 — INFORMATIONAL): ADOPTED
  - §4 (Jaccard pre-registered prediction 0.10-0.25; Jaccard>0.50 = PROMISING-MECHANICAL;
    <0.20 = NEW signal source; [0.20,0.50] = mixed mechanism): ADOPTED, integrated at
    Section 6.6 and Section 3.4
  - §5 (modal verdict INERT-no-effect; /020 = DIAGNOSTIC EXPLORATION; /027 bundle role =
    DIVERSIFICATION not ADDITIVE EDGE): ADOPTED at Section 1 hypothesis interpretation
    note + Section 11.6 bundle composition table
  - §6 (/021+ verdict-conditional pre-staging; modal /021 = LTC-only specialization 80%):
    ADOPTED at Section 11.7, LM Master matrix replaces QR's prior DOT-first staging
  - §7 (hyperparameters all frozen: n_trials=18, ENSEMBLE_SIZE=3, V1_FEATURE_COLUMNS_PRUNED,
    bounds_profile=v1_pruned, apply_r1=False, seeds=[42,123,456]): ADOPTED
  - §8 (cycle-3 specialist bundle update; BTC-only /027 role = DIVERSIFICATION baseline;
    /027 logic flow: INERT → use Model A not Model H): ADOPTED at Section 11.6
  - §12 (Critic Phase 7.5 priority items 1-5): ADOPTED at Section 10.1.b
  - Saturation Risks (informational cross-reference; already encoded in Section 5 + Section
    2.5): INFORMATIONAL CROSS-REFERENCE
  - What LM did NOT recommend (informational confirmation of brief design): INFORMATIONAL
    CROSS-REFERENCE

  Zero recommendations rejected or unaddressed.

## Cadence Check (v1 / EXPLORATION)
- Wall-clock budget declared: 25 minutes total (79% margin vs 2h cap): PASS
- EXPLORATION type: 2h cap applies; declared 25 min well within cap: PASS
- Kill-switch: 45 minutes (brief Section 3.6): PASS
- CONFIRMATION type: N/A (this is EXPLORATION)
- Exploration count #5 of 10 matches catalog count (4 EXPLORATIONs in cycle-3 before /020 +
  /015 CONFIRMATION-spec rotation-N/A): PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS window "2025-03 to 2026-05" appears in Section 0.3 and 2.3
  tables; IS window implicit from training_months=24 anchored at 2025-03-24 (same as /019
  PASS precedent); OOS_CUTOFF_DATE = 2025-03-24 and training_months = 24 referenced implicitly
  throughout config constants; per-cohort anchor BTC IS -37.28% / OOS +33.17% from IS EDA
  scripts committed at 283064b.

- Section 0.5 (Iteration Type): PASS — "EXPLORATION (cycle-3 #5 of 10)" declared at line 11
  and confirmed in Section 0.1 cadence ledger.

- Section 0.6 (Architecture-Family Justification): PASS — per-cohort-specialization-BTC declared
  as NEW 11th family; prior 5 EXPLORATION families listed and verified; rotation VALID with
  3-way orthogonality justification (QR + Critic /019 Path Forward + LM Master Phase 4.5 §9).

- Section 1 (Hypothesis): PASS — one-sentence primary hypothesis at line 118 (H1: BTC-only
  LightGBM will preserve BTC's IS-OOS asymmetric rotation per H_INTRINSIC). Sub-hypotheses
  H1a and H1b add specificity. Falsification logic with Sharpe-Δ thresholds clearly stated.
  NOT vague: "A LightGBM model trained on BTC-only data at Model A's existing pool config
  will preserve BTC's IS-OOS asymmetric rotation per H_INTRINSIC." Specific mechanism +
  specific predicted outcome.

- Section 2 (IS-Only Evidence): PASS — committed EDA scripts at analysis/iteration_v1-020/
  (commit 283064b: "feat(iter-v1/020): EDA — BTC IS catastrophic rotation hypothesis tests").
  Five scripts (01-05) produce concrete tables: btc_per_symbol_baseline.csv, btc_oos_trajectory.csv,
  btc_regime_concentration.csv, btc_pool_anchor_summary.csv, eda_summary.csv, wallclock_estimate.csv.
  Section 2.1-2.5 reproduce table contents with numerical evidence. H_POOL_ANCHOR refuted at ρ=−0.022
  (Pearson) / ρ=+0.023 (Spearman) from committed CSV. IS data only (OOS used only for verification
  of BTC-in-pool anchor numbers from prior baseline CSVs, not for EDA on /020 design).

- Section 2.5 (HIGH-RISK Axis Declaration): PASS — declared HIGH-RISK with one-sentence reason;
  mitigation opt-in declared as NONE; HIGH-RISK cumulative tracker shows 0 consecutive catastrophic
  negatives (no mandatory multi-seed trigger).

- Section 3 (Proposed Changes): PASS — implementation spec at Sections 3.1-3.3 with exact code
  blocks for V1_ITER020_UNIVERSE constant and elif dispatch branch; pinned values at Section 3.3;
  single src/ file change (run_baseline_v1.py). LM Master responses at Section 3.4 address all
  advisory items (see LM Master Response Verification above).

- Section 4 (Expected OOS Impact / Falsifiers): PASS — F1/F3/F2/F4-F8 + F-AXIS-MECHANISM
  #1/#2/#3/#4 falsifiers with concrete Sharpe-Δ and net_pnl-Δ thresholds; PROMISING/INERT/NEGATIVE
  band table at Section 4 F1; LM Master tighter sub-bands annotated on F-AXIS #2 (IS [79,147] /
  OOS [25,46]) as INFORMATIONAL; falsifier table pre-registered before Phase 6 backtest.

- Section 5 (Risk Mitigation / Predicted Verdict Distribution): PASS — PROMISING 20% / INERT 60%
  (INERT-no-effect 40% + INERT-preserved-asymmetric 20%) / NEGATIVE 20%; LM Master §1 ADOPTED
  refinement recorded; three specific mechanism predictions listed.

- Section 6 (Risk Management Design / Failure Modes): PASS — six failure modes documented
  (Sections 6.1-6.7): basin lottery, H_POOL_ANCHOR re-emergence, H_INTRINSIC partial-falsification,
  OOS catastrophic regime-loss, wall-clock breach, PROMISING-MECHANICAL adjacency. Section 6.6 has
  pre-registered Jaccard band [0.10, 0.25] from LM Master Phase 4.5 §4 with verdict implications
  (<0.20 new signal / [0.20,0.50] mixed / >0.50 PROMISING-MECHANICAL).

- Section 7 (Pre-Registered Failure-Mode Prediction): PASS — Section 6.6 serves as the explicit
  pre-registered failure-mode prediction (PROMISING-MECHANICAL Jaccard adjacency pre-registered
  before backtest). Sections 6.1-6.5 document additional forward-looking failure modes.

- Section 8 (Pre-Registered MERGE/NO-MERGE Numerical Criteria): PASS — Section 8 contains a
  verdict matrix table (8 rows) with locked F1/F-AXIS conditions determining verdict cell; verdict
  cell decision protocol documented; pre-registered BEFORE Phase 6 backtest. Note: this is an
  EXPLORATION (not MERGE-eligible); the verdict matrix gates are correctly framed as
  PROMISING/INERT/NEGATIVE/BLOCK cell assignment, not a portfolio MERGE decision (consistent with
  per-cohort EXPLORATION methodology per /018+/019 precedent).

- Section 9 (Library Stack Declaration): PASS — Section 9 enumerates mlfinlab/mlfinpy, pypbo,
  fracdiff, statsmodels, LightGBM, Optuna, V1_FEATURE_COLUMNS_PRUNED, validation_v1; zero
  cross-track imports (no features_v2, no features_v3, no risk_v2 imports noted — /020 has NO
  gate, removing /019's cross-track helper import). Fallback libraries not needed (same stack
  as prior cycle-3 iterations).

## Additional v1-Only Gate Checks

Section 0.6 Rotation Status VALID: confirmed (see Axis Family section above).

EDA script IS-only discipline: btc_regime_concentration.csv splits baseline IS data into H1/H2 halves
(verified Section 2.3 — IS only). Pool-anchor diagnostic uses IS monthly PnL from baseline trades.csv
IS portion (Section 2.4). No OOS data used to design the /020 intervention. PASS.

Wall-clock budget: 25 min projected with 79% margin vs 2h cap and 71+ min buffer vs 1.6h Phase 5.5
BLOCK threshold. PASS.

## Reasons (if BLOCK)
None — OVERALL: PASS.
