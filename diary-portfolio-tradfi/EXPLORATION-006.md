# EXPLORATION-006 — Momentum-crash brake (iter-006)

**Date:** 2026-06-30
**Status:** COMPLETE — **KEPT; PROMOTE-CANDIDATE** (first to clear the +0.30 IS bar). OOS HIDDEN.
**Cadence:** EXPLORATION (IS-only) · **Commit:** `d95d32c5` · risk note `diary-portfolio-tradfi/iter-006-risk.md`

---

## Hypothesis

iter-005's bear (−0.90) is the 2022 momentum crash (fast 3-1m sleeve whipsaws in the grind-down). The bear
is a **composition** problem — standalone bear Sharpes: 12-1m **−0.08**, 6-1m −0.80, 3-1m −1.23 — so the SLOW
sleeve survives. A leak-safe gate that collapses to the slow sleeve in a bear state should fix bear without
the uniform-de-lever wash that kills bull (the metals trap).

## Change (one) — fast-sleeve crash gate

In a past-only market bear state `g = 1{ EW-universe trailing 12m return < 0 }`, blend toward the bear-robust
12-1m sleeve: `raw = (1−g)·EW{3-1,6-1,12-1} + g·sleeve(252)`, then the unchanged iter-003 band δ=0.005 + core
vol-target. Thresholds **pre-registered, theory-pinned** (252d = the 12-1m sleeve's own lookback, canonical
TSMOM/Daniel-Moskowitz bear-state, sign-0). Chose the conservative `ret252` gate, NOT the max-net MA200 cell
(no curve-fitting). `analysis/portfolio/tradfi/iter_006_crashbrake.py`.

## Why not Barroso / drawdown vol-brake

net0 is already 63d vol-targeted, so regime vols barely differ (bull~15 / bear~17 / chop~14%). Both
IS-calibrated vol/DD overlays WASH net (+0.20→+0.13..+0.21) and WORSEN bear (−0.90→−1.0..−1.1) — they scale
all sleeves uniformly and can't exploit that only the slow sleeve survives. The fix had to be compositional.

## IS numbers (trading-day; IS-only)

| Metric | iter-006 | iter-005 |
|--------|----------|----------|
| **Net Sharpe** | **+0.31** | +0.20 |
| Gross Sharpe | +0.51 | +0.40 |
| Max Drawdown | −29.9% | −31% |
| **Per-regime** | bull **+0.42** / bear **−0.54** / chop **+0.26** | +0.38 / −0.90 / +0.26 |
| All-weather | 2/3 (bull+chop) | 2/3 |
| Turnover | 0.109/day (−5%) | 0.114/day |

**Bear −0.90 → −0.54.** Named target (2022 grind) fixed: −0.73/−11% → **−0.01/−1%** (gate fires 79% of bear).
**Bull/chop preserved** (+0.38→+0.42, +0.26 flat; gate fires 1.2% of bull). **Clears the +0.30 promote bar.**

## Honest blemish

COVID (2-month V-crash) worsens −1.94 → −5.85: a 12m-trend gate structurally LAGS V-crashes. The entire
residual aggregate-bear deficit is this COVID drag, not the 2022 target. → a *fast* V-crash overlay is the
natural orthogonal next complement (iter-008 candidate), NOT a re-tune of the pinned 252 window.

## Verdict — KEEP / PROMOTE-CANDIDATE (pending Critic + iter-007 comparison)

First book to clear net ≥ +0.30 (the promotable bar) with bull/chop positive, bear survivable (maxDD −29.9%),
the 2022 crash neutralized. Leak-safe (future-bar self-check + identity g=0→iter-005 / g=1→12-1m + gate
past-only; 36 passed). OOS hidden. **NOT yet promoted** — held against the user-directed iter-007 optimizer;
the best of {iter-006, iter-007} goes to the full Critic adversarial audit, then the CONFIRMATION/OOS-reveal
decision (the user's call).

## Next

- iter-007 (running) = portfolio-optimization upgrade (mean-variance + risk model + constraints, weekly
  rebalance) per user directive — the candidate-or-supersede for CONFIRMATION.
- iter-008 candidate = fast V-crash overlay (the COVID residual), orthogonal to the pinned 12m bear gate.
