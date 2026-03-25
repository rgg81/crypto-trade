# Phase 3: Symbol Universe Selection — Iteration 001

## Options Evaluated

### 1. Per-Symbol Models

- With 8h candles, each symbol has ~1095 candles/year
- After 12-month training window, first test month has ~1095 training samples
- After labeling + feature NaN rows, likely ~800-900 usable samples
- Optuna with 50 trials × 5 CV folds = 250 model fits per month, per symbol
- **Infeasible**: insufficient data for meaningful optimization, and O(symbols × months) computational cost

### 2. Cluster-Based (one model per sector/correlation cluster)

- Cross-symbol correlation analysis shows mean pairwise correlation of 0.60
- Minimum pair correlation is 0.13 (DOGE vs AXSUSDT) — still positive
- Natural clusters exist (e.g., SAND/MANA at 0.82, ARB/OP at 0.81)
- However, cluster boundaries are unstable across regimes (correlation rises from 0.55 to 0.69 between quiet and volatile periods)
- Would require re-clustering or fixed cluster assignments, adding complexity without clear benefit for iteration 001

### 3. Liquidity-Tiered (separate models for high/mid/low volume)

- Volume distribution is highly skewed (BTC 4.3B vs median 15M)
- Different volatility profiles by tier (BTC std 1.9% vs mid-cap 3-5%)
- Could help, but splits the training data — reducing sample size per model
- Worth exploring in future iterations, not for iteration 001

### 4. All Eligible Symbols, Pooled Model ← Selected

- 184 active USDT symbols (excluding BUSD/SETTLED) with start before 2023-07
- Pooled model gets ~184 × 1095 = ~200K candles/year of training data
- Model learns cross-symbol patterns (momentum regimes, volatility clustering)
- High correlation (0.60 mean) means shared dynamics dominate — pooling captures this
- Symbol identity is NOT a feature (model must generalize across symbols)

## Decision: Pooled Model on All Eligible USDT Symbols

### Selection Criteria

A symbol is included if ALL of:

1. **Quote currency**: Ends with USDT (excludes BUSD, USDC pairs which are duplicates)
2. **Not settled**: Does not contain "SETTLED" (contract rollovers)
3. **Minimum IS history**: At least 1095 candles (1 year) in IS period — ensures enough data to contribute meaningfully to training
4. **Start date**: First candle before 2023-07-01 — ensures the symbol has data spanning at least 20 months of IS period, giving 8+ months of walk-forward test coverage

### Expected Universe Size

- ~184 symbols meeting all criteria
- Includes ~26 delisted USDT symbols with sufficient history (avoids survivorship bias)
- The walk-forward approach handles symbols entering/exiting naturally: a symbol only contributes to training months where it has data

### Future Iteration Ideas

- Tier-specific models (top 50 by volume vs rest) if the pooled model shows inconsistent per-symbol performance
- Cluster-based if per-regime analysis reveals clear sub-populations
