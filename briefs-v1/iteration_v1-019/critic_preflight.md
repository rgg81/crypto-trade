# Phase 6.0 Critic Pre-Flight — iter-v1/019

OVERALL: PASS

## Pre-Flight Checks

### Check 1 (mini) — Brief Look-Ahead Audit: PASS

Brief Sections 2.1-2.7 (IS-Only Evidence) are pure read-only consumption of pre-existing baseline reports and EDA scripts committed at `2028c1d`. The threshold-sweep table at Section 2.5 includes columns labeled "OOS skip projected (informational)" / "OOS lift projected (informational)" — these are explicitly projected extrapolations from IS regime statistics, NOT OOS lookups; flagged in the brief at line 79 of phase5p5_gate.md ("OOS columns in threshold sweep are labeled 'informational' and use projected extrapolation, not OOS lookup"). No look-ahead in the proposed mechanism: the BTC-trend gate uses `BTC 14d return < threshold` computed via `np.searchsorted(btc_open_times, trade.open_time, side='right') - 1` with a 42-bar warmup floor (verified at `risk_v2.py:1386-1394`) — past-only by construction. No "future" or "rolling including current" language in Section 3 feature descriptions; no new features added (re-uses V1_FEATURE_COLUMNS_PRUNED unchanged).

### Check 13 (mini) — Anti-Pattern Static Scan: PASS

QE's src/ diff scope is two files: (a) `run_baseline_v1.py` dispatch branch additions (V1_ITER019_UNIVERSE constant, gate constants, import block, elif branch at lines 1364-1424) and (b) the new test file `tests/test_iteration_v1_019_eth_gate.py`. Foundation modules untouched. Scanned for §11 catalog signatures:
- **A1 (train_end_ms = test_start_ms without subtraction)**: grep returns 5 matches in `walk_forward.py:113` and `cross_sectional.py:1325, 1345` — every match carries `- embargo_ms` subtraction; the documentation lines at `walk_forward.py:22` and `cross_sectional.py:974` describe the formula, not the bug. ZERO bug-signature matches.
- **A2 (forward-window labeling std)**: not touched; labeling.py untouched.
- **A3 (fit_transform before split)**: QE diff has no scaler/fracdiff/PCA additions.
- **A8 (stateful gate deadlock)**: the gate at `risk_v2.py:1378-1416` is provably stateless — pure loop over trades, mutates only the local `stats` counter, no persistent state across trades. Brief Section 6.5 deadlock-impossibility proof confirmed by code reading. The 42-bar warmup floor falls through to `filtered.append(replace(trade))` (no kill), so even warmup edge cases cannot deadlock.
- **A12 (DSR/PSR wrong-granularity)**: no methodology changes in QE diff; existing reporting pipeline unchanged.
- **A13 (read-before-write)**: no new disk-I/O dependencies in QE diff; `gate_stats` is in-memory; `load_btc_klines_for_filter` reads `data/BTCUSDT/8h.csv` which is a static input file (not a report artifact).

The cross-track import `from crypto_trade.strategies.ml.risk_v2 import (BtcTrendFilterConfig, apply_btc_trend_filter, load_btc_klines_for_filter)` is reviewed under the "KEY CONCERN" rubric: `risk_v2.py` lives at `src/crypto_trade/strategies/ml/risk_v2.py` — under `strategies/ml/`, NOT under `features_v2/`. The documented v1 track-isolation guard (`run_baseline_v1.py:9-21`) explicitly forbids `features_v2`/`features_v3` imports; `strategies.ml.risk_v2` is helper-layer (post-hoc trade-stream filter), not feature-layer. The `apply_btc_trend_filter` function reads BTC OHLCV as a filter signal applied AFTER model trade generation — not added to the feature matrix; no Optuna trajectory contamination; no Model G training change. Functionally equivalent to vendoring with zero behavior change. Cross-track imports of helper-layer modules are permitted by the documented track-isolation rule; the brief's Section 3.1 fallback (vendor copy into `risk_v1_gates.py`) is reserved as Phase 6.0/Critic-conditional but is NOT triggered. PASS.

### Foundation Regression: PASS

`walk_forward.py:113` carries the canonical embargo subtraction `train_end_ms = test_start_ms - embargo_ms  # purge labels that would peek into test` UNCHANGED. Brief Section 3.1 explicitly enumerates ZERO changes to `src/crypto_trade/features_v1/`, `strategies/ml/lgbm.py`, `optimization.py`, `walk_forward.py`, `labeling.py`, R1/R3 gate code, and `risk_v2.py` (imported only). QE's diff confines src/ changes to dispatch branch in `run_baseline_v1.py` + new test file. The 4 mandated regression tests in `tests/test_lookahead_embargo.py` are all present at lines 120 (`test_labels_are_invariant_to_master_data_extent`), 163 (`test_demonstrates_bug_without_embargo`), 232 (`test_time_series_split_with_gap_excludes_correct_rows`), and 261 (`test_walk_forward_embargo_matches_cv_gap_formula`). QE reports 49 tests PASS; trusted per Phase 6.0 protocol (Critic re-runs not in scope).

### Cadence + Axis Sanity: PASS

phase5p5_gate.md confirms OVERALL=PASS at gate-time HEAD `f4b2884c0158a636653a655998debf8916cf9a91` (the brief's Section 0.5 cadence position "cycle-3 #4 of 10; CONFIRMATION earliest at /027" is internally consistent). Brief Section 0.6 declares axis family `per-cohort-specialization-ETH` as NEW 10th family (FIRST usage). Prior 5 EXPLORATIONs per brief Section 0.6 lines 67-72 and phase5p5_gate.md lines 13-18: /014 labeling, /015 labeling (CONFIRMATION-spec), /016 sample-weighting, /017 universe, /018 per-cohort-specialization-LINK. Rotation status VALID by both literal-name comparison and the 3-way orthogonality argument documented (different COHORT from /018 LINK, different SPECIALIZATION dimension introduced — stateless regime gate — and opposite-sign structural prior). LM Master Phase 4.5 §1 independently confirms this is NOT a v2/019 same-pattern re-discovery. HIGH-RISK declaration at Section 2.5 explicit (single-cohort + post-hoc gate; multi-domain training-objective change); cumulative tracker correctly populated; no 3-consecutive catastrophic HIGH-RISK forward-binding trigger fired.

### Falsifier Presence: PASS

Brief Section 4 carries:
- **F1** ETH-only OOS Sharpe Δ vs ETH-in-pool OOS anchor +0.0503 with 4 explicit cells (PROMISING Δ ≥ +0.20 / INERT [−0.20, +0.20] / NEGATIVE Δ ≤ −0.20 / Catastrophic Δ ≤ −0.55).
- **F3** ETH-only IS Sharpe Δ vs anchor −0.1022 with same 4-cell band structure.
- **F5** PSR_monthly_vs_0 catastrophic floor at < 0.10.
- **F7** ETH IS+OOS sign-agreement constraint (the strongest single mechanism check per brief Section 4 line 499).
- **F8** ETH-only trade band IS [80, 200] / OOS [25, 90] with explicit BREACH-low / BREACH-high subcells.
- **F-AXIS-MECHANISM #1** dispatch correctness (binary pass: `df['symbol'].unique() == ['ETHUSDT']`).
- **F-AXIS-MECHANISM #2** trade-count band.
- **F-AXIS-MECHANISM #3** gate fire-rate band IS [10%, 30%] / OOS [5%, 35%] with explicit **LOAD-BEARING** marker (per LM Master §9 elevation; Section 4 line 521).
- **F-AXIS-MECHANISM #4** n_eff_per_cell band [4, 8] (informational only).

Falsifier explicit on F1: "If gated ETH-only OOS Sharpe ≤ +0.05 (matches anchor) → gate has no effect or wrong direction → NEGATIVE" (Section 1 line 91). The Section 8 verdict matrix is a 10-row truth table with EXACTLY ONE cell required and hierarchy explicit (line 613). Catastrophic / IS-collapse / DISPATCH-defect cells separately defined. Wall-clock kill-switch at 45 min documented (Section 3.6 line 433).

## Notes (informational)

- **Wall-clock margin verification**: Section 0.8 / 3.6 predicts 26 min total against 2h cap (78% margin) and 1.6h Phase 5.5 BLOCK threshold (70+ min buffer). 45-min internal kill-switch documented. Per brief Section 3.6 contingency block, even 2× linear scaling stays at 52 min (57% margin). Acceptable.
- **HIGH-RISK declaration**: Section 2.5 declares HIGH-RISK with single-sentence reason (universe 5→1 + post-hoc gate = multi-domain training-objective change with NEGATIVE structural ETH prior 4/4). Mitigation opted: NONE (single-seed-style EXPLORATION at ENSEMBLE_SIZE=3). Per HIGH-RISK cumulative tracker on cycle-3 (1 catastrophic /016, 1 INERT /017, 1 PROMISING-INERT /018), no 3-consecutive catastrophic forward-binding mandatory-multi-seed trigger. Acceptable for cycle-3 #4 EXPLORATION.
- **Cross-track import rationale (track-isolation principle)**: the documented v1 track-isolation guard at `run_baseline_v1.py:9-21` forbids `features_v2`/`features_v3` imports — i.e., FEATURE-LAYER cross-track imports. `crypto_trade.strategies.ml.risk_v2` is HELPER-LAYER (strategy/risk module). LM Master §1 / §8 / §9 and Critic concur: this is CODE re-use, NOT signal re-use; the gate is applied post-hoc to the retrained Model G trade roster without contaminating Optuna training. No new feature added to V1_FEATURE_COLUMNS_PRUNED. Phase 7.5 Check 14 (axis-family validation) will still need to re-verify that the SRC diff and reports match the declared `per-cohort-specialization-ETH` family; preliminary read of QE diff confirms only `run_baseline_v1.py` dispatch and gate import — consistent with the cohort+specialization axis.
- **F-AXIS-MECHANISM #3 LOAD-BEARING marker**: brief Section 4 line 521 carries the explicit LOAD-BEARING label per LM Master §9 elevation. Phase 7.5 Critic will evaluate F-AXIS #3 BEFORE F1 magnitude when assigning verdict cell — this is methodology-correct given the small absolute F1 anchor (+0.0503) and the high diagnostic power of the binary fire-rate test.
- **PROMISING-MECHANICAL adjacency**: brief Section 6.7 pre-registers the trade_id Jaccard test (kept-trade roster vs EDA baseline roster) for Phase 7.4 LM Master post-mortem if verdict is PROMISING. This is correct anticipation of the `feedback_promising_mechanical_subtype.md` rule; classification responsibility is Phase 7.4 + Phase 7.5, not Phase 6.0.
- **Brief Section 3.1 fallback (vendor copy into `risk_v1_gates.py`)**: NOT triggered by Phase 6.0. The cross-track import of `risk_v2` helper-layer is permitted under the documented track-isolation rule (which forbids `features_v2`/`features_v3` not `strategies.ml.risk_v2`). If a future iteration discovers leakage via the import, Phase 7.5 Check 13 will catch it; at Phase 6.0 the structural integrity argument is sound.
- **Phase 7.5 forward-look**: assuming clean backtest at Phase 6, the Check 14 axis-family verification (per the v1 Critic refactor) will pass — declared family `per-cohort-specialization-ETH`, src/ diff confined to `run_baseline_v1.py` dispatch + helper-layer cross-import, NO changes to feature_columns / risk thresholds / labeling / lgbm internals. Match verifiable by `git diff` at Phase 7.5.

Phase 6 backtest cleared to launch.
