# Iteration 011 Diary - 2026-03-26

## Merge Decision: NO-MERGE

OOS Sharpe dropped +0.43→-0.84. WR dropped 38.6%→34.8%. SOL/XRP/DOGE diluted the BTC/ETH signal.

## Hypothesis
Expand from 2 (BTC+ETH) to 5 symbols (add SOL, XRP, DOGE) for more trades.

## Results: Out-of-Sample
| Metric | Value | Baseline |
|--------|-------|----------|
| Sharpe | -0.84 | +0.43 |
| WR | 34.8% | 38.6% |
| PF | 0.95 | 1.05 |
| Trades | 1,464 | 487 |
| MaxDD | 179% | 49.6% |

## Gap Quantification
WR 34.8%, break-even 33.3%, surplus +1.5pp. But PF<1 because timeout losses drag total PnL negative. Not enough margin.

## What Failed
- SOL IS WR 29.5%, DOGE 31.0% — both below break-even. Adding them introduced losing trades.
- XRP IS WR 33.6% was borderline, not enough to help.
- The pooled model trained on 5 symbols can't learn BTC/ETH-specific patterns as well.

## Next Iteration Ideas
1. **BTC-only model**: BTC alone had 50.6% WR. Remove ETH, focus purely on BTC.
2. **Per-symbol models**: Train separate models for BTC and ETH. Each model learns asset-specific patterns.
3. **Add calendar features**: Hour-of-day (0/8/16 UTC) showed 2.6pp spread in IS.

## Lessons Learned
- The 2-symbol sweet spot (BTC+ETH) cannot be easily expanded. SOL/XRP/DOGE add noise.
- BTC+ETH share enough structure for a pooled model. BTC+ETH+alts do not.
