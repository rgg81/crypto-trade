# Phase 6.0 Critic Pre-Flight — iter-v1/036

OVERALL: PASS

## Pre-Flight Checks

### Check A — Look-Ahead Audit: PASS
Trend-scanning forward 21-bar window past-only at training time via `walk_forward.py:113` embargo subtraction. No new feature module. V1_FEATURE_COLUMNS_PRUNED UNCHANGED. A1-A14 clean.

### Check B — Dispatch defect + Mini-Check J: PASS
- `v1-036` in catch-all exclusion tuple at line 3692
- /036 elif at line 3595 fires BEFORE catch-all at 3680
- F-AXIS hard-asserts at 3655-3664 use REAL `TradeResult.symbol`

### Check C — 2-model dispatch wiring: PASS
V1_ITER036_UNIVERSE = ("LINKUSDT", "DOTUSDT") at `features_v1/__init__.py:209`. Dual guard (iteration_label + universe set). Pre-flight `assert label_mode_arg == "trend_scanning"` at line 3604. ONLY Model C' (LINK) + Model E (DOT) dispatched.

### Check D — Configuration sanity: PASS
ENSEMBLE_SIZE=3, n_trials=18, single outer seed=42. HIGH-RISK 2-mechanism stack declared.

### Check E — Test suite: PASS
11 new tests + 8 existing trend-scanning tests pass. /027 LESSON real LightGbmStrategy. /030 LESSONS catch-all + banner.

### Check F — Anti-pattern A1-A14: PASS

### Mini-Check K — Strategy attribute symmetry: PASS

### Mini-Check L — Wall-clock plausibility: PASS
~25 min modal (0.4× cohort-coverage scaling vs /034 50 min anchor).

## Approved Launch Invocation

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --pruned-features --iteration 36 --exploration \
  --n-trials 18 --ensemble-size 3 --seeds 1 \
  --label-mode trend_scanning \
  --symbols LINKUSDT,DOTUSDT \
  > logs/v1_iter036.log 2>&1
```

Phase 6 backtest launch AUTHORIZED.
