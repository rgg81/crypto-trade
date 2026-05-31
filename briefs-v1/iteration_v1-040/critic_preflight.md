# Phase 6.0 Critic Pre-Flight — iter-v1/040

OVERALL: PASS

## Pre-Flight Checks

### Check A — Look-Ahead Audit: PASS
composed_v1.py:156 computes `ret_5d = log_close - log_close.shift(15)` (past-only via shift); hurst_100 computed by `_rolling_hurst` (values[i-window:i] — bar i uses bars i-window to i-1, strictly past-only). Test `test_compute_regime_momentum_signed_5d_past_only` injects future-bar spike at bar 111 and asserts bar 109 invariant. EDA Section 1.2 documents ADF p<2e-13 across all 5 v1 symbols (stationarity preserved). No forward-window std, no fit-on-combined-train-test, no master-data-extent dependency. Composed feature IS computed at feature-regen time so master-data-invariance must hold via the same regen run; documented past-only by shift+rolling kernel.

### Check B — Dispatch: PASS
run_baseline_v1.py:4142 has `elif iteration_label == "v1-040" and set(symbols) == set(V1_BASELINE_UNIVERSE):` BEFORE the catch-all at line 4261. Catch-all exclusion tuple at line 4277 contains `"v1-040"`. Both /030 LESSON guards satisfied.

### Check C — Wiring: PASS
V1_FEATURE_COLUMNS_PRUNED at features_v1/__init__.py:89-134 contains `regime_momentum_signed_5d` (line 111) and does NOT contain `basis_zscore_30`. Sanity assert `len == 44` enforced (line 142). V1_RETIRED_FEATURE_COLUMNS contains `basis_zscore_30` (line 153) for legacy-parquet defense. Registry wires `composed_v1` group at features/__init__.py:215-219 importing `add_composed_v1_features` from features_v1.composed_v1. V1_OOD_FEATURE_COLUMNS NOT modified (regime feature not added to OOD subspace per Section 5.2).

### Check D — Configuration: PASS
CLI invocation (brief Section 3.3): `--seeds 42` (single-seed=42), `--ensemble-size 3` (V1_EXPLORATION_ENSEMBLE_SIZE), `--n-trials 18` (v1 EXPLORATION standard). HP-1 (colsample bound bump) REJECTED per single-axis isolation; HP-2 + HP-3 ADOPTED. Pre-flight asserts in dispatch enforce `vol_ceiling_mode == 'none'`, `label_mode == 'triple_barrier'`, `optuna_objective == 'sharpe'`.

### Check E — Test Suite: PASS
tests/features_v1/test_composed_v1.py: 7 tests (hurst byte-identical to v3, burn-in NaN, known values, past-only invariant under future-bar spike, burn-in 99 NaN, BTC real-data smoke, stationarity ADF). tests/test_iteration_v1_040.py: 13 tests (tuple membership 3, retired column 1, dispatch branch 1, exclusion-tuple 1, banner 1, 5 pre-flight assert text checks, walk_forward embargo regression). 20 total tests (brief mandates ≥12). Foundation regression `test_v1_040_walk_forward_embargo_regression` confirms walk_forward.py contains `embargo_ms` and `train_end_ms`.

### Check F — Anti-Pattern A1-A14: PASS
A1 (train_end_ms = test_start_ms without subtraction): walk_forward.py:113 carries `train_end_ms = test_start_ms - embargo_ms` (verified by grep). A2 (forward-window std): no `returns[t:t+timeout].std()` in labeling.py. A3 (scaler.fit_transform on combined): no StandardScaler/MinMaxScaler/FractionalDifferentiation matches in src/. A5 (master-data-extent invariance): composed feature uses shift+rolling kernels, structurally invariant. A8 (stateful gate deadlock): no new stateful gates introduced. A12, A13: no methodology-axis changes (this is a feature-family axis). Cross-track import scan returns only documentation/comments (no actual `from crypto_trade.features_v3` import in composed_v1.py — Hurst math is BYTE-FOR-BYTE COPIED per brief Section 11.7).

### Check 14 — Axis Family Validation: PASS
Brief Section 0.6 declares family=`feature-family`. Actual src/ diff: new file features_v1/composed_v1.py, edit features_v1/__init__.py (tuple swap), edit features/__init__.py (registry), edit run_baseline_v1.py (dispatch). All feature-engineering changes. REPEAT of /034 (also feature-family) is mechanism-justified per Section 0.6: /034 was exogenous-new-data-source (perp-spot basis); /040 is endogenous composed-from-incumbents (ret_5d × sign(hurst_100 - 0.5) algebraically derived). Different mechanism classes — monoculture rule fires only on 5-consecutive-same-family which is NOT armed (prior 5 = 5 distinct families per phase5p5_gate.md).

### Mini-Check K — Strategy Attribute Symmetry: PASS
Dispatch invokes 4 models (A pool BTC+ETH, C LINK+R1, D LTC+R1, E DOT+R1+R2) — identical to /034 dispatch baseline. atr_tp/atr_sl per-model UNCHANGED. R1/R2/R3 gates UNCHANGED. All 4 strategies registered in `_post_dispatch_fi_strategies` for feature-importance writes (F-AXIS #2 binding gate evidence).

### Mini-Check L — Wall-Clock Plausibility: PASS
Brief Section 6 projects ~50min compute + 3-5min composed_v1 single-group regen + 3min report = ~60min modal (1.0h). Anchored on /034 (~50min at identical config: n_trials=18, ENSEMBLE_SIZE=3, 5 syms, n_features=44, single-seed=42). Well inside the 2h EXPLORATION cap. NO kill-switch per cycle-5 directive.

### Foundation Regression: PASS
walk_forward.py:113 carries `train_end_ms = test_start_ms - embargo_ms` (grep-verified). embargo_ms still derived from `compute_embargo_candles` (line 22 docstring). Walk_forward fix from iter-v3/058 / commit e149e9d intact. test_v1_040_walk_forward_embargo_regression in suite (test #20).

### Cadence + Axis Sanity: PASS
phase5p5_gate.md OVERALL=PASS. Brief Section 0.6 declares feature-family with REPEAT-MECHANISM-JUSTIFIED rationale. Rotation status VALID. Cycle-5 EXPLORATION #7/10; 3 EXPLORATIONs remain before /044 CONFIRMATION can launch.

### Falsifier Presence: PASS
Brief Section 11.6 contains 5-row pre-registered MERGE/NO-MERGE OOS Sharpe Δ band (NEGATIVE Δ < -0.10; NEGATIVE-CATASTROPHIC Δ < -0.30). Brief Section 2 F-AXIS #1 OOS Δ falsifier + F-AXIS #2 LOAD-BEARING importance rank gate (≥30 in ≥2 of 5 cohorts) + F-AXIS #3 trade-count band [560,690] IS / [165,215] OOS + F-AXIS #4 per-symbol direction + F-AXIS #5 cross-seed Spearman. Five explicit falsifiers; importance-rank gate appropriately substitutes Check 4 |IC|<0.50 per composed-feature IC carve-out doctrine.

### Composed-Feature IC Carve-Out Documentation: PASS
Brief Section 1.4 documents |IC|=1.000 vs ret_5d_15bar primitive (mechanical identity since sign is +1 everywhere) and |IC|=0.80 with mom_rsi_14. Brief Section 2 F-AXIS #2 cites `feedback_v3_engineered_feature_pivot.md` for the IC carve-out and pins importance ≥30 in ≥2/5 cohorts as binding falsifier — overriding the strict |IC|<0.50 gate per documented v3 doctrine.

### Feature Parquet Regeneration: ACTION REQUIRED (DOCUMENTED)
The 5 V1_BASELINE_UNIVERSE parquets (BTCUSDT/ETHUSDT/LINKUSDT/LTCUSDT/DOTUSDT 8h features) must be regenerated to materialize the `regime_momentum_signed_5d` column BEFORE backtest launch. Brief Section 3.2 documents the regen command. Pre-flight Critic does not block on this since the dispatch's first pre-flight assert (`"regime_momentum_signed_5d" in active_feature_columns`) fails-loud if regen is skipped. Orchestrator must run the documented regen step before Phase 6 backtest invocation.

## Approved Launch Invocation
