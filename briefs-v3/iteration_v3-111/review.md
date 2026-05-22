# Phase 7.5 Critic Review — iter-v3/111 — FINAL (single round — no clarifications requested)

OVERALL: EXPLORATION-NEGATIVE — the corrected `triple_barrier` re-test cleanly tested the CRV/AAVE/GRT/ADA universe-selection axis and the axis does not advance: IS monthly Sharpe −0.3075 (vs /060 anchor +0.8325, Δ −1.14), OOS trades 80 (vs 130 floor), OOS/IS ratio sign-inverted. The /110 label confound is genuinely fixed; the NEGATIVE is now an interpretable property of the universe, not an artifact.

## Iteration Type (from Brief Section 0.5)

TYPE: EXPLORATION (Cycle 6, EXPLORATION #2 of 10; iter-v3/120 is the mandatory CONFIRMATION).

Per the EXPLORATION protocol and `feedback_v3_dsr_mode_artifact.md`, Checks 1, 2, 4, 5, 6, 8 are scored for verdict; Check 3 (DSR/PSR/PBO edge thresholds) is informational only at the 3-seed/35-trial EXPLORATION budget.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

The only `src/` change in iter-v3/111 is `run_baseline_v3.py` (the runner correction — code commit `7dd84ee`). No file under `features_v3/`, `strategies/ml/labeling.py`, `lgbm.py`, or the RiskV2 stack was touched, so the look-ahead surface is bit-identical to the /059-validated baseline. The `e149e9d`-fixed walk-forward is in effect: every CV fold in `run.log` logs `gap=184h (22 rows)` uniformly across all 45 splits × 3 seeds × 4 symbols. The triple-barrier label path is a forward-scanning per-bar TP/SL detection loop — forward-looking by label-construction design, which is correct; leakage into the test fold is prevented by the embargo (Check 2), not by the label loop. The barrier distance uses `atr_values[idx]` indexed at the *entry* bar, knowable at that bar's close. First OOS trade `open_time` is 2025-03-29, after the immutable `OOS_CUTOFF_DATE=2025-03-24`; last IS trade is in the 2025-03 window — clean split. The reused Phase-2 EDA loader (`analysis/iteration_v3-110/_shared.py`) asserts `close_time < OOS_CUTOFF_MS` per symbol. No contemporaneous-or-future data path found.

### Check 2 — Embargo Width: PASS

Label timeout = 10080 min / 480 min per 8h candle = 21 candles. Required cross-cell gap = `(timeout_candles + 1) × n_symbols = (21+1) × 4 = 88`. `REQUIRED_GAP` is imported as 88; the `_canonical_v059` guard asserts `REQUIRED_GAP == 88`; the runner's `_verify_label_leakage_gap()` recomputes 88; `run.log` line 25 records the PASS. The per-cell walk-forward embargo is 22 candles = (21+1), applied symmetrically. Actual ≥ required, symmetric. The stale `(= (21+1)*3; ...3-sym /059 universe...)` diagnostic parenthetical that the /110 review flagged has been corrected — `run.log` line 33 now reads `Gap: 88 (= (21+1)*4; ... CRV/AAVE/GRT/ADA; ... label_mode=triple_barrier iter-v3/111 correction)`. No leakage.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION — NOT verdict-triggering)

`dsr.json`: DSR=0.0 and PSR=0.7815 (both below the 0.95 threshold); PBO=0.1094 (clears the <0.4 gate). `n_trials=420`, `n_eff=19`. Per Section 0.5 TYPE=EXPLORATION and `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR/PSR at the 3-seed/35-trial budget are structural regime artifacts, not edge-significance evidence — Check 3 FAILs do NOT trigger the verdict for an EXPLORATION iteration. DSR=0.0 is uninformative here in any case: with IS monthly Sharpe −0.3075 there is no positive in-sample Sharpe for the deflation machinery to act on. `frac_positive_paths=0.622` clears the informational 0.55 CPCV gate, but with 6 CPCV paths below −2.0 the path distribution is unstable — consistent with 3-seed EXPLORATION variance and a no-edge book. Flagged for the record; moot for verdict purposes.

### Check 4 — IC Correlation: PASS (no new feature family — not applicable)

iter-v3/111 is a universe-only axis: zero new features. `V3_FEATURE_COLUMNS` is asserted by the runner (`run.log` line 2, `feature-cols=14` pre-flight PASS) to be exactly the /059 14-feature stack. `ic_matrix.csv` is present (14×14) and shows only the known /059 intra-stack composed-feature correlations (`regime_momentum_signed_5d` vs `vwap_dev_20` 0.813, vs `sym_vs_btc_ret_7d` 0.714) — pre-existing, carved out per `feedback_v3_engineered_feature_pivot.md`, not introduced by this iteration. No new-vs-existing pair to test. PASS by non-applicability.

### Check 5 — ADF Stationarity: PASS

`adf_test.csv` on the /059-identical 14-feature stack: 2,531 / 3,136 cells stationary (80.7%, p < 0.05). The 605 non-stationary cells are dominated by early-history months with insufficient candles for the ADF regression (could-not-test sentinel, not a stationarity failure). No feature was added or modified — this is the /059 anchor stack. ADF evaluates feature stationarity (label-independent), unaffected by the labeling correction. PASS.

### Check 6 — Pareto Dominance: PASS (single-lineage EXPLORATION — multi-seed Pareto not applicable)

iter-v3/111 ran in EXPLORATION mode (`run.log` line 27: `ensemble_size=3`; seeds `[191664963, 1662057957, 1405681631]`, all `outer=42` lineage). EXPLORATION mode produces one deterministic roster; `pareto_front.csv` is correctly absent — no 10-seed Pareto front is generated or required at EXPLORATION budget. Multi-seed Pareto is a CONFIRMATION-mode concern, correctly deferred to iter-v3/120. PASS by non-applicability.

### Check 7 — Reproducibility: PASS

The engineering report stamps commit SHA `7dd84eedd07ae057228f202958bb307dcde939a7` — the runner-code commit the backtest ran against; the branch tip `8e989f1` is the docs commit that adds the report. Stamping the code-state SHA is correct. The runner passes explicit `feature_columns=list(features_for_symbol(symbol))` — never `None`; `_verify_feature_columns` asserts the 14-column stack. `ITERATION_LABEL = "v3-111"`. Inner ensemble seeds literal. PnL arithmetic spot-checked on two OOS trades — both match the file. Reproducibility properties hold.

### Check 8 — Hypothesis-Implementation Alignment: PASS

**This is the check iter-v3/110 failed. iter-v3/111's runner correction is genuinely and completely implemented — verified at source, not on the brief's or the report's assertion.**

The brief registers exactly one substantive axis (the `V3_MODELS` universe swap) plus the Critic-mandated `label_mode` correction (the iter-v3/105 revert that /106-109, all NULL-AT-EDA, never discharged). All three corrected runner properties were verified by reading the actual `run_baseline_v3.py`:

1. **Training label reverted to `triple_barrier`.** `run_baseline_v3.py:1907` — `_build_v3_model`'s `common_kwargs` carries `label_mode="triple_barrier"` (the /105 `trend_scanning` is gone; `trend_scan_grid` is no longer passed). The single edit propagates to all four symbol models via `common_kwargs`.
2. **Pre-flight assertion target corrected.** `run_baseline_v3.py:1139` — `expected_label_mode = "triple_barrier"`; the assertion block raises `RuntimeError` on anything else, and the print announces `label_mode (iter-v3/111 correction): 'triple_barrier' PASS`. This is the precise inversion of the /110 defect, where the pre-flight asserted the *stale* target and so enforced the bug.
3. **`_canonical_v059` guard extended from 11 to 13 knobs.** `run_baseline_v3.py:1044`/`:1050` add `label_mode` (canonical `triple_barrier`) and `trend_scan_grid`. The exact blind spot that let the /110 drift ride undetected for four iterations is now covered by an assertion the runner cannot bypass.

The run executed under the corrected config — corroborated independently of the source: `run.log` line 19 records `Config-accretion check ... 13 knobs verified — ALL /111-canonical (... label_mode=triple_barrier) PASS`; line 20 records `label_mode (iter-v3/111 correction): 'triple_barrier' PASS`; and the in-loop `[label]` lines show the per-bar TP/SL barrier-detection format of `triple_barrier`, not the trend-scanning format. The Configuration Diff vs /059 in the engineering report is accurate against `run.log`: exactly two substantive rows change — `V3_MODELS` (the axis) and `REQUIRED_GAP` 66→88 (the mechanical 3→4-symbol consequence). The /110 confound is genuinely absent; the universe-selection axis was, for the first time, cleanly tested.

The verdict EXPLORATION-NEGATIVE is correct on the pre-registered Section 8 criteria applied mechanically: IS monthly Sharpe −0.3075 is far below the +0.7325 NEGATIVE floor (Δ −1.14 vs the /060 anchor +0.8325); aggregate OOS trades 80 is below the 130 bundle-level trade-rate floor; the OOS/IS monthly Sharpe ratio is sign-inverted. Any one triggers NEGATIVE. The IS book is sub-breakeven by construction — 31.22% IS win rate is below the 33.3% breakeven of the 2:1 ATR barrier geometry. **One reporting defect, not a confound:** the engineering report's "Per-Symbol OOS Attribution" table conflates two distinct per-symbol PnL metrics — `net_pnl_pct` from `out_of_sample/per_symbol.csv` and `pct_of_total_pnl` — while `comparison.csv`'s per_symbol block carries a third (weighted-PnL concentration); on a near-zero OOS total weighted PnL (+3.39) all three share-denominators are numerically unstable. This does not change the verdict — every representation agrees GRT is the dominant dragger and the iteration is NEGATIVE on the trade-rate floor and the IS Sharpe regardless — but the report's per-symbol section is internally inconsistent. Recommendation, not a verdict-affecting FAIL.

## Clarifications Requested from QR — NONE

Every check is unambiguous. The runner correction is verified complete at source and corroborated by `run.log`; the EXPLORATION-NEGATIVE verdict follows mechanically from the pre-registered Section 8 criteria.

OVERALL: EXPLORATION-NEGATIVE — the corrected `triple_barrier` re-test cleanly tested the CRV/AAVE/GRT/ADA universe-selection axis; the axis does not advance (IS monthly Sharpe −0.3075 vs /060 anchor +0.8325; OOS trades 80 vs 130 floor; OOS/IS ratio sign-inverted). The iter-v3/110 `label_mode` confound is genuinely fixed — verified at `run_baseline_v3.py:1907`/`:1139`/`:1044`/`:1050` and `run.log` lines 19-20 — so this NEGATIVE is an interpretable property of the screened universe, not an artifact. The symbol-selection-by-feature-AUC-screen axis is now legitimately closed for cycle 6.

## Recommendations to QR

1. **Catalogue iter-v3/111 as the verdict that legitimately closes the symbol-selection-by-signal-screen axis for cycle 6 — not as a second confounded run.** The /110 review required the axis be recorded UNRESOLVED *pending a corrected re-run*; iter-v3/111 IS that corrected re-run, and it is clean (Check 8 PASS, verified at source). The Phase-8 diary and `briefs-v3/exploration_catalog.md` should record iter-v3/111 as "EXPLORATION-NEGATIVE — clean: the CRV/AAVE/GRT/ADA screened universe does not carry merge-grade IS or OOS edge under the corrected `triple_barrier` runner; symbol-selection-by-feature-AUC-screen axis CLOSED for cycle 6." The honest finding: the EDA's thin broad-population AUC margin (only CRV cleared the strict 3-criterion GO bar; AAVE/GRT/ADA were marginal) did not survive the production Optuna search + 7-gate stack — the IS gated proxy of +0.25 monthly Sharpe did not convert; it inverted to −0.31.

2. **Fix the engineering-report per-symbol-attribution metric conflation as a process note for future QE reports.** The /111 report's per-symbol table mixes `net_pnl_pct`, `pct_of_total_pnl`, and `comparison.csv` weighted-PnL concentration without labelling which is which. When the OOS total is near zero, every share denominator is unstable and the three representations diverge wildly. Future QE reports should pick one per-symbol PnL representation, name it explicitly, and not narrate share percentages computed on a near-zero denominator without flagging the instability.

3. **iter-v3/112 should advance to the next item on the cycle-6 structural axis menu — not a single-symbol patch of this universe.** The brief's Section 7 pre-registered AAVE-drop and ADA-drop fallbacks were predicated on one of those symbols being the clean OOS-worst; the as-run result is that GRT (not pre-registered as the primary dragger) is the dominant OOS dragger while CRV and AAVE were OOS-positive — the pre-registered fallback triggers do not cleanly fire. A drop-GRT re-test would be axis-saturation territory (a single-symbol tweak of a universe the screen already ranked, on a thin EDA margin). With symbol-selection-by-screen now closed clean, iter-v3/112 should take the next structural axis from `project_v3_cycle6_axis_menu.md` (the cycle has 8 EXPLORATION slots remaining before the iter-v3/120 CONFIRMATION), per `feedback_v3_structural_over_knob_exploration.md`.
