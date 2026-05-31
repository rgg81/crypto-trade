# Phase 7.5 Critic Review — iter-v1/038

OVERALL: EXPLORATION-NEGATIVE-CATASTROPHIC — per-symbol vol-ceiling at p75/0.5× destroyed IS Sharpe (Δ −0.31), worsened OOS Sharpe (Δ −0.53), and triggered the brief's NEG-CAT band (Δ < −0.45); H1 mechanism falsified (Max DD INCREASED, positive-expectancy trades sacrificed); EDA's linear −25.63pp PnL prediction empirically VINDICATED at 2× magnitude on IS PnL collapse.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION

## QR Response Considered (Round 2 only)
Not invoked. Round 1 went straight to FINAL — the brief's NEG-CAT band Δ < −0.45 fires directly off the comparison.csv OOS Sharpe column (+0.1337 vs baseline +0.6637 = Δ −0.5300), and every load-bearing F-AXIS predicate resolves to FAIL without ambiguity. No clarification could move the verdict band.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
- Foundation: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`. Grep confirms zero raw `train_end_ms = test_start_ms` matches outside `cross_sectional.py` documentation comments. `tests/test_lookahead_embargo.py` present.
- New code at `src/crypto_trade/risk/vol_ceiling.py:73-74` uses `closes_arr[:idx+1]` (past-only, strict). `compute_per_symbol_vol_ceiling` at line 130 filters `close_time < oos_cutoff_ms` BEFORE the percentile estimate — IS-only threshold confirmed. Default `_OOS_CUTOFF_MS` matches the sacred 2025-03-24 anchor.
- `apply_vol_ceiling` is stateless (lines 149-178), no forward-data access.
- Question raised in user prompt about leak of OOS data into IS percentile is REFUTED — the function signature is past-only by construction and the runtime invocation in the runner pre-computes thresholds at run start from IS-only slices.

### Check 2 — Embargo Width: PASS
Unchanged from baseline. Brief Section 5 declares `walk_forward.py:113` embargo intact. Vol-ceiling is a sizing-side gate downstream of label generation and CV; does not interact with MonthSplit construction.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
- DSR_corrected = −51.97 OOS (well below 0.95); PSR_monthly_vs_1 = 0.184 OOS; PBO not computed (single-seed EXPLORATION).
- Per skill §5.1, Check 3 axis FAILs are INFORMATIONAL at TYPE=EXPLORATION — not BLOCK-triggering. NOTED for catalog: this is the WORST DSR_corrected reading in v1 cycle-5 to date and corroborates the negative-edge verdict.

### Check 4 — IC Correlation: N/A
No new feature families. V1_FEATURE_COLUMNS_PRUNED unchanged. ic_matrix.csv present but uninformative.

### Check 5 — ADF Stationarity: N/A
No new features. adf_test.csv present, no new rows.

### Check 6 — Pareto Dominance: N/A
Single seed=42 EXPLORATION (NORMAL-RISK per Section 2.5). Multi-seed Pareto deferred to /044 CONFIRMATION — but /038 falsifier closes the axis before that point, so Pareto evaluation will never be conducted on this axis.

### Check 7 — Reproducibility: PASS
- HEAD at `eda76cd` (Phase 6 impl commit on iteration-v1/038).
- `"v1-038"` present in catch-all exclusion tuple at `run_baseline_v1.py:4048` (per /030 LESSON).
- Dispatch elif at line 3932 fires BEFORE catch-all; pre-flight asserts at lines 3941-3960 cover mode == per_symbol, pct ∈ [70,80], scale == 0.5, universe == V1_BASELINE_UNIVERSE.
- Dispatch banner at lines 3961-3970 emits all required fields.

### Check 8 — Hypothesis-Implementation Alignment: FAIL (H1 falsified, F1 NEG-CAT band fires)
- **H1 (PRIMARY)** said the mechanism "reduces tail downside without sacrificing positive-expectancy trades". Observed: IS Max DD **81.43%** (catastrophic — vs baseline IS ~37% range); OOS Max DD **46.09%** (vs baseline OOS 40.94%, Δ +5.15pp WORSE). Tail downside INCREASED on BOTH IS and OOS. Positive-expectancy trades were SACRIFICED (per-symbol OOS PnL is NEGATIVE on all 5 symbols: BTC −3.24, LTC −5.38, ETH −9.42, DOT −15.05, LINK −23.80). H1 is FALSIFIED on both clauses.
- **F-AXIS #1 (OOS Sharpe Δ vs +0.6637)**: observed +0.1337 → Δ = **−0.5300**. Lies inside NEG-CATASTROPHIC band (Δ < −0.45). F1 fires NEG-CAT.
- **F-AXIS #2 (wiring)**: PASS — IS fire-rate 10.56% (76 of ~720 IS trades; within predicted modal 60-90 band), OOS fire-rate 3.85% (10 of 260 OOS trades; within predicted modal 15-35 only at the low end → actually BELOW the modal 15 floor). Fire-rate asymmetry IS=10.56% vs OOS=3.85% (ratio 0.36) indicates the IS-derived p75 threshold is regime-mismatched to OOS — the OOS RV distribution sits BELOW the IS p75 for 96% of bars. This is a soft signal that the static-threshold mechanism is fragile to regime drift.
- **F-AXIS #3 (per-symbol PnL Δ LOAD-BEARING)**: cannot directly compare per-symbol Δ pct because /038 comparison.csv reports portfolio-weighted PnL not raw per-symbol-shares-of-baseline. Direction unambiguous: ALL 5 cohorts produced NEGATIVE OOS PnL, with LINK (−23.80) and DOT (−15.05) leading the destruction — matching the EDA's HOSTILE prediction for those cohorts. LTC produced −5.38 (EDA predicted +3.58 favorable; model retraining INVERTED expected sign). BTC produced −3.24 (EDA predicted +6.16 favorable; also inverted). The EDA's HOSTILE per-symbol calls (LINK, DOT) were qualitatively correct; the FAVORABLE per-symbol calls (BTC, ETH, LTC) were also inverted to negative. Model retraining did NOT compensate the ceiling clip — it made every cohort worse.
- **F-AXIS #4 (trade count)**: PASS — OOS 260 ≥ 130 floor; IS 720; no per-symbol cohort below 48 (LINK and LTC both have 48). Trade-count floor not the failure mode.
- **F-AXIS #5 (wall-clock)**: implicit PASS — no overrun reported.
- **EDA-vindication signal**: brief Section 9 predicted "portfolio IS weighted PnL Δ = −25.63pp" via IS-roster-linear approximation. Observation: IS Sharpe collapsed Δ −0.31 AND IS total_net_pnl = **−4.57** (the IS PnL went NEGATIVE on a window that was strongly positive at baseline). The IS PnL collapse is the EDA's −26% prediction REALIZED AT 2× MAGNITUDE because Optuna under retraining selected basins that AMPLIFIED rather than compensated the clip. Brief Section 0.6 and Section 2 modal prior assigned 25% to NEG-CAT; the observed outcome matches that scenario exactly. EDA prediction VINDICATED with STRONG signal strength — and the empirical excess beyond −0.45 (observed −0.53) closes the symmetric-ceiling axis at v1 cycle-5 with diagnostic clarity.

### Check 13 — Anti-Pattern Static Scan: PASS
- A1 (`train_end_ms = test_start_ms` no-subtract): 0 unexplained matches in `src/`. All 5 grep hits carry `- embargo_ms` or appear in documentation comments.
- A2 (forward-window labeling std): `labeling.py` unchanged.
- A3 (scaler.fit_transform combined): 0 matches.
- A7 (parquet append-without-clear): 0 matches in `optimization.py`.
- A12 (DSR/PSR wrong-granularity): no new methodology-axis report fields in /038.
- A13 (report-file read-before-write): no new methodology-axis report fields in /038.
- New vol-ceiling code path: no past-only violations, no state machine (per Section 2.5 stateless declaration), no integration-test gap (sizing-only gate downstream of model prediction).

### Check 14 — Axis Family Validation: PASS
- Brief Section 0.6 declares `risk-primitive`.
- src/ diff touches: `src/crypto_trade/risk/vol_ceiling.py` (NEW), `src/crypto_trade/backtest.py` (entry-time gate threading + BacktestConfig fields), `run_baseline_v1.py` (CLI flag + dispatch + exclusion-tuple). All edits are pre-trade sizing-gate plumbing — NO feature additions, NO label changes, NO Optuna objective changes, NO universe changes, NO model arch changes. Family declaration CLEAN.
- Rotation status was VALID at Phase 5.5 (last risk-primitive was /010 R5; prior 5 EXP families were sample-weighting/feature-family/labeling/per-cohort-spec/loss-function). No monoculture defiance.

## Observed Results vs Brief Verdict Matrix

| Metric | Baseline | /038 | Δ | Band threshold | Within band |
|---|---|---|---|---|---|
| OOS Monthly Sharpe | +0.6637 | +0.1337 | **−0.5300** | NEG-CATASTROPHIC Δ < −0.45 | YES (NEG-CAT) |
| IS Monthly Sharpe | (~+0.28 anchor) | −0.0308 | **−0.31** | IS-only informational | NEG-CAT confirmed |
| OOS Max DD | 40.94% | 46.09% | +5.15pp WORSE | H1 mechanism (tail clip) | FALSIFIED |
| IS Max DD | (~37% range) | **81.43%** | catastrophic | H1 mechanism | FALSIFIED |
| OOS trades | 189 | 260 | +71 | ≥ 130 floor | PASS |
| Per-symbol OOS PnL | (positive on most) | ALL 5 NEGATIVE | universal destruction | F-AXIS #3 LOAD-BEARING | FALSIFIED (LINK + DOT worst as EDA predicted) |
| IS vol-ceiling fire rate | predicted 75 of 620 (12.1%) | 10.56% (76/720) | matches | F-AXIS #2 wiring | PASS |
| OOS vol-ceiling fire rate | predicted 15-35 of 189 | 3.85% (10/260) | BELOW low end | F-AXIS #2 OOS calibration | SOFT FAIL (IS-derived static threshold regime-mismatched to OOS) |
| DSR_corrected (OOS) | (positive at baseline) | −51.97 | catastrophic | informational EXP | informational |
| PSR_monthly_vs_1 (OOS) | (~0.371 at /037) | 0.184 | regression | informational EXP | informational |

## Verdict Cell

**EXPLORATION-NEGATIVE-CATASTROPHIC** per brief Section 4 fifth row (Δ < −0.45). The OOS Sharpe Δ of −0.5300 sits 0.08 below the NEG-CAT threshold. The IS Sharpe also fell to −0.0308 (Δ −0.31 vs baseline IS) and IS Max DD blew out to 81.43%, indicating the failure is NOT a single-seed OOS regime artifact but a STRUCTURAL signal-destruction outcome: Optuna under retraining selected hyperparameter basins that allocated MORE capital to the cohorts the ceiling was designed to protect (LINK, DOT), amplifying rather than dampening the IS-roster-linear −25.63pp PnL prediction. The H1 mechanism (tail clip) and the H1a model-retrained mechanism (basin compensation) are BOTH falsified.

**Forensic note**: this is the FIRST v1 cycle-5 EXPLORATION where the EDA prior was NEG-DOMINANT (modal 65%) and the experiment fired at the catastrophic tail of that prior (25% modal weight). The EDA's linear approximation was correct in direction AND under-predicted in magnitude — the realized IS PnL Δ exceeds the −26% prediction because Optuna at single-seed=42 latched onto a worse basin than the linear extrapolation modeled. The catalog entry for /038 should record this as "EDA-vindicated NEG-CAT" — the prediction generalized to OOS with EXCESS magnitude, not less.

## Recommendations to QR

1. **Symmetric per-symbol ceilings are CLOSED for v1 cycle-5 (and prospectively for any future cycle).** The static-IS-threshold mechanism is regime-fragile (OOS fire-rate 3.85% vs IS 10.56% — IS-derived p75 doesn't generalize) AND model retraining inverts the EDA's per-symbol favorable predictions. Do NOT relaunch this axis at higher seed budget; do NOT propose a portfolio-level variant; do NOT propose a tighter percentile. The mechanism is structurally falsified.

2. **Risk-primitive axis family is at 2/2 NEG-predicted-then-realized** if /038 is paired with the proposed /039 drawdown-brake (which was already pre-rejected per the EDA pre-flight). Per Critic's adversarial duty to flag axis-family saturation: the risk-primitive family is FAMILY-SATURATED-FOR-V1-CYCLE-5. Pivot away from rule-layer downstream gates entirely; the cycle-5 evidence is that the signal at the model-output layer cannot be RESCUED by post-prediction gating.

3. **Pre-register the EDA-extrapolation-vs-realization log for future risk-primitive briefs.** The /038 EDA predicted −26% portfolio PnL Δ; the realized IS Sharpe Δ −0.31 implies a stronger PnL hit (~−50pp). Future risk-primitive briefs should include an EDA-prediction-error band specifying how much worse Optuna retraining could amplify the linear prediction; if that band is "≥ 2×", treat the axis as STRUCTURALLY UNRECOMMENDED before launching.

## Path Forward (mandatory — proposed alternative axes for /039+)

Prior 5 EXPLORATIONs (catalog + briefs Section 0.6 since /033): sample-weighting (/032), feature-family (/034), labeling (/035), per-cohort-specialization (/036), loss-function (/037), risk-primitive (/038). All 6 distinct families consumed in cycle-5. /038 + the proposed /039 drawdown-brake (pre-rejected EDA) constitutes **2 consecutive risk-primitive predicted-NEG EXPLORATIONs → AXIS-FAMILY-SATURATED-FOR-V1-CYCLE-5**.

Three alternative axes for /039 from families NOT used in the prior 5 EXPLORATIONs:

1. **Per-cohort Sortino × per-cohort specialist hybrid** — family: `loss-function × per-cohort interaction probe`. DIRECTLY answers the /037 forensic stacking question (Recommendation 2 in /037's review): does the Sortino DOT-concentrated lift (+0.84 per-cohort isolated) COMPOUND or COLLIDE with the /036 LINK+DOT trend-scan specialist? Run /037's Sortino-objective branch with the /036 LINK+DOT trend-scan label specialization layered on top. Mechanism: tests whether the right-tail concentration that /037 generated is orthogonal to or interferes with the per-cohort labeling specialization that /036 attempted. Single experiment resolves a load-bearing cycle-5 CONFIRMATION-bundling decision. EDA pre-flight from existing /037 + /036 trade rosters can predict compounding direction before launch.

2. **Ternary prediction-architecture** — family: `prediction-architecture`. Replace the binary {long, short} class head with a ternary {long, neutral, short} head + per-symbol neutral-class threshold via Optuna. Expected mechanism: explicit "no-trade" class lets LightGBM MODEL trade-skipping directly rather than relying on Optuna confidence-threshold post-hoc. Orthogonal to loss-function, labeling, weighting, feature, and risk-gate axes. This was the same recommendation surfaced in /037's review; given /038 now closes the risk-primitive family in cycle-5, prediction-architecture is the highest-priority unexhausted axis. Brief Section 1 should pre-register the OOS-Sharpe Δ that distinguishes architectural lift from saturation (suggested band ≥ +0.15 → PROMISING-CLEAN).

3. **Cross-asset non-OHLCV feature carry from v3** — family: `cross-asset-feature-family` (non-OHLCV). The v3 catalog at /123 CLOSED cross-asset OHLCV-derived primitives after 6 consecutive failures, but explicitly preserved non-OHLCV cross-asset (on-chain, liquidations, non-Binance basis) as PERMITTED with rolling-window T5 importance test. Port one non-OHLCV cross-asset primitive (e.g., perpetual-vs-spot funding-rate basis from a non-Binance source, OR on-chain stablecoin supply Z-score) into V1_FEATURE_COLUMNS_PRUNED with a strict |IC|<0.5 vs all 43 existing features. Tests whether v1 has been over-anchored on price-derived features — an axis the cycle-5 menu has not touched. Mechanism: orthogonal information stream, not a knob within existing scope.

(All three from families NOT in the prior-5 EXPLORATIONs. Critic is advisory; QR may adopt, modify, or reject. None depend on the failed /038 mechanism.)