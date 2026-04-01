# Iteration 108 Research Brief

**Type**: EXPLORATION
**Date**: 2026-04-01
**Theme**: Dynamic ATR labeling + DOGE expansion

## Section 0: Data Split

- OOS cutoff: `2025-03-24` (fixed, never changes)
- IS period: all data before 2025-03-24
- OOS period: all data from 2025-03-24 onward
- Walk-forward runs on ALL data; reports split at cutoff

## Problem Statement

The baseline (iter 093) uses FIXED labeling barriers (TP=8%, SL=4%) but DYNAMIC execution barriers (ATR-scaled: TP=2.9xNATR, SL=1.45xNATR). This creates a label-execution mismatch:

| Symbol | NATR | Execution TP | Execution SL | Label TP | Label SL | Mismatch |
|--------|------|-------------|-------------|----------|----------|----------|
| BTC    | 2.76%| ~8.0%       | ~4.0%       | 8.0%     | 4.0%     | ~0%      |
| ETH    | 3.57%| ~10.4%      | ~5.2%       | 8.0%     | 4.0%     | 30%      |
| DOGE   | 5.02%| ~14.6%      | ~7.3%       | 8.0%     | 4.0%     | 81%      |

The model optimizes for predicting 8%/4% outcomes, but executes with different barriers. For BTC the mismatch is negligible. For ETH it's moderate. For DOGE it's catastrophic — 81% of candles hit the 8% barrier within 7 days (vs 56% for BTC), making labels trivially easy but meaningless for execution.

This mismatch is the ROOT CAUSE why symbol expansion has failed. Iter 105 added BNB with the same fixed labeling — BNB's labels were noise because 8%/4% barriers are too tight for a 3.5% NATR asset.

## Proposed Change: Dynamic ATR Labeling

Align labeling barriers with execution barriers by passing per-candle ATR values to `label_trades()`. The infrastructure already exists — `label_trades` accepts an `atr_values` parameter.

When `atr_values` is provided:
- `label_tp_pct` → ATR multiplier (2.9)
- `label_sl_pct` → ATR multiplier (1.45)
- Per-candle: `tp_dist = atr_price × 2.9`, `sl_dist = atr_price × 1.45`

This means:
- BTC low-vol (NATR 1.5%): TP=4.35%, SL=2.18% (tighter barriers for quiet markets)
- BTC high-vol (NATR 5%): TP=14.5%, SL=7.25% (wider barriers for volatile markets)
- DOGE average (NATR 5%): TP=14.5%, SL=7.25% (appropriate for its volatility)

Labels adapt to market conditions AND symbol characteristics. The model learns to predict "which direction will the market move by a meaningful amount" instead of "which direction will the market move by a fixed 8%."

## Secondary Change: Add DOGEUSDT to Pool

With dynamic labeling fixing the barrier mismatch, add DOGE to the pooled model:
- **Symbols**: BTCUSDT + ETHUSDT + DOGEUSDT (3-symbol pool)
- **Samples**: ~6,480 per 24-month training window (was ~4,400)
- **Ratio**: 6480/189 = 34.3 samples/feature (improved from 23.8)
- **CV gap**: 66 rows (was 44) — 50% increase in wasted data per fold

## Research Analysis

### Category A: Feature Analysis

Feature-target rank correlation (Spearman) with 21-candle forward return (IS only):

| Symbol | Features with |corr|>0.05, p<0.01 | Top feature | Top |corr| |
|--------|-------------------------------------------|-----------------------------|------------|
| DOGE   | 35/189                                    | vol_obv (-0.22)             | 0.221      |
| SHIB   | 65/189                                    | trend_ema_100 (-0.24)       | 0.244      |
| BTC    | 44/189                                    | vol_vwap (-0.16)            | 0.159      |

DOGE has moderate feature-target signal (35 significant features). Top features are price-level (EMA, SMA, VWAP, ATR) which reflect mean-reversion: when prices are high, forward returns tend negative. These features work for per-symbol or per-candle prediction but are scale-dependent.

**Feature intersection**: Perfect — all 4 symbols have identical 189 features. No features lost by pooling.

### Category B: Symbol Universe Screening

#### B1: Correlation & NATR

| Pair | Return Corr | NATR Ratio | Rolling Corr Std |
|------|-------------|------------|------------------|
| ETH-BTC  | 0.851  | 1.30x      | 0.060           |
| DOGE-BTC | 0.663  | 1.82x      | 0.103           |
| SHIB-BTC | 0.540  | 1.82x      | 0.143           |
| DOGE-SHIB| 0.636  | 1.00x      | —               |

DOGE-BTC correlation 0.66 is moderate — genuine diversification potential. Rolling stability (std=0.103) is acceptable.

**Regime-dependent**: During high-vol (BTC NATR > median):
- DOGE-BTC: 0.72 (vs 0.42 in low-vol) — correlation rises +0.30 in crises
- SHIB-BTC: 0.60 (vs 0.31 in low-vol) — correlation rises +0.29

Diversification benefit weakens during crises but persists (DOGE stays < 0.75 even in high-vol).

**Lead-lag**: No significant lead-lag between BTC and DOGE/SHIB. All correlation at lag 0. Cross-asset features (xbtc_return) will NOT provide predictive value for DOGE.

#### B2: Gate Results

| Gate | DOGE | SHIB |
|------|------|------|
| 1. Data quality (>1,095 IS candles) | PASS (5,153) | PASS (4,240) |
| 2. Liquidity (>$10M/day) | PASS ($970M) | PASS ($509M) |
| 3. Stand-alone profitability | **TO TEST** | **TO TEST** |
| 4. Pooled compatibility | **TO TEST** | **TO TEST** |
| 5. Diversification value | Corr 0.66 < 0.7 PASS | Corr 0.54 < 0.7 PASS |

Gates 3 and 4 require running backtests — delegated to QE Phase 6.

**DOGE selected over SHIB** because:
- More IS candles (5,153 vs 4,240) — earlier start date provides more training data
- Slightly higher liquidity ($970M vs $509M)
- One symbol at a time (SHIB reserved for future iteration if DOGE succeeds)

### Category C: Labeling Analysis

| Metric | BTC | DOGE | SHIB |
|--------|-----|------|------|
| TP hit rate (8%/4%, 7d) | 55.9% | 81.0% | 83.1% |
| Timeout rate | 44.1% | 19.0% | 16.9% |
| Candles with |fwd_ret|>8% | 29.3% | 43.1% | 42.8% |
| Candles with |fwd_ret|>4% | 53.5% | 66.1% | 67.4% |

With fixed 8%/4% barriers, DOGE barriers are hit on 81% of candles — nearly every candle triggers TP or SL. The labels are dominated by first-candle direction (trivial to predict, useless for execution with wider barriers).

With dynamic ATR labeling (TP~14.5%, SL~7.3% for DOGE), the TP hit rate should drop to ~50-60% range (comparable to BTC), creating meaningful labels.

### Category F: Statistical Significance

Feature-target correlations for DOGE: 35/189 features have |corr| > 0.05 with p < 0.01 (highly significant). The signal exists but is modest (max |corr| = 0.22).

Key risk: the top features are price-level (EMA, SMA) which capture structural mean-reversion, not predictive signal. However, the LightGBM model uses these features in combination with momentum and volatility indicators, which may extract genuine signal.

## Implementation Spec for QE

### Code Changes

1. **`lgbm.py`: Pass ATR values to labeling**
   - Add `use_atr_labeling: bool = False` parameter to `LightGbmStrategy.__init__`
   - When `use_atr_labeling=True` AND `atr_tp_multiplier` is set:
     - Compute `atr_values = close * vol_natr_21 / 100` for master DataFrame
     - Pass `atr_values` to `label_trades()` calls
     - `label_tp_pct` becomes ATR multiplier (use `atr_tp_multiplier` value)
     - `label_sl_pct` becomes ATR multiplier (use `atr_sl_multiplier` value)
   - This affects both `_train_for_month()` labeling and optimization labeling

2. **Runner script `run_iteration_108.py`**:
   ```python
   SYMBOLS = ("BTCUSDT", "ETHUSDT", "DOGEUSDT")
   strategy = LightGbmStrategy(
       training_months=24,
       n_trials=50,
       cv_splits=5,
       label_tp_pct=2.9,    # ATR multiplier (was 8.0)
       label_sl_pct=1.45,   # ATR multiplier (was 4.0)
       label_timeout_minutes=10080,
       fee_pct=0.1,
       features_dir="data/features",
       seed=42,
       verbose=1,
       atr_tp_multiplier=2.9,
       atr_sl_multiplier=1.45,
       use_atr_labeling=True,
       ensemble_seeds=[42, 123, 456, 789, 1001],
   )
   ```

3. **CV gap**: With 3 symbols and 10080min timeout on 8h:
   - timeout_candles = 10080/480 = 21
   - gap = (21+1) × 3 = 66 rows

### Verification

- QE MUST verify that for BTC candles with NATR ~2.76%, dynamic barriers approximate 8%/4% (same as baseline)
- QE MUST verify that for DOGE candles, dynamic barriers scale to ~14.5%/7.3%
- QE MUST verify label leakage gap is correctly computed (66 rows for 3 symbols)
- QE MUST check 10-20 trades for correct entry/exit/PnL

### Expected Outcome

**Optimistic**: Dynamic labeling fixes the label-execution mismatch for ETH (+30% mismatch) and enables DOGE to contribute signal. 3-symbol pool increases trade count and diversification. OOS Sharpe >= baseline (1.01).

**Pessimistic**: DOGE adds noise to the pooled model (as BNB did in iter 105). CV gap increase (44→66) reduces optimization quality. OOS Sharpe < baseline.

**Fail fast**: Year 1 checkpoint (cumulative PnL < 0 or WR < 33%) triggers early stop.
