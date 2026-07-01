# EXPLORATION-016 — Bear-gate the directional TSMOM sleeve (iter-016)

**Date:** 2026-07-01 · **Status:** **KEEP** — strict improvement on iter-015 (net@1× +0.665→+0.728).
ONE change, **ZERO new parameters** (reuse iter-006's bear-state + iter-013's λ). OOS UNTOUCHED (IS-only).
Candidate to REPLACE iter-015 as baseline, pending QR CONFIRMATION + held-out OOS check (not tuned).

## Goal
The worst-months forensic (`worst-months-forensic.md`, PROBE A) named the deployed net-long TSMOM tilt as
the driver of the two worst crash/whipsaw MONTHS (Oct-2018, Jan-2019). Fix: turn the directional tilt OFF
in the bear-state, keep it ON in the bull melt-ups (2013/2017) where it was added to earn.

## The change (`iter_016_bear_gated_tsmom.py`)
REUSE iter-006's causal bear-state `g[t]=1{EW-universe 252d return<0}` (GATE_LOOKBACK=252, sign-0) to gate
the deployed λ=0.25 tilt: **λ_eff = 0.25·(1−g)** → 0.25 in bull/non-bear, 0 in bear. Everything else identical
(band δ=0.010/freq=1, VIX brake, vol-target). No new window, no new threshold — both constants pre-exist.

## Deployed IS metrics (band δ=0.010, freq=1, VIX-ON)
| config | net@1× | net@2× | gross | **net-β** | nlong | turnover | +yrs |
|--|--|--|--|--|--|--|--|
| iter-015 (base) | +0.665 | +0.520 | +0.810 | +0.129 | +0.153 | 0.0700 | 13/16 |
| **iter-016 (bear-gate)** | **+0.728** | **+0.581** | **+0.874** | +0.148 | +0.161 | 0.0698 | 13/16 |
| Δ | **+0.062** | **+0.061** | **+0.064** | **+0.019** | +0.009 | −0.0002 | +0 |

Gate fires 11.2% of IS days, surgically in the 5 bears + recoveries (2022: 86%, 2023: 32%, 2012: 23%,
2016: 14%, 2011: 8%; **2013/2017 melt-ups: 0 days**). Turnover essentially unchanged (it swaps composition).

## The two named months + bad years (iter-015 → iter-016)
| | before | after | Δ |
|--|--|--|--|
| **2019-01** (V-rebound whipsaw) | −10.77% | **−7.57%** | **+3.20pp** |
| **2018-10** (QT crash) | −6.92% | −6.92% | +0.00pp |
| **2019** (year) | −11.1% | **−7.6%** | **+3.4pp** |
| **2018** (year) | −7.3% | −6.9% | +0.4pp |

**Jan-2019 whipsaw substantially fixed** (by then g=1 → TSMOM off → no "short the rippers"). **Oct-2018 is
UNCHANGED** — honest limitation: the 12m-trend bear-state LAGS a fast-from-bull crash (trailing-12m still
positive in Oct-2018 → g=0 → not gated), exactly as the forensic warned. The 2018-year lift comes from Dec.

## Forensic IS-probe cross-check — CONFIRMED in a clean build
Predicted net +0.665→+0.73, 2019 +3.4pp, goodΔμ +0.62. Got: **net +0.665→+0.728, 2019 +3.4pp, goodΔμ
+0.62pp, good-year regressions = 0.** Melt-up 2013/2017 UNTOUCHED (0 gate days → tilt fully ON; 2013's +0.01
Sharpe wiggle is pure vol-target 63-day trailing-vol carryover off the changed Dec-2012 tail, not a 2013 gating).
It also lifts the post-bear recovery years (2016 +6.6→+9.5%, **2022 +5.2→+11.1%**, 2023 +4.4→+5.1%).

## Honest net-β finding (refutes the brief's directional prediction)
The brief predicted net-β would **DROP**. It did **NOT** — it ticked **+0.129→+0.148** (nlong also rose
+0.153→+0.161), still ≤0.15 but near the ceiling. **Mechanism:** by the time the 12m bear-STATE fires,
individual names are mostly down over 12m, so the TSMOM sleeve has flipped **net-SHORT** in bears (standalone
net-long fraction +0.62 bull → **−0.28 bear**; deployed book +0.18 → **−0.08**). What the gate removes is a
**net-SHORT whipsaw** (short the rippers into the Jan-2019 V-rally), not a net-long crash bet. Removing a
negative-beta short mechanically RAISES full-sample OLS beta and nlong. The brief's "net-long in bears"
framing fits the FAST Oct-2018 crash (g=0, NOT gated); the sustained bear-state cut is a short-whipsaw cut.
Net: risk-adjusted return up, worst month shrunk, beta still gate-compliant — but "beta drops" is REFUTED.

## Safety
- **IDENTITY:** g=0-everywhere → `bear_gated_combined_raw(pn, LAM, zeros)` == `combined_raw(pn, LAM)` bit-for-bit
  (raw + deployed net). **PASS.** Anchors iter-016 as a pure one-change delta off iter-015.
- **LEAK:** future-bar corruption of close + ret_fwd after a cutoff leaves the pre-cut deployed VIX-ON net
  bit-identical (g reuses the past-only iter-006 bear-state). **PASS.** In-script + 2 pytest tests added.
- Suite green (87 tradfi tests). OOS never computed. Data untouched. ZERO new params.

## Evaluation gate (strict-improvement to replace iter-015) — **KEEP**
net@1× +0.728 > +0.665 ✓ · net@2× +0.581 ≥ +0.50 ✓ · net-β +0.148 ≤ 0.15 ✓ (near ceiling) · +yrs 13 ≥ 13 ✓ ·
gross +0.874 ≥ +0.78 ✓ · no good-year regression (goodΔμ +0.62pp, 0 flips) ✓ · identity ✓ · leak-safe ✓.

## Verdict / next
Bear-gating the tilt **strictly improves the baseline on the risk-adjusted objective** (net@1× +0.062,
net@2× +0.061, gross +0.064, all 13/16 held) and **shrinks the single worst month** (Jan-2019 +3.2pp) with
zero new parameters. Two caveats for QR: (1) **net-β did NOT drop — it rose +0.019 to +0.148** (still ≤0.15
but with little headroom); the risk win is drawdown/worst-month, not beta. (2) **Oct-2018 is untouched** — a
12m-trend gate cannot catch the fast-from-bull crash; that residual would need the forensic's SECONDARY
realized-vol brake (PROBE C), which could STACK on this. Recommend CONFIRMATION of iter-016 as the new
baseline; if the near-ceiling β is a concern, QR may pair it with the rv-brake to reclaim beta headroom.
