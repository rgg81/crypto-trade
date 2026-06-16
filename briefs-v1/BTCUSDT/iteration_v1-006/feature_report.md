# Feature Report — iter-v1/006 (BTCUSDT) — Phase 4 (IS-ONLY)

**Author:** Feature Engineer. **Symbol:** BTCUSDT. **Mode:** EXPLORATION screen design.
**Scope:** IS-only orthogonal (non-OHLCV) feature space scan onto the frozen 41-col OHLCV prune
`V1_BTC_PRUNED_ITER002`. All numbers below come from the committed script
`analysis/BTCUSDT/iteration_v1-006/feature_ortho_scan.py` (re-runnable; asserts `open_time <
OOS_CUTOFF_MS = 1742774400000` = 2025-03-24; OOS never touched). Outputs:
`feature_ortho_scan.csv`, `candidate_mutual_corr.csv`, `purged_cv_marginal.csv`.

IS window: 2020-01-01 .. 2025-03-23 16:00 (5727 candles, 8h). Forward label =
`log(close[t+1]/close[t])` (matches `run_baseline_v1._compute_forward_returns`); 3-bar horizon
also reported.

---

## 0. Headline finding (read this first)

**BTC's price-only edge is at the noise floor, and the funding-rate *level* z-score is the only
orthogonal family that is genuinely stronger.** Two decisive numbers:

1. **None of the 41 prune columns the model already trains on has |IS-IC| > 0.041.** Max is
   `trend_adx_14` at 0.0281; mean 0.0115; **0/41 cols clear |IC|>0.04**. The IS edge the
   specialist learns from price is statistically a coin-flip — which is exactly why IS Sharpe
   keeps inverting negative (iter-001 −0.28, iter-004 −0.17).
2. **`funding_rate_zscore_30` (|IS-IC|=0.057) and `funding_rate_zscore_90` (|IS-IC|=0.043) have
   HIGHER univariate IC than ANY of the 41 price columns**, are orthogonal to the price base
   (max |corr| 0.26 / 0.37), rank top-9/42 on cluster gain-importance, AND improve out-of-fold
   directional accuracy in purged CV. The funding *level* z-score carries signal that the price
   base does not.

Critically, the iter-005 NEGATIVE was the funding *term-structure SPREAD* (`btc_funding_spread_30_90`),
not the funding *level*. The spread is the weakest funding member in every diagnostic here
(IC 0.026, importance rank 16/42, OOF not the strongest). **iter-005 tested the wrong funding
feature.** The level z-scores were never screened.

This is **not** a clean (C). There is a real, orthogonal, model-relevant signal above the price
band. → **RECOMMENDATION (A): `funding_rate_zscore_90`.** Detail below.

---

## 1. Candidate features — economic hypothesis + lineage

| feature | family | economic hypothesis (1 line) | lineage |
|---|---|---|---|
| `funding_rate_zscore_30` | funding | Funding z (30d) measures crowding/carry of perp longs; extreme positive funding = over-leveraged longs → forward mean-reversion down (sign: negative IC). | parquet, 98.4% IS cov, ADF stationary |
| `funding_rate_zscore_90` | funding | Same crowding signal at a slower 90d baseline — less noisy, captures regime-level positioning extremes. | parquet, 98.4% IS cov, ADF stationary |
| `btc_funding_rate_8h_impulse` | funding | Single-candle funding shock (impulse) — abrupt sentiment flip; faster than the z-scores. | parquet, 98.4% IS cov |
| `btc_funding_spread_30_90` | funding | Funding term-structure SLOPE (z30−z90). **iter-005 NEGATIVE — reference only, excluded.** | parquet, 97.3% IS cov |
| `oi_delta_30_z90` | open interest | OI build/unwind (30-bar Δ, 90-bar z): rising OI + flat price = positioning fragility. | parquet, **79.7%** IS cov |
| `btc_oi_delta_5_z30` | open interest | Fast 5-bar OI delta (30-bar z): short-horizon positioning impulse. | parquet, **84.8%** IS cov |
| `oi_price_divergence_30` | open interest | OI rising while price falls (or vice versa) = divergence → reversal setup. | parquet, **79.7%** IS cov |
| `basis_zscore_30` | basis | Perp-spot basis z (30d): rich basis = long crowding → reversion. **Retired iter-040 (3× INERT in pooled pipeline) — re-eval.** | parquet, 99.5% IS cov |
| `long_short_zscore_30` | positioning | Retail long/short account ratio z (30d): contrarian crowding gauge. | parquet, **73.2%** IS cov |
| `dot_vs_btc_ret_ratio_30` | cross-asset | BTC relative strength vs DOT. | **0% IS coverage — UNAVAILABLE** |
| `eth_vs_btc_ret_ratio_30` | cross-asset | BTC relative strength vs ETH. | **0% IS coverage — UNAVAILABLE** |
| `ltc_vs_btc_ret_ratio_30` | cross-asset | BTC relative strength vs LTC. | **0% IS coverage — UNAVAILABLE** |

**Cross-asset ratios are DEAD COLUMNS in the BTC parquet.** All three are 100% null across the
entire file (IS and OOS) — they are populated only when alt parquets are joined, which the
single-symbol BTC pipeline does not do. They cannot be evaluated or used at iter-006. (And on
merit: a BTC/alt *return ratio* encodes the alt's behavior more than BTC's own forward return —
weak prior for a BTC specialist even if populated.) **Excluded.**

---

## 2. IS Information Coefficient + ADF stationarity

Spearman (`sp`) and Pearson (`pe`) IC vs forward log-return at 1-bar and 3-bar. Quintile
forward-return monotonicity (`qmono`) is a plus.

| feature | cov% | sp_IC 1bar | pe_IC 1bar | sp_IC 3bar | qmono | ADF p | verdict |
|---|---|---|---|---|---|---|---|
| **funding_rate_zscore_30** | 98.4 | **−0.0567** | −0.0507 | −0.0701 | **decr** | 0.0000 (stat) | PASS |
| **funding_rate_zscore_90** | 98.4 | **−0.0426** | −0.0437 | −0.0431 | mixed | 0.0000 (stat) | PASS |
| btc_funding_rate_8h_impulse | 98.4 | −0.0312 | −0.0513 | −0.0363 | mixed | 0.0000 (stat) | WEAK (IC<0.04) |
| basis_zscore_30 | 99.5 | −0.0250 | −0.0207 | −0.0430 | mixed | 0.0000 (stat) | PASS (IC borderline) |
| oi_price_divergence_30 | 79.7 | +0.0103 | +0.0031 | +0.0137 | mixed | 0.0000 (stat) | WEAK |
| btc_oi_delta_5_z30 | 84.8 | +0.0046 | +0.0014 | −0.0176 | mixed | 0.0000 (stat) | WEAK (near-zero IC) |
| oi_delta_30_z90 | 79.7 | +0.0015 | +0.0062 | −0.0052 | mixed | 0.0000 (stat) | WEAK (near-zero IC) |
| long_short_zscore_30 | 73.2 | −0.0003 | +0.0021 | −0.0035 | mixed | 0.0000 (stat) | WEAK (zero IC) |
| _btc_funding_spread_30_90 (ref)_ | 97.3 | −0.0260 | −0.0230 | −0.0410 | mixed | — | EXCLUDED (iter-005 NEG) |

**Context band (the price signal in use):** 41-col prune univariate |IS-IC| max=0.0281, mean=0.0115,
0/41 > 0.04. → `funding_rate_zscore_30` (0.057) and `funding_rate_zscore_90` (0.043) are the only
features in the entire search that exceed the strongest price column. `funding_rate_zscore_30` has
a clean monotone-decreasing quintile structure (forward return falls as funding-z rises = crowding
reversion). All candidates are ADF-stationary (z-scores by construction) — informational, not
blocking.

---

## 3. Redundancy / cluster-importance

**Redundancy vs the 41-col prune (max |Pearson|; want LOW = orthogonal):**

| feature | max\|corr\| vs prune | nearest prune col |
|---|---|---|
| funding_rate_zscore_30 | 0.259 | trend_plus_di_21 |
| **funding_rate_zscore_90** | 0.370 | trend_plus_di_21 |
| btc_funding_rate_8h_impulse | 0.087 | mom_macd_hist_5_13_3 |
| oi_price_divergence_30 | 0.329 | trend_supertrend_7_3 |
| basis_zscore_30 | 0.339 | trend_plus_di_21 |
| long_short_zscore_30 | 0.242 | trend_plus_di_21 |
| btc_oi_delta_5_z30 | 0.175 | mr_pct_from_high_10 |

All candidates are orthogonal (max |corr| ≤ 0.37) — none is algebraically redundant with the price
base. funding_rate_zscore_90's 0.37 vs `trend_plus_di_21` is the highest but still well clear of a
redundancy threshold (≥0.7).

**Mutual correlation (cluster orthogonality):** the two funding z-scores are 0.78 correlated with
each other (same crowding factor at different windows) — they are ONE cluster, not two
orthogonal signals. Funding vs OI clusters are near-orthogonal (z30↔oi_price_div 0.05; z90↔oi
0.10). Funding↔basis 0.28–0.31 (both capture long-crowding). This matters for the cluster
recommendation in §6.

**Marginal cluster gain-importance (small IS LGBM, [41 prune + candidate], rank of 42):**

| feature | gain rank /42 | gain % | read |
|---|---|---|---|
| btc_funding_rate_8h_impulse | 5 | 5.35 | top — but weak IC + 0.087 corr (mostly own-variance) |
| funding_rate_zscore_90 | 8 | 4.15 | top quartile, IC-backed |
| oi_delta_30_z90 | 8 | 3.64 | top quartile, but near-zero IC |
| funding_rate_zscore_30 | 9 | 3.91 | top quartile, strongest IC |
| oi_price_divergence_30 | 9 | 3.45 | top quartile, weak IC |
| long_short_zscore_30 | 13 | 2.86 | mid |
| btc_oi_delta_5_z30 | 14 | 2.94 | mid |
| basis_zscore_30 | 18 | 2.65 | bottom-half — consistent with iter-040 INERT prior |

None is bottom-third INERT, but `basis_zscore_30` is the weakest by gain (rank 18) — its
re-evaluation **confirms the iter-040 retirement prior**: it carries IC borderline but the tree
deprioritizes it. Funding z-scores are the highest IC-backed members.

---

## 4. The decisive test — purged forward-chaining CV (marginal OOF lift)

Univariate IC is exactly what misled iter-005 (the funding spread had IC and still degraded IS
inside the bagged specialist — the documented failure mode: "high univariate IC does not survive
inside the bagged specialist"). So the load-bearing metric here is whether the candidate helps the
**model out-of-fold**: 5 forward-chaining folds, 3-bar embargo, 1-bar label, IS-only.

| config | OOF dir_acc | Δ vs prune-only | OOF R² | Δ R² |
|---|---|---|---|---|
| **PRUNE-ONLY (41 cols)** | 0.5068 | — | −0.0949 | — |
| + btc_oi_delta_5_z30 | 0.5186 | **+0.0118** | −0.0883 | +0.0066 |
| + **funding_rate_zscore_90** | **0.5173** | **+0.0105** | −0.0847 | **+0.0102** |
| + funding_rate_zscore_90 + oi_price_divergence_30 | 0.5162 | +0.0094 | −0.0863 | +0.0086 |
| + funding_rate_zscore_30 + funding_rate_zscore_90 | 0.5160 | +0.0092 | −0.0906 | +0.0044 |
| + btc_funding_rate_8h_impulse | 0.5142 | +0.0074 | −0.0874 | +0.0076 |
| + funding_rate_zscore_30 | 0.5127 | +0.0059 | −0.0899 | +0.0050 |
| + oi_delta_30_z90 | 0.5127 | +0.0059 | −0.0823 | +0.0126 |
| + oi_price_divergence_30 | 0.5112 | +0.0044 | −0.0838 | +0.0111 |
| + long_short_zscore_30 | 0.5109 | +0.0042 | −0.0838 | +0.0060 |
| + basis_zscore_30 | 0.5031 | **−0.0037** | −0.0881 | +0.0068 |

Reads:
- **Prune-only OOF dir_acc is 0.5068 (R²=−0.095)** — the price-only model barely beats a coin flip
  and has *negative* OOF R² (worse than predicting the mean). This is the quantitative root of the
  inverted-IS problem: there is almost nothing for the specialist to learn from price alone.
- **`funding_rate_zscore_90` is the best dual-signal:** +0.0105 dir_acc AND the best R² lift among
  single non-OI features (+0.0102), AND it has univariate IC (0.043). It improves the model on the
  linear axis (IC), the gain-importance axis (rank 8), AND the OOF-generalization axis (dir_acc &
  R²) — three independent confirmations. This is the profile that survived nowhere in iter-005.
- **`btc_oi_delta_5_z30` has the single largest dir_acc lift (+0.0118) but near-ZERO univariate IC
  (0.0046)** — its lift is purely non-linear/interaction. That is higher-variance (depends on the
  tree finding the interaction) and harder to reason about economically. Not the safe first probe.
- **`basis_zscore_30` is the only candidate that DEGRADES dir_acc (−0.0037)** — independent
  confirmation of the iter-040 3× INERT retirement. Do not re-screen basis.
- **The funding z30+z90 stack does NOT beat z90 alone (+0.0092 < +0.0105)** — because the two are
  0.78 correlated (one factor). Stacking is redundant and dilutes. Pick the better single member.

---

## 5. Recommended Optuna bounds + trial-stability prediction

**Bounds profile:** keep `v1_specialist` (max_depth 5, num_leaves 31), unchanged. With only 42
features and a noise-floor signal, do NOT widen the tree — wider trees overfit IS noise and worsen
OOS (the documented "INERT feature at higher budget harms OOS" failure mode). Recommended regions
for the EXPLORATION screen (K=3, n_trials=35):

| param | recommended region | rationale (IS evidence) |
|---|---|---|
| `num_leaves` | 15–31 (keep profile) | 42 features, OOF R²<0; complexity must stay capped |
| `min_child_samples` | 40–120 (lean high) | noise-floor signal → demand more samples per leaf to avoid fitting funding-z outliers |
| `colsample_bytree` | 0.6–0.9 | with 1 new strong feature among 42, do not let colsample drop so low the funding col is starved |
| `reg_alpha` / `reg_lambda` | 0.0–5.0 / 0.0–10.0 | regularize toward the few real signals |
| `learning_rate` | 0.01–0.08 | unchanged |
| `n_estimators` | 100–400 | unchanged |
| **`training_days`** | **keep 10–500, step 10** (do NOT tighten) | funding regimes shift (2021 bull crowding vs 2022 deleveraging vs 2024–25); the crowding signal's payoff is regime-dependent, so the specialist needs the freedom to pick short OR long windows. No IS evidence to tighten. |

**Trial-stability / basin prediction.** The baseline already shows HIGH bagging dispersion (K=20
σ=49.46; iter-005 K=5 σ=40.05) — BTC is structurally basin-sensitive because the price signal is a
coin-flip and the 20 studies disagree. Adding ONE IC-backed orthogonal feature (funding_rate_zscore_90)
should *reduce* per-candle disagreement modestly (a real signal gives the studies something to
agree on), but I predict dispersion stays elevated (>35 at K=3). **Plan the cadence accordingly:**
the K=3 EXPLORATION verdict is TENTATIVE per the basin-lottery vigilance rule; a both-positive K=3
must be confirmed at K=20 before any merge claim (this is exactly the iter-003→iter-004 lesson:
K=3 +0.17 IS evaporated to −0.17 at K=20). Do not over-read a single K=3 screen.

---

## 6. Expected substitution effects + coherence prediction

**Substitution prediction (post-Phase-6 addendum will check):** funding_rate_zscore_90 is 0.37
correlated with `trend_plus_di_21` and 0.28–0.37 with the other trend/DI prune cols. I expect it to
**partially substitute the trend-strength block** (trend_plus_di_21, trend_adx_7/14) — those are the
prune cols with the highest (still tiny) price IC, and funding-z is a cleaner crowding proxy for the
same "is the move exhausted" question. If the screen works, expect funding_rate_zscore_90 to land in
the top-8 of the importance CSV and the +DI/ADX cols to lose a few points of split share. If
funding_rate_zscore_90 lands rank-bottom (≈40/42) with the trend block unchanged, it was INERT and
the screen is NEGATIVE-INERT (drop it, do not retest at higher budget).

**Why (A) single feature, not (B) cluster.** The two funding z-scores are one factor (0.78 corr);
stacking them does not beat z90 alone in OOF (§4). The genuinely-orthogonal partner would be an OI
feature, but the best OI lift (`btc_oi_delta_5_z30`, +0.0118 dir_acc) is pure non-linear with
near-zero IC — bundling a zero-IC non-linear feature with a real-IC feature at single-seed
EXPLORATION is precisely the stacking-overfit risk the methodology warns against (v3
"engineered features don't stack at single-seed"). **Screen ONE clean dual-signal feature first.**
If funding_rate_zscore_90 confirms PROMISING at K=3 and survives K=20, the natural iter-007 probe is
to add the orthogonal OI partner (oi_price_divergence_30 or btc_oi_delta_5_z30) as a SECOND feature
— but that is a future iteration, tested one at a time.

---

## RECOMMENDATION

**(A) — add the single feature `funding_rate_zscore_90` to the 41-col prune (→ 42 cols).**

Exact column name for the iter-006 EXPLORATION screen: **`funding_rate_zscore_90`**
(base set = `V1_BTC_PRUNED_ITER002` + `("funding_rate_zscore_90",)`).

Rationale in one paragraph: It is the only candidate that clears every diagnostic simultaneously —
univariate IS-IC 0.043 (above the entire 41-col price band, max 0.028), orthogonal to the prune
(max |corr| 0.37), top-quartile cluster gain-importance (rank 8/42), AND the best dual-signal OOF
lift in purged CV (+0.0105 dir_acc, +0.0102 R², from a prune-only baseline that is a coin flip with
negative R²). Crucially it is a *different feature* from the iter-005 NEGATIVE: iter-005 tested the
funding term-structure SPREAD (rank 16/42, weakest funding member); the funding *level* z-score was
never screened and is materially stronger on every axis. The economic story is clean: 90-day funding
z = perp-long crowding/carry extreme → forward mean-reversion (negative IC). I prefer the 90d window
over the 30d (which has higher raw IC, 0.057) because the 90d gives the better OOF generalization
(+0.0105 vs +0.0059 dir_acc) — the 30d's extra IC is partly higher-frequency noise the model
overfits. Do NOT screen a cluster: the funding z-scores are one factor (0.78 corr), and the only
orthogonal partner (OI) is a zero-IC non-linear feature that should not be stacked at single-seed.

**Predicted behavioral effect on IS.** This is a noise-floor problem, so I am honest about the
ceiling: one feature with OOF dir_acc lift +0.0105 (0.5068→0.5173) is a small-but-real edge.
Mapped through a bagged signed-weight specialist it should lift IS Sharpe by roughly **+0.2 to
+0.4** — enough to move the prune-only K=20 IS from −0.17 toward the ~0/slightly-positive zone, but
**I do NOT confidently predict a positive-coherent IS at K=3**. The most likely K=3 outcome is IS in
[−0.10, +0.20] with OOS staying positive. A genuinely both-positive coherent profile (IS>0, OOS>0,
OOS/IS ≥0.5) is the upside case, not the base case — funding is one feature, not a regime fix.

**Pre-registered coherence falsifier.** The iter-006 screen is **NEGATIVE** if ANY of:
1. The profile stays INVERTED — IS Sharpe < 0 while OOS Sharpe > 0 (OOS/IS ratio negative), the
   recurring BTC artifact. An inverted profile is an automatic NEGATIVE no matter how high OOS prints
   (per the generalization-coherence gate).
2. `funding_rate_zscore_90` lands importance-rank ≈ bottom-third (≥ rank 38/42) in the run's
   feature-importance CSV with the trend/+DI block unchanged → INERT (learned-around, not learned).
   Drop it; do NOT retest at higher Optuna budget.
3. IS Sharpe regresses materially below the prune-only K-matched anchor (worse than iter-004 K=20
   −0.17 at K=20, or worse than ≈0 at K=3) — i.e. the feature drags IS the way the funding *spread*
   did at iter-005.

Positive (PROMISING) outcome: a both-positive coherent profile at K=3 (IS>0 AND OOS>0, ratio ≥0.5)
with funding_rate_zscore_90 in the top-half of importance → tentative PROMISING, escalate to a K=20
CONFIRMATION (ping user first) to isolate small-K lottery before any merge claim.

**If QR prefers a non-feature axis instead:** the honest fallback is not basis/OI (basis is INERT-
confirmed; OI is zero-IC non-linear) but a **label/horizon or regime axis**. The 3-bar forward IC is
consistently larger than 1-bar for the funding family (z30: 0.070 vs 0.057; basis: 0.043 vs 0.025),
which hints BTC's edge lives at a slightly longer horizon than the current 1-candle label — worth a
QR look as the iter-007 alternative if iter-006 confirms funding is the carrier but the 1-bar label
caps the lift.

---

### Post-Phase-6 addendum (to be appended after the backtest)
_Reserved._ Will compare the run's `feature_importance_*` CSV against the §6 substitution
prediction: did `funding_rate_zscore_90` gain split share (carried signal) or land rank-bottom
(inert), and did the trend/+DI block lose share as predicted.
