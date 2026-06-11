# Phase 6.0 Critic Pre-Flight — iter-v1/091

OVERALL: PASS

## Iteration Type
SPECIALIST — machinery EXPLORATION (2nd machinery axis of cycle-7; risk-primitive / post-aggregator RULE family). Test seat ETH/064.

## Checks
- **Check 1 Look-Ahead: PASS.** R-CONV gate uses ONLY the current candle's `_sp_confidence` (from the 50 seeds' predict_proba on THIS candle; lgbm.py:2144-2154); pure scalar comparison `_sp_confidence < r_conv_tau` (2194), no forward data/window/return-scan. IS-only τ derivation (analysis/iteration_v1-091/conviction_distribution.py reads only in_sample/trades.csv); τ=0.06 hardwired in run_iteration_091.py + run_baseline_v1.py:8884; no OOS read in the dispatch.
- **Check 13 Anti-Pattern: PASS.** A1 (walk_forward.py:113 embargo intact, not touched), A2/A3 clean, A12 N/A (SPECIALIST), A13 (dispersion CSV write-only). Diff confined to 2 init params + the gate branch + V1_ITER091_UNIVERSE + the v1-091 dispatch.
- **Foundation Regression: PASS.** walk_forward.py:113 `train_end_ms = test_start_ms - embargo_ms` unchanged; LOCK intact (50 seeds range(42,92), 30 trials, PRUNED==48 module-assert, OOS_CUTOFF imported, training_months=24). **Default-OFF byte-identity CONFIRMED**: gate guarded by `if self._enable_r_conv_gate and ...`, default False → branch fully skipped → bit-identical to pre-/091 for every existing iteration. Gate sits after `_sp_confidence` (2181), before Signal build (2231), same band as /074 AXIS-R / /084 R-FADE — stateless, no model/seed/trial/Optuna change. **Dispersion-pollution guard CONFIRMED**: skip returns NO_SIGNAL (2211) BEFORE `_specialist_dispersion_stats.append()` (2284). **ensemble_std on skips CONFIRMED** (r_conv_skip decision_log carries ensemble_std, 2205 — LM §1 deliverable wired).
- **Cadence + Axis: PASS.** 5.5 gate PASS; axis risk-primitive/aggregation matches src/; rotation VALID (prior 5: feature-family/universe×3/sample-weighting; risk-primitive not among them) — 2nd machinery axis after /090. PRUNED 48, zero new features, lock intact.
- **Falsifier Presence: PASS.** F1 (IS Δ≥+0.20 VALIDATED / <0 NEGATIVE), F2 (trade count must reduce; reduced-but-flat → NEG-NO-EFFECT), F3 (≥50 OOS survive else NEG-OVERFILTER), F4 (OOS Δ not ≤−0.30 while IS positive + conviction-vs-NATR/hold/trend-strength selection-bias guards). τ=0.06 hardwired (NOT OOS-tuned); the LM OOS diagnostic (dropped-set +6.25% OOS vs −5.43% IS) is pre-registered in §3.5 as a SKEPTICAL Phase-7 lens that caps an IS-only F1≥+0.20-with-flat/neg-OOS at TENTATIVE — correct anti-tuning posture.

## Observation for Phase 7.5 (non-blocking)
tests/test_r_conv.py exercises the gate ON/OFF logic by re-implementing the conditional inline (the _make_specialist_mock helper is a stub) rather than driving get_signal() end-to-end — verifies param storage + boolean algebra but not the actual code path at lgbm.py:2194. Byte-identity + ordering are verified by direct code inspection (above), so this does not gate the backtest; 7.5 to revisit test-coverage adequacy.

OVERALL=PASS
