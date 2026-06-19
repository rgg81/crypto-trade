# portfolio-iteration EXPLORATION-003 — trend-agreement gate (NEGATIVE, rejected)

**Axis:** one change vs the iter-002 TS-trend baseline — only hold a coin when its multi-horizon trend
signals agree (|mean-sign| >= gate). Hypothesis: filtering whipsaw lifts OOS / cuts DD.
**Code:** `analysis/portfolio/iter_003_gate.py`.

## Result
| gate | IS | OOS | maxDD | verdict |
|---|---|---|---|---|
| 0.0 (baseline) | +1.68 | +0.50 | −28% | — |
| 0.5 (≥3/4 agree) | +1.68 | +0.49 | −28% | no effect |
| 1.0 (all 4 agree) | +1.64 | −0.13 | −38% | WORSE |

## Read
The inverse-vol sizing already scales position by trend-strength continuously (the mean-sign
magnitude), so a hard agreement gate is redundant (0.5 ≈ baseline) or harmful (1.0 concentrates into
fewer unanimous trends → less diversification → worse DD and negative OOS). 

## Verdict: EXPLORATION-NEGATIVE — rejected, baseline unchanged.
## Next
- iter-004: add REAL funding P&L to the held perp legs (currently ignored) — more realistic, and a
  small funding tilt (prefer funding-positive positions where it doesn't fight the trend) may be
  additive income. Keep only if net Sharpe rises.
