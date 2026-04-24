# Iteration 171 Diary

**Date**: 2026-04-22
**Type**: EXPLOITATION (DOT-tuned feature set)
**Decision**: **NO-MERGE (EARLY STOP, hypothesis rejected)** — feature selection made things worse

## What I tested and what I learned

**Hypothesis**: DOT's signal lives at longer lookbacks than the LINK/LTC-optimised baseline captures (established in the Phase 1-5 research brief via DOT vs LTC MDI comparison — 8/20 top-feature overlap). A DOT-tuned 40-feature set should let the model focus on DOT-relevant signals and clear Gate 3.

**Result**: FALSE. The 40-feature set produced IS Sharpe −1.40 (vs +0.54 at baseline 193), year-1 PnL −44.4% (vs −14.0%), and year-1 WR 23.8% (vs 37.5%). Every direction was worse.

**Mechanism**: I built the 40-feature list from MDI of a reference model trained on DOT IS with 193 features — but that reference model was already in the catastrophic-overfit zone (samples/feature ≈ 11). MDI on an overfit model identifies the features most effective at fitting noise, and pruning to those concentrates the overfitting instead of reducing it. The skill's iter-094 warning applies directly:

> "Iter 094: Pruning BTC/ETH from 185→50 features destroyed co-optimization, IS Sharpe −1.46."

Iter-094 → IS Sharpe −1.46. Iter-171 → IS Sharpe −1.40. Same failure, same magnitude.

## The real problem with DOT

From the iter-168 research (carried forward into this iteration):

- 2022-09: 5 trades, 80% WR, +10.99%
- 2022-11: 5 trades, 40% WR, +1.63%
- 2022-12: 7 trades, 14.3% WR, **−19.11%** (post-FTX regime)

Drop Dec 2022 alone and DOT's year-1 is +12.62%. The signal is intact for 11 of 12 months; one regime-mismatch month breaks the fail-fast check.

Feature pruning can't fix regime mismatch. The model doesn't have a feature that tells it "we are in a post-FTX crisis regime", so it keeps signalling trades as if the distribution were normal.

## What the QR learned about its own methodology

1. **MDI on a single-symbol model is unreliable in our regime** (samples/feature ≈ 11). Features that maximise MDI are the same features that maximise training-set overfit. Pruning via that signal is a trap.

2. **A cheap label proxy (sign of next candle) for feature-ranking purposes is a bigger compromise than I realised**. The production label is triple-barrier 8%/4% over 7 days. Features that predict one-step direction are only loosely related to what matters for the trading model.

3. **Correlation dedup at |r|>0.90 is fine in isolation but compounded with (1) and (2) made things worse**, not better.

4. **Evidence-backed research is worth doing even when the hypothesis is wrong**. I learnt more from iter-171's failure than from iters 164/167/168/170 combined, because I had numbers to reason with. A NO-MERGE with evidence is a scientific advance; a NO-MERGE without evidence is just compute burned.

## Research Checklist

- **A1 / A3 (Feature Contribution)**: executed, hypothesis rejected. MDI top-40 with correlation dedup failed for DOT. Revised take: do not use this pattern for single-symbol candidate tuning.
- **C (Labeling / NATR)**: executed in the Phase 5 brief. DOT's NATR 4.15% fits ATR 3.5/1.75. Not the problem.
- **E (Trade Pattern)**: executed. Dec 2022 dominates the year-1 failure. Real problem is regime.

## Exploration/Exploitation Tracker

Window (162-171): [E, E, E, E, X, E, E, E, E, X] → 8E/2X. Iter-171 as X (narrowed feature set, same architecture). Need to continue EXPLOITATION lean.

## lgbm.py Code Review

No code changes this iteration. Pipeline handled the 40-feature list correctly, no crashes, no silent feature drops (validated by log `[lgbm] 40 feature columns, 51 walk-forward splits`).

## Next Iteration Ideas

### 1. Iter 172 (EXPLORATION, HIGH PRIORITY) — Regime-filter research for DOT

Dec 2022 is the failure. Find a regime metric that would have flagged it:

- **Hypotheses to test in QR Phase 1-5** (numerical analysis on IS BTC data):
  - BTC 30-day realised vol > 90th-percentile-of-history
  - BTC 30-day return < 10th-percentile-of-history (deep drawdown)
  - BTC NATR_21 in top quartile
  - BTC/ETH correlation spike > 0.95 (flight-to-BTC-quality signal)
- For each candidate metric, compute: what fraction of DOT's losing months does it flag, what fraction of DOT's winning months does it *also* (incorrectly) flag? Pick the metric with the best TP/FP ratio.
- **Implementation option A**: add chosen metric as a feature in `feature_columns` (let the model learn to handle it).
- **Implementation option B**: add `regime_veto_feature` + threshold to `BacktestConfig`. Pre-signal filter in `run_backtest`: skip the candle entirely when the veto condition is true.

Option B is cleaner (doesn't change model internals) and more testable. Favor B unless the QR analysis shows the metric should be a feature, not a gate.

### 2. Iter 173 — If regime filter works for DOT, does it help AAVE / ATOM / AVAX too?

Apply the same filter (with same threshold) to the four previously-rejected candidates. If they pass year-1 with the filter, the candidate-pool problem was always "adverse regimes" and we have 4 symbols to re-screen. If they still fail, DOT is special and the filter is DOT-specific.

### 3. Iter 174 (EXPLOITATION) — If iter 172/173 succeed, rebalance portfolio

Build the pooled portfolio A+C+LTC + whichever candidates passed with the regime filter. Check merge floors (IS > 1.0, OOS > 1.0) and concentration. Update baseline if merge passes.

### 4. Rejected for iter 172+ (per fail-fast ban after EARLY STOP)

Per skill, after an EARLY STOP the next iteration must make STRUCTURAL changes. These are banned:

- Changing DOT's ATR multipliers by less than 2× (3.5 → 2.9 is 0.83×, banned)
- Changing Optuna trial count
- Changing confidence threshold range
- Changing symbol count by less than 50% (staying on 1 symbol = OK, adding one = OK if structural)

Regime-filter work is structural (new mechanism), so iter 172 is allowed.
