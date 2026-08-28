# team-15 — regime-allocated ensemble (refinement candidate)

Working from `lane/scouting/THESIS.md` (Phase-S, sealed) and the single feedback packet `t01.json`.

---

## 1. What t01 actually said

t01 is the unmodified organizer seed, not my design, so it carries no information about my mechanism.
It carries a great deal about the **cost environment**, and that is what I refined against.

| gate | value | verdict |
|---|---|---|
| median effective breadth | 25.8 | pass |
| mean gross exposure | 0.990 | pass |
| long / short exposure share | 0.4996 / 0.5004 | pass |
| active bar fraction | 1.00 | pass |
| **annualised turnover** | **560.6** | **fail (ceiling)** |
| **gross edge / turnover** | **3.59 bps** | **fail** |
| **cost share of positive gross** | **2.09** | **fail** |
| **triple-cost return** | **−65.6%** | **fail** |

The seed is a structurally sound *portfolio* — breadth, gross, both sides, participation all clear.
All four failures are one failure, and the arithmetic pins it down.

At 8h bars there are ~1095 decisions a year, so turnover 560.6 is **0.51 of the book replaced per
bar**. Gross return is `560.6 × 3.5897 bps ≈ +20.1%`; net is `−20.1%`; so costs are ≈40%/yr, which
implies the venue charges

> **≈ 7.2 bps per unit of turnover at 1x.**

That single number sets the design constraint. Net return is `turnover × (density − k × 7.2 bps)`, so
survival at 3x requires

> **gross edge density > ~21.5 bps per unit turnover — independent of the turnover level.**

The seed sits at 3.59 bps. It needs a **6x** improvement in per-trade edge. Density is essentially
half the gross P&L of a round trip: the seed earns ~7 bps per position round trip and pays ~7 bps for
it. There is no setting of a lookback that turns a 7 bps round trip into a 43 bps one. **This is a
design fault, not a parameter fault**, which is why nothing below is a tuning of the seed.

Note what the arithmetic does *not* say: lowering turnover alone does not fix density, because
density is a ratio. Lowering turnover helps only because a slower signal captures more gross per unit
of trading. Which leads to the one mechanism that breaks the ratio outright.

---

## 2. The mechanism

**Carry is the only sleeve whose P&L accrues from *holding* rather than from *trading*.** Funding is
settled in cash three times a day to whoever is holding. It enters the numerator of the density ratio
and never touches the denominator. Every other candidate edge in this dataset must pay 7.2 bps to
collect itself; funding does not. Against a gate that is explicitly a density gate charged at 1x, 2x
and 3x, that asymmetry is the whole design, and it is why the refinement makes carry the engine
rather than one of three co-equal sleeves.

The economics (thesis §1.2, citations 1–3): Binance sets
`F = P + clamp(I − P, ±0.05%)` and settles at 00/08/16 UTC — the signal clock *is* the bar clock.
When leveraged long demand pushes the perp above the index, funding becomes a near-linear readout of
the premium crowded longs are paying. It is not an estimate of crowding; it is the settled price of
it. That is the structural difference from the equity factor-timing literature that Asness et al.
found so disappointing, where the conditioning variable is a slow, noisy, *estimated* spread.

**Who is on the other side.** Schmeling, Schrimpf and Todorov (BIS WP 1087) name them: trend-chasing
smaller investors buying leveraged directional exposure on USD-M, facing arbitrage capital that is
constrained by regulatory and margin frictions — concretely, that collateral is USDT sitting outside
the regulated banking perimeter, which a US-regulated fund cannot post at scale. I am paid to
warehouse their leverage demand. I am paid *because* the same BIS paper finds **high carry predicts
future price crashes**: the state in which the flow is richest is the state in which the hazard I am
carrying is largest. He, Manela, Ross and von Wachter show these deviations are shrinking over time —
arbitrage capital is arriving, slowly and incompletely — and Borri et al. document the crypto carry
trade compressing from Sharpe 6.45 to 4.06 and **turning negative in 2025**.

A premium that halves and then changes sign inside five years is the definition of a sleeve whose
weight should not be fixed. That is the mandate.

The other two sleeves exist because their documented failure regimes are close to disjoint from
carry's. Carry fails in the crowded-long unwind; reversal is paid precisely there, by absorbing
liquidation-driven price pressure; trend fails in a third state, choppy whipsaw. Non-overlapping
failure states are the structural precondition for the *rank ordering* of conditional Sharpes to
change across states — which is the only thing that lets a state-allocated book beat a fixed blend.

---

## 3. Three structural changes, and why each is a design change

### 3.1 Every sleeve is averaged to a common effective horizon

`_smoothing_window` gives each sleeve `max(3, H_TARGET − H_k + 1)` bars of **target-vector
averaging** — carry 3, trend 3, reversal 13, toward a common `H_TARGET = 15` bars (5 days).

The averaged vector is deliberately **not renormalised**. A sleeve whose direction does not persist
therefore *shrinks in magnitude* instead of being re-inflated. This is the point: renormalising
restores the rotation speed and with it the entire cost problem. Letting magnitude decay prices a
signal by its persistence, and persistence is exactly what density measures.

This is why the 8h reversal sleeve, which is what a 560-turnover book looks like, cannot dominate the
cost budget here even before the allocator sees it.

### 3.2 The allocator scores sleeves net of the turnover they generate

`_sleeve_net_returns` reconstructs each sleeve's full past-only weight path from the panel, computes
its realised return (price **and** funding), and subtracts `COST_PER_TURNOVER × |Δw|`.

A gross-scored allocator would hand weight to the fastest sleeve for the same reason the seed failed.
`COST_PER_TURNOVER = 15 bps` is set at roughly **2x** the 7.2 bps implied above — a deliberate
conservatism, since the book is graded at 1x, 2x *and* 3x. It is a stated cost assumption, not a
parameter fitted to anything; nothing about it is estimated from the evaluation window.

### 3.3 The state is soft, not a quantile split

The thesis declared `q_split ∈ {0.50, 0.67}` — a hard state boundary. I replaced it with a logistic
membership on a robust standardisation `(x − median) / IQR` over a trailing 180 bars.

Two independent reasons, both structural. A hard boundary makes the whole book jump when the state
variable crosses it, reintroducing turnover at exactly the moment the state is least certain. And a
hard boundary is a razor-thin threshold — precisely what the organizer's small-perturbation stability
check exists to catch. The soft state is strictly better on both counts and does not weaken the
mandate: membership still runs from ~0.27 at Q1 to ~0.73 at Q3, and with `λ = 0.5` a sleeve's
allocation still swings over **[0.167, 0.667]** against the equal-weight 0.333 — a 4x range. The
regime variable has real room to be right or wrong.

### Declared deviations from the Phase-S parameter surface

Recorded so the trial count stays honest:

- `H_carry` **21** bars, outside the declared {1, 3, 9}. Structural: a 3-bar funding mean re-ranks
  the cross-section every day and cannot clear a density gate.
- `q_split` replaced by a **soft logistic membership** (§3.3).
- `W_alloc` = **720 bars rolling**, a compute-bounded stand-in for the declared "expanding".
- **New:** `H_TARGET` (the turnover governor) and `COST_PER_TURNOVER`. These are the refinement.

Unchanged and *not* searched: three sleeves (adding a fourth after seeing a result is the overfit the
preregistration exists to prevent), `H_trend` 45, `H_rev` 3, `W_regime` 180, `λ` 0.50, per-symbol cap
0.10, cross-sectional demeaning, rebalance every bar, universe as given. **No volatility targeting** —
the risk unit is organizer-owned, so the state variable here can only change the book's *composition*,
never its *scale*.

---

## 4. Expected structural profile

| gate | seed | this book (estimate) | why |
|---|---|---|---|
| annualised turnover | 560.6 | **~40–70** | slow signals + target averaging |
| gross edge density | 3.59 bps | **needs > 21.5 bps** | funding accrual enters gross at zero turnover |
| effective breadth | 25.8 | similar | linear rank weights, no top-k selection |
| long / short share | 50/50 | 50/50 | cross-sectional demeaning is exact |
| mean gross | 0.99 | ~1.0 | book normalised to gross 1.0 each bar |

The turnover figure is an **estimate from signal-persistence arithmetic, not a measurement** — my
lane has no market data, no runner and no shell, so I could not execute this code. I hand-traced the
tie-averaging ranker and the constraint enforcement; I could not trace the turnover. Treat ~40–70 as
carrying a factor-of-two uncertainty in either direction. It sits ~13x below the level that failed the
ceiling and ~7x above a static book, which is where I wanted the margin given I cannot measure it.

**The honest weak point.** Density above 21.5 bps depends on the cross-sectional funding spread being
wide enough to matter, and on the funding accrual counting inside "gross edge". If gross edge is
measured on price P&L only, the carry engine does not appear in the numerator and the density gate
will fail again — that is the largest single unknown in this candidate, and t01 cannot resolve it.

---

## 5. What falsifies this

Preregistered in thesis §3. Restated as it applies to this object, and I will report all four
whether or not they favour me.

**F1 — the team brief's falsifier, made operational.** `RA` must beat a fixed equal-weight blend of
the identical three sleeves by **≥ 0.25 annualised Sharpe** on the full visible window, **and by ≥ 0
in each half independently**. `RA` and `EW` hold the same sleeves and are highly correlated, so the
standard error of the *difference* is far below that of either level. The two-halves clause is the
part that costs me: it kills a win that comes from one episode. **If F1 fails I nominate `EW`** — the
leaderboard measures distance from the seed, so conceding the regime variable is a real cost, and I
accept it.

**F2 — the mechanism, which I care about more than F1.** The premise is that sleeve Sharpes
*reorder* across states. Falsified if the arg-max sleeve is the same in every state (the map is
degenerate, there is nothing to rotate into), or if the sign of the within-state best-minus-worst
spread flips between halves in more than one state (the reordering exists but is unstable — the
Cederburg et al. failure). **F2 can fail while F1 passes**; if that happens the F1 pass was luck and I
report the mandate unsupported.

**F3 — contamination, the Asness failure mode.** The state axis is built from funding and the carry
sleeve is built from funding. `RA` could beat `EW` merely by being a nonlinear carry signal — a timing
overlay collapsing into an exposure already in the book. Falsified if `RA` does not beat carry-alone
conditioned on the same state.

**F4 — floor.** Falsified if `RA` does not beat its own best single sleeve.

**Structural falsifier added by this refinement:** if turnover lands outside the band, or density
stays below ~21.5 bps, the mechanism claim in §2 is wrong in a way no reallocation repairs, and I
retire rather than tune. A book that only survives at 1x is not a book.

**Expected shape of a genuine win.** Following Kritzman et al., if this works it should show up more
in drawdown and left-tail reduction than in headline Sharpe. I stated that before the result so that a
Sharpe-only win reads to me as suspicious rather than as confirmation.

---

## 6. Contract and invariance compliance

- `build_strategy()` → object with `target_weights(context, *, seed)`; returns `dict[str, float]`,
  `{}` only when the cross-section is untradable. Symbols come from `context.eligible_symbols` only.
- `sum|w| ≤ 1.0`, `|sum w| ≤ 0.20` (tighter than the 0.25 contract), `|w| ≤ 0.10` — enforced by an
  unconditional gross rescale as the **last** operation in `_finalise`, after the net correction.
- **Panel built on `open_time`**, never the positional `RangeIndex` (RULES.md §"Aligning across
  symbols"); timestamps are converted to UTC epoch-ns so bars and funding share one integer key, and
  unequal symbol histories align rather than landing in disjoint integer ranges. Funding is read from
  **`funding_rate`**, not `last_funding_rate`.
- *Look-ahead:* signals at row `i` use data through `i`; realised returns use `shift(-1)`, so the
  final row is always NaN and is excluded by the `coverage` mask. Nothing beyond the last supplied bar
  is referenced. *Determinism:* no RNG, `seed` unused, no attribute survives a call. *Calendar shift:*
  `decision_time` is never read and every window is positional. *Pseudonymisation:* ties take
  **average** ranks — a plain `argsort` would break under renaming whenever two names share the 0.01%
  baseline funding rate, which is constant. *Magnitude scale:* log-price differences and rank
  transforms only; no price level is referenced. *Perturbation stability:* smooth logistic state,
  linear rank weights, λ-shrinkage — no thresholds to sit on.
- Degradation is explicit, never silent: missing funding leaves the carry sleeve at zero weight and
  the state at neutral 0.5 rather than raising; delisted names are masked by an `alive` gate so a
  forward-filled funding rate can never resurrect a name whose price has stopped.

**Known limitation.** The allocator estimates state-conditional sleeve performance using only
currently-eligible symbols, since the API exposes no other cross-section. That is a mild survivorship
bias in the *allocator's estimate*, not in the traded book. It is unavoidable here and I am recording
it now rather than after a result.
