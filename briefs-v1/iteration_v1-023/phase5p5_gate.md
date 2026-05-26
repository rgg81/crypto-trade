# Phase 5.5 Gate — iter-v1/023

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-3 #8 of 10)

## Axis Family + Rotation Status
FAMILY: feature-family (NEW 15th family — first feature-family axis in cycle-3)
Prior 5 EXPLORATION families (going into /023):
  - /018: per-cohort-specialization-LINK
  - /019: per-cohort-specialization-ETH
  - /020: per-cohort-specialization-BTC (mapped as per-cohort-specialization-BTC in catalog)
  - /021: methodology-pivot
  - /022: per-cohort-specialization-LTC
`feature-family` is absent from all 5 prior families.
ROTATION_STATUS: VALID

## HIGH-RISK Declaration
HIGH-RISK: YES
Mitigation: none opted-in (single-seed=42 EXPLORATION budget; multi-seed opt-out justified
in brief Section 2.5 — 2h EXPLORATION HARD CAP + v3 4-data-point INERT precedent means
multi-seed does not address INERT-by-importance failure mode).
Count of HIGH-RISK single-seed EXPLORATIONs with >1σ negative delta in cycle-3:
  - /014 labeling HIGH-RISK: NEGATIVE (1 of 2)
  - /015 CONFIRMATION-spec HIGH-RISK: CONFIRMATION-NEGATIVE catastrophic (2 of 2 if counted; 
    spec was CONFIRMATION not EXPLORATION)
/023 is the 3rd cycle-3 HIGH-RISK at single-seed EXPLORATION; if NEG-CAT, /024 becomes 
mandatorily multi-seed per brief Section 11.5.

## LM Master Response Verification
- briefs-v1/iteration_v1-023/lgbm_advisor.md exists: PASS
  (present at commit 9c6c32f, Phase 4.5 section with 9 numbered recommendations)
- Brief Section 3.4 addresses each LM Master recommendation: PASS
  - §1 (v3 closure doesn't bind v1): ADOPT — brief Section 0.4 already cites 4-data-point catalog
  - §2 (ORACLE EDA downgrade): ADOPT — Section 1 caveat + Section 2.7 expanded
  - §3 (Verdict priors recalibrated 12/8/52/18/8/2): ADOPT — Section 5.1 priors REPLACED
  - §4 (F-AXIS #1 gain-share check CRITICAL): ADOPT — Section 4.2 F-AXIS #1 rewritten with dual gate
  - §5 (n_eff band [5,10]): ADOPT — Section 4.2 F-AXIS-MECHANISM #3 updated
  - §6 (/024+ verdict-conditional pre-staging): ADOPT — Section 11.7 new staging matrix
  - §7 (pool Model A architectural advantage probably not decisive): ADOPT — Section 5 modal INERT reflects
  - §8 (/027 bundle composition): ADOPT — Section 11.6 updated
  All 8 recommendations addressed. None REJECTED. PASS.

## Cadence Check
- Wall-clock budget declared: 35-45 min (Section 0.7) < 2h EXPLORATION HARD CAP: PASS
- EXPLORATION type, no CONFIRMATION cadence check required

## Per-Section Status
- Section 0 (Data Split): PASS
  OOS_CUTOFF_DATE = 2025-03-24 confirmed (Section 0.3 anchor table + comparison.csv reference).
  training_months = 24 (implied by anchor comparison.csv source = BASELINE_V1.md).
  IS window and OOS window are absolute-date anchored in Section 0.3.
- Section 0.5 (Iteration Type, v1/v3): PASS
  Declared EXPLORATION cycle-3 #8 of 10. Prior EXPLORATIONs /016-/022 enumerated.
- Section 0.6 (Architecture-Family Justification, v1-only): PASS
  Family = feature-family. Prior 5 listed. VALID rotation confirmed above.
- Section 1 (Hypothesis): PASS
  One mechanism-level sentence: adds funding_rate_zscore_30 + funding_rate_zscore_90 to
  V1_FEATURE_COLUMNS_PRUNED (40→42); pool Model A joint loss surface encodes positioning-
  crowding signal via cross-cohort splits (untested in v3). Specific mechanism + expected
  direction of lift + ORACLE EDA caveat per LM Master §2. Not vague.
- Section 2 (IS-Only Evidence): PASS
  Tables produced by committed analysis scripts at analysis/iteration_v1-023/ (commit c3f4551
  per brief). Scripts present: funding_eda.py, funding_oracle_eda.py, v3_prior_assessment.py.
  CSVs present: funding_availability.csv, funding_distribution.csv, funding_zscore_ic.csv,
  funding_regime.csv, funding_oracle_band_attribution.csv, funding_oracle_direction_attribution.csv,
  funding_v3_prior_assessment.csv. IS-only filter confirmed (funding_regime.csv labels "IS bars"
  in Section 2.2 table header). No category-matching — concrete numbers throughout.
- Section 2.5 (HIGH-RISK Axis Declaration, v1-only): PASS
  Declared HIGH-RISK. Reason: new data source + Optuna domain change (V1_FEATURE_COLUMNS_PRUNED
  40→42) + 4-data-point v3 NEGATIVE precedent. Multi-seed opt-out justified with specific
  rationale. PASS.
- Section 3 (Proposed Changes): PASS
  3.1: NEW file src/crypto_trade/features_v1/funding_v1.py (functions specified).
  3.2: V1_FEATURE_COLUMNS_PRUNED extension 40→42 with insertion positions identified.
  3.3: Runner wiring (feature-load path, assertion).
  3.4: LM Master responses (all 8 ADOPTED with brief-section traceability). PASS.
- Section 4 (Expected OOS Impact): PASS
  F1 OOS Sharpe Δ ≥ +0.10 → PROMISING threshold with explicit falsifier in Section 8.
  F-AXIS-MECHANISM #1-4 with DUAL GATE (rank + gain-share per LM Master §4) specified.
  Explicit falsifier: F1 Δ ≤ -0.55 → NEGATIVE-CATASTROPHIC. PASS.
- Section 5 (Risk Mitigation): PASS
  Risk priors stated: 12/8/52/18/8/2 (LM Master recalibrated). Mass-shifting catalysts.
  R1/R2/R3 unchanged (no risk primitive changes). Not a risk-primitive axis. PASS.
- Section 6 (Risk Management Design): PASS
  Failure modes A-E catalogued with diagnostic and cycle-3 implications per mode.
  Covers INERT (modal A), NEGATIVE-clean (B), PROMISING-clean (C), PROMISING-INERT-FAV (D),
  sample-size-too-small (E). Fire-rate predictions not applicable (no new gate). PASS.
- Section 7 (Failure-Mode Prediction, v1/v3): PASS
  Section 7 pre-registers: LM Master Phase 4.5 adjudication of priors (Section 7.1) +
  pre-committed verdict-mass-shifting rules (Section 7.2). Forward-looking failure mode
  predictions are embedded in Section 6 modes A-E (each with "Implication for cycle-3"
  subsection). LM Master §4 FIRED and recalibrated priors are already adopted. PASS.
- Section 8 (MERGE/NO-MERGE Criteria, v1/v3): PASS
  10-row verdict matrix. Explicit numerical thresholds per row. F1 OOS Sharpe Δ + F3 IS
  Sharpe Δ + F-AXIS #1 (rank + gain-share DUAL GATE per LM Master §4) + n_eff per row.
  NO-MERGE conditions enumerated (rows 5-10). Pre-registration complete. PASS.
- Section 9 (Library Stack, v1/v3): PASS
  pandas>=2.0, numpy>=1.24 (existing). No new external dependencies. Funding fetch CLI
  exists. Existing test suite reference. No library fallbacks needed. PASS.

## Summary
All 13 mandatory sections verified. LM Master advisory present + all 8 recommendations
addressed. Rotation status VALID (feature-family not in prior 5). HIGH-RISK declared with
single-seed opt-out rationale. EDA scripts committed. F-AXIS #1 DUAL GATE (rank + gain-share)
properly specified per LM Master §4 critical recommendation.

Data freshness note (informational — for Phase 6 pre-flight):
  data/funding_rates/BTCUSDT.csv last timestamp: 1779062400007 ms (~214h old as of gate
  check). Funding data requires re-fetch before backtest per 16h staleness rule.
  Command: uv run crypto-trade fetch-funding --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT
  This is not a Phase 5.5 block — data freshness is verified and corrected at Phase 6.

## Reasons (if BLOCK)
N/A — OVERALL: PASS
