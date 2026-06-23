# portfolio-iteration-v2 EXPLORATION-005 — factor-momentum routing trend↔XS-mom (NEGATIVE)

**Type:** EXPLORATION (OOS hidden). ONE change: ROUTE between the trend signal and the XS-mom signal by
factor momentum (hold whichever factor won over a trailing window W), past-only. Code:
`iter_v2_005_route.py`. **Verdict:** **NEGATIVE — whipsaw/lag destroys the complementarity.**

## Results (IS + EARLY/LATE; OOS hidden; default slip)
- anchor: IS +1.53, EARLY +2.17, LATE +1.16. trend-only: IS +1.46, EARLY +2.10, LATE +0.77.
  xs-only: IS +0.43, EARLY +0.19, **LATE +1.36**, turn 0.185, per-yr {2024:1.25, 2025:1.37, 2026:1.09}.
- routing sweep (W∈{63,126,189} × hard/soft): best LATE = W=63 hard → IS +0.66, EARLY +0.83, LATE +0.95;
  "LATE→xs" fraction only 49–57% (it does NOT cleanly detect the regime). 2x taker LATE +0.47.
- **Routed book is WORSE than each ingredient alone** (EARLY +0.83 << trend +2.10; LATE +0.95 < xs +1.36).

## Gate read
- **G_IS (routed IS ≥ +1.53): FAIL** (+0.66). **G2 (ΔLATE ≥ +0.20): FAIL** (LATE +0.95, ΔLATE −0.21).

## Lesson (closes the "combine trend+XS-mom" axis family)
The EARLY/XS-mom-LATE complementarity is a HINDSIGHT artifact of regime non-stationarity, NOT a tradeable
past-only signal. A trailing-performance switch lags the regime turn and whipsaws inside regimes
(routing to xs only ~50% of LATE candles, and mis-routing in 2025/2026). Four vehicles now KILLED on this
axis family: fixed blend (/002), L2 ML (/003), residual-mom (/004), factor-momentum routing (/005).
**Combining trend and XS-mom does not work on this cohort.**

## The pivot the negatives point to
xs-only is NOT weak in the regime we will actually trade: 2024 IS +1.25, LATE +1.36 (> anchor +1.16),
low turnover 0.185. Its only weakness is the DEAD EARLY years (2021/2023 ≈ 0) which a forward-deployed
book never trades. → iter-v2-006: (a) short-term cross-sectional REVERSAL (last literature lead, a
genuinely different signal class), and (b) rigorous characterization of **xs-only standalone as the
recent-regime deploy candidate** (cost-robustness, stability) — the most promising thing found in v2.
