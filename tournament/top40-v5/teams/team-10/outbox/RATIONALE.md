# team-10 — taker-flow pressure — nomination

**Mandate:** aggressor imbalance as a signal about who is pressing and where the pressure resolves.
**Preregistered thesis:** `lane/scouting/THESIS.md`, sealed 2026-08-26.
**Evidence in hand:** two packets — `t01`, the unmodified organizer seed, and `t02`, my own book.

---

## 0. What I am nominating, in one paragraph

The same mechanism as `t02`, with one number changed: the position filter's half-life goes from 12
bars to 24, and the residualising regression window from 48 bars to 192. Both are turnover controls
and neither touches the signal. `t02` failed exactly two gates — `gross_edge_density` and
`survives_triple_cost` — which at a flat proportional cost are one failure: the book did not hold
long enough per unit of edge it collected. I am deliberately nominating a book whose expected net
Sharpe is **lower** than `t02`'s 0.763, because `t02`'s Sharpe was not admissible and this one should
be. That is the trade the phase guidance describes, and I am taking it with my eyes open.

---

## 1. What the two packets actually established

### 1.1 The cost is a flat proportional rate, and I know it to three digits

Three independent routes, across two books whose turnover differs by a factor of nine:

| route | arithmetic | implied cost per unit turnover |
|---|---|---|
| t01, density × cost share | `2.1509 × 3.48690` | **7.500 bps** |
| t02, density × cost share | `20.50958 × 0.36568` | **7.500 bps** |
| t02, the 1× / 3× pair | `ln(1.071811) = 0.069345`; `ln(0.9844132) = −0.015709`; `Δ = 0.085054` over 2 cost units → `0.042527/yr` ÷ `56.681` | **7.503 bps** |

The same rate at turnover 503 and at turnover 56.7 means the charge is **linear in turnover with no
observable convexity** over a 9× range. This is the single most useful fact I have, and it has a
consequence that removes most of the design space:

> There is no liquidity tilt, no participation shaping, no venue-aware sizing and no execution
> cleverness available to me. The charge is a constant times turnover. **The only lever on cost is
> how long I hold.**

I want to be explicit that this is why I am not "improving the signal" this trial. It is not that the
signal could not be improved; it is that the failing gate is not a signal gate, and with one packet of
feedback on my own book, touching the signal would be a search dressed up as a fix.

### 1.2 The falsifier did not fire — and it was a real test

My preregistration (THESIS §3, restated in the refinement rationale §4) committed, *before* the
packet, to this: **if turnover lands in band and `gross_edge_bps_per_turnover` comes back below ~5
bps, taker imbalance at 8h is spanned by the price-volume state, the mandate is falsified, and I
nominate the seed.** That threshold was written down before I saw a number.

`t02` returned **20.51 bps** — four times the falsification threshold — on a book that trades *only*
the component of aggressor imbalance orthogonal to the contemporaneous accumulated return, the
single-bar return and log quote volume. That residualisation is F1 and F2 compiled into the book
rather than reported alongside it: what earned the 20.51 bps could not have been a restatement of the
bar that produced it, because the part spanned by that bar was regressed out before any weight was
formed. `positive_fold_fraction = 0.8` (4 of 5 folds) is the closest thing the packet offers to my F3
sign-stability test, and it points the same way.

The sign also came out **as preset**. I fixed every conditioner sign by mechanism in the sealed
thesis and committed that a preferred opposite sign would falsify the thesis rather than parameterise
it. Gross return was positive at the preset signs. I did not have to flip anything, and I have not.

So: the mandate stands. What failed is cost, and cost is a structural quantity I can solve rather
than search.

### 1.3 What `t02` did *not* fail

Every structural gate passed, and they are the gates the phase guidance says qualification actually
turns on: `mean_gross_exposure` 0.99998, `median_effective_breadth` 22.79, long exposure share 0.5021
vs short 0.4979, `active_bar_fraction` 1.0, `risk_unit_capped_fraction` 0.055, `turnover_ceiling`
cleared, `ruined` false, `max_drawdown` 0.128. This is already a portfolio. I am not rebuilding it.

---

## 2. The mechanism

Binance publishes `taker_buy_quote_volume` per kline: the exchange's own ledger of which side crossed
the spread and paid for immediacy. It is reported, not inferred. The entire equity order-flow
literature runs on *estimated* trade signs — tick rule, Lee-Ready, bulk volume classification — and
carries an unknown measurement-error haircut. Here that haircut is zero. That is the structural
reason this lane is worth running at all.

```
imb_t = (2 · taker_buy_quote_t − quote_volume_t) / quote_volume_t     ∈ [−1, +1]
```

Every taker buy is matched by a maker sell, so `imb_t > 0` is an accounting statement, not a mood
reading: **the intermediary sector absorbed `imb_t · quote_volume_t` of unwanted short inventory
during that bar**, in the direction it was imposed.

That inventory shock resolves two ways, and they point **opposite**:

- **Immediacy / inventory.** The maker did not want the position and was paid to carry it. The
  compensation is a price concession that subsequently reverts — the return to liquidity provision.
  **Fade it.**
- **Adverse selection.** Some aggressor flow is informed, and informed flow does not revert, it
  continues. Reversion cannot compensate the maker; only spread and withdrawal can. **Follow it.**

Aggressor imbalance is a mixture of the two, so its unconditional sign is not a constant. The
mandate's phrase *"where the pressure resolves"* is exactly the question of which component dominates,
and the whole bet of this lane is that the mixing weight is observable from fields this dataset
contains:

| conditioner | observable | preset sign — **fixed by mechanism, never estimated** |
|---|---|---|
| `none` | — | follow the flow |
| `absorption` | price response per unit flow | high response → informed → follow; low → absorbed → fade |
| `funding` | trailing funding rate | rich → crowded and financed → fade; cheap → fresh → follow |
| `composition` | `log(quote_volume / trade_count)` | large average trade → metaorder → follow; small → crowd → fade |

The 8h bar boundary **is** the funding clock — settlement at 00:00/08:00/16:00 UTC, kline published
on the same grid — which is why funding is the natural *stock* variable for a *flow* signal here
rather than an unrelated carry cost. And because a perpetual has no expiry, that periodic transfer is
the *only* convergence channel, which couples taker pressure and the price of financing it far more
tightly than in any dated contract.

### Who is on the other side

Mechanically, resting limit orders. Economically, the population that runs them:

- **Market makers and HFT desks**, earning spread plus the maker-fee advantage. They warehouse
  uninformed flow and flee informed flow — the counterparty in the absorption regime.
- **Cash-and-carry basis desks**, structurally short the perp against spot to harvest funding, and
  therefore the natural absorber of taker *buy* pressure. This sector is balance-sheet constrained and
  the constraint is common across coins, which is why the state is readable from funding at all.
- **Delta-hedging and structured-product desks**, whose perp leg is a hedge, not a view.
- **Funding-carry funds**, whose entire return is that transfer.

The aggressor side skews the other way: leveraged directional traders — retail and momentum-chasing
programs — for whom the perpetual is the cheapest available leverage and who need to be filled *now*.
Binance taker fees (~5 bps) are strictly worse than maker fees (~2 bps): **anyone appearing in the
`taker_buy_*` field revealed a preference for speed over price.** That revealed preference is the
economic content of the signal. When I fade an imbalance I rent balance sheet to an intermediary
sector short of capacity and am paid an immediacy premium; when I follow one I price information the
maker sector cannot fully requote against inside 8h and am paid an information rent. Both are
payments from the same leveraged taker.

---

## 3. What the book does

Per decision, entirely from past-only rows, no state carried across calls:

1. **Panel.** Align every eligible symbol on the `open_time` **column** — never the positional
   `RangeIndex` — into one 620-bar cube of `close`, `quote_volume`, `taker_buy_quote_volume`,
   `trade_count`. A symbol needs 130 bars before it can be held.
2. **Flow.** Both declared normalisations: `ratio` = `imb_t`, and `trailing` = flow over a **strictly
   lagged** EWMA of quote volume — the scale-matched fork that avoids multiplying the signal by
   inverse turnover. Zero-volume bars set the flow to exactly 0, never interpolated.
3. **Accumulate and standardise.** `L ∈ {9, 21}` bars, trailing z over `W ∈ {90, 360}` bars,
   `min_periods` = full window, winsorised at ±3σ.
4. **Condition.** Multiplicative, no gates or thresholds, all four conditioners at equal weight with
   their preset signs. A conditioner unobservable for a symbol-bar drops out of that average rather
   than voiding the name; if the funding frame cannot be aligned the book trades on the other three
   rather than going flat.
5. **Ensemble.** Equal weight over all `N × L × W` combinations — 8 of them, each carrying the
   4-conditioner average. **There is no selection step anywhere in this file.**
6. **Residualise.** Pooled cross-sectional OLS of the ensemble on the contemporaneous state —
   accumulated standardised return, single-bar standardised return, log quote volume — all
   per-timestamp demeaned, all observable at the same instant as the signal, over a trailing **192-bar**
   window. This is the team falsifier compiled into the book: what trades is only the part of
   aggressor imbalance that is not a restatement of the bar that produced it.
7. **Low-pass.** Exponential filter, **24-bar half-life** over a 96-bar window.
8. **Book.** Cross-sectionally demean, winsorise at ±3σ, scale to gross 1.0, clip `|w| ≤ 0.10` with
   water-filled renormalisation, net ≈ 0 by construction. Every eligible symbol appears explicitly, at
   0.0 if not held, so exits are stated rather than inferred.

### 3.1 The two changes, and why neither is a hill-climb

**Change 1 — filter half-life 12 → 24 bars.** Solved from the cost constant, not from a return.
Write the gates algebraically with gross pinned near 1 and holding period `H` bars:

```
turnover  T ≈ 2190 / H        density  d ≈ μ·H / 2        cost_share = 7.5 bps / d
```

Triple-cost survival needs `d > 3 × 7.5 = 22.5 bps`. `t02` delivered `d = 20.51` — it missed by 10%,
not by an order of magnitude. For an exponentially filtered book the per-bar traded fraction tracks
`1 − 2^{−1/h}` closely: at `h = 12` that predicts `1095 × 0.0561 ≈ 61` against 56.68 observed, so the
model is calibrated to within 8%. Doubling `h` roughly halves turnover.

Density then moves by `d′ = d · k · f(k)` where `k` is the turnover reduction and `f(k)` is how much
gross return survives the longer hold. I bracketed `f` under three assumptions about how fast the
signal's forward information decays (per-bar decay ρ = 1.0 / 0.9 / 0.8), carrying the fact that a
smoother position series also has a *higher* signal-to-noise ratio once renormalised to gross 1.0:

| information decay | `f(2)` | predicted density | predicted turnover |
|---|---|---|---|
| persistent (ρ→1) | ≈ 1.25 | ≈ 45 bps | ≈ 30 |
| moderate (ρ = 0.9) | ≈ 0.76 | ≈ 30 bps | ≈ 30 |
| fast (ρ = 0.8) | ≈ 0.70 | ≈ 27 bps | ≈ 30 |

**Every branch clears 22.5 bps.** That is the point of choosing the lever this way: the decision does
not depend on which branch is true. I checked `h = 30` and `h = 36` in the same algebra and they add
essentially nothing — once turnover drops near 25, the residual churn from weekly membership rotation
stops falling with `h`, so density plateaus around 28–33 bps while gross return keeps declining.
**24 is where the curve flattens**, and it is one clean doubling of the previous value rather than a
tuned decimal.

**Change 2 — residualising window 48 → 192 bars.** Betas re-estimated on 48 bars wander from decision
to decision. That wander moves target weights, is charged at 7.5 bps, and earns nothing: it is
turnover with a *zero* numerator, so it drags density down directly. A 192-bar pooled window (~4,000+
symbol-bars) makes the betas nearly static. This is a better estimator on statistical grounds and a
cheaper one on cost grounds, and it required no return to justify either.

**What I could not do, and it is worth recording.** The obvious cost fix in a real book is a no-trade
band — do not rebalance until the target has moved materially. `target_weights` is handed a
`DecisionContext` and nothing else, and persistent state across decisions is forbidden, so **the book
cannot know its own current position.** Hysteresis is therefore unavailable, and the *only* turnover
control that exists here is making the target itself a smooth function of time. That is exactly what
the low-pass and the long regression window do, and it is why they are the whole of my cost response.

### 3.2 Deviations from the sealed surface — declared, not quietly taken

- **`L ∈ {1, 3}` dropped.** On the §4.5 turnover tripwire, which fired at t01 and was confirmed at
  t02. A book at that speed cannot clear 7.5 bps/turnover at any credible `μ`.
- **`X` collapses to level 2** (time-series z + cross-sectional demean). Time-series-z-only cannot
  satisfy `|net| ≤ 0.25` or the both-sides-used gate as a standalone book. Structural, not a
  preference.
- **The position filter and the regression window are *fixed* choices, not searched knobs.** Neither
  was selected against a Sharpe, IC or drawdown — I have observed one packet on my own book and both
  values were solved from the cost constant and estimator variance. My deflated-Sharpe trial count
  therefore stays at the preregistered **128**, the full declared Cartesian product, regardless of how
  many cells were charged.

Everything else holds: preset signs, symmetric buy/sell treatment, one parameter set for the entire
universe, no per-symbol tuning, no volatility targeting (the organizer owns the risk unit), no
thresholds, no stops, and the conditioner forms exactly as sealed.

Nomination rule §5.4 said: equal-weight every configuration passing F1/F2/F3. The packets report no
IC and no sign-stability split, so those tests are not directly evaluable. The only non-selective
reading of my own commitment is to nominate the **whole** surface at equal weight, which is what this
file does. Subsetting it on observed performance is precisely the pick-the-best-backtest step the
preregistration exists to delete.

---

## 4. Why this book rather than the higher-Sharpe one

`t02` has a net Sharpe of 0.763 and is not admissible. This book should have a lower net Sharpe —
central estimate around 0.6–0.7, possibly 0.5 — and should be admissible. Given that ranking happens
later on evidence I have never seen, and that qualification is a bar on structure and cost, trading
~15% of development Sharpe for a book that survives triple cost is not a close call.

There is a second reason, and it matters more to me than the first. A book that clears `1×` cost and
dies at `3×` is a book whose P&L is a residual between two large numbers. Its out-of-sample behaviour
is governed by whichever of those two numbers moves. At `cost_share ≈ 0.22` instead of `0.37`, the
sealed-block outcome is governed mainly by whether the signal works, which is the thing I actually
have a thesis about. **Lower cost share is not just gate compliance; it is variance reduction on the
question I am being judged on.**

---

## 5. What would falsify this — stated before the packet

**Predicted metrics.** `annualised_turnover` 22–38 (design ≈30) · `gross_edge_bps_per_turnover` 26–42
(design ≈30) · `cost_share_of_positive_gross` 0.18–0.29 · `triple_cost_annualised_return` > 0 ·
`mean_gross_exposure` ≈ 1.0 · `median_effective_breadth` 20–32 · long/short exposure share ≈ 50/50 ·
`active_bar_fraction` ≈ 1.0 · `annualised_return` 4–8% · `net_sharpe` 0.5–1.0, **below t02's 0.763**.

- **Turnover outside 15–50** ⇒ my filter algebra is wrong. That is a structural miss, diagnosable
  from the number itself, and not a reason to touch the signal.
- **Turnover in band but density still below 22.5 bps** ⇒ the flow signal's forward information does
  not survive the longer hold, and since the charge is a flat 7.5 bps with no other lever, **this
  family cannot be traded profitably at 8h decisions under this cost model.** That is the mandate
  falsified on cost rather than on information, and I would say so and retire rather than keep
  slowing the book down until a gate happens to clear.
- **Density in band but net return meaningfully negative** ⇒ a sign error. Every sign here is preset
  by mechanism and sealed. A preferred opposite sign falsifies the thesis; it is not a parameter to
  flip, and I will not resubmit an inverted book.
- **Density implausibly high (> 80 bps)** ⇒ tripwire §4.2 fires. My first hypothesis is lookahead,
  not alpha, and I audit before nominating anything further.
- **Breadth collapsing or one side of the book emptying** ⇒ it is not a portfolio, and a book that is
  not a portfolio is not a marginal candidate.

**The honest statement of the central risk.** The effective holding period of this book is now roughly
three to four weeks, while the evidence closest to my venue, contract and horizon locates
taker-imbalance predictability at **4–12 hours**, and the same work warns that by 8–12h most of what
imbalance knows is already spanned by observable price-volume state. I have moved a microstructure
signal a long way from where microstructure signals are known to live, because the cost model leaves
no alternative. The reasons to think something survives are the accumulation (`L` = 3–7 days makes
the input a slow variable, not a bar-level one), the conditioning, and the residualisation — and,
concretely, that `t02` already held ~13 days and earned 20.5 bps per unit turnover on the orthogonal
component alone. That is one observation on one visible window. If the sealed blocks disagree, the
mechanism is wrong at this horizon and the packet will say so plainly.

---

## 6. Compliance notes

No network, subprocess, filesystem, `eval`/`exec`/`compile`/`__import__`/`getattr`/`setattr`, or RNG.
No state persists across decisions — `TakerFlowPressure` has no mutable attributes and every decision
is a pure function of the `DecisionContext` handed to it. No embedded data: no fitted parameters, no
timestamp-keyed tables, no encoded payloads, no returns, fills, positions or scores. All rolling
statistics are strictly trailing with `min_periods` equal to the full window, so appending future rows
cannot change a past decision. There are no date literals and no symbol literals, so calendar shifts
and symbol pseudonymisation are no-ops. Every signal and every control is a ratio or a trailing
z-score, so the book is invariant to price and volume scale. Weights satisfy `sum(abs(w)) ≤ 1.0`,
`abs(sum(w)) ≤ 0.25` and `abs(w) ≤ 0.10` before submission, and volatility is left entirely to the
organizer's ex-ante risk unit.

*Citation tags referenced in §2 correspond to `scouting/THESIS.md` §6.*
