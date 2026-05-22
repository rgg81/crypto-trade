# Iteration iter-v3/023 — Diary

## Decision: EXPLORATION-NEGATIVE (clean) — INERT-CONFIRMED + OVERFIT-AT-HIGHER-BUDGET

The funding_rate_zscore_30 retest at n_trials=35 (vs iter-v3/019's n_trials=10) achieved its primary mission — disambiguation of the iter-v3/019 PROMISING-INERT classification — and produced an unambiguous **INERT-CONFIRMED** verdict with an OOS overfit collapse footnote. Importance rank is **14/14 (LDO + TRX + Portfolio) and 13/14 (BCH)** at the higher Optuna budget — strictly worse than iter-v3/019's 14/14 (LDO + TRX + Portfolio) + 10/14 (BCH). The 3.5× larger trial budget did NOT lift funding feature importance; the model demonstrably does not split on it meaningfully across any of the 3 per-symbol architectures. **Funding axis is now permanently CLOSED in v3** (combination of iter-v3/019 + iter-v3/023 produces a 2-data-point structural verdict — NO budget can rescue this feature for the per-symbol-LightGBM-on-13-features architecture).

The OOS Sharpe **−1.0706** is the **worst single-seed OOS in v3 catalog history** (Δ −1.46 vs anchor +0.3869; previous worst was iter-v3/021 at −0.83 Δ vs anchor; iter-v3/016 XGBoost at −2.53 Δ on a different baseline level). OOS MaxDD **49.93%** is the first 50% breach in v3. The IS Sharpe lift +0.15 (Δ vs anchor +0.3788; observed +0.5270) is at the lower edge of the predicted [+0.40, +0.70] band, BELOW the median +0.50 — but the OOS collapse is decisive. Methodology of the run is clean — all 12 standard methodology checks PASS (Critic FINAL `c4574af`); the verdict reflects the AXIS performance, not a methodology defect.

NOT a CONFIRMATION-bundle candidate. The funding feature family axis is **PERMANENTLY-CLOSED for v3** at the catalog level — the structural-INERT prior is now confirmed by 2 EXPLORATION data points. Cadence #5 of 10 in the post-bootstrap cycle.

## What Was Tested

**Hypothesis (locked in brief Section 1):** "Adding back `funding_rate_zscore_30` (z-score over rolling 30 funding-cycle window of Binance Futures funding rate) as a 14th feature on top of the iter-v3/018 multi-seed BOOTSTRAP baseline — at the new EXPLORATION default n_trials=35 (vs iter-v3/019's n_trials=10) — will produce **importance rank improvement** (predicted ≤7 for ≥ 1 symbol) AND **IS Sharpe Δ ≥ +0.10** if the feature is genuinely informative and was budget-limited at iter-v3/019. Predicted IS Sharpe band [+0.40, +0.70] median +0.50; predicted OOS Sharpe band [+0.45, +0.70] median +0.55."

**Spec (locked, single-axis variation):**
- V3_FEATURE_COLUMNS_TOP_N RE-ADD `funding_rate_zscore_30` (13 → 14 columns)
- DISABLE regime gate (`enable_regime_gate=False`; was iter-v3/022 axis; code stays in repo)
- ITERATION_LABEL = "v3-023"
- 3-symbol BCH+LDO+TRX universe UNCHANGED
- Other gates BYTE-IDENTICAL to iter-v3/018 anchor (z=2.0, ATR 2.0/1.0, BTC ±15%, ADX=20, Hurst, low-vol, hit-rate disabled)
- per-symbol cap KEPT in repo but DISABLED
- Ran in EXPLORATION mode: --exploration --seeds 1 (1 outer × 1 inner × 35 n_trials × 3 symbols = **105 fits per cell**; colsample_bytree=1.0 hardcoded). 4th EXPLORATION at the n_trials=35 default per `feedback_v3_exploration_n_trials_35.md`.
- Anchor: iter-v3/018 multi-seed mean +0.3788 IS / +0.3869 OOS.

This was iter-v3/023, the **first NEW-feature-family RETEST iteration in v3 catalog** (15 unique axis representations after this iteration; cadence #5 of 10 in the post-bootstrap cycle).

## Headline Numbers

### Single-seed EXPLORATION run (seed 42)

| Metric | iter-v3/018 anchor (multi-seed mean) | iter-v3/019 (n=10 INERT) | iter-v3/023 (n=35 RETEST) | Δ vs anchor |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | +1.156 (lottery-overshoot) | **+0.5270** | **+0.1482** (within predicted [+0.40, +0.70] lower edge) |
| OOS monthly Sharpe | +0.3869 | +0.7847 (lottery-positive) | **−1.0706** | **−1.4575** (BELOW entire predicted [+0.45, +0.70] band; **WORST single-seed OOS in v3**) |
| OOS/IS Sharpe ratio | 1.02 | 0.68 | **−2.03** | sign flip (worst direction) |
| IS n_trades | 172 (mean) | 209 | **195** | within saturation band [129, 215] |
| OOS n_trades | 90.5 (mean) | 91 | **92** | <130 trade-rate floor (informational at EXPLORATION) |
| IS MaxDD | 21.86% (mean) | 22.5% | **20.54%** | within band |
| OOS MaxDD | 27.74% (best seed 42) | 28.1% | **49.93%** | **+22.19pp; FIRST OOS MaxDD > 50% breach in v3** |
| Total OOS PnL | +∼7% (mean) | +13.79% (single-seed=42) | **−33.21%** | sign flip (catastrophic) |
| DSR | 0.0 (n_trials=1500) | +0.0167 (n=10 artifact) | **0.0** | clean honest readout at n_trials=105 |
| **PSR** | 0.9936 | 1.0 (saturated artifact) | **0.0000** | collapsed (consistent with negative observed Sharpe at n_trials=105) |
| PBO mean | 0.0892 | 0.094 | **0.0922** | unchanged (methodology clean) |
| **PBO max** | **1.0 (TRX/2022-Q4)** | 1.0 | 1.0 | unchanged carry-forward |
| n_eff | 25 (CONFIRMATION) | 7 (n=10) | **19** | maintained from iter-v3/020/021/022 (validates n_trials=35 default; consistent regime ×4) |
| n_trials | 1500 (CONFIRMATION) | 30 (n=10 × 3 sym) | **105** (n=35 × 3 sym) | EXPLORATION default |

### funding_rate_zscore_30 importance rank — PRIMARY DISAMBIGUATION METRIC

| Symbol | iter-v3/019 rank (n=10) | iter-v3/023 rank (n=35) | Direction |
|---|---:|---:|---|
| BCH | 10/14 | **13/14** | WORSE (-3 positions) |
| LDO | **14/14** | **14/14** | IDENTICAL bottom rank |
| TRX | **14/14** | **14/14** | IDENTICAL bottom rank |
| Portfolio | **14/14** | **14/14** | IDENTICAL bottom rank |

**Falsifier 4 fires unambiguously**: rank ≤7 (top half) NOT achieved on any symbol at n_trials=35. PATH B (PROMISING-INERT-still) feature-importance condition strictly satisfied on 3 of 3 symbols (LDO + TRX + Portfolio at 14/14; BCH at 13/14 in bottom-quartile). The 3.5× Optuna trial budget produced strictly worse rank on BCH (10 → 13) and unchanged 14/14 elsewhere. **The feature is genuinely uninformative for v3's per-symbol-LightGBM architecture at the 13-feature stack baseline.**

### Per-symbol attribution (single-seed; OOS)

| Symbol | iter-v3/019 OOS PnL | iter-v3/023 OOS PnL | n_trades | WR | Concentration |
|---|---:|---:|---:|---:|---:|
| BCH | +1.45 | **−26.21** (catastrophic) | 36 | 25.0% | 78.93% (largest negative MaxDD driver) |
| LDO | +12.43 (lottery, 75% WR on 12 trades) | **−16.13** | 8 | **12.5%** (catastrophic) | 48.57% |
| TRX | −0.09 | **+9.13** (only positive) | 48 | 37.5% | −27.50% (offsetting) |

**Forensic finding**: BCH OOS collapse at iter-v3/023 (-26.21 vs iter-v3/019's +1.45 = Δ -27.66) is the single largest per-symbol negative move in v3 history. Mechanism: at n_trials=35 the larger Optuna search converged on IS-overfit hyperparams that don't generalize; the INERT 14th feature gives the search additional DoF to overfit. Adding INERT feature to V3_FEATURE_COLUMNS at higher Optuna budget actively HARMS OOS by expanding the search space along an uninformative dimension.

### Saturation falsifier verification (per `feedback_axis_saturation_predictor.md`)

| Predictor | Lower bound | Upper bound | Observed | Triggered? |
|---|---:|---:|---:|---|
| IS trade band (brief §2.3) | 129 | 215 | **195** | NO (within band — axis behavioral effect on trade count is in expected range) |

The saturation predictor passes — the new feature did not behave anomalously at the trade-count level. The iteration's failure mode is OOS overfit, not behavioral-effect saturation. Distinct from iter-v3/021 universe expansion (where the saturation falsifier FIRED at IS=311).

## What Worked

- **Methodology of the run is clean.** All 12 standard methodology checks PASS (Critic FINAL `c4574af`). Look-ahead audit verified by `.shift(1)` past-only construction in `compute_funding_rate_zscore` (preserved unchanged from iter-v3/019). Embargo width REQUIRED_GAP=66=(21+1)×3 unchanged. Reproducibility stamp clean (Setup `f525ea6`, gate `f94ce3e`, brief `04a715d`, EDA inherited from iter-v3/019 `95858cb`). Single-axis discipline preserved: V3_FEATURE_COLUMNS=14 (re-add funding_rate_zscore_30); regime gate disabled; ITERATION_LABEL=v3-023.

- **n_trials=35 EXPLORATION default validates positively at iter-v3/023 (PRELIMINARY-VALIDATED through iteration #4).** n_eff=19 maintained from iter-v3/020/021/022 — consistent regime across 4 EXPLORATIONs. PSR=0.0000 collapses honestly when observed Sharpe is materially negative. DSR=0.0 reflects honest deflation. Wall-clock 14 min (well within 2h cap). Four data points confirm n_trials=35 default operates in the honest deflation regime; the default is now empirically validated for this 3-symbol universe surface.

- **Disambiguation experiment succeeded as a research artifact.** The pre-committed PATH-A/B/C classification table in §2.4 + §4.4 + §11 of the brief produced an unambiguous classification result. The retest pattern itself (re-test PROMISING-INERT axes at higher trial budget) is now empirically tested for the first time in v3 — and it produces a strictly negative outcome. This is a generalizable lesson: INERT features should be DROPPED, not retested.

- **Frozen-baseline pattern confirmed at the +1-feature-column boundary.** Per `feedback_v3_single_seed_frozen_baseline.md`, single-seed=42 BCH/LDO Optuna trajectories were deterministic across iter-v3/020/021/022 at the 13-feature stack. iter-v3/023 changes the loss surface dimensionality (+1 column), and predictably the BCH/LDO trajectories DID shift (BCH: -6.25 → -26.21; LDO: -8.93 → -16.13). The frozen-baseline rule's scope clause ("at the SAME n_trials=35 budget on the SAME 13-column loss surface") is empirically verified — change the column count and the baseline unfreezes.

## What Failed

- **Falsifier 1 (PATH C trigger) fires unambiguously** per brief §4.3: OOS Sharpe Δ -1.46 << -0.10 threshold (anchor +0.3869). The catastrophic OOS collapse is decisive — observed -1.07 vs predicted [+0.45, +0.70] band missed by -1.52 from the lower bound.

- **Falsifier 4 (PATH B PROMISING-INERT-still trigger) ALSO fires** per brief §4.3 (Falsifier 4 / PRIMARY for budget-disambiguation): rank 14/14 across LDO+TRX+Portfolio; BCH 13/14 (bottom-quartile). The feature is INERT at higher budget, confirming iter-v3/019's INERT classification was NOT a budget artifact. Both PATH B + PATH C conditions fire simultaneously — the OOS collapse is the binding constraint; verdict triggers via PATH C OOS-collapse condition + PATH B INERT-CONFIRMED footnote.

- **OOS Sharpe Δ -1.46 (vs anchor) — WORST single-seed OOS in v3 anchor-basis history.** Brief §4.2 predicted OOS Sharpe band [+0.45, +0.70]; observed -1.07 missed the entire band by -1.52 from the lower bound. The QR's reasoning that "higher budget could surface signal" was directionally correct as a falsifiable prediction but the budget-limited hypothesis was empirically falsified. The feature is genuinely structurally INERT in this regime.

- **OOS MaxDD increased +22.19pp** from 27.74% (anchor seed 42 best) to 49.93%. **First OOS MaxDD > 50% breach in v3.** Counter to brief §6.1 risk-management story ("the new funding feature gives derivatives-positioning regime-classifier signal"). Observed: BCH OOS catastrophic collapse at -26.21 (78.93% concentration on a negative MaxDD driver) plus LDO 12.5% WR catastrophe drives OOS MaxDD into v3's deepest territory.

- **OOS n_trades=92 < 130 trade-rate floor.** Informational caveat at EXPLORATION single-seed (`feedback_trade_rate_floor_bundle_level.md` — floor applies at CONFIRMATION-bundle level, not EXPLORATION). Below floor at single-seed; mechanism unchanged from iter-v3/019/020/021/022 baseline.

- **Total OOS PnL sign flip from positive (+13.79% at iter-v3/019) to catastrophic (-33.21% at iter-v3/023).** The +14% / -33% swing on the SAME feature at different trial budgets is the cleanest empirical demonstration of the INERT-OVERFIT mechanism. iter-v3/019's +14% was lottery-positive (Optuna at n_trials=10 lacked search density to fully overfit IS); iter-v3/023's -33% is overfit-negative (Optuna at n_trials=35 had enough density to find IS-overfit hyperparams).

## Critical Lessons

(a) **INERT features actively HARM OOS at higher Optuna trial budgets.** This is the defining lesson of iter-v3/023. The 14th feature (`funding_rate_zscore_30`) carries near-zero feature importance (rank 14/14 across 3 symbols + Portfolio at n_trials=35) yet adding it to V3_FEATURE_COLUMNS at the higher trial budget produces OOS Sharpe -1.07 vs +0.78 at n_trials=10 — a 1.85-unit collapse on the SAME feature. Mechanism: at n=10, Optuna search density is too low to fully explore the 14-feature parameter space, so the INERT feature's coefficient stays near zero by default (de facto unused). At n=35, search reaches IS-optimal trajectories that EXPLICITLY use the INERT feature (overfitting IS noise) — OOS suffers because the IS-overfit doesn't generalize. **Action**: drop INERT features after 1 EXPLORATION verdict; do not retest at higher budget. New memory rule `feedback_v3_inert_features_at_higher_budget.md` codifies this.

(b) **iter-v3/019's +0.78 OOS at single-seed n_trials=10 was lottery-positive, not budget-limited signal.** The retest at n_trials=35 collapsed OOS to -1.07 — a strict 1.85-unit reversal on the SAME feature. This empirically falsifies the "budget-limited" hypothesis: if iter-v3/019's positive OOS were genuinely from the feature being signal-bearing (just under-explored at n=10), higher budget should improve OOS, not collapse it. The lottery-overshoot explanation (`feedback_v3_single_seed_frozen_baseline.md`) is now confirmed for iter-v3/019's headline +0.78 OOS Δ. Future EXPLORATION QRs should NOT anchor predictions to iter-v3/019's headline — anchor to iter-v3/018 multi-seed mean +0.3869.

(c) **Funding feature family is PERMANENTLY CLOSED for v3.** With 2 EXPLORATION data points (iter-v3/019 + iter-v3/023) showing rank 14/14 across LDO+TRX+Portfolio at BOTH n_trials=10 AND n_trials=35, the feature is structurally INERT in the per-symbol-LightGBM-on-13-features architecture. NO further EXPLORATION at higher trial budgets, NO compounding consideration at iter-v3/029+ CONFIRMATION. The funding_v3 module + fetch-funding CLI + data/funding_rates/<sym>.csv cache infrastructure stays in repo at zero revert cost (preserved for any HYPOTHETICAL future re-architecture, e.g., NEW model architecture or NEW labeling), but `funding_rate_zscore_30` is DROPPED from V3_FEATURE_COLUMNS at iter-v3/024 (back to 13).

(d) **Pre-commit for iter-v3/024: btc_funding_rate_zscore_30 (cross-asset funding stress signal) at n_trials=35.** Per Critic FINAL Recommendation #3 of iter-v3/023 (SHA `c4574af`): different mechanism than per-symbol funding (per-symbol was iter-v3/019/023 INERT-CONFIRMED). Hypothesis: BTC funding stress is exogenous to BCH/LDO/TRX-specific funding patterns. As a cross-asset stress signal, it captures market-wide leveraged-position imbalance that the per-symbol funding (intercepted by Optuna at the per-symbol-architecture per-symbol level) couldn't surface. Predicted importance rank improves from 14/14 (per-symbol funding) toward top-half (≤7) for ≥1 symbol IF cross-asset signal is detectable. PATHs: (A) PROMISING — rank ≤7 + IS Δ ≥ +0.10; (B) PROMISING-INERT — rank 14/14 across all → ALL funding-derived axes closed (funding family permanently dead in v3); (C) NEGATIVE — IS Δ < -0.10. Brief §11 in iter-v3/024 will pre-commit the PATH-classification table.

## Pre-Commit for iter-v3/024

Per Critic FINAL Recommendation #3 of iter-v3/023 (SHA `c4574af`) + diary lessons (a)-(d) + new memory rule `feedback_v3_inert_features_at_higher_budget.md`:

- **iter-v3/024 axis = `btc_funding_rate_zscore_30` (cross-asset funding stress signal)**.
- **DROP** per-symbol `funding_rate_zscore_30` from V3_FEATURE_COLUMNS (revert 14 → 13).
- **ADD** `btc_funding_rate_zscore_30` to V3_FEATURE_COLUMNS (13 → 14 with new feature). Cross-asset feature: BTC's funding rate broadcast to all 3 symbols (NOT per-symbol).
- **Implementation**: extend `funding_v3.py` (or new file `cross_funding_v3.py`) with `compute_btc_funding_rate_zscore` that loads BTC funding cache and broadcasts the z-score to per-symbol kline frames.
- **Verify** BTC funding rate cache exists (BTC funding fetched at iter-v3/019 fetcher infrastructure should produce `data/funding_rates/BTCUSDT.csv` if `crypto-trade fetch-funding --symbols BTCUSDT` was run; if not, run that fetch first).
- **ITERATION_LABEL** = "v3-024".
- **NEW memory rule** `feedback_v3_inert_features_at_higher_budget.md` committed (per lesson (a)).
- **Hypothesis**: BTC's funding rate is exogenous to BCH/LDO/TRX patterns. As a cross-asset stress signal, it captures market-wide leveraged-position imbalance that the per-symbol funding (iter-v3/019/023 INERT) couldn't. Predicted importance rank improves from 14/14 (per-symbol funding) toward top-half (≤7) for ≥1 symbol.
- **Predicted bands**: IS Sharpe [+0.30, +0.55] median +0.40; OOS Sharpe [+0.40, +0.65] median +0.50 (anchor +0.3869); single-seed lottery risk same as iter-v3/019.
- **Three pathways**:
  - **PATH A (PROMISING)**: rank ≤7 for ≥1 symbol AND IS Δ ≥ +0.10 → cross-asset signal works
  - **PATH B (PROMISING-INERT)**: rank 14/14 across all → ALL funding-derived axes closed (funding family permanently dead in v3)
  - **PATH C (NEGATIVE)**: IS Δ < -0.10 → cross-asset funding actively hurts

## Cadence Status

**5 of 10 EXPLORATIONs done in post-bootstrap cycle.** iter-v3/019 (PROMISING-INERT) + iter-v3/020 (NEGATIVE-clean / PATH C) + iter-v3/021 (NEGATIVE-clean) + iter-v3/022 (NEGATIVE-clean) + iter-v3/023 (NEGATIVE-clean / INERT-CONFIRMED + OVERFIT-AT-HIGHER-BUDGET) completed; **5 EXPLORATIONs remaining** before next CONFIRMATION (earliest = iter-v3/029).

CONFIRMATION wall-clock cap = 6h (per `feedback_v3_cadence_discipline.md` empirically updated post-iter-v3/018). EXPLORATION wall-clock cap = 2h (iter-v3/023 ran 14 min — well within).

**Funding axis (per-symbol funding_rate_zscore_30) PERMANENTLY CLOSED for v3** at the catalog level — 2 EXPLORATION data points (iter-v3/019 + iter-v3/023) confirm structural INERT in per-symbol-LightGBM-on-13-features architecture.

**iter-v3/024 = btc_funding_rate_zscore_30 cross-asset funding stress signal at n_trials=35.**

## Reproducibility

- Setup commit SHA: `f525ea6` (feat: re-add funding_rate_zscore_30 + disable regime gate + ITERATION_LABEL=v3-023)
- Phase 5.5 gate SHA: `f94ce3e` (PASS)
- Brief SHA: `04a715d`
- EDA carry-forward SHA (from iter-v3/019): `95858cb`
- Engineering report + Critic FINAL SHA: `c4574af` (combined commit)
- HEAD SHA at backtest run: `f525ea6`
- Reports: `reports-v3/iteration_v3-023/comparison.csv` (single-seed EXPLORATION row), `reports-v3/iteration_v3-023/dsr.json` (DSR=0.0 / PBO=0.0922 / PSR=0.0000 / n_trials=105 / n_eff=19), `reports-v3/iteration_v3-023/feature_importance.csv` (funding rank 13/14 BCH; 14/14 LDO+TRX+Portfolio), `reports-v3/iteration_v3-023/seed_summary.json`, `reports-v3/iteration_v3-023/pareto_front.csv`, `reports-v3/iteration_v3-023/ic_matrix.csv`, `reports-v3/iteration_v3-023/adf_test.csv`
- No tag (NEGATIVE-clean — funding axis PERMANENTLY CLOSED for v3; not a baseline-update event)
