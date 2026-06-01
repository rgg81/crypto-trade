# Phase 5.5 Gate — iter-v1/054

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION
SUBTYPE: FEATURE-PRUNING (impulse-drop attribution test)

## Axis Family + Rotation Status
FAMILY: feature-family (feature-pruning sub-axis; DROP btc_funding_rate_8h_impulse)
ROTATION_STATUS: VALID — prior 5 families: feature-family × 2, feature-family+risk-primitive × 1,
  validation × 2. Not all same family. Axis Rotation Discipline NOT triggered.

## HIGH-RISK Declaration
HIGH-RISK: NO
RISK_CLASS: NORMAL-RISK — dropping one INERT feature (rank >30/48 in 3/3 seeds) from 48 → 47
  cols does NOT change Optuna's training-objective domain. Precedent: /040 DROP basis_zscore_30
  classified NORMAL-RISK at Phase 5.5.
Mitigation: N/A (NORMAL-RISK; single-seed=42 EXPLORATION standard applies).

## LM Master Response Verification
- briefs-v1/iteration_v1-054/lgbm_advisor.md exists: PASS
- Brief Section 3.4 addresses each LM Master recommendation: PASS
  - Rec 1 (primary falsifier thresholds): ADOPTED — Section 4 F-AXIS #1 pre-registers spread IS ≥ +0.16 / [0,+0.16) / <0 decision tree
  - Rec 2 (trade-rate floor IS ≥ 50; anomaly note if IS < 100): ADOPTED — Section 4 F-AXIS #2
  - Rec 3 (spread rank expected 3-7/47 informational): ADOPTED — Section 4 F-AXIS #3
  - Flag A (preserve compute_btc_funding_rate_8h_impulse in funding_v1.py): ADOPTED — Section 3.1 explicit statement
  - Flag B (parquet regen required): ADOPTED — Section 3.1 + Section 10.2 parquet regen instruction

## Cadence Check
- Wall-clock budget declared: ≤ 2h (EXPLORATION hard cap): PASS
- CONFIRMATION precedents: N/A (EXPLORATION iteration; cadence counter 9/10 for cycle-6)
- Section 3 lists imported variations from prior EXPLORATIONs: PASS — /052-/053 BTC specialist
  architecture fully documented; impulse-drop mandate from /053 PARTIAL-CONFIRMED explicit

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 declared; IS/OOS windows named
- Section 0.5 (Iteration Type, v1): PASS — TYPE: EXPLORATION, SUBTYPE: FEATURE-PRUNING declared
- Section 0.6 (Architecture-Family Justification, v1): PASS — family=feature-family, prior 5 families listed, ROTATION_STATUS=VALID
- Section 1 (Hypothesis): PASS — specific: "spread-alone IS ≥ +0.16 within ±0.05 of /052's both-feature IS Sharpe; impulse contributes 0-5% genuine signal"
- Section 2 (IS-Only Evidence): PASS — committed analysis script `analysis/iteration_v1-054/attribution_impulse_drop.py`; multi-seed attribution tables from /053 reports (IS data only); impulse rank >30 in 3/3 seeds confirmed; spread rank 4-10 confirmed
- Section 2.5 (HIGH-RISK Axis Declaration, v1): PASS — RISK_CLASS: NORMAL-RISK declared with precedent cited
- Section 3 (Proposed Changes): PASS — enumerated: DROP impulse from V1_FEATURE_COLUMNS_PRUNED (48→47); KEEP spread; preserve funding_v1.py code; parquet regen BTCUSDT only; LM Master Rec/Flag responses all addressed
- Section 4 (Expected OOS Impact): PASS — F-AXIS #1 primary falsifier with spread IS ≥/∈/< thresholds; F-AXIS #2 trade-rate floor; F-AXIS #3 spread rank informational; OOS prediction with CI noted informational
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 configuration unchanged; feature-drop risk NORMAL-RISK documented
- Section 6 (Risk Management Design): PASS — 8-primitive table present with IS fire-rate predictions
- Section 7 (Failure-Mode Prediction, v1): PASS — 4 failure modes pre-registered (MARGINAL 35%, DEGRADES 15%, CONFIRMED-BUT-OOS-NEG informational, RANK-REGRESSION informational) with diagnostics and gates
- Section 8 (MERGE/NO-MERGE Criteria, v1): PASS — 3-verdict catalog table pre-registered (CONFIRMED/MARGINAL/DEGRADES) with CONFIRMATION gates deferred to /055
- Section 9 (Library Stack, v1): PASS — all libraries listed with versions; mlfinlab/pypbo fallbacks declared

## Reasons (if BLOCK)
N/A — OVERALL: PASS

## Notes
- This is cycle-6 EXPLORATION 9/10. One more EXPLORATION slot remains before /055 CONFIRMATION can launch.
- /053 PARTIAL-CONFIRMED closed at mean IS Δ +0.8102 (just 0.04 short of +0.85 SPECIALIST threshold). The
  /054 impulse-drop test resolves the attribution question before /055 CONFIRMATION bundle composition.
- The analysis script `analysis/iteration_v1-054/attribution_impulse_drop.py` must be committed alongside
  this brief as evidence for Section 2 (IS-Only Numerical Evidence). It reads from /053 reports (IS only).
- Parquet regen (BTCUSDT only) is required before the backtest. The 47-col features-base-hash
  (f19392b27f00b707c3da8686d2dc14ab367f8d7460e977be18a8f7386c70ce56) differs from the 48-col hash
  (106003ea8f1779b3ac3e1c051ee4c7097847f52f33e4820010951453570e6660). Runner hash guard enforces this.
