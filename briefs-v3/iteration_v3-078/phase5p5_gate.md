# Phase 5.5 Gate — iter-v3/078

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` confirmed unchanged. Re-anchor decomposition present: IS code-drift −0.0089 (TRX vol_scale_floor from /061) + OOS data-extent +0.0675 (2026-05 month) = current-code /060-config baseline IS +0.8236 / OOS +0.2078. IS and OOS windows stated in absolute dates. /059 CONFIRMATION baseline (IS +1.0894 / OOS +0.5791) correctly left unchanged.
- Section 0.5 (Iteration Type): PASS — declared EXPLORATION, cycle 2 #8 of 10. Single-axis, 2h HARD CAP, 3 outer seeds, n_trials=35. Does not update BASELINE_V3.md.
- Section 1 (Hypothesis): PASS — one sentence: replacing LDOUSDT (T2: 27.3% WR / −11.44% IS net_pnl / 11 IS trades; the one symbol whose drag is NOT regime-split-correlated) with ADAUSDT (T7: IS-edge-screen +0.617, clearing LDO by +1.17 IS-Sharpe) lifts the IS aggregate without re-triggering the /075 IS-up/OOS-down regime tension that feature and meta-labeling axes structurally produce.
- Section 2 (IS-Only Evidence): PASS — nine output tables (T0–T8) from committed EDA `e48ebad`. T0 anchor decomposition, T1 IS-regime stratification (BEAR_CHOP +1.29 / BULL +0.41), T2 per-symbol decomposition (LDO 11 trades / −11.44%), T3/T4 NEW-feature candidate exhaustion (two candidates INERT at rank 12-15/15), T5 meta-labeling M2 exhaustion (max |AUC−0.5| = 0.064, near-zero wall), T6 escapability bound (IS bull-month losers = OOS winners — /075 tension; LDO is the exception), T7 IS-edge screen (ADA +0.617 vs LDO −0.550 argmax), T8 holding-time predictor (added-vs-removed gap +0.38 candles). EDA `_grep_no_oos_tuning()` AST self-audit returns PASS. T6 OOS rows correctly labelled INFORMATIONAL and feed no selection.
- Section 3 (Proposed Changes): PASS — single axis: V3_MODELS LDOUSDT → ADAUSDT (3→3 replacement). Feature set unchanged (14-feature anchor). ATR labeling unchanged (`DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`, `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}`). Risk-gate stack unchanged. `vol_scale_floor_per_symbol = {"TRXUSDT": 0.5}` unchanged (LDO was never a key). `V3_FEATURES_PER_SYMBOL = {}` unchanged. /077 conditional-orthogonality instrumentation carried (accretive tooling). Single-axis discipline confirmed.
- Section 4 (Expected OOS Impact): PASS — IS delta predicted +0.13 to +0.33 (anchor IS +0.8236); OOS delta −0.27 to +0.13 (wide, OOS-blind). IS falsifier: Δ < +0.10 = INERT/NEGATIVE. OOS falsifier: Δ < −0.20 = NEGATIVE. Behavioral-effect predictor per `feedback_v3_axis_saturation_predictor.md`: maximal-effect axis, all LDO trades replaced (0% of BCH/TRX sub-roster predicted to change). Holding-time sub-channel falsifier (>+1.0 candle not fired). OOS/IS ratio SUSPICIOUS gate pre-registered at >3.0.
- Section 5 (Risk Mitigation): PASS — R-table covers ADA underperformance, regime-tension loading, over-concentration, trade-rate floor, Phase-6 wiring defect, ADA parquet staleness. IS-calibrated gate thresholds unchanged for BCH/TRX; freshly evaluated for ADA in Phase 6.
- Section 6 (Risk Management Design): PASS — 7-primitive table present. Primitives 1–6 listed with /060 config; disabled primitives (7, 9, 12, drawdown brake, per-symbol cap) correctly marked DISABLED. Fire-rate prediction for BCH/TRX = identical to /060; ADA freshly evaluated in Phase 6.
- Section 7 (Failure-Mode Prediction): PASS — three pre-registered failure modes: INERT-AT-EXPLORATION (BCH dominance absorbs ADA lift), SUSPICIOUS-OOS-DOMINANT (ADA's OOS blind spot), NEGATIVE (screen proxy does not transfer). Metric signatures stated. SUSPICIOUS probability floored at cycle-2 base rate ≈ 43% (3/7 past EXPLORATIONs); no below-base-rate float. Gates that detect each mode identified.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — disjunctive taxonomy LOCKED. Five outcomes with numerical thresholds: PROMISING (IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 AND frac_positive_paths ≥ 0.50, not SUSPICIOUS), NEGATIVE (IS Δ < −0.10 OR OOS Δ < −0.20), INERT (both in-band), SUSPICIOUS (ratio > 3.0 OR SUSPICIOUS-OOS-DOMINANT sub-mode), NULL-RESULT (mechanically impossible for a universe swap — listed for completeness). Evaluation order: SUSPICIOUS → NULL-RESULT → NEGATIVE → PROMISING → INERT.
- Section 9 (Library Stack): PASS — pinned: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. No new library added. No mlfinlab / fallback risk.
- Section 10 (QR Audit Trail): PASS — axis provenance documented; candidates #1 (NEW feature, INERT T3) and #2 (M2, |AUC−0.5|=0.064 T5) exhausted before selecting candidate #3 (universe revision, T6/T7). Per-parameter IS-only / a-priori disclosure table present. EDA SHA `e48ebad`, brief SHA `7be5323`, setup SHA `0648504` all recorded.

## Code-Readiness Checks

### 1. ITERATION_LABEL and V3_MODELS

- `ITERATION_LABEL = "v3-078"`: CONFIRMED (line 128).
- `V3_MODELS` tuple: CONFIRMED as `(("A (BCHUSDT)", "BCHUSDT"), ("C (ADAUSDT)", "ADAUSDT"), ("D (TRXUSDT)", "TRXUSDT"))` — LDOUSDT removed, ADAUSDT added, 3 symbols unchanged.

### 2. V3_EXCLUDED_SYMBOLS Check

`V3_EXCLUDED_SYMBOLS` in `src/crypto_trade/features_v3/__init__.py` contains: BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT, BNBUSDT, SOLUSDT, XRPUSDT, DOGEUSDT, NEARUSDT, MKRUSDT. **ADAUSDT is NOT in V3_EXCLUDED_SYMBOLS.** The runner's `set(cfg.symbols).isdisjoint(V3_EXCLUDED_SYMBOLS)` assertion passes for the BCH/ADA/TRX universe.

### 3. Pre-flight assertions

`_verify_feature_columns`, per-symbol `features_for_symbol("ADAUSDT")`, `atr_multipliers_for_symbol("ADAUSDT")` checks iterate over `("BCHUSDT", "ADAUSDT", "TRXUSDT")` — no stale LDOUSDT hardcode in the pre-flight loops. `REQUIRED_GAP = 66 = (21+1)×3` unchanged (n_symbols stays 3). `vol_scale_floor_per_symbol = {"TRXUSDT": 0.5}` confirmed unchanged (LDO was never a key).

NOTE: `test_regime_gate_v3_074.py` line 55 still passes `("BCHUSDT", "LDOUSDT", "TRXUSDT")` to `atr_multipliers_for_symbol` — this is a legacy symbol in a test of the ATR default-fallback mechanism (which is universe-agnostic; any symbol resolves to (2.0, 1.0) via the empty dict). It does NOT assert the v3 universe and does NOT fail. It is not a gate BLOCK, but it carries a stale label. The universe-assertion test (`test_hurst_drift_50_200_universal.py`) correctly asserts `("BCHUSDT", "ADAUSDT", "TRXUSDT")`.

### 4. ADA Data Coverage

- `data/ADAUSDT/8h.csv`: 6886 rows. **Earliest bar: 2020-01-31 08:00 UTC.** Latest close: 2026-05-14 16:00 UTC.
- `data/features_v3/ADAUSDT_8h_features.parquet`: exists (4.3 MB, mtime 2026-05-15 00:05 UTC).
- **IS window runway**: ADA's earliest bar 2020-01-31 provides 24 months of training history before 2022-01. The v3 walk-forward's first test month for ADA is **2022-01** (one month earlier than the T7 screen's implied 2022-02 BCH/TRX first test month — negligible difference, ADA's first-bar warmup clears the 24-month runway by one full month). The effective first test month is identical for all practical purposes.
- **Staleness**: ADA kline CSV last close is 2026-05-14 16:00 UTC; as of 2026-05-16, the data is **~28h stale** (>16h Phase-6 threshold). ADA parquet is similarly ~26h stale. **A fetch + parquet regen is required at Phase-6 pre-flight before the backtest runs.** This is a Phase-6 task, NOT a gate BLOCK.

### 5. Test Updates

- `test_hurst_drift_50_200_universal.py`: universe assertion updated to `("BCHUSDT", "ADAUSDT", "TRXUSDT")` — PASS.
- `test_fracdiff_d05_universal.py`: asserts `"LDOUSDT" not in symbols` — PASS.
- `test_features_for_symbol.py`: tests `features_for_symbol("ADAUSDT")` returning 14-feature fallback — PASS.
- `test_regime_momentum_signed_3d_universal.py`: references LDOUSDT in `_V3_ALL_SYMBOLS` but this is a "historical symbols ever tested" constant, not a universe-assertion. No false failure.
- `test_risk_v2_drawdown_brake.py`: uses LDOUSDT as a fixture symbol in brake-logic tests — universe-agnostic risk primitive tests; no universe assertion. No false failure.

### 6. Lint and Tests

- `uv run ruff check run_baseline_v3.py src/crypto_trade/features_v3/`: **All checks passed.**
- `uv run pytest tests/features_v3/ tests/strategies/ml/ -q`: **345 passed, 3 skipped** — clean.

## Phase 6 Pre-Flight Reminder (NOT a gate condition)

Before running `uv run python run_baseline_v3.py --exploration --n-trials 35`:
1. Re-fetch ADA klines: `uv run crypto-trade fetch --symbols ADAUSDT --intervals 8h`
2. Regenerate ADA features_v3 parquet: `uv run crypto-trade features --symbols ADAUSDT --interval 8h --track v3 --format parquet`
3. Verify ADA's `close_time` in the refreshed CSV is within 16h of run time.
4. Confirm BCH and TRX klines are also fresh (separate check; they are in the same 3-symbol universe).

## Reasons (if BLOCK)

None — OVERALL: PASS.
