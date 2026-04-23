# Iteration 197 — Bring live engine to v0.186 parity

**Date**: 2026-04-23
**Type**: ENGINEERING (live-trading module catch-up)
**Baseline**: v0.186 (unchanged — this iter is infrastructure, not strategy)
**Decision**: MERGE

## Context

The live-trading module (`src/crypto_trade/live/`) had been sitting at
baseline **v152** while the backtest and strategy accumulated four major
changes over iterations 165-186:

| Iter | Change | Scope |
|------|--------|-------|
| 165 | Model D: BNB → LTC | Live had `symbols=("BNBUSDT",)` |
| 172-176 | Model E: DOT added w/ R1+R2 | Live had no Model E at all |
| 173 | R1 consecutive-SL cooldown on C, D, E | Live never tracked SL streaks |
| 186 | R3 OOD Mahalanobis gate on all models | Live never gated on OOD |

If deployed as-is, the live engine would trade only BTC/ETH/LINK/**BNB**
without any R1/R2/R3 gating. Cumulative divergence from backtest would
be immediate and large — the same class of bug that bit us in iter 162-164.

## Changes

### `src/crypto_trade/live/models.py`
- `OOD_FEATURE_COLUMNS`: 16-feature scale-invariant subset, shared source
  of truth with `run_baseline_v186.py`.
- `ModelConfig` fields (per-model):
  - R1: `risk_consecutive_sl_limit`, `risk_consecutive_sl_cooldown_candles`
  - R2: `risk_drawdown_scale_enabled`, `risk_drawdown_trigger_pct`,
    `risk_drawdown_scale_anchor_pct`, `risk_drawdown_scale_floor`
  - R3: `ood_enabled`, `ood_features`, `ood_cutoff_pct`
- `BASELINE_MODELS`: A (BTC+ETH, no R1), C (LINK, R1), **D (LTC, R1)**,
  **E (DOT, R1+R2)**, all four with R3 at cutoff 0.70.
- Docstring updated from "v152" → "v186".

### `src/crypto_trade/live/engine.py`
- `ModelRunner.__init__`: forwards `ood_enabled`, `ood_features`,
  `ood_cutoff_pct` from `model_config` (not `live_config`) to
  `LightGbmStrategy`.
- `LiveEngine.__init__`: adds state dicts
  - `_sl_streak: dict[str, int]` per-symbol
  - `_risk_cooldown_until: dict[str, int]` per-symbol
  - `_cum_weighted_pnl: dict[str, float]` per-model
  - `_peak_weighted_pnl: dict[str, float]` per-model
  - `_symbol_to_model: dict[str, str]` lookup
- New method `_rebuild_risk_state()`: chronologically replays closed
  trades from the state DB to reconstruct R1/R2 state. Called in
  `run()` after `_rebuild_vt_history()`.
- New method `_record_trade_close_for_risk(trade)`: updates R1 streak
  and R2 cum/peak on each close. Called from `_handle_trade_close()`
  and from the catch-up inner loop.
- New method `_r2_scale_for(model_name)`: computes drawdown-scaling
  factor, mirroring `backtest.py:358-368` math exactly.
- `_catch_up_model`: signal-open gate now also checks
  `self._risk_cooldown_until`; `vt_scale` is multiplied by
  `self._r2_scale_for(model_name)`.
- `_tick` (the real-time path): same R1 gate + R2 scaling at the
  signal-open site.

### `run_baseline_v186.py`
- Imports `OOD_FEATURE_COLUMNS` from `live.models` (single source of
  truth) instead of redeclaring. Removes drift risk.

### `tests/live/test_engine.py`
Added 8 tests covering:
- `test_live_config_all_symbols` — updated to v0.186's 5-symbol list.
- `test_baseline_models_shape` — verifies D=LTC, E=DOT, R1/R2/R3 wiring.
- `test_model_runner_forwards_r3` — `ood_cutoff_pct=0.55` → strategy sees 0.55.
- `test_model_runner_r3_disabled` — `ood_enabled=False` → strategy gets None.
- `test_engine_r1_arms_cooldown_after_k_sls` — 3 SLs arm cooldown, then reset.
- `test_engine_r1_disabled_for_model_a` — no streak tracked when R1 off.
- `test_engine_r2_scale_within_dd_band` — linear interp trigger→anchor→floor.
- `test_engine_r2_records_weighted_pnl_and_peak` — cum and peak update correctly.
- `test_engine_rebuild_risk_state_from_db` — DB replay reproduces correct state.

### `analysis/iteration_197/live_backtest_april_parity.py` (gitignored)
End-to-end April 2026 parity script: seeds pre-March v0.186 trades into
a temp DB, calls `_rebuild_vt_history` + `_rebuild_risk_state`, then
runs `_catch_up_model` for each runner with a patched `time.time`.
Compares resulting April trades tuple-by-tuple against the backtest's
April trades.

## Verification results

### Unit tests
```
tests/live/test_engine.py: 11/11 passed (8 new)
tests/live/ full suite:    79/79 passed, incl. test_backtest_parity
```

### April 2026 parity (end-to-end)
```
Loaded 804 backtest trades from reports/iteration_186/
  pre-March (for state seeding): 768 trades
  April 2026 (for parity comparison): 14 trades
Seeding 768 pre-March trades into temp DB…
[live] Rebuilt VT history: 768 daily PnL entries across 5 symbols
[live] Rebuilt risk state: 30 R1 cooldowns armed, R2 cum PnL by model =
       {'A': 0.0, 'C': 0.0, 'D': 0.0, 'E': 43.72}
Running catch-up (fake now = 2026-04-30 23:59:59 UTC)…
  A catch-up: 365s  (19 opened, 18 closed)
  C catch-up: 359s   (6 opened,  6 closed)
  D catch-up: 260s   (6 opened,  5 closed)
  E catch-up: 250s   (4 opened,  3 closed)
Live engine opened 14 trades in April 2026
Backtest opened   14 trades in April 2026
✅ PARITY OK (after tolerance fix for CSV's 4-decimal precision)
```

Two "mismatches" on initial run (both for Model E DOT trades) were
artifacts of `iteration_report.py:121` writing `weight_factor` with
`:.4f`, truncating the in-memory value. The live engine's in-memory
values matched to 6+ decimals; the CSV just drops the 5th-6th decimal.
Parity script now tolerates 1e-4 (one CSV quantum) and passes.

## Why NOT running the full live flow here

This iter is strictly backtest-to-live parity. Paper-trading the live
engine against the real Binance API is iter 196's recommendation and
requires real-world compute/time we haven't committed to yet. The
parity check is the *prerequisite* for paper trading.

## Exploration/Exploitation Tracker

Window (187-197): [X, E, E, E, X, V, X, E, V, E, X-eng] — classification
flexible since iter 197 is infrastructure, not strategy exploration.
Treating as "engineering" (distinct from E/X).

## Commit plan

- `feat(iter-197): bring live engine to v0.186 parity — R1/R2/R3 + Model E (DOT)` ✅
- `test(iter-197): live engine R1/R2/R3 + BASELINE_MODELS shape tests` ✅
- `refactor(iter-197): deduplicate OOD_FEATURE_COLUMNS — single source of truth` ✅
- `docs(iter-197): research brief` (this doc)
- `docs(iter-197): engineering report`
- `docs(iter-197): diary entry — MERGE`

## Follow-up

- Iter 198 could be paper-trading v0.186 with confidence that live
  output matches backtest output.
- If the CSV 4-decimal precision becomes a usability issue (e.g. future
  iterations with very small weight_factors), consider tightening
  `iteration_report.py:121` to `:.6f`. Not urgent.
