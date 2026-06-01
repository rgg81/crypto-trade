# LightGBM Master Advisor — iter-v1/049 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1 (cycle-6 EXPLORATION 4/10).
- **Axis**: `feature-family` — NON-KLINE-CLASS defense post-/048 NEG-CLEAN-PRE-EDA (trade_count_zscore_30 |IC|=0.9063 vs `vol_volume_rel_20` — second consecutive ABORT).
- **Primary feature**: `long_short_zscore_30` = 30-bar (10-day) rolling z-score of `topLongShortAccountRatio` (Binance Futures positioning sentiment, 4h→8h aggregated to candle close). **Account-level top-trader long/short census; primitive class has ZERO representation in V1_FEATURE_COLUMNS_PRUNED (44 features, all OHLCV+funding+OI+calendar).**
- **Backup feature** (S3 if depth < 12mo): `funding_rate_momentum_30 = fr - fr.shift(30)`. Same-primitive-class as `funding_rate_zscore_30/90`; F5' risk non-trivial.
- **Anchor**: BASELINE_V1 IS daily Sharpe +0.4767 / OOS +1.1913.
- **Budget**: ENSEMBLE_SIZE=3, n_trials=18, single-seed=42 (v1 EXPLORATION default); wall-clock ≤ 3.0h (raised +0.5h for fetcher+download).
- **Cohorts**: BTC/ETH/LINK/LTC/DOT pooled-and-per-symbol (Model A pooled BTC+ETH; C/D/E per-symbol).
- **F5' band**: < 0.30 IDEAL / [0.30, 0.60) DOCUMENT / ≥ 0.60 ABORT — third consecutive codification.

## Critical Surfaced Concerns

**Concern 1 — Partial-depth IS contamination is HIGHER risk than the outline acknowledges.** `topLongShortAccountRatio` was launched 2020 but exchange-side documented gaps for low-cap symbols (LINK/LTC/DOT) are common pre-2022. If S2 (partial depth) materializes — say LINK starts 2022-07, full IS window starts 2021-03 — then LightGBM histogram-binning routes NaN to dominant child for 35-45% of LINK IS rows. The portfolio importance rank reports MEAN-GAIN; per-cohort rank is the load-bearing artifact. Pre-register per-symbol availability dates IN the brief Section 2 EDA table — DO NOT let the runner silently compute pooled IS Sharpe over NaN-heavy LINK.

**Concern 2 — basin-lottery via primitive-newness.** Three v1 NEW-primitive z-score features have run at v1 EXPLORATION budget; ALL THREE went modal-NEG: /023 funding_rate_zscore_30 INERT, /025 oi_delta_30_z90 INERT, /034 basis_zscore_30 LEARNED-NEG (-0.27 OOS Δ, 5/5 symbols OOS-negative). The `feedback_v1_pool_a_new_feature_lneg.md` rule codifies this as a structural pattern. **/049 is the FOURTH such attempt** and inherits the same base-rate prior. Top-trader positioning is genuinely a different data class (account census vs price/leverage primitive) — modest credit BUT not a get-out-of-jail card.

**Concern 3 — Lookahead via 4h→8h aggregation boundary.** The outline §2 says aggregation uses records in `[t-8h, t)` ending strictly before 8h candle close. ENFORCE in code that the 4h timestamp at `t` is NOT included in the 8h record CLOSING at `t` (the 4h record at timestamp=t is the snapshot AS OF the 4h close — fine — but it represents data already published; the 8h candle closing at `t` should use 4h records with timestamps `t-8h` and `t-4h`, NOT `t`). Off-by-one here is a silent OOS leak path. Pre-register this as a Critic Check item: integration test must show that `long_short_zscore_30[t]` was computable using only rows with `4h_timestamp < t`.

---

## Top 3 Recommendations

### 1. Keep Optuna search space FROZEN for the +1 feature ADD; ADD `--features-base-hash` audit

**What**: No change to `colsample_bytree`, `feature_fraction`, `lambda_l1`, `num_leaves`, `learning_rate`, `min_data_in_leaf`, or trial budget (n_trials=18, single-seed=42, ENSEMBLE_SIZE=3) relative to /047+/048 runners. The 1/44 → 1/45 dimensionality shift (2.27% → 2.22% per-feature default sampling at `feature_fraction=1.0`) is sub-noise at n_trials=18 — defensive widening of `feature_fraction` to "make room" for the new feature COMPOUNDS the axis and breaks single-axis isolation.

**Mechanism**: Same discipline as /047 Rec 1 and /048 Rec 1. Pre-register a frozen `--features-base-hash` (SHA-256 of `V1_FEATURE_COLUMNS_PRUNED + ['long_short_zscore_30']` sorted-tuple) in `run_iteration_049.py` so Critic Phase 6.0 + Phase 7.5 can verify the HP search-space was not silently expanded. The hash is line-1 of the runner's `_setup_log()` block.

**Secondary HP flag — single-seed under-reading reprise**: If F5' IC vs `funding_rate_zscore_30` returns max |IC| ∈ [0.30, 0.50] (my modal forecast — see Predicted Max |IC| section), LightGBM at depth 3-5 allocates splits to whichever of `{long_short_zscore_30, funding_rate_zscore_30}` Optuna favored in seed=42's first ~3 trials. **Verdict NEG-INERT at EXPLORATION ≠ verdict at multi-seed CONFIRMATION.** Brief Section 8 should pre-register that NEG-INERT routes to a 1-shot CONFIRMATION retry IF F1 partial-pass (rank ≤ 18 OR IS Sharpe Δ ≥ +0.03 but not both).

**Risk**: None on the HP-freeze side. The only downside is a slightly higher NEG-INERT probability than if we widened `feature_fraction` — but widening creates a multi-axis brief and contaminates the iteration's signal.

### 2. Window choice — 30-bar is DEFENSIBLE but pre-EDA must report 14-bar + 60-bar IC table as forensic context

**What**: Keep `min_periods=30` as the primary window (anchored to `funding_rate_zscore_30` + `oi_delta_30_z90` convention). DO NOT sweep window variants at /049. BUT add to `analysis/iteration_v1-049/ic_orthogonality_full_44.csv` two additional forensic-only rows: `long_short_zscore_14` and `long_short_zscore_60` (NO modifications to V1_FEATURE_COLUMNS_PRUNED — these are pre-EDA telemetry, not features).

**Mechanism**: top-trader positioning sentiment at 8h cadence has multiple characteristic timescales:
- **14-bar / ~5-day** — captures retail FOMO + capitulation bursts (weekly-cycle aligned).
- **30-bar / ~10-day** — captures funding-period (3 funding/day × 10 = 30 cycles) + halving-cohort transitions.
- **60-bar / ~20-day** — captures macro positioning regime (CPI/FOMC sentiment cycles).

If the 30-bar window's F5' IC vs `funding_rate_zscore_30` lands in [0.30, 0.60) DOCUMENT band, the 14-bar variant's IC may sit lower (faster mean-reversion of z-norm denominator) AND offer a marginal split-budget orthogonality gain — useful as a /050 follow-on EXPLORATION candidate IF /049 is PROMISING. **DO NOT swap windows mid-iteration**; this is forensic-only telemetry for cycle-7 planning.

**Risk**: Adds ~10 minutes to pre-EDA compute. Negligible vs information yield. No risk to /049 axis isolation since these variants are NOT in V1_FEATURE_COLUMNS_PRUNED.

### 3. Pre-registered cohort-conditional importance prediction (per-symbol diagnostic)

**What**: Per-cohort mean-gain rank prediction (out of 45):

| Cohort | Predicted rank band | Mechanism |
|---|---|---|
| **BTC** | 18-28 | Top-100 BTC traders are institutionally diluted (CME-spot-ETF arbitrage rebalancing); positioning z-score amplitude is dampened by passive flow. **Middle-band; expect rank ~22.** |
| **ETH** | 16-26 | Similar to BTC with more retail residual; ETF-effect smaller post-2024-05. Mid-band; expect rank ~20. |
| **LINK** | 10-20 | Mid-cap alt; top-trader positioning carries strongest signal here because passive/institutional flow is minimal. **Most likely cohort to surface a single-cohort PROMISING.** Expect rank ~14. |
| **LTC** | 22-35 | "Background symbol" pattern (same as /047 Rec 3, /048 Rec 3). LTC's positioning data is the lowest-volume of the 5 cohorts; expect rank ~28. **Weakest cohort.** |
| **DOT** | 12-22 | Smallest-cap of 5; highest retail FOMO sensitivity; positioning z-score should differentiate quiet→burst transitions cleanly. Expect rank ~16. |

**Portfolio-level rank prediction: 17-25 of 45** — middle band, INERT-leaning but not bottom-quintile.

**Mechanism**: This is a sharper prediction than /048 because the data class is genuinely different. The dispersion across cohorts (range 10-35, std-of-rank ~7) is itself the diagnostic — wide dispersion = cohort-conditional positioning signal (real but not pooled-additive); tight dispersion (all ~22) = mechanical noise allocation (NEG-INERT confirmed).

**Risk**: F1 dual-gate (TOP-15 portfolio AND IS Δ ≥ +0.05) requires BOTH conditions. My LINK rank-14 forecast is at the edge of the portfolio band; the dispersion forecast suggests LINK + DOT carry the load while BTC/ETH/LTC dilute the portfolio mean. **Forecast probability for portfolio-level rank ≤ 15: ~22%**; conjunction with IS Δ ≥ +0.05: ~13-17%.

---

## Prior Distribution (8 verdict bands)

| Band | Prior | Notes |
|---|---:|---|
| UNIVERSAL | 3% | All 5 cohorts positive Sharpe Δ — non-kline-class HAS marginally higher prior than kline-class (vs /048's 4%) — but base-rate from /023, /025, /034 is brutal. |
| REGIME-SPECIALIST-IS | 8% | Bull/recovery positioning extremes carry edge; bear/chop noisy. Plausible per-regime concentration. |
| REGIME-SPECIALIST-OOS | 3% | OOS is /046+/047+/048 forensic-only; cannot be a /049 verdict per discipline. |
| TAIL-CONTROL | 5% | Positioning extreme z-scores could filter low-quality entries — possible but unlikely at v1's open-only signal architecture. |
| **EXPLORATION-PROMISING** (CLEAN or CORRELATED) | 19% | Higher than /048's 17%: non-kline-class structural advantage. Split: PROMISING-CLEAN ~10%, PROMISING-WITH-CORRELATED-PRIMITIVE ~9%. |
| TRUE-NEG | 9% | Same /048 reasoning — clean evidence for "no positioning edge at v1 EXPLORATION budget". |
| **NEGATIVE-no-effect** | **35% (MODAL)** | Three v1 NEW-primitive z-score precedents all went modal-NEG: /023 funding-z INERT, /025 OI-z INERT, /034 basis-z LEARNED-NEG. Cross-track v3/019 funding_rate_zscore_30 PROMISING-INERT at rank 14/14. Base rate is binding. |
| LEARNED-NEG | 9% | v1/034 basis-z LEARNED-NEG (-0.27 OOS Δ, 5/5 symbols OOS negative) is the closest analog; same z-score-of-fresh-primitive at v1 EXPLORATION + Pool Model A. Adjusted UP slightly from /048's 9%. |
| NEG-CLEAN-PRE-EDA (F5' ABORT) | 4% | Lower than /048's 7%: data class is genuinely different from any existing v1 feature. funding_rate_zscore_30 is the closest empirical correlate; |IC| ≥ 0.60 implausible. |
| BLOCK-PENDING-FIX | 5% | NEW data infrastructure (fetcher pagination, 8h aggregation off-by-one, S3 backup-axis pivot path) raises defect surface vs /048. F4 + integration test catches most. |

Sum = 100%.

**Modal NEGATIVE-no-effect 35%** down from /048's 38% (non-kline-class advantage). Combined positive paths (UNIVERSAL + REGIME-SPECIALIST-IS + TAIL-CONTROL + EXPLORATION-PROMISING) = **35%**. NEG-cluster (TRUE-NEG + NEGATIVE-no-effect + LEARNED-NEG + NEG-CLEAN-PRE-EDA + BLOCK) = **62%**. Approximate 35/62 positive/negative split is the cleanest /049 has — modestly better than /048's 30/55.

---

## Predicted Max |IC| Against V1_FEATURE_COLUMNS_PRUNED (Pre-EDA Sanity Check)

**LM Master pre-launch prediction: max |IC| = 0.28 (point estimate); 80% band [0.18, 0.42].**

Top-3 most likely IC-pair predictions:

| Rank | Feature | Predicted |IC| | Mechanism |
|---:|---|---:|---|
| 1 | `funding_rate_zscore_30` | **0.28** | Funding rate is mark-vs-index basis; long/short ratio is account-direction census. Both encode "leveraged sentiment" but mechanically distinct: funding moves with NOTIONAL imbalance + perp arb activity; account-ratio moves with COUNT imbalance. Empirically lead-lag 1-3 bars at 8h cadence; raw Pearson IC modest. |
| 2 | `funding_rate_zscore_90` | 0.22 | Longer horizon = stronger decoupling from positioning z. Lower IC than funding-z-30. |
| 3 | `cross_btc_ret_5` / `cross_btc_ret_20` | 0.18 | If BTC top-trader positioning shifts ahead of BTC price moves, the z-score may carry early-warning correlated with realized BTC returns. Modest. |

**Distribution forecast**:
- max |IC| < 0.30 IDEAL: ~55% probability (modal)
- max |IC| ∈ [0.30, 0.50] DOCUMENT-low: ~30%
- max |IC| ∈ [0.50, 0.60) DOCUMENT-high: ~10%
- max |IC| ≥ 0.60 ABORT: ~5%

**This is materially different from /048's distribution** (which had ~80% probability of IC ≥ 0.30). Non-kline-class primitive carries a real structural orthogonality advantage at the algebra level. Empirical IC arbitration is still the load-bearing gate.

**Bayesian update note**: if pre-EDA pooled-IS sample is post-2023 dominated AND BTC's CME-spot-ETF era has caused top-trader positioning to MIRROR funding more tightly (institutional arb rebalancing), IC vs `funding_rate_zscore_30` could push to 0.40-0.50. If pre-2023 dominant or LINK/DOT-weighted, IC likely 0.15-0.25.

---

## Risk Flags

1. **HP search-space defensive widening risk** — Rec 1. Critic Check `--features-base-hash` audit.
2. **F5' borderline IC single-seed under-reading** — Rec 1 secondary. At n_trials=18 EXPLORATION, single-seed=42's first-3-trial Optuna trajectory will allocate splits deterministically; verdict NEG-INERT at EXPLORATION ≠ verdict at CONFIRMATION.
3. **v1/034 basis_zscore_30 LEARNED-NEG precedent** is the closest v1 base-rate (-0.27 OOS Δ, 5/5 symbols negative, rank 25-32). Same z-score-of-fresh-primitive architecture; same n_trials regime; same cohort set. Inform priors heavily.
4. **iter-v3/019 funding_rate_zscore_30 PROMISING-INERT precedent** is the closest cross-track base-rate (rank 14/14 LDO+TRX+Portfolio at v3 n_trials=10 single-seed). v1's n_trials=18 marginally higher; v1's 44-feature stack denser than v3's 14. Structural concern transfers.
5. **Partial-depth (S2) reporting honesty** — brief Section 2 EDA MUST report per-symbol availability dates BEFORE the F1/F2 evaluation. Pooled IS Sharpe over NaN-heavy LINK is silently optimistic.
6. **4h→8h aggregation lookahead** — Critic Check additional item: integration test must show `long_short_zscore_30[t]` was computable using only rows with `4h_timestamp < t`. The aggregation boundary is a NEW defect surface for /049.
7. **Backup axis (S3) F5' risk** — `funding_rate_momentum_30 = fr - fr.shift(30)` shares primitive class with `funding_rate_zscore_30/90`; expected |IC| ∈ [0.40, 0.70]. If S3 backup activates, /049 may NEG-CLEAN-PRE-EDA at backup's F5' too — third consecutive ABORT signals cycle-6 feature-family saturation.
8. **Three-consecutive-feature-family-axis risk** — /049 is the third feature-family attempt of cycle-6. Even on a PROMISING verdict, /050 MUST rotate axis (model-arch, labeling, risk-primitive). Pre-register this in brief Section 0.6.

---

## What I Did NOT Recommend

- **No HP region change** (Optuna search-space frozen).
- **No companion feature** (long_short_position_zscore_30 from `topLongShortPositionRatio`, OR taker_long_short_volume_zscore_30 from `takerlongshortRatio`) at /049 — single-feature-at-a-time discipline; saving for /050 follow-on IF /049 PROMISING.
- **No window-parameterization sweep** at /049 (forensic 14+60-bar IC reported but NOT added to V1_FEATURE_COLUMNS_PRUNED).
- **No swap-with-funding_rate_zscore_30** — F5' IC will arbitrate; if PROMISING-CLEAN, ADD alongside; if PROMISING-WITH-CORRELATED-PRIMITIVE, revisit after IC evidence on additional positioning-class candidates.
- **No ENSEMBLE_SIZE bump from 3** — v1 single-seed=42 EXPLORATION standard.
- **No raw `long_short_ratio` level feature** — z-score normalization is required for scale-invariance across the 5 v1 cohorts (BTC top-100 long/short ratio amplitude differs from DOT).
- **No global_long_short_zscore_30** (retail-skewed account variant) — same data class as top-trader variant; pick ONE for /049 EXPLORATION isolation. Top-trader is the more institutionally-meaningful signal per industry literature.
- **No backup axis primary-substitution** — S3 backup is OPERATIONAL fallback only; if data depth check fails, the brief is RE-ANCHORED with full F5'-fresh evaluation, not a silent swap.

---

## Closing Note

**Single most important point**: pre-EDA F5' max |IC| vs `funding_rate_zscore_30` is the load-bearing diagnostic for /049 — same as /047 (algebraic sister) and /048 (empirical correlation), but at a STRUCTURALLY HIGHER orthogonality floor because positioning sentiment is genuinely a non-kline data class. My point prediction is **0.28 (within IDEAL < 0.30 zone)**, with 55% probability of the IDEAL band — materially better than /048's modal DOCUMENT zone forecast. The pre-EDA gate F5' is still the methodology arbiter; my forecast is informative, not binding.

**Confidence: MEDIUM-HIGH** (up from /048's MEDIUM). Axis is the cleanest possible response to /048's lesson (non-kline data class entirely). Design is methodologically clean (F4 + tightened F5' + new R8 data-source operational risk + new R9 partial-depth honesty + per-cohort importance prediction as diagnostic). BUT: three v1 NEW-primitive z-score precedents (/023, /025, /034) all went modal-NEG, AND cross-track v3/019 funding_rate_zscore_30 PROMISING-INERT. The base-rate prior is binding even with the structural orthogonality advantage. **Modal expected outcome: NEGATIVE-no-effect at 35%**, with second-most-likely positive path being PROMISING-CLEAN at ~10% of the EXPLORATION-PROMISING 19% slice.

**Path Forward if NEG-INERT/NEG-CLEAN at /049**: /050 MUST rotate axis (model-arch, labeling, risk-primitive) per three-consecutive-feature-family saturation rule. Recommended: labeling axis — fractional-bar triple-barrier per López de Prado AFML Ch. 3 (carry-over from /047 + /048 Path Forward). Higher-variance hypothesis; orthogonal to all feature-family work.

**Path Forward if PROMISING (either subtype)**: /050 = decide between (a) 1-shot CONFIRMATION-style multi-seed retry to disambiguate verdict from single-seed lottery (recommended if PROMISING-WITH-CORRELATED-PRIMITIVE) or (b) SECOND positioning-class feature to test additivity hypothesis (recommended if PROMISING-CLEAN — candidates: long_short_position_zscore_30, taker_long_short_volume_zscore_30, global_long_short_zscore_30).

**Path Forward if NEG-CLEAN-PRE-EDA at /049 F5' (third consecutive ABORT)**: the cycle-6 feature-family axis is saturated at v1's current scope. /050 MUST pivot to a structurally different axis. The feedback rule "v1 EXPLORATION single-feature-ADD axis is empirically saturated at cycle-6 — both kline-internal and non-kline data classes fail the F5' orthogonality gate at single-seed EXPLORATION budget" becomes a candidate memory write.

**Path Forward if S3 backup activates AND backup ABORTs**: same as third-consecutive-ABORT routing; cycle-6 feature-family axis officially saturated.
