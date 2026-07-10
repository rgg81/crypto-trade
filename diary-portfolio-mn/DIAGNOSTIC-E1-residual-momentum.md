# DIAGNOSTIC-E Stage 1 — Residualized Past-Return Horizon Map, 8h (MN track)

**Date:** 2026-07-10 · **Role:** QR · **Script:** `analysis/portfolio/mn_diag_e1_residmom.py`
(committed spec = PLAN.md §2 Sketch E′ Stage 1, run exactly as frozen; trial ledger: 20 grid cells)
**Data hygiene:** `mn_panel_health()` → OK (BTC grid T=7147 contiguous; live feeds current).
**Blinding/IS:** panel sliced via `mn_split.mn_slice_is` before any computation; `mn_guard_grid`
passed; IS = 2020-01-01 → 2025-12-31 (T=6,576 candles × 747 syms). Old-track `is_mask`/
`OOS_CUTOFF` never touched. Verification: DIAG-D's vectorized Spearman imported (not forked) and
re-cross-checked against `scipy.stats.spearmanr` on 300 random candles (max abs diff 2.22e-16).

## VERDICT — pre-registered kill criterion (PLAN §2 Sketch E′, verbatim)

> "KILL the stage if no cell has |IC| ≥ 0.02 with same-sign stability across IS halves AND
> 2×-cost coverage at the cell's natural cadence."

| Arm | Measured | Verdict |
|---|---|---|
| \|IC\| ≥ 0.02 + same-sign halves | **15 of 20 cells eligible** (max \|IC\| = 0.0485 at L=63,h=3 — all eligible cells REVERSAL) | passes |
| 2×-cost coverage at natural cadence, champion cell L=63,h=3 (rebal=3, phase-agnostic) | net2x_ann = **−244.8%** (gross −146.1%, funding −49.1%, 2× costs −49.7%) | **FAILS** |

**STAGE 1 IS KILLED.** The conjunction fails for every eligible cell, not just the champion:
all 15 eligible cells are reversal-signed, and the IC-oriented decile-tail spread is negative
or ~zero GROSS in every one of them (best case +2.95 bps/21c at L=189,h=21 ≈ +1.5%/yr before
funding and costs — an order of magnitude below its cost hurdle). The coverage arm was scored
at the per-sign champion per the frozen reporting scope; the map shows a fortiori that no
eligible cell could have passed. No post-hoc re-gating (PLAN §5.7). Stage-1 lookbacks and
thresholds die with the stage (PLAN §6). **Stage 2 (1h) remains registered and alive** —
different microstructure by pre-registration; it rides the §4.3 fetch.

---

## 0. Construction (as registered + implementation decisions on record)

- Universe: PIT top-40 by trailing 30-candle mean $-volume, ≥90d (270-candle) history —
  DIAG-A/D builder imported verbatim. Mean 36.6 members/candle; median 40 names used → k=4
  names per decile leg, book gross = 2.0. Top-20 = pre-registered robustness column.
- Residualization FIRST (the core of the sketch): r̃[t] = r[t] − β[t−1]·r_BTC[t] with
  β = `mn_beta.rolling_beta` FROZEN defaults (270/135/λ=0.33/clip[0,3]) at the [k−1] lag.
  Warmup respected: 135 all-NaN warmup rows excluded (NaN residual → strict all-finite
  machinery drops the row), never zero-filled. Residual coverage over member-candles = 99.9%.
- Signal_L[t] = trailing L-candle residual return, L ∈ {3, 9, 21, 63, 189}. **Implementation
  decision on record:** computed as the trailing L-candle MEAN of residual returns (min finite
  obs = L//2+1, the DIAG-A/D majority convention) — rank-identical to the cumulative sum at
  full coverage, robust to intra-window gaps. No skip candle (none registered).
- IC = per-candle Spearman of Signal_L vs forward h-candle residual-return sum, h ∈ {1,3,9,21},
  strict all-finite, min 20 members — the frozen 5×4 = 20-cell grid (family E1 n_eff = 20).
- **Raw-return map: checked the PLAN and NOT run.** Sketch E′ registers the map on RESIDUAL
  returns only ("All IC probes below use residual returns"); a raw twin map was not
  pre-registered and would have been 20 unledgered cells. The registered raw-vs-residual object
  is the sorted-spread beta before/after return-neutralization (§5 below, DIAG-D §10 harness).
- Cost machinery: DIAG-D harness imported — held-weights decile book, funding on every held
  leg, 7.5 bps/side × Σ|Δw|, 2×-twin, natural cadence rebal=h with FULL phase sweep
  (phase-agnostic headline, PLAN §5.5).
- t-stats: for h>1 forward windows overlap → naive t inflated ≈ √h; overlap-adjusted
  t_adj = t/√h reported alongside. The kill floor is on |IC| level, unaffected.

## 1. THE MAP — where reversal ends and momentum begins (top-40, full IS)

Spearman IC of trailing-L residual return vs forward-h residual return, PLUS the IC-oriented
decile-tail spread (bps per h candles) — both reported per the DIAG-D lesson (rank IC and
dollar tails can disagree; here they do, systematically):

| cell | mean IC | t (t_adj) | sign | tail spread mean | median | %pos | t(sp) |
|---|---|---|---|---|---|---|---|
| L=3, h=1 | −0.0254 | −8.3 (−8.3) | REV | −9.58 | +5.09 | 50.7% | −1.73 |
| L=3, h=3 | −0.0157 | −5.2 (−3.0) | REV | −27.34 | −7.50 | 49.4% | −2.87 |
| L=3, h=9 | −0.0081 | −2.8 (−0.9) | REV | −30.80 | −13.87 | 49.4% | −2.12 |
| **L=3, h=21** | **+0.0068** | +2.4 (+0.5) | **MOM** | **+75.40** | +40.18 | 51.4% | +3.78 |
| L=9, h=1 | −0.0262 | −8.5 (−8.5) | REV | −13.11 | +3.26 | 50.7% | −2.30 |
| L=9, h=3 | −0.0298 | −9.7 (−5.6) | REV | −32.05 | −3.46 | 49.8% | −3.24 |
| L=9, h=9 | −0.0226 | −7.6 (−2.5) | REV | −85.84 | −21.03 | 49.1% | −5.77 |
| L=9, h=21 | −0.0078 | −2.7 (−0.6) | REV | −122.68 | −55.86 | 48.2% | −6.05 |
| L=21, h=1 | −0.0356 | −11.3 (−11.3) | REV | −19.31 | +7.89 | 51.0% | −3.39 |
| L=21, h=3 | −0.0434 | −13.9 (−8.0) | REV | −45.75 | +11.57 | 51.0% | −4.65 |
| L=21, h=9 | −0.0337 | −11.0 (−3.7) | REV | −101.67 | −15.67 | 49.1% | −6.87 |
| L=21, h=21 | −0.0192 | −6.4 (−1.4) | REV | −149.18 | −43.95 | 48.8% | −7.45 |
| L=63, h=1 | −0.0395 | −12.4 (−12.4) | REV | −14.30 | +10.39 | 51.7% | −2.57 |
| **L=63, h=3** | **−0.0485** | −14.9 (−8.6) | **REV** | **−38.46** | +9.34 | 50.7% | −3.95 |
| L=63, h=9 | −0.0363 | −11.3 (−3.8) | REV | −72.89 | −7.56 | 49.7% | −4.84 |
| L=63, h=21 | −0.0287 | −9.4 (−2.0) | REV | −140.47 | −22.96 | 49.2% | −6.74 |
| L=189, h=1 | −0.0373 | −11.9 (−11.9) | REV | −7.97 | +11.63 | 51.8% | −1.54 |
| L=189, h=3 | −0.0476 | −14.9 (−8.6) | REV | −20.94 | +14.06 | 51.3% | −2.32 |
| L=189, h=9 | −0.0403 | −12.7 (−4.2) | REV | −29.69 | +2.56 | 50.1% | −2.07 |
| L=189, h=21 | −0.0429 | −13.7 (−3.0) | REV | +2.95 | +79.92 | 52.5% | +0.15 |

**Shape of the map.** In RANK space the residual 8h cross-section is reversal almost
everywhere: 19/20 cells REV, strengthening with lookback (L=63/189 ICs ≈ −0.04 to −0.05,
t < −12 — the strongest rank signal any MN diagnostic has measured, 2.4× the kill floor). The
single momentum cell is L=3,h=21 (recent 1-day residual moves revert inside 1–3 days, but what
survives 3 days continues over 3 weeks) at IC +0.0068 — 3× BELOW the registered floor. In
DOLLAR-TAIL space the picture inverts: the oriented tail spread DISAGREES with the rank IC in
most cells (negative mean, positive median at h≤3; deeply negative at h≥9), i.e. the extreme
deciles CONTINUE while the mid-ranks revert. At L=189,h=21 the disagreement peaks: rank IC
−0.043 (t −13.7) yet the oriented tail spread is +2.95 bps mean / +79.92 bps MEDIAN — the tails
run opposite the ranks half the time and the rest is episodic. This is DIAG-D's two-layer
structure replicated on an independent signal: **per-candle mid-rank mean-reversion + episodic
extreme-tail continuation is a structural property of the 8h residual cross-section**, not a
taker-flow artifact.

## 2. IS halves + regime buckets (all cells)

- Halves (2020-22 / 2023-25): 19/20 cells same-sign; only L=9,h=21 flips (+0.0075/−0.0214) —
  correctly excluded from eligibility. The reversal ranks are era-stable, unlike DIAG-D's.
- Buckets: reversal IC is strongest in CRASH and grows with lookback there (L=63,h=21: −0.107;
  L=189,h=21: **−0.128**, t −13.1) — forced-flow reversal ranks best when liquidations run.
  MANIA is the weak bucket at short L (L=3,h=9/21 flip positive: +0.008/+0.018 — mania chases
  continue); CHOP tracks the full-sample sign everywhere.
- Eligible cells (|IC| ≥ 0.02 AND same-sign halves): 15, ALL reversal. Champion REV = L=63,h=3.
  Champion MOM = NONE (best momentum cell +0.0068 < 0.02).

## 3. Best reversal cell L=63,h=3 — strong ranks, untradeable book

Per-decile mean forward-3c residual return (bps, D1 = lowest past-resid): D1 **−18.10**, D2
−10.78, D3 −10.93, D4 −10.84, D5 −7.22, D6 −3.47, D7 +0.82, D8 −0.83, D9 +7.81, D10 **+20.61**.
The gradient the IC sees lives in D2–D9; both extremes CONTINUE (losers keep losing, winners
keep winning). The registered reversal-oriented book (long D1 / short D10) is structurally
short both continuation tails:

- Oriented spread: mean **−38.46 bps/3c** (t −3.95, t_adj −2.28) vs median **+9.34**, 50.7%
  positive — the typical candle pays the reversal book; fat squeeze/cascade episodes take it
  all back and more. ≈ −140%/yr gross.
- Per-year: negative 2020 (−70), 2021 (−84), 2022 (−60), 2025 (−18); ~flat 2023/2024 even
  though those are the best IC years (−0.071/−0.050) — IC and book P&L never agree on a good
  year, exactly the DIAG-D pathology.
- Buckets: CRASH +13.4 (t +0.45), MANIA −55.4 (t −2.33), CHOP −42.5 (t −3.73) — wins nowhere.
- Contamination twin (forward window fully before 2025-03): spread −44.45 bps (t −4.70), IC
  −0.0459 — the kill does not depend on the burned sub-window.
- Cost coverage at natural cadence rebal=3 (phase sweep 0/3 positive): gross −146.1%, funding
  **−49.1%**, NET −220.0%, net2x **−244.8%**; turnover 331×/yr (= 24.8%/yr at 1× costs).
  Turnover realism: an L=63 sort still reshuffles its extreme deciles nearly every candle.
- Top-20 twin: IC −0.0460 (t −11.4), spread −57.2 bps mean / +17.9 median, NET −302.1%/yr —
  same structure, worse. Not a top-40 artifact.
- Funding tells the mechanism story: the reversal orientation is **anti-carry** (−49%/yr drag —
  long recent losers that still carry positive funding, short squeeze names whose funding is
  negative). Fading residual momentum means fighting the funding cross-section that DIAG-A
  showed is the structurally-paid side.

## 4. Best momentum cell L=3,h=21 — the only cost-covering cell, and why it still dies

The one cell whose book makes money: oriented spread +75.4 bps/21c (t +3.78, t_adj +0.82,
median +40.2), NET_ann +45.2% / net2x +31.5% at rebal=21, **21/21 phases positive**, turnover
184×/yr, net Sharpe +0.41, top-20 twin +74.9%, contamination-robust (+77.1 ex-window). Honest
accounting of why the registered criterion still refuses it, and why that refusal is correct:

1. **IC = +0.0068 — 3× below the registered 0.02 floor** (top-20 twin +0.0163, also below).
   The spread is tails-only: per-decile means show the P&L is almost entirely SHORT-D1 bleed
   (D1 −87.7 vs D10 −16.8 bps/21c) — a short-recent-losers book, not a cross-sectional gradient.
2. **Era-concentrated:** 2020 +279, 2021 +180, then 2022 −16, 2023 +17, 2024 −17, 2025 +85 —
   three consecutive dead years in the middle of IS; half2 IC +0.0004 (t +0.10), i.e. the rank
   signal is ZERO in 2023-25.
3. **Significantly LOSES in CRASH:** −177.2 bps/21c (t −2.89), CRASH-conditional β_BTC −0.26.
   Would fail the neutrality gate G4 (worst-bucket t > −1.0) at EXPLORATION even if the IC
   floor were waived. Not an all-conditions book; the counterparty (the herding chaser)
   disappears exactly where the charter demands one.

## 5. Beta before/after residualization — verified, and NOT ~0 (headline methodological finding)

OLS of the best-rev-cell spread stream on forward BTC/ETH returns (n=6,165):

| stream | β_BTC | (se) | β_ETH | (se) |
|---|---|---|---|---|
| RAW (before return-neutralization) | +0.1400 | 0.0319 | +0.1531 | 0.0241 |
| RESIDUAL (after) | **+0.1393** | 0.0319 | +0.1563 | 0.0241 |

Bucket-conditional β_BTC of the residual stream: **CRASH +0.448 (se 0.075)**, MANIA −0.244
(se 0.067). Momentum-cell twin: full-sample −0.085 raw / −0.085 resid, CRASH −0.261.

Two lessons, both first-class for this track:

1. **Residualization of returns barely moved the spread's realized beta** (+0.140 → +0.139).
   Because both decile legs carry similar TRAILING betas, β·r_BTC nets out of the spread — the
   sort was already static-beta-flat. What remains is **conditional-beta asymmetry**: recent
   losers realize far higher downside beta in crashes than their trailing 90d OLS estimate
   (+0.45 crash beta on the loser-long book AFTER residualization), and the trailing estimator
   cannot see it by construction. "Neutral by construction" is falsified at bucket level —
   the sketch's own mechanism section claimed structural neutrality; G1/G2-style measurement
   was indispensable, exactly as the charter demands (measured, never assumed).
2. This generalizes DIAG-A's warning (crash β +0.172 on the carry spread): **measurement-level
   rolling-beta residualization does NOT deliver crash-conditional neutrality** for any sort
   that correlates with recent losses. EXPLORATION-A's hedge-overlay G2-CRASH test is the
   binding test, and its difficulty is now confirmed on a second, independent sort.

## 6. What dies with the stage, and what the finding is worth elsewhere

1. **Dead as registered:** all 20 Stage-1 cells as 8h decile books, both orientations — the
   reversal orientation loses outright everywhere (anti-tail, anti-carry, −49%/yr funding
   drag, 331×/yr turnover); the momentum orientation is sub-floor on IC, tails-only,
   2023-25-dead, and crash-negative. Stage-1 lookbacks/thresholds die with it (PLAN §6 — no
   knob inheritance without re-registration). The equity residual-momentum prior (Blitz-Huij-
   Martens) does NOT transfer to the 8h crypto cross-section in rank space.
2. **Stage 2 (1h) is untouched** — pre-registered as independent ("different microstructure");
   it runs when the §4.3 1h fetch lands, with its own 16-cell ledger. Note for its design
   window: at 8h the short-lookback reversal is rank-real (L=3,h=1 IC −0.025) but tail-broken;
   whether 1h reversal clears the 15bps/round-trip wall was and remains the registered question.
3. **Transferable observations (recorded, not acted on):**
   - The two-layer structure (mid-rank reversal + episodic extreme-tail continuation) is now
     confirmed on BOTH taker-flow (DIAG-D) and past-return (E1) sorts — any future MN
     construction that holds extreme deciles of ANY 8h activity/return sort is structurally
     short squeeze-continuation tails and must price that in at design time.
   - Reversal ranks are STRONGEST in CRASH (IC to −0.128) — a forced-flow/liquidity-provision
     rank signal exists there, but a decile book cannot monetize it (tails + costs + the +0.45
     conditional crash beta). If it is ever revisited, it needs a construction that (a) trades
     mid-ranks not tails, (b) survives the funding drag it fights — any such revisit is a NEW
     registration with its trial count carried into n_eff.
   - Conditional-beta asymmetry of losers is a risk-model fact for the §4.1 hedge overlay:
     trailing betas under-hedge crash downside for loser-heavy legs.
4. n_eff ledger for family E after this diagnostic: Stage-1 = 20 registered cells, no other
   knobs tried, no amendments, coverage scored at the per-sign champion only (map shows a
   fortiori no eligible cell could pass). Stage-2 ledger (16 cells) not yet opened.

*— QR, MN track, 2026-07-10. Probe run exactly as pre-registered; the |IC|/stability arm passed
broadly (15/20 cells) and the 2×-cost coverage arm killed the stage; no post-hoc re-gating.
A clean kill with a structural finding attached is the process working.*
