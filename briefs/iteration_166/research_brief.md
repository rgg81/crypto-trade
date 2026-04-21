# Iteration 166 Research Brief

**Date**: 2026-04-21
**Role**: QR
**Type**: **EXPLOITATION** (seed-robustness validation, post-MERGE)
**Previous iteration**: 165 (MERGE — LTC replaces BNB, OOS Sharpe +1.27 at seed=42)
**Baseline**: v0.165 (A+C+LTC, OOS Sharpe +1.27)

## Section 0 — Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

Iter 165 merged A+C+LTC as the new baseline under the diversification exception, using only `seed=42` for Model D (LTC). The skill mandates 5-outer-seed validation before a merge is considered robust. This iteration runs Model D (LTC) with outer seeds 123, 456, 789, 1001 and confirms or revokes the iter-165 merge.

Models A and C are inherited from iter 152 baseline (seed=42 only); their seed robustness is not tested here — that would require another 8+ hours of backtests and Models A, C were not altered in iter 165. The risk contained by this iteration is specifically: *does the LTC model survive seed changes?*

## Research Analysis (post-MERGE → 2 categories)

### F — Statistical Rigor

The Gate 3 seed=42 numbers (IS Sharpe +0.60, 155 trades) are a single observation. The skill's seed validation gate exists to distinguish "real signal" from "lucky seed". Pre-registered pass criteria:
1. **Mean OOS Sharpe across 5 seeds > 0**
2. **At least 4 of 5 seeds have OOS Sharpe > 0**

If either fails, iter 165 merge is **revoked** (revert BASELINE.md and the merge commit on main, re-open iter-165 branch for record).

### B — Symbol Universe (post-addition stability)

LTC was added to the portfolio in iter 165. This iteration doesn't change the universe — it validates that LTC's contribution is stable across seeds.

## Configuration

Runner: `run_iteration_166.py`. It runs the SAME LTC config as iter 165 four times in a row, sweeping outer seed across {123, 456, 789, 1001}. Each run uses `yearly_pnl_check=True` so a bad seed aborts after year-1. Each run's IS and OOS metrics are written to `reports/iteration_166/seed_<N>/comparison.csv`.

All other parameters identical to iter 165.

## Expected Outcomes

- **Strong pass**: 5/5 seeds profitable OOS, mean OOS Sharpe > 0.2 → iter 165 merge is robust. Baseline v0.165 stands.
- **Marginal pass**: 4/5 profitable, mean > 0 → borderline but meets the skill's threshold. Consider revisiting LTC config in iter 167.
- **Fail**: < 4/5 profitable OR mean < 0 → iter 165 merge is reverted. Baseline reverts to iter-152 reproduction (OOS Sharpe +0.99).

## Exploration/Exploitation Tracker

Window (157-166): [X, X, X, X, E, E, E, E, E, X] → **5E / 5X**, 50% E, above the 30% floor.

## Commit Discipline

- Brief → `docs(iter-166): research brief`
- Runner → `feat(iter-166): LTC seed validation runner`
- Engineering report (after all 4 seeds) → `docs(iter-166): engineering report`
- Diary → `docs(iter-166): diary entry` (LAST commit)

## Time Budget

Each seed: ~90 min (or < 15 min if year-1 fail-fast triggers). Total max ~6 hours. If the first additional seed (123) clearly fails, the "First Seed Rule" still allows us to STOP and skip 456/789/1001 — a fast NO-MERGE signal.
