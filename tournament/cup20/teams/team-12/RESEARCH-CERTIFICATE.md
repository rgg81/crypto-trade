# CUP-20 — Team 12 research certificate

**Lane:** preregistered multi-sleeve ensemble (≥3 orthogonal causal bases, a-priori weights).
**Nominee:** `candidates/mse-01` — four sleeves, inverse-volatility weighting, cadence 6, phase 3.
**Accepted trials:** 11 of 12 (journal sequences #121–#131). `T` for the multiplicity charge = **2**
(one `point`, one `neighbourhood`); eight `ablation` trials and one `falsification` trial are exempt
under amendment A6.

**SCORE (neighbourhood median, §5.1): `G` = 84.267.** Every hard floor PASS on the median;
`positive_point_fraction` 1.000 (9 of 9); trial-adjusted confidence 0.9920. Falsification (§6):
the exact sign inversion fails six of the eight core floors, and the gross-edge placebo exceedance
is 0.0000.

---

## 0. The one-paragraph answer

Four mechanisms on genuinely different causal bases — funding crowding, price trend, risk
characteristics and aggressive taker flow — were combined at a-priori equal risk, with the weight
rule written into the organiser's hash-chained journal at **sequence #121, before any combined book
of this team had been computed anywhere**. The combination beat every one of its own components on
the ranking score, and it beat its best single component on maximum drawdown, on Calmar, on median
fold Sharpe, on positive-quarter fraction and on every measure of how long the book stays underwater
— but **not** on worst-fold Sharpe at the nominated phase. The mechanism under test is
diversification itself, and the honest verdict is that on this window it diversified **drawdown
shape** (depth, duration, quarterly consistency) rather than **volatility**: the organiser's common
risk unit re-scales every book to roughly the same realised volatility, so the correlation benefit
cannot show up there and shows up instead in the shape of the equity curve. That distinction is the
substantive result. The decisive control is the other leave-one-out: **delete the best sleeve
entirely and the remaining three-sleeve combination still scores `G` 74.29**, thirty points above
the best sleeve left in it — the ensemble is not its strongest member wearing a coat. A second
leave-one-out shows the *weakest* sleeve cost the book about 7 points of `G`; it was **not**
removed, because removing a sleeve after seeing a combined result is re-weighting under another
name and this lane forbids it.

---

## 1. Preregistration — what was fixed, when, and where it is recorded

### 1.1 The weight rule, verbatim

Journaled at **sequence #121** (kind `ablation`, candidate `abl-baseline-ew`), before the first
combined book existed:

> **Inverse-volatility (naive risk-parity) sleeve weighting.** At every decision boundary `t`, each
> sleeve `k` emits a weight vector over the eligible symbols normalised to unit gross
> (`Σ_i |w_k,i(t)| = 1`). Sleeve `k`'s contribution to the combined book is that unit-gross vector
> multiplied by `1/σ_k(t)`, where `σ_k(t)` is the sample standard deviation (ddof=1) of sleeve `k`'s
> own past-only proxy return series over the most recent `RISK_PARITY_BARS` observations attributed
> to boundaries strictly before `t`. The proxy return attributed to boundary `g` is
> `x_k(g) = Σ_i w_k,i(g-1) · (close_i[g-1]/close_i[g-2] − 1)`, the sleeve's own unit-gross weight
> vector formed at the previous boundary applied to the close-to-close simple return of the bar that
> closed at `g`, with no costs, no funding and no leverage. Until `RISK_PARITY_BARS` such
> observations exist, or if `σ_k(t)` is not finite and strictly positive, sleeve `k` receives the
> multiplier 1. The combined book is the plain sum of the scaled sleeve vectors, returned
> unnormalised; the evaluator's own unit-gross normalisation then applies. **No other sleeve-level
> multiplier, tilt, cap, floor, sign flip, correlation adjustment or performance-conditioned term of
> any kind is applied, at any boundary, ever.**

`RISK_PARITY_BARS = 270` (90 days on the 8h grid), fixed a priori to match the organiser's own
common-risk-unit lookback of 90 days (charter §6), not selected from any result. The same journal
record fixes the four sleeves, the cadence (6) and the phase (3).

**Naive inverse volatility, not a full equal-risk-contribution solve, deliberately.** The
cross-sleeve correlation matrix is the channel through which a combination learns from the answer.
A rule that consumes it would tilt toward whatever happened to diversify in sample. Naive risk
parity is the version of "equal risk" that cannot learn from the result it is being scored on.

### 1.2 The prediction registered with the rule

Also at #121, before any combined number:

> If independent mechanisms diversify each other's drawdowns here, the equal-risk combination shows
> a **lower maximum drawdown and a higher worst-fold Sharpe** than its own best single sleeve. If
> instead its drawdown merely sits between the sleeves', the sleeves shared a factor and
> diversification did nothing, and that is the result to report.

**Outcome: half-confirmed, and reported as such** — see §4.

### 1.3 What was *not* preregistered, stated plainly

Sleeve **design** was iterated freely before #121 (the mandate permits this explicitly). Sleeve
lookbacks, measures and the cadence were chosen from standalone, phase-averaged offline evidence.
Two candidate sleeves were **falsified and dropped before #121** (§6). What was frozen at #121 and
never touched afterwards is the *combination*: the rule, its parameter, and the membership of the
sleeve set.

---

## 2. The four sleeves — causal argument first, then the empirical check

| Sleeve | Causal base | Construction (all past-only) | Gross share in the executed book |
|---|---|---|---:|
| **CARRY** | The perpetual funding mechanism is a cash transfer from the crowded side to the uncrowded side. A name paying persistent positive funding is one whose longs are paying to stay long. | cross-sectional rank of the trailing 126-boundary mean funding rate, sign flipped; dollar-neutral | 31.5% |
| **TREND** | Information diffuses slowly across a fragmented, 24/7, largely retail participant base, and leverage makes the diffusion reflexive. | per-coin time-series momentum over 45/90/135 boundaries, sign-averaged and divided by the name's own 90-bar realised volatility; **net exposure is a free variable** | 9.6% |
| **LOWRISK** | Leverage-constrained and lottery-seeking participants overpay for the wild names, so risk is priced too cheaply at the calm end of a blue-chip cross-section. | cross-sectional rank of trailing log-drawdown depth over 189/378/567 boundaries, sign flipped; dollar-neutral | 26.9% |
| **FLOW** | Aggressive, price-insensitive demand has to cross the spread, and leaves a persistent footprint in the buy/sell split of traded volume that price alone does not carry. | cross-sectional rank of the trailing mean taker-buy share of quote volume over 63/126 boundaries; dollar-neutral | 31.0% |

**Why these are four bases and not three momentum horizons wearing hats.** They read four different
objects: a *cash flow* (funding), a *price path* (trend), a *risk characteristic* (drawdown depth)
and a *volume composition* (taker split). Three of the four are dollar-neutral cross-sections and
one is directional; three are cross-sectional selectors and one is a time-series timer. The trend
sleeve is the only one whose net exposure moves, and it is the only one that can be short the market
as a whole.

### 2.1 Where the causal argument and the data disagree

Pairwise correlation of the four standalone books' daily net returns (each already at the common
risk unit, 1× cost, cadence 6 phase 3):

|          | carry | trend | lowrisk | flow |
|---|---:|---:|---:|---:|
| carry    | 1.000 | 0.000 | 0.065 | **0.383** |
| trend    | 0.000 | 1.000 | 0.148 | 0.124 |
| lowrisk  | 0.065 | 0.148 | 1.000 | **0.396** |
| flow     | 0.383 | 0.124 | 0.396 | 1.000 |

Two disagreements, both worth stating:

- **Causally distinct, empirically aligned:** CARRY and FLOW correlate +0.383, and their *underwater*
  series correlate **+0.599**. Funding and taker-buy share are different measurements, but on a
  20-name universe both end up expressing "which coins are being bought with conviction", and they
  are underwater together. The causal argument overstates their independence.
- **Causally similar-sounding, empirically opposed:** TREND is *negatively* correlated with every
  other sleeve in drawdown (carry −0.387, lowrisk −0.295, flow −0.406), despite a mildly positive
  return correlation. The one directional sleeve is the one that is up when the cross-sections are
  down. Return correlation understates how much it contributes.

Correlation-implied diversification ratio at the realised risk shares:
`sqrt(sᵀRs)/Σs = 0.673`, against 1.000 for perfectly correlated sleeves and 0.532 for perfectly
independent ones — the sleeve set captured **70% of the way to full independence**.

### 2.2 Regime role check (up / chop / down thirds of the 48 in-sample months)

Annualised Sharpe of each book within each market third, market state defined by the equal-weight
eligible basket's monthly return:

| book | up | chop | down |
|---|---:|---:|---:|
| **ENSEMBLE** | **+0.38** | **+1.19** | **+2.24** |
| carry | +0.44 | −0.91 | +1.61 |
| trend | +2.38 | −0.90 | +0.77 |
| lowrisk | −1.75 | **+3.15** | +1.51 |
| flow | +0.44 | +1.40 | +2.08 |

Every sleeve except FLOW has a regime in which it loses money. The ensemble has none. TREND and
LOWRISK are near-exact regime complements (+2.38/−1.75 in up, −0.90/+3.15 in chop), which is the
causal orthogonality argument showing up where it should.

**Long / short / chop roles.** Declared roles `long,short`; observed roles `long,short`; gate
`declared_roles_match_traded_sides` **PASS**. Both sides are gross-positive at 1× cost —
`long_gross_pnl = +0.611`, `short_gross_pnl = +0.083` — which is not free on this window: charter
§14.9 records that an equal-weight top-20 basket summed **+1.99** in simple returns over the same
4335 bars, so a diversified short sleeve has arithmetic against it. The book clears the floor
because the directional TREND sleeve carries the short side through the bear phases; the two
dollar-neutral sleeves CARRY (−0.077 standalone) and LOWRISK (−0.060 standalone) are individually
gross-negative on the short side, and say so in their own ablation packets.

**Net exposure** of the executed ensemble: mean −0.012 of gross, sd 0.140, 5th/95th percentile
−0.197/+0.198. The book is dollar-neutral on average with a small time-varying tilt supplied
entirely by the 9.6% of gross that TREND carries.

---

## 3. Results — organiser-scored, every number from a packet under an accepted trial

All rows are full-window in-sample runs at the common risk unit. `G` is the indicative ranking score
of the point; the nominee's *score* is the neighbourhood median in §5.

| candidate | seq | kind | G | Sh 1× | Sh 2× | maxDD 1× | maxDD 2× | worst fold 2× | median fold 2× | Calmar 2× | +qtr 2× | vol | turnover | trades |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `abl-baseline-ew` (transparent baseline) | #121 | ablation | −17.06 | 0.167 | 0.159 | 0.316 | 0.317 | −0.440 | 0.053 | 0.03 | 0.53 | 0.242 | 2.78 | 17525 |
| `abl-sleeve-carry` | #122 | ablation | −3.13 | 0.383 | 0.276 | 0.212 | 0.217 | −0.300 | 0.372 | 0.12 | 0.47 | 0.119 | 16.92 | 17540 |
| `abl-sleeve-trend` | #123 | ablation | 27.90 | 0.720 | 0.627 | 0.124 | 0.137 | −0.945 | 0.982 | 0.69 | 0.59 | 0.166 | 20.66 | 17022 |
| `abl-sleeve-lowrisk` | #124 | ablation | 43.66 | 0.867 | 0.795 | 0.153 | 0.156 | +0.171 | 0.806 | 0.60 | 0.65 | 0.123 | 11.81 | 17348 |
| `abl-sleeve-flow` **(best single sleeve)** | #125 | ablation | 83.12 | 1.304 | 1.175 | 0.123 | 0.126 | **+0.767** | 1.231 | 1.09 | 0.76 | 0.116 | 19.79 | 17243 |
| `abl-equal-notional` (rule removed) | #126 | ablation | 70.29 | 1.292 | 1.194 | **0.076** | 0.079 | −0.070 | 1.351 | 1.94 | 0.82 | 0.127 | 16.64 | 17125 |
| `abl-drop-carry` (leave-one-out, weakest sleeve) | #127 | ablation | 91.91 | 1.347 | 1.245 | 0.098 | 0.101 | +0.774 | 1.363 | 1.62 | 0.82 | 0.129 | 17.49 | 17047 |
| `abl-drop-flow` (leave-one-out, **strongest** sleeve) | #131 | ablation | 74.29 | 0.985 | 0.882 | 0.106 | 0.107 | +0.381 | 0.968 | 1.04 | 0.94 | 0.129 | 17.87 | 17185 |
| **`mse-01` NOMINEE** | **#128** | **point** | **85.02** | **1.294** | **1.193** | **0.115** | **0.118** | **+0.632** | **1.268** | **1.29** | **0.94** | **0.126** | **17.01** | **17126** |

Fold Sharpes at 2× cost:

| book | F1 | F2 | F3 | F4 | positive |
|---|---:|---:|---:|---:|---:|
| baseline EW long | 0.353 | −0.440 | −0.246 | 1.015 | 2/4 |
| carry | 0.180 | 0.694 | −0.300 | 0.565 | 3/4 |
| trend | 0.844 | 1.121 | −0.945 | 1.243 | 3/4 |
| lowrisk | 1.337 | 0.171 | 1.346 | 0.274 | 4/4 |
| flow | 1.040 | 1.422 | 0.767 | 1.447 | 4/4 |
| equal-notional | 1.811 | 1.273 | −0.070 | 1.428 | 3/4 |
| drop-carry | 1.440 | 1.344 | 0.774 | 1.382 | 4/4 |
| drop-flow | 1.077 | 1.180 | 0.381 | 0.859 | 4/4 |
| **ENSEMBLE (nominee)** | **1.336** | **1.574** | **0.632** | **1.200** | **4/4** |

### 3.1 Every hard floor at the nominated point (packet #128)

No measured failure. `net_sharpe` 1.294 ≥ 0.80 · `double_cost_sharpe` 1.193 ≥ 0.50 ·
`triple_cost_sharpe` 1.092 > 0 · `annualized_return` 0.168 > 0 · `double_cost_annualized_return`
0.153 > 0 · `max_drawdown` 0.115 ≤ 0.20 · `annualized_volatility` 0.126 ≥ 0.06 (substance gate) ·
`positive_quarter_fraction` 0.941 ≥ 0.50 · `positive_fold_count` 4 ≥ 3 · `worst_fold_sharpe` 0.632 ≥
−0.25 · `annualized_turnover` 17.01 ≤ 25 · `gross_edge_bps_per_turnover` 102.9 ≥ 40 ·
`cost_share_of_positive_gross` 0.0093 ≤ 0.30 · `top5_day_share` 0.033 ≤ 0.35 ·
`max_fold_positive_pnl_share` 0.324 ≤ 0.60 · `trade_count` 17126 ≥ 500 (substance gate) ·
`trial_adjusted_confidence` (at T=1) 0.996 ≥ 0.90 · `declared_roles_match_traded_sides` PASS ·
`role_long_gross_pnl` +0.611 > 0 · `role_short_gross_pnl` +0.083 > 0.

Exposure caps: `executed` 0 of 722 boundaries reduced; `requested` 2 of 722 reduced, minimum scale
0.9920, per-symbol cap binding. The book is essentially untrimmed, so §14.7's concentration
handicap does not apply to it. Risk-unit scalar median 0.4615, minimum 0.2347, maximum 1.0000 —
interior throughout, never pinned to the 0.20 floor and never near the 3.0 ceiling, so the book's
realised volatility is the risk unit's choice rather than a clamp artifact.

---

## 4. Did the sleeves diversify drawdown, or merely average returns?

This is the lane's actual question, so it gets its own section and a precise answer.

### 4.1 The ensemble against each sleeve standalone and against the best single sleeve

Against the **best single sleeve** (FLOW, `G` 83.12), the nominee is:

| | ensemble | FLOW alone | verdict |
|---|---:|---:|---|
| ranking score `G` | **85.02** | 83.12 | ensemble better |
| max drawdown 1× | **0.1148** | 0.1230 | ensemble better — *prediction met* |
| max drawdown 2× | **0.1183** | 0.1262 | ensemble better |
| worst fold Sharpe 2× | 0.632 | **0.767** | **FLOW better — prediction NOT met** |
| median fold Sharpe 2× | **1.268** | 1.231 | ensemble better |
| Calmar 2× | **1.29** | 1.09 | ensemble better |
| positive-quarter fraction 2× | **0.94** | 0.76 | ensemble better |
| net Sharpe 1× | 1.294 | **1.304** | FLOW marginally better |
| positive quarters (1×, 17 quarters) | **16** | 14 | ensemble better |

Against every **other** sleeve the ensemble dominates on every one of those rows.

And the converse test, which is the one that decides whether the combination is doing the work:
**with FLOW deleted altogether** (#131) the three remaining sleeves — individually `G` 43.66, 27.90
and −3.13 — combine at the same preregistered rule to `G` **74.29**, Sharpe 0.985 at 1× cost,
drawdown 0.106, four folds positive and 16 of 17 quarters positive. Thirty points of `G` above the
best component it contains. Whatever the ensemble is, it is not FLOW with three passengers.

The registered prediction asked for *both* a lower drawdown and a higher worst fold. It got the
first and missed the second at the nominated phase. That miss is a property of the nominated phase
rather than of the mechanism: averaged over all six rebalance phases at cadence 6 on the offline
replica, the ensemble's worst-fold Sharpe is **+0.787** against FLOW's **+0.688**, and the nominee's
phase 3 is the ensemble's weakest phase for that statistic (0.632, against 0.85 at phase 0 and 0.90
at phase 2). The nominee was not moved to a better phase, because phase 3 was journaled with the
rule at #121 and moving it afterwards is exactly the tuning this lane exists to exclude. It is
declared as a neighbourhood coordinate instead, so the sweep prices the phase choice rather than
hiding it.

### 4.2 Drawdown *shape*, which is where the diversification actually landed

Fraction of days spent underwater by more than a given depth (common risk unit, 1× cost — every book
below is at roughly the same realised volatility, so this is a matched-risk comparison):

| depth | ENSEMBLE | carry | trend | lowrisk | flow |
|---|---:|---:|---:|---:|---:|
| > 2% | **0.513** | 0.842 | 0.829 | 0.781 | 0.574 |
| > 5% | **0.116** | 0.656 | 0.509 | 0.520 | 0.271 |
| > 8% | **0.029** | 0.433 | 0.268 | 0.236 | 0.114 |
| > 10% | **0.010** | 0.272 | 0.149 | 0.089 | 0.054 |

Longest continuous underwater run, in days: **ENSEMBLE 179**, flow 409, lowrisk 393, trend 564,
carry 677.

At each sleeve's own worst moment the ensemble is roughly half as deep or less:

| sleeve | its own trough | ensemble underwater at that instant |
|---|---:|---:|
| carry | −0.212 (2021-01-06) | −0.098 |
| trend | −0.124 (2023-10-21) | −0.006 |
| lowrisk | −0.153 (2024-03-09) | −0.079 |
| flow | −0.123 (2021-02-13) | −0.066 |

Positive quarters out of 17 (1× cost): ENSEMBLE 16, flow 14, trend 11, lowrisk 11, carry 8.

### 4.3 The honest qualification: the risk unit hides the volatility channel

The naive test — "is the combined book's volatility below the risk-weighted average of the sleeves'
volatilities" — returns **0.970**, i.e. essentially no benefit. That number is an artifact and
should not be read as evidence against diversification. Every book in this tournament is rescaled by
the common risk unit toward the same 10% ex-ante target, so a correlation benefit cannot appear as
lower realised volatility; it is spent on gross exposure instead. The un-rescaled, correlation-
implied ratio is **0.673** (§2.1), a real 33% volatility reduction, and the risk unit converts it
into a book that runs at 0.46× gross where FLOW alone runs at 0.55× and still reaches the same 12.6%
realised volatility.

**So: the sleeves did diversify, and the diversification is visible in drawdown depth, drawdown
duration and quarterly consistency rather than in volatility.** What it did *not* do on this window
is improve the single worst 12-month block beyond what the best sleeve already achieved. Both halves
are the result.

### 4.4 What would have shown the sleeves *not* diversifying, and was checked for

Pre-stated in §1.2 and checked: an ensemble drawdown that sits *between* the sleeves' drawdowns
rather than below the best of them; a common worst fold shared by all four; and joint deep-drawdown
occupancy near the marginal rate. Measured: the ensemble's F3 (0.632) is its weakest fold and F3 is
also the weakest fold for carry (−0.300) and trend (−0.945) and flow (0.767) — so there *is* a
shared weak block, and it is the 2022-08 → 2023-08 post-FTX trough. The residual common factor is
real and named. Joint deep-drawdown occupancy (both books >5% underwater at once) is 0.264 for
carry+flow but only 0.051 for trend+flow — the pair whose causal argument said they were
independent is the pair that behaves independently.

---

## 5. The declared neighbourhood and its sweep

**Nominee fixed at #121 and #128, before the neighbourhood was declared at #129.** Coordinates were
chosen to be the ones most able to embarrass the result, not the flattest:

- `REBALANCE_PHASE` = 3 → points 1, 5. Phase is a first-order axis for any cadence above one bar
  (charter §9.1) and the nominee's phase is its *weakest* for worst-fold Sharpe.
- `RISK_PARITY_BARS` = 270 → points 180, 360. This is the combination rule's own parameter, so the
  sweep tests directly whether the answer depends on the exact sleeve weights or on the sleeves.
- `FLOW_BASE_LOOKBACK` = 63 → points 48, 80. The formation horizon of the strongest sleeve.
- `LOWRISK_BASE_LOOKBACK` = 189 → points 150, 231. The jumpiest standalone surface of the four.

k = 4 coordinates, 9 points including the nominee (≥ max(7, 2k+1) = 9). Every point distinct, every
coordinate varied materially above and below, every coordinate a single-valued module-level numeric
literal in the frozen `strategy.py`, and all nine verified to rewrite cleanly by the free `--check`
before the trial was journaled.

### 5.1 The sweep result — **this is the score**

`cup20_evaluate.py --neighbourhood`, 9 points, 9 workers, 1492.6 s wall clock. Every point
materialised as a separate file out of the frozen source and executed in its own fresh interpreter;
nine distinct `strategy.py` digests are on the record in the packet.

| point | coordinates changed | Sharpe 1× | Sharpe 2× | ann. return | maxDD 1× |
|---|---|---:|---:|---:|---:|
| nominee | — | 1.2944 | 1.1931 | 0.1680 | 0.1148 |
| 1 | `REBALANCE_PHASE` 3 → 1 | 1.1832 | 1.0812 | 0.1523 | 0.1156 |
| 2 | `REBALANCE_PHASE` 3 → 5 | 1.2876 | 1.1875 | 0.1666 | 0.1007 |
| 3 | `RISK_PARITY_BARS` 270 → 180 | 1.3342 | 1.2348 | 0.1744 | 0.1143 |
| 4 | `RISK_PARITY_BARS` 270 → 360 | 1.3339 | 1.2324 | 0.1734 | 0.0938 |
| 5 | `FLOW_BASE_LOOKBACK` 63 → 48 | 1.2091 | 1.1021 | 0.1550 | 0.1224 |
| 6 | `FLOW_BASE_LOOKBACK` 63 → 80 | 1.2732 | 1.1750 | 0.1643 | 0.1248 |
| 7 | `LOWRISK_BASE_LOOKBACK` 189 → 150 | 1.2277 | 1.1248 | 0.1575 | 0.1140 |
| 8 | `LOWRISK_BASE_LOOKBACK` 189 → 231 | 1.2643 | 1.1627 | 0.1616 | 0.1173 |

**Per-metric median across the nine points — the number the organiser ranks on:**

| metric | median | floor | |
|---|---:|---|---|
| `net_sharpe` (1×) | **1.2732** | ≥ 0.80 | PASS |
| `double_cost_sharpe` (2×) | **1.1750** | ≥ 0.50 | PASS |
| `triple_cost_sharpe` (3×) | **1.0766** | > 0 | PASS |
| `annualized_return` (1×) | **0.1643** | > 0 | PASS |
| `double_cost_annualized_return` | 0.1500 | > 0 | PASS |
| `max_drawdown` (1×) | **0.1148** | ≤ 0.20 | PASS |
| `double_cost_max_drawdown` (2×, ranking input) | **0.1183** | — | — |
| `annualized_volatility` (1×) | **0.1258** | ≥ 0.06 **substance** | PASS |
| `positive_quarter_fraction` (1× and 2×) | **0.9412** | ≥ 0.50 | PASS |
| `positive_fold_count` (2×) | **4** | ≥ 3 | PASS |
| `worst_fold_sharpe` (2×) | **0.6415** | ≥ −0.25 | PASS |
| `median_fold_sharpe` (2×) | **1.2398** | — | — |
| `calmar` (2×) | **1.2186** | — | — |
| `annualized_turnover` (1×) | **17.01** | ≤ 25 | PASS |
| `gross_edge_bps_per_turnover` (1×) | **102.94** | ≥ 40 | PASS |
| `cost_share_of_positive_gross` (1×) | **0.0093** | ≤ 0.30 | PASS |
| `top5_day_share` (1×) | **0.0330** | ≤ 0.35 | PASS |
| `max_fold_positive_pnl_share` (1×) | **0.3228** | ≤ 0.60 | PASS |
| `trade_count` (1×) | **17124** | ≥ 500 **substance** | PASS |
| `long_gross_pnl` / `short_gross_pnl` (1×) | **+0.6048 / +0.0741** | each > 0 | PASS |
| `positive_point_fraction` | **1.0000** (9 of 9) | ≥ 0.70 | PASS |
| `trial_adjusted_confidence` (B = 0.9960 median, T = 2) | **0.9920** | ≥ 0.90 | PASS |
| `declared_roles_match_traded_sides` | declared `long,short`, traded `long,short` | required | PASS |

**Indicative ranking score on the median: `G` = 84.267.** Decomposition:
worst-fold term 26.75 of 30 · median-fold term 20.00 of 20 · drawdown term 10.90 of 20 ·
Calmar term 12.19 of 15 · positive-quarter term 8.00 of 8 · multiplicity term 6.44 of 7.

Three things worth saying about this sweep:

1. **The nominee is not the peak.** Its own Sharpe (1.2944) is above the median (1.2732), but its
   worst-fold Sharpe (0.6318) is *below* the median (0.6415) and four of the eight points beat it on
   `G`. The a-priori choices — phase 3, `RISK_PARITY_BARS` 270 — landed on the low side of their own
   axes, which is what an honest a-priori choice looks like.
2. **The weight axis is the flattest one.** `RISK_PARITY_BARS` 180 and 360 both *improve* on 270
   (Sharpe 1.334 and 1.334 against 1.294), and the drawdown at 360 is 0.0938 against 0.1148. The
   result does not depend on the exact sleeve weights, which is the specific robustness claim this
   lane needs to make and could not have made from the nominee alone.
3. **No inert point.** All nine scored vectors are distinct; the A1 check passed.


---

## 6. Falsification battery (sequence #130)

Run by the organiser's harness, not self-reported: `cup20_evaluate.py --falsification`, 3182.2 s.

### 6.1 Exact sign inversion — **PASS** (`sign_inversion_not_profitable`)

Every emitted weight negated (`None` and `{}` untouched), scored through the identical pipeline
against the eight core performance floors:

| core floor | inverted book | verdict |
|---|---:|---|
| `net_sharpe` (1×) | **−1.6308** | fails |
| `double_cost_sharpe` (2×) | **−1.7308** | fails |
| `triple_cost_sharpe` (3×) | **−1.8307** | fails |
| `annualized_return` (1×) | **−0.1914** | fails |
| `double_cost_annualized_return` (2×) | **−0.2016** | fails |
| `max_drawdown` (1×) | **0.5877** | fails |
| `annualized_volatility` (1×) | 0.1254 | clears |
| `trade_count` (1×) | 17225 | clears |

Six of the eight core floors fail, including all five return and Sharpe floors and the drawdown
floor. **The inversion does not clear the core floors; the falsifier is satisfied.** The apparent
edge is directional, not an artifact of cost, funding or cap asymmetry: the inverted book does not
merely lose the fee, it loses 19.1% a year and takes a 58.8% drawdown, which is the mirror image of
a real signal rather than the −cost centring a construction artifact would show.

### 6.2 Gross-edge placebo — exceedance **0.0000**

Eight placebo books preserving the candidate's weight multiset and rebalance schedule exactly and
randomising only which eligible symbol receives which weight, scored on **gross** edge:

| | bps per unit one-way turnover |
|---|---:|
| candidate | **102.94** |
| placebo min | −2.06 |
| placebo median | 2.03 |
| placebo max | 6.96 |
| **exceedance** | **0.0000** (0 of 8 reached the candidate) |

The registered expectation (#130) was that the placebo would be informative about the three
cross-sectional sleeves and **structurally uninformative about TREND**, which makes no
cross-sectional selection and therefore cannot be degraded by permuting symbol labels. The measured
result is stronger than that caveat needed: the placebo books cluster near zero gross edge and the
best of eight reaches 6.96 bps against the candidate's 102.94. Because TREND carries only 9.6% of
gross and the other three sleeves are pure cross-sections, the ensemble's edge is essentially all
in *which symbol gets which weight* — the part the placebo can and does destroy.


---

## 7. Every failure, every abandoned attempt

Offline exploration before the first organiser-scored number existed: **about 945 full-window
simulations** over the complete 4335-boundary in-sample window. Each of those is four complete
evaluator passes — the reference book plus 1×, 2× and 3× cost — so roughly **3,800 full-window
passes**, none of which cost a trial.

They ran on a numpy replica of the organiser's evaluator (`research/fastsim.py`), which reproduces
boundary funding on the carried book, next-open fills, per-side fee and slippage at the cost
multiplier, holding-period funding, the per-bar participation cap, membership forced exits, the
delisting 100%-haircut on an unfillable residual, the terminal close-out, the three §4 exposure caps
applied by uniform reduction at both ends, and the common risk unit itself. It was calibrated
against `crypto_trade.tournament.engine_v2.evaluate_targets` on two reference books (a 20-name
equal-weight long basket and a 5/5 cross-sectional momentum book) and agrees to **1e-5 in Sharpe at
1× and 2×, 1e-5 in maximum drawdown, 5e-5 in annualised volatility, 8e-4 in annualised turnover and
1e-8 in the risk-unit scalar** (`research/validate_fastsim.py`); only `trade_count` differs, by
0.9%, and it is four orders above its floor. Signals were additionally checked by running the real
frozen candidate code through the organiser's own `generate_targets` and comparing the emitted
weight matrix to the replica's: exact to 5.6e-17 for CARRY, TREND and FLOW, and to a mean 1.3e-5 for
LOWRISK, whose residual comes from bar gaps that the replica's matrix form treats as missing and the
streaming form does not (`research/parity.py`, `research/check_combo_parity.py`). **The replica was
used for exploration only. Every number in §3–§6 comes from an organiser packet under an accepted
trial.**

Sleeve families tested and **abandoned before preregistration**:

| abandoned family | causal claim | what was measured | verdict |
|---|---|---|---|
| **CLOCK** — settlement/session seasonality | participation is not uniform around the 24h funding-settlement clock or the week; flow concentrates at the Asia/Europe/US handover | expanding-window mean 8h cross-sectional return per hour-of-day, day-of-week and day×hour bucket, long/short the whole cross-section on the sign; 6 configurations | **falsified.** Every configuration negative: best `G` = −25.95 (hour-of-day, cadence 3, Sharpe +0.03); day-of-week reached `G` = −57.5 at Sharpe −0.84. Dropped. |
| **REVSHOCK** — short-horizon liquidity-shock reversal | a liquidity provider absorbing an impatient flow demands compensation, so a move achieved on thin participation reverts | volatility-normalised 1/2/3/6/9/21-bar reversal, both signs, cadences 1 and 3; 24 configurations | **falsified.** Every configuration negative in both signs, most catastrophically: best `G` = −54.1. Turnover 100–770× equity annualised; costs consume 6–49% of positive gross PnL. The horizon this sleeve needs is not payable at 7.5 bps a side. Dropped. |

Failures and dead ends inside the surviving families. Everything about a **sleeve standalone** below
was measured before #121; everything about the **combined** book necessarily comes after it, because
the rule was journaled before the first combined number was computed:

- **CARRY is weak and stayed in anyway.** Best standalone configuration `G` = −1.3 to −4.6 across
  lookbacks 84/105/126/147/168 (phase-averaged at cadence 6); Sharpe 0.27–0.40; worst fold −0.18 to
  −0.66. Organiser-scored standalone: `G` −3.13, and it fails eight floors on its own including
  `role_short_gross_pnl`. It is the weakest of the four and was retained because excluding a sleeve
  on its standalone number is selecting the combination on performance.
- **TREND has a single-lookback lottery.** At a single horizon, only 90 boundaries worked (`G` 38.3
  at cadence 9) while 60 (`G` −25) and 126 (`G` −17) did not; the blended 45/90/135 form was adopted
  a priori as the standard remedy, and its ensemble-level surface is flat (base 72 → `G` 75.1, 80 →
  84.2, 90 → 84.8, 100 → 85.4, 110 → 81.5).
- **LOWRISK measure choice.** `vol` and `downside` measures produced higher standalone Sharpe (0.89,
  0.96) but strongly alternating folds (F2 and F4 negative); the `maxdd` measure at 189/378/567 was
  chosen for fold consistency (all four folds positive standalone) at lower Sharpe. Its standalone
  base-lookback surface is genuinely jumpy (`G` 19.1 at base 160, 44.0 at 189, 30.3 at 220, 44.1 at
  260), which is why it was declared as a neighbourhood coordinate rather than hidden.
- **Ensemble-level formation-horizon surfaces are flat, which the standalone surfaces were not.**
  Varying one sleeve's horizon at a time inside the combined book (cadence 6, phase 3, replica):
  `CARRY_LOOKBACK` 84/105/126/147/168/189 → `G` 87.1 / 86.3 / **84.8** / 87.7 / 86.2 / 90.3;
  `TREND_BASE` 72/80/90/100/110 → 75.1 / 84.2 / **84.8** / 85.4 / 81.5;
  `FLOW_BASE` 48/55/63/72/80/90 → 76.8 / 82.9 / **84.8** / 82.5 / 83.6 / 84.4;
  `LOWRISK_BASE` 150/168/189/210/231/252 → 83.8 / 82.9 / **84.8** / 87.9 / 84.3 / 82.1.
  Every one of the twenty-two off-nominee horizons scores between 75 and 91 where the corresponding
  standalone sleeve surfaces swing by 40 to 60 points of `G`. Diversification across four bases also
  smoothed the parameter surface, which is a second-order benefit the lane did not ask about and
  which is worth recording.
- **Cadence.** Phase-averaged ensemble `G` at cadences 1/3/6/9/12/21 = 73.0 / 84.9 / 88.8 / 87.5 /
  88.3 / 83.1. Cadence 1 is materially worse (turnover 42.5× against 16.9×). Cadence 6 was chosen
  before #121; the cadence surface is flat between 3 and 12.
- **The A6 kind mistake, which cost nothing.** The first seven ablation evaluations were launched
  without `--ablation` and were refused with "has accepted trials of kind ['ablation'], but none of
  kind 'point'". No trial was consumed; the runs were relaunched with the flag. Recorded because the
  refusal message is the only thing standing between that mistake and seven wasted trials.
- **The falsification battery was killed mid-run once, and the playbook's promise held.** The first
  attempt at #130 was terminated by a session-level process cleanup after roughly an hour of CPU.
  Re-running the identical command re-resolved the same accepted trial: the header read
  "running under accepted trial #130 (11 of 12 trials spent ...)", with the spent count unchanged.
  No trial was burned. The second attempt was launched detached (`setsid nohup`) so that a wrapper
  being stopped could not take the evaluation with it.
- **Two floors that CARRY and LOWRISK fail standalone and the ensemble does not:**
  `role_short_gross_pnl` (carry −0.077, lowrisk −0.060) — charter §14.9's arithmetic, visible in the
  raw. The ensemble clears it (+0.083) only because TREND's directional short carries the side.

**Formation horizons tested (charter §9.1 requires at least three).** CARRY: 21/63/126/252/504
single and 42/63/84/105/126/147/168/189/252 blended. TREND: 30/60/90/126/189/252/378 single and
seven blends. LOWRISK: 63/126/189/252/378/504/567/756 across three risk measures. FLOW: 9/21/42/48/
55/63/72/80/84/90/105/126/168/252/336 single and blended. **Rebalance horizons (at least two, with
phase swept):** cadences 1, 3, 6, 9, 12 and 21 boundaries, **every phase offset of each** run
separately — 5 sleeve families × 51 cadence-phase combinations in the standalone study alone, plus
all six phases of cadence 6 and every phase of cadences 1/3/9/12/21 on the combined book.

**Controls-off, individual-control and combined-control ablations.** The transparent baseline
(#121) is controls-off. The four sleeve-standalone runs (#122–#125) are the individual controls. The
equal-notional run (#126) removes the combination rule while keeping the sleeves; the leave-one-out
run (#127) removes a sleeve while keeping the rule. Together they separate the three things that
could be carrying the book: the sleeves, the rule, and any one component.

---

## 8. What the controls say about the mechanism

- **The rule does work, and it is not the only thing working.** Same four sleeves at equal notional
  (#126): `G` 70.29, with a *much* lower drawdown (0.076 against 0.115) but a worst fold of −0.070
  against +0.632. The inverse-volatility rule trades drawdown for fold consistency, and `G` rewards
  that trade. Neither weighting is a small perturbation of the other: the risk shares differ by more
  than 2× on the TREND sleeve, which at equal notional carries 25% of gross instead of 9.6%.
- **The weakest sleeve costs the book about 7 points of `G` and stays.** Leave-one-out without CARRY
  (#127): `G` 91.91 against the nominee's 85.02, drawdown 0.098 against 0.115, worst fold +0.774
  against +0.632. **The nominee was not changed.** Dropping a sleeve after seeing a combined result
  is setting its weight to zero, which is re-weighting, which this mandate excludes. The number is
  reported so that the discipline is priced rather than merely asserted.
- **Delete the strongest sleeve and the combination still carries the book.** Leave-one-out without
  FLOW (#131): `G` **74.29**, Sharpe 0.985 at 1× and 0.882 at 2×, maximum drawdown 0.106, all four
  folds positive, 16 of 17 quarters positive. The best *remaining* sleeve on its own is LOWRISK at
  `G` 43.66, and the other two are at 27.90 and −3.13. Combining three mediocre mechanisms produces
  a book that outscores every one of them by 30 points of `G` and beats the best of them on
  drawdown, worst fold and quarterly consistency simultaneously. This is the strongest single piece
  of evidence in the certificate that the mechanism being tested — the combination itself — is what
  carries the book, rather than the ensemble being FLOW wearing a coat.
- **The book is not the baseline.** The transparent equal-weight long top-20 basket on the identical
  schedule scores `G` −17.06 with a 31.6% drawdown and two negative folds. Whatever the ensemble is
  doing, it is not owning the market.

---

## 9. Notes for the organiser

1. **`--ablation` is not discoverable from the playbook.** The playbook's §5.5 running order and its
   A6 discussion both describe journaling `--kind ablation` and then running `cup20_evaluate.py`,
   with no mention that the evaluator needs a matching `--ablation` flag to resolve that trial. The
   refusal is correct and free, but a team that journals seven ablations and then reads
   "REFUSED: ... none of kind 'point'" could reasonably believe it had mis-journaled seven trials.
   One sentence in §5.2 would close it.
2. **The `funding_time` jitter is real in this snapshot and is handled here by flooring to the hour
   before bucketing**, per the playbook's warning; no boundary-leak test in this workspace selects
   on `funding_time` directly.
3. **Perp-minus-mark was not used.** The playbook records that it is not a perp-spot basis on this
   snapshot; the CARRY sleeve therefore reads the published funding rate itself and nothing else,
   and no quantity in this submission is called "basis".
4. **The gross-edge placebo is structurally uninformative for the TREND sleeve** and therefore
   partially uninformative for this ensemble: TREND makes no cross-sectional selection, so permuting
   which symbol receives which weight cannot degrade it. This was registered in the falsification
   trial's purpose (#130) before the battery ran.
