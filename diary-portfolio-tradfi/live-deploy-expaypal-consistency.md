# Live-deploy consistency — iter-016 backtest WITHOUT trading PAYP

**Date:** 2026-07-01 · **Status:** DONE — baseline ROBUST to the PAYP exclusion; live 68-name universe justified. IS-only, OOS hidden.
**Script:** `analysis/portfolio/tradfi/iter_016_expaypal_check.py` (harness self-check: no-drop path == confirmed +0.729/+0.875 baseline bit-for-bit).

## Why
The live paper desk excludes `PAYPUSDT` (a broken Binance perp: perp ~$14 vs PayPal/PYPL ~$43, corr 0.19
— a perp-VENUE decoupling from Phase-2b). The confirmed iter-016 backtest ran on all 69 SECTOR_MAP names
(PAYP's Yahoo data is CORRECT PayPal via the `PAYPUSDT->PYPL` ingest override — baseline uncontaminated).
For deploy honesty the backtest justification must match the traded universe (68).

## Two ways to "drop PAYP" (they answer different questions)
- **(B) DEPLOY-FAITHFUL** — exactly what the engine does: compute the whole 69-name book (PAYP stays in
  the cross-sectional ranking / EW-market proxy / bear-gate — valid PayPal data), then ZERO PAYP's final
  leg (no renormalize, same 69-name vol-target `scale`). Isolates the pure "don't trade PayPal" P&L.
- **(A) UNIVERSE-RECOMPUTE** — remove PAYP from the universe entirely (ranking/market/gate recompute on
  68). A stronger composition-sensitivity stress, NOT what the desk does.

## Result (IS-only, 2010→OOS_CUTOFF)
| config | net@1x | net@2x | gross | net-β | +yrs | maxDD |
|---|---|---|---|---|---|---|
| 69-name (confirmed base) | +0.729 | +0.582 | +0.875 | +0.148 | 13/16 | −24.7% |
| **(B) drop PAYP leg [LIVE]** | **+0.702** | +0.556 | +0.847 | +0.156 | **13/16** | −26.4% |
| (A) recompute on 68 | +0.667 | +0.518 | +0.815 | +0.148 | 13/16 | −27.6% |

- **(B) Δnet@1x = −0.027** → +0.702, still ≫ the ≥0.50 bar, 13/16 years, β controlled. **BENIGN.**
- (A) Δnet@1x = −0.062 → +0.667 (composition reshuffle, not PAYP's P&L) — also clears 0.50.
- Only year that moves materially: **2022** (+11.1% → +8.5%): PayPal crashed ~62% in 2022, the book was
  profitably SHORT it, so not trading it gives back some 2022 return. All other years within noise.
- Worst year (2010 −9.1%) + worst month (2024-05 −10.4%) unchanged under (B).

## Verdict
The confirmed iter-016 baseline is **robust** to excluding the broken PAYP perp; the live desk trading 68
names is **justified** at net@1x **+0.702** IS. No change to the deploy. (If Binance ever relists a PAYP
perp that tracks PayPal, re-check the basis and it can rejoin — the backtest keeps PayPal, only the leg is
dropped live.)
