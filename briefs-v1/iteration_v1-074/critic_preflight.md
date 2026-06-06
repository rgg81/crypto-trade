# Phase 6.0 Critic Pre-Flight — iter-v1/074

OVERALL: PASS

## Iteration Context

- TYPE: SPECIALIST-IMPROVEMENT (ETH-IMPROVED-V3; THIRD improvement attempt for the ETH /064 BUNDLE-001 seat)
- Anchor: /064 (IS Sharpe +0.2383, OOS Sharpe +0.5171, 198 IS / 81 OOS trades). /073 is NOT the anchor (discarded as IMPROVEMENT-FAIL).
- Axis: AXIS-R — Mid-Bull SHORT VETO post-aggregator rule layer. Skip direction=-1 entries when `ret_270b ∈ [0.20, 0.50]`. Pre-registered band edges, post-prediction deterministic filter; no feature/model/label/risk-wrapper change.
- Phase 5.5: PASS (confirmed `briefs-v1/iteration_v1-074/phase5p5_gate.md`).
- Branch: `iteration-v1/074`.

## Pre-Flight Checks

### Mini-Check 1 — Brief Look-Ahead Audit: PASS

AXIS-R computes `ret_270b = (close[t] / close[t-270]) - 1.0` using the CURRENT bar's close and a strictly past 270-bar window (`lgbm.py:1582 idx_past = idx_curr - self._mid_bull_short_veto_lookback`; if `idx_past < 0` returns None). No forward data is read. The veto is deterministic on `(ret_270b, signal.direction)` and fires only on already-emitted aggregated signals — Optuna's training objective domain is mechanically unchanged. The IS-firewall is declared in brief Section 0 + Section 2 (analysis scripts open ONLY `reports-v1/iteration_v1-064/in_sample/trades.csv` and IS-window kline data; path-substring assertion `assert "out_of_sample" not in p`). Band edges [0.20, 0.50] and lookback 270 are pre-registered and FROZEN at the brief commit (anti-tuning per `feedback_no_cheating.md`); runner asserts these values at lines 251-262 of `run_iteration_074.py`. No obvious look-ahead in the feature stack (48-col `V1_FEATURE_COLUMNS_PRUNED` UNCHANGED from /064; parquet hash `b81176f8...` pinned, NO regeneration).

### Mini-Check 13 — Anti-Pattern Static Scan: PASS

Scanned all 13 catalog signatures against `src/crypto_trade/` and `run_baseline_v1.py` / `run_iteration_074.py`:

- A1 (train_end_ms regression): PASS. `src/crypto_trade/strategies/ml/walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` (verified verbatim). The /058 fix (commit `5566a69`) is intact.
- A2 (labeling-window σ_t look-ahead): PASS. No matches for forward-window std in `labeling.py`.
- A3 (scaler fit on combined train+test): PASS. No `fit_transform`/`StandardScaler`/`MinMaxScaler`/`FractionalDifferentiation` matches anywhere in `src/`.
- A4 (universe survivorship): PASS. `V1_ITER074_UNIVERSE = ("ETHUSDT",)` is a static literal at `features_v1/__init__.py:564`, not computed from current data.
- A5 (master-data-extent dependency): PASS. Regression test `test_labels_are_invariant_to_master_data_extent` present in `tests/test_lookahead_embargo.py` (line 120).
- A6 (Optuna trial contamination): PASS. Specialist loop creates fresh studies per `(seed, symbol, month)` cell.
- A7 (OOF parquet append-without-clearing): PASS. `oof_persist_path=OOF_PARQUET_PATH` honored at /064 pattern; /074 inherits.
- A8 (stateful gate deadlock): N/A — AXIS-R is stateless (no persistent state; per-candle deterministic on `ret_270b`).
- A9 (forming-candle): N/A at Phase 6.0; will be checked at Phase 7.5.
- A10 (confidence threshold on test): PASS. confidence_threshold Optuna-tunable per seed inherits /064 in-fold convention.
- A11 (parquets with future data): PASS. No regeneration. Features computed at training-cell boundary.
- A12 (DSR/PSR wrong granularity): PASS. Brief Section 6 declares DSR/PBO/PSR at EXPLORATION budget as STRUCTURAL ARTIFACTS (informational only, NOT verdict gates); no smoke-test mismatch risk.
- A13 (report-file read-before-write): PASS. /074 dispatch reads no new disk artifacts before writing them; `specialist_dispersion.csv` is written before any downstream read (line 7264 write, no precedent read).

### Foundation Regression: PASS

Re-verified `src/crypto_trade/strategies/ml/walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` unchanged by QE's commits. The /058 walk-forward embargo fix is intact. `compute_embargo_candles` helper present and used by both `generate_monthly_splits` and the CV gap inside Optuna (single source of truth). Regression test `tests/test_lookahead_embargo.py` confirms 4 expected tests present:
- `test_labels_are_invariant_to_master_data_extent` (line 120)
- `test_demonstrates_bug_without_embargo` (line 171)
- `test_time_series_split_with_gap_excludes_correct_rows` (line 248)
- `test_walk_forward_embargo_matches_cv_gap_formula` (line 277)

### Cadence + Axis Sanity: PASS

- `phase5p5_gate.md` OVERALL=PASS (verified directly).
- Brief Section 0.6 declares FAMILY=`risk-primitive` (post-aggregator RULE-form veto); categorically distinct from /072 R1 streak-cooldown (different layer: regime-conditional direction veto vs streak-conditional cool-down) and /073 feature-family.
- ROTATION_STATUS=VALID. Axis-family rotation is SUSPENDED in cycle-7 per `feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md` (specialist mandate overrides), but rotation honored anyway: last 5 EXPLORATION families {feature-family+risk-primitive, feature-family+risk-primitive, feature-family+risk-primitive, risk-primitive, feature-family} — not all-same-family. /074 risk-primitive is mechanistically distinct from /072 risk-primitive.
- 2h HARD CAP for EXPLORATION declared. Kill-switch conditions enumerated (wall-clock > 2.5h, nan Sharpe, FEATURES_BASE_HASH_48COL mismatch, IS trade count divergence > 10% from expected 166 ± 17).

### Falsifier Presence: PASS

Brief Section 4 contains TWO HARD pre-registered falsifiers (F-AXIS-FALSIFIER) plus per-band F-AXIS #1 thresholds:

1. **F-AXIS #1 explicit Sharpe band**: "IS Sharpe < +0.19 (IS Δ < −0.05) → NEG-1st-STRIKE for ETH BUNDLE seat" and "IS Sharpe < −0.10 (IS Δ < −0.34) → NEG-CONFIDENT + multi-seed mandate trigger" (the OOS-Sharpe-below-X equivalent for an EXPLORATION specialist).
2. **F-AXIS-FALSIFIER #1** (HARD): "Per-trade Sharpe lift < +0.10 → AXIS-R-MECHANISM-FALSIFIED regardless of headline IS Δ."
3. **F-AXIS-FALSIFIER #2** (HARD): "Any single calendar month > 40% of realized IS Sharpe lift → FALSIFIED-REGIME-FIT."

All three are pre-registered, quantitative, and not re-fittable post-hoc. F-AXIS-COUNTERFACTUAL audit also pre-registers tolerance bands on vetoed-trade count (32 ± 5), net PnL (−9.73% ± 2pp), and WR (16.7% ± 5pp).

## Implementation Verification (QE src/ diff audit)

QE has implemented the SINGLE-BIT axis correctly:

- `run_iteration_074.py` — clone of /064 runner with `ITERATION_LABEL = "v1-074"`, FEATURES_BASE_HASH_48COL pinned, AXIS-R constants AXIS_R_VETO_LO=0.20 / AXIS_R_VETO_HI=0.50 / AXIS_R_VETO_LOOKBACK=270 with pre-flight assertions (lines 251-262).
- `run_baseline_v1.py:7118-7288` — `elif iteration_label == "v1-074"` dispatch branch identical to /064 dispatch except for 4 new kwargs (lines 7231-7234: `enable_mid_bull_short_veto=True, mid_bull_short_veto_lo=0.20, mid_bull_short_veto_hi=0.50, mid_bull_short_veto_lookback=270`). `assert len(active_feature_columns) == 48` at line 7161 enforces UNCHANGED feature stack.
- `src/crypto_trade/strategies/ml/lgbm.py:218-221, 355-358, 1563-1641, 1786` — strategy kwargs added, post-aggregator veto correctly placed at line 1786 AFTER `Signal(direction, weight)` is constructed from `_final_signed = np.mean(_signed_weights)` aggregator. Deterministic on `(ret_270b, signal.direction)`. Decision-log forensic event `kind=axis_r_veto` fires per veto (line 1619-1630). Veto log accumulated in `self._axis_r_veto_log` for Phase 7 counterfactual audit.
- `src/crypto_trade/features_v1/__init__.py:564` — `V1_ITER074_UNIVERSE = ("ETHUSDT",)` static literal.
- `tests/test_iteration_v1_074.py` — methodology constant tests present.

## Methodology Constants UNCHANGED Verification

| Variable | /064 | /074 | Status |
|---|---|---|---|
| FEATURES_BASE_HASH_48COL | b81176f8... | b81176f8... (asserted line 123) | UNCHANGED |
| V1_FEATURE_COLUMNS_PRUNED length | 48 | 48 (asserted lines 232 + 7161) | UNCHANGED |
| atr_tp_multiplier | 2.9 | 2.9 (line 7216) | UNCHANGED |
| atr_sl_multiplier | 1.45 | 1.45 (line 7217) | UNCHANGED |
| training_months | 24 | 24 (line 7207) | UNCHANGED |
| n_trials | 30 | 30 (V1_SPECIALIST_OPTUNA_TRIALS) | UNCHANGED |
| specialist_mode | True | True (line 7227) | UNCHANGED |
| max_depth | 5 FIXED | 5 FIXED | UNCHANGED |
| num_leaves | 31 FIXED | 31 FIXED | UNCHANGED |
| n_estimators_max | 500 | 500 (line 7229) | UNCHANGED |
| n_startup_trials | 10 | 10 (line 7228) | UNCHANGED |
| Walk-forward embargo | train_end_ms = test_start_ms - embargo_ms | UNCHANGED (line 113) | UNCHANGED |
| specialist seed roster | 42..91 (50 seeds) | 42..91 (50 seeds) | UNCHANGED |

## R1 NOT Enabled Verification

- `run_baseline_v1.py:7198`: `risk_consecutive_sl_limit=0,  # R1=OFF: CATALOG-CLOSED for SPECIALIST_mode`.
- `run_baseline_v1.py:7199`: `risk_consecutive_sl_cooldown_candles=0`.
- Comment cites skill commit `f81cafc3` (R1 CLOSED for SPECIALIST_mode per /072 falsification).
- R2 also OFF (`risk_drawdown_scale_enabled=False` at line 7200) — Model A baseline preserved.
- R3 ON-SHARED cutoff=0.70 (lines 7222-7224) — UNCHANGED from /064.
- R5 ON vt_target_vol=0.3 vt_lookback_days=45 (lines 7193-7197) — UNCHANGED from /064.

## Forensic Observations (NOT blocking; flagged for Phase 7.5 + future iteration review)

1. **engine.py AXIS-R parity NOT wired.** Brief Section 3.1(d), Section 5.3 item 11/12, and Section 11.C state that `engine.py:_tick` MUST mirror the AXIS-R conditional with byte-equivalent `ret_270b` computation per `feedback_v1_backtest_live_parity_hard.md` (Critic Check 15 = BUNDLE-PARITY-VIOLATION). Grep on `src/crypto_trade/live/engine.py` for `mid_bull_short_veto|axis_r_veto|enable_mid_bull` returns ZERO matches. The Phase 5.5 gate stated that engine parity was declared but did not verify the actual code presence. NOT a Phase 6.0 BLOCK because /074 is a SPECIALIST EXPLORATION (not a merge candidate; merge happens only at BUNDLE-002 assembly), and engine parity becomes the BLOCK-FINAL trigger at BUNDLE assembly via Critic Check 15. However, if /074 verdicts PROMISING and is proposed for BUNDLE-002, QR/QE MUST wire the engine parity conditional BEFORE BUNDLE-002 assembly. Critic Phase 7.5 will not BLOCK on this for /074 EXPLORATION specifically. Recommendation: at next BUNDLE assembly (whenever /074 or any other AXIS-R-bearing specialist is promoted), Phase 5.5 should verify engine.py wiring presence as a grep check before declaring PASS.

2. **R3 ordering in SPECIALIST path.** Brief Section 5.2 states "AXIS-R can flip a short to flat, and a flat signal does NOT trigger R3 OOD computation (R3 only gates non-flat signals)." However, in the SPECIALIST path at `lgbm.py:1681-1706`, R3 OOD is evaluated BEFORE the seed-aggregation loop (i.e., upstream of any signal). AXIS-R fires AFTER aggregation at line 1786. This means in the SPECIALIST path, R3 always runs first regardless of AXIS-R. This is the /063+ SPECIALIST architecture (R3 SHARED across seeds — single OOD check), not an AXIS-R regression. Brief's "BEFORE R3" claim is the NON-SPECIALIST ordering; in SPECIALIST it is structurally pre-aggregation. Order is consistent with /064. NOT a BLOCK; the brief comment could be tightened for next iteration.

## Path Forward

OVERALL=PASS — no Path Forward required. Backtest launch authorized.
