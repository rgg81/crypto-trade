# Phase 7.5 Critic Review — iter-v3/090

OVERALL: BLOCK — the engineering report's central "gross signal fell" finding rests on a wrong /089 gross-Sharpe anchor (+0.5947) that contradicts three independent /089 artifacts and is mathematically impossible; the gross comparison is computed on an inconsistent measurement basis, so the load-bearing classification input is unverified.

This is a methodology review. iter-v3/090's *run* is methodologically clean — the two new features are look-ahead-free, the embargo is correct, the single-axis claim holds, and the code faithfully implements the brief. **But the engineering report is not the run.** The report's decisive finding — "the 2 downside-risk features did NOT lift the gross signal; OOS gross Sharpe FELL from /089's +0.5947 to +0.5398" — is built on a /089 anchor figure (+0.5947) that is provably wrong, and on a gross-Sharpe computation that is not on the same measurement basis as every other Sharpe in the v3 cross-sectional line. The Section 8 classification (FEATURE-EXPANSION-FALSIFIED vs FEATURE-EXPANSION-PARTIAL) turns on whether the gross signal strengthened or fell — and that input is currently unverified. A methodology DEFECT in the central diagnostic is OVERALL=BLOCK regardless of the (likely-correct) negative direction of the result. The QR must not file the Section 8 call until the gross-Sharpe computation is corrected and recomputed on the per-month basis for both /089 and /090.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-3 slot #9 of 10; gross-signal-strengthening build on the RETAINED /088 cross-sectional architecture + /089 cost-aware construction). Per brief Section 0.5, Check 3 (DSR/PSR/PBO) edge-axis FAILs are informational and do NOT trigger BLOCK. The BLOCK here is NOT a Check-3 edge FAIL — it is a methodology DEFECT in the engineering report's central gross-Sharpe diagnostic, which is in scope for any iteration type.

## QR Response Considered (Round 2 only)

Single-round review. Every mandatory check resolved unambiguously against the committed artifacts. The one issue that would normally be a clarification — the cross-report gross-Sharpe discrepancy — is not a clarification because it is resolvable from the artifacts alone (the /089 engineering report, the /089 Critic review, the /089 diary, and arithmetic on the committed monthly_pnl.csv files all converge on +0.1717 and exclude +0.5947). It is a definitive DEFECT, not an open question.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

The two new features are the focus; the base architecture is /088/089-audited-clean and re-confirmed. `_engineer_xs_downside_features` (`src/crypto_trade/strategies/ml/cross_sectional.py:273-329`):

- **`xs_sortino_mom_12`** — `ret_1 = close.pct_change()`; `neg = ret_1.where(ret_1 < 0, 0)`; `semidev = neg.rolling(50).std()`; feature `= (close/close.shift(12) - 1) / semidev.replace(0, nan)`. Every transform (`pct_change`, `where`, `rolling().std()`, `shift(+12)`) is backward-looking. The value at bar `t` uses only bars ≤ `t`.
- **`xs_downbeta_50`** — `btc_ret_1` is a monotone transform of a historical bar-`t` observation; `down_mask = btc_ret_1 < 0` (contemporaneous, bar-`t`); `cov_d = r_d.rolling(50, min_periods=15).cov(b_d)`; `var_d = b_d.rolling(50, min_periods=15).var()`; feature `= cov_d / var_d`. All rolling windows backward-looking.
- The panel builder engineers the features before the 180-bar listing burn-in then drops the warm-up rows — correct; `expand_downside=False` keeps the /088/089 path byte-identical.

The load-bearing guard `test_iter090_downside_features_no_lookahead` engineers on a 400-bar full panel and a 300-bar prefix and asserts every overlapping non-NaN row bit-identical at `rtol=1e-9`. Genuinely adversarial; 40/40 tests green. The QE's Phase 5.5 gate reached the same finding independently. PASS.

### Check 2 — Embargo Width: PASS

Label horizon H=3 bars; pooled panel flattens 22 (symbol, timestamp) rows per timestamp. Purge requires `(H+1) × N = (3+1) × 22 = 88` flattened rows on both sides. `XS_REQUIRED_GAP = 88` — correct, verified independently. The two new features do not change H. `run.log` confirms `XS_REQUIRED_GAP=88 asserted`. The walk-forward `train_end_ms = test_start_ms − embargo_ms` is retained. PASS.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION — non-blocking)

`dsr.json`: `dsr=0.0`, `psr=0.0`, `pbo=NaN`, `n_trials=35`, `frac_positive_paths=0.200`. DSR/PSR/PBO sentinels — per `feedback_v3_dsr_mode_artifact.md` informational for EXPLORATION, non-blocking. The substantive read: `frac_positive_paths` **dropped from /089's 0.356 to 0.200** (9 of 45 CPCV paths positive, down from 16/45 — `cpcv_paths.csv` verified). Directionally consistent with a degraded IS gross signal — a genuine negative signal, informational for an EXPLORATION. **The BLOCK on this iteration comes from the engineering-report gross-Sharpe DEFECT (Check 8), not from this check.**

### Check 4 — IC Correlation: PASS

The iter-v3/070 redundancy discipline was applied upstream in the committed IS-only EDA (the correct place for a cross-sectional ranker). The C3 pairwise cross-sectional rank-correlation EDA explicitly DROPPED the candidate `cand_semidev_50` for a 0.80 cross-sectional rank correlation with the incumbent `range_realized_vol_50`. The two features carried forward — `xs_sortino_mom_12` (max |corr| 0.10) and `xs_downbeta_50` (max |corr| 0.19) — are genuinely orthogonal to the existing stack. No new-vs-existing pair exceeds 0.7. PASS.

### Check 5 — ADF Stationarity: PASS

The two new features are cross-sectionally rank-normalized by `build_cross_sectional_panel` (`_xs_rank_normalize` maps each feature to a per-timestamp rank in [0,1]) — a bounded transform with no unit root by construction. The 13 base features are the /059-anchor stack, ADF-cleared at /059. `xs_sortino_mom_12` and `xs_downbeta_50` are ratio/standardized quantities, not raw price levels. PASS.

### Check 6 — Pareto Dominance: PASS

Single-seed EXPLORATION (`seed=42`, `ensemble_size=1`). A 10-seed Pareto front is a CONFIRMATION requirement; `pareto_front.csv` is correctly absent. The brief's F5 falsifier (no single symbol > 50% of OOS book PnL) PASSES decisively: max OOS concentration FILUSDT 11.38%, MANAUSDT 10.43% — no symbol exceeds 12%. PASS.

### Check 7 — Reproducibility: PASS

(1) Commit SHA stamped — setup `a584fdf`, Phase 5.5 gate `55979e7`. (2) Explicit `feature_columns` — `XS_FEATURE_COLUMNS` literal, `_verify_feature_columns()` hard-asserts `len(XS_BASE_FEATURES)==13`, `len(XS_FEATURE_COLUMNS)==15`, both downside features present. (3) Seed literal `seed=42`. (4) PnL spot-check — sampled `out_of_sample/trades.csv` rows; `net_pnl = gross_pnl − fee` reconciles in every sampled row.

**Caveat (not a Check-7 failure, but load-bearing for the BLOCK):** the runner artifacts (comparison.csv, dsr.json, monthly_pnl.csv) are reproducible. But the engineering report's **gross monthly Sharpe figures are NOT runner artifacts** — `run.log` emits only net monthly Sharpe; `comparison.csv` and `dsr.json` carry no gross Sharpe. Every gross monthly Sharpe in both the /089 and /090 reports (+0.1717, +0.5947, +0.5398, +0.2675, +0.3204) is a QE hand-computation with no committed, reproducible derivation. That is the root of the Check-8 DEFECT.

### Check 8 — Hypothesis-Implementation Alignment: PASS (code) — but the engineering report's central diagnostic is DEFECTIVE

**The code matches the brief.** Brief Section 3.1/3.2 specifies `XS_DOWNSIDE_FEATURES = ("xs_sortino_mom_12", "xs_downbeta_50")`, `_engineer_xs_downside_features`, the `expand_downside` panel branch, `XS_FEATURE_COLUMNS`=15, `ITERATION_LABEL="v3-090"` — all present and correctly wired. Brief Section 3.3 specifies the /089 construction is RETAINED — `XS_REQUIRED_GAP=88`, `XS_LISTING_BURNIN_BARS=180`, `XS_QUANTILE_FRAC=0.20`, `XS_HOLD_BARS=3`, `XS_NO_TRADE_BAND=0.020`, `XS_TURNOVER_CEILING=0.138` — all verified unchanged. The single-axis claim holds. On the code-vs-brief axis, Check 8 is PASS.

**But Check 8 also tests whether the iteration's reported result is a sound basis for the Section 8 classification — and here there is a hard DEFECT.** The report's "Decisive question" section states: "/090 OOS gross monthly Sharpe = +0.5398 vs /089's **+0.5947** — a DROP of −0.055. The gross signal was NOT strengthened; it regressed." This is the load-bearing finding driving the Section 8 verdict toward FEATURE-EXPANSION-FALSIFIED (8.2, via F3). It is defective on two counts:

1. **The /089 anchor figure +0.5947 is wrong.** Three independent, merged /089 artifacts state /089's OOS gross monthly Sharpe is **+0.1717**: `briefs-v3/iteration_v3-089/engineering_report.md` ("OOS gross Sharpe +0.1717"); `briefs-v3/iteration_v3-089/review.md` (the /089 Critic FINAL: "OOS gross monthly Sharpe +0.1717"); `diary-v3/iteration_v3-089.md` (cites +0.1717 ~6 times). The /090 brief itself (Section 1, Section 4.1, falsifier F3) anchors on **+0.1717** throughout. The /090 engineering report's +0.5947 contradicts the very brief it is implementing.

2. **+0.5947 is mathematically impossible for /089's OOS gross book.** /089's OOS net monthly Sharpe is −0.09845 (authoritative — `comparison.csv`; reconstructed exactly from the 15-month `out_of_sample/monthly_pnl.csv` as mean/std, sample std, no annualization). /089's OOS fee total is +0.0893 and gross total +0.0567. Mean gross monthly = −0.0021760 + 0.0893/15 = +0.0037773. For OOS gross monthly Sharpe = +0.1717, the gross monthly std must be ≈ 0.02200 (≈ the net std — exactly what you expect adding a small low-variance fee series to the net series); **+0.1717 is internally consistent.** For +0.5947, the gross monthly std must be ≈ 0.00635, requiring `corr(net, fee)` ≈ **−6.8** — impossible. The same arithmetic applies to /090's own reported OOS gross figure +0.5398. **Both reports' gross monthly Sharpe figures are not computed on the per-month basis the net monthly Sharpe uses** — most likely a per-bar or daily aggregation.

**Consequence.** The report's central claim — "the gross signal fell" — compares a /090 gross Sharpe (+0.5398, wrong basis) against a /089 gross Sharpe (+0.5947, wrong basis AND contradicting the merged /089 record). The comparison is not apples-to-apples and the /089 number is simply wrong. The direction of the result may well still be NEGATIVE (`frac_positive_paths` 0.356 → 0.200; IS net Sharpe −0.196 → −0.2305; OOS rank-IC moved only +0.0079, within ±0.34 noise) — but the Section 8 taxonomy (8.2 FEATURE-EXPANSION-FALSIFIED fires via F3 "OOS gross monthly Sharpe ≤ /089's +0.1717") requires a *correct, like-for-like* OOS gross monthly Sharpe for /090. That number does not exist in the artifacts. A methodology DEFECT in the load-bearing diagnostic of a classification-driving report is OVERALL=BLOCK.

## Optional Checks 9–12

**Check 9 — Symbol Exclusion: PASS.** `_verify_xs_universe` hard-asserts `set(XS_UNIVERSE) & set(V3_EXCLUDED_SYMBOLS)` empty; the 22-symbol universe is unchanged from /088/089.

**Check 10 — Feature Isolation: PASS.** `cross_sectional.py` imports only `crypto_trade.config` + lightgbm/numpy/optuna/pandas/pyarrow. No v1/v2 feature imports.

**Check 11 — Forming-Candle Audit: PASS.** The /088/089 `_verify_data_freshness` check is unchanged. The downside features are engineered from historical parquet columns; the PnL `searchsorted(side="right")` makes a forming last bar yield `next_ret = 0.0`.

**Check 12 — Library Version Pinning: PASS.** No new third-party dependency; the two new features are pure pandas/numpy.

## My read on the Section 8 classification

- The engineering report routes /090 toward **8.2 FEATURE-EXPANSION-FALSIFIED** via "F3 fires — OOS gross monthly Sharpe ≤ /089's +0.1717." But the report's own gross-Sharpe figures are on a non-per-month basis and the /089 anchor it cites (+0.5947) contradicts the merged /089 record (+0.1717). The F3 evaluation as performed is invalid.
- **F3 must be re-evaluated with a correctly-computed OOS gross monthly Sharpe for /090** — per-month aggregation of `gross_pnl` from `out_of_sample/trades.csv` (per-bar gross → per-calendar-month sum → 15-month series → Sharpe = mean/std, sample std, no annualization — the exact method the runner uses for net monthly Sharpe and that yields /089's +0.1717) — **compared against /089's correct +0.1717.**
- Once recomputed correctly, the most probable outcome is still that **F3 fires** — the runner-artifact signals (`frac_positive_paths` 0.356 → 0.200; IS net Sharpe −0.196 → −0.2305; the QE's own read that "the small headline OOS improvement is noise within fee-dominated books"; OOS rank-IC delta +0.0079 swamped by ±0.34 noise) all indicate the 2 features did not strengthen the gross signal. So the eventual classification will *probably* still be **FEATURE-EXPANSION-FALSIFIED (8.2)** — but it cannot be *filed* on the current defective evidence.
- **NEGATIVE-vs-INERT:** my read is **NEGATIVE on the gross-signal axis, INERT in net effect.** The axis was to strengthen the gross signal; the runner artifacts indicate it did not. The headline net OOS moved +0.0215 — fee-noise, the INERT signature. The cross-sectional line: /088 OOS −0.54 → /089 OOS −0.10 (a genuine +0.44 construction lift) → /090 OOS −0.08 (a +0.02 step that is NOT a gross-signal lift).

## My read on /091 and the cross-sectional line

The cross-sectional line is **stuck at OOS ≈ −0.08, and /090 is the data point that should force a hard look.** /089's +0.44 lift was a one-time *mechanical* gain (sign fix + turnover reduction — removing drag, not adding edge). /090 was the *first genuine attempt to add gross edge* — a researched, multivariate-contribution-tested, redundancy-cut feature expansion — and the runner artifacts say it did not transfer. The honest concern: **the cross-sectional gross signal in this 22-altcoin universe may be genuinely too thin to monetize at the current cost structure** — a +0.17 gross monthly Sharpe that does not respond to a properly-researched feature expansion is a signal-strength problem, not a construction problem. The pre-registered /091 short-tilt construction is a *construction* lever — it re-slices the same thin gross signal; it does not create gross edge. My recommendation to the QR: do **not** auto-proceed to the /091 short-tilt construction as if /090 were a clean PARTIAL. Treat /090's failure to transfer as evidence that the gross-signal-strength question is now the open one, and consider whether /091 should be a second, genuinely-different gross-signal attempt (or a universe-level reconsideration) rather than a construction re-slice — and whether the /087-closeout "escalate to the user for a paradigm decision" contingency is closer than the /089 diary judged.

## Recommendations to QR

This iteration is OVERALL=BLOCK on a methodology DEFECT in the engineering report's central diagnostic. The run itself is clean — the BLOCK is not "the result is bad," it is "the load-bearing number is wrong and the classification cannot be filed on it." Three process-level fixes:

1. **Make gross monthly Sharpe a reproducible runner artifact, not a hand-computation.** The single root cause of this BLOCK is that gross monthly Sharpe is computed by hand in the engineering report with no committed derivation — so the /089 report got +0.1717, the /090 report got +0.5947 for the *same* /089 data, and neither is on the per-month basis the net monthly Sharpe uses. Per `feedback_v3_methodology_axis_integration_test.md`, any metric that drives a falsifier (F3) must be a runner output. The cross-sectional runner must emit `gross_monthly_sharpe` to `comparison.csv` and `dsr.json`, computed by the *identical* aggregation as `monthly_sharpe`, for both IS and OOS, with a smoke test asserting `gross_monthly_sharpe` and `monthly_sharpe` use the same code path.

2. **Before filing the Section 8 classification, recompute /090's OOS gross monthly Sharpe on the per-month basis and re-evaluate F3 against /089's correct +0.1717.** The diary must not be written on the engineering report's +0.5398-vs-+0.5947 comparison. The corrected F3 evaluation will most probably still fire — but it must be filed on a correct number. If the recompute shows /090 OOS gross monthly Sharpe > /089's +0.1717, F3 does not fire and the classification changes — which is exactly why the recompute is mandatory.

3. **For the /091 brief: do not anchor on the /090 engineering report's gross figures, and re-state the cross-sectional line's trajectory honestly.** The /091 brief must anchor on /089's correct OOS gross monthly Sharpe +0.1717 and on /090's recomputed per-month gross figure — never the +0.5947/+0.5398 pair. The /091 brief should state plainly that /090 was the first genuine gross-edge attempt on the cross-sectional line and it did not transfer — the line is two mechanical gains (/089 sign fix + turnover) plus one failed edge attempt, not an unbroken ascent. Whether /091 proceeds to the short-tilt construction or pivots to a second gross-signal attempt / universe reconsideration is the QR's EDA-grounded call — but it must be made with the honest trajectory.
