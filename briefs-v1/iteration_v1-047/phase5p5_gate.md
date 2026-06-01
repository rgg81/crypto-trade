# Phase 5.5 Gate — iter-v1/047 (retry)

OVERALL: BLOCK

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION

## Axis Family + Rotation Status
FAMILY: feature-family
ROTATION_STATUS: VALID — `feature-family` not in the prior 5 (labeling, model-arch,
per-cohort-specialization × labeling, bundle-substrate, methodology). The most-recent
feature-family EXPLORATION was /040 (regime_momentum_signed_5d), 6 EXPLORATIONs back —
outside the rolling-5 window. Verified against `briefs-v1/exploration_catalog.md`.

## HIGH-RISK Declaration
HIGH-RISK: NO (NORMAL-RISK) — feature ADDITION only; Optuna training objective unchanged;
training window unchanged; universe unchanged; architecture unchanged.

## LM Master Response Verification
- `briefs-v1/iteration_v1-047/lgbm_advisor.md` exists: **BLOCK** — file does not exist on
  disk and is not tracked in git. `git ls-files briefs-v1/iteration_v1-047/` returns only
  `_pre_brief_outline.md`, `phase5p5_gate.md`, `research_brief.md`. Every v1 iteration
  requires Phase 4.5 LM Master advisory BEFORE the Phase 5.5 gate can PASS.
- Brief Section 3.7 addresses each LM Master recommendation: **BLOCK** — Section 3.7
  remains placeholder ("Provisional placeholder rows; this brief revision will be updated
  post-LM-Master"). No numbered recommendations have been adopted / modified / rejected.
  This cannot be resolved until `lgbm_advisor.md` exists.

## Cadence Check
- Wall-clock budget declared ≤ 2.5h total (backtest 2h HARD + 0.5h overhead) for
  EXPLORATION: PASS
- CONFIRMATION precedent check: N/A (EXPLORATION iteration)

## Artifact Verification (inputs claimed by prompt vs actual disk state)
The prompt asserts the following artifacts are committed. Each was checked against
`git ls-files` and filesystem:

| Artifact | Claimed | Actual |
|---|---|---|
| `briefs-v1/iteration_v1-047/lgbm_advisor.md` | committed | **MISSING** — not on disk, not in git |
| `src/crypto_trade/features_v1/statistical_v1.py` | committed | **MISSING** — not in git |
| `tests/test_iteration_v1_047.py` | passing | **MISSING** — not on disk |
| `run_iteration_047.py` | committed | **MISSING** — only `old_runners/run_iteration_047.py` exists (legacy pre-refactor) |
| `analysis/iteration_v1-047/eda.py` | committed | **MISSING** — directory empty |
| `analysis/iteration_v1-047/eda.csv` (and other CSVs) | committed | **MISSING** — directory empty |

The git HEAD is unchanged at `edc0547` (the prior Phase 5.5 BLOCK gate commit). No new
commits have been added since the prior BLOCK.

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_MS = 1742774400000 (2025-03-24 UTC);
  training_months = 24; IS window < 2025-03-24; OOS window ≥ 2025-03-24; universe
  BTC/ETH/LINK/LTC/DOT unchanged.
- Section 0.5 (Iteration Type, v1): PASS — TYPE: EXPLORATION; cycle-6 EXPLORATION 2/10;
  cadence n_trials=18, --seeds 1, ENSEMBLE_SIZE=3, wall-clock ≤ 2h HARD declared.
- Section 0.6 (Architecture-Family Justification, v1-only): PASS — FAMILY: feature-family;
  ROTATION_STATUS: VALID; prior-5 table populated; one-sentence rationale present.
- Section 1 (Hypothesis): PASS — specific one-sentence hypothesis with dual numeric gate
  (top-15 importance AND IS daily Sharpe Δ ≥ +0.05 vs BASELINE_V1 +0.4767).
- Section 2 (IS-Only Evidence): BLOCK — 5 pre-Phase-6 committed artifacts enumerated in
  the brief (adf_stationarity_per_symbol.csv, distribution_stats_per_symbol.csv,
  ic_orthogonality_top5.csv, ic_orthogonality_full_44.csv, F4_F5_gate_outcomes.md) but
  NONE are present on disk or tracked in git. `analysis/iteration_v1-047/` directory is
  empty. The section also references `skew_zscore_21_definition.py` and
  `feature_columns.json` as artifacts — also absent. IS-window assertion code is present
  in brief prose but unverifiable without committed scripts.
- Section 2.5 (HIGH-RISK Axis Declaration, v1-only): PASS — NORMAL-RISK; reason stated.
- Section 3 (Proposed Changes): BLOCK (two sub-blocks):
  (a) LM Master response map (Section 3.7) is placeholder — TBD rows only.
  (b) `src/crypto_trade/features_v1/statistical_v1.py` cited as "NEW file" but not
      committed or present on disk.
- Section 4 (Expected OOS Impact / Falsifiers): PASS — F1 through F5 falsifiers
  pre-registered with numeric thresholds; DUAL gate (importance AND Sharpe); failure
  routes specified; forensic-only OOS declared (F3).
- Section 5 (Risk Mitigation): PASS — F4 ADF + F5 IC pre-launch gates; NEG-CLEAN routing;
  wall-clock kill switch; IS-calibrated thresholds with historical calibration.
- Section 6 (Risk Management Design): PASS — R1/R2/R3 inherited from BASELINE_V1 with
  explicit NO-CHANGE; F4/F5 as new pre-launch protective gates; concentration cap
  inherited.
- Section 7 (Failure-Mode Prediction, v1): PASS — verdict band priors with percentages;
  most-plausible failure scenario (NEG-INERT: stat_skew_20 informationally subsumes
  z-score form); expected metric signature table per verdict.
- Section 8 (MERGE/NO-MERGE Criteria, v1): PASS — pre-registered EXPLORATION verdict
  subtypes (PROMISING-CLEAN / PROMISING-WITH-CORRELATED-PRIMITIVE / NEG-INERT /
  NEG-CLEAN / BLOCK-PENDING-FIX); numeric thresholds locked; OOS forensic-only.
- Section 9 (Library Stack, v1): PASS — scipy ≥ 1.13 pinned; statsmodels for ADF;
  7 pre-Phase-6 artifacts enumerated verbatim; 5 post-Phase-6 artifacts enumerated.

## Reasons (BLOCK)

1. **`lgbm_advisor.md` missing (HARD BLOCK)**: `briefs-v1/iteration_v1-047/lgbm_advisor.md`
   does not exist on disk and is not tracked in git. Per v1 Phase 5.5 gate rules, the
   Phase 4.5 LM Master advisory MUST be authored and committed before Phase 5.5 can PASS.
   This is the same blocking reason as the prior gate at commit `edc0547`.

2. **Section 3.7 LM Master response map is placeholder (HARD BLOCK)**: Section 3.7
   contains only TBD rows — no LM Master recommendations have been responded to because
   the advisor does not exist. This cannot be resolved without first resolving blocker #1.

3. **Section 2 EDA artifacts not committed (BLOCK)**: The brief enumerates 5 pre-Phase-6
   EDA artifacts (adf_stationarity_per_symbol.csv, distribution_stats_per_symbol.csv,
   ic_orthogonality_top5.csv, ic_orthogonality_full_44.csv, F4_F5_gate_outcomes.md) plus
   `skew_zscore_21_definition.py` and `feature_columns.json`. None of these are on disk.
   The `analysis/iteration_v1-047/` directory is empty. IS-only numerical evidence
   (Section 2) requires committed scripts and CSVs — prose enumeration without committed
   artifacts is NOT evidence.

4. **`src/crypto_trade/features_v1/statistical_v1.py` not committed (BLOCK)**: Brief
   Section 3.1 specifies this as a NEW file, but it does not exist on disk or in git.
   (Note: the Engineer implements src/ changes in Phase 6, AFTER Phase 5.5 PASS — this
   is not a gate blocker in isolation. However the brief's Section 2.5 and Section 3.6
   test requirements reference this file, and the test file `tests/test_iteration_v1_047.py`
   also does not exist. These are Phase 6 artifacts and do not independently block Phase
   5.5, but they confirm no implementation work has been done.)

5. **`tests/test_iteration_v1_047.py` not present (informational — Phase 6 artifact)**:
   The prompt claims pytest is passing, but the test file does not exist. This is a Phase 6
   artifact; it does not independently block Phase 5.5, but it is inconsistent with the
   prompt's claim.

6. **`run_iteration_047.py` not present (informational — Phase 6 artifact)**: The prompt
   claims the runner is committed, but only `old_runners/run_iteration_047.py` exists
   (the legacy pre-refactor runner for the v1-pre-refactor track). The v1-refactored
   runner `run_iteration_047.py` at the worktree root does not exist. Phase 6 artifact;
   does not independently block Phase 5.5.

## Path Forward for QR

The hard blockers are items 1–3. Items 4–6 are Phase 6 artifacts (not Phase 5.5 blockers)
but are flagged because the prompt incorrectly asserted they are committed.

1. Dispatch LM Master (Phase 4.5) with `research_brief.md` for iter-v1/047.
2. Commit `briefs-v1/iteration_v1-047/lgbm_advisor.md` with numbered recommendations.
3. Update `research_brief.md` Section 3.7 with per-recommendation adoption matrix
   (adopted / modified / rejected + reason for each numbered recommendation).
4. Author and commit EDA scripts + CSVs to `analysis/iteration_v1-047/`:
   - `eda.py` (or `skew_zscore_21_definition.py` per Section 9.1 naming)
   - `adf_stationarity_per_symbol.csv`
   - `distribution_stats_per_symbol.csv`
   - `ic_orthogonality_top5.csv`
   - `ic_orthogonality_full_44.csv`
   - `F4_F5_gate_outcomes.md`
   - `feature_columns.json`
5. Re-submit to Phase 5.5 gate.

DO NOT launch Phase 6 implementation until Phase 5.5 gate returns OVERALL=PASS.
