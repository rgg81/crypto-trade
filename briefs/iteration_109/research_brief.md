# Iteration 109 Research Brief

**Type**: EXPLOITATION
**Date**: 2026-04-01
**Theme**: DOGE-only model (remove SHIB drag)

## Section 0: Data Split

- OOS cutoff: `2025-03-24` (fixed, never changes)
- IS period: all data before 2025-03-24
- OOS period: all data from 2025-03-24 onward
- Walk-forward runs on ALL data; reports split at cutoff

## Rationale

Iter 108 showed clear per-symbol divergence:
- **DOGE**: WR 34.5%, net PnL +20.3% (profitable, above break-even)
- **SHIB**: WR 42.4%, net PnL -9.1% (losing despite higher WR — dynamic ATR SL losses dominate)

Removing SHIB eliminates the drag. Single variable change from iter 108.

## What Changes

| Parameter | Iter 108 | Iter 109 |
|-----------|---------|---------|
| Symbols | DOGE + SHIB | **DOGE only** |
| Features | 42 curated | 42 curated (same) |
| ATR labeling | Yes (2.9x/1.45x) | Yes (same) |
| CV gap | 44 (2 symbols) | **22 (1 symbol)** |
| Training samples | ~4,400 | **~2,200** |
| Feature ratio | 4400/42=104.8 | **2200/42=52.4** |

The ratio drops to 52.4 — still above the minimum 50. The CV gap halves to 22, reducing data waste.

## Research Analysis (Categories B, E)

### Category B: Symbol Universe
SHIB failed Gate 3 (stand-alone profitability) with negative PnL despite 42.4% WR. The cause: during high-vol periods, dynamic ATR barriers create very wide SL (-7.5% to -10.5% losses) that overwhelm TP gains. SHIB's volatility spikes are more extreme than DOGE's.

### Category E: Trade Pattern (from iter 108)
- DOGE IS: 55 trades, 19 wins (34.5%), avg winner +13.6%, avg loser -5.2% → effective RR 2.6:1
- SHIB IS: 59 trades, 25 wins (42.4%), avg winner +8.9%, avg loser -8.0% → effective RR 1.1:1
- SHIB's dynamic barriers create near-symmetric RR, destroying the 2:1 edge

## Success Criteria

This is a standalone meme model. No baseline comparison:
1. IS Sharpe > 0.0
2. IS WR > 33.3%
3. At least 50 IS trades
4. Pass yearly checkpoints (no early stop)
5. OOS Sharpe > 0.0 (if reached)

## Implementation Spec

Same as iter 108 but `SYMBOLS = ("DOGEUSDT",)`. All other parameters unchanged.
