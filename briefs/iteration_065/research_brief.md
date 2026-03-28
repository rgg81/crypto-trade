# Iteration 065 — Research Brief

**Type**: EXPLORATION (labeling paradigm change)
**Date**: 2026-03-28

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24 (fixed, never changes)
```

- IS: all data before 2025-03-24
- OOS: all data from 2025-03-24 onward
- Walk-forward runs on full dataset; reporting layer splits at cutoff

## Context: After EARLY STOP in Iter 064

Iter 064 removed `training_days` from Optuna and was early-stopped (Year 1 PnL=-65.8%). Structural changes are mandatory. The diary recommended dynamic ATR labeling as the top priority.

## Hypothesis

**Align labeling with execution by using ATR-scaled barriers in both**.

Currently (iter 063 baseline):
- **Labeling**: Fixed TP=8%, SL=4% — model learns "which direction hits fixed 8% TP first"
- **Execution**: Dynamic TP=2.9×NATR_21, SL=1.45×NATR_21 — trades adapted to volatility

This creates a mismatch. The model is trained to predict outcomes under fixed barriers but trades under dynamic barriers. In calm markets (NATR≈1.8%), the execution TP is 5.3% — much easier to hit than the 8% the model was trained on. The model may be confidently predicting "8% TP won't be hit" when a 5.3% TP would easily be hit.

**Proposed change**: Label training data with ATR-scaled barriers too:
- Label TP = 2.9 × ATR_21 (raw ATR in price units)
- Label SL = 1.45 × ATR_21

This way the model learns "which direction hits the VOLATILITY-ADJUSTED TP first?" — exactly what it will execute in practice. The labels and execution are fully aligned.

## Expected Impact

1. **Better signal for low-volatility periods**: Model learns that smaller moves (3-5%) are sufficient for TP in calm markets
2. **Better signal for high-volatility periods**: Model learns that larger moves (8-15%) are needed for TP in volatile markets
3. **More consistent label quality**: Labels adapt to the tradeable range of each candle, not a fixed arbitrary threshold

## Risk

1. ATR-based labels may be noisier in early training data (2020) where ATR values may be less reliable (fewer data points)
2. The model may lose its ability to learn from "difficult" trades (where only large moves hit fixed TP) — these might carry useful signal
3. Label distribution may shift (more/fewer TPs with dynamic barriers)

## Configuration

All parameters identical to iter 063 baseline EXCEPT:
- **NEW**: `atr_label_mode=True` — labeling uses ATR-scaled barriers
- Labeling TP/SL: ATR_21 × 2.9 / ATR_21 × 1.45 (same multipliers as execution)
- Everything else unchanged: 24mo training, 50 trials, 5 CV, 106 features, BTC+ETH

## Implementation Notes for QE

1. Add `atr_label_mode: bool = False` to LightGbmStrategy constructor
2. In `_train_for_month`, when `atr_label_mode=True`:
   - Load `vol_atr_21` from feature store for training period
   - Build master-indexed array of raw ATR values
   - Pass to `label_trades` via `atr_values` parameter
   - Use `atr_tp_multiplier`/`atr_sl_multiplier` as TP/SL args (they become ATR multipliers)
3. The existing `label_trades` function already supports ATR mode — no changes needed

## Research Checklist

After EARLY STOP, minimum 4 categories required. However, the iter 064 early stop was from a clean exploitation failure (removing training_days), not a pattern of structural weakness. The structural change here (dynamic labeling) is well-motivated by the labeling/execution mismatch identified in iter 063's diary.

Categories addressed:
- **C (Labeling)**: This iteration IS a labeling change — ATR-scaled barriers replace fixed barriers
- **E (Trade Patterns)**: Analyzed in iter 064's research phase — IS/OOS patterns consistent, supporting the model's core signal
- **A (Features)**: Feature set unchanged (106), confirmed near-optimal in iters 061-062
- **D (Feature Frequency)**: Not applicable — no feature changes
