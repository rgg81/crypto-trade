# carry-iteration EXPLORATION-006 — CASH-AND-CARRY (spot-perp basis): the first capacity-survivable edge

**Axis:** the funding income's CLEAN capturable form. When funding > 0, hold LONG SPOT + SHORT PERP
(same notional): the short-perp earns funding, the spot leg hedges the perp price 1:1 — no squeeze,
no beta, capacity = spot liquidity. Code: `analysis/cash_carry.py` (realistic engine, 2-leg cost,
basis-artifact guard, spot-liquidity floor). Universe so far: 80 coins with spot+perp+funding
(targeted fetch in progress toward 338; result is STABLE across 49→80 coins).

## Result (diversified M=9, thresh=0, ~42 coins, turnover 0.08)
| cost | net IS | net OOS | DD |
|---|---|---|---|
| TAKER 0.07%/side | +1.13 | **−3.85** | −21% |
| **MAKER ~0.01%/side** | **+2.47** | **+2.05** | **−3%** |
| ZERO | +2.72 | +5.27 | −3% |

**Spot-liquidity floor (MAKER cost):** no floor OOS +2.05 → **$5M +0.42** → **$20M +0.35**, DD −1..−8%.
funding-leg OOS Sharpe ~+6.9 (income real); basis-leg OOS ~+1.9 (spot hedges perp cleanly).

## Read (honest)
- **The pivot worked.** The spot leg is the clean 1:1 hedge the perp-perp carry never had, so the DD
  collapses from −37%/−90% to **−3%** and the real funding income becomes capturable.
- **It is the FIRST result that survives capacity.** Under a tradeable spot floor the perp-perp carry
  INVERTED negative; cash-and-carry stays POSITIVE (~+0.4 OOS at $5M/$20M) with a tiny DD.
- **Two binding caveats:** (1) MAKER-cost-dependent — at taker (0.07%/side × 2 legs) it's dead
  (OOS −3.85); basis trades execute via resting limit orders so maker is realistic, but it REQUIRES
  maker execution infra, not market orders. (2) The realistic capacity-respecting number is MODEST
  (~+0.35–0.42 OOS) — below the Sharpe>1 floors the other tracks use. The +2.05 no-floor headline
  leans on smaller-spot coins.

## Verdict: EXPLORATION-PROMISING (first capacity-survivable positive) — pending full universe
Robust across 49→80 coins. Honest deployable shape: a LOW-Sharpe (~+0.4 OOS), LOW-DD (~−5%),
market-neutral funding-income strategy that REQUIRES maker fills. Not a high-Sharpe alpha — a clean
income harvest. Next: (1) finish the spot fetch to the full ~338-coin universe for the definitive
capacity-respecting number; (2) walk-forward the funding-window/threshold params (no global pick);
(3) maker-fill realizability (limit-order fill assumptions, basis-convergence on exit). Whether ~+0.4
OOS market-neutral income is worth deploying is a USER decision (it clears no Sharpe>1 floor, but it's
real, clean, and capacity-survivable — the only thing this session found that is).
