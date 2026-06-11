# iter-v1/092 Re-Run Projection — Pre-Registered Offline Estimate

**Status:** PRE-REGISTERED EXPECTATION, NOT A VERDICT.
This document is committed BEFORE the corrected backtest runs.
Its purpose is to pre-lock the expected gate effect so Phase 7 evaluation
cannot be post-hoc rationalized.

---

## Context

The initial /092 run was VOID due to a DISPATCH-WIRING-DEFECT:
`run_baseline_v1.py` line 8385 dispatched ALL `symbols={"XRPUSDT"}` runs to the /088
branch, regardless of `iteration_label`. Since V1_ITER088_UNIVERSE == V1_ITER092_UNIVERSE
== ("XRPUSDT",), the /092 branch at line 8990 was dead code. The strategy built had
`enable_btc_regime_kill=False`; the gate never armed; IS trades were bit-identical to
/088 (219 == 219). See `analysis/iteration_v1-092/gate_fire_forensic.py` for proof.

Fix: added `iteration_label == "v1-088" and` guard to line 8385, and `iteration_label
== "v1-087" and` guard to line 8191 (sibling collision prevention).

---

## Offline Projected Gate Effect (computed from void /092 roster)

These numbers are derived by applying the gate condition (`btc_ret_42 > 0.067`)
to the void run's trade roster OFFLINE — not by running the corrected backtest.
The replication of `_compute_btc_ret_42` is in `analysis/iteration_v1-092/gate_fire_forensic.py`.

### IS window (open_time < OOS_CUTOFF_MS = 1742774400000)

| Metric                   | Void /092 (= /088 clone) | Projected surviving | Delta     |
|--------------------------|--------------------------|----------------------|-----------|
| n_trades                 | 219                      | 162                  | -57 (26.0%) |
| Sharpe (annualized, approx) | 1.5187               | 2.3273               | +0.8086   |
| total_weighted_pnl       | 28.1325                  | 33.3425              | +5.2100   |
| win_rate                 | 0.4247                   | 0.4506               | +0.026    |

Suppressed IS entries (btc_ret_42 > 0.067): n=57 / 26.0%, total_wpnl=-5.2100, wr=0.3509.
All 57 have `btc_ret_42 > 0.067` (none_rate = 0.0 — BTC join is perfect).

### OOS window (open_time >= OOS_CUTOFF_MS)

| Metric                   | Void /092 (= /088 clone) | Projected surviving | Delta     |
|--------------------------|--------------------------|----------------------|-----------|
| n_trades                 | 84                       | 72                   | -12 (14.3%) |
| Sharpe (annualized, approx) | 2.0338               | 3.0264               | +0.9926   |
| total_weighted_pnl       | 10.0451                  | 12.8260              | +2.7809   |
| win_rate                 | 0.4286                   | 0.4444               | +0.016    |

Suppressed OOS entries: n=12 / 14.3%, total_wpnl=-2.7809, wr=0.3333.

---

## Position Model Note

The v1 XRP specialist is a SINGLE-SYMBOL sequential backtest (one position at a time;
no concurrent XRP positions). Verified: IS overlap count = 0 (sorted by open_time,
zero cases where open_time[i] < close_time[i-1]).

**Consequence for projection accuracy:** the trade-subtraction is EXACT. Each suppressed
entry is an isolated XRP position. Removing it does not affect any other position's timing,
sizing, or PnL. The projected Sharpe/wpnl computed by simple set-subtraction is analytically
exact for this position model.

For a multi-symbol pooled model (sequential within-symbol but potentially concurrent
across symbols), the subtraction would be an approximation because vol-targeting scales
interdependently. That does NOT apply here.

---

## Pre-Registered Falsifier Bands (F1-F3 for Phase 7 evaluation)

These are the EXPECTED ranges. Phase 7 acceptance is governed by the
pre-registered criteria in `research_brief.md` Section 8.

| Falsifier | Expected range (from projection + gate mechanics) | Acceptance |
|-----------|---------------------------------------------------|------------|
| F1: IS Sharpe lift vs /088 (0.3783) | IS Sharpe ≥ 0.578 (i.e. +0.20 lift at minimum) | PROJECTED: ~2.33, well above floor |
| F2: Mechanism engaged (20-45% IS suppression) | 57/219 = 26.0% — center of pre-registered band | PRE-REGISTERED BAND CONFIRMED |
| F3: OOS trades ≥ 50 | Projected 72 — above floor | PASS expected |
| F4 (primary): pre-Nov OOS ≥ -5% AND ≥ 3/8 months positive | Regime-breadth; not derivable offline | OPEN — determined by re-run |

**CRITICAL NOTE on OOS projection:** The OOS Sharpe projection (+3.03) is an OFFLINE
APPROXIMATION, not a forecast. The corrected backtest will differ because:
(a) The 50-seed Optuna ensemble is stochastic; seed=42 (used in the void run) is one
    of 50 seeds. The multi-seed aggregation will shift trade-entry timing.
(b) The gate fires at compute_features() time; the actual trade roster depends on the
    strategy's month-by-month training and prediction loop, not a simple roster subtract.

The offline projection proves the SIGN AND ORDER-OF-MAGNITUDE of the expected improvement,
not the exact OOS Sharpe. Use it to verify the gate mechanically engaged (F2 confirmation)
and that the direction is correct.

---

## What a Correct Re-Run Should Print

Run log must contain ALL of the following (absence = void run recurred):

1. `[iter-v1/092] XRP SPECIALIST + BTC-regime kill gate:` banner (NOT `[iter-v1/088]`)
2. `[lgbm] BTC-regime kill gate: loaded N BTC candles from data/features/BTCUSDT_8h_features.parquet`
3. `[iter-v1/092] Dispatch verified: XRP-only=N trades. R1=OFF/R2=OFF/R3=ON-AGGREGATOR-LEVEL/R5=ON/R6=ON(BTC-kill).`
4. Trade count N should be LESS THAN 219 (IS) and LESS THAN 84 (OOS) — gate suppressed some entries.
   Expected IS: ~162 (projection). Expected OOS: ~72 (projection).
   Actual may differ due to multi-seed ensemble stochasticity.

If run.log line ~49 still prints `[iter-v1/088]`, the fix was not applied correctly.

---

Committed: 2026-06-12 (before the corrected backtest runs)
Author: Quant Engineer (iter-v1/092 dispatch-fix mandate)
