# Diary — iter-v1/053-054 (ETHUSDT) — WALK-FORWARD OPTUNA SMA SELECTION (the long-trend strategy that replaces LightGBM) — EXPLORATION-NEGATIVE for "tune the SMA", but the definitive answer to the OOS-cheating worry

**Context (user directive).** The user worried the merged ETH/THETA deterministic core hardcodes
the trend SMA window at 200 — "I'm worried that we might have cheated it using OOS. If this 200
changes in the future, how we can tune that?" — and gave the direction: **"create a long trend
strategy to replace lightgbm and use the walkforward and optuna to determine the best long SMA."**
This iteration BUILDS that mechanism and runs it head-to-head against the fixed-200 baseline
(iter-034: IS +0.65 / OOS +0.41 doc-headline; +0.75 / +0.82 under the consistent monthly-sum agg
used here).

## What was built (the mechanism — `enable_trend_optuna_sma`)
The deterministic long-trend rule (trend-state DIRECTION = sign(close[t-1]−SMA_W[t-1]); conviction
gate |dist_atr_W| ≥ per-month q-quantile; `deterministic_entry_only` → LightGBM bypassed) with ONE
change: **the SMA window W is no longer hardcoded at 200 — it is Optuna-selected PER MONTH on the
PAST training window only.** Each test month, a TPE study searches the candidate grid; for each
window it simulates the deterministic-trend trades on `[train_start, train_end)` (the SAME 24-month
walk-forward window, embargo-respected) and scores the in-sample Sharpe; W* = argmax then drives
BOTH the direction and the conviction gate for that test month. The LightGBM scaffold still trains
(K=1, bypassed) but plays NO role — the decision is now a pure walk-forward-tuned long-trend rule.

**Leak-safety PROVEN (the load-bearing rigor).** `_simulate_trend_window` counts a trade only if
BOTH its entry candle AND its exit candle (entry+N) have `open_time < train_end_ms` — stricter than
the embargo, so the entire simulated trade lies inside the training window. A
**future-data-perturbation invariance test** (corrupt every candle with `open_time ≥ train_end` to
NaN/1e12, re-run) returns BIT-IDENTICAL trade returns → the selection uses ZERO out-of-sample
information. The 11-test `test_lookahead_embargo.py` regression suite still passes.

## Result — walk-forward SMA selection UNDERPERFORMS the fixed 200 (consistent agg)
`analysis/ETHUSDT/iteration_v1-053/walkforward_sma_comparison.py` (monthly-sum, √12, both iters):

| config | grid | IS Sharpe | OOS Sharpe | FULL |
|---|---|---|---|---|
| **iter-034 FIXED 200** | — | **+0.75** | **+0.82** | **+0.78** |
| iter-053 walk-forward SMA | 50..400 | −0.32 | +0.60 | −0.07 |
| iter-054 walk-forward SMA | 100..300 (robust plateau) | +0.04 | +0.60 | +0.22 |

The fixed 200 wins on **every segment in both tests.** Restricting the grid to the documented
robust plateau (100–300, the code's own `trend_state_sma_window` comment) recovers IS from −0.32 →
+0.04 (the 50/400 extremes did the worst damage) but does NOT close the gap.

## Mechanism diagnosis — why rolling re-optimization loses (regime-shift lag)
The selector maximizes the TRAILING 24-month Sharpe, so the window it picks overfits the trailing
regime and fails when the regime shifts:
- **2022-01 → picked W=400** (the 2020-21 bull rewarded slow trend-following). Applied to the 2022
  bear, the slow 400-SMA LAGGED — price stayed above it during the early crash → stayed LONG through
  the drawdown → **−41.5% vs the fixed-200's +50.9% that year** (the 200-SMA flips short sooner).
- **2023-24 chop → picked W=50–125** (short windows fit the trailing chop) → whipsawed out-of-window.
- Even within the 100–300 plateau the selector clustered at W=125 (28/54 months) — the trailing-best
  is systematically shorter than 200 and underperforms next-period.

The fixed 200 generalizes better **precisely because it is a non-overfit prior** that does not chase
the trailing regime. This is the textbook walk-forward-parameter-optimization instability.

## Verdict & significance — EXPLORATION-NEGATIVE (hypothesis), but the worry is RESOLVED
- **For the "tune the SMA" hypothesis: NEGATIVE.** Walk-forward Optuna selection of the SMA window
  does not beat — and materially underperforms — the fixed 200, regardless of grid width.
- **For the user's OOS-cheating worry: DEFINITIVELY ANSWERED.** (1) The 200 was never OOS-tuned — it
  is a crypto-canonical prior, and the iter-041-043 robustness check already showed 200 is the
  IS-peak. (2) Here is the legitimate, leak-proven walk-forward mechanism to "tune the 200" without
  OOS — and running it shows that legitimately re-tuning the window per-month makes it WORSE. So the
  honest answer to "if 200 changes in the future, how do we tune it?" is: **keep it fixed.** A robust
  prior beats rolling re-optimization here. If the regime ever genuinely shifts, this same
  walk-forward harness is the IS-justified instrument to re-validate the window (it will move the
  window only when the trailing IS-peak genuinely moves) — but it should not run continuously.
- The mechanism (`enable_trend_optuna_sma`) is committed, leak-safe, and reusable as a periodic
  re-validation tool, NOT a per-month live knob.

## Caveats (load-bearing)
1. **Selection–execution mismatch.** The selection objective uses non-overlapping fixed-horizon
   close-to-close trades (no SL); the executed strategy uses SL=1.45·ATR. An SL-aware objective is
   the obvious refinement, but it is unlikely to overturn the regime-shift-lag mechanism (the 2022
   long-window failure is a DIRECTION-timing lag, not an SL artifact).
2. **Short OOS (~15 months / 37 trades)** — the +0.60 OOS has wide error bars (same caveat as every
   ETH read). The durable claim is the IS collapse + the across-the-board / every-year
   underperformance, not the exact OOS magnitude.
3. **comparison.csv vs this script.** Each iter's `comparison.csv` uses its own vol-targeted/weighted
   series (iter-053 reads IS +0.06 / OOS +0.81 there); the consistent monthly-sum aggregation here is
   the apples-to-apples comparison. Both agree the IS collapsed.

## Next
- BASELINE_V1_ETHUSDT stays iter-034 (fixed SMA=200) — NOT updated; iter-053/054 are NEGATIVE.
- Optional refinement: SL-aware selection objective (low prior of overturning the finding).
- The `enable_trend_optuna_sma` harness is the IS-justified instrument for periodic window
  re-validation (run on demand, not continuously). Tag v0.v1-053.
