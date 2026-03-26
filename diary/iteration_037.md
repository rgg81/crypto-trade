# Iteration 037 Diary - 2026-03-26 — EXPLORATION
## Merge Decision: NO-MERGE
OOS -0.55 < baseline +1.33. Slow features didn't help.

## Feature Count: 118 (106 original + 12 slow that survived global intersection from 760 symbols)

## Comprehensive Feature Exploration Summary (iters 026-037)
| Iteration | Features Added | Feature Count | OOS Sharpe | Result |
|-----------|---------------|---------------|-----------|--------|
| 016 (base)| None | 106 | **+1.33** | BASELINE |
| 026 | Calendar + interaction (injected) | 113 | +0.28 | NO-MERGE |
| 029 | Long-period only (dropped short) | 93 | -0.94 | NO-MERGE |
| 033 | 13 macro (regenerated) | 198* | +0.62 | NO-MERGE |
| 034 | 2 macro (regenerated) | 187* | -0.55 | NO-MERGE |
| 036 | None (symbol-scoped discovery) | 185 | +0.11 | NO-MERGE |
| 037 | 12 slow/daily (regenerated all) | 118 | -0.55 | NO-MERGE |
*symbol-scoped discovery, not global intersection

## CONCLUSION
The 106-feature intersection is a LOCAL OPTIMUM for features. Every modification — adding, removing, or replacing features — makes things worse. The model has found its signal in these specific 106 features and the 0.85 confidence threshold.

## IS/OOS both positive remains unachieved. IS is -0.96 and appears structural (2021 cold-start + 2022 bear market with model trained on bull data only).

## Exploration/Exploitation Tracker
Last 10: [E, X, E, E, E, X, X, E, E, **E**] → 7/10 = 70%
