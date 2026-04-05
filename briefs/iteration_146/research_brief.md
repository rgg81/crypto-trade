# Iteration 146 Research Brief

**Type**: EXPLORATION (DOGE re-addition with vol targeting)
**Model Track**: A+C+D+DOGE with vol-targeted position sizing
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iter 143 failed to add DOGE to the portfolio: OOS MaxDD exploded 62.8% → 92.5%.
Iter 145 proved vol-targeting cuts MaxDD by 39%.

**Hypothesis**: With vol targeting active, DOGE's drawdown contribution may fit
within the 1.2× baseline MaxDD constraint, allowing DOGE's +73% PnL contribution.

**Expected math**:
- iter 143 MaxDD without sizing: 92.5%
- Expected with vol targeting (39% reduction): ~56%
- Threshold (1.2× baseline 38.1%): 45.7%
- If vol targeting can bring 4-model MaxDD below 45.7%, DOGE becomes viable

## Configuration

- Models: A (BTC+ETH) + C (LINK) + D (BNB) + E (DOGE) — 4 models
- Trade data: iter 138 + iter 142 DOGE (deterministic, identical to iter 143)
- Vol targeting: target_vol=1.5, lookback=14 (iter 145 IS-tuned config)

## Success Criteria

Primary: OOS Sharpe > baseline iter 145 (+2.33)
Constraints: MaxDD ≤ 45.7%, Trades ≥ 50, PF > 1.0, concentration ≤ 50%
