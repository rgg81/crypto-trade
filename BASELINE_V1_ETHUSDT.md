# BASELINE_V1_ETHUSDT

**Baseline = iter-v1/027 (CONFIRMATION, K=20) — MERGED 2026-06-18** (Critic OVERALL=MERGE). First
both-positive ETH baseline; replaces the iter-025 vanilla bootstrap (IS −0.48 / OOS −0.96, both
negative). Validates that the BTC iter-020 deterministic stack is a **portable template** — applied to
ETH (with ETH's own trend + ETH-calibrated R2) it produced a both-positive, K=20-confirmed result.

## Headline (net of fees + slippage)

| metric | in-sample | out-of-sample |
|---|---|---|
| **monthly Sharpe (weighted series)** | **+0.6336** | **+0.0560** |
| Sortino | +0.5207 | +0.0353 |
| max drawdown | 23.79% | 19.08% |
| win rate | 34.1% | 28.1% |
| profit factor | 1.7884 | 1.0343 |
| total trades | 82 | 32 |
| weighted net PnL | +58.54 | +1.50 |
| (unweighted Σ net_pnl_pct) | +100.8% | +12.0% |

Both-positive (IS +0.63 AND OOS +0.06), K=20-confirmed, 20/20 bagging studies. vs the both-negative
iter-025 bootstrap → wins decisively on the PRIMARY (both-positive) metric.

## Honest read + CAVEATS (Critic-recorded — load-bearing)
1. **Thin, magnitude-fragile OOS.** OOS Sharpe +0.056 is barely positive; the iter-026 K=5 screen's
   +0.97 did NOT confirm at K=20 (regressed to +0.06 — the strong K=5 number was a sizing/conviction
   lottery). Anchor future ETH expectations to **~+0.06**, NOT +0.97. The both-positive SIGN is the
   durable claim; the magnitude is not. (The direction is deterministic → sign held; sizing collapsed.)
2. **OOS-concentration falsifier literally fails.** Top single OOS trade ≈ 1223% of weighted net; top-2
   ≈ 438% (unweighted); 9/32 winners (28% WR). Intrinsic to the low-WR let-winners-run trend design
   (same shape as merged BTC iter-020) — recorded as a known structural property, NOT a blocker under
   the generalization-first gate. Implication: OOS is one-or-two-trade-dependent; a single big trade's
   absence flips OOS negative. (Positive PnL IS spread across 6 OOS months, so not a single-month spike.)
3. **Headline units:** +100.8%/+12.0% are UNWEIGHTED Σ net_pnl_pct; weighted net is IS +58.54 / OOS
   +1.50. The gate-relevant Sharpe (+0.63/+0.06) is on the weighted series. Use the same basis in
   future comparisons.
4. **Basin diagnostic vacuous here:** cross_seed_sharpe_std=0.0 is at outer-seeds=1 (K=20 = bagging
   studies, NOT random outer seeds) — do NOT cite it as cross-seed robustness. A genuine multi-outer-seed
   validation is an outstanding check (next-steps #3).

## Exact config (the rule, frozen — iter-v1/027 = the proven BTC iter-020 stack on ETH)
- **Model = specialist bagging, K=20.** Inner ensemble=1, outer seeds=1. n_trials=35/seed. bounds `v1_specialist`.
- **Features:** 19-col HYBRID short+regime set (`V1_BTC_ITER009_FEATURES`).
- **Label:** `fixed_horizon` N=42 candles (14d), `use_atr_labeling=False`.
- **Execution (let winners run, cut losers):** `atr_tp=100.0` (TP NON-BINDING → 14d timeout binds),
  `atr_sl=1.45`, exec timeout 14d.
- **Direction:** stateless 200-SMA **trend-state override on ETH's OWN close** (`enable_trend_state_dir`,
  `trend_state_sma_window=200`, `trend_state_symbol=ETHUSDT`) — parameter-free, can't overfit.
- **Conviction gate:** `|close[t−1]−SMA200[t−1]|/ATR14[t−1] ≥ q=0.40` (past-only training-window quantile,
  self-calibrating per coin).
- **Risk:** R2 drawdown brake ON — **ETH-calibrated** (trigger 4.07 / anchor 16.27 / floor 0.20 = RE
  relative shape 6.5%/26% on iter-026's IS maxDD 62.60; cut IS DD 62.6%→23.8%). R3=ON (0.70), R5=ON
  (vt 0.3). R1 OFF. TREND-SCALE OFF, funding-readmit OFF (BTC-rejected axes).
- **Costs:** fee 0.1% + slippage 2.0 bps/side. `OOS_CUTOFF=2025-03-24`, `training_months=24`, embargo
  intact. Look-ahead tests pass (trend-state + conviction-gate). Features regenerated 2026-06-17 to
  klines 2026-06-15. Reports: `reports-v1/ETHUSDT/iteration_v1-027/`. Run:
  `run_baseline_v1.py --confirmation --iteration 27 --symbols ETHUSDT --n-trials 35 --slippage-bps 2`.

## Merge gate (resolved 2026-06-17 — GENERALIZATION-FIRST, all coins)
(1) PRIMARY both-positive (IS>0 AND OOS>0); (2) then OOS, never chased/overfit; (3) no material IS
regression + K=20-confirmed; (4) OOS-concentration falsifier (no ≤2 trades/month >~40% of OOS net —
intrinsic-design exception per the BTC iter-020 precedent). No absolute Sharpe floor.

## Next (Critic next-steps)
1. **Widen the OOS base, don't chase magnitude:** a labeling/exit tweak (partial-take or 2nd let-winners
   band) to raise OOS trade count + trim single-trade dominance, holding the both-positive sign.
2. **Direction-robustness K=5 screen:** swap `trend_state_symbol`→BTC (cross-asset regime) or SMA
   window 100/300 — test the one deterministic primitive the edge rests on.
3. **Genuine multi-outer-seed validation** of this exact config (the basin diagnostic is vacuous at
   outer-seeds=1).
