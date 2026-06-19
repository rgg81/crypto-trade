# portfolio-iteration EXPLORATION-001 — BTC time-series momentum (anchor)

**Axis:** validate a vol-targeted multi-horizon trend signal on BTC, long & short, nets positive
after realistic costs + funding. The single-asset anchor for the top-20 L/S portfolio.
**Code:** `analysis/portfolio/iter_001_btc_trend.py`. Signal = mean sign of trailing returns over
{7d,14d,28d,56d} (8h candles), sized inverse-vol (target 1%/candle, max 2x). Decide close[t] →
fill open[t+1] → hold; taker 0.05%/side on turnover; funding paid/earned on the perp hold. Leak-safe.

## Result
| | IS Sharpe | OOS Sharpe | maxDD | net total |
|---|---|---|---|---|
| **BTC TREND (net)** | **+1.15** | **+0.64** | **−35%** | +573% |
| buy & hold BTC | +0.98 | −0.36 | −77% | +630% |

per-year net%: 2020 +92, 2021 +18, 2022 ~0, 2023 +66, 2024 +18, 2025 −4, 2026 +27. Turnover 0.08/candle.

## Read
- Beats buy-and-hold risk-adjusted (IS +1.15 vs +0.98; **OOS +0.64 vs −0.36** — the short side caught
  the 2025-26 chop where B&H lost). HALVES the drawdown (−35% vs −77%). Low turnover → taker fees fine.
- OOS +0.64 is modest but real, honest (leak-safe, net of cost+funding), and improvable. A legitimate
  POSITIVE anchor — no HFT / market-making / VIP needed.
- 2022 ~0 (chop) and 2025 −4% are the weak spots — diversification (the cross-section) + a trend-
  strength/regime filter are the obvious next lifts.

## Verdict: EXPLORATION-PROMISING — anchor established
## Next
- iter-002: expand to top-20, add CROSS-SECTIONAL momentum (rank long winners / short losers),
  portfolio vol-targeting + equal-risk weights — diversification should cut the −35% DD and lift OOS.
- then layer factors one at a time (carry tilt, short-term reversal, regime filter), each kept only
  if it lifts net Sharpe.
