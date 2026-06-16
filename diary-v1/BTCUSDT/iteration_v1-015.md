# Diary — iter-v1/015 (BTCUSDT) — EXPLORATION — R2 drawdown brake on the N=42 base (risk-method axis)

**Axis:** add the R2 drawdown brake (RE-validated, regime-AGNOSTIC) to the iter-013 N=42 base — the
campaign's strongest IS (+0.88). Single-axis vs /013 = ONLY R2. trigger=2.07 / anchor=8.28 / floor=0.20
(RE relative shape on iter-013's 31.85-pt IS max-DD scale). K=5, n_trials=35, slippage 2.

**Result:**
| | IS Sharpe | OOS Sharpe | IS maxDD | OOS maxDD | IS net | OOS net |
|---|---|---|---|---|---|---|
| iter-013 (no R2) | +0.8767 | −1.1814 | 31.85% | 31.80% | +121.5 | −27.96 |
| **iter-015 (+R2)** | **+0.8143** | **−1.1814** | **13.13%** | **6.36%** | +63.9 | **−5.59** |

**Verdict: R2 is a valuable capital-preservation primitive (KEEP it) but cannot make BTC both-positive.**
- **R2 cut OOS drawdown 80%** (31.8%→6.4%) and **OOS net loss 80%** (−27.96→−5.59) — big safety win.
- **But OOS Sharpe is IDENTICAL (−1.1814).** R2 de-levers return AND vol together during drawdowns →
  the risk-adjusted RATIO is preserved. Exactly the RE's pre-registered warning: sizing bounds the
  MAGNITUDE of a loss, never the SIGN of a negative Sharpe.
- IS Sharpe trimmed slightly (+0.88→+0.81; R2 shaved some bull-run size) but IS DD cut 59% — net a
  better IS risk profile.

**vs baseline (iter-001 IS −0.28 / OOS +0.64):** much better IS (+0.81), much better DD (OOS 6.4% vs
13.6%), but OOS Sharpe still negative (−1.18 vs +0.64) → NOT both-positive, does NOT beat baseline on
OOS Sharpe. R2 is a keeper for whatever base eventually wins.

## DIRECTIONAL GRIND — thoroughly exhausted (triply confirmed)
The OOS directional Sharpe is structurally negative and no overlay flips it:
- **iter-011** (diagnosis): IS-bull longs invert to OOS-bull — within-regime overfit, seed-deterministic.
- **iter-012** (de-lever sizing): failed — de-levered up-trends where the OOS losses were.
- **iter-015** (R2 brake): bounds the OOS loss MAGNITUDE 80% but Sharpe sign unchanged (−1.18).
- **iter-014** (FE indicators): NO off-the-shelf indicator is both directional AND sub-period-stable.
- **horizon sweep** (009/010/013): longer horizon BOOSTS IS, never fixes OOS.

You cannot risk-manage or feature-swap your way to a positive ratio from a negative OOS directional
edge (longs WR 22% OOS). The directional levers the user named — indicators (FE) + risk methods (RE) —
are both worked.

## The both-positive path (NOT "impossible" — redirect to where the signal generalizes)
The FE (iter-014) proved the **volatility-MAGNITUDE** signal is sub-period-STABLE (IC vs |move| +0.22,
sign-consistent up to 100% of sub-periods) — unlike DIRECTION, which doesn't generalize. So the
evidence-based both-positive path is a **NON-DIRECTIONAL target**: predict |move| / breakout /
magnitude, where the signal is generalizable, and trade it (long-biased on predicted up-magnitude or
breakout). This is the FE's highest-leverage lever and directly targets a generalizable (→ OOS-positive)
edge — pursued now that the directional grind is exhausted, not as a premature pivot.

**Next:** iter-v1/016 — crypto-QR designs the non-directional target (IS-only Phase 1/2), using the FE's
IS-validated stable vol-magnitude feature core. RETAIN R2 (capital preservation) in the new config.
