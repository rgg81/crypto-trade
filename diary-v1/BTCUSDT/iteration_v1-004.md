# Diary — iter-v1/004 (BTCUSDT) — CONFIRMATION (K=20) of the /003 prune-only config

**Config:** 41-col prune (V1_BTC_PRUNED_ITER002), R2 OFF, **K=20**, n_trials=35, slippage 2bps/side,
same Jun-15 data (matched-K + matched-data vs iter-001 baseline). Clean run (09:32→12:33, 0 failures).
**Feature count verified = 41** (exactly 41 non-zero importances; the run-summary "features=193" is a
COSMETIC reporting bug — global print, not the model's actual columns; flag to fix).

## Verdict: NO-MERGE. iter-001 baseline STANDS.

| | IS Sharpe | OOS Sharpe | ratio | dispersion | IS net | OOS net |
|---|---|---|---|---|---|---|
| iter-001 baseline (K=20) | −0.2793 | +0.6401 | −2.29 | 49.46 | −12.02 | +9.07 |
| iter-003 prune-only (K=3) | +0.1694 | +0.3980 | +2.35 | 34.57 | +7.81 | +5.41 |
| **iter-004 prune-only (K=20)** | **−0.1691** | **+0.4843** | **−2.86** | **45.51** | −7.51 | +6.43 |

**The K=3 screen was a small-K LOTTERY ARTIFACT.** Same config, K=3→K=20: IS Sharpe flipped
+0.17 → −0.17; the "both-positive coherence" did NOT survive. At robust K=20 the prune reverts to an
inversion (negative IS / positive OOS), like the baseline. So it does not clear the
generalization-coherence gate (still an inversion) and is not a clear improvement over iter-001
(IS less-negative −0.28→−0.17 and dispersion 49.5→45.5 at matched K, but OOS lower +0.64→+0.48, still
inverted). **NO MERGE.**

## Key learnings
1. **The K=20 confirmation did exactly its job — caught a K=3 false positive before it became the
   baseline.** Validates the seed rule + confirm-isolates-lottery discipline (user's insistence).
   The Critic's pre-registered K-mismatch warning ("can't attribute at K=3") was vindicated.
2. **A both-positive K=3 screen is necessary-but-NOT-sufficient.** K=3 is lottery-prone; read screens
   skeptically. (Methodology note: consider a cheaper mid-K gate before committing a 6.5h K=20, or
   weight K=3 verdicts as tentative.)
3. The OHLCV feature prune reduces redundancy (dispersion ↓, IS slightly less-negative) but does NOT
   manufacture a robust edge — BTC's IS edge stays negative at robust K. **Pruning isn't enough; new
   orthogonal signal is needed.**

## Next
iter-v1/005 = the FE-flagged orthogonal axis: add NON-OHLCV feature families (funding / OI /
long-short / basis) on the 41-col pruned base, R2 OFF, K=3 screen. This attacks the diagnosed
problem (thin single-factor price-only edge) rather than re-cutting price features. Cosmetic fix:
the run-summary "features=N / bounds=" line should print the resolved specialist config, not globals.
