# Phase 7.5 Critic Review — iter-v3/097

OVERALL: EXPLORATION-NEGATIVE — clean single-axis universe RE-SELECTION; LDO/GALA/ADA worse than /059 on BOTH axes; the QR's own pre-registered F1/F3 fired; no methodology defect; the Section-8 class 8.2 NEGATIVE-no-transfer is filable.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION — cycle-4, single-axis SYMBOL-UNIVERSE RE-SELECTION (`V3_MODELS` BCH/LDO/TRX → LDO/GALA/ADA). Scored on the methodology + look-ahead checks (1, 2, 4, 5, 6, 8) with full enforcement; Check 3 (DSR/PBO/PSR) is informational for an EXPLORATION — and in any case /097 is a NEGATIVE result, so there is no edge being claimed that the multiple-testing machinery could falsely launder.

## QR Response Considered

This review found ZERO blocking clarifications during the check sweep — every check resolved unambiguously against the committed artifacts. No QR `qr_response.md` round was required. The verdict below is final.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

The sole axis is the symbol universe; no feature, label, or window code changed. I traced the leak surface introduced by the swap. (a) The 14-feature `V3_FEATURE_COLUMNS_TOP_N` stack is bit-identical to /059 — `test_feature_columns_pinned_for_new_symbols` asserts `features_for_symbol("GALAUSDT")`, `("ADAUSDT")`, `("LDOUSDT")` each return the same 14-feature list and `V3_FEATURES_PER_SYMBOL` is empty; the test ran in the pre-backtest `&&`-chain. (b) The triple-barrier label is the unchanged `(2.0,1.0)`-ATR `(21+1)`-candle label. (c) The walk-forward embargo is intact: `test_walk_forward_embargo_intact` asserts `compute_embargo_candles(10080,480)==22`, `generate_monthly_splits` carries `train_end_ms = test_start_ms - embargo_ms` (the `e149e9d` fix), and `REQUIRED_GAP==66==(21+1)×3` for the 3-symbol universe. (d) The screening EDA itself is walk-forward-faithful — `symbol_universe_screen_eda.py:355-356` labels on the FULL panel first, THEN restricts to `[first_ms + 24mo, OOS_CUTOFF_MS)`, so the 21-candle forward scan never reads truncated-window data and no OOS row enters any IC; the purged 5-fold drops 22 embargo rows from both sides. GALA/ADA klines are pre-existing feature parquets; the runner's `_verify_data_freshness` hard-fails on >16h staleness and the run reached exit 0. No look-ahead introduced by the universe swap.

### Check 2 — Embargo Width: PASS

Required gap = `(timeout_candles + 1) × n_symbols = (21 + 1) × 3 = 66`. The universe count is unchanged (3 → 3), so the gap is unchanged from /059. Actual `REQUIRED_GAP` resolves to 66 (verified `run_baseline_v3.py:1019` config-accretion check, the `_verify_label_leakage_gap` runtime assertion at line 2665, and `test_walk_forward_embargo_intact`). The per-cell embargo `PER_CELL_GAP = 22 = (timeout_candles + 1)` is universe-count-invariant and unchanged. Symmetric application verified in the EDA's `purged_kfold_indices` and the runner's `combinatorial_purged_cv` calls. No serial-dependence leakage path.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION; provenance verified clean)

`dsr.json`: DSR 0.0, PBO 0.1089, PSR 0.0011. PSR 0.0011 << 0.95 and DSR 0.0 — both fail the CONFIRMATION thresholds. Per TYPE=EXPLORATION this is informational, NOT BLOCK-triggering, and /097 is a NEGATIVE result claiming no edge. The provenance question resolves CLEAN, not a /092-class defect:

- **DSR 0.0 is the known per-symbol-runner structural artifact, NOT a hardcoded placeholder.** The runner computes `dsr_val = deflated_sharpe_ratio_v3(...)["p_value"]` (`run_baseline_v3.py:2882-2889`), and `deflated_sharpe_ratio_v3` (`validation_v3.py:428-500`) returns `p_value = norm.cdf(dsr_z)` with NO clamp. The decisive cross-reference: the /059 canonical baseline `dsr.json` carries `"dsr": 0.0` with a HEALTHY IS monthly Sharpe of +1.0894 — DSR=0.0 is produced by a per-symbol-runner trade-volume regime where `dsr_z` is steeply negative against the large `expected_max_sr`, and `norm.cdf` underflows below 5e-9, rounding to 0.0 at `round(dsr_val, 8)`. Categorically different from the /092 BLOCK class (degenerate cross-sectional schema with `"pbo": NaN, "n_eff": 0`); /097's is the complete /059-identical schema with a genuine PBO float and `n_eff: 19`.
- **PBO 0.1089 is a genuine `validation_v3` CSCV computation.** `per_cell_pbo.csv` is a 109-row CSV of real per-(symbol, train_month) PBO values spanning 0.0–0.995; 0.1089 is their cross-cell mean. `cpcv_paths.csv` carries 45 genuine return-proxy paths with dispersed Sharpes (q25 −0.875, q50 +0.053, q75 +1.035). Not sentinels.
- **PSR 0.0011 is genuine.** `psr(...)` on the negative-Sharpe OOS trade series returns a small positive `norm.cdf(z)` — correct for a negative OOS Sharpe.
- `test_dsr_json_is_genuinely_computed` (the /090→/092 anti-sentinel guard) structurally verifies the runner imports and calls `validation_v3.psr` and `deflated_sharpe_ratio_v3` and both return finite values; both imported at `run_baseline_v3.py:70-78`; the test ran before the backtest.

`frac_positive_paths` 0.511 fails the 0.55 CPCV gate — consistent with a NEGATIVE result, not a defect.

### Check 4 — IC Correlation: PASS

`ic_matrix.csv` shows `regime_momentum_signed_5d` ↔ `vwap_dev_20` at 0.811 and `regime_momentum_signed_5d` ↔ `sym_vs_btc_ret_7d` at 0.745 — above the 0.70 raw threshold. However, iter-v3/097 adds ZERO new feature families: the 14-feature stack is the unchanged /059 stack (`test_feature_columns_pinned_for_new_symbols` enforces bit-identity). Check 4's threshold applies to families ADDED in the iteration's commits; there are none. These pairs are the pre-existing constructed-feature collinearity already documented at `feedback_v3_engineered_feature_pivot.md` (composed features mechanically correlate with their primitives). No new redundancy introduced. PASS.

### Check 5 — ADF Stationarity: PASS

`adf_test.csv` carries 1502 `stationary=True` rows and 416 `stationary=False` rows. The `False` rows with empty `adf_statistic`/`p_value` are early pre-burn-in calendar months (e.g. LDOUSDT 2022-09/2022-10, before LDO's 24-month-burn-in IS span) where the rolling feature window has insufficient data — NOT in the runner's IS evaluation span. For each symbol's actual IS window the features are stationary (LDOUSDT `hurst_100` 2024-09→2024-12: ADF p 8e-06 to 2e-06). The 14-feature stack is the unchanged /059 stack — no new price-derived feature introduced. No defect.

### Check 6 — Pareto Dominance: PASS (not applicable; correctly absent)

iter-v3/097 ran `--exploration --seeds 1` (outer seed 42, `ENSEMBLE_SIZE=3`). Single-seed EXPLORATION has no multi-seed Pareto front — `pareto_front.csv` correctly absent (Gate-10 Pareto was replaced by the `cpcv_frac_positive_paths_gate` at /059). The seed-selection methodology IS audited upstream: the screening EDA's seed-robustness check (`seed_robustness_check.py`, T6) confirms the GENUINE/THIN split holds across 4 LightGBM seeds. No Pareto defect.

### Check 7 — Reproducibility: PASS

Setup commit SHA `e6ed662a80982461241c32f6456a50343eb19454` stamped in the engineering report. `feature_columns` explicit and pinned (`V3_FEATURE_COLUMNS_TOP_N`, 14 entries). The 6-test integration suite `tests/strategies/ml/test_universe_reselection_v3.py` ships and is genuine (all 6 real HARD asserts, not stubs). Inner ensemble seeds deterministically derived. Trade-row spot check: 10+ rows of `in_sample/trades.csv` re-checked — `net_pnl_pct = pnl_pct − fee_pct` holds, `weighted_pnl ≈ net_pnl_pct × weight_factor` holds, exit prices internally consistent. No silent dependency, off-by-one, or sign error.

**One process gap, NON-BLOCKING.** The brief's Section 9.2 mandated `analysis/iteration_v3-097/roster_diff_oos.py` as a committed reproducible F0-verification artifact; the engineering report admits it "was not committed as part of Phase 6." A missed brief deliverable. It does NOT change the verdict: (a) F0 is structurally non-fireable here — GALA+ADA contribute 43/55 OOS trades (78%) and were ABSENT from /059, so >50% OOS roster overlap is arithmetically impossible; (b) F0 is a build-defect detector and the universe demonstrably changed; (c) recorded as Recommendation 1.

### Check 8 — Hypothesis-Implementation Alignment: PASS

Brief Section 1 hypothesis: re-anchor `V3_MODELS` from BCH/LDO/TRX onto LDO/GALA/ADA, single axis, everything else /059-identical. The implementation matches exactly. `V3_MODELS` is `(("C (LDOUSDT)","LDOUSDT"),("F (GALAUSDT)","GALAUSDT"),("G (ADAUSDT)","ADAUSDT"))`; `ITERATION_LABEL="v3-097"`. The single-axis claim is mechanically enforced by the runner's `config-accretion check` (`run_baseline_v3.py:1009-1046`) — it hard-fails the build if ANY of 11 knobs drift from /059-canonical, the SOLE permitted change being `V3_MODELS symbols`. The backtest reached exit 0 → this check passed; no hidden second axis. The 6-test suite genuinely asserts the single-axis claim. No hypothesis-faking.

### Falsifier Cross-Audit (brief Section 4.3)

Re-evaluated every falsifier against the runner artifacts directly — all six QE evaluations correct:
- **F0** (OOS roster >50% shared with /059) — does NOT fire. GALA+ADA = 43/55 OOS trades, both absent from /059.
- **F1** (OOS monthly Sharpe < +0.40) — **FIRES**. `comparison.csv` out_of_sample = −0.3541.
- **F2** (IS monthly Sharpe < +0.80) — **FIRES**. in_sample = +0.7197.
- **F3** (GALA OOS `weighted_pnl` < 0 AND IS > 0 — the named /087-reversal falsifier) — **FIRES**. `in_sample/per_symbol.csv` GALA net_pnl_pct +67.2008; `out_of_sample/per_symbol.csv` GALA −18.5027. The per-symbol numbers in the engineering report (GALA IS +67.2/OOS −18.5; ADA +47.0/−14.6; LDO −11.4/−15.8) are bit-faithful to the committed CSVs. The /087 GALA IS-up/OOS-down reversal recurred exactly as the QR pre-registered.
- **F4** (OOS lift >80% one-month) — does NOT fire (no positive OOS lift exists).
- **F5** (OOS/IS ratio < 0.50) — **FIRES**. Ratio −0.4921.
- **F6** (OOS trades < 130) — **FIRES**. 55 OOS trades.

Section-8 disjunctive precedence: 8.0 (F0) no → 8.1 (F4 / OOS-soars-on-flat-IS) no → **8.2 NEGATIVE-no-transfer fires first** (F1). F3 additionally fires as compounding evidence. The QE's classification of 8.2 NEGATIVE-no-transfer is correct. A clean, fully pre-registered NEGATIVE — every falsifier that fired was a LOCKED numerical gate set before Phase 6; F3 named the GALA reversal as the central risk before the run, and it recurred. No post-hoc rationalization. `BASELINE_V3.md` correctly UNCHANGED — v0.v3-059 stays canonical.

## Recommendations to QR

This is an EXPLORATION-NEGATIVE. The verdict is final; these are process items for the next iteration.

1. **Commit every brief-named artifact.** Section 9.2 mandated `roster_diff_oos.py` as a committed reproducible F0 script; Phase 6 skipped it. Here F0 was structurally non-fireable so it caused no harm — but a future iteration where F0 *could* fire would have no reproducible roster-diff to adjudicate the NULL-vs-NEGATIVE branch. Either commit every brief-named artifact, or have Phase 5.5 down-scope artifacts that are provably unnecessary so the brief and the delivered build agree.

2. **The IC-screen-necessary-but-not-sufficient result is now empirically demonstrated — fold it into the next universe brief, or abandon symbol-screening as a lever.** /097 confirms what Section 2.7 / 4.2 hypothesized: GALA's +0.127 within-symbol purged-CV rank-IC (seed-stable across 4 seeds) did NOT transfer to a positive OOS per-symbol `weighted_pnl` — and neither did ADA's +0.053. A genuine, cross-validated, seed-stable feature→label IC is not predictive of OOS per-symbol PnL in the v3 per-symbol framing. Three universe families have now failed (expansion ×4, revision-by-swap, this re-selection). Before any further universe axis, the QR should either (a) add an OOS-transfer step to the screen, or (b) abandon symbol-screening as a lever. The 2-symbol LDO+GALA / LDO+ADA fallbacks named in Section 4.4 are likely to inherit the same non-transfer; the QR's Phase-8 should weigh that against the directed cycle-4 feature-expansion / pooled-model axes rather than spending /098 on another universe permutation.

3. **F1 was set at the exact lower bound of the predicted OOS band (+0.40), leaving zero margin.** The observed −0.35 fired F1 by a wide margin so it did not matter here — but a result landing at +0.41 would have been a non-falsified PROMISING on a prediction the band itself called the floor. Future briefs should separate the falsifier threshold from the predicted-band edge by a stated margin so a marginal result is unambiguous.
