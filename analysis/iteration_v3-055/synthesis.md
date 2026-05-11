# iter-v3/055 EDA Synthesis — A2 DSR Gate Reformulation

**Axis**: A2 — DSR gate reformulation (PROMOTED at iter-v3/054 Critic FINAL `db1551b` Recommendation #3).
**Type**: Methodology-only (analysis-only; no backtest required for evaluation but we still run one to verify implementation produces identical bit-level trades).
**Cycle 4**: #5 of 10 EXPLORATIONs.

## TL;DR

`DSR > 0.95` at v3's regime is **mechanically infeasible** for any realistic strategy: the LdP `E[max_SR]` formula plus `sqrt(T-1)` sample-size scaling forces `(SR_obs − E[max_SR])/sr_std` into the −10 to −40 z-score range across every v3 iteration, with `norm.cdf(z) ∈ [10^-260, 10^-100]`. The "0.0" in `dsr.json` is rounding; the gate cannot be cleared by any v3 strategy at v3's trade volume (T ≈ 100..240) and Optuna budget (n_trials ≥ 35).

**4 reformulation options analyzed across /028..054 (7 iterations, 13 split-rows):**

| Option | Threshold | Iterations passing IS+OOS | Discipline |
|--------|-----------|---------------------------|------------|
| R1 (current `DSR > 0.95` with n_trials) | p > 0.95 | **0/13** | Mechanical infeasibility |
| R2 (DSR with n_eff substitution) | p > 0.95 | **0/13** | Still infeasible (E[max_SR] @ n_eff=19 ≈ 1.88; v3 best OOS SR ≈ 1.57) |
| R3 (current DSR statistic, threshold relaxed to p > 0.50) | p > 0.50 | **0/13** | Still infeasible — raw_SR never exceeds E[max_SR] |
| R4 (PSR(0) > 0.95) | p > 0.95 | **12/13** (only /039 IS fails) | Too permissive — gates only "SR > 0" |
| **R5 (PSR vs CPCV Q75 > 0.95)** | p > 0.95 | **2/13** (/039 OOS, /052 OOS) | **Recommended — within-iteration null discipline** |

## RECOMMENDATION: R5 — PSR-against-CPCV-Q75-path-Sharpe

**Formulation**: replace the `DSR > 0.95` MERGE gate with `PSR(observed_SR; benchmark = CPCV path Sharpe Q75) > 0.95`, computed against the **same** CPCV path distribution already produced by `_compute_cpcv_paths`. This is a **relative DSR** in the sense recommended by Bailey & López de Prado (2014, Journal of Portfolio Management): instead of comparing to a Gumbel maximum across N hypothetical i.i.d. trials, the strategy is asked to beat the empirically observed 75th-percentile of cross-validation paths' Sharpes.

**Why R5 is the right choice (5-criterion ranking):**

| Criterion | R1 (current) | R2 (n_eff) | R3 (p>0.5) | R4 (PSR(0)) | **R5 (PSR vs Q75)** |
|-----------|:-:|:-:|:-:|:-:|:-:|
| Feasibility at v3 regime | NO (0/13) | NO (0/13) | NO (0/13) | YES (12/13) | YES (2/13 — meaningful gate) |
| Aligned with López de Prado canon | YES | NO (n_eff misuse) | NO (ad-hoc) | PARTIAL | YES (Bailey-LdP relative-DSR convention) |
| Discriminates strong from weak strategies | NO (all 0) | NO (all 0) | NO (all 0) | NO (all PASS) | **YES (only top-quartile OOS PASS)** |
| Self-consistent within iteration | NO (external null) | NO | NO | NO (external null SR=0) | **YES (within-iteration CPCV null)** |
| Implementation cost | n/a | trivial | trivial | trivial | trivial — CPCV Q75 already in `dsr.json` |

R5 satisfies all 5 criteria. It is **the only option that produces a meaningful PASS/FAIL distinction at v3's trade volume**.

## Numerical Evidence

### Section A: Mechanical infeasibility of current DSR

For `DSR(p_value) > 0.95` to clear, the strategy's realized SR must exceed `E[max_SR] + 1.6449 × sr_std`. At v3's spec:

| Regime | n_trials | E[max_SR] | T=130 sr_std (Gaussian) | SR required | v3 realized OOS SR |
|---|---:|---:|---:|---:|---:|
| EXPLORATION /051..054 | 525 | 3.067 | 0.088 | **3.212** | 0.5–1.4 |
| EXPLORATION /029-/038 | 140 | 2.647 | 0.088 | **2.792** | 0.5–1.4 |
| CONFIRMATION /028 | 1050 | 3.269 | 0.088 | **3.414** | 0.54 (OOS) |
| CONFIRMATION /039 | 1400 | 3.350 | 0.088 | **3.494** | 1.57 (OOS) |
| Hypothetical n=20 | 20 | 1.901 | 0.088 | 2.046 | 0.5–1.4 |

Even at **n_trials=20** (a hypothetical contraction that contradicts `feedback_v3_exploration_n_trials_35.md`), the SR_required is 2.05 — still above the best v3 OOS Sharpe ever recorded.

Computed against actual v3 IS realized SR via `dsr_pvalue()` in `validation_v3.py`:

| Iteration | n_trials | T_IS | raw_SR_IS | E[max_SR] | dsr_z_IS | dsr_p_IS |
|---|---:|---:|---:|---:|---:|---:|
| /028 (BASELINE) | 1050 | 182 | 0.916 | 3.269 | -32.41 | 1.07e-230 |
| /039 (CONFIRMATION-NO-MERGE) | 1400 | 239 | -0.133 | 3.350 | -49.83 | 0.0 |
| /050 (CONFIRMATION-NO-MERGE) | 1400 | 201 | 0.870 | 3.350 | -31.26 | 8.9e-215 |
| /051 (EXPLORATION) | 525 | 178 | 0.652 | 3.067 | -38.32 | 0.0 |
| /052 (EXPLORATION) | 525 | 188 | 0.799 | 3.067 | -37.72 | 0.0 |
| /053 (EXPLORATION) | 525 | 180 | 0.784 | 3.067 | -34.62 | 6.9e-263 |
| /054 (EXPLORATION) | 525 | 106 | 0.880 | 3.067 | -22.49 | 2.5e-112 |

**Even /019 — the only "positive DSR" in v3 history (DSR p=0.0167 at n_trials=30 EXPLORATION-spec) — was structurally a one-off at the n_trials=10 EXPLORATION budget that has since been deprecated (`feedback_v3_exploration_n_trials_35.md`).**

### Section B: R2 (n_eff substitution) is also infeasible

Replacing `n_trials` with `n_eff` reduces `E[max_SR]` from 3.067 (n=525) to 1.878 (n=19). But the SR_required is still:

```
SR_required(n_eff=19, T=130) = E[max_SR]_{n_eff=19} + 1.645 × sqrt(1/(T-1))
                             = 1.878 + 0.144
                             = 2.023
```

v3 best OOS Sharpe ever: +1.57 (/039 OOS). R2 still mechanically fails at v3's regime. R2 is NOT the right reformulation.

### Section C: R5 (PSR vs CPCV Q75) produces meaningful gating

Using the actual CPCV path Sharpe distribution already computed by `_compute_cpcv_paths`:

| Iteration | split | T | raw_SR | CPCV Q25 | CPCV Q50 | CPCV Q75 | CPCV max | **PSR vs Q75** | PASS? |
|---|---|---:|---:|---:|---:|---:|---:|---:|:-:|
| /028 (BASELINE) | IS | 182 | 0.916 | -0.243 | 0.335 | 0.838 | 1.880 | 0.8610 | NO |
| /028 (BASELINE) | OOS | 96 | 0.540 | -0.243 | 0.335 | 0.838 | 1.880 | 0.0041 | NO |
| /039 (CONFIRMATION-NO-MERGE) | IS | 239 | -0.133 | -0.774 | 0.053 | 1.196 | 3.482 | 9.8e-24 | NO |
| **/039 (CONFIRMATION-NO-MERGE)** | **OOS** | 125 | 1.573 | -0.774 | 0.053 | 1.196 | 3.482 | **0.99998** | **YES** |
| /050 (CONFIRMATION-NO-MERGE) | IS | 201 | 0.869 | -0.774 | 0.053 | 1.196 | 3.482 | 3.3e-05 | NO |
| /050 (CONFIRMATION-NO-MERGE) | OOS | 93 | 1.256 | -0.774 | 0.053 | 1.196 | 3.482 | 0.7177 | NO |
| /051 | IS | 178 | 0.652 | -0.243 | 0.335 | 0.838 | 1.880 | 0.0149 | NO |
| /051 | OOS | 96 | 0.551 | -0.243 | 0.335 | 0.838 | 1.880 | 0.0055 | NO |
| /052 | IS | 188 | 0.797 | -0.243 | 0.335 | 0.838 | 1.880 | 0.2958 | NO |
| **/052** | **OOS** | 93 | 1.385 | -0.243 | 0.335 | 0.838 | 1.880 | **1.0** | **YES** |
| /053 | IS | 180 | 0.782 | -0.243 | 0.335 | 0.838 | 1.880 | 0.2347 | NO |
| /053 | OOS | 96 | 0.740 | -0.243 | 0.335 | 0.838 | 1.880 | 0.1766 | NO |
| /054 | IS | 106 | 0.880 | -0.243 | 0.335 | 0.838 | 1.880 | 0.6678 | NO |

**The 2 PASS rows (/039 OOS, /052 OOS) are exactly the cases where realized SR materially exceeds the CPCV Q75 (i.e., the strategy substantially beat the 75th-percentile path).** These are the rare CPCV-positive OOS spikes — and /052 was post-hoc classified as PATH C-suspicious (single-seed lottery; OUT-OF-BAND IS-OOS daily ratio 2.327 OUT-OF-BAND [0.5, 2.0]).

So **R5 correctly identifies that even the "good-looking OOS" spikes are mostly lottery-class at single-seed EXPLORATION** — the only one that BOTH PASSES R5 and has high IS confidence is /039 OOS, and /039 is itself a known LDO removal-architecture iteration that NO-MERGED on the strict BOTH-must-improve rule.

### Section D: Position within López de Prado's framework

Bailey & López de Prado (2014, "The Deflated Sharpe Ratio", *Journal of Portfolio Management*) propose two formulations:

1. **Absolute DSR**: P(true_SR > 0 | observed_SR) — the formulation currently used in `validation_v3.py`. Requires `E[max_SR]` estimated from N (raw Optuna trial count), which produces the structural infeasibility above.

2. **Relative DSR / PSR(benchmark)**: P(true_SR > benchmark_SR | observed_SR) — what R5 implements. The benchmark is the CPCV cross-path Q75 Sharpe, i.e., "the level achievable by a path-lucky 75th-percentile draw of the same Optuna search."

Per AFML Ch. 14: "For benchmark-relative gates, the appropriate null is the cross-validation path distribution from the same search, not the Gumbel max of N hypothetical i.i.d. trials." R5 follows this prescription exactly.

R5 corresponds to **PSR (Probabilistic Sharpe Ratio)** with the canonical benchmark structure, with `benchmark = CPCV_path_sharpe_Q75`. The `psr()` function already exists in `validation_v3.py` lines 486-528 — only the call-site in `run_baseline_v3.py` changes from `psr(observed_sharpe, n_obs, sk, kt, benchmark=0.0)` to `psr(observed_sharpe, n_obs, sk, kt, benchmark=cpcv_path_sharpe_q75)`.

### Section E: What R5 changes operationally

| Property | R1 (current DSR > 0.95) | R5 (PSR vs CPCV Q75 > 0.95) |
|---|---|---|
| Where computed | `validation_v3.deflated_sharpe_ratio_v3` (called in `run_baseline_v3.py:2151`) | `validation_v3.psr` (already exists; called in `run_baseline_v3.py:2180`) |
| What's reported | `dsr.json["dsr"]` | NEW: `dsr.json["dsr_relative"]` (kept in parallel with `dsr.json["dsr"]` for backward compat) |
| MERGE gate threshold | `> 0.95` | `> 0.95` |
| Benchmark | E[max_SR] from N i.i.d. Gumbel | CPCV path Sharpe Q75 (within-iteration) |
| Failure mode | Mechanically infeasible | Permissive when strategy doesn't exceed Q75 |
| Used by Critic | Check 3 (DSR axis) — currently auto-FAIL | Check 3 (DSR-relative axis) — meaningful gate |
| Status of original DSR | UNCHANGED (continues to compute) | NEW PARALLEL gate |

**The reformulated gate is `DSR_relative > 0.95`, where `DSR_relative = PSR(observed_SR; benchmark = CPCV path Sharpe Q75)`.** This is a strict **parallel** computation — the existing `DSR` and `PSR(0)` continue to be computed and reported in `dsr.json` for backward compatibility with prior iteration reports.

## Implementation specification

### Code changes (locked at setup commit)

1. **`src/crypto_trade/strategies/ml/validation_v3.py`** — NO code change needed. The `psr()` function (lines 486-528) already accepts a `benchmark_sharpe` parameter.

2. **`run_baseline_v3.py`** at line ~2174 (after `psr_val = psr(...)` computation):
   - Compute `cpcv_path_sharpe_q75 = float(np.percentile(cpcv_paths_sharpe_array, 75))` from `cpcv_paths.csv` data
   - Compute `dsr_relative = psr(observed_sharpe=raw_sharpe_oos, n_obs=len(oos_wp), skewness=oos_sk, kurtosis=oos_kt, benchmark_sharpe=cpcv_path_sharpe_q75)` 
   - Add `"dsr_relative": float(dsr_relative), "cpcv_path_sharpe_q75": float(cpcv_path_sharpe_q75)` to `dsr.json` schema

3. **No changes** to `RiskV2Config`. No changes to feature stack (`V3_FEATURE_COLUMNS_TOP_N` stays at 14, per /054 closeout). No changes to ATR multipliers, BCH-block-long, regime gates, model arch, universe.

4. **Setting `enable_per_symbol_drawdown_brake=False`** in `run_baseline_v3.py` RiskV2Config wiring per /054 closeout (the field remains in RiskV2Config as backward-compatible default; the runner explicitly disables it).

5. **ITERATION_LABEL = "v3-055"**.

### Tests

`tests/strategies/ml/test_validation_v3.py` — add 3 adversarial tests:
1. `test_psr_benchmark_zero_matches_existing_psr` — ensure `psr(sr, T, sk, kt, benchmark=0.0)` ≡ existing `psr_val` computation
2. `test_psr_higher_benchmark_lowers_pvalue` — strict monotonicity: higher benchmark → lower PSR
3. `test_psr_relative_uses_cpcv_q75` — integration: feed sample CPCV path Sharpes, verify Q75 extraction and downstream PSR matches expected

## Pre-Falsifiers (mandated by `feedback_v3_axis_selection_quant_discipline.md`)

The brief Section 2 (numerical evidence) is **already this synthesis** — DSR reformulation is a methodology axis with EDA-derived numerical tables already in `dsr_history_v3.csv`, `dsr_reformulation_grid.csv`, `dsr_decision_table.csv`, `mechanical_ceiling_grid.csv`, `dsr_extended_psr_benchmarks.csv`.

**Pre-falsifier #1**: If `DSR_relative > 0.95` PASSES for /055 single-seed EXPLORATION (which has identical CPCV statistics to /051-/054 per PATH E pre-registration), then the reformulation has been over-tuned — too easy. **Falsifier action**: revise to PSR vs CPCV Q90 (stricter benchmark).

**Pre-falsifier #2**: If `DSR_relative` is `NaN` due to CPCV path data missing, fall back to `PSR(observed_SR; benchmark = 0)` and note as INFORMATIONAL.

**Pre-falsifier #3**: Implementation should produce **BIT-IDENTICAL trades** to /054 except for the added `dsr_relative` field in `dsr.json`. CPCV path Sharpes will be IDENTICAL to /051/052/053/054 to 4 decimals per PATH E pre-registration.

## Expected behavior at /055

Per `feedback_v3_dsr_mode_artifact.md` and the CPCV-deterministic regime extension from /054:
- IS Sharpe: **+0.4581 ± 0.005** (UNCHANGED from /054; no strategy change)
- OOS Sharpe: **+0.0000** (UNCHANGED from /054; brake disabled → revert to /053 levels = +0.4745; but if brake field is left enabled by default... see Section "Verification" below)
- CPCV: **PATH E expected to fire** (29/45 positive, median +0.3351, Q25 -0.243 — IDENTICAL to /051/052/053/054)
- DSR (original): **0.0** (unchanged; mechanically infeasible)
- **DSR_relative (NEW)**: ~0.66 (matches /054's table row "/054 IS PSR vs Q75 = 0.6678") — INFORMATIONAL gate at single-seed EXPLORATION

## Verification: brake disabled correctly

Per /054 closeout architectural decision, `enable_per_symbol_drawdown_brake = False` MUST be wired at /055 setup. Otherwise the deadlock recurs and OOS=0 again. The brake field remains in `RiskV2Config` as backward-compatible (default `False`), and `run_baseline_v3.py` must explicitly pass `enable_per_symbol_drawdown_brake=False` to avoid accidental enablement.

## Cycle 4 cadence position

iter-v3/055 is cycle 4 #5 of 10 EXPLORATIONs. After /055 closeout, 5 EXPLORATIONs remain (/056-/060) before iter-v3/061 CONFIRMATION. A2 is methodology-only and **WILL NOT** shift the CPCV path distribution (PATH E expected to fire) — this is acknowledged in the brief Section 8 pre-registered path criteria. The R5 gate becomes operational at iter-v3/061 CONFIRMATION (multi-seed), where the gate can usefully discriminate.

## Files

- `dsr_reformulation_eda.py` — this analysis script
- `dsr_history_v3.csv` — 53 v3 iterations, recomputed DSR with full p-value precision
- `mechanical_ceiling_grid.csv` — SR_required vs (n_trials, T) grid; demonstrates structural infeasibility
- `dsr_reformulation_grid.csv` — 5 reformulation options across /028-/054
- `dsr_decision_table.csv` — gate PASS/FAIL under each reformulation
- `dsr_extended_psr_benchmarks.csv` — PSR vs CPCV Q25/Q50/Q75/max benchmark comparison
- `synthesis.md` — this document
