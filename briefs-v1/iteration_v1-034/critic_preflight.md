# Phase 6.0 Critic Pre-Flight — iter-v1/034

OVERALL: PASS

## Pre-Flight Checks

### Check A — Brief Look-Ahead Audit: PASS
Brief Section 1 cites IS-only EDA from `analysis/iteration_v1-034/` (8 files at `1436ef8`). Past-only invariant declared and implemented: `basis_bps[t]` uses bar-close perp + spot (knowable at bar t close); rolling denominator uses `.shift(1)` so bar t's own basis_bps does NOT enter bar t's rolling stats.

### Check B — Dispatch defect + Mini-Check J: PASS
`"v1-034"` in catch-all exclusion tuple at `run_baseline_v1.py:3492`. /034 elif at line 3399 < catch-all at 3482. F-AXIS #1 hard-assert at line 3406 verifies `"basis_zscore_30" in active_feature_columns`. Universe guard `set(symbols) == set(V1_BASELINE_UNIVERSE)`.

### Check C — basis_zscore_30 wiring: PASS
`features_v1/basis_v1.py:142` carries `(perp_close - spot_close_safe) / spot_close_safe * 10_000`. Line 149 applies `.shift(1)` before rolling. Clip ±10.0 at line 157. Zero-std guard at line 154. Spot data from `data/spot/<SYM>/8h.csv`. Registered in `features/__init__.py:209`; inserted at pos 0 in V1_FEATURE_COLUMNS_PRUNED; assertion `len == 44` at `features_v1/__init__.py:140`.

### Check D — Configuration sanity: PASS
ENSEMBLE_SIZE=3, n_trials=18, single outer seed=42, sample_weight_mode=abs_pnl (baseline), bounds_profile=v1_pruned (not axis016). All 4 models A/C/D/E preserve baseline atr/R-gate settings.

### Check E — Test suite: PASS
12 tests committed (8+ mandate): 6 in test_basis_v1.py (past_only / known_values / clip / burn_in / missing_spot / btc_smoke) + 6 in test_iteration_v1_034.py (banner / catchall / dispatch / basis_in_pruned / pruned_length_44 / foundation_regression).

### Check F — Anti-pattern static scan: PASS
A1-A14 all clean. walk_forward.py:113 carries embargo subtraction. Track isolation preserved (zero v2/v3 imports in basis_v1.py).

### Mini-Check K — Strategy attribute symmetry: PASS
Pure feature-add; no wrapper/gate primitives; no wrapper-vs-strategy attribute mismatch surface area.

### Mini-Check L — Wall-clock plausibility: PASS
Modal projection 60-80 min (anchor /016 50 min + 1.02× scaling + 5 min feature regen). Inside 2h target with margin.

## Approved Launch Invocation

```bash
# Step 0 — regenerate basis_v1 feature group on all 5 baseline symbols
uv run crypto-trade features \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT \
  --interval 8h --track v1 --groups basis_v1 --format parquet --workers 4

# Step 1 — pre-flight tests must all pass
uv run pytest tests/features_v1/test_basis_v1.py tests/test_iteration_v1_034.py -v

# Step 2 — backtest launch
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --pruned-features --iteration-label v1-034 \
  --exploration --n-trials 18 --ensemble-size 3 --seeds 42 \
  > logs/iter_v1_034_backtest.log 2>&1
```

Phase 6 backtest launch AUTHORIZED.
