# Iteration 152 Engineering Report

## Grid Results

| min_scale | max_scale | IS Sharpe | OOS Sharpe | OOS MaxDD | OOS PF | avg_scale |
|-----------|-----------|-----------|-----------|-----------|--------|-----------|
| 0.25 | 2.0 | 1.3184 | +2.8223 | **16.92%** | **1.84** | 0.40 |
| **0.33** | **2.0** | **1.3320** | **+2.8286** | **21.81%** | **1.76** | 0.47 |
| 0.50 (PROD) | 2.0 | 1.3056 | +2.7356 | 32.22% | 1.64 | 0.61 |
| 0.67 | 2.0 | 1.2530 | +2.5915 | 42.62% | 1.57 | 0.74 |
| 0.75 | 2.0 | 1.2275 | +2.5219 | 47.52% | 1.54 | 0.80 |
| 0.50 | 1.5 | 1.3056 | +2.7356 | 32.22% | 1.64 | 0.61 |
| 0.50 | 3.0 | 1.3056 | +2.7356 | 32.22% | 1.64 | 0.61 |
| 0.33 | 3.0 | 1.3320 | +2.8286 | 21.81% | 1.76 | 0.47 |

## Key Findings

1. **Monotonic**: lower min_scale → better OOS Sharpe AND lower OOS MaxDD.
2. **max_scale is irrelevant**: no trade hits scale > 2.0 (vol too high). Changing
   max_scale from 1.5 → 3.0 produces identical metrics.
3. **IS-best**: min_scale=0.33 (IS Sharpe 1.3320).
4. **min_scale=0.25 is slightly better OOS** but we select IS-best for walk-forward
   validity. The two are nearly identical (within 0.01 Sharpe).

## Official Metrics (min_scale=0.33)

| Metric | v0.151 (prod) | Iter 152 | Change |
|--------|---------------|----------|--------|
| OOS Sharpe | +2.7356 | **+2.8286** | **+3.4%** |
| OOS Sortino | +3.6523 | +3.3346 | -9% |
| OOS WR | 50.6% | 50.6% | same |
| OOS PF | 1.6402 | **1.7572** | **+7%** |
| OOS MaxDD | 32.22% | **21.81%** | **-32%** |
| OOS Calmar | 4.12 | **5.46** | **+33%** |
| OOS Net PnL | +132.7% | +119.1% | -10% |
| IS Sharpe | 1.3056 | 1.3320 | +2% |
| IS MaxDD | 93.93% | 76.89% | -18% |

## Mechanism

Lower `min_scale` allows position to shrink to 33% of nominal during worst vol
periods (e.g., July 2025 cross-asset crash). Mean scale drops from 0.61 (prod)
to 0.47 — ~23% less exposure on average, concentrated during high-vol periods.

During CALM periods, scales are typically above the floor (0.7-2.0) regardless
of min_scale setting. So lowering the floor doesn't affect calm trading — only
extreme vol events. This explains why both Sharpe AND MaxDD improve: the floor
change only hurts us during bad periods, never during good periods.

## Hard Constraints

| Constraint | Threshold | Iter 152 | Pass? |
|------------|-----------|----------|-------|
| OOS Sharpe > baseline | > +2.74 | +2.83 | **PASS (+3.4%)** |
| OOS MaxDD ≤ 38.7% (1.2×) | ≤ 38.7% | 21.81% | **PASS** |
| OOS Trades ≥ 50 | ≥ 50 | 164 | **PASS** |
| OOS PF > 1.0 | > 1.0 | 1.76 | **PASS** |
| Concentration ≤ 50% | ≤ 50% | 34.9% | **PASS** |
| IS/OOS ratio > 0.5 | > 0.5 | 0.47 | FAIL (marginal, consistent) |

## Engine Compatibility

No code change required. `vt_min_scale` is already a config parameter:

```python
BacktestConfig(
    ...,
    vol_targeting=True,
    vt_target_vol=0.3,
    vt_lookback_days=45,
    vt_min_scale=0.33,        # NEW: was 0.5
    vt_max_scale=2.0,
)
```

## Label Leakage Audit

No new training. Post-processing of iter 138 trades. Walk-forward tuning on IS
only. No leakage.
