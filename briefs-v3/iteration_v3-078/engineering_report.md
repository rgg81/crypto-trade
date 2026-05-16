# Engineering Report — iter-v3/078

## Headers

- Iteration: iter-v3/078
- Branch: iteration-v3/047 (cycle-2 shared branch)
- Commit chain (EDA → brief → brief backfill → setup → Phase 5.5 gate):
  - EDA: `e48ebad` — `analysis/iteration_v3-078/axis_selection_eda.py` + 11 output CSVs (T0–T8 + T_regime_label + axis_selection_summary)
  - Brief: `7be5323` — `briefs-v3/iteration_v3-078/research_brief.md`
  - Brief backfill: `ba35f66` — backfilled setup + gate SHAs in brief Section 10.3
  - Setup: `0648504` — `run_baseline_v3.py` V3_MODELS LDOUSDT→ADAUSDT + ITERATION_LABEL "v3-078" + 5 test files
  - Phase 5.5 gate: `9b475b4` — PASS
  - HEAD at report time: `9b475b4`
- Hardware: WSL2 / Linux 6.6.114.1-microsoft-standard-WSL2
- Wall-clock time: 0.89h (within 2.0h EXPLORATION cap; `--skip-features` because ADAUSDT parquet was pre-regenerated at setup)
- Run mode: `--exploration --skip-features` (`EXPLORATION_ENSEMBLE_SIZE = 3`, `ENSEMBLE_SEEDS[0:3]`, `--n-trials 35`)
- Seeds: `[191664963, 1662057957, 1405681631]` (outer=42 lineage subset)
- Total Optuna trials: 315 (3 seeds × 3 symbols × 35 trials)

---

## Configuration Diff vs /060 EXPLORATION-MODE ANCHOR (re-anchored)

The /078 brief adopted Critic /077 Rec #1 and re-anchors against the current-code /060-config baseline: IS +0.8236 / OOS +0.2078 (established by /077's diagnostic run of the /060 14-feature config on current code + current data). The stale frozen /060 anchor (+0.8325/+0.1403) is NOT used for /078 deltas.

| Parameter | /060 (anchor) | /078 |
|---|---|---|
| `V3_MODELS` | BCH + LDO + TRX | **BCH + ADA + TRX** (LDOUSDT replaced by ADAUSDT) |
| `_write_conditional_orthogonality()` | absent | PRESENT (carried from /077 — accretive tooling, not an axis) |
| `ITERATION_LABEL` | `"v3-060"` | `"v3-078"` |
| All other params (features, labeling, risk gates, seeds, n_trials) | — | UNCHANGED |

`vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` (introduced iter-v3/061) is present and unchanged. ADAUSDT, like LDOUSDT before it, uses the global vol floor (LDO was never a key in that dict; the removal leaves it correct for ADA).

Sacred constants confirmed: `OOS_CUTOFF_DATE = "2025-03-24"`, `TRAINING_MONTHS = 24`.

---

## Key Metrics Block

### Headline vs re-anchored current-code /060-config baseline (brief prediction in parentheses)

| Metric | Anchor IS | /078 IS | IS Δ | Anchor OOS | /078 OOS | OOS Δ | /078 OOS/IS ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | +0.8236 | **+0.8201** | **-0.0035** | +0.2078 | **+0.6892** | **+0.4814** | **0.8404** |
| daily_sharpe | — | +1.8242 | — | — | +1.6531 | — | 0.9062 |
| max_drawdown | — | 27.49% | — | — | 28.02% | — | 1.019 |
| profit_factor | — | 1.2856 | — | — | 1.2401 | — | 0.9646 |
| win_rate | — | 33.3% | — | — | 39.4% | — | 1.1835 |
| n_trades | ~159 (anchor) | **222** | **+63** | ~103 (anchor) | **109** | **+6** | 0.491 |
| total_pnl | — | 75.2402 | — | — | 27.0492 | — | 0.3595 |
| monthly_calmar | — | 2.7366 | — | — | 0.9655 | — | 0.3528 |
| pbo | 0.1278 (anchor) | **0.1277** | ~0 | — | — | — | — |
| psr | — | 1.0000 | — | — | — | — | — |
| dsr | 0.0 | 0.0 | — | — | — | — | — |
| dsr_relative_b4 | — | 0.9999 | — | — | — | — | — |
| frac_positive_paths | 0.644 (anchor) | **0.733** | **+0.089** | — | — | — | — |
| n_trials | 315 | 315 | 0 | — | — | — | — |
| n_effective_trials | 19 | 19 | 0 | — | — | — | — |

Note: DSR/PSR/DSR_relative_b4 are informational only at EXPLORATION mode (n_trials=315; EXPLORATION-mode DSR is a structural artifact per `feedback_v3_dsr_mode_artifact.md`).

### Per-symbol IS section

| Symbol | /078 trades | /078 win_rate | /078 net_pnl_pct | /078 weighted_pnl |
|---|---:|---:|---:|---:|
| BCHUSDT | 73 | 45.2% | +79.45% | +78.34 |
| ADAUSDT | 74 | 40.5% | +46.96% | +21.85 |
| TRXUSDT | 75 | 29.3% | -23.04% | -24.95 |

Anchor (from /077 IS per_symbol): BCH 73/45.2%/+79.45, LDO 11/27.3%/-11.44, TRX 75/29.3%/-23.04.

### Per-symbol OOS section

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| ADAUSDT | +0.4230 | 18 | 27.8% | 1.56% |
| BCHUSDT | +1.9078 | 37 | 32.4% | 7.05% |
| TRXUSDT | +24.7184 | 54 | 48.1% | 91.38% |

Note: concentration_pct computed against OOS total wpnl 27.0492. The 30% per-symbol cap is a CONFIRMATION gate; informational here. TRX's 91% concentration reflects its dominance of the OOS period.

---

## Classification per Brief Section 8 LOCKED

Evaluation order per brief: SUSPICIOUS (8.4) → NULL-RESULT (8.5) → NEGATIVE (8.2) → PROMISING (8.1) → INERT (8.3). First match is canonical. Anchor: IS +0.8236 / OOS +0.2078 (re-anchored).

| Gate | Threshold | /078 result | Status |
|---|---|---|---|
| **SUSPICIOUS — OOS/IS ratio > 3.0** | > 3.0 | **0.8404** | Does not fire |
| **SUSPICIOUS-OOS-DOMINANT — IS shift < 0 AND OOS shift ≥ +0.20** | IS<0 AND OOS≥+0.20 | IS -0.0035 (<0: TRUE) AND OOS +0.4814 (≥+0.20: TRUE) | **FIRES** |
| NULL-RESULT | bit-identical roster | mechanically impossible (universe swap) | Does not apply |
| NEGATIVE | IS<-0.10 OR OOS<-0.20 | IS -0.0035 (>-0.10), OOS +0.4814 (>-0.20) | Does not fire |
| PROMISING | IS≥+0.10 AND OOS≥+0.20 AND frac_pos≥0.50 AND not SUSPICIOUS | IS -0.0035 (<+0.10) | Fails IS gate; also blocked by SUSPICIOUS |
| INERT | both in-band AND not SUSPICIOUS | blocked by SUSPICIOUS | Does not apply |

**CLASSIFICATION: SUSPICIOUS-OOS-DOMINANT.**

The SUSPICIOUS-OOS-DOMINANT sub-mode fires on both conditions simultaneously: IS shift -0.0035 is negative (strictly < 0) AND OOS shift +0.4814 clears the +0.20 threshold. Per brief Section 8.4, SUSPICIOUS "fires on EITHER ground ... with no magnitude qualifier" and takes precedence in the disjunctive order over all other outcomes. The ratio gate did NOT fire (0.8404 < 3.0) — but the sub-mode is a separate, independent SUSPICIOUS ground. The healthy OOS/IS ratio means only that the ratio gate is absent; the sub-mode is the firing trigger.

This is NOT a reclassification opportunity. PROMISING (8.1) requires IS shift ≥ +0.10 independently; /078's IS shift is -0.0035, so PROMISING fails its own IS gate regardless of SUSPICIOUS. The brief's Section 7 pre-registered SUSPICIOUS-OOS-DOMINANT at ≈43% probability (the cycle-2 base rate), explicitly predicting "IS Δ < 0, OOS Δ ≥ +0.20" as the sub-mode signature. The pre-registration matches the observed outcome.

**NO-MERGE. LDOUSDT is retained. The universe-revision axis does NOT advance to the cycle-2 CONFIRMATION.**

---

## Hypothesis Falsification

### Primary falsifier (brief Section 4.2): IS Δ < +0.10 → hypothesis falsified

The brief's Section 1 hypothesis states ADA would "lift the IS aggregate monthly Sharpe without the IS-up/OOS-down regime tension." Section 4.1 predicted IS Δ +0.13 to +0.33 (central +0.20). Section 4.2 sets the explicit falsifier: "The hypothesis is falsified if the /078 IS monthly Sharpe Δ vs the +0.8236 anchor is below +0.10."

Observed IS Δ = -0.0035. The falsifier fires.

**Mechanism:** ADA traded actively — 74 IS trades vs LDO's 11, within the predicted 50–90 range (Section 4.3). ADA's IS wpnl contribution is positive (+21.85 vs LDO's -1.66, a +23.51 IS wpnl swing). However, ADA's 74-trade IS participation also proportionally raised IS monthly variance. The IS monthly mean PnL rose from +1.57 to +2.09 (+33%), but IS monthly std rose from 6.59 to 8.83 (+34%) — the variance increase matched the mean lift, producing IS Sharpe -0.0035 vs anchor (flat, not lifted).

The T7 IS-edge screen predicted ADA at +0.617 IS Sharpe (vs LDO -0.550) on a coarse single-seed fixed-parameter proxy. That screen's IS-Sharpe metric reflects the per-symbol model in isolation. The production 3-seed walk-forward measures the portfolio monthly Sharpe across BCH+ADA+TRX, where BCH (78.34 wpnl, 76.9% of IS total) dominates the monthly PnL distribution, and ADA's variance contribution enters the aggregate as a denominator driver, not only a numerator driver. The T7 screen correctly predicted ADA's positive IS edge at the symbol level; it did not predict the portfolio-variance impact that kept the aggregate Sharpe flat.

**Secondary falsifier (brief Section 4.2):** OOS Δ < -0.20 would have fired a second falsifier. Observed OOS Δ = +0.4814, so this falsifier does NOT fire. The OOS lift is real in absolute terms but is uncorroborated by IS — the defining signature of SUSPICIOUS-OOS-DOMINANT.

---

## Mechanism Nuance: /078 vs Prior SUSPICIOUS-OOS-DOMINANT Cases

/078 is SUSPICIOUS-OOS-DOMINANT, but its internal structure differs from the prior cycle-2 cases (/071, /073, /076):

| Iteration | IS shift | OOS shift | OOS/IS ratio | IS collapse type |
|---|---:|---:|---:|---|
| /071 | -0.55 | +0.28 | 4.51× | Large IS collapse (meta-label M2 over-filter) |
| /073 | -0.79 | +0.60 | 15.04× | Large IS collapse + ratio blow-up |
| /076 | -0.55 | +0.19 (near-SUSPICIOUS) | ~3.8× | Large IS collapse (BTC-trend de-rate) |
| **/078** | **-0.0035** | **+0.48** | **0.84×** | **Mild-negative — IS lift failed to materialize** |

/078's IS shift is -0.0035: essentially flat, not an IS collapse. The ratio is 0.84 (healthy). The classification is the same (SUSPICIOUS-OOS-DOMINANT sub-mode) but the mechanism is different: /078 is a case of "predicted IS lift failed to materialize + uncorroborated OOS lift," not "IS actively destroyed by the axis." The prior cases all had large IS collapses and often high ratios because the axis suppressed IS trades that were OOS winners — the /075 escapability-bound regime tension. /078's mechanism is subtler: ADA's added IS variance exactly offset its added IS mean, leaving the aggregate Sharpe flat, while ADA's OOS behavior (TRX dominating OOS at 91%) was not independently confirmed.

This distinction is a description nuance for the diary. It does NOT change the verdict: the SUSPICIOUS-OOS-DOMINANT sub-mode fired, NO-MERGE is correct, and LDOUSDT is retained.

---

## Single-Axis Discipline Forensic (Brief Section 4.3 Falsifier)

The brief predicted BCH and TRX sub-rosters would be UNCHANGED — they are independent per-symbol models, so a universe swap of the third symbol should not touch them. The pre-registered falsifier: if BCH or TRX (symbol, open_time) IS sub-roster differs from /077's beyond the 3-seed non-determinism band, this is a Phase-6 wiring defect.

**Results from trade-key diff (/078 vs /077):**

| Split | Symbol | /077 n | /078 n | Added | Removed |
|---|---|---:|---:|---:|---:|
| IS | BCH | 73 | 73 | 0 | 0 |
| IS | TRX | 75 | 75 | 0 | 0 |
| OOS | BCH | 37 | 37 | 0 | 0 |
| OOS | TRX | 54 | 54 | 0 | 0 |

**Field-by-field weight_factor verification:** Zero weight_factor differences for BCH IS (73 common rows) and TRX IS (75 common rows). Zero differences for BCH OOS (37) and TRX OOS (54).

**BCH and TRX sub-rosters are ABSOLUTELY BIT-IDENTICAL between /077 and /078.** The universe swap did not leak into the non-target symbols. No wiring defect. The Section 4.3 falsifier does NOT fire.

The per-symbol OOS wpnl confirms: BCH +1.9078/37 and TRX +24.7184/54 are identical in /078 and /077 to 4 decimal places. The entire OOS performance difference is attributable to ADA (0.4228/18) replacing LDO (-18.4079/12).

---

## ADA Contribution Analysis

### ADA IS contribution

ADA IS produced 74 trades (within the Section 4.3 predicted range of 50–90), 40.5% WR, net_pnl_pct +46.96%, weighted_pnl +21.85. ADA IS net PnL contribution is **positive** — ADA is a net IS contributor and lifted total IS wpnl from 51.73 (anchor) to 75.24 (+45%).

However, ADA's positive IS contribution lifted IS aggregate monthly *variance* proportionally to its mean lift, leaving IS monthly Sharpe flat (-0.0035). ADA replaced LDO (11 IS trades, -1.66 wpnl, a near-zero contributor that dominated the monthly PnL distribution by being thin and negative). Adding 74 ADA trades increased monthly portfolio PnL dispersion across 36 IS months — ADA's per-month IS PnL contribution was not smooth enough to lift the Sharpe ratio net of its added variance. The IS aggregate Sharpe's stability in the face of a +45% IS wpnl lift is a BCH-dominance artifact: BCH (78.34 IS wpnl, 76.9% of total) anchors the aggregate monthly PnL so strongly that ADA's contribution enters primarily as noise around BCH's trajectory, not as a mean-lifter of the Sharpe.

### ADA OOS contribution

ADA OOS: 18 trades / 27.8% WR / net_pnl_pct -14.56% / weighted_pnl +0.42. The OOS wpnl is marginally positive (driven by negative net_pnl_pct partially offset by weight_factor). ADA's OOS edge is weak: 27.8% WR on 18 trades is below the 50% threshold. The OOS wpnl of +0.42 is ADA's standalone OOS contribution; the +0.4814 OOS aggregate Sharpe lift is dominated by the removal of LDO (-18.41 OOS wpnl in /077) rather than ADA's own OOS performance.

**ADA's IS role:** net positive IS contributor (lifted IS wpnl +45%), but variance-matched — did NOT lift IS Sharpe.
**ADA's OOS role:** neutral-to-weak on standalone basis; the OOS lift is primarily attributable to LDO removal (ADA replaced a -18.41 OOS wpnl drag).

---

## Holding-Time and Behavioral Predictors

### Section 4.3 trade-count predictor

Predicted: 50–90 ADA IS trades. Observed: 74 ADA IS trades. **Within band — falsifier does not fire.**

### Section 4.4 duration predictors

| Channel | T8 prediction | Full-roster actual | Added-vs-removed actual | Falsifier threshold | Status |
|---|---|---|---|---|---|
| Full-roster delta vs anchor | small, ≈+0.1–0.2 candles | /077 6.31 → /078 6.66, **Δ +0.34 candles** | — | > +1.0 candle | **Does not fire** |
| Added (ADA) vs removed (LDO) label-implied gap | **+0.38 candles** | — | ADA 7.14 − LDO 4.91 = **+2.23 candles** | > +1.0 candle | **FIRES** |

**The added-vs-removed actual duration gap (+2.23 candles) exceeds the Section 4.4 falsifier threshold (+1.0 candle).** T8 predicted +0.38 (label-implied first-touch barrier simulation); the production walk-forward produced +2.23. The discrepancy is mechanistically explained: T8 used a screen-grade fixed-parameter simulation (Optuna DEFAULT n_estimators=120, ATR 2.0/1.0, timeout=21), whereas the production walk-forward uses Optuna-optimized timeout parameters. ADA incurred 5 IS timeout trades (none for LDO), each holding 21.0 candles (the timeout candle count). Excluding the 5 ADA timeout trades, the non-timeout duration gap is ADA 6.13 − LDO 4.91 = +1.22 candles — still above the +1.0 falsifier.

The full-roster falsifier (> +1.0 candle shift across all symbols) does NOT fire (+0.34 observed), because BCH and TRX are bit-identical and dilute the ADA-only duration shift across 3 symbols. The added-vs-removed sub-channel falsifier (the channel introduced by Critic /076 Rec #2) FIRES on the actual production data.

Per the brief, this firing means the swap may not be fully holding-time-orthogonal: the regime-loading-via-holding-time channel (sub-channel c from /076) cannot be mechanically excluded as a partial contributor to the OOS +0.48 lift. This reinforces the SUSPICIOUS-OOS-DOMINANT classification — the OOS lift is doubly uncorroborated: (a) the primary IS-Sharpe gate failed, and (b) the holding-time neutrality falsifier fired.

---

## Conditional-Orthogonality Instrumentation

`conditional_orthogonality.csv` was emitted (14 rows × 6 columns). The /077 instrumentation persists unchanged (accretive tooling carried forward). The HYBRID structure (PART A = last-month portfolio importance share from the /078 runner; PART B = the /077 EDA's full per-IS-month map, SHA `313d3c0`) is intact.

No `cusum_reset_count_200` ADF warning appeared in `run.log` (confirmed: 0 lines matching `cusum_reset_count`; 0 WARNING lines total). The stale ADF secondary-falsifier check was removed at the /077 diary step (commit `20c65cd`); the warning is absent as expected.

---

## Feature Importance (Last Walk-Forward Month Portfolio)

| Rank | Feature | Portfolio importance |
|---:|---|---:|
| 1 | ret_skew_200 | 569.3 |
| 2 | range_realized_vol_50 | 506.0 |
| 3 | vwap_dev_20 | 490.3 |
| 4 | ema_spread_atr_20 | 476.3 |
| 5 | max_dd_window_50 | 462.3 |
| 6 | ret_autocorr_lag1_50 | 456.0 |
| 7 | hurst_100 | 440.3 |
| 8 | hurst_diff_100_50 | 379.0 |
| 9 | ret_kurt_50 | 376.0 |
| 10 | sym_vs_btc_ret_7d | 360.7 |
| 11 | regime_momentum_signed_5d | 341.3 |
| 12 | btc_ret_14d | 328.7 |
| 13 | ret_kurt_200 | 322.7 |
| 14 | ret_skew_50 | 303.7 |

`regime_momentum_signed_5d` is rank 11/14 in the last walk-forward month (up from rank 14/14 at /077). ADA's top-3 features: `ret_skew_200`, `btc_ret_14d`, `range_realized_vol_50` — consistent with the broader portfolio pattern; no degenerate or pathological concentration.

---

## ADF and IC Matrix Notes

**ADF:** No warnings in `run.log`. 0 WARNING lines, 0 `cusum_reset_count` lines. The /077 ADF secondary-falsifier removal (commit `20c65cd`) successfully eliminated the benign LDO short-history artifact. ADAUSDT has deep history (parquet extends to early 2020) and generates no short-history edge cases.

**IC matrix:** 14×14 confirmed. No anomalies.

---

## Seed Concentration Audit

Single-axis EXPLORATION (outer=42 lineage, 3 seeds). BCH and TRX are bit-identical to /077 (0 IS wf differences, 0 OOS wf differences). ADA is the new active slot. IS concentration by IS total wpnl (75.24): BCH 78.34/104.1%, ADA 21.85/29.0%, TRX -24.95/-33.2% (TRX negative concentration is a wpnl sign artifact — TRX IS is drag but OOS profitable). OOS concentration: TRX 91.4% (OOS-dominant), BCH 7.1%, ADA 1.6%. The 30% per-symbol cap is a CONFIRMATION gate; informational at EXPLORATION.

---

## Label Leakage Audit

- `REQUIRED_GAP = 66 = (21+1) × 3 symbols` — confirmed unchanged.
- Embargo = 22 candles — unchanged.
- `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}` confirmed: all symbols (including ADAUSDT) use `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`.
- No feature was added or removed; the universe swap does not affect the feature pipeline or labeling logic.
- Walk-forward lookahead-bias note (`feedback_v3_walkforward_lookahead_bug.md`) applies equally to /078 — all v3 iterations carry the same embargo; IS/OOS deltas vs /077/060 are valid; absolute magnitudes uniformly biased upward.

---

## Gate Efficacy Table

All gates unchanged from the /060 baseline — only the universe symbol changed; no gate was modified.

| Primitive | State | IS fire rate (BCH/TRX) | IS fire rate (ADA) | OOS fire rate note |
|---|---|---|---|---|
| 1 — Feature OOD z>2.0 | ON | same as /060 anchor (bit-identical) | freshly evaluated | same as /060 for BCH/TRX |
| 2 — Hurst regime | ON | same as /060 anchor | freshly evaluated | same as /060 for BCH/TRX |
| 3 — ADX gate | ON | same as /060 anchor | freshly evaluated | same as /060 for BCH/TRX |
| 4 — Low-vol filter | ON | same as /060 anchor | freshly evaluated | same as /060 for BCH/TRX |
| 5 — Vol-adjusted sizing | ON | same as /060 anchor | freshly evaluated | same as /060 for BCH/TRX |
| 9 — Regime kill switch | OFF (CLOSED axis) | 0 | 0 | — |
| 10 — Direction kill switch | OFF (reverted /051) | 0 | 0 | — |
| 11 — Per-symbol drawdown brake | OFF (CLOSED /054) | 0 | 0 | — |
| 12 — BTC-trend-regime SIZE de-rate | OFF (reverted /076) | 0 | 0 | — |

TRX `vol_scale_floor=0.5` (from /061) is active and unchanged. ADAUSDT uses the global floor (no per-symbol entry in the dict, same as LDO before it).

---

## Anomaly Notes

1. **Spot-check 10 random OOS trades — 0 issues.** Entry/exit/PnL math checks pass for all 10 (verified: `weighted_pnl = net_pnl_pct × weight_factor` within float tolerance ≤ 0.0001). Exit reasons (take_profit, stop_loss, timeout, end_of_data) are self-consistent. Weight_factor values are non-negative. No anomalies detected.

2. **No NaN Sharpe, no zero-trade IS months, no NaN PnL.** IS monthly_pnl.csv: 36 rows, all with positive trade_count and numeric pnl_pct. OOS monthly_pnl.csv: 14 rows, all clean. IS monthly Sharpe recomputed from monthly_pnl.csv: 0.8201 (matches comparison.csv). OOS: 0.6892 (matches).

3. **BCH and TRX bit-identity confirmed field-by-field.** 73+75 IS and 37+54 OOS trades for BCH and TRX — all (symbol, open_time) keys identical, all weight_factor values identical (0 differences at 1e-8 tolerance). The single-axis swap did not perturb the non-target symbols at any level.

4. **ADA IS timeout trades — 5 of 74.** Five ADA IS trades exited at timeout (21.0 candles average). LDO IS had 0 timeout trades. This drives the added-vs-removed production duration gap from the T8-predicted +0.38 to the observed +2.23 candles, firing the Section 4.4 added-vs-removed falsifier. The 5 ADA timeout trades are collectively positive (total wpnl +9.88), so they are not IS drag — but they inflate ADA's mean holding time and trigger the sub-channel falsifier.

5. **IS Sharpe flat despite +45% IS wpnl lift.** IS mean monthly PnL +33% (1.57→2.09) but IS monthly std +34% (6.59→8.83). The variance increase matched the mean lift in proportion, leaving Sharpe at -0.0035 vs anchor. This is the mechanistic reason the Section 4.2 primary falsifier fired.

6. **PBO slightly tighter at 0.1277** (anchor 0.1278 — negligible delta). `frac_positive_paths` improved to 0.733 vs anchor 0.644 (+0.089), consistent with the OOS lift but informational at EXPLORATION mode.

---

## Status

OVERALL = READY-FOR-CRITIC

**Classification: SUSPICIOUS-OOS-DOMINANT — NO-MERGE. LDOUSDT retained.**

Brief Section 8.4 SUSPICIOUS-OOS-DOMINANT sub-mode fires: IS shift -0.0035 (< 0: TRUE) AND OOS shift +0.4814 (≥ +0.20: TRUE). The OOS/IS ratio gate did NOT fire (0.8404 < 3.0) — the sub-mode is the independent firing trigger. SUSPICIOUS takes disjunctive precedence over all other outcomes.

The brief Section 4.2 primary falsifier also fires independently: IS Δ = -0.0035 < +0.10. The T7 IS-edge screen prediction (ADA +0.617 IS Sharpe clears LDO -0.550 by +1.17) did NOT transfer to the production 3-seed walk-forward aggregate. ADA traded actively (74 IS trades, positive IS wpnl +21.85), but its per-month IS variance contribution matched its mean lift, leaving the aggregate IS monthly Sharpe flat. The screen's coarse single-seed proxy captured ADA's per-symbol IS edge; the portfolio aggregate Sharpe is dominated by BCH (76.9% of IS wpnl) and absorbs ADA's contribution primarily as added variance.

The Section 4.4 added-vs-removed holding-time falsifier also fired: actual production ADA-vs-LDO duration gap +2.23 candles (T8 label-implied prediction +0.38), exceeding the +1.0 candle threshold. Driven by 5 ADA IS timeout trades averaging 21.0 candles. This doubly reinforces SUSPICIOUS: the OOS lift is (a) uncorroborated by IS Sharpe and (b) carries a non-zero holding-time-loading channel that the T8 screen did not predict.

Distinction from prior SUSPICIOUS-OOS-DOMINANT cases (/071 IS -0.55, /073 IS -0.79, /076 IS -0.55): /078's IS shift is mild-negative (-0.0035, flat), not a collapse. Ratio is healthy (0.84, not 4-15×). The mechanism is "predicted IS lift failed to materialize" (ADA variance-matched its mean lift), not "IS actively destroyed by a regime-correlated gate." This nuance does not change the verdict — the sub-mode criteria are binary — but it informs the diary: the universe-revision axis is not categorically broken; the specific failure is that the T7 IS-edge screen's per-symbol Sharpe proxy does not predict portfolio aggregate Sharpe lift when BCH dominates.

BCH and TRX sub-rosters: BIT-IDENTICAL to /077 (0 IS added/removed, 0 OOS added/removed, 0 weight_factor differences). No wiring defect. The conditional_orthogonality.csv is emitted (14 rows, HYBRID PART A+B). No run.log warnings.

---

Phase 6 complete. Engineering report committed. Phase 7.5 Critic review required before Phase 7. Orchestrator: invoke `quant-critic` with branch=`iteration-v3/047`, report_dir=`reports-v3/iteration_v3-078`, brief_dir=`briefs-v3/iteration_v3-078`.
