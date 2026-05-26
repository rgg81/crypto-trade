# Phase 5.5 Gate — iter-v1/022

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-3 #7 of 10)

## Axis Family + Rotation Status
FAMILY: per-cohort-specialization-LTC (NEW 14th family — first usage)
ROTATION_STATUS: VALID

Prior 5 EXPLORATION families (from exploration_catalog.md entries /017-/021):
- /017: universe
- /018: per-cohort-specialization-LINK
- /019: per-cohort-specialization-ETH
- /020: per-cohort-specialization-BTC
- /021: methodology-pivot (REUSE family: methodology)

None of the prior 5 are `per-cohort-specialization-LTC`. LTC is a distinct COHORT from
LINK/ETH/BTC; cohort identifier is the rotation differentiator per /018-/020 closeout codified rule.
ROTATION_STATUS=VALID confirmed.

## HIGH-RISK Declaration
HIGH-RISK: YES
Declared reason: universe collapses from 5 symbols to 1 AND post-hoc gate alters realized trade
stream — both changes modify Optuna training-objective domain vs baseline.
Mitigation: NONE opted-in (single-seed-style EXPLORATION at ENSEMBLE_SIZE=3; multi-seed deferred to
/027 CONFIRMATION per cycle-3 default).

## LM Master Response Verification
- briefs-v1/iteration_v1-022/lgbm_advisor.md exists: PASS (committed at 79fd7fa, 91 lines)
- Brief Section 3.4 addresses each LM Master recommendation: PASS

  LM Master advisory has 9 numbered sections + Closing (§1-§9 + Closing). Section 3.4 responses:
  - §1 (H2 REFUTATION binding): 3.4.1 — ADOPTED
  - §2 (ORACLE EDA caveat): 3.4.2 — ADOPTED
  - §3 (verdict priors 8/12/40/20/10/10): 3.4.3 — ADOPTED
  - §4 (F-AXIS #2 sub-band + F-AXIS #3 LOAD-BEARING): 3.4.4 + 3.4.5 — ADOPTED
  - §5 (n_eff band [4,10]): 3.4.6 — ADOPTED
  - §6 (Jaccard [0.03, 0.20] modal 0.06): 3.4.7 — ADOPTED
  - §7 (/023+ verdict-conditional staging): 3.4.8 — ADOPTED
  - §8 (F-AXIS #3 supersedes F1 hierarchy): 3.4.9 — ADOPTED
  - §9 (/027 3-specialist bundle +1.20-1.50): 3.4.10 — ADOPTED
  - Closing (Critic Phase 7.5 4 priority items): 3.4.11 — ADOPTED; Section 10.6 NEW created

  Summary table at 3.4.12 lists 11 LM edits, 0 rejections. Every LM section addressed.

## Cadence Check
- Wall-clock budget declared: 26 minutes — within 2h EXPLORATION cap: PASS
- EXPLORATION #7 of 10 — valid position (CONFIRMATION earliest at /027): PASS
- (CONFIRMATION only) N/A

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 confirmed at config.py line 7; training_months=24 confirmed at runner line 349; IS window 2023-03-24 to 2025-03-24 (24 months); OOS window 2025-03-24 onwards. Named in brief Section 0.
- Section 0.5 (Iteration Type): PASS — TYPE: EXPLORATION; cycle-3 #7 of 10 declared at Section 0.1; 2h wall-clock cap at Section 3.6.
- Section 0.6 (Architecture-Family Justification): PASS — family `per-cohort-specialization-LTC` declared; prior 5 enumerated with catalog verification; ROTATION_STATUS=VALID; one-sentence rationale present.
- Section 1 (Hypothesis): PASS — single specific H1: LTC-only + stateless long-suppression gate at -4% will flip LTC OOS per-trade Sharpe from -0.27 toward neutral-or-positive; specific falsification bands defined; H2 explicitly labeled INFORMATIONAL only.
- Section 2 (IS-Only Evidence): PASS — numerical tables from analysis/iteration_v1-022/*.py scripts committed at 4eb091d; per-trade direction breakdown, OOS monthly distribution, IS half-split, exit-reason mix, ORACLE EDA gate fire rates — all concrete numbers, no category-matching.
  committed script: analysis/iteration_v1-022/ltc_prior_class.py + ltc_directional_btc_trend_analysis.py
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — HIGH-RISK declared with reason; mitigation=NONE (single-seed EXPLORATION); cumulative HIGH-RISK tracker present.
- Section 3 (Proposed Changes): PASS — enumerated changes to 2 src/ files (risk_v2.py + run_baseline_v1.py); pinned values at 3.3; LM Master responses at 3.4 (all 11 adopted, 0 rejected).
- Section 4 (Expected OOS Impact): PASS — F1 OOS per-trade Sharpe Δ bands with absolute thresholds; F-AXIS-MECHANISM #1-#4 all present; LOAD-BEARING markers on F-AXIS #3; specific falsifier: OOS per-trade Sharpe ≤ -0.55 → NEGATIVE-CATASTROPHIC.
- Section 5 (Risk Mitigation): PASS — verdict prior distribution 8/12/40/20/10/10 (LM Master recalibrated); high-probability modal cell INERT 40%; mechanism predictions informational only.
- Section 6 (Risk Management Design): PASS — 8 failure-mode sub-sections; gate deadlock impossibility stated; stateless design verified; PROMISING-MECHANICAL adjacency check flagged.
- Section 7 (Failure-Mode Prediction): PASS — forward-looking failure modes 6.1-6.8 including basin-relocation, gate over-kill/under-fire, LTC-intrinsic drag, PROMISING-MECHANICAL adjacency, wall-clock breach.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 11-cell verdict matrix with locked numerical thresholds per section 1 falsification logic; hierarchy rule (NEGATIVE-DISPATCH > NEGATIVE-OVER/UNDER-FIRE > ...); anchor frame integrity note; pre-registered BEFORE backtest.
- Section 9 (Library Stack): PASS — no new library dependencies; mlfinlab/pypbo/fracdiff/statsmodels/lightgbm/optuna versions inherited from cycle-3 baseline; risk_v2.py re-use noted as backward-compatible kwarg addition.

## Data Freshness (Pre-Flight)
- data/LTCUSDT/8h.csv: age=3.5h — FRESH (< 16h threshold)
- data/BTCUSDT/8h.csv: age=11.5h — FRESH (< 16h threshold)
- data/features/LTCUSDT_8h_features.parquet: EXISTS

## walk_forward.py Line 113 Verification
Line 113 carries `train_end_ms = test_start_ms - embargo_ms` — UNCHANGED. PASS (confirmed via
grep on source file at HEAD).

## Reasons (if BLOCK)
None — OVERALL=PASS.
