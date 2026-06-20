# portfolio-iteration EXPLORATION-016 — FUNDING-ACCELERATION factor (REJECT: orthogonal but NO edge)

**Axis:** the 2nd-order funding signal — the funding's DYNAMICS (change / slope), distinct from the
funding LEVEL the book already trades via CARRY. Crypto-native crowding-dynamics hypothesis: funding
RISING fast = the crowd piling into longs (a squeeze building → short early, ahead of the unwind);
funding COLLAPSING = capitulation / de-crowding (reversal). A coin can sit at a HIGH positive funding
level (carry already shorts it) while funding is FALLING (longs unwinding) — a state INVISIBLE to a
level-only signal. Code: `analysis/portfolio/iter_016_fundaccel.py`.

**Signal (PAST-ONLY, all inputs known at close[t], trade t+1 via `.shift(1)` on the weight):**
`f_mean[t] = funding.rolling(9).mean()` → `accel[t] = f_mean[t] − f_mean[t−9]` (DIFF form, the slope
of the trailing funding mean) → `accel_z` = cross-sectional z-score of `accel` across the ELIGIBLE
PIT top-20 (row-demean/row-std, `axis=1` same-time only — no time leak). IDENTICAL transform + lag
chain to iter_012's `flow_z`. MEAN_WIN=9 == iter_004's carry `M_FUND`, so accel is the **slope of the
very series carry takes the LEVEL of** — the cleanest apples-to-apples level-vs-change test. A MACD
form (short funding-mean − long funding-mean) is built as a cross-check (corr +0.81 to DIFF — the two
forms agree). Direction tested BOTH ways; the data picks the **IS-better** sign, NOT OOS.

**Leak-safety / alignment (HARD sanity gate, PASS):** the raw funding panel underlying the
acceleration reproduces the book's carry signal `−sign(fund.rolling(9).mean())` **byte-for-byte**
(max |Δ| = 0.0). This proves the funding ms-epoch alignment is identical to iter_004/005 and the
accel is built on the same funding series the carry leg uses. (A first-pass bug — a spurious
`// 1_000_000` on an already-ms `datetime64[ms].astype(int64)` index — zeroed all funding and gave
all-NaN; the sanity gate now guards it and the corrected run is below.) Same 206-coin PIT top-20
universe, zero survivorship. OOS_CUTOFF=2025-03-24 intact. Taker 0.05%/side + 2× stress.

## Orthogonality — DECISIVELY distinct from carry (the headline question = clean PASS)
| metric | value | read |
|---|---|---|
| corr(accel_z, **CARRY**) IS, signal-level | **−0.114** | NOT the LEVEL re-skinned — genuinely distinct |
| corr(accel_z, trend) IS | −0.001 | orthogonal to trend |
| corr(accel_z, flow) IS | +0.008 | orthogonal to flow |
| corr(accel net, **CARRY net**) IS, P&L-level | **+0.03** | P&L stream does NOT co-move with carry |
| corr(accel net, trend net) / (flow net) IS | +0.02 / +0.04 | P&L orthogonal to the whole book |
| carry-only β(accel net ~ carry net), IS | **+0.03** | ~zero carry loading |

The acceleration is **NOT redundant with carry** — the redundancy hypothesis the brief flagged as the
reject trigger is *itself rejected*. Signal corr −0.11, net corr +0.03, carry-β +0.03: the change of
funding is a genuinely independent quantity from the level on this universe. So the reject is **NOT**
"collinear with carry."

## Standalone — there is NO real edge (this is why it rejects)
| direction | IS | OOS | maxDD | netTot | turnover |
|---|---|---|---|---|---|
| MOMENTUM (+accel, long rising-funding) 1× | **−0.79** | **−1.07** | −96% | −94% | 0.349 |
| MOMENTUM 2× taker | −1.22 | −1.35 | −99% | −98% | 0.349 |
| FADE-CROWD (−accel, short rising-funding) 1× | **−0.07** | +0.47 | −62% | −33% | 0.349 |
| FADE-CROWD 2× taker | −0.49 | +0.14 | −80% | −78% | 0.349 |
| MACD-form 1× (picked dir) | +0.30 | −0.03 | −50% | +20% | 0.352 |

- **MOMENTUM is strongly NEGATIVE** (IS −0.79 / OOS −1.07) — the "ride rising funding" reading is wrong.
- The data picks **FADE-CROWD** by IS, but FADE-CROWD **IS is −0.07 (negative)** → gate [1] FAILS. The
  superficially-positive OOS +0.47 is NOT backed by a positive IS — it is unanchored.
- **Cost-fragile:** FADE OOS collapses +0.47 → +0.14 at 2× taker. Turnover **0.349 is HIGHER than the
  baseline's 0.296** (the daily-Δ signal whips), so cost eats it — opposite of flow's turnover-cheap edge.
- **Window-fragile / sign-unstable:** standalone OOS across the de-noise grid is {win6: −1.12, win9:
  −1.07, win15: +0.84} for momentum — the sign FLIPS across the grid. No stable cell; the headline is
  not a robust factor, it's grid noise.
- **Residual collapses:** raw accel IS/OOS −0.23 / −0.28 → residual (after trend+carry+flow OLS) −0.00 /
  **−0.13**. There is no positive return to be additive *with* — the regression has nothing to span.

## Pre-registered falsifier verdict (n=16 OOS months)
| gate | result |
|---|---|
| [1] standalone net-positive IS AND OOS (picked dir) | **FAIL** (IS −0.07) |
| [2] standalone OOS ≥ +0.30 | PASS (+0.47, but IS-unanchored → meaningless alone) |
| [3] cost-honest: net-positive at 1× AND 2× taker | **FAIL** (FADE 2× +0.14, MOM negative throughout) |
| [4] DISTINCT from CARRY (\|sig corr\| AND \|net corr\| < 0.50) | **PASS** (sig −0.114, net +0.03) |
| [5] residual-additive vs trend+carry+flow (resid OOS > +0.30) | **FAIL** (resid OOS −0.13) |
| [6] robust across the de-noise window (every cell IS+OOS>0, \|corr-carry\|<0.50) | **FAIL** (signs flip) |

## Read — REJECT for NO EDGE, NOT for redundancy (the honest distinction)
The brief asked two separable questions and the data answers them **oppositely**:
1. **Is it distinct from the carry LEVEL? YES, decisively** (corr −0.11 / net +0.03 / β +0.03). The
   2nd-order funding signal is a genuinely orthogonal quantity — funding's *change* is not its *level*
   re-skinned on this universe. Had it carried edge, it would have been a clean orthogonal candidate.
2. **Does it carry a usable standalone edge? NO.** MOMENTUM is −1.07 OOS; FADE has a negative IS, fails
   2× cost, flips sign across the smoothing window, and its residual-vs-book collapses to −0.13. The
   one positive number (FADE OOS +0.47) is an IS-unanchored, cost-fragile, window-unstable artifact —
   exactly the n=16-OOS-month lottery the gates are designed to catch.

So this is a **clean REJECT-for-no-edge**, distinct from a redundancy reject. The honest down-call: the
funding-dynamics *hypothesis* is sound and the signal is orthogonal, but the **directional crowding
edge is not there** — at least not in a sign-stable, cost-survivable, cross-sectional-z form. The most
likely reason (crypto-native): funding's *change* is dominated by short-horizon mean-reversion of the
funding rate itself (a high accel mean-reverts within a candle or two), so a held 8h cross-sectional
tilt on it trades noise at high turnover. The LEVEL persists (carry works, OOS +1.07); the CHANGE does
not persist long enough to harvest at this cadence.

## Verdict: REJECT — funding-acceleration is ORTHOGONAL to carry (and to trend/flow) but carries NO standalone edge (no sign-stable, cost-honest, window-robust factor). NOT a combiner candidate. Baseline UNCHANGED (iter_005 WF-λ trend+carry, IS +1.30 / OOS +1.37 / −23%).

## Axis status
- **Funding-acceleration (DIFF / MACD slope of trailing funding, cross-sectional z) factor: CLOSED at
  this construction.** Orthogonality confirmed (the level-vs-change distinction is real), but no edge:
  momentum strongly negative, fade IS-negative + cost-fragile + window-unstable, residual collapses.
- This is the 2nd funding-derived axis after CARRY: the LEVEL is the edge, the CHANGE is not. Consistent
  with the carry mechanism being a *standing crowding premium* (persistent), not a *crowding-momentum*
  one (transient). The 1st-order funding signal is harvestable at 8h; the 2nd-order is not.

## Next (candidate axes, not yet run)
- **Funding-LEVEL EXTREMES gate (not slope):** rather than the change, a per-coin *magnitude* tilt that
  over-weights carry only when the funding level is in an extreme cross-sectional percentile (the
  crowding is severe), leaving the modest-funding names to trend. Tests whether carry's edge is
  concentrated in the tails — orthogonal to "slope" (this iter), uses the LEVEL carry already proved.
- **Funding × OI / basis structural families** (roadmap, still untouched): open-interest change and
  perp-spot basis are the next non-price, non-flow microstructure columns — the encouragement from
  iter_012 (a fresh column carried orthogonal signal) has NOT been retired, only the funding-*dynamics*
  sub-axis has.
- **A funding-acceleration REGIME gate on gross exposure** (cf. the iter_012 Path Forward): instead of a
  directional per-coin tilt, use market-wide funding acceleration to scale the *book's* leverage
  (de-risk when aggregate funding is spiking = crowding building). Attacks the −23% DD lever, not the
  Sharpe — a different use of the same (orthogonal) signal that a directional standalone could not bank.

## INDEPENDENT CRITIC REVIEW (2026-06-20) — PASS (reject is sound)
Leak test bit-identical (accel slope past-only; only forward op is the correct fund.shift(-1) accrual).
Reject correctly discards a non-edge: fade IS -0.066 (clearly fails gate); OOS +0.47 is cost-fragile
(2x -> +0.14), window-sign-flipping (no cell IS>0 AND OOS>0), year-concentrated (all 2025; 2026 -19