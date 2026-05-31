# Phase 5.5 Gate — iter-v1/039

OVERALL: BLOCK

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION

## Axis Family + Rotation Status
FAMILY: loss-function × per-cohort-specialization (DOUBLE-REPEAT COMBO)
ROTATION_STATUS: VALID (prior 5 disperse across 5 distinct families: feature-family, labeling, per-cohort-specialization, loss-function, risk-primitive — no monoculture)

## HIGH-RISK Declaration
HIGH-RISK: YES (rotation rule — double-REPEAT COMBO with NEG-DOMINANT 60% prior)
Mitigation: single-seed OPT-OUT (brief Section 2.5 justifies; IF PROMISING → /044 multi-seed validates per HIGH-RISK escalation rule)

## LM Master Response Verification
- briefs-v1/iteration_v1-039/lgbm_advisor.md exists: PASS (file exists)
- Brief Section 3 addresses each LM Master recommendation: BLOCK

  The lgbm_advisor.md Phase 4.5 was authored for the REJECTED drawdown-brake axis
  (not the current Sortino × specialist hybrid). Brief Section 11 acknowledges this
  explicitly: "A re-issued LM Master advisor on the CURRENT axis is requested at
  Phase 5.5 / 6.0 closeout."

  The gate rule requires each numbered recommendation in lgbm_advisor.md to appear
  in Section 3 as adopted / modified / rejected with reason — even if the reason is
  "REJECTED — applies to prior drawdown-brake axis, not current Sortino × specialist
  dispatch." The brief's Section 3 contains NO response map for recommendations #1,
  #2, or #3 from lgbm_advisor.md. Section 11 pre-registers expectations for a NEW
  LM Master advisory but does not address the existing one.

  Resolution: QR must add a response map to Section 3 (or Section 11) marking each
  of the three recommendations adopted / modified / rejected with one-sentence reason.
  Example: "Rec #1 Hold HP grid constant — ADOPTED (v1 EXPLORATION standard n_trials=18
  applies to Sortino × specialist dispatch identically)."

## Cadence Check
- Wall-clock budget declared: 2h hard cap for EXPLORATION: PASS (Section 0.5 states "2h hard cap")
- EXPLORATION precedents since last CONFIRMATION: 6 of 10 (4 to go before /044 can launch): PASS (≥10 not yet required; CONFIRMATION not launching)

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE = 2025-03-24 and training_months = 24 confirmed sacred in Section 3.3 table and Section 10
- Section 0.5 (Iteration Type, v1/v3): PASS — TYPE: EXPLORATION declared, cadence 6/10 stated, wall-clock estimate and 2h hard cap present
- Section 0.6 (Architecture-Family Justification, v1-only): PASS — double-REPEAT COMBO justified with 3 explicit mitigations + /044 routing implication; prior 5 families listed; rotation status VALID per rule (5 distinct families in prior 5)
- Section 1 (Hypothesis): PASS — H1 3-sentence primary + H1a mechanism + H1b falsifiable; specific: "Sortino objective layered on /036 LINK+DOT trend-scanning 2-cohort substrate"; OOS delta falsifier present
- Section 2 (IS-Only Evidence): PASS — F-AXIS #1 verdict matrix with 6 bands + probabilities; EDA prior from IS-only /036 + /037 trades cited (Jaccard 0.1381, Sortino/Sharpe ratio 1.22); committed EDA script referenced (analysis/iteration_v1-039/eda.py in axis_rejected.md)
- Section 2.5 (HIGH-RISK Axis Declaration, v1-only): PASS — HIGH-RISK by rotation rule declared; NORMAL-RISK by mechanism explained; single-seed budget choice justified with counter at 1/3
- Section 3 (Proposed Changes): PASS with CAVEAT — implementation design is clear (elif dispatch + catch-all + 13 tests, NO new src/ code); CAVEAT: LM Master response map MISSING (see LM Master block above — this is the primary BLOCK reason)
- Section 4 (Expected OOS Impact): PASS — F-AXIS #2-#7 with pass/fail criteria, modal prediction +1.42 OOS Sharpe, explicit falsifiers H1b + §9 triggers
- Section 5 (Risk Mitigation): PASS — Section 5 references §3.3 table confirming R1/R2/R3 gates identical to /036 baseline; no new risk changes required
- Section 6 (Risk Management Design): PASS — Section 6 references §3.3 configuration table; risk gates inherited from /036 (R1 ON C'/E, R2 ON E, R3 ON both); fire-rate predictions implicit in /036 inheritance
- Section 7 (Failure-Mode Prediction, v1/v3): MISSING/INVALID — Section 7 in brief is "Expected Report Shape" (4-way comparison table format). The gate mandates a pre-registered failure-mode prediction paragraph (1-2 paragraphs forward-looking: how the iteration most plausibly fails OOS, what gates should catch, what failure looks like in metrics). The failure scenario IS present in Section 9 as "Mechanism failure scenario (PREDICTED FAILURE MODE)" — but it is under the wrong section number and the gate checks for Section 7 by name/intent. The QR must either retitle Section 7 to "Pre-Registered Failure-Mode Prediction" or add an explicit Section 7 sub-section.
- Section 8 (MERGE/NO-MERGE Criteria, v1/v3): MISSING/INVALID — Section 8 in brief is "Path Forward Predictions (/044 routing implications)". The gate mandates locked NUMERICAL thresholds before the backtest runs (e.g., "MERGE iff OOS_monthly_Sharpe ≥ X AND PBO < Y"). Section 8 provides OUTCOME QUADRANT ROUTING (PROMISING → SINGLE CONFIRMATION, INERT → SEPARATE, etc.) but NOT locked numerical MERGE/NO-MERGE thresholds. No row like "MERGE iff OOS Sharpe Δ ≥ +0.10 AND IS > 1.0 AND OOS > 1.0" appears. The QR must add explicit pre-registered numerical criteria.
- Section 9 (Library Stack, v1/v3): MISSING — Section 9 in brief is "Behavioral-effect predictor". No library stack declaration exists. The gate mandates which versions of mlfinlab/mlfinpy/pypbo/fracdiff are used (or which fallbacks and why). Even "no external ML-finance libraries used in this iteration; LightGBM + Optuna + NumPy only" would satisfy the intent.

## Reasons (BLOCK)
- Section 3 / Section 11: LM Master response map absent. Each of the 3 numbered recommendations in lgbm_advisor.md Phase 4.5 must be addressed in Section 3 as adopted/modified/rejected with reason. Brief Section 11 acknowledges the mismatch and requests re-issue but does NOT discharge the existing advisory. The QR must add a response map — even one-liners like "REJECTED — rec applies to drawdown-brake (rejected axis), not current Sortino × specialist hybrid" are sufficient per the gate rule.
- Section 7: Missing as a named gate section. The failure-mode prediction paragraph exists in Section 9 under "Mechanism failure scenario" but the gate requires it under Section 7 with the explicit mandate: 1-2 paragraphs predicting how the iteration most plausibly fails OOS, what gates catch it, what failure metrics look like. The content in Section 9 partially satisfies this but the QR should promote it to a clearly labeled Section 7.
- Section 8: Missing locked numerical MERGE/NO-MERGE thresholds. "MERGE iff OOS Sharpe Δ ≥ +0.10 AND OOS Sharpe absolute ≥ +1.75 AND IS Sharpe > 0 AND OOS trades ≥ 80" or equivalent must be pre-registered before Phase 6 runs.
- Section 9: Missing Library Stack Declaration. Must declare which library versions are in use (even a negative declaration: "no mlfinlab/mlfinpy; standard stack LightGBM/Optuna/NumPy/Pandas only").
