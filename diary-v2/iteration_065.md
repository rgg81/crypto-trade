# iter-v2/065 Diary

**Date**: 2026-04-23
**Type**: EXPLOITATION (parameter sweep)
**Parent baseline**: iter-v2/059-clean
**Decision**: **NO-MERGE** (informational iteration — sweep output feeds iter-v2/066)

## Summary

Swept NEAR position cap across [1.00, 0.90, 0.85, 0.80, 0.75, 0.70].
Identified **0.80 as the optimal cap**: NEAR drops from 44.44% to 39.02%
(passes n=4 40% inner cap), OOS monthly Sharpe drops only 9.1% (+1.659 →
+1.508), combined monthly −5.7%.

0.85 is marginal (40.47% — just over 40%). 0.75 and below are wasteful
(XRP becomes the bottleneck at 37.74%; further NEAR cap gives no
concentration benefit).

## Full table

```
  cap |   IS mo |  OOS mo |   comb | OOS day |   max% sym       |  NEAR%
 1.00 | +1.0421 | +1.6590 | +2.701 | +1.6626 | 44.44% NEARUSDT  | 44.44%  ← baseline, FAILS 40%
 0.90 | +1.0403 | +1.5853 | +2.626 | +1.6380 | 41.86% NEARUSDT  | 41.86%
 0.85 | +1.0392 | +1.5472 | +2.586 | +1.6239 | 40.47% NEARUSDT  | 40.47%  ← marginal
 0.80 | +1.0378 | +1.5084 | +2.546 | +1.6084 | 39.02% NEARUSDT  | 39.02%  ← sweet spot
 0.75 | +1.0363 | +1.4690 | +2.505 | +1.5916 | 37.74% XRPUSDT   | 37.50%
 0.70 | +1.0346 | +1.4291 | +2.464 | +1.5733 | 38.71% XRPUSDT   | 35.89%  ← iter-v2/064 (too aggressive)
```

## Why 0.80 is the right call

- **Concentration**: NEAR 39.02%, 0.98pp margin under 40% cap. Small
  margin but PASSES.
- **Sharpe**: 5.7% combined Sharpe regression vs baseline. Well within
  the skill's 15% balance-guard tolerance.
- **Monotonic tradeoff**: every additional 0.05 of cap costs ~4% of OOS
  monthly Sharpe. 0.80 is the point where concentration PASSES without
  over-spending.

## IS is immune to the cap

IS monthly Sharpe is near-flat across all caps (+1.042 → +1.035 at 0.70).
This is because NEAR's IS contribution was only a small fraction of IS
positive wpnl (IS is dominated by other symbols). Reducing NEAR's IS size
doesn't meaningfully change IS Sharpe.

This has a useful deployment implication: the cap is a pure OOS-concentration
fix, not an IS-performance drag.

## MERGE criteria — iter-v2/065

Not applicable. This iteration produced no new model. The sweep is
informational, feeding iter-v2/066's config.

## Next Iteration Ideas — iter-v2/066

### Primary: Full baseline run with NEAR cap = 0.80

1. Apply `PER_SYMBOL_POSITION_SCALE={"NEARUSDT": 0.80}` in
   `run_baseline_v2.py`
2. Fetch fresh data (mandatory pre-flight)
3. Run the standard single-seed baseline (~2.5h). Compare against
   iter-v2/059-clean line-by-line.
4. If passes all MERGE criteria, run 10-seed validation
   (`uv run python run_baseline_v2.py --seeds 10` — ~24h) to confirm:
   - Mean concentration ≤ 45% (n=4 mean rule)
   - ≤1 of 10 seeds above 40% (n=4 inner rule)
   - ≥7/10 seeds profitable

### Secondary: consider v2-v1 correlation
Not measured in iter-v2/065. The MERGE criterion requires v2-v1
correlation < 0.80. Need to compute this after iter-v2/066's full run.

### Alternative: more symbols (iter-v2/067+)
If iter-v2/066 succeeds, explore adding a proper Gate-3-screened 5th
symbol (to reduce position cap dependence and improve diversification
further). Candidates to screen: BCH, UNI, FIL, TRX. Avoid AAVE (already
tried iter-v2/063, failed).
