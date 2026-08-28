# team-14 — NOMINATION RATIONALE

**Mandate:** time net exposure from cross-sectional breadth and dispersion.
**Phase:** decision.
**What I nominate:** the **byte-exact source that produced trial `t02`** — the only configuration
of this mechanism that has ever been run. Not a re-tuned descendant of it.

---

## 1. The decision, stated first

Two charged trials exist. `t01` is the unmodified organizer seed. `t02` is my book, and it was
**admitted with zero failed gates**.

I am nominating `t02` unchanged. Three reasons, in order of weight:

1. **It is the only evidence I have about my own mechanism.** Every alternative configuration I
   could nominate has never been run. In this lane there is no market data mounted and no
   execution available — my entire evidence base is two JSON metric packets. A change I cannot
   test is a guess dressed as an improvement.
2. **Qualification is a bar on structure and cost, and this book clears every one of them with
   margin** (§3). Ranking happens on sealed blocks I will never see, and the phase guidance is
   explicit that a robust book I can explain beats a fragile one I cannot.
3. **The development Sharpe of 1.69 is a one-shot number, not a search maximum.** No configuration
   in this lane has ever been chosen by comparing two development results of my own strategy
   (§6). That is a rarer property than a higher Sharpe and I would rather nominate on it.

---

## 2. The mechanism

A Binance USD-M cross-section of several hundred perpetuals is not several hundred assets. It is
close to one common factor — the arrival and withdrawal of leveraged speculative capital — plus
narrative noise. That is normally a complaint; here it is the premise. Each symbol is a **noisy
measurement of one latent state**, and the cross-sectional *moments* estimate that state better
than the index price does, because they are not dominated by the one or two names that carry a
cap- or volume-weighted index.

- An index return of +2% says the factor moved. **Breadth** says how many measurements agree —
  whether the move is funded by broad capital arrival or by concentrated flow into a few names.
- **Dispersion** is the second moment of the same cross-section. Via
  `xs-variance ≈ average variance × (1 − average pairwise correlation)`, normalised dispersion is
  a **correlation proxy**. Low dispersion means the universe has collapsed onto one factor, which
  is what risk-on/risk-off deleveraging looks like from inside. High dispersion is the
  fragmenting, late-cycle rotation state that precedes weaker index returns, so it enters
  **negatively** (Maio 2016; Stivers & Sun 2010).
- **Taker-flow breadth** and **mean funding** are the positioning readings of the same state.
  Perps never expire, so crowding compounds instead of resetting at roll, and funding is a
  continuously observable positioning tax.

The book is one primitive read at two moments:

```
s_i   = (close_i / SMA_90(close_i) − 1) / sigma_i          per-symbol primitive
S     = z(B) + 0.5·z(F) − 0.5·z(D) − 0.5·z(C)              state variable
tau   = 0.25 · tanh((S + 0.5)/1.0),  floored at |tau| ≥ 0.05
w     = (1 − |tau|)·n  +  tau·v
```

`n` is the dollar-neutral rank core of `s_i` and trailing funding carry (`sum(n)=0`,
`sum(|n|)=1`); `v` is a long inverse-vol distribution summing to 1. By construction
**`sum(w) = tau` exactly** and `sum(|w|) ≤ 1`.

**The neutral leg is not decoration.** If the book were a pure net tilt `w_i = tau/N`, its return
is `tau·R` and its volatility is `|tau|·σ_R`; the organizer's common ex-ante risk unit divides by
exactly that, and **the magnitude of my timing is cancelled — only the sign survives**. With a
neutral leg, book variance is `γ²σ_n² + tau²σ_R² + 2γ·tau·cov`, so the *share* of risk coming from
net exposure varies with state and survives a common vol scaler. This hazard was recorded in the
sealed thesis (§1.6) before any data was mounted, and the design is the mitigation.

Two packet numbers are consistent with the mitigation working: `mean_gross_exposure` 0.888 and
`risk_unit_capped_fraction` 0.008. The book's native gross sits near 0.89 because the per-name clip
at 0.08 binds, and the common risk unit almost never needed to lever past the gross cap — i.e. the
risk unit is not fighting the book. That is weaker than a direct measurement, and I flag it as an
inference rather than a result.

---

## 3. Why it qualifies — the packet read honestly

Cost per unit turnover is an **environment constant** across both trials, and that is the single
most useful thing the two packets jointly reveal:

| | t01 (seed) | t02 (nominated) |
|---|---|---|
| gross edge / yr | `9.05 × 225.1` = **20.4%** | `57.86 × 35.85` = **20.7%** |
| cost per unit turnover | `0.828 × 9.05` = **7.50 bps** | `0.130 × 57.86` = **7.50 bps** |
| annualised turnover | 225.1 | **35.8** |
| cost share of positive gross | 82.8% | **13.0%** |
| net / 2x / 3x | 0.30 Sharpe / −1.14 / −26.6% | **1.69 / 1.44 / +13.0%** |
| max drawdown | 23.9% | **10.1%** |
| failed gates | 4 | **0** |

**The redesign did not manufacture gross edge. It produced essentially the same ~20.5%/yr gross as
the seed while paying one sixth the cost.** I want that stated plainly, because the opposite claim
— that I found a better signal — would be false. The seed's signal was never the problem; it paid
7.5 bps to buy 9.05. The three structural changes (averaging the *target vector* over M
recomputations, a 30-day trend primitive, and a soft threshold on the rank score) cut turnover 6.3x
at a cost of `(M−1)/2` bars of lag, and the gross edge survived that lag intact.

The cost-degradation profile is close to linear — 1.69 → 1.44 → ~1.21 implied at 3x — with no
cliff. A book whose edge is a spread it cannot pay for shows a cliff. This one does not.

**Gate margins, including the thin one.** `median_effective_breadth` is 19.3 against the seed's
29.7. Both passed on 100% of bars, so the per-bar threshold sits below my minimum, but this is the
gate closest to biting and the soft threshold `θ = 0.25` is what bought density at its expense. If
a sealed block presents a thinner or less liquid universe, this is where I would expect trouble
first. I chose not to concentrate harder for exactly this reason.

**Net exposure and the mandate.** `long_exposure_share` 0.527 vs `short_exposure_share` 0.473 puts
mean net at ~5.3% of gross, ~0.047 absolute — non-zero at every decision by construction (the
`|tau| ≥ 0.05` floor), timed by the state variable, and modest relative to the 0.25 cap. I will not
dress that up: this is a bounded tilt, not a directional book. Two things are worth knowing about
it. First, **within my preregistered parameter surface this is already the maximum-net corner** —
`b ∈ {0, 0.5}` and `κ ∈ {1.0, 2.0}`, and mean `|tau|` is largest at the largest `b` and smallest
`κ`, which is where the nomination sits. Reaching a materially larger net requires leaving the
declared surface after seeing that net came in small, which is precisely the move my sign-and-search
discipline forbids. Second, it would be a bad trade anyway: more net raises the market-beta share of
risk, the common risk unit then scales the whole book down, and the cross-sectional density that
clears the cost gates goes with it. The organizer admitted this book with zero failed gates, and
that list includes both-sides-used measured on exposure.

---

## 4. Who is on the other side

Two counterparties, and only one is paying me for skill.

**(a) Risk premium — I am short a tail exactly where I am largest.** A breadth-timed book is
maximally long precisely when the market is broad, calm and low-dispersion, which is the state where
correlation has collapsed onto one factor and nothing in the book diversifies. The other side is the
manager who declines net exposure in calm states because that tail is unhedgeable, and the market
maker who must warehouse inventory through the break. I supply risk-bearing capacity they withdrew;
when the state breaks I pay it back. **I expect most of any realised return to be this**, and a
development Sharpe of 1.69 over 808 days is substantially a statement about which tails did not
arrive in that window.

**(b) Inefficiency — constrained arbitrage and herding.** The other side is the leveraged retail
long *paying* funding to stay long into a state that breadth, flow and dispersion call fragile:
narrow participation, one-sided funding, high dispersion. Their position is a function of recent
price rather than of state, and their exit is mechanical (liquidation) rather than discretionary.
Arbitrage capital is chronically undersupplied here because perps have no expiry, so an arbitrageur
faces unbounded convergence risk plus margin spikes (BIS WP 1087; He et al.). This is the leg that
justifies the mandate at all.

The book trades **both channels of (b)**: the time-series channel (cut or reverse net when mean
funding says the whole book is crowded) and the cross-sectional channel (underweight the individual
names where leveraged longs are most crowded, at `CARRY_SHARE = 0.40`). The second is also the only
edge here whose density *rises* with holding period — funding earned by being short a crowded name
accrues at zero marginal turnover, which is exactly what `gross_edge_bps_per_turnover` rewards.

---

## 5. What would falsify this

**F4 — the cost fix had to be a cost fix, not a signal lobotomy. NOT falsified.** Preregistered in
the refinement rationale: falsified if turnover landed in band but density stayed near the seed's
~9 bps, which would mean the gross edge lived entirely at horizons my averaging destroys. Turnover
35.8, density 57.9. This is the one preregistered test that the evidence actually settled, and it
passed.

**F1 — breadth must lead, not summarise. NEVER EVALUATED, and I will not pretend otherwise.** The
primary falsifier was preregistered as a pooled HAC regression of forward 3-bar index return on
breadth *controlling for trailing index return*, falsified at `b̂ ≤ 0` or `|t| < 2.0`. The research
phase supplied standardised metric packets, not raw data or an execution surface, so this regression
could not be computed. **My primary falsifier is untested.** That is a material limitation of this
nomination and it is not one I can engineer around from inside the lane.

**F2 — timing must beat a constant tilt. NEVER EVALUATED.** The packet does not decompose the book
into timed-net and constant-net variants, so the number that would isolate the mandate's own claim
does not exist. The headline Sharpe is therefore **not** evidence for the state variable; it is
evidence for the whole book, of which the cross-sectional core carries most of the gross. I said in
the discovery rationale that I would read F2 before the Sharpe. I could not read it, so the Sharpe
should be read as unattributed.

**F3 — dispersion sign discipline. Unexercised.** No development regression was available, so no
evidence arose that could have triggered zeroing `w_d`. The sign remains where the prior put it.

**What would falsify this on sealed blocks:**

- **Density collapses toward the 7.5 bps cost line while turnover stays near 36.** That says the
  cross-sectional core was period-specific and the ~20.5%/yr gross does not generalise. This is the
  cleanest single kill shot and it is visible independently of Sharpe.
- **A sealed drawdown materially worse than 10%, concentrated in one deleveraging episode.** That is
  §4(a) arriving: I was paid for a tail, and then the tail came. My thesis says this is the *most
  likely* way this book underperforms, so I would read it as confirmation of the mechanism's cost,
  not as a bug.
- **`long_exposure_share` converging to 0.500.** The state variable stopped moving, and the mandate
  is being met only by the `|tau| ≥ 0.05` floor rather than by any view.
- **Effective breadth falling below the gate on a non-trivial fraction of bars.** The `θ = 0.25`
  threshold was set for density on a 60-name universe; a thinner sealed universe breaks it.

---

## 6. Search accounting — the honest version

**Charged trials: 2 of a declared cap of 20.** One was the organizer seed.

**No knob has ever been selected by comparing two development results of my own strategy.** The
single move off the preregistered baseline — `L_b` 21 → 90, a declared grid point — was derived
from turnover arithmetic on the *seed's* packet, before my mechanism had ever run. The coordinate
search declared in THESIS §4.3 was never executed.

**Against myself:** four constants in the nominated source were *not* in the preregistered surface —
`CORE_SMOOTH = 24`, `TILT_SMOOTH = 9`, `SCORE_FLOOR = 0.25`, `CARRY_SHARE = 0.40`. Each was set once
from the cost arithmetic in §3 and none was searched, but they widen the effective search space
beyond what was hashed at scouting. A deflation based on "2 trials" understates the real degrees of
freedom. I would rather record that than quietly let the trial count speak for a discipline it did
not fully cover.

**The largest expected weakness, stated at scouting and unchanged:** the effective sample for a
*state* variable is regime episodes, not bars. 808 days of 8h bars look like ~2,400 observations; the
real N is plausibly 10–30. **No parameter choice fixes this**, and any t-statistic computed on these
bars overstates confidence.

---

## 7. Contract compliance

Symbols come from `context.eligible_symbols`; the panel is built on the `open_time` **column**, never
on the positional `RangeIndex`; the funding column read is `funding_rate`. `sum(|w|) ≤ 1.0`,
`|sum(w)| ≤ 0.25` and `|w_i| ≤ 0.08` (inside the 0.10 rule cap) are enforced in `_finalise` after
clipping. A book is returned on every decision the data supports; every degenerate path returns
`None` (hold), never a silent `{}` — `active_bar_fraction` was 1.000 on 808 days.

Against the organizer's pre-nomination checks:

- **future-append / corrupt-future:** only past-only rows from `context` are read; nothing is cached.
- **exact-replay determinism:** no RNG, no mutable attributes on the strategy object, no state across
  decisions; `seed` is unused.
- **calendar-shift equivariance:** no absolute dates. Funding is attached to bars by relative position
  in integer nanoseconds against `bar_ns[0]`, never against a calendar anchor.
- **symbol pseudonymisation:** no symbol literals. The universe sort keys on `item[0]` (volume) only,
  so ties fall back to `eligible_symbols` order via Python's stable sort rather than to symbol name;
  cross-sectional ranks use `method="average"`, so ties do not depend on arrival order.
- **magnitude-scale equivariance:** every price input is a ratio (`close/SMA`), a log return, or a
  volume *share*. A common rescaling of prices leaves the book unchanged, and rescales `quote_volume`
  uniformly so the liquidity ranking is preserved.
- **small-perturbation stability:** `tanh` is smooth and `SCORE_FLOOR` is a *soft* threshold
  (continuous at the knee). The two hard per-symbol indicators — `sign(s_i)` for breadth and
  `ratio > 0.5` for flow breadth — are averaged across ~60 names before use, so the aggregate is
  stable. The one genuine discontinuity is the `|tau| ≥ 0.05` floor at a sign crossing; it moves
  0.10 of net across ~60 inverse-vol names (~0.0017 each) and leaves `(1 − |tau|)` unchanged, so its
  turnover footprint is negligible. It is in the sealed design and it is what makes "non-zero net at
  every decision" literally true, so I kept it.

Volatility is not targeted anywhere. No network, subprocess, filesystem, `eval`/`exec`, RNG, embedded
data, fitted artifact or cross-decision state.
