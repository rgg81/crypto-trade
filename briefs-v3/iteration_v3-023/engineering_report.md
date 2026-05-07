# Engineering Report — iter-v3/023

## Status: READY-FOR-CRITIC

Wall-clock: 0.23h (14 min). 3 symbols × 14 features × n_trials=35 × 1 outer × 1 inner.

## Hypothesis-Implementation Alignment

Single-axis discipline preserved: V3_FEATURE_COLUMNS=14 (re-add funding_rate_zscore_30); V3_MODELS=3 (BCH+LDO+TRX); REQUIRED_GAP=66; regime gate disabled (was iter-v3/022); ITERATION_LABEL=v3-023; n_trials=35 (post-iter-v3/019 default).

## Reproducibility Stamps

- Setup commit: `f525ea6`
- Phase 5.5 gate: `f94ce3e`
- Brief: `04a715d`
- EDA inherited: iter-v3/019 SHA `95858cb`
- Library stack pinned per BASELINE_V3.md

## Headline Metrics

| Metric | Value |
|--------|-------|
| IS monthly Sharpe | +0.5270 (Δ +0.15 vs anchor +0.3788) |
| OOS monthly Sharpe | **-1.0706** (Δ -1.46 vs anchor +0.3869 — worst single-seed OOS in v3) |
| IS trades | 195 |
| OOS trades | 92 (below 130 floor by 38) |
| IS MaxDD | 20.54% |
| OOS MaxDD | **49.93%** (first OOS MaxDD breach > 50% in v3) |
| DSR | 0.0 |
| PBO mean | 0.0922 |
| PSR | 0.0000 (collapsed) |
| n_eff | 19 (consistent with n_trials=35 default) |

## Per-symbol breakdown

| Symbol | OOS PnL | n_trades | WR | concentration |
|--------|---------|----------|-----|---------------|
| BCH | -26.21 | 36 | 25.0% | 78.93% (negative MaxDD driver) |
| LDO | -16.13 | 8 | 12.5% (catastrophic) | 48.57% |
| TRX | +9.13 | 48 | 37.5% | -27.50% (only positive) |

## Feature Importance — funding_rate_zscore_30 RANK

| Symbol | Rank | Importance | % of top feature |
|--------|------|------------|------------------|
| BCH | **13/14** | 23.0 | 24.0% (vs top vwap_dev_20 = 96.0) |
| LDO | **14/14** | 4.0 | 3.7% (vs top ret_kurt_50 = 107.0) — near-zero |
| TRX | **14/14** | 29.0 | 22.8% (vs top ema_spread_atr_20 = 127.0) |
| Portfolio | **14/14** | 56.0 | 22.1% (vs top ret_kurt_50 = 253.0) |

**Falsifier 4 fires**: rank ≤7 (top half) NOT achieved on any symbol. PATH B (PROMISING-INERT-still) condition: rank 14/14 strictly satisfied on 2 of 3 symbols (LDO, TRX, Portfolio) and BCH at 13/14 is in bottom-quartile (positions 11-14). Spirit of brief §4.4 PATH B fires.

## Critical Finding — INERT-OVERFIT Pattern

The funding rate is INERT (model demonstrably doesn't split on it meaningfully) AT BOTH n_trials=10 AND n_trials=35. This disambiguates iter-v3/019: the feature is genuinely informationally insufficient for v3's per-symbol LightGBM architecture, NOT a budget-constraint artifact.

But unlike iter-v3/019 (which had POSITIVE OOS lift +0.78 from single-seed lottery), iter-v3/023 produces OOS Sharpe **-1.07** — collapsing 1.85 units. Mechanism:
- At n_trials=10 (iter-v3/019), Optuna found a "lucky" hyperparam trajectory that produced positive OOS by chance
- At n_trials=35 (iter-v3/023), Optuna's larger search found IS-optimal hyperparams that overfit to noise INCLUDING the INERT funding feature, producing OOS overfit
- The IS Sharpe lift +0.15 at n=35 is actually LESS than n=10's +0.78 — confirming higher search converged to less-overfit IS but still doesn't generalize OOS

**This is NEGATIVE-OVERFIT-ON-INERT-FEATURE** — a hybrid mode. Adding an INERT feature to V3_FEATURE_COLUMNS gives Optuna more degrees of freedom to overfit IS, hurting OOS.

## §4.4 Classification Recommendation

**EXPLORATION-NEGATIVE (clean)** — OOS Sharpe collapse -1.46 vs anchor is the binding constraint. PATH B (PROMISING-INERT-still) condition partially fires (rank 14/14 across LDO+TRX+Portfolio; BCH 13/14) but PATH C (NEGATIVE: IS Sharpe Δ < -0.10) doesn't fire (IS Δ is +0.15). The OOS collapse drives the verdict to NEGATIVE despite IS being marginally positive.

**Funding axis is now permanently CLOSED**:
- iter-v3/019 PROMISING-INERT at n_trials=10 (lottery-positive)
- iter-v3/023 NEGATIVE at n_trials=35 (overfit-negative)
- Both confirm feature is INERT in importance
- The combination demonstrates NO budget can rescue this feature for v3's 13-feature/per-symbol-LightGBM architecture

## Recommendations

iter-v3/024 axis options (Critic decides):
- **DSR gate reformulation** (MEDIUM #5): DSR > 0.95 is mathematically blocked at v3's trade volume; reformulate to DSR > 0 OR n_trials reduction. PROCESS fix.
- **Try ATOMUSDT alone** as universe expansion (HBAR+AVAX axis tried; FILUSDT/ALGOUSDT untested). HIGH-priority axis #2b sub-axis.
- **Different feature category**: NEW labeling architecture other than triple-barrier (Category 3 untested in post-bootstrap cycle).
- **Hurst threshold tuning**: knob axis (LOW priority but might surface a quick win).
