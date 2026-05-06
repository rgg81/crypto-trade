# Phase 5.5 Gate — iter-v3/010

OVERALL: PASS

## Cadence-Discipline Checks

| Check | Status | Evidence |
|---|---|---|
| TYPE=EXPLORATION declared in Section 0.5 | PASS | "TYPE: EXPLORATION" present; "NEVER updates BASELINE_V3.md" explicit |
| Wall-clock budget ≤ 2h (target < 30 min) | PASS | Section 0.5 + §4.2: "target < 30 min, hard cap 2h" |
| Single-axis variation: labeling ONLY | PASS | §3.7: "feature set, model architecture, risk gates, CPCV, walk-forward window byte-for-byte unchanged" |
| `--seeds 1` (--exploration flag) | PASS | §3.5 sub-fix #6: "uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 10" |
| exploration_catalog.md exists | PASS | File present at briefs-v3/exploration_catalog.md |
| exploration_catalog.md has ≥2 prior EXPLORATION rows | PASS | 2 rows: iter-v3/007 (EXPLORATION-PROMISING), iter-v3/009 (EXPLORATION-NEGATIVE) |
| iter-v3/010 is EXPLORATION #3 (non-features axis per Critic Rec 1) | PASS | Labeling axis selected; §0.5 cites Critic FINAL Rec 1 SHA 1bc828f |

## Per-Section Status

| Section | Status | Notes |
|---|---|---|
| Section 0 — Data Split | PASS | OOS_CUTOFF_DATE=2025-03-24, training_months=24 declared unchanged; ENSEMBLE_SIZE=1 / colsample=1.0 / n_trials=10 set by --exploration |
| Section 0.5 — Iteration Type | PASS | TYPE: EXPLORATION; cadence count declared (EXPLORATION #3 of 10); explicit "NEVER updates BASELINE_V3.md"; non-features axis justified via Critic FINAL Rec 1 |
| Section 1 — Hypothesis | PASS | One sentence; specific testable target IS Sharpe ≥ +0.10 (Falsifier 1); not vague |
| Section 2 — IS-Only Evidence | PASS | Script analysis/iteration_v3-010/atr_multiplier_demo.py committed at SHA 80332c1 (2026-05-06 16:26:03); brief committed at SHA fdb17b1 (2026-05-06 16:30:07) — script PRECEDES brief by 4 min. Script reads IS-only trades.csv. Three outputs committed: atr_multiplier_demo.py, expected_label_shift.csv, synthesis.md. Per-symbol baseline table (§2.1) and projected shift table (§2.2) present with concrete numbers. |
| Section 3 — Proposed Changes | PASS | Symbols unchanged (4 v3 universe); labeling changed single-axis (tp 2.9→2.0, sl 1.45→1.0, 2:1 ratio preserved); features unchanged (13, vwap_dev_50 absent); risk gates unchanged. §3.5 sub-fix decomposition (6 sub-fixes). §3.6 reconciliation table: 10 rows, all cells filled with executable verifier commands. |
| Section 4 — Expected OOS Impact | PASS | Predicted IS Sharpe range [-0.20, +0.40] with median +0.10; 4 falsifiers in §4.3 (Falsifier 1 IS Sharpe threshold, Falsifier 2 trade-count floor, Falsifier 3 wall-clock process, process pre-flight); EXPLORATION outcome table in §4.4 |
| Section 5 — Risk Mitigation | PASS | 3 cadence-discipline structural safeguards (§5.1); 4 methodology-pipeline safeguards (§5.2); zero new model-level risks introduced (§5.3) |
| Section 6 — Risk Management Design | PASS | 7-primitive table identical to iter-v3/006-009; fire-rate predictions and regime coverage present; gate-vs-label independence explicitly verified |
| Section 7 — Failure-Mode Prediction | PASS | 6 predictions: P1, P2, P3 are PROCESS-level (≥3 required), P4–P6 are model-level; calibrated probabilities (50/30/15/5/10/5%); calibration-miss doctrine applied from iter-v3/009 lesson |
| Section 8 — Pre-Registered Criteria | PASS | 10 EXPLORATION-PROMISING criteria locked pre-backtest; EXPLORATION-NEGATIVE pathway defined; BLOCK pathway defined; "NEVER updates BASELINE_V3.md" explicit; discretionary judgment paragraph present |
| Section 9 — Library Stack | PASS | 8 packages declared (numpy, scipy, statsmodels, scikit-learn, lightgbm, pytest, pandas, pyarrow); no new deps; reproducibility stamp requirements enumerated; aggregator strategy unchanged |

## Additional Verifications Performed

| Check | Result |
|---|---|
| V3_FEATURE_COLUMNS len == 13 | PASS — `uv run python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13"` exits 0 |
| vwap_dev_50 not in V3_FEATURE_COLUMNS | PASS — confirmed by above import check |
| 35/35 adversarial tests | PASS — `uv run pytest tests/strategies/ml/ -v` → 35 passed in 58.91s |
| iter-v3/008 stale references in _verify_feature_columns docstring | NOTED — 3 occurrences remain in runner (lines 182, 184, 193); this is a PRE-Phase-6 state. §3.5 sub-fix #4 and §3.6 row 5 specify the docstring fix as a Phase 6 deliverable. Phase 5.5 does not require Phase 6 changes to be applied; this is NOT a BLOCK. |
| Analysis script reads IS-only data | PASS — script reads reports-v3/iteration_v3-009/in_sample/trades.csv (no OOS contact) |
| exploration_catalog.md count accuracy | PASS — catalog shows 2 rows and states "2 of 10 required"; consistent with iter-v3/010 being EXPLORATION #3 |

## Reasons for PASS

All 11 mandatory sections (0, 0.5, 1–9) are present and complete. The Phase 5.5 timestamp ordering requirement is satisfied: analysis script SHA 80332c1 (16:26:03) precedes brief SHA fdb17b1 (16:30:07). The cadence-discipline checks pass: TYPE=EXPLORATION declared, single-axis (labeling only), `--seeds 1` mandated, catalog has 2 prior rows. Section 7 contains 3 process-level predictions (P1, P2, P3) satisfying the ≥3 requirement. Section 3.6 reconciliation table has 10 rows with no empty verifier cells. The stale iter-v3/008 docstring references in the runner are a known pre-Phase-6 state documented as sub-fix #4 and are NOT a gate blocker.

Phase 6 may proceed.
