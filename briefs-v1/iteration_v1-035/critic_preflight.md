# Phase 6.0 Critic Pre-Flight — iter-v1/035

OVERALL: PASS

## Pre-Flight Checks

### Check A — Brief Look-Ahead Audit: PASS
Trend-scanning primitive at `labeling.py:132-214` reads `close_arr[sym_idx[pos+1 .. pos+max_h]]` — strictly forward bars (intentional at LABEL TIME), properly anchored at TRAINING TIME via `walk_forward.py:113`. Hard-causality regression test at `test_trend_scanning_label_mode.py:132`. EDA uses OOS_CUTOFF gate (IS-only).

### Check B — Dispatch defect + Mini-Check J: PASS
- /035 elif at run_baseline_v1.py:3505 fires BEFORE catch-all at 3594
- `"v1-035"` in catch-all exclusion tuple at 3605
- Pre-flight assert at 3516: `assert label_mode_arg == "trend_scanning"`

### Check C — Trend-scanning wiring: PASS
`--label-mode` CLI flag → `label_mode_arg` → `_r5_kwargs` → `run_model()` → `LightGbmStrategy(label_mode=...)` → `label_trades(label_mode=...)` → short-circuit to `_trend_scan_label` at labeling.py:398-407.

### Check D — Configuration sanity: PASS
ENSEMBLE_SIZE=3, n_trials=18, single outer seed=42. HIGH-RISK declared with single-seed OPT-OUT rationale + multi-seed CONFIRMATION at /044 mandate if PROMISING.

### Check E — Test suite: PASS
9 new tests at test_iteration_v1_035.py + 8 existing trend-scanning tests + foundation regression intact. /027 LESSON real LightGbmStrategy test (lines 122-148). /030 LESSONS catch-all + banner present.

### Check F — Anti-pattern static scan A1-A14: PASS
A1 `walk_forward.py:113` carries embargo subtraction. A2-A14 clean. Track isolation preserved.

### Mini-Check K — Strategy attribute symmetry: PASS
`label_mode` consistent name across CLI → run_model → LightGbmStrategy → label_trades.

### Mini-Check L — Wall-clock plausibility: PASS
Modal ~60 min (anchor /034 55 min × 1.0× scaling factor). Inside 2h target with margin. No kill-switch per cycle-5 directive.

## Approved Launch Invocation

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --pruned-features --iteration 35 --exploration \
  --n-trials 18 --ensemble-size 3 --seeds 1 \
  --label-mode trend_scanning \
  > logs/v1_iter035.log 2>&1
```

Phase 6 backtest launch AUTHORIZED.
