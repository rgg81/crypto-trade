# Iteration iter-v3/024 — Diary

## Decision: EXPLORATION-NEGATIVE (clean) — INERT-OVERFIT confirmed across funding family

The btc_funding_rate_zscore_30 cross-asset variant produced the **same INERT-OVERFIT pattern** as iter-v3/023's per-symbol funding RETEST: the new 14th feature ranks **14/14 (BCH portfolio + LDO + Portfolio)** and **9/14 (TRX)** in LightGBM importance — entirely concentrated in the bottom-quartile of feature contribution; the BCH model assigns importance 2 vs top vwap_dev_20=119 (1.7% of top); the LDO model assigns 57 vs top 156 (36.5% of top, but still rank 14/14); the Portfolio aggregator at 76 vs top vwap_dev_20=321 (23.7% of top, rank 14/14). The IS Sharpe lift +0.60 vs anchor +0.3788 (observed +0.9750) is at the **largest IS lift in the post-bootstrap cycle** but the OOS Sharpe **−0.8170** (Δ −1.20 vs anchor +0.3869) is the **3rd worst single-seed OOS in v3 anchor-basis history** (after iter-v3/023 −1.46 and iter-v3/021 −0.83); OOS MaxDD **49.97%** is the **2nd consecutive 50%-adjacent breach** (iter-v3/023 was 49.93%) — both within iterations adding rank-14/14 features at n_trials=35.

The **funding-feature family is now entirely closed in v3**: 3 of 3 funding-derived axes (per-symbol funding at n=10 in iter-v3/019, per-symbol funding at n=35 in iter-v3/023, BTC cross-asset funding at n=35 in iter-v3/024) all produce the same rank-14/14 importance pattern, and the 2 iterations at n_trials=35 both produce OOS Sharpe ≤ −0.82 and MaxDD ≥ 49.93%. The mechanism is INERT-OVERFIT (per `feedback_v3_inert_features_at_higher_budget.md`): the funding feature carries near-zero genuine information for v3's per-symbol-LightGBM-on-13-features architecture, but adding it as a 14th column at n_trials=35 expands Optuna's parameter search space along an uninformative dimension, leading to IS-overfit hyperparameter trajectories that do not generalize to OOS.

NOT a CONFIRMATION-bundle candidate. The funding feature family is **PERMANENTLY CLOSED** at the catalog level in v3 — neither per-symbol funding rate nor BTC-broadcast cross-asset funding can be retested at any higher trial budget without first changing the underlying model architecture, labeling, or feature set. Cadence #6 of 10 in the post-bootstrap cycle. **Per user directive 2026-05-08 + Critic FINAL Recommendation, iter-v3/025 axis MANDATED = genuine feature engineering pivot** — ENGINEERED/COMPOSED features built from existing primitives, not off-the-shelf indicator additions or new external data sources.

## What Was Tested

**Hypothesis (locked in brief Section 1):** "Adding `btc_funding_rate_zscore_30` (BTC's funding-rate z-score broadcast to ALL 3 per-symbol models) as the 14th feature on top of the iter-v3/018 multi-seed BOOTSTRAP baseline — at n_trials=35 — will produce **importance rank improvement** (predicted ≤7 for ≥1 symbol) AND **IS Sharpe Δ ≥ +0.10** if the cross-asset signal captures market-wide leveraged-positioning stress that per-symbol funding (iter-v3/019/023 INERT) couldn't surface. Predicted IS Sharpe band [+0.30, +0.55] median +0.40; predicted OOS Sharpe band [+0.40, +0.65] median +0.50."

**Spec (locked, single-axis variation — atomic funding-source switch):**
- V3_FEATURE_COLUMNS_TOP_N: DROP per-symbol `funding_rate_zscore_30` (revert 14 → 13)
- V3_FEATURE_COLUMNS_TOP_N: ADD `btc_funding_rate_zscore_30` (13 → 14 with new feature)
- Net column count UNCHANGED at 14 (atomic switch — single axis)
- ITERATION_LABEL = "v3-024"
- 3-symbol BCH+LDO+TRX universe UNCHANGED
- Other gates BYTE-IDENTICAL to iter-v3/018 anchor (z=2.0, ATR 2.0/1.0, BTC ±15%, ADX=20, Hurst, low-vol, hit-rate disabled, regime gate disabled)
- Implemented `compute_btc_funding_rate_zscore` + `add_btc_funding_v3_features` in `funding_v3.py`; new `btc_funding_v3` GROUP_REGISTRY entry
- Past-only adversarial test PASS (SHA `b28db27`)
- Ran in EXPLORATION mode: --exploration --seeds 1 (1 outer × 1 inner × 35 n_trials × 3 symbols = **105 fits per cell**; colsample_bytree=1.0)
- Anchor: iter-v3/018 multi-seed mean +0.3788 IS / +0.3869 OOS

This was iter-v3/024, the **first cross-asset variant of a previously-INERT feature in v3 catalog history**.

## Headline Numbers

### Single-seed EXPLORATION run (seed 42)

| Metric | iter-v3/018 anchor (multi-seed mean) | iter-v3/023 (per-sym funding n=35) | iter-v3/024 (BTC cross-asset n=35) | Δ vs anchor |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | +0.5270 | **+0.9750** | **+0.5962** (largest IS lift in post-bootstrap cycle; ABOVE predicted [+0.30, +0.55] upper bound) |
| OOS monthly Sharpe | +0.3869 | −1.0706 | **−0.8170** | **−1.2039** (3rd worst single-seed OOS in v3; missed predicted [+0.40, +0.65] band by −1.22 from lower bound) |
| OOS/IS Sharpe ratio | 1.02 | −2.03 | **−0.84** | sign flip (severe inversion) |
| IS n_trades | 172 (mean) | 195 | **182** | within saturation band [129, 215] |
| OOS n_trades | 90.5 (mean) | 92 | **85** | <130 trade-rate floor (informational at EXPLORATION) |
| IS MaxDD | 21.86% (mean) | 20.54% | **28.91%** | +7.05pp |
| OOS MaxDD | 27.74% (best seed 42) | 49.93% | **49.97%** | +22.23pp; **2nd consecutive 50%-adjacent breach** |
| Total OOS PnL | +∼7% (mean) | −33.21% | **−32.10%** | sign flip (catastrophic 2nd time) |
| DSR | 0.0 (n_trials=1500) | 0.000003 | **0.000003** | EXPLORATION artifact, structural |
| PBO mean | 0.0892 | 0.0922 | **0.0843** | unchanged (methodology clean) |
| **PBO max** | **1.0 (TRX/2022-Q4)** | 1.0 | 1.0 | unchanged carry-forward |
| **PSR** | 0.9936 | 0.0000 | **0.0000** | collapsed (consistent with negative observed Sharpe) |
| n_eff | 25 (CONFIRMATION) | 19 | **19** | maintained (validates n_trials=35 default; consistent regime ×5) |
| n_trials | 1500 (CONFIRMATION) | 105 | **105** (n=35 × 3 sym) | EXPLORATION default |

### btc_funding_rate_zscore_30 importance rank — PRIMARY DIAGNOSTIC METRIC

| Symbol | iter-v3/019 per-sym (n=10) | iter-v3/023 per-sym (n=35) | iter-v3/024 BTC cross-asset (n=35) | Verdict |
|---|---:|---:|---:|---|
| BCH | 10/14 | 13/14 | **14/14** (importance=2) | WORSE than iter-v3/023 |
| LDO | 14/14 | 14/14 | **14/14** (importance=57) | IDENTICAL bottom rank |
| TRX | 14/14 | 14/14 | **9/14** (importance=17) | mid-pack — ONLY symbol with non-bottom rank |
| Portfolio | 14/14 | 14/14 | **14/14** (importance=76) | IDENTICAL bottom rank |

**Falsifier 4 fires unambiguously**: rank ≤7 (top half) NOT achieved on any symbol. PATH B (PROMISING-INERT) feature-importance condition strictly satisfied on 3 of 4 cuts (BCH + LDO + Portfolio at 14/14). TRX's rank 9/14 (importance=17) is the only departure from the per-symbol funding INERT pattern — but rank 9 is still bottom-quartile (Q3 = 64th pctile from top), well below the top-half threshold (≤7) required for PATH A. **The cross-asset BTC funding broadcast feature is genuinely uninformative for v3's per-symbol-LightGBM architecture at the 13+1 feature stack.**

### Per-symbol attribution (single-seed; OOS)

| Symbol | iter-v3/023 OOS PnL | iter-v3/024 OOS PnL | n_trades | WR | Concentration |
|---|---:|---:|---:|---:|---:|
| BCH | −26.21 | **−18.65** | 33 | 33.3% | 58.11% (largest negative MaxDD driver) |
| LDO | −16.13 | **−27.75** (catastrophic) | 11 | 27.3% | 86.45% (lottery-negative) |
| TRX | +9.13 | **+14.31** (only positive) | 41 | 46.3% | −44.56% (offsetting) |

**Forensic finding**: TRX's positive contribution (+14.31 weighted_pnl) is the only OOS bright spot, consistent with TRX's mid-pack (9/14) feature rank — TRX's model does use the BTC funding feature non-trivially (importance=17, mid-quartile), and TRX's OOS performance is the only positive in the portfolio. This is suggestive but the BCH+LDO catastrophic collapse (−18.65 + −27.75 = −46.40 weighted_pnl loss vs a zero baseline) overwhelms TRX's gain by 3.2×. The cross-asset feature does not save the portfolio.

### Saturation falsifier verification (per `feedback_axis_saturation_predictor.md`)

| Predictor | Lower bound | Upper bound | Observed | Triggered? |
|---|---:|---:|---:|---|
| IS trade band (brief §2.3) | 129 | 215 | **182** | NO (within band — axis behavioral effect on trade count is in expected range) |

The saturation predictor passes — the new feature did not behave anomalously at the trade-count level. The iteration's failure mode is OOS overfit, not behavioral-effect saturation. Identical predictor outcome to iter-v3/023.

## What Worked

- **Methodology of the run is clean.** All 12 standard methodology checks PASS (Critic FINAL `5a47f5d`). Look-ahead audit verified by `.shift(1)` past-only construction in `compute_btc_funding_rate_zscore` (adversarial test PASS at setup commit `b28db27`). Embargo width REQUIRED_GAP=66=(21+1)×3 unchanged. Reproducibility stamp clean (Setup `b28db27`, gate `4a50c5c`, brief `c1c2f15`, EDA `afdb8bc`, engineering+Critic `5a47f5d`). Single-axis discipline preserved: V3_FEATURE_COLUMNS=14 (atomic switch — DROP per-symbol funding + ADD BTC cross-asset; column count UNCHANGED); ITERATION_LABEL=v3-024.

- **n_trials=35 EXPLORATION default validates positively at iter-v3/024 (PRELIMINARY-VALIDATED through iteration #5).** n_eff=19 maintained from iter-v3/020/021/022/023 — consistent regime ×5 EXPLORATIONs. PSR=0.0000 collapses honestly when observed Sharpe is materially negative. DSR=0.000003 reflects honest deflation. Wall-clock 14 min (well within 2h cap). Five data points confirm n_trials=35 default operates in the honest deflation regime.

- **TRX cross-asset signal-detection partial-success is suggestive.** Of all v3 funding tests (iter-v3/019/023/024), TRX is the ONLY symbol-axis combination where a funding feature reached non-bottom rank (9/14, importance=17 vs vwap_dev_20=46 = 37% of top). TRX's positive OOS contribution (+14.31) on the BTC cross-asset variant is consistent. **NOT a basis for PATH A** (only 1 of 3 symbols partial-success; rank 9 still in bottom-quartile), but a useful signal for future architecture exploration (e.g., funding-rate-as-regime-classifier-only for TRX on a different model family).

- **INERT-OVERFIT pattern generalized across funding family.** 2 consecutive iterations at n_trials=35 producing OOS MaxDD ≥ 49.93% on rank-14/14 funding features is now sufficient empirical evidence to permanently close the funding family in v3. The new memory rule from iter-v3/023 (`feedback_v3_inert_features_at_higher_budget.md`) is empirically reaffirmed.

## What Failed

- **Falsifier 1 (PATH C trigger) fires unambiguously**: OOS Sharpe Δ −1.20 << −0.10 threshold (anchor +0.3869). The catastrophic OOS collapse is decisive — observed −0.82 vs predicted [+0.40, +0.65] band missed by −1.22 from the lower bound.

- **Falsifier 4 (PATH B PROMISING-INERT trigger) ALSO fires**: rank 14/14 across BCH+LDO+Portfolio; TRX 9/14 (still bottom-quartile). PATHs B + C fire simultaneously — the OOS collapse is the binding constraint; verdict triggers via PATH C OOS-collapse condition + PATH B INERT-CONFIRMED footnote (3 of 4 cuts at 14/14).

- **OOS Sharpe Δ −1.20 (vs anchor) — 3rd worst single-seed OOS in v3 history.** Brief §4.2 predicted OOS Sharpe band [+0.40, +0.65]; observed −0.82 missed the entire band by −1.22 from the lower bound. The QR's reasoning that "BTC funding is exogenous to per-symbol patterns" was directionally testable but empirically falsified — the model didn't surface usable cross-asset signal at the per-symbol-LightGBM-on-14-features architecture.

- **OOS MaxDD 49.97% — 2nd consecutive 50%-adjacent breach.** Counter to brief §6.1 risk-management story ("BTC funding stress is a market-wide regime-classifier"). The pattern across iter-v3/023 (49.93%) + iter-v3/024 (49.97%) shows that adding INERT features at n_trials=35 produces deep MaxDD breaches, not just neutral outcomes. The breach magnitude is consistent (within 0.04pp), reinforcing the INERT-OVERFIT mechanism.

- **OOS n_trades=85 < 130 trade-rate floor.** Informational caveat at EXPLORATION single-seed (`feedback_trade_rate_floor_bundle_level.md` — floor applies at CONFIRMATION-bundle level). Below floor at single-seed; mechanism unchanged from prior 5 EXPLORATIONs.

- **Total OOS PnL sign flip from +∼7% (anchor) to −32.10%** — second consecutive catastrophic OOS PnL event. The +7%/−32%/−33% trajectory across anchor/iter-v3/023/iter-v3/024 is the cleanest empirical demonstration of the INERT-OVERFIT mechanism applied to the same feature family.

## Critical Lessons

(a) **Funding family is closed across BOTH per-symbol AND cross-asset variants in v3.** With 3 EXPLORATION data points (iter-v3/019 per-symbol n=10 INERT; iter-v3/023 per-symbol n=35 INERT-CONFIRMED + OOS −1.07; iter-v3/024 BTC cross-asset n=35 INERT-CONFIRMED + OOS −0.82) showing rank 14/14 across 3 of 4 cuts (3 of 4 in iter-v3/024; 4 of 4 in iter-v3/023; 3 of 4 in iter-v3/019), the entire funding feature family is structurally INERT in v3's per-symbol-LightGBM-on-13-features architecture — both for symbol-localized signals and for system-wide stress signals. NO further funding-family EXPLORATION at any trial budget (per `feedback_v3_inert_features_at_higher_budget.md`) and NO consideration in iter-v3/029+ CONFIRMATION bundling. The funding_v3 module + fetch-funding CLI + data/funding_rates/<sym>.csv cache infrastructure stays in repo at zero revert cost; both `funding_rate_zscore_30` and `btc_funding_rate_zscore_30` are DROPPED from V3_FEATURE_COLUMNS at iter-v3/025.

(b) **TRX's mid-rank (9/14) on the cross-asset variant is suggestive but not actionable.** Of the 12 (sym × test) cells in the funding family across v3, TRX/BTC-cross is the only non-bottom-quartile result (rank 9/14, importance=17, ~37% of top vwap_dev_20=46). TRX's positive OOS contribution (+14.31 weighted_pnl, 46.3% WR) is consistent with TRX using the cross-asset signal non-trivially. However, rank 9/14 is still bottom-quartile (Q3 = 64th pctile from top), well below the top-half threshold (≤7) required for PATH A; and the rank-14/14 outcomes on BCH+LDO+Portfolio dominate the portfolio OOS. **Action**: do not pursue funding-as-regime-classifier-for-TRX-only EXPLORATION in this 10-cycle; defer to potential future architecture-axis EXPLORATION (e.g., NEW model family with explicit regime-classifier branch).

(c) **The 13-feature stack appears saturated for direct off-the-shelf feature additions.** Three consecutive EXPLORATIONs (iter-v3/015 microstructure tbr_zscore_30 INERT, iter-v3/019 funding INERT, iter-v3/024 BTC funding INERT) of NEW features each producing rank 14/14 on at least 2 of 3-4 cuts is sufficient evidence that the existing 13-feature LightGBM cannot extract additional signal from raw indicator-style additions. The model is finding stable splits on the existing 13 features (vwap_dev_20 + ret_kurt + max_dd_window + ema_spread + range_realized_vol + skew/kurt/hurst variants + cross_asset_btc_ret variants); new features at the indicator-level do not displace these. **Action**: pivot from off-the-shelf indicator additions to **engineered features** — composed/interaction/regime-conditional features built from existing primitives that the depth-3-5 LightGBM trees cannot compose internally.

(d) **Pre-commit for iter-v3/025: genuine feature engineering pivot per user directive 2026-05-08.** Per Critic FINAL Recommendation of iter-v3/024 (SHA `5a47f5d`) + user directive: drop both funding feature variants from V3_FEATURE_COLUMNS, add ONE engineered feature (single-axis discipline preserved), and test whether the model learns it (rank ≤7 on ≥1 symbol). Candidate axis: `regime_momentum_signed_5d` = `ret_5d × sign(hurst_100 − 0.5)` — flips momentum sign by trend regime. This tests the "model can't compose" hypothesis directly: hurst_100 is rank 8 on BCH (importance=31) and rank 10 on LDO (importance=86); ret_5d derivative is in the existing primitives via fwd_return labeling but not as a feature column. The interaction (regime-conditional momentum) is exactly the kind of composed signal that depth-3-5 LightGBM trees cannot construct from raw inputs at the candidate-split level.

## Pre-Commit for iter-v3/025

Per Critic FINAL Recommendation of iter-v3/024 (SHA `5a47f5d`) + diary lessons (a)-(d) + user directive 2026-05-08:

- **iter-v3/025 axis = `regime_momentum_signed_5d` (genuine feature engineering — composed feature)**.
- **DROP** `btc_funding_rate_zscore_30` from V3_FEATURE_COLUMNS (revert 14 → 13 — entire funding family closed).
- **ADD** `regime_momentum_signed_5d` to V3_FEATURE_COLUMNS (13 → 14 with new engineered feature).
- **Implementation**: new module `engineered_v3.py` (clean separation from off-the-shelf primitives) with `compute_regime_momentum_signed_5d` that consumes existing primitives (5-bar return + hurst_100). New `engineered_v3` GROUP_REGISTRY entry.
- **Verify** ALL components past-only: ret_5d via `.shift(1)`-rooted close diff; hurst_100 already past-only via rolling 100-bar window. Adversarial test required at first commit.
- **ITERATION_LABEL** = "v3-025".
- **NEW memory rule** `feedback_v3_engineered_feature_pivot.md` committed (per lesson (c)+(d)): off-the-shelf indicator additions are saturated at 13-feature stack; future axes must be COMPOSED features built from primitives.
- **Hypothesis**: `regime_momentum_signed_5d` captures interaction effect that depth-5 LightGBM trees cannot compose from raw 13-feature input; expect importance rank ≤10 for ≥1 symbol AND IS Sharpe Δ ≥ +0.10 over anchor.
- **Predicted bands**: IS Sharpe [+0.30, +0.55] median +0.40 (anchor +0.3788); OOS Sharpe [+0.40, +0.65] median +0.50 (anchor +0.3869); single-seed lottery risk same as prior EXPLORATIONs.
- **Three pathways**:
  - **PATH A (PROMISING)**: rank ≤7 for ≥1 symbol AND IS Δ ≥ +0.10 — engineered feature works (signal exists but model couldn't compose internally)
  - **PATH B (PROMISING-INERT)**: rank 14/14 across all → engineered-feature-axis CLOSED for this 13-feature stack at iter-v3/025; pivot to different engineered candidate at iter-v3/026
  - **PATH C (NEGATIVE)**: IS Δ < −0.10 OR OOS Δ < −0.50 — feature actively hurts via expanded overfit space

## Cadence Status

**6 of 10 EXPLORATIONs done in post-bootstrap cycle.** iter-v3/019 (PROMISING-INERT) + iter-v3/020 (NEGATIVE-clean / PATH C) + iter-v3/021 (NEGATIVE-clean) + iter-v3/022 (NEGATIVE-clean / partially-effective-closed) + iter-v3/023 (NEGATIVE-clean / INERT-CONFIRMED + OVERFIT-AT-HIGHER-BUDGET) + iter-v3/024 (NEGATIVE-clean / INERT-OVERFIT-CROSS-ASSET-CONFIRMED) completed; **4 EXPLORATIONs remaining** before next CONFIRMATION (earliest = iter-v3/029).

CONFIRMATION wall-clock cap = 6h (per `feedback_v3_cadence_discipline.md` empirically updated post-iter-v3/018). EXPLORATION wall-clock cap = 2h (iter-v3/024 ran 14 min — well within).

**Funding family (per-symbol + cross-asset BTC) PERMANENTLY CLOSED for v3** — 3 EXPLORATION data points confirm structural INERT in per-symbol-LightGBM-on-13-features architecture.

**iter-v3/025 = genuine feature engineering pivot per user directive 2026-05-08.**

## Reproducibility

- Setup commit SHA: `b28db27` (feat: btc_funding_rate_zscore_30 cross-asset; DROP per-sym + ADD BTC broadcast)
- EDA SHA: `afdb8bc` (analysis/iteration_v3-024/btc_funding_eda.py + 5 CSV outputs + synthesis.md)
- Phase 5.5 gate SHA: `4a50c5c` (PASS)
- Brief SHA: `c1c2f15`
- Engineering report + Critic FINAL SHA: `5a47f5d` (combined commit — engineering report + review.md)
- HEAD SHA at backtest run: `b28db27`
- Reports: `reports-v3/iteration_v3-024/comparison.csv` (single-seed EXPLORATION row), `reports-v3/iteration_v3-024/dsr.json` (DSR=3.25e-06 / PBO=0.0843 / PSR=0.0000 / n_trials=105 / n_eff=19), `reports-v3/iteration_v3-024/in_sample/model_importance_last_month_*.csv` (BCH 14/14, LDO 14/14, TRX 9/14, Portfolio 14/14), `reports-v3/iteration_v3-024/seed_summary.json`, `reports-v3/iteration_v3-024/pareto_front.csv`, `reports-v3/iteration_v3-024/ic_matrix.csv`, `reports-v3/iteration_v3-024/adf_test.csv`
- No tag (NEGATIVE-clean — funding family PERMANENTLY CLOSED for v3; not a baseline-update event)
