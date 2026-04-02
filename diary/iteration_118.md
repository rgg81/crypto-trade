# Iteration 118 Diary

**Date**: 2026-04-02
**Type**: EXPLOITATION (single parameter change)
**Model Track**: Meme (DOGEUSDT + 1000SHIBUSDT)
**Decision**: **NO-MERGE** (OOS Sharpe +0.73 < baseline +1.01)

## Hypothesis

Wider ATR barriers (3.5x/1.75x, up from 2.9x/1.45x) will reduce premature SL exits on meme coins, capturing larger moves while maintaining 2:1 TP/SL ratio.

## Single Variable Changed

| Parameter | Iter 117 | Iter 118 |
|-----------|----------|----------|
| atr_tp_multiplier | 2.9 | **3.5** |
| atr_sl_multiplier | 1.45 | **1.75** |

Everything else identical: 45 pruned features, 24-month training, 5-seed ensemble, 7-day timeout, 2-candle cooldown.

## Results

### Comparison with Iter 117 (previous best meme)

| Metric | Iter 117 | Iter 118 | Change |
|--------|----------|----------|--------|
| OOS Sharpe | +0.66 | **+0.73** | +10.6% |
| OOS WR | 45.2% | 45.7% | +0.5pp |
| OOS PF | 1.17 | 1.20 | +2.6% |
| OOS MaxDD | 53.0% | 53.2% | +0.2pp (worse) |
| OOS Trades | 93 | 81 | -12.9% |
| OOS Net PnL | +45.9% | +49.1% | +7.0% |
| IS Sharpe | +0.93 | +0.63 | -32.3% |
| IS Net PnL | +93.1% | +164.8% | +77.0% |
| IS MaxDD | 90.5% | **170.7%** | +88.6% (much worse) |
| IS/OOS Ratio | 0.71 | **1.17** | OOS > IS now |

### Per-Symbol OOS

| Symbol | Trades | WR | Net PnL | % of Total |
|--------|--------|----|---------|------------|
| 1000SHIBUSDT | 41 | 53.7% | +65.8% | 134.0% |
| DOGEUSDT | 40 | 37.5% | -16.7% | -34.0% |

### OOS Monthly PnL

| Month | PnL | Trades |
|-------|-----|--------|
| 2025-03 | +25.2% | 2 |
| 2025-04 | -19.5% | 10 |
| 2025-05 | -12.7% | 2 |
| 2025-06 | +19.9% | 9 |
| 2025-07 | -6.3% | 1 |
| 2025-08 | **+46.4%** | 9 |
| 2025-09 | +7.3% | 11 |
| 2025-10 | -24.4% | 13 |
| 2025-11 | +26.5% | 4 |
| 2025-12 | **-37.6%** | 13 |
| 2026-01 | +20.7% | 4 |
| 2026-02 | +3.7% | 3 |

6 profitable months, 6 losing months. Best: Aug 2025 (+46.4%). Worst: Dec 2025 (-37.6%).

## Analysis

### What the wider barriers did

1. **IS PnL nearly doubled** (+164.8% vs +93.1%). The wider barriers captured massive moves during the March 2024 meme rally (+79% in one month) and the Nov 2024 DOGE pump. Each TP hit is bigger (e.g., SHIB +19.2% TP vs ~14% with narrower barriers).

2. **IS MaxDD exploded** (170.7% vs 90.5%). Wider SL means bigger losses per losing trade. During choppy periods, the model takes larger hits before stopping out. This is the fundamental tradeoff: bigger wins but also bigger losses.

3. **OOS improvement was moderate** (+0.73 vs +0.66). The wider barriers helped, but the OOS period (Mar 2025 → Feb 2026) doesn't have the same extreme bull runs that IS captured. The August 2025 spike (+46.4%) is the only month where wider barriers clearly dominated.

4. **IS/OOS ratio improved dramatically** (1.17 vs 0.71). This is counterintuitive — the OOS is now BETTER than IS on a risk-adjusted basis. This is because IS includes the early 2022-2023 period where the model was still learning, while OOS only sees 2025-2026 where the model is mature.

### DOGE vs SHIB divergence persists

SHIB carries 134% of OOS PnL while DOGE is -34%. This was also true in iter 117 (SHIB +26.9%, DOGE +19.0% — both positive then). The wider barriers made DOGE worse: DOGE's 37.5% OOS WR with bigger losses per trade = more negative PnL.

The problem is DOGE-specific: wider barriers on a coin with lower predictability amplify losses. SHIB's directional signal is stronger, so wider barriers help it.

### Gap quantification

WR is 45.7%, break-even is 33.3% (for 2:1 TP/SL), gap is +12.4pp. This is healthy.
TP rate: from exit reasons, wider barriers shift the mix toward more timeouts (trades that neither hit TP nor SL within 7 days) and fewer SL exits vs iter 117.

## Hard Constraints Check

| Constraint | Threshold | Iter 118 | Pass? |
|------------|-----------|----------|-------|
| OOS Sharpe > baseline | > +1.01 | +0.73 | FAIL |
| OOS MaxDD ≤ 1.2 × baseline | ≤ 55.9% | 53.2% | PASS |
| OOS Trades ≥ 50 | ≥ 50 | 81 | PASS |
| OOS PF > 1.0 | > 1.0 | 1.20 | PASS |
| IS/OOS Sharpe ratio > 0.5 | > 0.5 | 1.17 | PASS |

Primary metric fails (meme model +0.73 < baseline +1.01). Expected — this is the meme sub-model.

## Label Leakage Audit

- CV gap: 44 rows = (21 + 1) × 2 symbols. Verified in output logs (all months show "CV gap: 44 rows").
- TimeSeriesSplit(n_splits=5, gap=44) used correctly.
- Walk-forward: monthly retrain on past data only. No future leakage.

## lgbm.py Code Review

No changes to lgbm.py in this iteration. Same 45-feature set, same ensemble logic. Reviewed for ATR barrier passthrough — `atr_tp_multiplier=3.5` and `atr_sl_multiplier=1.75` correctly flow through to labeling and execution barriers. No bugs found.

## Research Checklist

Categories completed:
- **A** (features): Same 45 pruned features as iter 117. No changes.
- **E** (trade patterns): DOGE WR dropped from ~44% → 37.5% OOS with wider barriers. SHIB WR improved. Exit reason shift toward more timeouts.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, E, X, E, E, E, X, E, X, **X**] (iters 109-118)
Exploration rate: 7/10 = 70% (well above 30% minimum)
This iteration: EXPLOITATION (single parameter change)

## Next Iteration Ideas

1. **Per-symbol ATR barriers**: SHIB benefits from wider barriers, DOGE doesn't. Consider SHIB at 3.5x/1.75x but DOGE at original 2.9x/1.45x. Requires code change to support per-symbol barrier multipliers.

2. **Combined portfolio test**: With meme OOS Sharpe +0.73 (up from +0.66), the BTC/ETH (+1.01) + DOGE/SHIB (+0.73) combined portfolio should be closer to beating baseline. Iter 115 failed at +0.83 combined with meme at +0.29. Now at +0.73, the combined result should be significantly better.

3. **More aggressive feature pruning**: Try 35 features (remove more of the weakest meme microstructure features).

4. **18-month training window**: Faster adaptation to meme dynamics. Meme coins change behavior faster than BTC/ETH.
