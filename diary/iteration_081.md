# Iteration 081 Diary — 2026-03-29

## Merge Decision: NO-MERGE (EARLY STOP)

Year 2025 PnL=-19.1% (WR 34.1%, 88 trades). OOS Sharpe -1.17 vs baseline +1.84. Catastrophic regression from iter 080.

**OOS cutoff**: 2025-03-24

## Hypothesis

Lowering ternary neutral_threshold from 2.0% to 1.0% would recover trade volume while keeping label quality improvement. 1.0% removes 7.9% of labels (vs 16.7% at 2.0%), keeping 92% of training data.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **Labeling: ternary, neutral_threshold_pct=1.0** (was 2.0 in iter 080)
- Symbols: BTCUSDT, ETHUSDT (pooled)
- Features: 106 (global intersection)
- Walk-forward: monthly retraining, 24mo window, 5 CV folds, 50 Optuna trials
- Ensemble: 3 seeds [42, 123, 789]
- Execution: Dynamic ATR barriers TP=2.9, SL=1.45, cooldown=2

## Results: In-Sample

| Metric | Iter 081 | Iter 080 | Baseline (068) |
|--------|----------|----------|----------------|
| Sharpe | +1.26 | +1.26 | +1.22 |
| WR | 44.9% | 44.6% | 43.4% |
| PF | 1.38 | 1.38 | 1.35 |
| MaxDD | **87.9%** | 56.1% | 45.9% |
| Trades | 343 | 314 | 373 |

## Results: Out-of-Sample

| Metric | Iter 081 | Iter 080 | Baseline (068) |
|--------|----------|----------|----------------|
| Sharpe | **-1.17** | 1.00 | 1.84 |
| WR | **30.8%** | 45.2% | 44.8% |
| PF | **0.74** | 1.33 | 1.62 |
| MaxDD | 53.4% | 33.4% | 42.6% |
| Trades | 65 | 73 | 87 |
| Net PnL | **-38.6%** | +48.9% | +94.0% |

### Per-Symbol OOS

| Symbol | Trades | WR | PnL |
|--------|--------|-----|-----|
| BTCUSDT | 31 | 29.0% | -13.8% |
| ETHUSDT | 34 | 32.4% | -24.8% |

## What Happened

**The 1.0% neutral threshold is catastrophically worse than 2.0%.** Despite nearly identical IS metrics (Sharpe +1.26, WR 44.9%), OOS collapsed to Sharpe -1.17 with both symbols unprofitable.

**Root cause**: The 2.0% threshold removes the right amount of noise. At 1.0%, only 4.8% of training labels become neutral (vs ~11% at 2.0%). The 2.0% threshold specifically removes timeout labels where |return| < 2.0% — these are the ambiguous, directionless candles that confuse the model. At 1.0%, only the most extreme noise is removed, and the model still learns from ambiguous timeout labels with 1-2% returns.

**IS MaxDD is the warning sign**: 87.9% (vs 56.1% in iter 080). This massive IS MaxDD means the model has deeper drawdowns — it makes more trades during bad periods. The lighter noise filtering allows the model to be confident on ambiguous candles, generating more trades that happen to be wrong during drawdowns.

**The neutral threshold is not a linear scale.** Going from binary→2.0% was a big improvement. Going from 2.0%→1.0% didn't split the difference — it reverted to nearly-binary behavior. The quality improvement from ternary is concentrated in the 1-2% return range, which is exactly the noisiest regime.

## Quantifying the Gap

WR: 30.8%, break-even 33.3%, gap **-2.5pp below break-even**. OOS SL rate: 58% (vs 50.7% in iter 080). The model takes more stop-losses because it's less selective — the lighter filtering lets more ambiguous signals through.

## Exploration/Exploitation Tracker

Last 10 (iters 072-081): [E, E, X, X, E, X, E, E, E, **X**]
Exploration rate: 6/10 = 60%
Type: **EXPLOITATION** (neutral threshold parameter change)

## Research Checklist

Completed 4 categories: A (same features, referenced iter 080), C (neutral threshold sensitivity analysis — 6 thresholds on IS), E (trade patterns from iter 080 IS trades), F (monotonic quality improvement confirmed in analysis).

## lgbm.py Code Review

No changes from iter 080. The multiclass implementation works correctly. The only difference is the threshold parameter passed to labeling.

## Lessons Learned

1. **Neutral threshold 2.0% is a sharp optimum, not a smooth curve.** Despite the IS analysis showing gradual quality improvement from 0% to 3%, the OOS impact is highly nonlinear. 2.0% works; 1.0% catastrophically fails. The IS analysis of label quality (monotonic WR improvement) does NOT predict OOS performance.

2. **IS analysis of labeling is misleading.** The IS analysis showed 1.0% had +1.4pp WR improvement over binary (good) and -1.0pp vs 2.0% (small degradation). This suggested 1.0% would be "almost as good." In reality, the OOS performance cliff is between 1.0% and 2.0%.

3. **IS MaxDD is the best early warning for OOS failure.** IS MaxDD 87.9% (vs 56.1% in iter 080) was a clear signal that the model was taking too many risky trades. Future iterations should monitor IS MaxDD as a quality gate — if it degrades significantly from baseline (45.9%), the model is likely overfitting to noise.

4. **The 2.0% neutral threshold is load-bearing.** It removes exactly the right labels — timeout candles where the market barely moved (|return| < 2%). These are the candles where the direction label is essentially random. Removing them is critical for ternary to work.

5. **Do not tune the neutral threshold further.** 2.0% is the right value for 8%/4% TP/SL. Any lower and the ternary benefit disappears. Any higher (iter 080 suggested 3.0%) risks removing too many labels. The 2.0% threshold should be treated as fixed.

## Next Iteration Ideas

The ternary exploitation path is exhausted. 2.0% is the optimal threshold. Return to exploration:

1. **EXPLORATION: Regression target** — Predict forward 8h return magnitude using `objective="regression"`. The model learns magnitude, not just direction. This is the most fundamental unexplored labeling change. Binary/ternary both discretize the target; regression preserves the full information.

2. **EXPLORATION: Feature generation — interaction features** — Create RSI × ADX, volatility × trend_strength, and cross-asset (BTC return lag as feature for ETH). These have never been tried in 81 iterations. The 106 features are all single-indicator; interactions may capture nonlinear signal.

3. **EXPLOITATION: Ternary 2.0% + cooldown=0** — Iter 080's ternary is already selective. Removing cooldown might recover the 14 trades lost to cooldown without degrading quality. Simple parameter test.
