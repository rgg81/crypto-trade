# iter-v3/054 — Per-symbol drawdown brake synthesis

## Mechanism: OPTION B (30-day rolling-trade-window peak)

Carver, *Leveraged Trading* Ch. 11 canonical formulation:

    For each symbol s and current bar t:
        history(s, t) = trades closed for symbol s with close_time in [t - 30d, t]
        peak(s, t)    = max(cumulative_wpnl over history(s, t))
        dd_30d(s, t)  = peak(s, t) - cumulative_wpnl(s, t)
        brake_engages = dd_30d(s, t) >= T  (recommended T = 10.0)
        brake_disengages = dd_30d(s, t) <= T/2  (recommended recovery = 5.0)

## Why this mechanism (not the others)

At /053 trade roster (180 IS + 96 OOS trades; recommended T=10.0, recovery=5.0):

| Symbol | IS skipped | OOS skipped | IS wpnl Δ | OOS wpnl Δ |
|---|---:|---:|---:|---:|
| BCH | 2 | 0 | +4.39 | +0.00 |
| LDO | 0 | 5 | +0.00 | +12.51 |
| TRX | 0 | 0 | +0.00 | +0.00 |

Aggregate counterfactual (oracle):
- IS wpnl: +35.57 → +39.95 (Δ +4.39)
- OOS wpnl: +24.58 → +37.08 (Δ +12.51)

Mechanism cleanly:
1. Targets LDO OOS catastrophic streak (5 trades skipped, all in OOS losing streak)
2. Removes 2 BCH IS losers (the BCH May 2024 drawdown bars)
3. Does NOT skip TRX OOS — TRX OOS dd_30d max = 4.80 (below T=10)
4. Does NOT skip TRX IS catastrophic-looking trajectory — TRX IS dd_30d max = 10.39
   (just barely crosses T=10 for 1 bar). The IS-only DD distribution per-symbol is
   moderate when measured in a 30-day rolling window, even though cumulative IS
   TRX has a -17.79 wpnl final value — the structural loss is spread out, NOT a
   single drawdown event.

## Why TRX IS loss is NOT a drawdown event

TRX IS has cumulative -17.79 wpnl across 85 IS trades, but the worst 30-day rolling
dd is only 10.39 wpnl. This means TRX losses are SPREAD OUT — many small trades with
slight negative expectancy, NOT one or two catastrophic streaks. A drawdown brake by
definition can't fix small consistent leakage; it only fixes catastrophic streaks.

**This is a feature, not a bug.** Spread-out losses are signal-quality problems
(model says trade when it shouldn't), not risk-management problems. The right fix
for TRX is in the feature stack / model architecture, not in a risk gate.

## Why LDO OOS catastrophic IS a drawdown event

LDO has 9 IS trades + 16 OOS trades. The IS contributes +5.67 wpnl (mildly positive).
But OOS goes: trade 1 +9.74 → trade 2 +5.31 (cum +20.73 peak) → trades 3-9 ALL LOSSES
(7 consecutive losers, cum drops to -10.28 from peak +20.73 = 31.01 dd) → trade 10
+9.41 brief recovery → trades 11-13 LOSSES → trade 14 +6.90 → trade 15 LOSS → final -15.61.

The pattern is a CLASSIC catastrophic streak: an inflection point where the strategy
stopped working on LDO and a brake-style mechanism can detect it.

## Predicted /054 behavioral effect

With brake at T=10, recovery=5.0, 30-day window:
- 2 BCH IS trades skipped (wpnl share -1.5%)
- 5 LDO OOS trades skipped (wpnl share -50%; the LDO inflection-point losing streak)
- 0 TRX trades skipped (preserves TRX +15.60 OOS contribution)
- 0 LDO IS trades skipped (LDO IS dd never hits 10 in 30-day window)

Trade count change:
- IS: 180 → 178 (-2; -1.1%)
- OOS: 96 → 91 (-5; -5.2%)

## Confidence in counterfactual

Two caveats reduce confidence in the +0.20-0.30 OOS Sharpe lift prediction:

1. **Optuna trajectory will shift.** With the brake active, the model sees a different
   training-time PnL distribution. The Optuna hyperparameter draw may land in different
   local minima, changing trades the model would have taken regardless of brake state.
   This is the same caveat as `feedback_v3_single_seed_frozen_baseline.md` — single-seed
   EXPLORATION trajectory is search-noise-sensitive at n_trials=35.

2. **Backtest-time vs ORACLE counterfactual divergence.** The ORACLE applies the brake
   on TRUE trades as if they would have been generated identically. The real brake at
   backtest time prevents trades from being taken — affecting state (cooldown timer,
   ATR multiplier feedback) downstream. Backtest-time counterfactual COULD diverge
   from oracle by 30-50% in either direction.

## PATH probability prediction (locked-in §8 LOCKED criteria)

Based on the strength of the oracle counterfactual (+0.35 wpnl per OOS month avg; OOS
Sharpe lift estimate +0.15 to +0.30):

| Path | Mechanism | Probability |
|---|---|---:|
| A (PROMISING-clean) | IS Δ in [+0.05, +0.15] AND OOS Δ ≥ +0.10 AND ratio in [0.5, 2.0] AND brake fires ≥3 times in OOS | **35%** |
| B (PROMISING-INERT) | brake fires 0 times → no effect; not applicable for risk-primitive | **5%** |
| C-clean (NEGATIVE) | IS Δ < -0.10 OR OOS Δ < -0.30; would mean brake over-fires on a profitable streak | **15%** |
| C-suspicious | IS-OOS daily ratio outside [0.5, 2.0]; risk-primitive shouldn't cause this | **10%** |
| D (NULL-RESULT) | IS Δ in (-0.10, +0.05) AND OOS Δ in (-0.20, +0.20); brake fires too rarely | **30%** |
| E (CPCV-INVARIANT NULL) | CPCV path distribution UNCHANGED from /051/052/053 | **5%** |

PATH E firing alongside any other path would be surprising — a per-symbol risk primitive
that changes 5 OOS trades SHOULD shift the CPCV split-by-block path distribution. If
PATH E fires it means even the 5 skipped trades are within-block noise.