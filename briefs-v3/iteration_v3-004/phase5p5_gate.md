# Phase 5.5 Gate — iter-v3/004

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`, `ensemble_seeds = [42, 123, 456, 789, 1001]` declared immutable; IS window stated as symbol-first-kline through 2025-03-23 23:59:59 UTC; OOS window from 2025-03-24 onward; per-cell CPCV gap=22 documented as within-symbol variant; global REQUIRED_GAP=88 explicitly confirmed as still asserted by `_verify_label_leakage_gap()` and `combinatorial_purged_cv(expected_gap=REQUIRED_GAP)` — both invariants preserved
- Section 1 (Hypothesis): PASS — one sentence; specific testable target ("per-cell CSCV using existing trial_oof_returns.parquet will produce aggregated PBO strictly in (0.0, 1.0) AND median n_eff > 4"); falsifier in §4.2 locks acceptance criterion before backtest; correctly identified as methodology repair not strategy change
- Section 2 (IS-Only Numerical Evidence): PASS — committed script: `analysis/iteration_v3-004/per_cell_pbo_demo.py` at SHA `23bb5be` (precedes brief SHA `4500769` — chronological order confirmed); all 3 output files committed at same SHA: `per_cell_pbo_results.csv` (173 data rows + header = 174 lines, one per cell), `aggregated_pbo.json` (confirmed: mean_pbo=0.1305, median_pbo=0.000, median_n_eff=25, fisher_chi2=2052.7, synthetic_validation.validation_pairwise_separation=true), `synthesis.md`; per-cell PBO distribution present (§2.2 histogram, 9 bins); per-cell n_eff distribution present (§2.5, median=25, min=12, max=31); Fisher-vs-mean justification present (§2.3, Fisher saturates at chi²=2052.7, df=346); synthetic adversarial validation present (§2.4, overfit median=1.0 vs clean max=0.358, pairwise separation=True); IS-only filter documented (rows with candle_open_time_ms < OOS_CUTOFF_MS)
- Section 3 (Proposed Changes): PASS
  - 3.1 Symbols UNCHANGED: BCH, MKR, LDO, TRX retained; `set({BCH, MKR, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` asserted
  - 3.2 Labeling UNCHANGED: triple-barrier params (tp=2.9×NATR_21, sl=1.45×NATR_21, timeout=21 candles), purge gap=88 all inherited
  - 3.3 Features UNCHANGED: V3_FEATURE_COLUMNS (34 cols) unchanged; no cluster-importance check needed (no additions)
  - 3.4 Risk gates UNCHANGED: v2 5-gate + BTC trend filter; R1/R2/R3 still OFF; table present
  - 3.5 Single-change discipline: PASS — one consumer-side methodology fix decomposed into 5 atomic sub-fixes, each with spec + code path + file artifact; no multi-variable changes
  - 3.6 Brief-vs-code reconciliation table: PASS — all 12 rows have executable verifier commands in the right column; no prose-only cells; rows 1–12 verified to reference either `python -c ...` assertions or `uv run pytest ...` commands or `grep ...` / `diff ...` commands; no empty cells found
  - 3.7 No new features / no meta-labeling / no auto-d* / no universe change: explicit
  - 3.8 Inheritance plan: PASS — deviation C (branch directly from iteration-v3/003 commit `0ca7ba1` instead of quant-research) explicitly justified ("re-cherry-picking the 3-iteration chain is more error-prone than direct branching"); 5 inheritance verifier commands listed with expected output; parquet input artifact path specified
  - Deviation A (cell-key collapse from (sym, month, seed) to (sym, month)): PASS — §2.1 provides empirical justification (every group of 5 rows for same (sym, month, trial, fold, candle) has `nunique(oof_return)==1`; dedup by natural key loses no statistical signal because seed dimension is empirically degenerate in this parquet)
  - Deviation B (Fisher's method → cross-cell mean as headline aggregator): PASS — §2.3 provides empirical justification (Fisher chi²=2052.7 at df=346 underflows to numerical 0.0; mean is the only aggregator returning a value strictly in (0,1)); Fisher retained as supplementary diagnostic in aggregated_pbo.json; §9 provides mathematical justification (chi²=-2×Σln(p_i) dominated by 173×-2×ln(ε)≈+5900)
  - Deviation C (branch from iteration-v3/003): PASS — §3.8 explicit justification; standard worktree base-branch is quant-research but this deviation is justified and documented
- Section 4 (Expected OOS Impact): PASS — predicted metrics table with EXACT expected match on 13 headline metrics vs iter-v3/003; 5-tier falsifier in §4.2 (primary/secondary/tertiary/quaternary/quinary) all locked before backtest; split-merge clause in §4.3 with PBO strict-(0,1) as hard precondition; criterion 21 tightened (0.0 no longer acceptable)
- Section 5 (Risk Mitigation): PASS — 5 structural safeguards in §5.2 specifically targeting iter-v3/003's process failure mode; each safeguard maps to a named sub-fix or criterion; no new model-level risks introduced (headline metrics expected exact match)
- Section 6 (Risk Management Design): PASS — 7-primitive table identical to iter-v3/003 (fire rates present, regime coverage present, placeholder row 8 present); MKR concentration expected-fail acknowledged; combined kill rate target stated (69–78%)
- Section 7 (Pre-Registered Failure-Mode): PASS — 5 predictions total: P1, P2, P3 are PROCESS-LEVEL (consumer-side aggregator misuse, sub-fix silently dropped, per-cell sample-size failure) — meets the ≥3 process-level requirement per iter-v3/002 lesson #3; P4 and P5 are model-level; each prediction has a detection signal, probability estimate, and mitigation; Section 7 preamble explicitly names iter-v3/003 diary lessons as source of the process-level emphasis
- Section 8 (Pre-Registered MERGE/NO-MERGE): PASS — 24 criteria (22 inherited from iter-v3/003 + 2 NEW: criterion 23 (aggregator-vs-per-cell consistency |mean-median| ≤ 0.15) and criterion 24 (per_cell_pbo.csv ≥ 50 rows with rank>1)); criterion 21 tightened to strict (0.0, 1.0) (0.0 no longer acceptable, closing iter-v3/003 loophole); split-merge clause partitions headline-metric criteria (1, 2, 3, 4, 5, 6, 10, 11, 17) vs methodology-stack criteria (7, 8, 9, 12, 13, 14, 16, 18, 19, 20, 21, 22, 23, 24); NO-MERGE conditions include 24h wall-clock cap and Phase 5.5 BLOCK trigger
- Section 9 (Library Stack): PASS — no new external deps; all 8 packages declared already-installed with license; per-cell aggregation strategy explicitly declared (mean for PBO, median for n_eff) with mathematical rationale; Fisher saturation math stated (chi²≈5900 at df=346 underflows); reproducibility stamp spec provided (library versions, per_cell_pbo.csv stats, comparison.csv diff, 5 adversarial test SHAs and exit codes)

## Deviation Justification Verification

| Deviation | Justification Location | Adequacy |
|---|---|---|
| A — Cell-key collapse (sym,month,seed) → (sym,month) | §2.1 empirical: every 5-row group has nunique(oof_return)==1; no signal lost | ADEQUATE — empirical, reproducible, justified before backtest |
| B — Fisher's method → cross-cell mean (from diary prescription) | §2.3 empirical: Fisher chi²=2052.7 at df=346 underflows; §9 mathematical: chi²=-2×Σln(ε)≈+5900 dominates | ADEQUATE — empirical result committed at SHA 23bb5be; math present; Fisher retained as diagnostic |
| C — Branch from iteration-v3/003 (vs quant-research base) | §3.8: re-cherry-picking 3-iteration chain is more error-prone than direct branching; 5 verifiers confirm full src/ inheritance | ADEQUATE — explicit justification; risks of both paths considered |

## Section 2 Evidence Reproducibility Audit

| Check | Result |
|---|---|
| Analysis script SHA | 23bb5be (committed 2026-05-05) |
| Brief SHA | 4500769 (committed after 23bb5be — CONFIRMED by `git log --ancestry-path`) |
| per_cell_pbo_results.csv | EXISTS — 174 lines (173 data rows + header) |
| aggregated_pbo.json | EXISTS — mean_pbo=0.1305, median_n_eff=25, synthetic_validation=PASS |
| synthesis.md | EXISTS — interpretive narrative with aggregator comparison |
| Script reads IS-only data | Documented (OOS_CUTOFF_MS filter applied per §0 and §2 header) |

## Section 3.6 Reconciliation Table Verification

All 12 rows checked for executable verifier commands (not prose):

| Row | Command type | Executable? |
|---|---|---|
| 1 — per-cell mean PBO | `python -c "... 0.0 < d['pbo'] < 1.0 ..."` | YES |
| 2 — per-cell median n_eff | `python -c "... d['n_eff'] > 4 ..."` | YES |
| 3 — NEW adversarial test | `uv run pytest tests/strategies/ml/test_per_cell_pbo_synthetic.py -v` | YES |
| 4 — per_cell_pbo.csv persistence | `python -c "... len(df) >= 50 ..."` | YES |
| 5 — seed_summary.json PBO literal fix | `python -c "... isinstance(d[0]['pbo'], (int, float)) ..."` | YES |
| 6 — Symbols UNCHANGED | `grep -E '^V3_MODELS' run_baseline_v3.py` | YES |
| 7 — Risk gates UNCHANGED | `grep -E "RiskV3Wrapper\(" run_baseline_v3.py` | YES |
| 8 — Features UNCHANGED (34 cols) | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 34"` | YES |
| 9 — 4 inherited adversarial tests | `uv run pytest tests/strategies/ml/test_pbo_synthetic.py ... -v` | YES |
| 10 — aggregator cross-check | `python -c "... abs(d['pbo'] - med) <= 0.15 ..."` | YES |
| 11 — headline metrics MATCH iter-v3/003 EXACTLY | `diff <(head -50 ...) <(head -50 ...) ...` | YES |
| 12 — per_cell_pbo.csv rank distribution | `python -c "... (df['rank']>1).sum() >= 50 ..."` | YES |

No empty cells. No prose-only cells.

## Status

OVERALL: PASS

Phase 6 may proceed. Engineer implements §3.5 sub-fixes 1–5, writes `tests/strategies/ml/test_per_cell_pbo_synthetic.py`, and runs the validation pipeline against `reports-v3/iteration_v3-003/trial_oof_returns.parquet`. The §3.6 reconciliation table verifiers must ALL exit 0 before the engineering report is committed.
