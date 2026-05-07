# Phase 7.5 Critic Review — iter-v3/018

OVERALL: CONFIRMATION-MERGE-BOOTSTRAP — per user directive `feedback_v3_iter018_baseline_bootstrap.md`; 6 pre-registered MERGE gates FAIL under multi-seed validation but bootstrap framing forces baseline establishment regardless of gate outcomes (one-time only). Methodology of the multi-seed run itself is clean — the failure is genuine signal weakness, not a pipeline defect. Failed gates documented as outstanding constraints for iter-v3/019-028.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Triple-barrier labels use `close_arr[idx]` (knowable at t+1 decision) as entry and forward-scan `pos+1..end` for TP/SL — strictly future bars. ATR loaded from features parquet (past-only). The 13 V3_FEATURE_COLUMNS inherited from iter-v3/008; no new look-ahead surface this iteration.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=66=(21+1)×3 verified at runtime. Symmetric purge+embargo via CombinatorialPurgedKFold.

### Check 3 — Multiple-Testing Correction: FAIL
- **DSR=0.0** vs >0.95 — **FAIL hard, structural at n_trials=1500**. López de Prado E[max_SR]=3.369; observed annualized Sharpe ≈1.7 → dsr_z strongly negative → p≈0. NOT a code bug. Architectural limit.
- PBO mean=0.0892 PASS.
- **PBO max=1.0** on TRX/2022-10 and TRX/2023-01 — **FAIL on max-aggregator**. 13 cells ≥ 0.4 (TRX/2022-Q4 cluster = FTX/LUNA crash regime).
- PSR=0.9936 PASS.
- n_trials=1500 verified; n_eff=25 (vs single-seed 7).

### Check 4 — IC Correlation: PASS
No new feature families. Max |IC| = 0.685 (range_realized_vol_50 ↔ max_dd_window_50) inherited from iter-v3/008.

### Check 5 — ADF Stationarity: PASS
All 13 features stationary at end-of-training-window (2025-03) for all 3 symbols; p-values 1.4e-3 to 0.0.

### Check 6 — Pareto Dominance: WARN
Both seeds positive AND non-dominated on the binary brief gate 10 — PASS. **However**, seed 42 (the comparison.csv primary) is dominated by seed 123 on Sharpe/MaxDD/Calmar/concentration (4 of 6 metrics). BASELINE_V3.md must use multi-seed mean (NOT seed 42 numbers) to avoid embedding dominated-seed bias.

### Check 7 — Reproducibility: PASS
Setup `a595f46`; gate `98769ce`; brief `5c1b303`. ENSEMBLE_SIZE=5; `_derive_ensemble_seeds(42, 5) = [191664963, 1662057957, 1405681631, 942484272, 929893137]`.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Spec ran exactly as briefed. Single ITERATION_LABEL bump v3-017→v3-018; everything else byte-identical to iter-v3/013 baseline. Hypothesis tested cleanly; just falsified.

### Check 9 — Symbol Exclusion Enforcement: PASS
{BCH, LDO, TRX} ∩ V3_EXCLUDED_SYMBOLS = ∅.

### Check 10 — Feature Isolation Enforcement: PASS

### Check 11 — Forming-Candle Audit: PASS

### Check 12 — Library Version Pinning: PASS

## MERGE Gate Audit (per Brief §8)

| # | Gate | Threshold | Observed | Status |
|---|---|---:|---:|---|
| 1 | IS monthly Sharpe ≥ +1.0 | ≥ 1.0 | +0.3788 (mean) / +0.4563 (seed 42) | **FAIL by 0.62** |
| 2 | OOS monthly Sharpe ≥ +1.0 | ≥ 1.0 | +0.3869 (mean) / +0.2343 (seed 42) | **FAIL by 0.61** |
| 3 | OOS/IS ≥ 0.5 | ≥ 0.5 | 0.5134 (seed 42) / 1.79 (seed 123) | PASS |
| 4 | DSR > 0.95 | > 0.95 | 0.0 | **FAIL — structural at n_trials=1500** |
| 5 | PBO mean AND max < 0.4 | < 0.4 | mean 0.089 PASS; max 1.0 **FAIL** | **FAIL on max** |
| 6 | PSR > 0.95 | > 0.95 | 0.9936 | PASS |
| 7 | Top-symbol concentration ≤ 30% | ≤ 30% | TRX 66.08% (seed 42), 55.83% (seed 123) | **FAIL by 36pp/26pp** |
| 8 | Bundle OOS trades ≥ 130 | ≥ 130 | 102 (seed 42), 79 (seed 123) | **FAIL** |
| 9 | 10-seed validation | mean>0, ≥7/10 | NOT RUN (gates 1+2 fail decisively) | NOT TRIGGERED |
| 10 | Pareto: BOTH outer seeds Sharpe > 0 | both > 0 | seed 42: +0.234, seed 123: +0.539 | PASS |

**Confirmed FAILs: 6 of 10.**

## Critical Assessment — Was iter-v3/013 falsified or remediable?

iter-v3/013's headline IS +1.0088 / OOS +2.6970 is **formally falsified**:
- IS Sharpe: +1.0088 → +0.3788 (Δ -0.63, 62% reduction)
- OOS Sharpe: +2.6970 → +0.3869 (Δ -2.31, 86% reduction)
- LDO single-seed lottery confirmed: 80% WR / +40.6 weighted_pnl @ iter-v3/013 → 31.2% WR / -10.24 @ iter-v3/018
- Concentration did NOT compress; it shifted symbol (LDO 65% → TRX 66%)

**Not remediable by configuration tuning.** Engineering report assigns dominant mechanism (P=75%) to single-seed lottery at EXPLORATION budget — exactly what `feedback_seed_validation.md` was written to catch. Genuinely stronger signal source (new feature families, better universe construction, structural architecture) required to lift any future CONFIRMATION above the +1.0 floor.

**Bright spot**: both outer seeds positive AND non-dominated. The 13-feature stack has SOME marginal edge OOS at multi-seed scale (+0.39 mean Sharpe), it just doesn't clear the +1.0 floor.

## DSR > 0.95 gate — structural infeasibility analysis

DSR=0 is **not** a code bug. At n_trials=1500, López de Prado formula requires Sharpe > 3.369; observed ≈1.7. Gate as locked is mathematically blocked. Recommended for next CONFIRMATION: brief proposes either (a) `DSR > 0` (any positive deflation), OR (b) reduce CONFIRMATION budget to `--n-trials 20`. NOT a renegotiation of iter-v3/018's gate.

## Recommendations to QR — Diary + BASELINE_V3.md content

1. **BASELINE_V3.md must use multi-seed MEAN, not seed 42 numbers**. Write `IS monthly Sharpe = +0.3788`, `OOS monthly Sharpe = +0.3869`. Add "BOOTSTRAP BASELINE" prefix with caveat: "Six of ten pre-registered MERGE gates failed; baseline established per `feedback_v3_iter018_baseline_bootstrap.md` one-time directive; not production-ready." Document each failed gate with target lift required.

2. **Diary records iter-v3/013 as FALSIFIED**. Single-seed +2.70 OOS Sharpe was a lottery. Update `exploration_catalog.md` iter-v3/013 row from PROMISING-MECHANICAL to FALSIFIED-AT-CONFIRMATION; the universe drop-MKR component still has merit (TRX positive in BOTH seeds; BCH net positive) but the headline OOS metric is dead.

3. **Calibration miss documentation** per Brief §7 P-tracking: P7 (CONFIRMATION-MERGE @ P=35%) failed; P9 (Sharpe floors missed @ P=10%) realized; P6 (DSR < 0.95 @ P=15%) realized but NOT for predicted reason.

## Recommendations for NEXT 10 EXPLORATIONs (iter-v3/019-028)

1. **HIGH — New feature families.** 13-feature stack at multi-seed produces +0.39 mean OOS — ~0.6 Sharpe below floor. Knob-tuning saturated (10 EXPLORATIONs done). Order-book microstructure variants, funding-rate momentum, on-chain proxies. Bias toward economically-interpretable features.

2. **HIGH — Concentration architecture.** TRX 66% OOS (seed 42), 56% (seed 123) — structural to 3-symbol universe. Either (a) hard `max_per_symbol_pnl_share = 0.40` portfolio constraint, OR (b) universe expansion to 5+ symbols to dilute mechanically.

3. **MEDIUM — DSR gate reformulation.** iter-v3/019 brief proposes either `DSR > 0` OR `--n-trials 20` next CONFIRMATION budget. Process fix.

4. **MEDIUM — Per-symbol diagnostic on TRX/2022-Q4.** PBO max=1.0 on FTX/LUNA crash regime. Either (a) regime-aware TRX gate (kill when BTC_drawdown_30d > 30%), or (b) accept as known-unhedgeable tail with Critic-accepted exception clause. Do NOT remove TRX (strongest OOS contributor in seed 42, +11.97 weighted_pnl).

5. **LOW — Knob axes** (labeling multipliers, ADX, z-score). Saturated per `feedback_axis_saturation_predictor.md`.

6. **LOW — Universe expansion**. Defer until after one HIGH-priority feature-family axis is proven.

10-EXPLORATION cadence clock restarts at iter-v3/019. First post-bootstrap EXPLORATION should target axis #1 (new feature families).

## Final Verdict Summary

**OVERALL: CONFIRMATION-MERGE-BOOTSTRAP** — bootstrap baseline establishment forced by user directive. NOT CONFIRMATION-MERGE-FULL (6 of 10 gates FAIL). Methodology of validation IS clean; failure is strategy edge falling short of +1.0 floors. iter-v3/013 formally falsified. BASELINE_V3.md numbers (multi-seed mean: +0.3788 IS / +0.3869 OOS) anchor next 10 EXPLORATIONs against honest weak-but-positive baseline rather than single-seed lottery artifact.
