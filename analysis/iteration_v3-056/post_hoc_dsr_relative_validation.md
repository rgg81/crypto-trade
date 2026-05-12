# iter-v3/056 — Post-Hoc DSR_relative Validation

**Purpose**: Document the verified post-hoc DSR_relative = 0.5798 computation
that confirms R5 reformulation works as designed when wired correctly.
No new EDA is required for /056; this addendum validates the underlying
math against the broken /055 run.

**Parent EDA**: `analysis/iteration_v3-055/` at SHA `a71b2e5`. The 5-option
9-criterion ranking (R1..R5) and Bailey-LdP (2014) AFML Ch. 14 theoretical
foundation re-apply unchanged for /056. R5 (PSR vs CPCV Q75) remains PRIMARY.

## Source: Engineer report SHA `6dc8256`

After the /055 backtest produced the buggy `dsr_relative = 1.0` (because
`cpcv_path_sharpe_q75 = 0.0` due to the write-before-read defect), the
Engineer recomputed the value post-hoc using the in-memory CPCV data
that was available at runtime:

```
cpcv_path_sharpe_q75 (correct) = 0.8378  (np.percentile(cpcv_df["sharpe"], 75))
raw_sharpe_oos                 = 0.8591  (annualized daily OOS Sharpe from 88 obs)
n_obs                          = 88      (OOS daily PnL rows)
skewness                       = 1.0684
kurtosis                       = 5.6062

DSR_relative (correct) = PSR(0.8591; benchmark=0.8378; n=88, sk=1.07, kt=5.61)
                       = 0.5798          (FAIL; threshold = 0.95)
```

## Why this validates R5 (without re-running)

1. **PSR is monotone in `(observed_SR - benchmark_SR)`**. With observed=0.8591
   and benchmark=0.8378, `sr_hat = 0.0213` is small and positive. PSR ≈ 0.58
   is the right neighborhood for "observed Sharpe is marginally above CPCV
   path Q75 — strategy doesn't materially exceed the within-iteration null."

2. **The 0.95 gate does NOT clear** at single-seed cycle-4 baseline. This
   confirms the brief Section 2.4 prediction that "ALL recent cycle-4
   EXPLORATIONs (/051/053/054) fail to exceed Q75 — consistent with their
   EXPLORATION-NEGATIVE/NULL outcomes." iter-v3/055 strategy = bit-identical
   to iter-v3/028 single-seed=42, so its DSR_relative would naturally also
   fail the 0.95 threshold.

3. **The post-hoc 0.5798 sits ABOVE the EDA-projected /053 single-seed
   estimate of ~0.18** (brief Section 4.2). This is because:
   - EDA used /053's IS Sharpe 0.7839 with /053's CPCV Q75 0.838 → small `sr_hat`
   - The actual /055 run (= /028 single-seed=42) had OOS daily Sharpe 0.8591 vs
     Q75 0.8378 → marginally higher `sr_hat`
   The EDA's 0.18 was a directional estimate; the actual 0.58 is in the same
   "fails 0.95 gate" bucket. R5 discrimination behavior is preserved.

4. **The cycle-4 `cpcv_path_sharpe_q75 = 0.8378` matches the "PATH E
   bit-identical" structural constant** observed for 5 consecutive iterations
   (/051/052/053/054/055 all show Q75 = 0.838 to 4 decimals). The Q75 of
   45 CPCV paths is a robust within-iteration statistic.

## Recalibrated PATH A trigger band for /056 brief Section 8

Per Critic FINAL `6083b30` Recommendation #1: the /055 brief's PATH A trigger
band for DSR_relative was based on the EDA-projected ~0.18 estimate, which was
falsified by the verified post-hoc 0.5798. The /056 brief Section 8 PATH A
trigger band is recalibrated to:

| Field | /055 brief band | **/056 recalibrated band** | Justification |
|---|---|---|---|
| DSR_relative IS | [0.185, 0.285] | **[0.50, 0.65]** | Post-hoc 0.5798 sits in this band (Engineer-verified) |
| DSR_relative OOS | [0.127, 0.227] | **[0.50, 0.65]** | Same |
| cpcv_path_sharpe_q75 | n/a (/055 spec was bit-identity) | **[0.83, 0.84]** | Cycle-4 PATH E bit-identical structural constant |

All other PATH A bands (IS Sharpe, OOS Sharpe, IS trades, OOS trades, CPCV
positive paths, CPCV median Sharpe) are UNCHANGED from /055 brief, anchored
to bit-identity vs /028 single-seed=42 (which the /055 run reproduced).

## What is NOT changing for /056

- Theoretical foundation (Bailey-LdP 2014 + AFML Ch. 14): UNCHANGED
- 5-option ranking (R1..R5): UNCHANGED
- R5 PRIMARY selection: UNCHANGED
- 9-criterion scoring at SHA `a71b2e5`: UNCHANGED
- Cycle-4 baseline strategy (V3_FEATURE_COLUMNS_TOP_N=14, V3_MODELS=BCH+LDO+TRX,
  drawdown brake disabled): UNCHANGED
- Saturation falsifier (zero trade change, zero Sharpe shift vs /053-style): UNCHANGED

## What IS changing for /056 vs /055

- **Bug fix only**: `run_baseline_v3.py:2181-2196` rewritten to use
  `flat_path_sharpes` (in-memory; line 2090) or `q75` (line 2094) instead
  of reading `cpcv_paths.csv` from disk
- **6th integration test added** per `feedback_v3_methodology_axis_integration_test.md`:
  exercises the runner's `dsr.json` write block; asserts
  `cpcv_path_sharpe_q75 > 0` AND `dsr_relative != psr` when CPCV Q75 > 0
- **End-to-end smoke test pre-flight** mandated in brief Section 9 per the
  same memory rule
- Recalibrated PATH A trigger band per above table
- ITERATION_LABEL = "v3-056"

## See also

- `analysis/iteration_v3-055/synthesis.md` — primary EDA (REUSED unchanged)
- `analysis/iteration_v3-055/dsr_extended_psr_benchmarks.csv` — Q25/Q50/Q75/max
- `analysis/iteration_v3-055/candidate_axes_ranking.md` — 5-option ranking
- `briefs-v3/iteration_v3-055/engineering_report.md` — bug location + post-hoc 0.5798
- `briefs-v3/iteration_v3-055/review.md` — Critic FINAL with carry-forward mandate
- `feedback_v3_methodology_axis_integration_test.md` — new memory rule (2026-05-12)
