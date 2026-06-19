# portfolio-iteration EXPLORATION-008 — 1-2d short-term reversal overlay (REJECTED, honest noise)

**Agent-driven** (user mandate): quant-researcher designed the axis, orchestrator implemented on the
canonical framework, quant-critic adversarially reviewed the result before logging.

**Axis (Candidate A):** add a short-term mean-reversion term to the canonical iter_005 baseline
(walk-forward-λ trend+carry). Crypto-native thesis: trend (7-56d) is slow *position accumulation*
(trend-follower/ETF/OI build-up, positive multi-week return autocorr); a 1-2d reversal is the opposite
agent — forced-leverage overshoot (liquidation cascades, funding-spike squeezes, large taker sweeps)
that snaps back in 8-48h (negative 1-3-candle autocorr). Different timescale, different agent → should
ADD, not fight. Code: `analysis/portfolio/iter_008_reversal.py`.

**Construction (orthogonality keystone):** reversal = mean over h∈{3,6} (1d,2d) of −sign(ret_h),
strictly SHORTER than the shortest trend horizon (21=7d) with a buffer (no h=9). Folded into the
directional core: `core_dir = (1−β)·trend + β·reversal`; `sig = (1−λ)·core_dir + λ·carry`. Sign-based
(same [-1,1] scale as trend/carry). β is a STRUCTURAL param → ROBUSTNESS-SWEPT {0,.05,.10,.15,.20},
NOT walk-forwarded (no-cheating). λ walk-forward UNCHANGED. **Measured on the CANONICAL
per-λ-vol-target-then-stitch net** — β=0 byte-reproduces iter_005 (IS+1.30/OOS+1.37/−23%), confirming
NO iter_007-style raw-stitch re-ordering.

## Result (robustness sweep, walk-forward λ, canonical net)
| β | IS | OOS | dIS | dOOS | maxDD | turnover |
|---|---|---|---|---|---|---|
| 0.00 (baseline) | +1.30 | +1.37 | +0.00 | +0.00 | −23% | 0.296 |
| 0.05 | +1.35 | +1.37 | +0.05 | +0.00 | −25% | 0.303 |
| 0.10 | +1.19 | +1.34 | −0.11 | −0.03 | −27% | 0.321 |
| 0.15 | +0.78 | +1.32 | −0.52 | −0.05 | −37% | 0.349 |
| 0.20 | +0.44 | +1.68 | −0.86 | +0.31 | −42% | 0.380 |

Orthogonality probe: pooled corr(reversal, trend) on IS = **−0.243** (PASS, <0.3 — genuinely
orthogonal at the signal level, NOT collinear cannibalization).

## Pre-registered falsifier verdict (n=16 OOS months)
| gate | result |
|---|---|
| [1] all β cells IS+OOS ≥ baseline−0.05 | **FAIL** (β=0.10 IS +1.19 < 1.25; IS degrades monotonically) |
| [2] signature present already at small β=0.05 | PASS (β=0.05 OOS = baseline) |
| [3] mid-grid (β=0.10) OOS lift ≥ +0.15 | **FAIL** (dOOS −0.03) |
| [4] \|corr(reversal,trend)\| < 0.3 | PASS (−0.243) |
| [5] maxDD ≥ −28% across grid | **FAIL** (β=0.15/0.20 → −37%/−42%) |
| [6] no IS year flips negative | **FAIL** at higher β (IS collapses) |

## Read — REJECT (honest noise / negative)
The overlay is leak-safe, orthogonal, and measured on the canonical net (critic PASS), but it is NOT
accretive. At the only IS-non-degrading weight (β=0.05) the OOS lift is **exactly zero**. As β rises,
IS degrades monotonically (+1.30→+0.44) and maxDD blows out (−23%→−42%). The one "OOS improvement"
(+0.31 at β=0.20) is **cannibalization, not edge** — it appears only where IS has collapsed to +0.44
and DD is −42% (the classic "lift only-at-large-β" trap; OOS-picking β=0.20 would repeat the iter_007
mistake). A sign-based 1-2d reversal, however orthogonal in direction, simply does not pay after
taker cost + funding on this top-20 8h universe and actively levers the tail.

**Critic verdict: PASS on the honesty of the REJECT.** Confirmed (a) β=0 byte-reproduces iter_005 with
PER-λ-vol-target INSIDE the loop — no iter_007 raw-stitch + single-outer-vol-target re-ordering;
(b) all signals past-only (reversal from past closes, w.shift(1), funding fund.shift(-1) on held
weight); (c) β robustness-swept, not OOS-picked; (d) the REJECT falls through multiple independent
gate failures, not one phrasing. Critic-flagged the IS-year gate (was calendar `k<2026`, mixed OOS
months) — **fixed** to split on OOS_CUTOFF.

## Verdict: REJECT — sign-based short-term reversal overlay NOT promoted. Baseline UNCHANGED (iter_005, IS +1.30 / OOS +1.37 / −23%).
## Axis status
- **Sign-based 1-2d reversal overlay: CLOSED.** Orthogonal but unprofitable net + tail-levering.
- If revisited, only at the SIGNAL-STRENGTH level (z-score/rank-conditioned magnitude, NOT sign),
  reusing iter_008's per-λ-vol-target-preserving harness. Note: a magnitude reversal loads hardest on
  exactly the high-vol post-cascade candles where the /rvol denominator is least trustworthy — a real
  scale-leak risk to control before any such retry.
## Next
- iter-009: a genuinely orthogonal axis NOT in the price-trend family — e.g. an OI/positioning or
  basis-derived tilt (carry already harvests funding; basis/OI is the adjacent un-mined structural
  signal), measured on the canonical net, β/weight robustness-proven. (Candidate B per-coin caps was
  de-prioritized: concentration is the inverse-vol book's reward, not pure risk — cf. v3 "concentration
  is signal".)
