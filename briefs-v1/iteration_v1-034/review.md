# Phase 7.5 Critic Review — iter-v1/034

OVERALL: **EXPLORATION-NEGATIVE** (clean LEARNED-NEG; OOS Δ -0.27 vs BASELINE_V1 +0.6637)

## Iteration Type
TYPE: EXPLORATION cycle-5 #1/10 — feature-family axis (basis_zscore_30 NEW feature; perp-spot data class NOT derivable from OHLCV)

## Observed results

| Metric | Baseline | /034 | Δ |
|---|---|---|---|
| IS Sharpe | +0.2829 | -0.0057 | -0.29 |
| OOS Sharpe | +0.6637 | **+0.3935** | **-0.27** |
| OOS WR | 40.2% | 37.3% | -2.9pp |
| OOS Trades | 189 | 261 | +72 |
| OOS Max DD | 40.94% | 48.74% | +7.8pp |
| OOS PSR_vs_0 | 0.989 | 0.618 | -0.37 |
| OOS PSR_vs_1 | 0.079 | 0.236 | +0.16 |
| n_eff_per_cell median | n/a | 9 | (healthy) |

**Per-symbol OOS — ALL 5 NEGATIVE:**
| Symbol | Trades | WR | Net PnL% | Baseline OOS |
|---|---|---|---|---|
| BTC | 54 | 31.5% | -3.24% | +33.17% (catastrophic regression -36.4pp) |
| ETH | 56 | 35.7% | -9.42% | +2.75% |
| LINK | 48 | 39.6% | **-23.80%** | +34.23% (catastrophic regression -58.0pp) |
| LTC | 48 | 41.7% | -5.38% | -47.25% (slight improvement) |
| DOT | 54 | 38.9% | -15.05% | +1.96% |

**basis_zscore_30 feature importance:**
- Model A pool: rank 25 / gain 359.76
- Model C LINK: rank 29 / gain 105.62
- Model D LTC: rank 32 / gain 176.29
- Model E DOT: rank 26 / gain 260.13
- Portfolio: rank 27 / gain 901.79

Feature was LEARNED (mid-pack importance) but did NOT generalize to OOS.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
basis_zscore_30 uses `.shift(1)` past-only constraint. Foundation `walk_forward.py:113` embargo intact.

### Check 2 — Embargo Width: PASS

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (EXPLORATION)
DSR -50.99 / PSR_vs_1 0.236. Not BLOCK-triggering for EXPLORATION.

### Check 4 — IC Correlation: PASS
basis_zscore_30 max |Pearson| with existing 43 features = -0.371 (within informative band; not redundant).

### Check 5 — ADF Stationarity: PASS
basis_zscore_30 strongly stationary (ADF p < 1e-30 all 5 syms).

### Check 6 — Pareto: N/A (single seed)

### Check 7 — Reproducibility: PASS
HEAD `1be3bd1`. Seed=42 / ENSEMBLE_SIZE=3 / n_trials=18 / 44 features.

### Check 8 — Hypothesis-Implementation Alignment: PASS
H1 (basis adds OOS lift) → REFUTED by observation but implementation matched design 1:1.

### Check 13 — Anti-Pattern Static Scan: PASS

### Check 14 — Axis Family Validation: PASS
`feature-family` axis. Rotation VALID (last feature-family /025; >8 EXPLORATIONs gap).

## Verdict Cell

Per brief Section 4 verdict matrix:
- F1 OOS Sharpe Δ -0.27 → **EXPLORATION-NEGATIVE** (Δ ∈ [-0.55, -0.20] band; clean LEARNED-NEG not catastrophic)

## Structural Finding

**3rd consecutive LEARNED-NEGATIVE at single-seed Pool Model A** with NEW feature added:
- /023 funding z-score: Δ -0.20 OOS (LEARNED-NEG clean)
- /025 OI level z-score: Δ -1.40 OOS (LEARNED-NEG-CAT)
- **/034 basis z-score: Δ -0.27 OOS (LEARNED-NEG clean)**

All 3 NEW feature families learned (rank 4-32 importance) but OOS catastrophic or negative. Confirms `feedback_v1_pool_a_new_feature_lneg.md`: v1 Pool Model A + single-seed + n_trials=18 EXPLORATION budget STRUCTURALLY REJECTS NEW feature families.

## Path Forward

Per cycle-5 menu execution order, next axis is:
- **/035** = Open-interest velocity (orthogonal to /025 OI level)

Sample-weighting wrapper (/031) is the ONLY non-Pool-A axis class that produced PROMISING in v1; specialist isolation (/018 LINK, /028 LTC+atr_sl) also works. Pure Pool-A feature additions are structurally rejected — this is now n=3 confirmed.

**Critic recommendation**: cycle-5 should pivot away from "add 1 feature to pool" axes. The remaining Wave 1 candidates (/035 OI velocity, /036 funding velocity, /037 volume imbalance, /038 on-chain) face the same Pool-A-feature-addition risk. Consider testing as PER-COHORT specialist features instead, OR jumping to Wave 2 (label changes) and Wave 3 (risk primitives) which test different mechanisms.

## NO-MERGE

BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` `f8bc12c`. /034 closed; advance to /035.

Tag: v0.v1-034 at closeout.
