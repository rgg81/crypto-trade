# BASELINE_V1_BUNDLE — the v1 portfolio (ETH + BTC + THETA)

**Established 2026-06-18.** The payoff of three both-positive, low-cross-correlation single-symbol
baselines: a diversified portfolio that achieves **breadth + de-concentration + higher Sharpe** than any
single coin — the broad OOS the campaign sought (intractable single-symbol; achieved at the PORTFOLIO
level via low-correlation diversification).

## Components (each an independently-merged single-symbol baseline; pairwise-DISJOINT coins)
| coin | baseline | architecture | single OOS (monthly-agg) |
|---|---|---|---|
| ETH | iter-034 (tag v0.v1-035) | deterministic core (strip-model) | +0.82 |
| BTC | iter-020 (tag v0.v1-020) | model-gated trend-state | +0.45 |
| THETA | iter-047 (tag v0.v1-047) | deterministic core, low-corr | +0.74 |

## Construction (parity-clean; IS-only weights)
- **Each coin's single-symbol strategy runs INDEPENDENTLY** (as in live: each specialist trades only its
  own coin). The portfolio is the **capital-weighted SUM of the independent coins' PnL** — NO post-trade
  netting/aggregation. Backtest-live parity preserved (the weights are fixed capital allocations, not
  position-level netting). [feedback_v1_backtest_live_parity_hard]
- **No coin overlap:** each coin owned by exactly one component (ETH/BTC/THETA are disjoint).
  [feedback_v1_bundle_no_coin_overlap]
- **Weights: IS-only inverse-volatility** (w ∝ 1/std(IS monthly PnL), computed from IN-SAMPLE data only):
  ETH 0.336 / BTC 0.401 / THETA 0.263. [feedback_v1_bundle_weight_is_only]
- Reproduce: `analysis/portfolio/bundle_firstcut_eth_btc_theta.py`.

## Portfolio metrics (OOS, monthly-agg) vs single coins — the breadth payoff
| book | OOS monthly Sharpe | OOS trades | OOS top-1 share | OOS top-2 share |
|---|---|---|---|---|
| ETH alone | +0.82 | 34 | 66% | 124% |
| BTC alone | +0.45 | 38 | 133% | 231% |
| THETA alone | +0.74 | 35 | 47% | 92% |
| **PORTFOLIO (equal-wt)** | **+1.04** | **107** | **28%** | **53%** |
| PORTFOLIO (inv-vol) | +1.02 | 107 | — | — |

- **Sharpe:** portfolio OOS +1.04 > every single coin (best +0.82) — diversification benefit, crosses 1.0.
- **Breadth:** 107 OOS trades (3× any single coin's ~35).
- **De-concentration:** top-2 share 53% vs single coins' 92-231% — far broader. (The single-symbol
  de-concentration that was INTRACTABLE — 6+ mechanisms failed — is achieved here at the portfolio level.)
- **Driver:** low cross-correlation, OOS: ETH-THETA **−0.05** (genuinely independent), ETH-BTC 0.25,
  BTC-THETA 0.39. THETA (the low-corr coin) is the key diversifier.

## CAVEATS (load-bearing)
1. **First-cut aggregation.** Metrics are a simple monthly-SUM of net_pnl_pct (NOT the baselines'
   weighted/vol-targeted series), so absolute Sharpes differ from the single-coin baseline-doc headlines;
   the RELATIVE finding (portfolio > single on Sharpe AND concentration AND breadth) is the robust claim.
2. **Short OOS (~15 months → 15 monthly points):** the +1.04 has WIDE error bars; the durable claim is
   the diversification DIRECTION (portfolio beats single coins), not the exact magnitude.
3. **top-2 53% still > 40%** (the strict single-coin falsifier threshold) — but dramatically better than
   single coins; ADDING MORE low-corr coins would de-concentrate further (toward <40%).
4. **Component validation inherited:** ETH/THETA deterministic cores are seed-invariant (50-seed
   byte-identical) + leak-verified (ETH iter-034 Critic PASS); BTC iter-020 K=20-confirmed. A full
   portfolio backtest with the proper weighted PnL series + DSR/PBO is the next rigor (this is the
   demonstration-grade portfolio record).

## Next
1. **Add more low-corr coins** (screen trend-IS × corr first; the screen flagged candidates) → push top-2
   below 40% + deepen breadth.
2. **Full portfolio backtest** (proper weighted PnL series, DSR/PBO/PSR, 10-seed where applicable) for a
   CONFIRMATION-grade bundle merge.
3. **THETA gentler DD primitive** (its 46% standalone OOS MaxDD; the portfolio already dilutes it).
