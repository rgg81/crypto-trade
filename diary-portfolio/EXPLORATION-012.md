# portfolio-iteration EXPLORATION-012 — TAKER-FLOW IMBALANCE (REJECT-as-overlay / PROMOTE-standalone-to-CONFIRM)

**Agent-driven** (user mandate): quant-researcher designed the axis + pre-registered the falsifier,
orchestrator implemented on the canonical framework, quant-critic adversarially reviewed (PASS on
honesty + leak-safety) and materially refined the verdict before logging.

**Axis:** the first MICROSTRUCTURE factor — aggressive market-buy vs market-sell taker order flow. The
8h klines carry `taker_buy_volume` (aggressive lifts) and `volume`; the per-candle flow imbalance
`imb = taker_buy_volume/volume − 0.5 ∈ [−0.5,+0.5]` measures whether aggressors were net lifting offers
(informed/momentum DEMAND) or net hitting bids (distribution). A column always on disk, never used.
Code: `analysis/portfolio/iter_012_takerflow.py`.

**Signal (PAST-ONLY, all inputs known at close[t], trade t+1 via `.shift(1)` on the weight):**
`imb[t] = taker_buy/vol − 0.5` → `flow_sm = imb.rolling(42).mean()` (~14d, == HORIZONS[1]; per-candle
imbalance is noise) → `flow_z` = cross-sectional z-score of `flow_sm` across the ELIGIBLE PIT top-20
(row-demean/row-std, `axis=1` same-time only — no time leak). VOLUME version is headline (clean
participation primitive); quote-volume version printed as a cross-check (near-identical). Direction
tested BOTH ways (sign flip); the data picks **MOMENTUM** (long aggressive-buy), contrarian is
symmetrically negative — sign is mechanism-determined, NOT OOS-picked.

**Blend:** `sig = (1−λ)·trend + λ·carry + γ·flow_z` overlay BEFORE /rvol, then the IDENTICAL iter_005
per-λ-vol-target-then-`wf.walkforward`-stitch. **γ=0 BYTE-REPRODUCES iter_005 (IS +1.30 / OOS +1.37 /
−23%)** — verified EXACT (critic confirmed per-λ vol-target INSIDE the loop, no re-ordering). γ is
STRUCTURAL → robustness-swept {0,.05,.10,.15,.20,.30}, NOT walk-forwarded, NEVER OOS-picked. λ
walk-forward UNCHANGED. OOS_CUTOFF=2025-03-24 intact.

## Standalone flow_z (cost honesty — STRONG, unlike the prior 4 rejects)
| | IS | OOS | maxDD | netTot | turnover |
|---|---|---|---|---|---|
| **MOMENTUM 1× taker** | **+1.67** | **+1.59** | −38% | +3495% | 0.104 |
| MOMENTUM 2× taker | +1.45 | +1.39 | −41% | +2049% | 0.104 |
| CONTRARIAN 1× taker | −2.10 | −1.99 | −100% | −100% | 0.104 |
| MOMENTUM gross (pre-cost) | +1.88 | +1.79 | — | — | — |
| qv-version 1× MOM | +1.65 | +1.56 | −39% | +3316% | 0.104 |

MOMENTUM net%/yr **positive every year 2020–2026**. Turnover 0.104 is **a third of the baseline's
0.296** — the smoothed 42-bar signal is turnover-cheap. The edge **survives 2× taker** (+1.45/+1.39),
so it is NOT a gross-only / turnover-eaten mirage. This is a **categorically different** standalone read
from iter_008/010/011, where the signal lost even *gross*.

## Orthogonality — genuinely independent of trend (THE key question)
| metric | value | read |
|---|---|---|
| corr(per-candle imb, same-candle ret) IS | **+0.297** | informed flow, NOT "price went up" (would be ~+0.8) |
| corr(flow_z, trend) IS | **+0.233** | < 0.50 → independent factor, not a momentum re-skin |
| corr(flow_z, carry) IS | +0.045 | orthogonal to carry too |
| **β(flow net ~ trend net), IS-fit** | **+0.03** | flow net carries ~no trend loading |
| **RESIDUAL OOS Sharpe** (flow ⟂ trend) | **+1.37** vs raw +1.36 | **independently additive — NOT a 2nd momentum factor** |

The residual-orthogonality regression (critic Rec 3): regressing the standalone flow_z net on the
baseline TREND net (IS-fit β, applied to the whole series) leaves the residual OOS Sharpe essentially
UNCHANGED (+1.37 vs +1.36 raw) at β=+0.03. The standalone edge is **not** the trend book in disguise —
it is a distinct, orthogonal microstructure factor.

## Blend γ sweep (walk-forward λ, canonical net) — lift is BACK-LOADED
| γ | IS | OOS | dIS | dOOS | maxDD | turn |
|---|---|---|---|---|---|---|
| 0.00 (baseline) | +1.30 | +1.37 | +0.00 | +0.00 | −23% | 0.296 |
| 0.05 | +1.45 | +1.33 | +0.15 | **−0.04** | −23% | 0.286 |
| 0.10 | +1.49 | +1.47 | +0.19 | **+0.10** | −23% | 0.280 |
| 0.15 | +1.53 | +1.59 | +0.23 | +0.22 | −23% | 0.272 |
| 0.20 | +1.58 | +1.88 | +0.28 | +0.51 | −23% | 0.265 |
| 0.30 | +1.59 | +2.26 | +0.29 | +0.89 | −20% | 0.252 |

Every cell: **IS lifts monotonically** (+0.15 → +0.29), DD never worse (CUTS to −20% at γ=0.30), all IS
years positive. BUT the OOS lift is **back-loaded**: at the conservative small/mid γ where you would
actually deploy an overlay (0.05/0.10) the lift is −0.04 / +0.10 — below the pre-registered materiality
bars. It only becomes material at γ ≥ 0.20, i.e. when the blend is tilting hard toward what is itself a
+1.6-OOS standalone factor. The OOS curve is **monotone to the grid edge** (γ=0.30 untested beyond) —
the fixed grid cannot locate the natural weight, which is exactly why the verdict routes to CONFIRM not
PROMOTE.

## Smoothing-window robustness (prove the headline 42 is not a tuned cell)
| win | corr→trend | sa IS | sa OOS | g05 OOS | g10 OOS |
|---|---|---|---|---|---|
| 21 | +0.241 | +1.55 | +1.06 | +1.30 | +1.40 |
| **42** | **+0.233** | **+1.67** | **+1.59** | +1.33 | +1.47 |
| 84 | +0.189 | +1.46 | +1.28 | +1.31 | +1.43 |
| 168 | +0.126 | +1.36 | +0.95 | +1.31 | +1.33 |

Every window: standalone positive IS+OOS, blend g05/g10 OOS ≥ baseline (within noise). 42 is the best
standalone but NOT a knife-edge cell — the factor is robust across the whole {21,42,84,168} smoothing
range. (corr→trend falls with longer windows, as expected: longer smoothing = more trend-like.)

## Pre-registered falsifier verdict (n=16 OOS months)
| gate | result |
|---|---|
| [1] all γ cells IS+OOS ≥ baseline−0.05 | PASS |
| [2] small γ=0.05 dOOS ≥ +0.10 (not only-at-large) | **FAIL** (dOOS −0.04) |
| [3] mid γ=0.10 dOOS ≥ +0.20 | **FAIL** (dOOS +0.10) |
| [4] corr(flow_z, trend) < 0.50 (independent, not re-skin) | PASS (+0.233) |
| [5] maxDD ≥ −28% across grid | PASS (stretch: CUTS DD to −20% at γ=0.30) |
| [6] no IS year flips negative (blend) | PASS |
| [7] standalone net-positive at 1× AND 2× taker | PASS |

## Read — REJECT-as-overlay, PROMOTE-standalone-to-CONFIRM (NOT "noise")
Two claims must be separated (critic Q3):
- **As an accretive OVERLAY at the pre-registered small/mid γ: REJECT (honest).** Gates [2]+[3] fail —
  the blend OOS lift at γ=0.05/0.10 (−0.04 / +0.10) is inside the n=16-OOS-month paired noise band. You
  should NOT bolt this on at a conservative weight on the current evidence. Same disciplined down-call
  as EXPLORATION-011.
- **As a FACTOR: this is NOT noise — it is the strongest portfolio factor surfaced since the carry
  tilt.** The standalone is +1.67 IS / +1.59 OOS, survives 2× taker, turnover-cheap, positive EVERY
  year, orthogonal to trend (+0.233) AND carry (+0.045), with a residual OOS Sharpe of +1.37 at β=+0.03
  — i.e. independently additive, not a second momentum factor in disguise. Filing it under the same
  flat "NOISE/REJECT" label as the genuinely-inert liqfade (which lost even gross) would badly
  under-sell the result. The `iter_012` script's auto-printed "NOISE" verdict line is the gate-logic
  routing on [2]+[3] failing; the FACTOR is real.

The honest residual ambiguity the gates correctly surface: the blend lift is back-loaded and the OOS
curve is monotone to the grid edge, so a fixed-γ grid cannot tell apart "real factor with a naturally
large weight" from "return-stacking a 2nd factor as γ→0.5." The β=+0.03 / residual +1.37 result tilts
strongly toward the former, but the *deployable* weight is unproven on a fixed grid — that is a
CONFIRMATION question (walk-forward-γ), not an EXPLORATION one.

## Critic verdict: PASS (honesty + leak-safety), with a verdict-framing refinement.
Confirmed (a) γ=0 byte-reproduces iter_005 EXACTLY with per-λ-vol-target INSIDE the loop (no
re-ordering); (b) flow_z is genuinely past-only — z-score row-stats are `axis=1` (cross-coin, same
time), smoothing trailing, weight `.shift(1)`, funding `fund.shift(-1)` on held weight, identical lag
chain to iter_005/iter_011; (c) same 206-coin PIT top-20 universe, zero survivorship (taker columns are
extra columns of existing rows); (d) cost booked on actual post-overlay weight change, 1× both sides +
2× stress, turnover-decreasing-with-γ is plausible (slow signal smooths the book), not a red flag; (e)
γ robustness-swept not OOS-picked, λ walk-forward + OOS_CUTOFF intact, IS-year check on the cutoff. The
critic's material refinement: record this as REJECT-as-overlay-at-small-γ + PROMOTE-standalone-to-CONFIRM,
NOT a flat noise close — a different status from EXPLORATION-011.

## Verdict: REJECT as a small-γ accretive overlay (baseline UNCHANGED: iter_005, IS +1.30 / OOS +1.37 / −23%). PROMOTE the standalone taker-flow factor to a walk-forward-γ CONFIRMATION. First non-trend factor since carry to clear the standalone bar decisively.

## Axis status
- **Taker-flow imbalance (momentum direction) factor: OPEN — promoted to CONFIRMATION, NOT closed.**
  Standalone +1.59 OOS, 2×-cost-robust, orthogonal to trend AND carry, residual-additive (β +0.03).
  This is the encouraging counter-example to the price-derived-reversal family (iter_008/010/011, all
  closed): a fresh non-price column DOES carry orthogonal signal on this universe.
- **What's unresolved (the CONFIRMATION question):** the blend lift is back-loaded + monotone to the
  grid edge, so the natural/deployable γ is unproven on a fixed grid. A fixed small γ is a REJECT; the
  factor may still earn its weight under honest selection.

## Next
- **iter-013 (CONFIRMATION-track): walk-forward-γ taker-flow.** Walk-forward-select γ on past net
  Sharpe (the same machinery that legitimized λ in iter_005), report honestly-selected-γ OOS + DD +
  the residual-orthogonalized OOS. This directly resolves real-factor-vs-return-stacking: if WF-γ
  converges small and the lift evaporates → return-stacking (REJECT); if it converges ~0.20–0.30 with
  the lift intact and DD non-worse → real factor (PROMOTE to baseline). Reveal OOS once, full gauntlet.
- Adjacent (critic Path Forward): a **taker-flow REGIME gate on gross exposure** (market-wide aggressive-
  flow scaling the book — attacks the −23% DD lever iter_009 localized to correlated regime exposure),
  and the roadmap's **OI / perp-spot-basis** structural families, now with empirical encouragement that
  non-price microstructure columns are not exhausted.
