# Phase 5.5 Gate — iter-v1/046 (RETRY after score-formula fix)

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION

## Axis Family + Rotation Status
FAMILY: methodology (substrate re-composition / IS-only partition-solve)
ROTATION_STATUS: VALID — `methodology` is NOT present in the prior 5 EXPLORATIONs.

Prior 5 EXPLORATIONs (from briefs-v1/exploration_catalog.md rows 72-76):
| Iter | Axis family |
|---|---|
| iter-v1/039 | per-cohort × labeling COMBO (Sortino × LINK+DOT trend-scan hybrid) |
| iter-v1/040 | feature-family (composed `regime_momentum_signed_5d` swap) |
| iter-v1/041 | labeling (atr_tp/sl width tighten 2.9→1.5 / 1.45→0.75) |
| iter-v1/042 | model-arch (XGBoost head-to-head vs LightGBM) |
| iter-v1/043 | per-cohort-specialization × labeling COMBO (LINK-only trend-scan) |

`methodology` does not appear in any of the prior 5. Axis Rotation Discipline SATISFIED.

## HIGH-RISK Declaration
HIGH-RISK: NO (NORMAL-RISK) — no Optuna training-objective domain change; no src/ changes;
CSV-replay methodology-only iteration. No model fit; no Optuna call.

## LM Master Response Verification
- briefs-v1/iteration_v1-046/lgbm_advisor.md exists: PASS
- Brief Section 3.5 addresses each LM Master recommendation: PASS
  - R1 (HP-region diversity + IS sample-size audit): ADOPTED — top-3 per-coin emission + §11.D audit trail
  - R2 (per-coin multiple-comparison correction; deflated F1 floor): PARTIALLY ADOPTED — deflated F1 floor adopted (+0.50 deflated = +0.86 raw); per-component deflation reported in partition_solve_v2.csv diagnostic columns
  - R3 (3-part verification recipe: data-loaded + date-cutoff + hide-test): ADOPTED — §4 F5 extended to 3-sub-check functional-invariance proof
  - Flag A (IS-overfit-on-a-different-axis): ACKNOWLEDGED in Section 4 F1
  - Flag B (IS-only OOS may be worse; not a /046 failure): ADOPTED in Section 4 F4 + Critic constraint language (binding at Phase 7.5)
  - Flag C (tiebreaker IS_n_trades desc not asc): ADOPTED in Section 3.1 step 4 (tiebreaker FLIPPED)
  - Flag D (effective-weight calculation documented): ADOPTED in Section 3.5 — IS_n_trades/250 ranges [0.08, 0.60]; effective trade-count weight 8-15%

## Cadence Check
- Wall-clock budget declared: <30 min (EXPLORATION ≤ 2h cap): PASS
- CONFIRMATION cadence check N/A — cycle-6 EXPLORATION 1/10: PASS

## Score Formula Verification (Primary Retry Focus)
- brief Section 3.1 step 2: `IS_n_trades_norm = IS_n_trades / 250` — PASS (matches /250)
- brief Section 2.2 table header: `IS_n_trades_norm (n/250)` — PASS
- brief Section 3.5 Flag D effective-weight ranges: [0.08, 0.60] for 20-150 trades — PASS (consistent with /250)
- brief Section 4 F5: `score_is = 0.6 · IS_Sharpe + 0.4 · IS_n_trades / 250` — PASS
- analysis/iteration_v1-046/partition_solve_v2.py line 142: `return 0.6 * is_sharpe + 0.4 * (is_n_trades / 250.0)` — PASS
- Remaining /100 references in brief: ONLY historical /045 composite score context (`0.5·OOS_Sharpe + 0.3·IS_Sharpe + 0.2·OOS_n_trades/100`) — NOT the /046 score formula. PASS
- Brief and script: bit-consistent at /250. PASS

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE = 2025-03-24, training_months = 24, IS/OOS windows stated, IS-only filter assertion `close_time < OOS_CUTOFF_MS = 1742774400000` documented; both sacred constants unchanged
- Section 0.5 (Iteration Type): PASS — TYPE: EXPLORATION, <30 min wall-clock, cycle-6 1/10 declared, cadence requirement N/A
- Section 0.6 (Architecture-Family Justification): PASS — `methodology` family declared; prior 5 EXPLORATIONs tabulated with distinct families; ROTATION_STATUS=VALID confirmed; one-sentence rationale present
- Section 1 (Hypothesis): PASS — specific binary hypothesis (COINCIDES vs DIVERGES ≥3/5); both branches defined with clear routing logic to /047; falsifiers F2/F3/F4 pre-registered
- Section 2 (IS-Only Evidence): PASS — IS-Sharpe distribution from committed analysis/iteration_v1-046/partition_solve_v2.py; IS-only filter assertion at load; pre-EDA inventory per-coin coverage stated; committed scripts: analysis/iteration_v1-046/partition_solve_v2.py (commit e97fdf3) + is_only_substrate.csv (commit e97fdf3)
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — NORMAL-RISK declared; reason: no Optuna/LightGBM dispatch; CSV-replay only
- Section 3 (Proposed Changes): PASS — score formula mismatch RESOLVED: brief updated to IS_n_trades / 250 in Sections 2.2, 3.1, 3.5 Flag D, and 4 F5; matches partition_solve_v2.py implementation; LM Master R1/R2/R3 + Flags A-D all addressed with adopted/partially-adopted/acknowledged status
- Section 4 (Expected OOS Impact): PASS — F-AXIS #1–#5 falsifiers pre-registered; F1 upgraded with deflated floor per LM Master Rec 2; OOS explicitly forensic-only (Critic constraint binding); falsifier summary table present
- Section 5 (Risk Mitigation): PASS — R1-R6 methodology-layer gates; look-ahead audit; embargo inheritance from source iterations; reproducibility checksums declared
- Section 6 (Risk Management Design): PASS — R1-R6 methodology gates declared; IS-only filter as R3; per-coin sample-size floor (IS_n_trades ≥ 20) as R5; forensic OOS declared not used as gate (R6)
- Section 7 (Failure-Mode Prediction): PASS — verdict band priors tabulated (PROMISING-DIVERGENCE 45% modal, PROMISING-PARTIAL 20%, NULL-METHODOLOGY-FIX 15%, PROMISING-COINCIDENCE 10%, BLOCK-PENDING-FIX 5%); most-plausible BLOCK-PENDING-FIX, NULL-METHODOLOGY-FIX, and PROMISING-DIVERGENCE scenarios described in detail
- Section 8 (MERGE/NO-MERGE Criteria): PASS — pre-registered IS-regime Pareto criterion vs BASELINE_V1 (F-AXIS #4, relaxed); forensic ALT_1 comparison schema; per-coin top-1 match table pre-registered; Critic constraint on OOS-not-a-falsifier binding
- Section 9 (Library Stack Declaration): PASS — pandas, numpy, scipy.stats.spearmanr, pathlib, csv, hashlib (all existing pinning); mlfinlab/pypbo/optuna/lightgbm explicitly NOT invoked at /046

## Committed Artifact Status
- analysis/iteration_v1-046/partition_solve_v2.py: COMMITTED (e97fdf3)
- analysis/iteration_v1-046/is_only_substrate.csv: COMMITTED (e97fdf3)
- analysis/iteration_v1-046/weight_calibration.py: COMMITTED (e97fdf3)
- analysis/iteration_v1-046/bundle_weights.csv: COMMITTED (e97fdf3)
- run_iteration_046.py: COMMITTED (8d95540)
- tests/test_iteration_v1_046.py: COMMITTED (8d95540)
- briefs-v1/iteration_v1-046/research_brief.md: COMMITTED (f65b90e — score formula fix)
- briefs-v1/iteration_v1-046/lgbm_advisor.md: COMMITTED (f65b90e — score formula fix)
- briefs-v1/iteration_v1-046/phase5p5_gate.md: THIS FILE (retry gate)

## Resolution Log
- **BLOCK (6ded3a9):** Section 3 score formula mismatch — brief used `IS_n_trades / 100`; script used `IS_n_trades / 250`.
- **FIX (f65b90e):** Brief updated to `IS_n_trades / 250` in Sections 2.2, 3.1, 3.5 Flag D, and 4 F5. Script unchanged (was already correct).
- **RETRY PASS (this gate):** All sections verified consistent. Score formula matches across brief + script. No remaining blockers.
