# Diary — iter-v1/023 (BTCUSDT) — DIAGNOSIS (research-only) — HONEST NULL (non-directional magnitude doesn't rescue OOS)

**Axis:** the non-directional volatility-MAGNITUDE pivot (the FE iter-014 untried lever) — predict
|move| (the sub-period-stable signal) and use it to select/size the deterministic trend-state entries,
to broaden the OOS without the seed-varying directional-timing lottery. QR Phase 1/2, IS-only. No backtest.

**Outcome: HONEST NULL — magnitude is a stable SIZE signal but does NOT rescue OOS robustness. iter-020
remains the robust BTC ceiling.** (QR rigorously avoided a curve-fit.)

### IS-only evidence (3 committed cutoff-asserted scripts)
- **Magnitude selection generalizes WORSE:** every magnitude variant is NEGATIVE in the recent IS
  sub-periods (the OOS-proxy) — recent3 B=−0.63 vs incumbent strength gate A=+1.86. Magnitude selects
  candles profitable in 2020-23 that turn negative in 2024-25.
- **The binding constraint is DIRECTION-correctness, not size.** `IC(vol_state, trend-PnL)` = +0.137
  full-IS but INVERTS to −0.21/−0.45 in the two most-recent sub-periods (strength control stays +).
  The FE's +0.22 |move| IC was at N=9 (3d); at the deployed N=42 (14d) it drops to +0.079, recent
  sub-periods all negative. High coming-vol on BTC 8h clusters in corrections where the deterministic
  direction WHIPSAWS.
- **Seed-stability premise MOOT:** the deployable magnitude rule is a deterministic past-only quantile
  (same footing as the iter-020 strength gate); the K=20 lottery never lived in SELECTION — it lived
  in the model TIMING/SIZING. Magnitude adds no robustness iter-020 lacks. only-B incremental rows
  (magnitude selects, strength doesn't): recent3 −2.175 — net-toxic.

**OOS-vigilance:** 3 QR scripts verified IS-only (filter + leak-guard + `.shift(1)`); NULL declared on
IS sub-period evidence, no OOS-fit.

### Comprehensive BTC OOS-strengthening map (iter-005→023)
Every lever explored: features (orthogonal NULL) · label-mode (fixed_horizon = the IS unlock) ·
horizon (boosts IS, not OOS) · direction source (stateless trend-state = the both-positive unlock) ·
conviction gate (iter-020 MERGE) · risk/de-lever (R2 keeper; trend-scale failed) · funding-readmit
(K=5 lottery, collapsed K=20) · non-directional magnitude (this NULL). **The binding constraint is
direction-correctness at the 14d horizon, which does NOT generalize in the 2025-26 OOS regime.**
iter-020's thin-but-both-positive OOS is the robust CEILING of the directional trend approach.

**Next:** iter-v1/024 — the QR's last recommended genuinely-different axis: a crypto-native EXOGENOUS
regime KILL-SWITCH (deterministic, binary — turn the trend-state book OFF in high-funding-stress /
high-realized-vol regimes where direction whipsaws). Attacks direction-correctness deterministically
(no seed-lottery, no magnitude-sizing). IS-only test: does it lift the RECENT sub-period stability
(generalize) or just curve-fit the recent regime? If NULL → BTC OOS-strengthening is comprehensively
exhausted; consolidate + extend the proven iter-020 stack to the other coins (user: "work with others").
