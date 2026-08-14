# team-10 — Research Certificate

**Lane:** volatility-regime risk-on / risk-off timing (`volatility-regime-risk-on-risk-off-timing`)
**Nomination:** `volofvol-regime`
**Score (charter §7.2, neighbourhood median):** **G = 44.297**
**Trials:** 9 accepted (#101–#109), 3 unspent. Multiplicity-charged count under A6: **T = 2**.
**Falsification:** the exact sign inversion fails 6 of 8 core floors. `sign_inversion_not_profitable` PASS.

---

## 0. The answer, first

My mandate asks a question rather than for a book: *does regime timing add anything a static book
does not already have?* On this window, measured through the organiser's harness with everything
except the timing layer held identical:

| book | journal | Sharpe 1× | maxDD 1× | folds + | G |
|---|---|---:|---:|---:|---:|
| **untimed base book** — the layer removed | #103 | 0.467 | 0.272 | 2 / 4 | **−10.03** |
| the same book + a declared **drawdown brake** (5/10/15%) | #106 | 0.427 | 0.275 | 2 / 4 | **−8.80** |
| a **random gate** at matched selectivity, reading no data | #105 | 0.096 | 0.258 | 1 / 4 | **−17.19** |
| a **volatility-LEVEL** gate — the obvious reading — matched | #104 | 0.631 | 0.169 | 3 / 4 | **+5.19** |
| a **price-trend** gate at matched selectivity | #107 | 0.728 | 0.228 | 3 / 4 | **−1.31** |
| **the nominee** (vol-of-vol), own point | #101 | **1.087** | 0.189 | **4 / 4** | **+47.56** |
| **the nominee, neighbourhood median — MY SCORE** | #102 | **1.063** | 0.192 | **4 / 4** | **+44.30** |

Yes — and the answer is carried by a specific and non-obvious regime variable. Three findings, in
order of how much they surprised me:

1. **The obvious reading of this lane is signed the wrong way.** "Volatility is high, go flat" has
   a *negative* median ranking score at every formation window I tried, across ~1 400 offline
   configurations. Run through the organiser's harness at matched selectivity it scores G = 5.19
   against the layer's 47.56.
2. **The level of volatility carries almost nothing; the *steadiness* of it carries the timing.**
   The nominee's regime variable is the coefficient of variation of short-horizon realised
   volatility — a scale-free second-order statistic that cannot tell a quiet market from a violent
   one, only a stable variance process from an unstable one.
3. **This is not a drawdown brake.** An actual declared drawdown brake on the identical untimed
   book reaches G −8.80 and does not reduce the drawdown at all (0.275 against the untimed 0.272).
   Whatever the regime layer is doing, the risk policy does not give it away for free.

4. **The channel is not momentum in disguise, and the test that shows it is the one that could
   have embarrassed me.** `vov` carries a rank correlation of 0.31 with the trailing market return,
   so a price-trend gate is the control that matters. Alone it scores G −1.31 (#107). ANDed with
   the vol-of-vol gate and nothing else changed, it scores **G 63.75** (#109) — above either gate
   alone. The two channels are complements, not substitutes: adding volatility-regime information
   to a trend gate is worth +65 G points, and adding trend information to the volatility gate is
   worth +16. That conjunction is *not* my nomination — a price-trend gate belongs to another
   team's mandate and the run is journaled as an ablation precisely so it can never become my
   answer — but it is the strongest evidence in this certificate that my lane's channel is real.

The honest counterweight, stated rather than buried: in ~350 offline configurations a *searched*
trend gate reached G ≈ 86, above anything my vol-of-vol family reached. My gate was searched and
that trend control was not, so neither comparison is like-for-like, and I do not claim this channel
dominates price trend. What is measured, matched and journaled is that it dominates the volatility
**level**, a **drawdown brake**, and a **matched random gate** — and that it adds to trend rather
than duplicating it.

---

## 1. The book

Base book: **equal weight, long, every eligible name, rebalanced at every 8h boundary.** No
selection, no tilt, no cross-sectional opinion. On its own it is a bad book here — that is the
point, because everything claimed below is claimed by the layer on top of it.

The layer is one binary decision per boundary. Risk-on holds the base book; risk-off returns `{}`
and the book goes to cash. Weights are never negative, so the declared role is **long only**, and
the harness confirms it: `declared_roles_match_traded_sides` PASS, `short_gross_pnl = 0.000000`.

```
m[t]    equal-weight market log return observed at decision t, over the symbols eligible at t
rv[j]   sqrt(mean(m[j-FORMATION_BARS+1 .. j]^2))
vov[t]  std(rv[t-OUTER_BARS+1 .. t]) / mean(same)          <- scale free
z[t]    (vov[t] - mean(vov[t-BASELINE_BARS+1 .. t])) / std(same)
risk-on <=> z[t] <= REGIME_THRESHOLD
```

**Causality.** In panel coordinates the bar that has closed by decision `t` is the bar that *opened*
at `t-1`, which is exactly what the harness's own truncation admits
(`searchsorted(open_time + interval, decision_time, side="right")`). Every measure in this study is
built from a per-bar quantity and shifted once, centrally, so no statistic is ever one bar more
informed than the runner allows — and never one bar less, which would be leaving evidence on the
table rather than being careful.

**Nominee:** `FORMATION_BARS=5, OUTER_BARS=150, BASELINE_BARS=360, REGIME_THRESHOLD=−0.30,
REBALANCE_CADENCE=1`.

**Mechanism.** In a market whose leverage is renewed continuously through perpetual funding, a
variance process that repeatedly bursts and collapses is one where positioning is being forcibly
reset — liquidation clusters, funding whipsaw, gap risk — and that is where the drift is negative. A
variance process that is *steady* is one absorbing flow without breaking, and that is where the
drift is positive. The statistic is deliberately blind to which level it is steady at: `vov` is a
ratio of two moments of the same series, so scaling every return leaves it unchanged.

---

## 2. Method, and what it cost

**Offline exploration before the first trial: about 24 000 full-window simulations.** The organiser
charges trials; a private replica of the evaluator does not, and running one is the only way to
explore an axis honestly on a twelve-trial budget.

The replica (`research/fastsim.py`) reproduces the two-pass pipeline: unit-gross normalisation, the
§4 caps applied by uniform reduction at both ends of the common risk unit, `s_t = clamp(0.10/σ_t,
0.20, 3.0)` off the reference book's trailing 90-day gross returns, fills at the boundary open with
quantities sized off the boundary mark, funding split into the settlement *at* the boundary (paid by
the carried position) and settlements strictly inside the bar, 5 + 2.5 bps per side at 1×/2×/3×,
participation capped at 0.1% of the trailing three bars' quote volume, and delisting force-exits.

**Calibration.** It was checked against the organiser's own modules (`cup20.runner.run_candidate`,
`cup20.metrics.window_metrics`) imported and run in-process on an equal-weight long book. This
produced no journal entry and no tournament number; it exists only to measure the replica's error.

| | organiser | replica | difference |
|---|---:|---:|---:|
| Sharpe 2× | 0.173034 | 0.174380 | 0.0013 |
| annualised volatility | 0.243096 | 0.243110 | 0.00001 |
| max drawdown 2× | 0.318803 | 0.318800 | 0.000003 |
| fold Sharpes 2× | 0.4015 / −0.4224 / −0.3052 / 1.0145 | 0.4055 / −0.4225 / −0.3073 / 1.0145 | ≤ 0.004 |
| mean risk-unit scalar | 0.251714 | 0.251714 | exact |

**Out-of-sample check on the replica itself.** Before the sweep ran, the replica predicted the
declared neighbourhood's median at **G = 44.29 and median Sharpe 1.063**. The harness returned
**G = 44.297 and median Sharpe 1.063348** (#102). Every offline number below is from the replica
and is labelled as such; no offline number is reported as a measurement.

### 2.1 Two bugs the replica found in my own work, reported rather than buried

**A silent constant.** The first version of the exact-signal module ran a cumulative sum over a
series whose first element was NaN, which poisons every partial sum after it; a `sd > 0` guard then
fell through to a constant `0.0`, and the resulting book was always-long or always-flat and looked
like a real (bad) result rather than a bug. Cause: the panel begins at `IS_START`, but the bar that
closes at the *first* decision opened before it — the strategy sees that bar and the replica did
not. Fixed by reading the prior close from the bar file, and the silent fallback replaced by a
raise. The strategy's own transcription was never affected.

**A "flat" state that was not flat.** My weight builder mapped a regime state of `0` onto the
achievable net-exposure ladder, where zero net means *half the universe long and half short* rather
than *no position* — and the halves were split in eligibility order, which is an arbitrary
cross-sectional bet wearing the label "no exposure". Every "long-flat" sweep before that point was
therefore measuring a different book. It was found by transcribing the strategy and comparing, and
the fix cost a full re-run of the design box. The corrected long/flat book is **better and cleaner**
than the contaminated one (4/4 folds at every phase rather than at some), so nothing was lost but
time. The default is now `onoff`, because a default that quietly trades when the signal says do
nothing is the wrong default.

**Transcription proof.** The frozen `strategy.py` was run through the organiser's own
`generate_targets` on the real snapshot and compared boundary-by-boundary with the replica's book:
rebalance flags identical at all 4 335 boundaries, 1 758 risk-on boundaries in both, **maximum
weight difference 1.4 × 10⁻¹⁷**.

---

## 3. What I explored before spending anything

**IC study — 412 causal regime measures** across six channels (level, term structure, cross-
sectional dispersion, correlation to BTC, asymmetry, time-aggregation), 13 formation windows, three
standardisation windows, against forward market returns at 1 / 3 / 9 / 21 / 45 / 90 / 135 bars.

Nothing reaches |IC| 0.06 at one bar. The largest full-window rank ICs sit at 90–135 bars:
`vr:6,180` +0.35, `rangeratio:270` +0.33, `rvbtc:180|z360` +0.33, `btccorr:360` −0.26. **The number
worth stating is the effective sample, not the IC**: at a 90-bar horizon, 4 335 overlapping rows
carry about 48 independent observations, so an IC of 0.33 is roughly two standard errors. That is
why nothing below rests on an IC table.

**Configuration sweeps — ~24 000 full-window simulations**, ranked by the *median* over each
family's whole grid rather than its maximum:

| sweep | configurations | what it varied |
|---|---:|---|
| broad | 9 016 | 46 measures × 2 signs × 7 thresholds × {long-flat, long-short} × 7 cadence/phase |
| channel-fine | 9 360 | four named channels × formation windows × 5 thresholds × cadence 3/9/21 × phases |
| level control | 6 000 | `rv`/`rvbtc` at 6 windows × both signs × 5 thresholds × 4 cadences × phases |
| exact-arithmetic design box | 2 100 × 2 | the frozen signal's own inner/outer/baseline/threshold/cadence/phase |
| nulls and controls | ~1 700 | matched-selectivity nulls, trend controls, neighbourhood previews |

**Formation horizons: eleven** (3, 4, 5, 6, 7, 8, 9, 12, 21, 45, 90 bars and beyond in the channel
sweeps) — far past the required three. **Rebalance/holding horizons: eight** (cadence 1, 2, 3, 4, 5,
6, 7, 9), **with every phase offset swept at every cadence** and every result reported as a
phase-agnostic mean.

---

## 4. Which regime variable carries the information

The mandate asks which of level, term structure, dispersion or correlation carries the timing. The
offline answer, family medians over each family's whole grid (replica):

| channel | best family | median G over its grid |
|---|---|---:|
| stability of the variance process (vol-of-vol) | `vov:6,180` (−) | **31.7** |
| time-aggregation / term structure | `vr:21,180` (+) · `rangeratio:135` (−) | 37.0 · 33.2 |
| level | `rvbtc:45` (+) | 22.7 |
| correlation to BTC | `corr:270` (+) · `btccorr:360` (−) | 21.5 · 18.3 |
| dispersion | `dispratio:180` | 12.4 |
| **level, in the OBVIOUS direction** (high vol → flat) | every window | **negative at all six** |

The last row is the finding. `rv:9/21/45/90/180/270` and `rvbtc:9/21/45/90/180/270` with the
"go flat when volatility rises" sign have median G between −5 and −31 — *every* window, *every*
threshold, *every* cadence. The profitable half of the level channel is the inverted one: be long
unless volatility is unusually **low**.

### 4.1 Two channels dropped despite scoring well — lane hygiene

Rank correlation of each measure with the trailing market return, the thing a momentum lane uses:

| measure | max &#124;ρ&#124; over 9/21/45/90/180-bar trailing returns |
|---|---:|
| `rangeratio:180` | 0.104 |
| `rvbtc:45` | 0.156 |
| `vr:21,180` | 0.158 |
| `rangeratio:90` | 0.225 |
| **`vov:6,180` (nominee family)** | **0.307** |
| `dispratio:90` | 0.553 |
| `semi:90` | 0.594 |
| `semi:45` | 0.755 |

`semi` — the downside share of realised variance — scored among the best of everything I tried
(family median G 20.3, peaks near 78) and is a trailing-return signal wearing a variance
decomposition. It was **dropped**. So was `dispratio`. A candidate better described by team 01's or
team 03's mandate than by mine is drift, and drift into an occupied lane is the one collision that
matters.

The nominee's own family is not perfectly clean either — ρ up to 0.307 — which is precisely why the
trend control of §7 was run and is reported whatever it said.

---

## 5. Effective bets — the number this lane must state

**The nominee's gate makes 38 regime transitions over the whole in-sample window**: 20 risk-on
spells and 19 risk-off spells across 3 823 live boundaries, mean spell length 90 bars on (30 days)
and 106 bars off (35 days), risk-on 47.2% of the time.

Thirty-eight is the number of independent decisions behind a Sharpe of 1.06. It is not 4 335, and
the daily bootstrap that produces B = 0.958 does not know that — a 10-day block is far shorter than
a 30-day spell, which biases the fraction upward. Anyone reading this should treat the confidence
term as the weakest number in the packet. The evidence I would actually stand on is §6: the layer
beats a null that holds the spell structure fixed and randomises only *when* the spells fall.

---

## 6. Falsification

### 6.1 The organiser's battery — journal #108

**Exact sign inversion: fails 6 of the 8 core floors.**

| core floor | inverted book | verdict |
|---|---:|---|
| net Sharpe 1× / 2× / 3× | −1.165 / −1.200 / −1.235 | fails |
| annualised return 1× / 2× | −0.156 / −0.160 | fails |
| maximum drawdown | 0.581 | fails |
| realised volatility | 0.137 | clears |
| executed trades | 37 302 | clears |

The two it clears are the two that invert trivially — a mirrored book trades the same number of
times with the same exposure. Every floor that is a claim about *direction* fails, and by a wide
margin. `sign_inversion_not_profitable` **PASS**: the apparent edge is not a construction artifact.

**Gross-edge placebo: exceedance 1.0000, and this was predicted before the battery ran.** All eight
placebo books returned a gross edge of exactly 261.3326 bps — the candidate's own value, to four
decimals, minimum and maximum alike. The reason is arithmetic rather than surprising: the placebo
permutes *which eligible symbol receives which weight*, and this book gives every eligible symbol
the same weight, so the permutation is the identity map. The placebo half of the battery carries no
information about this candidate and I do not present it as though it did. §6.2 is the null that
does.

### 6.2 The matched-selectivity null — the test this lane needs

The harness's placebo randomises **which symbol receives which weight**. A timing lane whose base
book is uniform over the whole eligible set has no selection for that to null: permuting equal
weights among the same names reproduces the book exactly, so the placebo is a no-op for this
candidate and its exceedance carries no information. That is a property of the mandate, not a
weakness I can design around, and it is stated rather than left for a reviewer to notice.

The null that *does* bite a timing layer randomises **when** the risk-off spells fall while holding
the on-fraction and the run-length structure exactly. Offline, 150–250 draws per configuration
(replica):

| configuration | real G | null median G | null max G | G exceedance |
|---|---:|---:|---:|---:|
| the nominee family, five phases | 32.3 – 57.1 | ≈ −27 | 42.9 – 52.7 | **0.000 – 0.033** |
| `vov:3,180` | 82.7 | −13.9 | 61.7 | 0.000 |
| `rangeratio:90` | 78.6 | −8.5 | 69.4 | 0.000 |
| `rvbtc:45` | 73.4 | −3.8 | 59.7 | 0.000 |
| **`rv:45` — the volatility-LEVEL gate** | **−6.2** | −13.0 | 72.2 | **0.393** |

The last row again: a gate on the volatility level cannot be told apart from a random gate of the
same selectivity — 39% of matched random gates scored at least as well.

The same null was then run **through the organiser's harness** as journal **#105**, so the claim
does not rest on my own scorer: a random two-state gate matched to the nominee's on-fraction and
spell lengths, reading no market data at all, scores **G = −17.19**, fails 9 floors, is positive in
1 of 4 folds, and earns **28.7 bps of gross edge per unit turnover against the nominee's 261.3**.

This also disposes of the mechanical explanation. A random long-flat gate raises the untimed book's
Sharpe from 0.19 to a median 0.26–0.53 in the replica purely by being out of the market — any claim
about a timing layer not measured against this null is measuring that.

---

## 7. Ablations

All six controls were journaled `--kind ablation` under amendment A6, which is what made this
section affordable: at the pre-A6 charge they would have taken T from 2 to 8 and cost the candidate
its confidence term outright. Every one forfeits the right to be nominated, and none shares source
bytes with the nominee.

| # | control | what it changes | Sharpe 1× | maxDD | folds + | G |
|---|---|---|---:|---:|---:|---:|
| #103 | `ablation-untimed` | the timing layer removed, nothing else | 0.467 | 0.272 | 2/4 | −10.03 |
| #104 | `ablation-vol-level` | steadiness → **level** (the obvious reading), matched selectivity | 0.631 | 0.169 | 3/4 | +5.19 |
| #105 | `ablation-matched-random` | the gate → a random Markov gate reading no data | 0.096 | 0.258 | 1/4 | −17.19 |
| #106 | `ablation-drawdown-brake` | no timing; a declared 5/10/15% drawdown brake instead | 0.427 | 0.275 | 2/4 | −8.80 |
| #107 | `ablation-trend-gate` | the gate → a trailing-return gate at matched selectivity | 0.728 | 0.228 | 3/4 | −1.31 |
| #109 | `ablation-trend-plus-vov` | the trend gate **AND** the vol-of-vol gate | 1.281 | 0.140 | 4/4 | **+63.75** |

**Controls-off** is #103. **Individual controls** are #104 (level only), #106 (brake only) and #107
(trend only). **The combined control** is #109, which runs two gates together and is the only run
in this certificate where more than one mechanism is switched on at once.

**The drawdown-brake result is the one worth pausing on.** My brief warned that "high volatility, go
flat" is mostly a drawdown brake, which the risk policy hands over for free. Measured: a declared
brake at 5/10/15% moves the untimed book from G −10.03 to G −8.80, leaves the drawdown *unchanged*
at 0.275 against 0.272, and increases the trade count from 76 443 to 106 152 — it churns without
protecting. Charter §6's disclosure explains why: the brake watches the book the common risk unit
has already resized, so it engages at levels that are not the ones it appears to declare. The
regime layer is not a brake in disguise, and a brake is not a substitute for it.

### 7.1 Is the volatility channel just momentum? — #107 and #109

This is the control I most expected to lose, because `vov` carries ρ = 0.31 with the trailing
90-bar market return and "steady variance" and "trending market" are not obviously different
states.

| book | Sharpe 1× | maxDD | F1 | F2 | F3 | F4 | G |
|---|---:|---:|---:|---:|---:|---:|---:|
| trend gate alone (#107) | 0.728 | 0.228 | +1.636 | +0.048 | **−0.508** | +1.330 | −1.31 |
| vol-of-vol alone (nominee, #101) | 1.087 | 0.189 | +1.612 | +0.379 | **+1.671** | +0.538 | +47.56 |
| both, ANDed (#109) | **1.281** | **0.140** | +2.211 | +0.732 | +1.367 | +0.520 | **+63.75** |

The conjunction beats both parents on Sharpe, on drawdown, on every fold Sharpe but F4, and on the
ranking score. The two channels are **complementary**: the trend gate's failure is concentrated in
F3 (FTX, the bear trough) where it is −0.508 and the volatility gate is +1.671, which is exactly
the regime the volatility channel claims to detect and the price-trend channel is known to be
whipsawed by.

Three caveats I will not let this table hide. Selectivity falls when two gates are ANDed, so #109
is not a matched-selectivity comparison. Its turnover is 12.2× against the nominee's 5.9×. And it
is a book my mandate does not authorise me to nominate — the trend half belongs to lanes 01 and 03,
which is why it was journaled `--kind ablation` before it ran and can never become my answer. It is
reported because the question "does my lane's variable carry anything a price-trend variable does
not" has a clear measured answer, and the answer is yes.

---

## 8. Role checks

**Long:** the only side the book trades. Gross long PnL 0.599 on the neighbourhood median, positive
in every point of the sweep. **Short:** never traded — `short_gross_pnl = 0.000000`, so the
short-PnL floor is not applicable and the corresponding compliance credit is forfeited (12 of 13
unpriced floors earn full credit; the ranking score is multiplied by 0.923 accordingly). Declaring
`long` matches what the book did, and the harness's own check agrees.

**Chop:** the regime layer's whole claim is about chop, so it is checked directly rather than as a
sub-period label. F2 (2021-08 → 2022-08, the second peak, bear onset and LUNA) and F3 (2022-08 →
2023-08, FTX and the bear trough) are the two chop/stress folds. The untimed book scores −0.422 and
−0.305 there; the nominee scores **+0.379 and +1.671**. The layer's entire contribution is
concentrated in exactly the regime it claims to detect, and it does not give it back in the trending
folds (F1 +1.612, F4 +0.538).

---

## 9. The declared neighbourhood and the sweep — journal #102

Nominee fixed **before** the declaration; `neighbourhood.json` was written afterwards and the
`--check` that validates it consumed no trial. Four coordinates, nine points, each varied one at a
time:

| coordinate | nominee | below | above | variation |
|---|---:|---:|---:|---:|
| `FORMATION_BARS` | 5 | 4 | 6 | 20% |
| `OUTER_BARS` | 150 | 120 | 180 | 20% |
| `BASELINE_BARS` | 360 | 270 | 450 | 25% |
| `REGIME_THRESHOLD` | −0.30 | −0.45 | −0.15 | 50% |

All nine points ran as separately materialised files with nine distinct `strategy.py` digests, and
**no point reproduced the nominee's metric vector** (amendment A1). Nine of nine points have
positive 1× return and positive 2× Sharpe: `positive_point_fraction = 1.0000`.

Per-point Sharpe spans 0.285 to 1.238. The weakest point by a distance is `BASELINE_BARS = 450`
(Sharpe 0.285, maxDD 0.250) — a 150-day standardisation window is long enough that the z-score stops
responding to the regime it is meant to measure. It is inside the declaration and it drags the
median, which is what a declared neighbourhood is for.

**The nominee is not the peak of its own neighbourhood** — three of the eight other points beat it
on Sharpe. The median (1.063) sits below the nominee (1.087), which is the direction §7.2 exists to
enforce.

**Cadence and phase are not neighbourhood coordinates, and that is deliberate.** Phase offset was
the single largest source of variation anywhere in this study: at cadence 5 the same signal spans 25
ranking-score points across its five phases (neighbourhood-median G 32.3 to 50.8). The nominee runs
at **cadence 1**, where no phase offset exists to choose and therefore no phase luck can be
harvested. Turnover (5.92×) and trade count (37 052) sit far inside their limits, so nothing forced
a slower cadence. Both axes were swept exhaustively offline and are reported as phase-agnostic
means, per charter §9.1.

---

## 10. Floors on the scored median

Twenty of twenty-one measurable floors pass. One fails:

**`positive_quarter_fraction` = 0.4706 against a 0.50 floor** — 8 of 17 calendar quarters positive.
Under amendment A4 this is priced (it costs the whole 8-point term in `G`) rather than fatal, and I
did not chase it. The cause is structural and worth naming: the book is in cash 53% of the time, so
a quarter in which the regime never turns risk-on returns approximately zero and can land on either
side of it by a few basis points of residual cost. Six of the nine quarters that score negative do
so by less than 40 bps. A book that spends half its life flat will always struggle with a *count*
of positive quarters while doing well on every magnitude-based measure, and the honest fix would
have been to trade a book I had less evidence for.

Also disclosed: **`max_drawdown` = 0.1916 against a 0.20 ceiling** passes with 4% of headroom. That
is thin. The nominee's own point is 0.1893 and the worst point in the neighbourhood is 0.2502.

**Exposure caps.** The requested book was never trimmed (0 of 4 335 boundaries). The executed book
was reduced at 44 of 4 335 boundaries, minimum scale 0.333, median 0.579, always by the gross cap —
these are boundaries where the risk-unit scalar hit its 3.0 ceiling after a long flat stretch had
driven the reference book's trailing volatility toward zero. The risk-unit scalar's median is
0.2129 against a floor of 0.20: this book is pinned near the bottom of the clamp almost everywhere,
because a top-20 crypto basket realises ~97% annualised volatility against a 10% target.

---

## 11. Every failure and every abandoned attempt

| what | outcome | evidence |
|---|---|---|
| plain realised-volatility level, "high vol → flat" | **refuted** — negative median G at all six windows; indistinguishable from a random gate (exceedance 0.393) | offline; harness #104 |
| `semi` (downside share of realised variance) | **abandoned despite scoring well** — ρ = 0.594 with trailing returns; it is momentum in disguise | offline, §4.1 |
| `dispratio` (cross-sectional dispersion / market vol) | **abandoned** — ρ = 0.553, same reason | offline, §4.1 |
| cross-sectional dispersion channel generally | **weak** — best family median G 12.4 | offline sweeps |
| correlation-to-BTC channel | **weak** — best family median G 21.5, and the sign flips in F2 | offline sweeps |
| a **per-symbol** regime dial, to give the placebo something to null | **impossible in this book** — with a long/flat gate every eligible name carries the same weight, so the per-symbol ranking is inert by construction; all four rank variants returned metrics identical to the no-rank book to every printed digit, and the harness's placebo later returned exceedance 1.0000 for the same reason | offline, §6.2; #108 |
| long/**short** expression (risk-off = short the basket) | **worse than long/flat in almost every family** — the short leg does not earn on this window | offline sweeps |
| `vr:21,180` (variance ratio) as the nominee | **considered and rejected** — best plateau median of any family, but its on-vs-off spread is *negative* in F4, where vol-of-vol's is positive in all four folds | offline |
| `vov` at `OUTER_BARS` 120 or 210, `BASELINE_BARS` 450 | **weak** — the surface has cliffs on both sides of the 150–180 ridge; two of these are inside the declared neighbourhood and drag the median honestly | #102 |
| cadence 5 (highest offline G) | **rejected in favour of cadence 1** — 25 G points of phase spread | offline, §9 |
| the "flat" state that was a dollar-neutral book | **bug, cost a full re-run of the design box** | §2.1 |
| the NaN-poisoned cumulative sum | **bug, caught before any trial** | §2.1 |

**Pivots: none.** The original thesis — that a volatility-regime variable times exposure — was
never falsified; what was falsified was the *obvious* version of it, which is a different thing and
is reported as a result rather than as a pivot.

---

## 12. For the organiser

- **No harness defect was encountered.** Both team-facing commands behaved exactly as documented
  through nine trials, including the `--ablation` mode added in the D1 fix and the import restored
  in the D2 fix. The `--check` dry-run of the sweep substitution caught nothing because there was
  nothing to catch, which is the outcome it is designed for.
- **A6 is load-bearing for this lane.** Six of my nine trials are controls. Under the pre-A6 charge
  T would have been 9 rather than 2, taking the trial-adjusted confidence from 0.916 to 0.622 and
  the ranking score down by its whole 7-point term — for research that made the result *more*
  trustworthy, not less. The orthogonality control (#109), which is the single most informative run
  in this certificate, is exactly the run I would have skipped. That is the effect A6 was written to
  remove and, on this team's evidence, it removed it.
- **The permutation placebo cannot bite a pure timing lane** (§6.2). It is not broken; it nulls
  selection, and a timing lane over a uniform base book has none. If the organiser wants a
  falsifier with teeth for lane 10, the run-length-preserving null of §6.2 is the one — and it is
  cheap, because the candidate's own gate supplies the run-length distribution.
