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

---

## Phase 7.4 — LightGBM Master Post-Mortem (iter-v1/086)

**Outcome:** IS Sharpe −0.3044 (157 trades, WR 35.7%, PF 0.90, MaxDD 72.95%); OOS −0.5967 (90 trades). SPECIALIST-NEGATIVE; no bundle seat. Probe (n_trials=10, seed=42) +0.4930 → full (n_trials=30, same seed) −0.3044 = **Δ−0.7974**. cross_seed_std=0.000 is a DEGENERATE --seeds 1 artifact, NOT robustness. Seed count constant probe↔full → the only moving variable is n_trials 10→30.

### 1. Probe→full degradation mechanism (load-bearing)
Parsed 46 walk-forward folds (30 trials × 50 inner seeds = 1500 trial-lines/fold). **Per-fold best in-fold Optuna objective: mean +0.1788 (46/46 folds POSITIVE) vs realized walk-forward IS −0.3044 → ~0.48 Sharpe of pure optimism.** Textbook in-fold-up / walk-forward-down overfit (matches UNI/085's +0.116 vs −0.70). **Smoking gun — training_days collapsed SHORT: median 95d, mean 177d, 26/46 folds <120d** (my Phase 4.5 §1 red flag FIRED). n_trials=30 had budget to discover short-window noise-fit configs; n_trials=10 sampled too sparsely to find them. learning_rate median 0.0079 + reg_alpha median 0.071 (I predicted 0.018 / 0.8–2.0) → search abandoned regularization to chase in-fold fit. Deeper-search-overfits-noisier-surface, fully attributed.

### 2. Phase 4.5 prediction vs reality — owned
Predicted +0.48 modal MEDIUM-HIGH; actual −0.30 (Δ−0.78 miss). Root cause: treated the n_trials=10 probe as predictive of the n_trials=30 specialist; assumed deeper search IMPROVES walk-forward Sharpe (true on a real basin, FALSE on a noisy surface). The UNI precedent (probe→full Δ−0.46) was in the record; I should have de-rated +0.493 by ~0.5–0.8 → modal ~0.0 coin-flip, LOW confidence.

### 3. GATE-2 reform — KEY DELIVERABLE
**Recommendation: probe at n_trials=30 (SAME-BUDGET), NOT a threshold haircut.**
- Threshold-haircut corrects a bias measured only twice (Δ−0.46, Δ−0.80, 0.34-wide spread) — too noisy to set a single threshold; trades false-pass for unquantifiable false-reject.
- Same-budget probe eliminates the bias BY CONSTRUCTION: n_trials=30 single-seed probe vs n_trials=30 50-seed full differ ONLY in seed averaging (small, symmetric regression-to-basin, not one-sided optimism).
- Cost: n_trials=30 single-seed probe ≈ single-digit minutes (~0.5–1% of the 6h full run). No compute argument for keeping the mis-calibrated cheap probe.
- **Reform spec:** (1) GATE-2 PRIMARY probe at n_trials=30 single-seed=42, threshold stays ≥+0.30; (2) keep n_trials=10 probe as an optional seconds-long pre-pre-screen (advisory, never a PASS gate); (3) pre-register the in-fold/walk-forward gap as GATE-2 SECONDARY — if mean per-fold best-objective minus realized walk-forward IS > ~0.3, flag noise-dominated surface (the leading indicator that would have caught UNI + TRB); (4) optionally cap training_days lower bound ~120d for single-symbol stock-stack mines (26/46 folds <120d = the noise-exploitation channel).

### 4. Feature read — DIVERSIFIER-DEGENERATE confirmed
Top-10: vol_atr_14(1), btc_funding_spread_30_90(2), stat_autocorr_lag5(3), trend_aroon_osc_50(4), mom_macd_line(5), interact_natr_x_adx(6), funding_rate_zscore_30(7)/90(8), trend_adx_14(9), oi_delta_30_z90(10). MACD rank 5 (prediction ≤5 technically MET, boundary). **5 of top-10 = shared vol/funding/OI bundle anchors (entire top-2).** TRB's idiosyncratic momentum tier sits BELOW the shared funding block = F5a DIVERSIFIER-DEGENERATE. Moot for the seat (negative standalone) but confirms the 0.548 return-corr would have understated PnL-corr had TRB printed positive.

### 5. R5 cold-start — FIRED
TRB earliest kline 2022-09 (not 2020-09). **2022-09 IS PnL −38.43% (5 trades) = 15.7% of |total IS PnL| (clears the >15% trigger).** Dropping 2022-09 flips cumulative IS PnL −25.24% → +13.19% (Δ+38.43). R5 fire rate 0.0000 IS — vol-targeting did NOT damp the listing window (first 45 days ran at full weight before VT history matured). Caveat: flips PnL SIGN but NOT Sharpe to merge-worthy (Sharpe dominated by the §1 short-window overfit across all folds). Confirms R5 needs a hard listing-window guard (skip or 0.5× the first 45 days post-listing) for fresh-listing cohort mines.

### Notes for Critic (7.5)
1. cross_seed_std=0.000 is degenerate (n_outer_seeds=1), NOT a Check-1 robustness PASS.
2. Load-bearing artifact is METHODOLOGICAL (n_trials=10 probe systematically optimistic ~0.5–0.8 on 2 symbols), not a code defect. The in-fold/walk-forward gap (+0.179 vs −0.30, 46/46 folds positive in-fold) is the leading indicator. Reform: same-budget n_trials=30 probe.
