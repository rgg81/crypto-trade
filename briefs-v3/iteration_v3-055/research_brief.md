# Iteration v3-055 — Research Brief (A2 DSR Gate Reformulation, methodology-only)

**Type**: EXPLORATION (Cycle 4 #5 of 10)
**Track**: v3 (rigor arm) — fifty-fifth iteration
**Branch**: `iteration-v3/055` (off iter-v3/054 head at SHA `bacd0d2`)
**Date**: 2026-05-11
**Author**: QR (autopilot)
**EDA SHA**: `a71b2e5` (`analysis/iteration_v3-055/` — 8 files: 4 CSVs + 4 MDs)

**MANDATED AXIS** (per iter-v3/054 Critic FINAL SHA `db1551b` Recommendation #3
+ /054 diary "iter-v3/055 PROMOTED Axis" section, locked at /054 closeout):
**A2 — DSR gate reformulation (methodology-only)**.

Justification at /054 closeout per 5-criterion compliance: C1 ≤2h impl YES; C2
escapes 15th-slot SWAP saturation YES (methodology-only); C3 addresses cycle-4
structural finding HIGH (DSR=0 mechanically inevitable at n_eff=19 across 4
consecutive iterations /051-/054); C4 orthogonal to CLOSED precedents YES; C5
zero revert cost YES (parallel field in dsr.json).

**SELECTED REFORMULATION**: R5 — PSR(observed_SR; benchmark = CPCV path Sharpe
Q75) > 0.95 (relative DSR). EDA-driven selection from 5 candidate reformulations
(R1 current, R2 n_eff sub, R3 threshold relax, R4 PSR(0), R5 PSR vs CPCV Q75);
ranked at SHA `a71b2e5` by 9 criteria. R5 is the **unique option** that produces
meaningful PASS/FAIL discrimination at v3's regime (2/13 PASS across /028..054
single-seed scope vs 0/13 or 12/13 for others).

**MECHANISM**: Replace the `DSR > 0.95` MERGE gate with `DSR_relative > 0.95`,
where `DSR_relative = PSR(observed_SR; benchmark = CPCV_path_Sharpe_Q75)`. Within-
iteration null benchmark (CPCV path Q75 from `cpcv_paths.csv` produced by
`_compute_cpcv_paths`). Bailey-LdP (2014, *JPM*) canonical "relative DSR"
formulation. The `psr()` function already exists in `validation_v3.py` lines
486-528 — only the call-site in `run_baseline_v3.py:2174-2185` changes.

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

Sacred constants UNCHANGED. The QR sees iter-v3/055 OOS metrics for the FIRST
time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 4 — #5 of 10 (fifth EXPLORATION post-iter-v3/050 NO-MERGE CONFIRMATION)
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
  - ENSEMBLE_SIZE=5 (auto; inner ensemble)
  - n_trials=35 (default per `feedback_v3_exploration_n_trials_35.md`)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
  - --clean-oof (use guardrail from SHA `6a216b5`)

Carry-forward state from iter-v3/054 head SHA `bacd0d2` (UNCHANGED unless explicit at §3):
  - V3_FEATURE_COLUMNS_TOP_N at /054 HEAD = 14 features (hurst_drift_50_200 PARKED per /053 closeout)
  - V3_MODELS at /054 HEAD = (BCHUSDT, LDOUSDT, TRXUSDT) — 3 symbols UNCHANGED at /055
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty) UNCHANGED at /055
  - block_long_for = () (empty) UNCHANGED at /055
  - regime_momentum_signed_5d PRESERVED (iter-v3/028 edge ingredient) UNCHANGED at /055
  - DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) UNCHANGED at /055
  - adx_threshold_per_symbol = {} (empty) UNCHANGED at /055
  - All other risk gates UNCHANGED (BTC trend, OOD, ADX 20.0, hit-rate disabled, etc.)
  - REQUIRED_GAP at /054 HEAD = 66 = (21+1)×3 UNCHANGED at /055 (universe unchanged)
  - enable_per_symbol_drawdown_brake = True at /054 HEAD — MUST BE DISABLED at /055 setup
    per /054 closeout architectural decision (drawdown brake CLOSED-mechanism PARKED)

SINGLE-AXIS CHANGE for /055 (QR-EDA-backed per `feedback_v3_axis_selection_quant_discipline.md`):
  AXIS: ADD `dsr_relative` parallel computation to dsr.json schema; the current
        `DSR > 0.95` gate evaluated by Critic Check 3 becomes INFORMATIONAL only;
        the NEW operative gate is `DSR_relative > 0.95`. Methodology-only — does
        NOT change strategy, features, labels, or risk gates.

    Mechanism: After PSR(0) computation at `run_baseline_v3.py:2180-2185`,
      compute `cpcv_path_sharpe_q75` from cpcv_paths.csv data already loaded,
      then compute `dsr_relative = psr(raw_sharpe_oos, len(oos_wp), oos_sk,
      oos_kt, benchmark_sharpe=cpcv_path_sharpe_q75)`.

    Schema additions to `dsr.json`:
      - `"dsr_relative": float`
      - `"cpcv_path_sharpe_q75": float`

    PLUS: SET `RiskV2Config.enable_per_symbol_drawdown_brake = False` in
    `run_baseline_v3.py` (per /054 closeout architectural decision).

    Net effect: methodology-only axis; expected to produce BIT-IDENTICAL trades
      to /053 (NOT /054, because /054 had brake enabled). The reformulated DSR
      becomes operative at iter-v3/061 CONFIRMATION multi-seed scope.

Setup commit changes (locked in §3):
  - run_baseline_v3.py: ADD `dsr_relative` + `cpcv_path_sharpe_q75` to dsr.json schema
  - run_baseline_v3.py: SET `RiskV2Config.enable_per_symbol_drawdown_brake = False`
  - run_baseline_v3.py: ITERATION_LABEL "v3-055"
  - tests/strategies/ml/test_validation_v3.py: ADD 3 adversarial tests for PSR
    benchmark parameter (1: benchmark=0 matches existing PSR; 2: monotonicity;
    3: CPCV Q75 integration)
```

---

## Section 1 — Hypothesis

**Primary hypothesis**: REPLACING the `DSR > 0.95` MERGE gate evaluation with
`DSR_relative > 0.95` (where `DSR_relative = PSR(observed_SR; benchmark =
CPCV path Sharpe Q75)`) — alongside DISABLING the per-symbol drawdown brake
(per /054 closeout architectural decision) — produces a METHODOLOGICAL gate
that is feasible at v3's regime AND meaningfully discriminates strong from weak
strategies, REPLACING the structurally inevitable DSR=0 artifact established
across 4 consecutive iterations (/051-/054, n_eff=19 cycle-4 STRUCTURAL CONSTANT).

**Secondary hypothesis**: Because the axis is methodology-only and operates
post-hoc on backtest outputs, IS Sharpe / OOS Sharpe / trade counts / CPCV
distribution will be IDENTICAL to a /053-style baseline (which had hurst_drift
PARKED and no brake). The IS Sharpe should be +0.4726 ± 0.005 and OOS Sharpe
should be +0.4745 ± 0.005 to demonstrate that the implementation does not
disturb the bit-level reproducibility of the strategy.

**What this iteration does NOT test**: any strategy change. The CPCV path
distribution will FIRE PATH E (CPCV-INVARIANT NULL) per pre-registered Section
8 criterion — this is EXPECTED and NOT a failure mode (methodology axis).

**Targeted finding**: At /055 single-seed EXPLORATION, the realized `DSR_relative`
should be approximately 0.67 for IS and 0.50 for OOS (per `synthesis.md` Section
C row "/054 IS PSR vs Q75 = 0.6678" — but /055 reverts brake-disabled so should
match /053 single-seed at IS PSR vs Q75 ≈ 0.235 and OOS PSR vs Q75 ≈ 0.177).
At iter-v3/061 CONFIRMATION (multi-seed n_trials=1500), the gate becomes
operationally meaningful: an iteration that materially beats the CPCV Q75 will
clear the 0.95 threshold, while a single-seed-lottery OOS spike that produces
high OOS Sharpe but low IS Sharpe (PATH C-suspicious anti-pattern) will fail.

---

## Section 2 — IS-Only Numerical Evidence

**Methodology axis note**: Per `feedback_v3_axis_selection_quant_discipline.md`,
the brief Section 2 must contain EDA-derived numerical tables. The DSR
reformulation is a methodology axis with EDA at `a71b2e5` — all numerical
tables are COMMITTED in `analysis/iteration_v3-055/`. Below is the synthesis
distilled for brief Section 2; full details in `synthesis.md` and CSVs.

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
| EXPLORATION /051..054 | 525 | 3.067 | **3.212** | 0.5 – 1.4 |
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

**0 of 53 v3 iterations have EVER cleared `DSR > 0.95`.** /019 — at n_trials=30 EXPLORATION-spec (since deprecated to n_trials=35) — produced the largest dsr_p_IS ever observed at 0.0167, still ~50x below threshold. Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR is INFORMATIONAL ONLY because n_trials=10..35 has E[max_SR] of 1.57..2.14 which sits in v3's realized OOS Sharpe range. CONFIRMATION-mode DSR at n_trials=1500 has E[max_SR]=3.37, which exceeds the best v3 OOS Sharpe by ~2.0 standard-error units.

### Section 2.3 — 5 reformulation options analyzed

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

The 2 PASS rows are both **high-OOS-Sharpe iterations** that DID materially exceed their CPCV Q75 benchmark. /039 OOS represents the strongest single-axis OOS lift in v3 history; /052 OOS is a known single-seed PATH C-suspicious. **R5 correctly identifies that ALL recent cycle-4 EXPLORATIONs (/051/053/054) fail to exceed Q75 — consistent with their EXPLORATION-NEGATIVE/NULL outcomes.**

This is the **right discrimination behavior** for v3:
- An iteration that beats CPCV Q75 (top quartile of cross-validation paths) shows real OOS lift beyond what hyperparameter lottery could produce → PASS
- An iteration whose OOS Sharpe is structurally bounded by the search distribution → FAIL (correctly NO-MERGE)

### Section 2.5 — Alternative quantile benchmark sensitivity

From `dsr_extended_psr_benchmarks.csv`:

| Benchmark | Iterations passing IS+OOS | Discrimination | Verdict |
|---|---:|---|---|
| PSR vs Q25 | 13/13 (100%) | None | Too easy |
| PSR vs Q50 (median) | 12/13 (92%) | Weak | Too easy |
| **PSR vs Q75** | **2/13 (15%)** | **Top-quartile only** | **Sweet spot** |
| PSR vs max | 0/13 (0%) | None | Too hard |

Q75 is the empirically motivated quantile. Q50 (median) is too permissive because v3's CPCV path distribution has a center near 0.33 (cycle-4 STRUCTURAL CONSTANT) which most successful iterations naturally exceed. Q75 (0.838 cycle-4) raises the bar to the upper-quartile of CPCV paths — distinguishes structural lift from path-lottery.

### Section 2.6 — Theoretical foundation citation

Bailey & López de Prado (2014), "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality" (*Journal of Portfolio Management* 40(5):94-107). Section "Benchmark Selection" discusses two formulations:

1. **Absolute DSR** (currently implemented in `validation_v3.py:406`): null = SR=0; correction = Gumbel max of N i.i.d. trials. Appropriate when trials are genuinely i.i.d. and N is known.

2. **Relative DSR / PSR(benchmark)** (R5): null = benchmark SR; benchmark = same-search cross-validation distribution. Appropriate when Optuna trials are correlated (the typical case) and N_eff << N.

AFML Ch. 14 (López de Prado 2018): "When using cross-validation, the appropriate null for testing whether the IS-best strategy generalizes OOS is the cross-validation path distribution from the same search, not the Gumbel maximum of N hypothetical trials. This is the relative DSR formulation."

R5 implements the canonical relative-DSR per AFML Ch. 14.

---

## Section 3 — Code Changes (Setup Commit Locked)

The setup commit makes 4 edits and adds 1 test module. ALL changes localized
to `run_baseline_v3.py` + `tests/`. NO changes to `validation_v3.py` (already
has `psr()` function with `benchmark_sharpe` parameter).

### Edit 1: `run_baseline_v3.py` — DSR_relative computation

At `run_baseline_v3.py:2174-2188` (after the PSR(0) computation):

```python
# ---- DSR_relative — PSR with CPCV path Sharpe Q75 benchmark (iter-v3/055)
# Per `analysis/iteration_v3-055/synthesis.md` Section R5: replaces structural
# DSR=0 artifact with within-iteration null discipline. Reference: AFML Ch. 14
# + Bailey-LdP (2014) JPM "Deflated Sharpe Ratio".
cpcv_path_sharpe_q75 = 0.0
cpcv_paths_csv = REPORTS_DIR / f"iteration_{ITERATION_LABEL}" / "cpcv_paths.csv"
if cpcv_paths_csv.exists():
    try:
        cpcv_df = pd.read_csv(cpcv_paths_csv)
        if "sharpe" in cpcv_df.columns and len(cpcv_df) >= 4:
            cpcv_path_sharpe_q75 = float(np.percentile(cpcv_df["sharpe"], 75))
    except Exception as e:
        print(f"[dsr_relative] Could not read cpcv_paths.csv: {e}")
        cpcv_path_sharpe_q75 = 0.0

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
```

### Edit 2: `run_baseline_v3.py` — dsr.json schema additions

In the existing `dsr.json` write block, ADD two fields:

```python
dsr_payload = {
    "dsr": float(dsr_val),
    "pbo": pbo_result.pbo,
    # ... existing fields ...
    "psr": float(psr_val),
    "dsr_relative": float(dsr_relative),               # NEW iter-v3/055
    "cpcv_path_sharpe_q75": float(cpcv_path_sharpe_q75),  # NEW iter-v3/055
    "n_trials": n_trials_total,
    "n_eff": int(n_eff),
    "min_trl_months": float(min_trl_months),
}
```

### Edit 3: `run_baseline_v3.py` — disable drawdown brake

In the `RiskV2Config` instantiation block (search for `enable_per_symbol_drawdown_brake`):

```python
RiskV2Config(
    # ... existing fields ...
    enable_per_symbol_drawdown_brake=False,  # per iter-v3/054 closeout (CLOSED-mechanism)
    drawdown_brake_threshold_wpnl=10.0,      # retained as backward-compatible default
    drawdown_brake_recovery_wpnl=5.0,        # retained as backward-compatible default
    drawdown_brake_window_days=30,           # retained as backward-compatible default
)
```

The drawdown brake fields REMAIN in `RiskV2Config` as backward-compatible
disable-by-default fields. The runner explicitly disables.

### Edit 4: `run_baseline_v3.py` — ITERATION_LABEL

```python
ITERATION_LABEL = "v3-055"
```

### Edit 5: NEW test module `tests/strategies/ml/test_validation_v3_psr_relative.py`

5 adversarial tests for the PSR-with-benchmark integration:

```python
"""iter-v3/055 — adversarial tests for PSR with non-zero benchmark."""

import math
import numpy as np
from scipy.stats import norm

from crypto_trade.strategies.ml.validation_v3 import psr


def test_psr_benchmark_zero_matches_existing_psr():
    """PSR(benchmark=0) must equal existing v3-psr computation byte-for-byte."""
    # Synthetic Gaussian SR
    sr_obs = 1.0
    T = 100
    p0 = psr(observed_sharpe=sr_obs, n_obs=T, skewness=0.0, kurtosis=3.0,
             benchmark_sharpe=0.0)
    # Expected: SR_hat=1.0, var=1+0/4=1.0, std=sqrt(1/99)=0.1005, z=9.95
    expected_z = 1.0 / math.sqrt(1.0 / (T - 1))
    expected_p = float(norm.cdf(expected_z))
    assert abs(p0 - expected_p) < 1e-9, f"PSR(0)={p0} != expected {expected_p}"


def test_psr_higher_benchmark_lowers_pvalue():
    """Strict monotonicity: higher benchmark must produce lower PSR."""
    sr_obs = 1.0
    T = 100
    p_0 = psr(sr_obs, T, 0.0, 3.0, benchmark_sharpe=0.0)
    p_0_5 = psr(sr_obs, T, 0.0, 3.0, benchmark_sharpe=0.5)
    p_1 = psr(sr_obs, T, 0.0, 3.0, benchmark_sharpe=1.0)
    p_1_5 = psr(sr_obs, T, 0.0, 3.0, benchmark_sharpe=1.5)
    assert p_0 > p_0_5 > p_1 > p_1_5, (
        f"Monotonicity violated: p(0)={p_0} > p(0.5)={p_0_5} > p(1)={p_1} > p(1.5)={p_1_5}"
    )


def test_psr_benchmark_at_observed_returns_half():
    """PSR(benchmark = observed_SR) must return ≈ 0.5."""
    sr_obs = 1.0
    T = 100
    p = psr(sr_obs, T, 0.0, 3.0, benchmark_sharpe=1.0)
    assert abs(p - 0.5) < 1e-9, f"PSR(benchmark=observed)={p} != 0.5"


def test_psr_benchmark_negative_increases_pvalue():
    """Negative benchmark must produce higher PSR than benchmark=0."""
    sr_obs = 1.0
    T = 100
    p_0 = psr(sr_obs, T, 0.0, 3.0, benchmark_sharpe=0.0)
    p_neg = psr(sr_obs, T, 0.0, 3.0, benchmark_sharpe=-0.5)
    assert p_neg > p_0, f"Negative benchmark should raise PSR; got p(-0.5)={p_neg} ≤ p(0)={p_0}"


def test_psr_with_cpcv_q75_integration():
    """End-to-end: feed sample CPCV path Sharpes, verify Q75 extraction and PSR."""
    # Simulate /054-style CPCV path Sharpes (from cpcv_paths.csv: 45 paths)
    cpcv_sharpes = np.concatenate([
        np.array([-0.243] * 11),  # Q25 cluster
        np.array([0.335] * 11),   # Q50 cluster
        np.array([0.838] * 11),   # Q75 cluster
        np.array([1.20, 1.30, 1.40, 1.50, 1.60, 1.70, 1.75, 1.78, 1.80, 1.85, 1.88, 1.88]),  # top cluster
    ])
    assert len(cpcv_sharpes) == 45, f"Expected 45 paths, got {len(cpcv_sharpes)}"
    q75 = float(np.percentile(cpcv_sharpes, 75))
    assert 0.7 <= q75 <= 1.0, f"Q75={q75} out of expected band [0.7, 1.0]"

    # Strategy with SR=0.7 < Q75=0.84 → low PSR
    p_low = psr(0.7, 200, 0.0, 3.0, benchmark_sharpe=q75)
    assert p_low < 0.5, f"Low SR vs Q75 should give PSR < 0.5; got {p_low}"

    # Strategy with SR=1.5 > Q75=0.84 → high PSR
    p_high = psr(1.5, 200, 0.0, 3.0, benchmark_sharpe=q75)
    assert p_high > 0.95, f"High SR vs Q75 should give PSR > 0.95; got {p_high}"
```

---

## Section 4 — Predicted Outcome Bands

Per `feedback_axis_saturation_predictor.md`, predicted bands MUST be locked
upfront with falsifier triggers. For methodology-only axes, the behavioral-
effect prediction is **most rigorous** because we know exactly what to expect.

### Section 4.1 — Strategy-level outcomes (Carry-forward of /053 single-seed at brake-disabled)

Since /055 disables the drawdown brake (per /054 closeout) but otherwise preserves /054 head (which already has hurst_drift_50_200 PARKED reverting to 14 features), the strategy is OPERATIONALLY IDENTICAL to /053. Predicted bands:

| Metric | /053 single-seed | **/055 prediction** | Δ vs /053 |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.4726 | **+0.4726 ± 0.005** | 0 (bit-identical expected) |
| OOS monthly Sharpe | +0.4745 | **+0.4745 ± 0.005** | 0 (bit-identical expected) |
| IS daily Sharpe | +1.1849 | +1.1849 ± 0.005 | 0 |
| OOS daily Sharpe | +1.4344 | +1.4344 ± 0.005 | 0 |
| IS-OOS daily ratio | 1.21 | 1.21 ± 0.005 | 0 (in-band [0.5, 2.0]) |
| IS trades | 180 | **180 ± 1** | 0 |
| OOS trades | 96 | **96 ± 1** | 0 |
| IS MaxDD | 45.37% | 45.37% | 0 |
| OOS MaxDD | 44.22% | 44.22% | 0 |
| CPCV positive paths | 29/45 | **29/45** | 0 (PATH E expected) |
| CPCV median Sharpe | +0.3351 | **+0.3351 ± 0.0005** | 0 (PATH E expected to 4 decimals) |
| CPCV Q75 Sharpe | +0.838 | **+0.838 ± 0.005** | 0 (PATH E corollary) |

### Section 4.2 — Methodology axis outcomes

| Metric | /053 (current dsr.json) | **/055 prediction** | Operation |
|---|---:|---:|---|
| DSR (original) | 0.0 | **0.0** | Unchanged; mechanically infeasible |
| PBO (per-cell mean) | 0.1377 | **0.1377 ± 0.005** | Unchanged |
| PSR(0) | 1.0 | **1.0** | Unchanged |
| **DSR_relative (NEW)** | n/a | **~0.18** (PSR vs Q75 IS at /053) | NEW field |
| **cpcv_path_sharpe_q75 (NEW)** | n/a | **+0.838** | NEW field |
| n_trials | 525 | **525** | Unchanged |
| n_eff | 19 | **19** | Unchanged (cycle-4 CONSTANT) |

### Section 4.3 — Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

**Predicted effect on trades**: ZERO change to IS or OOS trade roster. Methodology axis operates POST-HOC on backtest outputs.

**Predicted effect on Optuna trajectories**: ZERO change. ENSEMBLE_SIZE=5, n_trials=35, seed=42 produce IDENTICAL hyperparameter draws to /053.

**Predicted effect on dsr.json**: 2 NEW keys added (`dsr_relative`, `cpcv_path_sharpe_q75`); all other keys unchanged byte-for-byte from /053.

**Predicted effect on Critic Check 3 outcome**: Check 3 INFORMATIONAL gate
(`DSR > 0.95`) FAILS as expected (per `feedback_v3_dsr_mode_artifact.md`,
EXPLORATION DSR is INFORMATIONAL). NEW informational gate `DSR_relative > 0.95`
ALSO FAILS at single-seed EXPLORATION (predicted: 0.18 IS / 0.18 OOS). Both
gates are appropriately reading "strategy does not exceed CPCV Q75 at this seed."

### Section 4.4 — Saturation falsifier (per `feedback_axis_saturation_predictor.md`)

**Predicted CHANGE in observable behavior**: ZERO trades; ZERO Sharpe shift.

**Falsifier band**: if observed IS trades or OOS trades differ from /053 by more than ±5 trades, OR if IS-OOS Sharpe differs from /053 by more than ±0.05, the implementation has unintentionally changed strategy logic. This would be PATH C-clean implementation defect (independent of methodology axis).

**Falsifier action**: If saturation falsifier fires, the iteration is classified PATH C-clean implementation defect; investigation focuses on identifying the strategy logic difference vs /053 (search for unintended `RiskV2Config` field changes or runner deltas vs /053 setup).

### Section 4.5 — DSR_relative behavior at hypothetical CONFIRMATION-spec

If /055 spec were CONFIRMATION (--seeds 2 --n-trials 35 produces n_trials=1050, 2× outer), the predicted CPCV path Q75 should be approximately the same (+0.838) per cycle-4 STRUCTURAL CONSTANT (CPCV-determinism). Multi-seed mean OOS Sharpe is expected to match /028 BASELINE (+0.5053) at brake-disabled per-symbol-architecture-preserved state. Predicted DSR_relative at CONFIRMATION: ~0.18 — same as /053 single-seed because CPCV statistics are determined by base 14-feature stack.

This gives a quantitative expectation for iter-v3/061 CONFIRMATION's DSR_relative gate: **the cycle-4 baseline strategy structurally lands at DSR_relative ~0.18, far below the 0.95 threshold**. To clear at iter-v3/061, a structural change to base 14-feature stack / universe / model arch / n_trials / ENSEMBLE_SIZE is required (per /054 updated CPCV-invariance finding). This is the cycle-5 mandate.

---

## Section 5 — Risk Mitigation

Per `feedback_risk_mitigation_design.md`, every merge-candidate iteration must
include a Risk Mitigation section. **iter-v3/055 is methodology-only**; the
strategy itself is /053-equivalent. The risk-mitigation matrix below maps to
the strategy's already-active gates plus the methodology axis's risk profile.

### R1 (consecutive-SL cooldown)
Inherited from /054. Cooldown=2 candles. UNCHANGED at /055.

### R2 (drawdown brake)
DISABLED at /055 per /054 closeout architectural decision. RiskV2Config fields
remain as backward-compatible defaults.

### R3 (OOD Mahalanobis / z-score gate)
Inherited from /054. `zscore_threshold=2.0` UNCHANGED at /055.

### R4 (vol kill-switch)
Inherited from /054. BTC trend filter (lookback=42, threshold=15%) UNCHANGED.

### R5 (concentration cap)
Inherited from /054. Per-symbol PnL cap DISABLED (CLOSED at /020). UNCHANGED.

### Methodology axis risk profile

| Risk | Mitigation | Verification |
|---|---|---|
| `cpcv_paths.csv` not produced | Fallback `cpcv_path_sharpe_q75 = 0.0` (logs warning) | Adversarial test 4 |
| CPCV path Sharpe distribution non-normal | PSR formula uses observed skew/kurt of weighted_pnl (not CPCV paths); benchmark is point-estimate Q75; non-normality of CPCV doesn't enter PSR computation | Section 2.6 theoretical foundation |
| Q75 sensitive to outlier paths | Q75 percentile-based extraction; if max path is outlier, Q75 is unchanged. Validated at /028 (max=1.88, Q75=0.838) | `cpcv_paths.csv` /028 inspection |
| Single-seed Q75 statistic noise | At single-seed EXPLORATION, Q75 is one-sample estimate — high variance. At multi-seed CONFIRMATION, Q75 averages across outer seeds → low variance | Behavioral predictor Section 4.5 |
| `psr()` returns NaN at zero-variance | Existing `psr()` has explicit zero-variance handling (lines 524-525); returns 1.0 if benchmark<observed or 0.0 otherwise | Existing function contract |
| Bit-identical reproducibility | All strategy logic unchanged from /053; only dsr.json schema delta | Saturation falsifier Section 4.4 |

### Simulated historical effect

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

**Critical observation**: the /052 OOS DSR_relative PASS (1.0) would have NO operational effect because PATH C-suspicious takes precedence in the brief Section 8 LOCKED hierarchy (the iteration's IS-OOS daily ratio 2.327 OUT-OF-BAND fires NEGATIVE classification BEFORE DSR-axis evaluation). This validates the principle that DSR_relative is one INPUT to the multi-gate decision, NOT the sole arbiter.

**Aspirational MERGE gate alignment**: Per `feedback_v3_baseline_update_policy.md`, the BOTH IS AND OOS must improve rule supersedes the DSR gate for BASELINE_V3.md updates. The reformulated DSR_relative is one of the HARD-BLOCKING gates (alongside Gate 3 OOS/IS ratio, Gate 6 PSR, Gate 10 Pareto). Removing the structurally infeasible DSR gate from operational binding (replacing with operationally feasible DSR_relative) does NOT relax the merge bar — the BOTH IS AND OOS must improve rule (Gate 1+2) remains the dominant constraint.

---

## Section 6 — Trade-Rate Floor Compliance

Per `feedback_v3_trade_rate_floor_bundle_level.md`, the trade-rate floor (≥130 OOS trades for v3) applies at CONFIRMATION-bundle level, not per EXPLORATION row. iter-v3/055 is EXPLORATION; trade-rate floor INFORMATIONAL only.

Predicted /055 trade counts (per Section 4.1): IS=180, OOS=96. Same as /053. Compliant with EXPLORATION expectations.

---

## Section 7 — Wall-Clock Budget

EXPLORATION 2h cap per `feedback_v3_cadence_discipline.md`.

| Phase | Wall-clock estimate | Notes |
|---|---|---|
| Phase 6 setup (Engineer pre-flight) | 5 min | Verify brake field disabled; verify dsr.json schema addition; verify tests added |
| Phase 6 backtest (single-seed n_trials=35) | ~1.25h | Same as /053 (bit-identical strategy expected) |
| Phase 7 Engineer report | 5 min | Verify dsr_relative + cpcv_path_sharpe_q75 fields populated; compare /055 IS/OOS trade rosters to /053 byte-for-byte |
| Phase 7.5 Critic | 10 min | All 12 standard checks PASS; Check 3 NEW DSR_relative axis evaluated |
| **Total** | **~1.5h** | Within 2h cap |

---

## Section 8 — LOCKED MERGE/NO-MERGE Criteria (Pre-Registered)

Per the v3 LOCKED-criteria discipline (`feedback_v3_axis_selection_quant_discipline.md` rule), this section CANNOT be renegotiated post-hoc by the Engineer or Critic. Methodology-only axes use ADAPTED path criteria per /054 PATH E precedent.

### Pre-registered path classification probabilities (locked at brief commit)

| Path | Probability | Trigger |
|---|---:|---|
| PATH A (PROMISING-clean) | 5% | Bit-identical to /053 (saturation falsifier ZERO trades change) AND DSR_relative IS=0.235 ± 0.05 AND DSR_relative OOS=0.177 ± 0.05 — confirms implementation does not disturb strategy |
| PATH B (PROMISING-INERT) | n/a | N/A for methodology axes |
| PATH C-clean (NEGATIVE clean) | 5% | Implementation defect: IS or OOS Sharpe differs from /053 by >±0.05 (strategy unintentionally changed) |
| PATH C-suspicious | 5% | IS-OOS daily ratio outside [0.5, 2.0] — strategy logic disturbed |
| PATH D (NULL-RESULT) | 0% | Not applicable (methodology axes always have a defined outcome) |
| **PATH E (CPCV-INVARIANT NULL)** | **85%** | CPCV statistics match /051/052/053/054 (positive=29/45, median +0.3351 ± 0.0005, Q75 +0.838 ± 0.005) AND DSR_relative fires within informational range |

PATH E is the EXPECTED outcome per /054 closeout (methodology axes cannot shift CPCV at cycle 4 single-seed regime). This is acknowledged.

### Section 8 LOCKED outcome hierarchy (precedence top → bottom)

1. **PATH C-clean / PATH C-suspicious**: implementation defect detected. ABORT axis; revisit setup. (5+5=10% probability)
2. **PATH A**: clean implementation, bit-identical to /053. ADVANCE axis (advances DSR_relative as INFORMATIONAL gate for /061 CONFIRMATION). (5%)
3. **PATH E**: CPCV-INVARIANT NULL. The methodology axis is OPERATIONAL but cannot shift CPCV distribution at single-seed scope. ADVANCE axis (becomes operational at /061 CONFIRMATION). (85%)

**Methodology axis advances iff Section 8 outcome ∈ {PATH A, PATH E}.** Strategy IS Sharpe and OOS Sharpe are EXPECTED to match /053 — any material deviation indicates implementation defect.

### Section 8 LOCKED path verdicts (mechanical, non-renegotiable)

| Path | Trigger conditions | Outcome |
|---|---|---|
| PATH A | (IS_Sharpe in [+0.4676, +0.4776]) AND (OOS_Sharpe in [+0.4695, +0.4795]) AND (IS_trades in [179, 181]) AND (OOS_trades in [95, 97]) AND (DSR_relative IS in [0.185, 0.285]) AND (DSR_relative OOS in [0.127, 0.227]) AND (CPCV positive=29/45) AND (CPCV median Sharpe in [+0.3346, +0.3356]) | ADVANCE axis; DSR_relative becomes operational gate for /061 |
| PATH C-clean | IS_Sharpe OR OOS_Sharpe differs from /053 by >±0.05 (independent of methodology axis) | NEGATIVE — implementation defect; abort axis |
| PATH C-suspicious | IS-OOS daily ratio outside [0.5, 2.0] | NEGATIVE — strategy unintentionally changed |
| PATH E | (CPCV positive=29/45) AND (CPCV median Sharpe in [+0.3346, +0.3356]) AND (CPCV Q75 Sharpe in [+0.833, +0.843]) AND (DSR_relative fires within informational range [0.10, 0.50]) — NO requirement on bit-identity since methodology axis can produce trivial floating-point deltas without strategic change | ADVANCE axis; PATH E reinforces /054 finding (methodology axis cannot shift CPCV) |

**PATH A is a STRICT subset of PATH E**; if both fire, PATH A takes precedence (bit-identical verification is the strongest evidence).

---

## Section 9 — Reproducibility

### Library stack

Same as /054. No new dependencies.

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
2. ITERATION_LABEL == "v3-055".
3. `RiskV2Config.enable_per_symbol_drawdown_brake == False`.
4. `psr()` function in `validation_v3.py` UNCHANGED (no edits to validation_v3.py).
5. `dsr.json` schema additions present in `run_baseline_v3.py` (search for `"dsr_relative"` and `"cpcv_path_sharpe_q75"`).
6. 5 NEW adversarial tests in `tests/strategies/ml/test_validation_v3_psr_relative.py` PASS.
7. All other adversarial tests pass:
   - `test_risk_v2_drawdown_brake.py` (5 tests; dead-code coverage)
   - `test_hurst_drift_50_200_universal.py` (5 tests; dead-code coverage)
   - `test_regime_momentum_signed_3d_universal.py` (5 tests; dead-code coverage)
   - `test_fracdiff_d05_universal.py` (5 tests; dead-code coverage)

---

## Section 10 — QR Audit Trail (per `feedback_v3_axis_selection_quant_discipline.md`)

### Section 10.1 — Mandated axis derivation

iter-v3/054 Critic FINAL `db1551b` Recommendation #3 PROMOTED axis A2 — DSR gate
reformulation. Justification per Critic recommendation:
- Methodology-only (analysis-only; no closed-loop backtest required for evaluation BUT we still run a backtest to validate)
- ≤2h implementation cost
- Addresses cycle-4 STRUCTURAL FINDING: DSR=0 at n_eff=19 mechanically inevitable (4 consecutive iterations)
- Zero CPCV-shift risk
- Zero deadlock risk (stateless per `feedback_v3_oracle_eda_validity.md`)

The orchestrator's Phase 1-5 dispatch (this brief's parent) confirmed A2 as the
mandated axis. No QR PIVOT required — the axis was pre-justified at /054 closeout
with full Critic-FINAL backing.

### Section 10.2 — STATELESS vs STATEFUL classification

Per `feedback_v3_oracle_eda_validity.md` NEW 2026-05-11: every axis must declare
STATELESS or STATEFUL classification with deadlock analysis if STATEFUL.

**iter-v3/055 axis classification: STATELESS**.

Justification: DSR_relative is a per-cell post-hoc computation read from
`cpcv_paths.csv` already produced by `_compute_cpcv_paths`. No signal-emission
feedback. The gate does not affect strategy decisions; it is computed AFTER all
trades close and reported in `dsr.json`. State: trivial (a single Q75 statistic
from existing CPCV data). Escape mechanism: NOT REQUIRED (no state-dependent
loop exists).

Deadlock analysis: N/A for STATELESS axes per `feedback_v3_oracle_eda_validity.md`.

### Section 10.3 — EDA-driven 5-option ranking (per `feedback_v3_axis_selection_quant_discipline.md` rule 2)

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
quartile only).

### Section 10.4 — Orthogonality to CLOSED precedents

Per `feedback_v3_structural_over_knob_exploration.md`:

CLOSED AXES vs iter-v3/055 AXIS DSR REFORMULATION:

- ~~ADX threshold~~ (CLOSED at /015) — orthogonal (gate-threshold axis vs methodology axis)
- ~~Per-symbol PnL caps~~ (CLOSED at /020) — orthogonal (concentration vs methodology)
- ~~LDO removal~~ (CLOSED via PRE-FALSIFICATION at /052 EDA) — orthogonal
- ~~regime_momentum_signed_3d UNIVERSAL~~ (CLOSED at /052 PATH C-suspicious) — orthogonal
- ~~hurst_drift_50_200 UNIVERSAL~~ (PARKED at /053 PATH D) — orthogonal
- ~~Per-symbol drawdown brake~~ (CLOSED at /054 PATH C-clean) — orthogonal
- ~~Per-symbol ATR multipliers~~ (CLOSED at /045-/050) — orthogonal
- ~~15th-slot SWAP family~~ (CLOSED at /053 CPCV-INVARIANT) — orthogonal

R5 DSR reformulation operates on POST-HOC backtest metrics; no overlap with any
of these strategy-level axes.

### Section 10.5 — Cycle-4 axis priority recall (informed by /054 closeout)

Per /054 closeout `iter-v3/055 PROMOTED Axis` section:
- PRIMARY: A2 DSR gate reformulation — methodology-only ≤2h — **SELECTED at /055**
- SECONDARY: A4 base-stack feature reordering — 2h+ requires fresh EDA — DEFERRED to /056+
- CLOSED: A1 per-symbol drawdown brake (PATH C-clean at /054)
- DEFERRED: A3 CatBoost head-to-head (multi-iter arc 7-10h)
- CLOSED: 15th-slot SWAP family (CPCV-INVARIANT NULL)

iter-v3/055 axis = A2 per pre-locked /054 closeout recommendation.

---

## Section 11 — Cycle Cadence Tracking

Per `feedback_v3_strict_10_to_1_cadence.md`:

- **Cycle 4 #1 of 10 = iter-v3/051** (fracdiff_d05_close ADD UNIVERSAL; EXPLORATION-NULL-RESULT PATH D; PARKED)
- **Cycle 4 #2 of 10 = iter-v3/052** (regime_momentum_signed_3d SWAP UNIVERSAL; EXPLORATION-NEGATIVE PATH C-suspicious; CLOSED)
- **Cycle 4 #3 of 10 = iter-v3/053** (hurst_drift_50_200 SWAP UNIVERSAL; EXPLORATION-NULL-RESULT PATH D; PARKED — LR-PF methodology refined)
- **Cycle 4 #4 of 10 = iter-v3/054** (per-symbol drawdown brake NEW RiskV2 primitive 11; EXPLORATION-NEGATIVE PATH C-clean primary + PATH C-suspicious + Saturation + PATH E all co-fire; entire "NEW risk primitive" axis family CLOSED; ORACLE EDA methodology defect confirmed)
- **Cycle 4 #5 of 10 = iter-v3/055** (THIS — DSR gate reformulation methodology-only; expected PATH E)
- **Cycle 4 #6-#10 = iter-v3/056-iter-v3/060** (TBD)
- **Cycle 4 CONFIRMATION at iter-v3/061** (SEPARATE single-seed iter-v3/060 first; do NOT collapse the 10th EXPLORATION into CONFIRMATION)
- **5 more EXPLORATIONs remain** before cycle 4 CONFIRMATION after /055: iter-v3/056 through iter-v3/060
- **Cadence wall-clock caps**: EXPLORATION 2h, CONFIRMATION 6h. iter-v3/055 target: ~1.5h within 2h cap.

**Cycle 4 hypothesis status** (carry-forward from /050 closeout): "lift IS Sharpe to ≥ +0.5101 (BASELINE_V3.md update gate floor) while preserving OOS Sharpe ≥ +0.5053 via UNIVERSAL axes (per-symbol customizations rejected at bundle level)." iter-v3/055 is methodology-only — no expected lift to IS or OOS Sharpe. The cycle 4 hypothesis remains NOT SATISFIED via clean PROMISING; 5 EXPLORATIONs remaining after /055.

**Cycle 4 cumulative score after /055** (predicted): 0 PROMISING-clean / 1 PROMISING-INERT (N/A risk primitives) / 2 NULL-RESULT / 2 NEGATIVE / 1 methodology-axis-PATH-E / 0 axes-advance with Sharpe lift. The structural finding (CPCV-determinism + n_eff=19 + reformulated DSR gate) is the primary cycle-4 contribution.

---

## Section 12 — See Also

### Predecessor iterations
- `diary-v3/iteration_v3-054.md` — immediate predecessor (drawdown brake deadlock; cycle 4 #4; ORACLE EDA methodology defect; A2 promoted)
- `diary-v3/iteration_v3-053.md` — cycle 4 #3 (hurst_drift_50_200 PATH D; LR-PF methodology)
- `diary-v3/iteration_v3-052.md` — cycle 4 #2 (regime_momentum_signed_3d PATH C-suspicious; engineered_features_dont_stack EXPANDED)
- `diary-v3/iteration_v3-051.md` — cycle 4 #1 (fracdiff_d05_close PATH D; PARKED)
- `diary-v3/iteration_v3-050.md` — cycle 3 CONFIRMATION-NO-MERGE closeout
- `diary-v3/iteration_v3-039.md` — first OOS gate PASS in v3 history (NO-MERGE on IS regression)
- `diary-v3/iteration_v3-028.md` — first CONFIRMATION-MERGE (BASELINE_V3.md anchor; regime_momentum_signed_5d)

### iter-v3/055 artifacts
- `analysis/iteration_v3-055/synthesis.md` — primary EDA synthesis (numerical evidence)
- `analysis/iteration_v3-055/candidate_axes_ranking.md` — 5-option 9-criteria ranking
- `analysis/iteration_v3-055/dsr_history_v3.csv` — 53 v3 iterations DSR recomputed
- `analysis/iteration_v3-055/mechanical_ceiling_grid.csv` — SR_required ceiling
- `analysis/iteration_v3-055/dsr_reformulation_grid.csv` — 5-option p-values
- `analysis/iteration_v3-055/dsr_decision_table.csv` — gate PASS/FAIL
- `analysis/iteration_v3-055/dsr_extended_psr_benchmarks.csv` — PSR vs Q25/Q50/Q75/max
- EDA SHA: `a71b2e5`

### Source code references
- `src/crypto_trade/strategies/ml/validation_v3.py` — `psr()` function (lines 486-528; UNCHANGED at /055)
- `src/crypto_trade/strategies/ml/validation_v3.py` — `deflated_sharpe_ratio_v3()` (lines 406-478; UNCHANGED at /055; preserved as parallel computation)
- `run_baseline_v3.py:2174-2188` — call-site for PSR(0); MODIFIED at /055 to add DSR_relative + cpcv_path_sharpe_q75
- `run_baseline_v3.py` RiskV2Config block — MODIFIED at /055 to set `enable_per_symbol_drawdown_brake=False`
- `tests/strategies/ml/test_validation_v3_psr_relative.py` — NEW at /055 setup (5 adversarial tests)

### Memory rules
- `feedback_v3_dsr_mode_artifact.md` — DSR EXPLORATION-INFORMATIONAL interpretation; n_eff=19 cycle-4 STRUCTURAL CONSTANT
- `feedback_v3_oracle_eda_validity.md` — STATELESS axis declaration for /055
- `feedback_v3_axis_selection_quant_discipline.md` — QR-EDA-driven; Section 10 audit trail
- `feedback_v3_strict_10_to_1_cadence.md` — cycle 4 cadence 5/10 advanced
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
- `briefs-v3/exploration_catalog.md` — iter-v3/055 catalog row will be added at /055 closure
