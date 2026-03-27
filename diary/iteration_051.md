# Iteration 051 — EXPLOITATION (14-day timeout)

## NO-MERGE (EARLY STOP): OOS Sharpe -0.65. 14-day timeout backfired — ETH WR collapsed to 28.8% OOS.

**OOS cutoff**: 2025-03-24

## Results

| Period | Sharpe | WR | PF | MaxDD | Trades | PnL |
|--------|--------|-----|------|-------|--------|------|
| IS | +1.51 | 42.1% | 1.39 | 54.5% | 413 | +370% |
| OOS | -0.65 | 32.4% | 0.88 | 82.7% | 102 | -32% |

**Per-symbol IS**: ETH 241 trades (+212%, 57.4%), BTC 172 (+158%, 42.6%) — both strong
**Per-symbol OOS**: BTC 36 trades, 38.9% WR (+8%, -24.6%), ETH 66 trades, 28.8% WR (-39%, 124.6%) — ETH collapsed

## What Happened

Hypothesis: 17% of 7-day timeout trades have 69.6% WR (from iter 047 analysis). Extending timeout to 14 days should capture these. Reality: the opposite happened.

- IS looks great (Sharpe +1.51, PF 1.39) — better than baseline IS
- OOS collapses: ETH WR drops from ~50% (baseline) to 28.8%, well below break-even (33.3%)
- 14-day timeout allows price to move further against positions, increasing loss magnitude
- Fewer trades (413 IS vs 574 baseline, 102 OOS vs 136 baseline) — model becomes more cautious but less accurate

The timeout extension changed the labeling distribution: with 14 days, more trades hit TP or SL (fewer timeouts), but the model can't predict 14-day outcomes as well as 7-day ones.

## Decision: NO-MERGE (EARLY STOP)

OOS Sharpe negative. 7-day timeout is optimal for this strategy.

## Exploration/Exploitation Tracker

Last 10: [..., X, E, E, X] (E=explore, X=exploit)
Type: EXPLOITATION (timeout parameter change within existing architecture)

## Next Iteration Ideas

- 7-day timeout is confirmed optimal — don't extend further
- Test independent pairs (BNB+LINK, AVAX+DOT) at baseline config
- Seed-validate iter 050's balanced weights result
