# Iteration 156 Engineering Report

## Methodology

Post-processing meta-labeling on iter 138's 816 trades. LightGBM classifier
(100 trees, depth=4, leaves=15, class_weight=balanced, seed=42) trained on
8 meta-features, walk-forward monthly refit. Trained only on CLOSED IS
trades before current month. No primary model retraining. Seed=42.

Meta-features (all walk-forward valid):
1. Traded-symbol NATR_21, ADX_14, RSI_14 at open_time
2. BTC NATR_21 at open_time
3. direction (-1/+1)
4. hour_of_day (0/8/16 UTC)
5. rolling_10trade_WR (per symbol, from past closed trades)
6. days_since_last_trade (per symbol)
7. symbol_index (0-3)

NaN fraction: 0.0% (all features populated). Base rate of profitable IS
trades: 44.5%.

Warmup: 100 closed trades required before meta-model fits. First 101 trades
(all IS) kept regardless. Total meta-predicted trades: IS=551, OOS=164.

## Baseline (v0.152, no meta-filter)

| Metric | IS | OOS |
|--------|-----|-----|
| trades | 652 | 164 |
| Sharpe | +1.3320 | +2.8286 |
| MaxDD | 76.89% | 21.81% |
| PF | — | 1.76 |

## Threshold Grid (meta-filter + VT scaling)

| thresh | IS n | OOS n | IS Sharpe | OOS Sharpe | IS MaxDD | OOS MaxDD | OOS PF |
|--------|------|-------|-----------|-----------|----------|-----------|--------|
| 0.40 | 459 | 122 | +0.8338 | +2.5923 | 76.89% | 18.03% | 1.87 |
| 0.45 | 391 | 100 | +0.6973 | +2.8150 | 76.89% | 12.23% | 2.06 |
| **0.50** | **320** | **83** | **+0.7134** | **+3.2606** | 76.89% | **8.78%** | **2.63** |
| 0.52 | 294 | 74 | +0.5517 | +2.7984 | 76.89% | 13.19% | 2.45 |
| 0.55 | 257 | 58 | +0.3721 | +2.8028 | 76.89% | 11.91% | 2.57 |
| 0.58 | 217 | 45 | +0.4635 | +2.5280 | 76.89% | 11.04% | 2.61 |
| 0.60 | 204 | 37 | +0.2768 | +2.3676 | 76.89% | 11.04% | 3.00 |

## Alt Grid: Meta-filter WITHOUT VT (scale=1)

| thresh | IS Sharpe | OOS Sharpe | OOS MaxDD | OOS PF |
|--------|-----------|-----------|-----------|--------|
| 0.40 | +0.5844 | +2.4183 | 42.34% | 1.65 |
| 0.45 | +0.4209 | +2.5412 | 33.77% | 1.77 |
| 0.50 | +0.3431 | +2.6246 | 26.61% | 1.91 |
| 0.55 | +0.0436 | +1.9939 | 36.09% | 1.76 |
| 0.60 | -0.2336 | +1.7081 | 22.63% | 1.88 |

Without VT, meta-filter is strictly worse. **VT and meta-labeling are
complementary** — VT protects during crashes, meta-filter removes weaker
trades.

## IS-Best Selection → OOS Validation

**Walk-forward-valid selection rule**: max IS Sharpe with ≥ 150 IS trades.

IS-best: **thresh=0.40**.

| Metric | Baseline (v0.152) | IS-best (iter 156) | Δ |
|--------|-------------------|--------------------|---|
| IS Sharpe | +1.3320 | +0.8338 | **-0.498 (-37%)** |
| OOS Sharpe | **+2.8286** | **+2.5923** | **-0.236 (-8.3%)** |
| OOS MaxDD | 21.81% | 18.03% | -17% (improvement) |
| OOS PF | 1.76 | 1.87 | +6% (improvement) |
| OOS Calmar | 5.46 | 5.13 | -6% |
| OOS PnL | +119.1% | +92.5% | -22% |
| OOS trades | 164 | 122 | -26% |

**IS-best fails primary OOS Sharpe constraint.**

## Hard Constraints (IS-best)

| Constraint | Threshold | Actual | Pass? |
|------------|-----------|--------|-------|
| OOS Sharpe > baseline | > +2.83 | +2.59 | **FAIL (-8.3%)** |
| OOS MaxDD ≤ 38.7% | ≤ 38.7% | 18.03% | PASS |
| OOS trades ≥ 50 | ≥ 50 | 122 | PASS |
| OOS PF > 1.0 | > 1.0 | 1.87 | PASS |
| IS/OOS ratio > 0.5 | > 0.5 | 0.32 | **FAIL (marginal worse)** |

**Decision: NO-MERGE** (primary constraint fails).

## Diagnostic: Why Does Meta-Filter Hurt IS Sharpe?

Every threshold catastrophically reduces IS Sharpe (1.33 → 0.28-0.83). The
meta-model trained on IS does NOT identify profitable IS trades well — it
drops as many winners as losers, and the timing degrades.

Yet meta-filter dramatically IMPROVES OOS MaxDD at every threshold (down to
8.78% at 0.50, vs 21.81% baseline). OOS PF improves in every config. The
meta-model has OOS-relevant patterns it doesn't have for IS.

**Interpretation**: The meta-model learned regime/feature patterns that
happen to map well to OOS's July 2025 crash period but don't generalize
within IS (2020-2025 Q1). This is classic look-ahead illusion of the
**OOS-best** result (thresh=0.50, Sharpe +3.26).

## Meta-Feature Importance (top 5)

(would require refitting on full IS — not done here; skip for brevity)

## Walk-Forward Correctness

- Meta-training uses only trades with close_time < current open_time
- Monthly refit cadence (no per-trade refit)
- LightGBM has no feature leakage within its own training (standard)
- VT scales computed as in iter 152 (per-symbol, past-only daily PnL)

## Conclusion

Meta-labeling with 8 meta-features does not beat baseline under
walk-forward-valid IS-best selection. The **OOS-best result (thresh=0.50,
OOS Sharpe +3.26)** is a look-ahead artifact and cannot be claimed.

Future work: adding `primary_confidence` as a meta-feature (requires
re-running iter 138 model to capture probabilities) may provide the
decisive signal. Also consider CV-based threshold selection via nested
walk-forward.
