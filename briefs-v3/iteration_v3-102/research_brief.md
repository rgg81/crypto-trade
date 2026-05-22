# iter-v3/102 — Research Brief — Cycle-5 EXPLORATION: WorldQuant-101 formulaic alpha (alpha032) as a 15th v3 engineered feature

**Type:** EXPLORATION (cycle-5 slot #2) — a NEW ENGINEERED FEATURE axis (USER-DIRECTED).
**Branch:** `iteration-v3/102`
**Canonical baseline:** iter-v3/059 (`v0.v3-059`) — per-symbol LightGBM, triple-barrier
ATR 2.0/1.0 + 21-candle timeout, 14-feature `V3_FEATURE_COLUMNS`, IS monthly Sharpe
**+1.0894** / OOS monthly Sharpe **+0.5791**, unified 10-seed ensemble. **Unbeaten at 101 iterations.**
**Axis (ONE variable):** add exactly ONE engineered feature — `alpha032`, a v3-portable
adaptation of WorldQuant Alpha#32 (Kakushadze 2015, arXiv 1601.00991) — to
`V3_FEATURE_COLUMNS`, taking it from 14 to 15 columns. No label change, no model-arch
change, no universe change, no risk-gate change.

---

## Section 0 — Data-Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24`, `OOS_CUTOFF_MS = 1742774400000` — **IMMUTABLE**, not touched.
- `training_months = 24` — **IMMUTABLE**, not touched.
- All Phase 1-5 EDA in this brief is **strictly IS-only**: every script masks
  `open_time < OOS_CUTOFF_MS` before any computation. The triple-barrier label is built
  on the full panel then IS-masked — the forward scan for the last IS rows legitimately
  reads post-cutoff candles, exactly as `labeling.py:label_trades` does; that is the
  production labeler, NOT a feature look-ahead. OOS data was **never read** during axis
  design. Verified in all 4 committed EDA scripts.
- The Phase-6 backtest runs on ALL data via `run_baseline_v3.py`; the reporting layer
  splits at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/`. The QR sees OOS
  results for the first time in Phase 7.
- 8h candles. CPCV n_paths=45, embargo=27, REQUIRED_GAP=66. Walk-forward embargo fix
  (`e149e9d`) inherited unchanged.

## Section 1 — Hypothesis

**The v3 14-feature stack lacks a vwap/price lead-lag term composed with a fast
mean-reversion gap. WorldQuant Alpha#32 is exactly that composition, it ports cleanly to
a per-symbol crypto 8h panel, and the held-out-tail horse race shows it lifts the
per-symbol model's predictive accuracy.**

The user directed (2026-05-18) that this v3 feature axis explore the WorldQuant 101
Formulaic Alphas. The 101 alphas are a library of *composed* operators on OHLCV + vwap +
returns — they are ENGINEERED/COMPOSED features, the Category-2 class v3's history says
outperforms off-the-shelf indicators: iter-v3/025's `regime_momentum_signed_5d`, a
composed feature, is v3's ONLY PROMISING feature post-bootstrap, and iter-v3/098's
off-the-shelf families (order-flow, entropy) were NO-GO. A formulaic alpha is the
strongest available expression of the composed-feature class.

The 101 alphas are largely cross-sectional (`rank` across a universe, `IndNeutralize`
within industry, `scale` over a CS vector). v3 is a per-symbol architecture and the
/088-092 cross-sectional re-architecture is CLOSED. The EDA therefore ported ONLY the
**time-series-pure** alphas (18 of them), screened them on IC, sign-stability, and
redundancy, and then ran a multivariate held-out-tail horse race. The horse-race winner
is **Alpha#32**.

Kakushadze Alpha#32 (verbatim Appendix-A formula):
`scale(((sum(close,7)/7) - close)) + (20 * scale(correlation(vwap, delay(close,5), 230)))`.

It composes two effects a depth-3-5 LightGBM cannot itself compose from the 14
incumbents:
- **Term 1 — a fast mean-reversion gap:** `(7-bar SMA of close) − close`, causally
  re-scaled. How far the close sits below/above its own 1-week average.
- **Term 2 — a slow vwap/price lead-lag:** `20 × correlation(vwap, close lagged 5 bars,
  230-bar window)`, causally re-scaled. Whether the per-bar VWAP and the 5-bar-lagged
  close have been co-moving over a long ~77-day window — a persistent lead-lag structure
  between traded-price and close.

The 14 incumbents carry `vwap_dev_20` (a 20-bar vwap deviation) and momentum terms, but
none carries a **long-window vwap-vs-lagged-close correlation** combined with a
fast SMA-gap. Alpha#32's horse-race lift (Section 2) is evidence the combination is
information the incumbents do not already encode.

## Section 2 — IS-Only Numerical Evidence

All numbers below are produced by four committed EDA scripts under
`analysis/iteration_v3-102/` — `alpha_lib.py` + `alpha_ic_eda.py` + `alpha_redundancy_eda.py`
+ `alpha_horserace_eda.py` (commit `fd3165a`) and `alpha032_deepdive.py` (commit
`6b917f8`) — strictly IS-only.

### The basket — 18 v3-portable time-series-pure formulaic alphas

`alpha_lib.py` ports the time-series-pure subset of the WorldQuant 101: alphas whose
Kakushadze formula uses only time-series operators on a single asset's own
OHLCV/vwap/returns. Adaptation decisions (documented per-alpha in the module):
cross-sectional `rank()` is dropped where it is an outer wrapper of a time-series
quantity (a monotone CS transform does not change a per-symbol model's information);
`Ts_Rank` (the TIME-SERIES rank, per-symbol) is kept; `adv{d}` becomes a per-symbol
rolling dollar-volume mean; `scale()` becomes a causal trailing-window mean-abs
normalization; `IndNeutralize` alphas are skipped entirely (no crypto industry data);
`vwap` is the `quote_volume / volume` per-bar proxy. The basket: alpha006, 012, 023, 024,
028, 032, 034, 035, 043, 046, 049, 051, 053, 054, 068, 084, 101, plus one ENGINEERED
Category-2 variant (`alpha053_regime_signed`).

### T3 — past-only adversarial audit: every alpha is causal (0/54 fail)

Each alpha was recomputed on a panel truncated 50 bars early; the overlap must be
bit-identical (the López de Prado look-ahead test). **0 of 54 (alpha × symbol) cells fail**
— `max_abs_diff_overlap = 0.0` and `nan_pattern_mismatch = 0` everywhere. No alpha in the
basket is look-ahead-contaminated. (Source: `T3_past_only_audit.csv`.)

### T2 — feature→label Spearman IC vs the /059 triple-barrier label (top rows)

Walk-forward-faithful directional IC = Spearman corr of the past-only alpha at bar t with
the {+1 long / −1 short} /059 triple-barrier label of bar t. Reference: the 14 incumbent
`V3_FEATURE_COLUMNS` have thin IC (/096: +0.025 BCH / +0.029 TRX) — thin signal is the v3
baseline.

| alpha | ic_BCH | ic_LDO | ic_TRX | mean_abs_ic | 3-sym sign-consistent |
|---|---:|---:|---:|---:|:--:|
| alpha054 | +0.016 | −0.085 | −0.026 | 0.0422 | NO |
| alpha084 | −0.028 | −0.091 | −0.005 | 0.0412 | YES |
| alpha053 | +0.010 | −0.079 | −0.023 | 0.0373 | NO |
| alpha049 | −0.011 | −0.078 | −0.019 | 0.0359 | YES |
| **alpha032** | **−0.026** | **+0.041** | **+0.040** | **0.0354** | **NO** |
| alpha101 | −0.012 | +0.069 | +0.020 | 0.0334 | NO |
| alpha006 | +0.010 | +0.031 | +0.051 | 0.0306 | YES |

(Source: `T2_alpha_label_ic.csv`, all 18 rows.) The univariate IC is thin for every
alpha — none is a standout. alpha032's mean |IC| 0.0354 is mid-basket; its BCH IC is
negative while LDO/TRX are positive (sign-INCONSISTENT — a fragility note carried to
Section 4/7). **The decisive point: univariate IC is a screen, not the selector** — the
/098 lesson is that IS-CV-IC does not predict multivariate held-out lift. The selector is
the horse race below.

### T4 — IC sign-stability across 4 IS sub-periods

Fraction of the 12 (3-symbol × 4-subperiod) IC cells sharing the dominant sign.
alpha032's sign-stable fraction is **0.583** — middling; the IC sign is regime-sensitive.
The basket leaders here are alpha049 / alpha084 (0.833). (Source:
`T4_ic_sign_stability.csv`.) This is honestly a *weakness* of alpha032 on the univariate
screens — recorded so Section 4/7 weigh it.

### T5 — redundancy vs the 14 incumbent V3_FEATURE_COLUMNS

Max |Spearman| of each alpha vs the 14 incumbents; the v3 family gate is |IC| < 0.70
(ITERATION_PLAN_8H_V3.md Critic Check 4). **0 of 18 alphas fail.** alpha032's max |IC| is
**0.466** with `vwap_dev_20` — comfortably below 0.70, so it is NOT redundant; it shares
some variance with `vwap_dev_20` (expected — both touch vwap) but carries distinct
information. (Source: `T5_redundancy_vs_incumbents.csv`.)

### T6/T7 — the DECISIVE test: multivariate held-out-tail horse race

The OOS-robust selection statistic (the /098 methodology): for each candidate set
S = BASE(14) + one alpha, a nested expanding-window walk-forward over the last 6 IS
months (held-out tail, 6 folds, 22-candle embargo purge, strictly IS); `dShACC` =
paired held-out-tail barrier-label accuracy lift of S over BASE, block-bootstrap 95% CI
(block = 21-bar label horizon); `dPnL` = held-out-tail labeled-PnL lift. BASE held-out
accuracy = 0.5758 over 1530 tail rows.

Top of the horse race (`T6_horserace.csv`, sorted by dShACC):

| alpha | dShACC mean | dShACC 95% CI | dPnL mean | importance share |
|---|---:|---:|---:|---:|
| **alpha032** | **+0.01373** | **[−0.0085, +0.0399]** | **+0.2214** | **0.0325** |
| alpha043 | +0.01242 | [−0.0072, +0.0360] | +0.1653 | 0.0165 |
| alpha034 | +0.00784 | [−0.0118, +0.0294] | +0.2347 | 0.0106 |
| alpha023 | +0.00588 | [−0.0111, +0.0248] | +0.1859 | 0.0065 |
| alpha084 | −0.00392 | [−0.0235, +0.0144] | −0.0145 | 0.0121 |
| alpha006 | −0.00784 | [−0.0261, +0.0124] | −0.0530 | 0.0343 |

**alpha032 leads the basket** on the held-out-tail accuracy lift (+0.01373, the largest
positive) AND on held-out-tail PnL (+0.2214, positive — the accuracy lift translates to an
economic gain), AND on the composite selection score (`T7_selection.csv`: 1.897, rank
1/18). The Script-1/2 IC leaders (alpha084, alpha054, alpha006) actually **underperform
BASE** in the multivariate race — the /098 lesson live: univariate IC does not predict
multivariate held-out lift.

**Honest caveat — recorded, not buried.** No alpha in the basket clears a CI lower bound
> 0; alpha032's CI is [−0.0085, +0.0399], straddling zero. This is the thin-signal v3
reality (the same outcome /096/098 reached). It means the horse race is a SELECTION among
candidates plus a positive-point-estimate GO-band, NOT a CI-confirmed edge. Per the
iteration mandate a NULL-AT-EDA is reserved for a *conclusively-dead* axis (a high bar);
alpha032 has a positive point estimate on BOTH the OOS-robust statistics (dShACC and
dPnL) and is the basket's best — the axis is **inconclusive-but-not-dead**, so it proceeds
to the Phase-6 backtest.

### T8/T9/T10 — alpha032 deep-dive

- **T8 per-symbol held-out-tail lift** (`T8_alpha032_per_symbol.csv`): BCH d_acc
  **+0.0591** (strong, d_pnl +376.6), LDO d_acc **+0.0156** (modest, d_pnl +60.9), TRX
  d_acc **−0.0111** (negative, d_pnl −164.7). **2/3 symbols positive.** The pooled
  +0.01373 lift is genuine but **BCH-led** — a fragility flag, recorded in Section 4
  (F3) and Section 7. It is consistent with the /059 baseline where BCH carries 95.76% of
  IS PnL — but it means a CONFIRMATION must check the lift is not a pure BCH artifact.
- **T9 ADF stationarity** (`T9_alpha032_adf.csv`): alpha032 is ADF-stationary in **3/3
  symbols** — BCH p≈0, TRX p≈0, LDO p=0.0409 (all < 0.05). It **passes the v3 ADF hard
  gate** with no regime-indicator carve-out needed.
- **T10 warm-up** (`T10_alpha032_warmup.csv`): first valid bar 333 (~111 days; the 230-bar
  correlation window dominates), absorbed by the 24-month IS warm-up.

## Section 3 — Proposed Changes (the full implementation spec)

**ONE variable changes: one new engineered feature is added to `V3_FEATURE_COLUMNS`.**

1. **New module `src/crypto_trade/features_v3/formulaic_v3.py`** — a `compute_alpha032`
   function and an `add_formulaic_v3_features` GROUP_REGISTRY entry point.
   - `compute_alpha032(df)` computes
     `scale_ts((sum(close,7)/7 - close), 100) + 20*scale_ts(corr(vwap, delay(close,5), 230), 100)`
     where `vwap = quote_volume / volume`, `scale_ts(x, 100)` divides by the trailing
     100-bar mean-absolute value of `x` (the causal per-symbol port of Kakushadze's
     cross-sectional `scale`), all rolling windows are past-only (`min_periods` = window
     length; `.shift()` for the lag). The reference implementation is
     `analysis/iteration_v3-102/alpha_lib.py:alpha032` + the operators it calls — the QE
     ports that math VERBATIM into the production module.
   - The module is **track-isolated**: no import from `crypto_trade.features` (v1) or
     `crypto_trade.features_v2` (v2). Enforced by the Phase-6 pre-flight grep.
   - Output column name: **`alpha032`**.
2. **`features_v3/__init__.py` — register `formulaic_v3` in `GROUP_REGISTRY`** and add
   `"alpha032"` as the **15th element of `V3_FEATURE_COLUMNS_TOP_N`** (appended after
   `regime_momentum_signed_5d`). `V3_FEATURE_COLUMNS` aliases `V3_FEATURE_COLUMNS_TOP_N`,
   so it becomes the 15-feature stack. `formulaic_v3` needs only `close`, `quote_volume`,
   `volume` — no ordering constraint vs other groups.
3. **`run_baseline_v3.py` — update `_verify_feature_columns`.** The current assertion
   hard-requires `len(V3_FEATURE_COLUMNS) == 14`; the QE updates the expected count to
   **15** and adds an explicit positive assertion `"alpha032" in V3_FEATURE_COLUMNS`. Bump
   `ITERATION_LABEL` to `"v3-102"`. No `common_kwargs` change is needed — the feature is
   added through the registry + column list, not a strategy kwarg.
4. **Feature regeneration.** The QE regenerates the v3 BCH/LDO/TRX feature parquets so
   `alpha032` is present (`uv run crypto-trade features --track v3 --symbols
   BCHUSDT,LDOUSDT,TRXUSDT --interval 8h`). Per `feedback_v3_data_staleness_per_worktree.md`
   the regeneration runs in THIS worktree's `data/`.
5. **No other change.** `V3_MODELS` (BCH/LDO/TRX) unchanged. ATR multipliers (2.0/1.0)
   unchanged. Timeout (21 candles) unchanged. `RiskV2Config` 7-gate stack unchanged.
   `V3_EXCLUDED_SYMBOLS` unchanged (no v1/v2 coin enters). CPCV/embargo/walk-forward
   unchanged. The 14 incumbents are bit-identical to /059.

**EXPLORATION run spec** (per `feedback_v3_cadence_discipline.md` +
`feedback_v3_exploration_n_trials_35.md`): single-seed 3-seed EXPLORATION mode
(`--exploration`, `EXPLORATION_ENSEMBLE_SIZE=3`, `--n-trials 35`). Command:
`uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof`. 2h
EXPLORATION wall-clock cap.

## Section 4 — Expected OOS Impact + Pre-Registered Numerical Falsifiers

**Anchor.** Per `feedback_v3_dsr_mode_artifact.md` and `feedback_v3_cycle1_axis_pass_criteria.md`,
a 3-seed EXPLORATION-mode run is classified against the **3-seed EXPLORATION-mode
reference /060** (IS monthly Sharpe **+0.8325** / OOS monthly Sharpe **+0.1403**), NOT the
10-seed /059 CONFIRMATION baseline. The /101 closeout Lesson 3 made anchor-matching
binding for cycle-5 EXPLORATION briefs — this brief applies it from the start.

**Predicted OOS impact.** The held-out-tail horse race shows a +0.01373 pooled
directional-accuracy lift (2/3 symbols positive). By the rough v3 historical
accuracy→Sharpe sensitivity (the /025 PROMISING precedent: a comparable-scale held-out
lift produced ~+0.84 OOS), a ~1.4pp accuracy lift translates to a **predicted OOS monthly
Sharpe delta of roughly +0.10 to +0.35 vs the /060 anchor's +0.1403** — a predicted OOS
monthly Sharpe band of **[+0.24, +0.49]**. IS monthly Sharpe is predicted approximately
flat to mildly positive (alpha032 is one added feature among 15; T8 shows BCH — the
IS-dominant symbol — gains) — predicted IS band **[+0.78, +1.00]** vs /060's +0.8325.
This is a 3-seed EXPLORATION — the prediction is an estimate, not a gate.

**Pre-registered numerical falsifiers** (these are GATES — distinct from the prediction;
per `feedback_v3_per_symbol_target_axis_falsifier.md`). The axis is FALSIFIED at Phase 7
if ANY of the following fires. Falsifiers are evaluated against the /060 matched anchor.

| # | Falsifier | Fires if |
|---|---|---|
| F1 | Headline OOS regression | OOS monthly Sharpe < **+0.00** (a material drop below the /060 anchor +0.1403 — adding alpha032 made the book net-losing OOS) |
| F2 | IS collapse | IS monthly Sharpe < **+0.60** (a >0.23 drop below the /060 anchor +0.8325 — alpha032 broke the in-sample fit, the /063 mass-expansion failure mode) |
| F3 | BCH-only artifact | the OOS lift is carried entirely by BCH AND BOTH LDO and TRX OOS weighted-pnl REGRESS vs /060 (the T8 fragility flag realized — the +0.01373 lift was a one-symbol artifact, not a generalizable feature) |
| F4 | INERT by importance | `alpha032`'s walk-forward-aggregated gain-importance rank is **last (15/15)** in all 3 per-symbol models OR its combined importance share is below the uniform-parity 1/15 = 0.0667 in all 3 (the tree does not allocate split capacity to it — `feedback_v3_inert_features_at_higher_budget`: an INERT feature added at higher budget actively HARMS OOS) |
| F5 | Mechanical roster-churn | OOS improves but the per-symbol added-vs-removed-trade mean-duration gap exceeds **+1.0 candles** on any symbol with a material OOS lift (the /076 + /101-F5 trade-selection sub-channel signature — the lift is regime-conditioned roster composition, not signal) |

**Behavioral-effect predictor** (per `feedback_v3_axis_saturation_predictor.md`): adding
`alpha032` to the feature set shifts the fitted per-symbol models, so the OOS trade roster
shifts. **Predicted behavioral effect: the OOS trade roster changes by 8-30% vs the /060
3-seed OOS roster (102 trades)** — i.e. roughly 8-31 trades added/removed. If the observed
OOS roster change is **below 5%**, the feature is behaviorally saturated (F4-adjacent) —
classify INERT.

## Section 5 — Risk Mitigation (R1-R5, IS-calibrated, simulated effect)

This axis adds one engineered feature; it does not modify any live risk gate. The R1-R5
stack is inherited from /059 unchanged and is itself the risk mitigation:

- **R1 (cooldowns):** unchanged. Not affected by a feature addition.
- **R2 (drawdown scaling):** the 7-gate `RiskV2Config` stack — vol scaling, ADX, Hurst,
  z-score OOD, low-vol filter, hit-rate (disabled), BTC-trend kill — is unchanged.
- **R3 (OOD detection):** the z-score OOD gate (`zscore_threshold=2.0`) is unchanged. NOTE:
  the OOD gate operates on its own configured feature subset, NOT `V3_FEATURE_COLUMNS`;
  adding `alpha032` does not enlarge the OOD feature set. T9 confirms `alpha032` is
  ADF-stationary in 3/3 symbols, so it does not introduce a non-stationary drift the OOD
  gate would have to absorb.
- **R4 (vol kill-switch):** the BTC-trend kill (`BTC_TREND_CONFIG.threshold_pct=15.0`) is
  unchanged.
- **R5 (concentration cap):** `enable_per_symbol_cap=False` unchanged (per /020 closeout —
  per-symbol PnL caps are CLOSED at catalog level).

**Simulated historical effect of the axis itself.** The T8 deep-dive simulated alpha032's
held-out-tail effect across the last 6 IS months: it lifted held-out side-PnL on BCH
(+376.6) and LDO (+60.9) and reduced it on TRX (−164.7). The feature's net simulated IS
effect is positive but concentration-amplifying (it helps the dominant symbol most) — the
F3 falsifier is the explicit gate against that concentration becoming an OOS failure. No
new gate is introduced, so no new gate needs IS-calibration; the alpha032 feature itself
is the only new component and its simulated effect is the T6/T8 horse-race evidence.

## Section 6 — Risk-Management Design (the deeper structural defense)

The deeper structural argument: a **single-feature addition is the lowest-blast-radius
way to test a new information source**, and it has a built-in risk control — the
`feedback_v3_engineered_features_dont_stack.md` discipline. /102 adds EXACTLY ONE
engineered feature, not a basket. The EDA SCREENED 18 alphas, but the axis is one. This is
deliberate: iter-v3/063's mass expansion (14→46 features) collapsed IS Sharpe −1.38
because a wide stack lets Optuna overfit IS noise; iter-v3/070's lesson is that a
correlated feature steals `colsample_bytree` picks. Adding one feature, validated by a
held-out-tail horse race and an |IC|<0.70 redundancy gate, is the structurally-conservative
move.

The second structural defense is the **ADF gate** (T9: 3/3 stationary) — a non-stationary
feature would silently shift the model's operating point between IS and OOS; alpha032 is
mean-reverting and bounded by its causal `scale_ts` normalization, so it cannot drift the
model the way a trending raw-price feature would. The causal `scale_ts` is itself a risk
control: it bounds the marginal influence of any single bar by normalizing against the
trailing 100-bar mean-absolute value, so a once-in-two-years extreme bar cannot dominate
the feature's range.

The honest risk this axis carries is **concentration** (T8: BCH-led lift, F3 the gate)
and **the thin-signal CI** (Section 2 caveat: no CI clears zero). Both are pre-registered
as falsifiers/caveats rather than hidden — the axis is run as a genuine EXPLORATION
experiment, and a CONFIRMATION (if /102 is PROMISING) would re-validate the BCH-led lift
at 10 seeds before any baseline update.

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most-likely failure mode, pre-registered: INERT (Falsifier F4).** The most probable
non-PROMISING outcome is that `alpha032`'s univariate IC is thin (T2: mean |IC| 0.0354,
sign-inconsistent across symbols) and its sub-period sign-stability is middling (T4:
0.583), so the per-symbol depth-3-5 LightGBM allocates little split gain to it and the
OOS roster barely moves. v3 has a long INERT track record for added features — the 7-FEED
STRUCTURAL VERDICT (/019/023/024/082/085/086 + microstructure /015) found 7 consecutive
non-OHLCV feature families INERT-by-importance. `alpha032` is OHLCV-derived (it is NOT a
new data feed — it is a composition of existing kline columns), which is the one
structural difference from the 7-FEED verdict, and its horse-race importance share
(0.0325) is non-zero — but INERT remains the modal predicted outcome. If F4 fires,
`alpha032` is recorded in BASELINE_V3.md Dead Ideas as "WorldQuant Alpha#32 — INERT as a
v3 per-symbol feature" and the formulaic-alpha axis is closed at one data point.

**Second failure mode: SUSPICIOUS via F5 (roster-churn).** The /101 closeout's Lesson 2
made the F5 trade-selection sub-channel a standard v3 risk: any change that shifts the
fitted model can load a duration factor through *which* trades it selects, paying off
spuriously in a directional OOS window. A feature addition shifts the model, so F5 is
live. The F5 roster-diff (added-vs-removed per-symbol mean duration) is a mandatory
Phase-7 diagnostic.

**Third failure mode: NEGATIVE (F1/F2/F3).** alpha032 could break the IS fit (F2 — the
/063 mass-expansion mode) or be a pure BCH artifact that regresses LDO+TRX OOS (F3 — the
T8 fragility flag realized). The T8 evidence (BCH +0.059, LDO +0.016 — 2/3 positive) is
the main argument against F3, but TRX is already negative in the held-out tail (−0.011),
so F3 is a genuine risk.

**Why this is still worth a backtest** (per the iteration mandate — a NULL-AT-EDA is
reserved for a *conclusively-dead* axis, a high bar): the EDA is deep (5 scripts, 10
tables, 18-alpha basket), the axis was selected by an OOS-robust held-out-tail horse race
(not a univariate IC rank), alpha032 has a **positive point estimate on BOTH OOS-robust
statistics** (dShACC +0.01373, dPnL +0.2214) and is the basket's best, it passes the ADF
and redundancy hard gates, and it is causal (T3 0/54 fail). It is the
"deep-but-not-conclusive" case — the held-out proxy points the right way but its CI
straddles zero — and a held-out single-classifier proxy is not the multi-seed Optuna
backtest. The experiment must run.

## Section 8 — Classification Taxonomy (LOCKED, disjunctive precedence)

Evaluated in Phase 8 against the Phase-7 OOS results, in this precedence order (first
match wins). Anchor = /060 (3-seed EXPLORATION-mode; IS +0.8325 / OOS +0.1403).

1. **BLOCKED** — Critic Phase-7.5 OVERALL=BLOCK (methodology defect). NO-MERGE.
2. **NEGATIVE** — Falsifier F1 OR F2 OR F3 fires (OOS monthly Sharpe < +0.00, or IS
   monthly Sharpe < +0.60, or a BCH-only artifact with LDO+TRX both regressing).
   NO-MERGE; record WorldQuant Alpha#32 as NEGATIVE in Dead Ideas.
3. **SUSPICIOUS** — Falsifier F5 fires (mechanical roster-churn signature) OR a
   structurally-suspicious IS/OOS divergence (IS daily Sharpe / OOS daily Sharpe ratio
   outside [0.2, 5]). NO-MERGE; non-advancing.
4. **INERT** — Falsifier F4 fires (`alpha032` importance rank last in all 3 models or
   sub-parity share in all 3) with no signal lift. NO-MERGE; the formulaic-alpha axis
   closes at one data point.
5. **PROMISING** — none of F1-F5 fires AND OOS monthly Sharpe improves over the /060
   anchor +0.1403 by ≥ +0.20 (the cycle-1/5 OOS-PASS gate from
   `feedback_v3_cycle1_axis_pass_criteria.md`) AND IS monthly Sharpe ≥ +0.60 AND the
   per-symbol picture is sign-consistent with the T8 EDA (the lift is not BCH-only). A
   PROMISING EXPLORATION does NOT update BASELINE_V3.md (only a CONFIRMATION-MERGE does,
   per `feedback_v3_baseline_update_policy.md`); it is carried to the cycle-5 CONFIRMATION
   for 10-seed validation, where the BCH-led-lift concentration risk (T8) is the primary
   thing the CONFIRMATION must re-check.
6. **NULL-RESULT** — the run completes but the outcome fits none of the above cleanly
   (e.g. mixed IS-up/OOS-flat within noise, or OOS up but below the +0.20 PROMISING gate).
   NO-MERGE; documented.

BASELINE_V3.md is **not** edited by this EXPLORATION regardless of outcome (the
`v0.v3-082`…`v0.v3-101` pattern). Tag `v0.v3-102` is a closeout marker only.

## Section 9 — Library Stack + Integration-Test Mandate

**Library stack:** no new library. `compute_alpha032` uses `numpy` and `pandas` rolling
operations (both already dependencies). `statsmodels.adfuller` (already a dependency) is
used only in the EDA, not in production. Pinned versions inherited from /059: lightgbm
4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0,
statsmodels 0.14.6, pyarrow 23.0.1.

**Integration-test mandate** (per `feedback_v3_methodology_axis_integration_test.md` — the
`alpha032` feature adds a code path through a new module + the GROUP_REGISTRY + the
feature-column list, so it needs end-to-end coverage, not just a unit test on the alpha
math):

1. **Unit test** — `tests/features_v3/test_formulaic_v3.py`: assert `compute_alpha032`
   on a synthetic OHLCV frame (a) produces a column named `alpha032`, (b) is past-only —
   recomputing on a frame truncated 50 bars early leaves the overlap bit-identical (the
   T3 audit, as a regression test), (c) the warm-up NaN count matches the 230-bar window
   (~333 bars), (d) raises or returns all-NaN cleanly if `quote_volume` or `volume` is
   missing.
2. **Integration smoke test** — generate v3 features for one symbol end-to-end and assert
   `alpha032` appears in the parquet and in `V3_FEATURE_COLUMNS`; then a short
   `LightGbmStrategy` train on one (symbol, month) cell asserting the model trains with
   the 15-feature stack and `alpha032` is among the columns passed to LightGBM.
3. The Engineer's Phase-6 pre-flight verifies `len(V3_FEATURE_COLUMNS) == 15`,
   `"alpha032" in V3_FEATURE_COLUMNS`, `ITERATION_LABEL == "v3-102"`, and the
   track-isolation grep on `formulaic_v3.py` is empty.

**ADF / IC gates:** `alpha032` is the one new feature. **ADF gate: PASS** — T9 shows
ADF-stationary in 3/3 symbols (BCH/TRX p≈0, LDO p=0.0409). **IC redundancy gate: PASS** —
T5 shows max |IC| 0.466 vs the 14 incumbents, below the 0.70 family gate. `alpha032` is a
Category-2-style COMPOSED feature (Kakushadze's `scale` + `sum` + `correlation` of OHLCV
quantities); the Critic-Check-4 strict |IC| gate is applied in full here and PASSES — no
carve-out is invoked.

## Section 10 — QR Audit Trail

- **Axis selection** was USER-DIRECTED (2026-05-18: explore the WorldQuant 101 Formulaic
  Alphas). The QR did NOT work from a vague summary: the EDA studied the Kakushadze 2015
  paper (arXiv 1601.00991) and the reference notebook, ported the time-series-pure subset
  with each cross-sectional→per-symbol adaptation documented per-alpha in `alpha_lib.py`,
  and selected the single axis alpha by a multivariate held-out-tail horse race — not by
  a univariate IC rank (the explicit /098 lesson). Per
  `feedback_v3_axis_selection_quant_discipline.md` the axis has a committed EDA basis
  (`analysis/iteration_v3-102/`, 5 scripts, T1-T10) authored before this brief.
- **Per `feedback_v3_engineered_features_dont_stack.md`** the /102 axis is exactly ONE
  alpha. The EDA screened a basket of 18, but only `alpha032` is added; same-family /
  sister-feature stacking is deferred to a CONFIRMATION.
- **The user's directive to genuinely research the alphas** was honored: the basket is
  the time-series-pure subset (the cross-sectional and fundamental-data alphas were
  correctly skipped or per-symbol-adapted, not force-fit); alpha032 was selected by the
  decisive OOS-robust statistic, and its weaknesses (thin univariate IC, middling
  sign-stability, BCH-led horse-race lift, CI straddling zero) are recorded honestly in
  Sections 2/4/7 rather than buried.
- **EDA commit SHAs:** `fd3165a` (`analysis(iter-v3/102): WorldQuant-101 formulaic-alpha
  EDA — 3 scripts + T1-T7`) and `6b917f8` (`analysis(iter-v3/102): alpha032 deep-dive —
  T8/T9/T10`).
- **Brief SHA:** this commit (`docs(iter-v3/102): research brief — WorldQuant Alpha#32 as
  a 15th v3 engineered feature`).
- **Setup commit SHA:** the runner + feature-module change (`formulaic_v3.py`,
  `V3_FEATURE_COLUMNS` 14→15, `_verify_feature_columns` count update, `ITERATION_LABEL`
  bump) is the QE's Phase-6 setup commit — to be backfilled here at the Phase 5.5 gate.
