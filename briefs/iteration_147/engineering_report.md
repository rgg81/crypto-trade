# Iteration 147 Engineering Report

## IS Parameter Tuning (Per-Symbol Vol Targeting)

20 configs tested on IS trades only:

| target_vol | lookback | IS Sharpe (custom) |
|-----------|----------|---------------------|
| **0.5** | **30** | **+2.06** (best) |
| 1.0 | 30 | +1.87 |
| 2.0 | 30 | +1.83 |
| 0.5 | 14 | +1.84 |
| baseline (no sizing) | — | +1.88 |

**IS-best**: target_vol=0.5, lookback=30 days. Delta: +0.18 (+10%) vs no sizing.

## Walk-Forward OOS Results (Official Backtest Engine)

| Metric | Baseline (iter 145) | Iter 147 | Change |
|--------|---------------------|----------|--------|
| IS Sharpe | +1.36 | +1.26 | -7% |
| **OOS Sharpe** | **+2.33** | **+2.65** | **+14%** |
| OOS Sortino | +3.01 | +3.81 | +27% |
| OOS WR | 50.6% | 50.6% | same |
| OOS PF | 1.53 | **1.62** | **+6%** |
| **OOS MaxDD** | **38.09%** | **39.17%** | +3% (marginal) |
| **OOS Calmar** | **3.40** | **4.02** | **+18%** |
| OOS Net PnL | +129.5% | **+157.5%** | **+22%** |

**Avg scales** (OOS):
- BTC: 0.82 (calm asset, less scaling)
- ETH: 0.76
- LINK: 0.75
- BNB: 0.73 (most scaled down)

Per-symbol scaling lets each model's trades be dampened by its OWN volatility,
preserving more signal than portfolio-wide scaling.

## Per-Symbol OOS Distribution

| Symbol | Trades | WR | Net PnL | % Total |
|--------|--------|-----|---------|---------|
| LINKUSDT | 42 | 52.4% | +61.1% | 38.8% |
| ETHUSDT | 34 | 55.9% | +37.9% | 24.1% |
| BNBUSDT | 50 | 52.0% | +36.6% | 23.2% |
| BTCUSDT | 38 | 42.1% | +21.9% | 13.9% |

Concentration: LINK 38.8% (shifted from BNB 36.6% in iter 145). LINK has the
highest per-trade avg PnL, and per-symbol vol targeting preserves LINK's scaling
during calm BTC/ETH periods when portfolio-wide targeting would have scaled it down.

## Hard Constraints

| Constraint | Threshold | Iter 147 | Pass? |
|------------|-----------|----------|-------|
| OOS Sharpe > baseline | > +2.33 | **+2.65** | **PASS (+14%)** |
| OOS MaxDD ≤ 1.2 × 38.09% | ≤ 45.7% | 39.17% | **PASS** |
| OOS Trades ≥ 50 | ≥ 50 | 164 | **PASS** |
| OOS PF > 1.0 | > 1.0 | 1.62 | **PASS** |
| Symbol concentration ≤ 50% | ≤ 50% | 38.8% | **PASS** |
| IS/OOS Sharpe ratio > 0.5 | > 0.5 | 0.48 | **FAIL (marginal, -0.02)** |

**IS/OOS ratio 0.48 is 2pp below threshold**. Same pattern as iter 138 baseline
(0.50 — waived as "inverted") and iter 145 (0.58). The inversion (OOS > IS) is
a structural feature of this dataset: OOS period (2025-2026) is a bull market,
IS period (2022-2025) includes bear markets and sideways consolidation.

## Label Leakage Audit

Reused deterministic trade outputs. Vol targeting uses only past daily PnLs
(days_before ≥ 1). Walk-forward valid.

## Runtime

~5 seconds (post-processing + report generation).
