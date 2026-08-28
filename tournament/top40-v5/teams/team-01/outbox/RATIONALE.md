# RATIONALE — team-01 nomination

**Candidate:** `lane/outbox/candidate.py` → `build_strategy()` → `HeldFundingCarry`
**Family:** risk-premium harvesting — cross-sectional funding carry with crowding protection
**Preregistered thesis:** `lane/scouting/THESIS.md` (sealed 2026-08-26)
**Direction:** harvest, as committed in F3. Long the most-negative-funding names, short the
most-positive. Not flipped.
**Configurations evaluated on visible data:** 3 (t01, t02, this nomination)

---

## 1. The mechanism, and who is on the other side

A perpetual has no maturity, so there is no convergence trade to enforce its price. In its place
Binance runs a feedback rule: every settlement, the long side pays the short side in proportion to
the perp's premium over the index, and the exchange takes none of it. Funding is not a fee and not
a spread — it is a **transfer between two populations**, and its level is the clearing price of an
imbalance in the demand for leverage.

Per unit of long notional, `r_total = r_price − f`. Harvesting means holding notional of the sign
opposite to funding. A cross-sectional book that is long the most-negative-funding names and short
the most-positive collects, by construction, a carry component equal to
`mean(f | short leg) − mean(f | long leg)`. **The carry leg is arithmetic. The only question is
whether the price leg gives it back — and whether the transport costs more than the transfer.**

On the short leg my counterparty is the levered directional long: retail and trend-following demand
for convex, custody-free, stablecoin-collateralised upside, whose position size is set by their
margin rather than by their view, and who leaves forcibly in a liquidation cascade. On the long leg
it is the squeezed short inside that cascade. I am not facing an arbitrageur: across the long tail
of alt perps there is no deep, cheaply borrowable spot on the same venue under the same collateral,
so cash-and-carry cannot close the gap and the only way to take the receiving side is to bear the
risk. A premium that can only be earned by bearing risk is a risk premium, and risk premia do not
get arbitraged away.

The competition on my own side is now institutional and reflexive — Ethena-style synthetic dollars
whose backing *is* this trade, and which rotate out when funding compresses. That is the crowding
the mandate names, and §5 below says exactly how much of it I am still expressing and how much I
have retired.

## 2. What the two packets actually measured

Both charged trials failed on cost, and the packets pin the cost down exactly. Net return is linear
in the cost multiplier, so the 1x and 3x legs identify gross and cost separately. Doing that
log-linearly (which is the reconstruction that reproduces the organizer's own reported numbers to
within 0.2%):

| | t01 | t02 |
|---|---|---|
| annualised turnover `T` | 289.47 | 107.42 |
| implied cost `C` | 21.75%/yr | 8.06%/yr |
| implied gross edge `G` | 18.83%/yr | 9.74%/yr |
| implied `C/T` | **7.51 bp** | **7.50 bp** |
| gross Sharpe `G/vol` | 1.81 | 0.97 |

And the organizer's own two cost metrics multiply out to the same constant in both packets:

```
t01:  6.6633 bp × 1.12558 = 7.500
t02:  9.4760 bp × 0.79147 = 7.500
```

So `cost_share_of_positive_gross = 7.5 / gross_edge_bps_per_turnover`, the venue charges **7.5 bp
per unit of annualised turnover**, and the three cost gates are one condition in three units:

> `survives_triple_cost` ⟺ `gross_edge_density > 22.5 bp` ⟺ `cost_share < 1/3`

Everything else has passed twice, comfortably: `breadth_pass_fraction` 1.0, `mean_gross_exposure`
0.96 / 0.99, long/short exposure share 0.500 / 0.500, `ruined` false. `turnover_ceiling` failed at
289 and passed at 107. **There is one gate to clear and it is arithmetic.**

The break-even bar as a function of speed, `G > 22.5 bp × T`:

| | required `G` | actual `G` | shortfall |
|---|---|---|---|
| t01 at T = 289 | 65.1%/yr | 18.8% | −46.3 pts |
| t02 at T = 107 | 24.2%/yr | 9.7% | −14.5 pts |
| this book at T ≈ 28 | **6.3%/yr** | to be measured | — |

## 3. Where t02's turnover actually came from

t02 predicted 35–80 turns and delivered 107. That miss is the useful part of the packet, and the
diagnosis is structural rather than parametric. A slow *signal* does not produce a slow *book* if
the construction re-derives every weight every eight hours:

- **Drift rebalancing.** A book with a literally unchanged target still pays to be pulled back to
  it. At the residual per-name volatility implied by t02 (≈ 39%/yr, from vol 10.06% at effective
  breadth 14.8), realigning a gross-1.0 book every bar costs ≈ 1.6% per bar ≈ **17 turns/yr on its
  own**, before any signal moves.
- **Book-wide renormalisations.** The soft-threshold cut, the side-balancing rescale, the beta
  hedge and the gross normalisation are each recomputed from scratch every bar, and each one moves
  *every* weight when it moves at all.
- **A noisy multiplicative overlay.** `score = tilt × (1 − λ·crowding)` with a rank composite that
  includes a fast/slow aggressor-share difference perturbs all ~38 weights every bar.

None of those carry information. They are noise trading against a premium that was already being
collected. That distinction is the whole design of this candidate.

## 4. The design, and why each piece is forced by §2

**(a) The book is held for three days, not re-derived every eight hours.** `target_weights` returns
`None` on eight bars in nine and a portfolio on the ninth. This is the API's documented affordance
for exactly this situation, and it is mechanism-correct: **the funding transfer accrues to the
holder at every settlement whether or not the book is touched**, so trading between decisions buys
nothing and costs 7.5 bp. Holding also cuts drift turnover superlinearly — accumulated drift grows
like `√k` while the number of rebalances falls like `k`, so drift turnover falls like `1/√k`, from
≈17/yr to ≈3.5/yr at k = 9.

The clock is derived from the panel's own origin (earliest `open_time` anywhere in `bars`) and the
panel's own median bar spacing, never from a wall-clock date. A shift of the whole calendar moves
origin and decision together and leaves the phase identical; pseudonymisation leaves a minimum over
all names identical; appended future rows leave truncated frames identical.

**(b) Fixed-size legs, so nothing renormalises.** Each leg holds a fixed count of names summing to
exactly 0.4975 gross. Dollar neutrality and gross exposure are properties of the construction, not
outputs of a nightly rescale. A name that stays in its leg keeps its weight; the only turnover the
signal can generate is a genuine membership change.

**(c) One 63-bar regime horizon for both carry and risk.** Carry is an exponentially weighted
8h-equivalent funding accrual with a 21-day centre of mass; risk is the 63-bar realised volatility.
Using a single horizon for both removes a knob and makes the object being traded explicit: the
funding *regime*, whose persistence is measured in weeks, not the funding *print*.

The 8h-equivalence is not cosmetic. Binance settles 8h, 4h or hourly by symbol and regime and the
published rate carries a `/(8/N)` divisor, so unadjusted per-interval rates systematically
under-rank precisely the fast-settling, cap-pinned names this mandate is about. The mean interval is
inferred per symbol from the spacing of its own settlements.

**(d) Inverse-volatility weights inside each leg, bounded to a 2.1:1 band.** Equal risk contribution
rather than equal notional. This is the mandate's crash concern expressed as composition: a name
whose realised volatility has already expanded — which in this universe means a name inside a
cascade — carries proportionally less of the book. The band keeps effective breadth near the name
count and keeps every weight inside the 0.10 cap without a clipping loop distorting the leg.

**(e) Selection at ~15% per side of a top-75 liquidity universe**, giving ≈ 10 names per leg and an
effective breadth near 20 — above both prior trials, which passed the breadth gate at 12.9 and 14.8.

### A note on the risk unit, stated rather than hidden

At breadth ≈ 20 this book's ex-ante volatility at gross 1.0 is ≈ 8.7% against a risk unit that has
been scaling both prior books to ≈ 10%. I expect to sit at the gross cap with
`risk_unit_capped_fraction` well above t02's 0.066, and to run slightly under the field's risk.

I am accepting that deliberately, for two reasons. First, a constant scale factor cancels out of
`G/T` entirely, so it changes neither density, nor `cost_share`, nor Sharpe — only the absolute
return. Second, a book that is *not* pinned pays turnover for the risk unit's own bar-to-bar
rescaling: if `s_t` wobbles by 1%, that is 11 turns/yr of pure cost with no information in it. Being
pinned sets `s_t ≡ 1` and removes that channel. This is a portfolio-construction choice about
breadth; I am not timing volatility and gross is a constant in the source.

## 5. Crowding protection: what I kept, and what I retired

Thesis §1.5 forces this: a common risk unit undoes any protection expressed as gross-leverage
timing, so crowding protection has to be *composition* — re-allocating a constant risk budget away
from crowded carry — or it is nothing. Four compositional protections survive here, and all four
are eligibility or selection rules, so **none of them costs turnover**:

1. **Cap-pinned tail trim (T = 0.02, declared).** At the funding cap the printed rate stops clearing
   the imbalance and stops being a measurement of the premium; it is also where the cascade lands.
   Both raw tails are dropped before ranking.
2. **Capacity discount.** `score = tilt × (1 − 0.5·(1 − rank(liquidity)))` — the declared
   multiplicative rank-discount form, applied to *selection* rather than to weights. A large premium
   sitting on thin turnover has no capacity behind it and no exit, which is precisely the state in
   which being the last holder is expensive. Both inputs are 63–90 bar statistics.
3. **Carry-to-risk normalisation and inverse-vol weighting.** The funding cap scales with the
   maintenance margin ratio, which is larger for riskier alts, so a raw-funding sort *mechanically*
   overweights junk. Dividing by realised volatility corrects an exchange-mechanical bias, and it
   symmetrically demotes names whose volatility has already expanded — the cascade names on both
   legs.
4. **Beta residualisation** of the ranked signal against the equal-weight universe. When funding is
   one-signed across the whole cross-section — the pre-cascade state — a naive sort is a disguised
   directional bet. Residualising at the selection stage removes that tilt for free, where an
   explicit weight-space hedge would have to be recomputed and re-traded every bar.

**Retired: C1 (funding-regime staleness) and C2 (taker-flow decay).** F2 declared `λ = 0` a control
arm and required the overlay to earn its complexity. I never got the matched pair — t02 changed the
overlay, the signal horizon and the construction at once — so I cannot claim the overlay passed. I
can say two things against it. C1 is magnitude-weighted funding-sign persistence, which is close to
mechanically collinear with the carry it is supposed to protect: it discounts the strongest carry
names hardest, and t02 is consistent with that having cost real gross edge. C2 is a fast fast/slow
difference of aggressor share and is a pure turnover generator; the thesis itself flagged it as the
component most likely to fail at 8h resolution. Carrying two unvalidated, edge-cannibalising,
turnover-generating terms into a nomination whose only failing gate is cost would be indefensible.

This is a partial falsification of the distinctive claim of my lane and I am recording it as one.
What remains of "crowding protection" is the part that is independently justified by execution
capacity and by the exchange's own margin mechanics, not the part that needed the positioning
inference to be true.

## 6. Predictions — these are falsifiable, not hopes

**Turnover budget, built bottom-up.** 121.7 rebalances/yr. Drift realignment ≈ 2.8% per rebalance
(≈ 3.4/yr). Membership churn = `2 × (fraction of each leg replaced)` per rebalance; at a ~30-day
mean tenure that is 0.20 per rebalance (≈ 24/yr). **Central estimate T ≈ 28/yr, plausible range
18–45.**

**What each outcome would mean:**

| `annualised_turnover` | reading |
|---|---|
| 18–45 | the clock and the fixed legs bound turnover as designed |
| < 15 | over-damped; watch for a turnover floor |
| > 70 | the clock did not bind — a code-level failure, not a parameter one |

**The gate itself,** at `T ≈ 28` (`density = G/T`, `cost_share = 7.5/density`):

| `G` | density | `cost_share` | net 1x | net 3x | verdict |
|---|---|---|---|---|---|
| 4% | 14.3 bp | 0.52 | +1.9% | −2.3% | fail |
| 6% | 21.4 bp | 0.35 | +3.9% | −0.3% | marginal fail |
| **8%** | **28.6 bp** | **0.26** | **+5.9%** | **+1.7%** | pass |
| 10% | 35.7 bp | 0.21 | +7.9% | +3.7% | pass |
| 12% | 42.9 bp | 0.17 | +9.9% | +5.7% | pass |

So: **the nomination qualifies if gross edge holds at ≥ 7%/yr while turnover lands near 28.**

Also predicted: `median_effective_breadth` ≈ 18–21; long/short exposure share 0.50/0.50 exactly, by
construction; `mean_gross_exposure` ≈ 1.0 with `risk_unit_capped_fraction` materially above 0.066;
`annualised_volatility` ≈ 8–9%, below the ~10% both prior books ran at; **`active_bar_fraction`
≈ 0.11**, which is the visible signature of the held book and is the one metric that will move in a
direction no prior packet has shown.

## 7. The strongest argument against this book

I want to state it as strongly as I can rather than bury it. Fit a power law through the only two
points I have: `G ∝ T^0.665` (from 18.83% at T = 289 to 9.74% at T = 107). Extrapolated to T = 28
that gives `G ≈ 4.0%` — the top row of the table, and a fail. Solved for break-even, that power law
says triple cost is only survivable below **T ≈ 7 turns/yr**, which is a frozen book, not a
portfolio. **If that functional form is right, the funding premium in this universe is real but not
transportable through a 7.5 bp cost at any turnover a portfolio can run at, and my mandate's
falsifier is one packet from triggering.**

My reason for believing the extrapolation is pessimistic is specific, not hopeful: **t01 → t02 and
t02 → this candidate buy their turnover reductions in different currencies.**

- t01 → t02 bought its 2.7× cut by *smoothing the signal* — a 1-day funding lookback became a
  14-day EWMA, a 14× change in horizon for a 2.7× change in turnover. What that pair measures is
  the elasticity of gross edge to **lookback**, and losing edge to smoothing is exactly what you
  would expect if part of t01's gross was fast price reversal rather than carry.
- This candidate barely smooths further (14-day → 21-day centre of mass). It buys its 3.8× cut by
  *holding* and by *deleting the renormalisations* — neither of which discards any information. §3
  accounts for roughly 17 turns/yr of pure drift realignment plus a large share of the remainder in
  book-wide rescales that move every weight and predict nothing.

Turnover reduction through holding is close to free in information terms; turnover reduction through
smoothing is not. That is the load-bearing claim of this nomination, and it is exactly what the next
packet tests.

**The clean falsification.** If this book returns `T ≈ 25–35` with density still below ~22 bp, then
gross edge scales with trading speed rather than with signal horizon, the power law was right, and
the honest conclusion is my mandate's falsifier: sorting on funding produces a spread that exists
but cannot be transported through this cost structure. That is a result, and retiring on it is
preferable to a fourth reparameterisation of the same book.

**Where I am confident:** the cost identity in §2 is measured, exact, and reproduced by the
organizer's own two metrics. The turnover mechanics in §3–§4 follow from construction rather than
from fitting. **Where I am not:** how much of `G` survives a three-day holding period. That single
unknown decides this nomination, and I would rather nominate a book whose failure mode is one clean
measurable question than one whose Sharpe I cannot explain.

## 8. Declared-surface accounting

Thesis §4.3: *"If a knob I did not declare would materially change the result, the honest move is to
report that fact and leave it unsearched."* Invoked again, and the largest item is the same
declaration failure identified after t01 — my sealed surface contained **no turnover control of any
kind**, and turnover is the only gate I have ever failed.

| Item | Declared | Here | Status |
|---|---|---|---|
| Rebalance cadence | fixed: every 8h bar | 9-bar clock, hold in between | **new dimension**, unsearched, set by §2 arithmetic |
| Funding lookback `L` | {1, 3, 9, 21} bars | 63-bar centre of mass, EW | outside the declared grid |
| Carry normalisation `Z` | carry-to-risk | carry-to-risk | as declared |
| Crowding metric `C` | C1 · C2 · C3 · composite | capacity term only | **reduced**; C1 and C2 retired per §5 |
| Overlay strength `λ` | 0.5 | 0.5, applied to selection | as declared, relocated |
| Leg fraction `q` | {0.10, 0.20, 0.33} | 0.15 | interpolated inside the declared interval |
| Tail trim `T` | 0.02 | 0.02 | as declared |
| Universe `U` | 75 | 75 | as declared |
| Weighting | rank-weight within leg | inverse-vol within leg, bounded | substituted (§4d) |

Three configurations have been evaluated on visible data. Every constant above was chosen from the
§2 cost identity or carried unchanged from the preregistration; none was chosen by sweeping and
keeping a winner, and there is no reserve of unreported trials behind this nomination.

## 9. Contract compliance

Reads only `decision_time`, `bars`, `funding` and `eligible_symbols` from `DecisionContext`. The
cross-sectional panel is aligned on the `open_time` **column** via `searchsorted` onto the longest
frame's timestamp grid — never on the positional index, which would return an almost entirely `NaN`
panel and an empty book that raises nothing. The funding rate column is `funding_rate`. Epoch units
are normalised before any age arithmetic, so a millisecond column cannot silently filter every
funding row away.

Returns a finite `dict[str, float]` keyed on `eligible_symbols`, naming every eligible name
explicitly with 0.0 for those out of the book so no position is carried by omission — or `None` to
hold, both between rebalances and when the panel is too degenerate to form a portfolio.
`sum(abs(w)) = 0.995 ≤ 1.0` and `sum(w) = 0` exactly by equal-gross legs; `abs(w) ≤ 0.095 ≤ 0.10`.

Stateless and a pure function of the context: no persistence across decisions, no RNG, no network,
subprocess or filesystem, no `eval`/`exec`/`getattr`, no embedded data, no absolute dates, no symbol
identity. Every quantity is scale-free — ranks, log returns, ratios — so magnitude-scale
equivariance holds; the clock is measured from the panel's own origin in the panel's own bar units,
so calendar-shift equivariance and future-append invariance hold; symbols are iterated in sorted
order and all sorts are stable, so exact replay is deterministic; and weights are piecewise-constant
in the inputs, so a small perturbation moves at most one name across a leg boundary.

**Not verified by execution.** This phase has no shell, so the code has been checked by reading
only. The failure modes hardened against explicitly are the ones that raise nothing and score as a
book with no edge: positional-index alignment, the wrong funding column, epoch-unit mismatch,
empty-slice paths, a degenerate clock (which degrades to rebalancing, not to a frozen book), and
hash-order nondeterminism in the returned mapping.
