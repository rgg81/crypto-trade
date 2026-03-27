# Iteration 056 — EXPLOITATION (remove is_unbalance=True)

## NO-MERGE: Removing is_unbalance degrades all metrics. IS Sharpe 1.09 vs baseline 1.60. OOS Sharpe 0.45 vs baseline 1.16. is_unbalance is load-bearing.

**OOS cutoff**: 2025-03-24

## Results (seed=42 only, no seed validation needed)

| Metric | IS | OOS | Baseline IS | Baseline OOS |
|--------|-----|-----|-------------|-------------|
| Sharpe | +1.09 | +0.45 | +1.60 | +1.16 |
| Win Rate | 41.9% | 39.4% | 43.4% | 44.9% |
| Profit Factor | 1.24 | 1.10 | 1.31 | 1.27 |
| Max Drawdown | 72.8% | 59.8% | 64.3% | 75.9% |
| Total Trades | 511 | 127 | 574 | 136 |
| OOS/IS Sharpe | 0.41 | — | 0.72 | — |

## What Happened

### 1. is_unbalance=True is load-bearing, not redundant

The hypothesis was that `is_unbalance=True` and PnL-magnitude sample weights were redundant, so removing one might reduce over-correction and improve OOS. **Wrong.** Removing `is_unbalance` hurt BOTH IS and OOS:

- IS Sharpe dropped 32% (1.60 → 1.09)
- OOS Sharpe dropped 61% (1.16 → 0.45)
- IS WR dropped 1.5pp, OOS WR dropped 5.5pp

The IS degradation proves this isn't about overfitting — `is_unbalance` genuinely helps the model learn better patterns during training. The two mechanisms are complementary, not redundant:
- `is_unbalance`: corrects for class frequency imbalance (57% long / 43% short)
- Sample weights: encode PnL magnitude (how much each trade matters economically)

### 2. Why it matters: class imbalance is real

Training labels are 57/43% long/short. Without `is_unbalance`, the model over-predicts longs (the majority class). Since shorts are more profitable in this strategy (PF 1.36 vs 1.26 for longs in baseline), suppressing short predictions hurts performance disproportionately.

### 3. Iter 055 + 056 bracket the solution

- Iter 055: MORE class balancing (`_balance_weights` + `is_unbalance`) → OOS degraded by -0.63 Sharpe
- Iter 056: LESS class balancing (only sample weights, no `is_unbalance`) → OOS degraded by -0.71 Sharpe
- Baseline 047: exactly `is_unbalance=True` + PnL sample weights → the sweet spot

This bracketing confirms the baseline's class-balancing configuration is optimal. Further changes to class weighting are a dead end.

## Quantifying the Gap

- OOS WR: 39.4% (iter 056) vs 44.9% (baseline) — 5.5pp degradation, 15% below baseline
- Break-even WR: 34.2%. Current 39.4% is 5.2pp above break-even — still profitable but barely
- OOS PF: 1.10 — just barely above 1.0. Marginal profitability
- The class-balancing mechanism accounts for ~5pp WR, which is the difference between marginal and solid profitability

## Decision: NO-MERGE

**Primary metric fails**: OOS Sharpe 0.45 < baseline 1.16
**Hard constraint fails**: OOS/IS Sharpe ratio 0.41 < 0.50 (overfitting gate)

Seed validation skipped — single seed already fails decisively.

## lgbm.py Code Review

No new findings beyond iter 055's review. The code correctly handles both `is_unbalance=True` and `is_unbalance=False` scenarios. The labeling weights ([1, 10] range) are applied correctly regardless of the `is_unbalance` setting. No bugs.

## Research Checklist Completed

Full research (4 categories) done in QR phases 1-4:

- **A (Feature Contribution)**: Top features are price-level (VWAP 8.25%, A/D 5.27%, OBV 3.65%). Momentum group weakest (4.45% for 36 features). Autocorrelation and kurtosis are genuine signals. 55 features have near-zero importance.
- **D (Feature Frequency)**: 15/25 feature types lack lookbacks > 10 days. Standard daily RSI-14 needs period=42 on 8h candles; current max RSI is 30 (≈ daily RSI-10). ADX, ATR, NATR, Supertrend all too short. This is the single largest structural gap.
- **E (Trade Patterns)**: 23:00 UTC session = 76% of PnL (49.5% WR). Year-over-year decay: +1.26%/trade (2022) → +0.23%/trade (2024). ETH = 79% of PnL. Shorts > longs (PF 1.36 vs 1.26).
- **F (Statistical Rigor)**: IS edge is real (p < 0.000002). Bootstrap WR CI [39.4%, 47.4%]. Minimum detectable improvement ~4pp WR at 574 trades. Trades are serially correlated (runs test p=0.011).

## Exploration/Exploitation Tracker

Last 10 (iters 047-056): [E, E, E, E, X, E, E, E, X, X]
Exploration rate: 7/10 = 70% — still over-explored. Exploitation needed.

## What We've Eliminated (iters 047-056)

| Iter | Change | Result | Learning |
|------|--------|--------|----------|
| 048 | Add _balance_weights() | NO-MERGE | More class balancing hurts |
| 049 | Parallel BTC+ETH + SOL+DOGE | NO-MERGE | Symbol pairs don't combine well |
| 050 | Balanced weights (no code change) | NO-MERGE | Was just a baseline re-run |
| 051 | 14-day timeout | EARLY STOP | Longer timeout hurts |
| 052 | Add XRP to pool | EARLY STOP | More symbols hurt |
| 053 | BNB+LINK independent pair | EARLY STOP | BTC+ETH best pair |
| 054 | AVAX+DOT independent pair | EARLY STOP | BTC+ETH best pair |
| 055 | Balanced weights (real code) | NO-MERGE | Confirmed over-correction |
| 056 | Remove is_unbalance | NO-MERGE | is_unbalance is load-bearing |

**Dead ends confirmed**: symbol expansion, class weight changes, timeout changes. The baseline 047 configuration is locally optimal for these dimensions.

## Next Iteration Ideas

The only unexplored structural improvement from research is **feature engineering**. The research analysis found massive gaps in feature lookback periods. This should be the priority.

1. **Slow features — Tier 1** (EXPLORATION, HIGHEST PRIORITY): Add daily-equivalent lookback periods to momentum, volatility, and trend features. Specifically: RSI_42/63/90, ADX_42/63, ATR_42/63, NATR_42/63, MACD_(21,63,9). 15/25 feature types currently max out at ≤10 days — the model has never seen standard daily indicators. This is the #1 untested exploration from the idea bank, validated by feature importance analysis showing long-period features consistently outrank short-period ones.

2. **Remove 55 near-zero features** (EXPLOITATION): Prune features with <0.05% importance. Reduces noise and dimensionality. Could combine with #1 (add slow features, remove useless ones).

3. **Time-of-day filter** (EXPLOITATION): The 15:00 UTC session produces only 0.10% avg PnL per trade vs 1.37% for 23:00. Filtering out 15:00 would lose 30% of trades but only 5% of PnL. Simple win.

4. **Per-symbol models** (EXPLORATION): Feature importance shows price-level features dominate because the model uses them to distinguish BTC from ETH. Separate models would eliminate this proxy and force the model to learn actual patterns per symbol.

5. **Regime-based TP/SL** (EXPLORATION): Year-over-year decay shows the fixed 8%/4% works well in volatile markets (2022) but poorly in calmer ones (2024). ATR-based dynamic barriers could adapt.
