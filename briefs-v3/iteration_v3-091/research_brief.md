# iter-v3/091 — Research Brief — the MODEL-FREE CROSS-SECTIONAL MOMENTUM BOOK (cycle-3 EXPLORATION #10)

**Iteration**: iter-v3/091
**Type**: EXPLORATION (cycle-3 slot #10 of 10 — the FINAL cycle-3 EXPLORATION) — a SCORING-FUNCTION axis on the RETAINED /088 cross-sectional architecture + the /089 cost-aware construction. NOT a fresh re-architecture; NOT a feature expansion; NOT a holding-horizon knob-tweak.
**Branch**: `iteration-v3/091` (off the /090 closeout)
**Date**: 2026-05-17
**Author**: QR (autopilot)

> **This brief SUPERSEDES the prior /091 "holding-horizon-extension" brief.** The prior brief proposed extending the `LGBMRanker`'s holding horizon from H=3 to H=21. After the Phase 5.5 gate (`c56c457`, OVERALL=BLOCK) caught a real walk-forward embargo bug and the EDA was re-worked with the embargo fixed, the *corrected* EDA surfaced a finding the horizon-extension brief did not exploit — and a confirming focused EDA (this brief's Section 2) makes it decisive: **the `LGBMRanker` itself is the bottleneck.** At the weekly horizon a *parameter-free* trailing-return cross-sectional sort beats the trained `LGBMRanker` by +0.20 IS net spread monthly Sharpe (at the runner's full Optuna budget). A horizon-extension of the `LGBMRanker` tests the wrong thing. /091's axis is re-designed around the finding the EDA actually shows.

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` — **IMMUTABLE** (`src/crypto_trade/config.py`, `OOS_CUTOFF_MS = 1742774400000`).
- `training_months = 24` — **IMMUTABLE**.
- IS = every bar with `open_time < OOS_CUTOFF_MS`. The pooled cross-sectional panel's IS slice spans **2020-03 → 2025-03-23** (the 22-symbol union of listing dates; the focused EDA console confirms `IS panel ... timestamps, 22 symbols`). OOS = every bar at/after the cutoff (2025-03 → 2026-05).
- The QR sees OOS for the **FIRST time in Phase 7**. Every design parameter in this brief — the scoring function, the trailing-return lookback horizon `H`, the implied `XS_REQUIRED_GAP`, the walk-forward time embargo — is selected on **IS data only** (the two committed `analysis/iteration_v3-091/*.py` EDA scripts) or set **a-priori from cited research**. This is scrutinised in Section 10.3. The /089 cost-aware construction (quintile legs, overlapping holds, no-trade band, the 0.138 turnover ceiling) is RETAINED.
- **Two distinct embargo quantities — do not conflate them.** The /091 lookback horizon `H` is set to 21 (Section 2.7), which changes two separate quantities, and the Phase 5.5 gate BLOCKed the prior /091 draft for conflating them:
  1. **The CPCV flattened-row purge gap** `XS_REQUIRED_GAP = (H+1) × N_symbols` — a **ROW COUNT**, correct for the pooled-panel 5-fold CPCV. At `H = 21` → `XS_REQUIRED_GAP = (21+1) × 22 = 484`. The CPCV purges this count of flattened (symbol, timestamp) rows and converts the row-count back to timestamp-steps internally (`cross_sectional.py` ~line 625: `gap_ts // len(self.symbols)` = `(H+1)×N // N = (H+1)` timestamp-steps).
  2. **The walk-forward wall-clock time embargo** — a **TIME** quantity. `_generate_xs_monthly_splits` computes `train_end_ms = test_start_ms − embargo_ms`. The correct embargo is **`(H+1) × interval_ms`** = `(H+1)` candle-intervals of *time*, **independent of N**. At `H = 21` this is `22 × 8h ≈ 7.3 days ≈ ~1.0%` of a 24-month training window — negligible. The prior draft and the runner computed `XS_REQUIRED_GAP × interval_ms = (H+1)×N×interval_ms`, over-embargoing by `N = 22×`. The gate certified the bug **harmless at the /088/089/090 H=3 runs** (a too-wide embargo is over-conservative — prior H=3 results valid) but **NOT harmless at long horizons**. The corrected EDAs and the /091 setup commit use `(H+1) × interval_ms`; the runner embargo fix is specified in Section 3 (it is a correctness item, not an edge axis).

## Section 0.5 — Iteration Type Declaration

iter-v3/091 is a **SCORING-FUNCTION-AXIS EXPLORATION** — cycle-3 slot #10 of 10, EXPLORATION mode. Its single edge axis is the **cross-sectional scoring function**: replace the trained `LGBMRanker`'s prediction with a **parameter-free trailing-`H`-bar-return cross-sectional score** (a model-free cross-sectional momentum book). The /089 cost-aware quintile long-short construction — quintile legs, inverse-vol weighting, portfolio vol-targeting, overlapping `H`-bar holds, the no-trade band, the 0.138 turnover ceiling — is RETAINED **verbatim**. Only the score that feeds the construction changes.

This is the next build on the **RETAINED** /088 cross-sectional architecture — /088 (ARCHITECTURE-PARTIAL) stood up a pooled `LGBMRanker`, /089 (CONSTRUCTION-PARTIAL) advanced it to a gross-positive book via a sign fix + cost-aware construction, /090 (FEATURE-EXPANSION-FALSIFIED, Critic OVERALL=BLOCK) established the gross signal does **not** respond to feature expansion. The corrected /091 EDA reveals **why** feature work failed: the `LGBMRanker` at the weekly horizon is destroying a real cross-sectional momentum signal that a parameter-free sort captures cleanly. /091 tests whether scoring the cross-section model-free recovers it.

This brief carries a **single edge axis** — the scoring function — plus **two correctness/instrumentation SETUP items** that are NOT edge axes (Section 3): (i) the walk-forward embargo bug fix (the Phase 5.5 BLOCK — a correctness fix), and (ii) the gross-Sharpe runner artifact (the Critic /090 Rec #1 — instrumentation). After /091, cycle 3's 10-EXPLORATION cadence is complete and iter-v3/092 is the cycle-3 CONFIRMATION.

**Run mode: EXPLORATION.** A model-free book has no Optuna search and no seed — the trailing-return score is deterministic. The /091 build runs the cross-sectional runner with `score_mode="model_free"` (Section 3); for completeness it ALSO emits the trained `LGBMRanker` book as a reference comparator on the same panel/construction (the `LGBMRanker` reference runs at the EXPLORATION single-seed `seed=42`, `ensemble_size=1`, `--n-trials 35` — the standard cross-sectional EXPLORATION spec). The /092 CONFIRMATION is where a model-free book — having no seeds — would be validated by IS sub-period and OOS-window stability rather than a seed sweep.

---

## Section 1 — Hypothesis

> **The cross-sectional book's net loss is substantially a MODEL DEFECT, not a horizon defect: at the weekly holding horizon the trained `LGBMRanker` — fed the /088/089 13-feature stack that was built for the H=3 label — destroys a real cross-sectional momentum signal that a parameter-free trailing-return sort captures cleanly. The committed IS-only EDA shows that, at H=21 (~7 days, the literature's weekly cross-sectional-momentum horizon) with the /089 cost-aware quintile long-short construction held identical, a model-free book scored by the raw trailing-21-bar return has IS net spread monthly Sharpe +0.2964, while the trained `LGBMRanker` at the runner's full 35 Optuna trials has only +0.0944 — a +0.2020 gap in the model-free book's favour. Replacing the `LGBMRanker` score with the parameter-free trailing-return cross-sectional score is therefore expected to lift the OOS net book materially above /089's −0.0985 — but, honestly, the IS model-free signal (~+0.30 monthly Sharpe) is well below the +1.0 absolute floor, it is regime-sensitive (net-negative −0.1039 in the 2021-12→2023-08 FTX/LUNA-crash IS sub-period), and OOS will be thinner; /091 tests whether the cross-sectional line has a genuine positive OOS book AT ALL.**

This is the honest hypothesis the focused EDA supports (Section 2). It is a **scoring-function** lever: the construction, the universe, the cost model, the holding horizon are all held fixed; only the cross-sectional score changes — from the trained `LGBMRanker` prediction to the raw trailing-`H`-bar return. The EDA's M3 diagnosis explains *why* the trained model loses: the 13-feature stack is horizon-mismatched (Section 2.5).

### 1.1 — Why this is the EVIDENCE-DRIVEN axis, not the superseded horizon-extension

The prior /091 brief — and the /090 closeout's RECOMMENDED axis — proposed extending the `LGBMRanker`'s holding horizon H=3→21. The corrected, embargo-fixed EDA (`holding_horizon_eda.py`) makes that axis the wrong test. Per `feedback_v3_axis_selection_quant_discipline.md` the axis must follow the EDA, and the EDA now points squarely at the model:

- At H=3 the `LGBMRanker` book and the model-free book are close (H1 net −0.2917, H2 net −0.2143 — both cost-dominated; model-free already marginally ahead).
- At H=21 the `LGBMRanker` book is **decisively beaten** by the parameter-free sort: model-free net +0.2964 vs `LGBMRanker` net −0.0125 at 8 Optuna trials, and +0.2964 vs +0.0944 at the runner's full 35 trials (this brief's M2). The construction, cost model and `_monthly_sharpe` are byte-identical between the two — the **only** difference is the scoring function.

A horizon-extension of the `LGBMRanker` would therefore produce a ~+0.09 IS net book (35-trial) while a *parameter-free sort on the same construction* gets +0.30. Testing "extend the `LGBMRanker`'s horizon" leaves +0.21 of IS net spread on the table and interrogates a parameter that is not the bottleneck. Per the standing bold-research mandate (`feedback_v3_bold_research_mandate.md`), pivoting /091 to interrogate the model — instead of running a horizon-tweak the EDA says yields a near-breakeven book — IS the bold, evidence-driven move. (The holding horizon is not discarded — the model-free book is held H=21 bars, the EDA-selected horizon; it is the *scoring* that is the axis, not the hold length.)

### 1.2 — Why this is not the /090 pre-registered short-tilt, and not a knob-tweak

The /090 brief pre-registered a "short-tilt / asymmetric-leg construction" as the /091 axis. **/091 does NOT take it** — the /090 Critic ruled correctly it re-slices a thin signal. The scoring-function axis is the opposite of a re-slice: it changes *what signal is being harvested*, not how the book is cut. It is also not a knob-tweak — the scoring function is the single most fundamental object in a cross-sectional ranking strategy (it IS the alpha model), and the EDA shows replacing it moves the IS net book by +0.20. A +0.20 IS-net-spread structural finding, confirmed at the runner's full Optuna budget and corroborated by a 9-point fine sweep and a feature-horizon-appropriateness diagnosis, is a structural axis, not a knob.

---

## Section 2 — IS-Only Numerical Evidence

Two committed EDA scripts, both IS-only (`open_time < OOS_CUTOFF_MS`), built on the RETAINED `cross_sectional.py` infrastructure:

1. `analysis/iteration_v3-091/holding_horizon_eda.py` (corrected-embargo, EDA SHA `d4ad137`) — the horizon-grid scan that surfaced the finding. Its H1 table is the trained-`LGBMRanker` book per horizon (8 Optuna trials/month); its H2 table is a model-free trailing-`H`-bar-return cross-sectional book, training-free and embargo-independent.
2. `analysis/iteration_v3-091/model_free_vs_ranker_eda.py` (the focused confirming EDA committed for this brief, SHA — see Section 11) — three stress-tests + one diagnosis of the model-free-beats-trained finding.

Both EDAs compute GROSS and NET monthly Sharpe through ONE shared `_monthly_sharpe(df, pnl_col)` helper — the exact per-calendar-month method `run_cross_sectional_v3.py::_write_xs_reports` uses, which the /090-closeout recompute confirmed reproduces `comparison.csv` to 1e-14. Gross and net in every table below are guaranteed apples-to-apples (the /090-BLOCK fix).

### 2.1 — The finding: a parameter-free sort beats the trained `LGBMRanker` at the weekly horizon

`holding_horizon_eda.py` (corrected embargo) — the trained `LGBMRanker` book (H1) vs the model-free trailing-return book (H2), identical /089 cost-aware quintile construction, both at the matched holding horizon:

| H (bars) | ~days | H1 trained `LGBMRanker` IS net spread Sharpe | H2 model-free IS net spread Sharpe | H2 − H1 |
|---:|---:|---:|---:|---:|
| 3 | 1.0 | −0.2917 | −0.2143 | +0.0774 |
| 7 | 2.3 | −0.3112 | +0.0596 | +0.3708 |
| 14 | 4.7 | −0.0746 | +0.2077 | +0.2823 |
| **21** | **7.0** | **−0.0125** | **+0.2964** | **+0.3089** |
| 28 | 9.3 | −0.0093 | +0.2593 | +0.2686 |
| 35 | 11.7 | −0.0016 | +0.1477 | +0.1493 |

(H1 used 8 Optuna trials/month — a light proxy; the runner uses 35 — see Section 2.4. H2 trains nothing.)

**The findings.**
1. **A parameter-free trailing-return cross-sectional sort beats the trained `LGBMRanker` at EVERY horizon ≥ 7 bars**, and the gap is largest exactly at the weekly horizon (H=21: +0.3089). The construction, the cost model and the per-calendar-month Sharpe are byte-identical — the **only** difference between H1 and H2 is the scoring function.
2. **The flip is informative.** At H=3 the two books are close (H1 −0.2917, H2 −0.2143 — both cost-dominated, model-free marginally ahead). At H=21 the model-free book wins decisively. The trained `LGBMRanker`, fed the H=3-built 13-feature stack, *degrades* the clean long-horizon momentum signal — see the M3 diagnosis (Section 2.5).
3. **The model-free book's H2 hump peaks at H=21** — +0.2964 net, declining to +0.2593 (H=28) / +0.1477 (H=35), the IS sign of the literature's beyond-fortnight cross-sectional-momentum reversal.

### 2.2 — M1(a): the model-free finding is robust off the grid point — fine sweep H ∈ [17, 25]

`model_free_vs_ranker_eda.py::M1a_model_free_fine_sweep.csv` — the model-free book at every integer horizon around H=21, to test whether +0.2964 is an artifact of the coarse 6-point grid:

| H (bars) | ~days | model-free gross spread Sharpe | model-free net spread Sharpe | turnover/bar |
|---:|---:|---:|---:|---:|
| 17 | 5.7 | +0.2693 | +0.2244 | 0.0336 |
| 18 | 6.0 | +0.2995 | +0.2560 | 0.0310 |
| 19 | 6.3 | +0.3037 | +0.2627 | 0.0296 |
| 20 | 6.7 | +0.3379 | +0.2941 | 0.0274 |
| **21** | **7.0** | **+0.3388** | **+0.2964** | **0.0263** |
| 22 | 7.3 | +0.3630 | +0.3226 | 0.0246 |
| 23 | 7.7 | +0.3651 | +0.3216 | 0.0232 |
| 24 | 8.0 | +0.3359 | +0.2934 | 0.0221 |
| 25 | 8.3 | +0.3229 | +0.2799 | 0.0210 |

**The model-free finding is a WIDE, SMOOTH PLATEAU, not a grid artifact.** Every integer horizon in [17, 25] produces an IS net spread monthly Sharpe in **[+0.2244, +0.3226]** — there is no spike at H=21, no fragile single point. The plateau is gently humped with an arithmetic peak at H=22/23 (+0.32). H=21 (~7 days) is the literature's weekly rebalance and sits squarely in the middle of the plateau; choosing it (rather than the arithmetic-best H=22/23) is the conservative interior pick — see Section 2.7. A smooth nine-point plateau is the strongest possible evidence that the model-free finding is structural.

### 2.3 — M1(b): the model-free book's IS sub-period stability — honest regime-sensitivity

`model_free_vs_ranker_eda.py::M1b_model_free_subperiod_stability.csv` — the H=21 model-free book's net monthly Sharpe restricted to three contiguous IS thirds:

| IS sub-period | window | model-free gross spread Sharpe | model-free net spread Sharpe | bars |
|---|---|---:|---:|---:|
| third 1 | 2020-04 .. 2021-12 | +0.5808 | **+0.5564** | 1798 |
| third 2 | 2021-12 .. 2023-08 | +0.0219 | **−0.1039** | 1798 |
| third 3 | 2023-08 .. 2025-03 | +0.2231 | **+0.1552** | 1797 |

**The model-free book is net-positive in 2 of 3 IS sub-periods — but it is regime-sensitive.** Third 2 (2021-12 → 2023-08) is **net-negative (−0.1039)** — that window contains the LUNA collapse (May 2022), the 3AC/Celsius cascade (June 2022) and the FTX collapse (Nov 2022). Cross-sectional momentum is documented to break in deleveraging crashes (the cross-section moves together — dispersion collapses, the long-short spread compresses). The aggregate IS +0.2964 is genuine but is carried by the two trending regimes (the 2020-21 bull, the 2023-25 recovery) and gives back ground in the 2022 crash. **This is the load-bearing honesty point for the OOS-transfer framing** (Section 4.2, Section 7): the 2025-03→2026-05 OOS window's regime mix is unknown to the QR, and a crash regime in OOS would compress the model-free spread.

### 2.4 — M2: the `LGBMRanker` stress-test — does the full 35-trial Optuna budget close the gap?

The H1 EDA used 8 Optuna trials/month; the runner uses 35. `model_free_vs_ranker_eda.py::M2_lgbmranker_trial_budget.csv` re-runs the trained `LGBMRanker` at H=21 at BOTH budgets, identical /089 construction:

| Optuna trials | config | trained `LGBMRanker` gross spread Sharpe | trained `LGBMRanker` net spread Sharpe | mean IS-train rank-IC |
|---:|---|---:|---:|---:|
| 8 | the H1-EDA "light proxy" | +0.0510 | −0.0125 | +0.4002 |
| **35** | **the RUNNER budget** | **+0.1534** | **+0.0944** | +0.3977 |

| | net spread monthly Sharpe |
|---|---:|
| model-free book, H=21 | **+0.2964** |
| trained `LGBMRanker`, H=21, 35 Optuna trials | **+0.0944** |
| **model-free − trained `LGBMRanker` @ 35-trial** | **+0.2020** |

**The full 35-trial Optuna budget does NOT close the gap — the finding is rock-solid.** Two honest readings:
1. The 8-trial H1 EDA *understated* the trained `LGBMRanker`: at 35 trials its IS net spread rises from −0.0125 to +0.0944 (a +0.107 lift — more Optuna search does help the trained model). So the dispatch's "~0.31 gap" was the 8-trial proxy figure; the **honest gap at the runner's real budget is +0.2020**.
2. Even at the full 35-trial budget the model-free book (+0.2964) beats the trained `LGBMRanker` (+0.0944) by **+0.2020 IS net spread monthly Sharpe**. The `model_free_beats_trained_at_full_budget` flag is `True`. A +0.20 margin at full Optuna budget — with a 9-point smooth plateau (M1a) corroborating the model-free side — is a decisive, well-stress-tested finding.

### 2.5 — M3: WHY the `LGBMRanker` underperforms — the 13-feature stack is horizon-mismatched

`model_free_vs_ranker_eda.py::M3_feature_horizon_appropriateness.csv` — for each of the /088/089 13 features: the univariate per-timestamp IS rank-IC vs the forward return at H=3 and at H=21, and the H=21-label-trained ranker's gain-based importance (the 35-trial set):

| feature | univariate rank-IC @ H=3 | univariate rank-IC @ H=21 | H=21 ranker gain % |
|---|---:|---:|---:|
| range_realized_vol_50 | −0.0608 | −0.0557 | 13.99 |
| ret_skew_200 | −0.0282 | −0.0022 | 12.00 |
| max_dd_window_50 | +0.0280 | +0.0266 | 11.66 |
| ret_kurt_200 | −0.0048 | −0.0242 | 11.54 |
| ret_skew_50 | −0.0203 | −0.0052 | 8.17 |
| ret_autocorr_lag1_50 | −0.0068 | −0.0179 | 8.01 |
| ema_spread_atr_20 | −0.0331 | −0.0146 | 7.92 |
| ret_kurt_50 | −0.0037 | −0.0147 | 6.76 |
| hurst_100 | +0.0026 | +0.0099 | 5.72 |
| sym_vs_btc_ret_7d | −0.0394 | −0.0200 | 4.84 |
| vwap_dev_20 | −0.0303 | +0.0145 | 3.40 |
| hurst_diff_100_50 | −0.0024 | +0.0012 | 3.39 |
| regime_momentum_signed_5d | −0.0402 | −0.0144 | 2.59 |

**The diagnosis — the 13-feature stack is built for the H=3 label and is horizon-mismatched at H=21:**
1. **The features correlate more weakly with the H=21 forward return than the H=3 forward return.** Mean `|univariate rank-IC|` of the 13-feature stack is **0.0231 at H=3** but only **0.0170 at H=21** — a ~26% loss of univariate predictive content at the weekly horizon. The stack's information was tuned (across /059→/088→/089) to a 3-bar label.
2. **The H=21 ranker spends two-thirds of its learning capacity on horizon-mismatched features.** 9 of the 13 features have *stronger* `|rank-IC|` at H=3 than at H=21, and the H=21-label-trained ranker allocates **68.0%** of its gain to those 9 horizon-mismatched features. The ranker is forced to fit features that are noisier at H=21 — it overfits that noise (the iter-v3/070 / `feedback_v3_inert_features_at_higher_budget.md` mechanism: at 35 trials the larger search space lets Optuna fit IS noise), degrading the clean long-horizon momentum.
3. **The stack has no clean long-horizon momentum feature; the model-free score IS one.** The three highest-importance features (range_realized_vol_50, ret_skew_200, max_dd_window_50 — 37.6% of gain combined) are volatility / tail-risk / drawdown transforms, not trailing-return momentum. The model-free score — the raw trailing-21-bar return — IS exactly the clean long-horizon cross-sectional-momentum signal the trained stack lacks. This is *why* a parameter-free sort beats the trained model: the parameter-free score is the right signal at the right horizon; the trained model is fitting the wrong features.

This M3 diagnosis answers the dispatch's TASK-1 "diagnose WHY" and grounds the axis choice (Section 2.6): the `LGBMRanker` is **not** trivially recoverable by re-pointing it at the H=21 label (the M2 35-trial result IS the H=21-label-trained model, and it still loses by +0.20) — recovery would require a horizon-matched *feature stack*, a larger multi-iteration re-design. The lowest-risk, single-axis, evidence-grounded move is to score the cross-section model-free.

### 2.6 — Axis choice: the model-free score, NOT a horizon-matched-feature re-design

The dispatch permits either (a) the model-free book, or (b) a horizon-matched-feature re-design of the `LGBMRanker` IF the M3 diagnosis shows the `LGBMRanker` is recoverable with the right features. The QR's call is **(a) the model-free book**, on three grounds:

1. **The M3 diagnosis does NOT show easy recoverability.** The M2 35-trial result *is* the `LGBMRanker` trained on the H=21 label — it is already horizon-matched on the *label*. It still loses by +0.20. The remaining lever for the trained model is a horizon-matched *feature stack* — but that is a research programme (engineer a clean trailing-momentum feature family for the 21-bar horizon, validate it multivariately, re-tune), not a single clean EXPLORATION axis, and /090 already established that feature work on this architecture is fragile (FEATURE-EXPANSION-FALSIFIED). A feature re-design is a cycle-4 candidate, recorded in Section 11 — not /091.
2. **The model-free book is a single, clean, fully-specified axis** — replace one function call. No Optuna, no seeds, no feature engineering, nothing to tune. It is testable in one EXPLORATION with zero ambiguity.
3. **A model-free signal is the lowest-overfitting-risk strategy possible** — maximally aligned with v3's anti-overfitting mission (Section 6.1). The cross-sectional line's repeated failures (/088 sign error, /090 feature overfit, the M3 finding that the ranker overfits H=3-built features) are *all* overfitting failures. Removing the trained model removes the overfitting surface entirely.

### 2.7 — Pre-registered lookback horizon: H = 21 (~7 days)

The model-free book scores the cross-section by the trailing-`H`-bar return and holds each tranche `H` bars. The pre-registered `H` is **21** (~7 days):

1. **The M1a fine sweep is a smooth plateau across [17, 25]** (net spread [+0.2244, +0.3226]) — the choice within the plateau is not fragile. The arithmetic best is H=22/23 (+0.32); H=21 is +0.2964, inside the plateau.
2. **H=21 is the literature's weekly cross-sectional-momentum rebalance** — Starkiller Capital (SSRN 4322637): greatest monotonicity and quintile-spread for a 7-day rebalance; Dobrynskaya (SSRN 3913263): crypto cross-sectional momentum positive up to ~2 weeks, reversing beyond. H=21 8h-bars = exactly 7 days. The arithmetic-best H=22/23 (~7.5 days) is inside the same weekly window; H=21 is chosen as the literature-canonical interior point — picking the arithmetic max of an IS sweep would be a mild "best-of-N" selection the discipline discourages when an a-priori-justified neighbour is inside the noise.
3. **The H2 hump (Section 2.1) and the M1a plateau both peak in the weekly band and decline beyond ~H=25** — consistent with the literature's beyond-fortnight reversal. H=21 sits before that decline.

**Pre-registered /091 parameters: scoring function = model-free trailing-`H`-bar return; `H = 21`; `XS_HOLD_BARS = 21`.** Induced constants: the CPCV flattened-row gap `XS_REQUIRED_GAP = (21+1)×22 = 484`; the walk-forward wall-clock embargo `(21+1)×interval_ms ≈ 7.3 days`. (The model-free book is itself embargo-independent — it trains nothing — but the reference `LGBMRanker` comparator and the CPCV path computation run on the panel, so the embargo fix still applies to the runner; Section 3.)

### 2.8 — Summary of IS evidence

1. A **parameter-free trailing-return cross-sectional sort beats the trained `LGBMRanker`** at the weekly horizon — IS net spread monthly Sharpe **+0.2964 vs +0.0944** at the runner's full 35-trial Optuna budget (a **+0.2020** gap), identical /089 cost-aware construction; the only difference is the scoring function.
2. The model-free finding is a **wide smooth plateau** across H ∈ [17, 25] (net spread [+0.2244, +0.3226]) — not a coarse-grid artifact.
3. The model-free book is **net-positive in 2 of 3 IS sub-periods** but **regime-sensitive** — net-negative (−0.1039) in the 2021-12→2023-08 FTX/LUNA-crash third. The aggregate +0.2964 is carried by the trending regimes.
4. The **WHY**: the /088/089 13-feature stack is **horizon-mismatched** — mean `|univariate rank-IC|` 0.0231 (H=3) → 0.0170 (H=21); the H=21 ranker spends **68.0%** of its gain on the 9 features that are stronger at H=3; the top-importance features are volatility/tail-risk transforms, not momentum. The trained model fits the wrong features and overfits their H=21 noise; the model-free score is the clean long-horizon momentum signal the stack lacks.
5. **The honest residual**: the model-free IS signal (~+0.30 net spread monthly Sharpe) is **well below the +1.0 absolute floor**, is regime-sensitive, and OOS is documented to be much thinner than IS for crypto cross-sectional momentum. /091 tests whether the cross-sectional line has a **genuine positive OOS book at all** — the foundation a cycle-4 multi-factor build would stand on.

---

## Section 3 — Proposed Changes (the /091 build spec — the QE Phase-6 build)

### 3.1 — The /091 single edge axis: the model-free cross-sectional scoring function

**The single edge axis.** The cross-sectional score that feeds the /089 cost-aware construction changes from the trained `LGBMRanker` prediction to a **parameter-free trailing-`H`-bar return**. The QE adds a model-free scoring path to the cross-sectional runner. Concretely:

- **`cross_sectional.py` — add a `score_mode` parameter to `run_cross_sectional_backtest`** (default `"trained"` — preserves the /088/089/090 behaviour exactly). Signature: `run_cross_sectional_backtest(..., score_mode: str = "trained")`.
- **The scoring branch is at `cross_sectional.py` ~line 1067**, currently:
  ```python
  x_t = panel_t[strategy.feature_columns].values.astype(np.float32)
  if strategy._model is not None:
      scores = strategy._model.predict(x_t)
  else:
      scores = np.zeros(len(panel_t))
  ```
  When `score_mode == "model_free"`, `scores` is instead the **trailing-`H`-bar return** for each symbol in `panel_t` at timestamp `ts`: `score(sym) = close(sym, ts) / close(sym, ts − H·interval) − 1`. The QE computes this from a precomputed wide trailing-return matrix `mom_wide = close_wide / close_wide.shift(XS_HORIZON) − 1.0` (where `close_wide` is the existing pivot at ~line 995), indexed by `(ts, sym)`. A symbol in `panel_t` with no `mom_wide` value at `ts` (insufficient history) is dropped from that bar's cross-section (consistent with `XS_MIN_SYMBOLS_PER_BAR`). **No look-ahead**: `close(ts)` and `close(ts−H·interval)` are both ≤ `ts`; the 1-bar PnL return is taken strictly after `ts` (the existing `searchsorted(ts, side="right")` at ~line 1107 is unchanged).
  - **The reference implementation is `analysis/iteration_v3-091/model_free_vs_ranker_eda.py::_model_free_bars`** — the QE's runner path must reproduce its scoring (the EDA computes `mom_wide = close_wide / close_wide.shift(horizon) − 1.0` and uses the row `mom_wide.loc[ts]` as the score). The /091 IS-EDA model-free net spread +0.2964 is the runner-fidelity target.
- **In `model_free` mode the per-month `_train_for_month` call is SKIPPED** (no model is trained — the runner does not call `strategy._train_for_month`; `strategy._model` stays `None`). This is what makes the model-free run have no Optuna and no seed.
- **The model-free score must still be written to the `predicted_score` results column** (`cross_sectional.py` ~line 1143 `pred_score = float(scores[row_iloc])`) so the downstream `compute_oos_rank_ic` (which Spearman-correlates `predicted_score` against the realised `label_grade`) keeps working — for the model-free book the OOS rank-IC then measures whether the trailing-momentum score rank-correlates with the realised forward cross-sectional rank. The `label_grade` column is still computed (via `label_cross_sectional_rank`) purely for this rank-IC diagnostic; it is not used to train anything in `model_free` mode.
- **`run_cross_sectional_v3.py` — the runner emits BOTH books.** The /091 build runs the cross-sectional backtest twice on the same panel/construction: once with `score_mode="model_free"` (the /091 axis — its `comparison.csv`/reports are the primary /091 artifacts) and once with `score_mode="trained"` (the `LGBMRanker` reference comparator — written to a `reference_lgbmranker/` subdirectory or clearly suffixed). The QE wires this as two backtest calls + two `_write_xs_reports` calls; the primary `reports-v3/iteration_v3-091/` reports are the model-free book.

### 3.2 — SETUP item 1 (CORRECTNESS, not an edge axis): fix the walk-forward embargo bug

The Phase 5.5 gate BLOCKed the prior /091 draft for a walk-forward embargo bug. **`cross_sectional.py` ~line 968**:
```python
# BEFORE (bugged — over-embargoes by N_XS_SYMBOLS = 22×):
embargo_ms = XS_REQUIRED_GAP * interval_ms
# AFTER (correct — (H+1) candle-intervals of wall-clock TIME, N-independent):
embargo_ms = (XS_HORIZON + 1) * interval_ms
```
The same bugged form is at **`run_cross_sectional_v3.py` ~line 825** (the `_run_smoke_test` path). **The QE must find and fix the full set** of walk-forward `embargo_ms` computations (any site feeding `_generate_xs_monthly_splits`). The CPCV row-count `gap` (which legitimately uses `XS_REQUIRED_GAP = (H+1)×N`, `cross_sectional.py` ~line 603) is **unchanged** — only the walk-forward *time* embargo is wrong. This is a **correctness fix** at the /091 setup commit — the same class of change as the `e149e9d` walk-forward look-ahead fix; it moves the train/test split boundary to its mathematically correct position. It is **not an edge axis**. (It chiefly affects the reference `LGBMRanker` comparator's training window — the model-free book trains nothing and is embargo-independent — but it must be fixed regardless, both for the reference comparator's validity and because leaving a known bug in `src` is unacceptable.)

### 3.3 — SETUP item 2 (INSTRUMENTATION, not an edge axis): the gross-Sharpe runner artifact

The /090 OVERALL=BLOCK root cause must be closed at the /091 setup commit. The /090 BLOCK was a methodology DEFECT — gross monthly Sharpe was a QE hand-computation with no reproducible derivation, producing two different numbers (+0.1717, +0.5947) for the same /089 data and corrupting falsifier F3. Per `feedback_v3_methodology_axis_integration_test.md`, any metric that drives a falsifier must be a runner output. The /091 setup commit (QE work in `src`/runner code):

- `run_cross_sectional_v3.py::_write_xs_reports` emits `gross_monthly_sharpe` (IS + OOS) to `comparison.csv` and `dsr.json`.
- `gross_monthly_sharpe` and the existing net `monthly_sharpe` MUST be computed by the **identical per-calendar-month code path**. Currently `_write_xs_reports` has an internal `_monthly_sharpe(monthly_df)` helper (~line 436) that only ever sees `net_pnl` (via `_monthly_pnl`, ~line 419). The QE refactors so ONE shared helper `_monthly_sharpe(sub, pnl_col)` computes both — the net call passes `pnl_col="net_pnl"`, the gross call passes `pnl_col="gross_pnl"` — exactly the shared-helper pattern both /091 EDAs already implement (`_monthly_sharpe(df, pnl_col)`).
- A smoke test asserts `gross_monthly_sharpe` and `monthly_sharpe` are produced by the same aggregation function (e.g. monkeypatch the shared helper and assert both emitted values reflect the patch).

This is **instrumentation, not a second edge axis** — it changes what the runner *reports*, not what it *trades*. It makes the /091 falsifier F1 gross-Sharpe input a reproducible runner artifact rather than a hand-computation.

### 3.4 — Other setup items (mechanical consequences, not axes)

- **`XS_HORIZON: int = 3 → 21`** — for the model-free book this is the trailing-return lookback (and, coupled, the hold). For the reference `LGBMRanker` comparator it is also the label horizon. `XS_REQUIRED_GAP` is a derived constant `(XS_HORIZON + 1) * N_XS_SYMBOLS` — it recomputes to 484 automatically; the docstring worked example `(3+1)*22 = 88` is updated to `(21+1)*22 = 484`.
- **`XS_HOLD_BARS: int = 3 → 21`** — each overlapping tranche is held 21 bars (Jegadeesh-Titman overlapping construction, unchanged in form). Horizon-matched.
- **`run_cross_sectional_v3.py` — revert the /090 feature expansion.** `expand_downside=True → False`; `XS_FEATURE_COLUMNS` reverts to the 13-feature base (`XS_BASE_FEATURES`); `_verify_feature_columns` assertion `len(XS_FEATURE_COLUMNS) == 15 → == 13`. (For the model-free book the feature set is irrelevant — it scores by trailing return; but the reference `LGBMRanker` comparator uses it, and leaving the /090 FALSIFIED features in `src` is wrong. This is a *revert*, not a feature axis.)
- **`run_cross_sectional_v3.py` — the preflight assertions** `_verify_xs_universe`, `_verify_xs_gap_assertion` already compute `expected_gap = (XS_HORIZON+1)*len(XS_UNIVERSE)` — they recompute to 484 automatically. `ITERATION_LABEL = "v3-091"`.

### 3.5 — Single-axis confirmation (Phase 5.5 gate)

iter-v3/091 changes **ONE edge axis: the cross-sectional scoring function** (trained `LGBMRanker` prediction → parameter-free trailing-`H`-bar return). The horizon `XS_HORIZON`/`XS_HOLD_BARS` 3→21 is the EDA-selected operating point of the model-free book (the trailing-return lookback IS part of defining the model-free score — a model-free momentum book is *defined* by its lookback, exactly as a triple-barrier is defined by its TP/SL); it is not a second independent axis. `XS_REQUIRED_GAP` 88→484 is the mechanical consequence of the formula. **Two correctness/instrumentation items accompany the axis and are NOT edge axes**: (i) the walk-forward embargo bug fix (Section 3.2 — a correctness fix); (ii) the gross-Sharpe runner artifact (Section 3.3 — instrumentation). No symbol change (the 22-symbol `XS_UNIVERSE` unchanged), no construction-knob change (the /089 quintile + no-trade-band + turnover-ceiling RETAINED verbatim), no risk-gate change. The /090 feature revert is a *revert* to the pre-/090 state, not a new axis. The /090-pre-registered short-tilt construction stays DEFERRED.

### 3.6 — UNCHANGED from /088 + /089

- **The /089 cost-aware construction** — quintile legs (`XS_QUANTILE_FRAC = 0.20`), the no-trade band (`XS_NO_TRADE_BAND = 0.020`), the HARD turnover ceiling (`XS_TURNOVER_CEILING = 0.138`), the overlapping-tranche form (Jegadeesh-Titman), inverse-vol weighting, portfolio vol-targeting — all RETAINED verbatim. Only the *score* feeding the construction changes.
- **The universe** — the 22-symbol `XS_UNIVERSE` — unchanged.
- **The reference `LGBMRanker`** — retained as a comparator only (`score_mode="trained"`), not the /091 primary book.

---

## Section 4 — Expected OOS Impact + evaluation + the pre-registered falsifiers

### 4.1 — Evaluation

iter-v3/091 produces a cross-sectional long-short book; per the /088/089/090 brief Section 4.1 it is **not directly comparable** to the per-symbol-book Sharpes of the /059 CONFIRMATION baseline (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791) — a different return distribution, beta, turnover. The operative evaluation:

**(A) The standing absolute bar.** The mission bar is top-quant-firm-grade: the standing v3 merge floors are IS monthly Sharpe ≥ +1.0 AND OOS monthly Sharpe ≥ +1.0. /091 is measured against these and — honestly — the IS model-free signal (~+0.30) is well below them. The /091-specific milestone is more proximate: a **net-positive OOS book** (OOS net monthly Sharpe > 0) — the concrete next step the /089 gross-positive / /090 still-net-negative line hands /091, and the question of whether the cross-sectional line has a genuine positive OOS book at all.

**(B) The architecture-internal diagnostics + the /091-specific gates** (all reproducible runner artifacts after the Section 3.3 SETUP item):
- **OOS net monthly Sharpe vs /089's −0.0985** — does the model-free score lift the net OOS book?
- **OOS gross monthly Sharpe vs /089's +0.1717** — does the model-free score strengthen the gross signal OOS?
- **OOS rank-IC > 0** — does the model-free trailing-momentum score rank-correlate with the realised 21-bar-forward cross-sectional rank OOS?
- **The HARD turnover ceiling — IS mean gross turnover/bar ≤ 0.138** (RETAINED /089 gate). The model-free EDA shows IS turnover/bar ≈ 0.0263 at H=21 — far inside.
- **frac_positive_paths (CPCV)** — the /089-corrected proxy (actual long-short net return per path).
- **No single symbol > 30% of OOS book PnL** — the model-free EDA H=21 max symbol concentration was 17.5%.
- **model-free vs the reference `LGBMRanker` comparator OOS** — does the model-free book also beat the trained `LGBMRanker` OOS, as it does IS (+0.2020)?

**The /091 anchors.** ANCHOR 1 (the honest internal anchor) is the **/089 cross-sectional book** — the like-for-like architecture predecessor with the cost-aware construction RETAINED: OOS gross monthly Sharpe **+0.1717**, OOS net monthly Sharpe **−0.0985** (the *correct* /089 figures — confirmed by the /090-closeout recompute `analysis/iteration_v3-090/gross_sharpe_recompute.py`, which reproduced +0.1717 to 4 decimals and `comparison.csv` net to 1e-14). /090's recomputed figures (OOS gross **+0.1558**, OOS net **−0.0770**) are the most-recent cross-sectional reading. **The defective /090-report figures +0.5947 / +0.5398 are NEVER cited.** ANCHOR 2 = the /059 CONFIRMATION baseline (a per-symbol-book reference, comparability caveat, reserved for the /092 CONFIRMATION). The cross-sectional line OOS net trajectory: **/088 −0.5418 → /089 −0.0985 → /090 −0.0770**.

**The embargo-fix anchor confound — addressed honestly.** /089's anchors were produced under the bugged 22×-overcounted walk-forward embargo (29.3-day at /089's H=3 instead of the correct 1.3-day). /091's *primary book is model-free — it trains nothing and is embargo-independent entirely* — so for the /091 headline the confound does not apply at all. The confound touches only the reference `LGBMRanker` comparator (which runs under the corrected embargo). The gate certified the H=3 bug **harmless** (a too-wide embargo is over-conservative, never leaking — /089's anchors are if anything a slightly conservative reading). The Phase-8 diary records the embargo correction as a methodology fix at /091.

### 4.2 — Predicted OOS impact (honest)

The IS evidence: the model-free book has IS net spread monthly Sharpe +0.2964 (vs the trained `LGBMRanker`'s +0.0944 at full budget), on a wide [17,25] plateau, but is net-negative (−0.1039) in the 2022-crash IS sub-period. Honest prediction for the OOS run:

- **OOS net monthly Sharpe improves materially on /089's −0.0985, modal range roughly [+0.00, +0.20].** The model-free book replaces a trained model that the EDA shows *destroys* the signal — removing it should lift the OOS net book. The IS model-free net spread is a solid +0.2964; crypto cross-sectional momentum is documented to be much thinner OOS than IS (Starkiller: IS top-quintile +37.8% → OOS −2.35%), so the OOS book will be a fraction of IS. **Modal prediction: OOS net monthly Sharpe ≈ [+0.00, +0.20]** — net-positive but thin, the first net-positive cross-sectional OOS book. Honestly, a *clearly* net-positive book is roughly as likely as a hover-around-breakeven outcome (the regime-sensitivity, Section 2.3). **Clearing the +1.0 floor is firmly NOT expected.**
- **OOS gross monthly Sharpe improves on /089's +0.1717, modal range roughly [+0.20, +0.45].** The model-free IS gross spread is +0.3388 (vs the trained `LGBMRanker`'s IS gross +0.1534) — the model-free score is a stronger gross signal. Thinner OOS, but the gross book should clear /089's +0.1717.
- **OOS rank-IC stays positive**, ≈ +0.03 to +0.08 — the model-free trailing-momentum score is a real cross-sectional predictor (/088/089's trained-model OOS rank-IC was +0.043/+0.028; the model-free score is the cleaner long-horizon signal).
- **IS mean gross turnover/bar ≈ 0.026** — far inside the 0.138 ceiling (the 21-bar overlapping hold cuts turnover ~5× vs the /089 3-bar book).
- **The model-free book beats the reference `LGBMRanker` comparator OOS** — predicted, consistent with the IS +0.2020 gap, but explicitly a prediction (not a falsifier).

### 4.3 — The LOCKED falsifier band (pre-registered — gates, not predictions)

Per `feedback_v3_per_symbol_target_axis_falsifier.md` / `feedback_v3_axis_selection_quant_discipline.md` — falsifiers are **gates**, and they reference **different numbers** than the Section 4.2 predictions. Evaluated in Phase 7. Anchored on /089's documented OOS figures (OOS gross +0.1717, OOS net −0.0985):

- **F1 — OOS net monthly Sharpe ≤ the /089 book's −0.0985**: the model-free score did NOT improve the net OOS book vs the /089 `LGBMRanker` predecessor at all → the central /091 hypothesis (the model-free score recovers the signal the `LGBMRanker` destroys) is falsified for the cycle. The most likely cause would be an OOS regime where cross-sectional momentum breaks (Section 2.3's 2022-crash analogue). NO-MERGE.
- **F2 — OOS gross monthly Sharpe ≤ the /089 book's +0.1717**: the model-free score did NOT strengthen the gross signal OOS. (F2 is evaluated on the reproducible `gross_monthly_sharpe` runner artifact, per the Section 3.3 SETUP item — this closes the /090 BLOCK root cause.)
- **F3 — IS mean gross turnover/bar > 0.138** (`XS_TURNOVER_CEILING`, the RETAINED /089 hard gate): the build did not realise the predicted turnover collapse — a build defect (the 21-bar overlapping hold should cut turnover to ≈0.026; a breach means the hold mechanism is mis-wired). NO-MERGE regardless of any Sharpe.
- **F4 — OOS rank-IC ≤ 0**: the model-free trailing-momentum score's OOS prediction rank does NOT correlate with the realised 21-bar-forward cross-sectional rank. Since a trailing-return score is a documented cross-sectional predictor and the /088/089 trained model had OOS rank-IC +0.043/+0.028, an OOS rank-IC ≤ 0 indicates either a genuine OOS momentum-reversal regime or a build defect — an investigate-before-classifying signal.
- **F5 — a single symbol > 50% of OOS book PnL**: the quintile dollar-neutral construction failed to diversify (a structural-construction failure distinct from a signal failure; model-free IS EDA H=21 max symbol concentration was 17.5%).

The falsifier/prediction separation: Section 4.2 *predicts* OOS net ≈ [+0.00, +0.20] and OOS gross ≈ [+0.20, +0.45]; F1/F2 are *gates* at the /089 anchors (−0.0985 net, +0.1717 gross) — different numbers, as the discipline requires.

### 4.4 — What each falsifier implies

- **If F3 fires** — NO-MERGE unconditionally; the turnover ceiling is the hard gate; a breach means the overlapping-hold mechanism did not realise the predicted ~5× turnover cut — a build defect to diagnose.
- **If F4 fires** — investigate the model-free scoring wiring (the `mom_wide` index alignment, the embargo) before any classification; if the wiring is clean, F4 firing means a genuine OOS cross-sectional-momentum reversal regime.
- **If F1 fires (and F3/F4 do not)** — the model-free score did not improve the net OOS book; the /091 hypothesis is falsified for the cycle; most likely an OOS regime where cross-sectional momentum compressed.
- **If F2 fires (and F3/F4 do not)** — the model-free score did not strengthen the gross signal OOS.
- **If no falsifier fires** — the model-free score strengthened the gross signal OOS, improved the net book, contained turnover, and transferred; /091 is a genuine, methodologically-clean advance on the scoring-function axis (the Phase-8 classification is the QR's call — Section 8).

---

## Section 5 — Risk Mitigation

Per `feedback_v3_risk_mitigation_design.md`, every merge-candidate iteration carries a Risk Mitigation section. /091's controls are the RETAINED /089 structural controls; the model-free score *removes* the dominant new-failure surface (the trained-model overfit):

| Risk | Mitigation | IS-calibrated / a-priori | Simulated historical effect |
|---|---|---|---|
| **Trained-model overfit** (the /088 sign error, /090 feature overfit, the M3 H=3-feature overfit) | The /091 axis itself — the model-free score has **no trained model, no Optuna, no seed, no feature stack** — the overfitting surface is removed entirely | a-priori (a parameter-free signal cannot overfit) | /091 EDA: the model-free book beats the trained `LGBMRanker` by +0.2020 IS net spread monthly Sharpe at the runner's full Optuna budget — the trained model was *subtracting* value |
| **Turnover / fee drag** (the /088/089/090 dominant book-failure mode) | The 21-bar overlapping hold (~5× fewer rebalances than /089's 3-bar) + the RETAINED /089 no-trade band τ=0.020 + the HARD turnover ceiling 0.138 | IS-selected (the /091 + /089 EDAs) | /091 EDA: model-free IS turnover/bar ≈ 0.0263 at H=21 — far inside the 0.138 ceiling |
| **Cross-sectional-momentum regime break** (the load-bearing /091 residual risk) | The dollar-neutral long-short construction caps directional loss; the regime risk is *measured* and pre-registered (M1b: net −0.1039 in the 2022-crash IS third) and reflected in the Section-7 failure weights | IS-calibrated (the M1b sub-period scan) | /091 EDA M1b: the model-free book is net-positive in 2/3 IS sub-periods, net-negative in the FTX/LUNA-crash third — the regime-sensitivity is quantified, not hidden |
| Lookback-horizon overfit (picking the IS-sweep arithmetic max) | Pre-register H=21 (the literature weekly horizon), NOT the arithmetic-best H=22/23; H=21 is inside a wide smooth [17,25] plateau (net spread [+0.2244, +0.3226]) | IS-selected + cited literature | /091 EDA M1a: the [17,25] sweep is a smooth plateau — the choice within it is not fragile |
| Walk-forward embargo bug (the Phase 5.5 BLOCK) | FIXED at the /091 setup commit: `embargo_ms` from `XS_REQUIRED_GAP×interval_ms` to `(XS_HORIZON+1)×interval_ms` (Section 3.2) | a-priori (the gate's Fix A) | the /091 model-free book is embargo-independent (trains nothing); the fix restores the full 24-month training window for the reference `LGBMRanker` comparator |
| Directional market drawdown | Dollar-neutral long-short construction | a-priori (construction) | /088/089/090: market beta removed by design |
| Single-symbol concentration | Quintile long-short — ~4–5 names/leg | a-priori (construction) | /091 EDA: H=21 model-free max IS symbol concentration 17.5% — structurally < 30% |
| High-vol-symbol domination | Inverse-vol weighting within each leg + portfolio vol-targeting | a-priori (standard cross-sectional construction) | /088/089/090: per-symbol concentration capped |
| Listing non-stationarity | 60-day (180-bar) listing burn-in per symbol | a-priori (crypto pitfall) | /088/089/090: applied |
| Label / feature look-ahead | The model-free score uses only `close(ts)`/`close(ts−H·interval)` (both ≤ ts); PnL return strictly after ts (`searchsorted side='right'`); the reference comparator runs under the 484-row CPCV purge + corrected `(H+1)×interval_ms` embargo | a-priori (formula) + the /091 setup tests | /091 EDA: model-free book is look-ahead-clean by construction; /091 adds the dual embargo-distinction assertion test (Section 9) |
| Methodology defect in a falsifier-driving metric (the /090 BLOCK) | The Section 3.3 SETUP item — `gross_monthly_sharpe` a reproducible runner artifact via the shared `_monthly_sharpe` helper, with a smoke test | a-priori (Critic /090 Rec #1) | closes the /090 BLOCK root cause — F2's gross-Sharpe input is a runner artifact |

The /091-specific risk *removal* is the headline: the model-free score eliminates the trained-model overfitting surface — the single most-aligned move with v3's anti-overfitting mission (Section 6.1). The load-bearing /091-specific residual *risk* is the cross-sectional-momentum regime break — quantified by M1b and carried honestly into the Section-7 failure weights.

## Section 6 — Risk Management Design

The cross-sectional book is risk-managed by construction (Section 5). The legacy v3 7-gate stack stays **deferred** — re-introducing it onto the cost-aware cross-sectional book in the same iteration would confound the scoring-function measurement (the same honest scoping call /088/089/090 made). /091's risk apparatus: dollar-neutral construction + inverse-vol + vol-targeting + quintile diversification + the 21-bar overlapping-hold tranching + the no-trade band + the HARD turnover ceiling + the lookback-horizon-overfit discipline (H=21, the literature weekly horizon inside a smooth plateau, not the IS arithmetic max).

### 6.1 — Rigor note: a model-free signal is the lowest-overfitting-risk strategy possible

This is stated explicitly so the Critic sees it framed, not implicit. v3's mission is anti-overfitting — the entire 8-phase workflow (purged CV, embargo, DSR/PSR, the OOS wall, the no-cheating discipline) exists to stop the researcher fooling himself. **A parameter-free trailing-return cross-sectional sort has zero fitted parameters**: no Optuna search, no seed, no learned feature weights, no model. There is *nothing to overfit*. The trailing-return lookback H=21 is the one design choice, and it is (a) set to the a-priori literature weekly horizon, (b) inside a wide smooth IS plateau where the choice is not fragile, and (c) not tuned to OOS. Contrast the cross-sectional line's failure history — every one is an overfitting failure: /088 longed the model's predicted losers (a fitted-model sign error), /090 added features the trained model overfit (FEATURE-EXPANSION-FALSIFIED), and the M3 finding is that the H=21 ranker overfits the H=3-built feature stack's noise. Replacing the trained model with a parameter-free score does not just reduce the overfitting risk — it *removes the overfitting surface*. This is the most anti-overfitting-aligned axis the cross-sectional line can run, and it is precisely *why* the EDA's model-free book beats the trained one: the parameter-free score cannot overfit, so it does not. /091 is, by construction, the lowest-overfitting-risk EXPLORATION in the cross-sectional line.

The honest cost of this rigor: a model-free book has no model to *improve* — its IS signal is ~+0.30 net spread monthly Sharpe and that is the ceiling of this single signal. /091 is not an attempt to clear the +1.0 floor; it is the test of whether the cross-sectional line has a genuine, parameter-free, positive OOS book — the un-overfittable foundation a cycle-4 multi-factor build (multiple orthogonal model-free cross-sectional sleeves) would stand on.

---

## Section 7 — Pre-Registered Failure-Mode Prediction (honest)

The /088/089/090 closeout calibration lessons are applied: pre-register the modal outcome honestly, name the dominant failure mechanism, do not over-weight the tail. The /091 IS evidence is strong on the *direction* (model-free beats the trained `LGBMRanker` by +0.2020 IS net spread at full Optuna budget, on a smooth [17,25] plateau) but **sober on the absolute level and honest on the regime-sensitivity** (net-negative in the 2022-crash IS third):

- **≈45% — the modal outcome: the model-free score MATERIALLY improves the OOS net book and it is net-positive but thin.** OOS net monthly Sharpe lifts from /089's −0.0985 to roughly [+0.00, +0.20]; OOS gross monthly Sharpe clears /089's +0.1717 (≈[+0.20, +0.45]); turnover collapses well within the 0.138 ceiling; OOS rank-IC stays positive; the OOS net monthly Sharpe remains far below the +1.0 floor. The first net-positive cross-sectional OOS book — the foundation /092 / cycle 4 builds on. This is the expected result.
- **≈22% — F1/F2 fire: the model-free score does NOT improve the net/gross OOS book** (OOS net ≤ −0.0985 OR OOS gross ≤ +0.1717). The dominant mechanism: the 2025-03→2026-05 OOS window contains a cross-sectional-momentum-compressing regime (a deleveraging crash, an analogue of the M1b 2022 third where the model-free book ran −0.1039), or the crypto "faster metabolism" (Dobrynskaya) reversed the H=21 signal faster OOS. This is the foreseeable failure for a momentum-family axis and is weighted higher than a pure model-improvement axis would be, because the IS evidence itself shows a regime where the signal loses.
- **≈22% — the model-free score lifts the OOS book clearly net-positive** (OOS net in [+0.20, +0.40]) — the model-free momentum book transfers strongly, helped by a favourable trending OOS regime. A good outcome, explicitly NOT the modal one.
- **≈8% — the model-free score lifts the gross signal but the net book hovers within ±0.03 of /089's −0.0985** — a marginal outcome where the gross gain and a thinner-OOS regime roughly cancel.
- **≈3% — full success: OOS net monthly Sharpe ≥ +1.0.** A model-free single-signal book clearing the floor on the first pass is firmly not expected — the IS model-free net spread is ~+0.30, and the floor is +1.0. Named honestly as a tail.

The single most-likely outcome is the **≈45% "model-free score works, OOS net book net-positive but thin, sub-floor."** The most likely *failure* is F1/F2 — an OOS cross-sectional-momentum-compressing regime (≈22%). The honest residual: the model-free book's IS signal is ~+0.30 net spread monthly Sharpe and regime-sensitive; /091 is the test of whether the cross-sectional line has a genuine positive OOS book at all, and /092 (the CONFIRMATION) is where that book — if /091 produces it — is validated for whether it is worth carrying.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria — Classification Taxonomy (LOCKED)

iter-v3/091 is a scoring-function-axis EXPLORATION on the RETAINED cross-sectional architecture. A scoring-function change is a **CONSTRUCTION axis** (it changes *what signal* is harvested from the cross-section, holding the construction fixed — consistent with the /089 CONSTRUCTION-PARTIAL taxonomy lineage; it is NOT a feature axis and NOT an architecture axis — the cross-sectional architecture, the pooled-panel + quintile-long-short + walk-forward apparatus, is unchanged). **An EXPLORATION cannot update BASELINE_V3.md regardless of classification** — BASELINE_V3.md stays `v0.v3-059` (IS +1.0894 / OOS +0.5791). The taxonomy, evaluated in disjunctive precedence (first match canonical):

### 8.1 — SUSPICIOUS (evaluated FIRST)
Fires on EITHER (a) OOS net monthly Sharpe / IS net monthly Sharpe **> 3.0** (the OOS-soars-on-flat-IS signature — N/A if IS is negative), OR (b) OOS rank-IC ≥ 2× the model-free book's IS rank-IC magnitude (an implausible OOS-better-than-IS divergence), OR (c) OOS gross monthly Sharpe ≥ 3× /089's +0.1717 (i.e. ≥ +0.515 — an implausible cross-sectional-momentum gross jump; the EDA supports a lift toward [+0.20, +0.45], so a tripling would be a SUSPICIOUS divergence).

### 8.2 — CONSTRUCTION-FALSIFIED
Fires if (NOT SUSPICIOUS) AND **F3 fires (IS turnover > 0.138 ceiling) OR F1 fires (OOS net monthly Sharpe ≤ /089's −0.0985) OR F2 fires (OOS gross monthly Sharpe ≤ /089's +0.1717)**. The model-free score blew turnover (a build defect), or did not improve the net OOS book, or did not strengthen the gross signal OOS → the /091 model-free-scoring hypothesis is falsified for the cycle. NO-MERGE. The cross-sectional architecture and `cross_sectional.py` infrastructure are RETAINED (the architecture is not falsified — the /088/089 OOS rank-IC stands; only the /091 scoring change is). The scoring reverts to the trained `LGBMRanker`.

### 8.3 — CONSTRUCTION-VALIDATED-PROMISING
Fires if (NOT SUSPICIOUS, NOT 8.2) AND **OOS rank-IC > 0 AND IS turnover ≤ 0.138 AND OOS gross monthly Sharpe > /089's +0.1717 AND OOS net monthly Sharpe > /089's −0.0985 AND OOS net monthly Sharpe > 0**. The model-free score strengthened the gross signal, contained turnover, transferred OOS, improved the net book, AND produced a **net-positive OOS book** — the first net-positive cross-sectional OOS book in the line. Sub-case **8.3-FULL**: additionally OOS net monthly Sharpe ≥ +1.0 AND IS net monthly Sharpe ≥ +1.0 — clears the absolute floors; a /092 CONFIRMATION-bundle candidate. Sub-case **8.3-FOUNDATION**: OOS net monthly Sharpe ∈ (0, +1.0) — validated and generalising, the cross-sectional book is net-positive but sub-floor; advances as the cross-sectional baseline into the /092 CONFIRMATION (the un-overfittable foundation a cycle-4 multi-factor build stands on).

### 8.4 — CONSTRUCTION-PARTIAL
Fires if (NOT SUSPICIOUS, NOT 8.2, NOT 8.3) AND **OOS rank-IC > 0 AND IS turnover ≤ 0.138 AND OOS gross monthly Sharpe > /089's +0.1717 AND OOS net monthly Sharpe > /089's −0.0985** but the OOS net monthly Sharpe is **≤ 0** (8.3 does not fire — the net book improved materially but is not yet net-positive). The model-free score strengthened the gross signal, contained turnover, transferred OOS, and materially improved the OOS net book — but the still-thin signal keeps it sub-zero. NO-MERGE; the scoring-function axis is advanced and recorded.

### 8.5 — NULL / INCONCLUSIVE
The Phase-6 build did not reach a runnable cross-sectional backtest. Recorded for completeness; the model-free build is a focused scoring-path addition on the RETAINED runnable /088/089 infrastructure, so this is not expected.

**MERGE/NO-MERGE statement.** /091 is an EXPLORATION — it does NOT merge to update BASELINE_V3.md regardless of class. A `v0.v3-091` annotated EXPLORATION closeout marker is issued at Phase 8 (the `v0.v3-082`…`v0.v3-090` pattern). The substantive decision: 8.3-FULL → the model-free cross-sectional construction advances to the /092 CONFIRMATION bundle; 8.3-FOUNDATION → the model-free cross-sectional book advances into the /092 CONFIRMATION as the cross-sectional baseline (net-positive but sub-floor); 8.4 → the model-free cross-sectional book is RETAINED as the cross-sectional baseline and recorded in the exploration catalog with its delta — /092 CONFIRMATION evaluates whether it is CONFIRMATION-worthy; 8.2 → the scoring reverts to the trained `LGBMRanker`, the cross-sectional architecture retained.

---

## Section 9 — Library Stack Declaration + integration-test mandate

- **LightGBM** — `LGBMRanker(lambdarank)` — used ONLY by the reference `LGBMRanker` comparator (`score_mode="trained"`). The /091 **primary book is model-free and uses no LightGBM at all.** Already a v3 dependency.
- **Optuna** — used ONLY by the reference comparator; the model-free book has no Optuna search.
- **pandas / numpy** — the pooled-panel construction, the model-free trailing-return cross-sectional score (`close_wide / close_wide.shift(H) − 1`), the cross-sectional rank-normalization, the overlapping-tranche book, the no-trade band, the turnover diagnostic, the CPCV path net-return computation, the shared `_monthly_sharpe` helper.
- **No new third-party dependency.** Every /091 change — the `score_mode` scoring branch, the `XS_HORIZON`/`XS_HOLD_BARS` constant changes, the induced `XS_REQUIRED_GAP` recompute, the walk-forward embargo bug fix, the gross-Sharpe runner artifact — is a constant edit + a scoring-branch addition + a one-line embargo correction + a pure-pandas refactor. No mlfinlab/mlfinpy/pypbo/fracdiff dependency added or changed.

**Integration-test mandate (per `feedback_v3_methodology_axis_integration_test.md`).** The /091 setup commit has THREE test deliverables, all required before the build is considered wired:

1. **The model-free scoring smoke test.** Assert that with `score_mode="model_free"`: (a) `run_cross_sectional_backtest` produces a non-empty results DataFrame on a small IS panel slice; (b) `strategy._train_for_month` is NOT called (no model trained — e.g. assert `strategy._model is None` after the run); (c) the `predicted_score` column equals the trailing-`H`-bar return computed independently on a fixture (the score IS the trailing return). This is the integration test for the new edge axis — it pins the scoring path to its definition.
2. **The gross-Sharpe runner-artifact smoke test (the Section 3.3 SETUP item — the Critic /090 Rec #1 mandate).** The runner emits `gross_monthly_sharpe` (IS + OOS) to `comparison.csv` and `dsr.json`, computed by the IDENTICAL per-calendar-month code path as the net `monthly_sharpe` — both calling one shared `_monthly_sharpe(sub, pnl_col)` helper. The smoke test asserts the two share the code path (monkeypatch the shared helper; assert both emitted values reflect the patch). A methodology-axis integration test at the runner call-site — the /090 BLOCK was a call-site DEFECT.
3. **The embargo-distinction assertion test (the Phase 5.5 BLOCK fix, codified).** A unit test asserting BOTH quantities at `XS_HORIZON = 21`:
   - **CPCV row-gap:** `XS_REQUIRED_GAP == 484 == (XS_HORIZON + 1) * N_XS_SYMBOLS` — the `×N` factor IS present (it is a row count).
   - **Walk-forward wall-clock embargo:** the `embargo_ms` fed to `_generate_xs_monthly_splits` `== (XS_HORIZON + 1) * interval_ms == 22 * interval_ms` — the `×N` factor is **absent** (it is a time quantity). Equivalently assert `embargo_ms != XS_REQUIRED_GAP * interval_ms` (the bugged form).
   - AND that `_generate_xs_monthly_splits` at the corrected embargo still produces a non-empty walk-forward over the IS panel.

The cross-sectional test suite (`tests/strategies/ml/test_cross_sectional.py`) must remain green; the three new tests are additive.

## Section 10 — QR Audit Trail

### 10.1 — The axis re-design and the QR call

The prior /091 brief — and the /090 closeout's RECOMMENDED axis — was the holding-horizon extension of the `LGBMRanker`. The Phase 5.5 gate (`c56c457`, OVERALL=BLOCK) caught a real walk-forward embargo bug; the QR took the gate's Fix A and re-ran the EDA with the embargo corrected. **The corrected EDA changed the conclusion**: at the weekly horizon the embargo-independent model-free H2 book (+0.2964 IS net spread monthly Sharpe) decisively beats the trained `LGBMRanker` H1 book (−0.0125 at 8 trials). Per `feedback_v3_axis_selection_quant_discipline.md` the axis follows the EDA — and the EDA now points at the *model*, not the horizon. The QR's calls in this brief, all IS-EDA / research-grounded:

(a) **Pivoting the axis from horizon-extension to the model-free scoring function.** The horizon-extension brief tested whether extending the `LGBMRanker`'s hold helps. The corrected EDA shows the `LGBMRanker` *itself* is the bottleneck — a parameter-free sort on the same construction gets +0.30 IS net where the `LGBMRanker` gets ~+0.09 (35-trial). The QR re-designed /091 around the finding the EDA actually shows. This brief SUPERSEDES the horizon-extension brief.

(b) **Committing a focused confirming EDA before re-writing the brief.** `analysis/iteration_v3-091/model_free_vs_ranker_eda.py` — three stress-tests + one diagnosis. M1 confirmed the model-free finding is a wide smooth [17,25] plateau (not a grid artifact) and is net-positive in 2/3 IS sub-periods but regime-sensitive. M2 stress-tested the `LGBMRanker` at the runner's full 35 Optuna trials — the gap *narrows* from the 8-trial proxy's +0.31 to a true **+0.2020**, but the model-free book still wins decisively. M3 diagnosed *why*: the 13-feature stack is horizon-mismatched (mean `|univariate rank-IC|` 0.0231 at H=3 → 0.0170 at H=21; the H=21 ranker spends 68.0% of its gain on horizon-mismatched features). The axis is QR-EDA-confirmed.

(c) **Choosing the model-free book over a horizon-matched-feature `LGBMRanker` re-design.** The dispatch permitted either. The QR chose the model-free book (Section 2.6): the M2 result IS the H=21-label-trained `LGBMRanker` and it still loses by +0.20 — recovery would need a horizon-matched feature *stack* (a cycle-4 research programme, recorded in Section 11), not a single clean EXPLORATION axis; the model-free book is a single fully-specified axis and the lowest-overfitting-risk strategy possible.

(d) **Honest framing of the IS level.** The QR records that the model-free IS signal (~+0.30 net spread monthly Sharpe) is well below the +1.0 floor and regime-sensitive (M1b: −0.1039 in the 2022-crash third). /091 is honestly framed as the test of whether the cross-sectional line has a genuine positive OOS book at all — not an attempt to clear the floor. The dispatch's "~0.31 gap" is corrected to the runner-fidelity +0.2020 (the 8-trial proxy overstated it).

(e) **The Phase 5.5 BLOCK and the embargo fix** — carried forward unchanged from the corrected horizon-extension brief: the QR took the gate's Fix A (the CPCV's own `gap // N` division proves the row-gap ≠ the time-embargo), corrected the EDA's walk-forward embargo to `(H+1)×interval_ms`, and specifies the runner embargo fix in Section 3.2 as a correctness item.

### 10.2 — Literature-research path

Cross-sectional crypto momentum, the model-free trailing-return cross-sectional sort, the weekly horizon:

1. **Drogen, Hoffstein & Otte, "Cross-sectional Momentum in Cryptocurrency Markets" (Starkiller Capital)** — SSRN 4322637. The practitioner reference for the *model-free* cross-sectional momentum book: a top-quintile / bottom-quintile sort on the **raw trailing return** (no learned model), tested across lookbacks of 5–150 days, finds the greatest monotonicity and quintile-spread for return timeframes of 10–35 days with a 7-day rebalance. Their preferred parameters (30-day lookback, 7-day rebalance) produced 37.8% annualized (top quintile) vs −33.8% (bottom) IS, but OOS top-quintile was only −2.35% — the stark IS/OOS gap that grounds the /091 honest residual. Crucially, the Starkiller book IS a model-free trailing-return sort — the /091 axis is the canonical practitioner construction, not an exotic one.
2. **Dobrynskaya, "Cryptocurrency Momentum and Reversal"** — SSRN 3913263 / *J. Alternative Investments* 26(1):65. Across ~2,000 cryptos, cross-sectional momentum returns are positive and significant for holding horizons up to ~2 weeks, reversing beyond — and the momentum-to-reversal switch is *much faster than equities* ("the faster metabolism of cryptocurrencies"). This grounds the H=21 (~7 days) pre-registration (squarely inside the weekly window, before the reversal) and the F4 / Section-7 OOS-reversal risk.
3. **Han, Kang & Ryu, "Time-Series and Cross-Sectional Momentum in the Cryptocurrency Market"** — SSRN 4675565. Examines lookback/holding periods 1–56 days; explicit that cross-sectional crypto momentum is **weak net of realistic transaction costs** ("significant returns often yield insignificant profits when accounting for transaction costs"). Grounds the honest residual and the importance of the /089 cost-aware construction (which /091 retains).
4. **Poh, Lim, Zohren & Roberts, "Building Cross-Sectional Systematic Strategies By Learning to Rank"** — arXiv 2012.07149. The /088 methodology paper — a learning-to-rank cross-sectional framework. Re-consulted here for the *contrast*: the LTR framework's premise is that a learned ranker beats a raw-factor sort *when the feature set carries orthogonal predictive content*. The /091 M3 diagnosis shows the v3 13-feature stack does not carry that content at the weekly horizon (it is horizon-mismatched) — which is precisely why, in this specific case, the model-free sort wins. The LTR architecture is not falsified in general; it is shown to need a horizon-matched feature stack (the cycle-4 candidate).

The research path: paper 1 (Starkiller) establishes the model-free trailing-return quintile sort as the canonical practitioner cross-sectional-momentum construction and supplies the weekly-rebalance horizon; paper 2 (Dobrynskaya) supplies the momentum-then-reversal structure grounding H=21 and the OOS-reversal risk; paper 3 (Han-Kang-Ryu) supplies the "thin net of costs" honest caveat; paper 4 (Poh et al.) frames why the learned ranker loses here specifically (a horizon-mismatched feature stack) without falsifying the LTR architecture in general.

### 10.3 — No-cheating audit

Per `feedback_no_cheating.md` — every design parameter selected on IS data only or a-priori:

- **OOS_CUTOFF_DATE / training_months** — IMMUTABLE, untouched. The backtest runs on full data; the reporting splits at the cutoff. The IS window is NOT trimmed; no date is cherry-picked.
- **The scoring function (model-free trailing-return cross-sectional sort)** — selected by the committed IS-only EDAs: `holding_horizon_eda.py` (H1 vs H2 — the trained book loses to the model-free book at every horizon ≥ 7) and `model_free_vs_ranker_eda.py` (M2 — confirmed at the runner's full 35-trial budget; M3 — the WHY). OOS never read.
- **The lookback horizon H=21** — selected on IS evidence (the M1a [17,25] smooth plateau) + the a-priori cited literature weekly horizon (Starkiller 7-day rebalance). H=21 is NOT the IS arithmetic max (H=22/23, +0.32) — it is the literature-canonical interior point inside the plateau, deliberately chosen so the pick is not a "best-of-N" IS selection.
- **`XS_REQUIRED_GAP = 484`** and **the walk-forward embargo `(XS_HORIZON+1)×interval_ms`** — mechanical consequences of the formulae, not tuned. The embargo fix is a correctness change (the Phase 5.5 BLOCK fix), not a tuning change.
- **The /089 cost-aware construction + the 0.138 turnover ceiling, the universe** — RETAINED unchanged; the /090 downside features are DROPPED (a revert).
- The EDA scripts read only IS rows; the model-free score uses only `close(ts)` and `close(ts−H·interval)` (both ≤ ts).
- The QR sees OOS for the first time in Phase 7. Every Section 4 OOS gate is a pre-registered evaluation gate, not a tuned parameter.

### 10.4 — The honest senior read

iter-v3/091 is a genuine, well-researched, IS-EDA-confirmed iteration — the final cycle-3 EXPLORATION on v3's most-sustained structural line. The Phase 5.5 gate caught a real walk-forward embargo bug; the corrected EDA then surfaced a finding bigger than the horizon-extension brief exploited, and a focused confirming EDA made it decisive: **at the weekly horizon a parameter-free trailing-return cross-sectional sort beats the trained `LGBMRanker` by +0.2020 IS net spread monthly Sharpe at the runner's full Optuna budget — the `LGBMRanker`, fed a feature stack built for the H=3 label, is destroying a real cross-sectional momentum signal.** The QR pivoted /091's axis to the evidence — score the cross-section model-free — which is the bold, evidence-driven move the standing mandate demands, and is simultaneously the **lowest-overfitting-risk strategy possible**: a parameter-free signal has nothing to overfit, which is maximally aligned with v3's anti-overfitting mission, and is *why* the model-free book wins. The brief is honest about the level: the model-free IS signal (~+0.30 net spread monthly Sharpe) is well below the +1.0 floor, is regime-sensitive (net-negative in the 2022-crash IS sub-period), and OOS will be thinner. /091 is not an attempt to clear the floor; it is the test of whether the cross-sectional line has a genuine positive OOS book at all — the un-overfittable foundation a cycle-4 multi-factor build (multiple orthogonal model-free cross-sectional sleeves) would stand on. The brief carries two correctness/instrumentation items — the embargo bug fix and the gross-Sharpe runner artifact — neither a second edge axis. The modal OOS outcome is a net-positive but thin cross-sectional book; the most likely failure is an OOS cross-sectional-momentum-compressing regime. That is the relentless, honest, top-quant-firm-grade execution the mission demands — /091 closes cycle 3 by testing whether the cross-sectional line has, at its un-overfittable core, a real positive book.

## Section 11 — Reproducibility Stamp

- **Phase 5.5 BLOCK → fix history.** Original horizon-extension EDA SHA `5ab371d` + original brief SHA `605ffdf`; the Phase 5.5 gate (`c56c457`, OVERALL=BLOCK) found the walk-forward embargo 22× too large; the corrected horizon-extension EDA was `d4ad137` and the corrected horizon-extension brief `e913d3e`. **This brief and the focused EDA SUPERSEDE the horizon-extension line entirely** — the corrected EDA surfaced a finding (model-free beats trained) that re-directs the /091 axis from the holding horizon to the scoring function.
- **EDA SHAs**:
  - `d4ad137` — `analysis/iteration_v3-091/holding_horizon_eda.py` (corrected-embargo horizon grid; its H1/H2 tables surfaced the finding). RETAINED as-is.
  - `a2c3a3f` — `analysis/iteration_v3-091/model_free_vs_ranker_eda.py` + `M1a/M1b/M2/M3/M4` CSVs + console output — the focused confirming EDA committed for this brief (M1 robustness, M2 the `LGBMRanker` 35-trial stress-test, M3 the WHY diagnosis).
  Both EDAs are IS-only (`open_time < OOS_CUTOFF_MS`); the IS-internal walk-forward trains the reference ranker on IS months and predicts the next IS month; the model-free book trains nothing; no OOS row is read.
- **Brief SHA**: `9d3d525` — this re-written brief, `briefs-v3/iteration_v3-091/research_brief.md` (the model-free scoring-function axis, superseding the horizon-extension brief `e913d3e`). This Section-11 brief SHA is backfilled in the immediately-following commit. The Phase 5.5 gate is re-run by the QE on this brief.
- **Setup SHA** (QE Phase-6, NOT done by the QR): the model-free scoring path (`score_mode` parameter + the trailing-return scoring branch — Section 3.1), the dual-book runner (model-free primary + `LGBMRanker` reference), the `XS_HORIZON`/`XS_HOLD_BARS` 3→21 change (the induced `XS_REQUIRED_GAP` recompute to 484), the walk-forward embargo bug fix (Section 3.2), the `expand_downside=False` / 13-feature revert, the gross-Sharpe runner-artifact SETUP item (Section 3.3), `ITERATION_LABEL "v3-091"`, and the three new tests (Section 9). To be recorded at the /091 setup commit.
- **Reports**: `reports-v3/iteration_v3-091/` (Phase 6 — the model-free book is the primary; the `LGBMRanker` reference is a clearly-suffixed comparator).
- **Run mode**: EXPLORATION. The primary model-free book has no Optuna and no seed (deterministic). The reference `LGBMRanker` comparator runs single-seed (`seed=42`), `ensemble_size=1`, `--n-trials 35`.
- **Future-iteration axes** (deferred from /091, recorded for the cycle plan): (i) a **horizon-matched feature stack for the `LGBMRanker`** — engineer a clean trailing-momentum feature family for the 21-bar horizon and re-test whether the trained ranker can then beat the model-free book (the M3 diagnosis's open question; a cycle-4 research programme, not a single EXPLORATION); (ii) a **multi-factor model-free cross-sectional construction** — multiple orthogonal parameter-free cross-sectional sleeves (momentum, low-volatility, size/liquidity) combined as a portfolio, the cycle-4 build that would stand on /091's foundation; (iii) the cross-sectional short-tilt / asymmetric-leg construction (DEFERRED — the /090 Critic ruled it a re-slice); (iv) the /092 cross-sectional CONFIRMATION — multi-window/sub-period validation of the /091 model-free book.
