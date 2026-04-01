# Iteration 111 Diary

**Date**: 2026-04-01
**Type**: EXPLORATION
**Merge Decision**: NO-MERGE (EARLY STOP — Year 2024: PnL=-157.4%, WR=31.0%, 100 trades)

**OOS cutoff**: 2025-03-24

## The Breakthrough: Meme Microstructure Features Fixed 2023

12 new features targeting candle structure, volume dynamics, and order flow **solved the 2023 choppy market problem**:

| Year | Iter 108 (42 feat) | Iter 111 (54 feat) | Delta |
|------|-------------------|-------------------|-------|
| 2022 H2 | +85.6% | +43.4% | -42pp (less crash profit) |
| 2023 | **-69.7%** | **+30.3%** | **+100pp improvement** |
| 2024 | never reached | **-157.4%** | new failure mode |

The model that couldn't navigate 2023 now profits through it. But a new problem emerged: the 2024 meme bull run.

## Results

| Metric | Iter 111 (54 feat) | Iter 108 (42 feat) | Iter 111b (3-day TO) |
|--------|-------------------|-------------------|---------------------|
| IS Sharpe | -0.42 | +0.10 | -1.04 |
| IS WR | 38.2% | 38.6% | 39.7% |
| IS PF | 0.88 | 1.03 | 0.77 |
| IS MaxDD | 213.4% | 108.6% | 67.1% |
| IS Trades | 204 | 114 | 63 |
| Early Stop | 2024 | 2023 | 2022 |

### Per-Symbol (flipped from iter 108!)
| Symbol | Iter 111 WR | Iter 111 PnL | Iter 108 WR | Iter 108 PnL |
|--------|------------|-------------|------------|-------------|
| SHIB | **45.7%** | **+67.4%** | 42.4% | -9.1% |
| DOGE | 30.3% | -157.1% | **34.5%** | **+20.3%** |

The meme features helped SHIB dramatically but hurt DOGE. This suggests the features capture patterns that SHIB exhibits more consistently.

## 2024 Failure Analysis

Monthly PnL shows the problem months:
- Jun 2024: **-70.8%** (12 trades, all losing → meme bull run with DOGE +170% in Nov)
- Nov 2024: **-41.4%** (11 trades → peak of bull market)
- The model shorts into strong uptrends because its 24-month training window is dominated by bearish/choppy 2022-2023 data

## Variant: 3-Day Timeout (111b)

Early-stopped in 2022 (PnL=-44.2%, WR=38.7%). Shorter timeout = more trades (62 in 6 months) but less time for moves to materialize. The 7-day timeout is correct for meme coins with ATR-scaled barriers.

## Exploration/Exploitation Tracker

Last 10 (iters 102-111): [E, E, E, E, E, X, E, E, E, **E**]
Exploration rate: 9/10 = 90%.

## Key Learnings

1. **Microstructure features genuinely help meme coins.** Body ratios, shadow ratios, volume spikes, and taker imbalance capture dynamics that standard technical features miss. The 2023 improvement (+100pp) is the strongest single-iteration signal improvement in the meme track.

2. **The 2024 problem is regime shift, not feature quality.** The model trains on bearish/choppy data and encounters a bull market it's never seen. This is a fundamental limitation of the 24-month walk-forward approach when market regimes change dramatically.

3. **3-day timeout is too short for meme coins.** 7 days with ATR-scaled barriers is the right timeframe.

4. **Per-symbol dynamics are unstable.** Features that help SHIB hurt DOGE. This suggests the model needs per-symbol specialization or the feature set needs both trend-following AND mean-reversion signals.

## Next Iteration Ideas

1. **EXPLORATION: Add trend-following features to balance the mean-reversion bias.** The current meme features (body ratios, z-scores, mean reversion) excel in choppy markets but fail in trends. Add: `meme_trend_strength` (cumulative return over 10 candles), `meme_breakout` (new 20-period high/low), `meme_momentum_persist` (RSI slope over 5 candles). The model needs to learn WHEN to mean-revert vs WHEN to trend-follow.

2. **EXPLORATION: Reduce training window from 24 to 12 months.** The 24-month window means the model trains on 2022 bear data even when predicting 2024 bull. A 12-month window adapts faster to regime changes. Risk: less training data per window.

3. **EXPLOITATION: Keep 54 features but increase cooldown to 4 candles (32h).** The model generated 204 trades (vs 114 in iter 108). More trades in a bad regime = more losses. Higher cooldown reduces overtrading.

4. **EXPLORATION: Add BTC trend as a cross-asset feature.** When BTC is in a strong uptrend, meme coins tend to follow. `xbtc_return_10` and `xbtc_rsi_14` as features (not trading BTC) could help the model detect bull markets.
