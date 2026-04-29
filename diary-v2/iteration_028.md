# Iteration v2/028 Diary

**Date**: 2026-04-15
**Type**: EXPLORATION (Optuna trials 10 → 25)
**Parent baseline**: iter-v2/026 (BTC features)
**Decision**: **NO-MERGE** — breakthrough OOS mean but concentration fails

## Results — best 10-seed mean yet on OOS

| Metric | Value |
|---|---|
| Mean IS monthly Sharpe | **+0.4269** |
| **Mean OOS monthly Sharpe** | **+1.0796** ← **ABOVE 1.0 for the first time** |
| Mean OOS trade Sharpe | +1.2320 |
| **Profitable seeds** | **10/10** |
| Balance ratio | 2.53x (slightly above target range) |

**Primary seed 42**:
| Metric | iter-v2/019 | iter-v2/028 |
|---|---|---|
| IS trade Sharpe (qs) | +0.57 | **+1.1280** (first >1.0!) |
| IS monthly Sharpe | +0.50 | +0.8260 |
| OOS trade Sharpe (qs) | +2.45 | +1.6221 |
| OOS monthly Sharpe | +2.34 | +1.4081 |
| Balance ratio | 4.68x | **1.44x** |
| IS MaxDD | 72.24% | 55.27% |

## Individual seed distribution

| Seed | IS monthly | OOS monthly | OOS trade |
|---|---|---|---|
| 42 | +0.83 | +1.41 | +1.74 |
| 123 | +0.33 | **+1.76** | +1.98 |
| 456 | +0.18 | **+1.29** | +0.67 |
| 789 | +0.55 | +1.19 | +1.36 |
| 1001 | +0.26 | +0.48 | +0.57 |
| 1234 | +0.53 | +0.91 | +1.34 |
| 2345 | +0.48 | +0.94 | +1.59 |
| 3456 | +0.36 | **+1.27** | +1.64 |
| 4567 | +0.73 | **+1.52** | +1.38 |
| 5678 | +0.02 | +0.03 | +0.05 |

**6 of 10 seeds have OOS monthly > 1.0**. Seed 5678 is the only
near-breakeven seed (+0.02 / +0.03). This is the most consistent
cross-seed result in iters 021-028.

## Why it didn't MERGE — concentration failure

Primary seed 42 per-symbol OOS:

| Symbol | Trades | Weighted PnL | **Share** |
|---|---|---|---|
| **XRPUSDT** | **15** | **+54.05** | **73.43%** ← STRICT FAIL |
| DOGEUSDT | 29 | +12.54 | 17.04% |
| NEARUSDT | 20 | +4.75 | 6.45% |
| SOLUSDT | 32 | +2.27 | 3.09% |

**XRP is 73.43% of OOS on primary seed**. The 25-trial Optuna is
TOO SELECTIVE — it found highly-profitable XRP signals (15 trades
averaging +3.6% per trade) but over-weights XRP relative to the
other symbols. Rule limit is ≤50%.

## NEAR transformation

Side effect: NEAR's IS contribution **flipped from −20.50 to
+125.96** (primary seed). The 25-trial Optuna finds hyperparameters
that actually work for NEAR's 2022 bear distribution. This is the
biggest per-symbol improvement in the entire v2 track.

The problem is the model's overall confidence threshold gets so
high that OOS trades concentrate on XRP (where its best signals
live). NEAR and SOL get fewer OOS trades.

## Why 25 trials works (mostly)

More Optuna trials produce hyperparameter sets that generalize
better across OOS periods. With 10 trials, Optuna finds
local-minimum hyperparameters that work on some IS but not OOS
(iter-019's monthly OOS only on primary). With 25 trials, Optuna
finds more robust hyperparameter sets that generalize to OOS,
lifting cross-seed OOS mean above 1.0.

**Cost**: 2.5x slower training (~15-20 min per seed, ~3 hours
for 10-seed validation).

## Key insight

**The 25-trial Optuna is a strong win for OOS but breaks
concentration**. Need to find a middle ground:
1. Fewer Optuna trials (15?) — less selective, better distribution
2. Same 25 trials + constrain confidence_threshold range
3. Same 25 trials + per-symbol position cap

## Next iteration (iter-v2/029)

**Try 15 Optuna trials** as middle ground. Should preserve most
of the OOS improvement without the extreme concentration. Runtime
~1.5x iter-019 (vs 2.5x for iter-028).

## MERGE / NO-MERGE

**NO-MERGE** despite the strongest aggregate result yet.
Concentration 73.43% > 50% strict rule. The OOS mean > 1.0
breakthrough is a very strong signal for the direction (more
Optuna trials), but the specific 25-trial config over-concentrates.

Next: iter-029 = 15 Optuna trials, goal both-means >1.0 AND
concentration ≤50%.
