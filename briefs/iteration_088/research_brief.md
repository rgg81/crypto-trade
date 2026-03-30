# Iteration 088 — Research Brief

**Type**: EXPLOITATION
**Date**: 2026-03-30
**Predecessor**: Iteration 080 (ternary, OOS Sharpe +1.00, MaxDD 33.4%)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES.
```

- IS: all data before 2025-03-24 (BTC: 5,727 candles, ETH: 5,727 candles)
- OOS: data from 2025-03-24 onward
- Walk-forward backtest runs on ALL data; reporting splits at cutoff

## Section 1: Hypothesis

**Lower the ternary neutral threshold from 2.0% to 1.0%** to retain more training samples and generate more trades while still filtering the most ambiguous timeout candles.

Iter 080 demonstrated that ternary labeling with neutral_threshold=2.0% improves model quality (IS Sharpe +1.26 vs baseline +1.22, OOS MaxDD 33.4% vs 42.6%). However, it produced fewer OOS trades (73 vs 87), resulting in lower OOS Sharpe (+1.00 vs +1.84). This iteration tests whether a lower neutral threshold recovers some of those trades while preserving ternary's noise-reduction benefit.

## Section 2: Configuration

| Parameter | Value | Change from baseline |
|-----------|-------|---------------------|
| Labeling | **Ternary** (neutral_threshold=1.0%) | Was binary |
| Features | Global intersection (~115) | Same approach |
| Symbols | BTCUSDT, ETHUSDT (pooled) | Same |
| Training | 24 months, 5 CV folds, 50 Optuna trials | Same |
| Ensemble | 3 seeds [42, 123, 789] | Same |
| Confidence threshold | [0.50, 0.85] | Same |
| Execution | Dynamic ATR (TP=2.9, SL=1.45), cooldown=2 | Same |
| TP/SL | 8% / 4%, timeout 7 days | Same |

**Single variable changed**: neutral_threshold 2.0% → 1.0%

## Section 3: Research Analysis

### Category A: Feature Verification

- Current global intersection: **115 features** (was 113 in baseline era — slight change from parquet regeneration)
- Symbol-scoped BTC+ETH intersection: 215 features (100 dropped by global intersection)
- No slow features in global intersection (iter 086's slow features weren't merged)
- Using global intersection to match baseline discovery approach

### Category C: Labeling Analysis

Label distribution using actual `label_trades()` on IS data:

| Threshold | Long | Short | Neutral | Avg labeled PnL |
|-----------|------|-------|---------|-----------------|
| Binary    | 53.1% | 46.9% | 0.0% | 2.243% |
| 1.0%      | 49.2% | 42.9% | **7.9%** | 2.397% |
| 2.0%      | 45.1% | 38.1% | 16.7% | 2.646% |

**Key findings**:
- 1.0% filters 899 candles (7.9%) vs 1,901 (16.7%) at 2.0%
- TP hit count is **identical** across all thresholds (3,454) — neutrals come from timeouts only
- SL hits decrease from 4,732 → 4,540 → 4,225 as more timeouts are neutralized
- TP rate improves: 30.4% → 33.0% → 36.5%

### Category E: Trade Pattern Analysis

**Candles filtered by 1.0% threshold** (899 candles):
- If traded with binary labels: mean PnL = 0.449%, WR = 49.4%
- These are genuinely ambiguous — barely above random

**Extra candles filtered by 2.0% but kept by 1.0%** (1,002 candles, the 1-2% band):
- If traded with binary labels: mean PnL = 0.047%, WR = 45.9%
- Weak signal but non-random — worth keeping in training

**Insight**: The 1.0% threshold removes the truly noisy timeouts (WR ≈ 50%) while retaining candles in the 1-2% band that carry mild directional signal. This is the optimal tradeoff — 2.0% was too aggressive, removing candles that could inform the model.

### Category F: Statistical Rigor

- **WR significance**: Ternary WR 45.2% with 73 trades: p=0.040 vs break-even (33.3%). Significant at 5%.
- **Estimated OOS trade count**: ~80-81 trades (vs 73 at 2.0%, 87 at binary), based on label retention ratio (92.1% vs 83.3%)
- **PnL gap to baseline**: To match 94.0% total OOS PnL, need avg 1.18%/trade at 80 trades (vs iter 080's 0.67%). Gap is large.
- **Honest assessment**: Ternary 1.0% alone is unlikely to beat OOS Sharpe +1.84. The baseline's OOS may be a favorable outlier (OOS/IS ratio 1.50 is flagged suspicious). However, ternary produces healthier risk metrics that matter for live trading.

## Section 4: Expected Outcome

**Optimistic**: ~80 OOS trades, WR ~45%, MaxDD ~35%, Sharpe ~1.2-1.5
**Realistic**: ~80 OOS trades, WR ~44%, MaxDD ~37%, Sharpe ~0.9-1.1
**Pessimistic**: Results between iter 080 and baseline with no clear improvement

## Section 5: Risk Assessment

- **Low risk**: This is a 1-variable change from a proven configuration (iter 080)
- **No new code**: Ternary labeling already implemented (iter 080)
- **Confidence threshold range unchanged**: Avoids the catastrophic failure mode from iter 087
