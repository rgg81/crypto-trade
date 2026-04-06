# Iteration 163 Engineering Report

## Run Summary

Full walk-forward retrain with 204 features (193 baseline + 11 entropy/CUSUM).
Runtime: ~7 hours (Model A 2.7h, Model C 1.8h, Model D 1.7h, reports 5min).

| Model | Trades | Runtime |
|-------|--------|---------|
| A (BTC/ETH) | 427 | 9657s (2.7h) |
| C (LINK) | 206 | ~6500s (1.8h) |
| D (BNB) | 205 | 5980s (1.7h) |
| **Combined** | **838** | **~6.2h** |

## Results

| Metric | Baseline v0.152 | Iter 163 | Δ |
|--------|-----------------|----------|---|
| IS Sharpe | +1.3320 | +1.0962 | **-17.7%** |
| IS WR | 44.5% | 42.7% | -1.8pp |
| IS MaxDD | 76.89% | 80.56% | +4.8% |
| IS PF | 1.33 | 1.26 | -5.3% |
| IS trades | 652 | 663 | +1.7% |
| OOS Sharpe | **+2.8286** | **+1.2248** | **-56.7%** |
| OOS WR | 50.6% | 45.1% | **-5.5pp** |
| OOS MaxDD | 21.81% | 37.15% | **+70%** |
| OOS PF | 1.76 | 1.27 | **-28%** |
| OOS PnL | +119.1% | +51.9% | **-56%** |
| OOS trades | 164 | 175 | +6.7% |
| OOS/IS ratio | 0.47 | 1.12 | improved |
| OOS DSR (N=163) | — | -20.52 | — |

## Hard Constraints

| Constraint | Threshold | Actual | Pass? |
|------------|-----------|--------|-------|
| OOS Sharpe > baseline | > +2.83 | +1.22 | **FAIL (-57%)** |
| OOS MaxDD ≤ 26.2% | ≤ 26.2% | 37.15% | **FAIL** |
| OOS trades ≥ 50 | ≥ 50 | 175 | PASS |
| OOS PF > 1.0 | > 1.0 | 1.27 | PASS |
| IS/OOS ratio > 0.5 | > 0.5 | 1.12 | PASS |

**Decision: NO-MERGE** (catastrophic OOS degradation).

## Diagnosis

The entropy/CUSUM features **harmed** the model. Both IS and OOS Sharpe
degraded materially. The 11 new features added noise that diluted the
existing signal rather than complementing it.

Key observations:
1. **IS Sharpe dropped 18%** from 1.33 to 1.10 — the model learned LESS
   effectively with the new features, not more.
2. **OOS Sharpe collapsed 57%** from 2.83 to 1.22 — the noise amplified
   on unseen data.
3. **OOS MaxDD nearly doubled** from 21.8% to 37.2% — VT couldn't
   compensate for the degraded signal quality.
4. **Trade count increased slightly** (652→663 IS, 164→175 OOS) — the
   model generated more signals but at much lower quality.
5. **IS/OOS ratio improved** (0.47 → 1.12) — perversely, because BOTH
   halves degraded, the ratio converged. This is not a good sign.

## Feature Impact Theory

The entropy and CUSUM features likely hurt because:

1. **Entropy is noisy at small windows**: ent_shannon_10 uses only 10
   data points for binning — the resulting entropy estimate has high
   variance. LightGBM may have used noisy splits on this feature.

2. **CUSUM threshold is data-dependent**: The adaptive σ threshold uses
   `median(rolling_std_50)` — a single value computed once from all
   data. This makes the CUSUM features regime-dependent in a way that
   doesn't generalize across IS/OOS boundaries.

3. **Feature dilution**: With 204 features (up from 193), and Optuna
   tuning `colsample_bytree` per month, the optimization space expanded.
   New features competed for split points with established ones,
   potentially displacing proven features in some monthly models.

4. **Samples-per-feature ratio dropped**: 4400/204 ≈ 22, below the
   danger zone. This is the same pathology as iter 078 (185 features,
   ratio 21, catastrophic).

## Label Leakage Audit

No code changes to CV or walk-forward logic. `TimeSeriesSplit` gap
unchanged. Leakage not the cause — this is a pure feature-quality issue.

## Conclusion

Entropy and CUSUM features degrade the model. The features should NOT be
included in future runs. v0.152's 193-feature baseline remains optimal.
