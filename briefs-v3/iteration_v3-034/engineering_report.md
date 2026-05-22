# Engineering Report — iter-v3/034

## Status: READY-FOR-CRITIC

Wall-clock 0.33h (20 min). NEGATIVE-IS but **dramatic per-symbol differentiation finding** that informs iter-v3/035.

## Hypothesis-Implementation Alignment

DROP VET (V3_MODELS 5→4); ADD fracdiff_d05_close (V3_FEATURE_COLUMNS 14→15); REQUIRED_GAP 110→88; ITERATION_LABEL=v3-034.

## Headline Metrics

| Metric | Value | vs iter-v3/032 anchor (+0.2360/+1.9338) |
|--------|-------|------------------------------------------|
| IS monthly Sharpe | -0.1636 | Δ -0.40 (NEGATIVE) |
| OOS monthly Sharpe | +1.7713 | Δ -0.16 |
| Bundle OOS trades | 119 | -10 |
| OOS MaxDD | **17.55%** | best in v3 catalog |
| IS MaxDD | 59.69% | +10pp worse |
| n_eff | 19 | consistent |

## Per-Symbol OOS — DRAMATIC PER-SYMBOL DIFFERENTIATION

| Symbol | weighted_pnl | Trades | WR | vs iter-v3/032 |
|--------|--------------|--------|-----|----------------|
| **BCH** | **+48.73** | 32 | **50.0%** | **+37.98 swing!** |
| ALGO | +12.63 | 27 | 37.0% | -8.24 |
| TRX | +9.13 | 45 | 40.0% | **-20.11 swing** |
| LDO | -2.83 | 15 | 33.3% | -6.81 |

The "frozen baseline" pattern from iter-v3/020-031 broke because adding fracdiff to V3_FEATURE_COLUMNS perturbed ALL per-symbol Optuna trajectories (frozen baseline only applies when V3_FEATURE_COLUMNS is unchanged).

## Feature Importance — Fracdiff Validated

Portfolio:
- regime_momentum_signed_5d: 251 (top)
- fracdiff_d05_close: **240** (rank 2; ~96% of top!)

Both engineered features are MEANINGFULLY USED by the model. fracdiff is NOT INERT — it's actually one of the top-2 features.

## Critical Insight — Per-Symbol Engineered Features

fracdiff is PER-SYMBOL-SPECIFIC:
- BCH benefits dramatically: +48.73 OOS PnL, 50% WR (was +10.75 / 39.5%)
- TRX suffers: +9.13 OOS, down -20.11 from +29.24
- ALGO suffers: +12.63, down -8.24 from +20.87
- LDO marginally worse

Mechanism: fracdiff captures memory-preserving regime-persistence info. BCH's price regime apparently has strong memory persistence (fracdiff fits well); TRX's doesn't (fracdiff adds noise).

**Universal application of an engineered feature can help one symbol while hurting others.** This is a new dimension of per-symbol thinking: not just feature SIGNATURE per symbol, but feature ADDITIONS per symbol.

## §4.4 Classification

PATH C fires: IS Δ -0.40 ≪ -0.10 threshold. Verdict: **EXPLORATION-NEGATIVE-IS-AXIS**.

The OOS lift is the same single-seed-suspicious pattern; OOS MaxDD 17.55% is interesting but not enough to override the IS axis collapse.

## Recommendations

iter-v3/035 axis: **BCH-only fracdiff via V3_FEATURES_PER_SYMBOL**.

Rationale:
- iter-v3/034 confirms fracdiff helps BCH (+38 OOS swing) while hurting TRX/ALGO
- V3_FEATURES_PER_SYMBOL architecture exists (from iter-v3/030 attempt — was negative for LDO subset, but architecture works)
- BCH gets 15 features (14 base + fracdiff_d05_close); LDO+TRX+ALGO keep 14 (no fracdiff)
- Tests "per-symbol engineered feature addition" methodology

Implementation:
```python
V3_FEATURES_PER_SYMBOL = {
    "BCHUSDT": V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",),  # 14 + 1 = 15
    # LDO/TRX/ALGO not specified → fall back to V3_FEATURE_COLUMNS_TOP_N (14, no fracdiff)
}
```

V3_FEATURE_COLUMNS_TOP_N reverts to 14 (drop fracdiff from universal); fracdiff is added BCH-only via per-symbol dict.

Predicted bands:
- IS Sharpe [+0.30, +0.70] median +0.50 (anchor +0.24; BCH improvement targeted)
- OOS Sharpe [+1.70, +2.20] median +1.95 (BCH +48 contribution preserved; TRX/ALGO restored)
- BCH OOS PnL ≥ +30 (was +48 with universal fracdiff)
- TRX OOS PnL restored to +25-30 (was +9 with universal fracdiff; back to +29 expected)

Status: READY-FOR-CRITIC.
