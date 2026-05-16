# Phase 5.5 Gate — iter-v3/059

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 UNCHANGED; IS 2023-03-24 to 2025-03-23, OOS 2025-03-24 onward
- Section 0.5 (Iteration Type): PASS — TYPE=RE-ANCHOR #2, orthogonal to cycle counting, NOT a cycle 1 EXPLORATION
- Section 1 (Hypothesis): PASS — Single specific hypothesis: /028 bundle under unified 10-seed ensemble (Phase B-3 `ab2d9ac`) + Optuna n_jobs=2 (`0a3c30e`) + post-fix walk-forward (`e149e9d`) produces new canonical BASELINE_V3.md
- Section 2 (IS-Only Evidence): PASS — RE-ANCHOR #2; no new EDA required; citations to BASELINE_V3.md /028 bundle spec + Phase A/B/fix commit SHAs; prior architecture comparison table provided
- Section 3 (Proposed Changes): PASS — Single change: ITERATION_LABEL="v3-059"; all other constants already set by Phase B-3 commit `ab2d9ac`; carry-forward state enumerated
- Section 4 (Expected OOS Impact): PASS — Predicted bands locked: IS [+0.55, +0.85]; OOS [+0.65, +0.95]; explicit falsifier: either axis < +0.40 triggers investigation; 4-path classification pre-committed
- Section 5 (Risk Mitigation): PASS — Same 7-primitive gate stack as /058; no new code paths; architecture change is runner-level only
- Section 6 (Risk Management Design): PASS — 8-primitive table provided with UNCHANGED status for all gates; thresholds unchanged
- Section 7 (Failure-Mode Prediction): PASS — 3 failure modes pre-registered with probability estimates; RE-ANCHOR-COLLAPSE (15-25%) and RE-ANCHOR-IS-DOMINANT (20-30%) as most plausible
- Section 8 (MERGE/NO-MERGE Criteria): PASS — RE-ANCHOR MERGE criteria locked; MANDATORY BASELINE_V3.md update; Pareto Gate 10 RETIRED; NEW Gate 10-CPCV (frac_positive_paths >= 0.55); path adjudication pre-committed
- Section 9 (Library Stack): PASS — Unchanged from /058; lightgbm 4.6.0, optuna 4.8.0 (n_jobs=2 via Phase A), all versions pinned
- Section 10 (QR Audit Trail): PASS — RE-ANCHOR mandate documented; commit chain cited; cycle counting clarified (RE-ANCHOR #2 orthogonal to cycle 1); setup SHA backfill slot present
- Section 11 (Catalog Row): PASS — Pre-committed catalog row template provided; NOT counted toward cycle 1 cadence

## Bundle State Verification

### V3_FEATURE_COLUMNS_TOP_N (14 features — PASS, matches /028 spec)

Verified by `uv run python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N; print(list(V3_FEATURE_COLUMNS_TOP_N))"`:

```
['max_dd_window_50', 'ema_spread_atr_20', 'ret_kurt_50', 'ret_skew_200',
 'range_realized_vol_50', 'hurst_diff_100_50', 'ret_kurt_200', 'hurst_100',
 'btc_ret_14d', 'ret_skew_50', 'vwap_dev_20', 'ret_autocorr_lag1_50',
 'sym_vs_btc_ret_7d', 'regime_momentum_signed_5d']
```

- Count: 14 — PASS
- ret_skew_50 PRESENT — PASS
- regime_momentum_signed_5d PRESENT — PASS
- sym_vs_btc_ret_7d PRESENT — PASS
- parkinson_gk_ratio_20 ABSENT — PASS
- efficiency_ratio_50 ABSENT — PASS
- fracdiff_d05_close ABSENT — PASS

### Per-symbol config (PASS)

- V3_ATR_MULTIPLIERS_PER_SYMBOL: {} (EMPTY) — PASS
- DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0) — PASS
- V3_FEATURES_PER_SYMBOL: {} (0 entries) — PASS
- features_for_symbol("BCHUSDT"): 14 — PASS
- features_for_symbol("LDOUSDT"): 14 — PASS
- features_for_symbol("TRXUSDT"): 14 — PASS
- atr_multipliers_for_symbol("BCHUSDT"): (2.0, 1.0) — PASS
- atr_multipliers_for_symbol("LDOUSDT"): (2.0, 1.0) — PASS
- atr_multipliers_for_symbol("TRXUSDT"): (2.0, 1.0) — PASS

### Runner constants (PASS)

- ITERATION_LABEL: "v3-059" — PASS
- ENSEMBLE_SIZE: 10 — PASS
- len(ENSEMBLE_SEEDS): 10 — PASS
- ENSEMBLE_SEEDS[0:5] = outer=42 lineage: (191664963, 1662057957, 1405681631, 942484272, 929893137) — PASS
- ENSEMBLE_SEEDS[5:10] = outer=123 lineage: (33158374, 1465339467, 1273345680, 115579757, 1952249162) — PASS
- OOS_CUTOFF_DATE: "2025-03-24" — PASS
- TRAINING_MONTHS: 24 — PASS
- REQUIRED_GAP: 66 = (21+1)×3 — PASS
- CPCV_EMBARGO: 27 — PASS

### _verify_feature_columns ENSEMBLE_SIZE=10 assertion (PASS)

Assertion confirmed at run_baseline_v3.py lines 271-274:
```python
assert ENSEMBLE_SIZE == 10, (
    f"iter-v3/059+ requires ENSEMBLE_SIZE=10; got {ENSEMBLE_SIZE}. ..."
)
```

### --seeds deprecation (PASS)

`--seeds` flag preserved for backward compatibility; logs warning if passed and is ignored.
Runner proceeds with ENSEMBLE_SIZE=10 unified architecture regardless of --seeds value.

## Foundation Audit (Boot Steps 9-11)

### Walk-forward embargo fix verified (Boot Step 9 — PASS)

`compute_embargo_candles` helper exists and is used in `generate_monthly_splits`:
- `train_end_ms = test_start_ms - embargo_ms` (embargo = 22 candles × 480 min/candle × 60000 ms/min)
- `lgbm._train_for_month()` reuses same helper for `cv_gap = 22 × 3 = 66 = REQUIRED_GAP`
- Single source of truth verified.

### Regression test confirmation (Boot Step 10 — PASS)

Smoke test output confirms all _verify_feature_columns checks pass:
```
V3_FEATURE_COLUMNS: 14 columns ... PASS
DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) ... PASS
V3_FEATURES_PER_SYMBOL: 0 entries ... PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL: 0 entries ... PASS
BCH/LDO/TRX: 14-feature universal fallback ... PASS
atr_multipliers_for_symbol: BCH/LDO/TRX all (2.0, 1.0) ... PASS
Primitive 10 (direction-asymmetric kill switch): block_long_for=(); block_short_for=() ... PASS
regime_momentum_signed_5d PRESENT ... PASS
vol_normalized_ret_5d ABSENT ... PASS
hurst_drift_50_200 ABSENT ... PASS
regime_momentum_signed_3d ABSENT ... PASS
efficiency_ratio_50 ABSENT ... PASS
Per-symbol ADX threshold: {} (EMPTY) ... PASS
Primitive 11 (per-symbol drawdown brake): enable=False ... PASS
Label-leakage gap: (timeout_candles=21+1) * n_symbols=3 = 66 [matches REQUIRED_GAP=66] PASS
Track isolation (features_v3 does not import v1/v2): PASS
```

Runner started: "BASELINE v3 iter-v3-059: BCHUSDT, LDOUSDT, TRXUSDT (seed-plumbing fix)"
"Ensemble: 10 seeds (unified)  Optuna trials/model: 1"

### Anti-Pattern Static Scan (Boot Step 11 — PASS)

- A1 (walk-forward lookahead): embargo fix at `e149e9d` present; `generate_monthly_splits`
  applies `train_end_ms = test_start_ms - embargo_ms` — CLEAN
- A5 (master-data-extent invariance): no changes to training data loading — CLEAN
- A7 (OOF parquet guardrail): `--clean-oof` required for backtest run — CLEAN
- A8 (stateful gate deadlock): no new gate primitives; block_long_for=() — CLEAN
- A12 (DSR/PSR granularity): DSR_relative gate operative; legacy DSR informational — CLEAN
- A13 (written-before-read): no new file I/O paths — CLEAN
- Track isolation: `grep` for "from crypto_trade.features " in features_v3/ = EMPTY — CLEAN
- Feature columns pinned: ENSEMBLE_SEEDS passed as explicit 10-tuple; ENSEMBLE_SIZE=10
  enforced by assertion — CLEAN

## Data Freshness (Pre-flight)

Re-fetch required: BCHUSDT, LDOUSDT, TRXUSDT, BTCUSDT were 18.8h stale.
Re-fetch completed: `uv run crypto-trade fetch --symbols BCHUSDT,LDOUSDT,TRXUSDT,BTCUSDT --intervals 8h`
Result: 2 new klines per symbol. Data now fresh.
Smoke test data freshness check: PASS (no stale-data RuntimeError after re-fetch).

## Track Isolation Check

`grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` = empty — PASS

## Forming-Candle Filter

`fetcher.py` filter `if k.close_time < now_ms` present — PASS (unchanged from /058).

## Summary

All 11 brief sections: PASS
Bundle state: PASS (14 features, matches /028 spec; all per-symbol configs EMPTY)
ENSEMBLE_SIZE=10 assertion: PASS
ENSEMBLE_SEEDS 10-tuple lineage: PASS
Foundation Audit (Boot Steps 9-11): PASS
Anti-Pattern Catalog (13 entries): CLEAN
Data freshness: PASS (re-fetched)
Sacred constants: PASS (OOS_CUTOFF_DATE=2025-03-24, training_months=24 UNCHANGED)

**OVERALL: PASS — Phase 6 authorized.**
