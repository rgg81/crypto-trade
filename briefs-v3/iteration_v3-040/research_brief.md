# Iteration v3-040 — Research Brief

**Type**: EXPLORATION (Cycle 3 #1 of 10)
**Track**: v3 (rigor arm) — fortieth iteration
**Branch**: `iteration-v3/040` (off iter-v3/039 head)
**Date**: 2026-05-09
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # single outer seed (EXPLORATION-spec)
n_trials         = 35             # EXPLORATION default
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees OOS metrics for the FIRST time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 3 — #1 of 10
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1
  - ENSEMBLE_SIZE=5 (auto; non-exploration inner ensemble)
  - n_trials=35 (default)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
Single axis: REVERT per-symbol customizations
  - CLEAR V3_FEATURES_PER_SYMBOL (empty dict: {} )
  - CLEAR V3_ATR_MULTIPLIERS_PER_SYMBOL (empty dict: {} )
Predicted classification: PROMISING-MECHANICAL
```

**Context**: iter-v3/039 was a CONFIRMATION of the iter-v3/035 4-ingredient bundle
(BCH fracdiff per-symbol + LDO ATR per-symbol + ALGO universe + regime_momentum).
The CONFIRMATION result was NO-MERGE: per-symbol customizations (V3_FEATURES_PER_SYMBOL BCH
entry + V3_ATR_MULTIPLIERS_PER_SYMBOL LDO entry) broke IS aggregate — IS Sharpe collapsed
below the +0.5101 iter-v3/028 baseline, preventing a strictly-better baseline update.

Cycle 3 starts by reverting ALL per-symbol customizations to establish a clean anchor.
Target state = iter-v3/029 config: 4 symbols (BCH+LDO+TRX+ALGO), regime_momentum_signed_5d
as 14th universal feature, default ATR multipliers (2.0, 1.0) for all symbols, no per-symbol
feature overrides. This is a PROMISING-MECHANICAL classification: the expected lift comes from
removing confirmed drag (IS-breaking customizations), not from discovering new signal.

---

## Section 1 — Hypothesis

Reverting iter-v3/032+iter-v3/035 per-symbol customizations (clearing V3_FEATURES_PER_SYMBOL
and V3_ATR_MULTIPLIERS_PER_SYMBOL to empty dicts) restores the iter-v3/029 single-seed IS
Sharpe anchor of approximately +0.79, confirming that the IS degradation observed at
iter-v3/039 was caused by the per-symbol customization stack rather than any other change,
and establishing a clean cycle 3 baseline from which new EXPLORATION axes can be measured.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — iter-v3/029 Single-Seed Result (anchor baseline)

iter-v3/029 was the first EXPLORATION of cycle 2, run on the iter-v3/028 4-symbol config
(BCH+LDO+TRX+ALGO) with regime_momentum_signed_5d as 14th universal feature, default ATR
multipliers, and no per-symbol customizations. iter-v3/029 established the single-seed
anchor that cycle 2 EXPLORATIONs (iter-v3/030–038) were measured against.

From iter-v3/028 BASELINE_V3.md (multi-seed mean) and iter-v3/029 single-seed anchor:

| Metric | iter-v3/028 (multi-seed) | iter-v3/029 (single-seed anchor) |
|---|---:|---:|
| IS monthly Sharpe | +0.5101 | ~+0.79 (4-sym single-seed) |
| OOS monthly Sharpe | +0.5053 | ~+1.77 (4-sym single-seed) |
| IS Trades | 182 | ~240 (4-sym including ALGO) |
| OOS Trades | 93.5 | ~110-130 |

The ~+0.79 IS / ~+1.77 OOS single-seed result at iter-v3/029 represents the clean 4-symbol
anchor with no per-symbol customizations. This is the target state for iter-v3/040.

### 2.2 — Per-Symbol Customization IS Degradation Evidence

Per-symbol customizations introduced across cycle 2:

| Iteration | Change | Observed IS Delta |
|---|---|---:|
| iter-v3/032 | V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] = (1.5, 0.75) | +0.24 IS (single-seed) |
| iter-v3/035 | V3_FEATURES_PER_SYMBOL["BCHUSDT"] = TOP_N + fracdiff | IS -0.10 (negative IS single-seed) |
| iter-v3/038 | V3_FEATURES_PER_SYMBOL["ALGOUSDT"] = TOP_N + fracdiff | IS worsened further |
| iter-v3/039 | CONFIRMATION (BCH+LDO per-symbol; ALGO reverted) | IS < +0.5101 baseline (NO-MERGE) |

Cumulative IS swing from per-symbol customizations: approximately -0.55 IS Sharpe versus
the iter-v3/029 clean-4-symbol anchor. Clearing both dicts removes both effects atomically.

Analysis script: `analysis/iteration_v3-039/is_pbo_strategy_axis_analysis.py` (committed
SHA `9294855`) covers IS-only PBO strategy-axis analysis confirming the IS degradation
pattern across cycle 2 EXPLORATIONs. This script validates on IS data only and was
committed before this brief.

### 2.3 — Predicted Behavioral Effect (per `feedback_v3_axis_saturation_predictor.md`)

Clearing V3_FEATURES_PER_SYMBOL removes BCH's 15-feature set (reverts to 14-feature fallback).
Expected IS trade count delta: BCH model switches from 15-feature to 14-feature input —
predicted IS trade change: ≤10% total portfolio (driven by BCH model internal Optuna variance
at 14 vs 15 features). If observed IS trade count vs iter-v3/039 single-seed changes by
> 30 trades (11%), investigate whether the revert introduced unexpected cross-symbol interactions.

Clearing V3_ATR_MULTIPLIERS_PER_SYMBOL reverts LDO barriers from (1.5, 0.75) → (2.0, 1.0).
LDO TP barrier widens: 10.01% → 13.36% (at natr_21_raw median 6.68%). Expected effect:
fewer LDO trades (wider barriers = harder to reach TP = more timeout exits). Predicted LDO
IS trade reduction: ~10-20% fewer LDO trades. Net portfolio IS trade change: ~3-5% fewer.

Falsifier: if observed IS trade count change vs iter-v3/039 is > 30 trades in either direction
OR if LDO trade count does NOT decrease (wider barriers should reduce trade frequency),
this is a structural anomaly requiring investigation.

---

## Section 3 — Proposed Changes

### Sub-fix 1: Clear V3_FEATURES_PER_SYMBOL

In `src/crypto_trade/features_v3/__init__.py`, clear the dict to empty:

```python
V3_FEATURES_PER_SYMBOL: dict[str, tuple[str, ...]] = {}
```

Removes: BCHUSDT entry (14 universal + fracdiff_d05_close).
Effect: BCH reverts to 14-feature V3_FEATURE_COLUMNS_TOP_N fallback (same as ALGO/LDO/TRX).
Architecture (the dict definition and `features_for_symbol` helper) is KEPT — only emptied.

### Sub-fix 2: Clear V3_ATR_MULTIPLIERS_PER_SYMBOL

In `src/crypto_trade/features_v3/__init__.py`, clear the dict to empty:

```python
V3_ATR_MULTIPLIERS_PER_SYMBOL: dict[str, tuple[float, float]] = {}
```

Removes: LDOUSDT entry ((1.5, 0.75)).
Effect: LDO reverts to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via fallback.
Architecture (the dict definition and `atr_multipliers_for_symbol` helper) is KEPT — only emptied.

### Sub-fix 3: Update ITERATION_LABEL

In `run_baseline_v3.py`, change:

```python
ITERATION_LABEL = "v3-040"
```

### Sub-fix 4: Update `_verify_feature_columns` in `run_baseline_v3.py`

Rewrite the per-symbol assertions to iter-v3/040 state:
- All 4 symbols (BCH/LDO/TRX/ALGO) fall back to V3_FEATURE_COLUMNS_TOP_N (14 features)
- V3_FEATURES_PER_SYMBOL is empty (no per-symbol entries)
- V3_ATR_MULTIPLIERS_PER_SYMBOL is empty (no per-symbol ATR overrides)
- fracdiff_d05_close MUST NOT appear in any symbol's feature set
- Remove all BCH-specific assertions (len==15, fracdiff present, etc.)
- Add assertion: V3_FEATURES_PER_SYMBOL is empty (len == 0)
- Add assertion: V3_ATR_MULTIPLIERS_PER_SYMBOL is empty (len == 0)
- Add assertion: atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0) (default)
- Add assertion: features_for_symbol("BCHUSDT") == V3_FEATURE_COLUMNS_TOP_N (14, no fracdiff)

### Sub-fix 5: Update tests in `tests/features_v3/test_features_for_symbol.py`

Rewrite tests to iter-v3/040 state (all 4 symbols fall back to 14-feature universal list):

Mandatory assertions for iter-v3/040:
- `test_bch_fallback_14`: BCHUSDT returns 14 features (no per-symbol entry; fallback)
- `test_bch_no_fracdiff`: BCHUSDT does NOT include fracdiff_d05_close
- `test_algo_fallback_14`: ALGOUSDT returns 14 features (unchanged from iter-v3/039)
- `test_algo_no_fracdiff`: ALGOUSDT does NOT include fracdiff_d05_close
- `test_ldo_fallback_14`: LDOUSDT returns 14 features (unchanged)
- `test_ldo_no_fracdiff`: LDOUSDT does NOT include fracdiff_d05_close
- `test_trx_fallback_14`: TRXUSDT returns 14 features (unchanged)
- `test_bchusdt_not_in_per_symbol`: BCHUSDT NOT in V3_FEATURES_PER_SYMBOL
- `test_algousdt_not_in_per_symbol`: ALGOUSDT NOT in V3_FEATURES_PER_SYMBOL
- `test_ldousdt_not_in_per_symbol`: LDOUSDT NOT in V3_FEATURES_PER_SYMBOL
- `test_trxusdt_not_in_per_symbol`: TRXUSDT NOT in V3_FEATURES_PER_SYMBOL
- `test_v3_features_per_symbol_is_empty`: len(V3_FEATURES_PER_SYMBOL) == 0
- `test_v3_atr_multipliers_per_symbol_is_empty`: len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 0
- `test_ldo_atr_default`: atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0)
- `test_regime_momentum_in_universal_list`: regime_momentum_signed_5d in TOP_N
- `test_fracdiff_not_in_universal_list`: fracdiff_d05_close NOT in TOP_N
- `test_cross_asset_divergence_not_in_universal_list`: cross_asset_divergence_norm NOT in TOP_N
- `test_vol_adj_autocorr_not_in_universal_list`: vol_adj_autocorr NOT in TOP_N
- `test_universal_list_is_14`: len(V3_FEATURE_COLUMNS_TOP_N) == 14
- `test_features_for_symbol_unknown_fallback`: unknown symbol falls back to TOP_N (14 features)

### Bundle state verification (what _verify_feature_columns must assert after sub-fixes)

```
V3_FEATURE_COLUMNS_TOP_N: 14 features — NO fracdiff_d05_close in universal list    PASS
V3_FEATURES_PER_SYMBOL: {} (empty — no per-symbol entries)                          PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL: {} (empty — no per-symbol ATR overrides)             PASS
features_for_symbol("BCHUSDT") == V3_FEATURE_COLUMNS_TOP_N (14 features)            PASS
features_for_symbol("ALGOUSDT") == V3_FEATURE_COLUMNS_TOP_N (14 features)           PASS
features_for_symbol("LDOUSDT") == V3_FEATURE_COLUMNS_TOP_N (14 features)            PASS
features_for_symbol("TRXUSDT") == V3_FEATURE_COLUMNS_TOP_N (14 features)            PASS
atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0)                                 PASS
atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0)                                 PASS
V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols                                       PASS
REQUIRED_GAP = 88 = (21+1) × 4                                                      PASS
regime_momentum_signed_5d in V3_FEATURE_COLUMNS_TOP_N                               PASS
```

---

## Section 4 — Expected OOS Impact

**IS Sharpe prediction (single-seed, vs iter-v3/029 single-seed anchor ~+0.79):**
- Predicted band: [+0.50, +0.95]
- Median point estimate: +0.75
- Rationale: Clearing per-symbol customizations restores the iter-v3/029 clean-4-symbol
  config. Single-seed IS Sharpe expected near the iter-v3/029 anchor (+0.79) with normal
  single-seed variance.

**OOS Sharpe prediction (single-seed, vs iter-v3/029 single-seed anchor ~+1.77):**
- Predicted band: [+1.50, +2.10]
- Median point estimate: +1.80
- Rationale: iter-v3/029 OOS ~+1.77 was the clean 4-symbol anchor. Reverting to that
  exact config should reproduce approximately the same OOS result modulo data freshness.

**OOS falsifier (pre-registered):**
- If IS Sharpe < +0.30 after revert: the revert did not restore the iter-v3/029 anchor;
  some other change between iter-v3/029 and iter-v3/040 is causing IS degradation that
  is NOT attributable to per-symbol customizations. Escalate to QR.

**Classification falsifier (pre-registered):**
- If IS Sharpe >= +0.50 and OOS Sharpe >= +1.50: PROMISING-MECHANICAL CONFIRMED — the
  per-symbol customizations were the source of IS degradation; cycle 3 anchor is established.
- If IS Sharpe < +0.30 despite full revert: NEGATIVE-unexpected — the degradation source
  is NOT per-symbol customizations; requires diagnostic EXPLORATION on a different axis.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.

**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward from
BASELINE_V3.md (iter-v3/028).

**R3 (OOD detection)**: unchanged. zscore_threshold=2.0 (iter-v3/011).

**Per-symbol customization removal risk**: clearing V3_ATR_MULTIPLIERS_PER_SYMBOL widens
LDO barriers (1.5x, 0.75x → 2.0x, 1.0x). LDO TP barrier increases from ~10% to ~13.4%.
Expected effect: fewer LDO trades (wider barriers are harder to reach), lower LDO IS trade
count. This is the EXPECTED mechanical effect of the revert — NOT a risk requiring mitigation.
If LDO trade count increases unexpectedly after revert, investigate.

**Concentration risk**: clearing BCH's per-symbol fracdiff entry reduces BCH-specific signal.
Expected BCH OOS concentration to decrease from iter-v3/039's ~47% toward ~25-35% (each of 4
symbols contributing ~25%). If BCH concentration drops below 10% after revert, investigate
whether the BCH model has degraded beyond the expected architectural change.

---

## Section 6 — Risk Management Design (7-Primitive Gate Table)

All 7 risk gates carried forward from iter-v3/028/039 baseline unchanged. No gate
parameters are modified in this EXPLORATION.

| Gate | Type | Parameter | Change |
|---|---|---|---|
| 1 — BTC trend | BtcTrendFilterConfig | lookback=42, threshold=15% | None |
| 2 — Hit rate | HitRateGateConfig | window=20, sl_threshold=0.65 | DISABLED (unchanged) |
| 3 — ADX gate | ADX regime filter | threshold=20 (v3 default) | None |
| 4 — Hurst regime | hurst_100 > 0.5 gate | implicit in regime_momentum | None |
| 5 — Drawdown brake | R2 cumulative | per-model PnL tracking | None |
| 6 — OOD gate | Mahalanobis z-score | zscore_threshold=2.0 | None |
| 7 — Liquidity floor | NATR floor | NATR >= 0.5% | None |

Regime coverage: BCH/LDO/TRX/ALGO all pass Gate 7 (NATR >= 0.5%) per iter-v3/032 EDA
(`analysis/iteration_v3-032/per_symbol_atr_eda.py` SHA `9834e84`). No new symbols added.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode (NEGATIVE-unexpected):**
The revert clears per-symbol customizations but IS Sharpe does NOT recover to ~+0.79.
This would indicate the IS degradation at iter-v3/039 was caused by something other than
per-symbol customizations — possibly Optuna variance at single-seed (the iter-v3/039 run
was --seeds 2; iter-v3/040 is --seeds 1, so the comparison is noisy) or data-freshness
drift between iter-v3/029 and iter-v3/040. If IS < +0.30, escalate to QR for diagnostic.

**Second plausible failure mode (PROMISING-MECHANICAL-partial):**
The revert recovers IS Sharpe to [+0.30, +0.50] — better than iter-v3/039 but not reaching
the iter-v3/029 anchor. This indicates partial recovery: the per-symbol customizations were
contributing to IS drag but were not the sole cause. Classify as PROMISING-MECHANICAL with
partial IS recovery; cycle 3 can still proceed from this anchor.

**What the gates should catch:**
Gate 6 (OOD): with 14-feature universal set (no fracdiff), BCH model's OOD filter fires at
the standard zscore_threshold=2.0. If fracdiff_d05_close was anchoring BCH's OOD distribution
in IS, removing it may shift BCH OOD firing rate. Expected BCH OOD rate: comparable to
iter-v3/029 (no fracdiff in IS).

**Behavioral effect predictor:**
Predicted IS trade count delta: -5% to -10% vs iter-v3/039 (LDO wider barriers = fewer
LDO trades; BCH 14-feature = comparable IS trade count). Falsifier: if IS trade count
increases by > 20 trades vs iter-v3/039, investigate.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is an EXPLORATION iteration. MERGE gates do NOT apply. Classification criteria
(pre-registered before backtest runs):

**PROMISING-MECHANICAL**: IS Sharpe >= +0.50 (recovery from iter-v3/039 degradation)
  AND OOS Sharpe >= +1.50 (recovery toward iter-v3/029 anchor)
  Classification triggers: cycle 3 anchor ESTABLISHED; next EXPLORATION measures from
  this baseline.

**PROMISING-MECHANICAL-partial**: IS Sharpe in [+0.30, +0.50) (partial recovery)
  AND OOS Sharpe >= +1.00 (positive OOS)
  Classification triggers: cycle 3 anchor partially established; QR notes partial recovery
  and proceeds with next EXPLORATION from this IS level.

**NEGATIVE-unexpected**: IS Sharpe < +0.30 after full revert
  Classification triggers: revert did not restore expected IS level; escalate to QR for
  diagnostic EXPLORATION on a different axis.

**Pre-registered EXPLORATION classification threshold (locked before backtest):**
- PROMISING-MECHANICAL requires IS >= +0.50 AND OOS >= +1.50
- These thresholds are LOCKED and cannot be post-hoc renegotiated.

---

## Section 9 — Library Stack Declaration

All versions identical to iter-v3/039 / iter-v3/028 CONFIRMATION-MERGE reproducibility stamp:

| Package | Version | Source |
|---|---|---|
| lightgbm | 4.6.0 | pyproject.toml pinned |
| numpy | 2.2.6 | pyproject.toml pinned |
| optuna | 4.8.0 | pyproject.toml pinned |
| pandas | 3.0.0 | pyproject.toml pinned |
| pyarrow | 23.0.1 | pyproject.toml pinned |
| scikit-learn | 1.8.0 | pyproject.toml pinned |
| scipy | 1.17.0 | pyproject.toml pinned |
| statsmodels | 0.14.6 | pyproject.toml pinned |
| pytest | 9.0.2 | pyproject.toml dev dep |

**fracdiff (PyPI package)**: UNAVAILABLE (same as iter-v3/039). Pure-numpy inline
implementation `compute_fracdiff_d05_close` in `src/crypto_trade/features_v3/engineered_v3.py`
is used as fallback (established at iter-v3/034). The column `fracdiff_d05_close` is still
COMPUTED in parquets (it is used for BCH at iter-v3/035-039 and preserved as dead parquet
column at iter-v3/040) but is NOT passed as a model input feature to any symbol at iter-v3/040.

**No new library dependencies**: this EXPLORATION changes only configuration dicts.
All infrastructure (features_v3, runner, validation_v3) is UNCHANGED.
