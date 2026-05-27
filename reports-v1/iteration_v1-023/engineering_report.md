# Engineering Report — iter-v1/023

## Header

- **Iteration**: iter-v1/023
- **Branch**: `iteration-v1/023`
- **Commit SHA (backtest run)**: `74f5689` (feat commit with src/ changes + backtest at Phase 6)
- **Commit SHA (LM Master post-mortem)**: `4d6f1ed` (Phase 7.4 HEAD at Critic dispatch)
- **Current HEAD**: `36ec61f` (Phase 7.5 Critic BLOCK-PENDING-FIX)
- **Iteration type**: EXPLORATION — cycle-3 #8/10 — family `feature-family` (NEW 15th)
- **Hardware**: Intel i9-12900HK / 58 GB RAM
- **Wall-clock**: ~51 min Optuna portion (00:42:39 → 01:33:47 from log timestamps); total run ~58 min including feature loading, labeling, and reporting
- **Written retrospectively** under BLOCK-PENDING-FIX from Critic Phase 7.5 (review.md at `36ec61f`); no backtest re-run, no src/ changes.

---

## Verdict Summary — EXPLORATION-NEGATIVE

**F1 OOS Sharpe Δ = -0.2031** (observed OOS Sharpe +0.4606 vs anchor +0.6637 from BASELINE_V1.md).

Per brief Section 8 Row 6: F1 OOS Δ ∈ [-0.55, -0.10) → **NEGATIVE clean** — axis CLOSED for cycle-3.

The LM Master Phase 7.4 proposed a LEARNED-NEGATIVE sub-classifier (gain-share ABOVE uniform parity = v1 learns funding; OOS Δ negative = signal not sufficient). This sub-classification was **catalogued as a diary finding** but NOT accepted as a verdict elevation per `feedback_no_cheating.md` (pre-registered Row 6 wins; 3bp from INERT threshold is not post-hoc exploitable).

**Key structural finding** (catalogued in diary): v1 LEARNS funding (5.40% portfolio gain share > 2.38% uniform-parity; first NEW feature family in cycle-3 to clear parity). v3 DID NOT (/082 family combined 9.90% at 4 features = 2.475%/feature < 5.56% v3 parity; /019 rank 14/14). This v1-vs-v3 structural distinction is the load-bearing LEARNED-NEGATIVE observation.

---

## Configuration Diff vs Baseline (BASELINE_V1.md)

| Parameter | Baseline | iter-v1/023 |
|---|---|---|
| Symbols | BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT | **UNCHANGED** (full universe) |
| Model dispatch | A (BTC+ETH), C (LINK), D (LTC), E (DOT) | **UNCHANGED** (all 4 models) |
| Feature columns | V1_FEATURE_COLUMNS (56-col) | **V1_FEATURE_COLUMNS_PRUNED (42-col)** |
| NEW features | — | **funding_rate_zscore_30, funding_rate_zscore_90** (added at PRUNED positions 2 and 3) |
| ENSEMBLE_SIZE | 5 (baseline) | **3** (cycle-3 EXPLORATION budget) |
| n_trials | baseline default | **18** |
| Seeds | [42, 123, 456, 789, 1001] | **[42, 123, 456]** (first 3) |
| OOS_CUTOFF_DATE | 2025-03-24 | **UNCHANGED** |
| training_months | 24 | **UNCHANGED** |

**Src/ changes in 4 files** (commit `74f5689`):
- `src/crypto_trade/features_v1/funding_v1.py`: NEW module (track-isolated; zero v2/v3 imports)
- `src/crypto_trade/features_v1/__init__.py`: V1_FEATURE_COLUMNS_PRUNED extended 40 → 42 (z30+z90 added alphabetically); sanity assert updated to == 42
- `src/crypto_trade/features/__init__.py`: `funding_v1` group registered in GROUP_REGISTRY; `df['symbol'] = symbol` guard added to `process_symbol` before `generate_features`
- `run_baseline_v1.py`: iter-v1/023 dispatch branch added; pre-flight asserts for z30+z90 presence; `_iter021_fi_strategies` renamed to `_post_dispatch_fi_strategies` (carry-forward Critic /022 Rec #2); `_post_dispatch_fi_strategies` populated for all 4 models (A/C/D/E)

---

## Key Metrics Block

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---|---|---|
| Sharpe (daily annualized) | **+0.4121** | **+0.4606** | 1.1177 |
| Sortino | +0.4936 | +0.5439 | 1.1019 |
| Max Drawdown | 76.58% | 41.27% | 0.5389 |
| Win Rate | 40.2% | 44.0% | 1.0937 |
| Profit Factor | 1.0879 | 1.0870 | 0.9992 |
| Total Trades | 694 | 257 | 0.3703 |
| Calmar Ratio | 1.0081 | 0.6033 | 0.5985 |
| DSR (corrected) | 0.0 | 0.0 | — |
| n_eff | 9 | 9 | 1.0000 |
| n_eff_per_cell_median | 9 | 9 | 1.0000 |
| PSR (monthly vs 0) | 0.8350 | 0.6596 | 0.7900 |
| PSR (monthly vs 1) | 0.2146 | 0.2523 | 1.1759 |
| Total Net PnL % | +77.20% | +24.90% | 0.3225 |

**F1 OOS Sharpe Δ = +0.4606 − +0.6637 = −0.2031** → Section 8 Row 6 (NEGATIVE clean).

**Per-symbol OOS breakdown:**

| Symbol | Trades | Wins | Win Rate | Net PnL % | Avg PnL % | % of Total OOS PnL |
|---|---|---|---|---|---|---|
| LINKUSDT | 48 | 28 | 58.3% | +97.26% | +2.03% | +75.4% |
| DOTUSDT | 51 | 24 | 47.1% | +67.71% | +1.33% | +52.5% |
| BTCUSDT | 58 | 23 | 39.7% | +39.41% | +0.68% | +30.5% |
| ETHUSDT | 56 | 22 | 39.3% | -17.63% | -0.31% | -13.7% |
| LTCUSDT | 44 | 16 | 36.4% | -57.68% | -1.31% | -44.7% |

LTC drag is the dominant source of OOS underperformance (−44.7% of OOS PnL allocation); LINK strongest cohort (58.3% WR). LTC also shows ASYMMETRIC_ROTATION pattern consistent with /020/022 basin-relocation history.

---

## F-AXIS-MECHANISM #1–4 Measurements

### #1 Dual Gate — Feature Importance Rank + Family Gain-Share

Per brief Section 4.2 (LM Master §4 strengthened BINDING dual gate): INERT = rank ≥ 32/42 bottom-quartile AND gain-share < 4.0% on ≥ 3 cohorts; PROMISING-clean = rank ≤ 14/42 top-third AND gain-share ≥ 4.0% on ≥ 2 cohorts.

**Per-cohort funding family ranks and gain shares (computed from `in_sample/feature_importance_*.csv`):**

| Model/Cohort | z30 rank | z90 rank | z30 gain | z90 gain | Total gain | Family gain share | vs 4.76% parity |
|---|---|---|---|---|---|---|---|
| Model A (Pool BTC+ETH) | **12/42** | **11/42** | 1721.22 | 1926.68 | 53051.07 | **6.88%** | +2.12pp above |
| Model C (LINK) | **12/42** | **11/42** | 994.88 | 1016.43 | 35616.32 | **5.65%** | +0.89pp above |
| Model D (LTC) | **18/42** | **14/42** | 804.64 | 1094.52 | 51888.26 | **3.66%** | -1.10pp BELOW |
| Model E (DOT) | **18/42** | **10/42** | 603.61 | 1573.29 | 39650.40 | **5.49%** | +0.73pp above |
| **Portfolio** | **14/42** | **11/42** | 4124.36 | 5610.93 | 180206.05 | **5.40%** | **+0.64pp above** |

Uniform parity for 42 features = 2.38% per feature. 2-feature family uniform parity = 4.76%.

**DUAL GATE verdict per cohort:**
- Model A Pool: z90 rank 11 + z30 rank 12 (top-third < 14/42 ≥ 2 features) + gain-share 6.88% ≥ 4.0% → **PROMISING-clean signal** for Pool A
- Model C LINK: z90 rank 11 + z30 rank 12 + gain-share 5.65% ≥ 4.0% → **PROMISING-clean signal** for C
- Model D LTC: z90 rank 14 + z30 rank 18 (z30 miss top-third) + gain-share 3.66% < 4.0% → **INERT-partial** for D
- Model E DOT: z90 rank 10 + z30 rank 18 (z30 miss top-third) + gain-share 5.49% ≥ 4.0% → **PROMISING-clean signal** for E
- Portfolio: z90 rank 11 + z30 rank 14 (exactly at threshold) + gain-share 5.40% ≥ 4.0% → **PROMISING-clean at portfolio level**

**DUAL GATE composite**: PROMISING-clean on 3/4 model cohorts (A, C, E); INERT-partial on LTC (D). Combined portfolio above parity.

**Section 8 interaction**: Row 6 F-AXIS #1 column = "any" — the DUAL GATE PROMISING-clean finding (3/4 cohorts) cannot promote Row 6 → Row 1. Pre-registered Row 6 verdict is binding per `feedback_no_cheating.md`. The DUAL GATE PASS is catalogued as a LEARNED-NEGATIVE sub-classifier finding.

**ic_matrix.csv note**: The auto-generated `in_sample/ic_matrix.csv` does NOT contain funding-family rows because the IC matrix computes family-family pair correlations by family label, and `funding_rate_zscore_30/90` were registered under the `funding_v1` group which is not included in the ic_matrix family groupings (legacy groups only). The brief Section 2.3 pre-computed 25 individual IC pairs using `analysis/iteration_v1-023/funding_zscore_ic.csv` (commit `c3f4551`); all 25 IC values pass the |IC| < 0.7 threshold (max = +0.438 for LTC z90 vs MACD). Per Critic Check 4 reservation, the full 42-col IC expansion is deferred to /024 brief.

### #2 Trade Count

| Window | Pre-registered band | Observed | Result |
|---|---|---|---|
| IS | [500, 750] (±20% around 621) | **694** | **PASS** |
| OOS | [140, 240] (±25% around 189) | **257** | **OUTSIDE band** (+36%) |

OOS trade count 257 is 36% above the +25% upper bound (240). The OOS trade expansion is driven by the model finding signals across 5 symbols at the PRUNED feature set; with V1_FEATURE_COLUMNS_PRUNED 42 cols the confidence threshold tuning in Optuna converges at lower thresholds on average, admitting more trades per month OOS. Not a labeling error — OOS monthly trade counts show no zero-trade months (range 4-25 trades/month across 15 OOS months). Flagged for diary inspection but does not constitute a methodology issue.

### #3 n_eff_per_cell

| Window | Pre-registered band (LM Master [5, 10]) | Observed median | Min / Max | Result |
|---|---|---|---|---|
| IS | [5, 10] | **9** | 5 / 11 | **PASS** (median in band; p75=10; max=11 trivially above — note below) |
| OOS | [5, 10] | **9** | 5 / 11 | **PASS** |

n_eff = 9 is the modal LM Master prediction. Per-cell breakdown by symbol: BTCUSDT=9, DOTUSDT=9, ETHUSDT=9, LINKUSDT=9, LTCUSDT=8. n_eff_per_cell_max=11 is trivially above the declared upper band of 10. This is not anomalous — the band was declared as typical operating range; cell-level variance at the 11-trial outlier with 258 total cells is well within expected distributional spread. n_cells=258 consistent with 5-symbol × 53 walk-forward splits × 3-seed IS path (averaged). PASS.

### #4 IC Correlation vs Existing Features

Pre-verified in brief Section 2.3: 25 IC pairs, max |IC| = +0.438 (LTC z90 vs MACD line). All 25 values below 0.7 threshold. F-AXIS-MECHANISM #4 PASS.

Post-run note: `ic_matrix.csv` is missing funding-family rows (see #1 note above). The Section 2.3 pre-computation covers the 25 most critical IC pairs (z30 and z90 vs top-5 existing features per symbol). Critic Check 4 flagged this as a reservation but not a block. Confirmed PASS on available evidence.

---

## Implementation Summary

### New module: `src/crypto_trade/features_v1/funding_v1.py`

- `compute_funding_rate_zscore(kline_df, funding_df, window=30, clip=10.0)`: past-only rolling z-score. Uses `.shift(1)` to ensure window ends at t-1 before computing at t. Clips to [-10, 10].
- `compute_funding_rate_zscore_90(kline_df, funding_df, window=90, clip=10.0)`: 90-bar variant.
- `add_funding_v1_features(df, data_dir="data", windows=(30, 90), clip=10.0)`: reads `data/funding_rates/<symbol>.csv`, computes both windows, appends `funding_rate_zscore_30` and `funding_rate_zscore_90`.
- Timestamp alignment: `(funding_time // 60_000) * 60_000` handles Binance 8h boundary jitter.
- Track isolation: zero imports from `crypto_trade.features_v2` or `crypto_trade.features_v3` (AST-verified by test suite).

### V1_FEATURE_COLUMNS_PRUNED extension

`src/crypto_trade/features_v1/__init__.py` modified:
- `funding_rate_zscore_30` inserted at alphabetical position (between `cal_hour_norm` and `interact_natr_x_adx`)
- `funding_rate_zscore_90` inserted after z30
- Sanity guard assertion updated: `len(V1_FEATURE_COLUMNS_PRUNED) == 42` (was 40)

### Runner wiring: `run_baseline_v1.py`

- iter-v1/023 elif dispatch branch added (first in chain, guards on `iteration_label == 'v1-023'`)
- Pre-flight asserts: `funding_rate_zscore_30` and `funding_rate_zscore_90` in `active_feature_columns`
- `_iter021_fi_strategies` renamed to `_post_dispatch_fi_strategies` (carry-forward Critic /022 Rec #2 — this fixes the /020/021/022 feature importance gap pattern permanently; future elif branches populate the same list)
- `_post_dispatch_fi_strategies` populated for all 4 models (A/C/D/E) in /023 elif branch

---

## Wall-Clock and Timing

| Phase | Timestamp | Notes |
|---|---|---|
| Commit feat (src/ setup) | 2026-05-27 00:35:59 | `74f5689` |
| Phase 6.0 Critic pre-flight commit | 2026-05-27 00:40:06 | `f4d56b1` |
| Backtest start (first Optuna trial) | 2026-05-27 00:42:39 | Model A Trial 0 |
| Backtest end (last Optuna trial) | 2026-05-27 01:33:47 | Model E Trial 17 |
| comparison.csv written | 2026-05-27 01:34:08 | File mtime |
| **Total Optuna wall-clock** | **~51 min 8 s** | First → last trial |
| **Estimated total run** | **~58 min** | Including labeling, feature load, reporting |

Well within the 2h EXPLORATION HARD CAP. No kill-switch required.

**Per-model approximate timing** (from log interleaving, ENSEMBLE_SIZE=3 × 18 trials each):
- Model A (BTC+ETH pool, 2 symbols, 53 splits × 3 seeds): first trial 00:42:39 → seed 1 trial 17 ~00:42:54 (first seed ~15 s per split-batch; total ~4 min per seed × 3 = ~12 min for Model A)
- Model C (LINK, 1 symbol): lighter than A; ~8 min
- Model D (LTC, 1 symbol): similar to C; ~8 min
- Model E (DOT, 1 symbol): similar; ~8 min
- Reporting + ADF + IC matrix: ~8 min

---

## Test Suite

All tests verified at commit `74f5689` (no src/ changes in retrospective fix).

```
tests/features_v1/test_funding_v1.py    — 19 tests PASS
tests/test_lookahead_embargo.py         — 11 tests PASS (4 mandated regression + 7 additional)
Total: 30 tests PASS
```

**test_funding_v1.py (19 tests):**
- `TestImport::test_importable` — import smoke
- `TestPastOnlyInvariant::test_denominator_does_not_include_bar_t` — shift(1) guard
- `TestPastOnlyInvariant::test_spike_propagates_to_next_row_only` — single-step propagation
- `TestBurnIn::test_z30_first_30_rows_nan` — 30-bar window burn-in
- `TestBurnIn::test_z90_first_90_rows_nan` — 90-bar window burn-in
- `TestClip::test_extreme_z_scores_clipped` — ±10 clip
- `TestAlignment::test_jitter_absorbed_by_minute_rounding` — Binance timestamp jitter
- `TestUnmatchedKlines::test_unmatched_rows_produce_nan` — graceful missing data
- `TestTwoWindowOutput::test_both_columns_added` — both z30+z90 columns present
- `TestTwoWindowOutput::test_z90_smoother_than_z30` — longer window is smoother
- `TestV1FeatureColumnsPruned::test_length_is_42` — V1_FEATURE_COLUMNS_PRUNED == 42
- `TestV1FeatureColumnsPruned::test_zscore_30_present` — z30 in list
- `TestV1FeatureColumnsPruned::test_zscore_90_present` — z90 in list
- `TestTrackIsolation::test_no_features_v2_import` — AST parse: no v2 imports
- `TestTrackIsolation::test_no_features_v3_import` — AST parse: no v3 imports
- `TestFileNotFound::test_missing_cache_raises_file_not_found` — missing CSV error
- `TestMissingSymbol::test_missing_symbol_raises_key_error` — missing symbol error
- `TestDispatchPreFlight::test_funding_cols_in_pruned_feature_list` — dispatch pre-flight
- `TestNonNullCoverage::test_coverage_above_95_pct` — z30 ≥ 95% non-null after burn-in at n=700

**test_lookahead_embargo.py (11 tests):**
4 mandated regression tests (lines 120/163/232/261 from /021 brief) + 7 additional verifying embargo formula, train-test gap, and walk-forward CV gap formula consistency.

---

## Anomaly Notes

1. **Feature parquet regen incident (resolved before backtest)**: The initial attempt to run the backtest with existing parquets (pre-/023) would have failed at the pre-flight assert (`funding_rate_zscore_30 not in active_feature_columns`) because the funding features were not yet in the parquet files. The funding-rate feature columns are appended by `uv run crypto-trade features --track v1 --groups funding_v1` which writes to the v1 parquets. This was run prior to the backtest dispatch (documented in feat commit `74f5689` under "Parquet verification (all 5 symbols): z30 coverage 97.4%–100%, z90 coverage 99.4%–100%"). The pre-flight assert mechanism caught the "not in parquet" condition before any compute was spent; regen completed successfully; backtest proceeded. No data corruption — the parquets were simply incomplete before the feature generation step.

2. **ic_matrix.csv missing funding-family rows**: `reporting_v1.py` computes IC matrix only over the pre-defined legacy feature family groups. The `funding_v1` group is not included in the IC matrix groupings. This is a known limitation; Critic Check 4 flagged it as a reservation. Pre-computed Section 2.3 IC pairs (25 pairs, max |IC|=0.438) confirm all values below 0.7. The full 42-col IC matrix expansion is scoped to /024 methodology improvement.

3. **Mean of empty slice RuntimeWarning in reporting_v1.py:1072**: `np.nanmean` on an empty slice during IC matrix computation (when a feature family has no cross-family pair with the `funding_v1` group). Non-blocking warning; no impact on correctness. The reporting pipeline completed successfully.

4. **OOS trade count above pre-registered band (257 vs upper bound 240)**: OOS trades 257 is +7.1% above the +25% upper bound. Investigation: no zero-trade months; monthly breakdown is 4–25 trades across 15 OOS months (median ~17). The slight trade expansion is attributable to the PRUNED feature set's confidence threshold tuning admitting slightly more signals; not a labeling or feature pipeline bug. Flagged as diary-level note.

5. **Trade spot-check (10 random OOS rows)**: All 10 verified — entry/exit PnL math correct, exit_reason values in {stop_loss, take_profit, timeout, end_of_data}, weighted_pnl = net_pnl_pct × weight_factor. No anomalies found.

---

## Gate Efficacy

R5 (vol-target + low-NATR kill) disabled for this EXPLORATION (same as baseline). Fire rates all 0.0000. R1/R2/R3 enabled per model dispatch (C: R1; D: R1; E: R1+R2; A: R3 only). No R1/R2 gate statistics recorded in comparison.csv for this iteration (fire rates are only written for R5 explicitly). Gate efficacy analysis deferred to CONFIRMATION.

---

## LEARNED-NEGATIVE Sub-Classifier (Catalogued, NOT Verdict Elevation)

Per LM Master Phase 7.4 and Critic Phase 7.5 adjudication:

**v1 LEARNS funding** — portfolio family gain-share 5.40% > 2.38% uniform-parity (2-feature parity = 4.76%). This is the first NEW feature family in cycle-3 to clear uniform-parity threshold. DUAL GATE PROMISING-clean on 3/4 cohorts (A, C, E).

**v3 DID NOT learn funding** — v3/082 4-feature funding family combined gain-share 9.90% = 2.475%/feature < 5.56% v3 parity. v3/019 rank 14/14.

**Structural interpretation**: v1's pool Model A (joint BTC+ETH loss surface) provides more training data than v3's per-symbol models. Funding signal is learned but not sufficient: the OOS realization (-0.2031 Δ) suggests funding-rate regime information is informationally present in the model but the signal magnitude does not close the OOS gap. The ORACLE EDA mechanism (negative funding band = short-crowded mean-reversion) is causal but the trade roster at retraining relocates such that the 154% PnL concentration in the negative band does not persist.

This is catalogued as `LEARNED-NEGATIVE` subtype for /023 in the Phase 8 diary (NOT as a verdict class different from NEGATIVE).

---

## Status

OVERALL=READY-FOR-CRITIC (retrospective engineering report — Critic re-eval is single-pass post-fix per BLOCK-PENDING-FIX protocol)
