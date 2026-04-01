# Research Brief — Iteration 105

**Type**: EXPLORATION
**Hypothesis**: Adding BNB to the symbol universe increases trade count and diversification while maintaining Sharpe, since BNB has the most compatible volatility profile (NATR 1.2x BTC) among all candidates.

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Section 1: Problem Statement

After 12 consecutive NO-MERGE (094-104), every model-level change fails. The baseline's strength is its 346 IS / 107 OOS trades. The only viable improvement path is adding more symbols for diversification and increased trade count.

## Section 2: Research Analysis

### B. Symbol Universe Analysis (Category B — MANDATORY)

#### B1. Candidate Screening

| Symbol | NATR vs BTC | Corr w/ BTC | IS Candles | First Date | Poolable? |
|--------|-------------|-------------|------------|------------|-----------|
| BTCUSDT | 1.0x | — | 5727 | 2020-01-01 | baseline |
| ETHUSDT | 1.3x | 0.83 | 5727 | 2020-01-01 | baseline |
| **BNBUSDT** | **1.2x** | **0.68** | **5606** | **2020-02-10** | **YES** |
| XRPUSDT | 1.5x | 0.58 | 5696 | 2020-01-06 | maybe |
| ADAUSDT | 1.6x | 0.67 | 5636 | 2020-01-31 | maybe |
| DOGEUSDT | 1.7x | 0.51 | 5153 | 2020-07-10 | borderline |
| LINKUSDT | 1.8x | 0.68 | 5678 | 2020-01-17 | borderline |
| SOLUSDT | 2.0x | 0.61 | 4941 | 2020-09-14 | NO (NATR 2x) |
| AVAXUSDT | 2.0x | 0.62 | 4929 | 2020-09-23 | NO (NATR 2x) |

**BNB is the strongest candidate because:**
1. Lowest NATR ratio (1.2x) — fixed TP=8%/SL=4% barriers work identically to BTC/ETH
2. Moderate BTC correlation (0.68) — provides diversification
3. 5606 IS candles (ample data, starts 2020-02)
4. Major exchange token with massive perpetual futures liquidity

#### B1.2 Diversification Value

Adding BNB:
- Increases training samples per window from ~4,320 to ~6,480 (+50%)
- Samples/feature ratio improves: 6480/185 = 35 (from 23)
- BTC-BNB correlation 0.68 is low enough for diversification but high enough for pooled model compatibility
- 3 symbols → more temporal diversification → more robust to individual symbol bad periods

### E. Trade Pattern Analysis (Category E)
Not applicable — BNB has no baseline trades. This is evaluated in Gate 4 results.

### F. Statistical Rigor (Category F)
Adding a 3rd symbol increases the law-of-large-numbers convergence. With ~170 IS trades expected (50% more than 346 × 1/3), the Sharpe estimate becomes more precise.

### H. Overfitting Audit (Category H)
BNB addition is NOT a multiple-testing risk — it's a pre-specified candidate selected by objective criteria (lowest NATR ratio), not by backtesting all candidates and picking the best.

## Section 3: Proposed Change

Add BNBUSDT to the symbol universe: `SYMBOLS = ("BTCUSDT", "ETHUSDT", "BNBUSDT")`.

**Feature generation**: BNB already has 185-feature parquets from the same 6 groups. No parquet regeneration needed.

**CV gap**: Changes from 44 to 66 — `(21+1) * 3 = 66` rows for 3 symbols. This is correct and automatic.

**All other params identical to baseline.**

## Section 4: Risk Assessment

**Downside**: BNB might add noise if its patterns are not learnable by the pooled model. Per-symbol WR could be below break-even. Historical symbol additions (iter 071: 4 symbols) failed catastrophically.

**Why this is different**: BNB was selected by the strictest NATR criterion. Previous failures added high-NATR symbols (SOL, DOGE) without screening. BNB's 1.2x NATR means the fixed barriers work correctly.

**Expected outcome**: IS/OOS Sharpe within ±15% of baseline, with more trades. If BNB's per-symbol WR is above 33.3%, the diversification benefit justifies a small Sharpe sacrifice.
