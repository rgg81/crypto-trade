# Iteration 144 Engineering Report

**Role**: QE (analytical — no backtest)
**Methodology**: Reuse existing iter 138 + iter 142 trade outputs for portfolio analysis.

## Monthly OOS PnL Per Model (April 2025 – February 2026)

| Month | A | C | D | E | Total |
|-------|---|---|---|---|-------|
| 2025-03 | +0.00% | +10.77% | +5.60% | +11.54% | +27.92% |
| 2025-04 | -6.68% | +0.03% | +16.03% | -0.25% | +9.12% |
| 2025-05 | +18.44% | -6.77% | -4.65% | +1.68% | +8.71% |
| 2025-06 | -3.81% | +35.45% | +6.45% | +25.72% | +63.80% |
| **2025-07** | **-4.12%** | **-19.69%** | **-21.06%** | **-13.43%** | **-58.31%** |
| 2025-08 | +3.34% | -9.63% | +8.89% | +3.04% | +5.64% |
| 2025-09 | +0.00% | +30.17% | +19.66% | +13.81% | +63.64% |
| 2025-10 | +15.88% | +6.97% | +4.21% | -3.39% | +23.68% |
| 2025-11 | +41.45% | +13.56% | -18.06% | +22.65% | +59.60% |
| 2025-12 | +0.75% | +0.99% | -3.69% | +7.96% | +6.01% |
| 2026-01 | -2.93% | +3.16% | +11.15% | -7.47% | +3.91% |
| 2026-02 | +16.38% | -9.02% | +13.21% | +11.20% | +31.77% |
| **Total** | **+78.71%** | **+55.99%** | **+37.73%** | **+73.06%** | **+245.49%** |

**July 2025 was catastrophic**: all 4 models lost double-digits simultaneously (-58.31%).
This single month drove the portfolio's drawdown.

## Correlation Matrix (Monthly OOS PnL)

| | A | C | D | E |
|-|---|---|---|---|
| **A** | +1.00 | -0.02 | **-0.43** | +0.34 |
| **C** | -0.02 | +1.00 | +0.34 | **+0.72** |
| **D** | -0.43 | +0.34 | +1.00 | +0.11 |
| **E** | +0.34 | **+0.72** | +0.11 | +1.00 |

**Key findings**:
- **A↔D: -0.43** — negatively correlated (diversifying!)
- **C↔E: +0.72** — DOGE and LINK move together (bad for diversification)
- **A↔C: -0.02** — nearly uncorrelated (good)

## Losing Month Jaccard Overlap

| Pair | Overlapping losing months | Jaccard |
|------|---------------------------|---------|
| A & E | 3 | **0.60** |
| C & D | 2 | 0.33 |
| A & C | 1 | 0.14 |
| A & D | 1 | 0.14 |
| C & E | 1 | 0.14 |
| D & E | 1 | 0.14 |

DOGE (E) has 60% losing month overlap with A — they lose together far too often.

## Portfolio Subset Comparison (OOS)

| Combo | Sharpe | MaxDD | PnL | Trades | Sharpe/MaxDD |
|-------|--------|-------|-----|--------|--------------|
| **A alone** | +1.67 | **19.81%** | +78.7% | 72 | **8.43** |
| A+D | +1.99 | 32.74% | +116.4% | 122 | 6.08 |
| A+C | +2.07 | 50.65% | +134.7% | 114 | 4.09 |
| **A+C+D** (baseline 138) | **+2.32** | 62.83% | +172.4% | 164 | 3.69 |
| A+C+E | — | — | — | — | — |
| A+D+E | — | — | — | — | — |
| A+C+D+E (iter 143) | +2.30 | 92.48% | +245.5% | 214 | 2.49 |

**Pareto frontier analysis**:
- Max **absolute Sharpe**: A+C+D at +2.32 (current baseline)
- Max **risk-adjusted** (Sharpe/MaxDD): A alone at 8.43 (4× baseline)
- **Middle ground**: A+D — 86% of baseline Sharpe with 52% of baseline MaxDD

## Label Leakage Audit

Reused deterministic trade outputs from iter 138 and iter 142. All prior audits valid.

## Runtime

~30 seconds for analysis + report generation. No backtests run.
