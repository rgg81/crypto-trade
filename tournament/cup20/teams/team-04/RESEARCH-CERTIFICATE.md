# Team 04 — Research Certificate

Lane: `market-residual-cross-sectional-momentum`
Candidate carried to the sweep: `candidates/resid-composite`
Journal sequences cited throughout: **#30, #31, #32, #33, #34, #35, #36, #37** (8 accepted trials,
4 unspent)

## VERDICT: NO NOMINATION

The declared neighbourhood sweep (**#36**) is this team's score. On the per-metric median across
its seven points, the candidate **passes twenty-one of the twenty-two measurable hard floors** —
net Sharpe 0.999 at 1× and 0.871 at 2×, maximum drawdown 0.124, all four folds positive at 2× with
a worst fold of **+0.195**, turnover 21.9×, gross edge 67.6 bps per unit turnover, both role
sleeves gross-positive, and 7 of 7 neighbourhood points positive.

It fails **trial-adjusted confidence: 0.8390 against a floor of 0.90**, with a per-point median
bootstrap fraction `B = 0.9770`. That floor is `1 − T·(1−B)` and the minimum trial count for any
nomination is `T = 8`, so a nomination requires `B ≥ 0.9875`. On a 1445-day window,
`B = Φ(Sharpe · √3.958)`, which makes the confidence floor **equivalent to a neighbourhood-median
in-sample Sharpe of about 1.13**. The measured plateau median is 0.999. The gap is not a
near-miss that a better parameterisation closes; it is about 13% of Sharpe standing between the
best plateau this lane produced and the multiplicity-adjusted bar, and no configuration in a
design space of ten formation lengths, twelve cadences, every phase offset of each, four sleeve
geometries, four market-factor definitions and six weighting schemes reached it as a **median**
rather than at a point.

The falsification battery (**#37**) was run anyway and **passes cleanly**: the exact sign inversion
fails six of the eight core floors, and not one of the eight gross-edge placebos reached a third of
the candidate's 77.8 bps per unit turnover. The mechanism is real. It is simply not, on four years
of daily data, distinguishable enough from zero to survive an eight-fold multiplicity penalty.

Four trials are left unspent. This is not a budget-exhaustion conclusion — it is a floor the lane
cannot clear, computed from the organiser's own numbers.

---

## 1. The mechanism, and why it should work

Roughly two thirds of an individual top-20 perpetual's 8h return variance is one common factor.
Measured on the in-sample rows, regressing each symbol's 8h log returns on the equal-weight
cross-section of the members gives a **median R² of 0.679** across the 45 symbols with enough
history, ranging 0.44 to 0.81. The loadings on that factor are strongly dispersed:

| | β vs the equal-weight cross-section |
|---|---:|
| BTCUSDT | 0.597 |
| BNBUSDT | 0.780 |
| ETHUSDT | 0.817 |
| median of 45 | 1.07 |
| GALAUSDT | 1.301 |
| WLDUSDT | 1.453 |
| 1000PEPEUSDT | 1.640 |

Both halves matter. If the factor explained little, there would be nothing to remove. If every
name loaded on it identically, removing it would be cross-sectional demeaning under another name —
and the evaluator demeans anyway, because a dollar-neutral book is a demeaned book. It is the
**dispersion** that makes a raw ranking a beta ranking: the residual score differs from the raw
score by `β_i × (market's own formation-window return)`, so the contamination is exactly
proportional to how much the market moved while the signal was forming. In a window where the
index rose, the top of a raw ranking is populated by whatever loaded hardest.

The reason residual dispersion should persist at a two-to-three-week horizon on a 24/7 tape is
crowding rotation: leverage and funding make a coin's own move reflexive, positioning builds and
unwinds over days rather than minutes, and the reconstitution-stable top twenty is exactly the set
where that positioning is large enough to matter and liquid enough to be trade-able. What the
mechanism does **not** predict is a short-horizon effect, and that prediction is testable — see §3.

**Falsifier stated in advance:** if the residual book and the raw book perform alike, the lane is
a beta ranking with extra steps. §4 reports what happened, including the part that does not
support the thesis.

---

## 2. Causality — how the market component is estimated

This is the failure mode the lane is most exposed to, so it is worth being explicit. At a decision
at time *t*:

1. `context.bars[symbol]` holds rows whose **close time is at or before *t***; the most recent is
   the bar closing exactly at *t*. The fill happens at the open of the bar that starts at *t*, and
   that price is never exposed.
2. The **market factor at a past bar *s*** is the equal-weight mean log return, at bar *s*, of the
   symbols the organiser named eligible **at *t***. Membership at *t* is information available at
   *t*; no later reconstitution is consulted and no symbol enters the factor that was not a member
   at this boundary.
3. **β is an OLS slope with an intercept, fitted on the trailing `BETA_WINDOW = 270` bars ending at
   *t*** (90 days). No row at or after the decision enters the fit.
4. The formation sum ends `SKIP_BARS = 1` bar before the decision, so the bar whose close sits
   closest to the unobserved execution open does not enter the score at all.
5. **The strategy holds no state between calls.** Every emitted weight is a pure function of that
   decision's own context. This is deliberate: a stateful accumulator would make the causality
   claim something a reader has to trust, whereas a stateless function makes it something a reader
   can check by inspection.

Two design choices inside the residualisation are worth stating because both could have been made
wrongly:

- **The estimation window is longer than the formation window** (270 bars against 42/63/126). This
  is not decoration. Ordinary least squares with an intercept forces the residuals to sum to zero
  *over the estimation window*; if the formation window were the estimation window, the signal
  would be identically zero for every name. A formation window strictly inside a longer estimation
  window is the standard construction and the only one that produces a signal at all.
- **The intercept is estimated but not subtracted.** The market component is `β_i × m_s`; the
  intercept is the coin's own drift, which is the thing a momentum lane exists to rank. Subtracting
  it converts the score into a short-horizon-versus-long-horizon contrast. Measured: the
  alpha-subtracting variant turns the rank IC from **+0.028 to −0.033** at formation 63 / forward
  42 bars, i.e. it flips the sign of the edge. Fitting the intercept but not subtracting it is what
  keeps β unbiased without destroying the signal.

---

## 3. Formation horizons — at least three, and the horizon where the lane does not work

Rank IC of the cross-sectional score against forward open-to-open returns, measured on the
in-sample rows with the alignment of §2 (`research/eda_02_ic.py`). Every number is a mean
cross-sectional Spearman correlation with its t-statistic.

| formation (bars) | forward 9 bars | forward 21 bars | forward 42 bars |
|---:|---:|---:|---:|
| 6 | −0.019 (t −2.4) | −0.011 (t −1.4) | +0.008 (t 1.1) |
| 12 | −0.027 (t −3.3) | −0.021 (t −2.7) | +0.005 (t 0.7) |
| 21 | −0.035 (t −4.3) | −0.022 (t −2.8) | +0.010 (t 1.3) |
| 42 | −0.022 (t −2.7) | −0.006 (t −0.8) | **+0.023 (t 3.0)** |
| 63 | −0.002 (t −0.2) | +0.014 (t 1.7) | **+0.028 (t 3.6)** |
| 90 | −0.005 (t −0.6) | −0.005 (t −0.6) | +0.008 (t 1.0) |

The mechanism's own prediction survives its test: **there is no short-horizon residual momentum in
this universe — the sign is reversal out to about three weeks of formation**, and momentum only
appears when both the formation and the holding horizon reach two to six weeks. Formation 90 is
already past it. Everything downstream uses formation windows in the 42–126 bar band, and the
nominee averages three of them.

Portfolio-level formation horizons run offline with full phase sweeps: 21, 42, 63, 84, 90, 126 and
180 bars. Measured on the harness: 63 bars single-horizon (#30, #31, #32) and the 42/63/126
composite (#33, #34, #35, #36).

---

## 4. The ablation the mandate exists for: raw against residual

**#30** and **#31** are the same book, the same cadence, the same phase, the same sleeve widths and
the same risk policy. One constant differs — `MARKET_REMOVAL`, 1.0 against 0.0 — so #31 ranks the
raw trailing return and #30 ranks it with `β_i × m` removed.

| | #30 residual | #31 raw |
|---|---:|---:|
| net Sharpe 1× | 0.822 | **0.943** |
| annualised return 1× | 0.1023 | 0.1167 |
| max drawdown 1× | 0.1390 | 0.1334 |
| turnover 1× | 24.891 | 23.369 |
| gross edge bps / turnover | 49.49 | 57.84 |
| worst fold 2× | −1.072 | −1.148 |
| long / short gross PnL | +0.533 / **−0.045** | +0.657 / **−0.121** |
| bootstrap B | 0.9485 | 0.9660 |

**At the one phase where both were measured on the harness, the raw book was better on Sharpe.**
That is the single most important sentence in this certificate and it does not support the lane's
premise, so it is stated first and without softening.

It is also, on the evidence, a phase artifact rather than a finding. The phase dispersion of this
shape's Sharpe is **±0.22 to ±0.36** across the 21 offsets of a cadence-21 book, so a 0.12 gap at
one offset is inside the noise. Averaged over **all** offsets in a simulator calibrated against
#30 (§7), the ordering reverses and widens:

| phase-mean over all 21 offsets | residual | raw |
|---|---:|---:|
| Sharpe | **+1.08** ± 0.22 | +0.90 ± 0.26 |
| worst phase Sharpe | +0.71 | +0.43 |
| worst fold (phase mean) | **−0.12** | −0.35 |
| gross edge bps / turnover | 69 | 57 |
| short gross PnL | −0.123 | −0.154 |

The control matrix (`research/eda_14_controls_regimes.py`, all eight on/off combinations of
residualisation, the skip, and the narrowed short sleeve, each a phase mean over 21 offsets) says
the same thing and localises it:

| residualise | skip | narrow short | Sharpe | up | chop | down |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0.89 | 0.68 | **0.10** | 0.69 |
| 0 | 1 | 0 | 0.90 | 0.66 | **0.13** | 0.72 |
| 0 | 1 | 1 | 0.79 | 0.53 | **0.22** | 0.61 |
| 1 | 0 | 0 | 1.06 | 0.59 | **0.55** | 0.84 |
| 1 | 1 | 0 | 1.04 | 0.52 | **0.58** | 0.87 |
| 1 | 1 | 1 | 1.08 | 0.56 | **0.70** | 0.82 |

Residualisation adds +0.17 to +0.31 Sharpe in every one of the four pairings, and **almost all of
it arrives in chop** — the regime where the index's trailing 63-bar move is inside ±5%, 21% of the
window. That is the mechanism doing exactly what it claims: when the factor is quiet a raw ranking
is mostly noise, and when the factor is moving a raw ranking is mostly β. The skip is **inert**
(±0.02 in every pairing) and is retained only as a causality margin, not because it pays.

**Honest summary of the ablation:** the residualisation earns its place on phase-averaged evidence,
on the regime decomposition, on the short sleeve and on the worst fold — but the one head-to-head
comparison run on the organiser's own pipeline went the other way, and one measured point beats a
simulator. A reader should treat the residual-versus-raw margin as *supported but not established*.

---

## 5. The floor that nearly ended this lane: `short_gross_pnl > 0`

Over the in-sample window the equal-weight top-20 basket returned a **summed simple return of
+2.47 on price and +1.96 after the funding a long pays**. A dollar-neutral cross-sectional book has
to short something inside that. The floor does not ask whether the shorted names *underperformed*;
it asks whether they *fell*.

Measured across every formation length (21–90), every cadence (9–42) and both sleeve widths
(a third and a seventh of the cross-section), a diversified short sleeve's cumulative simple return
was negative in **every one of the 48 configurations scanned** (`research/eda_08_shortscan.py`).
The best was −0.22; the mandate's own shape, a short third, was −0.89. Funding is a genuine and
very stable tailwind — **+0.48 to +0.51 cumulative** on a full-notional short, about 12%/yr — and it
is nowhere near enough. The residual short third *did* underperform the index by about 1.07
cumulative, a real 27%/yr spread; the index simply rose more than that.

The damage is concentrated: split by fold, the short third earned **−1.21 / +0.60 / +0.01 / −0.29**.
It is one regime, the 2020–21 melt-up, and it is not one name — the largest per-name contributions
are ZEC, XLM, BCH, EOS, NEO, LTC, spread over hundreds of holding periods each.

Three routes out were tried and reported here whether or not they worked:

- **Narrow the sleeve.** Cross-sectional and in lane. The short sleeve's PnL rises monotonically as
  the sleeve narrows: −0.21 at a third, −0.09 at a quarter, −0.04 at a fifth, −0.01 at a seventh.
  This is the route taken, at a fifth against a long third. It is *not* costless and it is not a
  trick: a narrower short sleeve is a more concentrated book, and the concentration is visible in
  the packet's `exposure_caps` block (it did not bind — minimum scale 1.0000 at both stages for
  #33).
- **Conviction weighting** by cross-sectional z-score instead of equal weight inside the sleeve.
  Rejected: short PnL barely moved (−0.026) and the worst fold degraded from −0.26 to −0.54.
- **Veto shorts whose own trailing return is positive** — never short something that is rising.
  Measured and **rejected on two grounds**. It is a per-coin trend gate, which is another team's
  mechanism, and it fails anyway: short PnL stayed negative at 0 of 21 phases and the drawdown blew
  out to 0.201–0.210, through the 0.20 floor, because vetoing shorts in the bull turns the book
  long-heavy in the fold that dominates the sample. Reporting it here rather than adopting it.

The one shape that made the short sleeve reliably positive in the simulator was a **one- or
two-name** sleeve, and it was rejected: at that width the sign of a disqualifying floor rests on a
handful of collapses, the per-symbol cap binds, and the five-largest-day concentration floor comes
into play. A floor whose sign flips with the rebalance offset is not passed, it is won.

---

## 6. Rebalance horizon and phase

Cadences run offline with a **full phase sweep at every one** (all K offsets, never one): 1, 3, 6,
9, 15, 21, 24, 27, 30, 42, 63, 84 bars. Phase-mean Sharpe of the residual thirds book at formation
63:

| cadence (bars) | 1 | 3 | 6 | 9 | 15 | 21 | 30 | 42 | 63 | 84 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Sharpe (phase mean) | 0.56 | 0.79 | 0.92 | 0.99 | 1.10 | **1.12** | 1.09 | 0.92 | 0.41 | 0.36 |
| turnover, harness-adjusted | 127 | 72 | 50 | 40 | 30 | 25 | 21 | 17 | 14 | 11 |

Cadence 1 is disqualified by turnover alone at 127× against a 25× floor — retargeting every
boundary pays drift correction on the whole book three times a day. Cadences past 42 lose the
signal. The band 21–30 is where the two constraints meet, and the nominee sits at 21.

**Phase is a first-order axis and is treated as one.** Every offline table in this certificate is a
phase mean, never a best phase — an early version of this research read a Sharpe of 1.23 off a
single offset whose phase mean was 0.79, which is exactly the trap. On the harness, phase 10 and
phase 16 of the nominated shape were both measured (**#33, #35**): Sharpe 1.138 against 1.202,
B 0.9865 against 0.9945, short PnL +0.093 against +0.055, worst fold +0.195 against +0.385. The
declared neighbourhood carries phase 4 and phase 16 as explicit points for the same reason.

---

## 7. The offline simulator, and the two things it got wrong

Every offline table above comes from `research/` and none of it is a score. The simulator exists
so that trials are spent on questions rather than guesses, and **#30 was spent calibrating it**.
Two corrections came out of that, and both are disclosed because both changed conclusions:

1. **Metrics must be computed on daily returns × √365, not 8h bars × √1095.** Before the fix the
   simulator put fold 3 at −0.03 where the harness put it at −1.07 (2× cost); fold 1 and fold 4 were
   almost unaffected. Under the wrong aggregation the fold profile of the whole design space looked
   survivable when it was not.
2. **Residual error of ±0.2 Sharpe on some shapes.** After the fix the simulator reproduced #30 to
   0.01 Sharpe (0.810 against 0.822) but under-read #32 by 0.23 (0.61 against 0.84), and it
   under-states one-way turnover by roughly 19%. Its bootstrap fraction was within ±0.005 of the
   harness at the two points of the nominated shape where both exist.

Nothing in this certificate rests on the simulator alone where a floor is concerned. Where the two
disagree, the harness wins and is quoted.

---

## 8. Role check: long, short, chop

Roles are declared `long, short` at every trial and the harness confirmed
`declared ['long','short'], traded ['long','short']` on all of them. Both sleeves are material at
every trial, so both role floors apply, and both are reported.

| | long gross PnL | short gross PnL |
|---|---:|---:|
| #30 residual thirds | +0.533 | **−0.045 FAIL** |
| #31 raw thirds | +0.657 | **−0.121 FAIL** |
| #32 residual, short fifth | +0.488 | +0.017 |
| #33 nominee | +0.571 | +0.093 |
| #35 nominee at phase 16 | +0.616 | +0.055 |

Regime split of the nominated construction (index trailing 63-bar move above +5% / inside ±5% /
below −5%, occupancy 0.38 / 0.21 / 0.41): Sharpe **0.56 / 0.70 / 0.82**. The book is not a
disguised directional bet in either direction — its *best* regime is the down regime and its
*weakest* is the up regime, which is the opposite shape to the raw book it is built against
(0.53 / 0.22 / 0.61) and the opposite shape to a beta ranking.

---

## 9. Every failure and every abandoned attempt

| what | verdict | evidence |
|---|---|---|
| **#30** residual thirds, the transparent baseline | **FAILED 2 floors**: worst fold 2× = −1.072 (needs ≥ −0.25), short gross PnL = −0.045 | journal #30 |
| **#31** raw thirds, the mandate ablation | **FAILED 3 floors**: worst fold −1.148, short gross PnL −0.121, confidence 0.898 | journal #31 |
| **#32** residual, cadence 24, short fifth | **FAILED 1 floor**: confidence 0.8515 (B = 0.9505) | journal #32 |
| **#34** short sleeve at 0.18 instead of 0.20 | **INERT — the metric vector came back byte-identical to #33.** `round(n × f)` on a 20-name cross-section maps 0.18 and 0.20 to the same integer. A real result about the parameterisation, obtained at the cost of a trial, and it is why `SHORT_SLEEVE_FRACTION` is **not** a declared coordinate: a ±10% declaration would have been a coordinate that cannot move the book, and the neighbourhood would have been a costume | journal #34 |
| alpha subtraction (residual minus fitted intercept) | rejected — flips the IC sign, −0.033 against +0.028 | `eda_02`, `eda_03` |
| residual-volatility standardisation (Blitz t-statistic form) | rejected — Sharpe 0.79 against 1.23 at the matched point, worst fold −1.22 | `eda_03` |
| beta-neutral sleeve scaling (Σ w β = 0) | rejected — Sharpe −0.12, drawdown roughly unchanged; the ranking is already β-free | `eda_03` |
| quartile sleeves instead of thirds | rejected — Sharpe 1.00 against 1.23 | `eda_03` |
| conviction (z-score) sleeve weighting | rejected — worst fold −0.54 against −0.26 | `eda_11` |
| inverse-volatility sleeve weighting | rejected — Sharpe −0.08, turnover +11% | `eda_15` |
| BTC as the market factor instead of the cross-section | rejected — Sharpe 1.05 against 1.08, B 0.978 against 0.985 | `eda_15` |
| cross-sectional median as the market factor | rejected — worst fold −0.21 against +0.05 | `eda_15` |
| short-side absolute-trend veto | rejected twice over — lane drift (a per-coin trend gate) **and** drawdown 0.201–0.210 through the floor | `eda_11` |
| one- and two-name short sleeves | rejected — the only shapes with a reliably positive short sleeve, and their positivity is a handful of collapses | `eda_07`, `eda_10` |
| cadence 1 with a no-trade band | rejected — turnover 127× against a 25× floor | `eda_05` |
| formation 90 and above | rejected — IC collapses to +0.008 at the horizon that pays | `eda_02`, `eda_12` |

Two further disclosures that cost nothing to make and would be dishonest to omit:

- **The nominee sits on a narrow ridge in the formation axis.** The bootstrap fraction along
  `FORMATION_BARS` in the simulator reads 0.972 / 0.977 / 0.989 / **0.990** / 0.969 / 0.984 / 0.987
  at 54 / 57 / 59 / 63 / 67 / 69 / 72. That is noise, not a plateau, and it is precisely what
  neighbourhood-median scoring exists to expose. The declared neighbourhood does not hide it.
- **A tighter neighbourhood would have scored better and was not declared.** A 7-point
  neighbourhood using `SHORT_SLEEVE_FRACTION` at ±10% had a simulated median B of 0.9895 against
  0.9835 for the declared one — because, per #34, that coordinate cannot move the book at ±10%.
  Choosing it would have been legal under every §6 rule and would have been a costume.

---

## 10. The declared neighbourhood

**The nominee was fixed before the neighbourhood was declared.** It is the state journaled at
**#33**, unchanged: `BETA_WINDOW = 270`, `FORMATION_BARS = 63`, `SKIP_BARS = 1`,
`REBALANCE_BARS = 21`, `REBALANCE_PHASE = 10`, `SLEEVE_FRACTION = 0.34`,
`SHORT_SLEEVE_FRACTION = 0.20`. Nothing moved after #36 was journaled.

Declaration rule, chosen before the sweep ran: **each coordinate varied by approximately ±10% of
the nominee's value, rounded to the nearest admissible integer — except the rebalance phase, varied
by ±6 offsets, because ±10% of phase 10 is one offset and one offset is not an exploration of the
phase axis.**

| coordinate | nominee | below | above |
|---|---:|---:|---:|
| `FORMATION_BARS` | 63 | 57 (−9.5%) | 69 (+9.5%) |
| `REBALANCE_BARS` | 21 | 19 (−9.5%) | 23 (+9.5%) |
| `REBALANCE_PHASE` | 10 | 4 (−6 offsets) | 16 (+6 offsets) |

Seven points including the nominee, k = 3, `max(7, 2k+1) = 7`. All distinct, all finite, every
coordinate a module-level plain numeric literal named identically to the coordinate. The three
formation windows the score averages (42 / 63 / 126) are derived **at import from
`FORMATION_BARS`**, so a neighbourhood point moves all three together rather than leaving two
frozen at the nominee's value.

### 10.1 The sweep — **#36**, 7 points, 1080 s, and the score

| point | `FORMATION_BARS` | `REBALANCE_BARS` | `REBALANCE_PHASE` | Sharpe 1× | Sharpe 2× | max DD |
|---|---:|---:|---:|---:|---:|---:|
| nominee | 63 | 21 | 10 | 1.138 | 1.017 | 0.124 |
| 1 | 57 | 21 | 10 | 0.999 | 0.871 | 0.137 |
| 2 | 69 | 21 | 10 | 0.950 | 0.832 | 0.118 |
| 3 | 63 | **19** | 10 | 0.866 | 0.734 | 0.178 |
| 4 | 63 | **23** | 10 | 0.878 | 0.761 | 0.153 |
| 5 | 63 | 21 | **4** | 1.390 | 1.258 | 0.117 |
| 6 | 63 | 21 | **16** | 1.202 | 1.072 | 0.124 |

**The score — the per-metric median across those seven points:**

| metric | median | floor | |
|---|---:|---:|---|
| net Sharpe 1× | 0.9987 | ≥ 0.80 | PASS |
| net Sharpe 2× | 0.8708 | ≥ 0.50 | PASS |
| net Sharpe 3× | 0.7428 | > 0 | PASS |
| annualised return 1× / 2× | 0.1322 / 0.1132 | > 0 | PASS |
| max drawdown 1× | 0.1236 | ≤ 0.20 | PASS |
| realised annualised volatility | 0.1288 | ≥ 0.06 | PASS |
| positive-quarter fraction | 0.6471 | ≥ 0.50 | PASS |
| positive folds 2× | 4 of 4 | ≥ 3 | PASS |
| **worst fold Sharpe 2×** | **+0.1954** | ≥ −0.25 | PASS |
| annualised one-way turnover | 21.91 | ≤ 25 | PASS |
| gross edge bps per turnover | 67.64 | ≥ 40 | PASS |
| cost share of positive gross | 0.0114 | ≤ 0.30 | PASS |
| five-largest-day share | 0.0310 | ≤ 0.35 | PASS |
| max fold share of positive PnL | 0.3147 | ≤ 0.60 | PASS |
| executed trades | 3577 | ≥ 500 | PASS |
| **neighbourhood positive fraction** | **1.0000 (7 of 7)** | ≥ 0.70 | PASS |
| **long gross PnL** | **+0.5568** | > 0 | PASS |
| **short gross PnL** | **+0.0707** | > 0 | PASS |
| declared roles vs traded sides | long, short | required | PASS |
| **trial-adjusted confidence** | **0.8390** (B = 0.9770, T = 7) | ≥ 0.90 | **FAIL** |

**Twenty-one of the twenty-two measurable floors pass on the median. One does not, and it is
decisive.**

The sweep also corrects the simulator once more, and in the direction that matters: the **cadence**
axis is far more fragile than the offline surface suggested. Points 3 and 4 — cadence 19 and 23,
a ±9.5% move — came back at Sharpe 0.866 and 0.878 against the nominee's 1.138, and their
drawdowns rose to 0.178 and 0.153. That is the plateau's real texture, and it is the reason the
median B is 0.9770 rather than the ~0.984 the simulator projected.

---

## 11. Falsification — **#37**

Run for the record even though #36 had already decided the verdict, because "the mechanism is real"
and "the mechanism clears the bar" are different claims and only one of them is in doubt.

**Exact sign inversion of the nominated point**, scored against the eight core floors:

| core floor | inverted book | |
|---|---:|---|
| net Sharpe 1× | −1.552 | fails |
| net Sharpe 2× | −1.671 | fails |
| net Sharpe 3× | −1.790 | fails |
| annualised return 1× | −0.1940 | fails |
| annualised return 2× | −0.2070 | fails |
| maximum drawdown | 0.5926 | fails |
| realised annualised volatility | 0.1333 | clears |
| executed trades | 3865 | clears |

The two it clears are the two that are sign-symmetric by construction — an inverted book trades the
same names at the same times with the same magnitudes. **The inversion does not clear the core
floors; the falsifier is satisfied.** The apparent edge is not a cost, funding or cap asymmetry.

**Gross-edge placebo** — the candidate's own weight multiset and rebalance schedule preserved
exactly, only *which* eligible symbol receives which weight randomised, scored on gross edge:

| | bps per unit one-way turnover |
|---|---:|
| candidate | **77.82** |
| 8 placebo books | min −16.66, median 5.56, max 23.15 |
| exceedance | **0.0000** |

Not one placebo reached a third of the candidate's gross edge. The edge lives in the *attribution* —
which name gets which weight — which is precisely where a cross-sectional ranking claims it lives,
and not in the book's size profile or its trading calendar.

---

## 12. Conclusion, and what the organiser should know

**No nomination.** The frozen candidate stays on disk with its neighbourhood declared and its sweep
on the record, because the sweep is the evidence for the conclusion, not a submission.

Three things are worth carrying forward from this lane.

**First, the lane's mechanism is real and it is not a beta ranking.** Removing a causally estimated
market component adds Sharpe in every one of four control pairings, roughly quadruples the Sharpe
in the chop regime where a raw ranking is nearly worthless, halves the short sleeve's bleed, and
turns the worst fold from −0.35 to −0.12 on phase-averaged evidence. The candidate that came out of
it clears the drawdown, volatility, turnover, cost-density, fold-positivity, role and
neighbourhood-positivity floors on its plateau median, with all four folds positive at double cost.
The thing it cannot do is be *statistically distinguishable enough* from zero to survive an
eight-fold multiplicity penalty on four years of daily data.

**Second, that penalty is the binding constraint for this whole class of strategy, and it may be
worth the organiser knowing how binding.** `1 − T(1−B)` with `T ≥ 8` requires `B ≥ 0.9875`, which
on a 1445-day in-sample window is a **median** Sharpe near 1.13. A book with a true Sharpe of 1.0
has roughly a coin's chance of showing a plateau median above that, and a 20-name dollar-neutral
cross-section is not a Sharpe-1.5 object. The floor is doing what it was designed to do — it is
just worth recording that in this lane it binds at a level where a genuinely positive, genuinely
robust, all-folds-positive book still fails, and it binds hardest on teams that spent their trials
on questions rather than on one lucky point. A team that ran exactly eight trials and got a
fortunate phase would clear it where this one did not.

**Third, the short-sleeve floor is a structural fact about this window, not a signal-quality
problem.** The equal-weight top-20 basket returned a summed simple +2.47 on price over the in-sample
window. Every diversified short sleeve tested — 48 configurations across formation, cadence and
width — was gross-negative, the best at −0.22. Only concentrating the short sleeve to a fifth of a
twenty-name cross-section made it positive, and it did so by about 0.07 against a long sleeve of
0.56. Any cross-sectional lane scored on this window meets that arithmetic, and the fix is a shape
decision rather than a better signal. It is worth the organiser knowing that this floor and the
20-name universe interact: a 40-name universe would have offered a deeper loser tail to short
without the concentration penalty.

Four trials remain unspent. They were not spent because no further trial could change the verdict:
the confidence floor is a deterministic function of a number the sweep already measured.

---

## 13. Blindness

Only `data/cup20/is/` was opened, through `pandas.read_parquet` in `research/` and through the
organiser's own harness for every scored number. No holdout snapshot, no acquisition snapshot, no
organiser-only tree and no other team's directory was read, listed, or resolved, in the working
tree or in version control. No market data was fetched. Every scored number in this certificate
came out of `scripts/cup20_evaluate.py`; the team wrote no scorer and never touched the journal.
The workspace scan reports 0 violations at every `--check`.
