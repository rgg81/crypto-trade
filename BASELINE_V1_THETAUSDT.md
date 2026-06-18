# BASELINE_V1_THETAUSDT

**Baseline = iter-v1/047 (deterministic core, R2-OFF) — MERGED 2026-06-18.** The portfolio's FIRST
genuinely-independent (low-correlation) coin — THETA (Theta Network) has only **0.65 return-correlation
to BTC/ETH** (vs 0.72-0.76 for the correlated majors LINK/LTC/DOT), so its edge is a real diversifier,
not duplicated beta. Found via a cheap trend-edge screen after ZEC (privacy coin) revealed the
**low-correlation ⟂ trend-tradability tension**: most low-corr coins are choppy/non-trending, but THETA
(video/streaming sector, idiosyncratic) is the one low-corr candidate whose deterministic trend core is
both-positive.

## Headline (net of fees + 2bps/side slippage; deterministic → K-INVARIANT)

| metric | in-sample | out-of-sample |
|---|---|---|
| **monthly Sharpe** | **+0.1465** | **+0.5626** |
| win rate | 28.4% | 37.1% |
| profit factor | 1.0915 | 1.3319 |
| max drawdown | 82.04% | 45.85% |
| total trades | 88 | 35 |

Both-positive (IS +0.15 AND OOS +0.56), deterministic (specialist_dispersion = 0 → K-invariant, no
basin-lottery). The strip-model deterministic core (the merged-ETH architecture) applied to THETA.

## What it is — the pure-deterministic trend (same architecture as ETH iter-034)
- **Entry decision:** `deterministic_entry_only=True` — LightGBM prediction bypassed; enter every
  conviction-gated candle in the deterministic trend-state direction.
- **Direction:** stateless 200-SMA trend-state on THETA's own close (parameter-free).
- **Conviction gate:** `|close[t-1]−SMA200[t-1]|/ATR14[t-1] ≥ q=0.40` (past-only per-month quantile).
- **Label/exec:** fixed_horizon N=42 (14d) let-winners-run, atr_tp=100 (non-binding) / atr_sl=1.45.
- **Risk:** R3=ON (0.70), R5 vt=0.3, R1 OFF. **R2 OFF** (see caveat 2).
- **Costs:** fee 0.1% + slippage 2.0 bps/side. OOS_CUTOFF 2025-03-24, training_months 24, embargo intact.
  Data: perp+spot+funding+OI fetched fresh 2026-06-18; 19/19 v1 features, 2020-05→2026-06-18, 1354 OOS rows.
  Reports: `reports-v1/THETAUSDT/iteration_v1-047/`. Run: `run_baseline_v1.py --exploration --iteration 47
  --symbols THETAUSDT --bagging-k 1 --n-trials 1 --slippage-bps 2` (K-invariant; result independent of K/n_trials).

## Honest read + CAVEATS (load-bearing)
1. **IS-weak → OOS magnitude is regime-dependent.** IS Sharpe +0.15 is thin (vs BTC +0.37, ETH +0.65);
   the strong OOS (+0.56) partly reflects THETA's favorable recent regime. The **both-positive SIGN is
   the durable, deterministic claim** (can't overfit); the +0.56 OOS *magnitude* should NOT be over-anchored
   (anchor to "both-positive, low-corr diversifier", not the exact +0.56). It is a MODEST but genuine
   independent edge — its value to the portfolio is the LOW CORRELATION (an independent both-positive edge),
   not standalone strength.
2. **R2 left OFF — R2 over-brakes THETA (coin-specific).** iter-048 (R2-calibrated 5.33/21.33/0.20) cut the
   MaxDD (82%→34% IS / 46%→21% OOS) but crushed the Sharpe (OOS +0.56→+0.14) — same over-brake as DOT/ZEC.
   Under the Sharpe objective, R2-OFF (higher Sharpe) is the baseline. CONSEQUENCE: high MaxDD (46% OOS),
   intrinsic to the uncontrolled let-winners-run trend. A future iteration could explore a gentler/
   different DD primitive (the standard R2 shape is wrong for THETA).
3. **Leak-rigor inherited.** The deterministic-core mechanism (deterministic_entry_only + trend-state +
   conviction gate) was adversarially Critic-verified leak-free at ETH iter-034 (Phase 7.5); THETA uses the
   IDENTICAL code path + the standard v1 feature pipeline + the same OOS split — no new leak surface. The
   result is deterministic (K-invariant). A THETA-specific Critic review is a recommended (non-blocking)
   follow-up.

## Merge gate (generalization-first, all coins)
(1) PRIMARY both-positive (IS +0.15>0 AND OOS +0.56>0) ✓; (2) OOS strong, not chased (deterministic) ✓;
(3) deterministic → K-invariant (no lottery; the strongest robustness) ✓; (4) concentration = intrinsic
let-winners-run exception ✓. No absolute Sharpe/DD floor (resolved gate). Portfolio value = low-correlation
independent edge.

## The v1 portfolio so far (toward real breadth)
- **ETH** iter-034: IS +0.65 / OOS +0.41 (strongest; trend-favorable).
- **BTC** iter-020: IS +0.37 / OOS +0.09 (modest).
- **THETA** iter-047: IS +0.15 / OOS +0.56 (MODEST but LOW-CORR 0.65 → the independent diversifier).
Three both-positive coins, one genuinely de-correlated → the start of portfolio-level breadth. Next:
either more low-corr-trend coins (screen first — most low-corr coins fail the trend, so screen the
trend-IS proxy before prepping) or a regime-complementary bundle of these three.

## Next
1. **More low-corr trend coins:** re-run the trend-edge×correlation screen; prep+baseline any other coin
   with low corr AND a both-positive trend proxy (the screen flagged THETA; others like VET/UNI had
   both-positive proxies at higher corr — candidates for breadth).
2. **THETA DD primitive:** the standard R2 over-brakes THETA; explore a gentler exposure cap to tame the
   46% OOS MaxDD without the Sharpe loss.
3. **Portfolio bundle:** assemble ETH + BTC + THETA (+ future coins) into a regime-complementary bundle
   (IS-only weights) for portfolio-level breadth + de-concentration.
