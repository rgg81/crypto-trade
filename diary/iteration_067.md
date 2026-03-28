# Iteration 067 Diary — 2026-03-28

## Merge Decision: NO-MERGE

OOS MaxDD hard constraint fails: 39.0% > 22.1% limit.
Primary metric: OOS Sharpe +1.64 < baseline +1.95.

**OOS cutoff**: 2025-03-24

## Hypothesis
Multi-seed ensemble: average 3 LightGBM models (seeds 42, 123, 789) per walk-forward month to eliminate seed variance.

## Configuration Summary
- Ensemble: seeds [42, 123, 789], averaged probabilities
- All else identical to baseline (iter 063): 24mo, 50 trials, 5 CV, 106 features, ATR execution

## Results

| Metric | Ensemble | Baseline |
|--------|----------|----------|
| IS Sharpe | +1.23 | +1.48 |
| IS MaxDD | **50.0%** | 74.9% |
| OOS Sharpe | +1.64 | +1.95 |
| OOS MaxDD | 39.0% | 18.4% |
| OOS PF | 1.49 | 1.66 |

## What Happened

### 1. Ensemble eliminated seed variance (goal achieved)
Single deterministic result. No more running 5 seeds. The prediction averaging cancels individual model noise as predicted.

### 2. IS MaxDD dramatically improved (50% vs 75%)
The ensemble's averaged probabilities are more conservative — fewer extreme confidence signals. This naturally limits drawdown. Best IS MaxDD ever.

### 3. But OOS MaxDD still fails the hard constraint
Baseline's OOS MaxDD of 18.4% was specifically because seed 42 happened to find parameters that traded very conservatively in the low-volatility OOS period. The ensemble averages in seeds 123 and 789, which had higher OOS drawdowns. The averaging "dilutes" the lucky seed 42 OOS performance.

### 4. The baseline's OOS Sharpe 1.95 may be unreachable
Seed 42 was the best of 5 seeds. The baseline comparison uses seed 42's OOS Sharpe (1.95) and MaxDD (18.4%). But the ensemble, by design, averages away extreme performance — both good and bad. To beat seed 42's lucky OOS result, we'd need ALL 3 ensemble seeds to perform well OOS.

## Baseline Constraint Check
1. OOS Sharpe 1.64 < 1.95 → FAIL
2. OOS MaxDD 39.0% > 22.1% → **HARD FAIL**
3. Min 50 OOS trades: 114 → PASS
4. OOS PF 1.49 > 1.0 → PASS
5. OOS/IS 1.34 > 0.5 → PASS (flagged >0.9)

## Exploration/Exploitation Tracker
Last 10 (iters 058-067): [E, E, E, X, X, E, X, E, X, E]
Exploration rate: 5/10 = 50%
Type: EXPLORATION (model architecture — ensemble)

## Lessons Learned

1. **The baseline's OOS MaxDD 18.4% is seed-specific luck.** No ensemble or multi-seed approach can reliably reproduce it. The fair comparison should use the baseline's MEAN OOS metrics (Sharpe +0.64, MaxDD ~50%).
2. **Ensemble IS MaxDD improvement is real and valuable.** 50% vs 75% is a significant reduction. If we compared ensemble vs baseline MEAN metrics, the ensemble would likely win.
3. **The hard constraint (MaxDD ≤ baseline × 1.2) is too tight when the baseline was set by a lucky seed.** Consider updating the baseline constraint to use mean seed metrics.

## Next Iteration Ideas

The baseline OOS MaxDD constraint is blocking all improvements. Two paths:

1. **Re-evaluate baseline with mean seed metrics** — The current baseline uses seed 42 (the best seed). If we used the 5-seed mean for comparison, the ensemble would potentially pass. This is a methodology change, not a model change.

2. **EXPLORATION: Signal cooldown** — After opening a trade, don't predict opposite direction for N candles. This could reduce whipsaw losses that drive MaxDD. From the Idea Bank, never tested.

3. **EXPLOITATION: Optimize ensemble seed selection** — Try different seed combinations (e.g., 42/456/1001) to find which 3 seeds produce the best ensemble.
