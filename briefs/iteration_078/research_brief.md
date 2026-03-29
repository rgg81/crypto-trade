# Iteration 078 — Research Brief

**Type**: EXPLORATION (architecture change: pooled → per-symbol models)
**Date**: 2026-03-29
**Baseline**: Iteration 068 (OOS Sharpe +1.84)

## Section 0: Data Split

- OOS cutoff: **2025-03-24** (fixed, never changes)
- IS period: all data before 2025-03-24 (~5,727 8h candles per symbol)
- OOS period: 2025-03-24 onward
- Walk-forward runs on full dataset; reporting layer splits at cutoff

## Section 1: Hypothesis

**Per-symbol LightGBM models will outperform the pooled baseline by allowing each symbol to specialize in its own dynamics.**

Evidence from IS analysis:
- ETH SHORT WR 51.1% vs ETH LONG 38.5% — 12.6pp directional asymmetry
- BTC is balanced: LONG 43.6% vs SHORT 41.0%
- ETH NATR 3.58% vs BTC NATR 2.75% — 30% more volatile
- BTC-ETH correlation 0.83 = highly redundant in a pooled model
- Per-symbol models allow different hyperparameters, confidence thresholds, and feature importance profiles

## Section 2: Research Analysis (4 of 6 checklist categories)

### B. Symbol Universe & Diversification Analysis

#### B1. Correlation & Lead-Lag

| Metric | Value |
|--------|-------|
| Overall correlation (IS) | 0.8275 |
| Rolling 90-day mean | 0.8284 |
| Rolling 90-day std (stability) | 0.074 (stable) |
| Rolling 90-day min/max | 0.575 / 0.931 |
| High-vol regime correlation | 0.838 |
| Low-vol regime correlation | 0.794 |

**Lead-lag cross-correlation:**
| Lag (candles) | Correlation |
|---------------|-------------|
| 0 (simultaneous) | 0.828 |
| 1 (BTC leads 8h) | 0.018 |
| 2 (BTC leads 16h) | ~0.00 |
| 3 (BTC leads 24h) | ~0.00 |

**Conclusion**: No exploitable lead-lag relationship. BTC and ETH move simultaneously. Cross-asset features (`xbtc_` lagged returns) will NOT help ETH predictions — they are redundant at lag 0 and noise at lag 1+. This was confirmed by iter 070's failure.

Correlation strengthens during high-vol (+0.044 vs low-vol). This means diversification benefit is MINIMAL during crashes — both assets fall together.

#### B3. Model Architecture Decision

| Criterion | BTC ↔ ETH | Implication |
|-----------|-----------|-------------|
| Correlation | 0.83 | Pooled OK (similar signal) |
| NATR ratio | 1.3x | Borderline (within 2x threshold) |
| WR difference | 1.8pp overall | Small |
| Direction asymmetry | ETH SHORT 51.1% vs BTC LONG 43.6% | **LARGE — per-symbol favored** |
| IS data per symbol | ~5,727 candles (5+ years) | Sufficient for per-symbol training |

**Decision**: Option B — Per-symbol models. The directional asymmetry is the key driver. A pooled model averages ETH's strong SHORT signal with BTC's balanced signal, diluting both. Per-symbol models allow each to optimize independently.

### C. Labeling Analysis

| Metric | BTC | ETH |
|--------|-----|-----|
| Long TP hit rate | 56.2% | 62.9% |
| Short TP hit rate | 39.6% | 35.8% |
| Timeout rate | 4.2% | 1.3% |
| Label flip rate | ~8% | ~8% |

ETH has higher long TP hit rate (62.9% vs 56.2%) and lower timeout rate (1.3% vs 4.2%), suggesting cleaner signal for ETH. Labeling parameters (TP=8%, SL=4%, timeout=7d) remain unchanged — fixed labels work better than dynamic (iters 076-077).

### E. Trade Pattern Analysis (IS, baseline 068)

| Metric | BTC | ETH |
|--------|-----|-----|
| Trades | 172 | 201 |
| WR | 42.4% | 44.3% |
| Total PnL | +80.7% | +183.6% |
| LONG WR | 43.6% | 38.5% |
| SHORT WR | 41.0% | 51.1% |

Exit reasons (pooled): TP 32.2%, SL 51.2%, timeout 16.6%.
- TP trades: 100% profitable, avg +7.49%
- SL trades: avg -3.85%, bounded
- Timeout: 67.7% profitable, avg +1.64%
- Positive skew (+0.81) — asymmetric upside

Max consecutive wins: 11. Max consecutive losses: 10. Avg loss streak slightly longer (2.64 vs 2.02).

### F. Statistical Rigor

| Test | Result |
|------|--------|
| Bootstrap WR 95% CI | [38.6%, 48.5%] |
| Binomial p-value (vs 33.3% break-even) | 0.000031 |
| Per-trade PnL: mean | +0.71% |
| Per-trade PnL: skewness | +0.81 (favorable) |

Signal is statistically significant. CI excludes break-even. Positive skew confirms asymmetric risk/reward.

## Section 3: Proposed Changes

### Change 1: Per-symbol model architecture

Modify `LightGbmStrategy` to train **separate models per symbol**:

1. **Feature discovery**: Run per-symbol (no cross-symbol intersection needed)
2. **Training**: For each month, train N separate models (one per symbol), each with own Optuna (50 trials, 5 CV folds)
3. **Ensemble**: Each symbol gets its own 3-seed ensemble (seeds 42, 123, 789)
4. **Confidence threshold**: Per-symbol, per-seed optimization (0.50-0.85)
5. **Inference**: Route `get_signal(symbol, ...)` to that symbol's models

### Change 2: No other changes

- Same labeling: TP=8%, SL=4%, timeout=7d (fixed)
- Same execution: dynamic ATR barriers (2.9/1.45), cooldown=2
- Same features: 106 (but per-symbol feature columns may differ slightly)
- Same training: 24mo window, 5 CV folds, 50 Optuna trials
- Same symbols: BTCUSDT, ETHUSDT

**One variable changed**: pooled → per-symbol. Attribution is clean.

## Section 4: Expected Outcome

- ETH SHORT accuracy should improve (currently diluted by pooled BTC patterns)
- BTC may maintain or slightly improve (no ETH noise in training)
- Per-symbol feature importance should be more interpretable
- Trade count may change (different confidence thresholds per symbol)
- Risk: halved training data per model (~2,200 candles/year vs ~4,400 pooled). Mitigated by 5+ years of IS data per symbol.

## Section 5: Runner Configuration

```python
# Per-symbol mode — new parameter
strategy = LightGbmStrategy(
    training_months=24,
    n_trials=50,
    cv_splits=5,
    label_tp_pct=8.0,
    label_sl_pct=4.0,
    label_timeout_minutes=10080,
    fee_pct=0.1,
    seed=42,
    verbose=1,
    atr_tp_multiplier=2.9,
    atr_sl_multiplier=1.45,
    ensemble_seeds=[42, 123, 789],
    per_symbol=True,  # NEW: train separate models per symbol
)

config = BacktestConfig(
    symbols=("BTCUSDT", "ETHUSDT"),
    interval="8h",
    cooldown_candles=2,
    position_size=1000.0,
    fee_pct=0.1,
)
```
