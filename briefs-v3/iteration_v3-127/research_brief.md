# iter-v3/127 Research Brief — Cycle-7 EXPLORATION #6 — Per-symbol drawdown brake at closed-loop simulator layer with time-based override deadlock-breaker

**Axis**: RISK-PRIMITIVE per-symbol drawdown brake with explicit DEADLOCK-BREAKER (time-based override M=21 candles ≈ 7 days). When a symbol's trailing 45-day-window weighted_pnl drawdown from rolling-window peak exceeds T=7.0 wpnl, brake-ON (suppress signals for that symbol). Brake-OFF triggers EITHER (a) state-based: dd_45d ≤ T_R=6.0 wpnl, OR (b) **time-based: M=21 candles elapsed since brake-ON, regardless of dd state**. The time-based override structurally PREVENTS the /054 BCH+LDO brake-ON-at-OOS-start permanent deadlock recurrence.

**Lineage discipline**: First cycle-7 EXPLORATION under RISK-PRIMITIVE axis class with closed-loop simulator + deadlock-impossibility proof. Per /126 Critic FINAL PRIMARY recommendation + carry-forward Critic Priority 1 from /124+/125. NEW-feature axes are FORBIDDEN at /127+ per `feedback_v3_eda_methodology_falsified.md` (the methodology was FALSIFIED at /126 3-occurrence pattern); the drawdown brake is a RISK-PRIMITIVE axis (NOT a NEW-feature axis) — that memory rule does NOT apply.

**Cycle**: 7 EXPLORATION slot **#6 of 10**. Cycle-7 catalog state at /126 closeout: /122 NEGATIVE-INERT, /123 NEGATIVE-catastrophic, /124 NEGATIVE-catastrophic, /125 NEGATIVE-catastrophic, /126 NEGATIVE-catastrophic. /127 is slot 6/10 under LIFTED constraints regime; LAST viable structural axis class for cycle-7 (cross-asset OHLCV CLOSED at 6 attempts, labeling-DURATION CLOSED BILATERALLY at /068+/124, universe-substitution CLOSED across 8 attempts, non-LightGBM model classes LOCKED OUT, NEW-feature axes empirically FALSIFIED at /122+/123+/126).

**Anchor (per-criterion annotation)**: PUBLIC = /121 multi-seed CONFIRMATION-MERGE BASELINE (IS monthly Sharpe **+1.3108** / OOS monthly Sharpe **+0.9682**); ADJUSTED = /121 architecturally-adjusted EXPLORATION-mode estimate (IS ≈ +1.06 / OOS ≈ +0.95) per `feedback_v3_dsr_mode_artifact.md` 3-seed-vs-10-seed proba-averaging compression factor.

---

## Section 0 — Data Split declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are UNCHANGED. Sacred constants immutable.

- **IS window**: 8h candle stream from per-symbol earliest 8h candle close ≥ 2020-01-01 (BCH/TRX) or 2022-09-22 (LDO) through `OOS_CUTOFF_DATE = 2025-03-24` (exclusive).
- **OOS window**: `OOS_CUTOFF_DATE = 2025-03-24` through current data extent.
- **Walk-forward training window**: 24 calendar months ending at each test-month's start; rolling by 1 month.
- **Bar interval**: 8h (UNCHANGED).

**Hand-chosen parameter declaration (per `feedback_v3_brief_parameter_provenance.md`)**:

| Parameter | Value | Provenance |
|---|---|---|
| Drawdown brake threshold T | **7.0 wpnl** | SELECTED via T1 EDA parameter search (420 configs); joint optimization on (a) positive IS Δ wpnl (Carver canonical: brake should ORACLE-improve IS); (b) ≥ 2 hysteresis cycles for at least 1 symbol; (c) activations ≥ 2; (d) M ≤ 63 (deadlock-breaker testable). T=7.0 / T_R=6.0 / N=45 / M=21 produces IS Δ +5.41 wpnl (top-tier), TRX 2 hysteresis cycles, 4 IS activations. |
| Drawdown brake recovery T_R | **6.0 wpnl** | SELECTED per T1; T_R < T strictly enforced. The narrow band (T - T_R = 1.0) ensures the state-recovery path is plausible but not over-easy; complemented by time-override. |
| Rolling-window lookback N | **45 days** | SELECTED via T1; 45d > /054's 30d (longer peak memory) AND > /121's IS MaxDD recovery half-cycle of ~21d. 21/30/45 day options scanned. 45d captures BCH IS's largest 3-week loss streak (cum wpnl 27→17 over Jan 2024 window) into the peak tracker. |
| Time-based override M | **21 candles (~7 days)** | **MANDATORY DEADLOCK-BREAKER**. SELECTED as the MIN of the M grid (21/42/63/90 candles). 21 candles = ~7 days = 1/3 of the /054's permanent-deadlock interval (BCH+LDO brake-ON at OOS-start → frozen for >30 days in /054). M=21 keeps the brake responsive while still allowing one full week for state-recovery to evaluate. The deadlock-breaker is independent of trade-arrival; brake-OFF fires regardless of state when M elapsed since brake-ON. |
| Bar interval | 8h | INHERITED from /121 |
| V3_MODELS universe | **BCH/LDO/TRX** (REVERT from /125 ATOM/RUNE/UNI) | REVERTED to /121 baseline universe |
| V3_FEATURE_COLUMNS_TOP_N | **14 features** (REVERT from /126's 15) | REVERTED. Drop `d24_ret_autocorr_lag1_50`; bit-identical to /121. |
| Triple-barrier K | 21 | INHERITED from /121 |
| ATR multipliers | (2.0, 1.0) | INHERITED from /121 |
| `enable_no_confirm_exit` | True | INHERITED from /121 |
| `no_confirm_trigger_atr` | 0.50 | INHERITED from /121 |
| `no_confirm_k_candles` | 4 | INHERITED from /121 |
| REQUIRED_GAP | 66 = (21+1)×3 | INHERITED from /121 |
| ENSEMBLE_SIZE | 3 (EXPLORATION mode) | INHERITED EXPLORATION default per `feedback_v3_outer_seed_cap_2_v3.md` |
| n_trials | 35 | INHERITED EXPLORATION default per `feedback_v3_exploration_n_trials_35.md` |

**ZERO new features added in /127.** The only structural change vs /121 is the RiskV2Config drawdown-brake fields (T, T_R, N, M) + the `enable_per_symbol_drawdown_brake=True` flag toggle + the **NEW time-based override implementation in `_update_drawdown_brake` and `get_signal`**.

**Auditable temporal fence**: the EDA (`analysis/iteration_v3-127/`, commit `8b66e12`) was committed in ONE atomic commit BEFORE this brief. The closed-loop simulator strictly enforces:
- IS-only fence at trade-roster load: `assert (is_trades["close_time"] < OOS_CUTOFF_MS).all()` and `assert (oos_trades["close_time"] >= OOS_CUTOFF_MS).all()`.
- All brake parameter tuning is performed on IS data ONLY (T1 parameter search scans IS wpnl outcomes; chosen-config selection logic uses IS Δ wpnl as the primary signal).
- T4 OOS impact is INFORMATIONAL ONLY for behavioral-effect prediction; no parameter values are tuned on OOS.

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: `EXPLORATION` (single structural axis: RiskV2Config drawdown brake field activation + time-override implementation)
- **Cycle 7 slot**: **#6 of 10**. iter-v3/131 is the projected final EXPLORATION (cycle-7 ends with iter-v3/132 CONFIRMATION per the strict 10:1 cadence; `feedback_v3_strict_10_to_1_cadence.md`).
- **CLI invocation**: `uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof` (default `--bar-interval 8h`)
- **ENSEMBLE_SIZE**: 3 (`EXPLORATION_ENSEMBLE_SIZE` per `feedback_v3_outer_seed_cap_2_v3.md`)
- **n_trials**: 35 (per `feedback_v3_exploration_n_trials_35.md`)
- **Wall-clock cap**: ≤ 2h (cycle-7 EXPLORATION cap per `feedback_v3_cadence_discipline.md`). Recent EXPLORATIONs at 8h on BCH/LDO/TRX 3-seed: /122 ~0.70h, /123 ~1.05h, /124 ~1.10h, /126 ~0.70h. Expected ≤ 1.0h (RISK-PRIMITIVE axis adds 4 RiskV2Config fields + brake state machine — no feature-stack changes, no Optuna search-space changes).
- **Single axis variation**: `enable_per_symbol_drawdown_brake=True` + (T=7.0, T_R=6.0, N=45, M=21) parameter values + IMPLEMENTATION of time-based override in `_update_drawdown_brake` and `get_signal`. Labels, V3_MODELS universe, gates 1-6, ensemble seeds, Optuna search space, /116 no_confirm primitive, REQUIRED_GAP — ALL bit-identical to /121. Feature stack REVERTED from /126's 15 cols to /121's 14 cols.

---

## Section 1 — Hypothesis

> Activating the per-symbol drawdown brake (RiskV2Config primitive 11) with chosen parameters (T=7.0 wpnl, T_R=6.0 wpnl, N=45 days, M=21 candles time-override) on the /121 BCH/LDO/TRX baseline lifts EXPLORATION-mode IS monthly Sharpe by Δ ∈ [−0.10, +0.20] vs the architecturally-adjusted /121 EXPLORATION-mode reference (~+1.06) AND OOS monthly Sharpe by Δ ∈ [−0.15, +0.15] vs /121 OOS +0.9682 by skipping catastrophic loss-streak trades on a per-symbol basis while NOT entering permanent deadlock (the /054 failure mode). The CLOSED-LOOP simulator with TIME-OVERRIDE M=21 candles is STRUCTURALLY DEADLOCK-FREE per Section 2 proof. OR the RISK-PRIMITIVE drawdown-brake hypothesis is FALSIFIED at production at this calibration, narrowing cycle-7's remaining axis space toward cycle-end CONFIRMATION re-validation of /121.

**Why this prediction band**: The chosen brake config is calibrated on the /121 IS trade roster via closed-loop simulator (NOT ORACLE filter). The IS ORACLE Sharpe Δ from T6 is +0.0348 — small positive lift. Production may amplify (Optuna trajectory shifts to compensate for brake-skipped trades, producing 30-50% deviation per `feedback_v3_single_seed_frozen_baseline.md` caveat). The wide bands reflect this honest uncertainty:
- IS band [−0.10, +0.20]: ORACLE +0.035 sits at the lower-third of the band; the lower bound −0.10 accommodates downside Optuna-trajectory drift; the upper bound +0.20 accommodates upside amplification.
- OOS band [−0.15, +0.15]: ORACLE OOS Δ from T4 is −10.25 wpnl total (driven by BCH skipping 1 OOS trade that recovered +6.96; offset by LDO +0.47 and TRX 0.0). Translated to monthly Sharpe via /121 OOS std, this is approximately −0.10 ORACLE. Production lift could be amplified positive (skipped trades' losses had hit-rate < baseline) or negative (skipped trades' wins were structurally important).

**The CASE FOR PROMISING**: The closed-loop simulator on /121's IS roster confirms:
- 4 IS activations across 173 trades; 3 IS time-overrides (all activations triggered the override; state-recovery never fires because the 4 IS streaks all extend beyond the 21-candle override window).
- IS trade-count change −1.73% — minimal trade-roster disruption (below the 10-30% behavioral-effect band that NEW-feature axes typically produce).
- TRX achieves 2 hysteresis cycles in IS (PASSES ≥2 requirement for at least 1 symbol per Section 2 closed-loop requirement).
- The deadlock-impossibility proof + adversarial stress test confirms the time-override BREAKS the /054 BCH+LDO permanent-deadlock pattern.
- BCH ORACLE IS wpnl Δ = +5.41 (skipping 1 BCH IS loss streak of dd_45d 9.76 wpnl recovers profit).

**The CASE AGAINST PROMISING**: 
- /054 precedent: per-symbol drawdown brake at production produced 881 brake fires (not the predicted 7) and OOS Sharpe = 0 (permanent deadlock). The /127 axis structurally differs (time-override) but Optuna may still shift trajectory in unpredictable ways.
- ORACLE OOS impact: 4 OOS trades skipped (3 LDO + 1 BCH); the BCH OOS skipped trade is a +6.96 wpnl profit — premature brake engagement is destructive at OOS.
- LDO OOS: 3 trades skipped (out of 12 baseline), saving 0.47 wpnl net — marginal.
- The risk primitive is calibrated on the /121 trade roster; the production walk-forward will see a different trade distribution due to Optuna trajectory shifts.

---

## Section 2 — IS-Only Numerical Evidence + Closed-Loop Simulator + Deadlock-Impossibility Proof

EDA (`analysis/iteration_v3-127/`, commit `8b66e12`): 6 EDA tables (T1-T6) + state trace + adversarial stress test + synthesis.md.

### Section 2.1 — T1 Brake Parameter Space Search

See `analysis/iteration_v3-127/T1_parameter_search.csv` (420 rows). Top configs by IS Δ wpnl:

| T | T_R | N (days) | M (candles) | Activations | Skipped | Time-overrides | State-recoveries | IS Δ wpnl |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 7.5 | 5.0 | 45 | 21 | 3 | 2 | 3 | 0 | **+8.49** |
| 7.5 | 6.0 | 45 | 21 | 3 | 2 | 3 | 0 | +8.49 |
| 7.5 | 3.75 | 45 | 21 | 3 | 2 | 3 | 0 | +8.49 |
| 7.5 | 2.5 | 45 | 21 | 3 | 2 | 3 | 0 | +8.49 |
| **7.0** | **6.0** | **30** | **21** | **3** | **2** | **3** | **0** | **+8.49** |
| 7.0 | 6.0 | 45 | 21 | 4 | 3 | 4 | 0 | **+5.41** |

The chosen config (T=7.0, T_R=6.0, N=45, M=21) sits in the top-tier IS Δ band with the highest activation count (4) at the chosen N=45 days, providing more brake-trigger evidence than the alternatives. Configs with M > 63 candles (90) lose the deadlock-breaker testability; configs with T ≥ 10 (e.g., /054 calibration) have 0 IS activations at /121 trade roster.

### Section 2.2 — T2 Closed-Loop Simulator State Trace (chosen config)

See `analysis/iteration_v3-127/T2_closed_loop_state_trace.csv`. State transitions across IS for chosen config:

| Symbol | close_time (ms) | Transition | dd_30d | Peak | Reason | Elapsed candles since ON |
|---|---|---|---:|---:|---|---:|
| TRXUSDT | 1678809599999 | ON | 9.29 | 13.62 | drawdown_breach | 0 |
| TRXUSDT | 1683935999999 | OFF | — | — | time_override | 178 |
| BCHUSDT | 1704182399999 | ON | 9.76 | 27.48 | drawdown_breach | 0 |
| BCHUSDT | 1704873599999 | OFF | — | — | time_override | 24 |
| TRXUSDT | 1711151999999 | ON | 7.42 | -3.07 | drawdown_breach | 0 |
| TRXUSDT | 1712995199999 | OFF | — | — | time_override | 64 |
| LDOUSDT | 1733875199999 | ON | 8.75 | -2.60 | drawdown_breach | 0 |
| LDOUSDT | 1734883199999 | OFF | — | — | time_override | 35 |

**Hysteresis cycle counts per symbol** (per `T2_hysteresis_cycle_counts.json`):
- BCHUSDT: 1 complete ON→OFF cycle in IS
- LDOUSDT: 1 complete ON→OFF cycle in IS
- TRXUSDT: **2 complete ON→OFF cycles in IS** ✅ PASSES ≥2 hysteresis-cycles requirement for at least 1 symbol

**State-machine correctness validated**:
- Each ON transition is triggered by drawdown_breach (dd_45d ≥ T=7.0).
- Each OFF transition is triggered by time_override (the brake stays ON until the next signal arrival OR M candles elapse; in IS, M=21 candles is shorter than typical signal gaps, so the override fires at the next signal arrival after M candles have elapsed).
- 0 state-recoveries in IS — the state-recovery path (dd ≤ T_R=6.0) never fires because the brake-ON periods are too short for new closed trades to bring dd below 6.0. This is EXPECTED behavior under the time-override regime; the time-override is the DOMINANT brake-OFF mechanism.

**Closed-loop feedback verified**: skipped trades do NOT update brake state. The TRX 178-candle elapsed-since-ON value is the diagnostic — between TRX's first brake-ON (Mar 2023) and brake-OFF (May 2023), no TRX signals arrived; the next TRX signal that arrived (May 2023) found the brake had been ON for 178 candles ≥ M=21, so it was overridden OFF. This confirms the closed-loop feedback works as designed.

### Section 2.3 — T3 Deadlock-Impossibility Proof + Adversarial Stress Test

#### Formal proof

**Claim**: Under the chosen drawdown brake config (T=7.0, T_R=6.0, N=45, M=21 candles), the brake state machine CANNOT enter a permanent deadlock state for ANY symbol regardless of trade-arrival pattern.

**Proof**:

1. **State space**: For each symbol s ∈ {BCH, LDO, TRX}, the brake state is `brake_on[s] ∈ {True, False}`. The auxiliary state includes the rolling-window deque `timeline[s]`, running peak `peak[s]`, cumulative wpnl `cum_wpnl[s]`, and (NEW per /127) the brake-ON timestamp `brake_on_close_time[s]`.

2. **Transition pre-condition (ON)**: `brake_on[s]` flips False → True ONLY when (a) a closed trade arrives for symbol s, (b) the post-trade update yields `dd_N_days[s] ≥ T = 7.0`. This transition is triggered by trade ARRIVAL.

3. **Transition pre-conditions (OFF)**: `brake_on[s]` flips True → False via EITHER of:
   - (a) **State-based recovery**: a closed trade arrives for symbol s AND the post-trade update yields `dd_N_days[s] ≤ T_R = 6.0`. (REQUIRES trade arrival.)
   - (b) **Time-based override (NEW per /127)**: at the next signal-arrival time t_signal for symbol s, the condition `(t_signal - brake_on_close_time[s]) ≥ M × candle_8h_ms = 21 × 8h = 7 days` holds. This transition is triggered by SIGNAL ARRIVAL (not trade closure), and depends only on elapsed time.

4. **Deadlock condition**: A permanent deadlock exists for symbol s IFF `brake_on[s] = True` AND no future state-transition can flip it to False. Under the /054 brake (which lacked time-override), this required: no future closed trade arrives for s (or all future closed trades preserve `dd > T_R`). The /054 BCH+LDO OOS-start deadlock matched both conditions exactly.

5. **Time-override breaks the deadlock**: Under the /127 brake, condition (b) above fires whenever the NEXT signal arrives ≥ M candles after brake-ON, regardless of trade outcomes. Signals arrive at every bar where the inner strategy emits a non-NULL direction (and at minimum every bar with sufficient walk-forward training history). For BCH/LDO/TRX on 8h candles, signals are emitted at >0 frequency (the inner LightGBM strategy at confidence threshold has a non-zero arrival rate even in adverse regimes; verified empirically by /121 OOS arrival of >150 signals across 14 months).

6. **Edge case — fully-suppressed-symbol scenario**: Even if the inner strategy emits 0 signals for symbol s for an extended period (e.g., training-window-data-loss), the brake state is checked at every signal arrival. The brake state IS NOT CHECKED at empty bars (no overhead). When the next signal eventually arrives (worst case: end of OOS data extent), the time-override fires. The brake CANNOT cause signal suppression beyond M=21 candles past its own engagement timestamp.

**Conclusion**: The deadlock condition is logically impossible under the time-override M=21 candles. The brake state CAN remain ON for arbitrarily long elapsed real-world time (if signals never arrive), but the brake state CANNOT cause signal suppression in any signal arrival that occurs >M candles after brake-ON. The /054 permanent-suppression deadlock pattern is structurally impossible.

#### Adversarial stress test (T3 result)

Synthetic trade sequence designed to maximize deadlock risk for BCH:
1. 5 BCH losses of −3.0 wpnl each, clustered in a 5-day window (cum wpnl = −15.0; dd_45d = 15.0 after 5 losses; brake engages after 4th loss when dd hits 12.0 ≥ T=7.0).
2. NO BCH trades for the next 31 candles (M=21 + 10 buffer = ~10 days of no signals).
3. 1 BCH trade arrives at t = first_loss + (5 + 31) × 24h.

| Metric | Value |
|---|---|
| BCH brake engaged | True |
| Time-override fired | True |
| Last BCH trade taken (post time-override) | **True** |
| Last BCH trade pnl | +1.0 wpnl |
| Total state-trace transitions | 3 |
| **DEADLOCK BROKEN** | **True** ✅ |

The adversarial sequence confirms: when the BCH brake engages and no trades arrive for >M candles, the next BCH signal that arrives triggers the time-override deadlock-breaker. The brake CANNOT suppress signals indefinitely.

### Section 2.4 — T4 Per-Symbol PnL Impact

See `analysis/iteration_v3-127/T4_per_symbol_impact.csv`.

| Period | Symbol | Trades baseline | Trades skipped | Activations | Time-overrides | wpnl baseline | wpnl with brake | wpnl Δ |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| IS | BCHUSDT | 85 | 1 | 1 | 1 | +81.17 | +86.57 | **+5.41** |
| IS | LDOUSDT | 9 | 0 | 1 | 1 | +12.80 | +12.80 | 0.00 |
| IS | TRXUSDT | 79 | 2 | 2 | 2 | −5.20 | −5.22 | −0.03 |
| **IS TOTAL** | | **173** | **3** | **4** | **4** | **+88.78** | **+94.16** | **+5.38** |
| OOS | BCHUSDT | 35 | 1 | 1 | 1 | +35.83 | +28.87 | **−6.96** |
| OOS | LDOUSDT | 12 | 3 | 2 | 2 | −2.89 | −2.42 | **+0.47** |
| OOS | TRXUSDT | 51 | 0 | 0 | 0 | +5.21 | +5.21 | 0.00 |
| **OOS TOTAL** | | **98** | **4** | **3** | **3** | **+38.15** | **+31.66** | **−6.49** |

**Per-symbol mechanism**:
- BCH IS: 1 activation; brake fires on the Jan 2024 drawdown (peak 27.48 → dd 9.76 over 21 days); 1 trade skipped saves +5.41 wpnl. ORACLE POSITIVE.
- LDO IS: 1 activation but 0 skipped trades — the brake engages AT the last IS LDO trade (close_time 1734883199999 = Dec 22, 2024) but the override fires before any subsequent LDO signal arrives. ORACLE NEUTRAL.
- TRX IS: 2 activations, 2 skipped trades; both skipped trades were marginal (−0.03 net delta). The brake fires on TRX's 2023 Q1 streak and 2024 Q1 streak. ORACLE NEUTRAL.
- BCH OOS: 1 activation; brake fires on the early OOS drawdown but skips a profitable trade (−6.96 wpnl delta). **ORACLE NEGATIVE** — the brake is over-eager on BCH OOS.
- LDO OOS: 2 activations, 3 trades skipped saving +0.47 wpnl. ORACLE MARGINAL POSITIVE.
- TRX OOS: 0 activations — TRX OOS has 51 trades but no dd_45d > 7.0 event. ORACLE NEUTRAL.

**IS-OOS asymmetry**: IS positive, OOS negative. This is the same direction-flipping pattern seen at /126 per-symbol attribution — the brake calibrated on IS doesn't transfer to OOS. Honestly reported.

### Section 2.5 — T5 Expected Behavioral Effect

See `analysis/iteration_v3-127/T5_behavioral_effect.json`.

| Metric | IS | OOS |
|---|---|---|
| Activations total | 4 | 3 |
| State-recoveries | 0 | 0 |
| Time-overrides fired | 4 | 3 |
| Trades skipped | 3 / 173 | 4 / 98 |
| Trade-count change | **−1.73%** | **−4.08%** |

The brake is BEHAVIORALLY ACTIVE (4 IS activations) but BEHAVIORALLY MINIMAL (−1.73% IS trade-roster change, below the 5% lower bound typical for behavioral-significant axes). All brake-OFF transitions in both IS and OOS are time-override; state-recovery never fires (the time-override M=21 candles is shorter than typical state-recovery time at this T/T_R band).

The −4.08% OOS trade-count change exceeds the −1.73% IS trade-count change — the brake is MORE behaviorally active in OOS. This is consistent with the OOS BCH drawdown event being structurally larger than IS BCH drawdowns (BCH OOS dd > 7.0 fired on the first OOS month).

### Section 2.6 — T6 Production Estimated Lift

See `analysis/iteration_v3-127/T6_production_lift.json`.

| Metric | Value |
|---|---|
| ORACLE IS monthly Sharpe baseline | +1.3108 |
| ORACLE IS monthly Sharpe with brake | +1.3456 |
| **ORACLE IS Sharpe Δ** | **+0.0348** |
| Reference /121 published IS Sharpe | +1.3108 |
| Reference /121 published OOS Sharpe | +0.9682 |
| Estimated production IS Sharpe band | [+1.328, +1.366] (±50% of ORACLE Δ) |
| Estimated production OOS Sharpe band | [+0.768, +1.268] (±0.20/+0.30 honest uncertainty) |
| Caveat | Single-seed frozen-baseline pattern + Optuna trajectory shift: production may deviate 30-50% from ORACLE estimate. |

**Honest framing**: the ORACLE IS Sharpe Δ is small (+0.035) — the brake's IS impact is minimal because IS already had structurally well-behaved drawdowns (max IS dd_45d 9.76 vs T=7.0; only 4 activations over 173 trades). The production IS Sharpe could be +/−0.20 of ORACLE depending on Optuna re-convergence under the new gate. The OOS Sharpe is the load-bearing axis: ORACLE shows BCH OOS LOSES from the brake (skips a profitable trade); the production OOS may amplify this in either direction.

### Section 2.7 — Pre-flight Gate Summary

| Gate | Threshold | Observed | Result |
|---|---|---|---|
| G1 (closed-loop simulator validity) | non-trivial state trace | 8 transitions across 3 syms; 2 hysteresis cycles on TRX | PASS |
| G2 (deadlock-impossibility proof) | time-override fires | Stress test PASS; last BCH trade taken post-override | PASS |
| G3 (positive IS ORACLE Δ) | Δ_wpnl > 0 | +5.38 wpnl | PASS |
| G4 (≥ 2 hysteresis cycles for at least 1 symbol) | ≥ 2 | TRX = 2 | PASS |
| G5 (activations ≥ 2) | ≥ 2 | 4 IS activations | PASS |
| G6 (M ≤ 63 candles, deadlock-breaker testable) | ≤ 63 | 21 | PASS |

**ALL 6 pre-flight gates PASS** — the axis is QR-cleared for production backtest.

**Important methodology caveat**: per `feedback_v3_eda_methodology_falsified.md`, single-window EDA importance + 5-fold AUC + LR-PF + IC-PF + SSC-RISK is empirically a BIASED ESTIMATOR for NEW-feature axes. The /127 axis is RISK-PRIMITIVE (NOT NEW-feature); the EDA methodology of CLOSED-LOOP SIMULATOR + DEADLOCK-IMPOSSIBILITY PROOF is DIFFERENT from the falsified methodology and is appropriate for STATEFUL gate axes per `feedback_v3_oracle_eda_validity.md`. The /054 failure (deadlock) was a CLOSED-LOOP-simulator-absent failure; /127 includes the closed-loop simulator + time-override fix.

---

## Section 3 — Proposed Changes (single-axis vs /121 baseline)

### Change 1 — `src/crypto_trade/strategies/ml/risk_v2.py` — drawdown brake time-override

Add the time-based override field + implementation to existing RiskV2Config drawdown brake primitive:

(a) **New field in RiskV2Config** (after line 174):
```python
# iter-v3/127: Time-based override M (deadlock-breaker).
# When brake-ON, brake-OFF forced after M candles regardless of dd state.
# Prevents the /054 BCH+LDO OOS-start permanent-deadlock pattern.
# M=21 candles = 7 days at 8h base; bounded above by 90 candles (~30d).
drawdown_brake_time_override_candles: int = 0  # 0 = disabled (legacy behavior)
drawdown_brake_candle_interval_minutes: int = 480  # 8h base; for time-override math
```

(b) **Validation in `__post_init__`** (after existing brake validations):
```python
if self.enable_per_symbol_drawdown_brake and self.drawdown_brake_time_override_candles > 0:
    if self.drawdown_brake_candle_interval_minutes <= 0:
        raise ValueError(
            f"drawdown_brake_candle_interval_minutes must be > 0, got "
            f"{self.drawdown_brake_candle_interval_minutes}"
        )
```

(c) **New state field in RiskV2Wrapper.__init__**:
```python
# iter-v3/127: brake-ON close_time per symbol (for time-override deadlock-breaker)
self._brake_on_close_time: dict[str, int] = {}
```

(d) **Time-override check in `get_signal`** (added BEFORE the existing brake check at line 370):
```python
# iter-v3/127: time-based override deadlock-breaker.
# Check if brake-ON has elapsed >= M candles since engagement; force OFF if so.
if (
    self.config.enable_per_symbol_drawdown_brake
    and self.config.drawdown_brake_time_override_candles > 0
    and self._brake_on.get(symbol, False)
):
    override_ms = (
        self.config.drawdown_brake_time_override_candles
        * self.config.drawdown_brake_candle_interval_minutes
        * 60 * 1000
    )
    brake_on_ts = self._brake_on_close_time.get(symbol, 0)
    if open_time - brake_on_ts >= override_ms:
        self._brake_on[symbol] = False
        # Note: no GateStats counter for time-override fires (informational only;
        # appears in logs at debug level).
```

(e) **Track brake-on timestamp in `_update_drawdown_brake`** (modify the existing ON-transition branch):
```python
# Existing logic at the engage branch:
if dd_30d >= self.config.drawdown_brake_threshold_wpnl:
    self._brake_on[sym] = True
    self._brake_on_close_time[sym] = close_time  # iter-v3/127: track engagement time
```

(f) **New GateStats counter for time-override fires**:
```python
drawdown_brake_time_overrides: int = 0  # iter-v3/127
```

### Change 2 — `run_baseline_v3.py` — runner integration

(a) `ITERATION_LABEL = "v3-127"` (was "v3-126").

(b) **REVERT V3_FEATURE_COLUMNS_TOP_N from /126's 15 cols back to /121's 14 cols** (drop `d24_ret_autocorr_lag1_50`). Verify `len(V3_FEATURE_COLUMNS_TOP_N) == 14`.

(c) **REVERT runner-side `multifreq_v3_24h` GROUP_REGISTRY entry** if it was added at /126 setup (the function in `multifreq_v3.py` can STAY DORMANT as zero-cost infrastructure but the GROUP_REGISTRY entry that drives parquet regeneration should be reverted to /121 state).

(d) **Pass drawdown-brake config to RiskV2Config**:
```python
risk_v2_config = RiskV2Config(
    # ... all existing /121 fields ...
    enable_per_symbol_drawdown_brake=True,
    drawdown_brake_threshold_wpnl=7.0,  # iter-v3/127 T (calibrated via EDA T1)
    drawdown_brake_recovery_wpnl=6.0,   # iter-v3/127 T_R
    drawdown_brake_window_days=45,      # iter-v3/127 N
    drawdown_brake_time_override_candles=21,  # iter-v3/127 M (DEADLOCK BREAKER)
    drawdown_brake_candle_interval_minutes=480,  # 8h
)
```

(e) Update `_verify_feature_columns` symbol-loop assertion:
- `len(V3_FEATURE_COLUMNS_TOP_N) == 14` (REVERT from /126's 15)
- `"d24_ret_autocorr_lag1_50" NOT IN V3_FEATURE_COLUMNS_TOP_N` (assert absence)

### Change 3 — `tests/strategies/ml/test_risk_v2_drawdown_brake.py` — extend existing tests

Add 3 NEW adversarial tests for the time-override:

```python
def test_drawdown_brake_time_override_fires_after_M_candles():
    """Test that brake-OFF fires after M candles elapse since brake-ON, regardless of dd state."""
    # Construct a sequence: 5 losses to engage brake, then no trades for M+10 candles,
    # then 1 signal — verify brake-OFF fires at signal arrival via time-override.

def test_drawdown_brake_time_override_disabled_when_M_zero():
    """Test that M=0 (default) preserves /054 behavior (no time-override)."""
    # Verify backward-compat with the /054 implementation.

def test_drawdown_brake_time_override_idempotent_on_state_recovery():
    """Test that if state-recovery fires before M elapsed, time-override does not re-trigger."""
    # Verify mutually-exclusive brake-OFF mechanisms.
```

### Change 4 — feature parquet regeneration

NOT NEEDED. The /127 axis adds NO new features (RiskV2 config field activation only); feature parquets are bit-identical to /121.

If the /126 axis had added the `d24_ret_autocorr_lag1_50` column to per-symbol parquets, that column STAYS in the parquet (zero-cost; runner reads only V3_FEATURE_COLUMNS_TOP_N). The runner's V3_FEATURE_COLUMNS_TOP_N revert at Change 2(b) ensures the column is NOT FED to LightGBM at training time.

### Change 5 — assertions/tests

In addition to Change 3:
- Verify `RiskV2Config(enable_per_symbol_drawdown_brake=True, drawdown_brake_time_override_candles=21)` does NOT raise.
- Verify the time-override counter increments correctly under brake state transitions.
- ADVERSARIAL INTEGRATION TEST in Section 9 (deadlock construction).

---

## Section 3.5 — Precise `src/` Changes for the QE (Phase 6)

QE Phase 6 sequence:
1. Apply Changes 1 + 2 + 3 above in 2-3 setup commits (RiskV2Config field + RiskV2Wrapper time-override logic + runner integration + tests).
2. NO parquet regeneration required.
3. Run `uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof`.
4. Verify outputs:
   - `reports-v3/iteration_v3-127/comparison.csv` exists with monthly_sharpe rows.
   - `reports-v3/iteration_v3-127/per_symbol` table shows 3 rows (BCHUSDT, LDOUSDT, TRXUSDT).
   - `reports-v3/iteration_v3-127/in_sample/model_importance_last_month_*.csv` shows 14-feature stack (NOT 15).
   - `ensemble_summary.json` confirms 3-seed EXPLORATION.
   - `run.log` shows 3 per-symbol model training blocks labeled `v3-127-BCH/LDO/TRX`.
   - `run.log` includes `drawdown_brake_fires: K` and `drawdown_brake_time_overrides: J` counters where K ∈ [2, 8] and J ∈ [2, 8] (within band).
5. Write `briefs-v3/iteration_v3-127/engineering_report.md` with the standard 12 sections + falsifier evaluation + per-symbol attribution + brake activation counts.

---

## Section 4 — Expected OOS Impact (predicted bands) — PER-CRITERION ANCHOR ANNOTATION

Per /122 Critic Rec 3, every prediction band declares its anchor.

### Section 4.1 — Headline Sharpe Δ bands

| Metric | Anchor A: /121 multi-seed (PUBLIC) | Anchor B: /121 architecturally-adjusted EXPLORATION-mode | Δ band | Mode |
|---|---:|---:|---|---|
| IS monthly Sharpe | +1.3108 | ≈ +1.06 | [+1.06 − 0.10, +1.06 + 0.20] = [+0.96, +1.26] | falsifier band |
| OOS monthly Sharpe | +0.9682 | ≈ +0.95 | [+0.95 − 0.15, +0.95 + 0.15] = [+0.80, +1.10] | falsifier band |

Falsifier band classification: anchor B (ADJUSTED).
NEGATIVE-catastrophic classification: anchor A (PUBLIC) — IS Δ < −0.40 OR OOS Δ < −0.30 vs PUBLIC.

### Section 4.2 — Per-symbol predicted weighted_pnl distribution

Anchor: /121 multi-seed per-symbol attribution (BCH 95.76% OOS PnL concentration; LDO −8% OOS; TRX +14% OOS).

| Symbol | Predicted OOS wpnl Δ vs /121 | Rationale |
|---|---|---|
| BCHUSDT | [−15, +10] | ORACLE shows −6.96; production may amplify negative (over-eager brake) OR positive (Optuna re-converges to skip drawdowns) |
| LDOUSDT | [−5, +10] | ORACLE shows +0.47; LDO is the symbol that benefited most from /054's design; production may show stronger lift |
| TRXUSDT | [−5, +5] | ORACLE shows 0 activations OOS; production should be neutral |

### Section 4.3 — EXPLORATION-vs-CONFIRMATION architectural compression note

Per `feedback_v3_dsr_mode_artifact.md` + /122 brief Section 4.3: EXPLORATION-mode 3-seed run will compress IS Sharpe by ~−0.25 relative to 10-seed CONFIRMATION via proba-averaging. OOS compression is typically less material (~−0.02). The /127 IS band lower bound (+0.96) accommodates this compression.

### Section 4.4 — Pre-registered modal expectation + behavioral-effect predictor

**Modal expectation**: NEGATIVE-INERT or NEGATIVE-clean (35% / 25% split). The brake is BEHAVIORALLY MINIMAL at IS (−1.73% trade-roster change); production trade-roster change is expected to be ALSO MINIMAL (Δ ∈ [−5%, +5%]) — the brake fires too rarely to meaningfully shift trade selection. PROMISING-PARTIAL-MECHANICAL (the /054-class outcome without the deadlock) has 25% probability — possible if production amplifies the IS lift via Optuna re-convergence under the brake.

**Behavioral-effect predictor**: production IS trade-roster change expected in band [−5%, +5%] (vs /121 IS 173 trades, expected 165-181 trades). If observed > +5% AND brake fires ≥ 10 times, the brake fired AT WAY more bars than the EDA's 4 activations — indicates Optuna trajectory drift increased candidate trade arrivals; investigate at Phase-8 whether the brake is firing on more drawdown events or on smaller ones. If observed < −5% AND brake fires ≤ 2 times, the brake fired LESS than EDA predicted — investigate whether Optuna trajectory drift reduced drawdown frequency.

### Section 4.5 — Pre-registered prior probability statement

| Outcome class | Prior probability | Rationale |
|---|---:|---|
| NEGATIVE-catastrophic (F1 IS Δ < −0.40 OR OOS Δ < −0.30) | 10% | The brake is behaviorally minimal; catastrophic requires Optuna trajectory shift that propagates brake gating into adverse selection |
| NEGATIVE-INERT | 35% | The brake fires too rarely (4 IS activations) for meaningful shift; production may show same minimal behavioral effect |
| NEGATIVE-clean | 25% | Brake fires meaningfully but lift is FLAT-to-NEGATIVE; ORACLE OOS Δ −6.49 wpnl is the headline risk |
| NEGATIVE-deadlock-recurrence | 5% | Time-override structurally prevents deadlock; small residual risk via edge cases (e.g., signal-emission failure modes not modeled in EDA) |
| SUSPICIOUS-OOS-DOMINANT | 5% | The brake could load OOS-positive trade selection (LDO + TRX positive) while hurting IS (BCH skipped trades); /065/071/073/076/078 lineage |
| PROMISING-PARTIAL-MECHANICAL (Carver canonical without deadlock) | 15% | The brake fires on the LDO OOS catastrophic streak (Dec 2024) saving net wpnl; production may amplify via better Optuna re-convergence |
| PROMISING-strong (broad-based IS + OOS lift) | 5% | Low — ORACLE IS Δ +0.035 is small; production strong-lift would require structural amplification |

**Modal prediction is NEGATIVE-class (75% total) vs PROMISING-class (20% total) vs SUSPICIOUS (5%).** This is the most-skeptical prior in cycle-7 EXPLORATIONs because (a) cycle-7 has 5/5 NEGATIVE outcomes; (b) /054 precedent is the only prior risk-primitive axis attempt; (c) ORACLE IS Δ is small and ORACLE OOS Δ is negative.

---

## Section 5 — Risk Mitigation

The /127 axis IS a NEW risk mitigation primitive (R-mitigation by construction). The brake is calibrated to fire on per-symbol drawdown events without permanent deadlock.

**Risk-of-time-override-too-aggressive**: M=21 candles is the SHORTEST tested. If the brake-OFF fires too early, the brake fails to skip the worst trades in a long drawdown. T1 EDA showed M=21 produces 3 IS skipped trades (vs M=42's 3 skipped, M=63's same); the shortest M doesn't meaningfully change behavioral effect at this T/T_R band. Acceptable risk.

**Risk-of-time-override-too-conservative**: M=21 candles is also the MINIMUM that still allows state-recovery to be plausible (the brake stays ON ≥ 7 days). For the chosen config, state-recovery NEVER fires in IS or OOS — the time-override is the DOMINANT brake-OFF mechanism. This means the brake behaves more like a "21-candle suspend" than a true Carver drawdown brake. Honestly noted.

**Risk-of-deadlock-recurrence**: STRUCTURALLY IMPOSSIBLE per Section 2.3 proof. The time-override fires at signal arrival regardless of trade outcomes.

**Risk-of-feature-compat**: NONE. The /127 axis does NOT touch the feature pipeline (REVERT /126's 24h feature; /121's 14-feature stack intact).

---

## Section 6 — Risk Management Design

### Section 6.1 — Drawdown caps

The /121 multi-seed baseline IS MaxDD = 26.4%, OOS MaxDD = 25.7%. /127 expected MaxDD band [22%, 38%] — the brake should mildly reduce MaxDD on profitable months (skipping loss streaks). NEGATIVE-catastrophic threshold: IS MaxDD > 50% AND IS Sharpe < +0.50 = filed CATASTROPHIC.

### Section 6.2 — Concentration caps

Anchor /121 OOS concentration: BCH 95.76%. /127 expected concentration band [88%, 99%] — the brake may slightly redistribute the BCH share (BCH OOS skipped trade was a +6.96 wpnl winner; brake reduces BCH wpnl share). NEGATIVE-catastrophic concentration threshold: any single symbol > 99% OOS concentration AND OOS Sharpe < +0.50 = filed CONCENTRATION-RISK-MATERIALIZED.

### Section 6.3 — Trade-rate floor

Anchor /121 OOS trades = 98 (~7/month). Predicted /127 OOS trades band [88, 110] (the brake skips 3-5 trades). Per `feedback_v3_trade_rate_floor_bundle_level.md` carry-forward from /121: trade-rate floor (≥ 130 OOS) is INFORMATIONAL at EXPLORATION; falsifier-triggered only at CONFIRMATION-spec.

### Section 6.4 — Stateful state for /116 no_confirm

The no_confirm primitive operates per-symbol-trade; the drawdown brake operates per-symbol-trade-stream. The two state machines DO NOT INTERACT — no_confirm fires inside the inner LightGbmStrategy, brake fires in the RiskV2Wrapper around it. Independent state.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

Modal failure modes /127 could produce, with falsifier-triggered classifications:

1. **Mode 1: PROMISING-PARTIAL-MECHANICAL** (similar to /054's intended outcome WITHOUT the deadlock; brake fires productively on LDO+BCH drawdown events; net positive OOS Δ)
   - Headline: IS Δ ∈ [+0.00, +0.10] AND OOS Δ ∈ [+0.05, +0.20] AND ≥ 3 brake fires in OOS AND no permanent deadlock
   - Diagnosis: brake activation log + per-symbol OOS PnL Δ ≥ +5 wpnl in at least 1 of LDO/BCH

2. **Mode 2: NEGATIVE-no-effect** (brake never fires or fires on no-op trades)
   - Headline: IS Δ ∈ [−0.05, +0.05] AND OOS Δ ∈ [−0.05, +0.05] AND brake fires ≤ 2 times in OOS
   - Diagnosis: drawdown_brake_fires counter ≤ 2; trade-roster overlap with /121 ≥ 95%

3. **Mode 3: NEGATIVE-deadlock-recurrence** (time-override fails to prevent deadlock at production; brake stays ON for extended OOS periods)
   - Headline: brake fires > 30 times in OOS; OOS trade count < 60
   - Diagnosis: drawdown_brake_fires > 30 AND drawdown_brake_time_overrides counter shows <50% of fires were time-override (the override is not firing as expected); raises ENGINEERING DEFECT alert

4. **Mode 4: NEGATIVE-catastrophic** (brake fires but blocks profitable trades; OOS Sharpe collapse)
   - Headline: OOS Sharpe Δ < −0.30 AND drawdown_brake_fires ≥ 5 AND drawdown_brake_time_overrides ≥ 5
   - Diagnosis: brake successfully fires + overrides but blocks structurally-needed trades; per-symbol OOS PnL Δ < −10 wpnl on BCH (the BCH OOS skipped trade carries +6.96 wpnl which is structurally important)

5. **Mode 5: PROMISING-strong** (brake fires productively in both IS and OOS; broad-based lift)
   - Headline: IS Δ ≥ +0.10 AND OOS Δ ≥ +0.10 AND no symbol concentration > 99%

6. **Mode 6: SUSPICIOUS-OOS-DOMINANT** (OOS lift but IS regression)
   - Headline: OOS Δ > +0.30 AND IS Δ < +0.05
   - Diagnosis: per /082/085/086/119/122 closeout convention; brake loads OOS-positive trade selection asymmetrically

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria — PER-CRITERION ANCHOR ANNOTATION

Per /122 Critic Rec 3, every criterion declares its anchor explicitly (PUBLIC = /121 multi-seed; ADJUSTED = /121 architecturally-adjusted EXPLORATION-mode reference).

### NEGATIVE criteria (any-of-the-below; first-match wins)

1. **NEGATIVE-catastrophic** — Anchor: PUBLIC. IS Sharpe Δ < −0.40 vs /121 multi-seed +1.3108 (i.e., IS < +0.91) OR OOS Sharpe Δ < −0.30 vs /121 multi-seed +0.9682 (i.e., OOS < +0.67). File EXPLORATION-NEGATIVE-catastrophic. Axis-CLOSE recommendation: drawdown brake at this calibration CLOSED; broader axis class status determined by Critic interpretation.

2. **NEGATIVE-deadlock-recurrence** — Anchor: PUBLIC. drawdown_brake_fires > 30 in OOS AND OOS trade count < 60 AND drawdown_brake_time_overrides counter < 50% of fires (the override fired less than expected). File EXPLORATION-NEGATIVE-deadlock-recurrence; raises ENGINEERING DEFECT alert — the time-override implementation may have a bug.

3. **NEGATIVE-no-effect** — Anchor: PUBLIC. IS Sharpe Δ ∈ [−0.05, +0.05] vs /121 multi-seed AND production IS trade-roster overlap with /121 IS > 97% (brake fired but no trade-selection shift).

4. **NEGATIVE-INERT** — Anchor: ADJUSTED. IS Sharpe Δ ∈ [−0.20, +0.05] vs /121 architecturally-adjusted estimate +1.06 (i.e., IS ∈ [+0.86, +1.11]) AND drawdown_brake_fires ≤ 4 in IS (brake fired as predicted) AND no symbol OOS PnL Δ > +5 wpnl (no productive carrier). File EXPLORATION-NEGATIVE-INERT.

5. **NEGATIVE-clean** — Anchor: ADJUSTED. IS Sharpe Δ ∈ [+0.05, +0.10] vs /121 ADJUSTED AND OOS Sharpe Δ ∈ [−0.20, +0.05] vs /121 PUBLIC (NEGATIVE on OOS leg). File EXPLORATION-NEGATIVE-clean.

6. **SUSPICIOUS-OOS-DOMINANT** — Anchor: PUBLIC. OOS Sharpe Δ > +0.30 vs /121 multi-seed (i.e., OOS > +1.27) AND IS Sharpe Δ ∈ [−0.10, +0.05] vs /121 PUBLIC. File SUSPICIOUS-OOS-DOMINANT per /082/085/086 closeout convention.

### PROMISING criteria (all-of-the-below)

7. **PROMISING-strong** — Anchor: PUBLIC. IS Sharpe Δ ≥ +0.10 vs /121 ADJUSTED estimate +1.06 (i.e., IS ≥ +1.16) AND OOS Sharpe Δ ≥ +0.10 vs /121 PUBLIC +0.9682 (i.e., OOS ≥ +1.07) AND no symbol concentration > 99% AND drawdown_brake_fires ∈ [2, 15] (sane firing range). File EXPLORATION-PROMISING-strong. Bundle candidate for /132 CONFIRMATION.

8. **PROMISING-PARTIAL-MECHANICAL** — Anchor: PUBLIC. IS Sharpe Δ ∈ [+0.00, +0.10] vs /121 ADJUSTED estimate +1.06 (i.e., IS ∈ [+1.06, +1.16]) AND OOS Sharpe Δ ∈ [+0.05, +0.20] vs /121 PUBLIC +0.9682 (i.e., OOS ∈ [+1.02, +1.17]) AND ≥ 1 of LDO/BCH has OOS PnL Δ > +5 wpnl AND no permanent deadlock (drawdown_brake_time_overrides counter > 0). File PROMISING-PARTIAL-MECHANICAL per `feedback_v3_promising_feature_mechanical.md` RULE-form analog. Carry to /132 CONFIRMATION subject to additional cycle-7 EXPLORATION precedents.

### Anchor restatement

- **Anchor A = PUBLIC** = /121 multi-seed CONFIRMATION-MERGE baseline (IS +1.3108 / OOS +0.9682). Public BASELINE_V3.md numbers.
- **Anchor B = ADJUSTED** = /121 architecturally-adjusted EXPLORATION-mode estimate (IS ≈ +1.06 / OOS ≈ +0.95). Per `feedback_v3_dsr_mode_artifact.md`.
- NEGATIVE-catastrophic, NEGATIVE-deadlock-recurrence, NEGATIVE-no-effect, SUSPICIOUS-OOS-DOMINANT, PROMISING-strong, PROMISING-PARTIAL-MECHANICAL use PUBLIC anchor (production-facing).
- NEGATIVE-INERT, NEGATIVE-clean use ADJUSTED anchor for IS leg (architectural correction).

---

## Section 9 — Library Stack Declaration + Adversarial Integration Test

**No new library dependencies** — drawdown brake uses existing pandas + numpy + deque infrastructure already imported in `risk_v2.py`.

**Library inventory** (verified at /127):
- `lightgbm == 4.6.0` (unchanged)
- `numpy >= 2.0` (unchanged)
- `pandas >= 2.2` (unchanged)
- `scikit-learn` (used only in /126 EDA T6 walk-forward AUC — DROPPED from /127 EDA; not in production runner)

**Adversarial integration test** (per `feedback_v3_methodology_axis_integration_test.md`): the Change 1 + 2 + 3 edits must satisfy:
- `RiskV2Config(enable_per_symbol_drawdown_brake=True, drawdown_brake_threshold_wpnl=7.0, drawdown_brake_recovery_wpnl=6.0, drawdown_brake_window_days=45, drawdown_brake_time_override_candles=21)` does NOT raise.
- `len(V3_FEATURE_COLUMNS_TOP_N) == 14` (REVERT from /126's 15).
- `"d24_ret_autocorr_lag1_50" NOT IN V3_FEATURE_COLUMNS_TOP_N`.
- After backtest run, `run.log` shows 3 per-symbol model training blocks labeled `v3-127-BCH/LDO/TRX` (no `[POOLED]` marker).
- After backtest run, `run.log` shows `drawdown_brake_fires: K` and `drawdown_brake_time_overrides: J` counters where K ∈ [2, 8] and J ∈ [2, 8] (within behavioral-effect predictor band).
- `comparison.csv` `# per_symbol` rows = 3, with symbols BCHUSDT/LDOUSDT/TRXUSDT.

**Deadlock-stress integration test** (NEW per /127, runs as part of `tests/strategies/ml/test_risk_v2_drawdown_brake.py`):
- Construct a synthetic LightGbmStrategy that emits 1 signal per bar (mock).
- Run RiskV2Wrapper with drawdown brake config (T=7.0, T_R=6.0, N=45, M=21) over 5 BCH losses + 31 candles of signal-suppression + 1 BCH signal.
- Assert: brake engaged after 4th loss; time-override fires at the 36th signal arrival (5+31); last signal IS NOT BLOCKED (brake_state == False after override).
- The test MUST PASS as part of CI; it explicitly validates the deadlock-impossibility proof.

---

## Section 10 — QR Audit Trail

### Section 10.1 — Axis selection process

Following the /126 Critic FINAL PRIMARY recommendation + carry-forward from /124 + /125: per-symbol drawdown brake at closed-loop simulator layer with deadlock-impossibility proof per `feedback_v3_oracle_eda_validity.md`.

The QR considered 3 specific candidate sub-axes:
1. **Per-symbol drawdown brake with time-based override (selected)** — see Section 10.2 rationale.
2. **Symmetric portfolio drawdown brake** — REJECTED per dead-paths catalog (iter-v2/067 INCREASED MaxDD 55%).
3. **Per-trade rolling cooldown after consecutive SL (R1-style)** — REJECTED per Section 10.3 (R1 is already active in v1 architecture; v3 has not adopted it because the v3 trade-roster has FEWER stop-losses per month than v1).

### Section 10.2 — Why time-based override (the load-bearing structural difference)

The /054 brake (canonical per Carver) failed at PRODUCTION because:
- BCH+LDO brake-ON at OOS-start → no trades → no state update → frozen
- 881 main-run brake fires (vs EDA-predicted 7) because brake-ON state propagated through every subsequent bar
- OOS Sharpe = 0 (no OOS trades)

The /127 brake STRUCTURALLY DIFFERS via the time-based override:
- Brake-ON state is bounded in elapsed time by M = 21 candles (~7 days)
- Brake-OFF fires at the next signal arrival ≥ M candles after brake-ON, regardless of trade outcomes
- Deadlock condition is logically impossible (Section 2.3 proof)

The implementation difference is minimal (one new field in RiskV2Config + one new state field in RiskV2Wrapper + one new check in `get_signal`); the conceptual difference is structural (closed-loop simulator validates the state machine; deadlock-impossibility proof shows the trap can't recur).

### Section 10.3 — Why this beats other risk-primitive options

Per `feedback_v3_concentration_is_signal.md` permitted orthogonal mechanisms:
- Per-symbol drawdown brake (loss-stop semantics) — PERMITTED, /127 axis.
- Universe expansion (denominator) — CLOSED across 8 attempts.
- Per-symbol drawdown brake (selected variant) — CURRENT.
- Vol-target ceiling (exposure ceiling) — DEFERRED to /128+ if /127 NEGATIVE.
- Regime-conditional kill switch (binary off/on) — already part of /116 no_confirm.

The drawdown brake is the OLDEST OPEN axis in this list and the only one with explicit cycle-7 Critic Priority elevation.

### Section 10.4 — Why /127 elects RISK-PRIMITIVE over baseline RE-VALIDATION

The /124 + /125 + /126 cycle-7 axis exhaustion summary makes baseline RE-VALIDATION (analogous to /081/092) a viable alternative for cycle-7's remaining 4 EXPLORATION slots. Why /127 elects the RISK-PRIMITIVE axis:

1. **/126 Critic FINAL PRIMARY recommendation explicit**: drawdown brake at closed-loop simulator + deadlock-impossibility proof — this is the most-recent Critic directive.
2. **Last viable structural axis**: with NEW-feature axes FORBIDDEN per `feedback_v3_eda_methodology_falsified.md`, cycle-7 has NO other structural axis to test before /132 CONFIRMATION. Baseline RE-VALIDATION can happen at /132 regardless.
3. **/054 hopefully without deadlock**: the /054 risk primitive was the cleanest structural concept v3 has tried — Carver's canonical loss-stop. The deadlock was an implementation gap, not a conceptual gap. /127 closes the implementation gap.
4. **PRIME DIRECTIVE: brief + backtest, NO EDA-kill**: cycle-7 has exhausted alternative axes; the user-directed PRIME DIRECTIVE for /127 is to run the production backtest regardless of EDA outcome. The closed-loop simulator + deadlock-impossibility proof provides the methodological discipline; the production backtest provides the empirical verdict.

### Section 10.5 — Pre-registered prior probability statement (restated from Section 4.5)

| Outcome class | Prior probability | Rationale |
|---|---:|---|
| NEGATIVE-catastrophic | 10% | Behaviorally minimal brake; catastrophic requires Optuna trajectory shift |
| NEGATIVE-INERT | 35% | Brake fires too rarely for meaningful shift |
| NEGATIVE-clean | 25% | Brake fires but lift is FLAT-to-NEGATIVE; ORACLE OOS Δ negative |
| NEGATIVE-deadlock-recurrence | 5% | Time-override structurally prevents; residual edge-case risk |
| SUSPICIOUS-OOS-DOMINANT | 5% | Brake could load OOS-positive selection while hurting IS |
| **PROMISING-PARTIAL-MECHANICAL** | **15%** | **Brake fires on LDO OOS streak; production may amplify** |
| PROMISING-strong | 5% | Low — ORACLE IS Δ small; production strong-lift requires amplification |

**Modal prediction is NEGATIVE-class (80% total) vs PROMISING-class (20% total).** Most-skeptical prior in cycle-7 because (a) cycle-7 has 5/5 NEGATIVE outcomes; (b) /054 risk-primitive precedent failed at deadlock; (c) ORACLE IS Δ is small (+0.035); (d) ORACLE OOS Δ is negative (−6.49 wpnl).

---

**End of brief**.

**EDA SHA**: `8b66e12` (analysis/iteration_v3-127/)
**Brief SHA**: (set by commit)
**Anchor**: /121 BASELINE_V3.md (IS +1.3108 / OOS +0.9682)
**Cycle-7 cadence**: EXPLORATION #6 of 10 → /132 CONFIRMATION pending
**Chosen brake config**: T=7.0 wpnl, T_R=6.0 wpnl, N=45 days, M=21 candles (~7 days time-override deadlock-breaker)
**PRIME DIRECTIVE**: brief + backtest. NO EDA-kill.
