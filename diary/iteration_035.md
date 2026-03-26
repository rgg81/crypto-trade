# Iteration 035 Diary - 2026-03-26 — EXPLORATION
## Merge Decision: NO-MERGE
OOS Sharpe -0.08 < baseline +1.33. Per-symbol models worse than pooled.

## Key Finding
The pooled BTC+ETH model outperforms separate models. BTC and ETH share structure — training together is beneficial. This is the OPPOSITE of what we hypothesized.

Also note: with symbol-scoped feature discovery (iter 033 fix), models see 187 features (vs 106 on main). This may explain why per-symbol results differ from iter 012 (which used main's 106 features).

## Exploration/Exploitation Tracker
Last 10: [E, E, X, E, E, E, X, X, E, **E**] → 7/10 = 70%

## Next Iteration Ideas
1. **MERGE the symbol-scoped discovery fix to main** — this is a critical bug fix that affects all future iterations
2. **Test pooled BTC+ETH with 187 features** (from regenerated parquets with macro.py removed) — the feature count difference (187 vs 106) may matter
3. **Slow features via 3x lookback multiplier** — regenerate parquets with indicators at daily-equivalent periods
