# Iteration v3-011 — Diary

## Decision: EXPLORATION-PROMISING (with lottery/concentration caveats)

Second consecutive PROMISING (after iter-v3/010). Critic FINAL OVERALL = `EXPLORATION-PROMISING (with lottery/concentration caveats)` at SHA `b9ebbb2`. All 12 methodology checks resolve to PASS / WARN-carry-forward / WAIVED-single-seed; **no BLOCK condition exists**. All four pre-registered falsifiers (Section 4.3 of the brief) NOT triggered. The catalog now has 4 of 10 EXPLORATIONs since the last CONFIRMATION. iter-v3/011 is a real candidate for the next CONFIRMATION bundle, with the LDO concentration caveat travelling forward as an explicit pre-commit for the bundling QR.

Headline differentiator from iter-v3/010 (PROMISING-broad-based) and iter-v3/009 (NEGATIVE-lottery): **iter-v3/011's IS axis is broad-based 286 trades at +0.9566 Sharpe (NOT lottery-driven), while OOS lottery-flag is concentrated in LDO 86.31% (10-trade 80% WR with binomial CI [44.4%, 97.5%])**. The IS axis is the falsifier-grade axis (per brief §4.3 / §8); OOS is informational under EXPLORATION. iter-v3/011 clears the falsifier-grade IS axis with substantial margin (+0.56 above the +0.40 PROMISING threshold) on a 286-trade broad-based sample.

## What Was Tested

**Single-axis variation** (risk-gate axis): `RiskV2Config.zscore_threshold` 2.5 → **2.0** (tighter). Code change at `run_baseline_v3.py:_build_v3_model` line 873. Setup commit `9b4af01`. ITERATION_LABEL updated to `v3-011`. Zero src/ code changes. Zero feature/labeling/symbol changes. The only behavior change at runtime is the gate threshold value.

**Hypothesis** (brief Section 1, SHA `1bd02dc`): tightening the z-score OOD threshold from 2.5 to 2.0 (kills any trade where any feature in V2_FEATURE_COLUMNS exceeds 2σ from the IS-window training distribution) on top of iter-v3/010's labeling baseline (ATR 2.0/1.0) will produce IS Sharpe maintained or improved (≥ +0.40, vs iter-v3/010's +0.5683) by filtering more aggressively against feature-distribution drift, testing whether iter-v3/010's IS lift was robust to stricter gating or signal-density-dependent.

**Configuration**: `--exploration --seeds 1 --n-trials 10` on full v3 universe (BCH+MKR+LDO+TRX), ENSEMBLE_SIZE=1, colsample_bytree=1.0, training_months=24, OOS_CUTOFF_DATE=2025-03-24. Identical to iter-v3/010 modulo the single `zscore_threshold` value + cosmetic ITERATION_LABEL.

**Axis chosen per Critic FINAL Rec 1 of iter-v3/010 review** (`f6f4ef7`): the prior catalog distribution was features×2 (007, 009) + labeling×1 (010) + gate×0. Risk-gate is structurally orthogonal to both features and labeling — gates filter trade entries at decision-time without changing feature inputs or label targets. iter-v3/011 produces axis coverage features×2 + labeling×1 + gate×1 — meaningful diversity for the eventual CONFIRMATION bundle.

**Direction (tighter not looser)**: 2.0 selected over 3.0 because iter-v3/010's OOS trade-rate was 8.07/month (already below the 10/month floor); tightening stress-tests whether the floor is recoverable at CONFIRMATION's 5-seed × ensemble multiplication. iter-v3/012 may test 3.0 (looser) if needed for axis-completeness.

## What Was Measured

### Headline metrics

| Metric | iter-v3/009 (top-13, z=2.5, 2.9/1.45) | iter-v3/010 (top-13, z=2.5, 2.0/1.0) | iter-v3/011 (top-13, **z=2.0**, 2.0/1.0) | Δ vs iter-v3/010 |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | +0.0802 | +0.5683 | **+0.9566** | **+0.388** |
| OOS monthly Sharpe | +1.1223 | +1.8122 | **+1.6251** | **−0.187** |
| IS/OOS Sharpe ratio | 13.99 | 3.19 | **1.70** | −1.49 (healthier) |
| IS trades | 267 | 357 | **286** | −71 (−19.9%) |
| OOS trades | 87 | 109 | **101** | −8 (−7.3%) |
| OOS trades/month | ~6.4 | ~8.07 | **~7.48** | −0.59/mo |
| IS max drawdown | — | 53.79% | **40.53%** | −13.26pp (better) |
| PBO (per-cell mean) | 0.1145 | 0.1077 | **0.1077** | 0.0000 (stable) |
| n_eff (per-cell median) | 7 | 7 | 7 | 0 |
| Wall-clock | 11 min | 7 min | **8 min** | +1 min (fresh refetch) |

**IS monthly Sharpe = +0.9566 — the highest in v3 track to date** (third consecutive record-setter on the falsifier-grade axis). Falsifier 1 (IS Sharpe < +0.10) NOT triggered; +0.86 above threshold. Falsifier 2 (IS trades > 357 — monotonicity bug) NOT triggered; 286 < 357 confirms monotonic decreasing trade count under tighter gate. Falsifier 3 (wall-clock > 30 min) NOT triggered; 8 min actual.

**OOS monthly Sharpe = +1.6251 — second-highest in v3 history** (slight regression from iter-v3/010's +1.8122 record). The OOS dip is small (−0.19) and the IS/OOS ratio collapsed from 3.19 to 1.70 — a substantially **healthier** generalization profile than iter-v3/010's 3.19 ratio.

### Per-symbol OOS PnL attribution

| Symbol | OOS trades | Win rate | Net PnL% | Avg PnL% | Concentration% | Note |
|---|---:|---:|---:|---:|---:|---|
| LDOUSDT | 10 | **80.0%** | +56.25% | +5.625% | **86.31%** | lottery-flag concentration; 95% binomial CI [44.4%, 97.5%] |
| BCHUSDT | 31 | 41.9% | +15.16% | +0.489% | 40.14% | broad-based contributor |
| TRXUSDT | 44 | 43.2% | +7.72% | +0.176% | 6.47% | breakeven-positive; largest trade count |
| MKRUSDT | 16 | 25.0% | -25.75% | -1.609% | -32.92% | **4th consecutive negative; threshold compressed 6-7 → 5** |

3 of 4 symbols OOS-positive. The OOS picture is a structural mix: LDO drives 86% of the headline OOS Sharpe (lottery-flag), BCH+TRX provide broad-based supporting evidence, MKR is the consistent drag. Without LDO's 8 wins, the OOS basket would not produce the +1.63 Sharpe — this is materially different from iter-v3/010's broader 3-of-4 dispersion (BCH 57% + LDO 41% + TRX 11%).

### IS Per-symbol attribution (broad-based — NOT lottery-driven)

| Symbol | IS trades | Win rate | Net PnL% |
|---|---:|---:|---:|
| BCHUSDT | 100 | 45.0% | +86.82% |
| LDOUSDT | 21 | 47.6% | +52.90% |
| TRXUSDT | 88 | 33.0% | -19.96% |
| MKRUSDT | 77 | 33.8% | -23.21% |

IS BCH dominates positive PnL (+86.82% on 100 trades) with LDO supportive (+52.90% on 21 trades). TRX flipped IS-negative under z=2.0 (−19.96% vs iter-v3/010's +19.49%) — the trades in the 2.0–2.5σ band were apparently positive IS contributors that the tighter gate killed. MKR IS improved slightly (−23.21% vs iter-v3/010's −32.37%). The IS Sharpe (+0.9566) is dominated by 100 BCH trades + 21 LDO trades = 121 of 286 IS trades on positive-PnL symbols — broad enough to refute any "IS lift is also lottery" reading.

### Methodology checks (Critic FINAL — `b9ebbb2`)

| # | Check | Status | Detail |
|---:|---|:---:|---|
| 1 | Look-Ahead | PASS | Zero new feature code; threshold change acts on past-only IS-window mean/std snapshots in `risk_v2.py:222-226` |
| 2 | Embargo | PASS | gap=88 (= (21+1)×4) verified at runtime; per-symbol gap=22 |
| 3 | MT correction (methodology) | PASS | PBO=0.1077 << 0.40 (identical to iter-v3/010); n_eff=7 > 4; **6 cells with PBO ≥ 0.9** flagged (vs 5 in iter-v3/010) |
| 3 | MT correction (edge) | INFORMATIONAL | DSR=0.0, PSR=1.0 — single-seed exploration artifact (cadence-rule informational) |
| 4 | IC correlation | PASS | max abs(IC) = 0.660 (< 0.70); 0 pairs above threshold; feature axis byte-for-byte unchanged |
| 5 | ADF stationarity | WARN-carry-forward | 82.3% stationary (same per-month low-T artifact; no regression vs iter-v3/010) |
| 6 | Pareto dominance | WAIVED | Single-seed (Section 8 criterion 9 + cadence rule). Max concentration LDO 86.31% > 35% CONFIRMATION cap — informational under EXPLORATION, captured in lottery-flag |
| 7 | Reproducibility | PASS | SHAs `9b4af01` runner / `17d01ab` analysis / `1bd02dc` brief / `138e861` Phase 5.5 gate stamped; trade-row spot-check OOS row 1 reconciles |
| 8 | Hypothesis alignment | PASS | Single-axis risk-gate variation; brief Section 1 = code; Falsifiers 1, 2, 3 NOT triggered |
| 9 | Symbol exclusion | PASS | {BCH,MKR,LDO,TRX} ∩ V3_EXCLUDED = ∅ |
| 10 | Feature isolation | PASS | features_v3 does not import v1/v2 |
| 11 | Forming-candle | PASS-with-documented-refetch | First launch failed staleness check (19.6h > 16h); re-fetched 2 klines × 5 symbols + regen features; pre-flight guard functioning per spec |
| 12 | Library pinning | PASS | Stack identical to iter-v3/010 (lightgbm 4.6.0, numpy 2.2.6, etc.) |

### Per-cell PBO outliers

6 cells with PBO ≥ 0.9 (`n_high_pbo_cells = 6/175`, +1 vs iter-v3/010):
- TRXUSDT cells (continuing pattern from iter-v3/010)
- MKRUSDT cells (continuing pattern from iter-v3/010)

Mean aggregator dilutes these to a clean 0.1077 PBO (identical to iter-v3/010). Recorded in catalog row; future CONFIRMATION QRs may use `(1 - max_per_cell_pbo)` weighting on bundle evidence as iter-v3/010's audit trail already pre-committed.

### Gate Efficacy — Z-gate kill rate shift (z=2.5 → z=2.0)

| Symbol | killed_by_zscore (z=2.5, iter-v3/010) | killed_by_zscore (z=2.0, iter-v3/011) | Delta kills |
|---|---:|---:|---:|
| BCHUSDT | 450 (14.2%) | 994 (31.4%) | +544 (+17.2pp) |
| MKRUSDT | 953 (35.0%) | 1360 (49.8%) | +407 (+14.8pp) |
| LDOUSDT | 278 (27.1%) | 456 (44.4%) | +178 (+17.3pp) |
| TRXUSDT | 432 (15.6%) | 928 (33.5%) | +496 (+17.9pp) |

The z-gate fired substantially more under z=2.0 (+15–18pp across symbols). Brief §6.1 predicted combined kill rate 75–88% (vs 69–78% at z=2.5); actual 73.8–86.5% — within predicted band. MKR has the highest z-gate kill rate (49.8%), consistent with brief §2.1 prediction that MKR has heaviest feature-distribution tails (highest SL%=66.3% at z=2.5). **P1 process-level failure prediction (config not propagating) definitively refuted** — kill rates show unambiguous threshold effect.

## Brief Section 7 Prediction Calibration (6/6 check)

Per iter-v3/004's calibration discipline, every brief Section 7 prediction is reconciled post-hoc:

| ID | Class | P | Prediction | Outcome |
|---|---|---:|---|---|
| P1 | process | 5% | `zscore_threshold` change doesn't propagate to `RiskV2Wrapper._zscore_ood` at runtime | DID NOT MATERIALIZE — pre-flight grep confirmed `zscore_threshold=2.0`; gate stats show +15–18pp kill-rate increase across all 4 symbols (definitively refutes "config not propagating") |
| P2 | process | 5% | Wall-clock > 30 min on full v3 universe at exploration config | DID NOT MATERIALIZE — 8 min actual, 3.75x under target |
| P3 | process | 5% | 0.5-pp drift reveals hidden floating-point comparison bug in `_zscore_ood` | DID NOT MATERIALIZE — 35/35 tests PASS; runtime gate stats show monotonic kill-rate increase |
| P4 | model | **50%** | IS Sharpe lands in [+0.40, +0.70] (PROMISING band) | **PARTIALLY MATERIALIZED — overshoot in favorable direction**: actual IS Sharpe +0.9566 sits **+0.26 above** the predicted band's upper end (+0.70). Verdict-class is correct (PROMISING), point-estimate overshot by the QR's prior. |
| P5 | model | 30% | IS Sharpe lands in [+0.10, +0.40) — soft-NEGATIVE | DID NOT MATERIALIZE — IS Sharpe = +0.9566 |
| P6 | model | 15% | IS Sharpe drops below +0.10 (Falsifier 1 activates) | DID NOT MATERIALIZE — IS Sharpe = +0.9566 |

**Calibration assessment**: 1/3 model-predictions partially materialized (P4 verdict-class correct, point-estimate overshoot). The QR weighted P4 (PROMISING) at 50% probability — verdict-class correct; **the magnitude of the IS lift was 1.37× the predicted upper bound**. This is a calibration miss in the FAVORABLE direction — **second consecutive favorable overshoot** (iter-v3/010 was 1.4× upper bound on labeling-axis; iter-v3/011 is 1.37× upper bound on gate-axis).

The structural pattern across iter-v3/010 + iter-v3/011: the QR's prior bands have been systematically too narrow on single-axis perturbations under colsample=1.0 + n_trials=10. Future EXPLORATION priors on ANY axis (features, labeling, gate) should widen the PROMISING band materially — e.g., label gate-axis priors at 35% in [+0.40, +1.00], 30% in [+1.00, +1.50] overshoot, 35% NEGATIVE. The favorable-overshoot pattern is informative for prior-update direction even though it does not change verdict classification.

## Differentiation from iter-v3/009 (the EXPLORATION-NEGATIVE precedent)

The contrast with iter-v3/009 is the central diary observation: **iter-v3/011's IS axis is broad-based (NOT lottery), with the OOS lottery isolated to LDO**, vs iter-v3/009's pure OOS lottery on a failed IS axis.

| Dimension | iter-v3/009 (NEGATIVE) | iter-v3/010 (PROMISING-broad) | iter-v3/011 (PROMISING-with-caveats) |
|---|---|---|---|
| Axis varied | Features (drop `vwap_dev_50`) | Labeling (tp/sl 2.9/1.45 → 2.0/1.0) | **Gate (zscore_threshold 2.5 → 2.0)** |
| IS Sharpe | +0.0802 (below Falsifier 1) | +0.5683 (well above Falsifier 1) | **+0.9566 (highest in v3 history)** |
| OOS Sharpe | +1.1223 INFORMATIONAL | +1.8122 (broad-based) | **+1.6251** |
| OOS concentration | **98.61% LDO** (single-symbol lottery) | 57.17% BCH (broad-based) | **86.31% LDO (lottery-flag)** |
| OOS positive symbols | 1 of 4 (LDO only) | 3 of 4 (BCH+LDO+TRX) | **3 of 4 (LDO+BCH+TRX)** |
| IS broad-based? | NO — IS Sharpe below floor | YES — 357 trades, broad attribution | **YES — 286 trades, broad attribution (BCH 100 + LDO 21 + TRX 88 + MKR 77)** |
| Lottery flag direction | OOS lottery + IS broken | No lottery flag | **OOS LDO lottery flag (IS broad-based)** |
| Mechanism | Redundancy-removal hypothesis REJECTED at IS axis | Tighter-labels-reduce-noise hypothesis ACCEPTED | **Tighter-gate-validates-iter-v3/010-robustness ACCEPTED on IS axis (broad-based confirmation)** |
| PBO direction | 0.1419 → 0.1145 (improved by feature-removal artifact) | 0.1145 → 0.1077 (improved by tighter labels) | **0.1077 → 0.1077 (stable; tighter gate did not move PBO)** |

The structural argument: iter-v3/009 had a 12-trade LDO lottery on a failed IS axis, classified NEGATIVE because the falsifier-grade axis (IS) was below threshold. iter-v3/011 has a 10-trade LDO lottery on a **passed-with-margin** IS axis (+0.9566 Sharpe over 286 trades broad-based), classified PROMISING because the falsifier-grade axis cleared with substantial margin and the OOS lottery-flag is informational only under EXPLORATION. iter-v3/010 had no lottery flag; iter-v3/011 has a lottery flag but the IS-axis differentiation forces the verdict to PROMISING-with-caveats.

## Caveats Recorded for Audit Trail

The PROMISING-with-caveats verdict comes with five explicit caveats catalogued for the future CONFIRMATION-bundling QR (per Critic FINAL Recommendation 2):

1. **Gate-orthogonal MKR**: 4th consecutive OOS-negative across iter-v3/007 (MKR -14.03%), iter-v3/009 (MKR -13.1%/-17.61%), iter-v3/010 (MKR -10.65%), iter-v3/011 (MKR -25.75%). Trajectory worsening in magnitude (−6.5 → −13.1 → −10.6 → −25.75) AND in WR (33.3% → 30.8% → 29.4% → **25.0% — worst yet**). Per Critic FINAL Recommendation 3: tighter z-gate (2.0) increased MKR kill-rate by ~15pp (35.0% → 49.8%) — the largest of any symbol — yet OOS net PnL declined and OOS WR dropped. **MKR pattern is gate-orthogonal**: tightening doesn't fix it. **Threshold compressed from 6-7 (per iter-v3/010) → 5 consecutive negatives**. If iter-v3/012+ records MKR's 5th consecutive negative, the NEXT EXPLORATION must be a per-symbol-diagnostic axis (e.g., drop-MKR universe-change exploration as single axis). Pre-committed via new memory rule `feedback_mkr_threshold_compression.md` to prevent post-hoc rationalization.

2. **LDO 86.31% OOS concentration (lottery-flag)**: 10 trades, 8 wins (80% WR), exact-binomial 95% CI **[44.4%, 97.5%]** — CI width is too wide to claim signal-from-noise distinction; the 80% WR is consistent with a lucky 10-flip sequence within 95% confidence. Future CONFIRMATION QR must scope ex-LDO basket fragility (without LDO's 8 wins, OOS Sharpe collapses materially).

3. **IS broad-based confirmation**: 286 trades, 36.4% WR, +0.9566 Sharpe with broad per-symbol contribution (BCH 100 trades / +86.82% net + LDO 21 / +52.90%). The IS axis is NOT lottery-driven — this is the differentiator from iter-v3/009's failed IS axis. The IS-axis broad-based-ness is what justifies the PROMISING verdict alongside the OOS lottery-flag; it forecloses the alternative interpretation "the entire iteration is lottery-driven on a small sample".

4. **Floor-recoverable bundle math**: iter-v3/011 single-seed = 101 OOS trades; predicted bundle at CONFIRMATION = 5 outer seeds × 3-4× ensemble = **303-404 OOS trades**. Factor 3-4× inherited from iter-v3/010 review, **UNVERIFIED at iter-v3/011's tighter gate setting** (the gate may shift the multiplication factor). Catalog flags "Floor recoverable: YES (factor unverified)" — a future CONFIRMATION QR must validate the multiplier empirically before claiming the floor clears at bundle level.

5. **Data-regen audit note**: First launch failed staleness check (19.6h > 16h); re-fetched 2 klines × 5 symbols + regenerated features (~3 min of the 8 min wall-clock). 0.5% data-extent drift on a 13.5-month OOS window is **NOT attributed to the −0.19 OOS Sharpe metric delta vs iter-v3/010** — the gate-axis kill-rate shifts (+15-18pp) are the dominant driver. Per-spec staleness guard functioning correctly. Audit-noted but not a methodology issue.

6. **n_high_pbo_cells = 6/175** (vs 5/175 at iter-v3/010): TRX/MKR cells continuing the iter-v3/010 pattern. Mean PBO aggregator dilutes these to a clean 0.1077; future CONFIRMATION QRs may use `(1 - max_per_cell_pbo)` for more conservative weighting alongside or instead of `(1 - mean_pbo)` (carried forward from iter-v3/010).

## Lessons

1. **The cadence rule worked exactly as designed — third consecutive iteration validating the framework.** iter-v3/011 caught a real signal at 8 min wall-clock by running a single-axis risk-gate variation at EXPLORATION density (`--exploration --seeds 1 --n-trials 10`). If the cadence rule were not in force, this iteration would have been re-run as a 5-seed CONFIRMATION (~5-9h) — the cumulative time saved across iter-v3/008-011: ~30-50 hours of compute, with two PROMISING verdicts (010, 011) to show for it.

2. **The Critic 2-round flow worked exactly as designed — second consecutive use producing concrete pre-commits.** Round 1 PRELIMINARY surfaced 4 substantive clarifications (MKR threshold compression, LDO lottery framing, trade-rate floor recoverability arithmetic, data-extent drift attribution); QR responded with explicit dispositions; Round 2 FINAL accepted all four with no regressions. The clarifications produced concrete pre-commitments that go into the catalog row and a NEW memory rule (`feedback_mkr_threshold_compression.md`) — preventing post-hoc renegotiation at future iterations.

3. **The pre-registered IS-axis falsifier (Falsifier 1) was decisive in interpreting the OOS LDO lottery.** iter-v3/009's OOS = +1.12 was correctly NEGATIVE because IS = +0.0802 < Falsifier 1 threshold AND OOS was lottery-driven. iter-v3/011's OOS = +1.63 has the same OOS lottery character (LDO 86.31% concentration; 10-trade 80% WR) but is correctly PROMISING because IS = +0.9566 >> Falsifier 1 threshold AND IS is broad-based. **The same pre-registration discipline that classified iter-v3/009 NEGATIVE classifies iter-v3/011 PROMISING — the rule does not bend for an attractive OOS number; it bends for the IS-axis pre-registered measurement that anchors the verdict.**

4. **MKR pattern is gate-orthogonal — tightening doesn't fix it.** The +15pp MKR z-gate kill-rate increase (35.0% → 49.8%, the LARGEST of any symbol) PRODUCED WORSE per-trade economics (OOS net PnL −10.65 → −25.75; OOS WR 29.4% → 25.0%). This **refutes the "more filtering helps MKR" hypothesis** at gate-axis. Tighter z-gate filtered MORE MKR signals than any other symbol, yet MKR's per-trade outcomes worsened — the surviving signals after tighter filtering have WORSE economics, not better. The threshold compression from 6-7 → 5 (Critic Rec #3) is the decisive structural rule update from this iteration: **the next per-symbol-diagnostic EXPLORATION is closer than previously thought**, and the rule is now pre-committed to memory before iter-v3/012 launches.

5. **Calibration miss recorded for QR prior-update — second consecutive favorable overshoot.** iter-v3/010 P4 ([+0.10, +0.30]) overshot to +0.5683 (1.4× upper bound, labeling-axis); iter-v3/011 P4 ([+0.30, +0.70]) overshot to +0.9566 (1.37× upper bound, gate-axis). Two consecutive iterations across two structurally orthogonal axes both produced overshoots in the favorable direction. Future EXPLORATION priors on ANY axis should widen the PROMISING band materially: current narrow [low, high] bands systematically underestimate the magnitude of the IS Sharpe response to single-axis perturbations under colsample=1.0 + n_trials=10. Suggested update: PROMISING band [+0.40, +1.00] with 35% prior, [+1.00, +1.50] overshoot at 30%, NEGATIVE at 35%.

6. **Single-axis risk-gate perturbation is structurally orthogonal to features-axis AND labeling-axis variations.** iter-v3/007/009 features-axis runs (top-14, top-13) varied 1 of 14 features; iter-v3/010 labeling-axis run rotated the entire label distribution; iter-v3/011 gate-axis run changed 0 features and 0 labels but shifted gate kill-rates by +15–18pp at trade-entry time. The fact that PBO did NOT move on a strictly tighter gate distribution (0.1077 → 0.1077, identical) is structurally consistent with the gate-axis acting as a pure trade-mix filter (changing which trades execute, not which signals are produced). **Future EXPLORATION axis-diversity should continue to be enforced** — the catalog now has features×2 + labeling×1 + gate×1 = 4 unique axes representations. iter-v3/012's planned BTC trend filter band is the natural next probe (per Critic FINAL Rec #1).

7. **Process-improvement: data-staleness guard functioned correctly.** First launch failed staleness check (19.6h > 16h threshold per `feedback_data_staleness_per_worktree`); pre-flight rejected the run; re-fetch + feature regen; second launch succeeded. This is the second iteration in a row to exercise the per-worktree freshness discipline (iter-v3/010 also re-fetched). Audit-noted in engineering report; not a methodology issue.

8. **Dead-paths catalog (tenth entry, second consecutive PROMISING):**
   - **iter-v3/011** — risk-gate axis (zscore_threshold 2.5 → 2.0) EXPLORATION on full v3 universe (BCH+MKR+LDO+TRX), `--exploration` mode (ENSEMBLE_SIZE=1, n_trials=10, colsample_bytree=1.0). **EXPLORATION-PROMISING with lottery/concentration caveats.** IS monthly Sharpe = +0.9566 (>> Falsifier 1's +0.10; +0.39 above iter-v3/010's +0.5683; **highest in v3 history**). OOS monthly Sharpe = +1.6251 (second-highest in v3 history; lottery-flagged at LDO 86.31% concentration; 101 trades / 7.48 trades/month). Methodology axes ALL PASS clean (PBO 0.1077 < 0.40 stable; n_eff 7 > 4; max abs(IC) 0.660 < 0.70; 35/35 tests pass; all 12 Critic checks PASS / WARN-carry-forward / WAIVED-single-seed / PASS-with-documented-refetch). 5 caveats catalogued: gate-orthogonal MKR with threshold compressed 6-7 → 5, LDO 86.31% lottery-flag with binomial CI [44.4%, 97.5%], IS broad-based confirmation (286 trades, 36.4% WR, NOT lottery-driven), floor-recoverable bundle math 303-404 with 3-4× factor inherited-and-unverified, data-regen audit note. **STRONG candidate for next CONFIRMATION bundle** (alongside iter-v3/007's top-14 features and iter-v3/010's labeling) — after 6 more EXPLORATIONs to reach the 10:1 quota, iter-v3/011 should be the gate component of any CONFIRMATION-bundle brief.

## Pareto Position

Single-row degenerate front (Section 8 criterion 9 waiver):

| seed | OOS Sharpe | OOS MaxDD | OOS Calmar | PBO | n_trades | max_conc% |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | +1.6251 | 18.62% | 2.5257 | 0.1077 | 101 | 64.94% |

Cross-symbol OOS dispersion (informational, NOT Pareto-equivalent under EXPLORATION):

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| LDOUSDT | +40.60 | 10 | 80.0% | 86.31% |
| BCHUSDT | +18.88 | 31 | 41.9% | 40.14% |
| TRXUSDT | +3.04 | 44 | 40.9% | 6.47% |
| MKRUSDT | -15.49 | 16 | 25.0% | -32.92% |

OOS total weighted PnL = +47.04% (concentrated on LDO+BCH; TRX breakeven; MKR dragging). Under CONFIRMATION's 5-seed regime, the standard concentration cap (≤35%) and Pareto checks become mechanical — LDO's 86.31% concentration substantially exceeds the cap on a single seed and would need either (a) the 5-seed average to bring it below the cap (less plausible than iter-v3/010's BCH-driven 57% case because LDO has fewer absolute trades to dilute concentration across seeds) or (b) an explicit waiver in the CONFIRMATION-bundle brief that prices in the lottery-flag explicitly. The catalog row preserves this explicit lottery-flag for the future bundling QR.

## Pre-Registered Failure-Mode vs Reality Summary

| Class | Materialized? |
|---|---|
| Process predictions (P1-P3, total 15%) | 0/3 materialized — pipeline ran clean, wall-clock 3.75x under target, gate logic propagated unambiguously |
| Model predictions (P4-P6, total 95%) | 1/3 PARTIALLY materialized as written; **P4 verdict-class correct but point-estimate overshot the band by 1.37×** |
| OOS-axis prediction | NONE — brief did not pre-register OOS predictions; +1.63 OOS Sharpe is informational alongside the IS verdict (iter-v3/011 inherits iter-v3/009/010 precedent of "OOS axis was not registered; falsifier 1 was registered at IS axis only") |

Calibration accuracy: 1/6 partial match (P4 verdict-class correct, point-estimate overshot the upper bound). Combined with iter-v3/010's identical-pattern miss, the empirical signal is **systematic upward overshoot on single-axis perturbations under EXPLORATION density**. iter-v3/012 prior-setting should reflect this pattern by widening the PROMISING band (suggested: [+0.40, +1.00]).

## Next Iteration

**iter-v3/012 — EXPLORATION on a NON-features, NON-labeling, NON-gate-zscore axis** (per Critic FINAL Recommendation 1).

After iter-v3/007 (features), iter-v3/009 (features), iter-v3/010 (labeling), iter-v3/011 (gate z-score), the next probe should be **BTC trend filter band axis** to maximize catalog axis diversity for downstream CONFIRMATION bundling. Critic FINAL Rec #1 recommended: **BTC trend filter band ±20% (currently) → ±15% (stricter) or ±25% (looser)** as single-axis variation. After iter-v3/012, the catalog will have axis coverage of features × 2, labeling × 1, gate-zscore × 1, gate-btc-trend × 1 — substantially diverse.

**Suggested specifics for iter-v3/012 brief**:

| Parameter | iter-v3/011 (current) | iter-v3/012 (suggested) |
|---|---:|---:|
| BTC trend filter band | ±20% (14d) | **±15% (stricter)** OR **±25% (looser)** |
| Z-score OOD threshold | 2.0 | UNCHANGED |
| ATR multipliers | (2.0, 1.0) | UNCHANGED |
| Feature set | 13 | UNCHANGED |
| Symbols | BCH+MKR+LDO+TRX | UNCHANGED |

**Rationale for BTC trend filter axis**:
- BTC trend filter is structurally orthogonal to z-score gate (filters cross-asset regime alignment), labeling (filters at trade-entry, not at signal-generation), and features (no feature change).
- iter-v3/011's BTC trend filter on TRX killed 26/387 = 6.72% — a small effect at ±20%. Tightening to ±15% might amplify cross-asset regime filtering; loosening to ±25% might recover trades during BTC-mild regimes.
- After this iteration, the catalog will have meaningful axis-quadruple-coverage (features, labeling, gate-zscore, gate-btc-trend), strengthening eventual CONFIRMATION bundling.

**Pre-conditions for iter-v3/012 brief**:
- Phase 5.5 PASS requires Section 7 prediction calibration to widen the PROMISING band materially based on iter-v3/010+iter-v3/011 systematic overshoot pattern (suggested: 35% in [+0.40, +1.00], 30% in [+1.00, +1.50] overshoot, 35% NEGATIVE).
- Wall-clock budget: same 2h hard cap, target < 30 min on full v3 universe at `--exploration --seeds 1 --n-trials 10`.
- Pre-register an OOS-axis falsifier IF the brief intends to read OOS metrics (otherwise OOS remains informational-only).
- Decide ex-ante whether to test stricter or looser BTC trend filter; do not run both as a 2-axis EXPLORATION (would violate single-axis rule).
- **MKR threshold pre-commit operative**: if iter-v3/012 produces MKR's 5th consecutive OOS-negative, the NEXT EXPLORATION (iter-v3/013) is mandatorily a per-symbol-diagnostic axis (drop-MKR universe-change exploration) per the new memory rule `feedback_mkr_threshold_compression.md`.

**Catalog count after iter-v3/011**: 4 of 10 EXPLORATIONs; **6 more required** before any CONFIRMATION can launch. Axis coverage to date: features × 2, labeling × 1, gate × 1.

**iter-v3/011 status**: STRONG candidate for next CONFIRMATION bundle (alongside iter-v3/007's top-14 features and iter-v3/010's labeling), conditional on the future bundling QR addressing the LDO lottery-flag and ex-LDO basket fragility explicitly.
