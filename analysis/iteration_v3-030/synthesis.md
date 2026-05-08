# iter-v3/030 LDO 7-feature subset — Synthesis

## Source

iter-v3/028 multi-seed (2 outer × 5 inner = 10 LightGBM models per cell)
``reports-v3/iteration_v3-028/in_sample/model_importance_last_month_LDOUSDT.csv``.

This is the canonical formal BASELINE feature importance — the file iter-v3/028
CONFIRMATION-MERGE updated BASELINE_V3.md with. NOT iter-v3/029 single-seed
(which is noisy; the user directive 2026-05-08 explicitly requested using the
multi-seed-validated read-out for LDO's tighter feature subset).

## LDO top-7 (the iter-v3/030 LDO model's feature set)

| rank | feature | iter-v3/028 importance |
|---:|---|---:|
| 1 | ret_skew_200 | 264.4 |
| 2 | ret_kurt_50 | 245.0 |
| 3 | ret_kurt_200 | 238.8 |
| 4 | vwap_dev_20 | 238.2 |
| 5 | hurst_diff_100_50 | 236.8 |
| 6 | btc_ret_14d | 231.6 |
| 7 | range_realized_vol_50 | 224.6 |


LDO bottom-7 (REMOVED from LDO subset; KEPT for BCH/TRX/ALGO unchanged):

| rank | feature | iter-v3/028 importance |
|---:|---|---:|
| 8 | ret_skew_50 | 210.8 |
| 9 | ema_spread_atr_20 | 200.0 |
| 10 | max_dd_window_50 | 181.2 |
| 11 | sym_vs_btc_ret_7d | 177.6 |
| 12 | ret_autocorr_lag1_50 | 175.6 |
| 13 | regime_momentum_signed_5d | 171.4 |
| 14 | hurst_100 | 162.8 |


## Cross-symbol top-7 overlap

| pair | jaccard | shared (count) |
|---|---:|---:|
| BCH-LDO | 0.5556 | 5 |
| BCH-TRX | 0.5556 | 5 |
| LDO-TRX | 0.4 | 4 |


3-way SHARED top-7 (in BCH AND LDO AND TRX simultaneously): **4 features**

```
range_realized_vol_50, ret_kurt_50, ret_skew_200, vwap_dev_20
```

(matches iter-v3/029 brief Section 2.1 finding of 4 SHARED-top features —
load-bearing for the per-symbol-signature methodology)

## regime_momentum_signed_5d ranks per symbol

| Symbol | rank / 14 | Status in iter-v3/030 |
|---|---:|---|
| BCH | 11 | KEPT (still in 14-feature set) |
| LDO | 13 | DROPPED from LDO subset (rank below top-7) |
| TRX | 11 | KEPT (still in 14-feature set) |

## Key findings

1. **LDO top-7** (canonical, multi-seed iter-v3/028): ret_skew_200, ret_kurt_50, ret_kurt_200, vwap_dev_20, hurst_diff_100_50, btc_ret_14d, range_realized_vol_50.
2. **LDO bottom-7** (DROPPED only from LDO subset): ema_spread_atr_20, hurst_100, max_dd_window_50, regime_momentum_signed_5d, ret_autocorr_lag1_50, ret_skew_50, sym_vs_btc_ret_7d.
3. **regime_momentum_signed_5d** is rank 13/14 on LDO. It is NOT in LDO's top-7 (rank below threshold). The brief MUST justify dropping the multi-seed-validated edge feature from LDO's subset.
4. **BCH and TRX unchanged**: both keep all 14 features (V3_FEATURE_COLUMNS unchanged for them).
5. **ALGO unchanged**: ALGO is the iter-v3/029 NEW symbol; falls back to V3_FEATURE_COLUMNS = 14 features (no per-symbol override).
6. **Per-symbol-feature-signature methodology**: the iter-v3/030 architecture extends iter-v3/029's per-symbol-feature-importance read-out from EDA-only into per-symbol-feature-set discipline. The first iteration where individual model heads use DIFFERENT feature subsets.

## Hypothesis (Phase 5 brief Section 1)

LDO trained on 14 features (8 below LDO's importance threshold) overfits noise
on its 31 IS-month sample. Tighter LDO-specific 7-feature subset should:

(a) Reduce LDO model's overfit to noise.
(b) Lift LDO IS+OOS Sharpe contribution from -22.05% (multi-seed iter-v3/028)
    or -3.07% (single-seed iter-v3/029) to ≥ 0.
(c) Maintain BCH+TRX+ALGO performance unchanged (their feature subsets are
    bit-identical to iter-v3/029 = 14-feature stack).

The mechanism is dimensionality reduction: in 31 IS months × 1 trade per
~3 candles, LightGBM's effective sample size for fitting LDO's signal is
small. 14 features → 7 features halves the search space, raising signal
density per feature.

## Caveats / falsifiers

- **Falsifier 1 — LDO bit-identical decisions despite subset change**: if
  LDO trade-roster is bit-identical to iter-v3/029 LDO, the 7-feature subset
  did not propagate to model output. PROMISING-MECHANICAL or NULL-RESULT.
- **Falsifier 2 — BCH/TRX/ALGO regress**: if any of the 3 unchanged-subset
  models has materially different IS or OOS PnL vs iter-v3/029, the
  per-symbol architecture introduced an unintended issue (training-loop
  side-effect, feature-column-pinning bug, or random-state perturbation).
  PATH C — REVERT.
- **Falsifier 3 — LDO drag worsens**: if LDO OOS PnL falls below -10% (worse
  than iter-v3/029's -3.07%), the dimensionality-reduction hypothesis is
  FALSIFIED. PATH B.
