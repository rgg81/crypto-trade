# Phase 5.5 Gate — iter-v3/074

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE = 2025-03-24, training_months = 24, IS/OOS windows named in absolute dates. Confirmed immutable constants in runner: `OOS_CUTOFF_DATE = "2025-03-24"`, `TRAINING_MONTHS = 24`.
- Section 1 (Hypothesis): PASS — One specific sentence. Axis: enable_regime_gate=True for TRXUSDT. Mechanism: BTC drawdown_30d > 20% OR |BTC vol_zscore_30d| > 1.5 suppresses TRX candidates. Predicted effect: IS lift via training-distribution shift (crash-regime bars dropped from TRX Optuna landscape). Holding-time-orthogonal qualifier stated.
- Section 2 (IS-Only Evidence): PASS — committed script at `analysis/iteration_v3-074/axis_selection_eda.py` (SHA `b5e42f6`). Numerical tables: regime-stratified IS sub-period Sharpe (-0.0242 bear/chop, +0.5195 bull), trade-level counterfactual (3 IS / 6 OOS suppressions with wpnl), holding-time predictor (mean Δ = -0.35 candles, median Δ = 0.0), bar-level fire rate (IS 14.9%, IS bear/chop 19.1%, IS bull 1.3%, OOS 8.9%), T0 anchor verified byte-exact vs `reports-v3/iteration_v3-060/comparison.csv` (IS monthly_sharpe 0.8325, OOS 0.1403, IS n_trades 159, OOS n_trades 102, frac_positive_paths 0.6444).
- Section 3 (Proposed Changes): PASS — ONE substantive axis (enable_regime_gate=True for TRX) plus ONE mandatory revert (V3_ATR_MULTIPLIERS_PER_SYMBOL = {} reverts /073 axis). Symbols unchanged (BCH/LDO/TRX). Features unchanged (14). label_mode stays "triple_barrier". Enumerated changes listed with history comments.
- Section 4 (Expected OOS Impact): PASS — IS Sharpe Δ +0.05 CI [-0.15, +0.30]; OOS Sharpe Δ +0.10 CI [-0.10, +0.40]. Explicit falsifier: OOS Sharpe Δ < -0.20 rejects hypothesis. BCH IS byte-identity predicted as hard positive control. Holding-time-effect predictor: predicted mean Δ ≈ 0 (-0.35 candles), median Δ = 0.0 (holding-time-orthogonal confirmed). Behavioral-effect predictor: TRX IS trades 70-74 (from 75), TRX OOS trades 46-53 (from 54), BCH/LDO unchanged. OOS/IS ratio SUSPICIOUS gate pre-registered: > 3.0 = SUSPICIOUS unconditionally.
- Section 5 (Risk Mitigation): PASS — Past-only discipline stated (`.shift(1)` / `np.searchsorted(..., side="left") - 1`). IS-calibrated thresholds (20.0% dd = IS-90th percentile; 1.5 vol-zscore = IS-95th percentile). Simulated historical effect = counterfactual in Section 2.2. Scope bound to TRXUSDT only. Three falsifiers defined (OOS Sharpe Δ < -0.20, duration shift > +1.5 candles, OOS/IS > 3.0).
- Section 6 (Risk Management Design): PASS — 8-primitive table (numbered 1-11 with gaps for closed/disabled). Primitive 9 fire-rate prediction given (IS 14.9% bar-level, OOS 8.9% bar-level; trade-level 3 IS / 6 OOS). Regime coverage analysis: gate fills the BTC-macro-conditional gap for TRX. `gate_stats_summary()` reporting noted.
- Section 7 (Failure-Mode Prediction): PASS — Three forward-looking failure modes named with probabilities: INERT 35% (gate fires but training-distribution shift too small), NEGATIVE 25% (gate suppresses net-positive TRX trades), SUSPICIOUS 10% (training-distribution shift accidentally produces longer-holding TRX model). Detectors named for each mode. Process predictions P1-P3 included.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Pre-registered axis-classification taxonomy in disjunctive priority order (SUSPICIOUS 8.4 → NULL-RESULT 8.5 → NEGATIVE 8.2 → PROMISING 8.1 → INERT 8.3). Numerical thresholds locked: PROMISING iff IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 AND frac_positive_paths ≥ 0.50 AND no Critic FAIL. SUSPICIOUS iff OOS/IS > 3.0 OR IS-shift<0 AND OOS-shift≥+0.20 OR duration shift > +1.5 candles. Evaluation order matches /071/073 precedence.
- Section 9 (Library Stack): PASS — No new libraries. Versions listed (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1). mlfinlab/pypbo/fracdiff not invoked.
- Section 10 (QR Audit Trail): PASS — EDA SHA `b5e42f6`, setup commit SHA `a5d5cdd` declared. QR axis-selection rationale: three candidates (A regime-gate, B meta-labeling, C entry-timing) evaluated on IS-only data; AXIS A selected with documented rejection of B and C. Both limbs of hard constraint satisfied (holding-time-orthogonal AND regime-diagnostic).

## Code Verification

- ITERATION_LABEL: "v3-074" — CONFIRMED in runner line 128.
- OOS_CUTOFF_DATE = "2025-03-24" — CONFIRMED (runner line 81).
- TRAINING_MONTHS = 24 — CONFIRMED (runner line 82).
- V3_FEATURE_COLUMNS: 14 columns — CONFIRMED (`len(V3_FEATURE_COLUMNS) = 14`).
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {} — CONFIRMED (reverted from /073 BCH/LDO entries).
- DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) — CONFIRMED.
- V3_FEATURES_PER_SYMBOL = {} — CONFIRMED.
- atr_multipliers_for_symbol(BCH/LDO/TRX) all = (2.0, 1.0) — CONFIRMED.
- enable_regime_gate = True in _build_v3_model — CONFIRMED (runner line 1592).
- regime_gate_symbols = ("TRXUSDT",) — CONFIRMED (runner line 1593).
- regime_dd_threshold_pct = 20.0 — CONFIRMED (runner line 1594).
- regime_vol_zscore_threshold = 1.5 — CONFIRMED (runner line 1595).
- block_long_for = () — CONFIRMED (primitive 10 reverted).
- block_short_for = () — CONFIRMED.
- adx_threshold_per_symbol = {} — CONFIRMED.
- enable_per_symbol_drawdown_brake = False — CONFIRMED.
- label_mode = "triple_barrier" — CONFIRMED (runner pre-flight line 797).
- REQUIRED_GAP = 66 = (21+1)*3 — CONFIRMED in validation_v3.py line 60.
- V3_MODELS = (BCH, LDO, TRX) — 3 symbols — CONFIRMED.

## Pre-Flight Assertions

- New Primitive 9 assertion: CONFIRMED — checks `strat_check.config.enable_regime_gate`, `regime_gate_symbols == ("TRXUSDT",)`, `regime_dd_threshold_pct == 20.0`, `regime_vol_zscore_threshold == 1.5` (runner lines 568-596).
- V3_ATR_MULTIPLIERS_PER_SYMBOL emptiness assertion: CONFIRMED — `_expected_atr_per_symbol = {}` and assertion at runner lines 453-465. Also per-symbol atr_multipliers_for_symbol loop for BCH/LDO/TRX at lines 510-528.
- No stale /073 assertion: CONFIRMED — The `_expected_atr_per_symbol` dict is now `{}` (matching the reverted state), not the /073 `{"BCHUSDT": (2.0,1.25), "LDOUSDT": (1.5,1.25)}` values. The assertion will PASS.

## Track Isolation

- `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` — empty. PASS.
- `grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v3/` — empty (only docstrings/comments mention "features_v2", no actual imports). PASS.

## Tests

- `tests/features_v3/test_regime_gate_v3_074.py` (new): 7 PASSED.
- `tests/features_v3/test_atr_multipliers_for_symbol.py` (new): 6 PASSED.
- `tests/strategies/ml/test_regime_gate.py` (pre-existing adversarial suite): 7 PASSED.
- `tests/features_v3/` full suite: 177 PASSED, 3 SKIPPED.
- `tests/strategies/ml/` key subset (regime_gate, direction_block, vol_scale_floor, v3_feature_count): 23 PASSED.
- Linter (`uv run ruff check src/crypto_trade/features_v3/ tests/features_v3/ run_baseline_v3.py tests/strategies/ml/test_regime_gate.py`): All checks passed.

## Data Freshness

- BCHUSDT: lag = 4.0h — PASS (< 16h).
- LDOUSDT: lag = 4.0h — PASS.
- TRXUSDT: lag = 4.0h — PASS.
- BTCUSDT: lag = 4.0h — PASS.

## Holding-Time-Orthogonal Verification (Section 4.3 mandated)

Section 4.3 contains the holding-time-effect predictor: mean Δ = -0.35 candles (IS), -0.29 (OOS); median Δ = 0.0 (IS), -0.5 (OOS). Deltas are near-zero and slightly NEGATIVE (opposite direction from holding-time-extension family). Falsifier pre-registered: if backtest kept-roster mean duration shifts > +1.5 candles, orthogonality violated. This is the load-bearing reason AXIS A satisfies the Critic /073 hard constraint.

## Exploration Catalog

Cycle 2 rows (/071-074) are NOT yet in `briefs-v3/exploration_catalog.md`. This is expected — catalog rows are appended at Phase 8 closeout. NOT a blocker.

## Minor Note

`tests/strategies/ml/test_v3_feature_count.py` function `test_feature_count_15` has a stale name (the iteration that briefly had 15 features was /064, since reverted). The function body correctly asserts `n == 14` and passes. This is documentation rot in the test function name only; the assertion logic is correct.

## Reasons

None — OVERALL: PASS.
