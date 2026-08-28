# team-02 — funding convexity · refinement candidate

**Family:** risk-premium harvesting · **Mandate:** realized-funding term structure against
realized volatility · **Prior evidence:** `lane/feedback/t01.json` (the unmodified organizer
seed), visible development window only.

---

## 1. Diagnosis of t01 — what the seed actually failed at

t01 failed three gates: `gross_edge_density`, `cost_share`, `survives_triple_cost`. It passed
every structural gate — breadth 12.8, mean gross 0.83, long/short exposure 0.5005/0.4995,
participation 0.99, and the turnover band at 87/yr. **This is not a "not a portfolio"
failure.** The seed is a well-formed book with nothing in it.

Backing the cost curve out of the packet:

| quantity | derivation | value |
|---|---|---|
| gross P&L | `1.7141 bps × 86.999` | **+149 bps/yr** |
| net P&L | reported | **−531 bps/yr** |
| implied cost | difference | **≈ 680 bps/yr** |
| **cost per unit turnover** | `680 / 87` | **≈ 7.8 bps** |
| same at 3× | | **≈ 23.4 bps** |

`cost_share_of_positive_gross = 4.376` is consistent with this (4.376 × 149 ≈ 652 bps).

One more thing the packet fixes for free: `active_bar_fraction = 0.990924092409241` is exactly
`2402/2424`. So the window carries **2424 decisions over 808 days — 8-hourly decisions, three
per day**, and the seed lost exactly 22 bars to warm-up. Every window below is sized against
that, and the code infers the cadence from `open_time` rather than assuming it.

**The binding constraint, stated as arithmetic.** To clear `survives_triple_cost` a book needs
`gross_edge_bps_per_turnover > ~23.4`. The seed is at 1.71. That is a **14× gap**, and no
parameter on any grid moves a number 14×. Two structural levers have to move together:

1. **Hold long enough that the carry pays for its own round trip.** At 3× cost a position must
   earn 23.4 bps of edge before it is worth opening. This is not a preference, it is a floor on
   the holding period, and it is the single most important number in the packet.
2. **Stop spreading gross across names with no conviction.** Every name held at a weight whose
   signal is indistinguishable from zero contributes turnover to the denominator and nothing to
   the numerator.

Both are *design* problems. The candidate changes the design; it does not tune the seed.

---

## 2. The mechanism

The funding rate on Binance USD-M is not a sentiment reading — it is a contract-enforced price,
computed from the impact bid/ask against the spot index, settled every 8h. It transcribes
levered crowding into an observable cash flow mechanically, with no estimation step. A position
of sign `p` accrues `−p·f` each interval: **carry is earned by holding, not by predicting.**

Funding *level* tells you the size of the insurance premium. It does not tell you whether the
premium is adequate for the variance being underwritten. The mandate's instruction — trade the
funding term structure *against realized volatility* — is exactly that missing normalisation.
With no options in this dataset there is no implied variance and therefore no literal VRP, but
funding is the only observable *price of a risk* here and realized variance is the only
observable *cost of bearing it*. The tradeable object is the ratio:

> **carry per unit of forecast forward realized variance**, taken cross-sectionally.

The book is:

```
w_i  ∝  −( carry_i − median(carry) ) / vhat_i        then demeaned, capped, gross-normalised
```

- `carry_i` — mean of the last **21** eight-hour funding prints (7 days).
- `vhat_i` — forecast of forward realized variance: a HAR baseline on **Garman–Klass** 8h
  variance (1d / 3d / 7d components) plus a trailing **funding-dispersion** term measured as
  the standard deviation of the last **63** prints (21 days), fitted online.

Three points about the construction that are load-bearing rather than cosmetic:

**(a) The carry is demeaned *before* the variance divide.** Funding has a positive
cross-sectional mean (the 0.01%/8h interest component plus structural long demand). Dividing
the raw level by variance therefore leaves a residual `−mean(carry)/v_i` term in every score —
a pure inverse-variance tilt that shorts the low-vol majors and buys the high-vol alts, with a
size that has nothing whatever to do with the mandate. Demeaning first removes it and leaves
`1/v` doing the one job it should: sizing the *deviation* by the risk borne to hold it. I
consider the naive ordering a construction defect, not a variant.

**(b) The dispersion term self-falsifies at runtime.** The coefficient on log dispersion is
fitted online by pooled OLS of log forward RV on the HAR basis, over past-only streamed rows,
and is **admitted only if it is positive with t ≥ 4.0**. The threshold is deliberately above
the thesis's preregistered 2.5 because pooled overlapping forward windows inflate a naive
t-statistic by roughly `sqrt(horizon)`. If dispersion is only a noisy re-encoding of trailing
volatility — the failure mode I named as most likely — the coefficient is set to zero and the
book degenerates cleanly to the HAR baseline. **The mandate's falsifier is wired into the
strategy rather than asserted about it.**

**(c) Gross is normalised to a constant at every rebalance.** The score is scale-free and
carries no gross-exposure timing, so the book expresses relative allocation only. Volatility
targeting is the organizer's control and this construction does not contest it.

### How this answers the diagnosis

| lever | mechanism | expected effect |
|---|---|---|
| carry window 21 prints (7d) | funding is persistent; a 7-day mean is both a better forecast of next week's funding and a slower-moving target | fewer signal-driven trades |
| rebalance every 3rd decision | daily, at the funding boundary; a position gets ~3 intervals to accrue before it is revisited | ~1/√3 of the per-decision turnover |
| soft-threshold at 0.4 MAD | names whose score is indistinguishable from zero go to *exactly* zero, not to a small churning weight | raises numerator, cuts denominator |
| top-half liquidity screen | costs and participation limits are worst in the thin tail | lowers realised bps per unit turnover |

Rough target: turnover ≈ **25–40/yr** against the seed's 87, which needs roughly **6–9% gross
annual** to clear triple cost. For scale, a book at gross ≈ 1.0 whose weights align with a
cross-sectional funding deviation of ~1 bp per 8h accrues ~3 bps/day ≈ 11%/yr in carry alone.
That is the right order of magnitude — which is the point of choosing a mechanism whose return
is a cash flow rather than a forecast. **These are order-of-magnitude estimates, not
predictions**, and §6 says what it means if they are wrong.

---

## 3. Who is on the other side

**Paying the premium:** the levered long. They are buying convex upside and financing it with a
steady funding drip, because the alternative — spot with custody and financing, or no leverage
at all — is unavailable or dearer to them. Offshore retail, trend followers, and
onshore-constrained funds.

**Already well supplied:** basis desks, market makers and delta-neutral yield vehicles who take
the other side unconditionally.

**On the other side of *this* book specifically — not the levered long.** That side is crowded.
My counterparty is the **unconditional funding harvester**: the vehicle that collects funding
without asking whether the premium is adequate for the variance it is underwriting. This
distinction is forced on me by the evidence, not chosen for elegance — the unconditional carry
trade has decayed hard (Sharpe 6.45 over Aug-2020–May-2025, 4.06 from 2024, **negative in
2025**). Preregistering "harvest funding" in 2026 would be preregistering a decayed factor. I
am not claiming the premium. I am claiming the **conditioning**: the cross-sectional dispersion
in premium-per-unit-variance that persists because capturing it is genuinely risky rather than
free. The supporting asymmetry is that the crypto variance risk premium is *larger* in
low-volatility regimes — so a book that sells more insurance simply because the raw premium
looks high is leaning the wrong way, and one that sizes on premium *relative to* forecast
variance is leaning the right way.

---

## 4. What would falsify this

Stated before the result, in descending order of how cheaply each one kills the lane.

**F1 — information (thesis §3.1, now embedded).** If the online dispersion coefficient never
clears `t ≥ 4` positive, funding dispersion carries no incremental information about forward
realized variance over a HAR baseline, the mandate's own falsifier has fired, and the book you
are scoring is the HAR-baseline book with the mandate's distinguishing term switched off.

**F2 — economic (thesis §3.3).** If the dispersion-conditioned book does not beat the same book
with the dispersion term removed by ≥ 0.15 Sharpe at the common risk unit, the signal is real
but not harvestable at equal risk.

**F3 — the cost falsifier, specific to this trial and new in refinement.** This is the one that
matters most now:

> If turnover falls to ≈ 25–40/yr as designed but `gross_edge_bps_per_turnover` does **not**
> improve by roughly the same factor as the turnover cut, then the seed's thin edge was never a
> turnover problem — the cross-sectional funding signal has no gross edge at the common risk
> unit, and slowing the book down only spreads the same nothing over fewer trades.

That outcome is not fixable by a parameter and I will not treat it as one. The pre-committed
consequence stands: nominate the unmodified seed and report that this dataset does not support
the family.

**F4 — the turnover band.** If turnover undershoots the band, the holding period is too long for
this book to count as a portfolio, and the trade-off between the cost gates and the band is
adverse at every setting. That is also a finding, not a knob.

**What would surprise me and should be treated as suspicious rather than good:** a large Sharpe
accompanied by breadth near the floor, or by long/short exposure shares drifting away from
0.5/0.5. Either means the demean is not holding and the book has become a directional bet on a
window I can see.

---

## 5. Honest accounting

**Deviations from the sealed primary cell (THESIS §4.2), stated plainly.**

| item | primary cell | here | status |
|---|---|---|---|
| `s` carry window | 9 prints (3d) | **21 prints (7d)** | on the declared grid `{3, 9, 21}` |
| `l`, dispersion, RV estimator, signal form, cross-section, `h` | — | unchanged | primary-cell values |
| rebalance stride | every interval | **every 3rd (daily)** | **not on the declared surface** |
| soft-threshold τ | none | **0.40 MAD** | **not on the declared surface** |

The `s` move is a within-grid choice made on mechanism, not on feedback: t01's measured cost
curve sets a floor on the holding period, and separately a 7-day funding mean is a less noisy
forecast of next week's funding than a 3-day mean. Two independent arguments, neither of which
required seeing a result for my own design — I have none.

The stride and the soft threshold are **genuine widenings of the declared surface**, introduced
in the refinement phase in response to the measured cost structure. I would rather record that
than pretend the surface is still 144 cells. Counting stride ∈ {3, 6, 9} as considered and τ as
set at a single value rather than searched: **if this is nominated, the trial count I claim is
N = 432, not 144 and certainly not 1.**

The carry-demean-before-divide (§2a) is not counted as a knob. It has one defensible ordering
and the other one silently embeds a vol tilt; that is a defect fix.

**Known weaknesses, unchanged from the sealed thesis.** The book is structurally short momentum
— shorting the highest-funding names is shorting the crowd, and in a sustained trending tape
that is a losing side for a long time before it is a winning one. Funding is cap-censored
exactly in the tail where dispersion should be loudest, and at 8h resolution I see a capped
print without knowing it was capped. 8h bars see a cascade's round trip, not its excursion.
None of these have a fix in this dataset and I am not pretending otherwise.

---

## 6. Compliance and failure-mode notes

- **Interface.** `build_strategy()` → object with `target_weights(context, *, seed)`. Returns a
  `dict[str, float]` over `context.eligible_symbols`, or `None` to hold. Enforced in code:
  `sum|w| ≤ 0.99`, `|sum w| ≈ 0` by construction, `|w_i| ≤ 0.095`. The per-symbol cap is applied
  *after* the final centring and the gross scale only ever moves down, so both caps are hard.
- **Panel alignment.** Every cross-symbol structure is keyed on timestamps, never on the
  positional `RangeIndex` — the funding panel is pivoted on `funding_time` (int64 ns) and
  dispersion is joined onto `open_time` by `searchsorted`. Bar cadence is inferred from
  `open_time` diffs rather than assumed.
- **No hidden state.** Nothing is cached between decisions; every quantity is recomputed from
  the past-only context. The rebalance clock is the decision boundary counted in whole bar
  intervals since the epoch, in integer arithmetic — no state, no dependence on appended future
  rows, no symbol identity, no price scale. Because one day is exactly three 8h intervals, a
  whole-day calendar shift leaves the rebalance phase unchanged.
- **No look-ahead.** The regression target is realized RV over the *next* `h` bars only for rows
  whose forward window is entirely in the past relative to the decision boundary; dispersion is
  shifted one print before being joined, so it uses funding strictly earlier than the bar it is
  attached to.
- **Banned constructs.** No network, subprocess, filesystem, `eval`/`exec`/`compile`,
  `__import__`, `getattr`/`setattr`, or RNG. `seed` is accepted and unused. No embedded fitted
  parameters or data tables — the only coefficients in the book are fitted at runtime from
  streamed rows.
- **Degenerate paths fail safe and loud, not silent.** If the online fit is unusable the
  forecast falls back to trailing 7-day Garman–Klass variance and **the book still trades**; the
  book never depends on the regression succeeding. During warm-up the declared 63-day history
  screen steps down to the most history the universe actually has, and only then, so the book
  starts at roughly day 10 rather than day 63 — the alternative costs ~8% of `active_bar_fraction`
  outright. `_to_ns` uses `is_datetime64_any_dtype` rather than `np.issubdtype`, which raises on
  tz-aware pandas dtypes; that single line is the difference between this book running and it
  holding flat for 808 days while looking like a strategy with no edge.

**Not verified by execution.** This phase has no shell, so the candidate has been reviewed by
reading, not run. The specific risks I could not discharge are the exact dtype of `funding_time`
and `open_time`, and whether `bars` frames are cumulative (as t01's 22-bar warm-up strongly
implies) rather than fixed-length windows. The rebalance clock was moved onto `decision_time`
precisely so that the second of those cannot silently produce a flat book.
