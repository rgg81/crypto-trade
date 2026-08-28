# RATIONALE — team-03 nomination

**Family:** risk-premium harvesting — defensive, beta-controlled allocation.
**Thesis of record:** `lane/scouting/THESIS.md`, sealed in phase S before data was mounted.
**Nominated book:** the trial-2 (`t02`) candidate, **unchanged**. Same constants, same construction,
same declared cell of the parameter surface.

---

## 0. The decision, stated first

I am nominating the book that was already admitted, without moving a single parameter.

That is a decision, not a default, and it has a cost I want to name: my development Sharpe of 0.77
does **not** clear its own preregistered deflated-Sharpe hurdle (§6). I am nominating anyway,
because the thing this phase actually gates on — structure and cost — this book clears by a factor
of 4.7, and because the two changes I seriously considered are untested variance with no feedback
left to test them against. The reasoning is in §5 and §6.

---

## 1. The mechanism

The canonical betting-against-beta story is a **leverage constraint**: investors who want more than
market return but cannot borrow bid up high-beta assets instead, so the premium is compensation for
supplying leverage to the constrained. **My thesis explicitly refuses that channel on this venue**
(THESIS §1.1), and it matters that it refused it before seeing data. Leverage is not scarce on
Binance USD-M — it is the product. Top leverage (125–150x) exists on the *lowest*-beta contracts,
BTC and ETH, while most alts cap at ≤75x. A return-hungry constrained trader here does not need to
buy a high-beta altcoin to get high-beta exposure; they can lever BTC directly and more cheaply.
The venue inverts Frazzini–Pedersen's constraint. Importing the equity rationale unexamined into a
125x venue would be the mistake.

What I claim instead:

> In equities, the compensation for holding the defensive side is an unobservable expected-return
> wedge you only ever recover in realized returns. **In a perpetual future, a large part of it is an
> explicit, periodic, observable cash flow: funding.** Leverage-seeking and lottery-seeking
> directional demand concentrates in high-volatility, low-quality contracts. When the perp trades
> above index — which is what crowded levered long demand *is* — longs pay shorts, every eight
> hours, in cash.

The **level** of funding is explicitly disclaimed as edge. It is positive by construction: the
+0.01%/8h interest term and the clamp asymmetry guarantee it, and harvesting it is a
short-the-market bet in a carry costume. It would be caught by the beta control, it is not what the
mandate names, and the organizer's common risk unit would not reward it. My claim is strictly about
the **cross-sectional spread in funding per unit of beta**, which survives beta-neutrality.

So the book: long low realised volatility / low trailing funding, short high realised volatility /
high trailing funding, each leg independently scaled to unit beta against the equal-weight member
index. Rank-weighted, Frazzini–Pedersen style, liquidity-screened, held 14 days.

**Why the mechanism and the cost diagnosis point the same way.** Funding accrues per unit of *time
held*. It does not require a cross-sectional price spread to materialise and it does not require me
to trade to collect it. A book whose return is partly metered carry has a gross edge per unit of
turnover that rises mechanically as the holding period lengthens — which is the exact quantity `t01`
failed on. A pure price-return ranker does not have that property. That is why the fix for the
cost failure was not a parameter: it was the mechanism doing what the thesis said it would do.

## 2. Who is on the other side

**Paying me:**

- **Levered retail directional longs on alt perpetuals** — the structural funding payer, routinely
  at 20x–100x. The 8h drip is the point: a ~20% annualized financing charge paid in 0.05% increments
  is far less salient than a quarterly roll gap, and the venue's design does nothing to make it
  salient.
- **Trend-following systematic books**, which are structurally long the highest-beta names in an
  uptrend and mechanically *add* as realised volatility rises — i.e. they buy exactly the leg I am
  short, exactly when my short leg is most expensive.

**Already on my side, and therefore my competition — I do not claim nobody does this:**

- **Delta-neutral basis and cash-and-carry desks** shorting the highest-funding perps against spot.
  The crowded competitor. My claim is narrower: the *beta-neutral, cross-sectional, index-relative*
  expression has a materially different risk profile from the delta-neutral carry expression, and
  carry capacity binds hardest in the thin contracts my 70% liquidity screen removes rather than the
  mid-liquidity band I trade.
- **Token treasuries and market makers** long spot inventory hedging by shorting perps. Their
  presence is why the spread does not fully close — and also why it should not be expected to be
  large.

**Why it should persist here specifically.** The payer population is renewable: each cycle recruits
new levered participants, unlike an equity anomaly worked over by a fixed institutional base. The
exchange's own risk machinery enforces the asymmetry — leverage brackets are tighter on high-vol
names and maintenance margin rises with notional, so the marginal levered long in a junk contract
sits closer to liquidation per unit of adverse move than the marginal levered long in BTC. And the
trade is unpleasant to hold: negative skew, squeeze risk, and paying funding whenever it flips. Premia
survive where the trade is uncomfortable.

---

## 3. What the two packets actually established

`t01` was the every-bar version of this book, with the funding tilt off. `t02` is the nominated
book. Reconstructing the cost line from each packet:

| | `t01` | `t02` | |
|---|---|---|---|
| admitted | **no** | **yes** | |
| failed gates | density, cost share, triple cost | none | |
| annualised turnover | 43.55 | 8.86 | −4.9× |
| gross edge / turnover | 6.50 bps | **115.0 bps** | +17.7× |
| implied gross P&L | 2.83 %/yr | 10.19 %/yr | +3.6× |
| cost per unit turnover¹ | 7.20 bps | 8.12 bps | +13% |
| triple-cost breakeven density | 21.6 bps | 24.4 bps | |
| **margin over triple-cost breakeven** | **0.30×** | **4.72×** | |
| net Sharpe | −0.038 | 0.773 | |
| triple-cost annual return | −7.18% | **+7.85%** | |

¹ `(net₁ₓ − net₃ₓ)/2`, divided by turnover.

Two readings matter.

**(a) The turnover cut alone does not explain the result.** Trading 4.9× less should raise density
4.9× at unchanged gross — 6.50 → 32 bps. It went to 115. So **3.6× of the improvement is gross P&L
that was not there before**: gross Sharpe went from ≈0.28 to ≈0.82. Something in the signal change
produced return, not just cost savings.

**(b) I cannot attribute that 3.6× to funding.** Three things changed at once between `t01` and
`t02`: the rebalance went from every-bar to 42-bar, `vol_lookback` went 63 → 189, and the funding
tilt turned on. My thesis says funding is load-bearing. The packet is *consistent* with that and
*does not demonstrate* it. I am recording this as an open attribution, not as confirmation. See §4.

**Honest scorecard against the predictions I published before `t02`:**

| observable | I predicted | actual | |
|---|---|---|---|
| turnover | 10–18 | 8.86 | missed low |
| density | > 21.6 bps | 115.0 | hit, by 5.3× |
| cost share | < 0.4 | 0.065 | hit |
| triple-cost return | > 0 | +7.85% | hit |
| effective breadth | 25–30 | 23.1 | missed low |
| long exposure share | 0.55–0.60 | 0.541 | missed low |

Three of six landed. All three misses are small and in the conservative direction. The density
prediction was beaten by 5.3×, which I read as **my cost model having been pessimistic**, not as
evidence the mechanism is five times stronger than I thought. Note also that cost per unit turnover
*rose* 13% when the book slowed down — larger clips per rebalance, as expected — so slowing further
would not be free.

---

## 4. Falsifier status — including the parts that did not resolve

The preregistered falsifiers stand as written. Where the evidence does not reach them, I say so
rather than declaring a pass.

### F1 — mandate level (the falsifier my brief names)

> *If low-volatility members do not outperform high-volatility members on a beta-adjusted basis, the
> defensive premium does not exist here.*

- **F1(a) — spread Sharpe ≤ 0: did not fire.** `t01` is the closest thing I have to the clean test —
  a pure beta-controlled volatility sort with no funding tilt. Its *gross* P&L was +2.83%/yr on
  10.3% vol, a gross Sharpe of ≈0.28 over 808 days, t ≈ 0.4. Right sign, indistinguishable from
  zero. The nominated book's gross Sharpe is ≈0.82. Both positive. F1(a) does not fire.
- **F1(b) — negative in a majority of non-overlapping 90-day blocks: I could not evaluate it.**
  The packets give me `positive_fold_fraction` on the *net* series — 0.2 for `t01`, 0.6 for `t02`.
  Neither is the preregistered test. `t01`'s 0.2 is a net statistic on a book whose costs exceeded
  its gross, so it cannot separate "no premium" from "premium eaten." `t02`'s 0.6 is on a different
  book. **The block-stability condition I said I expected to bite hardest is the one I never got to
  run.** I flag it as an unresolved gap rather than reading 0.6 as a pass.

### F2 — mechanism level

> *F2 fires if the funding component of the spread is ≤ 0.*

**Not evaluable from the packets, and therefore unconfirmed.** The metric schema gives me no
return decomposition, and `t01` → `t02` moved three knobs simultaneously, so I cannot isolate the
funding leg even by difference. My preregistered commitment was: *if F2 fires but F1 passes, I will
say in writing that my stated mechanism is wrong.* The adjacent honest statement, which is the one
the evidence supports, is this:

> The nominated book's positive result is **consistent with** the funding channel and is **not
> evidence for it over the alternatives** — a slower volatility sort, or a longer lookback, would
> produce the same packet. I have not earned the right to claim the mechanism is demonstrated.

I am not retrofitting a mechanism to whichever component happens to carry the return, and I am not
claiming a confirmation I do not have.

### F3 — junk leg

**Not live.** `junk_leg` is off, so F3 cannot be evaluated. It is off for a reason that predates
the packets and is reinforced by them: two of its four declared components (Amihud illiquidity,
inverse trade count) sort the short leg toward *thin* contracts. When the diagnosed failure mode was
cost, deliberately shorting illiquidity is the wrong direction — it raises realised cost per unit
turnover and pushes into the 0.1%-of-prior-24h-volume participation limit. That is the
Novy-Marx–Velikov microcap trap in crypto form. §4.3 of the thesis declares the junk composite as
atomic on/off; I am not entitled to keep MAX and drop Amihud after the fact, and I have not.

---

## 5. Why nothing moved

Four candidate changes, all rejected. Naming them so that adopting one later would be visible.

**(a) Nothing to hill-climb toward.** The book clears every gate with the tightest margin being
4.7× on the cost constraint that killed `t01`. There is no failing gate to fix. RULES is explicit
that twelve feedback-driven trials make a development Sharpe a statement about a search rather than
an edge; with the mechanism gates already passed, further feedback-fitting buys ranking noise.

**(b) Tranched rebalancing — considered, rejected.** The whole book is currently formed at one
instant every 42 bars (partly mitigated: the composite is averaged over the current and previous
grid points, so it is already a two-point formation-date smoother). Splitting into three staggered
tranches on a 14-bar sub-grid would diversify the formation date and cut the worst-case flat period
at the start of a run from 41 bars to 13. I rejected it because (i) 14 bars is *outside* my declared
`rebalance ∈ {21, 42}` surface and faster rebalancing is explicitly listed in THESIS §3 as a
non-rescue, (ii) it would raise turnover to an estimated 12–15 and cut density to ~75–85 bps — still
fine, but *estimated*, and I have no trial left to check the estimate, and (iii) `active_bar_fraction
= 0.988` says the flat-start cost is ~1.2% of bars, which is not a problem worth an untested
structural change.

**(c) Hardening the rebalance clock — considered, rejected as actively harmful.** The clock is
`max(len(bars[s]))` over **eligible** symbols. I looked at widening it to all keys of `bars` for
stability. That is a trap: a delisted contract keeps its frame and stops growing, so a long-history
dead symbol would **freeze the clock permanently** — the book would either never rebalance again or
fire every bar. Restricting to eligible symbols guarantees the argmax frame grows one row per bar,
so the clock is monotone. Its residual failure mode is bounded and benign: if the longest-history
name exits membership, the clock level jumps down and the 42-bar grid re-phases, costing at most one
extra holding period of staleness. Never permanent. **The existing clock is the right one; I left
it alone.**

**(d) Trimming the net long tilt — rejected as a mandate violation.** Realised exposure is 54.1%
long / 45.9% short, i.e. **+8.3% net long** of gross. That is not a drift; it is Frazzini–Pedersen
leg scaling working correctly. The long leg is low-beta, so equalising leg betas requires levering
it up, which leaves a positive *dollar* net at zero *index beta*. The mandate says neutral to the
equal-weight member index — beta-neutral, which is what this is. Forcing dollar-neutrality would
re-introduce the index exposure the construction exists to remove. The `NET_CAP = 0.20` guard
against the protocol's 0.25 limit was not binding (+0.083 observed) and stays as a guard.

**Also not done, named so that doing it later would be visible:** I did not tighten the liquidity
screen (fixed at 70% by declaration), did not retune the per-name cap, did not split the junk
composite, did not touch `vol_lookback`, `beta_shrink` or the correlation window, and did not
change a single numeric constant in the file.

---

## 6. Preregistration and deflation accounting

Trials consumed: **2**, both material. Cells of the 48-cell declared surface actually visited: **2**.
The nominated cell is `vol_lookback=189, beta_shrink=0.6, rebalance=42, junk_leg=off,
funding_tilt=on`. My §4.4 selection rule — highest deflated Sharpe, not highest raw Sharpe — selects
`t02` trivially, since `t01`'s Sharpe is negative.

I declared I would deflate at N = 49. Doing that honestly, on 2424 8h observations (808 days):

| | N = 49 (declared) | N = 2 (actually run) |
|---|---|---|
| expected-max Sharpe under the null | **1.53** annualised | 0.35 annualised |
| observed net Sharpe | 0.77 | 0.77 |
| **deflated Sharpe ≈** | **0.13** | 0.74 |

*(Standard Bailey–López de Prado construction; I do not have the skewness and kurtosis of the return
series, so these omit the higher-moment adjustment and should be read as approximations.)*

**Neither column clears 0.95.** Under my own declared standard, the development Sharpe of this book
is not evidence of an edge. I am stating this plainly because the whole point of §4 of the thesis was
to make the trial count mean something, and it would be worthless if I quietly skipped the
arithmetic when it came out against me.

So why nominate? Because deflated Sharpe answers "has this search found an edge?" and that is not
the question this phase asks. Qualification is a bar on **structure and cost**, and ranking happens
on sealed evidence I have never seen and cannot have overfit. What I can defend is:

- the book is a portfolio (breadth 23.1, gross 1.00, 54/46 exposure split, active on 98.8% of bars);
- it survives triple cost with 4.7× margin on the constraint that killed its predecessor;
- every constant traces to a document sealed before data was mounted, and none moved after a packet;
- my F1 falsifier did not fire.

My preregistered fallback — retire and nominate the unmodified seed — is conditioned on F1 firing.
It did not. Nominating is the committed action; claiming the Sharpe as proof of edge is not.

---

## 7. What would falsify this going forward

Sharpest first. These are readable on sealed evidence, and I would accept each as a defeat.

1. **Triple-cost return ≤ 0, or density below ~25 bps per unit turnover, on sealed blocks.** The
   cost margin is the one thing I have genuinely established. If it does not hold out of sample,
   nothing else about this book matters.
2. **Negative in a majority of non-overlapping 90-day sealed blocks.** This is F1(b), the condition I
   preregistered as the one I expected to bite and never got to run. A defensive premium that lives
   in one alt-cycle drawdown and nowhere else is a single trade, not a premium.
3. **The result surviving with the funding tilt removed.** That would not make the book fail — it
   would make my *thesis* fail while the book worked, which is F2. I would report it as an
   unexplained empirical regularity, not as the mechanism I preregistered.
4. **Gross Sharpe collapsing toward `t01`'s ≈0.28 on sealed data.** The 3.6× gross improvement is
   the least-verified number in §3 and the one most likely to be a 2-trial artifact.

## 8. What I expect to go wrong

- **The beta hedge fails when I need it.** In crypto risk-off, cross-sectional beta dispersion
  collapses toward 1 and realised betas jump, so a book neutralised on trailing 378-bar correlations
  is under-hedged exactly when it matters. Symmetrically, in an alt melt-up the high-volatility short
  leg runs away from a stale hedge ratio. Defensive is short convexity. **The 14-day grid makes this
  worse, not better** — I traded responsiveness for cost, deliberately and with my eyes open. Expect
  drawdowns sharp and clustered, not gradual. Development max drawdown was 12.6% against 12.5% vol;
  I would not be surprised by materially worse on a sealed liquidation cascade.
- **The funding tilt is structurally short crowded momentum.** The short leg's price return
  partially offsets the carry, and the offset is worst in exactly the squeezes that generate the
  carry. If the offset exceeds the carry, F2 fires.
- **Beta may simply not be priced in the crypto cross-section.** Borri, Liu, Tsyvinski & Wu (2026)
  find market beta has no significant predictive power there and that most equity smart-beta
  strategies are subsumed by a four-factor model. My answer — those are spot, coin-level *total*
  returns, and a perpetual's return is the price return *minus funding* — is real, but it is the
  whole of my defence, and it lives entirely in the leg I could not verify.
- **The literature contradicts itself on the lottery channel's sign.** Grobys & Junttila (2021) find
  low-MAX beats high-MAX; Ozdamar, Akdeniz & Sensoy (2021) find the opposite with a 3.03%/week raw
  spread. I could not resolve it in phase S and cannot resolve it now.
- **A thin sealed universe empties the book.** The construction requires 12 seasoned names and 5 per
  leg. Below that it returns `None` and holds. On a sparse block that is a flat book scoring as no
  edge. I accepted this floor rather than lowering it to chase a book I could not call a portfolio.

---

## 9. Compliance

Stateless: every call is a pure function of `context`. No attribute mutated, no RNG, no clock read,
no network, subprocess or filesystem access, no `eval`/`exec`, no embedded data, no fitted
parameters, no absolute date, no symbol literal, no price level. `seed` is unused because nothing is
stochastic. Symbols come only from `context.eligible_symbols`. The panel is aligned on the
`open_time` **column**, never on the positional `RangeIndex`. Funding is read from `funding_rate`,
and a missing or empty funding frame degrades the composite to volatility-only rather than raising.
Emission enforces `sum|w| ≤ 1.0`, `|sum w| ≤ 0.20` and `|w| ≤ 0.095`, all inside the protocol
limits. The rebalance grid is data-relative (row counts), not calendar-relative, so it is
calendar-shift equivariant; all signals are rank-based and log-ratio-based, so they are
magnitude-scale equivariant. **I do not target book volatility anywhere — that is the organizer's
risk unit** (it capped only 0.25% of bars in development).
