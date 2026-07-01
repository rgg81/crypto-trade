# iter-015 — COST DISCIPLINE on the CONFIRMED iter-013 baseline

**Date:** 2026-07-01 · **Status:** STRONG cost-capture found — **net@2× +0.42 → +0.68** (clears the
2×-cost ≥+0.50 bar) while **gross HELD +0.81 → +0.78** and **per-year 13/16 → 14/16**; turnover cut
**−75%** (0.0939 → 0.0238/day). **This is real cost-capture, NOT de-lever.** OOS UNTOUCHED (IS-only,
< 2025-03-24; no OOS number computed here).
**Scripts:** `analysis/portfolio/tradfi/cost_teardown.py`, `analysis/portfolio/tradfi/iter_015_cost.py`
**Signals UNCHANGED** — only the turnover / rebalance MECHANICS move (band width + rebalance frequency).

## Goal
Close the gross→net gap of the deployed iter-013 book (λ=0.25, band δ=0.005, VIX ON): gross **+0.81**
→ net **+0.61** @6bps → **+0.42** @12bps, so the book is 2×-cost-ROBUST (net ≥+0.50 @12bps) while
PRESERVING the gross edge (~+0.81) and the 13/16-year profile. Judge IS-only on {net@1×, net@2×,
turnover/day, gross(cost-off), per-year 13/16}. A genuine cost win LIFTS net (esp. @2×) while HOLDING
gross — a change that drops gross is a de-lever / signal-loss, reported as such.

## Task 1 — turnover teardown (`cost_teardown.py`, IS-only, VIX-independent)
Deployed banded turnover **0.0939/day**; the δ=0.005 band already removes **31%** of the raw target
churn (unbanded 0.1357). Turnover-implied annual cost = **1.4% @6bps / 2.8% @12bps**.

**Exact additive sub-book attribution** (deployed target book splits EXACTLY into 3 sleeve sub-books
wc_MOM + wc_LTR + wc_TSMOM = w_tgt; max resid 6e-17):

| sleeve | Σ\|Δsub\|/day | share of book movement |
|--------|--------------|------------------------|
| **MOM** (crash-braked multi-horizon) | **0.1199** | **75%** |
| LTR (3y-1y reversal) | 0.0223 | 14% |
| TSMOM (sign 12m / rvol) | 0.0173 | 11% |

**The MOMENTUM sleeve is the cost engine (75% of book movement)** — it is 0.75·neutral-weight AND the
intrinsically churniest signal. Within momentum, the **fast 3-1m (63/21) horizon churns 3× the slow
12-1m** (standalone banded 0.163 vs 0.054); the bear-gate adds ~zero churn (0.099 no-gate → 0.101
gated). LTR is nearly inert (0.029 banded standalone — a slow value signal).

**Small/marginal-trade distribution** (per-name \|Δw\| events, deployed banded book): 81% of trade
events are below τ=0.005 but they are only **13% of turnover**; 49% of events (below 0.0002, median
trade size) are just **2% of turnover**. So the cost is **NOT** a long tail of tiny re-snaps — it is
concentrated in the fewer, larger rebalances (top ~19% of trades carry ~87% of flow). Implication: a
wider band alone captures only part of the win; **cutting rebalance frequency (which kills the big
trades on non-rebalance days) is the bigger lever** — confirmed below.

## Task 2 — LEVER A: hysteresis band δ sweep (freq=1 daily; deployed λ=0.25 + VIX)
| δ | net@1× | net@2× | turn/day | gross | +yrs |
|------|--------|--------|----------|-------|------|
| **0.005 (current)** | +0.61 | +0.42 | 0.0939 | **+0.81** | 13/16 |
| 0.010 | +0.67 | **+0.52** | 0.0700 | **+0.81** | 13/16 | ← best δ that HOLDS gross exactly |
| 0.015 | +0.55 | +0.43 | 0.0552 | +0.66 | 13/16 |
| 0.020 | +0.63 | +0.53 | 0.0440 | +0.72 | 13/16 |
| 0.030 | +0.65 | +0.59 | 0.0307 | +0.71 | 13/16 |
| 0.050 | +0.50 | +0.46 | 0.0204 | +0.54 | 10/16 | ← over-widened, gross + years collapse |

Band alone: δ=0.010 lifts net@2× to +0.52 with gross fully held; wider δ (0.02–0.03) buys more net@2×
but shaves gross toward +0.71 (mild staleness). Contrary to iter-003 (δ=0.02 cratered the momentum-only
book), the 4-component book **tolerates δ up to ~0.03** before gross erodes — the diversified book is
more band-robust. δ=0.05 breaks it (10/16).

## Task 3 — LEVER B: rebalance frequency (δ=0.005 current band; deployed λ=0.25 + VIX)
| freq | net@1× | net@2× | turn/day | gross | +yrs |
|------|--------|--------|----------|-------|------|
| **1 (daily, current)** | +0.61 | +0.42 | 0.0939 | +0.81 | 13/16 |
| 2 | +0.64 | +0.49 | 0.0734 | +0.80 | 12/16 |
| 5 (weekly) | +0.61 | +0.51 | 0.0520 | +0.72 | 13/16 |
| 10 | +0.61 | +0.53 | 0.0387 | +0.69 | 14/16 |

Frequency alone lifts net@2× to +0.53 but **erodes gross more** than the band (0.81 → 0.69 at f=10) —
some slow-signal is lost holding a stale target 10 days with a tight δ=0.005 band that re-snaps hard
on refresh days. Frequency alone does not hold gross; it needs the band widened to complement it.

## BEST config — JOINT band × freq: **δ=0.020, freq=10**
| config | net@1× | net@2× | turn/day | gross | +yrs |
|--------|--------|--------|----------|-------|------|
| baseline (δ=0.005, f=1) | +0.61 | +0.42 | 0.0939 | +0.81 | 13/16 |
| **BEST (δ=0.020, f=10)** | **+0.73** | **+0.68** | **0.0238** | **+0.78** | **14/16** |

Selected IS-only by the pre-registered rule *max net@2× subject to gross ≥+0.75 AND +yrs ≥13*. It
lifts **net@2× +0.42 → +0.68** (clears +0.50 with margin), net@1× +0.61 → +0.73, cuts turnover **−75%**
(annual 12bps cost 2.8% → 0.7%), improves per-year 13 → 14 — **all while gross holds +0.81 → +0.78
(within noise).** The δ=0.020 column is a broad plateau (f=5 → net@2× +0.64/gross +0.76; f=10 → +0.68/
+0.78), not a knife-edge: widening the band AND slowing the refresh are complementary — the band keeps
the refreshed target from re-snapping hard, so the slow-signal edge (gross) survives the lower cadence.

**Is it real cost-capture or de-lever?** REAL cost-capture: gross(cost-off) is essentially preserved
(+0.81 → +0.78, Δ −0.03) while net@2× jumps +0.26 — the lift comes from paying **less cost on the same
edge**, not from de-levering the signal. A de-lever would have dropped gross materially (as δ=0.05 and
f=10-alone partially do); this cell does not.

## Discipline / integrity
- **OOS UNTOUCHED** — every metric is IS-only (< 2025-03-24); neither script computes/looks at OOS
  (no `--confirm` path exists in `iter_015_cost.py`). Signals (mom/LTR/TSMOM/VIX weights) UNCHANGED —
  only turnover mechanics (δ, freq).
- **Leak-safe:** `stride_hold` ffills only strictly-past rebalance rows (integer-position stride);
  band recursion is causal; `.shift(1)` execution lag unchanged. Future-bar self-check PASS in both
  scripts. New pytest `test_iter015_two_lever_future_bar_no_leak` (BOTH levers active) PASS.
- **Identity:** freq=1 & δ=0.005 reproduces the iter-013 deployed banded book bit-for-bit
  (`test_iter015_freq1_reproduces_iter003_band_bit_identical`); monotone turnover reduction test PASS.
  Suite green (84 passed, 2 CI-skips).

## Next
The **δ=0.020, freq=10** cost-robust config is the iter-015 candidate: net@2× +0.68 (2×-cost-ROBUST),
gross held, 14/16. Next EXPLORATION could micro-search the δ=0.015–0.025 × freq=5–10 plateau for the
robust interior (avoid the corner), and/or a per-sleeve cadence (refresh the fast momentum horizon
slower than the slow — it drives 75% of churn). CONFIRMATION / OOS-reveal decision deferred to QR.
