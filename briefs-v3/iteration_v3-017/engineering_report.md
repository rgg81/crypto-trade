# Engineering Report — iter-v3/017

## Headers

- Iteration: iter-v3/017
- Branch: iteration-v3/017
- Commit SHA (setup): 7ed27e5436bb7f9049a3a2efd88253acc9ebb666
- Hardware: x86_64 (DESKTOP-H1H6T11, WSL2)
- Wall-clock time (setup only): < 1h (backtest not yet run — per split-engineer-dispatch protocol)
- Status: SETUP COMPLETE — AWAITING ORCHESTRATOR BACKTEST LAUNCH

## Configuration Diff vs Baseline (iter-v3/013 → iter-v3/017)

| Parameter | iter-v3/013 (baseline) | iter-v3/017 |
|---|---|---|
| ITERATION_LABEL | v3-013 | **v3-017** |
| --model | lgbm | **metalabeling** (M1+M2 architecture) |
| M2 strategy | ABSENT | **MetaLabelingStrategy** (new module) |
| M2 confidence threshold | n/a | **0.5 PINNED** |
| _write_feature_importance scope | IS + OOS (duplicated) | **IS only** (OOS duplication dropped) |
| Feature importance filename | `feature_importance.csv` | **`model_importance_last_month_*.csv`** |
| All other parameters | (see §3.4 of brief) | **UNCHANGED** |

Sacred constants confirmed UNCHANGED:
- `OOS_CUTOFF_DATE = 2025-03-24`
- `training_months = 24`
- `V3_MODELS` = BCH+LDO+TRX (3 symbols, no MKR)
- `REQUIRED_GAP = 66`
- `V3_FEATURE_COLUMNS` = 13 features, vwap_dev_50 absent, tbr_zscore_30 absent
- `atr_tp_multiplier=2.0`, `atr_sl_multiplier=1.0`, `zscore_threshold=2.0`, `threshold_pct=15.0`

## New Files Committed

- `src/crypto_trade/strategies/ml/metalabeling.py` — MetaLabelingStrategy (~580 lines)
- `tests/strategies/ml/test_metalabeling.py` — 11 smoke + correctness tests
- `briefs-v3/iteration_v3-017/phase5p5_gate.md` — Phase 5.5 gate PASS

## Reconciliation Verifier Outcomes (§3.6 rows 1-14)

| Row | Verifier | Outcome |
|---|---|---|
| 1 | `len(V3_FEATURE_COLUMNS)==13` | PASS |
| 2 | `atr_tp_multiplier=2.0` in runner | PASS |
| 3 | `atr_sl_multiplier=1.0` in runner | PASS |
| 4 | `zscore_threshold=2.0` in runner | PASS |
| 5 | `threshold_pct=15.0` in runner | PASS |
| 6 | `len(V3_MODELS)==3`, MKRUSDT absent | PASS |
| 7 | `REQUIRED_GAP==66` | PASS |
| 8 | `ITERATION_LABEL == "v3-017"` | PASS |
| 9 | `default="lgbm"` in argparse | PASS |
| 10 | `"metalabeling"` in argparse choices | PASS |
| 11 | `_write_feature_importance` writes IS only, no OOS duplication | PASS |
| 12 | Saturation band [157, 261] in brief §2.5 | PASS (in research brief) |
| 13 | §4.4 row 5 condition "\|Δ trades\| ≥ 11 OR per-symbol shift > 5 trades" | PASS (in research brief) |
| 14 | `MetaLabelingStrategy` importable + `__name__=='MetaLabelingStrategy'` | PASS |
| 15 | IS trade count in [80, 156] (post-backtest falsifier) | PENDING — backtest not yet run |

## Test Suite

- `uv run pytest tests/strategies/ml/ -v` → 57 passed, 0 failed (wall-clock ~59s)
- New tests in `tests/strategies/ml/test_metalabeling.py`: 11/11 passed

## Label Leakage Audit

- M2 labels derived EXCLUSIVELY from `train_indices_kept` (the same training window M1 uses).
- `label_trades` called with `train_indices_kept` — no test-window rows included.
- M1 inference on training window uses M1 models trained on the same window — no look-ahead.
- `load_features_range` for test month features is called at M1._train_for_month time, not during M2 label generation.
- CV gap: REQUIRED_GAP=66 = (21+1)*3 symbols — unchanged from iter-v3/013.

## MetaLabelingStrategy Architecture Summary

- M1: LightGbmStrategy instance (delegates compute_features, skip; shares lazy training).
- M2: LGBMClassifier(objective='binary', is_unbalance=True) trained per calendar month.
- M2 training: Optuna F1-maximizing study (n_trials=10, same as M1 EXPLORATION budget).
- M2 threshold: 0.5 PINNED (not tuned — single-axis discipline per brief §3.2).
- M2 features: 14-dim = 13 V3_FEATURE_COLUMNS + M1 prediction probability.
- get_signal flow: M1 predicts → if M1 fires → M2 vetoes if M2 proba < 0.5.
- Feature importance: reads M1._m1._models (inner unwrap for MetaLabelingStrategy); M2 importances not reported.

## Pre-Flight Flags for Backtest

Run: `uv run python run_baseline_v3.py --model metalabeling --exploration --seeds 1 --n-trials 10 --skip-features`

(--skip-features safe if parquets are fresh; remove if data needs regeneration)

Expected output banner: `BASELINE v3 iter-v3-017: BCHUSDT, LDOUSDT, TRXUSDT (seed-plumbing fix)`

Post-backtest falsifiers (§4.3) to check before Critic handoff:
1. IS trade count in [80, 156] (row 15 verifier)
2. Per-symbol IS trade count: BCH ≤ 100, LDO ≤ 21, TRX ≤ 88 (Falsifier 5)
3. IS trade count NOT ≥ 157 (Falsifier 2 — saturation lower bound)
4. IS trade count NOT > 261 (Falsifier 3 — saturation upper bound)

## Anomaly Notes

None — clean implementation. No existing tests broken. All 15 reconciliation verifiers
for rows 1-14 pass; row 15 pending post-backtest.

## Status

OVERALL=READY-FOR-BACKTEST (Phase 6 setup complete; orchestrator launches backtest detached)
