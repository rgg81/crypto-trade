# IDEA-09 — Calendar / Seasonality Tilt (DIRECTIONAL) — IS Brief

**Track:** MN4 blind tournament, idea 09. **Model:** Opus 4.8 (Fable suspended this session; user-directed per charter).
**IS window:** 2020-01-01 → 2024-06-30 (T=4929 8h candles, BTC+ETH). **Holdout:** SEALED (zero reads, `mn3_split` guard, `reveal_token=None`).
**Verdict:** **PRIMARY (pre-registered weekend effect) is NULL at the gate.** IS-selected ARM-B (turn-of-month) fails the per-year sign-stability bar. The IDEA is **NOT reveal-eligible** in the positive sense. Banked for the holdout reveal as a NULL candidate (the tournament may still reveal it to confirm null generalization, per charter Phase B "reveal ALL 10").

---

## 1. The hypothesis (pre-registered)

The most-cited calendar anomaly in the crypto literature is the **weekend effect** (lower institutional flow + thinner weekend liquidity → structural drift). Pre-registered as the PRIMARY effect, *frozen before any IS result was looked at*, per the charter's "measure with a pre-registered statistical test, NOT eyeballed" mandate.

**Construction:** `ew_long` equal-weight on {BTC, ETH}, daily rebal (`rebal=3` on the 8h grid — the minimum cadence resolving day-of-week). The calendar tilt lives entirely in a `gross_scalar_series ∈ {0,1}` (long the favorable bucket, flat the unfavorable). Direction is IS-sign-determined (long whichever bucket has the higher IS mean).

**Crisis de-risk (per-construction Layer-2 throttle, principle-anchored — two independent primitives OR'd):**
- **C1 acute vol spike:** trailing 90-candle (30-day) BTC 8h-return vol annualized; flat when > 0.80 (COVID ~130%, Luna ~110%, FTX ~100%, calm 2023 ~35%).
- **C2 sustained bear:** BTC close below its **200-day SMA** (600 8h candles — the canonical structural trend line, universally known, not IS-fitted).
- Combined crisis scalar = calm iff (vol ≤ 0.80 **AND** BTC ≥ 200d-SMA). Both past-only (`close[k-1]` known at decision `k-1`).

**Pre-registered PRIMARY gate** (principle-anchored, multiplicity-aware):
| Gate | Threshold | Result |
|---|---|---|
| **G1** Welch \|t\| weekend-vs-weekday, pooled BTC+ETH | ≥ 2.0 | **FAIL** (t = **−0.362**) |
| **G2** per-year sign stability (5 year-slices 2020–2024-H1) | ≥ 4/5 same sign | **FAIL** (**3/5**) |
| **G3** cost-survival: Sharpe(1x) > 0 AND Sharpe(2x) ≥ 0.60·Sharpe(1x) | — | **PASS** |
| **G4** economic-relevance floor \|weekend−weekday\| contrast | ≥ 2 bps/candle | **FAIL** (**1.58 bps**) |

---

## 2. IS-only numerical evidence

### 2.1 PRIMARY measurement (weekend effect, pooled BTC+ETH, IS-only)

Per-symbol:

| Symbol | n_we | n_wd | mean_we (bps) | mean_wd (bps) | contrast (bps) | t | p |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 1409 | 3519 | +3.02 | +7.50 | **−4.47** | −0.86 | 0.39 |
| ETHUSDT | 1409 | 3519 | +10.57 | +9.27 | **+1.31** | +0.19 | 0.85 |
| **POOLED** | 2818 | 7038 | +6.80 | +8.38 | **−1.58** | **−0.362** | 0.717 |

The two symbols **disagree on sign** (BTC: weekday > weekend; ETH: weekend > weekday). Pooled contrast is economically trivial (−1.58 bps/8h) and statistically null.

Per-year sign of the pooled contrast (sign-stability, the canonical subsample-robustness test for a calendar anomaly):

| Year | contrast (bps) | matches pool sign? |
|---|---|---|
| 2020 | −17.25 | yes |
| 2021 | +8.19 | **no** |
| 2022 | −0.40 | yes |
| 2023 | −0.39 | yes |
| 2024-H1 | +6.00 | **no** |

3/5 consistent. The effect flips sign in 2 of 5 years and is near-zero in 2022–2023. **Not a stable behavioral pattern.**

### 2.2 SECONDARY measurements (descriptive only — multiplicity disclosure, NEVER traded)

| Effect | n_on | n_off | contrast (bps) | t | p | notes |
|---|---|---|---|---|---|---|
| Turn-of-month (last 3 + first 3 days) | 1942 | 7914 | **+16.44** | **+3.27** | 0.0011 | strong pooled t; per-year sign 3/5 → fails Bonferroni-2 sign-stability bar |
| DOW one-way ANOVA (7 buckets) | — | — | — | F=+1.80 | 0.096 | marginal; Bonferroni-7 fails |

DOW per-bucket means (bps): Mon +17.8, Tue +4.0, Wed +19.0, Thu −2.6, Fri +3.7, Sat +6.7, Sun +6.9. Monday/Wednesday stand out; but with 7 buckets the ANOVA p=0.096 does not clear 0.05, and Bonferroni-7 (α/7 ≈ 0.007) fails decisively. Not robust.

**Candidate set = {weekend, TOM, DOW}.** None clears a multiplicity-corrected bar **with per-year sign stability**. The TOM effect's strong pooled t (+3.27) is driven by a subset of years (sign-flips in 2/5), so it fails the pre-registered robustness floor — a calendar anomaly that does not reproduce across years is not a stable behavioral edge.

**Halving-cycle proximity** is structurally untestable in this IS (only one full halving inside IS, 2020-05; the 2024-04 halving sits at the very end). A single event cannot provide per-year sign stability by construction, so it is excluded from the candidate set.

### 2.3 ARM-A backtest (pre-registered PRIMARY = weekend tilt + crisis overlay)

| Variant | Sharpe | maxDD | ann | turn/yr | n_periods |
|---|---|---|---|---|---|
| **ARM-A 1×** | **+0.864** | **−49.87%** | +28.86% | 62.6× | 4865 |
| ARM-A 2× GT | +0.739 | −52.26% | +22.95% | — | — |
| ARM-A 1× NO-CRISIS | +0.657 | **−78.48%** | — | — | — |

Per-year Sharpe (ARM-A 1×): 2020 **+1.93**, 2021 +0.33, 2023 +0.96, 2024-H1 +0.69. **2022 is absent** — the 200d-trend filter is flat for almost the entire 2022 bear (BTC below its 200d-SMA), so 2022 has near-zero long-occupancy → zero-variance → NaN Sharpe. The trend filter worked as designed (avoided the bear).

### 2.4 **CRITICAL attribution** — the calendar contributes NEGATIVE Sharpe

| Baseline | Sharpe | maxDD | ann | turn/yr |
|---|---|---|---|---|
| **Crisis-only (trend+vol filter, NO calendar)** | **+1.417** | **−40.41%** | +65.62% | 7.7× |
| Always-long (B&H BTC+ETH 50/50) | +0.953 | −77.64% | +51.88% | 3.1× |
| ARM-A (calendar × crisis) | +0.864 | −49.87% | +28.86% | 62.6× |

**Calendar marginal contribution = Sharpe(ARM-A) − Sharpe(crisis-only) = +0.864 − +1.417 = −0.553.**

The calendar tilt **actively destroys Sharpe**: the trend-filter baseline alone earns +1.42; adding the calendar tilt brings it down to +0.86, *and* multiplies turnover 8× (7.7× → 62.6×) for the privilege. The construction's IS positive Sharpe is **entirely the trend-filter beta exposure** (which is idea 08's domain — vol-targeted managed-variance — not idea 09's calendar mechanism). **The calendar has no edge; the book's positivity is a beta artifact.**

### 2.5 Neutrality / β (directional book — β reported, not assumed)

- **Pooled β_BTC = +0.31**, pooled β_ETH = +0.31. Rolling-270 β_BTC: median **+0.40**, p10 +0.30, p90 +0.95.
- **Regime buckets:** CRASH β_BTC **+0.05** (crisis overlay de-risks → near-flat in crashes); CHOP β_BTC **+0.42**; MANIA β_BTC **+0.40**. The book carries material directional beta in calm + mania regimes — it is *not* crisis-robust by construction, only crisis-de-risked.

### 2.6 Cost coverage

Turnover = 62.6× one-way/yr (NOT "ultra-low" — daily rebal with 2 calendar flips/week). Cost drag @1× ≈ 62.6 × 7.5 bps ≈ 470 bps/yr; @2× ≈ 940 bps/yr. The trend-filter baseline turns over only 7.7×/yr (crisis overlay flips slowly). The calendar's incremental turnover is pure waste given its negative marginal Sharpe.

---

## 3. Leak battery (ALL PASS)

| Check | Result |
|---|---|
| (a) Crisis scalar corrupt-future: past bit-identical, future changed | **PASS** |
| (b) Calendar scalar deterministic-rebuild invariance (pure timestamp fn) | **PASS** (weekend, TOM) |
| (c) Inert-default byte-identity (scalar=None == ones) | **PASS** |
| (d) Decision-lag [k−1] (perturb scalar[t₀] → weights[:t₀+1] identical) | **PASS** |
| (e) Placebo negative-control (shuffled-dow t = −1.48, expect \|t\| < 2.0) | **PASS** |

---

## 4. Pre-registered GATE verdict

**PRIMARY (G1 & G2 & G4): FAIL** (G1 t=−0.36, G2 3/5 years, G4 1.58 bps). G3 cost-survival passes but is moot — the positive IS Sharpe is a trend-filter beta artifact, not a calendar edge.

**ARM-B (IS-selected TOM):** t=+3.27 clears Bonferroni-2 \|t\|≥3.0, BUT per-year sign-stability is 3/5 < 4 → **ARM-B not built.** No silent peeking.

**IDEA-09 reveal candidate: NONE (both arms NULL at their gates).**

Per the charter ("A clean null across 10 diverse untried ideas would itself be a strong, final structural result"), this is the methodology working: a pre-registered, multiplicity-safe test of the most-cited crypto calendar anomaly found **no robust edge**, and the attribution decomposition proves the calendar actively destroys value vs the trend-filter baseline. The honest finding is that **calendar/seasonality on BTC+ETH, measured over 4.5 years of IS, is not a tradeable edge at the daily cadence required to resolve day-of-week.**

---

## 5. What would falsify this NULL (design for OOS)

The holdout reveal will, with high probability, also show null calendar edge. The falsification of *this NULL verdict* would require:
1. A holdout weekend/weekday contrast with |t| ≥ 2.0 AND per-year sign stability in ≥ 4/5 of the *holdout's* year-slices (2024-H2, 2025, 2026-H1) — i.e. an effect that materialized *after* the IS.
2. A positive calendar marginal contribution (Sharpe(ARM-A) > Sharpe(crisis-only)) on the holdout.

Both are unlikely given the IS evidence (the effect flips sign across IS years, so any holdout sign is a coin flip). The construction is frozen byte-exact for the reveal; the gate is frozen; the verdict is pre-committed.

---

## 6. Files (namespaced)

- `analysis/portfolio/mn4_idea09_calendar_tilt.py` — measurement + construction (frozen).
- `tests/test_mn4_idea09_calendar_tilt.py` — 15 leak-safety + gate-integrity tests (all pass).
- `data/mn4_idea09/scorecard.json` — full IS scorecard (frozen).
- `data/mn4_idea09/dow_breakdown.csv`, `data/mn4_idea09/weekend_per_year.csv` — measurement tables.
- `briefs-portfolio-mn4/IDEA-09.md` (this file), `diary-portfolio-mn4/IDEA-09.md`.

**Frozen construction:** `ew_long` {BTC,ETH}, `rebal=3`, `gross=1.0`, weekend calendar scalar (long-weekday per IS sign) × crisis scalar (C1 vol>0.80 OR C2 BTC<200d-SMA → flat), `CostModel(5, 2.5, funding=True)`, 2× GT twin `CostModel(10, 5, funding=True)`. Reveal-ready as a NULL candidate.
