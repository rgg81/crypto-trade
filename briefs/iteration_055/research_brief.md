# Research Brief: Iteration 055 — EXPLOITATION

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

IS data only was used during this research phase.

## Objective

**Seed-validate iteration 050's balanced class weights** configuration. Iter 050 produced the highest OOS Sharpe ever (+1.66) with a single seed, but was not validated. If 4/5 seeds show OOS Sharpe > 0, this becomes the new baseline.

## Context: 7 Consecutive NO-MERGE Since Baseline 047

| Iter | Type | Change | Result |
|------|------|--------|--------|
| 048 | Explore | Balanced class weights | OOS +0.10 |
| 049 | Explore | +SOL+DOGE to pool | OOS +1.16 (no improvement) |
| 050 | Explore | Balanced weights retry | OOS +1.66 (single seed!) |
| 051 | Exploit | 14-day timeout | OOS -0.65 |
| 052 | Explore | +XRP to pool | IS +0.54 (EARLY STOP) |
| 053 | Explore | BNB+LINK pair | IS +1.08 (EARLY STOP) |
| 054 | Explore | AVAX+DOT pair | IS -0.24 (EARLY STOP) |

**Exploration rate**: 8/10 = 80%. This iteration MUST be exploitation.

Symbol expansion is exhausted — BTC+ETH is the optimal pair at 8%/4% + 7d barriers. The remaining lever is model training improvements.

## Research Analysis (4 categories completed)

### Category C: Labeling Analysis (IS)

- **Label distribution**: 45.9% long / 54.1% short — slight short bias but within 55/45 tolerance
- **Label stability**: 23.8% flip rate — well below 60% threshold, labels are stable
- **Exit reasons**: TP=32%, SL=52%, Timeout=16%
- **Timeout trades**: 70% WR, mean +1.51%, consistently profitable at 7-day window
- **Long/Short balance**: Both directions perform equally (WR ~42.5-43%, PnL ~160-174%)

### Category E: Trade Pattern Analysis (IS)

Monthly performance shows seasonal patterns:
- **Strong months**: Mar 2022, May-Aug 2022, Jan 2023, Feb-Apr 2024, Jul-Aug 2024, Nov 2024
- **Weak months**: Jan-Feb 2022, Apr 2022, Sep-Oct 2023, Jun 2024, Dec 2024-Jan 2025
- No systematic time-of-year bias — profitable and losing months are distributed across all seasons

Per-symbol per-year: All years profitable for both BTC and ETH individually.

**Critical per-symbol finding (iter 050 vs baseline 047)**:
- Iter 050 balanced weights IS: BTC 50.1% / ETH 49.9% of total PnL — perfectly balanced
- Baseline 047 IS: ETH 78.9% / BTC 21.1% — heavily ETH-biased
- Baseline 047 OOS: roles flip to BTC 70.5% / ETH 29.5%

This suggests balanced class weights prevent symbol-level overfitting. When IS contribution is 50/50, the model doesn't overfit to one symbol's patterns and generalizes better to OOS.

### Category F: Statistical Rigor (IS)

- **WR**: 42.7%, break-even WR: 34.2%, gap: **+8.6 pp**
- **Bootstrap WR 95% CI**: [38.7%, 46.8%] — **excludes break-even** (34.2%)
- **Binomial p-value** (WR > break-even): **p = 0.000015** — highly significant
- **Bootstrap total PnL 95% CI**: [+76.6%, +593.2%]
- **P(PnL < 0)**: 0.6% — the IS signal is real, not noise
- **TP/SL ratio**: 0.60 (above 0.50 break-even for 2:1 RR)

The IS signal is statistically robust. The question is whether OOS holds across seeds.

### Category A: Feature Contribution (partial)

No feature_importance.csv in iter 050 reports (not generated for this iteration). 106 global intersection features used — same as baseline.

No new features proposed for this iteration since the goal is seed validation of an existing config. Feature engineering is deferred to iter 056 (proposed as next exploration iteration).

## Code Change

Re-apply `_balance_weights(y, w)` from iteration/048 branch to `optimization.py`:
- Adds `_balance_weights()` function that scales sample weights so sum(w[class_0]) ≈ sum(w[class_1])
- Applied in both CV folds and final retrain
- No other code changes

## Configuration (identical to iter 050)

| Parameter | Value |
|-----------|-------|
| Symbols | BTCUSDT, ETHUSDT |
| Training months | 24 |
| Barriers | TP=8%, SL=4% |
| Timeout | 7 days (10080 min) |
| CV folds | 5 |
| Optuna trials | 50 |
| Confidence threshold | Optuna 0.50–0.85 |
| Fee | 0.1% |
| Seeds | 42, 123, 456, 789, 1001 |

## Merge Criteria

Per seed validation protocol:
1. Mean OOS Sharpe > 0
2. At least 4 of 5 seeds are profitable (OOS Sharpe > 0)

Also check baseline comparison rules:
- OOS Sharpe > baseline +1.16
- MaxDD ≤ baseline 75.9% × 1.2
- Min 50 OOS trades
- PF > 1.0 (OOS)
- No single symbol > 30% of OOS PnL
- IS/OOS Sharpe ratio > 0.5

## Next Iteration Ideas (if this merges)

1. **Feature engineering** (EXPLORATION): Cross-asset features (BTC as leading indicator for ETH), interaction features (RSI × ADX), multi-timeframe indicators
2. **ATR-dynamic barriers**: Scale TP/SL per-candle by recent volatility
3. **Regime-aware confidence**: Higher threshold in low-volatility periods
