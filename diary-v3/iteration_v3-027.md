# Iteration iter-v3/027 — Diary

## Decision: EXPLORATION-NEGATIVE-SUSPICIOUS-OOS — third engineered feature stacking REPRODUCES + AMPLIFIES iter-v3/026 anomaly

The third engineered feature `cross_asset_divergence_norm = (sym_ret_7d − btc_ret_14d) / (|vwap_dev_20| + 1e-6)` (atomic swap from iter-v3/026's vol_adj_autocorr; KEEP iter-v3/025's regime_momentum_signed_5d; V3_FEATURE_COLUMNS net unchanged at 15) at single-seed EXPLORATION at n_trials=35 produced a **STRUCTURALLY SUSPICIOUS-OOS RESULT MORE EXTREME THAN iter-v3/026**: IS monthly Sharpe collapsed to **−0.2817** (Δ −1.16 vs iter-v3/025 reference +0.8788; Δ −0.66 vs iter-v3/018 anchor +0.3788 — **FIRST IS-NEGATIVE in any post-bootstrap iteration**) while OOS monthly Sharpe spiked to **+1.6786** (Δ +0.45 vs reference; Δ +1.29 vs anchor — would be v3-historic high if multi-seed-validated). The 3-iter monotonic IS degradation pattern (regime_momentum alone +0.88 → stack vol_adj_autocorr +0.05 → swap to cross_asset_divergence −0.28) accompanied by monotonic OOS lift (+1.22 → +1.45 → +1.68) and worsening IS MaxDD trajectory (27.5% → 51.4% → **62.9%, worst ever in v3**) is the structural diagnostic for **single-seed lottery on overcomplicated loss surface** — NOT a true signal-add pattern.

§4.4 PATH C fires unambiguously on the IS axis (the controlled axis at single-seed EXPLORATION): IS Sharpe Δ −1.16 vs iter-v3/025 reference exceeds the −0.10 threshold by an order of magnitude AND is the first IS-negative in post-bootstrap. The OOS lift +1.6786 is single-seed-untrustable on three independent grounds, identical to iter-v3/026 reasoning + amplified:

1. **iter-v3/013 precedent**: single-seed +2.70 OOS at iter-v3/013 was falsified to +0.39 multi-seed (86% reduction). iter-v3/027's +1.68 OOS is structurally weaker than iter-v3/013's because IS is FRANKLY NEGATIVE (no co-directional support whatsoever).
2. **Worst IS MaxDD in v3 history at 62.90%** (iter-v3/025 27.49%; iter-v3/026 51.37%; anchor 21.86%). The IS Sharpe of −0.28 reflects a portfolio that LOSES money in-sample on a path that endured a 63% drawdown — a model that profits OOS at this IS quality is consistent with random walk + favorable OOS regime, NOT genuine signal.
3. **TRX OOS concentration 91.57% — extreme by any reasonable benchmark**. iter-v3/025 had 71% TRX, iter-v3/026 had 78% BCH; iter-v3/027 has 91.57% TRX — **the highest single-symbol concentration in any post-bootstrap iteration**. This fails Gate 7 of BASELINE_V3.md (top-symbol concentration ≤ 30% — accepted exception threshold) by an order of magnitude. The OOS lift is TRX-specific lottery on a 48-trade window.

cross_asset_divergence_norm IS USED meaningfully on LDO+TRX (LDO importance 360 = 65% of top, TRX 36 = 35% of top, Portfolio 406 = 64% of top) AND ESSENTIALLY IGNORED on BCH (importance 10 — both new features). regime_momentum_signed_5d's importance has degraded relative to iter-v3/025: BCH 0 (was 43), LDO 309 (was 232), TRX 38 (was 123), Portfolio 347 (was 398). The composed-feature stack is now using cross_asset_divergence_norm to reach for OOS regime favorability rather than encoding a generalizable interaction. Falsifier 4 PASSES at the importance threshold (cross_asset_divergence_norm imp 406 > 30) — vol_adj_autocorr-style INERT verdict is ruled out. The mechanism is therefore NOT under-utilization but the **same OVER-EXPANSION of the search space** documented at iter-v3/026, just amplified: combining 2 engineered features (regime_momentum + cross_asset_divergence) overwhelmed depth-3-5 LightGBM's representational capacity at the n_trials=35 single-seed budget; Optuna found IS-overfit hyperparams that fail to generalize on IS but happen to land on TRX-specific OOS regime favorability.

This is a **PIVOT-CONFIRMATION-CONSTRAINING signal**: iter-v3/026 + iter-v3/027 = 2 of 2 engineered-feature stacking attempts producing the IDENTICAL structural anomaly pattern (IS monotonic decline + OOS monotonic lift + worsening IS MaxDD). The engineered-features pivot remains valid for SINGLE-feature additions (iter-v3/025 PROMISING stands as the only genuinely PROMISING result in post-bootstrap), but stacking is structurally falsified. **Only iter-v3/025 (regime_momentum_signed_5d ALONE) survives as the validated PROMISING result for the iter-v3/029 CONFIRMATION bundle.** Cadence #9 of 10 in post-bootstrap cycle.

## What Was Tested

**Hypothesis (locked in brief Section 1):** "Adding `cross_asset_divergence_norm` (= `(sym_ret_7d − btc_ret_14d) / (|vwap_dev_20| + 1e-6)`) — relative-strength normalized — as the 15th feature in atomic swap with iter-v3/026's vol_adj_autocorr (DROP vol_adj_autocorr; KEEP regime_momentum_signed_5d; ADD cross_asset_divergence_norm) — at the EXPLORATION default n_trials=35 — will isolate whether the iter-v3/026 destabilization was (a) vol_adj_autocorr-specific (a particular composed-feature interaction broke things) OR (b) a structural property of stacking 2 engineered features at single-seed n_trials=35. If iter-v3/027 PROMISING (a different engineered feature alone produces clean co-directional IS+OOS lift), then the stacking-budget hypothesis is correct. If iter-v3/027 NEGATIVE (a different engineered feature alone STILL produces destabilization), then the engineered-features pivot is genuinely narrow (only specific compositions work)."

**Spec (locked, single-axis variation — atomic swap; third Category 2 axis):**
- V3_FEATURE_COLUMNS_TOP_N: DROP `vol_adj_autocorr` (revert iter-v3/026 stacking falsified result)
- V3_FEATURE_COLUMNS_TOP_N: ADD `cross_asset_divergence_norm` (atomic swap; net column count unchanged at 15)
- KEEP `regime_momentum_signed_5d` (do NOT revert; iter-v3/025 PROMISING per `feedback_v3_engineered_features_proven.md` mandate)
- ITERATION_LABEL = "v3-027"
- 3-symbol BCH+LDO+TRX universe UNCHANGED
- Other gates BYTE-IDENTICAL to iter-v3/018 anchor (z=2.0, ATR 2.0/1.0, BTC ±15%, ADX=20, Hurst gate, low-vol filter, hit-rate disabled, regime gate disabled, per-symbol cap disabled)
- Implemented `compute_cross_asset_divergence_norm` in existing module `src/crypto_trade/features_v3/engineered_v3.py` (extends iter-v3/025/026 module; output clipped to [−100, +100] to prevent infinity from near-zero |vwap_dev_20|)
- `add_engineered_v3_features` updated to call regime_momentum_signed_5d FIRST (kept), then cross_asset_divergence_norm (replaced vol_adj_autocorr)
- Past-only adversarial test PASS (4 new tests; SHA `b9b6f8d`); sym_ret_7d already past-only via 21-bar trailing window in cross_btc_v3.py; btc_ret_14d already past-only; vwap_dev_20 already past-only
- Ran in EXPLORATION mode: --exploration --seeds 1 (1 outer × 1 inner × 35 n_trials × 3 symbols = **105 fits per cell**; colsample_bytree=1.0)
- Anchor: iter-v3/018 multi-seed mean +0.3788 IS / +0.3869 OOS
- Reference: iter-v3/025 single-seed +0.8788 IS / +1.2244 OOS

This was iter-v3/027, the **third Category 2 (composed/interaction feature) axis in v3 catalog history** and the SECOND consecutive EXPLORATION attempting to STACK a second engineered feature on top of regime_momentum at single-seed.

## Headline Numbers

### Single-seed EXPLORATION run (seed 42)

| Metric | iter-v3/018 anchor | iter-v3/025 reference (single-seed) | iter-v3/026 (regime_momentum + vol_adj_autocorr) | **iter-v3/027 (regime_momentum + cross_asset_divergence_norm)** | Δ vs reference | Δ vs anchor |
|---|---:|---:|---:|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | +0.8788 | +0.0493 | **−0.2817** | **−1.16** (PATH C fires; FIRST IS-negative in post-bootstrap) | **−0.66** (well below anchor) |
| OOS monthly Sharpe | +0.3869 | +1.2244 | +1.4501 | **+1.6786** | **+0.45** (would be v3-historic high if multi-seed-validated) | **+1.29** |
| IS daily Sharpe | — | 1.86 | +0.1227 | **−0.8089** | (collapsed to negative) | — |
| OOS daily Sharpe | — | 2.03 | +3.3558 | **+1.8090** | (extreme lift) | — |
| OOS/IS Sharpe ratio | 1.02 | 1.39 | 29.4 | **−5.96** (sign flip) | (consistent with IS-negative anomaly) | — |
| IS n_trades | 172 (mean) | 194 | 196 | **205** | within saturation band [129, 215] | — |
| OOS n_trades | 90.5 (mean) | 95 | 79 | **105** | <130 trade-rate floor (informational at EXPLORATION) | — |
| IS MaxDD | 21.86% (mean) | 27.49% | 51.37% | **62.90%** (**worst IS MaxDD in v3 history**) | +35.41pp regression vs iter-v3/025 | — |
| OOS MaxDD | 27.74% (best seed 42) | 21.35% | 19.47% | **22.72%** | (broadly stable; OOS is favorable regime) | — |
| Total OOS PnL | ∼+7% (mean) | +32.56% | similar magnitude | **+33.46%** | similar magnitude | — |
| OOS WR | 36.4% (mean) | 45.26% | mixed | **40.0%** (BCH 28.6%, LDO 40.0%, TRX 50.0%) | broad weakening from iter-v3/025 | — |
| DSR | 0.0 | 0.0 | 0.0 | **0.0** | EXPLORATION artifact | — |
| PBO mean | 0.0892 | 0.1009 | 0.0914 | **0.1448** | PASS (< 0.40); minor uptick consistent with new feature dimension | — |
| PSR | 0.9936 | 1.0 | 1.0 | **1.0** | EXPLORATION saturation (informational only) | — |
| n_eff | 25 (CONFIRMATION) | 19 | 19 | **19** | maintained (consistent regime ×8) | — |
| n_trials | 1500 (CONFIRMATION) | 105 | 105 | **105** (n=35 × 3 sym) | EXPLORATION default | — |

### cross_asset_divergence_norm feature importance — feature USED (NOT INERT) but unevenly across symbols

| Cut | cross_asset_divergence_norm imp | regime_momentum_signed_5d imp | Top feature imp | Interpretation |
|---|---:|---:|---:|---|
| BCH | **10** | **0** | (top BCH feature) | **BOTH ENGINEERED FEATURES IGNORED** — BCH model doesn't use either; trades driven by 13 base features alone |
| LDO | **360** | **309** | (top LDO feature) | Both engineered features MEANINGFULLY USED on LDO; cross_asset_divergence dominant |
| TRX | **36** | **38** | (top TRX feature) | Both modest; TRX trades driven primarily by 13 base features but with engineered support |
| Portfolio | **406** | **347** | range_realized_vol_50=636 | cross_asset_divergence_norm 64% of top (Falsifier 4 PASSES) |

**Falsifier 4 PASSES** at importance threshold (cross_asset_divergence_norm imp 406 > 30) — feature is USED on aggregate. This rules out PROMISING-INERT classification (PATH B). The mechanism is therefore NOT model-under-utilization. Compared to iter-v3/025 baseline:

| Iteration | regime_momentum imp (Portfolio) | New feature imp (Portfolio) | OOS Sharpe Δ vs anchor | IS Sharpe Δ vs anchor | IS MaxDD | Verdict |
|-----------|---:|---:|---:|---:|---:|---|
| 025 | 398 (51% of top) | — (alone) | **+0.84** | **+0.50** | 27.5% | **PROMISING ✓** |
| 026 | 300 (48% of top) | vol_adj_autocorr 283 (45% of top) | +1.06 | −0.33 | 51.4% | NEGATIVE-SUSPICIOUS-OOS |
| **027** | **347 (55% of top)** | **cross_asset_divergence 406 (64% of top)** | **+1.29** | **−0.66** | **62.9%** | **NEGATIVE-SUSPICIOUS-OOS (more extreme)** |

The IS MaxDD trajectory (27% → 51% → 63%) and IS Sharpe trajectory (+0.88 → +0.05 → −0.28) are monotonic across the 3 iterations — diagnostic of structural single-seed lottery, not a feature-specific failure.

### §4.4 Classification — MIXED PATTERN AMPLIFIED FROM iter-v3/026

| Condition | Threshold | Observed | Trigger |
|---|---|---|---|
| IS Sharpe Δ < −0.10 vs iter-v3/025 reference | < −0.10 | −1.16 | YES (PATH C IS-axis decisive) |
| IS Sharpe Δ < −0.10 vs anchor | < −0.10 | −0.66 | YES (PATH C IS-axis confirmed; FIRST IS-NEGATIVE in post-bootstrap) |
| OOS Sharpe Δ ≥ +0.10 vs reference | ≥ +0.10 | +0.45 | YES (would be PATH A on OOS axis IF trustable; not trustable) |
| Concentration ≤ 30% | ≤ 30% | 91.6% TRX | NO — **HIGHEST TRX concentration in any post-bootstrap iteration** |
| New feature importance ≥ 30 | ≥ 30 | 406 | YES (Falsifier 4 PASSES — feature USED, NOT INERT) |
| IS MaxDD ≤ 35% | ≤ 35% | 62.90% | NO — worst IS MaxDD in v3 history |

**MIXED PATTERN AMPLIFIED**: PATH C on IS axis (decisive at single-seed EXPLORATION) + PATH A-direction on OOS axis (untrustable per single-seed lottery rules; TRX 91.6% concentration disqualifies). Verdict goes to NEGATIVE classification with the iter-v3/026 qualifier `SUSPICIOUS-OOS` to flag the structural anomaly distinct from clean NEGATIVE.

### Per-symbol attribution (single-seed; OOS) — TRX-dominated single-symbol carry

| Symbol | iter-v3/025 OOS PnL | iter-v3/026 OOS PnL | iter-v3/027 OOS PnL | Δ vs iter-v3/026 | Trades | WR | Concentration |
|---|---:|---:|---:|---:|---:|---:|---:|
| BCH | +11.31 | +37.29 | **−3.31** | −40.60 | 42 | 28.6% | −9.88% |
| LDO | −1.98 | +2.68 | **+6.13** | +3.45 | 15 | 40.0% | 18.31% |
| TRX | +23.23 | +7.56 | **+30.64** | +23.08 | 48 | 50.0% | **91.57%** |

**Forensic finding**: TRX OOS PnL roughly DOUBLED from iter-v3/025's +23.23 to iter-v3/027's +30.64, while BCH SWUNG NEGATIVE from +11.31 to −3.31 (a −14.62 weighted_pnl decline) and LDO improved from −1.98 to +6.13. The portfolio is now TRX-dominant at 91.57% — the iter-v3/025 portfolio diversity (BCH 35% / LDO -6% / TRX 71%) and even iter-v3/026 (BCH 78%) are GONE. The OOS lift is single-symbol TRX carry on a 48-trade window with 50% WR — multi-seed will reveal whether TRX 50% WR is robust or noise. If TRX falsifies at multi-seed (analogous to iter-v3/013's LDO 80% WR collapse), the entire OOS edge of iter-v3/027 evaporates.

### Saturation falsifier verification (per `feedback_axis_saturation_predictor.md`)

| Predictor | Lower bound | Upper bound | Observed | Triggered? |
|---|---:|---:|---:|---|
| IS trade band (brief §2.3) | 129 | 215 | **205** | NO (within band) |

Saturation predictor passes at the edge — IS trades 205 are at 95% of the upper bound 215. The new feature did not behave anomalously at the trade-count level. The behavioral effect is in the IS Sharpe + IS MaxDD dimensions (worst in v3 across both), not the trade-count dimension.

## What Worked

- **Methodology of the run is clean.** All 12 standard methodology checks PASS or PASS-EXPLORATION informational (Critic FINAL `966f4c1`). Look-ahead audit verified by 4 adversarial tests on `compute_cross_asset_divergence_norm` (past-only construction confirmed: sym_ret_7d via 21-bar trailing window in cross_btc_v3.py; btc_ret_14d via past-only log-return diff; vwap_dev_20 already past-only via 20-bar trailing rolling VWAP). Track-isolation grep clean. Embargo width REQUIRED_GAP=66=(21+1)×3 unchanged. Reproducibility stamp clean (Setup `b9b6f8d`, brief `4698b21`, EDA `254a5f2`, Phase 5.5 gate `c474cc9`, engineering+Critic FINAL `966f4c1`). Single-axis discipline preserved: V3_FEATURE_COLUMNS=15 (atomic swap — vol_adj_autocorr dropped, cross_asset_divergence_norm added; net count UNCHANGED); ITERATION_LABEL=v3-027.

- **Falsifier 4 PASSES at importance threshold** — cross_asset_divergence_norm was meaningfully used by the model on aggregate (importance 406 = 64% of top range_realized_vol_50). This rules out PROMISING-INERT (PATH B) and confirms the failure mode is NOT model-under-utilization. The structural anomaly is in IS/OOS coherence + TRX concentration, not feature usage.

- **Stacking-fragility hypothesis VALIDATED across 2 different feature compositions.** iter-v3/026 (vol_adj_autocorr stacked) and iter-v3/027 (cross_asset_divergence_norm stacked) produced the IDENTICAL structural anomaly pattern: IS Sharpe collapse, OOS Sharpe spike, IS MaxDD blow-out. The two features have NON-OVERLAPPING source primitives (ret_autocorr_lag1_50/range_realized_vol_50 vs sym_ret_7d/btc_ret_14d/vwap_dev_20) and DIFFERENT mechanisms (per-unit-vol return persistence vs cross-asset relative-strength normalized) — yet both fail in the same way when stacked on regime_momentum. This rules out feature-specific explanations and confirms the failure mode is **structural to engineered-feature stacking at single-seed n_trials=35**.

- **Engineered-features pivot single-feature validity preserved.** iter-v3/025 PROMISING evidence stands. The core hypothesis ("engineered features encode interactions trees can't compose at depth 3-5; they should be high-priority additions in the post-bootstrap cycle") remains supported for ONE engineered feature at a time. What's now decisively falsified is the secondary hypothesis ("engineered features stack incrementally at single-seed n_trials=35"). Future engineered features must be tested ALONE on top of iter-v3/013 baseline (not stacked on regime_momentum); the stacking question is deferred to multi-seed CONFIRMATION when n_eff is higher.

- **n_trials=35 EXPLORATION default validates positively at iter-v3/027 (PRELIMINARY-VALIDATED through iteration #8).** n_eff=19 maintained from iter-v3/020/021/022/023/024/025/026 — consistent regime ×8 EXPLORATIONs. PSR=1.0 saturates honestly when observed Sharpe is materially positive (here OOS only); DSR=0.0 reflects honest deflation at n_trials=105. PBO 0.1448 PASS. Wall-clock 14 min (well within 2h cap). Eight data points (5 NEGATIVE-clean + 1 PROMISING + 1 PROMISING-INERT + 2 NEGATIVE-SUSPICIOUS-OOS) confirm n_trials=35 default operates in the honest-deflation regime AND surfaces structural anomalies.

## What Failed

- **IS Sharpe collapse to −0.2817 — FIRST IS-negative in any post-bootstrap iteration.** The lowest IS Sharpe in v3 catalog history is now iter-v3/027 at −0.2817 (prior lowest was iter-v3/021 at +0.3183 universe-expansion; iter-v3/020 at +0.2745 per-symbol cap; iter-v3/026 at +0.0493 stacking). At single-seed EXPLORATION, the IS Sharpe is the **controlled axis** — Optuna optimizes for IS performance subject to feature-set constraints. An IS Sharpe of −0.28 means Optuna at n_trials=35 could not even find a hyperparameter trajectory that produced break-even IS performance on the 15-feature input space. The most parsimonious explanation: the 15-feature stack at depth-3-5 with colsample_bytree=1.0 hardcoded **expanded the search space along TWO uninformative dimensions** (vol_adj_autocorr at iter-v3/026; now cross_asset_divergence_norm at iter-v3/027), leaving Optuna's 35-trial budget insufficient to converge on a useful tree structure. The amplification from iter-v3/026's +0.05 to iter-v3/027's −0.28 is consistent with iter-v3/027's new feature being even MORE search-disruptive on this architecture.

- **Worst IS MaxDD in v3 history at 62.90%.** This complements the IS Sharpe collapse — the model's IS path had a 63% drawdown, indicative of position-taking driven entirely by noise rather than signal. iter-v3/025's IS MaxDD was 27.49%; iter-v3/026 51.37%; iter-v3/027 62.90%. The +35.41pp jump from iter-v3/025 is structural, not stochastic.

- **TRX 91.57% concentration regression — extreme by any reasonable benchmark.** iter-v3/025 had restored portfolio diversity (BCH 35% / LDO -6% / TRX 71%); iter-v3/026 reverted to BCH 78% single-symbol carry; iter-v3/027 reverts further to TRX 91.57% single-symbol carry. This is the highest single-symbol concentration in any post-bootstrap iteration and fails Gate 7 of BASELINE_V3.md (top-symbol concentration ≤ 30% — even with the 3-symbol structural exception, 91.6% is unprecedented). The OOS lift is single-symbol TRX carry on a 48-trade window — completely structurally distinct from iter-v3/025's diversified portfolio.

- **Engineered features DON'T STACK linearly — REPRODUCED + AMPLIFIED across 2 feature compositions.** The IS Sharpe trajectory from iter-v3/025's +0.88 (regime_momentum alone) → iter-v3/026's +0.05 (regime_momentum + vol_adj_autocorr) → iter-v3/027's −0.28 (regime_momentum + cross_asset_divergence) is monotonic and consistent across 3 iterations. Two engineered features at single-seed n_trials=35 produced DESTABILIZED IS at the same trial budget that worked for one. The 2-iteration replication (iter-v3/026 + iter-v3/027) confirms the stacking falsification is structural, not feature-specific.

- **`cross_asset_divergence_norm` is NOT a CONFIRMATION-bundle candidate.** Even though Falsifier 4 passes (feature is used), the IS-axis PATH C decisively rules out bundling. The single-seed lottery suspect rule per `feedback_v3_single_seed_frozen_baseline.md` AND iter-v3/013 precedent require the feature to clear PATH A on IS+OOS jointly to qualify as bundle ingredient.

- **OOS lift +1.6786 cannot be claimed as evidence of edge.** When IS Sharpe is FRANKLY NEGATIVE, any OOS lift is by definition disconnected from the IS-fitting process — it's a regime-favorability artifact (specifically TRX-favorable 2025+ regime), not learned signal. iter-v3/026's mechanism #1 (IS overfit) + mechanism #4 (single-symbol carry) is reproduced at iter-v3/027 with TRX as the carry target instead of BCH. iter-v3/013's classic lottery had IS/OOS daily ratio ~0.4× at single-seed; iter-v3/027's daily ratio is **−2.24** (sign flip — even worse than iter-v3/026's 27×). Multi-seed CONFIRMATION is the only test that disambiguates regime-favorability from genuine signal — and based on iter-v3/013's 86% OOS reduction precedent + iter-v3/027's IS-negative starting point, the expected multi-seed OOS would be at or below zero.

## Critical Lessons

(a) **Engineered features DON'T STACK at single-seed n_trials=35 — REPLICATED across 2 distinct feature compositions.** This is the cementing lesson of iter-v3/027 — iter-v3/026's `feedback_v3_engineered_features_dont_stack.md` rule is now empirically supported by 2 of 2 stacking attempts (vol_adj_autocorr + cross_asset_divergence_norm) producing the IDENTICAL structural anomaly. The IS Sharpe trajectory (+0.88 → +0.05 → −0.28) and IS MaxDD trajectory (27% → 51% → 63%) are monotonic across iterations. The replication rules out feature-specific explanations: the failure is **structural to stacking 2 engineered features at single-seed**. Mechanism: combining 2 engineered features at single-seed n_trials=35 expands Optuna search space beyond depth-3-5 LightGBM's representational capacity; Optuna finds IS-noise hyperparams that fail on IS but generalize OOS by chance via single-symbol regime-favorability carry.

(b) **The IS-axis is the controlled axis at single-seed EXPLORATION — confirmed across 8 EXPLORATIONs.** Optuna at single-seed=42 with n_trials=35 optimizes IS performance subject to feature-set + hyperparameter-space constraints. Through iter-v3/020-027, IS Sharpe values have correlated robustly with verdict classifications: PROMISING required IS Δ ≥ +0.30 (iter-v3/025 was +0.50); NEGATIVE-clean IS Δ near zero or moderately negative; NEGATIVE-SUSPICIOUS-OOS IS Δ severely negative (iter-v3/026 −0.33; iter-v3/027 −0.66). PATH C on IS is decisive at single-seed EXPLORATION. iter-v3/027 produced the FIRST IS-negative in post-bootstrap, signaling the most decisive PATH C trigger to date.

(c) **OOS lifts at IS-negative are even more structurally suspect than at near-zero IS.** When IS Sharpe is FRANKLY NEGATIVE (−0.28), any OOS lift is by definition disconnected from the IS-fitting process — it's a regime-favorability artifact, not learned signal. iter-v3/013's classic lottery had IS/OOS daily ratio ~0.4× at single-seed (both positive); iter-v3/026's 27× was order-of-magnitude worse (IS positive but tiny); iter-v3/027's **−2.24 sign flip** (IS negative, OOS positive) is the most extreme yet. The OOS lift cannot be claimed as evidence of edge under any methodological framework. Multi-seed CONFIRMATION is the only test that disambiguates regime-favorability from genuine signal — and based on iter-v3/013's 86% OOS reduction precedent + iter-v3/027's IS-negative starting point, the expected multi-seed OOS for iter-v3/027's stacked configuration would be near zero or below.

(d) **cross_asset_divergence_norm is NOT inert despite the failure mode.** Importance 406 = 64% of top portfolio is well above the ≥30 threshold. The model is using the new feature (especially on LDO at importance 360); it's just using it to overfit IS noise rather than to extract useful generalizable signal. Falsifier 4 PASSES — same diagnostic as iter-v3/026's vol_adj_autocorr (importance 283 = 45% of top). The failure mode is over-fit not under-fit, which is mechanistically distinct from iter-v3/015/019/023/024 (off-the-shelf indicator INERT pattern, importance ≤25%). Two consecutive iterations at this diagnostic confirm the over-fit-not-under-fit mechanism for engineered-feature stacking.

(e) **iter-v3/025's OOS lift remains MORE credible than either iter-v3/026's or iter-v3/027's**, despite all three being single-seed. iter-v3/025 had (a) co-directional IS+OOS lift (+0.50 / +0.84), (b) IS/OOS daily ratio ~0.92 (normal range), (c) feature importance 51% with healthy portfolio diversity (BCH 35% / TRX 71%; not single-symbol carry), (d) feature usage broad-based across all 4 cuts. iter-v3/026 had +0.05 IS / +1.45 OOS with 27× ratio + 78% BCH carry; iter-v3/027 has −0.28 IS / +1.68 OOS with −2.24× ratio + 91.6% TRX carry. Only iter-v3/025 satisfies the structural diagnostics for genuine signal. **Only iter-v3/025 (regime_momentum_signed_5d ALONE) is the validated PROMISING result for the iter-v3/029 CONFIRMATION bundle.**

(f) **The iter-v3/029 CONFIRMATION bundle is single-feature MINIMAL** per Critic FINAL Recommendation (review SHA `966f4c1`):
   - Base: iter-v3/013 baseline (BCH+LDO+TRX, 13 features, ATR labeling, 7 risk gates)
   - ADD: regime_momentum_signed_5d (V3_FEATURE_COLUMNS=14)
   - DROP: cross_asset_divergence_norm + vol_adj_autocorr (both stacking attempts FALSIFIED at single-seed)
   - Spec: --seeds 2 --n-trials=35, ENSEMBLE_SIZE=5, full DSR/PBO/PSR, 6h cap
   - This is a MINIMAL bundle — only 1 NEW edge ingredient validated across 9 EXPLORATIONs since iter-v3/018 BOOTSTRAP. The prior bootstrap baseline (iter-v3/018 multi-seed mean +0.38/+0.39) is what we're trying to lift via this single feature.

(g) **iter-v3/028 = MINI-VALIDATION of iter-v3/025 at --seeds 2 (NOT --exploration)** per Critic FINAL Recommendation (review SHA `966f4c1`) + user directive 2026-05-08:
   - REPLICATE iter-v3/025 (regime_momentum_signed_5d alone) at --seeds 2 default n_trials=35 + ENSEMBLE_SIZE=5
   - DROP cross_asset_divergence_norm from V3_FEATURE_COLUMNS (revert 15 → 14)
   - KEEP regime_momentum_signed_5d (proven at iter-v3/025; per `feedback_v3_engineered_features_proven.md` mandate)
   - Run command: `uv run python run_baseline_v3.py --seeds 2` (NO --exploration; default n_trials=35; ENSEMBLE_SIZE=5)
   - This is structurally a "mini-CONFIRMATION" — gives multi-seed Pareto + n_eff > 19 + DSR potentially non-zero
   - Wall-clock budget: ~30 min (--seeds 2 vs --seeds 1 + 5× ensemble vs 1× ensemble)
   - Why 10th of 10 EXPLORATIONs slot used for validation rather than another axis: iter-v3/025 is the ONLY validated PROMISING result in post-bootstrap; pre-validating at --seeds 2 (~30 min) gives early signal on whether iter-v3/029 CONFIRMATION at full --seeds 2 + n_trials=35 + ENSEMBLE_SIZE=5 (~3-4h compute) is worth the budget. If iter-v3/025 multi-seed falsifies → iter-v3/029 dead-on-arrival; we save CONFIRMATION budget. If iter-v3/025 multi-seed holds → iter-v3/029 launches with high confidence.

## Pre-Commit for iter-v3/028

Per Critic FINAL Recommendation of iter-v3/027 (SHA `966f4c1`) + diary lessons (a)-(g) + user directive 2026-05-08:

- **iter-v3/028 type = SPECIAL EXPLORATION (MINI-VALIDATION)**. This uses --seeds 2 instead of the typical --exploration --seeds 1. Per `feedback_v3_outer_seed_cap_2_v3.md`: "v3 CONFIRMATION runs use --seeds 2 max". This iter-v3/028 mini-validation uses --seeds 2 even though it's classified EXPLORATION — accepted exception per "validate before CONFIRMATION budget" justification. Document this in §0.5 of the iter-v3/028 brief explicitly.
- **iter-v3/028 axis = REPLICATE iter-v3/025 at --seeds 2** (NOT a new feature/methodology axis).
- **DROP** `cross_asset_divergence_norm` from V3_FEATURE_COLUMNS (revert 15 → 14).
- **KEEP** `regime_momentum_signed_5d` (proven at iter-v3/025; do NOT revert per `feedback_v3_engineered_features_proven.md`).
- **DO NOT add any new feature** (this is a mini-validation, not a feature/architecture axis).
- **Update `_verify_feature_columns`** to assert len==14 + regime_momentum_signed_5d present + cross_asset_divergence_norm ABSENT (reverted) + vol_adj_autocorr ABSENT (still reverted).
- **ITERATION_LABEL** = "v3-028".
- **Run command**: `uv run python run_baseline_v3.py --seeds 2` (NO --exploration; default n_trials=35; ENSEMBLE_SIZE=5)
- **Hypothesis**: iter-v3/025's single-seed +0.88 IS / +1.22 OOS holds at multi-seed --seeds 2 with similar magnitude (within ±0.30 on each axis). If so, iter-v3/029 CONFIRMATION launches with high confidence.
- **Predicted bands** (multi-seed):
  - IS Sharpe: [+0.55, +1.10] median +0.80 (some compression expected from single-seed +0.88)
  - OOS Sharpe: [+0.85, +1.40] median +1.10 (some compression expected from single-seed +1.22)
  - Both seeds positive on Pareto
- **3 pathways**:
  - **PATH A (PROMISING-CONFIRMED)**: IS Sharpe ≥ +0.55 AND OOS Sharpe ≥ +0.85 — iter-v3/025 result HOLDS at multi-seed; iter-v3/029 CONFIRMATION proceeds.
  - **PATH B (PROMISING-COMPRESSION)**: IS [+0.30, +0.55) OR OOS [+0.50, +0.85) — partial compression; iter-v3/029 still proceeds but with lowered expectations.
  - **PATH C (FALSIFIED)**: IS < +0.30 AND OOS < +0.50 — iter-v3/025 was single-seed lottery (analogous to iter-v3/013 → iter-v3/018); iter-v3/029 dead-on-arrival; pivot to fundamentally different bundle.

## Cadence Status

**9 of 10 EXPLORATIONs done in post-bootstrap cycle.** iter-v3/019 (PROMISING-INERT) + iter-v3/020 (NEGATIVE-clean / PATH C) + iter-v3/021 (NEGATIVE-clean) + iter-v3/022 (NEGATIVE-clean / partially-effective-closed) + iter-v3/023 (NEGATIVE-clean / INERT-CONFIRMED + OVERFIT-AT-HIGHER-BUDGET) + iter-v3/024 (NEGATIVE-clean / INERT-OVERFIT-CROSS-ASSET-CONFIRMED) + iter-v3/025 (EXPLORATION-PROMISING clean — first PROMISING; STRONG CONFIRMATION-BUNDLE CANDIDATE) + iter-v3/026 (NEGATIVE-SUSPICIOUS-OOS — engineered features DON'T STACK at single-seed) + iter-v3/027 (**EXPLORATION-NEGATIVE-SUSPICIOUS-OOS — engineered features DON'T STACK REPLICATED across 2 compositions; only iter-v3/025 PROMISING**) completed; **1 EXPLORATION remaining** before next CONFIRMATION (iter-v3/029).

CONFIRMATION wall-clock cap = 6h (per `feedback_v3_cadence_discipline.md` empirically updated post-iter-v3/018). EXPLORATION wall-clock cap = 2h (iter-v3/027 ran 14 min — well within). MINI-VALIDATION (iter-v3/028) budget = ~30 min target.

**Funding family (per-symbol + cross-asset BTC) PERMANENTLY CLOSED for v3** — 3 EXPLORATION data points (iter-v3/019/023/024).

**Off-the-shelf indicator additions SATURATED at the 13-feature stack** — 4 consecutive INERT outcomes (iter-v3/015 + iter-v3/019 + iter-v3/023 + iter-v3/024).

**Engineered features (Category 2 axis) PROVEN PROMISING at iter-v3/025; STACKING at single-seed FALSIFIED ACROSS 2 COMPOSITIONS at iter-v3/026 + iter-v3/027.** Per `feedback_v3_engineered_features_dont_stack.md`: test ONE engineered feature alone; defer stacking to multi-seed CONFIRMATION.

**iter-v3/028 = MINI-VALIDATION of iter-v3/025 at --seeds 2** per Critic FINAL of iter-v3/027 + user directive 2026-05-08. NOT a new feature/methodology axis; structurally a "mini-CONFIRMATION" sanity check before iter-v3/029 CONFIRMATION budget commits.

**iter-v3/029 = CONFIRMATION with iter-v3/013 baseline + regime_momentum_signed_5d bundle** (single-feature MINIMAL).

## Reproducibility

- Setup commit SHA: `b9b6f8d` (feat: cross_asset_divergence_norm engineered feature; atomic swap drop vol_adj_autocorr + add cross_asset_divergence_norm)
- EDA SHA: `254a5f2` (analysis/iteration_v3-027/third_engineered_eda.py + 5 CSV outputs + synthesis.md; cross_asset_divergence_norm selected via Critic FINAL Rec + user directive pre-commit)
- Brief SHA: `4698b21`
- Phase 5.5 gate SHA: `c474cc9`
- Engineering report + Critic FINAL SHA: `966f4c1` (combined commit — engineering_report.md + review.md)
- HEAD SHA at backtest run: `b9b6f8d`
- Reports: `reports-v3/iteration_v3-027/comparison.csv` (single-seed EXPLORATION row), `reports-v3/iteration_v3-027/dsr.json` (DSR=0.0 / PBO=0.1448 / PSR=1.0 / n_trials=105 / n_eff=19), `reports-v3/iteration_v3-027/in_sample/model_importance_last_month_*.csv` (BCH cross_asset 10 / regime 0; LDO cross_asset 360 / regime 309; TRX cross_asset 36 / regime 38; Portfolio cross_asset 406 / regime 347), `reports-v3/iteration_v3-027/seed_summary.json`, `reports-v3/iteration_v3-027/pareto_front.csv`, `reports-v3/iteration_v3-027/ic_matrix.csv`
- Tag (informational): NONE (NEGATIVE-SUSPICIOUS-OOS verdict; not a baseline-update or PROMISING-tag event)
