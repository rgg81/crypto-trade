# Phase 6.0 Critic Pre-Flight — iter-v1/033

OVERALL: PASS

## Pre-Flight Checks

### Check A — Look-ahead Audit: PASS
Brief Section 1 (1.1-1.4) sources from `analysis/iteration_v1-033/` committed at `f433f6b` plus prior iteration reports. Per-symbol OOS attribution in 1.2 references /018 LINK +0.9789, /019 ETH +0.6990, /028 LTC +0.331, /032 axis-only +0.21 — all from prior iteration commit history. Sections 1+1.5+2 cite IS-only EDA for design. composite_inv_concurrency past-only constraint verified at /031.

### Check B — Dispatch Defect Static Scan + Mini-Check J: PASS
Catch-all exclusion tuple at `run_baseline_v1.py:3404-3414` includes `"v1-033"` (line 3413). /033 elif at line 3225 fires BEFORE catch-all (positional ordering verified). F-AXIS #1 hard-asserts (lines 3366-3378) use ONLY `r.symbol` — zero `r.model_name` references. /027 LESSON inherited.

### Check C — Bundle Wiring Correctness: PASS
All 5 models receive `sample_weight_mode="composite_inv_concurrency"` (lines 3266, 3282, 3298, 3315, 3355). Model D' uses `atr_sl=1.0` (line 3291). Model G's BTC-trend gate fires with `lookback_bars=42, threshold_pct=8.0` (matches /019). `apply_btc_trend_filter` called POST-Optuna on Model G results. Model A REPLACEMENT-SEMANTICS: `results_a_btc_only` filtered by `.symbol == "BTCUSDT"` (line 3360).

**NOTE (non-blocking documentation drift)**: Brief Section 3.1 ATR table shows `A=3.0/1.75, C'=3.5/1.75, G=3.0/1.75, E=3.0/1.75`. Runner authoritative values: `A=2.9/1.45, C'=2.9/1.45, G=2.9/1.45, E=2.9/1.45, D'=3.5/1.0`. Documentation drift only — runner is correct. Surfaced as Phase 7 advisory.

### Check D — Configuration Sanity: PASS
ENSEMBLE_SIZE=10 (CONFIRMATION standard), n_trials=35 (CONFIRMATION default), CONFIRMATION-EXCEPTION 12h cap declared with user authorization 2026-05-29 + 5-step scaling justification (9.8h modal). 5-model dispatch order A → C' → D' → G → E.

### Check E — Test Suite: PASS
14 tests in `test_iteration_v1_033.py`. Test 8 (`test_bundle_iter33_real_trade_result_assertion`) constructs REAL TradeResult instance and asserts `.symbol` exists, `.model_name` does not — codifies /027 LESSON. Tests 1+2: catch-all exclusion + dispatch banner (/030 LESSON). Tests 9-11: atr_sl=1.0 + BTC-trend gate + composite_inv_concurrency count.

### Check F — Anti-Pattern Static Scan (A1, A2, A3, A5): PASS
- A1: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`. Zero raw matches without subtraction.
- A2: Zero forward-window std in `labeling.py`.
- A3: Zero `fit_transform/StandardScaler/MinMaxScaler` in `src/crypto_trade/strategies/ml/`.
- A5: 4 mandated lookahead tests present at `tests/test_lookahead_embargo.py` (lines 120/171/248/277).

QE setup diff does NOT touch foundation files. iter-v3/057 fix preserved.

### Mini-Check J — Catch-all guard ordering: PASS
/033 elif (line 3225) < catch-all (line 3404). `"v1-033"` in exclusion tuple (line 3413). Double-guard intact.

### Mini-Check K — Strategy Attribute Symmetry: PASS
F-AXIS #1 hard-asserts (lines 3372-3378) use ONLY `r.symbol`. /027-class wrapper attribute mismatch impossible.

### Mini-Check L — Wall-clock Estimate: PASS
Scaling factor 1.40× (10/5 inner × 35/50 trials × 1 outer × 1.0 labels) × 7h precedent = 9.8h modal. Kill-switch 10h gives 2h safety margin within 12h CONFIRMATION-EXCEPTION cap.

### Foundation Regression: PASS
`walk_forward.py:113` carries embargo subtraction. QE commit `3abbfc0` does NOT touch foundation files.

### Cadence + Axis Sanity: PASS
Brief Section 0.6 declares `confirmation-bundle` family. CONFIRMATIONs exempt from Axis Rotation. 15 EXPLORATION precedents across cycles 3+4. LM Master Phase 4.5 USER-DIRECTIVE-WAIVED per gate file (non-blocking, user authorized 2026-05-29 "Let's go A").

### Falsifier Presence: PASS
F1 OOS Sharpe Δ ≥ +0.336 for CONFIRMATION-MERGE (absolute ≥ +1.00). F2 trade-count [600, 1100]. F3 per-cohort sign ≥3/5. F4 n_eff ∈ [10, 25]. F5 OOS TP-exit ≥ 15 LOAD-BEARING.

---

## Approved Launch Invocation

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --confirmation \
  --iteration 33 \
  --n-trials 35 \
  --ensemble-size 10 \
  --pruned-features \
  --sample-weight-mode composite_inv_concurrency \
  --no-engineering-report \
  > logs/v1_iter033.log 2>&1
```

Wall-clock budget: 12h CONFIRMATION-EXCEPTION cap (user-authorized 2026-05-29). Kill-switch 10h. Month-boundary `[wall_clock]` logging per brief Section 3.3.

## Path Forward
N/A — OVERALL=PASS. Surface ATR table drift to QR at Phase 7 (advisory).

Phase 6 backtest launch AUTHORIZED.
