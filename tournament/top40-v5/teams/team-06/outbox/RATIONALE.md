# RATIONALE — team-06, cluster relative value (discovery baseline)

**Candidate:** `lane/outbox/candidate.py`
**Trial:** T1 of the preregistered search order (`lane/scouting/THESIS.md` §4.4).
**Feedback consumed:** none. `lane/feedback/` is empty; this is the first candidate I have
written and nothing in it is fitted to a result.

---

## 1. What this is

The thesis at its declared midpoint defaults, with every optional axis switched off. It is the
plainest possible expression of "rolling correlation clusters, trading deviation from cluster
mean" that is still recognisably the thing the mandate names, and it is deliberately not clever.

| axis (THESIS §4.3) | this candidate | why this value |
|---|---|---|
| `W` correlation window | 180 bars (~60d) | midpoint of {90, 180, 270} |
| `q_max` aspect ratio `N/T` | 0.4 | tighter of {0.4, 0.6}; keeps the matrix out of noise geometry |
| `K` clusters | MP-adaptive, clamped [2, 10] | data-driven; not chosen against performance |
| `m_min` | 5 | tighter of {3, 5} |
| `H` deviation lookback | 3 bars (~1d) | interior of {1, 3, 6, 21}; §5.3 predicts `H = 1` dies on cost |
| `Z` | within-cluster cross-sectional | simpler of the two; OU adds a fitted `κ` I cannot yet diagnose |
| `S` smoothing | 3 decisions | midpoint of {1, 3, 6} |
| `z_enter` | 0.75 | midpoint of {0, 0.75, 1.25} |
| `α` funding tilt | **0** | off — a second mechanism would confound the first read |
| `γ` liquidity weighting | **0** | off — same reason |
| `sign_mode` | contrarian | the thesis's stated prior (§1.6) |

Three axes are set to their inert value on purpose. `α` and `γ` each add a *separate* economic
claim (crowding/carry, and inventory rent concentrated in illiquid names). If I switch them on now
and the book works, I will not know which claim carried it. They are trials T6 and T8, in that
order, and they stay off until the residual reversal itself has been measured alone.

## 2. The mechanism, in one paragraph

Leveraged directional flow in Binance USD-M perpetuals arrives aimed at a *theme* — an L1 basket,
memecoins, an AI narrative, a rotation out of majors — but executes on *individual* contracts, each
with its own book and its own inventory-constrained market makers. Liquidation and ADL engines make
this worse: they sell what is margin-deficient, at whatever price, with no view at all. The result
is that one member of a genuinely co-moving group gets pushed away from the group without any news
about what the group has in common. Someone absorbs that at a price concession and lays it off over
the following hours to days. **This candidate rents its balance sheet on those terms: it is short
the members of a discovered co-movement group that have run rich to the group, and long the ones
that have run cheap, in proportion, with each group's contribution summing to zero.** The return
being claimed is the inventory concession, not a forecast.

## 3. Who is on the other side

- **Leveraged retail directional traders** picking the most salient name inside a narrative group.
  They create the deviation; they are impatient rather than wrong.
- **Liquidation and auto-deleveraging engines**, price-insensitive by construction.
- **Basis and funding-carry desks**, whose delta-neutral hedging puts one-sided pressure on a single
  contract's perp leg for reasons unrelated to that asset's value relative to its peers.
- **Cross-sectional momentum and trend programs**, which by construction buy the group member that
  has already moved most — the direct counterparty to the contrarian sign.
- **On the days this loses: whoever was right.** The deviation was information — an unlock, a
  listing, an exploit, a squeeze — and the book was short the start of it. There is no news feed,
  no open interest and no liquidation feed in this context, so that case cannot be filtered out. It
  is the adverse-selection cost the premium pays for, and it is unhedged.

## 4. Why the cluster, and not the universe

This is the whole marginal claim of the lane, so it is worth being precise. A raw cross-sectional
reversal signal in crypto is dominated by one market factor; demeaning against the whole universe
removes that factor and nothing else. Demeaning against a *discovered co-movement group* removes
the market factor **and** the narrative factor the group shares, which is where most of the
remaining non-idiosyncratic variance lives. Crypto has no GICS — listing-time sector labels are
marketing and are never revised — so the only defensible grouping is one re-estimated from the
realized correlation matrix at every decision.

The implementation takes the Laloux noise-dressing result seriously rather than decoratively, in
three places that are easy to skip:

1. **`q_max` caps the universe against the window.** With ~200 eligible perps and a 180-bar window
   the sample correlation matrix is rank-deficient and its "clusters" are noise geometry. The
   candidate caps `N ≤ 0.4·T` using the *actual* aligned window length, not the requested one.
2. **The Marchenko–Pastur bulk is clipped to its mean**, trace preserved, before anything is
   clustered.
3. **The top eigenvector is removed before clustering, not after.** Clustering raw correlations in
   crypto returns one giant cluster, because everything correlates with the market. Detoning first
   is what makes the partition about co-movement *structure* rather than about beta.

`K` is then set to `1 + (# eigenvalues above the MP edge, excluding the top)`, clamped to [2, 10].
This is the one place the candidate reads structure out of the data instead of being told it, and
it is deliberate: `K`, `m_min` and `q_max` are the three parameters the thesis committed to
choosing from stability diagnostics rather than from performance.

## 5. Construction details that are choices, stated so they can be argued with

- **Dead-zone is a hard entry gate, weight linear in z.** The frozen weight transform is "linear in
  clipped, smoothed z", so the gate zeroes names inside the dead zone rather than shrinking every
  name toward it. A soft threshold was written first and rejected: it concentrates gross onto the
  few extreme z's and puts the effective-breadth gate at risk. The discontinuity is bounded in book
  terms because a name entering at the gate carries the *smallest* weight in the book.
- **Smoothing reuses the current partition across all `S` lags.** The `H`-bar returns ending at
  `t`, `t−1`, `t−2` are all residualized against the partition estimated at `t`. This is past-only
  and it isolates smoothing of the *signal* from churn in the *partition*, which is the thing F1 is
  about.
- **Within-cluster demeaning is over each cluster's active names.** Demeaning over all members would
  spray tiny positions onto names the dead zone deliberately excluded.
- **Winsorization is near-inert under Spearman** and is applied only for fidelity to the
  preregistration. Rank correlation is already robust to the clipped tail; I would rather note this
  than quietly drop a frozen step.
- **Gross targets 0.98 and the per-name cap is 0.099**, purely as headroom under the hard 1.0/0.10
  limits. This is book *shape*, not risk sizing — the engine owns the ex-ante volatility unit and
  will rescale the whole book. No volatility targeting appears anywhere in the file.
- **Statelessness is structural, not asserted.** Nothing is carried between calls; every decision
  recomputes the panel, the matrix, the partition and the book from the streamed past-only rows.
  Turnover is controlled by making the *signal* slowly varying (`H`, `S`, `z_enter`), never by
  remembering positions.
- **No symbol identity, no date literals, no embedded data.** Symbols are used only as dictionary
  keys and are filtered to strings not beginning with `__` so the organizer's reserved target
  column can never be traded. Every quantity is a rank, a log return, a correlation or a
  z-score, so the book is invariant to a rescaling of price and volume levels.

## 6. What would falsify this

In priority order, as preregistered. **A profitable book that fails F2 is still a falsified thesis
and I will report it as one.**

**F2 (primary) — the cluster must earn its place.** At matched gross and matched turnover, this
book's gross edge per unit turnover must exceed that of the identical book with `K = 1`, i.e. plain
universe-demeaned reversal. If a discovered partition adds nothing over the universe mean, the
clustering is decoration and this is a generic reversal strategy carrying extra estimation error.
Trial T2 is that null, and it goes early precisely because it is the only trial that can embarrass
me.

**F1 — the lane falsifier.** If cluster membership is unstable across a *genuine* estimation
boundary, deviations from cluster mean are noise. Operationally: median Adjusted Rand Index between
partitions fitted on the disjoint windows `[t−2W, t−W)` and `[t−W, t)` must exceed 0.15 (disjoint,
not adjacent — adjacent windows overlap ~99% here and would score high mechanically, which is a
test that cannot fail); and the median count of eigenvalues above the MP edge, excluding the top,
must be ≥ 2. If it is ≤ 1, "cluster" is a synonym for "market beta" and the premise is dead
regardless of the backtest.

**F3 — the sign must be stable.** Split the visible window into four contiguous sub-blocks; the
sign of the cluster-residual autocorrelation at `H` must agree in at least 3 of 4. A sign that
flips across sub-blocks makes any full-window Sharpe an average over a coin flip.

If a falsifier fires I retire the thesis rather than substituting a different mechanism into the
slot. Specifically: I will not ship the `K = 1` book and call it cluster relative value, I will not
switch to declared sector labels to manufacture stability, and I will not select the sub-blocks
where the sign agreed.

## 7. What I most expect to be wrong, before seeing any number

Named now so that seeing them later is a confirmation rather than a discovery.

1. **A degenerate partition.** Average linkage chains. If detoning does not break it, the cut into
   `K` groups will be one giant cluster plus singletons; the singletons fall below `m_min` and are
   dropped, and what remains is a single global cluster — the F2 null, arrived at by accident. The
   diagnostic is a book that behaves identically to universe-demeaned reversal.
2. **Partition churn dominating turnover.** The partition is re-estimated every decision. When a
   name changes cluster its residual and therefore its weight can flip sign for reasons that have
   nothing to do with price. `S = 3` smooths the signal but not the partition, by design.
3. **The universe cap pushing me away from the edge.** The liquidity-provision literature puts the
   premium in small, illiquid, high-adverse-selection pairs. `q_max` and the `L_min = W` history
   requirement force the tradeable set toward the top ~72 names by volume, which is the *competed*
   end. This was declared in the thesis before data was mounted and I expect it to cost most of the
   edge.
4. **Effective breadth.** With ~72 names, a 0.75 gate on a smoothed z of standard deviation ~0.85
   should leave roughly a third of the cross-section active. If it leaves far fewer, `z_enter` and
   `S` move together at T7 — that is a gate repair, not a performance search.
5. **Cost.** `H = 3` on an 8h decision grid is a demanding turnover profile against a triple-cost
   survival gate. If the book only clears at 1x, it is not a book.

## 8. What I am not claiming

That this is a neglected corner. Market-neutral is the most populated declared strategy bucket in
crypto funds, and the canonical equity version of this trade had its Sharpe roughly halve as it was
competed. The claim is narrower: the *supply* of the flow — retail leverage, liquidation cascades,
carry-desk hedging — is structurally large and renewing, while the capital that absorbs it is
concentrated in the largest contracts and is subject to periodic forced withdrawal. That is a thin
edge in a crowded trade, and I would rather report a thin one honestly than a thick one I fitted.
