# Phase 7.5 Critic Review — iter-v3/053

OVERALL: **EXPLORATION-NULL-RESULT** — hurst_drift_50_200 UNIVERSAL SWAP FIRES pre-registered Section 8 LOCKED PATH D mechanically (IS Δ -0.0375 ∈ (-0.10, +0.05) AND OOS Δ -0.0308 ∈ (-0.20, +0.20) AND axis LEARNED at LDO rank 8/15). The feature was LEARNED at mid-table importance despite R²=1.0 linear redundancy with 3 source primitives — falsifying the QR's PATH B INERT-via-rank prediction (55% prob) on the MECHANISM level while CONFIRMING the OUTCOME level (no Sharpe lift). LR-PF methodology refinement is the iteration's primary contribution. PARK hurst_drift_50_200; pivot to /054 with NON-redundant feature family OUTSIDE the 15th-slot SWAP family.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION — Cycle 4 #3 of 10 (REFRAMED HYPOTHESIS B; QR-EDA-backed at SHA `1fc6d55` with three pre-falsifiers disclosed upfront). Spec: `--seeds 1 --n-trials 35 --clean-oof`; ENSEMBLE_SIZE=5; outer seed=42; ~1.25h wall-clock under 2h cap.

## QR Response Considered (Round 2 only)

Round 1 PRELIMINARY skipped — orchestrator dispatched directly with FINAL mode. The verdict pathway is mechanically determined by Section 8.1 LOCKED PATH D pre-registration: three AND-conditions (IS Δ band, OOS Δ band, LEARNED criterion) all fire simultaneously. No QR clarification could change this verdict without violating `feedback_no_cheating.md` post-hoc renegotiation discipline.

## Per-Check Status (12 standard methodology checks)

### Check 1 — Look-Ahead Audit: PASS
`compute_hurst_drift_50_200` is element-wise subtraction of three upstream past-only columns: `hurst_100 − hurst_diff_100_50 − hurst_200`. All three source primitives computed past-only by `add_regime_v3_features` (rolling 50/100/200-bar trailing R/S windows). Adversarial test verifies appending future bars does not alter row `t` value. ADF (Check 5) corroborates: bounded difference of bounded R/S statistics.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP = 66 = (21+1)×3 UNCHANGED from /051-/052. timeout_candles=21; symmetric purge applied; PBO mean=0.1377 < 0.40.

### Check 3 — Multiple-Testing Correction: EXPLORATION-INFORMATIONAL (PBO axis PASS)
- DSR=0.0 structural at n_trials=525 per `feedback_v3_dsr_mode_artifact.md`. Informational only for EXPLORATION.
- PBO mean = 0.1377 PASS. frac_positive_paths = 0.6444.
- PSR = 1.0 PASS at saturation.
- n_trials=525, n_eff=19.

### Check 4 — IC Correlation: PASS (post-carve-out)
Runtime: IC(hurst_drift_50_200, hurst_diff_100_50) = -0.866 (source-primitive carve-out per `feedback_v3_engineered_feature_pivot.md`). Max |IC| with non-source features ≤ 0.07 post-carve-out. Pre-existing regime_momentum_signed_5d ↔ vwap_dev_20 = 0.7642 is inherited from /028 baseline, NOT introduced by /053.

### Check 5 — ADF Stationarity: PASS
hurst_drift_50_200 IS-end ADF: BCH p=1.55e-21, LDO p=1.13e-15, TRX p=2.59e-21. All clear 0.05 by 14+ orders of magnitude.

### Check 6 — Pareto Dominance: PASS (single-seed trivially non-dominated; lottery caveat applies)
Single seed 42 OOS_Sharpe +0.4745, max_dd 44.22%, calmar 0.5558. **OOS max_dd 44.22% is highest in cycle 4** (vs /052: 30.42%; /051: 32.75%) — driven by 2025-08 OOS drawdown of -33.51% on 12 trades. Optuna draw localized to Aug 2025 vol regime, not structural per CPCV stability.

### Check 7 — Reproducibility: PASS
Setup SHA `abc52dc`; fix SHA `d16d7bb`; gate SHA `853bc7e`. ITERATION_LABEL="v3-053". Explicit `feature_columns`. `_verify_feature_columns` enforces hurst_drift_50_200 PRESENT + regime_momentum_signed_3d ABSENT. PnL spot-check OOS row 2 (BCH LONG, weight 0.69): pnl_pct +9.854%, net +9.754%, weighted +6.7304 — matches CSV.

### Check 8 — Hypothesis-Implementation Alignment: PASS
- `engineered_v3.py:490-554` adds compute_hurst_drift_50_200 (signature/docstring/identity match exactly)
- `engineered_v3.py:691` activates dispatch
- regime_momentum_signed_3d retained as dead-code dispatch (zero revert cost per /052 mandate)
- V3_FEATURE_COLUMNS_TOP_N 15th element = hurst_drift_50_200
- ONE-VARIABLE rule honored cleanly

PATH D verdict comes from LOCKED Section 8 path firing mechanically, NOT from implementation gap.

## Optional Checks 9-12

### Check 9 — Symbol Exclusion Enforcement: PASS
### Check 10 — Feature Isolation Enforcement: PASS
### Check 11 — Forming-Candle Audit: PASS
### Check 12 — Library Version Pinning: PASS (no new deps; pure numpy+pandas)

## Pre-Registered Path Adjudication

| Path | Triggers | Observed | Fired? |
|---|---|---|---|
| PATH A (PROMISING-clean) | IS Δ ≥ +0.05 AND OOS Δ ≥ -0.20 AND ratio ∈ [0.5, 2.0] AND rank ≤ 10 in ≥1 sym | IS Δ -0.0375 (FAIL +0.05); LDO rank 8 (PASS); ratio 1.21 (PASS) | NO |
| PATH B (PROMISING-INERT) | rank ≥ 14/15 ALL 3 syms AND \|IS Δ\| ≤ 0.10 AND \|OOS Δ\| ≤ 0.30 | BCH 14, LDO **8**, TRX 15 (FAIL ALL-syms) | NO |
| PATH C-clean | IS Δ < -0.10 OR OOS Δ < -0.30 | None fire | NO |
| PATH C-suspicious | IS-OOS daily ratio outside [0.5, 2.0] | 1.2105 (in band) | NO |
| **PATH D (NULL-RESULT)** | IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈ (-0.20, +0.20) AND axis LEARNED | IS Δ -0.0375 (in); OOS Δ -0.0308 (in); LDO rank 8 (LEARNED) | **YES — UNAMBIGUOUS** |

**PATH D is the sole path whose conditions are met. No discretion.**

## Critical Adversarial Findings

### 1. Engineering report mis-framed portfolio rank — corrected to 14/15

The engineering report Section "SURPRISING FINDING" framed hurst_drift_50_200 as "rank #1 portfolio." **This is incorrect:**

Portfolio importance ranking (last_month_portfolio.csv):
| Rank | Feature | Importance |
|---:|---|---:|
| 1 | range_realized_vol_50 | 456.6 |
| 2 | ret_kurt_50 | 425.8 |
| 3 | vwap_dev_20 | 402.0 |
| ... | ... | ... |
| 13 | btc_ret_14d | 272.0 |
| **14** | **hurst_drift_50_200** | **261.4** |
| 15 | regime_momentum_signed_5d | 257.0 |

hurst_drift_50_200 is **rank 14/15 portfolio** — only LDO mid-table allocation (8/15) prevents PATH B from firing. The QE's headline "rank #1" framing rests entirely on LDO's outlier mid-table rank; BCH (14/15) and TRX (15/15) place it at bottom tier consistent with LR-PF prediction.

### 2. LR-PF methodology refinement is structurally valid; memory rule update recommended

The QE's proposed refinement is correct: importance rank IS NOT a signal-quality proxy for R²=1.0 features. Tree models can allocate split BUDGET to a linearly-redundant precomputed column for representation EFFICIENCY (single-split access vs depth-3 reconstruction) without that allocation reflecting NEW information content. The Sharpe-Δ test is the correct primary diagnostic for R²=1.0 features.

**Memory rule update recommended at iter-v3/053 closeout:**
- For composed features with **R²=1.0 exact** algebraic identity: PRIMARY falsifier = IS Sharpe Δ ∈ (-0.10, +0.05); importance rank INFORMATIONAL only.
- For composed features with **|IC| ∈ (0.5, 1.0)** partial redundancy: current `feedback_v3_engineered_feature_pivot.md` carve-out (importance ≥ 30) APPLIES.
- For features with **|IC| < 0.5** orthogonal: standard rank ≥ 14/15 = PATH B mechanics APPLY.

### 3. CPCV insensitivity to 15th-slot swaps reveals structural limit on cycle 4 #4-10 axis design

29/45 positive paths, median +0.3351, Q25 -0.243 across /051, /052, /053 (IDENTICAL to 4 decimals on median and Q25 across THREE consecutive 15th-slot swaps). This is the cleanest signal yet that **the 14-feature base stack dominates cross-path generalization at 3-sym universe + n_trials=35 + ENSEMBLE_SIZE=5**. The 15th slot is mechanically incapable of moving CPCV distribution at single-seed EXPLORATION.

**This is the structural limit on cycle 4 #4-10 axis design.** Continuing 15th-slot SWAP experiments (4th, 5th, 6th candidate feature) is a guaranteed sequence of NULL-RESULT or PROMISING-INERT outcomes at CPCV level. **The QR must escape the 15th-slot SWAP family at /054.**

### 4. LDO drag is now confirmed structural across 3 iterations — but axis closed for cycle 4

LDO OOS weighted_pnl: -17.44 (/051), -13.96 (/052), -15.61 (/053). Range -13.96 to -17.44 across three 15th-slot swaps. LDO WR oscillates 23-29%. The LDO signal-generator problem is structurally independent of the 15th-slot feature identity. LDO REMOVAL was investigated at /052 EDA and PRE-FALSIFIED (LDO weighted_pnl was +11.155 at /051 IS = +36.78% IS contributor when corrected for weight_factor). Returning to LDO removal at /054 requires fresh /053-trade-roster EDA superseding /052's.

### 5. n_effective_trials = 19 is now a CYCLE-4 STRUCTURAL CONSTANT

n_eff=19 across /051, /052, /053. The 15-feature stack's effective independent trial count saturates at ~19 well below the naive 525. DSR=0 at single-seed EXPLORATION is mechanically inevitable: `E[max_SR] ≈ Z_alpha × sqrt(2*ln(n_eff))` saturates at this n_eff, and realized OOS daily Sharpe of ~1.4 doesn't clear the threshold. cycle 4 CONFIRMATION at iter-v3/061 will need to either (a) increase n_trials to ≥ 100, OR (b) propose alternative multiple-testing gate.

## Recommendations to QR for iter-v3/054 (cycle 4 #4 of 10)

1. **EXIT the 15th-slot SWAP family.** Three consecutive 15th-slot Category-2-composed-feature SWAP attempts (fracdiff PARKED at /051; regime_momentum_signed_3d CLOSED PATH C-suspicious at /052; hurst_drift_50_200 PARKED via PATH D at /053) confirm CPCV-insensitivity at this scope. iter-v3/054 axis MUST be structurally distinguishable. Per `feedback_v3_structural_over_knob_exploration.md` priority order, recommended priorities for /054 EDA:
   - **CatBoost head-to-head** (NEW model architecture) — implementation 4-8h likely exceeds 2h cap; alternative: methodology-only proof-of-concept (1-2h spike on single symbol-month) followed by full backtest in CONFIRMATION.
   - **DSR gate reformulation** (methodology axis) — analysis-only, no wall-clock budget consumption.
   - **Per-symbol drawdown brake** (NEW risk primitive, ~1.5h impl) — orthogonal to all CLOSED per-symbol cap precedents per `feedback_v3_concentration_is_signal.md`; loss-stop semantics differs from proportional scaling.
   - **Base-stack feature reordering** (replacing a mid-table feature in base 14, not slot 15) — directly tests CPCV path distribution response to non-slot-15 changes. Requires fresh EDA on which base feature is marginal contributor at /053.

2. **Update memory rules to document the LR-PF methodology refinement.** Recommended new feedback file: `feedback_v3_lr_pf_methodology.md` codifying: (a) R²=1.0 exact identity features use Sharpe-Δ as primary falsifier, importance rank informational only; (b) |IC|∈(0.5,1.0) features retain importance ≥30 carve-out gate; (c) |IC|<0.5 features retain rank ≥ 14/15 ALL-syms gate.

3. **Pre-register CPCV distribution sensitivity as a 6th pre-falsifier band.** For iter-v3/054 brief Section 8, ADD: "**PATH E (CPCV-INVARIANT NULL)**: CPCV positive-path count, median path Sharpe, and Q25 path Sharpe all match /051/052/053 to 2 decimals. If PATH E fires alongside any other path, the axis is classified as 'failed to escape 15th-slot saturation' and the axis family is CLOSED at /054."

## Catalog Row

`| iter-v3/053 | 2026-05-11 | EXPLORATION cycle 4 #3 of 10: SWAP V3_FEATURE_COLUMNS_TOP_N 15th element — DROP regime_momentum_signed_3d + ADD hurst_drift_50_200 UNIVERSAL (Category 1 NEW engineered feature; hurst_50 − hurst_200 = hurst_100 − hurst_diff_100_50 − hurst_200 algebraic identity R²=1.0 verified at EDA SHA 1fc6d55; V3_MODELS UNCHANGED 3-sym BCH+LDO+TRX; REQUIRED_GAP=66 unchanged); --seeds 1 + ENSEMBLE_SIZE=5 + n_trials=35 + --clean-oof. PROCEED under REFRAMED HYPOTHESIS B (LR-PF methodology documentation; PATH B 55% pred / PATH D 15% pred). Setup SHA abc52dc; fix SHA d16d7bb; gate SHA 853bc7e. | -0.0375 (vs iter-v3/028 baseline +0.5101 → +0.4726) | -0.0308 (vs iter-v3/028 baseline +0.5053 → +0.4745; BCH +24.59 / LDO -15.61 / TRX +15.60 wpnl; IS-OOS daily ratio 1.2105 IN-BAND; hurst_drift_50_200 importance BCH 14/15 + LDO 8/15 + TRX 15/15 + portfolio 14/15; LR-PF MECHANISM falsified — feature LEARNED at LDO mid-table for TREE EFFICIENCY not new signal; LR-PF OUTCOME confirmed — flat Sharpe; OOS max_dd 44.22% elevated vs /052/051 driven by 2025-08 -33.51% Optuna draw localized; CPCV 29/45 positive median +0.3351 Q25 -0.243 IDENTICAL to /051/052) | EXPLORATION-NULL-RESULT (PATH D) per Section 8 LOCKED pre-registration | NO — hurst_drift_50_200 PARKED at /053 closeout (not CLOSED; retain compute function + 5 adversarial tests as dead code per zero-revert-cost discipline). LR-PF methodology refined: R²=1.0 features use Sharpe-Δ as primary falsifier, importance rank INFORMATIONAL. CPCV 3-iteration stability confirms 15th-slot SWAP family is structurally exhausted at single-seed EXPLORATION; /054 MUST escape 15th-slot SWAP family per `feedback_v3_structural_over_knob_exploration.md`. LDO drag confirmed structural across 3 iterations; LDO axis revisit requires fresh /053-trade-roster EDA. Cycle 4 cadence advances 3/10. Tag NOT issued. |`

## Files Audited

- `briefs-v3/iteration_v3-053/research_brief.md` (SHA `f76cb69`)
- `briefs-v3/iteration_v3-053/phase5p5_gate.md` (SHA `853bc7e`)
- `briefs-v3/iteration_v3-053/engineering_report.md` (SHA `161a43d`)
- `reports-v3/iteration_v3-053/` (all artifacts; PnL spot-check OOS row 2)
- `src/crypto_trade/features_v3/engineered_v3.py` (compute_hurst_drift_50_200 + dispatch)
- `run_baseline_v3.py` (ITERATION_LABEL, _verify_feature_columns)
- `analysis/iteration_v3-053/synthesis.md` (SHA `1fc6d55`)
- `briefs-v3/iteration_v3-051/review.md` + `briefs-v3/iteration_v3-052/review.md` (predecessors)
