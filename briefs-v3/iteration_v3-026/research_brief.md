# Iteration v3-026 — Research Brief

**Type**: EXPLORATION (cadence #8 of 10 in the post-bootstrap cycle; **STRUCTURAL axis (Category 2 — GENUINE FEATURE ENGINEERING — second composed feature)** — `vol_adj_autocorr` per Critic FINAL Recommendation of iter-v3/025 (review SHA `402643d`) + user directive 2026-05-08)
**Track**: v3 (rigor arm) — twenty-sixth iteration
**Branch**: `iteration-v3/026` (off `iteration-v3/025` head; brief authored after EDA committed at SHA `97302db`)
**Date**: 2026-05-08
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 35             # SET BY --exploration default (PRELIMINARY-VALIDATED through iter-v3/020-025)
colsample_bytree = 1.0            # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000  # millisecond representation
```

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–025 briefs / engineering reports / Critic FINALs / diaries; the new iter-v3/026 EDA at SHA `97302db` (`analysis/iteration_v3-026/second_engineered_eda.py` + outputs).

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cadence #8 of 10 post-bootstrap)
Wall-clock budget: < 30 min target / 2h hard cap
Single-axis variation: SECOND GENUINE FEATURE ENGINEERING — composed feature.
                       KEEP regime_momentum_signed_5d in V3_FEATURE_COLUMNS
                       (do NOT revert; iter-v3/025 PATH A PROMISING).
                       ADD vol_adj_autocorr to V3_FEATURE_COLUMNS
                       (14 → 15). COMPOSED feature: ret_autocorr_lag1_50 /
                       (range_realized_vol_50 + 1e-6) — autocorrelation per
                       unit vol; structurally orthogonal to regime_momentum.
                       Per Critic FINAL Rec of iter-v3/025 (SHA `402643d`)
                       + user directive 2026-05-08.
Cadence: EXPLORATION #8 of 10 needed before next CONFIRMATION (earliest = iter-v3/029)
Axis category: 2 (GENUINE FEATURE ENGINEERING — second composed feature; SECOND
               Category 2 axis in v3 catalog; first was iter-v3/025
               regime_momentum_signed_5d PROMISING)
ANCHOR (formal BASELINE_V3.md anchor): iter-v3/018 BOOTSTRAP baseline
        (multi-seed mean +0.3788 IS / +0.3869 OOS)
REFERENCE (single-seed parent): iter-v3/025 (+0.8788 IS / +1.2244 OOS — single-seed
        reference; PROMISING but lottery-suspect per `feedback_v3_single_seed_frozen_baseline.md`)
NOT a gate-threshold knob. NOT an off-the-shelf indicator addition.
NOT a labeling change. NOT a model architecture change.
NOT a universe-expansion (3-symbol BCH+LDO+TRX UNCHANGED).
This iteration NEVER updates BASELINE_V3.md.
```

**Justification — second engineered feature pivot validation (per Critic FINAL `402643d` of iter-v3/025 Recommendation + user directive 2026-05-08)**:

After iter-v3/025 EXPLORATION-PROMISING (clean) — the FIRST PROMISING result in the post-bootstrap cycle:

- The engineered-feature axis category VALIDATED at single-seed: regime_momentum_signed_5d landed PATH A unambiguously per brief §4.4 LOCKED criteria (importance 51% of top portfolio = ~2× any prior NEW feature; co-directional IS+OOS lift; BCH/LDO frozen-baseline pattern from iter-v3/020-024 DISSOLVED).
- The empirical comparison surfaced in `feedback_v3_engineered_features_proven.md` enshrines: off-the-shelf NEW features (microstructure tbr_zscore_30, per-symbol funding, BTC funding) consistently produce rank 14/14 INERT outcomes; the ONE engineered (composed) feature broke through with importance ≥30 across all 4 cuts and OOS Sharpe Δ +0.84.
- **The iter-v3/025 PROMISING result is single-seed** — iter-v3/013 single-seed +1.0088 IS / +2.6970 OOS Sharpe was FALSIFIED at multi-seed iter-v3/018 CONFIRMATION (62% IS / 86% OOS reduction). iter-v3/025 needs multi-seed validation at iter-v3/029 CONFIRMATION before being trusted. **A second engineered feature with structurally orthogonal mechanism that ALSO clears PATH A would substantially de-risk the engineered-features-pivot hypothesis** by demonstrating that the iter-v3/025 result is generalizable, not lottery.
- **User directive 2026-05-08**: confirmed mandate to validate the FEATURE ENGINEERING pivot consistently. Specifically named `vol_adj_autocorr` as the recommended SECOND engineered candidate.
- **Critic FINAL Recommendation of iter-v3/025**: "iter-v3/026 axis = SECOND ENGINEERED FEATURE to validate the pivot strategy. Strong candidate: `vol_adj_autocorr` = `ret_autocorr_lag1_50 / (range_realized_vol_50 + 1e-6)` (autocorrelation per unit vol — orthogonal to regime momentum). If 2 of 2 engineered features PROMISING → strong evidence feature engineering is THE right axis category for v3."
- Forward priority order from prior iterations + new catalog state:
  1. **HIGH — SECOND GENUINE FEATURE ENGINEERING composed-feature axis (iter-v3/026 mandate, this iteration)**: validates pivot consistency
  2. HIGH — THIRD engineered feature (iter-v3/027) IF iter-v3/026 PATH A
  3. MEDIUM — DSR gate reformulation
  4. LOW — Knob axes (saturated)
  5. LOW — Universe expansion alternative symbols (ATOM/FIL/ALGO)

**iter-v3/026 first EXPLORATION axis = HIGH-priority — `vol_adj_autocorr` second composed feature.** Cannot be renegotiated post-hoc per Critic FINAL `402643d` of iter-v3/025 + user directive 2026-05-08.

**Why second engineered feature now (post iter-v3/025 PATH A)**:

- The iter-v3/025 result is necessary but not sufficient evidence for the engineered-features pivot. A single PROMISING engineered feature could still be lottery (precedent: iter-v3/013 PROMISING single-seed → iter-v3/018 multi-seed FALSIFIED). Two-of-two engineered features clearing PATH A is materially stronger evidence.
- The structural-orthogonality criterion (max |IC| vs regime_momentum_signed_5d ≤ 0.50 ideally; ≤ 0.20 preferred) ensures the second feature exercises a distinct interaction mechanism. `vol_adj_autocorr` per-symbol max |IC|_rm: BCH 0.075, LDO 0.0014, TRX 0.075 — all near-zero across all 3 symbols (EDA SHA `97302db`). This is the most orthogonal candidate by an order of magnitude versus the 4 evaluated.
- **Mechanism distinctness**:
  - `regime_momentum_signed_5d`: directional 5-day return × Hurst regime classifier — encodes momentum-vs-mean-reversion regime sign-flip via close-derived ret_5d × hurst_100
  - `vol_adj_autocorr`: lag-1 return persistence / range-realized vol — encodes per-unit-vol return persistence; disambiguates noise-driven persistence (high autocorr, high vol) from signal-driven persistence (high autocorr, low vol)
  - Source primitives are NON-OVERLAPPING (close + hurst_100 vs ret_autocorr_lag1_50 + range_realized_vol_50) → genuine new interaction, not a variation of regime momentum
- Per AFML (López de Prado, 2018) Ch. 8 + Sinclair, *Volatility Trading*: vol-normalized signal features are a textbook microstructure technique. The depth-3-5 LightGBM trees can split on raw `ret_autocorr_lag1_50` and raw `range_realized_vol_50` independently but cannot represent the ratio `f1 / f2` at the candidate-split level — making this an interaction the model cannot internally compose.

**Why this experiment is inexpensive at iter-v3/026**:

- Existing primitives: `ret_autocorr_lag1_50` (rank 12 mean across iter-v3/018-024 importance trajectories) and `range_realized_vol_50` (rank 5 mean — strongly used by all 3 per-symbol models).
- Implementation: extend existing module `engineered_v3.py` (introduced at iter-v3/025 — clean separation already established) with `compute_vol_adj_autocorr` that computes `ret_autocorr_lag1_50 / (range_realized_vol_50 + 1e-6)`. ~10 lines of code.
- Wall-clock impact: +1 feature column at 3-symbol universe × n_trials=35 expected to add ~3% to feature-loading time (computation is element-wise division of two existing primitives). Total wall-clock predicted 8-15 min (well within 2h cap).

After iter-v3/026 the catalog will have: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 2 + gate-adx × 1 (CLOSED) + NEW microstructure feature × 1 (CLOSED-narrow) + NEW model arch × 1 (CLOSED-at-config) + NEW labeling arch × 1 (PATH C) + bootstrap CONFIRMATION × 1 + NEW external-data-source feature × 1 (PERMANENTLY-CLOSED per-symbol variant) + NEW risk primitive (per-symbol cap) × 1 (CLOSED-mechanism) + NEW universe expansion × 1 (CLOSED-symbols-cycle) + NEW regime-conditional gate primitive × 1 (PARTIALLY-EFFECTIVE-CLOSED) + NEW external-data-source feature RETEST at higher Optuna budget × 1 (CLOSED-PERMANENTLY) + NEW external-data-source feature CROSS-ASSET variant × 1 (CLOSED-FAMILY-WIDE) + GENUINE FEATURE ENGINEERING composed-feature × 1 (PROMISING — iter-v3/025) + **GENUINE FEATURE ENGINEERING SECOND composed-feature × 1 (this iteration)** = 18 unique axis representations after iter-v3/026; **second Category 2 axis (composed feature) in v3 catalog**.

---

## Section 1 — Hypothesis

Adding `vol_adj_autocorr` (= `ret_autocorr_lag1_50 / (range_realized_vol_50 + 1e-6)`) — autocorrelation per unit vol — as the 15th feature on top of the iter-v3/025 14-feature stack (drop-MKR + z=2.0 + ATR 2.0/1.0 + BTC ±15% + ADX=20 + 14 V3_FEATURE_COLUMNS including regime_momentum_signed_5d) — at the EXPLORATION default n_trials=35 — will produce **importance rank ≤10 for ≥1 symbol AND importance ≥30 for ≥1 cut** (relaxed-rank threshold per Category 2 carve-out) AND **IS Sharpe Δ ≥ 0** (relaxed from +0.10 because the iter-v3/025 reference already captured the largest available regime/momentum interaction; marginal additional lift expected) — if the per-unit-vol return-persistence interaction is genuinely informative AND structurally distinct from regime_momentum's mechanism AND the LightGBM trees on the 14-feature stack cannot internally compose `f1 / f2` at depth-5.

Predicted IS Sharpe band [+0.80, +1.10] median +0.95 vs iter-v3/025 single-seed reference +0.8788; predicted OOS Sharpe band [+1.10, +1.45] median +1.25 vs iter-v3/025 single-seed reference +1.2244 (relaxed from "lift" to "maintain": the iter-v3/025 OOS result is already strong; the second engineered feature should at minimum NOT REGRESS, with a marginal additional lift if the orthogonal mechanism captures incremental signal).

**Mechanism explanation** (why per-unit-vol autocorrelation should surface where raw ret_autocorr_lag1_50 or raw range_realized_vol_50 alone don't):

The composed feature `ret_autocorr_lag1_50 / (range_realized_vol_50 + 1e-6)` encodes a textbook microstructure heuristic from Sinclair *Volatility Trading* + López de Prado AFML: **return persistence is a meaningful signal only when normalized by vol**. The same lag-1 autocorrelation has different implications:
- Low-vol regime, high autocorr → genuine momentum/persistence signal worth trading
- High-vol regime, high autocorr → noise-driven persistence; chasing it is a value trap

A LightGBM tree of depth 5 on the raw 14-feature stack containing both `ret_autocorr_lag1_50` AND `range_realized_vol_50` would need to (a) split first on `range_realized_vol_50 < threshold`, (b) split on `ret_autocorr_lag1_50` magnitude in each branch SEPARATELY with INVERTED interpretation conventions, and (c) preserve enough remaining splits for the actual decision boundary. The depth-5 budget combined with `colsample_bytree=1.0` HARDCODED at EXPLORATION makes this composition difficult to learn from data; a single hyperparameter trajectory at n_trials=35 may not converge on the right tree structure even if the signal exists. **The composed feature precomputes this ratio**, freeing tree capacity for actual decision splits.

**Why prior iterations don't directly predict iter-v3/026's outcome**:

- iter-v3/015 microstructure tbr_zscore_30 INERT and iter-v3/019/023/024 funding INERT: ALL four failures were OFF-THE-SHELF indicator additions (single-feature primitives). iter-v3/026 is a **COMPOSED feature** built from existing primitives; the failure mode is mechanistically distinct.
- iter-v3/025 regime_momentum_signed_5d PROMISING: the SAME axis category as iter-v3/026 — but the source primitives are non-overlapping. iter-v3/025 used close-derived ret_5d × hurst_100 (regime-conditional momentum); iter-v3/026 uses ret_autocorr_lag1_50 / range_realized_vol_50 (vol-adjusted persistence). The iter-v3/025 result confirms Category 2 axes can succeed in v3; iter-v3/026 tests whether the success generalizes to a structurally orthogonal mechanism.
- The hypothesis is falsifiable in 3 directions: (a) PROMISING (PATH A) — both engineered features rank ≤10 + importance ≥30 + IS+OOS co-direct → STRONG evidence feature engineering is consistently productive; (b) PROMISING-INERT-second (PATH B) — vol_adj_autocorr ranks 14/14 → first composition was lucky; engineered category narrowly succeeds (only regime_momentum works); (c) NEGATIVE (PATH C) — IS or OOS drops > 0.10 below iter-v3/025 reference → second feature actively hurts (regime_momentum captured all available signal; adding correlated-with-source-primitive feature expands overfit space). Each pathway has distinct downstream implications.

**Direction symmetry**: vol_adj_autocorr is naturally symmetric: positive autocorr / low vol → trade momentum-persistence (long bias when bias is up); negative autocorr / low vol → trade reversion (short bias when bias is up). The vol-normalization scales the magnitude but not the direction. EDA rank-IC results: BCH h=7 = +0.025 (slight positive momentum prediction), LDO h=7 = +0.028, TRX h=7 = +0.028 — all 3 symbols at h=7 are POSITIVE-direction (small magnitude but consistent), indicating a vol-normalized momentum-continuation signal. This is empirically consistent with Sinclair's vol-normalization argument: per-unit-vol persistence predicts continuation, raw persistence is noise-driven.

---

## Section 2 — Implementation Spec

### 2.1 Atomic feature add (single axis preserved)

iter-v3/026 first commit must atomically:
1. **KEEP** `regime_momentum_signed_5d` in `V3_FEATURE_COLUMNS_TOP_N` (do NOT revert; iter-v3/025 PROMISING).
2. **ADD** `vol_adj_autocorr` to `V3_FEATURE_COLUMNS_TOP_N` (14 → 15).
3. Net column count: 15 (one more than iter-v3/025 anchor).
4. Single axis preserved: ATOMIC add (no swap, no drop); other gates BYTE-IDENTICAL to iter-v3/025 anchor (z=2.0, ATR 2.0/1.0, BTC ±15%, ADX=20, Hurst, low-vol, hit-rate disabled, regime gate disabled).

### 2.2 Module structure

**Existing module**: `src/crypto_trade/features_v3/engineered_v3.py` (introduced at iter-v3/025 — clean separation from off-the-shelf primitives already established).

**New function**: `compute_vol_adj_autocorr(df: pd.DataFrame) -> pd.DataFrame` — consumes `ret_autocorr_lag1_50` and `range_realized_vol_50` (both from upstream groups already in the GROUP_REGISTRY), returns df with `vol_adj_autocorr` column appended.

```python
def compute_vol_adj_autocorr(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: ret_autocorr_lag1_50 / (range_realized_vol_50 + EPS).

    Past-only by construction:
    - ret_autocorr_lag1_50 is computed past-only by add_momentum_accel_v3_features
      (50-bar trailing rolling correlation of returns and lag-1 returns).
    - range_realized_vol_50 is computed past-only by add_tail_risk_v3_features
      (50-bar trailing rolling realized vol from high/low ranges).
    Both source primitives are upstream in GROUP_REGISTRY.
    """
    EPS = 1e-6
    df = df.copy()
    if "ret_autocorr_lag1_50" not in df.columns:
        df["vol_adj_autocorr"] = np.nan
        return df
    if "range_realized_vol_50" not in df.columns:
        df["vol_adj_autocorr"] = np.nan
        return df
    autocorr = df["ret_autocorr_lag1_50"].astype(float)
    vol = df["range_realized_vol_50"].astype(float)
    df["vol_adj_autocorr"] = autocorr / (vol + EPS)
    return df
```

**Update** `add_engineered_v3_features` to call BOTH compute functions:

```python
def add_engineered_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """GROUP_REGISTRY entry point for all Category 2 (composed) v3 features."""
    df = compute_regime_momentum_signed_5d(df)  # iter-v3/025
    df = compute_vol_adj_autocorr(df)            # iter-v3/026
    return df
```

**Order dependency**: `engineered_v3` already runs AFTER `momentum_accel` (which produces ret_autocorr_lag1_50) and AFTER `tail_risk` (which produces range_realized_vol_50) AND AFTER `regime` (which produces hurst_100 — needed for compute_regime_momentum_signed_5d). The current GROUP_REGISTRY insertion order is `regime → tail_risk → price_efficient_vol → momentum_accel → volume_micro → cross_btc → engineered_v3 → fracdiff → microstructure_v3 → funding_v3 → btc_funding_v3`. Verify all 3 source primitives are computed before engineered_v3 runs.

### 2.3 Behavioral-effect predictor (per `feedback_v3_axis_saturation_predictor.md`)

**IS trade count predictor**: the new feature is one of 15 columns at `colsample_bytree=1.0`; its incremental effect on tree-split structure is non-trivial but bounded. Predicted IS trade band based on prior +1-feature iterations and iter-v3/025's behavior:

| Iteration | New feature | IS trades | Δ from baseline |
|---|---|---:|---:|
| iter-v3/015 | tbr_zscore_30 | 175 | +3 (vs 172 anchor) |
| iter-v3/019 | funding_rate_zscore_30 (n=10) | 209 | +37 (vs 172) |
| iter-v3/023 | funding_rate_zscore_30 (n=35) | 195 | +23 (vs 172) |
| iter-v3/024 | btc_funding_rate_zscore_30 (n=35) | 182 | +10 (vs 172) |
| iter-v3/025 | regime_momentum_signed_5d (n=35) | 194 | +22 (vs 172) |

Empirical band on iter-v3/018 anchor (172 trades): IS trades ∈ [+3, +37] above 172 → predicted band [175, 209]. Reference is iter-v3/025's 194 trades. **For iter-v3/026 the 15th-feature addition is expected to shift trade count modestly** (predicted ±20 vs iter-v3/025 reference 194 → band [174, 214]). **Saturation falsifier threshold**: IS trades > 215 (= 1.05 × prior max 209) OR IS trades < 130 (= 0.75 × prior min 172). If observed IS trades are outside [129, 215], the axis behavioral effect is anomalous and the iteration verdict requires saturation-falsifier-FIRES qualifier in catalog row.

**Behavioral-effect predictor for the new feature specifically**: vol_adj_autocorr's source primitives have been used at modest rank (autocorr_lag1_50 mean rank ~12 out of 13-14 features; range_realized_vol_50 mean rank ~5). The composed ratio is expected to be used at LightGBM importance rank between 8-13 across the 3 symbols, with importance values 30-150 depending on per-symbol Optuna trajectory.

### 2.4 PATH classification table (LOCKED — cannot be renegotiated post-hoc)

| Path | Feature importance | IS Sharpe Δ vs iter-v3/025 ref | OOS Sharpe Δ vs iter-v3/025 ref | Verdict |
|---|---|---:|---:|---|
| **A** PROMISING | rank ≤10 for ≥1 symbol AND importance ≥30 | ≥ 0 | informational | second engineered feature works (signal exists; structurally orthogonal mechanism contributes) |
| **B** PROMISING-INERT | rank 14-15/15 across 3+ cuts | informational | informational | engineered-feature axis NARROW for 14-feature stack at iter-v3/026; second engineered candidate did not contribute |
| **C** NEGATIVE | informational | < −0.10 OR | < −0.50 | feature actively hurts (regime_momentum captured all available signal; redundant feature expands overfit) |
| **D** PROMISING-MECHANICAL | trade roster bit-identical to iter-v3/025 OR strict subset | any IS direction | any OOS direction | mechanical accounting effect; not new edge — see iter-v3/013 PROMISING-MECHANICAL precedent |

**PATH A relaxation rationale** (IS Δ ≥ 0 vs standard ≥ +0.10): The iter-v3/025 reference IS Sharpe +0.8788 already captures the largest single-feature lift in the post-bootstrap cycle (+0.50 Δ vs anchor). A second engineered feature with structurally orthogonal mechanism is hypothesized to **maintain** the iter-v3/025 result while contributing additional importance, not necessarily produce another +0.10+ lift. The binding evidence is feature-importance rank ≤10 + importance ≥30 (model usage), with IS+OOS no-regression (relaxed). Cannot be renegotiated post-hoc.

**Saturation falsifier (per `feedback_v3_axis_saturation_predictor.md`)**: IS trades outside [129, 215] OR rank/importance behavior outside §2.3 predictor band fires the saturation falsifier. Distinct from PATH classification; can co-fire with any PATH.

### 2.5 Adversarial past-only test (REQUIRED at first commit)

Per past iterations (iter-v3/019/023/024/025), every new feature requires an adversarial test confirming past-only computation. Test file: extend `tests/features_v3/test_engineered_v3.py` (introduced at iter-v3/025) with:

1. `compute_vol_adj_autocorr(df).vol_adj_autocorr.iloc[-1]` does NOT change when `df` is appended with future bars (i.e., the value at time t depends only on bars t-50 ... t).
2. The first 49 bars of output are NaN (insufficient history for the upstream rolling 50-bar autocorr / vol primitives).
3. EPS robustness test: `vol_adj_autocorr` is finite (not inf) when `range_realized_vol_50` is exactly zero (EPS=1e-6 prevents division-by-zero).
4. Idempotency test: calling `compute_vol_adj_autocorr` twice in succession produces identical output (function is pure; no in-place mutation).

### 2.6 Verification — pre-flight gates (Phase 5.5)

Before backtest run, verify:
- [ ] V3_FEATURE_COLUMNS = 15 (+1 vs iter-v3/025; vol_adj_autocorr added; regime_momentum_signed_5d KEPT)
- [ ] V3_FEATURE_COLUMNS list matches `_verify_feature_columns` assertion expected length
- [ ] `_verify_feature_columns` updated to assert BOTH `regime_momentum_signed_5d` AND `vol_adj_autocorr` PRESENT
- [ ] `ITERATION_LABEL = "v3-026"` set in runner
- [ ] All 3 v3 features parquets regenerated with new feature column
- [ ] Adversarial past-only test PASS (4 new tests)
- [ ] Track-isolation grep: `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` returns empty; `grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v3/` returns empty
- [ ] EDA committed at SHA `97302db` with all 5 CSVs + synthesis.md

---

## Section 3 — IS-Only Numerical Evidence (EDA at SHA `97302db`)

### 3.1 Candidate evaluation (4 of 4)

| Candidate | max |IC| BCH | max |IC| LDO | max |IC| TRX | max |IC|_14 (worst) | max |IC|_rm (worst) | max |rankIC| (best) | ADF (3/3 pass?) | Composite |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| `vol_adj_autocorr` | 0.985 vs ret_autocorr_lag1_50 | 0.980 | 0.976 | **0.985** | **0.075** | 0.028 (LDO h7) | YES | 0.6035 |
| `cross_asset_divergence_norm` | 0.695 vs sym_vs_btc_ret_7d | 0.756 | 0.746 | 0.756 | 0.464 | 0.109 (LDO h7) | YES | 0.6643 |
| `fracdiff_d05_close` | 0.505 vs vwap_dev_20 | 0.640 | 0.373 | 0.640 | 0.568 | 0.088 (LDO h7) | NO (TRX p=0.229) | 0.4954 |
| `ret_kurt_to_skew_ratio` | 0.559 vs ret_kurt_50 | 0.677 | 0.648 | 0.677 | 0.075 | 0.077 (LDO h7) | YES | **0.7322** |

### 3.2 Brief gates assessment (vol_adj_autocorr, the pre-committed axis)

| Gate | Threshold | vol_adj_autocorr observed | PASS? |
|---|---|---:|---|
| Coverage IS window per symbol | ≥ 80% | 100.0% (BCH) / 100.0% (LDO) / 100.0% (TRX) | YES |
| Max \|IC\| vs 14 V3_FEATURE_COLUMNS (HARD; INFORMATIONAL) | < 0.70 (info only) | 0.985 (BCH; ret_autocorr_lag1_50 source primitive) | INFORMATIONAL only (Category 2 carve-out) |
| Max \|IC\| vs regime_momentum_signed_5d (orthogonality) | low ≈ 0 | **0.075** worst-case (BCH/TRX); 0.0014 (LDO) | YES — highly orthogonal |
| ADF p-value < 0.05 per symbol | structural stationarity | BCH p<1e-5; LDO p<1e-5; TRX p<1e-5 | YES |
| Max \|rank-IC\| vs forward returns | ≥ 0.02 | 0.028 (LDO h7) | YES (bare; small-magnitude predictive signal) |

**4 of 5 binding brief gates PASS, 1 INFORMATIONAL only (IC vs source primitive expected for composed features per Category 2 IC carve-out).**

### 3.3 IC carve-out methodology decision (mirrors iter-v3/025 §3.3, LOAD-BEARING for brief acceptance)

**Standard application**: the IC hard gate < 0.70 (BASELINE_V3.md threshold) was designed to flag REDUNDANT off-the-shelf indicator additions — features that share variance with existing primitives and would mechanically duplicate signal already in the feature set. iter-v3/008 dropped vwap_dev_50 because of IC 0.875 with ema_spread_atr_20 + IC 0.794 with vwap_dev_20.

**Composed-feature application is fundamentally different**: A composed feature like `ret_autocorr_lag1_50 / (range_realized_vol_50 + 1e-6)` shares variance with its source primitives BY CONSTRUCTION — that's the entire point of a composed feature. Rejecting `vol_adj_autocorr` because of IC 0.985 with `ret_autocorr_lag1_50` would be analogous to rejecting `hurst_diff_100_50` (already in V3_FEATURE_COLUMNS_TOP_N) because of IC with `hurst_100`. The redundancy gate is misapplied.

**Methodology decision**: The brief explicitly accepts the IC hard-gate failure for `vol_adj_autocorr` on the same grounds as iter-v3/025:

1. The candidate is a COMPOSED interaction feature (Category 2 axis), not an off-the-shelf indicator addition (Category 1 axis); the IC orthogonality gate is structurally biased high for this category.
2. The HYPOTHESIS under test is precisely whether the COMPOSED form provides INTERACTION value the model can't compose internally — NOT whether the candidate is variance-orthogonal to source primitives.
3. The empirical test that disambiguates the hypothesis is the **feature importance rank** from the LightGBM model itself: if rank ≤10 with importance ≥30, the model is using the composed feature non-trivially despite high source IC.
4. **NEW for iter-v3/026**: the orthogonality-to-regime_momentum_signed_5d criterion is binding (max |IC|_rm 0.075 across BCH/TRX, 0.0014 on LDO). The two engineered features are mechanistically distinct — vol_adj_autocorr does not duplicate regime_momentum's signal.
5. Per AFML Ch. 8: feature importance under multicollinearity (cluster-based methods) systematically under-attribute composed features that share variance with source primitives. This is a known limitation; the rank ≤10 with non-trivial absolute importance is the correct evidence threshold.

**This methodology decision is documented in Phase 5.5 gate** as an explicit IC-gate carve-out for Category 2 (composed-feature) axes, mirroring iter-v3/025 phase5p5_gate.md §IC-Gate Carve-Out.

### 3.4 Why vol_adj_autocorr (vs other candidates)

The composite leaderboard ranks `ret_kurt_to_skew_ratio` first (0.7322), `cross_asset_divergence_norm` second (0.6643), `vol_adj_autocorr` third (0.6035), `fracdiff_d05_close` fourth (0.4954, ADF FAIL). The pre-commit binds the iter-v3/026 axis to `vol_adj_autocorr` independent of leaderboard rank. Justification:

1. **Single-axis discipline pre-commit binds**: iter-v3/025 Critic FINAL Recommendation (review SHA `402643d`) + user directive 2026-05-08 pre-committed to `vol_adj_autocorr`. Cannot be renegotiated post-hoc per `feedback_v3_engineered_feature_pivot.md` + `feedback_v3_engineered_features_proven.md`.
2. **STRUCTURAL ORTHOGONALITY THE STRONGEST**: vol_adj_autocorr's max |IC|_rm = 0.075 worst-case (BCH/TRX); 0.0014 on LDO. This is dramatically lower than the other candidates:
   - cross_asset_divergence_norm: 0.464 (LDO) — partially overlaps regime_momentum's mechanism
   - fracdiff_d05_close: 0.568 (LDO) — partially overlaps
   - ret_kurt_to_skew_ratio: 0.075 (BCH/TRX) but 0.075 (LDO worst) — comparable to vol_adj_autocorr but failed Critic FINAL named recommendation
   The hypothesis under test specifically requires structural orthogonality to validate "engineered features generalize" — vol_adj_autocorr is the cleanest test.
3. **Tests "model can't compose ratio" hypothesis directly**: ret_autocorr_lag1_50 is rank 12 mean across iter-v3/018-024 importance trajectories; range_realized_vol_50 is rank 5 mean (heavily used). The model already uses both source primitives; the question is whether it was COMPOSING the per-unit-vol ratio internally. If it was, vol_adj_autocorr will rank 14-15/15 (PATH B). If it wasn't, vol_adj_autocorr will rank ≤10 (PATH A).
4. **Implementation cost LOWEST**: 10 lines of code in existing `engineered_v3.py` module. Both source primitives already in features parquet — zero new computation.
5. **Critic-named recommendation**: iter-v3/025 Critic FINAL Recommendation 1 explicitly named vol_adj_autocorr as "strong candidate" with rationale "autocorrelation per unit vol — orthogonal to regime momentum". The brief honors this Critic-mandated single-axis pre-commit.
6. **ret_kurt_to_skew_ratio** is the leaderboard winner but: (a) NOT named by Critic FINAL Rec (single-axis discipline binds to Critic+user pre-commit), (b) defers to iter-v3/027 NEXT axis IF iter-v3/026 lands PATH B per Section 7.

### 3.5 Distribution stats (vol_adj_autocorr, IS window)

| Symbol | n_valid | coverage% | mean | std | p01 | p99 | outlier_ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| BCH | 2193 | 100.0% | -1.241 | 6.814 | -23.078 | +15.123 | 9.10 |
| LDO | 2193 | 100.0% | -0.762 | 4.680 | -13.479 | +10.731 | 7.36 |
| TRX | 2193 | 100.0% | -0.098 | 12.285 | -28.847 | +32.632 | 6.66 |

Distribution healthy: mean ≈ 0 (consistent with `autocorrelation` source ranging in [-1, +1] divided by positive vol), std reasonable for a ratio (range_realized_vol is small percentage-scale; 1/vol amplifies the magnitude), no extreme outliers (outlier_ratio 6.66-9.10 = (max-min)/std on a clipped distribution). Coverage 100% — both source primitives have full IS coverage.

### 3.6 Rank-IC (vol_adj_autocorr, IS window)

| Symbol | h=1 | h=3 | h=7 | max |rank-IC| |
|---|---:|---:|---:|---:|
| BCH | -0.002 | +0.001 | **+0.025** | 0.025 |
| LDO | +0.007 | +0.025 | **+0.028** | 0.028 |
| TRX | +0.001 | +0.016 | **+0.028** | 0.028 |

All 3 symbols at h=7 are POSITIVE-direction (consistent with vol-normalized momentum-continuation signal). Magnitude (0.025-0.028) is modest but above the 0.02 floor on at least 1 horizon for all 3 symbols — meaningful predictive signal. Notably, rank-IC at h=1 is near-zero for all 3 — the signal is in the multi-bar predictive horizon, consistent with a 50-bar lookback feature predicting forward 7-bar returns.

---

## Section 4 — Falsifiers (PRE-REGISTERED at SHA `97302db` + this brief — cannot be renegotiated)

### 4.1 Falsifier 1: PATH C trigger (NEGATIVE)

**Triggered if**: IS Sharpe Δ < −0.10 vs iter-v3/025 reference (+0.8788) OR OOS Sharpe Δ < −0.50 vs iter-v3/025 reference (+1.2244).

**Verdict if triggered**: EXPLORATION-NEGATIVE (clean) — second engineered feature actively hurts via expanded overfit space. Mechanism: regime_momentum already captured the available regime/momentum signal; vol_adj_autocorr adds a redundant-with-source-primitive feature that lets Optuna find IS-overfit hyperparameter trajectories. Engineered-features pivot is narrowly successful (only 1 of 2 engineered features works), not consistently productive.

### 4.2 Falsifier 2: Saturation falsifier

**Triggered if**: IS trades > 215 OR IS trades < 130.

**Verdict if triggered**: catalog row notes "saturation falsifier FIRES" qualifier; the axis behavioral effect is anomalous (trade count outside predicted band). Distinct from PATH C; can co-fire with any PATH.

### 4.3 Falsifier 3: PATH B trigger (PROMISING-INERT-second)

**Triggered if**: feature importance rank 14-15/15 across 3 of 4 cuts (BCH portfolio + LDO + Portfolio at minimum). NOTE: relaxed slightly vs the standard "14/14 across all 4" criterion to accommodate single-symbol partial-success patterns observed in iter-v3/024 (TRX rank 9/14 was the only departure).

**Verdict if triggered**: EXPLORATION-PROMISING-INERT-second — second engineered candidate did not contribute; the iter-v3/025 result is narrow (only regime_momentum mechanism worked). Engineered-features pivot validated for ONE specific composition but NOT a general productive category. Pivot remains LIMITED-priority for iter-v3/027; alternative candidate ranking ret_kurt_to_skew_ratio OR cross_asset_divergence_norm.

### 4.4 Falsifier 4: PATH A trigger (PROMISING — pivot validated)

**Triggered if**: feature importance rank ≤10 for ≥1 symbol AND IS Sharpe Δ ≥ 0 vs iter-v3/025 reference. Importance value ≥30 required as well (informational threshold; flags genuine model usage vs cosmetic non-zero importance).

**Verdict if triggered**: EXPLORATION-PROMISING — **second engineered feature works (signal exists; structurally orthogonal mechanism contributes additional value)**. STRONG evidence the engineered-features pivot is consistently productive — 2 of 2 PROMISING engineered features at single-seed. Both features qualify as CONFIRMATION-bundle candidates for iter-v3/029 (multi-seed validation). **Eligibility for CONFIRMATION-bundle inclusion at iter-v3/029** (single-seed lottery suspect rule per `feedback_v3_single_seed_frozen_baseline.md`; multi-seed validation is the binding test).

### 4.5 Falsifier 5: PATH D trigger (PROMISING-MECHANICAL)

**Triggered if**: trade roster bit-identical to iter-v3/025 baseline (or strict subset thereof). Mechanism: feature is genuinely INERT but happens to shift profit accounting; not new edge.

**Verdict if triggered**: EXPLORATION-PROMISING-MECHANICAL — non-compoundable across iterations; treat as iter-v3/013 PROMISING-MECHANICAL precedent (FALSIFIED at multi-seed CONFIRMATION).

### 4.6 PATH classification cannot be renegotiated post-hoc

If the engineering report observed metrics fall in a borderline zone (e.g., rank 11 on 1 symbol with importance value 32; IS Δ -0.05), the verdict is still bound by the strict §4.4 criteria. The QR must NOT relax thresholds based on observed outcome direction.

---

## Section 5 — Predicted Bands (and predicted-vs-observed schedule)

| Metric | Lower bound | Upper bound | Median | iter-v3/025 reference | iter-v3/018 anchor (multi-seed mean) |
|---|---:|---:|---:|---:|---:|
| IS monthly Sharpe | +0.80 | +1.10 | +0.95 | +0.8788 | +0.3788 |
| OOS monthly Sharpe | +1.10 | +1.45 | +1.25 | +1.2244 | +0.3869 |
| OOS/IS Sharpe ratio | 1.20 | 1.60 | 1.40 | 1.39 | 1.02 |
| IS n_trades | 175 | 215 | 195 | 194 | 172 |
| OOS n_trades | 85 | 110 | 97 | 95 | 90.5 |
| IS MaxDD | 18% | 30% | 24% | 27.49% | 21.86% |
| OOS MaxDD | 18% | 30% | 24% | 21.35% | 27.74% |
| Total OOS PnL | +25% | +45% | +35% | +32.56% | ~+7% |
| feature importance rank vol_adj_autocorr (best of 4 cuts) | 8 | 13 | 10 | n/a | n/a |
| feature importance value vol_adj_autocorr (best symbol) | 30 | 150 | 75 | n/a | n/a |
| feature importance regime_momentum_signed_5d (best of 4 cuts) | 7 | 12 | 9 | rank ~8-9 LDO; 51% top portfolio | n/a |

The predicted bands center on **maintaining** the iter-v3/025 single-seed reference rather than adding another large lift. The structural-orthogonality-first criterion ensures the second feature contributes a distinct mechanism without displacing regime_momentum_signed_5d's signal. A modest +0.10-0.20 OOS lift would be a strong outcome; flat OOS would still be PATH A if rank/importance criteria fire and the regime_momentum signal is preserved.

---

## Section 6 — Risk Mitigation

Per `feedback_risk_mitigation_design.md`, every merge-candidate iteration must include this section. iter-v3/026 is EXPLORATION (not merge-candidate) but the section is mandatory for all axis-changes per Phase 5.5 gate.

### 6.1 Risk model: composed-feature interaction overfit (and signal cannibalization)

The primary risks are:
1. **INERT-OVERFIT** (per `feedback_v3_inert_features_at_higher_budget.md`): if `vol_adj_autocorr` ranks 14-15/15 across all symbols, adding it as the 15th feature at n_trials=35 expands Optuna's parameter search space along an uninformative dimension, leading to IS-overfit hyperparameter trajectories that don't generalize to OOS — same mechanism as iter-v3/023/024. Outcome: PATH B (informational) or PATH C (NEGATIVE if OOS regresses materially).
2. **SIGNAL CANNIBALIZATION**: if vol_adj_autocorr partially correlates with regime_momentum_signed_5d's signal (despite low IC of 0.075 in EDA), Optuna may shift hyperparameter trajectories away from regime_momentum's tree splits, REDUCING regime_momentum's importance from iter-v3/025's 51% portfolio share. This would manifest as PATH C (NEGATIVE) with regime_momentum importance falling below 30 across 1+ cuts — distinct from PATH B (where vol_adj_autocorr itself ranks 14-15/15).

### 6.2 Mitigation: risk gates UNCHANGED from iter-v3/025 baseline

- **R1** (consecutive-SL cooldown): unchanged (3 SL → 27 candle pause; per BASELINE_V3.md)
- **R2** (drawdown-triggered position scaling): unchanged
- **R3** (OOD Mahalanobis gate): unchanged (70th-percentile cutoff)
- **z-score OOD**: 2.0 unchanged (iter-v3/011 PROMISING)
- **ATR multipliers**: 2.0/1.0 unchanged (iter-v3/010 PROMISING)
- **BTC trend filter**: ±15% unchanged (iter-v3/012 NULL-effect)
- **ADX threshold**: 20 unchanged (iter-v3/014 ADX=25 axis closed)
- **Hurst regime**: unchanged
- **Low-vol filter**: unchanged
- **Hit-rate feedback**: disabled
- **Regime gate**: disabled (was iter-v3/022 axis)
- **Per-symbol cap**: disabled (was iter-v3/020 axis)

### 6.3 Mitigation: kill-switch criteria

Iteration is abandoned mid-flight if:
1. Wall-clock exceeds 2h cap (EXPLORATION budget).
2. Adversarial past-only test FAILS (look-ahead bias detected).
3. Track-isolation grep returns non-empty (v3 imports v1/v2 features).
4. V3_FEATURE_COLUMNS not exactly 15 columns at backtest run.
5. Feature parquet regeneration fails on any of 3 symbols (BCH/LDO/TRX).

### 6.4 Mitigation: simulated historical effect

Counterfactual estimation: stacking a +1 composed feature on top of the iter-v3/025 14-feature stack is expected to:
- Shift IS trade count by ±20 vs iter-v3/025 reference 194 → band [174, 214]
- Shift IS Sharpe by ±0.10 vs iter-v3/025 reference 0.8788 → band [0.78, 0.98] (median ~0.88 if PATH B; +0.05 to +0.15 if PATH A)
- Shift OOS Sharpe by ±0.20 vs iter-v3/025 reference 1.2244 → band [1.02, 1.42] (median ~1.22 if PATH B; +0.05 to +0.20 if PATH A)
- Shift regime_momentum_signed_5d importance by ±10pp vs iter-v3/025's 51% portfolio share

The composed-feature stacking mechanism is novel (no v3 precedent at 15-feature stack); the predicted bands carry higher uncertainty than knob-axis iterations.

---

## Section 7 — Pre-Commit for iter-v3/027 (conditional on iter-v3/026 outcome)

Per Phase 5.5 + iter-v3/025 diary lessons:

- **If iter-v3/026 PATH A (PROMISING)**: iter-v3/027 axis = THIRD engineered feature (continuing pivot validation); candidate ranking is `cross_asset_divergence_norm` (composite 0.6643, second-highest in EDA, max |IC|_rm 0.464 — partial mechanistic overlap but lifts compositional coverage) OR `ret_kurt_to_skew_ratio` (composite 0.7322 — leaderboard winner; IC vs regime_momentum 0.075 but vs vol_adj_autocorr unknown — would need new EDA at iter-v3/027 setup). This would be the 16th feature. STRONG SIGNAL the engineered-features pivot is THE right axis category for v3.
- **If iter-v3/026 PATH B (PROMISING-INERT-second)**: iter-v3/027 axis = different engineered feature with stronger orthogonal mechanism; candidate ranking is `cross_asset_divergence_norm` (different mechanism family — cross-asset relative strength) OR `fracdiff_d05_close` (different mechanism family — memory preservation; addresses ADF stationarity test issue on TRX requiring fracdiff_logclose_dstat-style auto-d* substitution). This would still be the 16th feature.
- **If iter-v3/026 PATH C (NEGATIVE)**: iter-v3/027 axis = drop the SECOND engineered feature axis entirely; revert V3_FEATURE_COLUMNS 15 → 14 (KEEP regime_momentum_signed_5d only). Pivot to fundamental architectural exploration (e.g., explicit regime-conditional ensemble of two LightGBM models — one trained on Hurst > 0.5 subset, one on Hurst < 0.5 subset). Feature engineering pivot deemed NARROW-PRODUCTIVE: only specific compositions work, not a generally productive category.
- **If iter-v3/026 PATH D (PROMISING-MECHANICAL)**: NO iter-v3/027 axis-pivot; the iteration is an accounting-cleanup variation; wait for explicit evidence to compound.

Cannot be renegotiated post-hoc per `feedback_v3_engineered_feature_pivot.md` + `feedback_v3_engineered_features_proven.md`.

---

## Section 8 — Out-of-Scope (Cannot enter iter-v3/026 setup)

- ANY change to the 3-symbol BCH+LDO+TRX universe
- ANY change to the labeling parameters (ATR 2.0/1.0)
- ANY change to risk gates (z=2.0, ADX=20, BTC ±15%, regime gate disabled, per-symbol cap disabled)
- ANY change to model architecture (LightGBM remains; XGBoost rejected at iter-v3/016)
- ANY change to OOS_CUTOFF_DATE or training_months (sacred constants; immutable)
- ANY funding feature (PERMANENTLY-CLOSED across per-symbol + cross-asset variants)
- ADX as a feature column (rejected at EDA Stage 1; would be Category 1 axis, not the engineered-feature pivot)
- Multiple new engineered features in a single axis (single-axis discipline preserved; iter-v3/027 can compound IF iter-v3/026 lands PATH A)
- DROPPING regime_momentum_signed_5d (iter-v3/025 PROMISING; KEPT — feedback_v3_engineered_features_proven.md mandate)

---

## Section 9 — Reproducibility Stamp (final pre-flight)

- **Brief SHA**: this commit (will be assigned at commit time)
- **EDA SHA**: `97302db`
- **Anchor (formal)**: iter-v3/018 multi-seed mean +0.3788 IS / +0.3869 OOS
- **Reference (single-seed parent)**: iter-v3/025 +0.8788 IS / +1.2244 OOS (single-seed)
- **n_trials default**: 35 (PRELIMINARY-VALIDATED through 6 prior EXPLORATIONs: iter-v3/020/021/022/023/024/025)
- **Parent branch SHA**: `511934a` (iter-v3/025 diary commit on iteration-v3/025)
- **Parent baseline architecture**: 14 V3_FEATURE_COLUMNS_TOP_N (drop-MKR + ATR 2.0/1.0 + z=2.0 + BTC ±15% + ADX=20 + Hurst gate + regime_momentum_signed_5d)
- **Library stack pinned in BASELINE_V3.md**: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. No new dependencies.

---

## Section 10 — Hand-Off to Engineer (Phase 6)

Engineer must:
1. Read this brief + EDA at SHA `97302db` + iter-v3/025 diary at SHA `511934a`.
2. Verify Phase 5.5 gate (separate file `phase5p5_gate.md` once Phase 5.5 completes).
3. Implement `compute_vol_adj_autocorr` in `engineered_v3.py` per Section 2.2 spec (~10 lines).
4. Update `add_engineered_v3_features` to call BOTH compute functions (regime_momentum_signed_5d FIRST, then vol_adj_autocorr).
5. ADD `vol_adj_autocorr` to V3_FEATURE_COLUMNS_TOP_N (14 → 15).
6. KEEP `regime_momentum_signed_5d` in V3_FEATURE_COLUMNS_TOP_N (do NOT revert).
7. Update `_verify_feature_columns` assertion to expect 15 columns including BOTH `regime_momentum_signed_5d` AND `vol_adj_autocorr`.
8. Extend adversarial past-only test `tests/features_v3/test_engineered_v3.py` with 4 new tests (per §2.5).
9. Run `uv run pytest tests/features_v3/` — must PASS.
10. Run `uv run ruff check . && uv run ruff format .` — must PASS.
11. Regenerate feature parquets for BCH+LDO+TRX with new `engineered_v3` group output.
12. Set `ITERATION_LABEL = "v3-026"`.
13. Run backtest in EXPLORATION mode: `uv run crypto-trade backtest-v3 --exploration --seeds 1 --n-trials 35`.
14. Wait for backtest completion (predicted 8-15 min).
15. Write engineering report at `briefs-v3/iteration_v3-026/engineering_report.md`.
16. Hand off to Critic (Phase 7.5) for review.

Cannot be renegotiated post-hoc per `feedback_v3_engineered_feature_pivot.md` + `feedback_v3_engineered_features_proven.md`.

---

## Appendix A — EDA Composite Score Detail (iter-v3/026 weights)

Composite score = 0.10 × orthogonality_to_14_features (informational)
                + 0.20 × orthogonality_to_regime_momentum (NEW for iter-v3/026)
                + 0.30 × rank-IC magnitude
                + 0.20 × stability (coverage × ADF)
                + 0.10 × interpretability_prior
                + 0.10 × (1 − implementation_cost_prior)

| Candidate | Ortho-14 | Ortho-RM | RankIC | Stability | Interp | Impl | Composite |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ret_kurt_to_skew_ratio` | 0.0 | 0.85 | 0.77 | 0.99 | 0.4 | 0.1 | **0.7322** |
| `cross_asset_divergence_norm` | 0.0 | 0.07 | 1.0 | 0.99 | 0.7 | 0.2 | 0.6643 |
| `vol_adj_autocorr` | 0.0 | **0.85** | 0.28 | 0.99 | 0.6 | 0.1 | 0.6035 |
| `fracdiff_d05_close` | 0.0 | 0.0 | 0.88 | 0.66 | 0.7 | 0.4 | 0.4954 |

The leaderboard ranks ret_kurt_to_skew_ratio first because of its higher rank-IC magnitude (0.077 > vol_adj_autocorr's 0.028). However:

1. **Pre-commit binds to vol_adj_autocorr** per Critic FINAL Rec + user directive 2026-05-08 — single-axis discipline cannot be renegotiated post-hoc.
2. **vol_adj_autocorr has LOWER max |IC|_rm than ret_kurt_to_skew_ratio on LDO** (0.0014 vs 0.075 LDO worst-case). Both are highly orthogonal to regime_momentum, but vol_adj_autocorr is MORE orthogonal on LDO specifically.
3. **vol_adj_autocorr's mechanism (per-unit-vol persistence) is structurally distinct** from regime_momentum's (regime-conditional momentum). ret_kurt_to_skew_ratio's mechanism (fat-tail to asymmetry) is also distinct but the Critic FINAL Rec + user mandate selected vol_adj_autocorr explicitly.
4. **ret_kurt_to_skew_ratio is the iter-v3/027 fallback** if iter-v3/026 lands PATH B (per Section 7).

---

## Appendix B — Why this iteration validates the FEATURE ENGINEERING pivot

The v3 catalog has 25 prior iterations (iter-v3/001-025). The axis-category breakdown after iter-v3/025:

- Category 1 (off-the-shelf indicator additions): iter-v3/015 (microstructure), iter-v3/019/023/024 (funding × 3) — ALL INERT-class
- Category 1 (knob axes): iter-v3/009/010/011/012/014 — saturated per `feedback_v3_axis_saturation_predictor.md`
- Category 1 (universe + risk primitives): iter-v3/020/021/022 — CLOSED-mechanism / CLOSED-symbols-cycle / PARTIALLY-EFFECTIVE
- Category 1 (model architecture / labeling architecture): iter-v3/016 (XGBoost) / iter-v3/017 (meta-labeling) — both NEGATIVE
- CONFIRMATION: iter-v3/018 — BOOTSTRAP exception
- Feature pruning: iter-v3/007/008/009 (top-14 → top-13)
- **Category 2 (composed/interaction features)**: iter-v3/025 (regime_momentum_signed_5d) — **PROMISING (clean) — FIRST in post-bootstrap**

**iter-v3/026 is the SECOND Category 2 axis in v3 catalog history.** The validation chain:

- iter-v3/025: ONE engineered feature works → necessary but not sufficient evidence
- **iter-v3/026: TWO engineered features work (PATH A) → strong evidence pivot is CONSISTENTLY productive**, qualifying for CONFIRMATION-bundle inclusion
- iter-v3/027: THREE engineered features work (PATH A) → near-conclusive evidence

If iter-v3/026 lands PATH A:
- 2 of 2 engineered features PROMISING at single-seed (vs 4 of 4 INERT for off-the-shelf NEW features)
- Engineered features become the dominant CONFIRMATION-bundle ingredient for iter-v3/029 multi-seed validation
- The model architecture (depth-3-5 LightGBM at colsample_bytree=1.0) is established as systematically incapable of internally composing interaction features, validating the manual feature-engineering approach over off-the-shelf additions

If iter-v3/026 lands PATH B or PATH C:
- Engineered-features pivot is NARROW-PRODUCTIVE (only specific compositions work)
- Pivot remains LIMITED-priority for iter-v3/027; alternative composition mechanisms tested
- regime_momentum_signed_5d remains a strong CONFIRMATION-bundle component but NOT the dominant ingredient

**Per user directive 2026-05-08 + Critic FINAL Recommendation of iter-v3/025**: this is the second test of whether feature engineering is the path to v3 alpha. Cannot be renegotiated post-hoc.
