# team-07 — nomination rationale

**Family:** cross-sectional mispricing
**Mandate:** rolling pairwise cointegration on log prices, preregistered half-life, divergence stop
**Preregistration:** `lane/scouting/THESIS.md` (sealed in Phase S)
**Evidence:** `lane/feedback/t01.json`, `lane/feedback/t02.json` — visible development window only

---

## 1. What I am nominating

A book of **beta-hedged cointegrated pair spreads**, re-marked every sixth bar and held with
`None` in between.

At each scheduled decision, each eligible symbol is regressed Engle–Granger style on each of its
ten most return-correlated partners over a rolling 180-bar (60-day) window of log closes, with an
intercept. Each pair yields a hedge ratio β̂, a residual, an ADF t-statistic and a standardised
residual z. A pair is held when its **current excursion peak** lies inside the bounded interval
`[2.0σ, 3.5σ]`, its residual has not yet decayed back to 0.25σ, the excursion is younger than two
preregistered half-lives, β̂ has not drifted, neither leg has gapped, and the residual passes the
cointegration screen. Held pairs get an equal gross budget; legs are sized `1 : −β̂`.

The position is long the cheap leg and short the rich leg of the *hedged* spread. It is never a
cross-sectionally demeaned symbol score. That distinction is the single most important thing the
feedback taught me, and §3 is about why.

---

## 2. The mechanism, and who is on the other side

Unchanged from the preregistration, so I will state it compactly.

The Binance USD-M perp cross-section is low-rank: a few common stochastic trends explain most of
the covariation. A rolling Engle–Granger regression of `log P_i` on `[1, log P_j]` is therefore
mostly a data-driven estimate of *i*'s common-trend loading relative to *j*. β̂ absorbs the shared
trend; the residual is the relative idiosyncratic component of two names that load on it similarly.
I am not forecasting the common trend. I am forecasting that the residual around a locally
estimated relative price is not a martingale.

The return is compensation for **divergence risk** — being short an option on relationship
stability. The payoff is many small convergent gains against occasional large losses when the
relationship was structural and broke. Kondor's result is that this is not an engineering defect to
be designed away: convergence traders lose with positive probability even on fundamentally riskless
opportunities, and their returns are negatively skewed. Do & Faff put the base rate at roughly 62%
of pairs converging, which is why a stop has to exist at all. Secondarily the return is
liquidity provision, which is why the universe floor is set at the 25th percentile of trailing
quote volume rather than higher.

**Who is on the other side, named concretely:**

- **Leveraged retail being liquidated.** Forced liquidation is price-insensitive, concentrated in
  one contract, and mechanically overshoots. It is the largest source of single-name dislocation in
  perps. When a token-specific cascade moves one leg without moving its economic peers, whoever
  takes the other side is being paid.
- **Funding-carry desks.** Funding-rate arbitrage sizes the perp short leg *by funding*, not by
  relative value. A funding spike on one name pushes that specific perp below its peers for a
  reason unrelated to its relative fundamentals, and the flow unwinds when funding normalises. It
  is mean-reverting by construction. This is also why funding enters the book only as a veto: I
  want to be the counterparty to that flow, not to inherit its carry.
- **Rotation and narrative flow** — listings, promotions, sector narratives, scheduled unlocks —
  which pull capital into and out of individual names over hours to days.
- **Market makers laying off inventory** after absorbing one-sided flow in a single contract.

**A boundary I want to keep visible:** none of these flows are observable in my dataset. There is
no liquidation feed, no open interest, no order book. They are the economic story for why a
residual excursion exists and should decay. They are not a signal, and I have not tried to
reconstruct them from OHLCV.

**Why here specifically.** Every USD-M perp settles in the same quote asset, funds on the same 8h
clock, and is anchored to spot by the same premium-index formula with the same clamp. Two USD-M
perps are genuinely comparable instruments, so the spread is not contaminated by differing tick
conventions, settlement currencies, funding intervals or roll schedules. Shorting costs exactly
what going long costs. The mandate's chosen expression is more defensible in this venue than in the
equity markets where it was developed.

---

## 3. What the two trials actually said

Both trials failed admission. Neither is a P&L result I am arguing around; each is a structural
diagnosis.

| | t01 — hard-gated pair book | t02 — continuous cross-sectional book |
|---|---|---|
| gross edge, bps per unit turnover | **+5.97** | **−4.09** |
| annualised turnover | 168.8 | 231.1 |
| median effective breadth | 4.0 | 25.0 |
| breadth pass fraction | 0.24 | 1.00 |
| mean gross exposure | 0.379 | 0.667 |
| cost share of positive gross | 1.26 | — (denominator ≈ 0) |
| net Sharpe | −0.33 | −2.74 |
| positive fold fraction | 0.40 | 0.00 |
| failed gates | breadth, breadth persistence, edge density, cost share, triple cost | turnover ceiling, edge density, cost share, triple cost |

**Reading 1 — the mechanism was present in t01 and absent in t02.** t01's gross edge of 5.97 bps
per unit turnover on 168.8 of turnover is **10.1% annualised gross**, which is almost exactly the
base rate Krauss reports across 76 pairs-trading studies (~10.8%). That is the number the
preregistration told me to expect, and finding it is more reassuring than finding a large one would
have been. t02, which kept the same regressions but replaced the tail-conditional pair position
with a linear-in-z response demeaned across the cross-section, produced a **negative** gross edge.

Those two facts point the same way. t02 is not a cointegration book. Demeaning per-symbol residual
scores against the whole universe, soft-thresholding the aggregate and renormalising to constant
gross dissolves the β-hedge: what survives is a short-horizon cross-sectional reversal factor. My
own preregistration flagged that as the adverse case — the most liquid crypto names show daily
*momentum*, not reversal, and Fil & Kristoufek found pair-spread reversion at 5 minutes and one
hour and **absent at daily**. t02 went and collected that negative sign. The defence in §1.5 of the
thesis — that a β-hedged spread is not a raw return — is a claim I made in advance, and the only
evidence I have is consistent with it: the hedged, screened, tail-conditional expression earned
gross; the unhedged, unscreened, linear one lost gross.

I want to be precise about the strength of this. It is **not** falsifier F3. F3 required a control
set matched on |z| within ±0.25 that failed the cointegration screen; t01 and t02 differ in the
screen *and* the response shape *and* the aggregation, so the contrast is confounded. It is
suggestive evidence in the direction F3 predicts, and that is all.

**Reading 2 — t01 failed on structure and cost, not on signal.** Two numbers:

- Implied cost is `12.95% / 168.8 = ` **7.67 bps per unit turnover** at 1×. Surviving triple cost
  therefore requires a gross edge density above **~23 bps**. t01 delivered 5.97.
- t01 replaced `168.8 / 1095 / 0.379 =` **41% of its book every 8 hours**, for a signal whose
  information content changes at roughly `1/H = 6.7%` per bar. Roughly six-sevenths of that
  turnover carried no change in view.

The cause is visible in the same packet. Effective breadth of 4.0 and mean gross exposure of 0.379
mean the book was typically **two pairs**, capped at 0.10 per name — four names at 0.10 is a gross
of 0.4, which is exactly what was reported. When the book is two pairs, any change in the held set
turns over the whole book. The conjunction of hard gates (ADF ≤ −3.0 **and** peak ≥ 2σ **and** age
≤ 30 bars **and** β-drift **and** event veto **and** funding veto) admitted almost nothing:
~750 candidate pairs × ~5% passing a 5% screen × ~4.6% of the time at |z| ≥ 2 is between one and
two pairs, which is what the metrics show.

So the disease is churn and concentration. The mechanism is not what failed.

---

## 4. What changed, and against which declared trigger

Every parameter move below is a declared knob at a declared value. I am listing the trigger for
each so a later reader can check that I did not go shopping.

| knob | t01 | now | tier | trigger |
|---|---|---|---|---|
| `H` half-life | 15 | **30** | 1 | declared grid; see below |
| `N_pairs` | 20 | **30** | 1 | declared grid; breadth gate failed |
| `τ` ADF screen | −3.0 | **−2.6** | 2 (#7) | *"only if the screen admits fewer than `N_pairs` candidates at a majority of decisions"* — **met**: breadth pass fraction 0.24, median breadth 4 against `N_pairs` 20 |
| `m` partners | 5 | **10** | 2 (#9) | *"only if knob 7 is exhausted and breadth still fails"* — **partially met**; see below |
| `m_max` | 2 | **3** | 2 (#10) | *"only if the effective-breadth gate fails"* — **met** |
| `W`, `z_in`, `z_stop`, `z_out`, `e`, `δ`, `liq_floor`, `funding_veto`, `pair_weighting` | — | **unchanged** | — | no trigger met |

Three of these need more than a table row.

**`H` = 30 and the re-mark cadence are one decision, not two.** `H` enters only the excursion-age
stop and the funding horizon; it does not set the reversion speed I trade, which is set by the
entry/exit band and the residual's own dynamics. Moving it from 15 to 30 doubles the admissible
excursion age from 30 bars to 60 while keeping the stop at the declared `k = 2` half-lives. With
`W = 180` that keeps `W = 6H` exactly, at the tight end of the declared coupling. The honest
statement of what this buys is **breadth, not turnover**: a 2σ excursion in a residual whose own
half-life is 15–30 bars usually lasts longer than 30 bars, so `age ≤ 30` was very likely the
binding constraint in t01. It is coherent with the cadence in §5 — I am declaring the trade horizon
to be about ten days and therefore sampling it every two days.

**`m` = 10 is a sequencing deviation and I am flagging it as one.** The declared trigger says to
exhaust `τ` first. I have not spent a separate trial doing that, and with no further feedback
coming I will not get one. The arithmetic is why: `τ = −2.6` alone takes the expected admitted pair
count from ~1–2 to perhaps 5–15, still short of `N_pairs`. `m = 10` is a declared value of a
declared knob, opened on the same single piece of breadth evidence as `τ`. The surface is
unchanged; the order in which I walked it is not what I preregistered.

**`liq_floor` stays at 0.25 although its trigger fired.** Cost share failed in both trials, which
opens knob 13. I am declining to raise the floor to 0.50. The dominant term in cost share is
turnover, not the spread on the marginal name, and Farag et al. locate the liquidity-provision
premium precisely in the thinner names. Raising the floor would pay a certain cost in edge for an
uncertain saving in fees. I am recording the trigger as fired and unopened rather than quietly
skipping it.

---

## 5. The two structural changes that are supposed to fix the gates

### 5.1 Every gate is a taper, and the divergence stop is a bounded entry interval

The brief says the stop is the hard part of this mandate, and the reason is that **a distance stop
fires precisely when the trade is most attractive under the model**: if the OU is true, 4σ is a
better entry than 2σ. A pure loss stop is only correct if distance is evidence that the
*relationship broke* rather than that the opportunity grew.

So the stop is three stops, only one of which is a loss stop, and all three are stateless functions
of the window (commitment C4 — I cannot remember when a trade was entered, so the clock is "bars
since the residual last crossed its in-window mean"):

- **S1, excursion age (primary, model invalidation).** Under the preregistered OU an excursion
  should decay by 2⁻ᵏ in k half-lives. An excursion older than `k·H = 60` bars says the
  preregistered model is wrong *for this pair*, with no reference to P&L. It tapers to zero over the
  following half-life.
- **S2, relationship invalidation.** β̂ estimated on the recent half-window against β̂ on the full
  window; drift beyond 0.50 tapers the pair out. This is falsifier F2 turned into a live control.
- **S3, divergence (the loss stop).** Expressed on the **excursion peak**, not on current z, so it
  is a stateless reconstruction of "I would have been stopped out". Entry and stop are a single
  function: `strength = 0` below 1.75σ, `1` across `[2.0σ, 3.5σ]`, `0` above 4.0σ. That is Leung &
  Li's result written as code — the entry region is a bounded interval lying strictly above the
  stop, so the stop is not bolted onto an unchanged entry rule.

Every one of these, plus the cointegration screen, the β band, the correlation floor and the
funding veto, is a Lipschitz ramp instead of a step. A pair whose ADF t-statistic drifts across
−2.6 changes size by a few percent rather than round-tripping two legs. This is a turnover
reduction and a directly intended pass of the organizer's small-perturbation stability check.

The idiosyncratic-event veto stays hard, because it is a claim about kind rather than degree: a
single-bar move beyond 8 MAD-scaled deviations on either leg is news, and news is a permanent
break rather than a temporary excursion. It is a veto on entry and an exit trigger, never a reason
to size up. It is measured against a median absolute deviation because a genuine 8σ bar inflates an
ordinary standard deviation enough that an `e·std` rule would need a ten-sigma move to fire and
would sit inert.

### 5.2 Positions are held, not re-hedged

On five bars in six the strategy returns `None`. The evaluator still enforces membership exits,
delisting exits, participation limits and exposure reductions, so this is a decision not to
re-mark, not a decision to stop managing risk.

This is the largest single change and it is economic, not cosmetic. A convergence trade with a
ten-day half-life gains nothing from being re-hedged every eight hours. Worse, re-hedging a pair
back to constant *weight* means buying more of the diverging leg — averaging down — which is the
mechanism by which pairs books actually blow up. Holding fixed quantities lets the spread converge
and lets a diverging position shrink as a fraction of the book on its own.

Two further turnover reductions come with it:

- The per-pair budget is fixed at `GROSS / N_PAIRS`, **not** divided among the pairs actually held.
  A book with fewer live opportunities is simply smaller. This removes the rescaling ripple that
  turns every change in the opportunity count into turnover on every name. t02 renormalised to
  constant gross every bar and that is part of why its turnover breached the ceiling.
- Pairs are ranked by cointegration strength (which moves slowly over a 180-bar window) rather than
  by |z| (which does not), so the held set is stable between re-marks.

**The cost of this, stated plainly:** the divergence stop is only evaluated on scheduled bars, so a
broken pair can be carried for up to five extra bars — two days, or 20% of a half-life. That is a
real and deliberate exchange of stop latency for cost. It is the one place where the cost gates
have shaped a risk control, and I would rather name it than bury it.

### 5.3 The arithmetic this is aiming at

t01 re-marked 41% of its book per bar. The new book re-marks on ~17.5% of bars (`1/6 + 1/97`
less their overlap), and the marginal
pair is 1/30 of the book rather than 1/2, so a change in the held set no longer turns over
everything. Projected turnover is roughly **30–60 annualised**, which is 3–5× below t01 and far
inside the ceiling that t02's 231 breached. If the edge per position is unchanged, edge density
lands near **20–30 bps** against the ~23 bps that triple-cost survival needs, with additional
upside from removing pure set-churn turnover — turnover that generated cost and no P&L.

**This is an arithmetic projection from two data points, not a measurement.** The margin at triple
cost is thin and I am not going to dress it up. It is the honest expected value of the change,
and the direction is unambiguous even where the magnitude is not.

Breadth should follow from `N_pairs = 30`, `m_max = 3` and a per-name cap of 0.05 that is designed
not to bind: t01's breadth of 4 was an artefact of two pairs hitting the 0.10 cap, and a book of
~30 pairs across ~40 names has nothing like that shape.

---

## 6. What I did not do, and what would falsify this

### Falsifiers F1, F2 and F3 were never run. I have to say so.

The preregistration committed me to three mechanism measurements on visible development data:
out-of-window convergence rate (F1, retire below 55%), β stability (F2, diagnostic), and a
|z|-matched non-cointegrated control (F3, retire below a 5pp advantage). **None of them was
computed.** Phases 1–3 gave me no execution environment — no shell, no interpreter, no way to
run a data pass — only the organizer's metric packets. The preregistration assumed an
instrumentation capability I turned out not to have. That is a defect in the preregistration, and
it is mine.

What I have instead is the confounded contrast in §3: the screened, hedged, tail-conditional
expression earned gross edge and the unscreened, linear, cross-sectionally demeaned one lost gross
edge. It points where F3 predicted. It is not F3, and I am not going to call it F3.

### Why I am nominating rather than retiring

The preregistration says retire if F1 fails. F1 did not fail; it was never measured, which is a
different thing and a weaker position. What I do have is a mandate whose measured gross edge sits
almost exactly on the literature's base rate, failing on structure and cost in a way that is fully
explained by holding two pairs and re-marking them every eight hours. Fixing that is a structural
change, not a search for a better number, and the phase guidance is explicit that qualification is
a bar on structure and cost.

I am nominating a book I can explain end to end, at declared parameter values, with its stop
apparatus intact and its weakest joint — stop latency — named. I am not nominating my highest
development Sharpe, because I do not have a positive one, and I would not trust it if I did.

### An admitted gap in the preregistration

`REBALANCE_EVERY = 6` and `SAFETY_MODULUS = 97` are **not on the declared parameter surface**.
Section 5 of the thesis says that if I need a parameter that is not on the list, the honest report
is that the preregistration was incomplete. It was. The surface declared a decision grid of "every
bar" as a Tier-0 fixture and never contemplated declining to re-mark, which turns out to be the
most important cost control available to a book with a ten-day horizon on an 8h grid. I did not
search it: 6 bars is two days, chosen as one fifth of the preregistered half-life, and it is the
only value that has ever been written. `SAFETY_MODULUS` is not a tuning parameter at all — it is a
second, rare clock so that the schedule can never be degenerate if per-symbol history is not shaped
the way `RULES.md` describes.

### Trial count for deflation

Three distinct grid points have been instantiated, of which **two have been scored against
feedback** (t01, t02) and one is this nomination. Under coordinate descent from a declared centre
the realised trials are highly correlated, so the effective independent count is lower — but the
raw count is 3 and that is the number I report. The declared surface it sits inside is 504
admissible Tier-1 points × 26,244 Tier-2 = 13.2M, plus the one undeclared parameter above.

### What would falsify this book

Stated forward, on evidence I have not seen:

1. **Gross edge density below t01's 5.97 bps.** The entire thesis of this candidate is that most of
   t01's turnover was noise and that removing it leaves the P&L roughly intact. If density does not
   rise materially when turnover falls 3–5×, then the turnover *was* the signal — the book was
   being paid for churning, not for converging — and the mandate is dead in this venue.
2. **Gross edge density that rises but stays under ~23 bps.** Then the mechanism is real and
   uneconomic at 8h in this universe. That is Fil & Kristoufek's finding arriving on schedule: the
   effect lives at 5 minutes and one hour, and my data floor is above it. The honest report is that
   the family is present and untradeable at my sampling frequency, not that the design was wrong.
3. **Breadth still failing with ~30 pairs held.** That would mean the screen is admitting far fewer
   pairs than the count arithmetic in §3 predicts, i.e. residual cointegration among correlated
   perps is rarer than a 10% nominal screen suggests. It would falsify commitment C6's premise that
   the candidate set is large enough to be a portfolio.
4. **A drawdown concentrated in the five-bar hold windows.** That would say the stop-latency trade
   in §5.2 was priced wrong and that this horizon genuinely needs an every-bar stop — in which case
   the mandate's cost problem has no solution on this decision grid.

Failure 1 retires the mandate. Failures 2 and 4 are findings about the venue and the grid rather
than about cointegration, and I would report them as such.

---

## 7. Compliance notes

- `build_strategy()` returns an object with `target_weights(context, *, seed)`.
- Returns a finite `dict[str, float]`, `{}` for flat, or `None` to hold. Symbols come only from
  `context.eligible_symbols`.
- `sum(abs(w)) ≤ 1.0`, `abs(sum(w)) ≤ 0.20` and `abs(w) ≤ 0.05`, all inside the hard caps, enforced
  by reduction only in `_finalise`.
- Panels are aligned on the `open_time` **column**, never on the positional `RangeIndex`. Symbols
  with fewer than `W` rows, duplicated stamps, or rows off the common grid are dropped rather than
  forward-filled.
- The funding frame is read as `funding_rate`, and its timestamps are used only for sorting — never
  compared against a bar timestamp, so the veto cannot be silenced by a dtype mismatch.
- **No state across decisions.** No instance attributes are written; every quantity, including both
  the excursion clock and the rebalance clock, is a pure function of the past-only window.
- **No randomness**; `seed` is discarded. Exact-replay deterministic.
- **No absolute dates and no time-of-day conditioning.** Both clocks are row counts, so they are
  invariant under calendar shift. I am still declining to use the 00:00/08:00/16:00 funding clock,
  which remains a genuine candidate effect I am leaving on the table (commitment C5).
- **Scale invariance is structural.** The regression carries an intercept, absorbed by centring, so
  `P → cP` shifts `log P` by `log c` and leaves β̂ and the residual untouched.
- **No symbol identity anywhere.** Selection is purely statistical.
- No network, subprocess, filesystem, `eval`/`exec`/`compile`/`__import__`/`getattr`/`setattr`, no
  RNG, no embedded data, no fitted parameters.
- No volatility targeting. The ex-ante risk unit is the engine's, and nothing here conditions on
  realised or forecast portfolio volatility.
