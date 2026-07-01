# Sizing feasibility — trading the iter-016 book at a $10k budget (Binance perp minimums)

**Date:** 2026-07-01 · **Status:** DONE — **$10k is VIABLE** (~1% implementation shortfall, no universe change).
**Script:** `analysis/portfolio/tradfi/sizing_min_notional.py` (fetches LIVE exchangeInfo filters, quantizes the
actual deployed book). **Real budget is $10k, not the $100k the paper desk launched at.**

## Official Binance filters (live exchangeInfo, all 69 TradFi perps — uniform)
- **MIN_NOTIONAL = 5 USDT** — a leg's price×qty must be ≥ $5.
- **LOT_SIZE step = 0.01 units, minQty = 0.01** — qty trades in 0.01-unit lots (qtyPrecision 2).
- ⇒ a leg is untradeable if `|w|·equity < max(5, 0.01·price)`; every tradeable leg is quantized to
  `0.01·price` of notional — a granularity **10× coarser at $10k than $100k**, worst on the highest-priced
  perps (this 2026 memory supercycle: SNDK $2,250 → $22.50/lot, ASML $1,990 → $19.90, LLY $1,201, MU $1,157).
  Perp price LEVELS verified vs Yahoo (ratios 0.98–1.10 = the funding/long-premium basis, no decoupling).

## Impact — deployed book (68 legs ex-PAYP, gross 0.706), quantized to the filters
| equity | tradeable | dropped | grossR | netR (tgt +0.070) | weight-TE |
|--------|-----------|---------|--------|-------------------|-----------|
| **$10k** | **66/68** | 2 | 0.705 | +0.068 | **0.007 (~1% of gross)** |
| $25k | 67/68 | 1 | 0.705 | +0.070 | 0.002 |
| $100k | 67/68 | 1 | 0.705 | +0.070 | 0.001 |

- **At $10k only 2 legs drop** (CRCL ≈$0 weight, V $4 < $5 min-notional) = **0.06% of gross** — economically nil.
- gross + dollar-neutrality essentially preserved; realized book tracks target to ~1% (weight space).
- **Binding constraint at $10k is the 0.01-LOT STEP on the priciest perps, NOT the $5 min-notional.** A tiny
  sub-10bps leg on ASML ($19.90/lot) needs ~$18k to place cleanly; the $5 floor only bites below ~5bps.
- Min equity for a fully-clean book: **~$18k** for every leg ≥5bps; **~$3.8k** for the material (≥20bps, 54-leg) core.

## Verdict + action
**$10k trades the book faithfully** (~1% implementation shortfall, no name/universe change needed). The paper
desk was launched at $100k (cosmetic — returns are equity-invariant on continuous fills); reconfigured to the
real **$10k** budget. To make the $10k paper track *faithful* (not just rescaled), the engine now QUANTIZES the
live-track fills to the official lot/min-notional filters, so the desk reports the real ~1% shortfall a $10k
account experiences. Watch for de-lever regimes: if vol-targeting cuts gross well below 0.7, more small legs
drop — re-run this script at that gross to re-confirm.
