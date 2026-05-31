# Phase 6.0 Critic Pre-Flight — iter-v1/042

OVERALL: PASS

## Pre-Flight Checks

### Check A (Look-Ahead Audit, mini): PASS
walk_forward.py:113 carries `train_end_ms = test_start_ms - embargo_ms`. XGBoost training reuses the same `generate_monthly_splits` / `select_training_samples` walk-forward as LightGBM — no parallel training-boundary code path. Labels, embargo, master-data-extent invariance all inherited. No new feature engineering; V1_FEATURE_COLUMNS_PRUNED 44-col stack at /040 post-state. Brief Section 1 hypothesis description (depth-wise vs leaf-wise) is mechanism-only; no forward-data semantics. Mini-Check A clear.

### Check B (Dispatch + Catch-all): PASS
`elif iteration_label == "v1-042"` at run_baseline_v1.py:4471, located BEFORE the catch-all dispatch (line 4748). `"v1-042"` present in catch-all exclusion tuple at line 4747 per /030 LESSON discipline. Five pre-flight asserts (model, label_mode, optuna_objective, vol_ceiling, atr_tp_mult) compile against args.

### Check C (Wiring — --model xgboost dispatches XgboostStrategy): PASS
argparse declares `--model {lgbm,xgboost}` default=lgbm at lines 2084-2095. `from crypto_trade.strategies.ml.xgb import XgboostStrategy` at line 107. All 4 cohorts (Pool A, C, D, E) instantiate `XgboostStrategy(...)` at lines 4543, 4592, 4641, 4690. Dispatch banner `[iter-v1/042] XGBOOST ACTIVE: tree_method=hist grow_policy=depthwise n_jobs=1 / {N} features / ENSEMBLE_SIZE={K} / n_trials={T}` emitted at line 4516. F-AXIS #2 wiring strings present.

### Check D (Configuration — n_trials=18, ENSEMBLE_SIZE=3, max_depth ∈ [3,5]): PASS
`optimization_xgb.py:101` declares `trial.suggest_int("max_depth", 3, 5)` — matches LM Master Rec 1. `tree_method='hist'`, `grow_policy='depthwise'`, `n_jobs=1` pinned at lines 109-111 (and again at 372-374 for the final-fit code path). Optuna search space is 6 hp (num_leaves dropped). Brief Section 3.5 locks n_trials=18 + ENSEMBLE_SIZE=3 + single-seed=42 — passed via runner CLI per Section 3.4.

### Check E (Test suite): PASS
tests/test_iteration_v1_042.py contains 15 tests (mandate was ≥8). Tests cover: dispatch elif existence (T1), catch-all exclusion (T2), banner with tree_method/grow_policy/n_jobs strings (T3), 4 pre-flight asserts (T4-T7), feature_columns + ensemble_seeds guards (T8, T13), max_depth ∈ [3,5] (T9), --model argparse (T10), LGBM regression guard (T11), pinned config (T12), F-AXIS #2 xgb import (T14), and walk_forward embargo regression (T15 — the iter-v3/058 lookahead-fix guard, codifies the foundation invariant).

### Check F (Anti-Pattern A1-A14 static scan on src/): PASS
- A1 (train_end_ms = test_start_ms without subtraction): grep returns ONLY the legitimate `train_end_ms = test_start_ms - embargo_ms` at walk_forward.py:113 and cross_sectional.py:1345; no raw assignment.
- A2 (returns[t:t+timeout].std()): zero matches.
- A3 (fit_transform on combined train+test): zero matches.
- A4-A11: not applicable / unchanged (no universe, scaler, OOF, gate, forming-candle, threshold, or feature-parquet changes in /042).
- A12 (DSR/PSR wrong-granularity): no methodology axis change in /042; gates inherit /056 fix.
- A13 (report write-before-read): no new derived-report fields in /042.
- A14 (new): none.
Anti-pattern scan clean.

### Check 14 (Axis Family Validation): PASS
Brief Section 0.6 declares `model-arch` REPEAT (counter 3/5 v1-wide). Prior 5 EXPLORATIONs enumerated (/037-/041): loss-function, risk-primitive, hybrid, feature-family, labeling — none are `model-arch`. Last `model-arch` at /024 (18 iters ago); monoculture rule NOT armed. Actual src/ diff matches: ONLY library-swap dispatch + XgboostStrategy instantiation; no feature/label/universe/risk-gate change. Structural orthogonality from /003 (cohort split) and /024 (regime sub-models) documented and consistent with src/ diff. REPEAT is JUSTIFIED.

### Mini-Check L (Wall-clock viability — XGBoost 2-3× slower): PASS-CONDITIONAL
- max_depth bound enforced at [3,5] (optimization_xgb.py:101) — LM Master Rec 1 primary mitigation.
- tree_method='hist' pinned (rules out 'exact' which would be 5-10× slower).
- n_jobs=1 (NOT -1) — pinned for determinism per LM Master Rec 3 and brief Section 3.1. n_jobs=-1 would break determinism with fixed random_state on XGBoost 2.x; the determinism mandate (deterministic_trade_match.md) overrides the user-prompt n_jobs=-1 hint.
- Modal wall-clock: ~130 min (brief Section 6); 2h soft cap; cycle-5 NO-kill-switches per user directive 2026-05-30 accepts overrun. LM Master Section 2 suggested a hard kill at 110 min; brief Section 6 explicitly rejected the kill-switch in favor of honest accounting. Verdict: AT-CAP but viable; not a BLOCK condition.

### Foundation Regression: PASS
walk_forward.py:113 unchanged by QE commits — `train_end_ms = test_start_ms - embargo_ms` intact. The iter-v3/058 RE-ANCHOR fix is regression-tested by `test_v1_042_walk_forward_embargo_regression` (T15) AND the foundation-level `tests/test_lookahead_embargo.py` remains in place.

### Cadence + Axis Sanity: PASS
phase5p5_gate.md OVERALL=PASS confirmed. Brief Section 0.6 axis family declared (`model-arch`), rotation status VALID, counter 3/5 not at monoculture. Cycle-5 EXP-9/10 cadence honest.

### Falsifier Presence: PASS
Brief Section 1 H1b explicit falsifier: "If F-AXIS #1 OOS Sharpe Δ < -0.45 AND F-AXIS #7 OOS MaxDD inflation > 1.5× baseline 40.94% AND F-AXIS #2 OOS trades < 130, the library-swap axis is REFUTED at v1 EXPLORATION budget". Section 9 enumerates 5 numeric falsifiers; Section 11.6 locks OOS Sharpe Δ verdict bands.

## Approved for Launch

OVERALL=PASS. The QE setup is methodologically clean: foundation walk-forward embargo unchanged; XGBoost pinned at depth-wise + hist + n_jobs=1 + max_depth [3,5]; dispatch elif before catch-all with exclusion tuple updated; 15 tests covering dispatch, asserts, config, guards, F2 wiring, and foundation regression; axis family REPEAT but mechanism-orthogonal to /003 and /024; no anti-pattern signatures introduced. Wall-clock is AT-CAP (~130 min modal) but mitigated by max_depth tightening (LM Master Rec 1) and accepted under cycle-5 no-kill-switches discipline. Phase 6 backtest is cleared to launch.

## Wall-Clock Viability
Modal 130 min, band 100-150 min. AT-CAP against 2h soft cap. n_jobs=1 pinned (deterministic) not -1; max_depth ∈ [3,5] enforced. Soft overrun acceptable; QE should split-dispatch per `feedback_split_engineer_dispatch.md`.

## Path Forward
Not applicable — OVERALL=PASS.
