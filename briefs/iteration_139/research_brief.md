# Iteration 139 Research Brief

**Type**: EXPLORATION (ETH standalone screening)
**Model Track**: ETH standalone — potential Model A replacement or split
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

ETH achieves 55.9% OOS WR in the pooled Model A (iter 138), making it the strongest symbol in the portfolio. BTC contributes only 10.7% of OOS PnL with 42.1% WR — it dilutes Model A's signal.

**Hypothesis**: ETH as a standalone model could achieve even higher WR because:
1. All training samples dedicated to ETH patterns (no BTC dilution of ~2,200 samples)
2. Optuna optimizes specifically for ETH's dynamics
3. Feature importance would reflect ETH-specific indicators
4. LINK (IS +0.45) and BNB (IS +0.51) both work as standalone — ETH should too given its stronger signal

**Risk**: ETH standalone reduces training data from ~4,400 to ~2,200 samples with 196 features (ratio drops from 22.4 to 11.2). This is the same ratio as LINK/BNB, which work. But it's below the 50 threshold. LightGBM's `colsample_bytree` provides implicit feature selection.

## Research Checklist Categories

### B. Symbol Universe & Architecture

Testing Model A architecture: pooled BTC+ETH vs ETH standalone (Option B from skill framework).

**Architecture decision matrix**:

| Factor | Pooled A (BTC+ETH) | ETH standalone |
|--------|---------------------|----------------|
| OOS WR | 48.6% combined | ? (55.9% within pooled) |
| Training samples | ~4,400 | ~2,200 |
| Features ratio | 22.4 | 11.2 |
| ETH OOS WR | 55.9% | ? (expected ≥55.9%) |
| BTC OOS WR | 42.1% | N/A |

### E. Trade Pattern Analysis

From iter 138, ETH within Model A:
- OOS: 34 trades, 55.9% WR, +60.2% PnL
- IS: 180 trades, 45.0% WR, +176.9% PnL
- ETH is the #1 PnL contributor across both IS and OOS
- Strong both long and short — balanced direction split

## Configuration

Matching Model A's ATR labeling exactly, but ETH only:

| Parameter | Value |
|-----------|-------|
| Symbols | ETHUSDT |
| Labeling | ATR: TP=2.9×NATR, SL=1.45×NATR |
| Execution | ATR: TP=2.9×NATR, SL=1.45×NATR |
| Training months | 24 |
| Timeout | 7 days |
| Features | Auto-discovery (symbol-scoped) |
| Ensemble | 5 seeds [42, 123, 456, 789, 1001] |
| CV | 5 folds, 50 Optuna trials |
| CV gap | 22 (22 candles × 1 symbol) |
| Cooldown | 2 candles |

## Screening Gates

1. **Gate 1 — Data quality**: ETH has data since 2020. PASS.
2. **Gate 2 — Liquidity**: ETH is #2 by volume. PASS.
3. **Gate 3 — Stand-alone profitability**: IS Sharpe > 0, IS WR > 33.3%, ≥100 IS trades.

## Success Criteria

If ETH standalone beats ETH's contribution within Model A:
- IS trades ≥ 100
- IS Sharpe > 0 (profitable standalone)
- OOS WR > 50% (matching or exceeding pooled 55.9%)

If successful, iter 140 would test: ETH(standalone) + BTC(standalone or dropped) + C(LINK) + D(BNB).
