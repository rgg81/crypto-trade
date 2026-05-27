# Phase 6.0 Critic Pre-Flight — iter-v1/025

OVERALL: BLOCK — 2 isolated implementation defects (D1 + D2) prevent valid backtest

## Pre-Flight Checks

### Check 1 — Brief Look-Ahead Audit: PASS
`open_interest_v1.py:128-135` past-only `.shift(delta_window)` + `.shift(1)` on rolling stats. No forward-window aggregation. EDA IS-only.

### Check 13 — Anti-Pattern Static Scan: PASS (with 2 dispatch-wiring defects)
A1-A13 all clean. `walk_forward.py:113` unchanged. `labeling.py` untouched.

But 2 uncatalogued dispatch defects:

### DEFECT D1 — `open_interest_v1` not registered in features GROUP_REGISTRY
`src/crypto_trade/features/__init__.py:180-189` registers 10 groups including funding_v1 at line 189, but NO `_register("open_interest_v1", _add_oi_delta_v1_features)` line and NO import statement.

Consequence: `crypto-trade features --track v1 --groups open_interest_v1` will REJECT the argument. At backtest launch:
- Feature parquets won't contain `oi_delta_30_z90` column → KeyError OR silent NaN-fill
- F-AXIS #1 DUAL GATE structurally undefined
- Runtime assert at run_baseline_v1.py:2055 only checks SOURCE CSVs, not regenerated parquets → false-PASS handoff

### DEFECT D2 — Section 3.6 skip-month NaN policy missing
Brief Section 3.1 + 3.6 + LM Master §5(a) ADOPTED commit to: "when symbol's training-window slice has >50% NaN oi_delta_30_z90, exclude symbol from that month's training fold". Grep returns ZERO matches for `nan_frac`, `>50% NaN`, `oi_delta_30_z90.isna().mean() > 0.5` patterns. Only `n_skip_month_fallback` matches are from /024's RegimeRoutedStrategy (different mechanism).

Consequence: 2020-01→2020-09 pre-OI-archive NaN window passed verbatim to LightGBM → curve-fit hazard exactly as Section 3.1 sought to prevent ("LightGBM cannot synthesize a (symbol × NaN_indicator) interaction").

### Foundation Regression: PASS
walk_forward.py:113 carries embargo subtraction. 4 mandated regression tests present.

### Cadence + Axis Sanity: PASS
phase5p5_gate.md OVERALL=PASS at `6f14720`. Family `feature-family` 1-of-5 (not 5-of-5); rotation discipline does NOT fire. /024 Critic Path Forward #1 explicitly permitted 2-consecutive feature-family when NEW data class.

### Falsifier Presence: PASS
F1 bands explicit (PROMISING ≥+0.10, INERT (-0.10, +0.10), NEG-clean [-0.55, -0.10), NEG-CAT ≤-0.55). F-AXIS #1 DUAL GATE 3-sub-gate structure. F3 IS auto-reject ≤-0.30.

### OI Coverage: 3/5 PASS LM Master HARD BLOCK
BTC 6253 / ETH 4915 / LINK 4915 IS rows. LTC + DOT still fetching. Threshold ≥3/5 met.

### Track Isolation: PASS
Zero `features_v2` / `features_v3` imports in `open_interest_v1.py`.

### V1_FEATURE_COLUMNS_PRUNED 43: PASS
Assert at `features_v1/__init__.py:138`. `oi_delta_30_z90` at line 110 alphabetical position.

## Defect Summary

| ID | Defect | Severity | Required Fix |
|---|---|---|---|
| D1 | open_interest_v1 not registered in features GROUP_REGISTRY | BLOCKING | Add `_register("open_interest_v1", _add_oi_delta_v1_features)` line after line 189 in `src/crypto_trade/features/__init__.py` + corresponding import |
| D2 | Skip-month NaN policy missing | BLOCKING | Add per-(symbol, month) NaN-fraction guard in `_train_for_month` (or runner wrapper); exclude symbol from training fold when `oi_delta_30_z90.isna().mean() > 0.5`. Must NOT affect /023 funding cols (full IS coverage). Emit per-fold skip count in `oi_coverage_check.csv`. |

## Path Forward

QE re-implements D1 + D2 + Phase 6.0 RE-REVIEW. Both fixes are isolated implementation gaps — brief hypothesis and methodology unchanged. Primary path.

Alternative axes if implementation cannot be salvaged (families NOT in prior 5):

1. **Meta-labeling on /021 trade roster** — family `labeling`. Secondary classifier predicts trade win/loss; threshold-gate entries by meta-prob. AFML Ch. 3 pattern.

2. **DOT-specific drawdown brake** — family `risk-primitive`. Per-symbol drawdown brake gated by DOT funding-z regime.

3. **Universe expansion: provisional SOLUSDT Model F** — family `universe`. Denominator expansion test.

Forward-looking only if QE fix path exhausted.
