# Iteration 075 Diary — 2026-03-28

## Merge Decision: NO-MERGE (baseline reproduction — no improvement)

Baseline reproduced exactly. IS Sharpe +1.22, OOS Sharpe +1.84 — identical to iter 068 baseline. No improvement, but critically important diagnostic: confirms the code is correct and identifies the root cause of recent failures.

**OOS cutoff**: 2025-03-24

## Hypothesis

Revert the symbol-filtered discovery "fix" from iters 073/074 and run with the original global feature intersection (106 features across 760 symbols).

## Results — Exact Baseline Reproduction

| Metric | Iter 075 | Baseline (068) |
|--------|----------|----------------|
| IS Sharpe | +1.22 | +1.22 |
| IS WR | 43.4% | 43.4% |
| IS PF | 1.35 | 1.35 |
| IS MaxDD | 45.9% | 45.9% |
| IS Trades | 373 | 373 |
| OOS Sharpe | +1.84 | +1.84 |
| OOS WR | 44.8% | 44.8% |
| OOS PF | 1.62 | 1.62 |
| OOS MaxDD | 42.6% | 42.6% |
| OOS Trades | 87 | 87 |

Every metric matches. The model is deterministic with ensemble seeds [42, 123, 789].

## Critical Correction: Iter 074 Root Cause Was Wrong

Iter 074 blamed "parquet contamination from failed iterations." This was **INCORRECT**. The real story:

1. The feature code on main was NEVER changed — the 6 original groups always produced 185 features per symbol
2. The baseline used 106 features because `_discover_feature_columns()` scans ALL 760 parquet files and the global intersection is 106 features (some symbols lack certain features)
3. The "discovery fix" from iter 073 (scanning only BTC/ETH) increased features from 106→185
4. 185 features is too many for ~4400 training samples per month — the model overfits

**The global intersection IS the feature selection mechanism.** Removing it destroys the model.

## Exploration/Exploitation Tracker

Last 10 (iters 066-075): [X, E, E, X, E, E, E, E, X, X]
Exploration rate: 6/10 = 60%
Type: EXPLOITATION (baseline reproduction)

## Lessons Learned

1. **The global feature intersection is a feature, not a bug.** Scanning 760 parquet files and keeping only features present in ALL of them acts as aggressive feature selection (185→106). This is essential for the model's performance.

2. **Never "fix" something without understanding why it works.** The discovery scanning all files looked like a bug (why scan 760 files when only trading 2 symbols?), but it was actually the key mechanism preventing feature bloat.

3. **The baseline is reproducible.** With the original code and the same ensemble seeds, the results are deterministic and match exactly. This means we can trust future comparisons.

4. **Iters 069-072 may have been valid failures.** Since those iterations used the original discovery code (no symbol filter), they had 106 features. Their failures (cooldown sweep, feature additions, symbol expansion, calendar features) were genuine — not caused by the discovery issue. The discovery issue only affected iters 073-074.

## Next Iteration Ideas

Now that the baseline is confirmed reproducible, we can explore meaningful changes:

1. **EXPLORATION: Ternary labeling** — Add "neutral" class for timeout trades with |return| < 1%. Changes the classification from binary (long/short) to ternary (long/short/neutral). The iter 073 research found only 18/62 timeouts have |return| < 1%, but this could change with different thresholds.

2. **EXPLORATION: Prediction smoothing** — Majority vote of last 3 predictions before generating a signal. Reduces flip-flopping between directions. Would require tracking recent predictions in the strategy state.

3. **EXPLORATION: Dynamic confidence threshold** — Instead of Optuna choosing a fixed threshold per month, use a percentile-based threshold (e.g., only trade top 20% confidence predictions). Adapts to the model's calibration per month.
