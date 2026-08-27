# team-15 — discovery candidate: regime-allocated ensemble

**Family:** combination. **Configuration:** the *default* preregistered in
`lane/scouting/THESIS.md` §4, unmoved. No knob has been tuned, because no result has been seen —
this is Trial 2 in the declared protocol (Trial 1 is the organizer seed, which is not mine to write).

---

## 1. The mechanism

A combination has exactly two possible sources of return above its constituents, and only the second
one is my mandate:

1. **Diversification** — imperfectly correlated payoffs raise Sharpe arithmetically. Real, large,
   requires no forecast, and fully available to a fixed equal-weight blend. *Not* what "allocate
   across mechanism states" asks for.
2. **Conditional reordering** — if an observable state variable changes the *rank ordering* of the
   constituents' conditional Sharpes, allocating by state beats any fixed weighting. This requires a
   forecast. This is the mandate.

The honest prior is that (2) usually is not there: DeMiguel–Garlappi–Uppal found no optimizer beating
1/N out of sample; Cederburg et al. found even volatility management wins 53 of 103 portfolios and
loses 50. So the claim has to be about *why it should be there here*.

**Why here.** A perpetual future publishes the price of leverage as a settled cash flow, three times a
day, on exactly my bar clock. Binance sets `F = P + clamp(I − P, ±0.05%)` at 00:00/08:00/16:00 UTC;
when leveraged long demand pushes the perp above the index the clamp pins the adjustment and funding
becomes a near-linear readout of the premium. The conditioning variable is therefore not an estimate
of crowding — it is the realized payment crowded longs made. That removes the specific failure mode
(a slow, noisy, estimated conditioner) that sank the equity factor-timing literature.

And the state is economically loaded, not merely observable. BIS (Schmeling–Schrimpf–Todorov) document
that crypto carry averages >10% p.a., is driven by trend-chasing retail leverage demand against
frictionally limited arbitrage capital, and — the load-bearing fact — **high carry predicts future
price crashes.** The variable that says "carry is rich" is the same variable that says "the hazard
carry is being paid to bear is elevated." Borri et al. put the carry trade at Sharpe 6.45 over
2020–2025, compressing to 4.06 by end-2024 and *turning negative in 2025*. A sleeve whose premium
halves and then changes sign inside five years is a sleeve whose weight should not be fixed.

**One sentence:** carry accrual is a bounded, low-volatility flow that is richest exactly when the
crash hazard it is exposed to is highest, and that hazard is readable in the same 8h funding series
that prices the flow.

## 2. What the code actually does

Stateless; recomputed every decision from past-only rows. `seed` is accepted and unused — there is no
randomness in the module.

**Three sleeves**, each a cross-sectional rank of the eligible universe, demeaned to unit gross:

| Sleeve | Signal | Direction |
|---|---|---|
| carry | 3-bar (24h) mean funding rate | short the highest payers, long the lowest |
| trend | 45-bar (15d) trailing return | long winners |
| reversal | 1-bar (8h) trailing return | short the last bar's winners |

Ranking makes every sleeve invariant to its signal's units and scale; demeaning makes both sides used
by construction rather than by luck, and holds `|net| ≈ 0` well inside the 0.25 cap.

**The state.** Cross-sectional mean smoothed funding → its percentile within a trailing 180-bar (60d)
window → `HIGH` if ≥ 0.67, else `LOW`. A 3-bar dwell filter suppresses chatter (and the turnover it
would cause). Two states, computed as a pure function of history, so exact replay reproduces it.

**The map.** For each sleeve, reconstruct its per-bar P&L over the expanding past (weights lagged one
full bar against forward returns), bucket by the state *in force when the weights were formed*,
take mean/σ per bucket. Weights ∝ positive part of the state-conditional Sharpe, then shrunk halfway
back to equal weight (λ = 0.50). Below 60 observations in the current state, or if any sleeve's
estimate is unusable, the map falls back to equal weight — i.e. it *starts* as the null and only
departs from it on evidence.

**The book.** Blend the sleeves' current rows, normalise gross to 0.99, cap each name at 0.10,
re-normalise. Every symbol comes from `eligible_symbols`; no universe screen of my own.

## 3. Who is on the other side

- **Carry:** leveraged directional retail on USD-M who pay funding to hold levered exposure during
  booms. I warehouse their leverage demand and am paid for bearing the crash risk that BIS shows is
  *conditionally elevated exactly when the payment is largest*.
- **Trend:** those who must rebalance against the move, and late entrants. I supply immediacy.
- **Reversal:** forced sellers in liquidation cascades and impatient takers. I absorb price pressure.

The structural precondition for the mandate is that **carry and reversal fail in opposite states, and
trend fails in a third** — carry dies in the crowded-long unwind, reversal dies in persistent trends,
trend dies in whipsaw. If those failure regimes are not actually disjoint, there is nothing to rotate
into and the mandate is unsupported.

## 4. What would falsify it

Preregistered in THESIS §3 against three benchmarks built from the *identical* sleeves: `EW` (fixed
equal weight, λ=1), `BEST1` (best single sleeve), `CARRY-R` (carry alone, same regime conditioning).

- **F1 — the brief's falsifier, made operational.** `RA` must beat `EW` by ≥ 0.25 annualized Sharpe on
  the full visible window **and** by ≥ 0 in each half independently. The two-halves clause is the part
  that costs me: it kills a win coming from one episode. **If F1 fails I nominate `EW`** and concede
  the regime variable outright.
- **F2 — mechanism.** Falsified if the arg-max sleeve is the same in every state (degenerate map — any
  F1 pass is coincidence), or if the sign of the within-state best-minus-worst spread flips between
  halves in more than one state (the reordering exists but is unstable). **F2 can fail while F1
  passes**; if it does, I report the mandate unsupported and call the F1 pass luck.
- **F3 — contamination (the Asness failure mode).** The state axis is built from funding and the carry
  sleeve is built from funding, so `RA` could be beating `EW` merely by being a nonlinear carry
  signal. Falsified if `RA` does not beat `CARRY-R`.
- **F4 — floor.** Falsified if `RA` does not beat `BEST1`.

**Expected shape of a genuine win:** following Kritzman et al., more in drawdown and left-tail
reduction than in headline Sharpe. A Sharpe-only win reads to me as suspicious, not as confirmation.

## 5. Known weaknesses, recorded now rather than after a result

- **Funding is a weak crowding proxy.** The right variable is open interest × funding. There is no OI
  in this dataset. Funding alone conflates "many crowded longs" with "few longs paying a lot."
- **Turnover is the main structural risk.** The reversal sleeve runs at an 8h horizon and re-ranks
  every bar. If the turnover band or the cost-share / triple-cost gates bite, the preregistered first
  response is `H_rev` 1 → 3, which is an enumerated move in the declared surface, not a new knob.
- **Survivorship in the estimator.** Sleeve P&L is reconstructed over today's eligible universe, since
  past membership is not recoverable without persistent state. This biases the *level* of each
  sleeve's Sharpe; the map only uses the *relative ordering within a state*, which is second-order but
  not zero.
- **Warm-up.** The state needs 180 bars and the map needs 60 per-state observations, so roughly the
  first ~360 bars run as equal weight if `bars` carries no pre-window history. During that stretch the
  candidate *is* the `EW` null.
- **Two states may be too few.** Deliberate: `R_axis = F` alone is the mechanism-grounded axis, and the
  two-axis variants (`F×V`, `F×P`, giving 4 states) are declared search points for later phases, not
  discovery.

## 6. Compliance notes

No network, subprocess, filesystem, `eval`/`exec`/`getattr`, RNG, or cross-decision state. No symbol
literals, no date literals, no fitted parameters or embedded tables. All signals are ranks or returns,
so the book is invariant to price scale and to symbol pseudonymisation, and nothing references an
absolute calendar position. **No volatility targeting** — the organizer owns the ex-ante risk unit, so
the state variable here can only change the book's *composition*, never its *scale*, and every test in
§4 is a test of composition.

Constants that are *not* search knobs, declared so the trial count stays honest: submitted gross 0.99,
net guard 0.24, history cap 1500 bars (a tractability bound on "expanding"), minimum cross-section 8,
minimum per-state observations 60, a ±50%/bar return clip used **only** when scoring sleeves and never
when trading, and a 3-stamp forward-fill limit on missing funding rows.

**Declared trial cap: 24**, inclusive of the seed and the three benchmarks. That is the N to carry into
a deflated Sharpe, and it is honest because the protocol producing it was fixed before data was
mounted.
