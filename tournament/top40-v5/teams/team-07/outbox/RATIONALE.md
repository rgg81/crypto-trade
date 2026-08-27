# team-07 — Discovery candidate: cointegration convergence

**Family:** cross-sectional mispricing
**Mandate:** rolling pairwise cointegration on log prices, preregistered half-life, divergence stop
**Preregistration:** `lane/scouting/THESIS.md` (sealed in Phase S)
**Feedback consumed:** none. `lane/feedback/` is empty; this is the first pass.
**Grid points evaluated against feedback so far: 0.**

---

## 1. What this book is, in one paragraph

At every 8h decision I build a log-close panel aligned on `open_time`, drop the thinnest quartile of
the cross-section by trailing median `quote_volume`, and for each surviving symbol test its five
most return-correlated partners. Each candidate pair gets an Engle–Granger regression of the
higher-return-variance leg's log price on the other's, with an intercept, over a 180-bar (60-day)
window. Pairs whose residual passes a Dickey–Fuller screen at t ≤ −3.0 form the tradable set. Within
that set I hold pairs whose residual is currently displaced from its in-window mean, sized β-hedged
and equal-gross per pair, at most 20 pairs, each symbol in at most two of them. Gross is normalised
to 1.0 before the exposure caps; I never touch volatility — that unit belongs to the engine.

Every constant in `candidate.py` is a Tier-0 fixture, a Tier-1 declared centre, or a Tier-2 declared
default from §5 of the thesis. **Nothing has been moved in response to a result, because there is no
result yet.** This is the seed of my own search, deliberately the plainest expression of the mandate
I can write and still call it cointegration.

## 2. The mechanism, and why the residual should revert

The claim is *not* that two perpetual contracts share a fundamental equilibrium. It is that the
Binance USD-M cross-section is low-rank — one or two common stochastic trends dominate log prices —
so a rolling EG regression of `log P_i` on `[1, log P_j]` is mostly **an estimate of i's loading on
the common trend relative to j**. β̂ absorbs the shared trend; the residual is what is left, which is
the *relative idiosyncratic* component of two names that move together for structural reasons.

I am therefore not forecasting the market. I am claiming that when that residual makes a large
excursion, the excursion was caused by flow rather than by information, and that flow reverses. The
compensation for taking that side is divergence risk: many small convergent gains against occasional
large losses when the relationship was real and then broke. Under Kondor (2009) that negative skew
is the premium, not a defect to engineer away — which is why my falsifiers below are mechanism tests
and not P&L tests.

Contract homogeneity is why this expression is more defensible here than where it was developed.
Every USD-M perp settles in the same quote asset, funds on the same 8h clock, and is anchored by the
same premium-index formula. Two perps are genuinely comparable instruments, so a log-price spread
between them is not contaminated by differing tick conventions, settlement currencies or roll
schedules. And a short costs what a long costs — no locate, no recall, no borrow — so the asymmetry
that Do & Faff blame for the decay of equity pairs profitability does not exist in this venue.

## 3. Who is on the other side

Named concretely, and with the boundary stated up front: **none of these flows are observable in my
dataset.** There is no liquidation feed, no open interest and no order book here. They are the reason
a residual excursion exists and should decay; they are not inputs. I am not going to spend a trial
trying to reconstruct liquidations from OHLCV.

- **Leveraged retail being liquidated.** Forced liquidation is price-insensitive, lands in one
  contract, and mechanically overshoots. It is the largest single-name dislocation source in crypto
  perps. When a cascade moves one leg double digits without moving its economic peers, whoever takes
  the other side is paid for it.
- **Funding-carry and basis desks.** These size the perp short leg *by funding*, not by relative
  value. A funding spike on one name gets that specific perp sold below its peers for a reason
  unrelated to its relative fundamentals, and the position unwinds when funding normalises. That
  flow is mean-reverting by construction, and it is roughly a third of the crypto hedge fund
  universe, so it is large enough to move a name.
- **Rotation and narrative flow.** Listings, exchange promotions, sector narratives and token unlocks
  pull capital into and out of individual names over hours to days.
- **Market makers laying off inventory** after absorbing one-sided flow in a single contract.

The uncomfortable half of that list: the same paper that identifies crypto short-reversal as a
liquidity-provision premium finds the premium *largest where liquidity is worst* — and Binance perps
are, by construction, the most liquid crypto instruments there are. I am fishing in the part of the
pond where the fish are smallest. That is priced into my expectation, not hidden from it.

## 4. The stop — the part the mandate calls hard, and why it is three things

The hard problem is that **a distance stop fires exactly when the trade is most attractive under the
model.** If the residual really is an OU process, a spread at 4σ is a *better* entry than one at 2σ.
So a pure distance stop is only coherent if distance is evidence that the *relationship broke*, not
evidence that the opportunity grew. That is a claim about model invalidation, and it deserves its own
instrument. Hence three stops, only one of which is a loss stop:

- **S1 — excursion-age (primary).** Under a preregistered half-life H, an excursion should decay by
  2⁻ᵏ in k half-lives. If the residual has been on one side of its in-window mean for more than
  `k·H = 30` bars (10 days), the preregistered model is wrong *for this pair* and I hold nothing.
  Scale-free, requires no P&L, and is the stop most directly aligned with the mandate's falsifier.
- **S2 — relationship invalidation.** The screen is recomputed every decision; a pair that stops
  passing is out. Additionally β̂ re-estimated on the trailing half-window must be within 50% of β̂ on
  the full window. This is the thesis's F2 diagnostic turned into a live control.
- **S3 — divergence (the loss stop).** `|z| ≥ 3.5` in formation-window σ. It exists because roughly
  38% of pairs trades historically never converge and something must close them. Its declared range
  includes **off**, precisely so a later trial can tell me the stop is destroying value — a live
  possibility under Kondor.

Plus an **idiosyncratic-event veto**: a single-bar move on either leg exceeding 8× that leg's own
trailing dispersion, occurring inside the current excursion, is treated as news. News is a permanent
break, not a temporary excursion. This is the observable shadow of the unlocks, delistings and
listing shocks I cannot see directly. It vetoes entry and forces exit; it is never a reason to size
up.

**All four are stateless.** The rules forbid state across decisions, so I cannot remember when a
trade was entered. Every stop is therefore a function of the rolling window alone: the clock is
"bars since the residual last crossed its in-window mean", not "bars since I entered". The position
itself is *reconstructed* from the residual path — a pair is held iff, since the last mean crossing,
the peak |z| reached the entry band, never reached the divergence stop, current |z| is still above
the take-profit band, and the excursion is younger than k·H. This is a faithful path-consistent
replay of an entry/hold/exit rule with no memory, and it satisfies exact-replay determinism by
construction rather than by patch. It also gives me hysteresis for free — positions are held from
|z|=2.0 down through |z|=0.25 rather than flapping at a single threshold — which matters for the
turnover and cost gates.

One consequence of that clock is worth stating rather than discovering later: because the age is
measured from the **mean crossing** and not from entry, a slow-building divergence that takes 25 bars
to reach |z| = 2.0 has only 5 bars of life left and may never be traded at all. With H = 15 the
`k·H = 30` bar budget is comparable to a whole typical OU excursion, so S1 at the declared centre is
an aggressive stop — it discards the longer half of excursions on the grounds that they are
inconsistent with the preregistered half-life. That is what a model-invalidation stop is *for*, and
`k` has {1, 2, 3, off} in its declared range if the feedback says the cut is too deep. What I will
not do is reinterpret the clock as running from entry, because a stateless strategy has no entry to
run it from.

**Funding is treated as a veto, not as alpha.** A pair that is long a persistently
positive-funding name and short a persistently negative-funding name bleeds whether or not the price
spread converges. I veto a pair when its adverse trailing carry, compounded over the preregistered
half-life, exceeds the convergence gain the trade is waiting for. This is a genuine ex-ante
observable cost with no analogue in the equity pairs literature, and it is not a place I want to
earn a return — that would be a different family.

## 5. Structural properties that were designed in, not patched on

- **Magnitude-scale equivariance.** The regression carries an intercept, so `P → cP` shifts `log P`
  by `log c`, is absorbed by α̂, and leaves β̂ and the residual untouched. The z-score, the screen and
  the stops are all functions of the residual.
- **Symbol pseudonymisation.** No symbol identity appears anywhere. Pair enumeration is by integer
  index; the regressand is chosen by *return variance*, which is rename- and scale-invariant, so
  relabelling the universe cannot change which pairs form or which direction they regress in.
- **Calendar shift.** No absolute dates, no time-of-day conditioning. This costs me something real —
  the 00:00/08:00/16:00 UTC funding clock is a plausible effect and I am declining to use it — and I
  am recording that as a deliberate forfeit.
- **Small-perturbation stability.** The screen admits a large candidate set and the book holds up to
  20 pairs; no single threshold decides the book. The one place I am genuinely exposed is `Z_IN`,
  since it gates entry — a pair sitting at |z| = 1.99 flips on a perturbation. Breadth is the
  defence: with 20 pairs, one flip is 5% of gross.
- **Two-sided by construction.** Every pair is one long leg and one short leg. The "both sides
  genuinely used" gate is satisfied structurally, not statistically.
- **Effective breadth.** 20 pairs with each symbol in at most 2 of them means at least 20 distinct
  names. `M_MAX = 2` also makes the 0.10 per-symbol cap nearly automatic at full breadth.

## 6. What would falsify this

The mandate's falsifier — *if cointegrating relationships do not survive out of the window they were
estimated in, there is nothing to converge to* — was operationalised in §3 of the thesis before any
data was mounted. Restated here so the commitment is visible next to the code:

- **F1 (hard).** Freeze α̂, β̂ and the residual moments at t; evaluate the frozen spread forward over
  k·H bars with no re-estimation. Among frozen spreads at |z| ≥ 2.0, the fraction reaching |z| ≤ 0.25
  before touching |z| = 3.5 or running out of clock. A driftless random walk from z = 2.0 with
  barriers at 0 and 3.5 converges 42.9% of the time; the equity base rate is ~62%. **If the observed
  fraction is below 55%, F1 fails and I retire the mandate rather than search for a window or
  threshold that lifts it.**
- **F3 (hard).** Build a control set of pairs at the same t that *failed* the cointegration screen
  but had |z| matched within ±0.25. **If the screened set's convergence fraction does not exceed the
  control's by at least 5 percentage points, F3 fails** — the screen adds nothing over "the spread is
  wide" — and I do not nominate a cointegration book on the strength of a distance effect, **even if
  it makes money.**
- **F2 (diagnostic).** Median |β_{t+W} − β_t| / |β_t| on the next non-overlapping window. Above 0.50
  the cointegrating vector is being redefined faster than the spread can reach it. A passing F2 does
  not rescue a failing F1.

**The most likely killer is not the stop; it is the sampling frequency.** Fil & Kristoufek found
crypto pair-spread mean reversion at 5 minutes and at 1 hour and *absent at daily*. My grid is 8h —
squarely in the dead zone between the two. Meanwhile crypto short-horizon reversal concentrates in
illiquid names while the liquid ones show daily momentum, and my universe is by construction the
liquid end. My defence is that a β-hedged spread is not a raw return: the hedge removes the common
trend that carries the momentum. **That defence is a claim, not a fact, and F1 tests it directly.**

A second, cheaper way this dies: turnover. A 5-day half-life on an 8h grid implies a lot of trading,
and a full round-trip on both legs of a pair costs roughly 20bp gross at taker fees — about 60bp
under the triple-cost gate. If gross edge per unit turnover does not clear that, the honest report is
that the mechanism exists and is not harvestable at this frequency. **I will not tune H until
turnover lands inside the gate**; that would let the cost gate choose my half-life instead of the
mechanism.

## 7. Implementation choices the preregistration did not pin down

Per the thesis's own closing rule — if I need something not on the declared list, the honest report
is that the preregistration was incomplete — these five were under-specified and I fixed each at the
simplest admissible value rather than choosing among them. **None is a knob I will turn, and if a
later phase needs to move one I will say so explicitly.**

1. **Augmenting lags in the residual Dickey–Fuller regression: 1.** Zero lags over-reject under
   serially correlated increments; one lag is the cheapest correction. The test regression carries no
   intercept because the EG residual is mean-zero by construction.
2. **Which leg is the regressand: the one with higher return variance.** EG is direction-asymmetric.
   The common alternative — run both directions, keep the stronger rejection — adds a second
   selection channel on top of the screen. The variance rule is deterministic and invariant under
   both renaming and price rescaling.
3. **"Adverse funding carry" as a magnitude test, not a sign test.** A pure sign veto would reject
   about half of all signals and import a systematic carry tilt — a different family leaking into
   this one. I veto only when H·|carry| exceeds |z|·σ_u, i.e. when funding actually swamps the trade,
   which uses no parameter outside the declared surface.
4. **"Trailing leg dispersion" in the event veto is a MAD scale, not a standard deviation.** This one
   I want to be loud about, because the naive reading is a silent no-op. A single 8σ bar inside a
   179-return window inflates that window's own standard deviation by about 17%, so an `e·std` rule
   would need a ~10σ clean move to fire and the veto would sit inert while looking active. The median
   absolute deviation (×1.4826, the standard normal consistency factor) does not move with the
   outlier, so `e = 8` means what it says. `e` itself is untouched at its declared default. Because
   8h crypto returns are fat-tailed, a MAD scale runs somewhat below the standard deviation, so in
   practice this veto will fire on roughly 5–6 std-measured sigma — which is the intended order of
   magnitude for "this was news".
5. **Cap ordering: gross → per-symbol clip → net.** Every step after the first is a reduction, so all
   three constraints hold simultaneously at the end. The net fix scales the dominant side only,
   preserving relative weights within each side.

I should also flag, without dressing it up: **at the declared default the ADF screen is loose.** With
180 observations the 5% Engle–Granger critical value sits nearer −3.34 than −3.0, so `ADF_TAU = -3.0`
is closer to a 10% test and admits roughly one candidate pair in ten by chance alone. That is a
consequence of the Tier-2 default I preregistered, not a choice made here, and it is exactly the
condition F3 is designed to detect. If F3 fails, this is the first place to look.

## 8. What I want out of the feedback packet

Ranked by what would change my next move, not by what would look good:

1. **Effective breadth and mean number of held pairs.** If the book is routinely holding far fewer
   than 20 pairs, the declared trigger for opening `τ` (Tier-2 #7) has fired and that is a
   contingency, not a search.
2. **Turnover and gross edge per unit turnover, at 1× and 3× cost.** This decides whether the
   mechanism is harvestable at 8h at all. It is the fastest available proxy for the frequency problem
   in §6.
3. **Cost share split between fees and funding.** If funding dominates, Tier-2 #14 opens. If fees
   dominate, the answer is a longer half-life, not a better filter.
4. **Mean holding period.** If it sits far below `k·H = 30` bars, S1 is cutting trades short rather
   than catching broken ones, and `k` is the first Tier-1 coordinate to move — which is also the
   order the thesis committed to, stops first.
5. **Participation.** The 0.25 liquidity floor is a guess at where the participation cap binds.
6. **Whether the book ran at all.** A flat book for the whole window means the panel alignment or a
   filter is wrong, not that the edge is absent — and those two look identical in a Sharpe number.

Performance is reported here and enforced on blocks I never see. With twelve feedback-driven trials,
a development Sharpe is a statement about a search rather than about an edge. I am not going to
hill-climb it. The two numbers that decide whether this mandate survives are F1 and F3, and neither
is a P&L number.
