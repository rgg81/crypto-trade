# BASELINE_V1_BTCUSDT

**Baseline = iter-v1/020 (CONFIRMATION, K=20) — MERGED 2026-06-17.** First both-positive baseline of
the single-symbol redesign. Replaces the iter-001 bootstrap (IS −0.28 / OOS +0.64 — an INVERSION).
Merged under the user-resolved merge gate (2026-06-17): **generalization first — (1) both-positive
(IS>0 AND OOS>0), (2) then OOS; never chase/overfit OOS.** iter-020 is the first model that is
positive in BOTH windows; the inverted iter-001 was not, so iter-020 wins on metric (1).

## Headline (net of fees + slippage)

| metric | in-sample | out-of-sample |
|---|---|---|
| **monthly Sharpe** | **+0.3656** | **+0.0944** |
| Sortino | +0.2349 | +0.0602 |
| max drawdown | 15.04% | 4.12% |
| win rate | 27.4% | 31.6% |
| profit factor | 1.3144 | 1.0510 |
| total trades | 73 | 38 |
| total net PnL (weighted) | +15.92 | +0.65 |
| OOS/IS Sharpe ratio | — | +0.26 (coherent, both-positive) |

- **K=20 bagging:** 20/20 seeds, dispersion mean 43.15. **Lottery-solved:** the both-positive HELD
  K=5→K=20 (iter-019 K=5 +0.54/+0.06 → iter-020 K=20 +0.37/+0.09) — did NOT collapse like the earlier
  iter-016 timing-lottery (K=5 +0.11 → K=20 −1.15). The deterministic trend-state direction + the
  IS-calibrated conviction gate stabilized the seed dispersion.

## Honest read (first generalizing baseline — but the OOS is THIN; strengthen it next, don't overfit it)
- **Both-positive + IS-calibrated:** IS +0.37 AND OOS +0.09, every threshold IS-calibrated (OOS never
  tuned). This GENERALIZES in sign — the model is positive in both regimes — unlike the inverted
  iter-001 (whose +0.64 OOS sat on a losing IS = a regime artifact, not a generalizing edge).
- **CAVEAT (load-bearing, recorded honestly):** the OOS edge is MARGINAL and CONCENTRATED — Sharpe
  +0.09 on 38 OOS trades (~2.5/mo), with ~+6.3 of the +13.7 OOS net carried by 2 timeout-short months
  (2025-11, 2026-02). PSR(OOS) 0.18, PF(OOS) 1.05 — near breakeven. The OOS is "positive but thin,"
  not a strong robust edge. This is acceptable under the gate (both-positive first; don't overfit OOS),
  but the NEXT iteration's job is to THICKEN/robustify the OOS edge (more trades, less concentration)
  WITHOUT overfitting OOS — not to chase a bigger OOS number.
- The IS edge is the strongest of the campaign (+0.37, the conviction gate removed net-negative
  weak-trend chop). The IS-stable direction is LONG; OOS-short profits are a correction-regime artifact
  (do NOT build a short-only book — that's an OOS curve-fit; the IS short leg loses).

## Exact config (the rule, frozen — iter-v1/020)
- **Model = specialist bagging, K=20** independent Optuna studies/month → mean-of-signed-weights.
  Inner ensemble = 1, outer seeds = 1 (both fixed). n_trials = 35/seed. bounds_profile `v1_specialist`.
- **Features:** 19-col HYBRID short+regime set (`V1_BTC_ITER009_FEATURES`) — NOT the full 193.
- **Label:** `fixed_horizon` N=42 candles (14d), `use_atr_labeling=False` (sign of 14d-forward return).
- **Execution ("let winners run, cut losers"):** `atr_tp=100.0` (TP NON-BINDING → 14d timeout binds),
  `atr_sl=1.45` (protective stop), execution_timeout = 14d.
- **Direction (the breakthrough):** stateless 200-SMA **trend-state override** —
  `+1 if close[t−1] > SMA200[t−1] else −1`, past-only (`enable_trend_state_dir=True`,
  `trend_state_sma_window=200`). The model supplies timing/confidence/sizing; the trend-state supplies
  the executed direction (a parameter-free rule that cannot overfit).
- **Conviction gate:** trade only when `|close[t−1]−SMA200[t−1]| / ATR14[t−1] ≥ q=0.40` of the
  past-only (training-window) distribution (`enable_trend_strength_gate=True`,
  `trend_strength_atr_window=14`, `trend_strength_quantile=0.40`). Skips weak-trend chop.
- **Risk:** R1=OFF, R2 drawdown brake ON (trigger 2.07 / anchor 8.28 / floor 0.20 — cut OOS DD ~80%),
  R3=ON (cutoff 0.70), R5=ON (vt_target_vol 0.3). TREND-SCALE de-lever OFF (failed at iter-012).
- **Costs:** fee 0.1% round-trip + slippage 2.0 bps/side. `OOS_CUTOFF=2025-03-24`, `training_months=24`,
  embargo law intact. Look-ahead tests: `tests/test_trend_state_lookahead.py` +
  `tests/test_trend_strength_lookahead.py` (both pass; past-only verified).
- Reports: `reports-v1/BTCUSDT/iteration_v1-020/`. Run:
  `run_baseline_v1.py --confirmation --iteration 20 --symbols BTCUSDT --n-trials 35 --slippage-bps 2`.

## Merge gate (RESOLVED 2026-06-17 by user — supersedes the old "OOS improves" text)
**Generalization-first, no OOS overfit.** A candidate MERGES iff:
1. **(PRIMARY) Both-positive:** IS Sharpe > 0 AND OOS Sharpe > 0 (the model generalizes across regimes).
   A coherent both-positive beats a sign-inverted candidate regardless of raw OOS magnitude.
2. **(SECONDARY) Then OOS:** among both-positive candidates, prefer the better OOS — BUT never chase or
   overfit OOS (no OOS tuning; OOS magnitude is not pursued at the expense of generalization).
3. **No material IS regression** vs this baseline (IS +0.37), and K=20-confirmed (not a K=5 lottery).
4. **OOS-concentration falsifier (Critic-added):** no ≤2 OOS trades / single month may supply >~40% of
   OOS net (guards against reading lucky concentrated trades as an edge). iter-020 itself is at the edge
   of this (2 trades ≈ 46%) — flagged; strengthen next.
No absolute Sharpe floor. EXPLORATION (K=5) screens ideas; CONFIRMATION (K=20) decides the merge.

## Next
Strengthen the OOS edge — thicker, less concentrated, more robust generalization — WITHOUT overfitting
OOS. Candidate axes (IS-calibrated): crypto-native exogenous regime features (funding / realized-vol
state) to make the trend-state entries systematically better-timed; OR the FE's non-directional
volatility-MAGNITUDE target (iter-014: the |move| signal is sub-period-stable). Then extend the
trend-state + conviction-gate stack to the other coins (user: "we will work with the others soon").
