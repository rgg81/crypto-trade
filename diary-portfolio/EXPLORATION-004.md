# portfolio-iteration EXPLORATION-004 — funding P&L + carry tilt (PROMISING, pending walk-forward λ)

**Axis:** add real funding P&L to the held legs (the baseline ignored it) + a carry tilt that blends
the trend signal with a carry signal (−trailing funding: short high-funding / long low-funding) at
weight λ. Code: `analysis/portfolio/iter_004_funding.py`. Realistic cost, vol-targeted, leak-safe.

## Result
| variant | IS | OOS | maxDD | net total |
|---|---|---|---|---|
| A trend, no funding (baseline) | +1.68 | +0.50 | −28% | +1271% |
| B trend + real funding P&L | +1.65 | +0.49 | −29% | +1124% |
| **C trend + carry tilt λ=0.25** | **+1.67** | **+1.31** | **−27%** | +1259% |
| D trend + carry tilt λ=0.50 | +0.50 | +1.35 | −51% | +177% |

C per-year net%: 2020 +70, 2021 +47, 2022 +46, 2023 +61, 2024 +38, **2025 +21, 2026 +22**.

## Read
- **Real funding P&L alone (B) is ~neutral** (tiny drag — trend longs pay funding in bull years).
- **A modest carry tilt (λ=0.25) lifts OOS +0.50 → +1.31**, keeps IS (+1.67), trims DD (−27%), and the
  OOS years jump (2025 +13→+21, 2026 +8→+22). Trend + a carry lean generalizes much better than trend
  alone. λ=0.50 is too much (carry overwhelms trend → IS collapses, DD −51%).

## HONESTY FLAG — not yet confirmed
On IS, λ=0 and λ=0.25 are TIED (+1.68 vs +1.67) — I can only see 0.25 is better by looking at OOS,
which is the selection-bias trap. The OOS lift is promising AND there's a sound prior (carry is a
documented factor, additive to trend), but **λ must be WALK-FORWARD-selected (no OOS peek) before this
is a confirmed improvement.**

## Verdict: EXPLORATION-PROMISING (pending walk-forward λ)
## Next
- iter-005: walk-forward-select λ per period on PAST data only; if the OOS lift survives honest
  λ-selection, promote trend+carry-tilt to baseline. If it was OOS-selection-bias, reject.
