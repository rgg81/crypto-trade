# Phase 5.5 Gate — iter-v3/056

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 immutable; IS window 2023-03-24 through 2025-03-23, OOS from 2025-03-24 onward. Sacred constants confirmed in runner (lines 81, 1303).
- Section 1 (Hypothesis): PASS — Single sentence: replacing DSR>0.95 with DSR_relative>0.95 (PSR vs CPCV path Q75) produces a feasible gate. Specific falsifier locked: if cpcv_path_sharpe_q75==0.0 or dsr_relative==psr, bug fix did not apply.
- Section 2 (IS-Only Evidence): PASS — committed script `analysis/iteration_v3-055/dsr_reformulation_eda.py` at SHA `a71b2e5`; tables from `dsr_history_v3.csv`, `mechanical_ceiling_grid.csv`, `dsr_decision_table.csv`, `dsr_extended_psr_benchmarks.csv`; post-hoc addendum in `analysis/iteration_v3-056/post_hoc_dsr_relative_validation.md`. Numerical tables: 54-iteration DSR history, 5-option ranking, 2/13 PASS discrimination for R5.
- Section 3 (Proposed Changes): PASS — 3 edits enumerated: (1) run_baseline_v3.py:2181-2196 rewrite to use flat_path_sharpes in-memory, (2) ITERATION_LABEL="v3-056", (3) defensive enable_per_symbol_drawdown_brake=False verify; plus Edit 4: 6th integration test in test_validation_v3_psr_relative.py. Single-axis methodology-only change.
- Section 4 (Expected OOS Impact): PASS — Bit-identity prediction for strategy metrics (+0.5101±0.005 IS, +0.5053±0.005 OOS); DSR_relative=0.5798±0.05 (Engineer-verified post-hoc); cpcv_path_sharpe_q75=0.8378±0.005. Saturation falsifier band: ±5 trades, ±0.05 Sharpe.
- Section 5 (Risk Mitigation): PASS — R1-R5 gates documented (all inherited from /055); methodology-axis risk table with 7 mitigations; simulated historical effect across 8 prior iterations.
- Section 6 (Risk Management Design): PASS — 7-primitive risk gate stack documented in BASELINE_V3.md (BTC trend kill, vol scaling, ADX, Hurst regime, feature z-score OOD, low-vol filter, hit-rate DISABLED); methodology-axis risk profile with fallback and integration-test verification.
- Section 7 (Failure-Mode Prediction): PASS — Pre-registered failure modes: bug fix not applied (PATH C-clean, 5%), strategy unintentionally changed (PATH C-clean/suspicious, 10%), co-fire PATH E expected (10%). Diagnostic: grep for `cpcv_paths_csv = REPORTS_DIR` OR `np.percentile(flat_path_sharpes, 75)`.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — LOCKED PATH A trigger: IS_Sharpe in [+0.5051,+0.5151] AND OOS_Sharpe in [+0.5003,+0.5103] AND IS_trades in [181,183] AND OOS_trades in [95,97] AND cpcv_path_sharpe_q75 in [0.83,0.84] AND DSR_relative OOS in [0.50,0.65] AND CPCV positive=29/45 AND CPCV median Sharpe in [+0.3346,+0.3356]. Hierarchy: PATH C (bug/strategy) > PATH A > PATH E.
- Section 9 (Library Stack): PASS — 8 libraries pinned: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. No new dependencies. Fallback: N/A (no mlfinlab/mlfinpy usage in v3).

## Additional Checks

- Branch: `iteration-v3/056` — PASS
- Sacred constants: OOS_CUTOFF_DATE=2025-03-24 (line 81), training_months=24 (line 1303) — PASS
- Feature isolation: `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` returns COMMENT-ONLY lines (not actual imports) — PASS
- explicit feature_columns: `feature_columns=list(features_for_symbol(symbol))` at line 1318 — PASS
- enable_per_symbol_drawdown_brake=False at line 1366 — PASS
- REQUIRED_GAP=66=(21+1)*3 at lines 115,139 — PASS
- Single-axis change: methodology-only (lines 2181-2196 + ITERATION_LABEL + integration test) — PASS
- No v2 file edits from v3 branch — PASS

## Reasons (if BLOCK)

None — OVERALL=PASS. Proceeding to Phase 6.
