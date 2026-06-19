# portfolio-iteration EXPLORATION-014 — RISK-PARITY multi-factor combiner (PROMOTE-WORTHY, with a DD caveat)

**Agent-driven** (user mandate): this is THE path-forward iter_013 mandated. iter_012 confirmed the
standalone taker-flow factor (+1.59 OOS, 2×-cost-robust, orthogonal to trend +0.23 / carry +0.05,
residual-additive β +0.03); iter_013's joint-(λ,γ) walk-forward proved the factor is REAL and
PAST-picked in 100% of OOS months — but the additive blend coefficient γ is a CORNER solution (OOS
Sharpe monotone in γ, the WF pins it at whatever the grid edge is, 0.30→0.50→…). The mandated fix:
weight the three factors by their OWN realized risk, with NO tunable factor coefficient, so the
combiner physically cannot run to a corner. Code: `analysis/portfolio/iter_014_riskparity.py`.

**Method — combine standalone vol-targeted factor NETS by RISK PARITY (no blend coefficient):**
1. Build each factor as a clean standalone vol-targeted net, reusing EACH factor's OWN canonical
   per-coin sizing byte-for-byte:
   - `trend` = mean sign of trailing returns {21,42,84,168}, inverse-vol sized (iter_002/005 leg).
   - `carry` = −sign(trailing-9 funding), inverse-vol sized (iter_004/005 leg).
   - `flow` = xsec z-score of `(taker_buy/vol−0.5).rolling(42).mean()`, MOMENTUM, sized by the
     z-score itself — NO extra `/rvol` (the z-score IS flow's risk-normalizing transform;
     re-dividing by rvol would be a different, inflated, non-canonical signal). Reproduces
     iter_012.standalone EXACTLY.
2. `weight_i,t = (1/realized_vol_i,t) / Σ_j (1/realized_vol_j,t)`, realized vol PAST-ONLY via
   `factor_net.rolling(84).std().shift(1)` (Σ weights = 1, a risk-determined simplex). Combined =
   `Σ_i weight_i,t · factor_net_i,t`, then a FINAL portfolio vol-target. The only knob is the vol
   window (robustness-swept {42,84,168}); no factor coefficient to grid.

**HARD sanity gates (both PASS — verified before reading any combine):**
- trend factor net == `iter_005` fixed-λ=0 (pure trend): **PASS**
- flow factor net == `iter_012` standalone MOMENTUM 1× (IS +1.67 / OOS +1.59): **PASS**
- Baseline reproduced live: WF-λ trend+carry **IS +1.30 / OOS +1.37 / DD −23%** (n=16 OOS months).

## (a) Standalone factor nets (each vol-targeted, real funding, 1× taker)
| factor | IS | OOS | maxDD | netTot |
|---|---|---|---|---|
| trend | +1.61 | +0.73 | −27% | +1113% |
| carry | −0.03 | +1.07 | −67% | −11% |
| **flow** | **+1.67** | **+1.59** | −38% | +3495% |

Net-return correlation (IS): trend–carry **−0.24**, trend–flow **+0.12**, carry–flow **+0.19** — the
three factors are genuinely low-correlated, exactly the regime where risk-parity weighting is the
principled tool (and where ERC ≈ inverse-vol). Flow is the strongest single factor; carry is the
diversifier (negative-corr to trend, OOS-positive) but carries a −67% standalone DD.

## (b) Risk-parity {trend,carry} (2-factor) — is risk-parity itself a fair comparator?
| | IS | OOS | maxDD | netTot |
|---|---|---|---|---|
| WF-λ baseline (iter_005) | +1.30 | +1.37 | −23% | +578% |
| **RP-2 {trend,carry}** | **+1.37** | **+1.48** | −34% | +1011% |
| Δ vs baseline | +0.07 | **+0.11** | −11% (deeper) | — |

RP-2 OOS +1.48 is **within 0.20 of** the WF-λ baseline's +1.37 → risk-parity is a FAIR comparator on
the same two factors (it does not cripple the baseline; it is a slightly different, equally-valid
weighting that holds weights at a stable ~0.50/0.50). Gate [1] PASS. So any RP-3 lift over RP-2 is
attributable to FLOW, not to swapping the weighting scheme.

## (c) Risk-parity {trend,carry,flow} (3-factor) — does adding flow lift OOS?
| | IS | OOS | maxDD | netTot |
|---|---|---|---|---|
| WF-λ baseline | +1.30 | +1.37 | −23% | +578% |
| RP-2 {trend,carry} | +1.37 | +1.48 | −34% | +1011% |
| **RP-3 {trend,carry,flow}** | **+2.06** | **+2.40** | −29% | +6450% |
| Δ vs WF-λ baseline | +0.76 | **+1.03** | −5pp (deeper) | — |
| Δ vs RP-2 (flow's marginal) | +0.70 | **+0.92** | +6pp (DD cut vs RP-2) | — |

**Adding flow at a risk-determined weight lifts OOS +1.03 over the deployable baseline** (to +2.40),
and **+0.92 as flow's pure risk-set marginal over RP-2**. Both OOS years improve broadly:
| OOS year | RP-3 net% | baseline net% |
|---|---|---|
| 2025 | +54% | +14% |
| 2026 | +50% | +32% |

## (d) Factor-weight TIMELINE — flow's weight is a STABLE ~1/3, NOT a corner
**Mean risk-parity weight per year:**
```
year      trend   carry    flow
IS 2020    0.33    0.33    0.37
IS 2021    0.34    0.34    0.33
IS 2022    0.33    0.33    0.33
IS 2023    0.33    0.33    0.35
IS 2024    0.33    0.33    0.34
OOS2025    0.33    0.34    0.33
OOS2026    0.35    0.33    0.32
```
**Flow OOS weight: mean 0.33, range [0.19, 0.61].** This is the decisive answer to iter_013's open
question. The iter_013 (λ,γ) blend ran γ to the grid edge (0.30→0.50, monotone, no interior optimum);
here flow's exposure is set by its OWN realized risk to a STABLE ~1/3 share — the same order as trend
and carry — and the OOS still beats baseline by +1.03. The +1.03 lift is **NOT** a corner artifact:
flow earns a natural, risk-determined weight and the portfolio improves at that weight.

## Robustness — vary the risk-parity vol-estimation window (not knife-edge)
| win | IS | OOS | dOOS vs base | maxDD | metaTurn | flowW_OOS |
|---|---|---|---|---|---|---|
| 42 | +1.97 | +2.31 | +0.94 | −35% | 0.017 | 0.34 |
| **84** | **+2.06** | **+2.40** | **+1.03** | −29% | 0.009 | 0.33 |
| 168 | +2.15 | +2.62 | +1.25 | −30% | 0.004 | 0.32 |

Every vol window: OOS dramatically beats baseline (+0.94 → +1.25), flow weight stays ~0.32–0.34.
**Not a tuned cell** — the result is a smooth function of the one structural knob.

## Second non-tunable scheme — ERC (equal-risk-contribution, correlation-aware) AGREES
**ERC-3: IS +1.69 / OOS +2.55 / DD −26% / flowW_OOS 0.36.** ERC equalizes each factor's CONTRIBUTION
to portfolio variance (uses the full past-only covariance, not just standalone vols) via the correct
multiplicative Maillard/Spinu fixed point. It corroborates inverse-vol risk-parity (OOS +2.55 vs
+2.40, both ~+1.1 over baseline), flow's weight ~0.36 — the conclusion is **scheme-robust**, not an
artifact of naive inverse-vol. (Implementation note: the first ERC pass had a fixed-point bug —
`w←1/(cov·w)` instead of the correct `w←w/(cov·w)` — which collapsed ERC to +0.47 and would have been
a spurious falsifier; caught and fixed before the verdict. With low cross-factor correlation, ERC
SHOULD ≈ inverse-vol, so the original +0.47 was implausible on its face.)

## Turnover + cost-stress (honest)
Factor-weight meta-rebalancing turnover (mean L1 drift/candle): **0.009** — the risk weights are
slow-moving (the simplex barely whips between factors). Charging the meta-layer an explicit extra
taker cost: 1× → OOS +2.37, **2× → OOS +2.34** (still ≈ +1 over baseline). The lift is NOT a
turnover-eaten or gross-only mirage — it survives a 2× taker stress on the combiner's own rebalancing,
on top of the 1× coin-level cost already booked inside each factor net.

## Pre-registered falsifier verdict (n=16 OOS months)
| gate | result |
|---|---|
| [1] RP-2 {trend,carry} a FAIR comparator (OOS within 0.20 of WF-λ +1.37) | **PASS** (+1.48) |
| [2] RP-3 OOS lift ≥ +0.20 over WF-λ baseline (above noise) | **PASS** (dOOS +1.03) |
| [3] flow's risk-set marginal lifts OOS (RP-3 − RP-2 ≥ +0.10) | **PASS** (dOOS +0.92) |
| [4] flow OOS weight STABLE non-corner (0.15..0.55, not gridded) | **PASS** (0.33) |
| [6] robust: ALL vol-window cells OOS ≥ baseline−0.05 AND flow non-corner | **PASS** |
| [7] cost-honest: survives 2× meta-cost OOS ≥ baseline−0.05 | **PASS** (+2.34) |
| [8] ERC (correlation-aware) AGREES (OOS ≥ baseline−0.05) | **PASS** (+2.55) |
| [5] (quality) maxDD vs baseline −23% | **−29% — DEEPER by 5pp** (DD-refinement target) |

## Read — PROMOTE-WORTHY (with a DD caveat); flow's edge SURVIVES a non-tunable weighting
**The KEY question is answered YES.** iter_013 left the deployment question open: does flow's confirmed
edge survive a non-corner, non-tunable weighting, or was the corner-OOS gain just an artifact of
over-tilting toward the single strongest factor? Under risk parity:
- flow earns a STABLE, risk-determined ~1/3 weight (mean 0.33, range 0.19–0.61) — **the corner is
  gone**; there is no coefficient to grid, and the weight does not run to an edge.
- at that natural weight the 3-factor portfolio OOS Sharpe lifts **+1.03 to +2.40** (flow's pure
  risk-set marginal over RP-2 is **+0.92**), robust across the vol window, cost-honest at 2×, and
  corroborated by the correlation-aware ERC scheme. This is a real, non-tunable portfolio lift — the
  clean vehicle iter_013 mandated.

**The honest blemish — DD does NOT improve.** The user asked specifically "does adding flow lift OOS
AND cut DD?" The answer is: it lifts OOS hugely, but maxDD is **−29% vs the baseline's −23%** (deeper
by 5pp, tripping the strict ≤5pp quality gate [5]). The cause is mechanical and diagnosable: the carry
factor has a −67% standalone DD, and risk parity gives it a full ~1/3 risk share, so carry's drawdowns
enter the combined book at a larger weight than the WF-λ baseline's carry tilt (which sits ~0.25). The
Sharpe nearly DOUBLES (+1.37 → +2.40), so the risk-ADJUSTED gain dominates — but on the project's
"lift OOS AND cut DD" bar, flow lifts return without cutting DD. This is a refinement target, not a
reject of the edge.

## Verdict: PROMOTE-WORTHY (with a DD caveat) — recommend CONFIRM (held-OOS + full gauntlet) WITH a DD-targeting refinement, pending the separate critic. Baseline UNCHANGED until that critic PASS.
Every merge-relevant gate (fairness, material OOS lift, flow's positive marginal, non-corner weight,
vol-window robustness, 2×-cost honesty, ERC scheme-agreement) PASSES. The one failing criterion is the
DD quality gate, which is a known, mechanical consequence of carry's high standalone DD at a 1/3 risk
share — addressable by a per-factor DD brake or a vol-target ceiling on the carry leg (a separate,
pre-registered refinement), NOT a reason to reject a clean non-tunable edge. Per the track's promotion
rule, the baseline stays UNCHANGED (iter_005 WF-λ, IS +1.30 / OOS +1.37 / −23%) until a CONFIRMATION
with a critic PASS — promotion is the orchestrator's call after that review.

## Axis status
- **Risk-parity multi-factor combiner (trend+carry+flow): OPEN — PROMOTE-WORTHY, routed to
  CONFIRMATION.** The non-tunable combiner resolves iter_013's corner problem: flow's confirmed edge
  survives at a STABLE risk-determined ~1/3 weight with an OOS lift of +1.03 (robust, cost-honest,
  ERC-corroborated). This is the first multi-factor portfolio improvement since the carry tilt.
- **Outstanding (the DD-refinement question):** the combined DD (−29%) is 6pp deeper than baseline,
  carried by the carry factor's −67% standalone DD at a 1/3 risk share. The risk-parity weighting
  lifts Sharpe but does not cut DD.

## Next
- **iter-015 (CONFIRMATION-track): held-OOS risk-parity combiner + a DD-targeting refinement.** Reveal
  OOS once under the full gauntlet (per-year robustness, benchmark vs B&H BTC and the equal-weight
  basket, turnover + 2× cost). Layer ONE DD primitive that does NOT tune on OOS: a per-factor drawdown
  brake (de-lever a factor whose own rolling DD breaches an IS-calibrated threshold) OR a vol-target
  ceiling on the carry leg (cap its risk contribution so its −67% standalone DD does not dominate the
  combined book). Pre-register the DD target (combined ≤ −23%, i.e. at least hold the baseline) and the
  Sharpe floor (do not give back the +1.03 OOS lift below +0.20). If both hold → PROMOTE to baseline.
- Adjacent (still open from iter_012/013): a **taker-flow REGIME gate on gross exposure** (market-wide
  aggressive-flow scaling the book — a second, orthogonal lever on the −23% DD), and the roadmap's
  **OI / perp-spot-basis** structural families — now with three confirmed factors (trend, carry, flow)
  cleanly combined, the cross-section is demonstrably not exhausted.
