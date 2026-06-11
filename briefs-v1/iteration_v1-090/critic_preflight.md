# Phase 6.0 Critic Pre-Flight — iter-v1/090

**Track**: v1
**Branch**: `iteration-v1/090`
**Commit SHA (implementation)**: a6544f00d5b3bde5704b7c543f618d7fa4ba4d3b
**Phase 5.5 gate commit**: a7130ea2
**Brief commits**: 3222f808 + 0be382cd (QR) + 15797088 (LM Phase 4.5) + 0be382cd (LM integration)

OVERALL: PASS

---

## Mini-Check 1 — OPT-IN / default-OFF correctness

**PASS**

`sample_weight_mode="abs_pnl"` (default) follows the abs_pnl path in (b1.5) which has
no branch for `abs_pnl_timedecay`. The `_apply_timedecay` local bool defaults to `False`.
Block (b3) fires only when `time_decay_half_life is not None OR _apply_timedecay`.
With default `abs_pnl` mode: `time_decay_half_life=None` (not passed) AND
`_apply_timedecay=False` → (b3) is SKIPPED → abs_pnl path is BYTE-IDENTICAL.

Evidence: `tests/test_w_decay.py::TestAbsPnlDefaultUnchanged` (3 tests passing).
Evidence: existing `test_iteration_v1_016_sample_weighting.py` (21 tests all PASS — no regression).

---

## Mini-Check 13 — §1c attribution log present and unconditional

**PASS**

The `[W-DECAY §1c]` print block at lgbm.py lines 953–959 fires unconditionally
(NOT gated by `if self.verbose > 0`). It prints:
- `decay.mean` and `decay.min` (shape of the decay distribution)
- `weight_sum_before` and `weight_sum_after` (confirms weight mass drop ≈ decay.mean ≈ 0.55)
- `kish_ratio_after` (ESS shrink from un-renormalized decay)

This is the REQUIRED LM §1c artifact: Phase 7.4 uses weight_sum_before/after to split
recency-channel vs regularization-loosening side-effect (un-renormalized decay halves
`min_child_weight` bite by reducing total weight mass). Without this log, a VALIDATED F1
is unattributable between the two channels — the advisory's strongest recommendation.

---

## Foundation regression check — trim-after-decay ordering

**PASS**

The age computation at lgbm.py:930-933:
```python
train_times = self._open_time_arr[train_indices]
max_time = train_times.max()
age_ms = max_time - train_times
age_months = age_ms / (30.44 * 24 * 3600 * 1000)
```

`max_time = train_times.max()` is the LATEST open_time in the training split.
`train_indices` is derived from the walk-forward split (past-only). `self._open_time_arr`
is the full master frame open_time array; `train_indices` is the IS portion.
`max_time` <= `train_end_ms` (split boundary) → no look-ahead contamination.

Trim-after-decay ordering at optimization.py:392 + :417:
- Line 392: `train_idx = train_idx[trimmed_mask]` — numpy index trim to last `training_days`
- Line 417: `w_train = w[train_idx]` — reads the ALREADY-DECAYED `w` array (passed from lgbm.py)

The decay was applied to `train_weights` BEFORE `optimize_and_train` was called (in lgbm.py
block b3). So when optimization.py trims train_idx, it reads decayed weights that include ALL
training_window samples; after the trim, only the in-window decayed weights remain.
Trim-after-decay = AFML Ch.4 decay-within-window design. CONFIRMED.

---

## Cadence check — SPECIALIST 2h budget

**PASS**

Brief §3 projects ~1.5–2.0h (50 seeds × 30 trials × ~54 months ETH). Same as /064
actual. Inside the 2h SPECIALIST cap.

---

## Falsifier check — F2 scale correct, F1 threshold pre-registered

**PASS**

F1: ≥+0.20 VALIDATED, [0,+0.20) TENTATIVE-INERT, <0 NEGATIVE. Pre-registered baseline:
ETH/064 standalone IS +0.2383.

F2: RESCALED per LM §0 (adopted in brief §3.5). F2 is directional (~+30-60d median
training_days shift), NOT a move-toward-500d-cap expectation. F2-flat with F1>0 is NOT
auto-tagged NEGATIVE-INERT (decay composes-not-substitutes; §1c log is the arbiter).
The falsifier design is correctly calibrated to the LM's second-order magnitude finding.

F3: OOS-sign-direction (same sign as IS Δ).

---

## Lock intact check

**PASS**

In LightGbmStrategy dispatch (run_baseline_v1.py:8657-8685):
- `training_months=24` ✓
- `n_trials=V1_SPECIALIST_OPTUNA_TRIALS` (= 30) ✓
- `specialist_mode=True` ✓
- `specialist_n_startup_trials=10` ✓
- `specialist_n_estimators_max=500` ✓
- `bounds_profile="v1_specialist"` (max_depth=5 FIXED, num_leaves=31 FIXED) ✓
- `feature_columns=active_feature_columns` (48-col V1_FEATURE_COLUMNS_PRUNED) ✓
- `ood_cutoff_pct=0.70` (R3) ✓
- `sample_weight_mode="abs_pnl_timedecay"` (THE SINGLE CHANGE) ✓
- `time_decay_half_life` NOT set (uses _default_wdecay_half_life_months=12.0 in b3) ✓

Axis isolation: sample_weight_mode hardwired in constructor, NOT via `--sample-weight-mode`
CLI arg. The run_iteration_090.py runner sys.argv does NOT include `--sample-weight-mode`.
This correctly bypasses the global `/016 _disable_r5_for_sample_weighting` flag, ensuring
R5=ON (vt_target_vol=0.3) matches the ETH/064 seat config exactly.

---

## PRUNED 48 check

**PASS**

`len(active_feature_columns) == 48` guard in dispatch block (run_baseline_v1.py:8608-8612).
`len(V1_FEATURE_COLUMNS_PRUNED) == 48` guard in runner (run_iteration_090.py:119-131).
Both assertions abort before any training if the column count changes.
No feature additions or removals in this iteration.

---

## Notes

- ETH parquet staleness: `data/features/ETHUSDT_8h_features.parquet` is ~238h old
  (as of implementation date 2026-06-11). This MUST be refreshed before launching the
  backtest. Pre-backtest data freshness check:
  ```
  uv run crypto-trade fetch --symbols ETHUSDT --intervals 8h
  uv run crypto-trade features --symbols ETHUSDT --interval 8h --track v1 --format parquet
  ```
  This is a pre-launch operational step, not a code defect.

- The /016 `test_run_baseline_v1_accepts_flag` test checks that `"uniform"` and
  `"uniqueness_only"` appear in run_baseline_v1.py's argparser choices. The new
  `"abs_pnl_timedecay"` mode is NOT in the CLI choices (by design — it's hardwired
  in the /090 dispatch block). This is correct per axis isolation design.
