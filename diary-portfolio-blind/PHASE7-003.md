# PHASE7-003 — EXPLORATION-003 verdict + partition diagnostic (H1 vs H2 resolved)

**Date:** 2026-07-09. **Verdict: NO-MERGE.**

## EXPLORATION-003 gate result
G-ALPHA (blended ≥ +0.29) **FAIL**: blended −0.36 vs vol_low-only +0.09 (Δ −0.45, ~6–9σ).
rev_3 did NOT add alpha; the blend inherited rev_3's drag. Critic CONDITIONAL-PASS (REVIEW-003):
numbers real (no sign bug, no leak, 23/23 meaningful tests, parity +0.088≈+0.09).

## The diagnostic that changed the conclusion (REVIEW-003 F2 — resolved)
The Critic flagged the EXPLORATION-003 null was AMBIGUOUS between H1 (partition mismatch — midvol_short's
skip-tail skips the winners rev_3 wants to short) and H2 ("OHLCV too weak"). Ran the partition-sensitivity
probe (`blind_diag_partition.py`, IS-only, funding ON):

| signal | midvol_short (skip-tail) | rank_neutral (no-skip L/S) | longonly_tophalf |
|---|--:|--:|--:|
| vol_low | +0.09 (−48% DD) | −0.14 (−79%; 2021 −1.83) | **+0.51** (−87%) |
| rev_3 | −0.65 (−72%) | **−0.66** (−87%; 2021 −1.27) | **+0.26** (−92%) |

**Resolution — neither pure H1 nor H2:**
- **rev_3 L/S is negative regardless of partition** (rank_neutral −0.66 ≈ midvol −0.65). Removing the
  skip-tail did NOT rescue it → the SHORT side of reversal (shorting recent winners) blows up in mania
  (2021 −1.27) regardless of construction. Same lottery-squeeze toxicity as vol_low shorts. H1 only
  half-right.
- **rev_3 long-only = +0.26** (POSITIVE) → the LONG-side bounce alpha IS real & harvestable net-of-cost.
  Same shape as vol_low (long-only +0.51 works; L/S blows up). H2 ("OHLCV too weak") is **WRONG** — the
  alpha is there, it's just long-side-only.

## Refined synthesis (corrects the premature "OHLCV too weak")
1. **vol_low & rev_3 both have real but WEAK long-side alpha** (long-only +0.51 / +0.26), orthogonal
   (corr −0.036). The rank-IC (+0.052/+0.045) overstates tradeability because it conflates a harvestable
   LONG half with a toxic SHORT half (median-based IC hides the short-side fat tails).
2. **The short side is universally toxic at 8h** — shorting winners (rev_3) or high-vol (vol_low) blows
  up in mania (lottery squeezes) regardless of partition/tail-cap. EXPLORATION-002's mid-vol tail-cap
  *avoided* the blowup but the resulting near-neutral book had ~0 return (the short adds no alpha, just
  risk/funding dodge).
3. **Long-only pays the structural price:** ~12%/yr funding tax (net-long) + eats crashes (−87/−92% maxDD).
4. **Sobering benchmark:** NONE of the constructions beat B&H BTC (+1.07) or clear Sharpe 1.0. Best is
  vol_low long-only +0.51 — half of B&H BTC. The IS window (2020–25) was an exceptional bull; B&H BTC is
  a very high bar.

**Net:** the edge is real-but-weak and long-side-only; the barriers (funding tax on longs, toxic shorts,
crashes) are structural and severe. The brief excluded funding/carry/beta-hedging, so non-OHLCV short-alpha
sources are largely out of scope or unavailable (on-chain/liquidations absent; taker_imb IC ~0).
**This is a genuine strategic decision point** (pursue long-biased multi-factor + risk engineering /
rescope substrate / conclude), surfaced to the user.
