# Iteration 108 Diary

**Date**: 2026-04-01
**Type**: EXPLORATION
**Merge Decision**: NO-MERGE (EARLY STOP — Year 2023: PnL=-69.7%, WR=32.9%, 82 trades)

**OOS cutoff**: 2025-03-24

## Hypothesis

Build a dedicated meme coin model (DOGE + SHIB) with curated 42-feature set and dynamic ATR labeling. Goal: find profitable meme signal for later combination with BTC+ETH baseline.

## What Changed

1. **Meme-only universe**: DOGEUSDT + 1000SHIBUSDT (no BTC/ETH)
2. **Dynamic ATR labeling**: Label barriers = 2.9x/1.45x NATR per candle (aligns with execution)
3. **42 curated features**: Volume (12), Volatility (8), Mean Reversion (8), Momentum (8), Statistical (4), Trend (2). All scale-invariant.
4. **Feature ratio**: 4,400/42 = 104.8 (vs baseline 4,400/185 = 23.8)

## Results

| Metric | Iter 108 | Notes |
|--------|---------|-------|
| IS Sharpe | +0.10 | Marginally positive |
| IS WR | 38.6% | Above break-even (33.3%) |
| IS PF | 1.03 | Barely profitable |
| IS MaxDD | 108.6% | Catastrophic |
| IS Trades | 114 | Adequate |
| OOS | — | Never reached (early stop) |

### Per-Symbol IS Performance

| Symbol | Trades | WR | Net PnL | % of Total |
|--------|--------|----|---------|------------|
| DOGEUSDT | 55 | 34.5% | +20.3% | 180.6% |
| 1000SHIBUSDT | 59 | 42.4% | -9.1% | -80.6% |

DOGE is **profitable** (WR 34.5% with large TP trades). SHIB is **losing** despite higher WR (42.4%) because dynamic ATR barriers create asymmetric PnL — SHIB's high-volatility SL losses exceed its TP gains.

### Monthly PnL Breakdown

| Period | PnL | Trades | Key Event |
|--------|-----|--------|-----------|
| 2022-H2 | +85.6% | 31 | FTX crash shorts: +88% in Nov alone |
| 2023-Q1 | -23.5% | 36 | Feb -43.3% (post-crash whipsaw) |
| 2023-Q2 | +15.1% | 14 | Brief recovery |
| 2023-Q3 | -28.9% | 11 | Choppy meme market |
| 2023-Q4 | -32.4% | 21 | Dec -31.0% (year-end dump) |

Without Nov 2022 (+88.1%), the strategy PnL is -76.8%. **The entire profitability depends on one month.**

## Key Insights

### 1. Dynamic ATR Labeling Works Mechanically
Barriers scaled correctly: DOGE avg TP=10-14%, SL=5-7% (vs fixed 8%/4%). Labels are meaningful for meme coin volatility. The implementation in `lgbm.py` is sound.

### 2. Curated 42 Features Is The Right Approach
Ratio 104.8 is healthy. The model ran without overfitting symptoms from feature count. This validates the pruning approach.

### 3. DOGE Has Signal, SHIB Does Not
DOGE: profitable across the IS period (WR 34.5%, +20.3%).
SHIB: higher WR but negative PnL. With dynamic barriers, SHIB's wider SL during high-vol periods destroys profits. This suggests SHIB needs different barrier multipliers or a per-symbol model.

### 4. Meme Coins Are Crash-Dependent
88% of IS profit came from Nov 2022 (FTX collapse). The model excels at shorting during crashes but loses during sideways/choppy periods (all of 2023). This is not a robust edge — it's event-dependent.

### 5. Year 2023 Is Structurally Hard for Meme Coins
Meme coins had low volatility and no clear trends in 2023. The model generated 82 trades but only 32.9% won. This suggests the features (mean reversion, momentum) don't capture the choppy meme dynamics of 2023.

## Trade Execution Verification

Sampled 10 trades from trades.csv:
- Entry prices match close of signal candle ✓
- SL/TP prices scale with NATR (vary per trade) ✓
- Timeout = 7 days ✓
- PnL calculations correct ✓
- CV gap = 44 rows (correct for 2 symbols) ✓

## Exploration/Exploitation Tracker

Last 10 (iters 099-108): [E, E, X, E, E, E, E, E, E, **E**]
Exploration rate: 9/10 = 90%. Type: **EXPLORATION** (meme coin dedicated model)

## Research Checklist Categories Completed

- **A (Features)**: Pruned from 189 to 42 curated scale-invariant features. All grouped by meme-relevant category.
- **B (Symbols)**: DOGE+SHIB screened. Gates 1-2 passed. Gate 3 partial (DOGE profitable, SHIB not). Gate 4 N/A (separate model).
- **C (Labeling)**: Dynamic ATR labeling implemented and verified. Barriers appropriate for meme volatility.
- **F (Statistical)**: 42 features with 4,400 samples = ratio 104.8.

## lgbm.py Code Review

New `use_atr_labeling` parameter and `_load_atr_for_master()` method work correctly. Vectorized searchsorted approach for loading NATR values is efficient. No bugs found. The label_trades call correctly switches between fixed and ATR-based barriers.

## Gap Analysis

WR is 38.6% (IS overall), break-even is 33.3% for 2:1 RR. Gap: +5.3pp above break-even. But with dynamic barriers, the effective RR varies, making this comparison imprecise. The real issue is concentration risk (Nov 2022 = 88% of profit) and lack of edge in choppy markets.

## Next Iteration Ideas

1. **EXPLOITATION: DOGE-only model.** Remove SHIB (which loses money). Run DOGE solo with same 42 features. With ~2,200 training samples and 42 features, ratio = 52.4 (still acceptable). This directly addresses the SHIB drag.

2. **EXPLORATION: Regime filter.** Add a volatility regime filter: only trade when NATR > threshold (high-vol periods). The model clearly profits during crashes but loses in sideways. A regime gate would skip 2023-style choppy markets entirely, reducing trade count but improving WR.

3. **EXPLORATION: Asymmetric barriers per symbol.** SHIB's failure with 2.9x/1.45x multipliers suggests meme coins need different TP/SL ratios. Try wider multipliers for SHIB (3.5x/1.75x) or switch to per-symbol barrier optimization.

4. **EXPLORATION: Short-only model.** The strategy's profits come almost entirely from shorting during crashes. A short-only model (or heavily short-biased) might capture the meme coin crash dynamics more reliably.
