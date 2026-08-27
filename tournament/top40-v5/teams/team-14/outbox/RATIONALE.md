# team-14 — discovery candidate rationale

**Mandate:** time net exposure from cross-sectional breadth and dispersion.
**What this is:** the *unmodified declared baseline* of `lane/scouting/THESIS.md` §4.4, implemented
as written. No knob has been searched, no feedback packet exists yet, and no result has been seen.
This is trial 0 of my declared surface — the thing F2 is supposed to be evaluated *at*, before any
search, not the output of one.

---

## 1. The mechanism

A few hundred USD-M perpetuals are not a few hundred independent assets. They are close to one
common factor plus narrative noise. That is normally a complaint; here it is the premise. If a
single latent state variable drives the venue — call it risk-bearing capacity, or the arrival and
withdrawal of leveraged speculative capital — then **each symbol is a noisy measurement of it**, and
a bounded per-symbol indicator averaged across the cross-section is a better-conditioned estimator
of that state than the index return, because it is not dominated by the one or two large caps that
carry a cap- or volume-weighted index.

An index return of +2% tells you the factor moved. Breadth tells you **how many measurements agree**.
Those are different statistics, and only the second distinguishes a move funded by broad capital
arrival from a move funded by concentrated flow into a handful of names.

The book is built from **one primitive, read at two moments**:

| | quantity | reads |
|---|---|---|
| primitive | `s_i = (close_i / SMA_21(close_i) - 1) / sigma_i` | vol-normalised distance from own trend |
| 1st moment | `B = mean_i sign(s_i)` | breadth — how many names agree |
| 2nd moment | `D = xs-std(9-bar returns) / (mean_i sigma_i * sqrt(9))` | dispersion — a correlation proxy |
| flow | `F = 2 * frac_i(taker-buy quote share > 1/2) - 1` | breadth of buying pressure, not of price |
| positioning | `C = mean_i funding paid per bar, trailing 9 bars` | how one-sided the leveraged book is |

Dispersion is the complementary half. Under the approximate identity *cross-sectional variance ≈
average variance × (1 − average pairwise correlation)*, normalised dispersion **is** a correlation
proxy. Low dispersion means the universe has collapsed onto one factor — what risk-on/risk-off
deleveraging looks like from the inside. High dispersion means capital is discriminating between
names, the fragmenting late-cycle state that the equity literature (Maio 2016; Stivers & Sun 2010)
associates with *lower* subsequent index returns. Hence the negative sign.

```
S    = z(B) + 0.5*z(F) - 0.5*z(D) - 0.5*z(C)          (all z causal, 360-bar window)
net  = 0.25 * tanh((S + 0.5) / 1.0),  floored at |net| >= 0.05
w_i  = 1.0 * demeaned_rank(s_i)/gross  +  net * invvol_i
```

Every sign is fixed by external prior, declared before data: breadth and flow positive
(Zaremba et al. 2021), dispersion negative (Maio 2016), funding crowding negative (BIS WP 1087).
`b = 0.5` is an unconditional long tilt — the crypto risk premium is positive on average, and the
state variable modulates it rather than replacing it. `tanh` is the only concession I make to the
"event" half of my family: a breadth thrust and a breadth breakdown saturate, so extreme readings do
not produce extreme size.

### Why there is a neutral leg at all

This is the least obvious design choice and it is not decoration. My brief fixes a **common ex-ante
risk unit** that scales every lane to the same volatility. If my book were a pure net tilt,
`w_i = net/N`, then book return is `net·R` and book volatility is `|net|·sigma_R`; the risk unit
divides by exactly that and returns `v · sign(net) · R / sigma_R`. **The magnitude of my timing is
annihilated and only the sign survives** — my mandate would be untestable as stated.

Carrying a cross-sectionally neutral leg with roughly state-independent risk fixes this. Total book
variance becomes `gamma²·sigma_n² + net²·sigma_R² + 2·gamma·net·cov`, so the *share* of risk coming
from net exposure varies with state and survives a common scaler. After gross normalisation to 1.0
the neutral leg runs ~0.80–0.95 of gross and the timed leg ~0.05–0.20 — a composition that moves
with the state variable. I use the demeaned rank of the *same* primitive `s_i` rather than an
unrelated signal, so the book is one idea read two ways, not two strategies stapled together.

`gamma = 0` is a legal degenerate point of this design. If the harness turns out to want a pure
net-exposure book, I will say so rather than quietly re-specify.

---

## 2. Who is on the other side

Two counterparties, and only one of them is paying me for skill.

**(a) The risk-premium leg — I am short a tail where I am largest.** A breadth-timed book is
maximally long precisely when the market is broad, calm and low-dispersion. That is exactly the
state in which a regime break hurts most, because correlation has collapsed onto one factor and
nothing in the book diversifies. My counterparty is **the manager who declines to hold net exposure
in calm states because that tail is unhedgeable, and the market maker who must warehouse inventory
through the break**. When I am long in a broad state I supply risk-bearing capacity they have
withdrawn, and I am paid for it. When the state breaks I pay them back. Anyone reporting a
breadth-timing Sharpe without saying this is describing a short-volatility position and calling it
alpha. **I expect most of the realised return to be this, and it should be discounted accordingly.**

**(b) The behavioural leg — the part that justifies the mandate.** Zaremba et al. find the breadth
effect concentrates where limits to arbitrage are high and after bullish periods: a herding
signature, not a risk-compensation one. Crypto perps sit at the extreme of both. BIS WP 1087 gives
the same shape mechanically — trend-chasing retail demand for leveraged upside, met by arbitrage
capital that is chronically scarce because taking the other side means surviving margin spikes and
liquidations. My counterparty here is **the leveraged retail long paying funding to stay long into a
state that breadth, flow and dispersion say is fragile**: narrow participation, one-sided funding,
high dispersion. When I cut or reverse net exposure there, I stop being the marginal bid. Their exit
is mechanical (liquidation), not discretionary, and that forced exit is my return.

I do not claim (a) and (b) are separable in the data.

---

## 3. What would falsify this

Preregistered in THESIS §3, restated here so the record is in the outbox.

**F1 (primary) — breadth must lead, not summarise.** Regress the forward 3-bar (24h) equal-weight
index return on `B_t` **controlling for the trailing 3-bar index return**, Newey–West HAC lag 6,
pooled over the visible development window, at the fixed `L_b = 21`, `h = 3`:

```
sum_{j=1..3} R_{t+j} = a + b*B_t + c*sum_{j=0..2} R_{t-j} + eps_t
```

Pre-committed sign `b > 0`. **Falsified if `b_hat <= 0` or `|t(b_hat)| < 2.0`.** The `c` control is
the whole test: if breadth is a coincident summary of price, `b` collapses once trailing return is in
the regression. `h = 3` and `L_b = 21` are fixed; I will not substitute a passing horizon, and I will
not flip a negative `b_hat` into a "contrarian discovery".

**F2 (economic) — timing must beat a constant tilt.** Development Sharpe of this exact book with the
state-timed `net_t`, versus the identical book with `net_t` replaced by its own realised mean (a
constant, sign preserved), same ex-ante risk unit on both. **Falsified if the difference is `<= 0`
at this baseline.** F2 is evaluated *here*, at trial 0, before any knob moves. A state variable that
does not change the answer is not a state variable.

**F3 (sign discipline) — dispersion.** If the partial coefficient on `z(D_t)` is *positive* with
`|t| >= 2.0` in the F1 specification, my dispersion prior is wrong for this venue and I set
`w_d = 0`. **I do not flip it.** Flipping a sign after seeing data doubles the effective search
space; zeroing costs me something, which is the point.

**Directly observable failures in the returned packet** that would tell me the mechanism is not
there, independent of Sharpe: mean `|net|` not tracking any state (net pinned at the floor or the
cap), the timed and constant-net variants indistinguishable, gross edge per unit turnover failing
while the neutral leg alone passes (the tilt is pure cost), or survival at 3x cost failing while 1x
passes (I am harvesting a spread I cannot pay for).

---

## 4. What I already expect to be wrong

Recorded before the result so none of it can be presented later as a discovery.

1. **Breadth may simply be lagging.** Every moving-average-based breadth measure is mechanically
   lagging, and my `above-SMA` primitive is exactly that construction. F1's `c` control is the test,
   and it is a test I might fail.
2. **The effective sample is regime episodes, not bars.** 8h bars over a few years look like
   thousands of observations, but a *state* variable has as many independent observations as there
   are regimes — plausibly 10 to 30. This is the single strongest reason to expect a poor deflated
   Sharpe and **no parameter choice fixes it**. A pooled HAC t-statistic will overstate confidence.
3. **The neutral leg confounds the read.** It is a cross-sectional trend book and it will carry most
   of the gross. A good headline Sharpe may be that book, not my mandate. **F2 is the only number in
   the packet that isolates the mandate's claim**, and I will read it before I read the Sharpe.
4. **Turnover.** 8h rebalance across 60 names at ~4–5bp taker per side is not a rounding error. The
   `tanh` map with `b > 0` damps flips near the origin but does not remove them. I have added no
   hysteresis to the universe or the weights, deliberately — an undeclared turnover knob at trial 0
   would make the declared surface a fiction. If the cost gates bite, that is a diagnosis for a later
   phase and I will report it as one.
5. **Dispersion is partly coincident with realised volatility**, which the organizer's ex-ante risk
   unit may already supply for free. `w_d` could be paying for information I am given.
6. **Funding crowding is contaminated by trend.** Past return momentum explains more than half the
   time-series variation in the perp–spot spread (He et al.), so `C` may be a noisy copy of `B`.
   `w_c = 0` is in the declared grid for exactly this reason.
7. **Funding convention risk.** Binance settlement moved from 8h to 4h for many USD-M contracts and
   compresses to 1h at the cap, so a bar can hold one, two or eight events. I sum within the bar and
   average across symbols — "cost borne over the bar" — which is convention-stable in a way a
   per-interval mean is not. I could not verify this without data; if the field turns out to be a
   pre-aggregated per-bar rate, the sum is still correct.
8. **Universe non-stationarity.** The perp universe grew from tens to hundreds of symbols, so breadth
   has a non-stationary base rate and the 360-bar z-window is doing heavy lifting. If delisted
   contracts are absent from the data, historical breadth is biased *upward* — in the direction that
   flatters me. I will say so if I see it.

---

## 5. Implementation notes worth checking against the packet

- **Never flat, never silent.** Every path that cannot form a book returns `None` (hold) rather than
  `{}`, and the floor `|net| >= 0.05` plus the neutral leg guarantee a non-zero net inside the cap at
  every decision the book is formed. Mean `|net|` should land near 0.15–0.20 after gross
  normalisation, positive on roughly two thirds of bars.
- **Defensive reads throughout.** Panels are aligned on timestamps when the frames carry them and
  positionally from the newest row otherwise; a missing column collapses that term's z-score to 0
  rather than raising or producing NaN weights. This matters because a misread field produces a
  silently flat book that scores as "no edge" rather than "never ran".
- **Stateless.** Nothing persists between decisions; each book is recomputed from the past-only rows
  in the context handed in. No RNG, no dates, no symbol identity, no fitted artifacts. Signals are
  ratios and z-scores, so the book is invariant to a common price rescaling; universe ties resolve by
  stable sort on the given order, not by symbol name.
- **Gross is normalised to 1.0 and volatility is not targeted.** The organizer's risk unit rescales
  from there. The only guards carrying literals that are *not* in the declared surface are numerical:
  minimum name count, minimum z-history, a z-clip, and a floor on `sigma` at 20% of its
  cross-sectional median for the inverse-vol leg. None are signal knobs and none will be tuned.

**Declared trial accounting:** this is charged strategy trial **1** of a declared cap of **20**
(plus the unmodified organizer seed). The search protocol is a single-pass coordinate search over
the 8 knobs of THESIS §4.2 in fixed order, consuming 15 configurations; the remaining margin exists
for one partial second pass over the two lookbacks and nothing else.
