# Research Brief — Iteration 104

**Type**: EXPLORATION
**Hypothesis**: Requiring ≥4/5 ensemble models to agree on direction filters out low-conviction signals without the overfitting risk of meta-labeling.

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Section 1: Problem Statement

After 10 consecutive NO-MERGE (094-103), every approach that reduces trade count triggers early stop (meta-labeling, per-symbol, pruning). The baseline's strength IS its 346 IS trades — enough for 2:1 RR to converge.

The 5-seed ensemble currently averages probabilities. If 3 models say long and 2 say short, the average might be 0.52 → trades long. But this is a split-decision trade with low conviction.

**Ensemble disagreement filter**: Only trade when ≥4 out of 5 models agree on the predicted direction. This uses information already computed (per-model predictions) without any additional model, feature, or training change.

## Section 2: Research Analysis

### E. Trade Pattern Analysis
The baseline trades on averaged ensemble probabilities. Trades where models disagree are inherently lower-conviction because the direction depends on 1-2 models' random seed sensitivity.

### F. Statistical Rigor
The ensemble disagreement filter is NOT learned from data — it's a deterministic rule based on model agreement. Unlike meta-labeling (which overfits to OOF patterns), this filter cannot overfit because it has zero trainable parameters.

### A. Feature Contribution
No feature changes. The same 185 features, same models, same optimization. Only inference-time filtering changes.

### H. Overfitting Audit
This is the least overfit-prone change possible: zero parameters, zero training, zero data dependency. The 4/5 agreement threshold is a fixed rule, not optimized.

## Section 3: Proposed Change

Add `min_ensemble_agreement: int = 0` parameter to `LightGbmStrategy`. When set to 4 (or 5), require that many models to agree on direction before trading.

Implementation (~10 lines in get_signal()):
1. After computing per-model predictions, count how many agree with the averaged direction
2. If agreement count < min_ensemble_agreement: skip

**Expected trade count reduction**: ~15-25% (a guess — models agree most of the time since they share the same training data, differ only by seed). This is much less aggressive than meta-labeling's 66-98% reduction.

## Section 4: Risk Assessment

**Downside**: If models mostly agree (>95% of the time), the filter has minimal effect. The 5 seeds share the same training data — they differ only in random initialization, sampling, and split randomness.

**Upside**: If disagreement signals low-quality predictions, the filter selectively removes the worst trades with zero overfitting risk.
