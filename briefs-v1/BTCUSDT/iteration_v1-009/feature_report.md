# Feature Report — iter-v1/009 (BTCUSDT) — Phase 4 (Feature + Label-Horizon, IS-ONLY)

**Author:** Feature Engineer. **Symbol:** BTCUSDT. **Interval:** 8h (sacred). **Scope:**
Phase 4 — feature construction + selection + label-horizon design, IS-ONLY.
**Axis (user mandate):** *frequency emulation within the 8h constant* — higher-frequency
(short-window) features + expanded label timeout, so a fast entry read can ride crypto's
trend persistence and the payoff asymmetry lifts **Sharpe** (the objective), not return.

All numbers come from four committed, re-runnable, IS-only scripts under
`analysis/BTCUSDT/iteration_v1-009/`. Each asserts `open_time < OOS_CUTOFF_MS =
1742774400000` (2025-03-24) with a leak guard (`assert df["open_time"].max() <
OOS_CUTOFF_MS`); each reads ONLY the BTC 8h parquet; each computes every forward
quantity AFTER the IS filter (tail NaN-masks, no OOS peek); none touches `src/`, the
runner, or OOS:

- `short_vs_long_horizon_ic.py` → `short_vs_long_horizon_ic.csv` (Q1: multi-horizon IC)
- `label_feature_sharpe_grid.py` → `label_feature_sharpe_grid.csv` (Q2: label×feature Sharpe)
- `sharpe_seed_stability.py` → `sharpe_seed_stability.csv` (basin pre-check + importance)
- `label_mode_vs_horizon.py` → `label_mode_vs_horizon.csv` (causal lever disentangle)
- `recommended_set_redundancy.py` → `recommended_set_ic.csv`, `recommended_set_corr_matrix.csv`

The label scripts faithfully reproduce the runner's `label_trades` (ATR triple-barrier
first-hit; fixed_horizon sign), using the runner's ATR convention (`ATR = close *
vol_natr_21 / 100`, `lgbm.py:758`) and label fee 0.1%. IS window: 2020-01-01 ..
2025-03-23 16:00 (5727 8h candles, ≈62.7 months). All CV is purged forward-chaining
(5 folds, 3-bar embargo). **Objective = annualized Sharpe proxy** of per-trade OOF
returns = `mean(sign(pred)·realized_pnl) / std(...) · sqrt(3·365.25)`.

---

## 0. Headline finding (read this first)

**The BTC 8h directional null is a LABEL artifact, not a feature-set or noise-floor
artifact. The CURRENT label (ATR triple-barrier 2.9/1.45, 21-candle/7d timeout) is the
single quantitative root of the negative IS Sharpe — and the user's mandate fixes it.**

Three decisive, multi-seed numbers (recommended 19-col feature set, n=8 seeds):

1. **CURRENT label → mean Sharpe proxy +0.03, only 6/8 seeds positive, min −0.45
   (SIGN-MIXED).** This reproduces the incumbent BTC null (iter-008 anchor: OOF econ
   −0.24%/cand, dir_acc 0.4886). The triple-barrier's early TP/SL truncation caps
   winners and lets the BTC drift wash out the directional bet.
2. **Switching to `fixed_horizon` N=21 (same 7d hold, NO TP/SL truncation) → mean
   Sharpe +1.28, 8/8 seeds positive, min +0.95 (SIGN-ROBUST).** The single-lever
   `label_mode` flip at the SAME horizon is worth **Δ +1.22 Sharpe** (HYBRID set,
   `label_mode_vs_horizon.py` [B]). "Let winners run" is the mechanism: removing the
   barrier truncation is what rescues BTC.
3. **Expanding the triple-barrier timeout 21→42 candles (14d) ALSO flips it positive**
   (Δ +0.74 within triple-barrier mode, `label_mode_vs_horizon.py` [C]; mean Sharpe
   +0.90 with the recommended set, 8/8 positive, the LOWEST seed-spread of the
   positives at 0.556). This is the literal reading of the mandate ("expand the
   timeout") and is the lower-implementation-risk alternative.

→ **RECOMMENDATION: PROMISING. iter-009 = fixed_horizon N=21 (7d) label + 19-col
cluster-pruned HYBRID short+regime feature set.** Predicted IS Sharpe flips from ≈0
(SIGN-MIXED) to +1.0…+1.3 (SIGN-ROBUST 8/8). Caveat flagged for the team: the
MAGNITUDE is basin-sensitive (per-seed spread > 0.50) — the SIGN is robust but the
level is not; confirmation must run the full 20-seed cadence.

---

## 1. Candidate features — economic hypothesis + lineage (Q1: short vs long IC)

`short_vs_long_horizon_ic.py` computed IS univariate Spearman IC of 37 short-window
candidates and 34 long-window incumbents vs forward LOG returns at h ∈ {3, 6, 9, 21}
candles (1d/2d/3d/7d). The mandate's literal hypothesis — *pure short features beat the
long prune* — is **partially falsified**, but a sharper, more useful structure emerged.

**Family-level IC (script [B]):**

| family | mean\|IC\| h3 | h6 | h9 | h21 | mean abs_ic_mean | median peak h | frac \|IC\| grows w/ horizon |
|---|---|---|---|---|---|---|---|
| SHORT (37) | 0.0209 | 0.0185 | 0.0225 | 0.0213 | **0.0208** | 6.0 | 0.46 |
| LONG (34) | 0.0205 | 0.0252 | 0.0287 | **0.0361** | **0.0276** | 15.0 | 0.68 |

**Reads:**
- The LONG family carries slightly MORE average IC and — crucially — its |IC| **GROWS
  toward h=21** (68% positive slope, peaks late). The SHORT family is flatter and peaks
  early (h=6). So a *pure* short-feature swap is not the win.
- **But the highest-IC signals are NOT directional momentum — they are
  volatility/trend-regime + funding features whose IC grows with horizon.** The IS
  top-12 by mean |IC| (script [C]): `trend_adx_14` (0.054→0.121 h3→h21),
  `btc_funding_spread_30_90` (−0.041→−0.105), `trend_adx_7` (0.041→0.111),
  `funding_rate_zscore_30`, `mr_rsi_extreme_14`, `trend_supertrend_14_3`, then SHORT
  members `vol_taker_buy_ratio_sma_5` (peak h9 0.074), `vol_garman_klass_10`,
  `vol_parkinson_10`, `vol_natr_7`, `vol_atr_5`.
- **Fast directional momentum (RSI/ROC/MOM 5–9) is weak (|IC| ~0.012–0.018) and peaks
  EARLY (h3–6)** — at 8h BTC it behaves as short-horizon mean-reversion / noise, NOT
  trend anticipation. This is the guardrail: do not build the set around fast momentum.

**Economic hypotheses for the selected NEW short-window features (lineage = parquet
columns already computed past-only by `features_v1`; none requires regeneration):**

| feature | window | economic hypothesis (one sentence) |
|---|---|---|
| `trend_adx_7` | 7-bar | fast trend-strength read: high short ADX precedes the persistent multi-day moves a long hold monetizes. |
| `vol_garman_klass_10` | 10-bar | short OHLC-range realized vol; vol expansion regimes carry the directional payoff a fixed-horizon hold captures. |
| `vol_atr_5` | 5-bar | fastest true-range vol; the σ_t context that scales the forward payoff distribution. |
| `vol_taker_buy_ratio` / `_sma_5` | 1 / 5-bar | perpetual taker-flow imbalance — retail/aggressor pressure that leads BTC moves (a crypto-specific microstructure edge, no equity analogue). |
| `vol_mfi_7` | 7-bar | money-flow (price×volume) momentum; flow-confirmed direction over a fast window. |
| `mom_rsi_9` | 9-bar | mid-fast momentum; retained for non-redundant momentum coverage (carries the only meaningful short-momentum IC). |
| `stat_autocorr_lag1` | rolling | 1-lag return autocorrelation = the local trend-vs-chop regime; **TOP gain (14.9%) at fh_N9** — directly encodes persistence the long hold exploits. |
| `mr_pct_from_high_5` | 5-bar | proximity to recent high; fast pullback/breakout context. |
| `vol_cmf_10` | 10-bar | Chaikin money-flow; accumulation/distribution over a fast window. |
| `ent_shannon_10` | 10-bar | return-distribution entropy; low entropy = ordered/trending regime favorable to a long hold. |

**Retained long-horizon regime/funding anchors** (already in PRUNED-48, peak |IC| at
h=21): `trend_adx_14`, `trend_supertrend_14_3`, `btc_funding_spread_30_90`,
`funding_rate_zscore_30`, `stat_autocorr_lag5`, `vol_range_spike_72`, `mr_rsi_extreme_14`,
`stat_kurtosis_20`. Hypothesis: these set the slow regime/funding tilt; the short
features time entry within it.

---

## 2. IS IC + ADF table (recommended 19-col set)

From `recommended_set_redundancy.py` [A] (IC vs 3d/7d fwd log return) and
`short_vs_long_horizon_ic.py` (ADF p; all features pass at α=0.05, informational).

| feature | IC h9 (3d) | IC h21 (7d) | NaN% | ADF p |
|---|---|---|---|---|
| trend_adx_14 | +0.0877 | **+0.1205** | 0.2 | 0.000 |
| trend_adx_7 | +0.0631 | +0.1112 | 0.1 | 0.000 |
| btc_funding_spread_30_90 | −0.0699 | −0.1053 | 2.7 | 0.000 |
| trend_supertrend_14_3 | +0.0567 | +0.0790 | 0.2 | 0.000 |
| stat_autocorr_lag5 | +0.0173 | +0.0779 | 0.9 | 0.000 |
| mr_rsi_extreme_14 | −0.0652 | −0.0622 | 0.0 | 0.000 |
| vol_atr_5 | −0.0304 | −0.0634 | 0.1 | 0.001 |
| funding_rate_zscore_30 | −0.0520 | −0.0531 | 1.6 | 0.000 |
| vol_range_spike_72 | +0.0366 | +0.0520 | 1.2 | 0.000 |
| vol_garman_klass_10 | +0.0535 | +0.0515 | 0.2 | 0.000 |
| vol_taker_buy_ratio_sma_5 | +0.0737 | +0.0472 | 0.1 | 0.000 |
| stat_kurtosis_20 | −0.0458 | −0.0435 | 0.3 | 0.000 |
| mr_pct_from_high_5 | −0.0234 | −0.0370 | 0.1 | 0.000 |
| vol_taker_buy_ratio | +0.0498 | +0.0327 | 0.0 | 0.000 |
| ent_shannon_10 | +0.0097 | +0.0296 | 0.2 | 0.000 |
| stat_autocorr_lag1 | +0.0267 | +0.0238 | 0.9 | 0.000 |
| vol_mfi_7 | +0.0448 | +0.0160 | 0.1 | 0.000 |
| mom_rsi_9 | +0.0251 | +0.0115 | 0.0 | 0.000 |
| vol_cmf_10 | −0.0255 | −0.0020 | 0.2 | 0.000 |

All NaN% < 3% (LightGBM handles natively; **no parquet regeneration needed** — every
column already exists in `BTCUSDT_8h_features.parquet`).

---

## 3. Cluster-importance / redundancy

`recommended_set_redundancy.py` [B] within-set Spearman |corr| audit. The 23-col probe
set was cluster-pruned to 19 cols:

- **Dropped 3 collinear realized-vol estimators → kept 1.** `vol_natr_7`,
  `vol_garman_klass_10`, `vol_parkinson_10` are near-identical (|corr| 0.92–0.99). Kept
  `vol_garman_klass_10` (highest gain 6.3% at fh_N9 + highest |IC| of the trio); dropped
  `vol_natr_7` + `vol_parkinson_10`.
- **Dropped 2 near-inert features** (`mr_rsi_extreme_7` 0.01% gain, `cusum_norm_1s` 0.4%
  gain at fh_N9 — bottom-2 of the importance table).
- **Pruning IMPROVED the proxy:** 23-col fh_N21 mean Sharpe +1.025 → **19-col +1.278**
  (8/8 positive, min +0.95). Removing redundancy de-noised the loss surface.
- Remaining set: only 2 moderate pairs >0.65 (`trend_adx_7`↔`trend_adx_14` 0.715;
  `vol_mfi_7`↔`mom_rsi_9` 0.746); both encode distinct windows/families — retained. No
  pair >0.80.

---

## 4. Recommended Optuna bounds (incl. training_days range)

Profile: **`v1_pruned`** bounds. The 19-col set is small and dense; recommend a region
that resists IS-overfitting of a now-positive-but-basin-sensitive surface.

| hyperparameter | recommended region | rationale |
|---|---|---|
| `num_leaves` | 15 – 63 | 19 features; keep trees shallow-to-moderate to avoid memorizing the IS regime. |
| `min_child_samples` | 40 – 200 | larger floor (vs default) — the fixed_horizon label is noisier per-row; demand more support per leaf. |
| `colsample_bytree` | 0.6 – 0.9 | 19 cols → 0.6 keeps ~11/draw; preserves the short+regime mix. |
| `reg_alpha` | 1e-3 – 5.0 | moderate-to-strong L1; prune the weak fast-momentum splits. |
| `reg_lambda` | 1e-3 – 5.0 | L2 to stabilize the basin-sensitive magnitude. |
| `learning_rate` | 0.01 – 0.05 | lower end favored; the surface is regime-tilted, slow learning generalizes. |
| `n_estimators` | 200 – 800 | with low LR + early-stop. |
| **`training_days`** | **10 – 500, step 10 (UNCHANGED)** | **do NOT tighten.** The fixed_horizon edge is regime/funding-tilted and varies across the 5.2y IS window; Optuna should be free to pick the window length per fold. No IS evidence justifies narrowing the sacred search range. |

---

## 5. Expected substitution effects + trial-stability prediction

**Substitution (predicted, from `sharpe_seed_stability.py` [B]/[C] importance):**
- The new short features will substitute split-share away from the redundant long
  vol/momentum members. At fh_N9 the top gain is `stat_autocorr_lag1` (14.9%),
  `stat_autocorr_lag5` (8.8%), `stat_kurtosis_20`, `trend_adx_14`,
  `btc_funding_spread_30_90`, `vol_atr_5`, `vol_garman_klass_10` — a balanced short+regime
  mix, NOT dominated by any single family.
- **Predicted near-inert (rank-bottom) at confirmation:** `mom_rsi_9`, `vol_cmf_10`,
  `ent_shannon_10` (each <3% gain). If they land rank-bottom in the post-Phase-6 CSVs,
  **drop after one verdict** — do not re-test at higher Optuna budget (per the v3
  INERT-at-higher-budget precedent: it lets Optuna overfit IS noise and harms OOS).

**Trial-stability prediction (basin pre-check, `sharpe_seed_stability.py` [A]):**
- **SIGN is robust; MAGNITUDE is basin-sensitive.** Every positive cell has frac_pos =
  1.00 (8/8 seeds) but per-seed spread > 0.50 (fh_N21 0.95; fh_N9 0.85; tb_to42 0.556).
  This trips v1's basin-lottery flag on magnitude — so the team must plan the FULL
  cadence: **3-seed exploration screen → 20-seed confirmation** before any merge call.
- The CURRENT label is the ONLY SIGN-MIXED cell (min −0.45) — confirming the incumbent
  null is a label property, not a seed artifact.
- The single most STABLE positive is `tb_2.9/1.45 to42` (spread 0.556, the lowest of the
  positives, dir_acc 0.510) — the recommended FALLBACK if QR wants to minimize basin
  risk and keep the runner's native triple-barrier execution path.

**Pre-registered both-positive coherence FALSIFIER (NEGATIVE verdict if):**
1. confirmation IS Sharpe (20-seed mean) stays **≤ 0**, OR
2. the profile inverts (always-LONG / B&H beta beats the model's directional Sharpe in
   the positive regime — i.e. the lift is BTC drift not model alpha, the iter-008 §2
   failure mode), OR
3. fewer than **7/20** confirmation seeds are positive (sign not robust at full cadence).
Any of these → the expanded-horizon + short-feature axis is FALSIFIED for BTC 8h.

---

## 6. iter-009 config recommendation (exact)

**PRIMARY (cleanest single-lever, highest seed-robust mean):**
- **Feature columns (19, all in parquet — no regen):**
  `trend_adx_7, vol_garman_klass_10, vol_atr_5, vol_taker_buy_ratio,
  vol_taker_buy_ratio_sma_5, vol_mfi_7, mom_rsi_9, stat_autocorr_lag1,
  mr_pct_from_high_5, vol_cmf_10, ent_shannon_10, trend_adx_14, trend_supertrend_14_3,
  btc_funding_spread_30_90, funding_rate_zscore_30, stat_autocorr_lag5,
  vol_range_spike_72, mr_rsi_extreme_14, stat_kurtosis_20`
- **Label:** `label_mode="fixed_horizon"`, `label_timeout_minutes=10080` (= 21 candles =
  7d at 8h; N derived as `timeout_minutes // 480`). `use_atr_labeling`: irrelevant in
  fixed_horizon mode (barriers not scanned) — set `use_atr_labeling=False` /
  `atr_tp_multiplier=None` to be explicit. Execution-time barriers (backtest SL/TP) are
  a separate runner concern; QE should keep the existing ATR execution barrier OR widen
  TP — flag for QE.
- **Predicted IS Sharpe:** ≈0 (SIGN-MIXED) → **+1.0…+1.3 (8/8 seeds positive, min +0.95)**.

**FALLBACK (literal "expand the timeout"; lowest basin spread; native triple-barrier
execution preserved):**
- Same 19-col feature set.
- **Label:** `label_mode="triple_barrier"`, `use_atr_labeling=True`,
  `atr_tp_multiplier=2.9`, `atr_sl_multiplier=1.45`, **`label_timeout_minutes=20160`**
  (= 42 candles = 14d). Mean Sharpe +0.90, 8/8 positive, spread 0.556 (lowest of the
  positives), dir_acc 0.510.

QR makes the final call between PRIMARY and FALLBACK. My recommendation: **PRIMARY** —
the fixed_horizon mode flip is the single largest, cleanest causal lever (Δ +1.22 at the
SAME 7d hold) and most directly realizes the "let winners run → Sharpe" thesis. FALLBACK
is the right pick if minimizing implementation/basin risk outweighs the higher mean.

---

## [Post-Phase-6 addendum — to be appended after the real backtest]

_Reserved: feature-importance interpretation vs the §5 predictions (did the short
features gain split-share or land rank-bottom; did the fixed_horizon flip hold its
sign at 20 seeds; substitution effects realized)._
