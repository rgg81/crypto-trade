# iter-v2/068 Diary

**Date**: 2026-04-23
**Type**: EXPLOITATION (parameter tweak)
**Parent baseline**: iter-v2/059-clean
**Decision**: **NO-MERGE** — OOS monthly −13%, concentration WORSE (56%)

## Summary

Tightened z-score OOD threshold 2.5 → 2.4. Hypothesis: smaller step than
the failed 2.25 (iter-v2/060) might continue the iter-050→059 improvement
curve (3.0→2.5 helped +8%).

Result: NOT monotonic. 2.5 is the local optimum; 2.4 is on the wrong side.
IS slightly better but OOS monthly dropped 13% and NEAR concentration
INCREASED to 56.10% (from 44.44%). Tighter filter preferentially killed
non-NEAR signals.

## The broader pattern (iter-v2/063-068)

6 consecutive NO-MERGE iterations focusing on concentration / parameter
tuning. All degrade OOS or leave concentration unfixed:

| Iter | Approach | OOS mo | NEAR% |
|---|---|---|---|
| 059-clean | baseline | +1.66 | 44.44% |
| 063 | +AAVE 5th sym | +1.43 | 44.44% |
| 064 | NEAR 0.70× cap | +1.43 | 35.89% |
| 065 | cap sweep (0.80 best) | +1.51 proj | 39.0% |
| 066 | IS-only re-screen | +0.56 | XRP 78% |
| 067 | drawdown brake | +0.91 | XRP 45% |
| **068** | z-score 2.4 | **+1.45** | **56.10%** (worse) |

**All tunes degrade OOS Sharpe. Baseline is at local optimum for this
architecture. Parameter-tuning phase is exhausted.**

## QR Phase 1 EDA (real feature work, finally)

During the iter-v2/068 backtest I ran proper Category A feature analysis
(`qr_phase1_feature_eda.py`). **Findings:**

### Redundancy
40 features → 8 pairs with |rho|>0.85, including 4 near-identical OHLC
volatility estimators:
- `range_realized_vol_50` == `parkinson_vol_50` (rho=**1.000**)
- `parkinson_vol_20` ≈ `garman_klass_vol_20` ≈ `rogers_satchell_vol_20`
  (all rho>0.99)

4 clones spending model capacity on nothing.

### Non-stationarity
8 features drift >0.3σ across IS halves. Worst:
- `btc_vol_14d` drift 0.97σ (BTC vol has regime-shifted down over IS)
- All rolling-vol LEVELS (not ranked)

### Predictive power
Top univariate predictor: `fracdiff_logclose_d04` (Spearman rho = −0.073).
Bottom 10 have near-zero rho — candidates for replacement.

## Next Iteration Ideas — iter-v2/069

### Primary: BOLD feature iteration (Category A + E + G + I coverage)

**Prune**:
- `parkinson_vol_50` (duplicate of `range_realized_vol_50`)
- `garman_klass_vol_20` (duplicate of `parkinson_vol_20`)
- `rogers_satchell_vol_20` (duplicate)
- `close_pos_in_range_50` (duplicate of `vwap_dev_50`)
- `close_pos_in_range_20` (duplicate of `vwap_dev_20`)
- `atr_pct_rank_1000` (near-duplicate of `atr_pct_rank_500`)

Net: 40 → 34 features.

**Add (BOLD — new families)**:
- `rsi_divergence_14` — price-making-new-high but RSI-making-lower-high
  (or symmetric). Detects momentum exhaustion, a pattern the current
  feature set lacks.
- `liquidity_impact_20` — `abs(close - open) × volume / (high - low + eps)`:
  measures trade-driven moves vs indecision. Volume-weighted regime
  feature, distinct from existing `volume_cv_50`.
- `gap_open_prev_close_5` — rolling 5-bar avg of `(open − prior close)
  / prior close`. Overnight-gap proxy. Relevant for futures that
  respect daily boundaries even on 8h.
- `hurst_diff_100_200` — diff between two horizon Hursts. Detects
  regime CHANGES (not just regime state).

Net add: 4 features. Total: 34 + 4 = 38 (slightly below 40 baseline).

All new features scale-invariant or normalized. All stationary by
construction.

**iter-v2/069 plan**:
1. Implement 4 new feature groups in `features_v2/`
2. Prune 6 from V2_FEATURE_COLUMNS, append 4 new (preserve column
   order discipline)
3. Regenerate v2 features for 4 baseline symbols + BTC
4. Full baseline run (~2.5h)
5. Compare: did the feature refresh improve OOS?

This is a BOLD iteration (new feature families, new code, new hypothesis).
Covers QR Categories A (pruning analysis), E (via 2024-11 trade-pattern
driven feature selection), G (stationarity of new features), I (risk
primitives unchanged). 4+ categories — satisfies the post-NO-MERGE
minimum.

### Fallback: pure-prune iteration (if BOLD implementation runs long)

If implementing new feature modules stalls, run pure-prune iter-v2/069
(drop 6, keep 34). Small change, low risk, informative baseline for
iter-v2/070+ feature adds.
