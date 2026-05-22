# Phase 7.5 Critic Review — iter-v3/087

OVERALL: MERGE

This is an EXPLORATION-class review. OVERALL=MERGE means the iteration's METHODOLOGY is sound and the result may be recorded in the cycle-3 catalog — it does NOT mean the strategy improved. /087 is a methodologically clean run that produced a genuinely NEGATIVE result. The merge call is the orchestrator+QR's; this review certifies the result is trustworthy.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-3, slot #6 of 10). 3-seed EXPLORATION-mode, n_trials 35. Per `feedback_v3_dsr_mode_artifact.md`, Check 3 (DSR/PSR) is informational only; per-cell PBO and CPCV `frac_positive_paths` are the evaluated gates.

## Clarifications Round
Zero clarifications were raised. Every mandatory and optional check resolved unambiguously against committed artifacts; no QR response could change the verdict. This is a single-round review.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

No axis adds feature code — the SOLE axis is the `V3_MODELS` 3→6 tuple growth, and the two non-axis actions REVERT features (basis dropped). `V3_FEATURE_COLUMNS` is the 14-feature /059 anchor stack (`features_v3/__init__.py:319`, alias of `V3_FEATURE_COLUMNS_TOP_N`), verified at runtime by `_verify_feature_columns` to be exactly 14 columns with `basis_zscore_30/basis_momentum_3/basis_extreme_flag` absent (`run_baseline_v3.py:405-431`). The 3 new symbols (GALA/MANA/SAND) pass through the identical symbol-agnostic v3 feature pipeline as the incumbents — no symbol-specific feature code exists (`V3_FEATURES_PER_SYMBOL` is `{}`, verified at `run_baseline_v3.py:643-647`). The composed feature `max_dd_window_50` carries the `.shift(1)` past-only guard (EDA `wholesale_breadth_expansion_eda.py:257`); `regime_momentum_signed_5d` and `sym_vs_btc_ret_7d` are the /059-canonical composed features audited clean in prior cycles. Universe-selection look-ahead is the relevant risk for a breadth axis: the candidate screen used `open_time < OOS_CUTOFF_MS = 2025-03-24` on every frame (EDA lines 424, 620, 789), and the 60-day new-listing burn-in is applied (line 619) — GALA/MANA/SAND were selected on IS data only, no survivorship. ADF burn-in months 2020-2021 in `adf_test.csv` carry empty statistics (insufficient history), which is correct behavior for pre-training-window candles, not a leak.

### Check 2 — Embargo Width: PASS

This is the NO-CHEATING-critical check for /087 and it is clean. Labeling: `timeout_minutes = 10080`, `candle_minutes = 480` → `timeout_candles = 21`. Required pooled-CPCV gap = `(21+1) × n_symbols = 22 × 6 = 132`. `REQUIRED_GAP` is correctly `(21 + 1) * 6 = 132` at `validation_v3.py:69`, with the full universe-history comment block updated for the /087 6-symbol expansion. The runner imports it (`run_baseline_v3.py:71`), passes it to the global `combinatorial_purged_cv` with `expected_gap=REQUIRED_GAP` (`run_baseline_v3.py:1522-1524`), and `_verify_label_leakage_gap()` recomputes `(timeout_candles+1) × len(V3_MODELS)` dynamically and asserts equality (`run_baseline_v3.py:1138-1144`) — with `V3_MODELS` now 6 symbols, this auto-asserts 132. run.log line 27 confirms `"(timeout_candles=21+1) * n_symbols=6 = 132 [matches REQUIRED_GAP=132] PASS"`. The config-accretion table carries `("REQUIRED_GAP", REQUIRED_GAP, 132)` (`run_baseline_v3.py:1000`). `PER_CELL_GAP` correctly STAYS 22 (`run_baseline_v3.py:1600`) — the per-cell CSCV operates on a single-symbol `(symbol, month)` cell so the `×n_symbols` factor does not apply, and the per-cell call passes `expected_gap=PER_CELL_GAP` (`run_baseline_v3.py:1698`). The purge is symmetric. No stale 66 survives anywhere in the validation path. **Caveat for the QR (not a check failure):** the engineering report's config-diff table (line 22) prints `/084 PER_CELL_GAP = 11` and `/087 = 22 (= 132/6)`. Both are documentation errors — the /084 value was 22 (the /084 fix corrected 43→22), and the `132/6` derivation is a spurious rationalization. The actual code value 22 is correct and the math `(21+1)` is correct; only the report's prose is wrong. Flagged in Recommendations.

### Check 3 — Multiple-Testing Correction: PASS (informational for EXPLORATION)

DSR = 0.0, PSR = 0.0, PBO = 0.1230 (`dsr.json`, `comparison.csv`). DSR and PSR at zero are the expected EXPLORATION-mode artifact — `n_eff = 19`, `min_trl_months = 15.72`, n_trials = 630 — at the 3-seed/35-trial EXPLORATION budget the DSR/PSR estimators have insufficient trial history to clear any threshold, and per `feedback_v3_dsr_mode_artifact.md` they are INFORMATIONAL ONLY for an EXPLORATION and do NOT trigger BLOCK. The EVALUATED gates pass: per-cell PBO = 0.1230 is well below the 0.40 threshold, and CPCV `frac_positive_paths = 0.5556` (25/45 paths positive) clears the 0.55 gate — `cpcv_frac_positive_paths_gate_pass: true`. `n_trials = 630 = 35 × 6 symbols × 3 ensemble seeds` matches the EXPLORATION budget exactly. `n_eff = 19` from PCA on the trial-return matrix is sensible. For TYPE=EXPLORATION this check is non-blocking and the evaluated sub-gates pass.

### Check 4 — IC Correlation: PASS

`ic_matrix.csv` is present (the 14-feature /059-canonical pairwise Pearson IC matrix). No NEW feature family was added — /087 is a universe axis, the feature set is the unchanged /059 anchor — so there are no new-vs-existing pairs to gate. The `|IC| > 0.70` pairs (`regime_momentum_signed_5d ↔ vwap_dev_20` = 0.751; `regime_momentum_signed_5d ↔ sym_vs_btc_ret_7d` = 0.723) are the documented Category-2 composed-feature algebraic relationships covered by the `feedback_v3_engineered_feature_pivot.md` IC carve-out — pre-existing /059-stack pairs, not /087 regressions. `conditional_orthogonality.csv` confirms `regime_momentum_signed_5d` is not regime-loaded. No new collinearity introduced by the universe expansion.

### Check 5 — ADF Stationarity: PASS

`adf_test.csv` present with per-(symbol, feature, month) granularity — 4200 rows = 6 symbols × 14 features × [31..63] retraining months. The aggregate 80.2% stationary (3367/4200) is depressed by burn-in months (2020-2021 candles carry empty/insufficient-history statistics for long-window features — correct behavior). The relevant test is the training-window-end period: spot-audited 2024-10 through 2025-03 for BCH and LDO — every feature stationary at p < 0.05 except `ret_kurt_200` (p ≈ 0.06-0.09, borderline). `ret_kurt_200` is a 200-bar distributional-shape feature, inherently slow-mixing, /059-canonical and inherited unchanged — one borderline feature at the training-window edge on the established stack does not fail the check. No new feature was introduced to test.

### Check 6 — Pareto Dominance: PASS (not applicable — EXPLORATION single outer seed)

`pareto_front.csv` is absent. CORRECT for an EXPLORATION: the 10-seed pre-MERGE Pareto validation is a CONFIRMATION-stage requirement. /087 ran 3-seed EXPLORATION-mode at a single outer seed (`ensemble_summary.json`: `mode: exploration`, `ensemble_size: 3`, all 3 inner seeds `lineage: outer=42`). There is no multi-seed metric vector to Pareto-rank. Pareto dominance is the live gate at /092; structurally inapplicable here. No failure.

### Check 7 — Reproducibility: PASS

Setup commit `0d9a5e4` stamped in the brief Section 11 and the engineering report; the four-commit chain (`1a117b2` EDA → `287ce0d` brief → `0d9a5e4` setup → `a4b641f`/`32becde` SHA-backfill) is internally consistent. The runner uses an explicit 14-element `feature_columns` list (`V3_FEATURE_COLUMNS` alias, hard-asserted `== 14` at `run_baseline_v3.py:405`) — not `None`, not auto-discovered. The 3 inner ensemble seeds are literal and recorded (`ensemble_summary.json`: 191664963, 1662057957, 1405681631, all `outer=42`). `ITERATION_LABEL = "v3-087"`. Run integrity: exit code 0, zero "Optimization failed", zero Tracebacks, `trial_oof_returns.parquet` readable. I independently spot-checked 3 OOS trade rows from `out_of_sample/trades.csv`: row 1 (BCH short, entry 303.87 → exit 282.100779) `pnl_pct = 7.164%`, `net = 7.064`, `weighted = 7.064×0.33 = 2.3311` ✓; row 5 (TRX short) `pnl_pct = 3.909%`, `weighted = 1.5237` ✓; row 15 (TRX long) `pnl_pct = 3.123%` ✓. Sign convention, fee deduction, weight scaling all reconcile. The config-accretion guard (11 knobs) asserts every /059-canonical knob at runtime — only the 2 declared axis deltas (`V3_MODELS` 6-symbol, `REQUIRED_GAP` 132) differ.

### Check 8 — Hypothesis-Implementation Alignment: PASS

The brief Section 1 hypothesis — a wholesale 3→6 breadth expansion (GALA/MANA/SAND added) raises aggregate IS Sharpe via the `√N` diversification benefit — maps precisely to the implementation. The `V3_MODELS` tuple at `run_baseline_v3.py:179-186` grows exactly 3→6 with the three named symbols, each with a generic `("E/F/G (SYM)", "SYM")` label, no per-symbol features (`V3_FEATURES_PER_SYMBOL == {}`), no per-symbol ATR, no per-symbol gates — fully universal, exactly as Section 3.1 specifies. The two MANDATORY non-axis baseline-restore actions are correctly scoped and present: (a) the basis revert — `V3_FEATURE_COLUMNS_TOP_N` is the 14-feature stack, basis features absent and hard-banned at `run_baseline_v3.py:424-431` and `:648-655`; (b) the runner ABSENT-assertion ban for the 3 basis names is in place. No scope creep: the config-accretion table proves all 9 risk/labeling knobs stay /059-canonical. The single axis is the universe expansion exactly as the brief registered it. No hypothesis-faking.

## Optional Checks 9-12

### Check 9 — Symbol Exclusion Enforcement: PASS
`V3_EXCLUDED_SYMBOLS` (`features_v3/__init__.py:469-485`) contains only the v1/v2 symbols + MKR; GALA/MANA/SAND are absent. The closed universe-expansion candidates (HBAR/AVAX /021, ADA /078, FIL /083) are correctly excluded from the EDA candidate pool. The config-accretion check runs at runtime. PASS.

### Check 10 — Feature Isolation Enforcement: PASS
`grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` is empty — no v1/v2 cross-track imports. run.log confirms `"Track isolation (features_v3 does not import v1/v2): PASS"`. PASS.

### Check 11 — Forming-Candle Audit: PASS
The runner pre-flight asserts every kline CSV `close_time` within 16h of run time (run.log: `"data fresh (<16h) PASS"`). The Phase 6 prerequisite refreshed GALA/MANA/SAND from their stale 2026-02-28 extent to the common current extent; the 6-symbol IS-window row counts loaded cleanly (BCH 6984, LDO 3998, TRX 6926, GALA 5106, MANA 5652, SAND 5799). The engineering report's 10-row OOS trade spot-check found no NaN fields, zero anomalies. No future-dated forming candle. PASS.

### Check 12 — Library Version Pinning: PASS
Brief Section 9 declares no new libraries; the pinned stack (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1) matches the Section 11 reproducibility stamp. The axis is a tuple change + constant + feature-list revert — no dependency surface change. PASS.

## The Classification — Critic's Read for the QR's Section 8

The QR owns the final Section 8 call; this is the Critic's adversarial read.

**/087 is NEGATIVE.** The result is `IS Δ +0.0883 / OOS Δ −0.8349` vs ANCHOR 1 (/084). Walking the LOCKED disjunctive taxonomy (SUSPICIOUS → NEGATIVE → PROMISING → INERT → NULL):

- **SUSPICIOUS (evaluated first):** (a) OOS/IS ratio is −0.5460 — negative, not `> 3.0`, does not fire. (b) OOS-DOMINANT requires `IS Δ < 0 AND OOS Δ ≥ +0.20` — IS Δ is +0.0883 (positive) and OOS Δ is −0.8349, neither leg holds; does not fire. (c)/(d) the trade-selection sub-channels require the Phase-8 OOS roster-diff — but the brief T5 measured added-symbol IS duration gaps at +0.149/+0.181/−0.171 (all far inside ±1.0); F4-type firing is improbable but the QR must run the roster-diff to formally close (c)/(d). On the headline evidence, SUSPICIOUS does not fire.
- **NEGATIVE:** fires unambiguously. Section 8.2 trigger is `IS Δ < −0.10 OR OOS Δ < −0.20`. OOS Δ = **−0.8349** is far past the −0.20 leg. The OOS monthly Sharpe of **−0.5027** is a genuine collapse, not noise — all three new symbols lost in OOS (GALA −18.98%, MANA −27.16%, SAND −28.07% net pnl), OOS MaxDD blew out to 76.42%, and the worst CPCV path hit −3.47 Sharpe / 968 MaxDD. **NEGATIVE is canonical** (SUSPICIOUS does not fire, and NEGATIVE precedes PROMISING/INERT in precedence).

**The falsifier-band gap is real and the QR should record it.** The brief's F1 (`IS Δ < −0.20` → NEGATIVE, the /083 IS-collapse signature) did NOT fire — IS actually lifted +0.0883. F2/F3 were designed for the *opposite* divergence (IS flat/down, OOS up). /087 produced the **`IS up, OOS crashes`** overfit signature, which the brief's F1-F4 band had no dedicated trigger for. The taxonomy still classifies it correctly — Section 8.2's general NEGATIVE clause (`OOS Δ < −0.20`) is the catch-all and it fires cleanly — so there is no classification ambiguity and no methodology defect. But the *pre-registered falsifier table* (F1-F4) had no IS-up/OOS-down-specific gate. This is a brief-design observation, not a code or no-cheating problem — the QR should note it so future universe-axis briefs pre-register a symmetric falsifier (an `OOS Δ < −0.20 regardless of IS sign` gate as a named falsifier, not only as the Section 8.2 fallback).

**It is NOT INERT, NOT NULL, NOT SUSPICIOUS.** INERT requires `IS Δ ∈ [−0.10,+0.10] AND OOS does not clear +0.20` — the IS leg holds (+0.0883) but the disjunctive precedence puts NEGATIVE first and NEGATIVE fires, so INERT is foreclosed. NULL is mechanically impossible (3 symbols added, gap changed). SUSPICIOUS does not fire on headline metrics (QR confirms via roster-diff).

## The EDA-Screen Validity — QR-Process Finding

The /087 EDA screen had a fidelity weakness, and it should be recorded — though it does NOT invalidate the axis selection or warrant BLOCK.

The screen is honest about being a relative-ranking proxy: brief Section 2's "SCREEN SCOPE — LOAD-BEARING DISCLOSURE" explicitly states the screen runs un-tuned (fixed-LGBM-param, no Optuna, no 7-gate risk stack), that its absolute Sharpe numbers differ from production, and that only the SIGN/RANKING/correlation-structure are load-bearing. The screen used the full IS window (`open_time < OOS_CUTOFF_MS`, the same expanding 24-month walk-forward as production). So this is **not** a date-cherry-picked sub-window and **not** a no-cheating violation.

But the engineering report's anomaly note is correct and material: SAND screened at `+0.1289` standalone Sharpe / `+257 net pnl%` on the un-gated proxy roster (1485 IS trades) — yet the production run with the 7-gate stack + Optuna selected only 41 IS SAND trades that netted **−18.10%**. The screen's un-gated 1485-trade roster and the production 41-trade gated roster are different objects; the 7-gate stack discarded the bulk of SAND's screen-favorable trades and the residual was a net detractor. The screen's `direction-only` disclaimer covers magnitude error but does NOT cover a **sign flip** — SAND's screen sign (+) and production-IS sign (−) disagree. The screen therefore did not faithfully predict even the SIGN of one of the three selected symbols' full-IS behavior. This is the `/083`-lesson pattern recurring: a per-symbol-edge screen that does not survive the gate stack. It is a QR-process finding for the Recommendations. The methodology is sound — the screen was disclosed, IS-only, and committed — but its predictive fidelity was weaker than the brief's confidence implied. NEGATIVE result, sound methodology → OVERALL=MERGE.

## Recommendations to QR

1. **Record /087 as NEGATIVE in the cycle-3 catalog and BASELINE_V3.md Dead Ideas; do NOT advance the 6-symbol universe to the /092 bundle.** The wholesale breadth expansion is falsified for the GALA/MANA/SAND set — all three new symbols lost in OOS (the breadth `√N` benefit did not transfer through the production Optuna+7-gate stack). Direction 2 (universe expansion) now has a **4-failure track record (/021, /069, /083, /087)** across single, double, and wholesale adds — the QR should treat the breadth lever as CLOSED for the remainder of cycle 3 and direct /088-091 to Direction 3 (a non-naive pooled model) or genuinely fresh axes.

2. **Pre-register a symmetric NEGATIVE falsifier in future briefs.** /087's F1 falsifier (`IS Δ < −0.20`) was IS-collapse-specific and did not fire on the IS-up/OOS-crashes signature /087 actually produced; the result was caught only by the Section 8.2 general clause. Future briefs should name an explicit falsifier `OOS Δ < −0.20 regardless of IS sign → NEGATIVE` in the F-table, so the pre-registered falsifier set covers both divergence directions.

3. **Tighten the universe-screen fidelity protocol.** The /087 EDA screen mis-signed SAND (screen +0.13 Sharpe vs production IS −18.1% net pnl) because it ran un-gated while production runs the 7-gate stack. Future Direction-2 screens must either apply the production 7-gate risk stack inside the screen pipeline, OR flag any candidate whose un-gated and gated trade counts diverge by >10× as `screen-sign-provisional` and exclude it from the marginal-lift ranking until a gated re-screen confirms the sign.

4. **Fix the engineering-report config-diff documentation error.** The /087 engineering report config-diff table records `/084 PER_CELL_GAP = 11` and `/087 PER_CELL_GAP = 22 (= 132/6)`. Both are wrong: the /084 value was 22, and `PER_CELL_GAP` is `(timeout_candles+1) = 22` for a single-symbol cell — it has no `n_symbols` factor. The code (`run_baseline_v3.py:1600`) is correct at 22; only the report prose is wrong. Correct it so the archaeology record is not poisoned.
