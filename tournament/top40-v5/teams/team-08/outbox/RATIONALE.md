# team-08 — nomination: slow-ladder per-contract time-series trend, day-averaged book

**Family:** time-series trend. **Mandate:** the CTA transplant — per-contract, volatility scaled,
multiple lookbacks. **Phase:** decision. **Evidence:** `lane/feedback/t01.json` (unmodified
organizer seed), `lane/feedback/t02.json` (slow ladder, admitted), and the sealed preregistration
in `lane/scouting/THESIS.md`.

---

## 1. What I am nominating, and why it is not the packet I already passed

I am nominating the t02 mechanism with two changes, neither of which is aimed at Sharpe. t02 is
admitted and I could nominate it verbatim. I am not, and the reason is specific rather than
temperamental.

The seed failed exactly three gates — `gross_edge_density`, `cost_share`, `survives_triple_cost` —
and t02's remaining margin is thinnest on exactly those three. Its triple-cost annualised return is
**+2.6%**; its density is **28.7 bps** against a triple-cost break-even of **22.3–24.0 bps**. Those
gates are re-enforced on sealed blocks, on shorter samples than the 808 days I can see, and a
margin of 1.2× on the gate that killed the seed is not a margin I want to carry into a block I
cannot inspect. The two changes below spend a small and *bounded* amount of gross Sharpe to roughly
double that margin. Both sit inside the sealed parameter surface.

---

## 2. The one thing here that is measured rather than assumed

Two packets identify the cost schedule twice each, and they close:

| | t01 (seed) | t02 (slow ladder) |
|---|---|---|
| implied 1× cost `(net − triple)/2 / turnover` | **7.43 bps** | **8.00 bps** |
| identity `density × turnover × cost_share` vs implied cost | 0.0979 vs 0.0970 | 0.0385 vs 0.0410 |
| annualised turnover | 130.51 | 51.32 |
| gross return `net + cost` | 0.1875 | 0.1490 |
| **gross Sharpe** | **1.559** | **1.314** |
| net Sharpe | 0.780 | 0.961 |

Two consequences, both load-bearing.

**(a) The refinement's cost model was right.** It predicted a turnover cut of 2.45× from restricting
the ladder to the declared `SLOW(5–8)` window, on the argument that a rung-*L* z-score has per-bar
innovation `√(2/L)` so the fast four rungs carry ~80% of the position innovation. Realised: **2.54×**
(130.51 → 51.32). A four-percent miss on an ex-ante structural prediction is the strongest evidence
I have that I understand where this book's turnover comes from, and it is what licenses the second
change below — which is a prediction of the same kind, from the same model.

**(b) The cost of slowing down is now measured, not guessed.** Cutting turnover 2.54× cost **16% of
gross Sharpe** (1.559 → 1.314). Fitting `S_gross ≈ a + b·log(turnover)` through those two points
gives `b = 0.263`, and the net-Sharpe optimum of that curve at 1× cost sits at **turnover ≈ 48** —
which is where t02 already is. So t02 is close to optimal *at 1× cost*. The same curve's optimum at
**3×** cost sits far slower. Since the tournament charges 1×, 2× and 3× independently and says
plainly that "a book that only survives at 1× is not a book," the relevant optimum is not the 1× one.

---

## 3. The two changes

### 3.1 The ladder is sampled at √2 inside the same declared span — turnover-neutral

`LADDER = (45, 64, 90, 127, 180, 254, 360)` bars ≈ {15, 21, 30, 42, 60, 85, 120} days. Same
endpoints as the declared `SLOW(5–8)` window; the three new rungs are interpolations of it.

| | mean rung innovation `1/√L` |
|---|---|
| declared SLOW-4 {45, 90, 180, 360} | 0.09543 |
| nominated DENSE-7 {45, 64, 90, 127, 180, 254, 360} | 0.09403 |

**−1.5%.** This is turnover-neutral by construction, so it is not a cost move — it is a
variance-reduction move. **It cannot express hindsight:** neither packet contains a per-rung
decomposition, so I have no evidence about which lookback worked and could not have fitted this if
I wanted to. What it removes is the possibility that a quarter of the book rests on one lookback
that happened to land well. It is also a more honest reading of "multiple lookbacks" than four
rungs at 2× spacing.

### 3.2 The submitted book is the mean of the last three bars' books — the real cost move

The book at bar *t* is the equal-weighted mean of the books this identical construction would have
formed at bars *t*, *t−1*, *t−2*. On an 8h clock that is **one day**, and it is the declared Tier-2
cadence `R = "every 3 bars (daily)"` from THESIS §7.3 — expressed as a running mean rather than as a
discrete schedule.

The continuous form is strictly better than the discrete one for three reasons that matter here:
a discrete daily rebalance is **calendar-anchored** (it would fail calendar-shift equivariance and
target an absolute time of day), it trades in **lumps** three times larger than it needs to, and it
has a **threshold** — the schedule boundary — which is exactly what the small-perturbation stability
check is looking for. The running mean has none of these. Everything in the path from data to weight
remains continuous, which was the governing design constraint identified in the refinement: with no
position exposed in `DecisionContext` and no persistent state permitted, turnover has to be designed
into the signal rather than filtered out afterwards.

**Why it is nearly free.** For a signal whose bar-to-bar innovation is dominated by the newest
return (which it is — that term is common to every rung), a *k*-bar running mean reduces per-bar
position innovation by `1/√k` while leaving the level essentially unchanged, because *k* = 3 is tiny
against a 45–360 bar signal. The organizer's ex-ante risk unit therefore cannot undo it: it is not an
amplitude shrink, it is removal of high-frequency content relative to low-frequency content. The
cost is a mean lag of **one bar** on a signal whose lag-1 autocorrelation is ≈ 1 − 1/L ≈ 0.978 at the
*fastest* rung. A 15–120 day signal has no business re-trading three times a day; the two extra
decisions per day are close to pure noise-trading.

The recomputation at *t−1* and *t−2* reads only rows at or before its own anchor bar — its own EWMA
volatility, its own rung returns — so the average is over *past* books and adds no look-ahead. The
funding drag and the universe membership are held at the decision bar, which is information
available at the decision; holding the drag fixed also means it contributes zero turnover.

### 3.3 Everything else is t02 unchanged

Universe N=30 on a 270-bar trailing median of quote volume; EWMA vol at com 180 bars; `tanh`
transform; funding-inclusive signal basis; concentration cap at 3× median; net cap 0.20. These
produced measured breadth 21.87 at pass-fraction 1.0 and a 49.3/50.7 long/short split. I am not
touching what is measured and good.

---

## 4. The mechanism, and who is on the other side

Per contract and nothing else — no cross-sectional rank, no relative strength, no market-wide state
variable, and (per the §0 commitment I bound myself to before seeing data) **no volatility gate, no
drawdown control, no exposure throttle**:

```
z_L,j = (log return over L bars ending at t−j − funding paid over L) / (σ_j · √L)
g_j   = mean over available rungs of tanh(z_L,j)
w_raw = mean over j ∈ {0,1,2} of g_j / σ_j        # inverse-vol, relative weights only
w     = normalise → concentration cap → net cap
```

At a 15–120 day horizon the counterparties are, in descending order of how much of the transfer I
think they explain:

1. **Inventory hedgers.** Miners hedging production, treasuries and foundations hedging holdings,
   recipients of token unlocks, market makers laying off spot flow. They short into strength and buy
   into weakness for reasons unrelated to expected return. This is the classical Moskowitz–Ooi–
   Pedersen risk-transfer story and it is the counterparty best matched to the slow ladder's clock.
2. **Extrapolative demand arriving late.** Liu & Tsyvinski put crypto return predictability at a 1–8
   week horizon with investor attention as the channel. Binance's listing process is itself
   attention-selecting — perps get listed after a narrative catches — so the tradeable cross-section
   is populated with exactly the assets where late extrapolative demand is strongest. Crucially,
   **there is no valuation anchor**: nobody can compute a fair value for a token with no cash flows,
   so the corrective force that kills under-reaction in an equity index has no seat at this table.
3. **The cash-and-carry basis desk.** Long spot, short the perp, structurally short and completely
   indifferent to direction. They are *not* losing this trade — they are being paid by me, in
   funding, by exchange design (Binance's documented default is +0.01% per 8h at zero premium, ≈11%
   a year, longs to shorts, and the exchange takes no fee). This is the one counterparty I can name
   from documentation rather than by inference, and the signal prices it in rather than discovering
   it in the P&L.

**And one I have now abandoned twice.** THESIS §1.3–§1.4(d) argued the more interesting half of the
thesis: that the perpetual's liquidation engine manufactures a fast, mechanical, momentum-aligned
order flow that has no analogue in the CTA literature, and that Shen/Urquhart/Wang's intraday result
names its counterparty. I still believe that transfer is real. t01's packet says it does not clear a
7.4–8.0 bps schedule at 1×, let alone 3×. The slow ladder walked away from it; the daily average
walks further. That is the substance of both refinements and §6 is written so that being wrong about
it stays visible.

---

## 5. Quantified predictions, stated before the packet

Turnover: `51.32 × 0.985 (ladder) × ~0.62 (smoothing, 1/√3 diluted by unsmoothed universe churn)`.

| quantity | t02 (measured) | nominated (predicted) |
|---|---|---|
| annualised turnover | 51.32 | **26 – 40**, central **32** |
| gross edge / turnover | 28.67 bps | **38 – 52 bps** (3× break-even ≈ 24) |
| cost share of gross | 0.262 | **0.15 – 0.21** |
| net Sharpe | 0.961 | **0.95 – 1.10** |
| double-cost Sharpe | 0.621 | **0.72 – 0.85** |
| triple-cost return | +0.0259 | **+0.05 – +0.08** |
| effective breadth | 21.87 | 21 – 24 (averaging three books de-concentrates slightly) |
| long / short share | 49.3 / 50.7 | ≈ 50/50 |

Bracketing the signal cost of smoothing both ways, because that is the number I am least sure of:

- **Central** (lag costs 2% of gross Sharpe → 1.29): net Sharpe 1.06, triple-cost return **+0.070**.
- **Pessimistic** (charge the smoothing the *full* log-turnover penalty measured from deleting rungs,
  `b = 0.263` → gross Sharpe 1.19 — an over-charge, since a one-bar lag does not delete signal the
  way removing four rungs does): net Sharpe 0.96, triple-cost return **+0.058**.

**Under both, 1× net Sharpe is flat against t02 and the triple-cost margin is 2.2–2.7× larger.** That
insensitivity is the whole argument for the trade, and it is why I prefer this book to the one I
already passed with.

---

## 6. What would falsify this

### F-N — the nomination falsifier
The claim is that the last two of every three daily decisions are noise-trading, and that removing
them is nearly free in signal and large in cost. Three discriminating outcomes, all committed now:

- **Turnover lands in 26–40 and net Sharpe holds near 0.96+.** The claim holds; the extra
  intra-day decisions were noise.
- **Turnover falls as predicted but net Sharpe falls with it, proportionally.** Then the 8h clock
  was carrying real information at the slow ladder's horizon, my innovation model is wrong about
  *which* frequencies hold the edge, and the correct reading is that this family's edge in Binance
  perps is more frequency-dependent than a 15–120 day signal has any right to be.
- **Turnover does not fall into range.** Then the residual turnover is not signal-driven — it is
  universe churn, the vol estimate, or the organizer's risk-unit rescale — and my model of this
  book's cost, which correctly predicted 2.54×, has a term missing.

### F-C — the mandate falsifier, as assigned
> If no lookback horizon produces positive average returns per contract, time-series trend does not
> persist in this universe.

**Not breached.** Two packets show gross Sharpe of 1.56 (all eight rungs) and 1.31 (slow four) on 808
days. Some horizon in the ladder is positive. The open question was never whether the premium exists
here; it is whether it survives being paid for, and that is what both refinements have addressed.

### F-A and F-B — preregistered and still unrun, stated plainly
THESIS §6 preregistered F-A (a 1,000-path sign-scrambled block-bootstrap control establishing that
the *sign forecast* adds something above the organizer's imposed risk unit — the test Kim/Tse/Wald's
critique demands) and F-B (standalone per-rung net returns requiring a contiguous positive block of
three adjacent rungs). **Neither is executable.** This phase returns one aggregate metric packet per
trial, not a backtest harness; a bootstrap distribution and a per-rung decomposition cannot be built
from `{net_sharpe, turnover, cost_share, …}`.

I am recording this as an unmet preregistered commitment rather than substituting a weaker test I
*can* run and calling it F-A. The consequence, stated without hedging: **if this book makes money I
am not entitled to claim it for the trend family.** The Kim/Tse/Wald alternative — that the result is
the organizer's imposed risk unit plus an inverse-volatility tilt, with the sign forecast
contributing nothing — remains open and untested. The §0 no-vol-gate commitment is what keeps the
question at least honest: there is no volatility-conditional exposure anywhere in this book, so
whatever it earns, it does not earn from disguised volatility timing.

### On `positive_fold_fraction = 0.4`
t02 turned in 2 of 5 positive folds at a net Sharpe of 0.96, down from the seed's 0.6. I read this as
**preregistered prediction P5 confirming, not as fragility**: P5 said before any data that "performance
should be concentrated in a small number of large-move episodes" and that if it were not, the return
was not coming from trend capture. A convex, lookback-straddle payoff is *supposed* to be lumpy.
Arithmetically it is also unremarkable: at annual Sharpe 0.96 a 162-day fold has expected Sharpe 0.64,
so P(fold > 0) ≈ 0.74 and P(≤ 2 of 5) ≈ 0.12 — inside noise. The seed's higher fold consistency at a
*lower* Sharpe is the same fact from the other side: faster trading spreads P&L more evenly and then
hands it to the cost schedule. **Secondary prediction:** averaging three books tilts toward the
persistent component, so fold consistency should tick up rather than down. If it falls further while
Sharpe holds, that is a sign the return is concentrating into fewer episodes than trend capture
explains, and I would distrust it.

---

## 7. Where this is exposed

- **The turnover band floor is the single named qualification risk.** Evidence establishes only that
  the band contains [51.3, 130.5]. My prediction of ~32 is below anything I have observed to pass. If
  the floor sits above ~32 this book fails a structural gate outright and scores nothing, and the
  trade I made in §1 was the wrong one. I judged this less likely than the triple-cost risk it buys
  down — a floor above 32 would exclude essentially every genuine slow-trend CTA, in a tournament
  that fields a time-series-trend lane and warns at length about cost gates — but it is a real
  binary risk and I am not going to dress it up as anything else.
- **THESIS §3.1 remains the honest failure regime:** a high-realised-volatility, zero-net-drift range.
  Slowing the book does not defend against chop; it lengthens the period over which chop can bleed,
  and inverse-vol sizing shrinks positions *after* the volatility arrives, not before. Owning a
  lookback straddle means paying the premium in whipsaw. That is the trade, not a defect to engineer
  away.
- **THESIS §3.4 is unrepaired and unrepairable.** The CTA result stands on a tripod: small per-market
  Sharpe (~0.4), made investable by aggregating ~67 weakly-correlated markets. Crypto supplies one leg
  at ~0.6 average pairwise correlation. A 30-perp book is not 30 bets; measured effective breadth of
  21.9 flatters what is closer to a handful of independent ones. No choice available in this lane
  restores that leg, and the correct expectation for this family here is therefore modest. A
  development gross Sharpe of 1.31 is well above THESIS §P6's ~0.4 per-market calibration, and P6 said
  in advance to read that as a warning rather than a discovery.
- **Slow trends are market-directional.** The net cap enforces `|net| ≤ 0.20` and *nothing more* — it
  is not a both-sides-used guarantee. That gate is protected only by the cross-section genuinely
  containing both signs, which two packets suggest it does over 808 days but which is not promised bar
  by bar.
- **Survivorship (THESIS §3.7) is untestable from here** and would inflate the long side if present.
  Flagged before data, unresolved, and no strategy choice in this lane repairs it.

---

## 8. Declared deviations from the sealed surface, and the trial count

THESIS §7.5 requires that moving a fixed default be counted and reported rather than quietly amended.
Seven, of which two are forced by the contract and two are new at this phase.

1. **No-trade band `D` not implemented — forced.** §7.1 fixed 0.10 × target weight. A band is a
   position-space control; `DecisionContext` exposes no position and persistent state is forbidden.
   Turnover control moved into signal space, which is what §3.2 is.
2. **Tier-2 knobs used without completing Tier 1 — forced.** §7.3 made Tier 2 contingent on F-A/F-B
   passing and on a Tier-1 grid winner; §7.4 fixed the selection rule. No grid is runnable (§6). Cells
   were selected by mechanism reasoning instead.
3. **Net-exposure cap at 0.20 added.** Not in §7.1. Constraint hygiene mirroring the hard |net| ≤ 0.25,
   applied smoothly by me rather than bluntly by the evaluator.
4. **Funding drag approximated** by a trailing mean rate scaled to a per-bar drag, held fixed across
   the three smoothing lags, rather than an exact per-rung sum.
5. **Minimum history fixed at 202 bars.** §7.1 said "sufficient history" without a number; 202 gives
   200 usable observations at every smoothing lag, so all three books rest on the same ladder depth.
6. **NEW — ladder densified to √2 spacing inside the declared span.** §7.1 fixed the rungs at 2×
   spacing. Same endpoints, seven rungs instead of four, turnover-neutral (§3.1). Counted as a move of
   a fixed default. It is an averaging move over horizons, not a selection among them, and no per-rung
   evidence exists that could have informed it.
7. **NEW — cadence `R = daily` implemented as a running mean rather than a discrete schedule.** The
   *value* is the declared Tier-2 one; the continuous implementation is the deviation, taken because
   the discrete form is calendar-anchored and threshold-based (§3.2).

**Trial count.** The declared surface is 81 cells (§7.5). Charged trials actually spent: t01 (the
organizer seed, not mine and not in the count) plus **two of my own** — t02 and this nomination. Two
configurations drawn from an 81-cell declared space, each selected by a stated mechanism argument
rather than by grid search, and each with its structural prediction written down before the packet
returned. Both predictions were quantitative; the one that has been checked (2.45× predicted, 2.54×
realised) came in within 4%. That is the deflation argument, and it is a stronger one than a higher
development Sharpe would have been.
