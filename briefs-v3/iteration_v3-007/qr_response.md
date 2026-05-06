# QR Response to Critic — iter-v3/007

## Clarifications

### Clarification 1 — Check 4 IC redundancy interpretation

The brief endorses the **strict reading** (Check 4 measures NEWLY-ADDED feature redundancy; iter-v3/007 is a subsetting iteration, so vacuous PASS is correct). Both flagged pairs (`vwap_dev_50 × ema_spread_atr_20 = 0.875` and `vwap_dev_50 × vwap_dev_20 = 0.794`) are carry-forwards from `V3_FEATURE_COLUMNS_FULL` that survived prior Check 1+4 audits in iter-v3/001-006 — they surfaced here because the broader 34-feature set diluted the redundancy signal in earlier IC matrices. The redundancy structure WAS considered when picking N=14 vs N=10 (per `analysis/iteration_v3-007/summary.json`); N=14 was selected for diversity preservation across feature groups (5 of 8 v3 groups represented), and the iter-v3/008 CONFIRMATION brief Section 4 will document the carry-forward explicitly so future readers understand the IC pattern is structural, not introduced.

### Clarification 2 — Check 6 Pareto under single-seed

WAIVED per Section 8 criterion 9 ("NO 5-seed or 10-seed runs THIS iteration"). The cross-symbol OOS dispersion (LDO +17.7%, BCH +8.2%, TRX +3.9%, MKR -6.5%) is INFORMATIVE for iter-v3/008 brief planning but is not a Pareto-equivalent under EXPLORATION rules — under CONFIRMATION's multi-seed regime, MKR's negative contribution would matter, but EXPLORATION's goal is signal-direction discovery, not cross-symbol consistency validation. The dispersion will be recorded in iter-v3/007 diary and revisited in iter-v3/008 if CONFIRMATION proceeds.

### Clarification 3 — EXPLORATION verdict on IS Sharpe = +0.2241

QR endorses the **DISCRETIONARY reading → EXPLORATION-PROMISING with caveats**. Reasoning: (a) IS Sharpe +0.2241 is **+0.30 above iter-v3/003's -0.0746 baseline on the same 4-symbol universe** — a meaningful direction shift; (b) `--exploration` mode (n_trials=10, ENSEMBLE_SIZE=1, colsample=1.0) is structurally pessimistic vs CONFIRMATION (n_trials=50, ENSEMBLE_SIZE=5), so +0.22 is a FLOOR observation, not a representative point estimate of the top-14 subset's true IS Sharpe; (c) iter-v3/008 CONFIRMATION at the full config will mechanically test whether the floor lifts to >+0.5, and if it does not, iter-v3/008's NO-MERGE will catch it cleanly — the cost of a wrong PROMISING call here is one CONFIRMATION run (~6-12h), the cost of a wrong NEGATIVE call is abandoning a potentially valid de-noising axis. Per user direction "explore fast, then confirm findings", confirming a +0.30 direction-shift is worth the iter-v3/008 budget.

### Clarification 4 — Stale runtime banner

ITER-V3/008 CLEANUP. The mismatch (`run_baseline_v3.py:1305` comment + `:1315` print say "feature-cols=34 PASS" while the actual verifier checks `n != 14`) is cosmetic-only — code is correct, audit-trail printout is wrong. It does not affect this iteration's verdict and the engineering report explicitly documents the verifier passed. Worth fixing in iter-v3/008's first commit (parametrize the banner against `len(V3_FEATURE_COLUMNS)` to avoid future drift), but not blocking.

## Position

**STAND BY VERDICT** with request that Round 2 final verdict resolve to `EXPLORATION-PROMISING`.

QR accepts all of Critic's preliminary findings (Checks 1, 2, 3, 5, 7, 8, 9, 10, 12 PASS; Check 4 vacuous PASS under strict reading; Check 6 WAIVED) and asks Round 2 to invoke the discretionary reading of IS Sharpe = +0.2241 per Clarification 3 — the direction-shift evidence (+0.30 above same-universe baseline) plus the structural pessimism of `--exploration` config justifies emitting `EXPLORATION-PROMISING` and forwarding to iter-v3/008 CONFIRMATION, where the +0.5 guidance threshold becomes mechanical.
