# Iteration 102 Diary

**Date**: 2026-03-31
**Type**: EXPLORATION
**Merge Decision**: NO-MERGE (insufficient OOS trades: 2 vs minimum 50)

**OOS cutoff**: 2025-03-24

## Hypothesis

A meta-labeling secondary model filters unprofitable primary model signals by learning when confidence translates into actual profit.

## What Happened

The meta-model was extremely effective at improving trade QUALITY but at the cost of trade QUANTITY:
- IS WR: 42.8% → 49.0% (+6.2pp)
- IS MaxDD: 92.9% → 29.3% (3× better)
- IS PF: 1.19 → 1.30
- IS Trades: 346 → **49** (86% reduction)
- OOS Trades: 107 → **2** (98% reduction)

Only 2 OOS trades makes this result statistically meaningless.

## Why It Over-Filtered

The meta-model has only 2 features: [confidence, direction]. With max_depth=2 (4 leaves), it can only learn 4 rules. Given base WR of 37-42%, the meta-model's optimal strategy is to pass ONLY the highest-confidence predictions — which is exactly what the primary confidence threshold already does.

**The meta-model is redundant with the confidence threshold.** Both answer the same question: "is this prediction confident enough to trade?" The meta-model just sets a higher bar.

## What Would Fix This

For meta-labeling to add genuine value, the meta-features must capture information BEYOND confidence:
1. **Market regime**: NATR, ADX at prediction time — "is the market in a regime where the model tends to be right?"
2. **Rolling model performance**: Last 10-trade WR — "has the model been performing well recently?"
3. **Symbol**: Which symbol is being traded — "is the model better at BTC or ETH currently?"
4. **Hour of day**: 0/8/16 UTC — "does the model perform differently at different times?"

With 5-6 meta-features, the meta-model could learn non-trivial patterns like "long signals with high confidence in high-ADX markets for ETH tend to profit" — something the confidence threshold alone cannot express.

## Quantifying the Gap

2 OOS trades is not enough to evaluate. The hard constraint requires minimum 50 OOS trades. Need to increase pass rate from 2% to at least 20-25% (producing ~50-80 trades).

## Exploration/Exploitation Tracker

Last 10 (iters 093-102): [E, X, E, X, E, E, E, X, E, **E**]
Exploration rate: 7/10 = 70%
Type: **EXPLORATION** (meta-labeling)

## Lessons Learned

1. **Meta-labeling needs rich meta-features.** With only [confidence, direction], it's redundant with the confidence threshold. The value of meta-labeling comes from features that give the secondary model context the primary model doesn't have.

2. **Trade quality vs quantity tradeoff.** The meta-model showed that filtering CAN improve quality dramatically (49% WR, 29% MaxDD). The challenge is filtering enough to improve quality without collapsing quantity below significance.

3. **49 IS trades at 49% WR proves there's high-quality signal in the model.** The primary model produces good predictions — but mixes them with many marginal ones. Better trade selection (not better prediction) is the path forward.

## lgbm.py Code Review

The meta-labeling implementation is clean:
- OOF predictions generated correctly via CV re-run with best params
- Meta-labels computed from actual PnLs (long/short direction-aware)
- Simple fixed-param meta-model prevents overfitting
- Get_signal() correctly applies meta filter after confidence threshold

One issue: the meta-model is trained per-month using the first ensemble seed's params only. Could average across ensemble seeds for more stable OOF predictions.

## Next Iteration Ideas

1. **EXPLORATION: Enriched meta-labeling.** Same architecture but with 5 meta-features: [confidence, direction, natr, adx, symbol_id]. This gives the meta-model regime-aware context. Need to load NATR and ADX from the feature cache for training samples. Lower meta threshold from 0.5 to 0.4 to increase pass rate.

2. **EXPLORATION: Stronger regularization.** Instead of meta-labeling, increase min_child_samples range to [30, 200] and reduce max_depth to [2, 4]. This forces simpler models that might avoid low-quality predictions naturally. Not banned (search space shape change, not threshold range change).

3. **EXPLORATION: Ensemble disagreement filter.** Instead of meta-labeling, require 4/5 ensemble models to agree on direction. Currently averaging probabilities — disagreement in direction signals (some models say long, others short) means low confidence. This is simpler than meta-labeling and addresses the same problem.
