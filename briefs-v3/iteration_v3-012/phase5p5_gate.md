# Phase 5.5 Gate — iter-v3/012

OVERALL: PASS

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 UNCHANGED; ENSEMBLE_SIZE=1 / n_trials=10 / colsample_bytree=1.0 set by --exploration; IS window 2022-09-24 → 2025-03-23, OOS window 2025-03-24 → present declared; sacred constants explicitly confirmed unchanged.
- Section 0.5 (Iteration Type Declaration): PASS — TYPE=EXPLORATION declared; EXPLORATION #5 of 10 needed; single-axis BTC-trend-filter-band; wall-clock budget < 30 min target / 2h hard cap; explicit "NEVER updates BASELINE_V3.md"; axis choice justified by Critic FINAL Rec 1 on iter-v3/011.
- Section 1 (Hypothesis): PASS — one sentence; specific change (±20% → ±15%) with named IS Sharpe target ≥ +0.40; Falsifier 1 at +0.10 anchors the rejection criterion.
- Section 2 (IS-Only Evidence): PASS — committed script: analysis/iteration_v3-012/btc_trend_band_demo.py at SHA aadeb72 BEFORE brief; outputs btc_band_kill_rate.csv + synthesis.md committed; reads only BTC public kline data (no model trades, no IS/OOS split contamination); per-window-split fire-rate table + linear kill-rate projection provided as concrete numbers.
- Section 3 (Proposed Changes): PASS — symbols UNCHANGED (BCHUSDT/MKRUSDT/LDOUSDT/TRXUSDT, disjoint from V3_EXCLUDED_SYMBOLS verified in brief §3.1); labeling UNCHANGED (ATR 2.0/1.0, purge gap 88, §3.2); features UNCHANGED (13 columns, vwap_dev_50 absent, §3.3); single-axis change: BTC_TREND_CONFIG.threshold_pct 20.0 → 15.0 (§3.4); sub-fix decomposition with 12 verifier commands all populated in reconciliation table §3.6; inheritance plan §3.8.
- Section 4 (Expected OOS Impact): PASS — predicted IS Sharpe range [+0.40, +1.20] with median +0.65; 3 falsifiers locked in §4.3; EXPLORATION outcome interpretation table (PROMISING / NEGATIVE-soft / NEGATIVE / BLOCK) in §4.4; per TYPE=EXPLORATION, headline OOS gates are not BLOCK-triggering.
- Section 5 (Risk Mitigation): PASS — 3 cadence-discipline structural safeguards (2h hard cap, single-axis rule honored, EXPLORATION never updates baseline §5.1); 4 methodology-pipeline safeguards (35 adversarial tests, reconciliation table 12 verifiers, V3_FEATURE_COLUMNS len+name pre-flight, two-round Critic flow §5.2); zero new model-level risks §5.3.
- Section 6 (Risk Management Design): PASS — 7-primitive table with primitive #7 threshold tightened (±20% → ±15%, combined kill rate 80–90% vs 75–88%); gate orthogonality verified (BTC trend filter fires independent of the 13-feature LightGBM model and the 34-feature z-score OOD gate); regime coverage unchanged §6.2.
- Section 7 (Failure-Mode Prediction): PASS — 6 predictions (3 process: P1 config-propagation P=5%, P2 wall-clock overshoot P=5%, P3 docstring-stale P=5%; 3 model: P4 PROMISING 50%, P5 soft-NEGATIVE 30%, P6 hard-NEGATIVE 15%); calibrated priors with iter-v3/010+011 overshoot lessons applied; each prediction has named detection signal and mitigation.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 10 EXPLORATION-PROMISING criteria locked before backtest; EXPLORATION-NEGATIVE and BLOCK pathways defined; no MERGE pathway (TYPE=EXPLORATION explicitly stated); catalog update mechanic specified.
- Section 9 (Library Stack): PASS — no new external deps; 8 packages listed with versions noted as already installed; aggregator strategy unchanged from iter-v3/006-011; reproducibility stamp spec for engineering report fully specified.

## Cadence Checks
- TYPE=EXPLORATION: PASS
- Single-axis variation (BTC trend filter band only): PASS
- --seeds 1 specified: PASS
- Wall-clock budget ≤ 2h hard cap, target ≤ 30 min: PASS
- EXPLORATION #5 of 10 needed (catalog: 007 PROMISING, 009 NEGATIVE, 010 PROMISING, 011 PROMISING-w-caveats): PASS

## Pre-Flight Verifiers (run against current code before gate decision)
- Branch = iteration-v3/012: PASS (git branch --show-current)
- V3_FEATURE_COLUMNS len=13, vwap_dev_50 absent: PASS (uv run python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'vwap_dev_50' not in V3_FEATURE_COLUMNS")
- atr_tp_multiplier=2.0 in run_baseline_v3.py line 862: PASS
- atr_sl_multiplier=1.0 in run_baseline_v3.py line 863: PASS
- zscore_threshold=2.0 in run_baseline_v3.py line 873: PASS (inherited from iter-v3/011, UNCHANGED)
- threshold_pct=20.0 in run_baseline_v3.py line 121: PASS — will be changed to 15.0 in Phase 6
- ITERATION_LABEL="v3-011" at line 99: PASS — will be changed to "v3-012" in Phase 6
- analysis/iteration_v3-012/ outputs (btc_trend_band_demo.py, btc_band_kill_rate.csv, synthesis.md) committed at SHA aadeb72: PASS
- 35/35 tests pass (uv run pytest tests/strategies/ml/ -v): PASS (58.04s)

## Reasons (if BLOCK)
N/A — OVERALL=PASS
