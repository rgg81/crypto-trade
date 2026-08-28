# RATIONALE — team-05, illiquidity-conditioned short-horizon reversal

**Lane:** cross-sectional mispricing · **Phase:** refinement · **Evidence:** `lane/feedback/t01.json`
(the unmodified organizer seed, visible development window only, 808 days).

---

## 1. What t01 actually said

Four gates failed — `turnover_ceiling`, `gross_edge_density`, `cost_share`,
`survives_triple_cost`. They are not four problems. They are one number reported four ways.

Reconstructing the book's economics from the packet:

| quantity | derivation | value |
|---|---|---|
| gross alpha | `797.2 × 0.9843 bps` | **+7.8 % / yr** |
| total cost | `7.6198 × gross` | **≈ 59 % / yr** |
| implied cost rate | `59 % / 797` | **≈ 7.4 bps per unit turnover at 1×** |
| gross Sharpe | `7.8 % / 10.7 %` | ≈ 0.73 |
| net Sharpe | reported | −4.84 |

The seed is not signal-dead. Its gross edge is positive and its gross Sharpe is respectable.
It is destroyed by trading 0.73 of gross per bar — roughly a full book replacement every 2.7
bars — at ~7.4 bps a unit. Costs are 7.6× the entire gross edge.

**This is Junior (2026) exactly**, the base rate I recorded in the sealed thesis (§1.5, citation
[10]): positive information coefficient, deeply negative net Sharpe, same instrument, same
columns, same period. A costs-and-turnover failure, not a signal failure. I wrote down that this
was the single most likely way this lane dies. It is what happened.

## 2. Why this is a design problem and not a parameter problem

Write the book's economics per unit of gross exposure. Turnover per bar is `2/h` for a book of
mean holding `h`, so annual turnover is `τ = 2190/h` and annual gross alpha is
`g = 1095·A_h/h`, where `A_h` is the cumulative alpha one position earns over its whole life.
Then

```
net(k×) = τ · ( A_h/2 − k·c )        with c ≈ 7.4 bps
```

The holding period cancels out of the *sign*. Survival at 3× requires

```
A_h  >  6c  ≈  45 bps of cumulative gross alpha per position, at ANY horizon.
```

The seed earns `A ≈ 2·0.9843 = 2.0 bps` per position. The gap is a factor of 22, and it is
horizon-invariant, which is precisely why no setting inside my declared surface can close it.
`holding_bars ∈ {1,2,3}` and `turnover_band ∈ {0.0,0.25,0.5}` move `τ` and `g` together and
leave `A_h/2 − 3c` negative. Tuning them buys a smaller negative number, not a positive one.

The 45 bps hurdle is also the reason the horizon has to move. At 8h resolution a single-bar
reversal position that clears 45 bps net of nothing would be an implausible signal. At the
2–5 day horizon it is the *modal* number in the literature I preregistered: Bianchi/Babiak/
Dickerson report +1.26 %/day equal-weighted in low-activity crypto pairs, Ali/Peng/Shams
~2.77 % weekly for the crypto reversal factor. A tenth of either clears 45 bps comfortably.

**So: the mechanism is intact, the expression was wrong, and the specific thing that was wrong
is the holding period. That is a structural finding, and it is what this candidate is built on.**

## 3. The mechanism, unchanged

A negative (or positive) short-horizon cross-sectional return is not information about value. It
is a noisy observation of the inventory the market-making sector was just forced to absorb
(Nagel 2012). Only *transitory* price impact induces negative serial correlation; information
impact is permanent and pays the liquidity supplier nothing (Glosten–Milgrom). The rent for
holding that inventory scales with the shadow cost of holding it, whose observable dual is
illiquidity — price impact per dollar of flow (Amihud 2002). Hence: **reversal strength should
increase in ex-ante illiquidity**, and if it does not, what I am harvesting is not a
liquidity-provision premium.

**Who is on the other side.** Four named populations, at the 8h Binance USD-M bar:

1. **Forcibly liquidated leveraged directional traders.** The exchange's liquidation engine
   submits their market order; they did not choose to trade, hold no information, and cannot
   wait. This is the purest liquidity-motivated flow in any liquid market, and it does not exist
   in the equity cross-section the founding literature was built on.
2. **Retail momentum takers** chasing a multi-bar move and paying the taker fee for immediacy.
3. **Delta-neutral and funding-carry desks** mechanically rebalancing around the 00/08/16 UTC
   settlements — non-informational flow clustering exactly on my bar boundary.
4. **Market makers who have already left** — not my counterparty, but the reason my counterparty
   got a bad fill. When realised volatility spikes and their margin tightens they widen or pull.

My role: the marginal supplier of immediacy of last resort, accepting inventory the constrained
intermediary sector declined, and holding it while the transitory component decays.

**A tailwind I do not trade for.** The seed's arithmetic leaves roughly +11 %/yr unexplained by
gross-minus-cost. The natural candidate is funding: a reversal book is short recent winners,
which carry positive funding, so it is structurally long the funding carry. I take that as a
by-product and do **not** use funding as a signal — funding-as-signal is the carry family, and
blending it would make the mandate untestable.

## 4. What changed, and why each change is forced

### 4.1 Overlapping sleeves — the turnover fix (the load-bearing change)

The book is the equal-weight average of `H = 18` dated reversal sleeves, sleeve `k` being the
book the signal implied `k` bars ago, recomputed from the same past-only rows. Then

```
w_t − w_{t−1} = ( s_t − s_{t−H} ) / H
```

exactly — every intervening sleeve cancels. Turnover falls as `1/H` with **no** dependence on
the intermediate path, while the composite still expresses each signal for its full life. Nothing
else in the design moves turnover by an order of magnitude. Expected annual turnover ≈ 130–170
against the seed's 797.

This replaces the declared `turnover_band` (Novy-Marx & Velikov's buy/hold spread) rather than
implementing it. **A position-dependent no-trade band is not implementable through this API**:
`DecisionContext` does not expose current quantities, and the evaluator independently applies
membership exits, participation limits and exposure reductions, so any band would be measured
against a reconstructed position that drifts from the real one — and a band applied against a
wrong reference *adds* turnover. Overlapping sleeves obtain the same effect with an exact
identity instead of an estimate. I regard this as the correct reading of the citation, not a
departure from it.

### 4.2 Horizon: 9-bar formation, 18-bar span

72h dislocation, held across a 144h envelope (~3.2 bars mean age). Chosen so that `A_h` is
measured over the window where the crypto reversal literature actually places the effect
(daily-to-weekly), and short enough to stay clear of the 1–4 week formation horizons where
Liu/Tsyvinski/Wu document *continuation*. This is still "short-horizon reversal" in the sense the
family uses the term (Jegadeesh, Da–Liu–Schaumburg and Nagel all sit at weekly-or-shorter).

### 4.3 Selectivity — extremes only

Weight is `sign(c)·max(0, |c| − θ)` on the centred cross-sectional rank `c`, with `θ` set so
~60 % of the cross-section carries weight (capped at 40 names). A linear ranker spends turnover
on names whose signal is near zero. Under the mechanism, ordinary moves are information and only
large ones are plausibly inventory, so the alpha is convex in dislocation and the marginal name
is worth less than it costs. This raises `A_h` without raising `τ`.

### 4.4 The mandate — a continuous illiquidity tilt

Weights are multiplied by `0.40 + 1.20·rank_pct(Amihud)`: the most illiquid eligible name gets
4× the weight of the most liquid, continuously, with no threshold to fit. A gate would score
better on a subsample and worse as evidence; a monotone tilt that survives is the stronger
confirmation, and it is stable under the organizer's small-perturbation check.

Amihud has `|return|` in its numerator, so it is partly a volatility measure in disguise. The
inverse-volatility risk balancing applied alongside it (§4.5) largely removes that component, so
what the tilt is left leaning on is thinness — dollar depth — rather than variance. That is the
intended reading and it makes the tilt a cleaner test of the mandate than Amihud alone would be.

**Guard against the tilt eating itself.** My own thesis (§1.5) records that cost scales with the
same illiquidity that generates the premium, so the tilt is bounded (4:1, not unbounded) and the
thinnest decile by 30-bar median quote volume is excluded outright. Tilting *toward* thinness
while refusing the very thinnest tail is deliberate, not a contradiction: the interior optimum in
illiquidity is the whole difficulty of this lane.

### 4.5 Fixed from the sealed thesis, unchanged

Cross-sectional demeaning of the formation return (Da–Liu–Schaumburg — trading raw reversal is
shorting the market factor); rank transform to `[−0.5, +0.5]`; inverse-volatility cross-sectional
risk balancing at **constant gross**, which is risk balancing, not volatility targeting; funding
accrued, never signalled; dollar-neutral by construction, with each side scaled to exactly half
the gross so "both sides genuinely used" holds on exposure and not merely on P&L.

Volatility is not targeted anywhere. Gross is pinned at 1.0 every bar and the organizer's common
ex-ante risk unit sets the scale.

### 4.6 One softening I want on the record

The sealed surface defines `inventory_proxy = return_and_flow` as **requiring sign agreement**
between the demeaned return and the taker-buy imbalance. Implemented literally on a
top-of-market universe (the seed's median effective breadth of 18.8 implies a cross-section of
order 40), a hard AND-gate halves an already-small universe and drops effective breadth below the
structural gate. I therefore blend the two reversal ranks 0.70/0.30 and re-rank. Because the
magnitude threshold in §4.3 keeps only the tails of the blended rank, and the blend is extreme
precisely where the two components agree, this is a continuous version of the declared operator
rather than a different one — but it is a softening and I am not going to call it anything else.

## 5. Declared amendment to the parameter surface

The sealed surface was 972 configurations over seven knobs. t01 refutes two of them structurally:
`formation_bars ∈ {1,3}` and `holding_bars ∈ {1,2,3}` cannot clear a 45 bps per-position hurdle
at any value. I replace them with

- `formation_bars ∈ {3, 6, 9, 12}` (4)
- `sleeve_span ∈ {9, 12, 15, 18, 21}` (5)

and retire `turnover_band` (subsumed by `sleeve_span`, per §4.1). New cardinality
**972 / (2·3·3) × (4·5) = 54 × 20 = 1080**. Reported so the deflation benchmark stays a real
number: total multiple-testing exposure is now the 1080-point surface, the 19 development-split
configurations named in the sealed §4.3, and the realised count of charged trials. This candidate
is the declared default of the amended surface (`formation_bars = 9`, `sleeve_span = 18`, all
other knobs at their sealed defaults), not a swept optimum — nothing has been fitted to t01
beyond the cost rate, which is a measurement.

## 6. What would falsify this

The sealed falsifier stands: **if reversal strength does not increase with illiquidity, the
premium is not compensation for providing liquidity, and the correct nomination is the unmodified
seed.** I cannot run F1/F2/F4 directly in this phase — there is no shell and the only instrument
is the metric packet — so I state the packet signatures that stand in for them, with
pre-committed readings:

| observation on the next packet | reading |
|---|---|
| `gross_edge_bps_per_turnover` still ≈ 1–3 bps | The horizon was not the problem. `A_h` does not grow with holding, the reversion is not multi-bar, and the transitory-impact story (F4) is wrong. Mechanism in trouble, not just the expression. |
| edge density ≥ ~25 bps but `survives_triple_cost` still fails | Mechanism confirmed, expression not harvestable at taker execution — the sealed §3 "F3 fails" branch. Nominate a minimal-turnover variant, labelled as such. |
| turnover lands ≪ 130 with edge density high but `annualised_return` ≈ 0 | Over-smoothed: `A_h` saturated well before bar 18 and I am paying 1/H dilution for nothing. Shorten `sleeve_span`, do not touch the signal. |
| `median_effective_breadth` collapses or `mean_gross_exposure` falls | The selectivity threshold or the tilt is too aggressive for a ~40-name cross-section. Structural, fix before reading any performance number. |
| edge density rises but realised cost per unit turnover rises with it | The illiquidity tilt is buying premium and paying for it in the same coin — the §1.5 interior-optimum problem, resolved against me. Cap or invert the tilt and report the mandate as unconfirmed. |

And the standing pre-committed consequence from the sealed thesis: **zero movement from the seed
is an acceptable outcome of this lane; a rescued falsifier is not.** If the illiquidity tilt turns
out to be dead weight — if the book works only with the tilt removed — that is a falsification of
my mandate, not a parameter to flip, and I will report it as one.

## 7. Honest residual risks

- **The 45 bps hurdle may simply not be clearable.** Everything above shows the hurdle is
  horizon-invariant; nothing above shows it is *reachable*. Avramov/Chordia/Goyal's warning is
  that contrarian profits are smallest net of cost exactly where they are largest gross. That is
  the equilibrium condition keeping the premium alive, and it may sit below zero here.
- **Horizon extension buys the cost gate at the price of colliding with crypto momentum.**
  9-bar formation is comfortably inside Liu/Tsyvinski/Wu's continuation region if their effect
  starts earlier than one week in perpetuals. A negative `gross_edge_bps_per_turnover` — not
  merely a small one — is the signature, and it would mean the sign has flipped on me.
- **Flow may be momentum, not inventory.** The practitioner evidence on order-flow imbalance in
  crypto perps runs momentum at sub-minute horizons; I am assuming it aggregates to inventory at
  72h. It carries only 30 % of the blend so a wrong sign degrades rather than destroys, but it is
  an assumption and not a result.
- **Universe size is inferred, not observed.** Effective breadth of 18.8 in the seed packet is the
  only evidence about the cross-section's width. The selectivity rule is written to be
  size-adaptive (`60 % of the cross-section, floored at 16 names, capped at 40`) so that a much
  wider universe than I expect does not silently produce an unselective book — but if the
  universe is materially wider, `MAX_KEEP` is the parameter that is wrong.
