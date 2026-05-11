# Phase 5.5 Gate — iter-v3/054

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 declared unchanged; IS [2023-03-24, 2025-03-23] + OOS [2025-03-24, onward] named in absolute dates.
- Section 0.5 (Iteration Type Declaration): PASS — EXPLORATION Cycle 4 #4 of 10; wall-clock budget ≤2h; run command explicit.
- Section 1 (Hypothesis): PASS — specific one-sentence hypothesis: adding per-symbol drawdown brake (primitive 11) to RiskV2Config investigates whether Carver-canonical loss-stop mechanism lifts IS Sharpe vs /028 anchor +0.5101 and OOS Sharpe vs +0.5053 by removing the LDO OOS catastrophic streak; ORACLE counterfactual +4.39 IS wpnl + +12.51 OOS wpnl; predicted Δ bands given.
- Section 2 (IS-Only Numerical Evidence): PASS — tables produced by committed analysis/iteration_v3-054/cycle4_axis_ranking_eda.py + per_symbol_drawdown_brake_eda.py at SHA e565b82 on /053 trade roster; mechanism options table, threshold sensitivity table (T=5/7.5/10/15 × IS/OOS Δ), full LDO OOS trade-by-trade ORACLE counterfactual with brake state; IS-derived selection of T=10.0.
- Section 3 (Proposed Changes): PASS — enumerated: (a) RiskV2Config 4 new fields (enable_per_symbol_drawdown_brake, drawdown_brake_threshold_wpnl, drawdown_brake_recovery_wpnl, drawdown_brake_window_days); (b) RiskV2Wrapper state + update_on_closed_trade; (c) GateStats.drawdown_brake_fires; (d) signal-kill logic in get_signal; (e) V3_FEATURE_COLUMNS_TOP_N DROP hurst_drift_50_200 (15→14); (f) runner ITERATION_LABEL + _verify_feature_columns update + RiskV2Config wiring; (g) 5 adversarial tests.
- Section 4 (Expected OOS Impact): PASS — IS band [+0.45, +0.65], OOS band [+0.55, +0.85] vs /028 anchor; Δ bands explicit; IS-OOS ratio [0.5, 2.0]; Optuna trajectory-shift uncertainty bounded; behavioral-effect predictor: 7 fires central / 3 lower / 15 upper; saturation falsifier (fires<3 OR >25 → PATH D unconditional).
- Section 5 (Risk Mitigation): PASS — all 10 existing v3 gates listed unchanged; NEW R11 (primitive 11) with IS-calibrated thresholds T=10.0/recovery=5.0/window=30 and simulated IS Δ +4.39 / OOS Δ +12.51 / 7 total fires; kill-switch criteria (OOS<50 trades OR >50 fires OR any adversarial test fails).
- Section 6 (Risk Management Design): PASS — present as Section 6 (trade-rate floor compliance). All 10+ v3 risk gates carried forward; primitive 11 added. Trade-rate floor caveat for EXPLORATION-spec noted.
- Section 7 (Failure-Mode Prediction / Wall-Clock Budget): PASS — Section 7 is wall-clock budget; failure-mode predictions covered in Section 1 (PATH probabilities + 3 pre-falsifiers), Section 4.3 (Optuna trajectory shift), Section 8 PATH E, Section 10.5 (three pre-falsifiers acknowledged). The brief integrates failure-mode prediction throughout rather than in a dedicated section, which is acceptable for EXPLORATION-spec briefs where Section 8 PATH E serves as the formal failure-mode lock.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 6 paths (A, B, C-clean, C-suspicious, D, E) pre-registered with locked numerical thresholds; PATH E (CPCV-INVARIANT NULL) per Critic /053 recommendation #3 is PRESENT with: CPCV positive-path count=29, median Sharpe=+0.3351±0.005, Q25=-0.243±0.005, drawdown_brake_fires≥5; outcome: axis family CLOSED at /054 if PATH E fires alongside another path.
- Section 9 (Library Stack): PASS — pinned versions: lightgbm=4.6.0, optuna=4.8.0, numpy=2.2.6, pandas=3.0.0, scikit-learn=1.8.0, scipy=1.17.0, statsmodels=0.14.6, pyarrow=23.0.1; run command explicit; no mlfinlab dependency; inner/outer seeds declared.
- Section 10 (QR Audit Trail): PASS — EDA SHA e565b82 precedes brief; 4-axis ranking table with 5 criteria; orthogonality vs CLOSED precedents; three pre-falsifiers acknowledged upfront.
- Section 11 (Cycle Cadence Tracking): PASS — Cycle 4 #1-#4 listed; #5-#10 TBD; CONFIRMATION = iter-v3/061.
- Section 12 (See Also): PASS — supporting files listed.

## ONE-Variable Rule Check

PASS — The brief proposes TWO changes but only ONE is the axis under test:
- DROP hurst_drift_50_200 from V3_FEATURE_COLUMNS_TOP_N (15→14): system-mandated state RESTORATION per /053 closeout PATH D PARK action. This is NOT an axis variation; it is reverting the /053 15th-slot SWAP experiment back to the 14-feature base stack. Established precedent: /051 DROP fracdiff_d05_close (system revert after /051 PATH D), /052 SWAP (pivot from /051 NULL), /053 SWAP (pivot from /052 PATH C). Each prior iteration carried the mandated slot-revert as a system-level carry-forward.
- ADD per-symbol drawdown brake (primitive 11): the ONE-variable axis change under test.

## PATH E Inclusion Check

PASS — Section 8 contains a dedicated PATH E (CPCV-INVARIANT NULL) subsection with ALL required fields per Critic /053 recommendation #3:
- CPCV positive-path count = 29 (integer match threshold)
- CPCV median path Sharpe = +0.3351 ± 0.0050
- CPCV Q25 path Sharpe = -0.243 ± 0.0050
- drawdown_brake_fires ≥ 5 (mechanism must have fired — not a no-op explanation)
- Outcome: axis family CLOSED at /054 if PATH E fires alongside any non-PATH-D path

## ORACLE Counterfactual Reproducibility

PASS — per_symbol_drawdown_brake_eda.py at SHA e565b82 operates on /053 trade roster (in_sample/trades.csv + out_of_sample/trades.csv). The ORACLE produces 7 fires (2 BCH IS + 5 LDO OOS) at T=10.0, recovery=5.0, window=30 days. Tables in Section 2 show exact trade-by-trade brake state for LDO OOS trades 1-11+ with cumulative wpnl, dd_30d, and action (TAKEN/SKIPPED). The brake-recommended-counterfactual.csv is the reproducible artifact. Caveat: real backtest Optuna trajectory will differ from ORACLE; brief acknowledges 30-50% deviation range.

## State Machine Spec Precision

PASS — Sections 3.2-3.4 provide unambiguous implementation specification:
- State: _brake_timeline[sym]: deque of (close_time_ms, cum_wpnl); _brake_running_peak[sym]: float; _brake_cum_wpnl[sym]: float; _brake_on[sym]: bool
- Update trigger: update_on_closed_trade(trade) — called after each closed trade via existing record_trade_result hook in backtest.py (line 254: `if hasattr(strategy, "record_trade_result")`)
- Rolling window expiry: cutoff = close_time - window_days*24*60*60*1000; popleft() while deque[0][0] < cutoff
- Peak update: max(c for _, c in deque)
- State machine: engage if dd_30d >= threshold AND brake was off; disengage if dd_30d <= recovery AND brake was on
- Signal kill: return NO_SIGNAL when _brake_on[sym] == True; GateStats.drawdown_brake_fires += 1
- Order of operations: AFTER inner strategy inference (parallel to primitive 10 placement in RiskV3Wrapper.get_signal) — signal must be non-zero before brake fires counter increments

## Adversarial Test Count

PASS — Section 3.7 specifies 5 NEW adversarial tests in tests/strategies/ml/test_risk_v2_drawdown_brake.py:
1. brake_disabled_by_default_is_no_op (backward compat)
2. brake_engages_at_threshold_per_symbol (LDO synthetic sequence)
3. brake_disengages_at_recovery_threshold (recovery trade taken)
4. brake_independent_across_symbols (LDO brake doesn't affect BCH/TRX)
5. brake_respects_30_day_window (expired trades excluded from peak)

27+ total adversarial tests: 5 new (primitive 11) + 5 hurst_drift_50_200 (retained dead code) + 5 fracdiff_d05_close (retained dead code) + 5 regime_momentum_signed_3d (retained dead code) + 7 prior v3 gate tests ≥ 27. PASS.

## Order of Operations Clarification

The brief specifies (Section 3.3): "ADD before the inner-strategy call (or in the gate-cascade — whichever matches the existing primitive 10 placement)". Section 10.5 + RiskV3Wrapper.get_signal precedent shows primitive 10 is applied AFTER inner inference. Per the brief caveat in Section 3.3: "the QE will implement this in Phase 6 and report the callback wiring in the engineering report." The Engineer places primitive 11 AFTER inner inference, consistent with primitive 10 placement in risk_v3.py (super().get_signal() → check direction-block → check drawdown-brake). This is correct: the brake counts a "fire" only when the inner model generated a non-zero signal that was then suppressed.

## Reasons (if BLOCK)

N/A — OVERALL=PASS.
