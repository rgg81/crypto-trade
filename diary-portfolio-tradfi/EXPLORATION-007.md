# EXPLORATION-007 — Portfolio-optimization upgrade (iter-007)

**Date:** 2026-06-30 (user-directed: optimization + weekly rebalance + literature research)
**Status:** COMPLETE — **NEGATIVE/REJECT** (optimization does NOT beat naive demean at N≈40). OOS HIDDEN.
**Cadence:** EXPLORATION (research + IS prototype) · **Commit:** `725a37d5` · brief `iter-007-brief.md`

---

## Hypothesis (user directive)

Replace the naive cross-sectional-demean weighting with proper portfolio optimization (mean-variance with a
risk model + neutrality/position/turnover constraints) and test weekly rebalance — the institutional
market-neutral stack. The risk model should *use* the 62%-Semi/Tech covariance the naive demean ignores,
breaking the gross ceiling.

## What was done

Web research (cited) + a full cvxpy MVO prototype (`analysis/portfolio/tradfi/iter_007_probe.py`):
`max α'w − λ·w'Σw` s.t. Σw=0, |w|≤cap, gross=1, optional β-/sector-neutral; Ledoit-Wolf shrinkage Σ
(rolling, past-only); 21 (λ,cap,constraint) configs × {daily, weekly}.

## IS numbers (trading-day; IS-only) — optimization LOSES

| config | net | gross | bull/bear/chop | turn |
|--------|-----|-------|----------------|------|
| **iter-005 naive, daily (ref)** | **+0.20** | **+0.40** | +0.38/−0.90/+0.26 | 0.114 |
| naive, weekly | +0.12 | +0.22 | +0.23/−1.13/+0.49 | 0.061 |
| best MVO (λ=10, βN, weekly) | +0.07 | +0.17 | −0.05/−0.33/+1.95 | 0.096 |
| best plain MVO (λ=200, daily) | +0.05 | +0.31 | +0.27/−0.75/−0.41 | 0.193 |

**Optimization beats naive? NO, by −0.13** (best MVO +0.07 vs naive +0.20). Decisive: best MVO **gross +0.31 <
naive gross +0.40** → the variance penalty discards signal, so no cost trick recovers it. Weekly also loses
(−0.08); daily wins. Pre-registered falsifier (best-MVO gross < naive gross +0.40) MET → REJECT.

## Why (cited research)

1. Naive 1/N-style demean routinely beats sample-MVO at moderate N — estimation error swamps the optimization
   gain (**DeMiguel-Garlappi-Uppal 2009 RFS**; **Michaud 1989**).
2. The naive demean **is** MVO with Σ=identity = maximal Ledoit-Wolf shrinkage (δ→1); the probe independently
   located optimal δ→1 here. So we're already at the optimum the optimizer converges to.
3. For a directional momentum alpha the risk model belongs in the neutralization **constraints** + vol-scaling
   crash control, NOT a variance objective (**Barroso-Santa-Clara 2015**; **Daniel-Moskowitz 2016 JFE**).

## Verdict — REJECT (clean falsification; baseline unchanged = iter-006 +0.31)

A genuine "weapon tried and ruled out." `cvxpy==1.9.2` added as dormant infra — revisit MVO only at N≳80–100
(force the LW target to identity, which provably reproduces the naive book). OOS hidden throughout.

**Orthogonal find handed forward:** a HARD beta-neutral constraint transforms chop (+0.26 → +1.05 daily /
+1.95 weekly) but wrecks bear — a future *conditional-in-chop* candidate, not a now-change.

## Next

The real upside is the BEAR axis (crash control), not weight construction. iter-006 (+0.31) goes to the
Critic; the COVID V-crash residual + the beta-neutral-in-chop find are the live forward axes — pending the
Critic's overfitting verdict before stacking more.
