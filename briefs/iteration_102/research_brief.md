# Research Brief — Iteration 102

**Type**: EXPLORATION
**Hypothesis**: A secondary meta-labeling model (AFML Ch. 3) can filter out unprofitable signals from the primary model by learning when the primary model's confidence translates into actual profit.

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Section 1: Problem Statement

The primary model generates signals with a single confidence threshold. But not all high-confidence predictions are equally profitable — BTC longs at 28% OOS WR vs ETH longs at 56.5%. A meta-labeling model learns WHEN the primary model's signals translate into profit, providing a second layer of filtering.

## Section 2: Meta-Labeling Architecture

**Primary model**: Unchanged baseline LightGBM (5-seed ensemble, 185 features)
**Secondary model**: Simple LightGBM (max_depth=2, 50 trees, no Optuna)

**Training flow (each month):**
1. Train primary model via Optuna (unchanged)
2. Generate out-of-fold (OOF) predictions using primary model's best params + CV folds
3. Create meta-labels: for each OOF prediction, did the predicted direction's trade actually profit? (1=yes, 0=no)
4. Create meta-features: [confidence, direction]
5. Train simple meta-model on (meta-features, meta-labels)

**Inference flow:**
1. Primary model predicts direction + confidence (unchanged)
2. If confidence < threshold: SKIP (unchanged)
3. Meta-model predicts P(profitable) from [confidence, direction]
4. If P(profitable) < 0.5: SKIP (new filter)
5. Otherwise: trade

## Section 3: Research Analysis (Categories A, E, F)

**A (Features)**: Meta-features are derived from the primary model's output, not from raw data. They capture the model's self-assessment quality — information unavailable to the primary model itself.

**E (Trade Patterns)**: The meta-model learns patterns like "the primary model's long signals at confidence 0.55-0.60 rarely profit" or "short signals at high confidence are almost always right." This is a learned, adaptive version of the direction-conditional filtering identified in iter 099 analysis.

**F (Statistical Rigor)**: The meta-model is intentionally simple (2 features, max_depth=2, 4 leaves) to prevent overfitting. It can only learn 4 different trade filtering rules — enough to capture directional asymmetry without memorizing noise.

## Section 4: What Stays the Same

All primary model params identical to baseline iter 093. The meta-model only FILTERS signals — it never generates them. The primary model's training is completely unchanged.
