# Phase 7.5 Critic Review — iter-v3/056

OVERALL: **EXPLORATION-NEGATIVE** — PATH C-clean fires unambiguously per pre-registered Section 8 LOCKED thresholds. DSR_relative bug fix landed correctly (`cpcv_path_sharpe_q75=0.8378` from in-memory `flat_path_sharpes`, non-degenerate; `dsr_relative=0.0044` from correct call-site evaluation), BUT the observed value falls **0.58 below** the pre-registered PATH A trigger band `[0.50, 0.65]`. The /055 post-hoc 0.5798 prediction was built on an input-metric mismatch (annualized daily SR `0.8591` instead of trade-level SR `~0.55`); at v3's single-seed EXPLORATION regime (n_trades=96, n_eff=19, trade-level SR 0.55, CPCV Q75 0.838), the PSR z-score is -2.62 → `Phi(-2.62)=0.0044`. PATH E co-fires as the **6th consecutive** CPCV-INVARIANT NULL (29/45 positive, median +0.3351, Q25 -0.243, Q75 +0.838 bit-identical to /051-/055). **A2 axis substantively CLOSED for cycle 4** — the gate is mechanically sound but provides ZERO discrimination over legacy DSR=0 at v3's data extent.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION — Cycle 4 #6 of 10. Spec: `--seeds 1 --n-trials 35 --clean-oof`; ENSEMBLE_SIZE=5; outer seed=42; 1.95h wall-clock (within 2h cap).

## QR Response Considered (Round 2 only)

Single-round FINAL adjudication. Pre-registered Section 8 LOCKED PATH A trigger band specifies `DSR_relative OOS in [0.50, 0.65]`. Observed `dsr_relative=0.0044` falls outside band by -0.58. Per Section 8 hierarchy, PATH C-clean fires mechanically when "DSR_relative axis fails" OR "is out of predicted band". The /055 post-hoc input-metric mismatch was the root cause of band mis-specification (annualized daily Sharpe 0.8591 vs trade-level Sharpe ~0.55). No QR clarification can move this verdict per `feedback_no_cheating.md`. The bug fix DID take effect — gate is operationally evaluated — but realized value 0.0044 is the *correct* discrimination behavior for a strategy whose trade-level SR (0.55) sits 0.29 below CPCV Q75 (0.838).

## Per-Check Status (12 standard methodology checks)

### Check 1 — Look-Ahead Audit: PASS
Methodology-only axis. Strategy bit-identical to /055 (= /028 single-seed=42). DSR_relative computation POST-HOC at `run_baseline_v3.py:2183-2207` operates on already-closed trades and `flat_path_sharpes` populated at line 2090. No signal-path interaction.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=66=(21+1)×3. Sacred constants OOS_CUTOFF_DATE=2025-03-24, training_months=24 IMMUTABLE.

### Check 3 — Multiple-Testing Correction: FAIL (CONFIRMED, informational for EXPLORATION)
- DSR (legacy) = 0.0 (informational)
- PBO = 0.1243 < 0.40 — PASS
- PSR (plain) = 1.0 (legacy benchmark=0)
- **DSR_relative = 0.0044** (BUG FIXED at /056; gate operative; FAILS 0.95 threshold)
- **cpcv_path_sharpe_q75 = 0.837759** (BUG FIXED; matches cycle-4 STRUCTURAL CONSTANT 0.838)
- n_eff=19 (cycle-4 STRUCTURAL CONSTANT — 6th consecutive)

R5 reformulation provides ZERO additional discrimination at v3 single-seed EXPLORATION regime — both legacy DSR (0.0) and DSR_relative (0.0044) classify cycle-4 baseline as "does not beat CPCV Q75". Axis substantively closed.

### Check 4 — IC Correlation: PASS (14-feature stack unchanged from /055)
### Check 5 — ADF Stationarity: PASS (no new feature)
### Check 6 — Pareto Dominance: WARN — single-seed point cannot Pareto-dominate
### Check 7 — Reproducibility: PASS
Setup SHA `fc8ee98`; brief SHA `4bbcf23`; gate SHA `3d10a48`. ITERATION_LABEL="v3-056". weighted_pnl_total spot-check (8.5797 - 22.0502 + 29.9178 = 16.4473) matches comparison.csv to 4 decimals.

### Check 8 — Hypothesis-Implementation Alignment: PASS — bug fix LANDED
Verified at runtime:
- `grep -q "cpcv_paths_csv = REPORTS_DIR" run_baseline_v3.py` returns ZERO MATCHES (/055 BUG signature gone)
- `np.percentile(flat_path_sharpes, 75)` appears at line 2184 (post-fix branch)
- dsr.json fields `dsr_relative=0.004399` and `cpcv_path_sharpe_q75=0.837759` populated non-degenerate
- 6 test functions in `test_validation_v3_psr_relative.py` (new integration test at line 118 mirrors runner's exact post-fix code path)

Brief's pre-registered FALSIFIER (Section 4.4): "if `dsr_relative` equals `psr` exactly... PATH C-clean implementation defect (bug not fixed)". Observed: `dsr_relative=0.0044 != psr=1.0` — bug IS fixed; only the band was mis-specified at brief-recalibration time. PATH C-clean fires under the band-miss criterion, not under bug-not-fixed.

## Optional Checks 9-12

### Check 9 — Symbol Exclusion Enforcement: PASS
### Check 10 — Feature Isolation Enforcement: PASS
### Check 11 — Forming-Candle Audit: PASS (no new data)
### Check 12 — Library Version Pinning: PASS (no new deps)

## Pre-Registered Path Adjudication

| Path | Trigger | Observed | Fired? |
|---|---|---|---|
| PATH A | All bands incl. **DSR_relative OOS in [0.50, 0.65]** | All conditions hold EXCEPT DSR_relative OOS=0.0044 (-0.58 below band) | **NO — DSR_relative band miss** |
| **PATH C-clean (DSR_relative out-of-band)** | DSR_relative OOS outside predicted band | 0.0044 vs predicted 0.5798±0.05 → -0.58 below | **YES — PRIMARY** |
| PATH C-clean (bug fix not landed) | cpcv_path_sharpe_q75=0.0 OR dsr_relative=psr | q75=0.8378 != 0; dsr_relative=0.0044 != psr=1.0 | NO — bug fix LANDED |
| PATH C-clean (strategy unintentionally changed) | IS/OOS Sharpe Δ vs /055 > ±0.05 | Bit-identical to /055 | NO |
| PATH C-suspicious | IS-OOS daily ratio outside [0.5, 2.0] | 1.295 within band | NO |
| **PATH E (CPCV-INVARIANT NULL)** | CPCV positive=29/45 AND median in band AND Q75 in band | 29/45 ✓; +0.3351 ✓; +0.8378 ✓ | **YES — 6th consecutive** |

**Primary classification: PATH C-clean (DSR_relative out-of-band; band mis-specified at /055 post-hoc) + PATH E (6th-consecutive CPCV-INVARIANT NULL).** Per Section 8 outcome rule: "Methodology axis advances iff Section 8 outcome ∈ {PATH A, PATH E}". PATH A did NOT fire (band miss). The axis does NOT advance.

## Critical Adversarial Findings

### 1. Bug fix landed correctly
- run_baseline_v3.py:2183-2188 reads `flat_path_sharpes` in-memory (verified)
- /055 BUG signature `cpcv_paths_csv = REPORTS_DIR` returns ZERO MATCHES
- dsr.json contains non-degenerate Q75=0.837759 and DSR_relative=0.004399
- 6 integration tests committed (5 unit + 1 new integration at line 118)

### 2. Post-hoc prediction was wrong, not the gate (input-granularity mismatch)
The /055 Engineering report SHA `6dc8256` plugged `raw_sharpe_oos=0.8591` (annualized daily Sharpe from 88 obs) into `psr()` and computed `dsr_relative=0.5798`. Actual runner computes `raw_sharpe_oos = mean(oos_wp)/std(oos_wp)*sqrt(n_trades)` = trade-level Sharpe ≈ 0.55 over 96 OOS trades. Plugging correct trade-level SR into `psr(0.55; benchmark=0.8378; n=96)` yields 0.0044 — matches observed to 4 decimals. The post-hoc was off by ~130× in PSR space because of input-granularity mismatch.

**Methodologically significant**: future methodology-axis briefs that recalibrate PATH A bands from post-hoc estimates MUST verify the input statistic granularity matches the gate function's expected input. The /055 Engineering report failed to consult trade-level Sharpe at hand; the /056 brief inherited the wrong band.

### 3. A2 axis substantively CLOSED at cycle 4
- /055: PATH C-clean (gate broken — file-read defect)
- /056: PATH C-clean (gate operative — but post-hoc band mis-specified; observed 0.0044 ≈ legacy DSR=0)

At v3 single-seed EXPLORATION with n_trades=96, trade-level SR≈0.55, CPCV Q75=0.838, the gate FAILS at 0.0044 — correct discrimination behavior. But indistinguishable from legacy DSR=0 in informational content. EDA `synthesis.md` (SHA `a71b2e5`) Section R5 already established that only /039 OOS (+1.573) and /052 OOS (+1.385; PATH C-suspicious) pass R5 across 13 v3 IS+OOS splits — both high-OOS-Sharpe iterations. **Cycle-4 baseline at SR~0.55 sits in the FAIL region structurally. No methodology reformulation rescues this.**

Engineer recommendation (axis substantively CLOSED for cycle 4; gate will operate at /061 CONFIRMATION if a bundle materially exceeds CPCV Q75) is correct.

### 4. PATH E firing — 6th consecutive CPCV-INVARIANT NULL
CPCV stats bit-identical to /051/052/053/054/055 to 4 decimal places. The (BCH+LDO+TRX, 8h, 14-feature stack, ENSEMBLE_SIZE=5, n_trials=35) tuple anchors CPCV path distribution as a STRUCTURAL CONSTANT invariant to all axes tested in cycle 4. Per /054 Critic FINAL Recommendation #2 and /055 Critic FINAL #3: cycle-4 baseline architecture saturates CPCV distribution at single-seed EXPLORATION. Cycle-5 mass feature expansion (per `feedback_v3_mass_feature_expansion.md`) is the structural shift needed.

### 5. Cycle-4 cadence: 6/10 EXPLORATIONs complete
Remaining: /057, /058, /059, /060 + /061 CONFIRMATION. /060 (10th EXPLORATION) MUST be single-seed EXPLORATION per `feedback_v3_strict_10_to_1_cadence.md`.

### 6. /057 recommendation requires fresh EDA
Per /054 + /055 Critic recommendations: A4 base-stack reordering is the only viable cycle-4 structural axis remaining. EDA at 14-feature stack — per-feature drop-one importance/IC/ADF analysis — required at brief Section 2. Alternatively pivot to NEW feature family. QR's choice via /057 brief Section 10.

## Recommendations to QR (process-level for /057)

1. **/057 axis: A4 base-stack reordering OR NEW feature family — QR EDA-driven choice**. A2 DSR reformulation substantively CLOSED — no further A2 EXPLORATION until /061 CONFIRMATION.

2. **Recommend new memory rule: `feedback_v3_methodology_post_hoc_input_traceback.md`**. Codify: "Post-hoc bands must specify exact runner code path computing each input variable; if a statistic exists at multiple granularities (daily vs trade-level vs annualized), the brief MUST state which the gate function consumes." This would have prevented the /056 band mis-specification entirely.

3. **PATH E firing 6/6 cycle-4 EXPLORATIONs — cycle-5 mandate stands**. Per `feedback_v3_mass_feature_expansion.md` queued for /062: structural changes to (n_trials, ENSEMBLE_SIZE, universe, model arch, OR base-stack composition with ≥3-feature delta) needed to shift CPCV distribution. Cycle-5 should combine multiple structural shifts simultaneously.

## Catalog Row

`| iter-v3/056 | 2026-05-12 | EXPLORATION cycle 4 #6 of 10: A2 DSR gate reformulation CARRY-FORWARD with 2-line bug fix (run_baseline_v3.py:2181-2196 rewritten to use in-memory flat_path_sharpes); 6th adversarial integration test added test_psr_with_in_memory_flat_path_sharpes_integration; methodology-only; strategy bit-identical to /055 (= /028 single-seed=42). V3_FEATURE_COLUMNS_TOP_N=14 unchanged; REQUIRED_GAP=66; enable_per_symbol_drawdown_brake=False UNCHANGED. Setup SHA fc8ee98. Brief SHA 4bbcf23. EDA SHA a71b2e5 REUSED from /055. | +0.0000 (vs iter-v3/028 baseline +0.5101 → +0.5101 bit-identical) | +0.0000 (vs iter-v3/028 baseline +0.5053 → +0.5053 bit-identical; OOS trades=96; IS-OOS daily ratio=1.295 within [0.5, 2.0]; CPCV 29/45 positive median +0.3351 Q25 -0.243 Q75 +0.838 IDENTICAL to /051/052/053/054/055 6th-consecutive PATH E firing; cpcv_path_sharpe_q75=0.837759 BUG FIXED; dsr_relative=0.004399 BUG FIXED but -0.58 below pre-registered PATH A trigger band [0.50,0.65] from /055 post-hoc) | EXPLORATION-NEGATIVE (PATH C-clean primary: DSR_relative out-of-band 0.0044 vs predicted 0.5798±0.05; /055 post-hoc plugged annualized daily SR 0.8591 instead of trade-level SR ~0.55 into psr() → 130× error in PSR space; co-firing PATH E CPCV-INVARIANT NULL 6th-consecutive) | NO — A2 DSR_relative gate operative but provides ZERO discrimination over legacy DSR=0 at v3 single-seed EXPLORATION (n_trades=96, trade-level SR ~0.55, CPCV Q75 0.838 → PSR z=-2.62 → Phi(-2.62)=0.0044 indistinguishable from legacy DSR=0). R5 reformulation mechanically sound + theoretically rigorous (Bailey-LdP 2014 + AFML Ch. 14) but signal absent in trade distribution at v3 scale. A2 axis substantively CLOSED for cycle 4; gate will operationally evaluate at /061 CONFIRMATION. Recommend new memory rule `feedback_v3_methodology_post_hoc_input_traceback.md`. /057 axis: A4 base-stack reordering OR NEW feature family per QR EDA-driven choice. Cycle 4 cadence advances 6/10. Tag NOT issued. |`

## Files Audited

- `briefs-v3/iteration_v3-056/research_brief.md` (SHA `4bbcf23`)
- `briefs-v3/iteration_v3-056/phase5p5_gate.md` (SHA `3d10a48`)
- `briefs-v3/iteration_v3-056/engineering_report.md` (SHA `9c5d48b`)
- `reports-v3/iteration_v3-056/` (all artifacts; weighted_pnl_total spot-check)
- `run_baseline_v3.py` (bug-fix landing verified at line 2183-2188; /055 BUG signature ZERO MATCHES)
- `src/crypto_trade/strategies/ml/validation_v3.py` (`psr()` UNCHANGED)
- `tests/strategies/ml/test_validation_v3_psr_relative.py` (6 test functions verified)
- `briefs-v3/iteration_v3-055/review.md` (predecessor)
