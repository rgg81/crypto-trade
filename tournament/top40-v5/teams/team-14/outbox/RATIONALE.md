# team-14 — RATIONALE

**Mandate:** time net exposure from cross-sectional breadth and dispersion.
**Phase:** refinement. **Prior evidence:** one packet, `t01`, which is the *unmodified organizer
seed* — not this design. My mechanism has never been run.

---

## 1. What t01 actually told me

t01 is the seed, so it is a reading of the **environment**, not a verdict on my thesis. Read that
way it is very informative, because it prices the constraint that killed it:

| quantity | value |
|---|---|
| gross return before cost | 20.4%/yr (`9.053 bps × 225.10`) |
| net return | 2.91%/yr |
| **cost per unit turnover, 1x** | **~7.5 bps** (`0.8284 × 9.053`) |
| turnover | 225/yr = 0.206 per bar at gross 1.0 |

The seed's gross Sharpe is about `20.4 / 11.68 = 1.75`. **Its signal was not the problem.** All
four failed gates — `turnover_ceiling`, `gross_edge_density`, `cost_share`,
`survives_triple_cost` — are one number seen four ways: it paid 7.5 bps to buy 9.05 bps.

That converts the phase guidance into an inequality. Surviving 3x needs
`gross_edge_bps_per_turnover > 3 × 7.5 = 22.5`; being a *book* rather than a knife-edge needs
headroom. **Target ≥ 35 bps per unit turnover — a ~4x improvement.**

This is a design problem, not a parameter problem, and it has a specific shape: for a
cross-sectional book whose scores have one-bar autocorrelation `ρ ≈ 1 − 1/L`, per-bar turnover
goes as `sqrt(2/L)`. Going from a 21-bar to a 90-bar lookback buys only **2x**. Lookback alone
cannot close a 4x gap. Something structural has to change.

## 2. The mechanism

A Binance USD-M cross-section of several hundred perpetuals is not several hundred assets. It is
close to one common factor — the arrival and withdrawal of leveraged speculative capital — plus
narrative noise. Each symbol is therefore a **noisy measurement of one latent state**, and the
cross-sectional *moments* estimate that state better than the index price does, because they are
not dominated by the one or two names that carry a cap- or volume-weighted index.

- An index return of +2% says the factor moved. **Breadth** says how many measurements agree —
  whether the move is funded by broad capital arrival or by concentrated flow into a few names.
- **Dispersion** is the second moment of the same cross-section. Via
  `cross-sectional variance ≈ average variance × (1 − average pairwise correlation)`, normalised
  dispersion is a **correlation proxy**. Low normalised dispersion means the universe has
  collapsed onto one factor, which is what risk-on/risk-off deleveraging looks like from inside.
  High dispersion is the fragmenting, late-cycle rotation state that precedes weaker index
  returns, so it enters with a **negative** sign (Maio 2016; Stivers & Sun 2010).
- **Taker-flow breadth** and **mean funding** are the positioning readings of the same state.
  Perpetuals never expire, so crowding compounds instead of resetting at roll, and the funding
  rate is a continuously observable positioning tax.

The book expresses this in the shape the professional population actually uses — a bounded
directional tilt on top of a cross-sectional book, not a standalone timing model:

```
w = (1 − |tau|) · n  +  tau · v
```

`n` is dollar-neutral with `sum(|n|) = 1`; `v` is a long inverse-vol distribution summing to 1;
`tau = 0.25·tanh((S + 0.5)/1.0)`, `S = z(B) + 0.5·z(F) − 0.5·z(D) − 0.5·z(C)`. By construction
`sum(w) = tau` and `sum(|w|) ≤ 1`.

**The neutral leg is not decoration.** If the book were a pure net tilt `w_i = tau/N`, its return
is `tau·R` and its volatility is `|tau|·σ_R`; the organizer's common ex-ante risk unit divides by
exactly that, and **the magnitude of my timing is cancelled — only the sign survives**. With a
neutral leg, book variance is `γ²σ_n² + tau²σ_R² + 2γ·tau·cov`, so the *share* of risk coming
from net exposure varies with state and survives a common vol scaler. Here `γ = 1 − |tau|`,
because gross ≤ 1 is a hard cap and a free `γ` would only be renormalised away. This was recorded
in the sealed thesis (§1.6) before any data was mounted.

## 3. Who is on the other side

Two counterparties, and only one of them is paying me for skill.

**(a) Risk premium — I am short a tail where I am largest.** A breadth-timed book is maximally
long precisely when the market is broad, calm and low-dispersion, which is exactly the state where
the correlation structure has collapsed and nothing in the book diversifies. The other side is the
manager who declines net exposure in calm states because that tail is unhedgeable, and the market
maker who must warehouse inventory through the break. I supply the risk-bearing capacity they
withdrew; when the state breaks I pay it back. **I expect most of any realised return to be this**,
and a strong development Sharpe here is a statement about which tails did not happen.

**(b) Inefficiency — constrained arbitrage and herding.** The other side is the leveraged retail
long *paying* funding to stay long into a state that breadth and dispersion call fragile, whose
position is a function of recent price rather than of state and whose exit is mechanical
(liquidation) rather than discretionary. Arbitrage capital is chronically undersupplied here
because perps have no expiry, so an arbitrageur faces unbounded convergence risk plus margin
spikes. This is the leg that justifies the mandate at all.

The candidate now trades **both channels of (b)**: the time-series channel (cut or reverse net
when mean funding says the whole book is crowded) and the **cross-sectional channel** (underweight
the individual names where leveraged longs are most crowded). Same counterparty, same mechanism,
second expression. See §5 — this is an amendment to the sealed design and I am not pretending
otherwise.

## 4. How the cost gates are closed

Three structural changes, in order of how much each contributes.

**(i) Averaging the target vector, not the signal.** Each leg is recomputed on the last `M` bars
of strictly past data and the resulting *target vectors* are averaged. Then
`Δw = (w_t − w_{t−M})/M`, and since `|w_t − w_{t−M}| ≈ sqrt(M)·|Δw_1|` before saturation,
**turnover falls by `1/sqrt(M)` while the lag cost is only `(M−1)/2` bars**. This is the lever
lookback cannot supply, and it changes no signal definition.

Crucially the two legs get **different depths**, because they have different information horizons:

| leg | depth | mean lag | why |
|---|---|---|---|
| neutral core | `M = 24` (8 days) | 4 days | reshuffles the whole book; the 30-day trend primitive's own horizon dwarfs a 4-day lag |
| directional tilt | `M = 9` (3 days) | 1.3 days | this *is* the mandate; averaging it as hard as the core would neuter the thing being tested |

A single depth for both was the obvious simplification and it is the wrong one: `M = 24` on the
tilt puts a 4-day lag on a state variable whose preregistered test horizon is 1 day.

**(ii) A 30-day trend primitive** (`L_b = 90`, a declared grid point) instead of a fast one.
Worth ~2x on its own.

**(iii) A soft threshold on the rank score** (`θ = 0.25`). Mid-pack names carry almost no
conviction and almost all of the rank churn; they are held flat rather than traded around. This
raises edge per unit turnover directly. `θ` is deliberately mild so effective breadth stays high
(projected ~40 versus the seed's passing 29.7) — concentrating harder would buy more density and
risk the breadth gate, which is not a trade I want.

**(iv) Carry accrues while holding.** Funding earned by being short a crowded name is collected
every bar at **zero marginal turnover**. It is the only edge available here whose density *rises*
with holding period, which is precisely what `gross_edge_bps_per_turnover` measures.

**Projected budget:** core ≈ 38/yr + tilt ≈ 14/yr + universe churn ≈ 5/yr ≈ **55–60/yr**, a ~4x
cut. At 35 bps density that is gross ~19%/yr, cost share ~14% at 1x, and roughly **+7% net at 3x
cost**. The turnover gate is a *band*, so I aimed for the interior rather than the floor: cutting
to 15/yr would trade one failed gate for another.

## 5. Amendments to the sealed thesis — declared, not hidden

The sealed surface (§4.2) had 8 knobs. This candidate sits at declared grid points for all of
them — `L_b = 90`, `L_d = 9`, `w_f = w_d = w_c = 0.5`, `κ = 1.0`, `b = 0.5` — with `γ` pinned to
`1 − |tau|` by the gross cap. **`L_b = 90` rather than the baseline 21 is the single knob move,
and it was chosen from the turnover arithmetic in §1, not from any performance result** (I have no
performance result on this mechanism to choose from).

Four constants are **new** and were not in the sealed surface. Each was set once, by the cost
arithmetic above, and none was searched:

| new | value | forced by |
|---|---|---|
| `CORE_SMOOTH` | 24 | turnover gate |
| `TILT_SMOOTH` | 9 | turnover gate, bounded below by the mandate's own horizon |
| `SCORE_FLOOR` | 0.25 | edge density vs. the breadth gate |
| `CARRY_SHARE` | 0.40 | edge density at zero turnover |

Honest accounting: this widens the effective search space beyond what was preregistered, so any
Sharpe this produces should be deflated harder than the sealed trial count implies. I would rather
say that than quietly re-specify. Charged strategy trials so far: **1**, and it was the seed.

## 6. What would falsify this

**F1 (primary, from the sealed thesis, unchanged).** Breadth must *lead*, not summarise. Pooled
over development bars, `Σ_{j=1..3} R_{t+j} = a + b·B_t + c·Σ_{j=0..2} R_{t−j} + ε`, Newey–West
lag 6. **Falsified if `b̂ ≤ 0` or `|t(b̂)| < 2.0`.** The `c` control is the whole test: if breadth
is a coincident summary of price, `b` collapses once trailing return is in the regression. I will
not substitute a passing horizon or lookback, and I will not flip the sign and call a negative
`b̂` a contrarian discovery.

**F2 (economic).** Timing must beat a constant tilt: the same book with `tau` replaced by its own
realised mean, at equal ex-ante risk. **Falsified if `Sharpe_timed − Sharpe_static ≤ 0`.** A state
variable that does not change the answer is not a state variable.

**F3 (sign discipline).** If dispersion's partial coefficient is *positive* with `|t| ≥ 2.0`, my
prior is wrong for this venue and I set `w_d = 0`. **I zero it; I do not flip it.**

**F4 (new, for this candidate specifically).** The cost fix must be a cost fix, not a signal
lobotomy. **Falsified if turnover lands in band but `gross_edge_bps_per_turnover` is still under
~22 bps** — that would say the seed's gross edge lived entirely at horizons my averaging destroys,
and slowing down cannot rescue this family. The distinguishing observation is that failure would
show up as turnover ~55 with density still ~9 bps, rather than as a turnover miss.

## 7. What I expect to be wrong

Stated before the result, so none of it can be presented later as a discovery.

1. **The effective sample is regime episodes, not bars.** 8h bars over 808 days look like ~2,400
   observations; a *state* variable has as many independent observations as there are regimes —
   plausibly 10 to 30. **This is the strongest reason to expect a poor deflated Sharpe and it is
   not fixable by any parameter choice.** Any HAC t-statistic here overstates confidence.
2. **Breadth may simply be lagging.** Every moving-average-based breadth measure is mechanically
   lagging, and my `above-SMA` primitive is exactly that construction. F1 is the test and it is a
   test I might fail.
3. **Dispersion may be paying for information the risk unit already supplies.** Cross-sectional
   dispersion spikes when the market breaks, so part of `D` is contemporaneous volatility, which
   the organizer's ex-ante risk unit captures for free.
4. **Funding crowding is contaminated by trend** — past return momentum explains more than half
   the time-series variation in the futures–spot spread, so `C` may be a noisy copy of `B`, and
   the cross-sectional carry leg may partly cancel the trend leg rather than diversify it.
5. **The `|net| ≥ 0.05` floor is a genuine discontinuity** at the sign crossing (a 10% book jump).
   It is in the sealed design and it makes "non-zero net at every decision" literally true, so I
   kept it, but it is the one place this book is not smooth.
6. **Survivorship.** If delisted contracts are absent from the dataset, historical breadth is
   biased *upward* — the names that would have sat below their moving averages are the ones that
   got delisted. That bias runs in the direction that flatters me.
7. **Requiring 124 bars of history excludes new listings**, which are the churniest and, per the
   thesis, a real part of the flow event being measured. That is a cost-driven exclusion and it
   may be removing signal along with the turnover.

## 8. Contract compliance

Symbols come from `context.eligible_symbols`; the panel is built on `open_time`, never on the
positional `RangeIndex`; the funding column read is `funding_rate`. `sum(|w|) ≤ 1.0`,
`|sum(w)| ≤ 0.25`, `|w_i| ≤ 0.08` are enforced in `_finalise` after clipping. No network,
subprocess, filesystem, `eval`/`exec`, RNG, embedded data or cross-decision state; `seed` is
unused; the strategy object holds no mutable attributes, so exact replay is deterministic. No
absolute dates (funding is aligned to bars by relative position in integer nanoseconds), no
hard-coded symbols, ties share an average rank so the book does not depend on symbol order, and
every price input is a ratio or a log return so the book is scale-equivariant. Volatility is not
targeted anywhere.
