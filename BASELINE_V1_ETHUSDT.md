# BASELINE_V1_ETHUSDT

**Bootstrap baseline — established 2026-06-17 by iter-v1/025 (CONFIRMATION, K=20).**
First run of the single-symbol v1 track on ETHUSDT, from scratch, vanilla config (same as the BTC
iter-001 bootstrap), honest costs. No predecessor — this sets the ETH bar; future ETH confirmations
merge only if they beat it under the resolved generalization-first gate (below).

## Headline (net of fees + slippage)

| metric | in-sample | out-of-sample |
|---|---|---|
| **monthly Sharpe** | **−0.4787** | **−0.9589** |
| Sortino | −0.5018 | −1.5126 |
| max drawdown | 50.79% | 26.18% |
| win rate | 40.0% | 35.8% |
| profit factor | 0.8579 | 0.7720 |
| total trades | 215 | 81 |
| total net PnL (weighted) | −28.87 | −16.94 |
| PSR monthly vs 0 | 0.178 | 0.216 |

- **K=20 bagging dispersion:** 47.67 — HIGH (the 20 Optuna studies disagree per candle; weak signal
  consensus, same pattern as BTC's vanilla bootstrap).

## Honest read (a WEAK bootstrap — both windows negative)
- **IS −0.48 AND OOS −0.96 — both NEGATIVE.** The vanilla 193-col / triple-barrier directional
  LightGBM loses money on ETH in both windows (max DD 50.8% IS). Weaker than the BTC iter-001
  bootstrap (which was at least OOS-positive). The vanilla directional approach has no edge on ETH.
- This is fine for a *bootstrap*: it sets the honest ETH bar. The improvement phase is where the work
  happens — and the natural first improvement is the **proven BTC iter-020 stack** (stateless 200-SMA
  trend-state direction + conviction gate + fixed_horizon N=42 let-winners-run + R2/R3/R5), the
  deterministic template that produced BTC's both-positive. ETH's 2025-26 OOS is less
  correction-dominated than BTC's, so the both-positive coherence may get a fairer test.

## Exact config (the rule, frozen — iter-v1/025, VANILLA)
- **Model = specialist bagging, K=20** independent Optuna studies/month → mean-of-signed-weights.
  Inner ensemble = 1, outer seeds = 1 (fixed). n_trials = 35/seed. bounds_profile `v1_specialist`.
- **Features:** full `V1_FEATURE_COLUMNS` (193). **Label:** triple_barrier, `use_atr_labeling=True`,
  ATR TP 2.9 / SL 1.45, timeout 10080min (7d). **Direction:** the model's learned sign (no override).
- **Risk:** R1=OFF, R2=OFF, R3=ON (cutoff 0.70), R5=ON (vt_target_vol 0.3). No trend-state, no
  conviction gate, no funding-readmit (those are the BTC improvement axes — untested on ETH yet).
- **Costs:** fee 0.1% + slippage 2.0 bps/side. `OOS_CUTOFF=2025-03-24`, `training_months=24`, embargo
  law intact. Features regenerated 2026-06-17 to klines extent 2026-06-15 (cross-coin-comparable to BTC).
- Reports: `reports-v1/ETHUSDT/iteration_v1-025/`. Run:
  `run_baseline_v1.py --confirmation --iteration 25 --symbols ETHUSDT --n-trials 35 --slippage-bps 2`.
  Clean completion, 0 seed failures, 0 tracebacks.

## Merge gate (resolved 2026-06-17 — GENERALIZATION-FIRST, applies to all coins)
A candidate MERGES iff:
1. **(PRIMARY) Both-positive:** IS Sharpe > 0 AND OOS Sharpe > 0 (generalizes across regimes). A
   coherent both-positive beats this both-negative bootstrap on the primary metric.
2. **(SECONDARY) Then OOS:** among both-positive candidates, prefer better OOS — never chase/overfit OOS.
3. No material IS regression vs the then-current baseline; K=20-confirmed (not a K=5 lottery).
4. **OOS-concentration falsifier:** no ≤2 OOS trades / single month may supply >~40% of OOS net.
No absolute Sharpe floor. EXPLORATION (K=5) screens; CONFIRMATION (K=20) decides the merge.

## Next
**iter-v1/026 = the proven BTC iter-020 stack applied to ETH** (trend-state dir + conviction gate +
fixed_horizon N=42 let-winners-run + R2/R3/R5), K=5 screen → K=20 confirm. The highest-prior first
improvement, given it produced BTC's both-positive.
