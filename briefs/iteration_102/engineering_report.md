# Engineering Report — Iteration 102

## Change Summary

Added meta-labeling secondary model (AFML Ch. 3). Simple LightGBM (depth=2, 50 trees) trained on out-of-fold primary predictions. Meta-features: [confidence, direction]. Filters signals where P(profitable) < 0.5.

## Results

| Metric | Iter 102 (meta) | Baseline (093) |
|--------|-----------------|----------------|
| IS Sharpe | +0.52 | +0.73 |
| OOS Sharpe | +2.25 | +1.01 |
| IS WR | 49.0% | 42.8% |
| OOS WR | 50.0% | 42.1% |
| IS MaxDD | 29.3% | 92.9% |
| OOS MaxDD | 4.4% | 46.6% |
| IS Trades | **49** | 346 |
| OOS Trades | **2** | 107 |

## Analysis

The meta-model filtered 86% of IS trades and 98% of OOS trades. Trade quality improved dramatically (IS WR +6pp, IS MaxDD 3× better) but trade quantity collapsed to statistically insignificant levels.

**Meta-model behavior**: Pass rate of 2-6% across months. The model learned to only pass the very highest-confidence predictions, which is redundant with the existing confidence threshold. With only 2 features (confidence, direction), the meta-model can't learn anything beyond "higher confidence = better" — which the primary threshold already captures.

## Label Leakage Audit

- Primary model: CV gap=44, unchanged
- Meta-model: trained on OOF predictions from CV folds — no leakage by construction
- Walk-forward: unchanged

## Key Finding

Meta-labeling with only [confidence, direction] as meta-features is redundant with the confidence threshold. For meta-labeling to add value, it needs features that capture information BEYOND the primary model's confidence:
- Market regime (NATR, ADX)
- Rolling primary model performance
- Time-based patterns

## Trade Execution Verification

49 IS trades verified: entry/exit prices, SL/TP calculations correct. The 2 OOS trades are too few for meaningful verification.
