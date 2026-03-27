# Iteration 049 — EXPLORATION (parallel pairs: BTC+ETH + SOL+DOGE)

## NO-MERGE: SOL+DOGE added zero value. OOS identical to baseline (Sharpe +1.16) because only BTC+ETH generated OOS trades.

**OOS cutoff**: 2025-03-24

## Results

| Period | Sharpe | WR | PF | MaxDD | Trades | PnL |
|--------|--------|-----|------|-------|--------|------|
| IS | +1.37 | 40.9% | 1.20 | 64.3% | 959 | +445% |
| OOS | +1.16 | 44.9% | 1.27 | 75.9% | 136 | +79% |

**Per-symbol IS**: ETH 317 trades (+306%, 68.7%), BTC 257 (+82%, 18.4%), SOL 221 (+58%, 13.0%), DOGE 164 (-0.3%, -0.1%)
**Per-symbol OOS**: BTC 50 trades (+55%, 70.5%), ETH 86 (+23%, 29.5%) — SOL and DOGE generated zero OOS trades

## What Happened

Ran BTC+ETH and SOL+DOGE as independent parallel models (separate LightGBM per pair), combined trades for reporting. SOL contributed marginally in IS (+58%) but produced no OOS trades. DOGE was break-even in IS and also absent in OOS. The model learned these symbols have no predictable 8%/4% moves at 8h resolution.

The 8%/4% barrier + 7-day timeout configuration is BTC+ETH specific. Mid-cap alts (SOL, DOGE) have different volatility profiles and the model correctly abstained from trading them OOS.

## Decision: NO-MERGE

OOS Sharpe identical to baseline (+1.16). No improvement — SOL+DOGE added noise in IS and nothing in OOS.

## Exploration/Exploitation Tracker

Last 10: [..., X, E] (E=explore, X=exploit)
Type: EXPLORATION (new symbol pairs, parallel model architecture)

## Next Iteration Ideas

- Try BNB+LINK, AVAX+DOT as independent pairs (different volatility tier)
- Balanced class weights (from iter 048 insight)
- 14-day timeout to capture timeout trades that eventually hit TP
