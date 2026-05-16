# Phase 5.5 Gate — iter-v3/069

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 confirmed immutable; training_months=24 confirmed immutable; Section 0.5 declares EXPLORATION type (cycle 1 #10 of 10); 4-symbol universe (BCH+LDO+TRX+ADA) stated; IS/OOS windows in absolute dates.
- Section 1 (Hypothesis): PASS — One sentence; specifics present (mean_z_dist 0.6524, REQUIRED_GAP 66→88, predicted IS Δ [-0.50, +0.27], predicted OOS Δ [-0.50, +0.36]); well-calibrated probability distribution; not vague.
- Section 2 (IS-Only Evidence): PASS — committed script at `analysis/iteration_v3-069/universe_expansion_eda.py` (SHA 95038dd); T0-T6 tables; all T0 anchor values verified bit-exact against `reports-v3/iteration_v3-060/comparison.csv` (see verification notes below); IS-window EDA only.
- Section 3 (Proposed Changes): PASS — Enumerated: (1) V3_MODELS +ADAUSDT, (2) REQUIRED_GAP 66→88, (3) label_timeout REVERT 20160→10080, (4) ITERATION_LABEL bump; cross-iteration carry-overs listed; ONE substantive axis confirmed.
- Section 4 (Expected OOS Impact): PASS — Falsifier bands locked with numeric thresholds; disjunctive-OR PROMISING/NEGATIVE criteria; saturation falsifier with predicted IS trade band [194,209]; LDO OOS WR ±2pp falsifier; BCH IS WR ±5pp falsifier; SUSPICIOUS-OOS-DOMINANT sub-mode defined.
- Section 5 (Risk Mitigation): PASS — R1-R5 + R-NEW bundle-level trade-rate floor + BCH IS concentration sensitivity + LDO weakness pattern; all thresholds IS-calibrated; simulated historical effects stated.
- Section 6 (Risk Management Design): PASS — 7-primitive gate stack stated as BYTE-IDENTICAL to /060; ADA inherits universal gates; no new per-symbol customization; oracle-EDA validity stated for stateless gates.
- Section 7 (Failure-Mode Prediction): PASS — Probability distribution (INERT 45%, PROMISING 20%, NEGATIVE 25%, SUSPICIOUS-OOS-DOMINANT 10%) sums to 100%; mode-specific failure narratives; references /021 precedent.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Locked pre-registration: disjunctive-OR PROMISING threshold (IS Δ ≥ +0.10 OR OOS Δ ≥ +0.10); conjunctive-AND BUNDLE-INCLUSION threshold; NEGATIVE-CLOSE threshold; INERT zone; trade-rate-floor safety net; 4th-symbol minimum trade-rate floor.
- Section 9 (Library Stack): PASS — Full version list: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1; no new dependencies.

## Code Verification

### Constants
- ITERATION_LABEL = "v3-069": PASS (run_baseline_v3.py:128)
- OOS_CUTOFF_DATE = "2025-03-24": PASS (run_baseline_v3.py:81 — immutable)
- TRAINING_MONTHS = 24: PASS (run_baseline_v3.py:82 — immutable)
- label_timeout_minutes = 10080: PASS (run_baseline_v3.py:1425 — /068 Path C reverted)
- REQUIRED_GAP = 88 = (21+1)*4: PASS (validation_v3.py:58)
- Runtime assertion expected_label_timeout=10080: PASS (run_baseline_v3.py:729)
- Runtime assertion REQUIRED_GAP == 88: PASS (test_required_gap_matches_formula PASSED)

### V3_MODELS (4 symbols)
- ("A (BCHUSDT)", "BCHUSDT"): PASS
- ("C (LDOUSDT)", "LDOUSDT"): PASS
- ("D (TRXUSDT)", "TRXUSDT"): PASS
- ("F (ADAUSDT)", "ADAUSDT"): PASS — iter-v3/069 UNIVERSE EXPANSION axis
- test_v3_models_at_iter_v3_069: PASS (expected {BCH, LDO, TRX, ADA}, got exact match)

### Section 2 T0 Anchor Value Verification (bit-exact against reports-v3/iteration_v3-060/comparison.csv)
| anchor | brief | actual | match |
|---|---|---|---|
| monthly_sharpe IS | +0.8325 | +0.8325 | PASS |
| monthly_sharpe OOS | +0.1403 | +0.1403 | PASS |
| max_drawdown IS | 31.8701 | 31.8701 | PASS |
| max_drawdown OOS | 35.7804 | 35.7804 | PASS |
| n_trades IS | 159 | 159 | PASS |
| n_trades OOS | 102 | 102 | PASS |
| weighted_pnl_total IS | +51.8906 | +51.8906 | PASS |
| weighted_pnl_total OOS | +5.4989 | +5.4989 | PASS |
| dsr | 0.0 | 0.0 | PASS |
| pbo | 0.1278 | 0.1278 | PASS |
| psr | 0.9763 | 0.9763 | PASS |
| BCH OOS wpnl | +1.9078 | +1.9078 | PASS |
| LDO OOS wpnl | -19.7208 | -19.7208 | PASS |
| TRX OOS wpnl | +23.3119 | +23.3119 | PASS |
| BCH OOS n_trades | 37 | 37 | PASS |
| LDO OOS n_trades | 11 | 11 | PASS |
| TRX OOS n_trades | 54 | 54 | PASS |

Minor annotation note: brief Section 2.1 states TRX OOS win_rate=48.1%; actual per_symbol.csv shows 50.0% (27/54 = 50.0%). Difference is 1.9pp in a cosmetic annotation row. The T0 anchor values used by falsifier bands (Sharpe, drawdown, trades, wpnl) are all bit-exact. Not gate-blocking.

### Data Freshness
- ADAUSDT 8h: was stale (515h); FETCHED via `uv run crypto-trade fetch --symbols ADAUSDT --intervals 8h` (64 new klines); post-fetch age = 3.6h — PASS (<16h)
- ADAUSDT funding_rates: fetched via `uv run crypto-trade fetch-funding --symbols ADAUSDT` (6922 rows)
- BCHUSDT 8h: age=3.5h — PASS
- LDOUSDT 8h: age=3.5h — PASS
- TRXUSDT 8h: age=3.5h — PASS
- BTCUSDT 8h: age=3.5h — PASS

### ADAUSDT v3 Features
- Generated: `data/features_v3/ADAUSDT_8h_features.parquet` (6886 rows, 64 feature cols, 11.8s)
- V3_FEATURE_COLUMNS_TOP_N count: 14 — PASS
- All 14 features present in parquet: PASS (verified via pyarrow schema check)
  max_dd_window_50, ema_spread_atr_20, ret_kurt_50, ret_skew_200, range_realized_vol_50,
  hurst_diff_100_50, ret_kurt_200, hurst_100, btc_ret_14d, ret_skew_50, vwap_dev_20,
  ret_autocorr_lag1_50, sym_vs_btc_ret_7d, regime_momentum_signed_5d — ALL FOUND

### Track Isolation
- `grep -rP "from crypto_trade\.features " src/crypto_trade/features_v3/` — PASS (0 real imports; grep returned only comments/docstrings)
- `grep -rP "from crypto_trade\.features_v2 " src/crypto_trade/features_v3/` — PASS (0 matches)

### Feature Columns
- `feature_columns=list(features_for_symbol(symbol))` passed explicitly at run_baseline_v3.py:1435 — PASS
- _verify_feature_columns called before training at run_baseline_v3.py:2042 — PASS

### Mode-Flag Wiring
- EXPLORATION_ENSEMBLE_SIZE=3, CONFIRMATION_ENSEMBLE_SIZE=10 — PASS
- `args.exploration` routes to EXPLORATION_ENSEMBLE_SIZE at run_baseline_v3.py:2012 — PASS
- Brief specifies `--exploration` 3 seeds — PASS

### Label Leakage Gap
- embargo_candles = 10080 // 480 + 1 = 22
- cross-cell gap = 22 × 4 = 88 = REQUIRED_GAP — PASS
- Runtime assertion at _verify_label_leakage_gap() — PASS
- test_required_gap_matches_formula: REQUIRED_GAP==88 asserted — PASS

### Linter
- `uv run ruff check src/crypto_trade/features_v3/ src/crypto_trade/strategies/ml/validation_v3.py run_baseline_v3.py` — ALL CHECKS PASSED
- Pre-existing lint failures in old_runners/, notebooks, src/crypto_trade/live/ are unrelated to iter-v3/069 axis changes (confirmed via git diff — only validation_v3.py docstring modified in src/)

### Tests
- tests/features_v3/ + tests/strategies/ml/test_cpcv_embargo_assert.py: 176 passed, 3 skipped (0 failures)
- 3 skips are pre-existing (test_parkinson_gk_ratio_20_past_only.py swap tests — not active at current config)
- test_v3_models_at_iter_v3_069: PASS
- test_required_gap_matches_formula: PASS (REQUIRED_GAP==88)
- test_fracdiff_d05_close_present_in_all_4_symbol_parquets: PASS (includes ADAUSDT)
- test_regime_momentum_signed_3d_present_in_all_4_symbol_parquets: PASS (includes ADAUSDT)

### Docstring Fix Applied
- validation_v3.py:cpcv_walk_forward_splits docstring was stale (said "=110, 5-symbol"); fixed to "=88, 4-symbol BCH+LDO+TRX+ADA"; committed as fix(iter-v3/069) SHA ac401ea. No runtime change.

## Reasons (if BLOCK)
None.

## Summary
All 10 mandatory brief sections verified. Data fetched and fresh. ADAUSDT v3 features generated (14/14 columns). REQUIRED_GAP=88 matches formula. label_timeout=10080 reverted. Tests pass. Linter clean on all v3-iteration files. ONE substantive axis change. Sacred constants immutable. Track isolation clean.

Gate engineer: Claude Sonnet 4.6
Gate date: 2026-05-14
