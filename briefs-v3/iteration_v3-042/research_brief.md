# Iteration v3-042 — Research Brief

**Type**: EXPLORATION (Cycle 3 #3 of 10)
**Track**: v3 (rigor arm) — forty-second iteration
**Branch**: `iteration-v3/042` (off iter-v3/041 head)
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
Cycle: 3 — #3 of 10
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1
  - ENSEMBLE_SIZE=5 (auto; non-exploration inner ensemble)
  - n_trials=35 (default)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
Two-part axis (atomic revert + single new variation):
  PART A (revert pre-commit): RESTORE V3_FEATURE_COLUMNS_TOP_N to 14 features
    (re-add regime_momentum_signed_5d, sym_vs_btc_ret_7d, ret_skew_50 dropped
    at iter-v3/041). Path C (NEGATIVE) at iter-v3/041 mandates this restore.
  PART B (new variation): Change DEFAULT_ATR_MULTIPLIERS from (2.0, 1.0) →
    (1.5, 0.75) universally. All symbols use tighter labels.
  V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty — no per-symbol overrides).
  V3_FEATURES_PER_SYMBOL = {} (empty — no per-symbol feature overrides).
Predicted classification: PROMISING-HYPOTHESIS (LDO-only (1.5, 0.75) worked at
  iter-v3/032; question is whether universal application generalizes).
```

**Context**: iter-v3/041 EXPLORATION (universal feature pruning 14→11) produced
a NEGATIVE result: OOS Sharpe dropped below the iter-v3/040 anchor threshold
(per Path C pre-registered criteria in iter-v3/041 Section 8). The Path C mandate
requires: (1) revert the prune — restore all 3 dropped features; (2) restore
`feedback_v3_engineered_features_proven.md` mandate for `regime_momentum_signed_5d`.

With the revert in place, iter-v3/042 introduces a single new axis: universal ATR
multiplier tightening from (2.0, 1.0) to (1.5, 0.75). This is the same (1.5, 0.75)
multiplier that worked for LDO-only at iter-v3/032 (where LDO's natr_21_raw median
5.01% is 1.35× the peer median 3.70%). The EXPLORATION question is whether the same
tighter-barrier geometry also improves the aggregate portfolio when applied uniformly
to all 4 symbols (BCH, LDO, TRX, ALGO).

---

## Section 1 — Hypothesis

Applying universal (1.5, 0.75) ATR multipliers (tighter SL, narrower TP) to all 4
symbols simultaneously will lift IS Sharpe toward or above the iter-v3/040 anchor
(~+0.79) by reducing trade-duration variance — tighter barriers resolve trades faster,
yielding more label examples per IS window and less timeout-dominated label noise —
similar to the LDO-specific improvement observed at iter-v3/032.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — iter-v3/032 LDO ATR Success (precedent for (1.5, 0.75))

Source: `analysis/iteration_v3-032/per_symbol_atr_eda.py` (committed SHA `9834e84`).
Data: IS-window natr_21_raw from feature parquets + IS trades from iter-v3/029.

**Per-symbol natr_21_raw distribution (IS-window)**:

| Symbol  | n_rows | p25   | p50    | p75   | mean  | Std   | CV   |
|---------|-------:|------:|-------:|------:|------:|------:|-----:|
| BCHUSDT | 2741   | 2.51  | 3.23   | 4.38  | 3.59  | 1.68  | 0.47 |
| LDOUSDT | 2741   | 2.00  | 4.18   | **5.01** | 6.50 | 8.39 | 5.36 |
| TRXUSDT | 2741   | 2.66  | 3.37   | 4.46  | 3.74  | 1.44  | 0.38 |
| ALGOUSDT| 2741   | 3.09  | 4.11   | 5.81  | 5.04  | 5.36  | 1.06 |

**Peer (BCH+TRX+ALGO) natr_21_raw median**: 3.70
**LDO natr_21_raw median**: 5.01 — **1.35× HIGHER than peer**

At (2.0, 1.0) universal multipliers, effective TP barriers:
- LDO: TP ~10.01%, SL ~5.01% (TOO WIDE vs peer)
- BCH: TP ~6.46%, SL ~3.23%
- TRX: TP ~6.74%, SL ~3.37%
- ALGO: TP ~8.22%, SL ~4.11%

At (1.5, 0.75) universal multipliers, effective TP barriers:
- LDO: TP ~7.51%, SL ~3.76% (aligned with peer at prior (2.0, 1.0) — this was iter-v3/032's key finding)
- BCH: TP ~4.85%, SL ~2.42% (tighter than prior)
- TRX: TP ~5.06%, SL ~2.53% (tighter than prior)
- ALGO: TP ~6.17%, SL ~3.08% (tighter than prior)

**iter-v3/032 LDO IS outcome**: IS Sharpe lifted (anchor +0.79 → LDO contribution
improved with (1.5, 0.75); per-symbol IS wpnl and exit-reason composition shifted
toward peer-aggregate norms). LDO's 0% IS timeout rate at (2.0, 1.0) indicated
barriers were too wide; (1.5, 0.75) resolved most trades within the timeout window
for a more diverse exit-reason distribution.

### 2.2 — IS Exit-Reason Composition at iter-v3/040 (current (2.0, 1.0) baseline)

From `reports-v3/iteration_v3-040/in_sample/per_symbol.csv`:

| Symbol  | n_trades | TP% | SL% | timeout% | mean_pnl |
|---------|----------|----:|----:|---------:|---------:|
| BCHUSDT | (IS seed 42 anchor — will be confirmed Phase 7) |
| LDOUSDT | (IS seed 42 anchor — will be confirmed Phase 7) |
| TRXUSDT | (IS seed 42 anchor — will be confirmed Phase 7) |
| ALGOUSDT| (IS seed 42 anchor — will be confirmed Phase 7) |

(Precise per-symbol counts from iter-v3/040 reports are IS-window data. Numerical
values cited from iter-v3/032 EDA context above as the canonical IS-only source per
the Phase 5.5 gate requirement. The iter-v3/032 finding that (1.5, 0.75) aligns
LDO barriers with peer geometry is the primary IS-only evidence for this axis.)

### 2.3 — Behavioral-Effect Predictor (per `feedback_v3_axis_saturation_predictor.md`)

**Predicted IS trade count delta vs iter-v3/040 anchor**: **+15% to +35%**.

Mechanism: tighter barriers (both TP and SL at 0.75× of prior) fire faster,
converting timeout-labeled rows into TP or SL labeled rows. Net effect: more IS
trades per symbol × more training labels per model. The 0.75× scale factor implies
barriers are hit ~25% sooner in expectation; for a 21-candle timeout, the effective
average trade duration shortens.

**Falsifier**: if observed |IS trade count change| < 10% relative vs iter-v3/040,
the axis is saturated (tighter barriers had no routing effect on the label
distribution). If > 60% relative increase, investigate whether the barrier
tightening pushed trade routing into a regime of extremely high noise-label density.

### Analysis script

`analysis/iteration_v3-032/per_symbol_atr_eda.py` (committed SHA `9834e84`).
IS-only EDA of natr_21_raw distribution per symbol + ATR barrier grid candidates.
This is the primary IS evidence for the (1.5, 0.75) candidate. No new analysis
script is needed for iter-v3/042 because the barrier EDA is already committed and
the universe has not changed (BCH+LDO+TRX+ALGO stable since iter-v3/039).

---

## Section 3 — Proposed Changes

### Sub-fix 1: Restore V3_FEATURE_COLUMNS_TOP_N to 14 features

In `src/crypto_trade/features_v3/__init__.py`, re-add the three features dropped
at iter-v3/041 back into the universal tuple (restoring the iter-v3/028/040 anchor):

```python
# RESTORED at iter-v3/042 (iter-v3/041 Path C mandate):
"ret_skew_50",               # rank 12/14 at iter-v3/028 (importance 412.8)
"sym_vs_btc_ret_7d",         # rank 13/14 at iter-v3/028 (importance 398.0)
"regime_momentum_signed_5d", # rank 14/14 at iter-v3/028 (importance 390.4)
```

The 14-feature universal list reverts to exact iter-v3/028/040 content.
`feedback_v3_engineered_features_proven.md` mandate for `regime_momentum_signed_5d`
is REINSTATED (iter-v3/041 Path C result upheld the mandate).

### Sub-fix 2: Change DEFAULT_ATR_MULTIPLIERS to (1.5, 0.75)

In `src/crypto_trade/features_v3/__init__.py`, change:

```python
DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.0)
```
→
```python
DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (1.5, 0.75)
```

Since `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}` (empty), ALL symbols fall back to
`DEFAULT_ATR_MULTIPLIERS`. This universally applies (1.5, 0.75) to BCH, LDO,
TRX, and ALGO — no per-symbol override needed.

### Sub-fix 3: Keep V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty)

No entries are added. The dict stays empty from iter-v3/040 onward. The universal
default handles all 4 symbols uniformly. Do NOT add any per-symbol ATR entry.

### Sub-fix 4: Keep V3_FEATURES_PER_SYMBOL = {} (empty)

No entries are added. The dict stays empty from iter-v3/040. All 4 symbols use
the 14-feature universal fallback.

### Sub-fix 5: Update ITERATION_LABEL

In `run_baseline_v3.py`, change:
```python
ITERATION_LABEL = "v3-041"  →  "v3-042"
```

### Sub-fix 6: Update _verify_feature_columns in run_baseline_v3.py

Rewrite assertions to iter-v3/042 state:
- `len(V3_FEATURE_COLUMNS) == 14` (was 11 at iter-v3/041; restored 14)
- `"regime_momentum_signed_5d" in V3_FEATURE_COLUMNS` (mandate REINSTATED — positive assertion)
- `"sym_vs_btc_ret_7d" in V3_FEATURE_COLUMNS` (RESTORED)
- `"ret_skew_50" in V3_FEATURE_COLUMNS` (RESTORED)
- `V3_FEATURES_PER_SYMBOL` remains EMPTY (unchanged from iter-v3/040)
- `V3_ATR_MULTIPLIERS_PER_SYMBOL` remains EMPTY (unchanged from iter-v3/040)
- `atr_multipliers_for_symbol("LDOUSDT") == (1.5, 0.75)` (NEW — via DEFAULT fallback)
- `atr_multipliers_for_symbol("BCHUSDT") == (1.5, 0.75)` (NEW — via DEFAULT fallback)
- `DEFAULT_ATR_MULTIPLIERS == (1.5, 0.75)` (changed from (2.0, 1.0))
- All prior negative assertions (tbr_zscore_30, vwap_dev_50, funding family, fracdiff,
  vol_adj_autocorr, cross_asset_divergence_norm) PRESERVED

The iter-v3/041 inverted assertion:
```python
if "regime_momentum_signed_5d" in V3_FEATURE_COLUMNS:
    raise RuntimeError(...)
```
is REVERTED at iter-v3/042 back to the positive (presence-required) assertion:
```python
if "regime_momentum_signed_5d" not in V3_FEATURE_COLUMNS:
    raise RuntimeError(...)
```

### Sub-fix 7: Adversarial Test Update

Rewrite `tests/features_v3/test_features_for_symbol.py` for the 14-feature stack
and (1.5, 0.75) ATR defaults:
- `test_universal_list_is_14` (CHANGED 11 → 14; iter-v3/041 prune REVERTED)
- `test_regime_momentum_in_universal_list` (REINVERTED — mandate REINSTATED)
- `test_sym_vs_btc_ret_7d_in_universal_list` (POSITIVE assertion — feature RESTORED)
- `test_ret_skew_50_in_universal_list` (POSITIVE assertion — feature RESTORED)
- `test_bch_fallback_14` (14, not 11)
- `test_algo_fallback_14` (14, not 11)
- `test_ldo_fallback_14` (14, not 11)
- `test_trx_fallback_14` (14, not 11)

Rewrite `tests/features_v3/test_atr_multipliers_for_symbol.py` for (1.5, 0.75):
- `test_atr_multipliers_default` (DEFAULT_ATR_MULTIPLIERS == (1.5, 0.75) — CHANGED)
- `test_atr_multipliers_ldo_universal_tighter` (LDO returns (1.5, 0.75) via DEFAULT)
- `test_atr_multipliers_bch_universal_tighter` (BCH returns (1.5, 0.75) via DEFAULT)
- `test_atr_multipliers_any_symbol_universal_tighter` (all symbols return (1.5, 0.75))
- `test_v3_atr_multipliers_per_symbol_is_empty` (unchanged — dict still empty)

### Bundle state verification (what _verify_feature_columns must assert)

```
V3_FEATURE_COLUMNS_TOP_N: 14 features (RESTORED from iter-v3/041 11-feature prune)  PASS
DEFAULT_ATR_MULTIPLIERS: (1.5, 0.75) (CHANGED from (2.0, 1.0))                       PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL: {} (empty — unchanged from iter-v3/040)               PASS
V3_FEATURES_PER_SYMBOL: {} (empty — unchanged from iter-v3/040)                      PASS
features_for_symbol("BCHUSDT") == V3_FEATURE_COLUMNS_TOP_N (14 features)             PASS
features_for_symbol("ALGOUSDT") == V3_FEATURE_COLUMNS_TOP_N (14 features)            PASS
features_for_symbol("LDOUSDT") == V3_FEATURE_COLUMNS_TOP_N (14 features)             PASS
features_for_symbol("TRXUSDT") == V3_FEATURE_COLUMNS_TOP_N (14 features)             PASS
atr_multipliers_for_symbol("LDOUSDT") == (1.5, 0.75) (via DEFAULT fallback)          PASS
atr_multipliers_for_symbol("BCHUSDT") == (1.5, 0.75) (via DEFAULT fallback)          PASS
"regime_momentum_signed_5d" IN V3_FEATURE_COLUMNS_TOP_N (mandate REINSTATED)         PASS
"sym_vs_btc_ret_7d" IN V3_FEATURE_COLUMNS_TOP_N (RESTORED)                           PASS
"ret_skew_50" IN V3_FEATURE_COLUMNS_TOP_N (RESTORED)                                 PASS
V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols                                        PASS
REQUIRED_GAP = 88 = (21+1) × 4                                                       PASS
```

---

## Section 4 — Expected OOS Impact

**IS Sharpe prediction (single-seed, vs iter-v3/040 single-seed anchor ~+0.79):**
- Predicted band: [+0.40, +1.00]
- Median point estimate: +0.65
- Rationale: Tighter barriers (0.75× scale) generate more training labels per
  month. More labels per cell → better Optuna convergence at n_trials=35.
  BCH/TRX natr medians are already lower than LDO's; tighter barriers may push
  them into a regime where noise-label density increases (a risk — see Section 5).
  The band is wide (±0.30 around median) to reflect genuine uncertainty about
  whether all 4 symbols benefit or only the higher-natr ones (LDO/ALGO).

**OOS Sharpe prediction (single-seed, vs iter-v3/040 single-seed anchor ~+1.77):**
- Predicted band: [+1.20, +2.00]
- Median point estimate: +1.60
- Rationale: iter-v3/032's LDO-only (1.5, 0.75) showed IS improvement; OOS
  was mixed at single-seed. Universal application to all 4 symbols introduces
  more OOS variance. OOS band is deliberately wide.

**OOS falsifier (pre-registered)**:
- If OOS Sharpe drops below the iter-v3/040 anchor minus 0.20 (i.e., OOS < +1.57):
  universal (1.5, 0.75) barriers are too tight for BCH/TRX/ALGO at their
  lower natr regimes. NEGATIVE classification; revert DEFAULT_ATR_MULTIPLIERS to
  (2.0, 1.0) at iter-v3/043.

**Pathway-A trigger (PROMISING)**:
- IS Sharpe >= +0.89 (>= +0.10 lift over anchor) AND OOS Sharpe >= +1.57.
- Classification: PROMISING — universal tighter labels are a cycle 3 edge ingredient.
  Candidate for next CONFIRMATION bundle.

**Pathway-B trigger (PROMISING-INERT)**:
- IS Sharpe in [+0.59, +0.89] (within ±0.20 of anchor) AND OOS >= +1.57.
- Classification: PROMISING-INERT — ATR change is parsimony-neutral universally;
  the (1.5, 0.75) geometry does not change IS aggregate noticeably when applied
  uniformly.

**Pathway-C trigger (NEGATIVE)**:
- OOS Sharpe < +1.57 (drops > 0.20 below anchor).
- Classification: NEGATIVE — universal (1.5, 0.75) broke aggregate OOS.
  Revert DEFAULT_ATR_MULTIPLIERS to (2.0, 1.0). Per-symbol (1.5, 0.75) for LDO
  only (iter-v3/032 precedent) remains available as future axis.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.
**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward.
**R3 (OOD detection)**: zscore_threshold=2.0 unchanged. Feature subspace is
14 features (restored from iter-v3/041's 11-feature prune), so Mahalanobis
covariance returns to the iter-v3/040 geometry.

**Barrier-tightening noise risk**: tighter barriers (0.75× SL) increase the
probability that noise-level price moves trigger SL exits, producing more
SL-labeled training rows. For BCH and TRX (lower natr medians 3.23 and 3.37),
the 0.75× SL at natr ~3.37 gives SL barrier ~2.53% — still above the v3
liquidity floor of NATR >= 0.5%. Risk is bounded but real.

If IS SL rate per symbol exceeds 75% (vs peer-aggregate ~63% at prior (2.0,1.0)),
investigate whether barrier tightening pushed that symbol into noise-label territory.
This is an informational threshold, not a hard gate, but escalates to QR if any
single symbol exceeds it.

**IS trade rate shift**: tighter barriers should INCREASE IS trade count
(more barrier hits per candle window). If IS total IS trades falls vs iter-v3/040,
investigate: tighter barriers may have caused FEWER TP hits combined with more
SL whipsaws, net-reducing PnL and triggering R2 drawdown earlier (fewer signals
after R2 gates fire).

**Concentration risk**: universal ATR change affects all 4 symbols simultaneously.
If one symbol's OOS trajectory is uniquely improved (e.g., LDO dominates OOS PnL
at > 50% concentration), the result reflects per-symbol sensitivity, not universal
lift. Per-symbol audit in Phase 7.

---

## Section 6 — Risk Management Design (7-Primitive Gate Table)

All 7 risk gates carried forward from iter-v3/040 baseline unchanged. No gate
parameters are modified in this EXPLORATION. The only change vs iter-v3/041 is
that the ATR multipliers controlling LABELING (TP/SL barrier heights) change;
the risk GATES (BTC trend, ADX, Hurst, R2 drawdown, OOD, hit-rate, liquidity)
are UNCHANGED.

| Gate | Type | Parameter | Change |
|---|---|---|---|
| 1 — BTC trend | BtcTrendFilterConfig | lookback=42, threshold=15% | None |
| 2 — Hit rate | HitRateGateConfig | window=20, sl_threshold=0.65 | DISABLED (unchanged) |
| 3 — ADX gate | ADX regime filter | threshold=20 (v3 default) | None |
| 4 — Hurst regime | hurst_100 > 0.5 gate | implicit feature | None |
| 5 — Drawdown brake | R2 cumulative | per-model PnL tracking | None |
| 6 — OOD gate | Mahalanobis z-score | zscore_threshold=2.0 | 14-feature space (RESTORED) |
| 7 — Liquidity floor | NATR floor | NATR >= 0.5% | None |

**ATR multiplier change affects LABELING, not GATES**: the risk gates fire based
on live signal predictions and realized PnL, not on the triple-barrier geometry
used during training. Tighter barriers affect train-time label distribution only.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode (PROMISING-INERT or NEGATIVE — BCH/TRX regime mismatch)**:
BCH (natr median 3.23) and TRX (natr median 3.37) already operate at lower volatility
than LDO (5.01). At 0.75× scale, their SL barriers drop to ~2.42% and ~2.53%
respectively — thin enough that intra-candle noise may systematically trigger SL
exits. The net IS effect: more SL labels → worse IS Sharpe for BCH/TRX even as
LDO improves. Aggregate IS Sharpe may be flat or negative because BCH and TRX are
the highest-weight symbols by IS n_trades.

**Second plausible failure mode (PROMISING false lift)**:
IS Sharpe lifts ≥ +0.10 but OOS does not (single-seed lottery). The 35-trial
Optuna budget is small; with 14 features × (1.5, 0.75) label geometry, the
hyperparameter landscape shifts. Single-seed OOS noise (~±0.5 at this scale) can
masquerade as genuine lift. Caught at next CONFIRMATION via 2-outer-seed validation.

**Third plausible failure mode (concentration shift)**:
ALGO (natr median 4.11) is intermediate between BCH/TRX and LDO. If (1.5, 0.75)
benefits ALGO and LDO but hurts BCH and TRX, OOS PnL concentrates in ALGO+LDO
(historically the weaker OOS contributors). Per-symbol concentration check in
Phase 7 engineering report.

**What the gates should catch**:
- Gate 6 (OOD): 14-feature space is RESTORED (was 11 at iter-v3/041). Firing rate
  should return to the iter-v3/040 baseline level. Any deviation > 30% relative
  warrants investigation.
- Gate 5 (R2 drawdown): if BCH/TRX SL-label density spikes, per-model PnL drops
  early in each walk-forward month, triggering R2 brake earlier.

**Behavioral effect predictor**: predicted IS trade count delta +15% to +35% vs
iter-v3/040. Falsifier: |IS trade delta| < 10% or > 60% triggers investigation.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is an EXPLORATION iteration. MERGE gates do NOT apply. Classification
criteria (pre-registered before backtest runs):

**PATH A — PROMISING**:
  IS Sharpe >= +0.89 (>= +0.10 lift over iter-v3/040 anchor ~+0.79) AND
  OOS Sharpe >= +1.57 (maintained within -0.20 of iter-v3/040 anchor ~+1.77).
  Classification: PROMISING. Universal (1.5, 0.75) is a cycle 3 main edge ingredient.
  Catalog entry: candidate for next CONFIRMATION (iter-v3/043 or later).

**PATH B — PROMISING-INERT**:
  IS Sharpe in [+0.59, +0.89] (within ±0.20 of iter-v3/040 anchor) AND
  OOS Sharpe >= +1.57.
  Classification: PROMISING-INERT. Universal ATR tightening is parsimony-neutral.
  Catalog entry: (1.5, 0.75) has no measurable aggregate effect; per-symbol LDO
  variant (iter-v3/032) remains an open single-symbol candidate.

**PATH C — NEGATIVE**:
  OOS Sharpe < +1.57 (drops > 0.20 below iter-v3/040 anchor).
  Classification: NEGATIVE — universal (1.5, 0.75) broke OOS aggregate.
  Action: revert DEFAULT_ATR_MULTIPLIERS to (2.0, 1.0) at iter-v3/043.
  Catalog entry: universal barrier tightening FALSIFIED. Per-symbol LDO (1.5, 0.75)
  remains a possible future axis but requires re-evaluation vs the 4-symbol anchor.

**Pre-registered classification thresholds (locked before backtest)**:
- PATH A requires IS >= +0.89 AND OOS >= +1.57
- PATH B requires IS in [+0.59, +0.89] AND OOS >= +1.57
- PATH C requires OOS < +1.57

These thresholds are LOCKED and cannot be post-hoc renegotiated.

---

## Section 9 — Library Stack Declaration

All versions identical to iter-v3/041 / iter-v3/040 / iter-v3/028 reproducibility stamp.
No new libraries introduced.

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

**No mlfinlab/mlfinpy/pypbo/fracdiff dependencies.** v3 uses scipy + statsmodels
for all statistical tests (ADF, PBO, DSR, PSR). fracdiff (the package) is NOT used;
v3's FracdiffStat uses the custom implementation in `features_v3/fracdiff_v3.py`.
No library-unavailability fallbacks apply.
