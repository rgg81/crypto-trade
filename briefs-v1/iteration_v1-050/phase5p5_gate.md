# Phase 5.5 Gate — iter-v1/050

OVERALL: BLOCK

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION

## Axis Family + Rotation Status
FAMILY: feature-family + risk-primitive (compound; single DOT-specialist mechanism)
ROTATION_STATUS: VALID — last 5 families: methodology, feature-family, feature-family,
feature-family, feature-family+risk-primitive. Not all 5 same family. Rotation discipline
honored.

## HIGH-RISK Declaration
HIGH-RISK: NO — additive feature (NORMAL-RISK) + post-prediction stateless gate (NORMAL-RISK).

## LM Master Response Verification
- briefs-v1/iteration_v1-050/lgbm_advisor.md exists: **BLOCK** — file is absent.
  Brief Section 3.3 claims a "cycle-6 velocity mandate" exempts LM advisor dispatch.
  No such rule is documented in ITERATION_PLAN_8H_V1.md, BASELINE_V1.md, or any
  memory/feedback file. ITERATION_PLAN_8H_V1.md §"Thirteen phases" states explicitly:
  "Four gates are MANDATORY: Phase 4.5, 5.5, 6.0, 7.5. Skipping any is a
  process-integrity violation." and §"Do NOT" section states "NEVER skip the Phase 4.5
  LM Master advisory". Self-asserted exemptions in the brief do not override the
  workflow spec.
- Brief Section 3 addresses LM Master recommendations: **BLOCK** (conditional on above —
  no lgbm_advisor.md means no recommendations to address; gate blocked regardless).

## Cadence Check
- Wall-clock budget declared: <= 2h for EXPLORATION: PASS
- CONFIRMATION only checks: N/A (EXPLORATION)

## /049 Mandate Override Check
Brief Section 0.0 states "/050 per user mandate: regime-specialist approach for DOT
(per user mandate 2026-06-01)" and Section 0.6 states "user mandate (2026-06-01) for
per-symbol regime-specialist EXPLORATIONs." diary-v1/iteration_v1-049.md §5 Path Forward
declared "/050 = model-arch axis (MANDATORY)" with one documented alternative:
"cycle-7 closure with /045 ALT_1 substrate multi-seed validation IF user override."
Brief claims user override occurred (feature-family + risk-primitive axis selected
instead of model-arch). This override is ASSERTED in the brief but cannot be verified
from code or documentation alone. If the user issued this override, the QR must add a
brief Section 0.7 (Override Declaration) with explicit user directive text + date, and
re-author the brief. Without documented evidence, the gate treats the mandate violation
as an ambiguity requiring QR clarification, not a hard BLOCK on its own — the hard BLOCKs
are the missing mandatory sections listed below.

## long_short_zscore_30 Presence Check (INFORMATIONAL)
V1_FEATURE_COLUMNS_PRUNED contains long_short_zscore_30 (46 total = 45 including
long_short_zscore_30 + 1 dot_vs_btc_ret_ratio_30). The exploration catalog's /049 row
states "feature REVERTED" but also says "handled in /050 setup." The /050 setup commit
(9af77db) did NOT remove long_short_zscore_30 — it was intentionally retained in the
45-column starting state. The brief counts 45→46 treating long_short_zscore_30 as
already present. This is a catalog-narrative vs code discrepancy but the code is
internally consistent. INFORMATIONAL — not a BLOCK.

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_MS=1742774400000 (2025-03-24), training_months=24
  immutable; IS and OOS windows named; DOTUSDT cohort + BTC klines for feature only.
- Section 0.5 (Iteration Type): PASS — EXPLORATION, cycle-6 slot 5/10.
- Section 0.6 (Architecture-Family Justification): PASS — last 5 families listed; compound
  feature-family+risk-primitive; VALID rotation.
- Section 1 (Hypothesis): PASS — specific: "flip DOT IS Sharpe from -1.23 to >= 0 via
  cross-asset idiosyncratic ratio + vol-spike gate."
- Section 2 (IS-Only Evidence): PASS — informational per EDA rule change bf2c812; DOT IS
  Sharpe/trades from BASELINE_V1.md; feature design rationale; vol-spike gate design;
  predicted IC. No committed analysis script required under EDA-informational mandate.
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — NORMAL-RISK declared with explicit
  reasoning for both mechanisms.
- Section 3 (Proposed Changes): CONDITIONAL PASS pending lgbm_advisor.md. Enumerated
  changes are substantive; LM Master response exemption claim BLOCKED.
- Section 4 (Expected OOS Impact): PASS — F-AXIS #1-#5 table with PROMISING/PARTIAL/
  NEG-CLEAN thresholds; explicit falsifiers; F-AXIS #5 marked informational only.
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 active per BASELINE_V1; new regime gate
  IS-calibrated with q75 IS-only threshold.
- Section 6 (Risk Management Design): PASS — 8-primitive table with fire-rate prediction.
- Section 7 (Failure-Mode Prediction): **MISSING** — section not present in brief.
- Section 8 (MERGE/NO-MERGE Numerical Criteria): **MISSING** — section not present in brief.
- Section 9 (Library Stack Declaration): **MISSING** — section not present in brief.

## Lint Audit (Phase 6.0 pre-commit check, run at gate time)
run_baseline_v1.py had 2 ruff errors introduced by the /050 dispatch block:
  - E501 line too long (comment at line 5616)
  - N806 uppercase variable _REGIME_GATE_CONF_THRESHOLD_050 (renamed lowercase)
Both fixed by QE at gate time. ruff check now passes. Tests still pass (13/13).

## Reasons (BLOCK)
1. **lgbm_advisor.md MISSING** — Phase 4.5 LM Master advisory is a MANDATORY gate per
   ITERATION_PLAN_8H_V1.md. Brief Section 3.3's "cycle-6 velocity mandate" exemption is
   self-asserted and has no documented basis in any workflow doc or memory file. QR must
   dispatch the LM Master (quant-lm-master role) with current context before authoring
   the brief, then ensure brief Section 3 addresses each Phase 4.5 recommendation.
2. **Section 7 MISSING** — Brief must include 1-2 paragraphs predicting how /050 most
   plausibly fails OOS: e.g., DOT IS Sharpe may flip positive from single-seed variance
   (not genuine signal); vol-spike gate may have insufficient IS coverage to learn from;
   single-symbol DOT IS sample (93 trades before gate) is too small for reliable
   attribution. This section is verified against Phase 8 diary outcomes.
3. **Section 8 MISSING** — Pre-registered MERGE/NO-MERGE numerical criteria are required
   before the backtest launches to prevent post-hoc rationalization. Must include locked
   thresholds, e.g. "PROMISING iff DOT IS Sharpe Δ >= +0.50 AND IS trades >= 50 AND
   gate fire-rate IS in [5%, 30%]." Must be written before any backtest output is seen.
4. **Section 9 MISSING** — Library Stack Declaration must enumerate which versions of
   mlfinlab/mlfinpy/pypbo/fracdiff are used or explicitly state they are absent with
   fallback. Required to catch library availability risks early.

## Path Forward for QR
1. Dispatch LM Master (Phase 4.5) with: BASELINE_V1.md, last 3 diaries
   (diary-v1/iteration_v1-047.md, -048.md, -049.md), brief Sections 1-3, and
   the cross_btc_v1.py module. Ask for: hyperparameter recommendations for DOT-only
   3-ENSEMBLE_SIZE run; feature-engineering risks for cross-asset ratio at 90-bar zscore;
   regime-gate calibration advice; saturation risks at n_trials=18 for DOT-only cohort
   (93 IS trades total). LM Master emits briefs-v1/iteration_v1-050/lgbm_advisor.md.
2. Add Section 7 (Failure-Mode Prediction): predict the most plausible failure mode for
   /050. At minimum: single-seed DOT IS variance will mask whether the feature adds
   genuine signal; vol-spike gate may not fire enough IS to produce observable Sharpe
   contribution at n_trials=18; cross-asset ratio warmup (90 bars = 30 days) reduces
   effective IS training sample from 93 to ~75 trades.
3. Add Section 8 (Pre-Registered MERGE/NO-MERGE Criteria): lock thresholds before
   backtest. For an EXPLORATION, typical form: "PROMISING iff F-AXIS #1 PASS (DOT IS
   Sharpe Δ >= +0.50) AND F-AXIS #3 PASS (gate fire-rate IS in [5%, 30%]) AND F-AXIS #4
   PASS (IS >= 50 trades)."
4. Add Section 9 (Library Stack Declaration): enumerate versions in use; if mlfinlab not
   available, state stdlib fallback for CPCV/PBO/PSR.
5. If the user override of the /049 model-arch mandate is real, add a brief Section 0.7
   with the exact user directive text and date so future readers can understand why /050
   chose feature-family+risk-primitive instead of model-arch.
6. Re-submit brief; QE re-runs Phase 5.5 gate.
