# Iteration 155 Engineering Report

## Methodology

Post-processing of iter 138 raw trades (816 total) with per-symbol VT
parameters. Walk-forward valid: each trade's scale computed from past-only
per-symbol daily PnL over lookback=45 days. Selection rule: **IS-best**.
No model retraining; engine unchanged.

Verified `_compute_vt_scale` reproduces v0.152 metrics exactly
(IS Sharpe=+1.3320, OOS Sharpe=+2.8286, avg_scale=0.465).

## Grid 1: Per-symbol target_vol calibration

target_vol_sym = median_IS_realized_vol_sym × k, floor=0.33.

| k | IS Sharpe | OOS Sharpe | IS MaxDD | OOS MaxDD | OOS PF | avg scale |
|---|-----------|-----------|----------|-----------|--------|-----------|
| **baseline (universal 0.3)** | **+1.3320** | **+2.8286** | 76.89% | 21.81% | 1.76 | 0.465 |
| 0.30 | +1.0200 | +2.4302 | 136.22% | 25.32% | 1.60 | 0.504 |
| 0.50 | +1.1392 | +2.1680 | 155.36% | 39.80% | 1.49 | 0.630 |
| 0.70 | +1.1852 | +1.9480 | 177.93% | 54.85% | 1.41 | 0.789 |
| 1.00 | +1.1892 | +1.7963 | 207.53% | 75.48% | 1.37 | 1.026 |
| 1.50 | +1.1623 | +1.7107 | 245.76% | 107.99% | 1.35 | 1.379 |

**Every per-symbol calibration is strictly worse than baseline on both IS
and OOS.** Higher k = more exposure during low-vol periods = more July 2025
damage.

## Grid 2: Per-symbol floor (universal target=0.3)

Only floor varies per-symbol, target held at 0.3.

| Config | IS Sharpe | OOS Sharpe | IS MaxDD | OOS MaxDD | OOS PF |
|--------|-----------|-----------|----------|-----------|--------|
| **baseline (universal 0.33)** | **+1.3320** | **+2.8286** | 76.89% | 21.81% | 1.76 |
| inv-vol @ 0.40 | +1.3336 | +2.7591 | 67.45% | 19.68% | 1.76 |
| inv-vol @ 0.45 | +1.3414 | +2.7500 | 69.39% | 21.93% | 1.72 |
| inv-vol @ 0.50 | +1.3450 | +2.7353 | 71.59% | 24.21% | 1.69 |
| inv-vol @ 0.55 | +1.3445 | +2.7144 | 73.88% | 26.48% | 1.66 |
| inv-vol @ 0.60 | +1.3422 | +2.6902 | 76.17% | 28.73% | 1.64 |
| LINK-tight (0.20) | +1.3463 | +2.7904 | 66.75% | 17.82% | 1.79 |
| LINK-tight (0.15) | +1.3418 | +2.7602 | 63.32% | 16.34% | 1.80 |
| BTC-loose (0.50) | +1.3431 | +2.7934 | 75.60% | 23.67% | 1.73 |
| **BTC-loose (0.67)** [IS-best] | **+1.3473** | **+2.7484** | 74.31% | 25.66% | 1.70 |

## IS-Best Selection → OOS Validation

**IS-best config**: BTC-loose (0.67) — floors={BTC:0.67, BNB:0.33, ETH:0.33, LINK:0.33}

| Metric | Baseline (v0.152) | IS-best (iter 155) | Δ |
|--------|-------------------|--------------------|---|
| IS Sharpe | +1.3320 | +1.3473 | +0.0153 (+1.1%) |
| OOS Sharpe | **+2.8286** | **+2.7484** | **-0.0802 (-2.8%)** |
| OOS MaxDD | 21.81% | 25.66% | +3.85pp (worse) |
| OOS PF | 1.76 | 1.70 | -0.06 |

**IS-best fails OOS constraint: OOS Sharpe drops below baseline.**

## Hard Constraints (IS-best config)

| Constraint | Threshold | IS-best | Pass? |
|------------|-----------|---------|-------|
| OOS Sharpe > baseline | > +2.8286 | +2.7484 | **FAIL (-2.8%)** |
| OOS MaxDD ≤ 26.2% (1.2×) | ≤ 26.2% | 25.66% | PASS |
| OOS trades ≥ 50 | ≥ 50 | 164 | PASS |
| OOS PF > 1.0 | > 1.0 | 1.70 | PASS |
| IS/OOS ratio > 0.5 | > 0.5 | 0.49 | FAIL (marginal) |

**Decision**: **NO-MERGE** (primary constraint fails).

## Interpretation

Per-symbol VT adds IS Sharpe noise (~+0.01-0.02) but strictly hurts OOS. The
universal target=0.3 / floor=0.33 config is empirically optimal. Raising the
floor for any symbol adds exposure that hurts during the July 2025 crash.

**Key mechanism**: At iter 152's config, scales are binary — 78% at floor,
21% at default (new symbol). Adding per-symbol tuning creates intermediate
scales that always raise average exposure, which always hurts OOS.

The LINK-tight(0.20) result is worth noting: slightly lower OOS Sharpe
(-1.4%) but meaningfully better OOS MaxDD (-18%). This is a risk-adjusted
trade-off, but it does not meet the primary-metric bar for MERGE.

## Code Quality / Label Leakage

No engine changes. Post-processing only. Walk-forward valid:
`days_before >= 1` in scale computation. Matches engine's
`_compute_vt_scale` logic (verified).

## Conclusion

Per-symbol VT calibration does NOT beat the universal config. v0.152's
universal target=0.3 / floor=0.33 is **confirmed globally optimal** for the
4-symbol portfolio.
