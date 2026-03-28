# Research Brief — Iteration 063

**Type**: EXPLORATION (dynamic TP/SL via ATR)
**Date**: 2026-03-28

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Hypothesis

Replace fixed TP=8%/SL=4% execution barriers with ATR-scaled barriers: TP = 2.9 × NATR_21, SL = 1.45 × NATR_21. This adapts to volatility — tighter in calm markets (2023: 5.4%/2.7%), wider in volatile (2021: 11.6%/5.8%).

IS NATR analysis shows year-by-year variation from 1.85% (BTC 2023) to 5.00% (ETH 2021). Fixed 8%/4% barriers are only optimal for the IS mean volatility. OOS NATR is even lower (BTC 1.84%) — fixed barriers are too wide.

## Research Analysis (2 Categories: A, E)

### A. Feature/Model Analysis

- Same 106 features, same classification model
- Labeling unchanged (fixed 8%/4%) — model learns directional signal
- Execution adapts: barriers scale with current NATR_21
- Multipliers K_tp=2.9, K_sl=1.45 calibrated to match baseline mean barriers

### E. Trade Pattern Analysis (from IS data)

Year-by-year equivalent barriers under ATR scaling:
- 2020: BTC 8.1%/4.1%, ETH 8.9%/4.4% — close to baseline
- 2021: BTC 11.6%/5.8%, ETH 11.2%/5.6% — wider (volatile bull)
- 2022: BTC 8.3%/4.1%, ETH 8.7%/4.4% — close to baseline
- 2023: BTC 5.4%/2.7%, ETH 4.7%/2.3% — much tighter (calm)
- 2024: BTC 6.8%/3.4%, ETH 6.4%/3.2% — moderately tighter

Expected impact: more TP hits in calm periods (2023-2024) where fixed barriers were too wide to reach.

## Design Specification

- Execution: TP = 2.9 × NATR_21, SL = 1.45 × NATR_21 (per-candle)
- Labeling: fixed 8%/4% (unchanged — model learns from fixed barriers)
- Signal carries dynamic tp_pct/sl_pct via extended Signal dataclass
- Backtest uses Signal overrides when present
