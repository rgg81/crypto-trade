# Iteration 085 Research Brief — Regression Labeling

**Type**: EXPLORATION
**Date**: 2026-03-30
**QR**: Claude (autopilot)

## Section 0: Data Split (verbatim, never changes)

- OOS cutoff date: **2025-03-24** (fixed for all iterations)
- IS period: all data before 2025-03-24
- OOS period: all data from 2025-03-24 onward
- The walk-forward backtest runs on ALL data (IS + OOS) as one continuous process
- Reports split at cutoff: `in_sample/` and `out_of_sample/`
- QR sees OOS for the first time in Phase 7

## Section 1: Motivation

After 8 consecutive NO-MERGE iterations (077-084), structural changes are mandatory. The current binary classification (long/short) approach has been exhausted — feature pruning (iter 084), feature expansion (iter 083), ternary labels (iters 080-082), per-symbol models (iters 078-079), and parameter tuning (iter 077) all failed.

The fundamental issue: **binary classification discards magnitude information.** Whether a candle leads to a +20% move or a +0.5% move, both get labeled "long." The model has no way to express conviction in the SIZE of the predicted move, only its direction. The confidence threshold is a proxy for magnitude but it's indirect — it measures model certainty about direction, not predicted return size.

**Regression labeling** directly predicts the "direction value" — how much better long is vs short (long_pnl - short_pnl). This gives the model continuous targets that capture both direction AND magnitude.

## Section 2: Research Analysis

Completed **4 categories** from the Research Checklist (required: 4+ after 3+ NO-MERGE):

### C: Labeling Analysis (PRIMARY — this is the change)

**Current binary labeling**: For each candle, label = 1 (long) if long TP hits first, -1 (short) otherwise.

**Forward return analysis (IS, 7d horizon)**:
- BTC: 55.9% of candles have >=8% max move (TP-level), 34.5% have 4-8% (SL-level), 9.6% stay < 4%
- ETH: 71.0% TP-level, 25.4% SL-level, 3.6% small
- The labels are not very noisy — most candles resolve to TP or SL

**But magnitude varies hugely**:
- BTC 7d forward returns: mean +0.43%, std 5.0%, range roughly -30% to +40%
- ETH 7d forward returns: mean +0.54%, std 6.4%
- The binary label treats a +0.5% timeout and a +20% TP hit identically as "long"

**Proposed regression target**: `direction_value = long_pnl - short_pnl` (net of fees)
- If long much better: direction_value >> 0 (e.g., +15% when long hits TP, short hits SL)
- If short much better: direction_value << 0
- If ambiguous: direction_value ≈ 0 (timeout with tiny return)
- This target is already computed by `label_trades()` — no labeling code changes needed

**Trade decision from regression prediction**:
- If prediction > threshold → go LONG
- If prediction < -threshold → go SHORT
- If |prediction| ≤ threshold → no trade
- Optuna tunes the threshold (replaces confidence threshold)

**Why this might work**: The model can learn WHEN to predict large moves (high conviction) vs small moves (skip). Binary classification forces the model to always pick a direction; regression lets it say "I don't know" by predicting ≈0.

### A: Feature Analysis

**Using baseline's 106 features** (global intersection). Iter 084 showed that feature changes (both pruning and expansion) degrade performance. The feature set is NOT the bottleneck — the learning objective is. This iteration changes ONLY the labeling paradigm.

### E: Trade Pattern Analysis

From baseline IS trades:
- 43.4% WR with TP=8%/SL=4% → 2:1 reward ratio means PF > 1 at 33.3% break-even
- BTC IS: 48.0% WR (strong) vs ETH IS: 40.4% WR (weaker but profitable)
- Exit reason distribution is critical for regression: TP exits should map to high |direction_value|, timeout exits should map to low |direction_value|

### F: Statistical Rigor

**The regression target has favorable properties**:
- It's bounded (by TP/SL barriers) — no extreme outliers
- It's approximately symmetric (long and short can both hit TP/SL)
- Mean is slightly positive (IS data has slight long bias) — but not enough to cause issues
- The target preserves the Sharpe-optimizing objective: the optimizer still maximizes Sharpe from actual trade PnLs, just using regression predictions instead of classification probabilities

## Section 3: Configuration

### What Changes (vs baseline iter 068)
| Parameter | Baseline (068) | This iteration |
|-----------|---------------|----------------|
| Model type | LGBMClassifier (binary) | **LGBMRegressor** |
| Label | Binary {-1, 1} | **Continuous: long_pnl - short_pnl** |
| Confidence filter | P(class) > threshold | **|prediction| > threshold** |
| Threshold range | [0.50, 0.85] | **[0.0, 15.0] (pnl units)** |

### What Stays the Same
- Features: 106 (global intersection — baseline behavior, no symbol-scoped)
- Symbols: BTCUSDT + ETHUSDT (pooled)
- Labeling barriers: TP=8%, SL=4%, timeout=7 days (for computing long/short PnLs)
- Training: 24 months, 5 CV folds, 50 Optuna trials
- Ensemble: 3 seeds [42, 123, 789]
- Execution: Dynamic ATR barriers TP=2.9×NATR_21, SL=1.45×NATR_21
- Signal cooldown: 2 candles

### Implementation Notes for QE

1. Add `optimize_and_train_regression()` function to `optimization.py`:
   - Uses `LGBMRegressor` with `objective="regression"`
   - Target: `long_pnls - short_pnls` (direction value)
   - Prediction: continuous value
   - Threshold: Optuna tunes magnitude threshold [0.0, 15.0]
   - Trade: if predicted > threshold → long, if predicted < -threshold → short
   - Sharpe computed from selected trades' actual PnLs

2. Add `use_regression: bool = False` parameter to `LightGbmStrategy.__init__()`

3. In `_train_for_month()`:
   - If regression: compute `regression_target = long_pnls - short_pnls`
   - Call `optimize_and_train_regression()` instead of `optimize_and_train()`
   - Returns (model, columns, magnitude_threshold)

4. In `get_signal()`:
   - If regression: use `model.predict()` (returns scalar)
   - Trade if |predicted| > threshold
   - Direction = sign(predicted)

## Section 4: Success Criteria

**Primary**: OOS Sharpe > 0 (the model must be profitable OOS with regression)

**Stretch**: OOS Sharpe > baseline +1.84

**Hard constraints**:
- IS MaxDD < 55%
- At least 200 IS trades and 50 OOS trades
- IS Sharpe > 0 (regression must at least work in-sample)
