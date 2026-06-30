# EXPLORATION-004 — Within-sector short-term reversal sleeve (iter-004)

**Date:** 2026-06-30
**Status:** COMPLETE — **NEGATIVE** (reversal is the wrong complement; baseline stays iter-003 +0.16). OOS HIDDEN.
**Cadence:** EXPLORATION (IS-only — `--confirm` NOT passed)
**Commit:** `de356098` · builds on iter-003 (sector-relative momentum + band, IS +0.16)

---

## Hypothesis (Critic axis #2)

Momentum (12-1m) and 1-month reversal are the two classic complementary equity anomalies; reversal
classically works in CHOP — the iter-003 book's weakest regime (chop −0.10). A within-sector reversal sleeve
combined with the within-sector momentum should diversify and lift gross + all-weather.

## Change (one)

Add `rev_raw = sector_neutralize( −(close/close.shift(21)−1) / rvol63 )` (negated 1-month return, within
sector, inverse-vol) and combine with the iter-002 momentum sleeve; same δ=0.005 band. Tested equal-weight
and inverse-vol risk-parity combines. `analysis/portfolio/tradfi/iter_004_mom_rev.py`.

## IS numbers (trading-day; IS-only)

| Leg / combo | net Sharpe | gross | bull / bear / chop |
|-------------|-----------|-------|--------------------|
| mom-only (=iter-003, bit-identical) | +0.16 | +0.29 | +0.22 / −0.08 / −0.10 |
| **rev-only** | **−0.79** | **−0.31** | — |
| combo equal-weight | −0.49 | −0.06 | −0.45 / +0.59 / −2.19 |
| combo inv-vol parity (chosen) | **−0.39** | −0.03 | −0.33 / +0.55 / **−2.17** |

mom↔rev sleeve net correlation (IS): **−0.21** (mildly diversifying — but the partner is negative-EV, so
diversification cannot help). Reversal turnover 0.27/day (+344% vs momentum).

## Verdict — NEGATIVE (hypothesis falsified)

The reversal sleeve is **gross-NEGATIVE** standalone (−0.31) — the signal itself loses, not just cost. The
chop-help hypothesis is **falsified**: 1-month within-sector reversal is *anti-predictive* here (chop −2.17,
Δchop −2.07). Consistent with iter-001's finding that this ~62%-Semi/Tech universe is **momentum-persistent
at all horizons** (recent winners keep winning). A reversal complement is the wrong move.

Leak-safe (4 new leak/neutrality tests; suite 27/27 green). OOS hidden (0 `OOS_Sharpe` in default output).
**Baseline unchanged: iter-003 (+0.16).**

## Next

Lesson: the orthogonal complement must be **positive-EV**, and momentum/reversal horizons are all
correlated/momentum-persistent here. iter-005 (QR deep-analysis design): strengthen the gross signal
(multi-horizon / residual momentum) and/or a genuinely orthogonal positive-EV sleeve (low-vol/quality) or a
leak-safe regime gate to fix the bull-only profile. QR to ground the pick in IS probes.
