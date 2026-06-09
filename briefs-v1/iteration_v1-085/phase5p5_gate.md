# Phase 5.5 Gate — iter-v1/085

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: SPECIALIST — UNIUSDT single-coin cohort; NEW feature-engineering set (4 features);
      fresh-alt mine under the REFINED structure-gated selector.

## (v1) Axis Family + Rotation Status
FAMILY: per-cohort-specialization-UNI (under cycle-7 per-symbol regime-specialist mandate;
        standard 5-family axis-rotation discipline SUSPENDED per
        feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md; rotation check is
        symbol-cohort orthogonality vs live BUNDLE-002 universe)
ROTATION_STATUS: VALID — UNIUSDT not in {DOT, ETH, BTC, AAVE} (live BUNDLE-002 cohorts)
                         AND not in V1_EXCLUDED_SYMBOLS {XRPUSDT, DOGEUSDT, NEARUSDT,
                         BCHUSDT, LDOUSDT, TRXUSDT, BNBUSDT} AND not in prior NEGATIVE
                         mining set {LINK, LTC, ATOM, ICP, FIL, CRV}.
                 Pairwise-disjoint vs BUNDLE-002: CONFIRMED at runtime
                 (UNIUSDT intersect {DOT,ETH,BTC,AAVE} = empty set).

## (v1) HIGH-RISK Declaration
HIGH-RISK: YES — dual trigger: (1) NEW SYMBOL universe-substitution (UNIUSDT never a
           training objective in v1); (2) NEW 4-feature set changes feature-importance
           allocation surface at once.
MITIGATION: single-outer-seed=42 SPECIALIST with 50-inner-seed averaging (variance control).
            Multi-seed CONFIRMATION PERMANENTLY DROPPED per user directive 2026-06-09.
            Escalation clause pre-registered in brief Section 2.5: NEGATIVE verdict triggers
            "burden of proof has shifted to architecture" diary finding, NOT a multi-seed re-run.

## (v1) LM Master Response Verification
- briefs-v1/iteration_v1-085/lgbm_advisor.md exists: PASS
  (commit 82f02eb6; confidence LOW-to-MEDIUM lean LOW; predicted IS Sharpe +0.35
  range +0.10/+0.65; adversarial honest probe-FAIL reconciliation)
- Brief Section 3.5 addresses each LM Master recommendation: PASS
  - Rec 1 (KEEP HP lock — 50 seeds x 30 trials x depth-5 x leaves-31): ADOPTED
    (Section 3.4 holds the lock exactly)
  - Rec 2 (min_data_in_leaf 80-100 floor): MODIFIED/DEFERRED — deferred to /086 as
    first lever; rationale: HP change confounds pure 4-feature verdict; single-bit
    discipline; /086 lever pre-registered
  - Rec 3 (confirm lambda_l1 > 0 reachable): ADOPTED (verify-only) — standard v1
    Optuna space, no src change
  - Post-mortem / n_estimators pinning: ADOPTED as 7.4 telemetry
  - Per-feature rank predictions (F2-PRIMARY rev_extension_z_3 rank >= 14 in > 50%
    months; F2-SUSPICION capstone rank 1 while primitive >= 8; F2-COLLECTIVE < 30 gain):
    ADOPTED + HARDWIRED into Section 4 falsifiers
  - Risk A (probe sub-gate at -0.243): ADOPTED + HARDWIRED as F3
  - Risk B (IS/OOS ratio < 0.4 = overfit-drift tell): ADOPTED as 7.4 telemetry
  - Risk C (>= 50 OOS trade floor; pre-register expected count): ADOPTED + PRE-REGISTERED
    in Section 4.1 (modal 90-140 OOS, 180-280 IS)
  - Optional 52-col pre-flight probe (cheapest de-risk): ADOPTED as optional Phase 6
    pre-flight; QE may abort early if 52-col probe < -0.10
  - No multi-seed CONFIRMATION recommended or entertained: CONFIRMED

## Cadence Check (v1 SPECIALIST)
- Wall-clock budget declared: ~5.5-8h (user-mandated SPECIALIST budget: 50 inner seeds x
  30 trials x 24 months; exceeds default 2h EXPLORATION cap by explicit user directive;
  no kill-switch; overrun documented not killed): PASS
- Split-engineer dispatch applies: feedback_split_engineer_dispatch.md binds (>30 min
  backtest): PASS — QE does setup-only, orchestrator launches detached

## Sacred Constants Verification
- OOS_CUTOFF_DATE = 2025-03-24: PASS
  (run_iteration_085.py line 53; config.py OOS_CUTOFF_MS=1742774400000)
- training_months = 24: PASS (run_iteration_085.py confirmed)
- 50 inner seeds (42..91): PASS
  (V1_SPECIALIST_SEEDS = tuple(range(42,92)), asserted len==50 at runtime)
- max_depth = 5, num_leaves = 31: PASS (FIXED; removed from Optuna search)
- Global V1_FEATURE_COLUMNS_PRUNED == 48: PASS
  (runtime: len=48; assert at __init__.py:213-214; uv run python verified 2026-06-09)
- V1_ITER085_FEATURE_COLUMNS == 52: PASS
  (runtime: len=52; assert at __init__.py:242-244; uv run python verified 2026-06-09)
- New LOCAL cols (4): rev_extension_z_3, rev_halflife_50, rev_vol_gate_signed,
  vol_state_z_natr_30 (all present; alphabetically ordered; none modify global PRUNED)
- Features-base-hash (52-col prefix): c8b8e0a87abb280a — PASS
  (run_iteration_085.py --check-hash verified match with pre-registered FEATURES_BASE_HASH_52COL)

## Track Isolation
- mean_reversion_v1.py: ZERO imports from features_v2/features_v3 — PASS
- volatility_v1.py: ZERO imports from features_v2/features_v3 — PASS
- composed_v1.py: ZERO imports from features_v2/features_v3 — PASS

## IS-Only Evidence (Section 2) — Reproducibility Verification
Section 2 BLOCK from the prior gate (commit da8c17e8) is RESOLVED. Commit b67fdefa
(2026-06-09 22:04) force-adds all 19 EDA scripts + result CSVs to git history:
  - analysis/iteration_v1-085/uni_prescreen.py + uni_prescreen_results.csv
  - analysis/iteration_v1-085/probe_UNIUSDT.py + probe_UNIUSDT_results.csv
  - analysis/iteration_v1-085/structure_prescreen_{algo,etc,grt,matic,op,xlm}.py
  - analysis/iteration_v1-085/structure_prescreen_{algo,grt,matic,xlm}.csv
  - analysis/iteration_v1-085/structure_prescreen_op_{ic,results}.csv
  - analysis/iteration_v1-085/etc_feature_label_ic.csv
  - analysis/iteration_v1-085/feature_ic_algo.csv
  - analysis/iteration_v1-085/structure_prescreen_summary.csv
  - analysis/iteration_v1-085/probe_GRTUSDT.py + probe_GRTUSDT_result.json
Key gate numbers verified against committed CSVs:
  - trivial_baseline_min = -0.2485 (GATE 1 PASS): CONFIRMED from uni_prescreen_results.csv
  - autocorr_mag = 0.0843 (ac_lag3 = -0.0843): CONFIRMED from uni_prescreen_results.csv
  - max_feature_label_ic = 0.0393 (GATE 2 SECONDARY FAIL by 0.0007): CONFIRMED
  - probe_is_monthly_sharpe = -0.243 (GATE 2 PRIMARY FAIL): CONFIRMED from probe_UNIUSDT_results.csv
  - gate1_pass=True, gate2_pass=False, structure_signal=WEAK: CONFIRMED
All scripts enforce open_time < OOS_CUTOFF_MS with runtime leak assertion.
Reproducibility: PASS (all scripts and CSVs now in git at b67fdefa)

## Tests
- tests/test_iteration_v1_085.py: 37/37 PASS (uv run pytest confirmed 2026-06-09)
- tests/features_v1/ + tests/test_config.py: 69 additional PASS
  Total targeted run: 106/106 PASS

## Parquet Status (QE pre-flight)
- UNIUSDT 8h.csv freshness: 4.2h old (last close_time 2026-06-09 15:59:59 UTC — FRESH)
  Re-fetched via: uv run crypto-trade fetch --symbols UNIUSDT --intervals 8h
- UNIUSDT v1 parquet: REGENERATED with 52-col iter-085 stack
  Command: uv run crypto-trade features --symbols UNIUSDT --interval 8h --track v1 --format parquet
  All 52 V1_ITER085_FEATURE_COLUMNS present in data/features/UNIUSDT_8h_features.parquet
  (235 total cols; 0 missing): PASS

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 explicitly
  stated; IS window named (4.51y to OOS cutoff); OOS window named (2025-03-24 to present);
  sacred constants held per feedback_training_window.md + feedback_no_cheating.md.
- Section 0.5 (Iteration Type): PASS — TYPE: SPECIALIST declared; wall-clock budget stated;
  NO multi-seed CONFIRMATION stated (user directive HARD); cycle-7 mandate context provided.
- Section 0.6 (Architecture-Family Justification): PASS — per-cohort-specialization-UNI
  declared; mandate suspension rationale; prior 5 SPECIALIST cohorts listed
  (/064 ETH /065 BTC /078 AAVE /083 FIL /084 CRV); ROTATION_STATUS=VALID with
  cohort-orthogonality reasoning; pairwise-disjoint vs BUNDLE-002 explicitly stated.
- Section 1 (Hypothesis): PASS — one-sentence specific hypothesis naming exact features
  (rev_extension_z_3, vol_state_z_natr_30, rev_halflife_50, rev_vol_gate_signed), exact
  mechanism (lag-3 reversion + vol-state coordinates PRUNED stack is blind to), and
  explicit falsification frame. Vagueness bar cleared. GATE-2-WEAK caveat stated upfront.
- Section 2 (IS-Only Evidence): PASS — ALL load-bearing scripts + result CSVs committed
  at b67fdefa (resolves prior BLOCK). Key gate numbers verified against committed CSVs.
  Scripts enforce IS-only constraint with runtime leak assertion. Reproducibility verified.
  Committed scripts: analysis/iteration_v1-085/uni_prescreen.py,
                     analysis/iteration_v1-085/probe_UNIUSDT.py,
                     analysis/iteration_v1-085/structure_prescreen_*.py (6 scripts)
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — HIGH-RISK declared; dual triggers
  stated; mitigation stated (50-inner-seed, no multi-seed CONFIRMATION per directive);
  attribution-entanglement acknowledged; escalation clause pre-registered.
- Section 3 (Proposed Changes): PASS — enumerated: symbol (UNIUSDT added), 4 NEW LOCAL
  features (specs, warmup, clip, orthogonal-decomposition table), no new risk primitive.
  LM Master responses in Section 3.5 (every recommendation addressed). Global PRUNED stays
  48 (LOCAL-only architecture maintained; /084 discipline applied).
- Section 4 (Expected OOS Impact): PASS — predicted IS Sharpe modal +0.35 range
  [+0.10,+0.65]; OOS modal +0.05 range [-0.50,+0.55]; explicit falsifiers F1/F2/F3/F4/FB1
  with numerical thresholds; pre-registered trade counts (modal 90-140 OOS, 180-280 IS);
  explicit hypothesis-rejection threshold; behavioral-effect predictor (>= 20% IS trade
  change if features bind; < 10% = F2 INERT).
- Section 5 (Risk Mitigation): PASS — R1/R2/R3/R5 stack with IS-calibrated thresholds
  and simulated effects present across Section 3.3, Section 6, and the Risk Mitigation
  appendix. Content satisfies gate requirement; numbering convention is cosmetic and
  non-blocking.
- Section 6 (Risk Management Design): PASS — full primitive table (R1 DISABLED / R2
  DISABLED / R3 OOD cutoff=0.70 16-features / R5 vol-target vt_target_vol=0.3 /
  rev_vol_gate_signed as feature-level soft gate); fire-rate predictions IS+OOS;
  regime coverage rationale; simulated historical effect per /063/064/065/078 roster.
- Section 7 (Failure-Mode Prediction): PASS — 3 failure modes pre-registered with
  probability ordering: (1) NEGATIVE-PROBE-FLAT (modal, pre-registered before backtest);
  (2) NEGATIVE-INERT-FEATURE; (3) SUSPICIOUS-STRUCTURE-ABSENCE. Per-mode gate
  identification provided. Forward-looking, not post-hoc.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — pre-registered SPECIALIST candidacy bands
  (PROMISING-STRONG >= +0.40 / PROMISING-TENTATIVE [+0.10,+0.40) / NEGATIVE < +0.10)
  with explicit conditions; HARD gate table (IS/OOS trades >= 50, collective importance
  >= 30, probe lift > +0.25, ML IS Sharpe > +0.00); future-bundle gates inherited at
  assembly. NO multi-seed CONFIRMATION gate (user directive HARD).
- Section 9 (Library Stack): PASS — 7-library version table (Python 3.13, lightgbm 4.6.0,
  optuna 4.8.0, numpy 2.2.x, pandas 3.0.x, scikit-learn 1.8.x, scipy 1.17.x); no new
  third-party dependencies; DSR/PBO/PSR not computed at SPECIALIST EXPLORATION layer;
  track isolation stated.

## Branch Note (resolved)
Branch is iteration-v1/085 per git branch --show-current. The prior gate noted a
branch-naming issue; this is now resolved — the branch is correctly named.

## Runner Pre-flight (QE verification)
- run_iteration_085.py --check-hash: PASS (hash c8b8e0a87abb280a matches pre-registered)
- Pre-flight assertions: PASS (PRUNED=48, ITER085=52, seeds 42..91 len=50)
- sys.argv injection: correct (--exploration --iteration 85 --n-trials 30 --ensemble-size 1
  --symbols UNIUSDT --pruned-features --seeds 1)
- Dispatch branch at run_baseline_v1.py:7818 (iteration_label == "v1-085" and
  set(symbols) == set(V1_ITER085_UNIVERSE)): PRESENT
