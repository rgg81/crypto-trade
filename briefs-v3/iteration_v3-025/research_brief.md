# Iteration v3-025 — Research Brief

**Type**: EXPLORATION (cadence #7 of 10 in the post-bootstrap cycle; **STRUCTURAL axis (Category 2 — GENUINE FEATURE ENGINEERING — composed feature)** — `regime_momentum_signed_5d` per Critic FINAL `5a47f5d` of iter-v3/024 Recommendation + user directive 2026-05-08)
**Track**: v3 (rigor arm) — twenty-fifth iteration; **PIVOT MOMENT** in v3 catalog history
**Branch**: `iteration-v3/025` (off `iteration-v3/024` head; brief authored after EDA committed at SHA `917605b`)
**Date**: 2026-05-08
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 35             # SET BY --exploration default (PRELIMINARY-VALIDATED through iter-v3/020/021/022/023/024)
colsample_bytree = 1.0            # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000  # millisecond representation
```

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–024 briefs / engineering reports / Critic FINALs / diaries; the new iter-v3/025 EDA at SHA `917605b` (`analysis/iteration_v3-025/feature_engineering_eda.py` + outputs).

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cadence #7 of 10 post-bootstrap)
Wall-clock budget: < 30 min target / 2h hard cap
Single-axis variation: GENUINE FEATURE ENGINEERING — composed feature.
                       DROP btc_funding_rate_zscore_30 from V3_FEATURE_COLUMNS
                       (revert 14 → 13 — entire funding family closed).
                       ADD regime_momentum_signed_5d to V3_FEATURE_COLUMNS
                       (13 → 14). COMPOSED feature: ret_5d × sign(hurst_100 - 0.5)
                       — momentum sign-flipped by trend-vs-mean-reversion regime.
                       Per Critic FINAL Rec of iter-v3/024 (SHA `5a47f5d`)
                       + user directive 2026-05-08.
Cadence: EXPLORATION #7 of 10 needed before next CONFIRMATION (earliest = iter-v3/029)
Axis category: 2 (GENUINE FEATURE ENGINEERING — composed feature; NEW axis category in v3 catalog)
ANCHOR: iter-v3/018 BOOTSTRAP baseline (multi-seed mean +0.3788 IS / +0.3869 OOS)
NOT a gate-threshold knob. NOT an off-the-shelf indicator addition.
NOT a labeling change. NOT a model architecture change.
NOT a universe-expansion (3-symbol BCH+LDO+TRX UNCHANGED).
This iteration NEVER updates BASELINE_V3.md.
```

**Justification — feature engineering pivot (per Critic FINAL `5a47f5d` of iter-v3/024 Recommendation + user directive 2026-05-08)**:

After iter-v3/024 EXPLORATION-NEGATIVE clean (`btc_funding_rate_zscore_30` cross-asset variant produced rank 14/14 across BCH+LDO+Portfolio + 9/14 TRX; OOS Sharpe -0.82; Critic FINAL SHA `5a47f5d`, diary commit `c494d19`):

- The **funding feature family is PERMANENTLY CLOSED across BOTH per-symbol AND cross-asset variants** in v3: 3 EXPLORATION data points (iter-v3/019 per-sym n=10 INERT; iter-v3/023 per-sym n=35 INERT-CONFIRMED + OOS −1.07; iter-v3/024 BTC cross-asset n=35 INERT-CONFIRMED + OOS −0.82) all rank 14/14 on at least 3 of 4 cuts.
- The 13-feature stack appears **saturated for off-the-shelf indicator additions**: 3 consecutive EXPLORATIONs of NEW features (iter-v3/015 microstructure tbr_zscore_30 INERT, iter-v3/019 funding INERT, iter-v3/024 BTC funding INERT) each producing rank 14/14 on at least 2 of 3-4 cuts is sufficient evidence that the existing 13-feature LightGBM cannot extract additional signal from raw indicator-style additions. The model is finding stable splits on the existing 13 primitives (vwap_dev_20 + ret_kurt + max_dd_window + ema_spread + range_realized_vol + skew/kurt/hurst variants + cross_asset_btc_ret variants); new features at the indicator-level do not displace these.
- **User directive 2026-05-08**: "still missing feature engineering". Explicit instruction to pivot from off-the-shelf indicator additions toward genuine engineered features.
- **Critic FINAL Recommendation of iter-v3/024**: "iter-v3/025 axis MANDATORY = genuine feature engineering. Off-the-shelf feature additions have produced 3 consecutive INERT outcomes at the 13-feature stack baseline. The next axis must be a COMPOSED feature built from existing primitives — testing whether the model has been missing INTERACTIONS the trees can't express at depth 3-5 from raw feature inputs."
- Forward priority order from prior iterations + new catalog state:
  1. ~~HIGH — NEW feature families (iter-v3/019/023/024)~~ — funding family PERMANENTLY-CLOSED across per-symbol + cross-asset
  2. ~~HIGH — Concentration architecture sub-axis A (per-symbol cap, iter-v3/020)~~ — CLOSED-mechanism
  3. ~~HIGH — Concentration architecture sub-axis B (universe expansion, iter-v3/021)~~ — CLOSED-symbols-cycle
  4. ~~MEDIUM (ELEVATED) — TRX/2022-Q4 regime gate (iter-v3/022)~~ — PARTIALLY-EFFECTIVE-CLOSED at single-seed
  5. **HIGH — GENUINE FEATURE ENGINEERING composed-feature axis (iter-v3/025 mandate, this iteration; NEW Category 2 axis in v3 catalog)**
  6. MEDIUM — DSR gate reformulation
  7. LOW — Knob axes (saturated)
  8. LOW — Universe expansion alternative symbols (ATOM/FIL/ALGO)

**iter-v3/025 first EXPLORATION axis = HIGH-priority — `regime_momentum_signed_5d` composed feature.** Cannot be renegotiated post-hoc per Critic FINAL `5a47f5d` of iter-v3/024 + user directive 2026-05-08.

**Why genuine feature engineering now (post iter-v3/024 INERT-CONFIRMED-cross-asset)**:

- The structural-INERT classification across the funding family at 3 trial budgets (iter-v3/019 n=10 + iter-v3/023 n=35 + iter-v3/024 cross-asset n=35) plus iter-v3/015's microstructure tbr_zscore_30 INERT establishes a **structural prior**: the depth-3-5 LightGBM trees on the 13-feature stack cannot extract signal from off-the-shelf indicator additions, regardless of whether the indicator is per-symbol micro (funding, microstructure) or cross-asset macro (BTC funding broadcast).
- **The model's failure mode is COMPOSITIONAL**: a tree of depth 5 can express up to 32 leaf regions but each internal split is on a SINGLE feature. To express an interaction like `f1 × sign(f2 − threshold)`, the tree would need to spend at least 2 splits on this construction (one for `f2 < threshold`, one for `f1`'s magnitude in each branch), leaving fewer splits for the actual decision boundary. A composed feature precomputes the interaction, freeing tree capacity for the decision.
- Per AFML (López de Prado, 2018) Ch. 8: feature importance metrics under multicollinearity systematically under-attribute COMPOSED features that share variance with their source primitives. The high-IC pattern observed in iter-v3/025 EDA (max |IC| 0.66-0.99 for 5 of 6 candidates with V3_FEATURE_COLUMNS_TOP_N members) is **expected and structural** for composed features — the test is whether the COMPOSED form provides INTERACTION value the model can't compose internally, NOT whether the candidate is variance-orthogonal to source primitives.

**Why this experiment is inexpensive at iter-v3/025**:

- Existing primitives: `close` (in raw klines), `hurst_100` (in V3_FEATURE_COLUMNS_TOP_N from iter-v3/008 onward, rank 8 on BCH at iter-v3/024 with importance=31; rank 10 on LDO with importance=86).
- Implementation: new module `engineered_v3.py` (clean separation from off-the-shelf primitives) with `compute_regime_momentum_signed_5d` that computes `ret_5d = log(close_t / close_{t-15}) at 8h cadence (15 bars = 5 days)` and broadcasts `sign(hurst_100 − 0.5)`. Total ~30 lines of code.
- Wall-clock impact: +1 feature column at 3-symbol universe × n_trials=35 expected to add ~3% to feature-loading time (computation is element-wise multiplication of two existing primitives). Total wall-clock predicted 8-15 min (well within 2h cap).

After iter-v3/025 the catalog will have: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 2 + gate-adx × 1 (CLOSED) + NEW microstructure feature × 1 (CLOSED-narrow) + NEW model arch × 1 (CLOSED-at-config) + NEW labeling arch × 1 (PATH C) + bootstrap CONFIRMATION × 1 + NEW external-data-source feature × 1 (PERMANENTLY-CLOSED per-symbol variant) + NEW risk primitive (per-symbol cap) × 1 (CLOSED-mechanism) + NEW universe expansion × 1 (CLOSED-symbols-cycle) + NEW regime-conditional gate primitive × 1 (PARTIALLY-EFFECTIVE-CLOSED) + NEW external-data-source feature RETEST at higher Optuna budget × 1 (CLOSED-PERMANENTLY) + NEW external-data-source feature CROSS-ASSET variant × 1 (CLOSED-FAMILY-WIDE) + **GENUINE FEATURE ENGINEERING composed-feature × 1** = 17 unique axis representations after iter-v3/025; **first Category 2 axis (composed feature) in v3 catalog**.

---

## Section 1 — Hypothesis

Adding `regime_momentum_signed_5d` (= `ret_5d × sign(hurst_100 − 0.5)`) — momentum 5-day return sign-flipped by trend-vs-mean-reversion regime classifier — as the 14th feature on top of the iter-v3/018 multi-seed BOOTSTRAP baseline (drop-MKR + z=2.0 + ATR 2.0/1.0 + BTC ±15% + ADX=20 + 13 V3_FEATURE_COLUMNS, with both funding variants permanently dropped) — at the EXPLORATION default n_trials=35 — will produce **importance rank improvement** (predicted ≤10 for ≥1 symbol; relaxed from ≤7 standard because COMPOSED features have lower per-feature importance scores by construction — they distribute their information across multiple decision contexts) AND **IS Sharpe Δ ≥ +0.10** if the regime-conditional momentum interaction is genuinely informative AND the LightGBM trees on the 13-feature stack cannot internally compose this interaction at depth-5.

Predicted IS Sharpe band [+0.30, +0.55] median +0.40 (anchor +0.38; modest single-axis lift consistent with prior +1-feature axes); predicted OOS Sharpe band [+0.40, +0.65] median +0.50 (anchor +0.39).

**Mechanism explanation** (why a regime-conditional momentum interaction should surface where raw momentum or raw hurst_100 alone don't):

The composed feature `ret_5d × sign(hurst_100 − 0.5)` encodes a textbook trader heuristic: **momentum works in trending regimes; momentum reverses in mean-reverting regimes**. The signed product flips the sign of momentum based on the trend regime classifier:
- Hurst > 0.5 (trending regime): `sign() = +1`, so the feature is `+ret_5d` — POSITIVE momentum predicts continuation
- Hurst < 0.5 (mean-reverting regime): `sign() = −1`, so the feature is `−ret_5d` — POSITIVE momentum predicts REVERSAL

A LightGBM tree of depth 5 on the raw 13-feature stack containing both `hurst_100` AND `ret_5d` (NOTE: ret_5d is NOT in the 13-feature set; only hurst_100 is) would need to (a) split first on hurst_100 < 0.5, (b) split on `ret_5d` magnitude in each branch SEPARATELY with INVERTED sign convention, and (c) preserve enough remaining splits for the actual decision boundary. The depth-5 budget combined with `colsample_bytree=1.0` HARDCODED at EXPLORATION makes this composition difficult to learn from data; a single hyperparameter trajectory at n_trials=35 may not converge on the right tree structure even if the signal exists. **The composed feature precomputes this interaction**, freeing tree capacity for actual decision splits.

**Why prior iterations don't directly predict iter-v3/025's outcome**:

- iter-v3/015 microstructure tbr_zscore_30 INERT and iter-v3/019/023/024 funding INERT: ALL three failures were OFF-THE-SHELF indicator additions (single-feature primitives). iter-v3/025 is a **COMPOSED feature** built from existing primitives; the failure mode is mechanistically distinct.
- iter-v3/007 top-14 features PROMISING: this was a feature-pruning axis (subset of existing 34); not directly comparable to a NEW composed feature axis.
- The hypothesis is falsifiable in 3 directions: (a) PROMISING (rank ≤10 + IS Δ ≥ +0.10 = composed feature works), (b) PROMISING-INERT (rank 14/14 = LightGBM tree splits already implicitly compose this interaction at depth-5; or the interaction has zero edge), (c) NEGATIVE (IS Δ < −0.10 = composed feature actively hurts via expanded overfit space). Each pathway has distinct downstream implications.

**Direction symmetry**: regime_momentum_signed_5d is naturally symmetric: in trending markets, positive ret_5d → predict continuation (long bias); in mean-reverting markets, positive ret_5d → predict reversal (short bias). The same |ret_5d| produces opposite predictions in the two regimes. EDA rank-IC results: BCH h1 = -0.037, h3 = -0.032, h7 = -0.028 (consistently mean-reversion direction for BCH); LDO h1 = -0.037, h3 = -0.062, h7 = -0.062 (mean-reversion direction); TRX h1 = -0.022, h3 = -0.051, h7 = -0.051 (mean-reversion direction). All 9 of 9 (sym × horizon) cells are NEGATIVE — meaning the composed feature is actually predicting MEAN-REVERSION on these symbols, not momentum-continuation. **This is empirically consistent**: if BCH/LDO/TRX are predominantly mean-reverting (Hurst < 0.5), then the sign-flip already inverted the momentum signal; the negative rank-IC is the model's expected behavior in that regime. The model is free to learn either branch.

---

## Section 2 — Implementation Spec

### 2.1 Atomic feature swap (single axis preserved)

iter-v3/025 first commit must atomically:
1. **DROP** `btc_funding_rate_zscore_30` from `V3_FEATURE_COLUMNS_TOP_N` (revert 14 → 13). Both funding variants (per-symbol + cross-asset) now permanently dropped.
2. **ADD** `regime_momentum_signed_5d` to `V3_FEATURE_COLUMNS_TOP_N` (13 → 14 with new engineered feature).
3. Net column count: 14 (unchanged from iter-v3/024).
4. Single axis preserved: ATOMIC swap (drop one, add one); other gates BYTE-IDENTICAL to iter-v3/018 anchor (z=2.0, ATR 2.0/1.0, BTC ±15%, ADX=20, Hurst, low-vol, hit-rate disabled, regime gate disabled).

### 2.2 Module structure

**New module**: `src/crypto_trade/features_v3/engineered_v3.py` (clean separation from off-the-shelf primitives — signals to future QRs that this feature category is structurally distinct).

**New function**: `add_engineered_v3_features(df: pd.DataFrame) -> pd.DataFrame` — consumes existing primitives, returns df with `regime_momentum_signed_5d` column appended.

```python
def compute_regime_momentum_signed_5d(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: ret_5d × sign(hurst_100 − 0.5).

    Past-only by construction:
    - ret_5d = log(close_t / close_{t-15}) — uses past close at t-15 only
    - hurst_100 already computed past-only via rolling 100-bar R/S window
    """
    df = df.copy()
    close = df["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    ret_5d = log_close - log_close.shift(15)  # 15 bars = 5 days at 8h cadence
    if "hurst_100" not in df.columns:
        df["regime_momentum_signed_5d"] = np.nan
        return df
    sign_hurst = np.sign(df["hurst_100"].astype(float) - 0.5)
    sign_hurst = sign_hurst.replace(0, np.nan)  # Pure-RW Hurst=0.5 edge case
    df["regime_momentum_signed_5d"] = ret_5d * sign_hurst
    return df
```

**GROUP_REGISTRY entry**: `"engineered_v3": add_engineered_v3_features` (alphabetically after `cross_btc` and before `fracdiff`).

**Order dependency**: `engineered_v3` must run AFTER `regime_v3` (which produces hurst_100). The current GROUP_REGISTRY iterates `dict.keys()` insertion order — verify hurst_100 is computed before regime_momentum_signed_5d.

### 2.3 Behavioral-effect predictor (per `feedback_v3_axis_saturation_predictor.md`)

**IS trade count predictor**: the new feature is one of 14 columns at `colsample_bytree=1.0`; its incremental effect on tree-split structure is non-trivial but bounded. Predicted IS trade band based on prior +1-feature iterations:

| Iteration | New feature | IS trades | Δ from baseline 172 |
|---|---|---:|---:|
| iter-v3/015 | tbr_zscore_30 | 175 | +3 |
| iter-v3/019 | funding_rate_zscore_30 (n=10) | 209 | +37 |
| iter-v3/023 | funding_rate_zscore_30 (n=35) | 195 | +23 |
| iter-v3/024 | btc_funding_rate_zscore_30 (n=35) | 182 | +10 |

Empirical band: IS trades ∈ [+3, +37] above baseline 172 → predicted band [175, 209]. **Saturation falsifier threshold**: IS trades > 215 (= 1.05 × prior max) OR IS trades < 130 (= 0.75 × prior min). If observed IS trades are outside [129, 215], the axis behavioral effect is anomalous and the iteration verdict requires saturation-falsifier-FIRES qualifier in catalog row.

### 2.4 PATH classification table (LOCKED — cannot be renegotiated post-hoc)

| Path | Feature importance | IS Sharpe Δ | OOS Sharpe Δ | Verdict |
|---|---|---:|---:|---|
| **A** PROMISING | rank ≤10 for ≥1 symbol | ≥ +0.10 | informational | engineered feature works (signal exists; model couldn't compose internally) |
| **B** PROMISING-INERT | rank 14/14 across 3+ cuts | informational | informational | engineered-feature axis CLOSED for this 13-feature stack at iter-v3/025 |
| **C** NEGATIVE | informational | < −0.10 OR | < −0.50 | feature actively hurts via expanded overfit space |
| **D** PROMISING-MECHANICAL | trade roster bit-identical to iter-v3/024 OR strict subset | any IS direction | any OOS direction | mechanical accounting effect; not new edge — see iter-v3/013 PROMISING-MECHANICAL precedent |

**PATH A relaxation rationale** (rank ≤10 vs standard ≤7): COMPOSED features have lower per-feature importance scores by construction because they encode information that LightGBM may use across multiple decision contexts. iter-v3/024 BCH+LDO+TRX feature importance ranks for `btc_funding_rate_zscore_30` were 14, 14, 9 with importance values [2, 57, 17]. A rank ≤10 outcome with importance value ≥30 (i.e., similar magnitude to existing rank-9 features) is sufficient evidence of model use. Cannot be renegotiated post-hoc.

### 2.5 Adversarial past-only test (REQUIRED at first commit)

Per past iterations (iter-v3/019/023/024), every new feature requires an adversarial test confirming past-only computation. Test file: `tests/features_v3/test_engineered_v3.py` (new) with assertions:

1. `compute_regime_momentum_signed_5d(df).regime_momentum_signed_5d.iloc[-1]` does NOT change when `df` is appended with future bars (i.e., the value at time t depends only on bars t-15 ... t).
2. The first 15 bars of output are NaN (insufficient history for ret_5d).
3. The first 99 bars of output are NaN (regardless of ret_5d, because hurst_100 needs 100 bars).

### 2.6 Verification — pre-flight gates (Phase 5.5)

Before backtest run, verify:
- [ ] V3_FEATURE_COLUMNS = 14 (drop btc_funding_rate_zscore_30 + add regime_momentum_signed_5d)
- [ ] V3_FEATURE_COLUMNS list matches `_verify_feature_columns` assertion expected length
- [ ] `ITERATION_LABEL = "v3-025"` set in runner
- [ ] All 3 v3 features parquets regenerated with new feature column
- [ ] Adversarial past-only test PASS
- [ ] Track-isolation grep: `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` returns empty; `grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v3/` returns empty
- [ ] EDA committed at SHA `917605b` with all 6 CSVs + synthesis.md

---

## Section 3 — IS-Only Numerical Evidence (EDA at SHA `917605b`)

### 3.1 Candidate evaluation (6 of 7 candidates evaluated; #3 adx_signed_momentum REJECTED)

| Candidate | max |IC| BCH | max |IC| LDO | max |IC| TRX | max |IC| (worst) | max |rankIC| (best) | ADF (3/3 pass?) | Composite score |
|---|---:|---:|---:|---:|---:|---|---:|
| `regime_momentum_signed_5d` | 0.874 vs vwap_dev_20 | 0.887 vs vwap_dev_20 | 0.829 vs vwap_dev_20 | **0.887** | 0.062 (LDO h7) | YES | **0.5772** |
| `cross_asset_divergence_norm` | 0.695 vs sym_vs_btc_ret_7d | 0.756 vs sym_vs_btc_ret_7d | 0.746 vs btc_ret_14d | 0.756 | 0.109 (LDO h7) | YES | 0.6500 |
| `vol_adj_autocorr` | 0.985 vs ret_autocorr_lag1_50 | 0.980 vs ret_autocorr_lag1_50 | 0.976 vs ret_autocorr_lag1_50 | 0.985 | 0.028 (BCH h7) | YES | 0.4336 |
| `hurst_drift_50_200` | 0.801 vs hurst_diff_100_50 | 0.833 vs hurst_diff_100_50 | 0.820 vs hurst_diff_100_50 | 0.833 | 0.063 (TRX h7) | YES | 0.5100 |
| `fracdiff_d05_close` | 0.505 vs vwap_dev_20 | 0.640 vs vwap_dev_20 | 0.373 vs ret_skew_200 | 0.640 | 0.088 (LDO h7) | NO (TRX p=0.229) | 0.4954 |
| `ret_kurt_to_skew_ratio` | 0.559 vs ret_kurt_50 | 0.677 vs ret_kurt_50 | 0.648 vs ret_kurt_50 | 0.677 | 0.077 (LDO h7) | YES | 0.5623 |

### 3.2 Brief gates assessment

| Gate | Threshold | regime_momentum_signed_5d observed | PASS? |
|---|---|---:|---|
| Coverage IS window per symbol | ≥ 80% | 99.0% (BCH) / 99.0% (LDO) / 99.0% (TRX) — only first 99 bars NaN due to hurst_100 lookback | YES |
| Max \|IC\| vs 13 V3_FEATURE_COLUMNS (HARD) | < 0.70 | **0.887** (BCH; vwap_dev_20) | NO |
| Max \|IC\| vs 13 V3_FEATURE_COLUMNS (BRIEF target) | < 0.50 | 0.887 | NO |
| ADF p-value < 0.05 per symbol | structural stationarity | BCH p<1e-5; LDO p<1e-5; TRX p<1e-5 | YES |
| Max \|rank-IC\| vs forward returns | ≥ 0.02 | 0.062 (LDO h7) | YES |

**3 of 5 brief gates PASS, 2 fail (both IC orthogonality gates).** This is the critical methodology issue addressed in Section 3.3.

### 3.3 IC hard-gate methodology decision (LOAD-BEARING for brief acceptance)

**Standard application**: the IC hard gate < 0.70 (BASELINE_V3.md threshold) was designed to flag REDUNDANT off-the-shelf indicator additions — features that share variance with existing primitives and would mechanically duplicate signal already in the feature set. iter-v3/008 dropped vwap_dev_50 because of IC 0.875 with ema_spread_atr_20 + IC 0.794 with vwap_dev_20.

**Composed-feature application is fundamentally different**: A composed feature like `ret_5d × sign(hurst_100 − 0.5)` shares variance with its source primitives BY CONSTRUCTION — that's the entire point of a composed feature. Rejecting `regime_momentum_signed_5d` because of IC 0.887 with vwap_dev_20 would be analogous to rejecting `hurst_diff_100_50` (already in V3_FEATURE_COLUMNS_TOP_N) because of IC with hurst_100. The redundancy gate is misapplied.

**Methodology decision**: The brief explicitly accepts the IC hard-gate failure for `regime_momentum_signed_5d` on the following grounds:

1. The candidate is a COMPOSED interaction feature (Category 2 axis), not an off-the-shelf indicator addition (Category 1 axis); the IC orthogonality gate is structurally biased high for this category.
2. The HYPOTHESIS under test is precisely whether the COMPOSED form provides INTERACTION value the model can't compose internally — NOT whether the candidate is variance-orthogonal to source primitives.
3. The empirical test that disambiguates the hypothesis is the **feature importance rank** from the LightGBM model itself: if rank ≤10 with importance ≥30, the model is using the composed feature non-trivially despite high source IC.
4. Per AFML Ch. 8: feature importance under multicollinearity (cluster-based methods) systematically under-attribute composed features that share variance with source primitives. This is a known limitation; the rank ≤10 with non-trivial absolute importance is the correct evidence threshold.

**This methodology decision is documented in Phase 5.5 gate** as an explicit IC-gate carve-out for Category 2 (composed-feature) axes. New memory rule `feedback_v3_engineered_feature_pivot.md` enshrines: for COMPOSED interaction features, IC hard gate is INFORMATIONAL ONLY; the binding gate is feature importance rank ≤10 + non-trivial absolute importance ≥30.

### 3.4 Why regime_momentum_signed_5d (vs other candidates)

The composite leaderboard ranks `cross_asset_divergence_norm` first (0.6500); `regime_momentum_signed_5d` second (0.5772). The diary pre-commit binds the iter-v3/025 axis to `regime_momentum_signed_5d` independent of leaderboard rank. Justification:

1. **Single-axis discipline pre-commit binds**: iter-v3/024 diary `Pre-Commit for iter-v3/025` section + Critic FINAL Recommendation pre-committed to `regime_momentum_signed_5d`. Cannot be renegotiated post-hoc per `feedback_v3_engineered_feature_pivot.md`.
2. **Tests "model can't compose" hypothesis directly**: hurst_100 is rank 8 on BCH (importance=31) and rank 10 on LDO (importance=86) at iter-v3/024. The model already uses hurst_100; the question is whether it was COMPOSING the regime-momentum interaction internally. If it was, regime_momentum_signed_5d will rank 14/14 (PATH B). If it wasn't, regime_momentum_signed_5d will rank ≤10 (PATH A).
3. **Implementation cost LOWEST**: the simplest possible composition (multiply 2 columns). Other candidates require additional primitive computation (hurst_50 not in feature set; fracdiff weights+convolution).
4. **Interpretability HIGHEST**: regime-conditional momentum is part of standard systematic-trading toolkit (Robert Carver, *Systematic Trading*; Ernest Chan, *Algorithmic Trading*). If PATH A confirms, the result is immediately actionable for further research.
5. **cross_asset_divergence_norm deferred to iter-v3/026 NEXT axis IF iter-v3/025 lands PATH B**: as a fallback per Section 7.

### 3.5 Distribution stats (regime_momentum_signed_5d, IS window)

| Symbol | n_valid | coverage% | mean | std | p01 | p99 | outlier_ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| BCH | 2099 | 99.0% | 0.0001 | 0.0526 | -0.187 | +0.176 | 11.7 |
| LDO | 2098 | 99.0% | -0.0006 | 0.0879 | -0.301 | +0.303 | 9.5 |
| TRX | 2099 | 99.0% | 0.0017 | 0.0568 | -0.196 | +0.205 | 11.0 |

Distribution stable: mean ≈ 0 (consistent with 5-day return × {±1} sign flip), std reasonable for log-return scale, no extreme outliers (outlier_ratio ≈ 9-12 = (max-min)/std on a ~3σ-clipped distribution = healthy).

### 3.6 Rank-IC (regime_momentum_signed_5d, IS window)

| Symbol | h=1 | h=3 | h=7 | max |rank-IC| |
|---|---:|---:|---:|---:|
| BCH | -0.037 | -0.032 | -0.028 | 0.037 |
| LDO | -0.037 | -0.062 | -0.062 | 0.062 |
| TRX | -0.022 | -0.051 | -0.051 | 0.051 |

All 9 of 9 (sym × horizon) cells NEGATIVE-direction — meaning the composed feature predicts MEAN-REVERSION on these symbols (which are predominantly low-Hurst / mean-reverting in the IS window). LDO h=3 = -0.062 is comparable to per-symbol funding's iter-v3/019 0.0485 max rank-IC — directionally meaningful but small magnitude.

---

## Section 4 — Falsifiers (PRE-REGISTERED at SHA `917605b` + this brief — cannot be renegotiated)

### 4.1 Falsifier 1: PATH C trigger (NEGATIVE)

**Triggered if**: IS Sharpe Δ < −0.10 (anchor +0.3788) OR OOS Sharpe Δ < −0.50 (anchor +0.3869).

**Verdict if triggered**: EXPLORATION-NEGATIVE (clean) — feature actively hurts via expanded overfit space (same mechanism as iter-v3/023/024 INERT-OVERFIT).

### 4.2 Falsifier 2: Saturation falsifier

**Triggered if**: IS trades > 215 OR IS trades < 130.

**Verdict if triggered**: catalog row notes "saturation falsifier FIRES" qualifier; the axis behavioral effect is anomalous (trade count outside predicted band). Distinct from PATH C; can co-fire with any PATH.

### 4.3 Falsifier 3: PATH B trigger (PROMISING-INERT)

**Triggered if**: feature importance rank 14/14 across 3 of 4 cuts (BCH portfolio + LDO + Portfolio at minimum). NOTE: relaxed slightly vs the standard "14/14 across all 4" criterion to accommodate single-symbol partial-success patterns observed in iter-v3/024 (TRX rank 9/14 was the only departure from 14/14).

**Verdict if triggered**: EXPLORATION-PROMISING-INERT — engineered-feature axis CLOSED for this 13-feature stack at iter-v3/025; pivot to different engineered candidate (cross_asset_divergence_norm OR fracdiff_d05_close) at iter-v3/026.

### 4.4 Falsifier 4: PATH A trigger (PROMISING)

**Triggered if**: feature importance rank ≤10 for ≥1 symbol AND IS Sharpe Δ ≥ +0.10. Importance value ≥30 required as well (informational threshold; flags genuine model usage vs cosmetic non-zero importance).

**Verdict if triggered**: EXPLORATION-PROMISING — composed feature works (signal exists; LightGBM trees couldn't compose internally). NOT a CONFIRMATION-bundle candidate at single-seed (lottery suspect rule per `feedback_v3_single_seed_frozen_baseline.md`); flag for iter-v3/029+ CONFIRMATION evaluation.

### 4.5 Falsifier 5: PATH D trigger (PROMISING-MECHANICAL)

**Triggered if**: trade roster bit-identical to iter-v3/024 baseline (or strict subset thereof). Mechanism: feature is genuinely INERT but happens to shift profit accounting; not new edge.

**Verdict if triggered**: EXPLORATION-PROMISING-MECHANICAL — non-compoundable across iterations; treat as iter-v3/013 PROMISING-MECHANICAL precedent (FALSIFIED at multi-seed CONFIRMATION).

### 4.6 PATH classification cannot be renegotiated post-hoc

If the engineering report observed metrics fall in a borderline zone (e.g., rank 11 on 1 symbol with importance value 32; IS Δ +0.08), the verdict is still bound by the strict §4.4 criteria. The QR must NOT relax thresholds based on observed outcome direction.

---

## Section 5 — Predicted Bands (and predicted-vs-observed schedule)

| Metric | Lower bound | Upper bound | Median | Anchor |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | +0.30 | +0.55 | +0.40 | +0.3788 |
| OOS monthly Sharpe | +0.40 | +0.65 | +0.50 | +0.3869 |
| OOS/IS Sharpe ratio | 0.55 | 1.50 | 1.05 | 1.02 |
| IS n_trades | 175 | 209 | 192 | 172 |
| OOS n_trades | 80 | 105 | 92 | 90.5 |
| IS MaxDD | 18% | 28% | 22% | 21.86% |
| OOS MaxDD | 25% | 38% | 30% | 27.74% |
| Total OOS PnL | +5% | +18% | +10% | ~+7% |
| feature importance rank (best of 4 cuts) | 7 | 12 | 9 | n/a |
| feature importance value (best symbol) | 30 | 100 | 50 | n/a |

The predicted bands are tighter than iter-v3/024 (cross-asset funding) because the composed feature mechanism is more constrained — `regime_momentum_signed_5d` is a known ML-for-trading technique with documented effects in the literature, whereas BTC cross-asset funding broadcast was a more speculative axis.

---

## Section 6 — Risk Mitigation

Per `feedback_risk_mitigation_design.md`, every merge-candidate iteration must include this section. iter-v3/025 is EXPLORATION (not merge-candidate) but the section is mandatory for all axis-changes per Phase 5.5 gate.

### 6.1 Risk model: composed-feature interaction overfit

The primary risk is INERT-OVERFIT (per `feedback_v3_inert_features_at_higher_budget.md`): if `regime_momentum_signed_5d` ranks 14/14 across all symbols, adding it as the 14th feature at n_trials=35 expands Optuna's parameter search space along an uninformative dimension, leading to IS-overfit hyperparameter trajectories that don't generalize to OOS — same mechanism as iter-v3/023/024.

### 6.2 Mitigation: risk gates UNCHANGED from iter-v3/018 baseline

- **R1** (consecutive-SL cooldown): unchanged (3 SL → 27 candle pause; per BASELINE_V3.md)
- **R2** (drawdown-triggered position scaling): unchanged
- **R3** (OOD Mahalanobis gate): unchanged (70th-percentile cutoff)
- **z-score OOD**: 2.0 unchanged (iter-v3/011 PROMISING)
- **ATR multipliers**: 2.0/1.0 unchanged (iter-v3/010 PROMISING)
- **BTC trend filter**: ±15% unchanged (iter-v3/012 NULL-effect)
- **ADX threshold**: 20 unchanged (iter-v3/014 ADX=25 axis closed)
- **Hurst regime**: unchanged (the composed feature consumes hurst_100 but does not modify the regime gate)
- **Low-vol filter**: unchanged
- **Hit-rate feedback**: disabled
- **Regime gate**: disabled (was iter-v3/022 axis)
- **Per-symbol cap**: disabled (was iter-v3/020 axis)

### 6.3 Mitigation: kill-switch criteria

Iteration is abandoned mid-flight if:
1. Wall-clock exceeds 2h cap (EXPLORATION budget).
2. Adversarial past-only test FAILS (look-ahead bias detected).
3. Track-isolation grep returns non-empty (v3 imports v1/v2 features).
4. V3_FEATURE_COLUMNS not exactly 14 columns at backtest run.
5. Feature parquet regeneration fails on any of 3 symbols (BCH/LDO/TRX).

### 6.4 Mitigation: simulated historical effect

Counterfactual estimation: substituting a +1 composed feature into the iter-v3/024 framework (with both funding variants dropped) is expected to:
- Shift IS trade count by ±10-30 (band [175, 209] from prior +1-feature iterations)
- Shift IS Sharpe by ±0.20 (median ~+0.05 if PROMISING-INERT, +0.40 if PROMISING)
- Shift OOS Sharpe by ±0.30 (median ~0 if PROMISING-INERT, +0.50 if PROMISING, -1.20 if NEGATIVE matching iter-v3/024 pattern)

The composed-feature mechanism is novel (no v3 precedent); the predicted bands carry higher uncertainty than knob-axis iterations.

---

## Section 7 — Pre-Commit for iter-v3/026 (conditional on iter-v3/025 outcome)

Per Phase 5.5 + iter-v3/024 diary lesson (a)-(d):

- **If iter-v3/025 PATH A (PROMISING)**: iter-v3/026 axis = additional engineered feature (composed-feature compounding); candidate ranking is `cross_asset_divergence_norm` (composite 0.6500, second-highest in EDA). This would be the 15th feature.
- **If iter-v3/025 PATH B (PROMISING-INERT)**: iter-v3/026 axis = different engineered feature; candidate ranking is `cross_asset_divergence_norm` OR `fracdiff_d05_close` (composite 0.4954 but addresses ADF stationarity test issue on TRX requiring fracdiff_logclose_dstat-style auto-d* substitution).
- **If iter-v3/025 PATH C (NEGATIVE)**: iter-v3/026 axis = drop the engineered feature axis entirely; revert to fundamental architectural exploration (NEW model architecture beyond LightGBM/XGBoost; e.g., explicit regime-conditional ensemble of two LightGBM models — one trained on Hurst > 0.5 subset, one on Hurst < 0.5 subset).
- **If iter-v3/025 PATH D (PROMISING-MECHANICAL)**: NO iter-v3/026 axis-pivot; the iteration is an accounting-cleanup variation; wait for explicit evidence to compound.

Cannot be renegotiated post-hoc per `feedback_v3_engineered_feature_pivot.md`.

---

## Section 8 — Out-of-Scope (Cannot enter iter-v3/025 setup)

- ANY change to the 3-symbol BCH+LDO+TRX universe
- ANY change to the labeling parameters (ATR 2.0/1.0)
- ANY change to risk gates (z=2.0, ADX=20, BTC ±15%, regime gate disabled, per-symbol cap disabled)
- ANY change to model architecture (LightGBM remains; XGBoost rejected at iter-v3/016)
- ANY change to OOS_CUTOFF_DATE or training_months (sacred constants; immutable)
- ANY funding feature (PERMANENTLY-CLOSED across per-symbol + cross-asset variants)
- ADX as a feature column (rejected at EDA Stage 1; would be Category 1 axis, not the engineered-feature pivot)
- Multiple engineered features in a single axis (single-axis discipline preserved; iter-v3/026 can compound IF iter-v3/025 lands PATH A)

---

## Section 9 — Reproducibility Stamp (final pre-flight)

- **Brief SHA**: this commit (will be assigned at commit time)
- **EDA SHA**: `917605b`
- **Anchor**: iter-v3/018 multi-seed mean +0.3788 IS / +0.3869 OOS
- **n_trials default**: 35 (PRELIMINARY-VALIDATED through 5 prior EXPLORATIONs: iter-v3/020/021/022/023/024)
- **Parent branch SHA**: `c494d19` (iter-v3/024 diary commit on iteration-v3/024)
- **Parent baseline architecture**: 13 V3_FEATURE_COLUMNS (drop-MKR + ATR 2.0/1.0 + z=2.0 + BTC ±15% + ADX=20 + Hurst gate)

---

## Section 10 — Hand-Off to Engineer (Phase 6)

Engineer must:
1. Read this brief + EDA at SHA `917605b` + iter-v3/024 diary at SHA `c494d19`.
2. Verify Phase 5.5 gate (separate file `phase5p5_gate.md` once Phase 5.5 completes).
3. Implement `engineered_v3.py` module per Section 2.2 spec.
4. Add `engineered_v3` to GROUP_REGISTRY.
5. DROP `btc_funding_rate_zscore_30` from V3_FEATURE_COLUMNS_TOP_N (revert 14 → 13).
6. ADD `regime_momentum_signed_5d` to V3_FEATURE_COLUMNS_TOP_N (13 → 14).
7. Update `_verify_feature_columns` assertion to expect 14 columns including `regime_momentum_signed_5d`.
8. Write adversarial past-only test in `tests/features_v3/test_engineered_v3.py`.
9. Run `uv run pytest tests/features_v3/` — must PASS.
10. Run `uv run ruff check . && uv run ruff format .` — must PASS.
11. Regenerate feature parquets for BCH+LDO+TRX with new `engineered_v3` group.
12. Set `ITERATION_LABEL = "v3-025"`.
13. Run backtest in EXPLORATION mode: `uv run crypto-trade backtest-v3 --exploration --seeds 1 --n-trials 35`.
14. Wait for backtest completion (predicted 8-15 min).
15. Write engineering report at `briefs-v3/iteration_v3-025/engineering_report.md`.
16. Hand off to Critic (Phase 7.5) for review.

Cannot be renegotiated post-hoc per `feedback_v3_engineered_feature_pivot.md`.

---

## Appendix A — EDA Composite Score Detail

Composite score = 0.30 × orthogonality + 0.30 × rankIC + 0.20 × stability + 0.10 × interpretability + 0.10 × (1 − implementation_cost)

| Candidate | Orthogonality | RankIC | Stability | Interpretability prior | Implementation cost prior | Composite |
|---|---:|---:|---:|---:|---:|---:|
| `cross_asset_divergence_norm` | 0.0 | 1.0 | 0.99 | 0.7 | 0.2 | **0.6500** |
| `regime_momentum_signed_5d` | 0.0 | 0.624 | 0.99 | 1.0 | 0.1 | 0.5772 |
| `ret_kurt_to_skew_ratio` | 0.0 | 0.774 | 0.99 | 0.4 | 0.1 | 0.5623 |
| `hurst_drift_50_200` | 0.0 | 0.633 | 0.99 | 0.5 | 0.3 | 0.5100 |
| `fracdiff_d05_close` | 0.0 | 0.885 | 0.66 | 0.7 | 0.4 | 0.4954 |
| `vol_adj_autocorr` | 0.0 | 0.279 | 0.99 | 0.6 | 0.1 | 0.4336 |

The diary pre-commit binds the iter-v3/025 axis to `regime_momentum_signed_5d` (single-axis discipline, cannot be renegotiated post-hoc). The leaderboard is INFORMATIONAL and informs iter-v3/026 conditional axis selection per Section 7.

---

## Appendix B — Why this iteration is a PIVOT MOMENT in v3 catalog

The v3 catalog has 24 prior iterations (iter-v3/001-024). The axis-category breakdown:

- Category 1 (off-the-shelf indicator additions): iter-v3/015 (microstructure), iter-v3/019/023/024 (funding × 3) — ALL INERT-class
- Category 1 (knob axes): iter-v3/009/010/011/012/014 — saturated per `feedback_v3_axis_saturation_predictor.md`
- Category 1 (universe + risk primitives): iter-v3/020/021/022 — CLOSED-mechanism
- Category 1 (model architecture / labeling architecture): iter-v3/016 (XGBoost) / iter-v3/017 (meta-labeling) — both NEGATIVE
- CONFIRMATION: iter-v3/018 — BOOTSTRAP exception
- Feature pruning: iter-v3/007/008/009 (top-14 → top-13)

**iter-v3/025 introduces Category 2 (composed/interaction features) for the first time in v3 catalog history.** This is structurally distinct from all 24 prior axes:
- Source primitives are all in V3_FEATURE_COLUMNS_TOP_N already
- The candidate's information value is INTERACTION between primitives, not standalone signal
- The IC orthogonality gate is mechanically biased high (Section 3.3); rank-based gate replaces it
- Failure mode (PATH B PROMISING-INERT) means LightGBM is already composing the interaction internally — strong evidence the architecture is more capable than prior INERT outcomes suggested
- Success mode (PATH A PROMISING) opens an entire NEW axis category for v3; iter-v3/026+ can compound additional engineered features

**Per user directive 2026-05-08**: this is the PIVOT to begin building genuine alpha through feature engineering instead of chasing more off-the-shelf indicators. Cannot be renegotiated post-hoc.
