# Phase 5.5 Gate — iter-v3/102

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `OOS_CUTOFF_MS = 1742774400000`, `training_months = 24` explicitly stated as IMMUTABLE. IS window (first 24 months per symbol) and OOS window (2025-03-24 onward) named. All 4 EDA scripts verified IS-only (`open_time < OOS_CUTOFF_MS` mask present in `alpha_ic_eda.py` and `alpha_horserace_eda.py`). Walk-forward embargo fix (`e149e9d`) inherited unchanged.

- Section 1 (Hypothesis): PASS — One sentence, specific: the 14-feature stack lacks a vwap/price lead-lag term composed with a fast mean-reversion gap; Alpha#32 is exactly that composition; the held-out-tail horse race shows it lifts per-symbol predictive accuracy over a basket of 18 candidates. The hypothesis is specific enough to be falsified (T6/T7 dShACC, T8 per-symbol lift). Not vague.

- Section 2 (IS-Only Evidence): PASS — Committed EDA scripts at `analysis/iteration_v3-102/` (commits `fd3165a` + `6b917f8`). Tables T1–T10 present and verified against CSV outputs. Key tables spot-checked:
  - `T2_alpha_label_ic.csv` confirms alpha032 IC: BCH −0.0255 / LDO +0.0413 / TRX +0.0395, mean |IC| 0.0354.
  - `T3_past_only_audit.csv` confirms 0/54 causality failures (past_only_ok=True all rows).
  - `T6_horserace.csv` confirms alpha032 leads basket: dShACC_mean +0.01373 (rank 1/18), dPnL_mean +0.2214.
  - Numbers in brief match the CSV outputs exactly. Evidence is quantitative, not category-matching.
  - IS-only mask verified in both `alpha_ic_eda.py` line 193 and `alpha_horserace_eda.py` line 109.

- Section 3 (Proposed Changes): PASS — Enumerated: new module `formulaic_v3.py` with `compute_alpha032`, registry registration, `alpha032` as 15th element of `V3_FEATURE_COLUMNS_TOP_N`, `_verify_feature_columns` count update to 15, `ITERATION_LABEL` bump to `"v3-102"`, feature parquet regeneration. No label change, no model-arch change, no universe change, no risk-gate change stated explicitly. Single variable.

- Section 4 (Expected OOS Impact): PASS — Predicted OOS band [+0.24, +0.49] vs /060 anchor +0.1403; IS band [+0.78, +1.00]. Explicit 5-part falsifier table (F1–F5) with locked numerical thresholds. Behavioral-effect predictor (8–30% OOS roster change; <5% = INERT). Per `feedback_v3_per_symbol_target_axis_falsifier.md`, all 3 symbols have target-axis falsifiers: F3 explicitly covers BCH-only artifact with LDO+TRX regression gates; F5 covers the trade-selection sub-channel. The /101-closeout anchor-matching discipline is applied (anchor = /060, not /059).

- Section 5 (Risk Mitigation): PASS — R1–R5 explicitly addressed. Notes that the OOD gate operates on its own feature subset (not `V3_FEATURE_COLUMNS`), so adding `alpha032` does not enlarge OOD detection surface. T9 ADF-stationarity cited as evidence the feature does not drift the model. Simulated historical effect via T8 horse race (BCH +376.6, LDO +60.9, TRX −164.7 held-out PnL). Honest about concentration-amplifying tendency.

- Section 6 (Risk Management Design): PASS — Structural defense argument: single-feature addition is lowest-blast-radius test; the `feedback_v3_engineered_features_dont_stack.md` discipline is honored (only 1 feature added despite 18-alpha basket). ADF stationarity gate and causal `scale_ts` bounding discussed. Risks (concentration, thin CI) pre-registered as falsifiers/caveats rather than buried. Note: Section 6 does not present the 8-primitive gate-efficacy table (fire rates etc.) but that is a Phase-6 post-run requirement, not a pre-run gate requirement for brief Section 6.

- Section 7 (Failure-Mode Prediction): PASS — Three failure modes pre-registered in order: (1) INERT (F4 — modal predicted outcome, detailed reasoning including v3's 7-FEED STRUCTURAL VERDICT track record); (2) SUSPICIOUS via F5 (roster-churn sub-channel from /101 Lesson 2); (3) NEGATIVE (F1/F2/F3 — IS-collapse or BCH-only artifact). Section explains why the axis is worth a backtest despite CI straddling zero (positive point estimate on BOTH OOS-robust statistics, basket-best). Falsifiers are distinct from predictions.

- Section 8 (MERGE/NO-MERGE Criteria): PASS — Classification taxonomy with 6 named outcomes (BLOCKED, NEGATIVE, SUSPICIOUS, INERT, PROMISING, NULL-RESULT) evaluated in disjunctive-precedence order. Explicit numerical thresholds pre-registered: OOS < +0.00 → F1; IS < +0.60 → F2; BCH-only with LDO+TRX both regressing → F3; importance rank 15/15 all models or sub-parity all models → F4; duration-gap > +1.0 candles → F5. PROMISING gate: OOS Δ ≥ +0.20 vs /060 anchor AND IS ≥ +0.60. Baseline update policy respected (`BASELINE_V3.md` not edited by EXPLORATION).

- Section 9 (Library Stack): PASS — No new libraries. `compute_alpha032` uses numpy + pandas rolling (existing deps). Production library stack cited: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. Integration-test mandate explicit: unit tests (causality regression, formula correctness, NaN/range behavior), integration smoke test (parquet + LightGbmStrategy train with 15-feature stack), pre-flight verifications.

- Section 10 (QR Audit Trail): PASS — Axis is USER-DIRECTED (2026-05-18). QR studied the Kakushadze 2015 paper, ported 18 time-series-pure alphas with per-alpha adaptation documented in `alpha_lib.py`, selected by multivariate held-out-tail horse race (explicitly citing the /098 lesson against univariate IC ranking). `feedback_v3_engineered_features_dont_stack.md` compliance stated. Weaknesses (thin IC, middling sign-stability, BCH-led lift, CI straddling zero) recorded honestly. EDA commit SHAs cited.

## Reasons

No BLOCK items. All 10 sections are present and substantive. Section 2 evidence is numerical and backed by committed IS-only scripts. Section 4 falsifiers are specific (not vague), cover all 3 symbols including per-symbol target axes, and include a behavioral-effect predictor. Section 7 failure-mode predictions are pre-registered and include falsifier references. Section 8 classification is locked before the backtest runs.

Gate PASS — proceed to Phase 6.
