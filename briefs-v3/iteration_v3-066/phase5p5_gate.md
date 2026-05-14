# Phase 5.5 Gate — iter-v3/066

OVERALL: PASS

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 declared unchanged
- Section 0.5 (Iteration Type + --exploration mode 3 seeds): PASS — TYPE=EXPLORATION, cycle 1 #7, --exploration mode, ENSEMBLE_SIZE=3, seeds=[191664963, 1662057957, 1405681631] (outer=42 lineage subset)
- Section 1 (Hypothesis): PASS — single sentence, specific mechanism (LDO OOS anti-Kelly correction at vol_scale_ceiling=1.0→0.8), expected delta stated (IS Δ≥+0.10 AND OOS Δ≥+0.20), falsifier implicit in Section 4 gates
- Section 2 (IS-Only Numerical Evidence): PASS — committed EDA at SHA `1d75cb0` (analysis/iteration_v3-066/risk_primitive_eda.py), 7 tables (T0-T6), IS-data-only ORACLE counterfactual on /060 trade roster (STATELESS primitive — ORACLE valid per feedback_v3_oracle_eda_validity.md)
- Section 3 (Proposed Changes): PASS — 9 sub-fixes enumerated; Sub-fix 7 (parquet regen NOT required) and Sub-fix 8/9 (UNCHANGED) explicitly declared
- Section 4 (Expected OOS Impact): PASS — Predicted Sharpe delta bands present (IS Δ∈[-0.20,+0.17], OOS Δ∈[-0.34,+0.31]); falsifier bands A.1-E.17 explicit; saturation falsifier D.14 present (per Critic /065 Rec #3 per-symbol WR Δ ±2pp requirement); disjunctive OR NEGATIVE criteria in Section 8.4
- Section 5 (Risk Mitigation): PASS — full risk primitive stack enumerated; single substantive change identified (vol_scale_ceiling 1.0→0.8); all disabled/closed primitives documented
- Section 6 (Risk Management Design): PASS — change translated to live trading impact; vol-scale band [0.3,0.8] universal / [0.5,0.8] TRX documented; per-primitive status table present
- Section 7 (Failure-Mode Prediction): PASS — 4 modes (INERT 50%, PROMISING 15%, SUSPICIOUS-OOS-DOMINANT 10%, NEGATIVE 25%); NEGATIVE probability ≥25% calibrated per feedback_v3_iter064_process_lessons.md Rule 3; INERT 50% rationale provided (ORACLE sub-band)
- Section 8 (MERGE/NO-MERGE Criteria): PASS — LOCKED PROMISING/INERT/SUSPICIOUS/NEGATIVE/NEGATIVE-SUSPICIOUS/Methodology-FAIL criteria at Sections 8.1-8.6; Section 8.4 NEGATIVE is disjunctive OR (IS Δ<-0.20 OR OOS Δ<-0.30) per Rule 4
- Section 9 (Library Stack Declaration): PASS — Python 3.13, LightGBM, pandas, pyarrow, statsmodels declared; vol-scale formula at risk_v2.py:594-610 cited with exact code path; integration test smoke commands declared

## Anchor-Value Correctness Check (CRITICAL per Critic /064 Rec #1 + /065 Rec #1 RECURRENCE)

Values from `reports-v3/iteration_v3-060/comparison.csv` — byte-exact match against Section 2.1 T0:

| Metric | Brief Section 2.1 T0 | comparison.csv actual | Match |
|---|---:|---:|:-:|
| monthly_sharpe IS | +0.8325 | 0.8325 | PASS |
| monthly_sharpe OOS | +0.1403 | 0.1403 | PASS |
| n_trades IS | 159 | 159 | PASS |
| n_trades OOS | **102** | **102** | PASS (brief has 102 — NOT 94 as flagged in /065) |
| weighted_pnl_total IS | +51.8906 | 51.8906 | PASS |
| weighted_pnl_total OOS | +5.4989 | 5.4989 | PASS |
| BCH OOS wpnl | **+1.9078** | **1.9078** | PASS (NOT +24.75) |
| LDO OOS wpnl | **-19.7208** | **-19.7208** | PASS (NOT -6.18; brief uses -19.7208 in T2/T3 and -19.72 shorthand — both correct) |
| TRX OOS wpnl | **+23.3119** | **23.3119** | PASS |

RECURRENCE check: /065 CRITICAL anchor errors (BCH OOS +24.75, LDO OOS -6.18, OOS trades 94) are NOT present in /066 brief. Section 2.1 T0 correctly declares BCH +1.9078, LDO -19.7208, TRX +23.3119, OOS trades 102. PASS.

## Implementation Checks

### Sub-fix 1 — RiskV2Config.vol_scale_ceiling=0.8
- Code: `run_baseline_v3.py` line ~1419 has `vol_scale_ceiling=0.8,` in RiskV2Config init
- Runtime verified: `_build_v3_model('BCHUSDT')` returns `strat.config.vol_scale_ceiling=0.8`
- PASS

### Sub-fix 2 — DEFAULT_ATR_MULTIPLIERS REVERT to (2.0, 1.0)
- Code: `src/crypto_trade/features_v3/__init__.py` line 222 has `DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.0)`
- Runtime verified: `DEFAULT_ATR_MULTIPLIERS=(2.0, 1.0)`, `atr_sl_multiplier=1.0`
- PASS

### Sub-fix 3 — ITERATION_LABEL = "v3-066"
- Code: `run_baseline_v3.py` line 128 has `ITERATION_LABEL = "v3-066"`
- PASS

### Sub-fix 4 — Test assertion updates
- `tests/features_v3/test_features_for_symbol.py`: function renamed `test_all_symbols_atr_default_iter_v3_066`, asserts `(2.0, 1.0)` throughout
- `tests/features_v3/test_atr_multipliers_for_symbol.py`: fully rewritten for iter-v3/066; all assertions on `(2.0, 1.0)`
- PASS

### Sub-fix 5 — Runner consistency assertion revert (DEFAULT_ATR_MULTIPLIERS)
- Code: `run_baseline_v3.py` ~line 416 checks `DEFAULT_ATR_MULTIPLIERS != (2.0, 1.0)`
- PASS

### Sub-fix 5b — Runner per-symbol fallback assertion revert
- Code: `run_baseline_v3.py` ~line 503 checks each symbol returns `(2.0, 1.0)`
- PASS

### Sub-fix 6 — New runtime assertion vol_scale_ceiling == 0.8
- Code: new block after per-symbol vol_scale_floor check (after line 688); builds BCHUSDT model, asserts `config.vol_scale_ceiling == 0.8`
- PASS

### Sub-fix 7 — Parquet regeneration NOT required
- vol_scale_ceiling is consumed at INFERENCE time in risk_v2.py; no new feature columns
- PASS (no action required)

## Additional Gate Checks

### Track Isolation
- `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` returns only comment strings — no actual v1 imports
- PASS

### Sacred Constants
- `OOS_CUTOFF_DATE = 2025-03-24` — unchanged
- `training_months = 24` — unchanged
- Inner ensemble seeds [42, 123, 456, 789, 1001] — unchanged
- PASS

### V3_FEATURE_COLUMNS_TOP_N Count
- 14 features (unchanged; NON-FEATURE axis means feature universe held constant)
- PASS

### Data Freshness
- BCHUSDT 8h.csv: close_time age = 12.9h (< 16h limit) — FRESH
- LDOUSDT 8h.csv: close_time age = 12.9h (< 16h limit) — FRESH
- TRXUSDT 8h.csv: close_time age = 12.9h (< 16h limit) — FRESH
- PASS

### Linter
- `uv run ruff check run_baseline_v3.py src/crypto_trade/features_v3/__init__.py tests/features_v3/test_features_for_symbol.py tests/features_v3/test_atr_multipliers_for_symbol.py` — All checks passed
- PASS

### Tests
- `tests/features_v3/`: 169 PASSED, 0 failed, 0 skipped (full suite run)
- `tests/strategies/ml/test_per_symbol_vol_scale_floor.py`: PASSED (vol_scale_ceiling parameterized)
- `tests/strategies/`: 293 total (4 pre-existing failures unrelated to /066: test_required_gap_matches_formula, test_derive_returns_correct_size, test_feature_count_15, test_new_064_features_present — all pre-date /066 and are tracked)
- `tests/live/test_feature_parity.py::TestFeatureParity::test_parquet_timestamps_match_kline_csv` FAILED — BNBUSDT parquet staleness; pre-existing; BNBUSDT not in V3_MODELS
- Net new failures from /066 changes: ZERO
- PASS

### Mode-Flag Wiring
- `--exploration` mode wires ENSEMBLE_SIZE=3, seeds from outer=42 lineage subset (brief Section 0.5 confirmed)
- PASS

### Implementation Commit
- SHA: `8598f1c` — committed BEFORE gate (per discipline: code committed before backtest)
- PASS

## Summary

All 10 mandatory brief sections present and valid. Anchor-value correctness gate: PASS (no recurrence of /065 anchor errors). All implementation sub-fixes applied and runtime-verified. Tests: zero new failures from /066 changes. Linter: clean on changed files. Data: fresh (12.9h). Sacred constants: unchanged.

OVERALL: PASS — proceed to Phase 6 backtest.
