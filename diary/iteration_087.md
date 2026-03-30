# Iteration 087 Diary — 2026-03-30

## Merge Decision: NO-MERGE

OOS Sharpe +0.57 vs baseline +1.84. OOS MaxDD 79.6% vs baseline 42.6%. Relaxed threshold increased trade count but catastrophically worsened drawdowns.

**OOS cutoff**: 2025-03-24

## Hypothesis

Ternary labeling (neutral class for ambiguous timeout candles) with a relaxed confidence threshold [0.34, 0.60] would increase trade count from iter 080's 73 while maintaining ternary's noise reduction benefits.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **Ternary labeling**: neutral_threshold_pct=2.0% (11.1% of labels → neutral)
- **Threshold range**: [0.34, 0.60] (was [0.50, 0.85] in baseline and iter 080)
- Features: 115 (global intersection)
- Model: LGBMClassifier multiclass, ensemble [42, 123, 789]
- Walk-forward: monthly, 24mo window, 5 CV folds, 50 Optuna trials
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45, cooldown=2

## Results: In-Sample

| Metric | Iter 087 | Baseline (068) | Iter 080 (ternary) |
|--------|----------|----------------|-------------------|
| Sharpe | +0.83 | +1.22 | +1.26 |
| WR | 42.4% | 43.4% | 44.6% |
| PF | 1.19 | 1.35 | 1.31 |
| MaxDD | **98.7%** | 45.9% | 56.1% |
| Trades | 469 | 373 | 314 |

## Results: Out-of-Sample

| Metric | Iter 087 | Baseline (068) | Iter 080 (ternary) |
|--------|----------|----------------|-------------------|
| Sharpe | +0.57 | +1.84 | +1.00 |
| WR | 40.0% | 44.8% | 45.2% |
| PF | 1.13 | 1.62 | 1.40 |
| MaxDD | **79.6%** | 42.6% | 33.4% |
| Trades | 130 | 87 | 73 |

## What Happened

**The relaxed threshold destroyed the ternary advantage.** Iter 080's success was that ternary + HIGH threshold ([0.50, 0.85]) created a double-filtered system: neutral class removed 11% of noisy labels, AND high confidence threshold further filtered uncertain predictions. Together they produced fewer but higher-quality trades.

By relaxing the threshold to [0.34, 0.60], I removed the second filter. The ternary model alone is not selective enough — it still predicts long/short for ~89% of candles. Without the confidence gate, the model takes 469 IS trades vs 314 in iter 080 (49% more), but these extra trades are the noisy ones that ternary's neutral class was supposed to filter.

**The best confidence thresholds selected by Optuna were ~0.42-0.50**, which is within the relaxed range but LOWER than the baseline's typical 0.60-0.85. The model chose to be less selective because the Optuna objective (Sharpe) rewards more trades at marginal accuracy.

## Quantifying the Gap

OOS WR: 40.0%, break-even 33.3%, gap +6.7pp above break-even (profitable on paper). OOS PF: 1.13 (weak but positive). But MaxDD 79.6% makes this strategy uninvestable — you'd lose nearly your entire account before recovering.

Compared to iter 080 (ternary, same threshold as baseline): WR 40.0% vs 45.2% (-5.2pp), MaxDD 79.6% vs 33.4% (2.4x worse). The relaxed threshold converted a good risk profile into a catastrophic one.

## Exploration/Exploitation Tracker

Last 10 (iters 078-087): [E, E, X, X, X(abandoned), E, E, E, E, **E**]
Exploration rate: 7/10 = 70%
Type: **EXPLORATION** (labeling paradigm change + signal selection change)

## Research Checklist

Completed: C (labeling — ternary reuse), E (trade pattern analysis — prediction flip analysis DISPROVED smoothing hypothesis, informing pivot to ternary). Referenced iter 086's categories A, D, F.

## lgbm.py Code Review

The `threshold_range` parameter works correctly — Optuna uses the specified range. The ternary multiclass code (cherry-picked from iter 080) works as expected. New finding: the `threshold_range` parameter is reusable infrastructure for future iterations.

## Lessons Learned

1. **Ternary's value is as a COMPLEMENT to high confidence threshold, not a replacement.** The neutral class removes ~11% of noisy labels, but the remaining 89% still need confidence filtering. Without it, the model takes too many low-quality trades.

2. **The confidence threshold range [0.50, 0.85] is load-bearing.** Iter 080 and the baseline both use this range and produce reasonable MaxDD. Relaxing it to [0.34, 0.60] let Optuna find locally-optimal but globally-catastrophic thresholds (~0.42) that maximize IS Sharpe via more trades but destroy risk management.

3. **Trade count and MaxDD are inversely correlated.** More trades → more overlapping drawdown periods → deeper total drawdown. The baseline's 373 IS trades with 45.9% MaxDD vs 469 trades with 98.7% MaxDD — each additional trade adds disproportionate risk because of trade clustering.

4. **The IS MaxDD of 98.7% should have been the first warning.** Future iterations: any IS MaxDD > 60% is a strong signal that OOS will also be catastrophic. This validates iter 083's observation that IS MaxDD is predictive of OOS quality (while iter 084 was the exception, not the rule).

## Next Iteration Ideas

**After 11 consecutive NO-MERGE (077-087), the evidence is overwhelming: the baseline configuration (iter 068) is a local optimum that single-variable changes cannot improve.**

1. **EXPLOITATION: Exact ternary reproduction (iter 080 config)** — Run iter 080's exact config (ternary + threshold [0.50, 0.85]) with the current 115-feature parquets to verify if ternary still produces the same results. If OOS Sharpe ≈ 1.00 and MaxDD ≈ 33.4%, it confirms ternary is the second-best known config.

2. **EXPLORATION: Ternary + higher threshold [0.60, 0.90]** — If the standard threshold is load-bearing, what about RAISING it even higher? This would create a triple-selective system: neutral labels + high threshold + cooldown. Fewer trades but potentially much better per-trade quality.

3. **EXPLORATION: Different loss function** — Instead of LightGBM's default cross-entropy, use a custom loss that penalizes large drawdowns. This directly optimizes for the metric we care about (risk-adjusted returns) rather than classification accuracy.

4. **EXPLORATION: Completely different approach** — After 87 iterations, consider whether the LightGBM + monthly walk-forward framework has been exhausted. The next leap may require a fundamentally different trading strategy (e.g., regime-based allocation, options-like payoffs, or a non-ML signal generation approach).
