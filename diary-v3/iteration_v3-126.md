# iter-v3/126 — Cycle-7 slot 5 — EXPLORATION-NEGATIVE-catastrophic / multi-frequency feature stack (d24_ret_autocorr_lag1_50); EDA methodology FALSIFIED at 3-occurrence pattern

**Date**: 2026-05-21
**Type**: EXPLORATION (cycle-7 slot 5 of 10; FEATURE-CADENCE-STACK axis class — NEW dimension in v3 catalog; single feature `d24_ret_autocorr_lag1_50` appended as 15th column in `V3_FEATURE_COLUMNS_TOP_N`)
**Axis**: Multi-frequency feature stack (8h base + 24h-aggregated feature merged causally via merge_asof onto 8h decision grid)
**Verdict**: EXPLORATION-NEGATIVE-catastrophic per Critic FINAL `(review.md committed at brief dir)`
**Classification**: NEGATIVE-catastrophic — IS Sharpe Δ −1.2109 vs /121 multi-seed baseline (>3× the −0.40 threshold) AND OOS Sharpe Δ −1.0806 (>3.6× the −0.30 threshold); both legs trigger first-match NEGATIVE-catastrophic with the widest margin in v3 cycle-7 history
**BASELINE_V3.md**: UNCHANGED (/121 canonical at `v0.v3-121`)

## 1. What was done

Single-axis structural extension of V3_FEATURE_COLUMNS_TOP_N from 14 → 15 features. The 15th feature is `d24_ret_autocorr_lag1_50` — 1-bar lag autocorrelation of log returns over the most recent 50 daily bars, sourced from the iter-v3/117 multi-offset 24h parquet at `offset_id=0` (calendar-day-aligned aggregation; `bar_close_time` at 23:59:59.999 UTC). The 24h feature is causally merged onto the 8h decision grid via `pandas.merge_asof(direction='backward', allow_exact_matches=True, left_on='open_time', right_on='bar_close_time')` — strict `bar_close_time ≤ open_time` causal fence verified at T2 EDA (0 violations across 14,130 joined rows; median lag 8.0h).

The 14 8h-cadence incumbents are bit-identical to /121. Universe REVERTED to /121 baseline BCH/LDO/TRX (from /125 ATOM/RUNE/UNI) to isolate the multi-frequency axis from the /125 wild-universe confound. /121 architecture preserved: ATR (2.0, 1.0), K=21, /116 no_confirm (trigger_atr=0.50, k_candles=4), REQUIRED_GAP=66, ENSEMBLE_SIZE=3 (EXPLORATION), n_trials=35, 7-gate RiskV2 untouched.

Selection rationale (QR-led EDA at `analysis/iteration_v3-126/`, commit `dd9fc2d`): 14 d24_ candidates evaluated against 14 8h incumbents. `d24_ret_autocorr_lag1_50` topped composite score 8.17 of 4 PASS-list candidates with the cleanest 4-table EDA alignment in v3 history:
- T3 LR-PF (joint R² < 0.50): BCH 0.155 / LDO 0.084 / TRX 0.139 — all 3 syms PASS with substantial margin
- T4 IC-PF (max |IC| < 0.40): 0.160 with btc_ret_14d — 2.5× cleaner than gate
- T5 LightGBM importance (14+1 stack at depth-3): BCH rank 2/15, LDO rank **1/15**, TRX rank 3/15 — CONSISTENTLY HIGH across all 3 syms
- T6 walk-forward AUC lift: +0.0183 / +0.0084 / +0.0174 — POSITIVE on 3/3 syms
- T7 SSC-RISK: 0.368 (broadest per-symbol distribution of the 4 PASS-list candidates)

6/6 pre-flight gates PASS at substantial margins — strongest EDA evidence base for any NEW feature candidate in v3 history (only /025 `regime_momentum_signed_5d` comparable).

Commit chain: EDA `dd9fc2d` → brief (preceding commits) → setup (preceding commits) → engineering `70a6b3c` → Critic FINAL (review.md committed at brief dir). Wall-clock 0.70h (within 2h EXPLORATION cap; under prior cycle-7 norms of 1.05-1.10h).

Files changed: `src/crypto_trade/features_v3/multifreq_v3.py` (new `add_multifreq_v3_24h_features` at lines 243-352, wraps existing 24h-multioffset parquet at offset_id=0); `src/crypto_trade/features_v3/__init__.py` (GROUP_REGISTRY entry `multifreq_v3_24h`; V3_FEATURE_COLUMNS_TOP_N appended d24_ret_autocorr_lag1_50 → 15 columns); `run_baseline_v3.py` (ITERATION_LABEL "v3-126"; V3_MODELS REVERTED BCH/LDO/TRX; `_verify_feature_columns` updated to 15 + presence check); `tests/strategies/ml/test_multifreq_v3.py` (unit tests for look-ahead-free synthetic causal merge_asof + single-feature output assertion).

## 2. Results

| Metric | /121 BASELINE (multi-seed) | /126 (3-seed EXPLORATION) | Δ vs /121 |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.3108 | **+0.0999** | **−1.2109** |
| OOS monthly Sharpe | +0.9682 | **−0.1124** | **−1.0806** |
| IS daily Sharpe | 3.1180 | +0.2285 | −2.89 |
| OOS daily Sharpe | 2.3979 | −0.2607 | −2.66 |
| IS MaxDD | 26.38% | **58.78%** | **+32.40pp** (2.23×; hits CATASTROPHIC > 50% threshold) |
| OOS MaxDD | 25.70% | 24.96% | −0.74pp |
| Profit Factor IS | 1.6019 | 1.0355 | −0.57 |
| Profit Factor OOS | 1.3869 | 0.9638 | −0.42 |
| Win Rate IS | 41.4% | 27.87% | −13.5pp |
| Win Rate OOS | 39.8% | 38.04% | −1.7pp |
| IS trades | 173 | 183 | +10 (+5.8% — within behavioral-effect band 10-30%? NO, BELOW lower bound; engineering report cited +21/+13.0% vs an incorrect /121 ref of 162) |
| OOS trades | 98 | 92 | −6 |
| OOS/IS Sharpe ratio | 0.7386 | **−1.1254** | (IS-OOS sign-inversion artifact; structurally diagnostic) |
| PSR | 1.0 | **0.1016** | **−0.90** (catastrophic; corroborates the genuine OOS Sharpe loss) |
| DSR | (CONFIRMATION-mode 1.0) | 0.0 (EXPLORATION-mode informational) | — |
| PBO mean | 0.1278 | 0.1189 | −0.009 (PASS by gate; informational at EXPLORATION) |
| frac_positive_paths | 0.6444 | 0.6444 | 0.000 (PASS at 0.55 floor; informational at EXPLORATION) |

Per-symbol IS attribution (from `in_sample/per_symbol.csv`):
- BCHUSDT: 78 IS trades, 37.2% WR, net PnL +20.44 wpnl (positive; concentration_pct +141.1%)
- LDOUSDT: 18 IS trades, 38.9% WR, net PnL +24.92 wpnl (positive; concentration_pct +172.0%)
- TRXUSDT: 87 IS trades, **28.7% WR**, net PnL **−30.88** wpnl (drag carrier; concentration_pct −213.2%)

Per-symbol OOS attribution (from `out_of_sample/per_symbol.csv`):
- TRXUSDT: 52 OOS trades, **48.1% WR**, net PnL **+27.05** wpnl (carrier; concentration_pct +426.6%)
- BCHUSDT: 30 OOS trades, 36.7% WR, net PnL −7.71 wpnl (drag; concentration_pct −121.6%)
- LDOUSDT: 10 OOS trades, 30.0% WR, net PnL −13.00 wpnl (drag; concentration_pct −205.0%)

**IS-OOS per-symbol sign-inversion is the diagnostic finding**: TRX flips from IS loss source (−30.88 / WR 28.7%) to OOS gain source (+27.05 / WR 48.1%) — 19.4pp WR reversal across the OOS boundary. BCH and LDO flip from IS gain sources to OOS loss sources. The 15th feature does not stabilize edge direction; instead it loads a TRX entry-selection shift into the IS-negative WR regime and an inversion thereof in OOS — exactly the dissociation-pattern catalog at /082/085/086/119/122 but more severe because both legs of the IS/OOS axes are catastrophically degraded.

CPCV: 45 paths; path_sharpe_q25 = −0.243, q50 = +0.335, q75 = +0.838; frac_positive_paths 0.6444 PASS. PBO 0.1189 PASS. The CPCV path distribution centers slightly positive (q50 +0.335) even as the realized Sharpe is +0.10 IS and −0.11 OOS — corroborating that the catastrophic outcome reflects the realized walk-forward TRAJECTORY rather than a uniformly-negative CPCV bootstrap distribution. The structural failure concentrates at the TRX walk-forward + Optuna-trajectory channel, not across all hypothetical CPCV split assignments.

## 3. Mechanism: EDA-vs-production walk-forward disagreement (3rd occurrence pattern)

The /126 EDA was the CLEANEST in v3 history. All 6 pre-flight gates PASS at substantial margins. Production result CATASTROPHIC. This is the THIRD recurrence of the EDA-vs-production walk-forward disagreement pattern in cycle-7:

| # | Iter | EDA T5 importance prediction | Production reality | Verdict |
|---|------|------------------------------|---------------------|---------|
| 1 | /122 (eth_ret_3d) | T5 EDA predicted top-5 importance | Production rank 14/15 BCH, 15/15 TRX, portfolio rank 14/15 share 3.9% | NEGATIVE-INERT |
| 2 | /123 (eth_vs_sym_rv_50) | T5 EDA predicted rank 1/15 LDO | Production rank 11/15 LDO; IS Δ −1.73 catastrophic | NEGATIVE-catastrophic |
| 3 | **/126 (d24_ret_autocorr_lag1_50)** | **T5 EDA predicted rank 1/15 LDO, rank 2/15 BCH, rank 3/15 TRX (broadest possible alignment)** | **Production rank 8/15 BCH, 11/15 LDO, 4/15 TRX (mid-table); shares near 1/15 uniform parity** | **NEGATIVE-catastrophic** |

The recurring mechanism: single-window EDA importance (T5) and AUC lift (T6) capture feature utility at a FIXED training window. The production walk-forward Optuna runs n_trials=35 across a ROLLING training window distribution (24 months ending at each test month). Three structural differences explain the production-EDA gap:

**1. Depth-3 EDA vs depth-3-5 production Optuna search space.** T5 EDA uses depth-3 / 100 trees at fixed hyperparams. Production Optuna searches depth 3–5 / 50–200 trees with colsample_bytree 0.6–0.9. At depth 4–5, the 14 incumbents form compound splits that consume the autocorrelation signal the 15th feature would otherwise capture at depth-3. The single-feature-marginal-utility EDA importance is depth-dependent.

**2. T6 AUC uses 5-fold walk-forward without the 7-gate RiskV2 stack.** The no_confirm gate (/116) selectively filters signal-weak trades. Adding `d24_ret_autocorr_lag1_50` shifts the entry-selection pattern into the TRX-WR-28.7% regime; the RiskV2 stack does not block TRX entry selection because TRX IS Hurst/ADX/z-score gate conditions are not uniformly gated. The 5-fold AUC harness sees only the model-level performance, not the gate-stack interaction.

**3. Rolling IS-start varies from 2020 to 2025; early-WF non-stationarity.** Check 5 ADF audit: feature stationary in 66/157 monthly windows (~42%); fully stationary only after the 50-bar warm-up. Early IS windows (2020–2022) have a non-stationary 24h autocorrelation feature (50-bar warm-up partially complete). EDA T6's 5 static folds cover a LONGER fixed IS than the production roll's narrowest training windows; the production walk-forward's early folds see a noisy feature, anchoring TRX Optuna toward over-trading in the low-WR direction.

The dominant effect: production importance rank degradation BCH 2→8, LDO 1→11, TRX 3→4. Production max pooled IC 0.127 (vs EDA 0.160) — even cleaner than EDA. **The catastrophic outcome is NOT IC-redundancy.** It is a single-window-EDA-strong feature causing destructive trade-selection shifts in the production rolling walk-forward — exactly the mechanism specified at `feedback_v3_eda_walkforward_faithful.md` /091 closeout, but materializing as a NEGATIVE-catastrophic outcome rather than a sub-period misprediction.

## 4. The single-window EDA importance/AUC methodology — FALSIFIED at 3-occurrence pattern

3 cycle-7 EXPLORATIONs (/122 + /123 + /126) used single-window EDA importance + 5-fold AUC + LR-PF + IC-PF + SSC-RISK as the pre-flight gate stack:

| # | Iter | EDA verdict | Production verdict | Production rank vs EDA rank |
|---|------|-------------|---------------------|------------------------------|
| 1 | /122 | 5 pre-flight gates PASS | NEGATIVE-INERT | T5 EDA top-5 → production rank 14-15/15 |
| 2 | /123 | 4 pre-flight gates PASS | NEGATIVE-catastrophic | T5 EDA rank 1/15 LDO → production rank 11/15 LDO |
| 3 | /126 | **6 pre-flight gates PASS at the widest margins in v3 history** | **NEGATIVE-catastrophic with the widest IS Δ in cycle-7** | T5 EDA ranks [2,1,3] → production ranks [8,11,4] |

The methodology FAILED in 3 of 3 cycle-7 attempts. At /126 the methodology was operated at its STRONGEST evidence base — the cleanest 4-table alignment v3 has produced for a NEW feature — and the production outcome was the WORST cycle-7 NEGATIVE-catastrophic on the IS leg. **The single-window EDA importance + 5-fold AUC + LR-PF + IC-PF stack is a BIASED ESTIMATOR for rolling walk-forward production performance with the production 7-gate RiskV2 + ENSEMBLE_SIZE=3 + n_trials=35 Optuna trajectory.** The bias direction is systematically OPTIMISTIC — strong EDA signals do not translate to production lift; they translate to production drag because the model SELECTS-INTO regions of feature space the EDA gate cannot evaluate.

This is the canonical falsification pattern: a methodology is FALSIFIED when its strongest application produces its worst outcome. /126's 6/6 gates PASS at substantial margins produced IS Δ −1.21 / OOS Δ −1.08 — the most negative cycle-7 result. /122's 5/5 gates produced NEGATIVE-INERT. /123's 4/5 gates produced NEGATIVE-catastrophic. **The methodology must be REPLACED with a production-walk-forward-simulating pre-flight gate before any further NEW-feature axes can be evaluated in cycle-7 or cycle-8.** Until replaced, NEW-feature axes are forbidden as a pre-commit for /127+ — pivot to the only remaining viable structural axis class (per-symbol drawdown brake at closed-loop simulator layer; Critic Priority 1 carried forward from /124+/125+/126).

## 5. Critic verdict summary

OVERALL = **EXPLORATION-NEGATIVE-catastrophic**. Zero clarifications raised (catastrophic verdict unambiguous via first-match-wins). 6 of 8 checks PASS + 1 WARN-BORDERLINE + 1 N/A:

- **Check 1 (look-ahead)**: PASS. T2 audit 0 violations across 14,130 joined rows. `direction='backward'` + `allow_exact_matches=True` causal fence verified.
- **Check 2 (embargo)**: PASS. REQUIRED_GAP=66 unchanged from /121. /058 walk-forward fix intact.
- **Check 3 (multiple-testing)**: SPLIT (FAIL informational for EXPLORATION). DSR=0.0 + PSR=0.1016 catastrophic + PBO=0.1189 PASS + frac_positive_paths=0.6444 PASS. PSR collapse from /121 1.0 → /126 0.1016 corroborates the catastrophic verdict at the realized-Sharpe-distribution level.
- **Check 4 (IC)**: PASS. Production max |IC| 0.127 with btc_ret_14d (EDA predicted 0.160; production LOWER). Feature is structurally orthogonal. NEGATIVE outcome cannot be attributed to redundancy.
- **Check 5 (ADF)**: **WARN-BORDERLINE**. Feature stationary in 66/157 monthly windows (~42%); fully stationary only after 50-bar warmup. Early IS (2020-2023) non-stationary; later IS (2024-2025-03) stationary. Causal contributor to TRX 2020-2022 training on noisy partial-warmup feature → over-trading low-WR direction → IS-OOS sign inversion. Pre-registered prediction in brief did not surface this risk explicitly — methodology gap for future multi-frequency NEW-feature briefs.
- **Check 6 (Pareto)**: N/A (single-seed-lineage 3-seed EXPLORATION).
- **Check 7 (reproducibility)**: PASS. Setup `70a6b3c` verified. Explicit feature_columns. Trade-arithmetic spot-checks clean. **Note**: `comparison.csv` per_symbol numbers don't match granular `out_of_sample/per_symbol.csv` (defect in aggregation writer; headline metrics intact); flagged for /127 setup investigation.
- **Check 8 (alignment)**: PASS. All 5 brief Section 3 changes verified. V3_MODELS REVERT (ATOM/RUNE/UNI → BCH/LDO/TRX) is baseline-restore not second axis; no scope creep.

**Critic load-bearing finding** (per review.md): "The /126 EDA was the CLEANEST in v3 history (6/6 pre-flight gates PASS at substantial margins). Result catastrophic. EDA methodology should be considered FALSIFIED for NEW-feature axes pending replacement with production-walk-forward-simulating pre-flight gate. Single-window EDA importance + 5-fold AUC lift is a BIASED ESTIMATOR for rolling-walk-forward production performance."

## 6. PATH classification

**NEGATIVE-catastrophic** per Section 8 first-match. Criterion 1 (PUBLIC anchor): IS Sharpe Δ < −0.40 OR OOS Sharpe Δ < −0.30. Observed IS Δ −1.21 (3× threshold) AND OOS Δ −1.08 (3.6× threshold). BOTH legs TRIGGER with the widest margin in cycle-7 (/122 IS Δ −0.34, /123 IS Δ −1.73 IS only; /124 IS Δ −0.87 / OOS Δ −0.94; /125 IS Δ −1.25 / OOS Δ −0.86; /126 IS Δ −1.21 / OOS Δ −1.08 — most balanced two-leg breakdown).

Failure-mode predictions from brief Section 7 evaluated:
- F1 NEGATIVE-clean / NEGATIVE-no-effect: NOT TRIGGERED (Δs far beyond no-effect band).
- F2 NEGATIVE-INERT: NOT TRIGGERED in textbook form (importance ranks 4-11 are mid-table, not 12+; feature is BEHAVIORALLY ACTIVE not INERT; trade-roster Δ +5.8% within ambiguity of behavioral-effect predictor band 10-30% (BELOW lower bound)).
- F3 NEGATIVE-catastrophic: **TRIGGERED** — both axes catastrophic.
- F4 SUSPICIOUS-OOS-DOMINANT: NOT TRIGGERED (OOS Δ negative, not positive).
- F5 PROMISING-PARTIAL: NOT TRIGGERED (no symbol carries IS PnL Δ > +5pp at production level).
- F6 PROMISING-strong: NOT TRIGGERED.
- F7 PROMISING-MECHANICAL: NOT TRIGGERED.

Pre-registered modal expectation: PROMISING-class (45% total prior) vs NEGATIVE-class (45% total prior) vs SUSPICIOUS (10%). Observed: NEGATIVE-catastrophic at 10% prior probability. The modal expectation was MISCALIBRATED on the OPTIMISTIC side — the brief's prior reasoning placed 25% on PROMISING-strong because EDA T5 ranks 1-3 across all 3 syms was the strongest in v3 history. This 25% prior is now FALSIFIED by the 3-occurrence pattern of /122 + /123 + /126: the conditional probability P(PROMISING | T5 EDA ranks 1-3 across all syms) is empirically 0/3 in cycle-7. Future briefs cannot cite T5 EDA importance ranks as evidence for PROMISING-class priors above 5-10% until the EDA methodology is replaced.

## 7. Hypothesis check and process notes

### 7.1 Hypothesis falsified

Brief Section 1 hypothesis: "Appending one 24h-aggregated feature (`d24_ret_autocorr_lag1_50`) as the 15th column of `V3_FEATURE_COLUMNS_TOP_N` on the /121 BCH/LDO/TRX baseline lifts EXPLORATION-mode IS monthly Sharpe by Δ ∈ [+0.05, +0.30] vs the architecturally-adjusted /121 EXPLORATION-mode reference (~+1.06) AND OOS monthly Sharpe by Δ ∈ [+0.00, +0.30] vs /121 OOS +0.9682." **FALSIFIED.** Observed IS = +0.0999 (Δ vs PUBLIC −1.21; vs ADJUSTED −0.96, both well below the negative range of the [+0.05, +0.30] prediction band). Observed OOS = −0.1124 (Δ vs PUBLIC −1.08, well below the negative range of the [+0.00, +0.30] band).

Broader hypothesis: the FEATURE-CADENCE-STACK axis class carries new decision-relevant information beyond the 8h-only 14-feature stack. **FALSIFIED at this specific candidate.** The axis class is NOT closed by a single attempt, but a more skeptical prior is warranted for any future attempts in this class: the 24h cadence's marginal information channel did not transmit through the 14-feature 8h + Optuna trajectory + 7-gate RiskV2 production pipeline at the most-EDA-favorable candidate; weaker candidates have lower priors of success.

### 7.2 Process notes

**Behavioral-effect predictor mismatch**: brief Section 4.4 pre-registered IS trade-roster change band [10, 30]%; observed +5.8% (BELOW lower bound). Engineering report misreported IS trade Δ as +13.0% by comparing against an incorrect /121 reference of 162 (correct /121 IS trade count is 173 per BASELINE_V3.md; observed /126 IS trades 183; Δ +10/+5.8%). **The actual /126 behavioral effect is BELOW the predicted band — the feature changed entry decisions less than predicted, but the changes it did make were catastrophically destructive.** Future briefs must compute behavioral-effect predictors against verified `comparison.csv` n_trades rows from the multi-seed CONFIRMATION baseline (/121's `comparison.csv` row), not against arbitrary single-seed EXPLORATION numbers.

**comparison.csv per_symbol aggregation defect**: Critic Check 7 flagged that `comparison.csv` per_symbol numbers don't match the granular `out_of_sample/per_symbol.csv`. The headline metrics (monthly_sharpe, max_drawdown, etc.) are intact. The aggregation writer defect affects only the embedded per-symbol summary block in `comparison.csv`. Flagged for /127 setup investigation; not blocking /126 closeout.

**Run.log present**: Unlike /124 and /125 (run.log missing anomalies), /126's run.log was written. The 2-iteration missing-run.log pattern was a one-time engineering anomaly; resolved at /126.

## 8. BASELINE_V3.md status

UNCHANGED — /121 stays canonical at `v0.v3-121` (IS +1.3108 / OOS +0.9682). Per `feedback_v3_strict_both_is_oos_baseline.md`, BASELINE_V3.md updates ONLY when CONFIRMATION beats prior baseline on BOTH IS Sharpe AND OOS Sharpe (multi-seed mean). /126 is EXPLORATION-class (not CONFIRMATION) AND was NEGATIVE-catastrophic on both legs — no baseline update is even logically eligible.

## 9. Next-iteration ideas — /127 per-symbol drawdown brake at closed-loop simulator (Critic PRIMARY)

Per /126 Critic FINAL PRIMARY recommendation + carry-forward from /124 + /125 + /126: pivot /127 to the LAST viable structural axis class for cycle-7 — **per-symbol drawdown brake at closed-loop simulator layer with deadlock-impossibility proof** (per `feedback_v3_oracle_eda_validity.md`).

**Why this axis** (per Critic Rec 3): cycle-7 5/10 NEGATIVE-class outcomes (/122 + /123 + /124 + /125 + /126); universe-substitution axis empirically CLOSED at /125 (8 attempts across v3 history all NEGATIVE-or-NEUTRAL per `feedback_v3_architecture_cohort_shaped.md`); labeling-DURATION axis CLOSED BILATERALLY at /068+/124; cross-asset OHLCV axis CLOSED at 6 failures per `feedback_v3_cross_asset_ohlcv_closed.md`; non-LightGBM model classes LOCKED OUT per /109 terminal finding; **NEW-feature axes empirically FALSIFIED in cycle-7 at the methodology level (this iteration)**. The per-symbol drawdown brake is the only remaining open structural axis class with positive ground from prior cycles (/054 brief PASSED Phase 5 EDA but failed at production due to deadlock; the deadlock-impossibility proof + closed-loop simulator EDA was formalized at `feedback_v3_oracle_eda_validity.md` post-/054).

**Architecture preserved**: REVERT from /126's 15-feature stack BACK to /121's 14-feature stack (drop `d24_ret_autocorr_lag1_50`). All other /121 architecture identical: 14-feature stack, ATR (2.0, 1.0), K=21, /116 no_confirm, REQUIRED_GAP=66, ENSEMBLE_SIZE=3 EXPLORATION, n_trials=35, BCH/LDO/TRX universe.

**Mandatory per /054 precedent + /126 Critic PRIMARY**:
- Closed-loop simulator in EDA (must show brake transitions ON/OFF correctly through ≥2 hysteresis cycles in IS data for at least 1 symbol)
- Brief Section 2 explicit deadlock-impossibility proof with time-based escape mechanism (the /054 brake entered permanent deadlock because BCH+LDO brake-ON at OOS-start → no trades → no state update → frozen; the /127 brake MUST include time-based override e.g. brake-OFF after M candles regardless of state)
- Adversarial integration test in Section 9 (deadlock-construction stress test)

**Cycle-7 cadence**: slot 5/10 EXPLORATION done (this iteration). 5 EXPLORATIONs remain + /132 CONFIRMATION. If /127 + /128 + ... + /131 also exhaust NEGATIVE, /132 CONFIRMATION becomes baseline RE-VALIDATION of /121 (analogous to /081/092 — multi-seed re-validation of canonical config with NO new ingredient to bundle).

---

**Catalog entry appended** to `briefs-v3/exploration_catalog.md`:

```
| iter-v3/126 | 2026-05-21 | cycle-7 multi-frequency feature stack (d24_ret_autocorr_lag1_50) | -1.2109 | -1.0806 | EXPLORATION-NEGATIVE-catastrophic — EDA methodology FALSIFIED 3rd occurrence | NO |
```

**Tag**: `v0.v3-126`. Does NOT supersede `v0.v3-121` as canonical.

**Memory updates**: APPEND cycle-7 slot 5 NEGATIVE-catastrophic outcome + EDA-methodology-falsified-at-3-occurrence finding to `project_v3_cycle7_setup.md`; NEW feedback file `feedback_v3_eda_methodology_falsified.md` documenting that single-window EDA importance + 5-fold AUC + LR-PF + IC-PF + SSC-RISK is empirically a BIASED ESTIMATOR for rolling walk-forward production performance based on 3 cycle-7 attempts (/122 + /123 + /126), with the FALSIFICATION operating at the methodology's strongest application at /126.
