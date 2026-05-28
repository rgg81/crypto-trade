# Phase 5.5 Gate — iter-v1/028

OVERALL: PASS

## Iteration Type (from Brief Section 0.5 / Section 2.5)
TYPE: EXPLORATION

## Axis Family + Rotation Status (v1 mandatory)
FAMILY: per-cohort-specialization-LTC-v2 (NEW 15th family)
ROTATION_STATUS: VALID

Prior 5 EXPLORATION families (excluding /026 sanity + /027 TF per brief §0.6):
- /021: methodology-pivot
- /022: per-cohort-specialization-LTC (different mechanism class — pre-entry filter)
- /023: feature-family (funding-rate)
- /024: model-arch (regime-conditional)
- /025: feature-family (OI delta)

`per-cohort-specialization-LTC-v2` appears in 0 of the prior 5. Rotation discipline honored.

## HIGH-RISK Declaration (v1 mandatory)
HIGH-RISK: YES
Reasons: (a) per-cohort isolation changes Optuna's training-objective domain (LTC-only vs 5-cohort pool); (b) atr_sl 1.75→1.0 is upstream of triple-barrier label generation — both label class balance AND Optuna basin relocate simultaneously (TWO basin-relocation vectors per LM Master Rec #2 ADOPTED).
Mitigation: ENSEMBLE_SIZE=10 (v1-runner-compatible variance budget; no --seeds flag in v1 argparse; maps to inner ensemble per feedback_v1_ensemble.md).

## LM Master Response Verification (v1 mandatory)
- briefs-v1/iteration_v1-028/lgbm_advisor.md exists: PASS
- Brief Section 3.4 addresses each LM Master recommendation:
  - Rec #1 (MECHANICAL — ensemble-size 10, not --seeds 2): ADOPTED in §3.2/3.3
  - Rec #2 (REFRAMING — atr_sl is upstream of label generation, PARTIAL inoculation only): ADOPTED in §0.4/§1/§6.5
  - Rec #3 (PRIORS — 12/18/35/22/13 vs QR 15/20/35/20/10): ADOPTED in §5.1
  - Rec #4 (F-AXIS pre-registration — #1 dispatch, #2 trade-count, #3 SL fire-rate 75-90% counter-intuitive, #4 n_eff [6,10], #5 exit-reason LOAD-BEARING): ADOPTED in §4 F-AXIS-MECHANISM
  - Rec #5 (INOCULATION — PARTIAL not immunity; modal lift +0.25–+0.45): ADOPTED in §0.4/§1/§5.2
  - Rec #6 (MOST-IMPORTANT — F-AXIS #5 TP-exit count LOAD-BEARING, replaces F-AXIS #3): ADOPTED in §4/§6.2
  - Rec #7 (/029-STAGING verdict-conditional matrix): ADOPTED in §11.7 (supersedes §11.1 for /029 binding)
  All 7 recommendations addressed: PASS

## Cadence Check (v1 EXPLORATION)
- Wall-clock budget declared (modal 30 min / hard cap 2h): PASS (§3.6 present; 30 min modal, 90 min kill, 2h hard cap)
- EXPLORATION cadence check (not CONFIRMATION): N/A
- CONFIRMATION precedents N/A (not a CONFIRMATION): N/A

## Per-Section Status

### Section 0 — Data Split
PASS. §0.1 confirms OOS_CUTOFF_DATE=2025-03-24 and training_months=24 UNCHANGED. Anchor = v0.v1-baseline-corrected (f8bc12c). IS and OOS windows implied by baseline (24 months IS ending 2025-03-24; OOS from 2025-03-24 forward).

### Section 0.5 — Iteration Type Declaration
PASS. TYPE=EXPLORATION declared in §2.5 (HIGH-RISK Axis Declaration). Wall-clock cap = 2h per v1 EXPLORATION rule.

### Section 0.6 — Architecture-Family Justification
PASS. Family = per-cohort-specialization-LTC-v2 (NEW 15th family). Prior 5 EXPLORATION families enumerated in §0.6. ROTATION_STATUS=VALID with rationale (different mechanism class from /022's literal name; post-entry magnitude clip vs pre-entry direction filter). Critic Check 14 verification path stated in §3.5.

### Section 1 — Hypothesis
PASS. Single hypothesis H_028: LTC-only training + tighter ATR-based SL multiplier (atr_sl=1.0 vs baseline 1.75) caps dominant loss channel of LTC OOS (SL exits at -5 to -7% magnitude) at the cost of converting some TP-eligible trades into earlier SL fires. PARTIAL basin inoculation explained with two basin-relocation vectors. Predicted OOS Sharpe Δ band [-0.15, +0.55] modal +0.25 to +0.45. Specific and falsifiable.

### Section 2 — IS-Only Numerical Evidence
PASS. Tables committed from analysis/iteration_v1-028/ltc_oos_catastrophe_eda.py (commit 5f76b4a). §2.1 baseline trade distribution; §2.2 direction-split attribution; §2.3 OOS loss-channel ranking; §2.4 tighter-SL counterfactual (+36.17% Δ on baseline roster); §2.5 confidence calibration; §2.6 basin-relocation diagnostic (Jaccard 0.093 OOS); §2.7 monthly loss clustering. Script noted as committed and read-only (IS data only). Committed script path: analysis/iteration_v1-028/ltc_oos_catastrophe_eda.py.

### Section 2.5 — HIGH-RISK Axis Declaration
PASS. Declared HIGH-RISK with dual reasons (per-cohort isolation + atr_sl upstream of triple-barrier labeling = TWO basin-relocation vectors). Mitigation: ENSEMBLE_SIZE=10 (v1-runner-compatible). Cycle-3 §5.4 multi-seed mandate binding context provided.

### Section 3 — Proposed Changes
PASS. Enumerated in §3.1-3.6: single elif dispatch branch added to run_baseline_v1.py; V1_ITER028_UNIVERSE=("LTCUSDT",); atr_sl=1.0; atr_tp=3.5 (unchanged); apply_r1=True (unchanged); ensemble_size=10; n_trials=35; V1_FEATURE_COLUMNS_PRUNED (43 cols unchanged). LM Master responses in §3.4 (all 7 recs addressed). Axis family in §3.5. Wall-clock in §3.6.

### Section 4 — Expected OOS Impact
PASS. Predicted Sharpe Δ band [-0.15, +0.55], modal +0.25 to +0.45. Explicit falsifiers F1-F8 + F-AXIS-MECHANISM with pre-registered bands. F-AXIS #5 OOS TP-exit count declared LOAD-BEARING. Falsifier tables in §4 with explicit verdict-capping rules (e.g., OOS TP-count=0 → verdict cannot exceed PROMISING-INERT regardless of F1 magnitude).

### Section 5 — Risk Mitigation
PASS (v1 framing — Predicted Verdict Distribution). §5.1 priors with LM Master vs QR comparison + ADOPTED values (12/18/35/22/13). §5.2-5.3 rationale for each verdict class with binding references. No R1/R2/R3/R5 changes (baseline Model D config preserved — apply_r1=True, no R2, R3 via baseline path).

### Section 6 — Risk Management Design / Failure Modes
PASS. §6.1-6.7: single-cohort basin lottery (6.1), tighter SL clips winners PRIMARY verdict-determining variable per LM Master Rec #6 (6.2), R1 cooldown saturation (6.3), stateless mechanism no deadlock (6.4), TWO basin-relocation vectors (6.5), PROMISING-MECHANICAL adjacency risk (6.6), wall-clock breach (6.7). §6.2 includes quantitative scenario analysis (0-4 TP→SL conversions).

### Section 7 — Pre-Registered Failure-Mode Prediction
PASS (v1 maps to brief §6 Failure Modes + §5 Predicted Verdict Distribution). The skill §7 requirement is addressed: failure modes named forward-looking in §6.1-6.7 with pre-committed diagnostic criteria. The modal failure mode (INERT/35%) = SL fires + basin relocates + label distribution shifts → wash. NEG-CAT tail (13%) = basin relocates AND label shift compound adversely → all TP exits convert to SL. What gates catch: F-AXIS #5 TP-exit count is the binding diagnostic. What failure looks like: OOS TP-exit count=0 + F1 OOS Sharpe Δ < 0.

### Section 8 — Pre-Registered MERGE/NO-MERGE Criteria
PASS (v1 maps to brief §8 Verdict Matrix). Rows 1-8 pre-registered with specific F1 bands, F3 sign conditions, F-AXIS conditions, and F8 trade-count bands. Thresholds locked before backtest runs. PROMISING threshold ≥ +0.40 OOS Sharpe Δ. NEGATIVE-CATASTROPHIC ≤ -0.55. F-AXIS #5 OOS TP-count=0 acts as explicit verdict CEILING regardless of F1 magnitude.

### Section 9 — Library Stack Declaration
PASS. §9 declares: mlfinlab==1.4 (validation; not modified); pypbo (PBO; not invoked at single-cohort EXPLORATION); fracdiff>=0.10 (not used); statsmodels (ADF informational; not invoked); LightGBM (baseline strategy). No new dependencies. No version bumps.

## Reasons (if BLOCK)
N/A — OVERALL=PASS

## Gate Summary
All 9 mandatory sections PASS. LM Master advisory exists and all 7 recommendations addressed. Rotation VALID (per-cohort-specialization-LTC-v2 not in last 5 EXPLORATION families). HIGH-RISK declared with compliant mitigation (ENSEMBLE_SIZE=10, v1-runner-compatible). EXPLORATION cadence within 2h hard cap. No missing or invalid sections detected.
