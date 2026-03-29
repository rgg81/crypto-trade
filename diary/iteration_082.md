# Iteration 082 Diary — 2026-03-29

## Merge Decision: NO-MERGE (ABANDONED)

Killed mid-run. IS was healthy (+239% through May 2024, 292 trades) but the hypothesis was weak: removing cooldown from a configuration that already doesn't beat baseline (iter 080 OOS Sharpe +1.00 vs baseline +1.84). User decided to prioritize exploration over another ternary exploitation.

**OOS cutoff**: 2025-03-24

## Hypothesis

Ternary 2.0% + cooldown=0 would recover trades lost to cooldown in iter 080.

## Why Abandoned

1. Iter 080 (same config + cooldown=2) already peaked at OOS Sharpe +1.00 — 46% below baseline
2. Cooldown was validated as +12% Sharpe improvement in iter 068 (the baseline). Removing it goes backwards.
3. Ternary and cooldown are not redundant — different mechanisms (training vs execution filtering)
4. Even best case, recovering ~14 trades wouldn't close a 0.84 Sharpe gap

## Exploration/Exploitation Tracker

Last 10 (iters 073-082): [E, X, X, E, X, E, E, X, **X (abandoned)**]
Exploration rate: 4/10 = 40% (including abandoned)
Type: **EXPLOITATION** (abandoned)

## Lessons Learned

1. **Ternary exploitation path is fully exhausted.** Iter 080 (2.0%): best result. Iter 081 (1.0%): catastrophic. Iter 082 (cooldown=0): abandoned as weak hypothesis. No more ternary parameter changes.
2. **Fail fast means killing weak hypotheses before they run**, not just after yearly checkpoints.

## Next Iteration Ideas

Must be EXPLORATION. The biggest unexplored gaps after 82 iterations:

1. **Regression target** — predict forward return magnitude. Fundamentally different from classification. Never attempted.
2. **Interaction features** — RSI×ADX, volatility×trend, cross-asset BTC lag. Never generated in 82 iterations despite being identified as the #1 feature gap.
3. **Multi-timeframe features** — 1h indicators resampled to 8h. Never tried.
