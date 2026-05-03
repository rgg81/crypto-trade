# Crypto-Native Alpha Sources — Deep Reference

Comprehensive treatment of crypto-specific edge sources at the 8h timeframe, with paper-by-paper citations from 2023–2025 research. The main agent file's Section 5 is a 600-word summary; this file provides the depth.

This material draws on López de Prado's methodology canon (see `methodology-deep.md`) but applies it to crypto-native phenomena that don't appear in equities or commodities.

---

## 1. Why 8h Is Special

Four reasons the 8h timeframe captures structure that 1h and 1d both miss:

**Funding-cycle alignment.** Binance, OKX, and Bybit settle perpetual futures funding at 00:00, 08:00, and 16:00 UTC. An 8h candle is **exactly one funding period** — features computed at candle close are funding-period-aligned, not phase-shifted noise. Pre-funding microstructure (traders flatten before timestamps to avoid payments) creates a measurable volume/CVD pattern in the last hour, persistent at 8h aggregation.

**Behavioral cycle alignment.** 8h candle boundaries roughly coincide with Asia close → EU/US session handoff. The "tea time" paper (Springer s11156-024-01304-1, 2024) documents activity/volatility/illiquidity peaks at 16–17 UTC, with Amberdata's research showing peak liquidity at 11 UTC and trough at 21 UTC.

**Microstructure-noise filter.** 8h dampens spread noise and HFT-flicker but preserves the liquidation-cascade timescale (median cascade 2–6h per Ali, "Anatomy of the Oct 10–11 2025 Liquidation Cascade," SSRN 5611392).

**On-chain compatibility.** ~48 BTC blocks per 8h — enough confirmations that on-chain features are stable within-candle. Block-publication lag is well within the candle period.

---

## 2. Microstructure Features at 8h

At 8h, classical HFT order-flow noise washes out and "session microstructure" becomes the relevant scale. Available features:

**Range-spike / volatility-regime triggers.** The codebase's `range_spike_16` (4h-rolling 15m) exemplifies the class. At 8h, the analog is `(high − low) / open` normalized by a 4–8 candle rolling mean. Karagiorgis et al. (arXiv:2410.12801, 2024) document strong skew/kurtosis clustering at the regime extremes — this is what range-spike detects.

**VPIN at coarse buckets.** Easley/de Prado/O'Hara's volume-time bucketing extends naturally to 8h: bucket each candle's notional volume by side and compute |buy − sell| / total. Bitcoin VPIN significantly predicts price jumps with persistent positive serial correlation (ScienceDirect S0275531925004192, "Bitcoin wild moves," October 2025). Use 8h trade-side aggregates from the Binance trade tape — full L2 reconstruction is unnecessary.

**Realized higher moments.** Jia et al. (2021) and Karagiorgis et al. (2024) show kurtosis is **positively** related to future returns while skewness is **negatively** related across the cross-section of 84 cryptos. At 8h, compute realized skew/kurtosis from constituent 5m or 15m returns within each candle.

**Bid-ask volatility spread.** Kaiko reports BTC-perp 10M quote-size spread of ~0.25% normal, spiking to 7.95% during the March 2020 crash. Rolling spread expansion at 8h is a clean liquidity-stress feature.

**Aggressive/passive imbalance (CVD).** From Binance trade flag, build cumulative volume delta and an 8h slope. Combined with HAR-RV (heterogeneous autoregressive realized volatility), this is the strongest 8h "where-is-volume-coming-from" feature available without full L2.

---

## 3. Funding Rates — The 8h-Native Alpha

Funding rates settle every 8h (00/08/16 UTC). Persistent funding regimes encode positioning crowding.

**Theoretical foundation.** Ackerer, Hugonnier, Jermann (2024), "Fundamentals of Perpetual Futures" (arXiv:2212.06888v5), provides the formal arbitrage decomposition: the spot-perp basis ≈ expected funding integrated over horizon. The 2025 paper "Designing funding rates for perpetual futures" (arXiv:2506.08573) gives the replicating-portfolio derivation.

**Empirical regime.** Quantjourney's substack and BlOFin Academy document positive funding ≥0.05–0.2% per 8h as a classic short-the-crowd signal; reverting funding = short-squeeze setup. The BIS Working Paper 1087 (2025), "Crypto Carry," documents that carry (futures > spot) predicts liquidations: **a 10% carry shock predicts a 22% jump in sell liquidations.** This is the single most actionable empirical paper for a crypto futures bot.

**Features to engineer:**
- Current funding rate (raw)
- 8h / 24h / 72h funding momentum
- Funding rate z-score (rolling 30 candles)
- Premium index (raw mark-vs-index, before the clamp — more responsive than realized funding)
- Funding/price correlation (rolling 14 candles)

**Pitfall:** Mango Markets (Eisenberg, 2022) demonstrated funding-rate manipulation via thin index sources. Avoid using single-venue premium indices; use volume-weighted multi-venue or rely on the exchange's already-clamped funding rate.

---

## 4. Liquidation Cascades

Liquidations are clustered, self-exciting events.

**Modeling framework.** Multivariate Hawkes processes (Bacry/Muzy formulation) treat `liq_count_t` and `liq_notional_t` as self-exciting + cross-exciting between long-side and short-side. Per "Anatomy of the Oct 10–11 2025 Liquidation Cascade" (Ali, SSRN 5611392), $19B was liquidated in 24h, self-reinforcing through stop-loss/liquidation-price chaining.

**Data sources:** CoinGlass, Hyperliquid (per-symbol liquidation streams), Binance public liquidation feed.

**Features to engineer:**
- Liquidation count and notional, by side, in last 1/4/8/24h
- Hawkes intensity estimates (with care — fitting in real-time is fragile)
- Cluster boolean: true if last 8h liquidation > μ + 3σ of trailing 30-day distribution
- Asymmetry: long-liq notional / short-liq notional (extreme values flag one-sided pressure)

**Pitfall:** Liquidation data is venue-specific and reporting lags by 1–5 minutes. At 8h cadence this is irrelevant, but for shorter timeframes account for the lag.

---

## 5. On-Chain Features

For BTC and ETH at 8h, on-chain features add genuine information beyond price.

**Critical lookahead rule:** A block is "knowable" only after **6 confirmations on BTC, ~12 on ETH**. Glassnode metrics carry a 1-block to ~1h publication lag. **At 8h cadence, lag the on-chain feature by ≥1 candle to avoid leakage.**

**Top features (BTC/ETH):**

- **Exchange Whale Ratio** (top-10 inflows / total inflows): readings >0.85 preceded ≥30% drawdowns in 2024–25 per CryptoQuant data
- **MVRV-Z** for cycle anchor (per ScienceDirect S0952197625010875, 2025: on-chain + ML beats price-only)
- **NUPL, SOPR, LTH-SOPR** (155-day cohort) for holder-cohort stress
- **CDD / Coin Days Destroyed / Dormancy** for old-coin reactivation
- **Active addresses** (rolling 7-day mean)
- **Realized cap / market cap** (cycle-anchor)

**Data sources:** Glassnode (longest BTC on-chain history), CryptoQuant (free-tier API, exchange flow / miner / stablecoin metrics), CoinMetrics State of the Network (gold standard for definitions and free float supply / realized cap).

**Pitfall:** On-chain data is BTC/ETH only at 8h. For altcoins, on-chain signals are sparse, low-fidelity, or unavailable. The codebase's `cross_btc_*` features partially substitute — using BTC's on-chain regime as an alt-regime input.

---

## 6. Open Interest Dynamics

OI delta and OI/marketcap encode leverage stretch.

**Empirical patterns** (from Gate.com 2025 derivatives writeup and Amberdata 2026 Outlook):
- A 20% OI drop ≈ deleveraging/fear regime
- Rising OI + stable price = stealth leverage build
- OI rotation across exchanges (Binance vs OKX vs Bybit) flags venue-specific positioning

**Features to engineer:**
- Per-symbol OI 8h delta
- OI / market cap ratio
- OI venue concentration (Binance share of total)
- Cross-OI correlation (BTC OI vs alt OI — divergence signals selective deleveraging)

---

## 7. Cross-Exchange Premium / Basis

Premium index feeds into funding but trades faster than the funding clamp.

**Mechanics:** BlOFin academy "Spot-Perp Basis" treats persistent +basis as positioning-bullish, sudden basis collapse as deleveraging. Kaiko's bid-ask spread crosswalks identify exchange-specific dislocation.

**Features:**
- Mark-vs-index spread (raw premium)
- Cross-exchange basis: (Binance perp − Coinbase spot) / Coinbase spot
- Basis 8h delta and z-score

---

## 8. BTC Dominance — Alt-Regime Indicator

Per Kaiko / 21shares research: every alt-season was preceded by a BTC.D peak.

**As a feature for an alt model:**
- 30-day BTC.D z-score
- 7-day BTC.D momentum (crude proxy for capital-rotation regime)
- BTC.D acceleration (second derivative)

**Codebase note:** v1 already uses `cross_btc_ret_*` and `cross_btc_corr_*`; v2 has a BTC trend filter (±20%, 14d lookback) that gates trades during BTC regime divergence.

---

## 9. DeFi-Specific Signals

**TVL / Market Cap.** ScienceDirect S1544612324017343 (2024), "Trust as a driver in the DeFi market," shows TVL/MCAP bands anticipate DeFi-token price moves.

**Stablecoin minting/burning.** DefiLlama documents a $200M USDC mint preceding a 12% BTC rally in 48h (Nov 2024). The **Stablecoin Supply Ratio** (BTC mcap / stablecoin mcap) is a tested mean-reverting positioning gauge. Cf. BIS Working Paper 1270 "Stablecoins and safe asset prices."

**Lending utilization.** Aave/Compound utilization spikes signal leveraged-long demand.

**Pitfalls:** Stablecoin depeg events (S&P documented 609 distinct depeg events in 2023; USDC's March 2023 depeg deviated 3% from $1) corrupt any feature normalized against affected stablecoins. **Always mask training samples around depeg events** (>0.5% deviation from $1).

---

## 10. Behavioral / Sentiment Edges

Crypto's retail-driven nature makes behavioral edges fertile.

**Sentiment data:**
- Twitter/Reddit sentiment indices
- Alternative.me Fear & Greed Index
- Funding-rate as positioning proxy (more honest than survey-based sentiment because traders pay for it)

**Empirical evidence:** ScienceDirect S2214635025000243 (2025), "Investor sentiment and cross-section of cryptocurrency returns," shows lagged sentiment predicts +0.24–0.25% next-day returns OOS. **Use as a fade signal at extremes** — not a trend signal.

**Event-study patterns.** ScienceDirect S0927538X25002501 documents the "buy the rumor, sell the news" pattern: positive abnormal returns 30–60 days pre-event (halving, ETF, hard fork), negative 0–10d post-event. April 2024 halving rallied only ~100% to October 2025 — Amberdata's "2026 Outlook: End of the Four-Year Cycle" argues ETF flows now dominate supply-shock narrative.

**Overreaction.** ResearchGate 340627203 (Caporale & Plastun) documents short-term price overreactions with statistically significant reversal. At 8h, large negative-return shocks (>3σ) followed by next-candle reversal is exploitable on majors.

---

## 11. Crypto-Specific Pitfalls

**Survivorship bias.** Concretum/CoinAPI/Stratbase: 14k of 24k tokens are "dead." A naïve "top-20 by mcap, monthly rebalance" backtest inflates returns ~4× (2,800% biased vs 680% real, 2020–21). Mitigation: include delisted symbols in CSV history; the codebase's v2 weight_factor=0 trick is structurally correct.

**Stablecoin depeg corruption.** As noted in §9 — mask training around depegs.

**Exchange-specific liquidity.** A $100k clip on Binance ≠ $100k on Kraken/Coinbase. If your live execution is Binance-only, train on Binance data — Kaiko's spread cheatsheet shows venue dispersion of 5–10× during stress.

**Listing/delisting non-stationarity.** A coin's first 30 days post-listing has a return distribution that does not generalize. **Drop the first 30–60 days for newly listed symbols.**

**Funding-rate manipulation.** Mango Markets is the canonical case (see §3).

**24/7 + session bias.** No overnight gap, but Springer (2024) finds activity/volatility/illiquidity peaks at 16–17 UTC. Crypto often shows **within-session reversal** unlike equities.

**On-chain look-ahead.** Block time ≠ knowable time. Use confirmation time + indexer publication lag (~5–60 min). At 8h cadence, lag 1 candle.

---

## 12. What a Crypto Quant Should KNOW but NOT Use at 8h

Disambiguating scope — these are crypto-microstructure topics that are real but irrelevant at 8h cadence:

- **Tick-level order flow** — signal decays at <5min
- **L2 order-book reconstruction / queue position** — latency-sensitive
- **Latency arbitrage / co-location** — HFT scope
- **Cross-margin liquidation engine internals** — relevant for *risk modeling* (your own SL/TP placement vs liquidation price), **not for alpha**
- **DEX MEV / sandwich detection** — alpha decays before 8h close
- **Hyperliquid one-block execution** (0.2s latency) — relevant only if migrating venue, irrelevant for 8h signal generation

---

## 13. Recent Research Roll (2023–2025)

Curated list of papers and posts to cite:

**Funding & Perpetuals:**
- Ackerer, Hugonnier, Jermann (2024), "Fundamentals of Perpetual Futures" (arXiv:2212.06888v5) — formal arbitrage decomposition
- Kim & Park (2025), "Designing funding rates for perpetual futures" (arXiv:2506.08573)
- BIS Working Paper 1087 (2025), "Crypto Carry" — carry shock → liquidation prediction
- "Two-Tiered Structure of Cryptocurrency Funding Rate Markets" (*Mathematics* 14/2/346, 2026)

**Microstructure:**
- "Bitcoin wild moves: Evidence from order flow toxicity and price jumps" (ScienceDirect S0275531925004192, October 2025) — VPIN→jump prediction
- "Exploring Microstructural Dynamics in Crypto LOBs" (arXiv:2506.05764, 2025)
- "Skewness-Kurtosis plane for cryptocurrencies" (Karagiorgis et al., arXiv:2410.12801, 2024) — higher-moment factor structure
- "Anatomy of the Oct 10–11 2025 Liquidation Cascade" (Ali, SSRN 5611392) — empirical cascade microstructure

**Sentiment / Behavioral:**
- "Investor sentiment and cross-section of cryptocurrency returns" (ScienceDirect S2214635025000243, 2025)
- "The cryptocurrency halving event" (ScienceDirect S0927538X25002501, 2025)
- "The crypto world trades at tea time" (Springer s11156-024-01304-1, 2024)

**On-chain & ML:**
- "Using ML/DL, on-chain data, and TA for predicting BTC" (ScienceDirect S0952197625010875, 2025)
- "ML-driven feature selection and anomaly detection for BTC" (ScienceDirect S1568494625016953, 2025)
- "Forecasting Bitcoin volatility spikes from whale transactions" (arXiv:2211.08281)
- "Adaptive Sample Weighting with Regime-Aware Meta-Learning" (Jang et al., ICAIF 2025)

**Stablecoins / DeFi:**
- "Trust as a driver in the DeFi market" (ScienceDirect S1544612324017343, 2024) — TVL/MCAP
- BIS Working Paper 1270 "Stablecoins and safe asset prices"
- Cowles Foundation (Gorton/Klee, 2023), "Leverage and Stablecoin Pegs"
- "Detecting Stablecoin Failure" (MDPI 7/4/68, 2025)

**Industry research / data providers:**
- Coin Metrics, *State of the Network* substack
- Glassnode `glassnode.com/insights` and "On-Chain Data Solutions for Quant Trading"
- CryptoQuant, exchange flow / miner / stablecoin metrics
- Kaiko / Amberdata, institutional CEX trade & LOB feeds
- Binance Research, funding-rate / basis / OI deep dives
- ADIA Lab Crypto Working Papers (`adialab.ae`)

**Cadence to skim:** arXiv `q-fin.TR` and `q-fin.CP` listings monthly.

---

## 14. Cross-References

- §1, §3 → cited in main agent §3 (Project Mode — why 8h cadence matters)
- §3, §4, §5, §6 → cited in main agent §5 (Crypto-Native Alpha Sources summary)
- §11 → cited in main agent §9 (Anti-patterns: survivorship, stablecoin depeg, on-chain leakage)
- §13 → primary source list when the agent needs to cite recent crypto research
