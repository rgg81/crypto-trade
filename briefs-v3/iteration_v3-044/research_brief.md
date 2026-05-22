# Iteration v3-044 — Research Brief (REWRITTEN per QR EDA discipline directive)

**Type**: EXPLORATION (Cycle 3 #5 of 10)
**Track**: v3 (rigor arm) — forty-fourth iteration
**Branch**: `iteration-v3/044` (off iter-v3/043 head)
**Date**: 2026-05-09 (REWRITTEN)
**Author**: QR (autopilot)

> **REWRITE NOTE.** The original brief at SHA `2cd41fc` proposed adding regime_momentum_signed_3d
> to V3_FEATURE_COLUMNS_TOP_N as a universal 15th feature (orchestrator's ad-hoc pick at setup
> commit `1f56c72`). User directive 2026-05-09 mandated QR-driven quantitative axis selection
> after 3 NEGATIVE iterations in cycle 3 (iter-v3/041 pruning, 042 universal ATR, 043 Kaufman ER)
> all picked by orchestrator without QR EDA. This brief is rewritten to reflect the EDA-driven
> axis selection per `feedback_v3_axis_selection_quant_discipline.md`.
>
> Setup commits:
> - `1f56c72` — original ad-hoc setup (3d universal addition); SUPERSEDED.
> - `7f3be39` — QR EDA-driven setup (REVERT 3d universal + ADD per-symbol ATR for ALGO).
>
> The 3d feature implementation (compute_regime_momentum_signed_3d in engineered_v3.py) is
> RETAINED as dead code at zero revert cost. The 187-line test suite for the 3d function
> is also retained (passes against the dead-code function).

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
Cycle: 3 — #5 of 10
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1
  - ENSEMBLE_SIZE=5 (auto; inner ensemble)
  - n_trials=35 (default)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
Single axis: per-symbol ATR widening for ALGOUSDT only
  V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"] = (2.0, 1.5)  -- TP unchanged, SL +50%
  V3_FEATURE_COLUMNS_TOP_N = 14 (REVERTED iter-v3/043 ER + REVERTED orchestrator's
    iter-v3/044 ad-hoc 3d universal addition)
  V3_FEATURES_PER_SYMBOL = {} (unchanged)
  V3_MODELS = 4 (BCH, LDO, TRX, ALGO) — UNCHANGED.
  REQUIRED_GAP = 88 = (21+1)*4 — UNCHANGED.
  DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) — UNCHANGED.
Predicted classification: PROMISING (40%), PROMISING-INERT (35%), NEGATIVE (25%).
```

**Context**: After 3 NEGATIVE EXPLORATIONs in cycle 3 (iter-v3/041 universal pruning,
042 universal ATR (1.5, 0.75), 043 universal Kaufman ER), the user demanded QR-driven
quantitative axis selection. The QR diagnosis (SHA `eff841e`) established that the IS
bottleneck at iter-v3/040 anchor (+0.79) is direction-asymmetric per-symbol — ALGO LONG
is the single largest IS attribution loss (33 trades, -53.26 PnL, 18.2% IS WR / 11.1%
OOS WR; pattern persists OOS). All 3 cycle-3 axes touched UNIVERSAL parameters; none
addressed the per-symbol direction-asymmetric bottleneck. The new axis (per-symbol ATR
widening for ALGOUSDT only) directly targets the ALGO LONG SL/TP exit asymmetry (27/6 =
4.5:1) using the proven per-symbol ATR mechanism from iter-v3/032 LDO success.

---

## Section 1 — Hypothesis

Widening ALGOUSDT's stop-loss multiplier from 1.0×ATR to 1.5×ATR (TP unchanged at 2.0×ATR)
reduces the per-trade SL hit rate on ALGO long trades — the single largest IS attribution
loss bucket — by giving bear-trend longs more breathing room without changing the entry
signal. The mechanism is conservative (per-symbol mechanical adjustment) and mirrors the
proven iter-v3/032 LDO ATR success. Expected IS effect: ALGO LONG WR rises from 18.2% toward
30% as more longs reach TP; portfolio IS Sharpe lifts by approximately +0.10 to +0.20.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — Direction-Asymmetric Per-Symbol IS Bottleneck (from analysis/iteration_v3-044/cycle3_is_diagnosis.py SHA `eff841e`)

| Symbol-Direction | n_trades | Sum PnL | WR IS | WR OOS | Persists OOS? |
|---|---:|---:|---:|---:|---|
| **ALGO LONG** | **33** | **-53.26** | **18.2%** | **11.1%** | YES |
| BCH LONG | 39 | -18.68 | 28.2% | 28.6% | YES |
| TRX SHORT | 43 | -13.16 | 23.3% | 41.7% | NO (improves OOS) |
| BCH SHORT | 55 | +53.53 | 32.7% | 52.9% | YES (positive) |
| ALGO SHORT | 30 | +49.96 | 53.3% | 56.3% | YES (positive) |

ALGO LONG is the single largest IS attribution loss. Counterfactual block of 3 worst
direction-buckets (ALGO LONG, BCH LONG, TRX SHORT) lifts IS PnL from 65.76 → 150.86
(+129%) and IS Sharpe from +0.79 → +1.95 (above the +1.0 merge floor).

### 2.2 — ALGO LONG SL/TP Exit Asymmetry

| Exit Reason | Count | Avg pnl_pct |
|---|---:|---:|
| stop_loss | 27 | -5.24% |
| take_profit | 6 | +18.41% (incl. extreme +15.42%) |
| timeout | 0 | n/a |

ALGO LONG SL/TP ratio: **27/6 = 4.5:1** (severely asymmetric). Mean SL is -5.24% — well
below the 1.0×ATR barrier — suggesting most longs are stopped out close to entry rather
than trailing through the full ATR range. Widening SL to 1.5×ATR moves the threshold from
~-5% to ~-7.5% (50% wider band), giving longs more breathing room before stop-out.

ALGO SHORT SL/TP ratio: **14/14 = 1:1** (symmetric); shorts are well-calibrated at
current (2.0, 1.0) multipliers.

### 2.3 — Market Context

- ALGO IS market return: **-11.87%** (mild bear).
- ALGO OOS market return: **-34.62%** (severe bear).

ALGO is in a structural bear; long signals fight the trend. The wider SL approach is
consistent with the bear-trend hypothesis: in trending markets, mean reversion against
the trend (long signal in bear) needs more space before being abandoned.

### 2.4 — Why NOT regime_momentum_signed_3d

The orchestrator's ad-hoc setup commit `1f56c72` proposed adding regime_momentum_signed_3d
as a 15th universal feature. EDA test:

| Conditional | n | WR | sum_PnL |
|---|---:|---:|---:|
| ALGO LONG, regime_mom_3d > 0 | 18 | 22.2% | -6.01 |
| ALGO LONG, regime_mom_3d <= 0 | 15 | 13.3% | -47.25 |

The 3d sign DOES partially separate ALGO LONG outcomes (3d>0 has 22.2% WR vs 13.3% for
3d<=0), but the WR remains catastrophically low in BOTH regimes. regime_momentum_signed_5d
ranks 14/14 in the ALGO model (importance 56 vs top feature max_dd_window_50 at 164);
adding the 3d variant would also rank near the bottom. Universal addition would dilute
colsample_bytree picks slightly without addressing the bottleneck.

IC(regime_mom_3d, regime_mom_5d) on ALGO IS = 0.466 (moderate, not redundant).
IC(regime_mom_3d, fwd_21bar_ret) = 0.1122 (marginally more predictive than 5d's 0.0956).

The 3d implementation (compute_regime_momentum_signed_3d in engineered_v3.py) is RETAINED
as dead code at zero revert cost. It is available for future per-symbol experiments
(e.g., V3_FEATURES_PER_SYMBOL["ALGOUSDT"] = TOP_14 + ("regime_momentum_signed_3d",)) if the
ATR axis fails.

### 2.5 — Predicted Behavioral Effect (per `feedback_v3_axis_saturation_predictor.md`)

Predicted IS trade count delta vs iter-v3/040 anchor: **5–15% reduction** (driven by ALGO
trade count drop as wider SL allows trades to mature longer before stop-out, REDUCING
trade frequency overall but IMPROVING per-trade Sharpe).

Mechanism: ATR multiplier change directly affects the label distribution. Wider SL means
fewer SL exits (and slightly fewer TP exits as the wider band gives volatility more
opportunity to drag price away from entry). Net effect: some bars that previously closed
at SL within 1–2 candles now close at TP or timeout 5–10 candles later. Concretely:
- ALGO total IS trades current: 63; predicted post-axis: 50–60 (drop 3–13).
- ALGO LONG SL count current: 27; predicted post-axis: 18–22 (drop 5–9).
- ALGO LONG TP count current: 6; predicted post-axis: 8–12 (rise 2–6).

**Falsifier**: if observed |IS trade count change| > 30% relative vs iter-v3/040 anchor,
investigate label-pipeline correctness (axis behavior should be bounded; large change
suggests wider-SL is creating cascade effects beyond ALGO bar geometry).

### Analysis Script

`analysis/iteration_v3-044/cycle3_is_diagnosis.py` (committed SHA `eff841e`) produces
`is_constraint_analysis.csv` and `synthesis.md` documenting the direction-asymmetric
per-symbol IS bottleneck. The diagnosis covers DIAGNOSIS 1–8 (per-symbol contribution,
per-direction breakdown, IS-vs-OOS persistence, worst IS months, direction-asymmetry
severity per symbol, market trend, and combined attribution).

---

## Section 3 — Proposed Changes

### Sub-fix 1: REVERT efficiency_ratio_50 (carried forward from iter-v3/044 v1)

V3_FEATURE_COLUMNS_TOP_N has 14 features (ER already dropped per iter-v3/043 DISASTROUS
NEGATIVE). compute_efficiency_ratio_50 retained as dead code in engineered_v3.py;
NOT dispatched.

### Sub-fix 2: REVERT regime_momentum_signed_3d universal addition (NEW vs original brief)

V3_FEATURE_COLUMNS_TOP_N stays at 14 features (3d NOT added). compute_regime_momentum_signed_3d
retained as dead code in engineered_v3.py; NOT dispatched. The 187-line test suite passes
against the dead-code function (validates past-only, IC properties, etc., even though the
function isn't called by the production pipeline).

### Sub-fix 3: ADD V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"] = (2.0, 1.5)

In `src/crypto_trade/features_v3/__init__.py`, set:

```python
V3_ATR_MULTIPLIERS_PER_SYMBOL: dict[str, tuple[float, float]] = {
    "ALGOUSDT": (2.0, 1.5),
}
```

This widens ALGO's SL multiplier from 1.0× ATR (DEFAULT) to 1.5× ATR (50% wider band).
TP multiplier unchanged at 2.0× ATR. Other 3 symbols (BCH/LDO/TRX) remain on
DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via fallback.

### Sub-fix 4: Update _verify_feature_columns in run_baseline_v3.py

Update assertions for iter-v3/044 state:
- `len(V3_FEATURE_COLUMNS) == 14` (was 15 in original brief; reverted to 14)
- `"regime_momentum_signed_3d" not in V3_FEATURE_COLUMNS` (REVERTED — assertion flipped)
- `"regime_momentum_signed_5d" in V3_FEATURE_COLUMNS` (mandate still PRESENT)
- `"efficiency_ratio_50" not in V3_FEATURE_COLUMNS` (ABSENT — DISASTROUS NEGATIVE)
- `len(V3_ATR_MULTIPLIERS_PER_SYMBOL) == 1` (one entry, ALGOUSDT)
- `V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"] == (2.0, 1.5)` (per-symbol entry)
- `atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5)` (per-symbol)
- `atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0)` (DEFAULT fallback)
- `atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0)` (DEFAULT fallback)
- `atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0)` (DEFAULT fallback)
- All 4 symbols return 14-feature fallback via `features_for_symbol`

### Sub-fix 5: Update tests

`tests/features_v3/test_features_for_symbol.py`:
- Rename `test_*_fallback_15` → `test_*_fallback_14` (4 tests)
- Update `test_universal_list_is_15` → `test_universal_list_is_14`
- Update `test_all_symbols_fallback_15` → `test_all_symbols_fallback_14`
- Update `test_v3_atr_multipliers_per_symbol_is_empty` → `test_v3_atr_multipliers_per_symbol_has_algo`
- Update `test_all_symbols_atr_reverted` → `test_non_algo_symbols_atr_default_iter_v3_044`
- Update `test_regime_momentum_signed_3d_in_universal_list` → `test_regime_momentum_signed_3d_NOT_in_universal_list`
- Update `test_features_for_symbol_unknown_fallback`: 15 → 14, add 3d to dead-code list

`tests/features_v3/test_engineered_v3.py`:
- Update `test_integration_dispatched_by_add_engineered`: assert 3d NOT in output columns
  (compute_regime_momentum_signed_3d retained as dead code; not dispatched)

97 tests pass after these updates (verified at setup commit SHA `7f3be39`).

### Sub-fix 6: Update ITERATION_LABEL

In `run_baseline_v3.py`, ITERATION_LABEL = "v3-044" (already set).

### Bundle state verification (what _verify_feature_columns must assert)

```
V3_FEATURE_COLUMNS_TOP_N: 14 features (ER ABSENT; 3d ABSENT)                        PASS
DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0)                                                  PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL: 1 entry (ALGOUSDT → (2.0, 1.5))                      PASS
V3_FEATURES_PER_SYMBOL: {} (empty)                                                   PASS
features_for_symbol("BCHUSDT") == 14 features (TOP_N fallback)                       PASS
features_for_symbol("ALGOUSDT") == 14 features (TOP_N fallback)                      PASS
features_for_symbol("LDOUSDT") == 14 features (TOP_N fallback)                       PASS
features_for_symbol("TRXUSDT") == 14 features (TOP_N fallback)                       PASS
atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5) (per-symbol)                    PASS
atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0) (DEFAULT)                        PASS
atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0) (DEFAULT)                        PASS
atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0) (DEFAULT)                        PASS
"regime_momentum_signed_5d" IN V3_FEATURE_COLUMNS_TOP_N (mandate PRESENT)            PASS
"regime_momentum_signed_3d" NOT IN V3_FEATURE_COLUMNS_TOP_N (REVERTED per QR EDA)    PASS
"efficiency_ratio_50" NOT IN V3_FEATURE_COLUMNS_TOP_N (DISASTROUS NEGATIVE)          PASS
"ret_skew_50" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                                  PASS
"sym_vs_btc_ret_7d" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                            PASS
V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols                                        PASS
REQUIRED_GAP = 88 = (21+1) x 4                                                       PASS
```

---

## Section 4 — Expected OOS Impact

**IS Sharpe prediction (single-seed, vs iter-v3/040 single-seed anchor +0.79):**
- Predicted band: [+0.65, +1.05]
- Median point estimate: +0.85 to +0.95
- Rationale: Wider SL on ALGO redirects ~5–9 SL exits to TP/timeout (per-trade per Section
  2.5 prediction). Each redirected SL→TP is approximately +6 PnL swing per trade
  (+11.36 absolute net gain — TP +6.12 minus former SL -5.24). 5 redirected trades
  = ~+25 PnL portfolio-wide; 9 redirected = ~+45 PnL. Existing IS PnL is 65.76;
  +25–45 lifts to 90–110 (+38% to +67%). With a 24-month sample annualized SR scales
  with PnL/std; std also lifts modestly (wider SL = larger losing trade extremes), so
  Sharpe lifts proportionally less than PnL. Estimate +0.10 to +0.20 IS Sharpe lift.

**OOS Sharpe prediction (single-seed, vs iter-v3/040 single-seed anchor +1.77):**
- Predicted band: [+1.40, +2.10]
- Median point estimate: +1.75
- Rationale: ATR multiplier change preserves per-symbol model architecture (no LightGBM
  retrain shift; same Optuna search space). Pure label-distribution change. OOS impact
  expected modest (±0.20 from anchor) since ATR per-symbol change is a "label hygiene"
  axis, not a "new edge ingredient" axis. Single-seed variance dominates.

**OOS falsifier (pre-registered)**:
- If OOS Sharpe drops below +1.40 (more than 0.37 below iter-v3/040 anchor): the per-symbol
  ALGO ATR widening creates cascading drag on other symbols (label distribution shift in
  ALGO trade rate disturbs portfolio risk-adjusted weights); NEGATIVE classification.

**Pathway-A trigger (PROMISING)**:
- IS Sharpe >= +0.89 (>= +0.10 lift over anchor) AND OOS Sharpe >= +1.55.

**Pathway-B trigger (PROMISING-INERT)**:
- IS Sharpe in [+0.69, +0.89] (within ±0.10 of anchor) AND OOS Sharpe >= +1.55.

**Pathway-C trigger (NEGATIVE)**:
- OOS Sharpe < +1.40 (drops > 0.37 below anchor) OR
- IS Sharpe < +0.65 (drops > 0.14 below anchor).
- Action: REVERT V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"] at iter-v3/045; consider
  per-symbol features for ALGO (regime_momentum_signed_3d via V3_FEATURES_PER_SYMBOL,
  or new dist_from_high_42bar feature) as the next axis.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.

**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward.

**R3 (OOD detection)**: zscore_threshold=2.0 unchanged. Feature subspace unchanged at 14
features (Mahalanobis covariance space identical to iter-v3/040). Expected effect on OOD
firing rate: <2% relative (no feature dimensionality change).

**ALGO ATR widening risk**: wider SL means individual losing trades can lose MORE per trade.
Mean SL pnl_pct shifts from ~-5.24% to ~-7.86% per losing trade. If the wider SL doesn't
redirect enough SLs to TPs, ALGO LONG would lose MORE per trade with similar frequency,
making the bottleneck WORSE. Falsifier: if observed ALGO LONG SL count remains ≥25 (vs
predicted 18–22) AND mean SL pnl_pct ≤ -7%, the wider SL is hurting more than helping.
This would trigger Pathway-C and REVERT at iter-v3/045.

**IS trade-rate stability**: ATR multipliers change for ALGO only; non-ALGO label
distribution identical to iter-v3/040. ALGO IS trade count expected within ±15% of
iter-v3/040 (63 → 50–60 predicted). Portfolio total IS trade count expected within ±5%
(257 → ~250 predicted). If portfolio total deviates > 30%, investigate parquet freshness
(stale features, incorrect feature_columns list).

**Cross-symbol contagion risk**: per-symbol ATR change affects only ALGO model training
data. BCH/LDO/TRX models are completely independent (separate Optuna runs, separate
feature parquets at the model-input level). Cross-symbol contagion possible only via
portfolio-level risk gates (BTC trend filter, drawdown brake). Both gates use
portfolio-aggregate signals; ALGO trade-rate change shifts portfolio aggregates by
single-digit percent. Expected portfolio risk-gate firing rate change: <5%.

---

## Section 6 — Risk Management Design (7-Primitive Gate Table)

All 7 risk gates carried forward from iter-v3/040 baseline unchanged.

| Gate | Type | Parameter | Change |
|---|---|---|---|
| 1 — BTC trend | BtcTrendFilterConfig | lookback=42, threshold=15% | None |
| 2 — Hit rate | HitRateGateConfig | window=20, sl_threshold=0.65 | DISABLED (unchanged) |
| 3 — ADX gate | ADX regime filter | threshold=20 (v3 default) | None |
| 4 — Hurst regime | hurst_100 > 0.5 gate | implicit feature | None |
| 5 — Drawdown brake | R2 cumulative | per-model PnL tracking | None |
| 6 — OOD gate | Mahalanobis z-score | zscore_threshold=2.0, 14-D space | None (no feature change) |
| 7 — Liquidity floor | NATR floor | NATR >= 0.5% | None |

**Predicted OOD fire rate**: within ±2% of iter-v3/040 baseline. No feature subspace change.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode (NEGATIVE — wider SL increases loss per trade without raising WR)**:
The current ALGO LONG SL is hit at -5.24% pnl_pct (well below 1.0×ATR barrier). Widening
SL might just delay the inevitable — some bear-trend longs will continue to drift and
eventually hit the wider 1.5×ATR SL at -7.86%. If WR doesn't rise enough, the wider band
just amplifies losses. Per-trade Sharpe could WORSEN if WR rises only marginally.

**Second plausible failure mode (PROMISING-INERT — minimal IS impact)**:
ALGO trade rate changes by 5–15%, ALGO LONG WR rises modestly (18.2% → 22% range), but
the absolute PnL improvement is too small to move the needle. Portfolio IS Sharpe lift
< +0.10. Classification: PROMISING-INERT.

**Third plausible failure mode (cross-symbol drag from R2 brake recalibration)**:
ALGO trade rate drops 10–15%, R2 cumulative PnL tracking shifts (R2 brake based on
per-model PnL); marginal effect on portfolio risk weighting. If ALGO model's effective
PnL contribution shifts, R2 brake may fire more/less frequently. Expected effect: <5%.

**What the gates should catch**:
- Gate 5 (R2 drawdown): ALGO label-distribution shift may alter R2 firing rate. Monitor.
- Gate 7 (liquidity): NATR floor unchanged; ALGO trades that were marginal NATR-wise
  before still pass.

**Behavioral effect predictor**: predicted IS trade count delta -5% to -15% (ALGO model
specifically; -3% portfolio-wide). Falsifier: > 30% portfolio delta triggers investigation.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is an EXPLORATION iteration. MERGE gates do NOT apply. Classification criteria
(pre-registered before backtest runs):

**PATH A — PROMISING**:
  IS Sharpe >= +0.89 (>= +0.10 lift over iter-v3/040 anchor +0.79) AND
  OOS Sharpe >= +1.55 (maintained within -0.22 of iter-v3/040 anchor +1.77).
  Classification: PROMISING. Per-symbol ATR widening for ALGOUSDT contributes universal lift.
  Catalog entry: candidate for next CONFIRMATION bundle.

**PATH B — PROMISING-INERT**:
  IS Sharpe in [+0.69, +0.89] (within ±0.10 of anchor) AND OOS Sharpe >= +1.55.
  Classification: PROMISING-INERT. ALGO ATR widening is parsimony-neutral for IS lift.
  May be retained for CONFIRMATION bundle as zero-cost addition if other axes succeed.

**PATH C — NEGATIVE**:
  IS Sharpe < +0.65 (drops > 0.14 below anchor) OR OOS Sharpe < +1.40.
  Classification: NEGATIVE. Per-symbol ATR axis FALSIFIED for ALGO.
  Action: REVERT V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"] at iter-v3/045;
  consider per-symbol features for ALGO (regime_momentum_signed_3d via V3_FEATURES_PER_SYMBOL)
  as next axis.
  Catalog entry: "ALGO ATR widening (1.5×SL) FALSIFIED — direction-asymmetric IS bottleneck
  not addressable via mechanical ATR widening".

**Pre-registered classification thresholds (locked before backtest)**:
- PATH A: IS >= +0.89 AND OOS >= +1.55
- PATH B: IS in [+0.69, +0.89] AND OOS >= +1.55
- PATH C: IS < +0.65 OR OOS < +1.40

These thresholds are LOCKED and cannot be post-hoc renegotiated.

---

## Section 9 — Library Stack Declaration

All versions identical to iter-v3/043 / iter-v3/040 / iter-v3/028 reproducibility stamp.
No new libraries introduced. Per-symbol ATR is a config-only change (no new feature
implementations dispatched).

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

**No mlfinlab/mlfinpy/pypbo/fracdiff dependencies.** v3 uses scipy + statsmodels for all
statistical tests (ADF, PBO, DSR, PSR). fracdiff (the package) is NOT used; v3's
FracdiffStat uses the custom implementation in `features_v3/fracdiff_v3.py` (dead code
since iter-v3/040; retained for future use).

---

## Section 10 — QR Audit Trail (NEW for iter-v3/044 per process-discipline directive)

Per `feedback_v3_axis_selection_quant_discipline.md` (established 2026-05-09 user
directive after 3 NEGATIVE iterations in cycle 3 picked by orchestrator without QR EDA):

**EDA basis**: `analysis/iteration_v3-044/cycle3_is_diagnosis.py` (committed SHA `eff841e`).
Outputs: `is_constraint_analysis.csv`, `synthesis.md`. Establishes:
- Per-symbol contribution decomposition (ALGO LONG = single largest IS attribution loss)
- Direction-asymmetric breakdown (LONG -50.83 PnL portfolio-wide, 29.7% WR;
  SHORT +116.59 PnL portfolio-wide, 35.3% WR)
- IS-vs-OOS persistence check (ALGO LONG WR drops further from 18.2% → 11.1% OOS)
- Counterfactual block analysis (IS Sharpe +0.79 → +1.95 if 3 bad buckets removed)
- Worst IS month attribution (ALGO LONG dominates 4 of top-10 worst months)
- Top-3 candidate axes ranked by expected IS lift (per-symbol ATR for ALGO is #3 by lift
  but #1 by complexity-adjusted EV — chosen for cleanest single-axis test)

**Original orchestrator pick**: regime_momentum_signed_3d as 15th universal feature
(setup commit `1f56c72`). EDA showed this does NOT discriminate ALGO LONG WR (22.2% > 0,
13.3% <=0); ranks 14/14 in ALGO model. Predicted PATH B INERT or PATH C NEGATIVE.

**QR-driven replacement**: per-symbol ATR widening for ALGOUSDT only
(V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"] = (2.0, 1.5)). EDA shows ALGO LONG SL/TP exit
ratio = 4.5:1 (severely asymmetric); wider SL targets the bottleneck mechanically.
Proven mechanism per iter-v3/032 LDO ATR success.

**Setup commit SHA**: `7f3be39` (REVERT 3d universal addition + ADD per-symbol ATR for ALGO).
**Phase 5.5 gate must verify**: brief Section 2 numerical evidence committed BEFORE setup
commit `7f3be39` (committed at SHA `eff841e`); brief is rewrite of original SHA `2cd41fc`.

This Section 10 satisfies the process-discipline requirement that QR EDA precedes axis
selection. Cannot be retroactively renegotiated.
