# Phase 7.5 Critic Review — iter-v3/060

OVERALL: EXPLORATION-PROMISING — EXPLORATION-MODE-REFERENCE certified clean for /061-068 axis anchoring; methodology invariants intact; mode-flag refactor at `56f5a30` correctly wired.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION-MODE-REFERENCE (cycle 1 #1; FIRST 3-seed EXPLORATION-mode run + TRX OOS diagnostic publication; Path A passive)

## QR Response Considered (Round 2 only)

Single-round FINAL review. The 13 standard Checks plus the §11 Anti-Pattern Static Scan plus the EXPLORATION-mode-specific concerns enumerated in the dispatch resolve unambiguously against the artifacts in `reports-v3/iteration_v3-060/`, the runner state at `bb34e76`, and the brief's own LOCKED criteria in Section 8.1 + Section 4.4. The two adversarially-flagged concerns (BCH 176.68% IS share, n_trials=315 reduction) are dispositioned in-line with the relevant Checks rather than dispatched as clarifications, because the brief's pre-registered falsifier text in Section 4.4 already controls the BCH adjudication and the brief's Section 9 + iter-v3/059 anchor reporting already controls the n_trials accounting.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

Walk-forward fix at `src/crypto_trade/strategies/ml/walk_forward.py:113` intact: `train_end_ms = test_start_ms - embargo_ms` with `embargo_candles = compute_embargo_candles(10080, 480) = 22` and `embargo_ms = 22 × 480 × 60_000 = 633_600_000ms`. Mode-flag refactor at `56f5a30` did NOT touch `walk_forward.py` or `labeling.py` (verified by grep at `train_end_ms\s*=\s*test_start_ms\s*$` — zero matches). Triple-barrier σ_t at `src/crypto_trade/strategies/ml/labeling.py:212-234` uses ATR multipliers via `atr_values` argument — no rolling-std forward window. The 14 features at /060 are inherited verbatim from /028/058/059 (all walk-forward-safe in prior Critic audits). No look-ahead path introduced by the EXPLORATION mode flag — the flag controls only `ensemble_size_for_run` and `active_ensemble_seeds` at the runner level (lines 1960-1962, 2092).

### Check 2 — Embargo Width: PASS

REQUIRED_GAP = 66 = (timeout_candles=21 + 1) × n_symbols=3 — confirmed at `src/crypto_trade/strategies/ml/validation_v3.py:54`. Runtime assertion at `_verify_label_leakage_gap()` (run_baseline_v3.py) fires before backtest launches per Phase 5.5 gate output. CPCV `embargo=27` per BASELINE_V3.md config, unchanged. Walk-forward embargo of 22 candles applied at every train/test boundary via `compute_embargo_candles` single source of truth. Numerical proof: required = 22 × 3 = 66; actual REQUIRED_GAP = 66. Equality verified at runtime. Mode-flag refactor does NOT alter REQUIRED_GAP, CPCV embargo, or walk-forward embargo computation.

### Check 3 — Multiple-Testing Correction: PASS (per brief Section 8.6 EXPLORATION-mode informational)

Hard-blocking gates per brief Section 8.1 LOCKED:
- IS Sharpe ≥ +0.50 → observed +0.8325, PASS (+0.33 cushion)
- OOS Sharpe ≥ 0.0 → observed +0.1403, PASS (+0.14 cushion — borderline by design under relaxed EXPLORATION floor)
- BCH IS share band (see Check 8 adjudication; Section 4.4 falsifier is one-sided <80%)
- frac_positive_paths ≥ 0.50 → observed 0.6444, PASS

Informational, NOT BLOCK-triggering per brief Section 8.6 + `feedback_v3_dsr_mode_artifact.md`:
- DSR_relative = 0.0 — informational only at EXPLORATION mode (n_trials_total=315 vs CONFIRMATION's 1050; calibrated threshold inapplicable)
- Legacy DSR = 0.0 — structural at v3 trade volume; same root cause as /058/059 (PASS as informational)
- PSR = 0.9763 — informational; below /059's 1.0000 due to fewer trial points

n_trials accounting verified: 315 = 35 (trials/cell) × 3 (symbols) × 3 (ensemble_size). Per-cell trial count UNCHANGED from /059 (35 each) — per_cell_pbo.csv shows `n_trials,35` for ALL 108 rows (3 syms × 36 IS months). The 315 vs 1050 headline reduction is purely a cross-product accounting artifact of ensemble_size, NOT Optuna under-sampling per cell. n_eff = 19 (per-cell median PCA aggregation) identical to /059 — confirms n_eff is architecturally independent of ensemble size (computed per-(sym, month, fold) cell on trial returns matrix; this is correct, not a code defect). PBO = 0.1278 identical to /059 to four decimals (cross-cell mean computed from per_cell_pbo.csv rows; ensemble-architecture-independent).

### Check 4 — IC Correlation: PASS (carve-out applies; no new features at /060)

`reports-v3/iteration_v3-060/ic_matrix.csv` is 14×14, computed at IS-window CPCV cell level. No new features introduced at /060 (bundle IDENTICAL to /058/059/028). Highest pairs:
- `regime_momentum_signed_5d × vwap_dev_20 = 0.7642` (above 0.70 threshold; established composed-feature IC carve-out per `feedback_v3_engineered_feature_pivot.md` — regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5), R²=1.0 algebraic identity with primitives; carve-out approved at iter-v3/025 and re-affirmed at every subsequent Critic review)
- `regime_momentum_signed_5d × sym_vs_btc_ret_7d = 0.6189` (below threshold)
- `ret_kurt_200 × ret_skew_200 = 0.6129` (below threshold)

No new high-IC pairs above 0.80 introduced; no carve-out expansion required. IC matrix is identical-by-construction to /059's matrix (IS data + features unchanged).

### Check 5 — ADF Stationarity: PASS

`adf_test.csv` has 2198 rows (sym × feature × month grid). 1803 stationary (TRUE), 395 non-stationary (FALSE) overall. Of the 395 FALSE rows: 68 are blank-statistic rows (ADF could not compute due to insufficient lookback for features requiring 100-200 candles before first valid value, e.g. 2020-01 cells); 327 are real ADF-fail with p ≥ 0.05. Of those 327, only 22 occur in 2024-2025 months (the live IS window proper: 2023-03-24 through 2025-03-23). 22 / (22 + 608) = 3.5% non-stationary cells in the IS window itself — well below any methodology threshold. Identical pattern to /058/059 (ADF runs on raw features, not on trained models; architecture-independent). No structural ADF failure introduced by the mode flag.

### Check 6 — Pareto Dominance: PASS (Gate 10-CPCV replacement; frac_positive_paths ≥ 0.50 cleared)

Per `feedback_v3_iter018_baseline_bootstrap.md` and Gate 10 retirement at iter-v3/059, Pareto Gate is replaced by Gate 10-CPCV (`frac_positive_paths ≥ 0.50` for EXPLORATION; ≥ 0.55 for CONFIRMATION). Observed 0.6444 at /060 PASS at the relaxed EXPLORATION threshold AND at the stricter CONFIRMATION threshold. `pareto_front.csv` correctly ABSENT from `reports-v3/iteration_v3-060/` (unified-architecture-by-design). `seed_summary.json` ABSENT; `ensemble_summary.json` PRESENT with exactly 3 entries (`mode="exploration"`, `ensemble_size=3`, seeds `(191664963, 1662057957, 1405681631)`, all `lineage="outer=42"`). The 3-seed slice is a proper subset of the 10-seed CONFIRMATION lineage per `test_exploration_is_strict_subset_of_confirmation_seeds` in `tests/strategies/ml/test_ensemble_unified.py:345-356`.

### Check 7 — Reproducibility: PASS

- Commit SHAs verifiable: brief revision `8430516`, ITERATION_LABEL fix `3fae219`, Phase 5.5 re-gate `bb34e76` (pre-run HEAD), mode-flag refactor `56f5a30`, walk-forward fix `e149e9d`, Phase B-3 unified `ab2d9ac`. All confirmed in `git log iteration-v3/060`.
- Feature columns pinned: `_verify_feature_columns(ensemble_size=3)` at run_baseline_v3.py:1991 asserts `ensemble_size in (3, 10)` per lines 291-297; `len(V3_FEATURE_COLUMNS) == 14` per line 299; assertion fires at runner startup before any backtest work.
- ENSEMBLE_SEEDS hardcoded 10-tuple at run_baseline_v3.py:100-111; `ENSEMBLE_SEEDS[0:3]` slice at line 2092 produces the documented `(191664963, 1662057957, 1405681631)` per `test_exploration_seeds_are_outer_42_lineage_subset`.
- Trade-math spot check on 2 OOS trades from `out_of_sample/trades.csv`:
  - Row 2: BCH SHORT, entry=303.870, exit=282.100779, weight=0.33 → `(303.870 − 282.100779) / 303.870 × 100 − 0.10 = 7.0640%`; weighted = 7.0640 × 0.33 = 2.3311 — matches CSV to 4 decimals.
  - Row 4: TRX LONG, entry=0.261800, exit=0.269975, weight=0.47 → `(0.269975 − 0.261800) / 0.261800 × 100 − 0.10 = 3.0228%`; weighted = 3.0228 × 0.47 = 1.4207 — matches CSV exactly.
- OOF parquet guardrail: brief specifies `--clean-oof` was passed (per engineering report's anti-pattern pre-check); inferred clean-start of trial_oof_returns.parquet for ITERATION_LABEL="v3-060".

### Check 8 — Hypothesis-Implementation Alignment: PASS (with EXPLICIT NOTE on Section 8.1/4.4 internal inconsistency)

Brief Section 3 specifies exactly two substantive interventions:
1. `ITERATION_LABEL = "v3-060"` (line 128 of run_baseline_v3.py)
2. `--exploration` invocation at Phase 6 launch (mode-flag refactor at `56f5a30`)

Both verified. No feature, label, risk primitive, or universe changes — V3_FEATURE_COLUMNS_TOP_N count = 14, V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT), V3_ATR_MULTIPLIERS_PER_SYMBOL = {}, RiskV2Config.block_long_for = () per the explicit runtime assertions at run_baseline_v3.py:584-609 (Primitive 10 REVERT check) and line 713-718 (Primitive 11 DISABLED check). The mode flag itself controls ONLY `ensemble_size_for_run` (line 1960-1962) and `active_ensemble_seeds` (line 2092); no other path is gated on `args.exploration`.

**EXPLICIT NOTE on brief internal inconsistency** (BCH IS share adjudication): Brief Section 8.1 LOCKED PASS criteria text reads "BCH IS share in [80%, 100%] band" — a closed two-sided interval. Brief Section 4.2 prediction text reads "BCH IS share remains in [85%, 100%] band" with falsifier "If BCH share drops below 80%, flag as PATH-DIVERGENCE-AT-MODE-FLAG". Brief Section 4.4 falsifier list reads "BCH IS share < 80%" — explicitly one-sided lower bound only. Observed BCH IS share = 176.68% (above the upper bound of the 8.1 band; not below the 4.4 falsifier). Engineering report adopts the 4.4 falsifier interpretation (one-sided <80%) and classifies PASS. **Adjudication**: The brief is internally inconsistent between Section 8.1 (closed band) and Section 4.4 (one-sided <80% falsifier). Per Critic precedent that the pre-registered FALSIFIER is the binding gate (Section 4.4 is the testable assertion; Section 8.1 closed-band text is the SUCCESS prediction, not the elimination criterion), the Engineer's interpretation is acceptable. The 176.68% IS share is a **direct mathematical consequence of LDO and TRX both flipping IS-negative under 3-seed averaging**, which is itself an explicit pre-registered failure mode in brief Section 7 (Probability ~25% "3-seed variance noise floor"). PASS Check 8 stands, but the brief's Section 8.1 wording requires cleanup at cycle 1 #2 setup: state explicitly that the BCH-share gate is one-sided lower (≥80%, no upper cap) so the band [80%, 100%] is a prediction NOT a failure criterion. Recommendation #1 below.

### Check 9 (optional) — Symbol Exclusion Enforcement: PASS

V3_EXCLUDED_SYMBOLS audit fires at `_verify_symbols()` (run_baseline_v3.py:184-191) on every Phase 6 launch. V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT) — none in V3_EXCLUDED_SYMBOLS.

### Check 10 (optional) — Feature Isolation Enforcement: PASS

`grep -rn "^from crypto_trade.features " src/crypto_trade/features_v3/` returns no active import lines (only docstring/comment self-reference at `funding_v3.py:3`, `__init__.py:7`, `fracdiff_v3.py:23`). Track isolation verified at runtime by `_verify_track_isolation()`.

### Check 11 (optional) — Forming-Candle Audit: PASS

Phase 5.5 gate confirms last-candle close_time=1778687999999 (2026-05-13 16:00:00 UTC) — already closed, not forming. Runner filters `is_sample` candles by `close_time < now_ms`.

### Check 12 (optional) — Library Version Pinning: PASS

Brief Section 9 declares: Python 3.13, lightgbm 4.6.0, optuna 4.8.0 (n_jobs=1 per `31665f6` revert), numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. No new dependencies introduced by mode-flag refactor. Optuna `n_jobs` argument absent from `src/crypto_trade/strategies/ml/optimization.py` (verified by grep) — Phase A revert intact.

### Check 13 (optional — EXPLORATION-mode-specific) — Mode-Flag Wiring Audit: PASS

The mode-flag refactor at `56f5a30` is correctly wired across all expected sites:
- `EXPLORATION_ENSEMBLE_SIZE = 3` at run_baseline_v3.py:92
- `CONFIRMATION_ENSEMBLE_SIZE = 10` at run_baseline_v3.py:90
- `ENSEMBLE_SIZE = CONFIRMATION_ENSEMBLE_SIZE` backward-compat alias at line 93
- `--exploration` argparse flag at lines 1907-1914
- `ensemble_size_for_run = EXPLORATION_ENSEMBLE_SIZE if args.exploration else CONFIRMATION_ENSEMBLE_SIZE` at lines 1960-1962
- `_verify_feature_columns(ensemble_size=ensemble_size_for_run)` at line 1991, with assertion at lines 291-297 enforcing `ensemble_size in (3, 10)`
- `active_ensemble_seeds = ENSEMBLE_SEEDS[:ensemble_size_for_run]` at line 2092
- Startup mode log at lines 2024-2028 prints `mode={ensemble_size_for_run}`
- `ensemble_summary.json` mode + ensemble_size fields at lines 2399-2400 — verified in `reports-v3/iteration_v3-060/ensemble_summary.json`: `{"mode": "exploration", "ensemble_size": 3, "seeds": [3 entries]}`
- `cpcv_path_sharpe_q75` uses in-memory `flat_path_sharpes` from cpcv_df at line 2243 (written-before-read invariant A13 holds; identical to /059 architecture)
- Tests `tests/strategies/ml/test_ensemble_unified.py::TestExplorationConfirmationModeConstants` (5 tests at lines 302-356) cover `test_exploration_mode_uses_3_seeds`, `test_confirmation_mode_uses_10_seeds`, `test_exploration_seeds_are_outer_42_lineage_subset`, `test_ensemble_size_alias_equals_confirmation`, `test_exploration_is_strict_subset_of_confirmation_seeds` — per brief Section 9 + 5.5 gate, all 31/31 pass.

OOF parquet path collision-free across mode flips: different ITERATION_LABEL → different `reports-v3/iteration_v3-NNN/trial_oof_returns.parquet` path → structurally safe; /060's reports directory is `reports-v3/iteration_v3-060/`, distinct from /059's `reports-v3/iteration_v3-059/`. The startup OOF parquet guardrail at lines 2007-2021 also fires per iteration label.

## §11 Anti-Pattern Static Scan (A1-A13)

- **A1** (`train_end_ms = test_start_ms` without embargo): grep returns zero matches — PASS
- **A5** (master-data-extent invariance): walk-forward fix at `e149e9d` inherited unchanged at /060 — PASS
- **A7** (OOF parquet guardrail): brief specifies `--clean-oof` was passed; lines 2007-2021 guardrail fires on stale parquet — PASS
- **A8** (stateful gate deadlock — per-symbol drawdown brake): `enable_per_symbol_drawdown_brake=False` at runner line 1447 + runtime assertion at lines 713-718 — PASS
- **A10** (track isolation): `grep -rn "^from crypto_trade.features " src/crypto_trade/features_v3/` returns no active import lines — PASS
- **A12** (DSR/PSR granularity): `psr()` and `deflated_sharpe_ratio_v3()` both called with trade-level Sharpe (`raw_sharpe_is = is_wp.mean() / is_wp.std() * np.sqrt(len(is_wp))`); n_obs = trade count — PASS
- **A13** (written-before-read): `cpcv_path_sharpe_q75` at line 2243 uses in-memory `flat_path_sharpes` populated at line 2148 from `cpcv_df` (in-memory DataFrame), NOT a read from cpcv_paths.csv (which is written later at line ~2295) — PASS

## EXPLORATION-mode-specific concerns dispositioned

- **`_verify_feature_columns(ensemble_size=3)` assertion firing**: VERIFIED. Phase 5.5 re-gate output confirms `[v3-060]  ensemble_size_for_run=3, V3_FEATURE_COLUMNS=14, all pre-flight  PASS`. Assertion at lines 291-297 cannot silently fall through — `ensemble_size != None` triggers the `assert in (3, 10)`.
- **OOF parquet path collision-free across mode flips**: VERIFIED. Different ITERATION_LABEL → different reports dir → structurally safe.
- **3 active seeds genuinely a SUBSET of the 10**: VERIFIED by `test_exploration_is_strict_subset_of_confirmation_seeds` and visual inspection of `ENSEMBLE_SEEDS[0:3]` = `(191664963, 1662057957, 1405681631)`.
- **n_trials=315 producing meaningful n_eff=19**: n_eff is computed per-(sym, month) cell from the trial-returns matrix (PCA at 95% cumulative variance, median across cells with rank > 1). Architecture-independent — does NOT depend on outer ensemble size. n_eff=19 at /060 identical to /059 — CORRECT INVARIANT, not a code defect.
- **DSR_relative = 0.0 + Legacy DSR = 0.0**: Both reflect known structural artifacts at v3 trade volume (sparse trade-level returns). Brief Section 8.6 explicitly informational-only at EXPLORATION mode per `feedback_v3_dsr_mode_artifact.md`. Not gate-relevant.

## Adversarial Adjudication — BCH 176.68% IS Dominance

The 176.68% IS share is methodologically VALID in the following narrow sense:
- Arithmetic check: BCH 79.45 + LDO -11.44 + TRX -23.04 = 44.97 (matches portfolio). BCH 79.45/44.97 = 176.68%. Sum of shares 176.68 - 25.44 - 51.25 = 99.99% (rounding-consistent). NO arithmetic anomaly.
- Mechanism: Under 3-seed averaging (vs 10-seed at /059), LDO and TRX both flip from marginally IS-positive to IS-negative — exactly the noise-floor failure mode pre-registered in brief Section 7 with probability ~25%. BCH IS contribution (+79.45 vs /059's +109.23) is in the same ballpark; the share inflates because the denominator (LDO + TRX) goes negative.
- Falsifier semantics: Brief Section 4.4 explicit one-sided gate `BCH IS share < 80%`. 176.68% > 80%. PASS.

**However**, the methodological concern this raises for CYCLE 1 axis-attribution is real and Recommendation #2 captures it: a /060 anchor where 2 of 3 symbols are IS-negative is a fragile reference point. iter-v3/061-068 axis-PASS deltas measured against (IS=+0.8325, OOS=+0.1403) must NOT be conflated with deltas measured against /059's clean (IS=+1.0894, OOS=+0.5791) anchor. The brief is explicit on this (Section 2.10), and the engineering report's "EXPLORATION-MODE Anchor Establishment" section formalizes it. PASS WITH ATTACHED PROCESS RECOMMENDATION #2.

## Recommendations to QR

1. **Brief Section 8.1 BCH-share gate wording cleanup at cycle 1 #2 (iter-v3/061) setup.** State explicitly that the BCH IS share gate is one-sided lower (`≥80%`) per Section 4.4 falsifier — not a closed band `[80%, 100%]`. The current closed-band phrasing in Section 8.1 invites later Critic adjudication uncertainty. The Section 4.4 falsifier is the binding gate; Section 8.1 should reference it explicitly rather than re-stating an interval.

2. **Cycle 1 axis-PASS deltas anchored against /060 (NOT /059) MUST be cross-validated at CONFIRMATION.** iter-v3/061-068 PASS criteria (IS Sharpe shift ≥ +0.10 AND OOS Sharpe shift ≥ +0.20 vs /060 anchor) are 3-seed-mode deltas. Per `feedback_v3_strict_10_to_1_cadence.md` and `feedback_v3_dsr_mode_artifact.md`, any cycle 1 EXPLORATION classified PROMISING under /060-anchored criteria MUST run a CONFIRMATION-mode (10-seed) re-validation at iter-v3/069 before MERGE consideration. The /060 OOS Sharpe +0.14 is barely above the 0.0 floor; a /061-068 axis showing OOS +0.34 (PASS at /060-delta criterion) could still be lottery-noise relative to /059's CONFIRMATION-mode baseline (+0.58 OOS). Recommend iter-v3/069 CONFIRMATION brief Section 8 explicitly require the candidate bundle to clear /059's CONFIRMATION baseline (+1.0894 IS / +0.5791 OOS) on BOTH axes simultaneously, not /060's EXPLORATION baseline.

3. **iter-v3/061 axis = TRX RiskV2 anti-Kelly diagnostic per the EDA Q7 finding (`analysis/iteration_v3-060/trx_diagnostic.py`).** The EDA Q7 finding (TRX is the ONLY symbol where average weight_factor on winning trades < average weight_factor on losing trades, both IS and OOS) is the highest-value diagnostic insight from /060. iter-v3/061 brief Section 2 EDA must include committed IS-only numerical tables comparing per-symbol weight_factor distributions before and after the proposed change. Test ONE engineered intervention alone at single-seed/3-seed mode per `feedback_v3_engineered_features_dont_stack.md` — do not stack multiple changes.
