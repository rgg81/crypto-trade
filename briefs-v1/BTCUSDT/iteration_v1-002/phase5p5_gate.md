# Phase 5.5 Gate — iter-v1/002 (EXPLORATION, BTCUSDT)

OVERALL: PASS

## Scope (redesigned single-symbol v1 — Phase 5.5 gate)
Per the v1 redesign (2026-06-15), the Phase 5.5 gate for the single-symbol track
checks that: (1) the research_brief + feature_report + risk_report all exist,
(2) exactly one symbol is resolved, (3) the slippage cost assumption is stated.
Retired for v1: lgbm_advisor.md / specialist_catalog.md / Axis Rotation /
HIGH-RISK declaration / Critic Phase 6.0 pre-flight (Critic is now RESULTS-ONLY
at Phase 7.5). Those are NOT checked here.

## Brief-Completeness Checks
- research_brief.md present: PASS
  (`briefs-v1/BTCUSDT/iteration_v1-002/research_brief.md`)
- feature_report.md present: PASS
  (`briefs-v1/BTCUSDT/iteration_v1-002/feature_report.md`)
- risk_report.md present: PASS
  (`briefs-v1/BTCUSDT/iteration_v1-002/risk_report.md`)
- Single symbol resolved = BTCUSDT: PASS
  (brief Mode line + "Changes" §1; FE report header; risk report header;
   run command `--symbols BTCUSDT` in all three docs — no multi-symbol leak)
- Slippage cost assumption stated = 2.0 bps/side (0.04% round-trip): PASS
  (brief line 3 + §3.3; risk report §5 pre-registers `--slippage-bps 2` as the
   merge bar, with {1,2,4} cost-stress sweep as robustness context)

## Mode / Seed-Rule Check (redesigned single-symbol)
- Iteration TYPE: EXPLORATION (screen only — never merges). PASS
- Bagging K = 3 (EXPLORATION). PASS — brief Mode line + §3.3 "seed rule (K=3)".
- inner ensemble = 1, outer seeds = 1: UNCHANGED from BASELINE_V1_BTCUSDT rule. PASS
  (the runner fixes inner=1, outer seeds=1; K is the only seed number that
   varies — confirmed against the universal single-symbol routing guard).
- n_trials = 35 per seed (honored): PASS (brief Mode line).
- bounds_profile = v1_specialist (unchanged): PASS (FE report §4 — explicitly
  KEEP profile, do not widen depth/leaves, to isolate the prune variable).
- training_days = Optuna-searched 10..500 (IMMUTABLE-by-policy, NOT narrowed): PASS
  (FE report §4 row 8 + brief §3.3).
- OOS_CUTOFF = 2025-03-24 unchanged; training_months/embargo intact: PASS
  (brief §3.3; risk report constants OOS_CUTOFF_MS=1742774400000).

## Change-Attribution Check (one-variable discipline)
This EXPLORATION screen changes TWO things jointly (feature prune + R2 brake).
This is ACCEPTABLE for the gate because:
- The PRIMARY axis is the 41-col feature prune.
- The R2 brake is size-only (scales `weight_factor` in deep-drawdown pockets);
  it does NOT suppress entries, so the trade roster is ~unchanged (risk report
  §1.4: 200 trades, trade count unchanged) — minimal confound of the feature read.
- The brief PRE-REGISTERS (§"Attribution caveat" + falsifiers) that if PROMISING,
  the K=20 CONFIRMATION MUST include a feature-only ablation to attribute the lift.
The attribution risk is acknowledged, bounded, and carried forward to CONFIRMATION.
Gate does not BLOCK on it for an EXPLORATION screen.

## IS-Only Evidence Check
- FE report: committed IS-only scripts (ic_pruning_audit.py, build_pruned_set.py,
  dispersion_proxy.py) with concrete IC/cluster/importance tables, IS cutoff
  close_time < 1742774400000. PASS.
- Risk report: committed IS-only script (risk_is_analysis.py), IS-only stress
  matrix + Kelly + R2 simulated effect. PASS.
- Pre-registered falsifiers stated (FE §6, risk §5, brief). PASS.

## Verified Engineering Inputs
- 41-col `V1_BTC_PRUNED_ITER002` is a STRICT SUBSET of `V1_FEATURE_COLUMNS`:
  VERIFIED — 41 unique members, all present in the 193-col set, 0 missing.
- R2 override values (8.0 / 0.5 / 18.0) match risk report §6 pre-registered config.

## Reasons (if BLOCK)
- none — OVERALL=PASS.
