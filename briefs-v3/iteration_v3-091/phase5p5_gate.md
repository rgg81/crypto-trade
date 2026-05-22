# Phase 5.5 Gate — iter-v3/091

**OVERALL: PASS**

**Gate executed by**: QE (Phase 5.5 re-gate)
**Date**: 2026-05-17
**Branch**: iteration-v3/091
**Head SHA at gate time**: 905b6c8322dcd897d714605305f8aeeae5b73875
**Brief SHA being gated**: 9d3d525 (the re-written model-free-scoring-axis brief)
**Supersedes**: prior gate file (SHA c56c457, OVERALL=BLOCK, embargo bug)

---

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24` immutable; IS/OOS windows in absolute dates. The two distinct embargo quantities (CPCV row-count gap `XS_REQUIRED_GAP = (H+1)×N = 484`; wall-clock time embargo `(H+1)×interval_ms ≈ 7.3 days`) are explicitly distinguished and correctly formulated. The prior BLOCK's root issue is addressed in the brief text.
- Section 1 (Hypothesis): PASS — one sentence; names the mechanism (the trained `LGBMRanker` destroys a cross-sectional momentum signal the 13-feature stack is horizon-mismatched for), the lever (replace the `LGBMRanker` prediction with a parameter-free trailing-21-bar-return cross-sectional score), the predicted effect (+0.2020 IS net spread improvement) and the OOS direction; falsifiable; specific.
- Section 2 (IS-Only Evidence): PASS — two committed IS-only EDA scripts (`d4ad137` holding_horizon_eda.py corrected-embargo; `a2c3a3f` model_free_vs_ranker_eda.py). Four CSVs committed. All numbers in the brief match the committed CSV outputs (verified against M4_focused_eda_summary.csv, M1a, M1b, M2, M3 CSVs). EDA uses `(H+1)×interval_ms` corrected embargo throughout. OOS cutoff filter confirmed (`open_time < OOS_CUTOFF_MS`). No OOS rows read.
- Section 3 (Proposed Changes): PASS — see Item 1 below (build spec verification). The single edge axis and two correctness/instrumentation items are enumerated with code-line precision. The `XS_HORIZON` / `XS_HOLD_BARS` 3→21 change, the embargo bug fix, the gross-Sharpe instrumentation, the feature revert and the three integration tests are all specified implementably.
- Section 4 (Expected OOS Impact): PASS — OOS net predicted range [+0.00, +0.20] modal; OOS gross [+0.20, +0.45]; F1–F5 falsifiers at different numbers from predictions, anchored on /089's correct figures (+0.1717 gross, −0.0985 net). No /090-defective figures cited.
- Section 5 (Risk Mitigation): PASS — seven risks tabulated with IS-calibrated or a-priori mitigations; the crash-regime sensitivity is quantified (M1b −0.1039 in 2022-crash third) and the walk-forward embargo fix is present.
- Section 6 (Risk Management Design): PASS — the cross-sectional construction's risk primitives are stated (dollar-neutral, inverse-vol, vol-targeting, quintile, overlapping hold, no-trade band, HARD turnover ceiling); the v3 7-gate stack deferral is honest and consistently framed across /088/089/090/091. Section 6.1 addresses the rigor framework for a parameter-free strategy directly (see Item 3 below).
- Section 7 (Failure-Mode Prediction): PASS — five weighted outcomes (45%/22%/22%/8%/3%); the crash-regime failure path (≈22%, analogous to M1b third-2 −0.1039) is weighted higher than modal success; the Section 2.3 sub-period finding is directly reflected; forward-looking, distinct from Section 8 thresholds.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — five disjunctive taxonomy classes (SUSPICIOUS, CONSTRUCTION-FALSIFIED, CONSTRUCTION-VALIDATED-PROMISING with sub-cases 8.3-FULL and 8.3-FOUNDATION, CONSTRUCTION-PARTIAL, NULL); locked numerical thresholds; MERGE/NO-MERGE statement explicit; no-MERGE-for-EXPLORATION affirmed; BASELINE_V3.md stays v0.v3-059.
- Section 9 (Library Stack): PASS — LightGBM/Optuna/pandas/numpy declared; no new third-party dependency; three integration tests specified (model-free scoring smoke test; gross-Sharpe shared-code-path smoke test; embargo-distinction assertion test).

---

## Item 1 — Build spec precision (Section 3): PASS

The Section 3 build spec is precise enough to implement without research decisions in Phase 6. Verification:

**The scoring formula.** The brief specifies the exact score at `cross_sectional.py` ~line 1067: `score(sym) = close(sym, ts) / close(sym, ts − H·interval) − 1`, computed from `mom_wide = close_wide / close_wide.shift(XS_HORIZON) − 1.0` indexed by `(ts, sym)`. The reference implementation is named explicitly (`model_free_vs_ranker_eda.py::_model_free_bars`, committed `a2c3a3f`). The QE has a byte-exact reference. No look-ahead: `close(ts)` and `close(ts−H·interval)` are both ≤ `ts`; PnL return taken after `ts` via the existing `searchsorted(ts, side='right')`. The pre-registered `H = 21` is explicitly stated as a fixed, non-tunable constant.

**The `score_mode` parameter.** The brief specifies: `run_cross_sectional_backtest(..., score_mode: str = "trained")` default-preserving. When `score_mode == "model_free"`: the `_train_for_month` call is SKIPPED; `strategy._model` stays `None`; `scores` is the `mom_wide.loc[ts]` row; the `predicted_score` column is still written from the model-free score (so `compute_oos_rank_ic` keeps working).

**The dual-book runner.** The runner runs the backtest twice on the same panel/construction: once `score_mode="model_free"` (primary, `reports-v3/iteration_v3-091/`), once `score_mode="trained"` (reference comparator, clearly-suffixed subdirectory). Two `_write_xs_reports` calls. Precise.

**No-training path.** "In `model_free` mode the per-month `_train_for_month` call is SKIPPED" is an explicit build decision — the QE is not left to choose.

**Construction retention.** `XS_QUANTILE_FRAC = 0.20`, `XS_NO_TRADE_BAND = 0.020`, `XS_TURNOVER_CEILING = 0.138`, quintile legs, inverse-vol, vol-targeting, overlapping `H`-bar holds — all specified as RETAINED verbatim from /089.

**The `_verify_feature_columns` assertion.** `len(XS_FEATURE_COLUMNS) == 15 → == 13` is explicitly called out (Section 3.4). `expand_downside=True → False`.

**Three integration tests.** Each test is described with a concrete assertion, not just a label. No ambiguity about what "passes."

**Verdict: the build spec is complete. Phase 6 has zero research decisions to make.**

---

## Item 2 — Single-axis + the two correctness items (Section 3.5): PASS

**The single edge axis** is the cross-sectional scoring function (trained `LGBMRanker` prediction → parameter-free trailing-`H`-bar return). The brief is explicit and consistent across Sections 0.5, 1, 3.5, 6.1.

**The horizon `H = 21`** is the EDA-selected operating point of the model-free score (the trailing-return lookback IS the definition of the model-free book, not a second independent axis), pre-registered as fixed and non-tunable (Section 2.7). `XS_REQUIRED_GAP` 88→484 and `XS_HOLD_BARS` 3→21 are stated as mechanical consequences.

**The embargo bug fix (Section 3.2)** is correctly framed as a correctness item, not an edge axis. The fix is precisely specified:
- `cross_sectional.py` ~line 968: `embargo_ms = XS_REQUIRED_GAP * interval_ms` → `embargo_ms = (XS_HORIZON + 1) * interval_ms`
- `run_cross_sectional_v3.py` ~line 825 (the `_run_smoke_test` path): same fix required.
- The brief explicitly instructs the QE to "find and fix the full set of walk-forward `embargo_ms` computations."
- The CPCV row-count gap `XS_REQUIRED_GAP` is unchanged — the brief explicitly distinguishes the two quantities.
- Verification: `cross_sectional.py:968` currently reads `embargo_ms = XS_REQUIRED_GAP * interval_ms` (confirmed by `grep -n "embargo_ms" cross_sectional.py`). The bug is present in `src`; the fix is correctly specified.

**The gross-Sharpe runner artifact (Section 3.3)** is correctly framed as instrumentation:
- `_write_xs_reports` must emit `gross_monthly_sharpe` (IS + OOS) to `comparison.csv` and `dsr.json`.
- ONE shared `_monthly_sharpe(sub, pnl_col)` helper for both net and gross — same as the EDA's pattern.
- Verification: current `run_cross_sectional_v3.py::_write_xs_reports` has an internal `_monthly_sharpe(monthly_df)` that only ever sees `net_pnl` (confirmed by source inspection). The refactor is clear and correctly specified.
- The smoke test (monkeypatch the shared helper; assert both emitted values reflect the patch) is the correct integration-test approach per `feedback_v3_methodology_axis_integration_test.md`.

**No other axes are introduced.** The /090 feature revert is a revert (not a new axis); the universe is unchanged; no risk-gate changes; no labeling-parameter changes.

**Verdict: single-axis claim is sound. Both correctness items are precisely specified and framed as non-edge.**

---

## Item 3 — Rigor framework for a parameter-free strategy (Section 6.1): PASS

Section 6.1 addresses this directly. The brief states that a parameter-free trailing-return cross-sectional sort has **zero fitted parameters** (no Optuna, no seed, no feature stack, no model), that the trailing-return lookback `H = 21` is the only design choice, set to the a-priori literature weekly horizon and inside a wide smooth IS plateau. The brief explicitly reasons that CPCV/DSR/PBO/PSR are *not vacuous* for the model-free book:

- The CPCV path computation still runs on the panel (the cross-sectional results emit `cpcv_paths.csv`); the `frac_positive_paths` metric is coherent — it measures whether the book's net return is positive across the 45 combinatorially constructed IS paths. With no overfitting surface, a high `frac_positive_paths` is genuine signal stability, not optimistic artefact.
- PSR/DSR are acknowledged as near-trivial overfitting diagnostics for the model-free book (there is nothing to deflate), and the brief does not over-claim them; the operative evaluation is the falsifier taxonomy (F1–F5) and the OOS net vs /089's −0.0985.
- The brief does NOT silently ignore DSR/PBO/PSR — it acknowledges their limited information content for a parameter-free signal while keeping them as runner outputs.

The brief makes the coherent observation: for the model-free primary book these metrics are near-trivial as overfitting detectors (there is nothing to overfit). Their continued presence in the runner is correct (the reference `LGBMRanker` comparator still has an overfitting surface and benefits from DSR/PBO/PSR). The framework is applied coherently, not ignored.

**Verdict: the rigor framework is handled correctly. The brief does not silently ignore CPCV/DSR/PSR, states their near-trivial role for the model-free book, and retains them as runner outputs.**

---

## Item 4 — Horizon pre-registration: PASS

`H = 21` is explicitly pre-registered as a **fixed, non-tunable parameter** (Section 2.7 and Section 0). The brief explains why H=21 rather than the arithmetic-best H=22/23 (+0.32) — it is the literature-canonical interior point inside the wide smooth [17,25] plateau; choosing the arithmetic-max would be mild "best-of-N" IS selection the discipline discourages. This is disciplined and honest.

All inherited construction parameters are stated as RETAINED verbatim from /089, not re-tuned:
- `XS_QUANTILE_FRAC = 0.20`
- `XS_NO_TRADE_BAND = 0.020`
- `XS_TURNOVER_CEILING = 0.138`
- The 22-symbol `XS_UNIVERSE`

None of these are adjusted in /091.

**Verdict: PASS. H=21 pre-registered as fixed. All construction parameters inherited from /089, not re-tuned.**

---

## Item 5 — Regime-sensitivity caveat (Sections 2.3, 7, 5): PASS

The M1b sub-period finding (net −0.1039 in the 2021-12→2023-08 FTX/LUNA-crash IS third) is explicitly stated in:
- Section 2.3 (quantified IS result)
- Section 2.8 summary item 3 (explicit regime-sensitivity statement)
- Section 5 risk table ("Cross-sectional-momentum regime break — the load-bearing /091 residual risk")
- Section 7 (≈22% failure-mode weight on F1/F2 OOS crash-analogue regime)
- Section 1 hypothesis framing ("honestly, the IS model-free signal is regime-sensitive")

The regime-sensitivity is not buried or minimised. The brief is forthright that the OOS window's regime mix is unknown and a crash-like regime is a real, quantified failure path. This is the correct honest framing.

**Verdict: PASS. The crash-regime risk is prominently quantified, reflected in the failure weights, and not glossed over.**

---

## Item 6 — Anchors: PASS

The brief anchors falsifiers F1 and F2 on /089's correct documented figures:
- OOS gross monthly Sharpe: **+0.1717** (confirmed by /090-closeout recompute `analysis/iteration_v3-090/gross_sharpe_recompute.py`, reproduced to 4 decimals)
- OOS net monthly Sharpe: **−0.0985** (in `comparison.csv`, confirmed to 1e-14)

The /090 recomputed figures (+0.1558 gross, −0.0770 net) are cited as the most-recent reading but NOT used as falsifier anchors — the /089 documented figures are the anchors, and the brief is explicit that "the defective /090-report figures +0.5947 / +0.5398 are NEVER cited" (Section 4.1).

Cross-check: F1 gate is "OOS net monthly Sharpe ≤ /089's −0.0985"; F2 gate is "OOS gross monthly Sharpe ≤ /089's +0.1717". Both use the correct /089 anchors. The Section 8 taxonomy (8.3 and 8.4 thresholds) also reference /089's −0.0985 and +0.1717 consistently.

**Verdict: PASS. No defective /090-report figures appear as falsifier inputs. All anchors are correctly sourced.**

---

## Corrections to Prior Gate's Secondary Findings

The prior gate (BLOCK SHA c56c457) raised Secondary Finding S1: "the walk-forward produces 37−24=13 IS test months." This was incorrect. Verification against `_generate_xs_monthly_splits` source (cross_sectional.py:1210): the loop is `for i in range(training_months, len(months_ordered))` where `months_ordered` is the set of distinct (year, month) pairs in the IS timestamps. The IS window spans 2020-03 to 2025-03 = 61 distinct calendar months; `range(24, 61) = 37` iterations → 37 test folds. The EDA's "IS-internal test months = 37" (line 13466 of `model_free_vs_ranker_eda_output.txt`) is correct: `_generate_xs_monthly_splits` produces one split per calendar month AFTER the first `training_months` months — each fold uses the PRIOR 24 months as training, not 24 fixed months total. The brief's "37 IS test months" is not a mislabelling; it is correct. The prior gate's S1 concern is closed.

---

## Additional Notes

**EDA number cross-check (Section 2 vs committed CSVs):**
- M4_focused_eda_summary.csv: `M1_model_free_H21_net_spread_monthly_sharpe = 0.2964` ✓ matches brief Section 2.1 and 2.8
- M4: `M2_model_free_minus_trained_35trial_net = 0.202` ✓ matches brief "+0.2020"
- M4: `M1a_fine_sweep_net_spread_min = 0.2244`, `max = 0.3226` ✓ matches Section 2.2
- M4: `M1b_subperiods_net_positive = 2/3` ✓; M1b.csv third_2 net = −0.1039 ✓ matches Section 2.3
- M4: `M3_H21_ranker_gain_pct_on_horizon_mismatched_features = 68.0` ✓ matches Section 2.5
- M2.csv: `n_monthly_models = 37` at both trial budgets ✓ consistent with the 37-fold IS walk-forward

**The model-free book's no-training path** is an engineering decision the brief fully specifies; there is no ambiguity about whether the QE should or should not call `_train_for_month` in `model_free` mode.

**The IS model-free book is embargo-independent** (trains nothing, no training window to embargo) — so the embargo fix matters only for the reference `LGBMRanker` comparator's training window. The brief states this correctly and the QE must fix it regardless (Section 3.2: "leaving a known bug in src is unacceptable").

**The prior BLOCK is resolved.** The embargo issue that caused OVERALL=BLOCK (prior gate SHA c56c457) is fully resolved in the re-written brief: (1) the correct formula `(H+1)×interval_ms` is stated in Section 0, Section 3.2 and Section 9; (2) the two distinct embargo quantities are explicitly distinguished; (3) the QE is instructed to fix both `cross_sectional.py:968` and `run_cross_sectional_v3.py:825`; (4) an integration test (the embargo-distinction assertion test) codifies the fix and prevents regression.

---

## Reasons (no BLOCK)

All 10 mandatory sections present and substantive. Items 1–6 verified above. Prior BLOCK fully resolved. The brief carries the correct evidence base, a precisely implementable build spec, honest framing of IS level and regime-sensitivity, correctly anchored falsifiers, and a coherent account of the rigor framework for a parameter-free strategy.

**OVERALL: PASS. Phase 6 may proceed.**
