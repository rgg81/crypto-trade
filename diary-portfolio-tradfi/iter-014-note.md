# iter-014 — MULTI-HORIZON TSMOM {3m,6m,12m} — NEGATIVE (does NOT fix 2019/2018; regresses vs iter-013)

**ONE change vs iter-013:** replace the single-12m TSMOM directional sleeve with an EQUAL-WEIGHT
blend of three trend speeds `{3m,6m,12m}` (each `sign(close/close.shift(h)-1)/rvol`, gross-normed
first, then averaged; `h in {63,126,252}` = iter-005's `HORIZONS_MH` copied verbatim). Everything
else frozen: `lam=0.25` combine with `[MOM + 0.5*LTR]`, iter-003 band (`delta=0.005`), iter-008 VIX
brake, OOS-hidden accounting. Script: `analysis/portfolio/tradfi/iter_014_mh_trend.py`.

**Pre-registration / anti-overfit:** horizons NOT hand-picked to flip 2019, `lam` NOT re-tuned, no
2019-specific rule. IDENTITY confirmed: one-speed blend `(252,)` == iter-013 single-12m sleeve, and
combined `@lam=0.25` == iter-013 combined book, both `allclose(1e-12)` (PASS). Leak self-check PASS.
OOS never computed (no `--confirm`).

## Result (IS-only 2010-2025)

| metric | iter-013 (single-12m) | iter-014 (MH) |
|---|---|---|
| combined net @lam=0.25 | **+0.63** | **+0.51** |
| positive years | **13/16** | **12/16** |
| net-beta | +0.12 | +0.07 |
| maxDD | -32% | -39% |
| standalone sleeve net | +0.88 | +0.66 |
| standalone sleeve 2019 | +0.13 | **-0.14** |
| standalone sleeve 2018 | +0.05 | **-0.32** |

**Did NOT fix 2019 (−0.71 → −1.04) or 2018 (−0.62 → −0.78); both got WORSE.** Combined year count
DROPPED 13/16 → 12/16 because 2025 flipped negative (+0.26 → −0.60). Still-negative years:
`[2010, 2018, 2019, 2025]`. USER BAR (≥+0.50 AND 16/16) NOT met.

## Why the theory was falsified on this universe (mechanistic)

The thesis was "faster horizons re-enter LONG sooner after the 2018-12-24 V-bottom → catch the 2019
melt-up." Per-horizon diagnostic (standalone, same band): 3m 2019=+0.14 (net-long H1-2019 +0.41),
**6m 2019=−0.78** (net-long +0.28), 12m 2019=+0.13 (net-long +0.26). The 3m sleeve *did* re-enter
long fastest but earned no more than 12m; the **6m sleeve is the killer** — its lookback window sits
squarely across the 2018-Q4 crash and the sharp V-recovery, so it is whipsawed wrong-footed on both
legs (the canonical fast-momentum V-recovery crash). Blending it in drags the composite 2019 to
−0.14, WORSE than either 3m or 12m alone. Whole-IS, the fast speeds are simply weaker here
(standalone 3m +0.63 / 6m +0.56 vs 12m **+0.88**), so equal-weighting three sleeves — two materially
weaker and more whipsaw-prone — dilutes the 12m's clean bull-tape beta (bull +0.87→+0.72,
chop +0.18→+0.08) and lowers both net and year-count. Unlike the cross-sectional book at iter-005
(where the 3-1m sleeve was AS strong as 12-1m and decorrelated), the tradfi TSMOM speeds are NOT
co-equal, so multi-horizon does not generalize.

## Honest read + handoff

REJECT — keep iter-013 (single-12m TSMOM, +0.63 / 13/16) as best. The three remaining misses are
structural, not a trend-speed problem: **2010** = LTR 3y warm-up (thin pre-2013), **2018** = net-long
bear (the cost of the directional tilt; VIX brake only partly tames it), **2019** = a low-dispersion
melt-up the neutral book structurally misses that no trend-speed reshuffle rescued. 2018 and 2019
look structurally hard to fix from the trend sleeve alone; the honest 13/16 at +0.63 stands. Next
levers should be OUTSIDE the trend sleeve (e.g. the neutral engine's melt-up behaviour or a
warm-up-robust LTR), NOT further TSMOM-horizon tuning (axis exhausted here).
