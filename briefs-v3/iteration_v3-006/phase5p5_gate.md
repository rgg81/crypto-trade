# Phase 5.5 Gate — iter-v3/006

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24` both declared IMMUTABLE; `ensemble_size = 5` UNCHANGED; derivation function replaces hardcoded constant; IS/OOS windows stated in absolute dates.
- Section 1 (Hypothesis): PASS — single sentence; specific testable target (`per-seed Sharpe std > 0` under `--seeds 2`); falsifiers locked in §4.3; directly motivated by iter-v3/005 Critic BLOCK structural finding.
- Section 2 (IS-Only Evidence): PASS — committed script: `analysis/iteration_v3-006/seed_derivation_demo.py` at SHA `03b6004` (2026-05-06 00:18:47), which predates brief SHA `76f3999`. All 5 output artifacts exist (`derived_ensembles.csv`, `overlap_matrix.csv`, `legacy_check.csv`, `summary.json`, `synthesis.md`). Tables §2.1–2.4 inline with numerical results. 10/10 off-diagonal pairs zero overlap; 0/5 legacy reproductions.
- Section 3 (Proposed Changes): PASS — symbols scoped to BCH-only (§3.1); labeling, features, risk gates UNCHANGED (§3.2–3.4); 3 sub-fixes enumerated with status + verifier commands (§3.5); 10-row file-artifact reconciliation table with executable verifier commands (§3.6); §3.7 explicitly excludes 5-seed and 10-seed runs from this iteration's scope; §3.8 inheritance plan with 6 precondition verifiers (all confirmed: `validation_v3.py` ≥1 commit, `run_baseline_v3.py` ≥1 commit, all 3 test files exist, 35/35 tests pass).
- Section 4 (Expected OOS Impact): PASS — predicted metric table with 4 falsifiers (§4.3); methodology-only MERGE pathway declared (§4.4); headline metrics explicitly deferred to iter-v3/008; point estimates deliberately withheld per sound methodology reasoning.
- Section 5 (Risk Mitigation): PASS — 3 new structural safeguards (§5.1: per-seed Sharpe std>0 verifier, pre-flight 6 adversarial tests, wall-clock cap); 3 methodology-pipeline safeguards (§5.2); explicit statement that no new model-level risks are introduced (§5.3).
- Section 6 (Risk Management Design): PASS — 7-primitive table with fire-rate predictions and regime coverage for all primitives; concentration N/A declared by design for single-symbol scope with restoration planned for iter-v3/007.
- Section 7 (Failure-Mode Prediction): PASS — 5 predictions present; §7's 3 process-level predictions (P1, P2, P3) satisfy the "≥3 process-level" gate requirement per iter-v3/003 lesson #3 discipline; each has explicit detection signal and mitigation; Bayesian calibration probabilities assigned.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 10 criteria locked before backtest; all methodology-only; headline metrics (IS/OOS Sharpe, trade counts, concentration, DSR, etc.) explicitly deferred to iter-v3/008; criterion 4 (`per-seed Sharpe std > 0`) named as the central test; §3.7 + §8.9 confirm NO 5-seed and NO 10-seed runs this iteration; NO-MERGE conditions enumerated.
- Section 9 (Library Stack): PASS — 8 packages declared with versions, licenses, and usage; no new external deps; aggregator strategy declared UNCHANGED; reproducibility stamp specifies Phase 6 engineering report contents.

## Pre-Phase-6 Verifier Results

| Verifier | Result |
|---|---|
| `uv run pytest tests/strategies/ml/test_outer_seed_propagation.py -v` | 6/6 PASS (59s) |
| `uv run pytest tests/strategies/ml/ -v` | 35/35 PASS |
| `grep -E "LEGACY_ENSEMBLE_SEEDS.*42.*123.*456.*789.*1001" run_baseline_v3.py` | 1 match — PASS |
| Analysis outputs: `derived_ensembles.csv`, `overlap_matrix.csv`, `legacy_check.csv`, `summary.json`, `synthesis.md` | ALL EXIST |
| SHA `03b6004` predates brief SHA `76f3999` | CONFIRMED (03b6004 = 2026-05-06 00:18:47, brief committed after) |
| SHA `9314db4` predates SHA `03b6004` | CONFIRMED (9314db4 = 2026-05-06 00:11:29) |
| `git log --oneline -- src/crypto_trade/strategies/ml/validation_v3.py \| wc -l` ≥ 1 | 3 — PASS |
| `git log --oneline -- run_baseline_v3.py \| wc -l` ≥ 1 | 5 — PASS |
| `test_outer_seed_propagation.py` exists | PASS |
| `test_per_cell_pbo_synthetic.py` exists | PASS |
| `test_ensemble_seed_propagation.py` exists | PASS |

## Scope Confirmation

- 5-seed run: EXCLUDED from iter-v3/006 (§3.7 + §8.9 both confirm). Scoped to iter-v3/007.
- 10-seed run: EXCLUDED from iter-v3/006 (§3.7 + §8.9 both confirm). Scoped to iter-v3/008.
- Meta-labeling: EXCLUDED (§3.7).
- Universe change: TEMPORARY BCH-only scoping (§3.1), not permanent.

## Gate Decision

OVERALL=PASS. No missing sections, no empty reconciliation cells, no ambiguous scope. Reconciliation table §3.6 has 10 rows each with an executable verifier command. Central test (criterion 4, §3.6 row 5) is a strict numerical assertion: `df['monthly_sharpe'].std() > 0`. The 5/10 criteria verifiable pre-Phase-6 all pass. Remaining 5 require Phase 6 backtest outputs and are well-defined. Proceed to Phase 6.
