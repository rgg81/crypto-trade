# Team 09 — Research Certificate

**Lane:** taker-flow / price-volume pressure (`taker-flow-price-volume-pressure`)
**Nominated candidate:** `print-size-flow`
**Declared roles:** long, short
**Seed:** 17
**Status:** NOMINATED

---

## 0. The finding, in one paragraph

Taker-buy imbalance aggregated to 8h bars is a weak and unreliable basis for a book — the obvious
reading of this lane, run through the identical machinery, scores a ranking score of **−16.9** and
fails eight hard floors. What survives the aggregation is not the *level* of aggressive buying but
its *print structure*: whether the USDT arrived in many small trades or a few large ones, and
whether the large prints leaned the same way as the rest of the tape. A dollar-neutral
cross-sectional book built on two such measures, with the price move and the coin's size and
turnover class regressed out every boundary, clears every measurable floor with room. With the
print-size mechanism removed and nothing else changed, it does not; with the print-size information
scrambled across symbols it loses roughly a third of its ranking score; and a random gate at
identical selectivity is *negative*.

---

## 1. What was done before the first trial was spent

No organiser trial was spent until the design space had been mapped offline. The offline work, all
of it under `research/`, was:

| | count |
|---|---:|
| candidate flow measures constructed and IC-tested | **90 distinct measures** |
| cross-sectional rank-IC evaluations (measure × horizon, raw / residualised / purged) | **403** |
| **full-window book simulations logged to CSV** | **3,353** |
| further full-window simulations outside the logged sweeps (phase studies, falsifiers, neighbourhood comparisons, strategy replays) | ~350 |
| **total offline full-window simulations before trial #90** | **~3,700** |

Of the logged simulations, **429 were phase studies alone** — every phase offset of twelve
(measure, window, cadence, k) configurations — and 1,421 were of the nominated measure pair.

The offline simulator (`research/sim.py`) implements charter §4 and §6 directly: unit-gross
normalisation, exposure caps by reduction, the reference pass, the common risk unit
`clamp(0.10/σ_t, 0.20, 3.0)` off trailing-90-day gross returns, the executed pass, fills at the next
bar open, 5 bps + 2.5 bps per side at 1×/2×/3×, and native funding into the holding interval. It was
sanity-checked against the only public number the charter states about this window — §14.9's
"equal-weight top-20 basket sums to +1.99 in simple returns over 4335 bars" — reproducing **+1.978
over 4,335 bars**.

**The frozen strategy was proved to reproduce the offline research book exactly.**
`research/verify.py` drives `candidates/print-size-flow/strategy.py` through past-only contexts
built from the data root at all 4,335 boundaries and compares the emitted book against the offline
construction. Re-run at the frozen source digest `8031850e…`:

```
strategy replay: 4335 boundaries in 37s
max |dw| = 0.000e+00   mean |dw| = 0.000e+00
boundaries differing by > 1e-9: 0 of 4335
weight correlation = 1.00000000
```

Every offline number in this certificate therefore describes the code that was frozen, not an
approximation of it.

**Measured fidelity against the organiser (trial #90).** The simulator is optimistic by about
0.08 Sharpe on the nominee and essentially exact on risk:

| metric (1×) | organiser | offline | error |
|---|---:|---:|---:|
| net Sharpe | 1.6379 | 1.7141 | +0.076 |
| annualised return | 0.2074 | 0.2175 | +0.010 |
| annualised volatility | 0.1194 | 0.1186 | −0.001 |
| maximum drawdown | 0.0829 | 0.0830 | +0.000 |
| annualised turnover | 22.478 | 22.301 | −0.177 |
| gross edge per turnover (bps) | 94.14 | 98.01 | +3.9 |
| worst fold Sharpe (2×) | 0.6234 | 0.6157 | −0.008 |
| trade count | 85,502 | 80,539 | −4,963 |

The residual optimism comes from the three approximations the simulator's own docstring declares:
unfilled participation-capped notional is dropped rather than carried, delist force-exits are taken
at the bar's own close rather than the organiser's exact last open, and funding is folded into one
per-bar charge.

**Where the simulator is NOT reliable, stated plainly.** It tracks the nominee closely but
*compresses the range*: on the transparent baseline it predicted a ranking score of **+9.0** where
the organiser measured **−16.9**, a 26-point error in the optimistic direction. The simulator was
good enough to rank designs and to choose what to spend a trial on; it was not good enough to
certify a marginal book, and nothing here rests on it where an organiser number exists.

---

## 2. The mechanism, and how it was arrived at

### 2.1 What is observable

Each 8h bar carries `quote_volume`, `taker_buy_quote_volume`, `trade_count` and OHLC. Denomination
is stated because a ratio across denominations is meaningless: **every ratio here is quote/quote
(USDT)**, and the base-denominated `volume` / `taker_buy_volume` fields are used only in the `perb`
control measure, which is not in the nominee. From these:

```
imb_t   = (2 · taker_buy_quote_volume_t − quote_volume_t) / quote_volume_t     signed, USDT
ats_t   = quote_volume_t / trade_count_t                                       average print, USDT
shock_t = clip( log ats_t − mean(log ats over the NORM_BARS bars before t), ±3 )
```

### 2.2 The prior, and where it was wrong

The pre-registered prior was the standard microstructure one: aggressive flow is informative when it
reflects information and predatory when it reflects forced execution, and a few large prints look
more like one informed participant than many small ones do. The expectation was therefore that
**large**-print imbalance would predict better than small-print imbalance.

**Measured, the opposite is true.** Re-derived at the nominee's own parameters
(`research/verify_claims.py`), purged rank IC against the tradeable forward return
`open[i+h]/open[i]`, controls = window return + print-size class + turnover class:

| measure | h=9 | h=21 | h=42 |
|---|---:|---:|---:|
| `imbsml` — imbalance over **below**-norm-print bars | **+0.0377** (t 4.01) | **+0.0435** (t 3.24) | **+0.0571** (t 3.80) |
| `imbbig` — imbalance over **above**-norm-print bars | +0.0130 (t 1.44) | +0.0193 (t 1.56) | +0.0343 (t 2.47) |
| `lvl` — plain imbalance, all bars (the obvious reading) | +0.0325 (t 3.69) | +0.0429 (t 3.34) | +0.0564 (t 3.85) |
| `imbeq` — equal-bar-weight imbalance (no print size) | +0.0379 (t 4.19) | +0.0515 (t 4.04) | +0.0639 (t 4.33) |

The below-norm restriction is roughly **twice** as informative as the above-norm one at every
horizon, and the above-norm measure is not significant at the two shorter horizons. The reading that
survives is the reverse of the prior: at this aggregation, *diffuse* aggressive buying — spread
across many prints — is the informative kind, and flow concentrated into a few large prints is the
transient kind. That is consistent with what a large print usually is in a crypto perp: an execution
algo working a block, or a liquidation being unwound. Neither is a forecast.

> **An earlier draft of this certificate cited +0.060 / +0.031 / +0.037 for these three measures and
> claimed the other two were negative in F1. Those figures came from a pre-freeze configuration and
> could not be reproduced at the frozen parameters. They have been replaced by the table above,
> which `research/verify_claims.py` regenerates. The direction and the roughly-2× ratio are
> unchanged; the magnitudes and the F1 claim were wrong.**

**A finding that cuts against the mechanism, stated here rather than buried.** At the pooled-IC
level, `imbeq` — equal-bar-weight imbalance, which removes the dominance of the highest-volume bars
*without using print size at all* — is as good as or better than `imbsml` at every horizon. The
print-size conditioning's advantage does **not** show up in pooled IC. It shows up in the book, where
`imbeq` scores an offline G of 19.9 against `imbsml`'s 46.5, because the print-size version's errors
are less concentrated in fold and drawdown. That distinction is the reason the equal-bar-weight
ablation was run on the organiser's scorer (§4) rather than argued from IC.

### 2.3 The two terms

Over the last `FORMATION_BARS` bars:

```
COVATS = Σ( imb_t · shock_t · quote_volume_t ) / Σ( quote_volume_t )
IMBSML = Σ( imb_t · quote_volume_t | shock_t ≤ 0 ) / Σ( quote_volume_t | shock_t ≤ 0 )
```

`IMBSML` is the granular half of the tape. `COVATS` is the USDT-weighted covariance between flow
direction and print-size shock — positive when the unusually-large prints leaned the same way the
flow did. Together they say: aggressive buying predicts when it is **broad-based and
size-confirmed**.

The score is `rank(COVATS) + rank(IMBSML)`, cross-sectionally, residualised same-boundary by OLS
against three ranked controls — the window price change, mean `log ats` and mean `log quote_volume`.

**It is print size specifically, not activity in general.** The same covariance built against other
per-bar shocks, best offline G over the full sweep:

| shock the imbalance is covaried with | best offline G |
|---|---:|
| print size (`covats` / `bigp`) | **67.4 / 86.4** |
| quote volume (`covqv`) | 54.2 |
| trade count (`covnt`) | 32.3 |
| print size, normalised by its own dispersion (`covatsn`) | 50.0 |

Trade count alone is the weakest of the three. The discriminating quantity is the *size of the
average print*, which is exactly the ratio the mandate's "few large prints versus many small ones"
question is about.

### 2.4 Why the controls are there

Re-derived at the nominee's parameters (`research/verify_claims.py`), mean per-boundary
cross-sectional rank correlation of the score against each control, before and after
residualisation:

| control | raw score | residualised score |
|---|---:|---:|
| window price move | +0.1184 | +0.0109 |
| print-size class (mean `log ats`) | +0.2184 | +0.0170 |
| turnover class (mean `log quote_volume`) | +0.1659 | +0.0189 |
| **90-bar realised volatility — NOT controlled** | −0.1516 | **−0.0908** |

`corr(raw score, residual score) = +0.8194`, so residualisation removes the tilts without removing
the signal. On this window a big-coin-beats-small-coin tilt pays, so leaving those in would let a
size premium carry a book nominated for a taker-flow lane.

**Disclosed rather than removed:** the residualised score retains a **−0.091** rank correlation with
90-bar realised volatility — a mild long-lower-volatility tilt. It is not controlled for. It is
reported here because realised volatility was in fact the single strongest raw cross-sectional
predictor found anywhere in the EDA (raw IC −0.129 at h=21, t = −7.15), stronger than any flow
measure, and a reader is entitled to know that the book retains a fraction of it. It is roughly a
fifth of the raw exposure and an order of magnitude weaker than that standalone signal, and the
mechanism ablations in §4 are what establish that it is not what the book is earning.

### 2.5 Formation horizons and rebalance / holding horizons

Formation windows tested offline in full book simulations at **21, 42, 54, 63, 72, 81, 90, 99, 108,
117, 126, 144 and 180 bars** — 13 horizons, where the playbook requires at least three. The
underlying IC study additionally varied the measure lookback at 1, 3, 6, 9, 21, 42 and 90 bars
against forecast horizons of 1, 3, 9, 21 and 42 bars. The IC of every flow family rises with the
forecast horizon out to 42 bars, and the book score peaks with formation windows of 63–108 bars,
collapsing outside. Three — **72, 81, 90** — are carried into the scored neighbourhood.

Holding horizons tested at **9, 21, 42, 54, 63, 72, 84, 90 and 126 bars** — 9 horizons, where the
playbook requires at least two. The print-size norm window was independently swept at **54, 72, 90,
108, 126, 144, 162 and 180 bars**, and sleeve width at **3, 4, 5 and 6** names per side.

Three holding horizons — **60, 72, 84** — are carried into the scored neighbourhood. **`hold=60` is
the one declared neighbourhood point that was never simulated offline**: the offline grid stepped
54 → 63, and 60 was chosen for the declaration because it is a material (−17%) variation of the
nominee that the grid happened to skip. It was scored for the first time by the organiser, in the
sweep. That is a deliberate choice — a neighbourhood entirely composed of points already known to
be good is a neighbourhood chosen to flatter the median — and it is disclosed here so the reader
can weigh it.

### 2.6 Rebalance phase: swept, and the reason the nominee has no phase axis

Phase was swept exhaustively offline: **429 full-window simulations covering every phase offset of
twelve (measure, window, cadence, k) configurations**, at cadences 9 / 21 / 42 / 63. This is the
single most important design fact in this certificate:

| configuration | cadence | offsets | G min | G max | G mean | 2× Sharpe min | 2× Sharpe max |
|---|---:|---:|---:|---:|---:|---:|---:|
| `bigp` w=90 k=6 | 42 | 42 | **0.00** | **86.40** | 44.33 | **−0.001** | **+1.364** |
| `perb` w=90 k=6 | 42 | 42 | 0.91 | 76.54 | 28.25 | +0.118 | +1.047 |
| `per` w=90 k=5 | 42 | 42 | 0.00 | 64.56 | 26.23 | −0.029 | +1.059 |
| `lvl` w=180 k=5 | 42 | 42 | 0.00 | 48.04 | 12.93 | −0.238 | +0.729 |
| `bigp` w=90 k=6 | 21 | 21 | 10.33 | 63.82 | 34.19 | +0.418 | +1.063 |
| `bigp` w=90 k=5 | 9 | 9 | 12.58 | 52.68 | 29.44 | +0.354 | +0.785 |

The same signal, the same window, the same width, differing only in which boundary the cadence
starts on, spans a 2×-cost Sharpe from **−0.001 to +1.364**. A cadence-42 result reported at one
phase is a result about that phase and nothing else.

The nominee therefore **does not choose a phase**. It holds `HOLD_BARS` overlapping sleeves, one
opened every boundary and each held `HOLD_BARS` boundaries, which is exactly the average over all
`HOLD_BARS` phase offsets. Its cadence is one bar, so the §7 phase-sweep requirement does not bind
on it, and it cannot be lucky in phase by construction. That construction is itself ablated on the
organiser's scorer — `ablation-single-phase`, §4.

### 2.7 Nominee selection: a plateau interior point, not the maximum

The best single offline point in the entire 3,353-simulation sweep was `bigp+imbsml` at
w=90 / hold=72 / k=3, offline G **88.88**. **That point was not nominated.** The nominee is
w=81 / hold=72 / k=4, which sits in the interior of the plateau rather than on its edge. The
declared neighbourhood's eight other points score offline G 86.1–88.0 — a genuinely flat surface,
which is what makes a median a meaningful score rather than a penalty.

---

## 3. Trials

**Nine accepted trials of twelve; three left unspent. `T = 2` charged against the multiplicity bar**
— amendment A6 exempts `falsification` and `ablation`, and the organiser's own header confirms it:
`9 of 12 trials spent, 7 exempt from multiplicity; T=2`.

| # | kind | candidate | question | charged |
|---:|---|---|---|:-:|
| 90 | point | `print-size-flow` | do the substance gates pass, and does the offline replica agree with the organiser? | yes |
| 91 | neighbourhood | `print-size-flow` | the declared 9-point plateau median — **the score** | yes |
| 92 | falsification | `print-size-flow` | exact sign inversion + gross-edge placebo | no |
| 93 | ablation | `ablation-imbalance-baseline` | transparent baseline: the obvious reading of the lane | no |
| 94 | ablation | `ablation-covats-only` | does the covariance term carry it alone? | no |
| 95 | ablation | `ablation-imbsml-only` | does the small-print imbalance carry it alone? | no |
| 96 | ablation | `ablation-equal-bar-weight` | is it print size, or just de-weighting the biggest bars? | no |
| 97 | ablation | `ablation-controls-off` | what do the three controls cost or buy? | no |
| 98 | ablation | `ablation-single-phase` | is the overlapping-sleeve construction load-bearing? | no |

No trial was wasted on a typo — `--check` was run before every one — and nothing was abandoned
mid-flight. Trial #90 was journaled before the candidate had a `neighbourhood.json`; adding one
changed the directory digest, so #91 and #92 carry the later digest `8031850e…`. That is the
material-tuple rule working as intended, not an error, and both are the digest on disk today.

---

## 4. Results

Every number below is the organiser's, read from the packets in `research/packets/`, with two
exceptions that are labelled offline where they appear (§4.3) and are not claimed as measurements.
The organiser's own workspace scan on each run recorded **no violations** — 82 files scanned on the
sweep, 78 on the last ablation, 45 on the point — which is the independent corroboration of §6's
account of the shim.

### 4.1 The score — the declared neighbourhood median (trial #91)

The nine declared points, each separately materialised and separately executed, 1912s of wall clock
across four workers:

| point | FORMATION / HOLD / NORM / SLEEVE | net Sharpe | 2× Sharpe | ann. return | max DD | trades |
|---|---|---:|---:|---:|---:|---:|
| **nominee** | 81 / 72 / 126 / 4 | 1.6379 | 1.4965 | 0.2074 | 0.0829 | 85,502 |
| point-1 | **72** / 72 / 126 / 4 | 1.7428 | 1.5946 | 0.2201 | 0.0869 | 86,701 |
| point-2 | **90** / 72 / 126 / 4 | 1.6425 | 1.5065 | 0.2102 | 0.0792 | 83,610 |
| point-3 | 81 / 72 / **108** / 4 | 1.7476 | 1.6051 | 0.2204 | 0.1041 | 85,422 |
| point-4 | 81 / 72 / **144** / 4 | 1.5623 | 1.4230 | 0.1953 | 0.0798 | 84,643 |
| point-5 | 81 / **60** / 126 / 4 | 1.5341 | 1.3857 | 0.1919 | 0.0829 | 83,307 |
| point-6 | 81 / **84** / 126 / 4 | 1.5819 | 1.4456 | 0.1990 | 0.0829 | 86,879 |
| point-7 | 81 / 72 / 126 / **3** | 1.6341 | 1.5031 | 0.2131 | 0.0765 | 76,665 |
| point-8 | 81 / 72 / 126 / **5** | 1.5533 | 1.4024 | 0.1909 | 0.0858 | 89,740 |

Net Sharpe spans **1.534 to 1.748** and maximum drawdown **0.0765 to 0.1041** across ±11% on the
formation window, ±14% on the norm window, −17%/+17% on the holding horizon and −25%/+25% on sleeve
width. That is the flat surface §2.7 said the nominee was chosen to sit in the interior of, measured
rather than asserted.

**`hold=60`, the one declared point never simulated offline (§2.5), came back the weakest of the
nine** — net Sharpe 1.5341, the lowest in the table — and still cleared every floor comfortably. The
disclosure in §2.5 was that declaring only points already known to be good would flatter the median;
the point that was not known landed at the bottom of the range and cost roughly 0.10 Sharpe against
the nominee. It did not change any verdict.

**The score is the per-metric median of that table.** Ranking score **G = 91.246**.

| median metric | value | floor | |
|---|---:|---|:-:|
| net_sharpe | 1.634065 | ≥ 0.8 | PASS |
| double_cost_sharpe | 1.496504 | ≥ 0.5 | PASS |
| triple_cost_sharpe | 1.354994 | > 0 | PASS |
| annualized_return | 0.207375 | > 0 | PASS |
| double_cost_annualized_return | 0.187156 | > 0 | PASS |
| max_drawdown | 0.082859 | ≤ 0.2 | PASS |
| annualized_volatility | 0.119065 | ≥ 0.06 | PASS |
| positive_quarter_fraction | 0.882353 | ≥ 0.5 | PASS |
| positive_fold_count | 4.000000 | ≥ 3 | PASS |
| worst_fold_sharpe | 0.615308 | ≥ −0.25 | PASS |
| annualized_turnover | 22.386397 | ≤ 25 | PASS |
| gross_edge_bps_per_turnover | 94.428374 | ≥ 40 | PASS |
| cost_share_of_positive_gross | 0.012312 | ≤ 0.3 | PASS |
| top5_day_share | 0.027914 | ≤ 0.35 | PASS |
| max_fold_positive_pnl_share | 0.279375 | ≤ 0.6 | PASS |
| trade_count | 85,422 | ≥ 500 | PASS |
| neighbourhood_positive_fraction | 1.000000 | ≥ 0.7 | PASS |
| trial_adjusted_confidence | 1.000000 | ≥ 0.9 | PASS |
| declared_roles_match_traded_sides | ['long','short'] = ['long','short'] | — | PASS |
| role_long_gross_pnl | 0.652388 | > 0 | PASS |
| role_short_gross_pnl | 0.172936 | > 0 | PASS |

**All 21 floors a sweep can measure pass.** The organiser reports this is the first submission in
this field to clear every one of them; that is the organiser's statement, not a claim this team can
verify from inside its own workspace, and it is recorded here as reported rather than as a finding.
The verdict line is `NO MEASURED FAILURE -- 1 gate(s) cannot be decided by a neighbourhood sweep`;
the single undecidable gate is `sign_inversion_not_profitable`, which is exactly what trial #92
decides in §4.2. Between the two trials every charter §7.3 gate is measured, and every one passes.

Nine of nine points have positive 1× return **and** positive 2× Sharpe, so
`positive_point_fraction = 1.0000` against a 0.7 floor. `B = 1.0000` as the median across points,
`T = 2`, trial-adjusted confidence **1.0000** — see §4.4, which is where that number is argued
against rather than for.

Two costed observations. **Cost share of positive gross is 0.0123** — the book pays about 1.2% of
its gross in fees and slippage, so the 3× stress removes roughly 0.28 Sharpe rather than the edge.
And **top-5-day share is 0.0279**: the largest five days account for under 3% of the total, against a
0.35 ceiling. Nothing here is one week in 2021.

The nominated point's own vector differs from the median in the expected direction and by little:
net Sharpe 1.6379 against the median's 1.6341, worst fold 0.6234 against 0.6153, short sleeve 0.1660
against 0.1729. Its fold Sharpes are F1 **0.623**, F2 1.983, F3 1.932, F4 1.756 — F1 (2020-08 to
2021-08) is by a distance the weakest year and is also the year the transparent baseline loses most
(§4.3). The median is the score; the point is not materially better than it.

### 4.2 The falsification battery (trial #92)

**Exact sign inversion.** Multiply the book by −1 and score it on the eight core floors:

| core floor | inverted | clears? |
|---|---:|:-:|
| net_sharpe | −2.0576 | fails |
| double_cost_sharpe | −2.1959 | fails |
| triple_cost_sharpe | −2.3341 | fails |
| annualized_return | −0.2241 | fails |
| double_cost_annualized_return | −0.2370 | fails |
| max_drawdown | 0.6468 | fails |
| annualized_volatility | 0.1198 | clears |
| trade_count | 85,501 | clears |

Six of eight fail. The two that clear are the two a sign flip cannot change: flipping the book leaves
the number of trades and the magnitude of the returns alone and only reverses their sign. The
inversion is not a marginal loser, it is a symmetric one — net Sharpe −2.058 against +1.638, drawdown
0.647 against 0.083 — which is the shape a real directional claim produces. `sign_inversion_passes_core = false`.
The gate the sweep could not decide is decided.

**Gross-edge placebo.** Eight permutations, seeds 18–25:

| | gross edge, bps per unit one-way turnover |
|---|---:|
| candidate | **94.14** |
| placebo min | −1.40 |
| placebo median | **−0.09** |
| placebo max | +1.45 |
| exceedance | **0.0000** |

**What that margin means.** The placebo preserves the weight multiset exactly — gross exposure, the
sizing distribution, the risk-scalar path and the rebalance schedule are all untouched — and
randomises only which eligible symbol receives which weight, redrawn at every boundary and drawn
over the full eligible set rather than shuffled within the names the candidate picked. Everything
about the book except *who* survives. The edge does not: 94.14 bps becomes a median of −0.09 bps, a
distribution straddling zero with a range of under 3 bps. The best of the eight reached **1.5%** of
the candidate's edge; the median reached less than nothing.

The reading is unambiguous and it is a strong constraint on what this book can be claimed to be.
**Essentially all of the gross edge is cross-sectional symbol selection. None of it is timing, none
of it is the sizing profile, and none of it is a schedule artifact.** A dollar-neutral book rebalanced
on this cadence with this weight distribution earns nothing at all unless the names are chosen; the
machinery is a pure amplifier of an attribution decision and contributes no edge of its own. That is
precisely and only what §2 claims: `rank(COVATS) + rank(IMBSML)`, residualised same-boundary, is a
statement about *which coins to be long and which to be short at this boundary* and about nothing
else. The mechanism claims a cross-sectional ordering; the placebo says a cross-sectional ordering
is all there is. Had a meaningful fraction of the edge survived the permutation, §2's account would
have been wrong regardless of the score, because the edge would then have been coming from
something the mechanism does not describe.

Two limits on that reading, stated because the result is otherwise flattering. First, the placebo
re-draws the attribution *every boundary*, so it destroys holding persistence at the same time as it
destroys name choice; the null is "which symbols, held how long, jointly" rather than name selection
in isolation. It is a broad null, and a broad null passed is weaker evidence per unit of drama than
a narrow one. Second, and more important, **a permutation test cannot say which cross-sectional
signal produced the ordering.** It establishes that the book earns by selecting names; it does not
establish that it selects them on taker-flow print structure. Only the ablations can do that, which
is why §4.3 is the load-bearing section of this certificate and not this one.

### 4.3 The ablation programme — six controls, in one place

Six ablations were journaled, each the frozen nominee with **exactly one thing changed**
(`research/make_ablations.py` generates them from the nominee's own source; every one carries the
identical universe, book shape, parameters, risk policy and seed). Amendment A6 exempted all six
from the multiplicity charge, which is the only reason a programme this size was affordable — at
1 charged trial each this would have cost half the budget and the nomination would have been scored
at `T = 8`.

| # | ablation — the one change | G | net Sharpe | 2× | max DD | worst fold | short sleeve | verdict |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 90 | *(nominee, for reference)* | **90.68** | 1.638 | 1.497 | 0.0829 | +0.623 | +0.166 | no measured failure |
| 93 | plain USDT-weighted imbalance, no print-size conditioning at all | **−16.90** | 0.569 | 0.438 | 0.2466 | **−1.348** | **−0.003** | **fails 8 floors** |
| 94 | covariance term only; conditioned imbalance removed | **69.42** | 1.433 | 1.275 | 0.1277 | +0.274 | +0.115 | no measured failure |
| 95 | conditioned imbalance only; covariance removed | **8.21** | 0.462 | 0.326 | 0.1165 | **−0.349** | **−0.232** | **fails 7 floors** |
| 96 | equal-bar-weight imbalance — de-weights big bars *without* print size | **74.46** | 1.660 | 1.521 | 0.1415 | +0.490 | +0.224 | no measured failure |
| 97 | controls off — no residualisation | *(offline only, below)* | | | | | | |
| 98 | one cadence-72 sleeve at a single phase | *(offline only, below)* | | | | | | |

Floors failed: #93 — `net_sharpe`, `double_cost_sharpe`, `max_drawdown`, `positive_fold_count`,
`worst_fold_sharpe`, `gross_edge_bps_per_turnover`, `trial_adjusted_confidence`,
`role_short_gross_pnl`. #95 — the same list without `max_drawdown`.

**#93, the transparent baseline, at −16.9.** The obvious reading of this lane, through machinery
identical to the nominee's down to the three controls and the overlapping sleeves, is not a weaker
book — it is a failing one. Two folds negative, worst fold −1.35, drawdown 0.247, gross edge 39.8
bps against a 40 floor, and a **gross-negative short sleeve** (−0.003): ranking by plain taker
imbalance produces a short book that loses money before costs. §5.2 recorded that this measure has a
genuine positive pooled IC. It does, and it is worth −16.9.

**This is also the strongest thing the ablation set establishes, and it is a structural argument
rather than a numerical one.** All five organiser-measured books share the same universe, the same
dollar-neutral construction, the same three controls, the same overlapping-sleeve averaging, the
same risk scalar, the same costs and the same seed. Everything except the flow measure is held
fixed. Those five books score **−16.9, 8.2, 69.4, 74.5 and 90.7**. A common component — the size and
turnover controls, the construction, or the residual −0.091 volatility tilt disclosed in §2.4 and
flagged in §5.8 — cannot produce a 107-point spread while holding still. Whatever this book earns,
it earns from the flow measure, because the machinery's own floor is a failing book. That is the
answer to §5.8's open question, and it is indirect: it rules out the shared components as *the*
earner without quantifying what the retained volatility tilt contributes on its own. The trial that
would have quantified it is #97, which has no number (below).

**#94 and #95 — which half carries it.** The covariance term alone clears every measured floor
(G 69.4, four positive folds, worst fold +0.274, short sleeve +0.115). The conditioned imbalance
alone does not come close (G 8.2, two positive folds, worst fold −0.349, short sleeve −0.232, seven
floors failed). **`COVATS` is the load-bearing term and `IMBSML` is not a book on its own** — yet
combining them moves the score from 69.4 to 90.7, a gain of 21 points from a term that scores 8.2
standalone. `IMBSML` is a complement, not a duplicate: it contributes nothing alone and roughly a
fifth of the final score in combination, and what it visibly repairs is the fold profile (worst fold
0.274 → 0.623) and the drawdown (0.1277 → 0.0829). The mechanism, stated exactly, is *the
print-size/direction covariance, sharpened by the granular half of the tape*.

Note that this **inverts the pooled-IC ranking for the second time in this certificate.** §2.2
measured `IMBSML` as the strongest single measure in the flow family, roughly twice as informative
as its large-print counterpart at every horizon. On the organiser's scorer it is the half that
cannot stand up. Pooled IC ranked the terms in the opposite order to the book, twice, in the same
lane. That is a methodological finding about this window and it is more transferable than the book.

**#96, equal-bar-weight — the honest one.** This is the ablation §2.2 promised would be run on the
organiser's scorer rather than argued from IC, because pooled IC said the print-size conditioning
was unnecessary. The result does not vindicate the print-size conditioning on the terms a reader
would expect:

| | nominee | equal-bar-weight |
|---|---:|---:|
| net Sharpe | 1.638 | **1.660** |
| 2× Sharpe | 1.497 | **1.521** |
| gross edge (bps) | 94.14 | **96.53** |
| short sleeve | 0.166 | **0.224** |
| **max drawdown** | **0.0829** | 0.1415 |
| **worst fold Sharpe** | **+0.623** | +0.490 |
| G | **90.68** | 74.46 |

**On return quality the print-size conditioning is not needed.** Equal-bar weighting is marginally
better on Sharpe at every cost level, better on gross edge, and better on the short sleeve, and it
clears every measured floor. What print size buys is entirely **risk shape**: a 41% smaller maximum
drawdown and a materially better worst fold, worth 16 points of G under a scorer that weights
drawdown and fold consistency. §2.2 predicted exactly this — "the print-size version's errors are
less concentrated in fold and drawdown" — and it is confirmed, but a reader should record that if
the objective had been Sharpe alone, this ablation would have beaten the nominee and the print-size
mechanism would have been surplus. The lane's headline claim survives on drawdown, not on edge.

**#97 and #98 — no organiser number exists, and this is not reconstructed.** Both trials are
journaled and accepted (sequences 97 and 98, `research/packets/` has no file for either). Both were
killed by the organiser defect in §6 before trial resolution; only #91 and #92 were re-run
organiser-side afterwards, and re-running these two would spend nothing but is not permitted now
that the nominee is frozen. **The numbers below are the offline simulator's, from the committed
`research/ablation_offline.csv`, and they are not measurements.** §1 established the simulator
misranked the transparent baseline by 26 points in the optimistic direction and runs 7 points *under*
the organiser on the nominee — it compresses the range and cannot be trusted to settle anything.
They are reported because the artifact is durable and the alternative is silence:

| | offline G | offline net Sharpe | offline max DD | offline worst fold | offline trades |
|---|---:|---:|---:|---:|---:|
| nominee, offline, for scale | 83.43 | 1.714 | 0.0830 | +0.616 | 80,539 |
| #97 controls off | 84.17 | 1.623 | 0.0897 | +0.694 | 76,285 |
| #98 single phase, offset 0 | 42.12 | 1.163 | 0.1303 | **−0.408** | 34,186 |

The offline reading — offered as an indication and nothing more — is that the three controls are
roughly score-neutral on this window and that the overlapping-sleeve construction is worth about
half the score. Neither is established. **The controls stay in on the §2.4 argument, which is a lane
argument and not a score argument**: leaving a size and turnover tilt uncontrolled would let a size
premium carry a book nominated for a taker-flow lane, and that would be true even if removing them
raised the score. The single-phase question is worse served: offset 0 is *one draw* from the phase
distribution §2.6 measured across 42 offsets, where the same configuration spanned G 0.00 to 86.40.
A single-phase ablation at one offset is itself a phase-lottery ticket, so even the organiser number,
had it survived, would have been one sample from that distribution rather than a verdict on the
construction. §2.6's 429-simulation phase sweep remains the evidence for the overlapping-sleeve
design, and it is offline evidence.

**What the six establish, and what they do not.** They establish that the machinery does not carry
the book (the shared-component floor is −16.9); that the covariance between print-size shock and
flow direction is the load-bearing term; that the conditioned imbalance is a genuine complement
worth ~21 G points despite being worthless alone; and that the print-size conditioning's contribution
is specifically to drawdown and fold consistency rather than to edge. They do not establish what the
controls contribute, they do not quantify the retained volatility tilt directly, and they leave the
overlapping-sleeve construction argued from offline evidence only. Four of six landed. The
certificate is as strong as those four and no stronger.

### 4.4 `B = 1.0000` — why this is not a victory lap

Every one of 2,000 circular-block resamples of the nominee's 1× daily return stream, drawn in 10-day
blocks, came back with a positive mean. The median across the nine neighbourhood points is 1.0000
and the trial-adjusted confidence, after the `T = 2` multiplicity charge, is 1.0000 against a 0.9
floor.

**What that establishes.** Only this: given this realised daily return stream, the sign of its mean
is not an artifact of the ordering of a handful of 10-day windows. It is a statement about the
robustness of one sample's mean to resampling, and it is the weakest of the four claims in this
section.

**What it does not establish, and why the number should be read down rather than up.**

*It is at the resolution limit of its own estimator.* 2,000 draws cannot distinguish 1.0000 from
0.9995. The evidence is in this team's own sweep: three of the nine points came back at 0.9995,
0.9995 and 0.9990 — one or two negative resamples each — on books that differ from the nominee by
one parameter step. The nominee's true positive fraction is somewhere near, and below, 1. Reported to
four decimals, `1.0000` reads as certainty and means "fewer than one draw in two thousand".

*The block length is shorter than the holding horizon.* `HOLD_BARS = 72` at 8h is a **24-day**
holding period; the bootstrap block is **10 days**. The dependence the overlapping sleeves induce in
the daily return stream extends beyond the block, so resampling in 10-day blocks breaks
autocorrelation the book actually has and understates the variance of the mean. The direction of
that error is toward a *higher* positive fraction. This is the concrete reason to distrust the
number, and it applies to the whole neighbourhood since every point holds for 60–84 bars.

*It cannot see the selection that produced the book.* The resampler is handed the return stream of
one already-chosen configuration. It knows nothing about the ~3,700 offline simulations, the 90
candidate measures or the 403 IC evaluations that preceded the choice (§1). `T = 2` charges the two
trials the charter counts; it does not and cannot charge the offline search. A book selected as the
best of a large offline sweep will have a flattering bootstrap almost by construction, and this one
was.

*It is one window and one regime.* 2020-08 to 2024-08 is a single four-year path. The bootstrap
resamples within it and can never sample outside it. F1's Sharpe of 0.623 against F2–F4's 1.76–1.98
is the visible warning: the book's worst year is already a factor of three below its best, and a
resampler drawing from all four folds pooled will not reproduce a run of F1-like years.

**What would make me doubt it.** A bootstrap run at a block length of 24 days or longer — matching
the holding horizon — returning materially below 1.0. A fifth fold, out of this window, with a
Sharpe near or below F1's 0.623. Or a forward period in which the short sleeve, which contributes
0.173 gross against the long sleeve's 0.652 and goes gross-negative in two of the four measured
ablations, stops paying. None of those has been run. `B = 1.0000` is consistent with a real edge; it is not
evidence of one beyond what §4.2 and §4.3 already carry, and nothing in this certificate should be
read as resting on it.

---

## 5. Failures, dead ends and things that did not work

This section is the point of the certificate. Most of what follows was established offline, at no
trial cost; where a finding was confirmed on the organiser's scorer the journal sequence is cited.

**5.1 The stated prior was falsified (offline, then trial #94/#95).** Large prints were expected to
be the informed ones. They are the *less* informative half at every horizon tested (§2.2), and as a
standalone book `imbbig` reached a best offline G of only 26.4 with a worst fold of **−1.862**. The
mechanism that was eventually nominated is the inverse of the one that was predicted. This is
recorded as a falsified prior rather than a pivot: the axis — *print structure conditions the
meaning of flow* — never changed, only the sign of the conditioning.

**5.2 The obvious reading of the lane fails as a book, despite a real IC (trial #93).** Plain taker
imbalance has a genuine positive raw cross-sectional IC (+0.057 at h=21, t = 3.78, positive in all
four folds). It is nonetheless close to worthless as a book: G **−16.9**, eight hard floors failed,
worst fold −1.35, max drawdown 0.247, and a **gross-negative short sleeve**. A positive pooled IC
does not make a tradeable book, and this is the cleanest demonstration of that in this work.

**5.3 The flow-residual reading added nothing.** One of the more promising non-obvious readings —
"the informative quantity is the residual after removing the price move the flow *should* have
caused" — was built (`residflow_*`, `residflowint_*`) and tested. Its IC is statistically
indistinguishable from the plain level it was supposed to improve on: **+0.0833 vs +0.0822** at
w=90/h=42, and the pattern holds at every window. At 8h aggregation, flow and the move it
accompanied are not separable in the way the idea requires. **This is a null result and it is
reported as one.**

**5.4 Trade count is the weakest of the three activity fields.** Covarying imbalance with the
trade-count shock (`covnt`, best offline G 32.3) is much worse than covarying it with the print-size
shock (`covats`/`bigp`, 67.4 / 86.4), with quote-volume shock in between (54.2). The mandate's
question "does imbalance mean something different when trade count is high?" has an answer here:
only through the print size it implies, not on its own.

**5.5 Normalising the covariance by its own dispersion hurt.** `covatsn` — the scale-free variant,
dividing by the window's shock dispersion — scored 50.0 against `covats`'s 67.4. Removing the
magnitude of the print-size shock removed information.

**5.6 A missing-data rule was doing the work of a mechanism, and was removed.** An earlier draft
required at least `FORMATION_BARS / 6` qualifying bars before `IMBSML` was defined. That left the
measure undefined on about **9% of eligible symbol-boundaries**, concentrated precisely in the
print-size regime shifts the measure exists to detect, and handed those cases to whatever the
missing-component policy happened to be. That policy accounted for roughly **thirty points of
offline ranking score** — a rule, not a mechanism. The guard was deleted; the measure is now defined
almost everywhere, the score is nearly indifferent to the missing-component policy, and the book
improved. The comment recording this is in the frozen `strategy.py`.

**5.7 Equal-bar weighting matches the mechanism on IC and not in the book.** Disclosed in full at
§2.2. Had only IC been consulted, the print-size conditioning would have looked unnecessary.

**5.8 Realised volatility beat every flow measure found, and is not what is nominated.** The single
strongest raw cross-sectional predictor in the entire EDA is 90-bar realised volatility (raw IC
−0.129 at h=21, t = −7.15) — not a taker-flow measure at all. It would have been easy, and
lane-violating, to nominate it. The residual score retains −0.091 of it (§2.4); the ablations in §4
are what establish the book is not simply earning that.

**5.9 Single-phase cadence books were abandoned entirely.** Every cadence > 1 configuration proved
to be a statement about its phase offset rather than about its cadence (§2.6). Rather than pick a
phase and report it, the design was changed to average over all of them.

**5.10 Nothing was abandoned mid-flight and no trial was lost.** Three of twelve trials are
unspent. No trial was spent on a typo, and no evaluation had to be re-run for a mistake — the two
re-runs that did occur were caused by the organiser defect in §6 and cost no trial, exactly as the
playbook says they should not.

### 5.11 Role checks: long, short and chop

The organiser measures the long and short roles directly and both are gross-positive at the nominee
(§4). The playbook also asks for a chop check, which the harness does not provide, so it was done
offline in `research/regime.py` — using a regime definition built **only from this team's own data
root**, since the organiser's own regime series is not readable from here. Boundaries are split at
the terciles of the trailing 90-bar absolute t-statistic of the eligible equal-weight basket's
drift, measured strictly before each boundary: low = chop, high = trending.

| regime (tercile of trailing trend strength) | bars | net PnL (1×) | Sharpe | max DD |
|---|---:|---:|---:|---:|
| **CHOP** (weakest third) | 1,430 | +0.2346 | **1.014** | 0.0588 |
| MID (middle third) | 1,430 | +0.3389 | 1.341 | 0.0653 |
| **TREND** (strongest third) | 1,430 | +0.1525 | **0.537** | 0.0729 |

The book is profitable in all three regimes and earns **more** in chop than in trend. A
dollar-neutral book that was secretly a market-direction bet would show the opposite. The two
sleeves are complementary across the split: the short sleeve carries the chop third while the long
sleeve carries the middle and trending thirds.

---

## 6. Organiser defect report

**D-09-1 — `scripts/cup20_evaluate.py` is broken for every scored mode. Blocking, and it will hit
every team that has not yet run.**

`scripts/cup20_evaluate.py` calls `kind_for_mode(...)` at line 186 but never imports it. Every
scored mode — point, ablation, neighbourhood, falsification — dies with

```
NameError: name 'kind_for_mode' is not defined
```

immediately after the snapshot loads and immediately *before* the accepted trial is resolved. Only
`--check` returns early enough to survive, which is why the defect is invisible until a team spends
its first trial and tries to use it.

The function exists and is correct: it is defined at `src/crypto_trade/cup20/trials.py:595` and
exported from `crypto_trade.cup20.__init__`. **Only the import line is missing** — the
`from crypto_trade.cup20.trials import (...)` block in the script lists seven names and not this
one. The fix is one line in that import block.

*How this team proceeded, and why it is not a rule violation.* A team may write only under its own
directory, so editing an organiser file — and in particular editing the harness a team is scored by
— was not an option and must never be allowed to happen quietly. `research/run_evaluate.py` instead
loads the organiser's own script as a module, binds the missing name to the organiser's own function
imported from the organiser's own module, and calls the organiser's own `main()` with the arguments
unchanged. Nothing outside this team's directory is touched, and no configuration, scoring rule,
floor, journal record or number is affected. Every number in §4 is produced by unmodified organiser
code, running under the organiser's own trial resolution, and each run's header confirms the trial
it resolved.

*Cost.* No trial. The failed invocations died before trial resolution, and re-running under the shim
resolved the already-accepted trials, exactly as the playbook's "a killed evaluation does not burn
its trial" provision describes.

**D-09-2 — a note, not a defect.** The playbook's §5.5 worked as documented throughout, and the
`--check` mode caught every declaration error before a trial was spent, including the neighbourhood
substitution dry-run. The A6 exemption is correctly implemented: the header reports
`9 of 12 trials spent, 7 exempt from multiplicity; T=2`, and the six ablations plus the falsification
battery cost this candidate nothing on the multiplicity bar. Without A6 this certificate's ablation
programme would not have been affordable, and §4 would be a much weaker document.
