# iter-v2/065 Engineering Report — NEAR cap sweep

## Sweep results

All measurements from iter-v2/059-clean trade list, NEAR cap applied as
post-processing (`weight_factor ×= cap`, `weighted_pnl ×= cap`). All other
symbols unchanged.

| cap | IS mo | OOS mo | Combined | OOS day | Max share | NEAR share | Max per-symbol status |
|---|---|---|---|---|---|---|---|
| 1.00 (baseline) | +1.0421 | +1.6590 | +2.701 | +1.6626 | 44.44% NEAR | 44.44% | FAIL n=4 inner 40% |
| 0.90 | +1.0403 | +1.5853 | +2.626 | +1.6380 | 41.86% NEAR | 41.86% | FAIL |
| 0.85 | +1.0392 | +1.5472 | +2.586 | +1.6239 | 40.47% NEAR | 40.47% | FAIL (marginal) |
| **0.80** | **+1.0378** | **+1.5084** | **+2.546** | **+1.6084** | **39.02% NEAR** | **39.02%** | **PASS** |
| 0.75 | +1.0363 | +1.4690 | +2.505 | +1.5916 | 37.74% XRP | 37.50% | PASS |
| 0.70 | +1.0346 | +1.4291 | +2.464 | +1.5733 | 38.71% XRP | 35.89% | PASS |

## Findings

1. **0.85 is marginal** — NEAR share drops to 40.47%, fractionally over
   40% cap. Not robust.
2. **0.80 is the sweet spot** — NEAR drops to 39.02% (1pp margin under
   40% cap). OOS monthly drops 9.1% (+1.659 → +1.508), well within
   the 15% balance guard.
3. **0.75 and below flip max-symbol to XRP** — further cap gives no
   concentration benefit (XRP becomes the bottleneck) and only more
   Sharpe cost.

## Recommended cap: 0.80

| Metric | baseline (1.00) | cap 0.80 | Δ |
|---|---|---|---|
| IS monthly | +1.0421 | +1.0378 | −0.4% |
| OOS monthly | +1.6590 | +1.5084 | −9.1% |
| Combined | +2.701 | +2.546 | −5.7% |
| Max share | 44.44% NEAR | **39.02% NEAR** | −5.4pp (PASS n=4 40% cap) |

## Validation plan — iter-v2/066

Parameter-sweep-only analysis is informational. A proper MERGE candidate
requires:

1. Full baseline run with `PER_SYMBOL_POSITION_SCALE={"NEARUSDT": 0.80}`
   in `run_baseline_v2.py` on fresh data (next 24h candles) — confirms
   cap works on live pipeline.
2. 10-seed validation to confirm mean concentration ≤ 45% and ≤1 seed
   above 40% across the full seed sweep.
3. v2-v1 correlation check.

Cheap alternative: since iter-v2/064 applied 0.70× via the same
post-processing as the sweep, we already know the code works end-to-end.
The 10-seed sweep is the main outstanding validation for MERGE readiness.

## Verdict

**NO-MERGE** (informational iteration). iter-v2/065 is a parameter
sweep, not a candidate baseline. Its deliverable is the optimal cap
value (0.80) for use in iter-v2/066.
