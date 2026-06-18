# Top-20 breadth test — honest walk-forward SMA does NOT generalize (2026-06-18)

**Question (user):** does the honest walk-forward SMA strategy — which beat the hindsight-fixed-200
on ETH and THETA — expand to the top-20 coins (ex-stablecoins)?

**Method:** `analysis/top20_walkforward_sma_sweep.py` — self-contained backtest faithful to the
committed v1 deterministic core (trend-state direction + conviction gate q=0.40 + per-month
walk-forward SMA selection on a 50..400 grid, fixed-horizon N=42 with 1.45×NATR intrabar SL,
training_months=24, embargo=43 candles, OOS_CUTOFF=2025-03-24). Pure price action (LightGBM
bypassed) so it sweeps the FULL cross-track top-20 (the v1 runner excludes v2/v3 symbols). Measures
the RAW per-trade signal (no R5 vol-targeting — a per-coin overlay), so it matches the committed RAW
`net_pnl_pct`, not the R5-weighted `comparison.csv`. Leak-safe: window + threshold fit on past-only
training window each month (proven by the same future-perturbation argument as the committed code).

## Result (monthly Sharpe; WF = per-month walk-forward selection; FIX = biased fixed-200 reference)
| | WF IS | WF OOS | FIX IS | FIX OOS |
|---|---|---|---|---|
| BTC | +0.78 | +0.70 | +0.92 | +0.58 |
| ETH | +0.27 | +0.93 | +0.76 | +1.07 |
| BNB | +0.33 | −0.12 | +0.40 | +0.16 |
| SOL | +0.94 | −0.41 | +1.00 | −0.04 |
| XRP | +0.33 | −0.23 | +0.25 | +0.25 |
| ADA | +0.62 | +0.22 | +0.78 | +0.16 |
| DOGE | +0.83 | −0.64 | +0.57 | +0.05 |
| TRX | −0.33 | +0.85 | +0.26 | +1.02 |
| AVAX | +0.88 | +0.19 | +0.97 | −0.08 |
| LINK | +0.03 | +0.73 | −0.01 | +0.25 |
| DOT | +0.08 | +0.79 | +0.60 | +0.27 |
| BCH | −0.10 | −0.96 | −0.19 | +0.29 |
| LTC | −0.52 | −0.15 | −0.26 | −0.01 |
| MATIC | +0.52 | n/a | +0.44 | n/a (POL rename; klines end 2024-09) |
| UNI | +0.58 | −1.42 | +0.29 | +0.98 |
| ATOM | +0.41 | −0.51 | +0.22 | −1.25 |
| ETC | +0.25 | −0.59 | +0.40 | −1.27 |
| XLM | +0.45 | +0.25 | +0.40 | +0.94 |
| NEAR | +0.30 | −0.43 | +0.84 | −1.44 |
| FIL | +1.30 | −1.08 | +0.70 | −1.52 |

**Aggregate (19 coins with OOS):**
- WF both-positive (IS>0 & OOS>0): **7/19**
- WF OOS > 0: **8/19** (coin flip)
- WF OOS ≥ FIX OOS: **9/19** (a wash — neither systematically wins)
- median WF OOS −0.15 / FIX OOS +0.16 ; mean WF OOS −0.10 / FIX OOS +0.02

## Findings (honest, no self-deception)
1. **Trend-following SMA is NOT a robust broad edge.** On average across the top-20 the OOS Sharpe is
   ≈ 0 (mean wf −0.10, fix +0.02). It works on a MINORITY (BTC, ETH, TRX, LINK, DOT) and fails on
   many (DOGE, BCH, LTC, UNI, ATOM, ETC, NEAR, FIL).
2. **ETH and THETA were favorable draws, not the rule.** The earlier "honest walk-forward wins"
   generalizes to neither breadth nor to a top-20 portfolio.
3. **Walk-forward vs fixed-200 is a WASH at breadth** (9/19), median slightly favoring fixed. So the
   deeper truth supersedes both my earlier "fixed wins" and the corrected "walk-forward wins": the
   *signal itself* (SMA trend) doesn't generalize — the window-selection question is second-order.
4. **IS does NOT predict OOS** — high-IS coins frequently flip negative OOS (FIL +1.30→−1.08; SOL
   +0.94→−0.41; NEAR +0.84→−1.44; DOGE +0.83→−0.64). So you cannot pick the trend-tradable subset
   ex-ante from IS. A naive top-20 portfolio of this strategy is ≈ break-even-to-negative OOS.

## Caveats
- RAW signal only (no R5 vol-targeting). R5 helped ETH's official OOS (+0.60 raw → +0.99 weighted)
  but BROKE the ensemble (−0.53) — it is a per-coin overlay, not a reliable rescue. A full
  per-coin run (R5 on) could shift individual coins either way; the breadth conclusion (≈0 mean
  edge, coin-flip) is unlikely to reverse.
- ~40 OOS trades / ~15 months per coin → individual-coin OOS is noisy (wide bars); the AGGREGATE
  (mean ≈ 0 across 19) is the robust statement.
- close-to-close selection objective vs SL-bounded execution mismatch (inherited from the committed
  core); a refinement, not the driver.

## Implication
Trend-following SMA alone is not a top-20 strategy. Its value is confined to a coin-specific minority
that can't be identified in advance from IS. This also puts the ETH+BTC+THETA bundle under scrutiny —
those three are among the trend-favorable coins (selection/survivorship). Next options: (a) accept
trend as a coin-specific tool only; (b) look for an ex-ante filter that predicts which coins trend
(the missing piece — IS Sharpe does not); (c) combine trend with an orthogonal signal.
