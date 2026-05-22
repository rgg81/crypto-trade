# Phase 5.5 Gate — iter-v3/092

OVERALL: PASS

**This re-gate (2026-05-17, brief commit `cf64dcc`) supersedes the prior BLOCK (commit `bc4a089`). The prior gate BLOCKed on exactly two defects in Section 3.3 (Reason B: `_derive_ensemble_seeds` reuse mechanism unspecified; Reason C: cross-sectional `--seeds` naming conflict unacknowledged). Both defects are resolved by the surgical Section 3.3 edit. All other sections remain PASSed from the prior gate and are NOT re-litigated here.**

---

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24` stated immutable; IS/OOS windows named in absolute dates. No-cheating audit in Section 10.3 confirms every design parameter is IS-only or a-priori. (Unchanged from prior gate.)
- Section 1 (Hypothesis): PASS — single-sentence hypothesis present (Section 1.3). Specific, honest, non-vague: the cross-sectional `LGBMRanker` at best-faith H=21 multi-seed form does NOT reach a net-positive OOS book and does NOT beat the /059 canonical baseline. CONFIRMATION-NO-MERGE is the pre-registered modal expected outcome. (Unchanged from prior gate.)
- Section 2 (IS-Only Evidence): PASS — rests entirely on already-committed, walk-forward-faithful /091 horizon EDA (`analysis/iteration_v3-091/holding_horizon_eda.py`, SHA `d4ad137`). H=21 IS net monthly Sharpe +0.0944 (M2, 35-trial) is verified against committed CSV. Model-free M1-block numbers are explicitly excluded. (Unchanged from prior gate.)
- Section 3 (Proposed Changes): PASS — **RE-GATED. See re-gate section below.** The multi-seed build spec as a whole (Section 3.3 after `cf64dcc`) is complete and implementable with zero QE research decisions.
- Section 4 (Expected OOS Impact / CONFIRMATION Gates): PASS — ten CONFIRMATION gates G1-G10 present with numerical thresholds. DSR/PBO/PSR input provenance specified. BASELINE_V3.md update policy correctly stated. (Unchanged from prior gate.)
- Section 5 (Risk Mitigation): PASS — table covers single-seed lottery, turnover/fee drag, directional drawdown, concentration, listing non-stationarity, label look-ahead, all with IS-calibrated or a-priori sources. (Unchanged from prior gate.)
- Section 6 (Risk Management Design): PASS — scoped appropriately; legacy v3 7-gate per-symbol stack correctly deferred for the cross-sectional closing verdict. (Unchanged from prior gate.)
- Section 7 (Failure-Mode Prediction): PASS — probability-weighted distribution across four outcome paths, single-seed-inversion risk named, modal outcome plainly CONFIRMATION-NO-MERGE. (Unchanged from prior gate.)
- Section 8 (MERGE/NO-MERGE Criteria): PASS — three disjunctive classifications (8.1 CONFIRMATION-MERGE, 8.2 CONFIRMATION-NO-MERGE, 8.3 CONFIRMATION-INCONCLUSIVE) with pre-registered probabilities. BASELINE_V3.md update condition correctly stated (must beat /059 on BOTH IS AND OOS multi-seed mean AND both Pareto seeds positive). (Unchanged from prior gate.)
- Section 9 (Library Stack Declaration): PASS — LightGBM (LGBMRanker, lambdarank), Optuna (TPESampler, n_trials=35 per model), pandas/numpy, v3 DSR/PBO/PSR helpers. No new third-party dependency. (Unchanged from prior gate.)

---

## Re-Gate: Section 3 Defects B and C

### Defect B — RESOLVED

**Prior BLOCK:** Section 3.3 item 2 said "the QE locates [_derive_ensemble_seeds] and reuses it" without specifying the reuse mechanism. The function is module-private in `run_baseline_v3.py` (lines 119-128), not in any importable `src/` module, creating a QE research decision (copy vs move-to-src vs re-implement).

**Resolution verified:** Brief Section 3.3 item 2 (after `cf64dcc`, lines 171-181) now specifies **Mechanism A — copy verbatim** explicitly:

> "Reuse mechanism — SPECIFIED (mechanism A — copy verbatim, no `src/` change). `_derive_ensemble_seeds` is a module-private function in `run_baseline_v3.py` (lines 119-128 at `c6a03ed`)` — it is NOT in any importable `src/` module, so it cannot be `import`-ed. The QE **copies the `_derive_ensemble_seeds` function body verbatim from `run_baseline_v3.py` lines 119-128 into `run_cross_sectional_v3.py``"

The exact function body is quoted inline in the brief (the two-line body matching `run_baseline_v3.py:127-128` exactly). Mechanism B (move to `src/`) is explicitly rejected with rationale. The integration test spec (item 7(iv)) is correspondingly updated: it imports `_derive_ensemble_seeds` from `run_cross_sectional_v3` (the copied function), not from `run_baseline_v3`. **Zero QE research decision remains.**

**Code cross-check:** `run_baseline_v3.py` lines 119-128 confirmed to contain exactly:
```python
def _derive_ensemble_seeds(outer_seed: int, size: int = 5) -> list[int]:
    rng = np.random.default_rng(outer_seed)
    return [int(s) for s in rng.integers(low=0, high=2**31 - 1, size=size)]
```
The brief's quoted body is a character-for-character match. The QE copies exactly this.

### Defect C — RESOLVED

**Prior BLOCK:** Brief Section 3.5 build step 4 specified `--seeds 2` for the cross-sectional runner without acknowledging that `run_baseline_v3.py`'s `--seeds` was deprecated at iter-v3/059 and emits a WARNING + ignores the value. An engineer reading both runners would be uncertain whether the cross-sectional `--seeds` carries the same deprecation behaviour.

**Resolution verified:** Brief Section 3.3 item 1 (after `cf64dcc`, lines 168-169) now contains a dedicated mandatory note titled **"`--seeds` naming-conflict note (mandatory — for the QE)"** that states explicitly:

> "The cross-sectional runner's `--seeds` is a **NEW, independent argument** added by /092 to `run_cross_sectional_v3.py` (which has no `--seeds` argument today): it has **different semantics** — it actively controls the cross-sectional runner's outer-seed count (selecting the first N elements of `CONFIRMATION_OUTER_SEEDS`). The QE **must NOT** copy the per-symbol runner's deprecation behaviour into the cross-sectional runner: the cross-sectional `--seeds` is live and functional, emits **no** deprecation warning, and is **not** ignored. The name coincidence with the deprecated per-symbol `--seeds` is incidental; the two arguments live in two different runners and do not share code."

**Zero QE ambiguity remains.** The deprecation-behaviour inheritance is explicitly prohibited.

### No-Collateral-Breakage Check

The surgical edit is confined to Section 3.3 (16 insertions / 2 deletions per the brief commit description). Checked:

1. Section 3.3's internal coherence: the seven-item multi-seed spec (outer-seed loop, inner-ensemble derivation, per-seed + aggregate reports, CPCV aggregation, 2-seed Pareto, reproducibility, smoke + integration tests) is self-consistent after the edit. Item 2 now names Mechanism A; item 7(iv) correspondingly imports from `run_cross_sectional_v3`. No internal contradiction.

2. Section 3.5 build steps (the ordered QE build recipe): step 1 (add `CONFIRMATION_OUTER_SEEDS = (42, 123)` + `--seeds` argument) and step 4 (`uv run python run_cross_sectional_v3.py --skip-features --seeds 2 --n-trials 35`) remain consistent with the now-resolved Section 3.3 spec. No step references the prior ambiguous "locate and reuse" language.

3. No other section references the `_derive_ensemble_seeds` reuse mechanism or the `--seeds` naming. The edit is truly localized.

4. The seven-item spec as a whole is implementable with zero QE research decisions: the outer-seed constant is named (`CONFIRMATION_OUTER_SEEDS = (42, 123)`), the function to copy is quoted verbatim, the ensemble-scoring rule is stated (arithmetic mean of raw scores), the report layout is specified (per-seed `seed_<s>/` + multi-seed aggregate at root), the aggregate schema is named (`ensemble_summary.json`, `comparison.csv` with per-seed columns and min, `dsr.json` on the aggregate book), the CPCV aggregation rule is stated (mean `frac_positive_paths` across seeds), the Pareto boolean is defined (both seeds individually OOS-net-positive), and the test scope covers all four integration assertions.

---

## Reasons (if BLOCK)

None. Both prior BLOCK reasons are resolved. No new defect introduced by the surgical edit.

---

## Summary

The QR's surgical Section 3.3 fix at `cf64dcc` cleanly resolves both prior BLOCK defects:
- **Defect B:** `_derive_ensemble_seeds` reuse mechanism now specified as Mechanism A (copy verbatim from `run_baseline_v3.py:119-128`), with the exact function body quoted inline and the integration test spec updated accordingly.
- **Defect C:** Cross-sectional `--seeds` explicitly declared a NEW argument with different semantics from the deprecated per-symbol `--seeds`; deprecation behaviour explicitly prohibited.

The Section 3.3 multi-seed build spec is complete, internally coherent, and implementable with zero QE research decisions. All other sections remain PASSed from the prior gate.

**Phase 6 may proceed.**
