# iter-v3/105 — Research Brief — Cycle-5 EXPLORATION slot #5: the trend-scanning label — a per-bar data-selected prediction horizon (label-geometry re-framing)

> **Axis class:** LABEL GEOMETRY — a structural re-framing of the estimand itself. Replace the v3 single fixed 21-candle triple-barrier *training label* with a **trend-scanning label** (López de Prado, *Machine Learning for Asset Managers* §5.4): per bar, fit an OLS linear trend over a GRID of horizons and label the bar by the sign of the slope at the horizon with the largest |t-statistic|. The prediction horizon is **data-selected per bar**, not a fixed hyperparameter.
>
> **QR verdict from the Phase-1 fail-fast gating EDA: GO.** The pre-registered F-HORIZON / F-IC / F-RATE gates (set by the /104 closeout Section 7) all clear. This brief recommends the Phase-6 backtest.
>
> **EDA-mode classification anchor:** iter-v3/060 (3-seed EXPLORATION-mode; IS monthly Sharpe **+0.8325** / OOS **+0.1403**) — per `feedback_v3_dsr_mode_artifact.md` + `feedback_v3_cycle1_axis_pass_criteria.md` + the /101/102 closeout lesson that anchor-architecture-matching is verdict-determining. The 10-seed /059 CONFIRMATION baseline (IS +1.0894 / OOS +0.5791) is NOT the EXPLORATION-mode anchor.

---

## Section 0 — Data-Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` (`OOS_CUTOFF_MS = 1742774400000`) — **IMMUTABLE; untouched.**
- `training_months = 24` — **IMMUTABLE; untouched.**
- 8h candles. Universe BCHUSDT / LDOUSDT / TRXUSDT — **unchanged.** `V3_EXCLUDED_SYMBOLS` unchanged.
- All Phase 1-5 EDA in this brief is strictly **IS-only**: every row entering any horizon-distribution, IC, sign-stability, or label-balance computation has `open_time < OOS_CUTOFF_MS`. The post-cutoff OOS was **not** inspected by the QR in Phases 1-5; the QR sees OOS for the first time in Phase 7.
- The walk-forward embargo fix (`e149e9d`, `train_end_ms = test_start_ms - embargo_ms`) is inherited unchanged.

---

## Section 1 — Hypothesis

**The diagnosis cycle 5 has established (the /100→/104 closeout chain).** Every closed v3 axis — the 7-FEED feature families (funding ×4, microstructure, basis), /098 off-the-shelf families, /102 a literal formulaic alpha, /103 seven engineered composed features, /104 on-chain network-activity, the /016/093/096/100 model-architecture attacks, the /101 training objective, the /099 label-CLASS re-partition, the /097 universe — attacked the **INPUTS to** or the **ESTIMATOR of** a *fixed* prediction problem. **Not one changed what the prediction problem IS.** The /104 diary's structural read: the thin v3 signal is plausibly an artifact of the single fixed 21-candle prediction horizon — a lottery on whether the predictable move happens to complete inside exactly 21 candles, when on a per-symbol 8h series the resolvable horizon almost certainly varies bar-to-bar with the volatility regime.

**The hypothesis under test.** *Replacing the fixed 21-candle triple-barrier training label with a trend-scanning label — which lets each bar be labeled at the horizon where its move is statistically most resolvable — produces a label the existing 14-feature `V3_FEATURE_COLUMNS` stack predicts materially better (higher feature→label IC), and that better-predicted estimand lifts the OOS monthly Sharpe vs the /060 anchor without collapsing the IS fit.*

**Why this is genuinely new, not a re-tread — explicit.** iter-v3/099 re-partitioned the *same* fixed-horizon barrier event (a label-CLASS change — it added an abstention class) and closed NO-GO. iter-v3/010 tuned the barrier *multipliers* (2.0/1.0) — a knob on the same label. iter-v3/072 added a `fixed_horizon` mode — still a single fixed horizon, just the sign of the N-candle return instead of a barrier. Trend-scanning is none of these: it changes the **estimand**. The model is no longer asked "does a ±ATR barrier hit within 21 candles" but "what is the sign of the most statistically significant local trend, at whatever horizon that trend is most resolvable." That is the one structural lever the cycle-5 evidence most directly implicates and has never been pulled.

**The ONE clean variable.** The single axis is the **training label geometry**: `label_mode` `triple_barrier` → `trend_scanning`. The v3 backtest's trade EXECUTION layer — the triple-barrier TP/SL/timeout exits (ATR 2.0/1.0, 21-candle timeout), the 7-gate RiskV2 stack, the per-symbol architecture, the 14 features, the universe — is kept **bit-identical to /059**. Only the label the model is *trained on* changes. This makes the axis cleanly attributable to one variable: if OOS moves, it moves because the model learned a better-framed target, not because exits or risk gates changed.

---

## Section 2 — IS-Only Numerical Evidence

Three committed IS-only EDA scripts under `analysis/iteration_v3-105/` (EDA commit `857e176`): `trend_scanning_gating_eda.py` (the F-HORIZON / F-IC / F-RATE gates), `trend_scanning_robustness.py` (the longest-wins degeneracy probe + paired-cell significance), `trend_scanning_grid_sensitivity.py` (the decisive capped-grid check). Every row entering any computation has `open_time < OOS_CUTOFF_MS`. The incumbent /059 triple-barrier label is reconstructed with the EXACT production rule (`label_trades(label_mode="triple_barrier", use_atr=True, atr_tp=2.0, atr_sl=1.0, timeout=21 candles, fee_pct=0.1)`, ATR in price units = `close × natr_21_raw / 100`) so the IC comparison is apples-to-apples on the SAME shared-support rows.

### T1 — the selected-horizon distribution is broad, NOT degenerate (F-HORIZON does NOT fire)

`T1_selected_horizon_distribution.csv` — the per-bar data-selected horizon over the IS panel, gating grid {5,8,13,21,34}:

| Symbol | h=5 | h=8 | h=13 | h=21 | h=34 | median_h | norm. entropy |
|---|---:|---:|---:|---:|---:|---:|---:|
| BCH | 7.65% | 8.94% | 14.07% | 23.08% | 46.25% | 21.0 | 0.860 |
| LDO | 6.90% | 10.18% | 16.53% | 23.50% | 42.90% | 21.0 | 0.881 |
| TRX | 8.15% | 9.68% | 15.19% | 22.61% | 44.36% | 21.0 | 0.878 |

The F-HORIZON kill (the /104 pre-registration) fires only if the distribution is degenerate — collapsed to one horizon. It is not: **normalized entropy is 0.86-0.88** (1.0 = uniform), and the four shorter horizons collectively hold 54-57% of bars on every symbol. The horizon is genuinely data-selected per bar. **F-HORIZON does NOT fire.**

### T2 — the 14-feature stack predicts the trend-scanning label MATERIALLY better (F-IC fires GO)

`T2_feature_label_ic_comparison.csv` + `T5_screen_verdict.csv` — the 14-feature `V3_FEATURE_COLUMNS` feature→label Spearman IC, computed on the SAME shared-support rows against the NEW trend-scanning label vs the INCUMBENT triple-barrier label:

| Symbol | mean \|IC\| vs trend-scanning | mean \|IC\| vs triple-barrier | Δ |
|---|---:|---:|---:|
| BCH | 0.04524 | 0.02559 | **+0.01964** |
| LDO | 0.06670 | 0.04757 | **+0.01913** |
| TRX | 0.02673 | 0.01787 | **+0.00886** |
| **Aggregate (14 feat × 3 sym)** | **0.04622** | **0.03034** | **+0.01588** |

The aggregate **ratio is 1.52** — the 14-feature stack predicts the trend-scanning label **+52% better** than it predicts the incumbent triple-barrier label. The pre-registered F-IC GO bar (set in the gating script) was a ≥+20% relative lift (ratio ≥ 1.20). **The observed 1.52 clears it decisively. F-IC fires GO.** This is the single most direct IS-only evidence the /104 diagnosis is right: the binding constraint is the label geometry, not the features. The same 14 features that look thin against the incumbent estimand carry materially more signal against the re-framed estimand.

### T3 — the trend-scanning label is MORE temporally stable than the incumbent

`T3_subperiod_sign_stability.csv` — chronological quartile-resolution sign-stability of the per-symbol feature→label IC (the /103 `tsrank_dispersion_ratio` lesson: a half-split masks within-half flips, so quartile is the binding resolution). On the top-5 trend-scanning features per symbol, **8 of 15 cells are quartile-stable** (one IC sign held across all 4 IS quartiles) under trend-scanning. And the trend-scanning label is *more* stable than the incumbent on the same features: `ema_spread_atr_20` is quartile-stable `----` under trend-scanning on **all 3 symbols** while the incumbent triple-barrier flips (`-+--` on BCH and TRX); `regime_momentum_signed_5d` (v3's one PROMISING post-bootstrap feature) is quartile-stable `----` under trend-scanning on LDO and TRX. A re-framed label that the features predict both *more strongly* (T2) and *more consistently* (T3) is exactly the structural-lift signature.

### T4 — label balance is healthy; the trade rate is not at risk (F-RATE does NOT fire)

`T4_label_balance.csv` — the trend-scanning label is well-balanced and assigns a directional label to every IS bar with a fitted horizon:

| Symbol | trend-scan long/short | trend-scan n_labeled | triple-barrier long/short |
|---|---|---:|---|
| BCH | 48.3% / 51.7% | 5727 | 49.0% / 51.0% |
| LDO | 46.1% / 53.9% | 2741 | 49.3% / 50.7% |
| TRX | 59.6% / 40.4% | 5669 | 55.1% / 44.9% |

The trend-scanning label labels essentially every IS bar (no abstention class — unlike /099); the long/short split is 46-60%, well inside a tradeable band. The model still emits a per-bar directional score, and the EXECUTION layer (the triple-barrier exits + 7-gate RiskV2) is unchanged — so the *trade-emission rate* is governed by the same confidence threshold and the same gate stack as /059. The label change does not mechanically throttle the trade count. **F-RATE does NOT fire** at the EDA; it is re-checked as a Phase-7 falsifier (Section 4).

### The robustness checks — the decisive capped-grid finding

The gating grid {5,8,13,21,34} put 43-46% of mass on the longest horizon h=34. `trend_scanning_robustness.py` probed this adversarially (R1): adding h=55 to the grid, the new longest member grabs ~42-44% — **the same share h=34 had** — and h=34 collapses from ~44% to ~22%. **This is the mechanical-longest-wins signature**: the OLS t-statistic structurally favors longer windows (more degrees of freedom, a smoother fitted trend), so a naive grid biases trend-scanning toward its longest member.

This is a genuine grid-design concern — and `trend_scanning_grid_sensitivity.py` is the check that decides whether the axis survives it. **G1/G2: restrict the grid to {5,8,13,21}** — the longest member is now 21, *identical to the incumbent fixed horizon*, which removes the "longest-wins-beyond-the-incumbent" confound entirely (every horizon trend-scanning can pick is ≤ the incumbent's fixed horizon). Under the capped grid:

| Symbol | h=5 | h=8 | h=13 | h=21 | frac. bars h<21 | capped F-IC ratio |
|---|---:|---:|---:|---:|---:|---:|
| BCH | 13.39% | 15.30% | 22.07% | 49.24% | 50.8% | 1.425 |
| LDO | 12.62% | 16.05% | 23.57% | 47.76% | 52.2% | 1.197 |
| TRX | 14.01% | 15.79% | 22.67% | 47.54% | 52.5% | 1.447 |
| **Aggregate** | — | — | — | — | — | **1.31** |

`G2_capped_grid_fic_verdict.csv`: the capped-grid aggregate F-IC ratio is **1.31** (mean |IC| 0.03977 trend-scan vs 0.03034 incumbent), Wilcoxon signed-rank p = **0.013** over the 42 cells, 25/42 cells improved. **The F-IC lift SURVIVES with the longest-wins confound removed** — and ~51-53% of bars still pick a horizon strictly *shorter* than the incumbent 21. The lift is genuine per-bar data-selection, not a "label by the longest-window trend" relabel.

`R3_paired_ic_significance.csv` (gating grid): 28/42 cells improve, Wilcoxon p = 0.000044. `R2_per_symbol_fic.csv`: the F-IC lift is broad — 8-11 of 14 features improve under trend-scanning on every symbol; the aggregate 1.52 (gating) / 1.31 (capped) is not carried by one symbol.

**The production grid decision (Section 3): the capped grid {5,8,13,21}.** It removes the longest-wins confound, the F-IC lift holds under it, and ~52% of bars genuinely re-frame to a shorter horizon than the incumbent — the structural mechanism the /104 diagnosis posited. The gating grid {5,8,13,21,34} is documented as the EDA exploration; the {5,8,13,21} grid is the one carried to the backtest.

---

## Section 3 — Proposed Changes (the implementation spec)

The ONE-variable change: the training `label_mode` `triple_barrier` → `trend_scanning`. This iteration is a **GO** — the changes below ARE applied.

**1. New `label_mode="trend_scanning"` branch in `label_trades`** (`src/crypto_trade/strategies/ml/labeling.py`). The function already supports `label_mode` with two values (`triple_barrier`, `fixed_horizon` — iter-v3/072). Add a third. The trend-scanning branch:
- For each candidate bar, over the horizon grid (a new `trend_scan_grid` parameter, default `(5, 8, 13, 21)`), fit an OLS linear trend of `close[t : t+h+1]` on a `0..h` time index; compute the slope and its t-statistic `slope / SE(slope)` (`SE` from the OLS residual variance with `dof = n−2`).
- Select the horizon `h*` with the **largest |t-statistic|**; label the bar `+1` if that slope ≥ 0 else `−1`.
- `long_pnl` / `short_pnl`: keep the **same realized-forward-return-net-of-fee convention** the `fixed_horizon` branch already uses — the realized return from the bar's close to the close at `t + h*` (the *selected* horizon), net of `fee_pct`. `weight = |labeled_pnl|`, then the existing `[1, 10]` weight normalization. This keeps the optimizer's Sharpe objective well-defined and consistent with the existing two modes.
- The label uses only `close[t .. t+h*]` — a forward TARGET window (correct; it is the prediction target) — and `h* ≤ max(grid)`. The forward warm-down tail (bars with no full `max(grid)`-candle window) is handled exactly as `triple_barrier`/`fixed_horizon` already handle their tails.
- **Past-only / look-ahead discipline:** the OLS fit reaches only forward of the bar (it is the label); it never touches the training-feature side. The Engineer adds a `test_hard_causality`-style regression test (Section 9): removing N future bars beyond the grid maximum leaves every earlier bar's trend-scanning label bit-identical.

**2. Plumb `trend_scan_grid` through `LightGbmStrategy`** (`src/crypto_trade/strategies/ml/lgbm.py`): a `trend_scan_grid` constructor parameter, stored on the instance and passed into the `label_trades(...)` call at `lgbm.py:385` alongside the existing `label_mode`. Default `(5, 8, 13, 21)`. When `label_mode != "trend_scanning"` the parameter is inert (backward-compatible — v1/v2 and every existing caller are byte-identical).

**3. Runner change** (`run_baseline_v3.py`): pass `label_mode="trend_scanning"` and `trend_scan_grid=(5, 8, 13, 21)` to the `LightGbmStrategy` construction (lgbm.py:1869 region). `ITERATION_LABEL` → `"v3-105"`.

**4. CPCV / walk-forward gap.** The trend-scanning label's forward window extends to `max(grid) = 21` candles — **identical to the incumbent 21-candle triple-barrier timeout.** Therefore `label_timeout_minutes` stays `10080` (21 × 8h), `compute_embargo_candles` stays 22, `REQUIRED_GAP` stays `66 = (21+1) × 3`. **No CV-gap change is needed** — this is a deliberate consequence of capping the grid at the incumbent horizon, and it keeps the embargo correct with zero new leakage surface.

**5. No parquet regeneration.** The label is computed at train time inside `label_trades`, from the OHLCV columns already in the v3 parquets. No feature is added; `V3_FEATURE_COLUMNS` stays at **14, bit-identical to /059**. No feature-column count assertion changes.

**What is NOT changed (bit-identical to /059):** the 14 `V3_FEATURE_COLUMNS`; the BCH/LDO/TRX universe; the trade EXECUTION layer — triple-barrier TP/SL exits at ATR 2.0/1.0 with the 21-candle timeout; the 7-gate RiskV2 stack; the unified 10-seed ensemble architecture; the model architecture (per-symbol depth-3-5 LightGBM). **Only the training label geometry changes.**

**Backtest spec.** 3-seed EXPLORATION mode (`--exploration`, `EXPLORATION_ENSEMBLE_SIZE=3`, `--n-trials 35`) per `feedback_v3_exploration_n_trials_35.md` + `feedback_v3_cadence_discipline.md`. Run command: `uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof`. Estimated wall-clock ≈ the /102 3-seed run (~0.7-1.5h) — the trend-scanning OLS grid adds a per-bar fixed-cost grid fit at LABEL time only; the EDA computed the full-panel label for all 3 symbols in ~2s, so the labeling overhead is negligible against the Optuna fit.

---

## Section 4 — Expected OOS Impact + Pre-Registered Numerical Falsifiers

**Anchor.** iter-v3/060 (3-seed EXPLORATION-mode; IS monthly Sharpe **+0.8325** / OOS **+0.1403**) — the architecturally-matched reference.

**Predicted OOS impact.** The trend-scanning label is the first v3 axis with a *positive* IS-predictive structural signal — a +31% capped-grid feature→label IC lift, Wilcoxon p=0.013, that survived the longest-wins adversarial probe. That is a real but **modest** structural edge: a 14-feature stack predicting a re-framed label 31% better does not translate one-to-one into Sharpe, because (a) the per-symbol depth-3-5 LightGBM already extracts most of the linearly-available signal, (b) the EXECUTION layer (triple-barrier exits) is unchanged, so the label improvement only re-shapes *which direction* the model takes, not *how the trade resolves*. Predicted **OOS monthly Sharpe ≈ +0.45, band [+0.10, +0.95]** vs the /060 anchor +0.1403 — a band centred clearly above the anchor but with a wide lower tail (a label re-framing is a genuine structural change with genuine variance). Predicted **IS monthly Sharpe ≈ +0.85, band [+0.55, +1.15]** — centred near the /060 anchor +0.8325, because the label is better-predicted (T2) and more temporally stable (T3), which should help the IS fit rather than collapse it (the /102 IS-collapse mode is specifically NOT predicted here — /102 collapsed because a 15th feature widened the Optuna search space; /105 adds NO feature and does not widen the search space at all).

**Behavioral-effect predictor** (per `feedback_v3_axis_saturation_predictor.md`). The training label changes for essentially every IS bar — the trend-scanning label and the triple-barrier label disagree on a substantial fraction of bars (different estimands). This is the opposite of a saturated axis: the per-symbol Optuna fits are trained on a materially different target, so the OOS trade roster should shift **substantially — predicted 25-60% of the /060 3-seed OOS roster (102 trades) changes.** If the observed OOS roster change is **below 10%**, the label re-framing did not propagate to the fitted models (a saturation failure) → that is the F-SATURATION falsifier.

### Pre-registered numerical falsifiers (GATES — evaluated at Phase 7 against the /060 anchor; the axis is FALSIFIED if ANY fires)

| # | Falsifier | Fires if |
|---|---|---|
| F1 | Headline OOS regression | OOS monthly Sharpe **< +0.00** (the re-framed label made the book net-losing OOS — the label change destroyed signal) |
| F2 | IS collapse | IS monthly Sharpe **< +0.60** (a >0.23 drop below the /060 anchor +0.8325 — the label re-framing degraded the IS fit; this is the /102/063 IS-collapse mode, here predicted UNLIKELY because no feature is added and the search space does not widen) |
| F3 | BCH-only artifact | the OOS lift is carried entirely by BCH **AND both** LDO and TRX OOS weighted-pnl regress vs /060 (the label change helped only the IS-engine symbol) |
| F4 | F-RATE — trade-rate floor breach | bundle-level OOS trade count **< 60** (a >40% drop below the /060 3-seed OOS roster of 102 trades; per `feedback_v3_trade_rate_floor_bundle_level.md` the floor is bundle-level for v3) |
| F5 | Mechanical roster-churn / suspicious divergence | OOS improves AND the per-symbol added-vs-removed-trade mean-duration gap exceeds **+1.0 candles** on any symbol with a material OOS lift (the /076 + /101-F5 trade-selection sub-channel), OR a structurally-suspicious IS/OOS divergence: IS daily Sharpe / OOS daily Sharpe ratio outside **[0.2, 5]** |
| F6 | F-SATURATION | the OOS trade roster changes by **< 10%** vs the /060 3-seed OOS roster — the label re-framing did not propagate to the fitted models, the axis is behaviorally saturated |

The predicted modal outcome is **PROMISING** (Section 7) — but the falsifier set is genuinely two-sided: F2 guards the IS-collapse tail, F5/F6 guard the overfitting-and-saturation tails, F1/F3/F4 guard the no-signal tails.

---

## Section 5 — Risk Mitigation (R1-R5, IS-calibrated, simulated effect)

The single axis is a training-label-geometry swap. It introduces **no new live risk gate** — so the /059 R1-R5 stack is inherited unchanged and is itself the risk mitigation.

- **R1 (cooldowns):** unchanged. A label change does not affect SL-streak cooldowns — the cooldown logic keys off realized stop-losses in the EXECUTION layer, which is bit-identical to /059.
- **R2 (drawdown scaling):** the 7-gate `RiskV2Config` stack — vol scaling, ADX (`adx_threshold=20.0`), Hurst regime, z-score OOD, low-vol filter, hit-rate (disabled), BTC-trend kill — unchanged. The gates operate on the model's emitted signal + market features, neither of which the label change touches at inference time.
- **R3 (OOD detection):** the z-score OOD gate (`zscore_threshold=2.0`) operates on its own configured feature subset, **not on the label**. The label change cannot enlarge or destabilize the OOD feature set — it adds no feature. **ADF:** no feature is added, so the per-feature ADF gate is unaffected; all 14 `V3_FEATURE_COLUMNS` are bit-identical to /059 and their ADF status is inherited.
- **R4 (vol kill-switch):** the BTC-trend kill (`BTC_TREND_CONFIG.threshold_pct=15.0`) unchanged.
- **R5 (concentration cap):** `enable_per_symbol_drawdown_brake=False` unchanged (per /020/054 — per-symbol PnL caps and drawdown brakes are CLOSED at catalog level).

**Simulated historical effect of the axis itself.** The EDA *is* the IS simulation of the label change: T2 simulates the new label against the existing feature stack on the full IS panel and finds the features predict it +31% better (capped grid); T3 simulates its temporal stability and finds it more stable than the incumbent; T4 simulates its balance and finds it healthy (46-60% long). There is no destabilizing IS effect to mitigate — the simulated effect is a *better-predicted, better-balanced, more-stable* training target. No new gate is introduced, so no new gate needs IS-calibration. **The live system's risk profile is unchanged from /059** — the trade EXECUTION and the 7-gate RiskV2 stack are bit-identical; only what the model is trained to predict changes.

---

## Section 6 — Risk-Management Design (the deeper structural defense)

**Layer 1 — the label-geometry swap is a contained change class with a one-line revert.** The single axis touches one new branch in `label_trades`, one plumbed parameter through `LightGbmStrategy`, and two lines in the runner. It changes no feature, no model architecture, no universe, no risk gate, no CV gap (the grid is capped at the incumbent 21-candle horizon precisely so the embargo is unchanged). If the backtest fails, the revert is `label_mode` back to `"triple_barrier"` and the runner two lines — the `trend_scanning` branch and the `trend_scan_grid` parameter stay in the tree as zero-revert-cost dead code (the `fixed_horizon` / `formulaic_v3.py` retained-infrastructure precedent). The blast radius is minimal by design.

**Layer 2 — the fail-fast gating EDA is the primary risk control, and here it returned GO with a quantified, adversarially-probed signal.** The /103 and /104 fail-fast EDAs spent ~zero compute to *kill* dead axes. The /105 EDA spent ~zero compute to *qualify* a live one: it did not stop at the headline F-IC ratio 1.52. It ran the longest-wins degeneracy probe (R1), found the OLS t-stat mechanically favors the longest grid horizon, and then ran the decisive capped-grid check (G1/G2) that removes the confound — and the lift held at 1.31 with Wilcoxon p=0.013. **The risk-management design here is that the GO is not a single number; it is a number that survived the most obvious way it could have been an artifact.** That is why this brief recommends the backtest where /103/104 recommended NULL-AT-EDA: the difference is not optimism, it is that the IS-predictive evidence is positive AND robust.

**The structural argument for the catalog.** Cycle 5's closed-axis record is unambiguous: every *input-side* lever (features ×4 families, derivative data, on-chain data) and every *estimator-side* lever (model architecture, training objective, label class, universe) has failed to lift the thin v3 signal. /105 is the first axis to attack the **estimand** — what the model is asked to predict. The IS-predictive evidence (a re-framed label the existing features predict 31-52% better) is the first positive structural signal in the post-bootstrap v3 record since iter-v3/025's `regime_momentum_signed_5d`. If the backtest confirms it, the lesson generalizes: when every input and estimator lever is exhausted, the productive frontier is the prediction problem's *geometry*. If it fails, the lesson is equally sharp — a better-predicted IS label that does not transfer to OOS Sharpe means the EXECUTION layer (the fixed triple-barrier exits) is the binding constraint, and the next axis is the trade-construction layer (the /104 Section-7 runner-up: meta-labeling).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

Pre-registered, in probability order, for the Phase-6 backtest outcome:

1. **Most likely — EXPLORATION-PROMISING.** The EDA's positive, adversarially-robust IS-predictive signal (capped-grid F-IC ratio 1.31, Wilcoxon p=0.013, the lift broad across 8-11/14 features per symbol and not BCH-only) is the first such signal in post-bootstrap v3. The modal predicted outcome is OOS monthly Sharpe improving over the /060 anchor +0.1403 by ≥ +0.20 with the IS fit holding ≥ +0.60 — a PROMISING EXPLORATION carried to the cycle-5 CONFIRMATION. This is genuinely the modal prediction, not boilerplate: unlike /102/103/104, the IS-predictive screen returned a *positive and robust* verdict.
2. **Second — EXPLORATION-NULL-RESULT or EXPLORATION-SUSPICIOUS.** The IS-predictive lift is modest (+31% on a low base IC), and the EXECUTION layer is unchanged. A plausible second outcome: the better-framed label re-shapes the model's direction calls but the unchanged triple-barrier exits cap the realized benefit, leaving OOS roughly at the anchor (NULL-RESULT) — or the re-selected roster picks up a duration bias (→ SUSPICIOUS via F5). The structural read if this happens: the label is not the binding constraint, the exit layer is.
3. **Third — EXPLORATION-NEGATIVE via F1/F2/F3.** A lower-probability tail: the re-framed label, while better-predicted in-sample, does not generalize OOS — the trend-scanning label's IS-predictive edge is itself partly an IS artifact and the OOS book regresses. F2 (IS-collapse) is specifically predicted UNLIKELY: /102 collapsed IS because a 15th feature widened the Optuna search space; /105 adds NO feature and does not widen the search space — the IS-collapse mechanism is structurally absent.
4. **Fourth — EXPLORATION-INERT via F6 (saturation).** Least likely: the label change does not propagate to the fitted models and the OOS roster barely moves. The behavioral-effect predictor (Section 4) argues against this — the training target differs on a substantial fraction of bars, so the fits should differ substantially.

**The honest meta-prediction:** /105 is the first v3 EXPLORATION in a long run where the EDA evidence genuinely points toward a PROMISING backtest outcome rather than toward confirming a known failure. If the backtest does NOT confirm it, the most informative reading is structural — the label was not the constraint, and the trade-construction/exit layer is the next axis.

---

## Section 8 — Classification Taxonomy (LOCKED, disjunctive precedence)

Evaluated in Phase 8 against the Phase-7 OOS results, in this precedence order (first match wins). Anchor = /060 (3-seed EXPLORATION-mode; IS +0.8325 / OOS +0.1403).

1. **BLOCKED** — Critic Phase-7.5 OVERALL=BLOCK (a methodology defect — e.g. a look-ahead leak in the trend-scanning label, or an embargo error). NO-MERGE.
2. **NEGATIVE** — Falsifier F1 OR F2 OR F3 fires. NO-MERGE; record the trend-scanning label as NEGATIVE in Dead Ideas with the specific failure mode.
3. **SUSPICIOUS** — Falsifier F5 fires (trade-selection sub-channel duration gap, OR IS/OOS daily-Sharpe ratio outside [0.2, 5]). NO-MERGE; non-advancing.
4. **INERT** — Falsifier F6 fires (the OOS roster changes < 10% — the label re-framing did not propagate). NO-MERGE.
5. **NULL-RESULT** — the run completes, no falsifier fires, but the OOS monthly Sharpe does not clear the /060 anchor +0.1403 by ≥ +0.20 (the cycle-1/5 OOS-PASS gate) — the label change is real but does not lift the book. NO-MERGE; documented.
6. **PROMISING** — none of F1-F6 fires AND OOS monthly Sharpe improves over the /060 anchor +0.1403 by ≥ **+0.20** AND IS monthly Sharpe ≥ **+0.60** AND the per-symbol picture is sign-consistent (not BCH-only). A PROMISING EXPLORATION does **NOT** update `BASELINE_V3.md`; it is carried to the cycle-5 CONFIRMATION (iter-v3/106+ slot) for 10-seed multi-seed validation against /059. **This is the predicted modal outcome.**

`BASELINE_V3.md` baseline metrics are **NOT** edited by this EXPLORATION regardless of outcome (the `v0.v3-082`…`v0.v3-104` closeout-marker pattern; per `feedback_v3_baseline_update_policy.md` only a CONFIRMATION updates the baseline). Tag `v0.v3-105` is a closeout marker only.

---

## Section 9 — Library Stack + Integration-Test Mandate

**Library stack: no new library.** The trend-scanning label uses only `numpy` (the OLS slope + t-statistic is a closed-form least-squares computation — no `statsmodels` call needed, and a closed-form fit is faster and has no external-API surface). The EDA scripts use `numpy`, `pandas`, `scipy.stats` (`spearmanr`, `wilcoxon`) — all already pinned. Pinned versions inherited from /059: Python 3.13, lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1.

**Integration-test mandate** (per `feedback_v3_methodology_axis_integration_test.md` — the label change adds a code path through `label_trades` → `LightGbmStrategy` → the runner, so it needs end-to-end coverage; a unit test on the OLS math in isolation is insufficient):

1. **Unit test** — new `tests/strategies/ml/test_trend_scanning_label_mode.py` (the `test_fixed_horizon_label_mode.py` sibling): (a) `label_trades(label_mode="trend_scanning", trend_scan_grid=(5,8,13,21))` on a synthetic OHLCV frame returns labels in {−1,0,+1} and the selected horizon is always in the grid; (b) **hard causality** — removing N bars beyond `max(grid)` from the end of the frame leaves every earlier bar's label bit-identical (`max_abs_diff == 0`); (c) on a synthetic monotone-up series every bar labels `+1`, on a monotone-down series every bar labels `−1`; (d) `label_mode="triple_barrier"` (no `trend_scan_grid`) is **byte-identical** to the pre-change behavior — the v1/v2 backward-compat assertion.
2. **Integration smoke test** — a short `LightGbmStrategy` train on one (symbol, walk-forward month) cell with `label_mode="trend_scanning"`, asserting the model trains, emits a per-bar score, and the trained-model bundle is well-formed with the 14-feature stack.
3. **Phase-6 pre-flight** — the Engineer verifies `ITERATION_LABEL == "v3-105"`; `len(V3_FEATURE_COLUMNS) == 14` (UNCHANGED — no feature added); `label_mode == "trend_scanning"` and `trend_scan_grid == (5,8,13,21)` reach the `label_trades` call; `REQUIRED_GAP == 66` and `compute_embargo_candles(10080, 480) == 22` are UNCHANGED (the grid max 21 == incumbent timeout); the track-isolation greps are clean; the BCH/LDO/TRX parquet `close_time` freshness + forming-candle checks pass.

**Smoke test in this brief** (the Section-9 end-to-end requirement): the Engineer runs `label_trades` with `label_mode="trend_scanning"` on a real BCH IS slice and confirms (a) the label-distribution matches the EDA's T4 numbers within sampling tolerance, (b) the hard-causality test passes, (c) a one-cell `LightGbmStrategy` train completes — before launching the full 3-seed backtest.

**ADF / IC gates:** no feature is added — the 14 `V3_FEATURE_COLUMNS` are bit-identical to /059, so the per-feature ADF gate and the Critic-Check-4 inter-family IC gate are inherited unchanged and need no re-evaluation. The label is the prediction target, not a feature; it is not subject to the feature ADF gate.

---

## Section 10 — QR Audit Trail

Per `feedback_v3_axis_selection_quant_discipline.md`, axis selection must be QR-led with a committed `analysis/iteration_v3-NNN/*.py` EDA basis before the brief.

- **Axis origin.** The trend-scanning label axis is the iter-v3/104 closeout's **Recommendation #1 (TOP)** — pre-registered there by the QR with the explicit F-HORIZON / F-IC / F-RATE gating-EDA mandate. It is not an orchestrator ad-hoc pick: the /100→/104 closeout chain converged on label geometry as the one un-attacked structural frontier, and /104 Section 7 named the trend-scanning label specifically (López de Prado, MLAM §5.4) with the pre-registered gates this brief's EDA evaluates. No orchestrator pick was superseded; the QR Audit Trail records a direct continuation of the prior diary's QR recommendation.
- **QR EDA basis (committed BEFORE this brief, commit `857e176`):**
  - `analysis/iteration_v3-105/trend_scanning_gating_eda.py` — the F-HORIZON selected-horizon distribution (T1), the F-IC 14-feature feature→label IC comparison vs the incumbent (T2/T5), quartile-resolution sign-stability (T3), F-RATE label balance (T4). Outputs `T1`–`T5` CSVs.
  - `analysis/iteration_v3-105/trend_scanning_robustness.py` — the longest-wins degeneracy probe via an extended grid (R1), per-symbol F-IC decomposition (R2), the 42-cell paired Wilcoxon significance (R3). Outputs `R1`–`R3` CSVs.
  - `analysis/iteration_v3-105/trend_scanning_grid_sensitivity.py` — the DECISIVE check: the F-IC lift under a grid CAPPED at the incumbent 21-candle horizon (G1/G2), removing the longest-wins confound. Outputs `G1`/`G2` CSVs.
- **The apples-to-apples discipline — explicit.** The incumbent /059 triple-barrier label in the EDA is reconstructed with the EXACT production rule (`label_trades(label_mode="triple_barrier", use_atr=True, atr_tp=2.0, atr_sl=1.0, timeout=21 candles, fee_pct=0.1)`, ATR in price units = `close × natr_21_raw / 100`). The trend-scanning vs triple-barrier IC is computed on the SAME shared-support rows (IS-window ∩ trend-scanning-has-label ∩ incumbent-non-tail). The comparison is not against an idealized incumbent — it is against the literal /059 label the production runner builds.
- **The GO recommendation — and why it differs from /103/104.** /103 and /104 recommended NULL-AT-EDA because their IS-predictive screens returned conclusive *negative* verdicts (INERT, rank 15/15). /105's screen returns a *positive and adversarially-robust* verdict: a capped-grid feature→label IC lift of +31% (Wilcoxon p=0.013), broad across 8-11/14 features per symbol, that survived the longest-wins degeneracy probe. The GO is earned by the evidence, not asserted. The honest residual uncertainty (Section 7): the lift is modest on a low IC base and the EXECUTION layer is unchanged, so a NULL-RESULT is the credible second outcome — which is why the brief proceeds to the backtest experiment rather than claiming the result.
- **Setup commit SHA:** _(this research brief — backfilled by the orchestrator at the phase 5.5 gate)_. EDA commit SHA: `857e176` (3 scripts + 10 result CSVs).
- **NO CHEATING:** `OOS_CUTOFF_DATE` / `training_months` untouched; 8h candles, BCH/LDO/TRX universe, `V3_EXCLUDED_SYMBOLS` unchanged; all Phase 1-5 EDA strictly IS-only (`open_time < OOS_CUTOFF_MS`, verified in all 3 committed EDA scripts); the QR did not inspect the post-cutoff OOS — the QR sees OOS for the first time in Phase 7.
