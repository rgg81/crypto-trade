# Engineering Report — iter-v3/043

## Status: READY-FOR-CRITIC

DISASTROUS NEGATIVE — Kaufman efficiency_ratio_50 broke ALL 4 symbols (IS -0.84 / OOS -0.90).

## Headline

| Metric | Value | vs iter-v3/040 anchor (+0.79/+1.77) |
|--------|-------|--------------------------------------|
| IS Sharpe | -0.8445 | Δ -1.64 (worst) |
| OOS Sharpe | -0.8990 | Δ -2.66 (first NEGATIVE OOS in cycle 3!) |

## Per-Symbol — ALL 4 BROKEN

| Symbol | weighted_pnl | Trades | WR | vs anchor |
|--------|--------------|--------|-----|-----------|
| TRX | +5.61 | 43 | 39.5% | -23 swing |
| BCH | -2.40 | 37 | 35.1% | -13 swing |
| LDO | -12.19 | 9 | 22.2% | -10 swing |
| **ALGO** | **-40.68** | 23 | **21.7%** | **-61 swing (catastrophic)** |

## Mechanism

Kaufman ER importance 465 (rank 14/15, near-top). The model used it heavily, but somehow this caused all symbols to overfit to false regime signals. Maybe ER's [0,1] range causes the model to over-weight high-trend periods that don't generalize OOS.

## Verdict: EXPLORATION-NEGATIVE (worst in cycle 3)

PATH C fires on both IS and OOS axes.

## Cycle 3 Pattern

- iter-v3/041 pruning: NEGATIVE (BCH -26)
- iter-v3/042 universal ATR: NEGATIVE (per-symbol divergence)
- iter-v3/043 Kaufman ER: NEGATIVE (all symbols broken)

3 NEGATIVE iterations in a row. iter-v3/028 baseline appears at a local maximum that's resistant to small changes.

## Recommendations

iter-v3/044: REVERT iter-v3/043 (drop efficiency_ratio_50) + XGBoost retest. iter-v3/016 NEGATIVE was at 3-sym/13-feature baseline; the 4-sym/14-feature stack with regime_momentum may produce different XGBoost results.

Status: READY-FOR-CRITIC.
