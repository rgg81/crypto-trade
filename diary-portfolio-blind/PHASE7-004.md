# PHASE7-004 — EXPLORATION-004 verdict + calibration confirmation

**Date:** 2026-07-09. **Verdict: NO-MERGE.** Risk-engineer calibration (RISK-004) + Critic (REVIEW-004) both complete.

## Gate result (calibration-confirmed)
R5 (leg-decoupled blend-long 0.7 / mid-vol-short 0.3 + long-leg BTC-drawdown regime scalar) = **+0.336 Sharpe,
−47.8% maxDD**, 2022 +0.32. **PASS:** G-DD (−47.8%≥−50%), G-REGIME (all yrs ≥−1.0), G-FUND (2021 +1394bps≤+1500).
**FAIL:** G-ALPHA-MF (R3 blend-LO +0.36 < R1 vol_low-LO +0.51 — blend DILUTES, doesn't synergize), G-DEPLOY (+0.336 < +0.60),
G-COST (2x −0.057 < +0.5). 32/32 tests green; parity holds (R1/R2/RN).

## Calibration confirms the defaults are near-optimal (RISK-004)
8-combo regime sweep + gross_short sweep + VT diagnostic. **Best-achievable R5 = +0.336** (frozen: 180d/0.20/0.30/0.30, gross_short 0.30).
- Suppressing 2021 "false-positives" (threshold 0.25) HARMS 2022 (turns it −0.34) — the 51% 2021 firing is mostly the
  legitimate May–Jul −55% BTC crash, not chop. 90d lookback catastrophically misses the 2022 bear (2022 −1.64, maxDD −54.5%).
- gross_short: 0.20 has higher Sharpe but fails G-FUND (+1834bps); 0.30 is the highest that passes G-FUND.
- VT is INERT on `longbias_ls` (reads gross_long/gross_short directly, ignores the `gross` lever) — consistent with choosing regime-gate over VT.
- **The +0.34→+0.60 gap is STRUCTURAL (weak alpha), not a calibration deficit.**

## Risk analysis (R5 default)
- maxDD −47.8% is now a **2024 alpha-drought** (peak 2024-05 → trough 2024-12), NOT 2022 (gate tamed 2022; 2022 net leg-sum +0.15).
- Net exposure 79.4% net-long / 20.6% net-short; flips to net-short in the crash minority, releases promptly (not over-flipping).
- Per-name max|w| 0.371 (overlap-driven, >20% flag) — structural (3.27-name effective short band).
- **Fractional Kelly:** ann_vol 31%, full-Kelly leverage 0.59x. Book runs ABOVE Kelly at gross ~1.0. Prudent sizing 0.5–0.8x for Sharpe +0.34.

## THE CRYSTALLIZED CONCLUSION (4 explorations + diagnostics)
The OHLCV-8h-cross-section on the $-volume-ranked top-20 has a **hard ~+0.51 alpha ceiling** (vol_low long-only).
The alpha is real, weak, **long-side-only** (shorts universally toxic — lottery squeezes), and orthogonal factors
don't synergize under equal-weight top-N (averaged-IC + turnover dilution). **No combination of multi-factor blending,
leg-decoupled short hedging, regime gating, or calibration clears +0.60 deployable.** Defensive engineering is VALIDATED
and reusable (maxDD −87%→−48%, regime-robust, 2022 +), but the alpha engine is the binding constraint.

**Critic + risk-engineer converge:** STOP factor-engineering the OHLCV-8h substrate. The one untried lever is the
**SUBSTRATE**: (1) weekly rebalance (rebal 6→21 — cheapest; cuts 73–244x turnover ~3–4x, saves +0.10–0.15 Sharpe/rung;
the fast-turnover cost is the 2nd-largest drag after funding tax), (2) OI-ranked universe (fetch-oi available; less
adverse-selected than $-volume). If both fail → conclude (the OHLCV-8h edge is insufficient for a deployable Sharpe>0.60 book).

**Do NOT deploy R5** (+0.336 < EW-top-20 +0.451 < R1 vol_low-long-only +0.511 < B&H BTC +1.07). It's a research finding,
not a deployable book. Awaiting user direction on the substrate lever vs conclude.
