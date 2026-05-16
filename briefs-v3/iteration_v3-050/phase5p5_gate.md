# Phase 5.5 Gate — iter-v3/050

OVERALL: PASS

## Brief and Setup Commit Lineage

- Brief SHA `acc6baf` — research brief (QR-authored; 14 sections + Section 0.5 type
  declaration; 787 lines). CONFIRMATION type declared; SECOND v3 CONFIRMATION after
  iter-v3/018 BOOTSTRAP + iter-v3/028 first CONFIRMATION-MERGE + iter-v3/039 NO-MERGE.
- Authority: Critic FINAL `1908d50` (iter-v3/049 review.md) — bundle composition
  recommendation; per-symbol ADX TRX 21 DROPPED; cycle 3 axis CLOSED.
- Parent SHA: `3a3d05b` (iter-v3/049 head).
- Setup commit SHA: TBD (this commit, after gate).
- This gate authored against brief SHA `acc6baf` at 2026-05-10.

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24, IS/OOS
  windows stated in absolute dates (2023-03-24 through 2025-03-23 IS; 2025-03-24+ OOS),
  OOS_CUTOFF_MS=1742774400000 declared. ENSEMBLE_SIZE=5, outer_seeds=2 declared.
  Sacred constants UNCHANGED.
- Section 0.5 (Iteration Type): PASS — TYPE=CONFIRMATION (SECOND true v3 CONFIRMATION
  ever). Wall-clock budget 6h HARD CAP. "NOT bundle assembly; multi-seed validation
  of cycle 3 best PROMISING bundle." Pre-commitment lock cited
  (`feedback_v3_strict_10_to_1_cadence.md`, `feedback_v3_iter018_confirmation_baseline_validation.md`).
  BASELINE_V3.md update gate declared (BOTH IS+OOS multi-seed mean > /028 anchor
  +0.5101 IS / +0.5053 OOS per `feedback_v3_strict_both_is_oos_baseline.md`).
- Section 1 (Hypothesis): PASS — ONE sentence. Specific and testable: "The cycle 3
  best PROMISING bundle ... PRESERVES IS lift AND OOS lift at multi-seed ... AND beats
  the iter-v3/028 BASELINE_V3.md anchor on BOTH IS Sharpe AND OOS Sharpe (multi-seed
  mean), satisfying the BASELINE_V3.md update gate per
  `feedback_v3_strict_both_is_oos_baseline.md`." Named mechanism: multi-seed validation
  of primitive 10 + per-symbol ATR ALGO/LDO. Falsifier pre-registered.
- Section 2 (IS-Only Numerical Evidence): PASS — Structural difference from EXPLORATION
  briefs explicitly acknowledged and justified. CONFIRMATION's "evidence" = prior committed
  runs (iter-v3/044/045/047/049 single-seed reports). Tables provided: cycle 3 PROMISING
  bundle lineage table (6 iterations × 7 columns); iter-v3/045 strongest single-seed
  metrics table (14 rows); iter-v3/047 primitive 10 metrics vs /045; iter-v3/049
  most-recent EXPLORATION metrics; per-symbol /045 OOS attribution (4 symbols);
  per-cell PBO + n_eff diagnostics; setup integrity table. All values traceable to
  committed reports-v3/ CSVs. No fresh IS-only EDA script needed per CONFIRMATION
  structural rationale documented in §2.1. The prior Phase 5.5 precedent (iter-v3/028
  CONFIRMATION) also inherited prior PROMISING evidence — consistent pattern.
- Section 3 (Proposed Changes): PASS — All changes enumerated. Symbols/labeling/features/
  risk-gates ALL UNCHANGED minus one field DROP (per-symbol ADX TRX 21). Multi-seed config
  is the single axis changed (--seeds 1 → 2). 3.6 sub-fix decomposition: 16 sub-fixes
  (3 code edits + 13 pre-flight verifiers). 3.7 brief-vs-code reconciliation table: 22
  rows with executable verifiers. 3.8 inheritance chain documented. 3.9 wall-clock
  estimate with 2 calibration points (4.23h Calibration A; 1.17h Calibration B).
- Section 4 (Expected OOS Impact): PASS — Predicted multi-seed Sharpe bands tabulated
  [IS +0.40, +0.65] / [OOS +0.55, +1.50] with median predictions. Per-symbol
  concentration prediction bands. Bundle OOS trade count [80, 160]. 4 fragility tests
  F1-F4. CONFIRMATION outcome interpretation table (4 outcomes). Compression precedent
  calibration from iter-v3/018 and iter-v3/028. Falsifier: OOS or IS multi-seed mean
  < +0.51 (anchor) = NO BASELINE UPDATE.
- Section 5 (Risk Mitigation): PASS — 4 cadence-discipline structural safeguards
  (6h wall-clock hard cap; single-axis variation rule; BOTH-must-improve gate; pre-
  commitment lock). 5 methodology-pipeline safety items. 4 multi-seed-axis specific
  risks (outer-seed determinism; inner-ensemble determinism; n_trials budget; colsample
  Optuna-tuned). Per-symbol architecture concentration management. LDO single-seed
  lottery flag specific carry-forward concern (§5.5 with 3-outcome branching on LDO OOS).
- Section 6 (Risk Management Design): PASS — 10-primitive gate table inherited from
  iter-v3/049 minus per-symbol ADX field. Gate #3 updated: "global ADX=20.0; per-symbol
  DROP per Critic FINAL `1908d50` rec #2." All 10 gates documented with fire-rate
  predictions. Primitive 10 (BCH LONG block) UNCHANGED carry-forward at gate #10.
  Concentration is INFORMATIONAL gate per `feedback_v3_baseline_update_policy.md`.
- Section 7 (Failure-Mode Prediction): PASS — 10 pre-registered predictions with
  probabilities: P1 (trade-rate floor breach 10%), P2 (LDO lottery carry-forward 20%),
  P3 (PBO max-aggregator 15%), P4 (wall-clock 10%), P5 (10-seed pre-MERGE fail 10%),
  P6 (iter-v3/039 anti-pattern dominant 25%), P7 (BOOTSTRAP-style success 20%),
  P8 (FULL success 10%), P9 (both below anchor 15%), P10 (hard-blocking gate 10%).
  Summary probabilities: MERGE-FULL 10%, BOOTSTRAP-style 20%, NO-MERGE-revert 50%,
  BLOCK 10%. Total 100% with single-mode dominant failure (P6 iter-v3/039 anti-pattern).
- Section 8 (MERGE/NO-MERGE Criteria): PASS — LOCKED thresholds pre-committed.
  BASELINE_V3.md update gate: BOTH IS multi-seed mean > +0.5101 AND OOS multi-seed mean
  > +0.5053. 10 MERGE gates with hard-blocking vs aspirational distinction. 3
  CONFIRMATION verdict pathways (MERGE-FULL, MERGE-BOOTSTRAP-style, NO-MERGE-revert).
  BLOCK (process) defined. Concentration > 30% = aspirational only (per
  `feedback_v3_baseline_update_policy.md`). Discretionary override PROHIBITED.
- Section 9 (Library Stack): PASS — 9 packages pinned with versions (numpy 2.2.6,
  scipy 1.17.0, statsmodels 0.14.6, scikit-learn 1.8.0, lightgbm 4.6.0, pytest,
  pandas 3.0.0, pyarrow 23.0.1, optuna 4.8.0). No new external deps. Aggregator
  strategy UNCHANGED. Reproducibility stamp requirements listed for engineering_report.md.
- Section 10 (QR Audit Trail): PASS — NO QR-EDA-driven axis selection (CONFIRMATION).
  Bundle composition decided per Critic FINAL `1908d50` rec #2 with verbatim quote
  (lines 83-91). Authority chain documented (7 feedback rules cited). Parent SHA
  `3a3d05b` cited. Phase 5.5 verification expectations listed.
- Section 11 (Catalog-Row Pre-Commit): PASS — 3 outcomes pre-registered (MERGE-FULL,
  MERGE-BOOTSTRAP-style, NO-MERGE-revert). All 3 paths cover observable outcome space.
  Post-hoc rationalization prevented.
- Section 12 (Phase 5.5 Gate Self-Check): PRESENT — 14-row table (12 mandatory +
  Section 11 pre-commit + Section 12 self-check). QR projects OVERALL=PASS.

## One-Variable Rule Check (CONFIRMATION — special case)

CONFIRMATION iterations are EXEMPT from the one-variable rule. CONFIRMATIONs by
definition validate MULTIPLE PROMISING ingredients simultaneously (that is the point).
The changes in iter-v3/050 are:
- Multi-seed config: --seeds 1 → 2 (the single TEST AXIS)
- Per-symbol ADX field DROP: {TRXUSDT: 21.0} → {} (mandatory state restoration per Critic)
- ITERATION_LABEL cosmetic bump: "v3-049" → "v3-050"

The DROP is not a second "variable" in the research sense — it is a pre-committed
state restoration per Critic FINAL `1908d50` rec #2. The substantive comparison is
iter-v3/049 head bundle (minus ADX field) vs multi-seed validation. PASS.

## CONFIRMATION Bundle Stacking Discipline Check

iter-v3/050 validates the STACKING of:
1. regime_momentum_signed_5d (iter-v3/028 CONFIRMATION-MERGE feature)
2. V3_ATR_MULTIPLIERS_PER_SYMBOL ALGO/LDO = (2.0, 1.5) (iter-v3/044/045 PROMISING)
3. primitive 10 BCH LONG block (iter-v3/047 PROMISING, IS-only)
4. adx_threshold_per_symbol={} (iter-v3/049 DROPPED per Critic)

`feedback_v3_engineered_features_dont_stack.md` applies to single-seed EXPLORATION
stacking. CONFIRMATIONs explicitly stack all cycle PROMISING ingredients — that is the
CONFIRMATION's purpose. The suspicious-OOS falsifier (IS-OOS ratio < 0.5 → HARD BLOCK)
remains the primary guard against stacking artifacts.

`feedback_v3_per_symbol_lifts_oos_breaks_is.md` identifies the dominant fragility
(iter-v3/039 anti-pattern: per-symbol customizations lift OOS but break IS at multi-seed).
Section 7 prediction P6 explicitly assigns 25% probability to this outcome.

PASS — CONFIRMATION stacking is by design; suspicious-OOS falsifier + hard-blocking
Gate 3 (OOS/IS ≥ 0.5) provide the structural guard.

## Forbidden-Direction Check

- ADX global raise: CLOSED at iter-v3/014 (universal ADX-25 produced -1.83 OOS Δ).
  iter-v3/050 DROPS the per-symbol ADX field (reverts to global-only). This is the
  OPPOSITE direction of the closure (REMOVING a per-symbol ADX addition, not adding a
  new one). No forbidden direction.
- Per-symbol cap: CLOSED at iter-v3/020. iter-v3/050 has no per-symbol cap.
- Regime gate: CLOSED at iter-v3/022. iter-v3/050 has enable_regime_gate=False.
- Concentration mechanism: per-symbol PnL caps CLOSED per
  `feedback_v3_concentration_is_signal.md`. iter-v3/050 has no per-symbol cap.
PASS — no forbidden direction violated.

## REVERT-Honoring Check

One REVERT required: per-symbol ADX field {"TRXUSDT": 21.0} → {} per Critic FINAL
`1908d50` rec #2. Verified:
- `adx_threshold_per_symbol={}` now present in `_build_v3_model` (line 1379).
- `_verify_feature_columns` assertion updated: expects `== {}` not `== {"TRXUSDT": 21.0}`.
- `grep -E 'adx_threshold_per_symbol=\{"TRXUSDT": 21\.0\}'` finds only a comment line
  (line 211 inside docstring); no actual code.
PASS.

## Adversarial Tests Status

88/88 tests PASS at setup commit (verified by `uv run pytest tests/strategies/ml/ -v`).

Key suites verified:
- 7 primitive 10 tests: PASS (block_long_for=("BCHUSDT",) unchanged; all 7 fire correctly)
- 5 per-symbol ATR tests: PASS (ALGO/LDO (2.0, 1.5); BCH/TRX default (2.0, 1.0))
- 5 per-symbol ADX threshold tests: PASS (test_default_empty_dict_preserves_prior_behavior
  validates adx_threshold_per_symbol={} falls back to global 20.0 for all symbols)
- 7 regime gate tests: PASS (enable_regime_gate=False unchanged)
- 8 per-symbol cap tests: PASS (enable_per_symbol_cap=False unchanged)
- 4 CPCV embargo tests: PASS
- 4 clean-oof tests: PASS
- Remaining 48 regression tests: PASS

No new tests needed for iter-v3/050 (existing test_default_empty_dict_preserves_prior_behavior
covers the adx_threshold_per_symbol={} revert path explicitly).

## Bundle State Assertions (22 rows from §3.7)

```
V3_FEATURE_COLUMNS_TOP_N length == 14                               PASS (verified)
regime_momentum_signed_5d PRESENT in V3_FEATURE_COLUMNS_TOP_N      PASS (verified)
vol_normalized_ret_5d ABSENT from V3_FEATURE_COLUMNS_TOP_N         PASS (verified)
V3_ATR_MULTIPLIERS_PER_SYMBOL == {ALGO: (2.0,1.5), LDO: (2.0,1.5)}  PASS (verified)
DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)                               PASS (verified)
BTC_TREND_CONFIG.threshold_pct == 15.0                              PASS (grep)
V3_MODELS == 4 entries (BCH/LDO/TRX/ALGO); MKR absent              PASS (verified)
REQUIRED_GAP == 88                                                  PASS (verified)
ITERATION_LABEL == "v3-050"                                         PASS (verified)
ENSEMBLE_SIZE == 5 in runner                                        PASS (verified)
ensemble_size_for_run = 1 if args.exploration else ENSEMBLE_SIZE    PASS (grep)
fast_mode_for_run = bool(args.exploration)                          PASS (grep)
default --n-trials == 35                                            PASS (grep)
Seeds: 2 (invocation: --seeds 2)                                    PENDING (post-run)
--exploration NOT set (CONFIRMATION non-exploration mode)           PENDING (post-run)
comparison.csv produced with multi-seed metrics                     PENDING (post-run)
pareto_front.csv shows 2 distinct rows (Gate 10)                    PENDING (post-run)
Top-symbol concentration (multi-seed) (aspirational ≤30%)          PENDING (post-run)
Bundle-level OOS trade count ≥ 130 (aspirational)                  PENDING (post-run)
adx_threshold_per_symbol == {} (TRX 21 DROPPED)                    PASS (verified)
block_long_for == ("BCHUSDT",) UNCHANGED                            PASS (grep)
block_short_for == () UNCHANGED                                     PASS (grep)
```

PENDING rows are post-run verification items for the engineering report.

## Track Isolation

Checked via actual `import` grep (not comment lines):
- `grep -rn "^from crypto_trade.features " src/crypto_trade/features_v3/` → EMPTY. PASS.
- `grep -rn "^from crypto_trade.features_v2" src/crypto_trade/features_v3/` → EMPTY. PASS.

(The grep tool found comment strings in docstrings referencing the rule; no actual imports.)

## Data Freshness Check

Re-fetch performed at gate time:
- All 4 v3 symbols initially STALE (36.5h, exceeded 16h window).
- Re-fetched via `uv run crypto-trade fetch --symbols BCHUSDT,LDOUSDT,TRXUSDT,ALGOUSDT --intervals 8h`.
- Post-fetch age: 4.5h (all 4 symbols). PASS.
- Re-fetch documented in engineering report per Section 10 failure-mode table.

## Gate Decision

All 12 mandatory sections (0, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10) PRESENT and PASS.
Section 11 pre-commit catalog rows PRESENT (3 outcomes).
Section 12 self-check PRESENT.

One-variable rule: PASS (CONFIRMATION exemption; multi-seed is the test axis; ADX DROP
is mandatory state restoration per Critic, not a second research variable).
Forbidden-direction check: PASS (no closed axes violated).
REVERT-honoring check: PASS (ADX {TRXUSDT: 21.0} → {} applied and verified).
Stacking discipline check: PASS (CONFIRMATION stacking by design; OOS/IS Gate 3 is guard).
Adversarial tests: 88/88 PASS.
Track isolation: PASS (no actual imports from v1/v2 in features_v3/).
Data freshness: PASS (re-fetched; 4.5h < 16h window).
Bundle state: 22 assertions audited; 16 PASS at setup commit, 6 PENDING post-run.

OVERALL=PASS. Phase 6 may proceed after setup commit.

Setup commit: `feat(iter-v3/050): ITERATION_LABEL=v3-050 + DROP adx_threshold_per_symbol (multi-seed validation of cycle 3 best PROMISING bundle)`
Invocation: `PYTHONUNBUFFERED=1 uv run python run_baseline_v3.py --seeds 2 --clean-oof`
