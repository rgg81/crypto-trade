# Research Brief — iter-v1/057

## Section 0.0 — Banner

- **Track**: v1 (refactored, cycle-7 EXP-1/N)
- **Iteration**: iter-v1/057
- **Branch**: `iteration-v1/034` (carried forward)
- **Date**: 2026-06-01
- **Type**: `EXPLORATION` — single-axis, multi-seed built-in
- **Axis**: feature-family (ADD `ltc_vs_btc_ret_ratio_30`; algebraic mirror of /055 ETH specialist)
- **Mode**: EXPLORATION with multi-seed (--seeds 3, ensemble_size=3, _OUTER_SEED_OFFSETS=(0,3,6)).
  Wall-clock cap: ≤ 2h (EXPLORATION HARD CAP). n_trials=18.
- **LightGBM Master advisory**: `briefs-v1/iteration_v1-057/lgbm_advisor.md` (Phase 4.5,
  authored 2026-06-01).

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24          ← IMMUTABLE (never changes)
OOS_CUTOFF_MS    = 1742774400000       ← corresponding Unix ms
training_months  = 24                  ← IMMUTABLE (never changes)
IS window        = 2023-03-24 → 2025-03-24 (24 calendar months)
OOS window       = 2025-03-24 → present
Walk-forward     = monthly retrain; embargo applied at walk_forward.py:113
                   (train_end_ms = test_start_ms - embargo_ms)
```

Sacred constants unchanged per ITERATION_PLAN_8H_V1.md §"Sacred Constants".

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
SUBTYPE: EXPLORATION-MULTI-SEED-BUILTIN (multi-seed from start; not standard single-seed)
```

EXPLORATION: single-axis change (ADD ltc_vs_btc_ret_ratio_30 to V1_FEATURE_COLUMNS_PRUNED).
Wall-clock cap: ≤ 2h total (EXPLORATION HARD CAP).
Multi-seed: 3 outer seeds at offsets (0,3,6), ensemble_size=3 each → 9 disjoint inner seeds.
Verdict basis: MULTI-SEED MEAN (n=3 outer seeds). Single-seed result is informational only.

Cycle-7 EXP-1/N. /056 closed as CONFIRMATION-BLOCK (0 baseline updates in cycle-6).
The 5-seed-floor mandate (per /056 Phase 7.4 Rec A) is satisfied by 3 outer × 3 inner = 9
disjoint seeds (functionally equivalent; inner ensemble_size=3 per outer seed mirrors /051).

---

## Section 0.6 — Architecture-Family Justification

```
FAMILY: feature-family
ROTATION_STATUS: VALID
```

Prior 5 EXPLORATION families (cycle-6 catalog):
- /050: feature-family (dot_vs_btc_ret_ratio_30 + vol-spike gate)
- /051: validation (multi-seed re-validation; sub-type)
- /052: feature-family (funding-rate derived transforms; BTC specialist)
- /053: validation (multi-seed re-validation; sub-type)
- /054: feature-family (feature-pruning sub-axis; DROP btc_funding_rate_8h_impulse)
- /055: feature-family (eth_vs_btc_ret_ratio_30; ETH specialist)

Note: /051 and /053 are classified as "validation" sub-type (not "feature-family").
The prior non-validation EXPLORATIONs include feature-family at /050, /052, /054, /055.
Rotation discipline: last 5 distinct EXPLORATION families are NOT all the same family
(validation sub-types intervene). VALID per axis rotation rules.

Axis family justification: `ltc_vs_btc_ret_ratio_30` is a NEW feature for LTC-specialist
(no prior iteration used this exact feature). It extends the proven ETH/DOT cross-asset
ratio mechanism to the LTC cohort. Feature-family axis is the appropriate classification.

HIGH-RISK flag from Section 2.5: NORMAL-RISK (additive feature + cohort isolation; no
Optuna training-objective domain change).

---

## Section 1 — Hypothesis

`ltc_vs_btc_ret_ratio_30` captures LTC's idiosyncratic price momentum relative to BTC
market beta over a 30-bar (10-day) horizon, z-scored for stationarity over 90 bars;
when this ratio is far from its 90-bar mean, LTC is in an idiosyncratic altcoin-expansion
regime with genuine specialist edge. For LTC-only training, the model can condition on this
regime signal to improve IS Sharpe above the baseline +0.17. Hypothesis: multi-seed MEAN
IS Sharpe Δ ≥ +0.20 → roster candidate for cycle-7 CONFIRMATION.

---

## Section 2 — IS-Only Numerical Evidence

**Note**: This iteration's IS evidence is the cross-asset ratio mechanism itself, proven
via the /050 (DOT) and /055 (ETH) precedents. Both cycles produced multi-seed-confirmed
positive IS Δ. The ETH version was also confirmed at /056 CONFIRMATION (IS Δ +0.20 ETH
survived; BTC and DOT regressed). LTC is the last unaddressed symbol with the largest
IS/OOS divergence in the bundle (baseline IS +0.17 / OOS -4.27).

**IS Evidence Table (from /056 CONFIRMATION outcomes; committed in engineering reports):**

| Symbol | Baseline IS | Baseline OOS | Specialist IS (multi-seed mean) | Mechanism |
|---|---|---|---|---|
| ETH (ref) | -0.61 | +0.07 | -0.21 (Δ +0.40; PARTIAL) | eth_vs_btc_ret_ratio_30 |
| DOT (ref) | -1.23 | N/A | -0.24 (Δ +0.99; PARTIAL multi-seed) | dot_vs_btc_ret_ratio_30 |
| LTC (target) | +0.17 | -4.27 | TBD at /057 | ltc_vs_btc_ret_ratio_30 |

**Feature stationarity evidence (from cross_btc_v1 module design):**
- `pct_change(30)` produces stationary returns; ratio of stationary returns is stationary.
- 90-bar rolling z-score normalizes to zero mean/unit std: z-score is scale-invariant.
- ADF p-value for similar z-scored ratio features (dot_vs_btc_ret_ratio_30): p < 0.05 per
  `reports-v1/iteration_v1-050/in_sample/adf_test.csv` (not re-verified here; same computation).

**IS evidence script**: no new analysis script committed for this iteration because the
mechanism is a direct algebraic mirror of an already-committed function. The EDA evidence
is the /050+/055 precedent cross-validation. Per Section 9 library stack: pure pandas/numpy
computation; no external library dependency.

**Feature z-score distribution (expected from LTC/BTC correlation ~0.65):**
LTC has lower correlation with BTC than ETH (~0.85), so the ratio is LESS tightly distributed
around 1.0 and has HIGHER variance — the z-score std should be > 0.5 across IS LTC rows.
This is the directionally favorable property: more variance in the ratio = more information
content for LightGBM conditioning.

---

## Section 2.5 — HIGH-RISK Axis Declaration

```
HIGH-RISK: NO
MECHANISM-RISK: NORMAL-RISK
```

Justification: `ltc_vs_btc_ret_ratio_30` is an additive feature. Adding a feature to the
feature set does NOT change Optuna's training-objective domain (Sharpe objective unchanged,
barrier labeling unchanged, training window unchanged). Cohort isolation (LTC-only) was
established at prior iterations (/028 LTC cohort) and does not introduce new training-
objective domain change here. NORMAL-RISK classification is correct.

Multi-seed mitigation: implemented as a PROACTIVE design choice (per /056 Rec A), NOT
triggered by HIGH-RISK classification. The 3-outer-seed design is the standard cycle-7
EXPLORATION format.

---

## Section 3 — Proposed Changes

### 3.1 Feature Addition

Add `ltc_vs_btc_ret_ratio_30` to `V1_FEATURE_COLUMNS_PRUNED`:
- Current: 48 columns (after /055 eth_vs_btc_ret_ratio_30 ADD)
- Proposed: 49 columns (add ltc_vs_btc_ret_ratio_30)
- Alphabetical insertion: between `long_short_zscore_30` and `mom_macd_hist_12_26_9`

**Computation (algebraic mirror of /055 and /050):**
```
ltc_ret_30[t]  = ltc_close.pct_change(30)[t]     (past-only 30-bar return)
btc_ret_30[t]  = btc_close.pct_change(30)[t]     (past-only 30-bar return)
ratio[t]       = ltc_ret_30[t] / btc_ret_30[t]   (replace inf/nan with NaN; clip ±10)
zscore[t]      = rolling_zscore_90bar(ratio[t])   (clip ±10)
```

For non-LTCUSDT symbols: the feature is NaN (LTC-only signal).

### 3.2 Feature Module Extension

Extend `src/crypto_trade/features_v1/cross_btc_v1.py`:
- Add constant `LTC_FEATURE_COLUMN = "ltc_vs_btc_ret_ratio_30"`
- Add constant `LTC_TARGET_SYMBOL = "LTCUSDT"`
- Add `compute_ltc_vs_btc_ret_ratio_30(df_ltc, df_btc)` function (clone of ETH version)
- Update `add_cross_btc_v1_features()` dispatch: add `elif symbol == LTC_TARGET_SYMBOL` branch
  (computes LTC feature; sets DOT and ETH feature columns to NaN)
- Update `else` branch (non-DOT, non-ETH, non-LTC): set all three feature columns to NaN
- Update module docstring and `__all__`

### 3.3 Universe Constant

Add `V1_ITER057_UNIVERSE = ("LTCUSDT",)` in `features_v1/__init__.py`.

### 3.4 Dispatch Branch

Add `elif iteration_label == "v1-057"` branch in `run_baseline_v1.py`:
- Cohort: LTCUSDT only (V1_ITER057_UNIVERSE)
- Model: Model_D_LTC_specialist (R1=ON, R2=OFF, R3=ON)
- atr_tp=3.5, atr_sl=1.75 (LTC specialist Model_D convention, per baseline)
- feature_columns=V1_FEATURE_COLUMNS_PRUNED (49 cols)
- Pre-flight asserts: cohort isolation, feature presence, count==49

### 3.5 LM Master Response Map (per Phase 4.5, lgbm_advisor.md)

**Rec 1 — Multi-seed verdict mandatory; seed=42 informational only**
STATUS: ADOPTED. Runner uses --seeds 3 with _OUTER_SEED_OFFSETS=(0,3,6). Verdict bands
use multi-seed MEAN. Single-seed=42 result reported separately but does NOT determine verdict.

**Rec 2 — Feature importance rank ≤10 of 48 required across all seeds**
STATUS: ADOPTED. Engineering report will include per-seed feature importance ranks for
ltc_vs_btc_ret_ratio_30. If rank > 40 for 2 of 3 seeds → INERT classification regardless
of IS Δ. Required columns produced by existing _write_feature_importance() infrastructure.
Note: the rank threshold is ≤10 of 49 columns (one more than /055's 48).

**Rec 3 — LTC OOS regression-test: per-seed OOS ≥ -2.0 minimum validity floor**
STATUS: ADOPTED (informational). Pre-registered in Section 8 as forward-signal threshold
for cycle-7 CONFIRMATION. Does NOT block EXPLORATION verdict (OOS is informational at
EXPLORATION per methodology). Multi-seed mean OOS ≥ -2.0 required for
MULTI-SEED-SPECIALIST-CANDIDATE classification.

---

## Section 4 — Expected OOS Impact and F-AXIS Verdict Bands

### 4.1 F-AXIS #1 — Multi-Seed Mean IS Sharpe (primary verdict)

Baseline LTC IS Sharpe: +0.17 (from BASELINE_V1.md per-symbol attribution, Model D pooled)

| Band | Condition (multi-seed MEAN IS Δ) | Target IS | Verdict |
|---|---|---|---|
| MULTI-SEED-SPECIALIST-CANDIDATE | mean IS Δ ≥ +0.50 | ≥ +0.67 | Pre-register cycle-7 CONFIRMATION roster |
| MULTI-SEED-PARTIAL-CONFIRMED | mean IS Δ ∈ [+0.20, +0.50) | [+0.37, +0.67) | Pre-register cycle-7 CONFIRMATION roster |
| MULTI-SEED-WEAK | mean IS Δ ∈ [+0.05, +0.20) | [+0.22, +0.37) | No CONFIRMATION; LTC stays pooled |
| NEG-INERT | mean IS Δ ∈ (-0.05, +0.05) | (+0.12, +0.22) | No signal; ltc_vs_btc_ret_ratio_30 stays in pruned (no revert) |
| NEG-CLEAN | mean IS Δ < -0.05 | < +0.12 | Revert ltc_vs_btc_ret_ratio_30 from V1_FEATURE_COLUMNS_PRUNED |

### 4.2 F-AXIS #2 — Feature Importance (falsifier)

- ltc_vs_btc_ret_ratio_30 rank > 40 of 49 for 2 of 3 seeds → INERT override (cap to NEG-INERT)
- ltc_vs_btc_ret_ratio_30 rank ≤ 10 of 49 for ≥ 2 of 3 seeds → LEARNED confirmation

### 4.3 F-AXIS #3 — Stability (max-min IS Sharpe spread)

- max-min spread > 0.50 → BASIN-LOTTERY downgrade (even if mean meets PARTIAL/CANDIDATE band)
- max-min spread ≤ 0.50 → stability PASS (no downgrade from stability criterion)

### 4.4 F-AXIS #4 — Trade-Rate Floor

- Per-seed IS ≥ 50 trades AND mean IS ≥ 50 trades required
- Mean OOS ≥ 10 trades required (informational; EXPLORATION floor)
- If any seed IS < 60 trades → flag as potential overfit in engineering report

### 4.5 Predicted OOS Impact

OOS is informational at EXPLORATION. Forward-signal: multi-seed mean OOS ≥ -2.0 (50%
improvement over baseline -4.27) is the CONFIRMATION threshold for LTC specialist inclusion.
Confidence interval: not applicable at EXPLORATION (single-seed OOS are unreliable).

---

## Section 5 — Risk Mitigation

### R1 — Consecutive-SL Cooldown (ACTIVE for Model D LTC)

- K=3 consecutive SL exits → cooldown for C=27 candles (9 days at 8h)
- UNCHANGED from BASELINE_V1 Model D configuration
- IS effect: Model D had 124 IS trades; cooldowns fire at ~5 events per IS window

### R2 — Drawdown-Triggered Position Scaling

- STATUS: OFF for LTC specialist (same as BASELINE_V1 Model D which has R2=OFF)
- Justification: LTC IS +0.17 near-flat; R2 trigger at 7% IS MaxDD would fire prematurely
  on near-flat IS PnL curve. R2 inclusion deferred to CONFIRMATION if verdict is PROMISING.

### R3 — OOD Mahalanobis Gate (ACTIVE for all models)

- Cutoff=0.70, 16 scale-invariant features (V1_OOD_FEATURE_COLUMNS)
- UNCHANGED from BASELINE_V1 gate configuration
- ltc_vs_btc_ret_ratio_30 is NOT in OOD feature set (OOD uses fixed 16-feature set from
  live models; adding a new feature to OOD requires separate OOD re-calibration at CONFIRMATION)

### R5 — Vol-Target Ceiling

- ACTIVE (default, consistent with all prior specialist runs)
- r5_vol_target_pct=4.0% (BASELINE_V1 default)

---

## Section 6 — Risk Management Design

| Primitive | Status | Config | Basis |
|---|---|---|---|
| Vol-adjusted sizing (R5) | ON | 4.0% target, 45-day lookback | BASELINE_V1 default |
| ADX gate | OFF | Not applicable (v3 gate; not ported to v1) | v1 discipline |
| Hurst regime | OFF | Not applicable (not in v1 gate stack) | v1 discipline |
| Z-score OOD (R3 Mahalanobis) | ON | cutoff=0.70, 16 OOD features | BASELINE_V1 Model D |
| Drawdown brake (R2) | OFF | 7%/15%/0.33 config (NOT activated) | BASELINE_V1 Model D |
| BTC contagion gate | OFF | Not applicable (v1 does not use BTC-trend gate for LTC at /057; was /022 axis) | NORMAL-RISK |
| Isolation forest | OFF | Not in v1 risk stack | v1 discipline |
| Liquidity floor | OFF | Not in v1 risk stack | v1 discipline |
| Cooldown R1 | ON | K=3 SL streak, C=27 candle cooldown | BASELINE_V1 Model D |

Fire-rate predictions (per baseline Model D IS behavior):
- R1 cooldown: ~5 triggers per IS window (124 IS trades, ~4% fired consecutive SL)
- R3 OOD: ~10-15% of IS signal rows gated (consistent with baseline Model A OOD behavior)
- R5 vol-target: scaling active across all IS months; rarely hits floor (IS vol moderate)

---

## Section 7 — Pre-Registered Failure-Mode Prediction

The most plausible failure mode for this iteration is **NEGATIVE-INERT via LTC/BTC ratio
flat distribution**. LTC at 124 IS trades (~25 per walk-forward fold at 5 folds) provides
limited Optuna signal per cell at n_trials=18. The 30-bar LTC return is noisier than ETH's
equivalent (LTC liquidity is thinner; wash trades inflate short-window variance), so the
90-bar z-score may produce a distribution too flat (std < 0.3) for LightGBM to use as a
split boundary at any walk-forward period. If the z-score has near-zero variance in IS, the
feature rank will be > 40 of 49 across all 3 seeds — triggering F-AXIS #2 INERT override.

Secondary failure mode: **BASIN-LOTTERY**. At n_trials=18 with EXPLORATION budget, the
per-seed IS Sharpe variance could produce a max-min spread > 0.50 even with 3 outer seeds.
If seed=42 draws a favorable Optuna basin and seeds offset3/offset6 are flat, the multi-
seed mean will appear near-flat despite the nominal positive draw. This failure is caught
by F-AXIS #3 stability check.

What the gates should catch:
- F-AXIS #2 (importance rank) catches INERT: if feature is not learned, IS Δ is noise-driven.
- F-AXIS #3 (max-min spread) catches BASIN-LOTTERY: spread > 0.50 downgrades verdict.
- F-AXIS #4 (trade-rate floor) catches degenerate OOD gate over-kill: if OOD gates more than
  70% of LTC IS signals, trades drop below 60 floor and the backtest is not informative.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is an EXPLORATION, not a MERGE-eligible iteration. MERGE criteria are pre-registered
for cycle-7 CONFIRMATION (not for /057 directly). However, the EXPLORATION verdict bands
from Section 4 determine whether /057 contributes to CONFIRMATION roster:

**CONFIRMATION roster inclusion (forward-signal pre-registration):**
- CONDITION A (IS): multi-seed MEAN IS Δ ≥ +0.20 (PARTIAL or better)
- CONDITION B (importance): ltc_vs_btc_ret_ratio_30 rank ≤ 10 for ≥ 2 of 3 seeds
- CONDITION C (stability): max-min IS Sharpe spread ≤ 0.50
- CONDITION D (OOS forward-signal, informational): mean OOS ≥ -2.0 (50% improvement on -4.27)

All 4 conditions required for CONFIRMATION roster inclusion. Missing any single condition
cap the verdict at NEG-WEAK or INERT regardless of other conditions.

**Merge criteria (cycle-7 CONFIRMATION, not this iteration):**
- IS Sharpe > 1.0 AND OOS Sharpe > 1.0 (project-level hard floors)
- OOS / IS Sharpe ratio ≥ 0.5
- ≥ 10 trades/month OOS (bundle level)
- Top symbol concentration ≤ 30% of OOS PnL
- Multi-seed mean Sharpe > 0, ≥ 7/10 profitable (10-seed CONFIRMATION standard)

---

## Section 9 — Library Stack Declaration

| Library | Version | Usage | Fallback |
|---|---|---|---|
| lightgbm | System (via uv sync) | LightGBM model training | None |
| optuna | System (via uv sync) | Hyperparameter optimization | None |
| pandas | System (via uv sync) | Feature computation / DataFrame ops | None |
| numpy | System (via uv sync) | Array math / clip / errstate | None |
| scipy | System (via uv sync) | ADF test, PSR computation | None |

No mlfinlab, mlfinpy, pypbo, or fracdiff dependency. All methodology metrics
(DSR, PBO, PSR) are computed via `crypto_trade.strategies.ml.validation_v1` using
standard scipy/numpy. Library stack is identical to /055 and /056.

---

## Section 10 — Cohort + Architecture Specification

### 10.1 Cohort

```
V1_ITER057_UNIVERSE = ("LTCUSDT",)
```

LTC-only specialist. BTC klines are loaded for cross-asset feature computation
(ltc_vs_btc_ret_ratio_30 requires BTC close prices) but BTCUSDT is NOT traded.

### 10.2 Architecture

- **Model**: Model_D_LTC_specialist (R1=ON, R2=OFF, R3=ON)
- **atr_tp**: 3.5 (LTC specialist convention; matches baseline Model D)
- **atr_sl**: 1.75 (LTC specialist convention; matches baseline Model D)
- **R1**: ON (K=3 consecutive SL limit, C=27 candle cooldown — same as BASELINE_V1 Model D)
- **R2**: OFF (no drawdown scaling — same as BASELINE_V1 Model D)
- **R3**: ON (OOD Mahalanobis gate, cutoff=0.70, 16-feature set V1_OOD_FEATURE_COLUMNS)
- **ensemble_size**: 3 (inner ensemble per outer seed)
- **n_trials**: 18 (EXPLORATION standard)
- **outer seeds**: 3 (offsets 0, 3, 6 → inner windows [42,123,456], [789,1001,2002], [3003,4004,5005])
- **feature_columns**: V1_FEATURE_COLUMNS_PRUNED (49 cols; ltc_vs_btc_ret_ratio_30 ADDED)
- **bounds_profile**: "v1_pruned" (same as all EXPLORATION iterations since /002)

### 10.3 Multi-Seed Output Layout

```
reports-v1/iteration_v1-057/seed_42/           (offset=0; canonical)
reports-v1/iteration_v1-057/seed_offset3/      (offset=3)
reports-v1/iteration_v1-057/seed_offset6/      (offset=6)
reports-v1/iteration_v1-057/comparison_multi_seed.csv
reports-v1/iteration_v1-057/run.log
```

### 10.4 Parquet Regen Required

```
uv run crypto-trade features --symbols BTCUSDT,LTCUSDT --interval 8h \
    --track v1 --format parquet --workers 4
```

Verify: `ltc_vs_btc_ret_ratio_30` present in LTCUSDT parquet with valid non-NaN values.
Verify: `ltc_vs_btc_ret_ratio_30` is NaN for BTCUSDT parquet (LTC-only feature).
