# portfolio-iteration EXPLORATION-010 — magnitude vs sign signals (REJECT)

**Agent-driven** (quant-researcher), canonical iter_005 net. Replace binary SIGN with continuous
MAGNITUDE: trend = mean clip(ret_h/vol_h, ±C); carry = −cross-sectional z(funding). Code:
`analysis/portfolio/iter_010_magnitude.py`.

## Result vs canonical SIGN baseline (IS +1.30 / OOS +1.37 / DD −23%)
| variant | IS | OOS | maxDD |
|---|---|---|---|
| A magnitude-trend / sign-carry | +1.31 | +0.98 | −37% |
| B sign-trend / magnitude-carry | +1.48 | +0.71 | −28% |
| C magnitude / magnitude | +1.34 | +1.02 | −28% |

Robustness sweep (clip C ∈ {1.5,2,3,4,∞}): every variant strictly below the +1.37 SIGN OOS. Rank-trend
(pure magnitude) catastrophic (IS +0.51 / OOS −0.23 / DD −69%).

## Read — REJECT
- **Cannibalization** on magnitude-carry (B): IS +1.48 but OOS +0.71 (the IS-up/OOS-down trap).
- **Magnitude-trend collapses the walk-forward λ to 0** (A: 12/18 OOS months; C: 17/18) — a graded
  trend removes the structural reason carry helped, so the honest selector drops carry. Trend STRENGTH
  is a noisy mean-reverting overlay; **SIGN is the robust sufficient statistic** for perp trend.

## Verdict: REJECT. SIGN baseline stands (OOS +1.37). 4th consecutive reject.
## State: solid validated plateau — see report. Last untried DD lever = correlation/regime gross overlay.
