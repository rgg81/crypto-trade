# Phase 5.5 Gate — iter-v3/020

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 restated as IMMUTABLE. n_trials=35 for EXPLORATION mode. IS window 2023-03-24→2025-03-23, OOS window post-2025-03-24.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION, cadence #2 of 10 post-bootstrap. References `feedback_v3_iter019_axis_priorities.md` LOCKED HIGH #2 (concentration architecture). STRUCTURAL axis (NEW risk primitive), NOT a gate-threshold knob. NEVER updates BASELINE_V3.md.
- Section 1 (Hypothesis): PASS — One sentence plus mechanism explanation. Specific: adding `max_per_symbol_pnl_share=0.40` rolling cap inside `RiskV2Wrapper` reduces single-symbol lottery risk while preserving directional edge. Predicted IS band [+0.30, +0.55] median +0.40 / OOS band [+0.45, +0.65] median +0.55. Mechanism clearly distinguished from signal-gating (cap scales weight, does not kill signals).
- Section 2 (IS-Only Numerical Evidence): PASS — Analysis script `analysis/iteration_v3-020/per_symbol_cap_eda.py` committed at SHA `bbbe783` BEFORE brief. Seven output files committed alongside. Three counterfactual modes (Mode A static, Mode B rolling-90-bars) with concrete IS/OOS Sharpe tables. PATH C lower-bound confirmed numerically. Behavioral-effect predictor with derived saturation band [129, 215] anchored at iter-v3/018 IS trades 172 (±25%). Setup integrity table with 10 PASS rows. No category-matching; all numbers from executed code on IS trades only.
- Section 3 (Proposed Changes): PASS — Enumerated 10-item sub-fix decomposition with verifier commands for each. 15-row reconciliation table. Single varied axis (+cap mechanism). Symbols, labeling, existing gates, universe all UNCHANGED. Feature revert (14→13, funding dropped) mandated by Critic FINAL Rec 2 of iter-v3/019. sklearn pin mandated by Critic Check 12 of iter-v3/019.
- Section 4 (Expected OOS Impact): PASS — IS predicted band [+0.30, +0.55] / OOS predicted band [+0.45, +0.65]. 5 falsifiers explicitly pre-registered (Falsifier 1: IS<anchor AND OOS<anchor-0.10; Falsifier 2: IS trades outside [129,215]; Falsifier 3: wall-clock>30min; Falsifier 4: cap fire rate<5%; Falsifier 5: post-cap top-share>40%). Catalog framing table with 5 verdict conditions and next-iteration routing.
- Section 5 (Risk Mitigation): PASS — 5 cadence-discipline safeguards + 4 methodology-specific safeguards = 9 total. 4 axis-specific risks identified: (1) signed vs absolute share semantics, (2) look-ahead in rolling window, (3) vol-scaling composition, (4) Optuna preemption of cap. Each risk has explicit mitigation.
- Section 6 (Risk Management Design): PASS — 8-primitive table (7 inherited + 1 NEW: per-symbol cap). Fire-rate predictions, regime coverage per primitive. Order-of-operations specified. Primitive 8 correctly distinguished as SCALING not KILL gate. Gate orthogonality documented.
- Section 7 (Failure-Mode Prediction): PASS — 8 predictions calibrated. Process predictions P1-P3 (35% combined): cap not propagated to get_signal; look-ahead bug; share-semantics ambiguity. Model predictions P4-P8 (100% = PATH A/INERT/MECHANICAL/NEGATIVE/INERT-Optuna). P6 (PATH C) at 30% explicitly motivated by counterfactual evidence. Calibrated against 11 prior EXPLORATIONs.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 11 EXPLORATION criteria pre-registered. Criteria 1-3 lock the OOS Sharpe band thresholds numerically. Criterion 11 = saturation falsifier [129,215] + cap-fire-rate ≥5% + top-share<40%. No post-hoc rationalization possible. Catalog-axis verdicts mapped to §4.4 table.
- Section 9 (Library Stack Declaration): PASS — Full stack listed. sklearn pinned at >=1.8,<1.9 (addresses Critic Check 12 from iter-v3/019). No new package additions. Cap mechanism uses only stdlib dataclass + numpy (already imported). Sub-fix #8 cross-references pyproject.toml change.

## Reasons (if BLOCK)

None — all 10 mandatory sections PASS.

## Additional Checks

- Single-axis variation: PASS — only `max_per_symbol_pnl_share=0.40` cap added as the varied axis. Funding-feature revert is a mandated pre-commit (Critic FINAL Rec 2), not a second axis.
- Sacred constants: PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 explicitly stated as IMMUTABLE in Section 0.
- Analysis script committed BEFORE brief: PASS — SHA `bbbe783` cited, outputs enumerated.
- IS-only discipline: PASS — analysis script reads iter-v3/018 IS+OOS trades only (split is mechanical by OOS_CUTOFF_MS; no future-peeking).
- Behavioral-effect predictor: PASS — saturation band derived from anchor IS trades 172 ±25% = [129,215] per `feedback_axis_saturation_predictor.md`. Secondary verifier (cap fire rate ≥5%) pre-registered as Falsifier 4.
- Library isolation: PASS — Section 9 confirms no new dependencies; RiskV2Config uses only stdlib + numpy.
