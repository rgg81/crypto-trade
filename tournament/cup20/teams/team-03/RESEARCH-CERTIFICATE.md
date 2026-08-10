# Team 03 — Research Certificate

Lane: `trend-quality-gated-momentum`. Data root: `data/cup20/is/`, and nothing else.
Trials accepted: **11** (journal sequences 21–29, 43, 44). Trials remaining unspent: 1.

> **Read this certificate as two documents.** It was written to a close under the floors as they
> stood, and it concluded NO NOMINATION. The floors then changed. §0 below is the outcome section
> exactly as it was written then, preserved unedited; §0.1 is what changed and what I conclude now.
> Sections 1–8 are the original research record, with §4, §5.7 and §6 extended — never overwritten —
> where the second session added evidence. Nothing in the original reasoning has been retro-fitted to
> look as though it anticipated the amendment. It did not.

## Outcome: NOMINATED — `run-gated-trend` (formation 15, cadence 3, phase 1)

**Ranking score G = 35.05**, on the median of a declared 13-point neighbourhood (#43), with the
falsification battery re-run on the nominated point and passed (#44). Two floors are missed and both
are priced rather than fatal: annualised turnover 28.60 against 25, and trial-adjusted confidence
0.632 against 0.90. Every other floor passes on the median, including all four folds positive at 2×
cost, both sleeves gross-positive, maximum drawdown 0.114, and 13 of 13 neighbourhood points with
positive return and positive 2× Sharpe.

Under the amended rules the nominee is **not** the configuration this certificate originally called
the best one. That is the whole substance of the second session and it is stated first because it is
the part most open to the accusation of having been reverse-engineered from a scoreboard. §0.1 gives
the arithmetic.

---

## §0 — the outcome concluded under the rules as they stood (preserved unedited)

### Outcome: NO NOMINATION

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

## §0.1 — the rules changed, and what follows from that

### What changed

Two amendments, both recorded after this team stopped, move the thing §0 turned on.

**The performance floors stopped being vetoes.** They are still measured, still reported and still
recorded verbatim; advancement is now the ranking score over every admissible candidate. Four checks
still remove a candidate outright — the two integrity checks (the sign inversion, and declared roles
agreeing with traded sides) and two substance checks that ask whether there is a book at all
(realised volatility ≥ 0.06 and ≥ 500 executed trades). This candidate clears all four with room:
0.13 realised volatility against 0.06, and 29 978 trades against 500.

**The floors the ranking score has no term for are now priced** by a multiplicative compliance
factor — the mean graded credit across thirteen of them, each graded from its own frozen threshold
with a relative shortfall. Missing a floor therefore costs a real, proportional amount rather than
either nothing or everything. The same amendment un-saturated the score's terms, so a term keeps
losing credit below its threshold instead of clamping at zero.

### What that does to the ladder in §6, arithmetically

§6's cadence ladder is unchanged as measurement; every number in it was produced by the organiser's
harness and none of it moved. What moved is the price of each row's failure. Re-scoring the eight
journaled packets through the organiser's own `robustness_score` and `compliance_factor` — over the
metric vectors already in this team's packet JSONs, with nothing recomputed — gives
(`research/rescore_under_a4_a5.py`):

| seq | run | worst fold 2× | median fold 2× | maxDD 2× | calmar 2× | B | compliance | **G at T = 11** |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 24 | controls off (baseline) | −0.843 | −0.168 | 0.198 | −0.109 | 0.545 | 0.440 | −11.83 |
| 22 | gate OFF, controls kept | −0.786 | +0.146 | 0.162 | +0.125 | 0.758 | 0.778 | −11.18 |
| 25 | gate ONLY on baseline | −0.075 | +0.234 | 0.218 | +0.243 | 0.851 | 0.889 | +1.75 |
| 26 | formation 45 | −2.299 | −0.166 | 0.335 | −0.181 | 0.260 | 0.410 | −19.69 |
| 27 | full stack, cadence 1 | −0.106 | +0.566 | 0.130 | +0.606 | 0.955 | 0.976 | +23.88 |
| **21** | **full stack, cadence 3** | **+0.124** | +0.782 | 0.131 | +0.814 | 0.9755 | 0.988 | **+39.72** |
| 23 | full stack, cadence 9 | −0.385 | **+1.173** | 0.154 | +0.830 | 0.9855 | **1.000** | +31.42 |
| 29 | full stack, cadence 21 | −0.241 | +0.683 | 0.216 | +0.498 | 0.957 | 0.897 | +8.00 |

The ordering inverts. **§6 named cadence 9 the best configuration found, and under a ranking score it
is not.** The reason is a single term: worst-fold Sharpe at 2× cost carries thirty of the hundred
points, more than any other, and cadence 3 is the only configuration in this ladder with all four
folds positive. Its +0.124 earns 11.2 of those 30; cadence 9's −0.385 now *loses* 3.6 of them, a
14.8-point swing that its better median fold (+5.8), drawdown (−3.1) and quarters (+1.3) do not come
close to recovering. Cadence 3's turnover overrun — 28.76 against a 25× floor — is what removed it
from the field under the old rules and is now worth a compliance factor of 0.988: **1.2% of the
score, against the 100% it used to cost.**

### The honest reading of my own §0

§0's reasoning was sound on its own terms and I am not going to dress it up as prescience. It was
also, in one respect, *more* wrong than the rule change alone accounts for, and that is worth
recording because it is the part I own. §0 ranked the ladder by how many floors each rung failed and
by how close the best rung came to the confidence bar. That is ranking by distance-to-admission,
which is the right objective under a conjunctive gate and a poor proxy for quality under any other.
Reading §5.1's own table, cadence 3 was already the only rung with four positive folds — the fact
that now decides the ranking — and §0 recorded it in a row and then ranked past it, because a fold
count was not a floor and turnover was. A team that had been asked "which of these books
generalises best across regimes" rather than "which clears every bar" would have answered cadence 3
from the evidence already in this document. The amendment did not tell me something new about my
book; it stopped a gate from hiding what my book had already shown.

What the amendment genuinely did change is that a nomination became *possible*: under conjunctive
floors, cadence 3 failed turnover, and no cadence cleared everything. §6 is correct that no rung
cleared the old floors. It is that conclusion, and not the ladder underneath it, that the amendment
retires.

### What I did not do

I did not re-optimise the candidate against the new objective, and the temptation was concrete. The
score is 58 points of fold consistency and 35 of drawdown control, and it prices turnover at one
thirteenth of a multiplicative factor. §6.1 records that the largest Sharpe lever available is the
net-exposure damping, that raising it from 0.45 to 0.65 lifts offline gross IR from 1.31 to 1.49,
and that the only reason it was held at 0.45 is that it spends turnover budget. Under the amended
rules a run at turnover 35 would cost about 3% of the score. There was budget for exactly one point
trial to try it.

I did not, for three reasons. The term that decides this ranking is worst-fold Sharpe, and nothing
in this team's offline screen predicts it — the calibrated screen of §2 predicts turnover and net
Sharpe and has never been asked about a fold. Damping buys Sharpe by removing market exposure, which
raises executed turnover, which raises cost drag, which lands hardest in F3, which is the fold that
sets the worst-fold term at every rung of this ladder: the mechanism of the lever points the wrong
way for the term I would be buying it with. And a nominee chosen from a single post-amendment
observation, with no ablation journaled against it and no budget left to check it, is the maximum of
a noisy surface — exactly what the neighbourhood median exists to discount, and exactly what §0 was
right to refuse to do in the other direction. The nominee is the configuration my journaled evidence
already supported. What changed is the rule that kept it out, not my read of the book.

### Trials, and what the banked falsification does and does not cover

Two of the three remaining trials were spent, leaving one unspent:

- **#43, the declared neighbourhood sweep** on `run-gated-trend` — thirteen points, the first
  declared sweep this team has ever run, and the gap §0 correctly identified in §5.7.
- **#44, the falsification battery re-run** on `run-gated-trend`. The battery banked at #28 was run
  on `run-gated-trend-slow`, a different candidate at a different cadence and a different source
  digest. It passed decisively there and §5.6 stands as written, but a falsification result is a
  property of the point it was run on, and the charter runs the inversion on the *nominated* point.
  Carrying #28's verdict across a cadence change would have been exactly the kind of "close enough"
  claim this certificate has refused everywhere else. It was re-run.

`T = 11` at nomination. The confidence term only reaches its own 0.90 threshold — where it starts
earning anything at all — at `B ≥ 0.99091`, and earns full credit only at `B = 1`. It will do
neither, and that is now a graded 7-point term rather than the veto §6 measured itself against. The
whole cost of spending two more trials is about 0.6 of a point (G at T = 9 is 40.29, at T = 11 it is
39.72), against the roughly 8 points that switching the nominee from cadence 9 to cadence 3 is worth.

### The score

The declared sweep ran at #43 and is valid: thirteen points, thirteen distinct materialised source
digests, no inert point, 2841 s of wall clock. **The neighbourhood median — which is the score, and
not the nominated point's own vector — is:**

| | median (the score) | nominee (diagnostic) | floor |
|---|---:|---:|---|
| net Sharpe 1× | **0.980** | 1.018 | ≥ 0.80 ✔ |
| net Sharpe 2× | **0.808** | 0.850 | ≥ 0.50 ✔ |
| net Sharpe 3× | **0.639** | 0.683 | > 0 ✔ |
| annualised return 1× / 2× | **0.1224 / 0.1000** | 0.1311 / 0.1070 | > 0 ✔ |
| max drawdown 1× / 2× | **0.114 / 0.125** | 0.120 / 0.131 | ≤ 0.20 ✔ |
| realised volatility | **0.1288** | 0.1292 | ≥ 0.06 ✔ *(substance)* |
| worst-fold Sharpe 2× | **+0.091** | +0.124 | ≥ −0.25 ✔ |
| median-fold Sharpe 2× | **+0.660** | +0.782 | — |
| folds positive 2× | **4 of 4** | 4 of 4 | ≥ 3 ✔ |
| positive quarters 1× | **0.588** | 0.588 | ≥ 0.50 ✔ |
| Calmar 2× | **0.749** | 0.814 | — |
| gross edge / turnover | **50.2 bps** | 53.0 bps | ≥ 40 ✔ |
| cost share of positive gross | **0.0162** | 0.0163 | ≤ 0.30 ✔ |
| five-largest-day share | **0.0407** | 0.0413 | ≤ 0.35 ✔ |
| worst fold's share of positive PnL | **0.346** | 0.345 | ≤ 0.60 ✔ |
| executed trades | **29 978** | 29 978 | ≥ 500 ✔ *(substance)* |
| long / short gross PnL | **+0.529 / +0.046** | +0.556 / +0.047 | each > 0 ✔ |
| neighbourhood points positive | **13 of 13 (1.00)** | — | ≥ 0.70 ✔ |
| annualised turnover 1× | **28.60** | 28.76 | ≤ 25 ✘ |
| trial-adjusted confidence | **0.632** (B = 0.9665, T = 11) | — | ≥ 0.90 ✘ |

**Ranking score G = 35.05** at `T = 11` (the harness printed 35.238 at the `T = 10` it was run
under; the falsification trial moves it by 0.19). Two floors are missed, both priced rather than
fatal. Their exact price: a book identical in every other respect that exactly *met* both floors
would score **40.54**, so the two misses cost **5.49 points** — the turnover overrun sets the
compliance factor to **0.9889** (−0.39), and the confidence shortfall takes the 7-point term from 0
to **−5.10**.

Three things in that table are worth reading twice. **Every one of the four folds is positive at the
median, not only at the nominee** — the sweep did not merely fail to break the fold structure, it
reproduced it at thirteen points out of thirteen. **All thirteen points have positive 1× return and
positive 2× Sharpe**, so the neighbourhood-positivity floor passes at 1.00 rather than at its 0.70
requirement. And the median is a genuine haircut, not a formality: net Sharpe falls 1.018 → 0.980 and
worst fold +0.124 → +0.091, about 4% and 27% below the nominated point respectively, which is what a
plateau estimate is supposed to look like.

**The short sleeve remains this book's thinnest limb**, and the median makes that plainer than the
nominee did: +0.046 of gross PnL against the long sleeve's +0.529, an eleven-to-one split. It clears
its floor and it is carried largely by funding paid to shorts (§5.5). Anyone weighing this candidate
should treat the short sleeve as demonstrated-positive rather than as a source of edge.

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
| 43 | `run-gated-trend` | **neighbourhood** | the declared 13-point sweep — **the score** (§5.7) |
| 44 | `run-gated-trend` | **falsification** | sign inversion + placebo, re-run on the *nominated* point (§5.6a) |

No trial was abandoned and none crashed. Nothing was evaluated without a journaled trial. Sequences
21–29 are the first session; 43 and 44 are the second, after the amendments of §0.1. One trial of the
twelve is unspent, and was deliberately held back: the sweep's inertness check (charter §7.2 as
amended) cannot run until the points have run, and a void sweep would have needed a re-declaration
and a fresh trial. It was not needed.

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

### 5.6 Falsification battery — #28, on `run-gated-trend-slow`, which is **not** the nominee

*(Retained as evidence about the mechanism at a second cadence. The battery that decides the
nominated candidate is #44 in §5.6a below; this one does not transfer to it and is not claimed to.)*

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

### 5.6a Falsification battery re-run on the nominated point — #44

§5.6 above is the battery as run at #28, on `run-gated-trend-slow`. That is **not** the nominated
candidate. A sign-inversion verdict is a property of the point it was run on, the charter runs the
inversion on the nominated point, and the two candidates differ in cadence and in source digest — so
carrying #28's verdict across would have been an unaudited claim about a book nobody had inverted.
It was re-run at #44, on `run-gated-trend`, by the organiser's harness. Output in
`research/falsification_T44.log`.

**Exact sign inversion — the falsifier is satisfied, and by a wider margin than at #28.** Negating
every emitted weight gives net Sharpe **−1.485** (1×), **−1.653** (2×), **−1.821** (3×), annualised
return **−0.181** (1×) and **−0.199** (2×), maximum drawdown **0.597**. It **fails six of the eight
core floors** and clears only realised volatility (0.129) and trade count (30 026) — the two that are
sign-blind by construction and cannot distinguish a book from its negation. The apparent edge is
directional; it is not an artifact of cost, funding or cap asymmetry, because an artifact of any of
those would have survived the flip.

**Gross-edge placebo — the attribution carries the edge.** Eight placebo books preserving this
candidate's weight multiset and rebalance schedule exactly and randomising only which eligible symbol
receives which weight reach a gross edge per unit one-way turnover of **min −0.79, median 2.69, max
4.81 bps**, against the candidate's **52.96**. **Exceedance 0.0000** — the best of eight placebos
reaches under a tenth of the candidate. The book's performance is not a property of its shape, its
turnover profile or its schedule; it is a property of which name gets which sign, which is what the
run gate decides. The placebo distribution here is *tighter* than at #28 (median 2.69 against 5.68),
so the separation at the nominated cadence is if anything cleaner.

Both admission-critical integrity checks are therefore measured and passed on the nominated point:
`sign_inversion_not_profitable`, and `declared_roles_match_traded_sides` (declared long+short,
observed long+short, at every trial including this one). The two substance checks pass on the
neighbourhood median: realised volatility 0.129 against 0.06, and 29 978 executed trades against 500.

### 5.7 Declared neighbourhood — designed in session one, swept in session two (#43)

**As it stood at the close of session one**, verbatim: *"The neighbourhood was designed before any of
it was scored, with five coordinates (`FORMATION_BARS`, `PERSISTENCE_Z_FLOOR`, `SMOOTH_BARS`,
`NET_EXPOSURE_DAMPING`, `REBALANCE_PHASE`), eleven points, each coordinate varied materially above
and below, each `PERSISTENCE_Z_FLOOR` point checked to land on a different integer run count than the
nominee so that no point would be a behavioural duplicate. Its offline medians were gross IR 1.22
against the nominee's 1.31 — the 5–7% median-below-nominee haircut that is the whole point of §7.2.
`neighbourhood.json` was deliberately not written: declaring one is a nomination act, and this team
is not nominating."*

**What was declared and swept at #43** is that design with one coordinate added, six in total, and
thirteen points rather than eleven:

| coordinate | nominee | below | above |
|---|---:|---:|---:|
| `FORMATION_BARS` | 15 | 12 | 18 |
| `PERSISTENCE_Z_FLOOR` | 1.10 | 0.70 | 1.40 |
| `SMOOTH_BARS` | 33 | 27 | 39 |
| `NET_EXPOSURE_DAMPING` | 0.45 | 0.35 | 0.55 |
| `REBALANCE_EVERY` | 3 | 2 | 4 |
| `REBALANCE_PHASE` | 1 | 0 | 2 |

The added coordinate is **`REBALANCE_EVERY`, the cadence**, and adding it is against this team's
interest, which is why it is here. The cadence is unambiguously a material parameter — it is the axis
§6 explores most heavily and the one the whole ladder is built on — and its neighbours are measurably
worse than the nominee at both ends. Leaving the single axis I know most about out of the declaration,
*after* measuring that its neighbours drag the median down, is precisely the median management §7.2
exists to stop. It went in.

The design is a **one-at-a-time star**: nominee plus exactly one point above and one below on each of
the six coordinates, 13 points, which is `max(7, 2k+1)` for `k = 6` on the nose. Every point differs
from the nominee in exactly one coordinate. There is no corner point, no side of any axis is
sampled twice, and the shape has no free parameter left with which to lean on a median.

**The inertness trap, and why the z-floor points are where they are.** Charter §7.2 as amended voids
a sweep containing a point that reproduces the nominee's metric vector exactly. `PERSISTENCE_Z_FLOOR`
is compared against a quantised statistic: with 15 formation bars the agreeing-bar count is an
integer, so `z` can only be `(2k − 15)/√15` — 0.775 at k = 9, 1.291 at k = 10, 1.807 at k = 11. Every
threshold in `(0.775, 1.291]` selects the identical set of bars. The nominee's 1.10 sits inside that
cell, and so do the minimally-material variations 1.045 and 1.155 that satisfy the 5% rule: declaring
either would have produced a byte-identical book, voided the sweep and cost the trial. The declared
0.70 and 1.40 land in the k ≥ 9 and k ≥ 11 cells respectively. This is the same quantisation hazard
the first session flagged in its own design note; what is new is that it is now a rule with a price.

**`REBALANCE_PHASE` is swept exhaustively, not sampled.** At cadence 3 the offsets 0, 1, 2 are the
complete set, so §9.1's requirement that phase be swept for any cadence longer than one bar is met
completely rather than by two draws from a distribution. §5.3's acknowledged shortfall — that phase
evidence was offline only — is discharged for the nominated cadence. It remains true for cadences 9
and 21, which are not nominated.

**Every point, as run** (`research/sweep_T43.log` carries the materialised `strategy.py` digest for
each, all thirteen distinct):

| point | coordinate moved | Sharpe 1× | Sharpe 2× | ann. ret | maxDD 1× | trades |
|---|---|---:|---:|---:|---:|---:|
| nominee | — | 1.018 | 0.850 | 0.1311 | 0.120 | 29 978 |
| 1 | `FORMATION_BARS` 12 | 1.020 | 0.835 | 0.1282 | 0.113 | 31 936 |
| 2 | `FORMATION_BARS` 18 | 0.793 | 0.644 | 0.1016 | 0.118 | 26 170 |
| 3 | `PERSISTENCE_Z_FLOOR` 0.70 | 0.980 | 0.808 | 0.1219 | 0.098 | 32 360 |
| 4 | `PERSISTENCE_Z_FLOOR` 1.40 | 0.761 | 0.610 | 0.0951 | 0.144 | 19 518 |
| 5 | `SMOOTH_BARS` 27 | **0.587** | **0.405** | 0.0702 | **0.181** | 28 844 |
| 6 | `SMOOTH_BARS` 39 | 1.030 | 0.878 | 0.1348 | 0.143 | 30 570 |
| 7 | `NET_EXPOSURE_DAMPING` 0.35 | 0.948 | 0.793 | 0.1224 | 0.137 | 29 981 |
| 8 | `NET_EXPOSURE_DAMPING` 0.55 | 1.090 | 0.908 | 0.1412 | 0.103 | 29 956 |
| 9 | `REBALANCE_EVERY` 2 | 0.922 | 0.742 | 0.1138 | 0.113 | 43 794 |
| 10 | `REBALANCE_EVERY` 4 | 1.062 | 0.901 | 0.1372 | 0.095 | 23 045 |
| 11 | `REBALANCE_PHASE` 0 | 0.928 | 0.760 | 0.1173 | 0.114 | 29 995 |
| 12 | `REBALANCE_PHASE` 2 | 1.084 | 0.913 | 0.1368 | 0.089 | 29 883 |

Four readings of that table, three of which are uncomfortable and are therefore stated.

**The plateau is real but it is not flat, and the softest direction is `SMOOTH_BARS` downward.**
Point 5 — 27 tranches instead of 33 — is the worst point in the neighbourhood by a distance: Sharpe
0.587 against the nominee's 1.018 and a drawdown of 0.181, within touching distance of the 0.20
floor. Shortening the holding horizon is the one move that materially breaks this book, which is
consistent with §3's account of what the overlapping tranches are for. The upward direction (39) is
marginally *better* than the nominee. This is an asymmetric plateau and the nominee sits nearer its
cliff edge than its centre on that axis.

**The phase spread is real and it is wider than the offline sweep suggested.** Phases 0 / 1 / 2 give
Sharpe 0.928 / 1.018 / 1.084 — a spread of 0.156, where §5.3's offline gross-IR check found a ±5%
band around the middle offset. The nominated phase is the middle of the three, not the best; phase 2
would have scored higher at the point. **Nominating the middle offset was decided before any of the
three was measured in the harness, and I have left it there** rather than moving to phase 2 after
seeing this table, which would have been peak-picking on a coordinate whose whole purpose in the
declaration is to be averaged over.

**`NET_EXPOSURE_DAMPING` upward is genuinely better here too**, exactly as §6.1's offline work said
it would be: 0.55 gives Sharpe 1.090 and drawdown 0.103 against the nominee's 1.018 and 0.120, at
essentially unchanged trade count. Under the old floors that direction was closed by turnover; under
the new ones it is merely expensive. §0.1 records why I did not chase it, and this row is the
strongest evidence that I left something on the table by not doing so. It is left on the table.

**The cadence coordinate behaved as the ladder predicted**, which is the mild reassurance: cadence 2
is worse than 3 and cadence 4 is better, bracketing the nominee the way §6's curve says they should,
and the sweep median for turnover (28.60) sits just under the nominee's 28.76 rather than being
dragged by them.

---

## 6. Why the floors cannot be met — the session-one finding, stated precisely

*(Written under the conjunctive floors. The mechanism it describes — that lowering the book's own
volatility raises its executed turnover, so Sharpe and turnover budget are bought with the same coin
— is a fact about the common risk unit and is unaffected by the amendments. What the amendments
retire is the conclusion in its title. §6.2 states what survives.)*

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

### 6.2 What survives the amendments, and what does not

**Survives, unchanged.** The turnover–volatility coupling above is a property of the common risk
unit, not of any floor: executed turnover is unit-gross turnover times the risk scalar, the scalar is
`0.10/σ`, so anything that lowers this book's own volatility raises what it pays to trade. That is
why the cadence ladder is a trade-off curve at all, and it is why the damping coordinate cannot
simply be turned up now that the turnover floor has stopped being a veto. A ranking score that prices
turnover lightly does not make this book free to churn: the cost drag lands in the returns, and the
returns are what the fold terms measure.

**Survives, and matters more than it did.** The second observation — that low-volatility regimes are
penalised twice, because a collapsing universe volatility raises the scalar, the gross and the cost
in exactly the fold where the gross edge is thinnest — is now the single most expensive fact about
this candidate. F3 sets the worst-fold term at every rung of this ladder, and that term is 30 of 100
points. The nominee's F3 is +0.12 at 2× cost: positive, and thin. Anyone reading this candidate
should read that number as the load-bearing one.

**Does not survive.** The title. "No point on the ladder clears everything" is still true and is no
longer the question being asked. Under a ranking score the question is which point is best, and
§5.1's own table already answered it: the rung with four positive folds.

**One observation from §8 that is worth keeping in view.** That the confidence floor at the minimum
trial count demands an in-sample Sharpe near 1.17 on a plateau median, and that it might bind on more
lanes than intended, was written into §8 before this team had any way of knowing whether it had. It
is recorded as an observation that turned out to be load-bearing, not as a claim to have anticipated
the remedy — the remedy is the organiser's and it is more thorough than anything §8 proposed.

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

**Session two adds three more, all of them things this candidate does *not* do well:**

- **Shortening the holding horizon.** `SMOOTH_BARS = 27` is the worst point in the declared
  neighbourhood — Sharpe 0.587 against 1.018, drawdown 0.181 against a 0.20 floor (#43, point 5).
  This is the direction in which the plateau falls away, and the nominee is closer to that edge than
  to the middle of the axis.
- **The turnover floor was never repaired, only re-priced.** The median turnover is 28.60 against a
  25 floor. §6.1 explains why it cannot be repaired without giving back Sharpe: the risk unit ties
  the two together. Under the amended rules that costs 1.1% of the score; it is still a real miss and
  is reported as one.
- **The confidence floor was never reached and never could be.** The plateau median `B` is 0.9665,
  which at eleven accepted trials gives 0.632 against a 0.90 floor. §6 was right about this and it
  remains right: this mechanism does not produce a book with a bootstrap fraction near 0.99 on this
  window. It costs 5.1 of the 7 available points.

## 8. What the organiser should know

- The blindness scan reports **0 violations** on this workspace at every invocation, in both
  sessions — over 61 files at the close of the first and 70 at the close of the second.
  Every prohibited surface named in playbook §1 — the holdout snapshot, the acquisition snapshot,
  the organiser-only tournament subtree, the derived reports tree — and every other team's
  directory was never opened, never named in any file this team wrote, and never retrieved from
  version control in any revision. (This paragraph deliberately describes them rather than spelling
  their paths, because the scan matches the literal strings against file content and does not need
  to prove intent; an earlier draft of this certificate spelled them out and tripped the team's own
  scan, which is how the rule was confirmed to work as documented.)
- Nothing was fetched from any market data source. The only inputs are the five parquet files under
  `data/cup20/is/` and the rows the runner streamed through `DecisionContext`.
- The candidate directories are left in place and are reproducible: each carries `strategy.py` and
  `risk_policy.json`, and `run-gated-trend` — the nominee — additionally carries `README.md` and
  `neighbourhood.json`. The other eight are ablations and cadence variants and carry no
  neighbourhood, which is deliberate: only the nominated candidate has one.
- **The nominee's `strategy.py` and `risk_policy.json` are byte-identical to what trial #21 scored.**
  Nothing about the point moved between the two sessions; the only edits inside that directory were
  the addition of `neighbourhood.json` and a section appended to `README.md` describing it, both made
  before trial #43 was journaled, so the declared sweep and the falsification re-run ran against one
  fixed candidate state. The declared nominee coordinates equal the frozen source's constants, which
  is what the coordinate rule checks and what `--check` confirmed before either trial was appended.
- `risk_policy.json` declares `volatility_target.enabled: false` and has since the first trial, so
  the ban recorded in the amendments costs this candidate nothing. It was verified rather than
  assumed: `--check` accepts the policy, and the same flat policy is what every number in §5 was
  produced under.
- The one methodological point worth raising with the organiser, offered as an observation rather
  than a complaint: the trial-adjusted confidence floor at the *minimum* trial count of eight
  requires an in-sample Sharpe of roughly 1.17 on a four-year window, on a neighbourhood median.
  A team that spends its full twelve needs about 1.25. That is a high bar for an unlevered book held
  to 10% volatility, ≤ 25× turnover and ≤ 20% drawdown simultaneously, and it may be that the floor
  is binding on more lanes than intended. This team's finding is not that the bar is wrong — it is
  that this mechanism does not clear it, and that is what is being reported.

## 9. What this candidate is, and what it is not — the closing statement

It is a directional trend book with a run-structure admission gate, held to a common risk unit, and
its evidence base is: an ablation that removes the gate and costs 0.67 of net Sharpe; an inversion
that fails six of eight core floors; eight placebos that reach a twentieth of its gross edge density;
and a thirteen-point declared plateau on which all four folds are positive at 2× cost and every
single point makes money at two cost levels.

It is **not** a book that clears the charter's floors. It misses two, it will still miss them if it
advances, and the honest summary of why is short: it trades 14% more than the turnover ceiling
because the risk unit couples turnover to volatility on a book like this, and its bootstrap fraction
is 0.9665 where 0.9909 is needed at this trial count, which is a statement about how much edge a
four-year window can demonstrate rather than about a repairable defect. §0 concluded from those two
facts that there was no submission here. Under floors that gate, §0 was right. Under a score that
ranks, the same two misses cost 5.49 points out of 100, and the book that remains is one whose worst
regime year still made money after double costs.

The load-bearing risk in this candidate, stated so that nobody has to find it: **F3 — the FTX trough
and the range that followed — is +0.09 at 2× cost on the median.** Positive, and thin. It is the
fold that sets the largest term in the score, it is the fold that is weakest at every rung of the
cadence ladder and in every ablation, and if this book has a regime it cannot survive, that is what
it looks like. A holdout containing a long, low-volatility, two-sided range is the observation that
would falsify it, and this certificate would rather say so in advance than explain it afterwards.
