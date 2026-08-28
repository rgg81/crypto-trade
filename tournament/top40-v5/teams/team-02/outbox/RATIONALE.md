# team-02 — funding convexity · nomination

**Family:** risk-premium harvesting · **Mandate:** realized-funding term structure against
realized volatility · **Evidence:** `lane/feedback/t01.json` (unmodified organizer seed) and
`lane/feedback/t02.json` (my refinement candidate), visible development window only.

---

## 1. What I am nominating, and why it is not the seed

I am nominating the book in `candidate.py`: cross-sectional funding carry priced per unit of a
dispersion-informed forecast of forward realized variance, held on a daily rebalance with
triangular rank weights.

**This departs from the letter of my sealed thesis §3.4, and I would rather say so at the top
than bury it.** That table routes to the unmodified seed in three of four branches, each
conditioned on F1 or F2 *failing*. Neither has been evaluated. F1 is a pooled panel regression
and F2 is an ablation A/B at the common risk unit; this phase has no shell, no execution
surface and no way to read a fitted coefficient out of a metric packet. So the pre-committed
triggers did not fire — they were never tested. Nominating the seed on that basis would be
obeying the form of a commitment whose condition is unknown, and it would nominate a book that
is strictly dominated on every number I actually have:

| | t01 (seed) | t02 (mine) |
|---|---|---|
| net Sharpe | −0.555 | **+0.126** |
| gross edge bps / turnover | 1.71 | **9.54** |
| cost share of positive gross | 4.376 | **0.786** |
| triple-cost annualised return | −0.169 | **−0.075** |
| max drawdown | 0.178 | **0.140** |
| positive fold fraction | 0.40 | **0.60** |

What I have instead of F1 is the next best thing, and it is in the code rather than in a
claim: **the dispersion coefficient is fitted online and shrunk smoothly to zero when the data
does not support it.** If funding dispersion carries no incremental information about forward
realized variance in the streamed panel, the book you are scoring is the same book with the
mandate's convexity term switched off — a carry-per-unit-of-realized-variance book, still
inside the mandate, without the conditioning. I cannot tell you which of those two you got. I
can tell you the choice is made by the data and not by me.

## 2. The diagnosis the packets actually support

Both trials failed **the same three gates and only those three**: `gross_edge_density`,
`cost_share`, `survives_triple_cost`. Every structural gate passed twice — breadth 12.8/12.7,
mean gross 0.83/0.95, long/short exposure 0.5005/0.4995 and 0.4927/0.5073, active bar fraction
0.99/1.00, turnover inside the band at 87 and 57. **This is not a "not a portfolio" failure.**
It is a cost failure, and the packets price it exactly:

| quantity | t01 | t02 |
|---|---|---|
| gross P&L = `edge_density × turnover` | 1.714 × 87.0 = 149 bps/yr | 9.536 × 56.9 = 543 bps/yr |
| net P&L (reported) | −531 bps/yr | +75 bps/yr |
| implied cost | ≈ 680 bps/yr | ≈ 468 bps/yr |
| **cost per unit turnover `k`** | **≈ 7.8 bps** | **≈ 8.2 bps** |

Two independent trials agree on `k ≈ 8 bps`. That single number determines everything:

> To clear `survives_triple_cost` the book needs **gross edge per unit turnover > 3k ≈ 25 bps.**

t02 sits at 9.5. This is not a parameter problem — **it is a floor on the holding period.** Write
`G/T = ρ · (gross × 365 / T)`, where `ρ` is gross P&L per day per unit of gross exposure. From
t02: `ρ = 9.536 / (0.948 × 365 / 56.92) = 1.57 bps/day`. At that `ρ`, clearing 25 bps requires
turnover of roughly **22/yr or below**. Everything slow in this candidate exists to get there,
and nothing in it is tuned to a Sharpe.

## 3. The mechanism

Binance USD-M funding is not a sentiment reading. It is a contract-enforced price, computed
from the *impact* bid/ask against the spot index and settled every 8h, so levered crowding is
transcribed into an observable cash flow mechanically, with no estimation step. A position of
sign `p` accrues `−p·f` each interval: **carry is earned by holding, not by predicting.** That
is why a cost-bound lane should be trading this and not a forecast — the numerator survives a
long holding period, which is exactly the thing §2 says must grow.

The premium is capped per interval; the deleveraging cascade that makes you pay for it is not.
Bounded premium, unbounded loss, is the payoff of selling variance. Funding *level* tells you
the size of the insurance premium but not whether it is adequate for the variance being
underwritten. That missing normalisation is the mandate's instruction, and with no options in
this dataset the closest analog the data supports is:

> **VRP analog = funding carry per unit of forecast forward realized variance.**

```
score_i = −( carry_i − median(carry) ) / vhat_i
w_i     = triangular rank weight of score_i, gross-normalised, net-neutral
```

- `carry_i` — realized funding **per day** over the trailing 21 days, computed as a time-window
  sum divided by elapsed days rather than a mean per print, so a contract switched to hourly
  settlement stays comparable with one settling every 8h.
- `vhat_i` — equal-weight HAR blend of log Garman–Klass 8h variance at 3d/7d/21d, **plus
  `b · log(funding dispersion)`**, with `b` fitted online by pooled within-symbol OLS on
  past-only streamed rows, constrained non-negative, capped at 1, and shrunk by `t²/(t²+4²)`.

Four things are load-bearing rather than cosmetic.

**(a) Carry is demedianed *before* the variance divide.** Funding has a positive
cross-sectional mean (the 0.01%/8h interest component plus structural long demand). Dividing
the raw level by variance leaves a residual `−median(carry)/v_i` term in every score — a pure
inverse-variance tilt that shorts the low-vol majors and buys the high-vol alts, with a size
that has nothing to do with the mandate. I treat the naive ordering as a defect, not a variant.

**(b) Dispersion enters the denominator and only the denominator.** That is the one place the
convexity term can act without becoming a gross-exposure timing rule. Gross is renormalised to
a constant at every rebalance, so the book expresses relative allocation only. The organizer
owns the risk unit; this construction does not contest it.

**(c) The falsifier is shrunk, not thresholded.** t02 used a hard `t ≥ 4` gate on the same
coefficient. A hard gate is a razor-thin threshold that a small perturbation can flip, toggling
the book between two regimes — precisely what the small-perturbation stability check is built to
catch. Continuous shrinkage is both the better estimator and the check-safe one. `T0 = 4` sits
above the thesis's preregistered 2.5 because pooled overlapping forward windows inflate a naive
t-statistic by roughly `√horizon`.

**(d) Triangular rank weights are a turnover instrument, not a cosmetic.** Weight is a
soft-thresholded function of cross-sectional *rank*, so a name sitting at the threshold carries
**exactly zero weight** and two names swapping rank there generate no trade at all. t02's
capped z-score book had the opposite property: it ran ~13 names pinned at the 0.095 cap, so a
name crossing the boundary cost a full round trip. The threshold `τ` is derived from the
universe size to hold effective breadth near 16 whatever the universe does, which makes the
breadth gate structural rather than incidental, and makes the maximum weight a constant
`1.5/16 ≈ 0.094` of gross independent of `n`.

### How this answers the diagnosis

| lever | mechanism | intended effect |
|---|---|---|
| carry window 21d (was 7d) | funding is persistent; the 21-day mean moves ~⅓ as fast per day | less signal-driven turnover |
| triangular rank weights | zero weight at the selection boundary; no cap-pinning | removes boundary churn outright |
| daily rebalance retained | 3 bars = 1 day, the longest stride that is whole-day calendar-shift safe | drift correction 14/yr, not 25/yr |
| HAR components 3d/7d/21d | matched to a multi-week holding period, smoother than 1d/3d/7d | less denominator-driven turnover |
| top-half liquidity screen | unchanged, §4.3 | costs and participation are worst in the thin tail |

**Rough target: turnover 20–30/yr, edge density 22–30 bps.** Those are order-of-magnitude
estimates, not predictions, and §5 says what it means if they are wrong.

## 4. Who is on the other side

**Paying the premium:** the levered long. Offshore retail, trend followers and
onshore-constrained funds who cannot or will not hold spot with custody and financing. They buy
convex upside and finance it with a funding drip, because their alternative is unavailable or
dearer.

**Already well supplied:** basis desks, market makers and delta-neutral yield vehicles who take
the other side unconditionally — roughly $14bn of stablecoin is backed by exactly this trade.

**On the other side of *this* book specifically — not the levered long.** That side is crowded
and I am not claiming the premium. My counterparty is the **unconditional funding harvester**:
the vehicle that collects funding without asking whether the premium is adequate for the
variance it is underwriting. That distinction is forced on me by the evidence rather than
chosen for elegance — the unconditional carry trade ran a Sharpe of 6.45 over Aug-2020–May-2025,
4.06 from 2024, and **negative in 2025**. Preregistering "harvest funding" in 2026 would be
preregistering a decayed factor. I am claiming the **conditioning**, against someone doing none
of it. The asymmetry that makes *ratio* the right functional form rather than *level*: the
crypto variance risk premium is larger in low-volatility regimes and smaller in high-volatility
ones, so a book that sells more insurance simply because the raw premium looks high leans the
wrong way.

## 5. What would falsify it

**F1 — information.** If the online dispersion coefficient never clears zero with a meaningful
t, funding dispersion carries no incremental information about forward realized variance over a
HAR baseline, the mandate's own falsifier has fired, and what was scored is the ablated book. I
could not evaluate this in the decision phase and say so plainly; the shrinkage means the book
degrades rather than breaks, which protects the score but *hides the answer*. That is a real
cost of the design and I am not going to pretend otherwise.

**F2 — economic.** If the dispersion-conditioned book does not beat its dispersion-deleted twin
by ≥ 0.15 Sharpe at the common risk unit, the signal is real but not harvestable at equal risk.
Also unevaluated, for the same reason. Running that twin is the control the preregistered
falsifier demands and it remains the first thing I would spend a trial on.

**F3 — the cost falsifier. This is the one that matters now, and it is specific:**

> If turnover lands in the designed 20–30/yr band but `gross_edge_bps_per_turnover` does **not**
> rise roughly in proportion to the turnover cut — i.e. it comes back near 12–15 rather than
> 22–30 — then `ρ` fell as the book slowed. The cross-sectional funding differential does not
> survive a multi-week holding period, the premium decays faster than it accrues, and slowing
> the book down only spreads the same edge over fewer trades.

That is not fixable by a parameter and I will not treat it as one. It would mean the family is
not tradeable at this cost level in this dataset, and that is a result.

**F4 — the turnover band.** If turnover undershoots the band, the holding period this book needs
to pay for `k ≈ 8 bps` is longer than the band admits, and the trade-off between the cost gates
and the structural band is adverse at every setting. Also a finding, not a knob. This is the
risk I am most exposed to and least able to size: I have two observations of the band's interior
(87 and 57) and none of its edges.

**What would surprise me and should be read as suspicious rather than good:** a large Sharpe
with breadth near the floor, or long/short exposure shares drifting away from 0.5/0.5. Either
means the rank symmetry is not holding and the book has become a directional bet on a window I
can see.

**Known weaknesses, unchanged and unsolved.** The book is structurally short momentum — shorting
the highest-funding names is shorting the crowd, and in a sustained trending tape that loses for
a long time before it wins. Funding is cap-censored exactly in the tail where dispersion should
be loudest, and at 8h resolution I see a capped print without knowing it was capped. 8h bars see
a cascade's round trip, not its excursion. The observation this lane is built on is a
practitioner post-mortem on a single event, while the strongest peer-reviewed evidence on cascade
early warning is negative. None of these has a fix in this dataset.

## 6. Honest accounting

**Deviations from the sealed 144-cell surface (THESIS §4.1), stated plainly.**

| item | declared | here | status |
|---|---|---|---|
| dispersion window `l`, RV estimator, signal form, cross-section, `h` | — | unchanged | primary-cell values |
| cross-sectional weighting | rank-based | triangular rank weights | §4.4 declared fallback |
| carry window `s` | {3, 9, 21} prints | **63 prints (21d)** | **off-surface** |
| RV components | single window `v := s` | **HAR 3d/7d/21d** | **off-surface** |
| rebalance stride | every interval | **every 3rd (daily)** | **off-surface** |
| soft threshold | none | **rank-space, τ from breadth** | **off-surface** |

Counting the surface I have actually made available to myself — 144 cells × carry window {4
values} / {3} × stride {2} × RV {2} × weighting {2} — the honest deflation figure is
**N ≈ 1500, not 144 and certainly not 1**. Two configurations have ever been charged. I would
rather report a large surface truthfully than a small one I have quietly exceeded.

The carry-demedian-before-divide (§3a) and the shrinkage-instead-of-threshold (§3c) are not
counted as knobs. Each has one defensible form and the alternative is a defect — an embedded
vol tilt in the first case, a perturbation-flippable regime switch in the second.

**Considered and rejected, so the omissions are visible.** The funding *term-structure slope*
(short-window carry minus long-window carry) is the most obviously mandate-adjacent signal I did
not use: it isolates transient crowding rather than the structural premium, and it is what the
Oct-2025 dispersion observation actually points at. I left it out because it is fast-moving, and
the binding constraint in this lane is that fast signals cannot pay for `k ≈ 8 bps`. Taker
order-flow features stay excluded per §4.5. No momentum overlay: it would reduce the short-momentum
drag that is this book's largest P&L leak, and it would also stop the book being the thing the
mandate names. A cost-aware liquidity tilt on weights was drafted and dropped — it lowers `k` and
lowers `ρ` by roughly as much, and it is three more numbers I could not defend.

## 7. Compliance

- **Interface.** `build_strategy()` → object with `target_weights(context, *, seed)`. Returns a
  `dict[str, float]` over `context.eligible_symbols`, or `None` to hold. Enforced in code:
  `Σ|w| ≤ 0.98`, `|w_i| ≤ 0.090`, `|Σw| ≤ 0.10`. The per-symbol cap is applied *after* the final
  centring and gross only ever scales down, so both caps are hard.
- **Panel alignment.** Every cross-symbol structure is keyed on timestamps, never on the
  positional `RangeIndex`. Funding is grouped **per symbol** rather than pivoted into a union
  panel — a contract on hourly settlement cannot inject index rows that turn every other
  symbol's window into NaN. Dispersion joins onto `open_time` by `searchsorted(side="left") − 1`,
  so it uses funding strictly earlier than the bar it is attached to. Bar cadence is inferred
  from `open_time` diffs, not assumed.
- **No look-ahead.** The regression target is realized variance over the *next* `h` bars, used
  only for rows whose forward window lies entirely in the past relative to the boundary.
- **No hidden state.** Nothing is cached between decisions. The rebalance clock is the decision
  boundary counted in whole bar intervals since the epoch in integer arithmetic — no state, no
  dependence on appended future rows, no symbol identity, no price scale. One day is exactly
  three 8h intervals, so any whole-day calendar shift leaves the phase unchanged.
- **Invariances.** Scale: Garman–Klass reads log ranges, funding rates are already scale-free,
  quote volume enters only through a median split, and only the *ratio* of `vhat` is used, so its
  level cancels. Pseudonymisation: no symbol literal anywhere; ranks use `method="average"` so
  ties do not depend on symbol ordering. Determinism: no RNG, `seed` accepted and unused.
- **Banned constructs.** No network, subprocess, filesystem, `eval`/`exec`/`compile`,
  `__import__`, `getattr`/`setattr`. No embedded fitted parameters or data tables — the only
  coefficient in the book is fitted at runtime from streamed rows.
- **Degenerate paths.** If the online fit is unusable the forecast falls back to the HAR baseline
  and **the book still trades**; it never depends on the regression succeeding. During warm-up the
  63-day history screen steps down to the most history the universe actually has, and only then.
- **Blind spot, flagged rather than buried.** The top-level handler converts a malformed decision
  into `None` (hold) instead of a crash, which is the failure mode RULES warns about. The tell in
  the packet is `mean_gross_exposure` and `active_bar_fraction`: at or near zero means this book
  did not run, and the fix is parsing, not economics. t02 exercised the same parsing helpers and
  returned `active_bar_fraction = 1.0`, which is the strongest evidence available that the
  context is being read correctly.

**Not verified by execution.** This phase has no shell, so the candidate has been reviewed by
reading, not run. The specific risks I could not discharge: whether turnover lands inside the
band at the designed holding period (F4), and whether `ρ` survives the slowdown (F3). Both are
stated above as falsifiers rather than as assumptions.
