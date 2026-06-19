# portfolio-iteration EXPLORATION-006 — trend-horizon robustness (CONFIRMED robust, no change)

**Axis:** robustness check (not optimization) — is the confirmed trend+carry-tilt edge sensitive to
the {7,14,28,56d} horizon choice? Run the same strategy (λ=0.25, real funding) across fixed horizon
sets. Code: `analysis/portfolio/iter_006_horizons.py`.

## Result
| horizon set | IS | OOS | maxDD |
|---|---|---|---|
| short {3,7,14,28d} | +1.84 | +0.82 | −30% |
| **base {7,14,28,56d}** | +1.67 | +1.31 | −27% |
| long {14,28,56,112d} | +0.96 | +1.00 | −39% |
| wide {7,14,28,56,112d} | +1.40 | +1.15 | −29% |

## Read — ROBUST
ALL configs are positive in BOTH IS and OOS (IS +0.96..+1.84, OOS +0.82..+1.31). The edge does not
depend on the exact horizon choice — no fragility, no overfit-to-horizons red flag. Short horizons
have higher IS / lower OOS (faster signals fit recent IS more); long are weaker IS. Base is a sound,
balanced middle — kept (NOT claimed "best", which OOS would be selection bias).

## Verdict: ROBUSTNESS CONFIRMED — no baseline change. Strengthens confidence the edge is real.
## Next
- iter-007: attack the −27/−29% DD (the main weakness) — regime/vol gross-exposure scaling or per-coin
  weight caps, kept only if DD drops without breaking the OOS Sharpe. Then a short-term reversal overlay.
