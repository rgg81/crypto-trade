# Iteration 197 — Engineering Report

**Date**: 2026-04-23
**Type**: Infrastructure / live-engine parity
**Files touched**: 4 code files (3 src, 1 test), 1 runner, 1 analysis script

## Diff summary

| file | lines added | lines removed |
|------|------------:|--------------:|
| `src/crypto_trade/live/models.py` | +62 | −6 |
| `src/crypto_trade/live/engine.py` | +180 | −6 |
| `run_baseline_v186.py` | +4 | −10 |
| `tests/live/test_engine.py` | +310 | −6 |
| `pyproject.toml` + `uv.lock` | +3 | 0 (statsmodels dep — iter 195) |
| **Total** | **+559** | **−28** |

## Test suite

- Full `tests/live/` suite: **79/79 pass** (1165s wall) — `test_backtest_parity.py` still passes, confirming no regression in the v0.152 parity test.
- New `tests/live/test_engine.py`: **11/11 pass** (8 new tests added).
- Ran after every code change; no regressions.

## April 2026 parity result

End-to-end parity between `_catch_up_model()` and `reports/iteration_186/`
(v0.186 backtest):

- **14 live trades / 14 backtest trades** in April 2026
- 14/14 match on `(symbol, open_time, direction, exit_reason, close_time)`
- 12/14 match on `weight_factor` at arbitrary precision
- 2/14 differ on `weight_factor` only because of CSV `:.4f` truncation in
  `iteration_report.py:121` — live 0.369370 vs CSV-stored 0.3693 (diff
  7e-5, below the CSV's own 1e-4 precision quantum).
- Final result: **✅ PARITY OK** with 1e-4 tolerance.

## Runtime

Parity script: 17 minutes on the dev box.
- 4 models × ~2 monthly training triggers × 5 seeds × 50 Optuna trials
  ≈ 4000 Optuna runs total.
- Model A and C took ~6 min each, Model D and E ~4 min each.

## Design notes

1. **R1 state is per-symbol, R2 state is per-model.** This matches the
   backtest's implicit scoping (the backtest accumulator is scalar
   because each backtest runs one model; in live, per-model makes the
   symmetry explicit).

2. **`_rebuild_risk_state()` replays DB trades in chronological order.**
   This is the only way to get correct state at engine restart: R1's
   streak counting and R2's running peak depend on trade order.

3. **R3 moved from `LiveConfig` to `ModelConfig`.** v0.186 uses uniform
   R3 across models (cutoff 0.70, same 16 features), but per-model
   storage future-proofs the architecture — iter 189 proposed
   per-symbol cutoffs as a candidate direction.

4. **R3 gate lives inside `LightGbmStrategy.get_signal`.** Already in
   place from iter 186. The live engine just has to pass
   `ood_enabled=True` during construction; no state tracking needed in
   the engine itself.

5. **Catch-up uses `self._*` state dicts, not local ones.** Unlike the
   existing 2-candle post-close cooldown (local `cooldown_until` dict),
   R1/R2 state carries across catch-up → tick boundaries. Local dicts
   would be wrong because tick needs the R1 cooldown armed by a catch-up
   trade.

## Risks / known issues

- The CSV 4-decimal truncation means any downstream consumer comparing
  live to backtest CSV must tolerate ≤1e-4 weight_factor diffs. Noted
  in the parity script and research brief.
- Catch-up is currently bounded to "previous month start" by
  `_previous_month_start_ms(now_ms)`. For the parity test I monkey-patched
  `time.time()`. For production use, catch-up only needs to cover gaps
  since the engine was last running, so this bound is fine.
- No R1/R2 state persistence beyond SQLite trade history. This is
  intentional — on restart, state reconstructs deterministically from
  the DB, avoiding any persist/restore skew.
