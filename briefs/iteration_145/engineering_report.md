# Iteration 145 Engineering Report

**Role**: QE (analytical)
**Methodology**: Apply IS-tuned vol-targeting to iter 138 trades, generate new reports.

## IS Parameter Tuning

Tested 24 configs on iter 138 IS trades only:

| target_vol | lookback | IS Sharpe (custom) |
|-----------|----------|---------------------|
| **1.5** | **14** | **+2.21** (best) |
| 1.5 | 21 | +2.05 |
| 2.0 | 14 | +2.17 |
| 2.5 | 14 | +2.12 |
| 3.0 | 14 | +2.07 |
| ... | ... | ... |
| baseline (no sizing) | — | +1.88 |

**IS-best**: target_vol=1.5, lookback=14 days. IS Sharpe delta: +0.34 (+18%).

## Walk-Forward OOS Results

Applied IS-best config (target_vol=1.5, lookback=14) to OOS trades without further tuning:

| Metric | Baseline (iter 138) | Vol-Targeted (iter 145) | Change |
|--------|---------------------|--------------------------|--------|
| IS Sharpe | +1.15 | +1.36 | +18% |
| **OOS Sharpe** | **+2.32** | **+2.33** | **+0.4%** |
| OOS Sortino | +3.41 | +3.01 | -12% |
| OOS WR | 50.6% | 50.6% | same |
| OOS PF | 1.49 | **1.53** | +3% |
| **OOS MaxDD** | **62.83%** | **38.09%** | **-39%** |
| **OOS Calmar** | **2.74** | **3.40** | **+24%** |
| OOS Net PnL | +172.4% | +129.5% | -25% |
| OOS Trades | 164 | 164 | same (no trades skipped) |

**Avg OOS scale**: 0.65 (portfolio is 35% deleveraged on average during OOS).

## Per-Symbol OOS Distribution

| Symbol | Trades | WR | Net PnL | % Total |
|--------|--------|-----|---------|---------|
| BNBUSDT | 50 | 52.0% | +47.5% | **36.6%** |
| ETHUSDT | 34 | 55.9% | +37.4% | 28.9% |
| LINKUSDT | 42 | 52.4% | +36.3% | 28.0% |
| BTCUSDT | 38 | 42.1% | +8.3% | 6.4% |

Concentration shifted from LINK (34.4% in iter 138) to BNB (36.6% in iter 145).
BNB's trades happened during lower-vol periods, keeping them at higher scales.

## Hard Constraints

| Constraint | Threshold | Iter 145 | Pass? |
|------------|-----------|----------|-------|
| OOS Sharpe > baseline | > +2.32 | +2.33 | **PASS** |
| OOS MaxDD ≤ 1.2 × baseline | ≤ 75.4% | 38.09% | **PASS** |
| OOS Trades ≥ 50 | ≥ 50 | 164 | **PASS** |
| OOS PF > 1.0 | > 1.0 | 1.53 | **PASS** |
| Symbol concentration ≤ 50% | ≤ 50% | 36.6% | **PASS** |
| IS/OOS Sharpe ratio > 0.5 | > 0.5 | 0.58 | **PASS** |

All constraints pass.

## Label Leakage Audit

No re-training occurred. Applied post-processing rule to iter 138's trade outputs.
Vol-targeting uses only past daily PnLs (days_before ≥ 1) → walk-forward valid.

## Runtime

~5 seconds (parameter tuning + report generation).

## Deployment Notes

**IMPORTANT**: This iteration's improvements come from a **post-processing rule**
applied to existing trades. To deploy in production:

1. Modify `src/crypto_trade/backtest.py` to compute and apply dynamic weight_factor
   based on trailing portfolio vol
2. Set weight_factor per-trade at open time using only past daily PnLs
3. Verify live execution engine scales orders by weight_factor

The LightGBM models themselves are unchanged from iter 138.
