# Phase 6.0 Critic Pre-Flight — iter-v1/031

OVERALL: PASS

## Pre-Flight Checks

### Check A — Brief Look-Ahead Audit: PASS
Brief Sections 1, 1.5, 2 cite IS-only numerical evidence from committed CSVs at `0cff4b8`. No OOS contamination in EDA. The /016 PRIOR (Section 1.5) is historical reference, not a label/feature input. Brief Section 3.3 documents explicit past-only constraint for `c_at_entry(t)`. LM Master advisor carries no OOS leak.

### Check B + Mini-Check J — Dispatch graph integration smoke test: PASS
- `v1-031` is in baseline catch-all exclusion tuple at line 2802 (alongside v1-021/023/024/025/027/030)
- /031 elif at line 2707 fires BEFORE catch-all (line 2795)
- Runtime asserts (lines 2718-2728) cross-verify universe, feature count (43), and sample_weight_mode_arg pre-dispatch — silent fallback signature impossible by construction

### Check C — Sample-weighting wiring correctness: PASS
End-to-end weight propagation verified:
- CLI: `--sample-weight-mode` argparse choices include `composite_inv_concurrency`
- Threaded into `_r5_kwargs` → all 4 `run_model()` calls in /031 elif
- `LightGbmStrategy.__init__` accepts + validates mode (one of {abs_pnl, uniform, uniqueness_only, composite_inv_concurrency})
- Dispatch branch at `lgbm.py:676-708` calls `compute_composite_inv_concurrency_weights(...)`
- `train_weights` flows into `optimize_and_train(sample_weights=train_weights, ...)`
- LightGBM `model.fit(..., sample_weight=w_train)` at `optimization.py:308` AND final `model.fit(..., sample_weight=final_weights)` at `optimization.py:637`
- F-AXIS #1 print emitted at `lgbm.py:702-707` per (model, month) cell

### Check D — Configuration sanity: PASS
- ENSEMBLE_SIZE=5 (per /030 §8 BINDING)
- n_trials=50 (per /030 §8 BINDING)
- single outer seed=42
- bounds_profile=v1_pruned_axis016 STRICT REPLICATION (auto-upgrade from `v1_pruned` triggers when sample_weight_mode != abs_pnl)
- R1/R2/R3 baseline UNCHANGED
- 6h CONFIRMATION-mode hard cap declared; kill-switch armed at 5.0h
- R5 axis-isolation auto-disable when sample-weighting active (clean comparator vs BASELINE_V1)

### Check E — Test suite mandate: PASS
14 tests at `tests/test_iteration_v1_031.py` (exceeds 10+ mandate), covering:
- CLI flag parsing
- Weight formula correctness (against EDA CSV)
- Per-symbol mean-normalization
- Weight wiring to LightGBM (monkeypatched fit assertion — /027 LESSON sample-instance pattern)
- BASELINE CATCH-ALL EXCLUSION (/030 LESSON)
- F-AXIS #1 wiring print
- Dispatch banner (/030 LESSON)
- Reproducibility (deterministic weights)
- Lookahead concurrency
- pruned bounds STRICT replication
- Configuration constants (ENSEMBLE_SIZE=5, n_trials=50, seed=42)
- /016 mode preserved
- Invalid mode raises
- Foundation regression embargo

`tests/test_lookahead_embargo.py` 4 mandated tests confirmed present.

### Check F — Anti-pattern static scan A1-A14 + J/K/L: PASS
- A1 `train_end_ms = test_start_ms - embargo_ms` at `walk_forward.py:113` preserved
- A2 zero forward-window std calls in labeling
- A3 zero scaler fit_transform in sample_weighting.py
- A5 master-data-extent invariance test present + NEW concurrency test extends coverage
- A8/A12/A13 N/A for this axis
- `compute_concurrency_at_entry` past-only enforced by `t_row <= t_col` at `sample_weighting.py:99`

### Check G — Axis Family Validation: PASS
Brief Section 0.6 declares `sample-weighting` NINTH family. LM Master §1 three load-bearing distinctions vs /016 closure (std 100× wider, Kish 0.899 vs ~1.0, pooled Spearman vs uniqueness_only 0.034). Rotation VALID by dual criteria (3 distinct families in prior 5; >15 EXPLORATIONs since /016 last attempt). Src/ diff confirms family alignment: only `sample_weighting.py` (NEW), `lgbm.py` (NEW branch), `run_baseline_v1.py` (CLI + dispatch), `tests/` modified.

### Check H — Wall-clock + budget exception: PASS
PATH A 5-seed × 50 trials at 3.60h modal. LM Master §8 ENDORSE. Brief Section 0.5 EXPLORATION-WITH-BUDGET-EXCEPTION explicitly declared. 6h hard cap with kill-switch 5.0h. No mid-run n_trials compression authorized.

### Mini-Check K — Strategy attribute symmetry: PASS
`sample_weight_mode` attribute name symmetric across all call sites: CLI choices, LightGbmStrategy init/validation/dispatch, run_model signatures, runtime resolution, `_r5_kwargs`. No /030-class `atr_column` mismatch. Mode literal `"composite_inv_concurrency"` consistent across 5+ call sites.

### Mini-Check L — Wall-clock estimate vs precedent ratios: PASS
Brief §3.6: /016 anchor 50 min × 4.32× = 216 min = 3.60h. Tolerance window predicted ∈ [108 min, 324 min] = [1.8h, 5.4h]. Predicted 3.60h sits at center of band. Inside 6h hard cap with 40% modal margin.

## Foundation Regression Check: PASS
`walk_forward.py:113` UNCHANGED by QE diff. All `tests/test_lookahead_embargo.py` mandated tests present. NEW iteration-level coverage added.

## Cadence + Axis Sanity: PASS
Phase 5.5 PASS at `51dfcaf`. Cycle-4 EXPLORATION 4/10.

## Falsifier Presence: PASS
5 F-AXIS items with explicit OOS-Sharpe-below-X falsifier; Section 4 verdict matrix Row 12 explicit catastrophic-tail closure declaration.

---

## PRE-FLIGHT AUTHORIZATION

Phase 6 backtest dispatch AUTHORIZED.

**Launch invocation** (per brief Section 3.5 + actual runner CLI):

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --exploration \
  --iteration 31 \
  --n-trials 50 \
  --ensemble-size 5 \
  --pruned-features \
  --sample-weight-mode composite_inv_concurrency \
  > logs/v1_iter031.log 2>&1
```

Detached-bash launch recommended per `feedback_split_engineer_dispatch.md`. Modal 3.60h; HARD CAP 6h; kill-switch armed at 5.0h.

---

## Outstanding informational notes (NOT blocking)

1. **Attribution ambiguity at PATH A acknowledged.** Brief Section 0.2 + LM Master §1 closing flag PATH A confounds axis orthogonality with budget control. /032 routing PRE-COMMIT (PROMISING-CLEAN → /032 = budget-control replicate at 3-seed × 18). Critic Phase 7.5 will verify Validations 1-3 PASS thresholds before classifying any PROMISING outcome.

2. **F-AXIS #1 wiring print fires ONCE per (model, month) cell, NOT per trial.** Phase 7.5 grep-count target: ≥ 252 of 265 expected prints (53 months × 5 models × 0.95).

3. **F-AXIS forensic log path declared** (`data/v1_iter_v1-031_optuna_trials.parquet`) but implementation visibility limited. Phase 7.5 Validations 1+2 require the parquet.

4. **Modal verdict pre-committed INERT-NO-EFFECT 30%** (LM Master §4 ADOPTED). Combined PROMISING 40% > NEG 30%. Net OOS Δ +0.04. Phase 7.5 review will hold to this band.

5. **R5 axis-isolation auto-disable on sample-weighting** at `run_baseline_v1.py:1727-1742` is correct comparator construction vs BASELINE_V1.

No BLOCK conditions. Phase 6 backtest dispatch AUTHORIZED.
