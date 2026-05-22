# Iteration v3-058 — Research Brief (BASELINE RE-ANCHOR under post-fix walk-forward)

**Type**: RE-ANCHOR (special category — CONFIRMATION-spec EXPLORATION; NOT a regular cycle iteration)
**Track**: v3 (rigor arm) — fifty-eighth iteration
**Branch**: `iteration-v3/058` (created from `iteration-v3/057` head at SHA `414368a`; includes walk-forward fix at `e149e9d` + Critic enhancement at `414368a`)
**Date**: 2026-05-12
**Author**: QR (autopilot, orchestrator-mandated)
**EDA SHA**: N/A — RE-ANCHOR runs the EXACT iter-v3/028 BASELINE_V3.md bundle. No new EDA required.

**MANDATED AXIS** (per orchestrator user directive 2026-05-12 path (a)):
This is **NOT a new axis**. /058 verifies the EXACT iter-v3/028 BASELINE_V3.md bundle
composition under the post-fix walk-forward (commit `e149e9d`). Per memory rule
`feedback_v3_walkforward_lookahead_bug.md` action item #3 (USER DECISION 2026-05-12 path a):

> ALL v3 iterations PRE-`e149e9d` are INVALIDATED. BASELINE_V3.md anchor (iter-v3/028) and
> all subsequent cycle results (/029-/057 setup) are produced from BUGGY walk-forward and
> cannot be trusted as ground truth.
>
> Pending: Re-run BASELINE_V3.md establishing iteration (iter-v3/028) with fix to obtain
> UNBIASED baseline anchor.

iter-v3/058 IS that re-run. The output of /058 BECOMES the new BASELINE_V3.md anchor for
cycle 1 #1 onwards (iter-v3/059), regardless of the metric direction (lift OR regression).

**WHAT CHANGES vs /057 setup** (SHA `8ab05dc`):
1. **REVERT the /057 A4 SWAP**: parkinson_gk_ratio_20 OUT, ret_skew_50 IN at V3_FEATURE_COLUMNS_TOP_N
2. **ITERATION_LABEL** = "v3-058"
3. **Spec**: CONFIRMATION-spec `--seeds 2 --n-trials 35 --clean-oof` (5 inner × 2 outer = 10 models/cell)
4. **Test file housekeeping**: revert /057 changes to `tests/features/test_features_for_symbol.py`; keep `tests/features/test_parkinson_gk_ratio_20_past_only.py` but inert/skipped (compute function in `price_efficient_vol_v3.py` stays as dead code for future use)
5. **Walk-forward**: NEW post-fix `walk_forward.generate_monthly_splits` from `e149e9d` (purges last ~22 training candles per (model, month) via embargo)
6. **Critic protocol**: /058 is the FIRST iteration audited under the enhanced Critic protocol (Foundation Audit Boot Steps 9-11 + Check 13 Anti-Pattern Static Scan + §11 Anti-Pattern Catalog at SHA `414368a`)

**WHAT STAYS UNCHANGED from /028 BASELINE_V3.md spec**:
- V3_FEATURE_COLUMNS_TOP_N (14): `max_dd_window_50, ema_spread_atr_20, ret_kurt_50, ret_skew_200, range_realized_vol_50, hurst_diff_100_50, ret_kurt_200, hurst_100, btc_ret_14d, ret_skew_50, vwap_dev_20, ret_autocorr_lag1_50, sym_vs_btc_ret_7d, regime_momentum_signed_5d`
- V3_MODELS: (BCHUSDT, LDOUSDT, TRXUSDT)
- V3_ATR_MULTIPLIERS_PER_SYMBOL: {} (empty; default (2.0, 1.0) for all)
- RiskV2Config: block_long_for=(), adx_threshold_per_symbol={}, enable_per_symbol_drawdown_brake=False, regime_gate_symbols=()
- REQUIRED_GAP = 66 = (21+1)×3
- ENSEMBLE_SIZE = 5 (inner)
- CPCV: n_paths=45, embargo=27
- Sacred constants: OOS_CUTOFF_DATE=2025-03-24, training_months=24

**STRATEGY CHANGE**: NONE at strategy / signal / risk / labeling level. /058 = bit-revert
to /028 config + post-fix walk-forward + CONFIRMATION-spec multi-seed. The ONLY substantive
change vs the original /028 run is the corrected walk-forward (no lookahead at train/test
boundary).

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # inner ensemble (5 inner seeds: 42, 123, 456, 789, 1001)
outer_seeds      = 2              # 42, 123 (CONFIRMATION-spec; per `feedback_outer_seed_cap_2_v3.md`)
n_trials         = 35             # CONFIRMATION default (per `feedback_v3_confirmation_n_trials_35.md`)
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees iter-v3/058 OOS metrics for the FIRST time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: RE-ANCHOR (special category)
  - Subset of: EXPLORATION (CONFIRMATION-spec)
  - NOT a cycle iteration (NOT subject to cycle 4 cadence; cycle 4 RESET to ZERO per
    `feedback_v3_walkforward_lookahead_bug.md` action item #5)
  - NOT a competitive CONFIRMATION (this is INTEGRITY CORRECTION of /028 BASELINE_V3.md anchor)

Cycle counting: cycle 4 cadence RESET to ZERO. After /058, cycle 1 starts fresh:
  - iter-v3/059 = CYCLE 1 #1 of 10 EXPLORATIONs (post-fix cycle)
  - iter-v3/068 = CYCLE 1 CONFIRMATION (or earlier per cadence discipline)
  - Mass feature expansion mandate (per `feedback_v3_mass_feature_expansion.md`)
    currently queued for iter-v3/062 — REVIEW this queue when /058 lands.

Wall-clock budget: <= 6h hard cap (CONFIRMATION-spec; per `feedback_v3_cadence_discipline.md`)
Spec: uv run python run_baseline_v3.py --seeds 2 --n-trials 35 --clean-oof
  - ENSEMBLE_SIZE=5 (auto; inner ensemble seeds [42, 123, 456, 789, 1001])
  - n_trials=35 (CONFIRMATION default; same as /018 and /028)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=2 (CONFIRMATION-spec; seeds 42, 123)
  - --clean-oof (use guardrail from SHA `6a216b5`)

Re-anchor state from iter-v3/028 BASELINE_V3.md (REVERTED from /057 setup):
  - V3_FEATURE_COLUMNS_TOP_N = 14 features (parkinson_gk_ratio_20 OUT, ret_skew_50 IN)
  - V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — UNCHANGED
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty) UNCHANGED
  - block_long_for = () (empty) UNCHANGED
  - regime_momentum_signed_5d PRESERVED UNCHANGED
  - DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) UNCHANGED
  - adx_threshold_per_symbol = {} (empty) UNCHANGED
  - All other risk gates UNCHANGED (BTC trend, OOD, ADX 20.0, hit-rate disabled, etc.)
  - REQUIRED_GAP = 66 = (21+1)×3 UNCHANGED
  - enable_per_symbol_drawdown_brake = False UNCHANGED
  - dsr.json schema additions (dsr_relative, cpcv_path_sharpe_q75) from /056 head PRESERVED

POST-FIX walk-forward change (cherry-picked from main `5566a69` at v3 SHA `e149e9d`):
  - `walk_forward.compute_embargo_candles(timeout_minutes, interval_minutes)` helper NEW
  - `generate_monthly_splits()` signature change: now requires timeout+interval, applies
    embargo so `train_end_ms = test_start_ms - embargo_candles * interval_ms`
  - `lgbm._train_for_month()` reuses helper for `cv_gap`
  - Regression test coverage in `tests/test_lookahead_embargo.py` (42/42 PASS at v3 head)

Setup commit changes (locked in §3):
  - src/crypto_trade/features_v3/__init__.py: REVERT /057 SWAP (parkinson_gk_ratio_20 → ret_skew_50)
  - run_baseline_v3.py: ITERATION_LABEL "v3-058" + `_verify_feature_columns` assertions reverted
  - tests/features/test_features_for_symbol.py: revert /057 changes (ret_skew_50 PRESENT, parkinson_gk_ratio_20 ABSENT)
  - tests/features/test_parkinson_gk_ratio_20_past_only.py: KEEP file but mark tests as @pytest.mark.skip (inert; compute path retained as dead code)
```

---

## Section 1 — Hypothesis

**SINGLE HYPOTHESIS**: The /028 bundle (V3_FEATURE_COLUMNS_TOP_N 14 features, V3_MODELS
BCH+LDO+TRX, default ATR (2.0, 1.0), no drawdown brake, no block_long_for, no regime gate)
under the post-fix walk-forward (commit `e149e9d`) produces unbiased multi-seed mean
Sharpe values that establish the NEW BASELINE_V3.md anchor for cycle 1+.

**Mechanism**: The lookahead-bias bug in `walk_forward.generate_monthly_splits` caused the
last ~22 training candles per (model, month) per symbol to have triple-barrier labels whose
forward scan read price data from INSIDE the test month. This biased IS+OOS Sharpe UPWARD
across ALL v3 iterations (cycles 1-4). The fix at `e149e9d` purges these embargoed candles
from the training window (~1-2% training data loss). The re-run at /058 measures the bundle's
TRUE generalization without lookahead at the train/test boundary.

**What this iteration tests**: only the magnitude of the bias correction. The structural
question — "is regime_momentum_signed_5d a genuine multi-seed-validated edge ingredient?" —
is RE-EVALUATED, but the bundle composition is FIXED (no axis variation).

**What this iteration does NOT test**:
- ANY axis variation (no feature SWAP, no risk primitive change, no labeling change, no
  model arch change, no universe change)
- ANY methodology-only axis (DSR_relative gate reformulation deferred to cycle 1 EXPLORATIONs)
- ANY new feature family (mass feature expansion deferred to /062 cycle 5 — RE-REVIEW after /058)
- 15th-slot SWAP (CLOSED per /054)
- Per-symbol customizations (CLOSED for cycle 4)

---

## Section 2 — IS-Only Numerical Evidence

**NO new EDA required.** This is an INTEGRITY CORRECTION, not signal discovery. The bundle
composition is FIXED at /028 BASELINE_V3.md spec.

### Section 2.1 — Source spec (BASELINE_V3.md /028 bundle)

Direct citation from `BASELINE_V3.md` (canonical baseline, last updated 2026-05-08):

| Spec element | Value | Source |
|---|---|---|
| V3_FEATURE_COLUMNS_TOP_N | 14 features (see Section 1) | BASELINE_V3.md §Code Configuration |
| V3_MODELS | (BCHUSDT, LDOUSDT, TRXUSDT) | BASELINE_V3.md §Code Configuration |
| ATR multipliers | (atr_tp=2.0, atr_sl=1.0) default for all symbols | BASELINE_V3.md §Code Configuration |
| Labeling | triple-barrier, 21-candle (10080-min / 8h) timeout | BASELINE_V3.md §Code Configuration |
| ENSEMBLE_SIZE | 5 inner ensemble (seeds [42,123,456,789,1001]) | BASELINE_V3.md §Code Configuration |
| outer_seeds | 2 (42, 123) | BASELINE_V3.md §Code Configuration |
| n_trials | 35 per cell (1050 total = 35 × 3 sym × 2 outer × 5 inner) | BASELINE_V3.md §Code Configuration |
| CPCV | n_paths=45, embargo=27, REQUIRED_GAP=66 | BASELINE_V3.md §Code Configuration |
| Risk gate stack | 7 primitives (BTC trend, vol scaling, ADX 20, Hurst, z-score OOD 2.0, low-vol, hit-rate disabled) | BASELINE_V3.md §Code Configuration |

### Section 2.2 — Citations

1. **BASELINE_V3.md** (this worktree) — canonical /028 baseline spec (commit ef18e1d).
2. **`feedback_v3_walkforward_lookahead_bug.md`** (memory rule, 2026-05-12) — codifies the
   lookahead bug + INVALIDATION rule for all pre-`e149e9d` iterations.
3. **commit `e149e9d`** (v3 worktree, 2026-05-12) — cherry-picked walk-forward fix from
   main commit `5566a69`. 42/42 lookahead-embargo + lgbm regression tests pass at v3 head.
4. **commit `414368a`** (v3 worktree, 2026-05-12) — Critic agent enhancement (Foundation
   Audit Boot Steps 9-11, Check 13 Anti-Pattern Static Scan, §11 Anti-Pattern Catalog).
   /058 is the FIRST iteration audited under enhanced protocol.

### Section 2.3 — No new tables required

Per orchestrator directive: "NO new EDA required. Cite BASELINE_V3.md /028 bundle spec +
lookahead fix memory rule." All numerical evidence for the /028 bundle composition is
already documented in `BASELINE_V3.md`. The brief Section 4 expected impact predictions
anchor on the BIASED /028 numbers (+0.5101 IS / +0.5053 OOS multi-seed mean) but with
explicit awareness that those numbers are no longer ground truth.

---

## Section 3 — Code Changes (Setup Commit Locked)

The setup commit makes 4 edits and 1 test file modification. ALL changes localized to
`src/crypto_trade/features_v3/__init__.py` + `run_baseline_v3.py` + `tests/features/`.
NO changes to model/training/risk/labeling code. The post-fix walk-forward is ALREADY in
place at branch head (cherry-pick `e149e9d`).

### Edit 1: `src/crypto_trade/features_v3/__init__.py` — REVERT /057 SWAP

REPLACE the V3_FEATURE_COLUMNS_TOP_N tuple element `"parkinson_gk_ratio_20"` with
`"ret_skew_50"` (RESTORE the /028 BASELINE_V3.md composition). Update the preceding
comment block to reflect the iter-v3/058 RE-ANCHOR rationale:

```python
# iter-v3/057: ret_skew_50 SWAPPED for parkinson_gk_ratio_20 (A4 base-stack reordering).
# iter-v3/058: REVERT to /028 BASELINE_V3.md composition for RE-ANCHOR under post-fix
#              walk-forward (commit `e149e9d`). Per memory rule
#              `feedback_v3_walkforward_lookahead_bug.md` user-decision path (a):
#              all pre-`e149e9d` v3 iterations INVALIDATED. /058 re-anchors BASELINE_V3.md.
# Resulting tuple: 14 features identical to /028 spec. parkinson_gk_ratio_20 dropped
# (compute function in price_efficient_vol_v3.py retained as dead code; available for
# future cycle 1+ EXPLORATIONs without re-implementation cost).
"ret_skew_50",  # RESTORED iter-v3/058 — /028 BASELINE_V3.md composition for RE-ANCHOR
```

The comment block PRESERVES the /041/042/057 history (audit trail per `feedback_always_document.md`).
The tuple stays at 14 elements; ONE element is substituted (the inverse of the /057 SWAP).

### Edit 2: `run_baseline_v3.py` — ITERATION_LABEL + `_verify_feature_columns` assertions

```python
ITERATION_LABEL = "v3-058"
```

In `_verify_feature_columns`, REVERT the /057 assertions:

```python
# iter-v3/058: RE-ANCHOR — REVERT /057 SWAP.
# ret_skew_50 MUST be present (RESTORED at iter-v3/058 — /028 BASELINE_V3.md re-anchor).
# parkinson_gk_ratio_20 MUST NOT be present (SWAPPED OUT at iter-v3/058 — RE-ANCHOR).

if "ret_skew_50" not in V3_FEATURE_COLUMNS:
    raise RuntimeError(
        "ret_skew_50 NOT FOUND in V3_FEATURE_COLUMNS — must be PRESENT at iter-v3/058 "
        "(RE-ANCHOR; restore /028 BASELINE_V3.md composition). "
        "Add it back to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )
if "parkinson_gk_ratio_20" in V3_FEATURE_COLUMNS:
    raise RuntimeError(
        "parkinson_gk_ratio_20 FOUND in V3_FEATURE_COLUMNS — must be ABSENT at iter-v3/058 "
        "(RE-ANCHOR; /057 SWAP REVERTED for /028 BASELINE_V3.md re-anchor). "
        "Replace it with 'ret_skew_50' in V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )
```

Also update the docstring at line 192-242 to reflect /058 RE-ANCHOR mandate. Drop the
`/057` SWAP language; restore the /056 description with annotations marking the post-fix
walk-forward.

### Edit 3: `tests/features/test_features_for_symbol.py` — revert /057 changes

REVERT any /057 changes that assert parkinson_gk_ratio_20 in V3_FEATURE_COLUMNS_TOP_N.
Restore the pre-/057 assertions (ret_skew_50 PRESENT, parkinson_gk_ratio_20 ABSENT).

### Edit 4: `tests/features/test_parkinson_gk_ratio_20_past_only.py` — INERT/SKIP

KEEP the test file (do NOT delete — preserves /057's adversarial coverage for future
cycle 1+ EXPLORATIONs). MARK both tests as `@pytest.mark.skip` with reason:

```python
import pytest

@pytest.mark.skip(reason=(
    "iter-v3/058 RE-ANCHOR: parkinson_gk_ratio_20 reverted from V3_FEATURE_COLUMNS_TOP_N. "
    "Test file retained for future cycle 1+ retry. compute_price_efficient_vol_v3 path "
    "still tested by other adversarial tests in price_efficient_vol_v3 suite."
))
def test_parkinson_gk_ratio_20_past_only_discipline():
    ...

@pytest.mark.skip(reason=(
    "iter-v3/058 RE-ANCHOR: parkinson_gk_ratio_20 reverted from V3_FEATURE_COLUMNS_TOP_N. "
    "Test file retained for future cycle 1+ retry."
))
def test_parkinson_gk_ratio_20_within_expected_range():
    ...
```

The `compute_price_efficient_vol_v3` function in `src/crypto_trade/features_v3/price_efficient_vol_v3.py`
stays as dead code (zero revert cost; available for future cycle 1+ EXPLORATIONs).

### Edit 5 (DEFENSIVE-NO-OP): Carry forward state

Verify the following are UNCHANGED at iter-v3/058:
- `V3_MODELS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")`
- `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}`
- `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`
- `RiskV2Config(adx_threshold_per_symbol={}, block_long_for=(), enable_per_symbol_drawdown_brake=False)`
- `REQUIRED_GAP = 66`
- `ENSEMBLE_SIZE = 5`
- walk-forward fix at `e149e9d` is present (verify `walk_forward.compute_embargo_candles`
  helper exists and `generate_monthly_splits` requires `label_timeout_minutes` + `interval_minutes`)

---

## Section 4 — Expected Impact

### Section 4.1 — Mechanism of bias correction

The lookahead bug caused the last ~22 training candles per (model, month) per symbol to
have triple-barrier labels whose forward scan read price data from INSIDE the test month.
Removing this peek reduces training data by ~1-2% (22 candles × 3 syms × ~24 months ÷
total training candles per (model, month)).

**Expected direction**: Sharpe values DEFLATE (training labels no longer "know" the test
month's future). The magnitude is hard to predict exactly because:
1. The biased labels concentrated in the LAST 22 candles per training month, which are
   freshest and have highest impact on tree-leaf calibration.
2. The bias propagates to BOTH IS (in-sample of walk-forward Optuna) AND OOS Sharpe
   measurements via the same mechanism.
3. The lookahead is consistent across all symbols and all months → uniform downward
   correction expected at the bundle level.

### Section 4.2 — Predicted multi-seed mean Sharpe (anchored on /028 BIASED numbers)

Anchor: iter-v3/028 BASELINE_V3.md (biased) multi-seed mean Sharpe **+0.5101 IS / +0.5053 OOS**.

| Metric | /028 (biased anchor) | **/058 prediction band** | Δ vs /028 anchor |
|---|---:|---:|---:|
| IS monthly Sharpe (multi-seed mean) | +0.5101 | **+0.35 to +0.50** | [-0.16, -0.01] |
| OOS monthly Sharpe (multi-seed mean) | +0.5053 | **+0.30 to +0.50** | [-0.21, -0.01] |
| IS Trades (cumulative, multi-seed) | 182 | **170 to 195** (slight reduction from data loss) | [-12, +13] |
| OOS Trades (multi-seed mean) | 93.5 | **85 to 105** (similar; OOS unaffected by training data loss directly) | [-9, +12] |
| IS MaxDD | 41.43% | 38% to 47% | [-4pp, +5pp] |
| OOS MaxDD (multi-seed mean) | 23.53% | 19% to 28% | [-4pp, +5pp] |
| PBO mean | 0.1243 | 0.10 to 0.20 | [-0.02, +0.08] |
| PSR | 1.0 | 0.85 to 1.0 | [-0.15, +0.0] |
| Pareto: both seeds OOS Sharpe > 0 | YES (Gate 10 PASS) | **YES expected** (most plausible); NO is critical concern | -- |

### Section 4.3 — Falsifier outcomes

Per `feedback_axis_saturation_predictor.md`, predicted bands locked upfront. The
INTEGRITY-CORRECTION context means the falsifier is INTERPRETIVE not gate-based:

| Outcome | Probability | What it means |
|---|---:|---|
| **PATH RE-ANCHOR-NORMAL** | 50-60% | IS mean ∈ [+0.35, +0.50] AND OOS mean ∈ [+0.30, +0.50]. /028 bundle is mildly biased; deflation ~10-30%; bundle remains viable cycle 1 anchor. |
| **PATH RE-ANCHOR-MAJOR-DEFLATE** | 15-25% | IS mean OR OOS mean ∈ [+0.05, +0.30]. Bundle bias was substantial (~40-60%); cycle 1 anchor weaker than expected; strategy validity questioned but not refuted. |
| **PATH RE-ANCHOR-COLLAPSE** | 8-15% | IS mean OR OOS mean < +0.05 (i.e., near-zero or negative). Bundle was largely lookahead-driven; **forces re-think of v3 strategy validity entirely**. Cycle 1 mandate likely shifts to MASS feature expansion immediately (no incremental EXPLORATIONs on the /028 stack). |
| **PATH RE-ANCHOR-INVARIANT** | 5-10% | IS mean ≥ +0.51 AND OOS mean ≥ +0.50 (within ±5%). Lookahead bug had ZERO measurable impact → would invalidate the entire lookahead-bias narrative; would force diagnostic deep-dive on why 22-candle embargo had no effect. |
| **PATH RE-ANCHOR-DIVERGE** | 8-15% | IS mean lifts AND OOS mean deflates substantially (or vice versa). Bundle exhibits structural divergence under unbiased walk-forward → bundle is unstable; cycle 1 axis priorities re-evaluate. |

**Locked falsifier**: The Critic CANNOT post-hoc renegotiate which outcome fired. The Section 8
RE-ANCHOR MERGE Criteria establishes path adjudication PRE-RUN.

### Section 4.4 — Behavioral-effect predictor

**Predicted IS trade count delta vs /028 anchor**: -3% to -7% (170-185 IS trades).

Justification: ~22-candle embargo per (model, month) × 24 months × 3 syms ≈ 1584 candles
removed from training. At ~5% trade emission rate, this removes ~80 training candle
entry points across the 24-month IS window. /028 has 182 IS trades cumulative; ~5%
reduction → ~173 IS trades. OOS trade count primarily depends on OOS data + trained
model; less direct correction expected.

**Falsifier**: If observed |IS trade Δ| > 30 trades (i.e., < 152 or > 212), this signals
either (a) the embargo correction affected hyperparameter trajectories substantially more
than expected (PATH RE-ANCHOR-MAJOR-DEFLATE or RE-ANCHOR-DIVERGE) OR (b) the random-seed
realization at /028 was atypical and the /058 value is closer to true generalization.

---

## Section 5 — Risk Mitigation

This is a RE-ANCHOR run. The risk surface is well-bounded:

1. **No strategy / signal / risk / labeling change** — same 7-primitive gate stack as /028
   (BTC trend kill, vol scaling, ADX 20.0, Hurst regime, z-score OOD 2.0, low-vol filter,
   hit-rate disabled). No new code paths exercised.
2. **Post-fix walk-forward already validated** — 42/42 lookahead-embargo + lgbm regression
   tests pass at v3 head (commit `e149e9d`). The embargo helper is tested by
   `tests/test_lookahead_embargo.py::test_labels_are_invariant_to_master_data_extent` —
   the canonical bug property the fix targets.
3. **Drawdown brake DISABLED** — per /054 closeout architectural decision (drawdown brake
   mechanism CLOSED-mechanism PARKED). Same as /028.
4. **No labeling change** — ATR multipliers unchanged (2.0, 1.0); timeout 21 candles
   unchanged.
5. **No universe change** — 3-symbol BCH+LDO+TRX universe unchanged from /028.
6. **No risk-gate threshold change** — adx_threshold 20.0, hurst regime, z-score OOD 2.0
   all unchanged.
7. **Optuna search reproducibility** — `--clean-oof` guardrail prevents OOF parquet
   contamination (iter-v3/047 hazard fixed at SHA `6a216b5`). UNCHANGED.

**Risk: walk-forward fix introduces subtle artifacts**. Mitigation: 42/42 regression
tests pass at v3 head; the fix purges training candles whose labels would peek into the
test month — the test ASSERTION is that labels are invariant to master DataFrame data
extent. Validated.

**Risk: outcome is dramatic deflation (PATH RE-ANCHOR-COLLAPSE)**. Mitigation: this
outcome is expected at 8-15% probability per Section 4.3. If fired, it triggers a
strategic re-evaluation (NOT an immediate cycle 1 launch); the orchestrator + Critic
adjudicate at Phase 8 (diary).

---

## Section 6 — Wall-Clock Discipline

CONFIRMATION-spec cap: 6h hard (per `feedback_v3_cadence_discipline.md` — empirically
updated from 4h after iter-v3/018 ran 4.54h).

Predicted wall-clock from /028 reproducibility stamp:
- /028 BASELINE_V3.md reported wall-clock: **3.18h** (Pareto, 1050 total trials)
- /058 has IDENTICAL spec (`--seeds 2 --n-trials 35 --clean-oof`, ENSEMBLE_SIZE=5)
- Walk-forward fix loses ~1-2% training data per month → minor speed-up at training
- Predicted runtime: **3.0 to 3.5h** (well within 6h CONFIRMATION cap)

If /058 exceeds 6h, the run TIMES OUT and the orchestrator dispatches QE for re-run
analysis. Hard kill at 6h.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

Per `feedback_no_cheating.md` + `feedback_axis_saturation_predictor.md`, the failure
modes for this RE-ANCHOR are pre-registered (NOT post-hoc renegotiable):

**Most plausible failure mode** (10-25% combined probability):
PATH RE-ANCHOR-MAJOR-DEFLATE or PATH RE-ANCHOR-COLLAPSE — multi-seed mean OOS Sharpe
goes substantially negative (or < +0.05) under unbiased walk-forward. This would force
revisit of v3 strategy validity entirely. If this fires:
- BASELINE_V3.md still updates per RE-ANCHOR mandate (this is an INTEGRITY correction,
  not a competitive update — the new baseline is the truth of the bundle under unbiased WF).
- Cycle 1 mandate likely shifts to MASS feature expansion immediately (the /028 stack is
  no longer a viable anchor; the orchestrator + Critic adjudicate the next cycle 1 axis).
- Memory rule `feedback_v3_mass_feature_expansion.md` may be REVISED from "queued for /062"
  to "immediate for /059".

**Second most plausible failure mode** (50-60% probability):
PATH RE-ANCHOR-NORMAL — deltas are minor (1-3% Sharpe deflation) and /028 bundle remains
a viable anchor. The lookahead bug was a methodology-correctness issue but not a
practical strategy invalidation. Cycle 1 proceeds with the /028 stack on the new
unbiased baseline numbers.

**Third (low probability) failure mode** (5-10%):
PATH RE-ANCHOR-INVARIANT — no measurable change. Forces diagnostic dive into WHY the
fix had no effect. Possible explanations: (1) training candles 22-bars-from-month-boundary
have low signal contribution; (2) Optuna search space at n_trials=35 saturates information
content from the embargoed candles; (3) the lookahead bias was uniform across all training
months → corrected uniformly with no net Sharpe shift (would require investigation).

**Pre-registered acceptance**: BOTH outcomes (deflation OR invariance) are valid baseline
updates per `feedback_v3_strict_both_is_oos_baseline.md` carve-out for RE-ANCHOR. This
is NOT a "competing" CONFIRMATION; it's an INTEGRITY correction of an existing baseline.
The new baseline numbers REPLACE the /028 numbers as the cycle 1 anchor regardless of
direction.

---

## Section 8 — Re-Anchor MERGE Criteria

**This iteration ALWAYS updates BASELINE_V3.md.** The only question is whether the new
baseline is viable as the foundation for cycle 1+ EXPLORATIONs.

### Section 8.1 — Mandatory BASELINE_V3.md update

Per orchestrator directive 2026-05-12 (path a) + memory rule
`feedback_v3_walkforward_lookahead_bug.md` action item #4:

> Re-run BASELINE_V3.md establishing iteration (iter-v3/028) with fix to obtain UNBIASED
> baseline anchor.

iter-v3/058 IS the re-run. The diary at Phase 8 MUST update BASELINE_V3.md regardless of
metrics direction. The new baseline anchor REPLACES the /028 multi-seed values.

**Diary outcomes**:
- All metrics within prediction bands AND Gate 10 (both seeds OOS > 0) PASS →
  "RE-ANCHOR-MERGE (clean)"; cycle 1 proceeds normally on /058 anchor.
- Major deflate but Gate 10 (both seeds OOS > 0) still PASS → "RE-ANCHOR-MERGE
  (deflated)"; cycle 1 axis priorities re-evaluate; mass feature expansion likely advances.
- Gate 10 FAIL (any seed OOS Sharpe ≤ 0) → "RE-ANCHOR-MERGE (critical-concern)"; cycle 1
  axis priorities REVISE substantially; mass feature expansion may be immediate.
- Pathological outcomes (e.g., neither seed positive; Sharpe < -1.0) → "RE-ANCHOR-MERGE
  (collapse)"; the user + orchestrator adjudicate next steps before cycle 1 launches.

### Section 8.2 — Gates retained (informational only)

These gates were inherited from /028 BASELINE_V3.md but are NOT blocking for this RE-ANCHOR:

| Gate | Threshold | Status at /058 |
|---|---|---|
| IS monthly Sharpe ≥ +1.0 | ≥ 1.0 | Expected to FAIL (anchor was +0.51; deflated value likely +0.35-0.50). Aspirational, informs cycle 1+ priorities. |
| OOS monthly Sharpe ≥ +1.0 | ≥ 1.0 | Same. |
| OOS/IS Sharpe ratio ≥ 0.5 | ≥ 0.5 | Expected to PASS (was 0.99 at /028 anchor). |
| DSR > 0.95 | > 0.95 | Expected to FAIL (structural at v3's trade volume; same as /028 anchor). |
| PBO mean < 0.4 | < 0.4 | Expected to PASS (was 0.1243 at /028 anchor). |
| **PSR > 0.95** | **> 0.95** | **If FAILS — informational only, structural (NOT a blocking concern for RE-ANCHOR)**. |
| Top-symbol concentration ≤ 30% | ≤ 30% | Expected to FAIL (was 75-77% TRX at /028 anchor). |
| Bundle OOS trades ≥ 130 | ≥ 130 | Expected to FAIL (was 91-96 at /028 anchor). |
| **Pareto Gate 10: both seeds OOS Sharpe > 0** | **> 0** | **If FAILS — CRITICAL CONCERN. Forces strategic re-evaluation. Strategy validity questioned.** |

**Critical gate**: Pareto Gate 10 (both seeds OOS Sharpe > 0). If a seed goes negative
under unbiased walk-forward when it was positive under biased, that's the strongest signal
that the bundle was overfit to lookahead. The diary flags this explicitly and the
orchestrator + Critic decide whether cycle 1 launches on the /058 anchor or pivots to
immediate mass feature expansion.

### Section 8.3 — Path adjudication LOCKED

```
PRIMARY OUTCOME: BASELINE_V3.md update (MANDATORY, regardless of metrics).

SECONDARY OUTCOME tier (in priority order):
  1. RE-ANCHOR-MERGE (clean):       Both seeds OOS > 0 AND multi-seed mean OOS in
                                    [+0.30, +0.50]. /058 anchor is viable; cycle 1 normal.
  2. RE-ANCHOR-MERGE (deflated):    Both seeds OOS > 0 AND multi-seed mean OOS in
                                    [+0.05, +0.30]. /058 anchor weaker than expected;
                                    cycle 1 axis priorities adjusted.
  3. RE-ANCHOR-MERGE (critical-concern): Any seed OOS ≤ 0 OR multi-seed mean OOS < +0.05.
                                    Strategic re-evaluation; mass feature expansion
                                    likely advances from /062 to /059 (immediate).
  4. RE-ANCHOR-MERGE (collapse):    Multi-seed mean OOS < 0 OR both seeds negative.
                                    User adjudication required before cycle 1 launch.
  5. RE-ANCHOR-INVARIANT:           Both metrics within ±5% of /028 biased anchor.
                                    Diagnostic dive into WHY fix had no effect; may
                                    require additional regression tests before cycle 1.
```

The Critic CANNOT post-hoc renegotiate the outcome classification. Path adjudication
happens at Phase 7 (evaluation) based on the observed metrics.

---

## Section 9 — Library Stack Pinning

UNCHANGED from /028 + /056 + /057:
- Python 3.13
- lightgbm 4.6.0
- optuna 4.8.0
- numpy 2.2.6
- pandas 3.0.0
- scikit-learn 1.8.0
- scipy 1.17.0
- statsmodels 0.14.6
- pyarrow 23.0.1

No new dependencies. The post-fix walk-forward uses only existing stdlib operations
(integer arithmetic on epoch-ms timestamps + the new `compute_embargo_candles` helper).

---

## Section 10 — QR Audit Trail

Per `feedback_v3_axis_selection_quant_discipline.md`, when axis selection is QR-driven,
brief Section 10 must document the research path. For RE-ANCHOR, the audit trail
documents the orchestrator-mandated path (no EDA-driven axis choice):

### Stage 1 — Read mandate

User directive 2026-05-12 (path a) per `feedback_v3_walkforward_lookahead_bug.md` action
item #3:
> ALL v3 iterations PRE-`e149e9d` are INVALIDATED. BASELINE_V3.md anchor (iter-v3/028) and
> all subsequent cycle results (/029-/057 setup) are produced from BUGGY walk-forward and
> cannot be trusted as ground truth. Pending: Re-run BASELINE_V3.md establishing iteration
> (iter-v3/028) with fix to obtain UNBIASED baseline anchor.

iter-v3/058 IS the re-run.

### Stage 2 — Bundle composition source

The /058 bundle composition is DIRECTLY SOURCED from `BASELINE_V3.md` (last updated
2026-05-08, commit ef18e1d). NO axis variation, NO new feature selection, NO new risk
primitive design. The brief is METHODOLOGY-DRIVEN, not signal-discovery-driven.

### Stage 3 — Citation chain

- `BASELINE_V3.md` §Code Configuration — full /028 bundle spec
- `feedback_v3_walkforward_lookahead_bug.md` — establishes the INVALIDATION rule + user
  decision path (a)
- v3 commit `e149e9d` — walk-forward fix (42/42 regression tests pass)
- v3 commit `414368a` — Critic enhancement (Foundation Audit + Anti-Pattern Catalog at
  §11 Appendix; /058 is FIRST iteration audited)
- main commit `5566a69` — original walk-forward fix in v1/v2; cherry-picked to v3 at `e149e9d`

### Stage 4 — No EDA-driven axis selection required

Per orchestrator directive: "NO new EDA required. Cite BASELINE_V3.md /028 bundle spec +
lookahead fix memory rule." The brief is condensed (~400-500 lines) and methodology-focused.

### Stage 5 — Cycle 4 cadence RESET

Per memory rule `feedback_v3_walkforward_lookahead_bug.md` action item #5:
> Cycle 4 cadence RESET to ZERO. All /051-/056 invalidated. Next iteration after baseline
> re-anchor restarts cycle counting.

After /058 completes:
- iter-v3/059 = CYCLE 1 #1 of 10 EXPLORATIONs (fresh cycle starts post-fix)
- iter-v3/068 = CYCLE 1 CONFIRMATION (or earlier per cadence discipline)
- Mass feature expansion mandate (per `feedback_v3_mass_feature_expansion.md`) currently
  queued for iter-v3/062 — REVIEW this queue when /058 lands. If /058 fires PATH
  RE-ANCHOR-COLLAPSE or RE-ANCHOR-CRITICAL-CONCERN, the mass feature expansion may need
  to advance to /059.

### Stage 6 — Critic protocol awareness

Per v3 commit `414368a`, the Critic agent was enhanced with:
- Foundation Audit (Boot Steps 9-11) — mandatory before every review
- Check 13 Anti-Pattern Static Scan — checks for hardcoded lookahead patterns, biased
  CV splits, etc.
- §11 Anti-Pattern Catalog — 13 entries including catalog entry A1 (walk-forward
  lookahead bias at train/test boundary)

/058 will be the FIRST iteration audited under the enhanced protocol. The Critic should
verify:
- Foundation Audit confirms walk-forward fix is properly applied (Check 13)
- BASELINE_V3.md /028 bundle composition is correctly restored at /058
- Test file modifications are correct (ret_skew_50 PRESENT assertion; parkinson_gk_ratio_20
  test skipped not deleted)

### Stage 7 — Setup commit SHA backfill

Phase 5.5 gate at QE setup commit will backfill the setup commit SHA into Section 10.5
(BACKFILL slot) after Engineer dispatches the setup commit.

```
Setup commit SHA: 7a46e05
Phase 5.5 gate SHA: 2917cfc
Brief SHA: 3ab47a8
```

---

## Section 11 — Catalog Row Pre-Commit

Per `feedback_no_cheating.md` + `feedback_axis_saturation_predictor.md`, the catalog row
outcome is PRE-COMMITTED upfront (cannot be renegotiated post-hoc):

**RE-ANCHOR outcome**: This iteration ALWAYS updates BASELINE_V3.md (per RE-ANCHOR mandate).
The only question is whether the new baseline is viable as the foundation for cycle 1+
EXPLORATIONs.

**Pre-committed catalog row template** (will be inserted at
`briefs-v3/exploration_catalog.md` after Phase 8 diary lands):

```
| RE-ANCHOR | /058 | RE-ANCHOR under post-fix walk-forward | <multi-seed IS> | <multi-seed OOS> | <Pareto Gate 10 pass/fail> | RE-ANCHOR-MERGE (clean/deflated/critical/collapse/invariant) | BASELINE_V3.md replaced |
```

The catalog row is INFORMATIONAL — RE-ANCHOR iterations are NOT counted toward cycle 1
cadence (cycle 1 starts at /059).

---

## Section 12 — What This Iteration Means For The Cycle

### If RE-ANCHOR-NORMAL fires (50-60% probability)

The /028 bundle survives integrity correction with mild deflation. BASELINE_V3.md is
updated to the new multi-seed values (IS ~+0.40, OOS ~+0.40). Cycle 1 EXPLORATIONs
(iter-v3/059-068) proceed normally with the post-fix walk-forward as the new substrate.
The mass feature expansion mandate at /062 (per `feedback_v3_mass_feature_expansion.md`)
remains queued and intact. PROMISING bands shift downward to anchor on the new baseline:
- PROMISING (single-seed): IS Δ ≥ +0.10 vs /058 anchor; OOS Δ ≥ +0.10
- NEGATIVE: IS Δ < -0.10 OR OOS Δ < -0.10

### If RE-ANCHOR-MAJOR-DEFLATE or RE-ANCHOR-COLLAPSE fires (combined 25-40% probability)

The /028 bundle was substantially lookahead-driven. BASELINE_V3.md is updated to the
deflated values. Cycle 1 axis priorities re-evaluate:
- If multi-seed mean OOS < +0.30 OR Gate 10 fails on either seed → mass feature expansion
  likely advances from /062 to /059 (immediate). The single-feature SWAP approach is
  insufficient when the base stack itself has been over-credited.
- If both seeds remain positive but deflated → cycle 1 normal but with priority on
  STRUCTURAL axes (universe expansion, model arch, new feature families) over knob axes.

### If RE-ANCHOR-INVARIANT fires (5-10% probability)

No measurable change. Possible explanations require investigation:
1. The training candles 22-bars-from-month-boundary have low signal contribution
2. Optuna search space at n_trials=35 saturates information from embargoed candles
3. The lookahead bias was uniform across all training months → corrected uniformly with
   no net Sharpe shift

The orchestrator + Critic decide whether additional regression tests are needed before
cycle 1 launches. The /058 multi-seed values still become the new BASELINE_V3.md anchor.

### Cycle counting after /058

```
RE-ANCHOR iterations are NOT part of cycle 1 cadence count.
After /058:
  iter-v3/059 = CYCLE 1 EXPLORATION #1 of 10
  iter-v3/060 = CYCLE 1 EXPLORATION #2 of 10
  ...
  iter-v3/068 = CYCLE 1 CONFIRMATION (or earlier per cadence discipline)
```

Per `feedback_v3_strict_10_to_1_cadence.md`, the 10th EXPLORATION must be SEPARATE from
the CONFIRMATION (cannot be collapsed). Cycle 1 CONFIRMATION will multi-seed validate
either:
- The /058 anchor bundle PLUS new edge ingredients discovered in /059-068, OR
- A completely different bundle if mass feature expansion advances to /059

---

**END OF BRIEF — Phase 5 complete.**

**SHA**: this commit (populated at git commit time).
**Next**: Orchestrator dispatches QE for Phase 5.5 setup commit + Phase 5.5 gate +
detached-bash backtest launch (CONFIRMATION-spec; 6h cap).
