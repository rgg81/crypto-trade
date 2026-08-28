# RATIONALE — team-05, nomination

**Lane:** illiquidity-conditioned short-horizon reversal (cross-sectional mispricing)
**Phase:** decision · **Evidence:** `lane/feedback/t01.json` (unmodified organizer seed) and
`lane/feedback/t02.json` (my refinement candidate), visible development window only, 808 days.

---

## 1. What I am nominating

    weight_i  ∝  −resid( rank(r_i^{24h}/σ_i) | rank(trend_i^{4d}/σ_i) )
                 ×  pct(ILLIQ_i)  ×  clip(median σ / σ_i)

averaged over 18 overlapping dated sleeves weighted by how liquidity-stressed the market was on
the bar each sleeve was formed, then projected off the current medium-horizon trend, then
dollar-neutralised at gross 1.0.

In words: **fade the 24h cross-sectional dislocation, but only the part of it that is not the
4-day trend, in proportion to how thin the name's book was before the move, emphasising the bars
on which the whole market's book was thin — and hold it slowly.**

This is the sealed thesis's "F3 fails" branch, taken deliberately: *mechanism unrefuted, expression
constrained by cost, so nominate a minimal-turnover variant and label it as one.* It is not my
highest-conviction Sharpe story. It is the book whose every component I can point at a number for.

## 2. What the two packets actually establish

Two identities fall out of the metric definitions, and they decide the whole lane. Write `c` for
realised cost per unit turnover, `τ` for annualised turnover, `E` for `gross_edge_bps_per_turnover`
and `A_H` for the cumulative gross alpha one position earns over its whole life of `H` bars. For a
book of mean holding `H`, `τ ≈ 2·1095/H` and annual gross `≈ τ·E`, so

```
E  =  A_H / 2                 and                 cost_share  =  c / E
```

Check against t01: gross `= 797.2 × 0.9843 bps = 7.85 %/yr`; `cost_share = 7.6198` implies cost
`= 59.8 %/yr`, i.e. `c = 7.5 bps` per unit turnover; and `c/E = 7.5/0.98 = 7.65` against the
reported 7.62. The identity holds to rounding.

**The consequence is the single most important fact I own: `gross_edge_density` and `cost_share`
are invariant to holding period.** `E = A_H/2` and `cost_share = c/E` contain no `H`. Overlapping
sleeves, no-trade bands, longer horizons, slower rebalancing — none of them touch either gate. They
move `τ` and gross *together*. Only per-position cumulative alpha moves `E`.

That is why t02 passed `turnover_ceiling` (797 → 81, exactly as designed) and still failed the same
three cost gates. The turnover machinery worked and was never the binding constraint.

The second fact is the sign:

| | t01 (seed) | t02 (mine) |
|---|---|---|
| formation / holding | ~1–2 bars | 9 bars / 18-bar sleeve span |
| annualised turnover | 797.2 — **fails ceiling** | 80.9 — **passes** |
| `gross_edge_bps_per_turnover` | **+0.98** | **−21.32** |
| implied gross alpha | +7.9 %/yr | **−17.2 %/yr** |
| implied gross Sharpe | ≈ +0.73 | ≈ **−1.54** |
| `positive_fold_fraction` | 0.00 | 0.20 |

**A 72h-formation reversal held six days is not weakly wrong in this universe. It is strongly
wrong.** `A_18 ≈ −43 bps` per position ≈ −7 bps/day of continuation on a unit-gross book. That is
quantitatively where Bianchi/Babiak/Dickerson put the *liquid half* of the crypto cross-section
(value-weighted reversal −0.19 %/day, insignificant), and it is where Liu/Tsyvinski/Wu put
continuation. My universe — `median_effective_breadth` 19–21 on a full-cross-section rank book
implies roughly 40–50 names — **is** the liquid half of crypto. The disconfirming citation I
included on purpose is the one that fired.

Everything else in the two packets is clean and was never the problem: `active_bar_fraction` 1.0,
`breadth_pass_fraction` 1.0, `mean_gross_exposure` ≈ 0.99, long/short exposure shares 0.5000/0.5000,
`ruined` false, `risk_unit_capped_fraction` 2–3 %. The structural gates are free; the cost gates are
the whole examination.

## 3. The mechanism, and who is on the other side

Unchanged from the sealed thesis, because nothing has refuted it.

A short-horizon cross-sectional return is not information about value. It is a noisy observation of
the inventory the market-making sector was just forced to absorb (Nagel 2012). Only *transitory*
price impact induces negative serial correlation; information impact is permanent and pays the
liquidity supplier nothing (Glosten–Milgrom). The rent for warehousing that inventory scales with
the shadow cost of warehousing it, whose observable dual is price impact per dollar of flow —
Amihud illiquidity. Hence the mandate: **reversal strength should increase in ex-ante illiquidity,
and the trade should be taken on the moves a thin book had to absorb, not on every move.**

At the 8h Binance USD-M bar I am the residual supplier of immediacy to four named populations:

1. **Forcibly liquidated leveraged directional traders.** The exchange's liquidation engine submits
   their market order. They did not choose to trade, hold no information, and cannot wait. This is
   the purest liquidity-motivated flow in any liquid market and it does not exist in the equity
   cross-section the founding literature was built on (Ali/Peng/Shams 2025 name the channel).
2. **Retail momentum takers** crossing the spread to chase a 24h move and paying for immediacy.
3. **Delta-neutral and funding-carry desks** rebalancing around the 00/08/16 UTC settlements —
   non-informational flow clustered exactly on my decision boundary.
4. **Market makers who have already left** — not my counterparty, but the reason my counterparty got
   a bad fill. When realised volatility spikes and their collateral tightens they widen or pull.

Funding is accrued as cost or credit and **never read as a signal**; `context.funding` is not
touched anywhere in the candidate. Funding-as-signal is the carry family, not mine, and blending it
would make the mandate untestable. I note, without trading for it, that the t01 arithmetic leaves
`7.85 − 59.8 = −51.9 %` against a reported `−40.8 %`, i.e. roughly **+11 %/yr of funding accrual** on
a unit-gross reversal book. A book short recent winners is structurally long that carry. It is a
by-product, it scales with gross rather than with turnover, and it is the reason low turnover is
worth more here than the gross-alpha dilution costs.

## 4. What changed from t02, and why each change is forced

### 4.1 The horizon comes back inside the reversal region — 24h formation, not 72h

`FORMATION_BARS` 9 → 3. t02's amendment pushed formation into the region where the packet says
continuation dominates. Three bars is the sealed surface's own upper value (`formation_bars ∈
{1,3}`), it is the horizon at which the crypto reversal literature actually measures the effect
(Bianchi et al. report daily formation), and it is three times shorter than the horizon that
demonstrably flipped sign. I did not go to one bar: with an 18-bar sleeve span, an 8h shock held
six days is mostly stale, and a single 8h bar is the noisiest possible read on the dislocation.

### 4.2 The medium-horizon trend is hedged, twice, rather than hoped about

This is the load-bearing change and it is the direct answer to `E = −21.32`.

A reversal book formed on recent returns is *accidentally short medium-horizon momentum*, because a
name that just fell is more likely to be a 4-day loser. t02 measured that factor at roughly −7
bps/day against a fader. So the candidate:

- **residualises at formation.** Each sleeve ranks the 24h dislocation and the 4-day trend
  cross-sectionally, regresses the first on the second *in that bar's cross-section*, and trades the
  residual. The trend window ends where the formation window begins, so the hedge and the signal
  never share a bar and the hedge cannot cancel the thing it protects.
- **re-neutralises at delivery.** The composite book is projected off the *current* trend rank
  before it is sent. Sleeves age; a hedge fixed at formation goes stale by bar 10. This guarantees
  the delivered exposure is momentum-orthogonal at every decision, not merely at every formation.

Both slopes are measured on the cross-section present at the decision. Nothing is assumed about the
sign or size of the momentum factor — if it is zero the projection does nothing.

This is not a reaction fitted to one packet. Da/Liu/Schaumburg (2014) is in the sealed thesis as
citation [9] precisely for this: raw short-term reversal decomposes into across-industry momentum,
within-industry expected-return variation, under-reaction, and a residual, and **only the residual
is significantly positive**. The sealed thesis used it to fix cross-sectional demeaning as a design
choice. t02 told me the crypto analogue of "across-industry momentum" is large enough here that
demeaning alone does not remove it. Same citation, same operator, one level deeper.

### 4.3 The illiquidity conditioning stops being decorative

t02's tilt was `0.40 + 1.20·pct` — a 4:1 ratio between the extremes, with the thinnest decile
excluded outright and an unbounded `1/σ` sitting next to it. Since illiquid names are usually the
volatile ones, the `1/σ` term was quietly undoing the tilt. The mandate was being tested at
approximately quarter strength.

The candidate uses **`tilt = pct(ILLIQ)` on (0, 1]**: the most liquid name in the cross-section
carries no weight at all, and the tilt is linear with no threshold to fit. The `1/σ` balance is
clipped to `σ ∈ [0.70, 1.50] × median σ`, i.e. a genuine risk balance of at most 2.1:1, tight enough
that it cannot cancel the term it sits next to. The thinnest-decile floor stays — the participation
cap is 0.1 % of prior-24h quote volume, and weight below that floor is un-filled gross rather than a
position. Tilting toward thinness while refusing the very thinnest tail is the sealed §1.5 interior
optimum, deliberately, not a contradiction.

If the mandate is true this change is where the edge has to come from, and the size of the change is
set by the mandate's own claimed effect size, not by a search.

### 4.4 The "when" half of the mandate is expressed for the first time

The mandate says *condition on when liquidity was actually scarce*, not only on which names are
thin. Nagel's central result is a time-series one: the reversal premium runs below 0.2 %/day in calm
periods and near 1 %/day in the 1998 and 2008 liquidity crises. Neither t01 nor t02 used that axis.

The candidate weights sleeve `k` by where the bar it was formed on ranks, inside the holding window,
on market-wide liquidity stress — the cross-sectional median of each bar's realised price impact
divided by that symbol's own recent average impact. Unitless, scale-free, purely relative, no level
and no threshold. Weights are bounded to `[0.4, 1.6]`, a 4:1 emphasis between the most and least
stressed bar in the window.

**Bounded on purpose, and I want the limitation on the record.** The strong form of this — go to
cash in calm states — is unavailable to me and I am not going to pretend otherwise. It would fight
the organizer's ex-ante risk unit, which rescales my book and would partly undo any gross
modulation, and it would drag `mean_gross_exposure` down through a structural gate that both prior
trials passed comfortably. A 4:1 sleeve emphasis is what this interface actually supports. It is the
mandate's effect size, not Nagel's.

### 4.5 Two things removed

- **The taker-flow blend.** t02 carried the sealed default `inventory_proxy = return_and_flow` as a
  0.70/0.30 rank blend. The sealed thesis §1.6 flagged that practitioner evidence on order-flow
  imbalance in perps runs *momentum* at sub-minute horizons and that the sign may not survive
  aggregation. With flow in the book I cannot attribute `E = −21.32` between the horizon and the
  flow sign. It is gone, so the next packet is attributable to the mandate alone. Declared
  deviation, conservative direction, same choice the discovery candidate made.
- **The hard tail-selection threshold** (`KEEP_FRACTION`, `MAX_KEEP`). It bought convexity I have no
  evidence for, cost effective breadth, and is exactly the sort of fitted boundary the
  small-perturbation stability check exists to catch. Linear-in-rank already sends near-median names
  to near-zero weight.

### 4.6 Unchanged, because they were never the problem

Overlapping sleeves at `SLEEVE_SPAN = 18` (t02's proven turnover geometry); cross-sectional
demeaning carried by the rank transform; each sleeve dollar-neutral with each side scaled to exactly
half the gross, so "both sides genuinely used" holds on exposure and not merely on P&L; gross pinned
at 1.0 every bar with **no volatility targeting anywhere**; stateless, no RNG, no absolute dates, no
symbol literals, no price levels — everything enters as a log return, a ratio, or a cross-sectional
rank.

## 5. The arithmetic this has to clear, stated before the result

I would rather write the hurdle down than discover it. With `c ≈ 5–7.5 bps` per unit turnover (7.5
from t01; ≈4.9 from t02 net of funding), and `cost_share = c/E`:

- `E > c ≈ 6 bps` merely to make costs smaller than gross edge.
- `E > 3c ≈ 18–22 bps` for `survives_triple_cost` on price alpha alone — less if the ~11 %/yr
  funding accrual survives, since it scales with gross and not with turnover. At `τ ≈ 110`, `E ≈ 10
  bps` and funding `+8 %/yr` would already put the triple-cost return above zero.
- In per-position terms: **`A_H ≥ 30–45 bps` of cumulative gross alpha, against the seed's ≈ 2 bps.**

That is a factor of 15–20, and no structural change can produce it, because `E` is holding-period
invariant. It can only come from conditioning. **Which is the point.** The mandate's own literature
predicts a multiple of exactly this order: Bianchi's low-activity/high-activity reversal spread is
2.4× equal-weighted and sign-flipping value-weighted; Nagel's calm/crisis spread is ~5×. If the
mandate is true, only the strongly-conditioned expression clears the bar, and the mildly-conditioned
one provably cannot — which is what t02 was.

Expected turnover: the sleeve identity gives `≈ 1450/SLEEVE_SPAN`, calibrated on t02 (predicted 73,
realised 81), plus the stress reweighting, so **≈ 90–130/yr**. Known-good is 81, known-bad is 797.
Effective breadth should land near 22–27 against 19–21 in the prior trials, because the tail-selection
threshold is gone. Gross 1.0, net ≈ 0, per-symbol ≤ 0.10, all enforced in-book as well as by the
evaluator.

## 6. The alternative I rejected, and why

t02's `−21.32` is a large, clean number. Inverted, it is a 4-day-formation illiquidity-tilted
*continuation* book with gross Sharpe ≈ +1.54, gross ≈ +17 %/yr at 81 turnover, and a triple-cost
return that is plausibly positive. That book would probably qualify. I am not nominating it.

Three reasons, in order of weight.

1. **It is a different economic family.** My lane is cross-sectional mispricing expressed as
   liquidity provision. Illiquidity-tilted 4-day momentum is Liu/Tsyvinski/Wu's momentum factor with
   a decoration on top. Nominating it would be abandoning the mandate while keeping its vocabulary.
2. **The attribution is not identified.** t02 changed seven things at once relative to the seed. I
   cannot tell how much of `−21.32` is the reversal sign, how much is the 30 % flow blend I
   preregistered as possibly momentum-signed, how much is the tail-selection threshold, and how much
   is the vol-normalised dislocation. Flipping a sign on one aggregate number from one confounded
   book is the definition of hill-climbing feedback, and the rules are explicit that twelve
   feedback-driven trials make a development number a statement about a search rather than an edge.
3. **The sealed pre-commitment.** "Zero movement from the seed is an acceptable outcome of this
   lane. A rescued falsifier is not."

What I have done instead is *hedge* the factor rather than ride it. The candidate is orthogonal to
medium-horizon momentum by construction, which means the t02 finding is used as information about a
confound — its strongest legitimate use — without becoming the position.

I also rejected **nominating the unmodified seed**. The sealed consequence routes to the seed when
F1 or F2 fails, i.e. when the *interaction* between past return and illiquidity is non-negative.
That has never been measured: neither packet can separate it, and there is no shell in this phase to
run the panel regression. What has failed, twice, is F3 — tradeability under taker execution — whose
pre-committed consequence is "nominate at most a minimal-turnover variant, explicitly labelled as
such." This is that variant, and this is that label. Nominating the seed would also be nominating a
book that fails four gates on evidence I already hold, which forfeits qualification to make a point
the evidence does not support.

## 7. What would falsify this

The mandate's falsifier stands unamended: **if reversal strength does not increase with illiquidity,
the premium is not compensation for providing liquidity.** Pre-committed readings of the next
packet, written before I see it:

| observation | reading |
|---|---|
| `gross_edge_bps_per_turnover` still ≈ 0–3 bps | Conditioning does not concentrate the premium. The mandate's central claim is unsupported in this universe at this strength, and the honest statement is that the liquid core of Binance perps does not pay a measurable liquidity-provision rent at 8h resolution. |
| `E` negative again, and large | The residualisation did not remove the continuation factor, or 24h formation is already inside it. The reversal region, if it exists here, is shorter than one day and below the resolution I can trade. |
| `E` ≥ ~15 bps but `survives_triple_cost` still fails | Mechanism supported, expression not harvestable at taker execution — the sealed F3 branch, now with a number attached. Report it as such; do not search for a rescue. |
| `E` rises **and** realised cost per unit turnover rises with it | The tilt buys the premium and pays for it in the same coin. That is the sealed §1.5 interior optimum resolved against me, and the mandate is recorded as confirmed-but-uncollectable. |
| `median_effective_breadth` collapses or `mean_gross_exposure` falls | The `pct(ILLIQ)` tilt is too aggressive for a ~45-name cross-section. Structural, and it invalidates any performance reading above it. |
| turnover ≫ 130 | The stress reweighting costs more turnover than modelled. Structural; `STRESS_RANGE` is the term to shrink, not the signal. |

**The falsifier I most expect to fire is the first one**, and I am recording that now rather than
after. Everything in §5 says the conditioning must deliver a 15–20× improvement in per-position
alpha. The mandate's literature says an effect of that order exists. My universe is not that
literature's universe: it is ~45 large perpetual contracts, i.e. the half of the cross-section where
Bianchi et al. measure the reversal premium at *minus* 0.19 %/day value-weighted. The conditioning
has to reach a region my membership screen may simply not contain.

## 8. Honest residual risks

- **The hurdle may not be reachable at all.** Avramov/Chordia/Goyal's warning is the equilibrium
  condition that keeps this premium alive: contrarian profits are smallest net of cost exactly where
  they are largest gross. Junior (2026) reports positive rank-IC with net Sharpe −2.9 on ten Binance
  USDT perps over this period. Both were in the sealed thesis before any data was mounted, and both
  say the modal outcome of this lane is a cost failure. Nothing in this candidate makes that
  outcome unlikely; it makes it *diagnosable*.
- **The momentum hedge is a projection onto one factor at one horizon.** If the continuation in this
  universe lives at a different horizon than 4 days, or is non-linear in the rank, the residual still
  carries it.
- **The `1/σ` clip is a judgement call.** Tightening it to [0.70, 1.50] to stop it cancelling the
  illiquidity tilt is a deliberate trade of cross-sectional risk balance for mandate fidelity. If
  the book's risk turns out to be owned by two volatile thin names, that clip is what did it.
- **The stress reweighting is unfalsifiable at this resolution.** It is bounded so that a wrong sign
  degrades rather than destroys, but I have no packet that can tell me whether it helped.
- **Universe width is inferred, never observed.** Everything above rests on effective breadth 19–21
  implying 40–50 tradable names. If the cross-section is materially wider, `DEPTH_FLOOR_Q` and the
  `pct(ILLIQ)` tilt are shaped for the wrong distribution.

**Declared surface accounting**, so the deflation benchmark stays a real number. Sealed cardinality
972 over seven knobs; the t02 amendment restated it at 1080; this candidate consumes no new knob —
it sets `formation_bars = 3` (sealed range), `illiq_measure = amihud`, `illiq_lookback_bars = 21`,
`conditioning_form = tilt_linear`, `inventory_proxy = return`, `sleeve_span = 18` — and adds two
declared structural operators, the momentum residualisation and the bounded stress reweighting,
neither of which was swept. Charged trials realised to date: **two**. Total multiple-testing
exposure to report is the 1080-point surface, zero development-split configurations (there is no
shell in this phase, so Stage A and Stage B were never run), and two charged evaluations.
