# Iteration v3-037 — Research Brief

**Type**: EXPLORATION (cadence #9 of 10 in post-iter-v3/028 cycle; **FEATURE axis (per-symbol engineered feature swap) — revert TRX vol_adj_autocorr + add LDO-only cross_asset_divergence_norm**)
**Track**: v3 (rigor arm) — thirty-seventh iteration
**Branch**: `iteration-v3/037` (off `iter-v3/036` head)
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
TYPE: EXPLORATION (cadence #9 of 10 in post-iter-v3/028 cycle)
Wall-clock budget: <= 2h hard cap (per feedback_v3_cadence_discipline.md)
Single-axis variation: per-symbol engineered feature swap (V3_FEATURES_PER_SYMBOL)
  - REVERT V3_FEATURES_PER_SYMBOL["TRXUSDT"]: remove TRX entry (TRX reverts to 14-feature fallback)
  - ADD V3_FEATURES_PER_SYMBOL["LDOUSDT"] = V3_FEATURE_COLUMNS_TOP_N + ("cross_asset_divergence_norm",)
    (15 features for LDO only; 15 features for BCH via existing entry; 14 for TRX/ALGO via fallback)
  - V3_FEATURE_COLUMNS_TOP_N remains at 14 (no change to universal list)
  - BCHUSDT per-symbol entry UNCHANGED (V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",) = 15)
Cadence: 9 of 10 EXPLORATIONs in this cycle (next CONFIRMATION = iter-v3/039; 1 remaining)
Axis category: 2 (Category 2 engineered feature — per-symbol architecture swap)
ANCHOR: iter-v3/035 single-seed (IS -0.1023 / OOS +2.8521)
  NOTE: iter-v3/036 result is not yet available (NEGATIVE per brief context: "TRX vol_adj_autocorr
  hurt TRX (-15 swing)"); anchor remains iter-v3/035 as the most recent PROMISING baseline.
References:
  - iter-v3/027 cross_asset_divergence_norm (universal — NEGATIVE-SUSPICIOUS-OOS)
  - iter-v3/035 LDO feature importance (btc_ret_14d rank 6; lowest OOS contributor +3.98)
  - iter-v3/036 NEGATIVE outcome (TRX vol_adj_autocorr REVERTED)
  - feedback_v3_engineered_features_dont_stack.md (universal stacking constraint)
  - feedback_v3_axis_saturation_predictor.md (behavioral effect predictor requirement)
```

**Why revert TRX**: iter-v3/036 applied vol_adj_autocorr to TRX-only via V3_FEATURES_PER_SYMBOL.
The result was NEGATIVE: TRX OOS wpnl fell ~15 units relative to iter-v3/035 anchor. The
per-symbol isolation did not rescue the feature — TRX-specific vol_adj_autocorr is inert or
harmful at n_trials=35. The V3_FEATURES_PER_SYMBOL["TRXUSDT"] entry is reverted; TRX returns
to the 14-feature universal fallback (identical to iter-v3/035 TRX configuration).

**Why LDO-only cross_asset_divergence_norm**: LDO is the weakest OOS contributor at iter-v3/035
(+3.98 OOS wpnl, 14 trades, 35.0% WR — the only sub-50% WR symbol). LDO's feature importance
table (from iter-v3/035 `reports-v3/iteration_v3-035/in_sample/feature_importance.csv`) shows
`btc_ret_14d` at rank 6 in LDO's model — the strongest cross-asset feature engagement in the
portfolio. `cross_asset_divergence_norm = (sym_ret_7d - btc_ret_14d) / (|vwap_dev_20| + 1e-6)`
directly amplifies the btc_ret_14d signal by normalizing BTC-coupling divergence against LDO's
local mean-reversion intensity. The LDO-specific per-symbol architecture (V3_FEATURES_PER_SYMBOL)
provides the isolation needed to test LDO-specific cross_asset_divergence_norm without
contaminating BCH/TRX/ALGO.

**iter-v3/027 universal failure context**: cross_asset_divergence_norm applied universally to all
3 symbols (BCH+LDO+TRX at the time) produced NEGATIVE-SUSPICIOUS-OOS: IS Sharpe collapse -0.2817
+ OOS spike +1.6786 (3-iter monotonic IS degradation pattern). The per-symbol isolation tests
whether LDO specifically benefits when the feature is NOT applied universally — an architecturally
parallel test to iter-v3/035 (BCH-only fracdiff) which reversed a universal-failure (iter-v3/034)
into PROMISING (+2.85 OOS Sharpe).

**Single-axis justification**: this iteration makes ONE logical change to the per-symbol dispatch
architecture: swap TRXUSDT out of V3_FEATURES_PER_SYMBOL and LDOUSDT in (with a different feature).
BCH remains unchanged. The net result: V3_FEATURES_PER_SYMBOL has 2 entries (BCH+LDO) instead of
(BCH+TRX). Attribution is clean: any OOS delta vs iter-v3/035 anchor is explained by
(1) TRX returned to 14-feature fallback + (2) LDO-only cross_asset_divergence_norm.

---

## Section 1 — Hypothesis

`cross_asset_divergence_norm` applied selectively to LDOUSDT via
`V3_FEATURES_PER_SYMBOL["LDOUSDT"]` provides a LDO-specific BTC-coupling signal that amplifies
the already-high btc_ret_14d importance (rank 6 in LDO model at iter-v3/035) by normalizing
BTC-divergence against local mean-reversion intensity, yielding a net OOS Sharpe at or above
the iter-v3/035 anchor (+2.85) driven primarily by LDO OOS wpnl lift from +3.98 toward +10,
while BCH and TRX (reverted to 14-feature universal) maintain iter-v3/035 attribution levels.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — iter-v3/027 Universal Failure Evidence

The iter-v3/027 result at `reports-v3/iteration_v3-027/comparison.csv` provides the primary
evidence that universal cross_asset_divergence_norm fails:

| Metric | iter-v3/027 (universal) | iter-v3/025 anchor | Swing |
|--------|------------------------:|-------------------:|------:|
| IS monthly Sharpe | -0.2324 | +0.8788 | **-1.1112** |
| OOS monthly Sharpe | +1.6786 | +1.2244 | +0.4542 |
| IS/OOS daily ratio | ~5-7× | ~1× | SUSPICIOUS |

**Key observation**: The IS Sharpe collapse (-0.23 from +0.88) combined with OOS spike is the
canonical NEGATIVE-SUSPICIOUS-OOS signature. This is NOT evidence that cross_asset_divergence_norm
has no LDO-specific signal; it is evidence that universal application across BCH+LDO+TRX creates
cross-symbol interference. The per-symbol test (LDO-only) isolates whether LDO benefits without
cross-symbol contamination.

**Parallel to BCH fracdiff architecture**: iter-v3/034 applied fracdiff_d05_close universally and
produced IS Sharpe -0.1636 (worst post-bootstrap) with TRX -20.11 / ALGO -8.24 / LDO -6.81
regressions. iter-v3/035 applied fracdiff_d05_close BCH-only and produced OOS Sharpe +2.85
(PROMISING). The per-symbol architecture resolved a universal failure into a per-symbol signal.
The identical architecture is applied here for LDO-only cross_asset_divergence_norm.

### 2.2 — iter-v3/035 LDO Attribution and btc_ret_14d Evidence

The iter-v3/035 per-symbol OOS data at `reports-v3/iteration_v3-035/out_of_sample/per_symbol.csv`:

| Symbol | v3-035 OOS wpnl | v3-035 OOS n_trades | v3-035 OOS WR |
|--------|----------------:|--------------------:|--------------:|
| BCH    | +48.7337        | 32                  | 50.0%         |
| TRX    | +29.2441        | 46                  | 52.2%         |
| ALGO   | +20.8740        | 25                  | 40.0%         |
| LDO    | +3.9751         | 20                  | 35.0%         |

LDO is the only sub-50% WR symbol and the weakest OOS contributor by a factor of ~5× vs BCH.
Its 35.0% WR indicates the LDO model is taking directional risk without comparable signal quality.
Feature importance for LDO (from `reports-v3/iteration_v3-035/in_sample/feature_importance.csv`):
`btc_ret_14d` appears at rank 6 in LDO's model — the highest relative BTC cross-asset engagement
among the 4 symbols. `cross_asset_divergence_norm` directly constructs a BTC-coupling composite
from btc_ret_14d + sym_ret_7d + vwap_dev_20, where the LDO btc_ret_14d importance suggests the
BTC-coupling signal is already partially informative for LDO. Normalizing by vwap_dev_20 provides
the conditional signal that raw btc_ret_14d cannot capture.

### 2.3 — Per-Symbol Architecture Precedent (iter-v3/035)

iter-v3/035 established that `V3_FEATURES_PER_SYMBOL` architecture resolves universal failures
into per-symbol lift: BCH-only fracdiff produced OOS Sharpe +2.85 (PROMISING) after universal
fracdiff failed at IS Sharpe -0.1636. This provides the precedent and infrastructure for
LDO-only cross_asset_divergence_norm.

### 2.4 — IS Sharpe Prediction Basis

The combined change (revert TRX + add LDO per-symbol) predicts:
- BCH model: IDENTICAL to iter-v3/035 (no feature change) → BCH IS contribution unchanged
- TRX model: IDENTICAL to iter-v3/035 (reverted from iter-v3/036 TRX entry) → TRX IS contribution restored
- LDO model: receives one additional feature (cross_asset_divergence_norm) → small IS perturbation
- ALGO model: IDENTICAL to iter-v3/035 (no feature change) → ALGO IS contribution unchanged

Net IS Sharpe delta vs iter-v3/035 anchor (-0.1023): dominated by LDO model change only. Expected
small perturbation, with IS Sharpe near iter-v3/035 anchor.

**Behavioral effect predictor** (per `feedback_v3_axis_saturation_predictor.md`): the per-symbol
architecture change affects ONLY LDO's LightGBM model (15 features instead of 14). BCH/TRX/ALGO
models are IDENTICAL to iter-v3/035. Expected IS trade count delta: LDO model trades may shift
±5-20% due to cross_asset_divergence_norm signal; BCH/TRX/ALGO trades IDENTICAL to iter-v3/035.
Net IS trade change: small (< 20% total portfolio). Falsifier: if observed IS trade count change
is 0 trades for LDO (bit-identical to iter-v3/035), the cross_asset_divergence_norm feature is
INERT for LDO.

---

## Section 3 — Proposed Changes

### Sub-fix 1: UPDATE V3_FEATURES_PER_SYMBOL in `src/crypto_trade/features_v3/__init__.py`

Remove TRXUSDT entry; add LDOUSDT entry with cross_asset_divergence_norm:

```python
V3_FEATURES_PER_SYMBOL: dict[str, tuple[str, ...]] = {
    "BCHUSDT": V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",),
    "LDOUSDT": V3_FEATURE_COLUMNS_TOP_N + ("cross_asset_divergence_norm",),
}
# TRXUSDT removed (reverts to 14-feature universal fallback)
```

BCH unchanged at 15 features (14 universal + fracdiff_d05_close).
LDO gets 15 features (14 universal + cross_asset_divergence_norm).
TRX returns to 14-feature fallback (no per-symbol entry — iter-v3/036 reverted).
ALGO remains at 14-feature fallback.
BCH and LDO extension features are DISJOINT:
  BCH: fracdiff_d05_close (NOT cross_asset_divergence_norm)
  LDO: cross_asset_divergence_norm (NOT fracdiff_d05_close)

### Sub-fix 2: UPDATE dispatch in `add_engineered_v3_features`

In `src/crypto_trade/features_v3/engineered_v3.py`, replace the vol_adj_autocorr dispatch
with cross_asset_divergence_norm dispatch:

```python
def add_engineered_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    df = compute_regime_momentum_signed_5d(df)  # iter-v3/025 (KEPT)
    df = compute_fracdiff_d05_close(df)          # iter-v3/034 (KEPT; BCH-only at model level)
    df = compute_cross_asset_divergence_norm(df) # iter-v3/037 (LDO-only at model level)
    # compute_vol_adj_autocorr DROPPED (iter-v3/036 NEGATIVE; reverted at iter-v3/037)
    return df
```

This adds `cross_asset_divergence_norm` to ALL symbol parquets (same pattern as fracdiff_d05_close:
generated for all symbols, used only by LDO's explicit `feature_columns=` list at model-train time).
`vol_adj_autocorr` is dropped from dispatch (reverted to dead-code status as before iter-v3/036).

### Sub-fix 3: Update `_verify_feature_columns` in `run_baseline_v3.py`

Assertions that must PASS after this change (iter-v3/037 state):

- `len(V3_FEATURE_COLUMNS_TOP_N) == 14` (universal fallback is 14 features — UNCHANGED)
- `"fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N` (NOT in universal list — UNCHANGED)
- `"cross_asset_divergence_norm" not in V3_FEATURE_COLUMNS_TOP_N` (NOT in universal list — UNCHANGED)
- `"vol_adj_autocorr" not in V3_FEATURE_COLUMNS_TOP_N` (NOT in universal list — UNCHANGED)
- `"BCHUSDT" in V3_FEATURES_PER_SYMBOL` (BCH still has per-symbol entry — UNCHANGED)
- `len(V3_FEATURES_PER_SYMBOL["BCHUSDT"]) == 15` (BCH gets 15 features — UNCHANGED)
- `"fracdiff_d05_close" in V3_FEATURES_PER_SYMBOL["BCHUSDT"]` (fracdiff in BCH — UNCHANGED)
- `"LDOUSDT" in V3_FEATURES_PER_SYMBOL` (LDO now has per-symbol entry — NEW)
- `len(V3_FEATURES_PER_SYMBOL["LDOUSDT"]) == 15` (LDO gets 15 features — NEW)
- `"cross_asset_divergence_norm" in V3_FEATURES_PER_SYMBOL["LDOUSDT"]` (cross_asset in LDO — NEW)
- `"fracdiff_d05_close" not in V3_FEATURES_PER_SYMBOL["LDOUSDT"]` (NOT in LDO — NEW)
- `"TRXUSDT" not in V3_FEATURES_PER_SYMBOL` (TRX removed — NEW constraint)
- `features_for_symbol("TRXUSDT") len == 14` (TRX fallback = 14 features — REVERTED)
- `features_for_symbol("ALGOUSDT") len == 14` (ALGO fallback = 14 features — UNCHANGED)
- `"cross_asset_divergence_norm" not in features_for_symbol("TRXUSDT")` (TRX no cross_asset — NEW)
- `"cross_asset_divergence_norm" not in features_for_symbol("ALGOUSDT")` (ALGO no cross_asset — NEW)
- `"regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N` (portfolio mandate — UNCHANGED)
- `len(V3_FEATURES_PER_SYMBOL) == 2` (BCH + LDO entries — NEW count check)

### Sub-fix 4: Update ITERATION_LABEL "v3-036" → "v3-037"

In `run_baseline_v3.py`:
```python
ITERATION_LABEL = "v3-037"
```

### Sub-fix 5: Adversarial tests in `tests/features_v3/test_features_for_symbol.py`

Update the test suite to reflect iter-v3/037 state (V3_FEATURES_PER_SYMBOL has BCH+LDO entries):

- `test_bch_has_fracdiff`: UNCHANGED (BCH still 15 features with fracdiff_d05_close)
- `test_bch_no_cross_asset_divergence`: BCH must NOT include cross_asset_divergence_norm — NEW
- `test_ldo_has_cross_asset_divergence`: LDO returns 15 features WITH cross_asset_divergence_norm — NEW
- `test_ldo_no_fracdiff`: LDO must NOT include fracdiff_d05_close — UPDATED
- `test_trx_fallback_14`: TRX returns 14 features via fallback (no per-symbol entry) — UPDATED
- `test_trx_no_cross_asset_divergence`: TRX must NOT include cross_asset_divergence_norm — NEW
- `test_algo_fallback_14`: ALGO returns 14 features (unchanged) — UNCHANGED assertion
- `test_bch_ldo_per_symbol_entries_are_different`: BCH has fracdiff, LDO has cross_asset — NEW
- `test_trxusdt_not_in_per_symbol`: TRXUSDT must NOT be in V3_FEATURES_PER_SYMBOL — NEW
- `test_ldo_per_symbol_len`: len(V3_FEATURES_PER_SYMBOL["LDOUSDT"]) == 15 — NEW
- `test_v3_features_per_symbol_has_two_entries`: BCH + LDO (not BCH + TRX) — UPDATED
- `test_regime_momentum_in_universal_list`: UNCHANGED
- `test_fracdiff_not_in_universal_list`: UNCHANGED
- `test_cross_asset_divergence_not_in_universal_list`: cross_asset_divergence_norm NOT in TOP_N — NEW
- `test_vol_adj_autocorr_not_in_universal_list`: UNCHANGED (vol_adj still absent)
- `test_universal_list_is_14`: UNCHANGED

---

## Section 4 — Expected OOS Impact

**ANCHOR**: iter-v3/035 single-seed IS -0.1023 / OOS +2.8521

**IS Sharpe prediction (vs iter-v3/035 anchor -0.1023)**:
- Predicted band: [-0.20, +0.10]
- Median point estimate: 0.0
- Rationale: BCH/TRX/ALGO models IDENTICAL to iter-v3/035 (no feature change for these three).
  LDO model receives one additional feature. Net IS Sharpe effect: small perturbation dominated by
  LDO's low trade count (14 OOS trades → low IS weight). TRX revert from iter-v3/036 restores TRX
  IS contribution to iter-v3/035 levels.

**OOS Sharpe prediction (vs iter-v3/035 anchor +2.85)**:
- Predicted band: [+2.50, +3.20]
- Median point estimate: +2.85
- Rationale: if LDO's cross_asset_divergence_norm captures the BTC-coupling signal (amplifying
  btc_ret_14d rank-6 importance), LDO OOS wpnl may lift from +3.98 toward +10, adding ~+0.2-0.4
  OOS Sharpe to the portfolio. BCH+TRX (reverted to iter-v3/035 config) are expected to maintain
  iter-v3/035 attribution (+48.73 BCH / +29.24 TRX). The upper band reflects LDO meaningful lift;
  lower band reflects near-null effect.

**Path taxonomy**:
- Path A (PROMISING): cross_asset_divergence_norm importance ≥ 30 in LDO model AND IS Sharpe
  above iter-v3/035 anchor (-0.10) AND OOS Sharpe ≥ anchor + any positive delta AND LDO OOS
  wpnl lifts from +3.98
- Path B (PROMISING-INERT): cross_asset_divergence_norm learned but low importance (5-29 in LDO
  model). Budget-disambiguation retest at n_trials=70 may be warranted per precedent.
- Path C (NULL-RESULT — saturated axis for LDO): cross_asset_divergence_norm importance < 5 in
  LDO model AND IS trade count change for LDO = 0. Per `feedback_v3_axis_saturation_predictor.md`:
  axis saturated for LDO; NEXT EXPLORATION must move to different axis.
- Path D (NEGATIVE): OOS Sharpe < +2.0 OR IS Sharpe regression > 0.20 below iter-v3/035 anchor.

**OOS falsifier**: if OOS Sharpe < +2.0 (more than 0.85 below anchor), the LDO-only
cross_asset_divergence_norm hypothesis is rejected.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.

**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward from baseline.

**R3 (OOD detection)**: unchanged. Mahalanobis OOD z-score threshold unchanged.

**Per-symbol feature heterogeneity risk**: BCH's LightGBM model trains on 15 features
(14 + fracdiff_d05_close), LDO trains on 15 features (14 + cross_asset_divergence_norm), while
TRX/ALGO train on 14. This is architecturally safe: `features_for_symbol()` dispatches distinct
feature lists; `LightGbmStrategy` receives explicit `feature_columns=` per call.
The CPCV CV splits are computed per-cell (per symbol); each symbol's splits use its own
parquet. No cross-symbol contamination.

**cross_asset_divergence_norm generated for ALL symbols**: `add_engineered_v3_features` dispatch
generates `cross_asset_divergence_norm` for ALL symbols but only LDO's explicit `feature_columns`
list includes it. TRX/ALGO/BCH parquets contain the column but it is NOT passed to LightGBM for
those symbols. Safe by design.

**TRX revert risk**: TRX returns to 14-feature universal fallback (iter-v3/035 configuration).
This is a regression from iter-v3/036 but restoration to the known-good iter-v3/035 anchor. No
new TRX-specific risk introduced.

**BCH and LDO per-symbol entries are DISJOINT in their extension features**: BCH adds
fracdiff_d05_close; LDO adds cross_asset_divergence_norm. These two features are architecturally
independent. No risk of cross-feature contamination.

---

## Section 6 — Risk Management Design (7-Primitive Gate Table)

All 7 risk gates carried forward from iter-v3/035 baseline unchanged. No gate parameters
are modified in this iteration.

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

**Most plausible failure mode**: cross_asset_divergence_norm has no LDO-specific signal — the
iter-v3/027 universal failure was NOT a cross-symbol contamination artifact for LDO specifically.
LDO's btc_ret_14d rank-6 importance reflects a feature that is already captured in the 14-feature
universal model; cross_asset_divergence_norm is merely a function of btc_ret_14d, so it cannot
add information beyond what btc_ret_14d alone provides. Classification: NULL-RESULT (axis
saturated for LDO at n_trials=35) or PROMISING-INERT (importance 5-29 range).

**Second plausible failure mode**: cross_asset_divergence_norm has moderate LDO importance
(15-29, PROMISING-INERT range) but OOS Sharpe falls below +2.50 anchor lower band. This would
indicate that LDO's cross_asset_divergence_norm IS signal IS learned but produces IS exploitation
without OOS generalization — consistent with LDO's historically low OOS WR (35.0% at iter-v3/035)
suggesting the LDO model operates in a more fragile regime where additional features add noise.

**What the gates should catch**: any IS collapse in LDO model's per-cell Sharpe (watch for LDO IS
wpnl < iter-v3/035 LDO IS value), or any absurd IS/OOS Sharpe ratio on LDO-specific per-symbol
metrics. If LDO OOS concentration rises abnormally (from iter-v3/035 baseline ~38%), that is the
stacking alarm.

**Behavioral effect predictor**: Expected LDO IS trade count delta = ±5-20% (one additional
feature changes trade signals). BCH/TRX/ALGO = IDENTICAL to iter-v3/035 (zero delta).
Falsifier: if LDO IS trade count change = 0 trades, cross_asset_divergence_norm is INERT for LDO.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (EXPLORATION)

This is an EXPLORATION iteration. MERGE criteria are not applicable — only PROMISING /
NEGATIVE / NULL-RESULT classification applies.

**PROMISING** (proceed toward CONFIRMATION cadence): ALL of:
- cross_asset_divergence_norm feature importance ≥ 30 in LDO model (Category 2 carve-out gate)
- LDO IS trade count change ≠ 0 vs iter-v3/035 anchor (confirms feature is non-inert)
- BCH/TRX/ALGO models show 0 change in IS trade count vs iter-v3/035 anchor (no contamination)
- OOS Sharpe ≥ +2.50 (lower band of predicted range)

**PROMISING-INERT** (cross_asset learned but low importance):
- cross_asset_divergence_norm importance in [5, 29] in LDO model AND IS trade count for LDO ≠ 0.
  Budget-disambiguation retest at n_trials=70 may be warranted.

**NULL-RESULT (saturated axis for LDO)**:
- cross_asset_divergence_norm importance < 5 in LDO model AND IS trade count change for LDO = 0.
  Per `feedback_v3_axis_saturation_predictor.md`: axis saturated for LDO; NEXT EXPLORATION
  must move to different axis.

**NEGATIVE**: ANY of:
- OOS Sharpe < +2.0 (OOS falsifier — more than 0.85 below anchor)
- IS Sharpe regression > 0.20 below iter-v3/035 anchor (-0.30 or worse)
- BCH/TRX/ALGO IS trade counts change by > 5 trades vs iter-v3/035 (contamination signal)
- LDO OOS concentration rises > 70% (single-symbol lottery alarm)

---

## Section 9 — Library Stack Declaration

- **Python**: 3.13 (runtime)
- **LightGBM**: pinned in pyproject.toml (same as iter-v3/035/036; no change)
- **numpy**: standard array operations for cross_asset_divergence_norm computation (already in use)
- **fracdiff (PyPI package)**: UNAVAILABLE (same constraint as prior iterations: fracdiff==0.9.0
  requires statsmodels<0.14; project requires statsmodels==0.14.6). Not needed —
  cross_asset_divergence_norm uses no fracdiff library.
- **No new dependencies required**: cross_asset_divergence_norm is fully implemented in
  `src/crypto_trade/features_v3/engineered_v3.py` from iter-v3/027 (retained as dead code since
  iter-v3/028). `compute_cross_asset_divergence_norm` exists as dead code; re-adding the dispatch
  to `add_engineered_v3_features` and swapping V3_FEATURES_PER_SYMBOL entries are the ONLY code
  changes required.
- **Library versions (pinned — same as iter-v3/035/036)**:
  - lightgbm: 4.6.0
  - optuna: 4.8.0
  - numpy: 2.2.6
  - pandas: 3.0.0
  - scikit-learn: 1.8.0
  - scipy: 1.17.0
  - statsmodels: 0.14.6
  - pyarrow: 23.0.1
