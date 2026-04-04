# Iteration 139 Engineering Report

**Role**: QE
**Config**: ETH standalone, ATR labeling 2.9×NATR/1.45×NATR

## Results

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | -0.46 | -0.63 |
| WR | 35.6% | 33.3% |
| PF | 0.88 | 0.83 |
| MaxDD | 134.1% | 50.7% |
| Trades | 222 | 51 |
| Net PnL | -60.8% | -17.8% |

**Gate 3**: IS Sharpe < 0 → **FAIL**. ETH standalone is not profitable.

## Comparison: ETH Standalone vs ETH in Pooled Model A

| Metric | ETH Pooled (iter 138) | ETH Standalone |
|--------|----------------------|----------------|
| IS WR | 45.0% (180 trades) | 35.6% (222 trades) |
| OOS WR | 55.9% (34 trades) | 33.3% (51 trades) |
| Training samples | ~4,400 (BTC+ETH) | ~2,200 (ETH only) |
| Feature ratio | 22.4 | 11.2 |

ETH WR drops 22.6pp OOS when isolated. The pooled BTC data is essential.

## Label Leakage Audit

- CV gap = 22 (22 × 1 symbol). Verified.
- Walk-forward verified.

## Runtime: 5,786s (~96 min)
