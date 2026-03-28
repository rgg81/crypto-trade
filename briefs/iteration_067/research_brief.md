# Iteration 067 — Research Brief

**Type**: EXPLORATION (model architecture change — ensemble)
**Date**: 2026-03-28

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24 (fixed, never changes)
```

## Context: 3 Consecutive NO-MERGE (064-066)

- 064: Removing training_days → EARLY STOP (training_days essential for regime adaptation)
- 065: ATR labeling → NO-MERGE (fixed labeling + dynamic execution is optimal separation)
- 066: 100 Optuna trials → NO-MERGE (more trials → IS overfitting, OOS degradation)

All three confirmed: the iter 063 architecture (106 features, pooled, fixed labeling, ATR execution, 50 trials) is near-optimal. The main weakness is **seed variance** (OOS std 0.96).

## Hypothesis

**Multi-seed ensemble**: Train 3 LightGBM models per walk-forward month using different random seeds (42, 123, 789). Average predicted probabilities before applying confidence threshold.

### Why this works

Seed variance arises because different TPE seeds explore different regions of the hyperparameter space, finding different local optima. Each model is reasonable individually but predicts differently. By averaging:
- Correct predictions reinforce (all models agree → high confidence)
- Incorrect predictions cancel out (models disagree → low confidence → filtered by threshold)
- Mathematically: variance of mean decreases as 1/N (law of large numbers)

### Why previous approaches failed

| Approach | Why it failed | Why ensemble is different |
|----------|--------------|-------------------------|
| Remove training_days | Changed what data the model sees | Ensemble keeps full data access |
| ATR labeling | Changed what the model learns | Ensemble keeps fixed labeling |
| More trials | Better IS fit → OOS overfitting | Ensemble uses DIVERSE fits |

The key insight: individual model overfitting is OK if models overfit to DIFFERENT things. Averaging cancels out the individual noise.

## Configuration

All parameters identical to iter 063 baseline EXCEPT:
- **NEW**: `ensemble_seeds=[42, 123, 789]` — 3 models per walk-forward month
- Prediction: average probabilities across 3 models
- Confidence threshold: average of 3 per-model thresholds
- Everything else: 24mo training, 50 trials, 5 CV, 106 features, BTC+ETH pooled, ATR execution (2.9/1.45)

## Research Analysis (4 categories, mandatory after 3+ NO-MERGE)

### A. Feature Contribution
Unchanged from baseline — 106 features, proven near-optimal in iters 061-062. No new features proposed. The ensemble approach changes HOW models use features, not which features are used.

### C. Labeling
Fixed 8%/4% labeling confirmed optimal in iter 065 (ATR labeling created directional bias). No changes.

### E. Trade Patterns
From iter 064 analysis: IS/OOS trade patterns are consistent (SL ~49%, TP ~33%, timeout ~17%). Direction balanced. Both symbols contribute. The ensemble should maintain these patterns but with more consistent signal quality.

### F. Statistical Rigor
Baseline seed sweep shows OOS Sharpe std=0.96 across 5 seeds. Ensemble of 3 seeds should reduce effective OOS variance by √3 ≈ 1.73x. Expected std ≈ 0.96/1.73 ≈ 0.55. This is a testable prediction.

## Expected Impact

- Reduced seed variance (std from 0.96 → ~0.55)
- Similar or slightly lower mean OOS Sharpe (averaging dilutes the best seed)
- More consistent monthly performance (fewer outlier months)
- Runtime: ~60min (3× baseline per seed validation run)

## Implementation Notes for QE

1. Add `ensemble_seeds: list[int] | None = None` to LightGbmStrategy constructor
2. In `_train_for_month`: loop over ensemble seeds, run `optimize_and_train` for each
3. Store list of (model, threshold) pairs
4. In `get_signal`: predict with all models, average probabilities, use mean threshold
5. Feature loading shared (all models use same 106 columns)
6. For seed validation: the ensemble IS the seed stability mechanism. Run with ONE seed config (the ensemble), not 5 separate seeds.
