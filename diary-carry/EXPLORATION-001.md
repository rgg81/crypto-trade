# carry-iteration EXPLORATION-001 — per-month WALK-FORWARD parameter selection (kill the bias)

**Axis:** make parameter-finding part of the walk-forward (no global/hindsight param selection).
**Change:** each calendar month, select the carry params (M_FUND, FRAC, min_history) on the PAST
24-month training window only (best past monthly Sharpe), then apply to the test month. Coin
selection was already point-in-time (per-candle funding rank + point-in-time min-history listing-age
filter). So nothing is chosen with future info → the OOS is a TRUE walk-forward out-of-sample.
**Code:** `analysis/carry_walkforward.py` (precomputes 18 combos' realized nets, then per-month picks
the best-on-past combo). Realistic engine, 572-coin universe.

## Result
| config | IS | OOS | fullDD | oosDD | per-year net% |
|---|---|---|---|---|---|
| **walk-forward param-selected (NO bias)** | **+1.15** | **+0.96** | −37% | −33% | 2021 +64, 2022 +51, 2023 +10, 2024 +24, 2025 +2, 2026 +28 — **positive every year** |
| fixed global (2y/M9/F.25) — the biased ref | +0.46 | +1.76 | −34% | −26% | 2022 +55, 2023 −2, 2024 +1, 2025 +20, 2026 +35 |

Most-picked combo per month: **M=9, FRAC=0.25, min_history=1095 (1y)** — chosen ~39 of ~60 months
(stable, not thrashing). The walk-forward converges near my old global guess, but now it's EARNED on
past data each month rather than assumed.

## Read (honest)
- **Removing the param-bias LOWERS the headline OOS (+1.76 → +0.96)** — the fixed +1.76 was partly
  because the params I hand-picked happened to suit the 2025-26 regime (its OOS was concentrated
  there). The walk-forward number is the trustworthy one.
- BUT the walk-forward is **more consistent**: higher IS (+1.15 vs +0.46), positive EVERY year
  (incl. 2023/2024 where the fixed version was flat), smoother per-year profile. Regime robustness ✓.
- The funding edge remains the driver; DD ~−37% (the intrinsic squeeze tail, addressable with the
  dd-brake from #173 as a separate overlay).

## Verdict: EXPLORATION-PROMISING (methodology fix)
Walk-forward param selection is the correct, bias-free methodology and should become the default —
it trades a chunk of (biased) headline Sharpe for honesty + regime consistency. Net OOS ~+0.96 is the
honest unbiased carry. NOT yet a CONFIRMATION (single run); next: fold the dd-brake into the
walk-forward, and a sign-shuffle null on the walk-forward net.

## Next axes
- EXPLORATION-002: dd-brake inside the walk-forward (target the −37% DD on the unbiased book).
- EXPLORATION-003: null + cost-stress on the walk-forward net (gauntlet completion).
