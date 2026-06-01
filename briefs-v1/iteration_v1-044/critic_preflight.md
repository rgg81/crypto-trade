# Phase 6.0 Critic Pre-Flight — iter-v1/044

OVERALL: PASS

FIRST CONFIRMATION-MERGE-PORTFOLIO pre-flight under the new relative-regime-Pareto methodology. Bundle aggregator is post-hoc CSV-merge over frozen trade rosters; no new ML training path; no feature additions; no walk_forward / labeling changes. Foundation embargo (`walk_forward.py:113 train_end_ms = test_start_ms - embargo_ms`) intact. Methodology integrity is structurally protected by the architecture choice (sub-runs reuse the existing dispatch path verbatim; aggregator only operates on closed-trade CSVs post-hoc).

## Pre-Flight Checks

### Check A — Look-Ahead Audit: PASS
Bundle aggregator (`run_baseline_v1.py:1896-2362`) operates purely on closed-trade artifacts emitted by the 3 sub-runs. No data fetching, no feature computation, no model training, no labeling. Weighted-PnL aggregation per `(symbol, open_time)` cell uses only `pnl_pct` already crystallized in each component's trades.csv. IS/OOS split applied via `close_time < is_cutoff_ms` against the frozen `OOS_CUTOFF_MS` constant. No forward-data access possible.

### Check B — Dispatch: PASS
- `/044` elif branch at line 5573 precedes the catch-all (line 5785).
- `"v1-044"` in the catch-all exclusion tuple at line 5805.
- Banner `[iter-v1/044] CONFIRMATION-MERGE-PORTFOLIO ACTIVE` emitted at line 5617 (matches test #6 string).
- Bundle dispatch terminates with `sys.exit(0)` at line 5783; no fall-through to standard reporting.

### Check C — Wiring: PASS
- `--bundle-config` flag at line 2816-2830 with proper parser semantics.
- `_parse_bundle_config()` (line 2365-2412) validates: 3 known components, weight sum 1.0 ± 1e-6, malformed-token detection — matches tests 1-4.
- Bundle dispatch asserts `mode_label == "CONFIRMATION"` (line 5607).
- Sub-run argv builds correctly: `--confirmation --iteration 36 --symbols LINKUSDT,DOTUSDT --pruned-features --label-mode trend_scanning` for /036; `--iteration 43 --symbols LINKUSDT` for /043; `--baseline-mode` for baseline.
- All 3 sub-runs use `--seeds {arg} --n-trials {arg} --ensemble-size {arg}` from the parent invocation — uniform spec across components.
- Sub-run failures (non-zero rc) propagate via `sys.exit(rc)` at line 5722. No silent failure.

### Check D — Configuration: PASS
Launch invocation per Phase 5.5 gate: `--bundle-config "baseline:0.50,v1-036:0.30,v1-043:0.20" --seeds 2 --n-trials 35 --ensemble-size 5 --confirmation --iteration 44`. Matches v1 CONFIRMATION standard (2 outer × 5 inner = 10 effective models/cell). NOTE: brief Section 5 declares `--seeds 2 --n-trials 35 --ensemble-size 5`; brief Section 0.6 / Section 2.5 use these to compute the bundle-level σ_R proxy. Spec verified in sub-run argv construction.

### Check E — Test Suite: PASS
`tests/test_iteration_v1_044.py` contains all 12 mandatory tests + foundation regression test (13 total). Tests 1-4: `_parse_bundle_config` (valid + 3 error paths). Tests 5-6: dispatch source-string presence. Tests 7-8: aggregator weight semantics (renorm + all-active). Tests 9-12: schema validation for `comparison.csv`, `regime_attribution.csv`, `per_component_correlation.csv`, `component_substitution.csv`. Foundation test asserts `train_end_ms = test_start_ms - embargo_ms` AND explicit negative assertion against buggy form. Schema requirements match the new-skill checklist §Phase 6 schema spec.

### Check F — Anti-Pattern A1-A14 Static Scan: PASS
- A1 (`train_end_ms = test_start_ms` without subtraction): verified `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` (unchanged by this diff).
- A2 (forward-window σ_t): no labeling changes in diff.
- A3 (`fit_transform` on combined train+test): no scaler use in bundle aggregator; aggregator is pure pandas CSV merge.
- A7 (parquet append-without-clearing): bundle outputs use `to_csv(...)` overwrite semantics; no append paths.
- A8 (stateful gate deadlock): no risk-gate code changes.
- A12 (DSR/PSR granularity): aggregator does not compute DSR/PSR; comparison.csv emits monthly_sharpe only (DSR demoted to INFO per new methodology Section D).
- A13 (read-before-write): `bundle_aggregator()` writes `comparison.csv`, `regime_attribution.csv`, `per_component_correlation.csv`, `component_substitution.csv` in sequence; no in-function reads of files-not-yet-written. Sub-run dispatch reads component dirs AFTER their respective sub-processes return rc==0 — strict temporal ordering.
- A14+ not yet catalogued.
Zero unexplained matches.

### Foundation Regression: PASS
`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` (verified via Grep). No QE commits in this diff touch `walk_forward.py`, `labeling.py`, `lgbm.py`, or `optimization.py`. The iter-v3/058 fix (cherry-picked at `e149e9d`) is preserved.

### Cadence + Axis Sanity: PASS
- Phase 5.5 gate OVERALL=PASS confirmed at `briefs-v1/iteration_v1-044/phase5p5_gate.md` (RETRY-2 after 3 prior BLOCKs resolved).
- TYPE=CONFIRMATION-MERGE-PORTFOLIO; Section 0.6 rotation status N/A (CONFIRMATION; rotation discipline applies to EXPLORATIONs only) — correct per skill.
- 10/10 cycle-5 EXPLORATIONs satisfied at /043 closeout (catalog roster verified).
- LM Master Phase 4.5 advisor `briefs-v1/iteration_v1-044/lgbm_advisor.md` present with 3 numbered recommendations; brief Section 11.4.5 adjudicates each (ADOPTED / MODIFIED / REJECTED with reasoning).

### Falsifier Presence: PASS
Brief Section 4 (F-AXIS #1-#5) has explicit pre-registered falsifiers:
- F-AXIS #1: per-regime Pareto-dominance bands quoted numerically per regime (bull ≥ −2.28, bear ≥ +1.28, chop ≥ +3.23, vol-spike ≥ −0.46).
- F-AXIS #3: predicted bundle per-regime bands with "≥ 2 of 4 named regimes MUST fall in their predicted band" trigger.
- F-AXIS #4: component substitution test with explicit drop hypotheses.
Section 8 routes outcomes: MERGE / PARTIAL-MERGE / NO-MERGE / BLOCK-FINAL / BLOCK-PENDING-FIX. Section 9 pre-registers 3 failure modes with the F-AXIS catching each.

### New-Methodology Checks

**Mini-Check K (bundle aggregator outputs schema)**: PASS.
- `comparison.csv` columns `{metric, in_sample, out_of_sample, ratio}` (line 2149-2180) match test 9.
- `regime_attribution.csv` columns `{regime_tag, in_sample, candidate_sharpe, candidate_max_dd, candidate_trade_count, baseline_sharpe, baseline_max_dd, baseline_trade_count}` produced via shared `build_regime_attribution_csv()` helper (line 2217-2223) — verified against test 10 and new-skill schema.
- `per_component_correlation.csv` columns `{pair, daily_pnl_corr, trade_jaccard}` (line 2275-2281) match test 11; produces exactly 3 pairs (P0×P1, P0×P2, P1×P2) via `i<j` enumeration (line 2244).
- `component_substitution.csv` columns `{dropped_component, oos_sharpe_delta, bundle_oos_sharpe, oos_monthly_sharpe_without, ...}` (line 2323-2351) match test 12; produces 3 rows (one per drop scenario).

**Mini-Check L (wall-clock viability)**: PASS-with-flag.
Brief Section 6 predicts 3.5-4h wall-clock; LM Master predicts modal 4.5h / p90 5.5h. Hard cap 6h. Sub-runs are sequential subprocess calls — bundle aggregator at ~5 min is post-hoc. Margin: 0.5-2.5h. ACCEPTABLE under 6h cap; FLAG: if /044-baseline sub-run alone exceeds 4h (5-cohort 5-symbol n_trials=35 ensemble_size=5 seeds=2 is heavier than historical 3h estimate), engineering_report.md should document.

**Deterministic Weights**: PASS. Weights hard-coded via `--bundle-config` CLI value; `_parse_bundle_config()` parses verbatim; `bundle_aggregator()` validates `abs(total_weight - 1.0) > 1e-6` and raises. NO OOS-tuning of weights. NO grid-search code path. Section 3.1 documents Pareto-coverage derivation.

## Approved Launch Invocation
