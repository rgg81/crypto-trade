# Research Brief — Iteration 107

**Type**: EXPLORATION
**Hypothesis**: Half-Kelly position sizing based on ensemble confidence improves risk-adjusted returns by concentrating capital on high-conviction trades.

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Section 1: Problem Statement

Every iteration 094-106 that changes prediction quality or trade selection has failed. The remaining lever is POSITION SIZING — how much to bet on each trade. The baseline uses fixed weight=100 (full position) for all trades regardless of confidence. This means a barely-above-threshold trade at confidence 0.52 gets the same capital allocation as a high-confidence trade at 0.90.

## Section 2: Half-Kelly Formula

```
f* = (p - (1-p)/b) / 2
```

Where:
- p = ensemble confidence (model's predicted probability of correct direction)
- b = TP/SL ratio = 2.0 (8%/4%)
- Division by 2 = half-Kelly (standard conservative adjustment)

Weight = max(10, f* × 100)

| Confidence | f* | Weight | vs Baseline |
|------------|-----|--------|-------------|
| 0.50 | 0.125 | 12.5 | 12.5% of baseline |
| 0.60 | 0.200 | 20.0 | 20% |
| 0.70 | 0.275 | 27.5 | 27.5% |
| 0.80 | 0.350 | 35.0 | 35% |
| 0.90 | 0.425 | 42.5 | 42.5% |

## Section 3: Why This Is Different from All Previous Attempts

- Does NOT change trade count (all trades still execute)
- Does NOT change the model, features, or labeling
- Does NOT change which direction is predicted
- Only changes HOW MUCH capital is allocated per trade
- Zero trainable parameters — purely formula-based
- Based on the model's own confidence, which we haven't leveraged for sizing before

## Section 4: Risk Assessment

**Downside**: If model confidence is NOT predictive of actual win probability, Kelly under-sizes good trades and over-sizes bad ones. Average weight drops from 100 to ~20-30, reducing total PnL even if Sharpe improves.

**Upside**: If confidence IS predictive, concentrating capital on high-confidence trades improves Sharpe by reducing variance from low-conviction bets.
