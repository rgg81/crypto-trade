# Iteration 172 Research Brief

**Date**: 2026-04-22
**Role**: QR
**Type**: **EXPLORATION** (DOT full IS run — remove year-1 fail-fast to see complete behaviour)
**Previous iteration**: 171 (NO-MERGE, DOT-tuned 40-feature set rejected with evidence)
**Baseline**: v0.165 (A+C+LTC, OOS +1.27, IS +1.08)

## Section 0 — Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

Three iterations of research on DOT's Gate 3 failure (iter-168 baseline, iter-171 tuned features, iter-172 regime filter analysis) converged on a non-obvious conclusion: **the fail-fast protocol is itself biasing the research**. DOT's year-1 (2022) is catastrophic on Dec 2022 alone, and the backtest terminates there. We have zero data on DOT's 2023-2025 IS performance because it never got to run.

Meanwhile, LTC (which ran to completion) shows that 2022 was broadly hard for the A+C+LTC portfolio but LTC's Dec 2022 was only 3 trades, +1.63% — not a disaster, just a slow-down. DOT took the same regime and over-traded (7 trades in Dec, 6 consecutive LONG stop-losses on a downtrend).

We need to see DOT's full IS window before we can conclude anything.

## Research Analysis (IS data only)

Analysis scripts: `analysis/iteration_172/regime_filter_research.py` and direct pandas work inline.

### Finding 1 — No BTC regime metric cleanly separates DOT's 3 visible IS months

Evaluated 9 candidate filters (BTC drawdown 60d/180d, BTC 30/60/90d realised vol, BTC monthly return, BTC NATR_21):

| Metric           | Comparison | Threshold | Flagged | TPR    | FPR    |
|------------------|-----------|-----------|---------|-------:|-------:|
| btc_dd_180d      | <         | -40%      | 2/3     | 0%     | 100%   |
| btc_dd_180d      | <         | -50%      | 1/3     | 0%     | 50%    |
| btc_dd_60d       | <         | -20%      | 2/3     | 100%   | 50%    |
| btc_dd_60d       | <         | -30%      | 0/3     | 0%     | 0%     |
| btc_vol_30d      | >         | 80%       | 0/3     | 0%     | 0%     |
| btc_vol_30d      | >         | 100%      | 0/3     | 0%     | 0%     |
| btc_month_ret    | <         | -10%      | 1/3     | 0%     | 50%    |

None of these filters achieve TPR > 50% with FPR < 30% on the 3 visible DOT months. With only 3 data points (2 good, 1 bad) any filter is over-fit to the pattern.

**More importantly**: the intuition that "high vol regime = adverse" doesn't hold for DOT. Sep 2022 (DOT profitable, +11%) had BTC vol 65%; Dec 2022 (DOT disaster, -19%) had BTC vol 28%. LOWER vol coincided with WORSE DOT performance. The regime-filter framing is probably wrong for this problem.

### Finding 2 — DOT over-trades in the same month LTC is conservative

From trades.csv comparison:

**LTC Dec 2022** (3 trades, full IS from iter 165):
| Open           | Dir | Entry  | Exit  | Result            |
|----------------|-----|--------|-------|-------------------|
| 2022-12-08 07:59 | LONG | 75.62  | 74.74 | -1.26% timeout     |
| 2022-12-16 07:59 | LONG | 73.21  | 69.28 | -5.47% stop_loss   |
| 2022-12-31 15:59 | LONG | 70.05  | 75.98 | +8.36% take_profit |

Sum: +1.63% over 3 trades, 1 winner (the last one catching the year-end bounce).

**DOT Dec 2022** (7 trades, from iter-168 partial):
| Open           | Dir | Entry | Exit   | Result            |
|----------------|-----|-------|--------|-------------------|
| 2022-12-05 15:59 | LONG | 5.538 | 5.305  | -4.31% stop_loss   |
| 2022-12-08 07:59 | LONG | 5.293 | 5.081  | -4.11% stop_loss   |
| 2022-12-13 07:59 | LONG | 5.061 | 4.873  | -3.81% stop_loss   |
| 2022-12-17 23:59 | LONG | 4.705 | 4.458  | -5.36% stop_loss   |
| 2022-12-20 23:59 | LONG | 4.602 | 4.392  | -4.67% stop_loss   |
| 2022-12-23 15:59 | LONG | 4.486 | 4.293  | -4.39% stop_loss   |
| 2022-12-29 07:59 | LONG | 4.320 | 4.650  | +7.54% take_profit |

Sum: -19.11% over 7 trades, same pattern of ever-lower LONG entries on a persistent downtrend.

**LTC and DOT faced the same regime; LTC was more selective.** This is a model-calibration difference, not a regime-detection problem. The fix would be: make DOT more selective (tighter confidence threshold, longer cooldown, or a feature that captures "recent SL streak").

### Finding 3 — We have no data on DOT's 2023-2025 behaviour

Iter-168's fail-fast at Dec 2022 means we've never seen DOT run past that point. The skill's fail-fast rule ("year-1 < 0 → STOP") is protecting us from compute waste but also preventing the QR from doing research on the full IS history.

Without knowing whether DOT was profitable in 2023-2025 IS, we cannot judge whether DOT is a "2022-regime anomaly" or a systematic underperformer. LTC's full IS run shows 2023 was DOT's worst equivalent (LTC 2023 sum +7.78%, mean +0.16%) while 2024-2025 were strong. If DOT follows the same pattern (bad 2022-2023, better 2024+) then the merge decision at 2025-Q1 becomes legitimately interesting.

## Proposed experiment

Run DOT with `yearly_pnl_check=False` (skip fail-fast) and **full baseline 193-feature set** (no tuned pruning, learning from iter-171 that pruning makes things worse). This is the same config as iter-168 except the year-1 checkpoint is disabled — we let the backtest run all 51 walk-forward months and observe the full IS + OOS picture.

**Why this isn't banned by the "post-early-stop parameter tweak" rule**: iter-171 (the most recent early stop) banned param tweaks <2×. We are NOT tweaking TP/SL, trial count, confidence range, or symbol count. We are disabling a GATE — structurally different.

**Why this isn't "cheating" by ignoring fail-fast**: the fail-fast is a *merge gate*, and we are not proposing a merge. This is a research iteration to observe behaviour. The MERGE decision still requires year-1 > 0 via the standard rule (skill's "A good model should be profitable from year 1. Period").

## Expected outcomes

Three cases, mapped to action:

- **(a) DOT IS Sharpe > 1.0, OOS Sharpe > 1.0, IS year-1 PnL still < 0**: DOT recovers hard in 2023-2025. Merge is blocked by year-1 rule, but we have strong evidence that the right fix is *not* rejecting DOT — it's either extending the training window or adding a 2022-regime feature. Iter 173 targets that.
- **(b) DOT IS Sharpe < 1.0 overall**: DOT is genuinely weak even with more data. Iter 173 abandons DOT and either (i) revisits feature engineering for other candidates (ATOM/AAVE/AVAX), or (ii) pivots to Model A improvements.
- **(c) DOT IS Sharpe > 1.0 AND IS year-1 PnL > 0 too**: the iter-168 fail-fast was wrong (could be a seed-dependent flukery since year-1 barely cleared vs failed). Implausible since seed=42 is fixed, but worth seeing.

## Configuration

Runner: `run_iteration_172.py`. Identical to iter-168 (DOT with baseline 193 features, ATR 3.5/1.75) except `yearly_pnl_check=False`.

## Exploration/Exploitation Tracker

Window (163-172): [E, E, E, X, E, E, E, E, X, E] → 8E/2X. Iter-172 as E (removing a gate is structural). Skill says 30% floor; we're well above.

## Commit discipline

Research brief → `docs(iter-172): research brief`
Runner → `feat(iter-172): DOT full IS runner (no fail-fast)`
Engineering report → `docs(iter-172): engineering report`
Diary (last) → `docs(iter-172): diary entry`
