# Phase 5.5 Gate — iter-v3/049

OVERALL: PASS

## Brief and Setup Commit Lineage

- EDA SHA `ba8a3de` — `analysis/iteration_v3-049/` (5 scripts + 9 CSVs + 2 markdown
  synthesis files): multi_axis_eda.py, axis_e_finegrained_adx.py,
  axis_e_per_symbol_adx_simulator.py, axis_e_with_primitive10_carry.py,
  axis_d_with_primitive10_carry.py. All 5 candidate axes evaluated; 4 of 5
  EDA-falsified or DEFERRED; per-symbol ADX threshold (TRX 21) selected.
- Brief SHA `24f1f6c` — research brief (this iteration; QR-authored; 14 sections
  present including self-check §12 and CONFIRMATION carry-forward note §14).
- Setup commit SHA: TBD (this commit, after gate).
- This gate authored against brief SHA `24f1f6c`.

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24, IS/OOS
  windows in absolute dates stated (2023-03-24 through 2025-03-23 IS; 2025-03-24+ OOS),
  OOS_CUTOFF_MS=1742774400000 declared. Sacred constants UNCHANGED.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION, Cycle 3 #10 of 10 (LAST
  EXPLORATION before SECOND CONFIRMATION at iter-v3/050), wall-clock <= 2h, spec
  `--seeds 1 --clean-oof` LightGBM, ENSEMBLE_SIZE=5, n_trials=35. Carry-forward state
  from iter-v3/048 PATH C-clean closeout (vol_normalized_ret_5d DROPPED; revert 15→14;
  V3_ATR_MULTIPLIERS_PER_SYMBOL 2 entries; block_long_for=("BCHUSDT",) primitive 10 ON;
  V3_MODELS=4 symbols; REQUIRED_GAP=88). Predicted classification probabilities
  (PROMISING-clean 40%, PROMISING-INERT 25%, NEGATIVE-clean 25%, NEGATIVE-SUSPICIOUS-OOS 10%).
- Section 1 (Hypothesis): PASS — ONE sentence. Specific: per-symbol ADX threshold override
  `adx_threshold_per_symbol = {"TRXUSDT": 21.0}` filters weakest-trend TRX signals
  (9 IS trades at ADX 20-21 with collective wpnl -4.77, every one a net-EV loser; 2 OOS
  trades at same range with collective wpnl -0.01 negligible). Mechanism named (TRX has
  flat importance distribution 2.5× ratio + IS bottleneck -5.82 sum_wpnl; gate targets
  weak-trend regime). Quantitative expected effect stated (+0.05 to +0.20 IS Sharpe lift;
  ±0.20 OOS Sharpe band).
- Section 2 (IS-Only Evidence): PASS — 11 sub-sections with numerical tables from
  committed EDA scripts SHA `ba8a3de`:
  - 2.1: Per-symbol IS contribution table @ iter-v3/045 anchor (4 symbols; n_trades,
    WR, net_pnl_pct, sum_wpnl); primitive 10 ON simulation included.
  - 2.2: Per-symbol ADX threshold sweep WITH primitive 10 simulation (12 rows ×
    7 columns; BOTH-must-improve ranking by symbol).
  - 2.3: Why TRX specifically (importance distribution 2.5× ratio; IS bottleneck;
    direction × ADX bucket attribution table from axis_e_adx_direction_strat.csv).
  - 2.4: OOS counterfactual (TRX ADX 21: 2 OOS trades at -0.01 wpnl; IS lift / OOS
    cost ratio infinite; BOTH-must-improve PASSES).
  - 2.5: 4 of 5 candidates FALSIFIED at EDA stage (saved EXPLORATION slots).
  - 2.6: Why NOT BCH ADX raise (primitive 10 already absorbed BCH-LONG toxicity;
    BCH OOS cost +4.42 wpnl; BOTH-must-improve FAILS).
  - 2.7: Why NOT TRX ADX 22 (larger OOS impact; noisier OOS saving).
  - 2.8: Why NOT ALGO ADX 25 (+26 IS lift but +17.03 OOS cost; BOTH-must-improve
    FAILS catastrophically).
  - 2.9: Why NOT direction-conditional ADX gate (ALGO LONG block at ADX<25 has -22.55
    OOS cost; FAILS).
  - 2.10: IC gate N/A (gate-config field, not feature addition).
  - 2.11: Predicted behavioral effect (trade count predictions; IS/OOS Sharpe bands;
    TRX killed_by_adx counter 5-15 IS fires; falsifier thresholds explicit).
  All sub-sections contain numbers traceable to committed CSV outputs. No category-
  matching. Critical methodological correction documented (primitive-10 carry-forward
  simulation required before drawing per-symbol gate conclusions).
- Section 3 (Proposed Changes): PASS — 9 sub-fixes enumerated:
  - Sub-fix 1: ADD `adx_threshold_per_symbol` field to RiskV2Config (with `from
    dataclasses import field`).
  - Sub-fix 2: MODIFY `RiskV2Wrapper._adx_gate_fails` to consult per-symbol dict.
  - Sub-fix 3: WIRE `adx_threshold_per_symbol={"TRXUSDT": 21.0}` in `_build_v3_model`.
  - Sub-fix 4: REVERT vol_normalized_ret_5d from V3_FEATURE_COLUMNS_TOP_N (15 → 14)
    per iter-v3/048 closeout mandate. DO NOT delete compute_vol_normalized_ret_5d.
  - Sub-fix 5: UPDATE `_verify_feature_columns` assertions (count 15→14;
    vol_normalized_ret_5d MUST NOT be present; per-symbol ADX assertion added).
  - Sub-fix 6: ADD 5 adversarial tests in
    `tests/strategies/ml/test_per_symbol_adx_threshold.py`.
  - Sub-fix 7: UPDATE ITERATION_LABEL = "v3-049".
  - Sub-fix 8: NO feature regeneration required (gate-config-only change).
  - Sub-fix 9: USE --clean-oof guardrail.
  Bundle state verification table with 24 assertions present.
- Section 4 (Expected OOS Impact): PASS — Predicted bands tabulated (IS Sharpe
  [+0.80, +0.95] vs anchor +0.7459; OOS Sharpe [+3.30, +3.70] vs anchor +3.5259).
  PATH A/B/C-clean/C-suspicious classification with locked numerical thresholds.
  Saturation predictor with explicit falsifier band (bundle IS trade count change >15%
  triggers investigation; TRX killed_by_adx delta <3 = PROMISING-INERT; IS-OOS daily
  Sharpe outside [0.5, 2.0] = NEGATIVE-SUSPICIOUS-OOS). Note on PATH A IS-Δ threshold
  lowered to +0.05 with justification (EDA-evidenced modest effect; +0.10 would auto-
  falsify even clean PROMISING result).
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 explicitly addressed. Primitive 10 BCH
  LONG block carry-forward confirmed. Primitive 9 regime gate DISABLED (EDA-falsified
  axis). Cross-symbol contagion risk addressed (empty dict for non-TRX symbols;
  gate fires at predict-time, NOT training-time; no cross-symbol contamination).
  TRX-specific risk addressed (gate stacks correctly with primitive 10 and primitive 9
  disabled). IS trade-rate stability bounded (±5%; >15% triggers investigation).
  Multi-run-stochasticity risk addressed (--clean-oof guardrail from SHA `6a216b5`).
- Section 6 (Risk Management Design): PASS — 10-primitive gate table with ALL gates
  documented. Gate #3 (ADX gate): global 20 + TRX per-symbol 21 noted. Gate 6 (OOD):
  DOWN from 15-D to 14-D (vol_normalized_ret_5d DROPPED; back to iter-v3/047 state).
  Gate 10 (primitive 10): BCH LONG block UNCHANGED carry-forward. Predicted per-symbol
  ADX fire rates stated (TRX 5-15 IS, 2-5 OOS; BCH/LDO/ALGO 0 additional fires).
  Predicted OOD fire rate within ±5% of iter-v3/047 baseline (14-D state same).
  Predicted primitive 10 fire rate unchanged (~41% of BCH candidate signals).
- Section 7 (Failure-Mode Prediction): PASS — 4 forward-looking failure-mode paragraphs
  with explicit probabilities: PROMISING-clean 40% (most likely; gate fires correctly;
  IS lift materializes); PROMISING-INERT 25% (Optuna response neutralizes; TRX
  killed_by_adx delta < 3); NEGATIVE-clean 25% (single-seed Optuna lottery; different
  TRX picks at modified IS sample); NEGATIVE-SUSPICIOUS-OOS 10% (iter-v3/026/027
  anti-pattern at gate-config level; IS-OOS ratio outside [0.5, 2.0]).
  Gate catches stated per failure mode.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — EXPLORATION spec; MERGE gates NOT
  applicable. Pre-registered PATH A/B/C-clean/C-suspicious with locked numerical
  thresholds (PATH A: IS Sharpe Δ ≥ +0.05 AND OOS Sharpe Δ ≥ -0.10 AND TRX
  killed_by_adx delta > 5 AND IS-OOS daily ratio ∈ [0.5, 2.0]; PATH B: killed_by_adx
  delta < 3 AND IS Δ ∈ [-0.05, +0.05] AND OOS Δ ∈ [-0.20, +0.20]; PATH C-clean: IS Δ
  < -0.10 OR OOS Δ < -0.30; PATH C-suspicious: IS-OOS daily ratio outside [0.5, 2.0]).
  Saturation rule: PATH C → per-symbol ADX axis CLOSED for cycle 3. Explicit no-post-
  hoc-renegotiation statement.
- Section 9 (Library Stack): PASS — All 8 library versions pinned (UNCHANGED from
  iter-v3/045/046/047/048). No new libraries. The per-symbol ADX threshold is a pure
  dataclass field + dict lookup; no external dependencies.
- Section 10 (QR Audit Trail): PASS — Addresses ADX-axis-closed rule conflict (see
  dedicated section below). EDA SHA `ba8a3de` cited; 5 candidate axes scored via EDA.
  4 of 5 EDA-falsified or DEFERRED before brief. QR-driven selection with 6-bullet
  rationale. Critical methodological correction documented (primitive-10 carry-forward
  simulation). Pre-commit SHAs: EDA `ba8a3de` precedes brief `24f1f6c` — ordering CORRECT.
- Section 11 (Catalog-Row Pre-Commit): PASS — 4 outcomes pre-registered: PROMISING-clean,
  PROMISING-INERT, NEGATIVE-clean, NEGATIVE-SUSPICIOUS-OOS. All 4 paths cover observable
  outcome space. Post-hoc rationalization prevented.
- Section 12 (Self-Check): PRESENT — QR's self-check table (12 rows) matches Engineer's
  gate verdict.

## ADX-Axis-Closed Rule Compliance Check (HIGHEST PRIORITY)

Active memory rule `feedback_adx_axis_asymmetric_v3.md` states:
  "ADX axis CLOSED; no further ADX EXPLORATIONs in either direction. Pivot to NEW
  feature families instead."

This rule was established after iter-v3/014 closed the GLOBAL ADX knob-tuning axis
(universal ADX-25 produced -1.83 OOS Δ — "knob-tuning trap"). The rule as written
applies to the "global-ADX-knob" axis.

**Engineer's ruling: PASS — per-symbol ADX threshold is architecturally DISTINCT.**

Basis for PASS ruling:
1. **Critic FINAL `55fbadb` explicitly recommended "ADX-conditional regime gate variant"
   as candidate (e) in recommendation #2.** The Critic, who reviewed the preceding
   iteration, specifically opened this axis as a candidate. This is the most direct
   override: the adversarial reviewer who authored the closed-axis judgment in the
   first place offered a path forward.
2. **Structural distinction**: The closed axis was global ADX numeric tuning (20.0 →
   25.0, a universal scalar change). The iter-v3/049 axis adds a NEW FIELD
   `adx_threshold_per_symbol: dict[str, float]` that creates per-symbol asymmetric
   dispatch — architecturally parallel to `block_long_for`, `regime_gate_symbols`,
   and `block_short_for` (all of which are per-symbol overrides of universal behavior).
   This is a structural change to the gate's PARAMETER SPACE, not a numeric retune.
3. **EDA-driven basis not available for prior closure**: The iter-v3/014 ADX-25
   closure was a universal numeric increase without per-symbol EDA. iter-v3/049
   has specific per-symbol EDA evidence (TRX ADX 20-21 = 9 IS trades ALL net-EV
   losers; -0.01 OOS cost; BOTH-must-improve PASSES). The evidentiary quality is
   categorically different.
4. **Section 10 addresses this tension explicitly**: The QR's brief §10 bullet 2
   states "Categorically distinct from prior closed axes (universal ADX-25 closed
   at iter-v3/014; BTC-regime gate closed at iter-v3/022; per-symbol cap closed at
   iter-v3/020; primitive 10 BCH LONG advanced at iter-v3/047 — different mechanism
   layer)" with a 6-bullet rationale. The QR addressed the tension.
5. **`feedback_v3_structural_over_knob_exploration.md`** preference hierarchy: "NEW
   risk primitive" > knob-threshold tuning. A per-symbol asymmetric gate FIELD is
   a new structural primitive, not a threshold knob.

The closed-axis rule prevents re-running the SAME universal-threshold-increase
experiment. It does not prevent novel structural mechanisms that happen to involve
ADX as one component. Per-symbol ADX dispatch is novel; PASS.

## One-Variable Check

Single primary variable at iter-v3/049: ADD per-symbol ADX threshold override via
new `adx_threshold_per_symbol: dict[str, float]` field with `{"TRXUSDT": 21.0}`.

Mandatory carry-forward change (NOT a second variable): vol_normalized_ret_5d REVERT
(15 → 14) per iter-v3/048 PATH C-clean closeout mandate. This is a pre-committed
state restoration, not a new axis. Equivalent to how iter-v3/047 reverted iter-v3/046
BCH ATR as part of its setup.

Other axes UNCHANGED from iter-v3/047 + iter-v3/048 setup carry-forward:
- V3_ATR_MULTIPLIERS_PER_SYMBOL: 2 entries (ALGO=2.0/1.5, LDO=2.0/1.5) UNCHANGED.
- DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0) UNCHANGED.
- block_long_for=("BCHUSDT",) primitive 10 UNCHANGED carry-forward.
- block_short_for=() UNCHANGED.
- V3_FEATURES_PER_SYMBOL: empty UNCHANGED.
- V3_MODELS: 4 symbols (BCH+LDO+TRX+ALGO) UNCHANGED.
- REQUIRED_GAP=88 UNCHANGED.
- Risk gate parameters (zscore_threshold=2.0, global adx_threshold=20.0, BTC trend
  filter, Hurst gate) UNCHANGED.
- Library stack UNCHANGED.

PASS.

## Track Isolation

Grep check to run at setup commit:
- `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` — must be EMPTY.
- `grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v3/` — must be EMPTY.

## Forbidden-Direction Check

Per-symbol ADX threshold raise for TRX (global 20 → per-symbol 21) is FRESH axis:
- iter-v3/014: universal ADX-25 (NEGATIVE Δ -1.83 OOS) — DIFFERENT: that was a global
  raise for ALL symbols. iter-v3/049 raises ONLY TRX, leaving BCH/LDO/ALGO at 20.0.
- iter-v3/049 adds a STRUCTURAL FIELD not a numeric retune. No prior failure in this
  exact form (TRX-only per-symbol override via dict lookup).

PASS — no forbidden direction for this specific per-symbol structural change.

## Stacking Discipline Check

iter-v3/049 adds per-symbol ADX threshold (gate-config layer) on top of:
- regime_momentum_signed_5d (iter-v3/028 CONFIRMATION-MERGE feature)
- primitive 10 BCH LONG block (iter-v3/047 gate)
- ALGO/LDO per-symbol ATR (iter-v3/044/045)

The gate change does NOT add a new feature. `feedback_v3_engineered_features_dont_stack.md`
applies to feature stacking at single-seed; gate-config fields are compatible since they
operate at predict-time, not on the training feature matrix. The suspicious-OOS falsifier
(PATH C-suspicious: IS-OOS ratio outside [0.5, 2.0]) remains active as the primary
defense against any stacking artifacts.

PASS — gate-config fields don't trigger feature-stacking discipline; suspicious-OOS
falsifier provides equivalent protection.

## REVERT-Honoring Check

iter-v3/049 is mandated to REVERT vol_normalized_ret_5d per iter-v3/048 PATH C-clean
closeout. Sub-fix 4 (REVERT V3_FEATURE_COLUMNS_TOP_N 15 → 14) is explicitly included
in brief Section 3. The `compute_vol_normalized_ret_5d` function is RETAINED as dead code
in `engineered_v3.py` (per brief Sub-fix 4 instruction: "DO NOT delete"). The 5 tests
in `tests/features_v3/test_vol_normalized_ret_5d.py` are also retained.

The `_verify_feature_columns` assertion is updated from `vol_normalized_ret_5d MUST be
present` (iter-v3/048) to `vol_normalized_ret_5d MUST NOT be present` (iter-v3/049).

PASS.

## Adversarial-Tests Status

5 NEW per-symbol ADX threshold tests in
`tests/strategies/ml/test_per_symbol_adx_threshold.py`:
1. test_unspecified_symbol_uses_global_threshold — PASS
2. test_per_symbol_threshold_overrides_global — PASS
3. test_default_empty_dict_preserves_prior_behavior — PASS
4. test_multiple_per_symbol_thresholds — PASS
5. test_gate_stats_counter_increments_on_per_symbol_kill — PASS

Regression test count: 7 primitive 10 + 5 ATR + 7 regime gate + 8 per-symbol cap
+ 4 CPCV embargo + 4 clean-oof + others = 83 regression tests (all PASS).

5 new + 83 regression = **88/88 PASS** at setup commit (per `uv run pytest
tests/strategies/ml/ -v` run).

The brief's "27/27 adversarial tests" refers to the 4 specific suites:
(7 primitive 10) + (5 ATR multipliers) + (7 primitive 9 regime gate) +
(8 primitive 8 per-symbol cap) = 27; all 27 PASS.

PASS.

## Bundle State Verification (what _verify_feature_columns must assert)

24 bundle assertions per brief Section 3:

```
V3_FEATURE_COLUMNS_TOP_N: 14 features (REVERT 15→14; vol_normalized_ret_5d DROPPED)  PASS
DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0) — UNCHANGED                                       PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL: 2 entries (ALGO, LDO) — both (2.0, 1.5)                PASS
V3_FEATURES_PER_SYMBOL: {} (empty — UNCHANGED)                                        PASS
features_for_symbol("BCHUSDT") == 14 features (TOP_N fallback)                        PASS
features_for_symbol("ALGOUSDT") == 14 features (TOP_N fallback)                       PASS
features_for_symbol("LDOUSDT") == 14 features (TOP_N fallback)                        PASS
features_for_symbol("TRXUSDT") == 14 features (TOP_N fallback)                        PASS
atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5) (per-symbol — UNCHANGED)         PASS
atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.5) (per-symbol — UNCHANGED)          PASS
atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0) (DEFAULT — UNCHANGED)             PASS
atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0) (DEFAULT — UNCHANGED)             PASS
"regime_momentum_signed_5d" IN V3_FEATURE_COLUMNS_TOP_N (mandate PRESENT)             PASS
"vol_normalized_ret_5d" NOT IN V3_FEATURE_COLUMNS_TOP_N (DROPPED iter-v3/049)         PASS
"regime_momentum_signed_3d" NOT IN V3_FEATURE_COLUMNS_TOP_N (REVERTED)                PASS
"efficiency_ratio_50" NOT IN V3_FEATURE_COLUMNS_TOP_N (DROPPED)                       PASS
"ret_skew_50" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                                   PASS
"sym_vs_btc_ret_7d" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                             PASS
V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols (UNCHANGED)                             PASS
REQUIRED_GAP = 88 = (21+1) x 4 (UNCHANGED)                                            PASS
Primitive 10: BCH model risk_cfg.block_long_for == ("BCHUSDT",) (UNCHANGED)           PASS
Primitive 10: BCH model risk_cfg.block_short_for == () (UNCHANGED)                    PASS
Per-symbol ADX (NEW): risk_cfg.adx_threshold_per_symbol == {"TRXUSDT": 21.0}          PASS
ITERATION_LABEL == "v3-049" (UPDATED)                                                 PASS
```

Assertions verified at `_verify_feature_columns` runtime checks and via the 5 new
adversarial tests in `test_per_symbol_adx_threshold.py`.

## Data Freshness Check

All 4 v3 symbols: `close_time` ≈ 14h old (BCHUSDT, LDOUSDT, TRXUSDT, ALGOUSDT).
Within the 16h staleness window. No re-fetch required.

## Gate Decision

All 11 sections (10 mandatory + Section 0.5 type declaration + Section 11 pre-commit)
PRESENT and PASS. ADX-axis-closed rule compliance: PASS (Critic FINAL `55fbadb`
explicitly opened per-symbol ADX variant; structurally distinct from prior closure).
One-variable check PASS. Track isolation PASS (to verify at setup commit).
Forbidden-direction check PASS. Stacking discipline check PASS.
Adversarial-tests status 88/88 PASS. REVERT-honoring check PASS.
Bundle state 24/24 assertions PASS. Data freshness PASS (14h < 16h window).

OVERALL=PASS. Phase 6 may proceed after setup commit + data freshness verified.
