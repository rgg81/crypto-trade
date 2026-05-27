# Phase 5.5 Gate — iter-v1/025

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION
Cadence position: Cycle-3 EXPLORATION #10/10 — LAST EXPLORATION before /027 CONFIRMATION.

## Axis Family + Rotation Status (Section 0.6)
FAMILY: feature-family
Prior 5 EXPLORATION families (going into /025):
  - iter-v1/020: per-cohort-specialization-BTC
  - iter-v1/021: methodology-pivot
  - iter-v1/022: per-cohort-specialization-LTC
  - iter-v1/023: feature-family
  - iter-v1/024: model-arch
`feature-family` appears exactly ONCE in the prior 5 (iter-v1/023 funding). Not 5-of-5 same family.
ROTATION_STATUS: VALID — Critic Phase 7.5 /024 Path Forward #1 explicit permission for borderline 2-consecutive feature-family when NEW data class (OI, not funding). Rotation discipline NOT triggered.

## HIGH-RISK Declaration (Section 2.5)
HIGH-RISK: YES
Reason: NEW data class + NEW data ingestion pipeline (4-symbol OI fetch) + V1_FEATURE_COLUMNS_PRUNED 42→43 changes Optuna's training-objective domain.
Mitigation: OPT-IN single-seed=42 (NOT mandatory multi-seed). Rationale: feature-family axis has lower basin-relocation risk than model-arch or per-cohort axes; /023 feature-family produced NEG-clean -0.20 (NOT NEG-CAT). Mitigation justification accepted.
4th HIGH-RISK declaration in cycle-3 (/020, /022, /024, /025).

## LM Master Response Verification (Section 3.4)
- briefs-v1/iteration_v1-025/lgbm_advisor.md exists: PASS (HEAD 9502ecd per brief)
- Brief Section 3.4 addresses each LM Master recommendation:
  - §1 (Q4 depth-3-learnable + HARD BLOCK): ADOPTED — reflected in Section 1 close + Section 3.6 + 6.1
  - §2 (Verdict-prior recalibration 22/8/22/30/12/4/2): ADOPTED — Section 5 priors revised
  - §3 (F-AXIS #1 DUAL GATE TIGHTEN + breadth check): ADOPTED — Section 4 F-AXIS #1 updated with 3-sub-gate structure
  - §4 (HARD BLOCK on OI fetch ≥3/5 symbols ≥1000 IS rows): ADOPTED (BINDING) — Section 3.6 + 6.1 + 10.1 + 10.6
  - §5(a) (Skip-month NaN policy): ADOPTED — Section 3.1 + 3.6 NaN regime policy
  - §5(b) (Per-fold rank emission): ADOPTED — Section 10.4 + 10.5 deliverables updated
  - §6 (/027 bundle composition matrix): ADOPTED — Section 11.6 full matrix
  - §7 (duplicate of §1): ADOPTED — Section 1 close
  - §8 (/026 verdict-conditional staging matrix): ADOPTED — Section 11.7 full matrix
  - §9 (Critic Phase 7.5 priority items 1-5): ADOPTED — Section 10.8 new subsection
  - Net: 9/9 LM Master recommendations ADOPTED (zero MODIFIED, zero REJECTED)
  Brief Section 3 addresses LM Master recommendations: PASS

## Cadence Check
- EXPLORATION wall-clock budget declared: 35-45 min target, 2h HARD CAP declared: PASS
- Cycle-3 EXPLORATION count: #10/10 (LAST EXPLORATION) — PASS
- CONFIRMATION iteration (/027) staged correctly as next iteration after /026 sanity slot: PASS
- CONFIRMATION precedents check: NOT APPLICABLE (this is an EXPLORATION, not a CONFIRMATION)

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE = 2025-03-24 confirmed (BASELINE_V1.md); training_months = 24 stated; IS window 2023-03 → 2025-03 stated; OOS window 2025-03-24 → present stated.

- Section 0.5 (Iteration Type, v1): PASS — TYPE=EXPLORATION declared; cadence position cycle-3 #10/10 declared; /026 sanity + /027 CONFIRMATION pre-staging documented.

- Section 0.6 (Architecture-Family Justification, v1): PASS — family=feature-family; prior 5 enumerated; rotation status VALID per Critic §11.7 explicit permission for borderline 2-consecutive feature-family when NEW data class; one-sentence rationale citing BIS WP 1087 + SSRN 5611392 OI cascade-catalyst literature.

- Section 0.7 (Wall-clock target): PASS — 35-45 min target, 2h HARD CAP. (Not a mandatory section but present and consistent with cadence discipline.)

- Section 1 (Hypothesis): PASS — specific hypothesis: "OI delta captures leveraged-position buildup / unwinding velocity; at extreme values it signals mean-reversion / cascade catalysts that LightGBM can ingest as a NEW orthogonal feature alongside funding-rate signals." Q4 depth-3-learnable structural argument included. H1 falsifier pre-registered (F-AXIS #1 DUAL GATE rank+gain+breadth). H2 (orthogonality) + H2 falsifier present. Not vague.

- Section 2 (IS-Only Evidence): PASS with NOTE — committed script at analysis/iteration_v1-025/oi_eda.py; BTC IS-only EDA covers (a) availability, (b) distribution, (c) IC vs TOP5, (d) orthogonality vs funding, (e) ORACLE forward-return banding (Q4 Sharpe-proxy +1.68), (f) ADF stationarity. Non-BTC EDA deferred to Section 2.8 RESERVED (fetch in progress at brief authoring time). Defense for BTC-only EDA accepted: methodology same as /023 funding EDA; BTC IC results conservative; BTC OI is load-bearing cross-asset signal (v3 /121 baseline). NOTE: Section 2.8 remains placeholder; QE must update oi_availability.csv after fetch completes and re-run EDA before backtest dispatch.

- Section 2.5 (HIGH-RISK Axis Declaration, v1): PASS — HIGH-RISK declared; reason (new data class + 42→43 column expansion changes Optuna training-objective domain); mitigation (OPT-IN single-seed=42, feature-family lower basin-relocation risk than model-arch/per-cohort axes, /023 precedent); failure-mode coverage (F-AXIS #1 DUAL GATE catches INERT, F1 OOS band catches NEG-clean, F1 ≤ -0.55 catches NEG-CAT with auto-trip multi-seed mandate).

- Section 3 (Proposed Changes): PASS — enumerated changes: (3.1) NEW module oi_delta_v1.py with add_oi_delta_v1_features + compute_oi_delta_zscore functions + skip-month NaN policy; (3.2) V1_FEATURE_COLUMNS_PRUNED 42→43; (3.3) single feature not pair (SAME-FAMILY rule honored); (3.4) LM Master Phase 4.5 responses (9/9 ADOPTED); (3.5) run_baseline_v1.py dispatch branch; (3.6) HARD BLOCK precondition for OI fetch (≥3/5 symbols ≥1000 IS rows, per-symbol assertion code provided).

- Section 4 (Expected OOS Impact / Falsifiers): PASS — F1 OOS Sharpe Δ bands (PROMISING ≥+0.10, INERT ±0.10, NEG-clean [-0.55,-0.10), NEG-CAT ≤-0.55); F-AXIS #1 DUAL GATE 3-sub-gate structure (rank ≤14/43 on ≥2 cohorts + gain ≥4.0% on ≥2 cohorts + breadth rank ≤20/43 on ≥3 cohorts); F-AXIS #2 trade count; F-AXIS #3 orthogonality vs funding; F-AXIS #4 n_eff; F-AXIS #5 ADF; F3 IS Sharpe auto-reject; F7 behavioral expectation. Verdict matrix with explicit falsification triggers.

- Section 5 (Risk Mitigation / Predicted Priors): PASS — post-LM-Master priors (22/8/22/30/12/4/2); rationale for each shift documented; modal expectation LEARNED-NEGATIVE 30%.

- Section 6 (Risk Management Design / Failure Modes): PASS — 7 failure modes (OI unavailable → BLOCK-PENDING-FIX; INERT-by-importance; LEARNED-NEGATIVE; PROMISING; NEG-CAT; REDUNDANT-WITH-FUNDING; dispatch defect). HARD BLOCK precondition on OI fetch. Skip-month NaN policy. Anti-pattern static scan for silent NaN-fill. walk_forward.py:113 regression check. OI coverage assertion code.

- Section 7 (Pre-Registered Failure-Mode Prediction, v1): PASS — 9-row pre-registered prediction table covering BTC rank, gain share, IC vs funding, OOS Sharpe Δ, verdict modal mass, n_eff, IS/OOS trade counts, ADF stationarity. Explicit falsification triggers per row.

- Section 8 (MERGE/NO-MERGE Criteria, v1): PASS — correctly declares EXPLORATION (no baseline update); Section 8 provides verdict→/027 bundle composition matrix (6 verdicts × 3 columns). Appropriate for EXPLORATION. /027 CONFIRMATION will carry the MERGE/NO-MERGE decision.

- Section 9 (Library Stack, v1): PASS — pandas, numpy, lightgbm, statsmodels, mlfinlab==1.4, pypbo listed; no new dependencies; httpx already installed; fallbacks not needed.

## Additional v1-Only Checks

### OI Fetch Status (at Phase 5.5 gate time)
Current OI coverage (from analysis/iteration_v1-025/oi_availability.csv):
  - BTCUSDT: PRESENT, 4994 IS rows — PASS
  - ETHUSDT: MISSING, 0 IS rows — OI fetch in progress (PID 3710369 running)
  - LINKUSDT: MISSING, 0 IS rows — OI fetch in progress
  - LTCUSDT: MISSING, 0 IS rows — OI fetch in progress
  - DOTUSDT: MISSING, 0 IS rows — OI fetch in progress

Phase 5.5 gate verdict on fetch status: PASS (Phase 5.5 does not require the fetch to be complete). The brief explicitly acknowledges the partial-fetch state in Section 2 (BTC-only EDA as proof-of-methodology) and commits to the HARD BLOCK at Phase 6.0 (Section 3.6 + 10.6). The HARD BLOCK on ≥3/5 symbols ≥1000 IS rows is a Phase 6.0 gate, not a Phase 5.5 gate.

Phase 6.0 Critic HARD BLOCK status: PENDING (OI fetch in progress; Critic must re-check oi_coverage_check.csv at pre-flight time). If fewer than 3/5 symbols have ≥1000 IS rows at Phase 6.0 → BLOCK-PENDING-FIX per Section 6.1.

### walk_forward.py:113 regression
Verified at gate time: `train_end_ms = test_start_ms - embargo_ms` — PASS (correct embargo fix present).

### Foundation baseline unchanged
- OOS_CUTOFF_DATE = 2025-03-24 stated in brief Section 0 — PASS
- training_months = 24 stated — PASS
- V1_BASELINE_UNIVERSE unchanged (5-symbol: BTC/ETH/LINK/LTC/DOT) — PASS
- V1_FEATURE_COLUMNS_PRUNED currently 42; brief proposes 42→43 (single addition oi_delta_30_z90) — PASS

## Reasons for OVERALL=PASS
All 11 mandatory sections present and substantive. LM Master advisory exists. Section 3.4 addresses all 9/9 LM Master recommendations. Rotation VALID. HIGH-RISK declared with justification. walk_forward.py:113 embargo fix confirmed. EDA script committed. Section 2 evidence BTC-complete; non-BTC EDA deferred with documented defense; HARD BLOCK at Phase 6.0 covers the gap.

## Critical Handoff Notes for Phase 6.0 Critic
1. OI fetch HARD BLOCK is the PRIMARY Phase 6.0 check. Critic must verify oi_coverage_check.csv shows ≥3/5 symbols ≥1000 IS rows before backtest can launch. If <3/5 → BLOCK-PENDING-FIX.
2. Track isolation check: `grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v1/` and `grep -r "from crypto_trade.features_v3" src/crypto_trade/features_v1/` must both be empty after QE implements oi_delta_v1.py.
3. Anti-pattern check: no `np.zeros` or `np.nan` silent-fill fallback in oi_delta_v1.py; FileNotFoundError must be raised on missing OI cache.
4. V1_FEATURE_COLUMNS_PRUNED length assert must be updated to 43.
5. Per-fold feature importance table (24 walk-forward months × symbol) required in engineering report per LM Master §5(b) ADOPTED.
