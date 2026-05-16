# Engineering Report — iter-v3/079

## Headers

- Iteration: iter-v3/079
- Branch: iteration-v3/047 (cycle-2 shared branch)
- Commit chain (EDA → brief → SHAs backfill → setup → Phase 5.5 gate → implementation):
  - EDA: `0a54acd` — `analysis/iteration_v3-079/sizing_axis_eda.py` (T1–T8 + summary.csv)
  - Brief: `b61c8a8` — `briefs-v3/iteration_v3-079/research_brief.md`
  - Brief SHAs backfill: `06e6b1c` — backfilled setup + gate SHAs in brief Section 10.3
  - Setup: `3dbbd4b` — `run_baseline_v3.py` V3_MODELS ADA→LDO revert + ITERATION_LABEL "v3-079"
  - Phase 5.5 gate: `d93cfac` — PASS
  - Implementation: `8c36e2a` — primitive 13 conviction-derate map in `src/`
  - HEAD at report time: `8c36e2a`
- Hardware: WSL2 / Linux 6.6.114.1-microsoft-standard-WSL2
- Wall-clock time: 0.68h (within 2.0h EXPLORATION cap; `--skip-features` per setup)
- Run mode: `--exploration --skip-features --n-trials 35` (`EXPLORATION_ENSEMBLE_SIZE = 3`, `ENSEMBLE_SEEDS[0:3]`, 3 outer seeds)
- Seeds: `[191664963, 1662057957, 1405681631]` (outer=42 lineage subset)
- Total Optuna trials: 315 (3 seeds × 3 symbols × 35 trials)

---

## Configuration Diff vs /060 EXPLORATION-MODE ANCHOR (re-anchored)

The /079 brief adopted Critic /077 Rec #1 and re-anchors against the current-code /060-config baseline: IS +0.8236 / OOS +0.2078 (established by /077's diagnostic run of the /060 14-feature config on current code + current data). The stale frozen /060 anchor (+0.8325/+0.1403) is NOT used for /079 deltas.

| Parameter | /060 (anchor) | /079 |
|---|---|---|
| `V3_MODELS` | BCH + LDO + TRX | **BCH + LDO + TRX** (baseline-restore: /078's ADA reverted back to LDO) |
| conviction-derate (primitive 13) | absent | PRESENT — `conviction_derate(confidence)` replaces `weight=100` in `LightGbmStrategy.get_signal` |
| `ITERATION_LABEL` | `"v3-060"` | `"v3-079"` |
| All other params (features, labeling, risk gates, seeds, n_trials) | — | UNCHANGED |

Sacred constants confirmed: `OOS_CUTOFF_DATE = "2025-03-24"`, `TRAINING_MONTHS = 24`.

The /078 SUSPICIOUS-OOS-DOMINANT (ADA universe-revision axis) has been reverted. The V3_MODELS revert to BCH/LDO/TRX is the mandated baseline-restore (a closed axis revert, not a new varied axis). The primary axis is the conviction-derate sizing primitive.

---

## Key Metrics Block

### Headline vs re-anchored current-code /060-config baseline (brief Section 4.1 prediction in parentheses)

| Metric | Anchor IS | /079 IS | IS Δ | Anchor OOS | /079 OOS | OOS Δ | /079 OOS/IS ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | +0.8236 | **+0.8288** | **+0.0052** | +0.2078 | **+0.2791** | **+0.0713** | **0.3368** |
| daily_sharpe | — | +1.7387 | — | — | +0.7403 | — | 0.4258 |
| max_drawdown | — | 31.84% | — | — | 36.31% | — | 1.1406 |
| profit_factor | — | 1.2871 | — | — | 1.0983 | — | 0.8533 |
| win_rate | — | 31.4% | — | — | 39.8% | — | 1.2658 |
| n_trades | ~159 (anchor) | **159** | **0** | ~103 (anchor) | **103** | **0** | 0.6478 |
| total_pnl | — | 52.4370 | — | — | 11.2924 | — | 0.2154 |
| monthly_calmar | — | 1.6471 | — | — | 0.3110 | — | 0.1888 |
| pbo | 0.1278 (anchor) | **0.1278** | 0 | — | — | — | — |
| psr | — | 1.0000 | — | — | — | — | — |
| dsr | 0.0 | 0.0 | — | — | — | — | — |
| dsr_relative_b4 | — | 0.4200 | — | — | — | — | — |
| frac_positive_paths | 0.644 (anchor) | **0.644** | **0** | — | — | — | — |
| n_trials | 315 | 315 | 0 | — | — | — | — |
| n_effective_trials | 19 | 19 | 0 | — | — | — | — |

Note: DSR/PSR/DSR_relative_b4 are informational only at EXPLORATION mode (n_trials=315; EXPLORATION-mode DSR is a structural artifact per `feedback_v3_dsr_mode_artifact.md`).

### Per-symbol IS section

| Symbol | /079 trades | /079 win_rate | /079 net_pnl_pct | /079 weighted_pnl |
|---|---:|---:|---:|---:|
| BCHUSDT | 73 | 45.2% | +79.45% | +78.34 |
| LDOUSDT | 11 | 27.3% | −11.44% | −8.68 |
| TRXUSDT | 75 | 29.3% | −23.04% | −17.23 |

Anchor per-symbol IS (from /077): BCH 73/45.2%/+79.45/+78.34, LDO 11/27.3%/−11.44/−11.44, TRX 75/29.3%/−23.04/−23.04. The IS wpnl differences vs /077 (LDO: −8.68 vs −11.44; TRX: −17.23 vs −23.04) reflect the conviction-derate weight scalar reducing weighted_pnl for de-rated trades.

### Per-symbol OOS section (`comparison.csv` per_symbol block)

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | +1.9078 | 37 | 32.4% | 16.89% |
| LDOUSDT | −14.9133 | 12 | 25.0% | −132.06% |
| TRXUSDT | +24.2979 | 54 | 48.1% | 215.17% |

Note: concentration_pct computed against OOS total wpnl 11.29. The 30% per-symbol cap is a CONFIRMATION gate; informational here.

---

## Classification per Brief Section 8 LOCKED

Evaluation order per brief: SUSPICIOUS (8.4) → NULL-RESULT (8.5) → NEGATIVE (8.2) → PROMISING (8.1) → INERT (8.3). First match is canonical. Anchor: IS +0.8236 / OOS +0.2078 (re-anchored).

| Gate | Threshold | /079 result | Fires? |
|---|---|---|---|
| **SUSPICIOUS 8.4 — OOS/IS ratio > 3.0** | > 3.0 | **0.3368** | NO |
| **SUSPICIOUS 8.4 — OOS-DOMINANT sub-mode** | IS shift < 0 AND OOS shift ≥ +0.20 | IS shift +0.0052 (POSITIVE, fails IS < 0 clause) | NO |
| **NULL-RESULT 8.5 — behavioral saturation** | < 15% of IS trades de-rated | **7.5% de-rated (12/159)** | **YES — fires** |
| NEGATIVE 8.2 | IS < −0.10 OR OOS < −0.20 | IS +0.0052 (> −0.10); OOS +0.0713 (> −0.20) | Does not apply (NULL-RESULT already fired) |
| PROMISING 8.1 | IS ≥ +0.10 AND OOS ≥ +0.20 AND not SUSPICIOUS | IS +0.0052 (< +0.10) | Does not apply |
| INERT 8.3 | Both in-band AND de-rate ≥ 15% AND not SUSPICIOUS | De-rate 7.5% < 15% (INERT requires ≥ 15%) | Does not apply |

**CLASSIFICATION: NULL-RESULT (behavioral saturation).**

**Correction vs task dispatch brief.** The task dispatch suggested INERT-AT-EXPLORATION; however the locked Section 8 text is unambiguous: Section 8.5 fires when "< 15% of IS trades are de-rated (the behavioral-effect falsifier, Section 4.3)." The observed de-rate is 7.5% (12/159 IS trades), which is below the 15% NULL-RESULT threshold. Section 8.3 (INERT) explicitly requires "the roster is behaviorally changed (≥ 15% of IS trades de-rated)." Since only 7.5% were de-rated, the INERT condition fails, and NULL-RESULT fires by Section 8.5. The per brief's disjunctive order: NULL-RESULT (8.5) is evaluated before INERT (8.3) and fires first.

**NO-MERGE. The conviction-derate axis does NOT advance to the cycle-2 CONFIRMATION.**

---

## Conviction-Derate as Pure Weight Scalar — Verification

### (a) IS and OOS roster key bit-identity vs /077

A pure post-model per-trade weight scalar adds and removes zero trades. Verified by field diff:

| Split | Symbol | /077 n | /079 n | Keys added | Keys removed |
|---|---|---:|---:|---:|---:|
| IS | BCH | 73 | 73 | 0 | 0 |
| IS | LDO | 11 | 11 | 0 | 0 |
| IS | TRX | 75 | 75 | 0 | 0 |
| OOS | BCH | 37 | 37 | 0 | 0 |
| OOS | LDO | 12 | 12 | 0 | 0 |
| OOS | TRX | 54 | 54 | 0 | 0 |

**The (symbol, open_time) key roster is BIT-IDENTICAL between /077 and /079 for all six symbol-split pairs.** The Section 8.6 Phase-6 BLOCK condition (any trade added or removed vs the /060 key roster) does NOT fire. Implementation is wiring-correct: the conviction-derate changes weights, not trade selection.

### (b) Holding-time full-roster mean-duration delta

| Split | /077 mean duration (candles) | /079 mean duration (candles) | Delta |
|---|---:|---:|---:|
| IS | 6.3145 | 6.3145 | **0.0000** |
| OOS | 6.4660 | 6.4854 | **+0.0194** |

IS delta is exactly 0.0000 candles — confirmed holding-time-orthogonal on IS, as predicted (Section 4.4 brief). The OOS delta of +0.0194 candles is attributable to data-extent drift: the last LDO OOS trade (open_time=1778716799999) is an `end_of_data` position whose exit price and close_time differ between /077 and /079 because /079 ran on 2 additional candles of OOS data (close_time shifted from 2026-05-15 07:59:59 UTC to 23:59:59 UTC — a 16.0-hour / 2-candle extension). This is data-extent drift, not a barrier-touch from the conviction scalar. The weight scalar does NOT move any TP/SL/timeout barrier.

---

## Behavioral-Effect Predictor — Actual De-Rate Count

The brief Section 4.3 pre-registered that ≥ 25% of IS trades would be de-rated (falsifier < 15%).

**Actual IS de-rated count: 12 of 159 trades = 7.5%.**

This is below BOTH the predicted lower bound (25%) AND the falsifier threshold (15%). The behavioral-effect falsifier fires definitively.

Per-symbol IS de-rate breakdown:

| Symbol | IS trades | De-rated | Pct |
|---|---:|---:|---:|
| BCHUSDT | 73 | 6 | 8.2% |
| LDOUSDT | 11 | 0 | 0.0% |
| TRXUSDT | 75 | 6 | 8.0% |
| ALL | 159 | 12 | **7.5%** |

LDO had zero de-rated IS trades — LDO's Optuna-tuned confidence threshold for its walk-forward models was consistently ≥ 0.65, placing every surviving LDO IS signal at or above the clear-conviction reference. BCH and TRX each had exactly 6 de-rated trades: the de-rate fired only when the walk-forward model's Optuna threshold sat below 0.65 AND the surviving signal's confidence was in [0.60, 0.65).

**OOS de-rated count: 1 of 103 trades = 1.0%** — one TRX OOS trade (open_time=1760803199999) had its wf lowered from 0.76 to 0.64. The OOS de-rate was essentially null (1 trade).

---

## Why NULL-RESULT — The Mechanism

The conviction-derate map was designed to fire on confidence values in [0.60, 0.65) — trades that barely cleared the model's binary confidence threshold but remain below the a-priori clear-conviction reference of 0.65. The null firing-rate finding is mechanistically explained:

The walk-forward Optuna search optimizes the `_inference_threshold` for each (symbol, month) cell. When Optuna tuned thresholds at or above 0.65, the de-rate window [C_FLOOR=0.50, C_REF=0.65) is entirely below the inference floor — zero trades can land in the de-rate band. The /067 `_inference_threshold_floor` guarantees every surviving signal has confidence ≥ 0.60, but Optuna frequently chose thresholds ≥ 0.65 (above C_REF), leaving no room for the conviction-derate to fire. Only 12 IS trades survived with confidence in [0.60, 0.65).

**Did the de-rated (low-conviction) trades underperform the full-weight trades?**

Comparing /077 vs /079 IS weight changes isolates exactly which 12 trades received a de-rate. Their mean `net_pnl_pct` from the /077 roster (pre-derate, unconfounded by weight):

| Group | n | Mean net_pnl_pct | Win rate |
|---|---:|---:|---:|
| De-rated (confidence in [0.60, 0.65)) | 12 | **−0.019%** | 33.3% |
| Not de-rated (non-zero wf, confidence ≥ 0.65) | 121 | **+0.476%** | 38.0% |

The 12 de-rated trades did have slightly worse per-trade outcomes than the non-de-rated group (mean −0.019% vs +0.476%, WR 33.3% vs 38.0%). The conviction-derate MAP's directional hypothesis (low-confidence trades are worse) is directionally supported by this small sample. However, the de-rated population is so small (12 trades = 7.5%) that the weight reduction of this tail produced a trivially small IS Sharpe delta (+0.0052) — the axis barely engaged. The mechanism for NULL-RESULT is not that low-conviction trades were NOT worse; they were slightly worse. The mechanism is that the axis fired on too few trades to move the aggregate metric.

**Why did so few trades land in the de-rate window?** The brief (Section 2.3) predicted that "the de-rate window is the [0.60, 0.65) confidence band plus any cell whose Optuna-tuned threshold sits below 0.65." In practice, the Optuna search at n_trials=35 concentrated thresholds at ≥ 0.65 for the majority of (symbol, month) cells — the 8h directional problem's IS-optimized threshold sits above the a-priori C_REF. The `/067 inference_threshold_floor=0.60` sets the minimum, but the production IS-optimized thresholds were systematically higher, compressing the de-rate window toward empty.

---

## Per-Symbol Note — BCH OOS Bit-Identity

BCH OOS: 37 trades, weighted_pnl +1.9078 in both /077 and /079 — identical to 4 decimal places. BCH OOS had zero de-rated trades (all 37 BCH OOS weight_factor values matched /077 exactly). BCH's OOS weights were unchanged by the conviction-derate.

The OOS total wpnl change (+8.22 in /077 vs +11.29 in /079, Δ +3.07) decomposes as follows:
- **LDO OOS: +3.49 improvement** — attributable entirely to data-extent drift. The last LDO OOS trade (open_time=1778716799999, exit_reason=`end_of_data`) ran 2 additional candles in /079 (close_time extended 16 hours), capturing a +3.49 wpnl gain. This is a data-freshness artifact, not a conviction-derate effect.
- **TRX OOS: −0.42 decrease** — attributable to the single TRX OOS de-rated trade. That trade's wf changed from 0.76 to 0.64; net_pnl_pct = +3.50%, so wpnl change = (0.64 − 0.76) × 3.50 = −0.42. The calculation is exact.
- **BCH OOS: 0.0000 change** — bit-identical, zero de-rates.

The OOS monthly Sharpe lift (+0.0713 vs anchor) thus reflects primarily data-extent drift on the LDO last-trade position, partially offset by the TRX conviction-derate wpnl reduction. Neither effect is attributable to the conviction-derate axis carrying genuine OOS edge.

---

## Conditional-Orthogonality Instrumentation

`conditional_orthogonality.csv` was emitted — 14 rows × 6 columns (HYBRID PART A last-month portfolio importance share + PART B EDA per-month map from SHA `313d3c0`, carried from /077). No `cusum_reset_count_200` warning appeared in `run.log` (confirmed: 0 matching lines; 0 WARNING lines total). The /077-committed ADF falsifier removal (`20c65cd`) holds; LDO's short-history artifact is absent.

---

## Feature Importance (Last Walk-Forward Month Portfolio)

| Rank | Feature | Portfolio importance |
|---:|---|---:|
| 1 | ret_skew_200 | 816.3 |
| 2 | vwap_dev_20 | 759.7 |
| 3 | range_realized_vol_50 | 706.3 |
| 4 | ema_spread_atr_20 | 698.7 |
| 5 | max_dd_window_50 | 646.3 |
| 6 | ret_autocorr_lag1_50 | 607.0 |
| 7 | ret_kurt_50 | 598.0 |
| 8 | hurst_diff_100_50 | 593.3 |
| 9 | ret_kurt_200 | 582.0 |
| 10 | btc_ret_14d | 582.0 |
| 11 | hurst_100 | 569.3 |
| 12 | ret_skew_50 | 520.3 |
| 13 | sym_vs_btc_ret_7d | 511.7 |
| 14 | regime_momentum_signed_5d | 506.7 |

`regime_momentum_signed_5d` is rank 14/14 in this EXPLORATION run (last position). No degenerate or pathological concentration; importance distribution is broadly spread. The conviction-derate is a weight scalar applied post-signal and does not appear in the feature-importance output (it is not a feature; it is a sizing modifier).

---

## ADF and IC Matrix Notes

ADF: 2198 rows emitted (per sym × feat × month: BCH 63 months × 14 feats = 882; TRX 63 × 14 = 882; LDO 31 × 14 = 434; total 2198). Within the expected [1302, 2646] band. No warnings in `run.log`. IC matrix: 14 × 14 confirmed.

---

## Seed Concentration Audit

Single-axis EXPLORATION (outer=42 lineage, 3 seeds). IS total wpnl = 52.44: BCH 78.34 (149%), LDO −8.68 (−17%), TRX −17.23 (−33%). OOS: TRX 91.38% of non-LDO-drag total (TRX-dominant as in /077/078). The 30% per-symbol cap is a CONFIRMATION gate; informational here. BCH IS wpnl share is inflated above 100% due to LDO and TRX being IS-drag (their negative wpnl offsets the denominator).

---

## Label Leakage Audit

- `REQUIRED_GAP = 66 = (21 + 1) × 3 symbols` — confirmed unchanged.
- Embargo = 22 candles — unchanged.
- `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}` confirmed: all symbols use `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`.
- The conviction-derate map is applied inside `get_signal` after the model's `predict_proba` call, which operates on past-only features from the walk-forward training window. No future bar is consulted. Look-ahead-clean by construction.
- Walk-forward lookahead-bias note (`feedback_v3_walkforward_lookahead_bug.md`) applies equally to /079. IS/OOS deltas vs /077/060 are valid; absolute magnitudes uniformly biased upward.

---

## Gate Efficacy Table

All risk gates unchanged from /060. The conviction-derate map (primitive 13) is a sizing modifier, not a gate.

| Primitive | State | IS fire rate | OOS note |
|---|---|---|---|
| 1 — Feature OOD z > 2.0 | ON | same as /060 anchor (bit-identical BCH/TRX; LDO unchanged) | same as /060 for BCH/TRX |
| 2 — Hurst regime | ON | same as /060 anchor | same as /060 for BCH/TRX |
| 3 — ADX gate | ON | same as /060 anchor | same as /060 for BCH/TRX |
| 4 — Low-vol filter | ON | same as /060 anchor | same as /060 for BCH/TRX |
| 5 — Vol-adjusted sizing | ON | same as /060 anchor | same as /060 for BCH/TRX |
| 9 — Regime kill switch | OFF (CLOSED axis) | 0 | — |
| 10 — Direction kill switch | OFF (reverted /051) | 0 | — |
| 11 — Per-symbol drawdown brake | OFF (CLOSED /054) | 0 | — |
| 12 — BTC-trend-regime SIZE de-rate | OFF (reverted /076) | 0 | — |
| **13 — Conviction-derate (primitive 13)** | ON | **12/159 IS = 7.5%; 1/103 OOS = 1.0%** | Behavioral saturation confirmed |

TRX `vol_scale_floor=0.5` (from /061) active and unchanged.

---

## Anomaly Notes

1. **Spot-check 10 random OOS trades — 0 math errors.** Verified formula: `weighted_pnl = net_pnl_pct × weight_factor` (weight_factor already in [0, 1] range from `(signal.weight/100) × vt_scale`). All 10 sampled OOS trades pass (0 errors). Exit reasons (take_profit, stop_loss, timeout, end_of_data) are self-consistent. No zero-trade OOS months.

2. **Classification is NULL-RESULT per locked Section 8, not INERT.** The task dispatch pre-suggested INERT; the locked brief text (Section 8.3 vs 8.5) is the canonical authority. 7.5% de-rated < 15% fires Section 8.5 NULL-RESULT, which precedes INERT in the disjunctive order. INERT requires ≥ 15% de-rated (Section 8.3 clause: "the roster is behaviorally changed (≥ 15% of IS trades de-rated)"). This is not ambiguous.

3. **No NaN Sharpe, no zero-trade IS months, no NaN PnL.** IS monthly_pnl.csv: 36 rows, all with positive trade_count and numeric pnl_pct. OOS monthly_pnl.csv: 14 rows, all clean. IS monthly Sharpe = +0.8288 (matches comparison.csv). OOS = +0.2791 (matches).

4. **LDO and TRX bit-identity on IS** — zero weight_factor diffs on non-BCH-de-rated IS trades; conviction-derate fired exclusively within BCH (6 trades) and TRX (6 trades) sub-rosters on IS, and LDO had zero de-rates across both IS and OOS.

5. **OOS Sharpe lift (+0.0713) is data-extent artifact, not conviction-derate signal.** The OOS total wpnl increased by +3.07 vs /077: +3.49 from LDO's last-trade data-extent extension (2 extra candles of `end_of_data` position, a monotonic calendar artifact), and −0.42 from the single TRX OOS de-rate. The net OOS monthly Sharpe lift is driven by data-extent drift, not by the axis producing edge.

6. **PBO = 0.1278, frac_positive_paths = 0.644** — identical to the re-anchored baseline. The conviction-derate's 7.5% de-rate affected so few trades that the CPCV path distribution is unchanged. This is a clean null-result signal.

---

## Status

OVERALL = READY-FOR-CRITIC

**Classification: NULL-RESULT (behavioral saturation) — NO-MERGE. The conviction-derate axis does NOT advance to the cycle-2 CONFIRMATION.**

Firing ground per locked Section 8: Section 8.5 fires because 7.5% of IS trades were de-rated (12/159), below the 15% behavioral-effect falsifier threshold. Section 8.5 precedes Section 8.3 (INERT) in the disjunctive evaluation order; NULL-RESULT is the canonical first-match outcome.

The behavioral-effect falsifier (Section 4.3) fires definitively: predicted ≥ 25% de-rated (central 25%), observed 7.5%. The prediction missed by 3×. The mechanism: the walk-forward Optuna search at n_trials=35 concentrated (symbol, month) inference thresholds at or above 0.65 (the a-priori C_REF), leaving essentially no surviving signals in the [C_FLOOR=0.50, C_REF=0.65) conviction-derate window. The a-priori C_REF of 0.65 was placed above most of the IS-optimized thresholds rather than in the busy part of the confidence distribution.

The de-rated 12 IS trades did show slightly worse outcomes than the non-de-rated group (mean net_pnl_pct −0.019% vs +0.476%, WR 33.3% vs 38.0%), supporting the directional hypothesis that low-conviction trades are marginally worse. But at 7.5% de-rate incidence the effect on the aggregate IS/OOS Sharpe is negligible (+0.0052 IS / +0.0713 OOS, with the OOS lift attributable to data-extent drift rather than the axis).

The (symbol, open_time) key roster is BIT-IDENTICAL between /077 and /079 for all six symbol-split pairs (IS BCH/LDO/TRX and OOS BCH/LDO/TRX) — zero trades added, zero removed. Holding-time IS delta = exactly 0.0000 candles. The wiring is correct: primitive 13 is a pure weight scalar, not a trade-selection filter. `conditional_orthogonality.csv` emitted (14 rows, HYBRID PART A+B). Zero warnings in `run.log`.

---

Phase 6 complete. Engineering report committed. Phase 7.5 Critic review required before Phase 7. Orchestrator: invoke `quant-critic` with branch=`iteration-v3/047`, report_dir=`reports-v3/iteration_v3-079`, brief_dir=`briefs-v3/iteration_v3-079`.
