# Iteration 162 Research Brief

**Type**: EXPLORATION (new feature generation — entropy + CUSUM)
**Model Track**: v0.152 baseline, feature pipeline extension
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

From the Exploration Idea Bank Tier 1 (#4 and #5):
- **Entropy features (AFML Ch. 18)**: Shannon entropy of discretized returns.
  High entropy = unpredictable market (avoid trading). Low entropy =
  patterned market (edge exploitable). Never tested in 161 iterations.
- **CUSUM structural breaks (AFML Ch. 17)**: Detect regime changes via
  cumulative deviation from mean. Never tested. Prerequisite for
  event-driven sampling.

Both are genuinely novel — not variations of existing features.

## Feature Design (11 new features)

### Entropy (prefix `ent_`, 4 features)

| Feature | Description | Rationale |
|---------|-------------|-----------|
| ent_shannon_10 | Shannon entropy of 10-candle return window | Short-term predictability |
| ent_shannon_20 | Shannon entropy of 20-candle return window | Medium-term predictability |
| ent_shannon_50 | Shannon entropy of 50-candle return window | Long-term predictability |
| ent_volume_20 | Shannon entropy of 20-candle volume change | Microstructure regime |

**Economic rationale**: Markets oscillate between ordered (trending,
mean-reverting) and disordered (random walk) states. Low entropy indicates
patterned behavior that LightGBM can exploit. High entropy indicates
noise where signals are unreliable.

### CUSUM (prefix `cusum_`, 7 features)

| Feature | Description | Rationale |
|---------|-------------|-----------|
| cusum_since_1s | Candles since last 1σ CUSUM break | Regime freshness (1σ) |
| cusum_since_2s | Candles since last 2σ CUSUM break | Regime freshness (2σ) |
| cusum_since_3s | Candles since last 3σ CUSUM break | Regime freshness (3σ) |
| cusum_norm_1s | cusum_since_1s / 50 | Scale-invariant freshness |
| cusum_norm_2s | cusum_since_2s / 50 | Scale-invariant freshness |
| cusum_norm_3s | cusum_since_3s / 50 | Scale-invariant freshness |
| cusum_break_5 | Boolean: 2σ break in last 5 candles | Immediate regime change |

**Economic rationale**: Trades opened shortly after a structural break
(regime change) have different expected outcomes than trades in a stable
regime. CUSUM quantifies "how fresh is this regime?"

## Implementation Notes

- All features are **scale-invariant** (returns and volume changes, not raw prices).
- Shannon entropy uses 10-bin histogram — robust to distribution shape.
- CUSUM threshold is adaptive: `n_sigma × median(rolling_std_50)`.
- Both entropy and CUSUM use only past data (no lookahead).
- Net feature count: +11 (acceptable since baseline has ~106 features,
  and these REPLACE nothing — they're genuinely orthogonal information).

## Checklist Categories

- **A (Feature Contribution)**: A4 — new feature proposals with economic
  rationale. Net +11 features; samples-per-feature ratio moves from
  ~41 to ~37 (still above the danger zone of 22).
- **D (Feature Frequency)**: Entropy computed at windows 10/20/50;
  CUSUM at adaptive thresholds — multiple timescales covered.

## Next Steps

This iteration adds the feature computation only. To evaluate impact:
1. Regenerate parquets: `uv run crypto-trade features --groups all --format parquet`
2. Retrain primary model with new features included (~5h walk-forward)
3. Compare IS/OOS metrics against v0.152 baseline

Steps 2-3 are a separate iteration (iter 163+) — this iteration
establishes the feature pipeline.
