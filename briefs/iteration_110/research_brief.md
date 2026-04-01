# Iteration 110 Research Brief

**Type**: EXPLORATION
**Date**: 2026-04-01
**Theme**: Volatility regime filter — skip low-vol meme market

## Section 0: Data Split

- OOS cutoff: `2025-03-24` (fixed, never changes)
- IS period: all data before 2025-03-24
- OOS period: all data from 2025-03-24 onward
- Walk-forward runs on ALL data; reports split at cutoff

## Problem: 2023 Choppy Meme Market

Iter 108 (DOGE+SHIB) early-stopped because of 2023. Deep analysis reveals:

| Metric | DOGE 2022 | DOGE 2023 | DOGE 2024 |
|--------|-----------|-----------|-----------|
| Mean NATR | 4.71% | **3.15%** | 4.69% |
| High-vol candles | 50% | **29%** | 53% |
| Cumulative return | -59% | +29% | +252% |
| Return autocorrelation | +0.02 | **-0.08** | -0.01 |

2023 was 33% less volatile with negative autocorrelation (choppy mean-reversion). The model lost because:
1. **Low NATR → tight ATR barriers → more SL hits**: Dynamic barriers shrink in low-vol, creating a "whipsaw zone" where noise triggers SL
2. **No clear trend → random predictions**: The model predicts direction, but in a range-bound market, direction is noise
3. **Feb 2023 catastrophe**: 13 trades, 11 SL, -56.8% PnL. NATR 3.63% (moderate), but the market was choppy with no trend (ADX 24.6 — inconclusive)

### Monthly Evidence from Iter 108

**Profitable months (>+5% PnL)**: Oct 2022 (NATR 3.43, +33.7%), Nov 2022 (NATR 8.65, +61.9%), Mar 2023 (NATR 3.58, +17.1%), Jun 2023 (NATR 2.82, +17.5%)

**Losing months (< -5% PnL)**: Jul 2022 (NATR 4.12, -11.8%), Feb 2023 (NATR 3.63, -56.8%), Jul 2023 (NATR 3.45, -11.7%), Sep 2023 (NATR 1.78, -7.2%), Nov 2023 (NATR 4.01, -11.5%), Dec 2023 (NATR 3.79, -26.4%)

**Key finding**: NATR alone doesn't cleanly separate winners from losers (Feb 2023 was NATR 3.63 but lost 56.8%). But the **worst months cluster in low-NATR periods**. A filter won't catch Feb 2023 but WILL skip the "dead market" months (May/Aug/Sep/Oct 2023).

## Proposed Change: Per-Candle NATR Regime Filter

Add a `min_natr_threshold` parameter to `LightGbmStrategy.get_signal()`. When the current candle's NATR_21 < threshold, return NO_SIGNAL regardless of model prediction.

**Threshold: 3.0%** (based on IS analysis):
- DOGE median NATR_21 overall: ~3.5%
- DOGE median NATR_21 in 2023: 2.43% (most 2023 candles would be filtered)
- 2022 and 2024 median: ~3.6% (most candles pass)

Expected impact:
- Skip ~30-40% of 2023 candles (the dead ones)
- Keep most 2022 and 2024 candles
- Reduce total trade count but improve WR significantly
- The model only trades when there's enough volatility to generate meaningful barrier hits

## Research Analysis (Categories A, E, B, C)

### Category E: Trade Pattern Analysis (2022 vs 2023)
- **2022**: LONG 16 trades WR=50% (+35.9%), SHORT 17 trades WR=59% (+56.5%). Both directions profitable.
- **2023**: LONG 43 trades WR=30% (-16.0%), SHORT 38 trades WR=34% (-65.1%). Both directions lose. The model over-traded (81 trades vs 33 in 2022) in a market where it had no edge.
- **Short direction worse in 2023**: The model kept shorting in a slowly rising market (+29% cum return).

### Category A: Feature Relevance
The 42 features include vol_natr_21 which the model CAN use for regime detection. But the model uses it for direction prediction, not trade filtering. A hard NATR gate forces the behavior we want: "don't trade when volatility is too low for the strategy to work."

### Category B: DOGE+SHIB Pool Validated
Iter 109 proved DOGE-only fails (IS Sharpe -0.80). SHIB's training data is needed for model quality even though SHIB loses in execution. Keep the pool.

### Category C: Labeling Unchanged
Dynamic ATR labeling (2.9x/1.45x) stays. In low-vol periods the barriers become very tight, which is part of the problem — the regime filter prevents trading when barriers are too tight.

## Implementation Spec

### Code Change: `lgbm.py`

Add `min_natr_threshold: float | None = None` parameter:
```python
def get_signal(self, symbol, open_time):
    ...
    # After model predicts, before returning signal:
    if self.min_natr_threshold is not None:
        natr = self._month_natr.get((symbol, open_time))
        if natr is not None and natr < self.min_natr_threshold:
            return NO_SIGNAL
    ...
```

### Runner
```python
SYMBOLS = ("DOGEUSDT", "1000SHIBUSDT")
strategy = LightGbmStrategy(
    ...same as iter 108...
    min_natr_threshold=3.0,  # NEW: skip low-vol candles
)
```

### Expected Outcome

**Optimistic**: Skipping dead months eliminates the 2023 drawdown. IS Sharpe improves from +0.10 to +0.5-1.0. Model reaches OOS without early stop.

**Pessimistic**: The threshold is too aggressive, filtering out profitable months too. Or the remaining trades are too few (<50) for reliable metrics.

**Fail fast**: Same yearly checkpoints. If Year 1 (2022 H2) is still negative after filtering, the problem is deeper than regime.
