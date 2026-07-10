# DIAGNOSTIC-D — Taker-Flow Cross-Section Probe (MN track)

**Date:** 2026-07-10 · **Role:** QR · **Script:** `analysis/portfolio/mn_diag_d_takerflow.py`
(committed spec = PLAN.md §2 Sketch D, run exactly as frozen; trial ledger: 10 grid cells)
**Data hygiene:** `mn_panel_health()` → OK (BTC grid T=7147 contiguous; live feeds current).
**Blinding/IS:** panel sliced via `mn_split.mn_slice_is` before any computation; `mn_guard_grid`
passed; IS = 2020-01-01 → 2025-12-31 (T=6,576 candles × 747 syms). Old-track `is_mask`/
`OOS_CUTOFF` never touched. Verification: vectorized per-candle Spearman cross-checked against
`scipy.stats.spearmanr` on 800 random candles (max abs diff 1.1e-16); decile means reproduced
by an independent re-implementation bit-identically.

## VERDICT — pre-registered kill criteria (PLAN §2 Sketch D, verbatim)

| # | Criterion (frozen) | Measured | Verdict |
|---|---|---|---|
| (a) | max \|IC\| < 0.015 over the 10-cell grid | max \|IC\| = **0.0203** (cell L=21, h=3) | SURVIVES |
| (b) | best cell's decile spread fails 2×-cost coverage at its natural cadence (rebal=3, phase-agnostic) | net2x_ann = **−213.9%** (gross −121.8%, funding −28.7%, 2× costs −63.4%) | **KILLED** |
| (c) | best-cell IC sign flips between IS halves | half1 = −0.0018, half2 = −0.0364 — same sign | SURVIVES |

**SKETCH D IS DEAD.** Criterion (b) fired — not marginally: the IC-oriented decile book loses
−125%/yr GROSS before a single basis point of cost. Per PLAN §5.7 the sketch dies as
registered; no post-hoc re-gating. The taker-flow lookbacks/thresholds die with it (PLAN §6:
no knob inheritance by live sketches without explicit re-registration).

---

## 0. Construction (as registered + implementation decisions on record)

- Universe: PIT top-40 by trailing 30-candle mean $-volume, ≥90d (270-candle) history —
  DIAG-A's builder reused verbatim. Mean 36.6 members/candle; median 40 names used → k=4
  names per decile leg, book gross = 2.0.
- TI_i[t] = taker_buy_volume/volume per candle (ratio of in-candle sums, never a mean of
  ratios; volume==0 → NaN). Member TI quantiles: q1 0.426 / median 0.489 / q99 0.539.
- z_i[t] = per-name z of TI over the trailing 90 candles (frozen per PLAN; window includes t —
  TI[t] is known at close[t]). **Implementation decisions on record:** z-window min obs = 45
  (majority tolerance, the DIAG-A convention family); z coverage over member-candles = 99.7%.
- Signal_L = trailing L-candle mean of z ("aggregated over lookbacks" read as mean-of-z,
  parallel to DIAG-A's registered mean-of-funding-z; min finite obs = L//2+1, i.e. the
  DIAG-A 5-of-9 majority rule). L ∈ {1, 3, 9, 21, 63}.
- Forward return = sum of next-h residual returns (h ∈ {1, 3}, strict all-finite);
  residualization = `mn_beta.rolling_beta` frozen defaults at the [k−1] lag (harness shared
  with DIAG-A). IC = per-candle Spearman over current members (min 20).
- IS halves = 2020-22 / 2023-25 (DIAG-C's registered convention, split on the decision candle).
- Best cell = argmax |mean IC|; decile-spread book oriented by the measured IC sign
  (all 10 cells measured REVERSAL → long D1 lowest-TI-z, short D10 highest); cost coverage =
  residual price leg + funding on every held leg − 7.5 bps/side × Σ|Δw|, 2×-twin doubled.

## 1. The sign-per-horizon map (measured, not assumed)

Full-IS Spearman IC of Signal_L vs forward-h residual return, top-40 (n ≈ 6,166 candles/cell):

| cell | mean IC | t | sign | half1 (2020-22) | half2 (2023-25) | stable? |
|---|---|---|---|---|---|---|
| L=1, h=1 | −0.0106 | −4.42 | REV | −0.0065 (t −1.80) | −0.0141 (t −4.45) | same-sign |
| L=1, h=3 | −0.0067 | −2.80 | REV | +0.0006 (t +0.16) | −0.0132 (t −4.12) | **FLIP** |
| L=3, h=1 | −0.0116 | −4.72 | REV | −0.0040 (t −1.08) | −0.0182 (t −5.62) | same-sign |
| L=3, h=3 | −0.0103 | −4.23 | REV | −0.0011 (t −0.29) | −0.0184 (t −5.74) | same-sign |
| L=9, h=1 | −0.0164 | −6.52 | REV | −0.0083 (t −2.20) | −0.0235 (t −6.99) | same-sign |
| L=9, h=3 | −0.0178 | −7.07 | REV | −0.0044 (t −1.15) | −0.0296 (t −8.92) | same-sign |
| L=21, h=1 | −0.0194 | −7.73 | REV | −0.0090 (t −2.41) | −0.0286 (t −8.44) | same-sign |
| **L=21, h=3** | **−0.0203** | **−8.09** | REV | −0.0018 (t −0.49) | −0.0364 (t −10.94) | same-sign |
| L=63, h=1 | −0.0131 | −5.33 | REV | −0.0066 (t −1.80) | −0.0188 (t −5.70) | same-sign |
| L=63, h=3 | −0.0137 | −5.60 | REV | +0.0028 (t +0.74) | −0.0282 (t −8.74) | **FLIP** |

- **Every cell measures REVERSAL at the rank level** — no momentum cell anywhere on the
  5×2 grid. The IC strengthens with lookback up to L=21 then fades at L=63.
- The half-split is lopsided: essentially ALL of the rank-reversal lives in 2023-25
  (best cell t = −10.94); 2020-22 is flat (t = −0.49). Kill (c) survives on the registered
  halves rule, but only just — per-year ICs are +0.0056 / +0.0022 in 2020/2021 before turning
  negative 2022-25. The IC regime changed sign mid-sample.

Regime buckets (decision-candle label, best cell): CRASH IC −0.0037 (t −0.51, n=658), MANIA
−0.0244 (t −3.61, n=929), CHOP −0.0218 (t −7.53, n=4,578). The rank-reversal is a
mania/chop phenomenon; CRASH is flat — the mechanism's payer thins out exactly where an
all-conditions book needs it.

## 2. The headline finding — the IC and the tradeable tails DISAGREE

Best cell (L=21, h=3) per-decile mean forward-3-candle residual return (bps, D1 = lowest TI-z):

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | D10 |
|---|---|---|---|---|---|---|---|---|---|
| **−14.46** | −6.83 | −9.58 | +2.63 | −1.71 | −7.53 | −7.52 | −4.27 | −0.70 | **+19.90** |

The structure is NOT monotone. The rank-wide Spearman is negative (reversal), but both extreme
deciles CONTINUE: the most aggressively-bought decile keeps rising (+19.9 bps/3c) and the most
aggressively-sold keeps falling (−14.5 bps/3c). Reconciliation (verified independently):
D10−D1 mean = +34.4 bps but **median = −0.7 bps, 49.8% of candles positive** — the
tail-continuation is entirely mean-driven by fat squeeze/cascade episodes that dominate dollar
terms, while the typical candle carries the small rank-reversal the IC sees. Two phenomena,
one signal: per-candle noise reversal (equal-weighted, what IC measures) vs episodic
tail momentum (return-weighted, what a decile book actually eats).

Consequence: the registered reversal-oriented decile book (long D1 / short D10 per the
measured IC sign) is structurally short both continuation tails and loses
**−34.4 bps per 3 candles, t = −4.47, ≈ −125%/yr gross — before any costs.**

## 3. Decile spread: gross AND net at the pre-registered cadences (top-40, phase-agnostic)

Book = IC-oriented (long D1 / short D10, gross 2.0); net = residual price leg + funding on
every held leg − 7.5 bps/side on Σ|Δw|; 2×-twin doubles costs.

| rebal | gross ann | funding ann | NET ann (1×) | NET ann (2×) | turnover/yr | net Sharpe | ex-2025-03+ NET |
|---|---|---|---|---|---|---|---|
| 1 | −129.1% | −30.9% | −211.6% | −263.2% | 688× | −1.87 | −187.8% |
| 3 | −121.8% | −28.7% | −182.2% | **−213.9%** | 423× | −1.62 | −165.9% |

- Phase distribution at rebal=3: NET −192.6% / −181.1% / −173.0% — **0/3 phases positive**;
  the kill is phase-robust, not a phase artifact.
- **Implied turnover is the cost story the PLAN anticipated:** 688×/yr at rebal=1 → 51.6%/yr
  burned at 1× costs (103% at 2×); 423×/yr at rebal=3 → 31.7%/yr (63.4% at 2×). Even a
  hypothetical correctly-signed edge of the measured magnitude (~+125%/yr gross) would have
  had to clear a 32-64%/yr cost hurdle — the sort churns because a 21-candle mean of a
  90-candle z still reshuffles the extreme deciles nearly every candle.
- Funding drag −29 to −31%/yr on the reversal orientation: D10 shorts are disproportionately
  negative-funding names (squeeze candidates — shorting them PAYS funding), consistent with
  the tail-continuation picture.

## 4. Regime buckets and per-year stability (best cell, oriented spread)

| bucket | n | spread (bps/3c) | t | IC |
|---|---|---|---|---|
| CRASH | 658 | −42.62 | −2.05 | −0.0037 |
| MANIA | 929 | −16.65 | −0.95 | −0.0244 |
| CHOP | 4,578 | −36.76 | −3.97 | −0.0218 |

Negative in ALL three buckets — the registered book has no regime refuge (G4 would fail
immediately even if costs were free).

| year | n | spread (bps/3c) | t | IC |
|---|---|---|---|---|
| 2020 | 689 | −41.97 | −2.83 | +0.0056 |
| 2021 | 1,095 | −111.79 | −6.67 | +0.0022 |
| 2022 | 1,095 | −11.96 | −0.87 | −0.0105 |
| 2023 | 1,095 | +1.17 | +0.09 | −0.0473 |
| 2024 | 1,098 | +15.37 | +1.08 | −0.0416 |
| 2025 | 1,093 | −59.98 | −1.95 | −0.0203 |

IC and spread never agree on a good year: when the IC was strongest (2023-24, IC ≈ −0.045)
the oriented spread was ~flat because the mid-ranks — not the tails — carried the reversal;
when the tails moved (2020-21, 2025 squeeze eras) they moved AGAINST the reversal book. The
flipped (momentum) orientation is no candidate either: mean-positive only via 2020-21+2025
tail episodes, negative in 2023-24, median-negative overall — an unstable squeeze-harvest,
not a cross-sectional edge.

Contamination twin (forward window fully before 2025-03): spread −29.82 bps (t −4.61),
IC −0.0208 (n=5,247) — the kill does NOT depend on the burned sub-window; the book loses
just as decisively without it.

## 5. Beta before/after neutralization (best-cell spread stream)

| stream | β_BTC | (se) | β_ETH | (se) |
|---|---|---|---|---|
| RAW (before residualization) | −0.0160 | 0.0253 | +0.0053 | 0.0191 |
| RESIDUAL (after) | −0.0079 | 0.0252 | +0.0072 | 0.0191 |

Bucket-conditional β_BTC of the residual stream: CRASH −0.055 (se 0.053), MANIA −0.058
(se 0.049). Unlike DIAG-A (crash β +0.172), taker-flow sorts are close to beta-flat even
crash-conditionally — the one structurally pleasant property of this sketch, and it is not
worth anything without an edge to neutralize.

## 6. Top-20 robustness column (pre-registered secondary view)

Same best cell: IC −0.0154 (t −4.58); oriented spread −33.47 bps/3c (t −3.16, n=6,237);
natural-cadence NET_ann = −188.6%. Same sign, same structure — the kill is not a top-40
artifact.

## 7. What dies with the sketch, and what the finding is worth elsewhere

1. **Dead as registered:** the 8h taker-flow cross-section decile book, all 10 grid cells,
   both orientations implicitly (IC-oriented loses outright; the flip is a median-negative,
   era-concentrated squeeze bet that fails any stability standard). No 1h extension: the PLAN
   gates it on "the 8h map shows the signal decaying inside one candle" — the map shows the
   opposite (IC GROWS with lookback to L=21), so the 1h trigger does not fire.
2. **Transferable observation (recorded for family C, not acted on here):** extreme-decile
   taker imbalance marks squeeze CONTINUATION episodes at 8h, and its funding cross-wiring
   (D10 ≈ negative-funding names) is exactly the crowding-fade conditioning DIAG-C's
   pre-registered rank-sum score already contains (ΔOI z + funding-extremity z +
   taker-imbalance z). DIAG-C is the registered construction that can condition these tails
   on leverage build; per PLAN §6 any reuse of DIAG-D's specific windows there requires
   re-registration in that sketch's brief with the trial count carried into n_eff.
3. n_eff ledger for family D after this diagnostic: 10 registered cells, no other knobs
   tried, no amendments, no post-hoc re-orientation scored.

*— QR, MN track, 2026-07-10. Probe run exactly as pre-registered; kill criterion (b) fired;
sketch D dead as registered. A clean kill on a half-day probe is the process working.*
