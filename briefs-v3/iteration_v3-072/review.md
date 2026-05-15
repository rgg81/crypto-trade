# Phase 7.5 Critic Review — iter-v3/072

OVERALL: EXPLORATION-NEGATIVE — fixed-horizon labeling is a genuine catastrophic strategy property (label-execution decoupling), NOT a methodology bug; the NEGATIVE classification is certified clean.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION — cycle 2 #2 of 10. Axis: ALTERNATIVE LABELING (fixed-horizon-21 return-sign label replacing ATR triple-barrier).

## Clarifications Requested from QR — NONE

Every check resolved unambiguously. Look-ahead audit provable by embargo arithmetic; backward-compat provable by code structure; QE root cause corroborated by the methodology reference. Round 2 skipped.

## Foundation Audit (Boot Steps 9-11)

**Walk-forward lookahead fix INTACT.** `walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms`. `compute_embargo_candles(10080, 480) = 22`. (Note: `feedback_v3_walkforward_lookahead_bug.md` memory entry is stale — live code is fixed; same discrepancy /070+/071 Critics flagged.)

**labeling.py NEW `label_mode` param CORRECT.** The `fixed_horizon` branch reads `close[t+21]` exactly (loop terminates at the timeout candle: candle t+21 has close_time = deadline, processed; t+22 > deadline, break). `label = sign(fwd_return_pct)`; `long_pnl/short_pnl` fee-net sign-consistent. The `triple_barrier` default branch is fully gated behind `if not use_fixed_horizon` / `if use_fixed_horizon` — original barrier logic executes BYTE-IDENTICALLY when label_mode != "fixed_horizon".

**Threading verified end-to-end**: run_baseline_v3.py:1506 → lgbm.py:145/188/369 → labeling.py:143; metalabeling.py:218/257 forwards to M1. Pre-flight assertion at run_baseline_v3.py:746-761 hard-aborts unless label_mode=="fixed_horizon" — run completed, so the switch was active. REQUIRED_GAP=66 + embargo byte-unchanged.

**§11 Anti-Pattern Static Scan CLEAN.** No start_time mutation, no IS-month skipping, no hardcoded sentinels. Sacred constants unchanged. The per-symbol LDO `(1.5, 0.75)` ATR multiplier is /060 state — inert for fixed-horizon labels, unchanged for trade-exit barrier. No second axis.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Fixed-horizon label at training bar t reads `close[t+21]`. Last training bar's label window ends at `open_time[t] + 22 candles < test_start_ms`. Train-end embargo = 22 candles strictly exceeds the 21-candle label horizon. Critically: triple-barrier short-circuits on first hit (reads ≤21 candles); fixed-horizon ALWAYS reads to candle 21 — but the 22-candle embargo was sized for the triple-barrier MAXIMUM (21), so fixed-horizon at exactly 21 is fully covered. No look-ahead.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP = 66 = (21+1)×3. Embargo = 22 candles per cell, symmetric. Label horizon 21 ≤ 22. Byte-identical to triple-barrier baseline.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
DSR=0.0, PSR=0.0, dsr_relative_b4=0.0 — all correctly reflect the negative OOS daily Sharpe (-1.94); psr() of a negative Sharpe collapses to ~0. Not a computation defect — honest output for a losing strategy. **PBO=0.1426 < 0.4 PASS** (the one Check-3 axis that is BLOCK-triggering even at EXPLORATION; it clears). DSR/PSR/B4 FAILs are EXPLORATION-mode edge-axis informational per `feedback_v3_dsr_mode_artifact.md`. n_trials=315 matches budget; n_eff=16 sensible.

### Check 4 — IC Correlation: PASS (no-op delta)
ic_matrix.csv present (14×14). /072 adds/removes ZERO features. Inherited `vwap_dev_20 × regime_momentum_signed_5d = 0.7642` (>0.70) — same WARN-not-FAIL adjudication as /070 Check 4 (Category 2 carve-out; not introduced by this iteration).

### Check 5 — ADF Stationarity: PASS
adf_test.csv per-symbol per-month. False-stationary cells are early-history months (insufficient candles for ADF) — monthly-granularity artifact, not a feature defect. 14-feature set is the inherited /059 baseline; labeling-only change has no ADF surface.

### Check 6 — Pareto Dominance: PASS (not applicable at EXPLORATION)
pareto_front.csv correctly absent — EXPLORATION mode runs single 3-seed ensemble (ensemble_summary.json: mode=exploration, ensemble_size=3, outer=42 lineage). Multi-seed Pareto is CONFIRMATION-mode. Mode-correct absence.

### Check 7 — Reproducibility: PASS
Impl `79990bb`, gate `f2152fd`, engineering report `bca383d` stamped. Explicit per-symbol feature_columns (never None). Ensemble seeds deterministic + logged. Per-symbol wpnl reconciles: -0.6579 + -32.4913 + 7.2210 = -25.9282 = weighted_pnl_total. Bit-reproducible.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1 hypothesis (fixed-horizon label gives M1 a cleaner directional target) honestly FALSIFIED — IS Δ -1.15, OOS Δ -0.80. QR pre-registered this EXACT NEGATIVE failure mode at 35% (Section 7: "if path information was load-bearing, the M1 model will be worse... IS Sharpe down, PF down, trade count up"). Observed: IS PF 1.28→0.90, OOS PF 1.05→0.79, IS trades 159→185 (+26 up as predicted). Pre-registered signature MATCHED. Single-axis discipline preserved (no risk-gate/feature/universe/BacktestConfig change).

## Adversarial-Specific Findings

**Q1 — Genuine property or label-computation bug?** GENUINE PROPERTY. The fixed_horizon branch is verified correct. The catastrophe is structural: a fixed-horizon-trained model predicts 21-candle net direction, but the backtest exits at TP/SL barriers — a trade with positive 21-candle net return can hit SL on candle 3. The methodology reference §4 independently corroborates: fixed-horizon labels are correct ONLY when execution holds to a fixed horizon. The v3 backtest does not. QE's "label-execution mismatch" root cause is methodologically airtight.

**Q2 — Backward-compat byte-identity?** VERIFIED by code structure. The fixed_horizon logic is fully gated; when label_mode != "fixed_horizon" every original line executes unchanged. `test_triple_barrier_default_unchanged` confirms default ≡ explicit "triple_barrier". 53-test v1/v2 backward-compat suite passes. Residual gap (non-blocking): no test pins triple_barrier output against a pre-/072 git revision — structural gating argument is sound, regression risk nil, but a frozen-golden test would be strictly stronger (Rec #2).

**Q3 — Look-ahead embargo coverage?** VERIFIED. 22-candle embargo strictly exceeds 21-candle label horizon. No training label reads test-window data.

**Q4 — Single-axis (execution unchanged)?** VERIFIED. BacktestConfig.timeout_minutes asserted == 10080; DEFAULT_ATR_MULTIPLIERS=(2.0,1.0) + LDO (1.5,0.75) are /060 trade-exit state, unchanged. Training label changed; execution layer did not. Clean single-axis test of the (fixed-horizon label + triple-barrier execution) incoherence.

## Recommendations to QR

1. **Fixed-horizon-labeling axis CLOSED — scope is "label-execution decoupled," not "fixed-horizon" universally.** A coherent fixed-horizon design needs BOTH a fixed-horizon label AND fixed-horizon execution exit (close at candle 21 regardless of TP/SL) — a legitimate future axis but a 2-axis change requiring its own brief + EDA. Do not re-test fixed-horizon-label-only at a different horizon or as a hybrid — the incoherence is horizon-independent.

2. **Backward-compat tests for label-rule changes should pin a frozen golden output.** `test_triple_barrier_default_unchanged` proves new-default ≡ new-explicit, but both run post-/072 code. A test asserting triple_barrier output against a checked-in golden array would catch a future regression that silently mutates the shared path. Low-cost hardening for any iteration touching labeling.py.

3. **The EDA's "directional-spread" metric (Section 2.4) was a misleading PROMISING signal.** The +30-48% matched-horizon spread improvement was real and irrelevant — label-space cleanliness predicts nothing when the label target is decoupled from execution reward. Future labeling-axis EDAs must include a label-vs-execution-consistency diagnostic (fraction of bars where the candidate label agrees with the barrier-first-hit outcome the backtest realizes) BEFORE proposing the axis. The QR's own Section 2.3 agreement table (18-23% disagreement) was the warning sign — reframe disagreement-with-execution as a FALSIFIER, not a feature.
