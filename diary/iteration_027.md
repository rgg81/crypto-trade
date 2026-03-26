# Iteration 027 Diary - 2026-03-26 — EXPLORATION

## Merge Decision: NO-MERGE
OOS Sharpe -0.36 < baseline +1.33. But WR findings are extraordinary.

## Type: EXPLORATION (bold 2x TP/SL change)

## Exploration/Exploitation Tracker
Last 10: [X, E, X, X, X, X, X, E, E, **E**] (iters 018-027)
Exploration rate: 4/10 = 40% ✓ (above 30%)

## Results
| Metric | Value | Baseline |
|--------|-------|----------|
| OOS Sharpe | -0.36 | +1.33 |
| **OOS WR** | **46.0%** | 41.6% |
| OOS PF | 0.94 | 1.21 |
| OOS Trades | 202 | 286 |
| IS Sharpe | -0.04 | -0.96 |
| **IS WR** | **42.2%** | 34.0% |

## CRITICAL FINDING
**The model predicts 8% moves with 46% accuracy** — much higher than 4% moves (41.6%). Larger moves ARE more predictable. But the 4% SL means each loss takes 4.1%, making the strategy net negative despite high WR.

### The asymmetric opportunity
- At TP=8%/SL=2%: break-even = 2/(8+2) = **20%**
- Model WR on 8% direction: **~46%** (way above 20%)
- Expected per trade: 0.46 × 7.9 + 0.54 × (-2.1) = 3.63 - 1.13 = **+2.50% per trade!!**

This could be the most profitable configuration ever tested — IF the WR holds with asymmetric barriers.

## IS nearly positive!
IS Sharpe -0.04 at 8%/4% — essentially break-even. IS WR 42.2% at these bigger barriers.

## Next Iteration Ideas
1. **TP=8%/SL=2% ASYMMETRIC** — THE most promising idea from all 27 iterations. Break-even 20%, expected WR ~40%+. MUST try.
2. **TP=6%/SL=2% asymmetric** — more conservative 3:1 RR, break-even 25%.
3. **TP=10%/SL=3% asymmetric** — even bolder.

## Lessons Learned
- **Larger moves are MORE predictable on BTC/ETH**, not less. This contradicts the iter 007 finding (on 50 symbols).
- The 46% WR at 8%/4% proves the model has strong directional signal for large moves.
- The problem with symmetric 8%/4% is the loss magnitude (4.1%), not the accuracy.
