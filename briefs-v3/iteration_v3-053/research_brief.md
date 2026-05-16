# Iteration v3-053 — Research Brief (hurst_drift_50_200 UNIVERSAL SWAP)

**Type**: EXPLORATION (Cycle 4 #3 of 10)
**Track**: v3 (rigor arm) — fifty-third iteration
**Branch**: `iteration-v3/053` (off iter-v3/052 head at SHA `542c6a8`)
**Date**: 2026-05-11
**Author**: QR (autopilot)

**FRAMING NOTICE**: This brief proceeds under REFRAMED HYPOTHESIS B per
`feedback_v3_axis_selection_quant_discipline.md`. The orchestrator pick (per /052
closeout HIGH-priority #1) was PRELIMINARILY supported — it cited /051 EDA candidate
#4 (deferred-on-implementation-cost ranking) and is a Category 1 NEW feature family
distinct from regime_momentum. **However the /053 QR EDA at SHA `1fc6d55` revealed
three structural pre-falsifiers not previously tested**:

1. **Linear redundancy R² = 1.0 EXACT** across all 4 symbols: `hurst_drift_50_200 =
   hurst_100 − hurst_diff_100_50 − hurst_200` (algebraic identity since
   `hurst_50 = hurst_100 − hurst_diff_100_50` in regime_v3.py).
2. **Univariate Spearman ρ NOT SIGNIFICANT** at p<0.05 in any of 4 symbols (mean
   ρ +0.0114 — weakest signal of any v3 Category 2 candidate).
3. **Max |IC| 0.85-0.88** with `hurst_diff_100_50` (source primitive) across all 4
   symbols — exceeds prior 5 Category 2 candidates in v3 history.

**Decision: PROCEED with hurst_drift_50_200 as /053 axis under REFRAMED HYPOTHESIS B.**
The pre-falsifiers predict PATH B (PROMISING-INERT) with 55% probability; the
EXPLORATION's primary value is to DOCUMENT the **Linear Redundancy Pre-Falsifier
(LR-PF)** methodology, which compounds across all subsequent Category 2 composed-
feature axis selections. Section 10 audit trail documents the EDA-supported
re-framing.

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

Sacred constants UNCHANGED. The QR sees iter-v3/053 OOS metrics for the FIRST time
in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 4 — #3 of 10 (third EXPLORATION post-iter-v3/050 NO-MERGE CONFIRMATION)
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
  - ENSEMBLE_SIZE=5 (auto; inner ensemble)
  - n_trials=35 (default per `feedback_v3_exploration_n_trials_35.md`)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
  - --clean-oof (use guardrail from SHA `6a216b5` to prevent OOF parquet contamination)

Carry-forward state (UNCHANGED from iter-v3/052 head except 15th-slot SWAP):
  - V3_FEATURE_COLUMNS_TOP_N at /052 HEAD = 15 features (incl. regime_momentum_signed_3d
    at slot 15 — CLOSED per /052 PATH C-suspicious closeout; DROPPED at /053 setup)
  - V3_MODELS at /052 HEAD = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols (UNCHANGED at /053)
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty; UNCHANGED at /053)
  - block_long_for = () (empty; UNCHANGED at /053)
  - regime_momentum_signed_5d PRESERVED (iter-v3/028 edge ingredient; UNCHANGED at /053)
  - DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)
  - adx_threshold_per_symbol = {} (empty)
  - All other risk gates UNCHANGED (BTC trend, OOD, ADX 20.0, hit-rate disabled, etc.)
  - REQUIRED_GAP at /052 HEAD = 66 = (21+1)×3 (UNCHANGED at /053 — universe unchanged)

SINGLE-AXIS SWAP for /053 (QR-EDA-backed per `feedback_v3_axis_selection_quant_discipline.md`):
  AXIS: SWAP regime_momentum_signed_3d → hurst_drift_50_200 in V3_FEATURE_COLUMNS_TOP_N
    (DROP regime_momentum_signed_3d as 15th element per /052 closeout PATH C-suspicious
    action; ADD hurst_drift_50_200 as 15th element)
    Mechanism: hurst_drift_50_200 = hurst_50 − hurst_200
                                  = (hurst_100 − hurst_diff_100_50) − hurst_200
                                  (NEW Category 1 engineered feature; orthogonal at the
                                  FEATURE level to regime_momentum family but EDA-shown
                                  redundant at LINEAR-COMBINATION level with 3 source
                                  primitives already in feature stack)
    Net effect: V3_FEATURE_COLUMNS_TOP_N stays at 15 features; 3d PARKED, hurst_drift_50_200 ACTIVATED.

Setup commit changes (locked in §3):
  - src/crypto_trade/features_v3/engineered_v3.py: ADD `compute_hurst_drift_50_200`
    function (NEW; ~20 LOC) and DISPATCH in `add_engineered_v3_features` after
    `compute_regime_momentum_signed_5d` call.
  - src/crypto_trade/features_v3/__init__.py:V3_FEATURE_COLUMNS_TOP_N = 15 (SWAP 15th
    element: regime_momentum_signed_3d → hurst_drift_50_200)
  - NO feature regeneration required (computable from existing parquet columns
    `hurst_100`, `hurst_diff_100_50`, `hurst_200` — verified at axis5_linear_redundancy.csv)
  - run_baseline_v3.py:_verify_feature_columns updated (assert 15 with
    hurst_drift_50_200 present; assert regime_momentum_signed_3d NOT present;
    fracdiff_d05_close NOT present remains)
  - run_baseline_v3.py:ITERATION_LABEL = "v3-053"
  - V3_MODELS, REQUIRED_GAP, V3_ATR_MULTIPLIERS_PER_SYMBOL, block_long_for: UNCHANGED from /052
  - compute_regime_momentum_signed_3d + 5 adversarial tests RETAINED as dead-code
    (zero revert cost; feature column dropped but compute function preserved per
    /052 closeout PATH C-suspicious mandate)
  - compute_fracdiff_d05_close + 5 adversarial tests RETAINED as dead-code (PARKED at /051)

Predicted classification (locked in §7):
  - PATH A (PROMISING-clean): 5% probability
  - PATH B (PROMISING-INERT): **55%**
  - PATH C-clean (NEGATIVE-clean): 10%
  - PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS): 15%
  - PATH D (EXPLORATION-NULL-RESULT, per Critic FINAL `32cc46f` rec #3): 15%
```

**Context**: iter-v3/052 EXPLORATION-NEGATIVE PATH C-suspicious closeout per Critic
FINAL `34cc46f`. regime_momentum_signed_3d at universal scope ranked 14-15/15 across
all 3 symbols (saturation-INERT), but IS-OOS daily Sharpe ratio 2.327 OUT-OF-BAND
fired PATH C-suspicious — TRX OOS WR jump 41.3% → 52.5% on rank-15/15 feature
mechanically attributable to Optuna hyperparameter lottery on the base 14 features
(NOT signal). regime_momentum family EXHAUSTED at universal single-seed EXPLORATION
scope. /052 Critic FINAL Recommendation #2 mandated pivot to structurally distinct
feature family at /053.

The orchestrator pick per /052 closeout HIGH-priority #1 = `hurst_drift_50_200`
(NEW Category 1 engineered feature; structurally distinct from regime_momentum).
**Per `feedback_v3_axis_selection_quant_discipline.md` rule 1 (EDA precedes axis
selection), the /053 QR EDA at SHA `1fc6d55` produced numerical evidence on the
candidate.** The EDA revealed 3 pre-falsifiers (linear redundancy R²=1.0,
univariate ρ insignificant, max |IC| 0.85-0.88), but the orchestrator pick is
**PRELIMINARILY SUPPORTED** — no available alternative axis has comparable
implementation cost (CatBoost head-to-head: 4-8h OOB; DSR gate reformulation:
methodology-only; per-symbol drawdown brake: untested mechanism).

**Decision (this brief): PROCEED with hurst_drift_50_200 under REFRAMED HYPOTHESIS B**
— the EXPLORATION's primary value at PATH B PROMISING-INERT (55% prob) is to
DOCUMENT the Linear Redundancy Pre-Falsifier (LR-PF) methodology as an EDA-time
guard for future Category 2 composed-feature axis selections.

iter-v3/053 = cycle 4 #3 of 10 EXPLORATIONs (per `feedback_v3_strict_10_to_1_cadence.md`).
iter-v3/061 = cycle 4 CONFIRMATION (SEPARATE single-seed iter-v3/060 first; do NOT
collapse 10th EXPLORATION).

---

## Section 1 — Hypothesis

ADDING `hurst_drift_50_200` to V3_FEATURE_COLUMNS_TOP_N at universal scope (SWAP
with regime_momentum_signed_3d which DROPS per /052 closeout; net count stays 15) —
alongside the system-level REVERT carry-forward (V3_MODELS = 3-sym BCH+LDO+TRX,
V3_ATR_MULTIPLIERS_PER_SYMBOL = {}, block_long_for = (), REQUIRED_GAP = 66) —
investigates whether the NEW Category 1 engineered feature `hurst_drift_50_200 =
hurst_50 − hurst_200` (regime-drift between short-horizon and long-horizon Hurst
windows) provides incremental discriminative value to LightGBM's tree-split
decisions, DESPITE the EDA-discovered LINEAR REDUNDANCY R² = 1.0 with 3 source
primitives (hurst_100, hurst_diff_100_50, hurst_200 — all in feature stack except
hurst_200 which is in parquet but not in V3_FEATURE_COLUMNS_TOP_N).

The hypothesis is REFRAMED under HYPOTHESIS B: tree models with depth-3 splits on
(H100, HDIFF, H200) can approximate the linear combination via axis-aligned
hyperrectangles, but linear combinations are NOT exactly tree-representable. The
composed feature presents a SINGLE pre-aggregated number to LightGBM, which MAY
improve `colsample_bytree` efficiency if regime-drift signal exists. The primary
value of the EXPLORATION is to DOCUMENT the **Linear Redundancy Pre-Falsifier**
(LR-PF) methodology — an EDA-time guard against INERT-OVERFIT outcomes for future
Category 2 composed-feature axis selections.

**Predicted single-seed result (per QR EDA at SHA `1fc6d55`, axis1-axis6 CSVs):**

- Bundle IS Sharpe: predicted band [+0.40, +0.60] (mean +0.50); Δ vs /028 anchor
  +0.5101: **[-0.10, +0.05]** (saturation; minimal effect either way). Rationale:
  feature is mathematically expressible by 3 source primitives already in feature
  stack; insignificant univariate ρ (mean +0.0114) suggests minimal directional
  signal extraction at single-seed n_trials=35.
- Bundle OOS Sharpe: predicted band [+0.20, +0.85] (mean +0.50); Δ vs /028 anchor
  +0.5053: **[-0.30, +0.30]** (uncertain at single-seed). The OOS uncertainty is
  WIDER than IS because the 14 base features + the (mostly redundant) 15th feature
  may produce different Optuna hyperparameter draws on the OOS window.
- IS-OOS daily Sharpe ratio: predicted ∈ [0.5, 2.0] with 60% prob (in-band); outside
  band PATH C-suspicious with 15% prob (same anti-pattern as /026/027/052).
- IS trade count: predicted band [130, 200] (Δ -17% to +28% vs /052's 188).
- OOS trade count: predicted band [70, 110] (Δ -25% to +18% vs /052's 93).
- hurst_drift_50_200 importance rank: **PRE-FALSIFIER PREDICTION** = rank 13-15/15
  in ALL 3 symbols (saturation-INERT outcome PATH B with 55% prob). The linear-
  redundancy structure means Optuna at n_trials=35 single-seed will likely prefer
  the 3 source primitives (which the candidate is mechanically composed from) over
  the composed candidate.

This axis directly addresses the cycle 4 starting hypothesis: "lift IS Sharpe to
≥ +0.5101 (BASELINE_V3.md update gate floor) while preserving OOS Sharpe ≥ +0.5053
via UNIVERSAL axes (per-symbol customizations rejected at bundle level)" (per
iter-v3/050 diary §Cadence). However the EDA evidence predicts the axis will NOT
lift IS Sharpe materially — the LR-PF methodology documentation is the primary
contribution if PATH B fires.

---

## Section 2 — IS-Only Numerical Evidence

**Primary EDA evidence sourced from committed `analysis/iteration_v3-053/` (SHA
`1fc6d55`), produced by `hurst_drift_50_200_eda.py` on-the-fly from existing parquet
columns `hurst_100`, `hurst_diff_100_50`, `hurst_200` (NO feature regeneration
required).**

### 2.1 — hurst_drift_50_200 ADF stationarity (axis2_adf_per_symbol.csv)

| Symbol | n_is_obs | ADF stat | ADF p-value | Stationary at p<0.05 |
|---|---:|---:|---:|---|
| BCHUSDT | 5528 | -11.70 | 1.55e-21 | **TRUE** |
| LDOUSDT | 2542 | -9.30 | 1.13e-15 | **TRUE** |
| TRXUSDT | 5470 | -11.61 | 2.59e-21 | **TRUE** |
| ALGOUSDT | 5026 | -10.82 | 1.77e-19 | **TRUE** |

**ALL 4 symbols stationary at p<<0.05** (well beyond conventional critical value of
-2.86). Expected behavior: bounded difference of two bounded R/S Hurst measurements
is structurally stationary by construction.

### 2.2 — hurst_drift_50_200 IC matrix (axis3_ic_matrix.csv + axis3_top_ic_pairs.csv)

Per-symbol max |IC| with existing 14 features + hurst_200 source primitive:

```
symbol     max     mean    candidate (max-IC partner)
BCHUSDT    0.881   ~0.29   hurst_diff_100_50  (SOURCE PRIMITIVE)
LDOUSDT    0.860   ~0.30   hurst_diff_100_50  (SOURCE PRIMITIVE)
TRXUSDT    0.853   ~0.29   hurst_diff_100_50  (SOURCE PRIMITIVE)
ALGOUSDT   0.874   ~0.28   hurst_diff_100_50  (SOURCE PRIMITIVE)
```

Top 8 |IC| pairs (top of axis3_top_ic_pairs.csv):

| Symbol | candidate | existing_feature | IC | abs_IC | is_source_primitive |
|---|---|---|---:|---:|---|
| BCHUSDT | hurst_drift_50_200 | hurst_diff_100_50 | -0.881 | 0.881 | **YES** |
| ALGOUSDT | hurst_drift_50_200 | hurst_diff_100_50 | -0.874 | 0.874 | **YES** |
| LDOUSDT | hurst_drift_50_200 | hurst_diff_100_50 | -0.860 | 0.860 | **YES** |
| TRXUSDT | hurst_drift_50_200 | hurst_diff_100_50 | -0.853 | 0.853 | **YES** |
| TRXUSDT | hurst_drift_50_200 | hurst_200 | -0.322 | 0.322 | **YES** |
| LDOUSDT | hurst_drift_50_200 | hurst_200 | -0.287 | 0.287 | **YES** |
| BCHUSDT | hurst_drift_50_200 | hurst_200 | -0.275 | 0.275 | **YES** |
| ALGOUSDT | hurst_drift_50_200 | hurst_200 | -0.241 | 0.241 | **YES** |

ALL 4 strict-gate violations (>0.70) are with source primitives (hurst_100,
hurst_diff_100_50, hurst_200). Per `feedback_v3_engineered_feature_pivot.md`
Category 2 carve-out: composed features get IC carve-out vs source primitives.
**Carve-out PASSES mechanically.**

**HOWEVER** max |IC| 0.85-0.88 EXCEEDS the prior 5 Category 2 candidates in v3 history:

| Category 2 candidate | Status | max |IC| with source primitive |
|---|---|---:|
| regime_momentum_signed_5d | MERGED (iter-v3/025+/028 edge ingredient) | 0.467 |
| regime_momentum_signed_3d | CLOSED (iter-v3/052 PATH C-suspicious) | 0.619 |
| fracdiff_d05_close | PARKED (iter-v3/035 + /051) | 0.738 |
| vol_adj_autocorr | CLOSED (iter-v3/026 PATH C-suspicious) | n/a (not tracked) |
| cross_asset_divergence_norm | CLOSED (iter-v3/027 PATH C-suspicious) | 0.756 |
| **hurst_drift_50_200** | **THIS BRIEF** | **0.881** |

**Post-carve-out (excluding hurst_100, hurst_diff_100_50, hurst_200)**: max |IC| =
0.193 with ret_skew_50 at LDO. Clean post-carve-out, but the underlying R²=1.0
linear redundancy with 3 source primitives is unprecedented in v3 history.

### 2.3 — hurst_drift_50_200 Univariate Spearman ρ vs forward 1-bar return (axis4_univariate_spearman.csv)

| Symbol | feature | n_IS | Spearman ρ | p-value | Significant at p<0.05 |
|---|---|---:|---:|---:|---|
| BCHUSDT | hurst_drift_50_200 | 5528 | +0.0041 | 0.760 | **NO** |
| LDOUSDT | hurst_drift_50_200 | 2542 | +0.0118 | 0.552 | **NO** |
| TRXUSDT | hurst_drift_50_200 | 5470 | +0.0112 | 0.407 | **NO** |
| ALGOUSDT | hurst_drift_50_200 | 5026 | +0.0186 | 0.187 | **NO** |

**hurst_drift_50_200 univariate ρ is NOT significant at p<0.05 in ANY of 4 symbols.**
Mean ρ = +0.0114 (positive — OPPOSITE SIGN from prior mean-reversion engineered
features). Effect sizes 0.004-0.019 are roughly half the magnitude of regime_momentum_
signed_5d (significant only for TRX at ρ=-0.039, p=0.004).

**Comparison vs prior Category 2 candidates' univariate ρ**:
- regime_momentum_signed_5d (MERGED): mean ρ ≈ -0.024; significant only at TRX
- regime_momentum_signed_3d (CLOSED): mean ρ = -0.057, significant ALL 4 syms
- fracdiff_d05_close (PARKED): mean ρ = -0.044, significant ALL 4 syms

**hurst_drift_50_200 has the WEAKEST univariate signal of any v3 Category 2 candidate
tested or queued to date.**

### 2.4 — hurst_drift_50_200 Linear Redundancy diagnostic (axis5_linear_redundancy.csv — CRITICAL PRE-FALSIFIER)

OLS regression: `hurst_drift_50_200 ~ hurst_100 + hurst_diff_100_50 + hurst_200`

| Symbol | n_IS | intercept | coef_H100 | coef_HDIFF | coef_H200 | R² | RMSE | max_abs_residual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 5528 | -2.6e-16 | 1.0 | -1.0 | -1.0 | **1.000** | 8.9e-16 | 9.5e-16 |
| LDOUSDT | 2542 | +8.5e-16 | 1.0 | -1.0 | -1.0 | **1.000** | 8.5e-16 | 9.4e-16 |
| TRXUSDT | 5470 | -5.1e-18 | 1.0 | -1.0 | -1.0 | **1.000** | 2.2e-16 | 2.2e-16 |
| ALGOUSDT | 5026 | +2.6e-15 | 1.0 | -1.0 | -1.0 | **1.000** | 5.9e-16 | 8.9e-16 |

**hurst_drift_50_200 is the EXACT linear combination
`hurst_100 − hurst_diff_100_50 − hurst_200` to numerical precision (residuals at
machine epsilon).** By algebraic identity:
- `hurst_50 = hurst_100 − hurst_diff_100_50` (from regime_v3.py line 126:
  `hurst_diff_100_50 = hurst_100 - rolling_hurst(close, 50)` → re-arrange)
- `hurst_drift_50_200 = hurst_50 − hurst_200 = hurst_100 − hurst_diff_100_50 − hurst_200`

Tree models with depth-3 splits on (H100, HDIFF, H200) can approximate this linear
combination via axis-aligned hyperrectangles, but NOT exactly. The composed feature
DOES present single-column discrimination that splits cannot directly replicate.
**HOWEVER** at single-seed n_trials=35, Optuna may prefer the 3 source primitives
(which the candidate is mechanically composed from) over the composed candidate —
this is the basis of the PATH B PROMISING-INERT 55% probability prediction.

### 2.5 — hurst_drift_50_200 distribution stats (axis1_compute_and_distribution.csv + axis6_per_symbol_distribution.csv)

| Symbol | n_IS | mean | std | min | p5 | median | p95 | max | skew | kurt | autocorr_lag1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 5528 | -0.006 | 0.091 | -0.494 | -0.178 | 0.008 | 0.122 | 0.231 | -0.93 | 1.58 | 0.94 |
| LDOUSDT | 2542 | +0.010 | 0.084 | -0.386 | -0.150 | 0.026 | 0.123 | 0.241 | -0.81 | 0.80 | 0.93 |
| TRXUSDT | 5470 | +0.000 | 0.088 | -0.458 | -0.170 | 0.013 | 0.120 | 0.246 | -0.88 | 1.24 | 0.93 |
| ALGOUSDT | 5026 | -0.005 | 0.086 | -0.443 | -0.175 | 0.009 | 0.112 | 0.195 | -0.93 | 1.12 | 0.94 |

Bounded distribution (~[-0.5, 0.25]). Slightly left-skewed (-0.81 to -0.93). Modest
excess kurtosis (0.80 to 1.58). Mean near zero across all 4 symbols (no systematic
regime bias). **Autocorr_lag1 ~0.93-0.94 (very persistent — but expected given source
primitives' autocorr ~0.95-0.98)**. High autocorrelation creates risk: a feature with
weak univariate signal AND high autocorr contributes minimal cross-sectional
discrimination to LightGBM's split decisions.

### 2.6 — Summary of EDA evidence

**Three pre-falsifiers FIRE for hurst_drift_50_200**:

1. **Linear redundancy R²=1.0**: candidate is EXACT linear combination of 3 source
   primitives (hurst_100, hurst_diff_100_50, hurst_200). Tree models can
   approximate via depth-3 splits.

2. **Max |IC| 0.85-0.88 with hurst_diff_100_50** (source primitive) across all 4
   symbols. Carve-out applies mechanically but exceeds prior 5 Category 2 candidates.

3. **Univariate ρ INSIGNIFICANT** at p<0.05 in all 4 symbols. Mean ρ +0.0114 is
   weakest of any v3 Category 2 candidate.

**No EDA evidence supports a clean PROMISING outcome.** The axis proceeds under
REFRAMED HYPOTHESIS B (LR-PF methodology documentation) per QR discretion.

---

## Section 3 — Proposed Changes

### 3.1 — V3_FEATURE_COLUMNS_TOP_N SWAP

**SWAP 15th element**: DROP `regime_momentum_signed_3d` (per /052 closeout PATH
C-suspicious mandate); ADD `hurst_drift_50_200` (NEW Category 1 engineered feature).
Net feature count UNCHANGED at 15.

Current 15-feature list (at /052 head):

```
1.  max_dd_window_50
2.  ema_spread_atr_20
3.  ret_kurt_50
4.  ret_skew_200
5.  range_realized_vol_50
6.  hurst_diff_100_50           ← source primitive for hurst_drift_50_200
7.  ret_kurt_200
8.  hurst_100                   ← source primitive for hurst_drift_50_200
9.  btc_ret_14d
10. ret_skew_50
11. vwap_dev_20
12. ret_autocorr_lag1_50
13. sym_vs_btc_ret_7d
14. regime_momentum_signed_5d   ← iter-v3/028 edge ingredient; PRESERVED
15. regime_momentum_signed_3d   ← CLOSED at /052 PATH C-suspicious; DROPPED at /053 setup
```

Post-/053 setup 15-feature list:

```
1-14: UNCHANGED
15. hurst_drift_50_200          ← NEW Category 1 engineered feature
```

### 3.2 — V3_MODELS UNCHANGED at 3-sym

V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT). UNCHANGED from /052 (carry-forward).
ALGOUSDT REVERTED at system level per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`
2-cycle confirmation (iter-v3/039 + /050).

### 3.3 — Risk gate config UNCHANGED

Carry-forward state from /052:
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty)
- DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)
- block_long_for = () (empty)
- adx_threshold = 20.0 (global)
- adx_threshold_per_symbol = {} (empty)
- zscore_threshold = 2.0
- BTC_TREND_CONFIG.threshold_pct = 15.0
- enable_per_symbol_cap = False (CLOSED per /020)
- enable_regime_gate = False (CLOSED per /022)
- hit_rate_gate.enabled = False (DISABLED)

### 3.4 — REQUIRED_GAP UNCHANGED at 66

REQUIRED_GAP = 66 = (21+1)×3 (3-symbol universe; UNCHANGED from /052).

### 3.5 — ITERATION_LABEL UPDATE

`run_baseline_v3.py:ITERATION_LABEL = "v3-053"` (from "v3-052").

### 3.6 — Source code changes

**NEW compute function in `src/crypto_trade/features_v3/engineered_v3.py`**:

```python
def compute_hurst_drift_50_200(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: hurst_50 − hurst_200 (regime-drift across time-scales).

    Construction (uses existing past-only parquet primitives):
    - hurst_50  = rolling 50-bar R/S Hurst exponent (computable from hurst_100 −
      hurst_diff_100_50, since hurst_diff_100_50 = hurst_100 − rolling_hurst(close, 50)
      in regime_v3.py:126)
    - hurst_200 = rolling 200-bar R/S Hurst exponent (in parquet via
      regime_v3.add_regime_v3_features:125)
    - hurst_drift_50_200 = hurst_50 − hurst_200 = hurst_100 − hurst_diff_100_50 − hurst_200

    Mechanism: positive drift = short-horizon (50-bar) trending stronger than
    long-horizon (200-bar) — mean-reversion entering; negative = long-horizon
    trending stronger — momentum building.

    Stationarity: ADF p < 0.05 by construction (bounded difference of two bounded
    R/S Hurst measurements). Verified at axis2_adf_per_symbol.csv across all 4 syms.

    Linear redundancy DISCLOSURE: R² = 1.000 EXACT vs (hurst_100, hurst_diff_100_50,
    hurst_200) — see analysis/iteration_v3-053/axis5_linear_redundancy.csv. The
    composed feature is mathematically expressible as a depth-3 hyperrectangle split
    by tree models on the 3 source primitives, but NOT exactly. Single-column
    representation may improve `colsample_bytree` efficiency at LOW Optuna budget
    (n_trials=35 single-seed) — this is the REFRAMED HYPOTHESIS B basis.

    Past-only by construction:
    - All 3 source primitives are past-only (computed by upstream regime_v3 group).
    - Element-wise subtraction at row t uses only past-only values at row t.
    - Appending future bars does NOT alter the value at t.

    NaN warm-up: first 200 bars NaN (dominated by hurst_200 200-bar warm-up).

    Args:
        df: DataFrame with columns ``hurst_100``, ``hurst_diff_100_50``, ``hurst_200``
            (pre-computed by ``add_regime_v3_features``).

    Returns:
        Copy of ``df`` with ``hurst_drift_50_200`` column appended. If any source
        primitive is missing, the column is set to all-NaN without error (runner's
        _verify_feature_columns assertion catches the gap downstream).
    """
    df = df.copy()
    if not all(c in df.columns for c in ["hurst_100", "hurst_diff_100_50", "hurst_200"]):
        df["hurst_drift_50_200"] = np.nan
        return df
    df["hurst_drift_50_200"] = (
        df["hurst_100"].astype(float)
        - df["hurst_diff_100_50"].astype(float)
        - df["hurst_200"].astype(float)
    )
    return df
```

**Dispatch in `add_engineered_v3_features`**: add 1 line after the call to
`compute_regime_momentum_signed_5d`:

```python
df = compute_regime_momentum_signed_5d(df)
df = compute_hurst_drift_50_200(df)   # ← NEW dispatch at /053
```

`compute_regime_momentum_signed_3d` remains in the file as DEAD CODE (per /052
PATH C-suspicious closeout) — NOT dispatched.

### 3.7 — Feature parquet regeneration: NOT REQUIRED

The candidate feature is computable from existing parquet columns. Verified at
axis5_linear_redundancy.csv (R² = 1.000 across all 4 syms). The feature can be
computed on-the-fly during model training without regenerating the parquets.

Path 1 (preferred): the compute function dispatches at training-time loading; the
parquet files don't need updating. **This is the path used at /053.** Zero feature
regen cost.

Path 2 (alt): regenerate parquets to include hurst_drift_50_200 as a stored column.
Cost: ~5-10 min for 4 symbols (BCH, LDO, TRX, ALGO). Not needed.

### 3.8 — `_verify_feature_columns` assertions

Update at `run_baseline_v3.py:_verify_feature_columns`:

```python
def _verify_feature_columns(cols: tuple[str, ...]) -> None:
    n = len(cols)
    assert n == 15, f"V3_FEATURE_COLUMNS_TOP_N must have 15 features at iter-v3/053, got {n}"
    assert "hurst_drift_50_200" in cols, "hurst_drift_50_200 must be present at iter-v3/053"
    assert "regime_momentum_signed_3d" not in cols, "regime_momentum_signed_3d DROPPED at iter-v3/053"
    assert "regime_momentum_signed_5d" in cols, "regime_momentum_signed_5d MANDATE: iter-v3/028 edge ingredient"
    assert "fracdiff_d05_close" not in cols, "fracdiff_d05_close PARKED at iter-v3/051"
```

### 3.9 — Adversarial tests

5 NEW adversarial tests in `tests/features_v3/test_hurst_drift_50_200_universal.py`:

1. `test_hurst_drift_50_200_in_universal_feature_list` — assert presence at 15th
   slot in V3_FEATURE_COLUMNS_TOP_N.
2. `test_hurst_drift_50_200_computable_from_source_primitives` — assert exact match
   between `compute_hurst_drift_50_200` output and `hurst_100 − hurst_diff_100_50
   − hurst_200` on synthetic data.
3. `test_hurst_drift_50_200_stationary_per_symbol` — assert ADF p < 0.05 across all
   3 V3_MODELS (BCH, LDO, TRX).
4. `test_hurst_drift_50_200_past_only_no_lookahead` — assert value at row t depends
   only on rows 0..t (no future-bar contamination); verified by appending future
   bars and checking row t value is unchanged.
5. `test_v3_models_is_3_symbol_at_iter_v3_053` — assert V3_MODELS = (BCHUSDT,
   LDOUSDT, TRXUSDT).

### 3.10 — Dead-code retention

- `compute_regime_momentum_signed_3d` (engineered_v3.py:330-376): RETAINED as dead
  code per /052 closeout PATH C-suspicious mandate; NOT dispatched.
- `compute_fracdiff_d05_close` (engineered_v3.py:264+): RETAINED as dead code per
  /051 PARKED status; NOT dispatched.
- `compute_vol_adj_autocorr` (engineered_v3.py:92+): RETAINED as dead code per /026
  CLOSED PATH C-suspicious; NOT dispatched.
- `compute_cross_asset_divergence_norm` (engineered_v3.py:155+): RETAINED as dead
  code per /027 CLOSED PATH C-suspicious; NOT dispatched.
- `compute_efficiency_ratio_50` (engineered_v3.py:379+): RETAINED as dead code per
  /043 disaster NEGATIVE; NOT dispatched.
- `compute_vol_normalized_ret_5d` (engineered_v3.py:439+): RETAINED as dead code
  per /048 PATH C-clean; NOT dispatched.

Net total dead-code engineered features: 6 (post-/053).

---

## Section 4 — Expected OOS Impact

### 4.1 — Predicted bundle metrics

| Metric | /028 anchor | /052 single-seed | **/053 prediction (band)** | Δ vs /028 anchor |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | +0.5101 | +0.5161 | **+0.40 to +0.60** (mean +0.50) | **[-0.10, +0.05]** |
| OOS monthly Sharpe | +0.5053 | +1.4295 | **+0.20 to +0.85** (mean +0.50) | **[-0.30, +0.30]** |
| IS-OOS daily Sharpe ratio | 0.99 | 2.3267 | **0.5 to 2.0** (60% prob in-band) | n/a |
| IS Trades | 156 (mean) | 188 | 130-200 | -17% to +28% vs /052 |
| OOS Trades | 95 (mean) | 93 | 70-110 | -25% to +18% vs /052 |
| OOS Top concentration | 76.47% (TRX) | 74.58% (BCH) | 60-80% (likely BCH or TRX dominant) | n/a |
| OOS MaxDD | 23.53% | 30.42% | 25-35% | wider single-seed band |
| OOS Calmar | 0.92 | 1.47 | 0.5-1.5 | wider single-seed band |
| DSR | 0.0 (structural) | 0.0 | 0.0 (structural at n_trials=525) | structural |
| PBO | 0.1243 | 0.109 | 0.10-0.15 | tight |
| frac_positive_paths | 0.644 | 0.644 | 0.60-0.70 | tight |

### 4.2 — Behavioral-effect predictor (per `feedback_v3_axis_saturation_predictor.md`)

The orchestrator pick (hurst_drift_50_200 per /052 closeout HIGH-priority #1) has
3 EDA-derived pre-falsifiers. Behavioral-effect prediction:

- **IS trade count change**: predicted ±5% relative vs /052 (SATURATION-LIKELY).
  Mechanism: composed feature is linear combination of 3 in-stack primitives;
  Optuna at n_trials=35 single-seed unlikely to use composed feature for splits
  it could express via source-primitive splits. Saturated-axis falsifier likely.

- **OOS trade count change**: predicted ±10% relative vs /052 (uncertain).

- **hurst_drift_50_200 importance rank**: PRE-FALSIFIER PREDICTION = **rank 13-15/15
  in ALL 3 symbols (saturation-INERT)**. PATH B trigger criterion. The linear-
  redundancy structure means the composed feature competes with its own source
  primitives for split-allocation budget; Optuna at low budget prefers the
  primitives.

### 4.3 — SWAP-axis variant per /052 Critic Recommendation #3

Per Critic FINAL `34cc46f` of /052 Recommendation #3:
> "Behavioral-effect predictor needs revision for SWAP axes. Future SWAP-axis briefs
> Section 4.4 should add importance-rank-ONLY saturation trigger (rank ≥ N-1/N in
> ALL syms = saturation regardless of trade-count change), because for SWAPs the
> trade roster size is bounded by the unchanged 14 base features even when the swap
> fires INERT."

**SWAP-axis importance-rank-ONLY saturation trigger (for /053)**:

If hurst_drift_50_200 importance rank ≥ 14/15 in ALL 3 V3_MODELS at /053 backtest,
PATH B (PROMISING-INERT) fires INDEPENDENT of trade-count change. Mechanism: the
SWAP preserves the 14 base features (which carry most signal); the 15th slot's
identity change (3d → hurst_drift_50_200) creates a SAME-SHAPE feature stack where
trade-roster size is bounded by base features even if the 15th feature is INERT.

### 4.4 — Saturation falsifier

PATH B PROMISING-INERT fires IF:
- hurst_drift_50_200 importance rank ≥ 14/15 in ALL 3 V3_MODELS, AND
- |IS Δ| ≤ 0.10 vs /028 anchor, AND
- |OOS Δ| ≤ 0.30 vs /028 anchor

PATH B does NOT require trade-count condition (per /052 Critic rec #3 SWAP-axis
variant). If PATH B fires, hurst_drift_50_200 is PARKED at zero revert cost
(compute function + 5 tests retained as dead code).

### 4.5 — Stacking risk (vs source primitives in feature stack)

Per `feedback_v3_engineered_features_dont_stack.md` EXPANDED 2026-05-11 (orchestrator-
applied at /052 Critic FINAL `34cc46f`) to cover SAME-FAMILY sister stacking at any
IC:

> "Sister features from same compose family (same primitive structure with different
> lookback) DO displace each other at single-seed EXPLORATION even at moderate IC
> (0.44). Proposed addition: 'Do NOT stack two engineered features from same compose
> family (same primitive structure with different lookback) at single-seed
> EXPLORATION; defer to multi-seed CONFIRMATION.'"

hurst_drift_50_200 is NOT a same-family sister of regime_momentum_signed_5d (different
primitive: Hurst-difference vs ret × sign(Hurst)). However the **R²=1.0 linear
redundancy with 3 source primitives is a stronger structural violation** than
sister-family stacking. The /052 rule expansion does not directly apply but the
underlying mechanism (displacement at colsample budget allocation) is the same.

---

## Section 5 — Risk Mitigation

### 5.1 — Pre-falsifier mitigations

The 3 EDA-derived pre-falsifiers are documented in §2.6. Mitigations:

1. **Linear redundancy R²=1.0**: monitor importance rank at /053 engineering report.
   If rank ≥ 14/15 in ALL 3 syms, PATH B fires (mechanically) and we DOCUMENT the
   LR-PF methodology. Zero revert cost.

2. **Univariate ρ insignificant**: pre-registered prediction that the axis will not
   lift IS Sharpe materially (band [-0.10, +0.05]). Saturation acknowledged.

3. **Max |IC| 0.85-0.88 with source primitives**: Category 2 carve-out applies
   mechanically. The 3 source primitives are PRESERVED in feature stack (hurst_100,
   hurst_diff_100_50 in V3_FEATURE_COLUMNS_TOP_N; hurst_200 in parquet). The composed
   feature is added ON TOP, not as a replacement.

### 5.2 — Risk Mitigation primitives (R1-R5 inherited)

UNCHANGED from /052:
- R1: BTC trend filter (lookback=42, threshold=15%; gate kill switch for non-trend
  candidates)
- R2: vol-targeting (per-symbol normalized vol scaling)
- R3: ADX threshold (global 20.0; per-symbol overrides empty)
- R4: Hurst regime classifier (signed sign-flip mechanism on hurst_100)
- R5: feature z-score OOD gate (threshold 2.0 absolute)

No new risk primitives at /053. Single-axis discipline (NEW feature; no risk
primitive variation).

### 5.3 — IS-calibrated thresholds

Pre-registered behavioral-effect predictor calibrated against /028 multi-seed
baseline (+0.5101 IS / +0.5053 OOS). PATH bands locked at §7+§8.

### 5.4 — Simulated historical effect

The /053 axis does NOT introduce new risk primitives. The single feature SWAP at
15th slot is a feature-side change; no risk-gate threshold simulation needed.

---

## Section 6 — Risk Management Design (10-Primitive Gate Table)

| Primitive | Status at /053 | UNCHANGED from /052? |
|---|---|---|
| 1. BTC trend filter | ENABLED (lookback=42, threshold=15%) | YES |
| 2. Vol-targeting | ENABLED (per-symbol) | YES |
| 3. ADX threshold | ENABLED (global=20.0) | YES |
| 4. Hurst regime classifier | EMBEDDED in regime_momentum_signed_5d | YES |
| 5. Feature z-score OOD | ENABLED (threshold=2.0) | YES |
| 6. Low-vol filter | DISABLED | YES |
| 7. Hit-rate gate | DISABLED | YES |
| 8. Per-symbol PnL cap | DISABLED (CLOSED at /020) | YES |
| 9. Regime gate (BTC-drawdown + BTC-vol) | DISABLED (CLOSED at /022) | YES |
| 10. Direction-asymmetric kill switch (`block_long_for`) | EMPTY () (REVERTED at /051) | YES |

All 10 gate primitives UNCHANGED. SINGLE-AXIS discipline: only V3_FEATURE_COLUMNS_TOP_N
15th-slot SWAP.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Single most likely failure mode** (per §2 EDA findings): **PATH B (PROMISING-INERT)
at 55% probability** — hurst_drift_50_200 importance rank ≥ 14/15 in ALL 3 symbols
(saturation-INERT). Mechanism: R²=1.0 linear redundancy with 3 source primitives
(hurst_100, hurst_diff_100_50, hurst_200) means Optuna at n_trials=35 single-seed
will prefer the source primitives (already accessible via simple splits) over the
composed candidate (which requires the model to learn the linear combination
through depth-3 splits — and the candidate's univariate signal is insignificant).

Secondary failure mode: **PATH C-suspicious at 15% probability** — IS-OOS daily
Sharpe ratio outside [0.5, 2.0]. Same anti-pattern as /026/027/052: the composed
feature at single-seed n_trials=35 introduces colsample variance that produces
OOS-window-localized artifacts. Mitigated by the (modest) post-carve-out IC
cleanliness but high pre-carve-out IC.

Tertiary failure mode: **PATH D EXPLORATION-NULL-RESULT at 15% probability** —
feature LEARNED at rank 1-13/15 in ≥1 sym but no decisive IS/OOS lift. Same status
as fracdiff_d05_close at /051.

If PATH B fires: PARK hurst_drift_50_200 at /053 closeout; pivot to next axis at
/054 (most appropriate: per-symbol drawdown brake NEW risk primitive, OR CatBoost
head-to-head NEW model arch if implementation cost can be reduced).

### 7.1 — Predicted failure-mode taxonomy (5 paths per Critic FINAL `32cc46f` rec #3 PATH D addition)

| Path | Probability | Trigger | Action if fires |
|---|---:|---|---|
| PATH A (PROMISING-clean) | 5% | IS Δ ≥ +0.05 AND OOS Δ ≥ -0.20 AND IS-OOS ratio in band AND rank ≤ 10 in ≥1 sym | Carry hurst_drift_50_200 to /054 stacking test; falsifies LR-PF methodology |
| **PATH B (PROMISING-INERT)** | **55%** | rank ≥ 14/15 ALL 3 syms AND \|IS Δ\| ≤ 0.10 AND \|OOS Δ\| ≤ 0.30 | PARK hurst_drift_50_200 (zero revert cost); pivot to next axis at /054; DOCUMENT LR-PF methodology |
| PATH C-clean (NEGATIVE-clean) | 10% | IS Δ < -0.10 OR OOS Δ < -0.30 with ratio in band | CLOSE hurst_drift_50_200 UNIVERSAL axis; document NEGATIVE; pivot to /054 |
| PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS) | 15% | IS-OOS daily Sharpe ratio outside [0.5, 2.0] | CLOSE hurst_drift_50_200 UNIVERSAL axis; document anti-pattern (4th Category 2 candidate in this pattern after /026/027/052) |
| PATH D (NULL-RESULT) | 15% | IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈ (-0.20, +0.20) AND axis LEARNED (rank ≤ 13/15 in ≥1 sym) | PARK hurst_drift_50_200; retest at multi-seed CONFIRMATION as bundle ingredient |

### 7.2 — Additional sanity-check failure modes

- **Optuna trial-count saturation**: 525 trials at 5 inner × 35 × 3 sym; n_eff
  predicted 18-22 (UNCHANGED from /051+/052). DSR likely 0.0 (structural at
  n_trials=525; EXPLORATION-INFORMATIONAL per `feedback_v3_dsr_mode_artifact.md`).

- **PBO at 3-sym universe**: predicted 0.10-0.13 (consistent with /028 0.1243, /051
  0.1168, /052 0.1090). REQUIRED_GAP=66 unchanged.

- **Linear redundancy displacement risk**: per §2.4, hurst_drift_50_200 is the EXACT
  linear combination of (hurst_100, hurst_diff_100_50, hurst_200). At engineering
  report, monitor importance ranks of all 3 source primitives + the candidate. If
  candidate ranks high while source primitives drop, that would falsify the
  LR-PF prediction and elevate to PATH A. Conversely if source primitives retain
  importance and candidate ranks 14-15/15, LR-PF is CONFIRMED.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

**LOCKED at brief commit; mechanical evaluation post-backtest; NO post-hoc
renegotiation per `feedback_no_cheating.md` discipline.**

### 8.1 — 5 LOCKED paths (per Critic FINAL `32cc46f` rec #3 PATH D addition)

| Path | All conditions must fire (AND) | Decision |
|---|---|---|
| **PATH A (PROMISING-clean)** | IS Δ ≥ +0.05 vs /028 anchor (+0.5101) AND OOS Δ ≥ -0.20 vs /028 anchor (+0.5053) AND IS-OOS daily Sharpe ratio ∈ [0.5, 2.0] AND hurst_drift_50_200 importance rank ≤ 10/15 in ≥1 of 3 syms | PROMISING for cycle 4 #3; carry hurst_drift_50_200 to /054 stacking test; FALSIFIES LR-PF methodology |
| **PATH B (PROMISING-INERT)** | hurst_drift_50_200 importance rank ≥ 14/15 in ALL 3 syms AND \|IS Δ\| ≤ 0.10 AND \|OOS Δ\| ≤ 0.30 | PARK hurst_drift_50_200 (zero revert cost); pivot to next axis at /054; DOCUMENT LR-PF methodology in diary |
| **PATH C-clean (NEGATIVE-clean)** | IS Δ < -0.10 OR OOS Δ < -0.30 (with IS-OOS daily ratio ∈ [0.5, 2.0]) | CLOSE hurst_drift_50_200 UNIVERSAL axis for cycle 4; document NEGATIVE; pivot to /054 axis |
| **PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS)** | IS-OOS daily Sharpe ratio outside [0.5, 2.0] band | CLOSE hurst_drift_50_200 UNIVERSAL axis; document 4th Category 2 PATH C-suspicious pattern (after /026/027/052); pivot to /054 axis |
| **PATH D (EXPLORATION-NULL-RESULT)** | IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈ (-0.20, +0.20) AND axis effect LEARNED (hurst_drift_50_200 importance rank ≤ 13/15 in ≥1 sym AND trade count change ≥10% OR IS+OOS Sharpe Δ both ≤ ±0.10 with rank ≤ 13/15) | NULL-RESULT; PARK hurst_drift_50_200 (retain code at zero revert cost); retest at multi-seed CONFIRMATION as bundle ingredient |

### 8.2 — Numerical thresholds

| Threshold | Value | Source |
|---|---|---|
| IS Sharpe anchor (/028 baseline) | +0.5101 | BASELINE_V3.md |
| OOS Sharpe anchor (/028 baseline) | +0.5053 | BASELINE_V3.md |
| PATH A IS Δ floor | +0.05 | EXPLORATION PROMISING band |
| PATH A OOS Δ floor | -0.20 | EXPLORATION PROMISING band |
| PATH A IS-OOS ratio band | [0.5, 2.0] | `feedback_v3_engineered_features_dont_stack.md` |
| PATH A importance rank floor | ≤ 10/15 in ≥1 sym | Per `feedback_v3_engineered_features_proven.md` |
| PATH B \|IS Δ\| range | ≤ 0.10 | INERT band |
| PATH B \|OOS Δ\| range | ≤ 0.30 | INERT band (wider than IS to accommodate single-seed OOS noise) |
| PATH B INERT criterion | rank ≥ 14/15 ALL 3 syms | SWAP-axis variant per /052 Critic Rec #3 (importance-rank-ONLY) |
| PATH C-clean IS Δ ceiling | -0.10 | NEGATIVE band |
| PATH C-clean OOS Δ ceiling | -0.30 | NEGATIVE band |
| PATH C-suspicious ratio band | [0.5, 2.0] | `feedback_v3_engineered_features_dont_stack.md` |
| PATH D IS Δ range | (-0.10, +0.05) | NULL-RESULT no-man's-land |
| PATH D OOS Δ range | (-0.20, +0.20) | NULL-RESULT no-man's-land |
| PATH D learned criterion | rank ≤ 13/15 in ≥1 sym AND (trade count change ≥10% OR Sharpe Δ both ≤ ±0.10) | LEARNED with no decisive effect |

### 8.3 — BOTH-must-improve gate (advisory, NOT MERGE-blocking at EXPLORATION-spec)

Per `feedback_v3_strict_both_is_oos_baseline.md`, BASELINE_V3.md updates require
BOTH IS AND OOS Sharpe improvement vs prior baseline. This gate is **CONFIRMATION-
only** (not applied at EXPLORATION).

At iter-v3/053 EXPLORATION-spec: if PATH A fires (low probability 5%), the axis is
a candidate for /054 stacking. If PATH B fires (most likely 55%), the axis is
parked and we pivot to the next axis candidate.

### 8.4 — DSR / PBO / PSR INFORMATIONAL at EXPLORATION-spec

Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR is structural artifact
at n_trials=525 (E[max_SR] formula returns ~2.0 required; observed annualized
≈1.0-1.5 → DSR=0). Not a MERGE gate at EXPLORATION-spec.

- DSR > 0.95 gate: ENFORCED at CONFIRMATION only
- PBO < 0.4 gate: ENFORCED at both EXPLORATION and CONFIRMATION
- PSR > 0.95 gate: ENFORCED at both
- IC < 0.7 gate: ENFORCED at both (hurst_drift_50_200 fails strict |IC|<0.70 with
  source primitives — Category 2 carve-out APPLIES per `feedback_v3_engineered_
  feature_pivot.md`; post-carve-out max |IC| = 0.193 PASSES)

### 8.5 — Catalog row pre-commits (one per outcome)

| Outcome | Catalog row |
|---|---|
| PATH A (PROMISING-clean) | `iter-v3/053 \| hurst_drift_50_200 UNIVERSAL ADD (cycle 4 #3) \| 1fc6d55 (EDA) \| PROMISING-clean (LR-PF FALSIFIED) \| IS Δ +X / OOS Δ +Y / rank Z/15 in N syms \| carry to /054 stacking test` |
| PATH B (PROMISING-INERT) | `iter-v3/053 \| hurst_drift_50_200 UNIVERSAL ADD (cycle 4 #3) \| 1fc6d55 (EDA) \| PROMISING-INERT (LR-PF CONFIRMED at rank 14-15/15 ALL syms) \| IS Δ +X / OOS Δ +Y / rank 14-15/15 \| PARK; pivot to /054` |
| PATH C-clean | `iter-v3/053 \| hurst_drift_50_200 UNIVERSAL ADD (cycle 4 #3) \| 1fc6d55 (EDA) \| NEGATIVE-clean \| IS Δ -X / OOS Δ -Y / ratio Z \| CLOSE axis; pivot to /054` |
| PATH C-suspicious | `iter-v3/053 \| hurst_drift_50_200 UNIVERSAL ADD (cycle 4 #3) \| 1fc6d55 (EDA) \| NEGATIVE-SUSPICIOUS-OOS (4th Category 2 in pattern) \| IS-OOS ratio Z OUT-OF-BAND \| CLOSE axis; pivot to /054` |
| PATH D (NULL-RESULT) | `iter-v3/053 \| hurst_drift_50_200 UNIVERSAL ADD (cycle 4 #3) \| 1fc6d55 (EDA) \| EXPLORATION-NULL-RESULT (LEARNED but no decisive effect) \| IS Δ in (-0.10, +0.05) / OOS Δ in (-0.20, +0.20) \| PARK; retest at CONFIRMATION` |

---

## Section 9 — Library Stack Declaration

Pinned via `pyproject.toml` (UNCHANGED from /052):

```
lightgbm == 4.6.0
optuna == 4.8.0
numpy == 2.2.6
pandas == 3.0.0
scikit-learn == 1.8.0
scipy == 1.17.0
statsmodels == 0.14.6
pyarrow == 23.0.1
mlfinlab == 1.4 (fallback: mlfinpy)
pypbo
fracdiff >= 0.10
```

No new dependencies introduced at iter-v3/053. The candidate feature `hurst_drift_
50_200` uses only numpy + pandas arithmetic on existing parquet columns (no new
library imports).

Python version: 3.13+.

---

## Section 10 — QR Audit Trail (per `feedback_v3_axis_selection_quant_discipline.md`)

**EDA-DRIVEN FRAMING: Orchestrator pick PRELIMINARILY supported but REFRAMED per
QR EDA per `feedback_v3_axis_selection_quant_discipline.md` rule 3-4.**

### 10.1 — Setup commit SHA backfill

Setup commit SHA: `abc52dc` — `feat(iter-v3/053): SWAP hurst_drift_50_200 in / regime_momentum_signed_3d out of V3_FEATURE_COLUMNS_TOP_N` (fix: `d16d7bb` — stale 3d MUST-BE-PRESENT check in _verify_feature_columns)

### 10.2 — EDA commit SHA

**EDA SHA**: `1fc6d55` — `analysis(iter-v3/053): hurst_drift_50_200 EDA — pre-falsifier
discovered`

Located at `analysis/iteration_v3-053/`:
- `hurst_drift_50_200_eda.py` — 6-axis EDA script (compute + ADF + IC + univariate
  + linear redundancy + distribution)
- `axis1_compute_and_distribution.csv` — distribution stats per symbol
- `axis2_adf_per_symbol.csv` — ADF stationarity (all 4 syms p<<0.05)
- `axis3_ic_matrix.csv` — full IC matrix vs 14 features + hurst_200
- `axis3_top_ic_pairs.csv` — top 20 |IC| pairs (carve-out check)
- `axis4_univariate_spearman.csv` — ρ vs forward 1-bar return + sister features
- `axis5_linear_redundancy.csv` — **R²=1.0 LINEAR REDUNDANCY (CRITICAL PRE-FALSIFIER)**
- `axis6_per_symbol_distribution.csv` — per-symbol distribution comparison
- `synthesis.md` — markdown summary + axis ranking
- `candidate_axes_ranking.md` — final ranking (sister doc)

### 10.3 — Orchestrator pick PRELIMINARILY SUPPORTED

**The orchestrator pick (per /052 closeout HIGH-priority #1 + Critic FINAL `34cc46f`
Recommendation #2) stated:**

> "regime_momentum family is exhausted at universal single-seed EXPLORATION scope.
> Cycle 4 #3 should pivot to structurally distinct feature family per
> `feedback_v3_structural_over_knob_exploration.md`. Top recommendation:
> `hurst_drift_50_200` (/051 EDA candidate #4); secondary: CatBoost head-to-head
> (NEW model architecture per /050 Critic recommendation)."

The orchestrator's reasoning was:
- /051 EDA candidate #4 (the original deferred-on-cost ranking)
- Category 1 NEW feature family (structurally distinct from regime_momentum)
- Bounded by construction (ADF stationary trivially)
- Different primitive than regime_momentum (Hurst-diff vs ret × sign(Hurst))

**This reasoning is PRELIMINARILY SUPPORTED** — the candidate IS a Category 1
NEW feature family in the structural sense, distinct from regime_momentum.

### 10.4 — QR EDA reveals 3 pre-falsifiers (REFRAMING required)

**The /053 QR EDA at SHA `1fc6d55` produced numerical evidence on the candidate
that was NOT available at the /051 EDA (where hurst_drift_50_200 was DEFERRED on
implementation cost without compute being run):**

1. **Linear redundancy R²=1.0 EXACT** across all 4 symbols (axis5_linear_redundancy.csv).
   `hurst_drift_50_200 = hurst_100 − hurst_diff_100_50 − hurst_200` by algebraic
   identity. Tree models with depth-3 splits on (H100, HDIFF, H200) can approximate
   via axis-aligned hyperrectangles but NOT exactly. The composed feature presents
   a SINGLE pre-aggregated number that may improve `colsample_bytree` efficiency
   at LOW Optuna budget — but at /053's single-seed n_trials=35, Optuna may prefer
   the 3 source primitives.

2. **Univariate Spearman ρ NOT SIGNIFICANT** at p<0.05 in any of 4 symbols
   (axis4_univariate_spearman.csv). Mean ρ +0.0114 — the WEAKEST univariate signal
   of any v3 Category 2 candidate tested or queued. Compare:
   - regime_momentum_signed_5d (MERGED edge ingredient): TRX significant at -0.039
   - regime_momentum_signed_3d (CLOSED at /052): mean -0.057, significant ALL 4
   - fracdiff_d05_close (PARKED at /051): mean -0.044, significant ALL 4
   - **hurst_drift_50_200 (THIS BRIEF): mean +0.0114, significant NONE of 4**

3. **Max |IC| 0.85-0.88 with hurst_diff_100_50** (source primitive) across all 4
   symbols (axis3_top_ic_pairs.csv). EXCEEDS prior 5 Category 2 candidates in v3
   history. Category 2 carve-out applies mechanically per `feedback_v3_engineered_
   feature_pivot.md` but does unprecedented work.

### 10.5 — QR DECISION: PROCEED under REFRAMED HYPOTHESIS B

Per `feedback_v3_axis_selection_quant_discipline.md` rule 5: "Speculative pivots
without analysis are forbidden. 'Let's try X' is not enough; 'Let's try X because
EDA shows the IS bottleneck is Y, and X has mechanism Z that targets Y' is
required."

The QR EDA at SHA `1fc6d55` produced numerical evidence — three pre-falsifiers.
The remaining decisions are:
- **OPTION A**: REJECT the orchestrator pick (per the 3 pre-falsifiers). PIVOT to
  alternative axis. **Alternatives evaluated**:
  - CatBoost head-to-head: implementation cost 4-8h (new strategy class analogous
    to lgbm.py at 722 LOC). **OOB for 2h EXPLORATION cap.** Defer to dedicated
    CONFIRMATION-scope.
  - DSR gate reformulation: methodology axis (not edge ingredient). Doesn't test
    feature/model/risk change. Defer to standalone Critic-spec change.
  - Per-symbol drawdown brake: untested NEW risk primitive. Implementation cost
    ~1.5h. Viable BUT cycle 4 #3 was specifically mandated by /052 closeout to
    be a NEW feature family (Category 1 priority per `feedback_v3_structural_
    over_knob_exploration.md`). Defer to /054.
- **OPTION B**: PROCEED with the orchestrator pick under REFRAMED HYPOTHESIS B —
  document the Linear Redundancy Pre-Falsifier (LR-PF) methodology. **CHOSEN.**

**QR DECISION**: PROCEED with hurst_drift_50_200 as /053 axis under REFRAMED
HYPOTHESIS B. The EXPLORATION's primary value at PATH B PROMISING-INERT (55% prob)
is to DOCUMENT the Linear Redundancy Pre-Falsifier (LR-PF) methodology — an EDA-time
guard against INERT-OVERFIT outcomes for future Category 2 composed-feature axis
selections. The methodology improvement compounds across all subsequent NEW
Category 2 composed-feature axis selections.

If PATH A (5% prob) fires: the LR-PF methodology is FALSIFIED (composed features
CAN provide incremental discrimination even at R²=1.0 linear redundancy with
source primitives). This is a less-likely but still informative outcome.

### 10.6 — Single-axis discipline

UNCHANGED:
- ONE feature SWAPS (15th slot: 3d → hurst_drift_50_200)
- Net feature count UNCHANGED at 15
- V3_MODELS UNCHANGED (3-sym BCH+LDO+TRX)
- REQUIRED_GAP UNCHANGED at 66
- No risk-gate threshold changes
- No labeling parameter changes
- No model architecture changes

---

## Section 11 — References

### 11.1 — EDA and brief artifacts

- `analysis/iteration_v3-053/hurst_drift_50_200_eda.py` — 6-axis EDA script (SHA `1fc6d55`)
- `analysis/iteration_v3-053/axis1_compute_and_distribution.csv` — distribution stats
- `analysis/iteration_v3-053/axis2_adf_per_symbol.csv` — ADF stationarity
- `analysis/iteration_v3-053/axis3_ic_matrix.csv` — full IC matrix
- `analysis/iteration_v3-053/axis3_top_ic_pairs.csv` — top 20 |IC| pairs
- `analysis/iteration_v3-053/axis4_univariate_spearman.csv` — Spearman ρ vs forward returns
- `analysis/iteration_v3-053/axis5_linear_redundancy.csv` — **R²=1.0 linear redundancy (CRITICAL PRE-FALSIFIER)**
- `analysis/iteration_v3-053/axis6_per_symbol_distribution.csv` — per-symbol distribution
- `analysis/iteration_v3-053/synthesis.md` — markdown summary + axis ranking
- `analysis/iteration_v3-053/candidate_axes_ranking.md` — final ranking sister doc

### 11.2 — Source files (post-/053 setup)

- `src/crypto_trade/features_v3/engineered_v3.py` — NEW `compute_hurst_drift_50_200` (~20 LOC)
- `src/crypto_trade/features_v3/__init__.py:V3_FEATURE_COLUMNS_TOP_N` — SWAP 15th slot
- `run_baseline_v3.py:ITERATION_LABEL` = "v3-053"
- `run_baseline_v3.py:_verify_feature_columns` — assertions updated
- `tests/features_v3/test_hurst_drift_50_200_universal.py` — 5 NEW adversarial tests

### 11.3 — Predecessor briefs and diaries

- `briefs-v3/iteration_v3-052/research_brief.md` — predecessor (regime_momentum_signed_3d SWAP)
- `diary-v3/iteration_v3-052.md` — predecessor closeout (EXPLORATION-NEGATIVE PATH C-suspicious; CLOSED 3d UNIVERSAL)
- `briefs-v3/iteration_v3-051/research_brief.md` — fracdiff_d05_close PARKED (NULL-RESULT)
- `analysis/iteration_v3-051/synthesis.md` — /051 EDA where hurst_drift_50_200 first DEFERRED on impl cost (line §c2)
- `analysis/iteration_v3-052/synthesis.md` — /052 EDA LDO removal supersession

### 11.4 — Memory rules cited

- `feedback_v3_axis_selection_quant_discipline.md` — QR-EDA mandate; orchestrator may not commit setup ad-hoc
- `feedback_v3_engineered_feature_pivot.md` — Category 2 IC carve-out vs source primitives
- `feedback_v3_engineered_features_proven.md` — composed features CAN work; 5d at /025+/028 precedent
- `feedback_v3_engineered_features_dont_stack.md` EXPANDED 2026-05-11 — sister stacking at any IC
- `feedback_v3_inert_features_at_higher_budget.md` — INERT features at higher Optuna budget HARM OOS
- `feedback_v3_structural_over_knob_exploration.md` — Category 1 NEW feature family priority
- `feedback_v3_strict_10_to_1_cadence.md` — cycle 4 #3 of 10 EXPLORATIONs
- `feedback_v3_exploration_n_trials_35.md` — n_trials=35 EXPLORATION default
- `feedback_v3_strict_both_is_oos_baseline.md` — BOTH-must-improve at CONFIRMATION
- `feedback_v3_dsr_mode_artifact.md` — EXPLORATION-mode DSR informational only
- `feedback_v3_single_seed_frozen_baseline.md` REVISED 2026-05-11 — feature_columns change perturbs Optuna
- `feedback_no_cheating.md` — pre-registered paths LOCKED; no post-hoc renegotiation
- `feedback_v3_axis_saturation_predictor.md` — behavioral-effect predictor with falsifier

### 11.5 — BASELINE_V3.md anchor

- iter-v3/028 multi-seed mean: IS +0.5101 / OOS +0.5053 (regime_momentum_signed_5d edge ingredient)
- iter-v3/053 anchors against THIS baseline (multi-seed iter-v3/028), per BASELINE_V3.md §"Anchor Comparison Cheat-Sheet"

---

## Section 12 — Brief Validation Checklist (Pre-Phase-5.5)

| # | Section | Required content | Present? |
|---|---|---|---|
| 0 | Data Split Declaration | OOS_CUTOFF_DATE, training_months, ENSEMBLE_SIZE, n_trials, OOS_CUTOFF_MS | ✓ |
| 0.5 | Iteration Type Declaration | TYPE, Cycle position, wall-clock, run spec, carry-forward, axis, setup changes, predicted classification | ✓ |
| 1 | Hypothesis | Mechanism, predicted bands, IS+OOS Δ, IS-OOS ratio band, trade count bands, importance rank prediction | ✓ |
| 2 | IS-Only Numerical Evidence | ADF, IC matrix, univariate Spearman, linear redundancy, distribution stats, summary | ✓ |
| 3 | Proposed Changes | V3_FEATURE_COLUMNS_TOP_N SWAP, V3_MODELS, risk gate config, REQUIRED_GAP, ITERATION_LABEL, source code, tests, dead-code retention | ✓ |
| 4 | Expected OOS Impact | Predicted bundle metrics, behavioral-effect predictor, SWAP-axis importance-rank-ONLY trigger, saturation falsifier, stacking risk | ✓ |
| 5 | Risk Mitigation | Pre-falsifier mitigations, R1-R5 primitives, IS-calibrated thresholds | ✓ |
| 6 | Risk Management Design | 10-primitive gate table | ✓ |
| 7 | Pre-Registered Failure-Mode Prediction | Single most likely failure mode + 5-path taxonomy + Optuna sanity checks | ✓ |
| 8 | Pre-Registered MERGE/NO-MERGE Numerical Criteria | 5 LOCKED paths (A/B/C-clean/C-suspicious/D) + numerical thresholds + BOTH-must-improve + DSR-INFORMATIONAL + catalog row pre-commits | ✓ |
| 9 | Library Stack Declaration | Pinned versions; no new deps | ✓ |
| 10 | QR Audit Trail | EDA SHA, orchestrator pick assessment, 3 pre-falsifiers, QR decision (REFRAMED HYPOTHESIS B), single-axis discipline | ✓ |
| 11 | References | EDA artifacts, source files, predecessor briefs/diaries, memory rules, BASELINE anchor | ✓ |
| 12 | Brief Validation Checklist | This table | ✓ |

**All 12 sections present.** Brief is COMPLETE and ready for Phase 5.5 gate review
by Engineer.
