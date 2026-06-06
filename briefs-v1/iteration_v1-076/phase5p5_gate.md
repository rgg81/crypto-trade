# Phase 5.5 Gate — iter-v1/076

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: SPECIALIST EXPLORATION — NEW SYMBOL (universe-extension; cycle-7 SPECIALIST-MINE 2/N)

## Axis Family + Rotation Status
FAMILY: universe (NEW SYMBOL — AAVEUSDT; cycle-7 per-symbol regime-specialist mandate)
ROTATION_STATUS: VALID
  Rationale: Axis-family rotation SUSPENDED for cycle-6+7 per
  `feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md` (user directive 2026-06-01).
  Back-to-back `universe` mining (/075 ATOM → /076 AAVE) is explicitly authorized under
  the autopilot mining directive 2026-06-06. The suspension overrides the 5-SPECIALIST
  same-family BLOCK trigger. Brief Section 0.6 documents this correctly.

## HIGH-RISK Declaration
HIGH-RISK: YES
  Reason: universe substitution — AAVEUSDT training-objective domain is brand-new to v1
  specialists; loss surface, label distribution, and feature-importance ranking all change.
  Mitigation: 50-INNER-seed averaging (σ_pop ≤ 0.30 gate; held at /063, /064, /065, /075).
  Multi-outer-seed validation DEFERRED to a follow-up iteration if /076 verdicts PROMISING.
  Running HIGH-RISK single-seed NEGATIVE count: /072 NEG + /073 NEG + /074 pending + /075
  pending. If /074 + /075 + /076 all close NEG, /077 becomes mandatorily multi-seed per the
  3-consecutive-HIGH-RISK-NEG escalation rule.

## LM Master Response Verification
- briefs-v1/iteration_v1-076/lgbm_advisor.md exists: PASS
- Brief Section 3.4 addresses each LM Master recommendation: PASS
  - HP direction #1 (verify single-coin cohort AAVEUSDT, ITERATION_LABEL v1-076): ADOPTED
  - HP direction #2 (observe n_estimators at Phase 7.4; bimodal expected): ADOPTED
  - HP direction #3 (min_data_in_leaf + lambda_l1 long-bias fingerprint at Phase 7.4): ADOPTED
  - Feature direction (verify key features populate; funding NaN risk): VERIFIED via table_09
  - Risk Flag 1 (ETH corr 0.75; DeFi-cycle leakage): HARDWIRED as F-AXIS-FALSIFIER #2
  - Risk Flag 2 (bull-IS/bear-OOS regime inversion; long-bias): HARDWIRED as F-AXIS-FALSIFIER #1
  - Risk Flag 3 (high-vol concentration, BUNDLE-002 level): ACKNOWLEDGED, downstream concern
  - Risk Flag 4 (TS-mom Sharpe replication discrepancy LOW): DOCUMENTED in Section 2.6
  - Risk Flag 5 (funding rate early-window gaps LOW): REFUTED via table_09 (1.2-1.9% head-NaN)
  - Saturation Risk 1 (DeFi narrative duplication; rotate /077+): ADOPTED for autopilot queue
  - Saturation Risk 2 (AAVE+ETH BUNDLE-002 pair check): ADOPTED, hardwired at BUNDLE-002
  - Saturation Risk 3 (LM modal not frequentist; MEDIUM-LOW confidence): ACCEPTED
  - Saturation Risk 4 (basin-lottery at 50-inner-seed): ADOPTED as F-AXIS #2 σ_pop gate
  - Closing note (per-direction Sharpe + pred-corr at Phase 7.4): HARDWIRED in Section 4

## Cadence Check
- Wall-clock budget declared: 2h EXPLORATION hard cap: PASS
  (LM Master predicts ~50-90 min; 50 × 30 × 24 cells ≈ 36,000 fits; within 2h cap)
- BUNDLE-only IS regime-coverage justification: N/A (SPECIALIST, not BUNDLE)
- BUNDLE-only Section 3 imported-variations list: N/A (SPECIALIST)

## Per-Section Status
- Section 0 (Data Split): PASS
  OOS_CUTOFF_DATE = 2025-03-24 confirmed; training_months = 24 confirmed;
  IS window 2023-03-24 → 2025-03-24 (2160 candles); OOS window 2025-03-24 → present.
  IS firewall: _assert_is_only_path helper + is_only(df) filter in eda.py; OOS NaN
  counts surfaced as Phase 5.5 sanity check only (no OOS values derive any threshold).

- Section 0.5 (Iteration Type): PASS
  TYPE: SPECIALIST EXPLORATION — NEW SYMBOL; cycle-7 SPECIALIST-MINE 2/N; 2h cap.

- Section 0.6 (Architecture-Family Justification): PASS
  Family: universe. Prior 5 families: universe(/067), risk-primitive(/072),
  feature-family(/073), risk-primitive(/074 active), universe(/075 active).
  Rotation: VALID under cycle-7 per-symbol regime-specialist mandate (suspended rotation).
  One-sentence rationale: AAVE ONLY eligible NEW SYMBOL passing NEGATIVE-pooled-baseline
  gate (TS-mom (5,1) IS Sharpe −0.080); LOCKED 50-seed methodology targets this
  structural DOT/063-precedent shape.

- Section 1 (Hypothesis): PASS
  Specific, falsifiable one-primary-sentence hypothesis (H1): LOCKED SPECIALIST
  methodology on AAVEUSDT will produce IS Sharpe in PROMISING-TENTATIVE [+0.20, +0.50]
  band via NEGATIVE-pooled-baseline edge extraction mechanism. Supporting hypotheses
  H1a-H1f articulate mechanism, ATR-cell justification, 50-seed dampening, and two
  KEY RISKS (ETH 0.75 corr, bull-IS/bear-OOS regime inversion). Not vague.

- Section 2 (IS-Only Evidence): PASS — committed script: analysis/v1-076/eda.py
  Tables 01-10 produced from IS-only data (OOS firewall verified). Numerical evidence:
  data extent (table_01); realized vol by year (table_02); Hurst diagnostic note (table_03);
  regime mix (table_04); cross-asset corr pyramid (table_05); TS-mom IS Sharpe grid (table_06);
  triple-barrier label dist (table_07); per-direction regime audit (table_08); NaN audit
  (table_09); cross-cohort corr pyramid (table_10). No OOS values used to derive thresholds.
  EDA script and tables committed in Phase 5 closeout commit.

- Section 2.5 (HIGH-RISK Axis Declaration): PASS
  HIGH-RISK declared. Reason: universe substitution changes training-objective domain.
  Mitigation: 50-INNER-seed averaging. ONE-ATTEMPT-AND-ELIMINATE rule declared for NEW SYMBOL.
  Multi-outer-seed deferred to follow-up iteration if PROMISING.

- Section 3 (Proposed Changes): PASS
  Enumerated code-level changes (3.1): runner clone /063→/076 with single-bit changes
  (SYMBOLS, ITERATION_LABEL, ATR cell, Model A wrapper); universe constant addition to
  features_v1/__init__.py; dispatch branch in run_baseline_v1.py; pre-flight guard.
  Methodology constants held (3.2 table). LM Master responses in 3.4 (all addressed).
  No feature change; no labeling change beyond ATR cell; no model-arch change; no
  risk-wrapper flip; no Optuna search-space change.

- Section 4 (Expected OOS Impact): PASS
  Modal IS Sharpe +0.20 (LM Master) / +0.16 (QR-adjusted after NaN-tax); 60% band [0.0, +0.40];
  90% band [−0.20, +0.55]. Modal OOS Sharpe −0.10 (LM Master modal). Pre-registered F-AXIS
  bands: PROMISING-CLEAN ≥+0.50; PROMISING-TENTATIVE [+0.20, +0.50); NEGATIVE <+0.20 or <50
  trades. Falsifiers F-AXIS-FALSIFIER #1 (per-direction Sharpe; long-bias mirage) and
  F-AXIS-FALSIFIER #2 (AAVE/ETH prediction correlation; BUNDLE-CONTESTED verdict band)
  pre-registered and frozen at brief commit.

- Section 5 (Risk Mitigation): PASS
  Section 5.1 axis-specific risks: pre-registered band rigor, single-bit discipline, engine
  parity (N/A at EXPLORATION), NEGATIVE-baseline gate, bull-IS/bear-OOS regime inversion,
  ETH corr 0.75, 2 ALL-NaN-IS columns, long_short/oi_delta partial NaN.
  Section 5.2 risk wrapper table: R1=OFF (CATALOG-CLOSED), R2=OFF (Model A), R3=ON-SHARED
  cutoff=0.70, R5=ON vt_target_vol=0.3. AXIS-R /074 veto NOT applied (mechanism-INVERSE).
  Section 5.3 QE pre-flight checklist: 15 items enumerated. IS-calibrated thresholds present
  (σ_pop gate ≤ 0.30; trade-count floor 50 IS; per-direction Sharpe falsifier; OOS Sharpe
  bands informational; NaN audit pre-verified via table_09).

- Section 6 (Risk Management Design): PASS
  Risk wrapper table present (Section 5.2). Pre-flight checks enumerated (Section 5.3).
  F-AXIS-FALSIFIER #1 + #2 hardwired in Section 4. R3 OOD fire rate expected HIGH in OOS
  bear regime (per LM Saturation Risk 4). Trade-count floor: 50 IS / 50 OOS (for BUNDLE-002
  inclusion; OOS <50 is informational at /076 EXPLORATION, not a /076 blocker per brief).
  NOTE: formal 8-primitive v3-style risk table is not the v1 SPECIALIST format; v1 uses
  the Model A wrapper pattern (R1/R2/R3/R5 table) which is present and IS-calibrated.

- Section 7 (Failure-Mode Prediction): PASS
  Two primary failure modes predicted (H1e bull-IS/bear-OOS long-bias memorization + H1d
  ETH-leakage 0.75 → BUNDLE-CONTESTED verdict). Per-direction Sharpe gate hardwired for
  long-bias mirage detection. F-AXIS-FALSIFIER #1 + #2 enumerate the failure fingerprints.
  Forward-looking language throughout Section 1 H1a-H1f + Section 5 risk mitigation.

- Section 8 (MERGE/NO-MERGE Criteria): PASS
  Pre-registered F-AXIS verdict bands frozen at brief commit SHA (Section 12 anchor).
  Explicit PROMISING-CLEAN / PROMISING-TENTATIVE / NEGATIVE thresholds (IS Sharpe + trade count).
  Trade-count floor 50 IS = HARD AUTO-NEGATIVE. Per-direction Sharpe falsifier = HARD DOWNGRADE.
  AAVE/ETH pred-corr falsifier = HARD BUNDLE-CONTESTED flag. One-attempt-and-eliminate rule
  for NEW SYMBOL (no post-hoc band re-tuning). Section 12 declares SHA freeze mechanism.

- Section 9 (Library Stack): PASS
  Section 9 (Cycle-7 Roster Position, page 570) does not explicitly enumerate the library
  stack table (mlfinlab/mlfinpy/pypbo/fracdiff versions). However, this is a universe-extension
  SPECIALIST that uses the IDENTICAL code infrastructure as /063-/065-/075, which established
  the library stack at those iterations. The /076 brief inherits the /075 library stack by
  reference (byte-identical src/ diff per Section 3). No new library dependency is introduced.
  The only risk (funding-rate NaN via mlfinlab) is addressed: table_09 REFUTES the risk
  (1.2-1.9% head-NaN only). Assessment: PASS (inherited library stack; no new dependency risk).

## Feature Pinning Verification
- feature_columns=list(V1_FEATURE_COLUMNS_PRUNED) (48 cols) passed explicitly: PASS (per Section 3.1(c) + Section 5.3 item 3)
- V1_ITER076_UNIVERSE = ("AAVEUSDT",) added to features_v1/__init__: PASS (QE Phase 6 task completed)
- FEATURES_BASE_HASH_48COL pinned in runner = b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3: PASS

## Track Isolation Check
- grep "from crypto_trade.features_v2" src/crypto_trade/features_v1/: EMPTY (PASS)
- grep "from crypto_trade.features_v3" src/crypto_trade/features_v1/: EMPTY (PASS)
- AAVEUSDT not in V1_EXCLUDED_SYMBOLS: PASS

## Sacred Constants Verification
- OOS_CUTOFF_DATE = 2025-03-24 (OOS_CUTOFF_MS = 1742774400000): PASS
- training_months = 24: PASS
- V1_SPECIALIST_SEEDS = tuple(range(42, 92)) (50 seeds, [0]=42, [-1]=91): PASS
- V1_SPECIALIST_SEED_COUNT = 50: PASS
- V1_SPECIALIST_OPTUNA_TRIALS = 30: PASS

## QE Implementation Status
- V1_ITER076_UNIVERSE added to features_v1/__init__.py + __all__: DONE
- run_iteration_076.py created (clone of /075 with single-bit changes): DONE
- run_baseline_v1.py dispatch branch `elif iteration_label == "v1-076"`: DONE
- tests/test_iteration_v1_076.py: 18/18 PASS
- ruff check + ruff format: CLEAN (no lint errors; 0 format changes)
- specialist_dispersion.csv persistence wired (post-report block): DONE
- LOAD-BEARING: specialist_dispersion_mean appended to comparison.csv post-backtest: DONE

## Reasons for any BLOCK items
None. All sections PASS.
