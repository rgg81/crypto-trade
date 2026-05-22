# Phase 5.5 Gate — iter-v3/110

OVERALL: PASS

Iteration type: EXPLORATION
Cadence position: Cycle 6, EXPLORATION #1 of 10 (iter-v3/110–119; iter-v3/120 mandatory CONFIRMATION)
Wall-clock budget declared: HARD CAP 2h (PASS — ≤ 2h; run config `--exploration --seeds 1 --n-trials 35`)
Single-axis variation: PASS — ONE axis changed (symbol universe `V3_MODELS`, 3→4 symbols); features,
  labeling, model architecture, and 7-gate RiskV2 stack all declared /059-identical.
Run config: PASS — `--exploration --seeds 1` (ENSEMBLE_SIZE forced to 1 by `--exploration`; no outer
  seed loop; single deterministic path)

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` explicitly
  stated UNCHANGED/IMMUTABLE. IS window named per symbol with candle counts (≥4653 each, all ≥24 months).
  OOS window named as 2025-03-24 → ~2026-05-18. EDA loader asserts `close_time < OOS_CUTOFF_MS`
  (1742774400000) per symbol before any computation.

- Section 0.5 (Iteration Type): PASS — TYPE: EXPLORATION declared. Wall-clock budget ≤ 2h stated as
  HARD CAP. Run config `--exploration --seeds 1 --n-trials 35` explicit. Type justification provided
  (single structural axis, single-seed budget, no baseline update). Cadence position (cycle-6 block
  iter-v3/110–119, iter-v3/120 as mandatory separate CONFIRMATION) correctly stated and consistent with
  `feedback_v3_strict_10_to_1_cadence.md`.

- Section 1 (Hypothesis): PASS — ONE sentence: wholesale universe replacement
  (BCH/LDO/TRX → CRV/AAVE/GRT/ADA) selected by a per-symbol walk-forward-faithful feature→label
  predictive-signal screen produces an IS-positive, less-concentrated v3 book, because the /109
  permutation null is specific to the BCH/LDO/TRX joint distribution and does not transfer to a
  universe the screen shows carries measurably stronger signal. Specific mechanism stated; directly
  addresses the /109 terminal finding; not vague.

- Section 2 (IS-Only Numerical Evidence): PASS — committed analysis scripts at
  `analysis/iteration_v3-110/` (commit `cfeaf34`): `_shared.py`, `symbol_signal_screen.py`,
  `universe_construction.py`, `t6_recompute.py`, `gated_book_2to1.py`, `universe_finalize.py`.
  Result tables T1–T10 verified present in the analysis directory. Numerical tables provided:
  - T1/T10: per-symbol signal screen with mean fold AUC, permutation p-values, and SIGNAL_GO flags —
    incumbent universe reproduces /109 null (BCH p=0.72, LDO p=0.48, TRX p=0.75); proposed universe
    all-positive margin-over-q50.
  - T7: per-symbol 2:1-barrier gated books — all four proposed symbols individually POSITIVE (ADA +921,
    CRV +753, AAVE +387, GRT +136, PF>1.0); all three incumbents at PF<1.0 except LDO.
  - T9: aggregate bakeoff — U_B IS gated monthly Sharpe proxy +0.2527 vs incumbent −0.2659.
  - T8: leave-one-out robustness — worst LOO variant (minus CRV) still +641 PnL.
  - T5: pairwise PnL-proxy correlation — U_B mean ≈ 0.21, effective breadth ≈ 2.7.
  GALA exclusion justified with quantitative evidence (T7: GALA gated book −803, PF 0.93 despite
  highest hit rate). Signal thinness honestly disclosed (§2.7). IS-only invariant asserted at
  loader level. Category-matching absent — all evidence is numerical from committed scripts.

- Section 3 (Proposed Changes): PASS — enumerated as ONE axis:
  3.1 Universe: V3_MODELS 3-tuple → 4-tuple (BCH/LDO/TRX → CRV/AAVE/GRT/ADA). Table provided.
    V3_EXCLUDED_SYMBOLS disjointness confirmed (CRVUSDT/AAVEUSDT/GRTUSDT/ADAUSDT not in the
    11-entry excluded list — verified against `src/crypto_trade/features_v3/__init__.py` line 482).
  3.2 Labeling: UNCHANGED declared.
  3.3 Features: UNCHANGED declared (14-feature V3_FEATURE_COLUMNS_TOP_N; per-symbol dicts empty).
  3.4 Risk gates: UNCHANGED declared (7-primitive RiskV2 stack, all /059-canonical knobs).
  3.5 Required src/ changes: concrete and implementable — 8 numbered items:
    (1) V3_MODELS 3→4-tuple in runner lines 190–194. PASS.
    (2) REQUIRED_GAP 66→88 in validation_v3.py line 76: formula (21+1)*4=88 is correct for 4 symbols.
        Current value confirmed at line 76: `REQUIRED_GAP: int = (21 + 1) * 3  # 66`. PASS.
    (3) _canonical_v059 guard: update expected symbols tuple and REQUIRED_GAP from 66→88. The guard
        is confirmed at runner lines 1029–1059, currently hard-asserting BCHUSDT/LDOUSDT/TRXUSDT
        and REQUIRED_GAP==66. PASS — update targets are concrete and correct.
    (4) Per-flight model-build hardcoded symbol checks: lines ~778, ~927, ~951, ~982, ~1021, ~1069
        reference BCHUSDT/LDOUSDT/TRXUSDT. Update to CRVUSDT (any new-universe symbol). PASS.
    (5) ITERATION_LABEL: "v3-105" → "v3-110". Confirmed at runner line 131. PASS.
    (6) Feature-column assertions auto-iterate V3_MODELS — no edit needed beyond V3_MODELS update.
        Feature parquets for all 4 new symbols confirmed present in data/features_v3/. PASS.
    (7) Data freshness pre-flight: explicit instruction to verify 8h CSVs within 16h. PASS.
    (8) CPCV n_paths unchanged (45 paths, n_splits=10, n_test=2). PASS.

- Section 4 (Expected OOS Impact): PASS — predicted IS Sharpe +0.4 to +1.0 (central +0.7), OOS Sharpe
  +0.3 to +0.9 (central +0.55). Explicit falsifier stated: IS monthly Sharpe < +0.30 OR OOS monthly
  Sharpe < −0.10 → hypothesis rejected, symbol-selection-by-feature-AUC-screen axis closed for cycle 6.
  Confidence interval provided. Reasoning grounded in EDA raw gated book numbers (U_B +0.25 vs
  incumbent −0.27 monthly proxy). Honest caveat about barrier-geometry carry acknowledged (§4 and
  /059 reconciliation context). OOS/IS ratio prediction implicit (see Section 8 criteria).

- Section 5 (Risk Mitigation): PASS — structural universe axis itself directly attacks worst
  structural flaw (BCH 95.76% IS PnL concentration). 7-gate RiskV2 stack carried unchanged.
  Per-symbol OOD z-score gate adapts at training time to new symbol feature distributions.
  Per-symbol drawdown brake correctly kept DISABLED per /054 STATEFUL-gate finding. Simulated
  historical effect on IS gated book provided (T7/T9): −1294 PnL/0.93 PF → +2197/1.05.
  LOO robustness (T8) confirms no single-symbol-carries-the-book structure. IS-calibrated
  thresholds unchanged (all /059-canonical per Section 3.4).

- Section 6 (Risk Management Design): PASS — 7-primitive table provided with fire-rate predictions
  for the new universe CRV/AAVE/GRT/ADA. Each gate status (Active/Disabled) stated. Hit-rate gate
  correctly declared Disabled per iter-v2/045 lesson. Per-symbol OOD gate adaptation mechanism
  explained (per-symbol covariance fitted at training time). Sector diversification of proposed
  universe noted (DeFi/indexing/L1). No new risk primitive introduced — stated and justified
  (adding a primitive simultaneously would violate one-variable-at-a-time discipline). Fire-rate
  ranges are estimates by gate class — appropriate for EXPLORATION-type brief.

- Section 7 (Pre-Registered Failure-Mode Prediction): PASS — four failure modes pre-registered:
  (1) IS feature→label AUC screen does not survive IS→OOS regime shift; expected signature
      (IS Sharpe lifts, OOS decays toward zero, OOS/IS below 0.5 floor; elevated PBO; per-symbol
      OOS attribution shows 3 of 4 negative). Gates that should catch it identified.
  (2) Universe helps concentration but not edge — PROMISING-MECHANICAL-class outcome.
  (3) ADA specifically underperforms — dead-path risk with fallback (U_A = CRV+AAVE+GRT) scoped.
  (4) AAVE specifically underperforms — explicitly added as at-least-equally-likely weak link
      given weakest IS evidence (win rate 0.3632, p=0.164). Same fallback mechanism. Each mode
      produces distinct metric signatures for Phase 7/8 discrimination.

- Section 8 (Pre-Registered MERGE/NO-MERGE Criteria): PASS — locked thresholds (EXPLORATION
  verdict classification, not a MERGE decision — correctly stated as non-merging iteration):
  EXPLORATION-PROMISING: IS ≥ +0.60 AND OOS ≥ +0.30 AND OOS/IS ≥ 0.40 AND top-symbol OOS ≤ 70%
    AND aggregate OOS trades ≥ 130.
  EXPLORATION-PROMISING-MECHANICAL: concentration win (top-symbol ≤ 70%) with IS/OOS within ±0.20
    of /059 but not clearing PROMISING bars.
  EXPLORATION-NEGATIVE: IS < +0.30 OR OOS < −0.10 OR OOS/IS < 0.40 with OOS < +0.30.
  Critic scope for EXPLORATION checks stated (Checks 1,2,4,5,6,8; Check 3 DSR/PSR informational
  per `feedback_v3_dsr_mode_artifact.md`). Thresholds are pre-registered before backtest.

- Section 9 (Library Stack): PASS — no new library. EDA stack pinned: lightgbm==4.6.0,
  scikit-learn==1.8.0, scipy==1.17.0, numpy==2.2.6, pandas==3.0.0, pyarrow==23.0.1. Phase 6
  runner stack: optuna==4.8.0, statsmodels==0.14.6, in-repo validation_v3. No mlfinlab/fracdiff/
  pypbo version change. pyproject.toml UNCHANGED. No fallback needed.

- Section 10 (QR Audit Trail): PASS — axis selection documented per
  `feedback_v3_axis_selection_quant_discipline.md`. Three-point rationale: (1) /109 permutation
  null is universe-specific — screen reproduces it on incumbents (§2.1); (2) wholesale replacement
  selected by a feature→label signal screen is a genuinely distinct axis never previously run;
  (3) U_B over top-5 justified by T8 LOO (GALA dropped on decisive evidence, §2.4). ADA dead-path
  disclosure with specific new quantitative evidence (5-seed-averaged WF-faithful IS-only screen,
  ADA positive individual book +921). AAVE dead-path disclosure with honest caveat (weakest IS
  evidence of the four, pre-registered as equally-likely weak link). Escalation note on excluded
  liquid majors (not needed — positive universe found within v3-eligible set). No orchestrator
  pick superseded. Audit-trail section complete.

## Cadence Check

- Cycle-6 opening: PASS — iter-v3/110 is correctly the first EXPLORATION of cycle 6.
  Cycle-5 terminal iteration (iter-v3/109) closed as NULL-AT-EDA with user structural decision
  required; autopilot paused; cycle-6 opens with user-directed symbol-selection axis.
- 10:1 enforcement: PASS — iter-v3/120 declared as mandatory separate CONFIRMATION; the 10th
  EXPLORATION cannot be collapsed into the CONFIRMATION per `feedback_v3_strict_10_to_1_cadence.md`.
- EXPLORATION spec: PASS — single-seed, 2h hard cap, `--exploration --seeds 1 --n-trials 35`.

## Technical Verification

- V3_EXCLUDED_SYMBOLS disjointness: CRVUSDT, AAVEUSDT, GRTUSDT, ADAUSDT absent from
  `V3_EXCLUDED_SYMBOLS` (11 entries: BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT, BNBUSDT,
  SOLUSDT, XRPUSDT, DOGEUSDT, NEARUSDT, MKRUSDT). PASS.
- Feature parquets exist for all 4 new symbols in `data/features_v3/`:
  CRVUSDT_8h_features.parquet, AAVEUSDT_8h_features.parquet, GRTUSDT_8h_features.parquet,
  ADAUSDT_8h_features.parquet. PASS.
- REQUIRED_GAP formula: (21+1)*4=88 is correct for 4-symbol universe. Current value in
  validation_v3.py line 76 is 66 = (21+1)*3 — will need update per Section 3.5 item 2. PASS.
- _canonical_v059 guard confirmed at runner lines 1029–1059 — hard-asserts BCHUSDT/LDOUSDT/TRXUSDT
  and REQUIRED_GAP==66; Section 3.5 item 3 instructs correct update. PASS.
- ITERATION_LABEL at runner line 131 is "v3-105" — Section 3.5 item 5 instructs update to
  "v3-110". PASS.
- EDA script commit `cfeaf34` confirmed in git log. All 6 EDA scripts + 10 result CSVs present
  in `analysis/iteration_v3-110/`. PASS.
- One-variable-at-a-time: only V3_MODELS changes; features/labeling/model/risk-gates all
  /059-identical per Sections 3.2–3.4. PASS.
- Sacred constants: OOS_CUTOFF_DATE = 2025-03-24 unchanged; training_months = 24 unchanged;
  5-seed inner ensemble (ENSEMBLE_SEEDS) unchanged (unified 10-seed architecture per BASELINE_V3.md
  Phase B-3 is carried unchanged). PASS.

## Status

OVERALL: PASS — Phase 6 implementation authorized.
