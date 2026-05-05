# Iteration v3-006 — Research Brief

**Type**: METHODOLOGY VALIDATION (CLEAN RESTART) — minimum-cost confirmation that the iter-v3/006 seed-plumbing fix produces distinct trade distributions across outer seeds
**Track**: v3 (rigor arm) — sixth iteration; iter-v3/001-005 all NO-MERGE
**Branch**: `iteration-v3/006` (off `iteration-v3/005` head, with one new code commit at SHA `9314db4` already shipped — see Section 3.8 inheritance plan)
**Date**: 2026-05-06
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ensemble_size    = 5              # inner-ensemble cardinality (UNCHANGED from iter-v3/001-005)
ensemble_seeds   = _derive_ensemble_seeds(outer_seed)  # per-outer-seed derived
                                                        # (REPLACES hardcoded LEGACY_ENSEMBLE_SEEDS
                                                        # = [42, 123, 456, 789, 1001] used iter-v3/001-005)
OOS_CUTOFF_MS    = 1742774400000  # millisecond representation for IS-only filtering
```

- **Sacred constants UNCHANGED**: `OOS_CUTOFF_DATE`, `training_months`. The seed-plumbing fix at SHA `9314db4` does NOT touch either.
- **IS window**: from each symbol's first usable kline (with the listing-date floor 2022-09-24) through `2025-03-23 23:59:59 UTC` exclusive.
- **OOS window**: from `2025-03-24 00:00:00 UTC` through the data-extent timestamp at backtest time.
- **Walk-forward unit**: monthly retrain, 24-month rolling training window, 1-month OOS prediction window — UNCHANGED.
- The QR sees OOS metrics for the first time in Phase 7. This brief is produced reading ONLY the SHA `9314db4` commit (`run_baseline_v3.py` diff + new `tests/strategies/ml/test_outer_seed_propagation.py`), the iter-v3/005 brief / engineering report / Critic review / diary, and the analysis script committed at SHA `03b6004`.

---

## Section 1 — Hypothesis

**With the seed-plumbing fix shipped at SHA `9314db4` (`_derive_ensemble_seeds(outer_seed)` replaces the hardcoded `ENSEMBLE_SEEDS` constant), running `--seeds 1` and `--seeds 2` on BCH-only at `--n-trials 10` (~90-120 min total wall-clock) will produce: (i) distinct trade distributions across outer seeds (per-seed Sharpe std > 0), (ii) a non-tied 2-row `pareto_front.csv` that genuinely tests cross-seed model variation (UNLIKE iter-v3/005's tied 10-row false-positive PASS), AND (iii) sets up the graduated 1 → 5 → 10 rollout per project direction (iter-v3/007 = 5 seeds, iter-v3/008 = 10 seeds, each gated on prior-iteration Critic approval).**

Single sentence — testable, falsifiable, scoped to a methodology validation that costs <2h of wall-clock. The "false-positive Pareto" finding from iter-v3/005's Critic BLOCK is the structural pretext: Phase 6 must demonstrate the fix works on a small-scale run before expanding to full-universe (iter-v3/007) or 10-seed (iter-v3/008) commitments.

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v3-006/seed_derivation_demo.py` (committed at SHA `03b6004` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read**: `run_baseline_v3.py` (top-level constants and `_derive_ensemble_seeds`).

**Outputs** (all committed alongside the script at SHA `03b6004`):
- `analysis/iteration_v3-006/derived_ensembles.csv` — 25 rows = 5 outer × 5 inner positions
- `analysis/iteration_v3-006/overlap_matrix.csv` — 5×5 pairwise shared-inner-seed counts
- `analysis/iteration_v3-006/legacy_check.csv` — 5 rows confirming none of the demo outer seeds reproduces `LEGACY_ENSEMBLE_SEEDS`
- `analysis/iteration_v3-006/summary.json` — combined diagnostics
- `analysis/iteration_v3-006/synthesis.md` — interpretive narrative

### 2.1 Derived ensembles for the 5 demo outer seeds

| outer_seed | inner_ensemble |
|---:|---|
| 42 | `[191664963, 1662057957, 1405681631, 942484272, 929893137]` |
| 17 | `[1591207480, 1814784297, 230512677, 345687080, 983484580]` |
| 100 | `[1646872011, 1793109396, 266670593, 1281090017, 172364403]` |
| 999 | `[1747827325, 1672513988, 374097583, 369901117, 388482298]` |
| 8675309 | `[1574131626, 813751500, 727432243, 1749148543, 778347199]` |

### 2.2 Pairwise overlap matrix (off-diagonal entries = shared inner seeds across outer seeds)

| outer_seed | 42 | 17 | 100 | 999 | 8675309 |
|---:|---:|---:|---:|---:|---:|
| 42 | 5 | 0 | 0 | 0 | 0 |
| 17 | 0 | 5 | 0 | 0 | 0 |
| 100 | 0 | 0 | 5 | 0 | 0 |
| 999 | 0 | 0 | 0 | 5 | 0 |
| 8675309 | 0 | 0 | 0 | 0 | 5 |

- Total off-diagonal pairs: 10 (`C(5,2)`).
- Pairs with zero shared inner seeds: **10/10**. Max off-diagonal overlap: **0**.

### 2.3 Legacy reproduction check

| outer_seed | equals `LEGACY_ENSEMBLE_SEEDS=[42,123,456,789,1001]`? | shared inner seeds with legacy |
|---:|:---:|---:|
| 42 | False | 0 |
| 17 | False | 0 |
| 100 | False | 0 |
| 999 | False | 0 |
| 8675309 | False | 0 |

- **0/5** demo seeds reproduce the legacy hardcoded constant.
- **0** total inner seeds shared with legacy across all demos.

### 2.4 Adversarial tests

The 6 adversarial tests in `tests/strategies/ml/test_outer_seed_propagation.py` PASS at SHA `9314db4` (verified above):
- `test_derive_returns_correct_size` — PASS
- `test_derive_is_deterministic` — PASS
- `test_derive_distinct_for_distinct_outer_seeds` — PASS
- `test_derive_no_collision_within_ensemble` — PASS
- `test_derive_legacy_constant_no_longer_passed` — PASS (sampled 100 outer seeds; none reproduces legacy)
- `test_derive_size_parameter_respected` — PASS

Total adversarial test count post-SHA `9314db4`: **35** (29 inherited from iter-v3/001-005 + 6 new at SHA `9314db4`).

### 2.5 Implication for Phase 6

The producer-side property is verified: distinct outer seeds produce distinct inner ensembles. **Phase 6 verifies the consumer-side property** — that distinct inner ensembles produce distinct OOS trade distributions on a real backtest. The minimum-viable test is `--seeds 2 --n-trials 10` on BCH-only, asserting `df['monthly_sharpe'].std() > 0` on the 2-row `pareto_front.csv`.

---

## Section 3 — Proposed Changes

### 3.1 Symbols — SCOPED to BCHUSDT only for iter-v3/006

| Symbol | Status (iter-v3/006) | Rationale |
|---|---|---|
| BCHUSDT | KEEP | Cheapest single-symbol diagnostic; ~30-45 min wall-clock per `--seeds 1` run at `--n-trials 10`. |
| MKRUSDT | TEMPORARILY EXCLUDED | Not needed for the seed-plumbing validation. iter-v3/007 expands to full universe. |
| LDOUSDT | TEMPORARILY EXCLUDED | Same. |
| TRXUSDT | TEMPORARILY EXCLUDED | Same. |

`set({BCH}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

**This is NOT a permanent universe change.** iter-v3/006 isolates the seed-plumbing test from any concurrent universe drift. iter-v3/007 (per project direction: 5 seeds on full universe) restores `(BCH, MKR, LDO, TRX)` and validates that the fix scales to multi-symbol cells.

### 3.2 Labeling — UNCHANGED

Inherited from iter-v3/001-005:
- Triple-barrier with ATR-scaled barriers: `tp = 2.9 × NATR_21`, `sl = 1.45 × NATR_21`
- Timeout: 7 days = 21 candles at 8h
- σ_t for triple-barrier: past-only ATR (no leak)
- Label-horizon-derived purge gap: `gap = (timeout_candles + 1) × n_symbols`. With BCH-only (`n_symbols=1`), the per-cell gap is 22; the global runner-level `REQUIRED_GAP=88` constant is preserved (it asserts the multi-symbol case).

### 3.3 Features — UNCHANGED

`V3_FEATURE_COLUMNS` (34 columns) remains the feature set. NO new features.

### 3.4 Risk gates — UNCHANGED (v2's 5 active gates + BTC trend filter)

| Gate | Status |
|---|---|
| Vol scaling (atr_pct_rank_200) | ON |
| ADX threshold (20) | ON |
| Hurst regime check | ON |
| Z-score OOD (|z| > 2.5) | ON |
| Low-vol filter (atr_pct_rank_200 ≥ 0.33) | ON |
| BTC trend filter (±20%, 14d) | ON |
| Hit-rate feedback gate | OFF |
| R1 / R2 / R3 | OFF |

Identical risk profile to iter-v3/004 / iter-v3/005.

### 3.5 Sub-fix decomposition

iter-v3/006 has THREE atomic deliverables, of which #1 is already shipped. Each #2 and #3 is a Phase-6 commit that the QE owns. The QR has zero `src/`-level work to do.

| # | Sub-fix | Spec | Status / verifier |
|---|---|---|---|
| 1 | **`_derive_ensemble_seeds(outer_seed)` + 6 tests** | `run_baseline_v3.py:84-96` adds `LEGACY_ENSEMBLE_SEEDS` (documentation only) and `_derive_ensemble_seeds`. `tests/strategies/ml/test_outer_seed_propagation.py` (98 lines) adds 6 adversarial tests. | **SHIPPED at SHA `9314db4`**. Verifier: `uv run pytest tests/strategies/ml/test_outer_seed_propagation.py -v` exits 0 (verified locally; 6/6 PASS). |
| 2 | **`--seeds 1 --n-trials 10` BCH-only baseline** | Phase-6 invocation: `uv run python run_baseline_v3.py --seeds 1 --n-trials 10` with the existing `V3_MODELS` temporarily reduced to `("A (BCHUSDT)", "BCHUSDT")` only. Producing a complete `comparison.csv` for the new derivation. | **NOT SHIPPED**. Verifier: `test -f reports-v3/iteration_v3-006/seeds_1/comparison.csv` AND `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-006/seeds_1/comparison.csv'); assert df.iloc[0]['monthly_sharpe'] != 0, 'sharpe is zero'"`. |
| 3 | **`--seeds 2 --n-trials 10` BCH-only cross-seed run** | Phase-6 invocation: `uv run python run_baseline_v3.py --seeds 2 --n-trials 10` (BCH-only). Produces a 2-row `pareto_front.csv` where the two outer seeds have DIFFERENT trade distributions (per-seed Sharpe std > 0). | **NOT SHIPPED**. Verifier: `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-006/pareto_front.csv'); assert df['monthly_sharpe'].std() > 0, f'std={df[\"monthly_sharpe\"].std()}'"`. |

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input)

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK. Verifier commands MUST execute and exit 0 post-Phase 6.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | Sub-fix #1 (seed derivation) ships | `run_baseline_v3.py:84-96` + `tests/strategies/ml/test_outer_seed_propagation.py` | `uv run pytest tests/strategies/ml/test_outer_seed_propagation.py -v` exits 0 |
| 2 | Sub-fix #2 (`--seeds 1`) produces comparison.csv | runner | `test -f reports-v3/iteration_v3-006/seeds_1/comparison.csv` |
| 3 | Sub-fix #2 first row monthly_sharpe is non-zero | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-006/seeds_1/comparison.csv'); assert df.iloc[0]['monthly_sharpe'] != 0, 'sharpe is zero'"` |
| 4 | Sub-fix #3 (`--seeds 2`) produces 2-row pareto_front.csv | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-006/pareto_front.csv'); assert len(df) == 2, f'rows={len(df)}'"` |
| 5 | **Per-seed Sharpe std > 0** (THE iteration's central test — false-positive killer) | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-006/pareto_front.csv'); assert df['monthly_sharpe'].std() > 0, f'std={df[\"monthly_sharpe\"].std()}'"` |
| 6 | All 35 adversarial tests pass (29 inherited + 6 new) | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 |
| 7 | Wall-clock ceiling: total Phase 6 runtime < 3h | engineering report | `python -c "import json; d=json.load(open('briefs-v3/iteration_v3-006/engineering_report_summary.json')); assert d['wall_clock_hours'] < 3, f'hours={d[\"wall_clock_hours\"]}'"` |
| 8 | Symbols-scoped: BCH-only confirmed in runner invocation | `run_baseline_v3.py` invocation log | engineering report Section X documents BCH-only invocation; reconciliation row 5 (Sharpe std > 0) is the orthogonal check |
| 9 | Trades not byte-identical to iter-v3/003 (fix actually changed behavior) | runner | `python -c "import pandas as pd; a=pd.read_csv('reports-v3/iteration_v3-006/seeds_1/in_sample/trades.csv'); b=pd.read_csv('reports-v3/iteration_v3-003/in_sample/trades.csv'); assert not a.equals(b), 'trades identical to iter-v3/003 — fix did not propagate to model'"` (NOTE: this is the falsifier test — see Section 4.3 Falsifier 3) |
| 10 | Legacy constant intact in source as documentation | `run_baseline_v3.py:84` | `grep -E "LEGACY_ENSEMBLE_SEEDS.*42.*123.*456.*789.*1001" run_baseline_v3.py` exits 0 |

### 3.7 NO new features, NO new risk gates, NO 5-seed or 10-seed runs THIS iteration

iter-v3/006 is purely a methodology validation iteration. The model architecture, feature set, risk gates, label scheme, and CPCV parameters are byte-for-byte unchanged from iter-v3/005. The ONLY structural change is the seed-derivation function (already shipped at SHA `9314db4`).

The graduated rollout is explicit:
- **iter-v3/006 (THIS)**: `--seeds 1` + `--seeds 2` on BCH-only, ~90 min total. Validates the fix works.
- **iter-v3/007 (NEXT)**: `--seeds 5` on full universe (BCH+MKR+LDO+TRX), `--n-trials=50`. ~5-9h. Gated on iter-v3/006 Critic approval.
- **iter-v3/008 (NEXT-NEXT)**: `--seeds 10` for project memory's seed-validation rule. ~10-18h. Gated on iter-v3/007 Critic approval.

NO meta-labeling. NO universe change beyond the temporary BCH-only scoping.

### 3.8 Inheritance plan from iter-v3/005

The `iteration-v3/006` branch was branched from `iteration-v3/005` head (commit `0aa64df` — `recompute_10seed.py` headline-metrics fix). After branching, the iter-v3/005 wrong-premise QR work was discarded via reset, and ONE new code commit was applied:

- `9314db4 fix(iter-v3/006): plumb outer seed into inner ensemble derivation` (the seed-plumbing fix + 6 adversarial tests)

iter-v3/004's recompute fix (`0aa64df fix(iter-v3/005): recompute_10seed reads headline metrics from comparison.csv`) is carried over via the branching. iter-v3/005's BLOCK-causing structural Pareto issue (identical 10-row pareto_front.csv from hardcoded ENSEMBLE_SEEDS) is the structural defect the seed-plumbing fix targets.

Critical inheritance verifiers (run before any code edits):
- `git log --oneline iteration-v3/006 -- src/crypto_trade/strategies/ml/validation_v3.py | wc -l` ≥ 1
- `git log --oneline iteration-v3/006 -- run_baseline_v3.py | wc -l` ≥ 1
- `test -f tests/strategies/ml/test_outer_seed_propagation.py` (THIS iteration's new test)
- `test -f tests/strategies/ml/test_per_cell_pbo_synthetic.py` (iter-v3/004 inherited)
- `test -f tests/strategies/ml/test_ensemble_seed_propagation.py` (iter-v3/005 inherited)
- `uv run pytest tests/strategies/ml/ -v` exits 0 with 35/35 PASS

### 3.9 Engineer's Phase 6 work plan (informative, not mandatory)

1. Verify §3.8 inheritance preconditions.
2. Temporarily reduce `V3_MODELS` in `run_baseline_v3.py` to BCH-only:
   ```python
   V3_MODELS: tuple[tuple[str, str], ...] = (
       ("A (BCHUSDT)", "BCHUSDT"),
   )
   ```
   This is a Phase-6 LOCAL edit; the QE may revert it before commit OR ship a `--symbols` CLI flag. Either way, the Phase-6 invocation runs on BCH-only.
3. Update `REQUIRED_GAP` if `n_symbols=1` is detected (or assert the existing `REQUIRED_GAP=88` is the multi-symbol global, with per-cell gap = 22). Confirm that no per-cell verifier breaks under `n_symbols=1`.
4. Pre-flight: `--seeds 1 --n-trials 10` BCH-only. Wall-clock estimate: 30-45 min.
5. Persist outputs to `reports-v3/iteration_v3-006/seeds_1/` (new sub-directory pattern, distinct from the iter-v3/005 layout that mixed all seeds together).
6. Run `--seeds 2 --n-trials 10` BCH-only. Wall-clock estimate: 60-90 min total (incremental on top of step 4 if implementation runs them sequentially).
7. Persist outputs including `pareto_front.csv` to `reports-v3/iteration_v3-006/`.
8. Run `uv run pytest tests/strategies/ml/ -v` → 35/35 PASS.
9. Verify §3.6 reconciliation table — every verifier exits 0.
10. Write `engineering_report.md` + `engineering_report_summary.json` including: (a) wall-clock per run, (b) trade counts per seed, (c) per-seed Sharpe std value, (d) git SHAs, (e) hardware, (f) library versions.

Estimated total wall-clock: ~90-120 min (BCH-only, n_trials=10 keeps Optuna fast).

---

## Section 4 — Expected OOS Impact

### 4.1 Predicted impact on iteration metrics

Headline metrics WILL DIFFER from iter-v3/003's baseline because the inner ensemble seeds are different (the legacy hardcoded `[42, 123, 456, 789, 1001]` is replaced by `_derive_ensemble_seeds(42)=[191664963, 1662057957, 1405681631, 942484272, 929893137]` for outer seed 42). **This is the FIRST iteration where headline metrics differ from iter-v3/003 — that is expected and the iteration's whole point.**

| Metric | iter-v3/003 (legacy hardcoded ensemble) | iter-v3/006 (`--seeds 1`, outer=42) prediction | Δ |
|---|---:|---:|---:|
| BCH-only IS monthly Sharpe | depends on iter-v3/003 BCH-only sub-row | DIFFERENT (model retrained with new ensemble seeds) | uncertain |
| BCH-only OOS monthly Sharpe | depends on iter-v3/003 BCH-only sub-row | DIFFERENT (same reason) | uncertain |
| Per-seed Sharpe std (`--seeds 2`) | n/a (iter-v3/003 was single-seed) | **> 0** (THE iteration's central test) | **must be > 0** |

The headline metric values are deliberately NOT predicted as point estimates because (a) Phase 5 has not seen any backtest run with `_derive_ensemble_seeds(42)`, (b) `--n-trials 10` (vs the standard 50) shifts Optuna trajectories, and (c) BCH-only single-symbol runs differ structurally from the 4-symbol runner. iter-v3/006's MERGE evaluation is METHODOLOGY-ONLY (Section 8).

### 4.2 NEW metric — per-seed Sharpe std (the iteration's headline)

| Metric | Prediction | Falsifier |
|---|---:|---|
| `pareto_front.csv` row count (under `--seeds 2`) | 2 | If <2, sub-fix #3 not implemented (Falsifier 1 below) |
| Per-seed Sharpe std across 2 outer seeds | **strictly > 0** | If 0, model RNG ignores the inner ensemble seeds — fix did NOT propagate (Falsifier 2) |
| Trades CSV (`--seeds 1` outer=42) byte-identical to iter-v3/003's trades CSV | False | If True, fix did NOT change model behavior at all (Falsifier 3) |
| Total Phase 6 wall-clock | < 2h on BCH-only | If > 2h, escalate to QR for diagnostic (Falsifier 4) |

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: `pareto_front.csv` has fewer than 2 rows under `--seeds 2` → sub-fix #3 not implemented (engineer regressed on `--seeds 2` support, OR the runner short-circuited on the single-seed default path).

**Falsifier 2** (the iter-v3/005 false-positive recurrence test): per-seed Sharpe std = 0 under `--seeds 2` → outer seed not propagating through the LightGBM model RNG. Specifically: `_derive_ensemble_seeds(outer_seed)` returns distinct lists (verified at producer side, Section 2.1-2.3), but if the inner ensemble averaging dampens RNG variance to zero, OR if the LightGBM `random_state` ignores the inner seed parameter, the per-seed Sharpe will be identical.

**Falsifier 3**: Under `--seeds 1 --n-trials 10` (outer=42), the BCH-only IS trades CSV is byte-identical to iter-v3/003's BCH-only sub-row trades CSV → the seed change had ZERO effect on model behavior. This would mean the LightGBM training is dominated by data shuffling that ignores the inner ensemble seed. **Note**: iter-v3/003 ran at `--n-trials 50`, so a divergent trades CSV is overdetermined (n_trials change alone differs); a strict byte-equivalence check would be near-vacuous. The reconciliation row 9 verifier in §3.6 instead asserts the trades are NOT identical to iter-v3/003, which is a strict-superset check.

**Falsifier 4**: Phase 6 wall-clock on `--seeds 2` BCH-only `--n-trials 10` exceeds 2h → budget overrun; escalate to QR (the iter-v3/006 budget premise is "minimum-cost validation").

**Process falsifier**: `tests/strategies/ml/test_outer_seed_propagation.py` is REVERTED or its tests are made trivial → 6/6 PASS becomes vacuous. Reconciliation row 1 catches this case.

### 4.4 Expected MERGE outcome — methodology-only pathway

iter-v3/006 is a methodology-only iteration. Section 8 has 10 criteria, all methodology-stack. The headline-metric criteria (IS Sharpe > 1.0, OOS Sharpe > 1.0, etc.) used in iter-v3/004 / iter-v3/005 are explicitly DEFERRED to iter-v3/008 (the 10-seed run). iter-v3/006 PASSes if and only if:

1. Sub-fix #1 verifier (35/35 tests) PASSES
2. Sub-fix #2 verifier (`--seeds 1` produces comparison.csv) PASSES
3. Sub-fix #3 verifier (`--seeds 2` produces 2-row pareto_front.csv) PASSES
4. **Per-seed Sharpe std > 0** PASSES (Section 8 criterion 4 — the iter-v3/005 false-positive killer)
5. Wall-clock < 3h PASSES
6. Critic OVERALL = MERGE

The DSR / single-seed Pareto / OOS Sharpe / etc. headline-metric questions are NOT in scope for iter-v3/006's MERGE evaluation. They belong to iter-v3/008.

---

## Section 5 — Risk Mitigation

### 5.1 NEW structural safeguards

iter-v3/006 introduces three structural safeguards relative to iter-v3/005's BLOCK:

1. **Per-seed Sharpe std > 0 verifier** (§3.6 reconciliation row 5). This is the iter-v3/005 false-positive killer: iter-v3/005's pareto_front.csv had 10 tied rows (all seeds produced identical trade distributions because ENSEMBLE_SEEDS was hardcoded). The reconciliation row 5 asserts cross-seed variance is strictly positive. If FALSE, the fix did not propagate to model RNG and iter-v3/006 NO-MERGEs explicitly.

2. **Pre-flight: 6 adversarial tests in test_outer_seed_propagation.py must pass before backtest.** The Phase 6 work plan step 1 prescribes `uv run pytest tests/strategies/ml/test_outer_seed_propagation.py -v` BEFORE any backtest run. If ANY of the 6 tests fails, the producer-side derivation is broken and the consumer-side test would be a waste of compute.

3. **Wall-clock cap: cancel run if `--seeds 2` exceeds 2h on BCH-only**. The QE escalates to the QR for diagnostic (likely cause: parquet I/O bottleneck or accidental n_trials=50 default override).

### 5.2 Methodology-pipeline safety

Three additional safeguards:

1. **File-artifact reconciliation table** (§3.6). 10 verifier commands map to specific file artifacts. Empty cells = Phase 5.5 BLOCK. Verifier commands MUST execute and exit 0 post-Phase 6.

2. **Pre-flight on `--seeds 1` BEFORE `--seeds 2`** (Phase 6 work plan step 4). Catches the case where `--seeds 2` modification breaks the existing single-seed path. The Phase-6 step 4 reuses the iter-v3/005 pre-flight discipline.

3. **Sub-fix #1 (already shipped at SHA `9314db4`) verified at brief-time**. The 6 adversarial tests already PASS — Phase 6 must re-confirm but does not need to invent new tests.

### 5.3 NO new model-level risks introduced

The iter-v3/006 fix changes the inner ensemble's seed list, NOT any model hyperparameter, feature, or risk gate. Any drift in IS Sharpe from iter-v3/003's BCH-only sub-row can ONLY be attributed to the seed change — there is no co-modification confound.

The `--seeds 2` cross-seed variance introduces NEW cross-seed measurement, which is what the methodology test is designed to surface. This is a TRANSPARENCY safeguard, not a NEW risk.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — IDENTICAL TO iter-v3/005

| # | Primitive | Spec | Fire-rate prediction (IS) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX > 20 | ≈ 60% of bars pass | Trending only |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.5 | ≈ 5–8% killed | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±20% | ≈ 7–8% killed | Macro flips |

Combined kill rate target: 69–78%. Same as iter-v3/005.

### 6.2 Regime coverage — UNCHANGED

The BCH-only IS data spans 2020-01 → 2025-03-23. Regime coverage includes 2020 COVID, 2021 bull, 2022 LUNA/FTX, 2023 banking, 2024 halving + Trump rally, 2025 January correction.

### 6.3 Concentration — automatic by design

BCH-only single-symbol run means BCH owns 100% of OOS PnL by construction. Concentration cap (≤30%) is N/A for iter-v3/006 by design (single-symbol scope). Restored as a meaningful constraint in iter-v3/007 (full universe).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

iter-v3/004's 5/5 calibration win demonstrated the "≥3 process-level predictions" discipline. iter-v3/006's Section 7 inherits that discipline, with the model-level predictions reflecting the iter-v3/006 scope.

**Prediction P1 (process-level, P=25%): outer seed plumbed correctly into LightGbmStrategy `ensemble_seeds`, BUT LightGBM's underlying training is dominated by data shuffling that ignores the inner seed → cross-seed Sharpe std remains < 0.05.** The seed plumbs end-to-end at the producer side (Section 2 verified). However, if LightGBM's `LGBMClassifier(random_state=...)` call is missed in `_train_for_month` OR if the inner ensemble averaging operator is byte-stable across different inner ensembles (e.g., always returns the mean prediction without seed-specific weighting), then per-seed cross-seed variance could be near-zero. **Detection signal**: per-seed Sharpe std under `--seeds 2` is in [0, 0.05]. **Mitigation**: Phase 6 work plan step 1 prescribes reading `LightGbmStrategy._train_for_month` to confirm seeds propagate to `LGBMClassifier(random_state=...)` AND to the inner ensemble averaging. If the strict equality (std=0) holds, Falsifier 2 fires; if the std is in (0, 0.05], iter-v3/006 PASSES the methodology gate but iter-v3/007 must investigate the small variance explicitly.

**Prediction P2 (process-level, P=15%): the `--seeds 2` run hits a non-deterministic compute (e.g., OpenMP thread-count, GPU vs CPU non-determinism), producing different trades on re-run.** The seed-plumbing fix is deterministic at the algebra level (verified Section 2), but downstream LightGBM tree splits or numpy reductions could be non-deterministic. **Detection signal**: re-running `--seeds 1 --n-trials 10` produces different `comparison.csv` files. **Mitigation**: pre-flight with `--seeds 1` twice, assert byte-identical comparison.csv. Engineering report Section X documents the byte-identity check explicitly.

**Prediction P3 (process-level, P=10%): wall-clock overshoot to >2h on BCH-only.** Possible causes: (a) parquet I/O regresses, (b) Optuna's TPESampler is more expensive at the new seed values, (c) the runner's `--seeds 2` path re-loads features twice instead of caching. **Detection signal**: total Phase 6 wall-clock > 2h on BCH-only `--seeds 2 --n-trials 10`. **Mitigation**: QR cancels run and the QE reports the cause in the engineering report.

**Prediction P4 (model-level, P=30%): cross-seed Sharpe std is positive but small (<0.05).** The 5-seed inner ensemble averages 5 LightGBM predictions per bar, which mathematically dampens any individual seed's variance. The per-outer-seed inner ensembles use 5 DIFFERENT 5-seed lists, but the dampening from averaging may still leave only a small residual cross-outer-seed variance. **Pre-registered: this is INFORMATIVE, suggests inner-ensemble averaging dampens RNG variance.** iter-v3/007 (5 seeds) will run more outer seeds to characterize the distribution — if the std is small but positive, iter-v3/007's 5-row pareto_front.csv will surface the distribution shape.

**Prediction P5 (model-level, P=70%): `--seeds 1` (outer=42) produces a `comparison.csv` with `monthly_sharpe` DIFFERENT from iter-v3/003's BCH-only sub-row.** Because ensemble seeds differ, Optuna trials differ, model parameters differ, and the OOS trade distribution differs. **Pre-registered as expected behavior, NOT a defect.** The diary records the monthly_sharpe value and proceeds to iter-v3/007 if Critic approves.

The predictions are intentionally Bayesian-calibrated:
- 3 process-level (P1, P2, P3) per the iter-v3/003 lesson #3 discipline
- 2 model-level (P4, P5) per the historical class

If any of P1–P5 fails to materialize, the iter-v3/006 diary documents the calibration miss and updates the v3 skill's failure-mode taxonomy.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

**These thresholds are LOCKED before backtest. Phase 7 evaluation applies them mechanically.**

iter-v3/006 is a **methodology-only iteration**. The 10 criteria below are scoped to the seed-plumbing validation; the headline-metric criteria from iter-v3/005 (IS Sharpe > 1.0, OOS Sharpe > 1.0, OOS/IS ≥ 0.5, ≥130 OOS trades, etc.) are DEFERRED to iter-v3/008 (the 10-seed run on full universe).

### MERGE iff ALL of the following are true:

| # | Criterion | Threshold | Source |
|---|---|---:|---|
| 1 | Sub-fix #1 (seed derivation) ships: 6/6 tests pass at SHA `9314db4` | TRUE (already verified) | §3.5 #1 |
| 2 | Sub-fix #2 (`--seeds 1`) produces a complete comparison.csv on BCH-only | TRUE | §3.5 #2 |
| 3 | Sub-fix #3 (`--seeds 2`) produces a 2-row pareto_front.csv | TRUE | §3.5 #3 |
| 4 | **Per-seed Sharpe std > 0** (the iter-v3/005 false-positive killer) | TRUE — **THIS IS THE ITERATION'S CENTRAL TEST** | §3.6 row 5 |
| 5 | `--seeds 2` wall-clock < 2h | TRUE (else QR escalates) | §5.1 safeguard 3 |
| 6 | 35/35 adversarial tests pass | TRUE (29 inherited + 6 new) | §3.6 row 6 |
| 7 | Critic OVERALL = MERGE (not BLOCK) | TRUE | v3 mandatory |
| 8 | NO new features added | TRUE (vacuous; nothing changed) | §3.7 |
| 9 | NO 10-seed run executed (this iteration's scope is 1+2 seeds) | TRUE | §3.7 / project direction |
| 10 | Reconciliation table no empty cells, all 10 verifiers exit 0 | TRUE | §3.6 |

### NO-MERGE iff ANY of:

- Any of the 10 criteria fails
- Engineer's Phase 6 wall-clock exceeds 3h (lower than iter-v3/005's 60min cap because iter-v3/006 explicitly budgets ~90-120 min)
- Phase 5.5 gate emits BLOCK
- Phase 7.5 Critic emits BLOCK

### Discretionary judgment — methodology MERGE pathway

iter-v3/006 has NO split-merge clause because the iteration scope IS methodology-only. The MERGE pathway requires criteria 1, 4, 6, 7, 10 ALL passing — that is the methodology contract.

**Headline-metric criteria are explicitly DEFERRED to iter-v3/008 (10-seed)**:
- IS Sharpe > 1.0 — DEFERRED
- OOS Sharpe > 1.0 — DEFERRED
- OOS/IS ratio ≥ 0.5 — DEFERRED
- ≥130 OOS trades — DEFERRED
- ≥10 trades/month OOS — DEFERRED
- Top-symbol concentration ≤ 30% — DEFERRED (BCH-only single-symbol invalidates anyway)
- DSR > 0.95 — DEFERRED
- Worst-symbol OOS wpnl floor — DEFERRED
- OOS MaxDD ≤ 30% — DEFERRED
- All 4 symbols ≥ 1 OOS trade — DEFERRED (BCH-only invalidates anyway)
- 10-seed mean Sharpe > 0, ≥7/10 profitable — DEFERRED (iter-v3/008's primary merit)

**iter-v3/006 cannot MERGE with full headline metrics — that is by design.** It validates the seed-plumbing fix structurally so that iter-v3/007 (5-seed) and iter-v3/008 (10-seed) can run on a sound base.

---

## Section 9 — Library Stack Declaration

| Package | Version pinned | License | Usage | Fallback if install fails |
|---|---|---|---|---|
| `numpy` | (already installed) | BSD-3 | `np.random.default_rng` for `_derive_ensemble_seeds` | n/a |
| `scipy` | (already installed) | BSD-3 | (no use this iteration) | n/a |
| `statsmodels` | (already installed) | BSD-3 | `tsa.stattools.adfuller` for per-(sym, feat, month) ADF (unchanged) | n/a |
| `scikit-learn` | (already installed) | BSD-3 | `TimeSeriesSplit` in `_objective` (unchanged) | n/a |
| `lightgbm` | (already installed) | MIT | M1 only — no M2 | n/a |
| `pytest` | (already installed) | MIT | Adversarial unit tests (29 inherited + 6 new = 35) | n/a |
| `pandas` | (already installed) | BSD-3 | Parquet I/O (unchanged) | n/a |
| `pyarrow` | (already installed via pandas) | Apache-2 | Parquet engine (unchanged) | If missing, pandas auto-falls back to fastparquet |

**No new external deps.** The iteration's NEW code is:
- 1 analysis script + 5 output artifacts (already committed at SHA `03b6004`)
- 0 new pytest test files (the 6 tests in `test_outer_seed_propagation.py` were committed at SHA `9314db4`)
- 0 modifications to `run_baseline_v3.py` beyond SHA `9314db4` (Phase 6's BCH-only scoping is local)

### Aggregator strategy — UNCHANGED from iter-v3/005

Per-cell PBO with cross-cell mean aggregation. Per-cell n_eff with cross-cell median aggregation. The aggregator choices are fixed; iter-v3/006 only validates the outer-seed dimension produces distinct ensembles, distinct trades, and distinct Sharpes.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-006/engineering_report.md` with:
- The git commit SHAs at backtest time (expected: `03b6004` analysis script + `9314db4` seed-plumbing fix)
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|pytest|pandas|pyarrow)"`
- The 2-row `pareto_front.csv` summary (per-seed Sharpe values, std, max, min)
- The `--seeds 1` vs `--seeds 2` wall-clock breakdown
- The `tests/strategies/ml/test_outer_seed_propagation.py` test outcome (PASS/FAIL with sample count)
- The Phase 6 step 1 reading of `LightGbmStrategy._train_for_month` confirming `random_state` propagation (Prediction P1 mitigation)

---

## Appendix — Phase 5.5 Gate Self-Check

The QR has self-verified all 10 mandatory sections plus the Phase 5.5 inputs:

| Section | Status |
|---|---|
| 0 — Data Split | PASS — sacred constants UNCHANGED; ensemble_size=5 UNCHANGED; only the inner-seed list derivation changes |
| 1 — Hypothesis | PASS — one sentence; specific testable target (per-seed Sharpe std > 0 under `--seeds 2`); falsifiers in §4.3 |
| 2 — IS-Only Numerical Evidence | PASS — `analysis/iteration_v3-006/seed_derivation_demo.py` committed at SHA `03b6004` BEFORE this brief; 5 outputs committed; results inline in §2.1-2.4 |
| 3 — Proposed Changes | PASS — symbols SCOPED to BCH-only for THIS iteration only (NOT permanent); labeling UNCHANGED; features UNCHANGED; risk gates UNCHANGED; decomposed into 3 sub-fixes in §3.5; brief-vs-code reconciliation table in §3.6 with 10 file-artifact verifiers; inheritance plan in §3.8 |
| 4 — Expected OOS Impact | PASS — predicted metric table with 4 falsifiers in §4.3; methodology-only MERGE pathway in §4.4 |
| 5 — Risk Mitigation | PASS — 3 NEW structural safeguards in §5.1 + 3 methodology-pipeline safeguards in §5.2 |
| 6 — Risk Management Design | PASS — 7-primitive table identical to iter-v3/005; concentration N/A by single-symbol design |
| 7 — Pre-Registered Failure-Mode | PASS — 5 predictions with **3 process-level (P1, P2, P3)** per iter-v3/003 lesson #3 |
| 8 — Pre-Registered MERGE/NO-MERGE | PASS — 10 criteria; methodology-only pathway; headline-metric criteria EXPLICITLY DEFERRED to iter-v3/008 |
| 9 — Library Stack | PASS — no new deps; aggregator strategy unchanged from iter-v3/005 |

Engineer: please run Phase 5.5 gate verification against the brief-vs-code reconciliation table in Section 3.6. Empty cells in the right column = BLOCK. Verifier commands that do NOT execute and exit 0 post-Phase 6 = NO-MERGE per Section 8 criterion 10.
