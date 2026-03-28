# Iteration 076 Diary — 2026-03-28

## Merge Decision: NO-MERGE

OOS Sharpe +1.72 < baseline +1.84. Primary metric not beaten. However, OOS MaxDD halved (21.6% vs 42.6%) — the most significant risk improvement in 76 iterations. Strategy documented for future reference.

**OOS cutoff**: 2025-03-24

## Hypothesis

Align labeling barriers with execution barriers. The baseline trains on fixed TP=8%/SL=4% labels but executes with dynamic ATR barriers (TP=2.9×NATR_21, SL=1.45×NATR_21). 49.4% of candles have execution barriers tighter than training labels. Aligning them should teach the model the actual risk/reward for each volatility environment.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- Labeling: Triple barrier **dynamic ATR** TP=2.9×NATR_21, SL=1.45×NATR_21, timeout=7d
- Symbols: BTCUSDT, ETHUSDT
- Features: 106 (global intersection, unchanged)
- Walk-forward: monthly retraining, 24mo window, 5 CV folds, 50 Optuna trials
- Ensemble: 3 seeds [42, 123, 789]
- Execution: Dynamic ATR barriers (same multipliers), cooldown=2

## Results: In-Sample (trades with entry_time < 2025-03-24)

| Metric | Iter 076 | Baseline (068) | Change |
|--------|----------|----------------|--------|
| Sharpe | **+1.30** | +1.22 | **+6.5%** |
| Win Rate | **47.2%** | 43.4% | **+3.8pp** |
| Profit Factor | **1.39** | 1.35 | +3.0% |
| Max Drawdown | **41.6%** | 45.9% | **-4.3pp** |
| Total Trades | 307 | 373 | -18% |
| Net PnL | 241.2% | 264.3% | -8.7% |

## Results: Out-of-Sample (trades with entry_time >= 2025-03-24)

| Metric | Iter 076 | Baseline (068) | Change |
|--------|----------|----------------|--------|
| Sharpe | 1.72 | **1.84** | **-6.5%** |
| Win Rate | **46.2%** | 44.8% | +1.4pp |
| Profit Factor | 1.57 | **1.62** | -3.1% |
| Max Drawdown | **21.6%** | 42.6% | **-49.2%** |
| Total Trades | **93** | 87 | +6.9% |
| Net PnL | 90.6% | **94.0%** | -3.6% |

## Overfitting Diagnostics (Researcher Bias Check)

| Metric | IS | OOS | Ratio (OOS/IS) | Assessment |
|--------|-----|-----|----------------|------------|
| Sharpe | 1.30 | 1.72 | 1.32 | OOS > IS (good) |
| Sortino | 1.77 | 1.93 | 1.09 | OOS > IS (good) |
| Win Rate | 47.2% | 46.2% | 0.98 | Near-perfect transfer |

## Hard Constraints Check (all evaluated on OOS)

| Constraint | Value | Threshold | Pass |
|-----------|-------|-----------|------|
| Max Drawdown | 21.6% | ≤ 51.1% (42.6%×1.2) | **PASS** |
| Min OOS Trades | 93 | ≥ 50 | **PASS** |
| Profit Factor | 1.57 | > 1.0 | **PASS** |
| Max Symbol PnL % | 68.7% (ETH) | ≤ 30% | FAIL (2-sym waived) |
| IS/OOS Sharpe Ratio | 1.32 | > 0.5 | **PASS** |

All hard constraints pass. The single-symbol constraint is structurally impossible with 2 symbols (waived per baseline notes).

## Per-Symbol Performance (OOS)

| Symbol | Trades | WR | Net PnL | % of Total |
|--------|--------|-----|---------|------------|
| ETHUSDT | 49 | 44.9% | +62.2% | 68.7% |
| BTCUSDT | 44 | 47.7% | +28.4% | 31.3% |

Improvement: ETH concentration dropped from 91.6% → 68.7% (better balance).

## What Worked

1. **OOS MaxDD halved: 21.6% vs 42.6%.** This is the biggest risk improvement in 76 iterations. The ATR-aligned labeling produces more conservative trades during quiet markets (when barriers are tight), preventing the model from taking overconfident positions.

2. **IS metrics improved across the board.** Sharpe +6.5%, WR +3.8pp, MaxDD -4.3pp. The model learns the actual risk/reward better when labels match execution.

3. **Win rate improved in both IS and OOS.** 47.2% vs 43.4% (IS), 46.2% vs 44.8% (OOS). The model makes better directional predictions when trained on realistic barriers.

4. **Better symbol balance.** ETH PnL concentration dropped from 91.6% to 68.7%.

5. **More OOS trades.** 93 vs 87 — the strategy is slightly more active.

## What Failed

1. **OOS Sharpe lower: +1.72 vs +1.84.** The primary metric is not beaten despite IS improvements. The OOS net PnL is 90.6% vs 94.0% — very close, but the PnL distribution has lower mean per trade.

2. **IS net PnL lower: 241.2% vs 264.3%.** Fewer IS trades (307 vs 373) and smaller average PnL per trade. The aligned labeling produces fewer but better-quality trades, but loses some total PnL volume.

## Overfitting Assessment

The OOS/IS Sharpe ratio of 1.32 is excellent — no sign of researcher overfitting. The strategy generalizes well. The issue isn't overfitting but rather that the aligned labeling trades slightly less aggressively, which reduces total PnL despite better win rate and lower risk.

## Quantitative Gap

- OOS Sharpe: 1.72 vs target 1.84 — gap: 0.12 (7%)
- OOS PF: 1.57 vs target 1.62 — gap: 0.05 (3%)
- The gap is small and could be closed with parameter tuning

## lgbm.py Code Review

1. **ATR-aligned labeling implementation is clean** — uses existing `load_features_range()` and `label_trades()` ATR mode
2. **Potential optimization**: The NATR loading in `_train_for_month()` creates a full-length ATR array each month. Could cache across months when training windows overlap.
3. **No bugs found** in the new code path

## Research Checklist Completed

| Category | Finding | Impact |
|----------|---------|--------|
| A. Feature Contribution | Volatility 52%, statistical 24%, mean_reversion 16%. Momentum 7%, trend 0.5% | Model trades vol patterns, not trend |
| C. Labeling | 19.4% flip rate, timeouts 68% profitable, prediction smoothing counter-productive | Disproved iter 075 idea #1 |
| E. Trade Patterns | SHORT 46.5% WR vs LONG 40.9%; 51.2% SL rate | Direction asymmetry confirmed |
| F. Statistical Rigor | Sharpe CI [0.025, 0.222]; WR p=3.1e-05 vs break-even | Signal is real |

## Exploration/Exploitation Tracker

Last 10 (iters 067-076): [E, E, X, E, E, E, E, X, X, **E**]
Exploration rate: 7/10 = 70%
Type: **EXPLORATION** (new labeling approach — dynamic ATR barriers)

## Next Iteration Ideas

1. **EXPLOITATION: Combine ATR-aligned labeling with baseline parameters** — The ATR labeling improved IS and halved OOS MaxDD. The Sharpe gap is only 7%. Try adjusting ATR multipliers (TP=3.0/SL=1.5 or TP=2.8/SL=1.4) to find the sweet spot between the baseline and iter 076.

2. **EXPLORATION: Regression target** — Predict forward return magnitude instead of direction. This is the most fundamental unexplored change. ATR-aligned labeling showed that better label-execution alignment helps — regression takes this further by removing discretization entirely.

3. **EXPLOITATION: ATR-aligned labeling + slightly wider barriers** — The ATR labeling produces tighter average barriers (median TP=8.05% vs fixed 8%). Using TP_mult=3.2/SL_mult=1.6 would widen the median barriers, potentially recovering the PnL lost from fewer trades while keeping the MaxDD benefit.

## Lessons Learned

1. **Label-execution alignment matters.** Even though the median barriers were similar (8.05% vs 8%), aligning them per-candle improved IS metrics and halved OOS MaxDD. The model learns volatility-appropriate risk/reward.

2. **MaxDD and Sharpe can diverge.** Iter 076 dramatically improved risk (MaxDD -49%) but slightly reduced return (Sharpe -7%). Risk-adjusted returns improved by some measures (Calmar improved in IS) but not the primary metric.

3. **The OOS Sharpe gap is small (7%).** This suggests ATR-aligned labeling is a valid approach that needs tuning, not abandonment. A wider barrier multiplier might close the gap.

4. **Prediction smoothing is invalid.** The research found that model direction flips (12-17% rate) are actually BETTER signals than consistent predictions, especially for ETH (58.8% WR on flips vs 41.6% on consistent). This insight prevents a wasted iteration.
