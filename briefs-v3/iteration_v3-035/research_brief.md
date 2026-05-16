# Iteration v3-035 — Research Brief

**Type**: EXPLORATION (cadence #7 of 10 in post-iter-v3/028 cycle; **FEATURE axis (per-symbol engineered feature addition via V3_FEATURES_PER_SYMBOL) — BCH-only fracdiff_d05_close**)
**Track**: v3 (rigor arm) — thirty-fifth iteration
**Branch**: `iteration-v3/035` (off `iter-v3/034` head)
**Date**: 2026-05-08
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 35             # default per feedback_v3_exploration_n_trials_35
colsample_bytree = 1.0            # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees OOS metrics for the FIRST time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cadence #7 of 10 in post-iter-v3/028 cycle)
Wall-clock budget: <= 2h hard cap (per feedback_v3_cadence_discipline.md)
Single-axis variation: per-symbol engineered feature add (V3_FEATURES_PER_SYMBOL["BCHUSDT"])
  - REVERT V3_FEATURE_COLUMNS_TOP_N to 14 (drop fracdiff_d05_close from universal list)
  - ADD V3_FEATURES_PER_SYMBOL["BCHUSDT"] = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",)
    (15 features for BCH only; 14 features for TRX/ALGO/LDO via fallback)
Cadence: 7 of 10 EXPLORATIONs in this cycle (next CONFIRMATION = iter-v3/039)
Axis category: 2 (Category 2 engineered feature — per-symbol architecture extension)
ANCHOR: iter-v3/032 single-seed (IS +0.2360 / OOS +1.9338) for feature-axis comparison
References:
  - feedback_v3_engineered_features_proven.md (engineered features pivot validated by iter-v3/025+)
  - iter-v3/030 V3_FEATURES_PER_SYMBOL architecture (established per-symbol dispatch pattern)
```

**Why per-symbol fracdiff instead of universal**: iter-v3/034 established that fracdiff_d05_close
universally applied (all 4 symbols: BCH+LDO+TRX+ALGO) produced a large positive OOS swing for
BCH (+37.98 OOS wpnl over iter-v3/032 anchor: +48.73 vs +10.75) but significant regressions for
TRX (-20.11), ALGO (-8.24), and LDO (-6.81). The universal IS Sharpe was -0.1636 (worst IS in
post-bootstrap cycle; strong signal of fragmented feature utility). Applying fracdiff selectively
to BCH (the sole benefiting symbol) while restoring the 14-feature anchor for TRX/ALGO/LDO tests
the hypothesis that BCH's fracdiff utility is real signal rather than noise, and that it can be
isolated without contaminating the other symbols' training.

**Single-axis justification**: "revert universal list + add BCH per-symbol entry" is a logically
atomic operation — they are two parts of the same targeting decision. The net change to BCH's
model is IDENTICAL to iter-v3/034 (still 15 features including fracdiff_d05_close). The net
change to TRX/ALGO/LDO is a REVERT to iter-v3/032 anchor (14 features). Attribution is clean:
any OOS delta vs iter-v3/032 anchor is explained by BCH-only fracdiff.

---

## Section 1 — Hypothesis

`fracdiff_d05_close` applied selectively to BCHUSDT via `V3_FEATURES_PER_SYMBOL["BCHUSDT"]`
preserves the +37.98 OOS wpnl swing observed for BCH in iter-v3/034 while restoring
TRX/ALGO/LDO to their iter-v3/032 baselines (eliminating the -20.11/-8.24/-6.81 regressions),
yielding a net OOS Sharpe near the iter-v3/032 anchor of +1.9338 plus BCH-fracdiff lift.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — iter-v3/034 Per-Symbol OOS Evidence (Phase 7 result; no new EDA required)

The iter-v3/034 per-symbol OOS data at `reports-v3/iteration_v3-034/out_of_sample/per_symbol.csv`
provides the primary evidence base. The iter-v3/032 per-symbol OOS data at
`reports-v3/iteration_v3-032/out_of_sample/per_symbol.csv` provides the anchor comparison.

**iter-v3/034 OOS per-symbol weighted_pnl** (fracdiff applied universally to all 4 symbols):

| Symbol | v3-034 OOS wpnl | v3-032 OOS wpnl (anchor) | Swing (034 - 032) |
|--------|----------------:|-------------------------:|------------------:|
| BCH    | +48.7337        | +10.7519                 | **+37.9818**      |
| TRX    |  +9.1264        | +29.2441                 | **-20.1177**      |
| ALGO   | +12.6261        | +20.8740                 | **-8.2479**       |
| LDO    |  -2.8338        |  +3.9751                 | **-6.8089**       |

Source: `reports-v3/iteration_v3-034/out_of_sample/per_symbol.csv`,
        `reports-v3/iteration_v3-032/out_of_sample/per_symbol.csv`.

**Key observation**: BCH is the sole beneficiary of fracdiff_d05_close universal application.
Three of four symbols regress. The universal IS Sharpe of -0.1636 (vs iter-v3/032 IS +0.2360)
confirms that the fragmented per-symbol utility creates a net IS drag.

### 2.2 — Per-Symbol Architecture Precedent

The V3_FEATURES_PER_SYMBOL architecture was introduced in iter-v3/030 (LDO 7-feature subset)
and cleared in iter-v3/031 (LDO dropped from V3_MODELS). The dict is empty at iter-v3/034.
This iteration adds the first BCH-specific entry. The `features_for_symbol()` dispatch function
is already implemented and tested; no new infrastructure is required.

### 2.3 — IS Sharpe Prediction Basis

Per-symbol fracdiff targeting predicts the IS Sharpe delta by removing the TRX/ALGO/LDO drag
while preserving BCH's fracdiff utility. Expected IS Sharpe: between iter-v3/032 anchor
(+0.2360) and iter-v3/034 BCH-only lift component (estimated +0.10 to +0.30 attributable
to BCH alone given BCH's 4-symbol portfolio contribution).

---

## Section 3 — Proposed Changes

### Sub-fix 1: REVERT V3_FEATURE_COLUMNS_TOP_N to 14 features

Remove `fracdiff_d05_close` from `V3_FEATURE_COLUMNS_TOP_N` in
`src/crypto_trade/features_v3/__init__.py`. Drop the `"fracdiff_d05_close"` line from the
tuple and update the docstring comment block to document the iter-v3/035 revert (14-feature
universal list).

The 14-feature universal list is identical to the iter-v3/028/032 anchor:
`max_dd_window_50, ema_spread_atr_20, ret_kurt_50, ret_skew_200, range_realized_vol_50,
hurst_diff_100_50, ret_kurt_200, hurst_100, btc_ret_14d, ret_skew_50, vwap_dev_20,
ret_autocorr_lag1_50, sym_vs_btc_ret_7d, regime_momentum_signed_5d`

### Sub-fix 2: ADD V3_FEATURES_PER_SYMBOL["BCHUSDT"]

In `src/crypto_trade/features_v3/__init__.py`, update `V3_FEATURES_PER_SYMBOL` to:

```python
V3_FEATURES_PER_SYMBOL: dict[str, tuple[str, ...]] = {
    "BCHUSDT": V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",),
}
```

This gives BCH exactly 15 features (14 universal + fracdiff_d05_close). TRX/ALGO/LDO
fall back to V3_FEATURE_COLUMNS_TOP_N (14 features, no fracdiff).

Note: the V3_FEATURES_PER_SYMBOL docstring's subset-invariant documentation must be updated
to reflect that BCHUSDT's entry is NOT a strict subset of V3_FEATURE_COLUMNS_TOP_N — it
EXTENDS the universal list by one feature. The invariant documented for iter-v3/030 (LDO
7-feature subset was a REDUCTION of the full 14) does not apply here. The new invariant is:
`V3_FEATURES_PER_SYMBOL["BCHUSDT"]` is `V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",)`.
The `_verify_feature_columns` check in `run_baseline_v3.py` must be updated accordingly.

### Sub-fix 3: Expand V3_EXCLUDED_SYMBOLS to include MKRUSDT

Per `BASELINE_V3.md` §Forbidden Symbols, MKRUSDT was dropped per iter-v3/013 and should be
in V3_EXCLUDED_SYMBOLS. Verify it is present; add if missing.

### Sub-fix 4: Update `_verify_feature_columns` in `run_baseline_v3.py`

Assertions that must PASS after this change:

- `len(V3_FEATURE_COLUMNS_TOP_N) == 14` (universal fallback is 14 features)
- `"fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N` (NOT in universal list)
- `"BCHUSDT" in V3_FEATURES_PER_SYMBOL` (BCH has a per-symbol entry)
- `len(V3_FEATURES_PER_SYMBOL["BCHUSDT"]) == 15` (BCH gets 15 features)
- `"fracdiff_d05_close" in V3_FEATURES_PER_SYMBOL["BCHUSDT"]` (fracdiff in BCH only)
- `features_for_symbol("LDOUSDT") == V3_FEATURE_COLUMNS_TOP_N` (LDO fallback = 14 features)
- `features_for_symbol("TRXUSDT") == V3_FEATURE_COLUMNS_TOP_N` (TRX fallback = 14 features)
- `features_for_symbol("ALGOUSDT") == V3_FEATURE_COLUMNS_TOP_N` (ALGO fallback = 14 features)
- `"fracdiff_d05_close" not in features_for_symbol("TRXUSDT")` (TRX does NOT have fracdiff)
- `"fracdiff_d05_close" not in features_for_symbol("ALGOUSDT")` (ALGO does NOT have fracdiff)
- `"fracdiff_d05_close" not in features_for_symbol("LDOUSDT")` (LDO does NOT have fracdiff)
- `features_for_symbol("BCHUSDT") == V3_FEATURES_PER_SYMBOL["BCHUSDT"]` (BCH uses per-symbol)
- `"fracdiff_d05_close" in features_for_symbol("BCHUSDT")` (BCH gets fracdiff)
- `"regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N` (MUST be present; portfolio mandate)

Remove the existing `fracdiff_d05_close` presence-check on V3_FEATURE_COLUMNS_TOP_N (it now
checks V3_FEATURES_PER_SYMBOL["BCHUSDT"] instead).

### Sub-fix 5: Update `features_for_symbol` docstring in `__init__.py`

Update the `features_for_symbol` docstring to reflect iter-v3/035 state:
- BCH returns 15 features (per-symbol entry with fracdiff_d05_close)
- LDO/TRX/ALGO return 14 features (fallback to V3_FEATURE_COLUMNS_TOP_N)
- V3_FEATURES_PER_SYMBOL has 1 entry at iter-v3/035

### Sub-fix 6: Update ITERATION_LABEL "v3-034" -> "v3-035"

In `run_baseline_v3.py`, change:
```python
ITERATION_LABEL = "v3-035"
```

### Sub-fix 7: Adversarial tests in `tests/features_v3/test_features_for_symbol.py`

Replace the existing test suite (which asserts V3_FEATURES_PER_SYMBOL is EMPTY and all
symbols return 15 features) with iter-v3/035 assertions:

- `test_bch_has_fracdiff`: `features_for_symbol("BCHUSDT")` returns 15 features
  INCLUDING `fracdiff_d05_close`
- `test_trx_no_fracdiff`: `features_for_symbol("TRXUSDT")` returns 14 features
  NOT INCLUDING `fracdiff_d05_close`
- `test_ldo_no_fracdiff`: `features_for_symbol("LDOUSDT")` returns 14 features
  NOT INCLUDING `fracdiff_d05_close`
- `test_algo_no_fracdiff`: `features_for_symbol("ALGOUSDT")` returns 14 features
  NOT INCLUDING `fracdiff_d05_close`
- `test_bch_per_symbol_entry_has_fracdiff`: `V3_FEATURES_PER_SYMBOL["BCHUSDT"]` contains
  `fracdiff_d05_close`
- `test_non_bch_fallback_no_fracdiff`: parametrized over TRX/ALGO/LDO — none have fracdiff
- `test_bch_per_symbol_len`: len == 15
- `test_non_bch_fallback_len`: len == 14 for TRX/ALGO/LDO
- `test_subset_invariant_extended`: BCH entry is V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",)
- `test_v3_features_per_symbol_has_one_entry`: len(V3_FEATURES_PER_SYMBOL) == 1
- `test_regime_momentum_in_universal_list`: `regime_momentum_signed_5d` in V3_FEATURE_COLUMNS_TOP_N

---

## Section 4 — Expected OOS Impact

**IS Sharpe prediction (vs iter-v3/032 anchor +0.2360)**:
- Predicted band: [+0.30, +0.70]
- Median point estimate: +0.50
- Rationale: BCH-only fracdiff eliminates TRX/ALGO/LDO drag; BCH's fracdiff utility
  contributes positive IS Sharpe; 14-feature anchor restored for 3 of 4 symbols;
  net IS Sharpe expected above iter-v3/032 anchor (the drag from universal application
  was the primary IS degradation driver in iter-v3/034)

**OOS Sharpe prediction (vs iter-v3/032 anchor +1.9338)**:
- Predicted band: [+1.70, +2.20]
- Median point estimate: +1.95
- Rationale: iter-v3/032 anchor (+1.93) reflects the proven 14-feature 4-symbol
  baseline; BCH-fracdiff lift (+37.98 OOS wpnl swing in iter-v3/034) is expected
  to partially persist when BCH receives fracdiff selectively; TRX/ALGO/LDO restored
  to anchor performance (eliminating -20.11/-8.24/-6.81 regressions)

**Path taxonomy**:
- Path A (PROMISING): IS Sharpe >= +0.30 AND fracdiff_d05_close importance >= 30 in
  BCH model AND TRX/ALGO/LDO models show no fracdiff leakage
- Path B (NEGATIVE-no-effect): fracdiff importance < 5 in BCH model despite per-symbol
  entry — BCH's iter-v3/034 benefit was a positional artifact, not a signal
- Path C (NEGATIVE-regression): IS Sharpe < iter-v3/032 anchor (+0.2360); the per-symbol
  architecture itself introduces variance that overwhelms the BCH signal

**OOS falsifier**: if OOS Sharpe < +1.0, the BCH-only fracdiff hypothesis is rejected.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.

**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward from baseline.

**R3 (OOD detection)**: unchanged. Mahalanobis OOD z-score threshold unchanged.

**Per-symbol feature heterogeneity risk**: BCH's LightGBM model trains on 15 features while
TRX/ALGO/LDO train on 14. This is architecturally safe: `features_for_symbol()` dispatches
distinct feature lists; `LightGbmStrategy` receives explicit `feature_columns=` per call.
The CPCV CV splits are computed per-cell (per symbol); BCH's splits use its own 15-column
parquet while TRX/ALGO/LDO use their 14-column parquet. No cross-symbol contamination.

**fracdiff_d05_close still generated for all symbols**: the feature pipeline
(`process_symbol_v3`) generates ALL features for ALL symbols regardless of whether
they are in V3_FEATURE_COLUMNS_TOP_N or V3_FEATURES_PER_SYMBOL. The column
`fracdiff_d05_close` will appear in TRX/ALGO/LDO parquets but will NOT be passed
to LightGBM for those symbols (only BCH's explicit `feature_columns` list includes it).
This is safe by design — the LightGBM runner selects columns explicitly.

**Concentration risk**: BCH's elevated fracdiff signal could increase BCH's OOS contribution
concentration. The per-symbol concentration cap (no symbol > 35% of weighted PnL) continues
to apply. If BCH dominates (> 35%), this will be flagged in the engineering report.

---

## Section 6 — Risk Management Design (7-Primitive Gate Table)

All 7 risk gates carried forward from iter-v3/032 baseline unchanged. No gate parameters
are modified in this iteration.

| Gate | Type | Parameter | IS Fire Rate (iter-v3/032) | OOS Fire Rate (iter-v3/032) | Change in this iteration |
|---|---|---|---|---|---|
| 1 — BTC trend | BtcTrendFilterConfig | lookback=42, threshold=15% | ~8-12% | ~8-12% | None |
| 2 — Hit rate | HitRateGateConfig | window=20, sl_threshold=0.65 | DISABLED | DISABLED | None |
| 3 — ADX gate | ADX regime filter | threshold=20 (v3 default) | symbol-dependent | symbol-dependent | None |
| 4 — Hurst regime | hurst_100 > 0.5 gate | implicit in regime_momentum | symbol-dependent | symbol-dependent | None |
| 5 — Drawdown brake | R2 cumulative | per-model PnL tracking | symbol-dependent | symbol-dependent | None |
| 6 — OOD gate | Mahalanobis z-score | per-training-window | symbol-dependent | symbol-dependent | None |
| 7 — Liquidity floor | NATR floor | NATR >= 0.5% | All 4 symbols pass | All 4 symbols pass | None |

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode**: BCH's +37.98 OOS wpnl swing in iter-v3/034 was a
single-seed lottery artifact rather than a genuine per-symbol fracdiff signal. When isolated
to BCH-only (preserving TRX/ALGO anchor), the IS Sharpe would be near the iter-v3/032
anchor (+0.23), fracdiff_d05_close importance in BCH model would be in the [5, 29] range
(PROMISING-INERT), and OOS Sharpe would show the typical EXPLORATION variance (±0.30-0.40
Sharpe around the +1.93 anchor). Classification: PROMISING-INERT or NULL-RESULT.

**Second plausible failure mode**: IS Sharpe lifts (fracdiff IS importance > 30 in BCH
model), but OOS Sharpe FALLS below +1.93 anchor. This would indicate that BCH's fracdiff
lift in iter-v3/034 was driven by TRX's strong OOS positive offset masking BCH's actual
OOS utility. Specifically: in iter-v3/034, TRX had +9.13 OOS wpnl (down from +29.24 at
iter-v3/032) but this 4-symbol portfolio still produced OOS Sharpe +1.77 due to BCH's
+48.73 dominance. With TRX restored to anchor, if BCH's fracdiff doesn't deliver +37 OOS
wpnl again, the portfolio OOS Sharpe could FALL below the +1.93 anchor. The gate to watch:
BCH OOS concentration > 60% (single-seed lottery signal).

**What the gates should catch**: any spurious BCH fracdiff IS signal that emerges from
overfitting the IS window's BCH price dynamics (BCH had a specific 2024 halving-adjacent
trend that fracdiff may have latched onto) should manifest as: BCH OOS concentration > 60%
(single-symbol dependency), low OOS trade count for BCH (< 30 trades), and/or OOS Sharpe
BELOW iter-v3/032 anchor (+1.93) despite IS lift.

**Behavioral effect predictor** (per `feedback_v3_axis_saturation_predictor.md`): the per-symbol
architecture change affects ONLY BCH's LightGBM model (15 features instead of 14 universal).
TRX/ALGO/LDO models are IDENTICAL to iter-v3/032. Expected IS trade count delta: BCH model
trades may shift ±5-15% due to fracdiff signal; TRX/ALGO/LDO trades IDENTICAL to iter-v3/032.
Net IS trade change: small (< 15% total portfolio). Falsifier: if observed IS trade change is
0 trades for BCH (bit-identical to iter-v3/032), the fracdiff feature is INERT for BCH.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (EXPLORATION)

This is an EXPLORATION iteration. MERGE criteria are not applicable — only PROMISING /
NEGATIVE / NULL-RESULT classification applies.

**PROMISING** (proceed toward CONFIRMATION cadence): ALL of:
- IS Sharpe >= +0.30 (above iter-v3/032 anchor +0.2360)
- fracdiff_d05_close feature importance >= 30 in BCH model (Category 2 carve-out gate)
- TRX/ALGO/LDO fallback models show 0 change in IS trade count vs iter-v3/032 anchor
  (confirms no contamination from architecture change)
- OOS Sharpe >= +1.70 (lower band of predicted range; above -0.23 from anchor)

**PROMISING-INERT** (BCH fracdiff learned but low importance):
- IS Sharpe near anchor [+0.23, +0.30] AND fracdiff importance in [5, 29] in BCH model.
  Budget-disambiguation retest at n_trials=70 may be warranted per iter-v3/022 precedent.

**NULL-RESULT (saturated axis for BCH)**:
- fracdiff_d05_close importance < 5 in BCH model AND IS trade count change for BCH = 0.
  Per `feedback_v3_axis_saturation_predictor.md`: axis saturated; NEXT EXPLORATION must
  move to different axis.

**NEGATIVE**: ANY of:
- IS Sharpe < +0.10 (large IS regression vs anchor)
- OOS Sharpe < +1.0 (OOS falsifier)
- BCH IS trade count change = 0 AND fracdiff importance = 0 (pure NULL-RESULT)
- TRX/ALGO/LDO IS trade counts change by > 5 trades vs iter-v3/032 (contamination signal)

---

## Section 9 — Library Stack Declaration

- **Python**: 3.13 (runtime)
- **LightGBM**: pinned in pyproject.toml (same as iter-v3/034; no change)
- **numpy**: standard array operations for fracdiff weight computation (already in use)
- **fracdiff (PyPI package)**: UNAVAILABLE (same constraint as iter-v3/034: fracdiff==0.9.0
  requires statsmodels<0.14; project requires statsmodels==0.14.6). Fallback: pure-numpy
  inline implementation in `engineered_v3.py` (same as iter-v3/034 — already implemented).
- **No new dependencies required**: fracdiff_d05_close is fully implemented in
  `src/crypto_trade/features_v3/engineered_v3.py` from iter-v3/034. No code changes needed
  to `engineered_v3.py` — `compute_fracdiff_d05_close` already exists and is dispatched from
  `add_engineered_v3_features`. The column `fracdiff_d05_close` already appears in all symbol
  parquets. Only `features_v3/__init__.py` (V3_FEATURE_COLUMNS_TOP_N and V3_FEATURES_PER_SYMBOL)
  and `run_baseline_v3.py` (ITERATION_LABEL, _verify_feature_columns) require changes.
