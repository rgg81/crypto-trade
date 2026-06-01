# Phase 5.5 Gate — iter-v1/046

OVERALL: BLOCK

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION

## Axis Family + Rotation Status
FAMILY: methodology (substrate re-composition / IS-only partition-solve)
ROTATION_STATUS: VALID — `methodology` is NOT present in the prior 5 EXPLORATIONs
(prior 5: /039 per-cohort×labeling, /040 feature-family, /041 labeling, /042 model-arch, /043 per-cohort-specialization×labeling)

## HIGH-RISK Declaration
HIGH-RISK: NO (NORMAL-RISK) — no Optuna training-objective domain change; no src/ changes; CSV-replay only

## LM Master Response Verification
- briefs-v1/iteration_v1-046/lgbm_advisor.md exists: PASS
- Brief Section 3 addresses each LM Master recommendation: PASS
  - R1 (HP-region diversity + IS sample-size audit): ADOPTED (advisory; top-3 emission + §11.D audit trail)
  - R2 (per-coin multiple-comparison correction; deflated F1 floor): PARTIALLY ADOPTED (deflated F1 floor adopted; per-component deflation reported)
  - R3 (3-part verification recipe: data-loaded + date-cutoff + hide-test): ADOPTED
  - Flag A (IS-overfit-on-a-different-axis): ACKNOWLEDGED in Section 4 F1
  - Flag B (IS-only OOS may be worse; not a /046 failure): ADOPTED in Section 4 F4 + Critic constraint language
  - Flag C (tiebreaker IS_n_trades desc not asc): ADOPTED in Section 3.1 step 4
  - Flag D (effective-weight calculation documented): ADOPTED in Section 3.5

## Cadence Check
- Wall-clock budget declared: <30 min (EXPLORATION ≤ 2h): PASS
- CONFIRMATION cadence N/A at cycle-6 EXPLORATION 1/10: PASS

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE = 2025-03-24, training_months = 24, IS/OOS windows stated, IS-only filter assertion documented
- Section 0.5 (Iteration Type): PASS — TYPE: EXPLORATION, <30 min wall-clock, cycle-6 1/10 declared
- Section 0.6 (Architecture-Family Justification): PASS — methodology family, prior 5 EXPLORATIONs listed with families, VALID rotation status, one-sentence rationale
- Section 1 (Hypothesis): PASS — specific binary hypothesis (COINCIDES vs DIVERGES), both branches defined with clear routing to /047
- Section 2 (IS-Only Evidence): PASS — IS-Sharpe distribution from committed partition_solve_v2.py; IS-only filter assertion at load; committed script: analysis/iteration_v1-046/partition_solve_v2.py; is_only_substrate.csv committed
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — NORMAL-RISK declared with reason
- Section 3 (Proposed Changes): BLOCK — see Reasons below
- Section 4 (Expected OOS Impact): PASS — F-AXIS #1–#5 falsifiers registered; F1 upgraded with deflated floor per LM Master Rec 2; OOS explicitly forensic-only
- Section 5 (Risk Mitigation): PASS — methodology-layer R1–R6 registered; look-ahead audit; embargo inheritance documented
- Section 6 (Risk Management Design): PASS — R1-R6 methodology gates declared; IS-only filter as R3; regime-breadth coverage noted; forensic OOS not used as gate
- Section 7 (Failure-Mode Prediction): PASS — verdict band priors tabulated; most-plausible BLOCK-PENDING-FIX, NULL-METHODOLOGY-FIX, and PROMISING-DIVERGENCE scenarios described in detail
- Section 8 (MERGE/NO-MERGE Criteria): PASS — pre-registered IS-regime Pareto criterion vs BASELINE_V1 (F-AXIS #4); forensic ALT_1 comparison schema; per-coin top-1 match table pre-registered
- Section 9 (Library Stack Declaration): PASS — pandas, numpy, scipy.stats.spearmanr, pathlib, csv, hashlib; mlfinlab/pypbo/optuna/lightgbm explicitly NOT invoked at /046

## Reasons (if BLOCK)
- **Section 3 (Proposed Changes) — Score Formula Mismatch: Brief vs Code**

  The research brief specifies the IS-only scoring formula as `score_is = 0.6 * IS_Sharpe + 0.4 * (IS_n_trades / 100)` throughout:
  - Section 3.1 step 2: "IS_n_trades_norm = IS_n_trades / 100 (matching /045's trade-norm convention)"
  - Section 3.1 step 2: "score_is = 0.6 * IS_Sharpe + 0.4 * IS_n_trades_norm"
  - Section 3.1 step 6 (output schema): column named `IS_n_trades_norm`
  - Section 4 F5 (process integrity falsifier): "Compute score_is = 0.6 · IS_Sharpe + 0.4 · IS_n_trades / 100"
  - Section 3.5 (Flag D response): "`IS_n_trades/100` ranges roughly [0.2, 1.5]"

  The committed `analysis/iteration_v1-046/partition_solve_v2.py` implements:
  ```python
  def _score(is_sharpe: float, is_n_trades: int) -> float:
      return 0.6 * is_sharpe + 0.4 * (is_n_trades / 250.0)
  ```
  The normalization denominator is **250, not 100**. The commit message confirms this: "Implements IS-only scoring formula (0.6*IS_Sharpe + 0.4*IS_n/250)."

  This is a hypothesis-implementation misalignment. The brief says `/100`; the code ships `/250`. The committed output `is_only_substrate.csv` reflects the `/250` computation, whose results may differ from what the brief-specified `/100` formula would produce. The Critic cannot evaluate the /046 test (COINCIDES vs DIVERGES) without knowing which formula was actually intended and which substrate the /046 brief is asserting.

  The brief's Score formula documentation also includes effective-weight range estimates calibrated to `/100` ("`IS_n_trades/100` ranges roughly [0.2, 1.5]" for 20-150 IS trades) — at `/250` those same 20-150 trades produce [0.08, 0.60] normalized, materially changing the effective weight balance.

  Additionally, the brief's Section 3.1 step 6 prescribes the output file as `partition_solve_v2.csv`, but the committed script emits `is_only_substrate.csv`. This is a minor naming discrepancy but contributes to brief-code misalignment.

  **Required fix (QR):** update the brief to document the `/250` denominator as the intended formula (and update Section 3.5 Flag D effective-weight range estimates to match), OR update `partition_solve_v2.py` to use `/100` as the brief specifies and re-run to regenerate `is_only_substrate.csv`. Either resolution is acceptable, but brief and code MUST match before Phase 6.0 Critic pre-flight. Additionally clarify whether the output file name `is_only_substrate.csv` is the intended name or whether `partition_solve_v2.csv` should also be emitted.

## Committed Artifact Status
- analysis/iteration_v1-046/partition_solve_v2.py: COMMITTED (e97fdf3)
- analysis/iteration_v1-046/is_only_substrate.csv: COMMITTED (e97fdf3)
- analysis/iteration_v1-046/weight_calibration.py: COMMITTED (e97fdf3)
- analysis/iteration_v1-046/bundle_weights.csv: COMMITTED (e97fdf3)
- run_iteration_046.py: COMMITTED (8d95540)
- tests/test_iteration_v1_046.py: COMMITTED (8d95540)
- briefs-v1/iteration_v1-046/research_brief.md: ON DISK (untracked — not yet committed)
- briefs-v1/iteration_v1-046/lgbm_advisor.md: ON DISK (untracked — not yet committed)

Note: research_brief.md and lgbm_advisor.md being untracked is acceptable at Phase 5.5 gate time; they will be committed along with this gate file. The blocking reason is the score formula mismatch between the committed code (IS_n_trades / 250) and the brief specification (IS_n_trades / 100), which must be reconciled before Phase 6.0.
