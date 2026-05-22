# Phase 7.5 Critic Review — iter-v3/093

OVERALL: BLOCK — the "FROZEN /059 base book" is not frozen: the runner re-runs the /059 architecture with the wrong inner-ensemble seeds (`[42,123,456,789,1001]` instead of the /059-canonical derived seeds `[191664963,...]`), producing a base-book trade roster that is NOT bit-identical to the /059 anchor. The single-axis comparison is confounded — the regime-overlay contrast vs /059 is uninterpretable.

## Iteration Type (from Brief Section 0.5)

TYPE: EXPLORATION — cycle-4 opener, a genuine RE-ARCHITECTURE (derivatives-microstructure regime-conditioned book). Per the EXPLORATION rubric, Check 3 (DSR/PSR edge axis) is informational and does NOT trigger BLOCK; the BLOCK here is from Check 7/Check 8 (a reproducibility + hypothesis-implementation defect), which is BLOCK-triggering for an EXPLORATION because it destroys the iteration's attribution.

## Resolution of Scrutiny Items 1–4

### Item 1 — Look-ahead / leakage audit. RESOLVED — NOT a look-ahead leak. The OOS +1.78 is a base-book re-seeding artifact (Item 4 / Check 7).

I traced every leakage surface and found no contemporaneous-or-future data entering a feature or the regime gate:

- **The 13 derivatives features are strictly past-only.** `derivatives_state_v3.py`: funding z-scores use `.shift(1)` on the rolling denominator (`_zscore_past_only`, line 129); `f_sign_persist_9` shifts before rolling (line 182); basis is shifted one full bar before ALL computations (`b = basis_raw.shift(1)`, line 243); BTC cross-asset features inherit the same discipline (lines 375, 386). No feature reads bar `t`'s own contemporaneous external value into its own decision input.
- **The vol-regime label's tercile cut-points are train-window-only.** `compute_vol_regime_label` computes `fwd_vol` over all rows but takes `q33/q67` percentiles from `train_vol = fwd_vol[training_mask & fwd_vol.notna()]` (lines 268, 276–277). The classifier trains only on `mask_train` rows (`train_regime_classifier_for_month` line 363). The label's forward 21-bar window for the last training bar ends inside the 22-candle embargo zone, never inside the test month — the embargo (`train_end_ms = test_start_ms - 22·BAR_MS`, line 577) covers the 21-bar horizon.
- **The regime size multiplier uses only the past regime prediction.** `_apply_regime_overlay` (line 822) looks up `regime_multiplier` at the trade's own `open_time`; `predict_regime_proba` (line 433) consumes only `test_mask` feature rows. No forward leak in the gate.

The "OOS-soars / IS-drops" signature is real and is the textbook overfit/confound flag — but the cause is NOT a feature/label leak. It is the base-book re-seeding defect (Item 4). The regime gate fired on only 1.5% of bars (`mean stressed_fire_rate 0.0153`), so it is arithmetically impossible for the regime gate to triple the OOS Sharpe; the OOS lift comes from the differently-seeded base book drawing a different (more OOS-favorable on this single draw) trade roster.

### Item 2 — The F2/F3 falsifier-artifact gaps. RESOLVED — honestly-flagged artifact-completeness gaps; they do NOT themselves BLOCK (the NO-MERGE verdict is robust on the IS floor regardless). They DO warrant a structural Recommendation.

F2 (OOS MaxDD threshold) and F3 (OOS regime-IC) are genuinely un-evaluable against the brief's pre-registered thresholds, and the QE flagged both honestly:

- **F2** — the runner's `_max_drawdown` (line 875) returns `dd.max() * 100` where `dd` is in raw cumulative weighted-PnL units (`np.cumsum([t.weighted_pnl ...])`), yielding 1845.24. The /059 baseline reports OOS MaxDD = 34.53 as a percentage-of-book. The two are different units; the F2 threshold (`≥ 34.53%`) cannot be applied. The brief Section 4.2 specified F2 as "the core falsifier" — its un-evaluability is a real gap in the iteration's pre-registered evidence.
- **F3** — the brief specified F3 from `ic_matrix.csv` or "a dedicated regime-IC artifact." `ic_matrix.csv` is feature-to-feature Pearson IC only (`_write_ic_matrix`, line 1124 — `pooled.corr()`); no classifier-prediction-vs-vol-regime-label IC artifact exists. F3 cannot be confirmed.

Crucially, the contrast with /092 is exact and favorable to /093 on the fabrication question: at /092 the DSR/PSR gates were hardcoded `0.0` literals NARRATED in the engineering report as computed (a false provenance — the /090 defect class). Here the QE did NOT fabricate — the engineering report's F2/F3 anomaly notes explicitly state "INDETERMINATE — unit mismatch" and "cannot confirm... escalated to QR." That is honest reporting, not a /092-class fabrication. F2/F3 alone would NOT BLOCK: the iteration is NO-MERGE on the IS +0.7916 < +1.0 floor regardless of how F2/F3 resolve, and the QE's escalation is the correct disposition.

However — /090 (gross-Sharpe with an impossible anchor), /092 (DSR/PSR hardcoded placeholders), and /093 (MaxDD unit-mismatch + missing regime-IC artifact) are three consecutive iterations with a falsifier-driving-input artifact gap. The pattern warrants a structural Recommendation (below, Rec 2): every falsifier-driving input must be a correctly-unit'd, reproducible runner artifact with an integration test asserting both its existence AND its unit/granularity.

### Item 3 — DSR/PBO/PSR provenance. RESOLVED — genuine computations; the /092 anti-recurrence guard held. PASS.

The /092 BLOCK root cause does NOT recur. Verified:

- **The anti-recurrence guard is real and load-bearing.** `_verify_dsr_psr_call_sites` (runner lines 201–222) is a source-level grep preflight that raises `RuntimeError` unless `deflated_sharpe_ratio_v3(`, `psr(`, and `pbo_from_cpcv(` all appear as call-sites. It runs unconditionally in `main()` (line 1272).
- **DSR is a genuine call.** `deflated_sharpe_ratio_v3(observed_sr=oos_monthly_sharpe, num_trials=max(1, total_optuna_trials), backtest_length=n_backtest_months, ...)` (runner lines 1384–1390). The helper (`validation_v3.py:428`) is clamp-free. DSR = −5.7536 is a real trials-deflated rejection: with `n_trials = 21,875` the `E[max_SR]` haircut exceeds the observed OOS monthly SR. `dsr.json` carries `dsr_callsite` — provenance is stated.
- **PSR is a genuine call.** `psr(observed_sharpe=oos_trade_sr, n_obs=len(oos_wp), skewness=..., kurtosis=...)` (runner lines 1408–1413), trade-level SR granularity, documented in `dsr.json` `psr_callsite` + `sr_granularity`. PSR = 0.9742.
- **PBO null is an honest structural sentinel.** `pbo_from_cpcv` on a single-strategy `(n_paths × 1)` matrix yields `pbo=None`; `dsr.json` `pbo_note` states the structural reason ("CSCV requires S>1") and emits the descriptive `pbo_frac_positive_paths = 0.7778`. This is the brief's escape clause followed literally.

The DSR/PBO/PSR machinery is genuine. The /092 defect did not recur a third time. (One sub-defect noted under Check 3/Check 7 — `n_effective_trials` is fed a degenerate `(1, N)` shape and returns 1 via the early-return branch, not a real PCA; the engineering report narrates it as a PCA result. Informational-only — it feeds no gate — but it is a /092-style narration slip.)

### Item 4 — The classification / is there a BLOCK-worthy defect. RESOLVED — YES, there is a BLOCK-worthy defect, and it is NOT in items 1–3. The /059 base book is not frozen.

The brief's entire single-axis claim rests on the /059 base directional book being held bit-fixed while the regime overlay is the sole varied object. Brief Section 3.3: "the existing `v0.v3-059` per-symbol price-barrier LightGBM book — the canonical baseline book, UNCHANGED." Section 6 defense #3: "The base directional book is the proven `v0.v3-059`." The Phase 5.5 gate Item 1, Item 3, and the "Additional Observations" bullet 3 all flagged that the QE must verify in Phase 6 that the base book IS the same roster as the canonical anchor — not re-optimized. The engineering report's Configuration Diff lists the base book as "(unchanged)" and "FROZEN."

**The implementation contradicts this.** Three pieces of evidence:

1. **Wrong inner-ensemble seeds.** `_run_059_base_book` (runner line 726) hardcodes `ensemble_seeds_059 = [42, 123, 456, 789, 1001]` — the legacy literal seeds. The /059 canonical baseline runs with `_derive_ensemble_seeds(42, 5) = [191664963, 1662057957, 1405681631, 942484272, 929893137]` (`run_baseline_v3.py:101`). Different inner seeds → different `TPESampler` trajectories → different `best_params` → different trained ensembles → a different trade roster.
2. **The base book is re-run, not loaded.** `_run_059_base_book` calls `run_backtest(cfg, wrapped)` on the /093 worktree's re-fetched `data/` directory. A walk-forward LightGBM + Optuna is stochastic per training run.
3. **Empirical proof — the rosters diverge.** /059 `in_sample/trades.csv` first trade: `BCHUSDT open_time=1643587199999`. /093 `in_sample/trades.csv` first trade: `BCHUSDT open_time=1644479999999`. /059 `out_of_sample/trades.csv` contains `BCHUSDT 1744329599999`, `1746719999999`, `1748015999999` — all three ABSENT from /093's OOS roster. The /093 base-book roster is neither bit-identical to nor a subset of the /059 anchor roster.

**Why this BLOCKs.** The iteration's pre-registered comparison is "regime overlay applied to the /059 book vs the /059 book." If the base book is itself a different roster than /059, the comparison measures *base-book re-seeding noise + regime overlay*, not the regime overlay in isolation. The regime gate fired on only 1.5% of OOS bars — it is arithmetically impossible for a gate touching 1.5% of bars to move OOS monthly Sharpe from /059's +0.5791 to +1.7783. The OOS +1.20 lift and the IS −0.30 regression are dominated by the differently-seeded base book drawing a different roster — single-seed base-book lottery. The iteration cannot answer its own question because the control was not held fixed.

**On the Section 8 classification:** the SUSPICIOUS instinct is directionally right (OOS/IS 2.25, IS-regresses/OOS-soars, F5+F6 fire, DSR catastrophically negative), but the iteration cannot be cleanly FILED as SUSPICIOUS-NEGATIVE because the SUSPICIOUS taxonomy presumes the base book was frozen and the overlay is the variable — and it was not. The honest disposition is BLOCK: the result is methodologically confounded at the artifact level. The NO-MERGE outcome is not in dispute — but a confounded iteration cannot be FILED as a clean EXPLORATION-NEGATIVE; it must be re-run with the genuinely-frozen /059 roster.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
No feature or label uses contemporaneous-or-future data. All 13 derivatives features are past-only by the `.shift(1)` conventions in `derivatives_state_v3.py`. The vol-regime label's tercile cut-points are computed on the training-window subset only; the 22-candle embargo fully covers the 21-bar forward-vol label horizon. The regime size multiplier reads only the past regime prediction. The OOS-soars/IS-drops signature is attributable to the base-book re-seeding (Check 7), not a leak.

### Check 2 — Embargo Width: PASS
Required gap for the forward 21-bar vol-regime label = 22 candles; actual `EMBARGO_CANDLES = 22` (runner line 83), applied as `train_end_ms = test_start_ms − EMBARGO_CANDLES·BAR_MS` (line 577). The /059 base book inherits the `e149e9d` walk-forward fix. `_verify_embargo_intact` (runner line 185) asserts the embargo parameter is present. Both the regime classifier and the base book are correctly embargoed.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION — NOT BLOCK-triggering)
DSR = −5.7536 (threshold > 0.95 — FAIL), PSR = 0.9742 (marginal PASS), PBO = null (honest structural sentinel; `frac_positive_paths = 0.7778`). The machinery is genuine (Item 3). Per the EXPLORATION rubric, Check-3-edge FAILs are informational. Sub-defect (informational): `n_effective_trials` is fed `is_wp.reshape(1, -1)` — a degenerate `(1, N)` shape — and returns 1 via the `m.shape[0] < 2` early-return (`validation_v3.py:573–574`), NOT a genuine PCA; the engineering report Anomaly Note 4 narrates it as "PCA... identified rank 1," which is factually wrong. `n_eff` feeds no gate — informational — but it is a /092-style narration slip (also Check 7).

### Check 4 — IC Correlation: PASS
`ic_matrix.csv` present. The 13 derivatives features are a NEW family; brief Section 2.4 EDA measured max |IC| vs the price-derived V3 stack ≤ 0.321. Within-panel max off-diagonal |IC| (`f_mom_3`↔`f_accel_3` = 0.816) is an intra-family mechanically-derived pair — the `feedback_v3_engineered_feature_pivot.md` carve-out applies; the 0.70 gate governs new-vs-existing family redundancy. No cross-family pair breaches 0.70.

### Check 5 — ADF Stationarity: PASS
`adf_test.csv`: all 39 (13 features × 3 symbols) combinations stationary at p < 0.05; largest p-value 3.1e-05. The panel is z-scores, deltas, sign-persistence ratios — stationary by construction.

### Check 6 — Pareto Dominance: PASS (by inapplicability — single-seed EXPLORATION)
iter-v3/093 is a single-outer-seed (seed=42) EXPLORATION; the multi-seed Pareto front is a CONFIRMATION-stage check. No `pareto_front.csv` required.

### Check 7 — Reproducibility: FAIL — BLOCKING
The "FROZEN /059 base book" is not reproducible against the /059 canonical roster. `_run_059_base_book` (runner line 726) hardcodes `ensemble_seeds_059 = [42, 123, 456, 789, 1001]` — the legacy literal seeds — whereas /059 uses the derived seeds `_derive_ensemble_seeds(42, 5)` (`run_baseline_v3.py:101`). The base book is additionally re-run via `run_backtest` on the /093 worktree's re-fetched `data/`. Empirical confirmation: the /093 base-book roster is neither bit-identical to nor a subset of the /059 anchor (Item 4). Secondary self-consistency defect: `comparison.csv` reports IS `n_trades = 158` while `in_sample/trades.csv` carries 159 data rows. Tertiary: `comparison.csv` `max_drawdown` is emitted in raw PnL units while /059 emits a percentage — a unit regression that breaks F2. The reproducibility failures are verdict-determining; this BLOCKs.

### Check 8 — Hypothesis-Implementation Alignment: FAIL — BLOCKING
The brief registers a single axis: the regime-size overlay applied to a bit-frozen /059 base book. The implementation does not hold the base book fixed — it re-runs the /059 architecture with the wrong inner seeds on a re-fetched `data/` extent, producing a different roster (Check 7). The registered single-axis comparison is confounded by an unregistered second varied object (the re-seeded base book). With the regime gate firing on only 1.5% of bars, the OOS +1.20 lift is attributable to the base-book re-draw, not the registered overlay — the iteration tested something other than its registered single axis. Per the Check-8 rubric, this BLOCKs.

## Optional Checks 9–12

- **Check 9 — Symbol Exclusion: PASS.** `_verify_symbols` (runner lines 123–131) raises on overlap with `V3_EXCLUDED_SYMBOLS`; runs unconditionally.
- **Check 10 — Feature Isolation: PASS.** `derivatives_state_v3.py` imports only `numpy`, `pandas`, `pathlib` — zero v1/v2 feature imports.
- **Check 11 — Forming-Candle Audit: PASS.** `_verify_data_freshness` (runner lines 133–149) asserts each symbol's last `close_time` within 16h of now; runs unconditionally.
- **Check 12 — Library Version Pinning: PASS.** Brief Section 9.1 pins the stack inherited from /059; no new third-party dependency.

## Recommendations to QR

This iteration is BLOCK on a methodology root cause (the base book is not frozen). Per the v3 rule, a methodology root-cause BLOCK becomes a NEW iteration with a new brief, new code, and a new backtest — the current /093 artifact set cannot be FILED as a clean EXPLORATION-NEGATIVE because its central comparison is confounded. Process-level fixes:

1. **Genuinely freeze the /059 base book — load the roster, do not re-run the architecture.** The "frozen oracle" premise requires bit-identity with the /059 anchor roster. Re-running a stochastic walk-forward LightGBM+Optuna — at any seed list, on any `data/` extent — cannot deliver that. The re-run must read the /059 base-book trade roster directly from `reports-v3/iteration_v3-059/{in_sample,out_of_sample}/trades.csv` and apply the regime-size multiplier to those exact `weight_factor` values. A `test_base_book_roster_matches_059` integration test asserting roster bit-identity would catch this at Phase 6.

2. **Every falsifier-driving input must be a correctly-unit'd reproducible runner artifact with an integration test.** /090, /092, /093 are three consecutive iterations where a pre-registered falsifier could not be evaluated against its threshold. The runner's `_max_drawdown` must emit MaxDD in the SAME unit as the anchor (percentage-of-book, matching /059's 34.53%). The runner must emit the dedicated OOS regime-IC artifact F3 requires. Add integration tests asserting (a) `comparison.csv max_drawdown` is a percentage in a sane range, and (b) the OOS regime-IC artifact exists and is finite.

3. **Drop or repair the `n_effective_trials` surrogate, and never narrate a degenerate early-return as a computed result.** The runner feeds `n_effective_trials` a `(1, N)`-shaped array; the helper's guard returns 1 trivially. The engineering report narrates `n_eff = 1` as a PCA result — a computation that did not occur. Either build a genuine `(n_trials × n_periods)` matrix and run the real PCA, or drop the `n_eff` field and state plainly it is not computed. `n_eff` feeds no gate — an honest omission is strictly better than a fabricated PCA narrative.
