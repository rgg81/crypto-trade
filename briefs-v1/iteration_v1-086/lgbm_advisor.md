# LightGBM Master Advisory — iter-v1/086 (TRBUSDT)

## Context
SPECIALIST single-coin cohort ("TRBUSDT",), STOCK 48-col V1_FEATURE_COLUMNS_PRUNED, ZERO new features by design. Anchor BUNDLE-002 (v0.v1-082; IS +0.7157 / OOS +1.0043). Probe: single-seed=42 n_trials=10 → IS +0.4930, 180 IS trades, max |IC| 0.3863 (mom_macd_line_12_26_9). First fresh mine to clear GATE-2 (+64% over bar). Lock: max_depth=5, num_leaves=31 FIXED, n_trials=30, 50 inner seeds, ENSEMBLE_SIZE=1, single outer seed=42, specialist_mode, ATR 2.9/1.45, v1_pruned bounds, NO features, multi-seed CONFIRMATION dropped. All recs are predictions WITHIN the lock.

## 1. HP-region guidance WITHIN the lock (prediction, not a bound change)
From the UNI/085 run.log v1_pruned-specialist landing distribution (same 48-col surface):
- learning_rate: modal ~0.018 (range 0.015–0.025) — log-uniform pulls low.
- reg_alpha: 0.8–2.0 (L1~1 stock-stack sweet spot; TRB's tighter top-IC may pull lower 0.5–1.0).
- colsample_bytree: 0.65–0.75.
- training_days: **240–320, modal ~300 (load-bearing)** — TRB's 50d trivial Sharpe +0.418 (real longer-cadence trend) vs negative 5d/21d → productive window is MEDIUM-LONG. If it lands SHORT (<120d) = short-horizon noise-fitting red flag (Phase 7.4 watch).
- min_child_samples NOT searched (LGBM default 20). is_unbalance=True hardcoded (binary) — Phase 7.4 attribution flag only.

## 2. Probe→full-run expectation
n_trials 10→30 (IS Sharpe rises +0.05/+0.15) vs 50-seed averaging (regresses toward basin center if +0.49 was lucky). **Net modal 50-seed mean IS Sharpe ≈ +0.48, range [+0.38, +0.62], MEDIUM-HIGH confidence.**
**Basin-lottery call (load-bearing): cross_seed_sharpe_std predicted [0.05, 0.20], well under the 0.30 downgrade trigger.** A momentum signal with one clear top-IC family is the LEAST lottery-prone profile in v1 fresh-mine history. **Pre-registered falsifier:** if cross_seed_sharpe_std > 0.40 with positive single-seed-42 but mean < +0.20 = basin-lottery signature, prediction WRONG (Phase 7.4 must record).

## 3. Feature-importance prediction (pre-registered for Phase 7.4)
Pre-registered TRB top-5 (IS gain rank):
1. vol_atr_14 (rank 1-2, universal anchor, HIGH conf)
2. **mom_macd_line_12_26_9 rank ≤ 5 (DISCRIMINATING prediction** — TRB's max-IC; if rank > 8 despite top-IC, the IC→importance translation failed)
3. trend_adx_14 (rank 3-7)
4. oi_delta_30_z90 (bundle-shared, rank 2-4)
5. one of interact_natr_x_adx / stat_autocorr_lag5 / trend_aroon_osc_50
**Bundle-shared vs idiosyncratic (KEY):** expect ~2 of top-5 shared (vol_atr_14, oi_delta_30_z90). TRB's discriminating lift MUST come from MACD/ADX binding HIGHER than for the incumbents. **If vol_atr_14 + oi_delta dominate AND MACD/ADX sit rank > 8, TRB is re-learning the shared bundle basis and the diversification thesis WEAKENS** — flag explicitly at Phase 7.4.
Inert tail: cross-asset ratio features (dot_vs_btc_ret_ratio_30, eth_vs_btc_ret_ratio_30) will sit at gain ~0 (dead on stock stack) — EXPECTED/benign, NOT a /085-style crater (those were NEW inert features; here it's pre-existing dead weight Optuna routes around).

## 4. Risk flags (Phase 7.4 telemetry)
- **R5 cold-start:** TRB IS-start 2020-09 is a fresh-listing window but <3% of IS (vs UNI's larger exposure). Pre-registered ask: isolate IS PnL from 2020-09→2020-10-15 (first 45 days un-vol-targeted, can run at 2.0x). If >15% of |IS PnL| from <3% of period → attribute to R5 cold-start, not structure (as /085 diary did).
- **MaxDD watch:** UNI posted 91% IS MaxDD. A >70% IS MaxDD with positive Sharpe is a basin-fragility tell even at tight cross_seed_std.

## 5. Bundle-fit lens (CONDITIONAL — the load-bearing bundle caveat)
0.548 is RETURN-stream corr, not strategy-PnL corr. Decorrelation source is structural: TRB MACD-led momentum vs DOT aroon/autocorr, ETH/BTC vol+OI. **Cautiously positive, MEDIUM confidence — CONDITIONAL on §3: TRB's MACD/ADX tier binding ABOVE the shared vol_atr_14/oi_delta anchors.** If shared features dominate, TRB's trade-timing converges to the bundle and 0.548 UNDERSTATES PnL-correlation OOS → diversification evaporates.
**Reframe: 0.548 is the LEAST-correlated SURVIVOR of a high-baseline universe (STORJ 0.5505 essentially tied; floor ~0.55), NOT a classically low diversifier.** Benefit is REAL but MODEST. A PROMISING [+0.20,+0.50] standalone is bundle-accretive ONLY if realized PnL-stream corr comes in BELOW 0.548. **Phase 7.4 MUST compute realized TRB-specialist-PnL vs bundle-PnL correlation, not trust the return-corr proxy, before any BUNDLE-003 seat decision.**

## Closing
Confidence: MEDIUM-HIGH on standalone IS reproduction (+0.48 modal, tight cross_seed_std); MEDIUM on diversification. TRB is the cleanest fresh-mine setup v1 has produced (single-family momentum = least lottery-prone). **The QR must NOT ignore:** the diversification thesis is CONDITIONAL on the MACD/ADX importance-ordering check (§3, §5) — a PROMISING standalone that re-learns the shared basis is NOT a real diversifier at 0.548.
