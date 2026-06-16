# Feature Report — iter-v1/014 (BTCUSDT) — Phase 4 (Technical-indicator stability screen, IS-ONLY)

**Author:** Feature Engineer. **Symbol:** BTCUSDT. **Interval:** 8h (sacred). **Scope:**
Phase 4 — wide technical-indicator inventory + cross-IS-sub-period **stability** selection,
IS-ONLY. **Objective: SHARPE (risk-adjusted).** **TARGET = both-positive (IS>0 AND OOS>0).**

**User mandate (2026-06-16):** "grind it, try different tech indicators." The campaign lesson
(iter-005..012) is that **high IS-IC does NOT imply OOS generalization** — the 19-col HYBRID set
gives +0.39 IS at N=9 but the directional edge inverts IS-bull (+31%) → OOS-bull (−22%)
(diary-012). So the iter-014 selection criterion is NOT peak IS-IC. It is **cross-IS-sub-period
SIGN+MAGNITUDE STABILITY** of each indicator's univariate IC vs the forward return.

All numbers come from two committed, re-runnable, IS-only scripts under
`analysis/BTCUSDT/iteration_v1-014/`. Each hard-filters `open_time < OOS_CUTOFF_MS = 1742774400000`
(2025-03-24) and asserts `df["open_time"].max() < OOS_CUTOFF_MS` BEFORE any forward quantity; the
forward log-return is computed AFTER the IS filter (tail rows NaN-mask — no OOS candle in the
frame); features are read as-is from `data/features/BTCUSDT_8h_features.parquet` (already past-only
by `features_v1`); the purged walk-forward trains only on candles strictly before each monthly test
window minus an embargo ≥ label horizon. Nothing is fit/selected/calibrated against OOS; OOS rows
are never read. `src/`, the runner, and OOS are UNTOUCHED.

- `subperiod_ic_stability.py` → `subperiod_ic_stability.csv` (wide net: 182 candidates × 11 IS
  sub-periods, univariate Spearman IC vs N=9 forward log-return, frac-same-sign + dispersion +
  stability score)
- `stable_set_cv.py` → `stationary_stable_survivors.csv`, `stable_clusters.csv`,
  `stability_selected_set.csv`, `stable_vs_19col_cv.csv` (ADF stationarity gate → redundancy
  cluster → purged-CV directional let-run proxy, stable set vs 19-col, at N=9 and N=21)

IS window: 2020-01-01 .. 2025-03-23 (5727 8h candles, 1909 days, **11 ~6-month sub-periods**).
Stability metric: per-sub-period IC; `frac_same_sign` (fraction of sub-periods whose IC matches the
full-IS-IC sign); `ic_dispersion` (std across sub-periods); `stability_score = mean(|IC|) ×
frac_same_sign`.

---

## 0. Headline finding (read this first)

**A feature set selected for univariate-IC cross-sub-period STABILITY does NOT generalize better
than the IS-IC-selected 19-col set — it generalizes WORSE. The reason is mechanistic, not a tuning
miss: the indicators with the most sub-period-stable IC are VOLATILITY-MAGNITUDE features that
predict |forward move|, not direction. They are inert for the directional model the campaign is
building.** Three decisive, IS-only numbers:

1. **Among 182 technical-indicator candidates, exactly ONE has the same-sign IC in ALL 11 IS
   sub-periods AND a same-sign most-recent sub-period: `vol_natr_7` (a volatility level).** NO
   member of the current 19-col set is sign-consistent across all sub-periods (`frac with
   all-6-same-sign = 0.000`; median frac_same_sign 0.636). Stable *univariate direction* signals
   essentially do not exist on BTC 8h — confirming, quantitatively and family-wide, the iter-011
   structural diagnosis.

2. **The top-stability candidates are not directional.** `vol_natr_7 / vol_garman_klass_20 /
   vol_parkinson_20 / vol_bb_bandwidth_30 / interact_natr_x_adx` have IC vs **|forward return|**
   that is **4–5× larger** than their IC vs **signed** forward return (e.g. garman_klass_20: IC_|fwd|
   +0.233 vs IC_signed +0.051). Their "stable IC vs signed return" is largely the artifact of BTC's
   mild positive IS drift (high-vol bins coincide with the drift). They encode *how big* the next
   move is, **not which way** — useless to a sign(prediction) directional book.

3. **Purged-CV directional proxy: the 16-col stability-selected set is WORSE than the 19-col on
   every stability axis.** At N=9: sub-period `frac_pos` 0.556 (vs **0.667**), dispersion **1.358**
   (vs 0.834), worst sub-period −1.281 (vs −0.302), and — decisively — the **most-recent sub-period
   (the iter-011 OOS-fragility fingerprint) is MORE negative: −0.855 vs −0.170.** At N=21 it is also
   worse on dispersion/worst/recent. Stability-by-univariate-IC made the directional model LESS
   sub-period-stable, because it swapped genuine (if regime-bound) directional content for
   vol-magnitude noise the tree can't turn into a sign.

→ **RECOMMENDATION: NEGATIVE for the "stability-selected technical-indicator set" axis. Do NOT
swap the 19-col set for a univariate-IC-stability-selected set — it predictably widens, not
narrows, the IS→OOS gap.** The genuinely directional stable indicators (`trend_adx_*`,
`btc_funding_spread_30_90`, `vol_taker_buy_ratio*`) are ALREADY in the 19-col set or are window
twins of its members (cluster 15/17 evidence). There is no untapped technical indicator that is
both directional AND sub-period-stable on BTC 8h. **The honest implication: this is the same
structural wall iter-011/012 hit, re-confirmed from the feature side — the directional edge is
regime-bound and no off-the-shelf indicator escapes it.** Keep the incumbent 19-col set; the next
lever must be NON-directional (vol/breakout target) or an explicitly distribution-shift-robust
architecture, not a different indicator basket. Full rationale + falsifier in §5.

---

## 1. Wide-net inventory — technical-indicator families surveyed (185 columns)

`subperiod_ic_stability.py` inventory pass. The parquet has 235 columns; 185 distinct candidate
indicators were screened across 17 families (19 of them already in the current set). Concrete
columns by family:

| family | n | representative columns |
|---|---:|---|
| oscillator_stoch | 8 | `mom_stoch_k/d_{5,9,14,21}` |
| oscillator_willr | 3 | `mom_willr_{7,14,21}` |
| oscillator_roc_mom | 10 | `mom_roc_{3,5,10,15,20,30}`, `mom_mom_{5,10,15,20}` |
| oscillator_rsi | 6 | `mom_rsi_{5,7,9,14,21,30}` |
| trend_adx_di | 9 | `trend_adx_{7,14,21}`, `trend_plus/minus_di_{7,14,21}` |
| trend_aroon | 5 | `trend_aroon_osc_{14,25,50}`, `trend_aroon_up/down_14` |
| trend_macd | 7 | `mom_macd_line/hist/signal_{8_21_5, 12_26_9, 5_13_3}` |
| trend_structure | 11 | `trend_ema_cross_*`, `trend_sma_cross_*`, `trend_supertrend_*`, `trend_psar_dir/af` |
| vol_bb | 12 | `vol_bb_bandwidth_{10,15,20,30}`, `vol_bb_pctb_*`, `mr_bb_pctb_*` |
| vol_realized | 17 | `vol_atr_*`, `vol_natr_*`, `vol_garman_klass_*`, `vol_parkinson_*`, `vol_hist_*` |
| vol_range_spike | 6 | `vol_range_spike_{12,24,36,48,72,96}` |
| volume_flow | 23 | `vol_obv`, `vol_ad`, `vol_cmf_*`, `vol_mfi_*`, `vol_taker_buy_ratio*`, `vol_volume_rel/pctchg_*`, `vol_vwap`, `mr_dist_vwap` |
| mean_reversion | 21 | `mr_zscore_*`, `mr_rsi_extreme_*`, `mr_pct_from_high/low_*`, `mr_dist_sma_*` |
| statistical | 16 | `stat_return_*`, `stat_autocorr_lag{1,5,10}`, `stat_skew_*`, `stat_kurtosis_*` |
| regime_micro | 15 | `hurst_100`, `regime_momentum_signed_5d`, `rev_*`, `ent_shannon_*`, `ent_volume_20`, `cusum_*`, `basis_zscore_30`, `long_short_zscore_30` |
| funding_oi_cross | 10 | `funding_rate_zscore_{30,90}`, `btc_funding_spread_30_90`, `btc_funding_rate_8h_impulse`, `oi_*`, `{eth,ltc,dot}_vs_btc_ret_ratio_30` |
| interaction | 6 | `interact_{rsi,stoch,natr}_x_adx`, `interact_rsi_x_natr`, `interact_ret1_x_natr/ret3` |

This is a genuinely wide net — every standard oscillator, trend, volatility, volume/flow,
mean-reversion, statistical, regime, and funding/OI family available is included, well beyond the
19-col hybrid.

---

## 2. IS sub-period IC stability — the 19-col baseline vs the field (+ ADF)

`subperiod_ic_stability.py`. Univariate Spearman IC vs N=9 forward log-return, per ~6-month
sub-period. The decisive columns are `frac_same_sign` (sign consistency across the 11 sub-periods)
and `ic_dispersion`.

### 2a. The current 19-col set on the stability metric (the baseline-to-beat)

| feature | ic_full | frac_same_sign | mean\|IC\| | ic_disp | recent_ic | recent_ok | stability |
|---|---:|:--:|---:|---:|---:|:--:|---:|
| trend_adx_14 | +0.0877 | 0.818 | 0.143 | 0.151 | +0.116 | ✓ | 0.1173 |
| btc_funding_spread_30_90 | −0.0699 | 0.727 | 0.131 | 0.142 | +0.274 | ✗ | 0.0951 |
| vol_taker_buy_ratio_sma_5 | +0.0737 | 0.818 | 0.103 | 0.091 | +0.008 | ✓ | 0.0839 |
| trend_adx_7 | +0.0631 | 0.727 | 0.114 | 0.144 | +0.045 | ✓ | 0.0829 |
| vol_garman_klass_10 | +0.0535 | 0.909 | 0.088 | 0.062 | +0.082 | ✓ | 0.0796 |
| stat_kurtosis_20 | −0.0458 | 0.636 | 0.095 | 0.106 | −0.212 | ✓ | 0.0603 |
| stat_autocorr_lag1 | +0.0267 | 0.636 | 0.095 | 0.109 | +0.136 | ✓ | 0.0601 |
| … (remaining 12) … | | mean 0.651 | | | | | mean 0.058 |

**19-col SUMMARY: mean frac_same_sign 0.651, median 0.636, `frac with all-sub-periods-same-sign =
0.000`.** Every directional member of the deployed set flips IC sign in at least 2 of 11 IS
sub-periods. This is the IS-visible fingerprint of the regime-bound overfit — and it is a property
of the 19-col set by construction (it was selected on peak IS-IC, §iter-009).

### 2b. The full-field "sign-consistent club" — 1 member, and it is not directional

| feature | in_19col | ic_full | mean\|IC\| | ic_disp | ADF p | stability |
|---|:--:|---:|---:|---:|---:|---:|
| **vol_natr_7** | no | +0.0469 | 0.079 | **0.049** | 0.000 | 0.0794 |

`vol_natr_7` is the ONLY one of 182 candidates with the same IC sign in **all 11** sub-periods AND a
same-sign most-recent sub-period, and it has the lowest IC dispersion of any candidate (0.049). It
is a normalized-ATR **volatility level** — a magnitude, not a direction (see §3). ADF p ≈ 0 (all
stable candidates are stationary except the dropped level series, §3).

---

## 3. Stationarity gate + the mechanism (why stable ≠ directional)

`stable_set_cv.py` Stage A. Of the 62 candidates with `frac_same_sign ≥ 0.727`, **`vol_ad` was
dropped as ADF-nonstationary (p=0.095)** — a cumulative accumulation/distribution LEVEL series whose
apparent "stable IC" is a spurious-regression artifact (it trends with price). `vol_vwap` and
`vol_obv` were likewise nonstationary (p=0.73 / 0.69) and never entered the ≥0.727 pool. **This is
the econometric guardrail that prevents mistaking a level-trend for a cross-regime relationship.**

**Mechanism test (signed vs absolute forward return IC):** the top-stability survivors predict
|move|, not direction.

| feature | IC vs **signed** fwd | IC vs **\|fwd\|** | verdict |
|---|---:|---:|---|
| vol_natr_7 | +0.047 | **+0.220** | VOL(\|move\|) |
| vol_garman_klass_20 | +0.051 | **+0.233** | VOL(\|move\|) |
| vol_parkinson_20 | +0.048 | **+0.229** | VOL(\|move\|) |
| vol_bb_bandwidth_30 | +0.045 | **+0.164** | VOL(\|move\|) |
| interact_natr_x_adx | +0.080 | **+0.166** | VOL(\|move\|) |
| vol_taker_buy_ratio_sma_50 | +0.060 | −0.003 | directional |
| trend_adx_14 | +0.088 | +0.042 | directional |
| trend_adx_21 | +0.086 | +0.044 | directional |
| btc_funding_spread_30_90 | −0.070 | +0.001 | directional |

The "stable" club is dominated by realized-vol estimators whose IC vs |forward move| is 4–5× their
IC vs signed return. The only genuinely **directional** stable survivors are `trend_adx_*`,
`btc_funding_spread_30_90`, and `vol_taker_buy_ratio_sma_*` — **all already in the 19-col set or
window twins of its members** (see cluster table below).

---

## 4. Redundancy cluster + the directional-proxy head-to-head

`stable_set_cv.py` Stage B/C. 61 stationary stable survivors → **23 clusters** (Spearman |corr|>0.60
merged). The two giant clusters confirm the redundancy:

- **Cluster 17 (16 members):** the entire realized-vol-|move| family — `interact_natr_x_adx,
  vol_parkinson_{10,20}, vol_garman_klass_{10,20,30}, vol_natr_{7,14,21}, vol_bb_bandwidth_{10,15,20,30},
  vol_hist_{5,10,20}`. One vol-magnitude axis dressed 16 ways.
- **Cluster 3 (14 members):** the oscillator/DI/stoch mean-reversion family — `mr_pct_from_high_*,
  mom_stoch_*, trend_minus_di_*, vol_mfi_21, mr_rsi_extreme_7`. One overbought/oversold axis.
- **Cluster 15:** `trend_adx_14 | trend_adx_21`; **Cluster 10:** the 4 `vol_taker_buy_ratio_sma_*`
  windows. The directional content is concentrated in ADX + taker-flow + funding — exactly the
  19-col anchors.

**Stage C — purged-CV directional let-run proxy (seed 42, full both-side book; headline =
cross-sub-period stability):**

| set | n_feats | N | full Sₐₙₙ | sub-period frac_pos | dispersion | worst | **most-recent** |
|---|---:|---:|---:|:--:|---:|---:|---:|
| **iter009_19col** | 19 | 9 | +1.857 | **0.667** | **0.834** | **−0.302** | **−0.170** |
| stable_selected | 16 | 9 | +1.108 | 0.556 | 1.358 | −1.281 | −0.855 |
| iter009_19col | 19 | 21 | +1.137 | 0.444 | 1.390 | −2.156 | −0.806 |
| stable_selected | 16 | 21 | +1.033 | 0.556 | **1.975** | **−3.804** | **−3.804** |

The stability-selected set LOSES on every axis at N=9 (lower frac_pos, ~1.6× higher dispersion, far
worse worst- and most-recent sub-period). At N=21 it ties frac_pos but blows out dispersion/worst.
**Per-sub-period N=9 detail** (the OOS-fragility fingerprint is the last row):

| sub-period | 19col Sₐₙₙ | stable Sₐₙₙ |
|---|---:|---:|
| 2021-01 | +0.461 | −0.511 |
| 2021-07 | +2.348 | +1.632 |
| 2022-01 | +0.791 | −1.281 |
| 2022-07 | −0.275 | −1.110 |
| 2023-01 | +0.523 | +2.230 |
| 2023-07 | +0.499 | +0.560 |
| 2024-01 | +1.133 | +1.826 |
| 2024-07 | −0.302 | +0.962 |
| **2025-01 (nearest OOS)** | **−0.170** | **−0.855** |

The stable set is MORE negative in the most-recent IS sub-period — the single row that iter-011
showed pre-prints OOS. By the campaign's own stability criterion, the stable set is the WORSE OOS
bet.

---

## 5. RECOMMENDATION — NEGATIVE on the indicator-swap axis; KEEP the 19-col set

**Decisive choice: do NOT replace the 19-col HYBRID set with a univariate-IC-stability-selected
technical-indicator set.** The wide net was cast (185 indicators, 17 families) and the result is
clean and falsifiable: **no off-the-shelf technical indicator on BTC 8h is both directional AND
sub-period-stable.** The stable ones are vol-magnitude (predict |move|, inert for a directional
book); the directional ones flip sign across regimes (frac_same_sign ≤ 0.82, none all-11) and are
already in the incumbent set. A set built from the stable survivors empirically WIDENS the IS→OOS
fragility fingerprint (§4).

### Recommended column list (UNCHANGED — the incumbent 19-col HYBRID set)
`trend_adx_7, vol_garman_klass_10, vol_atr_5, vol_taker_buy_ratio, vol_taker_buy_ratio_sma_5,
vol_mfi_7, mom_rsi_9, stat_autocorr_lag1, mr_pct_from_high_5, vol_cmf_10, ent_shannon_10,
trend_adx_14, trend_supertrend_14_3, btc_funding_spread_30_90, funding_rate_zscore_30,
stat_autocorr_lag5, vol_range_spike_72, mr_rsi_extreme_14, stat_kurtosis_20`

It remains the most sub-period-stable DIRECTIONAL set available: it concentrates the only genuinely
directional stable signals (ADX windows, funding tilt, taker-flow) that the field search surfaced,
and it beats every stable-selected alternative on frac_pos / dispersion / most-recent-sub-period
(§4). No indicator swap improves it.

### Per-column sub-period IC consistency
See §2a table — every directional member has frac_same_sign 0.55–0.82 (none 1.00); the highest are
`trend_adx_14` (0.818), `vol_taker_buy_ratio_sma_5` (0.818), `vol_garman_klass_10` (0.909, but
vol-magnitude). The set's mean frac_same_sign 0.651 is at the directional ceiling for BTC 8h.

### Redundancy structure
The field clusters into 23 groups; the 19-col set already samples the directional clusters
(ADX/cluster-15, taker-flow/cluster-10, funding/cluster-20, vol-magnitude/cluster-17 via
garman_klass_10, statistical/autocorr). No un-sampled directional cluster exists to add.

### Predicted effect on the IS→OOS gap
**A stability-selected set will NOT generalize better — it generalizes measurably worse** (§4:
recent sub-period −0.855 vs −0.170; dispersion 1.358 vs 0.834). The gap is not a feature-selection
artifact; it is the structural regime-binding of BTC 8h direction (iter-011/012), and re-confirmed
here from the feature side: the stable-IC indicators are non-directional, so no indicator basket can
close the directional gap.

### Trial-stability / basin prediction
The univariate-IC sign pattern is data-deterministic (iter-011 showed the sub-period signs are
seed-stable). The stable-vs-19col proxy ranking is robust to seed because the gap is driven by
feature CONTENT (directional vs vol-magnitude), not basin draw. **No basin-lottery rescue is
available** — more seeds average variance, not the systematic vol-magnitude/direction mismatch.

### Pre-registered FALSIFIER (this NEGATIVE is overturned only if):
1. A backtest of the **stable-selected 16-col set** (if QR insists on testing it) produces a
   most-recent-IS-sub-period Sharpe **less negative than the 19-col's −0.170** AND OOS Sharpe > 0 —
   i.e. the directional proxy's stability ranking is contradicted by the real bagged specialist. (I
   predict it will not: the proxy and the |move|-vs-signed mechanism both point the same way.)
2. OR a candidate technical indicator is found with **frac_same_sign = 1.00 across all 11
   sub-periods AND IC_signed ≥ 1.5 × IC_|fwd|** (genuinely directional + fully sign-stable). The
   182-candidate sweep found ZERO such column — if one is constructed (e.g. a composed
   regime×direction feature, NOT off-the-shelf), the axis reopens.

If neither fires, the "different technical indicators" axis is FALSIFIED for BTC 8h directional, and
the only honest paths are: (A) a **non-directional target** (predict |move| / breakout / vol — the
stable signal that DOES exist: the vol-magnitude cluster has frac_same_sign up to 1.00 and
IC_|fwd| +0.22), or (B) accept BTC 8h directional as overfit-prone and pivot symbol/track. Both are
strategic calls for QR + the user, surfaced here with the data.

### Note on the |move|-target opportunity (flagged for QR, NOT this iteration's recommendation)
The one thing this screen found that IS sub-period-stable is **volatility magnitude**:
`vol_natr_7` (frac_same_sign 1.00), `vol_garman_klass_20` (IC_|fwd| +0.233). If the campaign pivots
from a directional target to a **|move|/breakout/vol target**, this stable vol-magnitude cluster is
the IS-validated feature core for it. That is a TARGET-redesign axis (QR Phase 1/2), not a
feature-swap — I flag it as the highest-leverage forward direction the data supports.

---

## [Post-Phase-6 addendum — to be appended after any real backtest]

_Reserved: if QR elects to backtest the stable-selected 16-col set to test falsifier (1), append the
feature-importance interpretation here — did the vol-magnitude features land rank-bottom (confirming
the §3 directional-inertness prediction), and did the most-recent-sub-period Sharpe come in worse
than the 19-col as predicted._
