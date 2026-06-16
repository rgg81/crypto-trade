# Feature Report — iter-v1/005 EXPLORATION (BTCUSDT)

**Author:** Feature Engineer (Phase 4) · **Cadence:** EXPLORATION (bagging **K=5**) · **Symbol:** BTCUSDT
**Axis:** NEW FEATURE FAMILY — add ONE orthogonal, NON-OHLCV feature to the 41-col OHLCV prune base.
**Anchor:** the 41-col prune base `V1_BTC_PRUNED_ITER002` (iter-004 K=20: IS **−0.1691** / OOS **+0.4843**,
dispersion 45.51) — and ultimately `BASELINE_V1_BTCUSDT` (iter-001 K=20: IS −0.2793 / OOS +0.6401).

All evidence is IS-only (`open_time < 1742774400000`, 2025-03-24). Scripts (committed):
- `analysis/BTCUSDT/iteration_v1-005/orthogonal_ic_audit.py` — parquet inventory + IS IC (1-bar + 21-bar)
  of every candidate orthogonal feature + orthogonality (max/mean |Spearman| vs the 41-col base) + ADF.
- `analysis/BTCUSDT/iteration_v1-005/funding_robustness.py` — sub-period IC stability, funding-family
  internal redundancy, and directional-coherence bucketing for the iter-005 pick.
- Tables: `parquet_availability.csv`, `orthogonal_ic_table.csv`, `family_best.csv`, `funding_family_corr.csv`.

IS window: 5,727 candles (2020-01-01 → 2025-03-23). IC conventions (both reported; **21-bar primary**):
- **ic_1bar** = Spearman(feature, next-candle log-return) — mirrors the runner's `_compute_forward_returns`.
- **ic_21bar** = Spearman(feature, 21-candle-forward log-return) — mirrors the MODEL's actual label horizon
  (`timeout_minutes=10080 / 480 = 21`). The decision-relevant number.

---

## The diagnosis this iteration attacks (iter-001..004)

iter-004 confirmed at robust K=20 that the 41-col OHLCV prune still **inverts** (IS −0.17 / OOS +0.48).
The iter-002 prune cut redundancy (dispersion 49.5→45.5, IS less-negative) but did **not** manufacture
a generalizing edge. **Every kept feature in the 41-col base is OHLCV-derived** — one shared price
factor. The diagnosed lever (iter-002 §4, my own prior recommendation): add **orthogonal, NON-OHLCV**
information — funding / open-interest / long-short / basis — that is independent of the price factor.
iter-005 fires that lever, **one family per screen** so attribution stays clean (skill: one axis per
EXPLORATION). This is a NEW-FEATURE axis on top of the prune base, not more pruning.

---

## 1. Parquet-availability inventory

**Every candidate orthogonal feature is ALREADY in `BTCUSDT_8h_features.parquet` (235 cols).** No
feature-gen code change and **no regen** is needed for iter-005..008 — the Engineer only changes the
`feature_columns` argument. (Source: `parquet_availability.csv`.)

| candidate | family | in parquet? | regen needed? | IS coverage | lineage |
|---|---|:--:|:--:|---:|---|
| `btc_funding_spread_30_90` | funding | **yes** | **no** | 97.3% | iter-052; STRONGLY LEARNED at /053 (rank 4–10/48) |
| `funding_rate_zscore_30` | funding | yes | no | 98.4% | iter-023 (pooled track) |
| `funding_rate_zscore_90` | funding | yes | no | 98.4% | iter-023 (pooled track) |
| `btc_funding_rate_8h_impulse` | funding | yes | no | 98.4% | iter-052; INERT at /053 (rank >30/48), dropped /054 |
| `oi_price_divergence_30` | open_interest | yes | no | 79.7% | iter-084 (CRV specialist; local-only there) |
| `btc_oi_delta_5_z30` | open_interest | yes | no | 84.8% | iter-058; BASIN-LOTTERY (pooled, multi-seed) |
| `oi_delta_30_z90` | open_interest | yes | no | 79.7% | iter-025 (pooled track) |
| `long_short_zscore_30` | long_short | yes | no | 73.2% | iter-049 (pooled track) |
| `basis_zscore_30` | basis | yes | no | 99.5% | iter-034 (pooled track); RETIRED at /040 (pooled INERT) |

OI/long-short coverage <100% because the Binance OI/long-short archive starts ~2020-09 and has scattered
gaps; the leading-NaN + scattered-NaN are LightGBM-native (no fill needed; first-valid 2020-09→10). These
are reduced-coverage but still 73–85% of the IS window — usable, just thinner than funding/basis.

**Other orthogonal families exist in the parquet** (`ent_shannon_*`, `cusum_*`, `hurst_100`,
`regime_momentum_signed_5d`, `rev_*`, `vol_state_z_natr_30`) but they are **OHLCV-derived** (entropy/
CUSUM/Hurst of returns; composed momentum) — same price factor as the base. The four candidate families
above are the only **truly non-price** information classes (funding, OI, positioning, basis), so the
BATCH draws exclusively from them.

---

## 2. IS IC + orthogonality table (the screen)

Sorted by **screen_score = |IC_21bar| × orthogonality**, where `orthogonality = 1 − max|Spearman| vs the
41-col base`. We want high IC *and* low correlation to the base (genuinely new signal). (Source:
`orthogonal_ic_table.csv`.) For context, the 41-col base's strongest features are `trend_adx_14`
|IC_21bar|=0.121, `trend_sma_50` 0.118, `trend_adx_7` 0.111; **base median |IC_21bar| = 0.0275.**

| feature | family | ic_1bar | ic_21bar | \|ic_21bar\| | max base corr | (vs) | orthogonality | **screen** | ADF |
|---|---|---:|---:|---:|---:|---|---:|---:|:--:|
| **btc_funding_spread_30_90** | funding | −0.0260 | **−0.1053** | **0.1053** | 0.339 | trend_aroon_osc_50 | **0.661** | **0.0696** | pass |
| funding_rate_zscore_30 | funding | −0.0567 | −0.0531 | 0.0531 | 0.258 | trend_plus_di_21 | 0.742 | 0.0394 | pass |
| basis_zscore_30 | basis | −0.0250 | −0.0347 | 0.0347 | 0.289 | trend_plus_di_21 | 0.711 | 0.0247 | pass |
| oi_price_divergence_30 | open_interest | +0.0103 | +0.0257 | 0.0257 | 0.330 | trend_plus_di_21 | 0.670 | 0.0172 | pass |
| btc_oi_delta_5_z30 | open_interest | +0.0046 | −0.0156 | 0.0156 | 0.171 | mr_pct_from_high_10 | 0.829 | 0.0129 | pass |
| oi_delta_30_z90 | open_interest | +0.0015 | +0.0149 | 0.0149 | 0.193 | mr_pct_from_high_10 | 0.807 | 0.0120 | pass |
| long_short_zscore_30 | long_short | −0.0003 | +0.0094 | 0.0094 | 0.226 | trend_plus_di_21 | 0.775 | 0.0073 | pass |
| btc_funding_rate_8h_impulse | funding | −0.0312 | −0.0065 | 0.0065 | 0.080 | mom_macd_hist_5_13_3 | 0.920 | 0.0060 | pass |
| funding_rate_zscore_90 | funding | −0.0426 | +0.0052 | 0.0052 | 0.379 | trend_plus_di_21 | 0.621 | 0.0032 | pass |

**Headline:** `btc_funding_spread_30_90` is the clear winner — **|IC_21bar| = 0.1053**, on par with the
strongest OHLCV-base features (`trend_adx_14` 0.121), ~3.8× the base median (0.0275), and **genuinely
orthogonal** (max base corr only 0.34, orthogonality 0.66). Its screen score (0.070) is **1.8× the
next-best** (funding z30 = 0.039). All 9 candidates ADF-pass (informational; not a gate).

**ADF (informational):** 9/9 candidates pass raw-α stationarity — expected, since funding/OI/long-short/
basis are already z-scored or differenced primitives by construction.

---

## 3. Cluster-importance / redundancy

The screen already encodes orthogonality vs the *base*; the redundancy concern *within* the orthogonal
candidates is the funding family. `funding_robustness.py` (B) gives the funding-family internal
|Spearman| matrix:

| | z30 | z90 | spread_30_90 | impulse |
|---|---:|---:|---:|---:|
| funding_rate_zscore_30 | 1.00 | **0.84** | 0.21 | 0.43 |
| funding_rate_zscore_90 | 0.84 | 1.00 | 0.28 | 0.35 |
| **btc_funding_spread_30_90** | 0.21 | 0.28 | **1.00** | 0.14 |
| btc_funding_rate_8h_impulse | 0.43 | 0.35 | 0.14 | 1.00 |

- `funding_rate_zscore_30` and `_90` are a **redundant pair** (|ρ|=0.84) — adding both is double-counting.
- **The spread is the distinct, orthogonal member** (|ρ| only 0.21/0.28 vs the raw z-scores). It encodes
  the *term-structure slope* (short-funding heat minus long-funding heat), not the funding level.
  This is exactly why we add the **spread alone**, not the family — one feature, one axis, clean attribution.

---

## 4. Recommended Optuna bounds (folded LightGBM-Master advisory)

**Keep `bounds_profile = "v1_specialist"` (max_depth 5, num_leaves 31). Change ONLY the feature set
(41 → 42).** Changing features *and* bounds at once would confound the new-feature verdict. Specific
regions (all inside `v1_specialist`):

| HP | Recommended region | Rationale (IS evidence) |
|---|---|---|
| `num_leaves` | keep profile (≤31) | 42 features still span comfortably at depth 5. |
| `max_depth` | keep profile (5) | unchanged — isolate the feature variable. |
| `min_child_samples` | keep default (favor mid–high) | the new feature has thin scattered structure; high min_child_samples remains the cheapest dispersion brake (carried from iter-002 advisory). |
| `colsample_bytree` | **0.6–1.0** | at 42 cols, 0.6 ⇒ ~25 features/tree — the lone orthogonal column is **not** reliably drawn into every tree at low colsample. If the K=5 importance shows the spread is *used but mid-rank*, recommend the K=20 confirmation nudge the lower bound up (e.g. 0.7) so the single non-OHLCV signal isn't colsample'd out. |
| `reg_alpha`/`reg_lambda` | keep default (1e-3 … 10, log) | no IS reason to tighten. |
| `learning_rate` | keep default (0.01–0.1, log) | unchanged. |
| `n_estimators` | keep default | unchanged. |
| **`training_days`** | **KEEP DEFAULT 10–500, step 10** | IMMUTABLE-by-policy; I am NOT proposing to narrow it. IS note (robustness §A): the spread's IC *strengthens* in the later IS thirds (−0.027 → −0.125 → −0.172), so a shorter training window may track the signal better — but that is exactly what the 10–500 search already explores per fold. Leave it to Optuna; do not pre-bias. |

`--n-trials` = default (35), `--slippage-bps 2`. **Risk: R2 stays OFF** (confirmed the OOS killer at
iter-003; do not re-enable). R3=ON (cutoff 0.70), R5=ON (vt_target_vol 0.3) — unchanged from the
iter-004 config. ATR TP 2.9 / SL 1.45 unchanged.

---

## 5. Expected substitution effects + trial-stability prediction

**Substitution effects (post-Phase-6 importance check, to be appended as addendum):**
- The funding spread should land **top-half** of the 42-feature importance (it was rank 4–10/48 in 3/3
  seeds at /053's pooled head, and here it has the highest candidate |IC_21bar|, near the OHLCV-base top).
  Because it is orthogonal (max base corr 0.34), it should **add** split share rather than cannibalize a
  base feature — unlike a redundant add. If the OHLCV-base ranks are largely preserved (Spearman ρ > 0.5
  vs the iter-004 importance) AND the spread enters top-half, that is the clean "new orthogonal signal"
  signature. If instead a trend feature loses rank to it, that is acceptable substitution (both encode
  positioning/trend-exhaustion).
- The spread's IC is **negative** (high relative funding heat → lower forward return) and the bucketing
  (§ robustness C) is monotone in the median: Q1 (low spread) → +1.44% median forward 21-bar return,
  Q5 (high spread) → −0.38%. This is the textbook over-leveraged-long mean-reversion read — economically
  coherent, so I expect the tree to use it as a *short/flatten* discriminator in high-funding regimes.

**Trial-stability / dispersion prediction (the falsifier's quantitative basis):**
Adding ONE orthogonal column to a 41-col base should be **dispersion-neutral-to-slightly-improving**. It
does not introduce a new redundant cluster (its max base corr is 0.34, well below the 0.70 cluster
threshold), so it cannot fragment the K studies the way redundant siblings do. **Prediction: K=5
dispersion stays in the ~35–46 band** (iter-004 K=20 was 45.5; iter-003 K=3 was 34.6). I do **not** expect
the new feature to *raise* dispersion. **Basin/lottery note: this axis is NOT a-priori basin-sensitive** —
an additive orthogonal feature does not change the Optuna training-objective domain (no labeling/ATR/
universe change). The K=5→K=20 cadence remains the correct control, and per the just-changed cadence rule,
**a both-positive K=5 screen is TENTATIVE — the K=20 confirmation is the arbiter** (iter-003's K=3 IS +0.17
flipped to K=20 IS −0.17; we now screen at K=5 to reduce that, but still confirm before merging).

---

## 6. Pre-registered falsifier (HARD, decided before the run) — iter-005

iter-005 adds `btc_funding_spread_30_90` to the 41-col base (42 cols). On the K=5 EXPLORATION backtest
vs the 41-col base anchor (iter-004: IS −0.17 / OOS +0.48, judged net of fees + 2bps/side slippage):

> **NEGATIVE if:** IS monthly Sharpe does NOT improve over the 41-col base's **−0.17** toward positive
> (i.e. stays ≤ −0.17) **AND** the funding-spread's K=5 feature-importance is **bottom-rank** (bottom
> third, rank > 28/42) — i.e. neither directional lift nor split-share. A bottom-rank INERT feature is
> **DROPPED after this one verdict** (do not re-test at higher Optuna budget — that lets Optuna overfit
> IS noise and harms OOS; established in v3 memory).

- **PROMISING if** IS improves toward/above 0 **AND** the spread lands top-half (rank ≤ 21/42) — advance
  to K=20 CONFIRMATION on the 42-col set (the merge-deciding run).
- **PARTIAL if** the spread is clearly USED (mid-rank, top-2/3) but IS stays flat/slightly-negative —
  the orthogonal family carries *some* signal but not enough alone; in that case **proceed to the next
  family in the BATCH** (iter-006) rather than re-budgeting iter-005.
- **Guardrail:** OOS must not collapse below the base's +0.48. Trade count expected to stay in the same
  ballpark (entry gate unchanged). **The K=5 screen is TENTATIVE regardless of outcome** — only the K=20
  confirmation can update `BASELINE_V1_BTCUSDT`.

---

## The BATCH — ranked sequence of K=5 EXPLORATIONs (one orthogonal family each)

Design intent: attack the single-price-factor diagnosis with the four non-OHLCV families, **best first**,
one per screen for clean attribution. All four candidates are already in the parquet (**no regen**). We
confirm only the best at K=20 later. Each screen adds its feature to the **41-col base** (not stacked on
the prior screen's add — clean one-axis attribution per the skill).

| order | iteration | add (to 41-col base) | family | \|IC_21bar\| | orthogonality | screen | regen? | rationale |
|---|---|---|---|---:|---:|---:|:--:|---|
| **1** | **iter-005** | **`btc_funding_spread_30_90`** | funding | **0.1053** | 0.661 | **0.0696** | **no** | Highest IC of any candidate (≈ best OHLCV-base feature), genuinely orthogonal, IC strengthens toward OOS, monotone economic structure, ADF-pass, already STRONGLY LEARNED in the pooled head. The single best orthogonal add. |
| 2 | iter-006 | `basis_zscore_30` | basis | 0.0347 | 0.711 | 0.0247 | no | Next-best screen score. Perp-spot basis is a *carry/funding-arb* signal distinct from the funding-spread (different primitive); 99.5% IS coverage (best of all). Was pooled-INERT at /040 but that was a *pooled* head — re-test on the BTC specialist where the OHLCV base is much leaner. |
| 3 | iter-007 | `oi_price_divergence_30` | open_interest | 0.0257 | 0.670 | 0.0172 | no | Best OI-family screen score and best-orthogonality OI feature. OI-price divergence (leverage building *against* price) is a structurally distinct flow signal. Caveat: 79.7% IS coverage (OI archive start). |
| 4 | iter-008 (if warranted) | `long_short_zscore_30` | long_short | 0.0094 | 0.775 | 0.0073 | no | Most-orthogonal candidate (max base corr 0.23) but weakest IC. Top-trader positioning crowding. Run **only if** iters 005–007 are all NEGATIVE and the team still wants to exhaust the orthogonal-family axis before pivoting (labeling/risk). Lowest priority — thin coverage (73%) and near-zero IC. |

Notes on the sequence:
- **iter-005 carries the strongest prior** by a wide margin (1.8× the next screen score) — it is the
  experiment most likely to move the IS inversion. If it is PROMISING → K=20 confirm it before running
  iter-006+ (don't burn screens once we have a confirmable candidate).
- **iter-006/007 are pre-staged but NOT auto-run** — the Engineer wires them one at a time as we go, and
  only if the prior screen doesn't yield a confirmable PROMISING. Each is a single-feature change to the
  41-col base (the same wiring pattern as iter-005).
- I deliberately **excluded the four lowest-screen candidates** (`funding_rate_zscore_90`,
  `btc_funding_rate_8h_impulse`, `btc_oi_delta_5_z30`, `oi_delta_30_z90`) from the BATCH: the z90 is a
  redundant sibling of z30 (|ρ|=0.84); the impulse was multi-seed INERT (/053→dropped /054); the OI deltas
  were BASIN-LOTTERY (/058) / weak. Re-testing prior-INERT/lottery features is the documented anti-pattern.
- `funding_rate_zscore_30` (screen 0.039) is the runner-up funding feature but is **superseded by the
  spread** for iter-005 — the spread is more orthogonal to its own family AND has 2× the IC. If iter-005
  is PROMISING and the team wants a *funding-stacking* confirmation, z30 is the natural second funding add
  (defer to a CONFIRMATION-time decision; not a separate exploration screen).

---

## iter-005 `feature_columns` (copy-pasteable, 42 cols = 41 base + 1 orthogonal add)

The Engineer changes ONLY this list (no feature-gen, no parquet regen). `btc_funding_spread_30_90` is
inserted alphabetically.

```python
V1_BTC_ORTHO_ITER005 = [
    "btc_funding_spread_30_90",   # NEW iter-005: funding term-structure slope (z30 − z90); orthogonal non-OHLCV add
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

**Handoff to Quant Research:** adopt/modify/reject. My recommendation: run iter-005 K=5 EXPLORATION with
this exact 42-col list, `bounds_profile="v1_specialist"`, `training_days` 10–500, `--n-trials 35`,
`--slippage-bps 2`, R2 OFF. Evaluate against the §6 falsifier. The BATCH (iter-006 `basis_zscore_30`,
iter-007 `oi_price_divergence_30`, iter-008 `long_short_zscore_30`) is pre-ranked for sequencing — wire
each only when the prior screen doesn't produce a confirmable PROMISING. None require regen.
