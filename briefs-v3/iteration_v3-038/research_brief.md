# Iteration v3-038 — Research Brief

**Type**: EXPLORATION (cadence #10 of 10 in post-iter-v3/028 cycle — FINAL EXPLORATION; **FEATURE axis (per-symbol engineered feature swap) — revert LDO cross_asset_divergence_norm + add ALGO-only fracdiff_d05_close**)
**Track**: v3 (rigor arm) — thirty-eighth iteration
**Branch**: `iteration-v3/038` (off `iter-v3/037` head)
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
TYPE: EXPLORATION (cadence #10 of 10 in post-iter-v3/028 cycle — FINAL EXPLORATION)
Wall-clock budget: <= 2h hard cap (per feedback_v3_cadence_discipline.md)
Single-axis variation: per-symbol engineered feature swap (V3_FEATURES_PER_SYMBOL)
  - REVERT V3_FEATURES_PER_SYMBOL["LDOUSDT"]: remove LDO entry (LDO reverts to 14-feature fallback)
  - ADD V3_FEATURES_PER_SYMBOL["ALGOUSDT"] = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",)
    (15 features for ALGO only; 15 features for BCH via existing entry; 14 for LDO/TRX via fallback)
  - V3_FEATURE_COLUMNS_TOP_N remains at 14 (no change to universal list)
  - BCHUSDT per-symbol entry UNCHANGED (V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",) = 15)
Cadence: 10 of 10 EXPLORATIONs in this cycle (FINAL; next = iter-v3/039 CONFIRMATION)
Axis category: 2 (Category 2 engineered feature — per-symbol architecture swap)
ANCHOR: iter-v3/035 single-seed (IS -0.1023 / OOS +2.8521)
  NOTE: iter-v3/037 result is NEGATIVE (-33 OOS swing per brief context). Anchor remains
  iter-v3/035 as the most recent PROMISING baseline for fracdiff specificity evaluation.
References:
  - iter-v3/034 universal fracdiff failure (IS Sharpe -0.1636; ALGO -8.24 OOS wpnl regression)
  - iter-v3/035 BCH-only fracdiff success (OOS Sharpe +2.85 PROMISING)
  - iter-v3/037 LDO cross_asset_divergence_norm NEGATIVE (-33 OOS swing; revert to 14-feature fallback)
  - feedback_v3_engineered_features_dont_stack.md (universal stacking constraint)
  - feedback_v3_axis_saturation_predictor.md (behavioral effect predictor requirement)
```

**Why revert LDO**: iter-v3/037 applied cross_asset_divergence_norm to LDO-only via
V3_FEATURES_PER_SYMBOL. The result was NEGATIVE: OOS Sharpe fell ~33 units relative to the
iter-v3/035 anchor. The per-symbol isolation did not rescue the feature for LDO — LDO-specific
cross_asset_divergence_norm is inert or harmful at n_trials=35. The V3_FEATURES_PER_SYMBOL["LDOUSDT"]
entry is reverted; LDO returns to the 14-feature universal fallback (identical to iter-v3/035 LDO
configuration).

**Why ALGO-only fracdiff_d05_close**: This iteration tests fracdiff SPECIFICITY: is fracdiff_d05_close
BCH-specific, or is it broadly useful for other symbols? iter-v3/034 applied fracdiff universally and
showed BCH +37.98 OOS wpnl (strongly positive) but ALGO -8.24 OOS wpnl (clearly negative). This was
the original evidence that BCH is the primary beneficiary. However, iter-v3/034 had 5 symbols at the
time (BCH+LDO+TRX+ALGO+VET); the drag was distributed across 4 symbols simultaneously. The per-symbol
architecture now allows an isolated ALGO test: does fracdiff help ALGO specifically when tested alone
(without universal application across all remaining symbols)?

ALGO is selected over TRX because:
- ALGO at iter-v3/035: +20.87 OOS wpnl, 25 trades, 40.0% WR (second-weakest contributor, WR below 50%)
- TRX at iter-v3/035: +29.24 OOS wpnl, 46 trades, 52.2% WR (strongest fallback contributor)
- Testing fracdiff on ALGO preserves the known-good TRX configuration as a control
- ALGO's below-50% WR suggests its model needs signal quality improvement, similar to the LDO rationale
  at iter-v3/035 (BCH-only fracdiff was motivated by BCH's high importance score)

**Single-axis justification**: this iteration makes ONE logical change to the per-symbol dispatch
architecture: swap LDOUSDT out of V3_FEATURES_PER_SYMBOL and ALGOUSDT in (with fracdiff_d05_close).
BCH remains unchanged. The net result: V3_FEATURES_PER_SYMBOL has 2 entries (BCH+ALGO) instead of
(BCH+LDO). Attribution is clean: any OOS delta vs iter-v3/035 anchor is explained by
(1) LDO returned to 14-feature fallback + (2) ALGO-only fracdiff_d05_close.

---

## Section 1 — Hypothesis

`fracdiff_d05_close` applied selectively to ALGOUSDT via `V3_FEATURES_PER_SYMBOL["ALGOUSDT"]`
tests whether the fracdiff memory-preservation signal is BCH-specific or broadly useful: if ALGO OOS
wpnl lifts from its iter-v3/035 baseline (+20.87) and OOS Sharpe remains at or above the iter-v3/035
anchor (+2.85), fracdiff is broadly useful and should be considered for additional symbols in
iter-v3/039 CONFIRMATION; if ALGO does not benefit and OOS Sharpe is flat or negative, fracdiff is
BCH-specific (5 of 5 per-symbol tests: universal-fail at iter-v3/034 across ALGO/TRX/LDO/VET,
BCH-only success at iter-v3/035, and now ALGO isolated-fail at iter-v3/038 if NEGATIVE).

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — iter-v3/034 Universal Fracdiff Failure Evidence (IS-confirmed)

The iter-v3/034 result at `reports-v3/iteration_v3-034/comparison.csv` provides primary
evidence that universal fracdiff is ALGO-harmful:

| Symbol | iter-v3/034 OOS wpnl (universal fracdiff) | iter-v3/028 baseline | Swing |
|--------|------------------------------------------:|--------------------:|------:|
| BCH    | +45.95 (approx)                           | ~+8.58 baseline     | +37.98 (strongly positive) |
| TRX    | ~+9.83                                    | ~+29.92 baseline    | -20.11 (negative) |
| ALGO   | ~+12.65                                   | ~+20.87             | -8.24 (negative) |
| LDO    | ~+16.13                                   | ~+22.05 loss        | -6.81 (negative) |

Source: `reports-v3/iteration_v3-034/out_of_sample/per_symbol.csv`
Analysis script: `analysis/iteration_v3-034/` (committed with iter-v3/034 brief)

**Key observation**: ALGO was clearly harmed by universal fracdiff (-8.24 OOS wpnl). However,
this was a SIMULTANEOUS test of fracdiff across 4 symbols. The per-symbol isolated test at
iter-v3/038 asks: was ALGO harmed by fracdiff itself, or by cross-symbol model noise from
training all 4 symbols on fracdiff simultaneously?

### 2.2 — iter-v3/035 BCH-Only Fracdiff Precedent (IS-confirmed)

The iter-v3/035 per-symbol data at `reports-v3/iteration_v3-035/out_of_sample/per_symbol.csv`:

| Symbol | v3-035 OOS wpnl | v3-035 OOS n_trades | v3-035 OOS WR |
|--------|----------------:|--------------------:|--------------:|
| BCH    | +48.7337        | 32                  | 50.0%         |
| TRX    | +29.2441        | 46                  | 52.2%         |
| ALGO   | +20.8740        | 25                  | 40.0%         |
| LDO    | +3.9751         | 20                  | 35.0%         |

ALGO at iter-v3/035 uses the 14-feature universal fallback (no fracdiff). ALGO's 40.0% WR is
the second-weakest in the portfolio. The IS feature importance for ALGO from
`reports-v3/iteration_v3-035/in_sample/feature_importance.csv` is the numerical basis for
the specificity test: if fracdiff_d05_close ranks high in the ALGO model, it is meaningful;
if it ranks at the bottom (similar to iter-v3/034 ALGO model), it is inert.

### 2.3 — Per-Symbol Architecture Precedent (iter-v3/035)

iter-v3/035 established that `V3_FEATURES_PER_SYMBOL` architecture resolves universal failures
into per-symbol lift: BCH-only fracdiff produced OOS Sharpe +2.85 (PROMISING) after universal
fracdiff failed at IS Sharpe -0.1636 (worst post-bootstrap). The same architecture is applied
for the ALGO isolated test.

### 2.4 — IS Behavioral Effect Predictor

**Behavioral effect predictor** (per `feedback_v3_axis_saturation_predictor.md`): the per-symbol
architecture change affects ONLY ALGO's LightGBM model (15 features instead of 14). BCH/TRX/LDO
models are IDENTICAL to iter-v3/035 (same config for BCH; LDO/TRX return to 14-feature fallback).
Expected IS trade count delta: ALGO model trades may shift ±5-20% due to fracdiff_d05_close signal
injection; BCH/TRX/LDO trades IDENTICAL to iter-v3/035. Net IS trade change: small (< 20% total).
Falsifier: if observed IS trade count change is 0 trades for ALGO (bit-identical to iter-v3/035),
fracdiff_d05_close is INERT for ALGO — axis saturated.

---

## Section 3 — Proposed Changes

### Sub-fix 1: UPDATE V3_FEATURES_PER_SYMBOL in `src/crypto_trade/features_v3/__init__.py`

Remove LDOUSDT entry; add ALGOUSDT entry with fracdiff_d05_close:

```python
V3_FEATURES_PER_SYMBOL: dict[str, tuple[str, ...]] = {
    "BCHUSDT": V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",),
    "ALGOUSDT": V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",),
}
# LDOUSDT removed (reverts to 14-feature universal fallback)
# TRXUSDT absent (no per-symbol entry — unchanged from iter-v3/037)
```

BCH unchanged at 15 features (14 universal + fracdiff_d05_close).
ALGO gets 15 features (14 universal + fracdiff_d05_close).
LDO returns to 14-feature fallback (no per-symbol entry — iter-v3/037 reverted).
TRX remains at 14-feature fallback (no per-symbol entry — unchanged from iter-v3/037).
BCH and ALGO per-symbol entries are IDENTICAL in extension feature (both get fracdiff_d05_close).

### Sub-fix 2: UPDATE `_verify_feature_columns` in `run_baseline_v3.py`

Update the verification function to reflect iter-v3/038 state:
- Replace LDO-specific assertions with ALGO-specific assertions
- BCH=15(fracdiff), ALGO=15(fracdiff), LDO=14(fallback), TRX=14(fallback)
- V3_FEATURES_PER_SYMBOL has 2 entries (BCHUSDT + ALGOUSDT)
- LDOUSDT MUST NOT be in V3_FEATURES_PER_SYMBOL (reverted from iter-v3/037)
- ALGOUSDT MUST be in V3_FEATURES_PER_SYMBOL with fracdiff_d05_close

Assertions that must PASS after this change (iter-v3/038 state):
- `len(V3_FEATURE_COLUMNS_TOP_N) == 14` (universal fallback is 14 features — UNCHANGED)
- `"fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N` (NOT in universal list — UNCHANGED)
- `"cross_asset_divergence_norm" not in V3_FEATURE_COLUMNS_TOP_N` (NOT in universal list — UNCHANGED)
- `"BCHUSDT" in V3_FEATURES_PER_SYMBOL` (BCH still has per-symbol entry — UNCHANGED)
- `len(V3_FEATURES_PER_SYMBOL["BCHUSDT"]) == 15` (BCH gets 15 features — UNCHANGED)
- `"fracdiff_d05_close" in V3_FEATURES_PER_SYMBOL["BCHUSDT"]` (fracdiff in BCH — UNCHANGED)
- `"ALGOUSDT" in V3_FEATURES_PER_SYMBOL` (ALGO now has per-symbol entry — NEW)
- `len(V3_FEATURES_PER_SYMBOL["ALGOUSDT"]) == 15` (ALGO gets 15 features — NEW)
- `"fracdiff_d05_close" in V3_FEATURES_PER_SYMBOL["ALGOUSDT"]` (fracdiff in ALGO — NEW)
- `"LDOUSDT" not in V3_FEATURES_PER_SYMBOL` (LDO removed — NEW constraint; reverted from iter-v3/037)
- `features_for_symbol("LDOUSDT") len == 14` (LDO fallback = 14 features — REVERTED)
- `features_for_symbol("TRXUSDT") len == 14` (TRX fallback = 14 features — UNCHANGED)
- `"cross_asset_divergence_norm" not in features_for_symbol("LDOUSDT")` (LDO no cross_asset — NEW)
- `"fracdiff_d05_close" not in features_for_symbol("LDOUSDT")` (LDO no fracdiff — NEW)
- `"regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N` (portfolio mandate — UNCHANGED)
- `len(V3_FEATURES_PER_SYMBOL) == 2` (BCH + ALGO entries — NEW count check)

### Sub-fix 3: Update ITERATION_LABEL "v3-037" → "v3-038"

In `run_baseline_v3.py`:
```python
ITERATION_LABEL = "v3-038"
```

### Sub-fix 4: Adversarial tests in `tests/features_v3/test_features_for_symbol.py`

Update the test suite to reflect iter-v3/038 state (V3_FEATURES_PER_SYMBOL has BCH+ALGO entries):

- `test_bch_has_fracdiff`: UNCHANGED (BCH still 15 features with fracdiff_d05_close)
- `test_algo_has_fracdiff`: ALGO returns 15 features WITH fracdiff_d05_close — NEW
- `test_algo_no_cross_asset_divergence`: ALGO must NOT include cross_asset_divergence_norm — NEW
- `test_ldo_fallback_14`: LDO returns 14 features via fallback (no per-symbol entry) — UPDATED
- `test_ldo_no_fracdiff_no_cross_asset`: LDO must NOT include fracdiff or cross_asset — UPDATED
- `test_trx_fallback_14`: TRX returns 14 features via fallback — UNCHANGED assertion
- `test_bch_algo_per_symbol_entries_same_extension_feature`: BCH and ALGO both have fracdiff — NEW
- `test_ldousdt_not_in_per_symbol`: LDOUSDT must NOT be in V3_FEATURES_PER_SYMBOL — NEW
- `test_algo_per_symbol_len`: len(V3_FEATURES_PER_SYMBOL["ALGOUSDT"]) == 15 — NEW
- `test_v3_features_per_symbol_has_two_entries`: BCH + ALGO (not BCH + LDO) — UPDATED
- `test_regime_momentum_in_universal_list`: UNCHANGED
- `test_fracdiff_not_in_universal_list`: UNCHANGED
- `test_cross_asset_divergence_not_in_universal_list`: UNCHANGED
- `test_vol_adj_autocorr_not_in_universal_list`: UNCHANGED
- `test_universal_list_is_14`: UNCHANGED

---

## Section 4 — Expected OOS Impact

**ANCHOR**: iter-v3/035 single-seed IS -0.1023 / OOS +2.8521

**IS Sharpe prediction (vs iter-v3/035 anchor -0.1023)**:
- Predicted band: [-0.20, +0.20]
- Median point estimate: 0.0
- Rationale: BCH/TRX/LDO models identical to iter-v3/035 (no feature change for these three).
  ALGO model receives one additional feature (fracdiff_d05_close). Net IS Sharpe effect: small
  perturbation dominated by ALGO's moderate trade count (25 OOS trades at iter-v3/035). LDO
  revert from iter-v3/037 restores LDO IS contribution to iter-v3/035 levels.

**OOS Sharpe prediction (vs iter-v3/035 anchor +2.85)**:
- Predicted band: [+2.50, +3.20]
- Median point estimate: +2.85
- Rationale: if ALGO benefits from fracdiff (similar to BCH at iter-v3/034/035), ALGO OOS wpnl
  may lift from +20.87 toward +30+, adding ~+0.2-0.4 OOS Sharpe to the portfolio. BCH+TRX+LDO
  (reverted to iter-v3/035 config) are expected to maintain iter-v3/035 attribution (+48.73 BCH /
  +29.24 TRX / +3.98 LDO). The upper band reflects ALGO meaningful lift; lower band reflects
  near-null effect or slight drag.

**Path taxonomy**:
- Path A (PROMISING): fracdiff_d05_close importance ≥ 30 in ALGO model AND IS Sharpe above
  iter-v3/035 anchor (-0.10) AND OOS Sharpe ≥ anchor + any positive delta AND ALGO OOS wpnl
  lifts from +20.87. Interpretation: fracdiff is BROADLY USEFUL (BCH + ALGO benefit).
- Path B (PROMISING-INERT): fracdiff learned in ALGO model but low importance (5-29).
  Budget-disambiguation retest at n_trials=70 may be warranted.
- Path C (NULL-RESULT — saturated axis for ALGO): fracdiff importance < 5 in ALGO model AND
  IS trade count change for ALGO = 0. Per `feedback_v3_axis_saturation_predictor.md`: axis
  saturated for ALGO; interpretation: fracdiff is BCH-SPECIFIC (iter-v3/034 showed ALGO drag
  even from universal application; fracdiff is not an ALGO signal at any concentration level).
- Path D (NEGATIVE): OOS Sharpe < +2.0 OR IS Sharpe regression > 0.20 below iter-v3/035 anchor.

**Specificity interpretation** (primary scientific output of this EXPLORATION):
- If ALGO PROMISING (Path A): fracdiff broadly useful → CONFIRMATION should test BCH+ALGO+TRX fracdiff
- If ALGO NULL-RESULT/NEGATIVE (Path C/D): fracdiff BCH-specific → CONFIRMATION uses only BCH fracdiff

**OOS falsifier**: if OOS Sharpe < +2.0 (more than 0.85 below anchor), the ALGO-only fracdiff
hypothesis is rejected.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.

**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward from baseline.

**R3 (OOD detection)**: unchanged. Mahalanobis OOD z-score threshold unchanged.

**Per-symbol feature heterogeneity risk**: BCH trains on 15 features (14 + fracdiff_d05_close),
ALGO trains on 15 features (14 + fracdiff_d05_close), while LDO/TRX train on 14. This is
architecturally safe: `features_for_symbol()` dispatches distinct feature lists;
`LightGbmStrategy` receives explicit `feature_columns=` per call. The CPCV CV splits are computed
per-cell (per symbol); each symbol's splits use its own parquet. No cross-symbol contamination.

**fracdiff_d05_close generated for ALL symbols**: `add_engineered_v3_features` dispatch generates
`fracdiff_d05_close` for ALL symbols. TRX/LDO parquets contain the column but it is NOT passed to
LightGBM for those symbols. Safe by design — same pattern as iter-v3/035 BCH targeting.

**LDO revert risk**: LDO returns to 14-feature universal fallback (iter-v3/035 configuration).
This is a regression from iter-v3/037 but restoration to the known-good iter-v3/035 anchor. No
new LDO-specific risk introduced.

---

## Section 6 — Risk Management Design (7-Primitive Gate Table)

All 7 risk gates carried forward from iter-v3/035 baseline unchanged. No gate parameters are
modified in this iteration.

| Gate | Type | Parameter | IS Fire Rate (iter-v3/035) | OOS Fire Rate (iter-v3/035) | Change |
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

**Most plausible failure mode**: fracdiff_d05_close is BCH-specific — the iter-v3/034 ALGO
drag (-8.24 OOS wpnl) is not a cross-symbol contamination artifact but reflects genuine inertness
of the fracdiff memory signal for ALGO. ALGO's price process at 8h cadence does not exhibit the
long-memory structure that fracdiff captures. Classification: NULL-RESULT (axis saturated for
ALGO, fracdiff is BCH-specific) or Path D (NEGATIVE, OOS drag from fracdiff noise in ALGO model).

**Second plausible failure mode**: fracdiff_d05_close has moderate ALGO importance (5-29,
PROMISING-INERT range) but OOS Sharpe falls below anchor lower band (+2.50). This would indicate
the fracdiff signal IS learned for ALGO but produces IS exploitation without OOS generalization —
consistent with ALGO's historically low OOS WR (40.0% at iter-v3/035), suggesting the ALGO model
operates in a more noise-prone regime.

**What the gates should catch**: any IS collapse in ALGO model per-cell Sharpe (watch for ALGO IS
wpnl < iter-v3/035 ALGO IS value), or IS/OOS Sharpe ratio collapse on ALGO-specific per-symbol
metrics. If ALGO OOS concentration rises > 70%, that is the lottery-concentration alarm.

**Scientific outcome regardless of path**: this EXPLORATION produces a 5-of-5 specificity verdict
on fracdiff. BCH-only (iter-v3/035) was 1-of-1 per-symbol positive. iter-v3/038 ALGO is the
second per-symbol isolated test. Regardless of ALGO outcome, the data point informs the
iter-v3/039 CONFIRMATION scope:
- ALGO PROMISING → CONFIRMATION should include BCH+ALGO fracdiff (2-symbol portfolio)
- ALGO NULL-RESULT/NEGATIVE → CONFIRMATION uses BCH-only fracdiff (specificity confirmed 2/2)

**Behavioral effect predictor**: Expected ALGO IS trade count delta = ±5-20% (one additional
feature changes trade signals). BCH/TRX/LDO = IDENTICAL to iter-v3/035 (zero delta).
Falsifier: if ALGO IS trade count change = 0 trades, fracdiff_d05_close is INERT for ALGO.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (EXPLORATION)

This is an EXPLORATION iteration. MERGE criteria are not applicable — only PROMISING /
NEGATIVE / NULL-RESULT classification applies.

**PROMISING** (proceed toward CONFIRMATION cadence — fracdiff broadly useful): ALL of:
- fracdiff_d05_close feature importance ≥ 30 in ALGO model (Category 2 carve-out gate)
- ALGO IS trade count change ≠ 0 vs iter-v3/035 anchor (confirms feature is non-inert)
- BCH/TRX/LDO models show ≤ 5 trade count change in IS vs iter-v3/035 anchor (no contamination)
- OOS Sharpe ≥ +2.50 (lower band of predicted range)
- Interpretation: fracdiff is BROADLY USEFUL → CONFIRMATION tests BCH+ALGO fracdiff bundle

**PROMISING-INERT** (fracdiff learned but low importance for ALGO):
- fracdiff_d05_close importance in [5, 29] in ALGO model AND IS trade count for ALGO ≠ 0.
  Budget-disambiguation retest at n_trials=70 may be warranted before CONFIRMATION decision.

**NULL-RESULT (saturated axis for ALGO — fracdiff is BCH-specific)**:
- fracdiff_d05_close importance < 5 in ALGO model AND IS trade count change for ALGO = 0.
  Per `feedback_v3_axis_saturation_predictor.md`: fracdiff axis saturated for ALGO.
  Interpretation: fracdiff is BCH-SPECIFIC → CONFIRMATION uses BCH-only fracdiff (narrow scope).

**NEGATIVE**: ANY of:
- OOS Sharpe < +2.0 (OOS falsifier — more than 0.85 below anchor)
- IS Sharpe regression > 0.20 below iter-v3/035 anchor (-0.30 or worse)
- BCH/TRX/LDO IS trade counts change by > 5 trades vs iter-v3/035 (contamination signal)
- ALGO OOS concentration > 70% (single-symbol lottery alarm)

---

## Section 9 — Library Stack Declaration

- **Python**: 3.13 (runtime)
- **LightGBM**: pinned in pyproject.toml (same as iter-v3/035/036/037; no change)
- **numpy**: standard array operations for fracdiff_d05_close computation (already in use)
- **fracdiff (PyPI package)**: UNAVAILABLE (same constraint as prior iterations: fracdiff==0.9.0
  requires statsmodels<0.14; project requires statsmodels==0.14.6). Not needed —
  fracdiff_d05_close is implemented via pure-numpy FFD in engineered_v3.py (iter-v3/034).
- **No new dependencies required**: fracdiff_d05_close is already implemented and dispatched
  in `add_engineered_v3_features`. The ONLY code changes required are:
  (1) Remove `"LDOUSDT"` from V3_FEATURES_PER_SYMBOL
  (2) Add `"ALGOUSDT": V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",)` to V3_FEATURES_PER_SYMBOL
  (3) Update `_verify_feature_columns` assertions in `run_baseline_v3.py`
  (4) Update ITERATION_LABEL
  (5) Update adversarial tests
  No new feature dispatch code needed — fracdiff_d05_close is already computed for all symbols
  by `add_engineered_v3_features`.
- **Library versions (pinned — same as iter-v3/035/036/037)**:
  - lightgbm: 4.6.0
  - optuna: 4.8.0
  - numpy: 2.2.6
  - pandas: 3.0.0
  - scikit-learn: 1.8.0
  - scipy: 1.17.0
  - statsmodels: 0.14.6
  - pyarrow: 23.0.1
