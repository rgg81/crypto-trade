# team-07 — cointegration convergence, refinement trial

**Family:** cross-sectional mispricing
**Mandate:** rolling pairwise cointegration on log prices, preregistered half-life, divergence stop
**Prior evidence:** `lane/feedback/t01.json` (unmodified organizer seed, visible window, 808 days)

---

## 1. What t01 actually said

The seed failed five gates: `effective_breadth`, `breadth_persistence`, `gross_edge_density`,
`cost_share`, `survives_triple_cost`. They are not five findings. They are one.

| metric | value |
|---|---|
| `median_effective_breadth` | 4.0 |
| `breadth_pass_fraction` | 0.241 |
| `annualised_turnover` | 168.8 |
| `gross_edge_bps_per_turnover` | 5.97 |
| `cost_share_of_positive_gross` | 1.256 |
| `triple_cost_annualised_return` | −0.246 |

Implied cost per unit turnover ≈ 5.97 × 1.256 ≈ **7.5bp at 1x**, so **~22.5bp at 3x**. The bar for
`survives_triple_cost` is therefore roughly a **4x improvement in gross edge per unit turnover**.

The important thing in that table is that `gross_edge_bps_per_turnover` is **positive**. Before
costs, the seed's P&L had the sign the thesis predicts. The mandate's falsifier — *"if
cointegrating relationships do not survive out of the window they were estimated in, there is
nothing to converge to"* — is not what fired. A book with no out-of-window convergence would show
gross edge density near zero, not ~6bp. What t01 refutes is the **expression**: a mechanism worth
~6bp per unit of trading cannot be monetised by a construction that pays 7.5bp per unit of
trading, and the deficit is 3x wider at the triple-cost gate.

### Why this is a design fault and not a parameter fault

The seed expresses the mandate as *a set of discrete pair trades gated on a threshold*: hold pair
(i, j) iff it clears an ADF cutoff **and** |z| ≥ z_in. That construction has two properties that no
setting of my declared Tier-1 grid can remove, because the grid moves them in opposite directions:

- **Breadth is an accident of how many spreads happen to be wide right now.** Four effective
  positions, and the bar met on 24% of bars.
- **Position existence is a step function of a fast statistic**, so every threshold crossing — of
  z *or* of the ADF cutoff — is a full round trip on two legs. 168.8x turnover is a 6.5-bar
  holding period against a preregistered 15-bar half-life: the book traded 2.3x faster than its
  own thesis says the edge decays.

Lower `z_in` → breadth up, turnover up. Raise it → turnover down, breadth collapses. Raise
`N_pairs` → breadth up, screen quality down. `z_stop` and `k` change *when* a position dies, not
how many exist or how often they flip. There is no admissible point on the declared grid where
breadth clears the bar **and** edge density reaches ~22bp. Hill-climbing here would buy a search
statistic, not an edge.

---

## 2. The redesign

**The pair is the estimator, not the position.**

Cointegration is used to construct, for each symbol, a continuous relative-value score against its
cointegrated peer set. The *book* is the cross-sectionally demeaned, symbol-level portfolio over
the whole eligible universe. Three changes, each of which attacks both failures with the same sign.

### 2.1 Continuous response instead of a gate

Weight is linear in −z up to `Z_STOP`, then tapered to flat by `Z_KILL`. This is not a softening
for its own sake: under the OU dynamics the mandate preregisters, the conditional drift of the
spread *is* proportional to −z, so a threshold is a strictly worse estimator of the conditional
mean as well as a turnover generator. Thresholding throws away the distinction between z = 2.0 and
z = 2.9 and then charges two legs of commission for the crossing between them.

### 2.2 Continuous screens instead of admission tests

ADF t-statistic, β plausibility, partner correlation, excursion age, the idiosyncratic-event veto
and the funding carry are all multipliers in [0, 1]. A pair whose t-statistic wanders across τ now
changes size by a few percent rather than flipping between full size and flat. This removes
**pair-set churn**, which I believe was the larger of the seed's two turnover sources, since it
generates round trips for reasons that have nothing to do with the spread having moved.

### 2.3 Aggregate to symbols and net

A symbol's score is the evidence-weighted mean of the signed residuals of every pair it appears in,
shrunk toward zero by the amount of evidence behind it. Offsetting legs across pairs cancel
**before** they are traded. This is the one move that raises breadth and cuts turnover
simultaneously — 5 partners per symbol across a few hundred names is thousands of pairwise
estimates collapsed into one diversified cross-section, rather than twenty concentrated bets.

Breadth stops being an accident: with a per-name cap of 0.030 against gross 1.0, the book holds at
minimum ~34 names, in practice several times the seed's effective 4, on *every* bar where the
window is populated — which is what `breadth_persistence` measures.

### 2.4 Turnover, explicitly

Four levers, in order of expected size:

1. **No threshold crossings** (§2.1) and **no pair-set churn** (§2.2).
2. **Netting at the symbol level** (§2.3).
3. **H = 30 bars** (10 days), the long end of the declared Tier-1 range, forcing W = 180 by the
   Tier-0 coupling W ≥ 6H. The seed asked a multi-day mechanism to pay for 2.3x-faster trading.
4. **The residual is measured, not sampled.** z is the frozen-β spread averaged over the last 6
   bars (H/5) and then standardised. For a half-life of 30 bars this costs ~7% of signal amplitude
   and removes roughly a factor of √6 of bar-to-bar noise from the target vector — a direct,
   favourable trade of edge for turnover.

I am explicit that this is where the candidate lives or dies: it must move gross edge per unit
turnover from ~6bp to ~22bp+. Levers 1–3 are structural and I expect the bulk from them; lever 4
is the only one that trades signal for cost, and it is sized by H rather than chosen freely.

---

## 3. The stop — the hard part of the mandate

The mandate names the stop as the difficult piece, and the reason is real: **under a true OU, a
spread at 4σ is a better entry than one at 2σ.** A distance stop is only correct if distance is
evidence that the *relationship broke*, not evidence that the opportunity grew. So the stop is
three stops, and only one is a loss stop. All three are stateless — functions of the rolling window
alone, never of when a position was opened — which is required, and which also means a stop can
never drift out of sync with the book.

- **S1 — excursion age (primary, model invalidation).** Bars since the residual last crossed its
  in-window mean. Because the regression carries an intercept, the residual has exactly zero mean
  in-window, so the crossing is well defined. Full size to 3H = 90 bars, ramping to flat at 180.
  An excursion that has survived three preregistered half-lives should have decayed 87.5%; if it
  has not, the preregistered model is wrong *for that pair*, and that is a statement about the
  model rather than about P&L.
- **S2 — relationship invalidation.** The ADF ramp, the β plausibility band and the partner-
  correlation ramp are recomputed every decision. A relationship that stops looking like one is
  wound down continuously.
- **S3 — divergence stop (the loss stop).** `|z| ≥ Z_STOP = 3.0` is the peak of the response; from
  there it ramps linearly to flat at `Z_KILL = 4.0`. Something has to close the ~38% of pairs that
  never converge.

**The design point:** in a stateless continuous book the stop must be a *shape of the response
function*, not an event. A hard exit at z_stop reintroduces exactly the step this redesign exists
to remove — it would round-trip two legs every time a diverging spread jittered across 3.0. The
taper is a genuine stop (the position is flat beyond 4σ) that is Lipschitz in z, so its cost is
bounded by how far the spread actually moved.

Alongside it, the **idiosyncratic-event veto**: a single-bar move on either leg exceeding 5–8x that
leg's trailing dispersion ramps the pair to zero. News is a permanent relationship break, not a
temporary excursion, and this is the observable shadow of the unlocks, listings and liquidation
cascades I cannot see directly. It vetoes entry and forces exit; it can never size a pair up.

---

## 4. Who is on the other side

Unchanged from the preregistration, and worth restating because it is what justifies the sign.

- **Leveraged retail being liquidated.** Forced liquidation is price-insensitive, concentrated in
  one contract, and mechanically overshoots. When a token-specific cascade moves one leg double
  digits without moving its economic peers, whoever takes the other side is compensated.
- **Funding-carry and basis desks.** They size the perp short leg *by funding*, not by relative
  value. When funding on one name spikes they short that specific perp — pushing it below its peers
  for a reason unrelated to its relative fundamentals — and unwind when funding normalises. Their
  flow is mean-reverting by construction.
- **Rotation and narrative flow**, and **market makers laying off inventory** after absorbing
  one-sided flow in a single contract.

The premium is compensation for **divergence risk** — being short an option on relationship
stability — and secondarily for liquidity provision. None of these flows are observable in the
dataset; they are the reason the residual exists and should decay, not a signal. Inputs are log
closes, `quote_volume` and `funding_rate`, nothing else.

Funding enters only as a **veto**: a pair whose expected net 8h carry over one half-life would eat
more than the expected convergence gain is damped to zero. The multiplier is clipped at 1, so it can
only ever reduce a pair's size. This is deliberate — sizing by funding would be a different family.
At H = 30 bars the carry term is second-order against a 60-day spread's dispersion, so I expect it
to bind rarely; it exists for the regimes where it does not.

---

## 5. Declared-surface accounting, honestly

**Moved, within Tier 1 (declared):** `H` 15 → **30** (long end of {6, 15, 30}), which forces
W = 180 through the Tier-0 coupling W ≥ 6H. `k` 2 → **3**, matched to the longer half-life.
`z_stop` held at the declared centre 3.5 in spirit but **implemented as a 3.0 → 4.0 taper**, whose
midpoint is the declared centre. `z_in` and `N_pairs` no longer exist as knobs — the redesign
deletes them, which is the point.

**Tier-2 knobs opened, with their preregistered triggers actually fired:**

- **13 `liq_floor` = 0.25** (the declared default). Trigger: *"only if participation or cost-share
  gates fail."* `cost_share` failed.
- **7 `τ`.** Trigger: *"only if the screen admits fewer than `N_pairs` candidates at a majority of
  decisions."* `breadth_pass_fraction = 0.241` is that condition, measured. The response is **not**
  to move τ to −2.6; it is to replace the cutoff with a ramp over −1.8 → −3.2, which brackets the
  entire declared band {−2.6, −3.0, −3.4}.
- **9 `m` = 5**, **10/15 (breadth)**: superseded — breadth is now set by the cross-section rather
  than by a pair count, so `m_max` and `pair_weighting` are not used.
- **14 `funding_veto` = on** (declared default).
- **11 `e`**: the event veto is on at its declared default of 8, implemented as a 5 → 8 ramp.

**Deviations I have to declare as such.** Per §5 of the thesis — *"if I find during Phases 1–3 that
I need a parameter that is not on this list, the honest report is that the preregistration was
incomplete, and I will say so"*:

1. `SMOOTH = H/5 = 6 bars`, the trailing span over which the frozen-β residual is averaged before
   standardising. The preregistration declared thresholds *on* z but never declared how z is
   measured in time; it implicitly assumed a single last observation. It is tied to H by
   construction and is not searched.
2. The **ramp endpoints** replacing each hard cutoff, and the **β plausibility band** (0.2/0.4 —
   2.5/4.0), which the preregistration did not contain at all.
3. `SHRINK`, `SOFT_FLOOR`, `MAX_WEIGHT` — book-construction constants that only exist because the
   book is now a cross-section rather than a pair list.

None of these were tuned against feedback; there is one feedback packet and it contains no
per-parameter information. They are consequences of the gates→ramps redesign. **Trials evaluated
against feedback so far: 1** (the unmodified seed). This candidate is the second.

---

## 6. What would falsify this

Stated before the result, and separated so that a single number cannot be read as vindicating the
whole design.

- **The mechanism.** `gross_edge_bps_per_turnover` at or below ~6bp again, *despite* turnover
  falling substantially. That would mean the edge scales down exactly with the trading — i.e. the
  seed's positive gross edge was the fast, threshold-crossing component and there is nothing slow
  to hold. That is the mandate's falsifier arriving at last: the cointegrating relationship does
  not survive out of the window it was estimated in, on the horizon I am now trading. Under my
  preregistration this retires the mandate; I do not go looking for a shorter H, because
  Fil & Kristoufek locate the effect at 5 minutes and one hour and I cannot reach either.
- **The redesign.** Turnover *not* falling materially below 168x. Then netting, ramps and the
  6-bar measurement did not do what I claim they do, and my diagnosis of t01 was wrong.
- **The construction.** `effective_breadth` or `breadth_persistence` failing again. With a 0.030
  per-name cap those are close to arithmetically guaranteed, so a failure means the book is not
  being built at all — most likely the panel is collapsing and I am returning `{}`. That is an
  implementation bug, not a finding, and I would treat it as one.
- **The cost gate specifically.** `survives_triple_cost` still failing while edge density lands in,
  say, 12–18bp. That is the genuinely ambiguous outcome: the redesign worked directionally and the
  mechanism is simply too thin for this venue's cost floor at 3x. The honest report is then that
  the family is present and unmonetisable at the required cost multiple, and I would say so rather
  than search for the parameter that squeaks over the line.

I expect a **modest** result if the design is right. Krauss's survey puts pairs trading at ~10.8%
annualised and Sharpe ≈ 0.96 across 76 studies, decaying to 6.4% post-2010, and PwC has 31% of
digital-asset hedge funds running market neutral. A large measured effect here would be a red flag,
not a success.

---

## 7. Interface compliance

- `build_strategy()` returns an object with `target_weights(context, *, seed)`.
- The panel is built on **`open_time`**, never on the positional `RangeIndex`.
- Returns `dict[str, float]` over `context.eligible_symbols`, or `{}` while the 180-bar window is
  unpopulated. Never `None`.
- `sum(abs(w)) ≤ 1.0`, `abs(sum(w)) ≤ 0.25` (the book is demeaned, so net is ~0 by construction),
  `abs(w) ≤ 0.030` against the 0.10 cap.
- Reads only `close`, `quote_volume`, `open_time` from `bars` and `symbol`/`funding_rate`/
  `funding_time` from `funding`.
- **No volatility targeting.** Nothing conditions on realised or forecast portfolio volatility; the
  book is normalised to unit gross and handed to the organizer's risk unit.
- Stateless, deterministic, no RNG, no I/O, no `eval`/`exec`/`getattr`, no embedded data. `seed` is
  accepted and unused.
- **Scale invariance** is structural: log prices are column-centred, which absorbs the
  Engle–Granger intercept, so `P → cP` leaves β̂ and every residual untouched. The liquidity filter
  is a cross-sectional percentile, so it is invariant too.
- **No symbol identity** anywhere — symbols are dict keys only. **No absolute dates and no
  time-of-day conditioning**, so calendar shift is satisfied; I decline the 00:00/08:00/16:00
  funding clock deliberately for this reason.
- **Small-perturbation stability** is the design: every screen is a ramp and the response is
  piecewise linear, so there is no threshold whose crossing changes the book discontinuously.
