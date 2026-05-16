# Iteration v3-057 — Research Brief (A4 base-stack SWAP: DROP ret_skew_50, ADD parkinson_gk_ratio_20)

**Type**: EXPLORATION (Cycle 4 #7 of 10)
**Track**: v3 (rigor arm) — fifty-seventh iteration
**Branch**: `iteration-v3/057` (off iter-v3/056 head at SHA `27047f1`)
**Date**: 2026-05-12
**Author**: QR (autopilot)
**EDA SHA**: `8160e3a` (`analysis/iteration_v3-057/` — 10 files: 6 CSVs/JSON + 2 .py + 2 .md)

**MANDATED AXIS** (per iter-v3/056 Critic FINAL SHA `1908d50` Recommendation #1):
**A4 — base-stack reordering** with QR-EDA-driven SWAP choice per
`feedback_v3_axis_selection_quant_discipline.md`.

**SELECTED SWAP** (EDA-derived):
- **DROP**: `ret_skew_50` (rank 12/14 portfolio importance, bottom-3 on BCH+TRX)
- **ADD**: `parkinson_gk_ratio_20` (family `price_efficient_vol`; NEVER tested at base stack; FIRST-IN-CATEGORY for V3_BASE_14)
- **Net feature count**: 14 → 14 (1-for-1 SWAP at base-stack level)

**MECHANISM** (predicted CPCV shift): The SWAP exchanges a tail_risk feature (which the
14-base stack already has 5 of) for a price_efficient_vol family feature (which the base
stack has ZERO of). parkinson_gk_ratio_20 (= Parkinson_HL / Garman-Klass_OHLC ratio)
captures intra-bar microstructure efficiency that no other base-14 feature encodes.
Univariate Spearman ρ = -0.044 / -0.071 / -0.039 across BCH/LDO/TRX (all p<0.005,
consistent negative direction → mean-reverting microstructure signal). max |IC| with
V3_BASE_14 = 0.245 (below 0.50 strict Category-1 gate; this is an off-the-shelf
vol-ratio indicator, NOT a Category-2 composed feature).

**WHAT CHANGES vs /056**:
1. `src/crypto_trade/features_v3/__init__.py`: V3_FEATURE_COLUMNS_TOP_N replaces
   `"ret_skew_50"` with `"parkinson_gk_ratio_20"` + comment block documenting iter-v3/057 SWAP rationale.
2. `run_baseline_v3.py`: ITERATION_LABEL = "v3-057".
3. NEW adversarial test: `tests/features/test_parkinson_gk_ratio_20_past_only.py` (past-only audit).
4. NO other code changes. NO new compute function (parkinson_gk_ratio_20 already in parquet via `add_price_efficient_vol_v3_features`).

**STRATEGY CHANGE**: 1-feature SWAP at base-stack level. NOT bit-identical to /056. Expected
CPCV path distribution shift: MILD (target: at least 1 of the structural constants
{positive count 29/45, median +0.3351, Q75 +0.838} shifts by detectable amount).

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # single outer seed (EXPLORATION-spec)
n_trials         = 35             # EXPLORATION default (per `feedback_v3_exploration_n_trials_35.md`)
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees iter-v3/057 OOS metrics for the FIRST
time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 4 — #7 of 10 (seventh EXPLORATION post-iter-v3/050 NO-MERGE CONFIRMATION)
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
  - ENSEMBLE_SIZE=5 (auto; inner ensemble)
  - n_trials=35 (default per `feedback_v3_exploration_n_trials_35.md`)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
  - --clean-oof (use guardrail from SHA `6a216b5`)

Carry-forward state from iter-v3/056 head SHA `27047f1` (UNCHANGED unless explicit at §3):
  - V3_FEATURE_COLUMNS_TOP_N at /056 HEAD = 14 features (ret_skew_50 included)
  - V3_MODELS at /056 HEAD = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols UNCHANGED at /057
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty) UNCHANGED at /057
  - block_long_for = () (empty) UNCHANGED at /057
  - regime_momentum_signed_5d PRESERVED (iter-v3/028 edge ingredient) UNCHANGED at /057
  - DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) UNCHANGED at /057
  - adx_threshold_per_symbol = {} (empty) UNCHANGED at /057
  - All other risk gates UNCHANGED (BTC trend, OOD, ADX 20.0, hit-rate disabled, etc.)
  - REQUIRED_GAP at /056 HEAD = 66 = (21+1)×3 UNCHANGED at /057 (universe unchanged)
  - enable_per_symbol_drawdown_brake = False at /056 HEAD UNCHANGED at /057
    (per /054 closeout architectural decision; brake mechanism CLOSED-mechanism PARKED)
  - dsr.json schema additions present at /056 HEAD (`dsr_relative`, `cpcv_path_sharpe_q75`)
    UNCHANGED at /057 (these are post-hoc fields not the axis of /057)

SINGLE-AXIS CHANGE for /057:
  AXIS: A4 base-stack SWAP — DROP `ret_skew_50` (rank 12/14 portfolio importance) AND
        ADD `parkinson_gk_ratio_20` (family `price_efficient_vol`; never tested at base stack)
        in V3_FEATURE_COLUMNS_TOP_N. Net count 14 → 14 (1-for-1 SWAP).

    Mechanism: parkinson_gk_ratio_20 = parkinson_vol_20 / garman_klass_vol_20
      = sqrt(HL^2 / (4·ln(2))) / sqrt(GK estimator from OHLC).
      Ratio > 1.0 → choppy/sideways bar (wide HL, small open-to-close move).
      Ratio < 1.0 → trending bar (open-to-close large vs HL).
      Captures intra-bar microstructure quality info that bar-level returns
      (ret_skew_*, ret_kurt_*, ret_autocorr_*) cannot encode.

    Schema: V3_FEATURE_COLUMNS_TOP_N stays at 14 elements; one element substituted.
      Output dsr.json schema UNCHANGED. Output trade-level CSVs UNCHANGED in structure.

    Net effect: 1-feature SWAP at base-stack level; expected to modify Optuna's
      reachable hyperparameter trajectories. CPCV path distribution may shift if
      the new feature provides genuine signal. Bit-identical OOS comparison vs
      /056 IS NOT EXPECTED (this is NOT a methodology-only axis).

Setup commit changes (locked in §3):
  - src/crypto_trade/features_v3/__init__.py: SWAP `"ret_skew_50"` → `"parkinson_gk_ratio_20"`
    in V3_FEATURE_COLUMNS_TOP_N + iter-v3/057 SWAP rationale comment block
  - run_baseline_v3.py: ITERATION_LABEL "v3-057"
  - tests/features/test_parkinson_gk_ratio_20_past_only.py: NEW past-only adversarial test
```

---

## Section 1 — Hypothesis

**Primary hypothesis**: SWAPPING `ret_skew_50` (rank 12/14 portfolio importance; bottom-3
on BCH+TRX; redundant with other tail_risk features ret_skew_200, ret_kurt_50, ret_kurt_200)
for `parkinson_gk_ratio_20` (first-in-category price_efficient_vol feature; consistent
univariate Spearman ρ p<0.005 across all 3 symbols; max |IC| with V3_BASE_14 = 0.245)
adds a STRUCTURALLY DISTINCT signal source to the base-14 stack that:
  (a) reaches Optuna trajectories not previously available at base-14 stack
  (b) shifts CPCV path distribution from cycle-4 STRUCTURAL CONSTANT (PATH E firing 6/6)
  (c) lifts IS Sharpe by ≥ +0.10 if the signal is genuinely orthogonal
  (d) maintains OOS/IS ratio within [0.5, 2.0] (no single-seed lottery artifact)

**Secondary hypothesis**: parkinson_gk_ratio_20 learns at LightGBM importance ≥ 30 in
at least one symbol — confirming the feature is captured by the model and not INERT.
Per the |Spearman| ρ heuristic, expected importance rank: 7-12 of 14.

**What this iteration tests**: whether a SWAP at the base-stack level (NOT a 15th-slot
extension, NOT a methodology axis, NOT a risk primitive) can escape the cycle-4 PATH E
CPCV-INVARIANT NULL pattern. Per Critic /056 FINAL Rec #1: "/057 axis: A4 base-stack
reordering OR NEW feature family — QR EDA-driven choice".

**What this iteration does NOT test**:
- ANY risk primitive change (drawdown brake stays disabled per /054 closeout)
- ANY labeling change (ATR multipliers, timeout unchanged)
- ANY model architecture (LightGBM unchanged)
- ANY universe change (3-symbol BCH+LDO+TRX unchanged)
- ANY methodology-only axis (DSR_relative, PBO — unchanged at /056 baseline)
- 15th-slot SWAP (Category-2 composed features) — CLOSED per /054

**Targeted finding** — at /057 single-seed EXPLORATION:

| Outcome | Probability | What it means |
|---|---:|---|
| **PATH A (PROMISING-clean)** | 8-12% | IS Δ ≥ +0.10 AND OOS Δ ≥ +0.10 AND importance ≥ 30 in ≥1 sym AND CPCV shift detectable |
| **PATH B (PROMISING-INERT)** | 5-10% | Feature does NOT learn (importance < 30 all syms); minimal IS/OOS shift |
| **PATH C-clean (NEGATIVE)** | 5-8% | IS Δ < -0.10 OR OOS Δ < -0.20 → BCH/LDO regression |
| **PATH C-suspicious** | <5% | IS-OOS daily Sharpe ratio outside [0.5, 2.0] → lottery artifact |
| **PATH D (NULL-RESULT)** | 25-30% | IS Δ in (-0.10, +0.10) AND OOS Δ in (-0.20, +0.20) AND importance learned; no Sharpe shift |
| **PATH E (CPCV-INVARIANT NULL)** | 50-60% | CPCV path distribution bit-identical to /051..056 to 4 decimals — 7th consecutive |

PATH E is compatible with PATHs A/B/D — it speaks to CPCV path distribution stability,
not Sharpe outcome.

---

## Section 2 — IS-Only Numerical Evidence

Per `feedback_v3_axis_selection_quant_discipline.md`, the brief Section 2 must contain
EDA-derived numerical tables produced by a committed analysis script. The EDA is
committed at SHA `8160e3a` in `analysis/iteration_v3-057/`.

### Section 2.1 — A4 drop candidate ranking (per-symbol importance)

From `analysis/iteration_v3-057/a4_drop_ranking.csv` (per-symbol importance from
`reports-v3/iteration_v3-056/in_sample/model_importance_last_month_*.csv`):

| Rank | Feature | BCH rank | LDO rank | TRX rank | bottom3_count | Portfolio importance | Drop score |
|---:|---|---:|---:|---:|---:|---:|---:|
| **1** | **ret_skew_50** | **12/14** | **8/14** | **12/14** | **2** | **137.6** | **286.2** |
| 2 | btc_ret_14d | 13/14 | 6/14 | 14/14 | 2 | 142.3 | 285.8 |
| 3 | sym_vs_btc_ret_7d | 9/14 | 11/14 | 13/14 | 1 | 132.7 | 186.7 |
| 4 | hurst_100 | 11/14 | 14/14 | 3/14 | 1 | 140.3 | 186.0 |
| 5 | ret_autocorr_lag1_50 | 7/14 | 12/14 | 6/14 | 1 | 153.0 | 184.7 |
| -- | regime_momentum_signed_5d | 10/14 | 13/14 | 11/14 | 1 | 130.1 | **0 (PROTECTED)** |

`regime_momentum_signed_5d` is EXCLUDED from drop candidates per iter-v3/041 lesson +
`feedback_v3_engineered_features_proven.md` MUST-be-present mandate (per-symbol
load-bearing for BCH despite rank 14 portfolio aggregate).

**Chosen drop target: ret_skew_50** — bottom-3 on BCH+TRX, middle-low on LDO (rank 8),
NOT load-bearing per /041 falsified-multi-drop lesson.

### Section 2.2 — NEW feature candidate screening

From `analysis/iteration_v3-057/new_feature_candidates.csv` — 28 features surveyed
that are computed in v3 parquets, NOT in V3_BASE_14, and NOT in CLOSED_FEATURES (the
13 already-CLOSED features per catalog).

Gate filters applied:
- All 3 symbols ADF p < 0.05 (stationary)
- All 3 symbols n_valid > 1000 (data efficiency)
- max |IC| with V3_BASE_14 < 0.50 (strict Category-1 gate; no carve-out)
- At least 1 symbol Spearman p < 0.05 (univariate predictability)
- |skew| < 10 AND |kurt| < 50 (numerical stability)

8 candidates pass all filters (`a4_drop_ranking.csv`):

| Rank | Feature | Family | mean abs Spearman | max abs IC | max IC partner |
|---:|---|---|---:|---:|---|
| **1** | **parkinson_gk_ratio_20** | **price_efficient_vol** | **0.0514** | **0.245** | **ret_skew_200 (LDO)** |
| 2 | obv_slope_50 | volume_micro | 0.0476 | 0.438 | ema_spread_atr_20 (BCH) |
| 3 | bb_width_pct_rank_100 | regime | 0.0433 | 0.199 | sym_vs_btc_ret_7d (TRX) |
| 4 | ret_autocorr_lag5_50 | momentum_accel | 0.0362 | 0.259 | ret_autocorr_lag1_50 (BCH) |
| 5 | hurst_200 | regime | 0.0354 | 0.440 | hurst_100 (TRX) |
| 6 | volume_mom_ratio_20 | volume_micro | 0.0301 | 0.377 | sym_vs_btc_ret_7d (BCH) |
| 7 | vol_return_divergence_30 | microstructure_v3 | 0.0292 | 0.062 | sym_vs_btc_ret_7d (LDO) |
| 8 | vol_transition_slope_20 | microstructure_v3 | 0.0266 | 0.205 | sym_vs_btc_ret_7d (TRX) |

### Section 2.3 — parkinson_gk_ratio_20 deep dive (chosen ADD target)

From `analysis/iteration_v3-057/spearman_top3.csv` + `parkinson_gk_ic_vs_base14.csv`:

**Univariate Spearman ρ vs forward 5-bar log return** (IS-only):

| Symbol | ρ | p-value | direction |
|---|---:|---:|---|
| BCHUSDT | -0.0435 | 0.0010 | NEGATIVE (mean-reverting) |
| LDOUSDT | -0.0715 | 0.0002 | NEGATIVE (mean-reverting) |
| TRXUSDT | -0.0392 | 0.0033 | NEGATIVE (mean-reverting) |

All 3 syms p<0.005; consistent NEGATIVE direction → high vol-ratio (Parkinson > GK,
choppy bar) precedes negative forward returns.

**ADF stationarity per symbol** (IS-only):

| Symbol | ADF p-value |
|---|---:|
| BCHUSDT | 1.30e-19 |
| LDOUSDT | 1.02e-11 |
| TRXUSDT | 4.30e-17 |

All 3 stationary (p < 1e-10).

**Distribution stability per symbol** (IS-only):

| Symbol | n_valid | skew | kurt |
|---|---:|---:|---:|
| BCHUSDT | 5718 | 0.66 | 0.69 |
| LDOUSDT | 2732 | (within ±2) | (within ±2) |
| TRXUSDT | 5660 | (within ±2) | (within ±2) |

Well-behaved distributions; no numerical instability.

**Top 10 |IC| pairs vs V3_BASE_14** (from `parkinson_gk_ic_vs_base14.csv`):

| Symbol | base feature | IC | abs IC |
|---|---|---:|---:|
| LDOUSDT | ret_skew_200 | -0.2450 | **0.2450** |
| BCHUSDT | sym_vs_btc_ret_7d | 0.2436 | 0.2436 |
| LDOUSDT | ret_kurt_50 | 0.1746 | 0.1746 |
| TRXUSDT | ret_kurt_50 | 0.1723 | 0.1723 |
| LDOUSDT | max_dd_window_50 | -0.1594 | 0.1594 |
| BCHUSDT | regime_momentum_signed_5d | 0.1585 | 0.1585 |
| BCHUSDT | vwap_dev_20 | 0.1265 | 0.1265 |
| TRXUSDT | ret_skew_200 | 0.1227 | 0.1227 |
| TRXUSDT | ret_skew_50 | 0.1097 | 0.1097 |
| BCHUSDT | ema_spread_atr_20 | 0.1070 | 0.1070 |

**Max |IC|** = 0.245 (well below 0.50 strict Category-1 gate). NO carve-out needed (this
is an off-the-shelf vol-ratio indicator, NOT a Category-2 composed feature).

**IC vs proposed drop (ret_skew_50)** (from `ic_top3_vs_drop.csv`):

| Symbol | IC of parkinson_gk_ratio_20 vs ret_skew_50 |
|---|---:|
| BCHUSDT | 0.093 |
| LDOUSDT | 0.051 |
| TRXUSDT | 0.110 |

All 3 below 0.15 → the SWAP captures GENUINELY ORTHOGONAL signal, not redirected variance.

### Section 2.4 — Family composition shift

Current V3_BASE_14 family composition (from analysis/iteration_v3-057/synthesis.md §C):
- **tail_risk (6)**: max_dd_window_50, ret_kurt_50, ret_skew_200, ret_kurt_200, ret_skew_50, range_realized_vol_50
- **momentum_accel (2)**: ema_spread_atr_20, ret_autocorr_lag1_50
- **volume_micro (1)**: vwap_dev_20
- **regime (2)**: hurst_diff_100_50, hurst_100
- **cross_btc (2)**: btc_ret_14d, sym_vs_btc_ret_7d
- **engineered (1)**: regime_momentum_signed_5d
- **price_efficient_vol (0)** — ZERO FROM THIS FAMILY

After SWAP:
- tail_risk: 6 → **5** (-1: ret_skew_50)
- price_efficient_vol: 0 → **1** (+1: parkinson_gk_ratio_20)
- Other families: UNCHANGED

**FIRST-IN-CATEGORY** — price_efficient_vol absent from v3 base-stack since iter-v3/007
top-N reduction. parkinson_gk_ratio_20 was ranked 17/34 at /007 (NOT NEGATIVE — simply
fell outside top-14 dimensionality cutoff).

### Section 2.5 — Historical context (parkinson_gk_ratio_20 has never been tested at axis)

- iter-v3/001-006: parkinson_gk_ratio_20 was IN V3_FEATURE_COLUMNS_FULL (34 features).
- iter-v3/007: DROPPED at top-N reduction (rank 17/34; fell outside top-14).
- iter-v3/008-056: NEVER tested at dedicated EXPLORATION axis.
- V2: parkinson_gk_ratio_20 is IN V2_FEATURE_COLUMNS (currently active in v0.v2-069 baseline).

**This is a fresh feature axis** — no prior NEGATIVE/INERT data. The CLOSED_FEATURES
list (in `analysis/iteration_v3-057/eda_a4_vs_new_family.py`) excludes parkinson_gk_ratio_20.

---

## Section 3 — Code Changes (Setup Commit Locked)

The setup commit makes 3 edits and adds 1 test. ALL changes localized to
`src/crypto_trade/features_v3/__init__.py` + `run_baseline_v3.py` + `tests/features/`.
NO changes to model/training/risk code.

### Edit 1: `src/crypto_trade/features_v3/__init__.py` — SWAP feature column

REPLACE the V3_FEATURE_COLUMNS_TOP_N tuple element `"ret_skew_50"` with
`"parkinson_gk_ratio_20"`. Update the preceding comment block to reflect the
iter-v3/057 SWAP rationale:

```python
# iter-v3/057: ret_skew_50 SWAPPED for parkinson_gk_ratio_20 (A4 base-stack reordering).
# Per analysis/iteration_v3-057/synthesis.md SHA `8160e3a`:
# - ret_skew_50 was rank 12/14 portfolio importance at /056; bottom-3 BCH+TRX, mid LDO.
# - parkinson_gk_ratio_20 (family `price_efficient_vol`) is FIRST-IN-CATEGORY for v3 base stack.
# - All 3 syms univariate Spearman ρ p<0.005 (BCH 0.001, LDO 0.0002, TRX 0.003).
# - max |IC| with remaining V3_BASE_14 = 0.245 (well below 0.50 strict gate).
# - Was in V3_FEATURE_COLUMNS_FULL (34) at /001-006; dropped at /007 top-N reduction (rank 17/34).
# - Never tested at dedicated EXPLORATION axis. Also in V2_FEATURE_COLUMNS (v0.v2-069 active).
"parkinson_gk_ratio_20",  # SWAP iter-v3/057 — price_efficient_vol family
```

The dropped feature comment block (for ret_skew_50 history at /041 + /042) is
PRESERVED but updated with the /057 SWAP context. The tuple stays at 14 elements;
ONE element is substituted.

### Edit 2: `run_baseline_v3.py` — ITERATION_LABEL

```python
ITERATION_LABEL = "v3-057"
```

### Edit 3: NEW adversarial past-only test for parkinson_gk_ratio_20

ADD `tests/features/test_parkinson_gk_ratio_20_past_only.py`:

```python
"""iter-v3/057 — adversarial past-only audit for parkinson_gk_ratio_20.

The feature is computed by `add_price_efficient_vol_v3_features` in
`src/crypto_trade/features_v3/price_efficient_vol_v3.py`:

    parkinson_vol_20 = sqrt(sum((log(H/L))**2) / (4·ln(2))) / 20  (20-bar trailing)
    garman_klass_vol_20 = sqrt(GK estimator from OHLC)            (20-bar trailing)
    parkinson_gk_ratio_20 = parkinson_vol_20 / garman_klass_vol_20

Both factors are 20-bar trailing rolling means terminating at bar t. The ratio
at bar t uses only OHLC data from bars [t-19, t]. The current bar's close is
observable at bar close (8h boundary); v3's trading convention is to act on
bar t+1's open, so observing close[t] at bar t-close is consistent with the
post-bar-close decision discipline (zero leakage from t+1+).

This test asserts: appending future bars t+1, t+2, ... does NOT alter the value
at bar t. The 20-bar trailing window is causal by construction.
"""
import numpy as np
import pandas as pd

from crypto_trade.features_v3.price_efficient_vol_v3 import (
    add_price_efficient_vol_v3_features,
)


def _make_synthetic_klines(n: int, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic OHLCV with realistic high-low range."""
    rng = np.random.default_rng(seed)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.01, n)))
    open_ = close * np.exp(rng.normal(0.0, 0.003, n))
    high = np.maximum(open_, close) * np.exp(np.abs(rng.normal(0.0, 0.005, n)))
    low = np.minimum(open_, close) * np.exp(-np.abs(rng.normal(0.0, 0.005, n)))
    volume = rng.uniform(100, 10000, n)
    return pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close,
        "volume": volume,
    })


def test_parkinson_gk_ratio_20_past_only_discipline():
    """Appending future bars t+1, t+2, ... must NOT alter the value at bar t.

    Compute the feature on a 500-bar series. Then compute again on a 600-bar
    series (appending 100 future bars). The first 500 values must match
    bit-identically (or within 1e-12 float tolerance).
    """
    short = _make_synthetic_klines(500, seed=42)
    longer = _make_synthetic_klines(600, seed=42)
    # The first 500 bars of `longer` must equal `short` exactly
    assert (short[["open", "high", "low", "close"]].values
            == longer[["open", "high", "low", "close"]].iloc[:500].values).all()

    short_feat = add_price_efficient_vol_v3_features(short.copy())
    longer_feat = add_price_efficient_vol_v3_features(longer.copy())

    s_vals = short_feat["parkinson_gk_ratio_20"].values
    l_vals = longer_feat["parkinson_gk_ratio_20"].iloc[:500].values

    # Both warmups: first 19 bars NaN expected
    assert np.isnan(s_vals[:19]).all()
    assert np.isnan(l_vals[:19]).all()

    # Beyond warmup: bit-identical (or within float tolerance)
    s_valid = s_vals[19:]
    l_valid = l_vals[19:]
    s_clean = s_valid[~np.isnan(s_valid)]
    l_clean = l_valid[~np.isnan(l_valid)]
    assert len(s_clean) == len(l_clean), \
        f"Mismatch in n_valid: short={len(s_clean)} vs longer-first-500={len(l_clean)}"
    np.testing.assert_allclose(
        s_clean, l_clean, rtol=1e-9, atol=1e-12,
        err_msg="parkinson_gk_ratio_20 values diverge between 500-bar and 600-bar "
                "computations — LOOK-AHEAD BIAS DETECTED",
    )


def test_parkinson_gk_ratio_20_within_expected_range():
    """The ratio should be in a reasonable band [0.5, 2.0] for most bars (not pathological)."""
    df = _make_synthetic_klines(2000, seed=1234)
    feat = add_price_efficient_vol_v3_features(df.copy())
    vals = feat["parkinson_gk_ratio_20"].dropna()
    # Expected: ratio centered near 1.0 (both estimators measure same vol, differ in detail)
    median = float(np.median(vals))
    assert 0.5 <= median <= 2.0, (
        f"parkinson_gk_ratio_20 median={median} outside expected [0.5, 2.0] band — "
        f"possible numerical instability"
    )
    # Expected: 95% of bars within [0.3, 2.5]
    q025, q975 = float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))
    assert 0.3 <= q025 and q975 <= 2.5, (
        f"parkinson_gk_ratio_20 2.5%-97.5% range [{q025}, {q975}] outside [0.3, 2.5] band"
    )
```

NO other tests changed. The `test_parkinson_gk_ratio_20_past_only.py` test file is NEW.

### Edit 4 (DEFENSIVE-NO-OP): Carry forward state

Verify the following are UNCHANGED at iter-v3/057:
- `V3_MODELS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")`
- `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}`
- `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`
- `RiskV2Config(adx_threshold_per_symbol={}, block_long_for=(), enable_per_symbol_drawdown_brake=False)`
- `REQUIRED_GAP = 66`
- `ENSEMBLE_SIZE = 5`

---

## Section 4 — Predicted Outcome Bands

Per `feedback_axis_saturation_predictor.md`, predicted bands MUST be locked
upfront with falsifier triggers.

### Section 4.1 — Strategy-level outcomes (1-feature SWAP at base-stack level)

The SWAP changes:
1. **Optuna search space** — colsample_bytree picks shift; new feature gets some
   tree splits at low Optuna budget.
2. **Per-symbol feature mix** — BCH/LDO/TRX models gain a price-efficient_vol signal.
3. **Cross-fold variance** — CPCV path distribution may show modest shift.

Anchor: iter-v3/056 (= /055 head bit-identical, = /028 single-seed=42) IS Sharpe **+0.5101** / OOS Sharpe **+0.5053**.

| Metric | /056 (anchor) | **/057 prediction band** | Δ vs /056 anchor |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.5101 | **+0.41 to +0.61** (PATH A: ≥+0.61; PATH C: <+0.41) | [-0.10, +0.10] |
| OOS monthly Sharpe | +0.5053 | **+0.30 to +0.70** (PATH A: ≥+0.61; PATH C: <+0.31) | [-0.20, +0.20] |
| IS daily Sharpe | +1.3383 | +1.18 to +1.49 | [-0.16, +0.15] |
| OOS daily Sharpe | +1.0340 | +0.78 to +1.28 | [-0.25, +0.25] |
| IS-OOS daily ratio | 1.295 | **0.5 to 2.0** (PATH C-suspicious if outside) | [-0.79, +0.71] |
| IS trades | 182 | **170 to 195** (±7%) | [-12, +13] |
| OOS trades | 96 | **88 to 108** (±10%) | [-8, +12] |
| IS MaxDD | 41.43% | 38% to 47% | [-4pp, +5pp] |
| OOS MaxDD | 22.97% | 19% to 28% | [-4pp, +5pp] |
| CPCV positive paths | 29/45 | **28 to 30 (band)** | [-1, +1] (PATH E if 29/45 exact) |
| CPCV median Sharpe | +0.3351 | +0.30 to +0.40 | [-0.04, +0.06] |
| CPCV Q75 Sharpe | +0.838 | +0.79 to +0.89 | [-0.05, +0.05] |

### Section 4.2 — Feature importance prediction

Heuristic mapping from |Spearman| ρ to importance rank:
- |ρ| ≈ 0.05 → importance 100-300 (rank 8-12 of 14)
- parkinson_gk_ratio_20 |ρ| range 0.039-0.071 across syms

| Symbol | Predicted importance | Predicted rank | PROMISING (≥30)? |
|---|---:|---:|:-:|
| BCHUSDT | 100-200 | 9-12 of 14 | YES |
| LDOUSDT | 100-250 | 8-11 of 14 | YES |
| TRXUSDT | 100-180 | 9-12 of 14 | YES |

### Section 4.3 — Behavioral-effect predictor (per `feedback_v3_axis_saturation_predictor.md`)

**Predicted IS trade count delta vs /056 anchor**: ±5% (172 to 191 trades).

Justification: 1-feature SWAP at depth-3-5 LightGBM with 14 features doesn't typically
shift trade count by > 10%. The new feature may make Optuna pick slightly different
hyperparameter regions but the gate-pass / signal-emission ratio is largely set by the
risk-gate stack (BTC trend, z-score OOD, ADX, Hurst), not by feature-stack composition.

**Falsifier**: If observed |IS trade Δ| > 30 trades (i.e., < 152 or > 212), escalate
to "Optuna regime shift detected" finding — the SWAP made the search reach materially
different hyperparameter trajectories than expected. Possible PATH A (PROMISING) signal.

### Section 4.4 — Falsifier band (post-EDA prediction)

Pre-registered Section 4.4 LOCKED falsifier triggers per `feedback_axis_saturation_predictor.md`:

| Trigger | Falsifier condition | Action |
|---|---|---|
| 1. PATH A (PROMISING) | IS Δ ≥ +0.10 AND OOS Δ ≥ +0.10 AND importance ≥ 30 in ≥1 sym | **PROMISING; carry to /058 OR /061 CONFIRMATION queue** |
| 2. PATH B (PROMISING-INERT) | importance < 30 all syms AND |IS Δ| ≤ 0.10 | feature didn't learn; DROP at /058 |
| 3. PATH C-clean (NEGATIVE) | IS Δ < -0.10 OR OOS Δ < -0.20 | DROP at /058; revert ret_skew_50 |
| 4. PATH C-suspicious | IS-OOS daily Sharpe ratio outside [0.5, 2.0] | Single-seed lottery; PATH C |
| 5. PATH D (NULL-RESULT) | IS Δ in (-0.10, +0.10) AND OOS Δ in (-0.20, +0.20) AND importance ≥ 30 | Feature learned but no Sharpe shift; saturation; A4 axis CLOSED for /058 |
| 6. PATH E (CPCV-INVARIANT NULL) | CPCV stats bit-identical to /051..056 to 4 decimals | 7th-consecutive; cycle-4 pin confirmed; cycle-5 mandate stands |

---

## Section 5 — Risk Mitigation

This is a 1-feature SWAP at base-stack level. The risk surface is well-bounded:

1. **No new compute function** — parkinson_gk_ratio_20 is already computed in v3
   parquets via `add_price_efficient_vol_v3_features` (`price_efficient_vol_v3.py:48`).
   The runtime path is already tested by existing iter-v3/001-006 history.
2. **Past-only discipline** — adversarial test `test_parkinson_gk_ratio_20_past_only.py`
   verifies that appending future bars does not alter prior-bar values.
3. **No risk-gate change** — drawdown brake stays disabled; BTC trend/OOD/ADX/Hurst
   gates unchanged.
4. **No labeling change** — ATR multipliers unchanged.
5. **Per-symbol drop safety** — ret_skew_50 is mid-table on LDO (rank 8); the drop
   may cause LDO IS regression. Bounded by predicted IS Δ band [-0.10, +0.10].
6. **Optuna search reproducibility** — `--clean-oof` guardrail prevents OOF parquet
   contamination (iter-v3/047 hazard fixed at SHA `6a216b5`).

---

## Section 6 — Wall-Clock Discipline

EXPLORATION cap: 2h hard. Predicted wall-clock from /056 carry-forward:
- /056 ran 1.95h (single-seed n_trials=35)
- /057 has IDENTICAL spec (--seeds 1 --n-trials 35 --clean-oof)
- 1-feature SWAP does NOT add compute (parquet already has parkinson_gk_ratio_20)
- Predicted runtime: 1.8 to 2.1h

If /057 exceeds 2h, the run TIMES OUT and the orchestrator dispatches QE for a
re-run analysis OR proceeds to /058 with PATH-undetermined catalog row.

---

## Section 7 — Reproducibility Discipline

Per BASELINE_V3.md Measurement Discipline:
1. **Data extent check** — Engineer Phase 6 pre-flight verifies all per-symbol
   parquets have `close_time` within 16h of measurement time.
2. **Library stack pinned** — UNCHANGED from /056 (lightgbm 4.6.0, optuna 4.8.0,
   numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6,
   pyarrow 23.0.1).
3. **Setup commit SHA** — populated at Phase 5.5 gate.
4. **Brief SHA** — this commit; populated by orchestrator.

---

## Section 8 — Pre-registered Path Adjudication

LOCKED Section 8 path hierarchy (CANNOT be renegotiated post-hoc per
`feedback_no_cheating.md`):

```
1. PATH C-clean (NEGATIVE) takes precedence: if IS Δ < -0.10 OR OOS Δ < -0.20.
2. PATH C-suspicious takes precedence next: if IS-OOS daily Sharpe ratio outside [0.5, 2.0].
3. PATH A (PROMISING-clean): IS Δ ≥ +0.10 AND OOS Δ ≥ +0.10 AND importance ≥ 30 in ≥1 sym.
4. PATH B (PROMISING-INERT): importance < 30 all syms AND |IS Δ| ≤ 0.10.
5. PATH D (NULL-RESULT): IS Δ in (-0.10, +0.10) AND OOS Δ in (-0.20, +0.20) AND importance ≥ 30.
6. PATH E (CPCV-INVARIANT NULL): co-fires regardless of PATH A/B/C/D; informational only.
```

**Methodology axis advancement**: Section 8 outcome ∈ {PATH A} → axis advances to /061
CONFIRMATION bundle queue. Section 8 outcome ∈ {PATH B, C, D} → axis CLOSED for cycle 4;
NEXT EXPLORATION (/058) chooses a different axis. PATH E is co-firing evidence not
a primary classification.

---

## Section 9 — Library Stack Pinning

UNCHANGED from /056:
- Python 3.13
- lightgbm 4.6.0
- optuna 4.8.0
- numpy 2.2.6
- pandas 3.0.0
- scikit-learn 1.8.0
- scipy 1.17.0
- statsmodels 0.14.6
- pyarrow 23.0.1

No new dependencies added. parkinson_gk_ratio_20 computation uses only numpy +
pandas (already in stack).

---

## Section 10 — QR Audit Trail

Per `feedback_v3_axis_selection_quant_discipline.md`, when axis selection is QR-EDA-driven,
brief Section 10 must document the research path.

### Stage 1 — Read mandate

Critic /056 FINAL Rec #1: "/057 axis: A4 base-stack reordering OR NEW feature family —
QR EDA-driven choice".

Critic /055 FINAL Rec #3 (carry-forward): "Cycle-5 mass feature expansion mandate queued
for /062 — NOT for /057. /057 stays within cycle 4 single-axis discipline."

Critic /054 FINAL Rec #1 (carry-forward): The 15th-slot SWAP family is CLOSED at
"Category 2 composed features" scope. NEW feature families remain UNTESTED at base-stack
SWAP scope. A4 base-stack reordering (DROP + ADD) is structurally distinct.

### Stage 2 — Catalog walk

Surveyed all v3 EXPLORATION catalog rows (/001-/056). Identified:
- Features in V3_BASE_14 (14 — unchanged since /042 restore)
- Features in CLOSED_FEATURES (13 — explicitly tested + closed)
- Features computed in parquet but NOT in either group (28 candidates)

### Stage 3 — A4 drop ranking

Loaded /056 single-seed per-symbol importance CSVs. Ranked V3_BASE_14 features by:
- bottom3_count across BCH/LDO/TRX
- mean portfolio importance
- per-symbol load-bearing exclusion (regime_momentum_signed_5d protected)

Top candidate: ret_skew_50 (bottom-3 on 2 of 3 syms; portfolio importance 137.6).

### Stage 4 — NEW feature filtering

Applied gates:
- ADF p < 0.05 all 3 syms
- max |IC| with V3_BASE_14 < 0.50 (Category-1 strict)
- At least 1 sym Spearman p < 0.05
- |skew| < 10, |kurt| < 50
- n_valid > 1000 all 3 syms

8 of 28 candidates passed all gates. Ranked by mean |Spearman| ρ.

### Stage 5 — Decision

Top filtered candidate: parkinson_gk_ratio_20.
- All 3 syms Spearman p<0.005 (strongest predictability)
- max |IC| 0.245 (well below 0.50 gate)
- FIRST-IN-CATEGORY for v3 base stack (price_efficient_vol family)
- Was in V3_FEATURE_COLUMNS_FULL at /001-006; dropped at /007 dimensionality reduction
  (rank 17/34; NOT NEGATIVE — just outside top-14)
- Never tested at dedicated EXPLORATION axis
- Also in V2_FEATURE_COLUMNS (v0.v2-069 active baseline)

### Stage 6 — Mechanism prediction

The SWAP exchanges a tail_risk feature (5th of 6 already in base stack) for a
price_efficient_vol feature (first in family). Expected to:
- Reach Optuna trajectories not available at base-14
- Shift CPCV path distribution (escape PATH E)
- Lift IS Sharpe if signal is genuine

### Stage 7 — Falsifier band lock

Per Section 4.4 LOCKED criteria, the outcome paths are pre-registered. No post-hoc
renegotiation per `feedback_no_cheating.md`.

### Stage 8 — Setup commit SHA backfill

Phase 5.5 gate at QE setup commit will backfill the setup commit SHA into Section 10
after Engineer dispatches.

---

## Section 11 — Bundle State Verification

At iter-v3/057 head (after setup commit):

| Component | Value | Source |
|---|---|---|
| V3_MODELS | (BCHUSDT, LDOUSDT, TRXUSDT) | UNCHANGED from /056 |
| V3_FEATURE_COLUMNS_TOP_N count | 14 | UNCHANGED (1-for-1 SWAP) |
| V3_ATR_MULTIPLIERS_PER_SYMBOL | {} | UNCHANGED |
| DEFAULT_ATR_MULTIPLIERS | (2.0, 1.0) | UNCHANGED |
| RiskV2Config.block_long_for | () | UNCHANGED |
| RiskV2Config.adx_threshold_per_symbol | {} | UNCHANGED |
| RiskV2Config.enable_per_symbol_drawdown_brake | False | UNCHANGED |
| REQUIRED_GAP | 66 | UNCHANGED (= (21+1)×3) |
| ENSEMBLE_SIZE | 5 | UNCHANGED |
| dsr.json schema fields | dsr_legacy + dsr_relative + cpcv_path_sharpe_q75 | UNCHANGED from /056 (post-fix) |
| ITERATION_LABEL | "v3-057" | NEW |
| V3_FEATURE_COLUMNS_TOP_N membership | ret_skew_50 OUT, parkinson_gk_ratio_20 IN | NEW |

---

## Section 12 — What This Iteration Means For The Cycle

### If PATH A fires (8-12% prior probability)

iter-v3/057 introduces the FIRST PROMISING component since iter-v3/045 LDO ATR
(cycle 3 #6). The SWAP is non-compoundable across iterations (it replaces an
existing feature; doesn't stack). The new feature parkinson_gk_ratio_20 becomes
a permanent V3_BASE_14 member, replacing ret_skew_50 in all subsequent cycle-4
EXPLORATIONs (/058-/060). The iter-v3/061 CONFIRMATION would multi-seed validate
the full 14-feature stack with the SWAP applied. Cycle 4 cadence advances 7/10.

### If PATH B, C, or D fires (most likely combined ~40-45% probability)

iter-v3/058 reverts the SWAP (restore ret_skew_50) and chooses a different axis.
A4 base-stack reordering is CLOSED for cycle 4 (the next attempt would test a
different DROP target or ADD target — but each attempt is a separate EXPLORATION
row in the cadence count). Per Critic /056 + /055 + /054 cumulative recommendations,
the next axis options are:
- NEW feature family at slot 15 (if /054's "Category 2" closure is interpreted
  narrowly — orchestrator + Critic to adjudicate)
- Pivot to /058 with a structural axis (universe, model arch — both CLOSED) or
  defer to /062 cycle 5 mass feature expansion.

### If PATH E fires alone (50-60% prior probability)

CPCV path distribution is bit-identical to /051..056 for the 7th consecutive
iteration. The cycle-4 architectural pin is confirmed at A4 SWAP scope. Cycle-5
mass feature expansion mandate (per `feedback_v3_mass_feature_expansion.md`) is
the next structural shift.

### Cycle 4 cadence after /057

After /057: 7/10 EXPLORATIONs done. Remaining: /058, /059, /060 + /061 CONFIRMATION.
Per `feedback_v3_strict_10_to_1_cadence.md`, /060 (10th EXPLORATION) MUST be a
SEPARATE single-seed EXPLORATION (NOT a CONFIRMATION-spec collapsed run).

---

**END OF BRIEF — Phase 5 complete.**

**SHA**: this commit (populated at git commit time).
**Next**: Orchestrator dispatches QE for Phase 5.5 setup commit + Phase 5.5 gate.
