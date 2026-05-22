# iter-v3/103 — Research Brief — Cycle-5 EXPLORATION: an engineered composed feature from the formulaic-alpha operator toolkit (formulaic-alphas round 2, /102-corrected)

> **Iteration:** iter-v3/103 — cycle-5 EXPLORATION slot #3
> **Branch:** `iteration-v3/103`
> **Axis:** ONE new engineered feature added to `V3_FEATURE_COLUMNS` (14 → 15) — one variable.
> **Run mode (planned):** 3-seed EXPLORATION (`--exploration`, `EXPLORATION_ENSEMBLE_SIZE=3`, `--n-trials 35`).
> **Canonical baseline (unchanged):** iter-v3/059 (`v0.v3-059`; IS monthly Sharpe +1.0894 / OOS +0.5791, 10-seed unified ensemble).
> **EDA-mode classification anchor:** iter-v3/060 (3-seed EXPLORATION-mode; IS monthly Sharpe +0.8325 / OOS +0.1403).
> **EDA commit SHA:** `e4d192d` (3 scripts + 6 result CSVs).
>
> **HEADLINE RECOMMENDATION — NULL-AT-EDA.** The deep, multi-angle IS-only EDA (Section 2) screened 7 engineered composed features built from the formulaic-alpha operator toolkit and **conclusively proves no candidate clears an IS-predictive bar.** The two candidates that survive the IS sub-period sign-stability screen (`argmax_pullback_signed_20`, `corr_gated_momentum_5d`) both rank **15/15 and 11-13/15** in IS-fold LightGBM gain-importance on the BCH+TRX IS-engine symbols — the v3 INERT signature (`feedback_v3_inert_features_at_higher_budget.md`). Per that memory rule an INERT feature added at higher Optuna budget actively **HARMS** OOS; proceeding to a Phase-6 backtest with a known-INERT 15th feature would knowingly reproduce the /102 failure. The full 10-section brief is provided per the dispatch mandate; Section 4 carries the NULL-AT-EDA recommendation with its complete numerical basis. The brief documents `argmax_pullback_signed_20` as the *designated* would-be axis (the EDA's strongest survivor) so that — if the Phase-5.5 gate or orchestrator overrides the NULL-AT-EDA recommendation and elects a backtest anyway — the implementation spec (Section 3) and the pre-registered falsifiers (Section 4) are complete and gate-able.

---

## Section 0 — Data-Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` (`OOS_CUTOFF_MS = 1742774400000`) — **IMMUTABLE**. Not touched.
- `training_months = 24` — **IMMUTABLE**. Not touched.
- The walk-forward / CPCV runs on ALL data; the reporting layer splits at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/`.
- **All Phase 1-5 EDA in this brief is strictly IS-only.** Every row entering any IC, sign-stability, quartile-stability, redundancy, or LightGBM-importance computation in the 3 committed EDA scripts has `open_time < OOS_CUTOFF_MS`. The post-cutoff OOS is **never read** by the QR in Phases 1-5. The triple-barrier label is built on the full panel and then IS-masked — the 21-bar forward scan for the last few IS rows legitimately reads post-cutoff candles, which is exactly how `labeling.py:label_trades` works in production; it is a label-construction mechanic, **not** a feature look-ahead (identical convention to the /102 EDA, Critic-verified there).
- The QR sees OOS results for the FIRST time in Phase 7. Hard floor `OOS_Sharpe / IS_Sharpe ≥ 0.5` (a CONFIRMATION gate; informational for an EXPLORATION).
- Universe: BCHUSDT, LDOUSDT, TRXUSDT. `V3_EXCLUDED_SYMBOLS` in force, unmodified.

---

## Section 1 — Hypothesis

**The axis.** iter-v3/103 is the second attempt at the user-directed WorldQuant-101 formulaic-alphas axis. iter-v3/102 ported the literal Kakushadze Alpha#32 and it closed EXPLORATION-NEGATIVE (IS monthly Sharpe collapsed to +0.3993; the held-out-tail accuracy proxy that selected it does not predict the multi-seed Optuna IS fit — /102 closeout Lesson 1).

/103 is the *smarter* attempt the dispatch mandates. Two corrections to /102:

1. **Engineer a v3-specific COMPOSED feature, do not port a literal alpha.** v3's only PROMISING post-bootstrap feature — iter-v3/025's `regime_momentum_signed_5d` = `ret_5d × sign(hurst_100 − 0.5)` — was an engineered composition that explicitly encodes a regime×momentum interaction a depth-3-5 tree cannot compose at split level. /103's candidates are built from the formulaic-alpha operator toolkit (`ts_argmax`, `ts_argmin`, `ts_rank`, `decay_linear`, `scale_ts`, `ts_corr`) into compositions of that same non-tree-representable class.

2. **The selection evidence must be IS-PREDICTIVE.** /102 selected on a held-out-tail single-classifier accuracy horse race — an OOS-leaning statistic. /103's screen is genuine IS feature→label IC, 3-symbol sign-consistency, IS sub-period (half + quartile) sign-stability, and an IS-fold LightGBM gain-importance + IS-validation-logloss test. None of these touch the post-cutoff OOS; all four directly predict what a multi-seed IS Optuna fit consumes.

**The hypothesis under test (the designated candidate).** *A signed extremum-proximity feature — `argmax_pullback_signed_20` = `(close / max(close, 20) − 1) × sign(ret_60)` — encodes a directional pullback-depth interaction (how far below the 20-bar high the close sits, sign-conditioned by the 20-day trend) that the v3 per-symbol depth-3-5 LightGBM cannot compose from price levels; adding it as a 15th `V3_FEATURE_COLUMNS` feature lifts the OOS monthly Sharpe vs the /060 anchor without collapsing the IS fit.*

**The honest disposition of this hypothesis.** The deep EDA (Section 2) **falsifies it at the EDA stage**: `argmax_pullback_signed_20` is the strongest survivor of the sign-stability screen but is INERT-by-importance (rank 15/15 on BCH and TRX). The recommendation is NULL-AT-EDA. Section 4 documents this in full.

---

## Section 2 — IS-Only Numerical Evidence

All tables below are produced by the 3 committed EDA scripts under `analysis/iteration_v3-103/` (commit `e4d192d`). All strictly IS-only.

### The candidate basket — 7 engineered composed features

`analysis/iteration_v3-103/candidate_lib.py` defines 7 candidates, each built from the formulaic-alpha operator toolkit into a composition that encodes a non-tree-representable interaction:

| Candidate | Construction | Encoded interaction |
|---|---|---|
| C1 `recency_weighted_momentum_5d` | `ret_5d × (1 − argmax20_recency/19)` | momentum down-weighted by trend staleness |
| C2 `extrema_recency_skew_30` | `(argmin30 − argmax30)/29` | recency asymmetry of the windowed high vs low |
| C3 `vol_decayed_trend` | `decay_linear(ret,10) × sign(atr_rank200 − 0.5)` | recency-weighted momentum, vol-regime sign gate |
| C4 `corr_gated_momentum_5d` | `ret_5d × corr(close,volume,20)` | momentum gated by volume-confirmation |
| C5 `tsrank_dispersion_ratio` | `ts_rank(ret_std20/ret_std60, 50)` | 50-bar percentile of short/long return-dispersion ratio |
| C6 `scaled_reversal_pressure_signed` | `scale_ts(close − sma7, 100) × sign(hurst − 0.5)` | the alpha032 fast term, regime-conditioned (repairs alpha032's regime-independent sign) |
| C7 `argmax_pullback_signed_20` | `(close/max20 − 1) × sign(ret60)` | signed pullback depth from the 20-bar high |

### T1 — IS panel summary (`T1_is_panel_summary.csv`)

| symbol | is_rows | is_first | is_last | long_label_frac |
|---|---:|---|---|---:|
| BCHUSDT | 3567 | 2021-12-21 | 2025-03-23 | 0.4558 |
| LDOUSDT | 581 | 2024-09-11 | 2025-03-23 | 0.5370 |
| TRXUSDT | 3509 | 2022-01-04 | 2025-03-23 | 0.5526 |

**Note the LDO panel is only 581 IS rows** — it is too thin to carry a feature verdict on its own. The IS-engine symbols are BCH (3567 rows, 95.76% of /059 IS PnL) and TRX (3509 rows). A feature must earn its place on BCH+TRX.

### T2/T3 — directional Spearman IC vs the /059 triple-barrier label + 3-symbol sign-consistency (`T2_is_directional_ic.csv`)

| candidate | ic_BCH | ic_LDO | ic_TRX | mean_abs_ic | sign_consistent_3sym |
|---|---:|---:|---:|---:|:--:|
| `tsrank_dispersion_ratio` | −0.0059 | −0.1728 | −0.1191 | **0.0992** | True |
| `argmax_pullback_signed_20` | +0.0515 | +0.0090 | +0.0905 | 0.0503 | True |
| `extrema_recency_skew_30` | −0.0750 | −0.0661 | −0.0089 | 0.0500 | True |
| `vol_decayed_trend` | −0.0095 | −0.0968 | +0.0090 | 0.0384 | False |
| `corr_gated_momentum_5d` | +0.0810 | +0.0109 | +0.0198 | 0.0372 | True |
| `recency_weighted_momentum_5d` | +0.0146 | −0.0400 | −0.0443 | 0.0329 | False |
| `scaled_reversal_pressure_signed` | +0.0024 | +0.0681 | +0.0044 | 0.0250 | True |

For reference, alpha032's /102 mean |IC| was 0.0354 with `sign_consistent=False`. Five of the 7 /103 candidates are sign-consistent across all 3 symbols — already a stronger basket than the /102 alpha basket, where alpha032's IS IC flipped sign (BCH −0.0255, LDO +0.0413, TRX +0.0395).

### T4 — IS sub-period sign-stability: half-split AND quartile resolution (`T4_is_subperiod_stability.csv`)

The half-split test (early half vs late half of each symbol's IS window, chronological — **IS-only, the post-cutoff OOS is never touched**) rejects all 7 candidates as not 3-symbol-stable. The decisive refinement is the **quartile-resolution** test on the IS-engine symbols BCH+TRX (a half-split can mask a sign-flip averaged over half a window; it also wrongly flags a sign-flip of a *near-zero* IC as instability). Quartile-by-quartile IC signs on the IS-engine symbols:

| candidate | BCH quartile signs | TRX quartile signs | quartile-stable on BCH+TRX |
|---|---|---|:--:|
| `recency_weighted_momentum_5d` | [−,+,+,−] | [+,−,−,−] | no |
| `extrema_recency_skew_30` | [−,−,−,−] | [+,+,+,−] | no |
| `vol_decayed_trend` | [−,+,+,−] | [−,+,+,+] | no |
| `corr_gated_momentum_5d` | [+,+,+,+] | [+,+,−,+] | no (TRX Q3 flips) |
| `tsrank_dispersion_ratio` | [−,+,−,+] | [−,+,−,−] | no |
| `scaled_reversal_pressure_signed` | [−,−,+,+] | [+,−,+,−] | no |
| **`argmax_pullback_signed_20`** | **[+,+,+,+]** | **[+,+,+,+]** | **YES** |

**`argmax_pullback_signed_20` is the only candidate** that holds one IC sign across all 4 BCH quartiles AND all 4 TRX quartiles. `corr_gated_momentum_5d` is the runner-up (BCH all positive, TRX flips once). Both are carried into the decisive importance test (Script 3).

**The `tsrank_dispersion_ratio` cautionary detail.** It has the strongest aggregate mean |IC| (0.0992, ~3× alpha032) and is sign-consistent — superficially the best candidate. The quartile breakdown destroys it: BCH full IC is −0.0059 (essentially zero) with quartiles [−0.032, +0.067, −0.055, +0.011] (sign oscillates); LDO quartiles [+0.125, −0.190, −0.266, −0.454] (sign flips Q1→Q2); TRX quartiles [−0.265, +0.009, −0.192, −0.039] (sign flips Q2). The strong aggregate |IC| was an artifact of a thin 581-row LDO panel plus per-symbol aggregation hiding sign instability — **the /102 trap in a different costume**: a number that looks good in aggregate but does not reflect a stable IS relationship a multi-seed Optuna fit could consume. This is exactly why /103's screen does not stop at aggregate |IC|.

### T5 — incumbent redundancy: candidate vs the 14 `V3_FEATURE_COLUMNS` (`T5_incumbent_redundancy.csv`)

Pairwise |Spearman| of each surviving candidate vs each of the 14 incumbents, IS-only, max over all (incumbent × symbol) pairs. Gate: max |IC| < 0.70 (the v3 hard redundancy gate, Critic Check 4).

| candidate | max abs_ic | nearest incumbent | gate |
|---|---:|---|:--:|
| `argmax_pullback_signed_20` | **0.6846** | `ema_spread_atr_20` (on BCH) | PASS (barely — 0.015 below the gate) |
| `corr_gated_momentum_5d` | 0.1543 | `regime_momentum_signed_5d` (on BCH) | PASS |

`argmax_pullback_signed_20` passes the strict 0.70 gate but only by 0.015 — it is **near-collinear with `ema_spread_atr_20`** (the EMA-spread-over-ATR incumbent) on BCH. A feature that nearly duplicates an incumbent steals `colsample_bytree` picks without adding orthogonal signal (the iter-v3/070 / iter-v3/023 mechanism). This is a fragility flag, corroborated by the importance test below.

### T6 — IS-fold LightGBM gain-importance — the DECISIVE IS-predictive test (`T6_isfold_importance.csv`)

For each symbol, a depth-4 LightGBM (the v3 architecture; `num_leaves=15`, `max_depth=4`) is fit on the IS panel with the 14 incumbents + the candidate (15 columns), using a **chronological 70/30 IS train/validation split** — no shuffling, no post-cutoff data, no leakage. Reported: the candidate's gain-importance rank among 15, its gain share, and the IS-validation binary-logloss WITH (15-feat) vs WITHOUT (14-feat) the candidate.

| candidate | symbol | gain_rank_of_15 | gain_share_pct | parity 6.67% | IS-val logloss 15-feat | IS-val logloss 14-feat | Δ (15 − 14) |
|---|---|---:|---:|:--:|---:|---:|---:|
| `argmax_pullback_signed_20` | BCH | **15** | **0.000** | below | 0.68300 | 0.68489 | −0.00189 |
| `argmax_pullback_signed_20` | LDO | 5 | 8.643 | above | 0.75400 | 0.75161 | +0.00238 |
| `argmax_pullback_signed_20` | TRX | **15** | 1.056 | below | 0.69181 | 0.69246 | −0.00065 |
| `corr_gated_momentum_5d` | BCH | 11 | 1.446 | below | 0.68327 | 0.68489 | −0.00163 |
| `corr_gated_momentum_5d` | LDO | 6 | 2.550 | below | 0.75040 | 0.75161 | −0.00121 |
| `corr_gated_momentum_5d` | TRX | 13 | 0.274 | below | 0.69045 | 0.69246 | −0.00201 |

**This is the decisive result.** `argmax_pullback_signed_20` ranks **dead last (15/15)** in BOTH BCH and TRX — the two IS-engine symbols — and its BCH gain share is literally **0.000%**. It is above parity only on the 581-row LDO panel (too thin to carry a verdict). This is the textbook v3 **INERT** signature — the /019/082/085/086 pattern, where the tree declines to allocate ranked split capacity to the feature. `corr_gated_momentum_5d` is the same story: rank 11-13/15, below parity in all 3 symbols.

The IS-validation logloss deltas are all noise-floor (−0.0019 to −0.0020, except a small *worsening* on LDO). A feature contributing 0.000% gain on the IS engine cannot move a multi-seed Optuna fit in either direction by signal — and per `feedback_v3_inert_features_at_higher_budget.md`, at the CONFIRMATION's n_trials=1050 a rank-15/15 feature actively **harms** OOS by letting Optuna overfit IS noise *through* the dead 15th column.

### EDA verdict

Seven engineered composed features, screened on four IS-predictive axes (directional IC, 3-symbol sign-consistency, quartile-resolution IS sub-period stability, IS-fold LightGBM importance + IS-validation logloss). **Every candidate fails an IS-predictive bar.** The strongest survivor of the stability screen is INERT-by-importance on the IS-engine symbols. No candidate is IS-predictive. The recommendation is **NULL-AT-EDA**.

---

## Section 3 — Proposed Changes (the designated-candidate implementation spec)

This section specifies the full implementation **as if** the designated candidate `argmax_pullback_signed_20` were to be backtested — so the spec is complete and gate-able if the Phase-5.5 gate or orchestrator overrides the NULL-AT-EDA recommendation. **The QR recommendation is NULL-AT-EDA (Section 4); under that recommendation, none of the changes below are applied and the iteration closes at the EDA.**

**The one-variable change (if backtested):**

1. **New feature function** in `src/crypto_trade/features_v3/engineered_v3.py` (the existing Category-2 composed-feature module — `argmax_pullback_signed_20` is a composed feature, the same home as `regime_momentum_signed_5d` and `trend_efficiency_signed`): `compute_argmax_pullback_signed_20(df) -> pd.DataFrame`. Construction (strictly past-only):
   - `roll_max = close.rolling(20, min_periods=20).max()` — the 20-bar high (ends at bar t; past-only).
   - `pullback = close / roll_max − 1.0` — ≤ 0; 0 means the close is at the 20-bar high.
   - `ret_60 = log(close) − log(close.shift(60))` — the 20-day (60-bar × 8h) trend.
   - `trend_sign = sign(ret_60)`; `sign(0)` → NaN (degenerate flat-trend bars).
   - `argmax_pullback_signed_20 = pullback × trend_sign`. Range ≈ [−1, +1].
   - NaN warm-up: first ~60 bars (the `ret_60` shift dominates the 20-bar max window).
2. **Dispatch:** add the `compute_argmax_pullback_signed_20` call to `add_engineered_v3_features` (the GROUP_REGISTRY `engineered_v3` entry point). The column is generated for all 3 symbols.
3. **`V3_FEATURE_COLUMNS_TOP_N`** in `src/crypto_trade/features_v3/__init__.py`: append `"argmax_pullback_signed_20"` as the 15th element (after `regime_momentum_signed_5d`).
4. **`_verify_feature_columns`** expected count: 14 → 15; add an explicit `"argmax_pullback_signed_20" in V3_FEATURE_COLUMNS` positive assertion.
5. **`ITERATION_LABEL`** → `"v3-103"`.
6. **Parquet regeneration:** regenerate the BCH/LDO/TRX v3 feature parquets so `argmax_pullback_signed_20` is present.

No label change, no model-architecture change, no universe change, no risk-gate change. The 14 incumbent `V3_FEATURE_COLUMNS`, the BCH/LDO/TRX universe, ATR multipliers (2.0/1.0), the 21-candle timeout, and the 7-gate RiskV2 stack are bit-identical to /059.

---

## Section 4 — Expected OOS Impact + Pre-Registered Numerical Falsifiers

**Anchor.** Per `feedback_v3_dsr_mode_artifact.md` + `feedback_v3_cycle1_axis_pass_criteria.md` + the /101/102 closeout lesson that anchor-architecture-matching is verdict-determining: a 3-seed EXPLORATION-mode run is classified against the **3-seed EXPLORATION-mode reference /060** (IS monthly Sharpe **+0.8325** / OOS **+0.1403**), NOT the 10-seed /059 CONFIRMATION baseline.

### The QR recommendation — NULL-AT-EDA

**The dispatch defines NULL-AT-EDA as "reserved only for an axis the deep EDA conclusively proves dead (high bar)." The /103 EDA clears that bar.** The proof, in three committed scripts:

- **No candidate is IS-predictive.** All 7 engineered composed features fail the joint IS-only screen (sign-consistency + quartile stability). The strongest stability survivor, `argmax_pullback_signed_20`, is **INERT-by-importance: rank 15/15 in both BCH and TRX**, the two symbols that carry 99%+ of the /059 IS PnL, with a BCH gain share of 0.000%.
- **An INERT 15th feature is known to harm, not help.** `feedback_v3_inert_features_at_higher_budget.md` is binding: a feature that ranks last in importance, added at higher Optuna budget, produces OOS Sharpe −1.07 vs +0.78 (Δ −1.85) because the larger search space lets Optuna overfit IS noise through the dead column. This is also the mechanism the /102 closeout identified (alpha032 was *learned* and still collapsed IS; an INERT feature is the milder-but-still-negative sibling).
- **Proceeding to a Phase-6 backtest would knowingly reproduce /102.** /102's failure was that its selection proxy (held-out-tail accuracy) did not predict the IS fit. /103's EDA uses an IS-predictive screen *and that screen returns a negative verdict*. To then run the backtest anyway would discard the very evidence the /102 lesson tells us to trust. The honest move is to report the negative EDA result with the numbers — which is what NULL-AT-EDA is.

**Predicted OOS impact if backtested anyway (the would-be axis).** Were `argmax_pullback_signed_20` backtested as a 15th feature: predicted OOS monthly Sharpe ≈ the /060 anchor +0.1403 **±0.30** (band **[−0.16, +0.44]**) — a wide, near-zero-centred band, because an INERT feature's effect on the roster is dominated by Optuna-noise re-selection, not signal. Predicted IS monthly Sharpe **[+0.40, +0.85]** — biased *below* the /060 anchor +0.8325, because the dominant predicted mechanism is the `feedback_v3_inert_features_at_higher_budget.md` IS-overfit-through-the-dead-column effect (and the T5 near-collinearity with `ema_spread_atr_20` means the 15th colsample slot is partly wasted). **The most likely backtest outcome is EXPLORATION-NEGATIVE-via-IS-collapse or EXPLORATION-INERT** — i.e. the run would, at material cost in compute, confirm what the EDA already shows.

### Pre-registered numerical falsifiers (GATES — used only if a backtest is run despite the NULL-AT-EDA recommendation)

These are evaluated against the /060 matched anchor. The axis is FALSIFIED at Phase 7 if ANY fires.

| # | Falsifier | Fires if |
|---|---|---|
| F1 | Headline OOS regression | OOS monthly Sharpe < **+0.00** (the 15th feature made the book net-losing OOS) |
| F2 | IS collapse | IS monthly Sharpe < **+0.60** (a >0.23 drop below the /060 anchor +0.8325 — the `feedback_v3_inert_features_at_higher_budget.md` IS-overfit mechanism; this is the **predicted modal failure**) |
| F3 | BCH-only artifact | the OOS lift is carried entirely by BCH AND **both** LDO and TRX OOS weighted-pnl regress vs /060 |
| F4 | INERT by importance | `argmax_pullback_signed_20`'s walk-forward-aggregated gain-importance rank is **last (15/15)** in **all 3** per-symbol models OR its combined share is below the 1/15 = 6.67% parity in **all 3** — **the EDA already predicts this fires** (T6: rank 15/15 on BCH and TRX; above parity only on the 581-row LDO panel, which is borderline) |
| F5 | Mechanical roster-churn | OOS improves AND the per-symbol added-vs-removed-trade mean-duration gap exceeds **+1.0 candles** on any symbol with a material OOS lift (the /076 + /101-F5 trade-selection sub-channel signature) |

**Behavioral-effect predictor** (per `feedback_v3_axis_saturation_predictor.md`): adding an INERT 15th feature shifts the per-symbol Optuna fits weakly, so the OOS roster shifts modestly. **Predicted: the OOS trade roster changes by 3-18% vs the /060 3-seed OOS roster (102 trades).** If the observed change is below 5%, the feature is behaviorally saturated → classify INERT.

---

## Section 5 — Risk Mitigation (R1-R5, IS-calibrated, simulated effect)

Under the NULL-AT-EDA recommendation **no code change is applied**, so the /059 risk stack is untouched by definition. The section below covers the *would-be* axis (if backtested anyway): a single engineered-feature addition modifies no live risk gate; the R1-R5 stack is inherited from /059 unchanged and is itself the risk mitigation.

- **R1 (cooldowns):** unchanged. A feature addition does not affect SL-streak cooldowns.
- **R2 (drawdown scaling):** the 7-gate `RiskV2Config` stack — vol scaling, ADX (`adx_threshold=20.0`), Hurst regime, z-score OOD, low-vol filter, hit-rate (disabled), BTC-trend kill — unchanged.
- **R3 (OOD detection):** the z-score OOD gate (`zscore_threshold=2.0`) operates on its own configured feature subset, **not** `V3_FEATURE_COLUMNS`; adding a 15th feature does not enlarge the OOD feature set. `argmax_pullback_signed_20` is bounded ≈ [−1, +1] by construction (a ratio-minus-1 times a sign), so it introduces no non-stationary drift the OOD gate would have to absorb. ADF: the feature is bounded and built from a price-ratio and a sign — ADF-stationary by construction (the Engineer's Phase-6 ADF check, if a backtest is run, would confirm; if the brief is closed at NULL-AT-EDA this is moot).
- **R4 (vol kill-switch):** the BTC-trend kill (`BTC_TREND_CONFIG.threshold_pct=15.0`) unchanged.
- **R5 (concentration cap):** `enable_per_symbol_drawdown_brake=False` unchanged (per /020/054 closeouts — per-symbol PnL caps and drawdown brakes are CLOSED at catalog level).

**Simulated historical effect of the axis itself.** The EDA *is* the simulation of the feature's IS effect: T6 simulates `argmax_pullback_signed_20`'s contribution inside a depth-4 LightGBM on each symbol's IS window and finds it INERT (rank 15/15, 0.000% BCH gain share). There is no positive simulated IS effect to mitigate — the simulated effect is "no effect on the IS engine." No new gate is introduced, so no new gate needs IS-calibration. **Under the NULL-AT-EDA recommendation the risk profile of the live system is unchanged from /059.**

---

## Section 6 — Risk-Management Design (the deeper structural defense)

The deeper structural argument has two layers.

**Layer 1 — the would-be axis is the lowest-blast-radius change class.** A single composed-feature addition touches one feature function, one GROUP_REGISTRY dispatch line, and one entry in `V3_FEATURE_COLUMNS_TOP_N`. It does not change the label, the model architecture, the universe, or any risk gate. If it were backtested and failed, the revert is one feature column (the `formulaic_v3.py` / `funding_regime_momentum_5d` precedent — drop the column, retain the function as zero-revert-cost dead code). The blast radius is minimal by design.

**Layer 2 — and the EDA is itself the primary risk control.** The genuinely important structural defense in /103 is *the EDA gate that produced the NULL-AT-EDA recommendation*. The /102 failure cost a full 3-seed backtest (~0.7h wall-clock plus the Phase 5.5/6/7.5 cycle) to confirm a feature was negative. /103's IS-predictive EDA — directional IC, sign-consistency, quartile stability, and the IS-fold LightGBM importance test — reaches a high-confidence negative verdict *before* any backtest is run. The IS-fold importance test in particular is a direct, cheap proxy for the question "will the multi-seed Optuna fit allocate split capacity to this feature, and will using it help or harm the IS fit" — the exact question the /102 held-out-tail proxy could not answer. **Recommending NULL-AT-EDA on conclusive IS-predictive evidence is the risk-management design**: it spends ~zero compute to avoid knowingly reproducing a known failure mode (`feedback_fail_fast.md` — the cheap-kill discipline the /094/095/096/098/099 fail-fast EDAs established).

**The structural lesson for the catalog.** Across cycle 4 + cycle 5, *every* single-feature-addition axis to the v3 14-feature stack has failed: the 7-FEED INERT verdict (funding ×4, microstructure ×1, basis ×1), /098 (off-the-shelf families, NO-GO at EDA), /102 (a literal formulaic alpha, NEGATIVE-by-IS-collapse), and now /103 (7 engineered composed features, NULL-AT-EDA-by-INERT). The binding constraint is not the feature *family* — it is that the v3 per-symbol depth-3-5 LightGBM on a thin 8h triple-barrier signal has a saturated feature set; a 15th feature does not lift it and tends to harm the IS fit. The structural priority (`feedback_v3_structural_over_knob_exploration.md`) for the next EXPLORATIONs is a genuinely new *edge source* or *new architecture*, not a 16th feature.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

Pre-registered, in probability order, for the outcome **if a backtest is run despite the NULL-AT-EDA recommendation**:

1. **Most likely — EXPLORATION-NEGATIVE via F2 (IS collapse).** The EDA shows `argmax_pullback_signed_20` is INERT on the IS engine (rank 15/15 on BCH+TRX) AND near-collinear with `ema_spread_atr_20` (T5 max |IC| 0.6846). Per `feedback_v3_inert_features_at_higher_budget.md`, adding such a feature at the 3-seed EXPLORATION's n_trials=35 (and a fortiori at a CONFIRMATION's 1050) lets Optuna overfit IS noise through the dead 15th column and through the near-duplicate slot — the modal predicted outcome is the IS monthly Sharpe dropping below the +0.60 F2 floor. This is the /102 failure mode and the /063 mass-expansion mode.
2. **Second — EXPLORATION-INERT via F4.** The EDA directly predicts F4: rank 15/15 in BCH and TRX. If the multi-seed walk-forward aggregation also lands LDO sub-parity (LDO is borderline at 8.6% on a 581-row panel), F4 fires cleanly in all 3 and the outcome is INERT — the feature is behaviorally ignored and the headline barely moves. Whether the backtest reads as NEGATIVE (F2) or INERT (F4) depends on whether the IS-overfit-through-the-dead-column effect is strong enough to breach the +0.60 floor; both are negative dispositions.
3. **Third — EXPLORATION-SUSPICIOUS via F5.** A lower-probability tail: the 15th feature shifts the fitted models enough to re-select a duration-biased OOS roster (the /076/101 trade-selection sub-channel), producing a spurious OOS lift on a collapsed IS fit. This is the iter-v3/026/027/030/034/036/037/102 IS-collapse / OOS-spike signature.
4. **Least likely — EXPLORATION-PROMISING.** The EDA gives near-zero probability to a genuine PROMISING outcome: an INERT feature has no IS-signal mechanism by which to lift OOS durably. Any OOS lift would be roster-churn (→ SUSPICIOUS, F5), not edge.

**The honest meta-prediction:** the most likely thing a /103 backtest would do is spend compute to confirm the EDA's NULL-AT-EDA verdict. That is precisely why the recommendation is to close at the EDA.

---

## Section 8 — Classification Taxonomy (LOCKED, disjunctive precedence)

Two cases.

### Case A — the iteration closes at NULL-AT-EDA (the QR recommendation)

**NULL-AT-EDA** — the deep, multi-angle IS-only EDA conclusively proves no candidate clears an IS-predictive bar (Section 2: all 7 engineered composed features fail the joint sign-consistency + quartile-stability + IS-fold-importance screen; the strongest survivor is rank 15/15 INERT on the IS-engine symbols). NO-MERGE; non-advancing. No code change is applied; `V3_FEATURE_COLUMNS` stays at 14. The formulaic-alphas axis — across /102 (literal port, NEGATIVE) and /103 (engineered compositions, NULL-AT-EDA) — closes at two data points. `BASELINE_V3.md` baseline metrics are UNCHANGED; a Dead Ideas entry records the formulaic-composed-feature basket (Section 9 below specifies the wording). Tag `v0.v3-103` is a closeout marker only.

### Case B — if the Phase-5.5 gate / orchestrator overrides and a backtest is run

Evaluated in Phase 8 against the Phase-7 OOS results, in this precedence order (first match wins). Anchor = /060 (3-seed EXPLORATION-mode; IS +0.8325 / OOS +0.1403).

1. **BLOCKED** — Critic Phase-7.5 OVERALL=BLOCK (methodology defect). NO-MERGE.
2. **NEGATIVE** — Falsifier F1 OR F2 OR F3 fires. NO-MERGE; record the axis as NEGATIVE in Dead Ideas.
3. **SUSPICIOUS** — Falsifier F5 fires OR a structurally-suspicious IS/OOS divergence (IS daily Sharpe / OOS daily Sharpe ratio outside [0.2, 5]). NO-MERGE; non-advancing.
4. **INERT** — Falsifier F4 fires (rank last in all 3 models or sub-parity share in all 3) with no signal lift. NO-MERGE.
5. **PROMISING** — none of F1-F5 fires AND OOS monthly Sharpe improves over the /060 anchor +0.1403 by ≥ +0.20 (the cycle-1/5 OOS-PASS gate) AND IS monthly Sharpe ≥ +0.60 AND the per-symbol picture is sign-consistent. A PROMISING EXPLORATION does NOT update `BASELINE_V3.md`; it is carried to the cycle-5 CONFIRMATION for 10-seed validation. **The EDA gives this near-zero probability.**
6. **NULL-RESULT** — the run completes but fits none of the above cleanly. NO-MERGE; documented.

`BASELINE_V3.md` is **not** edited by this EXPLORATION regardless of outcome (the `v0.v3-082`…`v0.v3-102` pattern). Tag `v0.v3-103` is a closeout marker only.

---

## Section 9 — Library Stack + Integration-Test Mandate

**Library stack:** **no new library.** The EDA scripts use `numpy`, `pandas`, and `lightgbm` — all already pinned dependencies. The would-be feature `compute_argmax_pullback_signed_20` uses only `numpy` + `pandas` rolling operations. Pinned versions inherited from /059: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. Python 3.13.

**Under the NULL-AT-EDA recommendation no production code is written, so no integration test is required** — the deliverable is the 3 committed EDA scripts (`e4d192d`) and this brief.

**Integration-test mandate IF a backtest is run anyway** (per `feedback_v3_methodology_axis_integration_test.md` — a feature addition adds a code path through the feature function + GROUP_REGISTRY + the feature-column list, so it needs end-to-end coverage):

1. **Unit test** — `tests/features_v3/test_engineered_v3.py` (extend the existing file): assert `compute_argmax_pullback_signed_20` on a synthetic OHLCV frame (a) produces a column `argmax_pullback_signed_20`; (b) is past-only — recomputing on a frame truncated 60 bars early leaves the overlap bit-identical (the LdP look-ahead test as a regression test); (c) the warm-up NaN count matches the 60-bar `ret_60` window; (d) returns all-NaN cleanly if `close` is missing.
2. **Integration smoke test** — generate v3 features for one symbol end-to-end and assert `argmax_pullback_signed_20` appears in the parquet and in `V3_FEATURE_COLUMNS`; a short `LightGbmStrategy` train on one (symbol, month) cell asserting the model trains with the 15-feature stack.
3. **Phase-6 pre-flight** — the Engineer verifies `len(V3_FEATURE_COLUMNS) == 15`, `"argmax_pullback_signed_20" in V3_FEATURE_COLUMNS`, `ITERATION_LABEL == "v3-103"`, the track-isolation grep on `engineered_v3.py` is empty, and the BCH/LDO/TRX parquet `close_time` freshness + forming-candle checks pass.

**ADF / IC gates (would-be axis):** `argmax_pullback_signed_20` is bounded ≈ [−1, +1] by construction → **ADF gate expected PASS**. **IC redundancy gate: marginal PASS** — T5 shows max |IC| 0.6846 vs `ema_spread_atr_20`, 0.015 below the 0.70 family gate. It is a Category-2 composed feature; the strict Critic-Check-4 |IC| gate is applied in full and passes only barely — itself a fragility flag corroborating the NULL-AT-EDA recommendation.

---

## Section 10 — QR Audit Trail

Per `feedback_v3_axis_selection_quant_discipline.md`, axis selection must be QR-led with a committed `analysis/iteration_v3-NNN/*.py` EDA basis before the brief.

- **Axis origin.** The formulaic-alphas axis is a standing user directive (the WorldQuant-101 exploration). iter-v3/102 was the first attempt (literal alpha032 port; EXPLORATION-NEGATIVE). iter-v3/103 is the QR-led /102-corrected second attempt: ENGINEER a v3-specific composed feature, and select on IS-PREDICTIVE evidence (the /102 closeout Lesson 1 + Critic Recommendation 2).
- **QR EDA basis (committed BEFORE this brief, commit `e4d192d`):**
  - `analysis/iteration_v3-103/candidate_lib.py` — 7 engineered composed features from the formulaic-alpha operator toolkit, with strictly-past-only operators.
  - `analysis/iteration_v3-103/is_predictive_screen.py` — directional IC (T2), 3-symbol sign-consistency (T3), IS sub-period stability (T4). Outputs `T1_is_panel_summary.csv`, `T2_is_directional_ic.csv`, `T4_is_subperiod_stability.csv`, `T2T4_screen_verdict.csv`.
  - `analysis/iteration_v3-103/is_importance_redundancy.py` — incumbent redundancy (T5), IS-fold LightGBM gain-importance + IS-validation logloss (T6). Outputs `T5_incumbent_redundancy.csv`, `T6_isfold_importance.csv`.
- **The /102-trap avoidance — explicit.** /102's selection proxy (T6 held-out-tail single-classifier accuracy) optimised an OOS-leaning statistic. /103 uses **no held-out-tail proxy**. The selection evidence is (a) genuine IS feature→label Spearman IC, (b) 3-symbol sign-consistency, (c) quartile-resolution IS sub-period sign-stability, (d) IS-fold LightGBM importance — all strictly IS-only, all directly predictive of what a multi-seed IS Optuna fit consumes. The `tsrank_dispersion_ratio` cautionary case in Section 2 (a candidate with a strong *aggregate* |IC| but unstable quartiles — the /102 trap in disguise) shows the screen actively catches the failure mode.
- **The QR recommendation.** **NULL-AT-EDA.** The deep EDA conclusively proves no engineered composed feature in the basket is IS-predictive (the strongest stability survivor is rank 15/15 INERT on the IS-engine symbols). Per `feedback_v3_inert_features_at_higher_budget.md`, backtesting an INERT 15th feature is known to harm OOS; per the /102 lesson and `feedback_fail_fast.md`, the honest move is to report the negative IS-predictive verdict and close at the EDA rather than spend compute to reproduce a known failure mode. The brief is provided complete (all 10 sections) per the dispatch mandate; the designated candidate `argmax_pullback_signed_20` and its full implementation spec (Section 3) and pre-registered falsifiers (Section 4) are documented so the Phase-5.5 gate has a complete, gate-able artifact if it elects to override the NULL-AT-EDA recommendation and run a backtest.
- **Setup commit SHA:** `0c7ae45` (this research brief). EDA commit SHA: `e4d192d` (3 scripts + 6 result CSVs).
- **NO CHEATING:** `OOS_CUTOFF_DATE` / `training_months` untouched; all Phase 1-5 EDA strictly IS-only (`open_time < OOS_CUTOFF_MS`); the IS-fold LightGBM is trained AND validated within the IS window; the QR did not inspect the post-cutoff OOS.
