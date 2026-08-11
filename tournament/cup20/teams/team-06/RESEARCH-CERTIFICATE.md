# Team 06 — Research Certificate

**Lane:** `downside-risk-low-volatility-selection`
**Nomination:** `candidates/downside-tercile`
**Trials accepted:** 8 (journal sequences #58–#65) — the minimum, with 4 left unspent
**Window:** `[2020-08-17, 2024-08-01)`, the organiser's in-sample snapshot and nothing else.

---

## 0. Verdict in one paragraph

I nominate a dollar-unbalanced, beta-balanced long/short book that sorts the point-in-time top-20
on an equal-weight composite of four downside-risk characteristics — left-tail CVaR, downside
semideviation, drawdown depth and recovery time — and holds the six lowest against the six highest,
rebalanced weekly.

**Scored on the declared neighbourhood median (#64), which is my score: G = 53.43**, net Sharpe
1.414 / 1.346 / 1.278 at 1×/2×/3× cost, annualised return 0.192, maximum drawdown 0.125, realised
annualised volatility **0.1304 against the 0.06 substance gate**, 3 991 executed trades against the
500 gate, turnover 11.7 against the 25 ceiling, 158 bps of gross edge per unit turnover, **both
sleeves gross-positive** — which §14.9 says is the hard part for a cross-sectional lane on a window
where the equal-weight basket returned +199% — and 7 of 7 neighbourhood points positive.

**One floor is missed and it is the expensive one: worst-fold Sharpe 2×, median −0.289 against a
−0.25 floor.** That single number forfeits the whole 30-point worst-fold term; the other five
ranking terms earn 53.4 of a possible 70. The failing fold is F2 (2021-08 → 2022-08), the alt
melt-up into the bear onset, at five of the seven neighbourhood points. Both substance gates and
both integrity gates are measured and passed (§11), so the candidate is admissible; under amendment A4 the
worst-fold miss is priced by the ranking rather than disqualifying. At the nominated point itself
there is no measured failure at all (worst fold −0.160), but the point is a diagnostic and the
median is the score.

The lane's headline question has a two-part answer and I am reporting the uncomfortable half first.
**On aggregate risk-adjusted performance, downside-risk selection and plain-volatility selection are
indistinguishable on this universe.** Identical book, identical everything, selector swapped: ranking
score 58.10 vs 57.97, Sharpe 1.414 vs 1.435, drawdown 0.1245 vs 0.1242. Across all 21 rebalance
phases offline the volatility book is if anything marginally ahead. **They differ on exactly one
thing, and it happens to be the thing the lane is about: which names end up in the short sleeve.**
The downside-selected short sleeve is gross-positive (+0.067); the volatility-selected one is
gross-negative (−0.072) and fails that floor. Selecting on left-tail depth and drawdown geometry
puts coins in the short sleeve that fall in *absolute* terms; selecting on total volatility puts
coins there that are merely wide.

---

## 1. Mechanism, and what would falsify it

**Why a left-tail measure could carry information that symmetric volatility does not.** In a 24/7
venue where leverage is universally available and every position is marked continuously, a coin's
left tail is not exogenous. Crowded leveraged length is liquidated *into* a falling book: the
liquidation engine sells what the down move already made cheap, which extends the down move, which
triggers the next tranche. Deleveraging is therefore one-sided in a way that re-leveraging is not,
and the size of a coin's realised left tail is largely a record of how much marginal leveraged
length has been forced out of it. That same crowding is what made the coin expensive. Symmetric
volatility counts the up-moves and the down-moves alike and cannot separate a coin whose width is
two-sided market-making churn from one whose width is repeated one-sided deleveraging.

Funding and forced liquidation both act asymmetrically on the downside, and both would push the same
way. I deliberately did **not** use funding as an input: that is another team's lane, and a
selection built on it would no longer be a selection on downside risk. Funding enters my book only
as something the organiser's evaluator charges or pays me.

**Pre-registered falsifier.** If the trailing composite carried no forecast of the *forward* realised
downside character, the book would be paid for a stale label rather than for a risk, and the whole
mechanism story would be decoration. Section 5 reports the measurement.

**What I expected to see if the lane's premise were true**, written down before the ablation ran: the
downside composite should beat the volatility ablation on drawdown and on worst-fold Sharpe, because
those are the statistics a left-tail selection should improve. Section 4 reports what actually
happened.

---

## 2. Discipline and disclosure

- **Data.** `data/cup20/is/` only. No market data was fetched. No organiser-only tree was opened,
  resolved, listed or referenced, in any revision. No other team's directory was read.
- **The evaluator is the organiser's.** Every number in this certificate that is described as
  *scored* comes from `scripts/cup20_evaluate.py` and cites a journal sequence.
- **An offline laboratory was used, and its multiplicity is disclosed rather than hidden.**
  `research/lab.py` approximates the two-pass evaluator; `research/preflight.py` runs the **frozen**
  strategy through the organiser's own `generate_targets`, so the signal under test offline is
  byte-identical to the candidate's and only the scoring half is approximate. I ran roughly **170
  offline configurations** across score families, formation horizons, breadths, cadences, phases and
  controls. That search is not charged to the trial budget because it never opened the organiser's
  scorer, but it is real multiplicity and a reader should price it: **the trial-adjusted confidence
  reported below understates the true search.** Its practical size is bounded by two things — the
  score family was chosen on principle rather than by ranking (§3), and the nominee's parameters sit
  at plateau centres rather than at offline maxima (§8).
- **Calibration of the laboratory against the real scorer.** At the nominated configuration the lab
  reported a ranking-score proxy of 64.6 and realised volatility 0.114; the organiser's scorer
  reported 58.10 and 0.130. The lab is directionally reliable and numerically loose, and no
  conclusion below rests on the lab alone unless it is labelled as an offline diagnostic.

---

## 3. How the composite was chosen — on principle, not by ranking

The mandate names the characteristics of the lane: *downside deviation, semivariance, drawdown depth
and recovery time, tail asymmetry*. The nominee is the **equal-weight z-score composite of one
estimator per named facet**, with no fitted weights:

| facet | estimator |
|---|---|
| left-tail depth | mean of the worst 5% of the window's 8h log returns (CVaR₅) |
| semivariance | root-mean-square of the below-mean returns |
| drawdown depth | deepest peak-to-trough on the window's log close path |
| recovery time | fraction of the window spent below its running maximum |

Equal weights are a choice made *before* looking at which weighting scored best, and I did not tune
them afterwards. That was not costless: an offline scan of nine score families across four formation
horizons showed a three-facet variant peaking higher at one horizon (proxy 84.2 at 189 bars) than
the four-facet composite anywhere. I did not take it, because it peaked at one horizon and collapsed
at the next (46.6 at 126 bars) while the four-facet composite held 56.6 / 71.7 / 74.4 / 62.1 across
126 / 189 / 252 / 315. A plateau is the thing a neighbourhood median can measure; a peak is not.

**Tail asymmetry, the fifth named facet, is not in the book, and this is the lane's first real
negative.** Every pure-asymmetry construction I could measure carries no cross-sectional return
information on this universe:

| measure (weekly cross-sections, forward 7d return) | mean IC | t | fold signs |
|---|---:|---:|---|
| total volatility | −0.123 | −5.66 | − − − − |
| downside semideviation | −0.116 | −5.30 | − − − − |
| left-tail CVaR₅ | −0.128 | −5.78 | − − − − |
| drawdown depth | −0.086 | −3.77 | − − − − |
| **semideviation ÷ volatility (pure asymmetry)** | **+0.009** | **+0.47** | − ~ + + |
| **skewness** | **−0.013** | **−0.69** | + − − − |
| **downside beta − upside beta** | **−0.010** | **−0.54** | − + + − |
| CVaR₅ residualised on volatility | −0.046 | −2.73 | − + − − |

The *level* of downside risk predicts. The *shape* does not. A book built on the residual alone was
measured offline and is worthless — proxy score 30.2 / 3.1 / 1.9 / 0.0 at formation 126 / 189 / 252
/ 315, Sharpe going negative at the long horizons. I abandoned the pure-asymmetry thesis on that
evidence rather than spending trials on it, and the nominee is a *level* selection with a left-tail
flavour, not an asymmetry selection.

---

## 4. THE ablation — is downside risk doing work that plain volatility does not?

`candidates/plain-vol` is the nominee with one line changed: the four-facet composite is replaced by
the standard deviation of the same window's returns. Same universe, same formation window, same
breadth, same cadence, same phase, same beta tilt, same weights, same risk policy.

| | nominee (composite) #58 | ablation (total volatility) #59 |
|---|---:|---:|
| indicative ranking score G | **58.10** | 57.97 |
| net Sharpe 1× / 2× / 3× | 1.414 / 1.346 / 1.278 | 1.435 / 1.381 / 1.328 |
| annualised return 1× | 0.1924 | 0.1868 |
| maximum drawdown 1× | 0.1245 | 0.1242 |
| realised annualised volatility | 0.1304 | 0.1248 |
| fold Sharpes 2× (F1–F4) | +2.61 / −0.16 / +2.14 / +0.50 | +2.74 / +0.01 / +2.41 / +0.15 |
| annualised turnover | 11.73 | 8.88 |
| gross edge per unit turnover | 163 bps | 208 bps |
| **long sleeve gross PnL** | **+0.692** | +0.804 |
| **short sleeve gross PnL** | **+0.067** | **−0.072 (FAILS the floor)** |
| measured floor failures | **none** | one |

**Answer, stated plainly: on everything except sleeve composition, no.** The two books have the same
Sharpe, the same drawdown, the same return and the same score. My pre-registered expectation — that a
left-tail selection would improve drawdown and worst-fold Sharpe — was **not** borne out; the
volatility ablation's worst fold is actually better (+0.01 vs −0.16). The lane's premise, in the form
I registered it, is unsupported.

To be sure the comparison was not a single-phase accident I ran both books through all 21 rebalance
phases offline, paired:

| offline, 21 paired phases | composite | volatility |
|---|---|---|
| proxy score, mean / median | 62.4 / 64.6 | 64.1 / 62.8 |
| Sharpe 1×, mean | 1.94 | 2.03 |
| maximum drawdown, mean | 0.122 | 0.125 |
| worst-fold (F2) Sharpe, mean / min | +0.10 / −0.97 | +0.49 / +0.30 |
| composite wins on score | 10 of 21 | |
| composite wins on drawdown | 11 of 21 | |

The composite is a **coin flip against plain volatility on aggregate performance, and is materially
more phase-fragile in the hardest fold.** I believe the reason is mechanical rather than mysterious:
two of the composite's four facets — drawdown depth and time under water — are path statistics with
roughly one effective observation per window, against 252 for a standard deviation. They estimate a
related quantity with far more noise, and that noise shows up as phase sensitivity.

**Where the composite does earn its place.** The short sleeve. Across the three selectors I scored:

| selector (tilt on) | short sleeve gross PnL | trial |
|---|---:|---|
| four-facet downside composite | **+0.067** | #58 |
| downside semideviation alone | −0.008 | #63 |
| total volatility | −0.072 | #59 |

Only the composite's short sleeve stands alone. Charter §14.9 records that a cross-sectional short
sleeve is gross-positive on this window only if the shorted names fall in absolute terms, and that a
previous team measured 48 diversified sleeves without finding one. My six-name, diversified,
never-concentrated short sleeve is gross-positive, and swapping the selector to total volatility
flips it negative. That is a genuine and lane-specific difference, and it is the only one I found.

**A caveat I owe the reader.** On the *unscaled* unit-gross book the short sleeve is gross-**negative**
(−0.57, offline). It is the organiser's common risk unit — which shrinks the book precisely through
the high-volatility 2021 melt-up where the short sleeve bleeds — that turns it positive on the scored
book. The sleeve's positivity is therefore a joint property of my selection and the tournament's own
risk normalisation, not of my selection alone. The risk unit is applied identically to every team,
so this is not an advantage I constructed, but it is not a claim I get to make unqualified either.

**A pre-committed switch rule, and what it did.** Before running #59 I wrote down that I would move
the nomination to the volatility book if it showed no measured floor failure and its offline
worst-fold distribution dominated the composite's. The second condition held. The first did not — the
short-sleeve floor. The rule therefore kept the nomination where it was, which is the outcome I want
a rule to be capable of overturning and the reason I wrote it before looking.

---

## 5. Forward-looking or backward-looking?

Downside-risk characteristics are strongly autocorrelated, so a book ranking on trailing semivariance
could be paid for persistence in the *measure* rather than for anything about future drawdown. Three
measurements on non-overlapping weekly cross-sections (n = 198–206, formation 252 bars, horizon 21
bars) separate those:

| | mean | t | F1 | F2 | F3 | F4 |
|---|---:|---:|---:|---:|---:|---:|
| **persistence** — composite now vs composite 21 bars later | 0.968 | 317.6 | 0.960 | 0.963 | 0.975 | 0.974 |
| **forecast** — trailing composite vs the *next* 21 bars' realised composite | **0.525** | **32.6** | 0.449 | 0.528 | 0.517 | 0.604 |
| **oracle** — the *realised* next-21-bar composite vs that same forward return | **−0.350** | **−13.9** | −0.324 | −0.292 | −0.426 | −0.353 |
| tradeable — trailing composite vs forward return | −0.122 | −5.13 | −0.080 | −0.109 | −0.126 | −0.172 |
| **trailing, with the oracle projected out** | **+0.064** | +3.51 | +0.062 | +0.071 | +0.094 | +0.028 |

Read in order: the measure is nearly perfectly autocorrelated (0.968), which on its own proves
nothing. It genuinely **forecasts** the next, non-overlapping window's realised downside character at
rank correlation 0.52 in every fold. The return premium attaches to the **realised** forward
characteristic (oracle IC −0.35), not to the label — and the part of the trailing label that does
*not* forecast forward risk carries none of the premium; its residual IC is small and of the *wrong*
sign (+0.064). The tradeable signal captures about a third of the oracle's cross-sectional
information, which is what an imperfect but real forecast looks like.

**Conclusion: the selection is forward-looking.** It works because it predicts next-period downside
risk, and the stale component of the label is worthless or mildly counterproductive.

Corroborating: discarding the most recent 3 or 7 days of the formation window (`skip` = 9 or 21 bars)
leaves the book unchanged or slightly better offline (proxy 74.4 → 72.7 → 84.5 at formation 252), and
only a 21-day discard degrades it (52.7). The freshest bars are not load-bearing, so the book is not
trading a rebound from whatever just crashed.

---

## 6. Baseline, and the exact sign inversion

**Transparent baseline (#61, `candidates/baseline-semidev`)**: the simplest thing this lane can do —
rank the point-in-time top-20 on downside semideviation alone, long the six lowest against the six
highest, equal dollar sleeves, no control, same formation and cadence.

| | baseline #61 | nominee #58 |
|---|---:|---:|
| G | 34.33 | **58.10** |
| net Sharpe 1× | 1.080 | 1.414 |
| maximum drawdown 1× | 0.1626 | 0.1245 |
| fold Sharpes 2× | +2.10 / +0.01 / +1.81 / −0.06 | +2.61 / −0.16 / +2.14 / +0.50 |
| short sleeve gross PnL | −0.065 (fails) | +0.067 |
| measured floor failures | 2 (short sleeve, confidence) | none |

One caveat on that last row: the baseline's `trial_adjusted_confidence` miss (0.889) is an artifact of
*when* it ran — `1 − T(1−B)` with T = 6 at that moment and B = 0.9815 — not a property of the book.
Read the baseline as failing one floor, the short sleeve. My own bootstrap fraction is high enough
(B = 0.998) that the confidence floor never bound at any trial count I could reach.

**Exact sign inversion**: run by the organiser's harness as part of the falsification battery (#65),
not by me. Result in §11.

---

## 7. Horizons and phase

**Three formation horizons**, all scored by the organiser inside the declared sweep (#64): 189, 252
and 315 bars (63, 84 and 105 days).

**Two rebalance horizons.** Weekly (21 bars) is the nominee, scored at three phases inside the sweep.
Fortnightly (42 bars) is trial #62, and it is worth reporting in full because it nearly changed my
nomination:

| | weekly (nominee) #58 | fortnightly #62 |
|---|---:|---:|
| G | 58.10 | **65.09** |
| net Sharpe 1× | 1.414 | 1.692 |
| maximum drawdown 1× | 0.1245 | 0.1026 |
| turnover | 11.73 | 8.18 |
| measured floor failures | none | none |

The fortnightly point scored **better on every axis**. I did not switch, and the reason is phase.
Sweeping all 42 fortnightly phases offline against all 21 weekly phases:

| offline, every phase | weekly (n=21) | fortnightly (n=42) |
|---|---|---|
| proxy score mean / median | **62.4 / 64.6** | 59.3 / 61.2 |
| Sharpe 1× mean | **1.94** | 1.88 |
| maximum drawdown mean | **0.122** | 0.136 |
| worst-fold mean | +0.10 | **+0.18** |
| spread (min → max) | 41 → 81 | 36 → 84 |

Phase-agnostically the weekly book is better on score, Sharpe and drawdown, and the fortnightly
trial's superiority was a phase draw — its phase sits 15th of 42. Cadence is not a free lunch here
and a single-phase cadence comparison would have sold me a spike.

**Phase is a first-order axis and I treated it as one.** The full 21-phase distribution of the nominee
mechanism spans proxy scores 41.1 to 81.3 while Sharpe barely moves (1.67 to 2.22) — the dispersion
is almost entirely in worst-fold Sharpe and drawdown, which are exactly the statistics the ranking
rewards. **The nominated phase is the one whose offline proxy score is the median of all 21**
(phase 2, proxy 64.6), chosen deliberately rather than the best (phase 16, proxy 81.3). Phase is then
also a declared sweep coordinate, so the scored median is a phase-agnostic estimate.

**Faster cadences were tested and rejected on cost, not on score.** Rebalancing every bar removes the
phase axis entirely — an attractive property — but costs 50.1× annualised turnover against the 25×
ceiling at 46 bps of gross edge. Every third bar: 30–32× turnover. Every ninth bar: 17.6× and inside
the ceiling but still phase-dispersed. Weekly at 11.7× is the regime where a slow characteristic can
be traded without the turnover floor binding.

---

## 8. Controls: off, individual, combined

The book has one control — a leg-weight tilt that sizes the two sleeves so their trailing market
betas offset rather than their dollar amounts. Selecting on risk necessarily produces sleeves of
unequal beta, and without the tilt the book is a short-beta position wearing a cross-sectional
costume. Crossed against the selector, this gives a complete 2×2, every cell scored:

| | selector = four-facet composite | selector = semideviation alone |
|---|---|---|
| **tilt on** | **#58 — G 58.10, Sharpe 1.414, DD 0.125, short +0.067, 0 failures** | #63 — G 55.91, Sharpe 1.660, DD 0.122, short −0.008, 1 failure |
| **tilt off** | #60 — G 19.68, Sharpe 1.003, DD 0.212, short +0.016, 2 failures | #61 — G 34.33, Sharpe 1.080, DD 0.163, short −0.065, 2 failures |

- **The tilt is the single most load-bearing element**: +38 score points on the composite
  (19.7 → 58.1), +22 on the baseline. With it off, the composite book breaches both the drawdown
  floor (0.212 > 0.20) and the worst-fold floor (−0.506 < −0.25). Nearly all of the book's drawdown
  control comes from the control, not from the selection.
- **The composite is worth about +2 score points over a single characteristic with the tilt on, and
  costs 0.25 of Sharpe** — but it is the only cell whose short sleeve is gross-positive.
- The tilt does what it claims. Regressing the offline book return on the equal-weight market:
  **beta +0.043, R² 0.026**, and by fold +0.062 / +0.017 / +0.064 / +0.021. The book is
  market-neutral in the sense that matters, at the cost of running a mean **+0.21 net long dollar
  exposure** (range −0.01 to +0.39), which is the price of beta-neutrality when the long sleeve is
  the low-beta one.

---

## 9. Role checks: long, short, chop

Long and short come from the organiser's packet (#58): long sleeve gross PnL **+0.692**, short sleeve
**+0.067**, both positive, and `declared_roles_match_traded_sides` **PASS** — declared `['long',
'short']`, traded `['long', 'short']`.

The packet carries no return stream, so the **chop** role is measured offline on the frozen
strategy's own targets, with regimes defined causally as terciles of the trailing 63-bar equal-weight
return of the point-in-time top-20:

| regime | bars | annualised return | Sharpe | long PnL | short PnL |
|---|---:|---:|---:|---:|---:|
| market down | 1 424 | +0.369 | +2.10 | +0.365 | +0.115 |
| **chop** | 1 487 | +0.524 | **+2.79** | +0.365 | +0.346 |
| market up | 1 424 | +0.272 | +0.90 | +1.383 | −1.030 |
| all | 4 335 | +0.390 | +1.71 | +2.113 | −0.569 |

All three regimes are positive; the book is strongest in chop and weakest in a rising market, which
is what a beta-neutral risk sort should look like. The short sleeve is the loser in up markets
(−1.03) and the earner in chop (+0.35) — it is not a permanent drag, it is a regime-dependent one.

---

## 10. The declared neighbourhood and its sweep

The nominee was **fixed before** the neighbourhood was written, and the neighbourhood was declared
and validated (`--check`, free) before trial #64 was journaled. Three coordinates, seven points:

```
coordinates  FORMATION_BARS   SELECTION_COUNT   REBALANCE_PHASE
nominee      252              6                 2
points       189/315          5/7               1/3
```

Every coordinate is a single-valued module-level numeric literal in the frozen `strategy.py`, named
identically, and each is consumed directly rather than re-derived — so the sweep's rewrite reaches
everything downstream. None is quantised: a one-name change in `SELECTION_COUNT` changes twelve
weights, a one-bar change in `REBALANCE_PHASE` moves every rebalance, and a formation change moves
every characteristic. The A1 inertness check is reported with the sweep result below.

**Sweep result (#64, 7 points, 4 workers, 1 108 s).** Every point was materialised as its own file,
executed in its own interpreter, and produced a distinct source digest and a distinct metric vector —
**no inert point**, so the A1 rule is satisfied on measurement and not merely by declaration.

| point | F1 | F2 | F3 | F4 | worst | Sharpe 1× | maxDD | vol | short PnL |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **nominee** 252 / 6 / ph2 | +2.614 | −0.160 | +2.137 | +0.496 | −0.160 | 1.414 | 0.125 | 0.130 | +0.0669 |
| 189 / 6 / ph2 | +2.543 | +0.248 | +1.371 | +0.407 | +0.248 | 1.303 | 0.135 | 0.128 | +0.0229 |
| 315 / 6 / ph2 | +2.516 | −0.828 | +1.133 | +1.334 | −0.828 | 1.179 | 0.160 | 0.123 | −0.0219 |
| 252 / 5 / ph2 | +2.835 | −0.349 | +2.627 | +0.777 | −0.349 | 1.663 | 0.121 | 0.135 | +0.1131 |
| 252 / 7 / ph2 | +2.743 | +0.342 | +1.780 | +0.459 | +0.342 | 1.462 | 0.119 | 0.128 | +0.0689 |
| 252 / 6 / ph1 | +2.395 | −0.289 | +1.778 | +0.655 | −0.289 | 1.298 | 0.135 | 0.133 | −0.0109 |
| 252 / 6 / ph3 | +2.474 | −0.305 | +2.856 | +0.551 | −0.305 | 1.540 | 0.131 | 0.121 | +0.0890 |

**It is a plateau, not a spike.** All seven points carry positive 1× return *and* positive 2× Sharpe —
`positive_point_fraction` 1.000 against the 0.70 floor. Sharpe ranges 1.18–1.66 and drawdown
0.119–0.160 across a ±25% formation change, a ±1-name breadth change and a ±1-bar phase change. The
nominee sits at the median of its own neighbourhood on Sharpe, drawdown, volatility and short-sleeve
PnL — which is what fixing it at a plateau centre rather than at an offline maximum was for.

**The one place the neighbourhood is worse than the nominee is the fold that was always going to be
the problem.** The nominee's worst fold is −0.160; the median across the plateau is **−0.289**, and
that is my one missed floor. F2 is the worst fold at five of seven points.

---

## 11. Falsification battery (#65)

Run by the organiser's harness on the nominated point, not by me, in 2 673 s.

**Exact sign inversion — every emitted weight negated, `None` and `{}` untouched.** Buying the
highest-downside-risk names and shorting the lowest is a catastrophe, which is what a real mechanism
should look like inverted:

| core floor | inversion | verdict |
|---|---:|---|
| net Sharpe 1× | **−1.6442** | fails |
| net Sharpe 2× | −1.7122 | fails |
| net Sharpe 3× | −1.7799 | fails |
| annualised return 1× | −0.2032 | fails |
| annualised return 2× | −0.2104 | fails |
| maximum drawdown | **0.6106** | fails |
| realised annualised volatility | 0.1327 | clears |
| executed trades | 4 093 | clears |

Six of the eight core floors fail and the two that clear are the substance gates, which are
sign-symmetric by construction (an inverted book trades the same names at the same size). **The
inversion does not clear the core floors: `sign_inversion_not_profitable` is measured and PASSES.**
The edge is directional, not a construction artifact of the harness.

**Gross-edge placebo — my exact weight multiset and rebalance schedule, with only the mapping of
weight to symbol randomised, scored on gross edge:**

| | bps per unit one-way turnover |
|---|---:|
| candidate | **163.40** |
| 8 placebo books | min −19.84, median 8.90, max 14.51 |
| exceedance | **0.0000** — no placebo reaches the candidate |

The placebos keep everything about the book's *shape* — how much gross, how many names, how often it
trades, how big each position is — and destroy only **which coin receives which weight**. They earn
roughly 9 bps against my 163, and none of the eight comes within an order of magnitude. Whatever this
book is being paid for, it is being paid for the cross-sectional selection and not for the exposure
profile or the trading schedule.

**Both integrity gates are now measured and passed**, so the candidate is admissible under A5.

---

## 12. Scored result — the neighbourhood median, which is my score

| metric | median across the 7 declared points | floor | |
|---|---:|---:|---|
| net Sharpe 1× | 1.4144 | ≥ 0.80 | PASS |
| net Sharpe 2× | 1.3463 | ≥ 0.50 | PASS |
| net Sharpe 3× | 1.2782 | > 0 | PASS |
| annualised return 1× | 0.1924 | > 0 | PASS |
| annualised return 2× | 0.1820 | > 0 | PASS |
| maximum drawdown 1× | 0.1245 | ≤ 0.20 | PASS |
| **realised annualised volatility 1×** | **0.1304** | **≥ 0.06** | **PASS — the substance gate, cleared by 2.2×** |
| positive-quarter fraction | 0.7059 | ≥ 0.50 | PASS |
| positive fold count 2× | 3 of 4 | ≥ 3 | PASS |
| **worst-fold Sharpe 2×** | **−0.2888** | **≥ −0.25** | **MISS — by 0.039** |
| annualised one-way turnover | 11.73 | ≤ 25 | PASS |
| gross edge per unit turnover | 157.5 bps | ≥ 40 | PASS |
| cost share of positive gross | 0.63% | ≤ 30% | PASS |
| five-largest-day share | 3.37% | ≤ 35% | PASS |
| worst fold's share of positive PnL | 32.0% | ≤ 60% | PASS |
| **executed trades** | **3 991** | **≥ 500** | **PASS — the substance gate, cleared by 8×** |
| neighbourhood points positive | 7 of 7 (1.000) | ≥ 0.70 | PASS |
| trial-adjusted confidence | 0.9860 (B = 0.9980, T = 7) | ≥ 0.90 | PASS |
| long sleeve gross PnL | +0.7009 | > 0 | PASS |
| short sleeve gross PnL | +0.0669 | > 0 | PASS |
| **declared roles match traded sides** | declared `long,short`, traded `long,short` | — | **PASS — integrity gate** |
| **exact sign inversion not profitable** | inversion: Sharpe −1.644, return −0.203, maxDD 0.611 | — | **PASS — integrity gate (#65)** |
| calmar 2× | 1.4363 | — | ranking input |
| median fold Sharpe 2× | 1.2336 | — | ranking input |
| maximum drawdown 2× | 0.1267 | — | ranking input |

**Indicative ranking score G = 53.428**, decomposed:

| term | weight | value | earned |
|---|---:|---|---:|
| worst-fold Sharpe 2× | 30 | −0.2888 | **0.0** |
| median fold Sharpe 2× | 20 | +1.2336 | 20.0 |
| maximum drawdown 2× | 20 | 0.1267 | 9.8 |
| Calmar 2× | 15 | 1.4363 | 14.4 |
| positive-quarter fraction 2× | 8 | 0.7059 | 4.4 |
| trial-adjusted confidence | 7 | 0.9860 | 4.9 |

**Every point of the shortfall is one number.** The worst-fold term is the largest in the formula and
I earn none of it, by 0.039 of Sharpe. The other five terms are at 53.5 of a possible 70.

**Exposure caps.** The requested book was never trimmed (0 of 206 boundaries). The executed book was
trimmed at 2 of 206 boundaries, minimum scale 0.918 — so nothing here is a capped-book artifact. The
risk-unit scalar ran at median 0.557 (range 0.218–1.104), i.e. the organiser's common risk unit
mostly *shrank* my book toward the 10% target rather than being blocked by the unlevered gross cap.
That is the healthy side of the volatility gate: there was headroom in both directions.

---

## 13. Trial ledger — every trial, including the ones that failed

| # | candidate | kind | question | outcome |
|---|---|---|---|---|
| 58 | `downside-tercile` | point | Does the four-facet downside composite, beta-tilted, clear the floors? | **No measured failure.** G 58.10, Sharpe 1.414, DD 0.125, vol 0.130, 4 006 trades, both sleeves positive. |
| 59 | `plain-vol` | point | THE ABLATION — does downside risk do work plain volatility does not? | **Largely no.** G 57.97 vs 58.10, same Sharpe and drawdown. Fails `role_short_gross_pnl` (−0.072), the one floor the nominee passes. |
| 60 | `no-beta-tilt` | point | Controls-off: how much of the book is the risk sort? | **Control is load-bearing.** G 19.68. Fails `max_drawdown` (0.212) and `worst_fold_sharpe` (−0.506). |
| 61 | `baseline-semidev` | point | The transparent baseline: one characteristic, no control. | G 34.33. Fails `role_short_gross_pnl` (−0.065) and `trial_adjusted_confidence` (0.889, at T=6). |
| 62 | `cadence-42` | point | Second rebalance horizon — fortnightly. | **No measured failure, G 65.09 — better than the nominee.** Not adopted: phase-agnostically weekly dominates (§7). Disclosed as the best single point I did not nominate. |
| 63 | `semidev-tilt` | point | Individual control on the baseline selector, completing the 2×2. | G 55.91, Sharpe 1.660 — the *highest* Sharpe of the family. Fails `role_short_gross_pnl` (−0.008). |
| 64 | `downside-tercile` | neighbourhood | Plateau or spike? | **Plateau. 7 of 7 points positive; Sharpe 1.18–1.66, drawdown 0.119–0.160, volatility 0.123–0.135 across the whole plateau. No inert point. Median = my score, G 53.43, one missed floor: worst-fold −0.289.** |
| 65 | `downside-tercile` | falsification | Sign inversion + gross-edge placebo. | **Both halves pass.** Inversion fails six of eight core floors (Sharpe −1.644, maxDD 0.611). Placebo exceedance 0.0000: 8 shuffled books earn a median 8.9 bps of gross edge per unit turnover against the candidate's 163.4. |

**Abandoned without spending a trial**, on offline evidence, all disclosed:

- **Pure tail-asymmetry selection** (semideviation ÷ volatility; skewness; downside-minus-upside
  beta; CVaR ratio). Zero IC, sign-flipping across folds (§3). This was my original preferred thesis
  and it is dead.
- **The volatility-residualised composite** (CVaR orthogonalised on σ). Offline proxy 30.2 / 3.1 /
  1.9 / 0.0 across four formation horizons, Sharpe negative at the long ones.
- **Every-bar and every-third-bar rebalancing**, on the turnover floor (50.1× and 30–32× against a
  25× ceiling), despite the attraction of eliminating the phase axis entirely (§7).
- **A three-facet composite** peaking at proxy 84.2, rejected for collapsing to 46.6 one formation
  horizon away (§3).
- **A skip/lag control** (discarding the freshest bars). Offline it neither helped nor hurt at
  9–21 bars and hurt at 63; it earns its place as evidence about forward-lookingness (§5), not as a
  control, so it is not in the book.

---

## 14. Honest reckoning

1. **The lane's premise, as I registered it, is not supported.** Downside-risk selection did not beat
   volatility selection on drawdown or on worst-fold Sharpe. It is the same selection measured with
   more noise — the two rank 0.89 alike cross-sectionally, and the incremental component carries
   t ≈ −2.7 against the level's t ≈ −5.8. The one place the difference is real and repeatable is
   short-sleeve composition, and that is where I have staked the nomination.
2. **F2 is the weakness, and on the median it is a missed floor.** The 2021-08 → 2022-08 fold — the
   alt melt-up into the bear onset — is where a low-downside-risk book is on the wrong side. The
   nominated point's F2 Sharpe is −0.160; the neighbourhood median worst fold is **−0.289 against a
   −0.25 floor**, and it forfeits the entire 30-point worst-fold term, which is 100% of my ranking
   shortfall. It is not a fluke I can parameter away: it is the regime in which coins with fat left
   tails are exactly what leveraged retail wants to own, and my selection is systematically short
   them. I could have chased it — the 189-bar and 7-name points both have positive F2 — but picking
   the point whose F2 happens to be positive is precisely the peak-picking the median exists to
   discount, and I had already fixed the nominee.
3. **The short sleeve's gross positivity is a median, not a universal.** Two of the seven
   neighbourhood points have marginally negative short sleeves (−0.022 at formation 315, −0.011 at
   phase 1). The claim I am entitled to is that the composite's short sleeve is gross-positive at the
   median of its plateau and at five of seven points, where total volatility's is negative — not that
   it is positive everywhere.
4. **Most of the drawdown control is the control, not the selection.** Turning off the beta tilt
   takes drawdown from 0.125 to 0.212. Anyone reading this as "downside-risk selection produces low
   drawdown" would be reading it wrong; the honest statement is "a beta-balanced cross-sectional risk
   sort produces low drawdown".
5. **The short sleeve's gross positivity is also partly the tournament's own risk unit** (§4), which
   shrinks the book through the period the sleeve bleeds.
6. **Offline multiplicity exceeds the trial count by more than an order of magnitude** (§2). The
   trial-adjusted confidence term is not a defence against that; the neighbourhood median and the
   plateau-centred parameter choices are the only real ones.
7. **`volatility_target.enabled` is `false`**, as amendment A3 requires. I did not need it and would
   not have used it: the book's realised volatility is 0.130, more than twice the 0.06 substance
   gate, so there was never a temptation to reach for a policy field to lift it — and the field
   cannot do that anyway, since the evaluator is unlevered and my book already runs at full gross
   where the risk unit does not shrink it. I also did not use it to move turnover, which is the
   exploit the amendment closes; my turnover is 11.7 against a 25 ceiling and needed no help.
