# Phase 6.0 Critic Pre-Flight — iter-v1/016

OVERALL: PASS

## Pre-Flight Checks

### Check 1 (mini) — Brief Look-Ahead Audit: PASS

Brief Section 1 hypothesis and Section 3.1 implementation describe per-row weight transformation applied to labeled training samples. The transformation operates on already-computed `train_indices` + `train_labels` returned by `label_trades` — no temporal expansion, no forward window access. Section 3 explicitly states "no other axis changes". EDA tables use IS-only data. No "forward 24h"/"tomorrow's"/"next-N-days" verbiage in feature descriptions.

### Check 13 (mini) — Anti-Pattern Static Scan: PASS

A1/A2/A3/A6/A12/A13 all clean. Files scanned: `lgbm.py`, `walk_forward.py`, `labeling.py`, `optimization.py`, `run_baseline_v1.py`, tests.

### Foundation Regression: PASS

`walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms` UNCHANGED. compute_embargo_candles helper single source of truth. labeling.py UNCHANGED (σ_t past-only EWMA preserved). 4 mandated regression tests present.

### Cadence + Axis Sanity: PASS

- Phase 5.5 OVERALL=PASS at `5811b69`
- Brief Section 0.6: `sample-weighting` NEW family (never used in v1)
- Prior 5 EXPLORATIONs: risk-primitive ×2, methodology-substrate-test ×2, labeling ×1
- Rotation VALID (NEW family)
- Cycle-3 cadence ledger begins at /016 EXPLORATION #1
- HIGH-RISK declared (Section 2.5); OPT-IN multi-seed not triggered

### Falsifier Presence: PASS

8 named falsifiers + F-AXIS-MECHANISM-NEW compound 3-sub-check. F1 OOS Sharpe Δ NEGATIVE threshold Δ ≤ -0.20; F3 IS catastrophic Δ < -0.30; F-AXIS-MECHANISM Kish > 0.95 + Model A balance |Δ| ≤ 0.02 + timeout_fallback < 0.6.

## /016-Specific Mini-Checks

| Check | Status | Evidence |
|---|---|---|
| `abs_pnl` BIT-IDENTICAL baseline | PASS | lgbm.py:550-568 — abs_pnl path explicit no-op; b1.5 block precedes legacy sample_uniqueness b2 |
| `uniform` REPLACES with np.ones(n) | PASS | lgbm.py:551 replacement assignment; test verifies std=0 |
| `v1_pruned_axis016` pins subsample=colsample=1.0 | PASS | optimization.py:226-236 explicit pin logic |
| Auto-upgrade --pruned-features + --sample-weight-mode != abs_pnl | PASS | run_baseline_v1.py:982-989 conditional bounds_profile upgrade |
| F-AXIS-MECHANISM CSV emission | PASS | run_baseline_v1.py:1267-1281 writes f_axis_mechanism.csv |
| n_trials=18 (compressed) | PASS-WITH-NOTE | CLI default 35; orchestrator MUST pass --n-trials 18 explicitly. Section 3.5 Rec #1 ADOPTED is authoritative. |
| Wall-clock ≤ 2h ≥20% margin | PASS | LM Master upper 1.58h with n_trials=18 → margin 21% ≥ 20% ✓ |
| NO outer-seed loop | PASS | single-pass flat model loop; 3 inner seeds [42, 123, 456] |

## Informational Notes

1. **Test file name differs from brief §10.3**: tests/test_iteration_v1_016_sample_weighting.py vs spec naming. 7 coverage categories all present. Not blocking.

2. **F-AXIS-MECHANISM is WIRING test, NOT edge test**: PASS by construction under uniform weighting. Phase 7.5 should NOT cite as edge evidence. LM Master Rec #3 + Risk #1 honest disclosure.

3. **n_trials launch discipline**: CLI default 35; runner MUST be invoked with `--n-trials 18` explicitly. Phase 5.5 gate documents.

4. **n_eff_per_cell prediction (LM Master Rec #3)**: predict stays [10, 20] range; uniform weighting does NOT restore /015's substrate collapse (label-shape-bound not weight-bound). Phase 7.5 should treat "n_eff_per_cell restored by sample weighting" claim as misattribution.

**Verdict: PASS. Backtest cleared to launch with --n-trials 18 --pruned-features --sample-weight-mode uniform (auto-upgrades to v1_pruned_axis016 bounds).**
