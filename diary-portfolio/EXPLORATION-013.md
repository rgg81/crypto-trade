# portfolio-iteration CONFIRMATION-013 — WALK-FORWARD-γ taker-flow (NO-PROMOTE: REAL FACTOR, CORNER WEIGHT)

**Agent-driven** (user mandate): orchestrator implemented the joint-(λ,γ) walk-forward on the canonical
framework and pre-registered the confirmation gates; the verdict is the honest down-call the gates
surface. Baseline UNCHANGED.

**Axis (the CONFIRMATION question from iter_012):** iter_012 PROMOTED the standalone taker-flow factor
(`flow_z` = xsec z-score of `(taker_buy_volume/volume − 0.5).rolling(42).mean()`, MOMENTUM direction)
to a CONFIRMATION — standalone +1.59 OOS, 2×-cost-robust, orthogonal to trend (+0.23) and carry
(+0.05), residual-additive (β +0.03). But as a fixed-γ OVERLAY the blend lift was REJECTED at the
small/mid γ where you would deploy (γ=0.05/0.10 → dOOS −0.04 / +0.10), only material at γ≥0.20,
monotone to the grid edge. The unresolved question: can the taker-flow weight γ EARN its place under
HONEST walk-forward selection — the SAME machinery that legitimized λ in iter_005 — or does it run away
to a corner / collapse to 0 OOS (return-stacking)? Code: `analysis/portfolio/iter_013_confirm.py`.

**Method — extend the iter_005 walk-forward from ONE weight (λ) to TWO (λ,γ):**
`signal = (1−λ)·trend + λ·carry + γ·flow_z`. Precompute the per-(λ,γ) net for the **16-combo coarse
grid** λ∈{0,0.1,0.25,0.4} × γ∈{0,0.1,0.2,0.3}, each **vol-targeted PER-COMBO then stitched** (EXACT
iter_005 ordering — `tf.lam_nets_gamma`, vol_target inside the per-combo loop). WALK-FORWARD-select
(λ,γ) **JOINTLY** per calendar month = the combo with best past-24mo monthly Sharpe (GAP_CANDLES=3
embargo, identical window logic to `iter_005.walkforward`), apply to the test month, stitch. Signal
construction REUSES iter_012 byte-for-byte (`build_flow_z`, `_panels`, `lam_nets_gamma`).

**HARD sanity gates (both PASS — verified before reading any γ>0 cell):**
- `[sanity 1]` γ=0 per-λ nets == `iter_005.lam_nets` byte-for-byte: **PASS**
- `[sanity 2]` joint WF restricted to γ=0 == `iter_005.walkforward` (the +1.37 WF-λ baseline): **PASS**
- Baseline reproduced live: **IS +1.30 / OOS +1.37 / maxDD −23% / netTot +578%**, OOS λ-picks
  {0.1:1, 0.25:13, 0.4:4}.

## Headline — joint walk-forward (λ,γ) vs the WF-λ baseline
| | IS | OOS | maxDD | netTot |
|---|---|---|---|---|
| **WF-λ baseline (γ≡0, =iter_005)** | +1.30 | +1.37 | −23% | +578% |
| **WF-(λ,γ) joint, 16-combo coarse grid** | **+1.61** | **+2.26** | **−20%** | **+1195%** |
| Δ vs baseline | +0.31 | **+0.89** | +4% (DD cut) | +617% |

OOS lift is **broad, not a single-month artifact** — both OOS years improve:
| OOS year | WF-(λ,γ) net% | baseline net% |
|---|---|---|
| 2025 | +29% | +14% |
| 2026 | +40% | +32% |

## γ-selection — γ>0 is reliably PAST-picked (NOT return-stacking)
| | γ-picks (months) |
|---|---|
| IS (year<2025) | {0.0:1, 0.1:4, 0.2:11, 0.3:41} |
| OOS (year≥2025) | **{0.3:18}** |

**OOS months selecting γ>0: 18/18 = 100%.** The walk-forward — choosing on PAST data only — picks the
flow weight in EVERY out-of-sample month. This is the decisive evidence against the return-stacking
hypothesis: a factor only picked in-sample would see its OOS γ-picks collapse to 0. They do the
opposite. Gate B PASS.

### (λ,γ) pick timeline (months per combo, by year)
```
IS  2020: (0,0):1, (0,0.1):4, (0,0.2):1, (0.1,0.2):2, (0.25,0.3):1
IS  2021: (0,0.2):8, (0.1,0.3):2, (0.25,0.3):2
IS  2022: (0,0.3):1, (0.1,0.3):3, (0.25,0.3):8
IS  2023: (0.25,0.3):4, (0.4,0.3):8
IS  2024: (0.25,0.3):4, (0.4,0.3):8
OOS 2025: (0.25,0.3):12
OOS 2026: (0.25,0.3):2, (0.4,0.3):4
```
The WF converges to the **γ=0.30 top edge** (with λ migrating 0→0.25→0.4 over time as carry's regime
shifts). Early-history months pick smaller γ only because the 24-mo training window has little flow
history; from 2022 on, γ pins at the grid maximum.

## Sanity surface — the fixed (λ,γ) grid is NOT knife-edge (it is MONOTONE in γ)
**OOS monthly Sharpe** (no walk-forward; γ=0 row = the iter_005 fixed-λ row):
```
λ\γ      0.00    0.10    0.20    0.30
0.00    +0.73   +0.97   +1.18   +1.36
0.10    +0.96   +1.19   +1.40   +1.58
0.25    +1.31   +1.55   +1.76   +1.94
0.40    +1.48   +1.64   +1.86   +2.05
```
**IS monthly Sharpe** (same surface):
```
λ\γ      0.00    0.10    0.20    0.30
0.00    +1.61   +1.68   +1.73   +1.74
0.10    +1.70   +1.77   +1.83   +1.86
0.25    +1.72   +1.82   +1.90   +1.98
0.40    +1.18   +1.34   +1.49   +1.61
```
The surface is a smooth, contiguous gradient — every λ row rises monotonically in γ on BOTH IS and OOS.
A spurious factor lifts a lone cell; this lifts the whole neighbourhood. **But that monotonicity is
exactly the problem: OOS Sharpe is still climbing at the γ=0.30 corner.** The coarse grid's top edge is
NOT an interior optimum — it is a truncation.

## Edge-runaway check (extend the γ-grid ONCE to {…,0.4,0.5} — a falsifier, not a new tunable)
| | IS | OOS | maxDD | OOS γ-picks |
|---|---|---|---|---|
| coarse (γ≤0.30) | +1.61 | +2.26 | −20% | {0.3:18} |
| **ext (γ≤0.50)** | +1.70 | **+2.46** | −21% | **{0.5:18}** |

Extending the grid ONCE pushes every OOS month's pick to **γ=0.50** and OOS climbs further (+2.26 →
+2.46). **The weight runs to whatever the grid edge is.** This is the iter_012 "monotone to the grid
edge" concern, now confirmed at the walk-forward level: the `(1−λ)·trend + λ·carry + γ·flow_z` blend
with a coarse γ-grid cannot locate the factor's natural weight — γ is a **corner solution**, not a
pinned interior one. (Scale check: at γ=0.3 the flow contribution is ~37% of the trend-component
magnitude; at γ=0.5, ~62% — even at the edge flow does not yet dominate, so the blend keeps reaching
for more of a +1.6-OOS standalone.)

## Pre-registered confirmation verdict (n=16 OOS months)
| gate | result |
|---|---|
| [A] OOS lift ≥ +0.20 above WF-λ baseline (above noise) | **PASS** (dOOS +0.89) |
| [B] γ>0 reliably PAST-selected in OOS (≥50% of OOS months) | **PASS** (100%) |
| [C] IS not worse (≥ baseline−0.05) | **PASS** (+1.61 vs +1.30) |
| [D] maxDD not worse (within 5pp of −23%) | **PASS** (−20%, cuts DD) |
| [E] lift NOT pinned at the γ-grid edge | **FAIL** (runs away to γ=0.5) |

## Read — NO-PROMOTE: REAL FACTOR, CORNER WEIGHT (honest down-call)
Two claims, cleanly separated:
- **The factor is real and the selection is honest.** Gates A–D all PASS strongly: the joint WF-(λ,γ)
  net lifts OOS +0.89 (to +2.26), cuts DD to −20%, improves IS to +1.61, and γ>0 is PAST-picked in
  100% of OOS months. This is **NOT return-stacking** (which would show OOS γ collapsing to 0) and
  **NOT a knife-edge cell** (the fixed grid is a smooth monotone surface). Combined with iter_012's
  standalone +1.59 OOS / residual-additive β +0.03, taker-flow CONFIRMS as a genuine, independently
  additive, deployable cross-sectional factor on this universe.
- **But the (λ,γ) blend is the wrong VEHICLE.** Gate E FAILS: the OOS surface is monotone in γ and the
  WF pins γ at the coarse-grid top edge; extending the grid once pushes the pick to 0.50 and OOS still
  climbs. The blend coefficient `γ` is a corner / runaway, so the *deployable weight* is whatever the
  grid is truncated to — an arbitrary artifact, not a number the walk-forward locates. Promoting this
  exact parametrization would bake an arbitrary truncation-γ into the baseline. Per the DoF discipline
  (keep to two coarse WF axes; do **not** refine the grid to chase the corner), the honest call is:
  **CONFIRM the factor, REJECT the fixed-coarse-γ blend as its vehicle.** Baseline UNCHANGED.

## Verdict: NO-PROMOTE — REAL FACTOR / CORNER WEIGHT. Baseline UNCHANGED (iter_005 WF-λ, IS +1.30 / OOS +1.37 / −23%).
The taker-flow factor passes every reality / honesty / leak-safety test (sanity gates, gates A–D), but
the joint-(λ,γ) walk-forward exposes that the additive *blend coefficient* has no interior optimum on a
coarse grid — it runs to the corner. A bigger γ always looks better OOS because flow_z is itself a
+1.6-OOS standalone; the blend can't tell "real factor with a large natural weight" from "tilt the book
ever-harder toward the strongest single factor." The right deployment is a **risk-aware multi-factor
combiner**, not a hand-gridded blend weight.

## Axis status
- **Taker-flow imbalance (momentum) factor: CONFIRMED REAL — but NOT promoted via the (λ,γ) blend.**
  Standalone +1.59 OOS (iter_012), joint-WF OOS +2.26 / DD −20% with γ 100%-past-picked OOS (this run).
  Independently additive (β +0.03), orthogonal to trend AND carry. The strongest portfolio factor
  surfaced since carry. What is REJECTED is the *fixed-coarse-γ blend parametrization* as its vehicle,
  on the corner-runaway falsifier [E].
- **Open (the actual deployment question):** how to weight three confirmed factors (trend + carry +
  flow) WITHOUT a hand-gridded coefficient that runs to a corner.

## Next
- **iter-014 — risk-aware multi-factor combiner (the path-forward this run mandates).** Build the three
  factors as standalone vol-targeted nets (trend, carry, flow) and combine by **inverse-vol / risk-
  parity** weighting — each factor's exposure set by its OWN realized risk, past-only, no blend
  coefficient to grid. This directly tests whether flow's confirmed edge survives a non-corner,
  non-tunable weighting (if the risk-parity combiner beats the WF-λ baseline OOS with flow carrying a
  natural, risk-determined share → PROMOTE; if the lift was an artifact of over-tilting toward the
  single strongest factor → the risk-parity weight dilutes it and we learn that too).
- Adjacent: a **taker-flow REGIME gate on gross exposure** (market-wide aggressive-flow scaling the
  book — attacks the −23% DD lever), and the roadmap's **OI / perp-spot-basis** structural families,
  now with two confirmed non-price factors (carry, flow) showing the cross-section is not exhausted.
