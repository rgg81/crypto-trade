# Iteration 077 Diary — 2026-03-28

## Merge Decision: NO-MERGE (EARLY STOP)

Year 2025 PnL -33.0% (WR 37.0%, 100 trades). OOS Sharpe -0.40. Wider ATR multipliers catastrophically overfit to IS.

**OOS cutoff**: 2025-03-24

## Hypothesis

Wider ATR multipliers (TP=3.2/SL=1.6 vs iter 076's 2.9/1.45) would close the 7% OOS Sharpe gap from iter 076 by producing wider median barriers (8.89%/4.45% vs 8.05%/4.03%).

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- Labeling: Triple barrier dynamic ATR **TP=3.2×NATR_21, SL=1.6×NATR_21**, timeout=7d
- Symbols: BTCUSDT, ETHUSDT
- Features: 106 (global intersection)
- Walk-forward: monthly retraining, 24mo window, 5 CV folds, 50 Optuna trials
- Ensemble: 3 seeds [42, 123, 789]
- Execution: Dynamic ATR barriers TP=3.2, SL=1.6, cooldown=2

## Results: In-Sample

| Metric | Iter 077 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | **+1.33** | +1.22 |
| WR | **50.2%** | 43.4% |
| PF | **1.43** | 1.35 |
| MaxDD | 47.4% | 45.9% |
| Trades | 267 | 373 |

## Results: Out-of-Sample (EARLY STOP)

| Metric | Iter 077 | Baseline (068) |
|--------|----------|----------------|
| Sharpe | **-0.40** | +1.84 |
| WR | **35.1%** | 44.8% |
| PF | **0.90** | 1.62 |
| MaxDD | **54.4%** | 42.6% |
| Trades | 77 | 87 |
| Net PnL | **-17.7%** | +94.0% |

## What Happened

The wider multipliers produced outstanding IS metrics (WR 50.2%!) but collapsed in OOS. The OOS/IS Sharpe ratio of -0.31 indicates extreme researcher overfitting.

**Root cause**: Wider labels (median TP ~9%, SL ~4.5%) make the labeling more "generous" — more candles get TP labels because the barrier is wider. But in execution, the actual barriers are ALSO wider (3.2×NATR), so trades need larger moves to resolve. During the 2025 OOS period (lower volatility), the wider barriers rarely hit TP, and the model's predictions from training on wider-label patterns don't transfer.

The key insight from iters 076-077 combined: **There's a nonlinear relationship between ATR multiplier and OOS performance**:
- 2.9/1.45 (iter 076): OOS Sharpe +1.72 (7% below baseline)
- 3.2/1.6 (iter 077): OOS Sharpe -0.40 (catastrophic)
- baseline (fixed 8%/4%): OOS Sharpe +1.84 (best)

Moving from 2.9→3.2 (10% wider) caused a collapse from +1.72→-0.40. This means ATR-aligned labeling is hypersensitive to the multiplier choice.

## Exploration/Exploitation Tracker

Last 10 (iters 068-077): [E, X, E, E, E, E, X, X, E, **X**]
Exploration rate: 6/10 = 60%
Type: **EXPLOITATION** (ATR multiplier tuning)

## Lessons Learned

1. **ATR multiplier sensitivity is extreme.** A 10% increase in multipliers (2.9→3.2) turned a near-baseline result into a catastrophe. The label-execution alignment is a knife's edge.

2. **The baseline's fixed 8%/4% labels work BETTER than dynamic labels.** Combined evidence from iters 076 (slight Sharpe loss) and 077 (catastrophe): the fixed labels provide beneficial regularization that dynamic labels lose.

3. **High IS WR is a warning sign.** IS WR of 50.2% (vs baseline 43.4%) should have been a red flag — the wider labels made it "easier" to label correctly in training but the patterns didn't generalize.

4. **Stop exploring ATR-aligned labeling.** Two iterations (076, 077) confirm: the approach either slightly underperforms (2.9/1.45) or catastrophically fails (3.2/1.6). The baseline's fixed labels are the optimal approach for this model.

## Next Iteration Ideas

ATR-aligned labeling is exhausted. Move to fundamentally different approaches:

1. **EXPLORATION: Regression target** — Predict forward 8h/24h return magnitude instead of binary direction. Uses `objective="regression"` in LightGBM. This is the most fundamental unexplored change — different loss function, no discretization of labels.

2. **EXPLORATION: Per-symbol models** — Train separate LightGBM for BTC and ETH, each with its own Optuna. Research showed ETH has 51.1% WR SHORT vs BTC 43.6% LONG — very different dynamics.

3. **EXPLORATION: Hybrid labeling** — Use fixed labels for quiet markets (NATR < P25) but ATR labels for volatile markets. This captures the benefit of fixed labels as a confidence filter while adapting to extreme volatility.
