# Research Brief — iter-v1/058
# BTC OI-Delta Short-Window Specialist

**Branch**: `iteration-v1/034` (worktree: quant-research)
**Date authored**: 2026-06-02
**Iteration type**: EXPLORATION — cycle-7 EXP-2/N

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` (UNCHANGED — sacred constant)
- `training_months = 24` (UNCHANGED — sacred constant)
- **IS window**: 2023-03-24 → 2025-03-23 inclusive (24 calendar months)
- **OOS window**: 2025-03-24 → present (live evaluation; approximately 15 months at run time)

These constants are pinned. This brief does NOT propose changing either constant.

---

## Section 0.5 — Iteration Type Declaration

**TYPE: EXPLORATION**

- Single-axis change: NEW feature `btc_oi_delta_5_z30` (5-bar OI delta, 30-bar z-score window)
- Single-cohort: `("BTCUSDT",)`
- Wall-clock budget: ≤ 2 hours (EXPLORATION standard)
- Multi-seed built-in: `--seeds 3` at `ENSEMBLE_SIZE=3`, `_OUTER_SEED_OFFSETS=(0, 3, 6)`
- Verdict basis: **MULTI-SEED MEAN (n=3 outer seeds)**. Single-seed=42 result is informational only.

---

## Section 0.6 — Architecture-Family Justification

**FAMILY: feature-family**

Rationale: `btc_oi_delta_5_z30` is a NEW open-interest derived feature at a different frequency
bin than the existing `oi_delta_30_z90` (5-bar delta + 30-bar z-score vs 30-bar delta + 90-bar
z-score). The axis targets the OI primitive cluster (same data source, different parameterization).
This is an axis-adjacent exploration within the feature-family axis per /025 precedent.

**Last 5 EXPLORATION axis families** (from exploration_catalog.md):
1. iter-v1/057 — feature-family (ltc_vs_btc_ret_ratio_30; BASIN-LOTTERY)
2. iter-v1/055 — feature-family (eth_vs_btc_ret_ratio_30; PROMISING)
3. iter-v1/054 — feature-family (btc_funding_rate_8h_impulse DROP; POSITIVE attribution)
4. iter-v1/053 — validation (BTC multi-seed re-validation)
5. iter-v1/052 — feature-family (btc funding-rate derived transforms)

Three of the last 5 are feature-family, but NOT all 5 consecutive — rotation rule is NOT violated.

**ROTATION_STATUS: VALID**

---

## Section 1 — Hypothesis

`btc_oi_delta_5_z30` (5-bar OI % change z-scored over 30 bars) captures rapid BTC institutional
positioning shifts at the 40h horizon not present in the existing `oi_delta_30_z90` (240h slow
accumulation signal), enabling a BTC-specialist LightGBM model to discover a decision boundary
inaccessible to the pooled Model A, improving BTC IS Sharpe from the baseline −0.85 by a mean
multi-seed Δ of ≥ +0.20 (toward −0.65 or better).

---

## Section 2 — IS-Only Numerical Evidence

**Committed analysis script**: `analysis/iteration_v1-058/oi_delta_5_eda.py`

### 2.1 Baseline BTC Statistics (BASELINE_V1.md anchors)

| Metric | Value |
|---|---|
| BTC IS Sharpe (pooled Model A) | −0.85 |
| BTC OOS Sharpe | +3.41 |
| BTC IS trades | 113 |
| BTC OOS trades | ~38 |

BTC has the largest IS-headroom (IS −0.85 is the most negative IS Sharpe in the bundle), making
it the highest-priority specialist target for cycle-7.

### 2.2 Feature Design Rationale

`btc_oi_delta_5_z30` computation:

```
delta_5[t]          = (oi[t] - oi[t-5]) / oi[t-5]    # 5-bar (~40h) OI % change
delta_5_clipped[t]  = clip(delta_5[t], -1.0, +5.0)    # same clip as oi_delta_30
z30[t]              = zscore(delta_5_shifted_1, window=30)  # past-only 30-bar window
btc_oi_delta_5_z30  = clip(z30[t], -10, +10)
```

Frequency comparison:
| Feature | Delta window | Z-score window | Horizon |
|---|---|---|---|
| `oi_delta_30_z90` (existing) | 30 bars = 240h | 90 bars = 30d | slow macro |
| `btc_oi_delta_5_z30` (NEW) | 5 bars = 40h | 30 bars = 10d | rapid institutional |

### 2.3 IC with Existing Sister Feature

The LM Master (Section Rec 1) estimates Pearson IC between `btc_oi_delta_5_z30` and
`oi_delta_30_z90` ≈ |0.30–0.55| (moderate, not blocking). Per the established sister-IC rule
(v3 analog applied here by v1-parity): IC < 0.80 is NOT a blocking condition. The EDA script
computes and reports this IC; it is informational for the Critic.

### 2.4 OI Data Availability

BTC OI data (`data/open_interest/BTCUSDT/8h.csv`) starts at `open_time=1598918400000`
(2020-09-01 UTC), covering the full IS window (IS start: 2023-03-24). No NaN gaps in the IS
window from missing OI data — the early-window NaN policy (skip months with >50% NaN, per /025
LM Master §5(a)) does NOT fire for BTC IS data.

Burn-in for `btc_oi_delta_5_z30`: first 5 (delta) + 30 (z-score) = 35 rows NaN. This is shorter
than the existing `oi_delta_30_z90` burn-in of 120 rows, so no additional IS training row loss.

### 2.5 Pre-Flight IC Orthogonality Check

IC check gate from /047 + /048 precedents applies for ALL new features. The brief pre-registers
that |IC| with `vol_volume_rel_20` (the highest-risk cluster) is expected to be < 0.30 (OI delta
is not a volume feature). If the analysis script finds |IC| ≥ 0.60 with any existing feature,
this is a BLOCK condition and the iteration should ABORT. Analysis script checks this.

---

## Section 2.5 — HIGH-RISK Axis Declaration

**HIGH-RISK: NO (NORMAL-RISK)**

Rationale: `btc_oi_delta_5_z30` is an additive feature to `V1_FEATURE_COLUMNS_PRUNED` (48 → 49
cols) combined with BTC-only cohort isolation. Neither change modifies Optuna's training-objective
domain (same triple-barrier labels, same Sharpe objective, same walk-forward structure). Per the
established v1 NORMAL-RISK criterion: additive features + cohort isolation without labeling
parameter changes = NORMAL-RISK.

Multi-seed mitigation: opted-in (3 outer seeds, `ENSEMBLE_SIZE=3`) as the primary basin-variance
protection mechanism, per /056 + /057 basin-lottery lessons.

---

## Section 3 — Proposed Changes

### 3.1 Feature Addition

- **ADD** `btc_oi_delta_5_z30` to `V1_FEATURE_COLUMNS_PRUNED` (48 → 49 cols)
- Computation location: `src/crypto_trade/features_v1/open_interest_v1.py`
  (`compute_oi_delta_zscore()` is parameterized; call with `delta_window=5, zscore_window=30`)
- The new feature is computed for ALL symbols (universal, not BTC-only), but only BTCUSDT is
  traded in /058 (BTC-only cohort). LightGBM handles NaN natively for non-BTC symbols in future
  multi-symbol contexts.

### 3.2 V1_FEATURE_COLUMNS_PRUNED Update

Add `"btc_oi_delta_5_z30"` after `"btc_funding_spread_30_90"` (alphabetical order: `btc_f` < `btc_o`).

### 3.3 New Universe Constant

Add `V1_ITER058_UNIVERSE = ("BTCUSDT",)` to `src/crypto_trade/features_v1/__init__.py` and `__all__`.

### 3.4 Runner Dispatch Branch

Add `elif iteration_label == "v1-058"` dispatch branch in `run_baseline_v1.py` with:
- Cohort: `("BTCUSDT",)` (BTC-only specialist)
- `atr_tp=3.5, atr_sl=1.75` (Model A BTC specialist convention; unchanged from /052–/054)
- `R3=ON` (OOD Mahalanobis gate, cutoff=0.70, 16-feature V1_OOD_FEATURE_COLUMNS)
- `R1=OFF` (no consecutive-SL cooldown for BTC specialist; same as /052-/054 convention)
- `R2=OFF` (no drawdown scaling for BTC specialist; same as /052-/054)
- `feature_columns=V1_FEATURE_COLUMNS_PRUNED` (49 cols)
- Multi-seed: `--seeds 3`, `_OUTER_SEED_OFFSETS=(0, 3, 6)` monkey-patched in runner

### 3.5 LM Master Recommendations (from lgbm_advisor.md Phase 4.5)

**Rec 1 — Document IC overlap with oi_delta_30_z90; do NOT block on IC alone**

ADOPTED. The analysis script (`analysis/iteration_v1-058/oi_delta_5_eda.py`) computes and reports
the Pearson IC between `btc_oi_delta_5_z30` and `oi_delta_30_z90`. IC < 0.80 is informational
only. IC ≥ 0.80 would be flagged as a concern but does not auto-block (per /025 precedent where
the IC gate was set at 0.80 for OI-family sisters). The engineering report will include this IC
value alongside feature importance.

**Rec 2 — Multi-seed verdict mandatory; per-seed spread > 0.5 = BASIN-LOTTERY downgrade**

ADOPTED. Verdict basis is MULTI-SEED MEAN (n=3 outer seeds). The /057 spread threshold of 0.50
applies unchanged. If `max_seed IS Sharpe − min_seed IS Sharpe > 0.50`, verdict is BASIN-LOTTERY
regardless of mean direction. Per-seed IS Sharpe and max-min spread are reported alongside the
mean in the engineering report and comparison_multi_seed.csv.

**Rec 3 — BTC has 113 IS trades — verify per-seed trade count ≥ 70**

ADOPTED. Pre-flight assertion in the runner verifies per-seed IS trade count ≥ 70. OOS trade
floor: per-seed OOS ≥ 15 (informational; not a blocker for EXPLORATION verdict). Both floors
are documented in Section 8 Pre-Registered Criteria.

---

## Section 4 — Expected OOS Impact

**Verdict bands (MULTI-SEED MEAN IS Δ vs BTC baseline −0.85):**

| Band | IS Δ Range | Verdict |
|---|---|---|
| MULTI-SEED-SPECIALIST-CANDIDATE | ≥ +0.50 (IS ≥ −0.35) | Pre-register cycle-7 CONFIRMATION |
| MULTI-SEED-PARTIAL-CONFIRMED | [+0.20, +0.50) (IS ∈ [−0.65, −0.35)) | Pre-register cycle-7 CONFIRMATION |
| MULTI-SEED-WEAK | [+0.05, +0.20) (IS ∈ [−0.80, −0.65)) | No CONFIRMATION; BTC stays pooled |
| NEG-INERT | (−0.05, +0.05) | Feature stays in pruned set (informational) |
| NEG-CLEAN | < −0.05 (IS < −0.90) | Feature reverted from V1_FEATURE_COLUMNS_PRUNED |

**Basin-lottery downgrade**: if max-min spread across 3 seeds > 0.50, verdict is downgraded to
BASIN-LOTTERY regardless of mean direction (per /057 precedent).

**Stability gate**: max-min ≤ 0.50 is PASS; > 0.50 is BASIN-LOTTERY.

**Trade-rate gate**: mean IS ≥ 50 trades AND mean OOS ≥ 10 trades required.

**LM Master prior distribution** (from lgbm_advisor.md):
- MULTI-SEED-SPECIALIST (mean IS Δ ≥ +0.50): 10%
- MULTI-SEED-PARTIAL (mean IS Δ ∈ [+0.20, +0.50)): 20%
- MULTI-SEED-WEAK (mean IS Δ ∈ [+0.05, +0.20)): 25%
- NEG-INERT (mean IS Δ ∈ (−0.05, +0.05)): 25%
- NEG-CLEAN (mean IS Δ < −0.05): 15%
- BASIN-LOTTERY (max-min > 0.50): 5%

**LM Master modal**: NEG-INERT (25%) or MULTI-SEED-WEAK (25%). Sister-IC risk with
`oi_delta_30_z90` at |IC| ≈ 0.30–0.55 means LightGBM's split budget allocation may already
partially explain variance captured by the slower version.

**Falsifier**: if `btc_oi_delta_5_z30` importance rank > 40/48 across ≥ 2 of the 3 outer seeds,
verdict is NEGATIVE-INERT regardless of IS Sharpe direction (INERT-by-importance gate; per /056
LM Master Phase 7.4 precedent where `btc_funding_spread_30_90` rank ≤ 10 was load-bearing for
LEARNED classification).

---

## Section 5 — Risk Mitigation

### 5.1 Risk Gate Config (R1/R2/R3)

- **R1=OFF**: no consecutive-SL cooldown. BTC specialist convention consistent with /052-/054.
  Rationale: BTC liquidation cascades may produce brief SL streak that R1 would penalize; pooled
  Model A baseline already uses R1=OFF for BTC-originated draws.
- **R2=OFF**: no drawdown scaling for BTC specialist. Consistent with /052-/054 specialist convention.
- **R3=ON**: OOD Mahalanobis gate, cutoff=0.70, using `V1_OOD_FEATURE_COLUMNS` (16 features).

### 5.2 IS-Calibrated Thresholds

- R3 cutoff=0.70 is the BASELINE_V1 anchor; no change.
- `btc_oi_delta_5_z30` clipped to ±10 (same as `oi_delta_30_z90` convention).
- Raw delta clipped to [-1.0, +5.0] (same as existing `oi_delta_30_z90` delta clip).

### 5.3 Simulated Effect on Prior Iterations

No prior iteration is affected: this dispatch branch is isolated to `iteration_label == "v1-058"`.
The `V1_FEATURE_COLUMNS_PRUNED` update (48 → 49) only affects /058 runner. No other runner
imports `V1_FEATURE_COLUMNS_PRUNED` with a strict `len() == 48` assertion active at other runners
(each prior runner pre-registered its own hash guard for its column count).

---

## Section 6 — Risk Management Design

| Primitive | State | Config | IS fire-rate estimate | OOS fire-rate estimate |
|---|---|---|---|---|
| R1 consecutive-SL cooldown | OFF | N/A | 0% | 0% |
| R2 drawdown scaling | OFF | N/A | 0% | 0% |
| R3 OOD Mahalanobis | ON | cutoff=0.70, 16-feat | ~8-12% (BTC specialist) | ~8-12% |
| ATR TP gate | ON | atr_tp=3.5 | set by labeling | set by labeling |
| ATR SL gate | ON | atr_sl=1.75 | set by labeling | set by labeling |
| Timeout | ON | 21 candles (8h) | ~15-25% (BTC typical) | ~15-25% |
| BTC contagion gate | N/A | BTC IS THE TRADED symbol | N/A | N/A |
| Regime coverage | IS only | walk-forward 24 months | 3 regimes: bull 2023, flat 2024, rally 2025 | OOS from 2025-03-24 |

BTC is the traded symbol, so the BTC-contagion primitive does not apply (the feature is itself
a BTC OI signal). R3 (OOD) provides the primary out-of-distribution protection.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode: NEGATIVE-INERT via sister-feature routing**

The highest-probability failure path (50% combined NEG-INERT + NEG-CLEAN per LM Master prior)
is that `btc_oi_delta_5_z30` and `oi_delta_30_z90` share sufficient IS predictive variance that
LightGBM's split budget routes almost entirely to the already-established 30-bar version. The
5-bar version would receive splits only in residual tree nodes, yielding importance rank > 40/48
across all 3 seeds while the IS Sharpe Δ is flat (≈ 0.0 range). This failure mode is distinct
from a labeling failure — it is a **feature-cluster saturation failure** where the existing sister
already explains the learnable OI-frequency signal at the BTC specialist's 113-trade IS sample size.

**What the gates should catch**: if importance rank ≥ 40/48 in ≥ 2 of 3 seeds, the INERT
falsifier fires (Section 4). Combined with flat IS Δ (< +0.05), the verdict is unambiguously
NEG-INERT. This is the intended path — the falsifier is load-bearing.

**Second plausible failure: BASIN-LOTTERY at 113-trade cohort**

BTC's 113 IS trades is the smallest specialist cohort of the three tested (LTC 124, ETH 145).
At `n_trials=18`, each fold has ≈22 trades. If the new feature creates minor but detectable
IS basin shifts (mean Δ ∈ [+0.05, +0.50)) but with max-min spread > 0.50 across 3 seeds, the
verdict is BASIN-LOTTERY — technically a positive mean signal but unreliable. The /057 pattern
(max-min 0.67 with mean in WEAK band) is the direct precedent for this outcome.

**What this looks like in OOS metrics**: EXPLORATION verdict is IS-only. OOS performance is
informational. A NEG-INERT outcome would show OOS Sharpe close to BTC baseline (+3.41) with
minor perturbation — no systematic collapse expected for an INERT feature.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is an EXPLORATION iteration. MERGE is NOT on the table at Phase 7. The pre-registered
criteria below govern verdict classification only; MERGE is reserved for a future CONFIRMATION.

**Verdict gates (evaluated on MULTI-SEED MEAN, n=3 outer seeds):**

1. **Trade-rate floor**: mean IS trades ≥ 50 AND mean OOS trades ≥ 10. If either fails, verdict
   is flagged as OVERFIT-RISK regardless of Sharpe.
2. **BASIN-LOTTERY gate**: max-min IS Sharpe spread across 3 seeds > 0.50 → BASIN-LOTTERY
   downgrade (overrides Sharpe band assignment).
3. **INERT falsifier**: `btc_oi_delta_5_z30` importance rank > 40/48 in ≥ 2 of 3 outer seeds
   → NEG-INERT regardless of IS Sharpe direction.
4. **IS Sharpe band** (multi-seed mean Δ vs BTC baseline −0.85):
   - ≥ +0.50 → MULTI-SEED-SPECIALIST-CANDIDATE
   - [+0.20, +0.50) → MULTI-SEED-PARTIAL-CONFIRMED
   - [+0.05, +0.20) → MULTI-SEED-WEAK
   - (−0.05, +0.05) → NEG-INERT
   - < −0.05 → NEG-CLEAN

**Revert rule**: if verdict is NEG-CLEAN or BASIN-LOTTERY, `btc_oi_delta_5_z30` is REVERTED
from `V1_FEATURE_COLUMNS_PRUNED` (49 → 48 cols) at closeout. If verdict is NEG-INERT, the
feature remains in the pruned set (informational; same as /057 ltc precedent pre-closeout).

---

## Section 9 — Library Stack Declaration

| Library | Version | Role |
|---|---|---|
| lightgbm | pinned in pyproject.toml | LightGBM model training |
| optuna | pinned in pyproject.toml | Hyperparameter search |
| pandas | pinned in pyproject.toml | Feature computation, data alignment |
| numpy | pinned in pyproject.toml | Numerical operations, clipping |
| scipy | pinned in pyproject.toml | Statistical tests (if used in EDA) |

No mlfinlab, mlfinpy, pypbo, or fracdiff dependencies in this iteration. All OI-delta feature
computation uses standard numpy/pandas rolling operations (same as `oi_delta_30_z90` in
`open_interest_v1.py`).

**Fallbacks**: none required. All dependencies are available in the project venv.
