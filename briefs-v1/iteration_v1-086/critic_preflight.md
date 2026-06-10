# Phase 6.0 Critic Pre-Flight — iter-v1/086

**Track**: v1 (refactored)
**Branch**: iteration-v1/086
**Commit**: 5da75fa869192bbbc510f826bbdf946c378334b4
**Date**: 2026-06-10

OVERALL: PASS

---

## Context (for record)

STOCK-STACK mine (no new features, no new risk). TRB cleared GATE-2 at IS +0.4930.
F5 diversification-conditionality falsifier is the key Phase 7.4 addition.
Axis family: per-cohort-specialization-TRB.

---

## Mini-Check 1 — Hypothesis-Implementation Alignment

**Brief hypothesis**: TRBUSDT specialist on the STOCK 48-col V1_FEATURE_COLUMNS_PRUNED
set, NO new features, same R-gate stack as incumbents.

**src/ diff review**:
- `V1_ITER086_UNIVERSE = ("TRBUSDT",)` added to `features_v1/__init__.py` — MATCHES
- `V1_ITER086_FEATURE_COLUMNS` does NOT exist — MATCHES (zero new features by design)
- `len(V1_FEATURE_COLUMNS_PRUNED) == 48` assert in `__init__.py` holds — MATCHES
- Dispatch block uses `active_feature_columns` (the global 48-col PRUNED set, set by
  `--pruned-features` path); does NOT override it with a local feature set — MATCHES
- Guard `assert len(active_feature_columns) == 48` fires at dispatch entry — MATCHES
- `model_name = "Model_A_TRB_specialist_086"` in dispatch print — MATCHES
- `R1=OFF, R2=OFF, R3=ON-cutoff=0.70, R5=ON-vt_target_vol=0.3` — MATCHES brief Section 3.3
- `atr_tp=2.9, atr_sl=1.45` — MATCHES brief Section 3.4
- `specialist_mode=True, V1_SPECIALIST_SEED_COUNT=50, V1_SPECIALIST_OPTUNA_TRIALS=30`
  — MATCHES brief Section 3.5
- Cohort isolation assert: `_e086_symbols.issubset({"TRBUSDT"})` — PRESENT

VERDICT: PASS

---

## Mini-Check 13 — Feature-Column Pinning

`feature_columns=active_feature_columns` explicitly passed to `LightGbmStrategy` at line
8103 of `run_baseline_v1.py`. `active_feature_columns` is set to
`list(V1_FEATURE_COLUMNS_PRUNED)` by the `--pruned-features` path at the top of `main()`.
The `--pruned-features` flag is injected into `sys.argv` by `run_iteration_086.py`.
Length guard `assert len(active_feature_columns) == 48` fires at dispatch entry.

No `None`, no empty list, no auto-discovery. PASS.

---

## Foundation Regression Check

`walk_forward.py:113`: `train_end_ms = test_start_ms - embargo_ms` confirmed present
(the iter-v3/058 fix). No regression. PASS.

---

## Cadence Check

SPECIALIST budget: 50 inner seeds × 30 Optuna trials. Brief Section 0.5 declares ~6h
wall-clock. This is within the SPECIALIST budget (no formal 2h cap for per-cohort
SPECIALIST mines under the cycle-6/7 regime-specialist mandate; the 9h cap applies to
BUNDLE, not SPECIALIST). Budget matches methodology-lock (AAVE/078 + UNI/085 precedents).
PASS.

---

## Falsifier Check

F1 (trade-rate floor ≥50 OOS): pre-registered. PRESENT.
F2 (probe-consistency IS Sharpe ≥+0.30): pre-registered with specific numerical band. PRESENT.
F3 (SPECIALIST candidacy bands: VALIDATED ≥+0.50, PROMISING [+0.20,+0.50], NEGATIVE <+0.20):
   pre-registered in Sections 4 and 8. PRESENT.
F4 (TS-mom-beat: IS > −0.179 AND > 0.00): pre-registered. PRESENT.
F5 (diversification-conditionality: MACD/ADX importance-ordering + realized PnL-stream
   corr): the KEY new falsifier, pre-registered explicitly. PRESENT.

All 5 falsifiers have specific numerical thresholds. The bundle-accretion carve-out for
[+0.20, +0.50] PROMISING result (conditional on F5a + F5b passing) is pre-registered in
Section 4 — prevents post-hoc rationalization in either direction. PASS.

---

## Additional Observation

The `/086` dispatch block correctly does NOT reference `V1_ITER086_FEATURE_COLUMNS`
(confirmed by `test_dispatch_no_feature_override`). This test was added specifically to
guard the one-variable discipline — a direct lesson from /085's inert-feature crater.

The `specialist_dispersion.csv` post-report persistence block mirrors the /085 pattern
exactly (critical for basin-lottery adjudication in Phase 7.5).

---

## Path Forward (if BLOCK)
N/A — OVERALL=PASS.
