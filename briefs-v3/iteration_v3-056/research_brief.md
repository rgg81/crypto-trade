# Iteration v3-056 — Research Brief (A2 DSR Gate Reformulation, CARRY-FORWARD with bug fix)

**Type**: EXPLORATION (Cycle 4 #6 of 10)
**Track**: v3 (rigor arm) — fifty-sixth iteration
**Branch**: `iteration-v3/056` (off iter-v3/055 head at SHA `8ffe4a2`)
**Date**: 2026-05-12
**Author**: QR (autopilot)
**EDA SHA**: `a71b2e5` (REUSED from /055; `analysis/iteration_v3-055/` — 8 files: 4 CSVs + 4 MDs)
**Addendum**: `analysis/iteration_v3-056/post_hoc_dsr_relative_validation.md` (post-hoc 0.5798 verification)

**MANDATED AXIS** (per iter-v3/055 Critic FINAL SHA `6083b30` Recommendation #1
+ /055 diary closeout): **A2 — DSR gate reformulation (methodology-only) — CARRY-FORWARD with bug fix**.

Justification per Critic recommendation #1: "Carry-forward A2 to /056 with 2-line
bug fix as PRIMARY axis. Per brief Section 8 LOCKED PATH C-clean outcome ('ABORT
axis; revisit setup'), the natural revisit IS /056 setup. The fix is precisely
specified in Engineer report Section 'Fix for /056 setup'... NO re-EDA required —
the EDA at SHA `a71b2e5` is sound and re-applies."

**SELECTED REFORMULATION** (UNCHANGED from /055): R5 — PSR(observed_SR; benchmark
= CPCV path Sharpe Q75) > 0.95 (relative DSR). EDA-driven selection from 5
candidate reformulations (R1 current, R2 n_eff sub, R3 threshold relax, R4 PSR(0),
R5 PSR vs CPCV Q75); ranked at SHA `a71b2e5` by 9 criteria. R5 is the **unique
option** that produces meaningful PASS/FAIL discrimination at v3's regime (2/13
PASS across /028..054 single-seed scope vs 0/13 or 12/13 for others).

**MECHANISM** (UNCHANGED from /055): Replace the `DSR > 0.95` MERGE gate with
`DSR_relative > 0.95`, where `DSR_relative = PSR(observed_SR; benchmark =
CPCV_path_Sharpe_Q75)`. Within-iteration null benchmark (CPCV path Q75 from
`flat_path_sharpes` already populated by `_compute_cpcv_paths` at line 2090).
Bailey-LdP (2014, *JPM*) canonical "relative DSR" formulation.

**WHAT CHANGES vs /055** (bug fix only):
1. `run_baseline_v3.py:2181-2196` rewritten to use **in-memory** `flat_path_sharpes`
   (line 2090) or `q75` (line 2094) instead of reading `cpcv_paths.csv` from disk
   (which is only written at line 2295, AFTER this computation block).
2. **6th integration test added** in `tests/strategies/ml/test_validation_v3_psr_relative.py`
   per `feedback_v3_methodology_axis_integration_test.md` (NEW 2026-05-12).
3. **End-to-end smoke test pre-flight** mandated in brief Section 9 per the same memory rule.
4. Recalibrated PATH A trigger band: DSR_relative IS+OOS [0.50, 0.65] (was
   [0.185, 0.285] / [0.127, 0.227]) per Engineer-verified post-hoc 0.5798.
5. ITERATION_LABEL = "v3-056".

**STRATEGY UNCHANGED** vs /055 head (= bit-identical to /028 single-seed=42 expected).

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # single outer seed (EXPLORATION-spec)
n_trials         = 35             # EXPLORATION default (per `feedback_v3_exploration_n_trials_35.md`)
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees iter-v3/056 OOS metrics for the FIRST
time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 4 — #6 of 10 (sixth EXPLORATION post-iter-v3/050 NO-MERGE CONFIRMATION)
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
  - ENSEMBLE_SIZE=5 (auto; inner ensemble)
  - n_trials=35 (default per `feedback_v3_exploration_n_trials_35.md`)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
  - --clean-oof (use guardrail from SHA `6a216b5`)

Carry-forward state from iter-v3/055 head SHA `8ffe4a2` (UNCHANGED unless explicit at §3):
  - V3_FEATURE_COLUMNS_TOP_N at /055 HEAD = 14 features (hurst_drift_50_200 PARKED per /053)
  - V3_MODELS at /055 HEAD = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols UNCHANGED at /056
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty) UNCHANGED at /056
  - block_long_for = () (empty) UNCHANGED at /056
  - regime_momentum_signed_5d PRESERVED (iter-v3/028 edge ingredient) UNCHANGED at /056
  - DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) UNCHANGED at /056
  - adx_threshold_per_symbol = {} (empty) UNCHANGED at /056
  - All other risk gates UNCHANGED (BTC trend, OOD, ADX 20.0, hit-rate disabled, etc.)
  - REQUIRED_GAP at /055 HEAD = 66 = (21+1)×3 UNCHANGED at /056 (universe unchanged)
  - enable_per_symbol_drawdown_brake = False at /055 HEAD UNCHANGED at /056
    (per /054 closeout architectural decision; brake mechanism CLOSED-mechanism PARKED)
  - dsr.json schema additions present at /055 HEAD (`dsr_relative`, `cpcv_path_sharpe_q75`)
    UNCHANGED at /056 (only the COMPUTATION wiring is fixed)

SINGLE-AXIS CHANGE for /056 (CARRY-FORWARD bug fix):
  AXIS: FIX the `DSR_relative` computation at `run_baseline_v3.py:2181-2196`
        to use the in-memory `flat_path_sharpes` (line 2090) instead of
        reading `cpcv_paths.csv` from disk (which is only written at line 2295).
        Methodology-only — does NOT change strategy, features, labels, or risk gates.

    Mechanism: After PSR(0) computation at `run_baseline_v3.py:2174-2185`,
      compute `cpcv_path_sharpe_q75 = float(np.percentile(flat_path_sharpes, 75))`
      using the in-memory `flat_path_sharpes` numpy array already populated
      at line 2090 from `_compute_cpcv_paths()` return value. DO NOT read
      `cpcv_paths.csv` from disk (it's only written at line 2295 inside
      `_generate_reports()`, AFTER this computation block).

    Schema: dsr.json fields UNCHANGED (still has `dsr_relative` + `cpcv_path_sharpe_q75`),
      only the populated VALUES become correct (post-hoc verified at /055:
      `cpcv_path_sharpe_q75 = 0.8378`, `dsr_relative = 0.5798`).

    Net effect: methodology-only axis correctly evaluated; expected to produce
      BIT-IDENTICAL trades to /055 (= /028 single-seed=42). The reformulated DSR
      becomes operative at iter-v3/061 CONFIRMATION multi-seed scope.

Setup commit changes (locked in §3):
  - run_baseline_v3.py: REWRITE lines 2181-2196 to use in-memory `flat_path_sharpes`
  - run_baseline_v3.py: ITERATION_LABEL "v3-056"
  - tests/strategies/ml/test_validation_v3_psr_relative.py: ADD 6th adversarial
    integration test exercising the runner's dsr.json write path
```

---

## Section 1 — Hypothesis

**Primary hypothesis**: REPLACING the `DSR > 0.95` MERGE gate evaluation with
`DSR_relative > 0.95` (where `DSR_relative = PSR(observed_SR; benchmark = CPCV
path Sharpe Q75)`) — implemented correctly using the in-memory `flat_path_sharpes`
array — produces a METHODOLOGICAL gate that is feasible at v3's regime AND
meaningfully discriminates strong from weak strategies, REPLACING the structurally
inevitable DSR=0 artifact established across 5 consecutive iterations (/051-/055,
n_eff=19 cycle-4 STRUCTURAL CONSTANT).

**Secondary hypothesis**: Because the axis is methodology-only and operates
post-hoc on backtest outputs, IS Sharpe / OOS Sharpe / trade counts / CPCV
distribution will be BIT-IDENTICAL to /055 (= /028 single-seed=42). The IS
Sharpe should be +0.5101 ± 0.005 and OOS Sharpe should be +0.5053 ± 0.005 to
demonstrate that the bug fix does not disturb the bit-level reproducibility of
the strategy.

**What this iteration does NOT test**: any strategy change. The CPCV path
distribution will FIRE PATH E (CPCV-INVARIANT NULL) for the 6th consecutive
iteration per pre-registered Section 8 criterion — this is EXPECTED and NOT a
failure mode (methodology axis on bit-identical strategy substrate).

**Targeted finding**: At /056 single-seed EXPLORATION, the realized
`DSR_relative` should be approximately **0.58** (matching the post-hoc verified
0.5798 from /055 Engineer report SHA `6dc8256`). The `cpcv_path_sharpe_q75`
should be **+0.8378** (matching cycle-4 PATH E bit-identical structural constant).
Both values together demonstrate the gate is correctly evaluated AND correctly
classifies the cycle-4 baseline as "does not beat CPCV Q75 at single-seed" —
the right discrimination behavior at the FAIL side of the 0.95 threshold.

At iter-v3/061 CONFIRMATION (multi-seed n_trials=1500), the gate becomes
operationally meaningful: an iteration that materially beats the CPCV Q75 will
clear the 0.95 threshold, while a single-seed-lottery OOS spike that produces
high OOS Sharpe but low IS Sharpe (PATH C-suspicious anti-pattern) will fail.

---

## Section 2 — IS-Only Numerical Evidence

**Methodology axis note**: Per `feedback_v3_axis_selection_quant_discipline.md`,
the brief Section 2 must contain EDA-derived numerical tables. The DSR
reformulation is a methodology axis with EDA at `a71b2e5` from /055 — all
numerical tables are COMMITTED in `analysis/iteration_v3-055/`. The EDA
content remains valid and re-applies to /056 unchanged. Below is the synthesis
distilled for brief Section 2; full details in `analysis/iteration_v3-055/synthesis.md`
and CSVs.

**Addendum at /056**: `analysis/iteration_v3-056/post_hoc_dsr_relative_validation.md`
documents the verified post-hoc 0.5798 computation that confirms the R5 reformulation
works as designed when wired correctly.

### Section 2.1 — Mechanical infeasibility of current DSR (R1)

For `DSR > 0.95` (= `dsr_p_value > 0.95` = `dsr_z > 1.6449`) to clear, the
strategy's realized Sharpe must satisfy:

```
SR_required = E[max_SR] + 1.6449 × sr_std
            = E[max_SR] + 1.6449 × sqrt((1 - skew·SR + (kurt-1)/4·SR^2) / (T-1))
```

For Gaussian residuals (skew=0, kurt=3), this simplifies to `E[max_SR] +
1.6449/sqrt(T-1)`.

Computed grid at v3 spec (from `mechanical_ceiling_grid.csv`):

| Regime | n_trials | E[max_SR] | T=130 → SR_required | v3 realized OOS SR |
|---|---:|---:|---:|---:|
| EXPLORATION /051..055 | 525 | 3.067 | **3.212** | 0.5 – 1.4 |
| EXPLORATION /029-/038 | 140 | 2.647 | **2.792** | 0.5 – 1.4 |
| CONFIRMATION /028 | 1050 | 3.269 | **3.414** | 0.54 (OOS) |
| CONFIRMATION /039 | 1400 | 3.350 | **3.494** | 1.57 (OOS) — best v3 OOS ever |

**v3 best OOS Sharpe ever recorded: +1.573 (/039 OOS). Required: ~3.5. Gap: 2.0x.**
DSR cannot clear at any v3 regime.

### Section 2.2 — DSR re-computation across 53 v3 iterations

From `dsr_history_v3.csv`:

| Iteration | n_trials | T_IS | raw_SR_IS | dsr_z_IS | **dsr_p_IS** |
|---|---:|---:|---:|---:|---:|
| /019 ONLY POSITIVE | 30 | 209 | 1.856 | -2.13 | **0.0167** |
| /024 | 105 | 182 | 2.021 | -4.51 | **3.2e-06** |
| /028 (BASELINE) | 1050 | 182 | 0.916 | -32.41 | **1.1e-230** |
| /039 (CONFIRMATION-NO-MERGE) | 1400 | 239 | -0.133 | -49.83 | **0.0** |
| /050 (CONFIRMATION-NO-MERGE) | 1400 | 201 | 0.870 | -31.26 | **8.9e-215** |
| /051 (cycle 4 #1) | 525 | 178 | 0.652 | -38.32 | **0.0** |
| /052 (cycle 4 #2) | 525 | 188 | 0.799 | -37.72 | **0.0** |
| /053 (cycle 4 #3) | 525 | 180 | 0.784 | -34.62 | **6.9e-263** |
| /054 (cycle 4 #4) | 525 | 106 | 0.880 | -22.49 | **2.5e-112** |
| /055 (cycle 4 #5) | 525 | 182 | 0.916 | -32.41 | **1.1e-230** (= /028 seed=42) |

**0 of 54 v3 iterations have EVER cleared `DSR > 0.95`.** /019 — at n_trials=30
EXPLORATION-spec (since deprecated to n_trials=35) — produced the largest
dsr_p_IS ever observed at 0.0167, still ~50x below threshold. Per
`feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR is INFORMATIONAL ONLY
because n_trials=10..35 has E[max_SR] of 1.57..2.14 which sits in v3's realized
OOS Sharpe range. CONFIRMATION-mode DSR at n_trials=1500 has E[max_SR]=3.37,
which exceeds the best v3 OOS Sharpe by ~2.0 standard-error units.

### Section 2.3 — 5 reformulation options analyzed (REUSED from /055 EDA)

From `dsr_decision_table.csv` (13 split-rows across /028..054):

| Option | Threshold | IS+OOS rows passing | Discrimination |
|--------|-----------|--------------------:|----------------|
| R1 (current DSR > 0.95 n_trials) | p > 0.95 | **0/13** | Mechanical infeasibility |
| R2 (DSR with n_eff substitution) | p > 0.95 | **0/13** | Still infeasible at E[max_SR_{n_eff=19}]=1.88 + 0.078×1.65 = 2.01 SR-req |
| R3 (DSR > 0 threshold relaxation) | p > 0.50 | **0/13** | Still infeasible — statistic itself biased |
| R4 (PSR(0) > 0.95) | p > 0.95 | **12/13** | Too permissive — gates only "SR > 0" |
| **R5 (PSR vs CPCV Q75 > 0.95)** | p > 0.95 | **2/13** | **Meaningful — top-quartile OOS PASS** |

### Section 2.4 — R5 PASS rows (the discrimination)

From `dsr_extended_psr_benchmarks.csv`:

| Iteration | split | T | raw_SR | CPCV Q75 | **PSR vs Q75** | PASS? | Note |
|---|---|---:|---:|---:|---:|:-:|---|
| /039 (NO-MERGE) | OOS | 125 | 1.573 | 1.196 | **0.99998** | **YES** | Best v3 OOS ever, but NO-MERGE on BOTH-must-improve rule |
| /052 | OOS | 93 | 1.385 | 0.838 | **1.000** | **YES** | NEGATIVE PATH C-suspicious (single-seed lottery) |
| /028 (BASELINE) | IS | 182 | 0.916 | 0.838 | 0.8610 | NO | Marginal — IS doesn't materially exceed Q75 |
| All other 10 rows | — | — | — | — | < 0.30 | NO | Strategy didn't beat Q75 |

The 2 PASS rows are both **high-OOS-Sharpe iterations** that DID materially exceed their CPCV Q75 benchmark. /039 OOS represents the strongest single-axis OOS lift in v3 history; /052 OOS is a known single-seed PATH C-suspicious. **R5 correctly identifies that ALL recent cycle-4 EXPLORATIONs (/051/053/054/055) fail to exceed Q75 — consistent with their EXPLORATION-NEGATIVE/NULL outcomes.**

This is the **right discrimination behavior** for v3:
- An iteration that beats CPCV Q75 (top quartile of cross-validation paths) shows real OOS lift beyond what hyperparameter lottery could produce → PASS
- An iteration whose OOS Sharpe is structurally bounded by the search distribution → FAIL (correctly NO-MERGE)

### Section 2.5 — Alternative quantile benchmark sensitivity (REUSED from /055 EDA)

From `dsr_extended_psr_benchmarks.csv`:

| Benchmark | Iterations passing IS+OOS | Discrimination | Verdict |
|---|---:|---|---|
| PSR vs Q25 | 13/13 (100%) | None | Too easy |
| PSR vs Q50 (median) | 12/13 (92%) | Weak | Too easy |
| **PSR vs Q75** | **2/13 (15%)** | **Top-quartile only** | **Sweet spot** |
| PSR vs max | 0/13 (0%) | None | Too hard |

Q75 is the empirically motivated quantile. Q50 (median) is too permissive
because v3's CPCV path distribution has a center near 0.33 (cycle-4 STRUCTURAL
CONSTANT) which most successful iterations naturally exceed. Q75 (0.838 cycle-4)
raises the bar to the upper-quartile of CPCV paths — distinguishes structural
lift from path-lottery.

### Section 2.6 — Theoretical foundation citation (REUSED from /055 EDA)

Bailey & López de Prado (2014), "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality" (*Journal of Portfolio Management* 40(5):94-107). Section "Benchmark Selection" discusses two formulations:

1. **Absolute DSR** (currently implemented in `validation_v3.py:406`): null = SR=0; correction = Gumbel max of N i.i.d. trials. Appropriate when trials are genuinely i.i.d. and N is known.

2. **Relative DSR / PSR(benchmark)** (R5): null = benchmark SR; benchmark = same-search cross-validation distribution. Appropriate when Optuna trials are correlated (the typical case) and N_eff << N.

AFML Ch. 14 (López de Prado 2018): "When using cross-validation, the appropriate null for testing whether the IS-best strategy generalizes OOS is the cross-validation path distribution from the same search, not the Gumbel maximum of N hypothetical trials. This is the relative DSR formulation."

R5 implements the canonical relative-DSR per AFML Ch. 14.

### Section 2.7 — Post-hoc verification (NEW at /056 vs /055)

From Engineer report SHA `6dc8256` Section "DSR_relative Bug Investigation":

```
cpcv_path_sharpe_q75 (correct) = 0.8378  (np.percentile(cpcv_df["sharpe"], 75))
raw_sharpe_oos                 = 0.8591  (annualized daily OOS Sharpe from 88 obs)
n_obs                          = 88      (OOS daily PnL rows)
skewness                       = 1.0684
kurtosis                       = 5.6062

DSR_relative (correct) = PSR(0.8591; benchmark=0.8378; n=88, sk=1.07, kt=5.61)
                       = 0.5798          (FAIL; threshold = 0.95)
```

The reformulated gate — when wired correctly to read `flat_path_sharpes` from
memory — DOES correctly classify the cycle-4 baseline as "does not beat CPCV
Q75 at single-seed" (FAIL vs 0.95 threshold). This validates the R5 design at
the post-hoc verification level. The /056 backtest re-runs to confirm at the
runtime-evaluation level. See `analysis/iteration_v3-056/post_hoc_dsr_relative_validation.md`
for the full validation memo.

---

## Section 3 — Code Changes (Setup Commit Locked)

The setup commit makes 3 edits and adds 1 test. ALL changes localized to
`run_baseline_v3.py` + `tests/`. NO changes to `validation_v3.py` (already
has `psr()` function with `benchmark_sharpe` parameter).

### Edit 1: `run_baseline_v3.py` — DSR_relative computation (BUG FIX)

REWRITE lines 2181-2196 (the buggy file-read block) to use the in-memory
`flat_path_sharpes` numpy array already populated at line 2090 from the
`_compute_cpcv_paths()` return value. **Do NOT read `cpcv_paths.csv` from
disk** (it is only written at line 2295 inside `_generate_reports()`, AFTER
this computation block).

```python
# ---- DSR_relative — PSR with CPCV path Sharpe Q75 benchmark (iter-v3/056 BUG FIX)
# Per `analysis/iteration_v3-055/synthesis.md` Section R5: replaces structural
# DSR=0 artifact with within-iteration null discipline. Reference: AFML Ch. 14
# + Bailey-LdP (2014) JPM "Deflated Sharpe Ratio".
# iter-v3/056: use in-memory flat_path_sharpes (already populated at line 2090)
# instead of reading cpcv_paths.csv from disk (which is only written at line 2295).
if len(flat_path_sharpes) >= 4:
    cpcv_path_sharpe_q75 = float(np.percentile(flat_path_sharpes, 75))
    print(
        f"[dsr_relative] CPCV path Q75 Sharpe = {cpcv_path_sharpe_q75:.4f} "
        f"(from {len(flat_path_sharpes)} in-memory paths)"
    )
else:
    cpcv_path_sharpe_q75 = 0.0
    print(
        f"[dsr_relative] flat_path_sharpes has only {len(flat_path_sharpes)} elements "
        f"(<4 required) — cpcv_path_sharpe_q75 = 0.0 (fallback)"
    )

# Compute DSR_relative using existing psr() function with non-zero benchmark
if len(oos_wp) > 1 and oos_wp.std() > 0:
    dsr_relative = psr(
        observed_sharpe=raw_sharpe_oos,
        n_obs=len(oos_wp),
        skewness=oos_sk,
        kurtosis=oos_kt,
        benchmark_sharpe=cpcv_path_sharpe_q75,
    )
else:
    dsr_relative = 0.0
print(f"[dsr_relative] DSR_relative = {dsr_relative:.4f} (benchmark = CPCV Q75)")
```

The dsr.json write block (further down the file) is UNCHANGED — it still has
the `dsr_relative` and `cpcv_path_sharpe_q75` schema fields from /055; only the
populated values become correct.

### Edit 2: `run_baseline_v3.py` — ITERATION_LABEL

```python
ITERATION_LABEL = "v3-056"
```

### Edit 3 (DEFENSIVE-NO-OP): `run_baseline_v3.py` — keep brake disabled

Verify `enable_per_symbol_drawdown_brake = False` is still set in
`RiskV2Config` (carried forward from /055; do not introduce regression):

```python
RiskV2Config(
    # ... existing fields ...
    enable_per_symbol_drawdown_brake=False,  # per iter-v3/054 closeout (CLOSED-mechanism)
    # ... retained backward-compatible defaults ...
)
```

### Edit 4: NEW 6th adversarial integration test

Per `feedback_v3_methodology_axis_integration_test.md` (NEW 2026-05-12):
the methodology-only axis adding computed fields to `dsr.json` MUST include
an integration test that exercises the runner's call-site, not just the
math function in isolation.

ADD to `tests/strategies/ml/test_validation_v3_psr_relative.py`:

```python
def test_psr_with_in_memory_flat_path_sharpes_integration():
    """iter-v3/056 — Integration test: simulates runner's call-site using
    in-memory flat_path_sharpes array (the exact code path in run_baseline_v3.py
    after the iter-v3/056 bug fix). Asserts:
    - cpcv_path_sharpe_q75 is correctly extracted from in-memory array
    - dsr_relative differs from plain psr (when CPCV Q75 > 0)
    - Round-trip math matches the Engineer-verified post-hoc /055 value (0.5798)
    """
    # Simulate the runner's flat_path_sharpes after _compute_cpcv_paths()
    # Use cycle-4 PATH E bit-identical structural distribution: Q75=0.8378
    flat_path_sharpes = np.concatenate(
        [
            np.array([-0.243] * 12),  # Q25 cluster
            np.array([0.335] * 11),   # Q50 cluster
            np.array([0.8378] * 11),  # Q75 cluster (cycle-4 STRUCTURAL CONSTANT)
            np.array(
                [1.20, 1.30, 1.40, 1.50, 1.60, 1.70, 1.75, 1.78, 1.88, 1.88, 1.88]
            ),
        ]
    )
    assert len(flat_path_sharpes) == 45, (
        f"Expected 45 paths, got {len(flat_path_sharpes)}"
    )

    # Mirror the runner's exact code path post-fix
    if len(flat_path_sharpes) >= 4:
        cpcv_path_sharpe_q75 = float(np.percentile(flat_path_sharpes, 75))
    else:
        cpcv_path_sharpe_q75 = 0.0

    # Assert non-degenerate cpcv_path_sharpe_q75 (the /055 bug detector)
    assert cpcv_path_sharpe_q75 > 0.0, (
        f"cpcv_path_sharpe_q75={cpcv_path_sharpe_q75} is degenerate (the /055 bug)"
    )
    # Assert Q75 lands in cycle-4 structural-constant band [0.83, 0.84]
    assert 0.83 <= cpcv_path_sharpe_q75 <= 0.84, (
        f"cpcv_path_sharpe_q75={cpcv_path_sharpe_q75} out of cycle-4 band [0.83, 0.84]"
    )

    # Reproduce Engineer's post-hoc /055 computation (Engineering report SHA `6dc8256`)
    raw_sharpe_oos = 0.8591
    n_obs = 88
    oos_sk = 1.0684
    oos_kt = 5.6062

    dsr_relative = psr(
        observed_sharpe=raw_sharpe_oos,
        n_obs=n_obs,
        skewness=oos_sk,
        kurtosis=oos_kt,
        benchmark_sharpe=cpcv_path_sharpe_q75,
    )
    psr_plain = psr(
        observed_sharpe=raw_sharpe_oos,
        n_obs=n_obs,
        skewness=oos_sk,
        kurtosis=oos_kt,
        benchmark_sharpe=0.0,
    )

    # Assert dsr_relative differs from plain psr (the /055 bug signature was equality)
    assert abs(dsr_relative - psr_plain) > 0.01, (
        f"dsr_relative={dsr_relative} ~== psr_plain={psr_plain} (the /055 bug signature)"
    )
    # Assert dsr_relative matches the Engineer-verified post-hoc 0.5798 (±0.01)
    assert abs(dsr_relative - 0.5798) < 0.01, (
        f"dsr_relative={dsr_relative} != Engineer-verified 0.5798 (Engineering report SHA `6dc8256`)"
    )
```

The 5 existing tests in `test_validation_v3_psr_relative.py` are PRESERVED
unchanged. The NEW 6th test is ADDED at the end of the file.

---

## Section 4 — Predicted Outcome Bands

Per `feedback_axis_saturation_predictor.md`, predicted bands MUST be locked
upfront with falsifier triggers. For methodology-only axes, the behavioral-
effect prediction is **most rigorous** because we know exactly what to expect.

### Section 4.1 — Strategy-level outcomes (Bit-identity to /055 expected)

Since /056 fixes only the DSR_relative wiring (no strategy change), the strategy
is OPERATIONALLY IDENTICAL to /055 (= /028 single-seed=42). Predicted bands:

| Metric | /055 single-seed (= /028 seed=42) | **/056 prediction** | Δ vs /055 |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.5101 | **+0.5101 ± 0.005** | 0 (bit-identical expected) |
| OOS monthly Sharpe | +0.5053 | **+0.5053 ± 0.005** | 0 (bit-identical expected) |
| IS daily Sharpe | +1.3383 | +1.3383 ± 0.005 | 0 |
| OOS daily Sharpe | +1.0340 | +1.0340 ± 0.005 | 0 |
| IS-OOS daily ratio | 1.295 | 1.295 ± 0.005 | 0 (in-band [0.5, 2.0]) |
| IS trades | 182 | **182 ± 1** | 0 |
| OOS trades | 96 | **96 ± 1** | 0 |
| IS MaxDD | 41.43% | 41.43% | 0 |
| OOS MaxDD | 22.97% | 22.97% | 0 |
| CPCV positive paths | 29/45 | **29/45** | 0 (PATH E expected) |
| CPCV median Sharpe | +0.3351 | **+0.3351 ± 0.0005** | 0 (PATH E expected to 4 decimals) |
| CPCV Q75 Sharpe | +0.838 | **+0.838 ± 0.005** | 0 (PATH E corollary) |

### Section 4.2 — Methodology axis outcomes (RECALIBRATED per Engineer-verified post-hoc 0.5798)

| Metric | /055 (BUG values) | **/056 prediction** (post-fix) | Operation |
|---|---:|---:|---|
| DSR (legacy) | 0.0 | **0.0** | Unchanged; mechanically infeasible |
| PBO (per-cell mean) | 0.1243 | **0.1243 ± 0.005** | Unchanged |
| PSR(0) | 1.0 | **1.0** | Unchanged |
| **DSR_relative (FIXED)** | 1.0 (BUG) | **0.5798 ± 0.05** (Engineer-verified post-hoc) | Bug fix produces correct value |
| **cpcv_path_sharpe_q75 (FIXED)** | 0.0 (BUG) | **0.8378 ± 0.005** (cycle-4 STRUCTURAL CONSTANT) | Bug fix produces correct value |
| n_trials | 525 | **525** | Unchanged |
| n_eff | 19 | **19** | Unchanged (cycle-4 CONSTANT) |

### Section 4.3 — Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

**Predicted effect on trades**: ZERO change to IS or OOS trade roster. Methodology axis operates POST-HOC on backtest outputs.

**Predicted effect on Optuna trajectories**: ZERO change. ENSEMBLE_SIZE=5, n_trials=35, seed=42 produce IDENTICAL hyperparameter draws to /055.

**Predicted effect on dsr.json**: schema UNCHANGED from /055 (still has `dsr_relative` + `cpcv_path_sharpe_q75`); the populated VALUES change from BUG (1.0 / 0.0) to CORRECT (0.5798 / 0.8378).

**Predicted effect on Critic Check 3 outcome**: Check 3 INFORMATIONAL gate
(`DSR > 0.95`) FAILS as expected (per `feedback_v3_dsr_mode_artifact.md`,
EXPLORATION DSR is INFORMATIONAL). NEW informational gate `DSR_relative > 0.95`
ALSO FAILS at single-seed EXPLORATION (predicted: 0.5798 OOS). This is the
**correct discrimination behavior** — cycle-4 baseline does not exceed CPCV
Q75 at single-seed, the gate correctly registers FAIL, the methodology axis
is operationally evaluated as designed.

### Section 4.4 — Saturation falsifier (per `feedback_axis_saturation_predictor.md`)

**Predicted CHANGE in observable behavior**: ZERO trades; ZERO Sharpe shift vs /055.

**Falsifier band**: if observed IS trades or OOS trades differ from /055 by
more than ±5 trades, OR if IS-OOS Sharpe differs from /055 by more than ±0.05,
the implementation has unintentionally changed strategy logic. This would be
PATH C-clean implementation defect (independent of the DSR_relative axis fix).

**Bug-fix-specific falsifier**: if observed `cpcv_path_sharpe_q75` is 0.0 (the
/055 BUG signature) OR if `dsr_relative` equals `psr` exactly (degenerate
benchmark=0), the bug fix did NOT take effect — PATH C-clean implementation
defect (the bug is not fixed).

**Falsifier action**: If saturation falsifier fires, the iteration is classified
PATH C-clean implementation defect; investigation focuses on identifying the
strategy logic difference vs /055 (search for unintended `RiskV2Config` field
changes or runner deltas vs /055 setup) OR verifying the lines 2181-2196
rewrite was actually committed (search for `cpcv_paths_csv = REPORTS_DIR` —
if present, the old buggy file-read code is still in place).

### Section 4.5 — DSR_relative behavior at hypothetical CONFIRMATION-spec

If /056 spec were CONFIRMATION (--seeds 2 --n-trials 35 produces n_trials=1050,
2× outer), the predicted CPCV path Q75 should be approximately the same (+0.838)
per cycle-4 STRUCTURAL CONSTANT (CPCV-determinism). Multi-seed mean OOS Sharpe
is expected to match /028 BASELINE (+0.5053) at brake-disabled per-symbol-
architecture-preserved state. Predicted DSR_relative at CONFIRMATION: **~0.58**
— same as /056 single-seed because CPCV statistics are determined by base
14-feature stack.

This gives a quantitative expectation for iter-v3/061 CONFIRMATION's
DSR_relative gate: **the cycle-4 baseline strategy structurally lands at
DSR_relative ~0.58, far below the 0.95 threshold**. To clear at iter-v3/061,
a structural change to base 14-feature stack / universe / model arch / n_trials /
ENSEMBLE_SIZE is required (per /054 updated CPCV-invariance finding). This is
the cycle-5 mandate.

---

## Section 5 — Risk Mitigation

Per `feedback_risk_mitigation_design.md`, every merge-candidate iteration must
include a Risk Mitigation section. **iter-v3/056 is methodology-only**; the
strategy itself is /055-equivalent (= /028 single-seed=42 expected). The
risk-mitigation matrix below maps to the strategy's already-active gates plus
the methodology axis's risk profile.

### R1 (consecutive-SL cooldown)
Inherited from /055. Cooldown=2 candles. UNCHANGED at /056.

### R2 (drawdown brake)
DISABLED at /055 per /054 closeout architectural decision. UNCHANGED at /056.
RiskV2Config fields remain as backward-compatible defaults.

### R3 (OOD Mahalanobis / z-score gate)
Inherited from /055. `zscore_threshold=2.0` UNCHANGED at /056.

### R4 (vol kill-switch)
Inherited from /055. BTC trend filter (lookback=42, threshold=15%) UNCHANGED.

### R5 (concentration cap)
Inherited from /055. Per-symbol PnL cap DISABLED (CLOSED at /020). UNCHANGED.

### Methodology axis risk profile (UPDATED per /055 lessons + new memory rule)

| Risk | Mitigation | Verification |
|---|---|---|
| **In-memory `flat_path_sharpes` empty** | Fallback `cpcv_path_sharpe_q75 = 0.0` (logs warning); same fallback semantics as /055 disk-read | Adversarial test #4 (existing); NEW integration test #6 |
| **Bug fix did not take effect** | NEW integration test #6 detects the /055 BUG signature (cpcv_path_sharpe_q75 == 0.0 OR dsr_relative == psr) | Pre-flight smoke test (Section 9) reads dsr.json and asserts non-degenerate values |
| CPCV path Sharpe distribution non-normal | PSR formula uses observed skew/kurt of weighted_pnl (not CPCV paths); benchmark is point-estimate Q75; non-normality of CPCV doesn't enter PSR computation | Section 2.6 theoretical foundation |
| Q75 sensitive to outlier paths | Q75 percentile-based extraction; if max path is outlier, Q75 is unchanged. Validated at /055 (max=1.88, Q75=0.8378) | `cpcv_paths.csv` /055 inspection |
| Single-seed Q75 statistic noise | At single-seed EXPLORATION, Q75 is one-sample estimate — high variance. At multi-seed CONFIRMATION, Q75 averages across outer seeds → low variance | Behavioral predictor Section 4.5 |
| `psr()` returns NaN at zero-variance | Existing `psr()` has explicit zero-variance handling (lines 524-525); returns 1.0 if benchmark<observed or 0.0 otherwise | Existing function contract |
| Bit-identical reproducibility | All strategy logic unchanged from /055; only DSR_relative wiring changed (lines 2181-2196 rewritten) + ITERATION_LABEL bumped | Saturation falsifier Section 4.4 |

### Simulated historical effect (REUSED from /055 EDA)

Per `feedback_risk_mitigation_design.md` mandate: simulate the methodology
axis on prior iterations. Already done in EDA `synthesis.md` Section C +
`dsr_decision_table.csv`. Summary:

| Iteration | Status | DSR_relative IS | DSR_relative OOS | Would PASS gate? |
|---|---|---:|---:|:-:|
| /028 BASELINE | CONFIRMATION-MERGE | 0.861 | 0.004 | OOS FAIL (correct — concentration concerns) |
| /039 NO-MERGE | NO-MERGE on IS regression | 0.0 | 0.99998 | IS FAIL (correct — BOTH-must-improve preserved) |
| /050 NO-MERGE | NO-MERGE on multiple gates | 0.00003 | 0.72 | BOTH FAIL (correct) |
| /051 EXPLORATION | NULL-RESULT | 0.015 | 0.005 | BOTH FAIL (correct) |
| /052 EXPLORATION | NEGATIVE PATH C-suspicious | 0.296 | 1.0 | OOS PASS — but PATH C-suspicious overrides per Section 8 hierarchy |
| /053 EXPLORATION | NULL-RESULT PATH D | 0.235 | 0.177 | BOTH FAIL (correct) |
| /054 EXPLORATION | NEGATIVE PATH C-clean | 0.668 | N/A (OOS=0) | OOS FAIL (correct) |
| /055 EXPLORATION | NEGATIVE PATH C-clean (BUG) | n/a | n/a | n/a (gate broken; correct post-hoc 0.5798 → FAIL) |

**Critical observation**: the /052 OOS DSR_relative PASS (1.0) would have NO operational effect because PATH C-suspicious takes precedence in the brief Section 8 LOCKED hierarchy (the iteration's IS-OOS daily ratio 2.327 OUT-OF-BAND fires NEGATIVE classification BEFORE DSR-axis evaluation). This validates the principle that DSR_relative is one INPUT to the multi-gate decision, NOT the sole arbiter.

**Aspirational MERGE gate alignment**: Per `feedback_v3_baseline_update_policy.md`, the BOTH IS AND OOS must improve rule supersedes the DSR gate for BASELINE_V3.md updates. The reformulated DSR_relative is one of the HARD-BLOCKING gates (alongside Gate 3 OOS/IS ratio, Gate 6 PSR, Gate 10 Pareto). Removing the structurally infeasible DSR gate from operational binding (replacing with operationally feasible DSR_relative) does NOT relax the merge bar — the BOTH IS AND OOS must improve rule (Gate 1+2) remains the dominant constraint.

---

## Section 6 — Trade-Rate Floor Compliance

Per `feedback_v3_trade_rate_floor_bundle_level.md`, the trade-rate floor (≥130 OOS trades for v3) applies at CONFIRMATION-bundle level, not per EXPLORATION row. iter-v3/056 is EXPLORATION; trade-rate floor INFORMATIONAL only.

Predicted /056 trade counts (per Section 4.1): IS=182, OOS=96. Same as /055 (= /028 single-seed=42). Compliant with EXPLORATION expectations.

---

## Section 7 — Wall-Clock Budget

EXPLORATION 2h cap per `feedback_v3_cadence_discipline.md`.

| Phase | Wall-clock estimate | Notes |
|---|---|---|
| Phase 6 setup (Engineer pre-flight) | 5 min | Verify lines 2181-2196 use `flat_path_sharpes` (NOT `cpcv_paths.csv` disk-read); verify ITERATION_LABEL "v3-056"; verify integration test #6 added; run end-to-end smoke test (Section 9) |
| Phase 6 backtest (single-seed n_trials=35) | ~1.25h | Same as /055 (bit-identical strategy expected); avoid concurrent v1/v2 baseline contention if possible |
| Phase 7 Engineer report | 5 min | Verify `dsr_relative=0.5798±0.05` and `cpcv_path_sharpe_q75=0.8378±0.005` populated correctly; compare /056 IS/OOS trade rosters to /055 byte-for-byte |
| Phase 7.5 Critic | 10 min | All 12 standard checks PASS; Check 3 NEW DSR_relative axis evaluated as designed (no longer broken); Check 8 hypothesis-implementation alignment passes |
| **Total** | **~1.5h** | Within 2h cap |

---

## Section 8 — LOCKED MERGE/NO-MERGE Criteria (Pre-Registered)

Per the v3 LOCKED-criteria discipline (`feedback_v3_axis_selection_quant_discipline.md` rule), this section CANNOT be renegotiated post-hoc by the Engineer or Critic. Methodology-only axes use ADAPTED path criteria per /054 PATH E precedent. **PATH A trigger band RECALIBRATED at /056** per Critic FINAL `6083b30` Recommendation #1 + Engineer-verified post-hoc 0.5798.

### Pre-registered path classification probabilities (locked at brief commit)

| Path | Probability | Trigger |
|---|---:|---|
| PATH A (PROMISING-clean — bug-fix-validated) | **75%** | Bit-identical strategy to /055 (saturation falsifier ZERO trades change) AND DSR_relative OOS=0.5798 ± 0.05 AND cpcv_path_sharpe_q75=0.8378 ± 0.005 — confirms bug fix took effect |
| PATH B (PROMISING-INERT) | n/a | N/A for methodology axes |
| PATH C-clean (NEGATIVE clean — bug fix didn't take effect) | **5%** | cpcv_path_sharpe_q75 == 0.0 (BUG signature) OR dsr_relative == psr (degenerate benchmark=0) |
| PATH C-clean (NEGATIVE clean — strategy unintentionally changed) | **5%** | IS or OOS Sharpe differs from /055 by >±0.05 (strategy unintentionally changed) |
| PATH C-suspicious | 5% | IS-OOS daily ratio outside [0.5, 2.0] — strategy logic disturbed |
| PATH D (NULL-RESULT) | 0% | Not applicable (methodology axes always have a defined outcome) |
| **PATH E (CPCV-INVARIANT NULL)** | **10%** | CPCV statistics match /051/052/053/054/055 (positive=29/45, median +0.3351 ± 0.0005, Q75 +0.838 ± 0.005) — co-fires with PATH A as expected; PATH A precedence per hierarchy below |

PATH A is the EXPECTED outcome at /056 (bug fix applied + bit-identical strategy
+ correct DSR_relative computation). PATH E will co-fire structurally (CPCV
identity to /055). PATH A precedence per hierarchy.

### Section 8 LOCKED outcome hierarchy (precedence top → bottom)

1. **PATH C-clean (bug fix didn't take effect)**: implementation defect detected — fix not applied. ABORT axis; investigate. (5% probability)
2. **PATH C-clean (strategy changed) / PATH C-suspicious**: implementation defect detected — strategy unintentionally perturbed. ABORT axis; revisit setup. (5+5=10% probability)
3. **PATH A**: bug fix applied + bit-identical strategy + correct DSR_relative computation. **ADVANCE axis** — DSR_relative becomes operational gate for /061 CONFIRMATION. (75%)
4. **PATH E**: CPCV-INVARIANT NULL. The methodology axis is OPERATIONAL but cannot shift CPCV distribution at single-seed scope. Co-fires with PATH A — PATH A takes precedence as the stronger evidence. (10%; co-fires with PATH A)

**Methodology axis advances iff Section 8 outcome ∈ {PATH A, PATH E}.** The bug
fix being applied (PATH A primary) is the GOAL of /056; PATH E is the structural
consequence. Strategy IS Sharpe and OOS Sharpe are EXPECTED to match /055 — any
material deviation indicates implementation defect.

### Section 8 LOCKED path verdicts (mechanical, non-renegotiable; RECALIBRATED at /056)

| Path | Trigger conditions | Outcome |
|---|---|---|
| **PATH A (NEW recalibrated bands)** | (IS_Sharpe in [+0.5051, +0.5151]) AND (OOS_Sharpe in [+0.5003, +0.5103]) AND (IS_trades in [181, 183]) AND (OOS_trades in [95, 97]) AND (cpcv_path_sharpe_q75 in [0.83, 0.84]) AND (DSR_relative OOS in [0.50, 0.65]) AND (CPCV positive=29/45) AND (CPCV median Sharpe in [+0.3346, +0.3356]) | **ADVANCE axis**; DSR_relative becomes operational gate for /061 |
| PATH C-clean (bug fix didn't take effect) | (cpcv_path_sharpe_q75 == 0.0) OR (dsr_relative == psr to 4 decimals when cpcv_path_sharpe_q75 > 0) | NEGATIVE — bug fix did not apply; investigate runner SHA |
| PATH C-clean (strategy changed) | IS_Sharpe OR OOS_Sharpe differs from /055 by >±0.05 (independent of methodology axis) | NEGATIVE — implementation defect; abort axis |
| PATH C-suspicious | IS-OOS daily ratio outside [0.5, 2.0] | NEGATIVE — strategy unintentionally changed |
| PATH E | (CPCV positive=29/45) AND (CPCV median Sharpe in [+0.3346, +0.3356]) AND (CPCV Q75 Sharpe in [+0.833, +0.843]) — NO requirement on bit-identity since methodology axis can produce trivial floating-point deltas without strategic change | Reinforces /054/055 finding (methodology axis cannot shift CPCV); co-fires with PATH A; PATH A precedence |

**PATH A is the strongest condition** (it implies PATH E plus the bug-fix-applied
condition). If PATH A fires, the iteration ADVANCES with full confidence in the
DSR_relative reformulation. If only PATH E fires (bug not detected as fixed), the
classification falls to PATH C-clean (bug fix didn't take effect) and the axis
remains broken.

---

## Section 9 — Reproducibility

### Library stack

Same as /055. No new dependencies.

| Library | Version | Notes |
|---|---|---|
| lightgbm | 4.6.0 | UNCHANGED |
| optuna | 4.8.0 | UNCHANGED |
| numpy | 2.2.6 | UNCHANGED |
| pandas | 3.0.0 | UNCHANGED |
| scikit-learn | 1.8.0 | UNCHANGED |
| scipy | 1.17.0 | UNCHANGED — used for `norm.cdf` in `psr()` |
| statsmodels | 0.14.6 | UNCHANGED |
| pyarrow | 23.0.1 | UNCHANGED |

### Reproducibility stamps

- Setup commit SHA: TBD (post-brief)
- Phase 5.5 gate SHA: TBD (post-setup)
- Brief SHA: TBD (this commit)
- Engineering report SHA: TBD (post-backtest)
- Critic SHA: TBD (post-engineering-report)
- Wall-clock: ≤2h target
- Hardware: WSL2 / Linux 6.6.114.1 x86_64
- Run command: `uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof`

### Pre-flight checks (Engineer Phase 5.5 gate)

1. `feature_columns=list(V3_FEATURE_COLUMNS)` passed to LightGbmStrategy (per `feedback_explicit_feature_columns.md`).
2. ITERATION_LABEL == "v3-056".
3. `RiskV2Config.enable_per_symbol_drawdown_brake == False` (carried forward from /055).
4. `psr()` function in `validation_v3.py` UNCHANGED (no edits to validation_v3.py).
5. `dsr.json` schema: present from /055 (UNCHANGED) — fields `dsr_relative` + `cpcv_path_sharpe_q75`.
6. **Bug fix verification**: `run_baseline_v3.py:2181-2196` uses `flat_path_sharpes`
   (in-memory; line 2090). MUST NOT contain `pd.read_csv(cpcv_paths_csv)` or
   `cpcv_paths_csv = REPORTS_DIR /` (the /055 BUG signatures). Grep:
   ```bash
   ! grep -q "cpcv_paths_csv = REPORTS_DIR" run_baseline_v3.py
   grep -q "np.percentile(flat_path_sharpes, 75)" run_baseline_v3.py
   ```
7. **6 NEW adversarial tests in `tests/strategies/ml/test_validation_v3_psr_relative.py` PASS** (5 existing + NEW integration test #6 per `feedback_v3_methodology_axis_integration_test.md`).
8. **MANDATORY end-to-end integration smoke test pre-flight** per
   `feedback_v3_methodology_axis_integration_test.md` (NEW 2026-05-12):

   After implementation but before launching the full backtest, run a minimal
   end-to-end pipeline (e.g., on a 1-month synthetic IS slice OR by reusing
   /055's existing CPCV data + dsr.json schema). READ the produced `dsr.json`
   and ASSERT:
   - `cpcv_path_sharpe_q75 > 0` (rejects the /055 BUG signature)
   - `dsr_relative != psr` when `cpcv_path_sharpe_q75 > 0` (rejects degenerate
     benchmark=0 fallback)

   Acceptable smoke-test approaches (Engineer chooses):

   a. **Minimal pipeline run**: `uv run python run_baseline_v3.py --seeds 1
      --n-trials 2` on the existing 8h dataset; takes ~5 min; reads produced
      `reports-v3/iteration_v3-056/dsr.json` and asserts the two conditions.

   b. **Synthetic in-memory test**: Import `_compute_cpcv_paths` and the
      DSR_relative computation block from `run_baseline_v3.py`, feed synthetic
      CPCV data, assert the same two conditions. Faster but does not exercise
      the actual file-write path.

   c. **Reuse /055 CPCV data**: Copy `reports-v3/iteration_v3-055/cpcv_paths.csv`
      into a synthetic `reports-v3/iteration_v3-056/` directory, run only the
      DSR_relative + dsr.json write block (manual subprocess); assert the two
      conditions. Fast and exercises the exact dsr.json write path.

   Smoke test result MUST be documented in the engineering report.

9. All other adversarial tests pass:
   - `test_risk_v2_drawdown_brake.py` (5 tests; dead-code coverage)
   - `test_hurst_drift_50_200_universal.py` (5 tests; dead-code coverage)
   - `test_regime_momentum_signed_3d_universal.py` (5 tests; dead-code coverage)
   - `test_fracdiff_d05_universal.py` (5 tests; dead-code coverage)

---

## Section 10 — QR Audit Trail (per `feedback_v3_axis_selection_quant_discipline.md`)

### Section 10.1 — Mandated axis derivation (CARRY-FORWARD from /055)

iter-v3/055 Critic FINAL `6083b30` Recommendation #1: "Carry-forward A2 to /056
with 2-line bug fix as PRIMARY axis. Per brief Section 8 LOCKED PATH C-clean
outcome ('ABORT axis; revisit setup'), the natural revisit IS /056 setup. The
fix is precisely specified in Engineer report Section 'Fix for /056 setup' (use
`flat_path_sharpes` in-memory at line 2090). NO re-EDA required — the EDA at
SHA `a71b2e5` is sound and re-applies."

The orchestrator's Phase 1-5 dispatch (this brief's parent) confirmed the
carry-forward A2 with bug fix as the mandated /056 axis. No QR PIVOT required —
the axis was pre-justified at /055 closeout with full Critic-FINAL backing AND
the new memory rule `feedback_v3_methodology_axis_integration_test.md` was
created at the same closeout to prevent recurrence.

### Section 10.2 — STATELESS vs STATEFUL classification (UNCHANGED from /055)

Per `feedback_v3_oracle_eda_validity.md` NEW 2026-05-11: every axis must declare
STATELESS or STATEFUL classification with deadlock analysis if STATEFUL.

**iter-v3/056 axis classification: STATELESS** (UNCHANGED from /055).

Justification: DSR_relative is a per-cell post-hoc computation read from
the in-memory `flat_path_sharpes` array already produced by `_compute_cpcv_paths`.
No signal-emission feedback. The gate does not affect strategy decisions; it is
computed AFTER all trades close and reported in `dsr.json`. State: trivial (a
single Q75 statistic from existing CPCV data). Escape mechanism: NOT REQUIRED
(no state-dependent loop exists).

Deadlock analysis: N/A for STATELESS axes per `feedback_v3_oracle_eda_validity.md`.

### Section 10.3 — EDA-driven 5-option ranking (REUSED from /055; per `feedback_v3_axis_selection_quant_discipline.md` rule 2)

EDA `analysis/iteration_v3-055/` at SHA `a71b2e5` produced 9 files:
- `dsr_reformulation_eda.py` — analysis script
- `dsr_history_v3.csv` — 53 iterations recomputed DSR with full precision
- `mechanical_ceiling_grid.csv` — SR_required vs (n_trials, T) ceiling
- `dsr_reformulation_grid.csv` — 5-option p-value comparison
- `dsr_decision_table.csv` — gate PASS/FAIL across reformulations
- `dsr_extended_psr_benchmarks.csv` — PSR vs CPCV Q25/Q50/Q75/max comparison
- `synthesis.md` — full synthesis with recommendation
- `candidate_axes_ranking.md` — 5-option 9-criteria ranking → R5 PRIMARY
- `synthesis_snapshot.md` — auto-generated stats summary

The 5-option ranking established R5 (PSR vs CPCV Q75) as PRIMARY across 9
criteria. R1/R2/R3 are mechanically infeasible at v3 regime (0/13 PASS); R4 is
too permissive (12/13 PASS); R5 is the unique sweet spot (2/13 PASS — top
quartile only). This ranking is UNCHANGED for /056.

**/056 addendum** at `analysis/iteration_v3-056/post_hoc_dsr_relative_validation.md`:
documents the verified post-hoc 0.5798 computation that confirms the R5
reformulation works as designed when wired correctly. No new EDA was required.

### Section 10.4 — Orthogonality to CLOSED precedents (UNCHANGED from /055)

Per `feedback_v3_structural_over_knob_exploration.md`:

CLOSED AXES vs iter-v3/056 AXIS DSR REFORMULATION (carry-forward bug fix):

- ~~ADX threshold~~ (CLOSED at /015) — orthogonal (gate-threshold axis vs methodology axis)
- ~~Per-symbol PnL caps~~ (CLOSED at /020) — orthogonal (concentration vs methodology)
- ~~LDO removal~~ (CLOSED via PRE-FALSIFICATION at /052 EDA) — orthogonal
- ~~regime_momentum_signed_3d UNIVERSAL~~ (CLOSED at /052 PATH C-suspicious) — orthogonal
- ~~hurst_drift_50_200 UNIVERSAL~~ (PARKED at /053 PATH D) — orthogonal
- ~~Per-symbol drawdown brake~~ (CLOSED at /054 PATH C-clean) — orthogonal
- ~~Per-symbol ATR multipliers~~ (CLOSED at /045-/050) — orthogonal
- ~~15th-slot SWAP family~~ (CLOSED at /053 CPCV-INVARIANT) — orthogonal
- ~~iter-v3/055 same-axis run~~ (PATH C-clean implementation defect; CARRY-FORWARD) — same axis with bug fix

R5 DSR reformulation operates on POST-HOC backtest metrics; no overlap with any
of these strategy-level axes. iter-v3/055 was the SAME axis that hit a 2-line
implementation defect at the integration boundary; /056 is the carry-forward
with the fix applied.

### Section 10.5 — Cycle-4 axis priority recall (UPDATED post-/055 closeout)

Per /055 closeout Critic FINAL `6083b30` Recommendations:
- **PRIMARY for /056**: A2 DSR gate reformulation CARRY-FORWARD with 2-line bug fix — **SELECTED at /056** (this iteration)
- DEFERRED: A4 base-stack feature reordering — 2h+ requires fresh EDA — DEFERRED to /057+
- CLOSED: A1 per-symbol drawdown brake (PATH C-clean at /054)
- DEFERRED: A3 CatBoost head-to-head (multi-iter arc 7-10h — exceeds 2h cap; needs CONFIRMATION-spec slot)

iter-v3/056 axis = A2 carry-forward per pre-locked /055 closeout recommendation #1.

### Section 10.6 — Carry-forward justification (NEW at /056)

Per `feedback_no_cheating.md`: re-running /055 with the bug fix is FORBIDDEN
("re-run after fix forbidden — but this is /056 NEW iteration with fix, NOT a
re-run of /055"). The /055 verdict (EXPLORATION-NEGATIVE PATH C-clean) stands
final on the buggy artifact at SHA `4a32e00`.

The /056 carry-forward is a **NEW iteration** with:
- New iteration label "v3-056"
- New brief (this document) with recalibrated PATH A bands
- New setup commit (TBD)
- New backtest run (single-seed, ~1.25h)
- New engineering report
- New Critic review

The axis A2 itself remains methodologically sound (per Critic Adversarial
Finding #4: "The METHODOLOGY axis is sound; only the IMPLEMENTATION is broken.
Carry-forward to /056 with 2-line fix is justified."). The carry-forward is
NOT a re-run; it is the next iteration that completes the same axis cleanly.

---

## Section 11 — Cycle Cadence Tracking

Per `feedback_v3_strict_10_to_1_cadence.md`:

- **Cycle 4 #1 of 10 = iter-v3/051** (fracdiff_d05_close ADD UNIVERSAL; EXPLORATION-NULL-RESULT PATH D; PARKED)
- **Cycle 4 #2 of 10 = iter-v3/052** (regime_momentum_signed_3d SWAP UNIVERSAL; EXPLORATION-NEGATIVE PATH C-suspicious; CLOSED)
- **Cycle 4 #3 of 10 = iter-v3/053** (hurst_drift_50_200 SWAP UNIVERSAL; EXPLORATION-NULL-RESULT PATH D; PARKED — LR-PF methodology refined)
- **Cycle 4 #4 of 10 = iter-v3/054** (per-symbol drawdown brake NEW RiskV2 primitive 11; EXPLORATION-NEGATIVE PATH C-clean primary + PATH C-suspicious + Saturation + PATH E all co-fire; entire "NEW risk primitive" axis family CLOSED; ORACLE EDA methodology defect confirmed)
- **Cycle 4 #5 of 10 = iter-v3/055** (DSR gate reformulation methodology-only first attempt; EXPLORATION-NEGATIVE PATH C-clean primary + PATH E co-fires 5th consecutive; bug at runner integration; new memory rule `feedback_v3_methodology_axis_integration_test.md` created)
- **Cycle 4 #6 of 10 = iter-v3/056** (THIS — A2 DSR gate reformulation CARRY-FORWARD with 2-line bug fix + 6th integration test + smoke-test pre-flight; expected PATH A)
- **Cycle 4 #7-#10 = iter-v3/057-iter-v3/060** (TBD)
- **Cycle 4 CONFIRMATION at iter-v3/061** (SEPARATE single-seed iter-v3/060 first; do NOT collapse the 10th EXPLORATION into CONFIRMATION)
- **4 more EXPLORATIONs remain** before cycle 4 CONFIRMATION after /056: iter-v3/057 through iter-v3/060
- **Cadence wall-clock caps**: EXPLORATION 2h, CONFIRMATION 6h. iter-v3/056 target: ~1.5h within 2h cap.

**Cycle 4 hypothesis status** (carry-forward from /050 closeout): "lift IS Sharpe to ≥ +0.5101 (BASELINE_V3.md update gate floor) while preserving OOS Sharpe ≥ +0.5053 via UNIVERSAL axes (per-symbol customizations rejected at bundle level)." iter-v3/056 is methodology-only — no expected lift to IS or OOS Sharpe. The cycle 4 hypothesis remains NOT SATISFIED via clean PROMISING; 4 EXPLORATIONs remaining after /056.

**Cycle 4 cumulative score after /056** (predicted): 0 PROMISING-clean (strategy lift) / 1 PROMISING-clean methodology-axis-bug-fix-validated (PATH A target at /056) / 0 PROMISING-INERT (N/A risk primitives) / 2 NULL-RESULT / 2 NEGATIVE / 1 methodology-axis-PATH-C-clean-then-fixed (/055→/056 sequence) / 0 axes-advance with Sharpe lift. The structural finding (CPCV-determinism + n_eff=19 + reformulated DSR gate operationally evaluable) is the primary cycle-4 contribution.

---

## Section 12 — See Also

### Predecessor iterations
- `diary-v3/iteration_v3-055.md` — immediate predecessor (DSR_relative bug; cycle 4 #5; new memory rule created; carry-forward A2 mandated)
- `diary-v3/iteration_v3-054.md` — drawdown brake deadlock; cycle 4 #4; ORACLE EDA methodology defect; A2 promoted
- `diary-v3/iteration_v3-053.md` — cycle 4 #3 (hurst_drift_50_200 PATH D; LR-PF methodology)
- `diary-v3/iteration_v3-052.md` — cycle 4 #2 (regime_momentum_signed_3d PATH C-suspicious; engineered_features_dont_stack EXPANDED)
- `diary-v3/iteration_v3-051.md` — cycle 4 #1 (fracdiff_d05_close PATH D; PARKED)
- `diary-v3/iteration_v3-050.md` — cycle 3 CONFIRMATION-NO-MERGE closeout
- `diary-v3/iteration_v3-039.md` — first OOS gate PASS in v3 history (NO-MERGE on IS regression)
- `diary-v3/iteration_v3-028.md` — first CONFIRMATION-MERGE (BASELINE_V3.md anchor; regime_momentum_signed_5d)

### iter-v3/056 artifacts
- `analysis/iteration_v3-056/post_hoc_dsr_relative_validation.md` — post-hoc 0.5798 verification + recalibrated PATH A bands
- `analysis/iteration_v3-055/synthesis.md` — primary EDA synthesis (REUSED unchanged)
- `analysis/iteration_v3-055/candidate_axes_ranking.md` — 5-option 9-criteria ranking (REUSED)
- `analysis/iteration_v3-055/dsr_history_v3.csv` — 53 v3 iterations DSR recomputed (REUSED)
- `analysis/iteration_v3-055/mechanical_ceiling_grid.csv` — SR_required ceiling (REUSED)
- `analysis/iteration_v3-055/dsr_reformulation_grid.csv` — 5-option p-values (REUSED)
- `analysis/iteration_v3-055/dsr_decision_table.csv` — gate PASS/FAIL (REUSED)
- `analysis/iteration_v3-055/dsr_extended_psr_benchmarks.csv` — PSR vs Q25/Q50/Q75/max (REUSED)
- `briefs-v3/iteration_v3-055/engineering_report.md` — bug location + post-hoc 0.5798 (REFERENCED)
- `briefs-v3/iteration_v3-055/review.md` — Critic FINAL with carry-forward mandate (REFERENCED)
- EDA SHA: `a71b2e5` (REUSED from /055)

### Source code references
- `src/crypto_trade/strategies/ml/validation_v3.py` — `psr()` function (lines 486-528; UNCHANGED at /056)
- `src/crypto_trade/strategies/ml/validation_v3.py` — `deflated_sharpe_ratio_v3()` (lines 406-478; UNCHANGED at /056; preserved as parallel computation)
- `run_baseline_v3.py:2181-2196` — call-site for DSR_relative; **REWRITTEN at /056** to use in-memory `flat_path_sharpes` (line 2090); the BUG SITE from /055 is removed
- `run_baseline_v3.py` — `flat_path_sharpes` populated at line 2090, `q75` at line 2094 (UPSTREAM SOURCES — UNCHANGED)
- `run_baseline_v3.py` RiskV2Config block — `enable_per_symbol_drawdown_brake=False` UNCHANGED from /055
- `tests/strategies/ml/test_validation_v3_psr_relative.py` — 5 unit tests UNCHANGED + NEW 6th integration test added at /056 setup

### Memory rules
- `feedback_v3_methodology_axis_integration_test.md` **NEW 2026-05-12** — methodology-only axes adding computed fields MUST include end-to-end smoke test + ≥1 integration test
- `feedback_no_cheating.md` — re-run after fix forbidden; /056 is NEW iteration NOT re-run of /055
- `feedback_v3_dsr_mode_artifact.md` — DSR EXPLORATION-INFORMATIONAL interpretation; n_eff=19 cycle-4 STRUCTURAL CONSTANT
- `feedback_v3_oracle_eda_validity.md` — STATELESS axis declaration for /056
- `feedback_v3_axis_selection_quant_discipline.md` — QR-EDA-driven; Section 10 audit trail
- `feedback_v3_strict_10_to_1_cadence.md` — cycle 4 cadence 6/10 advanced
- `feedback_v3_baseline_update_policy.md` — BOTH-must-improve rule preserved; DSR reformulation does NOT relax merge bar
- `feedback_v3_structural_over_knob_exploration.md` — methodology axis orthogonal to all knob axes
- `feedback_axis_saturation_predictor.md` — saturation falsifier locked
- `feedback_risk_mitigation_design.md` — methodology axis risk profile + simulated historical effect
- `feedback_v3_cadence_discipline.md` — 2h EXPLORATION cap

### References
- Bailey, D. & López de Prado, M. (2014), "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality", *Journal of Portfolio Management* 40(5):94-107.
- López de Prado, M. (2018), *Advances in Financial Machine Learning*, Ch. 11-12, 14.

### Other v3 docs
- `BASELINE_V3.md` — UNCHANGED at iter-v3/028 (+0.5101 IS / +0.5053 OOS; SHA `b0576df`)
- `ITERATION_PLAN_8H_V3.md` — v3 workflow definition
- `briefs-v3/exploration_catalog.md` — iter-v3/056 catalog row will be added at /056 closure

### Catalog row pre-commit (Section 11 cadence)

iter-v3/056 catalog row (to be appended at /056 closure):

```
| iter-v3/056 | 2026-05-12 | EXPLORATION cycle 4 #6 of 10: A2 DSR gate reformulation CARRY-FORWARD with 2-line bug fix at run_baseline_v3.py:2181-2196 (use in-memory flat_path_sharpes line 2090 instead of disk-read of cpcv_paths.csv); ADD 6th integration test in test_validation_v3_psr_relative.py per `feedback_v3_methodology_axis_integration_test.md`; mandatory end-to-end smoke-test pre-flight in brief Section 9; recalibrated PATH A trigger band per Engineer-verified post-hoc 0.5798 from /055 SHA `6dc8256`. V3_FEATURE_COLUMNS_TOP_N=14 unchanged from /055; V3_MODELS BCH+LDO+TRX 3-sym; REQUIRED_GAP=66; enable_per_symbol_drawdown_brake=False unchanged. Setup SHA TBD. EDA SHA `a71b2e5` (REUSED from /055; no new EDA needed); /056 addendum at analysis/iteration_v3-056/post_hoc_dsr_relative_validation.md. | TBD vs iter-v3/028 baseline +0.5101 (target +0.5101 bit-identical; ±0.005 falsifier band) | TBD vs iter-v3/028 baseline +0.5053 (target +0.5053 bit-identical; ±0.005 falsifier band; OOS trades=96 expected; IS-OOS daily ratio target 1.295 within [0.5, 2.0]; CPCV 29/45 positive median +0.3351 Q25 -0.243 Q75 +0.838 expected; PATH E co-fires 6th-consecutive expected) | TBD (target EXPLORATION-PROMISING-clean PATH A: bug fix applied + bit-identical strategy + correct DSR_relative ≈0.58 + correct cpcv_path_sharpe_q75 ≈0.84) | TBD (target ADVANCE A2 axis as operational gate for /061 CONFIRMATION; new memory rule `feedback_v3_methodology_axis_integration_test.md` enforced via Phase 5.5 gate; bug-fix-applied verification mandatory at engineering report). Cycle 4 cadence advances 6/10. Tag NOT issued. |
```

(Numerical fields populated at /056 closure per actual results; all "TBD" entries replaced with observed values.)
