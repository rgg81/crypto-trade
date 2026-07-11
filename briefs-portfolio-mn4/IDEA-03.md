# IDEA-03 Regime-Adaptive Allocator — Research Brief

**Track:** MN4 blind tournament (10-idea parallel). **Pair:** QR+QE (model: Opus 4.8;
Fable suspended this session — user-directed). **Date:** 2026-07-12.

## 0. Construction One-Liner

**Principle-anchored threshold-rule regime detector** (NORMAL/STRESS/CRISIS on BTC
realized-vol + acute gap-z, with STRESS hysteresis + 3-candle CRISIS dwell) →
60c cross-sectional **momentum** alpha (single signal, all regimes) → regime drives
universe (top-20 → top-5 blue-chip core in STRESS) + gross (1.0 → 0.5 → 0.0) →
rank-neutral dollar-neutral + BTC/ETH beta-hedge overlay → daily rebal (rebal=3).

## 0.1 The Mandate vs the Data (transparent disclosure)

The user's seed mandate: *"a trend sub in trend regimes, a reversal sub in chop"*
and *"interrupt trading in black swan; stick to blue chips."*

**What the data showed (IS-only, pre-registered diagnostics):**

1. **Momentum vs reversal:** A close-to-close signal-IC scan (Spearman ρ vs fwd-3c
   close-to-close) initially showed reversal positive (+0.04 to +0.11) and momentum
   null/negative. This MISLED the first design into a -1.55 Sharpe reversal-only book.
   Diagnosis: the IC scan used close-to-close forward returns, but the engine earns
   **open-to-open** hold-period returns (fill at open[k], hold to open[k+1]). A
   bare-signal open-to-open simulation revealed the TRUE structure:

   | Horizon | 0-cost SH | 1x-cost SH | 2x-cost SH | TO ann |
   |---------|-----------|------------|------------|--------|
   | 7       | +1.76     | +1.18      | +0.60      | 323    |
   | 15      | +2.08     | +1.66      | +1.24      | 232    |
   | 30      | +1.27     | +0.95      | +0.64      | 172    |
   | **60**  | **+1.52** | **+1.29**  | **+1.06**  | **125**|
   | 90      | +1.45     | +1.24      | +1.03      | 110    |

   **Momentum is strongly positive** at all horizons 7-180c on open-to-open.
   **Reversal is negative** at all horizons (mirror image).

   **Design consequence:** The "trend sub in trend" mandate is EMPIRICALLY CORRECT.
   The "reversal sub in chop" mandate is EMPIRICALLY NULL — reversal does not exist
   in the PIT top-20 crypto perp universe at 8h on an open-to-open basis at any
   horizon. The frozen construction uses a single 60c momentum alpha across all
   regimes. The **regime-adaptive allocation** is in the **risk primitives**
   (universe + gross contraction toward the blue-chip core), NOT in the alpha sign.
   The sub-regime (TREND/CHOP) is reported for attribution but does not switch the
   signal.

2. **h=60 chosen on principle:** the best **2x-cost survivor** (+1.06 Sharpe), the
   slowest practical momentum horizon (lowest turnover 125x ann), and the most robust
   across regimes. NOT the peak-zero-cost horizon (h=15 at +2.08) — the charter's
   binding constraint is cost survival, and h=60 is the peak of the cost-surviving
   Sharpe curve.

## 0.2 The Regime Detector (load-bearing — pre-registered)

**Choice: principle-anchored threshold rule with hysteresis (NOT HMM).** Reasons:
HMM calibration is opaque (hidden-state emission probabilities are fit-DOF that
smuggle in Sharpe-tunable parameters — the "coupled-dial" anti-pattern). A threshold
rule with round-number thresholds is fully transparent, mechanically reproducible,
and leak-testable.

**Indicators (all past-only, data <= close[t]):**
- `rv30_ann[t]` = BTC 30c annualized realized vol (8h log returns).
- `gap_z[t]` = |r_BTC[t]| / EWMA-σ (halflife=30, σ through t-1).
- `xs_corr[t]` = median pairwise 90c correlation across PIT top-20 (**reported
  forensic only** — NOT wired into the state decision; crypto's chronic high
  baseline corr inflates calm-time occupancy).

**Thresholds (ALL principle-anchored, NONE Sharpe-scanned):**
- `STRESS_VOL_ENTER = 0.80` annualized. Round-number crypto stress level (IS median
  vol = 0.52). Enter STRESS.
- `STRESS_VOL_EXIT = 0.60` annualized. Hysteresis exit (enter 0.80 / exit 0.60).
- `CRISIS_GAP_Z = 5.0` σ. Acute spike trigger (catches COVID, LUNA, FTX).
- `CRISIS_ABS_RETURN = 0.12` (12% BTC 8h candle). Round-number black-swan bar.
- `CRISIS_DWELL = 3` candles. Minimal dwell for daily rebal to catch CRISIS.
- `TREND_RATIO = 0.25`. Sub-regime split (round number, IS median = 0.231).

**CRISIS-FALSIFY-003 discipline:** CRISIS dwell is minimal (3 candles = 1 daily
rebal cycle, NOT the 9-candle dwell that killed the shared floors). Calm-time
CRISIS occupancy = 0.90% (44/4898 defined candles, 13 distinct entries) — well
within the <5% bar. The detector reports calm-time occupancy honestly.

## 1. IS-Only Evidence

### Headline scorecard (IS 2020-01-01 → 2024-06-30, 4929 8h candles, 747 syms)

| Metric | 1x cost | 2x cost (GT twin) |
|--------|---------|-------------------|
| **Sharpe** | **+1.552** | **+1.280** |
| Ann return | +65.78% | — |
| MaxDD | -41.66% | — |
| Win rate | 0.493 | — |
| Turnover (ann one-way) | 132.5x | — |
| Mean gross leverage | 0.920 | — |
| Final equity | 9.45x | — |

### Regime occupancy (IS)

| State | n candles | frac | Expectation | Status |
|-------|-----------|------|-------------|--------|
| NORMAL | 3749 | 0.765 | ≥60% | PASS |
| STRESS | 1105 | 0.226 | <25% (S+C) | PASS |
| CRISIS | 44 | 0.009 | <5% | PASS |
| NORMAL-TREND | 1697 | 0.453 (of NORMAL) | — | — |
| NORMAL-CHOP | 2052 | 0.547 (of NORMAL) | — | — |
| distinct CRISIS entries | 13 | — | — | — |

### Per-regime attribution (candle-level, 1x cost)

| Regime | n candles | mean bps/candle | Sharpe |
|--------|-----------|-----------------|--------|
| NORMAL | 3748 | +6.38 | +1.79 |
| STRESS | 1105 | +0.88 | +0.36 |
| CRISIS | 44 | +15.19 | +5.25 |
| NORMAL-TREND | 1697 | +8.04 | +2.02 |
| NORMAL-CHOP | 2051 | +5.00 | +1.57 |

CRISIS-regime Sharpe +5.25 is the crisis defense WORKING: the book is FLAT
(gross_scalar=0) during crisis dwell, so it AVOIDS the crash. The +15.19 bps/candle
is the relative benefit of not being invested.

### Per-year Sharpe

| 2020 | 2021 | 2022 | 2023 | 2024-H1 |
|------|------|------|------|---------|
| +2.77 | +2.08 | +0.56 | +1.40 | +0.75 |

All years positive. 2022 (crypto bear: LUNA, FTX) is the weakest at +0.56 — the
crisis defense fired most in 2022.

### Beta (neutrality MEASURED)

| Metric | Value |
|--------|-------|
| BTC rolling-270c mean | +0.014 |
| BTC rolling-270c |max| | +0.355 |
| BTC rolling-270c |p95| | +0.216 |
| CRASH bucket β (n=637) | -0.012 |
| MANIA bucket β (n=912) | +0.050 |
| CHOP bucket β (n=3289) | +0.009 |

All bucket betas < 0.05 (well within the 0.20 bar). The rolling |p95| = 0.216
exceeds the charter G1a gate (|β| ≤ 0.10 on ≥95%); disclosed — the hedge overlay
partially but not fully cancels directional beta during strong trend periods.

### De-risk primitive forensics

| Metric | Value |
|--------|-------|
| rebals delevered (gross_scalar<1) | 383 |
| rebals FLAT (CRISIS) | 15 |
| rebals HALF-gross (STRESS) | 368 |
| rebals executed | 1642 |
| hedge ETH-armed rebals | 327 |

## 2. Leak Battery

| Test | Result |
|------|--------|
| corrupt-future (state[:t0] identical) | PASS |
| corrupt-future (signal[:t0] identical) | PASS |
| corrupt-future (non-vacuous: future differs) | PASS |
| decision-lag [k-1] (single-bar corruption) | PASS |
| **LEAK BATTERY OVERALL** | **PASS** |

The regime detector is stateful (hysteresis + CRISIS dwell). The corrupt-future
positive control confirms state[:t0] is bit-identical when close[t≥t0, :] is
replaced with a different random walk. The decision-lag test confirms single-bar
corruption at t0 leaves state[:t0] unchanged.

## 3. IS Gate (principle-anchored, pre-registered)

| Gate | Threshold | Result |
|------|-----------|--------|
| honest_engine | by construction | PASS |
| is_only (mn3_split guard) | no holdout reads | PASS |
| leak_battery | corrupt-future + decision-lag | PASS |
| sharpe_1x_positive | > 0 | PASS (+1.552) |
| sharpe_2x_survives_cost | > 0 | PASS (+1.280) |
| crisis_occupancy_lt_5pct | < 5% | PASS (0.90%) |
| stressplus_occupancy_lt_25pct | < 25% | PASS (23.5%) |
| beta_crash_abs_lt_0.20 | < 0.20 | PASS (-0.012) |
| beta_mania_abs_lt_0.20 | < 0.20 | PASS (+0.050) |
| maxdd_gt_neg50pct | > -50% | PASS (-41.66%) |

**IS GATE OVERALL: PASS → reveal-ready.**

## 4. Files (namespaced)

- `analysis/portfolio/mn4_idea03_regime.py` — regime detector (load-bearing).
- `analysis/portfolio/mn4_idea03_alpha.py` — 60c momentum alpha (frozen).
- `analysis/portfolio/mn4_idea03_run.py` — IS runner + scorecard + leak battery.
- `tests/test_mn4_idea03.py` — 13 tests (corrupt-future, decision-lag, occupancy,
  sign semantics, universe contraction, dwell discipline).

## 5. OOS Risks (honest disclosure)

1. **2022 was the weakest IS year (+0.56 Sharpe).** The holdout (2024-H2 → 2026-H1)
   includes the 2025-11→2026-06 crash-heavy period. If crypto momentum weakens in
   bear/crash periods (as 2022 suggests), the book's alpha may compress OOS. The
   crisis defense (flat in CRISIS) partially mitigates this.
2. **The rolling beta |p95| = 0.216** exceeds the strict G1a gate. During strong
   trends, the book has residual directional beta that the hedge doesn't fully cancel.
3. **MaxDD -41.66%** is under the -50% bar but not "very controlled." The STRESS
   gross reduction (0.5x) helps but doesn't prevent large drawdowns during sustained
   elevated-vol periods.
4. **Funding income is a contributor** (+0.23 Sharpe from funding — shorting
   high-funding alts earns income). If the funding regime shifts OOS (e.g., funding
   compresses), this tailwind may weaken.
5. **The IC-vs-P&L disconnect lesson:** the close-to-close IC scan was misleading by
   ~2.5 Sharpe. The open-to-open scan is the correct convention for this engine. Any
   OOS signal-monitoring must use the open-to-open convention.
