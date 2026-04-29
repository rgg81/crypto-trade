# Iteration v2/027 Diary

**Date**: 2026-04-15
**Type**: EXPLORATION (BTC features + TRX replacing NEAR)
**Parent baseline**: iter-v2/026
**Decision**: **NO-MERGE** — combination worse than either standalone

## Results

**10-seed mean**:
| Metric | iter-026 (BTC features + NEAR) | iter-027 (BTC features + TRX) |
|---|---|---|
| IS monthly Sharpe | +0.5606 | +0.5118 (worse) |
| OOS monthly Sharpe | +0.6904 | +0.6116 (worse) |
| Profitable seeds | 9/10 | **7/10** (worst yet) |
| Balance ratio | 1.23x | 1.19x |

**Three seeds went negative on OOS**: 456 (−0.06), 1001 (−0.05), 5678 (−0.58).

## Why the combination hurt

Theory: **TRX has low BTC correlation**, so adding BTC features to
TRX's training distribution adds noise rather than signal.

- TRX is a "stablecoin-ish" payment network (Tron)
- Its price movements are relatively decoupled from BTC
- BTC features (3d/7d/14d returns, vol) have low predictive power
  for TRX direction
- The model over-weights irrelevant BTC context at the expense of
  TRX-specific patterns
- Result: more seeds produce bad trade distributions

The BTC features worked in iter-026 with NEAR because NEAR IS
BTC-correlated. BTC regime awareness translated to NEAR direction
decisions. With TRX, that translation fails.

## Key insight

**BTC features are not universally useful**. They help symbols that
correlate with BTC and hurt symbols that don't.

For a diverse basket (DOGE meme, SOL L1, XRP payment, TRX payment,
NEAR L1), some symbols benefit from BTC context and some don't.
Per-symbol feature engineering might help but is complex.

## Comparison summary: iter-021-027

| Iter | Config | Mean IS | Mean OOS | Prof | Notes |
|---|---|---|---|---|---|
| 019 baseline | 4 sym + NEAR | ~0.35 | ~1.10 | 10/10 | Unbalanced high OOS |
| 021 | 3 sym + 5-seed ensemble | +0.36 | +1.75 | ? | Too conservative |
| 022 | LTC replace NEAR | — | — | — | LTC worse than NEAR |
| 023 | TRX replace NEAR | +0.61 | +0.70 | 10/10 | Best balance |
| 024 | 5 sym + TRX + NEAR | +0.64 | **+0.97** | 9/10 | Closest to OOS 1.0 |
| 025 | 3 sym drop NEAR | +0.50 | +0.59 | 9/10 | Balance, low |
| 026 | +BTC features + NEAR | +0.56 | +0.69 | 9/10 | Features help 12-17% |
| **027** | **BTC features + TRX** | **+0.51** | **+0.61** | **7/10** | **Combination hurt** |

**No configuration reaches 10-seed mean >= 1.0 on both IS and OOS**.

The bottleneck is **seed variance** — primary seed 42 often hits
target-level metrics, but 2-3 seeds per iteration produce weak or
negative results that drag the mean.

## Strategic options

1. **Increase Optuna trials** (10 → 25): more hyperparameter search
   depth might reduce seed variance
2. **Longer training window** (24 → 36 months): more data per fold
3. **Accept iter-026 as best balanced** and merge it
4. **Accept iter-019 as final** (highest primary OOS) and stop

## Next iteration (iter-v2/028)

Try **BTC features (iter-026) + 25 Optuna trials** (iter-007's
untested combination with gates). This is a pure hyperparameter
depth increase on the current iter-026 baseline. 2.5x slower
training but should produce more robust per-seed hyperparameters.

Prediction: mean improvement of 10-20% on both IS and OOS if the
variance reduction hypothesis is correct. Might just push above
1.0 on OOS mean.

## MERGE / NO-MERGE

**NO-MERGE**. Combined worse than either standalone. Revert to
iter-026 baseline (BTC features + NEAR) for iter-028.
