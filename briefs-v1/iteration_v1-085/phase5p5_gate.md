# Phase 5.5 Gate — iter-v1/085

OVERALL: BLOCK

## Iteration Type (from Brief Section 0.5)
TYPE: SPECIALIST — UNIUSDT single-coin cohort; NEW feature-engineering set (4 features);
      fresh-alt mine under the REFINED structure-gated selector.

## (v1) Axis Family + Rotation Status
FAMILY: per-cohort-specialization-UNI (under cycle-7 per-symbol regime-specialist mandate;
        standard 5-family rotation SUSPENDED per feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md)
ROTATION_STATUS: VALID — UNIUSDT ∉ {DOT, ETH, BTC, AAVE} (live BUNDLE-002 cohorts) AND
                         ∉ V1_EXCLUDED_SYMBOLS (XRPUSDT, DOGEUSDT, NEARUSDT, BCHUSDT, LDOUSDT, TRXUSDT, BNBUSDT)
                         AND ∉ {LINK, LTC, ATOM, ICP, FIL, CRV} (prior NEGATIVE mining set).
                 Pairwise-disjoint vs BUNDLE-002: CONFIRMED at runtime (UNIUSDT ∩ {DOT,ETH,BTC,AAVE} = ∅).

## (v1) HIGH-RISK Declaration
HIGH-RISK: YES — dual trigger: (1) NEW SYMBOL universe-substitution (UNIUSDT never a training
           objective in v1); (2) NEW 4-feature set changes feature-importance allocation surface.
MITIGATION: single-outer-seed=42 SPECIALIST with 50-inner-seed averaging (variance control).
            Multi-seed CONFIRMATION PERMANENTLY DROPPED per user directive 2026-06-09.
            Escalation clause pre-registered in brief: NEGATIVE verdict triggers
            "burden of proof has shifted to architecture" diary finding, NOT a multi-seed re-run.

## (v1) LM Master Response Verification
- briefs-v1/iteration_v1-085/lgbm_advisor.md exists: PASS
  (commit 82f02eb6; confidence LOW-to-MEDIUM lean LOW; predicted IS Sharpe +0.35 range +0.10/+0.65)
- Brief Section 3.5 addresses each LM Master recommendation: PASS
  - Rec 1 (KEEP HP lock): ADOPTED — Section 3.4 holds the 50×30×depth-5×leaves-31 lock.
  - Rec 2 (min_data_in_leaf 80-100 floor): MODIFIED/DEFERRED — deferred to /086 as first lever;
    rationale: HP change would confound pure 4-feature verdict; single-bit discipline.
  - Rec 3 (confirm lambda_l1 > 0 reachable): ADOPTED (verify-only) — standard v1 Optuna space.
  - Post-mortem / n_estimators pinning: ADOPTED as 7.4 telemetry.
  - Per-feature rank predictions (F2-PRIMARY rev_extension_z_3 rank ≥14; F2-SUSPICION
    capstone rank 1 + primitive ≥8; F2-COLLECTIVE <30 gain): ADOPTED + HARDWIRED into Section 4.
  - Risk A (probe sub-gate): ADOPTED + HARDWIRED as F3.
  - Risk B (IS/OOS ratio < 0.4): ADOPTED as 7.4 telemetry.
  - Risk C (≥50 OOS trade floor): ADOPTED + PRE-REGISTERED in Section 4.1.
  - "Optional 52-col pre-flight probe": ADOPTED as OPTIONAL Phase 6 pre-flight.
  - No multi-seed CONFIRMATION recommended or entertained: CONFIRMED.

## Cadence Check (v1 SPECIALIST)
- Wall-clock budget declared: ~5.5–8h (user-mandated SPECIALIST budget per 50-seed ×
  30-trial × 24-month lock; exceeds default 2h EXPLORATION cap by design; no kill-switch;
  overrun documented, not killed). Split-engineer dispatch applies per
  feedback_split_engineer_dispatch.md (>30min backtest). PASS — wall-clock declared and
  consistent with the /078/083/084 precedent for the same methodology lock.

## Sacred Constants Verification
- OOS_CUTOFF_DATE = 2025-03-24: PASS (run_iteration_085.py line 53; config.py OOS_CUTOFF_MS=1742774400000)
- training_months = 24: PASS (run_iteration_085.py confirmed)
- 50 inner seeds (42..91): PASS (run_iteration_085.py V1_SPECIALIST_SEEDS = tuple(range(42,92)), asserted len==50)
- max_depth = 5, num_leaves = 31: PASS (run_iteration_085.py; FIXED, removed from Optuna search)
- Global V1_FEATURE_COLUMNS_PRUNED == 48: PASS (runtime: len=48; assert at __init__.py:213-214)
- V1_ITER085_FEATURE_COLUMNS == 52: PASS (runtime: len=52; assert at __init__.py:242-244)
- New LOCAL cols (4): rev_extension_z_3, rev_halflife_50, rev_vol_gate_signed, vol_state_z_natr_30
  (all present; none modify global PRUNED)

## Track Isolation
- mean_reversion_v1.py: ZERO imports from features_v2/features_v3 — PASS
- volatility_v1.py: ZERO imports from features_v2/features_v3 — PASS
- composed_v1.py: ZERO imports from features_v2/features_v3 — PASS

## Tests
- tests/test_iteration_v1_085.py: 37/37 PASS (commit 7dc58418; includes past-only, clip,
  semantic, track-isolation, parquet, hash, dispatch guards)
- tests/features_v1/ + tests/test_config.py: 69 additional PASS (run 2026-06-09)
  Total targeted run: 106/106 PASS

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 explicitly
  stated; IS window named (4.51y to OOS cutoff); OOS window named (2025-03-24 → present).
  Sacred constants held per feedback_training_window.md + feedback_no_cheating.md.
- Section 0.5 (Iteration Type): PASS — TYPE: SPECIALIST declared; wall-clock budget stated;
  NO multi-seed CONFIRMATION stated (user directive); cycle-7 mandate context provided.
- Section 0.6 (Architecture-Family Justification): PASS — per-cohort-specialization-UNI
  declared; mandate suspension rationale; prior 5 SPECIALIST cohorts listed (/064 ETH /065 BTC
  /078 AAVE /083 FIL /084 CRV); ROTATION_STATUS=VALID with cohort-orthogonality reasoning;
  pairwise-disjoint vs BUNDLE-002 explicitly stated.
- Section 1 (Hypothesis): PASS — one-sentence (multi-clause) specific hypothesis naming
  exact features, exact mechanism (lag-3 reversion + vol-state coordinates), and expected
  effect (lift above −0.243 probe). Vagueness bar cleared; explicit falsification frame.
- Section 2 (IS-Only Evidence): BLOCK — see Reasons below.
  Scripts referenced: analysis/iteration_v1-085/uni_prescreen.py,
                      analysis/iteration_v1-085/probe_UNIUSDT.py,
                      analysis/iteration_v1-085/structure_prescreen_*.py
  COMMITTED scripts (git ls-files): analysis/iteration_v1-085/probe_GRTUSDT.py (only)
  UNTRACKED (unconfirmed reproducible): uni_prescreen.py, probe_UNIUSDT.py,
    structure_prescreen_algo.py, structure_prescreen_etc.py, structure_prescreen_grt.py,
    structure_prescreen_matic.py, structure_prescreen_op.py, structure_prescreen_xlm.py,
    uni_prescreen_results.csv, probe_UNIUSDT_results.csv, structure_prescreen_summary.csv,
    and 7 other result CSVs.
  Brief Section 2 claims "produced by the committed IS-only scripts" — this claim is
  materially false for the load-bearing gate-evidence scripts. The gate numbers (probe
  −0.243, autocorr_mag 0.0843, max IC 0.0393, trivial_min −0.2485) are cited from these
  untracked files; reproducibility cannot be verified without the committed scripts.
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — HIGH-RISK declared; dual triggers
  stated (new symbol + new 4-feature set); mitigation stated (50-inner-seed, no multi-seed
  CONFIRMATION per directive); attribution-entanglement acknowledged.
- Section 3 (Proposed Changes): PASS — enumerated: symbol (UNIUSDT added), 4 NEW LOCAL
  features (specs, warmup, clip, orthogonal-decomposition table), no new risk primitive.
  LM Master responses in Section 3.5 (every recommendation addressed). Global PRUNED stays
  48 (LOCAL-only architecture maintained).
- Section 4 (Expected OOS Impact): PASS — predicted IS Sharpe modal +0.35 range [+0.10,+0.65];
  OOS Sharpe modal +0.05 range [−0.50,+0.55]; explicit falsifiers F1/F2/F3/F4/FB1 with
  numerical thresholds; pre-registered trade counts (modal 90–140 OOS, 180–280 IS);
  explicit hypothesis-rejection threshold stated.
- Section 5 (Risk Mitigation): PASS-WITH-NOTE — content is substantively present but
  Section 5 is not explicitly numbered. The R1/R2/R3/R5 stack with IS-calibrated thresholds
  and simulated effects appears across Section 3.3, Section 6, and the trailing "Risk
  Mitigation" appendix (line 372). Content satisfies the gate requirement; the numbering
  omission is a cosmetic gap that does NOT constitute a BLOCK.
- Section 6 (Risk Management Design): PASS — full 8-primitive-equivalent table (R1
  DISABLED / R2 DISABLED / R3 OOD 0.70 cutoff / R5 vol-target vt_target_vol=0.3 /
  rev_vol_gate_signed as feature-level soft gate); fire-rate predictions IS+OOS;
  regime coverage rationale; simulated historical effect per /063/064/065/078 roster.
- Section 7 (Failure-Mode Prediction): PASS — 3 failure modes pre-registered with
  probability ordering: (1) NEGATIVE-PROBE-FLAT (modal); (2) NEGATIVE-INERT-FEATURE;
  (3) SUSPICIOUS-STRUCTURE-ABSENCE. Per-mode gate identification provided. Forward-looking,
  not post-hoc.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — pre-registered SPECIALIST candidacy bands
  (PROMISING-STRONG ≥+0.40, PROMISING-TENTATIVE +0.10/+0.40, NEGATIVE <+0.10) with
  explicit conditions; HARD gates table (IS trades ≥50, OOS trades ≥50, collective
  importance ≥30, probe lift >+0.25, ML IS Sharpe >+0.00); future-bundle MERGE gates
  inherited at assembly. NO multi-seed CONFIRMATION gate (user directive).
- Section 9 (Library Stack): PASS — 7-library version table (Python 3.13, lightgbm 4.6.0,
  optuna 4.8.0, numpy 2.2.x, pandas 3.0.x, scikit-learn 1.8.x, scipy 1.17.x); no new
  third-party dependencies; DSR/PBO/PSR not computed at SPECIALIST EXPLORATION layer;
  track isolation stated.

## Branch Note (non-blocking)
Current branch: iteration-v1/084 (expected: iteration-v1/085). The /085 commits
(7dc58418, 82f02eb6, 88e68366) are on the /084 branch — no iteration-v1/085 branch was
created. This is a branch-naming administrative issue, NOT a Phase 5.5 BLOCK condition.
QR may create iteration-v1/085 from HEAD (git branch iteration-v1/085 && git checkout
iteration-v1/085) before Phase 6 if desired; the gate BLOCK below takes precedence.

## Reasons (BLOCK)
- Section 2 (IS-Only Evidence) — ANALYSIS SCRIPTS NOT COMMITTED:
  The load-bearing GATE-1 + GATE-2 analysis scripts and result CSVs cited in Section 2
  as "committed IS-only scripts" are NOT in git history. Specifically:
    (a) analysis/iteration_v1-085/uni_prescreen.py — UNTRACKED (the GATE-1 trivial-baseline
        + GATE-2 IC + autocorr evidence for UNIUSDT; produces uni_prescreen_results.csv)
    (b) analysis/iteration_v1-085/probe_UNIUSDT.py — UNTRACKED (the GATE-2 PRIMARY probe
        IS Sharpe −0.243 evidence; produces probe_UNIUSDT_results.csv)
    (c) analysis/iteration_v1-085/structure_prescreen_*.py (7 scripts) — all UNTRACKED
        (the eligible-pool sweep evidence cited in Section 2.2)
    (d) All associated result CSVs (uni_prescreen_results.csv, probe_UNIUSDT_results.csv,
        structure_prescreen_summary.csv, and 6 symbol-specific CSVs) — UNTRACKED
  The gate numbers in Sections 2.1/2.2/2.3 (probe −0.243, IC 0.0393, autocorr_mag 0.0843,
  trivial_min −0.2485) are not reproducible from the committed codebase. The "committed
  script" reproducibility requirement per the Phase 5.5 schema is NOT met.
  Fix: `git add analysis/iteration_v1-085/` and commit with
  `analysis(iter-v1/085): commit IS-only EDA scripts + result CSVs`.
