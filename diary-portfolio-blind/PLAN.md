# Baseline-Blind Top-20 Portfolio: PLAN.md

**CONTEXT:** This is a FRESH start. We are NOT looking at the existing deployed strategy (trend+carry, hysteresis bands, eligibility-exit, funding flows, etc.). We MUST invent from first principles.

**MISSION:** Invent NOVEL top-20 (ex-stablecoin) crypto perpetual-futures L/S strategies that maximize Sharpe ratio, robust across regimes, with NO look-ahead bias.

**HARD CONSTRAINTS:**
1. No cheating / no look-ahead bias: All walk-forward parameters calibrated on IS data only (pre-2025-03-24). OOS revealed ONLY at CONFIRMATION.
2. Sharpe is the metric: Maximize risk-adjusted return, NOT absolute return.
3. Robust to market conditions: Perform across regimes (trend, chop, vol spikes).
4. Respect OOS_CUTOFF: 2025-03-24 (immutable).
5. Always refresh top-20 list: Universe = top 20 coins by open interest (ex-stablecoins), re-rank dynamically.
6. Long/short portfolio: Net positions can be long or short per-coin; overall book can be net-long, net-short, or market-neutral.

**DATA AVAILABLE (8h candles, 667 coins → 2026-07-08):**
- OHLCV: open, high, low, close, volume, taker_buy_volume
- Funding rates (8h)
- Top-20 by open interest: recompute dynamically per candle
- **NOT available:** OI history (~30d only), spot prices, options/IV, liquidations, positioning data

---

## CREATIVE APPROACH SKETCHES (First-Principles Brainstorm)

Below are 5 novel approach sketches. These are intentionally DIFFERENT from the existing deployed strategy. The goal is creativity.

### Approach 1: **Volatility Regime-Switching Momentum**

**Core idea:** Crypto markets have distinct volatility regimes (low-vol "grind up", high-vol "chop/crash"). A single momentum signal fails across regimes. Instead, detect the regime and adapt the strategy.

**Mechanism:**
- Regime detector: Use rolling ATR, realized volatility skew, and funding-rate dispersion to classify each candle into {low-vol-trend, high-vol-chop, crash-panic}
- Per-regime signal:
  - Low-vol-trend: Trend-following (past returns, volume confirmation)
  - High-vol-chop: Mean-reversion (extreme candles fade)
  - Crash-panic: Defensive (flatten book, go to cash)
- Portfolio: Equal-vol weighted per coin, but net exposure scales with regime confidence (1× in low-vol, 0.5× in high-vol, 0× in panic)

**Why it's novel:** It's not a static trend+carry blend; it's an adaptive regime switch that changes BOTH signal AND risk. The deployed baseline doesn't have regime detection.

**Test first:** Simple 3-state Markov regime model on ATR; compare Sharpe vs static momentum.

---

### Approach 2: **Cross-Asset Momentum Diffusion**

**Core idea:** Leading coins (BTC, ETH) move first; laggard alts catch up with a delay. Exploit the lead-lag structure.

**Mechanism:**
- For each alt coin in top-20:
  - Compute lagged correlation with BTC/ETH returns (lags: 0, 1, 2 candles)
  - If alt positively correlated with lagged BTC/ETH → trade alt in direction of BTC/ETH prior move
  - If alt negatively correlated with lagged BTC/ETH → fade BTC/ETH prior move (trade alt opposite)
- Signal strength = correlation × prior BTC/ETH return magnitude
- Portfolio: Dollar-neutral (equal long/short notional), but not necessarily beta-neutral

**Why it's novel:** It's not a cross-sectional ranking; it's a time-series lead-lag exploit. The deployed baseline doesn't use BTC→alt diffusion.

**Test first:** 1-day lag correlation matrix; simple backtest of top-5 correlated alts.

---

### Approach 3: **Funding-Rate-Implied Carry Mean Reversion**

**Core idea:** Funding rates embed carry expectations. When funding diverges from price momentum, mean-revert the funding side.

**Mechanism:**
- For each coin, compute funding z-score (rolling mean/SD over 90 candles)
- Compute price momentum (past 5-candle return)
- Signal:
  - If funding z-score > 2 (expensive longs) AND price momentum < 0 → SHORT the coin (funding mean-reversion)
  - If funding z-score < -2 (cheap longs) AND price momentum > 0 → LONG the coin
  - Else: no position
- Portfolio: Volatility-weighted, but positions only when funding diverges from price

**Why it's novel:** It's not just "carry tilt" (long positive funding, short negative funding); it's a conditional trade that requires funding AND price to disagree. The deployed baseline has a static carry tilt.

**Test first:** Histogram of funding z-scores; Sharpe of funding-z > 2 filter.

---

### Approach 4: **Liquidity-Provision TWAP Simulation**

**Core idea:** Market makers earn bid-ask spread but take inventory risk. Can we simulate a passive liquidity-provision strategy using OHLCV?

**Mechanism:**
- Assume we provide liquidity at the open price of each candle (bid = open × (1 - spread), ask = open × (1 + spread))
- Inventory accumulated = (volume_at_bid - volume_at_ask) / total_volume × candle_range
- Signal: If inventory net-positive → we're "long the market's microstructure noise" → mean-revert (flatten)
- Portfolio: Market-neutral by construction (bid = ask)

**Why it's novel:** It's not a directional strategy; it's a microstructure simulation. The deployed baseline doesn't have any inventory-management or market-making logic.

**Test first:** Simple bid/ask at 5bp spread; compute realized PnL using candle OHLC (extreme-case where all fills happen at wicks).

---

### Approach 5: **Dynamic Factor Rotation (Momentum vs Reversal vs Carry)**

**Core idea:** No single factor works all the time. Rotate factor exposure based on recent performance.

**Mechanism:**
- Track 3 factor streams continuously:
  - Momentum: past-return-weighted portfolio
  - Reversal: negative past-return-weighted portfolio
  - Carry: funding-rate-weighted portfolio
- Each candle, compute each factor's 30-candle trailing Sharpe
- Allocate to the factor with highest trailing Sharpe (winner-takes-all) OR blend proportionally
- Portfolio: Factor-level allocation (not coin-level), then coin-level within the chosen factor

**Why it's novel:** It's not a static blend; it's dynamic factor rotation. The deployed baseline has a fixed trend+carry blend.

**Test first:** Compute 3 factor streams separately; test "momentum-last-month wins" vs equal-weight blend.

---

## NEXT STEPS

1. **Choose the most promising approach** based on:
   - Theoretical plausibility (does it make sense given crypto market structure?)
   - Data availability (do we have the required signals?)
   - Test cheaply (can we run a 1-day diagnostic in <5 min?)

2. **Run a cheap diagnostic** (same-day backtest, minimal parameters):
   - For Approach 1: Simple 3-state ATR regime detector; compare static vs regime-switch momentum
   - For Approach 2: 1-day lag correlation matrix; simple BTC→alt diffusion
   - For Approach 3: Funding z-score histogram; funding+price disagreement filter
   - For Approach 4: 5bp spread simulation using candle OHLC
   - For Approach 5: Compute 3 factor streams; test factor rotation vs static blend

3. **If diagnostic is promising** (IS Sharpe > 0.5, turnover reasonable), proceed to full EXPLORATION with proper leak-check, Critic review, etc.

4. **If diagnostic fails**, move to next approach.

---

## RECOMMENDED FIRST APPROACH

**Start with Approach 1 (Volatility Regime-Switching Momentum)** or **Approach 3 (Funding-Rate-Implied Carry Mean Reversion)**.

**Reason:**
- Approach 1: Uses only OHLCV + funding (we have it); regime-switching is a genuinely new angle; cheap to test (simple ATR threshold).
- Approach 3: Funding divergence is a strong prior; conditional funding+price disagreement is novel vs static carry tilt.

**Suggested first diagnostic:** Run a 1-day backtest of Approach 3 with parameters {funding_z_threshold=2, price_momentum_window=5}. If IS Sharpe > 0.5, proceed to full EXPLORATION.

---

**READY TO BEGIN?** Choose an approach, run the diagnostic, and report back with findings.
