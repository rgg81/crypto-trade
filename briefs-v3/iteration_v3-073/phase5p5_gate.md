# Phase 5.5 Gate — iter-v3/073

OVERALL: BLOCK

## Per-Section Status

- Section 0 (Data Split): PASS
- Section 0.5 (Iteration Type): PASS
- Section 1 (Hypothesis): PASS
- Section 2 (IS-Only Evidence): PASS — committed script: analysis/iteration_v3-073/axis_selection_eda.py (SHA b004bc9)
- Section 3 (Proposed Changes): PASS — single-axis variation; code edits enumerated
- Section 4 (Expected OOS Impact): PASS — bands pre-registered; SUSPICIOUS gate pre-registered; saturation falsifier present; per-symbol falsifiers present
- Section 5 (Risk Mitigation): PASS
- Section 6 (Risk Management Design): PASS — 7-primitive table; UNCHANGED vs /060
- Section 7 (Failure-Mode Prediction): PASS — four outcomes enumerated with probabilities; failure signatures specified
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION classification; four pre-registered bands with disjunctive/conjunctive logic locked
- Section 9 (Library Stack): PASS — no new libraries; stack pinned
- Section 10 (QR Audit Trail): PASS — EDA commit b004bc9; quantitative basis documented; axis selection process documented

## Reasons (BLOCK)

### BLOCK 1 — Pre-flight assertion: `V3_ATR_MULTIPLIERS_PER_SYMBOL` count check (HARD)

`run_baseline_v3.py` lines 450-463 assert:

```python
if n_atr_custom != 0:
    raise RuntimeError(
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL has {n_atr_custom} entries — expected exactly 0 ..."
    )
```

The iter-v3/051 SYSTEM-LEVEL REVERT assertion is stale. `V3_ATR_MULTIPLIERS_PER_SYMBOL` now has 2 entries (`BCHUSDT`, `LDOUSDT`). The runner will crash at pre-flight before the first model is built. The QR's brief Section 3.1 identifies this as a pre-flight assertion that must be updated, but the runner code was NOT changed at setup commit `b859dab`.

**Required fix**: Update the pre-flight block (lines 446-463) to accept exactly 2 entries and assert the specific keys `{"BCHUSDT": (2.0, 1.25), "LDOUSDT": (1.5, 1.25)}` (or relax to ≥ 0 and rely on the downstream per-symbol assertions). Update the print message correspondingly.

### BLOCK 2 — Pre-flight assertion: per-symbol ATR loop (HARD)

`run_baseline_v3.py` lines 505-525 iterate over all 3 symbols and assert each returns `(2.0, 1.0)`:

```python
for _sym_atr in ("BCHUSDT", "LDOUSDT", "TRXUSDT"):
    sym_atr = atr_multipliers_for_symbol(_sym_atr)
    if sym_atr != (2.0, 1.0):
        raise RuntimeError(...)
```

With `V3_ATR_MULTIPLIERS_PER_SYMBOL` populated, `atr_multipliers_for_symbol("BCHUSDT")` returns `(2.0, 1.25)` and `atr_multipliers_for_symbol("LDOUSDT")` returns `(1.5, 1.25)` — both raise. The runner crashes at pre-flight on the second iter after the count-check crash above.

**Required fix**: Replace this block with one that asserts the iter-v3/073 per-symbol values — BCH → (2.0, 1.25), LDO → (1.5, 1.25), TRX → (2.0, 1.0) (DEFAULT fallback). The iter-v3/070 CLOSEOUT comment and assertion must be updated to reflect the /073 state.

### BLOCK 3 — Pre-flight assertion: `label_mode` expected `"fixed_horizon"` (HARD)

`run_baseline_v3.py` lines 746-765 assert:

```python
expected_label_mode = "fixed_horizon"
if _p13_lgbm.label_mode != expected_label_mode:
    raise RuntimeError(...)
```

`_build_v3_model` at line 1511 now correctly passes `label_mode="triple_barrier"` (the /073 Edit 2 revert). But the pre-flight assertion still hard-codes `"fixed_horizon"` (from /072). The assertion raises on the correctly-configured model. The runner crashes at pre-flight.

**Required fix**: Update lines 746-765 to assert `expected_label_mode = "triple_barrier"` and update the print message to reflect the /073 revert (remove the `/072: fixed-horizon` framing; add `/073: REVERT to triple_barrier`).

### BLOCK 4 — Existing test `test_atr_multipliers_for_symbol.py` fails (HARD)

`tests/features_v3/test_atr_multipliers_for_symbol.py::test_atr_multipliers_default` asserts `atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0)`. With `V3_ATR_MULTIPLIERS_PER_SYMBOL` populated with `LDOUSDT: (1.5, 1.25)`, this assertion fails. `pytest tests/ -x` fails at this test before reaching the new `test_per_symbol_atr_v3_073.py` file.

**Required fix**: Update `tests/features_v3/test_atr_multipliers_for_symbol.py` to reflect the /073 state — `LDOUSDT` and `BCHUSDT` now return per-symbol values; the test should either be updated to pin the /073 values or the per-symbol lookup test should be consolidated into the new /073 test file.

## Ancillary observations (non-blocking)

- **T0 anchor**: byte-exact vs `reports-v3/iteration_v3-060/comparison.csv`. All 9 values match. PASS.
- **`label_mode` in `_build_v3_model`**: correctly reverted to `"triple_barrier"` at line 1511. The QR's Edit 2 fired correctly in `_build_v3_model`. The failure is ONLY in the pre-flight assertion that cross-checks it.
- **New test `test_per_symbol_atr_v3_073.py`**: all 6 tests PASS independently. The failure is in the pre-existing test file `test_atr_multipliers_for_symbol.py` (Block 4).
- **`vol_scale_floor_per_symbol`**: unchanged at `{"TRXUSDT": 0.5}` — confirmed at runner line 685-690 assertion. PASS.
- **`DEFAULT_ATR_MULTIPLIERS`**: confirmed `(2.0, 1.0)`. PASS.
- **`block_long_for` / `block_short_for`**: both `()` — confirmed. PASS.
- **`REQUIRED_GAP`**: 66 = (21+1)*3. Unchanged. PASS.
- **Sacred constants**: `OOS_CUTOFF_DATE = "2025-03-24"`, `training_months = 24`, 5-seed inner ensemble unchanged. PASS.
- **`ITERATION_LABEL`**: `"v3-073"` at line 128. PASS.
- **Track isolation**: no `from crypto_trade.features ` in `features_v3/`. PASS.
- **Data freshness**: BCH/LDO/TRX/BTC 8h CSVs all 2.5h old. PASS.
- **Linter**: ruff errors in non-iteration analysis scripts (`analyze_drawdown_brake.py`, `compare_baseline_vs_clean.py`) — pre-existing, not introduced by this iteration's commits.
- **Feature columns**: `features_for_symbol()` returns exactly 14 features for all 3 symbols; `feature_columns=list(features_for_symbol(symbol))` passed explicitly at line 1503. PASS.
- **Label-execution consistency**: verified at Section 3.2 and in `lgbm.py:352-353` (training) and `lgbm.py:705-713` (live signal). Both paths consume the same per-symbol multipliers from `atr_multipliers_for_symbol()`. PASS (by design; not contingent on fixing the pre-flight assertions).

## Summary

All 10 brief sections are complete and correctly specified. The QR's code changes to `features_v3/__init__.py` (Edit 1 — dict population), `run_baseline_v3.py` lines 1506-1511 (Edit 2 — label_mode revert), `run_baseline_v3.py:128` (Edit 3 — ITERATION_LABEL), and `tests/features_v3/test_per_symbol_atr_v3_073.py` (Edit 4 — 6 new tests) are all correct. However three pre-flight assertion blocks in `run_baseline_v3.py` and one existing test file were NOT updated to match the new dict state and reverted label_mode. The runner will crash at pre-flight before executing a single training cell. Phase 6 is BLOCKED pending QR resolution of all four items.
