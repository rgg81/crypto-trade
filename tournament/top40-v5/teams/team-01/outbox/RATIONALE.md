# RATIONALE — team-01 discovery candidate

**Book:** cross-sectional funding-carry harvest, Binance USDⓈ-M perpetuals, 8h decisions.
**Protocol position:** THESIS §4.3 **Stage A** — the declared control arm, `λ = 0`.
**Trials consumed by this candidate:** 1.

---

## 1. Why this book and not the fancier one

My mandate is *funding carry with crowding protection*, and my preregistered Stage 0 default
carries a crowding overlay at `λ = 0.50`. I am submitting **Stage A instead — the matched control
with the overlay off** — on purpose, and I want the reason on the record before any number comes
back.

Falsifier **F2** in my thesis is not "does the book make money." It is: *does the crowding overlay
beat the matched `λ = 0` book at equal ex-ante risk, on both left-tail reduction and drawdown?*
That comparison is undefined until the `λ = 0` book has been measured. Running the overlay first
would give me one number I could not decompose: I would not know whether it came from the carry
sort or from the crowding discount, and I would have burned the trial that tells me.

There is a second reason, specific to this phase. The overlay's most important component (C2,
taker-flow decay) is a genuine inference about positioning from aggressor share, and I said in the
thesis that it is the piece I most expect to fail at 8h resolution. Putting an untested inference
*and* an untested carry sort into the same first trial makes both undiagnosable. A baseline I can
read is worth more than a book I cannot take apart.

Everything in §4.1 that is **fixed by declaration** is present here. Only the searched knobs sit at
their Stage A coordinates.

---

## 2. The mechanism

A perpetual future has no maturity, so nothing forces convergence to the index. In place of
convergence Binance runs a feedback rule: each settlement, the side that is long pays the side that
is short in proportion to the perp's premium over the index. The exchange takes none of it. Funding
is therefore **not a fee and not a spread — it is a transfer between two populations of traders**,
and its level is the clearing price of an imbalance in the demand for leverage.

Per unit of long notional over an 8h bar:

```
r_total = r_price − f_8h
```

Holding notional of the sign opposite to funding collects `f` instead of paying it. A book long the
most-negative-funding names and short the most-positive collects, by construction, a strictly
positive carry component equal to `mean(f | short leg) − mean(f | long leg)`. **The carry leg is
arithmetic. The entire question is whether the price leg gives it back.** That question is what the
trial is for.

Why it should persist here specifically: for the long tail of alt perps there is no deep, cheaply
borrowable spot on the same venue with the same collateral, so the cash-and-carry that competes the
premium away on BTC/ETH is unavailable. The only way to take the receiving side is to bear
directional risk. A premium that can only be earned by bearing risk is a risk premium, and risk
premia do not get arbitraged to zero. This book lives in exactly the part of the cross-section
where the arbitrage does not close.

---

## 3. Who is on the other side

This is a perp-only cross-sectional book, so the counterparty is explicit rather than inferred.

| Leg | Who I face | Why they are there | How they leave |
|---|---|---|---|
| **Short** (high positive funding) | Levered directional longs — retail and trend-followers buying convex upside without spot custody or fiat rails | Funding is the rent on leverage; in a boom the expected move dwarfs 30% annualised carry | Forcibly, in a liquidation cascade |
| **Long** (deeply negative funding) | Panicked or squeezed levered shorts, mid-cascade | Forced, not chosen — position size set by margin, not by view | Forcibly, via liquidation or ADL |

I am not facing an arbitrageur on either leg. I am facing someone whose size is determined by their
margin.

Crucially, **the side I am joining is itself crowded**. Delta-neutral basis desks and synthetic-dollar
vehicles have institutionalised the funding-receiving trade at multi-billion-dollar scale since 2024,
and that capital is reflexive — it rotates out when funding compresses. That is the crowding my
mandate names, and it is why the premium is compensation rather than a free lunch: I am being paid to
be the warehouse of last resort, and the raid on the warehouse arrives precisely when the carry is
largest.

The failure modes are asymmetric and I want both stated before I see results:

- **Short leg — the slow failure.** Funding pins at the cap for weeks while price compounds against
  me. I collect at most ~1% per 8h and lose multiples of it on price.
- **Long leg — the fast failure.** Deeply negative funding *occurs inside* a liquidation event. I am
  paid to be long the exact assets being force-sold. This is where the fat left tail of the whole
  book lives, and it is what the (absent) crowding overlay is eventually meant to address.

---

## 4. What is actually implemented

| Step | Choice | Why |
|---|---|---|
| Funding measurement | Sum every settlement in the trailing 3 bars (24h), divide by 3 | Binance settles 8h / 4h / hourly by symbol and regime. **Summing settlements is schedule-agnostic**; a per-settlement mean would rank fast-settling, cap-pinned names systematically too low — and those are exactly the crowded names the thesis is about |
| Universe | Top 75 by trailing 90-bar median quote volume; ≥64 bars of history | Funding at listing is wild and untradeable. Also keeps the book inside the 0.1%-of-24h-volume participation limit |
| Tail trim | Drop 2% of each raw-funding tail | Cap-pinned prints are not tradeable carry |
| Normalisation | Carry-to-risk: `−funding ÷ 63-bar realised vol`, then cross-sectional rank | The funding cap scales with the maintenance margin ratio, which is larger for riskier alts. **A raw-funding sort mechanically overweights junk** — this corrects an exchange-mechanical bias, not merely a statistical one |
| Beta handling | Rank signal residualised on beta vs the equal-weight universe (90 bars) | When funding is one-signed across the whole cross-section — precisely the pre-cascade state — a naive "cross-sectional" sort is a disguised directional bet |
| Construction | Top/bottom 20% (≈15 a side), linear rank weights within leg, gross 1.0 | Exactly dollar-neutral and exactly symmetric by construction; ~30 names of breadth |
| Gross | Constant | THESIS §1.5: gross timing is mechanically undone by the organizer's common risk unit. De-risking by size is not available to me, so crowding protection must be **composition**, never shrinkage |
| Vol targeting | None | Mandate |

**Contract compliance is structural, not clipped.** Each leg's magnitudes sum to 0.5, so
`sum|w| = 1.0` and `sum(w) = 0` exactly. Max weight is `1/(n_leg+1) ≈ 0.0625` at full universe,
under the 0.10 cap; the explicit clip only ever binds on a degenerate small universe, and it is
symmetric so net stays zero. Symbols come only from `context.eligible_symbols`.

**Failure mode is flat, never wrong.** Every degenerate path returns `{}` rather than a partial or
garbage book: missing funding, thin universe, zero vol, unusable prices. Beta estimation failure
falls back to `β = 1.0` for that name, which makes the residualisation a no-op rather than a source
of scrambled signal. Bars are aligned **by position from the most recent row**, not by index label,
because every eligible symbol has an executable open at the decision and so shares the same last
bar — this holds regardless of the index dtype, which the protocol does not specify.

**Invariance checks.** No absolute dates (all windows are relative to `decision_time`). No symbol
literals. No price levels used except as ratios, log-differences, or ranks — quote volume enters
only through a rank. No RNG, no `getattr`, no persistent state; `seed` is accepted and deliberately
unused, so replay is exact.

---

## 5. What would falsify this

Stated before results, per THESIS §3.

**F1 — the mandate falsifier.** If the top-minus-bottom spread on this signal has an information
ratio **below 0.3** on the visible development span **and** the sort is non-monotone (Spearman
rank correlation between quantile and mean total return **≤ 0.5**), then funding does not produce a
usable spread in this universe and I nominate the unmodified organizer seed. The cost is explicit
and accepted: honouring F1 scores zero movement from the seed rather than fitting something else to
the same data.

**F3 — direction.** I committed to the harvest direction. If the development spread is reliably
**negative** — funding momentum dominating funding carry — **I report a direction falsification and
do not flip the book.** Reversing the sign after seeing the result would convert a preregistered
risk premium into an unregistered momentum strategy, which is a different economic family and not my
mandate.

**Prior I am recording so the falsifier means something.** Information ratio ≈ **0.4–0.9** at the
common risk unit; returns materially left-skewed; and the majority of maximum drawdown concentrated
in **five or fewer identifiable multi-day episodes** rather than diffused across the sample. If the
drawdown is diffuse rather than episodic, my account of *what the premium is compensation for* is
wrong even if the Sharpe is fine — and that matters more to me than the Sharpe, because the whole
crowding programme is built on the episodic story.

**F2 is not testable from this trial and is not claimed.** It becomes testable once this control has
a number.

---

## 6. Named risks in this specific implementation

Listed so that feedback can adjudicate them rather than my rereading the code.

1. **Funding-rate units.** I read `funding_rate` as Binance's per-settlement rate and therefore sum
   settlements. If the organizer has already normalised the column to an 8h equivalent, summing
   over-weights fast-settling symbols by their settlement count. The distortion is monotone in
   settlement frequency and would show up as the book systematically favouring the same handful of
   fast-settling names. Diagnosable from turnover concentration and leg composition.
2. **Turnover.** Rank selection of the top/bottom 20% rebalanced every 8h can churn. `L` is a
   declared knob (1, 3, 9, 21) and is the correct lever if turnover breaches the band or cost share
   is too high. I will not reach for undeclared smoothing or hysteresis.
3. **Beta neutralisation is signal-level, not book-level.** THESIS §4.1 declares beta-neutrality;
   I implemented it by residualising the *signal* rather than projecting the *weights*. This is a
   deliberate deviation: projecting the weights sprays small non-zero positions across every
   universe name, which dusts up a 30-name book into a 75-name one and manufactures turnover and
   participation churn for a second-order hedge. The consequence is that realised book beta is
   reduced but not exactly zero. If feedback shows residual market exposure, the book-level
   correction is the fix.
4. **Burn-in is stricter than declared.** §4.1 declares a 30-bar listing burn-in; the 63-bar
   realised-vol window forces ≥64 bars. This narrows the early-sample universe. It is a
   tightening, not a widening, of the declared surface.
5. **Cost survival.** The carry leg is arithmetic but small per bar. Survival at 3× cost is the
   gate I consider most at risk, and it is a genuine property of the mechanism rather than a
   parameter I intend to tune around.
