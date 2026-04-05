# Iteration 155 Research Brief

**Type**: EXPLORATION (per-symbol VT architecture)
**Model Track**: v0.152 baseline, post-processing VT calibration
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iter 153 diary's Next Ideas explicitly listed: "Per-symbol target/floor (EXPLORATION) — different vt config per model. BTC could have different optimal than LINK. Not pursued yet."

IS analysis of iter 138's trades reveals that v0.152's universal VT config
(target=0.3, lookback=45, min_scale=0.33) is **not actually adaptive** — 78% of
trades sit at the floor, 21% sit at default=1.0, and only 0.5% of trades get a
middle scale. The config behaves as a binary switch: "trade at 1.0 when the
symbol has <3 recent trades, otherwise scale by 0.33."

This happens because median realized vol per symbol (4-8% daily PnL std) is far
above the target of 0.3, so scale = 0.3/median_vol ≈ 0.04-0.08 → always clipped
to the 0.33 floor.

## Research Analysis (Checklist Categories)

### B. Symbol Universe & Diversification (B3 — per-symbol architecture)

IS per-symbol realized vol distribution (std of last-45d trade PnLs, walk-forward valid):

| Symbol | median | mean | min | max | std of vol |
|--------|--------|------|-----|-----|-----------|
| BTCUSDT | 4.08 | 4.03 | 1.76 | 7.23 | 1.00 |
| BNBUSDT | 4.43 | 5.11 | 0.57 | 13.50 | 2.27 |
| ETHUSDT | 5.43 | 5.80 | 0.25 | 12.76 | 2.14 |
| LINKUSDT | 7.77 | 8.51 | 0.70 | 21.37 | 3.61 |

LINK has **1.9x BTC's median realized vol** and **3.6x BTC's vol dispersion**.
Applying the same target_vol across all four is a mismatch — it forces all of
them to the floor equally even though LINK is genuinely more volatile.

### E. Trade Pattern — iter 152 scale distribution diagnostic

Per-symbol scale distribution under iter 152's config:

| Symbol | trades | mean scale | @ floor (0.33) | @ default (1.0) |
|--------|--------|-----------|----------------|-----------------|
| BTCUSDT | 184 | 0.527 | 71% | 29% |
| BNBUSDT | 193 | 0.493 | 76% | 24% |
| ETHUSDT | 214 | 0.456 | 81% | 18% |
| LINKUSDT | 225 | 0.423 | 85% | 14% |

The 0.472 global avg scale matches iter 152's engineering report (0.47). The
entire adaptivity comes from whether each trade has ≥3 closes in the past 45
days. After that threshold is met, every subsequent trade hits floor 0.33.

## Hypothesis

A per-symbol target_vol calibrated to each symbol's **actual median realized
vol** will produce scales in the middle of the range [0.33, 1.0] instead of a
binary {0.33, 1.0}. This tests whether true adaptive vol targeting beats the
current "fresh start" heuristic.

### Proposed config: per-symbol target_vol

```
target_vol_BTC  = 4.08 × k     (median BTC realized vol × multiplier)
target_vol_ETH  = 5.43 × k
target_vol_LINK = 7.77 × k
target_vol_BNB  = 4.43 × k
```

At k=0.5, scale-at-median=0.5 for all symbols. Scaling in high-vol periods
pulls toward floor (0.33); scaling in low-vol periods pulls toward default.

### Grid (post-processing on iter 138 raw trades, IS only for selection)

| Config | k | Description |
|--------|---|-------------|
| A (baseline) | — | Universal target=0.3 (v0.152) |
| B (calibrated-tight) | 0.3 | Lower target → more deleveraging |
| C (calibrated-mid) | 0.5 | Median-centered |
| D (calibrated-loose) | 0.7 | Higher target → less deleveraging |
| E (calibrated-wide) | 1.0 | Target = median realized vol |

Floor=0.33 and lookback=45 held constant (iter 152 winners). Only target_vol
varies per symbol.

## Success Criteria

Selection metric: **IS Sharpe** (v0.152 baseline IS Sharpe is 1.3320). The
winner is the config with highest IS Sharpe, then validated on OOS.

Hard constraints (for MERGE):
- OOS Sharpe > v0.152 (+2.83)
- OOS MaxDD ≤ 38.7% (1.2 × baseline 32.2%, using pre-iter-152 baseline)
- ≥ 50 OOS trades (none dropped — VT is weight-only)
- IS/OOS Sharpe ratio > 0.5

## Exploration Justification

This is EXPLORATION because it introduces **per-symbol VT parameters** — a new
architecture dimension. Current config applies a single universal target_vol
across all four symbols. Calibrating per-symbol changes the VT mechanism from
"binary fresh-start" to "true adaptive scaling."

## Notes

- No model retraining needed. This is post-processing of iter 138 trades.
- Walk-forward valid: each trade's scale uses only past per-symbol daily PnL.
- Only IS trades determine config selection; OOS seen only in Phase 7.
- If no per-symbol config beats v0.152 IS, NO-MERGE — current universal config
  is confirmed optimal and the binary fresh-start behavior is genuinely the
  right mechanism.
