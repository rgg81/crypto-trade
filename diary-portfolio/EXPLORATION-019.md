# portfolio-iteration EXPLORATION-019 — market-regime gross-exposure overlay (REJECT)

**Agent-driven.** Goal: cut the baseline's −23% maxDD WITHOUT hurting OOS Sharpe, using a MARKET-LEVEL
gross-exposure scalar (the DD is correlated portfolio-wide reversals, not single-name concentration —
iter-009 proved per-coin caps don't move it; iter-007 proved P&L-state brakes are counterproductive on
this mean-reverting book). Every signal here is VOL-STATE / regime, applied to the CANONICAL net.
Code: `analysis/portfolio/iter_019_regime.py`.

## Method — overlay on the CANONICAL net (no stitch-order artifact)
- The overlay scales `iter_005.walkforward(iter_005.lam_nets(coins))[0]` — the deployable per-λ-vol-
  target-then-stitch +1.37 series. `m[t]∈[floor,1]`, all inputs shift(1) + `m` shifted once more
  before it multiplies the net. **Overlay-off (m≡1) reproduces +1.37 EXACTLY (asserted at runtime).**
  This is precisely the trap iter-007 fell into (it scaled a raw-stitch + single-outer-vol-target net);
  measuring on the canonical net removes it.
- Accounting: the canonical net is linear in gross (P&L, funding, cost all linear in `w`), so a market
  scalar `m` scales the WHOLE next-candle net incl. its proportional turnover cost → `m * net`.
- 4 regime families, each robustness-swept over windows/threshold/floor (effect must hold ACROSS the
  sweep): (A) VOL-RATIO (aggregate market realized-vol spike), (B) DISPERSION (cross-sectional return
  std), (C) BREADTH (|mean sign of coin returns| — one-way tape), (D) |aggregate FUNDING|.

## Result vs canonical baseline (IS +1.30 / OOS +1.37 / maxDD −23.4% / oosDD −21.8%)
| family | Pareto cells | DD relief range | OOS Δ range | read |
|---|---|---|---|---|
| VOL-RATIO  | 0/9 | [−0.0, +1.6]pt | [−0.02, +0.10] | no DD relief — iter-007 idea dead on canonical net |
| DISPERSION | 0/9 | [−1.0, +0.4]pt | [−0.02, +0.39] | ~0pt DD; OOS-up cells just de-lever ~constantly |
| BREADTH    | 4/9 | [+0.5, +4.5]pt | [+0.06, +0.10] | APPARENT Pareto — but it's a disguised constant de-lever (below) |
| \|FUNDING\| | 0/4 | [−0.7, +1.0]pt | [−0.17, −0.03] | OOS WORSE — a DD-for-Sharpe trade |

## The decisive control — BREADTH is a disguised lower vol target, NOT regime timing
BREADTH's "Pareto" cells fire ~always (89–100%) at a near-constant ~0.82× multiplier — a red flag.
Two controls on its strongest cell (`w21/th0.4/fl0.5`, mean mult 0.816, fires 100%):

| net | IS | OOS | maxDD | oosDD |
|---|---|---|---|---|
| baseline | +1.301 | +1.371 | −23.4% | −21.8% |
| overlay | +1.368 | +1.426 | −18.9% | −17.1% |
| **CONSTANT 0.816×** (dumb flat de-lever) | +1.301 | +1.371 | **−19.4%** | **−18.0%** |
| overlay, re-vol-targeted to baseline vol | +1.368 | +1.426 | −22.6% | −20.5% |
| CONSTANT, re-vol-targeted | +1.301 | +1.371 | −23.4% | −21.8% |

- A **dumb constant 0.816× scalar** (zero regime information, scale-invariant ⇒ identical Sharpe) gets
  DD to **−19.4%** on its own. The overlay's −18.9% is barely better → the DD relief is the mechanical
  effect of trading a smaller book, **not** timing. You'd get it for free by lowering the vol target.
- **Re-vol-targeted to baseline vol** (strip the "smaller book" effect, leaving only timing): the
  constant collapses EXACTLY to baseline (0 edge, as it must); the breadth overlay's residual real edge
  is +0.05 OOS / ~1pt DD — within noise.
- `corr(mult, |net|) = +0.03` — essentially zero, even slightly wrong-signed. The overlay does **not**
  de-lever into the dangerous candles. No timing.

## Verdict: REJECT. Baseline UNCHANGED (IS +1.30 / OOS +1.37 / DD −23%).
No market-level gross-exposure regime overlay cleanly cuts the −23% DD without costing OOS:
- VOL-RATIO (the iter-007 idea, now canonical): no DD relief — confirms the earlier "+0.16 OOS" was the
  stitch-order artifact, dead under canonical accounting.
- DISPERSION / |FUNDING|: no DD relief, or DD-for-Sharpe.
- BREADTH: the only apparent Pareto is a near-constant de-lever in disguise (knife-edge in the floor/
  threshold making it fire ~always) — genuine timing is within noise. Not a regime signal.

The −23% DD is correlated portfolio-wide reversals that none of these market-state signals ANTICIPATE.
A scalar that fires ~always = a lower vol target, which is a separate (sizing) decision, not a regime
edge. NOT promote-worthy.

## Next
The lever for this DD is not a univariate market-state scalar. Candidates worth a future EXPLORATION:
(1) a CORRELATION/cross-sectional-rank overlay that de-levers only when the book's effective breadth
collapses AND positions are crowded one-way (must beat the constant-de-lever control + show negative
corr(mult,|net|)); (2) accept the DD as the price of the +1.37 OOS and pivot back to signal/alpha axes.

## INDEPENDENT CRITIC REVIEW (2026-06-20) — PASS (reject sound, DD intrinsic)
Leak CLEAN (overlay-off bit-exact +1.37; corruption test past bit-identical; lag=2 conservative; pure
scalar on canonical net, NO stitch trap). Control VALID: constant 0.816× reproduces 89% of breadth's
DD relief w/ zero regime info (Sharpe scale-invariant), corr(mult,|net|)=+0.03 (doesn't de-lever into
danger), re-vol-targeted residual within noise (phase-randomization null p=0.244). The -23% DD is
INTRINSIC correlated portfolio-wide reversals — no market-state signal anticipates it. Honest reject,
baseline +1.37 untouched.
CONSTRUCTIVE: portfolio exploration LARGELY CONCLUDED (7 directional rejects + flow-only + combiner HELD
@ DSR-N=14 + DD overlay rejected). Ship +1.37 baseline to testnet + shadow combiner (task #184). ONE
genuinely un-mined lever = TURNOVER/holding-period: every iter modulated gross-exposure or factor-weight,
none touched REBALANCING CADENCE. A hysteresis-banded slower-turnover version of the same trend+carry
book (rebalance only on meaningful signal change) attacks the DD AT ITS SOURCE (whipsaw into reversals)
+ is deployment-relevant (lower cost/slippage). The honest one-more iteration (iter-020); else ship+shadow.
