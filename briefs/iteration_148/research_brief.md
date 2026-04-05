# Iteration 148 Research Brief

**Type**: EXPLORATION (DOGE + per-symbol VT — 3rd attempt)
**Model Track**: A+C+D+DOGE with per-symbol VT
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

DOGE failed in iter 143 (no sizing, MaxDD 92.5%) and iter 146 (portfolio-wide VT,
Sharpe -10%). Per-symbol VT (iter 147) works for A+C+D — could it unlock DOGE?

**Hypothesis**: If DOGE's scaling depends only on DOGE's own daily PnL vol, it
might be less dampened than under portfolio-wide VT, preserving its +73% PnL while
still controlling DOGE-specific drawdowns.

## Configuration

- Models: A+C+D+E (4 models, 5 symbols)
- Per-symbol VT: target=0.5, lookback=30 (iter 147 IS-tuned params)

## Success Criteria

Primary: OOS Sharpe > baseline iter 147 (+2.65)
MaxDD constraint: ≤ 1.2 × 39.17% = 47%
