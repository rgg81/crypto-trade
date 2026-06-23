# BRIEF — iter-v2-003 EXPLORATION: cross-sectional LightGBM return predictor on rank 21–40

**Track:** portfolio-iteration-v2 (L/S rank-21–40 mid-cap perps). **Type:** EXPLORATION — ONE change:
replace the hand-crafted trend+carry+xs blend with a **cross-sectional ML signal** (fast LightGBM) that
predicts each coin's RELATIVE forward return within the band, walk-forward, dollar-neutral. OOS HIDDEN.

**Why ML, why now (grounded in the measured findings):** iter-v2-001/002 showed the cohort holds real
but *regime-split* structure — trend is EARLY-alive (2021–23) / LATE-dead, XS-mom is the mirror
(EARLY-dead / LATE-alive). A fixed blend can't exploit a regime-conditional combination; a walk-forward
LightGBM can LEARN it (it retrains monthly, so it re-weights features as the regime turns). This is the
critic's regime-complementarity insight, generalized: let the model route across trend/XS-mom/carry/vol
adaptively instead of a hand-set γ. **Objective = SHARPE, dollar-neutral; not return.**

## Hard rules (same gauntlet as every v2 iteration)
- **Leak-safe walk-forward (the critical risk).** Features at candle t use ONLY data ≤ t. The label is a
  FORWARD return used ONLY in training, on rows strictly BEFORE the test month, with the embargo gap.
  Predictions for a test month use a model trained only on prior data. A future-perturbation leak test
  is MANDATORY (perturb all inputs ≥ cutoff → pre-cutoff signal+net bit-identical).
- **Fast model** (user directive): LightGBM, ~200 trees, depth ≤ 6, lr 0.05, 1–3 seeds. No giant search.
- **Honest cost:** the SAME slippage-inclusive pipeline; report turnover + 2×-taker (rank-churn binding).
- **Era-split is the load-bearing falsifier:** EARLY (2021–23) vs LATE (2024→cutoff) in-sample; the ML
  must lift the LATE era over the anchor, else it's regime beta in a costume (KILL).
- **No OOS-tuning.** OOS hidden; single CONFIRMATION reveal later. Structural choices pre-registered here.

## 1. Engine hook (parity-preserving infra — do FIRST)
Add `run_book_from_signal(coins, signal_panel, *, rank_lo, rank_hi, season, slip_bps_fn, delta, k_exit,
mode, cost_mult, slip_mult, liq_win)` to `engine_v2.py`. It takes a precomputed per-(coin,candle)
`signal_panel` (DataFrame aligned to the opens grid) and runs the EXISTING downstream pipeline ONLY:
`raw = (signal_panel / rvol).where(elig)` → gross-norm → `.shift(1)` lag → band → eligexit → renorm →
vol-target → net (taker+slippage+funding), reusing the SAME `_apply_band_eligexit`, `_renorm`,
`_slip_side_panel`, `build_panel`, `_signals` (for rvol/ret_fwd/fund_next), `eligibility` code paths as
`run_book`. There is NO walk-forward λ here (the signal IS the target; λ is a trend+carry concept).
Returns the same dict shape as `run_book` (net, target_w, held_w, turnover, avg_positions, tickets,
IS, OOS, elig, scale). This is a NEW path — it does not touch `run_book`, so parity_check stays green.
Add a unit test: a constant/zero signal_panel produces a degenerate book without error; a hand-set
signal reproduces a hand-computed small-panel net.

## 2. The ML module (`analysis/portfolio_v2/ml_v2.py`)
### 2.1 Feature panel (ALL past-only, per coin, computed on the full pool then masked to the band)
Build a long/tidy frame of (coin, candle, features, label). Features (each knowable at close[t]):
- **Trend:** `ret_h = close/close.shift(h) - 1` for h ∈ {7,21,42,84,168}; and `sign(ret_h)`.
- **Momentum accel:** `ret_21 - ret_84`, `ret_42 - ret_168`.
- **XS rank:** centered within-band return-rank (the `_xsmom` construction) at L ∈ {21,84} — past-only.
- **Carry:** `fund.rolling(9).mean()`, `fund` level, `sign(fund.rolling(9).mean())`.
- **Vol:** `rvol_84 = close.pct_change().rolling(84).std()`; `ret_21/rvol_84` (vol-scaled mom).
- **Cross-sectional context (within band, past-only):** rank of `rvol_84`, rank of `carry`, and
  `ret_84 − band-median(ret_84)` (relative strength vs cohort).
- **Regime / trend-health (cohort-level, broadcast to every coin):** band-mean `|trend|`,
  band-median `rvol_84`, and a trailing realized-Sharpe of the trend anchor net over the prior ~63
  candles (past-only) — the EARLY/LATE regime proxy that lets the tree gate trend vs XS-mom.
All features must be NaN-safe (early-life coins drop out via the seasoning/elig mask, not via fill).

### 2.2 Label (relative, dollar-neutral by construction)
`y[c,t] = ret_fwd1[c,t] − band_mean(ret_fwd1[·,t])` where `ret_fwd1[c,t] = open[c,t+2]/open[c,t+1] − 1`
(the return the signal at t will earn AFTER the engine's `.shift(1)` lag — i.e. signal[t] predicts the
t+1→t+2 open-to-open return), cross-sectionally DEMEANED within the eligible band at t. Predicting the
demeaned forward return makes the model learn RELATIVE performance → the centered-rank signal is
dollar-neutral. The label is forward; it appears ONLY in training rows (all < test month).

### 2.3 Walk-forward training (leak-safe, fast)
For each calendar test month M (same month loop as `_canonical_book`):
- Train rows: candles in `[M − TRAIN_MONTHS(24)mo, M − GAP_CANDLES(3)candles)`, eligible-band only, label
  non-NaN. Embargo GAP so the last train label (t+1) does not reach into M.
- Model: LightGBM regressor, `n_estimators≈200, num_leaves≈31, max_depth≤6, learning_rate=0.05,
  subsample=0.8, colsample_bytree=0.8, min_child_samples≈50`, objective `regression_l2` (or
  `lambdarank`/`rank_xendcg` on the within-month groups if it’s not materially slower — try L2 first).
  Optional 3-seed mean for prediction stability (keep it fast). Require ≥ ~1000 train rows else skip M
  (cold start → that month falls back to the anchor signal, see §3).
- Predict the test-month band rows → `pred[c,t]`.

### 2.4 Prediction → signal panel
`signal[c,t] = centered within-band rank of pred[c,t]` (same centering as `_xsmom`: rank → `(rk −
(n+1)/2)/n`, `.where(elig)`), so the book is dollar-neutral and on the same scale as the other signals.
Coverage starts only after 24mo of training history exists (like the anchor's walk-forward) → the
EARLY-period 2020-21 is naturally thin; that's fine and honest.

## 3. Config / integration
- `iter_v2_003_xsml.py` (run script): load_pool_pit(), rank 21-40, season=168, default slip. Build
  features → walk-forward predict → signal panel → `run_book_from_signal(...)`. On months with no model
  (cold start), fill the signal with the anchor's trend+carry signal (so the book is never undefined;
  document the fallback fraction). Report the SAME diagnostics as iter-v2-002: IS + EARLY/LATE split,
  per-year Sharpe, turnover/tickets/avgPos, dollar-neutrality, OOS HIDDEN behind `--reveal`.
- **Pre-registered gates (judged IS + LATE only, OOS hidden):**
  - **G1 — IS:** ML IS Sharpe ≥ anchor +1.53 − 0.10 (a small give-back ok iff LATE improves).
  - **G2 (load-bearing) — LATE lift:** ML LATE (2024→cutoff) Sharpe > anchor LATE (+1.16) by ≥ +0.20.
  - **G3 — cost survival:** the LATE lift survives 2×-taker AND `slip_pessimistic` (rank-churn is the
    risk; if 2×-taker eats it like iter-002, KILL).
  - **G4 — not a single-feature/regime artifact:** report feature importance; the LATE lift must NOT be
    carried by a single feature, and the model must beat a same-pipeline **trend-only** and
    **XS-mom-only** signal on LATE (i.e. ML adds over its own ingredients).
  - **G5 — methodology:** leak test green (future-perturbation), parity_check unchanged, dollar-neutral,
    cold-start fallback fraction reported, no per-month label leakage.
- **KILL:** lift concentrated in EARLY only (regime costume); dies at 2×-taker; or no lift over the
  trend-only/XS-only baselines (ML adds nothing).

## 4. Deliverables + verification
- `analysis/portfolio_v2/engine_v2.py` (+ `run_book_from_signal`), `analysis/portfolio_v2/ml_v2.py`,
  `analysis/portfolio_v2/iter_v2_003_xsml.py`, tests in `tests/test_portfolio_v2.py`
  (`run_book_from_signal` sanity + a leak test: ML signal pre-cutoff unchanged under post-cutoff
  perturbation — can be a fast small-but-spanning synthetic panel, OR a targeted check that the
  walk-forward train windows never include ≥cutoff rows).
- Verify: `ruff` clean; `pytest` all green; `parity_check.py` UNCHANGED at ~1e-16 (the ML path must not
  perturb run_book); then run `iter_v2_003_xsml.py` and report the full IS + EARLY/LATE table + feature
  importance + turnover + cold-start fraction. Keep it FAST (target < ~15 min wall).
- DO NOT reveal OOS. DO NOT modify v1 `analysis/portfolio/` or `src/`.
