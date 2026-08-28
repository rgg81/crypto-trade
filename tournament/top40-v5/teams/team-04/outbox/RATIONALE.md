# team-04 — residual cross-sectional momentum · refinement candidate

## 1. What t01 actually said

t01 was the unmodified organizer seed, so it carries no information about my signal. It carries a
great deal of information about **the venue's cost structure**, and that is what I designed against.

The three failed gates reconcile to a single number:

| from the packet | value |
|---|---|
| `annualised_turnover` | 90.10 |
| `gross_edge_bps_per_turnover` | 9.90 |
| `cost_share_of_positive_gross` | 0.758 |
| `triple_cost_annualised_return` | −0.1124 |

Gross return ≈ `90.10 × 9.90bps` = 8.92%. Cost at 1x ≈ `0.758 × 8.92%` = 6.76%, i.e.
**7.50 bps per unit of turnover per cost multiple**. Verify against the packet's own triple-cost
line: `(9.90 − 3 × 7.50) bps × 90.10 = −11.3%` versus the reported −11.24%. The model closes.

So the gate is not a preference, it is an inequality:

> **A book survives triple cost only if its gross edge exceeds ~22.5 bps per unit of turnover.**

The seed earns 9.90. It needs 2.3x more. Nothing else was wrong with it — breadth 28.5, gross
exposure 0.98, long/short exposure 49.99/50.01, participation 1.0, no ruin. It is a well-formed
portfolio that cannot pay for itself.

The decisive property: `gross_edge_bps_per_turnover` is **scale-invariant**. The organizer's
ex-ante risk unit multiplies both gross return and turnover by the same factor, so leverage cannot
move this ratio, and neither can anything else about position sizing. The only lever is the ratio
itself. That is why this is a design problem, not a parameter problem.

## 2. The design change

The seed is a fast ranker: 90 turns a year against a signal worth 9.9 bps a turn. I am not tuning
it down — I am changing what generates turnover in the first place. Four structural choices, all
aimed at the numerator/denominator ratio rather than at Sharpe.

**(a) Residualisation is a turnover argument, not only a risk argument.** This is the part of the
mandate that pays for itself here, and it is the reason I think the mandate and the failed gate
point the same way. In a raw-return momentum book, when the market factor moves, every high-beta
contract moves together and the cross-sectional ranking reshuffles. Those rank changes are *forced
trades that carry no information*, because past market returns do not predict future market returns
(Huij–Lansdorp). A raw crypto momentum book — in a universe with pairwise correlations near 0.9 —
is therefore paying 7.5 bps a unit to churn on the one component of return it has no view on.
Stripping `β̂ · m` out of the return before ranking removes exactly that churn. Residual momentum
should show up as *higher edge density*, not merely as lower beta.

**(b) Overlapping formation lags (Jegadeesh–Titman), which is the only stateless way to hold.** The
natural cost fix is hysteresis: don't trade unless the target has moved far enough. I cannot do
that. It requires knowing my current position, and `DecisionContext` exposes none, while caching my
own last book is persistent state — banned outright and caught by the replay-determinism check.

So instead of smoothing the *transition*, I make the *target itself* a smooth functional of
past-only data. At each decision I recompute the formation signal as of `t, t−1, … t−(H−1)` and
average the resulting rank vectors. Then

```
w_t − w_{t−1} = (1/H) · (v_t − v_{t−H})
```

Turnover per decision is bounded by `2·gross/H` and is typically far below it. This is the textbook
implementation of a holding period H, it is a pure function of the streamed rows, and it requires no
memory at all. It is also why the lag set must be **consecutive**: a subsampled lag set
`{0, s, 2s, …}` does not telescope and delivers no turnover reduction whatsoever.

**(c) Smooth weights.** Linear-in-rank across the whole surviving cross-section, not decile buckets.
Decile boundaries generate a jump in weight every time a name crosses one; a linear rank map
generates a change proportional to the rank change. Under the plausible model that expected return
is roughly linear in rank, linear weights also *dominate* convex (tail-concentrated) weights on
density: cubic rank weights raise gross edge per unit gross by ~20% while doubling turnover. Blitz
et al. report that residual momentum is specifically *less* concentrated in the extremes than
conventional momentum, which is an independent reason to spread the book rather than pile into the
tails.

**(d) Vol-scaled residuals.** Ranking on `Σe / sd(e)` rather than `Σe` stops the high-volatility
names from monopolising both tails. In a universe where realised vol spans an order of magnitude,
raw cumulative residuals rank almost the same as raw volatility, and the resulting book both
concentrates risk and churns on vol shocks rather than on information.

### Where this lands

With lookbacks blended over {45, 90} bars and H = 63 bars, the signal autocorrelation at lag H is
low enough that `‖v_t − v_{t−H}‖₁ / gross ≈ 1.0–1.1`, giving

```
turnover ≈ (1095 decisions/yr / 63) × 1.05 ≈ 18, plus ~5/yr of membership churn ≈ 20–25/yr
```

against the seed's 90. If gross Sharpe is merely preserved at the seed's ~0.8 (8.9% gross on 11%
vol), density becomes ~35–45 bps against a 22.5 bps bar, cost share falls from 0.76 to ~0.20, and
triple cost clears with real margin. If longer holding costs a third of the gross return — the
pessimistic case, where momentum alpha saturates around 15 days — density is still ~25–30 and the
book survives. The ratio improves under both, because turnover falls faster than edge does.

**The honest risk in this direction is the turnover band's floor, not its ceiling.** I do not know
where it sits. A 20–25/yr book replaces itself roughly every five weeks, which is an ordinary
institutional cadence rather than a static book, so I expect to clear a floor designed to catch
buy-and-hold. If I am wrong, that is the diagnosis to make from the next packet, and the fix is one
step back along H — which is the axis I moved.

## 3. The mechanism, and who is on the other side

Unchanged from the sealed thesis; I am not re-deriving the economics from a cost packet.

What I am buying is **coin-specific continuation** after the index component is removed. It exists
because attention over 300–500 continuously churning perpetual contracts is scarce and allocated by
salience, so contract-level information diffuses slowly through a retail-dominated holder base
(Liu–Tsyvinski–Wu locate crypto momentum precisely in the large-and-liquid group that the Binance
USD-M universe *is*).

Named counterparties:

- **Long leg.** The disposition-effect holder realising gains early in a winner, and the market
  maker who requires inventory compensation to stand short a contract with one-sided flow.
- **Short leg.** The levered retail long in a falling contract who averages down and is ultimately
  closed by the liquidation engine, not by choice. Perps concentrate this population because they
  are the cheapest leverage in the asset class.
- **Why it is not arbitraged.** The short leg is essentially unavailable on spot — Liu–Tsyvinski–Wu
  concede this and fall back to shorting Bitcoin. Perps dissolve it: uniform specs, one margin pool,
  no locate. Meanwhile the institutional capital that is present in crypto sits in basis and
  funding-carry, not in cross-sectional relative value across 150 alt perps (BIS WP 1087 on limits
  to arbitrage from regulatory, custody and margin frictions).
- **On my side, and dangerous for it.** The trend-chasing leveraged flow the BIS paper identifies
  is what makes continuation continue. It is a tailwind and the crash mechanism at once: the failure
  mode is being last into a crowded narrative. Residualising removes the index-level part of that
  risk and none of the contract-level part.

I am compensated for a genuinely ugly tail (Daniel–Moskowitz crashes; Grobys–Shahzad argue crypto
momentum's realised variance follows a power law whose population moments may not exist). I am
barred from targeting volatility, so I absorb this rather than time it.

## 4. What would falsify this

The sealed falsifiers stand. **None of them can be evaluated from t01** — a single aggregate packet
for the organizer seed contains no residual-versus-raw comparison, no ex-post beta, and no
cross-sectional signal correlation. I am not claiming any of them passed.

- **F1 — the edge was beta all along.** Fires if the residualised book's net Sharpe is ≤ 0.5 and the
  median across residualised configurations is ≤ 0.5. Consequence: I do not nominate a
  residual-momentum variant.
- **F2 — residualisation is decorative.** Fires if the residual and raw signals have mean
  cross-sectional Spearman > 0.95 *and* residualisation does not lift median net Sharpe by ≥ 0.2.
  This is the Liu–Tsyvinski–Wu objection: near-zero R² of the raw momentum long–short on the coin
  market factor at short horizons means there may be little beta in the book to remove.
- **F3 — the betas are noise.** Fires if the realised ex-post beta of the neutralised book to the
  equal-weighted market factor has |β| > 0.15. Consequence: fall back to λ = 1, dollar-neutrality
  only, as an honest statement of what is estimable here.

Added by this trial, and specific to the design change above:

- **F4 — the density fix does not fix density.** If this book comes back with turnover in the 15–30
  band as designed but `gross_edge_bps_per_turnover` still below ~22.5, then holding longer does not
  buy edge here, and residual momentum in this universe does not have a cost-viable expression at
  8h decision frequency. That is a retirement condition, not a signal to search H further.
- **F5 — the turnover collapsed instead.** If turnover lands below the band floor, the diagnosis is
  the holding period alone and the correction is one declared step back along H. This is a
  construction miss, not evidence about the mandate, and I will label it as such rather than let it
  read as a falsified thesis.

The mandate's own falsifier remains the one that matters: **if the edge disappears once the market
factor is removed, the signal was market beta all along.** Note this candidate cannot itself
distinguish that case — it only runs the residualised arm. The comparison is F1/F2's job.

## 5. Deviations from the sealed parameter surface — declared

The sealed grid was written before the cost structure was observable, and no point in it clears
22.5 bps per unit turnover at any plausible gross Sharpe. Rather than hide the change inside the
declared surface, I state it:

1. **H extended to 63 bars (21 days).** The declared H axis was {3, 9, 21} bars, justified in §4.1
   on crash-exposure grounds. One new level added, for the structural reason above. This is the only
   genuinely new level.
2. **L blended over {45, 90} rather than selected.** Both are declared levels; I equal-weight them
   instead of picking one, because with twelve feedback trials picking a lookback is a search, not
   an edge. L = 9 and L = 21 are dropped as the cost-hostile end of the axis.
3. **Return basis is price log return, not price + funding.** §4.2 fixed the basis as including
   funding. Joining the 8h funding stamps to bar windows is a silent-failure risk I cannot test for
   without a shell, and funding contributes ~1% of a 30-day cumulative signal. It is also the
   channel that would have introduced a carry tilt, which §4.3 excludes. Conservative deviation,
   declared.
4. **History requirement graded rather than hard.** §4.2 required `W + L + 1` clean bars. Instead a
   contract needs 66 clean trailing bars to enter, and contributes to whichever formation components
   its history supports; missing components score zero, so young contracts are shrunk toward the
   middle of the book rather than excluded. This protects the breadth gate early in the window.
5. **One beta per decision, applied to every formation lag.** β̂ is estimated at the decision
   boundary and used to residualise the whole return series. It uses no data after the decision, so
   it is not look-ahead; it is a different (and more coherent) estimator, and it makes the residual
   a single series rather than 126 inconsistent ones.

**Deflation count.** The declared 120 becomes, with the extra H level and the blended-L composite
counted as a fifth L level, `2·2·5·4·2 + 5·4·2 = 200` distinct configurations. That is the number I
hold myself to, and it is worse than the number I sealed. I would rather report the honest count.

Everything in §4.3 remains excluded: no funding signal, no volume or taker-buy conditioning in the
signal (volume enters once, in eligibility), no regime switches or crash filters, no multi-factor
residualisation, no asymmetric legs, no hand-curated universes. No volatility targeting of any kind.

## 6. Compliance notes

- **Constraints.** Weights are projected orthogonal to {1, β̂}, so `Σw = 0` and `Σwβ̂ = 0` before
  capping; then normalised to gross ≤ 1.0 and clipped to |w| ≤ 0.10, with a net-exposure backstop at
  0.20·gross against the 0.25 limit. Only symbols from `eligible_symbols` are ever emitted.
- **Panel alignment.** Built on `open_time` via `pd.DataFrame({sym: series})`, never on the
  positional `RangeIndex` — the failure mode RULES §"Aligning across symbols" describes, which
  raises nothing and returns an empty book forever.
- **No state.** `__slots__ = ()`; every decision is recomputed from the streamed rows. No RNG, no
  clock, no filesystem, no dynamic execution.
- **Invariance checks.** `decision_time` is never read, so calendar-shift equivariance is trivial.
  Symbols are never named and ranks are tie-averaged, so results are order- and pseudonym-invariant.
  All computation is on log returns and volume *ranks*, so magnitude rescaling of prices leaves the
  book unchanged. Weights are smooth in the scores with no thresholds, so small perturbations move
  the book slightly rather than discontinuously.
- **Degenerate decisions return `None`, not `{}`.** If the cross-section is momentarily too thin,
  holding is correct; returning `{}` would liquidate the entire book and rebuild it the next bar,
  which is precisely the turnover the whole design exists to avoid.
