# Iteration 116 Diary

**Date**: 2026-04-01
**Type**: EXPLOITATION
**Merge Decision**: NO-MERGE — OOS Sharpe -0.04 (was +0.29 in iter 114). Shorter timeout caused massive overfitting.

**OOS cutoff**: 2025-03-24

## Results

| Metric | IS | OOS | Iter 114 OOS |
|--------|-----|-----|-------------|
| Sharpe | +1.71 | **-0.04** | +0.29 |
| WR | 51.8% | **39.4%** | 43.0% |
| PF | 1.62 | **0.99** | 1.07 |
| MaxDD | 57.4% | **125.9%** | 78.5% |
| Trades | 249 | **104** | 93 |
| Net PnL | +372.8% | **-2.5%** | +18.8% |

## OOS Per-Symbol

| Symbol | Trades | WR | PnL |
|--------|--------|----|-----|
| DOGE | 51 | 41.2% | +6.2% |
| SHIB | 53 | 37.7% | -8.7% |

## What Went Wrong

Shorter timeout (5 days vs 7 days) made the model dramatically worse:
1. **IS Sharpe jumped from +0.11 to +1.71** — suspiciously high, classic overfitting signal
2. **OOS collapsed to -0.04** — the model learned IS-specific patterns
3. **IS/OOS ratio: negative** — complete researcher overfitting
4. **SHIB turned negative** — from +7.8% to -8.7%

The 5-day timeout changes the label distribution: more labels, more aggressive signals. Optuna finds IS-optimal parameters that don't generalize. The 7-day timeout was actually well-calibrated for meme coin dynamics.

## Configuration

Same as iter 114 except:
- timeout_minutes: 7200 (5 days, was 10080 = 7 days)
- label_timeout_minutes: 7200 (5 days, was 10080 = 7 days)

## Exploration/Exploitation Tracker

Last 10 (iters 107-116): [X, E, E, E, E, E, X, E, E, **X**]
Exploration rate: 7/10 = 70%

## Next Iteration Ideas

1. **Feature pruning**: The meme model has 67 features. Prune to 40-50 based on domain knowledge. Remove features that duplicate information (e.g., vol_natr_7 vs vol_natr_14 vs vol_natr_21 — keep only vol_natr_14).

2. **Wider ATR barriers**: Try TP=3.5x, SL=1.75x (was 2.9x/1.45x). Gives meme coins more room to breathe before hitting barriers.

3. **Shorter training window**: 18 months instead of 24. Meme coin dynamics change faster — older data may be noise.

4. **Don't change timeout** — 7 days works. Learned the hard way.
