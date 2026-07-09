# ORCHESTRATOR BRIEF — Baseline-Blind Top-20 Portfolio Exploration

**MISSION:** Invent NOVEL top-20 (ex-stablecoin) crypto perpetual-futures L/S strategies from FIRST PRINCIPLES. 

**CRITICAL CONSTRAINT:** You are BASELINE-BLINDED. Do NOT read, reference, or copy ANY idea from the existing deployed strategy (trend+carry, hysteresis bands, eligibility-exit, carry tilt, funding flows, etc.). You must NOT look at `BASELINE_PORTFOLIO.md` — it does not exist for you. Think like a researcher who has NEVER seen this book before. Be creative.

**HARD CONSTRAINTS (non-negotiable):**
1. **No cheating / no look-ahead bias:** All walk-forward parameters calibrated on in-sample (IS) data only. OOS revealed ONLY at CONFIRMATION, never before.
2. **Sharpe is the metric:** Maximize risk-adjusted return (Sharpe ratio), NOT absolute return, NOT buy-and-hold comparisons.
3. **Robust to market conditions:** Strategy should perform across regimes (trend, chop, vol spikes). Avoid overfitting to a single regime.
4. **Respect OOS_CUTOFF:** Out-of-sample cutoff date = **2025-03-24** (immutable). Data before this date = IS; data after = OOS (sealed until CONFIRMATION).
5. **Always refresh top-20 list:** Universe = top 20 coins by open interest (ex-stablecoins) on Binance Futures. Re-rank dynamically (no static set).
6. **Long/short portfolio:** Net positions can be long or short per-coin; overall book can be net-long, net-short, or market-neutral.

**DATA AVAILABLE (assessed per worktree):**
- 8h OHLCV (open, high, low, close, volume, taker_buy_volume) for ~667 coins → 2026-07-08
- Funding rates (8h) for ~644 coins → 2026-07-08
- Top-20 by open interest: recompute dynamically per candle
- **NOT available:** OI history (Binance keeps ~30d), spot prices, options/IV, liquidations, positioning data

**VALIDATION FRAMEWORK (use `portfolio-iteration` skill):**
- Full agent team: quant-researcher → quant-engineer → risk-engineer → quant-critic
- EXPLORATION phase: Invent and test ideas IS-only (OOS sealed)
- CONFIRMATION phase: ONE OOS reveal per candidate; pre-registered gates; frozen interpretation map
- Mandatory Critic leak-check with positive controls (detect lookahead bias)
- Pre-registration discipline: brief committed BEFORE any run; frozen interpretation maps; no post-hoc tuning

**OUTPUT:** A deployable top-20 L/S strategy that:
- Clears IS Sharpe > 1.0 (suggested floor; not absolute)
- Survives OOS CONFIRMATION (Sharpe > 0.5 suggested, maxDD < −35%)
- Is genuinely novel (not trend+carry with different knobs)
- Is walk-forward (no regime-specific tuning)

**CADENCE:** This may be a LONG-RUN task. Iterate through ideas systematically. Report back after each EXPLORATION with findings. Plan before long backtests.

**NAMESPACE:** 
- Analysis scripts: `analysis/portfolio/blind_*.py` (NEW namespace, NOT `top20_*`)
- Diary: `diary-portfolio-blind/` (NEW diary, NOT `diary-portfolio-top20/`)

**STARTING POINT:** 
1. First, write a PLAN.md in `diary-portfolio-blind/` with 3-5 novel approach sketches (NOT trend+carry, NOT funding-flow tilt, NOT beta-hedging). Think from first principles: microstructure, regime switches, cross-asset patterns, behavioral biases, volatility dynamics, liquidity provision, etc.
2. Run a cheap diagnostic on the most promising sketch (same-day backtest, minimal parameters).
3. Report back with findings; proceed to full EXPLORATION if promising.

**GO BE CREATIVE.** The OHLCV+funding cross-sectional well is NOT exhausted if you think beyond the existing patterns. The prior complement work was anchored to "decorrelate from v3" — you are NOT. You can rediscover similar mechanisms if they're genuinely robust, but aim for genuinely new angles.

---

**QUESTIONS?** If you need clarification on any constraint, ask BEFORE proceeding.

**READY?** Write PLAN.md and begin.
