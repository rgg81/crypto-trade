# Iteration 097 — Research Brief

**Type**: EXPLORATION (sample uniqueness weighting — AFML Ch. 4)
**Date**: 2026-03-31
**Previous**: Iter 096 (NO-MERGE, identical to baseline — bug fix isolation)

## Section 0: Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Hypothesis

Triple-barrier labels with 7-day timeout scan 21 candles forward on 8h data. When adjacent samples' label windows overlap, they are not independent observations. The current weighting (|PnL| normalized to [1,10]) treats all samples equally regardless of overlap.

Sample uniqueness weighting (AFML Ch. 4) computes how "unique" each sample's label window is — samples with fewer concurrent labels get higher weight. This forces the model to focus on truly independent observations rather than over-learning from crowded periods.

**Single variable changed**: sample weight formula. Existing |PnL| weights multiplied by uniqueness factor.

## Research Analysis (4 categories — mandatory after 3 NO-MERGE)

### Category A: Feature Analysis

185 features confirmed essential (iters 094-096). No feature changes in this iteration.

### Category C: Labeling Analysis (IS data)

- **Label distribution**: 51.2% long, 48.8% short — balanced (good)
- **Label flip rate**: 18% — very stable labels, low noise
- **Avg trade duration**: 83.3h (median 72h, max 168h = 7-day timeout)
- **Concurrent trade overlap**: avg 1.0 concurrent trades, 78.3% have at least 1 overlap, 1.4% have 3+ overlaps
- **Implication**: Most training samples overlap with at least one neighbor. Uniqueness weighting will down-weight crowded periods (market stress events with rapid labeling) and up-weight isolated trades.

### Category E: Trade Pattern Analysis (IS data)

- Best months: Jun 2022 (+68.3%, 75% WR), Feb 2024 (+44.9%, 73% WR), Nov 2024 (+63.2%, 71% WR) — all high-volatility periods
- Worst months: Jun 2024 (-22.3%, 0% WR), Mar 2023 (-22.1%, 20% WR), Jul 2022 (-16.6%, 33% WR)
- Pattern: The model excels in volatile directional markets and fails in choppy/ranging periods
- Uniqueness weighting may help by reducing the influence of clustered losing trades in choppy markets

### Category F: Statistical Rigor (IS data)

- **WR**: 42.8%, 95% binomial CI: [37.6%, 48.0%]
- **Break-even WR**: 33.3% (for 2:1 RR)
- **WR is statistically significantly above break-even** — the signal is real
- **WR is NOT significantly different from 50%** at 95% — the model has genuine but modest directional skill

## Proposed Configuration (iter 097)

**UNCHANGED from iter 093**:
- Symbols: BTCUSDT + ETHUSDT
- Training: 24 months, walk-forward monthly
- Features: 185 (full symbol-scoped discovery)
- Labeling: TP=8%, SL=4%, timeout=7 days, dynamic ATR barriers
- CV: 5 folds, gap=44, 50 Optuna trials
- Ensemble: 5 seeds [42, 123, 456, 789, 1001]
- Cooldown: 2 candles

**CHANGED**:
- **Sample weights**: `uniqueness(i) * |PnL|(i)` instead of just `|PnL|(i)`
- Uniqueness computed per training window using concurrent label overlap
- New `compute_sample_uniqueness()` function in `labeling.py`
- New `sample_uniqueness` flag in `LightGbmStrategy`

## Implementation Plan

1. Add `compute_sample_uniqueness(candidate_indices, timeout_minutes, open_time_arr, sym_arr)` to `labeling.py`
   - For each sample i, count concurrent active labels at each timestamp in [t_i, t_i + timeout]
   - Uniqueness(i) = mean(1/c_t) for all t in window
   - Returns array of uniqueness values in [0, 1]

2. Add `sample_uniqueness: bool = False` parameter to `LightGbmStrategy`

3. In `_train_for_month()`, after `label_trades()`, compute uniqueness and multiply with PnL weights:
   ```python
   if self.sample_uniqueness:
       uniqueness = compute_sample_uniqueness(...)
       train_weights = train_weights * uniqueness
   ```

4. Runner uses `sample_uniqueness=True`

## Expected Outcome

- IS Sharpe may decrease slightly (fewer effective samples)
- OOS/IS ratio should improve (less overfitting to crowded periods)
- Trade count should be similar (weighting doesn't filter, just re-weights)
