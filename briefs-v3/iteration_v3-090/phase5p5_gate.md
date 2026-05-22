# Phase 5.5 Gate — iter-v3/090 (INDEPENDENT QE GATE — supersedes QR self-gate `662d7cc`)

**QE review date**: 2026-05-17
**Brief SHA**: `bb425a5`
**EDA SHA**: `cecbc8f`
**Setup SHA**: `a584fdf`
**Branch**: `iteration-v3/090`
**Ruff fix**: 2 fixable violations in `analysis/iteration_v3-090/b2_feature_selection_eda.py` caught and fixed by QE before gate issuance (F401 unused import `V3_FEATURE_COLUMNS_TOP_N`; I001 un-sorted import block)

---

OVERALL: PASS

---

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24` (`OOS_CUTOFF_MS = 1742774400000`) and `training_months = 24` confirmed immutable; IS (2022-03 to 2025-02, 37 months) and OOS (2025-03 to 2026-05, 15 months) windows stated in absolute dates.
- Section 0.5 (Iteration Type): PASS — EXPLORATION, cycle-3 slot #9 of 10, single-seed seed=42, `--n-trials 35`, wall-clock budget ≤ 2h. Correctly characterised as GROSS-SIGNAL-STRENGTHENING build on the RETAINED /088 cross-sectional architecture + /089 cost-aware construction.
- Section 1 (Hypothesis): PASS — specific, falsifiable, one-paragraph claim. IS composite IC-IR lift +9.6% (+0.1981 → +0.2171); IS quintile L-S spread Sharpe +0.0219. The /089 book is gross-positive (+0.1717) and fails net only on fees; the two orthogonal downside features strengthen the gross spread without blowing the 0.138 turnover ceiling. Honest scope: single feature-expansion axis; short-tilt construction deferred to /091.
- Section 2 (IS-Only Evidence): PASS — two committed EDA scripts (SHA `cecbc8f`), both IS-only (`df[df["open_time"] < OOS_CUTOFF_MS]`, 180-bar burn-in, confirmed in source). Evidence is genuinely MULTIVARIATE-INCREMENTAL (iter-v3/070-correct): `_composite_ic_series` computes the IC of the FULL sign-aligned composite (anchor + candidate family) vs the forward return — the joint multivariate effect, not univariate Spearman. B-block delta rows are composite-WITH minus composite-WITHOUT the candidate family. C-block (`b2_feature_selection_eda.py`) applies C1 greedy forward selection (stopping at marginal d(IC-IR) ≤ 0.005), C2 leave-one-out, C3 pairwise redundancy (cross-sectional rank correlation, not time-series), and the C4 orthogonal-subset tiebreak. Numerical tables confirmed committed: A3 within-half IC bottom 0.0576 vs top 0.0141 (4.1×); B2 d composite IC-IR +0.0306 / d spread Sharpe +0.0215 (strongest family); C3 `cand_semidev_50` xs-rank-corr 0.8014 with incumbent `range_realized_vol_50`; C4 orthogonal pair IS IC-IR +0.2171 / spread −0.0535 vs all-3's −0.0539 (identical to 4 d.p. — redundant candidate costs ~0 spread Sharpe). No univariate category-matching.
- Section 3 (Proposed Changes): PASS — single axis (feature expansion only). Precise, wired spec: `XS_DOWNSIDE_FEATURES = ("xs_sortino_mom_12", "xs_downbeta_50")`, windows a-priori (50/12), new function `_engineer_xs_downside_features(df)`, `expand_downside: bool = False` parameter (legacy path byte-identical), `XS_FEATURE_COLUMNS` = 15, `ITERATION_LABEL = "v3-090"`, `_verify_feature_columns()` asserts all 4 invariants. All /089 construction constants RETAINED verbatim (quintile=0.20, hold=3, band=0.020, ceiling=0.138).
- Section 4 (Expected OOS Impact): PASS — dual evaluation (absolute +1.0/+1.0 floor + proximate net-positive-OOS goal + architecture-internal diagnostics). /089 cross-sectional book as ANCHOR 1; /059 as ANCHOR 2 with comparability caveat. Five falsifiers F1–F5 pre-registered with numerical thresholds; F2 (IS turnover > 0.138) is the RETAINED hard gate; F3 (OOS gross ≤ +0.1717) and F4 (OOS net ≤ −0.0985) are the central hypothesis falsifiers; F-ASYM is correctly a /091-input measurement. Honest modal prediction: OOS net monthly Sharpe [−0.10, +0.20], plausibly net-positive but well below +1.0 floor.
- Section 5 (Risk Mitigation): PASS — /090-specific addition (feature-overfit/colsample-dilution control via multivariate-contribution selection, dropping the 0.80-redundant `cand_semidev_50`) tabulated with IS-EDA simulated effect. RETAINED /089 turnover controls and structural cross-sectional controls tabulated with /089 simulated effect.
- Section 6 (Risk Management Design): PASS — legacy 7-gate stack deferred (would confound the feature-expansion measurement — same honest scoping /088/089 made). /090 risk apparatus: dollar-neutral + inverse-vol + vol-targeting + quintile diversification + overlapping-hold tranching + no-trade band + hard turnover ceiling + multivariate-contribution feature-selection discipline.
- Section 7 (Failure-Mode Prediction): PASS — five probability-weighted scenarios with honest modal outcome (≈45% feature-expansion-works-sub-floor; ≈20% net-positive-sub-floor; ≈20% F3/F4-fires; ≈10% marginal-mechanical; ≈5% full-success). Dominant failure mode named (IS composite IC-IR lift does not transfer OOS — the residual iter-v3/070 colsample risk even after the redundancy cut). Not over-weighted.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — five-class LOCKED taxonomy in disjunctive precedence with numerical gates per class (SUSPICIOUS, FEATURE-EXPANSION-FALSIFIED, FEATURE-EXPANSION-VALIDATED-PROMISING with FULL/FOUNDATION subcases, FEATURE-EXPANSION-PARTIAL, NULL). Explicit statement: EXPLORATION cannot update BASELINE_V3.md.
- Section 9 (Library Stack): PASS — LightGBM (LGBMRanker, lambdarank), Optuna, pandas/numpy. No new third-party dependency. No mlfinlab/mlfinpy/pypbo/fracdiff. `XS_REQUIRED_GAP=88` unchanged; no walk-forward fallback triggered (H unchanged at 3).
- Section 10 (QR Audit Trail): PASS — Section 10.1 records orchestrator direction-steer + QR design ownership (QR rejected /089-scoped G4 trailing-return channels as iter-v3/070 dead-path). Section 10.2 six literature sources with IDs. Section 10.3 no-cheating audit. Section 10.4 honest senior read.

---

## Code-Readiness Checks

### CR-1 — Look-ahead audit of `xs_sortino_mom_12` and `xs_downbeta_50`

PASS. Both features in `_engineer_xs_downside_features` (`cross_sectional.py` lines 273–329) are strictly backward-looking:

- `xs_sortino_mom_12 = (close / close.shift(lb) - 1) / semidev_50.replace(0, nan)`. `semidev_50 = neg.rolling(win).std()` where `neg = ret_1.where(ret_1 < 0, 0)`. Every transform (`pct_change`, `where`, `rolling().std()`, `shift(lb)`) looks back. Value at bar t uses only bars ≤ t.
- `xs_downbeta_50 = cov_d / var_d.replace(0, nan)`. `cov_d = r_d.rolling(win, min_periods=15).cov(b_d)`, `var_d = b_d.rolling(win, min_periods=15).var()`. `r_d` and `b_d` are masked via `where(down_mask)` where `down_mask = btc_ret_1 < 0` — a past observation. All rolling windows are backward-looking.
- `btc_ret_3d` (the input): a historical observation in the v3 parquet; converted to a ~1-bar proxy via a monotone transformation.

The no-look-ahead unit test `test_iter090_downside_features_no_lookahead` (test file lines 1074–1098) is genuinely adversarial: engineers features on a 400-bar full panel and a 300-bar prefix; asserts every non-NaN overlapping row is bit-identical to `rtol=1e-9, atol=1e-12`. Both features had > 50 overlapping non-NaN comparison rows (assertion enforced). Test passed (40/40). Appending future bars cannot alter a past row's value — confirmed both by construction analysis and by the unit test.

Cross-sectional rank-normalization in `build_cross_sectional_panel` ranks within each timestamp only — no future timestamp accessed.

### CR-2 — ITERATION_LABEL and 15-feature set

PASS. `ITERATION_LABEL = "v3-090"` at line 95 of `run_cross_sectional_v3.py`. `XS_BASE_FEATURES` = 13 columns (V3_FEATURE_COLUMNS_TOP_N minus btc_ret_14d). `XS_FEATURE_COLUMNS = XS_BASE_FEATURES + list(XS_DOWNSIDE_FEATURES)` = 15. `_verify_feature_columns()` runs at startup (line 680) and hard-asserts all 4 invariants. Test `test_iter090_runner_feature_count` validates at import time.

### CR-3 — No-cheating verification

PASS. All /090 parameters are IS-selected or a-priori:
- Feature identities: C1 greedy forward selection + C2 leave-one-out + C3/C4 redundancy cut — all IS-only.
- Windows (50, 12): a-priori, matched to existing 50-bar v3 feature windows; the EDA used identical windows.
- Sign alignment: derived from IS rank-IC (X0_feature_is_ic.csv), IS-only.
- Drop of `cand_semidev_50`: C3 pairwise redundancy (xs-rank-corr 0.8014) and C4 tiebreak — IS-only. A redundancy cut, not an OOS-tuned cut.
- All /089 construction constants: retained from /089-IS-grounded parameters; not re-tuned.
- Both EDA scripts: strict `df[df["open_time"] < OOS_CUTOFF_MS]` filter applied before any computation. Forward-return target `fwd_H = close.shift(-H)/close - 1` computed AFTER `_engineer_candidates` — correct order; target is not used as feature input.
- QR sees OOS for the first time in Phase 7.

### CR-4 — /089 construction constants retained unchanged (single-axis)

PASS. Verified in `cross_sectional.py`:
- `XS_REQUIRED_GAP = 88` — unchanged.
- `XS_LISTING_BURNIN_BARS = 180` — unchanged.
- `XS_QUANTILE_FRAC = 0.20` — unchanged.
- `XS_HOLD_BARS = 3` — unchanged.
- `XS_NO_TRADE_BAND = 0.020` — unchanged.
- `XS_TURNOVER_CEILING = 0.138` — unchanged; re-used as F2 hard gate.
- `expand_downside=False` default preserves /088/089 byte-identical legacy path.
- Both `build_cross_sectional_panel` calls in `run_cross_sectional_v3.py` (main backtest + smoke test) pass `expand_downside=True`.

### CR-5 — Tests and ruff

Tests: 40/40 PASS (1.91s). Four new /090 tests: `test_iter090_downside_feature_constants`, `test_iter090_engineer_adds_both_downside_features`, `test_iter090_downside_features_no_lookahead` (the load-bearing look-ahead guard), `test_iter090_runner_feature_count`. All 36 prior /088+/089 tests still pass — no regression.

Ruff: the QR self-gate (`662d7cc`) incorrectly claimed ruff was clean. The QE found 2 fixable violations in `analysis/iteration_v3-090/b2_feature_selection_eda.py`: F401 unused import `V3_FEATURE_COLUMNS_TOP_N` and I001 un-sorted import block. Both fixed by QE (`ruff check --fix`). After fix: `uv run ruff check analysis/iteration_v3-090/ src/crypto_trade/strategies/ml/cross_sectional.py run_cross_sectional_v3.py tests/strategies/ml/test_cross_sectional.py` — **All checks passed**. Tests still 40/40.

---

## EDA Methodology — Multivariate vs Univariate Confirmation

`_composite_ic_series` at each timestamp computes the IC of the full sign-aligned equal-weight rank composite (anchor + candidate family) against the forward return. The delta rows in B1_B3_family_incremental.csv are the JOINT incremental effect of each candidate family on the composite — this is not a univariate Spearman of the candidate features alone. The C3 pairwise redundancy check uses cross-sectional rank correlation (per-timestamp, averaged) — the correct measure for a pooled-panel ranker where features are cross-sectionally normalized. IS sign-alignment via X0 is correctly used only for composite construction, not for selection. All selection decisions (C1 acceptance threshold, C2 LOO floor, C3 redundancy cut) are applied on IS data, consistent with the no-cheating audit.

---

## Note on QR Self-Gate

The QR self-gate (`662d7cc`) reached OVERALL PASS but incorrectly claimed ruff was clean. The QE's independent review caught the 2 violations and fixed them before issuing this gate. This is the expected function of the Phase 5.5 gate: a separate agent independently verifies. The substantive gate verdict is the same (PASS); the ruff fix is logged here for transparency.

---

OVERALL: **PASS**. Phase 6 may proceed.
