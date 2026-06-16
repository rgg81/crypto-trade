# Research Brief — iter-v1/002 (EXPLORATION, BTCUSDT)

**Mode:** EXPLORATION (specialist bagging **K=3**, inner=1, outer=1, n_trials=35, slippage 2 bps/side).
**Anchor:** `BASELINE_V1_BTCUSDT` (iter-v1/001): IS Sharpe −0.2793 / OOS +0.6401, 201/95 trades,
K=20 bagging dispersion 49.46 (HIGH). Goal: a fast screen of whether the changes below are worth a
K=20 CONFIRMATION. (Exploration NEVER merges; it only flags PROMISING / NEGATIVE.)

## Hypothesis
The raw 193-feature dump is ~86% redundant and drives the high per-candle study disagreement
(dispersion 49.5) and negative IS. **Pruning to a 41-col BTC-specific, low-redundancy, higher-IC
subset** lifts IS Sharpe and lowers dispersion without surrendering OOS — and a single IS-calibrated
**R2 drawdown brake** trims the IS stop-loss bleed (MaxDD 22%→~17.6%) without changing the trade
roster (size-only ⇒ minimal confound of the feature read).

## Changes (vs iter-001 baseline)
1. **PRIMARY — feature set:** `feature_columns` = the 41-col `V1_BTC_PRUNED_ITER002` (FE report;
   strict subset of `V1_FEATURE_COLUMNS`, no feature-generation change). See
   `briefs-v1/BTCUSDT/iteration_v1-002/feature_report.md`.
2. **SUPPORTING — risk:** enable R2 drawdown scaling: `risk_drawdown_scale_enabled=True`,
   `trigger_pct=8.0`, `scale_floor=0.5`, `anchor_pct=18.0`. All other risk = baseline (R1 OFF,
   R5/vt ON, R3 ON cutoff 0.70, ATR 2.9/1.45). See `risk_report.md`. RE rejected R1 + R5-NATR-kill
   on IS evidence. Kelly ≤ 0 ⇒ no sizing-up (max_amount_usd=1000 unchanged).
3. **Unchanged:** seed rule (K=3), training_days Optuna-searched, costs (fee 0.1% + 2bps/side),
   OOS_CUTOFF 2025-03-24, embargo.

## Pre-registered falsifiers
- **Feature (FE):** NEGATIVE if IS Sharpe stays ≤ −0.28 AND K=3 dispersion doesn't drop below ~45.
- **Risk (RE):** R2 effect is directional (lower MaxDD, ~flat trade count); verdict is the backtest,
  not the offline estimate. Slippage cost-stress: R2 MaxDD reduction must persist at slippage {1,2,4}.
- **Attribution caveat:** this screen tests features + R2 JOINTLY. R2 is size-only (roster ~unchanged)
  so the feature read is largely clean, but if PROMISING the CONFIRMATION must include a feature-only
  ablation to attribute the lift.

## Verdict criteria (EXPLORATION screen — not a merge)
PROMISING (→ worth a K=20 confirmation) if: IS Sharpe improves over −0.28 (toward/above 0) AND OOS
does not collapse (stays clearly positive) AND dispersion drops. NEGATIVE otherwise. No absolute
Sharpe floor (relative track). Critic reviews RESULTS only at Phase 7.5.

## Run
`run_baseline_v1.py --exploration --iteration 002 --symbols BTCUSDT --n-trials 35 --slippage-bps 2`
→ `reports-v1/BTCUSDT/iteration_v1-002/`.
