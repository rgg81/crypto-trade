# Iteration 175 Diary

**Date**: 2026-04-22
**Type**: EXPLOITATION (infrastructure — R2 engine implementation)
**Decision**: NO-MERGE (infrastructure only; baseline unchanged)

## Summary

Implemented R2 (drawdown-triggered position scaling) in the backtest engine with unit tests. No portfolio evaluation this iteration — evaluation deferred to iter 176.

## Why infrastructure-only is the right move here

Iter 174's research was conclusive: DOT(R1) adds value but the correlated-drawdown problem blocks the merge. R2 is the specific mitigation the skill prescribes for this case. Implementing R2 is a prerequisite for iter 176's evaluation; doing both in one iteration would mix a code change with a data-dependent merge decision, which is a clean-slate-every-iteration violation.

## Research Checklist

- Infrastructure iteration — no analysis categories claimed.

## Exploration/Exploitation Tracker

Window (166-175): [E, E, E, E, X, E, E, X, E, X] → 7E/3X. Iter 175 as X (code-only).

## Next Iteration Ideas

### Iter 176 — Calibrate and evaluate R2 on v0.173 baseline + DOT

1. QR Phase 1-5: compute IS rolling-30-day pooled drawdown for v0.173 (A+C(R1)+LTC(R1)). Identify the trigger threshold that fires during genuine adverse periods (2022-Q2, 2022-Q4) but not during healthy months. Propose trigger/anchor/floor from evidence.
2. QE Phase 6: run the full portfolio backtest with R2 active (real engine, not simulator).
3. Phase 7-8: evaluate against v0.173. If OOS Sharpe improves AND MaxDD improves materially AND LINK concentration moves toward 30%, MERGE.

### Iter 177+

- R3 (OOD feature detection) — Mahalanobis z-score on current candle feature vector vs. trailing 24-month IS distribution.
- R5 (concentration soft-cap) — per-symbol contribution cap at the runner level.
- Revisit AVAX / ATOM / AAVE with R1+R2 active from the start (they may have been premature rejections).

## lgbm.py Code Review

No changes. R2 is entirely in `backtest.py` + `backtest_models.py`, consistent with R1's clean separation from the model layer.
