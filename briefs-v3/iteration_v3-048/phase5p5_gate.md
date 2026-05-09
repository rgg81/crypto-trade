# Phase 5.5 Gate — iter-v3/048

OVERALL: PASS

## Brief and Setup Commit Lineage

- EDA SHA `a230cd1` — `analysis/iteration_v3-048/` (3 scripts + 4 CSVs + 2 markdown
  synthesis files): multi_axis_diagnosis.py, regime_gate_validation.py,
  regime_threshold_sweep.py. All 4 direction-asymmetric axes EDA-falsified; 5 candidate
  engineered features ranked; vol_normalized_ret_5d selected.
- Brief SHA `81af783` — research brief (this iteration; QR-authored; 13 sections present).
- Setup commit SHA `c69fdaa` — feat(iter-v3/048): NEW universal engineered feature
  vol_normalized_ret_5d (15th feature). 5 adversarial tests + 95/95 regression tests PASS.
- This gate authored against setup commit SHA `c69fdaa`.

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24, IS/OOS
  windows in absolute dates stated (2023-03-24 through 2025-03-23 IS; 2025-03-24+ OOS),
  OOS_CUTOFF_MS=1742774400000 declared. Sacred constants UNCHANGED.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION, Cycle 3 #9 of 10, wall-clock
  <= 2h, spec `--seeds 1 --clean-oof` LightGBM, ENSEMBLE_SIZE=5, n_trials=35. Carry-
  forward state from iter-v3/047 fully enumerated (V3_ATR_MULTIPLIERS_PER_SYMBOL,
  block_long_for, V3_MODELS, REQUIRED_GAP=88). Predicted classification probabilities
  (PROMISING 25%, PROMISING-INERT 35%, NEGATIVE-clean 30%, NEGATIVE-SUSPICIOUS-OOS 10%).
- Section 1 (Hypothesis): PASS — ONE sentence. Specific: vol_normalized_ret_5d = ret_5d /
  (range_realized_vol_50 + ε) gives LightGBM a risk-normalized momentum signal it cannot
  represent at depth-3-5 splits. Mechanism named (range_realized_vol_50 is rank-1 TRX
  importance, 2.5× top:bottom ratio = flat importance = model can't discriminate signal).
  Quantitative expected effect: IS Sharpe lift [+0.05, +0.15]; OOS Sharpe band [-0.10,
  +0.30]. Falsifier implied by PATH C thresholds.
- Section 2 (IS-Only Evidence): PASS — 11 sub-sections with numerical tables from committed
  analysis scripts SHA `a230cd1`:
  - 2.1: Per-symbol IS contribution table @ iter-v3/045 (LDO/BCH/TRX/ALGO with n_trades,
    WR, net_pnl, pct_total) from per_symbol.csv.
  - 2.2: Per-symbol direction asymmetry IS+OOS table (8 rows × 7 columns).
  - 2.3: TRX SHORT regime-conditional gate FALSIFIED at all 5 thresholds (T1-T5 tested;
    OOS cost at all thresholds).
  - 2.4: Top-5 features by mean importance rank across 4 symbols; range_realized_vol_50
    mean_rank=3.00 (rank-1 TRX) — quantitative basis for composition choice.
  - 2.5: TRX importance distribution (14 rows, top:bottom ratio 2.5× vs BCH 7.9×).
  - 2.6: Cycle 3 NEW engineered feature attempt history (5-row saturation context).
  - 2.7: IC carve-out justification (Category 2 per feedback_v3_engineered_feature_pivot.md).
  - 2.8-2.10: Why NOT TRX SHORT block / regime-conditional block / ALGO LONG block
    (quantitative counterfactuals with OOS cost estimates).
  - 2.11: Predicted behavioral effect (trade count ±4%; importance rank predictions;
    IS/OOS Sharpe bands). Falsifier bands stated explicitly.
  No category-matching. All numbers traceable to committed CSV outputs.
- Section 3 (Proposed Changes): PASS — 8 sub-fixes enumerated:
  - Sub-fix 1: ADD compute_vol_normalized_ret_5d to engineered_v3.py.
  - Sub-fix 2: REGISTER in add_engineered_v3_features.
  - Sub-fix 3: ADD vol_normalized_ret_5d to V3_FEATURE_COLUMNS_TOP_N (14 → 15).
  - Sub-fix 4: UPDATE _verify_feature_columns assertion (len==15, PRESENT check).
  - Sub-fix 5: ADD 5 adversarial tests (test_vol_normalized_ret_5d.py).
  - Sub-fix 6: UPDATE ITERATION_LABEL = "v3-048".
  - Sub-fix 7: REGENERATE v3 features parquets.
  - Sub-fix 8: USE --clean-oof guardrail.
  Bundle state verification table with 22 assertions present.
- Section 4 (Expected OOS Impact): PASS — Predicted bands tabulated (IS [+0.85, +1.15]
  vs anchor +0.7459; OOS [+3.30, +3.85] vs anchor +3.5259). PATH A/B/C-clean/C-suspicious
  classification with numerical thresholds. Saturation predictor with falsifier band.
  IS-OOS daily Sharpe ratio ∈ [0.5, 2.0] band falsifier. Per-symbol importance rank
  predictions (TRX 5-8, BCH/ALGO/LDO 8-12).
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 explicitly addressed. Primitive 10 BCH
  LONG block carry-forward confirmed. Primitive 9 regime gate disabled (EDA-falsified axis
  not applied). Cross-symbol contagion risk addressed (all 4 symbols train with new feature;
  per-symbol importance falsifier stated). Multi-run-stochasticity risk addressed (--clean-oof
  guardrail at SHA `6a216b5` prevents OOF contamination). IS trade-rate stability bounded
  (±4% prediction; >15% triggers investigation).
- Section 6 (Risk Management Design): PASS — 10-primitive gate table. Gate 6 (OOD):
  14 → 15 dimension update noted; predicted fire rate ±5% relative. Primitive 10 fire
  rate prediction ~41% of BCH candidate signals (carry-forward unchanged). All other
  gates status stated (enabled/disabled/config).
- Section 7 (Failure-Mode Prediction): PASS — Four forward-looking failure-mode paragraphs
  with explicit probabilities: PROMISING-INERT 35% (most plausible; model didn't learn);
  NEGATIVE-clean 30% (IS regression); PROMISING-clean 25%; NEGATIVE-SUSPICIOUS-OOS 10%
  (iter-v3/026/027 anti-pattern). Diagnostic indicators and gate catches stated per mode.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION spec; MERGE gates NOT applicable.
  Pre-registered PATH A/B/C-clean/C-suspicious with locked numerical thresholds. Saturation
  rule stated (vol_normalized_ret_5d axis CLOSED if PATH B or C; 1 EXPLORATION slot
  remains before iter-v3/050 CONFIRMATION). Explicit no-post-hoc-renegotiation statement.
- Section 9 (Library Stack): PASS — All 8 library versions pinned (unchanged from
  iter-v3/045/046/047). No new libraries introduced. vol_normalized_ret_5d is pure
  numpy + pandas (parallel to compute_regime_momentum_signed_5d).
- Section 10 (QR Audit Trail): PASS — EDA basis cited (3 scripts SHA `a230cd1`). 5-bullet
  QR-driven selection rationale. All 4 direction-asymmetric axes EDA-falsified before
  brief. 5 candidate engineered features ranked with quantitative basis (range_realized_
  vol_50 rank-1 TRX + FLAT importance distribution). Orchestrator correctly did NOT
  pre-commit axis (per feedback_v3_axis_selection_quant_discipline.md discipline).
  Pre-commit SHAs: EDA `a230cd1` precedes brief `81af783` — ordering CORRECT.
- Section 11 (Catalog-Row Pre-Commit): PASS — 4 outcomes pre-registered: PROMISING-clean,
  PROMISING-INERT, NEGATIVE-clean, NEGATIVE-SUSPICIOUS-OOS. All 4 paths cover observable
  outcome space. Post-hoc rationalization prevented.

## One-Variable Check

Single primary variable at iter-v3/048: ADD vol_normalized_ret_5d to
V3_FEATURE_COLUMNS_TOP_N (14 → 15; cycle 3 plan Axis 1).

Other axes UNCHANGED from iter-v3/047 carry-forward:
- V3_ATR_MULTIPLIERS_PER_SYMBOL: 2 entries (ALGO=2.0/1.5, LDO=2.0/1.5) UNCHANGED.
- DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0) UNCHANGED.
- block_long_for=("BCHUSDT",) primitive 10 UNCHANGED carry-forward.
- block_short_for=() UNCHANGED.
- V3_FEATURES_PER_SYMBOL: empty UNCHANGED.
- V3_MODELS: 4 symbols (BCH+LDO+TRX+ALGO) UNCHANGED.
- REQUIRED_GAP=88 UNCHANGED.
- Risk gate parameters (zscore_threshold, adx_threshold, BTC trend filter) UNCHANGED.
- Library stack UNCHANGED.

PASS.

## Track Isolation

Grep check run at setup commit:
- `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` — EMPTY (only
  comment strings; no actual imports). PASS.
- `grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v3/` — EMPTY (only
  comment strings; no actual imports). PASS.

## Forbidden-Direction Check

vol_normalized_ret_5d is a NEW composed feature (Category 2). No prior failure direction
exists for this specific feature. The feature axis history:
- iter-v3/026: vol_adj_autocorr (ret_autocorr_lag1_50 / range_realized_vol_50 + ε) —
  NEGATIVE-SUSPICIOUS-OOS at single-seed stacking. Different numerator (autocorr vs ret_5d).
- iter-v3/043: efficiency_ratio_50 — DISASTROUS NEGATIVE. Category 1 (not composed).
- iter-v3/043: fracdiff_d05_close universal — NEGATIVE. Different transformation entirely.

vol_normalized_ret_5d differs from vol_adj_autocorr (different numerator: ret_5d vs
ret_autocorr_lag1_50) and is NOT a Category 1 indicator. No forbidden direction applies.

PASS — no forbidden direction; mechanism is architecturally novel in this specific form.

## Stacking Discipline Check

iter-v3/048 adds vol_normalized_ret_5d ON TOP of regime_momentum_signed_5d (iter-v3/028
CONFIRMATION-MERGE ingredient) in a single-seed EXPLORATION run. Stacking risk is
explicitly pre-registered in Section 7 PATH C-suspicious (iter-v3/026/027 anti-pattern;
IS-OOS ratio outside [0.5, 2.0] band = NEGATIVE-SUSPICIOUS-OOS; 10% probability) and
Section 8 (PATH C-suspicious locked classification threshold).

The brief's own Section 7 and Section 8 ACCOUNT for the stacking risk with pre-registered
falsifiers. Multi-seed CONFIRMATION (iter-v3/050) would be required to validate any
two-feature stacking per feedback_v3_engineered_features_dont_stack.md.

PASS — stacking risk explicitly modeled with locked pre-registered falsifier.

## Adversarial-Tests Status

5 NEW vol_normalized_ret_5d tests in `tests/features_v3/test_vol_normalized_ret_5d.py`:
1. test_vol_normalized_ret_5d_past_only_discipline — PASS
2. test_vol_normalized_ret_5d_warmup_nan — PASS
3. test_vol_normalized_ret_5d_zero_vol_protection — PASS
4. test_vol_normalized_ret_5d_monotonicity — PASS
5. test_vol_normalized_ret_5d_missing_input_returns_nan — PASS

22 regression tests (primitive 10 × 7, ATR × 5, regime gate × 7, per-symbol cap × 8,
plus existing engineered_v3 × 63 = 90 total regression):
All 95 tests: 95/95 PASS at setup commit `c69fdaa`.

5 new + 90 regression = **95/95 PASS** (the brief's "27/27" format counts only the first
4 test suites: 7 primitive 10 + 5 ATR + 7 primitive 9 + 8 primitive 8 = 27; all 27 PASS).

PASS.

## REVERT-Honoring Check

No REVERT mandated for iter-v3/048. iter-v3/047's carry-forward state (BCH ATR REVERTED
at iter-v3/047 per Critic FINAL `5dae6d6`; primitive 10 BCH LONG block SET at iter-v3/047)
is preserved UNCHANGED. iter-v3/046 BCH ATR remains REVERTED. Per-symbol ATR for ALGO
and LDO remains at (2.0, 1.5) per iter-v3/044/045 carry-forward.

PASS.

## Bundle State Verification (from _verify_feature_columns assertions)

All 22 bundle assertions in brief Section 3 verified at setup commit:
- V3_FEATURE_COLUMNS_TOP_N: 15 features (14 → 15; vol_normalized_ret_5d ADDED)    PASS
- DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0)                                               PASS
- V3_ATR_MULTIPLIERS_PER_SYMBOL: 2 entries (ALGO, LDO) — both (2.0, 1.5)           PASS
- V3_FEATURES_PER_SYMBOL: empty                                                     PASS
- features_for_symbol("BCHUSDT") == 15 features (TOP_N fallback)                   PASS
- features_for_symbol("ALGOUSDT") == 15 features (TOP_N fallback)                  PASS
- features_for_symbol("LDOUSDT") == 15 features (TOP_N fallback)                   PASS
- features_for_symbol("TRXUSDT") == 15 features (TOP_N fallback)                   PASS
- atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5) (per-symbol)                PASS
- atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.5) (per-symbol)                 PASS
- atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0) (DEFAULT)                    PASS
- atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0) (DEFAULT)                    PASS
- "regime_momentum_signed_5d" IN V3_FEATURE_COLUMNS_TOP_N (mandate PRESENT)        PASS
- "vol_normalized_ret_5d" IN V3_FEATURE_COLUMNS_TOP_N (NEW iter-v3/048)            PASS
- "regime_momentum_signed_3d" NOT IN V3_FEATURE_COLUMNS_TOP_N (REVERTED)           PASS
- "efficiency_ratio_50" NOT IN V3_FEATURE_COLUMNS_TOP_N (DROPPED)                  PASS
- "ret_skew_50" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                              PASS
- "sym_vs_btc_ret_7d" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                        PASS
- V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols                                    PASS
- REQUIRED_GAP = 88 = (21+1) x 4                                                   PASS
- Primitive 10: BCH model block_long_for == ("BCHUSDT",) (carry-forward)            PASS
- Primitive 10: BCH model block_short_for == () (carry-forward)                     PASS
- ITERATION_LABEL == "v3-048"                                                       PASS

## Gate Decision

All 11 sections (10 mandatory + Section 0.5 type declaration + Section 11 pre-commit)
PRESENT and PASS. One-variable check PASS. Track isolation PASS. Forbidden-direction
check PASS. Stacking discipline check PASS. Adversarial-tests status 95/95 PASS.
REVERT-honoring check PASS. Bundle state 22/22 assertions PASS.

OVERALL=PASS. Phase 6 may proceed after setup commit `c69fdaa` + parquet regeneration.
