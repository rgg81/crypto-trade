# CUP-20 — team-07 research certificate

**Lane:** funding carry with crowding-crash protection.
**Nomination:** `candidates/carry-crowd-guard`.
**Accepted trials:** 9 of 12 — journal sequences **#68–#76**, every one listed below.
**Nominee fixed before the neighbourhood was declared:** yes — the constants were frozen and
`--check` clean before `neighbourhood.json` existed; the declaration was journaled at #75 after
the nominee's own point trial #68.

**Score (neighbourhood median, trial #75): net Sharpe 0.9225 at 1×, 0.6384 at 2×, all four folds
positive at 2× with a worst fold of +0.271, maximum drawdown 0.1655, realised volatility 0.1113,
35 071 executed trades, 9 of 9 neighbourhood points positive, `G` = 29.820.** Both substance gates
and both integrity gates pass; the falsification battery (#76) is clean in both halves. Three
performance floors are missed and are itemised in §9: turnover, gross edge per unit turnover, and
trial-adjusted confidence.

---

## 0. The finding, stated first

The carry is real and the protection is not.

A dollar-neutral cross-sectional funding-carry book on the point-in-time top-20, sized by
carry-to-risk, earns a 1× net Sharpe of **0.97** with **all four fold Sharpes positive at 2× cost**
and a 16.6% maximum drawdown. Its funding leg is the same size in every fold; its price leg carries
all of the fold variation.

The crowding mechanism the lane exists to test — read funding level, persistence and premium
duration, and stand aside before the unwind — **does not add anything on this window, and destroys
the book whenever it is strong enough to remove a position.** Seven distinct implementations were
tried. Six are harmful, monotonically in their own strength. The seventh, a soft weight guard,
moves 1× Sharpe by **−0.004** against the identical book with it switched off — indistinguishable
from zero, and the same size as the noise from shifting the rebalance by one 8h boundary. Doubling
its strength inside the declared sweep (λ = 0.40 → 0.80) moves 1× Sharpe by **0.009**.

The reason is measurable rather than rhetorical: the crowding signal and the carry signal are
**+0.471 rank-correlated in the cross-section**. They are largely the same number, exactly as the
mandate warned, and on this universe the separation does not exist. Standing aside from the crowd
means standing aside from the carry.

I nominate the guarded book anyway, and say plainly why: the guard is free rather than earned. It
caps concentration in the most entrenched shorts at no measured cost, which is a property I want in
a short-volatility book facing a window this one did not contain. It is not the source of the
edge, and this certificate does not claim it is.

---

## 1. The mechanism, and what the data said before any book existed

Perpetual funding is a cashflow the crowded side pays. Binance's rate is a premium index plus an
interest component clamped at 0.01% per 8h, so `funding > 0.0001` means the contract genuinely
traded above its index rather than merely paying the resting rate. That threshold is a fact about
the contract, not a fitted parameter, and it is the only threshold in the book.

Measured on the in-sample snapshot, 20-name point-in-time universe, 4335 8h decisions from
2020-08-17:

- Median funding is **exactly 0.000100** — the clamp. Mean annualised funding across eligible names
  **+13.3%**; 5th percentile −24%, 95th +81%.
- Funding is strongly persistent. Cross-sectional rank autocorrelation **+0.60** at one boundary,
  **+0.45** at six, **+0.34** at 21, **+0.26** at 63.
- Trailing mean funding predicts forward price return with rank IC **≈ −0.018**, stable at every
  lookback from 1 to 63 boundaries. Small, but signed the *same way as the carry*: the rich-funding
  names also drift down, so the price and funding legs of a carry book point in the same direction
  rather than fighting.

### The decomposition that determined the whole design

Equal-weight top-6 carry sleeves, cadence 9, per fold (team's own approximate simulator):

| fold | price leg | funding leg | cost | net |
|---|---:|---:|---:|---:|
| F1 | −0.050 | **+0.058** | −0.015 | −0.006 |
| F2 | +0.050 | **+0.058** | −0.014 | +0.094 |
| F3 | −0.006 | **+0.061** | −0.014 | +0.041 |
| F4 | −0.006 | **+0.035** | −0.015 | +0.015 |

The funding leg is a constant. The price leg is the entire fold variance. Beta of that price leg to
the equal-weight universe is **−0.022**, explaining **0.8%** of its variance, so the noise is
idiosyncratic cross-sectional dispersion and not market direction — beta-hedging was dropped
immediately.

Everything after that point is an attempt to reduce price-leg variance without touching the funding
leg. One thing worked, and it is a risk transform rather than a signal: split the cross-section by
each name's own realised volatility and the carry spread's forward return is **+26.6 bps (t = 2.51)**
among low-volatility names, +5.0 among mid, **−5.7** among high. Ranking on `(f − median f)/σ` and
sizing at `1/σ` is the response, and it is what turns a Sharpe-0.55 book into a Sharpe-0.97 one
(§4, trial #70 vs #68).

---

## 2. The nominated book

`candidates/carry-crowd-guard/strategy.py`. At every second 8h boundary (`None` in between, so
positions are held rather than re-targeted):

```
carry_i   = mean funding over the last CARRY_LOOKBACK = 63 settlements
sigma_i   = stdev of the last RISK_LOOKBACK = 63 bar close-to-close returns
score_i   = (carry_i - median carry) / sigma_i
shorts    = the SLEEVE_NAMES = 7 highest score;  longs = the 7 lowest
w_i       = +/- 1 / sigma_i
crowd_i   = fraction of the last CROWDING_LOOKBACK = 63 settlements with funding > 0.0001
w_i      *= clip(1 - CROWDING_PENALTY * crowd_i, 0, 1)      for shorts only, penalty 0.60
each sleeve normalised to equal gross  ->  dollar neutral by construction
```

`risk_policy.json` declares nothing: `volatility_target.enabled = false` (charter §6, amendment
A3 — and see §8 below on the target I declined even before it was banned), no drawdown brakes, no
stops, no turnover limit, no side scaling. Scale is the organiser's; shape is mine.

**Declared roles: `long,short`.** Both sleeves trade at every rebalance and carry equal gross.
Observed roles agree at every trial.

---

## 3. Causality — how I verified there is no funding look-ahead

This lane's characteristic failure is a carry signal reading the settlement it is about to be paid.
`research/lookahead_audit.py` establishes, on the snapshot itself:

- **A.** Every `funding_time` in the snapshot lands at or **after** its nominal boundary — minimum
  offset 0.000 s, **zero negative offsets** across 201,036 rows. A settlement stamped at boundary
  `T` therefore never has a timestamp below `T`, and the harness's strictly-before filter excludes
  it at the decision at `T`. There is no jitter case in which the current boundary's rate leaks in.
- **B.** Sampling 41 decisions across the window, the smallest gap between the decision instant and
  the newest readable settlement is **2.000 hours**, strictly positive at every one.
- **C.** A position opened by the decision at `T` fills at `open[T]` and is held to `open[T+8h]`, so
  the funding it pays settles at `T+8h`. The newest rate the book can read settles at `T−8h`.
  **The signal is two full boundaries behind the cashflow it earns.** Nothing about the book's own
  future funding is observable when it sizes the position.
- **D.** Bars are admitted on `close_time <= T`, so the bar `[T, T+8h)` whose open is the fill price
  is never visible. Bar length is a constant 28,799.999 s.
- **E.** The frozen source reads exactly three things: `context.eligible_symbols`,
  `context.funding['funding_time','symbol','funding_rate']` and `context.bars[sym]['close']`. No
  open, no mark, no auxiliary frame, no equity, no fill, no cost. A grep of the frozen file is in
  the audit output.

Two further points of hygiene:

- The book **counts settlements rather than calendar days**, so nothing about it depends on how the
  organiser buckets timestamps. Two symbols (ORDIUSDT, WIFUSDT) settle 4-hourly — 0.29% of funding
  rows — and for them a 63-settlement lookback spans fewer calendar days than for the rest. That is
  an inhomogeneity, disclosed here, not a leak.
- Funding history is accumulated incrementally, and because the context filters funding to the
  *currently eligible* names, a symbol that leaves and rejoins the universe would otherwise carry a
  hole. The ingest rebuilds any name not covered through the previous call's horizon rather than
  appending to it (`_ingest`, strategy.py). This is a correctness fix, not a performance one, and
  it can only ever discard state, never manufacture it.

I did not reimplement funding PnL, and the book expresses no opinion about how funding settles. The
organiser's accounting is the only accounting used anywhere in this certificate.

---

## 4. Every trial, with its sequence number

All nine are point/neighbourhood/falsification runs of the organiser's own evaluator on the full
in-sample window. Metrics are that evaluator's; `G` is its indicative ranking score at the trial
count in force when the run happened.

| # | candidate | what it changes vs the nominee | 1× Sharpe | 2× Sharpe | fold Sharpes (2×) | worst | maxDD 1× | G |
|---|---|---|---:|---:|---|---:|---:|---:|
| **68** | **carry-crowd-guard** | **— (nominee)** | **0.974** | **0.697** | **0.371 / 1.292 / 0.528 / 0.735** | **+0.371** | **0.166** | **41.19** |
| 69 | carry-guard-off | `CROWDING_PENALTY = 0.00` | 0.978 | 0.704 | 0.467 / 1.288 / 0.527 / 0.650 | +0.467 | 0.164 | 43.41 |
| 70 | carry-controls-off | `CROWDING_PENALTY = 0`, `RISK_SIZING = 0` | 0.547 | 0.321 | 0.029 / 0.806 / 0.707 / −0.142 | −0.142 | 0.201 | 3.77 |
| 71 | carry-guard-veto | `CROWDING_PENALTY = 1.00` | 0.848 | 0.564 | −0.199 / 1.320 / 0.531 / 0.884 | −0.199 | 0.167 | 18.27 |
| 72 | carry-cadence-1 | `REBALANCE_CADENCE = 1` | 0.902 | 0.563 | 0.365 / 0.910 / 0.353 / 0.712 | +0.353 | 0.160 | 31.28 |
| 73 | carry-phase-1 | `REBALANCE_PHASE = 1` | 0.860 | 0.596 | 0.447 / 0.703 / 0.692 / 0.582 | +0.447 | 0.152 | 34.57 |
| 74 | carry-guard-only | `RISK_SIZING = 0` | 0.533 | 0.304 | −0.053 / 0.804 / 0.708 / −0.109 | −0.109 | 0.202 | 2.80 |
| 75 | carry-crowd-guard | declared 9-point neighbourhood sweep | *see §6* | | | | | |
| 76 | carry-crowd-guard | falsification battery | *see §7* | | | | | |

Every variant is the nominee's `strategy.py` with the named module constants rewritten and every
other byte identical, so "nothing else changed" is literal.

**No trial was abandoned and none crashed.** All nine produced a packet, all nine are in
`research/packets/`. Nothing was journaled and then discarded, and nothing was evaluated without
being journaled first.

---

## 5. The ablation at the centre of this lane

### 5.1 Protection on versus protection off (#68 vs #69)

| | guard on (λ = 0.60) | guard off (λ = 0.00) | difference |
|---|---:|---:|---:|
| net Sharpe 1× | 0.9744 | 0.9779 | **−0.0035** |
| net Sharpe 2× | 0.6972 | 0.7041 | −0.0069 |
| annualised return 1× | 10.78% | 10.83% | −0.05 pp |
| maximum drawdown 1× | 0.1655 | 0.1641 | +0.0014 |
| worst fold Sharpe 2× | +0.371 | +0.467 | −0.096 |
| positive folds | 4 of 4 | 4 of 4 | — |
| short-sleeve gross PnL | +0.027 | +0.031 | −0.004 |
| `G` | 41.19 | 43.41 | −2.22 |

**They perform alike.** The Sharpe difference is 0.4% of the level. The only visible movement is in
the worst fold, and it is not a movement the guard can claim: the *same book* on the other
rebalance phase (#73) has a worst fold of **+0.447** against #68's +0.371. The guard's entire
apparent effect on the ranking's largest term (−0.096) is the same size as the noise from shifting
the rebalance by one 8h boundary (+0.076), and the declared sweep settles it independently: at
λ = 0.40 and λ = 0.80 the book's 1× Sharpe is 0.9765 and 0.9674, so **doubling the guard's strength
is worth 0.009 of Sharpe**.

I ran the ablation expecting the opposite. My own approximate simulator, over four cadences and
every phase offset, had shown the guard raising the neighbourhood median monotonically from λ = 0 to
λ = 0.8 (`research/NOTES.md` §4). On the organiser's harness at the nominated point, it does not.
The two disagree about the sign of a 0.004-Sharpe effect, which is the correct thing for two
estimators to disagree about, and the organiser's is the one that counts.

**Conclusion: the lane's premise is unsupported on this window.** A crowding signal built from
funding level, funding persistence and premium duration does not tell you to stand aside before the
unwind in any way that shows up in the book.

### 5.2 Why it fails, measured rather than asserted

The crowding measure's cross-sectional rank correlation with the carry signal is **+0.471**; with
the carry-to-risk score, **+0.458**. Standing aside from the crowd is standing aside from the carry.
Two orthogonal channels were checked as alternatives and neither produced a usable signal: the
perp-versus-mark premium is **+0.024** correlated with carry (genuinely orthogonal, but its
cross-sectional rank autocorrelation is −0.03 at one boundary — it is noise, not a state), and
funding acceleration is −0.175 correlated and did not improve any book.

### 5.3 The cliff — protection as a filter (#71)

Push the same guard to `CROWDING_PENALTY = 1.00`, at which a name that traded at a premium in every
one of the last 63 settlements reaches exactly zero weight and leaves the book, and it stops being
free:

- 1× Sharpe **0.848** (from 0.974), 2× **0.564** (from 0.697)
- worst fold **−0.199** (from +0.371) — F1 flips negative
- short-sleeve gross PnL **−0.035** — the short sleeve stops being viable standalone
- `G` **18.27** (from 41.19)

Six independent implementations of "stand aside" behave the same way, monotonically in their own
strength (measured on the team's simulator, `research/NOTES.md` §4): a hard persistence veto on the
shorts (42.4 → −27.8), the symmetric version (42.4 → −3.4), an aggregate go-flat brake on
market-wide premium duration (42.4 → −21.5, and it did not reduce drawdown at all — 16.3% either
way), skipping the k richest-carry shorts (43.1 → −18.7), skipping the k most entrenched shorts
(43.1 → −7.2), and a carry-adequacy gate that stands aside when the cross-section is not paying
enough (which takes realised volatility to **3.6%** and fails the substance floor outright).

The single coherent statement across all seven forms: **the most crowded names must stay in the
book at parity weight.** They are the carry. Removing them removes the only part of the return that
does not vary across regimes. Sizing them down is affordable; excluding them is not.

### 5.4 Controls-off and individual controls (#70, #74)

The book has two controls. §9.1 asks for all four corners:

| corner | risk control | crowding guard | 1× Sharpe | worst fold | short gross | G |
|---|---|---|---:|---:|---:|---:|
| controls off (#70) | off | off | 0.547 | −0.142 | −0.048 | 3.77 |
| individual: guard only (#74) | off | on | 0.533 | −0.109 | −0.052 | 2.80 |
| individual: risk only (#69) | on | off | 0.978 | +0.467 | +0.031 | 43.41 |
| combined (#68) | on | on | 0.974 | +0.371 | +0.027 | 41.19 |

Unambiguous. **Carry-to-risk sizing is worth +0.43 of Sharpe and moves the worst fold from −0.14 to
+0.47.** The crowding guard is worth −0.014 without it and −0.004 with it. The guard is inert in
both directions; the risk control is the book.

This corner table is also the answer to a question I would otherwise be tempted to duck: without
carry-to-risk sizing, the raw carry book's **short sleeve is gross-negative** (−0.048) and it fails
the standalone-viability floor. The transparent baseline for this lane is not a viable book on its
own.

### 5.5 Rebalance horizons and the phase axis (#72, #73)

Two rebalance horizons were journaled. Cadence 1 has no phase offset to sweep; cadence 2 has two
and both were run.

| | 1× Sharpe | worst fold 2× | turnover | G |
|---|---:|---:|---:|---:|
| cadence 1 (#72) | 0.902 | +0.353 | 50.4× | 31.28 |
| cadence 2, phase 0 (#68) | 0.974 | +0.371 | 41.1× | 41.19 |
| cadence 2, phase 1 (#73) | 0.860 | +0.447 | 40.5× | 34.57 |

**Cadence 2 was chosen for a mechanism reason, not a score reason.** The decision grid is three
boundaries a day, so cadences 3 and 6 *divide* it and lock every rebalance to a single UTC hour —
which is a bet on the settlement clock and belongs to a different mandate. Cadence 2 does not
divide it: both phases visit 00:00, 08:00 and 16:00 equally. Measured on the team's simulator, the
neighbourhood median across phases has standard deviation **0.1 at cadence 2** against **8.8 at
cadence 3** and **6.1 at cadence 6** — and cadence 3 phase 0 was the single highest-scoring
configuration I found anywhere. I did not take it.

The two organiser-measured cadence-2 phases differ by 6.6 of `G` and by 0.096 of worst-fold Sharpe,
which is the noise scale that §5.1's ablation has to be read against.

### 5.6 Formation horizons

Three, all journaled inside the declared sweep (#75): `CARRY_LOOKBACK` ∈ {48, 63, 84} settlements,
i.e. 16, 21 and 28 days. The team's own simulator additionally covered 9, 21, 42, 90, 126 and 189;
the surface has a broad interior optimum near 63 and collapses below 21 (`G*` −34 at
`CARRY_LOOKBACK = 9`, where the signal is one day of funding and the turnover is 56× annualised).

### 5.7 Long, short and chop role checks

Roles are observed, not declared: at every trial the packet's `declared_roles_match_traded_sides`
gate passed with declared `['long','short']` and traded `['long','short']`.

Standalone viability at the nominee (#68): long sleeve gross PnL **+0.523**, short sleeve
**+0.027**. Both positive, so the book clears charter §14.9's standalone-viability test — but the
short sleeve clears it by very little, and **that margin is phase-dependent**: the same book on
phase 1 (#73) has short-sleeve gross PnL of **−0.051**. On a window whose equal-weight top-20
basket returns +199%, a gross-positive short sleeve is a knife-edge property of this book rather
than a robust one, and I would not claim otherwise.

Chop: splitting the window into terciles of the *trailing* 63-boundary market return (team's
simulator; buckets labelled by that trailing trend, low → high):

| trailing-trend tercile | book net /yr | book Sharpe | price leg | funding leg |
|---|---:|---:|---:|---:|
| low | +21.1% | +2.08 | +0.225 | +0.089 |
| mid | +0.1% | +0.01 | −0.025 | +0.066 |
| high | +7.8% | +0.66 | +0.070 | +0.069 |

The funding leg is +0.066 to +0.089 in all three; the price leg is what varies, and in the middle
bucket it is slightly negative and the carry alone carries the book to flat. **The book does not
lose money in chop; it stops earning on price and lives on the carry** — which is the behaviour a
carry mandate should have. By trailing-volatility tercile the annualised net is +21.0% / +1.3% /
+6.6%: positive in all three, including the stressed one, and again with the funding leg
(+0.070 / +0.078 / +0.076) flat across them.

---

## 6. The declared neighbourhood and its sweep (#75)

Declared **after** the nominee was frozen and journaled (#68), and validated by the free `--check`
before the trial was appended.

Coordinates: `CARRY_LOOKBACK`, `RISK_LOOKBACK`, `SLEEVE_NAMES`, `CROWDING_PENALTY` — k = 4, so 9
points including the nominee. Every one is a module-level plain numeric literal named identically
to the coordinate, with the nominee's declared value equal to the frozen source's.

| point | CARRY | RISK | NAMES | PENALTY | variation |
|---|---:|---:|---:|---:|---|
| nominee | 63 | 63 | 7 | 0.60 | — |
| 1 | 48 | 63 | 7 | 0.60 | −23.8% |
| 2 | 84 | 63 | 7 | 0.60 | +33.3% |
| 3 | 63 | 48 | 7 | 0.60 | −23.8% |
| 4 | 63 | 84 | 7 | 0.60 | +33.3% |
| 5 | 63 | 63 | 6 | 0.60 | −14.3% |
| 6 | 63 | 63 | 8 | 0.60 | +14.3% |
| 7 | 63 | 63 | 7 | 0.40 | −33.3% |
| 8 | 63 | 63 | 7 | 0.80 | +33.3% |

All distinct, all material, one strictly above and one strictly below on every coordinate, all
finite. None is quantised: `SLEEVE_NAMES` moves by a whole name, the two lookbacks change the
rolling windows, and `CROWDING_PENALTY` scales every short weight continuously.

**Disclosure about the fourth coordinate.** `CROWDING_PENALTY` is a *flat* axis — that is this
certificate's headline finding — so points 7 and 8 sit close to the nominee in metric space and
pull the per-metric median toward it, relative to a three-coordinate declaration in which every
point moves the book more. The declaration is legal on every §7.2 rule and was written before the
sweep ran, but a reader should know that a nine-point set containing two near-flat variations is a
gentler test than a seven-point set of sharp ones. On the team's own simulator, the same nominee's
three-coordinate seven-point median is **38.7** against the four-coordinate nine-point median of
**42.5**; the difference is the dilution, and it is roughly 4 points of `G`.

**Sweep result — this is the score.** 9 points, 4 workers, 1856.9 s.

| point | CARRY | RISK | NAMES | PENALTY | 1× Sharpe | 2× Sharpe | ann return | maxDD | trades |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| nominee | 63 | 63 | 7 | 0.60 | 0.9744 | 0.6972 | 0.1078 | 0.1655 | 35103 |
| 1 | **48** | 63 | 7 | 0.60 | 0.4171 | 0.1018 | 0.0406 | 0.1460 | 35668 |
| 2 | **84** | 63 | 7 | 0.60 | 0.7847 | 0.5363 | 0.0817 | 0.1706 | 34579 |
| 3 | 63 | **48** | 7 | 0.60 | 0.9225 | 0.6384 | 0.1021 | 0.1630 | 35075 |
| 4 | 63 | **84** | 7 | 0.60 | 0.9651 | 0.7011 | 0.1068 | 0.1721 | 35028 |
| 5 | 63 | 63 | **6** | 0.60 | 0.9063 | 0.6298 | 0.0988 | 0.1700 | 30048 |
| 6 | 63 | 63 | **8** | 0.60 | 0.7898 | 0.5199 | 0.0836 | 0.1588 | 40332 |
| 7 | 63 | 63 | 7 | **0.40** | 0.9765 | 0.7007 | 0.1079 | 0.1649 | 35067 |
| 8 | 63 | 63 | 7 | **0.80** | 0.9674 | 0.6879 | 0.1072 | 0.1664 | 35071 |

**Per-metric median — the scored vector:**

| metric | median | floor | |
|---|---:|---:|---|
| net Sharpe 1× | **0.9225** | ≥ 0.80 | PASS |
| net Sharpe 2× | **0.6384** | ≥ 0.50 | PASS |
| net Sharpe 3× | 0.3545 | > 0 | PASS |
| annualised return 1× | 0.1021 | > 0 | PASS |
| annualised return 2× | 0.0676 | > 0 | PASS |
| maximum drawdown 1× | 0.1655 | ≤ 0.20 | PASS |
| maximum drawdown 2× | 0.1716 | — | ranking input |
| realised annualised volatility | **0.1113** | ≥ 0.06 | **PASS (substance)** |
| positive-quarter fraction 1× | 0.7647 | ≥ 0.50 | PASS |
| positive-quarter fraction 2× | 0.7059 | — | ranking input |
| positive folds | **4 of 4** | ≥ 3 | PASS |
| worst fold Sharpe 2× | **+0.2706** | ≥ −0.25 | PASS |
| median fold Sharpe 2× | +0.5681 | — | ranking input |
| Calmar 2× | 0.3985 | — | ranking input |
| long / short gross PnL | +0.4947 / **+0.0274** | each > 0 | PASS |
| annualised one-way turnover | 40.83 | ≤ 25 | **FAIL** |
| gross edge per unit turnover | 32.07 bps | ≥ 40 | **FAIL** |
| cost share of positive gross | 0.0233 | ≤ 0.30 | PASS |
| five largest days' share | 0.0277 | ≤ 0.35 | PASS |
| largest fold's share of positive PnL | 0.2712 | ≤ 0.60 | PASS |
| executed trades | **35 071** | ≥ 500 | **PASS (substance)** |
| neighbourhood points positive | **9 of 9 = 1.000** | ≥ 0.70 | PASS |
| trial-adjusted confidence | 0.7300 (B = 0.970, T = 9) | ≥ 0.90 | **FAIL** |

**Indicative ranking score `G` = 29.820.** Its decomposition, recomputed with the organiser's own
`robustness_score` and `compliance_factor`:

| term | weight | value |
|---|---:|---:|
| worst fold Sharpe 2× | 30 | +15.617 |
| median fold Sharpe 2× | 20 | +8.481 |
| maximum drawdown 2× | 20 | +3.790 |
| Calmar 2× | 15 | +3.985 |
| positive quarters 2× | 8 | +4.392 |
| trial-adjusted confidence | 7 | **−4.407** |
| | | **31.858** |
| × amendment A5 compliance factor | | **× 0.936** |
| | | **29.820** |

The A5 factor is 0.936 because two unpriced floors are missed: turnover earns credit 0.367 and
gross edge per turnover earns 0.802; all eleven others earn 1.000. **My turnover costs me about
two points of `G` directly**, on top of what it costs through cost drag.

Three observations I owe the record:

1. **The median is 0.05 of Sharpe below the nominee** (0.9225 vs 0.9744) and the worst fold is
   0.10 below (+0.271 vs +0.371). That gap is what §7.2 exists to charge, and it is charged.
2. **Point 1 (`CARRY_LOOKBACK = 48`) is the whole cost.** It scores 1× Sharpe 0.417 against the
   nominee's 0.974 — the carry surface falls off a cliff somewhere between 48 and 63 settlements,
   which my own simulator had shown as a gradient rather than a cliff. Sixteen days of funding is
   not enough history to rank a cross-section on; twenty-one is. Had I known the shape this sharply
   I would have nominated a longer lookback with more room below it, and the honest reading is that
   my nominee sits nearer the edge of its plateau than I believed when I froze it.
3. **`CROWDING_PENALTY` is measurably the flattest axis**, exactly as §5 says: points 7 and 8
   (λ = 0.40 and 0.80) return 1× Sharpe 0.9765 and 0.9674 against the nominee's 0.9744. The guard
   does nothing across a doubling of its own strength. That is the cleanest single piece of
   evidence in this certificate that the lane's protection thesis is unsupported — and, as §6's
   disclosure says, it is also why those two points lift the median relative to a
   three-coordinate declaration. Both facts are the same fact.

**A1 inertness: no point reproduced the nominee's metric vector.** All nine differ; the sweep did
not report an inert point and was not void.

---

## 7. Falsification battery (#76)

Run by the organiser's harness, not by me, on the **nominated point**. 3440.6 s.

### 7.1 Exact sign inversion — `sign_inversion_not_profitable` **PASSES**

Every emitted weight negated, `None` and `{}` untouched, scored through the identical pipeline
against the eight core floors:

| core floor | inverted book | verdict |
|---|---:|---|
| net Sharpe 1× | **−1.5214** | fails |
| net Sharpe 2× | −1.7975 | fails |
| net Sharpe 3× | −2.0731 | fails |
| annualised return 1× | **−16.09%** | fails |
| annualised return 2× | −18.62% | fails |
| maximum drawdown | **0.5246** | fails |
| realised annualised volatility | 0.1112 | clears |
| executed trades | 35 032 | clears |

Six of eight core floors fail, and the two that clear are the substance floors that any book
trading this much and this volatile would clear in either direction. **The inversion is not merely
unprofitable; it is the mirror image of the book, losing 16% a year with a 52% drawdown.** The
apparent edge is directional, not a construction artifact of the harness.

This one matters more in this lane than in most, and for a reason worth stating: **the inverted
book is a book that pays funding.** It is long the crowded names and short the uncrowded ones, so
it hands the carry to its counterparty at every settlement. Had it cleared the core floors, the
edge would have been coming from something other than the carry — cost asymmetry, cap asymmetry, or
the harness. It does not, and by a wide margin, which is the strongest available evidence that what
this book earns is the cashflow it says it earns.

### 7.2 Gross-edge placebo — no exceedance

Eight placebo books preserving the candidate's weight multiset and rebalance schedule exactly and
randomising only *which* eligible symbol receives which weight, scored on gross edge:

| | bps per unit one-way turnover |
|---|---:|
| candidate | **33.854** |
| placebo minimum | −2.960 |
| placebo median | −0.912 |
| placebo maximum | 3.024 |
| **exceedance** | **0.0000** — 0 of 8 |

The placebos centre near zero and the best of eight reaches 3.0 bps against the candidate's 33.9.
The edge is in *which name gets which weight* — the funding cross-section — and not in the book's
weight distribution, its gross, its turnover or its schedule.

---

## 8. Everything else I tried, and why it is not in the book

Unjournaled, on the team's approximate simulator; full tables in `research/NOTES.md`.

- **Beta-hedging the price leg.** Abandoned on measurement: beta −0.022, 0.8% of variance.
- **Continuous / soft-threshold weighting** instead of equal-weight sleeves. Monotonically worse as
  the tilt concentrates on the extreme carry names. Combined with the skip-the-richest results of
  §5.3 this says the return to carry is **concave**: the extreme names belong in the book, at
  parity weight, neither over-weighted nor removed.
- **Blending the carry across lookbacks** (21/63/126 rank average). Worse at every breadth.
- **Overlapping tranches** (average the last m target books). Lowered Sharpe monotonically.
- **Hysteresis on sleeve membership.** `G*` across buffer widths 0–6: 43.1, 36.7, 26.8, 35.8, 6.0,
  33.3, 31.7. No plateau — pure noise. Rejected.
- **A realised drawdown brake in `risk_policy.json`.** One brake at 10%/0.5 took `G*` from 42.4 to
  52.3, the largest single improvement I found. Declined: it engages in **two episodes** across the
  window, and phase dispersion rose from ±5.0 to ±12.9 when it was on. Two effective observations
  is not evidence, and 20 of the ranking's 100 points sit on drawdown, which is exactly the
  circumstance in which a two-observation control should be distrusted. The risk policy is flat.
- **A declared volatility target.** Amendment A3 forbids it and the free `--check` refuses it, so it
  never cost a trial. For the record I had already measured the interaction it describes: the book
  is over the turnover floor and a smaller declared target is the paperwork route past it. I did
  not take that route before the ban and did not attempt it after.
- **A market vol-spike stand-aside gate.** `G*` 43.1 → 46.6 at a threshold binding on 225 of 4335
  boundaries, falling away at every tighter setting. Within noise; not adopted; also not a crowding
  mechanism, so adopting it would have been lane drift.

**No mechanism pivot was used.** The lane's mechanism was tested and its protection half was
falsified; the carry half survived and is what is nominated. That is a negative result inside the
mandate, not a move to a different one.

---

## 9. Known weaknesses of the nominated book

Stated because the ranking wants the book with its weaknesses on the record.

1. **Turnover.** 41.1× annualised one-way against a 25× floor — missed by 64%. Cost share of
   positive gross PnL is only 2.3%, so the book is not being eaten by fees, but it trades a great
   deal for the edge it extracts. Under amendment A4 this costs points rather than admission, and
   it appears in neither the §7.4 ranking inputs nor the §8 holdout eligibility list — but it is a
   real property of the object and it would matter on a paper desk. Slowing to cadence 6 clears the
   gross-edge floor and nearly clears turnover, at the price of the settlement-hour phase exposure
   §5.5 rejects.
2. **Gross edge per unit turnover.** 33.9 bps against a 40 bps floor. Same cause.
3. **The short sleeve is barely standalone-viable** (+0.027 gross) and goes negative on the other
   rebalance phase. §5.7.
4. **Concentration.** 14 of ~20 names, so the caps bind: the requested book was trimmed at 5 of
   2160 boundaries with a minimum scale of 0.47 (per-symbol cap), and the executed book at 46 of
   2160 with a minimum scale of 0.81 (gross cap). The risk-unit scalar ran at a median of 0.68 and
   hit its 3.0 ceiling never and its floor never (range 0.29–1.23), so the book is not being held
   back by the unlevered gross cap.
5. **The guard is decorative.** §5.1. It is in the frozen book because it is free and because it
   caps concentration in the most entrenched shorts, not because it earns anything measurable.
6. **Trial-adjusted confidence is 0.730 against a 0.90 floor**, on B = 0.970 and T = 9. Charter
   §14.10 records that a team at the eight-trial minimum needs B = 0.9875; a book of this Sharpe
   over this window cannot reach that, and neither could the all-folds-positive submission §14.10
   describes. I spent nine trials rather than eight because the ablation, the controls-off corner,
   the veto arm and the phase sweep are the evidence this lane was asked to produce; the ninth cost
   0.03 of confidence and about 0.3 of `G`, and I would spend it again.
7. **The whole result rests on one 4-year window** containing one alt-season, one bear and one
   bull. The funding leg's stability across those three regimes is the strongest thing in this
   certificate; the price leg's positivity in all four folds is the weakest, and is the part I
   would expect to shrink out of sample.

---

## 10. What I did not do

I did not open, read, resolve, reference or name any organiser-only or holdout artifact; the
workspace scan runs before every evaluation and reported **0 violations** at every trial (72 files
at the final check). I fetched no market data. I read no other team's directory and no prior tournament's. I
wrote nothing outside `tournament/cup20/teams/team-07/`. I retrieved no prior revision of anything
from version control. Every scored number in this certificate came out of
`scripts/cup20_evaluate.py`; every number from my own simulator is labelled as such and none of it
is presented as a result.
