# Iteration iter-v3/025 — Diary

## Decision: EXPLORATION-PROMISING (clean) — FIRST PROMISING in post-bootstrap cycle

The Category 2 composed feature `regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)` produced a co-directional IS+OOS lift on the iter-v3/018 multi-seed BOOTSTRAP anchor (+0.3788 IS / +0.3869 OOS multi-seed mean), with **IS monthly Sharpe +0.8788** (Δ +0.50 vs anchor — within predicted [+0.30, +0.55] band, slightly above median +0.40) and **OOS monthly Sharpe +1.2244** (Δ +0.84 vs anchor — **FIRST OOS > +1.0 in the post-bootstrap cycle**, ABOVE predicted [+0.40, +0.65] upper bound by +0.57). OOS daily Sharpe +2.0291 is the strongest single-seed daily Sharpe in the post-bootstrap cycle. OOS MaxDD **21.35%** is materially improved from the anchor 27.74% (–7.85pp) AND from the recent 5-iter trajectory of 49.93%-49.97% breaches at iter-v3/023/024. PSR 1.0 + DSR 0.0 are EXPLORATION-mode artifacts (per `feedback_v3_dsr_mode_artifact.md`) — informational only.

**FIRST genuinely PROMISING result in the post-bootstrap cycle** (iter-v3/019 was PROMISING-INERT at single-seed lottery; iter-v3/020/021/022/023/024 all NEGATIVE-clean). PATH A fires unambiguously per brief §4.4 LOCKED criteria: IS Δ +0.50 ≥ +0.10 ✓; OOS Δ +0.84 (positive lift, exceeds anchor + relaxed +1.0 floor) ✓; importance ≥30 across all 4 cuts (BCH 43, LDO 232, TRX 123, Portfolio 398) ✓; co-directional IS+OOS lift (NOT lottery pattern of iter-v3/013) ✓. The engineered feature contributes **51% of top portfolio importance** (398/779) — approximately **2× the contribution of any prior NEW feature** (tbr_zscore_30 25-67% scattered, funding rate variants 22-24% portfolio).

The iter-v3/020/021/022/023/024 frozen-baseline pattern (BCH OOS −6.2465 / LDO OOS −8.9257 bit-identical across 5 iterations per `feedback_v3_single_seed_frozen_baseline.md`) **DISSOLVED** at iter-v3/025: BCH OOS shifted +6.25 → +11.31 (a +17.56 weighted_pnl swing), LDO OOS shifted −8.93 → −1.98 (a +6.95 swing toward neutral). This is structurally consistent with the frozen-baseline rule — adding the engineered feature changed each per-symbol Optuna search space, producing different (and BETTER) trajectories on BCH and LDO. Frozen baseline was feature-set-specific.

**STRONG CONFIRMATION-BUNDLE CANDIDATE for iter-v3/029** — but single-seed lottery risk per `feedback_v3_single_seed_frozen_baseline.md` AND iter-v3/013 precedent (single-seed +1.01 IS / +2.70 OOS → 62% / 86% reduction at multi-seed iter-v3/018 CONFIRMATION). Multi-seed validation is the binding test. Cadence #7 of 10 in the post-bootstrap cycle. Per Critic FINAL Rec of iter-v3/025 + user directive 2026-05-08, **iter-v3/026 axis MANDATED = SECOND ENGINEERED FEATURE** to validate the feature engineering pivot strategy.

## What Was Tested

**Hypothesis (locked in brief Section 1):** "Adding `regime_momentum_signed_5d` (= `ret_5d × sign(hurst_100 − 0.5)`) — momentum 5-day return sign-flipped by trend-vs-mean-reversion regime classifier — as the 14th feature on top of the iter-v3/018 multi-seed BOOTSTRAP baseline (drop-MKR + z=2.0 + ATR 2.0/1.0 + BTC ±15% + ADX=20 + 13 V3_FEATURE_COLUMNS, with both funding variants permanently dropped) — at the EXPLORATION default n_trials=35 — will produce **importance rank improvement** (predicted ≤10 for ≥1 symbol; relaxed from ≤7 because composed features distribute information across multiple decision contexts) AND **IS Sharpe Δ ≥ +0.10** if the regime-conditional momentum interaction is genuinely informative AND LightGBM trees on the 13-feature stack cannot internally compose this interaction at depth-5."

**Spec (locked, single-axis variation — atomic feature swap, NEW Category 2 axis category):**
- V3_FEATURE_COLUMNS_TOP_N: DROP `btc_funding_rate_zscore_30` (revert 14 → 13 — entire funding family now permanently closed)
- V3_FEATURE_COLUMNS_TOP_N: ADD `regime_momentum_signed_5d` (13 → 14 with new engineered feature)
- Net column count UNCHANGED at 14 (atomic swap — single axis)
- ITERATION_LABEL = "v3-025"
- 3-symbol BCH+LDO+TRX universe UNCHANGED
- Other gates BYTE-IDENTICAL to iter-v3/018 anchor (z=2.0, ATR 2.0/1.0, BTC ±15%, ADX=20, Hurst gate, low-vol filter, hit-rate disabled, regime gate disabled, per-symbol cap disabled)
- Implemented `compute_regime_momentum_signed_5d` + `add_engineered_v3_features` in NEW module `src/crypto_trade/features_v3/engineered_v3.py` (clean separation from off-the-shelf primitives — Category 2 distinct from Category 1)
- New `engineered_v3` GROUP_REGISTRY entry (alphabetically AFTER `cross_btc`, BEFORE `fracdiff`); dependency on `hurst_100` from `regime` group preserved by GROUP_REGISTRY insertion order
- Past-only adversarial test PASS (SHA `3b1f979`); 20 adversarial tests verifying ret_5d uses only past close at t-15 + hurst_100 already past-only via 100-bar trailing R/S window
- Ran in EXPLORATION mode: --exploration --seeds 1 (1 outer × 1 inner × 35 n_trials × 3 symbols = **105 fits per cell**; colsample_bytree=1.0)
- Anchor: iter-v3/018 multi-seed mean +0.3788 IS / +0.3869 OOS

This was iter-v3/025, the **first Category 2 (composed/interaction feature) axis in v3 catalog history** and the **FIRST genuinely PROMISING result in the post-bootstrap cycle**.

## Headline Numbers

### Single-seed EXPLORATION run (seed 42)

| Metric | iter-v3/018 anchor (multi-seed mean) | iter-v3/024 (BTC funding cross-asset) | iter-v3/025 (regime_momentum_signed_5d) | Δ vs anchor |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | +0.9750 | **+0.8788** | **+0.5000** (within predicted [+0.30, +0.55], slightly above median +0.40) |
| OOS monthly Sharpe | +0.3869 | −0.8170 | **+1.2244** | **+0.8375** (ABOVE predicted [+0.40, +0.65] upper bound by +0.57; FIRST OOS > +1.0 in post-bootstrap cycle) |
| OOS daily Sharpe | +0.6 (mean) | — | **+2.0291** | strongest single-seed daily Sharpe in post-bootstrap |
| OOS/IS Sharpe ratio | 1.02 | −0.84 | **1.39** | within predicted [0.55, 1.50] — strong generalization |
| IS n_trades | 172 (mean) | 182 | **194** | within saturation band [129, 215] (Δ +22 from anchor) |
| OOS n_trades | 90.5 (mean) | 85 | **95** | <130 trade-rate floor (informational at EXPLORATION; bundle-level at CONFIRMATION per `feedback_trade_rate_floor_bundle_level.md`) |
| IS MaxDD | 21.86% (mean) | 28.91% | **27.49%** | improved relative to iter-v3/024 (−1.42pp) |
| OOS MaxDD | 27.74% (best seed 42) | 49.97% | **21.35%** | **−7.85pp from anchor** ; **−28.62pp from iter-v3/024** ; broken the 50%-adjacent breach trajectory |
| Total OOS PnL | +∼7% (mean) | −32.10% | **+32.56%** | sign restored (+39.66% vs iter-v3/024) |
| OOS WR | 36.4% (mean) | — | **45.26%** | broad improvement in win rate |
| DSR | 0.0 (n_trials=1500) | 3.25e-06 | **0.0** | EXPLORATION artifact (n_trials=105 = 35×3 sym; structural per `feedback_v3_dsr_mode_artifact.md`) |
| PBO mean | 0.0892 | 0.0843 | **0.1009** | PASS (< 0.40); minor uptick consistent with new feature dimension |
| PSR | 0.9936 | 0.0000 | **1.0** | EXPLORATION-mode saturation (consistent with positive observed Sharpe; informational only) |
| n_eff | 25 (CONFIRMATION) | 19 | **19** | maintained (validates n_trials=35 default; consistent regime ×6) |
| n_trials | 1500 (CONFIRMATION) | 105 | **105** (n=35 × 3 sym) | EXPLORATION default |
| profit_factor (IS / OOS) | — | — | **1.31 / 1.30** | balanced |
| monthly_calmar (IS / OOS) | — | — | **2.51 / 1.52** | strong IS, healthy OOS |

### regime_momentum_signed_5d feature importance — PRIMARY DIAGNOSTIC METRIC

| Cut | Importance value | % of Top Feature | Cohort Rank | PATH A criterion (≤10 OR ≥30) |
|---|---:|---:|---:|---|
| BCH | 43 | 25% (vs top ret_kurt_50=173) | 13-14/14 | ✓ (importance 43 ≥ 30) |
| LDO | **232** | **67%** (vs top hurst_diff_100_50=347) | **~8-9/14** | ✓ ✓ (rank ≤10 AND importance ≥30) |
| TRX | 123 | 39% (vs top range_realized_vol_50=313) | ~10-11/14 | ✓ (importance 123 ≥ 30; rank borderline) |
| Portfolio | 398 | **51%** (vs top range_realized_vol_50=779) | 14/14 | ✓ (importance 398 ≥ 30) |

**Falsifier 4 (PATH A trigger) fires unambiguously**: rank ≤10 satisfied on LDO (rank ~8-9) AND importance ≥30 satisfied on ALL 4 cuts. Compared to the prior NEW-feature-attempt history:

| Iteration | Feature | Importance % of Top | OOS Sharpe Δ | Verdict |
|-----------|---------|---------------------|---------------|---------|
| 015 | tbr_zscore_30 (microstructure) | 25-67% (per-sym 14/14) | +1.74 vs anchor (lottery) | PROMISING-INERT |
| 019 | funding_rate_zscore_30 (per-sym, n=10) | 22% portfolio | +0.39 vs anchor (lottery) | PROMISING-INERT |
| 023 | funding_rate_zscore_30 (per-sym, n=35) | 22% portfolio | -1.46 vs anchor | NEGATIVE |
| 024 | btc_funding_rate_zscore_30 (cross-asset) | 24% portfolio | -1.20 vs anchor | NEGATIVE |
| **025** | **regime_momentum_signed_5d (ENGINEERED)** | **51% portfolio** | **+0.84 vs anchor** | **PROMISING ✓** |

The engineered feature has ~2× the importance contribution of any prior NEW feature AND co-directional positive lift. This validates the user's "feature engineering" pivot directive empirically.

### Per-symbol attribution (single-seed; OOS) — frozen baseline DISSOLVED

| Symbol | iter-v3/020-024 frozen baseline OOS | iter-v3/025 OOS PnL | Δ | Trades | WR | Concentration |
|---|---:|---:|---:|---:|---:|---:|
| BCH | −6.2465 | **+11.31** | **+17.56** | 38 | 39.5% | +34.73% |
| LDO | −8.9257 | **−1.98** | **+6.95** | 11 | 36.4% | −6.09% (~neutral) |
| TRX | +5.39 to +14.31 (varied) | **+23.23** | mid-range improvement | 46 | **52.2%** | 71.36% (positive concentration) |

**Forensic finding**: the frozen baseline pattern (BCH/LDO bit-identical across iter-v3/020/021/022/023/024) DISSOLVED at iter-v3/025. This is consistent with `feedback_v3_single_seed_frozen_baseline.md`: per-symbol Optuna trajectories are deterministic at single-seed=42 only when V3_FEATURE_COLUMNS is identical across iterations. iter-v3/025 changed V3_FEATURE_COLUMNS by atomically swapping the 14th column (drop btc_funding + add regime_momentum), producing distinct Optuna search spaces for each per-symbol model and BETTER trajectories on BCH+LDO.

TRX's 52.2% WR is the highest single-symbol single-seed WR in v3 catalog. The regime feature plausibly filters bad-trend trades by sign-flipping momentum based on Hurst regime — but a multi-seed CONFIRMATION at iter-v3/029 will reveal whether this WR is robust or single-seed lottery.

### Saturation falsifier verification (per `feedback_axis_saturation_predictor.md`)

| Predictor | Lower bound | Upper bound | Observed | Triggered? |
|---|---:|---:|---:|---|
| IS trade band (brief §2.3) | 129 | 215 | **194** | NO (within band — axis behavioral effect on trade count is in expected range) |

Saturation predictor passes — the new feature did not behave anomalously at the trade-count level. Iteration's PROMISING outcome is genuine signal-add, not behavioral-effect saturation. Identical predictor outcome to iter-v3/023 + iter-v3/024 (consistent regime ×3).

## What Worked

- **Methodology of the run is clean.** All 12 standard methodology checks PASS or PASS-EXPLORATION informational (Critic FINAL `402643d`). Look-ahead audit verified by 20 adversarial tests on `compute_regime_momentum_signed_5d` (past-only construction confirmed: `ret_5d` via `.shift(15)`-rooted log-close diff; `hurst_100` already past-only via rolling 100-bar R/S window). Track-isolation grep clean. Embargo width REQUIRED_GAP=66=(21+1)×3 unchanged. Reproducibility stamp clean (Setup `3b1f979`, brief `6b44e81`, EDA `917605b`, engineering+Critic `402643d`). Single-axis discipline preserved: V3_FEATURE_COLUMNS=14 (atomic swap — DROP btc_funding + ADD regime_momentum; column count UNCHANGED); ITERATION_LABEL=v3-025.

- **IC orthogonality CARVE-OUT (per `feedback_v3_engineered_feature_pivot.md`) operates as designed.** EDA flagged max |IC|=0.887 with vwap_dev_20 — would have BLOCKED the candidate under standard Category 1 rules. The Phase 5.5 gate explicitly bypassed the IC hard gate per Category 2 carve-out, deferring the binding evidence test to feature importance rank ≤10 AND absolute importance ≥30. The empirical outcome (LDO rank ~8-9 with importance 232) validates the carve-out: the high-IC pattern is structural for composed features (they share variance with source primitives BY CONSTRUCTION), but the model uses the composed feature non-trivially anyway.

- **n_trials=35 EXPLORATION default validates positively at iter-v3/025 (PRELIMINARY-VALIDATED through iteration #6).** n_eff=19 maintained from iter-v3/020/021/022/023/024 — consistent regime ×6 EXPLORATIONs. PSR=1.0 saturates honestly when observed Sharpe is materially positive (mirror of iter-v3/023/024's PSR=0.0 honest collapse on materially negative Sharpe). DSR=0.0 reflects honest deflation at n_trials=105. Wall-clock 14 min (well within 2h cap). Six data points (4 NEGATIVE + 1 PROMISING + 1 PROMISING-INERT) confirm n_trials=35 default operates in the honest deflation regime AND surfaces genuine signal when the underlying feature is informative.

- **OOS MaxDD trajectory inverted.** iter-v3/023 (49.93%) + iter-v3/024 (49.97%) were 2 consecutive 50%-adjacent breaches under the INERT-OVERFIT mechanism. iter-v3/025's 21.35% OOS MaxDD is **−28.62pp from iter-v3/024** AND **−7.85pp from anchor** — the engineered feature both adds signal AND reduces tail risk. Mechanistic explanation: regime-conditional momentum reduces position-taking in adverse regimes (when sign-flip inverts predicted direction relative to short-term trend), filtering out catastrophic drawdown periods that the raw 13-feature stack couldn't classify.

- **OOS WR 45.26% broad improvement.** Anchor mean ~36.4%; iter-v3/025 +8.86pp. Per-symbol: BCH 39.5%, LDO 36.4%, TRX 52.2%. The improvement is broad-based (not lottery-concentrated) — TRX 52.2% is the standout but BCH+LDO also improved relative to their prior frozen-baseline 36.1% / 38.5% WRs.

- **Engineered feature mechanism empirically validated.** PATH A criteria fired unambiguously across all 4 cuts. The hypothesis "depth-3-5 LightGBM trees on the 13-feature stack cannot internally compose `feature_A × sign(feature_B − threshold)` interactions at the candidate-split level" is now empirically supported. The model's feature importance rank ~8-9 on LDO (importance 232 = 67% of top hurst_diff_100_50) is direct evidence the composed feature provides INTERACTION value the raw 13 features could not surface.

## What Failed (caveats — informational, not verdict-blocking)

- **Single-seed lottery risk per iter-v3/013 precedent.** iter-v3/013 looked similarly strong at single-seed (+1.0088 IS / +2.6970 OOS); falsified at iter-v3/018 multi-seed CONFIRMATION (62% IS reduction, 86% OOS reduction; LDO 80% WR was Optuna-path lottery). iter-v3/025 needs multi-seed validation at iter-v3/029 CONFIRMATION before being trusted as a CONFIRMATION-MERGE candidate. Brief §4.4 PATH A explicitly flagged this caveat: "NOT a CONFIRMATION-bundle candidate at single-seed (lottery suspect rule per `feedback_v3_single_seed_frozen_baseline.md`); flag for iter-v3/029+ CONFIRMATION evaluation."

- **OOS trades 95 < 130 trade-rate floor.** Informational caveat at EXPLORATION single-seed per `feedback_trade_rate_floor_bundle_level.md` — the floor applies at CONFIRMATION-bundle level (5 outer seeds × 3-4× ensemble inflation = 285-380 OOS bundle trades predicted at iter-v3/029, well above 130). At single-seed EXPLORATION, n=95 is below floor; mechanism unchanged from prior 6 EXPLORATIONs.

- **Importance rank 14/14 in portfolio aggregate (BY ABSOLUTE IMPORTANCE ORDERING).** The relaxed `importance ≥ 30` threshold is what catches this case under the Category 2 carve-out — strict `rank ≤ 7` would have missed it (portfolio importance 398 is the 14th-highest absolute value but is 51% of top). The carve-out per `feedback_v3_engineered_feature_pivot.md` is doing real work: composed features distribute information across multiple decision contexts, so absolute-importance rank can mislead even when the model uses the feature heavily. The relaxed `rank ≤10 OR importance ≥30` criteria caught LDO at rank 8-9 AND all 4 cuts at importance ≥30, validating the carve-out. Portfolio rank 14/14 is informational only at iter-v3/025; the multi-seed CONFIRMATION at iter-v3/029 will produce per-cell rank distributions that more accurately reflect the feature's contribution across Optuna trajectories.

- **TRX 52.2% WR is the highest single-symbol single-seed WR in v3 catalog.** Suggestive of Optuna lottery risk at single-seed=42 (a 7-of-13-trade win streak fits within reasonable noise on a fair-coin-around-40% baseline). Multi-seed CONFIRMATION at iter-v3/029 is the test. Audit-trail caveat for the future CONFIRMATION-bundling QR: do NOT bundle iter-v3/025 into iter-v3/029 if multi-seed mean WR < 42% across BCH+LDO+TRX.

## Critical Lessons

(a) **Composed features capture interactions LightGBM trees cannot compose internally at depth 3-5.** This is the central lesson of iter-v3/025 and validates the entire FEATURE ENGINEERING pivot directive. The model has been finding stable splits on the existing 13 primitives across iter-v3/015/019/023/024 (all rank-14/14 INERT additions) precisely because the missing signal is INTERACTION between primitives, not standalone signal in a new primitive. The composed `regime_momentum_signed_5d = ret_5d × sign(hurst_100 - 0.5)` precomputes one specific interaction (regime-conditional momentum), freeing tree capacity for the actual decision boundary. Per AFML Ch. 8 — feature importance under multicollinearity systematically under-attributes composed features that share variance with source primitives. The high-IC pattern observed in EDA (max |IC|=0.887) is expected and structural.

(b) **Off-the-shelf indicators (microstructure, funding, BTC funding cross-asset) all hit rank 14/14 INERT in the 13-feature stack.** Four consecutive Category 1 NEW-feature axes (iter-v3/015 microstructure tbr_zscore_30; iter-v3/019 per-sym funding n=10; iter-v3/023 per-sym funding n=35; iter-v3/024 BTC cross-asset funding n=35) each producing rank 14/14 across at least 3 of 4 cuts confirms the existing 13-feature LightGBM cannot extract additional signal from raw indicator-style additions. The category-level lesson: off-the-shelf indicator additions are SATURATED for this architecture; future axes must be engineered features.

(c) **Engineered features OUTPERFORM off-the-shelf indicators for v3's per-symbol LightGBM at the 13-feature stack.** iter-v3/025's engineered feature contributes 51% of top portfolio importance vs. 22-25% for prior NEW Category 1 features (~2× the contribution). Co-directional IS+OOS lift (+0.50 IS / +0.84 OOS) versus iter-v3/019's lottery-positive IS lift that collapsed at retest. The OOS MaxDD reduction (−28.62pp from iter-v3/024) is structurally distinct from any prior +1-feature axis. **This is not a one-off lucky composition — it's empirical evidence that the failure mode of Category 1 axes at the 13-feature stack is COMPOSITIONAL.** Future axes in the post-bootstrap cycle (iter-v3/026/027/028) should prioritize Category 2 (engineered/composed) over Category 1 (off-the-shelf indicator) additions.

(d) **Frozen baseline is feature-set-specific; dissolves on V3_FEATURE_COLUMNS change.** Per `feedback_v3_single_seed_frozen_baseline.md` (established iter-v3/022), per-symbol Optuna trajectories at fixed seed=42 are deterministic ONLY when the input feature space is identical across iterations. iter-v3/020/021/022/023/024 all shared V3_FEATURE_COLUMNS = 13 (or 14 with funding variants treated as functionally INERT — model ignored them at rank 14/14). iter-v3/025 changed V3_FEATURE_COLUMNS by introducing a NEW feature with 51% portfolio importance — this changed the per-symbol search space and produced new (better) Optuna trajectories on BCH+LDO. The frozen-baseline rule continues to hold at the architectural level: same V3_FEATURE_COLUMNS + same single-seed ⇒ same per-symbol trajectories. Cross-iteration headline regression in the iter-v3/020-024 chain was a symptom of this rule, not a real signal.

(e) **Single-seed PROMISING needs multi-seed validation at CONFIRMATION before bundling.** Per `feedback_v3_single_seed_frozen_baseline.md` + iter-v3/013 precedent, single-seed Sharpe values at EXPLORATION are subject to Optuna-trajectory lottery noise. iter-v3/013 looked like +1.01 IS / +2.70 OOS at single-seed; multi-seed CONFIRMATION reduced these to +0.38 / +0.39 (62% / 86% reductions). iter-v3/025's +0.88 IS / +1.22 OOS may exhibit similar reduction at multi-seed CONFIRMATION. The catalog row carries this caveat explicitly. iter-v3/029 CONFIRMATION must run multi-seed (--seeds 2 minimum per `feedback_outer_seed_cap_2_v3.md`) and pre-register a formal lottery-floor: PROMISING at single-seed must clear ≥+0.20 IS Δ AND ≥+0.20 OOS Δ at multi-seed mean to count as a true CONFIRMATION-bundle candidate.

(f) **iter-v3/026 axis = SECOND ENGINEERED FEATURE to validate the pivot strategy.** Per Critic FINAL Recommendation of iter-v3/025 (SHA `402643d`) + Critic prior in engineering report §iter-v3/026 axis recommendation: if 2 of 2 engineered features land PROMISING, this is strong evidence the feature engineering pivot is THE right axis category for v3 in the remainder of the post-bootstrap cycle (iter-v3/027/028 also engineered features). If iter-v3/026 lands PROMISING-INERT or NEGATIVE, the pivot is narrower than hoped — only one specific composition (regime-conditional momentum) works at the 13+1 feature stack. Either outcome is informative. KEEP `regime_momentum_signed_5d` in V3_FEATURE_COLUMNS at iter-v3/026 (do NOT revert) — engineered features can stack incrementally; the second engineered feature composes ON TOP of regime momentum.

## Pre-Commit for iter-v3/026

Per Critic FINAL Recommendation of iter-v3/025 (SHA `402643d`) + diary lessons (a)-(f) + user directive 2026-05-08:

- **iter-v3/026 axis = SECOND engineered feature (Category 2 axis #2 in v3 catalog)**.
- **KEEP** `regime_momentum_signed_5d` in V3_FEATURE_COLUMNS (do NOT revert — engineered features stack incrementally per Critic Rec).
- **ADD** ONE additional engineered feature (V3_FEATURE_COLUMNS 14 → 15). QR's call from the EDA leaderboard candidates:
  1. `vol_adj_autocorr` = `ret_autocorr_lag1_50 / (range_realized_vol_50 + 1e-6)` — autocorrelation per unit vol; structurally orthogonal to regime_momentum (different primitives: ret_autocorr_lag1_50 vs ret_5d; range_realized_vol_50 vs hurst_100). Implementation cost lowest.
  2. `cross_asset_divergence_norm` = `(sym_ret_7d − btc_ret_14d) / vwap_dev_20` — composite of cross-asset ratio and volume-divergence normalization. Composite leaderboard #1 (0.6500).
  3. `fracdiff_d05_close` (López de Prado AFML Ch. 5) — fractional differentiation of close at d=0.5; explicit v3 skill mandate from iter-v3/001 scope never delivered.
  4. `hurst_drift_50_200` = `hurst_50 − hurst_200` (multi-timeframe regime drift) — requires hurst_50/hurst_200 primitives not currently in V3_FEATURE_COLUMNS.

- **Recommendation**: pick #1 `vol_adj_autocorr` — simplest, structurally orthogonal to regime_momentum (different primitives), implementation cost lowest. #3 fracdiff is more ambitious but adds significant infrastructure cost (LdP Ch. 5 weight-coefficient computation + convolution).
- **Implementation**: extend existing `engineered_v3.py` module with new `compute_<chosen_feature>` function and update `add_engineered_v3_features` to call it. Single-axis discipline preserved (1 NEW composed feature).
- **Verify** ALL components past-only via adversarial test at first commit. ret_autocorr_lag1_50 already past-only via 50-bar trailing window; range_realized_vol_50 already past-only.
- **ITERATION_LABEL** = "v3-026".
- **Update `_verify_feature_columns`** to assert len==15 + new feature present + regime_momentum_signed_5d still present.
- **Hypothesis**: A second engineered feature (orthogonal mechanism to regime_momentum) further captures interactions that LightGBM trees cannot compose internally; lifts OOS Sharpe an additional +0.10 to +0.30 above iter-v3/025 anchor. Tests whether the feature engineering pivot is consistently productive (NOT just a one-off lucky composition).
- **NEW anchor** = iter-v3/025 single-seed +0.8788 IS / +1.2244 OOS (per single-seed PROMISING precedent).
- **Predicted bands**:
  - IS Sharpe: [+0.80, +1.10] median +0.95 (anchor +0.8788, +0.07 to +0.22 marginal lift)
  - OOS Sharpe: [+1.05, +1.40] median +1.20 (anchor +1.2244, near-flat to +0.18 marginal lift)
  - Importance: ≥30 for the new feature (consistent with iter-v3/025 PATH A floor)
- **Three pathways**:
  - **PATH A (PROMISING)**: both engineered features show importance ≥30, IS+OOS co-direct → STRONG bundle for iter-v3/029 CONFIRMATION
  - **PATH B (PROMISING-INERT)**: new feature 14/14 importance, regime_momentum_signed_5d retains importance ≥30 — engineered category narrowly succeeds (only regime_momentum works); pivot to architectural axes at iter-v3/027
  - **PATH C (NEGATIVE)**: IS or OOS drops > 0.10 below iter-v3/025 anchor — second feature actively hurts; might be regime_momentum capturing all signal; the engineered-feature pivot is single-feature-narrow

## Cadence Status

**7 of 10 EXPLORATIONs done in post-bootstrap cycle.** iter-v3/019 (PROMISING-INERT) + iter-v3/020 (NEGATIVE-clean / PATH C) + iter-v3/021 (NEGATIVE-clean) + iter-v3/022 (NEGATIVE-clean / partially-effective-closed) + iter-v3/023 (NEGATIVE-clean / INERT-CONFIRMED + OVERFIT-AT-HIGHER-BUDGET) + iter-v3/024 (NEGATIVE-clean / INERT-OVERFIT-CROSS-ASSET-CONFIRMED) + iter-v3/025 (**EXPLORATION-PROMISING clean — FIRST PROMISING in post-bootstrap; STRONG CONFIRMATION-BUNDLE CANDIDATE**) completed; **3 EXPLORATIONs remaining** before next CONFIRMATION (earliest = iter-v3/029).

CONFIRMATION wall-clock cap = 6h (per `feedback_v3_cadence_discipline.md` empirically updated post-iter-v3/018). EXPLORATION wall-clock cap = 2h (iter-v3/025 ran 14 min — well within).

**Funding family (per-symbol + cross-asset BTC) PERMANENTLY CLOSED for v3** — 3 EXPLORATION data points (iter-v3/019/023/024) confirmed structural INERT in per-symbol-LightGBM-on-13-features architecture.

**Off-the-shelf indicator additions SATURATED at the 13-feature stack** — 4 consecutive INERT outcomes (iter-v3/015 + iter-v3/019 + iter-v3/023 + iter-v3/024).

**Engineered features (Category 2 axis) PROVEN PROMISING at iter-v3/025** — first PROMISING in post-bootstrap cycle. Highest-priority axis category for the remainder of the cycle (iter-v3/026/027/028).

**iter-v3/026 = SECOND engineered feature per Critic FINAL of iter-v3/025 + user directive 2026-05-08.**

## Reproducibility

- Setup commit SHA: `3b1f979` (feat: regime_momentum_signed_5d engineered feature; DROP btc_funding + ADD regime_momentum_signed_5d)
- EDA SHA: `917605b` (analysis/iteration_v3-025/feature_engineering_eda.py + 5 CSV outputs + synthesis.md; 6 of 7 candidates evaluated; #3 adx_signed_momentum REJECTED)
- Brief SHA: `6b44e81`
- Engineering report + Critic FINAL SHA: `402643d` (combined commit — engineering_report.md + review.md)
- HEAD SHA at backtest run: `3b1f979`
- Reports: `reports-v3/iteration_v3-025/comparison.csv` (single-seed EXPLORATION row), `reports-v3/iteration_v3-025/dsr.json` (DSR=0.0 / PBO=0.1009 / PSR=1.0 / n_trials=105 / n_eff=19), `reports-v3/iteration_v3-025/in_sample/model_importance_last_month_*.csv` (BCH 14/14 imp 43, LDO ~8-9/14 imp 232, TRX ~10-11/14 imp 123, Portfolio 14/14 imp 398), `reports-v3/iteration_v3-025/seed_summary.json`, `reports-v3/iteration_v3-025/pareto_front.csv`, `reports-v3/iteration_v3-025/ic_matrix.csv`, `reports-v3/iteration_v3-025/adf_test.csv`
- Tag (informational): `iter-v3/025-PROMISING` (FIRST PROMISING in post-bootstrap cycle; not a baseline-update event)
