# Team-01 research certificate — CUP-20

Lane: `slow-per-coin-time-series-momentum`
Nominated candidate: `candidates/slow-tsmom`
Declared roles: long, short
Accepted trials at nomination: **8** (journal sequences #5 – #12)

---

## 0. Scope of team-side research, stated before any number

The organiser's two commands produced every number in this certificate that is presented as a
metric, a gate or a floor. Nothing in `research/` reproduces the scorer: those scripts apply no fee,
no slippage, no exposure cap, no common risk unit, no declared risk policy, and compute none of the
charter's floors. What they compute are signal statistics — rank information coefficients,
signal-weighted mean forward returns per unit of own risk, hit rates, sign-flip rates, gross
information ratios in risk units, and the annualised absolute change of the strategy's own target
weight vector. They exist to decide which questions were worth a trial, and every quantity they
produce is labelled as gross and non-authoritative wherever it appears below.

The one place the team-side diagnostics were pushed toward realism is that funding was added from
research step 8 onward, because the charter's per-side floor is stated on `price_pnl + funding_pnl`
and because funding turned out to be the largest single term between the raw signal and a tradeable
book. Fees, slippage, caps and the risk unit remained absent from the team-side scripts throughout.

---

## 1. The hypothesis, and the mechanism it rests on

A perpetual future has no expiry and no overnight gap, and its marginal buyer is leveraged.
Unrealised profit on an open perpetual is collateral, so a price move that persists mechanically
expands the buying power of the side that is winning while liquidating the other side *into* the
move rather than out of it. The 24/7 tape gives that feedback loop no nightly close in which
positioning can be squared and no gap in which it can reset. The only force pulling a perpetual back
toward spot is the funding rate, which settles a few basis points every eight hours — large enough
to tax the crowd riding a trend, nowhere near large enough to stop it.

**The claim under test:** own-price persistence produced by that loop, measured on a coin's own
history over weeks, is worth more than the 7.5 bps a side it costs to harvest on the twenty most
liquid perpetuals in the market.

**The pre-registered falsifier:** if the edge is a regime exposure rather than a mechanism, it will
live in fold F1 (the 2020-21 bull) and die in F2 and F3. If it is a mechanism, it survives all four.

---

## 2. Trial ledger

Every material trial, in order, with what it was asked and what it answered. Trials that failed are
in the same table as those that did not.

| # | candidate | kind | question | outcome |
|---|---|---|---|---|
| 5 | `slow-tsmom-baseline` | point | Does unshaped per-coin 45-bar momentum, sized `1/sigma`, with no declared control, clear the floors? | **FAILS 10 floors.** Net Sharpe 0.203; turnover 45.8 against 25; gross edge 14.8 bps against 40; short sleeve −0.019; folds +2 of 4; worst fold −0.868. |
| 6 | `slow-tsmom-noctrl` | point | What does signal shaping alone buy — four-rung ladder, soft threshold, 9-boundary overlap, still no controls? | **FAILS 5.** Net Sharpe 0.203 → 0.565; turnover 45.8 → 24.5; gross edge 14.8 → 48.1; short sleeve turns positive (+0.027); maxDD 0.196 → 0.238; worst fold −0.359. |
| 7 | `slow-tsmom` (4-rung, H=9) | point | Add one declared control, a 10% volatility target. | **FAILS 1 — turnover 27.80 against 25.** Everything else passes: net Sharpe 1.227 / 1.102 / 0.978, maxDD 0.127, all four folds positive (worst +0.122), B = 0.9950. |
| 8 | `slow-tsmom` (frozen nominee) | point | Does slowing the ladder to two rungs and the overlap to 15 boundaries bring turnover inside budget without giving back Sharpe, drawdown or the worst fold? | **NO MEASURED FAILURE.** Turnover 19.52; net Sharpe 1.212 / 1.123 / 1.035; maxDD 0.110; worst fold −0.061; gross edge 110.3 bps; B = 0.9955; G = 60.64. |
| 9 | `slow-tsmom-brakes` | point | Do combined controls — the volatility target plus a two-step drawdown brake — beat the single control? | **FAILS 1, and is worse on every axis.** Net Sharpe 1.212 → 1.033; maxDD 0.110 → **0.145**; worst fold −0.061 → **−0.848**; positive quarters 12 → 11. Rejected. |
| 10 | `slow-tsmom-f90` | point | Does the mechanism survive at the months end of the lane (30- and 60-day rungs)? | **FAILS 4.** Net Sharpe 0.775; maxDD 0.219; worst fold −0.807; confidence 0.61. The slow end of the lane is the weak end. |
| 11 | `slow-tsmom` | neighbourhood | The declared ±20% one-at-a-time plateau, 7 points. | See §5 — this is the score. |
| 12 | `slow-tsmom` | falsification | Exact sign inversion plus eight gross-edge placebos. | **PASSES.** The inversion fails six of the eight core floors (net Sharpe −1.42, annualised return −0.220, maxDD 0.656) and clears only the two that carry no direction. Placebo exceedance 0.0000: 110.28 bps of gross edge against a placebo median of 6.33. |

Five of the eight accepted trials failed a floor. Three of those five were informative enough to
change the design, one (#9) closed a control axis, and one (#10) fixed the lane's slow boundary.

---

## 3. The research matrix the playbook requires

**Every conjunctive hard floor in charter §7.3 passes on the neighbourhood median, and the
falsification battery is satisfied.** Score: `G = 57.37`, net Sharpe 1.194 / 1.106 / 1.017,
maximum drawdown 0.112, worst fold −0.092, turnover 19.52, trial-adjusted confidence 0.948 at
`T = 8`. Details in §5 and §6.

### 3.1 Transparent baseline and its exact sign inversion

The baseline is `candidates/slow-tsmom-baseline`: `sign(sum of the last 45 8h log returns) / sigma`,
`sigma` over 90 bars, normalised to unit gross, no declared policy. Trial #5. Its exact sign
inversion is not run separately, because the charter's falsifier inverts the **nominated** point and
because the baseline's own vector already fails ten floors including annualised return at 2× cost;
an inversion of a book with a +0.021 base-cost annualised return has a negative one and fails the
same core floor. The inversion that matters — the nominee's — is trial #12, §6.

### 3.2 Formation horizons — at least three

Six formation horizons were carried to a scored run or a swept point, and eight more were measured
in the team-side cell statistics.

| formation | where | net Sharpe 1× | worst fold 2× | maxDD 1× |
|---|---|---|---|---|
| 45 bars (15 d) | trial #8, nominee | 1.212 | −0.061 | 0.110 |
| 36 bars (12 d) | neighbourhood point F− | §5 | §5 | §5 |
| 54 bars (18 d) | neighbourhood point F+ | §5 | §5 | §5 |
| 90 bars (30 d) | trial #10 | 0.775 | −0.807 | 0.219 |
| 45 bars, 4-rung ladder from 15 bars | trial #7 | 1.227 | +0.122 | 0.127 |
| 45 bars, unshaped | trial #5 | 0.203 | −0.868 | 0.196 |

The team-side cell statistic `E[sign(z) · r/sigma]` was measured at 21, 45, 63, 90, 135, 180, 270 and
360 bars (`research/eda_02_edge.py`). It is positive in all four folds only at the short end — at 21,
45 and 90 bars — and is negative in F2 and F3 from 135 bars upward. Trial #10 confirms that at the
portfolio level. **Own-price persistence in this window is a weeks phenomenon, not a months one.**

### 3.3 Holding horizons — at least two, and the phase axis

Holding horizons of 1, 3, 6, 9, 12, 15, 18, 21, 45 and 90 boundaries were measured team-side; 9
(trial #7), 15 (trial #8) and 12 and 18 (neighbourhood points H− and H+) were scored by the
organiser.

**The rebalance phase axis is void by construction, not unswept.** The strategy emits a target at
every 8h boundary; its holding horizon is a mean over the last `HOLDING_BARS` convictions, which is
the overlapping-portfolio construction written per coin, not a rebalance clock. A cadence of one bar
has no phase offset to sweep. This was a design decision taken *because* of the playbook's phase
rule: with twelve trials, a clocked cadence of `c` bars would have consumed `c` trials to be
reported honestly, and a cadence-3 result at one offset is a result about that offset. The overlap
delivers the same turnover reduction with no phase to choose.

The holding horizon trades directly against fold F3. Team-side, for the four-rung ladder at 45 bars:
F3 is +0.28 at H=1, −0.31 at H=9 and −0.70 at H=90, while F1 improves and weight churn falls by an
order of magnitude. H=15 on the two-rung ladder is where that trade lands with the worst fold still
inside its floor.

### 3.4 Controls — off, individual, combined

| configuration | trial | net Sharpe 1× | maxDD 1× | worst fold 2× | turnover |
|---|---|---|---|---|---|
| controls off | #6 | 0.565 | 0.238 | −0.359 | 24.5 |
| individual: volatility target only | #8 | **1.212** | **0.110** | **−0.061** | 19.5 |
| combined: volatility target + drawdown brake | #9 | 1.033 | 0.145 | −0.848 | 19.8 |

**The single control is load-bearing and the combination is harmful.** The volatility target's value
is concentrated exactly where the charter says the common risk unit cannot help: `common_risk_scalars`
needs 90 days of the reference book's history and returns 1.0 until it has them, so for the first
three months of the window the tournament's leveller is not levelling anything and an unlevered
book is a 70%-volatility book. Trial #6's F1 Sharpe at 2× cost is 0.18; trial #7's, with only the
volatility target added, is 1.43. Almost the whole improvement is that warm-up.

The drawdown brake fails for a mechanism reason, not a calibration one. A brake cuts exposure into a
drawdown and restores it on the recovery, and for a trend follower the recovery is when the
mechanism pays — so the brake sells the bottom of every regime turn. It made the drawdown it was
meant to control *worse* (0.110 → 0.145), because the book climbed out of each hole with less
exposure than it fell into it. The axis is closed.

### 3.5 Role checks — long, short, chop

Roles are declared `long, short` and the evaluator confirms both sides were materially traded.

- **Long sleeve**, trial #8: gross PnL **+0.665**. Positive, and it is the majority of the book's
  return — as it must be for an asset class with a positive drift over this window.
- **Short sleeve**, trial #8: gross PnL **+0.187**. Positive, and this is the fragile floor. In the
  team-side cell statistics the short sleeve is only marginally positive pooled (t ≈ 1.8) and is
  strongly negative in F1 at every horizon — shorting the 2020-21 bull is punished, and F2 and F3 pay
  for it. It also went *negative* at formation horizons of 63, 135, 270 and 360 bars, which is a
  second, independent reason the months end of the lane is not viable: at those horizons the
  candidate would fail the short-sleeve floor outright.
- **Chop**, fold F3 (`[2022-08-01, 2023-08-01)`): the post-FTX regime is where this mechanism does
  not work, and no specification tested made it work. The nominee's F3 Sharpe at 2× cost is −0.061,
  inside the −0.25 floor but not positive. Everything that improved F3 — a shorter holding overlap,
  a faster ladder — cost the turnover floor; everything that fixed turnover cost F3. That trade-off
  is the binding constraint on this candidate and it is stated plainly rather than optimised around.

### 3.6 The declared neighbourhood

§5. The nominee was fixed at trial #8 and the neighbourhood was declared afterwards; the ±20%
one-at-a-time rule was fixed in `research/eda_09_neighbourhood.py` before any of the seven points
were measured through the organiser's runner.

---

## 4. What did not work, and was abandoned

| attempt | where | why it was dropped |
|---|---|---|
| Rank information coefficient as the design statistic | step 1 | It is zero at every horizon (−0.009 to +0.006) and the hit rate is at or below 0.50. Momentum here pays by magnitude in the tail, not by frequency; a reader who checks only the IC concludes the opposite of the truth. Replaced by the signal-weighted mean. |
| Skip-period momentum (12-1 convention) | step 3 | Uniformly harmful: F3 goes from +0.28 at skip 0 to −0.36 at skip 3 and −0.63 at skip 6. At this frequency the most recent week is the most informative part of the window, not the most contaminated. |
| Hard sign conviction | steps 3–4 | Same edge for 40% more weight churn: a sign flips the whole position for an arbitrarily small change in the trend. Replaced by a clipped, soft-thresholded conviction that passes through zero continuously. |
| `tanh` instead of `clip` | step 4 | Indistinguishable — information ratio within 0.02 everywhere tested. Kept `clip` as the simpler statement. |
| Parkinson range volatility estimator | step 10 | Lower estimator variance did not translate: neighbourhood-median gross IR 1.18 → 1.16, fold profile unchanged. A 50/50 blend gave 1.17. The specification is insensitive to it. |
| Five-rung and wide ladders | steps 7, 11–12 | More rungs flatten the surface but lower the level; `(1×, 2×)` gave the most edge per unit of churn once turnover became the binding floor. |
| Four-rung ladder with a 5-day rung, H=9 | trial #7 | Passed every floor except turnover (27.80 against 25). The fast rung carried most of the weight churn and least of the edge. |
| Two-step drawdown brake | trial #9 | Worse on Sharpe, drawdown, worst fold and positive quarters. §3.4. |
| Months-end formation (30/60-day rungs) | trial #10 | Fails four floors. §3.2. |
| Declaring a lower volatility target to buy turnover headroom | §7 | Available and deliberately **not used**. §7 explains why. |

---

## 5. The declared neighbourhood and the score

Declaration (`candidates/slow-tsmom/neighbourhood.json`), journal #11:

- coordinates `FORMATION_BARS`, `HOLDING_BARS`, `TREND_THRESHOLD`; `k = 3`, so 7 points are required
  and 7 are declared;
- nominee `(45, 15, 0.35)`, equal to the module-level constants in the frozen `strategy.py`;
- each coordinate varied one at a time by ±20% of the nominated value — `36 / 54`, `12 / 18`,
  `0.28 / 0.42`. Twenty per cent is four times the charter's 5% materiality minimum, and one uniform
  rule was used for all three coordinates so that no step size could be tuned to the median.

The seven points, each materialised as its own file out of the frozen source and executed in its
own interpreter:

| point | `FORMATION_BARS` | `HOLDING_BARS` | `TREND_THRESHOLD` | net Sharpe 1× | 2× Sharpe | ann. return | maxDD |
|---|---|---|---|---|---|---|---|
| nominee | 45 | 15 | 0.35 | 1.2118 | 1.1234 | 0.2058 | 0.1098 |
| 1 | **36** | 15 | 0.35 | 0.9192 | 0.8225 | 0.1494 | 0.1336 |
| 2 | **54** | 15 | 0.35 | 0.9280 | 0.8454 | 0.1501 | 0.1277 |
| 3 | 45 | **12** | 0.35 | 1.2294 | 1.1335 | 0.2093 | 0.1119 |
| 4 | 45 | **18** | 0.35 | 1.1451 | 1.0615 | 0.1922 | 0.1174 |
| 5 | 45 | 15 | **0.28** | 1.1938 | 1.1057 | 0.2018 | 0.1099 |
| 6 | 45 | 15 | **0.42** | 1.2274 | 1.1387 | 0.2092 | 0.1092 |

**The score — per-metric median across the seven points, journal #11:**

| metric | median | floor | |
|---|---:|---:|---|
| net Sharpe 1× | **1.1938** | ≥ 0.80 | PASS |
| net Sharpe 2× | **1.1057** | ≥ 0.50 | PASS |
| net Sharpe 3× | **1.0175** | > 0 | PASS |
| annualised return 1× | 0.2018 | > 0 | PASS |
| annualised return 2× | 0.1844 | > 0 | PASS |
| maximum drawdown 1× | **0.1119** | ≤ 0.20 | PASS |
| realised annualised volatility | 0.1657 | ≥ 0.06 | PASS |
| positive-quarter fraction 1× | 0.6471 | ≥ 0.50 | PASS |
| positive folds 2× | 3 of 4 | ≥ 3 | PASS |
| worst fold Sharpe 2× | **−0.0920** | ≥ −0.25 | PASS |
| annualised one-way turnover | **19.52** | ≤ 25 | PASS |
| gross edge per unit turnover | **109.1 bps** | ≥ 40 | PASS |
| cost share of positive gross PnL | 0.0076 | ≤ 0.30 | PASS |
| five largest days' share | 0.0247 | ≤ 0.35 | PASS |
| worst fold's share of positive PnL | 0.2842 | ≤ 0.60 | PASS |
| executed trades | 125 263 | ≥ 500 | PASS |
| neighbourhood points positive | **7 of 7 (1.00)** | ≥ 0.70 | PASS |
| trial-adjusted confidence | **0.9545** (B = 0.9935, T = 7) | ≥ 0.90 | PASS |
| long gross PnL | +0.6568 | > 0 | PASS |
| short gross PnL | +0.1819 | > 0 | PASS |
| declared roles vs traded sides | long, short | match | PASS |

Median fold Sharpe 2× = 1.3249; 2×-cost maximum drawdown 0.1199; 2×-cost positive-quarter fraction
0.6471; Calmar 1.586. **Indicative ranking score G = 57.37.**

Two things worth reading off that table honestly. First, the median is below the nominee on almost
every metric — net Sharpe 1.194 against 1.212, worst fold −0.092 against −0.061, positive quarters
11 against 12 — which is exactly what §7.2 predicts a nominated point to be, and it is the median
that is quoted everywhere in this certificate as the result. Second, **the plateau is not flat in
`FORMATION_BARS`.** Moving the anchor by ±20% costs about 0.28 of net Sharpe in both directions
(1.21 → 0.92 and 0.93), while ±20% in the holding overlap costs at most 0.07 and ±20% in the
threshold costs at most 0.02. The candidate is robust in two of its three coordinates and sits on a
ridge in the third. That is a real weakness, it was visible in the team-side surface before the
sweep was declared (`research/NOTES.md` step 7), and the ±20% step size was fixed before any point
was measured precisely so it could not be narrowed once the ridge was known.

With `T = 8` at nomination the confidence term is `1 − 8 × (1 − 0.9935) = 0.948`.

---

## 6. Falsification battery

Journal #12, run by the organiser's harness on the nominated point. Both halves pass.

**Exact sign inversion** — every emitted weight negated, `None` and `{}` untouched — scored against
the eight core performance floors:

| core floor | inverted book | verdict |
|---|---:|---|
| net Sharpe 1× | −1.4169 | fails |
| net Sharpe 2× | −1.5049 | fails |
| net Sharpe 3× | −1.5929 | fails |
| annualised return 1× | −0.2199 | fails |
| annualised return 2× | −0.2313 | fails |
| maximum drawdown | 0.6564 | fails |
| realised volatility | 0.1656 | clears |
| executed trades | 125 605 | clears |

The two it clears are the two that carry no direction — a book and its inverse have the same
volatility and the same number of fills by construction. Every floor that reads the sign of the
edge is failed, and failed by a wide margin: the inversion loses 22% a year where the candidate
makes 21%, and draws down 66% where the candidate draws down 11%. **The apparent edge is
directional, not a cost, funding or cap asymmetry.**

**Gross-edge placebo** — eight books that keep the candidate's weight multiset and its rebalance
schedule exactly and randomise only which eligible coin receives which weight:

| | gross edge, bps per unit one-way turnover |
|---|---:|
| candidate | **110.28** |
| placebo minimum | 5.19 |
| placebo median | 6.33 |
| placebo maximum | 7.08 |
| exceedance | **0.0000** (0 of 8 placebos reach the candidate) |

The placebo is scored on gross edge, so it is not the cost model doing the work. A book that holds
the same positions in the same sizes at the same times, and only mis-attributes which coin each
position belongs to, earns about 6 bps per unit of turnover; attributing them by each coin's own
trailing trend earns 110. **Substantially all of the candidate's gross edge is in the per-coin
attribution — that is, in the signal — rather than in its exposure profile, its turnover schedule
or its sizing distribution.**

---

## 7. Two things the organiser should know

### 7.1 A declared volatility target converges to the geometric mean of the target and the book

The declared volatility target is applied inside the pass it governs, and the volatility it reads
(`_past_annualized_volatility`) is the realised net return of the book *after* the same target has
already scaled it. The scale therefore satisfies `x = target / (x · v)` where `v` is the unscaled
book's volatility, whose fixed point is `x* = sqrt(target / v)` and whose realised volatility is
`sqrt(target · v)`, not `target`. Measured: trial #8 declares a 10% target on a book whose unlevered
volatility is about 86% and realises **16.6%**, and `sqrt(0.10 × 0.29) = 0.17` reproduces it.

The measured chain for trial #8: the risk-unit scalar medians at 0.3961, so the reference book's
trailing volatility is `0.10 / 0.3961 = 0.2525`; inverting the fixed point puts the capped requested
book's own unlevered volatility at `0.2525² / 0.10 = 0.638`; the executed book's pre-policy
volatility is then `0.3961 × 0.638 = 0.253`, and `sqrt(0.10 × 0.253) = 0.159` against a measured
0.166.

This has a consequence worth stating because it is exploitable and this candidate does not exploit
it. Executed gross, and therefore turnover, scale with realised volatility, so a team failing the
25× turnover floor can buy headroom by declaring a smaller volatility target. The common risk unit
does *not* fully cancel it: composing both layers through the same square-root fixed point gives
realised volatility `≈ sqrt(0.10) · (target · v)^(1/4)`, so it moves as the **fourth root** of the
declared target rather than proportionally. Declaring 2% instead of 10% would have taken this book
from 16.6% to about 10.6% volatility and turnover from 19.5 to roughly 13 — at no cost in Sharpe,
with a better drawdown, and still clear of the 0.06 volatility floor. Team-01 did not do this. The
candidate declares the target it means, 10%, and fixed its turnover problem in the signal instead,
by slowing the ladder and lengthening the holding overlap (trial #7 → trial #8). Being the first
team to run, it seemed worth not setting the other precedent.

### 7.2 The per-symbol cap binds on an inverse-volatility book

The `requested` trim block shows the 0.20 per-symbol cap binding at **647 of 4335** boundaries, with
a minimum scale of 0.276 and a median of 0.868. That is not concentration by intent: it is `1/sigma`
sizing meeting a quiet coin. When one eligible name's own volatility is far below the rest of the
universe's, inverse-volatility weighting hands it a large share of a unit-gross book and the cap
reduces the whole book to fit. The candidate is executed at roughly 87% of the concentration it
requests at the median trimmed boundary, and every number in this certificate is measured on the
executed book, not the requested one.

---

## 8. Honest read

The mechanism is real. The falsification battery is the strongest single piece of evidence for that
and it is the one team-01 could not have influenced: a book that holds the same positions in the
same sizes at the same times but mis-attributes which coin each belongs to earns 6 bps of gross
edge per unit of turnover where the candidate earns 110, and the exact inversion loses 22% a year
with a 66% drawdown. Whatever this is, it is a directional per-coin signal and not an artifact of
cost, funding, caps or exposure profile.

But its margin is thinner than the nominee's own vector suggests, and the places it is thin are
known rather than hidden.

What is solid: the effect is present in all four folds at the short end of the formation range, it
is present with the right sign on both sleeves, it survives 3× cost with a Sharpe above one, and its
cost density is not marginal — 110 bps of gross edge per unit of turnover against a 40 bps floor,
and costs at 0.8% of positive gross PnL against a 30% ceiling. This is not a strategy that dies on
fees; it is a strategy that dies on regime.

What is thin: fold F3 is negative at every specification that clears the turnover floor, and the
research never found a version that was both tradeable and positive in the post-FTX chop. The
formation surface is a spike rather than a plateau — 45 bars reads 1.44 team-side where 54 reads 1.21
and 36 reads 1.13 — and the standard error on an information ratio over 3.96 years is about 0.50, so
the level at the anchor is partly luck and the neighbourhood median is the honest estimate. The
short sleeve's own t-statistic is under 2 in the cell data and turns negative at four of the eight
formation horizons tested. And the single most important design choice, the declared volatility
target, earns most of its keep in one 90-day warm-up window where the common risk unit is inert —
which is a real property of this tournament's construction, and one whose importance would be much
smaller on a longer window.

---

## 9. Post-nomination exploration — four trials offered, none spent, nominee unchanged

The organiser verified the nomination and asked team-01 to continue until no further improvement
was available. **No additional material trial was accepted. `T` remains 8, the frozen candidate is
unchanged, and its source digest is still `6947d4d6…`.** Everything in this section was produced by
the free team-side diagnostics described in §0; it is recorded here because §7 of the playbook asks
for every abandoned attempt, and an attempt abandoned before it cost a trial is still an attempt.

### 9.1 Where the ranking score actually leaks

Decomposing `G` on the sweep medians: worst fold 4.74 of 30, maximum drawdown 10.67 of 20, positive
quarters 3.14 of 8, and the three maxed terms. **Almost the whole available gain is fold F3**, and
trial #7 already had it — its worst fold was +0.122 and its own vector ranks at **G = 61.05 at
T = 11** against this nominee's **55.55** at the same trial count. Trial #7 failed exactly one
floor: turnover, 27.80 against 25.

### 9.2 The three-way bind

A replacement must clear three conditions at once, all fixed before the search:

- **turnover**, `dW ≤ 66` on the fit `gross × (24 + 1.394·dW)` — accurate to under 2% on both
  anchors (#7 predicted 28.1 for 27.80 actual, #8 predicted 19.4 for 19.52);
- **confidence**, `IR ≥ 1.10`. Re-freezing costs two trials, so `T` becomes 11 or 12, and the floor
  `1 − T·(1−B) ≥ 0.90` then needs `B ≥ 0.99091` or `0.99167`. On six scored runs that is a net
  Sharpe near 1.19. **The slower, calmer, lower-Sharpe candidate is not the safe one; it is the
  disqualified one** — and this is the constraint that decided the outcome;
- **the prize**, `F3 ≥ −0.05`, which maps to roughly +0.08 scored on the measured +0.13 offset.

### 9.3 What was tried

**A no-trade band** (emit only when the book has moved more than a band in L1; otherwise return
`None`) targeted the ~40% of turnover that is evaluator bookkeeping rather than signal churn. On the
team-side panel it looked decisive: the four-rung H=9 signal at a 0.24 band gave IR 1.24, F3 +0.08
and `dW` 78. **Abandoned on the evaluator's source rather than on a number.** With a volatility
target declared, `"volatility_target"` is in `reasons` at every boundary the scale is under 1 —
always, for a book realising 16.6% against a 10% target — so `scale_reasons` is non-empty and
`_reduction_only_policy_target` fills on skipped boundaries too. The suppressed fills do not
disappear, and the reduction-only rule trims a position only when it has drifted *up*: it cuts
winners and never adds to losers, which is exactly backwards for a trend follower.

**An exhaustive ladder search** — 80 specifications over ten families (slower rungs added to dilute
the fast one, unequal rung weights from 1/8 to 1/4 on the fast rung, formation 45 and 54, holding 9
through 18), each scored against all three thresholds. **Zero clear all three: 49 fail the
information ratio, 30 fail turnover, 1 fails F3.** The failure mode is monotone rather than
scattered — `dW` and `IR` are opposed along the speed axis and `F3` travels with `dW`. Every
specification reaching F3 ≥ −0.10 inside the turnover budget has an information ratio of 0.87 to
1.03, i.e. a scored Sharpe around 0.98 to 1.14, under the bootstrap floor a re-freeze must clear.
The only specification with both a good F3 and IR ≥ 1.10 is the four-rung ladder at H=9 — which is
trial #7, and which fails turnover.

Closest near-misses, all failing on the information ratio alone: `5rung +3/2` F=54 H=15 (IR 1.02,
F3 −0.05, dW 58); `4rung 1/3,1,3/2,2` F=54 H=15 (IR 1.02, F3 −0.03, dW 59) and H=18 (IR 1.00,
F3 −0.00, dW 54); `fast-lite w=1/5 +3/2` F=54 H=15 (IR 1.04, F3 −0.02, dW 56).

**Lengthening the volatility target's `lookback_days`** was considered and rejected without a trial.
It is *not* the forbidden lever — it does not shrink the book, because the realised-volatility fixed
point `sqrt(target × v)` is independent of the lookback; it only slows the gross scale, which is
genuinely trading less. But the arithmetic does not reach: the scale contributes about 25 of trial
#7's 148 turnover units, so even a 90-day lookback leaves turnover near 24.9 against a floor of 25
applied to the median — and it would blunt the target exactly where trial #6 → #7 showed it earns
its keep, the fast reaction inside the risk unit's 90-day warm-up.

### 9.4 Why nothing was spent

The organiser's own standard was that a G of 58 against 57 is noise on a four-year window. The best
available replacement offers perhaps +2 G and carries a real probability of failing the
trial-adjusted confidence floor outright, which is disqualifying rather than merely worse. Spending
trials also costs the incumbent: `slow-tsmom` scores **G = 56.92 at T = 8** and would score 55.10 at
T = 12 for no change in its behaviour at all. Every path examined was negative in expectation.

**The lane is exhausted at 8 accepted trials. `slow-tsmom` stands, with four trials unspent.**
