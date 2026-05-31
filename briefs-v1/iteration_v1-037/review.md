# Phase 7.5 Critic Review — iter-v1/037

OVERALL: EXPLORATION-PROMISING

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION

## QR Response Considered (Round 2 only)
Not invoked. Round 1 went straight to FINAL because no clarifications were needed — the brief's verdict matrix bands and falsifier table are sharp enough to score directly off the observed comparison.csv numbers.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
- Foundation: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`. Confirmed by grep — every match in the strategies/ml tree includes the `- embargo_ms` subtraction; no raw `train_end_ms = test_start_ms` in production code.
- New Sortino math at `optimization.py:105-163`: `pnls = np.where(y_pred == 1, long_pnls[mask], short_pnls[mask])` then `downside = pnls[pnls < 0]` and `downside.std()`. Only operates on the current validation fold's already-computed `long_pnls/short_pnls` arrays — no forward-bar slicing, no `[t:t+timeout]` window. The Sortino downside-deviation calc is a pure post-hoc filter on the SAME pnl vector the Sharpe path consumes, with no additional data source. No look-ahead.
- Regression-test coverage: `tests/test_lookahead_embargo.py` present with all 4 required tests (`test_labels_are_invariant_to_master_data_extent`, `test_demonstrates_bug_without_embargo`, `test_walk_forward_embargo_matches_cv_gap_formula`, `test_time_series_split_with_gap_excludes_correct_rows`).

### Check 2 — Embargo Width: PASS
Unchanged from baseline. `compute_embargo_candles(label_timeout_minutes=10080, interval_minutes=480) × n_symbols=5` formula intact at both `walk_forward.py:113` and the lgbm CV gap helper. Sortino swap does not touch `MonthSplit` construction.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
DSR_corrected = −21.38 (well below 0.95); PSR_monthly_vs_1 = 0.371 (below 0.95). Per TYPE=EXPLORATION rule (skill §5.1), Check 3 axis FAILs are INFORMATIONAL — not BLOCK-triggering for EXPLORATION. NOTED for the eventual cycle-5 CONFIRMATION bundle: Sortino's 4.7× PSR_vs_1 lift over baseline is the most positive multiple-testing signal in cycle-5 to date, but absolute level is still in negative-edge territory at n_trials=18 single-seed.

### Check 4 — IC Correlation: N/A
No new feature families. V1_FEATURE_COLUMNS_PRUNED unchanged from /034. ic_matrix.csv present but uninformative.

### Check 5 — ADF Stationarity: N/A
No new features. adf_test.csv present, no new rows to evaluate.

### Check 6 — Pareto Dominance: N/A
Single seed=42 EXPLORATION (per Section 2.5 NORMAL-RISK declaration). pareto_front.csv 10-seed dispersion deferred to cycle-5 CONFIRMATION. Cross-seed variance file shows std=0 (single seed) — confirms no Pareto evaluation possible.

### Check 7 — Reproducibility: PASS
- HEAD at `5a30d96` (Phase 6 setup commit on iteration-v1/037 branch).
- `--exploration --iteration 37 --n-trials 18 --pruned-features --optuna-objective sortino` matches brief Section 10.5 dispatch.
- `v1-037` present in catch-all exclusion tuple at `run_baseline_v1.py:3817` — /030 LESSON satisfied.
- Dispatch banner string + assert at line 3727 (`assert optuna_objective_arg == "sortino"`) guards against silent Sharpe fallback.

### Check 8 — Hypothesis-Implementation Alignment: PASS (with H1-mechanism dissonance flagged)
- Implementation: `compute_sortino_with_threshold` + `optuna_objective` plumbed through `optimize_and_train` → `_objective` → `LightGbmStrategy` → `run_baseline_v1.py`. All 4 files match brief Section 3.1.
- **H1 mechanism resolution (the central forensic question)**: Brief H1 claimed Sortino would "reduce LEFT-TAIL trade losses" → expected lower Max DD. Observed: OOS Max DD **43.04%** vs baseline **40.94%** = Δ **+2.10pp WORSE**. The drawdown-reduction MECHANISM is FALSIFIED.
- **BUT** brief Section 4 verdict matrix routes on OOS bundle Sharpe Δ, NOT Max DD. Observed Sharpe Δ = +0.1751 (baseline +0.6637 → /037 +0.8388), squarely inside the **PROMISING-CLEAN band** (Δ ≥ +0.10).
- Brief H1b falsifier ("Δ < +0.05 AND DD improvement ≤ -2pp") requires BOTH conjuncts; only the second fires. Falsifier does NOT trigger.
- **Resolution**: The OOS Sharpe lift comes from a DIFFERENT mechanism than H1a posited. Trade-roster Jaccard vs baseline = 0.102 across all symbols (basin migration massive — F-AXIS #3 PASS by inversion: not a silent no-op). Per-symbol per_symbol.csv shows DOT carries 78.62% of OOS PnL (+39.30%) and BTC adds +18.53% — i.e. the Sortino basin found a DOT-concentrated allocation with HIGHER per-trade variance (consistent with the larger Max DD) but BETTER mean. The lift is "right-tail concentration" not "left-tail clipping". Pre-registered hypothesis MECHANISM diverged from realised mechanism, but verdict band per Section 4 is determined by the lift metric, not the mechanism.
- F-AXIS #1 (wiring): PASS (assert in dispatch branch + dispatch banner enforced).
- F-AXIS #2 (trade floor): PASS (OOS 243 ≥ 130; IS 688 ≥ 500).
- F-AXIS #3 (basin migration): PASS (roster Jaccard 0.102 ≪ 0.5; basins demonstrably reselected).
- F-AXIS #4 (downside std shrinkage): FAIL (Max DD INCREASED — downside std proxy worsened). INFORMATIONAL per brief Section 2 wording.
- F-AXIS #5 (TP exit floor): PASS (56 portfolio OOS TPs, 7 LTC OOS TPs).

### Check 13 — Anti-Pattern Static Scan: PASS
- A1 (train_end_ms = test_start_ms): all 5 matches in src/ carry `- embargo_ms`. Foundation discipline intact.
- A2 (forward-window labeling std): N/A; labeling.py unchanged.
- A3 (scaler.fit_transform combined): grep returns no matches. Clean.
- A7 (parquet append-without-clear): grep returns no matches in optimization.py.
- A12 (DSR/PSR wrong-granularity): DSR/PSR are baseline path — unchanged from baseline's accepted granularity convention.
- A13 (report-file read-before-write): /037 added no new methodology-axis report fields.

### Check 14 — Axis Family Validation: PASS
- Brief Section 0.6 declares `loss-function` as NEW 12th family.
- Actual src/ diff touches: `optimization.py` (new Sortino + score_fn dispatch), `lgbm.py` (ctor param threading), `run_baseline_v1.py` (CLI flag + dispatch + exclusion). All changes are scoring-objective wiring — NO label changes, NO feature additions, NO risk-gate tweaks, NO universe shifts.
- Match between declared family and observed src/ diff: CLEAN. Prior 5 EXPLORATIONs (032/033/034/035/036) span 5 distinct families. Rotation discipline preserved.

## Observed Results vs Brief Verdict Matrix

| Metric | Baseline (/baseline) | /037 | Δ | Band threshold | Within band |
|---|---|---|---|---|---|
| OOS Monthly Sharpe | +0.6637 | +0.8388 | **+0.1751** | PROMISING-CLEAN ≥ +0.10 | YES |
| OOS Monthly Sortino | +0.7697 | +0.9514 | +0.1817 | — | informational |
| OOS Max DD | 40.94% | **43.04%** | +2.10pp **WORSE** | F-AXIS #4 informational | informational |
| OOS PSR_monthly_vs_1 | (~0.079 IS proxy) | 0.371 | 4.72× | — | informational |
| OOS trades | 189 | 243 | +54 | ≥ 130 floor | PASS |
| OOS TP exits | (n/a parsed) | 56 | — | ≥ 15 floor | PASS |
| OOS LTC TP exits | (n/a parsed) | 7 | — | ≥ 3 floor | PASS |
| Trade-roster Jaccard vs baseline | — | 0.102 | — | F-AXIS #3 ≤ 0.85 (Spearman proxy) | PASS |

## Verdict Cell

PROMISING-CLEAN per brief Section 4 first row. OOS bundle Sharpe Δ +0.1751 clears the +0.10 threshold. F-AXIS #1, #2, #3, #5 all PASS. F-AXIS #4 (downside std) is the ONLY failure and is informational by brief's own Section 2 wording ("at single-seed=42 EXPLORATION budget, this metric has noise floor ~±15%; report INFORMATIONAL").

**Forensic note**: this is a PROMISING-CLEAN classification by VERDICT BAND, but a PROMISING-MECHANISM-DIVERGENT classification by mechanism integrity. The Sortino basin found a DOT-concentrated higher-variance allocation, not a downside-clipped lower-variance one. This is non-trivial for cycle-5 CONFIRMATION bundling — if the Sortino lift is mechanism-orthogonal to H1a (i.e. driven by basin-lottery on a right-tail concentration rather than left-tail clipping), it may not COMPOUND with the /036 LINK+DOT trend-scan specialist as the brief's Section 4 PROMISING-CLEAN routing suggests. The cycle-5 CONFIRMATION QR should pre-register that compounding test as a falsifier, not assume orthogonality.

## Recommendations to QR

1. **Cycle-5 CONFIRMATION must multi-seed-validate the DOT-concentration finding**. Single-seed=42 produced DOT carrying 78.62% of OOS PnL — this is a concentration warning that the v3 catalog has repeatedly identified as basin-lottery signal. Re-run at 10 outer seeds before bundling Sortino into the cycle-5 closeout merge.
2. **Pre-register the Sortino × /036 stacking compounding test**: if Sortino × trend-scan-LINK+DOT specialist OOS Sharpe Δ < Sortino-alone + trend-scan-alone, the two are mechanism-COLLIDING (not orthogonal). Classify accordingly (compoundable vs strictly-accretive-decision per the v3 PROMISING-MECHANICAL precedent).
3. **Document the H1-mechanism dissonance in the diary closeout**. The brief predicted left-tail reduction; the realised mechanism is right-tail concentration. Future loss-function experiments should base mechanism predictions on per-symbol EDA of post-Optuna allocations, not pre-Optuna distribution shape.

## Path Forward (mandatory — proposed alternative axes for /039+)

Prior 5 EXPLORATION families used (from brief Section 0.6 + catalog): sample-weighting-isolation, hyperparameter-region (CONFIRMATION-blocked), feature-family, labeling, per-cohort-specialization. /037 adds loss-function as the 12th. Excluding all 6 used families, here are 3 candidate axes for /039+ from families NOT used in the prior 5:

1. **Confidence-threshold ternary architecture** — family: `prediction-architecture`. Replace the binary {long, short} class head with a ternary {long, neutral, short} head + per-symbol neutral-class threshold. Expected mechanism: explicit "no-trade" class lets the LightGBM head MODEL trade-skipping directly, rather than relying on Optuna confidence-threshold post-hoc. Orthogonal to loss-function, label, weight, feature, risk-gate axes. Brief Section 1 should pre-register the OOS-Sharpe Δ that distinguishes architectural lift from saturation.

2. **Per-symbol drawdown brake (R-primitive expansion)** — family: `risk-primitive`. ADD a 4th risk gate to the R1/R2/R3 stack: per-symbol rolling-30d-drawdown threshold that BINARILY KILLS that symbol's signal output (not proportional scaling — the v3 cycle-7 catalog has FALSIFIED proportional scaling). Calibrate threshold per-symbol on IS-only data. Targets the Sortino mechanism-failure observation: if the right-tail-concentration mechanism puts /037 at higher DD, an orthogonal DD-clip primitive could reclaim the H1-claimed downside benefit at the rule layer rather than the objective layer.

3. **Cross-asset feature carry from v3** — family: `cross-asset-feature-family`. Port one CAREFULLY-SELECTED on-chain or basis primitive from v2/v3 catalogs that does NOT appear in v1's catalog of cross-asset OHLCV (v3 closed that axis at /123). Specifically: funding-rate-vs-perp-basis spread (NOT OHLCV-derived; non-Binance-source). This expands the feature space orthogonally to the per-cohort-specialization axis and tests whether v1 has been over-anchored on price-derived features.

(All three from families NOT in the prior-5 EXPLORATIONs. None overlap with the loss-function/labeling/feature-family/per-cohort axes already explored. Critic is advisory; QR may adopt, modify, or reject.)

## BLOCK-PENDING-FIX Rerun Protocol
Not applicable. Verdict is EXPLORATION-PROMISING, not BLOCK.