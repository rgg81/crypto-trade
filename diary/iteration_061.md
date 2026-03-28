# Iteration 061 Diary — 2026-03-28

## Merge Decision: NO-MERGE

OOS Sharpe +0.51 vs baseline +1.16. OOS/IS ratio 0.36 < 0.50 gate. Feature selection on IS data introduced researcher overfitting. However, this is the **best result since baseline** — first full completion, IS metrics nearly match, MaxDD improved.

**OOS cutoff**: 2025-03-24

## Hypothesis

Pruning 56 low-importance features (106 → 50) reduces noise, allowing LightGBM to focus on the most informative features. The bottom 56 features account for only 20.8% of gain importance.

## Configuration Summary
- OOS cutoff: 2025-03-24 (fixed)
- Labeling: triple barrier TP=8%, SL=4%, timeout=7 days
- Symbols: BTCUSDT + ETHUSDT (pooled)
- Features: **50** (top 50 by gain importance, from baseline's 106)
- Walk-forward: monthly, 24mo training, 5 CV folds, 50 Optuna trials
- Random seed: 42

## Results: In-Sample (trades with entry_time < 2025-03-24)

| Metric | Value | Baseline IS |
|--------|-------|-------------|
| Sharpe | +1.40 | +1.60 |
| Win Rate | 43.3% | 43.4% |
| Profit Factor | 1.31 | 1.31 |
| Max Drawdown | 53.5% | 64.3% |
| Total Trades | 503 | 574 |
| PnL | +341.3% | +387.9% |

## Results: Out-of-Sample (trades with entry_time >= 2025-03-24)

| Metric | Value | Baseline OOS |
|--------|-------|-------------|
| Sharpe | +0.51 | +1.16 |
| Win Rate | 39.7% | 44.9% |
| Profit Factor | 1.10 | 1.27 |
| Max Drawdown | 55.3% | 75.9% |
| Total Trades | 141 | 136 |
| PnL | +32.3% | +78.6% |
| OOS/IS Sharpe | 0.36 | 0.72 |

## What Happened

### 1. IS nearly matches baseline — pruning didn't hurt IS

IS Sharpe 1.40 vs 1.60 (only 12.5% lower). IS PF identical at 1.31. IS WR 43.3% vs 43.4%. This confirms that the bottom 56 features carry minimal IS signal — removing them barely affects IS performance.

IS MaxDD improved from 64.3% to 53.5% — a 17% improvement. The removed noisy features were causing the model to make worse calls during drawdown periods.

### 2. IS per-symbol balance improved dramatically

| Symbol | Baseline IS PnL | Iter 061 IS PnL |
|--------|-----------------|-----------------|
| BTC | +81.8% (21.1%) | +173.6% (50.9%) |
| ETH | +306.1% (78.9%) | +167.7% (49.1%) |

BTC's IS PnL more than doubled (+81.8% → +173.6%). ETH decreased but remained profitable. The 50/50 balance is much healthier than the 21/79 concentration.

### 3. OOS degraded — researcher overfitting

OOS Sharpe dropped from 1.16 to 0.51 (56% lower). OOS WR dropped from 44.9% to 39.7% (5.2pp). The OOS/IS ratio of 0.36 is below the 0.50 gate, indicating the feature selection biased toward IS patterns.

The feature selection was done using gain importance from a single LightGBM trained on IS data. This implicitly selects features that explain IS variation, which doesn't fully generalize to OOS.

### 4. OOS BTC went negative

BTC OOS: 53 trades, 39.6% WR, -6.5% PnL. The improved IS balance didn't transfer to OOS. This suggests the BTC IS improvement was partly due to overfitting on IS BTC patterns.

### 5. MaxDD improved in both IS and OOS

IS: 53.5% vs 64.3% (better)
OOS: 55.3% vs 75.9% (better!)

Feature pruning does reduce drawdown risk, even OOS. This is a genuine improvement — the removed features were causing noise-driven trades during drawdowns.

## Quantifying the Gap

- OOS Sharpe: +0.51, baseline +1.16 — 56% lower but still positive
- OOS WR: 39.7%, break-even ~34.2%, gap = +5.5pp. Baseline gap = +10.7pp. Lost 5.2pp.
- OOS PF: 1.10 — modestly profitable. Baseline 1.27.
- OOS/IS ratio: 0.36 — researcher overfitting. Feature selection on IS data biased model.

## Decision: NO-MERGE

Fails primary metric (OOS Sharpe 0.51 < 1.16) and researcher overfitting gate (ratio 0.36 < 0.50). But the direction is very promising.

## lgbm.py Code Review

The `feature_columns` whitelist implementation is clean — filters discovered columns in `compute_features()`. No issues.

One concern: the importance analysis used a proxy label (3-candle forward return) on full IS data rather than the actual walk-forward labeling. The selected features may not be optimal for the walk-forward regime. A better approach would be permutation importance within each walk-forward fold, but this adds significant complexity.

## Research Checklist

Completed 2 categories (A, F) — minimum for exploitation:
- **A (Feature Contribution)**: Gain-based importance from single IS LightGBM. Top 50 features = 79.2% of importance.
- **F (Statistical Rigor)**: Feature/sample ratio improved from 0.024 to 0.011. IS performance confirmed minimal degradation.

## Exploration/Exploitation Tracker

Last 10 (iters 052-061): [E, E, X, X, X, E, E, E, E, X]
Exploration rate: 6/10 = 60%
Type: EXPLOITATION (feature pruning)

## What Worked

- **IS performance preserved**: Sharpe 1.40, PF 1.31, WR 43.3% — nearly identical to baseline with 53% fewer features
- **MaxDD improved**: 53.5% IS, 55.3% OOS — both better than baseline
- **IS balance improved**: 50/50 BTC/ETH vs 21/79 in baseline
- **Full backtest completion**: First since iter 047 (13 iterations ago!)

## What Failed

- OOS degraded (Sharpe 0.51 vs 1.16) — researcher overfitting from IS-based feature selection
- OOS BTC went negative (-6.5%) while baseline BTC was +78.6%
- OOS/IS ratio 0.36 < 0.50 gate

## Next Iteration Ideas

Feature pruning is the right direction — it preserved IS and improved MaxDD. The problem is the feature SELECTION method (full-IS importance), not the concept.

1. **Less aggressive pruning: top 75 features** (EXPLOITATION): Keep 75 instead of 50. The remaining 25 features may carry OOS-relevant signal that the IS-only analysis missed. Less bias from feature selection.

2. **Correlation-based dedup instead of importance** (EXPLOITATION): Remove features with |corr| > 0.95 from each other. This is agnostic to IS performance — removes redundancy, not "low importance" features. Less researcher overfitting risk.

3. **Dynamic TP/SL via ATR** (EXPLORATION): Combine with the baseline 106 features. The pruning results show the model is robust — changes to the execution layer (ATR-based barriers) may improve OOS by adapting to market conditions.

4. **Combine pruning + ATR barriers** (EXPLORATION): Use 50-75 features AND dynamic barriers. The IS MaxDD improvement from pruning + adaptive barriers could compound.

5. **Walk-forward importance**: Compute importance per monthly fold and keep features that are consistently important across folds. More robust than single-shot IS importance.

## Lessons Learned

- **Feature pruning works for IS**: Removing 53% of features barely affected IS Sharpe (1.40 vs 1.60) and improved MaxDD (53.5% vs 64.3%). The baseline's 106 features contain significant redundancy.
- **IS-based feature selection introduces researcher overfitting**: Selecting features on IS data biases the model toward IS patterns, hurting OOS. The 0.36 OOS/IS ratio confirms this.
- **MaxDD improvement is robust**: Both IS and OOS MaxDD improved, suggesting pruned features genuinely added noise during drawdowns.
- **BTC IS improvement was partly overfitting**: BTC went from 21% of IS PnL to 51% — but this didn't transfer to OOS where BTC was negative. The feature selection favored BTC IS patterns.
- **This is the most promising direction since iter 047**: First full completion in 14 iterations. The concept is sound; the selection method needs improvement.
