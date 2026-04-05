# Iteration 142 Engineering Report

**Role**: QE
**Config**: Standalone screening — AVAX, ATOM, DOGE (each with ATR 3.5×/1.75× template)

## Screening Results

### AVAX

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | **-0.03** | +2.02 |
| WR | 45.5% | 53.8% |
| PF | 0.99 | 2.55 |
| MaxDD | 137.5% | 31.8% |
| Trades | 132 | 26 |

**Gate 3: FAIL** (IS Sharpe < 0). OOS looks strong but only 26 trades — too thin to trust. The OOS/IS Sharpe ratio of -70 is a red flag suggesting IS/OOS regime divergence.

### ATOM

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | **+0.93** | +0.03 |
| WR | 44.0% | 43.1% |
| PF | 1.35 | 1.01 |
| MaxDD | 86.7% | 78.8% |
| Trades | 168 | 58 |

**Gate 3: PASS but MARGINAL OOS**. Strongest IS signal of any standalone symbol screened (+0.93 vs LINK +0.45, BNB +0.51), but OOS collapses to +0.03. Classic IS/OOS divergence — the strategy may be overfitting to IS regime, or 2025 is simply a flat period for ATOM.

### DOGE

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | **+0.32** | **+1.24** |
| WR | 48.3% | 52.0% |
| PF | 1.12 | 1.46 |
| MaxDD | 88.8% | **30.0%** |
| Trades | 120 | 50 |

**Gate 3: STRONG PASS**. OOS Sharpe +1.24 is the strongest OOS of any alt screened (beats LINK +1.20, BNB +1.04). 50 OOS trades hits threshold exactly. OOS WR 52.0% above break-even. OOS MaxDD only 30% (excellent). OOS/IS ratio 3.90 is unusual but healthy.

## Updated Scorecard (10 symbols tested)

| Symbol | Config | IS Sharpe | OOS Sharpe | OOS Trades | Verdict |
|--------|--------|-----------|------------|------------|---------|
| **LINK** (Model C) | 3.5x/1.75x | +0.45 | +1.20 | 42 | IN PORTFOLIO |
| **BNB** (Model D) | 3.5x/1.75x | +0.51 | +1.04 | 50 | IN PORTFOLIO |
| **DOGE** (Model E?) | 3.5x/1.75x | **+0.32** | **+1.24** | **50** | **STRONG PASS** |
| ATOM | 3.5x/1.75x | +0.93 | +0.03 | 58 | MARGINAL |
| SOL | 3.5x/1.75x | +0.16 | +0.47 | 32 | MARGINAL |
| DOT | 3.5x/1.75x | -0.02 | +1.10 | 47 | FAIL (IS flat) |
| XRP | 3.5x/1.75x | -0.03 | +2.03 | 22 | FAIL (IS flat) |
| ADA | 3.5x/1.75x | -0.73 | +0.31 | 47 | FAIL |
| AVAX | 3.5x/1.75x | -0.03 | +2.02 | 26 | FAIL (IS flat, thin OOS) |
| ETH | 2.9x/1.45x | -0.46 | -0.63 | 51 | FAIL |
| BTC | 3.5x/1.75x | -0.90 | -1.41 | 50 | FAIL |

## Label Leakage Audit

- CV gap = 22 (22 candles × 1 symbol) for each standalone run. Verified correct.
- Walk-forward training uses only prior-window data. Verified.

## Trade Execution Verification

Sampled 10 DOGE trades. Entry prices match signal candle closes. ATR-scaled barriers verified. PnL calculations consistent.

## Runtime

- AVAX: 5,994s (~100 min)
- ATOM: 6,108s (~102 min)
- DOGE: 5,560s (~93 min)
- **Total: ~295 min (~5 hours)**

## Recommendation

DOGE is the strongest Model E candidate. Next iteration (143) should run the full A+C+D+E portfolio (BTC/ETH + LINK + BNB + DOGE) to validate DOGE's contribution to overall Sharpe.
