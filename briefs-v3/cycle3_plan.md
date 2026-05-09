# v3 Cycle 3 Plan — iter-v3/040–050 (post-iter-v3/039 strategy)

**Date:** 2026-05-09 (at iter-v3/039 closeout — CONFIRMATION-NO-MERGE)
**Author:** QR (autopilot)
**Anchor:** BASELINE_V3.md UNCHANGED at iter-v3/028 (+0.5101 IS / +0.5053 OOS)
**Cycle:** 3rd post-bootstrap cycle (cycle 1 = iter-v3/019-028 → CONFIRMATION-MERGE; cycle 2 = iter-v3/029-039 → CONFIRMATION-NO-MERGE)

## Cycle 3 Goal

**Lift IS Sharpe to ≥ +1.0** (or at minimum ≥ +0.5101 to satisfy strict BOTH-must-improve rule per `feedback_v3_strict_both_is_oos_baseline.md`) **while preserving OOS Sharpe ≥ +1.0** (target: maintain iter-v3/039's OOS gate clearance with a more IS-friendly mechanism).

**Why IS is the focus.** iter-v3/039 confirmed that OOS Sharpe ≥ +1.0 IS achievable in v3 (+1.4650 multi-seed mean, first time in v3 history). The binding constraint shifted from OOS to IS. Strict baseline rule (per user directive 2026-05-09): BOTH IS and OOS multi-seed mean Sharpe must improve to update BASELINE_V3.md. Cycle 3 must produce an iteration that lifts BOTH simultaneously.

**Why per-symbol customizations are off the table.** iter-v3/039 confirmed the "suspicious-OOS-divergence" pattern is STRUCTURAL to per-symbol-customizations bundle (PERSISTED at multi-seed; was hoped to dissolve). Per-symbol features (BCH fracdiff) and per-symbol labels (LDO ATR) systematically lift OOS but break IS. Future per-symbol additions must clear IS-axis pre-validation BEFORE inclusion.

## Starting State (iter-v3/040)

**iter-v3/040 = REVERT per-symbol customizations + restore iter-v3/028 baseline + ALGO universe + regime_momentum.** Acts as cycle 3 baseline-restore-and-extend.

Specific changes from iter-v3/039 head:
1. **Clear V3_FEATURES_PER_SYMBOL** (currently `{"BCHUSDT": V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",)}`) → `{}` (empty). Or keep as architecture but unused — implementation choice for the iter-v3/040 Engineer.
2. **Clear V3_ATR_MULTIPLIERS_PER_SYMBOL** (currently `{"LDOUSDT": (1.5, 0.75)}`) → `{}` (empty). Or keep as architecture but unused.
3. **KEEP V3_MODELS = (BCH, LDO, TRX, ALGO)** — 4 symbols, ALGO is validated PROMISING from iter-v3/029 single-seed.
4. **KEEP V3_FEATURE_COLUMNS_TOP_N = 14** including regime_momentum_signed_5d (validated at iter-v3/028 CONFIRMATION-MERGE).
5. **KEEP REQUIRED_GAP = 88 = (21+1) × 4** for 4-symbol universe.
6. **ITERATION_LABEL = "v3-040"**.

Hypothesis for iter-v3/040: clean baseline restore beats iter-v3/039 on IS axis (lift to ≥ +0.30) and approximately matches iter-v3/028 baseline OOS (~ +0.50). Acts as cycle-3 anchor for iter-v3/041-049 EXPLORATIONs.

**iter-v3/040 classification:** EXPLORATION (single-seed=42 EXPLORATION-spec; --exploration --seeds 1 --n-trials 35 default; ENSEMBLE_SIZE=5 inner). NOT a CONFIRMATION-NO-MERGE retry (per user directive "let's try to fix is next cycle" — iter-v3/040 is the start of a new EXPLORATION cycle, not a CONFIRMATION re-run).

**Why iter-v3/040 is also a "PROMISING-MECHANICAL"-class candidate:** baseline restoration is a clean architectural decision (drag removal of per-symbol customizations that were proven to break IS at multi-seed). Per `feedback_promising_mechanical_subtype.md`, mechanical lift gets classified as PROMISING-MECHANICAL — strictly accretive component decision NOT new edge ingredient — and is non-compoundable across iterations.

## Cycle 3 EXPLORATION Axes (iter-v3/041–049)

Five candidate axes for the next 9 EXPLORATIONs after iter-v3/040 baseline-restore. All are UNIVERSAL (target both IS and OOS lift), not per-symbol.

### Axis 1 — NEW universal engineered feature with proven IS lift (3-4 EXPLORATIONs)

**Why first:** Engineered features have the strongest track record in v3 (iter-v3/025 → iter-v3/028 CONFIRMATION-MERGE; first multi-seed-validated edge ingredient). The pattern that fails at multi-seed is per-symbol customization, NOT engineered features per se. UNIVERSAL composed features should still work.

**Selection methodology:** ANALYSIS-DRIVEN, not random. Build IS-only candidate-screening pipeline:
1. EDA on iter-v3/028 multi-seed importance ranks per symbol (BCH+LDO+TRX) — already done at `analysis/iteration_v3-029/per_symbol_feature_analysis.py` (commit `d451885`).
2. Identify high-importance primitive pairs that LightGBM can't compose at depth 3-5 (similar to regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)).
3. Test composed features for: (a) IS Spearman ρ with target ≥ 0.05 (mild lift over universal feature distribution), (b) IC with existing 14 features ≤ 0.50 (orthogonality), (c) ADF p < 0.05 (stationarity).
4. RANK candidates by IS Spearman ρ DESC; test top 3-4 candidates as separate EXPLORATIONs (atomic swap one universal feature each — replace or add).

**Candidate features (illustrative, to be re-derived from analysis):**
- `hurst_drift_50_200 = hurst_50 − hurst_200` (multi-timeframe regime drift; requires hurst_50/hurst_200 primitives — small EDA cost)
- `adx_signed_momentum = adx_14 × sign(ret_5d)` (REJECTED at iter-v3/025 EDA but worth retesting at cycle 3 anchor)
- `vwap_dev_signed_momentum = vwap_dev_20 × sign(ret_5d)` (cross of mean reversion and momentum; new mechanism)
- `volatility_regime_momentum = ret_5d × sign(range_realized_vol_50 − rolling_median(range_realized_vol_50, 100))` (regime-conditional momentum; high-vol vs low-vol)

**Iterations consumed:** iter-v3/041, iter-v3/042, iter-v3/043 (and possibly iter-v3/044) for top 3-4 candidates as separate atomic-swap EXPLORATIONs.

### Axis 2 — NEW model architecture (1-2 EXPLORATIONs)

**Why retest:** iter-v3/016 closed XGBoost head-to-head as NEGATIVE (worst OOS Δ in v3 history at -2.53), but the closure was specifically for `n_trials=10 + cross-entropy + depth-wise defaults`. NOT closed for all configs. Cycle 3 retest at:
- `n_trials=35` (current default; matches iter-v3/041+ EXPLORATION budget)
- Sharpe-objective Optuna (vs cross-entropy)
- `lossguide` growth (vs depth-wise)
- New universal feature set from Axis 1

**Hypothesis:** XGBoost on the NEW universal feature set (post-Axis 1 winner) outperforms LightGBM on IS Sharpe by ≥ +0.20 (XGBoost's sequential boosting may capture different decision-tree splits than LightGBM's leaf-wise growth, which could surface IS signal that LightGBM misses).

**Iterations consumed:** iter-v3/045 (XGBoost head-to-head retest with new feature set + Sharpe objective).

### Axis 3 — NEW universal labeling architecture (1-2 EXPLORATIONs)

**Why:** iter-v3/017 closed meta-labeling as NEGATIVE PATH C (over-filter; M2 filters 42.7% per-candle but kept trades show no quality lift). Cycle 3 retest with new universal feature set (post-Axis 1) and possibly relaxed M2 threshold (vs PINNED 0.5 at iter-v3/017).

**Alternative labeling axes:**
- Fixed-horizon return labels (vs triple-barrier) — simpler, may produce different IS distribution
- Volatility-clustering labels (recent-vol-conditional barrier) — adapts barrier to volatility regime instead of fixed ATR multipliers
- Asymmetric triple-barrier (TP=2.0, SL=0.5 instead of 2.0/1.0) — emphasizes positive tail captures

**Iterations consumed:** iter-v3/046 (one labeling EXPLORATION; if PROMISING, iter-v3/047 = labeling refinement).

### Axis 4 — Feature pruning for parsimony (1 EXPLORATION)

**Why:** iter-v3/039 used 14 universal features + per-symbol BCH fracdiff. Cycle 3 anchor (iter-v3/040) is 14 universal features. Test if dropping the bottom-3 importance features (per iter-v3/028 multi-seed importance ranks) lifts IS Sharpe via parsimony (smaller search space → less Optuna overfitting on IS).

**Hypothesis:** Dropping 3 lowest-importance universal features (e.g., `ret_skew_50`, `ret_skew_200`, `vwap_dev_20` if low-importance — TBD from EDA) reduces IS overfitting risk without dropping signal. Predicted IS lift: +0.10 to +0.30; OOS effect: neutral to slightly positive.

**Iterations consumed:** iter-v3/048 (single feature-pruning EXPLORATION; atomic drop of 3 features; V3_FEATURE_COLUMNS_TOP_N 14 → 11).

### Axis 5 — Per-symbol additions that DON'T break IS (1 EXPLORATION, optional)

**Why:** Per-symbol architecture is validated as CODE INFRASTRUCTURE at iter-v3/039. The structural problem is per-symbol customizations breaking IS. Cycle 3 reserves ONE iteration to test a per-symbol addition that PASSES an IS-axis pre-validation gate.

**IS-axis pre-validation gate (NEW — cycle 3 protocol):** Before adding any per-symbol feature or per-symbol label to V3_FEATURES_PER_SYMBOL or V3_ATR_MULTIPLIERS_PER_SYMBOL, the QR must run an IS-only paired-bootstrap CV showing:
- Δ IS Sharpe with the candidate ≥ -0.10 (does NOT regress IS by more than 0.10 monthly Sharpe at 90% CI)
- Δ IS Sharpe at 90% CI lower bound ≥ -0.20

**If the IS-axis pre-validation FAILS, the per-symbol candidate is REJECTED at the brief stage** (Phase 5.5 gate BLOCK). Only candidates passing the IS-axis pre-validation enter the EXPLORATION queue.

**Iterations consumed:** iter-v3/049 (per-symbol candidate; only if Axis 5 produces a candidate that passes IS-axis pre-validation; otherwise reserve as buffer).

## iter-v3/050 — SECOND v3 CONFIRMATION

**Trigger:** 10/10 EXPLORATIONs in cycle 3 (iter-v3/040-049) complete; choose the bundle that lifts BOTH IS and OOS.

**Bundle selection criteria (pre-registered, locked at cycle 3 start):**
1. iter-v3/040 baseline-restore (always-included; cycle anchor)
2. From Axis 1 EXPLORATIONs: select the engineered feature with highest IS Sharpe lift AND positive OOS Sharpe lift (SINGLE feature; engineered features DON'T STACK at single-seed per `feedback_v3_engineered_features_dont_stack.md`).
3. From Axis 2-4 EXPLORATIONs: select architectural changes (model, labeling, pruning) that produced PROMISING (clean) at single-seed. Do NOT bundle PROMISING-INERT or PROMISING-MECHANICAL (per cycle 2 lessons).
4. From Axis 5 EXPLORATION: include only if the per-symbol candidate passed IS-axis pre-validation AND showed positive IS Sharpe lift at single-seed.

**Pre-registered MERGE gate criteria for iter-v3/050:** Same 10 gates as iter-v3/039 brief Section 8. STRICT BOTH-must-improve rule: must clear iter-v3/028 baseline on BOTH IS and OOS multi-seed mean Sharpe to update BASELINE_V3.md.

**iter-v3/050 spec:** `--seeds 2 + ENSEMBLE_SIZE=5 + n_trials=35` (CONFIRMATION-spec, identical to iter-v3/028 and iter-v3/039). 6h wall-clock cap.

## Cadence Summary

| Iteration | Type | Axis | Status |
|---|---|---|---|
| iter-v3/040 | EXPLORATION (PROMISING-MECHANICAL) | Cycle 3 baseline-restore | iter-v3/039 closeout deliverable |
| iter-v3/041 | EXPLORATION | Axis 1 — engineered feature #1 | TBD (analysis-driven) |
| iter-v3/042 | EXPLORATION | Axis 1 — engineered feature #2 | TBD |
| iter-v3/043 | EXPLORATION | Axis 1 — engineered feature #3 | TBD |
| iter-v3/044 | EXPLORATION | Axis 1 — engineered feature #4 (optional) | TBD |
| iter-v3/045 | EXPLORATION | Axis 2 — XGBoost retest with new features | TBD |
| iter-v3/046 | EXPLORATION | Axis 3 — labeling architecture | TBD |
| iter-v3/047 | EXPLORATION | Axis 3 — labeling refinement (optional) | TBD |
| iter-v3/048 | EXPLORATION | Axis 4 — feature pruning | TBD |
| iter-v3/049 | EXPLORATION | Axis 5 — per-symbol with IS-axis pre-validation (optional) | TBD |
| iter-v3/050 | SECOND v3 CONFIRMATION | Best bundle (multi-seed validation) | Pre-registered MERGE gates |

**STRICT 10:1 cadence per `feedback_v3_strict_10_to_1_cadence.md`** — iter-v3/040-049 are 10 SEPARATE EXPLORATIONs; iter-v3/050 is a SEPARATE CONFIRMATION. Do NOT collapse 10th into next CONFIRMATION.

## What This Plan Avoids (carry-forward from cycle 2)

- **Per-symbol customizations breaking IS** — primary cycle 2 failure mode; addressed by IS-axis pre-validation gate (Axis 5).
- **Knob-tuning** — saturated per `feedback_axis_saturation_predictor.md`. No ADX, z-score, BTC-band tunes in cycle 3.
- **Symbol-swapping** — 4-symbol universe (BCH+LDO+TRX+ALGO) FROZEN for cycle 3 unless an EXPLORATION explicitly proposes a structural reason (which would require new EDA + per-symbol-feature-signature alignment per iter-v3/032 methodology).
- **Stacking 2 engineered features at single-seed** — per `feedback_v3_engineered_features_dont_stack.md`. Test ONE engineered feature alone per Axis 1 EXPLORATION.
- **CONFIRMATION-bundle assembly outside iter-v3/050** — per cycle 2 conflation lessons. Only iter-v3/050 runs CONFIRMATION-spec.

## Status

**Cycle 3 plan COMMITTED at iter-v3/039 closeout (this commit).** Cycle 3 EXPLORATIONs commence at iter-v3/040 baseline-restore. iter-v3/041's specific axis-1 candidate selection deferred to the iter-v3/041 brief (will be analysis-driven, not pre-committed here).

**Anchor for cycle 3:** iter-v3/028 baseline (multi-seed +0.5101 IS / +0.5053 OOS). NOT iter-v3/039 NO-MERGE result (which is documented but does not update the anchor).

## See Also

- `BASELINE_V3.md` — cycle 3 anchor
- `briefs-v3/iteration_v3-039/` — cycle 2 closeout artifacts (research brief, engineering report, Critic FINAL)
- `diary-v3/iteration_v3-039.md` — cycle 2 closeout diary
- `briefs-v3/exploration_catalog.md` — cycle history
- `feedback_v3_strict_both_is_oos_baseline.md` — cycle 3 baseline-update rule
- `feedback_v3_per_symbol_lifts_oos_breaks_is.md` — per-symbol architecture validated; per-symbol customizations need IS-axis pre-validation
- `feedback_v3_baseline_update_policy.md` — predecessor STRICTLY-BETTER policy (now tightened to BOTH-must-improve)
- `feedback_v3_strict_10_to_1_cadence.md` — cycle structure
- `feedback_v3_engineered_features_proven.md` — Axis 1 evidence base
- `feedback_v3_engineered_features_dont_stack.md` — Axis 1 single-feature constraint
- `feedback_promising_mechanical_subtype.md` — iter-v3/040 classification
