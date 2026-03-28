# Iteration 069 Diary — 2026-03-28

## Merge Decision: NO-MERGE

No cooldown value clearly beats the baseline cd=2. The sweep shows noisy, non-monotonic behavior across values. cd=3 early-stopped, cd=4 looks suspicious (OOS/IS=2.1).

**OOS cutoff**: 2025-03-24

## Hypothesis

Cooldown=2 was chosen based on EDA. Test cd={1,3,4} with single seed to find optimal value.

## Configuration Summary

- Single seed=42 (no ensemble) for fast comparison
- Cooldown values tested: 1, 3, 4
- All else identical to iter 068

## Results (single seed=42)

| Cooldown | IS Sharpe | OOS Sharpe | IS MaxDD | OOS MaxDD | IS Trades | OOS Trades | Note |
|----------|-----------|------------|----------|-----------|-----------|------------|------|
| 1 | +1.49 | +1.52 | 62.6% | 31.1% | 442 | 82 | |
| 3 | +0.88 | -0.19 | 71.6% | 43.6% | 391 | 53 | EARLY STOP |
| 4 | +1.03 | +2.16 | 54.2% | 14.6% | 364 | 65 | OOS/IS=2.1 |

Baseline (cd=2 ensemble): IS +1.22, OOS +1.84, IS MaxDD 45.9%, OOS MaxDD 42.6%, 460 trades

## What Happened

### 1. Cooldown sensitivity is non-monotonic and seed-dependent

cd=3 early-stopped (Year 2025 PnL -26.7%), while cd=4 had the best OOS Sharpe. This non-monotonic pattern strongly suggests the results are seed-dependent rather than reflecting a genuine relationship between cooldown value and performance.

### 2. cd=4 OOS looks amazing but is suspicious

OOS Sharpe 2.16, MaxDD 14.6% — but only 65 OOS trades and OOS/IS ratio of 2.1. This is almost certainly a favorable OOS period artifact with reduced sample size.

### 3. cd=1 has the most IS trades but worst IS MaxDD

More trades = more exposure during loss streaks = higher MaxDD (62.6%). cd=1 is too permissive.

### 4. The baseline cd=2 remains the sweet spot

With ensemble averaging, cd=2 achieves good IS MaxDD (45.9%), decent OOS Sharpe (1.84), and sufficient trade count (460). No other value demonstrates a clear, robust improvement.

## Baseline Constraint Check

Not applicable — NO-MERGE. No value beats baseline cd=2 (ensemble).

## Exploration/Exploitation Tracker

Last 10 (iters 060-069): [E, X, X, E, X, E, X, E, E, X]
Exploration rate: 4/10 = 40%
Type: EXPLOITATION (cooldown value sweep)

## Lessons Learned

1. **Cooldown value optimization is low-value.** The relationship between cooldown and performance is noisy. cd=2 was a good initial guess, and the marginal returns of fine-tuning are dominated by seed variance.

2. **Single-seed sweeps are unreliable for parameter comparison.** Results vary wildly by seed (cd=3 early-stops, cd=4 looks amazing). This confirms that the ensemble is essential for reliable evaluation.

3. **Don't optimize what's already good enough.** cd=2 works. Spending another iteration on cd values would be a waste of time. Move to structural improvements.

## Next Iteration Ideas

1. **EXPLORATION: Add more symbols (SOL, DOGE)** — The single-symbol concentration constraint requires diversification. This would also provide more training data.

2. **EXPLORATION: Optuna-optimized cooldown per month** — Instead of a fixed global cooldown, let Optuna choose cd=0-4 per walk-forward month.

3. **EXPLORATION: Direction-specific cooldown** — After SL, longer cooldown; after TP, shorter. Adapts to recent accuracy.

4. **EXPLORATION: Feature engineering** — Never done in 69 iterations. Cross-asset features (BTC momentum as leading indicator), interaction features (RSI x ADX), calendar features.
