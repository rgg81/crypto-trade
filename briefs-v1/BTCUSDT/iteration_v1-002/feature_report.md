# Feature Report — iter-v1/002 EXPLORATION (BTCUSDT)

**Author:** Feature Engineer (Phase 4) · **Cadence:** EXPLORATION (bagging K=3) · **Symbol:** BTCUSDT
**Axis:** feature SELECTION / PRUNING — cut the redundant OHLCV noise that drives iter-001's
HIGH K=20 bagging dispersion (49.46), lift IS without surrendering OOS.
**Anchor:** `BASELINE_V1_BTCUSDT` (iter-001) — IS Sharpe **−0.2793** / OOS **+0.6401**, 201/95 trades,
net of fees + 2bps/side slippage. Full 193-feature `V1_FEATURE_COLUMNS`.

All evidence is IS-only (`close_time < 1742774400000`, 2025-03-24). Scripts (committed):
- `analysis/BTCUSDT/iteration_v1-002/ic_pruning_audit.py` — per-feature IS IC (1-bar + 21-bar) + iter-001 importance merge + hierarchical clustering on |Spearman| distance.
- `analysis/BTCUSDT/iteration_v1-002/build_pruned_set.py` — cluster-dedup + importance-gate selection rule → the proposed list.
- `analysis/BTCUSDT/iteration_v1-002/dispersion_proxy.py` — full-vs-pruned redundancy/signal-density (grounds the dispersion prediction).
- Tables: `ic_importance_cluster_table.csv`, `pruned_set_final.csv`.

IS window: 5,727 candles, 2020-01-01 → 2025-03-23. IC target conventions:
- **ic_1bar** = Spearman(feature, next-candle log-return) — mirrors iter-001's `ic_matrix.csv` convention (`run_baseline_v1._compute_forward_returns`).
- **ic_21bar** = Spearman(feature, 21-candle-forward log-return) — mirrors the MODEL's actual label horizon (`timeout_minutes=10080 / interval 480 = 21`). The 21-bar IC is the more decision-relevant number; primary in all tables below.

---

## 1. Candidate features + economic hypothesis + lineage

This is a **pure pruning iteration**. No new engineered features are authored. The proposed set is
a **strict subset of the 193-feature `V1_FEATURE_COLUMNS`** that iter-001 trained on, so the Quant
Engineer only changes the `feature_columns` argument — no feature-gen change, no parquet change.

### Lineage / why not the legacy `V1_FEATURE_COLUMNS_PRUNED` (48 cols)
The repo already carries a 48-col `V1_FEATURE_COLUMNS_PRUNED` from the OLD **pooled multi-symbol**
v1 track. **It is NOT fit for the BTC specialist.** On iter-001's BTC IS importance, only **7/40**
of its members (40 are in the 193) land in BTC top-50, and **23/40 land >100** (BTC-weak). It was
optimized for a pooled head, not BTC. I re-derived the pruned set from **BTC-specific** iter-001
importance + BTC IS IC + BTC IS clustering. (Source: `ic_pruning_audit.py` `[legacy]` block.)

### Selection rule (transparent, IS-only)
1. **Cluster dedup.** Hierarchical clustering (average linkage, distance = 1 − |Spearman ρ|) cut at
   0.30 ⇒ merge anything with |ρ| ≥ 0.70. The 193 collapse to **52 clusters**; 26 multi-member
   clusters cover **167 of 193 features** — i.e. the baseline is ~86% redundant. Keep ONE
   representative per cluster: the best iter-001 BTC importance rank, with an ADF-stationary swap
   when an ADF-passing sibling is within 3 ranks (don't anchor a family on a non-stationary
   price-level proxy).
2. **Importance gate.** Drop any representative that is **jointly inert** — iter-001 BTC rank > 130
   AND |IC_21bar| < 0.03 (neither split-share nor directional signal). 12 representatives dropped.
3. **Result:** 41 features, 1 per surviving cluster. (No orthogonal non-OHLCV add — see §4 note.)

### Economic rationale per family (what structural effect each cluster encodes)
| Family (count) | Representative members kept | Structural effect captured |
|---|---|---|
| **trend (12)** | trend_sma_50, trend_adx_7/14, trend_aroon_osc_14/25/50, trend_aroon_down_25/50, trend_plus_di_21, trend_psar_af, trend_supertrend_7_3, trend_supertrend_10_2 | Trend strength/direction & regime persistence. ADX/Aroon/DI/SuperTrend are the high-|IC_21bar| carriers (ADX |IC|≈0.11–0.12). trend_sma_50 kept as the single price-level anchor (rank 3, the dominant tree split). |
| **vol (11)** | vol_ad, vol_obv, vol_vwap-cluster (via vol_ad), vol_garman_klass_50, vol_hist_5/10, vol_cmf_20, vol_taker_buy_ratio + sma_10/sma_50, vol_volume_pctchg_15/20 | Volatility magnitude + order-flow pressure. Garman-Klass/hist = realized-vol state; taker-buy ratios = aggressor imbalance (|IC_21bar|≈0.05–0.09, among the strongest non-trend signals); AD/OBV = cumulative flow. |
| **stat (9)** | stat_autocorr_lag1/5/10, stat_skew_10/20/50, stat_kurtosis_10/30/50 | Return-distribution shape & serial dependence. autocorr_lag5 |IC_21bar|=0.078 is a genuine momentum/mean-reversion-timing signal; skew/kurtosis encode tail asymmetry (regime). Orthogonal to trend/vol clusters. |
| **mr (6)** | mr_pct_from_low_20/100, mr_pct_from_high_10/100, mr_bb_pctb_10, mr_rsi_extreme_14 | Distance-from-extreme mean-reversion. pct_from_low_100 |IC_21bar|=0.087 (3rd-strongest in the set) — proximity to range floor is directionally predictive on BTC. |
| **mom (2)** | mom_macd_hist_12_26_9, mom_macd_hist_5_13_3 | MACD-histogram momentum acceleration at two speeds. The 56-member momentum mega-cluster (cluster 35) collapses to its best representatives here; MACD-hist carries the residual orthogonal-to-trend momentum. |
| **cal (1)** | cal_dow_norm | Day-of-week seasonality (cheap, orthogonal). cal_hour_norm dropped (ADF-fail + |IC|=0.0017, joint-inert). |

**Note on `interact` (0 kept):** all 6 interaction features were either joint-inert (interact_ret1_x_natr
rank 157, interact_ret1_x_ret3 rank 167) or absorbed into the vol cluster (interact_natr_x_adx is a
member of cluster 49, represented by vol_garman_klass_50). A depth-5 tree composes these pairwise
products natively, so the explicit columns are redundant on BTC.

---

## 2. IS IC + ADF table (proposed set, sorted by iter-001 BTC importance rank)

| feature | imp_rank/193 | IC_1bar | IC_21bar | \|IC_21bar\| | ADF raw-α | cluster |
|---|---:|---:|---:|---:|:--:|---:|
| vol_ad | 1 | −0.0225 | −0.0871 | 0.0871 | FAIL | 44 |
| trend_sma_50 | 3 | −0.0184 | −0.1185 | 0.1185 | FAIL | 45 |
| vol_taker_buy_ratio_sma_50 | 8 | +0.0102 | +0.0870 | 0.0870 | pass | 16 |
| stat_kurtosis_50 | 9 | −0.0050 | +0.0045 | 0.0045 | pass | 42 |
| stat_autocorr_lag1 | 10 | +0.0125 | +0.0238 | 0.0238 | pass | 1 |
| vol_obv | 11 | +0.0079 | −0.0115 | 0.0115 | FAIL | 51 |
| vol_garman_klass_50 | 12 | +0.0110 | +0.0352 | 0.0352 | pass | 49 |
| trend_aroon_osc_50 | 13 | +0.0083 | +0.0208 | 0.0208 | pass | 20 |
| stat_autocorr_lag10 | 14 | −0.0024 | −0.0266 | 0.0266 | pass | 52 |
| stat_skew_50 | 15 | +0.0182 | +0.0369 | 0.0369 | pass | 18 |
| mr_pct_from_low_100 | 18 | +0.0160 | +0.0872 | 0.0872 | pass | 25 |
| trend_adx_14 | 19 | +0.0281 | +0.1205 | 0.1205 | pass | 46 |
| stat_skew_20 | 20 | +0.0103 | +0.0096 | 0.0096 | pass | 17 |
| stat_autocorr_lag5 | 26 | +0.0018 | +0.0779 | 0.0779 | pass | 2 |
| vol_hist_10 | 33 | +0.0128 | +0.0238 | 0.0238 | pass | 48 |
| mr_pct_from_high_100 | 36 | −0.0066 | +0.0155 | 0.0155 | pass | 22 |
| trend_aroon_down_50 | 38 | −0.0166 | −0.0308 | 0.0308 | pass | 23 |
| trend_aroon_osc_25 | 39 | −0.0128 | −0.0187 | 0.0187 | pass | 32 |
| stat_kurtosis_30 | 40 | −0.0156 | −0.0262 | 0.0262 | pass | 41 |
| trend_adx_7 | 48 | +0.0247 | +0.1112 | 0.1112 | pass | 47 |
| trend_plus_di_21 | 49 | +0.0026 | +0.0198 | 0.0198 | pass | 35 |
| vol_cmf_20 | 51 | −0.0127 | +0.0275 | 0.0275 | pass | 31 |
| mr_pct_from_low_20 | 53 | −0.0016 | +0.0124 | 0.0124 | pass | 26 |
| mom_macd_hist_12_26_9 | 58 | −0.0038 | −0.0491 | 0.0491 | pass | 29 |
| trend_psar_af | 59 | −0.0055 | −0.0143 | 0.0143 | pass | 40 |
| vol_taker_buy_ratio_sma_10 | 66 | — | +0.0458 | 0.0458 | pass | 15 |
| stat_skew_10 | 75 | — | −0.0188 | 0.0188 | pass | 19 |
| stat_kurtosis_10 | 87 | — | −0.0324 | 0.0324 | pass | 43 |
| trend_aroon_osc_14 | 89 | — | −0.0363 | 0.0363 | pass | 34 |
| mr_pct_from_high_10 | 91 | — | −0.0496 | 0.0496 | pass | 27 |
| trend_supertrend_7_3 | 94 | — | +0.0629 | 0.0629 | pass | 21 |
| vol_hist_5 | 97 | — | +0.0252 | 0.0252 | pass | 50 |
| mr_bb_pctb_10 | 107 | — | −0.0116 | 0.0116 | pass | 30 |
| mom_macd_hist_5_13_3 | 109 | — | −0.0177 | 0.0177 | pass | 28 |
| trend_aroon_down_25 | 115 | — | −0.0188 | 0.0188 | pass | 33 |
| trend_supertrend_10_2 | 123 | — | +0.0237 | 0.0237 | pass | 37 |
| vol_volume_pctchg_15 | 137 | — | +0.0314 | 0.0314 | pass | 8 |
| cal_dow_norm | 138 | +0.0006 | +0.0035 | 0.0035 | pass | 11 |
| vol_volume_pctchg_20 | 147 | — | +0.0387 | 0.0387 | pass | 9 |
| vol_taker_buy_ratio | 154 | +0.0008 | +0.0327 | 0.0327 | pass | 14 |
| mr_rsi_extreme_14 | 190 | — | −0.0622 | 0.0622 | pass | 24 |

**ADF (informational, not blocking):** 38/41 (93%) pass raw-α stationarity. The 3 ADF-fails
(vol_ad, vol_obv, trend_sma_50) are the cumulative-flow / price-level anchors — kept because they are
iter-001's top-3 importance carriers and LightGBM's split-finding is invariant to monotone level
shifts. (Full-193 ADF pass rate is lower because the trend_sma/ema/vwap cluster, mostly pruned here,
is uniformly ADF-fail.)

**Honest caveat:** absolute IS |IC| values are small (median |IC_21bar| ≈ 0.0275) across the board —
consistent with iter-001's negative IS Sharpe and HIGH bagging dispersion. BTC's per-feature edge is
thin; pruning concentrates what little there is and removes the noise the tree overfits to. We are
**not** claiming a strong-IC feature set; we are claiming a *higher-density, lower-redundancy* one.

---

## 3. Cluster-importance / redundancy

Hierarchical clustering on IS |Spearman ρ| (cut at |ρ|≥0.70):

| metric | full-193 | pruned-41 | change |
|---|---:|---:|---|
| feature count | 193 | 41 | −152 (79% cut) |
| clusters represented | 52 | 41 | 1 feature/family |
| frac of pairs \|ρ\|≥0.70 (redundancy load) | **0.1228** | **0.0098** | **12.5× lower** |
| mean \|Spearman\| off-diagonal | 0.2666 | 0.1515 | −43% |
| median \|IC_21bar\| (signal density) | 0.0250 | 0.0275 | +10% |
| share \|IC_21bar\|≥0.03 | 0.42 | 0.49 | +7pp |
| median iter-001 importance rank | 97/193 | 49/193 | kept the carriers |

The three giant redundant clusters that were collapsed:
- **Cluster 35 (56 members!)** — the momentum/oscillator mega-family (RSI/Stoch/Willr/ROC/MACD-line/
  DI/MFI/BB-%b at every window). All mutually |ρ|≥0.70; iter-001's best member ranks only 49. Collapsed
  to trend_plus_di_21 + the two MACD-hist representatives.
- **Cluster 45 (16 members)** — trend/price-level (sma/ema/atr at every window) + mr_dist_vwap. All
  ADF-fail. Collapsed to trend_sma_50 (the dominant split).
- **Cluster 49 (16 members)** — vol-magnitude (hist/garman_klass/parkinson/natr/bb_bandwidth) +
  interact_natr_x_adx. Collapsed to vol_garman_klass_50.

These three families alone are 88 of the 193. Removing 85 redundant siblings is the bulk of the
prune and is the mechanistic reason to expect the dispersion to fall (§5).

---

## 4. Recommended Optuna bounds (folded LightGBM-Master advisory)

**Bounds profile: KEEP `v1_specialist` (max_depth 5, num_leaves 31).** Do NOT widen depth/leaves for
this iteration. With a 41-feature space (vs 193), the same depth-5 / 31-leaf capacity is now a
*higher* features-per-leaf budget — the model can fit the kept signal without the previous pressure to
chase redundant siblings. Changing two things (features + bounds) at once would confound the prune
test. Specific regions (all within the `v1_specialist` profile):

| HP | Recommended region | Rationale (IS evidence) |
|---|---|---|
| `num_leaves` | keep profile (≤31) | 41 features need fewer leaves to span; tighter leaves = stronger per-study agreement. |
| `max_depth` | keep profile (5) | unchanged — isolate the feature variable. |
| `min_child_samples` | **lean HIGH (e.g. 40–120)** | thin per-feature IC ⇒ small leaves overfit noise. Higher min_child_samples is the cheapest dispersion brake; recommend Optuna favor the upper region. |
| `colsample_bytree` | **0.6–1.0** | at 41 cols, 0.6 still gives ~25 features/tree (plenty); keep the default range. Lower colsample on a *pruned* set no longer risks dropping the only signal-bearing column the way it did at 193. |
| `reg_alpha` / `reg_lambda` | keep default search (e.g. 1e-3 … 10, log) | regularization is the second dispersion brake; no IS reason to tighten. |
| `learning_rate` | keep default (e.g. 0.01–0.1, log) | unchanged. |
| `n_estimators` | keep default | unchanged. |
| **`training_days`** | **KEEP DEFAULT 10–500, step 10** | This is IMMUTABLE-by-policy and I am NOT proposing to narrow it. IS note: iter-001's IS is regime-split (negative on 2020–2025-03), so a *shorter* training window may help the model track regime — but that is exactly what the 10–500 search already explores per fold. Leave it to Optuna; do not pre-bias. |

**Why not also add the orthogonal non-OHLCV families now?** The funding / OI / long-short / basis /
regime-composed features exist in the parquet and were each vetted in the prior pooled track, but they
are **NOT** in iter-001's 193-col `V1_FEATURE_COLUMNS` — adding them is a NEW-FEATURE axis, not pruning.
Mixing it in would confound the prune verdict (can't attribute a lift to pruning vs new signal). I
**recommend them as the iter-003 axis**: take the iter-002 pruned set as the new base, then add the
2–3 highest-IS-IC orthogonal families one cohort at a time. This is the single most promising next move
because every kept feature here is OHLCV-derived and thus shares the same factor exposure — the biggest
remaining diversification gap is non-price information (funding/OI/flow).

---

## 5. Expected substitution effects + trial-stability prediction

**Substitution effects (post-Phase-6 importance check, to be appended as addendum):**
- iter-001's top-3 (vol_ad, vol_vwap, trend_sma_50) all sit in clusters 44/45. We keep vol_ad +
  trend_sma_50 and drop vol_vwap (cluster-44 sibling of vol_ad). Expect vol_ad + trend_sma_50 to
  **absorb vol_vwap's split share** and rise/hold near the top.
- The 56-member momentum cluster collapses to ~3 columns. Expect trend_plus_di_21 / MACD-hist to
  **gain substantial split share** (they now carry the whole momentum factor with no siblings to
  steal splits) — a clean substitution signature, not new signal.
- The high-|IC_21bar| carriers (trend_adx_7/14 ≈0.11–0.12, mr_pct_from_low_100 ≈0.087,
  vol_taker_buy_ratio_sma_50 ≈0.087, stat_autocorr_lag5 ≈0.078) should be top-tier in the pruned-set
  importance. If any of these instead lands rank-bottom, that is a falsification flag for that column.
- Weak keeps to watch for INERT verdicts: stat_kurtosis_50 (|IC|=0.0045), cal_dow_norm (|IC|=0.0035),
  mr_bb_pctb_10 (|IC|=0.0116). They are cluster representatives, so they should at least be USED, but
  if rank-bottom in the K=20 confirmation, drop them next.

**Trial-stability / dispersion prediction (the falsifier's quantitative basis):**
The K=20 dispersion measures per-candle disagreement among the 20 Optuna studies. Its mechanistic
driver is the redundant feature space: on each study's colsample subsample + bootstrap, different
studies latch onto *different members of the same cluster* (study A splits on trend_ema_5, study B on
trend_sma_50 — same factor, different column), producing divergent signed weights per candle. Pruning
to **1 representative per cluster** (redundant-pair load 0.123 → 0.010) removes that degree of freedom.
**Prediction: K=3 exploration dispersion drops materially below iter-001's 49.46; at K=20 confirmation
I expect dispersion in the ~30–40 band** (a 20–40% reduction). The 41-feature space also lets a depth-5
tree cover ~all features per tree (colsample 0.6 → ~25/41), further aligning the studies.

basin/lottery note: iter-001 basin_diagnostics V1 = PASS (cross-outer-seed std 0.0, expected since
outer seeds = 1; K-bagging is the relevant axis). I do **not** flag basin-lottery risk a priori for
this axis — pruning *reduces* the feature-space DOF that fragments studies, so if anything it lowers
lottery risk. The K=3 → K=20 cadence remains the correct control.

---

## 6. Pre-registered falsifier (HARD, decided before the run)

The pruning hypothesis is **NEGATIVE** if, on the iter-002 K=3 exploration backtest vs iter-001:

> **IS monthly Sharpe does NOT improve over −0.28 (i.e. stays ≤ −0.28) AND the K-bagging dispersion
> does NOT drop below ~45** (vs iter-001's 49.46).

- If **IS improves AND dispersion drops** → PROMISING; advance to K=20 CONFIRMATION on the same pruned set.
- If **dispersion drops but IS stays flat/down** → PARTIAL: the prune worked mechanically (consensus
  up) but BTC's OHLCV-only edge is genuinely thin; pivot iter-003 to the orthogonal non-OHLCV add (§4)
  rather than further OHLCV pruning.
- If **neither moves** → NEGATIVE: the high dispersion was not redundancy-driven; reconsider labeling
  (QR) / risk (RE) rather than features.
- Guardrail: OOS must not collapse (no material regression below iter-001's +0.64). Judge net of
  fees + 2bps/side slippage. Trade count expected to stay in the same ballpark (entry gate unchanged).

---

## Proposed `feature_columns` (copy-pasteable, 41 cols, strict subset of `V1_FEATURE_COLUMNS`)

```python
V1_BTC_PRUNED_ITER002 = [
    "cal_dow_norm",
    "mom_macd_hist_12_26_9",
    "mom_macd_hist_5_13_3",
    "mr_bb_pctb_10",
    "mr_pct_from_high_10",
    "mr_pct_from_high_100",
    "mr_pct_from_low_100",
    "mr_pct_from_low_20",
    "mr_rsi_extreme_14",
    "stat_autocorr_lag1",
    "stat_autocorr_lag10",
    "stat_autocorr_lag5",
    "stat_kurtosis_10",
    "stat_kurtosis_30",
    "stat_kurtosis_50",
    "stat_skew_10",
    "stat_skew_20",
    "stat_skew_50",
    "trend_adx_14",
    "trend_adx_7",
    "trend_aroon_down_25",
    "trend_aroon_down_50",
    "trend_aroon_osc_14",
    "trend_aroon_osc_25",
    "trend_aroon_osc_50",
    "trend_plus_di_21",
    "trend_psar_af",
    "trend_sma_50",
    "trend_supertrend_10_2",
    "trend_supertrend_7_3",
    "vol_ad",
    "vol_cmf_20",
    "vol_garman_klass_50",
    "vol_hist_10",
    "vol_hist_5",
    "vol_obv",
    "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_10",
    "vol_taker_buy_ratio_sma_50",
    "vol_volume_pctchg_15",
    "vol_volume_pctchg_20",
]
```

**Handoff to Quant Research:** adopt/modify/reject as you see fit. My recommendation is to run the
K=3 exploration with this exact 41-col list, `bounds_profile="v1_specialist"`, `training_days` 10–500,
`--n-trials 35`, `--slippage-bps 2`, and evaluate against the §6 falsifier. If you want a tighter
list, the 12 weakest keeps (rank > 100 OR |IC_21bar| < 0.02) are the trim candidates; if you want a
broader one, the next cluster representatives by importance are the add candidates — both are in
`ic_importance_cluster_table.csv`.
