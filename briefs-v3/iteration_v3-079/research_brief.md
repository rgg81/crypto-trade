# iter-v3/079 — Research Brief

**Iteration**: iter-v3/079 — Cycle 2 EXPLORATION #9 of 10
**Branch**: `iteration-v3/079`
**Date**: 2026-05-16
**Axis**: NEW MODEL-ARCHITECTURE — conviction-weighted per-trade position sizing (a conviction-DERATE map driven by the M1 model's own directional confidence). Plus a baseline-restore: `V3_MODELS` reverts from /078's BCH/ADA/TRX back to BCH/LDO/TRX.

---

## Section 0 — Data Split Declaration

The sacred constants are **UNCHANGED**:

```
OOS_CUTOFF_DATE = 2025-03-24       # IMMUTABLE
training_months = 24                # IMMUTABLE
```

- **IS window**: earliest available data per symbol → 2025-03-24. The walk-forward backtest's first trade-eligible month is governed by the 24-month training window plus feature warm-up.
- **OOS window**: 2025-03-24 → present (data extent ~2026-05).
- The QR uses ONLY IS data in Phases 1–5. The walk-forward / CPCV backtest runs on ALL data; the reporting layer splits at `OOS_CUTOFF_DATE`. The QR sees OOS for the first time in Phase 7.
- The EDA `analysis/iteration_v3-079/sizing_axis_eda.py` reads ONLY the `reports-v3/iteration_v3-060/in_sample/trades.csv` IS roster for parameter design (asserted `close_time < OOS_CUTOFF_MS` for every row); it reads the `/060` OOS roster ONCE, in table T8, ONLY to print the OOS trade count for the holding-time degeneracy proof — NO OOS metric selects any design parameter.

### RE-ANCHORING (Critic /077 Rec #1 — adopted at the /077 closeout; re-stated for /079)

The frozen iter-v3/060 EXPLORATION-MODE anchor (IS +0.8325 / OOS +0.1403) is **STALE** — iter-v3/077 (the first iteration since /060 to run the exact /060 14-feature config with no axis) established that it does not reproduce on current code + current data. **iter-v3/079 anchors against the current-code /060-config baseline: IS +0.8236 / OOS +0.2078.** All /079 IS/OOS deltas in this brief are computed against IS +0.8236 / OOS +0.2078, NOT the frozen /060 values.

The anchor gap decomposes exactly and additively (established by /077, `analysis/iteration_v3-077/`, and carried by /078):
- **IS code-drift: −0.0089** — entirely the iter-v3/061 TRX `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` (introduced 16 iterations after /060; a permanent, deterministic offset that floors 13 IS TRX `weight_factor` values).
- **OOS data-extent: +0.0675** — the 2026-05 OOS month that post-dates /060's data fetch (monotonic with calendar time).

This is a methodology correction — a stale reference value replaced by the freshest reproducible no-axis run of the canonical config — **not** a measurement-window change. The OOS-cutoff and start dates are untouched. The /059 CONFIRMATION baseline (tag `v0.v3-059`, IS +1.0894 / OOS +0.5791) is the canonical baseline and is **NOT** the EXPLORATION anchor; it is unchanged and unaffected.

**V3_MODELS confirmation.** /078's universe-revision axis (BCH/ADA/TRX) was SUSPICIOUS-OOS-DOMINANT and the universe-revision axis is CLOSED for cycle 2; LDOUSDT is RETAINED. At /079's setup `V3_MODELS` reverts from /078's BCH/ADA/TRX back to **BCH/LDO/TRX** — the /060 anchor universe. This revert is a **baseline-restore**, not a second varied axis (Section 3.3).

---

## Section 0.5 — Iteration Type Declaration

**TYPE: EXPLORATION** — cycle 2 EXPLORATION #9 of 10.

- Single-axis variation: ONE primary change — a NEW conviction-weighted per-trade sizing primitive in the M1 strategy. The `V3_MODELS` ADA→LDO revert is a baseline-restore of the /078 axis, not a second axis (Section 3.3).
- Run config: `run_baseline_v3.py --exploration --n-trials 35` → `EXPLORATION_ENSEMBLE_SIZE = 3`, 3 outer seeds (`ENSEMBLE_SEEDS` outer=42 lineage subset `[191664963, 1662057957, 1405681631]`). 3-symbol universe (BCH/LDO/TRX). REQUIRED_GAP=66, embargo 22. Total 315 Optuna trials.
- **Wall-clock budget HARD CAP: 2h.**
- This EXPLORATION does NOT update `BASELINE_V3.md` regardless of classification (only a CONFIRMATION-MERGE updates the baseline). It is cycle 2 EXPLORATION #9; the cycle-2 CONFIRMATION is iter-v3/081 or later.
- **Type justification**: an EXPLORATION is the correct vehicle — a NEW sizing primitive is a single-axis structural variation whose multi-seed behaviour the cycle-2 CONFIRMATION must validate before any baseline change. The EXPLORATION's job is to produce the single-axis data point and the per-symbol behavioral attribution the CONFIRMATION QR needs.

---

## Section 1 — Hypothesis

The M1 LightGBM ensemble already computes a per-trade directional confidence (`confidence = max(P(long), P(short))`) but `lgbm.py:get_signal` discards it after the binary confidence-threshold gate and emits a **flat `weight=100` for every surviving trade**. Replacing that flat weight with a monotone, all-a-priori **conviction-DERATE map** — every trade with directional confidence below an a-priori clear-conviction reference (0.65) is sized down toward a half-size floor; trades at/above 0.65 keep full weight — lifts the IS aggregate monthly Sharpe by shrinking marginal-confidence trades (which the EDA shows the current vol-targeting size fails to discriminate) **without** the IS-up/OOS-down regime tension, because a per-trade weight scalar deletes no trade, touches no barrier, and changes no model input (it is holding-time-orthogonal, selection-orthogonal, and feature-orthogonal by construction).

---

## Section 2 — IS-Only Numerical Evidence

All evidence is produced by the committed EDA `analysis/iteration_v3-079/sizing_axis_eda.py` (EDA SHA in Section 10.3) and its eight output tables (`T1`–`T8`) + `summary.csv`. The EDA is IS-data-only; the per-parameter IS-only / a-priori selection functions are disclosed in the EDA docstring and re-stated in Section 10.2. The EDA does TWO things: PART A (T1–T5) FALSIFIES the /078-diary candidate #1 (cross-symbol re-weighting); PART B (T6–T8) is the IS-only evidence for the selected conviction-weighting axis.

### Section 2.1 — PART A: the cross-symbol re-weighting candidate is FALSIFIED

The /078 diary's #1-priority candidate for /079 was a NEW model-architecture axis targeting "the BCH IS-concentration fragility" — a cross-symbol re-weighting (per-symbol-variance-normalized aggregation, or inverse-volatility cross-symbol sizing) to stop BCH's ~77% IS-PnL share from "pinning" the aggregate Sharpe. The QR EDA tested it FIRST and FALSIFIED it.

**T1 — per-symbol IS edge.** The /060-config IS roster, per symbol (calendar-monthly summed `weighted_pnl`):

| Symbol | IS trades | IS monthly-PnL mean | IS monthly-PnL std | IS per-symbol monthly Sharpe | IS wpnl concentration |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 73 | +0.0270 | 0.0692 | **+1.3532** | 150.98% |
| LDOUSDT | 11 | −0.0033 | 0.0632 | **−0.1825** | −3.21% |
| TRXUSDT | 75 | −0.0092 | 0.0320 | **−0.9950** | −47.77% |

The decisive fact: **BCH is the ONLY positive-edge symbol.** LDO and TRX both carry negative per-symbol IS monthly Sharpe. The portfolio IS Sharpe of +0.8236 is BCH's +1.35 *diluted* by two negative sleeves. The /078 framing — "BCH dominates the aggregate Sharpe, so prevent one symbol from dominating it" — is itself a trap: BCH's dominance is the strategy *working*, not a variance artifact.

**T2/T3 — inverse-vol cross-symbol sizing COLLAPSES the IS Sharpe.** Inverse-vol sizing scales each symbol's weight by `median(σ) / σ[symbol]` to equalise variance contributions. T2: because TRX has the *lowest* monthly-PnL std (0.0320), inverse-vol UP-weights TRX by 1.976× — and TRX is the WORST-edge symbol. T3 simulates the resulting portfolio IS monthly Sharpe:

| Configuration | IS portfolio monthly Sharpe |
|---|---:|
| /060-config baseline | +0.8325 |
| inverse-vol cross-symbol sizing | **+0.3021** |
| **Δ** | **−0.5304** |

Inverse-vol sizing is RETURN-BLIND — it equalises variance by amplifying the negative sleeve's drag on the portfolio MEAN. **T4** confirms the mechanism: variance shares equalise to exactly 33.3/33.3/33.3, but the portfolio mean PnL is destroyed. This is a textbook risk-parity failure mode in a universe where 2 of 3 sleeves carry negative edge.

**T5 — the edge-aware sweep shows why per-symbol tuning is ALSO closed.** Down-weighting a negative-edge symbol IS IS-Sharpe-monotonic (down-weighting TRX to 0 lifts IS Sharpe to +1.2147; down-weighting LDO to 0 lifts it to +0.8657). But selecting a per-symbol multiplier by IS-Sharpe-maximization is **OOS-tuning** (`feedback_no_cheating.md` — improve the strategy, not the measurement-fit), and a per-symbol multiplier is the **/078-CLOSED per-symbol-customization pattern** (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`). It is therefore rejected too.

**Conclusion (per `feedback_axis_saturation_predictor.md`): the cross-symbol re-weighting candidate is HARMFUL on IS evidence — the EXPLORATION SKIPS it.** The candidate-#1 family (any cross-symbol re-weighting) is closed by this EDA. The QR pivots to candidate-#3 — a per-trade conviction-weighted sizing primitive.

### Section 2.2 — PART B: the conviction-weighting axis — the codebase finding

The load-bearing, fully-verifiable finding: `lgbm.py:get_signal` computes a per-trade directional confidence from the M1 ensemble's averaged probability vector:

```
all_proba = [m.predict_proba(feat_df)[0] for m in self._models]
proba = np.mean(all_proba, axis=0)
... directional_conf = max(float(proba[0]), float(proba[2]))   # confidence
if confidence < self._confidence_threshold: return NO_SIGNAL    # binary gate
...
return Signal(direction=direction, weight=100, tp_pct=tp_pct, sl_pct=sl_pct)  # FLAT weight
```

`confidence` is used ONLY as a **binary gate** (`if confidence < threshold: SKIP`) and is then **DISCARDED**. Every surviving signal emits a **flat `weight=100`** regardless of whether the model barely cleared the threshold (proba ~0.61) or was highly confident (proba ~0.95). A marginal-confidence trade is sized identically to a clear-conviction trade. The M1 model's own per-trade conviction signal is computed and thrown away.

### Section 2.3 — PART B: T6 — per-trade IS outcome dispersion (the heterogeneity to exploit)

A conviction sizing signal can only help if per-trade outcomes are heterogeneous within each symbol. T6 measures the dispersion of per-trade `net_pnl_pct` on the /060 IS roster:

| Symbol | IS trades | net_pnl_pct mean | net_pnl_pct std | p10 | p90 | p90−p10 dispersion |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 73 | +1.0883 | 5.7400 | −4.5911 | +8.7216 | 13.31 |
| LDOUSDT | 11 | −1.0398 | 9.6314 | −8.4675 | +12.5147 | 20.98 |
| TRXUSDT | 75 | −0.3072 | 3.0097 | −2.9425 | +4.4741 | 7.42 |
| ALL | 159 | +0.2828 | 5.0709 | −4.6066 | +7.3705 | 11.98 |

Per-trade outcomes are strongly heterogeneous within every symbol (the p90−p10 spread is 7–21 percentage points). There is substantial per-trade dispersion for a conviction signal to differentiate — flat-100 sizing treats a +12% trade and a −8% trade identically.

### Section 2.4 — PART B: T7 — the current sizing is conviction-BLIND

T7 measures whether the *current* per-trade size (the vol-targeting `weight_factor` already in the roster) correlates with per-trade outcomes:

| Symbol | IS trades | corr(weight_factor, net_pnl_pct) | corr(weight_factor, win) |
|---|---:|---:|---:|
| BCHUSDT | 73 | +0.2358 | +0.2621 |
| LDOUSDT | 11 | +0.1734 | +0.2420 |
| TRXUSDT | 75 | **−0.1408** | **−0.1338** |
| ALL | 159 | **+0.0937** | +0.0683 |

The current `weight_factor` is essentially **conviction-blind**: pooled it correlates only +0.094 with per-trade `net_pnl_pct`, and for TRX it correlates with the **WRONG sign** (−0.141 — the current sizing puts MORE size on TRX's worse trades). Vol-targeting sizes by realised volatility, not by edge. A conviction signal — the M1 model's own directional margin — is therefore an **orthogonal** per-trade size input: it carries per-trade edge information the current sizing does not.

### Section 2.5 — PART B: T8 — holding-time orthogonality (degeneracy proof)

T8 verifies the conviction-derate map is holding-time-orthogonal **by construction**:

| Split | n_trades | mean duration (candles) | full-roster mean-duration delta | trades added by axis | trades removed by axis |
|---|---:|---:|---:|---:|---:|
| IS | 159 | 6.3145 | **0.000** | **0** | **0** |
| OOS | 102 | 6.4608 | **0.000** | **0** | **0** |

A pure post-model per-trade weight scalar adds and removes ZERO trades — the `(symbol, open_time)` key roster is bit-identical before and after. The full-roster mean/median duration delta is exactly 0.000 (no barrier — TP/SL/timeout — is touched). The Critic /076 added-vs-removed roster-composition sub-channel is **DEGENERATE** (empty added set AND empty removed set). The /076 trade-SELECTION channel and the /078 universe-swap channel are both structurally INACCESSIBLE to a per-trade weight scalar (Section 4.4 expands this).

### Section 2.6 — EDA limitation (disclosed honestly)

The per-trade M1 `confidence` is **NOT persisted** in the trade roster or any report artifact — recovering it requires re-training every walk-forward month's ensemble (a Phase 6 backtest, not a 2h EDA). So the EDA establishes (a) the architecture DISCARDS the margin, (b) the current sizing is conviction-blind, (c) the per-trade dispersion a conviction signal could exploit — but it **cannot prove the M1 confidence itself carries IS edge**. That is the genuine residual risk of the axis (Section 4.2, Section 7). The Section 7 SUSPICIOUS probability is floored at the cycle-2 base rate accordingly — this EDA presents NO conditional-orthogonality proof that would justify deviating below the base rate.

---

## Section 3 — Proposed Changes

### 3.1 — PRIMARY AXIS: conviction-weighted per-trade position sizing (a conviction-DERATE map)

A NEW model-architecture primitive (primitive 13) — a **conviction-DERATE map** applied inside `LightGbmStrategy.get_signal`, replacing the hardcoded `weight=100`:

```
weight(confidence) = round( 100 * clip( (confidence - C_FLOOR) / (C_REF - C_FLOOR),
                                        W_MIN_FRAC, 1.0 ) )
```

where `confidence = max(P(long), P(short))` is the value `get_signal` already computes (`lgbm.py` line ~646-650), and the three parameters are **a-priori, data-free constants**:

| Param | Value | Rationale (a-priori — NOT fitted to any IS or OOS metric) |
|---|---:|---|
| `C_FLOOR` | 0.50 | The coin-flip line. A trade at the coin-flip line maps to the weight floor. |
| `C_REF` | 0.65 | The a-priori clear-conviction reference — a 65/35 read. The existing `_inference_threshold_floor` (/067 Path D) already establishes 0.60 as the project's a-priori "marginal" line; 0.65 sits one notch above it as the "clear-conviction" line. A RULE. |
| `W_MIN_FRAC` | 0.50 | The weight floor as a fraction of 100 — a marginal-confidence trade is de-rated to weight 50. Mirrors the R2 drawdown-scale floor (0.33) and the primitive-12 de-rate discipline; 0.50 is a round, conservative half-size floor. |

The map is **monotone non-decreasing** in confidence, **bounded on [50, 100]**, and equals exactly 100 for every `confidence ≥ 0.65`. It is a **de-rate-only** map (`W_MAX = 100`) — it NEVER levers above the current flat weight.

**Why de-rate-only.** (1) It keeps the emitted `weight` inside the `Signal.weight` documented `0-100` int contract — no dataclass change. (2) It is gross-exposure-NEUTRAL-OR-LOWER — it introduces NO new leverage and NO new tail risk (a Risk-Mitigation property, Section 5). (3) It mirrors primitive 12's proven de-rate-only design exactly. The axis still genuinely differentiates sizing — it shrinks marginal-confidence trades relative to clear-conviction trades.

**Application point and look-ahead safety.** The map is applied INSIDE `LightGbmStrategy.get_signal` at the point where `confidence` is already in scope — immediately after the existing confidence-threshold gate and before the `Signal(...)` return at line ~725. `confidence` is computed from PAST-ONLY features and a model trained ONLY on the past walk-forward window — it is inherently walk-forward-safe and look-ahead-clean (the production model never sees a future bar). The downstream vol-targeting scale and the RiskV3 gate stack multiply this weight exactly as they multiply the current flat 100 (`backtest.py`: `weight_factor = (signal.weight/100) * vt_scale`), so the change composes cleanly with every existing primitive (including primitive 12, currently OFF). **No IS statistic feeds the production map** — all of P5's parameters are a-priori constants located by the intrinsic [0.5, 1.0] confidence scale; there is no PIVOT computed from data.

**In-scope: ALL of {BCH, LDO, TRX}, ALL directions.** ONE universal map — NO per-symbol constant (the /078-closed per-symbol-customization pattern). NOT a tuned subset.

### 3.2 — Affected code

**QR-authored setup commit (runner config only — the QR does not write `src/` model code):**
- `run_baseline_v3.py`: `ITERATION_LABEL` `"v3-078"` → `"v3-079"`.
- `run_baseline_v3.py`: `V3_MODELS` reverts BCH/ADA/TRX → **BCH/LDO/TRX** (the /078 axis revert; Section 3.3). All pre-flight assertion sites, smoke-loop symbol tuples, and the comment/print strings that name `ADAUSDT` revert to `LDOUSDT` (the `V3_MODELS` block + comment; the 14-feature-fallback loop ~line 507; the ATR-multiplier loop ~line 565; the `vol_scale_floor` block ~line 775; the `features_for_symbol`/`atr_multipliers_for_symbol` docstring).

**QE Phase-6 scope (the primary axis implementation — the QR specifies it, the QE implements it):**
- The conviction-derate map function + the `lgbm.py:get_signal` wiring (replace the hardcoded `weight=100` at line ~725 with `weight=conviction_derate(confidence)`, applied where `confidence` is already in scope) is `src/` model code — **QE Phase-6 scope** (role boundary: the QR does not write `src/` model code).
- A NEW Phase-6 pre-flight assertion confirming the conviction-derate map's a-priori parameters are at their declared values and the map equals 100 at `confidence ≥ 0.65` / 50 at `confidence ≤ 0.50` (a 3-point sanity check) — also QE Phase-6 scope, since it asserts against the QE-authored map function.

This brief specifies the map (3.1) precisely; the QE implements it and writes its adversarial test (Section 6, Section 8.6 BLOCK conditions).

### 3.3 — Single-axis discipline

ONE primary change: the conviction-derate sizing primitive. The `V3_MODELS` ADA→LDO revert is a **baseline-restore** — /078's universe-revision axis went SUSPICIOUS-OOS-DOMINANT and is CLOSED; restoring the /060 anchor universe is the mandated post-/078 setup state, not a new varied axis (a revert of a closed axis is the established "mandatory secondary edit" pattern — cf. /076 reverting /075's primitive 12, /077 reverting /076's feature). The labeling, the 14-feature stack, the `ENSEMBLE_SEEDS`, the Optuna search, and the 7-primitive risk-gate stack are ALL unchanged. Primitive 12 stays OFF.

---

## Section 4 — Expected OOS Impact

### 4.1 — Predicted IS / OOS deltas (anchor: re-anchored /060-config IS +0.8236 / OOS +0.2078)

The conviction-derate map de-rates marginal-confidence trades. The IS-Sharpe effect depends on whether low-confidence trades are systematically worse than high-confidence trades on IS:

- **Central prediction**: IS Δ **+0.05 to +0.20** (central +0.12); OOS Δ **−0.10 to +0.20** (central +0.05).
- The IS lift is bounded modest: the map only DE-rates (it cannot lever winners up), so the gain is from down-weighting the marginal tail, not from amplifying the strong trades. The de-rate is partial (floor 0.50, not 0), so even a low-confidence loser still contributes half its PnL.
- The OOS band is centred near zero and is deliberately WIDE on the downside — the EDA cannot prove M1 confidence carries edge (Section 2.6); if M1 confidence is uninformative the de-rate is noise (INERT); if M1 confidence is informative on IS but the IS-vs-OOS confidence→outcome relationship has drifted, the de-rate could be slightly OOS-negative.

### 4.2 — Falsifier (LOCKED)

**Primary falsifier: IS Δ < +0.05 → the hypothesis (the M1 confidence carries per-trade edge that flat sizing wastes) is FALSIFIED.** An IS Δ in [−0.10, +0.05] with the roster behaviorally changed is the INERT-AT-EXPLORATION outcome (Section 8.3): M1 confidence does not separate IS winners from losers, so de-rating by it is noise.

### 4.3 — Behavioral-effect predictor (mandated by `feedback_axis_saturation_predictor.md` / `feedback_v3_axis_saturation_predictor.md`)

The axis MUST change a material fraction of the IS roster's `weight_factor` values, else it is a saturated/null axis. The predictor:

- **Predicted: ≥ 25% of the 159 IS trades have their `weight_factor` de-rated (multiplier < 1.0).** Mechanism: the de-rate fires on every trade whose M1 directional confidence is below 0.65. The existing inference-threshold floor is 0.60 (`_inference_threshold_floor`, /067) — so every surviving trade has confidence ≥ 0.60, and the de-rate window is the [0.60, 0.65) confidence band plus any cell whose Optuna-tuned threshold sits below 0.65. Given the M1 confidence distribution typically concentrates near the threshold for a hard 8h directional problem, a large share of trades sit in [0.60, 0.65). The 25% lower bound is conservative.
- **Falsifier**: if **< 15%** of IS trades are de-rated, the axis is behaviorally saturated (every trade is high-confidence ≥ 0.65) — the result is a NULL-RESULT (Section 8.5) and the predictor missed.
- **Important**: a de-rate changes `weight_factor`, hence `weighted_pnl`, hence the headline IS/OOS Sharpe — but it adds/removes NO trade. So the `(symbol, open_time)` key roster stays bit-identical to /060; only `weighted_pnl` values move. NULL-RESULT (Section 8.5) here means "behaviorally saturated" (too few de-rates to matter), NOT "bit-identical roster" — the roster IS bit-identical on keys by construction; the discriminator is the count of de-rated trades, reported by the QE.

### 4.4 — Holding-time-effect predictor + added-vs-removed sub-channel (mandated by `feedback_v3_is_oos_regime_divergence.md` + Critic /076 Rec #2)

**Full-roster holding-time predictor: mean/median trade duration delta = EXACTLY 0.000 candles.** A per-trade weight scalar touches NEITHER direction, NOR take-profit, NOR stop-loss, NOR timeout, NOR the labeling, NOR any model input. Every trade enters on the same signal bar and exits at the same barrier — identical duration. This is empirically proven for a weight scalar at iter-v3/075 primitive 12 (kept-roster duration delta 0.000 IS / +0.004 OOS — "a size scalar deletes no trade"). EDA T8 confirms it on the /060 roster.

**Added-vs-removed roster-composition sub-channel (Critic /076 Rec #2): DEGENERATE.** A per-trade weight scalar adds ZERO trades and removes ZERO trades — the added set and the removed set are BOTH empty. The /076 trade-SELECTION channel (a feature shifting which trades the model picks) and the /078 universe-swap channel (an added symbol's duration-loaded roster) are both structurally INACCESSIBLE to a pure post-model per-trade weight scalar: the model, its inputs, and its trade roster are bit-identical; only the size of each kept trade changes. **The conviction-derate axis CANNOT load the v3 IS/OOS regime factor via the holding-time-extension channel, the trade-selection channel, OR the universe-swap channel** — all three known regime-loading vectors are closed to it.

**Sub-channel falsifier**: if the QE's roster diff finds ANY trade added or removed vs the /060 key roster, the implementation has a wiring defect (a weight scalar must not change which trades are taken) — this would be a Check-8 / Phase-6 implementation BLOCK, not a classification.

### 4.5 — OOS/IS ratio SUSPICIOUS pre-registration (mandated by `feedback_v3_oos_is_ratio_gate.md`)

Pre-registered, LOCKED, using the canonical within-iteration `comparison.csv` `monthly_sharpe` ratio:

- **OOS/IS monthly Sharpe ratio > 3.0 → SUSPICIOUS classification** — fires regardless of absolute OOS Sharpe magnitude.
- **OOS-DOMINANT sub-mode → SUSPICIOUS classification**: IS shift < 0 (vs the +0.8236 anchor) AND OOS shift ≥ +0.20 (vs the +0.2078 anchor).

Either ground fires SUSPICIOUS with disjunctive precedence and no magnitude qualifier. The conviction-derate axis is *structurally* protected against the holding-time/selection/universe regime-loading vectors (Section 4.4) — but it is NOT immune to SUSPICIOUS: if M1 confidence happens to correlate with the IS/OOS regime split (e.g. the model is more confident in the OOS uptrend than in the IS bear/chop), de-rating by confidence would preferentially shrink IS trades and lift OOS trades, reproducing the OOS-DOMINANT signature through a fourth channel (a conviction signal that is itself regime-correlated). This residual risk is real and is reflected in the Section 7 SUSPICIOUS floor.

---

## Section 5 — Risk Mitigation

The 7-primitive risk-gate stack is UNCHANGED. The conviction-derate map is a NEW sizing primitive (primitive 13); its risk properties:

- **R-property 1 — gross-exposure-NEUTRAL-OR-LOWER.** The map is de-rate-only (`W_MAX = 100`). It NEVER levers a trade above the current flat weight — it introduces NO new leverage, NO new gross exposure, and NO new tail risk. The portfolio's worst-case exposure is unchanged or reduced. This is the central risk-mitigation property.
- **R-property 2 — bounded weight floor.** The map floors at `W_MIN_FRAC = 0.50` — a marginal-confidence trade is de-rated to half size, never to zero. No trade is silently dropped (dropping would be a holding-time-extension veto, the /071 trap; the map is a SCALAR, not a filter). A de-rated trade still contributes; the map only re-weights.
- **R-property 3 — composes with the existing stack.** The conviction-derated weight flows through vol-targeting and the 7 gates multiplicatively, exactly as the current flat 100 does. Primitive 12 (also a de-rate, currently OFF) and the conviction-derate would multiply if both were ON — but primitive 12 stays OFF, so there is no compounding.
- **R-property 4 — IS-calibrated behavioral bound.** Section 4.3 pre-registers the de-rate fire-rate band [15%, ...] with a falsifier; the QE reports the realised de-rate count. If the de-rate fires on essentially every trade (all trades < 0.65 confidence) the portfolio gross exposure halves uniformly — which is still bounded and safe (no leverage), and would show up as a uniform IS/OOS PnL scale-down (a measurable, benign signature).

Simulated historical effect: the EDA cannot recover per-trade confidence, so a precise historical de-rate simulation is not possible at the EDA stage (Section 2.6); the QE's Phase-6 backtest produces the realised per-trade de-rate distribution and the realised IS/OOS effect.

---

## Section 6 — Risk Management Design

The v3 risk stack is the 7-primitive RiskV3 gate cascade (BTC trend kill, vol scaling, ADX, Hurst regime, feature z-score OOD, low-vol filter, hit-rate [disabled]). The conviction-derate map is **primitive 13**, a sizing primitive applied UPSTREAM of the RiskV3 cascade — inside `LightGbmStrategy.get_signal`, the M1 strategy that RiskV3Wrapper wraps.

| Primitive | Type | Scope | Fire-rate prediction | Regime coverage |
|---|---|---|---|---|
| 13 — conviction-derate | per-trade weight scalar (DE-rate only) | M1 strategy, all 3 symbols, all directions | ≥ 25% of IS trades de-rated (Section 4.3); falsifier < 15% | regime-NEUTRAL by construction — the map is a pure function of the M1 confidence, not a regime label; it cannot load the regime factor via holding-time / selection / universe vectors (Section 4.4) |

The map composes with the 7 downstream gates multiplicatively (`weight_factor = (signal.weight/100) * vt_scale`, then RiskV3 gates). It is the FIRST weight-modifying step (it sets the signal weight that vol-targeting and the gates then scale). No gate threshold changes. The QE's Phase-6 implementation includes an adversarial test asserting (a) the map is monotone non-decreasing, (b) it equals 100 for `confidence ≥ 0.65` and `50` for `confidence ≤ 0.50`, (c) the trade roster `(symbol, open_time)` key set is bit-identical to /060 (a weight scalar adds/removes no trade), and (d) `confidence` is read look-ahead-clean (it is computed from the already-past-only `proba` vector).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

The conviction-derate axis is structurally protected against the three known v3 regime-loading vectors (holding-time extension, trade selection, universe swap — Section 4.4) — but it has its own most-plausible failure modes, predicted here:

**Most plausible failure mode — INERT-AT-EXPLORATION (probability ≈ 40%).** M1 confidence does not separate IS winners from losers — the model's directional probability is a poor proxy for per-trade edge on this hard 8h problem. The de-rate fires on a material fraction of trades (the behavioral-effect predictor holds) but the de-rated trades are not systematically the losers, so the IS and OOS Sharpe move trivially (both inside the noise bands). EDA T7 shows the *current* sizing is conviction-blind — but it does NOT prove the M1 *confidence* is informative; INERT is the honest modal outcome.

**Second failure mode — SUSPICIOUS-OOS-DOMINANT (probability ≈ 45% — floored at the cycle-2 base rate).** M1 confidence is itself regime-correlated: the model is systematically more confident in the OOS sustained uptrend than in the IS mixed bear/chop regime. De-rating by confidence then preferentially shrinks IS trades (lower confidence) and preserves OOS trades (higher confidence) — the IS Sharpe falls and/or the OOS Sharpe rises, reproducing the OOS-DOMINANT signature through a fourth, conviction-correlation channel. **The /078 calibration discipline (Critic /076 Rec #3) requires the Section 7 SUSPICIOUS probability to be floored near the running cycle-2 base rate (4 of 8 = 50%) UNLESS the brief presents a proof strong enough to justify deviating below it.** This brief presents NO such proof — the EDA explicitly CANNOT measure whether M1 confidence is regime-correlated (the per-trade confidence is not persisted; Section 2.6). The structural protection in Section 4.4 closes the holding-time/selection/universe vectors but does NOT close the conviction-correlation channel. SUSPICIOUS is therefore floored at ≈ 45% — just below the 50% base rate, the small reduction reflecting only that three of the four regime-loading vectors are provably closed (a partial, not a full, structural argument).

**Third failure mode — NULL-RESULT (probability ≈ 10%).** The de-rate is behaviorally saturated — essentially every surviving trade has M1 confidence ≥ 0.65, so the map equals 100 everywhere and changes < 15% of trades. The behavioral-effect predictor (Section 4.3) misses; the metrics move ~0.

**PROMISING (probability ≈ 5%).** M1 confidence carries genuine, regime-uncorrelated per-trade edge: low-confidence trades are systematically worse on BOTH the IS and OOS windows, so de-rating them lifts IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 co-directionally. This is the success outcome; it is honestly weighted low — cycle 2 is 0/8 clean PROMISING.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (LOCKED)

This is an EXPLORATION; it does NOT merge and does NOT update `BASELINE_V3.md`. The classification is LOCKED before the backtest. Anchor: re-anchored current-code /060-config baseline **IS +0.8236 / OOS +0.2078**. The disjunctive taxonomy is evaluated in order **SUSPICIOUS → NULL-RESULT → NEGATIVE → PROMISING → INERT**; the FIRST match is canonical.

### 8.1 — PROMISING
IS shift ≥ **+0.10** vs anchor (i.e. IS monthly Sharpe ≥ +0.9236) **AND** OOS shift ≥ **+0.20** vs anchor (OOS monthly Sharpe ≥ +0.4078) **AND** `frac_positive_paths` (CPCV) ≥ 0.50 **AND** not SUSPICIOUS. A PROMISING conviction-derate axis advances as a candidate component for the cycle-2 CONFIRMATION (iter-v3/081).

### 8.2 — NEGATIVE
IS Δ < **−0.10** **OR** OOS Δ < **−0.20** (and not SUSPICIOUS). A NEGATIVE axis does not advance; the conviction-derate sizing primitive is recorded as harmful.

### 8.3 — INERT-AT-EXPLORATION
Both shifts inside the noise bands — IS Δ ∈ [−0.10, +0.10] AND OOS Δ ∈ [−0.20, +0.20] — the roster is behaviorally changed (≥ 15% of IS trades de-rated, per Section 4.3), and SUSPICIOUS does not fire. The conviction signal does not separate winners from losers; the axis does not advance.

### 8.4 — SUSPICIOUS (disjunctive precedence — evaluated FIRST)
Fires if EITHER:
- **Ratio gate**: OOS/IS monthly Sharpe ratio (canonical `comparison.csv monthly_sharpe`) **> 3.0** — regardless of absolute magnitude; OR
- **OOS-DOMINANT sub-mode**: IS shift **< 0** (vs +0.8236) **AND** OOS shift **≥ +0.20** (vs +0.2078).

A SUSPICIOUS axis NEVER advances to the CONFIRMATION bundle — the OOS lift is uncorroborated by IS (regime exposure, not robust edge).

### 8.5 — NULL-RESULT
The axis is **behaviorally saturated** — **< 15%** of IS trades are de-rated (the behavioral-effect falsifier, Section 4.3) — so the metrics move ~0. NOTE: for a weight-scalar axis the `(symbol, open_time)` key roster is bit-identical to /060 BY CONSTRUCTION (a scalar adds/removes no trade); the NULL-RESULT discriminator is therefore the **count of de-rated trades**, NOT roster bit-identity. NULL-RESULT does not advance.

### 8.6 — Phase-6 implementation BLOCK conditions (not classifications)
- The QE's roster diff finds ANY trade added or removed vs the /060 `(symbol, open_time)` key roster (Section 4.4 sub-channel falsifier) → wiring defect → BLOCK.
- The conviction-derate map is non-monotone, or does not equal 100 at `confidence ≥ 0.65` / 50 at `confidence ≤ 0.50` → BLOCK.
- `confidence` is read in a way that consults a future bar → look-ahead → BLOCK.

---

## Section 9 — Library Stack Declaration

No new libraries. The conviction-derate map is pure arithmetic (`clip`, `round`) on the M1 ensemble's already-computed `proba` vector inside `lgbm.py`. Pinned stack (carried from /059 / `BASELINE_V3.md`): lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. CPCV/PBO/PSR/DSR per `validation_v3.py`. No mlfinlab/mlfinpy/pypbo/fracdiff change.

---

## Section 10 — QR Audit Trail

### 10.1 — Axis selection provenance (per `feedback_v3_axis_selection_quant_discipline.md`)

The /078 diary Section 11 + Critic /078 Rec #3 seeded three candidate families for /079 (NON-binding — the actual axis is QR-EDA-driven):
1. A NEW model-architecture axis targeting the BCH IS-concentration fragility — a cross-symbol re-weighting (variance-normalized aggregation OR inverse-vol sizing).
2. A NEW labeling-architecture axis (trend-scanning / first-significant-move label, or per-symbol past-only-vol-set barriers).
3. A holding-time-orthogonal NEW risk primitive — a per-trade conviction-weighted sizing primitive driven by the M1 prediction-margin.

**The QR EDA (`analysis/iteration_v3-079/sizing_axis_eda.py`) tested candidate #1 FIRST and FALSIFIED it** (Section 2.1, EDA PART A): inverse-vol cross-symbol sizing collapses the IS Sharpe by −0.53 (it is return-blind — it up-weights TRX, the worst-edge symbol); the edge-aware "cut-the-loser" alternative is IS-Sharpe-monotonic, which makes per-symbol-multiplier selection an OOS-tuning and per-symbol-customization trap. Candidate #1 (any cross-symbol re-weighting) is closed by the EDA per `feedback_axis_saturation_predictor.md` (skip a harmful axis). Candidate #2 (a new labeling architecture) was NOT pursued: the binding constraint is that the labeling change must not extend mean/median trade duration (Critic /078) — a trend-scanning / first-significant-move label is variable-horizon and would change duration, loading the regime factor at the brief stage. **The QR selected candidate #3 — the conviction-weighted per-trade sizing primitive** — the one structural candidate that is provably holding-time-orthogonal, selection-orthogonal, feature-orthogonal, NOT per-symbol-customized, and NOT a macro classifier. The EDA's PART B (T6–T8) is the IS-only evidence for it. This is the QR's call, EDA-backed, made before this brief.

### 10.2 — Per-parameter IS-only / a-priori selection-function disclosure (mandated by Critic /075 Rec #2)

Every design parameter and its selection function — full statement in the EDA docstring (`sizing_axis_eda.py`):

| Param | Value | Selection function — IS-only or a-priori |
|---|---:|---|
| `C_FLOOR` | 0.50 | A-PRIORI, data-free — the coin-flip line. |
| `C_REF` | 0.65 | A-PRIORI, data-free — a 65/35 clear-conviction read, one notch above the existing 0.60 inference-threshold floor. NOT fitted to any metric. |
| `W_MIN_FRAC` | 0.50 | A-PRIORI, data-free — a round, conservative half-size floor; mirrors the R2 0.33 floor and primitive-12 discipline. |
| in-scope symbols | all 3 | A-PRIORI structural — one universal map; no per-symbol constant. |
| in-scope directions | both | A-PRIORI structural. |

**NO design parameter of the selected axis is fitted to an IS metric and NONE to an OOS metric.** All three numeric parameters are a-priori constants; the map is located entirely by the intrinsic [0.5, 1.0] confidence scale — there is no data-derived PIVOT. The EDA's PART A inverse-vol parameters (`vol_anchor` = median IS σ; clip [0.5, 2.0]) ARE IS-derived, but they are **diagnostic-only** — used solely to FALSIFY the rejected candidate, never to design the selected axis. The EDA reads NO OOS metric to select any parameter (it reads the /060 OOS roster once, in T8, only to print the OOS trade count for the degeneracy proof).

### 10.3 — Commit SHAs

- EDA: `0a54acd` (`analysis(iter-v3/079): sizing-axis EDA …`); stale-CSV cleanup `b942dc7`; conviction-derate design refinement `dc5b723`.
- Brief: `b61c8a8` (`docs(iter-v3/079): research brief …`).
- Setup commit: `3dbbd4b` (`feat(iter-v3/079): setup — V3_MODELS revert ADA->LDO …`).
- This SHA-backfill commit: `<backfill_sha>`.
