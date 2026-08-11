# Team 05 — Research Certificate

Lane: `short-horizon-liquidity-shock-reversal`
Nominated candidate: **`cascade-breadth-01`**
Declared roles: **long** (observed roles: long)
Accepted trials: **11** of 12 (journal sequences #46–#56)

---

## 0. The one-paragraph result

The naive form of this lane is false on this universe, and the certificate opens with that because
everything else follows from it. A large single-name move at 8h does not revert — it **continues**,
and it continues hardest when volume and trade count spiked with it. Reversing on return magnitude
alone earns 22.3 bps per unit of one-way turnover, is positive in two folds of four, draws down 24%
and returns a 3×-cost Sharpe of 0.01. What does revert is a move that arrives in **several names at
once**: a margin engine unwinds correlated collateral simultaneously, while information arrives at
one asset. Requiring the same outsized down bar in at least two point-in-time members of the same
8h bar, changing nothing else, takes gross edge to 42.6 bps per unit turnover, four positive folds
of four, a 19.1% drawdown and a 3×-cost Sharpe of 0.54. That book is the nomination. It misses the
turnover ceiling by 75% and the 1× net Sharpe floor is cleared but only just; both are on the record
below rather than argued away.

---

## 1. The mechanism, and what would falsify it

**Claim.** A liquidation cascade is a liquidity event. Forced sellers do not choose their price:
margin engines and stop ladders emit market orders at whatever size the book absorbs, so price
travels further than the information in the move justifies. The excess is repaid once the forced
flow is exhausted. The trade is the repayment.

**The conditioning problem.** A forced move and an informed move both look like one big red candle.
The lane exists only if something separates them. Three candidate separators were pre-registered
from the mechanism before any of them was scored:

| # | signature | mechanism story |
|---|---|---|
| S1 | the move outran its own recent scale | an overshoot is defined relative to normal dispersion, not in absolute return |
| S2 | it was printed by a burst of orders (trade-count spike) | a liquidation ladder is many small involuntary orders in a short window |
| S3 | it happened to several names at once | a margin engine unwinds correlated collateral simultaneously; news does not |

**Pre-registered falsifier.** If the book conditioned on S1–S3 performs like the book conditioned on
S1 alone, the signature is decoration and the lane has produced a plain reversal with extra steps.
That comparison is trials #48 versus #49 and it is reported in §4.

**Second pre-registered falsifier.** If the snap-back is an execution artifact rather than a real
repayment, it will not survive a cost shock. Every result is reported at 1×, 2× and 3× cost in §7.

---

## 2. What the exploratory work found before any trial was spent

All of §2 is free research on the in-sample snapshot: forward-return conditioning, event studies and
weight-path arithmetic. It computes no floor, no fold Sharpe against a threshold and no ranking
score. Every scored number in this certificate comes out of the organiser's two commands.

**2.1 The lane's naive form is backwards.** Reversing on `z = 8h return / trailing 60-bar σ`, on
cross-sectionally demeaned forward returns, the reversal trade *loses* at every magnitude bucket and
loses more the larger the move: |z| ≥ 4 gives −49.7 bp over 8h (t = −3.2) and −76.4 bp over 16h
(t = −3.6). Conditioning made it worse in the direction that mattered: splitting |z| ≥ 2.5 events by
trade-count spike, the top tercile reversed at −34.6 bp (t = −2.5) and the bottom at −4.3 bp. Large
moves on heavy involuntary-looking flow continue **hardest**. This was the first thing measured and
it nearly ended the lane.

**2.2 The direction split rescued it.** Pooling up and down shocks through `−sign(z)` was hiding a
strong asymmetry. Split by direction, on **raw** (not demeaned) forward returns:

| trigger | 8h | 16h | 24h |
|---|---:|---:|---:|
| down shock, z ≤ −2, market down | −21.9 bp | — | **+98.7 bp** (t = 6.3) |
| up shock, z ≥ 2 (short pays −raw) | −46.9 bp (t = −5.6) | −80.2 bp (t = −6.8) | −55.0 bp (t = −3.7) |
| all member bars (baseline drift) | +4.7 bp | — | +14.1 bp |

Down cascades snap back; up spikes continue. That asymmetry is the reason this book has no short
sleeve (§6).

**2.3 The snap-back is a beta event, not a cross-sectional one.** The same down-shock conditioning
measured on cross-sectionally demeaned forward returns is flat to slightly negative at every
horizon. The repayment accrues to the whole complex, not to the shocked name relative to its peers.
This is disclosed here because it is the single most important limitation of the result and it
governs how the placebo in §8 should be read.

**2.4 The impulse response is narrow and was measured, not fitted.** For qualifying events, mean
open-to-open return of the shocked names by bar after the shock bar:

| bar | +1 | +2 | +3 | +4 | +5 | +6 |
|---|---:|---:|---:|---:|---:|---:|
| bp | −2.5 | **+60.8** | **+98.9** | −0.5 | −28.4 | −41.8 |
| t | −0.15 | 4.34 | 7.61 | −0.04 | −2.38 | −3.35 |

The forced selling completes in bar +1 and the repayment lands in bars +2 and +3. `ENTRY_DELAY = 1`
and `HOLD_BARS = 3` come from this table. Trials #53 and #54 later tested moving each of them and
both are worse (§5).

**2.5 Turnover is the lane's binding arithmetic, and it is not the signal's fault.** A name held H
bars in a book renormalised at every boundary costs about 2/H of one-way turnover per invested bar
regardless of signal quality, so a 24h horizon at an 8h cadence cannot be cheap. The first
overlapping-slice constructions turned over 250–330× a year and earned about 10 bps per unit of it —
a book paying the exchange for the privilege of being right. The fix that made the lane viable is
architectural, not parametric: **enter once, return `None` for the whole holding window (which holds
quantities and costs nothing), exit once, and be flat between episodes.** Turnover per episode is
then ~2.0 whatever H is.

---

## 3. The trial ledger

Every scored evaluation, in order, with what it answered. `G` is the organiser's indicative ranking
score for that point; it is not a neighbourhood median except at #55.

| seq | candidate | question | 1×/2×/3× Sharpe | turnover | bps/turn | maxDD 1× | folds 2× | G |
|---|---|---|---|---:|---:|---:|---|---:|
| #46 | `cascade-snapback-01` | does a breadth-and-flow-conditioned cascade snap-back pay for its turnover? | 0.633 / 0.499 / 0.365 | 29.0 | 42.0 | 0.153 | 0.91 / −0.07 / 0.26 / 0.73 | 22.45 |
| #47 | `cascade-snapback-02` | does a fixed-size basket beat one sized by threshold-crossing count? | 0.654 / 0.510 / 0.366 | 31.8 | 40.6 | 0.195 | 0.71 / 0.45 / 0.18 / 0.74 | 23.09 |
| #48 | `baseline-plain-reversal` | **transparent baseline / controls off**: does plain post-shock reversal work at all? | 0.461 / 0.237 / 0.013 | 51.1 | 22.3 | 0.243 | 1.23 / 0.25 / **−1.37** / **−0.48** | −22.79 |
| #49 | `ablate-flow-signature` | **individual control**: breadth on, trade-count spike off | **0.931 / 0.738 / 0.544** | 43.7 | 42.6 | 0.191 | 0.98 / 1.47 / 0.16 / 0.48 | **35.43** |
| #50 | `ablate-breadth` | **individual control**: trade-count spike on, breadth off | 0.382 / 0.198 / 0.014 | 40.7 | 22.4 | 0.212 | 0.59 / 0.64 / **−0.47** / **−0.28** | −10.48 |
| #51 | `formation-30` | formation horizon halved to 30 bars | 0.502 / 0.362 / 0.223 | 30.6 | 33.5 | 0.166 | 0.54 / 0.28 / 0.14 / 0.48 | 13.60 |
| #52 | `cascade-breadth-b3` | is breadth a plateau or a cliff? tighten 2 → 3 | 0.757 / 0.586 / 0.413 | 39.2 | 39.5 | 0.212 | 0.96 / 1.06 / **−0.20** / 0.48 | 13.40 |
| #53 | `cascade-breadth-hold2` | **second holding horizon**: exit after 2 boundaries not 3 | 0.583 / 0.337 / 0.090 | 49.0 | 24.9 | 0.190 | 0.97 / 1.42 / −0.08 / **−1.02** | −9.02 |
| #54 | `cascade-breadth-delay0` | **entry phase**: buy the first boundary after the shock | 0.849 / 0.672 / 0.493 | 38.6 | 42.5 | 0.165 | 1.19 / 0.51 / **−0.39** / 1.17 | 16.54 |
| #55 | `cascade-breadth-01` | **declared neighbourhood sweep** — the score (7 points, median-scored) | 0.931 / 0.738 / 0.539 | 43.7 | 42.2 | 0.192 | 4/4 pts, worst +0.16 | **30.36** |
| #56 | `cascade-breadth-01` | **falsification battery** — sign inversion + placebo | inv. −1.321 / −1.514 / −1.705 | — | 42.58 vs placebo med. 33.49 | inv. 0.692 | — | PASS |

Nothing was abandoned unrecorded. #46 and #47 are the superseded first design (§10.1); #51 sits on
the first design's family and is labelled as such wherever it is used.

---

## 4. Is the conditioning doing work? — the ablation the lane exists to run

This is the comparison the mandate calls the single most informative run, and it is a clean
two-by-two because the four books differ **only** in two constants, generated from one template.

| | breadth OFF | breadth ON |
|---|---|---|
| **flow spike OFF** | #48 controls off: G **−22.79**, 22.3 bps/turn, 2/4 folds, 3× Sharpe 0.01 | #49 **G 35.43**, 42.6 bps/turn, **4/4 folds**, 3× Sharpe 0.54 |
| **flow spike ON** | #50: G −10.48, 22.4 bps/turn, 2/4 folds, 3× Sharpe 0.01 | #47 combined: G 23.09, 40.6 bps/turn, 4/4 folds, 3× Sharpe 0.37 |

Read the columns, not the cells. **Breadth is the entire effect.** Moving from breadth-off to
breadth-on nearly doubles gross edge per unit of turnover (22.3 → 42.6), takes two negative folds
positive, and takes the 3×-cost Sharpe from zero to 0.54. Moving from flow-off to flow-on with
breadth already required does the opposite: it removes about a quarter of the events, moves gross
edge the **wrong** way (42.6 → 40.6), and costs 12 points of G.

So the honest answer to "is the conditioning doing work" is: **yes, and not the conditioning I
expected.** The trade-count spike — the most obvious proxy for forced flow, and the one the mandate's
own text names — is not what separates a forced move from an informed one once simultaneity is
required. Cross-sectional simultaneity is. That is still a statement about *how* the move happened
rather than how large it was, which is what the lane asks for, and the magnitude-only baseline at
#48 is what proves the distinction is load-bearing rather than cosmetic.

**The pre-registered failure mode fired on a component, and it is reported rather than buried.** S2
was pre-registered as a separator and it failed. The constant survives in the frozen source at its
disabled value (`FLOW_SPIKE = 0.0`) so the decision is legible in the code, not only here.

---

## 5. Formation horizons, holding horizons, phase

**Formation horizons (four).** The formation horizon here is `LOOKBACK_BARS`, the window over which
"its own recent scale" is measured. Scored: **30** (#51, on the first-design family, G 13.60,
22.3 bps/turn → 33.5), **60** (the nominee), and **45** and **80** inside the declared sweep (#55,
§9). Halving the window costs about a fifth of the gross edge per unit turnover; the surface is flat
across 45–80 (§9).

**Holding horizons (two).** **3** (the nominee) and **2** (#53). Exiting one boundary early is not a
small change: it drops bar +4 of the impulse response, raises turnover from 43.7 to 49.0, cuts gross
edge from 42.6 to 24.9 bps per unit turnover, and takes F4 from +0.48 to −1.02. The measured impulse
response in §2.4 predicted the direction; it did not predict the size.

**Rebalance phase.** The book decides at **every** boundary — its rebalance cadence is one bar — so
the charter's phase-offset requirement, which is written for cadences longer than one bar, does not
bind on a calendar phase here. The analogous quantity for an event-triggered book is the offset of
the entry from the triggering event, and that is swept: `ENTRY_DELAY` 0 (#54) against 1 (nominee).
Buying the first boundary after the shock instead of waiting one costs 19 points of G and takes F3
from +0.16 to −0.39. The mechanism predicted it (bar +1 is the cascade completing, and its mean
return is −2.5 bp), and the scored run agreed.

---

## 6. Role checks

**Long.** The only side the book trades. `declared_roles_match_traded_sides` passes on every scored
run: declared `['long']`, traded `['long']`. Long gross PnL is positive on every run in the ledger.

**Short.** Tested and rejected on evidence, in exploratory work, before any trial was spent on it.
Shorting after an up shock lost at every horizon and under every conditioning tried:

| up-shock subset | 8h | 16h | 24h | 48h |
|---|---:|---:|---:|---:|
| plain (z ≥ 2) | −46.9 | −80.2 | −55.0 | −88.4 |
| + trade-count spike ≥ 2 | −49.3 | −74.0 | −31.9 | −50.9 |
| + trade-count spike < 1.5 | −31.6 | −66.1 | −67.4 | −137.2 |
| during a market-wide squeeze | −54.1 | −100.3 | −53.4 | −82.4 |
| in a calm market | −31.3 | −57.1 | −50.3 | −125.2 |

(bp, short pays −raw; every cell is a loss for the short.) No trial was spent on a short sleeve
because no configuration of one was worth scoring. **This costs the candidate one of the thirteen
graded floors** — `role_short_gross_pnl` is a bare `> 0` gate with no scale, so a book that never
trades short scores zero credit on it exactly as a book with a losing short sleeve would, worth 1/13
of the multiplicative compliance factor. That is a known, priced cost and it is preferred to
declaring a sleeve the evidence says loses.

**Chop.** The book is flat about 91% of boundaries by construction, so the sideways regime is mostly
a non-event for it: the exposure is switched on by a cascade and off three boundaries later. The
measurable form of the chop check is the positive-quarter fraction and the fold spread, and for the
nominee those are 0.706 of 17 quarters positive and four positive folds of four (#49). The nearest
thing to a chop failure in the ledger is #48, whose controls-off book is invested 2.5× as often and
whose two losing folds (F3 −1.37, F4 −0.48) are exactly the periods where single-name shocks are
frequent and cascades are not.

---

## 7. Is the snap-back real, or is it the spread?

The mandate is right that a reversal measured at 8h boundaries on a fast-turning book is where
execution assumptions flatter a result, so this is stated plainly.

| | 1× | 2× | 3× |
|---|---:|---:|---:|
| nominee behaviour (#49) net Sharpe | 0.931 | 0.738 | 0.544 |
| nominee annualised return | 15.3% | 11.6% | 8.0% |
| controls-off baseline (#48) net Sharpe | 0.461 | 0.237 | **0.013** |

The book loses about **0.19 of Sharpe per unit of cost multiple**. Tripling costs — 22.5 bps a side
against the tournament's 7.5 — leaves 58% of the 1× Sharpe standing and the annualised return
positive. The controls-off baseline loses 0.22 per multiple from a much lower base and is dead at
3×. Cost share of positive gross PnL is 4.7% at 1× and 14.2% at 3×, against a 30% ceiling.

Two structural reasons the cost drag is smaller than the raw turnover suggests, both of which are
properties of the tournament's own contract rather than of the strategy:

1. **The common risk unit makes cost drag scale-invariant.** Executed turnover and executed
   volatility are both proportional to `s_t`, so the Sharpe cost of turnover is
   `turnover_requested × 7.5 bps / volatility_requested` and does not depend on the scalar. The
   nominee's requested book runs at roughly 45% annualised volatility and is scaled to 17%.
2. **Holding costs nothing.** Returning `None` during the window means the only turnover in an
   episode is the entry and the exit. A book that re-weighted its basket each boundary over the same
   signal turned over 250–330× a year in exploratory work; this one turns over 43.7.

What this does **not** establish: the participation cap, the fill-at-next-open convention and the
7.5 bps/side model are all the organiser's, and a cascade bar is precisely when a real book's
slippage would be worst. A 3×-cost re-score is a proxy for that, not a measurement of it. The honest
statement is that the edge survives the proxy with room, not that the fills are realistic.

---

## 8. Falsification battery (#56)

Run as accepted trial #56 — the eleventh and last trial spent — over the full in-sample window
[2020-08-17, 2024-08-01), 2503 s.

### 8.1 Exact sign inversion

The harness negates every emitted weight, leaving `None` and `{}` alone because neither carries a
direction, and scores the result through the identical pipeline against the core floors.

| core floor | inverted book | |
|---|---:|---|
| `net_sharpe` | −1.321073 | fails |
| `double_cost_sharpe` | −1.513961 | fails |
| `triple_cost_sharpe` | −1.705250 | fails |
| `annualized_return` | −0.213018 | fails |
| `double_cost_annualized_return` | −0.239045 | fails |
| `max_drawdown` | 0.692092 | fails |
| `annualized_volatility` | 0.170467 | clears |
| `trade_count` | 3735 | clears |

**The inversion does not clear the core floors. The falsifier is satisfied.**

Two notes on how much that is worth. The two gates the inversion clears are the two a sign flip
cannot change: an inverted book trades the same bars at the same sizes and is scaled to the same
risk unit, so its volatility (0.1705 against the candidate's 0.1689) and its trade count (3735
against 3684) were never in question. Those two lines are structural, not evidence.

What is evidence is that the inversion comes out an almost exact arithmetic mirror. Fitting the
candidate's own three cost levels (0.9306 / 0.7376 / 0.5440) to `net(k) = g − k·c` gives an implied
gross Sharpe `g = 1.1240` and a cost drag `c = 0.1933` per unit of cost multiple. An inverted book
should then score `−g − k·c` — the gross term flips, the cost term is paid a second time instead of
being refunded:

| | predicted `−g − k·c` | measured | difference |
|---|---:|---:|---:|
| 1× | −1.3173 | −1.3211 | −0.0038 |
| 2× | −1.5106 | −1.5140 | −0.0033 |
| 3× | −1.7040 | −1.7053 | −0.0013 |

Within 0.004 at all three levels. The book's PnL is a sign-carrying function of its signal and of
essentially nothing else: no cost-model residue, no risk-unit artifact, no rebalance-schedule term
that would have paid in either direction. That is more informative than the pass/fail it is graded
on, and it is the part of §8.1 worth citing.

### 8.2 The gross-edge placebo, and what it says about where the edge lives

The control keeps the weight multiset and the rebalance schedule exactly and randomises **only**
which symbol receives which weight — drawing at each boundary from the eligible set, not from the
names the candidate picked. Because this book is equal-weight (`weight = 1.0 / len(ranked)`), the
multiset is degenerate, so the randomisation here is a pure name permutation and nothing else. It is
scored on **gross** edge, since a costed random book centres at minus its costs rather than at zero.

| | bps per unit one-way turnover | share of candidate |
|---|---:|---:|
| **candidate** (nominated point) | **42.5827** | — |
| placebo max, of 8 | 37.0853 | 87.1% |
| placebo median | 33.4906 | 78.6% |
| placebo min | 27.6012 | 64.8% |

**Exceedance 0.0000** — no placebo reached the candidate. The battery passes.

**The margin is narrow and it is not going to be described here as anything else.** A book that
gets the timing right and then buys eight names drawn at random from the eligible twenty captures
about four fifths of the gross edge density this candidate earns by buying the eight that fell
furthest. The residual attributable to the selection is **9.09 bps per unit turnover, 21% of the
total**, and the candidate beats the best of eight placebos by 5.50 bps. The pool the placebo draws
from is not "other fallers" — it is every eligible symbol, including names that *rose* on the
trigger bar. A harsher control than the obvious one still reproduces most of the result.

**Where that puts the edge.** The two controls in this certificate partition cleanly, because they
null different things:

- **§4 nulls the trigger** and lets the episodes move. Removing the breadth condition takes gross
  edge density from 42.6 to 22.3–22.4 bps per unit turnover (#48, #50) — the choice of *when* is
  worth roughly a factor of 1.9.
- **§8.2 nulls the attribution** and holds the episodes fixed. Randomising *which* names are bought
  inside those same episodes costs 21%.

So the edge is mostly in episode timing, and only secondarily in symbol selection. Sizing
contributes nothing separable, because the weights are equal by construction and the placebo
therefore preserves them exactly. The sweep in §9 says the same thing from a third direction: moving
the basket from the 6 deepest fallers to the 10 deepest — diluting from the most extreme names
toward less-shocked ones — moves net Sharpe by 0.011 and edge density by 1.5 bps. If name identity
carried the result, that would have cost more.

**Is this consistent with §1, or damaging to it?** Consistent with what §1 actually claims, and
damaging to a stronger reading of it that a reader could reasonably have taken. §1 claims a
liquidity event and its repayment: forced sellers overshoot, the excess is repaid. That is a claim
about *when* the market is dislocated, not about which name is most dislocated relative to its
peers. §2.3 measured exactly this before any trial was spent — the same conditioning on
cross-sectionally demeaned forward returns is flat to slightly negative — and disclosed it as the
single most important limitation of the result. The placebo confirms that pre-registered
measurement at the scored level rather than contradicting it. The pieces line up: a margin engine
unwinding correlated collateral is a *complex-wide* event, so the repayment accrues complex-wide,
so a random basket of the complex collects most of it.

What it damages is the implicit reading that this is a cross-sectional book which identifies the
most-overshot names. It is not, and nobody should size it as one. §12's first bullet was written as
a conditional before the battery ran, and **the condition has now fired**: the honest one-line
description of the nomination is *buy a basket of the complex two bars after a simultaneous
multi-name forced-selling event, hold three bars, be flat otherwise* — with the deepest-faller
ranking a modest refinement rather than the mechanism. That is a market-timing book. Its four
positive folds are four observations of a timing rule, which is a weaker statistical position than
3,684 quasi-independent cross-sectional bets would be, and a reader should discount accordingly.
The one thing it buys back: a book whose edge does not depend on picking specific names is less
hostage to any single name's liquidity than a selection book would be.

**And the instrument is blunt.** Eight draws. `0.0000` is the smallest exceedance this test can
report and it means "beat all eight", not `p < 0.001`. From the three reported order statistics a
crude range-based dispersion estimate puts the candidate about 2.7 standard deviations above the
placebo median; that is suggestive, and no tighter number should be defended from eight draws with
only min/median/max in hand.

---

## 9. The declared neighbourhood and its sweep (#55)

**The nominee was fixed before the neighbourhood was declared.** The nominee's behaviour was chosen
at trial #49; `neighbourhood.json` was written afterwards, validated by the free `--check`, and the
`--kind neighbourhood` trial was journaled against the resulting digest. The nominee has not moved
since.

Coordinates, all three module-level single-valued numeric literals in the frozen `strategy.py`:

| coordinate | nominee | below | above | why this axis |
|---|---:|---:|---:|---|
| `SHOCK_Z` | −2.0 | −2.25 | −1.75 | how far a member's move must outrun its own scale |
| `BASKET_NAMES` | 8 | 6 | 10 | how many of the deepest fallers the basket holds |
| `LOOKBACK_BARS` | 60 | 45 | 80 | the window "its own recent scale" is measured over |

Seven points including the nominee, `max(7, 2·3+1) = 7`; every point distinct; every variation at
least 12% of the nominee's magnitude against a 5% requirement.

**Two axes were deliberately not declared, and both refusals are disclosed with their numbers,
because either would have been a lever on the median rather than an exploration of the plateau.**

- **`MIN_BREADTH`.** Its only legal downward variation is 1, and `MIN_BREADTH = 1` is not a
  neighbouring parameterisation — it is the ablation (#50 measures it at G −10.48). A neighbourhood
  containing its own control-off point is not a robustness estimate. A non-integer variation is
  worse: the constant is consumed as `qualifying < MIN_BREADTH`, so 1.5 and 2 produce a
  byte-identical book, which is exactly the inert coordinate amendment A1 voids a sweep for.
- **`HOLD_BARS`.** Measured at 2 (#53, G −9.02) and it is a cliff, not a plateau, for the reason
  §2.4 gives: the impulse response is three bars wide and dropping one of them removes a third of
  the repayment while keeping the entry cost. Declaring it would have priced a known cliff into the
  median. It is reported here instead, which is the fair instrument.

### 9.1 The sweep, as measured

Trial #55. Source `366b7da1…`, snapshot `ceeedfcd…`, window [2020-08-17, 2024-08-01), seed 20240801,
folds F1 [2020-08-17, 2021-08-01) / F2 [2021-08-01, 2022-08-01) / F3 [2022-08-01, 2023-08-01) /
F4 [2023-08-01, 2024-08-01). Seven points, four workers, 979.8 s. Every point was separately
materialised and separately executed, with a distinct `strategy.py` digest — no point reproduced the
nominee's vector, so the §7.2 / A1 inertness check is clean.

| point | coordinates | 1×/2×/3× Sharpe | ann. ret | turnover | bps/turn | maxDD | trades | F1 / F2 / F3 / F4 (2×) | B |
|---|---|---|---:|---:|---:|---:|---:|---|---:|
| **nominee** | z −2.00, names 8, look 60 | 0.931 / 0.738 / 0.544 | 0.1532 | 43.73 | 42.58 | 0.1906 | 3684 | +0.98 / +1.47 / +0.16 / +0.48 | 0.9950 |
| point-1 | z **−1.75** | 0.990 / 0.765 / 0.539 | 0.1661 | **51.27** | **39.63** | 0.1741 | 4800 | +1.41 / +0.92 / +0.36 / **−0.07** | 0.9965 |
| point-2 | z **−2.25** | 0.614 / 0.439 / 0.264 | 0.0932 | 39.27 | **33.02** | **0.2125** | 2973 | +0.80 / +0.72 / **−0.15** / +0.28 | 0.9500 |
| point-3 | names **6** | 0.893 / 0.705 / 0.517 | 0.1482 | 43.04 | 42.19 | 0.1927 | 2711 | +0.86 / +1.59 / +0.29 / +0.31 | 0.9930 |
| point-4 | names **10** | 0.903 / 0.705 / 0.506 | 0.1448 | 43.95 | 40.69 | 0.1922 | 4641 | +0.90 / +1.63 / +0.14 / +0.31 | 0.9920 |
| point-5 | look **45** | 1.011 / 0.811 / 0.611 | 0.1664 | 44.38 | 44.60 | 0.1793 | 3808 | +1.19 / +0.78 / +0.16 / +1.10 | 0.9970 |
| point-6 | look **80** | 1.033 / 0.847 / 0.661 | 0.1748 | 42.43 | 48.11 | **0.2238** | 3672 | +1.17 / +1.55 / +0.33 / +0.43 | 0.9925 |

**The score is the per-metric median across those seven rows**, not the nominee's row: net Sharpe
**0.930629**, 2× **0.737588**, 3× **0.538556**, annualised return **0.153175**, turnover
**43.731810**, gross edge **42.189005** bps/turn, max drawdown **0.192184**, volatility **0.169044**,
cost share of positive gross **0.045214**, top-5-day share **0.122355**, max fold share of positive
PnL **0.418744**, positive quarters **12 of 17 (0.705882)**, positive folds **4**, worst fold
**+0.159843**, median fold **+0.638312**, trades **3684**, long gross PnL **+0.737235**, short gross
PnL **−0.000000**.

`positive_point_fraction` **1.0000** against the 0.70 floor — all seven points have a positive 1×
return and a positive 2× Sharpe. `B` **0.9930** (median across points), `T` **11**, trial-adjusted
confidence **0.9230** against 0.90.

**The nominee turns out to sit at the median of its own star, not on top of it.** On net Sharpe
three points score above it and three below, and the median lands exactly on the nominee's own value;
the same holds for annualised return, turnover, positive-quarter fraction, worst fold and trade
count. The usual sweep pathology — a nominee that is the peak of a noisy surface and a median that
collapses beneath it — is absent. That is a property of the surface, not a decision: the nominee was
fixed at trial #49, six trials before the neighbourhood was declared, and it could as easily have
landed on a spike.

**`SHOCK_Z` is the load-bearing coordinate; the other two are flat.** Both threshold variations lose
a fold (point-1 F4 −0.07, point-2 F3 −0.15) and neither of the basket-size or formation-window
variations does. Loosening to −1.75 buys 0.06 of Sharpe by trading 17% more (turnover 51.27) at an
edge density of 39.63 that would miss the 40-bps floor on its own; tightening to −2.25 costs 0.32 of
Sharpe and 9.6 bps of density. Basket size is close to free over 6–10 (0.893 / 0.931 / 0.903), which
is the §8.2 finding seen from a different angle. The formation window is a shallow ridge rather than
a peak at 60: both 45 and 80 score *higher* than the nominee at every cost level, and 80 has the
star's best edge density (48.11) together with its worst drawdown (0.2238, over the 0.20 ceiling on
its own). The nominee is a conservative point on that axis, not an optimised one — and stated the
other way round, which is the honest way: had the nominee been chosen as the star's maximum-Sharpe
point, the drawdown floor would have been at risk. That is an observation about the surface made
after the fact, not a reason the choice was made.

**The turnover result the star adds, which §10.6 could only assert.** Across all seven points
turnover runs 39.27–51.27. The minimum, at `SHOCK_Z` −2.25, is still **57% above the ceiling**, and
reaching it costs 0.32 of net Sharpe, 9.6 bps of edge density and a negative fold. No point in the
declared neighbourhood comes near 25×. That is now measured rather than argued.

**The score.** `G` = **30.363**, which is `G_core` **35.084** multiplied by a compliance factor of
**0.8654** (amendment A5 — the mean credit across the thirteen graded floors the ranking formula
does not itself price). Eleven of the thirteen take full credit; annualised turnover takes
**0.2507**, graded on relative shortfall from 43.73 against 25; `role_short_gross_pnl` takes **0**,
because a bare `> 0` gate has no scale to grade against and is binary. `(11 + 0.2507 + 0) / 13 =
0.8654`.

The compliance factor costs **4.72 points of G**, and it is worth splitting because the split is not
the one §10.6's ordering implies: the **absent short sleeve costs 2.70 points** (a full thirteenth)
and the **turnover shortfall costs 2.02**. The larger of the two penalties is the one taken
deliberately in §6 on measured evidence that every short configuration lost. That was a priced
decision and this is the price.

---

## 10. Failures, dead ends and everything abandoned

**10.1 The first design — basket sized by threshold-crossing count (#46, #47).** The original book
bought exactly the names that crossed both thresholds, so the *number* of names that happened to
qualify set the book's exposure. The organiser's `exposure_caps` block made the consequence visible:
78 of 276 emitted rows were reduced to `minimum_scale 0.4000` with the per-symbol cap binding — more
than half of all entries executed at 0.40 gross because they carried exactly two names, while an
eight-name cascade executed at 1.00. Charter §14.7 does not redistribute the trimmed weight back.
Fixing the basket at a structural size removed the trim entirely (0 of 276 rows reduced at #47) and
was worth +0.6 of G on its own; the design change that mattered came later (§4).

**10.2 The trade-count spike (S2).** Pre-registered as a forced-flow separator; measured as a
subtraction. See §4.

**10.3 Overlapping-slice construction.** Abandoned in exploratory work before any trial: 250–330×
annual turnover at ~10 bps of gross edge per unit of it. No trial was spent on it because the
turnover arithmetic in §2.5 is not an empirical question.

**10.4 Three attempts to flatten the parameter surface, all of which made the book worse.**
Measured in exploratory work on the star median rather than the peak: refreshing the basket when a
new cascade fires mid-hold, tapering the exit over two half-exits, and sizing by shock intensity
rather than equal weight. Every one of them diluted the narrow impulse response of §2.4 and reduced
both the nominee and the star median. None was scored.

**10.5 Declared risk controls — both instruments rejected on mechanism and on measurement.** The
policy schema offers a drawdown brake and a position stop, and drawdown control is 35 of the 100
ranking points, of which this book earns very few. Neither was declared:

- A **drawdown brake** is pro-cyclical against this book. Its opportunities *are* drawdown events: a
  cascade is what puts a long book under water, so a brake keyed on the book's own drawdown would
  cut exposure precisely as the next cascade arrives. Rejected on mechanism, before measuring.
- A **position stop** was measured and is contraindicated. Conditional on the first held bar, the
  remaining two bars return **+563.7 bp** (t = 2.9) when the first bar was worse than −10%, against
  **+79.9 bp** when it was mildly positive. A position still falling means the forced flow is still
  running and the overshoot is still growing, not that the thesis was wrong. Every stop level
  reduced the mean episode return monotonically (155.7 bp unstopped → 147.6 at −15% → 136.2 at −10%
  → 131.6 at −5%).

The declared policy is therefore flat, with `volatility_target.enabled` **false** (charter §6,
amendment A3). The ban was never a constraint here — this book's problem is that its turnover is too
high, and A3's exploit only helps a team whose turnover is too *low*. Recording it anyway: the
interaction was understood and not used.

**10.6 What the nomination gives up, stated as a number.** The nominee misses three floors: 1× net
Sharpe (0.931 against 0.80 — this one **passes**; see §11 for the medians), annualised turnover
(43.7 against 25, credit 0.251) and `role_short_gross_pnl` (no short sleeve, credit 0). Under
amendment A5 those cost a multiplicative compliance factor of about 0.87. They are not argued away
and no attempt was made to reach the turnover ceiling by paperwork: the only honest routes are a
slower formation, a longer hold or fewer events, and #52, #53 and the flow-gate family measured all
three making the book worse rather than better.

---

## 11. Floors, as measured

### 11.1 The gate vector

Every floor below is read off the **neighbourhood median** from #55 (§9.1), which is the record the
floors are evaluated on, except `sign_inversion_not_profitable`, which a sweep cannot decide and
which #56 decided (§8.1).

| floor | measured | required | |
|---|---:|---|---|
| `net_sharpe` | 0.930629 | ≥ 0.80 | PASS |
| `double_cost_sharpe` | 0.737588 | ≥ 0.50 | PASS |
| `triple_cost_sharpe` | 0.538556 | > 0 | PASS |
| `annualized_return` | 0.153175 | > 0 | PASS |
| `double_cost_annualized_return` | 0.115988 | > 0 | PASS |
| `max_drawdown` | 0.192184 | ≤ 0.20 | PASS |
| `annualized_volatility` | 0.169044 | ≥ 0.06 | PASS |
| `positive_quarter_fraction` | 0.705882 | ≥ 0.50 | PASS |
| `positive_fold_count` | 4 | ≥ 3 | PASS |
| `worst_fold_sharpe` | +0.159843 | ≥ −0.25 | PASS |
| **`annualized_turnover`** | **43.731810** | **≤ 25** | **FAIL** |
| `gross_edge_bps_per_turnover` | 42.189005 | ≥ 40 | PASS |
| `cost_share_of_positive_gross` | 0.045214 | ≤ 0.30 | PASS |
| `top5_day_share` | 0.122355 | ≤ 0.35 | PASS |
| `max_fold_positive_pnl_share` | 0.418744 | ≤ 0.60 | PASS |
| `trade_count` | 3684 | ≥ 500 | PASS |
| `neighbourhood_positive_fraction` | 1.000000 | ≥ 0.70 | PASS |
| `trial_adjusted_confidence` | 0.923000 | ≥ 0.90 | PASS |
| `declared_roles_match_traded_sides` | declared `['long']`, traded `['long']` | — | PASS |
| `role_long_gross_pnl` | 0.737235 | > 0 | PASS |
| `sign_inversion_not_profitable` | inversion fails 6 of 8 core floors (§8.1) | — | PASS |

**Nineteen of twenty measured floors pass, plus the falsifier. One fails.** Verdict as reported:
`FAILS 1 measured floor(s)`; `G` 30.363.

### 11.2 The failure, stated plainly

**Annualised one-way turnover is 43.731810 against a ceiling of 25.** The book trades 1.75× the
permitted rate. This is not a rounding matter and it is not disputed: it is the single measured floor
this nomination does not clear, it carries a graded credit of 0.2507, and through the A5 compliance
factor it removes 2.02 points of `G`.

Why it is where it is, and what was done about it, is already on the record and is not re-argued
here: §2.5 gives the arithmetic (a book that enters once and exits once still pays about 2.0 units of
turnover per episode, so turnover is set by the event rate, not by signal quality), §10.6 names the
only three honest remedies — a slower formation, a longer hold, fewer events — and #52, #53 and the
flow-gate family measured all three making the book worse. §9.1 adds the measurement those sections
could not have: across the seven declared points turnover ranges 39.27–51.27, and its minimum is
still 57% above the ceiling. Nothing in this design's neighbourhood reaches 25.

### 11.3 The passes that are thin, and the ones that are not

Three floors pass by less than 6% of their threshold and should be read as passing, not as cleared:

- **`max_drawdown` 0.192184 against 0.20** — 3.9% of headroom, the thinnest margin in the vector.
  And the median passing is not the same as the surface sitting inside the ceiling: two of the seven
  declared points breach it individually (point-2 at 0.2125, point-6 at 0.2238).
- **`gross_edge_bps_per_turnover` 42.189 against 40** — 5.5% of headroom, with two of seven points
  individually under the floor (point-1 at 39.63, point-2 at 33.02).
- **`trial_adjusted_confidence` 0.9230 against 0.90** — 2.6% of headroom. The arithmetic is
  `1 − T(1 − B)` with `T = 11` and `B = 0.9930`, so at this `B` the floor requires `B ≥ 0.9909`;
  the margin is 0.0021 of `B`. A twelfth accepted trial would give 0.9160 and still pass; the floor
  breaks at `T ≥ 15`.

The rest pass with room that is not in question: cost share 0.045 against 0.30, top-5-day share
0.122 against 0.35, max fold share of positive PnL 0.419 against 0.60, trade count 3684 against 500,
volatility 0.169 against 0.06, worst fold +0.160 against −0.25.

---

## 12. What would change my mind

- **The beta caveat (§2.3).** If the placebo in §8 reproduces most of the gross edge, the honest
  description of this book is "buy the complex after a deleveraging", with name selection adding
  little. That is still the lane's mechanism, but it is a market-timing book rather than a
  cross-sectional one, and a reader should size their confidence accordingly.
- **The window.** The in-sample period is a net-rising four years for a long-only book. F2 and F3
  contain the 2022 bear and both are positive for the nominee, which is the main evidence against
  "this is just beta", but four folds is four observations.
- **F4's shifted impulse response.** In the last fold the repayment arrives one bar earlier than in
  F1–F3 (bar +1 positive, bar +2 negative). The chosen entry delay is right for three folds of four
  and wrong for one. If that shift is a permanent microstructure change rather than noise, the entry
  delay is the parameter that will decay first.
