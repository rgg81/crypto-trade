# Iteration 008 Diary - 2026-03-26

## Merge Decision: NO-MERGE

OOS Sharpe worsened -1.91→-3.96. WR dropped 32.9%→31.2%. More features and BTC cross-asset didn't help.

## Research Checklist Categories Completed: A, C, E, F

### Key Research Findings

**A. Features**: Volume (27.3%), Trend (25.2%) dominate. Momentum barely contributes (6.3%). 31/185 features have zero importance.

**C. Labeling**: Labels are stable (BTC flip rate 16.6%). TP_rate in labeled direction at 4%/2% is 68% — the labels have strong signal, the model can't learn them. **4:1 barriers (TP=4%/SL=1%) have margin of +20.8pp above break-even.**

**E. Trade Patterns**: SHORT outperforms LONG by 4.1pp (32.7% vs 28.6%). 23:00 UTC worst hour. Loss streaks average 4.0.

**F. Statistical Rigor**: **Bootstrap CI [30.18%, 30.98%] does NOT include break-even 33.3% (p=4.8e-37)**. Parameter tuning CANNOT close this gap. Short-only CI [32.09%, 33.28%] also misses.

## Gap Quantification

WR is 30.6% (IS), break-even is 33.3%, gap is 2.7pp. TP rate is 29.5%, SL rate is 68.9%. Bootstrap CI proves this gap is statistically significant. The current classification approach on these features CANNOT reach break-even.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- **Changes**: Feature intersection→union (189 features, from 106) + 4 BTC cross-asset features
- Symbols: Top 50, TP=4%/SL=2%, 50 Optuna trials, seed 42

## Results: Out-of-Sample

| Metric | Value | Baseline |
|--------|-------|----------|
| Sharpe | -3.96 | -1.91 |
| WR | 31.2% | 32.9% |
| PF | 0.84 | 0.92 |
| Trades | 8,367 | 6,831 |
| MaxDD | 1,933% | 997% |

## What Failed

- **More features made it worse**: 189 features (union) vs 106 (intersection) reduced WR from 32.9% to 31.2%. More noise features diluted the signal.
- **BTC cross features didn't add value**: The model already captures BTC dynamics through BTC's own features. Cross-asset features are redundant.
- **IS/OOS ratio 0.99**: Perfect consistency — the model is uniformly bad, not overfit.

## lgbm.py Code Review

- Fixed the intersection→union bug. Result: access to 189 features instead of 106.
- Added BTC cross-asset feature injection (_load_btc_cross_features, _inject_btc_features).
- Test month feature loading now handles mixed parquet + injected features correctly.
- The code works but the approach doesn't help performance.

## Next Iteration Ideas

1. **Revert to intersection** (106 features was better than 189) and try **ternary classification** — add a "neutral/don't-trade" class for ambiguous candles. This changes the model formulation.
2. **Per-symbol models for BTC and ETH** — BTC had 50.6% OOS WR in iter 004. A dedicated BTC model with all 185 features might be even better.
3. **Switch to regression** — predict forward return, only trade when |predicted| > threshold. Fundamentally different approach.
4. **Short-only strategy** — SHORT has 4.1pp WR advantage over LONG in IS data. Remove long trades entirely.

## Lessons Learned

- Feature intersection (106 features) > feature union (189 features). The intersection acts as natural feature selection — features present in all symbols are the most universal and predictive.
- Cross-asset features are redundant when the model is pooled — BTC's own features are already in the training data for BTC candles.
- The statistical rigor analysis (checklist F) should have been done BEFORE iteration 001. The p=4.8e-37 result proves the current approach is fundamentally limited.
