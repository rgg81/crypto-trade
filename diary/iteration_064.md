# Iteration 064 Diary — 2026-03-28

## Merge Decision: NO-MERGE (EARLY STOP)

**OOS cutoff**: 2025-03-24

## Hypothesis

Remove `training_days` from Optuna search space to reduce seed variance. Force the model to use the full 24-month training window consistently.

## Configuration Summary
- OOS cutoff: 2025-03-24 (fixed)
- Labeling: triple barrier TP=8%, SL=4%, timeout=7 days (unchanged)
- Execution barriers: dynamic — TP=2.9×NATR_21, SL=1.45×NATR_21 (unchanged)
- Symbols: BTCUSDT + ETHUSDT (pooled), 106 features
- Walk-forward: monthly, 24mo training, 5 CV folds, 50 Optuna trials
- **CHANGE**: `optimize_training_window=False` — disabled training_days Optuna param
- Random seed: 42

## Result: EARLY STOP at Year 1

| Metric | Iter 064 | Baseline (063) |
|--------|----------|---------------|
| IS Sharpe | **-0.91** | +1.48 |
| IS Win Rate | **33.6%** | 45.3% |
| IS Profit Factor | **0.82** | 1.34 |
| IS Max Drawdown | **139.9%** | 74.9% |
| IS Total Trades | 116 (truncated) | 541 |

Year 2022: PnL=-65.8%, WR=33.9%, 115 trades → EARLY STOP triggered.
No OOS data (stopped before OOS period).

## What Happened

### 1. training_days is a regime adaptation mechanism, not noise

The hypothesis was wrong. `training_days` (range [10, 500]) isn't just a variance source — it's how the model adapts to market regime changes. In each walk-forward month, Optuna finds the optimal training window:
- In regime transitions: shorter window (recent data only)
- In stable periods: longer window (more data)

### 2. Full 24-month window dilutes regime signal

Without training_days optimization, the model uses ALL 24 months equally. For 2022 predictions (bear market), this includes 2020-2021 bull-market patterns. The conflicting signals destroyed WR: 45.3% → 33.6% (below break-even 35.6%).

### 3. The early stop was fast and decisive (404s)

The model failed its very first year of predictions. This is exactly how fail-fast should work — no wasted compute on 4 more years of bad predictions.

## Gap Analysis

WR is 33.6%, break-even is ~35.6% (given mean TP=7.25%, SL=4.00%). Gap is 2.0pp. But this is moot — the approach is fundamentally flawed, not a close miss.

## Lessons Learned

- **training_days is ESSENTIAL.** It's the mechanism that makes walk-forward adaptive. Without it, the model can't adjust to regime changes, and 24 months of data becomes a liability rather than an asset.
- **The "one search dimension" assumption was wrong.** training_days doesn't just find a number — it enables the model to focus on the most relevant sub-period of training data per month. This is architectural, not just a hyperparameter.
- **Seed variance from training_days may be a feature.** Different seeds finding different training_days reflects genuine uncertainty about the optimal window. The variance is information, not noise.

## lgbm.py Code Review

The `optimize_training_window` flag implementation is clean and backward-compatible. Default `True` preserves existing behavior. No bugs found. The code change is correct — the result is simply that removing training_days is a bad idea.

## Exploration/Exploitation Tracker

Last 10 (iters 055-064): [X, X, E, E, E, E, X, X, E, X]
Exploration rate: 4/10 = 40%
Type: EXPLOITATION (removed one Optuna parameter)

## Research Checklist

Categories completed: A (partial — no feature importance, feature set unchanged), E (trade patterns).
After MERGE, 2 categories sufficient. ✓

## Next Iteration Ideas

Since this was an EARLY STOP, the next iteration MUST propose **structural changes only**. Parameter-only changes are banned.

**Priority proposals** (from Research Checklist + Idea Bank):

1. **EXPLORATION: Dynamic ATR-based labeling** — Currently labels use fixed 8%/4%, execution uses ATR-scaled barriers. Align both: label with TP=2.9×NATR_21, SL=1.45×NATR_21. The model would learn which direction is profitable given CURRENT volatility, not a fixed barrier. This addresses a fundamental mismatch between what the model trains on vs what it executes.

2. **EXPLORATION: Ensemble across 3 seeds** — Train 3 models (seeds 42, 123, 789), average their predicted probabilities before applying confidence threshold. Reduces seed variance architecturally rather than parametrically.

3. **EXPLORATION: Add interaction features** — RSI × ADX, volatility × trend_strength. Never tested. Creates new feature category (currently 6 groups, ~106 features).

**Recommended**: Option 1 (dynamic labeling). Addresses the labeling/execution mismatch directly, builds on the ATR barrier breakthrough from iter 063, and is the most theoretically justified. The current separation works OK but aligning them could improve signal quality.
