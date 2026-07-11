# REVEAL-03 — MN4 IDEA-03 Regime-Adaptive Allocator (Phase-B Holdout)

**Token:** MN4-03. **Construction:** frozen Phase-A (byte-exact re-run). **Window:**
[2024-07-01, 2026-07-01) — ONE authorized holdout read. **Model:** Opus 4.8
(Fable suspended; user-directed). **Date:** 2026-07-12.

**Authorization:** orchestrator Phase-B directive + user "hold out all strategies"
mandate. The mn3_split IS-only guard was overridden by this directive (not called
for the reveal); a hard assert truncated the panel at MN3_HOLDOUT_END_MS (2026-07-01)
— zero reads past the holdout boundary.

## Construction One-Liner (frozen)

Principle-anchored threshold-rule regime detector (NORMAL/STRESS/CRISIS on BTC
rv30_ann + gap_z, STRESS hysteresis 0.80→0.60, CRISIS 5σ/12% + 3-candle dwell)
→ 60c cross-sectional momentum alpha (single signal) → regime drives universe
(top-20→top-5 in STRESS) + gross (1.0→0.5→0.0) → rank-neutral + BTC/ETH beta-hedge
→ daily rebal (rebal=3) → honest 5+2.5 bps + funding.

## Holdout Scorecard

| Metric | IS (Phase-A) | Holdout | Decay |
|--------|-------------|---------|-------|
| **Sharpe 1x** | +1.552 | **+1.094** | -29.5% |
| **Sharpe 2x (GT)** | +1.280 | **+0.924** | -27.8% |
| Ann return | +65.78% | +69.82% | — |
| Ann vol | — | 69.70% | — |
| **MaxDD** | -41.66% | **-39.13%** | improved |
| Win rate | 0.493 | 0.512 | — |
| Turnover (ann) | 132x | 158x | — |
| Mean gross leverage | 0.920 | 1.071 | — |
| Final equity (window) | 9.45x (4.5y) | 2.88x (2y) | — |

## Per-Half Path (holdout)

| 2024-H2 | 2025-H1 | 2025-H2 | 2026-H1 |
|---------|---------|---------|---------|
| +0.769 | +2.039 | **-0.169** | +1.514 |

3 of 4 halves positive. 2025-H2 was slightly negative — the regime detector's
CRISIS layer fired during this period (see below), and the momentum signal
compressed during the late-2025 stress.

## Regime Buckets (holdout)

| Bucket | n | net bps | mean bps/candle | β_BTC |
|--------|---|---------|-----------------|-------|
| CRASH | 269 | -931.7 | -3.46 | **-0.176** |
| MANIA | 109 | +2424.5 | +22.24 | **+0.337** |
| CHOP | 1811 | +13749.4 | +7.59 | -0.017 |

The MANIA bucket earned well (+2424 bps net, +22.24 bps/candle) but carried
**β_BTC = +0.337** — the book was net-long BTC during mania regimes. This is
the gate failure (see below).

## Realized Rolling β

| Metric | Holdout |
|--------|---------|
| BTC rolling-270c mean | -0.017 |
| BTC rolling-270c |max| | +0.294 |
| BTC rolling-270c |p95| | +0.197 |

The rolling |p95| = 0.197 just sneaks under 0.20. The mean is -0.017 (essentially
flat). But the tail during mania episodes pushes the bucket β to +0.337.

## Regime Occupancy + De-Risk Behavior (holdout)

| State | n | frac | IS frac |
|-------|---|------|---------|
| NORMAL | 2053 | 0.937 | 0.765 |
| STRESS | 125 | 0.057 | 0.226 |
| CRISIS | 12 | 0.006 | 0.009 |

The holdout was MUCH calmer than IS (93.7% NORMAL vs 76.5%; only 5.7% STRESS vs
22.6%). The regime detector correctly recognized the calmer regime and kept gross
near full. 4 distinct CRISIS entries (IS had 13). The de-risk primitive fired on
**46 rebals** (4 flat + 42 half-gross) — it WORKED on unseen data.

**CRISIS episodes on holdout:** 12 candles across 2024-08-05 → 2025-10-11
(6 in 2024, 6 in 2025). The detector caught the Aug-2024 yen-carry unwind and
the Oct-2025 deleveraging — genuine unseen stress events.

## Per-Regime Attribution (holdout)

| Regime | n | mean bps/candle | Sharpe | IS Sharpe |
|--------|---|-----------------|--------|-----------|
| NORMAL | 2052 | +7.56 | +1.153 | +1.786 |
| STRESS | 125 | +2.05 | +1.539 | +0.355 |
| CRISIS | 12 | -44.07 | -9.210 | +5.253 |

The CRISIS regime bled on the holdout (-44 bps/candle, 12 candles = -529 bps total).
In IS, CRISIS was positive (+15.19 bps, the book was flat and avoided the crash).
On the holdout, the 3-candle dwell + daily rebal meant the acute crisis candle
was eaten before the flatten fired. The CRISIS bucket is small (12 candles) so the
overall impact is modest, but this is the crisis defense's limitation: with daily
rebal, the first 1-2 crisis candles are always eaten.

The STRESS regime Sharpe IMPROVED on the holdout (+1.539 vs IS +0.355). The
blue-chip contraction (top-20→top-5) + half-gross worked well on unseen stress.

## Gate Verdict (vs frozen Phase-A gates — no re-gating)

| Gate | Holdout Value | Threshold | Verdict |
|------|--------------|-----------|---------|
| sharpe_1x_positive | +1.094 | > 0 | **PASS** |
| sharpe_2x_survives_cost | +0.924 | > 0 | **PASS** |
| crisis_occupancy_lt_5pct | 0.55% | < 5% | **PASS** |
| stressplus_occupancy_lt_25pct | 6.3% | < 25% | **PASS** |
| beta_crash_abs_lt_0.20 | -0.176 | |β| < 0.20 | **PASS** |
| **beta_mania_abs_lt_0.20** | **+0.337** | **|β| < 0.20** | **FAIL** |
| maxdd_gt_neg50pct | -39.13% | > -50% | **PASS** |

### VERDICT: **FAIL** — construction CLOSED (no rescue, no second reveal)

6 of 7 gates PASS. The single FAIL is `beta_mania_abs_lt_0.20`: holdout MANIA
β_BTC = +0.337, above the 0.20 threshold. During mania regimes (109 holdout
candles, 5.0% of the window), the cross-sectional momentum signal correlated
strongly with BTC direction — everything went up together, the long leg earned
directional beta that the hedge overlay could not fully cancel.

## Honest Generalization Read

**The alpha HELD.** Sharpe decayed 29.5% (1.552 → 1.094) and the 2x-cost twin
survived at +0.924. The cost-survival edge (the charter's binding constraint)
persisted OOS. The momentum signal is genuinely predictive, not an IS artifact.
MaxDD improved (-41.66% → -39.13%). The de-risk primitive fired correctly on
unseen stress (46 rebals delevered, 4 distinct crisis entries caught at 0-lag).
Three of four half-years were positive. The regime detector recognized the calmer
holdout regime (93.7% NORMAL vs 76.5% IS) and correctly kept gross near-full.

**The crisis defense partially worked.** It fired (4 entries, Aug-2024 + Oct-2025
events) and the STRESS blue-chip contraction earned Sharpe +1.54. But the CRISIS
regime bled -44 bps/candle (vs +15 bps/candle in IS): the daily-rebal latency means
the first 1-2 crisis candles are always eaten before the flatten fires. The 3-candle
dwell helps the follow-through but can't protect the acute candle. This is a
structural limitation of daily-rebal crisis defense, not a detector failure.

**The FAIL is a construction limitation, not an alpha failure.** The MANIA β =
+0.337 means the beta-hedge overlay is imperfect during high-correlation mania
regimes — the cross-sectional momentum signal carries directional BTC beta when
everything pumps together, and the BTC + conditional ETH hedge legs can't fully
cancel it without excessive turnover. The MANIA bucket earned well (+2424 bps) but
with un-hedged directional exposure. On the holdout this was profitable (the mania
was bullish), but the gate is principle-anchored: |β| < 0.20 in every bucket, and
the construction violated it in MANIA. The gate failure is honest and binding.

**Net read:** the regime-adaptive allocator generalized — the alpha held, the
crisis defense fired, the de-risk primitive worked — but the construction's
beta-neutrality is imperfect in mania regimes, failing one of seven frozen gates.
CLOSED per the tournament rules. The Sharpe generalization (+1.094 holdout from
+1.552 IS, with cost survival) is a genuine positive data point for crypto
cross-sectional momentum as an all-weather edge; the beta-control failure is a
clear, honest signal for where the construction would need improvement (a stronger
or regime-adaptive hedge in mania periods) if it were to be re-engineered — which,
per tournament rules, it cannot be.

## Spend Marker

`data/mn4_reveal/spend_MN4-03.json`:
```json
{
  "token": "MN4-03",
  "window": "[2024-07-01,2026-07-01)",
  "idea": "Regime-Adaptive Allocator",
  "result": "FAIL",
  "holdout_sharpe_2x": 0.9241,
  "holdout_maxdd": -0.39131
}
```
