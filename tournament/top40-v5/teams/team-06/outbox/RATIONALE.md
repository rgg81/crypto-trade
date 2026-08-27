# RATIONALE — team-06, cluster relative value

**Trial:** T1, the preregistered baseline of `lane/scouting/THESIS.md` §4.4.
**Phase:** discovery. No feedback packets exist yet; nothing here is fitted to a result.

---

## 1. What the book is

At every decision, from past-only rows only:

1. Keep `eligible_symbols` with at least `W = 180` bars (60 days) of history.
2. Rank by median `quote_volume` over the window, keep the top `N = floor(q_max · W) = 72`.
3. Build the `W × N` close panel **aligned on `open_time`**, forward-fill genuine bar gaps, take
   8h log returns, winsorize each column at 1%/99% within the window.
4. Spearman correlation → Marchenko–Pastur eigenvalue clipping (bulk clipped to its own mean,
   trace preserved) → **remove the top eigenvector** → renormalize to unit diagonal.
5. Distance `d = √(2(1−ρ))`; average-linkage agglomerative clustering into `K` groups, where
   `K = 1 + (#eigenvalues above λ₊ = (1+√q)², excluding the market mode)`, clamped to [2, 10].
   Clusters with fewer than `m_min = 5` members are not traded.
6. Residual = each name's `H = 3`-bar (1 day) return minus its cluster's equal-weight 3-bar return.
7. Standardize the residual cross-sectionally **within its own cluster**, clip at ±3, and average
   that z over the last `S = 3` decision boundaries.
8. Contrarian sign, dead-zone `z_enter = 0.75` applied as a soft threshold.
9. Demean within each cluster, then globally; normalize `Σ|w| = 1.0`; cap `|w| ≤ 0.10`.

`α = 0` and `γ = 0`: the funding tilt and the liquidity weighting are declared knobs (§4.3 axes 9
and 10) held at their neutral setting. This is the mandate with nothing bolted on.

---

## 2. The mechanism

Order flow in Binance USD-M perpetuals is **thematically correlated but name-specific in its
execution**. Leveraged directional flow arrives aimed at a narrative group — L1s, memecoins, an AI
basket, a rotation out of majors — but it lands on individual contracts, each with its own book, its
own makers, and its own inventory limits. The group-level view that motivated the trade is usually
not new information about the single member that absorbed it. So the flow pushes one name away from
the contemporaneous move of the assets it genuinely co-moves with, without any change in the common
factor driving all of them.

Someone holds the other side at a price concession and unwinds it over the following hours to days.
**The return claimed here is that concession, measured against the group rather than against the
asset's own past.** Bianchi–Babiak–Dickerson (2022) and Farag et al. (2025) identify this premium as
inventory rent for liquidity provision, not a behavioural anomaly, and find it concentrated exactly
where liquidity provision is hardest.

Two things make this a *cluster* claim rather than a generic reversal claim:

- **The benchmark has to be the right one.** Liu–Tsyvinski–Wu (2022) show the crypto cross-section
  is dominated by a market factor. "This name fell 4% today" is mostly "crypto fell 4% today," and a
  reversal signal that does not remove that is trading beta while calling it relative value.
  Demeaning against the whole universe removes the market factor and nothing else. Demeaning against
  a discovered co-movement group removes the market factor **and** the narrative/sector factor the
  group shares — where most of the remaining non-idiosyncratic variance lives.
- **The groups cannot be declared.** Crypto has no GICS. Sector labels are marketing, assigned at
  listing and never revised, while the co-movement structure they proxy rotates on a timescale of
  months. The only defensible grouping is one re-estimated from the realized correlation matrix at
  every decision.

Two structural choices are not decoration. **MP eigenvalue clipping** is there because Laloux et al.
(1999) show the bulk of an empirical correlation spectrum is indistinguishable from a matrix with no
correlation structure at all — cluster on the raw sample matrix and you cluster noise geometry. The
**`q_max` aspect-ratio cap** is the same constraint in universe terms: with ~150–250 eligible perps
and a 180-bar window the sample matrix is rank-deficient and its partition meaningless, so the
universe is capped at 72 names. **Removing the top eigenvector before clustering** is what stops the
"discovered sectors" from being a beta sort.

---

## 3. Who is on the other side

- **Leveraged retail directional traders** buying the strongest-looking member of a narrative group.
  Not stupid — impatient, and selecting the name within the group on salience rather than on relative
  value. This is the flow that creates the deviation.
- **Liquidation and auto-deleveraging engines.** Price-insensitive by construction: they sell what is
  margin-deficient, not what is expensive. This is the cleanest version of the signal and it exists
  in this venue in a way it does not exist in equities.
- **Basis and funding-carry desks**, whose delta-neutral spot-perp hedging puts one-sided pressure on
  a single contract's perp leg for reasons unrelated to that asset's value against its peers.
- **Cross-sectional momentum and trend programs**, which by construction buy the group member that
  has already moved most.
- **On the losing days: whoever was right.** See §4.

---

## 4. What the premium pays for

It is not a free lunch. Avellaneda–Lee report the equity version's Sharpe roughly halving from
1997–2007 to 2003–2007 as it was competed, and PwC/AIMA report market-neutral as the *most common*
declared crypto hedge fund strategy. This is a crowded bucket, and the payment is for:

1. **Immediacy** — renting balance sheet on the same terms as a market maker.
2. **Adverse selection** — sometimes the deviant name is deviating for a reason (unlock, listing,
   exploit, squeeze). With no news feed, no open interest and no liquidation feed, the residual will
   occasionally say "short it, it is rich to its cluster" at the start of a 300% squeeze. The ±3
   z-clip and the 0.10 cap are the only defence and they are not a good one.
3. **Correlation-regime risk** — the cluster is a hedge that fails when it is needed. In a drawdown
   correlations converge, the partition collapses toward one market cluster, and residual variance
   vanishes.
4. **Crowding and deleveraging** — Khandani–Lo's August 2007 template: a crowded residual book loses
   on a mechanical unwind, not on signal decay, and it loses when the counterparty that normally pays
   the immediacy premium has stepped away. Perps have an exchange-run version of this.

The expected edge is budgeted accordingly. The estimation constraints above push the tradeable
universe toward the *liquid* end — which is the *competed* end — and §1.5 of the thesis preregisters
the expectation that this costs most of the edge.

---

## 5. What would falsify this

Stated in the sealed thesis before any data was mounted, and restated here unchanged.

**F2 — PRIMARY. The cluster must earn its place.** At matched gross and matched turnover, this
book's gross edge per unit turnover must exceed that of the identical book with `K = 1` — a single
global cluster, i.e. plain universe-demeaned cross-sectional reversal. If it does not, the mandate is
falsified: the only thing "sectors are discovered" adds is the claim that a *discovered partition* is
a better benchmark than the universe mean. If it adds nothing, the clustering is decoration and this
is a generic reversal strategy carrying extra estimation error — **even if it makes money.** A
profitable book that fails F2 is a falsified thesis and will be reported as one. `K = 1` is the next
trial (T2) precisely because it is the only one that can embarrass me.

**F1a — cluster identity must survive re-estimation.** Median Adjusted Rand Index between the
partition from `[t−W, t)` and the partition from the **disjoint** window `[t−2W, t−W)` must exceed
0.15. Disjoint, not adjacent: overlapping rolling windows share ~90% of their data and would score
high mechanically, which is a test that cannot fail.

**F1b — structure above noise.** Median count of eigenvalues above the MP edge `λ₊ = (1+√q)²`,
excluding the market mode, must be ≥ 2. If it is ≤ 1, the only structure in the matrix is the market
factor, "cluster" is a synonym for "market," and the discovered-sector premise is dead regardless of
what any backtest says. (This is the same quantity the code uses to set `K`, so a degenerate spectrum
shows up as `K` pinned at its floor of 2.)

**F3 — the sign must be stable.** Split the visible window into four contiguous sub-blocks; the sign
of the cluster-residual autocorrelation at `H` must agree in at least 3 of 4. Otherwise the effect is
regime-contingent and any full-window Sharpe is an average over a coin flip.

**If a falsifier fires I retire the thesis rather than substitute a mechanism into the same slot.**
Specifically: if F2 fires I will not ship the `K = 1` global-demeaned book and call it cluster
relative value; if F1 fires I will not switch to declared sector labels to manufacture stability; if
F3 fires I will not select the sub-blocks where the sign agreed.

Zaremba et al. (2021) find daily cross-sectional reversal in crypto driven by illiquidity but
*momentum* in the largest and most tradeable coins — the tier a Binance-perp universe sits in. The
sign is therefore not assumed: `sign_mode` is a declared, literature-motivated, last-in-search-order
knob (§4.3 axis 11). I expect reversal to survive cluster-demeaning, because much of that large-cap
"momentum" is unremoved market direction and demeaning removes it. If only the sign-flipped
configuration works, that is weak evidence, not a discovery.

---

## 6. Reading decisions, recorded rather than argued later

- **Winsorized returns feed both the correlation and the signal.** §4.1 winsorizes at panel
  construction (step 3) and step 8 operates on that panel. Using raw returns for the signal would put
  a single 300% bar into a 5-member cluster's cross-sectional standard deviation and squash everyone
  else to zero. The ±3 z-clip is the second line, not the first.
- **Smoothing is stateless.** `S = 3` averages the z measured at the last three decision boundaries,
  all recomputed from the same panel. Turnover is controlled by making the *signal* slowly varying
  (`H`, `S`, `z_enter`), never by remembering previous positions — which the rules forbid and which
  would fail exact-replay determinism.
- **The dead-zone is a soft threshold**, `sign(z)·max(|z|−0.75, 0)`, so the ranking inside the
  surviving tails is preserved rather than flattened to ±1.
- **A missing bar is forward-filled**, i.e. treated as a bar with no observed price change, not as a
  hole that disqualifies the name.
- **No volatility targeting.** Gross is fixed at `Σ|w| = 1.0` before the engine's common ex-ante risk
  unit rescales it. Cross-sectional z-scoring is per-name signal standardization, not book risk
  scaling; this interpretation was recorded in §4.5 before data was mounted.
- **The per-decision `except` returns a flat book, not a masked bug.** A degenerate cross-section at
  one decision (failed eigendecomposition, collapsed panel) should cost that decision, not the run. A
  *systematic* failure is unmistakable in the packet — gross exposure and turnover are zero
  everywhere, which is not what a strategy with no edge looks like.

---

## 7. What I want back from this packet

Beyond the standard metrics: **mean number of names held**, **mean gross**, **turnover**, and
**gross edge per unit turnover** — the last is the F2 comparison quantity, and T2 (`K = 1`) is
useless without it measured the same way here. Also whether the book is ever flat, which would
indicate the universe filters are biting harder than intended rather than the signal being off.

Structural expectations, stated now so a miss is informative: roughly 60–72 names in the universe,
~35–40% of them non-zero after the dead-zone (the `H`-bar windows at consecutive lags overlap, so the
smoothed z shrinks less than independence would suggest), both sides used by construction since every
cluster is demeaned to zero, and net ≈ 0.

The costly corner is turnover: `H = 3` with `S = 3` on an 8h grid is a demanding hurdle against
~9bp round-trip at 1× and ~27bp at 3×. If the triple-cost gate is what fails, that is the
pre-registered job of T7, not evidence against the mechanism.
