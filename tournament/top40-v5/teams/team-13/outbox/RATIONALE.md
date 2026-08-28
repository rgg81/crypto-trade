# team-13 — universe inclusion and attention

**Family:** event and state · **Mandate:** weekly membership entry and exit
**Phase:** refinement, on one feedback packet (`t01`, the unmodified organizer seed)

---

## 1. What the feedback actually said

`t01` is the organizer seed, not my design, but it is the only evidence I have and it is
informative about the *lane*, not just the seed.

| Gate | Value | Verdict |
|---|---|---|
| median effective breadth | 14.5 | pass |
| mean gross exposure | 0.867 | pass |
| long / short exposure share | 0.491 / 0.509 | pass |
| annualised turnover | 163.8 | pass (inside band) |
| participation | — | pass |
| **gross edge per turnover** | **−1.83 bps** | **fail** |
| **cost share of positive gross** | **2.7e11** | **fail** |
| **survives triple cost** | **−33.2% / yr** | **fail** |

Those three failures are one failure with three names. `gross_edge_bps_per_turnover` is
negative, so the book loses money *before* a single basis point of cost; the `cost_share`
figure is large only because its denominator — positive gross P&L — is essentially zero.

The seed's cost level falls straight out of the packet. Gross annual return
≈ −1.83 bps × 163.8 turns ≈ **−3.0%**; net was **−14.6%**. The difference is cost:

> **≈ 11.6% / yr of cost on 163.8 turns ⇒ ≈ 7 bps per unit of turnover.**

Triple cost is then ≈ 35%/yr of drag, which is why `triple_cost_annualised_return` is
−33.2% and why nothing about the seed's signal could have saved it.

**The diagnosis is structural, not parametric.** At 7 bps per turn, surviving 3× cost
requires roughly **21 bps of gross edge per unit of turnover**. No cross-sectional signal
in 8h alt-perp data produces 21 bps per turn while turning over 164 times a year. The
seed's design spends its entire turnover budget re-deciding at high frequency. The fix is
not a better ranker at the same frequency — it is a book that **holds**. That is the one
change this candidate is really making, and every other choice below follows from it.

Note also what the seed *did* get right and I must not break: breadth 14.5, gross 0.87,
and a genuine 49/51 exposure split. Those are the gates a narrow event book fails. Any
"three entrants a week" expression of this mandate would fix the edge gate by destroying
the portfolio gates. So the book has to be an event book **and** a portfolio.

---

## 2. Mechanism

From the sealed thesis (§1.2), the committed sign is:

> **short the crowded entrant, long the uncrowded entrant, mirror on the leaver leg.**

Split the mandate into its two legs and the algebra collapses to one line. Let
`A_in ≥ 0` be entrant intensity, `A_out ≥ 0` leaver intensity, `C` the crowdedness of
leveraged positioning. The entrant leg is `−A_in · C` and the mirrored leaver leg is
`+A_out · C`; with `E = A_in − A_out`,

```
score = −E · C
```

which is exactly what `candidate.py` computes. Quadrant by quadrant:

| event | state | position | what I am doing |
|---|---|---|---|
| entrant | crowd levered long | **short** | selling immediacy to attention buyers; paid funding while I wait |
| entrant | crowd absent / short | **long** | genuine liquidity migration, not an attention shock — it continues |
| leaver | crowd levered long | **long** | buying inventory from holders facing a delisting / exit clock |
| leaver | crowd absent / short | **short** | selling to forced short-coverers into the same clock |

The economics are index inclusion restated for a venue with no substitutes. Wurgler &
Zhuravskaya's result is that the inclusion effect survives precisely where arbitrage
between close substitutes fails; an alt USD-M perp is the limiting case (no ETF, no
creation/redemption, no cash-index arb, no sector basket). Greenwood & Sammon's
"disappearing index effect" is the base rate I have to beat, and the reason the book is
*conditional*: Messari's practitioner work found Binance listings delivered ≈ 0%
five-day outperformance once outliers were controlled, so the unconditional
long-the-new-name trade is dead **on this venue specifically**. The return has to come
from the state, not the event. Barber & Odean supply the attention channel — retail buys
what has abnormal volume and extreme returns, and universe entry is by construction
exactly that name.

Crucially, on perpetuals the reversal trade and the carry trade are the same trade: when
the crowd is levered long an entrant, funding turns positive and the short is paid every
settlement. What I give up is convexity — funding is capped at 0.75 × maintenance margin
ratio while a squeeze is not. That asymmetry is not a flaw in the thesis; it is the
identity of the premium.

### 2.1 Who is on the other side

1. **Leveraged retail directional traders on Binance Futures**, selecting off volume- and
   gainer-ranked tables. Barber & Odean's attention buyers, at 10–50×. Primary
   counterparty on the crowded-entrant short.
2. **Copy-trading followers**, who synchronise and deepen that flow.
3. **Other systematic books running the same trailing-dollar-volume screen** — the crypto
   analogue of Russell reconstitution. Published rules-based crypto indices reconstitute
   on liquidity screens with record dates; when a name crosses, many books add it in the
   same window.
4. **Token treasuries, market makers on loan-and-option deals, and unlock recipients**,
   distributing supply into attention.
5. **Forced closers at delisting** — Binance removes USD-M perps for low volume and
   reduced liquidity, with scheduled auto-settlement and non-reduce-only orders restricted
   before the cutoff. A counterparty with a hard clock is the cleanest one that exists.

I sell immediacy to (1)–(3) when they most demand it and buy it from (4)–(5) when they
least can wait, and I am paid funding on the leg where the crowd is levered long.

---

## 3. How the mandate's event is observed without state

`DecisionContext` carries no membership history — only the current `eligible_symbols` —
and persistent state across decisions is forbidden. The literal "member at week *w*,
absent at *w−1*" event is therefore **unobservable to a compliant strategy**. My sealed
parameter surface anticipated this: knob 5 level (ii) declares a *self-computed trailing
dollar-volume rank-crossing proxy*. That is what is implemented, from three past-only
measurements per symbol, each recomputed from scratch at every decision:

| component | construction | what it captures |
|---|---|---|
| rank crossing | cross-sectional rank of mean quote volume over the last week **minus** its rank over the preceding two weeks | the inclusion-threshold crossing itself |
| dollar-volume surge | `log(mean quote volume, 1w / mean quote volume, prior 2w)` | Barber & Odean's abnormal-volume trigger, in time series |
| seasoning | bars of available history at the decision | how *newly the contract exists* — the purest form of "new member" |

Crowding uses exactly the declared composite (knob 4, level ii), no more:

| component | construction |
|---|---|
| funding level | mean `funding_rate` over the trailing three weeks (`L_z = 63`, knob 2 level 2) |
| taker-buy skew | `Σ taker_buy_quote_volume / Σ quote_volume − 0.5` over the same window |

Both `E` and `C` are built by ranking each component to `[−1, 1]`, averaging, and
re-ranking. Rank rather than z, because alt-perp funding and volume cross-sections carry
outliers that would otherwise set the scale for every other name; the bounded score also
keeps the product bounded, which is what makes the `±0.10` cap non-binding for most names.

### 3.1 Declared deviations, stated rather than buried

Per §4.3 of the thesis I owe an explicit account of anything outside the sealed surface:

- **Seasoning is an added component of `E`.** It is not a dollar-volume construct. I hold
  that it implements the *fixed* membership definition of §4.1 (a newly listed contract is
  definitionally a new member) rather than being a searched knob, but it is a deviation and
  I count it. **Effective N = 49, not 48.**
- **Trade-size and funding-slope were dropped.** §1.2 named "small average trade size" and
  "rising funding" as crowding proxies, but §4.2 knob 4 enumerates only funding level and
  taker imbalance. I stayed inside the declared surface and left both out.
- **Bounded rank scores replace "z clipped at ±3".** Same intent — outlier control — one
  choice, stated once.
- **This is one configuration**, evaluated once: `H = 3 weeks`, `L_z = 63`,
  `S = funding + taker composite`, `A` = the rank-crossing proxy. The threshold `θ` does
  not appear because the book is continuous in the state rather than split at a cut; that
  removes a knob rather than adding one.

---

## 4. How the cost gates are attacked

Everything below exists to move `gross_edge_bps_per_turnover` from −1.83 to something
above ~21, and all of it works on the denominator first.

**Hold the event.** The declared linear decay over `H = 3` weeks is implemented statelessly
as a lag-weighted average of the same rules evaluated at 21 historical offsets, weights
declining linearly to zero at three weeks. The book at each decision is the decayed average
of the books these rules would have chosen over the past three weeks. It is recomputed from
scratch every time — no state, no look-ahead — but it behaves like a held position with a
decaying event weight. Two effects: per-bar innovations are averaged across offsets whose
new information is largely independent, cutting signal noise by roughly √21; and the target
vector moves slowly, so turnover collapses. I expect roughly **40–70 annualised turns**
against the seed's 164.

**Slow the state.** `L_z = 63` bars (the declared slow level) rather than 21. Crowding is a
state; measuring it over three weeks costs almost nothing in fidelity and buys a great deal
of smoothness.

**Weight toward what can absorb the book.** Entrants and leavers are by construction the
widest, thinnest names in the universe — thesis failure mode #5, and the reason the sealed
falsifier F1 carries a magnitude clause. Weights are multiplied by
`0.25 + 0.75 × liquidity_rank`, which keeps the leaver leg alive but stops the book paying
top dollar for its worst fills, and keeps positions inside the 0.1%-of-prior-24h-volume
participation limit rather than relying on the evaluator to truncate them.

**Spend turnover only on conviction.** Names inside a soft threshold go to exactly zero, so
the book does not churn a long tail of near-zero positions. The threshold is continuous
(`sign(u)·max(|u| − τ, 0)`), so a small perturbation moves weights smoothly instead of
flipping names in and out — this is a turnover control *and* a small-perturbation-stability
control. `τ` adapts downward if fewer than ~30 names would survive, so breadth cannot fail
in a thin cross-section.

**Cost arithmetic at the three charge levels**, using the 7 bps/turn implied by `t01` (my
liquidity tilt should make it lower, but I am not going to assume that):

| turnover | 1× | 2× | 3× | gross Sharpe needed at 3× (11% vol unit) |
|---|---|---|---|---|
| 40 | 2.8% | 5.6% | 8.4% | ≈ 0.76 |
| 60 | 4.2% | 8.4% | 12.6% | ≈ 1.15 |
| 164 (seed) | 11.5% | 23% | 34% | ≈ 3.1 — unreachable |

That table is the whole refinement. A book that only survives at 1× is not a book, and at
164 turns nothing survives at 3× regardless of signal quality.

---

## 5. Why this stays a portfolio

The organizer scales every book to a common ex-ante volatility unit before re-applying
caps, so I do not target volatility anywhere. But the risk unit does determine whether I
pass `mean_gross_exposure`, and that is worth reasoning about explicitly. The seed reached
11.1% realised vol at 0.867 gross on 14.5 effective names — consistent with ~50%
idiosyncratic vol per name and `√Σw²` ≈ 0.26. This book runs ~30–45 non-zero names with
effective breadth ~20–30, giving `√Σw²` ≈ 0.18–0.22 and a raw book vol *below* the unit, so
the scaler levers toward the 1.0 gross cap rather than shrinking me. Breadth and gross
exposure are therefore load-bearing in the same direction as cost, which is a pleasant
coincidence rather than a designed one.

Both sides are used by construction: the score is demeaned and then exactly dollar-balanced
by scaling the heavier side, so `Σw = 0` before the per-name cap and `|Σw| ≤ 0.20` after it,
with `Σ|w| ≤ 1` and `|w| ≤ 0.10` enforced directly.

---

## 6. Compliance and the invariance checks

- **Stateless.** No instance attributes, no accumulation across calls. Every number is
  recomputed from `context`. Exact-replay determinism and future-append invariance follow
  from this rather than being patched in.
- **No panel-alignment trap.** The book never concatenates per-symbol frames. All
  cross-symbol work is on *scalars* per symbol, so the positional-`RangeIndex` failure that
  silently produces an all-`NaN` panel and an empty book cannot occur here. Where time
  alignment is genuinely needed — matching funding rows to a bar — it is done by
  `searchsorted` on `open_time` / `funding_time`, never by position.
- **Column names taken from `protocol.py`**, including `funding_rate` (not
  `last_funding_rate`), with `volume` / `taker_buy_volume` as fallbacks.
- **Magnitude-scale equivariant.** Every input is a ratio (`volume surge`, `taker share`), a
  rank (`crossing`, `liquidity`), a count (`seasoning`), or a rate (`funding`). A uniform
  rescaling of prices or volumes leaves the book unchanged.
- **Calendar-shift equivariant.** No absolute date is read. Bars-per-week is *inferred* from
  the median `open_time` spacing rather than hard-coded at 21, so a different cadence
  rescales every window consistently.
- **Pseudonymisation-safe.** No symbol literal appears; all operations are symmetric in
  symbol order (ties take average ranks).
- **Small-perturbation stable.** All transforms are continuous or rank-based; the only
  thresholding is soft.
- **No RNG** (`seed` is accepted and discarded), no network, subprocess, filesystem,
  `eval`/`exec`, no embedded data or fitted parameters.
- Per-symbol extraction is guarded field-by-field and a symbol that cannot be measured is
  skipped rather than poisoning the cross-section; the book returns `{}` only if fewer than
  10 names can be scored at all.

---

## 7. What would falsify this

The sealed falsifiers stand, restated against what the feedback packet can actually show:

**F1 — the mandate's falsifier, made numeric.** *If entrants and leavers show no abnormal
return around their membership change, inclusion carries no attention effect.* Observable
here as `gross_edge_bps_per_turnover`. **If it is not positive, the event leg is dead and I
say so.** I will not respond by widening the event window or adding event types until
something clears.

**F1b — the magnitude clause, which is the one that matters at this venue.** A positive but
small gross edge falsifies the *tradeable* claim even if the effect is real. **If gross edge
per turnover is positive but below ~21 bps, this mandate does not clear costs in Binance
perpetuals**, and the honest report is that the effect exists and is not harvestable — not a
search for a cheaper parameterisation. `survives_triple_cost` is the gate that decides this
and it is the one I am designing against.

**F2 — the state claim.** The book earns from the *interaction*, not from either main
effect. If the return is actually coming from unconditional crowding (a funding-carry book
wearing an inclusion costume) then the state conditioning has not been demonstrated. The
signature would be a book whose long/short split tracks funding rank rather than the
event-by-state quadrants; because `E` is demeaned and the score is `−E·C`, net funding
exposure is ≈ 0 by construction, so a large realised carry contribution would itself be the
falsification.

**F3 — the unseasoned-universe rerun, which the mandate demands I prove rather than
discover.** I committed before seeing data that **the effect should be at least as strong in
the unseasoned universe, not weaker** — an unseasoned universe contains more entrants,
younger entrants, and more extreme attention shocks. This candidate is built to make that
testable rather than accidental: seasoning is an explicit, first-class component of `E`, so
young contracts are actively engaged and *conditioned on crowding* rather than being an
unmodelled exposure the book quietly dies of. **I am falsified if the unseasoned rerun
halves the effect or inverts its sign** — that would mean what I measured on the seasoned
universe was survivorship, and the mechanism is wrong for this venue.

**F4 — sign integrity.** The four quadrants in §2 are preregistered. If the data shows the
opposite sign, that is a falsification of the mechanism, not a parameter to flip. Any book
that later trades the inverted sign will be labelled post-hoc and reported without the
pretence of preregistration.

**Known failure modes, preregistered so none can later be sold as a discovery:** decay with
arriving capital (the equity instance lost ~90% of its effect in three decades); migration
into the anticipation window; momentum crash on the short leg — shorting a crowded entrant
during a real bull leg, with capped funding compensation against an uncapped squeeze, is the
single most likely way this book dies; wash-traded volume corrupting the rank crossing;
funding-cap saturation censoring the crowding proxy exactly at the extreme where it should
be strongest; and funding being a *price* rather than a *quantity*, which with no open
interest in the dataset caps how sharply the state can ever be measured here.

Retiring honestly remains available. If `gross_edge_bps_per_turnover` comes back negative
again, the correct report is that this lane's mandate does not pay at Binance perpetual
costs — not a forty-ninth configuration.
