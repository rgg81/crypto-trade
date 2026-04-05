# Iteration 145 Research Brief

**Type**: EXPLORATION (Volatility-targeted position sizing — post-processing rule)
**Model Track**: A+C+D portfolio + dynamic position sizing
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iter 144 analysis identified July 2025 as a systemic drawdown event: all 4 models
lost -58% combined in a single month, driving the portfolio's 62.8% OOS MaxDD.

**Hypothesis**: Applying volatility-targeted position sizing would reduce exposure
during high-vol regimes, limiting drawdown in crash months without destroying
Sharpe during normal periods.

**Rule**: For each trade, compute trailing-N-day realized portfolio volatility
(std of daily aggregate PnL). Scale the position:

```
scale = target_vol / realized_vol    (clipped to [0.5, 2.0])
```

This is a classical risk management technique (inverse-vol weighting).

## Walk-Forward Methodology

1. **Tune parameters on IS only**: Test 24 configs (6 target_vol × 4 lookback_days)
   on IS trades. Pick best by IS Sharpe.
2. **Apply IS-best to OOS**: Use same rule on OOS trades.
3. **Evaluate**: Compare new OOS metrics vs iter 138 baseline.

**Leakage audit**: For each trade at time T, vol is computed from daily PnLs of
trades that CLOSED before T (days_before ≥ 1). No future information used.

## Research Checklist Categories

### E. Trade Pattern Analysis
Uses iter 138 trades directly — tests whether sizing rules change portfolio
dynamics without re-training models.

### F. Statistical Rigor
Walk-forward validation: tune on IS, test on OOS. Parameter selection uses IS only.
OOS metrics are honest out-of-sample.

## Configuration

| Parameter | Value | Source |
|-----------|-------|--------|
| Scaling rule | `scale = target_vol / realized_vol` | Inverse-vol weighting |
| Target vol | 1.5 | IS-tuned |
| Lookback days | 14 | IS-tuned |
| Min scale | 0.5 | Prevents full deleveraging |
| Max scale | 2.0 | Caps leverage |
| Min history | 5 past daily returns | Avoid noisy initial scaling |

**Applied to**: iter 138 A+C+D trades (816 trades total: 652 IS + 164 OOS).

## Success Criteria

| Constraint | Target |
|-----------|--------|
| OOS Sharpe > baseline +2.32 | Primary |
| OOS MaxDD ≤ 75.4% (1.2× baseline) | Required |
| OOS Trades ≥ 50 | Required |
| OOS PF > 1.0 | Required |
| Symbol concentration ≤ 50% | Required |

## Note on Production Deployment

This iteration tests a **post-processing rule** applied to existing trade outputs.
Implementing this in production requires adding vol-targeting logic to the
backtest/execution engine (modifying `backtest.py` or runner scripts).
