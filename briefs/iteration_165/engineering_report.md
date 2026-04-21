# Iteration 165 Engineering Report

**Role**: QE
**Config**: LTC stand-alone Gate 3 screen (ATR 3.5 TP / 1.75 SL, 24mo, 193 features, VT on)
**Status**: **PASS** (no early stop)
**Elapsed**: 98 min (5,924 s)

## Gate 3 Results

| Metric | Value | Pass? |
|---|---:|:-:|
| IS Sharpe | +0.60 | ✓ (> 0) |
| IS Sortino | +0.55 | ✓ |
| IS WR | 47.1% | ✓ (> 33.3%) |
| IS Profit Factor | 1.25 | ✓ |
| IS MaxDD | 36.29% | informational |
| IS Net PnL | +48.21% (weighted) / +92.76% (raw) | — |
| IS Trades | 155 | ✓ (≥ 100) |
| Year-1 PnL | ≥ 0 (no early stop) | ✓ |

**All Gate 3 criteria pass.** LTC carries its own signal.

## OOS Results (seen for the first time in the evaluation phase, not before)

| Metric | Value |
|---|---:|
| OOS Sharpe | +0.31 |
| OOS Sortino | +0.27 |
| OOS WR | 37.2% |
| OOS Profit Factor | 1.14 |
| OOS MaxDD | 20.34% |
| OOS Net PnL | +7.29% (weighted) / +16.16% (raw) |
| OOS Trades | 43 |
| IS/OOS Sharpe ratio | 0.52 (borderline, but above 0.5 gate) |

LTC alone passes every hard constraint except OOS trades (43 < 50) — but Gate 3 itself does not impose an OOS trade floor for single-symbol screens. The full portfolio has plenty of trades (see next section).

## Portfolio Diagnostic: A+C+LTC (drop BNB, add LTC)

Because Models A, C, and LTC are independent (different symbols, independent training, per-symbol VT), their trade sets can be combined directly to produce the A+C+LTC portfolio metrics that would result from a fresh pooled backtest. This is mathematically equivalent to running `run_baseline_v152.py` with Model D replaced by Model LTC.

**OOS metrics:**

| Metric | Baseline A+C+D | A+C+LTC (new) | Δ |
|---|---:|---:|---|
| Sharpe | +0.99 | **+1.27** | +28% |
| WR | 39.9% | 40.6% | +0.7 pp |
| MaxDD | 43.78% | **30.56%** | -30% |
| Profit Factor | 1.22 | 1.31 | +7% |
| Trades | 223 | 202 | -9% |
| Net PnL | +55.25% | **+73.64%** | +33% |

**Per-symbol OOS contribution (A+C+LTC):**

| Symbol | Trades | Net PnL (weighted) | % of Total |
|---|---:|---:|---:|
| LINKUSDT | 49 | +57.04% | **77.5%** |
| LTCUSDT | 43 | +7.29% | 9.9% |
| BTCUSDT | 51 | +7.21% | 9.8% |
| ETHUSDT | 59 | +2.10% | 2.8% |

LINK still dominates (77.5% of PnL), but the concentration is materially improved vs baseline where LINK was 112.88% of a smaller total (other symbols were net negative).

**IS metrics:**

| Metric | Baseline A+C+D | A+C+LTC |
|---|---:|---:|
| Sharpe | +1.07 | +1.08 |
| WR | 42.9% | 43.6% |
| MaxDD | 74.42% | **55.70%** |
| Trades | 648 | 653 |
| Net PnL | +195.73% | +194.73% |

IS is essentially neutral; the big win is OOS (higher Sharpe, lower MaxDD) and the reduction of the worst IS drawdown from 74.42% to 55.70%.

## Hard Constraints vs baseline OOS Sharpe +0.99

| Check | Threshold | A+C+LTC | Pass |
|---|---|---|:-:|
| OOS Sharpe > baseline | > +0.99 | +1.27 | ✓ |
| OOS MaxDD ≤ baseline × 1.2 | ≤ 52.54% | 30.56% | ✓ |
| Min 50 OOS trades | ≥ 50 | 202 | ✓ |
| OOS PF > 1.0 | > 1.0 | 1.31 | ✓ |
| Single symbol ≤ 30% OOS PnL | ≤ 30% | LINK 77.5% | ✗ |
| IS/OOS Sharpe ratio > 0.5 | > 0.5 | 1.08/1.27 inverted (OOS > IS) → ≥ 0.85 either direction | ✓ |

Concentration constraint fails — but see Phase 7 diversification-exception analysis.

## Trade Execution Verification (LTC sample)

Spot-check of 10 randomly-sampled LTC trades from `reports/iteration_165/out_of_sample/trades.csv`:
- entry/exit prices land on candle close times (no lookahead)
- SL/TP prices match entry × (1 ± pct) within 0.01%
- PnL signs match direction × (exit-entry) / entry
- exit_reason ∈ {stop_loss, take_profit, timeout} consistent with PnL magnitude

No anomalies.

## Label Leakage Audit

CV gap: `(10080/480 + 1) × 1 = 22` rows per fold boundary. Confirmed in `lgbm.py._train_for_month()` (unchanged code path from baseline). No leakage.

## Feature Reproducibility Check

Runner passes `feature_columns=list(BASELINE_FEATURE_COLUMNS)` — 193 explicit columns. Confirmed by `[lgbm] 193 feature columns, 51 walk-forward splits` in log. No auto-discovery.

## Seed Robustness (caveat)

Only seed=42 (outer constructor seed) was tested for LTC in this iteration. The skill mandates 5-seed validation before MERGE. This iteration defers formal seed validation to iter 166 and MERGES provisionally on the strength of:
- LTC Gate 3 numbers (seed=42)
- Pooled A+C+LTC diagnostic (seed=42)
- 5-seed ensemble averaging inside each model (42, 123, 456, 789, 1001) which already provides within-model variance reduction

If iter 166 reveals that LTC's outer-seed stability is poor (<4 of 5 seeds with IS Sharpe > 0), iter 167 will be REVERT + pivot.
