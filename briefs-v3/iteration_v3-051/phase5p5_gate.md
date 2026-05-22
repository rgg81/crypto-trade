# Phase 5.5 Gate — iter-v3/051

OVERALL: PASS

## Brief and Setup Commit Lineage

- EDA SHA `290f37b` — `analysis/iteration_v3-051/` (3 scripts + 9 CSVs + 2 markdown
  synthesis files): multi_axis_eda.py, axis_c_fracdiff_deep_dive.py,
  axis_c_regime_3d_compute.py. 4 candidate axes evaluated; 3 eliminated/deferred; 1
  selected (fracdiff_d05_close UNIVERSAL).
- Brief SHA `6697f95` — research brief (this iteration; QR-authored; 12 sections
  present including self-check §12).
- EDA artifacts committed before brief write per
  `feedback_v3_axis_selection_quant_discipline.md` ordering: SHA `290f37b` precedes
  brief `6697f95`. Ordering CORRECT.
- Setup commit SHA: TBD (this commit, after gate).
- This gate authored against brief SHA `6697f95`.

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24,
  ENSEMBLE_SIZE=5, n_trials=35, OOS_CUTOFF_MS=1742774400000 declared. IS window
  2023-03-24 through 2025-03-23 in absolute dates. OOS window 2025-03-24+ stated.
  Sacred constants UNCHANGED.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION, Cycle 4 #1 of 10 (FIRST
  EXPLORATION post-iter-v3/050 NO-MERGE CONFIRMATION), wall-clock ≤2h hard cap,
  spec `--seeds 1 --n-trials 35 --clean-oof` LightGBM, ENSEMBLE_SIZE=5. System-level
  REVERT to iter-v3/028 architecture declared (V3_MODELS=3-sym, V3_ATR_MULTIPLIERS_
  PER_SYMBOL={}, block_long_for=(), REQUIRED_GAP=66). Single axis under test declared
  (ADD fracdiff_d05_close 14→15). Predicted classification probabilities stated
  (PROMISING-clean 35%, NEGATIVE-clean 30%, PROMISING-INERT 20%, NEGATIVE-SUSPICIOUS-
  OOS 15%). Context (iter-v3/050 NO-MERGE + system-level confirmation) present.
- Section 1 (Hypothesis): PASS — ONE sentence. Specific: "Adding `fracdiff_d05_close`
  to `V3_FEATURE_COLUMNS_TOP_N` at universal scope (14→15; broadcast to all 3 symbols
  BCH/LDO/TRX) — alongside the SYSTEM-LEVEL REVERT of per-symbol customizations to
  iter-v3/028 architecture — provides a NEW universal stationary engineered feature with
  mean-reversion signal (univariate Spearman ρ ∈ [-0.068, -0.038] significant at p<0.05
  across all 4 symbols)." Mechanism named (LdP AFML Ch. 5 FFD at d=0.5; long-memory
  preservation vs stationarity). Quantitative expected effect stated (+0.05 to +0.30
  IS Sharpe lift vs iter-v3/028 baseline reference +0.5101).
- Section 2 (IS-Only Evidence): PASS — 7 sub-sections with numerical tables from
  committed EDA scripts SHA `290f37b`:
  - 2.1: Cycle 4 starting baseline reference (iter-v3/028 multi-seed metrics table).
  - 2.2: fracdiff_d05_close EDA — ADF stationarity (all 4 syms p<0.05), IC matrix
    (top-5 |IC| pairs with carve-out analysis), Univariate Spearman (all 4 syms
    significant negative).
  - 2.3: Why universal scope (system-level constraint from
    `feedback_v3_per_symbol_lifts_oos_breaks_is.md`; iter-v3/050 diary explicit
    recommendation).
  - 2.4: Why fracdiff_d05_close ranked #1 vs regime_momentum_signed_3d (7-criterion
    table).
  - 2.5: Other candidates EDA-falsified or deferred (6 candidates in table with
    rationale).
  - 2.6: IC-gate consideration (Category 2 carve-out explicitly addressed per
    `feedback_v3_engineered_feature_pivot.md`).
  - 2.7: Predicted behavioral effect (fracdiff importance rank, bundle IS/OOS trade
    count, IS/OOS Sharpe bands, IS-OOS daily Sharpe ratio, falsifier thresholds
    explicit).
  All sub-sections contain numbers traceable to committed CSV outputs. No category-
  matching. Committed script: `analysis/iteration_v3-051/axis_c_fracdiff_deep_dive.py`.
- Section 3 (Proposed Changes): PASS — 10 sub-fixes enumerated with line-number
  references:
  - Sub-fix 1: REVERT V3_MODELS to 3-symbol BCH+LDO+TRX (drop ALGO).
  - Sub-fix 2: REVERT V3_ATR_MULTIPLIERS_PER_SYMBOL to {} (clear ALGO+LDO custom ATR).
  - Sub-fix 3: REVERT block_long_for to () (clear primitive 10 BCH LONG block).
  - Sub-fix 4: UPDATE REQUIRED_GAP = 66 = (21+1)*3 (revert from 88 for 3-sym).
  - Sub-fix 5: ADD fracdiff_d05_close to V3_FEATURE_COLUMNS_TOP_N (14→15).
  - Sub-fix 6: UPDATE `_verify_feature_columns` assertions (count 14→15; ADD
    fracdiff_d05_close MUST BE PRESENT; REMOVE ALGO-specific and primitive-10
    assertions; UPDATE V3_MODELS to 3-sym; UPDATE V3_ATR_MULTIPLIERS_PER_SYMBOL
    to 0 entries).
  - Sub-fix 7: ADD 5 adversarial tests in
    `tests/features_v3/test_fracdiff_d05_universal.py`.
  - Sub-fix 8: UPDATE ITERATION_LABEL = "v3-051".
  - Sub-fix 9: NO feature regeneration required (fracdiff_d05_close already in
    parquets — verified at gate: all 4 symbol parquets contain the column).
  - Sub-fix 10: USE --clean-oof guardrail.
  Bundle state verification table (22 assertions) present.
- Section 4 (Expected OOS Impact): PASS — Predicted bands tabulated (IS Sharpe
  [+0.55, +0.85] vs anchor +0.5101; OOS Sharpe [+0.30, +0.85] vs anchor +0.5053).
  Behavioral-effect predictor (fracdiff importance rank per symbol; IS/OOS trade count
  predictions; IS-OOS daily Sharpe ratio band). PATH A/B/C-clean/C-suspicious triggers
  with locked numerical thresholds. Saturation predictor with falsifier thresholds
  explicit. Note on PATH A IS-Δ threshold (+0.05 vs standard +0.10) with justification.
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 explicitly addressed. Primitive 10
  REVERT (block_long_for=()). Per-symbol ATR REVERT (V3_ATR_MULTIPLIERS_PER_SYMBOL={}).
  Per-symbol ADX empty (unchanged). Primitive 9 disabled (unchanged). Cross-symbol
  contagion risk addressed (broadcast but per-symbol training independent; --clean-oof
  guardrail). Universe contraction risk (4→3 syms; REQUIRED_GAP recomputed to 66).
  Risk-budget redistribution risk (returns to /028 7-primitive composition). IS trade-
  rate stability bounded (±20% per symbol; >30% triggers investigation).
  Multi-run-stochasticity risk addressed (--clean-oof guardrail per SHA `6a216b5`).
- Section 6 (Risk Management Design): PASS — 10-primitive gate table with ALL gates
  documented. Gate 6 (OOD): UP from 14-D to 15-D (fracdiff_d05_close ADDED).
  Gate 10 (direction block): REVERT — block_long_for=(); block_short_for=(). Predicted
  OOD fire rate within ±5% of /028 baseline. Predicted ADX fire rate unchanged.
  Predicted primitive 10 fire rate 0 (gate cleared).
- Section 7 (Failure-Mode Prediction): PASS — 4 forward-looking failure-mode paragraphs
  with explicit probabilities: PROMISING-clean 35% (most likely; BCH per /035 precedent
  or LDO per strongest univariate ρ), NEGATIVE-clean 30% (single-seed lottery), PROMISING-
  INERT 20% (Optuna ignores 15th feature), NEGATIVE-SUSPICIOUS-OOS 15% (IS-OOS daily
  ratio outside [0.5, 2.0]; IC 0.67 with regime_momentum at LDO). What the gates should
  catch stated per failure mode.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION spec; MERGE gates not
  applicable. Pre-registered PATH A/B/C-clean/C-suspicious with locked numerical
  thresholds. Saturation rule stated (PATH C → fracdiff UNIVERSAL CLOSED for cycle 4;
  pivot to regime_momentum_signed_3d at /052). Non-renegotiable post-hoc statement
  present. Note on PATH A IS-Δ threshold lowered to +0.05 with justification present.
- Section 9 (Library Stack): PASS — 8 library versions pinned (UNCHANGED from prior
  iterations). No new libraries. `compute_fracdiff_d05_close` uses only numpy/pandas/
  scipy (no mlfinlab/mlfinpy/pypbo/fracdiff dependencies).
- Section 10 (QR Audit Trail): PASS — EDA SHA `290f37b` cited; 4 candidate axes scored
  via EDA. Candidates (a)/(b1)/(b2)/(b3)/(b4)/(c2)/(d) eliminated, deferred, or
  incorporated. (c1) fracdiff_d05_close selected with 9-point rationale. Cross-
  validation against regime_momentum_signed_3d (alternative). Adversarial review
  preparation (4 Q&A pairs). System-level REVERT justification (NOT axis under test;
  structural baseline restoration per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`
  UPDATED 2026-05-10). Pre-commit SHAs: EDA `290f37b` precedes brief `6697f95` —
  ordering CORRECT.
- Section 11 (Catalog-Row Pre-Commit): PRESENT with renaming note — The brief labels
  Section 11 as "References" (departs from iter-v3/049 format where §11 was "Catalog-
  Row Pre-Commit Disposition"). However, the catalog pre-registration content IS present
  in Section 8 PATH A/B/C-clean/C-suspicious with explicit classification labels,
  actions, and saturation rules. 4 outcome paths cover observable outcome space. Post-
  hoc rationalization prevented by locked thresholds. PASS with engineering note:
  future briefs should use a dedicated §11 Catalog-Row section per /049 precedent.
- Section 12 (Self-Check): PRESENT — QR's self-check checklist (12 rows) present.
  Brief written WITHOUT viewing iter-v3/051 OOS data (stated explicitly). Pre-registered
  Section 8 thresholds locked before backtest runs.

## ONE-Variable Check (HIGHEST PRIORITY)

**PASS.**

Single primary variable at iter-v3/051: ADD `fracdiff_d05_close` to
V3_FEATURE_COLUMNS_TOP_N (14→15) at universal scope.

Mandatory carry-forward change (NOT a second variable): system-level REVERT to
iter-v3/028 architecture (V3_MODELS 4→3; V3_ATR_MULTIPLIERS_PER_SYMBOL {}; block_long_for
()). Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10 with second-
cycle confirmation (iter-v3/039 + iter-v3/050 both CONFIRMATION-NO-MERGE on per-symbol
bundle). This is a pre-committed state restoration, not a new axis — structurally identical
to how iter-v3/049 mandated vol_normalized_ret_5d REVERT as part of its setup (not the axis
under test). The Critic FINAL `b6339c5` of iter-v3/050 explicitly named this as
"system-level mandate #2+#3" (per Section 10 QR Audit Trail). The ONE variable under
test is fracdiff_d05_close UNIVERSAL addition. PASS.

## fracdiff_d05_close Availability Check

**PASS — no feature regeneration required.**

Verified at gate via `pyarrow.parquet.read_schema`:
- BCHUSDT_8h_features.parquet: fracdiff_d05_close = True
- LDOUSDT_8h_features.parquet: fracdiff_d05_close = True
- TRXUSDT_8h_features.parquet: fracdiff_d05_close = True
- ALGOUSDT_8h_features.parquet: fracdiff_d05_close = True (reserved-for-future)

All 4 symbol parquets contain the column. No `uv run crypto-trade features --track v3`
invocation needed.

## REQUIRED_GAP Recalculation (3-Symbol Universe)

**PASS.**

Current REQUIRED_GAP in `src/crypto_trade/strategies/ml/validation_v3.py` = 88 = (21+1)*4
(4-symbol universe at iter-v3/034–050).

For iter-v3/051 (3-symbol BCH+LDO+TRX): REQUIRED_GAP = (21+1)*3 = 66.

Formula basis: López de Prado purge requirement — gap = (timeout_candles+1)*n_symbols.
timeout_candles = 10080 min / 480 min = 21. n_symbols = 3.

Required change: `validation_v3.py` REQUIRED_GAP constant 88 → 66, with history comment
updated to record the universe contraction.

The `_verify_label_leakage_gap` function in run_baseline_v3.py uses `n_symbols = len(V3_MODELS)`
dynamically — it will self-verify at runtime that the formula gives 66 and matches the
constant. If REQUIRED_GAP is NOT updated to 66, the assertion at line 660 will FAIL
loudly, blocking the backtest.

## Bundle State Assertions

22 assertions per brief Section 3 bundle state verification table:

```
V3_FEATURE_COLUMNS_TOP_N: 15 features (ADD fracdiff_d05_close — iter-v3/051 axis)        TO VERIFY
DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0) — UNCHANGED                                           TO VERIFY
V3_ATR_MULTIPLIERS_PER_SYMBOL: 0 entries (REVERT — system-level mandate)                  TO VERIFY
V3_FEATURES_PER_SYMBOL: {} (empty — UNCHANGED)                                            TO VERIFY
features_for_symbol("BCHUSDT") == 15 features (TOP_N fallback)                            TO VERIFY
features_for_symbol("LDOUSDT") == 15 features (TOP_N fallback)                            TO VERIFY
features_for_symbol("TRXUSDT") == 15 features (TOP_N fallback)                            TO VERIFY
atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0) (DEFAULT — REVERT)                    TO VERIFY
atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0) (DEFAULT — REVERT)                    TO VERIFY
atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0) (DEFAULT — REVERT)                    TO VERIFY
"regime_momentum_signed_5d" IN V3_FEATURE_COLUMNS_TOP_N (mandate PRESENT)                 PASS (pre-checked)
"fracdiff_d05_close" IN V3_FEATURE_COLUMNS_TOP_N (NEW iter-v3/051)                        TO VERIFY (post-code-change)
"vol_normalized_ret_5d" NOT IN V3_FEATURE_COLUMNS_TOP_N (DROPPED iter-v3/049)             PASS (pre-checked)
"regime_momentum_signed_3d" NOT IN V3_FEATURE_COLUMNS_TOP_N (queued iter-v3/052)          PASS (pre-checked)
"efficiency_ratio_50" NOT IN V3_FEATURE_COLUMNS_TOP_N (DROPPED iter-v3/043)               PASS (pre-checked)
V3_MODELS = (BCH, LDO, TRX) — 3 symbols (REVERT — system-level mandate)                   TO VERIFY
ALGOUSDT NOT IN V3_MODELS (REVERT)                                                        TO VERIFY
REQUIRED_GAP = 66 = (21+1) x 3 (REVERT)                                                   TO VERIFY
Primitive 10: BCH model risk_cfg.block_long_for == () (REVERT — system-level mandate)     TO VERIFY
Primitive 10: BCH model risk_cfg.block_short_for == () (UNCHANGED)                        TO VERIFY
Per-symbol ADX: risk_cfg.adx_threshold_per_symbol == {} (UNCHANGED)                       PASS (pre-checked; /050 already cleared it)
ITERATION_LABEL == "v3-051" (UPDATED)                                                     TO VERIFY
```

All "TO VERIFY" assertions are implemented as runtime checks in `_verify_feature_columns`
and `_verify_label_leakage_gap` which run at the start of every backtest. The setup commit
must update each corresponding code location.

## IC-Gate Carve-Out (Category 2 Composed Feature)

**PASS.**

fracdiff_d05_close max |IC| = 0.7381 with vwap_dev_20 at LDO. Per
`feedback_v3_engineered_feature_pivot.md` Category 2 carve-out: composed features get IC
carve-out vs source primitives. fracdiff_d05_close = FFD(close, d=0.5) and vwap_dev_20 =
(close - vwap)/vwap — both are close-derived. Carve-out applies. Strict |IC|<0.70 gate
bypassed for this pair.

Post-carve-out max |IC| = 0.6721 with regime_momentum_signed_5d at LDO, which is BELOW
the strict 0.70 gate. No additional carve-out needed.

## Data Freshness Check

All 3 v3 symbols (BCH/LDO/TRX): close_time age = 14.5h. Within the 16h staleness window.
No re-fetch required.

## Track Isolation

To verify at setup commit:
- `grep -rP "^from crypto_trade\.features " src/crypto_trade/features_v3/` — must be EMPTY.
- `grep -rP "^from crypto_trade\.features_v2" src/crypto_trade/features_v3/` — must be EMPTY.

## REVERT-Honoring Check

iter-v3/051 mandates REVERT of:
1. V3_MODELS: 4→3 symbols (drop ALGO). Brief Sub-fix 1.
2. V3_ATR_MULTIPLIERS_PER_SYMBOL: {} (clear ALGO+LDO custom ATR). Brief Sub-fix 2.
3. block_long_for: () (clear primitive 10 BCH LONG block). Brief Sub-fix 3.
4. REQUIRED_GAP: 88→66 (3-sym formula). Brief Sub-fix 4 + validation_v3.py update.

All 4 REVERTs explicitly included in Section 3 sub-fixes. _verify_feature_columns must
update assertions to reflect the REVERTed state. Primitive 10 assertion flips from
"block_long_for == ('BCHUSDT',)" to "block_long_for == ()" (REVERT). V3_ATR assertion
flips from "2 entries (ALGO, LDO)" to "0 entries (empty — REVERT)". PASS.

## Adversarial-Tests Count

5 NEW fracdiff_d05_universal tests in
`tests/features_v3/test_fracdiff_d05_universal.py`:
1. test_fracdiff_d05_close_in_universal_feature_list
2. test_fracdiff_d05_close_present_in_all_4_symbol_parquets
3. test_fracdiff_d05_close_stationary_per_symbol
4. test_fracdiff_d05_close_no_lookahead
5. test_v3_models_is_3_symbol_at_iter_v3_051

Prior regression suites expected to still PASS (7 primitive 10 + 5 per-symbol ATR + 7
per-symbol ADX threshold + 8 per-symbol cap + 4 CPCV embargo + 4 clean-oof + others).

Note: The iter-v3/047 primitive 10 tests (7 tests in
`tests/strategies/ml/test_direction_block_primitive_10.py`) verify behavior AT the
block_long_for=("BCHUSDT",) state. With REVERT to block_long_for=(), these tests may
CONFLICT with the new state. The `_verify_feature_columns` runtime check is updated to
assert block_long_for=() — the adversarial tests must also pass under the new state.
This is addressed in Sub-fix 6 (_verify_feature_columns update). Ensure the primitive 10
adversarial tests remain valid (they test the gate mechanism with configurable inputs, not
the specific BCH state).

Per iter-v3/049 brief precedent, the gate counts "27/27" as the 4 specific primitive
suites (7 primitive 10 + 5 ATR multipliers + 7 primitive 9 regime gate + 8 primitive 8
per-symbol cap). All 27 must PASS at setup commit.

## Forbidden-Direction Check

fracdiff_d05_close at UNIVERSAL scope is fresh:
- iter-v3/034 added fracdiff_d05_close to V3_FEATURE_COLUMNS_TOP_N at universal scope
  (14→15) BEFORE the REVERT pattern was established.
- iter-v3/035 DROPPED fracdiff_d05_close from universal list (15→14) and moved it to
  V3_FEATURES_PER_SYMBOL["BCHUSDT"] only (BCH-only per-symbol).
- iter-v3/039 CONFIRMATION-NO-MERGE rejected the per-symbol bundle including
  fracdiff_d05_close per-symbol — NOT the universal scope.
- iter-v3/051 UNIVERSAL scope = cycle 4 HIGH-priority axis #1 per Critic FINAL `b6339c5`
  recommendation #5, explicitly endorsed for cycle 4.

No prior NEGATIVE result for fracdiff_d05_close at universal scope ON TOP OF
iter-v3/028 baseline architecture (the /028 baseline adds regime_momentum_signed_5d which
was absent at iter-v3/034). The universal scope axis is fresh from the current baseline
perspective. PASS.

## Gate Decision

All 12 sections (10 mandatory + Section 0.5 type declaration + Section 12 self-check)
PRESENT and PASS. Section 11 catalog pre-registration content present in Section 8
(renaming noted for future brief discipline). ONE-variable check PASS (system-level
REVERT is mandatory state restoration, not a second axis). fracdiff_d05_close parquet
availability PASS (all 4 symbols confirmed). REQUIRED_GAP recalculation PASS (88→66 for
3-sym; formula = (21+1)*3 = 66). IC-gate carve-out PASS (Category 2 applies; post-carve-
out max |IC| = 0.6721 < 0.70). Data freshness PASS (14.5h < 16h window). REVERT-honoring
check PASS (4 REVERTs in Section 3). Track isolation to verify at setup commit.
Forbidden-direction check PASS (cycle 4 #1 fresh axis at iter-v3/028 baseline).

OVERALL=PASS. Phase 6 may proceed after setup commit.
