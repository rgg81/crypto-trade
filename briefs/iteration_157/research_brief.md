# Iteration 157 Research Brief

**Type**: EXPLORATION (rule-based meta-filter, no ML)
**Model Track**: v0.152 baseline + simple filter layer
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iter 156's Next Ideas #2: "Simple rule-based meta-filter (no LightGBM)".
The LightGBM meta-model (iter 156) over-fitted on IS and failed to beat
baseline OOS. A simple rule-based filter trained on aggregate IS
statistics may generalize better because it has fewer parameters to fit.

## Research Analysis

### IS Aggregate Bucket Statistics (iter 138 trades, 652 IS trades)

**Overall**: WR 44.5%, mean PnL +0.58%. Break-even = 33.3% WR.

**Direction split** (STRONG signal):
| Direction | n | WR | Mean PnL |
|-----------|---|-----|---------|
| LONG (+1) | 346 | 48.3% | **+1.14%** |
| SHORT (-1) | 306 | 40.2% | -0.06% |

**Symbol × Direction** (critical pattern):
| Symbol | Dir | n | WR | Mean PnL |
|--------|-----|---|-----|---------|
| BTCUSDT | SHORT | 77 | 39.0% | **-0.21%** |
| BTCUSDT | LONG | 69 | 52.2% | +0.77% |
| BNBUSDT | SHORT | 69 | 39.1% | **-0.11%** |
| BNBUSDT | LONG | 74 | 50.0% | +0.94% |
| ETHUSDT | SHORT | 84 | 41.7% | +0.50% |
| ETHUSDT | LONG | 96 | 47.9% | **+1.41%** |
| LINKUSDT | SHORT | 76 | 40.8% | **-0.48%** |
| LINKUSDT | LONG | 107 | 44.9% | +1.28% |

**BTC/BNB/LINK SHORTs are strictly unprofitable on IS.** ETH SHORT is
break-even. LONGs all profitable.

**Hour-of-day** (weaker signal):
| Hour | n | WR | Mean PnL |
|------|---|-----|---------|
| 07 UTC | 219 | 46.6% | +1.20% |
| 15 UTC | 208 | 43.8% | +0.69% |
| 23 UTC | 225 | 43.1% | -0.13% |

**Traded-symbol ADX quartile**:
| Quartile | Range | WR | Mean PnL |
|----------|-------|-----|---------|
| Q1 (<19.6) | low | 49.1% | +1.17% |
| Q2 (19.6-25.6) | mid-low | 41.7% | +0.56% |
| Q3 (25.6-34.6) | mid-high | 39.9% | **-0.44%** |
| Q4 (>34.6) | high | 47.2% | +1.03% |

Q3 is worst — false trends at mid-range ADX.

### Proposed Rules (to grid-search on IS)

**Rule A (no-short)**: Drop all SHORT trades. Very aggressive (-46% trades).

**Rule B (targeted-short)**: Drop SHORTs where symbol ∈ {BTC, BNB, LINK}.
Keep ETH SHORT and all LONGs. Drops ~222 trades (34%).

**Rule C (hour-filter)**: Drop trades at hour=23 UTC. Drops 225 trades (35%).

**Rule D (ADX-Q3)**: Drop trades where symbol ADX ∈ (19.6, 34.6]. Drops
~326 trades (50%).

**Rule E (B + C combo)**: Targeted-short + hour-23 filter.

**Rule F (weak-bucket)**: Drop intersections of WR < 40% buckets:
BTC/BNB/LINK × SHORT × (hour=23 OR ADX-Q3).

### Success Criteria

Selection metric: **IS Sharpe** (v0.152 baseline IS Sharpe = 1.33).
Winner: config with highest IS Sharpe, ≥ 150 IS trades retained.

Merge requires:
- OOS Sharpe > baseline (+2.83)
- OOS trades ≥ 50
- OOS MaxDD ≤ 38.7%
- OOS PF > 1.0

### Checklist Categories

- **E (Trade Pattern)**: Full bucket analysis by direction, hour, ADX,
  symbol × direction. Identified LONG bias and SHORT weakness per symbol.
- **F (Statistical Rigor)**: WR variance across buckets — BTC/BNB/LINK
  SHORTs all fall below break-even (40%) with n=69-77 per bucket.

## Hypothesis

A simple IS-derived rule (e.g., "no BTC/BNB/LINK SHORTs") has 1-2
parameters and should overfit less than iter 156's 8-feature LightGBM. It
will either improve OOS Sharpe (via better selection) or maintain it (if
the IS pattern reflects noise).

## Risks

1. **IS-OOS regime shift**: the LONG bias on IS may reverse on OOS.
2. **Concentration**: drops many trades → fewer portfolio effects.
3. **The 30% concentration rule**: if we drop all BTC trades, ETH might
   exceed 30%.

## Notes

No primary model retraining. Post-processing on iter 138 trades. VT
scales from iter 152 config applied to kept trades. Walk-forward valid
by construction: rules based on aggregate IS statistics (not per-trade
past data).
