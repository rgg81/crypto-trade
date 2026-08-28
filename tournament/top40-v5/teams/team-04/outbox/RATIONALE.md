# team-04 — nomination: residual cross-sectional momentum

## 0. What is nominated

`outbox/candidate.py` is **byte-identical to the source that produced trial t02**
(`lane/candidates/refinement-candidate.py`). Not a descendant of it, not a tidied version of it —
the same file. Every number in §4 below was measured on exactly this code. I have deliberately not
edited it, because an edit I cannot re-measure turns a measured book into an argued one, and this
lane has no trials left to re-measure with.

| | value |
|---|---|
| Signal | 8h log returns orthogonalised to an equal-weighted market factor via winsorised, half-shrunk rolling beta; cumulative residual scaled by its own residual vol |
| Lookback `L` | blended equal-weight over 45 and 90 bars (15 and 30 days) |
| Hold `H` | 63 bars (21 days), as overlapping Jegadeesh–Titman formation lags |
| Beta window / shrinkage | 270 bars (90 days) / `λ = 0.5` |
| Book | linear-in-rank across the full surviving cross-section, projected orthogonal to `{1, β̂}` |
| Universe | eligible symbols, top-150 by trailing median quote volume, ≥66 clean trailing bars |

**Why this one rather than a better one.** I have two packets. t01 is the organizer seed and t02 is
this book. t02 was admitted with zero failed gates. Anything I nominated instead would be an
unmeasured book whose gate outcomes I would be *predicting*, and the three gates the seed failed
were precisely the ones nobody predicts well. The guidance says qualification is a bar on structure
and cost and that a robust book I can explain beats a fragile one I cannot. This is the book I can
explain, and it is the only one in this lane that has cleared the bar.

---

## 1. The mechanism

A dollar-neutral winners-minus-losers book built on **total** returns is not a bet on relative
performance. After an up-move the winners are the high-beta names, so the book is implicitly long
beta; after a down-move it is implicitly short beta. Blitz–Huij–Martens found roughly half of
conventional momentum's risk comes from these conditional factor exposures, and Huij–Lansdorp state
why they are not paid for: the tilt only earns if past factor returns predict future factor returns,
and they essentially do not. It is risk without compensation.

Crypto is the extreme case — pairwise correlations among liquid perps near 0.9, one dominant factor,
wide beta dispersion (a memecoin perp and BTCUSDT are not the same instrument). So the disguised-beta
fraction of a raw crypto momentum book should be *larger* than in equities. Stripping it is where the
mandate earns its keep.

What is left is coin-specific continuation, with three channels: fragmented attention over 300–500
continuously churning contracts, so contract-level information diffuses slowly through a
retail-dominated holder base (Liu–Tsyvinski–Wu locate crypto momentum specifically in the
large-and-liquid group that the Binance USD-M universe *is*); disposition-driven early supply into
winners; and leverage-constrained trend-chasing demand expressed through perps (Schmeling–Schrimpf–
Todorov). That flow does not spread evenly across the index — it lands on whatever token is the
current narrative, which is to say on the residual.

**There is a second, sharper reason residualisation belongs here, and it is a cost argument rather
than a risk argument.** In a raw-return momentum book, when the market factor moves, every high-beta
contract moves together and the cross-sectional ranking reshuffles. Those rank changes are forced
trades carrying no information, because past market returns do not predict future ones. In a universe
with correlations near 0.9, a raw crypto momentum book pays ~7.5 bps per unit of turnover to churn on
the one component of return it has no view on. Removing `β̂ · m` before ranking removes exactly that
churn. This is the part of the mandate that pays for itself at the gate, and §4 is the measurement.

**Holding is implemented statelessly.** No state may persist across decisions, and `DecisionContext`
exposes no current position, so ordinary hysteresis ("don't trade unless the target moved far
enough") is unavailable — it needs memory, and memory is banned and caught by the replay-determinism
check. Instead of smoothing the *transition*, the *target itself* is a smooth functional of past-only
data: the formation signal is recomputed as of `t, t−1, … t−62` and the resulting rank vectors are
averaged. Then `w_t − w_{t−1} = (1/H)·(v_t − v_{t−H})`, so per-decision turnover is bounded by
`2·gross/H`. This is the textbook implementation of a holding period, it is a pure function of the
streamed rows, and it needs no memory. It is also why the lag set must be **consecutive** — a
subsampled set `{0, s, 2s, …}` does not telescope and delivers no turnover reduction at all.

Two supporting choices. **Linear-in-rank weights**, not deciles: a bucket boundary produces a jump in
weight every time a name crosses it, a linear map produces a change proportional to the rank change;
Blitz et al. separately report that residual momentum is *less* concentrated in the extremes than
conventional momentum, which is an independent reason to spread the book. **Vol-scaled residuals**:
ranking on `Σe/sd(e)` rather than `Σe` stops high-vol names monopolising both tails, where raw
cumulative residuals would rank almost the same as raw volatility.

I set no volatility target. The organizer owns the ex-ante risk unit; `GROSS_TARGET = 1.0` is a shape,
not a risk statement. This forecloses the Daniel–Moskowitz dynamic-momentum remedy for momentum
crashes, and I absorb that crash risk rather than smuggle in risk timing.

---

## 2. Who is on the other side

- **Long leg.** The disposition-effect holder taking profits in a winner before the information has
  finished diffusing, and the market maker who needs inventory compensation to stand short a contract
  with one-sided flow.
- **Short leg.** The levered retail long in a falling perp who averages down and is closed by the
  liquidation engine rather than by choice. Perps concentrate that population because they are the
  cheapest leverage in the asset class — 20–100× is routine.
- **On my side, and a hazard for it.** The trend-chasing leveraged flow the BIS paper identifies is
  what makes continuation continue. It is a tailwind and the crash mechanism at once: the failure mode
  is being last into a crowded narrative. Removing the market factor removes the index-level part of
  that risk and none of the contract-level part.
- **Why it is not arbitraged away.** The short leg is barely executable on spot for most of this
  universe — Liu–Tsyvinski–Wu concede the point and fall back to shorting Bitcoin. Perps dissolve it:
  uniform specs, uniform 8h funding, one margin pool, no locate. Meanwhile the institutional capital
  deployed in crypto sits overwhelmingly in basis and funding carry, not in cross-sectional relative
  value across 150 alt perps (BIS WP 1087 on limits to arbitrage).
- **What the premium compensates.** An ugly tail. Grobys–Shahzad argue the realised variance of crypto
  momentum follows a power law whose population moments may not be defined; if they are right, every
  variance-based statistic below — including the Sharpe ratios — is a number without a clean
  population counterpart. I restate that caveat rather than drop it.

**Funding.** Part of the return, not a nuisance. By the BIS mechanism I expect to *pay* funding on the
long leg and *receive* it on the short leg; the net sign on a dollar-neutral book I refuse to guess at.
Funding enters no signal, filter or weight — tilting by it would be drift into the carry family.
Neither packet decomposes funding by leg, so this remains an untested prediction, not a result.

---

## 3. What the two packets established about cost — the measurement the nomination rests on

Both packets pin the same constant. Reading cost per multiple off the spread between the 1× and 3×
return lines:

| | t01 (seed) | t02 (this book) |
|---|---|---|
| annualised turnover | 90.10 | 29.31 |
| implied gross return | 8.03% | 8.72% |
| implied cost @1× | 6.43% | 2.29% |
| **cost per unit turnover per multiple** | **7.13 bps** | **7.81 bps** |
| gross edge bps / turnover | 9.90 | 30.37 |
| cost share of positive gross | 0.758 | 0.247 |
| triple-cost annualised return | −11.24% | **+1.85%** |

The venue charges roughly 7–8 bps per unit of turnover per cost multiple, so **a book survives triple
cost only if its gross edge exceeds ~23 bps per unit of turnover.** The seed earns 9.9 and cannot pay
for itself; it is otherwise a well-formed portfolio (breadth 28.5, gross 0.98, 50/50 exposure, no
ruin). This book earns 30.4.

Note the row that matters most: **the seed's extra 61 turns a year bought no extra gross return.**
Gross was 8.03% at turnover 90 and 8.72% at turnover 29. That is the churn-is-uninformative claim of
§1 showing up as a number. I flag the limit of it honestly — t01 is the organizer's signal, not mine
at high turnover, so this is a suggestive across-strategy comparison, not a controlled sweep of `H`.

Headroom, stated as a falsifiable quantity: at 7.81 bps/turnover the triple-cost line turns negative
once edge density falls below 23.4, so **gross edge can decay ~23% from its visible-window value
before this book stops surviving triple cost.** That is the margin I am nominating on, and it is not
large.

Other gate-relevant t02 metrics, all passing: median effective breadth 27.6, mean gross exposure
1.000, long/short exposure share 49.99/50.01, active bar fraction 1.00, max drawdown 13.8%, no ruin,
double-cost Sharpe 0.441.

---

## 4. Preregistered falsifier ledger — verdicts, including the ones I cannot give

The thesis committed to reporting all verdicts before nominating, whatever they say. Two fired
nothing, one is partial, two are **unevaluated**, and I am not going to let the unevaluated ones read
as passes.

| | verdict |
|---|---|
| **F1** — the edge was beta all along | **Does not fire, on one arm only.** F1 is a conjunction: net Sharpe ≤ 0.5 *and* median across the 96 residualised cells ≤ 0.5. Observed net Sharpe is 0.653, so the first conjunct is false and F1 cannot fire. But the configuration measured is not the sealed *primary* point (`H=63`, blended `L`, not `H=9, L=21`), and I never ran the 96-cell grid. This is a weaker "does not fire" than the test contemplated. |
| **F2** — residualisation is decorative | **Not evaluated. This is the material gap in the nomination.** It requires a `λ = 1` arm and a residual-vs-raw signal correlation, and I ran neither. I therefore **cannot demonstrate that residualisation is doing work** rather than being a relabelling of plain cross-sectional momentum. The §1 turnover argument predicts it does; the prediction is untested against the null. |
| **F3** — the betas are noise | **Not evaluated.** The packet reports no ex-post beta to the market factor. What I can say is narrower: beta-neutrality is imposed *exactly* on `β̂` by orthogonal projection, so any ex-post exposure is pure estimation error in `β̂` — which is precisely the Sila–Mark–Weber–Kristoufek failure mode, and `λ = 0.5` is the declared hedge against it. Realised exposure share is 49.99/50.01, which confirms dollar-neutrality and says nothing about beta. |
| **F4** — the density fix does not fix density | **Does not fire.** Density went 9.90 → 30.37 against a ~23 bps bar. |
| **F5** — the turnover collapsed below the band | **Does not fire.** 29.31 was admitted with no turnover gate failure. The band therefore contains [29.3, 90.1], and I still do not know where its floor is. |

**On F2, one precision the thesis got slightly wrong and I want on the record.** The thesis claimed
the null is nested exactly in this code at `BETA_SHRINK = 1.0`. That is exact for the *unscaled*
signal — with `β̂ ≡ 1`, `Σe = Σr − Σm` and `Σm` is common to every contract, so it cannot alter a
cross-sectional ranking. It is *not* exact for the vol-scaled signal actually nominated, because
`sd(r_i − m)` is symbol-specific. At `λ = 1` this book collapses to market-demeaned, residual-vol-
scaled momentum, which is close to but not identical to plain momentum. The knob is still there and
the comparison is still one line of code for anyone who wants to run it — but "the null is nested
exactly" was an overstatement.

---

## 5. What would falsify the nomination going forward

1. **Triple-cost return ≤ 0 on the sealed blocks.** Given §3, this means sealed-window edge density
   fell below ~23 bps — a >23% decay in gross edge. Consequence: residual momentum has no cost-viable
   expression at 8h decision frequency in this universe, and the honest response is retirement, not a
   further search along `H`.
2. **Ex-post |β| > 0.15 to the equal-weighted market factor.** F3. The book is still partly a levered
   index position, the mandate has failed on its own terms whatever the Sharpe says, and the fallback
   is `λ = 1` — dollar-neutrality only, as an honest statement of what is estimable here.
3. **A `λ = 1` arm matching or beating this on density and Sharpe.** F2. Then the residualisation is
   decorative and plain cross-sectional momentum was the right nomination. I would rather this be
   found and reported than left unmeasured and implied away.
4. **Turnover materially outside ~15–45 on sealed blocks.** A construction miss in the overlapping-lag
   machinery, not evidence about the mandate, and I would label it as such.
5. **Positive fold fraction staying near 0.4.** t01 and t02 both report 0.40, so with a 0.653 Sharpe
   the return is concentrated in a minority of folds. If that persists, the book is a few episodes
   rather than a premium, and the Grobys–Shahzad caveat governs the reading of every Sharpe here.

The mandate's own falsifier remains the one that matters: **if the edge disappears once the market
factor is removed, the signal was market beta all along.** This candidate runs only the residualised
arm and cannot settle that by itself.

---

## 6. The statistical claim I am *not* making

The thesis committed: *"I will not claim the mandate is confirmed unless the deflated Sharpe —
deflating for the 120 distinct strategies declared in §4 — remains positive."* The refinement trial
widened the declared surface to 200 configurations and I hold to that larger number.

By that standard, **the mandate is not confirmed, and I am not claiming it is.** A 0.653 annualised
Sharpe over 808 days is `t ≈ 0.97` — not distinguishable from zero at any conventional level before
deflation, and comfortably inside the expected maximum of a 200-configuration search after it. The
triple-cost Sharpe of ~0.18 is weaker still.

Two things keep that from being a reason to retire:

- **I did not perform the search.** I ran one configuration of the declared 200, plus the seed. The
  200 is a bound on selection bias I could have incurred, not bias I did incur; the realised
  selection is one draw, not a maximum over 200. I report the conservative bound anyway because that
  is what preregistering a surface is for.
- **The result I am actually leaning on is not the Sharpe.** Turnover, edge density and cost share are
  estimated from every bar of trading activity rather than from a mean return, and they are an order
  of magnitude better identified than the alpha. §3 is a measurement about the *structure* of the
  book. The gates are structural, and that is the bar this nomination is built to clear.

Ten of twelve feedback trials are unspent. That was a choice: with the cost constant pinned and the
structural design confirmed, further trials would have moved parameters against a development Sharpe
that is already statistically empty, which is the hill-climbing the rules warn buys very little. I
would rather nominate a book whose one measurement I trust than a book with eleven.

---

## 7. Construction and compliance notes

- **Constraints.** Weights are projected orthogonal to `{1, β̂}`, so `Σw = 0` and `Σwβ̂ = 0` hold
  before capping; then normalised to gross ≤ 1.0 and clipped to `|w| ≤ 0.10`, with a net backstop at
  `0.20·gross` against the 0.25 limit. Only symbols drawn from `eligible_symbols` are ever emitted.
- **Panel alignment.** Built on `open_time` via `pd.DataFrame({sym: series}).sort_index()`, never on
  the positional `RangeIndex` — the silent-empty-book failure mode RULES describes at length. Symbols
  of unequal history contribute `NaN` outside their own range and are handled by an explicit trailing
  run-length filter, not by dropping rows.
- **No state.** `__slots__ = ()`; every decision is refitted from the streamed past-only rows. No RNG,
  no clock, no filesystem, no dynamic execution, no fitted artifacts, no embedded data.
- **Invariance.** `decision_time` is never read → calendar-shift equivariant. No symbol is named and
  ranks are tie-averaged → order- and pseudonym-invariant. All computation is on log returns and on
  volume *ranks* → magnitude-scale equivariant. Weights are smooth in the scores with no thresholds →
  small perturbations move the book slightly rather than discontinuously.
- **Degenerate decisions return `None`, not `{}`.** If the cross-section is momentarily too thin,
  holding is correct; `{}` would liquidate the whole book and rebuild it next bar, which is exactly
  the turnover this design exists to avoid.
- **Exclusions still honoured.** No funding signal, no volume or taker-buy conditioning in the signal
  (volume enters once, in eligibility), no regime switches or crash filters, no multi-factor
  residualisation, no asymmetric legs, no hand-curated universes, and no volatility targeting of any
  kind.
- **Declared deviations from the sealed surface** are unchanged from the refinement rationale §5:
  `H = 63` is one new level on the declared `H` axis; `L` is blended over two declared levels rather
  than selected; the return basis is price log-return rather than price-plus-funding; the history
  requirement is graded rather than hard; and one beta per decision is applied to all formation lags.
  These are counted in the 200.
