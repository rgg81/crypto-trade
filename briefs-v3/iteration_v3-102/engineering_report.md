# Engineering Report — iter-v3/102

## Headers

- Iteration: iter-v3/102
- Branch: iteration-v3/102
- Phase 5.5 Gate commit SHA: bc2a30a
- Phase 6 setup commit SHA: 556c345
- Hardware: WSL2 Linux 6.6.114 (Roberto's workstation)
- Wall-clock time (setup only): ~15 min
- Backtest status: NOT YET RUN — setup-only per split-Engineer-dispatch protocol

## Configuration Diff vs Baseline (v0.v3-059)

The ONLY strategy-level change vs /059 is the addition of one feature column:

```
ITERATION_LABEL:        "v3-059" → "v3-102"
V3_FEATURE_COLUMNS:     14 columns → 15 columns (alpha032 appended)
```

All other /059-canonical parameters are unchanged:
- `V3_MODELS`: (BCH, LDO, TRX) — unchanged
- `training_months = 24` — IMMUTABLE, unchanged
- `OOS_CUTOFF_DATE = "2025-03-24"` — IMMUTABLE, unchanged
- `ATR_MULTIPLIERS`: (2.0, 1.0) for all 3 symbols — unchanged
- `label_timeout_minutes = 10080` (21 × 8h candles) — unchanged
- `ENSEMBLE_SEEDS`: 10-seed unified ensemble — unchanged
- `EXPLORATION_ENSEMBLE_SIZE = 3` — unchanged (EXPLORATION mode)
- CPCV n_paths=45, embargo=27, REQUIRED_GAP=66 — unchanged
- `RiskV2Config` 7-gate stack — unchanged

## alpha032 Implementation

**New module:** `src/crypto_trade/features_v3/formulaic_v3.py`

Per-symbol port of Kakushadze (2015) arXiv:1601.00991 Alpha#32:

```
alpha032 = scale_ts(7-bar SMA gap, 100) + 20 * scale_ts(vwap/lagged-close corr 230, 100)
```

where:
- `scale_ts(x, d)` = x / rolling_mean(|x|, d) — causal per-symbol proxy for Kakushadze's CS `scale`
- vwap = quote_volume / volume (per-bar proxy; known at t close)
- `delay(close, 5)` = close.shift(5) — strictly past
- `correlation(vwap, delay(close,5), 230)` = rolling Pearson, min_periods=230

All operators are past-only (min_periods = window length; .shift() for lags).

**GROUP_REGISTRY registration:** `"formulaic_v3"` → `add_formulaic_v3_features`

**V3_FEATURE_COLUMNS_TOP_N** (was 14, now 15):
```
# 14 BASELINE_V3 features unchanged...
"alpha032",  # formulaic_v3 [iter-v3/102 EXPLORATION axis]
```

## Pre-Flight Checks

1. **Data freshness**: PASS — BCH/LDO/TRX 8h CSVs age = 6.4h (< 16h threshold)
2. **Forming candles**: no re-fetch performed; CSVs from prior fetch with standard filter
3. **Track isolation grep**: PASS — 0 matches for `from crypto_trade.features ` or
   `from crypto_trade.features_v2` in `src/crypto_trade/features_v3/formulaic_v3.py`
4. **V3_FEATURE_COLUMNS** count: `len(V3_FEATURE_COLUMNS) == 15` — PASS
5. **`"alpha032" in V3_FEATURE_COLUMNS`**: PASS
6. **`ITERATION_LABEL == "v3-102"`**: PASS
7. **`_verify_feature_columns()`**: ALL PASS (full runner pre-flight)
8. **`V3_EXCLUDED_SYMBOLS` disjointness**: PASS (BCH/LDO/TRX ∩ excluded = ∅)

## Label Leakage Audit

Walk-forward embargo unchanged from /059:
- `compute_embargo_candles(10080, 480) = 22` candles
- `cv_gap = 22 × 3 = 66` (3 symbols)
- `train_end_ms = test_start_ms - embargo_ms` (the /058 lookahead fix `e149e9d`)

The `alpha032` feature is strictly causal:
- T3 adversarial audit: 0/54 look-ahead failures (all past_only_ok=True)
- Hard causality regression test (test_hard_causality): PASS — max_abs_diff = 0.0
  when 50 future bars are removed (bit-identical overlap)

## Tests

All tests PASS after Phase 6 implementation:

```
895 passed, 3 skipped, 204 warnings
```

New tests in `tests/features_v3/test_formulaic_v3.py` (11 tests):
- `test_import_smoke` — PASS
- `test_column_name` — PASS
- **`test_hard_causality`** — PASS (max_abs_diff = 0.0; causality verified)
- `test_nan_warmup_minimum` — PASS (bars 0..232 NaN, bar 499 non-NaN)
- `test_formula_correctness` — PASS (max_abs_diff < 1e-10 vs manual inline)
- `test_missing_quote_volume_raises` — PASS
- `test_missing_volume_raises` — PASS
- `test_missing_close_raises` — PASS
- `test_zero_volume_rows` — PASS (no crash)
- `test_add_formulaic_v3_features_registry` — PASS
- `test_v3_feature_columns_contains_alpha032` — PASS (count=15)

Updated tests (14→15 feature count assertions):
`test_features_for_symbol.py`, `test_fracdiff_d05_universal.py`,
`test_parkinson_gk_ratio_20_past_only.py`, `test_regime_momentum_signed_3d_universal.py`,
`test_hurst_drift_50_200_universal.py`, `test_v3_feature_count.py`,
`test_cross_sectional.py`, `test_universe_reselection_v3.py`.

Known out-of-scope failure: `tests/live/test_feature_parity.py::test_recent_candle_has_features`
(BTCUSDT environmental — requires live data; not related to this iteration).

## Parquet Regeneration

BCH/LDO/TRX feature parquets regenerated via:
```
uv run crypto-trade features --track v3 --symbols BCHUSDT,LDOUSDT,TRXUSDT --interval 8h --workers 3
```

alpha032 present in all 3 parquets:
- BCHUSDT: 6656/6989 valid rows (~95%)
- LDOUSDT: 3670/4003 valid rows (~92%)
- TRXUSDT: 6598/6931 valid rows (~95%)

Warm-up NaN count (~333 bars = 111 days) matches the expected 230-bar correlation
window dominating the feature's warm-up. All valid rows are non-degenerate
(BCHUSDT: mean=19.82, std=2.14 on synthetic verification).

## Smoke Test

`_verify_feature_columns()` PASS end-to-end, confirming:
- `len(V3_FEATURE_COLUMNS) == 15` — PASS
- `"alpha032" in V3_FEATURE_COLUMNS` — PASS
- `ITERATION_LABEL == "v3-102"` — PASS
- All incumbent absent-bans PASS (no banned features present)
- All V3_MODELS disjoint from V3_EXCLUDED_SYMBOLS — PASS

No `trial_oof_returns.parquet` artifacts in `/102` report dir (backtest not yet run).

## Launch Command

The full EXPLORATION backtest is NOT run in this setup-only phase.
The orchestrator must launch it detached:

```bash
uv run python run_baseline_v3.py --exploration --clean-oof
```

Estimated runtime: ~1.1h (3 symbols × 3 seeds × 35 trials × walk-forward months;
matches the /101 EXPLORATION wall-clock observed at identical spec).

## Status

OVERALL=SETUP-COMPLETE — backtest not yet launched
