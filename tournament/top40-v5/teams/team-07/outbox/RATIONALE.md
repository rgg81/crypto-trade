# team-07 — cointegration convergence. Discovery baseline.

**Trial:** first charged trial, discovery phase. No lane feedback exists yet, so nothing in this
book has been fitted to a result. Every constant is Tier-0 (fixed by the sealed thesis), the
declared Tier-1 **centre**, or a declared Tier-2 **default**.

**Trials evaluated against feedback so far: 0.** That is the number I will report for deflation.

---

## 1. The mechanism

The Binance USD-M cross-section is low-rank: a few hundred contracts whose log prices are driven
by one or two common stochastic trends. A rolling Engle–Granger regression of `log P_y` on
`[1, log P_x]` is therefore not primarily a test of a fundamental equilibrium. It is a
**data-driven estimate of one name's loading on the common trend relative to a peer**. The fitted
β̂ absorbs the shared trend; what is left is the *relative idiosyncratic* component of two names
that move together for structural reasons.

The trade is: when that residual makes a large excursion, take the other side of whatever pushed
one leg away from its peer, and get paid as the excursion decays.

This is what makes it **cross-sectional mispricing** rather than market timing. I am not
forecasting the common trend — the hedge removes it. I am claiming the residual around a
locally-estimated relative price is not a martingale.

**What the premium compensates,** in the order I believe each matters:

1. **Divergence risk — short gamma on relationship stability.** Many small convergent gains
   against occasional large losses when the relationship was structural and broke. This is not an
   engineering defect to design away; it is the payoff shape the premium is attached to. The
   canonical base rate is that only about 62% of pairs trades converge, so roughly two in five
   positions must be closed by something other than convergence. That number, not a P&L target,
   is what the stop apparatus is designed against.
2. **Liquidity provision.** Compensation for standing in front of urgent, price-insensitive flow.
3. **Funding/inventory carry**, which in perps is a real ex-ante-observable cost rather than an
   alpha source — so it is treated as a veto (§4).

## 2. Who is on the other side

Named concretely, in this instrument:

- **Leveraged retail being liquidated.** Forced liquidation is price-insensitive, concentrated in
  one contract, and mechanically overshoots. When a token-specific cascade moves one leg double
  digits without moving its economic peers, whoever takes the other side is compensated.
- **Funding-carry and basis desks**, which size a perp short **by funding rather than by relative
  value**. When funding on one name spikes they short that specific contract, pushing it below its
  peers for a reason unrelated to its relative fundamentals, and unwind when funding normalises.
  Their flow is mean-reverting *by construction*.
- **Narrative and rotation flow** — listings, exchange promotions, sector rotations, unlocks.
- **Market makers laying off inventory** after absorbing one-sided flow in a single contract.

**Boundary, stated plainly:** none of these flows are observable in my dataset. There is no
liquidation feed, no open interest, no order book. They are the economic story for *why a residual
excursion exists and should decay*, not a signal. My inputs are log closes, `quote_volume`,
`trade_count` and `funding_rate`, and I will not spend a trial reconstructing liquidations from
OHLCV.

## 3. Why it should persist in Binance USD-M perps specifically

- **Contract homogeneity makes the pair a clean object.** Every USD-M perp settles in the same
  quote asset, funds on the same 8h clock, and is anchored to spot by the same premium-index
  formula. Two USD-M perps are genuinely comparable instruments — the spread is not contaminated
  by differing settlement currencies, funding intervals or roll schedules. Pairwise cointegration
  on log prices is *more* defensible here than in the equity market where it was developed.
- **Symmetric shortability.** A short costs what a long costs; the locate and recall costs that
  drove the decay of equity pairs trading do not exist here.
- **This is where the flow lands.** Perpetuals dominate crypto derivative volume and open interest,
  so single-name dislocation is observable and tradable in the same contract.

## 4. What the code actually does

Per decision, from the past-only window it is handed:

1. **Panel.** Align the last `W` bars of log close across eligible symbols. Symbols whose grid does
   not match the reference (taken from the longest-history member) are **dropped, not padded** — a
   misaligned pair regression is a spurious-cointegration factory. Drop the bottom 25% of the
   cross-section by trailing median `quote_volume`.
2. **Candidate generation.** Only each symbol's top-5 return-correlated peers, giving O(N·m) tests
   instead of N(N−1)/2. Testing every pair on 300 names is ~45,000 tests per decision; at 5% size
   that manufactures thousands of spurious relationships by construction. Leg roles are assigned by
   trailing liquidity — the deeper name is the regressor — which is a statistical rule, so no
   symbol identity enters anywhere.
3. **Screen.** Engle–Granger step one (`y ~ 1 + x`), then a batched ADF t-stat on the residual
   (one lag, no constant — the residual is mean-zero by construction). Require `t ≤ −3.0`,
   `β > 0`, and β re-estimated on the recent half-window within 50% of the full-window β.
4. **Signal, entirely as window statistics.** Because state may not persist across decisions, every
   stop is expressed as a function of the rolling window. The residual has mean exactly zero
   in-window, so `z = e_last / sd(e)`, and "crossed the mean" is a sign change. Define the
   **current excursion** as the bars since the residual's last sign change, and hold the pair iff:

   | condition | what it implements |
   |---|---|
   | `peak\|z\| ≥ 2.0` | entry threshold was reached during this excursion |
   | `peak\|z\| < 3.5` | **S3 divergence stop** — and it is sticky, because once the *peak* breaches it the pair stays dead until the residual returns to its mean |
   | `\|z_now\| ≥ 0.25` | take-profit: the gap has not yet closed |
   | `age ≤ 2 × H` | **S1 excursion-age stop**, the primary stop |
   | screen still passes | **S2 relationship-invalidation stop**, recomputed every bar |

   Using the excursion *peak* rather than only the current `z` is not a flourish — it is what makes
   the strategy hold through the convergence. A naive stateless band "in when `|z| ≥ 2`" exits the
   moment `z` drops below 2 and therefore captures almost none of the decay that is the entire
   source of return.
5. **Idiosyncratic-event veto.** A bar on either leg whose `|log return|` exceeds 8× that leg's own
   trailing median absolute return within the last `H` bars vetoes the pair. News is a *permanent*
   relationship break, not a temporary excursion. This is the observable shadow of the unlocks,
   delistings and cascades the dataset does not carry.
6. **Funding veto.** Compare the carry paid over one half-life against the convergence gain
   expected over the same span (half the gap closes in one half-life); veto if carry would eat more
   than half of it. Direction-dependent, so it vetoes the half of the opportunity set where the
   *required* direction bleeds, not half of all pairs.
7. **Book.** Top 20 surviving pairs ranked by ADF t-stat — the mandate's own statistic, a measure of
   formation quality, deliberately **not** a return forecast. Equal gross per pair, legs weighted
   `(1, −β)` normalised to unit pair gross, each symbol capped at 2 appearances. Gross ≈ 0.99,
   per-symbol ≤ 0.099, net small by construction since `β > 0` forces every pair to be one long and
   one short.

## 5. Why the stop is shaped this way

The mandate names the stop as the hard part, and the reason is a genuine contradiction:
**a distance stop fires precisely when the trade is most attractive under the model.** If the OU is
true, a spread at 4σ is a *better* entry than one at 2σ. A pure distance stop is only correct if
distance is evidence the **relationship broke**, not evidence the opportunity grew.

So the primary stop is not a loss stop. It is **S1, excursion age**: under the preregistered
half-life an excursion should decay by 2⁻ᵏ in k half-lives, so a residual that has stayed on one
side of its in-window mean for more than 2H bars has falsified the preregistered model *for that
pair*. That is scale-free, needs no P&L, and is the stop most directly aligned with the lane's
falsifier. The divergence stop S3 exists because ~38% of pairs never converge and something has to
close them — and "off" is inside its declared range precisely because it is a live possibility that
it destroys value.

## 6. Why the half-life is preregistered rather than fitted

The ML/LS estimator of the OU mean-reversion parameter is biased, and the bias is of order T⁻¹ in
the data **span**, not n⁻¹ in the number of observations. Sampling at 8h instead of daily triples
my observation count and buys nothing against it, and the standard bias correction degrades exactly
in the near-unit-root case that is empirically realistic. Fitting κ̂ per pair on a 60-day span would
mean **selecting pairs on a biased estimate of the very quantity that determines profitability**. A
single preregistered H, used identically for every pair — for the z-normalisation, the excursion
clock and the event window — has no such selection channel. The window is then tied to it (`W ≥ 6H`)
rather than searched independently, which collapses a two-dimensional search into a
mostly one-dimensional one.

H and W are declared in **days** (5 and 60) and converted to bars from the observed bar spacing,
because a half-life is a duration. A duration is not an absolute date, so calendar-shift
equivariance is unaffected.

## 7. What would falsify this

Preregistered, and stated as **mechanism tests rather than performance tests**. A losing stretch is
*consistent* with this premium being present and correctly priced — convergence trading loses money
with positive probability even when the opportunity is fundamentally riskless — so a P&L falsifier
would be testing the wrong thing, and would additionally be contaminated by the engine's ex-ante
volatility unit, cost model and exposure caps, none of which I control.

- **F1 — out-of-window convergence rate.** Freeze α̂, β̂ and the residual moments at *t*; evaluate
  the frozen spread forward with no re-estimation. Among frozen spreads at `|z| ≥ 2.0`, record the
  fraction reaching `|z| ≤ 0.25` before touching `|z| = 3.5` or exhausting 2H bars. A driftless
  random walk from z = 2.0 with barriers at 0 and 3.5 converges 1.5/3.5 = **42.9%** of the time;
  the equity literature says ~62%. **Below 55% and F1 fails**: the residual is a random walk I
  selected on in-window noise, and there is nothing to converge to. **I retire rather than search
  for a window or threshold that lifts it.**
- **F3 — does cointegration add anything over distance?** Build a matched control of pairs that
  **failed** the ADF screen but had comparable `|z|` (within ±0.25). **If the screened set does not
  beat the control by ≥5 percentage points on F1's measure, F3 fails** — the screen adds nothing
  over "the spread is wide", and the mandate's specific expression is falsified **even if the book
  makes money**. I would then report that I was running a distance strategy wearing a cointegration
  hat, and would not nominate on the strength of it.
- **F2 — β stability (diagnostic, not an escape hatch).** Median `|β_{t+W} − β_t| / |β_t|` over
  non-overlapping windows. Above 0.50 the "equilibrium" is being redefined faster than the spread
  can reach it. A passing F2 does not rescue a failing F1.

**Signature that would tell me the falsifier has bitten, in feedback terms:** gross edge per unit
turnover near zero with high participation and healthy breadth. That is the book trading a great
deal and converging on nothing — F1 failing with the gates passing.

## 8. Honest adverse evidence, recorded before the result

- Pair-spread mean reversion has been found on Binance at **5-minute and 1-hour and reported absent
  at daily**. My floor is 8h — I am sampling in the dead zone between where the effect was found
  and where it was not. **This is the single most likely killer, above the stop.**
- Crypto short-horizon reversal concentrates in **illiquid** names; the most liquid coins show daily
  *momentum*. Binance USD-M perps are by construction the most liquid crypto instruments, and my
  liquidity floor pushes me further toward the region where the premium is smallest. My defence is
  that a β-hedged spread is not a raw return — the hedge removes the trend that carries the
  momentum. **That defence is a claim, not a fact, and F1 is exactly its test.**
- Cointegration's superiority over the distance method is established in equities and **not** in
  crypto perps. F3 tests it in my universe and I expect to be uncomfortable with the answer.
- The base rate is modest and decaying (~6.4% annualised post-2010) and the trade is crowded
  (roughly a third of digital-asset hedge funds run market-neutral). **A large measured effect is a
  red flag, not a success.**

**Acknowledged and unresolved by design:** a 5-day half-life on an 8h grid implies real turnover,
and at ~20bp per pair round-trip — ~60bp under the triple-cost gate — that may not survive. The
resolution is *not* to tune H until turnover lands inside the gate, because that would let the cost
gate rather than the mechanism choose my half-life. I will report the cost outcome as a finding.

## 9. Compliance notes

- **No volatility targeting.** Nothing conditions on realised or forecast portfolio volatility; the
  ex-ante risk unit is the organizer's.
- **No persistent state.** The strategy object has no mutable attributes. Every decision is a pure
  function of its window, so exact-replay determinism holds by construction. No RNG; `seed` is
  unused.
- **No look-ahead.** Only rows the context supplies are read, all at or before the boundary.
- **Scale equivariance** is structural: the regression carries an intercept, so `P → cP` shifts
  `log P` by `log c`, which α absorbs, leaving β and the residual untouched.
- **Pseudonymisation**: no symbol identity anywhere. Leg roles come from trailing liquidity, pair
  selection from correlation and ADF.
- **Calendar shift**: no absolute dates, no time-of-day conditioning. This costs me something real —
  the 00:00/08:00/16:00 UTC funding clock is a genuine candidate effect and I am declining to use it
  because it is calendar-linked.
- **No forbidden builtins.** No `eval`/`exec`/`compile`/`__import__`/`getattr`/`setattr`, no
  network, subprocess or filesystem access, no embedded data — no fitted parameters, tables,
  returns, fills, positions or scores. `DecisionContext` fields are read as direct attributes,
  since `getattr` is on the prohibited list and the protocol dataclass guarantees them anyway.
- **Defensive reads.** Every column access (`close`, `quote_volume`, `symbol`, `funding_rate`) is
  guarded, and the funding frame is read from its tail rather than filtered on a timestamp so no
  timezone assumption can silently empty it. The kit warns that reading a field that does not exist
  produces a flat book rather than an error; the funding rate column is `funding_rate`, not
  `last_funding_rate`.

## 10. What I want from the first feedback packet

In priority order, because these decide the next move rather than the next parameter:

1. **Effective breadth and pair count.** If the ADF screen at τ = −3.0 admits fewer than 20 pairs at
   a majority of decisions, that opens Tier-2 knob 7 (τ) — a *declared* contingency, not a new
   search.
2. **Gross edge per unit turnover, and cost share.** This is where the 8h-is-too-slow risk shows up
   first, and it distinguishes "no edge" from "edge eaten by costs".
3. **Survival at 3× cost.** A book that only survives at 1× is not a book.
4. **Both-sides-used on exposure, and net exposure.** Should pass by construction (`β > 0`); if it
   does not, my sizing arithmetic is wrong and that is a bug, not a finding.
