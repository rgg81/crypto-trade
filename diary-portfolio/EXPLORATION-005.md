# portfolio-iteration EXPLORATION-005 — carry tilt CONFIRMED via walk-forward λ (OOS +1.22)

**Axis:** the honesty check for iter-004's carry tilt. Select λ per month on the PAST 24mo only (best
past Sharpe), no OOS peek. Code: `analysis/portfolio/iter_005_wf_lambda.py`. Grid λ∈{0,0.1,0.25,0.4}.

## Result
| config | IS | OOS | maxDD | net total |
|---|---|---|---|---|
| **WALK-FORWARD λ (no OOS peek)** | **+1.21** | **+1.22** | −29% | +503% |
| fixed λ=0 (trend only) | +1.65 | +0.49 | −29% | +1124% |
| fixed λ=0.25 | +1.67 | +1.31 | −27% | +1259% |

OOS λ-picks: **0.25 chosen 14/18 months**, 0.4 ×3, 0.1 ×1 — the walk-forward independently converges
on ~0.25 from past data alone.

## Read — CONFIRMED
Selecting λ honestly (past-only) delivers OOS **+1.22**, essentially the full fixed-λ=0.25 lift
(+1.31). The carry tilt is a REAL, walk-forward-validated improvement over trend-only (OOS +0.49) —
NOT OOS-selection bias. (Walk-forward IS is lower, +1.21, because the early period warms up / switches
λ; the OOS +1.22 is the honest deployable number.)

## Verdict: CONFIRMED — trend+carry-tilt (walk-forward λ) PROMOTED to baseline.
BASELINE_PORTFOLIO.md updated. A validated long/short top-20 perp edge: OOS Sharpe +1.22, −29% DD,
positive every year, plain taker fees, no HFT/MM/VIP.

## Next (little by little)
- iter-006: walk-forward the trend horizon mix {7,14,28,56d} (currently equal-weight).
- then: short-term reversal overlay; regime/vol gross-scaling; per-coin caps to trim the −29% DD.
