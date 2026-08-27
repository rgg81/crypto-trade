# team-04 — Residual Cross-Sectional Momentum (discovery candidate)

This is the **pre-registered primary configuration** of `lane/scouting/THESIS.md` §4.1, implemented
without additions. No parameter has been chosen after seeing a result, because no result has been
seen: there is no feedback packet in this lane yet. The phase guidance asks for the honest simple
version, and the honest simple version of this mandate is the sealed primary point.

| Knob (THESIS.md §4.1) | Value here |
|---|---|
| Beta window `W` | 90 days (270 bars at 8h) |
| Beta shrinkage `λ` | 0.5 |
| Momentum lookback `L` | 7 days (21 bars) |
| Hold `H` | 3 days (9 bars), as an overlapping portfolio |
| Signal standardisation `s` | residual-vol-scaled |

One trial of a declared 120.

---

## 1. The mechanism

A dollar-neutral winners-minus-losers book built on **total** returns is not a bet on relative
performance. After an up-move the winners are the high-beta names, so the book is implicitly long
beta; after a down-move it is implicitly short beta. Blitz-Huij-Martens showed roughly half of
conventional momentum's risk comes from these conditional factor exposures, and Huij-Lansdorp state
why they are not paid for: the tilt only earns if past factor returns predict future factor returns,
and they essentially do not. The exposure is risk without compensation.

Crypto is the extreme case. Pairwise correlations among liquid perps run near 0.9, one factor
dominates the variance, and beta dispersion across the perp universe is wide — a memecoin perp and
BTCUSDT are not the same instrument. So the disguised-beta fraction of a raw crypto momentum book
should be *larger* than in equities. Stripping it is where the mandate earns its keep.

What remains is coin-specific continuation, and the thesis names three channels for it: fragmented
attention over a wide, fast-rotating universe (Liu-Tsyvinski-Wu find crypto momentum concentrated in
the larger, liquid names — precisely the Binance USD-M subset); disposition-driven early supply into
winners; and leverage-constrained trend-chasing demand expressed through perps specifically
(Schmeling-Schrimpf-Todorov). That flow does not spread evenly across the index — it lands on
whatever token is the current narrative, which is to say on the residual.

**Implementation, in the order the code runs it.** Universe: eligible symbols screened to the top
150 by trailing 30-day median quote volume — the single place volume is permitted to enter (§4.3).
Market factor `m_t`: the equal-weighted cross-sectional mean of 8h log returns; no market-cap data
exists here, so a cap-weighted factor is not constructible, and no symbol is named in the code.
Beta: OLS on `m` over the trailing 90 days, winsorised to [−1, 3] and shrunk halfway to 1.0 — Sila
et al. find crypto betas materially less predictable than equity betas, and shrinkage is their
remedy, not mine. Residual: `e_it = r_it − β̂_i · m_t`. Signal: the cumulative residual over the last
7 days divided by its own standard deviation. Weights: cross-sectional rank z-score, then projected
onto the orthogonal complement of `{1, β̂}` so that `Σw = 0` **and** `Σ w β̂ = 0` hold together.

That last projection is a separate act from residualising the signal, and the mandate needs both: a
book ranked on residuals can still carry net beta if the residual winners happen to be the
high-beta contracts.

**Two implementation choices worth flagging, both driven by `RULES.md` rather than by taste.**

*Horizons are declared in days and converted to bars from the observed median bar spacing.* The
thesis assumes 8h funding-aligned bars. If the runner streams something else, hard-coded bar counts
would silently trade a 3-day lookback wearing a 7-day label. Deriving the spacing costs nothing and
removes a whole class of silent misreading — the failure mode `RULES.md` warns is expensive because
it scores as a book with no edge rather than one that never ran.

*The 3-day hold is stateless.* No state may persist across decisions, so the hold is built as a
Jegadeesh-Titman overlapping portfolio: the rank score is averaged over the H formation windows
ending at t, t−1, … t−H+1. That is the same book as rebalancing a third of the capital each day, it
implements the declared `H` exactly, and it needs no memory. It is also the turnover control — a
raw every-bar rebalance on a 21-bar signal would push cost share against the gates well before the
3× cost check.

I set no volatility target. The organizer owns the ex-ante risk unit; `TARGET_GROSS = 0.98` is a
shape, not a risk statement. This forecloses the Daniel-Moskowitz dynamic-momentum remedy for
momentum crashes, and I absorb that crash risk rather than smuggle in risk timing.

## 2. Who is on the other side

- **Long leg.** The disposition-effect holder taking profits in a winner before the information has
  finished diffusing, and the market maker who needs inventory compensation to be short a name with
  one-sided flow.
- **Short leg.** The levered retail long in a falling perp who averages down and is closed by the
  liquidation engine rather than by choice. Perps are where that population is most concentrated,
  because perps are the cheapest leverage in the asset class — 20–100× is routine.
- **On my side, and therefore a hazard.** The trend-chasing leveraged flow the BIS paper identifies
  is what makes the continuation continue. It is a tailwind and a crowding risk at once: the failure
  mode is being the last participant into a crowded narrative, which is the momentum-crash
  mechanism. Removing the market factor removes only the index-level part of that.
- **Why it is not arbitraged away.** The short leg is barely executable on spot for most of this
  universe — Liu-Tsyvinski-Wu concede the point and fall back to shorting Bitcoin. Perps dissolve
  it: uniform specs, uniform 8h funding, one USDT margin pool, no locate. And the institutional
  capital that is deployed in crypto sits overwhelmingly in basis and funding carry, not in
  cross-sectional relative value across 150 alt perps.
- **What the premium is compensation for.** An ugly tail. Grobys-Shahzad argue the realised variance
  of crypto momentum follows a power law whose population moments are not statistically defined. If
  they are right, a Sharpe ratio on this family is a number without a population counterpart. I do
  not have the sample to adjudicate that, and I will restate the caveat rather than drop it.

Funding is part of the return, not a nuisance. By the BIS mechanism I expect to **pay** funding on
the long leg (winners are where trend-chasing longs crowd in) and **receive** it on the short leg.
The net sign on a dollar-neutral book is an empirical question I refuse to guess at — it is a
required diagnostic (§4.4), not an assumption. Funding enters no signal, filter or weight; tilting
by it would be drift into the carry family, which §4.3 excludes.

## 3. What would falsify this

Sealed before any data was mounted, and reported whatever the verdicts say.

**F1 — the edge was beta all along.** Fires if the residualised book has net Sharpe ≤ 0.5 at the
primary configuration **and** the median net Sharpe across all 96 residualised grid points is ≤ 0.5.
The median condition exists so one lucky cell cannot save the mandate. *Consequence:* the family
does not survive in this universe; nominate the unmodified organizer seed and report the
falsification as the lane's result.

**F2 — residualisation is decorative.** Fires if the mean per-rebalance cross-sectional Spearman
correlation between the residual signal (λ = 0.5) and the raw signal (λ = 1) exceeds 0.95, **and**
the median net Sharpe of the residualised cells does not beat the λ = 1 cells by at least 0.2. This
is the outcome Liu-Tsyvinski-Wu point at: near-zero R² of the raw momentum long-short on the coin
market factor at short horizons means there may be almost no beta in the book to remove.
*Consequence:* report that residualisation is not distinguishable from plain cross-sectional
momentum here, and nominate the simplest cell, λ = 1. That costs the mandate's distinctiveness, and
I would rather pay it than dress plain momentum in residual clothing.

The null is **nested inside this code**, deliberately. Set `BETA_SHRINK = 1.0` and `β̂ ≡ 1` for every
contract; because `Σm` is then common to every symbol it cannot alter a cross-sectional ranking, so
the book collapses *exactly* to plain cross-sectional momentum with dollar-neutrality. F2 can
genuinely fire.

**F3 — the betas are noise.** Fires if the ex-post realised beta of the book to the equal-weighted
market factor exceeds |β| > 0.15 over the development window. This is the Sila et al. failure mode
made concrete: if ex-ante neutralisation leaves material ex-post exposure, the book is still partly
a levered index position and the mandate has failed on its own terms even with a healthy Sharpe.
*Consequence:* report it and fall back to λ = 1, dollar-neutrality only — an honest statement of
what is actually estimable in this market.

**Not firing is not confirmation.** I will not claim the mandate is confirmed unless the Sharpe
deflated for the declared **120 distinct strategies** remains positive.

## 4. What I want back from this trial

Beyond the standard packet, the diagnostics that decide the next move: realised ex-post beta to the
market factor (F3); turnover and cost share, since the overlapping-hold construction is the only
turnover control in the book and the 3× cost gate is where it will be tested first; effective
breadth and both-sides-used, which the full-cross-section rank weighting should satisfy comfortably;
and the worst peak-to-trough drawdown against the market factor's path over the same window — the
Daniel-Moskowitz panic-state check.

If the book turns out to be flat or near-flat for long stretches, the first thing to suspect is not
the signal but the eligibility screen: at the declared window this candidate wants a clean aligned
history of roughly 97 days per contract before it will trade a name.

**One documented degradation path, stated up front rather than discovered later.** If fewer than 12
screened contracts have that full clean history — early in the window, or if the runner's warm-up
history is short — the code retries once on the shortest usable window, which floors the beta
estimate at 45 bars (~15 days) instead of 270. This is a data-availability fallback, not a searched
knob: it is deterministic, it applies uniformly, and it exists only because the alternative is
holding nothing at all and scoring as a book with no edge rather than one that never ran. But a
45-bar beta is a materially noisier beta, which is exactly the Sila et al. failure mode, so if the
packet shows the book trading during a stretch where most contracts are young, F3's realised-beta
number should be read as a verdict on the fallback and not on the mandate. If that turns out to be
the bulk of the window, the honest next trial is to raise the history requirement and accept a
smaller universe, not to keep the fallback and call the result residual momentum.
