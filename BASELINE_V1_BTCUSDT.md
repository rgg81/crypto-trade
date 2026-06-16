# BASELINE_V1_BTCUSDT

**Bootstrap baseline — established 2026-06-16 by iter-v1/001 (CONFIRMATION).**
First run of the redesigned single-symbol v1 track on BTCUSDT, from scratch, with honest costs.
No predecessor — this run *sets the bar*; future BTC confirmations merge only if they beat it
(relative gate, no absolute Sharpe floor).

## Headline (net of fees + slippage)

| metric | in-sample | out-of-sample |
|---|---|---|
| **monthly Sharpe** | **−0.2793** | **+0.6401** |
| Sortino | −0.2545 | +1.1154 |
| max drawdown | 22.14% | 13.57% |
| win rate | 39.3% | 44.2% |
| profit factor | 0.9156 | 1.1855 |
| total trades | 201 | 95 |
| total net PnL | −12.02 | +9.07 |
| DSR (n_eff=1) | 0.2769 | 0.8106 |
| PSR monthly vs 0 | 0.276 | 0.759 |

- **K=20 bagging dispersion (mean per-candle σ of signed-weights):** 49.46 — HIGH. The 20
  independent Optuna studies disagree substantially per candle ⇒ weak signal consensus on BTC.
- basin_diagnostics: V1=PASS (cross-outer-seed std=0.000, expected — outer seeds=1).

## Honest read (this is a weak baseline, but it's the honest one)
- **IS is NEGATIVE (−0.28), OOS is POSITIVE (+0.64).** The model loses money on the 2023→2025-03
  in-sample window and makes it on the 2025-03→2026-06 out-of-sample window. That inversion +
  the high bagging dispersion say BTC's edge here is thin and regime-dependent, not robust.
- This is fine for a *bootstrap*: it sets BASELINE_V1_BTCUSDT. The Feature Engineer + Risk
  Engineer now have a concrete, honest bar to improve against (lift IS without giving up OOS;
  reduce bagging dispersion = stronger consensus).

## Exact config (the rule, frozen)
- **Model = specialist bagging, K=20** independent Optuna studies/month → mean-of-signed-weights.
  **Inner ensemble = 1, outer seeds = 1** (both fixed). Seeds = `V1_SPECIALIST_SEEDS[:20]` = 42..61.
- **n_trials = 35 per seed** (honored). bounds_profile = `v1_specialist` (max_depth 5, num_leaves 31).
- **training_days**: Optuna-searched (10..500), applied at CV folds AND final per-seed retrain.
  NO full-window training.
- **Features**: full `V1_FEATURE_COLUMNS` (193). **Risk**: R1=OFF, R2=OFF, R3=ON (aggregator-level,
  cutoff 0.70), R5=ON (vt_target_vol 0.3). **ATR** TP 2.9 / SL 1.45.
- **Costs**: fee 0.1% round-trip + slippage 2.0 bps/side (0.04% round-trip). `OOS_CUTOFF=2025-03-24`,
  `training_months=24`, embargo law intact.
- Reports: `reports-v1/BTCUSDT/iteration_v1-001/` (IS + OOS + comparison.csv + specialist_dispersion.csv).
- Run: `run_baseline_v1.py --confirmation --iteration 001 --symbols BTCUSDT --n-trials 35 --slippage-bps 2`.
  Clean completion, 0 seed failures, 0 tracebacks.

## Next
Future BTC iterations (Feature Engineer → Risk Engineer → Quant Research → Engineer → Critic)
run EXPLORATION (K=3) to screen ideas, then CONFIRMATION (K=20) to decide a merge. A candidate
MERGES iff it beats THIS baseline (OOS improves net of costs, no material IS regression, healthy
bagging dispersion) — no absolute Sharpe floor.
