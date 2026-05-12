# Phase 5.5 Gate — iter-v3/057

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 confirmed IMMUTABLE; IS/OOS windows stated in absolute dates.
- Section 1 (Hypothesis): PASS — Specific 1-sentence mechanism: SWAPPING ret_skew_50 (rank 12/14) for parkinson_gk_ratio_20 (price_efficient_vol FIRST-IN-CATEGORY; Spearman p<0.005 all 3 syms) adds structurally distinct signal to base-14 stack; expected to shift CPCV path distribution.
- Section 2 (IS-Only Evidence): PASS — Committed EDA at SHA `8160e3a` (`analysis/iteration_v3-057/`). Scripts: `eda_a4_vs_new_family.py` + `synthesis.md` + 6 CSV/JSON artifacts. Tables in §2.1 (drop-candidate ranking), §2.2 (28-candidate filter), §2.3 (Spearman ρ, ADF, IC), §2.4 (family composition), §2.5 (historical context). IS-only; no OOS contamination. Category-matching absent — all values numerical.
- Section 3 (Proposed Changes): PASS — 3 edits + 1 test enumerated and locked: (1) SWAP ret_skew_50 → parkinson_gk_ratio_20 in V3_FEATURE_COLUMNS_TOP_N; (2) ITERATION_LABEL="v3-057"; (3) NEW adversarial test; (4) carry-forward UNCHANGED state verified. Net feature count 14 → 14.
- Section 4 (Expected OOS Impact): PASS — Prediction bands for 12 metrics vs /056 anchor; IS-OOS daily ratio falsifier [0.5, 2.0]; PATH A/B/C/D/E criteria; feature importance prediction (rank 7-12 of 14).
- Section 5 (Risk Mitigation): PASS — 6 risk bounds stated: no new compute function; past-only adversarial test; no risk-gate change; no labeling change; drop safety for LDO rank 8; clean-oof guardrail.
- Section 6 (Risk Management / Wall-Clock Discipline): PASS — EXPLORATION 2h hard cap; predicted 1.8-2.1h; carries forward 7-primitive risk gate stack UNCHANGED.
- Section 7 (Failure-Mode Prediction): PASS — PATH E probability 50-60% pre-registered (7th consecutive CPCV-INVARIANT NULL expected); failure modes in §1 PATH table (PATH B INERT, PATH C negative, PATH D null) and §4.4 falsifier triggers. Substance present; numbering diverges from template but all required content present.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Locked PATH hierarchy pre-registered (§8): PATH C > PATH C-suspicious > PATH A > PATH B > PATH D; PATH E co-fires. No post-hoc renegotiation per feedback_no_cheating.md.
- Section 9 (Library Stack): PASS — Unchanged from /056; all versions pinned: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1.

## Implementation Verification

- parkinson_gk_ratio_20 compute function: ALREADY EXISTS in
  `src/crypto_trade/features_v3/price_efficient_vol_v3.py` (line 48). Computed
  as pv20 / gk20 with gk20.replace(0, np.nan) guard. No new module required.
- Column already present in v3 feature parquets (computed at iter-v3/001-006; preserved
  in GROUP_REGISTRY dispatch). Parquet regeneration REQUIRED (parkinson_gk_ratio_20
  was in FULL set but was it preserved post-/007 top-N reduction? Parquets contain all
  GROUP_REGISTRY outputs, not just TOP_N — confirmed present via code inspection of
  add_price_efficient_vol_v3_features dispatch).
- ONE-variable rule: CONFIRMED. Drop ret_skew_50 + Add parkinson_gk_ratio_20 = 1-for-1
  SWAP. Net count 14. Single axis change.
- Track isolation: PASS — price_efficient_vol_v3.py imports numpy/pandas only; no
  crypto_trade.features or crypto_trade.features_v2 imports.
- 5 adversarial tests written to `tests/features_v3/test_parkinson_gk_ratio_20_past_only.py`.
  All 5 PASS. Full test suite 155/155 PASS.
- Lint: PASS (ruff check on all changed files).

## Setup Commit SHA

`8ab05dc` (Phase 5.5 gate + setup commit combined).

## Notes

Brief Section 3 specifies test path as `tests/features/test_parkinson_gk_ratio_20_past_only.py`.
Actual location is `tests/features_v3/test_parkinson_gk_ratio_20_past_only.py` (project convention).
Implementation uses correct path. Trivial discrepancy; does not block gate.
