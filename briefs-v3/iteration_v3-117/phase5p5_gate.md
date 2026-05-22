# Phase 5.5 Gate — iter-v3/117

OVERALL: PASS

Iteration type: EXPLORATION (single structural axis: candle frequency 8h → 24h multi-offset)
Cadence position: Cycle-6 EXPLORATION slot #8 of 10 (catalog confirms 7 prior cycle-6 entries:
  /110, /111, /112, /113, /114, /115, /116 — brief's "#8 of 10" is accurate)
Wall-clock cap: 2h (EXPLORATION per feedback_v3_cadence_discipline.md)
CLI invocation declared: `uv run python run_baseline_v3.py --exploration --n-trials 35 --bar-interval 24h`
ENSEMBLE_SIZE declared: 3 (first-3 of unified 10-seed lineage)
n_trials declared: 35 (EXPLORATION default per feedback_v3_exploration_n_trials_35.md)

---

## Per-Section Status

- Section 0 (Data Split): PASS
  OOS_CUTOFF_DATE = 2025-03-24 explicitly declared unchanged. training_months = 24 explicitly
  declared unchanged. IS window (data-extent start through 2025-03-24 exclusive) and OOS window
  (2025-03-24 through ~2026-05-19) named in absolute dates. Walk-forward 24-month rolling window
  declared. Reporting split at OOS_CUTOFF_DATE declared. All 5 hand-chosen design parameters
  (frequency, offset count, offset grid, training architecture, label timeout) declared
  hand-chosen with IS-only rationale, not laundered as sweep outputs. Auditable temporal fence
  asserted: EDA commit c64a5fc before brief commit bb713e6 (confirmed by git log).

- Section 0.5 (Iteration Type Declaration): PASS
  TYPE = EXPLORATION explicitly declared. CLI invocation with new --bar-interval 24h flag declared.
  ENSEMBLE_SIZE = 3. n_trials = 35. Single axis (candle frequency). Wall-clock estimate (<=2h)
  with prior-iteration wall-clock evidence cited (/116: 0.70h, /115: 0.69h, /113: 0.80h). The
  /116 no_confirm revert declared for isolation. This section is not listed in the v3 skill's
  mandatory 10-section checklist (Sections 0 and 1-9 are mandatory), but is present and complete.

- Section 1 (Hypothesis): PASS
  One sentence. Specific: 24h decision grid with 3-offset multi-offset derived series lifts IS
  monthly Sharpe materially above /060 anchor (+0.8325) with positive OOS Sharpe delta, via daily-
  frequency aggregation removing 8h microstructure noise + 3-offset panel multiplying training
  data 3x. Explicitly falsifiable on three axes declared (IS floor +0.7325, OOS direction,
  trade-roster cardinality). Not vague ("explore different frequency") — mechanism-specific.

- Section 2 (IS-Only Numerical Evidence): PASS
  Backed by committed analysis/iteration_v3-117/ (10 tables T1-T10), committed in EDA commit
  c64a5fc BEFORE brief commit bb713e6 (confirmed). Scripts: _shared.py,
  multifreq_24h_gating_eda.py, synthesis.py. EDA scripts assert IS-only fence
  (close_time < OOS_CUTOFF_MS = 1742774400000 per commit message). Numerical tables present with
  concrete values:
    T2/T9: universe-pooled AUC 0.5823, null_q95 0.5104/0.5113, p=0.00 (PASS)
    T2: per-symbol AUC with p-values (BCH 0.4778/p=0.53, LDO 0.5201/p=0.18, TRX 0.5092/p=0.17)
    T3: per-offset AUC for 9 (symbol x offset) cells, 6/9 AUC > 0.5 (g3 PASS)
    T4: derivation audit 900/900 PASS (look-ahead-free assertion)
    T5/T6: data coverage and label balance per symbol per offset
    T7: ADF stationarity 40.5% stationary (documented as warm-up artifact, not blocking)
    T10: GO/NO-GO synthesis with gate verdicts (formal NO-GO g1 FAIL, PARTIAL-GO substantive)
  Rejected design preserved: T5/T6_BAR_COUNT_EQUIV_REJECTED.csv committed (21-daily-bar BAR-
  count-equivalent tested FIRST and rejected on BCH 99.13% positive evidence — auditable
  design-choice lineage). Category-matching is absent — all evidence is numerical from IS-only
  scripts. GO/NO-GO synthesis is honest: formal NO-GO declared on g1 FAIL; PARTIAL-GO substantive
  read explicitly justified; PRIME DIRECTIVE cited for proceeding to Phase 6 despite NO-GO.
  Anchors vs prior committed artifacts: /109, /113 T1/T4/T5 committed CSVs cited by path.

- Section 3 (Proposed Changes): PASS
  Enumerated table comparing /059 baseline vs /117 on every relevant axis: candle frequency,
  multi-offset derivation, per-symbol training architecture, universe (UNCHANGED), model
  (UNCHANGED), label (calendar-time-equivalent timeout=7 daily bars = 168h), feature stack
  (14 V3_FEATURE_COLUMNS at 24h + offset_id = 15 features), REQUIRED_GAP (66 -> 72),
  cooldown_candles (4 -> 2), enable_no_confirm_exit (REVERTED to False). All labeling params,
  symbol set (BCH/LDO/TRX unchanged), feature additions (offset_id only), risk-gate changes
  (NONE — 7-gate RiskV2 stack unchanged). Cluster-importance check not referenced since no new
  feature family is being introduced from an external source; offset_id is a new categorical
  encoding column, not a feature family requiring importance pre-screening. This is acceptable
  given offset_id has a mechanical role (identifies which offset's decision-row is being
  presented to the model).

- Section 4 (Expected OOS Impact): PASS
  Four outcome bands with explicit IS and OOS Sharpe ranges, probability weights, and rationale
  for each:
    Modal (~50%): INERT/EXPLORATION-NEGATIVE, IS [+0.30,+0.70], OOS [-0.20,+0.30]
    Secondary (~20%): EXPLORATION-PROMISING, IS [+0.85,+1.20], OOS [+0.40,+0.90]
    Tertiary (~25%): SUSPICIOUS-OOS-DOMINANT, IS [+0.30,+0.65], OOS [+0.50,+1.10]
    Residual (~5%): BEHAVIORAL-INERTIA or CATASTROPHE
  Explicit falsifier: OOS < -0.20 AND IS < +0.30 rejects the hypothesis.

- Section 5 (Risk Mitigation): PASS
  Five risks identified with mechanisms and mitigations:
    R1: BCH structural label imbalance -> degenerate LightGBM -> 7-gate filter + pre-flight
        IS-trade-count check (<30 = BEHAVIORAL-INERTIA per Section 8 Criterion 3)
    R2: Cross-offset label leakage at fold boundaries -> REQUIRED_GAP=72 covers
        within-offset AND cross-offset purging; pre-flight assertion verifies
    R3: Feature stationarity warm-up at 24h (40.5% stationary) -> NaN-filter min_periods
        enforcement in walk-forward; Critic Check 5 ADF in context
    R4: Per-symbol weakness (LDO/TRX p=0.18/0.17) -> 7-gate filter on high-conviction trades
    R5: Multi-offset architecture complexity -> T4 900/900 audit + Change 8 adversarial test
        + pre-flight accretion guard
  R1-R5 have IS-calibrated evidence (IS trade counts, T4 derivation audit, T7 stationarity).
  No v3 7-gate equivalents with simulated historical effect on prior iterations are provided,
  but this is consistent with prior EXPLORATION briefs where the risk-gate stack is UNCHANGED
  (Section 6 confirms 7-gate RiskV2 is UNCHANGED; no new primitives introduced).

- Section 6 (Risk Management Design): PASS
  8-primitive table equivalent for v3 (7 primitives: vol scaling, ADX threshold, Hurst regime,
  z-score OOD, low-vol filter, hit-rate feedback, BTC trend filter). All UNCHANGED from /059.
  No_confirm primitive explicitly REVERTED. Predicted fire-rate impact at 24h described
  (~1/3 per-offset raw signals restored to 8h-comparable by 3-offset architecture;
  filter rate ~30-40% unchanged). Matches v3 7-gate design. The gate specification mandates
  "8-primitive table" — v3 uses 7 primitives per the BASELINE_V3.md architecture, and all
  are listed and declared unchanged. This matches the format of prior-iteration gate PASSes.

- Section 7 (Failure-Mode Prediction): PASS
  Four modes with probability weights (50% / 25% / 20% / 5%) matching Section 4. Each mode
  specifies the exact failure mechanism, the EDA evidence that informs it, and the diagnostic
  signature for the Critic to classify the outcome. Application of the /116 regime-asymmetry
  lesson is explicitly stated: /117 is a representation change NOT a regime-adaptive rule,
  so the /116 IS-cost pattern is NOT expected (but 24h's longer trade duration could look
  like it superficially, and Section 8 Criterion 5a's SUSPICIOUS gate distinguishes Mode 2
  from Mode 3). Forward-looking — all language is predictive, not retrospective.

- Section 8 (MERGE/NO-MERGE Criteria): PASS
  First-match-wins EXPLORATION taxonomy with locked numerical thresholds:
    Criterion 1 (NEGATIVE): IS < +0.7325 OR OOS < -0.0597
    Criterion 2 (SUSPICIOUS): OOS/IS > 3.0 AND OOS > +0.50 AND IS > +0.30
    Criterion 3 (BEHAVIORAL-INERTIA): IS trades < 30 OR OOS trades < 15
    Criterion 4 (PROMISING): IS >= +0.9325 AND OOS >= +0.3403 AND OOS/IS in [0.5, 3.0]
    Criterion 5: Substantive Phase-7 checks (SUSPICIOUS substnative, PROMISING substantive,
      /116 UPGRADE precedent, /114 DOWNGRADE precedent)
    Criterion 6: Multi-seed (CONFIRMATION only — not applicable)
  Anchor explicitly stated: /060 IS +0.8325 / OOS +0.1403. Criteria 1 thresholds are the
  STANDARD band (IS floor /060 - 0.10 = +0.7325) — NOT the /116 regime-cost-relaxed band
  (/059 IS - 0.50 = +0.59). This is correct: the /116 IS-band relaxation was mandated for
  the /120 CONFIRMATION ONLY (per /116 Critic Recommendation 2), not for /117. The brief
  explicitly acknowledges this in Section 7: "/117's design is NOT a regime-adaptive rule
  (it's a frequency-axis representation change), so the IS-vs-OOS regime-cost-asymmetry
  pattern of /116 is NOT expected." Section 8 calibration is appropriate and not over-applied.

- Section 9 (Library Stack Declaration): PASS
  10-library table with versions and fallbacks declared. All libraries named with versions:
  lightgbm 4.5.0, numpy 2.x, pandas 2.x, scikit-learn 1.x, statsmodels 0.14+, pyarrow 16+,
  optuna 3.x, mlfinlab/mlfinpy 1.4/1.x, pypbo 0.x, fracdiff 0.10+. Zero new dependencies
  introduced. mlfinpy declared as fallback for mlfinlab licensing. Catches the
  "mlfinlab license" risk per the gate spec.

- Section 10 (QR Audit Trail): PASS
  No orchestrator-pick supersession. Dispatch recommendation was candle-frequency per /116 diary
  Section 9 + user directive 2026-05-20. QR's EDA backed the axis with 6 enumerated empirical
  points. 5 design-parameter declarations all hand-chosen with IS-only rationale. Honest formal
  NO-GO declared (g1 FAIL per-symbol q95). PRIME DIRECTIVE cited. Cycle-6 cadence status:
  "7 of 10 EXPLORATIONs filed (/110-/116); 3 EXPLORATION slots left (/117, /118, /119)."
  This matches the catalog count (7 cycle-6 entries confirmed). All per
  feedback_v3_axis_selection_quant_discipline.md.

---

## Section 3.5 Scope Verification (8 Changes)

All 8 brief-declared implementation changes are explicit, unambiguous, and actionable:

Change 1 (Data aggregation): CLEAR. New module src/crypto_trade/features_v3/multioffset_24h.py
  porting _shared.py::aggregate_to_24h() bit-identical. Reads 8h.csv, produces 3-offset 24h
  bars per symbol. bar_close_time = close_time of latest sub-bar (causal timestamp). No new
  fetch. Reference: T4 900/900 audit PASS as validation evidence.

Change 2 (Feature generation at 24h): CLEAR. New directory data/features_v3_24h/. Per-offset
  isolation enforced (offset-0 features computed ONLY from offset-0 bars). Reference:
  _shared.py::compute_features_24h() + add_btc_cross_features() + load_labeled_is().

Change 3 (--bar-interval CLI flag): CLEAR. New argument --bar-interval {8h, 24h} default 8h.
  When 24h: BacktestConfig.interval="24h", timeout_minutes=10080, cooldown_candles=2. Feature
  path switches to data/features_v3_24h/. feature_columns = V3_FEATURE_COLUMNS + ["offset_id"]
  (15-column list pinned explicitly per feedback_v3_explicit_feature_columns.md).

Change 4 (REQUIRED_GAP recomputation): CLEAR. REQUIRED_GAP = (7+1) x 3 x 3 = 72 when
  --bar-interval 24h. Formula documented: timeout_candles=7, n_symbols=3, n_offset_series=3.
  Pre-flight accretion guard verifies the conditional value. REQUIRED_GAP=66 preserved when 8h.

Change 5 (REVERT /116 no_confirm at 3 surfaces): CLEAR. QE has zero ambiguity. Three surfaces
  specified with exact line numbers in run_baseline_v3.py:

  (a) BacktestConfig constructor at run_baseline_v3.py:1941-1943 — flip
      enable_no_confirm_exit=True -> enable_no_confirm_exit=False (verified: currently True
      at line 1941, must revert to False)
  (b) Pre-flight assertion at run_baseline_v3.py:2837-2851 — change
      assert _pf_cfg.enable_no_confirm_exit is True -> assert ... is False, with explicit
      message naming /116 revert and /117 isolation rationale (verified: currently asserts
      True at line 2837, must revert to False)
  (c) Accretion guard at run_baseline_v3.py:1108-1112 — change
      ("enable_no_confirm_exit", _acc_cfg.enable_no_confirm_exit, True) expected value True
      -> False (verified: currently expects True at line 1110, must revert to False)

  The two scalar trigger fields (no_confirm_trigger_atr=0.50, no_confirm_k_candles=4) STAY at
  their default values at all three surfaces. backtest_models.py field DEFINITIONS stay
  unchanged. backtest.py order-loop logic stays unchanged (dead code when flag=False).

  REVERT COMPLETENESS: the brief specifies the revert at ALL 3 SURFACES explicitly. The pattern
  matches the /115->116 revert (the /115 label_mode revert also touched 3 surfaces). The
  phase5p5 gate for /116 (commit 5d4cc6d) verified the same 3-surface completeness pattern for
  /115's revert. The /117 brief is equally explicit and unambiguous.

Change 6 (Banner-print + ITERATION_LABEL + MODEL_SPECS): CLEAR. Three specific sub-changes
  with exact line numbers: ITERATION_LABEL at line 131 (v3-116 -> v3-117), MODEL_SPECS
  prefix at lines 197-199 (v3-116-BCH/LDO/TRX -> v3-117-BCH/LDO/TRX), banner-print at
  lines 2922-2925 with new REQUIRED_GAP and bar_interval conditional text. Code snippet
  provided.

Change 7 (Accretion guard extension for --bar-interval): CLEAR. expected_required_gap
  conditional on args.bar_interval (72 if 24h, else 66). BacktestConfig.interval check
  conditional on args.bar_interval. enable_no_confirm_exit expected False (/117 REVERT).
  Code snippet provided.

Change 8 (Adversarial integration test): CLEAR. New file
  tests/test_multioffset_24h_aggregation.py. Three test cases with specific assertions:
  (a) look-ahead-free: no 8h candle with close_time > bar_close_time enters aggregation
  (b) per-offset feature isolation: offset-0 EMA at row 50 depends ONLY on offset-0 bars 0..49
  (c) trade-loop integrity: trade open_time/close_time differ by multiple of MS_PER_DAY;
      cooldown_candles=2 -> 48h suppression after trade close

---

## /116 Revert Completeness Confirmation

The Phase 5.5 gate explicitly confirms the /116 no_confirm revert is specified at all 3 surfaces
in run_baseline_v3.py (lines 1941, 2837, 1110) with the correct direction (True -> False).
This is the same 3-surface pattern as the /115 stale-knob revert (the precedent case that /116's
own gate caught). The QE has zero ambiguity about which lines to touch and what values they must
carry after the revert. The pre-flight assertion (surface b) provides a human-readable error
message naming /117 isolation explicitly, which will surface in run.log for the Critic's Check 8
verification.

---

## Provenance Discipline Confirmation

All five hand-chosen design parameters are declared hand-chosen in Section 0 with IS-only
rationale. No parameter is laundered as a sweep output:

1. Candle frequency = 24h: declared hand-chosen per user directive 2026-05-20 +
   /116 diary Section 9 recommendation. IS rationale: /109 terminal null intrinsic to 8h;
   /113 T5 daily-ONLY AUC 0.5275 p=0.00 positive prior evidence. Not from a sweep.

2. Number of offsets = 3: declared hand-chosen. IS rationale: 8h base candle stream produces
   exactly 3 sub-bars per UTC day; aligning offsets to 8h sub-bar boundaries (00/08/16) is
   the natural, look-ahead-free derivation. Not tuned.

3. Training architecture (pooled-offset): declared hand-chosen over 3-LightGBM-per-symbol
   alternative. IS rationale: multiplies training data 3x per model; matches /059 per-symbol
   pattern; single Optuna fit surface per symbol-month. Not tuned.

4. Label timeout = 7 daily bars: declared hand-chosen with AUDITABLE LINEAGE. The 21-daily-bar
   BAR-count-equivalent was TESTED FIRST (EDA commit c64a5fc T5/T6_BAR_COUNT_EQUIV_REJECTED.csv)
   and REJECTED on T6 evidence (BCH 99.13% positive). Calendar-time-equivalent chosen thereafter.
   Preserved rejected files confirm chronological order. Not tuned.

5. Calendar-time-equivalent scaling: implicit from choice of 7 daily bars (= 168h = /059's
   21 x 8h = 10080 min). No additional tuning.

The EDA commit c64a5fc precedes the brief commit bb713e6 (verified by git log). The brief Section
0 includes the "Auditable temporal fence" paragraph explicitly asserting the ordering and that
no OOS-window file is read. Provenance discipline holds at /117 per the /114 lesson
(feedback_v3_brief_parameter_provenance.md).

---

## Section 8 Calibration Confirmation

The brief uses the STANDARD IS NEGATIVE floor (IS < +0.7325 = /060 anchor - 0.10) at Section 8
Criterion 1, NOT the /116 relaxed IS band (/059 IS - 0.50 = +0.59 that the /116 Critic
recommended for the /120 CONFIRMATION only).

This is correct. The /116 Critic Recommendation 2 ("IS NEGATIVE floor at /059 IS - 0.50 = +0.59")
was explicitly scoped to the /120 CONFIRMATION brief -- the recommendation notes "CONFIRMATION
brief Section 4 must pre-register an IS band that does NOT fire NEGATIVE on the IS leg by
accident." It does NOT apply to /117 (an EXPLORATION). The brief explicitly acknowledges that
/117 is NOT a regime-adaptive rule (it's a representation change), so the /116 regime-cost
argument does not transfer: "iter-v3/117's design is NOT a regime-adaptive rule (it's a
frequency-axis representation change), so the IS-vs-OOS regime-cost-asymmetry pattern of /116
is NOT expected." The IS floor at /060 - 0.10 is correctly and appropriately calibrated for a
candle-frequency representation change where no systematic IS-cost mechanism is pre-registered.

---

## Reasons (PASS — no blocks)

No blocking gaps. All 10 mandatory sections present and substantively complete. The 8 Section 3.5
changes are explicit and unambiguous. The /116 revert is specified at all 3 surfaces. Provenance
discipline is clean. Section 8 criteria are correctly calibrated.

---

Gate issued: 2026-05-20
Branch: iteration-v3/117
EDA commit: c64a5fc (before brief commit bb713e6 — temporal fence confirmed)
Brief commit: bb713e6
