# iter-v3/082 — Research Brief — Funding-rate FEATURE FAMILY (cycle-3 EXPLORATION #1, Direction 1)

**Type**: EXPLORATION (cycle 3 #1 of 10)
**Axis**: a NEW crypto-native feature family — a 4-member **funding-rate family** added to `V3_FEATURE_COLUMNS` (14 → 18). Direction 1 of `briefs-v3/cycle3_plan.md`.
**Anchor**: BASELINE_V3.md `v0.v3-059` (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**), freshly re-validated at iter-v3/081 CONFIRMATION (IS +1.0894 exact / OOS +0.5999).
**EDA SHA**: `37d4da8` (`analysis/iteration_v3-082/funding_family_eda.py` + 6 result CSVs).
**Branch**: `iteration-v3/082`.

---

## Section 0 — Data Split Declaration

`OOS_CUTOFF_DATE = 2025-03-24` — **UNCHANGED, IMMUTABLE.** `training_months = 24` — **UNCHANGED, IMMUTABLE.**

- **IS window**: data-start (BCH 2020-01-01; LDO 2022-09-22; TRX 2020-01-15) → **2025-03-24** (exclusive).
- **OOS window**: **2025-03-24** → current data extent (~2026-05).
- The walk-forward / CPCV backtest runs continuously on full data; the reporting layer splits at `OOS_CUTOFF_DATE`. The QR has used **only IS data** in Phases 1–5; the QR sees OOS for the first time in Phase 7.
- The EDA script `analysis/iteration_v3-082/funding_family_eda.py` masks every computation to `open_time < OOS_CUTOFF_MS` (`1742774400000`). No OOS column is read, ranked, or filtered on. No design parameter (the family members, their window lengths, the feature count) was selected on OOS data — every choice traces to an IS-only EDA table or an a-priori literature-grounded default. (`feedback_no_cheating.md` Vectors 1+2.)
- `start_time` is **not** an iteration variable — the backtest runs from the earliest available data.

## Section 0.5 — Iteration Type Declaration

**TYPE: EXPLORATION.** Cycle-3 EXPLORATION #1 of 10 (iter-v3/082–091), followed by the SEPARATE CONFIRMATION iter-v3/092 — strict 10:1 cadence (`feedback_v3_strict_10_to_1_cadence.md`); the 10th EXPLORATION is NOT collapsed into the CONFIRMATION.

- **Wall-clock budget HARD CAP: 2h.** Config: `run_baseline_v3.py --exploration --n-trials 35`. `--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3` (ENSEMBLE_SEEDS outer-42 lineage subset `[191664963, 1662057957, 1405681631]`), single-seed-equivalent. n_trials=35 per the v3 EXPLORATION default (`feedback_v3_exploration_n_trials_35.md`) — raised from 10 specifically to fix the NEW-feature-family rank-14/14 INERT pattern that the original funding attempt /019 hit at n_trials=10.
- **Single primary axis**: V3_FEATURE_COLUMNS 14 → 18 (the 4-member funding family added). No labeling change, no symbol change, no risk-gate change, no model-architecture change. `V3_MODELS` stays BCH/LDO/TRX; `REQUIRED_GAP = 66 = (21+1)×3` unchanged (universe count unchanged).
- **Why EXPLORATION not CONFIRMATION**: this is a single-axis variation testing whether a researched funding *family* (vs the closed single z-score) carries IS-conditional signal worth a CONFIRMATION bundle slot. EXPLORATION never updates BASELINE_V3.md.
- Expected wall-clock ≈ 1.1–1.4h (the /078 universe EXPLORATION at the same `--exploration --n-trials 35` 3-symbol config ran ~1.2h; +4 features adds a small Optuna-search overhead). Within the 2h cap.

## Section 1 — Hypothesis

**Adding a 4-member funding-rate feature family — `funding_sign_persist_9`, `funding_momentum_3`, `funding_accel_3`, `funding_price_divergence_6` — to `V3_FEATURE_COLUMNS` (14 → 18) will lift IS monthly Sharpe by +0.10 to +0.35 over the /059 anchor, because the family encodes leveraged-positioning crowding, funding momentum/shock, and the funding-price-divergence reversal setup — derivatives-market information the 14 OHLCV-derived anchor features structurally cannot carry, and which the IS-only EDA (T4) shows separates winning from losing /081 baseline trades on BCH and TRX.**

This axis is materially different from the closed single-z-score funding axis (/019/023/024) — see Section 3.4 for the explicit differentiation the cycle-3 plan demands.

## Section 2 — IS-Only Numerical Evidence

All tables produced by the committed EDA `analysis/iteration_v3-082/funding_family_eda.py` (SHA `37d4da8`), IS-only (`open_time < 2025-03-24`). Funding-rate coverage: BCH 5727 IS rows, LDO 2741, TRX 5669; family non-NaN coverage 99.7–99.9% per symbol per feature.

### T1 — Funding-family vs triple-barrier-label Spearman IC (IS-only)

Reference: the closed single `funding_rate_zscore_30` had univariate IC ≈ 0.04–0.05 (diary /019).

| Feature | BCH IC | LDO IC | TRX IC | Pooled IC |
|---|---:|---:|---:|---:|
| funding_sign_persist_9 | -0.0011 | **-0.0851** | -0.0124 | -0.0306 |
| funding_momentum_3 | +0.0172 | -0.0240 | +0.0007 | +0.0040 |
| funding_accel_3 | +0.0149 | -0.0010 | -0.0091 | +0.0017 |
| funding_price_divergence_6 | +0.0020 | -0.0301 | -0.0324 | -0.0194 |

`funding_sign_persist_9` reaches |IC| 0.085 on LDO — materially above the single z-score's 0.04–0.05 baseline, and it is a *signed* signal (the z-score, being mean-zero, discards exactly this). Honest reading: univariate IC is modest (as it is for most of the 14 anchor features individually) — the IC test is necessary but not the load-bearing evidence; T3 (conditional) and T4 (baseline-trade) carry the axis.

### T2 — IC orthogonality vs the 14 anchor features (Critic Check 4)

Hard gate |IC| < 0.70; strict target < 0.50. **All 4 family members PASS on all 3 symbols, and all clear the strict 0.50 target** (single exception below):

| Feature | BCH max\|IC\| | LDO max\|IC\| | TRX max\|IC\| | vs |
|---|---:|---:|---:|---|
| funding_sign_persist_9 | 0.258 | 0.305 | 0.315 | ret_skew_200 / ema_spread_atr_20 / btc_ret_14d |
| funding_momentum_3 | 0.099 | 0.100 | 0.137 | vwap_dev_20 |
| funding_accel_3 | 0.023 | 0.039 | 0.039 | ret_skew_200 / btc_ret_14d |
| funding_price_divergence_6 | 0.239 | 0.306 | 0.218 | ema_spread_atr_20 / vwap_dev_20 |

Max |IC| across all 12 cells = **0.315** — far below 0.70 and below 0.50. The family carries information genuinely orthogonal to the price/return/vol/regime anchor stack. (The EDA's first pass exposed `funding_sign_persist_9` ~ `funding_level_ewm_9` at intra-IC 0.91 — `funding_level_ewm_9` was DROPPED at the EDA stage to avoid wasting `colsample_bytree` picks on a near-collinear pair; the pruned 4-member family is the result.)

**Intra-family diversity**: max intra-family |IC| is `funding_momentum_3` ~ `funding_accel_3` at 0.73–0.77 — a momentum / second-difference pair, the same expected-redundancy pattern as `hurst_100` ~ `hurst_diff_100_50` already in the anchor stack (Category-2 carve-out precedent, `feedback_v3_engineered_feature_pivot.md`). All other intra-family pairs |IC| < 0.40. Both `funding_momentum_3` and `funding_accel_3` are retained because the EDA shows them carrying *different* conditional signal (T3: on LDO, accel separates +0.0145 while momentum separates only -0.0041).

### T3 — Conditional forward-return separation by funding-family terciles (IS-only)

Top-tercile minus bottom-tercile of the 21-bar forward log return. |sep| > 0.012 flagged monotone:

| Feature | BCH sep | LDO sep | TRX sep |
|---|---:|---:|---:|
| funding_sign_persist_9 | -0.0114 | -0.0072 | +0.0017 |
| funding_momentum_3 | +0.0092 | -0.0041 | -0.0000 |
| funding_accel_3 | -0.0010 | **-0.0145** | -0.0014 |
| funding_price_divergence_6 | **+0.0145** | +0.0025 | +0.0058 |

`funding_price_divergence_6` produces a monotone +0.0145 BCH separation (high divergence → higher forward return — note: the screen labels the long side; the production model is direction-aware). `funding_accel_3` produces -0.0145 on LDO. Two of three symbols show at least one family member with monotone forward-return separation — conditioning on the feature *does* separate the forward-return distribution, which is exactly what the single z-score failed to do (rank 14/14 = no useful split).

### T4 — /081 IS-trade winner/loser separation by funding family at entry (THE load-bearing table)

On the /081 IS trade roster (BCH 83 trades / 49.4% WR; TRX 79 / 34.2%; LDO 9 — too few, skipped), the funding-family value at each trade's entry candle, winners (`net_pnl_pct > 0`) vs losers:

| Symbol | Feature | Winner mean | Loser mean | Gap |
|---|---|---:|---:|---:|
| BCH | funding_sign_persist_9 | -0.0027 | **+0.1799** | -0.1826 |
| BCH | funding_price_divergence_6 | +0.0299 | **+0.1701** | -0.1402 |
| TRX | funding_sign_persist_9 | +0.2263 | **+0.4444** | -0.2181 |
| TRX | funding_price_divergence_6 | -0.0738 | **+0.4021** | -0.4760 |

(`funding_momentum_3` / `funding_accel_3` winner/loser gaps are near-zero at the per-trade entry level — they carry forward-return signal, T3, not entry-quality signal; they remain in the family because T3 shows their conditional value.)

**This is the bottleneck the axis targets.** On BOTH BCH and TRX — independent per-symbol models — losing trades systematically entered when funding was crowded-long (`funding_sign_persist_9` high) and funding-price-divergent (`funding_price_divergence_6` high). Winning trades entered at neutral funding. The direction is *consistent across two symbols*: it is not a single-symbol artifact. This is the BIS WP 1087 / "crowded at the high" mechanism, measured directly on v3's own baseline roster: the 14 anchor features cannot see leveraged-positioning crowding, so the baseline model has been entering trades into crowded-long setups that subsequently lose. A funding family gives the model the signal to discriminate those entries.

### T5 — ADF stationarity (Critic Check 5)

All 12 cells (4 features × 3 symbols) **stationary** at p < 0.05; in fact all p ≤ 5e-4 and most p < 1e-15. No regime-indicator exemption needed.

### T6 — Marginal regime-label correlation (necessary, not sufficient)

Spearman IC of each family member vs a within-IS bull-regime proxy (270-bar SMA slope > 0, `.shift(1)`-lagged):

| Feature | BCH | LDO | TRX |
|---|---:|---:|---:|
| funding_sign_persist_9 | +0.165 | +0.206 | +0.101 |
| funding_momentum_3 | +0.013 | +0.015 | +0.008 |
| funding_accel_3 | +0.014 | +0.037 | +0.006 |
| funding_price_divergence_6 | +0.050 | -0.012 | +0.031 |

`funding_momentum_3` and `funding_accel_3` have near-zero marginal regime correlation (≤ 0.04) — these are the cleanest. `funding_sign_persist_9` has moderate correlation (0.10–0.21) — economically expected (sustained positive funding correlates with bull regimes) — and `funding_price_divergence_6` is near-zero on 2 of 3. Per the /076 lesson, MARGINAL orthogonality is necessary but NOT sufficient: the binding test is CONDITIONAL orthogonality (SHAP/split-allocation vs regime), pre-registered in Section 8.3.

## Section 3 — Proposed Changes

### 3.1 The funding-rate family — 4 new features

A new computation in `src/crypto_trade/features_v3/funding_v3.py` and a new GROUP_REGISTRY entry build these 4 columns. Construction (all past-only — see 3.3):

| Feature | Definition | What it encodes |
|---|---|---|
| `funding_sign_persist_9` | mean of `sign(funding_rate).shift(1)` over trailing 9 settlements (3 days) | crowding DIRECTION + PERSISTENCE — a mean-zero z-score structurally cannot carry this |
| `funding_momentum_3` | `funding_rate[t] − funding_rate[t−3]` (1-day change) | funding momentum — leverage building/unwinding |
| `funding_accel_3` | `momentum_3[t] − momentum_3[t−3]` (second difference) | funding ACCELERATION / carry SHOCK (BIS WP 1087: carry shocks, not levels, predict liquidation jumps) |
| `funding_price_divergence_6` | z(trailing-6-bar cum funding, 60-bar) − z(trailing-6-bar price return, 60-bar), clipped ±10 | the "crowded at the high" reversal setup — funding extended while price stalls |

`V3_FEATURE_COLUMNS_TOP_N` goes 14 → **18**. The 14 anchor features are UNCHANGED and KEPT (no removal — single-axis discipline: the only change is the *addition* of the family). Feature order: the 14 anchor features first (unchanged order), then the 4 funding family members appended.

### 3.2 Data-acquisition plan (Direction-1 prerequisite per cycle-3 plan §3)

**No new fetch infrastructure is required.** v3 already has a complete funding-rate data pipeline, built at iter-v3/019:

- **Feed**: Binance Futures REST endpoint `/fapi/v1/fundingRate` (the canonical funding-rate history endpoint).
- **CLI**: `uv run crypto-trade fetch-funding --symbols <SYM>` (`src/crypto_trade/main.py:1009` `_cmd_fetch_funding`). Incremental, cached.
- **Cache**: `data/funding_rates/<SYMBOL>.csv`, schema `funding_time` (ms epoch), `funding_rate` (float). **Verified present and current** for all 3 v3 symbols: BCH 6994 rows (2019-12→2026-05), LDO 3971 rows (2022-09→2026-05, covering the full LDO IS window), TRX 6914 rows (2020-01→2026-05).
- **Engineering build for /082**: only `src/crypto_trade/features_v3/funding_v3.py` is extended — a new `compute_funding_family` function building the 4 columns, plus a new GROUP_REGISTRY entry `funding_family_v3` registered in `features_v3/__init__.py`. The runner regenerates the v3 parquets via the existing `process_symbol_v3` path (no `--skip-features`). The Phase-6 QE should re-run `fetch-funding` for BCH/LDO/TRX first to guarantee the cache `funding_time` extends within the 16h staleness window, then regenerate parquets.

This is a real but contained engineering build — a new feature-family function and a registry entry, not a new fetcher. The funding-rate data infrastructure cost was already paid at /019; the cycle-3 investment here is the *family construction* the single-z-score attempt never made.

### 3.3 Look-ahead discipline

The funding rate AT bar `t` SETTLED at candle `open_time` T and is broadcast ~5 min before the 8h boundary — `funding_rate[t]` is fully knowable at bar `t` open. This is the identical convention the existing `funding_v3.py` uses and `tests/features_v3/test_funding_v3.py` enforces.

- `funding_sign_persist_9`: `sign(rate).shift(1).rolling(9).mean()` — the 9-bar window is `[t−9, t−1]`; bar `t`'s own settlement is excluded from its own window. Past-only.
- `funding_momentum_3` = `rate[t] − rate[t−3]`: `rate[t]` past-only by broadcast; `rate[t−3]` trivially so.
- `funding_accel_3` = `momentum[t] − momentum[t−3]`: past-only by `funding_momentum_3` construction.
- `funding_price_divergence_6`: both the cumulative-funding leg and the price-return leg are `.shift(1)`-lagged before the 6-bar window and the 60-bar z-score normalisation — window `[t−6, t−1]`, normalisation history `[t−66, t−1]`. Past-only.

Phase-6 unit tests (Section 3.6) include spike-perturbation tests: perturbing `funding_rate[t+k]` for any `k ≥ 0` must NOT change any family value at bar `t`.

### 3.4 Why this axis is DIFFERENT from the closed funding axis (/019/023/024) — the cycle-3-plan-mandated differentiation

The cycle-3 plan §3 explicitly requires this brief to address why a funding axis differs from the PERMANENTLY-CLOSED /019/023/024 funding axis. The closed axis is `funding_rate_zscore_30` — **one feature, a rolling 30-bar z-score**. The differentiation is structural, not cosmetic:

1. **A z-score is mean-zero by construction — it discards SIGN and LEVEL.** `funding_rate_zscore_30` answers only "is funding unusual vs its own recent 30-bar mean". It cannot encode "funding has been positive (leveraged-long crowded) for 9 straight settlements" — because subtracting the rolling mean removes exactly the persistent-level information. `funding_sign_persist_9` and the funding-price-divergence feature are built specifically to carry the crowding-direction signal the z-score throws away. The EDA T4 winner/loser separation is *on the sign-persistence and divergence features* — the z-score, by construction, could not have produced that table.

2. **It was ONE feature on a 14-column loss surface.** /019 (n_trials=10), /023 (n_trials=35), /024 (n_trials=35, BTC cross-asset variant) all added a single 14th column. A single new feature competing for `colsample_bytree` picks against 13 incumbents needs a high univariate rank to be split on — and the diaries explicitly attribute the rank-14/14 outcome to that. A 4-member family of *correlated-but-diverse* funding views (the family covers crowding, momentum, shock, divergence) gives the model multiple complementary entry points into the funding signal; LightGBM can compose a funding-conditional rule from several family members even if no single one would rank top-half alone. This is the same logic that motivated the cycle-3 plan's "researched family with proper construction is a different axis" carve-out.

3. **It is not univariate-rank-selected.** /070-era lesson (`feedback_v3_inert_features_at_higher_budget.md`): a feature chosen by univariate Spearman ρ correlates with incumbents and wastes picks. The /082 family is selected by (a) literature-grounded construction (sign/level, momentum, shock, divergence — the four channels the funding literature identifies) and (b) the T4 baseline-trade attribution that shows a real bottleneck. Section 8 pre-registers a *multivariate* contribution test (the conditional-orthogonality / cluster-importance test), not a univariate rank.

4. **The /019/023 OOS collapse was an INERT-feature-overfit artifact, not a funding-signal verdict.** The /023/024 OOS −1.07/−0.82 collapses are documented (`feedback_v3_inert_features_at_higher_budget.md`) as: adding an *inert* 14th column expands Optuna's search space along an uninformative dimension → IS-overfit hyperparameters. That mechanism applies to a feature the model *does not use*. If the /082 family is genuinely used (the EDA T3/T4 evidence says it should be), the INERT-overfit mechanism does not trigger. If the /082 family is NOT used — it ranks 18/18 — then /082 reproduces the INERT verdict and is correctly classified INERT (Section 8). The honest position: /082 is a genuine retest of the funding *signal* under a *family* construction, and the classification taxonomy handles both outcomes.

The runner's existing pre-flight assertions ban the literal names `funding_rate_zscore_30` and `btc_funding_rate_zscore_30` — the /082 family uses four entirely distinct names and does NOT re-introduce the banned columns. The QE retains those bans (the closed single-z-score axis stays closed) and adds the 18-feature-count assertion.

### 3.5 No changes to labeling, symbols, risk gates, model architecture

- Labeling: triple-barrier `(atr_tp=2.0, atr_sl=1.0)`, 21-candle timeout — UNCHANGED.
- `V3_MODELS`: BCH/LDO/TRX — UNCHANGED. `V3_EXCLUDED_SYMBOLS` — UNCHANGED.
- 7-primitive risk-gate stack — UNCHANGED. `vol_scale_floor_per_symbol={}` (the /081 revert) — KEPT.
- Model: per-symbol LightGBM, unified ensemble — UNCHANGED. `--exploration` → ENSEMBLE_SIZE=3.
- `REQUIRED_GAP = 66`, embargo 22 — UNCHANGED (universe count unchanged).

### 3.6 Engineering checklist for Phase 6

1. `fetch-funding --symbols BCHUSDT,LDOUSDT,TRXUSDT` to refresh the funding cache within the 16h staleness window.
2. Implement `compute_funding_family` in `funding_v3.py` (4 columns; the EDA's `build_funding_family` is the reference implementation — the runner version reads the cache like `add_funding_v3_features` does).
3. Register `funding_family_v3` in `GROUP_REGISTRY` (`features_v3/__init__.py`).
4. Append the 4 names to `V3_FEATURE_COLUMNS_TOP_N` (14 → 18).
5. Update the runner pre-flight: `n != 14` → `n != 18`; KEEP the `funding_rate_zscore_30` / `btc_funding_rate_zscore_30` bans (closed single-z-score axis stays closed).
6. Per Critic /081 Rec #3: add a generalised "config == /059-canonical config" pre-flight accretion check (Section 5).
7. Regenerate v3 parquets (no `--skip-features`). New unit-test file `tests/features_v3/test_funding_family_v3.py` (≥5 tests: past-only spike perturbation, NaN warm-up, clip bounds, registry smoke, FileNotFoundError on missing cache).
8. `ITERATION_LABEL = "v3-082"`.

## Section 4 — Expected OOS Impact

### 4.1 Predicted impact

- **IS monthly Sharpe**: +0.10 to +0.35 over the /059 anchor (+1.0894 → predicted band **[+1.19, +1.44]**), central **+0.20**. Rationale: the funding family gives the model entry-quality discrimination the T4 table shows is missing; the model should avoid the crowded-long losing entries. EXPLORATION single-seed has wide variance — the band is deliberately wide.
- **OOS monthly Sharpe**: roughly flat to modestly positive, **[+0.40, +0.85]** vs the /081-confirmed +0.5999, central **+0.60**. A funding family is not a holding-time-extension axis (Section 4.3), so it should not load the OOS-favourable regime factor the way SL widening did — OOS should track IS, not soar.
- EXPLORATION-mode anchor: per the iter-v3/077 anchor-staleness note, the current-code 14-feature no-axis baseline is **IS +0.8236 / OOS +0.2078** (EXPLORATION-mode reference). The /082 run is `--exploration` 3-seed, so its raw numbers compare to the EXPLORATION-mode reference; the *canonical* anchor for the verdict is /059 (IS +1.0894 / OOS +0.5791). The engineering report must report both comparisons.

### 4.2 Falsifier (LOCKED)

**If IS monthly Sharpe Δ < +0.10 vs the EXPLORATION-mode current-code reference (IS +0.8236), the hypothesis is FALSIFIED** — the funding family did not lift IS, the axis is NEGATIVE/INERT, and the family does not advance to the iter-v3/092 CONFIRMATION bundle.

Supplemental feature-level falsifier (per `feedback_v3_inert_features_at_higher_budget.md` / the /019 INERT precedent): **if all 4 family members rank in the bottom quartile (rank ≥ 14/18) of LightGBM importance across ≥ 2 of 3 symbols, the family is INERT** — the model did not learn the funding signal, regardless of the IS Sharpe number, and the axis is classified INERT (the /019 outcome reproduced under a family construction). For PROMISING, at least one family member must rank ≤ 9/18 (top half) for ≥ 1 symbol AND absolute importance ≥ 30 (the Category-1 multivariate-contribution bar).

### 4.3 Holding-time / roster-composition predictor (`feedback_v3_is_oos_regime_divergence.md`)

A feature-only axis touches **no barrier** — no SL, no TP, no timeout, no labeling. So the holding-time-EXTENSION channel (the /065/071/073 mechanism) is mechanically OFF: the family cannot lengthen a single trade's duration. **Predicted full-roster mean/median trade-duration Δ: 0.000 candles** (mechanically forced — barriers unchanged).

But per the /076 lesson, a feature can still load the regime factor via trade SELECTION — the family changes WHICH trades the model picks, and if the added trades skew longer-held than the removed trades (and longer-held trades are OOS-favourable in v3's OOS uptrend), the regime factor loads via composition. **Pre-registered sub-channel predictor**: on the anchor-vs-/082 OOS roster diff, the **added-vs-removed trade-set mean-duration gap is predicted ≤ +0.5 candles** (the funding family discriminates entry *quality* by crowding, not by duration — there is no mechanical reason a funding-crowding feature systematically picks longer-held trades). **Sub-channel falsifier (LOCKED): if the added-vs-removed mean-duration gap > +1.0 candle, the family loaded the regime factor via selection** — the OOS lift (if any) is regime-luck, not edge, and the axis is SUSPICIOUS regardless of the IS number. This gap will be computed under the production Optuna-tuned barrier parameterisation (the /078 lesson: a screen-grade fixed-parameter proxy under-predicts the timeout-trade tail).

### 4.4 OOS/IS ratio SUSPICIOUS gate (LOCKED — `feedback_v3_oos_is_ratio_gate.md`)

**OOS/IS monthly Sharpe ratio > 3.0 → SUSPICIOUS classification**, regardless of absolute OOS magnitude. AND the OOS-DOMINANT sub-mode: **IS Δ < 0 AND OOS Δ ≥ +0.20 → SUSPICIOUS-OOS-DOMINANT** (the /078 signature). Both are pre-registered supplemental classifiers; the ratio is the `comparison.csv` `monthly_sharpe` row ratio.

## Section 5 — Risk Mitigation

This is a feature-addition axis — it adds no risk primitive and removes none. The 7-primitive risk-gate stack is UNCHANGED (BTC-trend kill, vol scaling, ADX, Hurst regime, feature z-score OOD, low-vol filter, hit-rate DISABLED).

- **R-feature-overfit (the /019/023 precedent)**: the documented funding-axis failure mode is INERT-feature-overfit — adding an unused 18th–21st column expands Optuna's search and degrades OOS. **Mitigation**: (a) the EXPLORATION classification taxonomy (Section 8) explicitly catches this — an unused family is classified INERT and does not advance; (b) EXPLORATION mode uses ENSEMBLE_SIZE=3 + n_trials=35, the configuration `feedback_v3_exploration_n_trials_35.md` calibrated to give a NEW feature family a fair chance to be learned (vs the n_trials=10 of /019); (c) the family is 4 *complementary* features, not 1 — the model has multiple entry points, reducing the rank-14/14 single-feature failure mode.
- **R-IC-redundancy**: max |IC| vs the 14 anchors is 0.315 (T2) — far below the 0.70 hard gate; the family does not duplicate an incumbent. Intra-family max |IC| 0.77 (`funding_momentum_3` ~ `funding_accel_3`) is the expected momentum/second-difference pair (carve-out precedent) and the two carry different conditional signal (T3).
- **Config-accretion pre-flight (Critic /081 Rec #3)**: /082 touches `run_baseline_v3.py` setup, so per the cycle-3-plan §5 mandate the runner gains a generalised **"config == /059-canonical config" accretion check** — a pre-flight that asserts every behavior-affecting knob (DEFAULT_ATR_MULTIPLIERS, V3_ATR_MULTIPLIERS_PER_SYMBOL, V3_MODELS, RiskV2Config gate thresholds, vol_scale_floor_per_symbol, block_long/short_for, the enable flags) matches the /059 canonical values, with the SOLE intended /082 delta being the 14→18 feature-count change. This catches a future /061-style accretion at runtime, not by archaeology. The QE implements this as an explicit `_verify_canonical_config_accretion()` pre-flight that lists the /059 expected values and raises `ValueError` on any unexplained drift.

## Section 6 — Risk Management Design

v3's risk stack is the 7-primitive RiskV3Wrapper. /082 changes NONE of it. Fire-rate predictions are therefore identical to the /059/081 baseline — the funding family is a *model-input* change, not a *gate* change, so no gate's fire rate moves by construction.

| Primitive | /082 status | Fire-rate vs /059 |
|---|---|---|
| BTC-trend kill | UNCHANGED | identical |
| Vol scaling | UNCHANGED | identical |
| ADX threshold (20.0) | UNCHANGED | identical |
| Hurst regime | UNCHANGED | identical |
| Feature z-score OOD (2.0) | UNCHANGED | identical |
| Low-vol filter | UNCHANGED | identical |
| Hit-rate | DISABLED (unchanged) | n/a |

Regime coverage: the funding family is *itself* a regime-information enrichment — it gives the model a leveraged-positioning-crowding view it lacked. The mechanism by which it should *improve* risk-adjusted return is entry-quality discrimination (T4): the model avoids entering into crowded-long setups that the EDA shows subsequently lose. This is signal-quality improvement upstream of the gates, not a new gate.

## Section 7 — Pre-Registered Failure-Mode Prediction

The single most plausible way /082 fails OOS: **the funding family is learned and lifts IS, but the lift is regime-correlated and does not carry to OOS — a SUSPICIOUS-OOS-DOMINANT or INERT outcome.**

Concretely, two failure paths, and a third honest one:

1. **INERT (probability ≈ 40%)** — the most likely failure. The family ranks bottom-quartile across symbols (the /019/023/024 outcome reproduced). LightGBM at EXPLORATION budget does not split on the funding family meaningfully; the IS Sharpe move is colsample/hyperparameter noise on an 18-column surface, not funding signal. The gates that catch it: the Section 4.2 feature-level falsifier (all 4 members rank ≥ 14/18 across ≥ 2 symbols). In metrics: IS Δ inside the ±0.10 noise band, trade roster near-bit-identical to /081, family importance flat. This is a real risk because three prior funding attempts hit exactly this — though all three were *single*-feature; the family construction is the specific hedge, and whether it is enough is the open question /082 answers.

2. **SUSPICIOUS-OOS-DOMINANT (probability ≈ 25%)** — `funding_sign_persist_9` has moderate marginal regime correlation (T6: 0.10–0.21). If the model leans on the sign-persistence feature and that feature is regime-loaded, the family could lift OOS (the OOS uptrend has persistent positive funding) while IS stays flat or slips — the /078 signature (IS Δ < 0, OOS Δ ≥ +0.20). The gates that catch it: the Section 4.4 OOS-DOMINANT sub-mode + the OOS/IS > 3.0 ratio gate + the Section 4.3 added-vs-removed duration sub-channel falsifier. In metrics: IS flat/down, OOS up, OOS/IS ratio elevated.

3. **NEGATIVE (probability ≈ 15%)** — the family is partially used but the funding signal, conditioned on v3's specific 3-symbol roster and the triple-barrier label, is net-harmful: it shifts the model toward funding-conditional entries that underperform on this universe. IS Δ < −0.10. The /019/023 OOS-collapse mechanism (inert column expands overfit space) is the related risk if the family is half-learned.

Residual ≈ 20% PROMISING — the family is learned, lifts IS (T3/T4 say it should), and OOS tracks IS without the regime signature. Per the /078 calibration discipline, the SUSPICIOUS probability is held near the running base rate (cycle 2's SUSPICIOUS base rate was 4/10 ≈ 40% across all axis types; for a feature-only holding-time-orthogonal axis the rate should be lower than the cycle-wide rate — funding features touch no barrier — so ≈ 25% is the floored estimate, not below it). The central forecast leans INERT/PROMISING; the honest reckoning is that the funding axis has a 3-data-point INERT track record and the family construction is the explicit, literature-grounded attempt to break it — /082 is a genuine, well-motivated retest, not a knob retune.

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (LOCKED classification taxonomy)

This is an EXPLORATION — it never updates BASELINE_V3.md. The taxonomy classifies the axis for the iter-v3/092 CONFIRMATION-bundle decision. Anchor: EXPLORATION-mode current-code reference **IS +0.8236 / OOS +0.2078** for delta computation; the /059 canonical numbers (IS +1.0894 / OOS +0.5791) frame the absolute bands. Evaluation order is disjunctive — **SUSPICIOUS → NEGATIVE → PROMISING → INERT** — first match is canonical.

### 8.1 PROMISING
IS Δ ≥ **+0.10** vs the EXPLORATION-mode reference AND OOS Δ ≥ **−0.10** (OOS not collapsed) AND `frac_positive_paths` ≥ 0.50 AND NOT SUSPICIOUS AND at least one family member ranks ≤ 9/18 with absolute importance ≥ 30 for ≥ 1 symbol (the family is genuinely used — Section 8.3). → the funding family advances to the iter-v3/092 CONFIRMATION bundle as an edge-ingredient candidate.

### 8.2 NEGATIVE
IS Δ < **−0.10** OR OOS Δ < **−0.20**. → the family hurts; CLOSED for cycle 3; does not advance.

### 8.3 SUSPICIOUS (disjunctive precedence — fires before PROMISING)
- **Ratio gate**: OOS/IS monthly Sharpe ratio > **3.0**. OR
- **OOS-DOMINANT sub-mode**: IS Δ < 0 AND OOS Δ ≥ **+0.20**. OR
- **Holding-time sub-channel**: added-vs-removed OOS-roster mean-duration gap > **+1.0 candle** (Section 4.3), computed under production Optuna-tuned barriers.
- **CONDITIONAL-ORTHOGONALITY test (NEW-feature-family requirement, /076 lesson)**: marginal orthogonality (T2/T6) is necessary but NOT sufficient. The Phase-6 engineering report must compute, per symbol, the Spearman correlation between each family member's **LightGBM split-allocation / importance share** and the within-IS bull-regime label, and report it in a `conditional_orthogonality` table (the /077 instrument exists). If a family member the model *relies on* (importance ≥ 30) has split-allocation-vs-regime correlation > 0.50, the family's IS lift is regime-loaded → SUSPICIOUS even if the marginal IC was clean. → a SUSPICIOUS axis produces no edge ingredient; does not advance.

### 8.4 INERT
Both IS Δ and OOS Δ inside the ±0.10 / ±0.20 noise bands AND NOT SUSPICIOUS; OR all 4 family members rank ≥ 14/18 (bottom quartile) across ≥ 2 of 3 symbols (the /019 feature-level INERT signature). → the funding family is not learned at EXPLORATION budget; recorded; does not advance. An INERT-at-EXPLORATION funding family would, combined with /019/023/024, make a 4-data-point structural verdict — the brief acknowledges this stake honestly.

### 8.5 NULL-RESULT
Trade roster bit-identical to /081 (the family changed zero trades). Listed for taxonomy completeness; a 4-feature addition that the model uses at all is mechanically unlikely to be bit-identical.

## Section 9 — Library Stack Declaration

No new dependencies. The funding family is built with `numpy` + `pandas` only (the existing `funding_v3.py` convention — stdlib + numpy + pandas). Pinned stack carried from /059/081: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. `statsmodels.tsa.stattools.adfuller` (already a dependency) is used for the Section-2 T5 ADF table and the runner's per-feature ADF report.

## Section 10 — QR Audit Trail (literature-research path)

Per `briefs-v3/cycle3_plan.md` §2, this section documents the genuine WebSearch/WebFetch literature research that motivated the axis. Cycle-3 mandate: research before EDA.

**The research path.** The cycle-3 plan named funding-rate term structure / regimes as the top Direction-1 candidate. I researched the 2023–2025 funding-rate literature via WebSearch/WebFetch before any EDA:

1. **BIS Working Paper No. 1087, "Crypto carry" (2025)** — the single most actionable empirical reference for a crypto futures bot. Finding: crypto carry (funding/basis) is large and time-varying (average annualised carry 6–8%, frequently > 20%); a **carry SHOCK predicts a liquidation jump** — a 10% carry shock → ~22% jump in sell liquidations. Contribution to the axis: this is *why* `funding_accel_3` (funding acceleration = the second difference = the carry-shock proxy) is a family member — the BIS result says carry *shocks*, not carry *levels*, carry the predictive content. The single z-score has no acceleration channel.

2. **"The Two-Tiered Structure of Cryptocurrency Funding Rate Markets," MDPI Mathematics 14(2):346 (2025)** — funding-rate markets have structure beyond a single noisy series; persistent funding regimes encode positioning. Contribution: motivates `funding_sign_persist_9` (sign persistence over a multi-day window) as a regime/crowding-direction encoding distinct from a deviation z-score. (The MDPI page returned HTTP 403 to WebFetch; the WebSearch result summary supplied the finding.)

3. **CFB Benchmarks, "Revisiting the Bitcoin Basis: How Momentum & Sentiment Impact the Structural Drivers of Basis Activity" (2024)** and the **funding-rate-as-sentiment-indicator literature (Phemex Academy; the funding-reversal-signal search results)** — the empirical "crowded at the high" finding: *"price was no longer making upward progress yet funding stayed extended to the upside … ends up resulting in a violent unwind in the opposite direction."* Funding extremes above the 90th percentile precede trend exhaustion. Contribution: this is the direct motivation for `funding_price_divergence_6` — the funding-crowding-minus-price-progress divergence; the family member that encodes the reversal setup. The single z-score has no price leg, so it cannot represent divergence.

4. **The funding-rate-arbitrage / carry literature (Gate Learn 2025; the basis-and-carry search results)** — confirms funding rates carry tradeable information at the 8h cadence and that the 8h candle is exactly one funding-settlement period — the structural reason the v3 8h cadence is well-suited to funding features (cycle-3 plan §3, Direction 1).

5. **Open-interest / liquidation-cascade research (the OI-divergence search results; Ali SSRN 5611392 2025 context)** — I researched OI dynamics as the *alternative* Direction-1 axis. OI delta as a leverage-stretch signal is real, but v3 has **no OI data feed** (the `data/funding_rates/` cache exists; there is no OI cache) — an OI axis would require building a new fetcher first. Funding has a *complete, current data pipeline already in place* (built at /019). Per the cycle-3 plan's instruction to pick the higher-expected-value axis, funding wins on data-readiness: the engineering cost is a feature-family function, not a new fetcher + a multi-month backfill.

**How I got from "literature says X" to "the /082 axis is Y".** The literature converges on four channels of funding predictive content — crowding sign/persistence (MDPI), funding momentum, funding acceleration / carry shock (BIS WP 1087), and funding-price divergence (CFB / the crowding-reversal literature). The v3 closed funding axis (/019/023/024) used a single rolling z-score, which is mean-zero and price-blind — it captures *none* of the four channels cleanly (it captures only "funding unusual vs recent mean"). The /082 axis is the 4-member family that encodes exactly those four channels, one feature per channel. The IS-only EDA (`37d4da8`) then validated the construction on v3's own data: T2 confirmed orthogonality to the 14 anchor features, T3 confirmed conditional forward-return separation, and T4 — the load-bearing table — showed on v3's own /081 baseline roster that losing trades systematically entered into crowded-long / funding-price-divergent setups on both BCH and TRX. Research motivated the family; the EDA proved it targets a real, measured bottleneck.

**Direction-2 (universe expansion) consideration.** I also researched Direction 2. The universe-expansion literature search returned mostly retail portfolio-allocation content, not rigorous cross-sectional factor research — and the v3 catalog already has two failed universe expansions (/021 HBAR+AVAX, /069 ADA) plus the /078 SUSPICIOUS swap, all of which failed because a per-symbol IS-edge screen does not transfer to portfolio-aggregate lift under BCH dominance. Direction 1 (funding family) has (a) a stronger, more specific 2023–2025 research base, (b) a complete data pipeline already built, and (c) a load-bearing EDA table (T4) measured on v3's own roster. It is the higher-expected-value first bold axis. Universe expansion remains a strong Direction-2 candidate for a later cycle-3 slot (iter-v3/083+).

**No OOS data was consulted in selecting any /082 design parameter.** The family members, their window lengths (9-bar persistence, 3-bar momentum, 6-bar divergence, 60-bar normalisation), and the 14→18 feature count all trace to either an IS-only EDA table or an a-priori literature-grounded default (e.g. the 3-bar window = 1 day at 8h cadence; the 9-bar window = 3 days). The EDA masks every computation to `open_time < 2025-03-24`.

**Setup commit SHA**: `87195d1` (`feat(iter-v3/082)`: funding-family axis + config-accretion pre-flight; V3_FEATURE_COLUMNS 14→18; ITERATION_LABEL v3-082; 204 features_v3 + lookahead-embargo tests pass; ruff clean).
**EDA SHA**: `37d4da8`. **Brief SHA**: `275d24a`. **Phase 5.5 gate SHA**: (TBD, QE).
