# team-10 research log — volatility-regime risk-on / risk-off timing

Chronological. Offline work only unless a journal sequence number is quoted; a sequence number
means the organiser's harness produced the number and the trial is on the record.

## 0. Infrastructure

- `panel.py` — aligned (time × symbol) matrices on the 8h decision grid from `data/cup20/is/`.
  IS_START is computed, not chosen: 2020-08-17, the first reconstitution reaching 20 names. Grid
  is 4335 boundaries × 62 symbols ever; 4329 of 4335 boundaries carry exactly 20 eligible names,
  six carry 13. BTC and ETH are eligible at every boundary.
- `signals.py` — causal regime measures. Row `t` of every measure uses only bars closed by `t`.
  In panel coordinates bar `i` opens at `grid[i]` and closes at `grid[i+1]`, so the last visible
  bar at decision `t` is `i = t-1`; the shift is applied once, centrally, in `_causal`. This was
  checked against the harness's own truncation rule
  (`searchsorted(open_time + interval, decision_time, side="right")`), which admits bar `i` iff
  `i <= t-1`. The measures are therefore exactly as informed as the harness allows, and no more.
- `fastsim.py` — a fast replica of the organiser's two-pass evaluator.
- `book.py` — regime state → weights. Net exposure is the only exposure dial a weights-only
  protocol has, because the evaluator renormalises every rebalance row to unit gross.
- `runner_mp.py` — parallel driver.

### Simulator calibration (offline, no trial, no tournament number)

The fast simulator was calibrated against the organiser's OWN modules — `cup20.runner.run_candidate`
and `cup20.metrics.window_metrics` — imported and run in-process on an equal-weight long book over
the full window. This produces no journal entry and is not a scored evaluation; it exists only to
measure how far the replica sits from the real pipeline.

| metric | organiser | fastsim | difference |
|---|---:|---:|---:|
| Sharpe 2× | 0.173034 | 0.174380 | 0.0013 |
| Sharpe 3× | 0.156423 | 0.157800 | 0.0014 |
| annualised return 2× | 0.012005 | 0.012340 | 0.0003 |
| annualised volatility | 0.243096 | 0.243110 | 0.00001 |
| max drawdown 2× | 0.318803 | 0.318800 | 0.000003 |
| annualised turnover | 5.3797 | 5.3736 | 0.006 |
| trade count | 91 984 | 91 930 | 54 |
| fold Sharpes 2× | 0.4015 / −0.4224 / −0.3052 / 1.0145 | 0.4055 / −0.4225 / −0.3073 / 1.0145 | ≤ 0.004 |
| mean risk-unit scalar | 0.251714 | 0.251714 | exact |

Every offline number below is from the replica and is labelled as such. No offline number is
reported as a measurement.

## 1. The untimed base book

Equal-weight long the eligible universe, rebalanced every boundary. This is the "identical book
with the timing layer disabled" that my mandate makes the centre of gravity.

Sharpe 0.191 (1×), maxDD 0.318, realised volatility 0.243, folds **+0.41 / −0.42 / −0.31 / +1.01**
(2 of 4 positive), turnover 5.37×, 91 930 trades. The common risk unit pins it at `s_t = 0.20`
(the floor of the clamp) at almost every boundary, because a top-20 crypto basket realises ~97%
annualised volatility against a 10% target — so the book executes at 0.20 gross and still realises
24% volatility. It fails the 0.80 Sharpe floor, the 0.20 drawdown floor and the 3-of-4 fold floor.

That matters for how this lane should be read: on this window the base book is a poor book, so a
timing layer has a great deal of room. The honest question is not whether timing helps — it is
whether a **causal** regime signal helps more than a random gate that is flat for the same
fraction of the window.

## 2. IC study over 412 regime measures (offline)

Six channels: level, term structure, cross-sectional dispersion, correlation to BTC, asymmetry
(downside share of realised variance) and time-aggregation (variance ratios), each at 13 formation
windows, plus trailing z-scored variants at three baseline windows. Forward target: the
open-to-open equal-weight market return at 1 / 3 / 9 / 21 / 45 / 90 / 135 bars.

Headline: **the information is at long horizons and it is weak at short ones.** Nothing reaches
|IC| 0.06 at one bar. The largest full-window rank ICs are at 90–135 bars (30–45 days):
`vr:6,180` +0.35, `rangeratio:270` +0.33, `rvbtc:180|z360` +0.33, `btccorr:360` −0.26.

Effective sample size is the thing to state, not the IC: at a 90-bar horizon 4335 overlapping rows
carry about 48 independent observations, so an IC of 0.33 is roughly two standard errors. This is
why the certificate's evidence rests on the matched-selectivity null and on fold consistency
rather than on an IC table.

Per-fold sign stability (four folds, IC measured inside each): only `rvbtc:45|z360` and the
variance ratios keep one sign in all four folds at 21/45/90 bars.

## 3. Broad configuration sweep (offline, 9 016 full-window simulations)

46 measures × 2 signs × 7 thresholds × {long-flat, long-short} × 7 cadence/phase combinations.
Ranked by the **median** G across each family's whole grid rather than by its maximum, because the
maximum of a 9 016-point search is not evidence.

Best families by median G: `vov:3,180` (−, long-flat) 27.5 · `rvbtc:45` (+, long-flat) 24.9 ·
`rangeratio:90` (−, long-flat) 23.6 · `vr:21,360` (+) 22.4 · `vov:9,180` (−) 21.1 ·
`semi:90` (−) 20.3 · `corr:270` (+) 19.9.

Long-flat beat long-short in almost every family: the short leg does not earn.

## 4. The matched-selectivity null — the test that separates timing from hindsight

For a gate that is risk-on a fraction `f` of the window with `s` switches, the null keeps the gate's
**run-length structure and on-fraction exactly** and randomises only *when* the risk-off spells
fall. 150 draws per configuration.

| configuration | real G | null median G | null max G | G exceedance | Sharpe exceedance |
|---|---:|---:|---:|---:|---:|
| `vov:3,180` (−) | 82.66 | −13.86 | 61.71 | **0.0000** | 0.0000 |
| `semi:90` (−) | 77.81 | −21.45 | 75.17 | **0.0000** | 0.0000 |
| `rangeratio:90` (−) | 78.63 | −8.48 | 69.37 | **0.0000** | 0.0067 |
| `rvbtc:45` (+) | 73.43 | −3.82 | 59.70 | **0.0000** | 0.0800 |
| `vov:9,180` (−) | 66.78 | −16.95 | 43.45 | **0.0000** | 0.0000 |
| **`rv:45` — the plain volatility-level gate** | **−6.19** | −13.01 | 72.16 | **0.3933** | 0.4267 |

The last row is the result this lane was asked for. A gate built on the **level** of realised
volatility is not distinguishable from a random gate that is flat for the same fraction of the
window: 39% of matched random gates scored at least as well, and 43% earned at least as much
Sharpe. The obvious reading of my mandate does not survive its own null.

Note also what the null teaches about the base book: a *random* long-flat gate lifts Sharpe from
0.19 to a median 0.26–0.53 purely by being out of the market part of the time. Any claim about a
timing layer that is not measured against this null is measuring that mechanical effect.

## 5. Direction-blindness — staying inside the lane

Rank correlation of each measure with the trailing market return (what a momentum lane would use):

| measure | |ρ| max over 9/21/45/90/180-bar trailing returns |
|---|---:|
| `rv:90` | 0.087 |
| `rangeratio:180` | 0.104 |
| `rvbtc:45` | 0.156 |
| `rangeratio:90` | 0.225 |
| `vov:3,180` | 0.288 |
| `dispratio:90` | 0.553 |
| `semi:90` | 0.594 |
| `semi:45` | 0.755 |

`semi` — the downside share of realised variance — is a trailing-return signal wearing a variance
decomposition, and `dispratio` is nearly as bad. Both were dropped despite scoring well: a
candidate better described by team 01's or team 03's mandate than by mine is drift, and drift into
an occupied lane is the one collision that matters.

## 6. Two bugs found by transcribing the strategy — both before any trial was spent

**(a) A cumulative sum poisoned by one NaN.** `exact.vov_z` ran `cumsum` over a series whose first
element was NaN, which makes every partial sum after it NaN; a `sd > 0` guard then fell through to a
constant `0.0`, and the resulting book was always-long or always-flat. It did not look like a bug —
it looked like a bad result. Root cause: the panel starts at IS_START, but the bar that closes at
the FIRST decision opened before it. The strategy sees that bar (every symbol's frame carries its
whole history) and the replica did not. Fixed by reading the prior close from the bar file; the
silent fallback is now a raise.

**(b) A "flat" state that traded.** `build_weights` mapped a regime state of 0 onto the achievable
net-exposure ladder, where zero net means half the universe long and half short — split in
eligibility order, i.e. alphabetically. Every "long-flat" sweep before this point was measuring a
book that took an arbitrary cross-sectional bet whenever the signal said "no exposure". Found by
transcribing the frozen strategy and comparing books. The corrected long/flat book turned out
BETTER and cleaner (4/4 folds at every phase rather than at some), so only time was lost. `mode`
now defaults to `onoff`.

**Transcription proof.** The frozen `strategy.py` run through the organiser's `generate_targets` on
the real snapshot, compared boundary-by-boundary with the replica: rebalance flags identical at all
4335 boundaries, 1758 risk-on boundaries in both, max weight difference 1.4e-17.

## 7. Final measured results (organiser harness)

| journal | run | Sharpe 1x | maxDD | folds + | G |
|---|---|---:|---:|---:|---:|
| #101 | nominee, own point | 1.087 | 0.189 | 4/4 | 47.56 |
| #102 | **nominee, neighbourhood median — THE SCORE** | **1.063** | **0.192** | **4/4** | **44.297** |
| #103 | untimed base book | 0.467 | 0.272 | 2/4 | −10.03 |
| #104 | volatility-LEVEL gate (the obvious reading) | 0.631 | 0.169 | 3/4 | +5.19 |
| #105 | matched random gate, reads no data | 0.096 | 0.258 | 1/4 | −17.19 |
| #106 | untimed + declared drawdown brake | 0.427 | 0.275 | 2/4 | −8.80 |
| #107 | price-trend gate at matched selectivity | 0.728 | 0.228 | 3/4 | −1.31 |
| #108 | falsification: inversion fails 6 of 8 core floors; placebo exceedance 1.0000 (no-op) | | | | |
| #109 | trend gate AND vol-of-vol gate | 1.281 | 0.140 | 4/4 | +63.75 |

Replica error, measured out of sample against #102: predicted G 44.29 / median Sharpe 1.063 against
the harness's 44.297 / 1.063348.
