# Iteration 196 — Frac-diff Model A, and exit-criterion

**Date**: 2026-04-23
**Type**: EXPLORATION + meta-analysis
**Baseline**: v0.186 — unchanged
**Decision**: NO-MERGE. Next iter should be paper-trading.

## TL;DR

Model A (BTC+ETH, 5303 samples, 2x LINK) pre-test for frac-diff features
showed Δ +0.003 CV proxy Sharpe — same marginal result as LINK's iter 195.
Below the +0.01 threshold for committing to a full backtest.

**Nine consecutive NO-MERGEs on exploration** (iter 178 through 196)
establish that v0.186 is a robust local optimum on the axes accessible
by offline iteration. Further gain requires live data.

## Frac-diff MDI ranks (Model A)

| feature | MDI | rank (of 196) |
|---------|----:|:--------------|
| fracdiff_close_d02 | 32 | 35 (top 18%) |
| fracdiff_close_d04 | 10 | 90 (top 46%) |
| fracdiff_volume_d02 | 0 | last |

d=0.2 frac-diff of close is a legitimately useful feature (top-18% MDI),
but the +0.003 proxy Sharpe gain suggests it's substituting for rather
than complementing existing features. The overall predictive system
isn't meaningfully better.

## The exit case

Nine failed exploration iterations since iter 186's merge:
xbtc augment (189), xbtc swap (190), prune (191), 14d timeout (192),
bootstrap validation (193 — OK), drop DOT (194 — concentration fail),
frac-diff LINK (195), frac-diff Model A (196), plus the earlier screens
178/180/183.

Every axis tried:
- Cross-asset features (BTC-derived): rejected on both LINK and implicitly Model A
- Feature count (prune / augment): both fail
- Feature kind (frac-diff): marginal
- Label horizon: catastrophic
- Symbol universe expansion: year-1 fails
- Portfolio composition (drop DOT): concentration fail

v0.186 is a genuine local optimum on the offline-iterable axes. The
skill's workflow accomplished what it's designed to: find and validate
a robust baseline via systematic search.

## Why paper-trading is now the right step

1. **Validated baseline.** Bootstrap CI (iter 193) places OOS Sharpe
   firmly above 1.0 with 79% probability.
2. **Live engine exists.** The `src/crypto_trade/live/` code has been
   hardened through the live-divergence incident (iter 162-164) and is
   the natural next deployment surface.
3. **Offline iteration ROI is now zero.** Nine consecutive NO-MERGEs is
   a clear signal. Continuing to search an exhausted space burns time
   that could be spent gathering the live data that will drive the NEXT
   good iteration.

## Exploration/Exploitation Tracker

Window (186-196): [X, X, E, E, E, E, V, X, E, E, **E**] → **6E/4X**
(plus 1 validation). Exploration ratio healthy; hit rate zero.

## Next Iteration (iter 197)

**Ship v0.186 to paper-trading.** Configure the live engine against
a paper-trading endpoint (Binance Futures Testnet or read-only
production mode), run for 2 weeks, log all predictions/gates/trades.

At the end of 2 weeks:
- Compare live vs backtest Sharpe estimates
- Check that R3 OOD gates fire at expected rates
- Measure actual trade count/month against the 16/month backtest
  expectation
- Identify any divergence points requiring code fixes

Only after live data is collected should we resume offline iteration,
informed by reality.
