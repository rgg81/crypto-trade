# RATIONALE — team-06, cluster relative value

**Nomination.** Preregistered thesis: `lane/scouting/THESIS.md`, sealed before any data was mounted.
**Evidence available:** two packets, `t01` and `t02`, on the visible development window only.

---

## 1. What the two packets actually establish

They establish less than two packets sound like, and I want that on the record before anything else.

**`t02` is not a result.** `active_bar_fraction = 0.0`, gross `0.0`, turnover `0.0`, every metric zero. That
is not a book with no edge; it is a book that never opened a position. It is precisely the silent
failure `RULES.md` describes, and it carries **zero information about the mechanism** — only about the
code that expressed it. I am not going to mine it for a signal it does not contain.

**`t01` is one observation, and its single most useful number is a cost.** Gross P&L was
`−3.37 bp × 311.9 = −10.5%`; net was `−29.25%`. The `18.7%` difference over `311.9` units of turnover
is

> **≈ 6.0 bps of cost per unit of turnover at 1×, ≈ 18 bps at 3×.**

That number, not any signal insight, determines what kind of book can exist in this venue. To bring
`cost_share` under a half a candidate needs roughly **12 bps of gross edge per unit turnover**; to
survive triple cost it needs roughly **18–20 bps**. `t01` also failed `turnover_ceiling` at 311.9/yr,
so the ceiling is below that; `t02` failed `turnover_floor` at 0.0. The admissible band is bracketed
but not known.

Alpha per unit of turnover scales like `√h` in the holding horizon. At an 8-hour cadence, with 8h
idiosyncratic vol near 1.7% and a generous cross-sectional IC of 0.04, one bar buys ~3 bps and one day
~6 bps — under the 1× cost, never mind the 3× gate. **No improvement in signal quality rescues a book
rebalanced every 8 hours.** Reaching 18–20 bps requires `h ≈ 36–44` bars, i.e. **12–15 days**.

That is the design constraint, and it happens to land on the same horizon the clustering literature
gives independently: Jing et al. (2025) report consensus-clustered crypto correlation structure paying
out to roughly 14 days. The cost arithmetic and the cluster-persistence prior agree on ~2–3 weeks. I
did not tune to that agreement; I noticed it after both were fixed.

---

## 2. The book

At every decision, recomputed from the past-only rows in `context` and nothing else:

1. Eligible symbols carrying `W = 180` bars (60 days) of history, ranked by median `quote_volume`;
   the top `q_max·W = 72` form the correlation universe. A ladder drops `W` to 120 then 90 if fewer
   than 32 names qualify, so the book is never silently flat at the start of the run.
2. **The tradeable weight is tapered to zero across the bottom of the liquidity ranking** — flat for
   ranks 0–43, linear to zero at rank 72.
3. Panel of closes **aligned on `open_time`**, 8h log returns, winsorized at 0.5%/99.5% per column.
4. Spearman correlation → Marchenko–Pastur eigenvalue clipping of the noise bulk → removal of the top
   (market) eigenvector → renormalized to unit diagonal. Distance `d = √(2(1−ρ))`.
5. Average-linkage agglomeration, **read off at five nested cut levels `K ∈ {12, 8, 6, 4, 3}`**.
6. Per level, the leave-one-out mean of the name's own group. Levels where that group has fewer than
   `m_min = 5` members are skipped; a name with no valid level anywhere is not traded. The benchmark
   is the average across surviving levels.
7. Residual return series, divided by the name's own residual volatility.
8. **Displacement** = a symmetric triangular kernel over the last `L = 63` bars (21 days) of that
   residual. Weight zero at both ends, peak at ~10 days back.
9. Centred within the coarse `K = 4` partition, scaled cross-sectionally, clipped at ±3, contrarian
   sign, soft dead zone `|z| > 0.85`.
10. Plus a cluster-relative funding tilt at `α = 0.4`, from the last 21 settlements.
11. Taper-weighted demean inside each coarse cluster, then globally; gross `Σ|w| = 1.0`; cap
    `|w| ≤ 0.09`; `|net| ≤ 0.20`.

### 2.1 Three choices that are structural, not parameters

**The consensus cut is the answer to my own lane falsifier.** My lane's falsifier is that cluster
membership is unstable week to week. A single cut of a dendrogram is exactly where that instability
bites: a name near a boundary flips, its benchmark changes discretely, and the flip is paid for in
turnover at 6 bps a unit. Reading one dendrogram at five heights means a flip at one level leaves the
other four agreeing, so the benchmark moves by ~1/5 of the flip. It is also the remedy the literature
prescribes (Jing et al., consensus clustering for temporal persistence) rather than one I invented to
patch a number, and it is a genuine expression of "sectors are discovered": a name's benchmark is a
blend of its tight neighbours and its broad sector, which is what a hierarchy actually says.

**The liquidity taper removes universe churn as a turnover source.** A hard top-N cut turns every
boundary crossing into a full-size trade. Under the taper a name arrives and departs at ~0 weight.
This is stateless — it depends on the current liquidity ranking only, never on the previous book —
and it is why the demeaning is taper-weighted rather than flat: a flat demean would hand a boundary
name the group offset back and undo the taper.

**The triangular kernel is what makes the book slow enough to be affordable.** A boxcar or a
decay-from-lag-1 window admits each new bar at full weight, so the signal changes by a full bar's
residual every decision and turnover is set by the cadence regardless of the window length. A kernel
that ramps in *and* out changes by `O(1/L)` per bar. For `L = 63` the implied lag-1 signal
autocorrelation is ~0.998, which puts turnover near **50/yr from the signal**, plus cluster and
universe churn — call it **50–90/yr**. At the measured 6 bps that is 3–5% of cost at 1× and 9–16% at
3×, against a book the engine scales to ~11–12% volatility.

It also has a second, independent virtue: the most recent bars carry ~zero weight. That vacates the
8h–24h window where informed and liquidation-driven *continuation* lives, which is the horizon
Zaremba et al. (2021) find flips sign in exactly the largest-and-most-tradeable tier a Binance perp
universe sits in. I am not betting against that horizon; I am declining to be in it.

### 2.2 Why the book is deliberately not more diversified

`t01` passed `effective_breadth` at 12.26 with `mean_gross_exposure` 0.83 and 11.8% realised vol —
implying roughly 50% annualised idiosyncratic vol per name, and that the engine's risk unit sits near
11–12%. A cluster- and market-neutral book's volatility falls roughly as `1/√breadth`, so pushing
breadth to 35 would drop volatility per unit gross to ~8%, the engine would need gross above the 1.0
cap to reach its risk unit, and `risk_unit_attained` would fail. The dead zone and the cap are set to
land **effective breadth near 13–16**: clear margin over a floor that `t01` shows is well below 12.26,
and still concentrated enough that the engine scales the book *down* rather than running into its cap.
This is a portfolio-construction choice about concentration, not volatility targeting — gross is fixed
at 1.0 before the engine's risk unit touches it, exactly as recorded in THESIS §4.5 before data.

---

## 3. The mechanism, and who is on the other side

Unchanged from the sealed thesis.

Order flow in Binance USD-M perpetuals is **thematically correlated but name-specific in its
execution**. Leveraged directional flow arrives aimed at a narrative group — L1s, memecoins, an AI
basket, a rotation out of majors — but it lands on individual contracts, each with its own book, its
own makers and its own inventory limits. The group-level view that motivated the trade is usually not
new information about the single member that absorbed it. Someone takes the other side at a price
concession and lays the inventory off over the following days. **The return claimed is that
concession, measured against the discovered group rather than against the asset's own past.**

Demeaning against a discovered co-movement group removes the market factor — without which "this name
fell 4%" is mostly "crypto fell 4%" (Liu–Tsyvinski–Wu) — *and* the narrative factor the group shares,
which is where most of the remaining non-idiosyncratic variance lives. MP clipping is there because
Laloux et al. show the bulk of an empirical correlation spectrum is indistinguishable from a matrix
with no structure at all: cluster the raw sample matrix and you cluster noise geometry.

On the other side, named:

- **Leveraged retail directional traders** buying the salient member of a narrative group. Not
  stupid — impatient, and choosing the name within the group on salience rather than relative value.
- **Liquidation and auto-deleveraging engines**, price-insensitive by construction: they sell what is
  margin-deficient, not what is expensive.
- **Basis and funding-carry desks**, whose delta-neutral hedging puts one-sided pressure on a single
  contract's perp leg for reasons unrelated to that asset's value against its peers.
- **Cross-sectional momentum and trend programs**, which buy the group member that already moved most.
- **On the losing days: whoever was right.**

At a three-week holding horizon the counterparty story shifts weight away from the market maker's
hours-to-days inventory unwind and toward **slow relative-value convergence and lead-lag diffusion
within a correlated group** — the laggard-catching-up trade *is* residual reversal. Both mechanisms
predict the same sign. I am naming the shift because the cost arithmetic forced the horizon, and I
would rather say so than pretend the original mechanism reaches unchanged to three weeks.

The premium pays for immediacy, for adverse selection (with no news feed, open interest or liquidation
feed, the residual will sometimes say "short it, it is rich" at the start of a squeeze; the ±3 clip and
the 0.09 cap are the only defence and they are not a good one), for correlation-regime risk (the
cluster is a hedge that fails when correlations converge), and for crowding — PwC/AIMA report
market-neutral as the *most common* declared crypto hedge fund strategy, and Khandani–Lo is the
template for how a crowded residual book dies. This is not a neglected corner.

---

## 4. What would falsify this

**F2 remains the primary falsifier and it is still untested. I am nominating with it open.**
From THESIS §3.1: at matched gross and turnover, this book's gross edge per unit turnover must exceed
the identical book with `K = 1` — plain universe-demeaned reversal. If it does not, the clustering is
decoration and the mandate is falsified *even if the book makes money*. Two charged trials produced one
cost measurement and one non-run; neither could be spent on the null. Per THESIS §3.4, a `K = 1` book
that won would be reported as a falsification, not shipped — and this candidate is not that book: its
benchmark is a five-level consensus of discovered groups, which reduces to the universe mean only if
the correlation matrix has no structure beyond market beta.

**F1b degrades in plain sight.** If the denoised, market-stripped matrix carries no sector structure,
average linkage on a near-identity distance matrix produces groups that are arbitrary but stable, the
five levels stop disagreeing in any informative way, and the benchmark converges toward the universe
mean. That is F1b firing visibly rather than being concealed behind a fixed `K`. I deliberately did
*not* gate trading on a per-decision structure test: that is the dispersion-threshold regime switch
THESIS §4.5 forbids and which `RULES.md` says no invariance check closes.

**Specific, checkable ways this candidate is wrong:**

- **Turnover outside ~40–110/yr.** Then my model of what drives turnover here — kernel shape, taper,
  consensus cut — is wrong, and the §1 diagnosis with it.
- **Gross edge density still negative.** Then cluster residuals do not revert at 2–3 week horizons
  either, and cluster relative value has no expression in this venue that clears 6 bps a turn. That is
  a retirement, not a re-tune.
- **Positive but under ~12 bps per unit turnover.** The mechanism may be real and still not worth its
  immediacy cost at any cadence reachable at 8h resolution.
- **Effective breadth collapses toward 8–10.** Average linkage is chaining into one giant group plus
  singletons; the discovered sectors are one sector.
- **`risk_unit_capped_fraction` rises materially.** My concentration estimate in §2.2 is wrong in the
  diversified direction and the engine cannot reach its risk unit inside the gross cap.
- **Survives 1× but not 3×.** Same verdict as `t01`. Per the phase guidance, that is not a book.

---

## 5. Declared departures from the preregistration

THESIS §4.4 requires that a knob I want mid-phase be reported as an incomplete preregistration rather
than added silently. Four are, and I would rather list them than let them pass as inside the surface:

1. **Consensus cut levels `K ∈ {12, 8, 6, 4, 3}` replace the single MP-adaptive `K`.** §4.3 axis 3
   declared `K ∈ {4, 6, 8, MP-adaptive}` as a choice of *one* cut. Reading one dendrogram at five
   heights is not on that surface. It is motivated by §2.10, which was cited in the seal for exactly
   this purpose, and it makes the benchmark continuous where a single cut is discrete.
2. **The triangular kernel `L = 63` replaces the `(H, S)` pair.** §4.3 axes 5 and 7 declared a boxcar
   `H`-bar deviation averaged over `S` decisions, with `H ≤ 21` and `S ≤ 6`. The arithmetic in §1 shows
   that family cannot reach the required horizon: its turnover is dominated by each new bar entering at
   full weight. The kernel is the same idea — a slowly-varying signal, no memory of previous
   positions — with the front weight taken to zero.
3. **The liquidity taper is new.** §4.3 axis 10 declared a liquidity *weighting exponent* `γ`; a rank
   taper at the universe boundary is a different object, and its purpose is turnover, not tilt. It is
   stateless.
4. **The window ladder `(180, 120, 90)` is new**, and exists only so a thin start to the run cannot
   produce another all-zero packet.

Inside the declared surface: `q_max` = 0.4, `m_min` = 5, `z_enter` = 0.85 (§4.3 range {0, 0.75, 1.25},
which this sits between — a further small departure, chosen for breadth per §2.2 rather than for
performance), `α` = 0.5→0.4, `γ` = 0, `sign_mode` = contrarian.

**Trial accounting, stated plainly.** Two charged trials have been spent. Neither measured this
mechanism: `t01` measured the organizer's seed, `t02` measured nothing. The deflation benchmark should
read this nomination as a **design derived from one cost measurement and the preregistered
literature**, not as the survivor of a search — because no search over this surface has been run
against feedback. That is unusually honest and also unusually untested, and both halves of that
sentence are true.

---

## 6. Contract compliance and invariance

- **Interface.** `build_strategy()` returns an object with
  `target_weights(context, *, seed) -> Mapping[str, float] | None`. Output is a fully specified book
  over `eligible_symbols` (0.0 for names not traded), so a rebalance is never ambiguous.
- **Caps.** `Σ|w| ≤ 1.0`, `|Σw| ≤ 0.20 < 0.25`, `|w| ≤ 0.09 < 0.10`.
- **Context shape.** Only the five documented attributes are read. Bars are read via
  `open_time`, `close` and `quote_volume`; funding via `symbol`, `funding_rate` and `funding_time` —
  not `last_funding_rate`. The panel is built on `open_time`, never on the positional index, and the
  columns are re-indexed back onto the liquidity ordering so a `concat` cannot permute them.
- **Statelessness / determinism.** No instance attributes (`__slots__ = ()`), no RNG, `seed` unused,
  no network, subprocess, filesystem, `eval`/`exec`/`getattr`. Every number is recomputed from the
  streamed past-only rows. Sorts are stable and ties fall back on the organizer's `eligible_symbols`
  ordering.
- **Look-ahead.** Only trailing slices of frames the runner has already truncated at the boundary;
  funding is read from the tail of a frame whose rows are strictly earlier than the decision.
- **Calendar shift.** No absolute date is read anywhere — `decision_time` is never touched. The
  funding window is positional, not dated.
- **Symbol pseudonymisation.** Symbols are dict keys only; nothing branches on the string.
- **Magnitude scale.** Log returns, rank correlation and an ordinal liquidity screen; no price level
  enters a comparison.
- **Small perturbation.** The dead zone is a soft threshold (`sign(z)·max(|z|−0.85, 0)`, continuous at
  the boundary), the universe boundary is a ramp rather than a step, and the five-level consensus damps
  the one genuinely discrete object in the pipeline — the dendrogram cut.
- **Failure policy.** A degenerate cross-section at a single decision returns `None`, which holds
  rather than churning to flat and back. A *systematic* failure would be unmistakable in the packet and
  would look exactly like `t02` — which is why the pipeline's entry requirements are permissive and the
  optional funding tilt is guarded separately, so it can never zero the core book.
