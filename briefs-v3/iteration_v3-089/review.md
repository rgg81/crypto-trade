# Phase 7.5 Critic Review — iter-v3/089

OVERALL: MERGE

This is a methodology review. iter-v3/089 is a CONSTRUCTION-PARTIAL *result* from a methodologically-sound run: the sign fix, the CPCV-proxy rewrite, the overlapping-hold tranche book, and the no-trade band are all leakage-free; the GROSS-POSITIVE finding (IS gross monthly Sharpe +0.0925, OOS gross monthly Sharpe +0.1717) is genuine and not an artifact of look-ahead in the new PnL accounting; the hard turnover ceiling is genuinely enforced and emitted; the EDAs are IS-only; and Check 8 PASSES because the code faithfully implements the brief. A CONSTRUCTION-PARTIAL result (improved +0.44 on both IS and OOS vs /088, gross-positive, still net-sub-floor) from a clean run is OVERALL=MERGE — validly recorded. I find no methodology DEFECT. The base architecture (`XS_REQUIRED_GAP = 88` embargo, the label, the panel) is unchanged from the /088-audited-clean state and I re-confirm it.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-3 slot #8 of 10; CORRECTED-BUILD on the RETAINED /088 cross-sectional architecture). Per brief Section 0.5, Check 3 (DSR/PSR/PBO) edge-axis FAILs are informational only and do NOT trigger BLOCK.

## QR Response Considered (Round 2 only)

Single-round review — every check resolved unambiguously against the committed artifacts. No clarifications were required from the QR. Round 2 skipped.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

This is the highest-stakes check. The /089 changes — the sign flip, the 3-bar overlapping-hold logic, the no-trade band, the CPCV-proxy rewrite — are the focus; the base architecture is /088-audited.

**(a) The sign flip in `build_positions` (`cross_sectional.py:657-663`).** `order = np.argsort(scores)` (ascending), `long_syms = sorted_syms[-n_leg:]` (top quantile, highest scores), `short_syms = sorted_syms[:n_leg]` (bottom quantile). `scores` comes from `strategy._model.predict(x_t)` — the model trained on the prior month's data, scored on the time-`t` cross-section. The sign flip is a relabeling of *which* decided positions are long vs short; it introduces no temporal dependency. No look-ahead.

**(b) The 3-bar overlapping-hold logic (`run_cross_sectional_backtest:950-960`).** This is the known look-ahead trap and I traced it explicitly. At each bar a `new_tranche = {s: w/hold_bars for s,w in target.items()}` is formed, where `target = build_positions(panel_t, scores, hist, ...)`. `panel_t` is the time-`t` cross-section; `hist = ret_wide[ret_wide.index < ts]` is strictly past (`< ts`, not `<= ts`); `scores` are from the prior-month model. The tranche carries a retire-bar index `bar_counter + hold_bars`; `tranches` is filtered to live tranches and `raw_book` is their sum. The book at bar `t` is therefore the sum of tranches formed at `t`, `t-1`, `t-2` — all decided at-or-before `t`. The PnL is `gross_pnl = pos * next_ret` with `next_ret = ret_wide[sym].iloc[idx_loc]`, `idx_loc = ret_wide.index.searchsorted(ts, side="right")` — the strictly-after-`t` (`t→t+1`) return. The book position is decided at `t`, earns the `t→t+1` return, and **exactly one `gross_pnl` row is emitted per (bar, symbol)** — the book PnL is computed once from the current summed-tranche position. There is no double-count and no peek: a tranche does not separately accrue PnL; it only contributes its weight to the single per-bar book position. The `bar_counter` and `prev_book` are correctly carried *across* walk-forward month boundaries because the test months are contiguous calendar months and a real book does not reset at month-end.

**(c) The no-trade band (`apply_no_trade_band:742-767`).** `out[s] = t if abs(t - h) > band else h`, where `t = target.get(s, 0.0)` is the current bar's `raw_book` weight and `h = held.get(s, 0.0)` comes from `prev_book` — the **previous** bar's post-band book (`prev_book = dict(book)` at line 1031, set at the end of each bar). The comparison is current-target vs previous-actual — strictly past-referencing. No look-ahead.

**(d) The CPCV-proxy rewrite (`_compute_xs_cpcv:230-356`).** It restricts to IS rows (`~results["is_oos"]`), sums the per-bar `net_pnl` into one book return per IS timestamp (`bar_ret`), and for each of the 45 CPCV paths computes the Sharpe of the path's test-fold slice `bar_ret_arr[test_idx]`. It reads the already-computed corrected-sign walk-forward `net_pnl` (it does not re-fit) — so the path metric is the genuine realised long-short net return, not the /088 degenerate `mean(sub_labels[long])−mean(sub_labels[short])` label-grade self-correlation. `combinatorial_purged_cv` is called with `gap=XS_REQUIRED_GAP, expected_gap=XS_REQUIRED_GAP` — the silent-rescale guard fires on mismatch. `cpcv_paths.csv` is non-degenerate (45 distinct Sharpes spanning −0.094 to +0.053), confirming the rewrite. No look-ahead.

**(e) Base architecture re-confirmation.** `XS_REQUIRED_GAP = (XS_HORIZON+1)*N_XS_SYMBOLS = (3+1)*22 = 88` is unchanged. `_generate_xs_monthly_splits:1088` sets `train_end_ms = test_start_ms − embargo_ms` (the `e149e9d` fix). The label `label_cross_sectional_rank` and the panel `_xs_rank_normalize` are byte-unchanged from the /088-audited state. The per-bar vol estimate `ret_wide[ret_wide.index < ts]` is strictly past-only.

The gross-positive claim survives this audit. OOS gross monthly Sharpe +0.1717 from a +0.0279 OOS rank-IC is plausible for a concentrated quintile long-short with inverse-vol weighting (the rank-IC is a flat per-timestamp average; the book monetizes the tail spread, which is steeper than the average). A leaked result would show an OOS rank-IC an order of magnitude larger. The +0.0279 faint OOS rank-IC and the +0.17 gross Sharpe are mutually consistent with a real, clean, thin signal. PASS.

### Check 2 — Embargo Width: PASS

The label horizon is H=3 bars. The pooled panel flattens 22 (symbol, timestamp) rows per timestamp. López de Prado's purge requires `(H+1) × N = (3+1) × 22 = 88` flattened rows on both sides of every test boundary. `XS_REQUIRED_GAP = 88` is correct, verified independently. It is wired with hard self-assertions in two places (`_verify_xs_universe`, `_verify_xs_gap_assertion`) and passed to `combinatorial_purged_cv` with `expected_gap=88` — `run.log` confirms `[preflight] XS_REQUIRED_GAP=88 == (H=3+1)*N=22 — PASS` and `XS_REQUIRED_GAP=88` asserted on the CPCV call. The walk-forward embargo is `88 bars × 8h = 704h` against a 24h H=3 label window — conservative by ~29×. Unchanged from /088; re-confirmed. PASS.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)

`dsr.json` reports `dsr=0.0`, `psr=0.0`, `pbo=NaN`, `frac_positive_paths=0.356`, `n_trials=35`, `n_eff=0`. None of the DSR/PSR/PBO thresholds (>0.95, >0.95, <0.4) clear. **Per brief Section 0.5, TYPE=EXPLORATION — Check 3-edge axis FAILs do NOT trigger BLOCK; flagged here for record.** The runner sets `dsr/psr=0.0` as deliberate sentinels with the honest note "DSR/PSR not applicable at EXPLORATION" rather than computing a misleading number — correct, and per `feedback_v3_dsr_mode_artifact.md` EXPLORATION-mode DSR is a structural artifact regardless. The substantive read: `frac_positive_paths = 0.356` is now a genuine, informative number — the /088 CPCV-proxy defect (Critic /088 Rec #3) is fixed, and `cpcv_paths.csv` is non-degenerate (16 of 45 paths positive, Q50 −0.0210, range [−0.094, +0.053]). 0.356 is below the brief's F4-style 0.55 threshold, consistent with a net-negative book. Informational only for an EXPLORATION; the CPCV gate now carries information for the first time on this architecture. FAIL (informational, non-blocking).

### Check 4 — IC Correlation: PASS

No new feature *family* was added. The feature set is the same 13-feature cross-sectional stack (`V3_FEATURE_COLUMNS_TOP_N` minus `btc_ret_14d`) carried byte-unchanged from /088, confirmed at `run_cross_sectional_v3.py:89-91` and `_verify_feature_columns` (hard `len == 13` + `btc_ret_14d`-absent assert). The brief Section 3.5 explicitly defers the G4 cross-sectional-momentum feature expansion to /090. No new-vs-existing feature-family pair exists, so `ic_matrix.csv` is not required for a construction-axis iteration. PASS.

### Check 5 — ADF Stationarity: PASS

No new price-derived features were introduced — the 13 features are the /059 anchor stack, ADF-cleared at /059. The cross-sectional rank-normalization transform (`_xs_rank_normalize`) maps each feature to a per-timestamp rank in [0,1], which is bounded and has no unit root by construction — it strengthens stationarity. `adf_test.csv` is not emitted by the cross-sectional runner; acceptable here because no new feature requires the test. PASS.

### Check 6 — Pareto Dominance: PASS

Single-seed EXPLORATION (`seed=42`, `ensemble_size=1` per `run_cross_sectional_v3.py:761`). The 10-seed Pareto front is a CONFIRMATION requirement; an EXPLORATION runs single-seed and a Pareto front does not apply. The relevant concentration check is the brief's F5 falsifier (no single symbol > 50% of OOS book PnL) and it PASSES decisively: `out_of_sample/per_symbol.csv` shows max OOS concentration `ICPUSDT` at 12.18%, `FILUSDT` at 9.42% — no symbol exceeds 13%. The quintile dollar-neutral construction delivers structural diversification. PASS.

### Check 7 — Reproducibility: PASS

(1) **Commit SHA stamped** — engineering report header: implementation SHA `bb8c231`, Phase 5.5 gate PASS SHA `32ee747`; brief Section 11 corroborates Setup SHA `bb8c231`. (2) **Explicit `feature_columns`** — `XS_FEATURE_COLUMNS` is a literal list comprehension over `V3_FEATURE_COLUMNS_TOP_N` (`run_cross_sectional_v3.py:89-91`), `_verify_feature_columns` hard-asserts `len == 13` and `btc_ret_14d` absent, `CrossSectionalRankStrategy.__init__` raises `ValueError` if `feature_columns` is falsy — no auto-discovery. (3) **Seed literal** — `seed=42` default threaded into `TPESampler(seed=self.seed)` and `LGBMRanker(random_state=self.seed)`. (4) **PnL spot-check** — I reconciled 3 rows. IS row 2 (FILUSDT, first bar, entry from flat): `pos = −0.0847255`, `gross = 0.00170421` → implied 1-bar return `gross/pos = −0.020114` (a short profiting from a −2% move); `fee = |pos − 0| × 0.001 = 8.47255e-05` (exact match); `net = gross − fee = 0.00161949` (exact match). IS row 36 (FILUSDT exits to flat, `pos = 0.0`): `fee = 8.47255e-05 = |0 − (−0.0847255)| × 0.001` — the exit-fee path over the `book ∪ prev_book` union is correct. OOS row 53 (RUNEUSDT, `pos = 0.0`): `fee = 2.479e-05 = |0 − (−0.02479)| × 0.001` — exit fee correct. The widespread `fee = 0.0` in OOS rows is the no-trade band correctly carrying bit-stable weights bar-to-bar (`pos == prev_pos` → zero fee), not a bug. PASS.

### Check 8 — Hypothesis-Implementation Alignment: PASS

Check 8 tests "does the code match the brief," and it does. The brief Section 3.1 specifies the sign fix: LONG the top quantile (high score = predicted future winner), SHORT the bottom. The code (`build_positions:662-663`) implements exactly that — `long_syms = sorted_syms[-n_leg:]`, `short_syms = sorted_syms[:n_leg]` — the inverse of /088. The `test_sign_fix_longs_highest_scores` test deterministically verifies it. The engineering report's predicted_score audit confirms it empirically: mean LONG-leg score +0.114, mean SHORT-leg score −0.209. Brief Section 3.2 specifies the CPCV-proxy rewrite — `_compute_xs_cpcv` implements it. Brief Section 3.3 specifies `XS_QUANTILE_FRAC=0.20`, `XS_HOLD_BARS=3`, `XS_NO_TRADE_BAND=0.020` — all three constants set to those values (`test_iter089_construction_constants` confirms) and passed explicitly at the runner call site. Brief Section 3.4 specifies `XS_TURNOVER_CEILING=0.138` as a hard gate — wired and emitted to both `comparison.csv` and `dsr.json`.

No scope creep: the legacy per-symbol `run_baseline_v3.py` path is untouched. No hypothesis-faking: every /089 code change maps to a brief sentence. The four mandatory components (sign fix, CPCV-proxy fix, cost-aware construction, turnover ceiling) are all present and correctly wired. PASS.

## Optional Checks 9–12

### Check 9 — Symbol Exclusion Enforcement: PASS
`_verify_xs_universe` (`run_cross_sectional_v3.py:119-126`) hard-asserts `set(XS_UNIVERSE) & set(V3_EXCLUDED_SYMBOLS)` is empty. The 22-symbol `XS_UNIVERSE` carries no v1/v2-excluded symbols. PASS.

### Check 10 — Feature Isolation Enforcement: PASS
`cross_sectional.py` imports only from `crypto_trade.config`. `run_cross_sectional_v3.py` imports only from `crypto_trade.config`, `crypto_trade.features_v3`, and `crypto_trade.strategies.ml.{cross_sectional,validation_v3}`. No v1/v2 feature imports. PASS.

### Check 11 — Forming-Candle Audit: PASS
`_verify_data_freshness` checks every symbol's `8h.csv` for staleness, accepting fresh (<16h) or last-bar-past-`OOS_CUTOFF_MS` (delisted-but-complete). `run.log` confirms feature regeneration ran for all 22 symbols. The PnL `searchsorted(side="right")` makes a forming last bar yield `next_ret = 0.0` rather than a corrupt feature. PASS.

### Check 12 — Library Version Pinning: PASS
Brief Section 9 declares no new third-party dependency. `cross_sectional.py` imports exactly `lightgbm`, `numpy`, `optuna`, `pandas`, `pyarrow.parquet` — all pre-existing v3 dependencies. PASS.

## Recommendations to QR

This iteration is a methodologically-clean CONSTRUCTION-PARTIAL — recorded validly. My read on the Section 8 classification and three items for /090.

1. **Section 8 classification: this is 8.4 CONSTRUCTION-PARTIAL — and the QR should file it as such.** The disjunctive-precedence walk: 8.1 SUSPICIOUS does not fire — OOS/IS Sharpe ratio is +0.50 (both negative; the SUSPICIOUS signature is OOS-soars-on-flat-IS, and /089 produced two coherent improvements, not a divergence), and OOS rank-IC +0.0279 is *weaker* than the model's IS-train rank-IC (~0.10–0.13), the opposite of SUSPICIOUS. 8.2 CONSTRUCTION-FALSIFIED does not fire — F2 (IS turnover 0.1153 > 0.138) does NOT fire (the hard gate PASSES), and F3 (OOS Sharpe ≤ /088's −0.5418) does NOT fire (OOS −0.0985 > −0.5418, a +0.44 improvement). 8.3 CONSTRUCTION-VALIDATED-PROMISING does not fire — it requires OOS monthly Sharpe > 0, and OOS is −0.0985 ≤ 0. **8.4 CONSTRUCTION-PARTIAL is the canonical match**: OOS rank-IC +0.0279 > 0, IS turnover ≤ 0.138, OOS Sharpe > /088's −0.5418, but OOS Sharpe ≤ 0. The corrected construction works, contains turnover, transfers OOS, and materially improves the OOS book — but the thin gross signal keeps it sub-zero. This is the brief's pre-registered ~45% modal outcome. NO-MERGE; BASELINE_V3.md stays `v0.v3-059`.

2. **The book is now gross-positive with fees/gross down to 1.58× OOS — /090 should pursue gross-signal strengthening, not a third round of turnover reduction.** The load-bearing finding is that the book IS gross-positive (OOS gross monthly Sharpe +0.1717) and fails net only on fees (OOS fees/gross 1.58×, down from /088's 8.8×). Of the three /090 directions: (a) further turnover reduction has steeply diminishing returns — the /089 EDA E4 shows IS net Sharpe gains of only ~0.01–0.04 per band step, and pushing hold-bars or the band harder will start sacrificing the gross signal itself (E3 already shows gross Sharpe going negative on the IS-internal walk-forward at hold ≥ 3); (b) gross-signal strengthening is the higher-EV lever — the OOS gross Sharpe +0.17 is the asset to grow, and the brief already scoped the G4 cross-sectional-momentum feature expansion (+2% IC-IR on IS) as the /090 axis with its own EDA. I concur with the brief's deferral. /090 should be the gross-signal feature-expansion EXPLORATION, multivariate-contribution-tested per the iter-v3/070 dead-path discipline.

3. **The short-leg-carries-the-alpha asymmetry is a real, pre-registerable signal-anatomy finding — /090's brief should treat it as a hypothesis, not noise.** The engineering report documents that the SHORT leg carries the entire gross spread (OOS short-leg gross +0.1200; OOS long-leg gross −0.0633 — the long leg loses gross despite longing the model's predicted winners). This is the opposite of the textbook cross-sectional pattern. It is internally consistent (the per-leg PnL reconciles, the sign fix is confirmed correct). /090's QR should pre-register, with IS-only EDA, whether the cross-sectional signal in this 22-symbol altcoin universe is structurally a downside/short predictor — and if so, a long-only-short or short-tilted construction (or an asymmetric leg-sizing) is a legitimate /090/091 axis with its own pre-registered falsifier band. Do not let the asymmetry be rationalized post-hoc; make it a falsifiable hypothesis.

One minor record item, not affecting any verdict: the brief Section 2.4 E4 table transcribes 5 of the 7 τ-grid rows the EDA actually scanned (`E4_no_trade_band_scan.csv` has τ ∈ {0.0, 0.0025, 0.005, 0.0075, 0.010, 0.015, 0.020}; the brief table shows {0.0, 0.005, 0.010, 0.015, 0.020}). The IS-best τ=0.020 is the same in both, so no parameter is affected — but future briefs should transcribe EDA grids in full.
