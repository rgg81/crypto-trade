# Phase 5.5 Gate — iter-v3/093

**OVERALL: PASS**

Gated by: Quant Engineer (QE)
Date: 2026-05-18
Branch: `iteration-v3/093`
Brief SHA: `5bb5a76`
EDA SHA: `359bd74`

---

## Per-Section Status

- **Section 0 (Data Split)**: PASS — `OOS_CUTOFF_DATE = 2025-03-24` / `training_months = 24` stated
  and flagged IMMUTABLE; the IS and OOS windows are named (`[first_kline + 24mo, 2025-03-24)` and
  `[2025-03-24, present)`). The OI-deferral is disclosed explicitly (Section 2.7). Section 0
  cross-references the runner's cutoff millisecond literal (`1742774400000`).

- **Section 1 (Hypothesis)**: PASS — the hypothesis is specific and architectural: "a model whose
  prediction target is a forward derivatives-microstructure state (3-state vol-regime) and whose
  feature panel is the derivatives-microstructure state (funding + basis + OI) carries genuine
  forward predictive information that price-only models structurally cannot see; a
  regime-CONDITIONED book converts that predictive content into a Sharpe improvement primarily
  through drawdown avoidance." The hypothesis names the mechanism (drawdown avoidance, not carry
  collection), distinguishes itself from /082 (the label is a derivatives-state object, not a
  price barrier), and states the carry-decay rationale. It is one architectural claim, not a
  vague category.

- **Section 2 (IS-Only Numerical Evidence)**: PASS — committed IS-only EDA (`359bd74`,
  `analysis/iteration_v3-093/derivatives_microstructure_eda.py`) with five committed CSVs (T1-T5).
  Evidence verified against the committed CSVs:
  - T2 best mean regime-IC across core symbols: `f_rate` at H=21 = +0.2128 (BCH), +0.1427 (TRX);
    `f_sign_persist_9` at H=21 = +0.2576 (BCH); brief's reported mean (+0.1819 / +0.1699)
    consistent with the per-symbol rows in T2. The 8-of-39 measurements clearing the |IC| > 0.05
    bar is verified. T5 summary CSV: `best_vol_regime_feature = f_rate`, `best_vol_regime_ic =
    0.18187` — matches brief Section 2.1.
  - T3 deleveraging lift verified: core BCH H=3 lift = 1.2977, LDO H=3 = 1.44, TRX H=3 = 1.241;
    brief's reported range 1.11-1.37 (mean H=21) consistent. Wide-universe lift cross-check
    matches (GALA/HBAR/ICP H=3 lifts 1.38-1.54 in T3).
  - T4 orthogonality: max |IC| vs any price feature is 0.3211 (core) — brief states 0.321, exact
    match; all 13 derivatives features pass the <0.70 Critic Check-4 ceiling, confirmed by T4
    `check4_pass_ic_lt_0p70 = True` for all rows.
  - Walk-forward fidelity: EDA enforces `_is_test_window` per-symbol as `[first_kline + 24mo,
    OOS_CUTOFF_MS)` (lines 40-49 of EDA script), matching the runner's IS span exactly. The /091
    mistake is not repeated.
  - The OI deferral is honest and bounded: Section 2.7 states plainly what is and is not
    evidenced, and the architecture does not depend on OI being predictive for the GREEN-LIGHT
    conclusion (funding+basis IC is sufficient). OI is additive; its IS-validation is deferred to
    Phase 6 integration test #5 (Section 9).

- **Section 3 (Proposed Changes)**: PASS — the re-architecture spec is enumerated with enough
  precision for zero-research-decision implementation:
  - Universe: BCH/LDO/TRX (Section 3.0, justified).
  - Layer 1: 18-feature panel named feature-by-feature with group/formula/convention references
    (Section 3.1); the 5 OI features spec'd against the verified `metrics` schema.
  - Layer 2: multi-class `objective="multiclass"` LightGBM; forward 21-bar realized-vol terciles;
    train-window-only cut-points; 5-seed ensemble; Optuna n_trials=35; walk-forward with `e149e9d`
    embargo + 24-month window (Section 3.2).
  - Layer 3: smooth probability-weighted size multiplier `1.0·P(calm) + 0.6·P(normal) +
    0.0·P(stressed)`; hard-argmax fallback noted as robustness check (Section 3.3).
  - Runner: `run_derivatives_regime_v3.py`, `ITERATION_LABEL = "v3-093"`, 6 enumerated Phase-6
    setup items (Section 3.4/3.5).
  - `fetch-oi` CLI subcommand fully described: source (`data/futures/um/daily/metrics/<SYM>/`),
    target (`data/open_interest/<SYM>/8h.csv`), resample from 5-min `metrics` rows, incremental.

- **Section 4 (Expected OOS Impact)**: PASS — the expected-impact table is honest (modal
  expectation: modest OOS Sharpe improvement driven by drawdown avoidance; drawdown the
  highest-confidence prediction). Six numerical falsifiers pre-registered (F1-F6) with explicit
  anchor numbers distinct from the Section-4.1 estimates. F6 is the behavioral-effect predictor
  per `feedback_v3_axis_saturation_predictor.md` (pre-registered gate-fire band [8%, 45%];
  estimate [20%, 40%]; the two are correctly different numbers). MERGE/NO-MERGE classification
  locked in Section 8 (this is an EXPLORATION; it cannot merge).

- **Section 5 (Risk Mitigation)**: PASS — R-gate (the regime gate itself), R1, R2, R3, R4, R5 all
  addressed. IS-calibrated thresholds: multipliers {1.0, 0.6, 0.0} justified by the Test-3 lift
  profile. Simulated historical effect stated (the gate would have zeroed ~33% of IS bars; the
  IS conditional-forward-return on risk-state bars is positive but the vol reduction dominates).
  The gate is described as trading a small expected-return give-up for a large vol reduction.

- **Section 6 (Risk-Management Design)**: PASS — five structural defenses enumerated: balanced
  label (equal-mass terciles), monotone-conservative gate (never adds leverage), proven base book
  (/059), genuine DSR/PBO/PSR from day one, walk-forward IS-fidelity. The largest structural risk
  (OOS IC transfer failure) is named, its probability estimated (≈40% NEGATIVE-no-effect), and
  F2/F3 are the direct detection mechanism.

- **Section 7 (Failure-Mode Prediction)**: PASS — five outcomes pre-registered with honest
  probabilities (≈40% NEGATIVE-no-effect, ≈25% PROMISING, ≈15% SUSPICIOUS, ≈12%
  NEGATIVE-trade-starvation, ≈8% NEGATIVE IS-break; sum = 100%). The modal failure is the
  regime-IC OOS transfer failing. Forward-looking, specific, and consistent with v3's base rate.

- **Section 8 (MERGE/NO-MERGE Criteria)**: PASS — five-class disjunctive taxonomy with locked
  precedence (8.1 SUSPICIOUS → 8.2 NEGATIVE-no-effect → 8.3 NEGATIVE-harmful → 8.4
  NEGATIVE-trade-starvation → 8.5 PROMISING). Each class has a numerical criterion. The
  PROMISING class requires ALL six falsifiers to NOT fire. The /103 CONFIRMATION bundle path is
  named. No ambiguity in the classification sequence.

- **Section 9 (Library Stack + Integration-Test Mandate)**: PASS — library stack pinned
  (lightgbm 4.6.0, optuna 4.8.0, numpy/pandas/sklearn/scipy/statsmodels/pyarrow) with no new
  third-party dependency. Six mandatory integration tests named with their assertions:
  #1 (`test_dsr_json_is_computed`) is the structural /092-anti-recurrence guarantee; #5
  (`test_oi_feature_ic_check`) is the deferred OI-leg validation. Both are marked as hard build
  items. The QE engineering report must cite the `validation_v3` call-site and SR granularity
  per `feedback_v3_methodology_post_hoc_input_traceback.md`.

---

## Specific-Item Resolutions (items 1-6 from the Phase 5.5 dispatch)

### Item 1 — Single-axis integrity: PASS

The brief keeps the /059 base directional book bit-UNCHANGED. Section 3.3 states explicitly: "The
base directional signal is the existing `v0.v3-059` per-symbol price-barrier LightGBM book — the
canonical baseline book, UNCHANGED." Section 3.5 run-config table row: "Base directional book:
`v0.v3-059` per-symbol price-barrier LightGBM (UNCHANGED)." The regime gate multiplies position
size by a scalar in [0.0, 1.0] after the /059 book has emitted the trade signal; it does not alter
the /059 book's features, label, model, or risk gates. R1/R2/R3/R5 are inherited "unchanged."
There is no second axis — the single variable is the regime-conditioned size overlay.

### Item 2 — Regime-gate differentiation from prior failures: PASS

The brief makes the case explicitly and credibly (Section 1, Section 3.3, Section 10). The two
prior v3 regime-gate attempts failed because:
- iter-v3/022: a regime gate later disabled; the regime variable was price-derived.
- iter-v3/074: a binary kill switch, price-derived regime signal, classified INERT.

The /093 differentiation is twofold and structural:
1. The signal source is genuinely new (derivatives-microstructure: funding/basis/OI), not a
   re-encoding of price. T4 confirms max |IC| vs any price feature ≤ 0.321 — the orthogonality
   is measured, not asserted.
2. The gate is a smooth probability-weighted size multiplier (continuous [0.0, 1.0]), not a
   binary kill switch. A soft gate degrades gracefully under mis-classification; the prior binary
   gate had a knife-edge that fired too often (iter-v3/074's INERT verdict) or too rarely.

The /082 funding-axis ban is also addressed directly: /082 failed because funding was a *feature*
on a *price-barrier label* and ranked 15-18/18 in importance; the label itself was a price object.
Here the *label* is the derivatives state (forward vol-regime), making funding/basis/OI the
primary signal. The /082 closeout §11 Rec 1 explicitly names this as the exempted construction.
The Section 1 argument is substantial and IS-evidenced (the IC +0.18 vs vol-regime vs IC −0.08
vs returns is the quantitative proof of architectural choice).

### Item 3 — Stateless vs stateful gate: PASS (stateless; ORACLE EDA valid)

The regime-size-multiplier is STATELESS. Per Section 3.3: the /059 base book emits ALL its trades
normally (the base book's R1 streak tracking, R2 drawdown scaling, and position-entry logic are
all inherited unchanged); the regime gate then scales each position's SIZE by the probability-
weighted multiplier. The gate does not suppress signal emission, does not update the base book's
persistent state (no cooldown interaction, no R2 peak interaction), and does not create a feedback
loop. A mis-classified stressed bar results in a smaller position, not a suppressed trade that
leaves R1/R2 state frozen.

This satisfies the `feedback_v3_oracle_eda_validity.md` condition for ORACLE EDA validity: the
gate is stateless, so EDA on the /059 trade roster correctly represents what the gated book will
produce. The iter-v3/054 deadlock pattern (drawdown brake entered permanent deadlock because
gating suppressed trade emission and froze state) CANNOT recur: the /093 gate never suppresses a
trade from being entered — it only changes its SIZE. The base book's state always updates.

Integration test #4 (`test_regime_gate_is_monotone_conservative`) enforces the size multiplier
in [0.0, 1.0] at the unit-test level, which is the necessary condition for the gate being
exposure-reducing-only.

### Item 4 — Label leakage + embargo: PASS

The brief is specific on all three leakage surfaces:
- Tercile cut-points: Section 3.2 states "The tercile cut-points are computed per-symbol on the
  TRAINING window only (the trailing 24 months) — past-only, no look-ahead, recomputed each
  walk-forward month." Integration test #3 (`test_vol_regime_label_uses_train_window_cutpoints`)
  asserts this invariant.
- Forward-vol label as feature: Section 3.2 states the label is "used only as the training
  target, never as a feature." The 18-feature panel (Section 3.1) contains no forward-looking
  element; all features are past-only via `.shift(1)`. Integration test #2
  (`test_no_lookahead_in_derivatives_panel`) enforces the past-only invariant.
- Walk-forward embargo: the forward 21-bar label requires an embargo of at least 22 candles. The
  brief states "Embargo: `e149e9d` walk-forward fix, 22 candles" (Section 3.5). The existing
  `compute_embargo_candles(timeout_minutes=10080, interval_minutes=480)` → 22 covers the 21-bar
  forward horizon (21 + 1 = 22 candles). Integration test #6
  (`test_walk_forward_embargo_intact`) asserts the embargo is present and load-bearing.

One potential ambiguity: the L2 vol-regime classifier and the L1/L3 /059 base book have the
SAME embargo (22 candles), which is correct — the 21-bar forward vol label uses the same
timeout horizon as the /059 triple-barrier label (both are 10,080-minute timeouts = 21 bars).
The brief is consistent. No leakage gap detected.

### Item 5 — OI deferral assessment: ACCEPTABLE (not a BLOCK)

The OI feature group (5 features in Section 3.1) lacks IS-window evidence at brief submission
time. The brief handles this honestly and with structural safeguards:
- Section 2.7 states the OI deferral plainly: the architecture does not depend on OI being
  predictive for the green-light conclusion; funding+basis already clear the IS bar.
- The cycle-4 prep memo verified the `metrics` archive schema and full-window coverage for
  BCH/LDO/TRX — the data-availability question is resolved; the predictive-content question is
  what is deferred.
- Integration test #5 (`test_oi_feature_ic_check`) is a hard Phase-6 build item: after `fetch-oi`,
  it asserts ≥ 0.90 coverage and prints the OI features' IS vol-regime IC to a committed artifact
  (`analysis/iteration_v3-093/oi_leg_ic.csv`). The Phase-7 QR reads that artifact.
- The F6 behavioral band (stressed-fire rate [8%, 45%]) implicitly catches an OI-pathology
  scenario where a degenerate OI feature drives the regime classifier to always-stressed.

The OI deferral is NOT a Section-2 completeness block because: (a) the EDA's principal claim
(derivatives state predicts the vol regime) is fully supported by the funded+basis evidence; (b)
OI is an additive leg with a strong literature prior; (c) the Phase-6/7 validation path is
explicitly specified and gated by an integration test. This is meaningfully different from a
deferral of the primary evidence — which WOULD be a block.

### Item 6 — DSR/PBO/PSR anti-recurrence mandate: PASS

The brief's Section 9.2 directly integrates all three /092 Critic Recommendations:
- Rec #1 (import and CALL `validation_v3.psr` and `deflated_sharpe_ratio_v3`): the Section 3.4
  runner description states it "carries genuine CONFIRMATION-grade DSR/PBO/PSR machinery from
  day one... imports and CALLS `validation_v3.psr`, `validation_v3.deflated_sharpe_ratio_v3`,
  `validation_v3.pbo_from_cpcv` on the genuine OOS monthly-return series — NEVER hardcoded
  `0.0`/`NaN` sentinels."
- Rec #2 (dsr.json integration test): integration test #1 (`test_dsr_json_is_computed`) asserts
  the `dsr.json` `dsr`/`psr` fields are finite computed values (not `0.0`/`NaN` literals) and
  `pbo` is a genuine fraction in [0,1] OR an explicitly-noted structural sentinel. The brief
  states "a Phase-6 build that omits the DSR/PBO/PSR machinery MUST fail the suite before the
  backtest runs" — a source-level `grep` assertion + a value-level finiteness assertion.
- Rec #3 (engineering report must cite exact call-site): this is a Phase-6 QE build constraint,
  not a brief content requirement. The brief names it in Section 9.2: "the Phase-6 engineering
  report MUST cite the exact `validation_v3` call-site and the SR granularity fed to `psr()`."

The Phase 5.5 gate verifies the brief specifies all three. It does. The /090→/092 defect class
is pre-empted at the brief level; whether the QE honours it in Phase 6 is what integration
test #1 enforces at build time.

---

## Additional Observations (informational, not blocking)

- **EDA proxy features**: the EDA uses `proxy_taker_imb` and `proxy_vol_surge_z` (reconstructed
  from OHLCV) as OI surrogates. These are NOT in the 18-feature panel spec in Section 3.1 (which
  names the genuine `oi_log_delta_1`, `oi_zscore_30`, etc.). The EDA is appropriately using
  them as *placeholders* pending the `fetch-oi` build; the EDA's 13-feature panel is a
  subset/proxy of the brief's 18-feature panel. This is coherent with the OI-deferral. No
  misleading claim in brief Section 2 — the hedging is explicit.

- **F4 threshold (OOS trades < 80)**: the brief states the /059 base book has 94 OOS trades and
  the gate must not zero >15% of them. 15% of 94 = 14.1, so 80 is the threshold. The arithmetic
  is consistent. However, the gate can zero MORE than 15% of trades if stressed-regime fires on
  > 15% of bars AND those bars happen to be entry bars. The brief acknowledges this risk in
  Section 4.2 and in Section 7's ≈12% NEGATIVE-trade-starvation path. F4 is the correct
  post-hoc catch, not a pre-flight guarantee.

- **The /059 base book as a "frozen oracle"**: the brief's EDA and gate design implicitly treat
  the /059 trade roster as known (ORACLE EDA, Item 3 above). This is valid because the gate is
  stateless. The QE should verify in Phase 6 that `run_derivatives_regime_v3.py` runs the /059
  base book unmodified (not a retrained version) so the IT IS the same roster as the canonical
  anchor — not a re-optimized one.

- **EXPLORATION spec compliance**: single outer seed = 42, ENSEMBLE_SIZE = 5, n_trials = 35,
  wall-clock cap 2h. Consistent with `feedback_v3_exploration_n_trials_35.md`,
  `feedback_v3_strict_10_to_1_cadence.md`, `feedback_v3_v1_ensemble.md`,
  `feedback_v3_cadence_discipline.md`. No CONFIRMATION gates invoked (Section 8 correctly
  designates PROMISING as the top outcome at EXPLORATION).

---

## Reasons (BLOCK items)

None.

---

**OVERALL = PASS**

Phase 6 may proceed. The QE must:
1. Implement the `fetch-oi` subcommand before running the backtest.
2. Ship all six integration tests in `tests/strategies/ml/test_derivatives_regime.py` and
   confirm test #1 fails without the DSR/PSR call-sites (i.e., test it actually gates the build).
3. Run the OI-leg IC check (integration test #5) after `fetch-oi` and commit
   `analysis/iteration_v3-093/oi_leg_ic.csv` before the backtest.
4. Verify the /059 base book is loaded as frozen (not retrained) in the new runner.
5. In the engineering report, cite the exact `validation_v3` call-site lines and the SR
   granularity (monthly vs trade-level) fed to `psr()`.
