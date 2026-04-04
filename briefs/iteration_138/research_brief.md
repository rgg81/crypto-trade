# Iteration 138 Research Brief

**Type**: EXPLOITATION (MILESTONE: A(ATR)+C+D portfolio)
**Model Track**: Combined A (BTC/ETH + ATR labeling) + C (LINK) + D (BNB)
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iteration 137 proved that ATR labeling transforms Model A:
- OOS Sharpe: +1.67 (Model A alone)
- ETH OOS WR: 55.9% (was 45.5%)
- BTC OOS WR: 42.1% (was 38.5%)

The baseline A+C+D portfolio (iter 134) has OOS Sharpe +1.94 with static-labeling Model A. Replacing Model A with the ATR-labeling version should improve the portfolio. This iteration tests the full combination.

## Configuration

**Model A (BTC+ETH)** — changed from baseline:
- Labeling: **ATR: TP=2.9×NATR, SL=1.45×NATR** (was static 8%/4%)
- use_atr_labeling: **True** (was False)
- All other params identical to iter 134

**Model C (LINK)** — unchanged from baseline:
- ATR labeling: TP=3.5×NATR, SL=1.75×NATR

**Model D (BNB)** — unchanged from baseline:
- ATR labeling: TP=3.5×NATR, SL=1.75×NATR

**Single variable changed**: Model A's use_atr_labeling.

## Success Criteria

Must beat baseline (iter 134) on primary metric + pass all hard constraints:

| Constraint | Baseline 134 | Threshold |
|------------|-------------|-----------|
| OOS Sharpe | +1.94 | > +1.94 |
| OOS MaxDD | 79.7% | ≤ 95.6% (1.2×) |
| OOS Trades | 199 | ≥ 50 |
| OOS PF | 1.38 | > 1.0 |
| Symbol concentration | 34.4% | ≤ 50% |
