# Diary — iter-v1/024 (BTCUSDT) — DIAGNOSIS (research-only) — HONEST NULL → CAMPAIGN-CLOSING (BTC OOS exhausted)

**Axis:** deterministic exogenous-stress regime KILL-SWITCH (the last genuinely-different BTC OOS axis).
Turn the trend-state book OFF (flat) in high-stress regimes where direction whipsaws — binary,
deterministic, purely subtractive (can't add seed-varying trades). QR Phase 1/2, IS-only. No backtest.

**Outcome: HONEST NULL. No exogenous-stress regime robustly lifts recent-sub-period stability. The one
promising candidate (high-vol kill) is the iter-011 fragile gate again — caught by the fragility control.**

### IS-only evidence (60 configs: 10 crypto-native stress regimes × 6 thresholds)
- Only RVOL-high-NATR-z showed a threshold plateau (recent3 +0.785). The fragility control KILLED it:
  - **Curve-fit-by-proxy:** dropping the single thin 24-12 slice (21 trades) → lift +0.785 → **+0.005**.
  - **Sign-consistency:** only 5/10 sub-periods improve (coin-flip).
  - **Removes net-WINNERS:** killed-trade Sharpe +1.26 / mean +2.88% > retained +0.94 / +2.27% — the
    let-winners-run upside LIVES in high-vol breakout candles; killing them removes signal, not noise.
  - **Grid-dependent:** recent3 lift +1.32 (4mo) / +0.785 (6mo) / +0.033 (9mo) — not invariant.
  - **Grid-free last-IS-year (cleanest OOS-proxy):** kill is WORSE (incumbent +0.455 → kill +0.314).
- All other regimes (funding-stress, OI-unwind, range-spike) NO-LIFT or knife-edge.

**OOS-vigilance:** 3 QR scripts IS-only (filter + leak-guard + `.shift(1)`); NULL on IS sub-period
evidence; the kill regime/threshold were NOT chosen by OOS.

## CAMPAIGN-CLOSING: BTC OOS-strengthening is COMPREHENSIVELY EXHAUSTED
Both directions of attack on iter-020's thin OOS are now closed:
- **ADD trades:** funding-readmit (iter-021/022, K=5 lottery → K=20 collapse) · magnitude-selection
  (iter-023, generalizes worse). 
- **SUBTRACT trades:** exogenous kill-switch (iter-024, fragile/curve-fit).
The binding constraint is **direction-correctness at 14d** — and NO IS-identifiable signal (feature,
label, horizon, magnitude, regime add/subtract) cleanly separates the whipsaw-losing candles from the
trend-winning ones in the 2025-26 correction-dominated OOS. **iter-020 (IS +0.37 / OOS +0.09,
both-positive, K=20-confirmed, fully deterministic/IS-calibrated) is the robust BTC CEILING.**

## Recommendation (QR + mine) — CONSOLIDATE + EXTEND TO OTHER COINS
iter-020 stands as the BTC baseline. The highest-EV next step is NOT more BTC knob-tuning (exhausted)
— it's to **extend the proven deterministic stack** (200-SMA trend-state direction + strength gate q40
+ fixed_horizon N=42 let-winners-run + R2/R3/R5) **to the other coins.** This is a genuinely different
bet: a coin whose 2025-26 OOS regime is LESS correction-dominated than BTC's gives the both-positive
coherence a fairer test (BTC's OOS opened in a correction that whipsaws the trend direction — a
symbol-specific headwind, not necessarily a strategy flaw). Surfaced to the user (their "work with
others soon"); recommended next coin = ETH (the other major; high liquidity + retail flow).
