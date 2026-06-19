# portfolio-iteration EXPLORATION-011 — liquidation-cascade FADE (REJECT, honest noise)

**Agent-driven** (user mandate): quant-researcher designed the axis, orchestrator implemented on the
canonical framework, quant-critic adversarially reviewed the REJECT before logging (PASS).

**Axis:** add a uniquely-crypto, contrarian **liquidation-cascade fade** to the canonical iter_005
baseline (walk-forward-λ trend+carry). Thesis: liquidation cascades are forced-deleverage overshoots
that snap back in 8-48h. Detect the forced-deleverage candle from OHLCV and FADE the overshoot:
violent DOWN-flush → LONG the snap-back at open[t+1]; violent UP-spike (forced short-covering) →
SHORT. Aimed at (a) being orthogonal to trend+carry and (b) cutting the −23% DD (iter_009 showed the
DD is correlated portfolio-wide trend reversals — a fade that's LONG when many coins flush together
should buffer exactly that). Code: `analysis/portfolio/iter_011_liqfade.py`.

**Why this is NOT iter_008 (the pitch):** iter_008 rejected a CONTINUOUS, unconditional `−sign(ret_h)`
reversal on EVERY coin-candle (orthogonal but unprofitable + tail-levering). liqfade is
**EVENT-TRIGGERED and SPARSE** — fires only on detected cascade candles (~36 events/month across the
top-20, 2350 IS / 471 OOS). It also fixes iter_008's flagged scale-leak: the fade is a **fixed ±1
event flag, NEVER divided by the contaminated post-cascade rvol** — after the overlay enters the
shared `/rvol` step, the large suspect denominator SHRINKS (not levers) the post-cascade contribution.

**Detector (past-only, all known at close[t], `.shift(1)` excludes candle t):**
`rng_ratio = (high−low)/open ÷ trailing-median₉₀`; `vol_ratio = volume ÷ trailing-mean₉₀`;
`cascade = (rng_ratio≥3.0) AND (vol_ratio≥2.5) AND eligible-top20`; `fade_dir = −sign(close/open−1)`.

**Blend:** `sig = (1−λ)·trend + λ·carry + γ·liqfade` overlay BEFORE /rvol, then the IDENTICAL iter_005
per-λ-vol-target-then-`wf.walkforward`-stitch. **γ=0 BYTE-REPRODUCES iter_005 (IS +1.30 / OOS +1.37 /
−23%)** — verified, with per-λ vol-target INSIDE the loop (no iter_007 raw-stitch re-ordering). γ is
STRUCTURAL → robustness-swept {0,.05,.10,.15,.20}, NOT walk-forwarded, NEVER OOS-picked. λ
walk-forward UNCHANGED.

## Standalone liqfade (cost honesty — a gross-only edge is a REJECT)
| | IS | OOS | maxDD | turnover |
|---|---|---|---|---|
| 1× taker | −1.26 | +0.09 | −99% | 0.345 |
| 2× taker | −1.43 | −0.03 | −100% | 0.345 |
| **gross (pre-cost)** | **−1.08** | **+0.20** | — | — |

The fade has **NO standalone edge even gross** — even RAW (pre-vol-target, pre-cost) it is IS −0.96 /
OOS −0.38. The −99% is a near-1-coin degenerate book under vol-targeting (median 0 active coins/candle,
active only 19.8% of the time), but the gross-negative read does the rejecting, not the vol-target
artifact. The snap-back simply does not pay on the top-20 8h universe.

## Blend γ sweep (walk-forward λ, canonical net)
| γ | IS | OOS | dIS | dOOS | maxDD | turn |
|---|---|---|---|---|---|---|
| 0.00 (baseline) | +1.30 | +1.37 | +0.00 | +0.00 | −23% | 0.296 |
| 0.05 | +1.34 | +1.36 | +0.04 | −0.01 | −22% | 0.295 |
| 0.10 | +1.31 | +1.35 | +0.01 | −0.02 | −25% | 0.297 |
| 0.15 | +1.31 | +1.34 | +0.01 | −0.03 | −25% | 0.295 |
| 0.20 | +1.30 | +1.33 | +0.00 | −0.04 | −25% | 0.298 |

Orthogonality: on-event corr(liqfade, trend) on IS = **−0.290** (PASS, genuinely contrarian; the
unconditional corr is −0.055 by sparsity). The blend OOS **decays monotonically** with γ; IS is
essentially flat. No material lift anywhere.

## Detector + hold robustness (prove the REJECT is not a knob artifact — committed in `sensitivity()`)
7 variants, RANGE_K∈{2.5..6}, VOL_K, HOLD∈{1,2,3} (event counts 288→6589): **no variant lifts OOS
materially.** Best OOS is +1.38 (RANGE_K=5/6, the rarest detectors, +0.01 = noise) and those leave
DD unchanged at −23% (the fade barely touches the book). Every cell is dOOS within ±0.02 of baseline.
The cascade fade is inert-to-slightly-negative across the entire reasonable parameter space.

## Pre-registered falsifier verdict (n=16 OOS months)
| gate | result |
|---|---|
| [1] all γ cells IS+OOS ≥ baseline−0.05 | PASS |
| [2] signal present at small γ=0.05 | PASS |
| [3] mid-grid (γ=0.10) OOS lift ≥ +0.15 | **FAIL** (dOOS −0.02) |
| [4] on-event \|corr(liqfade,trend)\| < 0.3 | PASS (−0.290) |
| [5] maxDD ≥ −28% across grid | PASS (stretch: γ=0.05 grazes −22% but dOOS −0.01) |
| [6] no IS year flips negative | PASS |
| [7] standalone net-positive at 1× AND 2× taker | **FAIL** (no edge even gross) |

## Read — REJECT (honest noise)
The detector is leak-safe (future-perturbation leak test: 0 past cells changed), genuinely sparse
(~36 events/mo), and genuinely contrarian (on-event corr −0.29 to trend). **But it carries no net
alpha.** Standalone it loses even gross; blended, every γ cell decays OOS monotonically (best dOOS
−0.01) and IS is flat — there is **no lift on IS OR OOS**, and the −23% DD does **not** get cut on any
positive cell (the one −22% graze at γ=0.05 comes with dOOS −0.01, i.e. noise, not a DD win). The
answer to the key question — *does fading cascades cut the DD and/or add OOS, on IS too?* — is **no on
all counts**. This is NOT an OOS-mirage trap (iter_008's failure mode); it's simply an inert signal.

**Critic verdict: PASS on the honesty of the REJECT.** Confirmed (a) γ=0 byte-reproduces iter_005 with
per-λ-vol-target INSIDE the loop (no iter_007 re-ordering); (b) all detector stats past-only
(`.shift(1)`), weight `.shift(1)`, funding `fund.shift(-1)` on held weight, HOLD>1 ffill uses only past
triggers; (c) γ robustness-swept not OOS-picked, λ walk-forward + OOS_CUTOFF intact, IS-year check
splits on the cutoff; (d) the REJECT is conservative — no removed leak would manufacture an edge; the
standalone −99% is a legit signal-quality read and the artifact-free blend independently justifies the
REJECT. Critic found a diagnostic-only bug during dev (`liqfade.where(elig)!=0` counted NaN cells,
inflating the event count to 1.3M and the on-event corr) — **fixed** to `(liqfade!=0)&elig`; the
load-bearing numbers (blend sweep, standalone, γ=0 repro) never used the buggy mask.

## Verdict: REJECT — liquidation-cascade fade NOT promoted. Baseline UNCHANGED (iter_005, IS +1.30 / OOS +1.37 / −23%). 5th consecutive reject.

## Axis status
- **OHLCV-detected liquidation-cascade fade: CLOSED.** Orthogonal/contrarian and leak-safe, but no net
  (or gross) edge on the top-20 8h universe; does not cut the DD.
- **Pattern across iter_008/010/011:** every price-derived contrarian/short-horizon overlay (sign
  reversal, magnitude, event-fade) is orthogonal but inert-or-negative net. The reversal/fade
  *direction family* is exhausted on this universe; the snap-back does not pay after taker cost.
- A future cascade retry would need a **non-OHLCV trigger** (real liquidation-volume feed / OI-drop /
  forced-flow proxy) and likely a **longer hold or a regime gate**, not a tighter OHLCV detector knob
  (7 detector variants all inert here).

## Next
- iter-012: pivot OFF the price-trend/reversal family entirely (3 consecutive rejects in it). The DD
  lever still lives in **correlation/regime gross exposure** (iter_009 localized it there and it remains
  the only untried DD axis) — e.g. a portfolio-correlation or vol-regime gross-scaling overlay,
  robustness-proved on the canonical net, critic-gated. OR a genuinely new STRUCTURAL signal family
  (OI/positioning, perp-spot basis) per the roadmap.
