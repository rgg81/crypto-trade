# Phase 7.5 Critic Review — iter-v3/050

OVERALL: **CONFIRMATION-NO-MERGE-revert** — IS multi-seed mean Sharpe **+0.3189** REGRESSES below /028 baseline +0.5101 (Δ -0.19); BOTH-must-improve gate per `feedback_v3_strict_both_is_oos_baseline.md` FAILS on IS axis. BASELINE_V3.md UNCHANGED at iter-v3/028.

## Iteration Type (from Brief Section 0.5)
TYPE: CONFIRMATION (SECOND v3 CONFIRMATION post-iter-v3/028 BASELINE_V3.md; THIRD in v3 history after iter-v3/018 BOOTSTRAP and iter-v3/039 NO-MERGE)

## QR Response Considered (Round 2 only)

(Round 1 PRELIMINARY skipped — orchestrator dispatched directly with FINAL mode given the unambiguous CONFIRMATION-mechanical-gate evaluation. The verdict pathway is mechanically determined by the brief's pre-registered Section 8 LOCKED criteria; no QR clarifications could change a binary IS-multi-seed-mean-vs-anchor comparison. Discretionary override is PROHIBITED per brief Section 8.)

## Per-Check Status (12 standard methodology checks)

### Check 1 — Look-Ahead Audit: PASS
The iteration adds NO new feature, NO new label generation, NO new training-window logic. The single code change is a one-kwarg DROP (`adx_threshold_per_symbol={"TRXUSDT": 21.0}` → `adx_threshold_per_symbol={}`) at `run_baseline_v3.py:1373` plus an assertion update at `:639-645` and `ITERATION_LABEL` cosmetic bump. No look-ahead surface introduced. The 14-feature stack is byte-identical to iter-v3/049 (which inherited from iter-v3/047 audited at Critic FINAL `1908d50`). Trade-row PnL spot-check on row 100 (TRX SL): `(0.102170 - 0.104100) / 0.104100 × 1 × 100 = -1.8540% → -1.9540% with fees → -1.5633 weighted at 0.80 weight` — matches CSV. Row 102 (BCH TP): `(247.1781 - 274.30) / 274.30 × -1 × 100 = +9.8877%` — matches. Past-only discipline holds.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=88 = (timeout_candles=21 + 1) × n_symbols=4. Universe byte-identical to iter-v3/045+. Per-symbol ADX field DROP does NOT modify label horizons or fold geometry. CPCV embargo geometry unchanged from iter-v3/049 audit.

### Check 3 — Multiple-Testing Correction: MIXED (DSR=0.0 FAIL structural; PBO=0.0939 PASS; PSR=1.0 PASS)
- **DSR=0.0** vs threshold > 0.95 — **FAIL hard, structural at n_trials=1400.** López de Prado E[max_SR] formula returns required SR ≈ 3.5; observed annualized OOS Sharpe ≈ 1.5-2.0 → DSR returns 0.0. Same root cause as iter-v3/018 BOOTSTRAP, iter-v3/028, iter-v3/039. Per `feedback_v3_baseline_update_policy.md`, DSR is ASPIRATIONAL (informational) at v3 trade volume.
- **PBO mean=0.0939** PASS (threshold 0.4). frac_positive_paths=0.5333. Max-aggregator across 174 cells: 4 cells at PBO=1.0 + 4 at PBO ∈ [0.93, 0.99] — informational per iter-v3/028 BOOTSTRAP precedent.
- **PSR=1.0** PASS at multi-seed n_trials=1400 saturation.
- n_trials=1400 = 4 syms × 5 inner × 35 trials × 2 outer (verified). n_eff=18.

### Check 4 — IC Correlation: PASS (composed-feature carve-out)
Per `feedback_v3_engineered_feature_pivot.md` IC carve-out for Category 2 composed features: `regime_momentum_signed_5d` mechanically correlates with primitives — observed max |IC|=0.7790 with vwap_dev_20 (carve-out applies). Other 13 features: max cross-pair |IC|=0.6481 between range_realized_vol_50 and max_dd_window_50. NO new feature added in iter-v3/050.

### Check 5 — ADF Stationarity: PASS (per BASELINE_V3.md inherited)
Monthly rolling ADF identical to iter-v3/049 carry-forward (no NEW feature, no labeling change). 1803/2198 cells stationary at p<0.05 per iter-v3/028 audit.

### Check 6 — Pareto Dominance: PASS (multi-seed Gate 10 binary rule cleared)
**Both outer seeds Sharpe > 0 — Gate 10 PASS.** seed 42: OOS +1.1659; seed 123: OOS +0.3149. The ratio 3.70× is ~2× MORE dispersed than iter-v3/028's 1.72× ratio. Note: iter-v3/039 also cleared Gate 10 (+1.4650/+0.5290) yet was NO-MERGE — Gate 10 is necessary but not sufficient; the BOTH-must-improve baseline-update gate is the binding constraint.

### Check 7 — Reproducibility: PASS
Setup commit SHA `45ddb0f` exists. Brief SHA `acc6baf`. Engineering report SHA `56c671b`. ENSEMBLE_SIZE=5 per `run_baseline_v3.py:90`. `_derive_ensemble_seeds(outer_seed, size=5)` deterministic per outer seed. Outer seeds [42, 123] applied. Runner uses explicit `feature_columns=list(features_for_symbol(symbol))` — NOT auto-discovery. ITERATION_LABEL="v3-050". `--clean-oof` guardrail fired. Reproducibility intact.

### Check 8 — Hypothesis-Implementation Alignment: PASS (hypothesis FALSIFIED on IS axis)
Brief Section 1: bundle "PRESERVES IS lift AND OOS lift at multi-seed ... satisfying the BASELINE_V3.md update gate." Implementation correctly applies bundle composition. **The hypothesis was FALSIFIED on the IS axis** — bundle did NOT preserve IS lift at multi-seed (compressed -57.3% from iter-v3/045 +0.7459 to multi-seed mean +0.3189; -0.19 below /028 baseline). This is a CLEAN scientific result: the hypothesis was specific, testable, and falsifiable; the test fired and the answer is "NO." Hypothesis-implementation alignment is PASS; the hypothesis itself was falsified by the data.

## Optional Checks 9-12

### Check 9 — Symbol Exclusion Enforcement: PASS
{BCHUSDT, LDOUSDT, TRXUSDT, ALGOUSDT} ∩ V3_EXCLUDED_SYMBOLS = ∅.

### Check 10 — Feature Isolation Enforcement: PASS
ZERO matches for `from crypto_trade.features` or `from crypto_trade.features_v2` in features_v3/. Track isolation cleanly enforced.

### Check 11 — Forming-Candle Audit: PASS
Phase 5.5 gate documented data freshness re-fetch: all 4 v3 symbols re-fetched from 36.5h staleness back to 4.5h (within 16h window). Forming-candle filter `if k.close_time < now_ms` per fetcher.py applied.

### Check 12 — Library Version Pinning: PASS
9 packages pinned UNCHANGED from iter-v3/028 BASELINE_V3.md reproducibility stamp. No drift.

## MERGE Gate Audit (per brief Section 8 LOCKED criteria)

### BASELINE_V3.md update gate (BOTH-must-improve per `feedback_v3_strict_both_is_oos_baseline.md`)

| Axis | iter-v3/050 multi-seed mean | iter-v3/028 anchor | Δ | Gate Result |
|---|---:|---:|---:|---|
| IS monthly_sharpe | **+0.3189** | +0.5101 | **-0.1912** | **FAIL** |
| OOS monthly_sharpe | **+0.7404** | +0.5053 | +0.2351 | PASS |

**RESULT: BASELINE_V3.md UPDATE BLOCKED.** IS regression of -0.19 fails the BOTH-must-improve rule regardless of OOS improvement. SAME asymmetric failure pattern as iter-v3/039 (cycle 2 CONFIRMATION, IS -0.59 / OOS +0.96, NO MERGE). The pattern is now SYSTEMATIC across two consecutive cycles.

### Hard-blocking gates (Gates 3, 6, 10)

| Gate | Threshold | Observed | Status |
|---|---|---|---|
| Gate 3: OOS/IS Sharpe ratio ≥ 0.5 | ≥ 0.5 | 0.7404 / 0.3189 = **2.32** | **PASS** |
| Gate 6: PSR > 0.95 | > 0.95 | **1.0000** | **PASS** |
| Gate 10: BOTH outer seeds Sharpe > 0 | both > 0 | seed 42: +1.1659 / seed 123: +0.3149 | **PASS** |

All 3 hard-blocking gates PASS. The NO-MERGE decision is driven exclusively by the BASELINE_V3.md update gate (IS regression).

### Aspirational gates (informational only per `feedback_v3_baseline_update_policy.md`)

| Gate | Threshold | Observed | Status |
|---|---|---|---|
| Gate 1: IS Sharpe ≥ +1.0 | ≥ 1.0 | +0.32 (mean) | FAIL (informational) |
| Gate 2: OOS Sharpe ≥ +1.0 | ≥ 1.0 | +0.74 (mean) | FAIL (informational) |
| Gate 4: DSR > 0.95 | > 0.95 | 0.0 | FAIL (structural) |
| Gate 5: PBO mean < 0.4 | < 0.4 | 0.0939 | PASS |
| Gate 7: Top-symbol concentration ≤ 30% | ≤ 30% | TRX 64.53% (seed 42) | FAIL (informational) |
| Gate 8: Bundle OOS trades ≥ 130 | ≥ 130 | 187 aggregate | PASS at aggregate; per-seed FAIL |
| Gate 9: 10-seed pre-MERGE validation | mean>0, ≥7/10 | NOT RUN | NOT TRIGGERED |

## Critical Observations

### 1. Two-cycle confirmation of the per-symbol-customization anti-pattern
iter-v3/039 (cycle 2 CONFIRMATION, IS -0.08 / OOS +1.47, NO MERGE) and iter-v3/050 (cycle 3 CONFIRMATION, IS +0.32 / OOS +0.74, NO MERGE) both bundle per-symbol customizations and both produce the asymmetric IS-regression-OOS-improvement pattern. Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`: the suspicious-OOS-divergence pattern PERSISTS at multi-seed across two cycles. The pattern is no longer a hypothesis; it is a system-level constraint.

### 2. Seed 42 vs Seed 123 dispersion is alarming (3.70× ratio)
OOS Sharpe ratio seed_42/seed_123 = 1.1659 / 0.3149 = **3.70×**, vs iter-v3/028's 1.72×. The 2× higher dispersion indicates Optuna's per-seed hyperparameter trajectories are NOT converging to a robust signal-driven configuration. Trade count parity (93 vs 94) rules out path-level randomness; the difference is entirely Optuna chosen hyperparameters. **At 3.70× the bundle is below the iter-v3/028 robustness benchmark.**

### 3. LDO is the structural drag (frozen-baseline pattern at OOS-row level)
LDO OOS = -19.13 weighted_pnl, 12 trades, 33.3% WR at seed 42 — BIT-IDENTICAL to iter-v3/047 (-19.13) and iter-v3/049 (-19.13). Three consecutive single-seed=42 anchorings show LDO is the structural drag. The per-symbol ATR (2.0, 1.5) for LDO from iter-v3/045 is an IS-positive customization that does NOT translate to OOS at the portfolio level.

### 4. regime_momentum_signed_5d is now bottom-rank for all 4 symbols
Engineering report feature importance: regime_momentum_signed_5d ranks 14/14 portfolio + 14/14 LDO + 13/14 ALGO + 11/14 BCH + 11/14 TRX. After universe expansion to 4 symbols (ALGO added at iter-v3/033), the feature's signal is no longer a top contributor — possibly diluted by ALGO's universe inclusion.

### 5. The brief calibration was accurate
Brief Section 7 P6 pre-registered the "iter-v3/039 anti-pattern" at P=25% as the DOMINANT failure mode. Brief Section 4.2 predicted IS multi-seed mean ∈ [+0.40, +0.65] median +0.52, OOS ∈ [+0.55, +1.50] median +1.00. Observed: IS +0.3189 (slightly BELOW lower band; -0.0811 outside), OOS +0.7404 (within band). **The QR's brief is methodologically sound; the bundle itself is the problem, not the prediction.**

## On 10-Seed Pre-MERGE Validation

Brief Section 8 Gate 9 trigger condition is "only fires if main 2-seed run passes BOTH-must-improve gate." Since iter-v3/050 fails the BOTH-must-improve gate, Gate 9 is not triggered.

**Critic recommends NOT invoking the 10-seed validation here.** The 2-seed result already shows 3.70× inter-seed dispersion; a 10-seed run would consume ~25h of wall-clock to characterize a NO-MERGE bundle's distribution. Research effort should be reallocated to cycle 4 EXPLORATIONs.

## Recommendations for Cycle 4 (iter-v3/051+)

Per `feedback_v3_strict_10_to_1_cadence.md`: cycle 3 closure is COMPLETE with NO-MERGE; cycle 4 begins at iter-v3/051 = #1 of 10 EXPLORATIONs; iter-v3/061 = cycle 4 CONFIRMATION.

1. **Cycle 3 validated (negatively) the per-symbol customization architecture as a CONFIRMATION-class strategy.** Three PROMISING ingredients (ALGO ATR, LDO ATR, BCH LONG block) individually cleared their EXPLORATION PATH-A gates at single-seed but collectively failed to produce a multi-seed IS improvement at CONFIRMATION. Two consecutive CONFIRMATION-NO-MERGEs both driven by per-symbol customizations breaking IS at multi-seed. Memory rule reinforcement: `feedback_v3_per_symbol_lifts_oos_breaks_is.md` is now CONFIRMED across two cycles, not just one.

2. **iter-v3/051 EDA must investigate LDO removal.** LDO has produced negative OOS in EVERY single-seed iteration since iter-v3/047 (-19.13 frozen baseline at seed 42). LDO's IS-positive ATR customization (2.0, 1.5) is the iter-v3/045 PROMISING ingredient that does NOT survive multi-seed validation at OOS. iter-v3/051 EDA should produce numerical tables comparing 3-symbol BCH+TRX+ALGO vs 4-symbol BCH+LDO+TRX+ALGO at IS-only baseline.

3. **iter-v3/051 EDA must also investigate per-symbol customization REVERT.** Per Critic FINAL `bdd6fc2` (iter-v3/039 review.md) recommendation #1: "REVERT per-symbol customizations" should be the cycle 4 starting hypothesis. Possible 4-axis ranking: (a) LDO removal alone, (b) per-symbol ATR ALGO+LDO REVERT alone, (c) primitive 10 BCH LONG block REVERT alone, (d) full per-symbol REVERT.

4. **CLOSED axes in cycle 3 (do NOT re-test in cycle 4)**:
   - per-symbol ADX threshold (iter-v3/049; ADX axis CLOSED in BOTH global AND per-symbol forms)
   - vol_normalized_ret_5d (iter-v3/048; INERT)
   - per-symbol ATR for BCH (iter-v3/046)
   - Per-symbol customization stacking AT CONFIRMATION (now confirmed across 2 cycles; structural anti-pattern)

5. **HIGH-priority cycle 4 axes**:
   - NEW universal engineered features (composed Category 2): `fracdiff_d05_close` for ALL 4 symbols; `hurst_drift_50_200`; `regime_momentum_signed_3d` retest at universal scope.
   - 3-symbol universe restoration WITHOUT ALGO (test whether regime_momentum_signed_5d recovers from rank-14/14 in 3-symbol universe).
   - DSR gate reformulation (deferred from iter-v3/028 + /039 + /050; structural at v3 trade volume).

6. **MEDIUM-priority cycle 4 axes**:
   - regime_momentum_signed_5d feature importance investigation (rank-14/14 portfolio).
   - NEW model architecture retest (XGBoost variant per iter-v3/016 NOT-CLOSED-for-all-configs caveat).

7. **LOW-priority cycle 4 axes**:
   - Knob axes (saturated): labeling multipliers, ADX, z-score, BTC trend band. CLOSED.
   - Universe expansion (e.g., HBAR+AVAX): CLOSED at iter-v3/021.

## Catalog Row

`| iter-v3/050 | 2026-05-10 | SECOND v3 CONFIRMATION on cycle 3 best PROMISING bundle: V3_FEATURE_COLUMNS_TOP_N=14 (regime_momentum_signed_5d PRESENT; vol_normalized_ret_5d ABSENT); V3_ATR_MULTIPLIERS_PER_SYMBOL={ALGO+LDO (2.0, 1.5)}; primitive 10 BCH LONG block; adx_threshold_per_symbol={} (TRX 21 DROPPED); --seeds 2 + ENSEMBLE_SIZE=5 + n_trials=35 + --clean-oof | -0.19 (multi-seed mean; vs iter-v3/028 baseline +0.5101 → +0.3189) | +0.235 (multi-seed mean; Δ +0.235 vs iter-v3/028 +0.5053 → +0.7404; Pareto +1.1659/+0.3149 both positive Gate 10 PASS; OOS Calmar mean 1.29 vs 0.92; Top-conc TRX 64.53% seed 42; LDO -19.13 weighted_pnl frozen-baseline carry-over; seed 42/seed 123 dispersion ratio 3.70× vs /028 1.72×) | CONFIRMATION-NO-MERGE-revert | NO — BASELINE_V3.md UNCHANGED at iter-v3/028 per `feedback_v3_strict_both_is_oos_baseline.md` BOTH-must-improve rule. Cycle 3 PROMISING ingredients (per-symbol ATR ALGO+LDO + primitive 10 BCH LONG block) compressed -57.3% IS / -79.0% OOS from iter-v3/045 single-seed +0.7459/+3.5259 anchor to multi-seed mean. Hard-blocking gates 3, 6, 10 PASS. Iter-v3/039 anti-pattern (per-symbol customizations lift OOS but break IS aggregate) RECONFIRMED across two consecutive CONFIRMATIONs — `feedback_v3_per_symbol_lifts_oos_breaks_is.md` is now system-level confirmed. iter-v3/051 EDA priorities: LDO removal, per-symbol REVERT, NEW universal engineered features, 3-symbol universe restoration. Tag NOT issued (NO MERGE). |`

## Files Audited

- `briefs-v3/iteration_v3-050/research_brief.md` (SHA `acc6baf`; 787 lines)
- `briefs-v3/iteration_v3-050/phase5p5_gate.md` (SHA `45ddb0f`; PASS verdict)
- `briefs-v3/iteration_v3-050/engineering_report.md` (SHA `56c671b`; CONFIRMATION-NO-MERGE classification)
- `reports-v3/iteration_v3-050/comparison.csv` + `dsr.json` + `seed_summary.json` + `pareto_front.csv` + `per_cell_pbo.csv` + `cpcv_paths.csv` + `ic_matrix.csv` + `adf_test.csv`
- `reports-v3/iteration_v3-050/in_sample/trades.csv` + `out_of_sample/trades.csv` (rows spot-checked for PnL formula)
- `run_baseline_v3.py` (lines 90, 94-103 ENSEMBLE_SIZE; 106 ITERATION_LABEL; 165-169 V3_EXCLUDED_SYMBOLS; 1326 feature_columns; 1340-1374 RiskV2Config bundle composition)
- `BASELINE_V3.md` (iter-v3/028 anchor; SHA `b0576df`)
- `briefs-v3/iteration_v3-039/review.md` (CONFIRMATION-NO-MERGE precedent)
- `briefs-v3/iteration_v3-028/review.md` (CONFIRMATION-MERGE-BOOTSTRAP precedent)
- `briefs-v3/iteration_v3-049/review.md` (cycle 3 PROMISING-bundle composition source)
