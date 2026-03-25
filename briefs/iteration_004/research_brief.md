# Research Brief: 8H LightGBM Iteration 004

## 0. Data Split & Backtest Approach

- OOS cutoff date: 2025-03-24 (project-level constant, applies to all iterations)
- The researcher used ONLY IS data (before 2025-03-24) for all design decisions below
- The walk-forward backtest runs on the FULL dataset (IS + OOS) as one continuous process
- Monthly retraining with timeseries CV, 12-month minimum training window (unchanged)
- The report layer splits backtest results at OOS_CUTOFF_DATE into two report batches

## 1. Change from Iteration 002 (current baseline)

**Single variable change: reduce symbol universe from 201 to top 50 by IS quote volume.**

### Problem

Win rate is stuck at ~31% across 3 iterations. The pooled model trains on 201 symbols with widely varying liquidity ($37M to $4.3B per 8h candle). Low-liquidity symbols have noisier price action and may dilute the model's ability to learn patterns present in liquid markets.

### Decision

Use only the top 50 symbols by average IS-period quote volume. All have >$37M per 8h candle. This:
- Focuses the model on the most liquid, best-quality data
- Reduces training set noise from illiquid mid/small-caps
- Cuts compute time ~4x (50 vs 201 symbols)

### Top 50 Selection

Ranked by mean quote_volume in IS period. Includes: BTC, ETH, SOL, XRP, DOGE, 1000PEPE, LUNA, BNB, 1000SHIB, ADA, SUI, MATIC, GMT, AVAX, LINK, LTC, DOT, APT, ARB, ETC, FTM, APE, GALA, SAND, FIL, OP, BCH, NEAR, AXS, EOS, MANA, DYDX, CFX, ATOM, PEOPLE, INJ, AAVE, UNI, 1000FLOKI, CRV, FET, CHZ, TRX, TRB, STX, RNDR, MASK, XLM, LDO, WAVES.

## 2. Everything Else Unchanged

All 185 features, TP=4%/SL=2%, confidence threshold 0.50–0.65, monthly walk-forward, 50 Optuna trials, seed 42.

## 3. Implementation

Pass a `min_quote_volume` or explicit symbol list to the runner script. The `select_symbols()` function already works; just take the top 50 from the ranked list.
