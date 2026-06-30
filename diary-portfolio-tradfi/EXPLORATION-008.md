# EXPLORATION-008 — VIX brake + stop-loss (iter-008)

**Date:** 2026-06-30 (user-directed risk primitives)
**Status:** COMPLETE — **WASH/REJECT for promote**; VIX-alone = near-free crash insurance. OOS HIDDEN.
**Cadence:** EXPLORATION (IS-only, Yahoo clean data) · **Commit:** `bf4f82c8` · risk note `iter-008-risk.md`

---

## Hypothesis (user directive)

On clean Yahoo data iter-006 is strong in bull/chop (+0.60/+0.56) but the bear blows out to **−1.23** (the +30
high-beta recent IPOs whipsaw). A **VIX brake** (exogenous crash de-risk) + a **stop-loss** should bound the
bear without killing the strong regimes.

## Change — two risk overlays (outer scalars on the vol-targeted net)

- **VIX brake:** continuous `s = clip(VIX_BASE / VIX[t−1], floor, 1)`, **base=20** (long-run VIX median,
  theory-pinned — NOT IS-fit), **floor=0.50**, past-only. Inert at VIX≤20, binds at VIX≥40. Continuous chosen
  over a step threshold (step is knife-edge: bear −0.35@25 vs −1.24@30 = the IS-fitting the Critic blocked).
- **Stop-loss:** portfolio-level causal drawdown stop (metals-style hysteresis), **D_trip=15.1%** (worst-
  quintile IS rule, not max-net), floor=0.50, re-arm −7.6%. Portfolio-scalar (a per-name stop would break
  per-sector dollar-neutrality). `analysis/portfolio/tradfi/iter_008_vix_stop.py`.

## IS numbers (Yahoo, IS-only) — vs iter-006 (+0.43 / +0.60 / −1.23 / +0.56 / maxDD −25.5%)

| variant | net | bull | bear | chop | maxDD |
|---------|-----|------|------|------|-------|
| **VIX-alone** | **+0.41** | +0.52 | **−0.88** | +0.35 | −25.9% |
| stop-alone | +0.34 | +0.44 | −1.07 | +0.56 | **−20.6%** |
| combined | +0.31 | +0.36 | **−0.48** | +0.35 | −20.8% |

Bear −1.23 → −0.48 (combined; 2022 grind −0.38 → **+0.26**, COVID −11% → −4%). **Bull/chop NOT preserved** —
both dented (bull −0.24, chop −0.21, net −0.12). Combined cost-fragile: 6bps +0.31 → 12bps **+0.10**.

## Verdict — WASH/REJECT for baseline-promote

De-risking a vol-targeted neutral book **structurally trades the strong regimes for the weak one** — no
variant Pareto-dominates iter-006. The honest asymmetry: the bear-fix is **suggestive (N=2 bears, COVID
Sharpe unmeasurable at ~1.5mo)** while the bull/chop cost is **reliably estimated** (long windows). Leak-safe
(combined future-bar + identities, 44 passed). OOS hidden.

**Deployable takeaway:** ship **VIX-alone** as crash insurance — best bear-fix/cost ratio (−1.23 → −0.88 at
~zero net cost). Stop is optional maxDD insurance (−25.9% → −20.6%, preserves chop). Don't stack both.

## Next

The bear-control rests on N=2 bears — unconfirmable. **iter-009 = extend IS history to 2010** (Yahoo has it),
adding 2011 / 2015-16 / 2018-Q4 bears → N≈5, to test whether the momentum edge and the VIX bear-control
GENERALIZE or were a 2-event coincidence. This is the gate before any CONFIRMATION.
