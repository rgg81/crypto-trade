# Iteration 023 Diary - 2026-03-26
## Merge Decision: NO-MERGE
IS -0.71, OOS -0.69. Both negative.

## Training Window Sweep Summary (BTC+ETH, threshold 0.85)
| Window | IS Sharpe | OOS Sharpe | 
|--------|----------|-----------|
| 12mo   | -0.96    | **+1.33** |
| 18mo   | -0.75    | -0.29     |
| 20mo   | -0.71    | -0.69     |
| 24mo   | **+0.37**| -0.23     |

No single window makes both positive. IS and OOS are inversely correlated with window length.

## Key Insight
The IS/OOS tradeoff is fundamental — the market dynamics pre-2025 (IS) differ from post-2025 (OOS). A short window adapts to recent dynamics (good OOS) but doesn't accumulate enough history for stable IS. A long window has enough IS data but overfits to older patterns.

## To get both positive, we need a different approach entirely — not just window tuning.
