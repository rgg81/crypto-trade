# Phase 5.5 Gate — iter-v3/082

OVERALL: BLOCK

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`, anchor /059. Correctly declares IS/OOS windows. IS mask in EDA verified (`open_time < OOS_CUTOFF_MS`).
- Section 0.5 (Iteration Type): PASS — EXPLORATION, cycle-3 #1 of 10, 2h wall-clock hard cap, `--exploration --n-trials 35`, ENSEMBLE_SIZE=3.
- Section 1 (Hypothesis): PASS — single-sentence, specific: 4-member funding-rate family (14→18 features) will lift IS monthly Sharpe +0.10–+0.35 via leveraged-positioning-crowding signal absent from the 14 OHLCV-derived anchor features. Not vague.
- Section 2 (IS-Only Evidence): PASS — committed EDA `analysis/iteration_v3-082/funding_family_eda.py` (SHA `37d4da8`) + 6 result CSVs (t1–t6). Tables T1–T6 cover IC vs label, IC orthogonality vs 14 anchors, conditional forward-return separation, /081 IS-trade winner/loser attribution (load-bearing T4), ADF stationarity, regime marginal correlation. All computations IS-masked to `open_time < 2025-03-24`. No OOS column read. Numerical tables in brief Sections 2 match EDA output format.
- Section 3 (Proposed Changes): PASS — 4-feature family enumerated with construction definitions; data-acquisition plan present (Section 3.2); look-ahead discipline explicit (Section 3.3 + `.shift(1)` discipline documented per feature); /019 differentiation present (Section 3.4, 4 numbered structural arguments); engineering checklist (Section 3.6, 8 steps).
- Section 4 (Expected OOS Impact): PASS — IS band [+1.19, +1.44], OOS band [+0.40, +0.85], central estimates. Falsifier locked: IS Δ < +0.10 vs EXPLORATION-mode reference → FALSIFIED. Feature-level falsifier: all 4 members rank ≥ 14/18 across ≥ 2 symbols → INERT. Holding-time predictor present (added-vs-removed mean-duration gap ≤ +0.5 candles predicted; falsifier > +1.0 candle). OOS/IS ratio gate pre-registered (> 3.0 → SUSPICIOUS; IS Δ < 0 AND OOS Δ ≥ +0.20 → SUSPICIOUS-OOS-DOMINANT).
- Section 5 (Risk Mitigation): PASS — feature-overfit risk (R-feature-overfit) identified with mitigations; IC redundancy risk addressed (T2 max |IC| = 0.315); config-accretion pre-flight described (Critic /081 Rec #3).
- Section 6 (Risk Management Design): PASS — 7-primitive table present; all UNCHANGED; fire-rate predictions (identical to /059/081 — correct, this is a model-input change not a gate change); regime coverage rationale.
- Section 7 (Failure-Mode Prediction): PASS — 3 failure paths pre-registered with probabilities (INERT ≈ 40%, SUSPICIOUS-OOS-DOMINANT ≈ 25%, NEGATIVE ≈ 15%, residual PROMISING ≈ 20%). Specific diagnostic metrics for each path. The /019/023/024 INERT 3-data-point prior is acknowledged honestly.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION classification taxonomy (SUSPICIOUS → NEGATIVE → PROMISING → INERT, disjunctive precedence). All four categories defined with locked numerical thresholds. Conditional-orthogonality test for NEW feature family (the /076 lesson) pre-registered in Section 8.3 as a SUSPICIOUS sub-gate: SHAP split-allocation-vs-regime correlation > 0.50 for a relied-on family member (importance ≥ 30) → SUSPICIOUS. PROMISING requires at least one family member rank ≤ 9/18 with importance ≥ 30 for ≥ 1 symbol.
- Section 9 (Library Stack): PASS — no new dependencies; pinned stack listed (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1). ADF from statsmodels (already a dependency). Funding family built with numpy + pandas only.
- Section 10 (QR Audit Trail): PASS — 5 literature sources cited with specific findings mapped to specific family members (BIS WP 1087 → funding_accel_3; MDPI 14(2):346 → funding_sign_persist_9; CFB/Phemex crowding-reversal → funding_price_divergence_6; basis-carry literature → 8h cadence suitability; OI/liquidation literature → Direction-2 rejected on data-readiness grounds). OI direction-2 deferred with documented reason (no OI data feed vs complete funding pipeline). Design parameter justification traces each window length to either IS-only EDA or a-priori literature default.

## Code-Readiness Checks

**ITERATION_LABEL**: `run_baseline_v3.py` line 131 — `ITERATION_LABEL = "v3-082"`. PASS.

**V3_MODELS**: BCH/LDO/TRX — PASS (unchanged from /059 canonical).

**V3_FEATURE_COLUMNS_TOP_N (14→18)**: confirmed 18 entries in `src/crypto_trade/features_v3/__init__.py` lines 196–199, with the 4 funding family members appended after the 14 anchors. PASS.

**funding_v3.py — `funding_family_v3` group**: `compute_funding_family` and `add_funding_family_v3_features` implemented in `src/crypto_trade/features_v3/funding_v3.py` lines 395–550. All 4 `FUNDING_FAMILY_COLUMNS` present. Look-ahead discipline verified: `funding_sign_persist_9` uses `.shift(1).rolling(9).mean()` (window [t-9, t-1]); `funding_price_divergence_6` has `.shift(1)` on both legs before the 6-bar window. PASS.

**GROUP_REGISTRY**: `funding_family_v3` registered in `src/crypto_trade/features_v3/__init__.py` line 87. PASS.

**Config-accretion pre-flight (Critic /081 Rec #3)**: `_verify_canonical_config_accretion()` implemented; asserts 11 behavior-affecting knobs match /059 canonical values. The check fires at runner pre-flight. PASS.

**`_verify_feature_columns` updated to 18**: runner pre-flight `if n != 18` at line 347; both the global count and per-symbol count assertions updated. Closed single-z-score bans (`funding_rate_zscore_30`, `btc_funding_rate_zscore_30`) retained UNCHANGED. PASS.

**`fetch-funding` CLI**: exists at `src/crypto_trade/main.py:331,418,1009` (`_cmd_fetch_funding`). Incremental, cached to `data/funding_rates/<SYMBOL>.csv`. Infrastructure built at iter-v3/019. Data plan is implementable. PASS.

**Funding-rate cache for BCH/LDO/TRX**: brief Section 3.2 states verified present (BCH 6994 rows, LDO 3971, TRX 6914). Phase 6 must re-run `fetch-funding` to refresh within the 16h staleness window before regenerating parquets. (Engineer to verify at Phase 6 pre-flight.)

**/019 Differentiation**: Section 3.4 contains 4 numbered structural arguments distinguishing the 4-member family from the closed single `funding_rate_zscore_30`: (1) z-score is mean-zero by construction, discards sign/level, cannot encode crowding-direction persistence; (2) single-feature rank-14/14 failure mode vs 4 complementary family entry points; (3) family members selected by literature channels + T4 baseline-trade attribution, not univariate rank; (4) the /019/023 OOS collapse was INERT-overfit artifact not a funding-signal verdict. Differentiation is substantive. PASS.

**test_funding_family_v3.py**: present at `tests/features_v3/test_funding_family_v3.py`, 10 tests covering all required cases (past-only spike perturbation, NaN warm-up, clip bounds, accel = 2nd difference of momentum, sign-persist range, registry smoke, FileNotFoundError, KeyError, all-columns-present). PASS.

## Reasons (BLOCK)

**Test suite failure — 1 test FAILING:**

`tests/strategies/ml/test_v3_feature_count.py::test_feature_count_14` — this file was NOT updated in setup commit `87195d1` despite the commit message stating "The 4 affected feature-count-contract test files updated 14 -> 18". The test asserts `n == 14` but `V3_FEATURE_COLUMNS_TOP_N` now has 18 entries. Observed failure:

```
AssertionError: V3_FEATURE_COLUMNS_TOP_N has 18 features — expected 14.
```

**Required fix**: update `tests/strategies/ml/test_v3_feature_count.py` to reflect the 18-feature /082 state — the `test_feature_count_14` function name, docstring, and assertion must be updated to match 18. The brief's Section 3.6 step 7 mandates test-suite passage before Phase 6 proceeds.

**Ruff status**: clean (`uv run ruff check run_baseline_v3.py src/crypto_trade/features_v3/` — all checks passed). Not a blocker.

**All other 412 tests pass; 3 skipped.**

## Resolution Path

The QE must:
1. Update `tests/strategies/ml/test_v3_feature_count.py`: change `test_feature_count_14` → `test_feature_count_18`, update docstring, update `assert n == 14` → `assert n == 18`, update error message text.
2. Confirm that `test_baseline_v3_features_present`, `test_range_efficiency_50_absent`, `test_new_064_features_present`, `test_reverted_063_new_features_absent`, `test_prohibited_features_absent`, `test_no_duplicates` in the same file still PASS (they will — the prohibited-feature set is orthogonal to the 4 new funding-family members, and the 14 BASELINE_V3 features remain present).
3. Re-run `uv run pytest tests/ -q` — must be 0 failures.
4. Commit the fix as `fix(iter-v3/082): update test_v3_feature_count 14→18 (missed in setup commit)`.
5. Re-run this gate; issue updated `phase5p5_gate.md` with OVERALL: PASS.

Once the test fix is committed and green, Phase 6 may proceed. The only Phase 6 prerequisite action beyond normal is `uv run crypto-trade fetch-funding --symbols BCHUSDT,LDOUSDT,TRXUSDT` before parquet regeneration.
