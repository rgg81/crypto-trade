# carry-iteration EXPLORATION-004 — per-leg capacity + ALPHA-vs-BETA decomposition (the decisive test)

**Axis:** the QR pivot ("the long leg is the +309% hero, go capacity-friendly there") + the critic's
realizability BLOCK. Split the carry into LONG (w>0) and SHORT (w<0) legs, evaluate each across
liquidity floors, and benchmark each leg against just longing/shorting the WHOLE eligible universe
(pure alt-beta). Code: `analysis/carry_long_leg.py`. Realistic engine, IS-emphasis (OOS shown).

## Result (net Sharpe; legs are directional → big DD)
| | no floor | $5M floor |
|---|---|---|
| LONG leg (long lowest-funding) | IS +0.72 / OOS **−1.44** | OOS **−2.53** |
| SHORT leg (short highest-funding) | IS −0.08 / OOS **+1.79** | OOS **+1.48** |
| COMBINED market-neutral | IS +1.38 / OOS +1.04 | OOS **−1.03** |

**ALPHA-vs-BETA ($5M floor, OOS):**
| | OOS Sharpe |
|---|---|
| long-low-funding | −2.53 |
| long-ALL equal-weight (+beta) | −2.60 |
| short-high-funding | +1.48 |
| short-ALL equal-weight (−beta) | **+1.70** |

## The decisive finding (corrects the QR IS-story; the deepest carry result)
1. **The QR's "long leg is the hero" was IS-only — OOS it's the LOSER** (+0.72 IS → −1.44/−2.53 OOS).
   The +309% was the 2020-22 alt-bull; in the 2025-26 OOS, longing crowded-shorts crashes.
2. **NEITHER leg's funding SELECTION adds OOS alpha over plain alt-beta:** long-low-funding ≈
   long-ALL (−2.53 vs −2.60); short-high-funding is actually WORSE than short-ALL (+1.48 vs +1.70).
   → the carry's OOS returns are ALT-BETA (long-alts lose / short-alts win in the bear OOS), not
   cross-sectional funding alpha. The funding selection contributes ~nothing OOS net of beta.
3. **The combined market-neutral dies under a floor** because the two legs' betas don't cancel and
   the long leg drags (confirming the critic), AND there is no selection-alpha to fall back on.

## Verdict: EXPLORATION-NEGATIVE — the carry is NOT a clean scalable cross-sectional alpha
The funding INCOME is real + regime-stable (OOS Sharpe ~+6.6), but harvesting it requires
beta-confounded, capacity-killed, squeeze-prone price exposure, and the funding SELECTION shows no
demonstrable OOS alpha over alt-beta. Under the FULL gauntlet (realistic engine + walk-forward +
capacity + per-leg + alpha-vs-beta) the broad funding carry does NOT survive as a deployable
market-neutral alpha. The earlier +0.96/+2.61 headlines were (a) survivorship, (b) un-hedged alt-beta,
(c) illiquid-coin premium. The methodology stayed clean throughout — the EDGE is what failed.

CAVEAT: this is ONE OOS regime (2025-26 alt-bear). Alpha-vs-beta can't be fully disentangled in a
single regime. But the burden of proof (clean OOS alpha net of beta + capacity) is NOT met.

## Next (honest)
The carry-as-clean-alpha axis is largely EXHAUSTED. The only intellectually honest continuations:
(1) a properly BETA-NEUTRAL funding-income harvest (regress out alt-beta per coin, not just
dollar-neutral) — but the risk-engineer already found a BTC/ETH beta-hedge KILLS the net; a full
per-coin beta-neutralization is the last untried form; (2) accept funding income is real but not
cleanly capturable cross-sectionally → shelve the carry as a scalable alpha. Deploy (#168): NO.
