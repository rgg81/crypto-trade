# Engineering Report — iter-v3/041

## Status: READY-FOR-CRITIC

NEGATIVE — universal feature pruning (drop regime_momentum + sym_vs_btc_ret_7d + ret_skew_50) destroyed BCH (-26 swing).

## Headline

| Metric | Value | vs iter-v3/040 anchor (+0.79/+1.77) |
|--------|-------|--------------------------------------|
| IS Sharpe | +0.0099 | Δ -0.78 |
| OOS Sharpe | +1.0041 | Δ -0.76 |
| BCH OOS | -15.33 / 42 / 35.7% | -26 swing from +10.75 |

## Critical Lesson — IMPORTANCE Aggregation Misleads

iter-v3/028 multi-seed PORTFOLIO importance ranked regime_momentum_signed_5d at 14/14. But that's a SUM across 4 symbols. Per-symbol importance:
- BCH (iter-v3/035 single-seed): regime_momentum at importance 2 (rank 14 within BCH)
- LDO: rank 13 within LDO
- TRX: rank 11 within TRX
- ALGO: rank 14 within ALGO

So at the per-symbol level regime_momentum is rank 11-14 but it's load-bearing for BCH (BCH used it indirectly via complementary fit).

Removing it from V3_FEATURE_COLUMNS_TOP_N → BCH model can't use it → BCH model finds different (worse) IS-fit configurations → BCH OOS collapses.

**Pure importance-based pruning is misleading when features have low aggregate but per-symbol load-bearing value.**

## Verdict: EXPLORATION-NEGATIVE

PATH C fires (IS Δ -0.78 ≪ -0.10).

## Recommendations

iter-v3/042: REVERT pruning (restore V3_FEATURE_COLUMNS_TOP_N to 14) + try a different IS-lift axis.

Candidates:
1. Universal ATR multiplier change (e.g., (1.5, 0.75) instead of (2.0, 1.0)) — labeling axis  
2. NEW universal engineered feature designed to filter bad regimes
3. NEW labeling architecture (fixed-horizon return labels)

Critic prior: option 1 (universal tighter ATR). Tests labeling sensitivity without breaking per-symbol fit. Lower risk than new feature additions.

Status: READY-FOR-CRITIC.
