# RATIONALE — team-03, refinement trial

Defensive / beta-controlled allocation. Risk-premium harvesting.

---

## 1. Diagnosis of t01 — this is a design failure, not a parameter failure

The seed was rejected on `gross_edge_density`, `cost_share` and `survives_triple_cost`. Every
structural gate passed: median effective breadth 22.1, mean gross exposure 0.877, long/short
exposure share 55.7/44.3, active bar fraction 1.0, risk unit capped only 2.2% of bars. So the seed
*is* a portfolio. It just cannot pay for itself.

Reconstructing the cost line from the packet:

| quantity | value | how |
|---|---|---|
| annualised turnover | 43.55 | reported |
| gross edge | 6.50 bps per unit turnover | reported |
| implied gross P&L | ≈ 2.83 %/yr | 43.55 × 6.50 bps |
| cost per unit turnover | **7.20 bps** | (net₁ₓ − net₃ₓ) / 2 = 3.133 %/yr, ÷ 43.55 |
| implied gross from the P&L line | ≈ 2.22 %/yr | net₁ₓ (−0.914 %) + cost (3.133 %) |
| **breakeven density at 3× cost** | **21.6 bps/turnover** | 3 × 7.20 bps |

The two independent estimates of gross P&L (2.83% from the density line, 2.22% from the cost
line) bracket the truth; I use the lower one where it matters.

**The whole result is one number: the book earns 6.50 bps per unit of turnover and pays 7.20 bps
for it.** It is underwater at 1× before triple cost is even considered. `cost_share = 1.153` is
the same fact restated, and `net_sharpe = −0.038` is what a 3.3× shortfall looks like once it has
been divided by a 10.3% volatility.

Two things follow, and they set the entire design.

**(a) No parameter moves a 3.3× gap.** Re-cutting terciles or re-estimating volatility changes
the numerator by tens of percent, not by 230%. Something structural has to change.

**(b) The gross edge is not the primary problem; the trading rate is.** 2.83%/yr of gross on a
10.3% vol book is a gross Sharpe of ~0.27 over 808 days — a t-statistic near 0.4, which is to say
*not distinguishable from zero*, but also not negative. A weak-but-real slow premium destroyed by
fast trading and a weak-but-absent premium look identical in the net column and completely
different in the density column. 6.50 bps/turnover is the signature of the first: the book is
paying for churn it is not being compensated for. At 43.55 turnover on 1095 decisions/yr, the seed
was moving ~4% of gross every 8 hours. For a defensive premium the literature measures at
horizons of one week to one quarter, that is almost all noise.

So: **cut the trading rate hard, and move as much of the return as possible onto a component that
accrues with time held rather than with volume traded.**

---

## 2. The mechanism, and who is on the other side

My preregistered thesis (§1.2) explicitly refuses the Frazzini–Pedersen leverage-constraint story
on this venue: leverage is not scarce on Binance, it is the product, and maximum leverage is
*tighter* on the high-volatility names, which inverts the classic constraint. The premium, if it
exists here, has to come from somewhere else, and the thesis names it:

> In a perpetual future, a large part of the compensation for holding the defensive side is not an
> unobservable expected-return wedge — it is an explicit, periodic, observable cash flow: funding.

Leverage-seeking and lottery-seeking directional demand concentrates in high-volatility,
low-quality contracts. On this venue that concentration is *metered*: when the perp trades above
index — which is what crowded levered long demand is — longs pay shorts every eight hours in cash.
My claim is strictly about the **cross-sectional spread in funding**, not its level; the level is
positive by construction (the +0.01%/8h interest term and the clamp asymmetry) and harvesting it
would just be a short-the-market bet in costume. A dollar- and beta-controlled book nets the level
out and keeps only the spread.

**Paying me:** levered retail directional longs on alt perpetuals, for whom a 20%-annualised
financing charge dripped out in 8h increments is far less salient than a quarterly roll gap; and
trend-following systematic books, which are structurally long the highest-beta names in an uptrend
and mechanically add as realised volatility rises.

**Already on my side, and therefore my competition:** delta-neutral basis and cash-and-carry desks
shorting the highest-funding perps against spot, and token treasuries and market makers hedging
long spot inventory. Their presence is exactly why the spread does not fully close, and why the
capacity binds hardest in the thin contracts my liquidity screen removes rather than the
mid-liquidity band I trade.

**This is why the diagnosis and the mechanism point the same way.** Funding accrues per unit of
*time held*. It does not require a cross-sectional price spread to materialise, and it does not
require me to trade to collect it. A book whose return is partly metered carry has a
`gross_edge_bps_per_turnover` that rises mechanically as the holding period lengthens — which is
the exact quantity t01 failed on. A pure price-return ranker does not have that property.

---

## 3. What changed, and what did not

### Changed — turnover, by construction, three ways

1. **A 42-bar (14-day) rebalance grid; `None` in between.** `None` skips only the strategy
   rebalance and holds quantities, so the inter-grid turnover is *zero*, not "small". This is the
   slowest option on my declared surface (§4.1 knob 3, values {21, 42} bars) and the direction my
   preregistered tie-break already pointed.
2. **The longest declared estimation windows.** `vol_lookback = 189` bars (63 days), funding
   averaged over the same 189 intervals, beta correlation over 378 bars. Slow signals produce slow
   rank churn, and rank churn is what turnover is made of. 63 days is also where the FRL 2026
   revisit puts the crypto low-volatility effect (2–3 month measurement).
3. **One holding period of score smoothing.** The composite is the average of its value at this
   grid point and at the previous one. This halves the rank churn that has to be paid for at each
   rebalance without shortening any estimation window. It is the one construction choice not
   literally enumerated in §4 — see §6.

Expected effect. Turnover at each grid point is roughly (drift of held weights over 14 days ≈ 0.16
of gross) + (rank churn ≈ 0.3) ≈ 0.45–0.5, over 26 grid points/yr ⇒ **≈ 12–15 annualised, a 3–3.6×
cut from 43.55.** At unchanged gross that puts density at 19–24 bps against a 21.6 bps triple-cost
breakeven — i.e. *the turnover cut alone only buys breakeven*. The margin has to come from §4.

### Changed — the return source

`funding_tilt = on` (§4.1 knob 5): trailing mean funding enters the ranking composite as an
equal-weight z-score component alongside realised volatility. This is the load-bearing channel of
my thesis promoted from a *return component I hoped to collect passively* to a *signal I select
on*. High trailing funding is crowded levered long demand; I want to be short it.

### Deliberately **not** changed — `junk_leg` stays off

Two of the four preregistered junk components (Amihud illiquidity, inverse trade count) sort the
short leg toward *thin* contracts. When the diagnosed failure is cost, deliberately shorting
illiquidity is the wrong direction: it raises realised cost per unit turnover and pushes into the
0.1%-of-prior-24h-volume participation limit. This is the Novy-Marx–Velikov microcap trap in its
crypto form. §4.3 declares the junk composite as an atomic on/off — I am not entitled to keep MAX
and drop Amihud after the fact, and I am not going to. Off, which is also the declared tie-break.

### Unchanged — everything §4.2 fixed by declaration

Parkinson high–low volatility estimator; FP beta `ρ̂·σ̂ᵢ/σ̂ₘ` shrunk 0.6 toward 1; 378-bar
correlation window (808 days = 2424 bars, so 378 leaves 84% of the window testable and the
step-down contingency does not trigger); equal-weight member index; each leg independently scaled
to unit beta; liquidity screen at the top 70% by trailing 63-bar median quote volume; per-name cap
5% of gross; seasoning ≥ 252 bars; rank-weighted portfolio form.

---

## 4. Construction

Per decision, at a grid point only:

1. **Clock.** `clock = max(len(bars[s]))` over eligible symbols; act only when
   `clock % 42 == 0`. This is *data-relative*, not calendar-relative: under a calendar shift the
   row counts shift identically, so the grid lands on the same data rows. A timestamp-modulo grid
   would not, and would read as absolute-date targeting.
2. **Panel.** Every column aligned on `open_time`, never on the positional `RangeIndex` — symbols
   have unequal history and an integer-index concat returns a nearly all-`NaN` panel and a silently
   empty book.
3. **Screen.** ≥ 252 bars of seasoning, then the most liquid 70% by trailing 63-bar median quote
   volume.
4. **Composite.** `score = −½·rankZ(Parkinson vol) − ½·rankZ(mean funding)`, averaged over this
   grid point and the previous one. Rank z-scores rather than raw z-scores: bounded by
   construction, invariant to monotone rescaling (which is what the magnitude-scale check tests),
   and stable to small perturbations. Names missing funding score neutral on that component rather
   than being dropped.
5. **Beta.** `β = 0.6·ρ̂σ̂ᵢ/σ̂ₘ + 0.4`, ρ̂ over 378 bars against the equal-weight member index,
   clipped to [0.35, 2.5].
6. **Legs.** FP rank weights `k − k̄`; positive part is the long leg, negative part the short leg,
   each normalised to unit gross. Each leg scaled by `1/β_leg` and renormalised to gross 1.0, so
   portfolio beta is zero by construction — this is FP's leg scaling, *not* a cross-sectional
   regression of the score on beta. That distinction matters: regressing β out would delete most
   of the low-volatility tilt, since low-vol names are low-beta names. BAB keeps the beta bet and
   sizes the legs so the net index exposure is zero.
7. **Net.** FP leg scaling implies a positive dollar net (the long leg is levered up because it is
   low beta). Clipped at 0.20 against the protocol's 0.25 limit. If it clips, residual index beta
   goes mildly negative; I would rather be slightly short the index than breach.
8. **Caps.** Per-name 5% of gross, enforced inside each leg so the leg shares — and therefore the
   beta neutrality — survive capping. Leg members below 1% of their own leg are dropped: they
   carry no signal and only turnover. Final clip at 0.095 against the 0.10 limit.

Expected structural profile: effective breadth ≈ 25–30 (capped linear ramp over two legs), gross
1.0 submitted, exposure split ≈ 58/42 long/short with zero index beta.

**Compliance.** Stateless — every call is a pure function of `context`; no attribute is mutated,
no RNG, no clock read, no absolute date, no symbol literal, no price level, no embedded data.
`seed` is unused because there is nothing stochastic to seed. Symbols come only from
`eligible_symbols`. `sum|w| ≤ 1.0`, `|sum w| ≤ 0.20`, `|w| ≤ 0.095`, all enforced at emission.
I do not touch book volatility anywhere — that is the organizer's risk unit.

---

## 5. What would falsify this

The thesis falsifiers stand as preregistered. What this trial adds is that the packet can now
distinguish between them.

- **F1 (mandate).** If the beta-neutral low-minus-high volatility spread has Sharpe ≤ 0, or is
  negative in a majority of 90-day blocks, the defensive premium does not exist here. `t01` gives
  a hint and no more: gross ≈ +2.2 to +2.8%/yr with a t-statistic near 0.4 — the right sign,
  indistinguishable from zero. `positive_fold_fraction = 0.2` is a real warning, but it is a *net*
  statistic on a book whose costs exceeded its gross, so it cannot yet separate "no premium" from
  "premium eaten".
- **F2 (mechanism).** If the funding component of the spread is ≤ 0, my stated mechanism is wrong
  and any positive result is an unexplained regularity, not my thesis. I will say so rather than
  retrofit.
- **F3 (junk leg).** Not tested here; the leg is off.

**The specific, falsifiable prediction of *this* candidate,** readable directly off the next
packet:

| observable | prediction | what it means if it misses |
|---|---|---|
| `annualised_turnover` | 10–18 (from 43.5) | the turnover mechanism failed — most likely the grid clock never fires or fires every bar, i.e. `bars` is windowed rather than full history |
| `gross_edge_bps_per_turnover` | > 21.6 | below this, no holding period saves it at 3× cost |
| `cost_share_of_positive_gross` | < 0.4 (from 1.153) | |
| `triple_cost_annualised_return` | > 0 | |
| `median_effective_breadth` | 25–30 | leg capping or dust removal is concentrating the book |
| `long_exposure_share` | ≈ 0.55–0.60 | FP leg scaling is not producing the expected beta split |

The honest arithmetic is that turnover reduction alone lands me *at* breakeven; the funding tilt
has to supply the margin. So the sharpest single read on the next packet is: **if turnover lands
near 13 and density is still under ~20 bps, then the cross-sectional funding spread is not paying
for the trading either, F2 has effectively fired, and there is no slower version of this book that
rescues it.** That is a retirement signal, not a tuning signal, and I will read it that way.

---

## 6. Preregistration accounting

Honest ledger, because the deflated-Sharpe trial count is supposed to mean something.

**Within the declared 48-cell surface:** `vol_lookback = 189`, `beta_shrink = 0.6`,
`rebalance = 42`, `junk_leg = off`, `funding_tilt = on`. One cell.

**Two implementation resolutions §4 did not specify:**

- *Beta's volatility inputs.* §4.2 names Parkinson as "the volatility estimator" but the
  equal-weight index has no high/low, so a Parkinson numerator over a close-to-close denominator
  would bias every β by a constant. I use close-to-close for **both** legs of the β ratio and
  Parkinson for the volatility **signal**. This is a consistency fix, not a knob; the alternative
  is a systematically mis-scaled β.
- *Score smoothing across two grid points.* This is genuinely additional and I am flagging it
  rather than burying it. It is not one of the rescues §3 forbids — it is not faster rebalancing,
  a different start date, an excluded symbol or episode, a lower cost assumption, or a new data
  field. It is strictly *slower*, adopted for the diagnosed cost reason. It expands my effective
  trial count and I will carry it as such.

**Not done, and named so that doing it later would be visible:** I did not tighten the liquidity
screen, though the cost diagnosis tempts toward it — §4.2 fixed it at 70% and it is not mine to
move now. I did not retune the per-name cap. I did not split the junk composite.

---

## 7. What I expect to go wrong

- **Beta-hedge failure is correlated with my worst days.** In crypto risk-off, cross-sectional
  beta dispersion collapses toward 1 and realised betas jump; a book neutralised on trailing betas
  is under-hedged precisely when it matters. Symmetrically, in an alt melt-up the high-volatility
  short leg runs away from a stale hedge ratio. Defensive is short convexity — I expect sharp,
  clustered drawdowns, not gradual ones. The 14-day grid makes this *worse*, not better: I have
  traded responsiveness for cost, deliberately.
- **The funding tilt is short crowded momentum.** The price return of the short leg partially
  offsets the carry, and the offset is worst in exactly the squeezes that generate the carry. If
  the offset exceeds the carry, F2 fires.
- **Beta may simply not be priced in the crypto cross-section.** Borri, Liu, Tsyvinski & Wu (2026)
  find market beta has no significant predictive power and that most equity smart-beta strategies
  are subsumed by a four-factor crypto model. My distinction — those are spot, coin-level, total
  returns, and a perpetual's return is the price return *minus funding* — is real, but it is the
  whole of my defence, and it lives entirely in the funding leg.
- **`bars` windowing would break the clock.** RULES states long-listed contracts carry thousands
  of rows while recent members carry a few hundred, which I read as full history truncated at the
  boundary. If the frames were a fixed trailing window instead, `max(len(...))` saturates and the
  modulo grid either fires every bar or never fires. This is the single assumption in the
  candidate that could silently change the book's character, and `annualised_turnover` in the next
  packet reads it directly.
- **Turnover could undershoot the band.** I am targeting ~13 against a seed at 43.5. If the
  turnover band has a floor above that, I fail a structural gate I passed last time. I judged that
  risk worth taking: a book that clears the turnover floor and fails triple cost is not a book.
