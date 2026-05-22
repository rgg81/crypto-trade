# Phase 5.5 Gate — iter-v3/003

OVERALL: PASS

## Per-Section Status
- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`, `ensemble_seeds = [42, 123, 456, 789, 1001]` declared and confirmed immutable; IS/OOS windows stated in absolute dates; CPCV N=10, k=2, 45 paths, purge gap=88 candles all explicit; sacred constants unchanged from iter-v3/002
- Section 1 (Hypothesis): PASS — one sentence; specific and testable ("per-Optuna-trial OOF return persistence produces a (45, 50) path matrix causing `pbo_from_cpcv` to return a number in [0.0, 1.0], not NaN"); falsifier in §4.2 locks the acceptance criterion before backtest
- Section 2 (IS-Only Numerical Evidence): PASS — committed script: `analysis/iteration_v3-003/pbo_strategy_axis_demo.py` at SHA `9294855` (predates brief SHA `1c18760`); 3 output files committed at same SHA (`pbo_strategy_axis.csv`, `persistence_schema.csv`, `synthesis.md`); inputs use IS-only data (iter-v3/002 IS-window CPCV paths); quantitative tables in §2.1 with 9 rows across 3 regimes; no category-matching
- Section 3 (Proposed Changes): PASS
  - 3.1 Symbols UNCHANGED: BCH, MKR, LDO, TRX retained; V3_EXCLUDED intersection confirmed empty
  - 3.2 Labeling UNCHANGED: triple-barrier params, timeout, purge gap all inherited from iter-v3/002
  - 3.3 Features UNCHANGED: V3_FEATURE_COLUMNS (34 cols, d=0.4 fracdiff) unchanged; no cluster-importance check needed
  - 3.4 Risk gates UNCHANGED: v2 5-gate + BTC trend filter; R1/R2/R3 still OFF
  - 3.5 Single-change discipline: PASS — one architectural change decomposed into 6 atomic sub-fixes (1a, 1b, 1c, 1d, 2, 3), each with spec + code path + file artifact
  - 3.6 File-artifact reconciliation table: PASS — all 11 rows have executable verifier commands in the right column; no prose-only cells (row 11 fix confirmed: `uv run pytest tests/strategies/ml/test_oof_persistence.py -v` exits 0)
  - 3.6.1 Adversarial test specification: PASS — 4-clause spec ((a)–(d)) present adjacent to table; the 4 clauses give the Engineer the assertion contract for `test_oof_persistence.py` in Phase 6; §3.6.1 is referenced by row 11
  - 3.7 No new features / no meta-labeling / no auto-d*: explicit
  - 3.8 Inheritance plan: PASS — cherry-pick instruction present with source commits `267bb1d` and `01a68fb`; enumerated missing files listed
- Section 4 (Expected OOS Impact): PASS — predicted metrics table with EXACT headline-metric match expected vs iter-v3/002; 3-tier falsifier (primary/secondary/tertiary) in §4.2 locked before backtest; split-merge clause in §4.3 with PBO non-NaN as hard precondition (NaN loophole closed); Sharpe Δ predicted = 0
- Section 5 (Risk Mitigation): PASS — 3 structural safeguards in §5.2 targeting iter-v3/002's specific process failure mode (file-artifact reconciliation, adversarial test, tightened split-merge clause); no new model-level risks introduced
- Section 6 (Risk Management Design): PASS — 7-primitive table identical to iter-v3/002; fire-rate predictions present; concentration expected-fail acknowledged; placeholder row 8 present for future primitives
- Section 7 (Pre-Registered Failure-Mode): PASS — 5 predictions; predictions 1, 2, 3 are process-level (per iter-v3/002 lesson #4 mandate for per-source-file explicitness); detection signals and mitigations stated for each; probability estimates present
- Section 8 (Pre-Registered MERGE/NO-MERGE): PASS — 22 criteria (19 inherited + 3 NEW: 20, 21, 22 for file-artifact gates); criterion 8 strict reading explicitly removes the NaN-acceptable loophole; split-merge clause partitions headline-metric criteria (1-6, 10, 11, 17) vs methodology-stack criteria (7-9, 12-14, 16, 18-22); Section 8 criterion 13 rewritten as per-symbol formula per Critic Recommendation #2
- Section 9 (Library Stack): PASS — no new external deps; `pyarrow`/`fastparquet` fallback documented for new `to_parquet` call; all packages declared already-installed; reproducibility stamp spec provided in §9.3

## Verifier Command Sanity-Check (re-run)

| Row | Verifier | Executable? |
|---|---|---|
| 1a — OOF buffer in `_objective` | `git diff iteration-v3/002 iteration-v3/003 -- src/.../optimization.py` + `git log ... | wc -l` ≥ 1 | YES |
| 1b — buffer flushed by `optimize_and_train` | `python -c "import pandas as pd; assert pd.read_parquet('reports-v3/iteration_v3-003/trial_oof_returns.parquet').shape[0] >= 40000"` | YES |
| 1c — `_train_for_month` plumbs path | `git diff iteration-v3/002 iteration-v3/003 -- src/.../lgbm.py` shows `oof_persist_path` param | YES |
| 1d — runner passes path | `grep -n "oof_persist_path" run_baseline_v3.py` returns ≥ 1 line | YES |
| 2 — `_compute_cpcv_paths` reads parquet | `python -c "import json; d=json.load(open('reports-v3/iteration_v3-003/dsr.json')); assert isinstance(d['pbo'], (int, float)) and 0.0 <= d['pbo'] <= 1.0"` | YES |
| 3 — `_compute_n_eff_trials` reads parquet | `python -c "import json; d=json.load(open('reports-v3/iteration_v3-003/dsr.json')); assert d['n_eff'] > 4"` | YES |
| Symbols UNCHANGED | `grep -E '^V3_MODELS' run_baseline_v3.py` shows 4 symbols | YES |
| Risk gates UNCHANGED | `grep -E "RiskV3Wrapper\(" run_baseline_v3.py` shows v2 5-gate config | YES |
| Features UNCHANGED | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 34"` | YES |
| Adversarial tests inherited | `uv run pytest tests/strategies/ml/test_pbo_synthetic.py tests/strategies/ml/test_dsr_negative_is.py tests/strategies/ml/test_cpcv_embargo_assert.py -v` exits 0 | YES |
| (NEW) Adversarial test for OOF persistence | `uv run pytest tests/strategies/ml/test_oof_persistence.py -v` exits 0 | YES — **FIXED** (was prose-only in prior gate; now executable verifier command) |
