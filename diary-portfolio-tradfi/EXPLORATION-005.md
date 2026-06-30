# EXPLORATION-005 — Multi-horizon within-sector momentum (iter-005)

**Date:** 2026-06-30
**Status:** COMPLETE — **KEPT (new working best)**; PROMISING-INTERMEDIATE (net +0.20, < +0.30 bar). OOS HIDDEN.
**Cadence:** EXPLORATION (IS-only) · **Commit:** `4a62a320` · QR brief `iter-005-brief.md` (`cb562890`)

---

## Hypothesis (QR deep-analysis, probe-grounded)

iter-003's single 12-1m within-sector momentum was gross-capped (+0.29) and bull-only. A multi-horizon blend
should robustify and lift gross; the QR probed alternatives (residual mom −0.24, low-vol −0.76, dispersion
gate inert, risk-parity −0.07) and found the equal-weight {3-1, 6-1, 12-1}m blend best.

## Change (one)

Signal = equal-weight average of `sector_neutralize((close.shift(21)/close.shift(h)-1)/rvol63)` for
h ∈ {63, 126, 252} (each gross-normed to unit gross first), then the iter-003 band δ=0.005.
`analysis/portfolio/tradfi/iter_005_multihorizon.py`.

## IS numbers (trading-day; IS-only)

| Metric | iter-005 | iter-003 |
|--------|----------|----------|
| **Net Sharpe** | **+0.20** | +0.16 |
| Gross Sharpe | **+0.40** | +0.29 |
| Max Drawdown | −31% | −32.8% |
| **Per-regime** | bull +0.38 / bear **−0.90** / chop **+0.26** | +0.22 / −0.08 / −0.10 |
| All-weather | **2/3** (bull+chop) | 1/3 |
| Turnover | 0.114/day | 0.061/day |
| N active | 33 / 39 | — |

Reproduces the QR probe exactly. Non-obvious win: the *weak-standalone* 6-1m sleeve is what flips chop
positive ({3-1,12-1} only → chop −0.30). Turnover ~doubles but maxDD still improves → breadth, not churn.

## Verdict — KEPT (all 4 pre-registered gates pass)

net +0.20 > +0.16 ✓ · all-weather 2/3 ≥ 2/3 ✓ · gross +0.40 ≥ +0.35 ✓ · NOT(bear<−1.3 & net<+0.18) ✓.
Leak-safe (`test_iter005_multihorizon_banded_future_bar_no_leak` + sleeve/neutrality tests, 31/31 green).
OOS hidden. New working stack: multi-horizon within-sector momentum + band.

**The cost (as predicted):** a deeper BEAR (−0.90, the 2022 grind-down momentum crash). Bear is now the
binding regime; "succeed in all markets" requires fixing it before promote.

## Next

- iter-006 (running) = momentum-crash brake (risk-engineer) to make bear survivable without killing bull/chop.
- **User directive (2026-06-30): escalate the toolkit** — replace naive sector-demean weighting with proper
  **portfolio optimization** (mean-variance / risk-model with dollar-beta-sector-neutral + position + turnover
  constraints), test **weekly rebalance**, ground in market-neutral equity literature. This is the iter-007+
  architectural upgrade — the optimizer handles the 62%-Semi/Tech correlation that caps the naive gross.
