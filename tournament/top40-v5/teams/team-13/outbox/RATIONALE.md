# team-13 — universe inclusion and attention (nomination)

**Family:** event and state · **Mandate:** trade weekly membership entry and exit
**Thesis:** `lane/scouting/THESIS.md`, sealed 2026-08-26 · **Evidence:** `t01` (organizer seed), `t02`

---

## 0. The falsifier fired. Reporting it first, because that is the result.

My sealed F1 read:

> I am falsified if |t| < 2.0 on that pooled spread, **or if the spread's magnitude is smaller than a
> round-trip cost estimate for the marginal-liquidity names that constitute entrants and leavers.**

I now have that round-trip cost estimate, and it is the most reliable number in this lane because two
structurally unrelated books agree on it to within 6%:

| | t01 (organizer seed) | t02 (my thesis, expressed) |
|---|---|---|
| annualised turnover | 163.77 | 65.91 |
| gross return `= edge/turn × turns` | −1.831 bps × 163.77 = **−3.00%** | −5.416 bps × 65.91 = **−3.57%** |
| net return | −14.64% | −8.54% |
| **implied cost** | 11.64% / 163.77 = **7.11 bps/turn** | 4.97% / 65.91 = **7.54 bps/turn** |

Call it **7.3 bps per unit of annualised turnover.** `survives_triple_cost` therefore requires

> **gross edge > 3 × 7.3 ≈ 22 bps per unit of turnover.**

I measured **−5.4**. The magnitude clause of F1 has fired, on precisely the quantity it named.

**What has *not* fired is F4.** The gross Sharpe is −3.57 / 9.71 = **−0.37 over 808 days**, i.e.
|t| ≈ **0.55**. That is not an inverted mechanism; it is *no measurable effect in either direction*,
sitting ~27 bps/turn below the cost bar. The seed shows the same thing (gross Sharpe −0.27, |t| ≈ 0.40).
So the honest statement is:

> **On visible development data, the weekly-inclusion event carries no return I can distinguish from
> zero, and it is an order of magnitude short of clearing Binance perpetual costs as I expressed it.**

I am not flipping the sign. F4 forbids it, and the arithmetic makes it pointless anyway: inverting
−5.4 gives +5.4 bps/turn, still 17 bps short, obtained from a t-statistic of 0.55. That would be
fitting a sign to noise *and* failing the gate.

I am also not searching for configuration 49 on a metric with |t| = 0.55. Twelve feedback-driven
trials make a development Sharpe a statement about a search; two make it a statement about nothing.

**Why nominate at all, then.** Because qualification is a bar on *structure and cost*, ranking happens
on sealed evidence, and I have one thing worth putting forward: a genuine portfolio, on a
preregistered mechanism, whose one remaining problem is a cost arithmetic I can now attack with a
*measured* number rather than a fitted one. Retiring would forfeit the lane to keep a book I already
know how to make cheaper. What I will not do is dress up the negative result — it is stated above,
first, and it is the honest reading of this nomination.

---

## 1. Mechanism

**The event decides who is in the book; the state decides the sign and the size.** `score = −E · C`,
which is the sign committed in the sealed thesis §1.2, unchanged:

| event | state | position | what I am doing |
|---|---|---|---|
| entrant | crowd levered long | **short** | selling immediacy to attention buyers; paid funding while I wait |
| entrant | crowd absent / short | **long** | genuine liquidity migration, not an attention shock — it continues |
| leaver | crowd levered long | **long** | buying inventory from holders facing an exit clock |
| leaver | crowd absent / short | **short** | selling to forced short-coverers into the same clock |

A weekly liquidity-ranked universe is a published, forecastable, synchronized demand schedule. Entry
in crypto is *endogenous to attention* — a symbol enters because its turnover just surged relative to
peers — so membership entry is a dated, observable attention shock, exactly Barber & Odean's trigger
set (abnormal volume plus extreme recent return). Exit is genuinely forced: Binance delists USD-M
perps for low volume with a scheduled auto-settlement clock, and falling out of a volume ranking is
positively correlated with that.

The sign is conditional rather than unconditional because the evidence says the unconditional version
is dead *on this venue specifically*: after outlier control, Binance listings delivered ≈ 0% five-day
outperformance against ≈ 29% for Coinbase, and Zaremba et al. find crypto reversal is
liquidity-conditional — the illiquid majority reverses while the most tradeable names show momentum.
The return has to come from the state, not the event.

And on perpetuals the reversal trade and the carry trade are the same trade: when the crowd is levered
long an entrant, funding turns positive and the short is paid every settlement. What I give up is
convexity — funding is capped at 0.75 × maintenance margin ratio while a squeeze is not. That is not a
flaw in the thesis; it is the identity of the premium.

### 1.1 Observing the event without state

`DecisionContext` carries no membership history, so the literal "member at *w*, absent at *w−1*" event
is unobservable to a compliant strategy. Two past-only readings stand in, both recomputed from scratch
at every decision:

| component | construction | what it captures |
|---|---|---|
| **seasoning** | bars of available history at the decision | how newly the contract exists at all — definitionally a new member, and the one membership fact needing no cross-sectional estimate |
| **rank crossing** | rank of mean quote volume over the last week **minus** its rank over the preceding two weeks | the inclusion-threshold crossing itself |

They are averaged and then re-ranked, which means **`E` fires on concurrence**: the top of the
cross-section is *young and climbing*, the bottom is *old and falling*. That is deliberate. The
rank-crossing channel is attackable — fabricated volume demonstrably improves exchange rankings, so a
crossing can be an artifact — while seasoning cannot be faked. Requiring the two independent readings
to agree costs me the "established name surging into the top-N" case and buys a much lower false-event
rate. It is separately falsifiable (§4).

### 1.2 The state, net of volatility — the one measurement change

Crowding is the declared composite (funding level + taker-buy skew, both over the declared slow
`L_z = 63` bars), **residualised cross-sectionally on trailing realised volatility.**

This is a measurement fix, not a hedge bolted on afterwards. Funding is the *price of leverage*, and
the price of leverage rises with the volatility of the underlying. Raw funding rank is therefore part
crowding and part volatility rank wearing a crowding costume. Two consequences, one of which I
preregistered as the way this book most likely dies:

- **It mismeasures the state.** A name is crowded when the crowd pays *more than its own volatility
  already justifies*. That residual is the quantity §1.2 of the thesis was reaching for and did not
  isolate.
- **It made the book structurally short volatility.** `−E·C` shorts high-`C` names. If `C` is partly a
  volatility rank, then a dollar-balanced book is systematically short the high-volatility, high-beta
  half of the cross-section — which is preregistered failure mode #3, "momentum crash on the short
  leg," arriving not as a tail event but as a permanent drag. Both packets show a gross loss near −3%
  on books with nothing else in common; a common short-volatility exposure is the most plausible
  single explanation I can name, and this removes it.

I residualise the *state variable*, not the portfolio. A portfolio-level neutrality constraint would
be gutted by collinearity — the more the two are correlated, the more of the signal it deletes.
Residualising `C` and then re-ranking keeps the score bounded in [−1, 1] regardless of how collinear
the two turn out to be.

**This is not volatility targeting.** Nothing in this file scales the book by any volatility estimate;
gross is set by a pure sum-of-absolute-weights rescale. Removing a cross-sectional characteristic
exposure is a neutrality constraint of the same kind as `Σw = 0`. The ex-ante risk unit remains the
organizer's and I do not touch it.

---

## 2. Who is on the other side

1. **Leveraged retail directional traders on Binance Futures**, selecting off volume- and gainer-ranked
   tables the venue itself publishes. Barber & Odean's attention buyers at 10–50×. Primary
   counterparty on the crowded-entrant short.
2. **Copy-trading and social-trading followers**, who synchronize that flow and deepen the crowding.
3. **Other systematic books running the same trailing-dollar-volume screen.** Every rules-based crypto
   index screens on trailing liquidity with published record dates and buffers; when a name crosses,
   many books add it in the same window. The crypto analogue of Russell reconstitution.
4. **Token treasuries, market makers on loan-and-option deals, and unlock recipients**, distributing
   supply into attention — the natural sellers who appear once a name is finally liquid enough to sell
   into.
5. **Forced closers at delisting**, facing scheduled auto-settlement and restricted order types. A
   counterparty with a hard clock is the cleanest one that exists.

I sell immediacy to (1)–(3) when they most demand it, buy it from (4)–(5) when they least can wait,
and am paid funding on the leg where the crowd is levered long — in exchange for wearing the squeeze
tail. Madhavan's summary of the reconstitution trade is the same sentence: supplying immediacy is
profitable but undiversified, costly to trade, and price-risky on the unwind.

---

## 3. How the cost gates are attacked

All three failing gates are one gate with three names: `gross_edge_bps_per_turnover` is negative, so
`cost_share_of_positive_gross` explodes on a vanishing denominator and `survives_triple_cost` cannot
hold. Everything below works on the denominator, because 7.3 bps/turn is *measured* and a positive
signal is not.

**Hold longer: H = 3 → 6 weeks.** The declared linear decay is implemented statelessly as a
lag-weighted average of the same rules evaluated at 18 historical offsets. Doubling the hold roughly
halves turnover and so roughly doubles edge density for any given gross return.

*Why 6 and not 12.* The arithmetic keeps pushing longer — at 20 turns the required gross Sharpe falls
to ~0.45 — and I am deliberately not following it. My sealed grid was `H ∈ {1, 2, 3}` weeks, an
explicit statement that I believed this effect lives inside three weeks. Six weeks is a 2× departure
justified by a measured cost; twelve would be trading a preregistered belief for a gate, which is the
same overfitting in a different costume. Six also keeps expected turnover near **30–45**, comfortably
inside a band I have *observed* to admit 66 and 164 — the band's lower edge is unobserved and I would
rather not discover it by falling through it.

**Size to what the tape can absorb.** Each name's weight is ceilinged at
`0.10 × clip(capacity_i / median(capacity), 0.15, 1)`, where capacity is the more conservative of its
trailing-one-week and trailing-three-week mean quote volume. Entrants and leavers are by construction
the thinnest names in the universe. Oversizing them is paid for twice — once in impact, and once in
turnover spent every bar re-requesting a target the participation limit truncates. The ratio is taken
against the cross-sectional median, so the rule carries no absolute currency scale. The 0.15 floor
keeps the leaver leg alive rather than excluding the thin half outright.

**Stop generating turnover that carries no signal.** The previous book's soft-threshold cut adapted to
the 30th-largest score magnitude, so *every* weight moved whenever that one order statistic moved. The
cut is now fixed at 0.40σ. It remains soft — `sign(u)·max(|u|−τ, 0)` — so a name entering the book
enters at zero size and grows, and no name round-trips on a crossing.

**Bound the unseasoned leg by size, not by exclusion.** The kernel divides by its *full* mass rather
than by the mass a name was present for, so a contract's engagement ramps linearly from zero over its
first six weeks. The book is tilted toward young names by *signal* and bounded in them by *size*. The
mandate asks for the inclusion effect to be modelled explicitly rather than discovered by accident by
a book that then dies of it; this is that, in one line. The previous book instead required 42 bars of
history to trade a name at all, which silently excluded the purest entrants there are.

**The bar, stated plainly.** At ~35 turns and 7.3 bps/turn, triple-cost survival needs ≈ 7.7%/yr gross,
a gross Sharpe near **0.8**. I have measured **−0.37**. These changes raise edge *density* by roughly
2×; they cannot manufacture edge. If the mechanism is worth zero, this book will fail the same three
gates less badly. I would rather say that now than discover it later.

---

## 4. What would falsify this

**F1 — the mandate's falsifier, already fired on magnitude (§0).** Restated forward: if
`gross_edge_bps_per_turnover` returns below ~22 on sealed data, the weekly-inclusion event does not
clear Binance perpetual costs, and the correct report is that the effect is not harvestable here — not
a fiftieth configuration. Retiring honestly remains available and I will take it rather than search.

**F1b — concurrence.** `E` requires seasoning and rank crossing to agree. If the return survives
replacing the rank-crossing term with a constant, I have written a contract-age book with decoration,
not an inclusion book. This is the single most important ablation on the returning packet.

**F2 — the state claim.** The book earns from the *interaction*, not from either main effect. `E` is
re-ranked and hence roughly cross-sectionally centred, so net funding exposure is ≈ 0 by construction;
a large realised carry contribution would itself be the falsification — a funding-carry book wearing
an inclusion costume.

**F2b — the volatility residual, new and therefore owed a test.** I claim residualising `C` on
volatility is a *measurement* improvement, not a signal deletion. If the residualised book's gross
edge is materially worse than the raw one's, the volatility component *was* the signal, my §1.2 story
about the price of leverage is wrong, and I should say so.

**F3 — the unseasoned-universe rerun, which the mandate demands I prove rather than discover.** I
committed before seeing any data: **the effect should be at least as strong in an unseasoned universe,
not weaker** — it contains more entrants, younger entrants, and more extreme attention shocks. That
commitment stands and this book is built to make it testable rather than accidental: seasoning is a
first-class, explicit component of `E`, young contracts are actively engaged from ~24 bars of history
rather than excluded at 42, and their *size* is bounded by an explicit linear ramp. Because every
input is a cross-sectional rank, the book holds the relatively youngest and oldest names whatever the
universe's age distribution, so its unseasoned exposure is bounded by construction rather than by
luck. **I am falsified if the rerun halves the effect or inverts its sign** — that would mean what I
measured on the seasoned universe was survivorship.

**F4 — sign integrity.** The four quadrants in §1 are preregistered and unchanged. I have not flipped
them and will not. Any book trading the inverted sign is post-hoc and must be reported without the
pretence of preregistration.

**Preregistered failure modes that remain live:** decay with arriving capital (the equity instance of
this family lost ~90% of its effect in three decades — that is the base rate); migration of the move
into the anticipation window; momentum crash on the short leg, with capped funding compensation
against an uncapped squeeze; wash-traded volume corrupting the rank crossing; funding-cap saturation
censoring the crowding proxy exactly at the extreme where it should be strongest; and funding being a
*price* rather than a *quantity*, which with no open interest in the dataset caps how sharply the
state can ever be measured here.

---

## 5. Search accounting

Sealed surface: **N = 48**. Everything outside it, declared rather than buried, per thesis §4.3:

| # | deviation | why |
|---|---|---|
| 49 | seasoning as a component of `E` | declared at t02; a newly listed contract is definitionally a new member |
| 50 | `H = 6` weeks, outside the declared `{1, 2, 3}` grid | measured cost of 7.3 bps/turn; F1's magnitude clause |
| 51 | participation-share weight ceiling | cost control; replaces t02's multiplicative liquidity tilt |
| 52 | volatility residualisation of `C` | measurement of crowding net of the price of leverage; failure mode #3 |

**Effective N = 52**, and deflation should be computed on 52 regardless of how many configurations I
actually evaluated — I evaluated two. Declaring a surface and then claiming credit for under-searching
it is the same overfitting in a different costume.

Fixed and *not* searched: the sign (§1), both legs traded, `L_z = 63`, the state composite, no
per-symbol parameters, no sample-period selection, the harness cost model untuned, and no volatility
targeting.

---

## 6. Compliance

- **Stateless.** No instance attributes, no accumulation across calls; every number is recomputed from
  `context`. Exact-replay determinism and future-append invariance follow from this rather than being
  patched in. `seed` is accepted and discarded.
- **No panel-alignment trap.** Per-symbol frames are never concatenated. All cross-symbol work is on
  *scalars* per symbol, so the positional-`RangeIndex` failure that silently yields an all-`NaN` panel
  and an empty book cannot occur. Where time alignment is genuinely needed — matching funding rows to
  a bar — it is `searchsorted` on `open_time` / `funding_time`, never position.
- **Columns taken from `protocol.py`**, including `funding_rate` (not `last_funding_rate`), with
  `volume` / `taker_buy_volume` / `open` as guarded fallbacks. A symbol that cannot be measured is
  skipped rather than poisoning the cross-section.
- **Calendar-shift equivariant.** No absolute date is read. Bars-per-week is inferred from median
  `open_time` spacing, and an inference outside a sane range falls back to the 8h grid rather than
  being clipped onto a boundary — clipping would silently mis-scale every window in the file.
- **Magnitude-scale equivariant.** Every input is a ratio (taker share), a rank (crossing, capacity
  share, volatility), a count (seasoning), a log-return standard deviation, or a rate (funding). A
  uniform rescaling of prices or volumes leaves the book unchanged; the capacity ceiling is a ratio to
  the cross-sectional median.
- **Pseudonymisation-safe.** No symbol literal appears; ranks use average ties, so nothing depends on
  symbol ordering.
- **Small-perturbation stable.** All transforms are rank-based or continuous; the only threshold is
  soft, and it is fixed rather than adaptive.
- **Limits enforced directly**, with headroom: `Σ|w| ≤ 0.98` target and a hard renormalisation,
  `|w| ≤ 0.10`, `|Σw| ≤ 0.20` against a 0.25 limit, and sides dollar-balanced before sizing so both are
  genuinely used *on exposure*.
- No network, subprocess, filesystem, `eval`/`exec`, RNG, embedded data or fitted parameters.
