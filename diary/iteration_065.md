# Iteration 065 Diary — 2026-03-28

## Merge Decision: NO-MERGE

OOS MaxDD hard constraint fails: 70.6% > 22.1% limit (baseline 18.4% × 1.2).
Primary metric also fails: OOS Sharpe +0.94 < baseline +1.95.

**OOS cutoff**: 2025-03-24

## Hypothesis

Align labeling with execution: label training data with ATR-scaled barriers (TP=2.9×ATR_21, SL=1.45×ATR_21) instead of fixed 8%/4%. Model would learn direction given current volatility.

## Configuration Summary
- OOS cutoff: 2025-03-24 (fixed)
- Labeling: **ATR-based** TP=2.9×ATR_21, SL=1.45×ATR_21, timeout=7 days ← CHANGE
- Execution barriers: dynamic — TP=2.9×NATR_21, SL=1.45×NATR_21 (unchanged)
- Symbols: BTCUSDT + ETHUSDT (pooled), 106 features
- Walk-forward: monthly, 24mo training, 5 CV folds, 50 Optuna trials
- Random seed: 42

## Results: Seed 42

| Metric | Iter 065 | Baseline (063) |
|--------|----------|---------------|
| IS Sharpe | +1.07 | +1.48 |
| IS Win Rate | 43.6% | 45.3% |
| IS MaxDD | 70.4% | 74.9% |
| IS Trades | 518 | 541 |
| OOS Sharpe | +0.94 | +1.95 |
| OOS Win Rate | 39.5% | 44.0% |
| OOS MaxDD | **70.6%** | **18.4%** |
| OOS Trades | 147 | 100 |
| OOS/IS | 0.87 | 1.32 |

## Baseline Constraint Check

1. OOS Sharpe 0.94 < 1.95 → FAIL
2. OOS MaxDD 70.6% > 22.1% (18.4% × 1.2) → **HARD FAIL**
3. Min 50 OOS trades: 147 → PASS
4. OOS PF 1.225 > 1.0 → PASS
5. OOS/IS 0.87 > 0.5 → PASS

## What Happened

### 1. ATR labeling creates directional bias in trending markets

The biggest issue: in bull markets (2020-2021), ATR barriers make long TPs easier to hit because large upward moves are more common. This created a 60/40 long/short label imbalance in early training data. The fixed 8%/4% barriers are symmetric in percentage terms and produce ~50/50 labels.

### 2. OOS MaxDD exploded from 18.4% to 70.6%

The baseline's exceptional OOS MaxDD of 18.4% was specifically because:
- The model trained on fixed labels made conservative trades
- ATR execution tightened barriers in the calm OOS period
- The combination limited drawdown accumulation

With ATR labeling, the model learned different patterns, producing more trades (147 vs 100) and less effective signals. The lower confidence threshold (0.510) let through weaker signals.

### 3. The labeling/execution separation is actually OPTIMAL

Iter 063's key insight holds: the model should learn direction on FIXED barriers (symmetric, regime-independent) and EXECUTE with dynamic barriers (adaptive). Aligning them hurts because:
- Fixed labels provide clean directional signal without market regime bias
- Dynamic execution provides volatility adaptation at trade time
- Combining both in labeling introduces correlated noise

### 4. OOS/IS ratio of 0.87 is the healthiest we've seen

Despite worse absolute metrics, the OOS/IS ratio suggests less researcher overfitting. This is because ATR labels create more diverse training conditions. But the absolute performance doesn't justify the change.

## Gap Analysis

OOS WR is 39.5%, break-even is ~35% (given mean TP≈6%, SL≈3.5%). Gap from baseline: 4.5pp WR deficit (39.5% vs 44.0%).

The fundamental issue is signal quality degradation from regime-biased labels, not a parameter tuning problem.

## lgbm.py Code Review

The `atr_label_mode` implementation is clean. One potential issue: the ATR column derivation (`vol_natr_21` → `vol_atr_21` via string replace) is fragile. Should use an explicit `atr_label_column` parameter. Not a bug but poor practice.

## Exploration/Exploitation Tracker

Last 10 (iters 056-065): [X, E, E, E, E, X, X, E, X, E]
Exploration rate: 5/10 = 50%
Type: EXPLORATION (labeling paradigm change)

## Lessons Learned

1. **The labeling/execution separation in iter 063 is a feature, not a bug.** Fixed labeling provides regime-independent directional signal. Dynamic execution adapts trade sizing to conditions. Aligning them introduces unwanted correlation.

2. **ATR-based labeling creates market-regime-dependent label distributions.** In bull markets, long labels dominate. In bear markets, short labels dominate. This biases the model toward the dominant regime in training data.

3. **More trades ≠ better.** The lower confidence threshold (0.510 vs ~0.8) generated 47% more OOS trades but with worse signal quality. The baseline's higher threshold was better at filtering.

## Next Iteration Ideas

Two consecutive explorations failed (iters 064, 065). The model architecture (106 features, pooled, fixed labeling, ATR execution) is proving robust. The next iteration should:

1. **EXPLOITATION: Increase Optuna trials** — 50 → 100 trials. The main weakness is seed variance (std 0.96). More thorough optimization should produce more consistent parameter selection. Simple, low-risk, directly targets the identified weakness.

2. **EXPLOITATION: Narrow training_days range** — Instead of [10, 500], try [200, 500]. This prevents absurdly short training windows (the first month's optimizer was gravitating to training_days=10) while preserving regime adaptation. Targets seed variance from different starting points.

3. **EXPLORATION: Prediction smoothing** — Majority vote of last 3 predictions before generating signal. Reduces prediction flip noise. From the Idea Bank, never tested.

**Recommended**: Option 1 (more Optuna trials). It's the simplest change and directly addresses seed variance without changing the model architecture that's proven robust.
