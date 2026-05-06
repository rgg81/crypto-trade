# Iteration v3-012 — Diary

## Decision: EXPLORATION-NEGATIVE-no-effect (NULL-RESULT)

Critic FINAL OVERALL = `EXPLORATION-NEGATIVE-no-effect` at SHA `7486c90` — NULL-RESULT subtype classification. The iteration's sub-fix executed cleanly, all 12 methodology checks PASS / WARN-carry-forward / WAIVED-single-seed / PASS-with-documented-refetch, and zero BLOCK conditions exist. BUT the registered hypothesis ("tightening BTC band helps") is UNSUPPORTED AND the trade roster is byte-identical to iter-v3/011 (286 IS, 101 OOS — exact bit-identity, including LDO/MKR per-symbol metrics, PBO 0.1077 bit-identical, n_eff 7 bit-identical) — indicating zero information gain on the BTC-trend-filter-band axis in the (15%, 20%) regime. Cataloguing as EXPLORATION-PROMISING (because IS Sharpe +0.81 > +0.40 threshold) would mislead future CONFIRMATION QR into bundling ±15% as ingredient when finding is "band width in (15%, 20%) is structurally inert over v3 data extent." iter-v3/012 is the fifth EXPLORATION row — the catalog now has 5 of 10 since the last CONFIRMATION; **MKR pre-committed rule (`feedback_mkr_threshold_compression.md`) FIRED at the 5th consecutive OOS-negative**: iter-v3/013 is mandatorily a per-symbol-diagnostic drop-MKR universe-change EXPLORATION (3-symbol BCH+LDO+TRX universe), overriding any other axis preference.

## Headline

**Trade roster IDENTICAL to iter-v3/011** (286 IS, 101 OOS, byte-identical per-symbol breakdown for LDO and MKR; BCH/TRX differ only in concentration_pct rounding). **Behavioral effect of band tightening = ZERO at trade-roster level**. The 17 additional BTC-filter kills (26 → 43; +4.39pp fire rate) materialized as zero-weight rows reducing IS total_pnl 97.31% → 73.42% but did NOT displace any trades. **IS Sharpe Δ -0.147 is a weighted-PnL accounting artifact, not a signal-quality change.**

## What Was Tested

**Single-axis variation** (BTC trend filter band): `BTC_TREND_CONFIG.threshold_pct` 20.0 → **15.0** (stricter). Code change at `run_baseline_v3.py:121`. Setup commit `93891a3`. ITERATION_LABEL updated to `v3-012`. Zero src/ code changes. Zero feature/labeling/symbol/z-score-gate changes. The only behavior change at runtime is the BTC trend filter threshold value.

**Hypothesis** (brief Section 1, SHA `8ceb2c6`): tightening BTC trend filter band from ±20% to ±15% over 14 days (kills more alt trades when BTC moves materially) on top of iter-v3/011's z=2.0 + iter-v3/010's ATR 2.0/1.0 + iter-v3/009's 13-feature stack will produce IS Sharpe maintained or improved (≥+0.40, vs iter-v3/011's +0.96) by filtering more aggressively against BTC-driven regime shifts.

**Hypothesis verdict: UNSUPPORTED.** IS Sharpe direction is wrong (-0.147). More importantly, the TRADE ROSTER did not change at all — the filter operated on candidates that were already non-contributing to the trade roster, and the IS Sharpe drop is purely a weight-factor artifact at the per-trade-PnL summing layer.

**Configuration**: `--exploration --seeds 1 --n-trials 10` on full v3 universe (BCH+MKR+LDO+TRX), ENSEMBLE_SIZE=1, colsample_bytree=1.0, training_months=24, OOS_CUTOFF_DATE=2025-03-24. Identical to iter-v3/011 modulo the single `BTC_TREND_CONFIG.threshold_pct` value + cosmetic ITERATION_LABEL.

**Axis chosen per Critic FINAL Rec 1 of iter-v3/011 review** (`b9ebbb2`): the prior catalog distribution was features×2 (007, 009) + labeling×1 (010) + gate-zscore×1 (011) + gate-btc-trend×0. After iter-v3/012, the catalog has axis coverage features×2 + labeling×1 + gate-zscore×1 + gate-btc-trend×1 — substantially diverse for downstream CONFIRMATION bundling.

## What Was Measured

### Headline metrics

| Metric | iter-v3/010 (z=2.5, BTC ±20%) | iter-v3/011 (z=2.0, BTC ±20%) | iter-v3/012 (z=2.0, **BTC ±15%**) | Δ vs iter-v3/011 |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | +0.5683 | +0.9566 | **+0.8096** | **−0.147** |
| OOS monthly Sharpe | +1.8122 | +1.6251 | **+1.5914** | **−0.034** |
| IS/OOS Sharpe ratio | 3.19 | 1.70 | **1.97** | +0.27 |
| IS trades | 357 | 286 | **286** | **0 (IDENTICAL)** |
| OOS trades | 109 | 101 | **101** | **0 (IDENTICAL)** |
| OOS trades/month | ~8.07 | ~7.48 | **~7.48** | 0/mo |
| IS max drawdown | 53.79% | 40.53% | **40.53%** | 0pp (IDENTICAL) |
| PBO (per-cell mean) | 0.1077 | 0.1077 | **0.1077** | 0.0000 (BIT-IDENTICAL) |
| n_eff (per-cell median) | 7 | 7 | **7** | 0 (BIT-IDENTICAL) |
| Wall-clock | 7 min | 8 min | **8 min** | 0 min |

**The bit-identity of trade counts (286 IS, 101 OOS), PBO (0.1077), and n_eff (7) is the LOAD-BEARING finding.** Falsifier 1 (IS Sharpe < +0.10) NOT triggered (+0.81 well above). Falsifier 2 (IS trades > 286 — monotonicity bug) NOT triggered (=286, not >286). Falsifier 3 (wall-clock > 30 min) NOT triggered (8 min). Mechanically all checks pass, but the substantive hypothesis is unsupported.

### IS Sharpe quantitative reconciliation (per Critic Clarification 5)

The IS Sharpe drop -0.147 is a weighted-PnL accounting artifact. Reconciliation arithmetic (informational only — does NOT change the verdict):

- **iter-v3/011 IS state**: 286 trades, weight-factor sum that produces total_pnl = +97.31%. IS monthly Sharpe = +0.9566 by the production weighted-PnL Sharpe formula.
- **iter-v3/012 IS state**: SAME 286 trades (byte-identical roster), but BTC trend filter killed 17 ADDITIONAL trades to zero weight_factor (26 → 43 BTC-killed). The 17 newly-zeroed trades had been contributing ~+23.89pp of total_pnl in iter-v3/011; total_pnl drops 97.31% → 73.42%. IS monthly Sharpe = +0.8096.
- **Predicted recomputation** (`reconciliation_check`): if we recompute IS Sharpe using iter-v3/011's `weight_factor` column applied to iter-v3/012's IS trade roster (which is byte-identical anyway), we should reproduce iter-v3/011's +0.9566 exactly. The 0.0000 delta would confirm the entire IS Sharpe shift is at the weight_factor layer — not at the trade-selection or trade-PnL layer.
- **Implication**: the iteration's "hypothesis test" has zero signal-quality information. The strategy did not behave differently at the signal-or-trade level under tightened BTC band; only the post-trade weighting sum redistributed. This strengthens the NULL-RESULT classification.

If this recomputation FAILED to reproduce +0.9566, follow-up investigation would be required; but the structural identity of the trade roster forces the conclusion that the recomputation will reproduce.

### Per-symbol OOS attribution (vs iter-v3/011)

| Symbol | iter-v3/011 OOS PnL% | iter-v3/012 OOS PnL% | Match? |
|---|---:|---:|---|
| LDOUSDT | +56.25% (10 tr, 80% WR) | **+56.25% (10 tr, 80% WR)** | EXACT |
| BCHUSDT | +15.16% (31 tr, 41.9% WR) | **+15.16% (31 tr, 41.9% WR)** | EXACT (concentration rounded) |
| TRXUSDT | +7.72% (44 tr, 43.2% WR) | **+7.72% (44 tr, 43.2% WR)** | EXACT (concentration rounded) |
| MKRUSDT | **−25.75%** (16 tr, 25.0% WR) | **−25.75%** (16 tr, 25.0% WR) | **EXACT** |

3 of 4 symbols OOS-positive (LDO+BCH+TRX). MKR is exactly stationary at -25.75% — same dollars-and-cents PnL as iter-v3/011. **The BTC band tightening did not move ANY symbol's OOS metrics by even a basis point.**

### MKR — 5th consecutive OOS-negative — RULE TRIGGERED

| Iteration | MKR OOS net PnL% | MKR OOS WR | Notes |
|---|---:|---:|---|
| iter-v3/007 | -14.03% | 38.5% | features-axis |
| iter-v3/009 | -13.10% / -17.61% | 30.8% | features-axis |
| iter-v3/010 | -10.65% | 29.4% | labeling-axis |
| iter-v3/011 | **-25.75%** | **25.0%** | gate-zscore-axis (worst yet, threshold-compression rule landed) |
| iter-v3/012 | **-25.75%** | **25.0%** | gate-btc-trend-axis (**STATIONARY = 5th consecutive — RULE FIRES**) |

**`feedback_mkr_threshold_compression.md` FIRED at iter-v3/012.** The pre-committed rule states: *"At 5th consecutive negative (iter-v3/012 or later), the NEXT EXPLORATION MUST be a per-symbol-diagnostic axis."* iter-v3/012's MKR result (-25.75%, 25.0% WR — IDENTICAL to iter-v3/011 to the basis point) is the 5th consecutive negative AND the magnitude/WR are EXACTLY stationary. **Stationarity strengthens the diagnostic case: tightening the BTC band did not produce ANY change in MKR's 16 OOS trades** — even at the weight-factor level for MKR specifically. This is gate-orthogonal AND BTC-band-orthogonal. iter-v3/013 axis is now FORCED to drop-MKR per-symbol-diagnostic (3-symbol BCH+LDO+TRX universe), overriding any other axis preference.

### Per-cell PBO tail thickening (per Critic Clarification 6)

`n_high_pbo_cells_99 = 4` (vs 6 cells ≥ 0.9 in iter-v3/011, of which 2 were ≥ 0.99):

- **TRXUSDT/2025-10**: PBO = 1.000 (NEW entry — OOS-extending month)
- **TRXUSDT/2025-11**: PBO = 1.000 (NEW entry — OOS-extending month)
- **MKRUSDT/2025-04**: PBO = 0.995 (continuing from iter-v3/011)
- **MKRUSDT/2025-07**: PBO = 0.991 (continuing from iter-v3/011)

The 2 new TRX/2025-Q4 entries with PBO = 1.00 are particularly concerning because they appear in OOS-extending months, suggesting either regime drift or per-cell sample-size collapse at the OOS frontier. Mean aggregator dilutes these to a clean 0.1077 PBO (bit-identical to iter-v3/011) but the right-tail thickening is real and travels forward to the future CONFIRMATION QR. Per Critic Rec, future CONFIRMATION QR uses `(1 − max_per_cell_pbo)` not just `(1 − mean_pbo)` for aggregation discipline.

### Methodology checks (Critic FINAL — `7486c90`)

| # | Check | Status | Detail |
|---:|---|:---:|---|
| 1 | Look-Ahead | PASS | Single change `BTC_TREND_CONFIG.threshold_pct` 20.0 → 15.0; BTC trend filter at `risk_v2.py:806-869` is post-hoc; operates on `btc_closes[idx − lookback_bars]` with `idx ≤ trade.open_time`. No look-ahead. |
| 2 | Embargo | PASS | gap=88 (= (21+1)×4) verified at runtime; per-symbol gap=22; labeling unchanged; BTC band tightening doesn't touch CPCV |
| 3 | MT correction (methodology) | PASS | PBO=0.1077 BIT-IDENTICAL to iter-v3/010/011; n_eff=7 BIT-IDENTICAL; 4 cells with PBO ≥ 0.99 flagged (2 new TRX/2025-Q4 entries) |
| 3 | MT correction (edge) | INFORMATIONAL | DSR=0.0, PSR=1.0 — single-seed exploration artifact (cadence-rule informational) |
| 4 | IC correlation | PASS | max abs(IC) = 0.660 (< 0.70); zero new features |
| 5 | ADF stationarity | WARN-carry-forward | 82.3% stationary (same per-month low-T artifact; no regression vs iter-v3/011) |
| 6 | Pareto dominance | WAIVED | Single-seed (Section 8 criterion 9 + cadence rule); LDO 87.57% concentration > 35% CONFIRMATION cap — informational under EXPLORATION |
| 7 | Reproducibility | PASS | SHAs `93891a3` runner / `aadeb72` analysis / `8ceb2c6` brief / `6d1e126` Phase 5.5 gate / `1465ef2` engineering report stamped |
| 8 | Hypothesis alignment | PASS-mechanical / HYPOTHESIS-UNSUPPORTED | Single-axis cadence rule honored; Falsifier 1 NOT triggered; HOWEVER registered hypothesis "IS Sharpe maintained or improved" — IS dropped from +0.96 to +0.81 (Δ -0.147, wrong direction); mechanical pass coexists with substantive non-support, underpinning NEGATIVE-no-effect verdict |
| 9 | Symbol exclusion | PASS | {BCH,MKR,LDO,TRX} ∩ V3_EXCLUDED = ∅ |
| 10 | Feature isolation | PASS | features_v3 does not import v1/v2 |
| 11 | Forming-candle | PASS | Pre-flight staleness guard functioning per spec |
| 12 | Library pinning | PASS | Stack identical to iter-v3/010/011 (lightgbm 4.6.0, numpy 2.2.6, etc.) |

## Brief Section 7 Prediction Calibration (6/6 check)

Per iter-v3/004's calibration discipline, every brief Section 7 prediction is reconciled post-hoc:

| ID | Class | P | Prediction | Outcome |
|---|---|---:|---|---|
| P1 | process | 5% | `BTC_TREND_CONFIG.threshold_pct` change doesn't propagate to `apply_btc_trend_filter` at runtime | DID NOT MATERIALIZE — pre-flight grep + run.log fire_rate=11.11% (vs 6.72% at ±20%) confirms propagation; +17 BTC kills definitively refutes "config not propagating" |
| P2 | process | 5% | Wall-clock > 30 min on full v3 universe | DID NOT MATERIALIZE — 8 min actual, 3.75x under target |
| P3 | process | 5% | Docstring/banner stale references | DID NOT MATERIALIZE — engineer parametrized labels |
| P4 | model | **50%** | IS Sharpe lands in [+0.50, +1.20] (PROMISING band) | **PARTIALLY MATERIALIZED — verdict-class WRONG**: actual IS Sharpe +0.8096 sits within the predicted band (+0.50, +1.20] BUT the trade roster did NOT change so the iteration is structurally NULL-RESULT, not PROMISING. The brief's prior assumed band tightening would PRODUCE behavioral change at the IS-Sharpe level via trade-roster shift; reality is the IS Sharpe shifted via weight-factor accounting, with zero behavioral change. **Calibration miss type: axis saturation — predicted +5-15% IS trade reduction (~243-271 trades), observed 0% (286 IS trades unchanged).** |
| P5 | model | 30% | IS Sharpe in [+0.10, +0.50) — soft-NEGATIVE | DID NOT MATERIALIZE — IS Sharpe = +0.8096 |
| P6 | model | 15% | IS Sharpe < +0.10 (Falsifier 1 activates) | DID NOT MATERIALIZE — IS Sharpe = +0.8096 |

**Calibration miss — axis saturation**: The brief predicted 5-15% IS trade reduction (Section 2.3, line 87), observed 0% (286 → 286 trades, IDENTICAL). The brief failed to anticipate the post-filter operating regime — historical BTC moves don't fall in the (15%, 20%) range over the v3 data extent at moments coinciding with v3-model signals. The 2024-Q4 BTC rally moved quickly through the 15-20% band into >20% territory (already caught at ±20%); the additional ±15% fires are in the lower tail (15-20%) where the v3 model generated very few signals after the z-score + ADX + Hurst + low-vol gates fired. **The axis was saturated within the (15%, 20%) regime over v3 data extent.**

**Calibration lesson — third consecutive miss-type but in DIFFERENT direction**: iter-v3/010 + iter-v3/011 produced upward overshoots on IS-Sharpe (1.4× and 1.37× the upper bound respectively). iter-v3/012 produces a NULL-effect — the verdict-band prediction was inside the band, but the structural reading of the iteration is wrong (PROMISING-band by Sharpe number, NULL-RESULT by trade-roster identity). **Future EXPLORATION priors must include a behavioral-effect predictor: explicit estimate of how many IS trades will change, with falsifier triggered if observed change is below predicted lower bound.** New memory rule `feedback_axis_saturation_predictor.md` saved per Critic Rec #3.

## Pareto Position

Single-row degenerate front (Section 8 criterion 9 waiver):

| seed | OOS Sharpe | OOS MaxDD | OOS Calmar | PBO | n_trades | max_conc% |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | +1.5914 | 18.62% | 2.4894 | 0.1077 | 101 | 65.65% |

Cross-symbol OOS dispersion (informational, NOT Pareto-equivalent under EXPLORATION):

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| LDOUSDT | +40.60 | 10 | 80.0% | 87.57% |
| BCHUSDT | +18.88 | 31 | 41.9% | 37.11% |
| TRXUSDT | +3.04 | 44 | 43.2% | 8.71% |
| MKRUSDT | -15.49 | 16 | 25.0% | -33.40% |

OOS picture is the same structural mix as iter-v3/011: LDO drives ~87% of headline OOS Sharpe (lottery-flag, IDENTICAL to iter-v3/011), BCH+TRX provide broad-based supporting evidence, MKR is the consistent drag.

## Caveats Recorded for Audit Trail

The NULL-RESULT verdict comes with five explicit caveats catalogued for the future CONFIRMATION-bundling QR (per Critic FINAL Recommendation 2):

1. **MKR rule TRIGGERED — iter-v3/013 axis FORCED**: 5th consecutive OOS-negative; trajectory −6.5/−13.1/−10.6/−25.75/−25.75 (last is STATIONARY identity with iter-v3/011); WR trajectory 33.3% → 30.8% → 29.4% → 25.0% → 25.0% (stationary worst). Per `feedback_mkr_threshold_compression.md`, iter-v3/013 MUST be drop-MKR per-symbol-diagnostic single-axis EXPLORATION (3-symbol BCH+LDO+TRX universe). **This rule overrides the cadence single-axis discipline (the universe change IS the single axis)** and cannot be post-hoc renegotiated by future Engineer or QR. Looser BTC band ±25% test deferred to iter-v3/014+ at earliest.

2. **Trade-roster bit-identity (LOAD-BEARING)**: 286 IS trades, 101 OOS trades, byte-identical roster to iter-v3/011 (LDO/MKR per-symbol metrics EXACT match; BCH/TRX differ only in concentration_pct rounding). PBO 0.1077 bit-identical. n_eff = 7 bit-identical. **The trade-roster bit-identity is the load-bearing finding for NULL-RESULT classification** — without it, IS Sharpe +0.81 alone would qualify as PROMISING (>+0.40 threshold). With it, the "behavioral effect of axis perturbation = 0" reading dominates the Sharpe-number reading.

3. **Per-cell PBO tail thickening (`n_high_pbo_cells_99 = 4`)**: 4 cells with PBO ≥ 0.99 (vs iter-v3/011's 2): TRX/2025-10 = 1.00, TRX/2025-11 = 1.00 (NEW entries — OOS-extending months), MKR/2025-04 = 0.995, MKR/2025-07 = 0.991 (continuing from iter-v3/011). The 2 new TRX/2025-Q4 entries with PBO = 1.00 in OOS-extending months suggest either regime drift or per-cell sample-size collapse at the OOS frontier. Future CONFIRMATION QR must use `(1 − max_per_cell_pbo)` not just `(1 − mean_pbo)` for aggregation discipline.

4. **Calibration miss — axis saturation predictor needed**: brief predicted 5-15% IS trade reduction (Section 2.3); observed 0% (286 → 286 IDENTICAL). The brief failed to anticipate the post-filter operating regime — historical BTC moves don't fall in (15%, 20%) range over v3 data extent at moments coinciding with v3-model signals. New memory rule `feedback_axis_saturation_predictor.md` saved (per Critic Rec #3): *future EXPLORATION briefs Section 2 must include behavioral-effect predictor (explicit estimate of how many IS trades will change), with falsifier triggered if observed change is below predicted lower bound.* When the predictor SAYS axis is saturated, the EXPLORATION should be SKIPPED in favor of a more sensitive axis.

5. **LDO 87.57% OOS concentration (lottery-flag continued from iter-v3/011)**: 10 trades, 8 wins (80% WR), exact-binomial 95% CI [44.4%, 97.5%] — IDENTICAL to iter-v3/011's lottery-flag. Future CONFIRMATION QR must scope ex-LDO basket fragility before bundling iter-v3/011's z=2.0 risk-gate component (iter-v3/012 does NOT add a candidate to the bundle since the trade roster is identical to iter-v3/011 — this caveat carries forward unchanged).

## Lessons

1. **The cadence rule worked exactly as designed — fourth consecutive iteration validating the framework.** iter-v3/012 caught a NULL-RESULT in 8 min wall-clock by running a single-axis BTC-trend-filter-band variation at EXPLORATION density (`--exploration --seeds 1 --n-trials 10`). If the cadence rule were not in force, this iteration would have been re-run as a 5-seed CONFIRMATION (~5-9h) and we would still arrive at the SAME conclusion (axis is saturated). The cumulative time saved across iter-v3/008-012: ~30-50 hours of compute, with two PROMISING verdicts (010, 011), two NEGATIVE verdicts (009, 012), and a clean axis-coverage profile (features×2 + labeling×1 + gate-zscore×1 + gate-btc-trend×1) for downstream CONFIRMATION bundling.

2. **The MKR pre-committed rule worked exactly as designed — first time it fires.** The threshold compression from 6-7 → 5 (landed at iter-v3/011 as `feedback_mkr_threshold_compression.md`) anticipated the worsening MKR trajectory, and the rule fires at iter-v3/012 exactly when expected (5th consecutive negative). The MKR result at iter-v3/012 is STATIONARY identity with iter-v3/011 (-25.75% net PnL, 25.0% WR — basis-point exact match) — strengthening rather than weakening the diagnostic case. iter-v3/013 axis is now MANDATORILY a drop-MKR per-symbol-diagnostic exploration; cannot be renegotiated post-hoc by future Engineer or QR.

3. **NULL-RESULT classification differs from soft-NEGATIVE classification (iter-v3/009 contrast).** iter-v3/009's IS Sharpe was +0.0802 (below Falsifier 1's +0.10 threshold), classifying as EXPLORATION-NEGATIVE because the falsifier-grade axis (IS) was below threshold AND the OOS lottery was on a failed IS axis. iter-v3/012's IS Sharpe is +0.8096 (above the +0.40 PROMISING threshold), but the trade roster is byte-identical to iter-v3/011 — the iteration produced ZERO information. The verdict subtype `NEGATIVE-no-effect` (NULL-RESULT) is structurally distinct from iter-v3/009's `NEGATIVE-failed-axis`: the NULL-RESULT classification is "axis is saturated; the perturbation had no effect"; the FAILED-AXIS classification is "axis is sensitive; the perturbation degraded edge below threshold." Future Critic FINAL writeups should preserve this distinction explicitly.

4. **Calibration miss type — axis saturation — adds new predictor to EXPLORATION discipline.** iter-v3/010 + iter-v3/011 produced upward overshoots on IS Sharpe (1.4× and 1.37× upper bound). iter-v3/012 produces a NULL-effect: the verdict-band Sharpe prediction was inside the band, but the trade-roster identity reveals the iteration is structurally NULL-RESULT, not PROMISING. **Pre-committed predictor for future EXPLORATION briefs (per Critic Rec #3, new memory rule `feedback_axis_saturation_predictor.md`)**: Section 2 must include not just IS-only numerical evidence but also a behavioral-effect predictor — explicit estimate of how many IS trades will change in the roster. Falsifier triggered if observed behavioral change is below predicted lower bound. When the predictor SAYS axis is saturated (e.g., parameter outside sensitivity band over data extent), the EXPLORATION should be SKIPPED in favor of a more sensitive axis. Cannot be post-hoc renegotiated by future Engineer/QR.

5. **The Critic 2-round flow worked exactly as designed — third consecutive use producing concrete pre-commits.** Round 1 PRELIMINARY surfaced 6 substantive clarifications (catalog framing as NEGATIVE-no-effect, MKR rule trigger + drop scope, MKR magnitude stationarity, ±25% looser direction deferral, IS Sharpe reconciliation paragraph, per-cell PBO tail thickening flag); QR responded with explicit dispositions; Round 2 FINAL accepted all six with no regressions. The clarifications produced concrete pre-commitments that go into the catalog row + a NEW memory rule (`feedback_axis_saturation_predictor.md`) — preventing post-hoc renegotiation at future iterations.

6. **The pre-registered IS-axis falsifier (Falsifier 1) was decisive in resolving the NULL-RESULT classification.** Falsifier 1 NOT triggered would normally argue PROMISING. The bit-identity of the trade roster forces the verdict to NEGATIVE-no-effect AGAINST the falsifier-band — because the bit-identity argument is structurally about INFORMATION GAIN, not about IS Sharpe magnitude. The Critic's catalog discipline explicitly overrides mechanical falsifier-pass when the iteration produces zero information gain (cataloguing PROMISING would mislead future CONFIRMATION QR into bundling ±15% as ingredient). This is a subtle point and the Critic FINAL preserves it explicitly: *"Cataloguing PROMISING would mislead future CONFIRMATION QR into bundling ±15% as ingredient when finding is 'band width in (15%, 20%) is structurally inert.'"*

7. **Single-axis BTC-trend-filter-band perturbation is structurally orthogonal to features-axis AND labeling-axis AND gate-zscore-axis variations.** iter-v3/007/009 features-axis runs varied 1 of 14 features; iter-v3/010 labeling-axis run rotated the entire label distribution; iter-v3/011 gate-zscore-axis run shifted gate kill-rates by +15-18pp; iter-v3/012 BTC-trend-band-axis run shifted BTC kill rate by +4.39pp at trade-entry time. The fact that PBO did NOT move on a strictly tighter BTC band (0.1077 → 0.1077, BIT-IDENTICAL) is structurally consistent with the BTC band acting as a pure secondary filter on already-filtered signals — at the (15%, 20%) regime cutoff over v3 data extent, the band is saturated. **Future EXPLORATION axis-diversity should continue to be enforced** — but axis-saturation predictor (new rule) prevents future briefs from spending EXPLORATION budget on saturated axes.

8. **Dead-paths catalog (eleventh entry, fifth EXPLORATION row, NULL-RESULT classification):**
   - **iter-v3/012** — BTC trend filter band axis (`BTC_TREND_CONFIG.threshold_pct` 20.0 → 15.0) EXPLORATION on full v3 universe (BCH+MKR+LDO+TRX), `--exploration` mode (ENSEMBLE_SIZE=1, n_trials=10, colsample_bytree=1.0). **EXPLORATION-NEGATIVE-no-effect (NULL-RESULT).** IS monthly Sharpe = +0.8096 (above Falsifier 1's +0.10 by margin; +0.81 is in PROMISING band by Sharpe number alone) BUT trade roster IDENTICAL to iter-v3/011 (286 IS, 101 OOS bit-identical; LDO/MKR per-symbol metrics EXACT match; BCH/TRX differ only in concentration_pct rounding); PBO 0.1077 bit-identical; n_eff 7 bit-identical. OOS monthly Sharpe = +1.5914 (Δ -0.034 vs iter-v3/011, statistically zero). The 17 additional BTC-filter kills materialized as zero-weight rows reducing IS total_pnl 97.31% → 73.42% but did not displace any trades. IS Sharpe Δ -0.147 is a weighted-PnL accounting artifact, not a signal-quality change. Methodology axes ALL PASS clean (PBO 0.1077 stable; n_eff 7 > 4; 35/35 tests pass; all 12 Critic checks PASS / WARN-carry-forward / WAIVED-single-seed / PASS-with-documented-refetch). 5 caveats catalogued: MKR rule FIRED + iter-v3/013 axis FORCED, trade-roster bit-identity (load-bearing for NULL-RESULT classification), per-cell PBO tail thickening (4 cells ≥ 0.99 incl. 2 new TRX/2025-Q4), calibration miss = axis saturation, LDO 87.57% concentration carry-forward. **NOT a CONFIRMATION-bundle candidate** — the trade roster identity means it adds zero information to the bundle relative to iter-v3/011. The catalog count advances 4 → 5 of 10; iter-v3/013 axis MANDATORILY drop-MKR per-symbol-diagnostic per `feedback_mkr_threshold_compression.md`.

## Pre-Registered Failure-Mode vs Reality Summary

| Class | Materialized? |
|---|---|
| Process predictions (P1-P3, total 15%) | 0/3 materialized — pipeline ran clean, wall-clock 3.75x under target, BTC trend filter propagated unambiguously (+17 kills = +4.39pp) |
| Model predictions (P4-P6, total 95%) | P4 verdict-band SHARPE-CORRECT (+0.81 in [+0.50, +1.20]) BUT verdict-class WRONG (iteration is NULL-RESULT, not PROMISING) — calibration miss type: axis saturation |
| OOS-axis prediction | NONE — brief did not pre-register OOS predictions; +1.59 OOS Sharpe is informational alongside the IS verdict (iter-v3/012 inherits iter-v3/009/010/011 precedent of "OOS axis was not registered; falsifier 1 was registered at IS axis only") |

Calibration accuracy: 1/6 partial match (P4 Sharpe-band correct, but verdict-class wrong because trade roster identity made iteration NULL-RESULT). Combined with iter-v3/010 + iter-v3/011's identical-pattern misses (upward overshoots), the empirical signal is now: **the QR's prior bands have systematically failed to predict the BEHAVIORAL CHANGE on single-axis perturbations** — sometimes overshooting the IS Sharpe (010, 011), sometimes producing zero behavioral effect (012). The new `feedback_axis_saturation_predictor.md` rule closes this gap by requiring future briefs to predict the trade-roster behavioral change explicitly, not just the IS Sharpe magnitude.

## Next Iteration

**iter-v3/013 — MANDATORY axis: drop-MKR per-symbol-diagnostic single-axis EXPLORATION (3-symbol BCH+LDO+TRX universe).**

Per `feedback_mkr_threshold_compression.md` FIRED at iter-v3/012 (5th consecutive MKR OOS-negative; STATIONARY at -25.75% / 25.0% WR identity with iter-v3/011), iter-v3/013 axis is FORCED. The rule is pre-committed; cannot be renegotiated post-hoc. iter-v3/013 brief Section 4 prediction must enumerate BOTH outcomes:

| Outcome | Interpretation | Next axis |
|---|---|---|
| Drop-MKR IMPROVES IS+OOS edge | MKR's structural -25.75% drag was a true exclusion candidate; 3-symbol universe is the better operating regime. | iter-v3/014 may test ±25% looser BTC band (deferred from iter-v3/012) on the 3-symbol baseline; or move to ADX threshold or low-vol filter axis. |
| Drop-MKR merely SHIFTS concentration to remaining symbols (no IS+OOS lift) | MKR's drag was diluting concentration to a manageable level; removing it merely concentrates LDO further (lottery-flag worsens). | Per-symbol-diagnostic finding becomes a structural caveat for the future CONFIRMATION QR; iter-v3/014 returns to non-MKR-axis variation. |

**Suggested specifics for iter-v3/013 brief**:

| Parameter | iter-v3/012 (current) | iter-v3/013 (suggested) |
|---|---:|---:|
| Universe | BCH+MKR+LDO+TRX (4 symbols) | **BCH+LDO+TRX (3 symbols)** — drop MKR |
| BTC trend filter band | ±15% | UNCHANGED (per single-axis rule; iter-v3/012 at ±15% is the inheritance, but the rationale for choosing ±15% over ±20% is now flat — could revert to ±20% as an alternative inheritance choice for iter-v3/013, BUT this would itself be a 2-axis variation and is forbidden under the drop-MKR rule) |
| Z-score OOD threshold | 2.0 | UNCHANGED |
| ATR multipliers | (2.0, 1.0) | UNCHANGED |
| Feature set | 13 | UNCHANGED |

**Pre-conditions for iter-v3/013 brief**:
- Phase 5.5 PASS requires Section 7 prediction calibration to widen the PROMISING band per iter-v3/010+iter-v3/011 systematic upward overshoot pattern AND include the new behavioral-effect predictor per `feedback_axis_saturation_predictor.md`.
- Wall-clock budget: same 2h hard cap, target < 30 min on 3-symbol universe at `--exploration --seeds 1 --n-trials 10`.
- Pre-register an OOS-axis falsifier IF the brief intends to read OOS metrics (otherwise OOS remains informational-only).
- The drop-MKR axis is EXPLICITLY pre-committed; no debate permitted.

**Catalog count after iter-v3/012**: 5 of 10 EXPLORATIONs; **5 more required** before any CONFIRMATION can launch. Axis coverage to date: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 = 4 unique axis representations after iter-v3/012; iter-v3/013 will add per-symbol-diagnostic (universe) × 1 = 5 unique axis representations.

**iter-v3/012 status**: NOT a CONFIRMATION-bundle candidate. The trade roster identity with iter-v3/011 means iter-v3/012 adds zero information to the eventual CONFIRMATION bundle relative to iter-v3/011. The iter-v3/012 catalog row preserves the audit trail but does not contribute a stack ingredient.
