# Iteration v2/031 Diary

**Date**: 2026-04-15
**Type**: EXPLORATION (5th symbol, audit improvements, skill update)
**Parent baseline**: iter-v2/029 (forced reset)
**Decision**: **NO-MERGE** — concentration still fails + OOS mean regressed

## What changed vs iter-029

1. Added ADAUSDT as 5th symbol (Model I)
2. Regenerated ADAUSDT parquet with BTC cross-asset features
3. Fixed concentration metric to use **positive-total share**
4. Added **distressed-seed flag** (|total_oos_wpnl| < 10 or ≤ 0)
5. Added **n-symbol-aware thresholds** in both runner and skill

## Results — bimodal, IS big win, OOS regression

| Metric | iter-029 | **iter-031** | Δ |
|---|---|---|---|
| Mean IS monthly | +0.5578 | **+0.7477** | **+34%** |
| Mean OOS monthly | +0.8956 | +0.6605 | **−26%** |
| Profitable seeds | 9/10 | **7/10** | −2 |
| OOS/IS ratio | 1.61x | 0.88x | inverted |

**Primary seed 42**:
- OOS monthly **+1.5604** (iter-029: +1.2774, **+22%**)
- IS monthly **+0.8980** (iter-029: +0.6680, **+34%**)
- OOS trade Sharpe **+1.6150** (best after iter-019)
- **XRP concentration 41.87%** (iter-029: 69.47%, **−27.6pp**)
- ADA contributes 24.62% of positive PnL (47.8% WR)

**The primary seed result is the best 5-symbol run in v2's history.**
But the mean is dragged down by 3 seeds (1001, 3456, 4567) going
OOS-negative, while iter-029 had those same seeds neutral or positive.

## Seed concentration audit — all fail the new n=5 rule

```
n_symbols=5, thresholds: max≤40%, mean≤35%, ≤1 above 32%

  seed     max    symbol
    42   41.87%   XRPUSDT   (1.87pp over)
   123   78.59%   XRPUSDT
   456   58.83%   XRPUSDT
   789   47.52%   XRPUSDT
  1001  100.00%   XRPUSDT   DISTRESSED
  1234   45.85%  DOGEUSDT
  2345   67.64%   XRPUSDT
  3456  100.00%   XRPUSDT   DISTRESSED
  4567   70.93%   XRPUSDT   DISTRESSED
  5678   53.40%  NEARUSDT

Mean max-share: 66.46%  (rule: ≤35%)
Pass max: 0/10
Pass inner: 0/10
Distressed: 3/10  (rule: ≤2)
Overall: FAIL on every gate
```

**Best seed is primary (42) at 41.87%**, just 1.87pp over. Every other
seed is worse. Three seeds are now 100% dominated (distressed).

## The key insight — adding symbols doesn't fix concentration; it
## exposes seed variance

Before iter-031:
- 4-symbol portfolio: concentration mean ~71% (all dominated by XRP
  or NEAR)
- Sometimes distressed when 2+ symbols lost money

After iter-031:
- 5-symbol portfolio: concentration mean 66% (slightly better)
- But distressed seeds went from marginal to 100% dominated
- MORE losing symbols on bad seeds = bigger drag on total

**Adding ADA helped primary and ~3 other seeds, but on seeds where
Optuna finds bad hyperparameters, the 5 losers cascade more than 4
losers did.**

The real problem isn't too few symbols. It's that some seeds produce
hyperparameter sets that trade well on 1 symbol and poorly on 4.
With more symbols, the bad-trade cascade is worse.

## Per-seed deep dive — who improved, who regressed

| Seed | Δ IS | Δ OOS | Explanation |
|---|---|---|---|
| 42 | +0.23 | **+0.28** | clean improvement |
| 123 | +0.05 | −0.58 | IS flat, OOS regressed |
| 456 | +0.09 | **+0.42** | clean improvement |
| 789 | +0.06 | **+0.59** | best improvement |
| 1001 | **+0.66** | **−0.87** | IS much better, OOS dump |
| 1234 | +0.08 | −0.01 | flat |
| 2345 | +0.26 | −0.61 | IS better, OOS regressed |
| 3456 | +0.22 | **−1.18** | catastrophic OOS |
| 4567 | +0.15 | −0.54 | OOS flip |
| 5678 | +0.10 | +0.15 | mild improvement |

**Observations**:
- Seeds that IMPROVED on OOS (42, 456, 789, 5678): 4 seeds, clean wins
- Seeds that REGRESSED significantly on OOS (1001, 2345, 3456, 4567): 4 seeds
- Seeds that STAYED FLAT (123, 1234): 2 seeds

The split is ~50/50. On balance, the aggregate mean looks worse
because the regressions are bigger in magnitude than the improvements.

## Why the IS/OOS ratio inverted (0.88x)

OOS/IS ratio < 1 is an "anti-overfitting" signal that usually means
the model is **underfitting**. iter-031's 0.88x ratio says the model
learned patterns that work on IS (+0.75 mean) but transfer more weakly
to OOS (+0.66 mean).

This is the opposite of v1/v2's usual failure mode (overfitting,
OOS/IS > 2). The 5-symbol config may be pushing the model to find
over-generalized patterns that don't capture each symbol's nuances.

## Skill update recap

Committed to `iteration-v2/031` (will be on quant-research after
the iter-031 infrastructure merge):

1. **n-symbol-aware concentration table**:
   - n=2: max≤60%, mean≤55%, ≤1 above 50%
   - n=3: max≤55%, mean≤50%, ≤1 above 45%
   - n=4: max≤50%, mean≤45%, ≤1 above 40%
   - n=5: max≤40%, mean≤35%, ≤1 above 32%
   - n=6-7: max≤35%, mean≤30%, ≤1 above 28%
   - n=8+: max≤30%, mean≤25%, ≤1 above 23%
2. **weighted_pnl is the canonical measure** (not net_pnl_pct from
   per_symbol.csv). iter-029 primary's "60.86%" was really 69.47%.
3. **Distressed-seed flag**: |total_oos_wpnl| < 10 or ≤ 0 → flag.
   Rule: ≤2 of 10 distressed.
4. **Positive-total share** metric for all share computations.

## Lessons learned

1. **Dilution via symbol addition is LIMITED** by seed variance.
   Adding a 5th symbol helps primary seed but hurts seeds that were
   already marginal.
2. **ADA is a real signal** — 47.8% WR, positive PnL, +24.62% share
   on primary. Not a filler.
3. **SOL and NEAR are chronic losers** on primary seed (-1.66, -2.73
   wpnl). The 4-symbol era's SOL/NEAR were sometimes winners,
   sometimes losers; now with ADA they're consistently losers.
4. **The primary seed result is the best v2 run yet** but the
   10-seed mean is worse. This is the "primary-seed vs mean"
   trade-off we've seen before.
5. **IS/OOS ratio of 0.88x suggests underfitting**, not overfitting.
   The 5-symbol config may be too diluted.

## iter-032 options (ranked)

### Option A — Drop SOL, test 4-symbol w/ ADA (DOGE+XRP+NEAR+ADA)

- SOL is net-negative on 5 of 10 seeds and contributes 0% positive
  share on primary seed (SOL wpnl = −1.66).
- Dropping SOL gives 4 symbols; rule reverts to n=4 (max≤50%).
- ADA is a real contributor so keeping it is clearly beneficial.
- Expected: concentration drops modestly, OOS mean improves (less
  drag from SOL's chronic losses).

### Option B — Fix seed variance via Optuna constraints

- Cap Optuna's confidence_threshold upper bound (prevents extreme
  selective configs)
- Warm-start Optuna from a known-good seed's hyperparameters
- Requires non-trivial code change to `lgbm.py`

### Option C — Ensemble average 5 seeds per model

- Currently each model uses 1 seed. Ensemble-averaging 5 seeds per
  model should reduce per-seed noise.
- Runtime goes up 5x per model (75 minutes per seed → 6+ hours for
  10-seed validation).
- Requires `ensemble_seeds` parameter support which already exists.

### Option D — Drop both SOL and NEAR, keep XRP+DOGE+ADA (3 symbols)

- Aggressive: the 3 strongest primary-seed contributors only.
- n=3 rule: max≤55%, mean≤50%, ≤1 above 45%.
- Primary seed max-share would be XRP 48.71% — JUST under the n=3 rule.
- Expected to pass concentration AND be cleaner overall.

**Recommended iter-032**: **Option D** (drop SOL and NEAR, keep
XRP+DOGE+ADA). Reasoning: these 3 symbols are the ONLY net-positive
contributors on primary seed. Dropping noise-filler symbols is simpler
than tuning Optuna and has higher expected value than keeping the
5-symbol config. If the 3-symbol config passes concentration AND has
Sharpe comparable to iter-029, it becomes the new baseline.

**Stretch goal**: if Option D fails concentration or Sharpe, try
Option B (Optuna constraint) in iter-033.

## MERGE / NO-MERGE

**NO-MERGE**.

Gating criteria:
- Seed concentration: **FAIL** (all 4 sub-rules)
- Mean OOS monthly > 0.80: **FAIL** (+0.6605)
- Profitable ≥8/10: **FAIL** (7/10)
- OOS PF > 1.2: PASS (primary 1.65)

Only 1 of 4 gates pass. Clean NO-MERGE.

**Baseline stays at iter-v2/029.** The audit code and n-symbol-aware
skill updates are the iter-031 contribution to infrastructure — they
should be cherry-picked to quant-research regardless.

**Next iteration**: iter-v2/032 = Drop SOL and NEAR, run 3-symbol
portfolio (DOGE + XRP + ADA). Test the "keep only net-positive
contributors" hypothesis.
