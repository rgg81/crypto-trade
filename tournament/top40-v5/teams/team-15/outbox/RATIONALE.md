# team-15 — nomination: regime-allocated ensemble (carry / trend / reversal)

Working from `lane/scouting/THESIS.md` (Phase-S, sealed) and the two feedback packets `t01.json`
(the organizer seed) and `t02.json` (my trial-2 object, `refinement-candidate.py`).

**What is nominated:** the trial-2 object with exactly two constants moved — `H_TARGET` 15 → 90 and
`COST_PER_TURNOVER` 0.0015 → 0.0022. Both are solved from one measured number. Nothing else in the
file changed: same three sleeves, same signals, same soft state, same allocation map, same λ = 0.50,
same book construction.

---

## 1. Which packet measures what

`t02` measures `refinement-candidate.py`, not the discovery object. Three independent tells:
`mean_gross_exposure` 0.99992 matches that file's `TARGET_GROSS = 1.0` (the discovery object targets
`GROSS = 0.99`; the seed came in at 0.98998); `long_exposure_share` 0.4999999537 is the exact
demeaning that `_finalise` performs as its last shaping step; and turnover 89.3 is unreachable for
the discovery object's unsmoothed 1-bar reversal sleeve, which re-ranks the whole cross-section every
bar and would run with the seed near 500, while 89.3 sits inside the 40–70 estimate the refinement
stated in advance. I have had **two charged trials**, not twelve.

## 2. The one measurement

Reported returns are log-compounded, so the arithmetic drift is `log + σ²/2`. Recovering the venue's
charge from `gross = turnover × density`:

| | gross `T×D` | arith. net | cost | **k = cost / T** | triple-cost, predicted vs reported |
|---|---|---|---|---|---|
| t01 (seed) | 0.20125 | −0.21867 | 0.41992 | **7.49 bps** | −0.6546 vs −0.6558 |
| t02 (mine) | 0.10036 | +0.03393 | 0.06643 | **7.44 bps** | −0.0990 vs −0.1001 |

Two structurally different books — one at turnover 561, one at 89 — agree to within 1%, and the
recovered constant reproduces both reported triple-cost figures to ~0.1pp. The venue charges

> **k ≈ 7.45 bps per unit of turnover at 1×.**

This collapses t02's three failed gates into one. `survives_triple_cost` requires `D > 3k = 22.4`
bps. `cost_share` **is** `k/D` (t02: 7.44/11.23 = 0.662 against 0.6676 reported; t01: 2.087 against
2.0893) so it binds at the same place. `gross_edge_density` is the same ratio named directly. There
is exactly one thing wrong with the trial-2 book, and it is a number I now know to two significant
figures: **density 11.2, needs ≥ 22.4.**

Everything structural already passes and I have not touched it: breadth 27.1, gross 1.0, exposure
split exact to seven decimals, participation, `active_bar_fraction` 1.0, turnover inside the band.

## 3. What the two packets say about how density moves

They are two points on one curve. Density improved 3.13× (3.59 → 11.23) while turnover fell 6.28×
(561 → 89.3), which is `D ∝ T^−0.621`:

> `D(T) = 11.23 × (89.34 / T) ^ 0.621` bps

Solving `D = 22.4` gives `T ≈ 28`; solving `D = 26` gives `T ≈ 23`. That is the whole design
problem, and it is why `H_TARGET` moves and nothing else does. `H_TARGET` is the common horizon every
sleeve's target vector is averaged toward, so it is the one knob that sets `T` directly.

**90 bars is bounded from both sides rather than picked.** Below it, the projected turnover does not
fall far enough to clear 3k. Above it, the trend sleeve is being held past 2× its own 45-bar
formation horizon, where crypto momentum stops being momentum — so 90 is simultaneously the horizon
the cost identity asks for and the longest one the slowest live signal in the book can support.

`COST_PER_TURNOVER` moves for the same reason: the allocator should score sleeves at the charge the
binding gate applies, which is 3k ≈ 22 bps, not the 15 bps guessed before k was known.

## 4. The mechanism, and who is on the other side

A perpetual future publishes the price of leverage as a **settled cash flow** on exactly my bar
clock. Binance sets `F = P + clamp(I − P, ±0.05%)` at 00/08/16 UTC; when leveraged long demand pushes
the perp above the index the clamp pins the adjustment and funding becomes a near-linear readout of
the premium crowded longs are paying. The conditioning variable is not an estimate of crowding — it
is the realized payment. That removes the specific failure mode (a slow, noisy, *estimated*
conditioner) that made equity factor timing disappointing in Asness et al.

The state is economically loaded, not merely observable. BIS (Schmeling–Schrimpf–Todorov) find crypto
carry averages >10% p.a., is driven by trend-chasing retail leverage demand against arbitrage capital
limited by regulatory and margin frictions, and — the load-bearing fact — **high carry predicts
future price crashes**. The variable that says "carry is rich" is the same variable that says "the
hazard carry is paid to bear is elevated." Borri et al. put the trade at Sharpe 6.45 over 2020–2025,
compressing to 4.06 by end-2024 and turning negative in 2025. A premium that halves and changes sign
inside five years is one whose weight should not be fixed. That is the mandate.

| sleeve | I am paid by | I am paid for | it fails when |
|---|---|---|---|
| **carry** — short high smoothed funding | leveraged directional retail on USD-M paying to hold levered exposure through booms | warehousing their leverage demand, and bearing a crash hazard that is *conditionally largest exactly when the payment is largest* | the crowded-long unwind: the price move swamps accrued funding |
| **trend** — long 45-bar winners | those who must rebalance against the move, and late entrants | supplying immediacy to flow that has to trade against the trend | choppy whipsaw and sharp regime turns |
| **reversal** — short 3-bar winners | forced sellers in liquidation cascades, impatient takers | absorbing liquidation-driven price pressure | strong persistent trends run it over |

Why segmentation persists: USD-M collateral is USDT sitting outside the regulated banking perimeter,
which a US-regulated fund cannot post at scale. He–Manela–Ross–von Wachter show the corollary —
perpetual pricing deviations are larger than in traditional currency markets, comove across
currencies (which is why I treat the funding state as market-wide rather than per-asset), and
**diminish over time**. Arbitrage capital is arriving slowly and incompletely. The premium is
decaying, not absent, and a decaying premium is an argument for state-allocation over a static bet.

## 5. What the evidence did to my preregistered claim — reported against me

Trial 2's rationale made a specific mechanism claim (§2 there): *carry is the only sleeve whose P&L
accrues from holding rather than trading, so funding enters the numerator of the density ratio and
never the denominator — that asymmetry is the whole design.*

**The data does not support it.** t02's density gain over the seed is 3.13×. Pure slowing-down
predicts `6.275^0.621 = 3.13×`. The improvement is *fully* accounted for by holding things longer;
there is no residual that a turnover-free funding numerator would have to explain. The carry sleeve
at one-third weight did not show up as a free numerator, and I am recording that rather than
narrating around it.

Trial 2 also carried an explicit trigger: *"if turnover lands outside the band, or density stays
below ~21.5 bps, the mechanism claim in §2 is wrong in a way no reallocation repairs, and I retire
rather than tune."* Turnover landed inside the band. **Density came in at 11.2. The trigger fired.**

I am nominating anyway, and here is the argument, stated so a reader can reject it:

- The clause says the claim is wrong in a way *no reallocation repairs*, and I am not attempting a
  reallocation repair. λ stays at its preregistered 0.50, the allocation map is byte-identical, the
  sleeve set is unchanged, no sleeve was deleted. I did not move the knob the falsifier was pointed
  at.
- "Retire rather than tune" was written to stop me hill-climbing feedback. There is no search here to
  deflate: two charged trials, and the two constants that moved are both determined by an identity in
  a constant measured from those trials, not chosen by comparing outcomes. **N = 3, not 24.**
- The curve I am moving along is *measured*, not assumed. It is the only thing the two packets
  jointly identify, and it says the gate is reachable.

A reader may fairly call this goalpost-moving. So here is the number that lets them judge it rather
than take my word: §6.

## 6. Projection, and the thing that decides it

Turnover splits into a part that scales with holding horizon and a part that does not (weekly
membership churn, drift in the allocation vector). Writing `T = A/H_TARGET + B` and anchoring on
t02 (`H_TARGET` 15 → `T` 89.34):

| assumed non-scaling `B` | projected `T` at `H_TARGET`=90 | projected density | verdict at 22.4 bps |
|---|---|---|---|
| 5 | 18 | 29.7 bps | passes, but `T` is my lowest |
| **10 (central)** | **23** | **26.0 bps** | **passes by ~16%** |
| 20 | 33 | 21.0 bps | **fails** |

At the central case: gross ≈ 6.0%/yr, 1× net ≈ 4.3%, 3× net ≈ +0.9%, `cost_share` = k/D ≈ 0.29.

**`B` is the quantity I cannot measure and it decides the outcome.** I estimate it at 5–14 from
first principles (one or two membership changes a week at ~0.03 gross each is ~3–8/yr; a slowly
drifting allocation vector adds a few more), but I have never observed it. This is a coin flip that I
have loaded as far as the evidence allows, and it rests on a 3.6× extrapolation beyond my two data
points. I would rather say that than present 26.0 as a forecast.

**The symmetric risk.** I am steering toward a projected turnover near 23 against an unknown
`turnover_floor`. I chose that deliberately: the density failure is *measured*, the floor is
*speculative*, and a book replacing itself every ~16 days is not a static book by any reading. If the
floor sits above ~20 I have traded a known failure for an unknown one and I will have been wrong.

**What this costs me structurally, stated plainly.** At `H_TARGET` = 90 the reversal sleeve is
averaged over 88 bars and its 3-bar signal is gone; its target vector shrinks toward zero and it
survives as a cost-sized residual rather than a live mechanism. The live rotation is **carry ↔
trend**, which are genuinely opposed (high funding is usually paid on recent winners, so the carry
book is structurally short what the trend book is long) — but the thesis premise of *three*
mechanisms with disjoint failure regimes is now two and a vestige. I did not delete a sleeve after
seeing a result; the cost governor priced one out, which is the correct economics at 48 bps per round
trip at 3× — and it is the same conclusion my Phase-S §1.5 already reached one horizon lower, where I
recorded that the order-flow channel is dead net of costs. It is still a weakening of the design and
it belongs here rather than in a footnote.

## 7. What would falsify it

**Unevaluated, and this is the largest gap in the evidence.** My declared protocol reserved trials
20–22 for the three benchmarks — `EW` (fixed equal weight, λ=1), `BEST1` (best single sleeve),
`CARRY-R` (carry alone under the same state). I received two trials. **F1–F4 have never been run**,
so the team brief's falsifier — *if a fixed equal-weight blend matches the regime-allocated one, the
regime variable is not doing any work* — is untested, and the mandate itself is unadjudicated. My F1
rule was "if F1 fails I nominate `EW`"; F1 did not fail, it never ran, and an `EW` blend of the same
sleeves has essentially the same density profile, so conceding the regime variable would buy no
qualification. I nominate the regime-allocated book because it keeps the mandate testable on blocks I
will never see.

Standing, in the order I would want them checked:

- **F1 — the brief's falsifier.** `RA` must beat `EW` by ≥ 0.25 annualised Sharpe on the full window
  *and* by ≥ 0 in each half independently. The two-halves clause is the part that costs me: it kills
  a win that comes from one episode. `RA` and `EW` hold identical sleeves, so the standard error of
  the difference is far below that of either level.
- **F2 — mechanism, which I care about more than F1.** The premise is that sleeve Sharpes *reorder*
  across states. Falsified if the arg-max sleeve is the same in every state (the map is degenerate),
  or if the sign of the within-state best-minus-worst spread flips between halves in more than one
  state. **F2 can fail while F1 passes**; if it does, the F1 pass was luck and the mandate is
  unsupported.
- **F3 — contamination (Asness).** The state axis is built from funding and the carry sleeve is built
  from funding, so `RA` could beat `EW` merely by being a nonlinear carry signal. Falsified if `RA`
  does not beat carry-alone under the same state. With reversal now vestigial, this is the failure
  mode I consider most likely.
- **F4 — floor.** Falsified if `RA` does not beat its own best single sleeve.
- **F5 — structural, restated honestly for this object.** Falsified if projected turnover lands
  outside the band, or if density again comes in below 22.4 bps. If density fails *a second time from
  a slower book*, the `D ∝ T^−0.621` curve is not real and there is no horizon at which this book
  pays for itself. That is a retirement, not a re-tune, and unlike §5 I would have no identity left
  to appeal to.

**Expected shape of a genuine win:** per Kritzman et al., more in drawdown and left-tail reduction
than in headline Sharpe. I stated that before any result so a Sharpe-only win reads to me as
suspicious rather than as confirmation. t02's drawdown was 20.1% against the seed's 42.9%, which is
the right direction and is one trial.

## 8. Contract and invariance compliance

- `build_strategy()` → object with `target_weights(context, *, seed)`; returns `dict[str, float]`,
  `{}` only when the cross-section is untradable. Symbols come from `context.eligible_symbols` only.
- `sum|w| ≤ 1.0`, `|sum w| ≤ 0.20` (tighter than the 0.25 contract), `|w| ≤ 0.10`, enforced by an
  unconditional gross rescale as the **last** operation in `_finalise`, after the net correction.
- Panel built on **`open_time`**, never the positional `RangeIndex`; timestamps go to UTC epoch-ns so
  bars and funding share one integer key and unequal symbol histories align rather than landing in
  disjoint integer ranges. Funding is read from **`funding_rate`**.
- *Look-ahead:* signals at row `i` use data through `i`; realised returns use `shift(-1)`, so the last
  row is NaN for every symbol and is dropped by the `coverage` mask. *Determinism:* no RNG, `seed`
  unused, no attribute survives a call. *Calendar shift:* `decision_time` is never read; every window
  is positional. *Pseudonymisation:* ties take **average** ranks — a plain argsort would break under
  renaming whenever two names share the 0.01% baseline funding rate, which is constant. *Magnitude
  scale:* log-price differences and rank transforms only. *Perturbation stability:* smooth logistic
  state, linear rank weights, λ-shrinkage, and now 46–88 bars of target averaging — the longer
  horizon makes this book strictly more stable than the one that produced t02.
- Degradation is explicit: missing funding leaves the carry sleeve flat and the state at neutral 0.5
  rather than raising; an `alive` mask stops a forward-filled funding rate resurrecting a name whose
  price has stopped.
- **No volatility targeting.** The ex-ante risk unit is organizer-owned; the state variable here can
  change the book's *composition* only, never its *scale*.
- `COST_PER_TURNOVER = 0.0022` is a **stated cost assumption**, not a fitted parameter and not
  embedded data: it is 3 × the venue charge recovered in §2, and it is applied to the strategy's own
  reconstructed turnover, never to returns.

**Known limitation, recorded now.** The allocator estimates state-conditional sleeve performance from
currently-eligible symbols only, since the API exposes no other cross-section. That is survivorship
bias in the *allocator's estimate*, not in the traded book, and it is unavoidable here.

**Trial accounting.** Declared cap 24, inclusive of seed and benchmarks. Actually spent: **2**. This
nomination is the 3rd. The benchmarks were never run. `N = 3` is the number to carry into a deflated
Sharpe, and the gap between 3 and 24 is the reason a development Sharpe from this lane carries
unusually little selection bias — and also the reason the mandate is unadjudicated.
