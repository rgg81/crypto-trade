# Portfolio Iteration — systematic LONG/SHORT top-20 crypto perp portfolio

## Mission
Build, and then **improve little by little**, a systematic **long/short top-20 (ex-stablecoin)
perpetual-futures portfolio** on Binance Futures. Medium-frequency (daily/weekly rebalance), plain
**taker** fees, **no** HFT, **no** market-making, **no** VIP fee tier, **no** special infrastructure.

This is what systematic crypto funds actually run: a vol-targeted multi-factor cross-section. The
literature is clear it works at accessible size/cost:
- **Time-series momentum / trend** on crypto perps: net Sharpe ~1.5–2.4 in recent studies (one
  rule-based system on 150+ Binance perps 2022–24: Sharpe 2.41, maxDD −12.7%, net of cost+funding).
- **Cross-sectional momentum** (long winners / short losers): Sharpe ~1.5 (28d lookback / 5d hold).
- **Factor combinations** (trend + XS-momentum + carry + short-term reversal): OOS Sharpe >1–2.

Sources: Liu & Tsyvinski (2021); Han et al. trend factor (JFQA 2024); AUT TS-vs-XS momentum;
AdaptiveTrend (arXiv 2602.11708). The goal is a real, improving net Sharpe — not perfection.

## The philosophy (READ THIS — it is the point)
**Improve little by little.** Each EXPLORATION makes ONE change, measured on the backtest. A change
that helps gets kept; a change that doesn't informs the next one. Negative results narrow the search
— **they do not end it.** We are building a strategy, not looking for reasons to quit. Be rigorous
about overfitting, NOT defeatist about edges.

## Rigor (recalibrated — honest, not self-defeating)
A change is "real" when it survives:
1. **Realistic execution** — signal decided on candle CLOSE[t], rebalanced at OPEN[t+1], held; **taker**
   fee + slippage per turnover; **funding** paid/earned on perp holds. Leak-safe (signals past-only).
2. **Walk-forward params** — any tunable (lookback, vol-target, thresholds) is selected per-period on
   PAST data, never hindsight-picked across the whole sample.
3. **OOS holdout** — `OOS_CUTOFF = 2025-03-24`. Evaluate OOS once per confirmation. Treat OOS as ONE
   regime (informative, not gospel): judge per-year robustness too, don't over-react to one window.
4. **Benchmarks** — beat buy-and-hold BTC AND an equal-weight top-20 basket on risk-adjusted terms.
5. **Turnover / cost-stress** — report turnover + Sharpe at 1×/2× cost. Net Sharpe is what counts.

**NOT in the gauntlet** (these killed the prior carry effort wrongly): no institutional-capacity
liquidity floor, no maker-only / VIP-fee assumption. This is a normal-size portfolio; taker fees on
the top-20 (deep, liquid) are the cost model.

## Foundation (build once, reuse every iteration)
- `analysis/portfolio/engine.py` — realistic portfolio backtest: per-coin signal → target weights
  (long/short, dollar-neutral or net-tilted) → next-bar-open rebalance → hold → taker cost on weight
  change + funding on perp legs → portfolio return series. Vol-targeting at the portfolio level.
  Helpers: `monthly_sharpe`, per-year breakdown, maxDD, turnover, benchmark comparison.
- `analysis/portfolio/universe.py` — top-20 by trailing $-volume, ex-stablecoins, point-in-time.
- Tests in `tests/` — leak test (future-data perturbation), dollar-neutrality, cost accounting.
- Data already on disk: `data/<SYM>/8h.csv` (726 coins) + `data/funding_rates/<SYM>.csv` (572). 8h
  candles (the project's sacred interval). No re-fetch.

## Cadence
- **EXPLORATION** — one change (a new factor, a signal/lookback refinement, portfolio-construction
  improvement, a regime filter), scored on the backtest with the rigor checks that don't need OOS.
  Cheap, frequent. Logged to `diary-portfolio/EXPLORATION-NNN.md` with the numbers + verdict.
- **CONFIRMATION** — reveal OOS + full gauntlet; only this promotes a change into the baseline
  (`BASELINE_PORTFOLIO.md` + the engine defaults). Commit every step with the honest result.

## Roadmap (build BTC-first, then widen — little by little)
1. **iter-001** — BTC time-series momentum (trend) standalone: validate the single-asset trend signal
   (multi-horizon, vol-scaled, long & short) nets positive after costs+funding. Anchor.
2. **iter-002+** — expand to the top-20; cross-sectional momentum (rank long/short); portfolio
   construction (vol-target, equal-risk weights, correlation-aware).
3. then layer factors one at a time: carry (funding tilt), short-term reversal, trend-strength /
   regime filter, vol-scaling refinements — each its own EXPLORATION, kept only if it lifts net Sharpe.
4. CONFIRMATION → baseline → repeat. The portfolio gets better one accretive change at a time.

## Sacred constants
- `OOS_CUTOFF = 2025-03-24` (immutable). 8h candles. Signals past-only; fills at open[t+1].
- Never tune on OOS; never trim the window. Report net (after cost+funding), not gross.
- Universe = top-20 by liquidity, ex-stablecoins, point-in-time (no survivorship cherry-pick).

## Run
```
uv run pytest tests/test_portfolio_engine.py -q     # foundation stays green
uv run python analysis/portfolio/iter_001_btc_trend.py   # current iteration
```
