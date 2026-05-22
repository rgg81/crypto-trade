# Phase 7.5 Critic FINAL — iter-v3/039

OVERALL: **CONFIRMATION-NO-MERGE** per user directive 2026-05-09 ("no merge. Close it." + "both is and oos must be in shape").

## Verdict

iter-v3/039 (SECOND v3 CONFIRMATION) FAILS the user-directed strict BOTH-IS-AND-OOS baseline-update rule. OOS Sharpe **+1.4650** PASSES Gate 1 for the first time in v3 history; IS Sharpe **-0.0800** is WORSE than iter-v3/028 baseline (-0.59 below) — Gate 2 FAILS, Gate 3 (OOS/IS ratio) FAILS due to IS sign-flip. The methodology of the run is clean (12 of 12 standard checks PASS); the bundle's per-symbol customization stack lifts OOS but breaks IS aggregate. **BASELINE_V3.md is UNCHANGED at iter-v3/028 (+0.5101 IS / +0.5053 OOS).**

## 12 Standard Methodology Checks (all PASS)

| # | Check | Status | Evidence |
|---|---|---|---|
| 1 | Look-ahead bias audit | PASS | Pre-existing 20 adversarial tests at iter-v3/025 SHA `3b1f979` carry forward; per-symbol features go through same `features_for_symbol` lookup; ATR multipliers operate on past-only candles in `triple_barrier.py` |
| 2 | Embargo width (REQUIRED_GAP) | PASS | REQUIRED_GAP=88 = (timeout_candles=21+1) × n_symbols=4 (BCH+LDO+TRX+ALGO) — matches CPCV setup at iter-v3/035 |
| 3 | IC max | PASS | regime_momentum_signed_5d max |IC|=0.887 with vwap_dev_20 (carve-out per `feedback_v3_engineered_feature_pivot.md` for composed features); fracdiff_d05_close |IC| within bounds; per-symbol additions don't introduce new portfolio-wide IC violations |
| 4 | ADF stationarity | PASS | All 14 universal features unchanged from iter-v3/028 baseline; fracdiff_d05_close ADF p-value < 0.05 by construction (fractional differencing achieves stationarity per LdP AFML Ch. 5) |
| 5 | Hypothesis-implementation alignment | PASS | Single sub-fix (revert ALGO entry from V3_FEATURES_PER_SYMBOL) executed atomically per brief Section 3; ITERATION_LABEL "v3-039"; runner spec `--seeds 2` matches CONFIRMATION-spec declaration |
| 6 | Library pinning | PASS | All 9 packages pinned identically to iter-v3/028 reproducibility stamp; no version drift in lightgbm/optuna/numpy/pandas/scikit-learn/scipy/statsmodels/pyarrow |
| 7 | Reproducibility properties | PASS | Explicit `feature_columns=list(V3_FEATURE_COLUMNS_TOP_N)` passed; ensemble seeds literal [42, 123, 456, 789, 1001]; trade-row PnL spot-check available in comparison.csv |
| 8 | CONFIRMATION-spec compliance | PASS | `--seeds 2` (2 outer × 5 inner = 10 models per cell); n_trials=35 default; ENSEMBLE_SIZE=5; colsample_bytree Optuna-tuned (NOT hardcoded 1.0); matches iter-v3/028 CONFIRMATION-spec exactly |
| 9 | Per-symbol architecture isolation | PASS | V3_FEATURES_PER_SYMBOL["BCHUSDT"] = 15 features (14 universal + fracdiff_d05_close); ALGOUSDT, LDOUSDT, TRXUSDT fall through to V3_FEATURE_COLUMNS_TOP_N (14 features); V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"]=(1.5, 0.75) — no cross-symbol contamination |
| 10 | Sacred constants immutable | PASS | OOS_CUTOFF_DATE=2025-03-24, training_months=24 unchanged; OOS_CUTOFF_MS=1742774400000 verified |
| 11 | DSR/PBO/PSR computation | PASS | DSR=0.0 (structural at n_trials=1400 — same root cause as iter-v3/018, iter-v3/028); PBO mean=0.1072 PASS < 0.4; PSR=1.0 PASS at multi-seed n_trials=1400 saturation; n_eff=19 |
| 12 | Brief gate pre-registration honored | PASS | Brief Section 8 listed 10 gates with thresholds, sources, and priority classification; engineering report audited all 10 gates against pre-registered thresholds (no post-hoc renegotiation) |

## Gate Status Summary (matches engineering report)

| # | Gate | Status |
|---|---|---|
| 1 | OOS Sharpe ≥ +1.0 | **PASS — first time in v3 history (+1.4650)** |
| 2 | IS Sharpe ≥ +1.0 | **FAIL by 1.08 (-0.0800)** |
| 3 | OOS/IS ratio ≥ 0.5 | **FAIL — IS sign-flipped (-18.31 ratio is non-evaluable)** |
| 4 | DSR > 0.95 | **FAIL — structural** |
| 5 | PBO < 0.4 | **PASS at 0.1072** |
| 6 | PSR > 0.95 | **PASS at 1.0** |
| 7 | Top-symbol concentration ≤ 35% | FAIL by 15pp (TRX 49.96%; substantial improvement from 76%, still above 35% gate) |
| 8 | Bundle OOS trades ≥ 130 | **FAIL by 12 trades (mean 118)** |
| 9 | 10-seed validation | NOT RUN at --seeds 2 (not triggered for v3) |
| 10 | Pareto: BOTH outer seeds OOS Sharpe > 0 | **PASS (+1.4650, +0.5290)** |

**4 of 9 evaluated gates PASS** — same count as iter-v3/028 (4 of 9 PASS) but with different mix: iter-v3/039 PASSES Gate 1 (OOS) for first time but FAILS Gates 2 + 3 that iter-v3/028 passed. The trade-off is structural.

## Per-User-Directive Strict-Both-Rule Application

User directive 2026-05-09 establishes: **BASELINE_V3.md updates ONLY when CONFIRMATION beats prior baseline on BOTH IS Sharpe AND OOS Sharpe (multi-seed mean).** OOS-only improvement with IS regression = NO MERGE.

Application to iter-v3/039:

- iter-v3/028 baseline: IS +0.5101 / OOS +0.5053
- iter-v3/039 multi-seed: IS -0.0800 / OOS +1.4650
- IS axis: **WORSE** by -0.59 (regression below baseline)
- OOS axis: BETTER by +0.96 (improvement)
- BOTH-must-improve rule: **FAIL — IS regressed**
- **Decision: CONFIRMATION-NO-MERGE.** BASELINE_V3.md UNCHANGED.

This rule is symmetric to the prior STRICTLY-BETTER-than-prior-baseline policy from 2026-05-08 — that policy required BOTH IS and OOS multi-seed mean Sharpe to strictly beat the prior baseline. iter-v3/028 satisfied this on both axes (+0.13 IS / +0.12 OOS); iter-v3/039 satisfies only OOS, so the strict version of the rule (now confirmed at user closeout) blocks the baseline update.

## Suspicious-OOS-Divergence Pattern Confirmation

The "suspicious-OOS-divergence" pattern observed at iter-v3/026, iter-v3/027, iter-v3/030, iter-v3/034, iter-v3/036, iter-v3/037 SINGLE-SEED was hoped to dissolve at multi-seed. **It PERSISTED at multi-seed in iter-v3/039.** Both outer seeds (42 + 123) reproduce the IS-near-zero / OOS-positive shape. This confirms the divergence is **structural** to the per-symbol-customization bundle, NOT a single-seed Optuna lottery artifact.

## Per-Symbol Architecture Validation

Per-symbol architecture (V3_FEATURES_PER_SYMBOL + V3_ATR_MULTIPLIERS_PER_SYMBOL) is validated as **code infrastructure**:
- Runs cleanly at multi-seed (no crashes, deterministic with seeds, reproducible)
- Per-symbol feature lookup honored (BCHUSDT gets 15 features; others get 14 fallback)
- Per-symbol ATR labeling honored (LDOUSDT gets 1.5/0.75; others get 2.0/1.0 default)
- No cross-symbol contamination

What is NOT validated at multi-seed: the **specific per-symbol customizations chosen in iter-v3/035** (BCH-only fracdiff + LDO-only ATR). At multi-seed these break IS aggregate. **Architecture is kept; specific customizations are rejected for this iteration's bundle.**

## Recommendations for Next Cycle (iter-v3/040+)

1. **REVERT per-symbol customizations.** iter-v3/040 should clear V3_FEATURES_PER_SYMBOL and V3_ATR_MULTIPLIERS_PER_SYMBOL (or keep as architecture but unused). Restore iter-v3/028 baseline + ALGO universe + regime_momentum_signed_5d as the working state.

2. **Focus on UNIVERSAL axes that lift BOTH IS and OOS.** Per-symbol customizations are non-trivially likely to break IS even when they lift OOS — adopt them only with IS-axis pre-validation (test on IS-only data and confirm IS Sharpe doesn't regress before adopting).

3. **Per-symbol additions need IS-axis discipline.** Future per-symbol features must clear an IS-axis test (e.g., paired bootstrap CV showing the candidate doesn't reduce IS Sharpe at 90% CI) BEFORE inclusion in any CONFIRMATION bundle.

4. **OOS gate IS achievable** (+1.4650 confirmed at multi-seed). The strategic question for cycle 3 is: how to lift IS while preserving the OOS lift mechanism. Candidate axes: NEW universal engineered features with proven IS contribution, NEW model architecture (XGBoost retest), NEW universal labeling variant, feature pruning (parsimony).

## Catalog Row

`| iter-v3/039 | 2026-05-09 | SECOND v3 CONFIRMATION: iter-v3/035 bundle multi-seed validation (V3_MODELS=BCH+LDO+TRX+ALGO; V3_FEATURE_COLUMNS_TOP_N=14 incl regime_momentum_signed_5d; V3_FEATURES_PER_SYMBOL["BCHUSDT"]=14+fracdiff_d05_close; V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"]=(1.5, 0.75)) at --seeds 2 + ENSEMBLE_SIZE=5 + n_trials=35 (CONFIRMATION-spec; ALGO entry reverted from iter-v3/038) | -0.59 (multi-seed mean; vs iter-v3/028 baseline +0.5101 → -0.0800) | +1.4650 (multi-seed mean; Δ +0.96 vs iter-v3/028 +0.5053; Gate 1 PASS first time in v3 history; Pareto +1.4650/+0.5290 both positive Gate 10 PASS; Calmar mean 1.318 vs 0.9229; Top-conc 49.96% vs 76.47% improved) | CONFIRMATION-NO-MERGE | NO — BASELINE_V3.md UNCHANGED per user directive 2026-05-09 strict BOTH-IS-AND-OOS-must-improve rule. iter-v3/035 single-seed +2.85 OOS / -0.10 IS multi-seed-validated as +1.47 OOS / -0.08 IS — 49% OOS compression (within iter-v3/028 precedent of 42-58%); IS prediction band failed (predicted [+0.20, +0.70] median +0.45 — observed -0.08 below band lower bound). 5 of 9 MERGE gates FAIL (Gates 2, 3, 4, 7, 8); 4 PASS (Gate 1 OOS=+1.47 first time, Gate 5 PBO=0.107, Gate 6 PSR=1.0, Gate 10 Pareto). "Suspicious-OOS-divergence" pattern from iter-v3/026/027/030/034/036/037 single-seeds PERSISTED at multi-seed — confirmed structural to per-symbol-customizations bundle, NOT single-seed Optuna lottery. Per-symbol architecture validated as CODE INFRASTRUCTURE; per-symbol customizations need IS-axis discipline. NEW memory rules: feedback_v3_strict_both_is_oos_baseline.md (BOTH must improve), feedback_v3_per_symbol_lifts_oos_breaks_is.md (suspicious-OOS-divergence persists at multi-seed). Tag NOT issued (NO MERGE). Cycle 3 starts at iter-v3/040 with REVERT per-symbol customizations + focus on UNIVERSAL IS-lift axes per briefs-v3/cycle3_plan.md. |`
