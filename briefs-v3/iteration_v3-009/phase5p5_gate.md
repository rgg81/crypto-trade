# Phase 5.5 Gate — iter-v3/009

OVERALL: PASS

---

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` declared UNCHANGED; `OOS_CUTOFF_MS = 1742774400000` consistent; `ENSEMBLE_SIZE = 1` and `n_trials = 10` documented as set by `--exploration` flag.
- Section 0.5 (Iteration Type Declaration): PASS — `TYPE: EXPLORATION` declared; wall-clock budget `< 30 min` (hard cap 2h) stated; single-axis variation (features) stated; cadence position declared as EXPLORATION #2 of 10 required; explicit "NEVER updates BASELINE_V3.md".
- Section 1 (Hypothesis): PASS — one sentence; testable target (IS Sharpe ≥ +0.20 within ±0.05 of iter-v3/007's +0.2241); falsifiers locked in §4.3.
- Section 2 (IS-Only Evidence): PASS — committed analysis script `analysis/iteration_v3-009/top_13_validation.py` at SHA `565e0ec` (2026-05-06 15:41:10) before brief SHA `96ec4d5` (2026-05-06 15:44:48); outputs `top_13_features.csv` + `synthesis.md` committed alongside; IC evidence reuses iter-v3/007 and iter-v3/008 scripts (IS-only inputs only — no OOS contact); 4 numeric quantities tabulated in §2.1.
- Section 3 (Proposed Changes): PASS — symbols UNCHANGED (4-symbol v3 universe); labeling UNCHANGED; features: 13-tuple already set by inherited SHA `56b8f8b` (runtime-verified: `len=13`, `vwap_dev_50 absent`); risk gates UNCHANGED; Section 3.5 sub-fix table (3 rows) covers only `ITERATION_LABEL` update; Section 3.6 reconciliation table has 10 rows each with an executable verifier command; Section 3.7 confirms single-axis; Section 3.8 lists inherited commits with verifier commands.
- Section 4 (Expected OOS Impact): PASS — predicted IS Sharpe range [+0.18, +0.28]; median +0.22; 4 falsifiers; EXPLORATION pathway table covering PROMISING / NEGATIVE / BLOCK verdicts. Correctly noted that EXPLORATION headline metrics are guidance, not gate-blocking.
- Section 5 (Risk Mitigation): PASS — 3 cadence-discipline structural safeguards (2h cap, single-axis, no BASELINE update); 3 methodology-pipeline safeguards (35 adversarial tests, reconciliation table, pre-flight len check).
- Section 6 (Risk Management Design): PASS — 7-primitive table identical to iter-v3/006-008; gate-vs-feature-column independence explicitly verified (gates read from full 34-feature parquet, not from `V3_FEATURE_COLUMNS`; `atr_pct_rank_200` added to `needed` list at SHA `849c4a6`); `vwap_dev_50` confirmed NOT a gate input.
- Section 7 (Failure-Mode Prediction): PASS — 6 predictions total; 3 are explicitly process-level (P1: setup drift, P=5%; P2: wall-clock overshoot, P=5%; P3: importance rank shift, P=10%); 3 model-level (P4 predicted-band PROMISING, P5 undershoot NEGATIVE, P6 overshoot PROMISING); satisfies ≥3 process-level requirement.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 10 EXPLORATION-PROMISING criteria table; EXPLORATION-NEGATIVE condition; BLOCK condition; explicit "NEVER updates BASELINE_V3.md"; correct framing that no MERGE pathway exists for EXPLORATION type.
- Section 9 (Library Stack): PASS — 8 packages listed with license and usage; no new external deps; aggregator strategy declared unchanged; reproducibility stamp specifies 9 required engineering report fields.

---

## Cadence Check

- TYPE: EXPLORATION declared in Section 0.5: PASS
- Wall-clock budget ≤ 2h declared in Section 0.5: PASS — `< 30 min` target, `2h` hard cap, both stated.
- Section 3.5 changes ONE axis (features only): PASS — the only axis changed is features (drop `vwap_dev_50`; code already landed in inherited SHA `56b8f8b`; Section 3.7 confirms "byte-for-byte unchanged" on all other axes).
- `--seeds 1` for EXPLORATION: PASS — `ENSEMBLE_SIZE = 1` set by `--exploration`; `--seeds 1` in Phase 6 invocation in §3.5 row 3 and §3.6 row 9 verifier.
- `exploration_catalog.md` exists with ≥ 1 entry: PASS — file exists at `briefs-v3/exploration_catalog.md`; iter-v3/007 row present as entry #1 (EXPLORATION-PROMISING, 2026-05-06). iter-v3/009 is EXPLORATION #2 — no CONFIRMATION precondition required; 10:1 ratio constraint requires 9 more after iter-v3/009 before any CONFIRMATION can launch.

---

## Section 3.6 Reconciliation Cells — Pre-Phase-6 Verifiable Items

Items 1 and 2 are executable NOW (pre-Phase 6). Items 3-10 are executable post-Phase 6.

| # | Verifier status (pre-Phase 6) | Outcome |
|---|---|---|
| 1 | `uv run python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13"` | PASS — live verified: `len=13` |
| 2 | `uv run python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert 'vwap_dev_50' not in V3_FEATURE_COLUMNS"` | PASS — live verified: `vwap_dev_50 absent: True` |
| 3 | `grep -E 'ITERATION_LABEL.*=.*"v3-009"' run_baseline_v3.py` | PENDING — currently `"v3-008"`; Phase 6 engineer task (Section 3.5 row 1). NOT a gate BLOCK — this is the ONLY code change Phase 6 must make. |
| 4–10 | Post-Phase-6 verifiers (comparison.csv, IS Sharpe, tests, wall-clock, symbols, --exploration, pareto_front.csv) | PENDING — Phase 6 execution required |

---

## Analysis Script Chronology

- `analysis/iteration_v3-009/top_13_validation.py` committed at SHA `565e0ec` — 2026-05-06 15:41:10
- `briefs-v3/iteration_v3-009/research_brief.md` committed at SHA `96ec4d5` — 2026-05-06 15:44:48
- Script precedes brief by 3 min 38 s. Reproducibility requirement: PASS.

---

## Reasons

None — OVERALL = PASS. No blocking gaps found.

**Note for Phase 6 Engineer**: The only required code change is updating `ITERATION_LABEL` from `"v3-008"` to `"v3-009"` in `run_baseline_v3.py` (Section 3.5 row 1). All other changes are inherited from SHA `56b8f8b`. Run the 10 Section 3.6 verifiers post-backtest to confirm gate compliance. Wall-clock hard cap is 2h; target is 30 min on `--exploration --seeds 1 --n-trials 10`.
