# Phase 7.5 Critic Review — iter-v3/070

OVERALL: CONFIRMATION-MERGE

(Verdict certification: the SUSPICIOUS-OOS-DOMINANT NO-MERGE classification is methodologically clean. The iteration correctly does NOT update BASELINE_V3.md — /059 stays canonical. "MERGE" certifies the iteration's closeout integrity; it does NOT imply a baseline update.)

## Iteration Type (from Brief Section 0.5)
TYPE: CYCLE 1 CONFIRMATION (full gate stack, binding thresholds — no EXPLORATION informational carve-outs applied).

## Foundation Audit (Boot Steps 9-11)

- **walk_forward lookahead fix INTACT**: `_verify_label_leakage_gap()` recomputes `required_gap = (21+1)×3 = 66`, asserts equality with REQUIRED_GAP. /058 `e149e9d` embargo logic inherited unchanged.
- **DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5)** confirmed (Component A). V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (universal).
- **Path B4 implementation** VERIFIED at run_baseline_v3.py:2386-2464. Additive `_write_dsr_json` extension; legacy `dsr_relative` field PRESERVED.
- **NEW `_verify_timeout_consistency()`** (run_baseline_v3.py:790-821) implemented + invoked in pre-flight — asserts BacktestConfig.timeout_minutes == LightGbmStrategy.label_timeout_minutes == 10080. Critic /069 Rec #1 addressed.
- **V3_MODELS = 3 syms; REQUIRED_GAP = 66; ITERATION_LABEL = "v3-070"; ENSEMBLE_SIZE = 10** (CONFIRMATION mode, full 10-seed tuple, lineage preserved).

**Two stale-docstring defects (NOT behavioral)**: (1) `features_v3/__init__.py:205-219` docstring calls V3_FEATURE_COLUMNS a "15-feature set" — actual tuple is 14 (adx_14 removed at /064). (2) `validation_v3.py:589` docstring says "Default gap = 88" — actual REQUIRED_GAP=66. Documentation rot; process recommendation below.

## §11 Anti-Pattern Static Scan: CLEAN

No start_time/OOS_CUTOFF_DATE/training_months manipulation. No look-ahead shift, no fillna(method=). Track isolation clean.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Component A changes only the ATR-SL multiplier in `label_trades()` (label-time). Component B is post-trade-roster reporting. Trade-math spot-check on 3 OOS rows verified to float precision. Row 5 confirms SL-widening: TP:SL distance ratio 1.333 = 2.0/1.5.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP = 66 = (21+1)×3. Runtime-asserted. /069 4-symbol GAP=88 correctly reverted to 66.

### Check 3 — Multiple-Testing Correction: PASS
PBO=0.1068 (<0.40), PSR=1.0 (>0.95), frac_positive_paths=0.6444 (recounted 29/45). n_trials=1050. **Path B4 verification**: `dsr_relative_b4=1.0` is a LEGITIMATE computed value, NOT degenerate. Forensic: `sr_hat = 2.277246 - 0.639849 = 1.637`; benchmark annualization independently verified (`0.837759/√1296×√756 = 0.639849`); `z ≈ 9.5 → cdf ≈ 1.0` via the live psr() path (not a fallback branch). Path B4 is an OOS-only relative-DSR metric — measures OOS dimension correctly, makes no IS claim. Legacy dsr_relative 0.1134→0.9999 is the granularity-fix working as the /062 thesis predicted.

### Check 4 — IC Correlation: WARN
ic_matrix.csv shows `vwap_dev_20 × regime_momentum_signed_5d = 0.7642` (>0.70 gate). The Category 2 carve-out's stated rationale ("composed feature correlates with its own primitive") is IMPRECISE for this pair — `regime_momentum_signed_5d`'s primitives are `ret_5d` and `hurst_100`, NOT `vwap_dev_20`. The 0.76 is a genuine cross-family correlation. Does NOT escalate to FAIL because: (1) both features inherited from /059 BASELINE_V3 14-feature set — /070 makes ZERO feature change; (2) QR documented it transparently per Critic /069 Rec #3 with importance evidence; (3) both clear importance ≥30. FAIL-ing /070 for an inherited-unchanged baseline correlation would penalize a /059 property /070 did not create. WARN + process recommendation.

### Check 5 — ADF Stationarity: PASS
All 14 features stationary=True at end-of-training-window months across BCH/LDO/TRX. `ret_kurt_200` occasionally marginal (p≈0.051) — known kurtosis-estimator property, inherited from /059 baseline. No new price-derived feature → no new ADF exposure.

### Check 6 — Gate 10-CPCV: PASS
frac_positive_paths = 0.6444 ≥ 0.55 (recounted 29/45). IDENTICAL to /059 — CPCV architecture-invariant; SL-widening trade-roster change did not move it.

### Check 7 — Reproducibility: PASS
Commit SHA `aab9347` (impl), gate `2d733b1`. Explicit 14-feature feature_columns (no auto-discovery). ENSEMBLE_SEEDS literal 10-tuple with lineage in ensemble_summary.json. Trade-math spot-check passed. `--clean-oof` guardrail active. Wall-clock 3.13h within 6h cap.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1 hypothesis (IS ≥ +1.0894 AND OOS ≥ +0.5791) tested honestly and FALSIFIED on IS axis. Implementation matches brief — git-traceable changes exactly the 12 enumerated sub-fixes; no scope creep. **Component decomposition CLEAN**: Path B4 block (lines 2386-2464) contains zero `braked` mutation, zero `label_trades()` call, zero Optuna invocation — provably reporting-layer-only. The entire IS collapse is 100% attributable to Component A (SL widening).

**SUSPICIOUS-OOS-DOMINANT → NO-MERGE classification is CORRECT.** Per `feedback_v3_strict_both_is_oos_baseline.md` BOTH-must-improve: IS Δ -0.9734 is binding FAIL; BASELINE_V3.md correctly stays /059. IS collapse is a GENUINE strategy property (per-symbol forensics: LDO IS -47.46 net at -3.39%/trade — wider 1.5×ATR SL lets each loss run 50% deeper; TRX IS -23.91; worst IS month 2024-12 at -28.97). OOS +1.25 built from 14 distributed monthly returns (no single carrying month) — not leakage. OOS/IS ratio 10.81 is regime asymmetry (SL widening helps trending OOS window, hurts chop/bear IS window).

## Adversarial Questions (Cycle 1 CONFIRMATION)

1. **IS collapse +0.12 — genuine or bug?** GENUINE. Per-symbol IS forensics attribute cleanly to SL widening in adverse regimes. Component B provably cannot touch trades.

2. **OOS/IS ratio 10.81 — leakage?** NO. Walk-forward fix intact, embargo gap=66 asserted, CPCV purge verified. OOS distributed across 14 months. Ratio is regime asymmetry.

3. **Path B4 DSR_relative_B4=1.0 — clean or degenerate?** CLEAN. Real z≈9.5→cdf≈1.0 via live computation (not fallback). Benchmark annualization arithmetic verified. OOS-only metric measuring OOS dimension correctly.

4. **Component decomposition — IS collapse cleanly attributed to /065?** YES. Path B4 verified pure reporting-layer. IS collapse 100% Component A.

5. **BASELINE_V3.md decision.** Correct: /070 NO-MERGE per BOTH-must-improve; BASELINE_V3.md stays `v0.v3-059`. Path B4 retention as infrastructure methodologically sound — strictly-better metric computation, additive dsr.json fields, legacy field preserved. Non-compoundable accretive methodology improvement per `feedback_v3_promising_mechanical_subtype.md`.

## Recommendations to QR

1. **Fix two stale docstrings before cycle 2** — `features_v3/__init__.py:205-219` ("15-feature set" → 14) and `validation_v3.py:589` ("Default gap = 88" → 66). Inert today but exactly the desync class Critic /069 Rec #1 targets.

2. **Tighten Category 2 IC carve-out wording** — `feedback_v3_engineered_feature_pivot.md` justifies the carve-out as "composed features correlate with their primitives." The `vwap_dev_20 × regime_momentum_signed_5d = 0.7642` pair is NOT feature-vs-own-primitive (regime_momentum's primitives are ret_5d + hurst_100). Cycle 2 should either (a) restrict the carve-out to feature-vs-own-primitive pairs only, or (b) explicitly grandfather inherited baseline correlations and apply the gate only to NEWLY-added features.

3. **Adopt OOS/IS ratio bound as a pre-registered gate** — the report Rec #5 proposes rejecting any iteration with OOS/IS ratio > 3.0 regardless of absolute OOS Sharpe. This pattern fired at single-seed /065 and amplified at /070 CONFIRMATION; recurring structural red flag (also /026/027). Cycle 2 EXPLORATION briefs should pre-register the ratio bound in Section 4 as a supplemental SUSPICIOUS classifier.
