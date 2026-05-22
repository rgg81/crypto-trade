# Phase 7.5 Critic Review — iter-v3/077

OVERALL: MERGE

## Iteration Type (from Brief Section 0.5)

TYPE: EXPLORATION — cycle 2 #7 of 10. Axis category: PASSIVE-DIAGNOSTIC (report-instrumentation-only). Per the two-tier protocol, Checks 1, 2, 4, 5, 6, 8 are scored with full threshold enforcement; Check 3 (DSR/PSR/PBO edge axes) is informational for an EXPLORATION and does not trigger BLOCK.

This was dispatched as a single-round full review (no preliminary/QR-clarification cycle requested); the verdict below is FINAL.

## Verdict Summary

iter-v3/077 is a PASSIVE-DIAGNOSTIC EXPLORATION that emits `conditional_orthogonality.csv` and reverts /076's `range_efficiency_50` to the /060 14-feature anchor. The brief predicted a bit-identical-to-/060 roster (intended NULL-RESULT). The prediction was wrong. The QE re-classified INERT-AT-EXPLORATION. I independently verified every forensic claim against the raw trade CSVs: the IS `(symbol, open_time)` key roster IS bit-identical to /060 (159 = 159, 0 added, 0 removed); the divergence is 13 TRX IS `weight_factor` values floored at 0.5 (root cause: `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` introduced at iter-v3/061, 16 iterations after /060 — genuinely external to /077's config) plus one extra OOS LDO `end_of_data` trade and one OOS TRX `end_of_data`→`take_profit` resolution (both data-extent artifacts). No wiring defect. No look-ahead. The diagnostic deliverables (conditional-orthogonality map, reframing finding, anchor-staleness finding) are produced and sound. /077 closes as a non-advancing diagnostic iteration; the report instrumentation lands as accretive tooling.

## Foundation Audit (Boot Steps 9-11)

**Boot Step 9 — Foundation Audit: PASS.** `walk_forward.py:113` carries the post-fix state `train_end_ms = test_start_ms - embargo_ms` (purges 22 candles). `compute_embargo_candles(10080, 480) = 22`; `REQUIRED_GAP = 66 = (21+1) × 3` confirmed. `ITERATION_LABEL = "v3-077"` at `run_baseline_v3.py:128`. `OOS_CUTOFF_DATE = "2025-03-24"` and `TRAINING_MONTHS = 24` immutable (`run_baseline_v3.py:81-82`). V3_FEATURE_COLUMNS_TOP_N is exactly 14 entries; `range_efficiency_50` absent and asserted-absent (`run_baseline_v3.py:388-395`); the `efficiency_ratio_50` literal-name ban is retained (`run_baseline_v3.py:346-354`); `regime_momentum_signed_5d` present and asserted-present.

**Boot Step 10 — Regression Test Confirmation: PASS-equivalent.** Phase 5.5 gate Check 5 records `345 passed, 3 skipped` for `tests/features_v3/ tests/strategies/ml/` and `ruff` clean. Five test files updated for the 14-feature count.

**Boot Step 11 — Anti-Pattern Static Scan: PASS.** No `start_time` manipulation, no OOS-cutoff drift, no hardcoded-Sharpe injection. `V3_EXCLUDED_SYMBOLS` enforcement is present (`run_baseline_v3.py:189-193`, Check 9). Feature-isolation grep of `features_v3/` returns zero genuine cross-track imports (Check 10) — the three matches are docstring/comment lines, not `import` statements. `_write_conditional_orthogonality` (`run_baseline_v3.py:2026-2154`) is pure post-backtest report emission: called at line 2828, between `_write_feature_importance` (2823) and `_write_v3_comparison` (2830); it reads already-trained `model_pairs` and a committed EDA CSV from disk, writes one CSV, and touches no model / feature / labeling / risk-gate / Optuna / seed path.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

No feature was added in /077. The single primary axis (`_write_conditional_orthogonality`) is post-backtest report emission — it reads `inner._models[*].feature_importances_` from completed models and copies the EDA's `T3_conditional_orthogonality.csv`. It cannot introduce look-ahead because it runs after `run_backtest` returns and writes only a report CSV. The EDA's own per-month importance training (`compute_per_month_importance`, `axis_selection_eda.py:462-530`) is embargo-disciplined: `train_end_ms = test_start - embargo*_8H_MS` (22-candle purge) plus `train.iloc[: len(train) - timeout]` to drop the unformed-label tail. `build_btc_monthly_regime` applies `.shift(1)` before the rolling SMA-270 (`axis_selection_eda.py:270-271`) — past-only. The reverted `range_efficiency_50` is dead code (`compute_range_efficiency_50` still dispatched but the column is never in `V3_FEATURE_COLUMNS_TOP_N`). Clean.

### Check 2 — Embargo Width: PASS

`timeout_candles = 10080 / 480 = 21`. Required gap = `(21+1) × 3 = 66`. The runner's CV gap is 66 and the walk-forward embargo is 22 candles — both confirmed in the engineering report Label Leakage Audit and the Foundation Audit. Unchanged from /060; bit-comparable. No leakage surface added by a report-emission axis.

### Check 3 — Multiple-Testing Correction: PASS (informational for EXPLORATION)

`dsr.json`: DSR=0.0, PBO=0.1278, PSR=0.9987, `dsr_relative=2e-06`, `dsr_relative_b4=0.0512`, n_trials=315, n_eff=19. **PBO=0.1278 clears the < 0.4 threshold.** Legacy DSR=0.0 and `dsr_relative_b4=0.0512` FAIL the 0.95 threshold but are informational at EXPLORATION mode per `feedback_v3_dsr_mode_artifact.md` — `n_trials=315` (3-seed EXPLORATION) is not comparable to the CONFIRMATION-mode `n_trials=1050` against which the 0.95 threshold is calibrated; these do not trigger BLOCK for an EXPLORATION. PSR=0.9987 clears 0.95. PBO and `frac_positive_paths` (0.6444) are mechanically identical to /060 — the CPCV path-return proxy is weight-factor-independent, as the QE notes (verified: `cpcv_paths.csv` has 45 paths; `per_cell_pbo.csv` 117 cells; PBO unchanged is expected for a bit-identical-key roster).

### Check 4 — IC Correlation: PASS

`ic_matrix.csv` is 14×14, present, no `range_efficiency_50` column (correctly reverted). **/077 adds no new feature family**, so the `|IC| < 0.7` new-vs-existing gate is not triggered. The one high pair — `regime_momentum_signed_5d` vs `vwap_dev_20` at IC=0.764 — is a pre-existing baseline-stack pair carried since iter-v3/028, and `regime_momentum_signed_5d` is a composed feature for which `feedback_v3_engineered_feature_pivot.md` establishes an importance-based carve-out from the strict IC gate. Not a /077 finding; not actionable here.

### Check 5 — ADF Stationarity: PASS-equivalent

`adf_test.csv` has 2198 rows = 1803 stationary (82.0%) — consistent with the 14-feature × 3-symbol × variable-month grid and with /074-/076. The non-stationary rows are dominated by warmup months (e.g. 2020-01 all-NaN/`False` — features not yet formed), not end-of-window failures. The comparison.csv is bit-comparable to /060. The run-log `[ADF] WARNING: LDOUSDT/cusum_reset_count_200 not found in ADF output` is a stale hardcoded secondary-falsifier check (`run_baseline_v3.py:1149-1161`) for a feature that is NOT in the 14-feature stack — it is print-only with no `raise` and zero behavioral effect. Benign, as in /074-/076. (One precision note for the QR: the engineering report calls this "LDO short-history artifact"; the actual cause is that `cusum_reset_count_200` is not a current feature at all — the report's framing is imprecise but the benign conclusion stands.)

### Check 6 — Pareto Dominance: PASS-equivalent

`pareto_front.csv` is RETIRED under the unified-ensemble architecture (BASELINE_V3.md: "`pareto_front.csv` no longer produced"); the replacement is Gate 10-CPCV `frac_positive_paths ≥ 0.55`. /077: `frac_positive_paths = 0.6444` — PASS, and architecturally invariant (identical to /060). `ensemble_summary.json` confirms the 3-seed EXPLORATION roster (`191664963, 1662057957, 1405681631`, outer=42 lineage) — bit-identical mode/seeds to /060's `ensemble_summary.json`. No seed-selection concern for a bit-identical-key roster.

### Check 7 — Reproducibility: PASS

Setup commit `30cda98` stamped; HEAD at report time `50995c6`. The runner uses an explicit literal 14-feature `V3_FEATURE_COLUMNS_TOP_N` (no `None`, no auto-discovery), guarded by a `RuntimeError` on count ≠ 14. `ENSEMBLE_SEEDS` is the hardcoded lineage-preserving constant. PnL spot-check: /077 OOS line 2 (BCH short, 303.87→282.100779, wf 0.33): `pnl_pct = (303.87−282.100779)/303.87×100 = 7.164`, `net = 7.064`, `weighted = 7.064×0.33 = 2.331` — matches. Line 104 (LDO short, 0.3878→0.3808, wf 0.77): `pnl_pct = 1.8051`, `net = 1.7051`, `weighted = 1.3129` — matches. Sign convention and fee handling correct.

### Check 8 — Hypothesis-Implementation Alignment: PASS

The brief (Section 3.3) declares exactly two changes: (1) PRIMARY AXIS — `_write_conditional_orthogonality` report instrumentation; (2) MANDATORY BASELINE-RESTORE — revert /076's `range_efficiency_50`. Both are present and nothing else is: `run_baseline_v3.py` gains the `_write_conditional_orthogonality` function and its call site; `features_v3/__init__.py` `V3_FEATURE_COLUMNS_TOP_N` is back to 14; pre-flight assertions and 5 test files updated for the count. No `RiskV2Config` change, no `V3_MODELS` change, no labeling change, no scope creep. Every code change maps to a brief sentence; every brief claim has a code change.

## Special Adjudications

### Adjudication #1 — the falsified bit-identity prediction

**The QE's roster diff is independently verified.** I diffed `reports-v3/iteration_v3-077/in_sample/trades.csv` against `reports-v3/iteration_v3-060/in_sample/trades.csv` (both 159 trades) and the OOS files (103 vs 102):

- **IS `(symbol, open_time)` keys: bit-identical** — 159 = 159, 0 added, 0 removed. `in_sample/per_symbol.csv` is byte-identical between /077 and /060 (BCH 73/33/+79.4465, LDO 11/3/−11.4379, TRX 75/22/−23.0435). The 13 differing rows are all TRX `weight_factor`: e.g. row TRX `1646467199999` is wf 0.4200 in /060 → wf 0.5000 in /077 (net_pnl_pct identical −3.4260, weighted_pnl −1.4389 → −1.7130); row TRX `1659513599999` is wf 0.3600 → 0.5000. Every floored value lands at exactly 0.5; non-floored TRX rows and all BCH/LDO rows are bit-identical. `in_sample/monthly_pnl.csv` has bit-identical `trade_count` in all 33 rows but `pnl_pct` differs in 11 (because `monthly_pnl.csv` reports weighted PnL while `per_symbol.csv` reports unweighted). This is exactly the `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` mechanism.

- **Root cause confirmed external to /077.** `run_baseline_v3.py:1689-1693` carries `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` with an in-code provenance comment dating it to iter-v3/061 ("`iter-v3/061: TRX-specific vol_scale_floor=0.5 per QR EDA SHA d198b25`"); the iteration-history block at lines 229-235 independently records the /061 introduction. BASELINE_V3.md (which documents /059, pre-/061) does not list it — consistent. This is genuine 16-iteration code accretion, not a /077 setup drift.

- **OOS +1 trade confirmed a data-extent artifact.** /060's last OOS trade is TRX `1778572799999` `end_of_data` (pnl +0.2092); /077 has the SAME key resolving as `take_profit` (pnl +1.8330) plus an additional `(LDOUSDT, 1778716799999)` `end_of_data` trade (pnl +1.7051, wpnl +1.3129) that is absent from /060. Same data-extent pattern certified by the /074 and /075 Critics.

**The QE's "benign, not a wiring defect" conclusion is sound** — the IS key roster is bit-identical, and both perturbation sources are fully external to /077's config change with a complete wpnl reconciliation (A +1.3129 + B +0.8119 + C +0.5943 = +2.7191 OOS; IS −0.1616 from the TRX floor alone).

**On the falsified prediction itself: this is a process-recommendation-level brief defect, NOT a BLOCK.** The brief's Section 4.1 over-claimed ("not a confidence interval — it is an algebraic identity"), and that claim was wrong. But the SAME brief, Section 8.3, explicitly pre-registered this exact outcome shape as a LOCKED classification gate: "INERT-AT-EXPLORATION ... fires only if a benign non-determinism perturbs the roster without moving the metrics — Section 7's ≈4% tail." The brief built the classification machinery to catch its own prediction being wrong, the disjunctive evaluation order resolved cleanly to INERT, and the QE root-caused the perturbation to two fully-explained benign causes with zero residual. A BLOCK is reserved for a genuine wiring defect, a look-ahead, or an un-pre-registered failure mode — none of which is present. The defect is that the brief asserted algebraic certainty over a config it had not actually held fixed since /060; the fix is process-level (next adjudication), not a NO-MERGE.

### Adjudication #2 — the /060 anchor staleness finding

**The finding is sound.** /077 is the first iteration since /060 to run the exact /060 14-feature config with no axis, and it does NOT reproduce the frozen /060 anchor: the current-code /060-config baseline is **IS +0.8236 / OOS +0.2078**, not the frozen +0.8325 / +0.1403.

- **Code-drift component (IS):** −0.0089, entirely the iter-v3/061 TRX `vol_scale_floor` acting on 13 IS TRX trades (4 wins, 9 losses → net IS wpnl −0.1616 → monthly Sharpe −0.0089). This is a permanent, deterministic code-state difference, not noise.
- **Data-extent component (OOS):** +0.0675, dominated by the 2026-05 OOS month that post-dates /060's data fetch (data-extent A+B = +2.1248 wpnl; the TRX-floor C contributes +0.5943, positive because OOS TRX has a 48% win rate). Data extent grows monotonically with calendar time.

**This is independently corroborated by the cycle-2 record.** The /074 diary reports /074's OOS at +0.2090 and /074/075 themselves landed near +0.21 on the 14-feature stack. The "true" current-code /060-config OOS has been ≈ +0.21 for several iterations — the +0.1403 frozen value is stale.

**Implication for /071-/076 classifications: robust, not invalidated.** The IS code-drift (−0.0089) is an order of magnitude inside the INERT IS noise band (±0.10); the OOS data-extent drift (+0.0675) is well inside the ±0.20 OOS band. /071/073/076 were classified SUSPICIOUS by the OOS/IS *ratio* gate (4.51 / 6.85 / 15.04) — a ±0.07 OOS shift cannot move a ratio across the 3.0 boundary for those magnitudes. /074/075 were INERT by noise-band shifts that already absorbed the same drift. No cycle-2 classification flips under the staleness.

**Implication for the cycle-2 CONFIRMATION: none.** The CONFIRMATION (iter-v3/081+) MERGE gates anchor on `BASELINE_V3.md` /059 (the canonical /059 unified-architecture numbers) — the /060 EXPLORATION-MODE-REFERENCE is an intra-cycle delta anchor only and never feeds the CONFIRMATION gate.

**Re-anchoring recommendation for /078+:** the /078 brief Section 0 should explicitly state which anchor it uses and STOP citing the frozen +0.1403 OOS as if it were reproducible. Cleanest: anchor /078-/080 against the current-code /077 baseline (IS +0.8236 / OOS +0.2078), since /077 is the freshest no-axis run of the canonical config, and annotate the −0.0089/+0.0675 decomposition. The classification noise bands remain interpretable under either anchor. This is recorded as a Recommendation below.

### Adjudication #3 — the reframing finding (Brief Section 2.2 / EDA T1)

**The reframing is methodologically sound and the conclusion holds.** EDA `T1_regime_stratification.csv` (verified against the committed file) stratifies /060's IS monthly PnL by the per-calendar-month BTC regime label and finds **IS_BEAR_CHOP Sharpe +1.2909 (15 months, 47% positive) vs IS_BULL Sharpe +0.4100 (18 months, 33% positive)** — the IS drag is in the BULL months, the opposite of what /074/075/076 targeted.

The per-month BTC-regime label (`build_btc_monthly_regime`: a month is BULL if ≥50% of BTC 8h bars have `close[t-1] > SMA_270[t-1]`) is methodologically superior to the prior framing for one decisive reason: it is **exogenous to the strategy**. The prior "IS bear/chop drag" framing used the strategy's own trade-level regime tag — a label that is endogenous (it is conditioned on where the strategy chose to trade and how those trades resolved), so stratifying performance by it is partially circular. A calendar/price BTC-trend label is computed purely from BTCUSDT OHLCV with `.shift(1)` past-only discipline and assigns every calendar month independently of strategy behavior. The two labels disagree, and the exogenous one is the correct instrument. The conclusion — three cycle-2 iterations (/074, /075, the /076 framing) optimized against a stratum that is not the structural drag — holds. This finding should steer /078-/080 toward bull-month entry-discrimination, and it is consistent with the EDA T6 directional-quality diagnosis (win/loss duration ratio 2.08, 64% stop-loss exits, bull-month WR 32.7% vs bear/chop 43.6%).

### Adjudication #4 — the conditional-orthogonality deliverable

**The deliverable is valid.** `conditional_orthogonality.csv` is the hybrid the brief Section 3.1 implementation note pre-disclosed: PART A is the runner's last-walk-forward-month gain-importance share per feature (`lgbm._train_for_month` clears `self._models` each month, so only the final month survives to report time — a degenerate single-point map, correctly labeled as supplementary); PART B is the full per-IS-month map copied verbatim from the committed EDA `T3_conditional_orthogonality.csv` (EDA SHA `313d3c0`). I verified the report CSV's PART B columns byte-match the EDA `T3_conditional_orthogonality.csv` rows. The runner code (`run_baseline_v3.py:2092-2104`) reads the EDA file from a fixed path and degrades gracefully (`PART_A_runner_only` source tag) if absent.

**The EDA's conditional-orthogonality map is computed IS-only and correctly.** `compute_per_month_importance` trains a 3-seed walk-forward LightGBM per (symbol, IS-month) on the 14-feature anchor over IS-window months only (`open_time < OOS_CUTOFF_MS`), with embargo-22 purge and unformed-label-tail drop; `t3_conditional_orthogonality` correlates each feature's per-month gain-importance SHARE against the BULL=1 indicator restricted to `is_window` months. The 4-of-14 conditionally regime-loaded result is confirmed: `btc_ret_14d` max|corr| 0.4803, `hurst_diff_100_50` 0.4416, `max_dd_window_50` 0.4339, `range_realized_vol_50` 0.3704 — all above the a-priori 0.35 ceiling; `regime_momentum_signed_5d` clean at 0.2092. The map is the Critic /076 Rec #1 instrument and is now available for /078-/080.

**One internal EDA inconsistency, cosmetic, non-blocking:** `axis_selection_summary.csv` reports `IS_bull_months=36 / IS_bearchop_months=27` (sum 63) while `T1_regime_stratification.csv` reports `IS_BULL=18 / IS_BEAR_CHOP=15` (sum 33). The 63 is the count of ALL IS-window *calendar* months; the 33 is the count of IS-window months in which /060 actually *traded* (the 24-month training window means the first trade-active IS month is ~2022-02). Both numbers are individually correct for their respective denominators; the T3 conditional-orthogonality correlation correctly uses the per-month importance rows (which only exist for trade-relevant months with sufficient training data), so the map itself is unaffected. The defect is purely a same-name-different-denominator labeling inconsistency in the summary CSV. Recorded as a minor recommendation.

## Recommendations to QR

For the next iteration's brief (these are process/forward-looking; /077's verdict is final):

1. **Re-anchor /078+ explicitly.** The /060 frozen anchor (IS +0.8325 / OOS +0.1403) does not reproduce on current code+data — /077 establishes the current-code /060-config baseline at IS +0.8236 / OOS +0.2078. The /078 brief Section 0 must state which anchor it uses and stop treating the frozen +0.1403 OOS as reproducible. Recommended: anchor against /077's current-code numbers with the −0.0089 (code-drift) / +0.0675 (data-extent) decomposition annotated.

2. **Stop asserting "algebraic identity" for roster predictions unless the entire config has been git-verified frozen since the anchor.** /077's brief Section 4.1 claimed bit-identity as "not a confidence interval — an algebraic identity" while the codebase had silently accreted the /061 TRX `vol_scale_floor` since /060. A bit-identity prediction must be backed by a git-diff of every behavior-affecting config (`RiskV2Config`, ATR multipliers, vol-scale floors/ceilings, seeds) between the anchor commit and HEAD — not by an assumption that "no axis change" implies "no roster change." A pre-registered ≈4% benign-perturbation tail (which the brief did have) is the correct hedge; the over-confident framing of the point estimate is the defect.

3. **Fix the same-name-different-denominator inconsistency in EDA summary CSVs, and clean the stale ADF secondary-falsifier check.** `axis_selection_summary.csv` reports IS-window *calendar* months (63) under the same `IS_bull_months` key that `T1` uses for trade-active months (33) — disambiguate the labels. Separately, `run_baseline_v3.py:1149-1161` hardcodes a secondary-falsifier ADF check for `LDOUSDT/cusum_reset_count_200`, a feature that has not been in the stack since the /063 mass-expansion was reverted; it now emits a perpetual benign WARNING. Either remove it or make it conditional on the feature being present.
