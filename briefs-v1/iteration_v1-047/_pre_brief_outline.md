# iter-v1/047 — Pre-Brief Outline

**Status:** Pre-brief outline authored 2026-06-01. Synthesizes /046 closeout (PROMISING-DIVERGENCE on methodology axis) + /045 Critic Path Forward #3 (NEW feature family preferred over substrate iteration) + LM Master /045 + /046 modal recommendation (cycle-6 → on-chain / cross-asset / microstructure / asymmetric-tail). Full brief authored in Phase 5; this file is the design substrate the brief draws from.

**TYPE:** `EXPLORATION` (cycle-6 EXPLORATION 2/10).

**Cycle slot:** cycle-6 EXPLORATION 2/10. /046 was 1/10 (methodology axis); /047 PIVOTS to a NEW feature-family axis per the user mandate "feature engineering is the biggest gap (never done in 25 iters)" and per /045 Critic Path Forward #3.

---

## 1. Hypothesis (one-sentence)

A scale-invariant **realized-skewness z-score over a 21-bar (7-day) window, z-normalized over a rolling 90-bar (30-day) window** — `skew_zscore_21` — adds an asymmetric-tail regime signal that LightGBM does not currently access via `V1_FEATURE_COLUMNS_PRUNED`'s existing 44 features, and produces both (a) **top-15 importance at the portfolio level** AND (b) **IS daily Sharpe Δ ≥ +0.05 vs BASELINE_V1 (+0.4767)**, demonstrating that asymmetric tail behavior is an unexploited edge axis in v1's pooled-and-per-symbol Optuna search.

---

## 2. Axis Family Declaration (Section 0.6)

**Axis family:** `feature-family` (NEW asymmetric-tail / higher-moment statistical primitive — a regime-form variant on raw skewness; first z-scored-regime higher-moment feature in v1 history).

**Prior 5 EXPLORATION families (from `briefs-v1/exploration_catalog.md`):**

| Iter | Date | Axis family |
|---|---|---|
| iter-v1/041 | 2026-05-31 | labeling (uniform `atr_tp=1.5 / atr_sl=0.75` across cohorts) |
| iter-v1/042 | 2026-05-31 | model-arch (XGBoost head-to-head vs LightGBM) |
| iter-v1/043 | 2026-05-31 | per-cohort-specialization × labeling (LINK-only trend-scanning) |
| iter-v1/045 | 2026-06-01 | bundle-substrate (CONFIRMATION-MERGE-PORTFOLIO, 5-component partition) |
| iter-v1/046 | 2026-06-01 | methodology (IS-only partition-solve re-composition) |

**Rotation status:** `VALID` — `feature-family` is NOT in the prior 5 (which span labeling, model-arch, per-cohort-specialization×labeling COMBO, bundle-substrate, methodology). Rotation discipline SATISFIED. The most recent `feature-family` EXPLORATION was /040 (regime_momentum_signed_5d swap), which is the 6th-most-recent EXPLORATION — outside the prior 5 window.

**One-sentence rationale:** /046 PROMISING-DIVERGENCE established that ALT_1's headline +3.49 OOS was a post-hoc selection artifact; cycle-6's next move per /045 Critic Path Forward #3 + LM Master modal recommendation is to ADD a NEW feature primitive that LightGBM has never had access to (vs continuing to re-shuffle substrate composition from the same 44-feature surface), and asymmetric-tail z-score is both a literature-supported edge (Harvey-Siddique JoF 2000) AND the only higher-moment regime-form primitive missing from `V1_FEATURE_COLUMNS_PRUNED`.

---

## 3. Axis Rotation Discipline — Family Rationale

**Why `feature-family` is the right axis after /041–/046:**

- /041–/043 spent late-cycle-5 exhausting **content** axes (label width, model-arch, per-cohort specialization).
- /044 / /045 attempted CONFIRMATION-MERGE-PORTFOLIO bundling at the bundle-substrate level — /044 grandfathered, /045 BLOCK-FINAL on substrate-selection prudence.
- /046 fixed the substrate-selection METHODOLOGY (IS-only score); verdict PROMISING-DIVERGENCE — methodology axis has now been ENGAGED and the answer is "OOS-inflation was real." The fix is in. Cycling on /046's axis again would be redundant.
- /047's job per /045 Critic Path Forward #3 and LM Master modal recommendation: **expand the feature surface**. The 44-feature pruned set has been the substrate of /034-/046 (13 iterations). LightGBM's `colsample_bytree` and `feature_fraction` have been searching within that 44-dim space across 50 Optuna trials × 5 seeds for the full cycle. Adding 1 well-chosen primitive is the cheapest way to **expand the reachable hypothesis space**.

**What this is NOT:**
- Not a feature swap (no DROP). `skew_zscore_21` is ADDITIVE: V1_FEATURE_COLUMNS_PRUNED 44 → 45. If F1 + F5 both pass, future iterations decide retention; if F1 fails, the feature is added to V1_RETIRED_FEATURE_COLUMNS like basis_zscore_30 was at /040.
- Not a feature-engineering EXPERIMENT (no novel composition operator). `skew_zscore_21` uses standard stats primitives (`scipy.stats.skew` + `rolling.mean/std`). The novelty is the **scale-invariant z-scored regime form** of a primitive that exists in raw form (`stat_skew_20`) but has never been z-scored — making it a regime-indicator vs a level-indicator.
- Not an off-the-shelf indicator (TA-lib has no realized-skewness-z-score primitive). The construction is from Harvey-Siddique JoF 2000 conditional-skewness empirical literature, adapted to a 21-bar / 8h cadence.

**Critical pre-existing-feature flag (must be confronted in Section 4 F5):** `stat_skew_20` IS in `V1_FEATURE_COLUMNS_PRUNED` at line 116 — a 20-bar rolling skewness of `close.pct_change()`. The proposed `skew_zscore_21` differs structurally:
1. **Window**: 21-bar log-returns vs 20-bar pct_change (negligible — 5% sample-size difference, log vs pct returns differ by 2nd-order).
2. **Z-normalization**: rolling 90-bar mean/std normalization of the skew time series. This converts skewness from a **level indicator** ("how skewed is the return distribution NOW") to a **regime indicator** ("how skewed is NOW relative to the recent 30-day distribution of skewness"). Trees can split on level OR regime — they are not algebraically equivalent.
3. **Importance independence expectation**: pairwise IC of `skew_zscore_21` vs `stat_skew_20` is expected to be moderate (~0.30-0.60 in absolute value) — high enough to flag for explicit Section 4 F5 treatment, low enough to plausibly be orthogonal in the trees' split-finding regime. **The F5 threshold is |IC| < 0.50 vs ALL existing 44 features**; if IC vs `stat_skew_20` exceeds 0.50, the brief is reconsidered before launch.

---

## 4. Falsifier Preview (full Section 4 in brief)

### F1 — Master (LightGBM importance — DUAL CONDITION)

**Claim:** `skew_zscore_21` ranks in TOP-15 of 45 features by mean-gain importance at the portfolio-aggregated level (averaged across Models A/C/D/E, weighted by per-model trade count) AND IS daily Sharpe Δ ≥ +0.05 vs BASELINE_V1 +0.4767 (i.e., observed IS daily Sharpe ≥ +0.5267).

**Rationale:** Either condition alone is insufficient:
- Importance without Sharpe lift → LightGBM is USING the feature but not gaining edge from it (mechanically allocating splits without net signal). This is the iter-v3/019 `funding_rate_zscore_30` PROMISING-INERT pattern AT PORTFOLIO level — rank 14/14 LDO+TRX+Portfolio NULL — though that was bottom-rank not top-rank, the symmetric concern is "rank could be top but Sharpe could be flat."
- Sharpe lift without importance → the lift is attributable to Optuna basin-lottery noise on the existing 44 features, NOT the new feature.

Dual gate prevents both false-positive patterns. Lifted directly from v3's `engineered_features_proven` precedent (regime_momentum_signed_5d at iter-v3/025 produced 51% top importance AND IS +0.50 / OOS +0.84 vs anchor).

**Status:** Master falsifier — F1 PASS → PROMISING (sub-classified by F2/F3 below). F1 FAIL (either condition fails) → escalate to F-AXIS #2 (which condition failed; what does it mean about the feature) — do NOT propose feature retention.

### F2 — IS Sharpe Δ Direction (clean PROMISING vs NEG-CLEAN)

**Claim:** IS daily Sharpe Δ ≥ +0.05 above BASELINE_V1 +0.4767 → PROMISING; -0.05 < Δ < +0.05 → NEG-INERT; Δ ≤ -0.05 → NEG-CLEAN (active OOS-side regression).

**Three-band classification:**

| IS Δ band | Verdict subtype |
|---|---|
| ≥ +0.05 | PROMISING-CLEAN (if F5 PASS) or PROMISING-WITH-CORRELATED-PRIMITIVE (if F5 borderline) |
| -0.05 < Δ < +0.05 | NEG-INERT (feature is benign; tied to baseline within noise; informational drop) |
| ≤ -0.05 | NEG-CLEAN (actively harms IS — feature is mechanically allocated splits but is harmful; INERT-features-at-higher-budget pattern from v3/023 — adding INERT at n_trials=18+ can ACTIVELY HARM OOS by reorganizing the loss surface to non-signal regions) |

**Interpretation if FAIL into NEG-INERT:** Inventory ground-truth update — asymmetric-tail z-score IS reflected in `stat_skew_20` already; redundant. Add `skew_zscore_21` to V1_RETIRED_FEATURE_COLUMNS at /047 closeout.

**Interpretation if FAIL into NEG-CLEAN:** Same routing — RETIRE the feature, and ALSO add a new feedback rule "rolling-z-score of an existing skewness primitive is NOT additive at v1's Optuna budget" similar to v3's `inert_features_at_higher_budget` rule.

### F3 — OOS Δ (forensic-only, per /046 discipline)

**Claim:** OOS daily Sharpe Δ vs BASELINE_V1 +1.1913 — REPORTED in comparison.csv but NOT a /047 success criterion. /046 PROMISING-DIVERGENCE established that OOS-aware selection is a leak path; /047 preserves that discipline by treating OOS as DIAGNOSTIC EVIDENCE for which sub-band to file under but NOT for the verdict gate itself.

**Status:** Forensic only. Critic Phase 7.5 CANNOT cite OOS Sharpe Δ < +0.05 as a /047 failure mode. The OOS observation is logged for /048+ priors and for the eventual CONFIRMATION run.

### F4 — ADF Stationarity (pre-EDA gate)

**Claim:** `skew_zscore_21` is stationary across all 5 v1 symbols (BTC, ETH, LINK, LTC, DOT) at the IS-window upper bound — ADF p-value < 0.05 with `regression='c'` (constant) and `maxlag=10`. This must be VERIFIED in IS-only pre-EDA before backtest launch.

**Interpretation:**
- 5/5 PASS → V1_FEATURE_COLUMNS_PRUNED stationarity invariant preserved (line 87 "40/40 pass ADF raw-α=0.05" extended to 45/45). Brief notes the property in Section 3.
- 4/5 PASS → INVESTIGATE which symbol fails; if borderline (p ∈ [0.05, 0.10]), document and proceed. If hard fail (p > 0.10), redesign the rolling window for that symbol or DROP that symbol from the feature's parquet population (NaN-mask). The feature must be PASS-pure for `V1_FEATURE_COLUMNS_PRUNED` membership.
- ≤3/5 PASS → ABORT pre-launch. The z-score normalization on a 90-bar window may be inadequate for high-vol symbols. Redesign required.

**Rationale:** The pruned-feature stationarity invariant was a hard property of the /021 pruning campaign and has been preserved through all subsequent ADD/DROP/SWAP operations. /047 must not break it.

### F5 — IC Orthogonality vs Existing 44 Features

**Claim:** Max absolute pairwise Pearson IC (information coefficient — instantaneous, lag-0) of `skew_zscore_21` vs ALL 44 features in `V1_FEATURE_COLUMNS_PRUNED` is < 0.50 — measured on IS-only data, pooled across all 5 symbols (sample-weighted by per-symbol IS row count).

**Special attention symbols:**

- **`stat_skew_20`** — algebraically the closest primitive (raw 20-bar rolling skew of pct returns). Expected |IC| ~ 0.30-0.60. If |IC| ∈ [0.40, 0.50], FLAG in brief Section 2 but PROCEED. If |IC| > 0.50, RECONSIDER (either redesign window, abort, or escalate to PROMISING-WITH-CORRELATED-PRIMITIVE subtype where the IC is acknowledged + the dual F1 importance gate is the disambiguator).
- **`stat_kurtosis_20`** — companion higher-moment from the same family (4th vs 3rd moment). Expected |IC| ~ 0.15-0.40 (kurtosis and skewness are mathematically distinct but often co-move in high-vol regimes). Allowed up to 0.50.
- **`vol_atr_14` / `vol_natr_14` / `vol_bb_bandwidth_20`** — volatility primitives. Realized skew is a higher-moment of returns; raw 2nd-moment vol features may be correlated in fat-tail regimes. Expected |IC| ~ 0.10-0.30.

**Interpretation:**
- max |IC| < 0.50 across all 44 features → ORTHOGONAL OK. Proceed to launch.
- max |IC| ∈ [0.50, 0.60] AND the offending feature is `stat_skew_20` ONLY → ESCALATE in brief Section 2 to "PROMISING-WITH-CORRELATED-PRIMITIVE" subtype where F1 dual-gate is the disambiguator (a feature can be 0.55 |IC| with `stat_skew_20` AND still rank top-15 AND produce IS Δ ≥ +0.05 — that pattern would mean the z-scored regime form IS extracting incremental signal beyond the level form).
- max |IC| ≥ 0.60 vs ANY feature → ABORT. The feature is mechanically duplicative.

**Rationale:** The /021 pruning campaign retained features with low pairwise IC; preserving that invariant prevents wasted `colsample_bytree` picks (the iter-v2/070 lesson: high-IC redundant features steal split-budget from genuinely orthogonal features).

---

## 5. Pre-EDA Outputs (Section 9 deliverables)

`analysis/iteration_v1-047/` script + CSV deliverables PRE-BACKTEST:

1. **`skew_zscore_21_definition.py`** — VERIFIABLE pandas formula (Section 6 verbatim) committed before launch.
2. **`adf_stationarity_per_symbol.csv`** — ADF p-value per symbol × `skew_zscore_21` column. Schema: `symbol, n_obs, adf_stat, adf_pvalue, lag_used, pass_at_005`. 5 rows.
3. **`distribution_stats_per_symbol.csv`** — IS-only distribution stats: mean, std, skew, kurtosis, 5th/25th/50th/75th/95th percentile of `skew_zscore_21` per symbol. 5 rows × 9 cols. Empirical confirmation that z-score normalization produces approximately mean=0, std=1 per symbol (or document the deviation).
4. **`ic_orthogonality_top5.csv`** — Pearson IC of `skew_zscore_21` vs the 5 highest-pre-conjectured-correlation existing features: `stat_skew_20`, `stat_kurtosis_20`, `vol_atr_14`, `vol_natr_14`, `vol_bb_bandwidth_20`. Pooled across symbols. 5 rows × 3 cols (feature, IC, pair_n).
5. **`ic_orthogonality_full_44.csv`** — Pearson IC of `skew_zscore_21` vs ALL 44 V1_FEATURE_COLUMNS_PRUNED features. 44 rows. The max |IC| from this file is the F5 gate input.

All 5 outputs MUST be committed BEFORE Phase 6 backtest launch. F4 and F5 gates evaluated from these files.

---

## 6. Feature Definition (verbatim)

**Pandas formula (per-symbol, computed independently for each of BTC/ETH/LINK/LTC/DOT):**

```python
# Inputs: df has columns ['close'] indexed by open_time
# Output: df['skew_zscore_21']
log_returns = (df['close'] / df['close'].shift(1)).apply(np.log)
skew_21bar = log_returns.rolling(window=21, min_periods=21).apply(
    lambda x: scipy.stats.skew(x, bias=False), raw=True
)
skew_mean_90 = skew_21bar.rolling(window=90, min_periods=90).mean()
skew_std_90 = skew_21bar.rolling(window=90, min_periods=90).std()
df['skew_zscore_21'] = (skew_21bar - skew_mean_90) / skew_std_90
```

**Properties:**
- Past-only construction: `log_returns` at time `t` uses `close[t]` and `close[t-1]`; `skew_21bar` at time `t` uses `log_returns[t-20:t+1]` (21 candles ending at t inclusive); `skew_mean_90` and `skew_std_90` at time `t` use `skew_21bar[t-89:t+1]` (90 candles ending at t inclusive). Decision at candle `t+1` uses `skew_zscore_21[t]` — no look-ahead.
- `min_periods=21` (skew) and `min_periods=90` (z-score normalization) → first ~110 candles per symbol are NaN. At 8h cadence, this is ~37 days warmup. ALL v1 symbols have ≥4 years history; warmup loss is negligible.
- Scale-invariant by construction: log_returns are scale-invariant; rolling skew preserves invariance; z-score normalization removes the unit. The feature is **bounded approximately to [-3, +3] under Gaussian assumptions** (CLT-like; observed range will be wider with fat tails — Section 5's distribution_stats_per_symbol.csv quantifies).
- `bias=False` per scipy default for sample skewness (G1 estimator with bias correction). Pinned to scipy 1.13+ default for determinism across runs.

**Pinning:** scipy version pinned in pyproject.toml; failure mode if version skew → integration test in /047's PR catches drift.

---

## 7. Axis-Family Justification (Section 3 detail)

**Why ASYMMETRIC TAIL / REALIZED SKEWNESS specifically:**

1. **Literature precedent (Harvey-Siddique JoF 2000):** conditional skewness is priced in equity cross-sections — assets with NEGATIVE coskewness earn premia. Crypto extension: Karagiorgis et al. arXiv 2410.12801 (2024) — higher-moment factor structure across 84 cryptos. The 21-bar / 7-day window matches the trend horizon in v1's existing `regime_momentum_signed_5d` (5-day) and v3's 21-day cycles, anchoring the feature at the medium-term regime scale.

2. **Mechanism (orthogonal to existing 44 features):**
   - `stat_skew_20` (existing) is a LEVEL indicator: "is the distribution skewed RIGHT NOW?"
   - `skew_zscore_21` (proposed) is a REGIME indicator: "is the current skewness HIGH or LOW relative to its own recent (30-day) distribution?"
   - Trees can split on `skew_zscore_21 > +2` to detect "current return distribution is exceptionally right-skewed RELATIVE to recent history" — a fundamentally different signal than `stat_skew_20 > +0.5` ("current absolute skew is positive"). The mechanism is the same as how `vol_range_spike_24` (vol regime) differs from `vol_atr_14` (vol level).

3. **8h cadence fit (project memory: "8h is special"):** funding-cycle alignment + behavioral-cycle alignment + microstructure-noise filter. 21-bar = 7 days = one funding-cycle-week. The window encompasses ~21 funding settlements at Binance perp 8h cadence.

4. **Computational cost (Section 5 wall-clock):** rolling skew at 21-bar + rolling mean/std at 90-bar is O(N) per symbol with scipy's optimized rolling apply. Estimated <2 min added to feature regen across all 5 symbols. Pinned in `features_v1/__init__.py` after the dispatch function for `regime_momentum_signed_5d`.

5. **Why NOT other higher-moment primitives this iteration:**
   - **Realized kurtosis z-score** — companion candidate (4th moment); deferred to /048 if /047 PROMISING. Single-feature-at-a-time per the v3 lesson `engineered_features_dont_stack` — even though that rule was originally for SAME-FAMILY engineered features at single-seed EXPLORATION, the spirit applies to ANY two same-family additions in the same EXPLORATION budget.
   - **Coskewness vs BTC** — cross-asset higher-moment; richer signal but requires 2-symbol joint computation. Defer to /048+ if /047 PROMISING.
   - **Asymmetric vol (semi-variance)** — different family (2nd moment, not 3rd). Defer.

---

## 8. Risk Plan (Section 6)

**R1 (importance-rank robustness):** F1's TOP-15-of-45 portfolio-level threshold is calibrated against the empirical distribution of feature importance in V1_FEATURE_COLUMNS_PRUNED — the current top-15 features (per /045 mean-gain audit) capture roughly 70-80% of total information gain across A/C/D/E. A NEW feature ranking outside top-15 has empirically zero predictive utility at v1's Optuna budget (the v3/019 funding_rate_zscore_30 INERT pattern — rank 14/14, contributed <2% gain). TOP-15 is the **active-feature threshold**, not the cumulative-importance threshold.

**R2 (IS Sharpe lift floor +0.05):** Tight floor calibrated against the empirical distribution of EXPLORATION verdicts in v1 history (/034-/043 had 9 verdicts; PROMISING-CLEAN verdicts typically posted IS Δ in the [+0.05, +0.15] range — /037 Sortino IS +0.10; /040 regime_momentum_signed_5d IS +0.06). +0.05 is the meaningful-signal threshold above noise.

**R3 (NEG-CLEAN routing if active harm):** F2's NEG-CLEAN band (Δ ≤ -0.05) triggers RETIRE + feedback rule. Specifically:
- Retire `skew_zscore_21` to V1_RETIRED_FEATURE_COLUMNS at /047 closeout.
- New feedback rule candidate: "rolling-z-score of an existing skewness primitive is NOT additive at v1's 18-trial EXPLORATION budget" — to be confirmed at /048 if /047 NEG-CLEAN.

**R4 (ADF stationarity gate F4):** PRE-LAUNCH GATE. If F4 fails 2+ symbols, the brief is REVISED before Phase 6 launch (window redesign or abort). Do not run backtest on a feature that violates the V1_FEATURE_COLUMNS_PRUNED stationarity invariant.

**R5 (IC orthogonality gate F5):** PRE-LAUNCH GATE. If max |IC| > 0.60, ABORT before launch. If max |IC| ∈ [0.50, 0.60] with `stat_skew_20`, escalate to PROMISING-WITH-CORRELATED-PRIMITIVE subtype WITH explicit acknowledgment in brief Section 3.

**R6 (Risk Mitigation IS-calibrated — BASELINE_V1 stack unchanged):** /047 inherits BASELINE_V1's risk stack (R1 consecutive-SL cool-down for C/D/E, R2 drawdown brake for E, R3 OOD Mahalanobis for ALL) unchanged. The new feature is added to `V1_FEATURE_COLUMNS_PRUNED` but is NOT added to `V1_OOD_FEATURE_COLUMNS` (the 16-feature Mahalanobis subset is decoupled per `features_v1/__init__.py:158-164` comment). Adding `skew_zscore_21` to OOD would be a SECOND change in the same iteration — deferred to /048+ if /047 PROMISING.

**R7 (NORMAL-RISK declaration — Section 2.5):** This is a feature-ADD iteration. The Optuna training objective (sharpe) is UNCHANGED. The training window (24 months) is UNCHANGED. The symbol universe (5-cohort BCH/ETH/LINK/LTC/DOT) is UNCHANGED. The model architecture (4-model LightGBM 5-seed ensemble) is UNCHANGED. Only the feature_columns argument expands from 44 → 45. **This is NORMAL-RISK per the v1 HIGH-RISK criterion definition** (HIGH-RISK = axis changes Optuna's training-objective domain: risk-primitive constraint changes, universe substitution, label-mode change, feature-set REPLACEMENT [not addition], bar-interval change). Feature ADDITION does not change Optuna's objective; it expands its input space by 1 dimension.

---

## 9. Wall-Clock Budget (Section 5)

**Total: ≤ 2.5h.**

Breakdown:

| Phase | Wall-clock | Notes |
|---|---|---|
| Pre-EDA Section 5 deliverables | 10-15 min | scipy rolling skew + ADF + IC; 5 symbols × small computation |
| Feature regen (V1_FEATURE_COLUMNS_PRUNED + skew_zscore_21) | ~30 min | `crypto-trade features --track v1 --workers 4`; the 30 min is the v1 feature regen baseline; +skew_zscore_21 adds <2 min |
| Optuna backtest (5 cohorts × monthly retrain × 18 trials × 3 EXPLORATION seeds × ENSEMBLE_SIZE=3) | ≤ 2h | EXPLORATION default per v1 (n_trials=18, 2h cap); the additional feature dimension adds ~5% to Optuna search-space dimensionality but does not change trial count |
| Reports + comparison.csv + diary + closeout | 15-20 min | standard /034-/043 cadence |

**Wall-clock cap:** 2.5h HARD. If Optuna+backtest exceeds 2h at the 80% mark, abort and triage. /047 is an EXPLORATION; signal extraction should not exceed EXPLORATION budget.

**No-runtime-kill condition:** the feature regen and Optuna call are pure compute; no exchange-side IO, no rate limits. The hard cap is wall-clock, not external dependency.

---

## 10. Section Pre-Fills for Phase 5 Brief

| Brief section | Pre-filled content (this outline) |
|---|---|
| 0.0 — Banner | EXPLORATION; cycle-6 2/10; axis `feature-family`; anchor BASELINE_V1 |
| 0.5 — Type + Cadence | EXPLORATION; cycle-6 EXPLORATION 2/10 (after /046 1/10); /034-/046 cycle-5+6 precedents cited |
| 0.6 — Axis family + rotation | `feature-family`; VALID — not in prior 5 (/041-/046 spanned labeling, model-arch, per-cohort×labeling, bundle-substrate, methodology) |
| 1 — Hypothesis | §1 of this outline verbatim |
| 2 — IS-only Numerical Evidence | EDA tables from §5 deliverables: ADF per symbol, distribution stats per symbol, IC top-5 + IC full-44, |IC| max value, F4/F5 pre-launch gate outcomes |
| 2.5 — HIGH-RISK | NORMAL-RISK declaration per §8 R7 (feature ADDITION; Optuna objective+domain UNCHANGED) |
| 3 — Proposed Changes + LM Master | (a) `features_v1/__init__.py` — add `skew_zscore_21` to V1_FEATURE_COLUMNS_PRUNED (44→45), update assertion, (b) `features_v1/statistical.py` — register `compute_skew_zscore_21(df) -> Series` dispatch, (c) `tests/test_features_v1_skew_zscore.py` — past-only verification, ADF dummy-validation, NaN-mask warmup-period verification, (d) `run_iteration_047.py` — runner with `feature_columns=list(V1_FEATURE_COLUMNS_PRUNED)`; LM Master Phase 4.5 invocation: feature-family axis — LM Master typically returns 2-4 HP recommendations + 1-2 feature ideas; brief Section 3 must address each |
| 4 — Falsifier | F1–F5 from §4 of this outline (TOP-15 portfolio importance dual-gated with IS Δ ≥ +0.05) |
| 5 — Wall-clock | ≤ 2.5h — §9 of this outline |
| 6 — Risk Mitigation | R1–R7 from §8 of this outline |
| 7 — Pre-registered Failure-Mode Prediction | F1 PASS prior ~30-40% (asymmetric-tail is literature-supported but z-score regime form is novel; v1's Optuna 18-trial budget at EXPLORATION may be insufficient to engage a 45th feature); F1 FAIL prior ~50-60%; NEG-CLEAN prior ~15-20% (the iter-v3/023 inert-features-at-higher-budget concern applies symmetrically when the new feature is moderately IC-correlated with stat_skew_20); F4 PASS prior ~85% (rolling z-score on already-rolling primitive — stationarity well-supported); F5 PASS prior ~70% (the only credible correlation risk is stat_skew_20, expected |IC| ~ 0.30-0.60) |
| 8 — MERGE/NO-MERGE | EXPLORATION verdict only (PROMISING-CLEAN / PROMISING-WITH-CORRELATED-PRIMITIVE / NEG-INERT / NEG-CLEAN / BLOCK-PENDING-FIX); NO MERGE at /047 by EXPLORATION budget convention |
| 9 — Smoke test | Engineering report MUST emit (a) ADF table 5/5 pass, (b) distribution stats per symbol, (c) IC top-5 + full-44, (d) F4/F5 gate outcomes, (e) skew_zscore_21 importance rank at portfolio + per-cohort, (f) IS Δ + OOS Δ comparison.csv, (g) integration test confirming feature pin in runner |

---

## 11. Pre-EDA Anticipated F1/F2 Outcome Distribution

The Bayesian priors on /047 outcomes (refined in brief Section 7 after pre-EDA):

| Outcome | Prior | Reasoning |
|---|---|---|
| **PROMISING-CLEAN** (F1 PASS via TOP-15 + IS Δ ≥ +0.05; F5 PASS with max |IC| < 0.40) | **20-25%** | Asymmetric tail is a real edge in crypto (Karagiorgis); z-score regime form has not been tested at v1's 8h cadence; the absence of any z-scored higher-moment in V1_FEATURE_COLUMNS_PRUNED is a real surface gap. v1 Optuna at 18 trials × 3 seeds × ENSEMBLE_SIZE=3 has ~150 effective optimization steps per cohort — empirically sufficient to engage a NEW feature if its information is orthogonal. Anchored to /040 regime_momentum_signed_5d (PROMISING-CLEAN with IS Δ +0.06). |
| **PROMISING-WITH-CORRELATED-PRIMITIVE** (F1 PASS but max |IC| ∈ [0.50, 0.60] with stat_skew_20) | **10-15%** | The z-scored regime form is a transform of a primitive that already exists in `stat_skew_20`. Even with the level-vs-regime distinction in Section 3, the empirical correlation could be moderate. The dual F1 gate is the disambiguator — if importance rank ≤ 15 AND IS Δ ≥ +0.05 despite |IC| > 0.50, the regime form IS extracting incremental signal. |
| **NEG-INERT** (IS Δ ∈ (-0.05, +0.05); rank possibly > 15) | **30-40%** | Inventory ground-truth update: asymmetric-tail z-score is reflected ENOUGH in `stat_skew_20` that the trees do not gain edge from the regime form. v1 has 13 cycle iterations already on the 44-feature surface; the additive-feature space may be empirically signal-bounded. |
| **NEG-CLEAN** (IS Δ ≤ -0.05; active OOS-side regression) | **15-25%** | v3's `inert_features_at_higher_budget` rule: adding a feature that is mechanically correlated with an existing feature but whose null-signal channel diverts split-budget AWAY from genuinely orthogonal features. If `skew_zscore_21` is in the |IC| 0.4-0.6 range with `stat_skew_20`, the tree's split-finding becomes confused — it can split on EITHER feature without gaining new signal, but the new feature steals splits from `stat_kurtosis_20`/`vol_atr_14` which were carrying real signal. |
| **BLOCK-PENDING-FIX** (F4 or F5 hard fail before launch; or src/ code defect at Critic Phase 7.5) | **5-10%** | F4 pre-EDA gate catches stationarity defect before launch; F5 catches IC defect. If both pass, the only block path is Critic Phase 7.5 finding a defect in the dispatch (e.g., NaN handling at the 110-candle warmup boundary, or test coverage gap). |

These priors will be hardened in brief Section 7 after pre-EDA.

---

## 12. Section 9 Smoke-Test Pre-Registration

Engineering report (Phase 6) MUST emit:

1. `analysis/iteration_v1-047/skew_zscore_21_definition.py` — committed before launch with verbatim formula and unit test.
2. `analysis/iteration_v1-047/adf_stationarity_per_symbol.csv` — 5 rows.
3. `analysis/iteration_v1-047/distribution_stats_per_symbol.csv` — 5 rows × 9 cols.
4. `analysis/iteration_v1-047/ic_orthogonality_top5.csv` — 5 rows (high-correlation conjectures).
5. `analysis/iteration_v1-047/ic_orthogonality_full_44.csv` — 44 rows (full V1_FEATURE_COLUMNS_PRUNED).
6. `analysis/iteration_v1-047/F4_F5_gate_outcomes.md` — pass/fail per gate with quoted critical values.
7. `reports-v1/iteration_v1-047/comparison.csv` — IS / OOS Sharpe / Sortino / MaxDD / WR / PF / trade count vs BASELINE_V1.
8. `reports-v1/iteration_v1-047/feature_importance.csv` — `skew_zscore_21` rank per cohort (A/C/D/E) and at portfolio level (gain-weighted average).
9. `reports-v1/iteration_v1-047/integration_smoke_test.md` — confirms feature is pinned in runner (`feature_columns=list(V1_FEATURE_COLUMNS_PRUNED)`), confirms `len(V1_FEATURE_COLUMNS_PRUNED) == 45` assertion updated, confirms test suite passes.

---

## 13. Definition of `PROMISING-WITH-CORRELATED-PRIMITIVE` Subtype

Per the v1 catalog convention, /047 may introduce (if applicable) a NEW subtype:

**`PROMISING-WITH-CORRELATED-PRIMITIVE`** = an EXPLORATION verdict where:
- F1 dual-gate PASSES (importance rank ≤ 15 AND IS Δ ≥ +0.05).
- F5 IC orthogonality is BORDERLINE (max |IC| ∈ [0.50, 0.60], with the offending pair being a structurally similar primitive — e.g. raw vs z-scored version of the same higher-moment).

This subtype is COMPOUNDABLE as signal (the dual F1 PASS is the disambiguator confirming incremental edge) but requires explicit documentation in the diary of the IC level + a CONFIRMATION-time decision about which form (raw or z-scored) to RETAIN. The default in cycle-6 is to RETAIN both pending CONFIRMATION; at CONFIRMATION, the SHAP / cluster-MDA test determines retention.

This subtype is a sibling of /046's `PROMISING-DIVERGENCE` (methodology) and /040's `PROMISING-FEATURE-MECHANICAL` (composed feature with sister cannibalization).

---

## 14. /047 Disposition Recommendation

**Recommendation:** RUN. The feature-family axis is the right next move after /046's methodology-axis verdict; the EXPLORATION budget (≤2.5h) is well within v1 EXPLORATION cadence; the hypothesis is genuinely uncertain (F1 PASS prior ~20-25%, F1 FAIL prior ~70-80%); F4/F5 pre-launch gates protect against pathological feature additions.

**Sequencing:** /047 strictly precedes /048+. If /047 PROMISING-CLEAN or PROMISING-WITH-CORRELATED-PRIMITIVE, /048 considers realized kurtosis z-score (companion higher-moment) OR cross-asset coskewness (a richer asymmetric-tail signal). If /047 NEG-INERT or NEG-CLEAN, /048 pivots to a NON-asymmetric-tail axis (cycle-6 EXPLORATION 3/10) — likely on-chain or microstructure per LM Master /046 modal.

---

## 15. Phase 5 Brief Authoring Checklist (for /047 proper)

The full /047 brief must contain all sections of the v1 brief template, with these pre-fills from this outline:

- Section 0.0 — Banner (EXPLORATION; cycle-6 2/10; feature-family axis; anchor BASELINE_V1)
- Section 0.5 — Cadence (cycle-6 EXPLORATION 2/10; /034-/046 cycle-5+6 precedents cited)
- Section 0.6 — Axis Family `feature-family` + Rotation VALID (this outline §2)
- Section 1 — Hypothesis (this outline §1 verbatim)
- Section 2 — IS-only Numerical Evidence (post-EDA: §5 deliverables data tables with quoted values; F4/F5 gate outcomes documented)
- Section 2.5 — NORMAL-RISK (per §8 R7)
- Section 3 — Proposed Changes + LM Master response (LM Master invocation at Phase 4.5; brief addresses each recommendation: ADOPTED / MODIFIED / REJECTED)
- Section 4 — Falsifier F1–F5 (this outline §4 verbatim)
- Section 5 — Wall-clock ≤ 2.5h (this outline §9)
- Section 6 — Risk Mitigation R1–R7 (this outline §8)
- Section 7 — Pre-Registered Failure-Mode Prediction (refine §11 priors after pre-EDA)
- Section 8 — EXPLORATION verdict subtypes (PROMISING-CLEAN / PROMISING-WITH-CORRELATED-PRIMITIVE / NEG-INERT / NEG-CLEAN / BLOCK-PENDING-FIX)
- Section 9 — Smoke test pre-registration (this outline §12)
- Section 11 — Bundle composition disclaimers — NOT APPLICABLE (this is feature-family EXPLORATION, not bundle CONFIRMATION; no Section 11.A/B/C/D)

---

## 16. Open Questions for /047 Phase 5 Authoring

1. **Should the 21-bar window be parameterized for sensitivity check (e.g., 15-bar vs 21-bar vs 28-bar)?** **A:** No. Single-feature-at-a-time per the v3 `engineered_features_dont_stack` rule. /048 considers sensitivity ONLY IF /047 PROMISING. The 21-bar choice is anchored to the medium-term-regime literature (7-day window at 8h cadence) and the existing `regime_momentum_signed_5d` 5-day kernel for cross-feature timescale consistency.

2. **Should the 90-bar z-score window be parameterized similarly?** **A:** No, same reasoning. The 90-bar choice is anchored to the 30-day regime-stationarity window from the cross-asset 30-day correlation literature and matches `funding_rate_zscore_30` / `oi_delta_30_z90` z-score conventions in existing pruned features.

3. **Should ENSEMBLE_SIZE be raised from 3 (EXPLORATION default) to 5 (CONFIRMATION default) for this iteration?** **A:** No. /047 is EXPLORATION; the 3-seed ENSEMBLE_SIZE is by-convention. If PROMISING, /048+ multi-seed re-validates at ENSEMBLE_SIZE=10. Raising EXPLORATION budget pre-emptively is a methodology defect (it's a hidden HIGH-RISK upgrade).

4. **Should `stat_skew_20` be SIMULTANEOUSLY dropped from V1_FEATURE_COLUMNS_PRUNED if `skew_zscore_21` is added?** **A:** No. /047 is ADDITIVE (44→45). If F1 PASSES and F5 shows |IC| > 0.50 with `stat_skew_20`, /048 considers a head-to-head SWAP test (DROP stat_skew_20, KEEP skew_zscore_21) as a follow-up EXPLORATION. /047 must isolate the ADD effect; SWAP confounds add vs drop signal.

5. **Should the LM Master Phase 4.5 invocation produce a different recommendation given this is a feature-family axis?** **A:** Yes — LM Master at feature-family axes typically provides 2-4 HP recommendations (e.g., raise `colsample_bytree` to 0.85 if NEW feature is being added; adjust `feature_fraction` similarly; consider `lambda_l1` if NEW feature is suspected of being noisy). Brief Section 3 must address each. LM Master may also recommend ADDITIONAL features (e.g., realized kurtosis z-score, semi-variance); brief must REJECT those with /048+ deferral reasoning.

---

## 17. Honesty Discipline

This outline is DESIGNED to be honest about both branches:

- **PROMISING** branches (CLEAN, WITH-CORRELATED-PRIMITIVE) are NOT pre-judged as "the good outcome." They are evidence statements about a 45th feature's incremental edge contribution. PROMISING does NOT itself authorize MERGE; multi-seed CONFIRMATION at /048+ is required.
- **NEG-INERT** is NOT pre-judged as a "failure." Inventory ground-truth update is a substantive finding — it documents that asymmetric-tail z-score is reflected enough in `stat_skew_20` that no incremental edge exists at v1's EXPLORATION budget. This refines the feature surface for /048+ pivots.
- **NEG-CLEAN** is the inventory's strongest possible answer that the feature is NOT additive. It triggers RETIRE + feedback rule, mirroring /034's basis_zscore_30 closeout (3-consec INERT-then-DROP precedent extended to single-iter actively-harmful-DROP at /047).
- **BLOCK-PENDING-FIX** is the only true /047 process failure — F4/F5 fail OR src/ defect — and is corrected with one re-run cycle per the v1 single-rerun discipline.

Per THE PRIME DIRECTIVE: this outline DOES NOT pre-judge the outcome. The EDA designs the experiment; the experiment resolves what the EDA cannot.

---

*End of /047 pre-brief outline.*
