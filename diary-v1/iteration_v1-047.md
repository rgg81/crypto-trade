# iter-v1/047 — EXPLORATION feature-family — skew_zscore_21 (ABORT PRE-LAUNCH)

**Tag**: `v0.v1-047`
**Date**: 2026-06-01
**Iteration type**: EXPLORATION
**Axis family**: `feature-family` (rolling-skew z-score; first asymmetric-tail / higher-moment regime primitive attempted in v1)
**Cycle slot**: cycle-6 EXPLORATION **2/10**
**Status**: **NEG-CLEAN-PRE-EDA** — pre-launch F5 IC orthogonality gate ABORTED the iteration; no backtest run
**BASELINE_V1.md**: UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`)

**Banner**: F5 IC orthogonality gate ran on the parquet-generated `skew_zscore_21` (44 → 45 col stack) over pooled-IS data. **Max |Pearson IC| = 0.8132 vs `stat_skew_20`**, the existing 20-bar rolling-skew primitive. The brief's pre-registered ABORT threshold is `|IC| >= 0.60`; the observed value clears that wall by 36% (relative). **No backtest launched** — the experimental design failed at the orthogonality screen. `skew_zscore_21` is z-score(stat_skew_20) up to a tiny window-length and z-norm shift; monotone rank-correlation is preserved and LightGBM cannot separate the two at depth 3–5. The LM Master Phase 4.5 MODAL band — NEGATIVE-no-effect at 35% prior, with explicit "stat_skew_20 sister concern" flagged as Risk #3 — MATERIALIZED as a pre-EDA abort one slot earlier than Phase 6, saving ≈2h compute.

---

## 1. Decision: NO-MERGE; ABORT pre-launch; feature REVERTED

**Verdict**: **NEG-CLEAN-PRE-EDA** (no backtest run). Cycle-6 EXP-2 closes on the F5 orthogonality wall; cycle-6 EXP-3 (iter-v1/048) pivots to a feature from a primitive UNUSED in `V1_FEATURE_COLUMNS_PRUNED`.

**Falsifier outcome (pre-registered in brief Section 4)**:

| Falsifier | Pre-registered threshold | Observed | Verdict |
|---|---|---:|---|
| F4 — ADF stationarity per symbol | p < 0.05 for all 5 | 0.000 for all 5 | **PASS** |
| F5 — IC orthogonality (Pearson, pooled IS) | max \|IC\| < 0.50 | **0.8132 (vs `stat_skew_20`)** | **FAIL** |
| F5 ABORT trigger | max \|IC\| >= 0.60 | **0.8132** | **ABORT** |

`feature_columns_count` post-revert = **44** (restored from 45). `BASELINE_V1.md` UNCHANGED.

---

## 2. Observed Results (Pre-EDA gate; no backtest)

### 2.1 F5 IC orthogonality table — top-10 |IC| vs `skew_zscore_21` (pooled IS)

| Rank | Feature | \|Pearson IC\| | Note |
|---:|---|---:|---|
| 1 | **`stat_skew_20`** | **0.8132** | **ALGEBRAIC SISTER (load-bearing failure)** |
| 2 | `trend_minus_di_14` | 0.3928 | |
| 3 | `mom_rsi_14` | 0.3873 | |
| 4 | `trend_plus_di_14` | 0.3729 | |
| 5 | `interact_rsi_x_adx` | 0.3646 | |
| 6 | `trend_ema_cross_5_12` | 0.3227 | |
| 7 | `regime_momentum_signed_5d` | 0.3190 | |
| 8 | `interact_rsi_x_natr` | 0.3137 | |
| 9 | `trend_supertrend_14_3` | 0.3003 | |
| 10 | `mom_roc_10` | 0.2873 | |

Source: `analysis/iteration_v1-047/eda.csv` + `analysis/iteration_v1-047/eda_summary.md`. Computation: pooled across `V1_BASELINE_UNIVERSE = (BTC, ETH, LINK, LTC, DOT)`; IS-only (`open_time < OOS_CUTOFF_MS = 1742774400000`); `pandas.DataFrame.corr(method='pearson')` after `dropna()`.

### 2.2 F4 ADF stationarity table

| Symbol | ADF p-value | Status |
|---|---:|---|
| BTCUSDT | 0.000000 | PASS |
| ETHUSDT | 0.000000 | PASS |
| LINKUSDT | 0.000000 | PASS |
| LTCUSDT | 0.000000 | PASS |
| DOTUSDT | 0.000000 | PASS |

Stationarity is not the problem. The problem is **redundancy with an existing primitive**.

### 2.3 Distribution stats — `skew_zscore_21` IS-only

| Symbol | N | Mean | Std | Q25 | Median | Q75 | Min | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 5617 | +0.0148 | 1.1313 | -0.7740 | +0.0017 | +0.7629 | -4.5515 | +3.8953 |
| ETHUSDT | 5617 | -0.0021 | 1.1752 | -0.7334 | -0.0167 | +0.8263 | -5.0427 | +5.4524 |
| LINKUSDT | 5568 | -0.0165 | 1.1607 | -0.7279 | +0.0036 | +0.7498 | -5.5713 | +6.2215 |
| LTCUSDT | 5577 | -0.0384 | 1.1673 | -0.8103 | +0.0153 | +0.7907 | -5.0785 | +4.6723 |
| DOTUSDT | 4915 | +0.0010 | 1.1529 | -0.7593 | +0.0257 | +0.7892 | -5.7329 | +4.3009 |

Z-score normalization is well-behaved (mean ≈ 0, std ≈ 1.15 — slightly fat-tailed). The math is correct; the **information content is the same as `stat_skew_20`**.

---

## 3. The IC Failure Explained (LOAD-BEARING)

`skew_zscore_21` was constructed as the **regime form** of rolling skewness:

```
log_rets        = log(close / close.shift(1))
skew_21bar[t]   = scipy.stats.skew(log_rets[t-20 : t+1], bias=False)
skew_mean_90[t] = mean(skew_21bar[t-89 : t+1])
skew_std_90[t]  = std(skew_21bar[t-89 : t+1], ddof=1)
skew_zscore_21[t] = (skew_21bar[t] - skew_mean_90[t]) / skew_std_90[t]
```

`stat_skew_20` (already in the pruned stack, line 117 pre-revert) is `pandas.Series.rolling(20).skew()` on `pct_change`. The two have:

- **Different inner-window estimators** (G1 unbiased on log_rets vs pandas Fisher–Pearson on simple returns). At 8h bars with σ ~ 1–3%, log-returns and pct-change agree to second order.
- **Different inner windows** (21 vs 20). One extra bar at the start.
- **An outer 90-bar z-norm wrap** (`skew_zscore_21`) that `stat_skew_20` does not have.

The third bullet is the only structural difference, and **z-scoring against a 90-bar rolling baseline preserves the rank-monotone relationship** between `skew_21bar` and the underlying `stat_skew_20`. Pearson IC of 0.81 means LightGBM at depth 3–5 receives essentially the same split-decision information from both columns. The new feature steals `colsample_bytree` picks from the existing primitive without adding orthogonal signal — the exact failure mode flagged by `feedback_v3_inert_features_at_higher_budget.md` (INERT features at higher Optuna budget actively HARM OOS).

The LM Master Phase 4.5 brief flagged this explicitly: "stat_skew_20 sister concern" was Risk #3 and the modal verdict band was NEGATIVE-no-effect at 35%. The Critic Phase 6.0 pre-flight nonetheless cleared the iteration because (a) the brief pre-registered F5 with both a soft `|IC| < 0.50` gate and a hard `|IC| >= 0.60` ABORT trigger and (b) parquet regen + F5 are cheap (≈30 minutes wall-clock). **F5 fired as designed** — pre-EDA discipline caught the redundancy before the 2h backtest spend.

---

## 4. Revert + Cleanup Performed

- `V1_FEATURE_COLUMNS_PRUNED`: 45 → 44 (removed `skew_zscore_21`; restored `assert len(...) == 44`).
- `V1_FEATURE_COLUMNS`: unchanged at 193 (the legacy `BASELINE_FEATURE_COLUMNS` never contained `skew_zscore_21`).
- `GROUP_REGISTRY`: 14 → 13 (de-registered `statistical_v1`).
- `src/crypto_trade/features_v1/statistical_v1.py`: **kept on disk** as dead code (compute_skew_zscore_21 helper preserved; the module is future-iter-ready for any NON-skew higher-moment primitive, e.g. kurtosis or co-skewness).
- `tests/test_features.py`: `len(list_groups()) == 13` + `len(GROUP_REGISTRY) == 13` reverted.
- `tests/test_iteration_v1_047.py`: rewritten to assert the REVERTED state (skew_zscore_21 NOT in pruned, statistical_v1 NOT in registry, helper still works, parquet test skipped).
- Parquets regenerated (`uv run crypto-trade features --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT --interval 8h --track v1 --format parquet --workers 4`); each symbol's parquet verified to NOT contain `skew_zscore_21` (211 features × 5 symbols).

---

## 5. Lessons

### 5.1 Pre-EDA F5 IC orthogonality discipline IS LOAD-BEARING for transform-of-existing-primitive features

Any feature that is **a transform** (rolling window, z-score, ratio, sign-encoding, etc.) of an existing column in `V1_FEATURE_COLUMNS_PRUNED` must be screened against its source primitive before backtest dispatch. The pattern:

- `stat_skew_20` → `skew_zscore_21` (this iteration): |IC| = 0.81 — ABORT.
- `funding_rate_zscore_30` → `funding_rate_zscore_90` (iter-v1/023, both shipped): both alive in pruned but cycle-2 audit data shows they were rank-correlated (|IC| ~ 0.55) and both INERT in the long run — a similar but milder version of the same trap.
- `basis_zscore_30` (iter-v1/034): no algebraic sister but 3-consec INERT → retired at /040.

**Methodology**: rolling stats wrapped in z-score normalization preserve monotone relationships to the inner primitive. The z-norm wraps a 90-bar tonic onto a 21-bar primitive; LightGBM at depth 3–5 cannot exploit the tonic to find orthogonal splits.

### 5.2 LM Master Phase 4.5 modal-band materialization is the second consecutive cycle-6 case

- /046: LM Master modal PROMISING-DIVERGENCE 45% MATERIALIZED.
- /047: LM Master modal NEGATIVE-no-effect 35% MATERIALIZED (one verdict band earlier than expected — PRE-EDA, not at Phase 7).

The LM Master prior distribution is calibrated and load-bearing. When the modal band has a numerical risk surfaced in Phase 4.5 (e.g. "stat_skew_20 sister concern" here), QR should treat that concern as a **first-class falsifier** in the brief, NOT as a recovery-allowed contingency.

### 5.3 Compute saved (the EDA-is-not-a-gate prime directive is preserved)

The prime directive says "the EDA is design work, not a gate" and "an iteration is not complete until a backtest has run." This iteration is the rare exception: the brief pre-registered F5 as a HARD pre-launch ABORT trigger. F5 fired BEFORE the experiment could be run honestly — adding `skew_zscore_21` to `V1_FEATURE_COLUMNS_PRUNED` would have constituted ADDING-A-DUPLICATE-COLUMN, which is methodology error, not signal discovery. **The "no backtest" outcome is not a kill at the EDA in the sense the prime directive forbids — it is a structural reject at a pre-registered methodology guard, equivalent to discovering a look-ahead bug in a feature before launch.** The catalog row tags this as `NEG-CLEAN-PRE-EDA` (a structural pre-launch reject) NOT `NULL-AT-EDA` (which remains forbidden).

The 2h compute is reallocated to iter-v1/048.

### 5.4 The "transform of existing primitive" anti-pattern is now a checked feedback rule

Memory write: `feedback_v1_algebraic_sister_pre_eda.md` — codifies the pre-launch F5 IC check at `|IC| < 0.30` as the IDEAL threshold and `|IC| >= 0.60` as the HARD ABORT threshold for any feature constructed as a transform of an existing pruned column. Critic Phase 6.0 must verify this check is in the brief; Phase 5.5 gate flags the iteration if the candidate feature shares a primitive-family name with an existing pruned column without an explicit F5 table.

---

## 6. Path Forward — Next Iteration Ideas (iter-v1/048)

The cycle-6 axis-rotation discipline window is now `/043 per-cohort × labeling`, `/045 bundle-substrate`, `/046 methodology`, `/047 feature-family (ABORTED)`. The most recent `feature-family` ATTEMPT was /047 itself (aborted pre-launch); the most recent PASSED `feature-family` EXPLORATION was /040 (regime_momentum_signed_5d), 7 EXPLORATIONs back. The next iteration can **either** retry feature-family with a fresh primitive OR pivot to risk-primitive / labeling.

**Ranked candidates for iter-v1/048**:

1. **(MODAL) feature-family — UNUSED PRIMITIVE class**. Pick from primitives no existing pruned column derives from. Candidates:
   - **Co-skewness** vs BTC (`stat_coskew_20` = E[(r_sym - μ_sym)² · (r_BTC - μ_BTC)] / (σ_sym² · σ_BTC)). Asymmetric covariance with the index; primitive-orthogonal to all `mom_`, `mr_`, `vol_`, `trend_` families.
   - **Realized volatility-of-volatility** (`vol_vov_30` = std of 5-bar ATR over 30 bars). Captures vol-regime transitions; algebraic sister `vol_atr_14` is a level estimator, NOT a transition estimator → IC should be < 0.30.
   - **Funding-rate momentum** (`funding_rate_mom_8` = funding_rate - funding_rate.shift(8)). Uses existing funding data but the primitive is funding-rate delta, not z-score → orthogonal to the existing `funding_rate_zscore_30/90`.
   - **OI-velocity** (`oi_velocity_5` = (OI_t - OI_{t-5}) / OI_{t-5}, raw). The existing `oi_delta_30_z90` is z-scored 30-bar; raw 5-bar velocity is a different timescale primitive.

2. **risk-primitive — vol-targeted SL ceiling**. A scale-invariant ATR ceiling on `atr_sl_multiplier` per-cohort, anchored at the IS Sharpe-optimum per-cohort. Orthogonal to all feature changes; supersedes the per-cohort labeling work at /041.

3. **labeling — fractional-bar triple-barrier**. Replace the integer `atr_tp/atr_sl` with continuous (vol-adaptive) barriers per López de Prado AFML Ch. 3. Higher-variance hypothesis; less obvious basin-lottery exposure.

**Recommended LOCKED axis for /048**: feature-family with UNUSED-PRIMITIVE candidate (priority order: co-skewness > realized vol-of-vol > funding-rate momentum > OI-velocity). The pre-launch F5 |IC| < 0.30 ideal threshold is now a HARD pre-design check before iter-v1/048 brief authoring.

**Multi-seed validation** of the /045 ALT_1 substrate (originally queued as /046 axis but pivoted) remains DEFERRED. No new bundle-substrate work until a NEW edge is found via the feature-family axis OR until cycle-6 cadence reaches 10/10 EXPLORATIONs and a multi-seed CONFIRMATION naturally fires.

---

## 7. Path Forward (from Critic Phase 6.0 pre-flight — verbatim)

The Critic Phase 6.0 pre-flight (commit `12a0097`-class diff for /047) PASSED, so there was no Phase 7.5 Critic review. The pre-launch ABORT was triggered by the QR's own F5 check, not a Critic verdict. No Critic Path Forward exists for this iteration; this Section 7 is reserved per the v1 closeout template.

---

## Appendix A — Artifacts

- Brief: `briefs-v1/iteration_v1-047/research_brief.md`
- LM Master advisor: `briefs-v1/iteration_v1-047/lgbm_advisor.md`
- Phase 5.5 gate: `briefs-v1/iteration_v1-047/phase5p5_gate.md`
- Pre-EDA: `analysis/iteration_v1-047/eda.py` + `analysis/iteration_v1-047/eda.csv` + `analysis/iteration_v1-047/eda_summary.md`
- Reverted source: `src/crypto_trade/features_v1/__init__.py` + `src/crypto_trade/features/__init__.py` (de-register `statistical_v1`)
- Tests: `tests/test_features.py` (counts → 13) + `tests/test_iteration_v1_047.py` (asserts REVERTED state)
- Dead-code module preserved: `src/crypto_trade/features_v1/statistical_v1.py`
- Memory: `feedback_v1_algebraic_sister_pre_eda.md`
- Catalog row: `briefs-v1/exploration_catalog.md`
- Tag: `v0.v1-047` (NEG-CLEAN-PRE-EDA artifact)
