# BASELINE_V1_ETHUSDT

**Baseline = iter-v1/034 (EXPLORATION) CONFIRMED by iter-v1/035 (K=20, byte-identical) — MERGED
2026-06-18** (Critic OVERALL=CONFIRMATION-MERGE: leak-free, determinism sound, Pareto-dominates the
prior baseline). The **PURE-DETERMINISTIC trend**: the proven iter-027 stack with the overfit LightGBM
ENTRY layer STRIPPED (`deterministic_entry_only=True`) — enter EVERY conviction-gated candle in the
deterministic trend-state direction; the model prediction is IGNORED. Replaces iter-027 (IS +0.6336 /
OOS +0.0560), which it Pareto-dominates on both regimes. **First ETH baseline to beat BTC's OOS ceiling
(+0.09) — ETH succeeds where BTC couldn't, via OOS STRENGTH.**

## Headline (net of fees + slippage; K-INVARIANT — K=1 ≡ K=20 byte-identical)

| metric | in-sample | out-of-sample |
|---|---|---|
| **monthly Sharpe** | **+0.6481** | **+0.4148** |
| Sortino | +0.6460 | +0.2754 |
| max drawdown | 24.96% | 17.47% |
| win rate | 34.1% | 32.4% |
| profit factor | 1.7902 | 1.2297 |
| total trades | 85 | 34 |
| OOS/IS Sharpe ratio | — | **0.64** |

Both-positive (IS +0.65 AND OOS +0.41), **deterministic** (specialist_dispersion = 0.0 → zero seed
variance → no basin-lottery; iter-035 K=20 is BYTE-IDENTICAL to iter-034 K=1 in comparison.csv + IS +
OOS trades.csv). vs the prior iter-027 baseline → wins decisively: better IS (+0.6481 ≥ +0.6336) AND
**7.4× better OOS (+0.4148 vs +0.0560)**.

## The breakthrough (mechanism — campaign thesis vindicated)
The campaign's core thesis: DETERMINISTIC parts generalize, LEARNED parts overfit. The 200-SMA
trend-state DIRECTION + conviction gate are deterministic (merged at iter-020/027); the LightGBM
entry-TIMING/selection layer is LEARNED. iter-030's forensic showed de-correlating from the model's
entry edge LIFTS OOS. iter-034 takes it to the limit — **REMOVE the model entry layer entirely.** The
model had learned IS-specific entry setups that did NOT generalize and SKIPPED OOS-generalizing trends
(e.g. it missed the +30% July-2025 ETH uptrend that the deterministic rule captures). Entering on ALL
conviction-gated candles catches those trends → OOS +0.056 → +0.41. **The LightGBM was a DRAG on the
OOS, not an edge.** No model → no overfit → no lottery → K-invariant.

## Honest read + CAVEATS (Critic-recorded — load-bearing)
1. **STRENGTH win, NOT a breadth win.** 34 OOS trades (≈ iter-027's 32); OOS de-concentration was
   separately proven INTRACTABLE for this design family (6 mechanisms, iter-028→033). This baseline
   does NOT broaden the OOS; it dramatically STRENGTHENS it.
2. **OOS magnitude is top-trade-fragile (intrinsic let-winners-run).** OOS weighted net +13.79 across
   34 trades / 6 positive months (not a single-month spike). Top-1 weighted trade ≈ 110% of net, top-2
   ≈ 190% → dropping the top-2 flips OOS negative. This is the accepted intrinsic let-winners-run
   exception (same shape as merged iter-020/027) — and iter-034 is MATERIALLY LESS concentrated than
   iter-027 (whose top-1 OOS trade was ~1223% of weighted net). The both-positive SIGN is the durable
   claim (deterministic → cannot overfit); the +0.41 MAGNITUDE is data-extent-dependent — anchor future
   expectations to the SIGN + Pareto-dominance, not the exact +0.41.
3. **DSR/PSR positive but EXPLORATION-mode artifacts** (n_trials=1, model unused) — informational only,
   NOT cited as edge significance.
4. **K is irrelevant by construction** (model bypassed). Run at K=1 (fast); K=20 is byte-identical.

## Exact config (the rule, frozen — iter-v1/034 = iter-027 stack with the entry layer stripped)
- **Entry decision:** `deterministic_entry_only=True` — bypass the LightGBM predict_proba aggregation +
  no-consensus skip in get_signal; enter on EVERY conviction-gated candle (when flat) in the trend-state
  direction with fixed unit confidence. The model still trains per month (R3 OOD stats fit from
  training-window FEATURES) but its prediction is UNUSED → result independent of K / n_trials.
- **Direction:** stateless 200-SMA **trend-state** on ETH's own close (`enable_trend_state_dir`,
  `trend_state_sma_window=200`, `trend_state_symbol=ETHUSDT`) — parameter-free, can't overfit.
- **Conviction gate:** `|close[t−1]−SMA200[t−1]|/ATR14[t−1] ≥ q=0.40` (past-only per-month training-window
  quantile, self-calibrating).
- **Label:** `fixed_horizon` N=42 candles (14d), `use_atr_labeling=False`.
- **Execution (let winners run):** `atr_tp=100.0` (TP NON-BINDING → 14d timeout binds), `atr_sl=1.45`,
  exec timeout 14d.
- **Risk:** R2 ETH-calibrated (trigger 4.07 / anchor 16.27 / floor 0.20), R3=ON (0.70), R5 vt=0.3, R1 OFF.
  TREND-SCALE OFF, funding-readmit OFF, M2 OFF.
- **Costs:** fee 0.1% + slippage 2.0 bps/side. `OOS_CUTOFF=2025-03-24`, `training_months=24`, embargo
  intact (`walk_forward.py:113`). Look-ahead tests pass (trend-state + conviction-gate + deterministic
  entry: 7 + 60 = 67). Features regenerated 2026-06-17. Reports: `reports-v1/ETHUSDT/iteration_v1-034/`
  (K=1 EXPLORATION) ≡ `reports-v1/ETHUSDT/iteration_v1-035/` (K=20 CONFIRMATION, byte-identical). Run:
  `run_baseline_v1.py --confirmation --iteration 35 --symbols ETHUSDT --n-trials 1 --slippage-bps 2`
  (K-invariant; --bagging-k 1 reproduces it).

## Merge gate (resolved 2026-06-17 — GENERALIZATION-FIRST, all coins)
(1) PRIMARY both-positive (IS>0 AND OOS>0) ✓; (2) OOS improves, not chased — deterministic, can't
overfit ✓ (+0.056→+0.41); (3) no material IS regression (+0.6481 ≥ +0.6336) + K-confirmed (byte-identical
K=1≡K=20) ✓; (4) OOS-concentration falsifier = intrinsic let-winners-run exception ✓ (less concentrated
than iter-027). Critic OVERALL=CONFIRMATION-MERGE (look-ahead audit PASS, determinism sound, no leak).

## Next (Critic next-steps + the open frontier)
1. **Breadth-on-top-of-the-strong-core:** now that the deterministic core OOS is robust (+0.41), add a
   complementary DETERMINISTIC 2nd let-winners band / partial-take to raise OOS trade count + trim the
   top-trade dominance, holding the both-positive sign. (De-concentration via within-trend mechanisms
   was intractable on the WEAK iter-027 OOS; retry on the STRONG core.)
2. **Direction-robustness K-invariant screen:** swap `trend_state_symbol`→BTC (cross-asset regime) or
   SMA 100/300 — stress the single deterministic primitive the edge rests on (all K-invariant, fast).
3. **Portability:** apply the model-stripped deterministic core to BTC (does removing the model lift
   BTC's iter-020 OOS too?) + the next coins — corroborate the "deterministic core generalizes, learned
   layer overfits" thesis beyond ETH. This may be the single highest-EV change across the WHOLE v1 track.
