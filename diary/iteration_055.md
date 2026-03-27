# Iteration 055 — EXPLOITATION (seed-validate balanced class weights)

## NO-MERGE: Mean OOS Sharpe -0.22 (3/5 profitable). Balanced weights hurt OOS, not help. Iter 050's +1.66 was a baseline fluke, not balanced weights.

**OOS cutoff**: 2025-03-24

## Results (5-seed validation)

| Seed | IS Sharpe | OOS Sharpe | OOS WR | OOS PF | OOS Trades | OOS PnL |
|------|-----------|------------|--------|--------|------------|---------|
| 42   | +1.86     | +0.10      | 40.0%  | 1.02   | 170        | +6.8%   |
| 123  | +1.65     | -1.94      | 32.3%  | 0.73   | 130        | -89.1%  |
| 456  | +1.19     | +0.77      | 40.7%  | 1.15   | 150        | +50.3%  |
| 789  | +1.09     | +0.53      | 41.7%  | 1.12   | 115        | +30.4%  |
| 1001 | +1.32     | -0.56      | 36.8%  | 0.91   | 133        | -28.1%  |

**IS**: mean +1.42 (std 0.29), 5/5 positive
**OOS**: mean -0.22 (std 0.97), 3/5 positive
**Verdict**: FAIL (need mean > 0 AND ≥ 4/5 profitable)

## What Happened

### 1. Balanced class weights degrade OOS

Compared to baseline 047 seed validation:

| Metric | Baseline 047 | Iter 055 (balanced) |
|--------|-------------|---------------------|
| Mean IS Sharpe | +1.38 | +1.42 (+0.04) |
| Mean OOS Sharpe | +0.41 | -0.22 (-0.63) |
| OOS Profitable | 3/5 | 3/5 |

Balanced weights slightly improve IS (+0.04) but significantly hurt OOS (-0.63). Classic overfitting: the model fits training data better but generalizes worse. The balanced weighting changes the loss landscape in a way that captures IS-specific patterns rather than robust signals.

### 2. Iter 050's OOS +1.66 was NOT from balanced weights

The QE discovered that `git diff main..iteration/050 -- src/` shows NO code changes. The iteration/050 branch was identical to main — balanced weights were never applied. Iter 050 was just a re-run of the baseline configuration with seed=42, and the OOS +1.66 was a lucky Optuna run.

This explains the massive discrepancy: iter 050 seed=42 got +1.66, but iter 055 seed=42 (with actual balanced weights) got +0.10. The +1.66 came from different Optuna outcomes, not from balanced weights.

### 3. Per-symbol OOS is chaotic

No consistent per-symbol pattern across seeds. BTC and ETH trade dominance randomly. In 3/5 seeds, one symbol is significantly negative while the other carries the portfolio. This is inherent seed variance, not a fixable problem.

## Quantifying the Gap

- OOS WR ranges from 32.3% to 41.7% across seeds (break-even = 34.2%)
- Mean OOS WR = 38.3% → +4.1 pp above break-even
- IS WR consistently 42.8-45.3% → +8.6 pp above break-even
- Gap between IS and OOS WR: ~4.5 pp of degradation
- The model has real signal (IS is statistically significant: p = 0.000015), but OOS degradation + high seed variance makes it unreliable

## Decision: NO-MERGE

Both criteria failed:
1. Mean OOS Sharpe -0.22 ≤ 0
2. Only 3/5 profitable (need ≥ 4)

Balanced class weights are a dead end. The IS improvement is real but comes at the cost of OOS generalization.

## lgbm.py Code Review

Reviewed lgbm.py and optimization.py. No bugs found. Key observation: `is_unbalance=True` is already set in LightGBM params alongside the new `_balance_weights()`. These two mechanisms are partially redundant — `is_unbalance` adjusts the loss function internally, while `_balance_weights` rescales sample weights externally. Using both together may over-correct. However, removing `is_unbalance` and using only `_balance_weights` would be a separate experiment.

## Research Checklist Completed

- **C (Labeling)**: Labels stable (23.8% flip rate), balanced long/short (46/54%), timeout trades 70% WR
- **E (Trade Patterns)**: Monthly IS analysis, per-symbol per-year all years profitable, exit reason breakdown (TP=32%, SL=52%, TO=16%)
- **F (Statistical Rigor)**: Bootstrap WR 95% CI [38.7%, 46.8%] excludes break-even (34.2%), binomial p = 0.000015, bootstrap PnL P(loss) = 0.6%
- **A (Features)**: 106 features unchanged — deferred to next exploration iteration

## Exploration/Exploitation Tracker

Last 10 (iters 046-055): [E, E, E, E, X, E, E, E, E, X]
Exploration rate: 8/10 = 80% — still heavily over-explored. Next iterations MUST be exploitation.

Note: Most "explorations" (049, 052-054) were symbol pair tests that are now conclusively exhausted. BTC+ETH is confirmed optimal.

## Next Iteration Ideas

The baseline 047 remains our best strategy. Future improvements should focus on the model itself, not the data/symbols.

1. **Remove `is_unbalance` and test baseline without it** (EXPLOITATION): The baseline uses `is_unbalance=True` — does it help or hurt? Test the same config with `is_unbalance=False` and no balanced weights. Clean comparison.

2. **Feature engineering — slow features** (EXPLORATION, HIGH PRIORITY): Use 3-4x lookback multiplier for daily-equivalent features on 8h candles (e.g., SMA_300 ≈ daily SMA_100). This is the #1 untested exploration from the idea bank. The current 106 features may be too noisy at short lookbacks.

3. **Interaction features** (EXPLORATION): RSI × ADX, volatility × trend strength. Could capture nonlinear relationships that trees miss as individual features.

4. **Prediction smoothing** (EXPLORATION): Majority vote of last 3 predictions before generating signal. Could reduce flip-flopping and improve consistency.

5. **ATR-dynamic barriers** (EXPLORATION): Scale TP/SL per-candle by recent volatility. Adapt to market conditions rather than fixed 8%/4%.
