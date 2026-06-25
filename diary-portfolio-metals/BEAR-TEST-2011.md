# BEAR-TEST-2011 — backward OOS on the 2011–2015 metals bear

**Date:** 2026-06-25. Closes outstanding constraint #1 from `BASELINE_METALS.md` (metals-bear OOS).
**Method:** ingest gold/silver **back to 2010** (Dukascopy; warmup), run the **FROZEN** L2 baseline once
over the never-seen pre-IS window (2011-01 → 2015-03-24). **ONE shot, NO tuning.** Gold/silver only
(pt/pd have no pre-2022 data) = the deep-history core L2 reduces to before 2022. Leak-trivial: data is
entirely BEFORE the IS window; params were never fit on it.

## Results (frozen L2, IS-built params, on the unseen bear)
| Window | book | Sharpe | maxDD | net% | gold B&H |
|---|---|---|---|---|---|
| **FULL unseen 2011-01→2015-03** | L1 anchor | −0.37 | **−46.6%** | −31% | −11% |
| | **L2 baseline** | −0.32 | **−45.6%** | −28% | |
| | dispersion-alone | **+0.25** | −27.8% | +17% | |
| **PURE bear (peak→IS) 2011-09→2015-03** | L1 anchor | −0.75 | −46.3% | −43% | −35% |
| | **L2 baseline** | −0.74 | **−45.1%** | −42% | |
| | dispersion-alone | **+0.53** | −17.7% | +36% | |
| **2013 crash year** | L1 anchor | −1.83 | −31.2% | −29% | −28% |
| | **L2 baseline** | −1.96 | −32.4% | −31% | |
| | dispersion-alone | **+0.55** | −14.2% | +9% | |

Per-year net% (unseen): 2013 is the killer — anchor **−29%** / L2 **−31%** (gold B&H −28%); 2014 anchor
−10% / L2 −6%; 2011/2012/2015 small.

## Verdict — the baseline FAILS the bear (this is the honest, important finding)
1. **The long-biased anchor gets crushed: maxDD ≈ −46%, net −42% in the pure bear, Sharpe −0.75.** This
   is NOT a survivable drawdown for most mandates. The book's #1 vulnerability is CONFIRMED and LARGE.
2. **The CONFIRMATION OOS Sharpe of +1.71 was heavily regime-flattered.** The book's true regime profile
   is now bracketed by both tails: **benign bull → +1.71; severe bear → −46% maxDD.** It is a
   LONG-BIASED metals strategy whose Sharpe is conditional on a friendly metals regime — not a
   regime-robust market-neutral book.
3. **The dispersion overlay is a GENUINE diversifier — but underweighted to protect.** Standalone
   dispersion was **POSITIVE through the entire bear** (+0.25 to +0.53 Sharpe, −18% to −28% maxDD),
   because long-gold/short-silver profited (silver fell ~70% vs gold ~45%). But at α=0.5 in L2 it only
   shaves ~1pp off the anchor's −46% drawdown — the directional anchor dominates the book's bear risk.

## Implication + the fix direction (NOT done here — a future pre-registered exploration)
The dispersion-alone book (+0.25 Sharpe / −28% maxDD over the full unseen bear; +0.53 / −18% in the pure
bear) is FAR more regime-robust than L2. So the obvious regime-robustness move is a **rebalance of the
directional-vs-neutral mix** and/or a **regime brake on the anchor** (cut the long floor toward 0 in a
confirmed, persistent downtrend — to FLAT, never short, since shorting metals loses per iter-001). This
trades bull upside for bear survival. It must be its OWN exploration with its OWN out-of-sample test —
NOT a retune of the params on this 2011-2015 result (that would corrupt the test into in-sample fitting).

## Disposition
- Outstanding constraint #1 (metals-bear OOS) → **RUN; result = FAIL (−46% bear maxDD).** Recorded in
  `BASELINE_METALS.md`. The L2 baseline stands as the IS/bull-OOS-validated book but is now explicitly
  flagged regime-conditional with a quantified bear drawdown.
- Reproduce: `uv run python analysis/portfolio/metals/bear_test_2011.py` (re-ingests `data_bear/`).
