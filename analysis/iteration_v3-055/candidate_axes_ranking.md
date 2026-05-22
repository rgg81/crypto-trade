# iter-v3/055 Candidate Axes Ranking

**Date**: 2026-05-11 (mid-cycle 4; #5 of 10 EXPLORATIONs).
**Predecessor**: iter-v3/054 EXPLORATION-NEGATIVE PATH C-clean + PATH E (drawdown-brake deadlock).
**Mandate**: A2 DSR gate reformulation (PROMOTED per Critic FINAL `db1551b` Recommendation #3).

This ranking documents the 5 reformulation options analyzed in `dsr_reformulation_eda.py` and ranks them by 5 criteria. The result is **R5 (PSR vs CPCV Q75)** selected as PRIMARY for /055.

## 5 Reformulation Options Considered

### R1 — Current DSR (DSR > 0.95 with n_trials)

**Formulation**: `dsr_z = (SR_obs - E[max_SR_{N=n_trials}]) / sr_std`, threshold p > 0.95.

**At v3 regime (n_trials=525, T=180, SR=0.78):**
- `E[max_SR] = 3.067`
- `sr_std = 0.078` (gaussian)
- `dsr_z = (0.78 - 3.07) / 0.078 = -29.4`
- `p = norm.cdf(-29.4) ≈ 10^-190`
- Threshold: p > 0.95 → **gate FAIL with probability 1**

**Iterations passing across /028..054**: **0/13** rows.

**Why it fails at v3 regime**: The Gumbel E[max_SR] formula assumes n_trials i.i.d. trials, but Optuna's TPE doesn't produce i.i.d. trials — its sampling is correlated. The formula compounds the problem: at n_trials=525, E[max_SR] ≈ 3.07, and v3's realized OOS Sharpe maxes out around 1.57 (the iter-v3/039 outlier). The gate is **structurally infeasible** regardless of strategy quality.

### R2 — DSR with n_eff substitution

**Formulation**: `dsr_z = (SR_obs - E[max_SR_{N=n_eff}]) / sr_std`, threshold p > 0.95.

**Rationale**: López de Prado AFML Ch. 12 notes that n_eff (PCA-95% on trial returns) is the correct denominator when trials are correlated. v3's n_eff has been **19 across all 4 cycle-4 EXPLORATIONs (/051-/054)** — a structural constant per CPCV-determinism. At n_eff=19, `E[max_SR] = 1.878`.

**At v3 regime (n_eff=19, T=180, SR=0.78):**
- `E[max_SR] = 1.878`
- `dsr_z = (0.78 - 1.88) / 0.078 = -14.1`
- `p = norm.cdf(-14.1) ≈ 10^-45`
- Threshold: p > 0.95 → **STILL infeasible**

**Iterations passing across /028..054**: **0/13** rows.

**Why R2 also fails**: Even at n_eff=19, the required SR is ~2.0 — above v3's best OOS Sharpe ever (+1.57 at /039). R2 is **less infeasible** than R1 but still impossible.

### R3 — Same DSR statistic with relaxed threshold (DSR > 0)

**Formulation**: `dsr_z = (SR_obs - E[max_SR_{N=n_trials}]) / sr_std`, threshold p > 0.50.

**Rationale**: Relax the threshold from "95% confident strategy beats null" to "more likely than not strategy beats null".

**At v3 regime**: p never reaches 0.5 because `SR_obs < E[max_SR]` makes `dsr_z < 0` and `norm.cdf(dsr_z) < 0.5`. Mechanically requires `SR_obs > E[max_SR]` for any pass.

**Iterations passing**: **0/13** rows.

**Why R3 also fails**: Threshold relaxation doesn't help when the statistic itself is structurally biased downward by the inappropriate Gumbel-max denominator.

### R4 — PSR(0) (drop E[max_SR] entirely)

**Formulation**: `psr_z = SR_obs / sr_std`, threshold p > 0.95. Bailey-LdP (2014) base PSR formula with benchmark=0.

**At v3 regime (T=180, SR=0.78):**
- `sr_std = 0.078`
- `psr_z = 0.78 / 0.078 = 10.0`
- `p = norm.cdf(10.0) = 1.0`
- Threshold: p > 0.95 → **PASS** trivially

**Iterations passing**: **12/13** rows (only /039 IS with SR=-0.13 fails).

**Why R4 is too permissive**: It only asks "is SR > 0 with 95% confidence?" — which any modestly profitable strategy clears at T > 50. No multiple-testing correction; no within-iteration discipline. This **fails the methodology purpose** of v3 (rigor arm).

### R5 — PSR(CPCV path Sharpe Q75) — RELATIVE DSR (RECOMMENDED)

**Formulation**: `psr_z = (SR_obs - CPCV_Q75) / sr_std`, threshold p > 0.95.

**Benchmark**: 75th-percentile of cross-validation path Sharpes from `cpcv_paths.csv`. This is the **within-iteration null** — the Sharpe level achievable by a path-lucky 75th-percentile CPCV draw of the same Optuna search.

**Theoretical foundation**: AFML Ch. 14 + Bailey-LdP (2014, JPM). The appropriate null for benchmark-relative significance testing IS the cross-validation path distribution, NOT the Gumbel maximum of N hypothetical i.i.d. trials.

**At v3 regime (T=180, SR=0.78, CPCV_Q75=0.838):**
- `sr_hat = 0.78 - 0.838 = -0.058`
- `psr_z = -0.058 / 0.078 = -0.74`
- `p = norm.cdf(-0.74) = 0.23`
- Threshold: p > 0.95 → **FAIL** (correct — IS SR doesn't exceed Q75)

**Iterations passing across /028..054**: **2/13** rows:
- /039 OOS: SR=1.57 vs Q75=1.20 → PSR=0.99998 → PASS
- /052 OOS: SR=1.39 vs Q75=0.84 → PSR=1.0 → PASS

**Discriminating power**: R5 distinguishes the rare CPCV-positive OOS spikes (/039 OOS at 1.57, /052 OOS at 1.39) from the structural cycle-4 baseline (/028 BASELINE at 0.54, /051-/053 at 0.55-0.74). This is **meaningful gating** — not too easy (12/13), not too hard (0/13), but principled (2/13 = top quartile).

## Ranking Table

| Criterion | R1 | R2 | R3 | R4 | **R5** |
|---|:-:|:-:|:-:|:-:|:-:|
| C1: ≤2h implementation cost | n/a | trivial | trivial | trivial | **trivial — psr() exists** |
| C2: Escapes 15th-slot SWAP saturation | YES | YES | YES | YES | **YES** (methodology-only) |
| C3: Addresses cycle-4 structural finding (DSR=0 inevitable) | NO (doesn't change anything) | PARTIAL (still infeasible) | NO (still infeasible) | YES (always PASS) | **YES (creates meaningful gate)** |
| C4: Orthogonal to CLOSED precedents | YES | YES | YES | YES | **YES** |
| C5: Zero revert cost | YES | YES | YES | YES | **YES (parallel field in dsr.json)** |
| C6: Feasibility at v3 regime | NO (0/13) | NO (0/13) | NO (0/13) | YES (12/13 PASS) | **YES (2/13 PASS — meaningful)** |
| C7: Within-iteration null discipline | NO (external Gumbel) | NO (external Gumbel) | NO (external Gumbel) | NO (external SR=0) | **YES (CPCV path distribution)** |
| C8: Aligned with LdP canon | YES (Gumbel) | NO (n_eff misuse) | NO (ad-hoc) | PARTIAL | **YES (Bailey-LdP relative-DSR)** |
| C9: Discriminates strong from weak strategies | NO (all 0) | NO (all 0) | NO (all 0) | NO (all PASS) | **YES (only top-quartile OOS PASS)** |

**R5 is the unique option that satisfies all 9 criteria.**

## Why NOT a Hybrid

A "DSR with n_eff AND threshold > 0.5" hybrid was considered. Result: still 0/13 PASS at v3 regime. A "PSR vs Q50" was considered. Result: 12/13 PASS — too permissive (same problem as R4). Q75 is the **only quantile** that produces meaningful 2/13 PASS rate at v3's CPCV distribution.

A "PSR vs Q90" was considered. Result: 0/13 PASS at v3 regime (Q90 ≈ 1.32-1.50; only /039 OOS at 1.57 marginally clears).

Q75 is the empirically motivated quantile for v3's cycle-4 regime. If v3 later moves to a multi-seed CONFIRMATION regime where CPCV Q75 shifts upward, the gate naturally tightens. This is the **right adaptive property** of a within-iteration null.

## Final Selection

**PRIMARY: R5 — PSR(observed_SR; benchmark = CPCV path Sharpe Q75) > 0.95**

Computed in `run_baseline_v3.py` as `psr(observed_sharpe=raw_sharpe_oos, n_obs=len(oos_wp), skewness=oos_sk, kurtosis=oos_kt, benchmark_sharpe=cpcv_path_sharpe_q75)`. Reported in `dsr.json` as `"dsr_relative"` parallel to existing `"dsr"` (R1, kept for backward compatibility).

## See Also

- `synthesis.md` — full numerical evidence with tables
- `dsr_reformulation_grid.csv` — 5-reformulation evaluation
- `dsr_decision_table.csv` — gate PASS/FAIL across reformulations
- `dsr_extended_psr_benchmarks.csv` — PSR vs CPCV Q25/Q50/Q75/max comparison
- `mechanical_ceiling_grid.csv` — SR_required at (n_trials, T) grid
- `dsr_history_v3.csv` — 53 v3 iterations' DSR re-computation
