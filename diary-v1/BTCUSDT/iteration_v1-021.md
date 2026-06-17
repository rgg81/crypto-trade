# Diary — iter-v1/021 (BTCUSDT) — EXPLORATION — funding-contra-crowd re-admission — PROMISING (improves baseline; OOS still concentrated)

**Axis:** crypto-native FUNDING-CONTRA-CROWD re-admission on the MERGED iter-020 stack. Re-admit a
conviction-gate-skipped row ONLY when funding OPPOSES the trend-state direction (short-trend+positive
funding = crowded longs → squeeze fuel; long-trend+negative funding = crowded shorts). Direction never
flipped. `funding_rate_zscore_30`, q_f=0.50, past-only. Single-axis vs /020. K=5, n_trials=35.

**Result (vs MERGED baseline iter-020 K=20 IS +0.37 / OOS +0.09, 73/38 tr):**
| | IS Sharpe | OOS Sharpe | ratio | trades (IS/OOS) | OOS DD |
|---|---|---|---|---|---|
| iter-020 (baseline, K=20) | +0.37 | +0.09 | +0.26 | 73/38 | 4.1% |
| **iter-021 (+readmit, K=5)** | **+0.5219** | **+0.2216** | **+0.42** | **93/49** | 3.5% |
WR 25.8%/28.6%. OOS net +24.6%. 5/5 seeds.

**Verdict: PROMISING — improves the baseline on the user's gate (both-positive, higher OOS, more
trades, healthier ratio) — BUT the OOS profit is STILL 1-trade concentrated. K=20 confirmation MANDATORY.**
- **Improves on iter-020 (user gate = both-positive first, then OOS):** both-positive ✓; OOS Sharpe
  +0.09→+0.22 (more than doubled); OOS trades 38→**49** (~3.3/mo, above the floor); ratio +0.26→+0.42.
- **⚠️ OOS-concentration falsifier FAILED:** top-1 OOS trade = **98% of net**, top-2 = 155% (rest cancel),
  only 14/49 winners (sum+ 118.9 / sum− −94.3). The readmit thickened the trade COUNT but did NOT
  de-concentrate the PROFIT — the OOS edge is still ONE big 14d trend-capture. (iter-020 was top-2=231%;
  iter-021 is marginally less concentrated but both fail the ≤2-trades-<40% falsifier.)
- **This concentration appears INTRINSIC to the design:** a low-WR (28%), high-payoff, 14d-hold
  let-winners-run trend-follower inherently makes its money on a few big trend-captures. "Thicker
  trades" is achievable; "de-concentrated profit" may not be without abandoning the let-winners-run
  structure (and shorter holds overfit — iter-009/010). The QR pre-registered this as a possible null.

**Lottery risk — LOWER than iter-016:** the trend-state DIRECTION is deterministic (same all seeds), so
the big OOS winner is TAKEN at every seed (only its sizing varies). Unlike iter-016 (model-direction
seed-lottery that collapsed K=5→K=20), iter-021's K=20 should hold the both-positive direction — the
open question is whether the OOS MAGNITUDE (+0.22) survives the bagged sizing or regresses toward
iter-020's +0.09.

**Next:** iter-v1/022 — **K=20 CONFIRMATION of iter-021**. The backtest is the arbiter (no offline
pre-call despite the concentration concern). If both-positive holds AND OOS ≥ iter-020's +0.09 (i.e.
the readmit genuinely improves the baseline) → candidate MERGE (improved baseline), WITH the honest
concentration caveat surfaced to the user (is a 1-trade-concentrated OOS an acceptable "improvement"?
— the user accepted concentration at iter-020). If OOS regresses to ~iter-020 → no improvement, iter-020
stays. Either way: the concentration is intrinsic to the trend-following design — a genuinely
de-concentrated OOS likely needs a different (non-let-winners-run) edge source.
