# Phase 7.5 Critic Review — iter-v3/055

OVERALL: **EXPLORATION-NEGATIVE** — PATH C-clean fires unambiguously per pre-registered Section 8 LOCKED thresholds. The DSR_relative gate's primary computational output (`cpcv_path_sharpe_q75`) is structurally degenerate (0.0 instead of 0.8378) due to a write-before-read ordering defect at `run_baseline_v3.py:2181-2196`. `dsr_relative=1.0` reported in `dsr.json` is mathematically identical to `psr=1.0` (`PSR(observed; benchmark=0)`); the reformulated gate was NOT evaluated as designed. PATH E co-fires (5th consecutive CPCV-invariant null: 29/45 positive, median +0.3351, Q25 -0.243, Q75 +0.838 — bit-identical to /051/052/053/054 to 4 decimals). Per brief Section 8 hierarchy, PATH C-clean takes precedence as primary classification; PATH E is reinforcing structural evidence. Per `feedback_no_cheating.md`, BLOCK + re-run is forbidden — verdict is final on the buggy artifact as committed at SHA `4a32e00`.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION — Cycle 4 #5 of 10. Spec: `--seeds 1 --n-trials 35 --clean-oof`; ENSEMBLE_SIZE=5; outer seed=42; 2.03h wall-clock (extended due to v1 baseline running concurrently per Engineer report).

## QR Response Considered (Round 2 only)

Round 1 PRELIMINARY skipped — orchestrator dispatched directly with FINAL mode. The verdict pathway is mechanically determined by Section 8 LOCKED PATH A trigger vector: PATH A required `cpcv_path_sharpe_q75 ≠ 0.0` (specifically: `DSR_relative IS in [0.185, 0.285] AND DSR_relative OOS in [0.127, 0.227]`). Observed `cpcv_path_sharpe_q75=0.0` and `dsr_relative=1.0` mechanically falsifies PATH A. PATH C-clean trigger fires on the DSR_relative axis even though strategy is bit-identical to /028. No QR clarification can change this verdict without violating `feedback_no_cheating.md`.

## Per-Check Status (12 standard methodology checks)

### Check 1 — Look-Ahead Audit: PASS
Methodology-only axis. Strategy is bit-identical to /028 single-seed. DSR_relative computation occurs POST-HOC; cannot affect signal generation.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=66 UNCHANGED. Sacred constants UNCHANGED.

### Check 3 — Multiple-Testing Correction: FAIL — DSR_relative axis is buggy; PBO axis PASS
- DSR_legacy = 0.0 (informational; structural at n_eff=19)
- PBO = 0.1243 < 0.40 PASS
- PSR = 1.0 PASS (legacy)
- **`dsr_relative` = 1.0 (BUG; correct=0.5798)** — degenerate value identical to `psr` (benchmark=0). The reformulated gate as committed cannot discriminate any iteration. Operationally NULL.
- **`cpcv_path_sharpe_q75` = 0.0 (BUG; correct=0.8378)** — verifies upstream input was never populated.

For TYPE=EXPLORATION, Check 3-edge axis FAILs are normally informational — but DSR_relative IS this iteration's mandated axis. The axis being broken IS the iteration's central finding → PATH C-clean per pre-registered Section 8.

### Check 4 — IC Correlation: PASS (composed-feature carve-out unchanged from /054)
### Check 5 — ADF Stationarity: PASS (inherited from /054)
### Check 6 — Pareto Dominance: WARN — single-seed point cannot Pareto-dominate
Concentration TRX=181.90% + LDO=-134.07% (negative share inflates positives). Identical distribution to /028 single-seed=42.

### Check 7 — Reproducibility: PASS
Setup SHA `4a32e00`; ITERATION_LABEL="v3-055". Spot-check IS row 0 (TRX SHORT, weight 0.57): pnl=-4.7988% / net=-4.8988 / weighted=-2.7923 — matches CSV. Spot-check OOS row 0 (BCH SHORT TP, weight 0.33): pnl=+7.164% / net=7.0640 / weighted=2.3311 — matches.

### Check 8 — Hypothesis-Implementation Alignment: FAIL — implementation defect at the axis-mandated computation

**Bug location precisely identified at `run_baseline_v3.py:2181-2196`**:
The block reads `cpcv_paths.csv` from disk via `pd.read_csv(cpcv_paths_csv)` at line 2185, but the file is only written at line 2297 inside `_generate_reports()` AFTER `dsr_relative` is computed. The `else` branch at line 2196 fires ("cpcv_paths.csv not found"), benchmark silently set to 0, `psr(raw_sharpe_oos, n_obs, oos_sk, oos_kt, benchmark_sharpe=0.0)` returns 1.0.

The brief's own Section 3 Edit 1 said: "compute `cpcv_path_sharpe_q75` from cpcv_paths.csv data already loaded" — meaning in-memory. The implementation interpreted as on-disk. The in-memory `cpcv_df` (line 2078), `flat_path_sharpes` (line 2090), and `q75` (line 2094) were ALL available 85-100 lines above the bug.

The 5 adversarial unit tests in `tests/strategies/ml/test_validation_v3_psr_relative.py` test `psr()` in isolation — they DON'T exercise the runner's call-site integration. Bug is exactly at the integration boundary not covered.

PATH C-clean primary classification per brief Section 8 LOCKED hierarchy.

## Optional Checks 9-12

### Check 9 — Symbol Exclusion Enforcement: PASS
### Check 10 — Feature Isolation Enforcement: PASS
### Check 11 — Forming-Candle Audit: PASS
### Check 12 — Library Version Pinning: PASS (no new deps)

## Pre-Registered Path Adjudication

| Path | Trigger | Observed | Fired? |
|---|---|---|---|
| PATH A | All bands hold incl. DSR_relative IS [0.185, 0.285] AND OOS [0.127, 0.227] AND cpcv_path_sharpe_q75 > 0 | DSR_relative=1.0 OUT-OF-BAND; cpcv_path_sharpe_q75=0.0 OUT-OF-BAND | NO |
| **PATH C-clean** | IS Sharpe OR OOS Sharpe differs from /053 by >±0.05 OR DSR_relative axis fails | DSR_relative axis FAILED | **YES — defect on DSR_relative axis** |
| PATH C-suspicious | IS-OOS daily ratio outside [0.5, 2.0] | ratio=1.295 within band | NO |
| **PATH E (CPCV-INVARIANT NULL)** | CPCV stats bit-identical to /051/052/053/054 | 29/45 ✓; median +0.3351 ✓; Q25 -0.243 ✓; Q75 +0.838 ✓ | **YES — 5th consecutive** |
| Saturation falsifier | IS/OOS Sharpe Δ vs /053 > ±0.05 OR trade count Δ > ±5 | All within bands; strategy clean | NO |

**Primary classification per brief Section 8 LOCKED hierarchy: PATH C-clean (implementation defect; "ABORT axis; revisit setup"). Co-firing: PATH E (CPCV-INVARIANT NULL on strategy substrate).**

## Critical Adversarial Findings

### 1. Bug location and minimum-cost fix verified
The defect is precisely 16 lines (`run_baseline_v3.py:2181-2196`). The fix is 2-3 lines: replace the file-read with `cpcv_path_sharpe_q75 = float(np.percentile(flat_path_sharpes, 75)) if len(flat_path_sharpes) >= 4 else 0.0` using the in-memory array (line 2090) OR the already-computed `q75` (line 2094). Per `feedback_no_cheating.md`, the FIX cannot be applied to /055 — it must be carried forward to /056 setup.

### 2. The brief's pre-flight checks did not catch this
Brief Section 9 Pre-flight check #5 verifies the WRITE side of dsr.json but not the READ side of cpcv_paths.csv. The 5 adversarial tests cover `psr()` math but not the runner's integration. A 6th integration test loading dsr.json and asserting `cpcv_path_sharpe_q75 > 0` would have caught this in 5 minutes.

### 3. PATH E firing — 5th consecutive iteration confirms cycle-4 STRUCTURAL CONSTANT
CPCV stats bit-identical to /051/052/053/054. The CPCV path-Sharpe distribution is anchored by the (base 14-feature stack, BCH+LDO+TRX universe, 8h cadence, ENSEMBLE_SIZE=5, n_trials=35) tuple INVARIANT to all axes tested in cycle 4. Per /054 Critic FINAL Recommendation #2: "Cycle-5 axis design must account for CPCV-determinism." iter-v3/055 confirms the rule extends to methodology-only axes.

### 4. The brief's R5 PSR-vs-CPCV-Q75 reformulation is theoretically sound
Independent of the bug, the EDA at SHA `a71b2e5` is methodologically rigorous. Bailey-LdP (2014) AFML Ch. 14 canonical relative-DSR formulation correctly identified. Discrimination test (only /039 OOS and /052 OOS pass R5 at single-seed) is empirically grounded. **The METHODOLOGY axis is sound; only the IMPLEMENTATION is broken.** Carry-forward to /056 with 2-line fix is justified.

### 5. n_eff=19 cycle-4 STRUCTURAL CONSTANT extends to /055
n_eff=19 across /051/052/053/054/055. The post-hoc 0.5798 confirms /055's R5 gate, AS DESIGNED, would correctly classify cycle-4 baseline as "does not beat CPCV Q75 at single-seed" — correct discrimination behavior per brief Section 2.4.

## Recommendations to QR for iter-v3/056

1. **Carry-forward A2 to /056 with 2-line bug fix as PRIMARY axis**. Per brief Section 8 LOCKED PATH C-clean outcome ("ABORT axis; revisit setup"). The fix is precisely specified. NO re-EDA required (sound at SHA `a71b2e5`). Recalibrate Section 8 PATH A trigger band to `DSR_relative OOS ~[0.50, 0.65]` based on Engineer's verified post-hoc 0.5798.

2. **MANDATORY pre-flight check addition for /056 brief Section 9**: After running smoke test, READ produced `dsr.json` and ASSERT `cpcv_path_sharpe_q75 > 0` AND `dsr_relative != psr` (whenever cpcv_path_sharpe_q75 != 0). Add a 6th adversarial integration test in `test_validation_v3_psr_relative.py` exercising the full pipeline.

3. **New memory rule recommendation: `feedback_v3_methodology_axis_integration_test.md`**. For future methodology-only axes that ADD computed fields to dsr.json or any other report file, brief Section 9 Pre-flight checklist MUST require an end-to-end SMOKE TEST that runs full pipeline on synthetic dataset and asserts non-degenerate computed value. The /055 unit tests passed; the integration was broken. Integration-test-coverage gap, not math-correctness gap.

4. **Defer A4 (base-stack reordering) to /057**. /056 should clear A2 backlog cleanly first.

5. **CatBoost A3 remains DEFERRED** (7-10h estimated cost exceeds 2h cap; needs CONFIRMATION-spec slot or multi-iter arc).

## Catalog Row

`| iter-v3/055 | 2026-05-12 | EXPLORATION cycle 4 #5 of 10: A2 DSR gate reformulation methodology-only — ADD `dsr_relative` (PSR vs CPCV Q75) and `cpcv_path_sharpe_q75` to dsr.json schema; SET enable_per_symbol_drawdown_brake=False per /054 closeout; V3_FEATURE_COLUMNS_TOP_N=14 unchanged from /054; V3_MODELS BCH+LDO+TRX 3-sym; REQUIRED_GAP=66. Setup SHA 4a32e00. EDA SHA a71b2e5 (5-option ranking; R5 selected). | +0.0000 (vs iter-v3/028 baseline +0.5101 → +0.5101 bit-identical) | +0.0000 (vs iter-v3/028 baseline +0.5053 → +0.5053 bit-identical; OOS trades=96; IS-OOS daily ratio=1.295 within [0.5, 2.0]; CPCV 29/45 positive median +0.3351 Q25 -0.243 Q75 +0.838 IDENTICAL to /051/052/053/054 5th-consecutive PATH E firing) | EXPLORATION-NEGATIVE (PATH C-clean primary: DSR_relative computation defective; co-firing PATH E CPCV-INVARIANT NULL 5th-consecutive) | NO — A2 DSR_relative axis BROKEN at runner integration: line 2181-2196 reads cpcv_paths.csv from disk BEFORE line 2295 writes it; fallback fires; cpcv_path_sharpe_q75=0.0 instead of 0.8378; dsr_relative=PSR(SR; benchmark=0)=1.0 degenerate identical to plain psr; correct post-hoc dsr_relative=0.5798 (FAIL vs 0.95). 2-3 line fix verified by Engineer (use in-memory `flat_path_sharpes`/`q75` already at line 2090/2094). Per `feedback_no_cheating.md` re-run forbidden; carry A2 to /056 with bug fix as PRIMARY axis; mandate end-to-end integration smoke-test pre-flight in /056 brief Section 9. New memory rule recommended `feedback_v3_methodology_axis_integration_test.md`. CPCV-determinism extends to methodology-only axes (5th consecutive bit-identical CPCV stats across feature add/drop, risk-gate add, methodology-only schema extension). Cycle 4 cadence advances 5/10. Tag NOT issued. |`

## Files Audited

- `briefs-v3/iteration_v3-055/research_brief.md` (SHA `522db75`)
- `briefs-v3/iteration_v3-055/phase5p5_gate.md` (SHA `4a32e00`)
- `briefs-v3/iteration_v3-055/engineering_report.md` (SHA `6dc8256`)
- `reports-v3/iteration_v3-055/` (all artifacts; PnL spot-check IS row 0 + OOS row 0)
- `run_baseline_v3.py` (lines 2060-2360 DSR/PSR block; **line 2181-2196 BUG SITE confirmed**; line 2078-2096 in-memory data available 85+ lines above bug; line 2295 cpcv_paths.csv write site)
- `src/crypto_trade/strategies/ml/validation_v3.py` (`psr()` UNCHANGED; bug at call-site, not function)
- `tests/strategies/ml/test_validation_v3_psr_relative.py` (5 unit tests; integration gap)
- `analysis/iteration_v3-055/synthesis.md` (EDA SHA `a71b2e5`; methodologically sound)
- `briefs-v3/iteration_v3-054/review.md` (immediate predecessor)
