# Team 11 — Research Certificate

Lane: `calendar-settlement-clock-seasonality`
Workspace: `tournament/cup20/teams/team-11/`
Data root: `data/cup20/is/` (nothing else was opened; the sealed holdout tree was never touched, and
the organiser's workspace scan at trial #115 read 90 files and recorded zero violations)

| | |
|---|---|
| nominee | `desk-closed-share` |
| journaled source sha256 | `90e0dfbf2347fe2a9c14455c53afd9e2bcb7e544717051e6804e9b840d4f32fb` |
| `strategy.py` file sha256 | `dbb6443ee50adffadcaa5f9c3475ba171976e4978519d76a2753e24885606cd1` |
| risk policy sha256 | `811fec7d201bfafb3294884d5bd6ccca429ef73e789e104917f8a64e42e5ee7a` |
| snapshot sha256 | `ceeedfcd7117a16a58d2bb9bbf9716356c9473098fe8512703d1656834746d48` |
| seed | 11 |
| trials | 8 accepted, journal sequences #112–#119; T = 2 under amendment A6 |
| declared roles | long, short |

**Status: complete.** The nominee was frozen at trial #112 and never changed; the neighbourhood was
declared afterwards and swept at #115. Nothing in this document is provisional.

---

## 0. What this lane found, in one page

**The aggregate calendar is noise, and the cross-sectional calendar is not.**

Measured on the full in-sample window, the equal-weight universe return shows no usable drift in
any calendar cell: the strongest of three intraday slots reaches t = +1.27, the strongest of seven
weekdays t = +1.56, and every one of the 21 day-of-week × slot cells changes sign between the two
halves of the window. "Buy Mondays" is dead on this sample and this certificate records it as
dead.

What survives is not a drift but a **characteristic**: *which* coins trade *when*. A coin's share
of trading activity that lands in the calendar cells where professional desks are shut — the
00:00–08:00 UTC settlement session and the weekend — predicts its cross-sectional return
negatively, stably in both halves of the window, and does so because of the clock rather than in
spite of it.

**The mandate's headline question is not identified on this snapshot, and that is a finding.**
The task asks whether the settlement boundary behaves differently from an arbitrary 8h boundary.
On these data it cannot be asked: **100.0000% of eligible symbol-boundaries carry a funding
settlement at the boundary** (86,658 of 86,658). The 8h decision grid *is* the settlement clock,
for every symbol, at every boundary. There is no arbitrary 8h boundary to control against, so the
matched control had to be constructed differently — see §5.

**The scored result**, trial #115, the per-metric median across the declared nine-point
neighbourhood, which is what section 7.2 ranks:

| | |
|---|---:|
| ranking score **G** | **50.449** |
| net Sharpe 1× / 2× / 3× | 0.8597 / 0.7697 / 0.6795 |
| annualised return 1× / 2× | 0.0980 / 0.0865 |
| annualised volatility | 0.1174 |
| maximum drawdown 1× / 2× | 0.1010 / 0.1019 |
| worst fold Sharpe (2×) / positive folds | +0.2854 / 4 of 4 |
| positive quarters | 11 of 17 (0.647) |
| annualised one-way turnover | 14.34 |
| gross edge | 78.83 bps per unit turnover |
| cost share of positive gross | 0.0080 |
| top-5-day share / max fold PnL share | 0.0270 / 0.2702 |
| trades | 7,092 |
| neighbourhood points positive | 9 of 9 |
| trial-adjusted confidence | 0.9350 (B = 0.9675, T = 2) |
| measured floors failed | **1 — `role_short_gross_pnl` = −0.065736, required > 0** |
| falsification (#116) | sign inversion does not clear the core floors — **passes** |

**One floor fails and it is not a technicality.** Under amendment A4 the in-sample stage ranks
rather than gates, so the miss is priced: the equal-weighted compliance factor of 0.9231 — twelve of
the thirteen floors that the ranking's own terms do not otherwise price — takes G_core 54.65 down to
the 50.449 above. The next section says what
the miss actually means, because it is a statement about the book and not about the scoring rule.

---

## 0.1 The headline weakness: the short sleeve lost money gross

**The names this book's clock signal told it to short did not fall.** Over the four-year window the
short sleeve returned a gross PnL of **−0.0657** at the neighbourhood median (−0.0498 at the
nominated point) against **+0.5168** for the long sleeve. The book is profitable, dollar-neutral and
low-drawdown, and it is profitable entirely because of what it was long and only in spite of what it
was short.

That is not a rounding artifact and this certificate will not treat it as one. Three things were
measured about it.

**(a) It is not a phase, window or parameter artifact.** Across **299 configurations of the
corrected offline bench** — every cell, every activity window, every volatility window, every
weighting exponent, all 21 weekly phases, seven cadences — the short sleeve's gross PnL is negative
in **296**. All three exceptions are the *non-neutralised* variant of the desk-closed book. On the
21-point phase surface at the nominee's own windows, the short sleeve is negative at every one of
the 21 phases, ranging from −0.0498 to −0.2845 with a median of −0.1712. There is no corner of this
design in which the short side pays.

**(b) The one thing that flips it is the control that keeps this lane in its lane.** Removing the
cross-sectional volatility projection — ablation `raw-share`, trial #114 — turns the short sleeve
positive (+0.0300) and raises net Sharpe to 1.088. That is because the raw desk-closed share is
cross-sectionally correlated with realised volatility (§4): shorting it raw is partly shorting
high-beta, and on this window high-beta names fell. The neutralisation strips exactly that, and with
it the short sleeve's only source of gross profit. What the raw variant bought with its positive
short sleeve is visible in the same packet: maximum drawdown 0.179 against 0.101, a fourth fold of
−0.296 that breaks the worst-fold floor, and G 35.76 against 50.45. **The negative short sleeve is
the price of not being a volatility book.** It is a deliberate and disclosed trade, not an accident,
and the reader is entitled to think the trade was wrong.

**(c) Part of it is the window and this certificate cannot say how much.** In a dollar-neutral
cross-sectional book each sleeve's gross PnL carries the universe's own drift with opposite signs,
and this universe drifted up: §2 measures a positive mean equal-weight return in two of three
intraday slots and five of seven weekdays. A short sleeve that merely failed to fall enough will
print negative gross in such a window. I did not measure a clean drift-versus-selection
decomposition of the two sleeves, so I do not claim one, and I do not claim the short side "really"
worked once the market is removed. What the floor measures is the raw sleeve, and the raw sleeve
lost money.

**What I expect to persist.** The mechanism says a coin whose activity concentrates in the
desk-closed cells is priced by leveraged retail perpetual flow. That predicts *relative*
underperformance, not absolute decline, so in a rising universe I expect the short sleeve to keep
printing negative gross PnL, and in a falling one I expect it to carry the book. The honest form of
this candidate's claim is therefore about the **spread**, not about either sleeve standing alone,
and a deployment that cannot tolerate a short book that loses money gross for four years should not
deploy this one.

**One disclosure that cuts against me.** The nominated phase, 4, happens to have the *least*
negative short sleeve of all 21 phases (−0.0498 against a surface median of −0.1712). The
neighbourhood median that gets scored, −0.0657, is therefore flattering relative to the mechanism at
large. Had the phase been chosen anywhere else on the weekly surface, the reported miss would have
been two to five times larger.

---

## 1. The window, and the effective sample per calendar cell

| | |
|---|---|
| IS window | `[2020-08-17T00:00:00Z, 2024-08-01T00:00:00Z)` |
| decision boundaries | 4,335 |
| mean eligible members per boundary | 19.99 |
| eligible symbol-boundaries | 86,658 |

**Effective sample per calendar cell.** The unit of independent observation is the *boundary*, not
the symbol-boundary: twenty crypto perpetuals at one instant are one draw from a market with one
dominant factor, not twenty. Stating the symbol count would inflate every t-statistic in this
document by roughly √20.

| cell type | cells | boundaries per cell | symbol-observations per cell |
|---|---:|---:|---:|
| intraday slot | 3 | 1,445 | 28,886 |
| day of week | 7 | 619 | 12,380 |
| **day-of-week × slot** | **21** | **206** | 4,127 |

206 boundaries per interaction cell is the number that governs how much of this lane can be
believed. It is why no result in this certificate rests on a day-of-week × slot interaction, and
why the two cells that are used — the intraday settlement session and the weekend — are the two
largest cells available (1,445 and 1,238 boundaries).

---

## 2. The aggregate calendar: measured, and negative

`research/eda_calendar.py`. Equal-weight universe open-to-open return per boundary.

| slot | n | mean (bp) | t | 1st half | 2nd half |
|---|---:|---:|---:|---:|---:|
| 00:00–08:00 | 1445 | +8.36 | +1.27 | +10.54 | +6.17 |
| 08:00–16:00 | 1445 | −0.30 | −0.04 | +4.81 | −5.39 |
| 16:00–24:00 | 1444 | +5.85 | +0.86 | +6.00 | +5.70 |

| weekday | n | mean (bp) | t | 1st half | 2nd half |
|---|---:|---:|---:|---:|---:|
| Mon | 621 | +1.44 | +0.13 | −4.04 | +6.98 |
| Tue | 621 | −2.34 | −0.24 | +8.08 | −12.74 |
| Wed | 620 | +4.46 | +0.37 | +8.79 | +0.15 |
| Thu | 618 | −0.75 | −0.07 | +0.82 | −2.32 |
| Fri | 618 | +7.53 | +0.75 | +2.80 | +12.26 |
| Sat | 618 | +13.91 | +1.56 | +20.04 | +7.79 |
| Sun | 618 | +8.26 | +0.90 | +13.44 | +3.08 |

Nothing here clears any reasonable bar once the ten cells tested are accounted for, and the
21-cell interaction table is worse: its largest entries (Thu 16:00–24:00 at −27.6 bp, Tue
08:00–16:00 at −19.5 bp) rest on 206 boundaries each and do not repeat.

**What is stable in the aggregate is not the return but the shape of the day**, and that is what
the rest of this certificate uses:

| slot | share of quote volume | cross-sectional dispersion |
|---|---:|---:|
| 00:00–08:00 | 27.4% | 162.8 bp |
| 08:00–16:00 | 39.4% | 175.3 bp |
| 16:00–24:00 | 33.2% | 158.6 bp |

---

## 3. The measure that survives, and how it was found

`research/ic_study.py`, `research/eda_broad.py`, `research/eda_offhours.py`.

Before a single trial was spent, **412 causal measures were evaluated** as cross-sectional rank
ICs against the 1-, 3-, 6-, 9- and 21-bar forward open-to-open return, in five families:

| family | what it is | verdict |
|---|---|---|
| A | plain close-to-close momentum over 1–252 bars (the no-calendar control) | reverses weakly, IC −0.033 at 1 bar |
| B | slot- and weekend-decomposed formation returns, and their tilts | no incremental content over A |
| C | **share of activity in a calendar cell** (quote volume, trade count, absolute return) | the survivor |
| D | session-conditional realised-volatility spreads | duplicates C |
| E | intrabar (open→close) session drift decomposition | no content |

**One methodological trap is worth recording because it would have cost a trial.** The evaluator
earns `open[t+1]/open[t] − 1`, so a formation built from *open* returns shares the price `open[t]`
with the forward return and inherits a mechanical negative correlation from bid–ask bounce. On the
first pass this produced a spectacular-looking lag-1 cross-sectional reversal at the 00:00 UTC
decision (IC −0.0708, t = −9.36) that is largest exactly where spreads are widest. Every formation
in this certificate is therefore built from **close prices of already-closed bars**, which share no
price with the forward return. The finding is reported as a measurement artifact, not as alpha.

### 3.1 Why the two cells are one mechanism

Family C's best cells are the **00:00–08:00 UTC settlement session** and the **weekend** — the two
calendar cells in which professional desks are shut. They behave alike and they compose:

| cell (activity = bar trade count, W = 378 bars) | IC | t | 1st half | 2nd half |
|---|---:|---:|---:|---:|
| 00:00–08:00 UTC only | −0.0245 | −5.54 | −0.0137 | −0.0335 |
| weekend only | −0.0225 | −4.84 | −0.0017 | −0.0396 |
| **union (desk-closed)** | **−0.0278** | **−6.07** | −0.0111 | −0.0417 |
| weekday 00:00–08:00 only | −0.0172 | −3.96 | −0.0124 | −0.0211 |

The union beats either half, which is what one mechanism seen at two frequencies looks like and
not what two unrelated calendar coincidences look like. Both halves of the window carry the same
sign in every row.

**The table above is measured on trade count and the frozen book trades quote volume.** That is a
deliberate mismatch and it is disclosed here rather than left for a reader to find: the cell was
selected on the trade-count ICs, and the activity *quantity* was then chosen at the book level (§8),
where quote volume was clearly better. The two quantities agree at the IC level — desk-closed share
at W = 252 gives IC −0.0247 (t = −5.67) on trade count and −0.0240 (t = −5.57) on quote volume — so
nothing about the cell selection depends on which one is used.

**The effect is materially stronger in the second half of the window.** That is stated here rather
than buried: the sign holds in both halves for every cell and window tested, but the first-half
t-statistics sit between −1.0 and −2.4 while the second-half ones sit between −3.3 and −6.7. A
reader should treat the first half as *consistent with* the mechanism and the second half as the
evidence.

---

## 4. Is it the clock, or is something else wearing a clock?

`research/eda_neutralise.py`, `research/eda_offhours.py`. This is the lane's own discipline test,
and it is reported in full including the part that goes against the candidate.

A share-of-activity measure is mechanically correlated with things that are emphatically not
calendar, three of which belong to other lanes. Each control is a cross-sectional rank,
residualised out of the measure boundary by boundary:

| desk-closed share, W = 378, residualised on | IC | t | 1st half | 2nd half |
|---|---:|---:|---:|---:|
| nothing (raw) | −0.0249 | −5.43 | −0.0069 | −0.0397 |
| realised volatility | −0.0132 | −3.07 | −0.0003 | −0.0238 |
| size (log trailing quote volume) | −0.0149 | −3.24 | −0.0000 | −0.0273 |
| momentum (63 bars) | −0.0244 | −5.56 | −0.0059 | −0.0397 |
| funding crowding (mean \|funding\|) | −0.0137 | −3.10 | +0.0025 | −0.0271 |
| **all four together** | **−0.0073** | **−1.77** | +0.0004 | −0.0137 |

**Read honestly: roughly 30% of the raw predictive content of the desk-closed share is orthogonal
to volatility, size, momentum and funding crowding, and roughly 70% is shared with them.** The two
largest overlaps are realised volatility (lane 06) and funding crowding (lane 07). Momentum is not
an overlap at all — residualising on it slightly *strengthens* the measure.

The reverse direction is reported too, and it does not flatter this lane: realised volatility
residualised on the desk-closed share still carries IC −0.0478 (t = −9.47), roughly twice the raw
calendar measure. Volatility is the stronger standalone predictor on this window. This lane's
claim is not that the clock beats volatility; it is that the clock carries content volatility does
not, and that the clock is doing the work of *defining* the characteristic.

The frozen book projects out **one** control, realised volatility, because that is the largest
overlap and the one that turns the book into another lane's book. The four-way combined control was
measured at the IC level (the table above, and the same test at W = 126 and W = 252, all three
negative, t between −1.77 and −1.97) but **was never scored under a trial** — see §14.

---

## 5. The settlement-boundary control, and why it had to be built differently

**The mandate's headline control is not identified on this snapshot.** Every eligible
symbol-boundary carries a funding settlement at the boundary:

```
eligible symbol-boundaries                          86,658
  ... carrying a settlement AT the boundary         86,658   (100.0000%)
  ... carrying an EXTRA mid-bar settlement             653   (  0.7535%)
```

The 8h decision grid and the settlement clock are the same object here, for every symbol, at every
boundary. There is no "arbitrary 8h boundary" in these data to control against, and any team that
plans a settlement-versus-arbitrary-boundary test on this snapshot should know that before
budgeting a trial for it. Two consequences:

**(a) The only real settlement contrast available is the mid-bar one.** 0.75% of eligible bars sit
in a 4h or 2h funding regime and therefore carry an *extra* settlement inside the bar. Those bars
are more violent — mean |return| 268.6 bp against 209.0 bp — but at 653 observations concentrated
in a handful of symbol-periods this is a disclosure, not a result, and nothing in the candidate
rests on it.

**(b) The matched control that does have teeth is a scrambled clock.** Instead of contrasting
settlement against non-settlement boundaries, contrast the *true* clock partition against a
partition of identical shape whose alignment with the clock has been destroyed:

* each calendar day independently permutes its **own** three settlement slots, so every pseudo cell
  still receives exactly one bar per day;
* each week independently nominates two of its **own** seven days as the pseudo weekend, so the
  pseudo weekend is always exactly two days.

Cell sizes, coin mix, volatility mix and sample size are all held exactly. Only the clock moves.
300 draws, `research/eda_clock_null.py`:

| measure (W = 126) | true IC | null mean | null sd | z | p (one-sided) |
|---|---:|---:|---:|---:|---:|
| Asia-session volume share | −0.0202 | +0.0009 | 0.0046 | **−4.56** | 0.0000 |
| US-minus-Asia volume share | +0.0140 | +0.0002 | 0.0049 | **+2.81** | 0.0000 |
| Asia-session volatility share | −0.0144 | +0.0000 | 0.0046 | −3.15 | 0.0033 |
| weekend volatility share | −0.0246 | +0.0006 | 0.0044 | **−5.78** | 0.0000 |
| desk-closed volume share | −0.0227 | +0.0004 | 0.0051 | **−4.54** | 0.0000 |
| desk-closed volume share (W = 252) | −0.0240 | −0.0001 | 0.0057 | −4.19 | 0.0000 |

A shape-matched scrambled clock produces essentially nothing (null means within ±0.0009 of zero).
The alignment with the real settlement and working-week clock is what makes the characteristic
exist at all. The same scramble was then executed as a **scored book** at trial #113 — §10.

**One caveat, stated because it limits the claim.** A cruder null — relabelling the three
settlement slots globally rather than per day — cannot separate *which* of the three sessions is
the negative one (p = 0.33, because there are only three cells and therefore only three distinct
values). So: the clock partition demonstrably carries information (z = −4.5); the identification of
00:00–08:00 specifically as the negative session rests on the mechanism (thinnest global liquidity
window, 27.4% of quote volume) plus a 1-in-3 in-sample choice, not on the null. The weekend half of
the cell does not have this problem — its null ranges over all 21 two-day cells and the true
weekend beats it at z = −5.8.

---

## 6. Out-of-cell prediction

`research/eda_out_of_cell.py`. The strongest defence available to a seasonality lane: estimate the
pattern on one part of the calendar and test it on a part not used to estimate it. Numerator and
denominator of the share are both restricted to the measurement cell, so the measurement cell and
the prediction cell share no bar at all. W = 252.

| split | IC | t | n |
|---|---:|---:|---:|
| Asia share measured **Mon–Wed**, tested at **Thu–Sun** boundaries | −0.0061 | −1.18 | 2,328 |
| Asia share measured **Thu–Sun**, tested at **Mon–Wed** boundaries | −0.0352 | −6.10 | 1,754 |
| Asia share measured **even ISO weeks**, tested on **odd weeks** | −0.0156 | −2.90 | 2,045 |
| Asia share measured **odd ISO weeks**, tested on **even weeks** | −0.0236 | −4.27 | 2,037 |
| *(reference: measured and tested on everything)* | −0.0216 | −5.58 | 4,082 |

The characteristic transfers out of cell in three of four splits with the correct sign, and the
week-parity split — the cleanest of the four, since it does not confound the measurement cell with
the prediction cell's own weekday composition — transfers in **both** directions at t = −2.90 and
t = −4.27. The Mon–Wed measurement is the weak one, which is consistent with the weekend carrying
much of the cell's information.

The half-window split holds sign for the Asia share (H1 −0.0168 t = −3.07, H2 −0.0257 t = −4.73)
and for the US-minus-Asia contrast at W = 252 (H1 +0.0036, H2 +0.0263), though the latter's first
half is not significant and it *flipped* sign at W = 126 in the raw form. The US-minus-Asia
contrast was therefore **not** used in the candidate; the desk-closed union was.

---

## 7. The offline bench, and how far it can be trusted

`research/fastsim.py`, `research/calibrate.py`. Every design decision in this certificate was made
on an offline replica of the organiser's two-pass evaluation, written by reading
`crypto_trade.cup20.runner`, `crypto_trade.cup20.risk_unit` and
`crypto_trade.tournament.engine_v2` and restricted to the inert-risk-policy branch this team
actually uses. **No number the replica produces is reported as a result** — every scored number
below comes from `scripts/cup20_evaluate.py` under a journaled trial.

Calibrated against the organiser's own `run_candidate` on a transparent 21-bar reversal book
rebalanced every 3 bars, over the full in-sample window:

| metric | organiser | replica | residual |
|---|---:|---:|---:|
| net Sharpe 1× | −1.387613 | −1.414285 | −0.026672 |
| net Sharpe 2× | −1.978861 | −2.005383 | −0.026522 |
| annualised volatility 1× | 0.119462 | 0.119310 | −0.000152 |
| maximum drawdown 1× | 0.528214 | 0.528218 | +0.000004 |
| annualised turnover | 94.204031 | 94.097633 | −0.106397 |
| cost share | 0.057096 | 0.057230 | +0.000134 |
| trade count | 32,171 | 32,157 | −14 |
| fold Sharpe F2 / F3 / F4 (2×) | −0.7475 / −2.3806 / −2.2214 | identical to 1e-4 | ±0.0000 |
| fold Sharpe F1 (2×) | −2.5355 | −2.6200 | −0.0845 |

Wall clock: **4.9 s** against **433.7 s**, an 88× speed-up. The whole residual is concentrated in
F1, the fold containing the warm-up during which symbols first become eligible; F2–F4 agree to
four decimal places. The replica is trusted for *ranking* designs and for the sign and rough
magnitude of a fold, and is not trusted to four decimals in F1.

### 7.1 Two defects in the first bench, and how they were caught

The replica being *accurate* is not the same as the replica building *the same signal the frozen
strategy builds*. `research/diff_signal.py` streams the frozen `strategy.py` through the organiser's
own `generate_targets` and diffs its emitted weights against the offline pipeline's, boundary by
boundary. Two defects fell out, both of which had silently shaped the early sweeps:

1. **Rolling windows were computed on the IS slice**, so every measure was undefined for the first
   `window` rows of the scored window and the offline book sat flat until 2020-12-22. The strategy
   is handed each eligible symbol's *entire* history up to the decision, so it trades from the very
   first boundary.
2. **Activity was masked by top-20 membership**, zeroing a coin's activity on bars where it was not
   a member. The strategy sees those bars.

Both are fixed in `research/signals.py`, and the corrected bench agrees with the frozen strategy's
own emitted weights at **206 of 207 rebalance rows to floating point**, the single exception being a
rank tie broken by symbol name rather than by array order. The pre-correction sweeps
(`sweep_grid`, `sweep_neutral`, `sweep_focus` — 186, 168 and 288 configurations) are therefore
**superseded, and no design number in §8 comes from them.** They are left in the workspace because
they are part of the record, not because they are evidence.

A separate check, `research/verify_strategy.py`, runs the frozen file end to end through
`generate_targets` and evaluates the resulting target frame in the replica; it reproduces the
nominee's vector. Neither script costs a trial — `generate_targets` calls the strategy and produces
no metric.

---

## 8. The design sweep: what was searched, and what chose the frozen design

All numbers in this section are from the **corrected** bench (`research/signals.py`), 299
configurations in total across `sweep_v2_stageA.csv` (78), `sweep_v3_A2.csv` (75),
`sweep_v3_B.csv` (63), `sweep_v3_C.csv` (51), `nominee_phase_surface.csv` (21) and
`nominee_neighbourhood.csv` (11). Every one of them is an offline number; none is a scored result.

**Stage A — cell, neutralisation and windows, at one fixed phase** (78 configs). Median 1× Sharpe
by cell, activity = trade count:

| cell | configs | median Sharpe | best |
|---|---:|---:|---:|
| desk-closed (union) | 25 | 0.465 | 0.795 |
| weekend only | 25 | 0.379 | 0.651 |
| 00:00–08:00 only | 25 | 0.151 | 0.417 |

Three quote-volume configurations were run alongside and were clearly better (median 0.707 against
0.465), which is what sent Stage A2 to quote volume.

**Stage A2 — activity quantity across the full window grid, all three cells** (75 configs, quote
volume):

| cell | configs | min | median | max | median gross edge | short sleeve positive |
|---|---:|---:|---:|---:|---:|---:|
| desk-closed (union) | 25 | +0.437 | **+0.780** | +1.088 | 66.6 bps | 3 of 25 (all non-neutralised) |
| weekend only | 25 | +0.272 | +0.592 | +1.002 | 52.0 bps | 0 of 25 |
| 00:00–08:00 only | 25 | −0.177 | +0.104 | +0.497 | 17.5 bps | 0 of 25 |

The ordering union > weekend > settlement-session is the same ordering the scored ablations found
(§10), on 25 configurations per cell rather than on one point each.

**Stage B — the full 21-point weekly phase surface**, at three weighting exponents (63 configs).
Positive at 21 of 21 phases at every exponent. At exponent 1.0: mean +0.630, min +0.342, max +0.901;
weekday phases mean +0.710 (worst fold −0.067), weekend phases mean +0.431 (worst fold −0.728). The
phase gradient runs the same way the mechanism does — rebalancing while the desks are shut is worse
— which is why the frozen phase is a weekday one.

**Stage C — cadence and holding horizon, phase swept at every cadence** (51 configs). Median across
phases, by cadence:

| cadence (bars) | median Sharpe 1× | median Sharpe 2× | median turnover | median gross edge | trades |
|---:|---:|---:|---:|---:|---:|
| 3 | 0.570 | 0.272 | 43.5 | 21.8 | 35,280 |
| 6 | 0.594 | 0.403 | 30.8 | 30.2 | 19,438 |
| 9 | 0.558 | 0.399 | 24.6 | 33.7 | 14,213 |
| 12 | 0.660 | 0.526 | 20.7 | 44.6 | 11,435 |
| **21 (weekly)** | **0.655** | **0.567** | **14.0** | **63.5** | **7,477** |
| 42 | 0.430 | 0.370 | 9.9 | 60.5 | 4,652 |
| 63 | 0.489 | 0.439 | 8.2 | 82.0 | 3,630 |

Seven holding horizons, each with its phase offset swept — the playbook's two-horizon requirement is
met seven times over. The signal is a rolling 84-day activity share; it does not move fast, and
trading it faster buys costs and nothing else. Weekly wins on the cost-adjusted metrics and on
turnover headroom, and everything faster than 12 bars fails the 40-bps gross-edge floor before any
trial is spent on it. The three-day cadence was then scored anyway, as an ablation (#119), because
an unscored horizon is not a measured horizon.

**What the frozen design is, and where each coordinate came from:**

| coordinate | value | chosen by |
|---|---:|---|
| cell | weekend ∪ 00:00–08:00 UTC | mechanism + the IC study (§3.1) + Stage A/A2 |
| activity quantity | quote volume | Stage A / A2 |
| `ACTIVITY_WINDOW_BARS` | 252 (84 days) | window grid; plateau, not peak (§11) |
| `VOLATILITY_WINDOW_BARS` | 252 | fixed *a priori* equal to the activity window |
| neutralisation | one projection, realised volatility | §4 lane purity + fold profile |
| `REBALANCE_CADENCE_BARS` | 21 (weekly) | Stage C |
| `REBALANCE_PHASE_BARS` | 4 (Tue 08:00 UTC) | mechanism: a weekday boundary in the deepest session |
| `WEIGHT_POWER` | 1.0 | flat rank weighting, the null choice |

---

## 9. The trial ledger — eight accepted trials

Journal sequence numbers are the trial numbers. Six of the eight are exempt from the multiplicity
charge under amendment A6 (five ablations, one falsification battery), so **T = 2**.

| # | seq | kind | candidate | charged | result |
|---|---|---|---|---|---|
| 112 | #112 | point | `desk-closed-share` | yes | net Sharpe 0.9145 / 2× 0.8233, maxDD 0.1015, 4 of 4 folds positive, G **56.384**; one floor fails (`role_short_gross_pnl` −0.0498) |
| 113 | #113 | ablation | `ablation-scrambled-clock` | no | G **−9.604**, 7 floors fail — see §10 |
| 114 | #114 | ablation | `ablation-raw-share` | no | G **35.763**, 1 floor fails (worst fold −0.296) — see §10 |
| 115 | #115 | neighbourhood | `desk-closed-share` | yes | **the score.** Median vector in §0; G **50.449**; 9 of 9 points positive; confidence 0.9350 |
| 116 | #116 | falsification | `desk-closed-share` | no | sign inversion fails the core floors — **passes**; placebo exceedance 0.0000 — see §12 |
| 117 | #117 | ablation | `ablation-weekend-only` | no | G **7.726**, 6 floors fail — see §10 |
| 118 | #118 | ablation | `ablation-asia-only` | no | G **−9.942**, 10 floors fail — see §10 |
| 119 | #119 | ablation | `ablation-cadence-9` | no | G **18.980**, 6 floors fail — see §10 |

Four of the twelve trials were never spent. The nominee was frozen at #112, before the
neighbourhood was declared at #115; no coordinate of `strategy.py`, `risk_policy.json` or
`neighbourhood.json` moved after #112.

**Risk policy.** `team-11-flat`: every brake disabled, no volatility target (forbidden outright
under amendment A3), no side scaling, no stops. The book is the signal and nothing else. The
organiser's own exposure caps bound at 14 of 207 rebalance boundaries, minimum scale 0.8501, median
0.9288, gross-binding only; the requested book was never itself capped.

**Roles.** Declared long and short, and `declared_roles_match_traded_sides` passed at every scored
trial. **There is no chop or flat role**: the book is dollar-neutral and fully invested at every
rebalance, standing aside only if fewer than eight eligible symbols are measurable, which never
bound after warm-up. The role checks are therefore the two sleeve PnLs — long +0.5168 (passes),
short −0.0657 (fails, §0.1) — plus the risk-unit scalar the organiser applies (median 0.6121, min
0.2849, max 1.1813).

---

## 10. The ablation programme, in one place

Five ablations, all journaled with `--kind ablation` and therefore ineligible for nomination under
amendment A6. Each holds every other parameter at the contender's value, so the difference between
its row and the contender's is attributable to the one thing that changed. All rows are single
scored points, compared against the contender's own single scored point (#112) rather than against
the neighbourhood median.

| candidate | trial | what changed | Sharpe 1× | Sharpe 2× | maxDD | worst fold | gross edge | short sleeve | G |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| **`desk-closed-share`** | #112 | — (the contender) | **0.915** | 0.823 | 0.101 | **+0.285** | **82.3** | −0.050 | **56.38** |
| `ablation-raw-share` | #114 | volatility projection removed | 1.088 | 1.008 | 0.179 | −0.296 | 109.7 | **+0.030** | 35.76 |
| `ablation-cadence-9` | #119 | weekly → three-day rebalance | 0.699 | 0.530 | 0.109 | −0.348 | 38.5 | −0.145 | 18.98 |
| `ablation-weekend-only` | #117 | cell = weekend only | 0.577 | 0.481 | 0.146 | −0.401 | 52.2 | −0.159 | 7.73 |
| `ablation-scrambled-clock` | #113 | clock destroyed, shape held | 0.357 | 0.249 | 0.243 | **−2.083** | 32.2 | −0.105 | −9.60 |
| `ablation-asia-only` | #118 | cell = settlement session only | 0.091 | 0.009 | 0.159 | −0.518 | 15.5 | −0.309 | −9.94 |

**`ablation-scrambled-clock` (#113) — the control that matters most for a seasonality lane.** The
cell is chosen by a deterministic scramble of identical shape: each day permutes its own three
settlement slots, each week nominates its own two pseudo-weekend days. Cell size, coin mix and
volatility mix are held exactly; only alignment with the real clock is destroyed. Gross edge falls
from **82.3 to 32.2 bps** per unit turnover, the worst fold falls from **+0.29 to −2.08**, maximum
drawdown more than doubles, and seven floors break. **If this book's edge were a generic
share-of-activity effect rather than a clock effect, this row would look like the contender's. It
does not.**

Two honesty notes on it. First, the scramble does not go to zero (Sharpe +0.357) and it should not
be expected to: a shape-matched scramble retains chance alignment by construction — a permuted slot
matches the true one 1 time in 3, and a random two-of-seven pseudo-weekend overlaps the true weekend
about 29% of the time — so the scramble is a *dilution* of the clock, not an orthogonalisation of
it. The measured collapse is the result, not the residual level. Second, this is **one** scrambled
draw at the book level; the distributional version of the same test is the 300-draw IC null in §5
(z = −4.5, zero draws as extreme), and it is the pair that carries the claim, not either alone.

**`ablation-weekend-only` (#117) and `ablation-asia-only` (#118) — does one half carry the book?**
No, and this is the cleanest thing in the ablation set. Neither half is a book on its own: the
weekend alone reaches Sharpe 0.58 and 52.2 bps of gross edge (and fails the fold-count floor), the
settlement session alone is *flat* — Sharpe 0.09, gross edge 15.5 bps, 10 floors broken, essentially
a non-book. The union reaches 0.915 and 82.3 bps, which is more than either half and more than a
naive sum of the two would suggest. The 25-configuration-per-cell Stage A2 table in §8 says the same
thing without spending a trial on it. So: **the weekend is the stronger half, the settlement session
alone is not tradeable at this cadence, and the mechanism only becomes a book when both cells are
taken as one partition.** That is consistent with the §3.1 claim that the two cells are one
mechanism, and it is the reason the frozen strategy defines a single `_is_desk_closed` predicate
rather than two signals.

It is also where the short sleeve is at its worst: the settlement-session-only book's short sleeve
loses −0.309 gross, six times the contender's. Narrowing the cell makes the short side much worse,
not better.

**`ablation-raw-share` (#114) — controls off.** Discussed in §0.1. The one row in the whole
programme that beats the contender on raw Sharpe, and the one row with a positive short sleeve. It
pays for both with a fourth fold of −0.296, a drawdown of 0.179 against 0.101, and a lower G. The
choice to neutralise is the single largest judgement call in this certificate and it is the one a
reader is most entitled to disagree with.

**`ablation-cadence-9` (#119) — a second holding horizon, scored.** The mechanism survives being
traded 2.3× as often — the book is still directionally right, Sharpe 0.699, four folds with three
positive — but turnover rises to 25.5 (over the ≤25 floor) and gross edge falls to 38.5 (under the
≥40 floor). The horizon is genuinely weekly-or-slower, exactly as an 84-day activity share should
be, and this is measured rather than asserted.

**What the set establishes, and what it does not.** Together: the clock is doing the work (#113);
neither calendar half carries the book alone (#117, #118); the neutralisation costs raw Sharpe and
buys fold stability and lane purity (#114); the horizon is weekly (#119). What the set does *not*
establish is that this book beats a volatility book, or that the desk-closed characteristic survives
a joint control against all four factors at the book level — the first is contradicted at the IC
level in §4, and the second was measured only at the IC level and never scored (§14).

---

## 11. The declared neighbourhood, the phase surface, and how much of this is fitted

**The declaration** (`candidates/desk-closed-share/neighbourhood.json`) varies four coordinates,
each of which visibly moves the executed book, as amendment A1 requires: no two points share a
metric vector, and the offline pre-check confirmed zero inert points before the trial was spent.

Trial #115, nine points, four workers, 2,212 s:

| point | `ACTIVITY` | `VOLATILITY` | `PHASE` | `POWER` | net Sharpe | 2× Sharpe | ann. return | maxDD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **nominee** | 252 | 252 | 4 | 1.0 | 0.9145 | 0.8233 | 0.1057 | 0.1015 |
| 1 | 189 | 252 | 4 | 1.0 | 0.8453 | 0.7439 | 0.0962 | 0.1108 |
| 2 | 315 | 252 | 4 | 1.0 | 0.7797 | 0.6907 | 0.0882 | 0.1065 |
| 3 | 252 | 189 | 4 | 1.0 | 0.9045 | 0.8104 | 0.1045 | 0.1010 |
| 4 | 252 | 315 | 4 | 1.0 | 0.8207 | 0.7292 | 0.0934 | 0.0991 |
| 5 | 252 | 252 | 2 | 1.0 | 0.9742 | 0.8829 | 0.1152 | 0.0977 |
| 6 | 252 | 252 | 7 | 1.0 | 0.8302 | 0.7414 | 0.0960 | 0.0925 |
| 7 | 252 | 252 | 4 | 0.7 | 0.8597 | 0.7697 | 0.0980 | 0.0978 |
| 8 | 252 | 252 | 4 | 1.4 | 0.9130 | 0.8204 | 0.1061 | 0.1066 |

Nine of nine have positive 1× return *and* positive 2× Sharpe. The score is the per-metric median,
which is 0.8597 on net Sharpe — 94% of the nominated point's 0.9145. **The gap between the point I
picked and the median I am scored on is 0.055 of Sharpe.** That is the number that says whether a
nominee is the top of a spike, and it is small.

**The phase surface** is the load-bearing one for this lane, and it was swept exhaustively at the
nominee's own windows before the neighbourhood was declared (`research/nominee_check.py`, offline):

```
phase   0    1    2    3    4    5    6    7    8    9   10   11   12   13   14   15   16   17   18   19   20
1x Sh +.80 +.88 +.97 +.95 +.91 +.95 +.89 +.83 +.94 +.84 +.76 +.60 +.57 +.53 +.74 +.62 +.58 +.52 +.54 +.69 +.63
```

Mean +0.749, sd 0.160, min +0.525, max +0.971, **positive at 21 of 21**. Weekday phases mean +0.811
with a worst fold of +0.114; weekend phases mean +0.596 with a worst fold of −0.369. There is a real
gradient and it runs the way the mechanism says it should.

**A correction to the frozen file's own docstring.** `REBALANCE_PHASE_BARS`'s docstring says phase 4
"sits at [the surface's] median, not at its maximum". On the final measured surface that is not
exact: the surface median is +0.761 and phase 4 is +0.915, which is **5th best of 21** — in the
upper tercile, not at the median. The substantive claim the docstring was making still holds — the
phase was chosen by the mechanism, it is not the maximum (phase 2 is), and four other phases beat it
— but the word "median" is wrong and the file is frozen, so the correction lives here.

**Plateau or spike?** Neither extreme; a broad hill with a real gradient. Every one of the 21 phases,
every one of the nine declared points, and every one of the 25 desk-closed Stage A2 configurations is
positive. But the far corner of the declared box, measured offline at
`ACTIVITY=315, VOLATILITY=315, PHASE=7, POWER=1.4`, drops to 0.415 — less than half the nominee. The
honest description is: **no sign change anywhere in the explored region, a factor-of-two degradation
at the corners, and a nominee that sits on the shoulder rather than on the summit.**

---

## 12. The falsification battery

Trial #116, on the frozen nominee, 2,708 s.

**Exact sign inversion** — every weight negated, nothing else touched:

| metric | inverted | clears core floor? |
|---|---:|---|
| net Sharpe | −1.1332 | no |
| double-cost Sharpe | −1.2230 | no |
| triple-cost Sharpe | −1.3125 | no |
| annualised return | −0.1311 | no |
| double-cost annualised return | −0.1404 | no |
| maximum drawdown | 0.4803 | no |
| annualised volatility | 0.1179 | yes (a floor an inversion cannot fail) |
| trade count | 6,991 | yes (a floor an inversion cannot fail) |

**The inversion does not clear the core floors, so the falsifier is satisfied.** The two it does
clear are the two that are indifferent to sign. This matters more for a calendar book than for most:
if "short the coins that trade while the desks are shut" and "long the coins that trade while the
desks are shut" had both worked, the apparent edge would have been a construction artifact of
rank-weighting, not a mechanism.

**Gross-edge placebo** — the same weight vector, randomly re-attributed across eligible symbols,
8 draws (seeds 12–19):

| | bps per unit one-way turnover |
|---|---:|
| candidate | **82.31** |
| placebo min / median / max | −9.52 / 3.09 / 24.42 |
| exceedance | **0.0000** (0 of 8 placebos reach the candidate) |

The candidate's gross edge is 3.4× the best of eight placebo books and roughly 27× their median. The
organiser has disclosed (journal, limitation L1) that the placebo half of this battery is weak for
*directional* books; this book is cross-sectional and dollar-neutral, which is the case the placebo
is informative for — a random re-attribution of a dollar-neutral weight vector destroys the symbol
selection and keeps everything else. Exceedance is reported, never gated.

---

## 13. The mandate's warning, answered directly

The mandate says seasonality is the easiest place in this tournament to fit noise, and that the
phase-offset sweep and the declared neighbourhood are load-bearing for me in a way they are not for
anyone else. The answer has three parts.

**How many independent seasonal effects am I claiming? One.** A single binary partition of the 8h
grid — desk-closed (weekend ∪ 00:00–08:00 UTC) against desk-open — with a single sign fixed a priori
by the mechanism (short the high desk-closed share). Not a day-of-week effect: §2 records the
aggregate weekday table as dead. Not an interaction effect: nothing here rests on a
day-of-week × slot cell. Not two effects: the two sub-cells are claimed as one mechanism, and §3.1
and the scored ablations #117/#118 are the evidence offered for that, not an assumption.

The degrees of freedom actually spent on the calendar are three, and they are not equally defensible:

1. **Which of the three intraday slots is the desk-closed one.** A 1-in-3 in-sample choice. The
   scrambled-clock null *cannot* resolve it (§5, p = 0.33 on the crude global relabelling). This rests
   on the mechanism — 00:00–08:00 UTC is the thinnest global liquidity window at 27.4% of quote
   volume — plus one in-sample pick. It is the weakest link in the identification and it is stated as
   such.
2. **Whether the weekend belongs in the cell.** This one *is* resolved: the null ranges over all 21
   two-day cells and the true weekend beats it at z = −5.78.
3. **Union versus either half.** Decided by scored ablations that cost two trials (#117, #118), not
   by an offline choice.

Everything else — the 84-day window, the activity quantity, the weighting exponent — was checked for
*insensitivity* rather than tuned: the desk-closed IC is negative and second-half-stable at every
window in {63, 126, 252, 378} and for all three activity quantities (quote volume, trade count,
absolute return), 12 of 12 combinations, t between −4.4 and −6.1.

**How many effective observations support it?** Fewer than the raw counts suggest, and the raw
counts are not used anywhere in this document:

| unit | count | is it independent? |
|---|---:|---|
| symbol-boundaries | 86,658 | **no** — 20 perps at one instant are ~1 draw (§1) |
| executed trades | 7,092 | **no** — 20-odd legs per rebalance |
| decision boundaries in the intraday cell | 1,445 | yes, for the calendar statistics |
| decision boundaries in the weekend cell | 1,238 | yes, for the calendar statistics |
| weekly rebalances (one-week PnL draws) | **207** | yes, for the book's returns |
| non-overlapping 84-day formation windows | **≈ 17** | this is the honest count for the *characteristic* |

The last row is the one that should govern belief. `ACTIVITY_WINDOW_BARS = 252` is 84 days, so two
consecutive weekly rebalances share eleven twelfths of their measurement window; the four-year IS
period contains only about 17 non-overlapping formation windows. **A Sharpe of 0.86 rests on 207
weekly PnL draws generated by a characteristic that renews itself roughly 17 times.** Four
independent folds, all positive, and 11 positive quarters of 17 are the coarsest and most honest
summary of that.

**What did the neighbourhood show about plateau versus spike?** §11 in one line: 9 of 9 declared
points positive, 21 of 21 phases positive, the scored median at 94% of the nominated point, and a
factor-of-two degradation at the far corner of the declared box. That is a shoulder on a broad hill.
It is not a plateau — the corners are materially worse — and it is not a spike, because there is no
sign change anywhere in the region and the median-versus-point gap is 0.055 of Sharpe.

---

## 14. Failures, abandoned attempts, and what this certificate does not establish

Nothing in this section cost a trial except where a sequence number is given; the rest was killed
offline, which is where it should have been killed.

1. **The aggregate calendar** — "some slot or weekday drifts". Measured (§2), dead. Ten cells, best
   t = +1.56, 21 interaction cells that change sign between halves. Abandoned before any trial.
2. **The open-return formation artifact** — a lag-1 cross-sectional reversal at 00:00 UTC of IC
   −0.0708 (t = −9.36) that was bid–ask bounce sharing `open[t]` with the forward return (§3).
   Abandoned, and the rule "formations from closed-bar closes only" adopted for everything after it.
3. **The US-minus-Asia contrast** — genuinely significant against the scrambled null (z = +2.81) and
   out-of-cell (t = +3.40 / +0.92), but its first-half IC is +0.0036 (not significant) and it flipped
   sign at W = 126 in raw form. **Not used in the candidate.** It is the most interesting thing this
   lane leaves on the table.
4. **The settlement-versus-arbitrary-boundary test** — the mandate's own headline question, found
   **unidentifiable** on this snapshot (100.0000% of eligible symbol-boundaries carry a settlement,
   §5). Abandoned as unaskable, and reported as a finding rather than a failure.
5. **The mid-bar settlement contrast** — 653 observations, more violent bars (mean |return| 268.6 bp
   against 209.0 bp), too few and too concentrated to build on. Disclosed, not used.
6. **Two bench defects** (§7.1): rolling windows computed on the IS slice, and activity masked by
   membership. Both invalidated 642 configurations of pre-correction sweeping. Caught by diffing the
   frozen strategy's own emitted weights, before any trial was spent on the affected design.
7. **Trade count as the activity quantity** — better at the IC level, worse at the book level;
   dropped in favour of quote volume at Stage A (§8).
8. **Faster cadences** — 3, 6 and 9 bars all fail the gross-edge floor offline; cadence 9 was scored
   anyway (#119) and failed it for real, along with the turnover floor.
9. **`ablation-asia-only` (#118)** — the settlement session alone, the cell closest to the mandate's
   literal wording, scored and found to be **not a book** (Sharpe 0.091, ten floors broken).
10. **The candidate's own short sleeve** (#112, #115) — the one measured floor this submission
    fails. §0.1.

**What this certificate does not establish, stated plainly:**

- It does not establish that the desk-closed characteristic beats realised volatility. §4 measures
  the opposite: volatility residualised on the calendar measure is about twice as strong as the
  calendar measure residualised on volatility.
- It does not establish that the characteristic survives a **joint** control against volatility,
  size, momentum and funding crowding *at the book level*. The four-way combined control was measured
  only at the IC level (−0.0073, t = −1.77 at W = 378; −0.0077, t = −1.97 at W = 252) and **was never
  scored under a trial**, though four trials remained unspent. That is the largest gap in this
  programme, and the one I would close first. At the IC level the honest reading of §4 is that
  roughly 70% of the raw content is shared with other factors.
- It does not establish which of the three intraday slots is the negative one; that identification is
  a 1-in-3 in-sample choice supported by mechanism (§13).
- It does not establish the short sleeve as a standalone source of return; it measures the opposite
  (§0.1).
- It establishes nothing whatsoever about the holdout, which was never opened.

---

## 15. Provenance: a host restart, and five re-runs at no charge

Partway through this programme the machine restarted while five evaluations were executing. All five
were killed with only the `running under accepted trial` header written to their logs:

| trial | candidate | kind |
|---|---|---|
| #115 | `desk-closed-share` | neighbourhood sweep — **the scored trial** |
| #116 | `desk-closed-share` | falsification battery |
| #117 | `ablation-weekend-only` | ablation |
| #118 | `ablation-asia-only` | ablation |
| #119 | `ablation-cadence-9` | ablation |

All five were re-run organiser-side under the **same already-accepted trials**: `cup20_evaluate.py`
resolves an accepted trial rather than creating one, so nothing was charged and no trial was burned.
This is the behaviour the organiser recorded in the playbook update at journal sequence #67 ("a
killed evaluation does not burn its trial"), reported independently by two earlier teams. The trial
count stands at **8 of 12 accepted, T = 2**, exactly as it would have without the restart. The
nominee's source bytes, the risk policy, the declared neighbourhood and the journal were untouched by
the incident; the accepted-trial records at sequences #115–#119 predate it and are unchanged.

Every packet and log in `research/packets/` is the organiser's own output. The numbers in this
certificate that carry the word "scored" come from those eight packets and from nowhere else.

---

## 16. Nomination

**Nominated: `desk-closed-share`.** Frozen at trial #112, unchanged since, scored at trial #115 with
**G = 50.449**, one measured floor failed (`role_short_gross_pnl` = −0.065736), falsifier satisfied
at #116.

I consider the nomination sound, with the reservation stated in §0.1 rather than around it. The case
for it is that the mechanism is identified rather than fitted: a shape-matched scrambled clock
destroys it at the book level (#113) and at the IC level over 300 draws (z = −4.5), neither calendar
half survives on its own (#117, #118), the characteristic transfers out of cell in both directions of
a week-parity split, the sign inversion fails, the placebo exceedance is zero, all four folds and 9
of 9 neighbourhood points are positive, and the whole thing runs at 14× annual turnover with cost
taking 0.8% of gross — it is not a book that needs the cost model to be kind to it.

The case against it is one sentence long and it is a real sentence: **a long/short book whose short
sleeve lost money gross for four straight years is a book with one working sleeve, and the four
trials I did not spend should have gone to the joint four-factor control that would have told me how
much of the working sleeve is the clock's.**
