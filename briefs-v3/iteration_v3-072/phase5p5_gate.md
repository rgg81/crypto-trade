# Phase 5.5 Gate — iter-v3/072

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 declared IMMUTABLE. IS/OOS windows in absolute dates. Walk-forward embargo unchanged (compute_embargo_candles(10080,480)=22, REQUIRED_GAP=66).
- Section 0.5 (Iteration Type): PASS — TYPE: EXPLORATION, cycle 2 #2 of 10. Axis category: STRUCTURAL (Category 3, NEW labeling). Run mode --exploration, EXPLORATION_ENSEMBLE_SIZE=3, --n-trials 35.
- Section 1 (Hypothesis): PASS — ONE sentence: replacing ATR triple-barrier with fixed-horizon return-sign label at 21-candle horizon lifts both IS and OOS monthly Sharpe vs /060 anchor by giving M1 a directionally cleaner training target. Specific mechanism (barrier path-noise vs net-drift), specific target (LDO 69% SL-saturated), specific magnitude (EDA shows +30-48% directional-spread improvement at matched horizon). Not vague.
- Section 2 (IS-Only Evidence): PASS — EDA committed at SHA 5da9b1b. Script: analysis/iteration_v3-072/axis_selection_eda.py + 6 output CSVs. All tables computed on IS-window candles only (open_time < 2025-03-24). Section 2.1 T0 anchor byte-exact from reports-v3/iteration_v3-060/comparison.csv. Section 2.2 label distribution (IS, all candles). Section 2.3 TB-vs-FH agreement (18-23% disagree on material moves). Section 2.4 label economics (FH-21 spread 30-48% larger at matched horizon — THE DECISIVE TABLE). Section 2.5 LDO barrier diagnosis (69% SL-saturated, 41% already fixed-horizon). Section 2.6 AXIS 2 rejection evidence (funding z-score AUC-0.5 max 0.0347 — near-zero). Section 2.10 anchor confirmation. Category-matching not used; all evidence is numeric from committed scripts.
- Section 3 (Proposed Changes): PASS — ONE substantive change (fixed-horizon return-sign label at 21-candle horizon, all 3 v3 models). Section 3.1 code edits enumerated exactly: labeling.py label_mode param, lgbm.py thread-through, metalabeling.py thread-through, run_baseline_v3.py label_mode="fixed_horizon" + ITERATION_LABEL bump + pre-flight assertion. Section 3.2 disambiguation: label barriers (changed) vs trade-exit barriers (UNCHANGED). No feature added/removed, no risk gate changed, no universe change. Single-axis discipline preserved.
- Section 4 (Expected OOS Impact): PASS — PROMISING-AT-EXPLORATION: IS Δ ≥ +0.10 (IS ≥ +0.9325) AND OOS Δ ≥ +0.20 (OOS ≥ +0.3403) AND frac_positive_paths ≥ 0.50. NEGATIVE: IS Δ < -0.10 OR OOS Δ < -0.20 (disjunctive OR). INERT: noise bands. Section 4.4 SUSPICIOUS gate pre-registered (OOS/IS > 3.0; SUSPICIOUS-OOS-DOMINANT sub-mode). Section 4.5 behavioral-effect predictor (IS trade roster changes by ≥15%; saturation falsifier specified if IS count within ±3 of 159 AND per-symbol within ±3 AND IS Sharpe within ±0.03 of +0.8325). Section 4.6 per-symbol Δ prediction (LDO target, BCH fragility, TRX). Section 4.7 BCH IS concentration sensitivity check pre-registered.
- Section 5 (Risk Mitigation): PASS — R1-R3 / 7-primitive gate stack UNCHANGED. Risk-relevant consequences of label change documented (removes downside-asymmetry from training signal; trade-exit barriers UNCHANGED). MaxDD watch pre-registered. Look-ahead audit: fixed-horizon scans forward same as triple-barrier; embargo 22 candles strictly covers 21-candle label horizon.
- Section 6 (Risk Management Design): PASS — 8-primitive table present. All 7 active gates shown as UNCHANGED with identical fire-rate prediction. Meta-labeling M2 (8th slot) not active for this iteration. Regime coverage identical to /060.
- Section 7 (Failure-Mode Prediction): PASS — 3 failure modes pre-registered with probabilities: NEGATIVE 35% (fixed-horizon discards load-bearing path info → IS Sharpe regression), SUSPICIOUS-OOS-DOMINANT 10% (labeling suits trending OOS but not choppy IS), INERT 30% (label is cleaner but tree cannot convert to better prediction). PROMISING 25%. Mechanism for each. What gates catch which failure. Process predictions P1-P3 included.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — All thresholds LOCKED. Section 8.1 PROMISING-AT-EXPLORATION conjunctive AND. Section 8.2 NEGATIVE disjunctive OR. Section 8.3 INERT + NULL-RESULT sub-flavor. Section 8.4 SUSPICIOUS disjunctive gate with OOS/IS > 3.0 AND SUSPICIOUS-OOS-DOMINANT clauses. Section 8.5 trade-rate floor (52-trade OOS floor for thin-sample flag). Classification precedence stated. Cannot be post-hoc renegotiated.
- Section 9 (Library Stack): PASS — No new external dependency. Fixed-horizon is pure-Python change inside label_trades. Stack pinned: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. Integration-test mandate carve-out documented (labeling-definition change, not methodology-only computed-field axis). New unit test test_fixed_horizon_label_mode specified.
- Section 10 (QR Audit Trail): PASS — EDA SHA 5da9b1b. Axis choice QR-driven with quantitative rejection of both competing candidates (AXIS 2 distinct-feature M2: AUC evidence; AXIS 3 LDO replacement: deferred per priority ordering). For-vs-against reasoning quantitative. Horizon choice (21 candles) justified: keeps embargo/REQUIRED_GAP byte-identical. Honest caveat on NEGATIVE failure mode.

## Implementation Verification

**ITERATION_LABEL**: "v3-072" — PASS (run_baseline_v3.py:128)

**label_mode default = "triple_barrier"**: PASS — labeling.py:143 signature `label_mode: str = "triple_barrier"`; v1/v2 callers unchanged; test_triple_barrier_default_unchanged confirms byte-identity.

**label_mode = "fixed_horizon" on v3 models**: PASS — run_baseline_v3.py common_kwargs `label_mode="fixed_horizon"` at line ~1486; pre-flight assertion at _verify_model_config validates _p13_lgbm.label_mode == "fixed_horizon" before backtest.

**REQUIRED_GAP = 66 UNCHANGED**: PASS — label horizon stays 21 candles (timeout_minutes=10080 unchanged); compute_embargo_candles(10080,480)=22; REQUIRED_GAP=(21+1)*3=66. Verified in run_baseline_v3.py _verify_label_leakage_gap.

**Embargo unchanged**: PASS — walk_forward.generate_monthly_splits uses compute_embargo_candles(10080,480)=22; train_end_ms=test_start_ms-embargo_ms. The label horizon 21 < embargo 22 — fixed-horizon-21 label window is strictly covered by the embargo.

**V3_FEATURE_COLUMNS_TOP_N count = 14**: PASS — no features added/removed; common_kwargs passes feature_columns=list(features_for_symbol(symbol)), same as /060/071.

**DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)**: PASS — ATR multipliers unchanged; inert under fixed-horizon labeling (no barriers at training time) but trade-exit barriers still use these values.

**V3_MODELS = 3 symbols (BCH/LDO/TRX)**: PASS — unchanged from /060.

## Tests

**New tests (6/6 PASS)**: tests/strategies/ml/test_fixed_horizon_label_mode.py
- test_fixed_horizon_label_returns_sign_of_fwd_return: PASS
- test_fixed_horizon_pnl_is_realized_return: PASS
- test_triple_barrier_default_unchanged: PASS (backward-compat verified — byte-identical output to call without kwarg)
- test_fixed_horizon_ignores_sl_barrier: PASS (adversarial: short-TP fires first under triple_barrier → label=-1; but fwd_return=+6% → fixed_horizon label=+1)
- test_lgbm_strategy_stores_label_mode: PASS (default "triple_barrier" and "fixed_horizon" stored correctly)
- test_metalabeling_strategy_forwards_label_mode: PASS (label_mode propagates to M1._m1.label_mode)

**V1/V2 backward-compat (affected test suites)**: 53 tests PASS covering ML strategy, embargo, ensemble, metalabeling, label_timeout_minutes. Pre-existing failure: test_cpcv_embargo_assert.py::test_required_gap_matches_formula hardcodes REQUIRED_GAP==88 from /069 4-symbol universe — this failure is NOT introduced by iter-v3/072 (confirmed via `git show HEAD:tests/strategies/ml/test_cpcv_embargo_assert.py | grep "== 88"`). All tests introduced by this iteration pass; all tests that previously passed still pass.

## Track Isolation

`grep -rn "^from crypto_trade.features " src/crypto_trade/features_v3/` — EMPTY (PASS)

## Sacred Constants

- OOS_CUTOFF_DATE = "2025-03-24": UNCHANGED (run_baseline_v3.py:81)
- training_months = 24: UNCHANGED (run_baseline_v3.py:82, TRAINING_MONTHS constant)
- REQUIRED_GAP = 66: UNCHANGED (embargo computation byte-identical)
- ENSEMBLE_SEEDS (10-tuple lineage): UNCHANGED

## Data Freshness

All 3 v3 symbols (BCHUSDT, LDOUSDT, TRXUSDT) measured at gate time:
- BCHUSDT: last close_time age = 16.8h (STALE — exceeds 16h limit by 0.8h)
- LDOUSDT: last close_time age = 16.8h (STALE — exceeds 16h limit by 0.8h)
- TRXUSDT: last close_time age = 16.8h (STALE — exceeds 16h limit by 0.8h)

**ACTION REQUIRED before launching backtest**: re-fetch all 3 symbols via:
`uv run crypto-trade fetch --interval 8h --symbols BCHUSDT,LDOUSDT,TRXUSDT`
Then re-run `uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT --interval 8h --track v3 --format parquet --workers 4` to regenerate parquets. The data staleness is at the Phase 5.5 gate level only — the backtest is NOT launched by this gate. The Engineer performing Phase 6 must re-verify freshness before running.

## Implementation SHA

Implementation commit: `79990bb` (feat(iter-v3/072): fixed-horizon label_mode + ITERATION_LABEL v3-072)

## Reasons

No blocking concerns. OVERALL=PASS.
