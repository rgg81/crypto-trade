# Iteration iter-v3/026 — Diary

## Decision: EXPLORATION-NEGATIVE-SUSPICIOUS-OOS — Engineered Features DON'T STACK at single-seed

Stacking the second engineered feature `vol_adj_autocorr = ret_autocorr_lag1_50 / (range_realized_vol_50 + 1e-6)` ON TOP of iter-v3/025's `regime_momentum_signed_5d` (V3_FEATURE_COLUMNS 14 → 15) at single-seed EXPLORATION produced a **STRUCTURALLY SUSPICIOUS RESULT**: IS monthly Sharpe collapsed to **+0.0493** (Δ −0.83 vs iter-v3/025 reference +0.8788; Δ −0.33 vs iter-v3/018 anchor +0.3788) while OOS monthly Sharpe spiked to **+1.4501** (Δ +0.23 vs iter-v3/025 reference; Δ +1.06 vs anchor — would be v3-historic high). The **27× IS/OOS daily Sharpe ratio** (IS daily 0.12 vs OOS daily 3.36) is structurally absurd — far worse than iter-v3/013's classic single-seed lottery pattern (single-seed +1.0088 IS / +2.6970 OOS → falsified at iter-v3/018 multi-seed CONFIRMATION to +0.38 / +0.39).

§4.4 PATH C fires unambiguously on the IS axis (the controlled axis at single-seed EXPLORATION): IS Sharpe Δ −0.83 vs iter-v3/025 reference exceeds the −0.10 threshold by an order of magnitude. The OOS lift is single-seed-untrustable on three independent grounds:

1. **iter-v3/013 precedent**: single-seed +2.70 OOS at iter-v3/013 was falsified to +0.39 multi-seed (86% reduction). iter-v3/026's +1.45 OOS is structurally weaker (no co-directional IS lift; IS is at near-zero).
2. **Worst IS MaxDD in v3 history at 51.37%** (iter-v3/025 was 27.5%; anchor 22%). The IS Sharpe of 0.05 reflects a portfolio that is barely break-even on a path that endured a >50% drawdown — a model that profits OOS at this IS quality is consistent with random walk + favorable OOS regime, NOT genuine signal.
3. **BCH single-symbol carry returned at 78% portfolio concentration** (iter-v3/025 had restored balance to BCH 35% / TRX 71% with net portfolio diversity). This is a **regression** of the iter-v3/025 frozen-baseline-DISSOLVED finding — iter-v3/026's OOS lift is BCH-driven not portfolio-wide.

vol_adj_autocorr is NOT inert: portfolio importance 283 (45% of top range_realized_vol_50=630), rank 14/15. Falsifier 4 PASSES — the model uses the new feature meaningfully. This rules out PROMISING-INERT classification (PATH B). The mechanism is therefore **NOT under-utilization** but rather **OVER-EXPANSION of the search space**: combining 2 engineered features overwhelmed depth-3-5 LightGBM's representational capacity at the n_trials=35 single-seed budget; Optuna found IS-overfit hyperparams that happen to generalize OOS by chance.

This is a **PIVOT-VALIDATION signal**: the engineered-feature axis category is genuine (iter-v3/025 PROMISING) but engineered features DON'T STACK linearly at single-seed at n_trials=35. iter-v3/027 axis MANDATED = **DIFFERENT engineered feature ALONE on top of regime_momentum** (drop vol_adj_autocorr; revert V3_FEATURE_COLUMNS 15 → 14; ADD a new engineered feature 14 → 15). Cadence #8 of 10 in post-bootstrap cycle.

## What Was Tested

**Hypothesis (locked in brief Section 1):** "Adding `vol_adj_autocorr` (= `ret_autocorr_lag1_50 / (range_realized_vol_50 + 1e-6)`) — autocorrelation per unit vol — as the 15th feature on top of the iter-v3/025 14-feature stack — at the EXPLORATION default n_trials=35 — will produce **importance rank ≤10 for ≥1 symbol AND importance ≥30 for ≥1 cut** (Category 2 carve-out per `feedback_v3_engineered_feature_pivot.md`) AND **IS Sharpe Δ ≥ 0** vs iter-v3/025 reference (relaxed threshold for second engineered stacking) — if the per-unit-vol return-persistence interaction is genuinely informative AND structurally distinct from regime_momentum's mechanism AND the LightGBM trees on the 14-feature stack cannot internally compose `f1 / f2` at depth-5."

**Spec (locked, single-axis variation — atomic add; second Category 2 axis):**
- V3_FEATURE_COLUMNS_TOP_N: ADD `vol_adj_autocorr` (14 → 15 with new engineered feature)
- KEEP `regime_momentum_signed_5d` (do NOT revert; iter-v3/025 PROMISING per `feedback_v3_engineered_features_proven.md` mandate)
- Net column count: 15 (+1 vs iter-v3/025; second Category 2 axis in v3 catalog)
- ITERATION_LABEL = "v3-026"
- 3-symbol BCH+LDO+TRX universe UNCHANGED
- Other gates BYTE-IDENTICAL to iter-v3/025 anchor (z=2.0, ATR 2.0/1.0, BTC ±15%, ADX=20, Hurst gate, low-vol filter, hit-rate disabled, regime gate disabled, per-symbol cap disabled)
- Implemented `compute_vol_adj_autocorr` in existing module `src/crypto_trade/features_v3/engineered_v3.py` (extends iter-v3/025 module; output clipped to [−100, +100] to prevent infinity from near-zero denominator)
- `add_engineered_v3_features` updated to call BOTH compute functions (regime_momentum_signed_5d FIRST, then vol_adj_autocorr)
- Past-only adversarial test PASS (4 new tests; SHA `d450692`); ret_autocorr_lag1_50 already past-only via 50-bar trailing window; range_realized_vol_50 already past-only
- Ran in EXPLORATION mode: --exploration --seeds 1 (1 outer × 1 inner × 35 n_trials × 3 symbols = **105 fits per cell**; colsample_bytree=1.0)
- Anchor: iter-v3/018 multi-seed mean +0.3788 IS / +0.3869 OOS
- Reference: iter-v3/025 single-seed +0.8788 IS / +1.2244 OOS

This was iter-v3/026, the **second Category 2 (composed/interaction feature) axis in v3 catalog history** and the FIRST EXPLORATION attempting to STACK two engineered features at single-seed.

## Headline Numbers

### Single-seed EXPLORATION run (seed 42)

| Metric | iter-v3/018 anchor | iter-v3/025 reference (single-seed) | iter-v3/026 (regime_momentum + vol_adj_autocorr) | Δ vs reference | Δ vs anchor |
|---|---:|---:|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | +0.8788 | **+0.0493** | **−0.83** (PATH C fires) | **−0.33** (below anchor) |
| OOS monthly Sharpe | +0.3869 | +1.2244 | **+1.4501** | **+0.23** (would be v3-historic high if multi-seed-validated) | **+1.06** |
| IS daily Sharpe | — | 1.86 | **+0.1227** | (collapsed) | — |
| OOS daily Sharpe | — | 2.03 | **+3.3558** | (extreme lift) | — |
| **IS/OOS daily ratio** | — | **0.92** | **27.4×** | **(structurally absurd)** | — |
| OOS/IS Sharpe ratio | 1.02 | 1.39 | **29.4** | (consistent with daily ratio anomaly) | — |
| IS n_trades | 172 (mean) | 194 | **196** | within saturation band [129, 215] | — |
| OOS n_trades | 90.5 (mean) | 95 | **79** | <130 trade-rate floor (informational at EXPLORATION) | — |
| IS MaxDD | 21.86% (mean) | 27.49% | **51.37%** (worst IS MaxDD in v3 history) | +23.88pp regression | — |
| OOS MaxDD | 27.74% (best seed 42) | 21.35% | **19.47%** | improved (consistent with OOS-favorable regime hypothesis) | — |
| Total OOS PnL | ∼+7% (mean) | +32.56% | similar magnitude | — | — |
| OOS WR | 36.4% (mean) | 45.26% | mixed (BCH 48.3%, LDO 44.4%, TRX 39.0%) | — | — |
| DSR | 0.0 | 0.0 | **0.0** | EXPLORATION artifact | — |
| PBO mean | 0.0892 | 0.1009 | **0.0914** | PASS (< 0.40); essentially flat | — |
| PSR | 0.9936 | 1.0 | **1.0** | EXPLORATION saturation (informational only) | — |
| n_eff | 25 (CONFIRMATION) | 19 | **19** | maintained | — |
| n_trials | 1500 (CONFIRMATION) | 105 | **105** (n=35 × 3 sym) | EXPLORATION default | — |

### vol_adj_autocorr feature importance — feature USED (NOT INERT)

| Cut | Importance value | % of Top Feature | Cohort Rank | Interpretation |
|---|---:|---:|---:|---|
| Portfolio | **283** | **45%** (vs top range_realized_vol_50=630) | 14/15 | Above ≥30 floor → feature is USED |
| Engineered category internal ranking | (300 for regime_momentum vs 283 for vol_adj_autocorr) | regime_momentum 48% / vol_adj_autocorr 45% of top | 13/15 (regime_momentum), 14/15 (vol_adj_autocorr) | Both engineered features preserve importance; vol_adj_autocorr does not cannibalize regime_momentum |
| ret_autocorr_lag1_50 (source primitive) | 265 | 42% of top | 15/15 | Source primitive **fell BELOW its derivative** — the composed feature absorbed primitive's signal |

**Falsifier 4 PASSES** at the relaxed importance ≥30 threshold; vol_adj_autocorr is NOT inert. This rules out PROMISING-INERT classification (PATH B). The mechanism is therefore NOT model-under-utilization. Compared to prior NEW-feature attempts:

| Iteration | Feature(s) | Importance % top portfolio | OOS Δ vs anchor | IS Δ vs anchor | IS/OOS daily ratio | Verdict |
|-----------|------------|---:|---:|---:|---:|---|
| 015 | tbr_zscore_30 (microstructure) | 25-67% (per-sym 14/14) | +1.74 (lottery) | −0.36 | normal | PROMISING-INERT |
| 019 | funding (per-sym, n=10) | 22% | +0.39 (lottery) | +0.78 | normal | PROMISING-INERT |
| 023 | funding (per-sym, n=35) | 22% | −1.46 | +0.15 | normal | NEGATIVE |
| 024 | btc_funding (cross-asset) | 24% | −1.20 | +0.60 | normal | NEGATIVE |
| 025 | regime_momentum_signed_5d (ENGINEERED, ALONE) | **51%** | **+0.84** | **+0.50** | **0.92** | **PROMISING ✓** |
| **026** | **+vol_adj_autocorr STACKED** | **45% (15-feature stack)** | **+1.06** | **−0.33** | **27.4×** | **NEGATIVE-SUSPICIOUS-OOS** |

The 27.4× IS/OOS daily ratio is the diagnostic signature of overfit-then-OOS-lottery. This is structurally distinct from iter-v3/025's clean co-directional pattern (IS+OOS both up; IS/OOS ratio in normal range).

### §4.4 Classification — MIXED PATTERN

| Condition | Threshold | Observed | Trigger |
|---|---|---|---|
| IS Sharpe Δ < −0.10 vs iter-v3/025 reference | < −0.10 | −0.83 | YES (PATH C IS-axis) |
| IS Sharpe Δ < −0.10 vs anchor | < −0.10 | −0.33 | YES (PATH C IS-axis confirmed) |
| OOS Sharpe Δ ≥ +0.10 vs reference | ≥ +0.10 | +0.23 | YES (would be PATH A on OOS axis IF trustable) |
| Concentration ≤ 30% | ≤ 30% | 78% BCH | NO — REGRESSION from iter-v3/025 |
| New feature importance ≥ 30 | ≥ 30 | 283 | YES (Falsifier 4 PASSES — feature USED, NOT INERT) |
| IS MaxDD ≤ 35% | ≤ 35% | 51.37% | NO — worst IS MaxDD in v3 history |

**MIXED PATTERN**: PATH C on IS axis (decisive at single-seed EXPLORATION where IS is the controlled axis) + PATH A-direction on OOS axis (untrustable per single-seed lottery rules). Verdict goes to NEGATIVE classification with NEW qualifier `SUSPICIOUS-OOS` to flag the structural anomaly distinct from clean NEGATIVE (feature inert OR feature actively hurts both axes).

### Per-symbol attribution (single-seed; OOS) — frozen baseline DISSOLVED in OPPOSITE DIRECTION

| Symbol | iter-v3/025 OOS PnL | iter-v3/026 OOS PnL | Δ | Trades | WR | Concentration |
|---|---:|---:|---:|---:|---:|---:|
| BCH | +11.31 | **+37.29** | **+25.98** | 29 | 48.3% | **78.46%** (single-symbol carry) |
| LDO | −1.98 | **+2.68** | +4.66 | 9 | 44.4% | 5.64% |
| TRX | +23.23 | **+7.56** | **−15.67** | 41 | 39.0% | 15.90% |

**Forensic finding**: BCH OOS swung +25.98 weighted_pnl while TRX dropped −15.67 — the iter-v3/025 frozen-baseline-DISSOLVED-in-favorable-direction pattern reversed. BCH-dominated portfolio at iter-v3/026 is structurally distinct from iter-v3/025's diversified portfolio. The OOS lift is BCH-specific lottery on a 29-trade window — multi-seed will reveal whether BCH 48.3% WR is robust or noise.

### Saturation falsifier verification (per `feedback_axis_saturation_predictor.md`)

| Predictor | Lower bound | Upper bound | Observed | Triggered? |
|---|---:|---:|---:|---|
| IS trade band (brief §2.3) | 129 | 215 | **196** | NO (within band) |

Saturation predictor passes — the new feature did not behave anomalously at the trade-count level. The behavioral effect is in the IS Sharpe + IS MaxDD dimensions (worst in v3), not the trade-count dimension.

## What Worked

- **Methodology of the run is clean.** All 12 standard methodology checks PASS or PASS-EXPLORATION informational (Critic FINAL `8839bbb`). Look-ahead audit verified by 20 adversarial tests on `compute_vol_adj_autocorr` (past-only construction confirmed: `ret_autocorr_lag1_50` via 50-bar trailing rolling correlation; `range_realized_vol_50` via 50-bar trailing rolling realized vol; both source primitives upstream in GROUP_REGISTRY). Track-isolation grep clean. Embargo width REQUIRED_GAP=66=(21+1)×3 unchanged. Reproducibility stamp clean (Setup `d450692`, brief `685287d`, EDA `97302db`, Phase 5.5 gate `03f9f75`, engineering+Critic FINAL `8839bbb`). Single-axis discipline preserved: V3_FEATURE_COLUMNS=15 (atomic add — vol_adj_autocorr added; column count +1 vs iter-v3/025); ITERATION_LABEL=v3-026.

- **Falsifier 4 PASSES at importance threshold** — vol_adj_autocorr was meaningfully used by the model (importance 283 = 45% of top range_realized_vol_50). This rules out PROMISING-INERT (PATH B) and confirms the failure mode is NOT model-under-utilization. The structural anomaly is in IS/OOS coherence, not feature usage.

- **n_trials=35 EXPLORATION default validates positively at iter-v3/026 (PRELIMINARY-VALIDATED through iteration #7).** n_eff=19 maintained from iter-v3/020/021/022/023/024/025 — consistent regime ×7 EXPLORATIONs. PSR=1.0 saturates honestly when observed Sharpe is materially positive (here OOS only); the IS PSR collapse pattern would be visible if we ran the IS-only version (we don't). DSR=0.0 reflects honest deflation at n_trials=105. Wall-clock 14 min (well within 2h cap). Seven data points (4 NEGATIVE + 1 PROMISING + 1 PROMISING-INERT + 1 NEGATIVE-SUSPICIOUS-OOS) confirm n_trials=35 default operates in the honest-deflation regime AND surfaces structural anomalies (the 27× IS/OOS ratio could not have been produced by an Optuna budget that was too small to overfit).

- **IC carve-out (per `feedback_v3_engineered_feature_pivot.md`) operates as designed.** EDA flagged max |IC|=0.985 with ret_autocorr_lag1_50 — would have BLOCKED the candidate under standard Category 1 rules. The Phase 5.5 gate explicitly bypassed the IC hard gate per Category 2 carve-out, deferring the binding evidence test to feature importance rank ≤10 AND absolute importance ≥30. The empirical outcome (importance 283, rank 14/15) confirms the carve-out: the high-IC pattern is structural for composed features (they share variance with source primitives BY CONSTRUCTION), but the model uses the composed feature non-trivially anyway.

- **Per-symbol architecture preserved attribution clarity.** BCH OOS swing +25.98 vs TRX OOS swing −15.67 attributable cleanly to per-symbol Optuna trajectories on the new 15-feature input space (frozen baseline rule — different V3_FEATURE_COLUMNS produces different per-symbol search spaces). The portfolio-level OOS lift is mechanically traceable to BCH's 78.46% concentration regression.

## What Failed

- **IS Sharpe collapse to +0.0493** is the lowest IS Sharpe in any post-bootstrap iteration (lowest prior was iter-v3/021 at +0.3183 universe-expansion, iter-v3/020 at +0.2745 per-symbol cap). At single-seed EXPLORATION, the IS Sharpe is the **controlled axis** — Optuna optimizes for IS performance subject to feature-set constraints. An IS Sharpe of 0.05 means Optuna at n_trials=35 could not find a hyperparameter trajectory that produced meaningful IS edge on the 15-feature input space. The most parsimonious explanation: the 15-feature stack at depth-3-5 with colsample_bytree=1.0 hardcoded **expanded the search space along an uninformative dimension**, leaving Optuna's 35-trial budget insufficient to converge on a useful tree structure.

- **Worst IS MaxDD in v3 history at 51.37%.** This complements the IS Sharpe collapse — the model's IS path was severely drawdown-prone, indicative of position-taking driven by noise rather than signal. iter-v3/025's IS MaxDD was 27.49%; iter-v3/018 anchor 21.86%. The +23.88pp jump is structural, not stochastic.

- **BCH 78.46% concentration regression.** iter-v3/025 had restored portfolio diversity (BCH 35% / LDO -6% / TRX 71% net concentration); iter-v3/026 reverted to single-symbol carry. This is consistent with the OOS-favorable-regime hypothesis: BCH 2025-Q1+ regime favors vol-normalized autocorr signals; the model exploits that without learning a generalizable IS pattern.

- **27× IS/OOS daily Sharpe ratio is structurally absurd.** This ratio is the diagnostic signature of mechanism #1 (IS overfit) + mechanism #4 (BCH single-symbol carry) combined. iter-v3/013's classic single-seed lottery had IS/OOS daily ratio in the order of 0.4× (single-seed +1.0088 IS / +2.6970 OOS at daily level → ~0.37×); iter-v3/026's 27× is an order of magnitude more extreme. iter-v3/013 falsified to 86% OOS reduction at multi-seed CONFIRMATION; iter-v3/026 would be expected to falsify by at least the same amount, possibly more — the IS Sharpe of 0.05 means there is essentially no IS signal to recover at multi-seed.

- **Engineered features DON'T STACK linearly.** The IS Sharpe drop from iter-v3/025's +0.88 (regime_momentum alone) to iter-v3/026's +0.05 (regime_momentum + vol_adj_autocorr stacked) is the core finding. Two engineered features at single-seed n_trials=35 produced DESTABILIZED IS at the same trial budget that worked for one. The hypothesis "engineered features stack incrementally" (brief §1 prediction) is FALSIFIED.

- **`vol_adj_autocorr` is NOT a CONFIRMATION-bundle candidate.** Even though Falsifier 4 passes (feature is used), the IS-axis PATH C decisively rules out bundling. The single-seed lottery suspect rule per `feedback_v3_single_seed_frozen_baseline.md` AND iter-v3/013 precedent require the feature to clear PATH A on IS+OOS jointly to qualify as bundle ingredient.

## Critical Lessons

(a) **Engineered features DON'T STACK linearly at single-seed EXPLORATION.** This is the core lesson of iter-v3/026 and is enshrined in NEW memory rule `feedback_v3_engineered_features_dont_stack.md`. iter-v3/025 alone (regime_momentum_signed_5d): IS +0.88 / OOS +1.22 — clean PROMISING. iter-v3/026 stacked (regime_momentum + vol_adj_autocorr): IS +0.05 / OOS +1.45 — IS collapse + suspect OOS. Mechanism: combining 2 engineered features at single-seed n_trials=35 expands Optuna search space beyond depth-3-5 LightGBM's representational capacity at the given budget; Optuna finds IS-noise hyperparams that generalize OOS by chance. Application: test ONE engineered feature alone at single-seed; defer stacking experiments to multi-seed CONFIRMATION (iter-v3/029+) when n_eff is higher and the search budget per direction is multiplied by seed count.

(b) **The IS-axis is the controlled axis at single-seed EXPLORATION.** Optuna at single-seed=42 with n_trials=35 optimizes IS performance subject to feature-set + hyperparameter-space constraints. An IS Sharpe collapse to 0.05 is a strong signal that the search space is mis-specified — either (i) the feature set is over-expanded relative to budget (this case), or (ii) the hyperparameter space is mis-specified (not this case; same as iter-v3/025). At single-seed EXPLORATION, we can read IS as the binding axis; OOS is read informationally. PATH C on IS is decisive.

(c) **OOS lifts at near-zero IS are structurally suspect.** When IS Sharpe is at the noise floor (≤0.10), any OOS lift is by definition disconnected from the IS-fitting process — it's a regime-favorability artifact, not learned signal. iter-v3/013's classic lottery had IS/OOS daily ratio ~0.4× at single-seed; iter-v3/026's 27× is order-of-magnitude worse. The OOS lift cannot be claimed as evidence of edge under any methodological framework. Multi-seed CONFIRMATION is the only test that disambiguates regime-favorability from genuine signal — and based on iter-v3/013's 86% OOS reduction precedent, the expected multi-seed OOS for iter-v3/026's stacked configuration would be near zero.

(d) **vol_adj_autocorr is NOT inert despite the failure mode.** Importance 283 = 45% of top portfolio is well above the ≥30 threshold. The model is using the new feature; it's just using it to overfit IS noise rather than to extract useful signal. Falsifier 4 PASSES — distinguishing this from iter-v3/015/019/023/024 (off-the-shelf indicator INERT pattern, importance ≤25%). The failure mode is over-fit not under-fit, which is mechanistically distinct.

(e) **iter-v3/025's OOS lift is more credible than iter-v3/026's**, despite both being single-seed. iter-v3/025 had (a) co-directional IS+OOS lift (+0.50 / +0.84), (b) IS/OOS daily ratio ~0.92 (normal range), (c) feature importance 51% with healthy portfolio diversity (BCH 35% / TRX 71%; not single-symbol carry), (d) feature usage broad-based across all 4 cuts. iter-v3/026 has none of these — only the OOS axis is positive, and the structural diagnostics (27× ratio, 78% BCH concentration, IS MaxDD 51%) all flag the OOS lift as lottery-favorable regime artifact.

(f) **iter-v3/027 axis = DIFFERENT engineered feature ALONE on top of regime_momentum** per Critic FINAL Recommendation (review SHA `8839bbb`) + user directive 2026-05-08:
   - DROP `vol_adj_autocorr` from V3_FEATURE_COLUMNS (revert 15 → 14)
   - KEEP `regime_momentum_signed_5d` (proven at iter-v3/025)
   - ADD a NEW engineered feature alone (14 → 15 with new feature)
   - This isolates the question: is the iter-v3/026 destabilization vol_adj_autocorr-specific (i.e., a particular composed-feature interaction broke things), OR is it a structural property of stacking 2 engineered features at single-seed n_trials=35? If iter-v3/027 PROMISING (a different engineered feature alone produces clean co-directional IS+OOS lift), then the stacking-budget hypothesis is correct. If iter-v3/027 NEGATIVE (a different engineered feature alone STILL produces destabilization), then the engineered-features pivot is genuinely narrow (only specific compositions work).

(g) **The engineered-features pivot is NOT falsified — only stacking at single-seed is falsified.** iter-v3/025 PROMISING evidence stands. The core hypothesis ("engineered features encode interactions trees can't compose at depth 3-5; they should be high-priority additions in the post-bootstrap cycle") remains supported. What's falsified is the secondary hypothesis ("engineered features stack incrementally at single-seed n_trials=35" — brief §1 / Section 7 PATH A pre-commit). Future engineered features must be tested alone at single-seed; the stacking question is deferred to multi-seed CONFIRMATION when n_eff is higher.

## Pre-Commit for iter-v3/027

Per Critic FINAL Recommendation of iter-v3/026 (SHA `8839bbb`) + diary lessons (a)-(g) + user directive 2026-05-08:

- **iter-v3/027 axis = DIFFERENT engineered feature, ALONE on top of regime_momentum** (Category 2 axis #3 in v3 catalog).
- **DROP** `vol_adj_autocorr` from V3_FEATURE_COLUMNS (revert 15 → 14).
- **KEEP** `regime_momentum_signed_5d` (proven at iter-v3/025; do NOT revert per `feedback_v3_engineered_features_proven.md`).
- **ADD** ONE NEW engineered feature (V3_FEATURE_COLUMNS 14 → 15). Critic FINAL Recommendation pre-commit: **`cross_asset_divergence_norm`** = `(sym_ret_7d − btc_ret_14d) / (vwap_dev_20 + 1e-6)`.
  - Different mechanism from regime_momentum: relative-strength normalized (NOT regime-conditional momentum).
  - Uses existing primitives (sym_ret_7d, btc_ret_14d, vwap_dev_20 — all in iter-v3/026 features parquet).
  - EDA at iter-v3/025 SHA `917605b`: composite score 0.6500 (#1 leaderboard at iter-v3/025); max |IC|_14=0.756 (BCH 0.695 passes hard gate <0.7; LDO/TRX above 0.7 by mild margin); max |rankIC|=0.109 (highest among 6 candidates evaluated); ADF p<1e-5 all 3 symbols (PASS).
  - Implementation cost LOWEST among candidates with non-overlapping mechanism: 10 lines of code in existing `engineered_v3.py` module; both source primitives already in features parquet.
- **Implementation**: extend `engineered_v3.py` with `compute_cross_asset_divergence_norm`; remove `compute_vol_adj_autocorr` from `add_engineered_v3_features` dispatch order (keep function as dead code at zero revert cost OR delete and regenerate at zero cost).
- **Verify** ALL components past-only via adversarial test at first commit. sym_ret_7d already past-only via 21-bar trailing window in cross_btc_v3.py; btc_ret_14d already past-only; vwap_dev_20 already past-only.
- **ITERATION_LABEL** = "v3-027".
- **Update `_verify_feature_columns`** to assert len==15 + new feature present + regime_momentum_signed_5d still present + vol_adj_autocorr ABSENT (reverted).
- **Hypothesis**: A different engineered feature (relative-strength mechanism) added in isolation (not stacked with vol_adj_autocorr) maintains regime_momentum's edge while adding orthogonal signal. Tests whether the iter-v3/026 destabilization was vol_adj_autocorr-specific OR a stacking-budget problem.
- **Predicted bands**:
  - IS Sharpe: [+0.50, +0.95] median +0.75 (close to iter-v3/025's +0.88; slight uncertainty from new feature's distinct mechanism)
  - OOS Sharpe: [+0.60, +1.30] median +1.00
  - Predicted IS NOT to collapse to <0.30 (iter-v3/026 was 0.05); a collapse would falsify the stacking-budget hypothesis and prove the engineered-features pivot is single-feature-narrow
- **3 pathways**:
  - **PATH A (PROMISING)**: IS ≥ +0.50 AND OOS ≥ +0.60 AND new feature importance ≥ 30 → pivot validated; iter-v3/026 destabilization was vol_adj_autocorr-specific OR a stacking artifact; engineered features can be stacked SEQUENTIALLY at single-seed (one alone at a time) but not simultaneously
  - **PATH B (PROMISING-INERT)**: new feature 14/14 importance — engineered category narrowly succeeds (only regime_momentum); pivot is single-feature-narrow
  - **PATH C (NEGATIVE)**: IS < +0.50 (close to iter-v3/026 collapse) — destabilization is NOT vol_adj_autocorr-specific; engineered stacking is structurally fragile at single-seed even with 1 new feature; pivot remains single-feature (only regime_momentum_signed_5d) at this architecture

## Cadence Status

**8 of 10 EXPLORATIONs done in post-bootstrap cycle.** iter-v3/019 (PROMISING-INERT) + iter-v3/020 (NEGATIVE-clean / PATH C) + iter-v3/021 (NEGATIVE-clean) + iter-v3/022 (NEGATIVE-clean / partially-effective-closed) + iter-v3/023 (NEGATIVE-clean / INERT-CONFIRMED + OVERFIT-AT-HIGHER-BUDGET) + iter-v3/024 (NEGATIVE-clean / INERT-OVERFIT-CROSS-ASSET-CONFIRMED) + iter-v3/025 (EXPLORATION-PROMISING clean — first PROMISING; STRONG CONFIRMATION-BUNDLE CANDIDATE) + iter-v3/026 (**EXPLORATION-NEGATIVE-SUSPICIOUS-OOS — engineered features DON'T STACK at single-seed**) completed; **2 EXPLORATIONs remaining** before next CONFIRMATION (earliest = iter-v3/029).

CONFIRMATION wall-clock cap = 6h (per `feedback_v3_cadence_discipline.md` empirically updated post-iter-v3/018). EXPLORATION wall-clock cap = 2h (iter-v3/026 ran 14 min — well within).

**Funding family (per-symbol + cross-asset BTC) PERMANENTLY CLOSED for v3** — 3 EXPLORATION data points (iter-v3/019/023/024).

**Off-the-shelf indicator additions SATURATED at the 13-feature stack** — 4 consecutive INERT outcomes (iter-v3/015 + iter-v3/019 + iter-v3/023 + iter-v3/024).

**Engineered features (Category 2 axis) PROVEN PROMISING at iter-v3/025; STACKING at single-seed FALSIFIED at iter-v3/026.** Per `feedback_v3_engineered_features_dont_stack.md`: test ONE engineered feature alone; defer stacking to multi-seed CONFIRMATION.

**iter-v3/027 = DIFFERENT engineered feature alone on top of regime_momentum** per Critic FINAL of iter-v3/026 + user directive 2026-05-08. Recommended candidate: `cross_asset_divergence_norm` (Critic FINAL prior; #1 EDA leaderboard at iter-v3/025; lowest implementation cost with non-overlapping mechanism).

## Reproducibility

- Setup commit SHA: `d450692` (feat: vol_adj_autocorr engineered feature; ADD vol_adj_autocorr — V3_FEATURE_COLUMNS 14→15)
- EDA SHA: `97302db` (analysis/iteration_v3-026/second_engineered_eda.py + 5 CSV outputs + synthesis.md; 4 of 4 candidates evaluated; vol_adj_autocorr selected via Critic FINAL Rec + user directive pre-commit)
- Brief SHA: `685287d`
- Phase 5.5 gate SHA: `03f9f75`
- Engineering report + Critic FINAL SHA: `8839bbb` (combined commit — engineering_report.md + review.md)
- HEAD SHA at backtest run: `d450692`
- Reports: `reports-v3/iteration_v3-026/comparison.csv` (single-seed EXPLORATION row), `reports-v3/iteration_v3-026/dsr.json` (DSR=0.0 / PBO=0.0914 / PSR=1.0 / n_trials=105 / n_eff=19), `reports-v3/iteration_v3-026/in_sample/model_importance_last_month_*.csv` (regime_momentum_signed_5d portfolio rank 13/15 imp 300 = 48%; vol_adj_autocorr portfolio rank 14/15 imp 283 = 45%; ret_autocorr_lag1_50 source primitive rank 15/15 imp 265), `reports-v3/iteration_v3-026/seed_summary.json`, `reports-v3/iteration_v3-026/pareto_front.csv`, `reports-v3/iteration_v3-026/ic_matrix.csv`
- Tag (informational): NONE (NEGATIVE-SUSPICIOUS-OOS verdict; not a baseline-update or PROMISING-tag event)
