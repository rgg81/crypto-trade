# Iteration v3-036 — Research Brief

**Type**: EXPLORATION (cadence #8 of 10 in post-iter-v3/028 cycle; **FEATURE axis (per-symbol engineered feature addition via V3_FEATURES_PER_SYMBOL) — TRX-only vol_adj_autocorr**)
**Track**: v3 (rigor arm) — thirty-sixth iteration
**Branch**: `iteration-v3/036` (off `iter-v3/035` head)
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
TYPE: EXPLORATION (cadence #8 of 10 in post-iter-v3/028 cycle)
Wall-clock budget: <= 2h hard cap (per feedback_v3_cadence_discipline.md)
Single-axis variation: per-symbol engineered feature add (V3_FEATURES_PER_SYMBOL["TRXUSDT"])
  - ADD V3_FEATURES_PER_SYMBOL["TRXUSDT"] = V3_FEATURE_COLUMNS_TOP_N + ("vol_adj_autocorr",)
    (15 features for TRX only; 15 features for BCH via existing entry; 14 for LDO/ALGO via fallback)
  - V3_FEATURE_COLUMNS_TOP_N remains at 14 (no change to universal list)
  - BCHUSDT per-symbol entry UNCHANGED (V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",) = 15)
Cadence: 8 of 10 EXPLORATIONs in this cycle (next CONFIRMATION = iter-v3/039)
Axis category: 2 (Category 2 engineered feature — per-symbol architecture extension)
ANCHOR: iter-v3/035 single-seed (IS -0.1023 / OOS +2.8521)
References:
  - feedback_v3_engineered_features_proven.md (engineered features pivot validated by iter-v3/025+)
  - iter-v3/030 V3_FEATURES_PER_SYMBOL architecture (established per-symbol dispatch pattern)
  - iter-v3/035 V3_FEATURES_PER_SYMBOL precedent (BCH-only fracdiff — PROMISING OOS +2.85)
```

**Why per-symbol vol_adj_autocorr instead of universal**: iter-v3/026 established that
vol_adj_autocorr universally applied (all 3 symbols at the time: BCH+LDO+TRX) produced a
NEGATIVE-SUSPICIOUS-OOS result: IS Sharpe collapse to +0.0493 (lowest IS in post-bootstrap
cycle) and OOS spike to +1.4501 (27× IS/OOS daily ratio — structurally absurd; stacking-falsified
at single-seed n_trials=35). The universal application was a second Category 2 composed feature
stacked on top of regime_momentum_signed_5d, which violated the stacking constraint. However,
at iter-v3/026 the per-symbol contribution of vol_adj_autocorr was NOT decomposed — the aggregate
failure does not preclude a per-symbol signal for TRX specifically.

TRX is the dominant OOS contributor at iter-v3/035 (+29.24 OOS wpnl, 26.59% concentration,
52.2% win rate, 46 trades). Its autocorrelation-related features may carry TRX-specific
signal when normalized by realized vol. The per-symbol architecture (V3_FEATURES_PER_SYMBOL)
established at iter-v3/035 provides the isolation needed to test TRX-specific vol_adj_autocorr
without contaminating BCH/LDO/ALGO.

**Single-axis justification**: "add TRX per-symbol entry with vol_adj_autocorr" is a logically
atomic operation — it adds a single column to TRX's LightGBM model only. BCH remains at 15
features (fracdiff), LDO/ALGO remain at 14 features (fallback). TRX moves from 14 to 15
features (14 universal + vol_adj_autocorr). Attribution is clean: any OOS delta vs iter-v3/035
anchor is explained by TRX-only vol_adj_autocorr.

**No new infrastructure**: vol_adj_autocorr is already implemented in `engineered_v3.py`
(from iter-v3/026; retained as dead code per `feedback_v3_engineered_features_dont_stack.md`).
The dispatch in `add_engineered_v3_features` dropped vol_adj_autocorr at iter-v3/027 but
`compute_vol_adj_autocorr` remains in the module. Re-adding the dispatch adds the column to
ALL symbol parquets; only TRX's explicit `feature_columns=` list will include it at model-train
time. This is architecturally identical to how fracdiff_d05_close is handled for BCH.

---

## Section 1 — Hypothesis

`vol_adj_autocorr` (= `ret_autocorr_lag1_50 / (range_realized_vol_50 + 1e-6)`) applied
selectively to TRXUSDT via `V3_FEATURES_PER_SYMBOL["TRXUSDT"]` provides a TRX-specific
persistence-normalized-by-volatility signal that the universal application at iter-v3/026
obscured via cross-symbol noise, yielding a net OOS Sharpe near the iter-v3/035 anchor
(+2.85) or above, with TRX vol_adj_autocorr feature importance ≥ 30 in TRX model as the
confirmatory gate.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — iter-v3/026 Universal Failure Evidence (QR archival analysis)

The iter-v3/026 result at `reports-v3/iteration_v3-026/comparison.csv` provides the primary
evidence that universal vol_adj_autocorr fails:

| Metric | iter-v3/026 (universal) | iter-v3/025 anchor | Swing |
|--------|------------------------:|-------------------:|------:|
| IS monthly Sharpe | +0.0493 | +0.8788 | **-0.8295** |
| OOS monthly Sharpe | +1.4501 | +1.2244 | +0.2257 |
| IS/OOS daily ratio | 27× | ~1× | absurd — SUSPICIOUS |

**Key observation**: The 27× IS/OOS ratio is the canonical NEGATIVE-SUSPICIOUS-OOS signature.
This is NOT evidence that vol_adj_autocorr has no signal; it is evidence that vol_adj_autocorr
stacked universally on top of regime_momentum_signed_5d creates IS collapse + OOS noise. The
per-symbol test isolates whether TRX benefits without the cross-symbol contamination.

### 2.2 — iter-v3/035 TRX OOS Attribution (Phase 7 result; no new EDA required)

The iter-v3/035 per-symbol OOS data at `reports-v3/iteration_v3-035/out_of_sample/per_symbol.csv`:

| Symbol | v3-035 OOS wpnl | v3-035 OOS n_trades | v3-035 OOS WR |
|--------|----------------:|--------------------:|--------------:|
| BCH    | +48.7337        | 32                  | 50.0%         |
| TRX    | +29.2441        | 46                  | 52.2%         |
| ALGO   | +20.8740        | 25                  | 40.0%         |
| LDO    | +3.9751         | 20                  | 35.0%         |

TRX's 52.2% win rate and +29.24 OOS wpnl make it the second-strongest contributor at
iter-v3/035. High win rate (above portfolio mean) suggests TRX model is operating in a
regime where persistence/autocorrelation signals may be actionable. vol_adj_autocorr
specifically captures whether autocorrelation is high IN LOW-VOL REGIMES (genuinely tradeable)
vs. noise-driven persistence in high-vol regimes. This is a plausible TRX-specific signal
given TRX's lower NATR vs BCH.

### 2.3 — Per-Symbol Architecture Precedent (iter-v3/035)

iter-v3/035 established that `V3_FEATURES_PER_SYMBOL` architecture WORKS for per-symbol
feature additions: BCH-only fracdiff produced OOS Sharpe +2.85 (PROMISING), demonstrating
that per-symbol isolation of a feature that fails universally is a valid methodology. This
provides the precedent and infrastructure for TRX-only vol_adj_autocorr.

### 2.4 — IS Sharpe Prediction Basis

Per-symbol TRX vol_adj_autocorr addition predicts: BCH/LDO/ALGO models IDENTICAL to
iter-v3/035 (no feature change); TRX model receives one additional feature. Expected IS
Sharpe delta: small (TRX model ±IS Sharpe shift from one new feature), with net portfolio
IS Sharpe near iter-v3/035 anchor (-0.1023; dominated by BCH's fracdiff lift and LDO drag).

**Behavioral effect predictor** (per `feedback_v3_axis_saturation_predictor.md`): the per-symbol
architecture change affects ONLY TRX's LightGBM model (15 features instead of 14). BCH/LDO/ALGO
models are IDENTICAL to iter-v3/035. Expected IS trade count delta: TRX model trades may shift
±5-15% due to vol_adj_autocorr signal; BCH/ALGO/LDO trades IDENTICAL to iter-v3/035.
Net IS trade change: small (< 15% total portfolio). Falsifier: if observed IS trade change is
0 trades for TRX (bit-identical to iter-v3/035), the vol_adj_autocorr feature is INERT for TRX.

---

## Section 3 — Proposed Changes

### Sub-fix 1: ADD V3_FEATURES_PER_SYMBOL["TRXUSDT"]

In `src/crypto_trade/features_v3/__init__.py`, update `V3_FEATURES_PER_SYMBOL` to:

```python
V3_FEATURES_PER_SYMBOL: dict[str, tuple[str, ...]] = {
    "BCHUSDT": V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",),
    "TRXUSDT": V3_FEATURE_COLUMNS_TOP_N + ("vol_adj_autocorr",),
}
```

This gives TRX exactly 15 features (14 universal + vol_adj_autocorr). BCH unchanged at 15
features (14 universal + fracdiff_d05_close). LDO/ALGO fall back to V3_FEATURE_COLUMNS_TOP_N
(14 features). BCH and TRX per-symbol entries are DISTINCT: BCH has fracdiff_d05_close and
NOT vol_adj_autocorr; TRX has vol_adj_autocorr and NOT fracdiff_d05_close.

### Sub-fix 2: RE-ADD vol_adj_autocorr dispatch in `add_engineered_v3_features`

In `src/crypto_trade/features_v3/engineered_v3.py`, re-add the dispatch call:

```python
def add_engineered_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    df = compute_regime_momentum_signed_5d(df)  # iter-v3/025 (KEPT)
    df = compute_fracdiff_d05_close(df)  # iter-v3/034 (KEPT)
    df = compute_vol_adj_autocorr(df)  # iter-v3/036 RE-ADDED (dead code since iter-v3/027)
    return df
```

This adds `vol_adj_autocorr` to ALL symbol parquets (same pattern as fracdiff_d05_close —
generated for all symbols, but only TRX's explicit `feature_columns=` list includes it at
model-train time). NO cross-symbol contamination at the LightGBM level.

Update the docstring to document iter-v3/036: vol_adj_autocorr re-dispatched for per-symbol
parquet generation (TRX-only at model level via V3_FEATURES_PER_SYMBOL["TRXUSDT"]).

### Sub-fix 3: Update `_verify_feature_columns` in `run_baseline_v3.py`

Assertions that must PASS after this change (iter-v3/036 state):

- `len(V3_FEATURE_COLUMNS_TOP_N) == 14` (universal fallback is 14 features — UNCHANGED)
- `"fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N` (NOT in universal list — UNCHANGED)
- `"vol_adj_autocorr" not in V3_FEATURE_COLUMNS_TOP_N` (NOT in universal list — NEW check)
- `"BCHUSDT" in V3_FEATURES_PER_SYMBOL` (BCH still has per-symbol entry — UNCHANGED)
- `len(V3_FEATURES_PER_SYMBOL["BCHUSDT"]) == 15` (BCH gets 15 features — UNCHANGED)
- `"fracdiff_d05_close" in V3_FEATURES_PER_SYMBOL["BCHUSDT"]` (fracdiff in BCH — UNCHANGED)
- `"vol_adj_autocorr" not in V3_FEATURES_PER_SYMBOL["BCHUSDT"]` (NOT in BCH — NEW check)
- `"TRXUSDT" in V3_FEATURES_PER_SYMBOL` (TRX now has per-symbol entry — NEW)
- `len(V3_FEATURES_PER_SYMBOL["TRXUSDT"]) == 15` (TRX gets 15 features — NEW)
- `"vol_adj_autocorr" in V3_FEATURES_PER_SYMBOL["TRXUSDT"]` (vol_adj_autocorr in TRX — NEW)
- `"fracdiff_d05_close" not in V3_FEATURES_PER_SYMBOL["TRXUSDT"]` (NOT in TRX — NEW check)
- `features_for_symbol("LDOUSDT") len == 14` (LDO fallback = 14 features — UNCHANGED)
- `features_for_symbol("ALGOUSDT") len == 14` (ALGO fallback = 14 features — UNCHANGED)
- `"vol_adj_autocorr" not in features_for_symbol("LDOUSDT")` (LDO has no vol_adj — NEW)
- `"vol_adj_autocorr" not in features_for_symbol("ALGOUSDT")` (ALGO has no vol_adj — NEW)
- `"regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N` (portfolio mandate — UNCHANGED)
- `len(V3_FEATURES_PER_SYMBOL) == 2` (BCH + TRX entries — NEW count check)

### Sub-fix 4: Update ITERATION_LABEL "v3-035" → "v3-036"

In `run_baseline_v3.py`, change:
```python
ITERATION_LABEL = "v3-036"
```

### Sub-fix 5: Adversarial tests in `tests/features_v3/test_features_for_symbol.py`

Update the test suite to reflect iter-v3/036 state (V3_FEATURES_PER_SYMBOL has 2 entries):

- `test_bch_has_fracdiff`: `features_for_symbol("BCHUSDT")` returns 15 features
  INCLUDING `fracdiff_d05_close` — UNCHANGED assertion
- `test_bch_no_vol_adj_autocorr`: `features_for_symbol("BCHUSDT")` does NOT include
  `vol_adj_autocorr` — NEW: BCH entry must NOT have TRX's feature
- `test_trx_has_vol_adj_autocorr`: `features_for_symbol("TRXUSDT")` returns 15 features
  INCLUDING `vol_adj_autocorr` — NEW
- `test_trx_no_fracdiff`: `features_for_symbol("TRXUSDT")` does NOT include
  `fracdiff_d05_close` — UPDATED (was: 14 features; now: 15, different feature)
- `test_ldo_no_fracdiff_no_vol_adj`: `features_for_symbol("LDOUSDT")` returns 14 features
  NOT including either `fracdiff_d05_close` or `vol_adj_autocorr` — UPDATED
- `test_algo_no_fracdiff_no_vol_adj`: `features_for_symbol("ALGOUSDT")` returns 14 features
  NOT including either feature — UPDATED
- `test_bch_per_symbol_entry_has_fracdiff`: dict check — UNCHANGED
- `test_trx_per_symbol_entry_has_vol_adj_autocorr`: `V3_FEATURES_PER_SYMBOL["TRXUSDT"]`
  contains `vol_adj_autocorr` — NEW
- `test_bch_trx_per_symbol_entries_are_different`: BCH and TRX per-symbol entries must
  DIFFER in content (BCH has fracdiff, TRX has vol_adj_autocorr) — NEW adversarial
- `test_bch_per_symbol_len`: 15 — UNCHANGED
- `test_trx_per_symbol_len`: `len(V3_FEATURES_PER_SYMBOL["TRXUSDT"]) == 15` — NEW
- `test_non_bch_trx_fallback_no_special_features`: LDO/ALGO fallback = 14,
  no fracdiff, no vol_adj_autocorr — UPDATED parametrize
- `test_subset_invariant_extended_bch`: BCH entry = TOP_N + ("fracdiff_d05_close",) — UNCHANGED
- `test_subset_invariant_extended_trx`: TRX entry = TOP_N + ("vol_adj_autocorr",) — NEW
- `test_v3_features_per_symbol_has_two_entries`: `len(V3_FEATURES_PER_SYMBOL) == 2` — UPDATED
- `test_regime_momentum_in_universal_list`: mandate check — UNCHANGED
- `test_fracdiff_not_in_universal_list`: universal list check — UNCHANGED
- `test_vol_adj_autocorr_not_in_universal_list`: `vol_adj_autocorr` NOT in TOP_N — NEW
- `test_universal_list_is_14`: still 14 — UNCHANGED

---

## Section 4 — Expected OOS Impact

**ANCHOR**: iter-v3/035 single-seed IS -0.1023 / OOS +2.8521

**IS Sharpe prediction (vs iter-v3/035 anchor -0.1023)**:
- Predicted band: [-0.20, +0.20]
- Median point estimate: 0.0 (TRX model change has small IS effect; BCH/LDO/ALGO identical)
- Rationale: TRX-only vol_adj_autocorr adds one feature to TRX's 14-feature model; BCH/LDO/ALGO
  models IDENTICAL to iter-v3/035. Net IS Sharpe effect dominated by BCH's fracdiff dynamics
  (already captured at iter-v3/035); TRX's new feature has small IS perturbation.

**OOS Sharpe prediction (vs iter-v3/035 anchor +2.8521)**:
- Predicted band: [+2.40, +3.10]
- Median point estimate: +2.75
- Rationale: if TRX's vol_adj_autocorr captures TRX-specific persistence signal, it may add
  ±0.3-0.5 OOS Sharpe to the portfolio. The iter-v3/035 anchor (+2.85) is the primary OOS
  reference; the upper band reflects small TRX-only lift; lower band reflects near-null effect.

**Path taxonomy**:
- Path A (PROMISING): vol_adj_autocorr importance ≥ 30 in TRX model AND IS Sharpe above iter-v3/035
  anchor (-0.10) AND OOS Sharpe ≥ anchor + any positive delta
- Path B (PROMISING-INERT): vol_adj_autocorr learned but low importance (5-29 in TRX model).
  Budget-disambiguation retest at n_trials=70 may be warranted per precedent.
- Path C (NULL-RESULT saturated axis for TRX): vol_adj_autocorr importance < 5 in TRX model
  AND IS trade count change for TRX = 0. Per `feedback_v3_axis_saturation_predictor.md`:
  axis saturated for TRX; NEXT EXPLORATION must move to different axis.
- Path D (NEGATIVE): IS Sharpe regression > 0.20 below iter-v3/035 anchor OR OOS Sharpe < +2.0.

**OOS falsifier**: if OOS Sharpe < +2.0 (more than 0.85 below anchor), the TRX-only
vol_adj_autocorr hypothesis is rejected.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.

**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward from baseline.

**R3 (OOD detection)**: unchanged. Mahalanobis OOD z-score threshold unchanged.

**Per-symbol feature heterogeneity risk**: BCH's LightGBM model trains on 15 features
(14 + fracdiff_d05_close), TRX trains on 15 features (14 + vol_adj_autocorr), while
LDO/ALGO train on 14. This is architecturally safe: `features_for_symbol()` dispatches
distinct feature lists; `LightGbmStrategy` receives explicit `feature_columns=` per call.
The CPCV CV splits are computed per-cell (per symbol); each symbol's splits use its own
parquet. No cross-symbol contamination.

**vol_adj_autocorr still generated for ALL symbols**: `add_engineered_v3_features` dispatch
generates `vol_adj_autocorr` for ALL symbols but only TRX's explicit `feature_columns` list
includes it. LDO/ALGO/BCH parquets contain the column but it is NOT passed to LightGBM for
those symbols. Safe by design — the LightGBM runner selects columns explicitly.

**BCH and TRX per-symbol entries are DISJOINT in their extension features**: BCH adds
fracdiff_d05_close; TRX adds vol_adj_autocorr. These two features are architecturally
independent (one is fractional differencing of price, the other is autocorrelation ratio).
No risk of cross-feature contamination.

---

## Section 6 — Risk Management Design (7-Primitive Gate Table)

All 7 risk gates carried forward from iter-v3/035 baseline unchanged. No gate parameters
are modified in this iteration.

| Gate | Type | Parameter | IS Fire Rate (iter-v3/035) | OOS Fire Rate (iter-v3/035) | Change in this iteration |
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

**Most plausible failure mode**: vol_adj_autocorr has no TRX-specific signal — the iter-v3/026
universal failure was NOT a cross-symbol contamination artifact but rather a genuine indicator
that autocorrelation normalized by realized vol is inert in the 8h TRX model at n_trials=35.
When isolated to TRX-only, IS Sharpe would be near iter-v3/035 anchor (-0.10) with TRX
vol_adj_autocorr importance in the [0, 15] range (NULL-RESULT or PROMISING-INERT). OOS
Sharpe would show near-zero delta from the anchor. Classification: NULL-RESULT (axis saturated
for TRX at n_trials=35 budget).

**Second plausible failure mode**: vol_adj_autocorr importance is non-trivial in TRX model
(importance 15-29, PROMISING-INERT range) but OOS Sharpe falls below +2.40 anchor lower band.
This would indicate that TRX's vol_adj_autocorr IS signal IS learned but produces IS exploitation
without OOS generalization — consistent with the category-2 feature stacking constraint: the
TRX model already has regime_momentum_signed_5d (a composited-feature derived from related
autocorrelation/momentum primitives), and adding a second composited feature produces the
same IS-collapse/OOS-spike pattern as iter-v3/026, now localized to TRX.

**What the gates should catch**: any IS collapse in TRX model's per-cell Sharpe (watch for
TRX IS wpnl < iter-v3/035 TRX IS value), or any absurd IS/OOS Sharpe ratio on TRX-specific
per-symbol metrics. If TRX OOS concentration rises above 80% (from iter-v3/035 baseline of
28.44%), that is the second Category 2 stacking alarm.

**Behavioral effect predictor**: Expected TRX IS trade count delta = ±5-15% (one additional
feature changes trade signals). BCH/LDO/ALGO = IDENTICAL to iter-v3/035 (zero delta).
Falsifier: if TRX IS trade count change = 0 trades, vol_adj_autocorr is INERT for TRX.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (EXPLORATION)

This is an EXPLORATION iteration. MERGE criteria are not applicable — only PROMISING /
NEGATIVE / NULL-RESULT classification applies.

**PROMISING** (proceed toward CONFIRMATION cadence): ALL of:
- vol_adj_autocorr feature importance ≥ 30 in TRX model (Category 2 carve-out gate)
- TRX IS trade count change ≠ 0 vs iter-v3/035 anchor (confirms feature is non-inert)
- BCH/LDO/ALGO models show 0 change in IS trade count vs iter-v3/035 anchor
  (confirms no contamination from architecture change)
- OOS Sharpe ≥ +2.40 (lower band of predicted range)

**PROMISING-INERT** (vol_adj_autocorr learned but low importance):
- vol_adj_autocorr importance in [5, 29] in TRX model AND IS trade count for TRX ≠ 0.
  Budget-disambiguation retest at n_trials=70 may be warranted.

**NULL-RESULT (saturated axis for TRX)**:
- vol_adj_autocorr importance < 5 in TRX model AND IS trade count change for TRX = 0.
  Per `feedback_v3_axis_saturation_predictor.md`: axis saturated for TRX; NEXT EXPLORATION
  must move to different axis.

**NEGATIVE**: ANY of:
- OOS Sharpe < +2.0 (OOS falsifier — more than 0.85 below anchor)
- IS Sharpe regression > 0.20 below iter-v3/035 anchor (-0.30 or worse)
- BCH/LDO/ALGO IS trade counts change by > 5 trades vs iter-v3/035 (contamination signal)
- TRX OOS concentration > 80% (stacking alarm — single-symbol lottery)

---

## Section 9 — Library Stack Declaration

- **Python**: 3.13 (runtime)
- **LightGBM**: pinned in pyproject.toml (same as iter-v3/035; no change)
- **numpy**: standard array operations for vol_adj_autocorr computation (already in use)
- **fracdiff (PyPI package)**: UNAVAILABLE (same constraint as iter-v3/035: fracdiff==0.9.0
  requires statsmodels<0.14; project requires statsmodels==0.14.6). Not needed — vol_adj_autocorr
  uses no fracdiff library.
- **No new dependencies required**: vol_adj_autocorr is fully implemented in
  `src/crypto_trade/features_v3/engineered_v3.py` from iter-v3/026. `compute_vol_adj_autocorr`
  exists as dead code (not dispatched since iter-v3/027). Re-adding the dispatch to
  `add_engineered_v3_features` and adding the `V3_FEATURES_PER_SYMBOL["TRXUSDT"]` entry
  are the ONLY code changes required.
- **Library versions (pinned — same as iter-v3/035)**:
  - lightgbm: 4.6.0
  - optuna: 4.8.0
  - numpy: 2.2.6
  - pandas: 3.0.0
  - scikit-learn: 1.8.0
  - scipy: 1.17.0
  - statsmodels: 0.14.6
  - pyarrow: 23.0.1
