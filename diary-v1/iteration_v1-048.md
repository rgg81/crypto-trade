# iter-v1/048 — EXPLORATION feature-family — trade_count_zscore_30 (ABORT PRE-LAUNCH)

**Tag**: `v0.v1-048`
**Date**: 2026-06-01
**Iteration type**: EXPLORATION
**Axis family**: `feature-family` (NEW primitive `number_of_trades` — rolling-30bar z-score; first microstructure-class kline-count primitive attempted in v1)
**Cycle slot**: cycle-6 EXPLORATION **3/10**
**Status**: **NEG-CLEAN-PRE-EDA** — pre-launch F5 IC orthogonality gate ABORTED the iteration; no backtest run
**BASELINE_V1.md**: UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`)

**Banner**: F5 IC orthogonality gate ran on the parquet-generated `trade_count_zscore_30` (44 → 45 col stack) over pooled-IS data. **Max |Pearson IC| = 0.9063 vs `vol_volume_rel_20`** — the existing 20-bar rolling-relative volume primitive. The brief's pre-registered ABORT threshold is `|IC| >= 0.60`; the observed value clears that wall by 51% (relative). Two further rank-2/rank-3 |IC| also breach the ABORT wall (`vol_range_spike_24` = 0.7908, `vol_range_spike_72` = 0.7322). **No backtest launched** — the experimental design failed at the orthogonality screen. The "UNUSED primitive" hypothesis (number_of_trades is a kline field outside the volume/return cluster) is **REFUTED**: empirically, Binance kline OHLCV+count fields are tightly coupled by liquidity-cluster physics. The LM Master Phase 4.5 MODAL band — NEGATIVE-no-effect at ~35% prior, with explicit "volume-cluster collinearity" flagged as a residual risk — MATERIALIZED as a pre-EDA abort one slot earlier than Phase 6, saving ≈2h compute. This is the SECOND consecutive cycle-6 NEG-CLEAN-PRE-EDA closeout (after /047 skew_zscore_21).

---

## 1. Decision: NO-MERGE; ABORT pre-launch; feature REVERTED

**Verdict**: **NEG-CLEAN-PRE-EDA** (no backtest run). Cycle-6 EXP-3 closes on the F5 orthogonality wall; cycle-6 EXP-4 (iter-v1/049) MUST pivot to NEW DATA SOURCES (non-kline) — the v1 internal-kline feature space is empirically saturated.

**Falsifier outcome (pre-registered in brief Section 4)**:

| Falsifier | Pre-registered threshold | Observed | Verdict |
|---|---|---:|---|
| F4 — ADF stationarity per symbol | p < 0.05 for all 5 | 0.000 for all 5 | **PASS** |
| F5 — IC orthogonality (Pearson, pooled IS) | max \|IC\| < 0.30 (TIGHTENED for /048) | **0.9063 (vs `vol_volume_rel_20`)** | **FAIL** |
| F5 ABORT trigger | max \|IC\| >= 0.60 | **0.9063** | **ABORT** |

`feature_columns_count` post-revert = **44** (restored from 45). `BASELINE_V1.md` UNCHANGED.

---

## 2. Observed Results (Pre-EDA gate; no backtest)

### 2.1 F5 IC orthogonality table — top-10 |IC| vs `trade_count_zscore_30` (pooled IS)

| Rank | Feature | \|Pearson IC\| | Note |
|---:|---|---:|---|
| 1 | **`vol_volume_rel_20`** | **0.9063** | **VOLUME-CLUSTER ANCHOR (load-bearing failure)** |
| 2 | `vol_range_spike_24` | 0.7908 | ABORT_TRIGGER (volume cluster) |
| 3 | `vol_range_spike_72` | 0.7322 | ABORT_TRIGGER (volume cluster) |
| 4 | `vol_volume_pctchg_5` | 0.6662 | ABORT_TRIGGER (volume cluster) |
| 5 | `interact_ret1_x_ret3` | 0.3181 | WARN |
| 6 | `cal_dow_norm` | 0.2530 | |
| 7 | `trend_plus_di_14` | 0.2300 | |
| 8 | `mr_pct_from_low_20` | 0.1431 | |
| 9 | `vol_natr_14` | 0.1367 | |
| 10 | `vol_bb_bandwidth_20` | 0.1324 | |

Source: `analysis/iteration_v1-048/eda.csv` + `analysis/iteration_v1-048/eda_summary.md`. Computation: pooled across `V1_BASELINE_UNIVERSE = (BTC, ETH, LINK, LTC, DOT)`; IS-only (`open_time < OOS_CUTOFF_MS = 1742774400000`); `pandas.DataFrame.corr(method='pearson')` after `dropna()`.

**Critical pattern**: the **top-4 |IC| values are ALL from the volume cluster**. number_of_trades is not orthogonal to OHLCV-derived volume — it is a near-duplicate of the volume-aggregation surface that Binance kline-stream computes.

### 2.2 F4 ADF stationarity table

| Symbol | ADF p-value | Status |
|---|---:|---|
| BTCUSDT | 0.000000 | PASS |
| ETHUSDT | 0.000000 | PASS |
| LINKUSDT | 0.000000 | PASS |
| LTCUSDT | 0.000000 | PASS |
| DOTUSDT | 0.000000 | PASS |

Stationarity is not the problem (as with /047). The problem is **redundancy with the existing volume cluster**.

### 2.3 Distribution stats — `trade_count_zscore_30` IS-only

| Symbol | N | Mean | Std | Q25 | Median | Q75 | Min | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 5698 | -0.0007 | 1.0357 | -0.7476 | -0.2386 | +0.5158 | -1.9950 | +4.7284 |
| ETHUSDT | 5698 | +0.0152 | 1.0624 | -0.7482 | -0.2213 | +0.5396 | -2.0457 | +4.9251 |
| LINKUSDT | 5649 | +0.0069 | 1.0905 | -0.7657 | -0.2596 | +0.5223 | -2.3699 | +5.0649 |
| LTCUSDT | 5658 | +0.0133 | 1.0862 | -0.7507 | -0.2392 | +0.5383 | -2.5873 | +5.0963 |
| DOTUSDT | 4996 | -0.0031 | 1.0720 | -0.7429 | -0.2669 | +0.4592 | -2.2142 | +4.9689 |

Z-score normalization is well-behaved (mean ≈ 0, std ≈ 1.07 — slight right-skew from liquidation-cluster spikes). The math is correct; the **information content is the same as `vol_volume_rel_20`**.

---

## 3. The IC Failure Explained (LOAD-BEARING)

`trade_count_zscore_30` was constructed as the **standardized regime form** of the `number_of_trades` kline field:

```
tc[t]            = number_of_trades[t]            (raw Binance kline field 8)
tc_mean_30[t]    = mean(tc[t-29 : t+1])
tc_std_30[t]     = std(tc[t-29 : t+1], ddof=1)
trade_count_zscore_30[t] = (tc[t] - tc_mean_30[t]) / tc_std_30[t]
```

`vol_volume_rel_20` (already in the pruned stack, line 134) is constructed as `volume[t] / mean(volume[t-19 : t+1])` — a 20-bar relative-volume ratio. The theoretical case for primitive-orthogonality was:

- `number_of_trades` measures **count of executions** (microstructure).
- `volume` measures **notional traded** (count × average size).
- The two differ when **average trade size shifts**: e.g. a liquidation cascade involves many small forced exits → count spikes harder than notional; a whale block trade is the opposite.

That argument is correct in principle. The empirical Pearson IC of 0.9063 says it does not matter in practice at 8h cadence: at this horizon, count and notional **co-move on the dominant axis of liquidity-cluster physics**. The decomposition trades-count = volume / avg-size has avg-size as a slow-moving auxiliary variable whose 30-bar rolling z-norm is dominated by the volume-side numerator. Three additional concurrent ABORT-triggers (`vol_range_spike_24` 0.79, `vol_range_spike_72` 0.73, `vol_volume_pctchg_5` 0.67) confirm the column lives inside the same liquidity-cluster manifold as the existing volume/range features — there is no separable signal direction at this cadence.

LightGBM at depth 3–5 cannot exploit a sub-axis projection that requires conditioning on a 4th variable (average trade size) when the dominant variable (`vol_volume_rel_20`) is already in the feature set. ADD would have stolen `colsample_bytree` picks from genuinely orthogonal columns — the exact failure mode flagged by `feedback_v3_inert_features_at_higher_budget.md` (INERT features at higher Optuna budget actively HARM OOS).

---

## 4. Revert + Cleanup Performed

- `V1_FEATURE_COLUMNS_PRUNED`: 45 → 44 (removed `trade_count_zscore_30`; restored `assert len(...) == 44`).
- `V1_FEATURE_COLUMNS`: unchanged at 193 (the legacy `BASELINE_FEATURE_COLUMNS` never contained `trade_count_zscore_30`).
- `GROUP_REGISTRY`: 14 → 13 (de-registered `microstructure_v1`).
- `src/crypto_trade/features_v1/microstructure_v1.py`: **kept on disk** as dead code (`compute_trade_count_zscore_30` helper preserved; the module is future-iter-ready for any NON-kline microstructure primitive — e.g. funding-rate momentum, OI-velocity, basis delta).
- `src/crypto_trade/features/__init__.py`: `microstructure_v1` `_register` call removed; replaced with a documented dead-code marker.
- `tests/test_features.py`: `len(list_groups()) == 13` + `len(GROUP_REGISTRY) == 13` retained from /047 (no change needed since /048 also lands at 13).
- `tests/test_iteration_v1_048.py`: rewritten to assert the REVERTED state (trade_count_zscore_30 NOT in pruned, microstructure_v1 NOT in registry, helper still works, parquet test skipped).
- `tests/test_iteration_v1_047.py`: count assertions tightened from `>= 44` / `>= 13` to `== 44` / `== 13` (the steady-state post-/048 revert).
- Parquets regenerated (`uv run crypto-trade features --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT --interval 8h --track v1 --format parquet --workers 4`); each symbol's parquet verified to NOT contain `trade_count_zscore_30` (211 features × 5 symbols).

---

## 5. Lessons

### 5.1 A-priori orthogonality reasoning is insufficient — F5 pre-EDA gate is ESSENTIAL

The /048 brief's primary argument was theoretical primitive-orthogonality: number_of_trades is a kline field NOT used by any existing pruned feature, therefore its z-score must be orthogonal to existing features. The empirical Pearson |IC| = 0.9063 falsifies that argument. **Theoretical decomposition arguments at the algebraic level (count = volume / avg-size) do not survive the empirical rank-correlation test at 8h cadence.** Two consecutive cycle-6 NEG-CLEAN-PRE-EDA closeouts (/047 + /048) confirm the F5 pre-EDA gate is the binding discipline; without it, two iterations × 2h = 4h compute would have been wasted on backtests that ship duplicate signal.

### 5.2 The v1 internal-kline feature space is empirically dense

Two consecutive ABORTs:
- **/047**: `skew_zscore_21` |IC| 0.81 vs `stat_skew_20` (transform-of-existing primitive).
- **/048**: `trade_count_zscore_30` |IC| 0.91 vs `vol_volume_rel_20` (theoretically-untouched kline primitive).

The pattern: **all Binance OHLCV+count fields are tightly coupled by liquidity-cluster physics at 8h cadence**. The 5 fields available in the kline schema (close, high, low, volume, taker_buy, number_of_trades) plus their derivatives (range_spike, taker_buy_ratio, etc.) populate the same liquidity-cluster manifold; their z-score transforms preserve the rank-monotone relationship onto that manifold. Any NEW feature constructed from the kline schema risks |IC| > 0.60 against an existing pruned feature regardless of the underlying primitive.

**Cycle-6 axis priority shift codified**: NEW DATA SOURCES (non-kline) are preferred over kline-derived primitives. Candidate non-kline data sources:
- **Long/short ratio** — Binance Futures `globalLongShortAccountRatio` + `topLongShortAccountRatio` + `topLongShortPositionRatio` (3 distinct cohorts).
- **On-chain** — Glassnode / CryptoQuant primitives (Exchange Whale Ratio, MVRV-Z, NUPL, CDD).
- **Funding/OI NEW transforms** — momentum / delta / acceleration of existing funding/OI (not z-scores; v1 already has `funding_rate_zscore_30/90` and `oi_delta_30_z90`).
- **Cross-asset macro** — DXY, TLT, VIX correlations (8h-resampled).

### 5.3 LM Master Phase 4.5 modal-band materialization is now THREE-IN-A-ROW

- /046: PROMISING-DIVERGENCE 45% MODAL MATERIALIZED.
- /047: NEGATIVE-no-effect 35% MODAL MATERIALIZED (pre-EDA stage).
- /048: NEGATIVE-no-effect MODAL MATERIALIZED (pre-EDA stage).

The LM Master prior distribution remains calibrated and load-bearing. Cycle-6 has now produced a sustained pattern of modal-band materialization — the prior is not optimistic noise; it is a binding forecast that QR should treat as a first-class falsifier in the brief.

### 5.4 Compute saved (the EDA-is-not-a-gate prime directive is preserved)

Same logic as /047 closeout Section 5.3: the brief pre-registered F5 as a HARD pre-launch ABORT trigger; F5 fired BEFORE the experiment could be run honestly; the "no backtest" outcome is NOT a kill-at-EDA in the sense the prime directive forbids — it is a structural reject at a pre-registered methodology guard, equivalent to discovering a duplicate-column bug in a feature before launch. The catalog row tags this as `NEG-CLEAN-PRE-EDA` (structural pre-launch reject), NOT `NULL-AT-EDA` (forbidden).

The 2h compute is reallocated to iter-v1/049.

### 5.5 The "kline-feature space is dense" rule is now a checked feedback rule

Memory write: `feedback_v1_kline_feature_space_dense.md` — codifies that after /047 + /048 the v1 internal-kline feature space is empirically dense; all Binance OHLCV+count primitives at 8h cadence are tightly coupled by liquidity-cluster physics; cycle-6 NEW feature families MUST come from non-kline data sources. This is a HARD convention going forward: any /049+ brief whose new feature is derived from `df[['open','high','low','close','volume','taker_buy','trades']]` alone must declare why the pattern is broken before the F5 gate runs.

---

## 6. Path Forward — Next Iteration Ideas (iter-v1/049)

The cycle-6 axis-rotation window is now `/044 confirmation-multi-seed-aborted`, `/045 bundle-substrate`, `/046 methodology`, `/047 feature-family (ABORTED)`, `/048 feature-family (ABORTED)`. Three consecutive feature-family entries (the last two aborted at the same F5 gate against different anchors) saturate the feature-family axis under the kline-only data class. The next iteration MUST pivot off kline primitives entirely.

**Ranked candidates for iter-v1/049**:

1. **(MODAL) feature-family — NON-KLINE DATA CLASS**. Pre-launch F5 |IC| < 0.30 ideal threshold is HARD pre-design check before brief authoring. Candidates ranked by data-availability and likely orthogonality:
   - **Binance long/short ratio** (`globalLongShortAccountRatio` 8h-resampled). Microstructure positioning signal; primitive-orthogonal to volume cluster (it measures account-side imbalance, not size-side flow). Data class: NEW (Binance Futures public endpoint, no key needed).
   - **On-chain Exchange Whale Ratio** (BTC only, propagate via cross-asset feature for all 5 symbols). Per BIS WP / Glassnode 2024-25 empirical: EWR > 0.85 preceded ≥30% drawdowns. Data class: NEW (Glassnode / CryptoQuant — paid).
   - **Funding-rate ACCELERATION** (`funding_rate_mom_8` = funding[t] - funding[t-8], **NOT z-score**). Uses existing funding data but the primitive is funding-delta rather than z-score. Should F5-test orthogonal to `funding_rate_zscore_30/90` (they measure level deviation; momentum measures slope).
   - **OI-velocity** (`oi_velocity_5` = (OI[t] - OI[t-5]) / OI[t-5], raw). The existing `oi_delta_30_z90` is z-scored 30-bar; raw 5-bar velocity is a different timescale primitive and likely F5-orthogonal.

2. **risk-primitive — vol-targeted SL ceiling** (carry-over from /047 Path Forward). A scale-invariant ATR ceiling on `atr_sl_multiplier` per-cohort, anchored at the IS Sharpe-optimum per-cohort. Orthogonal to all feature changes; supersedes the per-cohort labeling work at /041.

3. **labeling — fractional-bar triple-barrier** (carry-over from /047 Path Forward). Replace integer `atr_tp/atr_sl` with continuous (vol-adaptive) barriers per López de Prado AFML Ch. 3. Higher-variance hypothesis; less obvious basin-lottery exposure.

**Recommended LOCKED axis for /049**: feature-family with NON-KLINE DATA CLASS candidate. Priority order: Binance long/short ratio (free, immediate) > funding-rate acceleration (existing data, new transform) > OI-velocity (existing data, new transform) > on-chain Exchange Whale Ratio (paid, requires data-source integration). The pre-launch F5 |IC| < 0.30 ideal threshold is HARD pre-design check.

**Multi-seed validation** of the /045 ALT_1 substrate remains DEFERRED. No new bundle-substrate work until a NEW edge is found via the non-kline feature-family axis OR until cycle-6 cadence reaches 10/10 EXPLORATIONs and a multi-seed CONFIRMATION naturally fires.

---

## 7. Path Forward (from Critic Phase 6.0 pre-flight — verbatim)

The Critic Phase 6.0 pre-flight (commit `12a0097`-class diff for /048) PASSED, so there was no Phase 7.5 Critic review. The pre-launch ABORT was triggered by the QR's own F5 check, not a Critic verdict. No Critic Path Forward exists for this iteration; this Section 7 is reserved per the v1 closeout template.

---

## Appendix A — Artifacts

- Brief: `briefs-v1/iteration_v1-048/research_brief.md`
- LM Master advisor: `briefs-v1/iteration_v1-048/lgbm_advisor.md`
- Phase 5.5 gate: `briefs-v1/iteration_v1-048/_pre_brief_outline.md` (gate predates `phase5p5_gate.md` rename)
- Pre-EDA: `analysis/iteration_v1-048/eda.py` + `analysis/iteration_v1-048/eda.csv` + `analysis/iteration_v1-048/eda_summary.md`
- Reverted source: `src/crypto_trade/features_v1/__init__.py` + `src/crypto_trade/features/__init__.py` (de-register `microstructure_v1`)
- Tests: `tests/test_features.py` (counts at 13) + `tests/test_iteration_v1_048.py` (asserts REVERTED state)
- Dead-code module preserved: `src/crypto_trade/features_v1/microstructure_v1.py`
- Memory: `feedback_v1_kline_feature_space_dense.md`
- Catalog row: `briefs-v1/exploration_catalog.md`
- Tag: `v0.v1-048` (NEG-CLEAN-PRE-EDA artifact)
