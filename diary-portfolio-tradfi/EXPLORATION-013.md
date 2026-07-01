# EXPLORATION-013 — Controlled directional TSMOM sleeve (iter-013)

**Date:** 2026-07-01 · **Status:** KEPT — **clears the ≥0.5 Sharpe bar** (net +0.63); 13/16 years (not 16/16). OOS HIDDEN.
**Commit:** `db8e17b` · risk note `iter-013-risk.md` · builds on iter-011 (mom+LTR, +0.33)

## Change — bounded time-series-momentum (TSMOM) directional sleeve (user-approved: relax pure neutrality)
`book = (1−λ)·[mom + 0.5·LTR] + λ·TSMOM`, TSMOM = sign(own trailing-12m)/rvol gross-normed (net-long in
uptrends → earns the beta the neutral book can't in low-dispersion melt-ups). Band + vol-target + VIX brake.
TSMOM standalone: Sharpe +0.88, net-long +0.51, β +0.32.

## IS (2010-2025, IS-only) per λ
| λ | net | +years | net-β | maxDD |
|---|-----|--------|-------|-------|
| 0.15 | +0.51 | 11/16 | +0.07 | −37% |
| **0.25 (chosen, +VIX)** | **+0.63** | **13/16** | **+0.12** | −32% |
| 0.35 | +0.72 | 13/16 | +0.17 | −28% |

**Chosen λ=0.25** — smallest λ that fixes the melt-ups; net-beta **+0.12 (85% still neutral)**, a genuinely
controlled tilt. λ=0.35 buys net only via bear drag (max-net-fit) → rejected.

## Years
FIXED: 2013 (+0.46→+1.40), 2017 (−1.11→+0.28), bonus 2020 flips +. **Still negative (3):** 2010 (LTR/TSMOM
warm-up, thin pre-2013), 2018 (Q4 bear, net-long cost — VIX helps), 2019 (TSMOM whipsaw off the 2018 V-bottom).
VIX manages the added beta (bear −0.31→−0.20, maxDD −4pts, net −0.02). Leak PASS, 63 green, OOS hidden.

## Verdict
**Sharpe bar MET (+0.63 ≥ 0.5); perfect-year bar MISSED (13/16).** Real accretive directional step at a
controlled +0.12 beta. 16/16 needs a separate iteration (multi-horizon trend for the 2019 whipsaw), NOT a λ
tweak — no overfitting. Book is now 4-component: XS-momentum + LT-reversal + TS-momentum + VIX brake.

## Next
iter-014 = MULTI-HORIZON TSMOM (blend 3/6/12m trend, faster V-bottom re-entry) to address the 2019 whipsaw
(and possibly 2018) toward 16/16 — theory-grounded (same fix that helped the XS book at iter-005), not
year-specific. Then: honest verdict on the achievable ceiling + the CONFIRMATION/OOS-reveal decision.
