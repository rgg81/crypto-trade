# iter-v3/127 EDA Synthesis — Per-symbol Drawdown Brake (Closed-Loop Simulator + Deadlock-Impossibility)

## Axis context
- /127 axis: RISK-PRIMITIVE per-symbol drawdown brake at closed-loop simulator layer with time-based override M (deadlock-breaker).
- Universe: BCH/LDO/TRX (REVERT from /125 cohort change; stay on /121 baseline).
- Anchor: /121 BASELINE (IS +1.3108 / OOS +0.9682 multi-seed).
- /126 architecture REVERTED: 14-feature stack (drop d24_ret_autocorr_lag1_50).
- /121 risk gates preserved (7-gate RiskV2 stack + /116 no_confirm).

## Chosen brake configuration
- Threshold T = 7.0 wpnl (engage when dd_45d >= T)
- Recovery T_R = 6.0 wpnl (state-based disengage when dd <= T_R)
- Lookback N = 45 days (rolling window for peak)
- Time-override M = 21 candles (~7.0 days; DEADLOCK BREAKER — brake-OFF after M candles regardless of state)

## Closed-loop simulator findings
- IS activations: 4
- IS state-recoveries: 0
- IS time-override fires: 4
- IS trades skipped: 3 / 173 (-1.73%)
- OOS activations: 3
- OOS state-recoveries: 0
- OOS time-override fires: 3
- OOS trades skipped: 4 / 98 (-4.08%)
- Hysteresis cycles per symbol (≥2 cycles required for at least 1 symbol): {'BCHUSDT': 1, 'LDOUSDT': 1, 'TRXUSDT': 2}

## Deadlock-impossibility proof (T3)
- BCH brake engaged in adversarial test: True
- Time-override fired: True
- Last BCH trade taken (POST time-override): True
- DEADLOCK BROKEN: True

The time-override M=21 candles (7.0 days) BREAKS the deadlock that the /054 brake suffered: BCH+LDO brake-ON at OOS-start cannot recur because brake-OFF triggers either via state-recovery (closed-loop dependent) OR via time-override (state-independent, fires regardless of trade arrivals).

## Per-symbol PnL impact at chosen config
period  symbol  n_trades_baseline  n_trades_skipped  n_trades_with_brake  activations  time_overrides_fired  wpnl_baseline  wpnl_with_brake  wpnl_delta
    IS BCHUSDT                 85                 1                   84            1                     1         81.166           86.572       5.406
    IS LDOUSDT                  9                 0                    9            1                     1         12.796           12.796       0.000
    IS TRXUSDT                 79                 2                   77            2                     2         -5.196           -5.224      -0.028
   OOS BCHUSDT                 35                 1                   34            1                     1         35.832           28.873      -6.958
   OOS LDOUSDT                 12                 3                    9            2                     2         -2.886           -2.416       0.470
   OOS TRXUSDT                 51                 0                   51            0                     0          5.208            5.208       0.000

## Production lift estimate
- ORACLE IS Sharpe Δ: 0.0348
- ORACLE IS baseline Sharpe (monthly aggregated): 1.3108
- ORACLE IS with-brake Sharpe: 1.3456
- Estimated production IS Sharpe band: [1.3282, 1.363]
- Estimated production OOS Sharpe band: [0.7682, 1.2682]
- Caveat: Single-seed frozen-baseline pattern + Optuna trajectory shift: production may deviate 30-50% from ORACLE estimate.

## EDA tables inventory
- T1_parameter_search.csv — parameter space scan (T × T_R × N × M)
- T2_closed_loop_per_trade.csv — per-trade state at chosen config
- T2_closed_loop_state_trace.csv — state transitions (ON/OFF + reason + dd + peak)
- T2_hysteresis_cycle_counts.json — per-symbol complete ON→OFF cycle counts (>=2 for at least 1 symbol = PASS)
- T3_deadlock_stress_test.json — adversarial test confirming time-override breaks deadlock
- T4_per_symbol_impact.csv — per-symbol IS+OOS PnL impact at chosen config
- T5_behavioral_effect.json — brake activations + trade-count change
- T6_production_lift.json — Sharpe-Δ estimate with sample-uniqueness caveat
- chosen_config.json — chosen (T, T_R, N, M) configuration
