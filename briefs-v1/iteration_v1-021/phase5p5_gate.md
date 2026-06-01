# Phase 5.5 Gate — iter-v1/021

OVERALL: PASS

## Iteration Type (from Brief Section 0.5 / Section 0)
TYPE: EXPLORATION — cycle-3 #6 of 10
SUBTYPE: METHODOLOGY PIVOT (diagnostic; no directional-Sharpe-improvement backtest)

## Axis Family + Rotation Status
FAMILY: methodology-pivot (NEW 12th family in v1 catalog — first usage; convergent recommendation per Section 0.2 three-role consensus: /020 Critic Phase 7.5 Path Forward #1 + /020 LM Master Phase 7.4 §5 hybrid Option C+B + /019 LM Master Phase 7.4 §6 outstanding gap)
ROTATION_STATUS: VALID — `methodology-pivot` is in NONE of the prior 5 EXPLORATION families:
  - /016: sample-weighting
  - /017: universe
  - /018: per-cohort-specialization-LINK
  - /019: per-cohort-specialization-ETH
  - /020: per-cohort-specialization-BTC (diary not yet committed to exploration_catalog.md — acceptable at gate; /020 closeout is /020's scope; axis rotation valid regardless)

Note: exploration_catalog.md ledger ends at /019. The brief correctly declares /020 as per-cohort-specialization-BTC per the iteration branch record. Phase 5.5 accepts this on the basis that the /020 iteration ran and closed on branch iteration-v1/020 (tag v0.v1-020 per branch HEAD reference in brief). The gap in catalog is /020 diary/closeout debt, not a /021 gate issue.

## HIGH-RISK Declaration
HIGH-RISK: NO (NORMAL-RISK declared in Section 2.5)
Justification: src/ changes are PURELY ADDITIVE — (a) `params_persist_path` adds a new optional parquet flush after `study.optimize` completes (no-op when None); (b) `_write_feature_importance` adds a report-emission-only function post-training. Neither change alters Optuna's training-objective domain, feature set, labeling, universe, or risk gates.

## LM Master Response Verification
- briefs-v1/iteration_v1-021/lgbm_advisor.md exists: PASS (101 lines, Phase 4.5 section present)
- Brief Section 3.4 addresses each LM Master recommendation: PASS

  Verification per recommendation:
  1. Rec #1 (H1 priors recalibrated 55→45 / 30→40 / 15→15): ADDRESSED in Section 3.4 Rec #1 (ADOPTED) + Section 5 priors updated to 45/40/15
  2. Rec #2 (REJECT n_trials=3 re-run AND log-grep; mandate §3.1 implementation): ADDRESSED in Section 3.4 Rec #2 (ADOPTED) + Section 3.1 introduction anchors §3.1 as the substrate and explicitly rejects both alternatives
  3. Rec #3 (F-AXIS-MECHANISM #1 THREE-LAYER TEST: Layer A ≥168 rows / Layer B bit-identical / Layer C 10-param non-null): ADDRESSED in Section 3.4 Rec #3 (ADOPTED) + Section 4.4 amended with three-layer table
  4. Rec #4 (feature importance = mean gain, `importance_type='gain'`): ADDRESSED in Section 3.4 Rec #4 (ADOPTED) + Section 3.2 LOCKED to `importance_type='gain'`
  5. Rec #5 (/022 conditional staging: HIGH-CONFIDENCE gate ≥6/10 params + ≥2 of {confidence_threshold, n_estimators, num_leaves, min_child_samples} → accelerated /022=/027): ADDRESSED in Section 3.4 Rec #5 (ADOPTED) + Section 11.7 amended with HIGH-CONFIDENCE threshold separation
  6. Rec #6 (directional call — §3.1 IS the substrate): ADDRESSED in Section 3.4 Rec #6 (ADOPTED) + Section 3.1 introduction opens with LM Master §6 framing
  7. Rec #7 (/027 bundle = Option β: FULL POOL preserved + specialists as alpha-enhancement): ADDRESSED in Section 3.4 Rec #7 (ADOPTED) + Section 11.6 bundle table amended
  8. Closing 5-item Critic Phase 7.5 checklist: ADDRESSED in Section 3.4 Closing-response (ADOPTED) + Section 10.5 amended with 5-item list

## Specific Check: LM Master Mandates Verified Against Brief
- Methodology LOCKED to `params_persist_path` (NOT n_trials=3 re-run, NOT log-grep): PASS — Section 3.1 intro + Section 3.4 Rec #2 explicit
- Feature importance LOCKED to `importance_type='gain'`: PASS — Section 3.2 explicitly states "LOCKED to importance_type='gain'"
- F-AXIS #1 = THREE-LAYER TEST (Layer A ≥168 rows, Layer B BASELINE bit-identical, Layer C 10/10 params non-null): PASS — Section 4.4 table with all three layers
- Section 5 priors 45/40/15: PASS — Section 5 states exactly "DIAGNOSTIC-CONFIRMED 45% / DIAGNOSTIC-MIXED 40% / DIAGNOSTIC-REFUTED 15%"
- Section 11.6 bundle architecture = Option β: PASS — Section 11.6 explicitly states "Option β FULL POOL + alpha-enhancement specialists (LM Master Phase 4.5 §7, ADOPTED)"
- Section 11.7 /022 routing per LM Master §5 HIGH-CONFIDENCE thresholds: PASS — Section 11.7 separates H1-CONFIRMED-floor (≥4/10) from /022-ACCELERATION-floor (≥6/10 + ≥2 key-params) per LM Master Rec #5
- Section 10.5 Critic Phase 7.5 checklist = LM Master Closing 5-item list: PASS — Section 10.5 enumerates all 5 items: Layer A buffer flush completeness / Layer B determinism / Layer C 10-param visibility / H1 falsifier evaluation / H2 Spearman rank correlation

## Cadence Check
- Wall-clock budget declared: ≤60 min HARD CAP (target ≤30 min for backtest): PASS (Section 10.1)
- EXPLORATION budget: PASS (not CONFIRMATION; no cadence count required)
- Cycle position: cycle-3 #6 of 10 — CONFIRMATION earliest at /027 (or /022 if H1 HIGH-CONFIDENCE CONFIRMED): PASS

## Per-Section Status
- Section 0 (Data Split): PASS — Section 3.6 explicitly confirms OOS_CUTOFF_DATE=2025-03-24 IMMUTABLE + training_months=24 IMMUTABLE; Section 0 declares "cycle-3 EXPLORATION #6 of 10" and positions iteration in context
- Section 0.5 (Iteration Type, v1): PASS — "EXPLORATION (cycle-3 #6 of 10) — METHODOLOGY PIVOT subtype" declared in opening header
- Section 0.6 (Architecture-Family Justification, v1-only): PASS — methodology-pivot family declared; prior 5 verified; VALID rotation; one-sentence rationale provided; NEW family declaration follows /012-precedent with 3-role convergence
- Section 1 (Hypothesis): PASS — TWO hypotheses: H1 (training-time pool-anchor mechanism via Optuna best-trial parameter delta BTC-in-pool vs BTC-only) AND H2 (feature importance signature divergence per-cohort); both mechanistic and specific; falsifiers pre-registered
- Section 2 (IS-Only Evidence): PASS — committed EDA scripts at analysis/iteration_v1-021/ (commit f6a7632); script 01 (three_cohort_outcome_table.csv), script 02 (oof_per_month_summary_stats.csv + oof_per_month_best_trial_proxy.csv), script 03 (h1_verdict_class_priors.csv + h2_verdict_class_priors.csv + h1_h2_pre_registration_predictions.csv); Section 2.6 justifies why IS-only (OOF parquets from prior iterations are IS-window data; script 02 does NOT access OOS data)
- Section 2.5 (HIGH-RISK Axis Declaration, v1-only): PASS — NORMAL-RISK declared; src/ changes enumerated as purely additive (1-4); explicit confirmation that Optuna objective/bounds/feature/label/universe/risk unchanged
- Section 3 (Proposed Changes): PASS — Section 3.1 (params_persist_path spec), 3.2 (_write_feature_importance spec + importance_type='gain' LOCKED), 3.3 (analysis script spec), 3.4 (all 7 LM Master recommendations addressed + Closing), 3.5 (H2 analysis script spec), 3.6 (explicit NO-CHANGE list)
- Section 4 (Expected OOS Impact — repurposed as Falsifiers): PASS — Section 4 contains complete H1 falsifier table (10 params × direction × threshold × channel), H2 falsifier table (Spearman ρ bands), joint H1×H2 verdict matrix (9 cells), and F-AXIS-MECHANISM #1 THREE-LAYER TEST with BLOCK verdicts
- Section 5 (Risk Mitigation — repurposed as Predicted Verdict-Class Priors): PASS — H1 priors 45/40/15 (recalibrated per LM Master §1); H2 priors 70/20/10; joint modal prior; Bayesian update plan for /022 routing
- Section 6 (Risk Management Design — repurposed as Failure Modes): PASS — 6 failure modes: diagnostic noise at single-seed, feature importance noise at n=24 months, wall-clock overrun, LM Master directional track concern, determinism risk, engineering_report.md timing incident
- Section 7 (Pre-Registered Failure-Mode Prediction, v1): PASS — 9-row table of observation → pre-registered interpretation for both H1 and H2 failure modes; prevents post-hoc rationalization in Phase 8 diary
- Section 8 (MERGE/NO-MERGE Criteria, v1): PASS — explicit: "/021 does NOT update BASELINE_V1.md regardless of outcome"; trade-roster determinism gate is the only merge-style criterion; verdict mapping DIAGNOSTIC-CONFIRMED/MIXED→PROMISING-METHODOLOGY / DIAGNOSTIC-REFUTED→NEGATIVE
- Section 9 (Library Stack, v1): PASS — no new library additions; existing libs confirmed (lightgbm, optuna, pandas, scipy.stats.spearmanr via scipy 1.13+)

## Additional V1-Only Checks
- walk_forward.py:113 unchanged: NOT modified in this iteration (additive changes only in optimization.py + run_baseline_v1.py). PASS
- labeling.py unchanged: NOT touched. PASS
- V1_FEATURE_COLUMNS_PRUNED unchanged (Section 3.6 explicit): PASS
- OOS_CUTOFF_DATE sacred constant: PASS
- training_months=24 sacred constant: PASS
- Ensemble seeds [42] (single-seed EXPLORATION): Section 3.6 confirms no seed change. PASS

## Data Freshness Pre-Note (for QE Phase 6)
Data freshness check at gate time:
- BTCUSDT/8h.csv: age ~8h [FRESH]
- ETHUSDT/8h.csv: age ~88h [STALE — requires re-fetch before backtest]
- LINKUSDT/8h.csv: age ~88h [STALE — requires re-fetch before backtest]
- LTCUSDT/8h.csv: age ~88h [STALE — requires re-fetch before backtest]
- DOTUSDT/8h.csv: age ~88h [STALE — requires re-fetch before backtest]

QE MUST re-fetch ETH/LINK/LTC/DOT before running the /021 backtest and re-generate features for all 5 symbols.

## Reasons (if BLOCK)
N/A — OVERALL=PASS
