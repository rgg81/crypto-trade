# portfolio-iteration EXPLORATION-002 — top-20 L/S portfolio (diversified trend wins; xsec rejected)

**Axis:** extend the iter-001 BTC trend anchor to a long/short portfolio on a POINT-IN-TIME top-20
(ranked each candle by trailing $-volume, ex-stablecoins; 206 candidate coins ≥2y history). Test two
factors. Code: `analysis/portfolio/iter_002_top20.py`. Realistic cost, vol-targeted, leak-safe.

## Result
| mode | IS | OOS | maxDD | net total | verdict |
|---|---|---|---|---|---|
| **TS-TREND (diversified)** | **+1.68** | **+0.50** | **−28%** | **+1271%** | **KEEP — new baseline** |
| XSEC-MOM (rank L/S) | +0.88 | −1.81 | −64% | +76% | REJECT (fails OOS) |
| COMBO (avg) | +1.58 | −1.08 | −39% | — | reject (xsec drags it) |

TS-trend per-year net%: 2020 +73, 2021 +75, 2022 +36, 2023 +61, 2024 +40, 2025 +13, 2026 +8 —
**positive EVERY year**.

## Read
- **Diversifying the trend across the top-20 beats the BTC anchor**: IS +1.15→+1.68, DD −35%→−28%,
  total +573%→+1271%, positive every single year. OOS held positive (+0.64→+0.50; the slight dip is
  higher OOS vol, but 2025 +13% / 2026 +8% are real positive returns, not a low-vol mirage).
- **Cross-sectional momentum FAILS OOS** here (−1.81; 2023/2025/2026 negative) — momentum reversals
  in the recent regime. Adding it (combo) drags the trend down. So XSEC is rejected, not bundled.
  (Matches the literature caveat that XS-momentum crashes in reversals; TS-momentum is sturdier.)

## Verdict: EXPLORATION-PROMISING — diversified TS-trend is the new working baseline
## Next (little by little)
- iter-003: lift the OOS +0.50 / cut the −28% DD without breaking IS — candidates (one at a time):
  trend-strength / regime filter (sit out chop), horizon-weight optimization (walk-forward),
  per-coin vol-floor, a FUNDING tilt as a small additive overlay (earn carry on the held legs).
