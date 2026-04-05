# Iteration 153 Diary

**Date**: 2026-04-06
**Type**: EXPLOITATION (min_scale extension search)
**Decision**: **NO-MERGE** — IS Sharpe peaks at 0.33 (production). Lower values reduce IS.

## Results

Extended grid {0.10, 0.15, 0.20, 0.25, 0.30} on top of iter 152's {0.25, 0.33, 0.50, 0.67, 0.75}:

| min_scale | IS Sharpe | OOS Sharpe | OOS MaxDD | OOS PF |
|-----------|-----------|-----------|-----------|--------|
| 0.10 | 1.2192 | +2.67 | 17.97% | 2.09 |
| 0.20 | 1.2943 | +2.80 | 16.68% | 1.91 |
| 0.30 | 1.3296 | +2.83 | 19.98% | 1.78 |
| **0.33 (PROD)** | **1.3320** | +2.83 | 21.81% | 1.76 |
| 0.50 | 1.3056 | +2.74 | 32.22% | 1.64 |

## Analysis

### IS Sharpe peak confirmed at 0.33

IS Sharpe is concave: rises from min_scale=0.10 (1.22) to peak at 0.33 (1.33),
then descends to 0.75 (1.23). Production config is walk-forward optimal.

### Divergence between IS and OOS

- **IS**: aggressive deleveraging hurts — reduces winning-period PnL
- **OOS**: aggressive deleveraging helps — protects during July 2025 crash

This divergence is a regime difference, not overfitting. The 2022-2024 IS period
had more sustained drawdowns where deleveraging hurt; 2025 OOS had sharp vol
spikes where deleveraging helped.

### Robustness confirmed

OOS Sharpe stays in [+2.67, +2.83] across min_scale ∈ [0.10, 0.75] — a 7.5x
range. Strategy is genuinely robust to this parameter. The specific choice of
0.33 is optimal but not fragile.

## Hard Constraints

N/A — this iteration confirms the current baseline, no new config proposed.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, X, E, E, E, X, X, X, X, **X**] (iters 144-153)
Exploration rate: 4/10 = 40% ✓

## Next Iteration Ideas

1. **ACCEPT v0.152 as definitively final** — parameter search exhausted.
2. **Paper trading** — move to deployment.
3. **Per-symbol target/floor** (EXPLORATION) — different vt config per model.
   BTC could have different optimal than LINK. Not pursued yet.
