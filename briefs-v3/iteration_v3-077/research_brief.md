# iter-v3/077 — Research Brief

**Cycle 2 EXPLORATION #7 of 10. Axis: PASSIVE-DIAGNOSTIC — per-feature conditional-orthogonality instrumentation (bit-identical roster).**

---

## Section 0 — Data Split Declaration

- **IS window**: data start → `OOS_CUTOFF_DATE` (2025-03-24). IMMUTABLE.
- **OOS window**: `OOS_CUTOFF_DATE` → data end. The QR does not see OOS results until Phase 7.
- **training_months**: 24. IMMUTABLE.
- **Walk-forward**: `generate_monthly_splits` applies `compute_embargo_candles(10080, 480) = 22` candles; `train_end_ms = test_start_ms - embargo_ms`.
- **Universe**: BCH, LDO, TRX (V3_MODELS unchanged; REQUIRED_GAP = 66 = (21+1) × 3).
- **Sacred constants**: `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24` — UNCHANGED. No `start_time` change.

> **Walk-forward lookahead bug carry-over.** Per `feedback_v3_walkforward_lookahead_bug.md`, the v3 worktree carries the pre-main-`5566a69` walk-forward state and BASELINE_V3.md states the /059 anchor inherits the fix at `e149e9d` (`train_end_ms = test_start_ms - embargo_ms`). iter-v3/077 inherits the same post-fix state — no walk-forward change. Absolute Sharpe values across all v3 iterations remain bias-comparable (same embargo); deltas vs /060 are the load-bearing quantity.

## Section 0.5 — Iteration Type Declaration

- **TYPE**: EXPLORATION — cycle 2 #7 of 10 (iter-v3/071–080 = cycle 2 EXPLORATIONs; iter-v3/081 or later = the SEPARATE cycle 2 CONFIRMATION per `feedback_v3_strict_10_to_1_cadence.md` — the 10th EXPLORATION is NOT collapsed into the CONFIRMATION).
- **Axis category**: **PASSIVE-DIAGNOSTIC** — a reporting/instrumentation-only change. The single primary axis is a new report CSV (`conditional_orthogonality.csv`) emitted from the already-trained models; the trade roster is provably bit-identical to /060. This is BASELINE_V3.md cycle-2 candidate #3 (the dedicated IS-drag attribution / "is the tension escapable" axis), elevated by the cycle-2 0/6-PROMISING state and the Critic /076 Rec #1 (a NEW feature now requires a conditional-orthogonality map that does not yet exist — this iteration builds it).
- **Run mode**: `--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3` (ENSEMBLE_SEEDS[0:3], outer=42 lineage subset), `--n-trials 35`. Per `feedback_v3_unified_10seed_baseline.md` EXPLORATION/CONFIRMATION mode separation.
- **Run command**: `uv run python run_baseline_v3.py --exploration --clean-oof`
- **Anchor**: iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403). Confirmed valid — see Section 2.1.
- **Wall-clock target**: bit-identical to /060's run (the only delta is one additional report CSV computed from already-trained models in O(features × symbols) time). **Estimated wall-clock ≈ /060 ≈ 1.0–1.3h** — well within the 2h EXPLORATION cap.
- **Type justification (1–2 sentences)**: Cycle 2 is 6/10 done with 0 clean PROMISING and 3 escalating SUSPICIOUS-OOS-DOMINANT outcomes; the load-bearing meta-question per the /076 diary Section 11 is whether the IS-up/OOS-down tension is escapable at all, and the Critic /076 Rec #1 mandates that any NEW feature first be validated against a conditional-orthogonality map that does not yet exist. A PASSIVE-DIAGNOSTIC iteration is the only candidate whose SUSPICIOUS probability is a provable near-zero (bit-identical roster) AND it produces the conditional-orthogonality tooling /078–/080 + the CONFIRMATION need.

## Section 1 — Hypothesis

Emitting a per-feature **conditional-orthogonality map** — the correlation of each baseline feature's monthly model-split-allocation (gain-importance share) with the BTC monthly regime label — characterizes which of the 14 baseline features are already regime-loaded, and (paired with the IS regime-stratified attribution) tests the cycle-2 meta-question of whether the IS drag is a holding-time-escapable problem or a directional-quality problem, while the trade roster stays provably bit-identical to /060 so the iteration cannot itself produce a SUSPICIOUS outcome.

This is a **diagnostic hypothesis**, not a performance hypothesis: the iteration's deliverable is the conditional-orthogonality map + the escapability characterization, NOT an IS/OOS Sharpe lift. The expected and intended classification is **NULL-RESULT** (Section 7).

## Section 2 — IS-Only Numerical Evidence

EDA committed at SHA `313d3c0` (`analysis/iteration_v3-077/axis_selection_eda.py` + 10 output files). All tables computed IS-data-only on the /060 EXPLORATION-mode roster + the v3 feature parquets; the per-month conditional-orthogonality models train on the 14-feature anchor stack over the IS-window months only. The EDA's NO-OOS-TUNING self-audit (an AST scan for OOS-metric live identifiers) returns PASS.

### Section 2.1 — T0 Anchor-value declaration

Every anchor value is byte-exact from `reports-v3/iteration_v3-060/comparison.csv`.

| Metric | /060 value | Source |
|---|---:|---|
| IS monthly Sharpe | **+0.8325** | `comparison.csv` monthly_sharpe in_sample |
| OOS monthly Sharpe | **+0.1403** | `comparison.csv` monthly_sharpe out_of_sample |
| OOS/IS monthly Sharpe ratio | **0.1685** | `comparison.csv` monthly_sharpe ratio |
| IS n_trades | 159 | `comparison.csv` n_trades in_sample |
| OOS n_trades | 102 | `comparison.csv` n_trades out_of_sample |
| IS win_rate | 31.4465% | `comparison.csv` win_rate in_sample |
| OOS win_rate | 39.2157% | `comparison.csv` win_rate out_of_sample |

### Section 2.2 — T1: IS regime-stratified attribution (DELIVERABLE 2 — the reframing finding)

The /060 monthly PnL stratified by the BTC monthly regime label (a month is BULL if ≥50% of its BTC 8h bars have `close[t-1] > SMA_270[t-1]`, else BEAR/CHOP — the established /075 macro-regime classifier; see Section 10 PARAMETER 2):

| Stratum | n_months | total_pnl% | mean_monthly_pnl% | monthly_sharpe | pct_positive_months | n_trades |
|---|---:|---:|---:|---:|---:|---:|
| **IS_BEAR_CHOP** | 15 | +38.39 | +2.56 | **+1.2909** | 46.7% | 55 |
| **IS_BULL** | 18 | +13.50 | +0.75 | **+0.4100** | 33.3% | 104 |
| OOS_all (INFORMATIONAL) | 14 | +5.50 | +0.39 | +0.1403 | 50.0% | 102 |

**This is a counterintuitive, cycle-reframing finding.** When stratified by the BTC monthly regime, **the IS drag is in the BULL months (Sharpe +0.41, 33% positive), NOT the bear/chop months (Sharpe +1.29, 47% positive).** The /074 brief EDA PART 1 — which 3 prior iterations (/074, /075, and the /076 framing) chased as "the IS bear/chop drag, monthly Sharpe −0.0242" — used the *strategy's own trade-level regime tag*, a different and miscalibrated label. Under a clean calendar/price BTC-regime label, the drag is the IS bull months where the strategy under-performs the bull tape. Three cycle-2 iterations targeted a stratum that is not, in fact, the structural drag.

### Section 2.3 — T2: IS drag decomposition

Per-symbol / per-regime / per-exit-reason decomposition of the 159 IS trades:

| Cut | n_trades | win_rate% | net_pnl% | win_mean_dur | loss_mean_dur |
|---|---:|---:|---:|---:|---:|
| symbol=BCHUSDT | 73 | 45.2 | +79.45 | 10.21 | 4.08 |
| symbol=LDOUSDT | 11 | 27.3 | −11.44 | 4.33 | 5.12 |
| symbol=TRXUSDT | 75 | 29.3 | −23.04 | 8.95 | 4.77 |
| regime=BULL | 104 | 32.7 | −0.49 | 9.09 | 4.90 |
| regime=BEAR/CHOP | 55 | 43.6 | +45.45 | 9.92 | 3.68 |
| exit_reason=stop_loss | 101 | 0.0 | −316.27 | — | 4.52 |
| exit_reason=take_profit | 49 | 100.0 | +332.07 | 7.31 | — |
| exit_reason=timeout | 9 | 100.0 | +29.16 | 21.00 | — |

The IS bull months carry 104 of 159 trades at a 32.7% win rate and net −0.49% — the strategy trades the most in bull months and barely breaks even there. 64% of all IS exits are stop-losses.

### Section 2.4 — T3/T4: conditional-orthogonality map (DELIVERABLE 1 — the Critic /076 Rec #1 tool)

For each of the 14 baseline features, a walk-forward LightGBM is trained per (symbol, IS month) on the anchor stack; the per-month GAIN-importance SHARE (the model's split allocation — the closest available proxy for SHAP attribution; SHAP is not in the v3 library stack) is correlated with the BULL=1 / BEAR-CHOP=0 monthly regime indicator. A near-zero correlation = the model allocates the feature comparably across regimes (conditional regime-orthogonality); a large |corr| = the model's *use* of the feature is regime-loaded (the /076 failure signature). 2086 (symbol, month, feature) importance rows; flag ceiling = a-priori 0.35 (reused verbatim from the /076 marginal-T3 ceiling so the conditional map is directly comparable to /076's marginal map):

| Feature | corr_portfolio_pooled | max_abs_corr | conditionally regime-loaded (>0.35) |
|---|---:|---:|:--|
| btc_ret_14d | +0.3591 | **0.4803** | **YES** |
| hurst_diff_100_50 | +0.2798 | **0.4416** | **YES** |
| max_dd_window_50 | −0.0757 | **0.4339** | **YES** |
| range_realized_vol_50 | −0.1737 | **0.3704** | **YES** |
| ret_skew_200 | −0.2362 | 0.3319 | no |
| ret_kurt_50 | −0.1372 | 0.3132 | no |
| ret_skew_50 | +0.1200 | 0.2851 | no |
| ret_autocorr_lag1_50 | −0.0116 | 0.2749 | no |
| sym_vs_btc_ret_7d | +0.1972 | 0.2651 | no |
| hurst_100 | −0.1349 | 0.2118 | no |
| regime_momentum_signed_5d | +0.0582 | 0.2092 | no |
| ret_kurt_200 | −0.0221 | 0.1996 | no |
| ema_spread_atr_20 | +0.0772 | 0.1974 | no |
| vwap_dev_20 | −0.0600 | 0.1538 | no |

**4 of the 14 baseline features are already conditionally regime-loaded** (max |corr| > 0.35): `btc_ret_14d` (0.48 — unsurprising, it is literally a BTC-trend feature), `hurst_diff_100_50` (0.44), `max_dd_window_50` (0.43), `range_realized_vol_50` (0.37). The one engineered feature `regime_momentum_signed_5d` is clean at 0.21. This is the first conditional-orthogonality map for the baseline stack — the exact instrument the Critic /076 Rec #1 named, now computed.

### Section 2.5 — T6: escapability synthesis

| Finding | Value |
|---|---:|
| IS win-trade mean duration (candles) | 9.431 |
| IS loss-trade mean duration (candles) | 4.525 |
| win/loss duration ratio | **2.084** |
| IS stop_loss exit share | 0.6352 |
| IS win-rate BULL months (%) | 32.7 |
| IS win-rate BEAR/CHOP months (%) | 43.6 |
| worst IS regime stratum | IS_BULL |
| diagnosis: directional-quality problem? | **YES** |

Win trades are held **2.08× longer** than loss trades, and 64% of exits are stop-losses. The mechanical reading: at entry the model cannot tell a future-winner from a future-loser; future-winners then ride to TP/timeout (long duration), future-losers stop out fast (short duration). This is the *signature* the holding-time SUSPICIOUS channel exploits — any axis that lengthens holding time mechanically over-weights the future-winners (regime-favorable in OOS). It also means the IS drag is a **directional-quality problem** — better entry discrimination — which is structurally NOT addressable by a holding-time mechanism (channel (a)) or a post-gate macro classifier (channel (b)). It needs a feature or an M2 that improves entry discrimination — and the conditional-orthogonality map (Section 2.4) is the tool that lets a future iteration pick such a feature against measured fact.

## Section 3 — Proposed Changes

Exactly **TWO** changes. ONE is the single primary axis; the other is a mandatory baseline-restore (NOT a second varied axis).

### 3.1 — PRIMARY AXIS: per-feature conditional-orthogonality report instrumentation

A new function `_write_conditional_orthogonality(model_pairs, report_dir, regime_label)` is added to `run_baseline_v3.py` and called immediately after `_write_feature_importance` (the existing call site). It:

1. Reads the per-month per-feature GAIN importance from the trained `model_pairs` (the same `model_pairs` object `_write_feature_importance` already consumes; for each `(cfg, strat)` it unwraps `strat.inner._models` and reads `model.feature_importances_`).
2. Builds the BTC monthly regime label (BULL / BEAR-CHOP) via the past-only SMA-270 classifier (PARAMETER 2 — Section 10).
3. Correlates each feature's per-(symbol, IS-month) importance share with the BULL indicator.
4. Writes `reports-v3/iteration_v3-077/conditional_orthogonality.csv` with columns `feature, corr_portfolio_pooled, corr_<SYM>×3, max_abs_corr, conditionally_regime_loaded`.

**This instrumentation does NOT touch the model, the feature set, the labeling, the risk gates, the Optuna search, or the ENSEMBLE_SEEDS.** It reads already-trained models and emits a CSV. The runner's existing `_write_feature_importance` already reads `feature_importances_`; this is the same data, re-projected against the regime label. There is no `RiskV2Config` change, no `V3_MODELS` change, no labeling change.

> **Implementation note for the Engineer.** If the trained-model objects available at the report stage carry only the LAST walk-forward month's models (the lazy-monthly-training pattern — `_write_feature_importance` reads `model_importance_last_month_*`), the per-month conditional map cannot be reconstructed at the report stage from those objects alone. In that case the instrumentation emits a **last-month-only** conditional-orthogonality row set (one importance vector per symbol, projected against that month's regime tag is degenerate) — and instead emits the EDA's full per-IS-month map as a committed artifact reference. The Engineer must, in the engineering report, state explicitly which of the two the shipped `conditional_orthogonality.csv` contains. Either way the **trade roster is unaffected** — this is purely a report-emission detail. The brief's diagnostic deliverable (the full per-month map) is already committed in the EDA at `analysis/iteration_v3-077/T3_conditional_orthogonality.csv`; the report CSV is the runner-integrated companion.

### 3.2 — MANDATORY BASELINE-RESTORE: revert /076's `range_efficiency_50`

`V3_FEATURE_COLUMNS_TOP_N` is reverted **15 → 14** — `range_efficiency_50` is removed, restoring the BASELINE_V3 /059/060 anchor 14-feature stack. This is required because /076 was SUSPICIOUS-OOS-DOMINANT (non-advancing) and the Kaufman path-efficiency axis is now CLOSED across two data points (BASELINE_V3.md "Dead Ideas"). Reverting it returns /077 to the /060 baseline state so the diagnostic measures the canonical anchor. This is a **baseline-restore, NOT a second varied axis** — it returns the feature set to the state every cycle-2 EXPLORATION /071–/075 ran on.

Affected code: `src/crypto_trade/features_v3/__init__.py` (`V3_FEATURE_COLUMNS_TOP_N`), `run_baseline_v3.py` pre-flight assertions (count 15→14; `range_efficiency_50` presence assertion removed; `efficiency_ratio_50`/`vol_adj_autocorr` bans retained), and the test files asserting the 15-count (`test_v3_feature_count.py`, `test_features_for_symbol.py`, `test_hurst_drift_50_200_universal.py`). `ITERATION_LABEL` → `"v3-077"`.

### 3.3 — Single-axis discipline

The brief declares exactly TWO changes: (1) the conditional-orthogonality report instrumentation — the single primary axis; (2) the mandatory revert of /076's `range_efficiency_50` — a baseline-restore to the /060 14-feature state, NOT a second varied axis. No feature is added. No labeling change. No risk-gate change. No model-architecture change.

## Section 4 — Expected OOS Impact

### 4.1 — Predicted IS / OOS deltas (mechanical identities)

The PASSIVE-DIAGNOSTIC axis emits a report CSV from already-trained models and reverts /076's feature back to the /060 14-feature anchor. The Phase-6 backtest therefore runs the **byte-identical /060 configuration** — same 14-feature stack, same labeling, same risk gates, same `ENSEMBLE_SEEDS`, same Optuna search. The trained models are deterministically identical to /060's; the trade roster is **bit-identical to /060**.

| Metric | Predicted /077 | vs /060 anchor | Basis |
|---|---:|---:|---|
| IS monthly Sharpe | +0.8325 | **Δ 0.000** | bit-identical roster → identical comparison.csv |
| OOS monthly Sharpe | +0.1403 | **Δ 0.000** | bit-identical roster |
| OOS/IS monthly Sharpe ratio | 0.1685 | identical | mechanical identity |
| IS n_trades | 159 | 0 | deterministic models |
| OOS n_trades | 102 | 0 | deterministic models |

This is **not a confidence interval** — it is an algebraic identity. /077 reproduces /060 exactly. (One operational caveat the Critic should note: /076's run executed on the 15-feature stack; /071–/075 ran on the 14-feature anchor; /060 is the 14-feature anchor. /077 reverting to the 14-feature anchor returns to the /060 configuration exactly — so the bit-identity claim is "/077 == /060", verified against the /060 roster, not against /076.)

### 4.2 — Falsifier

**The diagnostic hypothesis is falsified if the Phase-6 /077 trade roster is NOT bit-identical to /060** — i.e. if IS n_trades ≠ 159, OOS n_trades ≠ 102, or any `(symbol, open_time)` trade differs. Such a divergence would NOT be regime-loading — it would be a Phase-6 wiring defect (an unintended config drift). It is a falsifier of the iteration's PASSIVE-DIAGNOSTIC framing, to be diagnosed and fixed, not interpreted as signal.

### 4.3 — Behavioral-effect predictor (mandated by `feedback_v3_axis_saturation_predictor.md`)

The behavioral-effect prediction is a **mechanical identity**: the axis changes **0 IS trades and 0 OOS trades**. The added trade set and the removed trade set are both EMPTY. Falsifier: any non-zero roster delta → Phase-6 wiring defect (Section 4.2). This is not a "saturated axis" in the `feedback_v3_axis_saturation_predictor.md` sense (an axis whose parameter is outside the data-extent sensitivity band) — it is a deliberately zero-behavioral-effect axis: a PASSIVE-DIAGNOSTIC. The diagnostic VALUE is in the report CSV + the EDA, not in a roster change. This is the legitimate exception the `feedback_v3_axis_saturation_predictor.md` rule contemplates ("when the predictor says the axis is saturated, SKIP it" — here the predictor says the axis is zero-effect *by design*, and the EDA's already-committed diagnostic tables are the deliverable).

### 4.4 — Holding-time-effect predictor + added-vs-removed sub-channel (mandated by `feedback_v3_is_oos_regime_divergence.md` + Critic /076 Rec #2)

Both holding-time channels are **mechanical identities** (T5):

| Channel | Predicted | Falsifier |
|---|---|---|
| Full-roster mean/median trade-duration delta vs /060 | **0.000 candles** (byte-identical labeling + model → identical per-trade barriers) | >+1.0 candle full-roster shift → Phase-6 wiring defect |
| Added-vs-removed roster-composition mean-duration gap (Critic /076 Rec #2 sub-channel) | **UNDEFINED** — the added set and the removed set are both EMPTY (0 trades added, 0 removed) | any non-empty added/removed set → Phase-6 wiring defect |

The /076 channel (regime-loading via trade SELECTION) **cannot fire**: the model feature set is byte-identical to /060, the seeds are identical, the Optuna search is identical → the models are deterministically identical → there is no re-selection of trades. Both the >+1.0-candle full-roster falsifier AND the added-vs-removed sub-channel falsifier are pre-registered (Critic /076 Rec #2) and both are trivially satisfied; a non-zero observed value is a wiring-defect signal, not a regime-loading signal.

### 4.5 — OOS/IS ratio SUSPICIOUS pre-registration (mandated by `feedback_v3_oos_is_ratio_gate.md`)

**Pre-registered SUSPICIOUS gate: if the /077 OOS/IS monthly Sharpe ratio > 3.0, the axis is classified SUSPICIOUS regardless of absolute OOS Sharpe magnitude.** The canonical ratio definition is the within-iteration `comparison.csv` `monthly_sharpe` ratio column (the value the Section 8 SUSPICIOUS classifier consumes — `feedback_v3_iter074` canonical definition).

**Predicted /077 OOS/IS ratio = 0.1685** — mechanically equal to /060 (bit-identical roster → identical `comparison.csv`). 0.1685 ≪ 3.0. The SUSPICIOUS ratio gate is **mechanically impossible to trip** here: the ratio is an algebraic copy of /060's, and /060's ratio is 0.1685. The SUSPICIOUS-OOS-DOMINANT sub-mode is likewise mechanically impossible — it requires OOS shift ≥ +0.20, and the predicted OOS shift is exactly 0.000. This is the conditional-orthogonality PROOF the Critic /076 Rec #3 demands as the prerequisite to flooring SUSPICIOUS below the cycle-2 50% base rate (Section 7): a bit-identical roster makes the OOS/IS ratio an identity, not an estimate.

## Section 5 — Risk Mitigation

iter-v3/077 ships **no strategy change** — the trade roster, the risk-gate stack, the labeling, and the model are byte-identical to /060. There is therefore no new risk surface to mitigate at the strategy level. The risk-gate stack is the established 7-primitive stack at its /060 configuration (BTC trend kill, vol scaling, ADX, Hurst regime, feature z-score OOD, low-vol filter, hit-rate DISABLED — `RiskV2Config` unchanged).

The only iteration-level risk is a **Phase-6 wiring defect** — an unintended config drift causing the /077 roster to diverge from /060. Mitigation: the Section 4.2 falsifier (roster bit-identity check) is the explicit detector; the Engineer's Phase-6 pre-flight verifies `ITERATION_LABEL`, the 14-feature stack, the reverted assertions, and the unchanged `RiskV2Config`; the Critic Check 8 (hypothesis-implementation alignment) independently audits that the only code delta is the report instrumentation + the feature revert. The reverted /076 feature (`range_efficiency_50`) returning the stack to the /060 14-feature anchor is itself the primary "risk mitigation": it removes the SUSPICIOUS-classified /076 feature.

## Section 6 — Risk Management Design

The 7-primitive v3 risk gate stack is UNCHANGED at its /060 configuration. No primitive is added, removed, re-scoped, or re-thresholded.

| # | Primitive | /077 state | Fire-rate prediction |
|---|---|---|---|
| 1 | BTC trend kill | /060 config (`threshold_pct=15.0`) | identical to /060 |
| 2 | Vol scaling | /060 config | identical to /060 |
| 3 | ADX threshold | /060 config (`adx_threshold=20.0`) | identical to /060 |
| 4 | Hurst regime | /060 config | identical to /060 |
| 5 | Feature z-score OOD | /060 config (`zscore_threshold=2.0`) | identical to /060 |
| 6 | Low-vol filter | /060 config | identical to /060 |
| 7 | Hit-rate | DISABLED (as /060) | n/a |
| — | Regime-conditional kill switch (primitive 9) | DISABLED (CLOSED axis) | not fired |
| — | BTC-trend position-SIZE de-rate (primitive 12) | DISABLED (reverted at /076) | not fired |
| — | Per-symbol PnL cap / drawdown brake | DISABLED (CLOSED axes) | not fired |

Regime coverage: identical to /060 — the diagnostic instrumentation is post-training report emission and does not touch the gate stack. Every gate fires exactly as it did at /060.

## Section 7 — Pre-Registered Failure-Mode Prediction

The expected and **intended** classification is **NULL-RESULT** (probability ≈ 95%). iter-v3/077 is a PASSIVE-DIAGNOSTIC iteration: it emits a report CSV from already-trained models and reverts /076's feature to the /060 14-feature anchor. The Phase-6 backtest reproduces /060 exactly — the trade roster is bit-identical, IS Δ = 0.000, OOS Δ = 0.000. Per the Section 8 disjunctive classifier, a roster bit-identical to /060 with shifts inside the noise band is **NULL-RESULT**. NULL-RESULT here is not a failure — it is the designed outcome: a diagnostic iteration's deliverable is the conditional-orthogonality map + the escapability characterization (the EDA tables T1–T6 + the runner-emitted `conditional_orthogonality.csv`), not a Sharpe lift.

**SUSPICIOUS is mechanically ruled out** (probability ≈ 1%, residual): all three SUSPICIOUS grounds are *structurally* excluded — (a) the labeling is byte-identical to /060 so per-trade duration delta is 0.000 (no holding-time extension); (b) there is no macro classifier (the gate stack is byte-identical); (c) the model feature set + seeds + Optuna search are byte-identical so there is no trade re-selection. The OOS/IS ratio is an algebraic copy of /060's 0.1685, far below the 3.0 gate, and the SUSPICIOUS-OOS-DOMINANT sub-mode requires OOS shift ≥ +0.20 against a predicted 0.000. The residual ≈1% is **not** a regime-loading allowance — it is the probability of a Phase-6 wiring defect (a config drift breaking the bit-identity), which the Section 4.2 falsifier and the Critic Check 8 are designed to catch, and which would be diagnosed as an engineering bug, not interpreted as signal. **This residual-1% SUSPICIOUS weight, deviating below the running cycle-2 50% base rate, is justified by the conditional-orthogonality PROOF of Section 4.5** (a bit-identical roster makes the OOS/IS ratio a mechanical identity, not a probability estimate) — exactly the proof standard the Critic /076 Rec #3 requires for a sub-base-rate weight. The remaining ≈4% covers a benign roster perturbation from an unforeseen non-determinism source (e.g. a floating-point reduction-order change) landing the shifts inside the noise band → still NULL-RESULT or INERT, never SUSPICIOUS.

The genuine *diagnostic* risk — distinct from a classification failure — is that the conditional-orthogonality map proves **uninformative**: if the runner can only emit a last-month-only importance vector (Section 3.1 implementation note), the report CSV is degenerate and the diagnostic value falls back entirely to the EDA's already-committed full per-month map. This is a reporting-completeness risk, not a strategy risk, and the EDA artifact (`T3_conditional_orthogonality.csv`) is the mitigation — the deliverable is already committed.

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (LOCKED)

The /077 classification is the per-brief disjunctive taxonomy, evaluated in this DISJUNCTIVE ORDER (SUSPICIOUS → NULL-RESULT → NEGATIVE → PROMISING → INERT — first match is canonical). All thresholds are LOCKED before the backtest. Anchor = iter-v3/060 (IS +0.8325 / OOS +0.1403). "IS shift" / "OOS shift" = /077 minus /060 monthly Sharpe. "OOS/IS ratio" = the within-iteration `comparison.csv` `monthly_sharpe` ratio column.

**8.1 — PROMISING-AT-EXPLORATION**: IS shift ≥ **+0.10** AND OOS shift ≥ **+0.20** AND `frac_positive_paths` ≥ 0.50 AND not SUSPICIOUS. (Mechanically impossible here — predicted shifts are 0.000.)

**8.2 — NEGATIVE-AT-EXPLORATION** (disjunctive OR): IS shift < **−0.10** OR OOS shift < **−0.20**, AND not SUSPICIOUS. (Mechanically impossible here — predicted shifts are 0.000.)

**8.3 — INERT-AT-EXPLORATION**: both shifts within **[−0.10, +0.10]** IS and **[−0.20, +0.20]** OOS (the noise bands), AND the roster is NOT bit-identical to /060 (≥1 trade differs), AND not SUSPICIOUS. (This fires only if a benign non-determinism perturbs the roster without moving the metrics — Section 7's ≈4% tail.)

**8.4 — SUSPICIOUS** (disjunctive — fires on EITHER ground; SUSPICIOUS takes precedence over NEGATIVE/INERT/NULL-RESULT with no magnitude qualifier):
- **Ratio gate:** OOS/IS monthly Sharpe ratio > **3.0**.
- **SUSPICIOUS-OOS-DOMINANT sub-mode:** IS shift < 0 AND OOS shift ≥ +0.20.
(Both mechanically impossible here — Section 4.5. If SUSPICIOUS fires, it is a Phase-6 wiring defect and the iteration is NO-MERGE pending root-cause.)

**8.5 — NULL-RESULT** (the expected/intended outcome): the /077 trade roster is **bit-identical to /060** — IS n_trades = 159, OOS n_trades = 102, and every `(symbol, open_time)` trade matches — AND IS shift = OOS shift = 0.000. The diagnostic deliverable (the conditional-orthogonality map + the escapability characterization) is produced.

**Evaluation order:** SUSPICIOUS (8.4) → NULL-RESULT (8.5) → NEGATIVE (8.2) → PROMISING (8.1) → INERT (8.3). First match is canonical.

**MERGE / NO-MERGE:** This is an EXPLORATION — it does NOT update BASELINE_V3.md regardless of classification (only a CONFIRMATION-MERGE updates the baseline). "MERGE" at the EXPLORATION level means the Critic certifies the classification clean and the report instrumentation lands on the branch as accretive diagnostic infrastructure (a strictly-accretive, non-compoundable methodology component per `feedback_v3_promising_mechanical_subtype.md` — the conditional-orthogonality report is tooling, not an edge ingredient). A NULL-RESULT diagnostic iteration with the deliverable produced and the bit-identity verified is the intended success. **/077 does NOT advance to the cycle-2 CONFIRMATION bundle as an edge ingredient** — a PASSIVE-DIAGNOSTIC has no edge to bundle; its output is the conditional-orthogonality map that informs /078–/080 axis design + the CONFIRMATION QR's bundle decisions.

An INERT / NEGATIVE / SUSPICIOUS classification (Section 7's tail outcomes) would each indicate a Phase-6 wiring defect breaking the bit-identity, not a genuine strategy result — to be diagnosed, not bundled.

## Section 9 — Library Stack Declaration

Unchanged from the /076 stack (pinned in `pyproject.toml` / `uv.lock`):

- lightgbm 4.6.0
- optuna 4.8.0
- numpy 2.2.6
- pandas 3.0.0
- scikit-learn 1.8.0
- scipy 1.17.0
- statsmodels 0.14.6
- pyarrow 23.0.1

No new library is added. The conditional-orthogonality instrumentation uses only numpy + pandas (already in the stack). SHAP is **not** added — the map uses LightGBM gain-importance share as the split-allocation proxy (the Section 2.4 / Section 3.1 rationale states this explicitly; adding SHAP would be a second axis and is out of scope).

## Section 10 — QR Audit Trail

### 10.1 — Axis selection provenance (per `feedback_v3_axis_selection_quant_discipline.md`)

- **EDA SHA**: `313d3c0` — `analysis/iteration_v3-077/axis_selection_eda.py` + 10 output CSVs. Committed BEFORE this brief.
- **Orchestrator-seeded candidates** (`/076` diary Section 11, non-binding): (1) a conditional-orthogonality-validated NEW feature; (2) a re-scoped meta-labeling M2; (3) a dedicated IS bear/chop regime-stratified attribution (PASSIVE-DIAGNOSTIC).
- **QR axis decision**: candidate **#3 — the PASSIVE-DIAGNOSTIC axis**, augmented to also emit the per-feature conditional-orthogonality map (the Critic /076 Rec #1 tool). The QR did NOT pick candidate #1 (a NEW feature carries the running 50% cycle-2 SUSPICIOUS base rate, and the Critic /076 Rec #1 conditional-orthogonality test requires a map of the existing 14 features that does not yet exist — /077 builds it) or candidate #2 (the M2 veto removing early stop-outs is intrinsically holding-time-extending — channel (a) — and re-scoping it correctly itself needs the conditional-orthogonality map). Candidate #3 is the only candidate whose SUSPICIOUS probability is a *provable* near-zero (bit-identical roster — Section 4.5), and it produces the tooling /078–/080 + the CONFIRMATION require. No orchestrator setup commit was made ad-hoc; the QR EDA backs the axis and this brief is the first setup artifact.

### 10.2 — Per-parameter IS-only / a-priori selection-function disclosure (mandated by Critic /075 Rec #2)

Every design parameter is selected by a function whose inputs are demonstrably IS-only or a-priori. The EDA module docstring carries the same disclosure verbatim; it is reproduced here:

| Parameter | Selection function | Input columns | IS-only / a-priori |
|---|---|---|---|
| PARAMETER 1 — the AXIS (PASSIVE-DIAGNOSTIC instrumentation) | `_pick_axis()` — returns the fixed string; not a sort/filter/argmax over any metric | NONE (data-free) | **a-priori** |
| PARAMETER 2 — the BTC monthly regime label (used in the conditional-orthogonality correlation + the stratified attribution) | `build_btc_monthly_regime()` — month tagged BULL if ≥50% bars have `close[t-1] > SMA_270[t-1]` | BTCUSDT 8h `open_time`, `close` ONLY (a calendar/price label, not an OOS performance metric) | **a-priori** |
| PARAMETER 3 — the conditional-orthogonality flag ceiling (0.35) | a-priori constant `COND_ORTHO_CEILING = 0.35`, reused verbatim from the /076 marginal-T3 ceiling for comparability | NONE | **a-priori** |
| PARAMETER 4 — the EDA per-month training window | a-priori — `training_months = 24`, the SACRED CONSTANT | NONE | **a-priori (sacred)** |

The EDA computes **no** per-candidate OOS counterfactual. The only OOS-window quantity anywhere is the INFORMATIONAL `OOS_all` row of the T1 stratified table — clearly labelled informational and feeding no `sort`, `filter`, `argmax`, or threshold. The EDA carries a `_grep_no_oos_tuning()` self-audit (an AST scan that flags any OOS-metric token used as a live identifier — a `Name`, `Attribute`, `Subscript` key, or non-docstring string `Constant`); it returns **PASS**. **No design parameter was selected on OOS data.**

### 10.3 — Setup commit SHA

- EDA commit SHA: `313d3c0` (`analysis/iteration_v3-077/` — committed before the brief)
- Brief commit SHA: `77d0b62`
- Setup commit SHA: `30cda98` (`run_baseline_v3.py` + `features_v3/__init__.py` + 5 test files — ITERATION_LABEL "v3-077", `_write_conditional_orthogonality` instrumentation, /076's `range_efficiency_50` reverted)
- Phase 5.5 gate SHA: `<to be backfilled by the Engineer>`
