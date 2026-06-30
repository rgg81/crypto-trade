# EXPLORATION-003 — Hysteresis no-trade band (iter-003)

**Date:** 2026-06-30
**Status:** COMPLETE — **PROMOTED-INTERMEDIATE** (real cost-capture; new working best, still < +0.30 bar). OOS HIDDEN.
**Cadence:** EXPLORATION (IS-only — `--confirm` NOT passed)
**Commit:** `4926881` · builds on iter-002 (sector-relative momentum, IS +0.08)

---

## Hypothesis

iter-002 had a real +0.26 GROSS edge but only +0.08 net — turnover (~21.7×/yr) ate +0.18. A causal
hysteresis no-trade band (rebalance a name only when its target moves > δ from the held weight) should cut
churn and capture more of the gross, at minimal signal cost (proven on the metals iter-011 / crypto iter-020).

## Change (one)

Add a causal, path-dependent hysteresis band on iter-002's sector-relative weight book, then the same
`net_from_raw` downstream. `analysis/portfolio/tradfi/iter_003_hysteresis.py`, `--delta` arg.

## IS numbers (trading-day; IS-only) — δ sweep

| δ | net Sharpe | turnover/day | maxDD |
|---|-----------|--------------|-------|
| 0.000 (=iter-002) | +0.08 | 0.0845 | −34.7% |
| **0.005 (chosen)** | **+0.16** | 0.0608 (−28%) | −32.8% |
| 0.010 | +0.16 | 0.0460 (−45%) | −31.7% |
| 0.020 | +0.05 | 0.0327 (−61%) | −34.5% |
| 0.030 | +0.20 | 0.0259 (−69%) | −35.9% |

**Chosen δ=0.005** (conservative edge of the stable {0.005, 0.010} basin, both +0.16): net **+0.16**, gross
**+0.29**, drag +0.13, turnover −28%, maxDD −32.8%, regimes bull **+0.22** / bear **−0.08** / chop **−0.10**.
δ=0.02 craters to +0.05 (signal-distorting) → δ=0.03's +0.20 is a non-robust spike across a collapse valley,
NOT picked (no-cheating: structural param must be IS-robust, not a single-cell peak).

## Cost-capture, NOT de-lever (the key check)

gross held/nudged **+0.26 → +0.29** (renormed ~1 each bar) while drag fell **+0.18 → +0.13** and turnover
−28%. The +0.26 gross edge survives into net; only cost shrank. All-weather profile *improved*: chop
−0.29 → −0.10, bull up, bear ~flat, maxDD down. This is a Pareto improvement, not a sizing artifact.

## Leak-check — PASS

Added `test_iter003_banded_future_bar_no_leak` (corrupt inputs after a cutoff → past net AND lagged
held-book bit-identical despite the path-dependent recursion), a δ=0 bit-identity test, and a
turnover-monotone test. Suite 21/21 green. Sector-neutrality residual 3e-02 of gross (band slightly
desyncs within-sector pairs; book stays materially neutral).

## Verdict — PROMOTED-INTERMEDIATE (new working best)

Net **doubled +0.08 → +0.16** via genuine cost-capture. Still < +0.30 promote bar, and the honest ceiling
is now the **+0.29 gross signal** — turnover is mostly harvested, further band-cranking is de-lever. Kept
as the working stack (sector-relative momentum + band).

## Next

The lever is no longer cost; it's the **gross signal strength + all-weather** (book still bull-only).
**iter-004 = add a within-sector short-term reversal sleeve** (Critic axis #2) — momentum (12-1m) and
1-month reversal are complementary; reversal classically works in CHOP (the weakest regime here). A
diversified mom+rev composite should lift gross and all-weather together.
