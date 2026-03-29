# Iteration 080 — Research Brief

**Type**: EXPLORATION (labeling paradigm change: binary → ternary classification)
**Date**: 2026-03-29
**Baseline**: Iteration 068 (OOS Sharpe +1.84)

## Section 0: Data Split

- OOS cutoff: **2025-03-24** (fixed, never changes)
- Walk-forward runs on full dataset; reporting layer splits at cutoff

## Section 1: Hypothesis

**Ternary classification (long/neutral/short) will improve signal quality by removing noisy labels from training data.** Currently, timeout candles with near-zero returns are force-labeled long or short by return sign, adding noise. With ternary, these become "neutral" — the model no longer learns from ambiguous examples.

### Evidence from IS data analysis:
- 7.0% of candles reach timeout (649/9,222)
- Of timeouts, 80.6% have |return| < 2% (mean 1.24%, median 1.13%)
- At threshold |return| < 2%: 5.7% of all candles become neutral (523 candles)
- These are the hardest candles to classify — removing them cleans the training signal

### Mechanism:
1. During labeling: timeout candles with |return| < `neutral_threshold` → label = 0 (neutral)
2. LightGBM `objective="multiclass"` with 3 classes
3. At inference: neutral prediction → NO_SIGNAL, long/short with confidence > threshold → trade
4. Optuna still optimizes Sharpe on non-neutral predictions only

## Section 2: Research Analysis (4 categories)

### A. Feature Contribution
Same 106 features as baseline. No feature changes — isolating the labeling variable.

### C. Labeling Analysis
**IS label distribution (current binary):**
- TP long: 403 (4.4%), TP short: 536 (5.8%)
- SL: 7,625 (82.7%)
- Timeout: 649 (7.0%), of which 80.6% have |return| < 2%

**Proposed ternary distribution (neutral_threshold=2.0%):**
- Long: ~47% → ~44% (some timeouts removed)
- Short: ~53% → ~50% (some timeouts removed)
- Neutral: 0% → **5.7%**

Label flip rate for timeout candles: these are the noisiest labels. A candle that times out with +0.1% return is labeled "long" but has no meaningful directional signal. Removing these should reduce flip rate at transition boundaries.

### E. Trade Pattern Analysis (reused from iter 078)
- Baseline IS: 373 trades, WR 43.4%, PF 1.35, Sharpe +1.22
- TP 32.2%, SL 51.2%, timeout 16.6%
- Timeout trades: 67.7% profitable with avg +1.64%
- Key: 16.6% of baseline TRADES are timeout exits. These trades generated +1.64% avg PnL — the model already handles some timeouts well. The ternary change affects TRAINING labels, not trade execution.

### F. Statistical Rigor (reused from iter 078)
- Bootstrap WR 95% CI: [38.6%, 48.5%]
- Binomial p-value: 0.000031 (signal is real)
- Signal exists but is noisy. Removing the noisiest 5.7% of training labels could tighten the CI.

## Section 3: Proposed Changes

### Change 1: Ternary labeling in `labeling.py`

Add `neutral_threshold_pct` parameter (default: None = binary mode). When set:
- Timeout candles with |forward_return| < `neutral_threshold_pct` → label = 0
- All other labels unchanged (TP long → +1, TP short → -1, SL → by direction)

### Change 2: Multiclass support in `optimization.py`

- LGBMClassifier with `objective="multiclass"`, `num_class=3`
- Classes: 0=short, 1=neutral, 2=long (LightGBM multiclass requires 0-indexed)
- Sharpe computation: only on non-neutral predictions
- `predict_proba` returns 3 probabilities; take max of long/short, ignore neutral

### Change 3: Signal generation in `lgbm.py`

- If model's argmax is neutral → NO_SIGNAL
- If model's argmax is long/short and confidence > threshold → trade
- Confidence = max(P(long), P(short)), ignoring P(neutral)

### Configuration

```python
strategy = LightGbmStrategy(
    training_months=24,
    n_trials=50,
    cv_splits=5,
    label_tp_pct=8.0,
    label_sl_pct=4.0,
    label_timeout_minutes=10080,
    fee_pct=0.1,
    seed=42,
    verbose=1,
    atr_tp_multiplier=2.9,
    atr_sl_multiplier=1.45,
    ensemble_seeds=[42, 123, 789],
    neutral_threshold_pct=2.0,  # NEW: timeout |return| < 2% → neutral
)
```

## Section 4: Expected Outcome

- Fewer but cleaner training labels → better model generalization
- WR should improve (noisy labels removed from training)
- Trade count may decrease (model more selective)
- Risk: neutral class too small (5.7%) → model rarely predicts neutral → no benefit
- Risk: multiclass overhead degrades model quality
