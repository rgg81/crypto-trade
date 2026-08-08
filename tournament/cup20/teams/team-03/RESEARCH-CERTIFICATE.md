# Team 03 — Research Certificate

Lane: `trend-quality-gated-momentum`. Data root: `data/cup20/is/`, and nothing else.
Trials accepted: **9** (journal sequences 21–29). Trials remaining unspent: 3.

## Outcome: NO NOMINATION

The mechanism is real. The gate-removal ablation is as decisive as an ablation gets: taking the
run-structure gate out of the full stack and changing nothing else drops net Sharpe from 1.018 to
0.347, gross edge per unit turnover from 53.0 bps to 26.3 bps, and turns the short sleeve negative
— nine hard floors flip from passing to failing on that one switch (#21 vs #22). The falsification
battery (#28) agrees from the other side: the exact sign inversion fails six of eight core floors,
and eight placebo books that keep the weight multiset and rebalance schedule but randomise which
symbol gets which weight reach a median gross edge of 5.7 bps per unit turnover against the
candidate's 67.5, with zero exceedance.

The book the mechanism produces still cannot satisfy the charter's conjunctive floors. The binding
pair is **annualised turnover ≤ 25×** and **trial-adjusted confidence ≥ 0.90**, and they pull in
opposite directions along the only axis that moves either of them. The best configuration found
(#23) clears nineteen of the twenty measurable gates with net Sharpe 1.130 and turnover 24.34,
failing only worst-fold Sharpe (−0.385 against −0.25) — and it clears trial-adjusted confidence in
its own packet only because that packet was printed at T = 3. At the tournament's own minimum trial
count of eight the same B = 0.9855 gives 0.884 against a floor of 0.90, so a nomination would have
turned a passing gate into a second failing one. Slowing the
book further to fix the fold breaks the quarter, fold-count and short-sleeve floors instead (#29).
No point on the cadence ladder clears everything, and the gap in confidence is not a rounding
error: it needs an in-sample Sharpe near 1.17 on a *neighbourhood median*, against a best single
point of 1.13.

Nominating anyway would mean nominating a candidate I know fails a hard floor, and would have cost
two further trials that raise the same bar. Section 8 of the playbook is explicit that a negative
candidate is evidence and not a submission, so this is the submission.

---

## 1. The thesis, and the falsifier posed before testing it

Two coins can post the same trailing return by completely different paths. The economic story
committed to before any number was read:

> On the twenty most liquid perpetuals a multi-day displacement of a given size arrives one of two
> ways. Either many consecutive eight-hour sessions of one-sided flow — slow leverage accumulation,
> funding and basis pulling the same way, the reflexive regime that keeps going — or one or two
> violent impulses (a liquidation cascade, a single repricing headline) around otherwise two-sided
> flow. The first has flow behind it that has not finished; the second has already spent itself.
> The endpoint return cannot tell them apart. The structure of the path can.

Three predictions were written into `research/eda_gate.py` before it was run.

**P1 — continuation rises with the efficiency ratio. FALSIFIED as posed, and this is the most
important negative result here.** The efficiency ratio (net displacement ÷ path length) is not a
distinct reading of the path at all. Across every formation tested (15, 21, 27, 33, 45, 63 bars) its
correlation with the absolute vol-normalised momentum `|z| = |Σx| / (s√N)` is **0.980–0.986**
(`research/eda_gates_compare.py`). Gating on ER and gating on `|z|` at matched selectivity produce
books that agree within noise: 44.9 vs 42.1 bps of continuation per unit gross at 60% retention,
54.6 vs 52.3 at 45%, 58.7 vs 62.3 at 35%. The reason is arithmetic and should have been anticipated
— for steps that are not extremely heavy-tailed `Σ|x|` and `s√N` differ by roughly a constant, so ER
is a monotone transform of risk-adjusted magnitude. **An efficiency-ratio gate is a magnitude gate
wearing a path-quality name.** Had the lane been implemented from its own headline statistic, the
candidate's mechanism would not have been the one in the mandate.

**P3 — at fixed momentum, a high single-bar jump share predicts weaker continuation. FALSIFIED
outright at the horizons that matter.** Selecting on a *low* jump share destroyed the edge at every
short formation — 8.6 bps at N=15 against 44.9 bps for the same retention on the run gate, and
negative in several folds. It only becomes weakly informative at N ≥ 63. The "one big candle is a
cascade that retraces" half of the story is simply not true on this universe at these horizons.

**P2 and the surviving reading.** Sign persistence — the fraction of formation bars whose own step
agreed with the net direction — is scale-free, depends on the order and sign of increments rather
than their sizes, and correlates with `|z|` at only **0.50–0.54**. It is the one path statistic
tested that magnitude cannot already express, and it is what the mandate names by "run length and
persistence statistics". The evidence is a double sort (`research/eda_persistence.py`), continuation
over the next 21 bars in bps per name, split by `|z|` tertile within each persistence half:

| formation | low-persistence half (\|z\| low / mid / high) | high-persistence half (\|z\| low / mid / high) |
|---|---|---|
| 18 | −24.9 / −1.1 / −3.0 | +31.5 / +47.8 / +61.6 |
| 21 | −24.2 / +1.6 / −0.6 | +50.1 / +58.0 / +65.8 |
| 24 | −38.1 / −8.0 / +43.0 | +73.7 / +75.3 / +44.9 |
| 27 | −28.4 / +9.9 / +36.3 | +56.0 / +70.2 / +60.3 |
| 30 | −24.5 / −15.2 / +54.9 | +45.7 / +75.9 / +54.6 |
| 36 | −12.7 / −2.6 / +12.3 | +68.4 / +91.9 / +50.5 |

In every magnitude tertile at every formation, the high-persistence half continues and the
low-persistence half does not — including in the *largest* momentum tertile, which is P2 confirmed
in the direction that matters. This table is the mandate's claim stated as data, and it is what the
candidate was built on.

**Standardising the gate.** A fixed *fraction* threshold is a different test at every window length,
because under a coin-flip null the agreeing fraction concentrates as √N: "62% of bars agreed"
selects the top ~30% of readings at N=15 and the top ~5% at N=45. Moving the formation therefore
silently moves the selectivity — which is exactly what made the formation axis look so violent in
`research/eda_final_scout.py` (IR 1.16 at N=15, 0.55 at N=26, −0.48 at N=45; an artifact of the
threshold, not of the horizon). The invariant form used throughout is

```
z = (2 · agreeing_fraction − 1) · sqrt(FORMATION_BARS)      admit when z ≥ PERSISTENCE_Z_FLOOR
```

Selectivity then stays near-constant across horizons (`research/eda_zgate.py`: 4–12% of member-bar
readings admitted at every N from 9 to 45), and the surface flattens: **312 of 315 grid points over
formation × z × smoothing × damping had a positive gross information ratio.**

---

## 2. Disclosure — what was computed privately, and what was not

The playbook is unambiguous that the two organiser commands are the only scorer. Every result and
every floor verdict in this certificate comes from `scripts/cup20_evaluate.py`. Design decisions,
however, were made offline on `data/cup20/is/`, and presenting the candidate as though they were
not would be dishonest. Exactly what `research/` computes:

- conditional forward gross log returns, information coefficients, hit rates and gate coverage
  (`eda_gate.py`, `eda_gates_compare.py`, `eda_persistence.py`);
- mechanical properties of our own emitted weight stream — one-way turnover, fill counts, name
  counts, net/gross ratio (`eda_mechanics.py`, `eda_smooth.py`);
- per-sleeve and per-fold **gross** PnL with funding attributed to its 8h bar (`eda_surface.py`);
- from `eda_variants.py` onward, the **gross information ratio** of the uncosted, unscaled reference
  book: mean gross bar return ÷ its own standard deviation. Both terms were already required — the
  standard deviation is the input to the organiser's own risk scalar `s = clamp(0.10/σ, 0.20, 3.0)`
  and is what converts unit-gross turnover into executed turnover, so the turnover floor cannot be
  reasoned about without it — and their ratio is an information ratio;
- from `eda_calibrated.py` onward, an explicitly **calibrated screen**. After #21 returned turnover
  28.76 and net Sharpe 1.018 where the offline figures were 20.5 and IR 1.31, two constants were
  fitted from that single organiser observation (`turnover_packet ≈ 1.40 · turnover_offline`;
  `sharpe_packet ≈ 0.92 · IR_offline − 0.00912 · turnover_offline`) and used to steer the turnover
  repair. It predicted #23 at turnover 24.1 / Sharpe 1.06 against actuals of 24.34 / 1.130.

Never computed offline: a costed equity curve, a net Sharpe on a simulated book, a drawdown, a
quarter or fold Sharpe, an exposure-cap application, a risk-policy application, a participation cap,
or any floor verdict. No candidate was selected against a private replica of the charter's metric
vector. The calibrated screen above is the closest this team came to one and it is named as such.

---

## 3. What was built

`candidates/run-gated-trend/` (and the cadence variants `-slow`, `-weekly`, plus five ablations).
Full construction in that directory's README. In one line: direction from the net displacement over
`FORMATION_BARS` 8h bars; admission only where the standardised count of agreeing bars clears
`PERSISTENCE_Z_FLOOR`; size `direction/σ` inside the admitted set; target = the mean of the last
`SMOOTH_BARS` unit-gross admitted cross-sections (overlapping tranches, which set the holding
period); `NET_EXPOSURE_DAMPING` × the book's own mean weight subtracted from every live name;
`None` returned on every boundary off the `REBALANCE_EVERY`/`REBALANCE_PHASE` cadence so the
evaluator holds quantities and no turnover is incurred.

Ablations are the *same file* with `USE_GATE` / `USE_INVERSE_VOLATILITY` / `NET_EXPOSURE_DAMPING`
changed, so a control's contribution cannot be confounded with a second implementation.

`risk_policy.json` is explicitly flat — no volatility target, no drawdown brake, no stops, no
turnover limit. **No number anywhere in this certificate is reached through a declared risk
policy**, and the organiser's standing constraint on declared volatility targets is satisfied
vacuously.

Roles declared long+short and observed long+short on every run.

---

## 4. Every trial

| seq | candidate | kind | question |
|---|---|---|---|
| 21 | `run-gated-trend` | point | does the gated construction clear the floors at cadence 3? |
| 22 | `abl-gate-off` | point | **gate-removal ablation** — same code, `USE_GATE=0` |
| 23 | `run-gated-trend-slow` | point | can the turnover floor be cleared, and at what price? (cadence 9) |
| 24 | `abl-controls-off` | point | transparent baseline: no gate, equal weight, no damping |
| 25 | `abl-gate-only` | point | individual control: the gate alone on the baseline |
| 26 | `abl-formation-45` | point | third formation horizon: 45 bars instead of 15 |
| 27 | `abl-cadence-1` | point | second rebalance horizon at the fast end: every 8h boundary |
| 28 | `run-gated-trend-slow` | falsification | exact sign inversion + 8 gross-edge placebos — **both passed** |
| 29 | `run-gated-trend-weekly` | point | third cadence point: weekly, to fix the worst fold |

No trial was abandoned and none crashed. Nothing was evaluated without a journaled trial.

---

## 5. Results — every packet, at 1× cost unless stated

| seq | run | Sharpe 1× | Sharpe 2× | ann. ret | vol | maxDD | turnover | edge/turn bps | long PnL | short PnL | trades | pos-Q | fold Sharpes @2× | B | measured failures |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| 24 | controls off (baseline) | 0.066 | −0.030 | −0.0045 | 0.181 | 0.189 | 23.06 | 12.3 | +0.207 | −0.094 | 32449 | 0.412 | −0.25 +0.97 −0.84 −0.08 | 0.545 | 11 floors |
| 22 | gate OFF, other controls kept | 0.347 | 0.210 | 0.0408 | 0.146 | 0.142 | 26.55 | 26.3 | +0.323 | −0.046 | 32473 | 0.471 | +0.48 +0.90 −0.79 −0.19 | 0.758 | 9 floors |
| 25 | gate ONLY (on the baseline) | 0.552 | 0.432 | 0.0710 | 0.143 | 0.208 | 22.72 | 42.0 | +0.396 | −0.018 | 29811 | 0.647 | +0.28 +0.19 −0.07 +1.64 | 0.851 | 5 floors |
| 27 | full stack, cadence 1 | 0.867 | 0.670 | 0.1055 | 0.125 | 0.118 | 32.74 | 40.3 | +0.490 | +0.033 | 84610 | 0.588 | +0.80 +0.34 −0.11 +1.72 | 0.955 | turnover, confidence |
| 21 | full stack, cadence 3 | 1.018 | 0.850 | 0.1311 | 0.129 | 0.120 | 28.76 | 53.0 | +0.556 | +0.047 | 29978 | 0.588 | +1.01 +0.55 +0.12 +1.86 | 0.9755 | turnover |
| 23 | full stack, cadence 9 | **1.130** | 0.990 | 0.1484 | 0.130 | 0.134 | **24.34** | 67.5 | +0.529 | +0.122 | 10716 | 0.647 | +1.70 +0.65 **−0.38** +2.02 | **0.9855** | worst-fold |
| 29 | full stack, cadence 21 | 0.892 | 0.785 | 0.1247 | 0.143 | 0.198 | 20.51 | 69.1 | +0.631 | **−0.069** | 5020 | 0.471 | +1.46 −0.10 −0.24 +1.96 | 0.957 | quarters, fold count, short sleeve, confidence |
| 26 | formation 45 bars | −0.298 | −0.410 | −0.0467 | 0.131 | 0.312 | 19.49 | −12.8 | +0.043 | −0.142 | 18595 | 0.294 | −0.03 −0.30 −2.30 +0.40 | 0.260 | 12 floors |

(The confidence column is omitted because it is a function of `B` and the *final* trial count; at
T = 9 the requirement is B ≥ 0.98889, and the best B achieved is 0.9855.)

### 5.1 The gate-removal ablation — the run this lane turns on

| | baseline #24 | + gate only #25 | full stack − gate #22 | full stack #21 |
|---|---:|---:|---:|---:|
| net Sharpe 1× | 0.066 | 0.552 | 0.347 | **1.018** |
| gross edge per unit turnover | 12.3 bps | 42.0 bps | 26.3 bps | **53.0 bps** |
| short-sleeve gross PnL | −0.094 | −0.018 | −0.046 | **+0.047** |
| positive folds @2× | 1 of 4 | 1 of 4 | 2 of 4 | **4 of 4** |

Read it two ways and it says the same thing. **Adding only the gate** to the transparent baseline
takes Sharpe from 0.066 to 0.552 and gross edge per unit turnover from 12.3 to 42.0 bps — from
comfortably failing the 40 bps cost-density floor to passing it. **Removing only the gate** from the
full stack takes Sharpe from 1.018 to 0.347 and edge density from 53.0 back to 26.3. The other two
controls together (inverse-vol weighting, net-exposure damping) are worth 0.28 of Sharpe on their
own (#24 → #22); the gate is worth 0.49 on its own and 0.67 in the presence of the others. It is the
largest single contributor by a factor of two and the only control that moves the cost-density and
short-sleeve floors across their thresholds.

The candidate would emphatically *not* work about as well with the gate removed. That was the
question the mandate said to answer, and the answer is unambiguous.

### 5.2 Formation horizons — three journaled, and a real limit

15 bars (5 days) — #21/#22/#23/#27/#29 — Sharpe 1.018 at cadence 3.
45 bars (15 days) — #26 — Sharpe **−0.298**, twelve floors failed, worst fold −2.30.
Offline, with the standardised gate holding selectivity fixed, the surface is positive at 9–33 bars
and collapses beyond about 36 (`research/eda_zgate.py`, `research/eda_finalists.py`: IR 1.31 at a
15-bar centre, 1.24 at 18, 1.07 at 21, 1.00 at 24).

This is a genuine limitation and it is stated rather than buried: **the run-structure edge is a
short-horizon phenomenon on this universe.** Eight-hour bars aggregated over 3–11 days carry a
readable run structure; over three weeks they do not, and the gate at 45 bars selects a small,
idiosyncratic set that loses money. A lane described as "trend quality" would like the effect to
strengthen with horizon, as classical trend following does. It does the opposite here.

### 5.3 Rebalance horizons and the phase offset

Four cadences journaled — 1 bar (#27), 3 bars (#21), 9 bars (#23), 21 bars (#29). Turnover falls
monotonically with cadence (32.7 → 28.8 → 24.3 → 20.5) while Sharpe rises and then falls
(0.867 → 1.018 → 1.130 → 0.892). Cadence 1 needs no phase offset by definition. For the cadences
longer than one bar the phase was swept **offline only** — at cadence 3 the three offsets are
exhaustive and gave gross IRs of 1.41 / 1.35 / 1.28 (phases 0/1/2, `research/eda_freeze_check.py`
and the scratch sweep of the eleven intended neighbourhood points), a ±5% spread around the middle
offset that was used everywhere.

**This is an acknowledged shortfall against §7 of the playbook.** The phase offset was to have been
swept inside the organiser's harness as a declared neighbourhood coordinate — that was the plan, and
the neighbourhood was designed with `REBALANCE_PHASE` as one of five coordinates and the three
cadence-3 offsets as an exhaustive set. The declared sweep was never run because the candidate it
would have scored cannot clear the floors, and spending the trial would have raised the confidence
bar on a candidate already failing it. Phase evidence for cadences 9 and 21 is therefore offline
only, and a cadence-21 book has 21 offsets of which none was tested in the harness. Anyone reading
#29 should treat it as one phase draw from a distribution that was not measured.

### 5.4 Controls-off, individual-control and combined-control ablations

Journaled: controls off (#24), gate alone (#25), gate + inverse-vol + damping (#21/#23/#27/#29), and
the leave-one-out that removes the gate (#22). Not journaled: the two leave-one-out runs that remove
inverse-vol weighting or damping individually from the full stack; those were measured offline only
(`research/eda_freeze_check.py`) at gross IR 1.05 and 0.99 against the full stack's 1.14, i.e. each
worth roughly 0.10–0.15 of IR — an order of magnitude less than the gate. They were not journaled
because the trial budget was better spent on the cadence ladder that decides the floors.

### 5.5 Long, short and chop role checks

Roles were declared long+short before every run and observed long+short on every run; the declared/
observed check passed every time. The short sleeve is the mechanism's weakest limb and this is the
candidate's second-thinnest floor after confidence: gross short PnL is +0.047 at cadence 3, +0.122
at cadence 9, and **−0.069 at cadence 21**, against long-sleeve PnL of +0.53 to +0.63. It is
positive only because perpetual funding is paid to shorts (mean 8h funding rate on the IS window is
+0.0121%, so a short earns roughly 13% a year in carry); on price alone the short sleeve is close to
flat. Every ablation with the gate removed has a negative short sleeve. The chop check is fold F3
(2022-08 → 2023-08, the FTX trough and the range that followed), and it is where every configuration
is weakest: 2×-cost fold Sharpes of +0.12 (cadence 3), −0.38 (cadence 9), −0.24 (cadence 21),
−0.79 (gate off), −0.84 (baseline).

### 5.6 Falsification battery — #28, on the strongest configuration

Both halves were run by the organiser's harness on `run-gated-trend-slow`, the strongest
configuration. Output in `research/packet_T28_falsification.txt`.

**Exact sign inversion — the falsifier is satisfied.** Negating every emitted weight produces net
Sharpe −1.507 (1×), −1.646 (2×), −1.784 (3×), annualised return −0.185, maximum drawdown 0.569. It
fails six of the eight core floors and clears only realised volatility and trade count, which are
sign-blind by construction. The apparent edge is directional, not an artifact of cost, funding or
cap asymmetry — had it been, the inverted book would have shared it.

**Gross-edge placebo — the attribution carries the edge.** Eight placebo books preserving the
candidate's weight multiset and rebalance schedule exactly, randomising only which eligible symbol
receives which weight: gross edge per unit one-way turnover of **min −0.60, median 5.68, max 13.96
bps** against the candidate's **67.51 bps**. Exceedance 0.0000 — not one placebo came within a
factor of four. The book's performance is not a property of its shape, its turnover profile or its
schedule; it is a property of *which name gets which sign*, which is exactly what the run gate
decides.

Taken together with §5.1, this is as strong an internal case as this evidence base can make: the
mechanism is real, it is directional, and it is the gate rather than the packaging.

### 5.7 Declared neighbourhood — designed, validated offline, never swept

The neighbourhood was designed before any of it was scored, with five coordinates
(`FORMATION_BARS`, `PERSISTENCE_Z_FLOOR`, `SMOOTH_BARS`, `NET_EXPOSURE_DAMPING`, `REBALANCE_PHASE`),
eleven points, each coordinate varied materially above and below, each `PERSISTENCE_Z_FLOOR` point
checked to land on a *different* integer run count than the nominee so that no point would be a
behavioural duplicate. Its offline medians were gross IR 1.22 against the nominee's 1.31 — the
5–7% median-below-nominee haircut that is the whole point of §7.2, and the haircut that puts the
confidence floor definitively out of reach. `neighbourhood.json` was deliberately **not** written:
declaring one is a nomination act, and this team is not nominating.

---

## 6. Why the floors cannot be met — the finding, stated precisely

The common risk unit rescales every book toward 10% annualised volatility. This construction
realises 35–65% annualised volatility at unit gross, so the scalar is well under 1 (median 0.29 at
cadence 3, 0.30 at cadence 9, 0.32 at cadence 21) — and **executed turnover is the unit-gross
turnover multiplied by that same scalar**. Two consequences follow that are not obvious from the
outside and cost this team its submission:

1. **Anything that lowers the book's own volatility raises its executed turnover.** The
   net-exposure damping is the largest single Sharpe lever available (offline, raising it from 0.45
   to 0.65 lifts gross IR from 1.31 to 1.49) and it works by removing market exposure — which lowers
   σ, which raises the risk scalar, which raises executed turnover roughly proportionally. Damping
   therefore buys Sharpe and spends turnover budget at the same time, and the 25× floor caps how much
   of it can be bought. Every configuration in the search with predicted net Sharpe above ~1.19 had
   predicted turnover above 30.
2. **Low-volatility regimes are penalised twice.** In fold F3 the whole universe's volatility
   collapsed, so the scalar rose toward its 1.0 ceiling, so gross rose, so turnover and cost rose —
   in exactly the fold where the gross edge was thinnest. F3's 2×-cost Sharpe is the floor this
   candidate fails at cadence 9, and it is not primarily a signal failure: F3's *gross* information
   ratio offline was +0.47, and the cost drag at 24.3× turnover and 13% volatility is about 0.28 of
   Sharpe at 2×.

The cadence ladder is the trade-off curve those two facts imply, measured by the organiser's harness
at four points:

| cadence | turnover | Sharpe 1× | worst fold @2× | short sleeve | verdict |
|---:|---:|---:|---:|---:|---|
| 1 | 32.74 | 0.867 | −0.11 | +0.033 | turnover fails |
| 3 | 28.76 | 1.018 | +0.12 | +0.047 | turnover fails |
| 9 | 24.34 | 1.130 | −0.38 | +0.122 | worst fold fails; confidence 0.884 at T=8 |
| 21 | 20.51 | 0.892 | −0.24 | −0.069 | quarters, fold count, short sleeve fail |

There is no point on it that clears everything, and the two ends fail for opposite reasons. Even
granting the best point, the trial-adjusted confidence floor requires `B ≥ 0.9875` at the minimum
eight trials; the best measured `B` is 0.9855, corresponding to a Sharpe of 1.130 where roughly 1.17
is needed — **on a neighbourhood median that runs 5–7% below the nominated point**, which pushes the
requirement to about 1.25 at the nominated point. That is a 10% shortfall in Sharpe, not a
tuning gap, and closing it by further search would raise `T` and the bar with it.

---

## 7. Everything that did not work, with its cost

- **The efficiency ratio, the lane's own headline statistic.** Falsified as a distinct path reading
  (corr 0.98 with `|z|`). Offline only; cost: no trials, one day of direction.
- **Jump share.** Falsified as a gate at every horizon under 63 bars; selecting low-jump moves
  destroyed the edge. Offline only.
- **A fixed-fraction persistence threshold.** Not wrong, but it confounds the formation axis with
  the selectivity axis and made the surface look far more fragile than it is. Replaced by the
  standardised z form. Offline only.
- **Skipping recent bars** (short-horizon reversal): monotonically worse (IR 1.14 → 1.09 → 1.02 →
  0.97 for skips of 0–3 bars). Offline only.
- **Strength-weighted admission** instead of binary: neutral to slightly worse. Offline only.
- **Multi-formation ensembles**: +0.03 to +0.07 of gross IR, not worth the extra coordinates.
  Offline only.
- **Damping each tranche's own net before averaging** (to cut turnover): cut turnover as intended
  but cut IR from 1.42 to 1.12 — a net loss. Offline only.
- **Dropping the per-tranche renormalisation**: better fold F3, lower overall Sharpe. Offline only.
- **Formation 45.** Journaled as #26: Sharpe −0.298, twelve floors failed. The horizon limit is
  real.
- **Cadence 1 and cadence 21.** Journaled as #27 and #29. Both fail; they bracket the workable
  region rather than extending it.
- **The gate-off and controls-off runs.** Journaled as #22 and #24. They are the evidence the
  mechanism is real, and they are also two candidates that fail nine and eleven floors respectively.

## 8. What the organiser should know

- The blindness scan reports **0 violations** on this workspace at every invocation, over 61 files.
  Every prohibited surface named in playbook §1 — the holdout snapshot, the acquisition snapshot,
  the organiser-only tournament subtree, the derived reports tree — and every other team's
  directory was never opened, never named in any file this team wrote, and never retrieved from
  version control in any revision. (This paragraph deliberately describes them rather than spelling
  their paths, because the scan matches the literal strings against file content and does not need
  to prove intent; an earlier draft of this certificate spelled them out and tripped the team's own
  scan, which is how the rule was confirmed to work as documented.)
- Nothing was fetched from any market data source. The only inputs are the five parquet files under
  `data/cup20/is/` and the rows the runner streamed through `DecisionContext`.
- The candidate directories are left in place and are reproducible: each carries `strategy.py`,
  `risk_policy.json`, and — for `run-gated-trend` — a README. `neighbourhood.json` is deliberately
  absent from all of them.
- The one methodological point worth raising with the organiser, offered as an observation rather
  than a complaint: the trial-adjusted confidence floor at the *minimum* trial count of eight
  requires an in-sample Sharpe of roughly 1.17 on a four-year window, on a neighbourhood median.
  A team that spends its full twelve needs about 1.25. That is a high bar for an unlevered book held
  to 10% volatility, ≤ 25× turnover and ≤ 20% drawdown simultaneously, and it may be that the floor
  is binding on more lanes than intended. This team's finding is not that the bar is wrong — it is
  that this mechanism does not clear it, and that is what is being reported.
