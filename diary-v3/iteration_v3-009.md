# Iteration v3-009 — Diary

## Decision: EXPLORATION-NEGATIVE

Falsifier 1 (pre-registered in brief Section 4.3 at IS Sharpe < +0.10) mechanically activated by IS Sharpe = +0.0802. QR endorsed mechanical reading per `feedback_no_cheating` ("never override registered measurement on un-pre-registered evidence"). OOS = +1.1223 catalogued as INFORMATIONAL only (LDO-driven 12-trade lottery, OOS_trades=87 < 130 floor, MKR regression). All 12 methodology checks PASS / WAIVED / WARN-carry-forward; no process-level BLOCK.

Catalog row #2 of 10 needed before any CONFIRMATION can launch. Critic FINAL SHA `1bc828f`.

## What Was Tested

**Single-axis variation** (features axis): drop `vwap_dev_50` from `V3_FEATURE_COLUMNS`, reducing it from 14 features (iter-v3/007) to 13 features. Setup commit `56b8f8b` (inherited from iter-v3/008's aborted CONFIRMATION) made the code change; iter-v3/009 only updated `ITERATION_LABEL = "v3-009"` at SHA `43b3ed8`.

**Hypothesis** (brief Section 1): `vwap_dev_50`'s contribution was redundant with `ema_spread_atr_20` (IC=0.875) and `vwap_dev_20` (IC=0.794) rather than independent signal — so dropping it should preserve IS Sharpe in [+0.18, +0.28] band (i.e., iter-v3/007's +0.2241 ± 0.05).

**Configuration**: `--exploration --seeds 1 --n-trials 10` on full v3 universe (BCH+MKR+LDO+TRX), ENSEMBLE_SIZE=1, colsample_bytree=1.0, training_months=24, OOS_CUTOFF_DATE=2025-03-24 — identical to iter-v3/007 modulo the one dropped feature.

## What Was Measured

### Headline metrics

| Metric | iter-v3/007 (top-14) | iter-v3/009 (top-13) | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.2241 | **+0.0802** | **-0.144** |
| OOS monthly Sharpe | +0.0622 | **+1.1223** | +1.060 |
| OOS/IS ratio | 0.28 | 13.99 | — |
| IS trades | — | 267 | — |
| OOS trades | 90 | **87** | -3 |
| PBO (per-cell mean) | 0.1419 | **0.1145** | -0.027 |
| n_eff (per-cell median) | 7 | 7 | 0 |
| Wall-clock | 8 min | 11 min | +3 min |

**IS Sharpe = +0.0802 sat BELOW Falsifier 1's +0.10 threshold AND below the predicted [+0.18, +0.28] band.** Falsifier 1 mechanically activated.

### Per-symbol OOS PnL attribution

| Symbol | OOS trades | Win rate | weighted_pnl | concentration_pct | Note |
|---|---:|---:|---:|---:|---|
| LDOUSDT | 12 | **75.0%** | +70.77 | **132.97%** | binomial 95% CI on 75% WR: [42.8%, 94.5%] — too wide to claim signal |
| TRXUSDT | 25 | 44.0% | +1.00 | 1.87% | breakeven |
| BCHUSDT | 37 | 43.2% | -0.93 | -1.75% | flat |
| MKRUSDT | 13 | 30.8% | -17.61 | -33.09% | **regression vs iter-v3/007** (-6.5% → -13.1%) |

OOS total weighted_pnl = +53.22%, **98.61% concentration in LDO** (single-seed pareto front). Without LDO's 12-trade lucky run, OOS portfolio is -17.5% across 75 trades on the remaining three symbols.

### Methodology checks (Critic FINAL)

| # | Check | Status | Detail |
|---:|---|:---:|---|
| 1 | Look-Ahead | PASS | Zero new features; vwap_dev_50 DROPPED |
| 2 | Embargo | PASS | gap=88 (= (21+1)×4) verified at runtime |
| 3 | MT correction (methodology) | PASS | PBO=0.1145 < 0.40; n_eff=7 |
| 3 | MT correction (edge) | INFORMATIONAL | DSR=0.0, PSR=1.0 — single-seed exploration artifact |
| 4 | IC correlation | PASS | max \|IC\| = 0.6602 (< 0.70); 0 pairs above threshold |
| 5 | ADF stationarity | WARN-carry-forward | 17.7% non-stationary (same per-month low-T artifact) |
| 6 | Pareto dominance | WAIVED | Single-seed (Section 8 criterion 9) |
| 7 | Reproducibility | PASS | SHA `43b3ed8` stamped, libs pinned |
| 8 | Hypothesis alignment | PASS | Single-axis features variation; brief Section 1 = code |
| 9 | Symbol exclusion | PASS | {BCH,MKR,LDO,TRX} ∩ V3_EXCLUDED = ∅ |
| 10 | Feature isolation | PASS | features_v3 does not import v1/v2 |
| 11 | Forming-candle | PASS | Same data-staleness guard as iter-v3/007 |
| 12 | Library pinning | PASS | Stack matches iter-v3/007-008 |

## Brief Section 7 Prediction Calibration (5/5 check)

Per iter-v3/004's calibration discipline, every brief Section 7 prediction is reconciled post-hoc:

| ID | Class | P | Prediction | Outcome |
|---|---|---:|---|---|
| P1 | process | 5% | iter-v3/008 setup commit didn't propagate cleanly (rebase silently reverted drop, downstream test asserts 14) | DID NOT MATERIALIZE — `len(V3_FEATURE_COLUMNS)==13` and `'vwap_dev_50' not in V3_FEATURE_COLUMNS` both verified pre-flight; 35/35 tests PASS |
| P2 | process | 5% | wall-clock > 30 min on full v3 universe at exploration config | DID NOT MATERIALIZE — 11 min actual, 2.7x under 30-min target |
| P3 | process | 10% | iter-v3/009 importance ranks differ materially from iter-v3/007 (e.g., `range_realized_vol_50` shifts from rank 3 to 11) | DID NOT MATERIALIZE — top-3 importance order preserved |
| P4 | model | **60%** | IS Sharpe lands in [+0.18, +0.28] (predicted band; redundancy hypothesis confirmed) | **DID NOT MATERIALIZE** — IS Sharpe = +0.0802 sat **below** the band |
| P5 | model | **15%** | IS Sharpe drops to [+0.10, +0.18] — `vwap_dev_50` had small-but-real contribution | **PARTIALLY MATERIALIZED** — IS Sharpe (+0.0802) sits 0.02 below P5's lower band, closer to a deeper-than-P5 drop |
| P6 | model | 10% | IS Sharpe rises to >+0.30 — dropping redundancy unexpectedly helps | DID NOT MATERIALIZE — IS Sharpe dropped, did not rise |

**Calibration assessment**: 0/3 model-predictions materialized as written; the actual outcome (IS Sharpe = +0.0802) sat **below all three model predictions**, including the bearish P5 lower band. The QR weighted P4 (PROMISING band) at 60% and P5 (small drop) at 15% — reality undershot P5. The +1.12 OOS Sharpe was OUTSIDE all six prediction tracks (no OOS prediction was made — brief Section 4 explicitly assumed IS direction → OOS direction).

The miss is informative: **redundancy-drop hypothesis was rejected at the IS axis**. Either (a) `vwap_dev_50` was carrying small-but-real independent signal that the high-IC pairs were absorbing AND that the model needed under colsample=1.0, OR (b) the 1-feature drop materially shifted LightGBM's gain-estimation pattern in a way the 14-feature run did not have. Both readings argue against "redundancy was free to remove."

QR prior calibration miss: future EXPLORATION briefs on features-axis variation should weight "drop helps" / "drop neutral" / "drop hurts" closer to 30/30/40 (not 60/15/25), reflecting the empirical evidence that single-feature drops at colsample=1.0 are not free even when IC suggests redundancy.

## What Failed (and was caught by pre-registration discipline)

1. **OOS Sharpe = +1.1223 was the highest OOS in v3 track history** but is NOT evidence of edge.
   - 98.61% LDO concentration, 12 trades, 75% WR with 95% binomial CI [42.8%, 94.5%].
   - OOS_trades=87 < 130 trade-rate floor (`feedback_trade_rate_floor`).
   - MKR_OOS regression: iter-v3/007's MKR weighted_pnl was -14.03% on 12 trades; iter-v3/009's MKR is -17.61% on 13 trades — actually WORSE per-trade, arguing against uniform "redundancy drop helps" reading.
   - Single-seed run; DSR=0.0, PSR=1.0 are exploration-mode artifacts (degenerate at N=1).
   - Reading +1.12 OOS Sharpe as edge would require ignoring all four caveats above. The pre-registration discipline ("OOS axis was not registered; falsifier 1 was registered at IS axis only") is the correct mechanical disposition.

2. **Predicted P4 IS Sharpe band [+0.18, +0.28] missed by 0.10** in the unfavorable direction. The QR's prior weighted P4 at 60% probability — reality was inside neither P4 nor P5, falling 0.02 below P5's lower bound. This is a calibration miss (next iteration should weight "features-axis drop hurts" higher) but NOT an iteration failure: pre-registered falsifier 1 caught it cleanly.

3. **Carry-forward stale `_verify_feature_columns()` docstring** (Critic Clarification 3). `run_baseline_v3.py:182-185` references `"iter-v3/008 brief Section 3.3"` and `"iter-v3/008 CONFIRMATION"` — both stale (iter-v3/009 is EXPLORATION, brief is iter-v3/009's). This is the **second iteration with a stale docstring banner reference** (iter-v3/007 had the same pattern). Tracked as a P1 process-improvement for iter-v3/010's first commit: parametrize all banner/docstring references against `ITERATION_LABEL` so they cannot drift across rebases.

## Lessons

1. **Pre-registration discipline matters more than chasing OOS lift.** The +1.12 OOS Sharpe was the most attractive number in v3 history; the correct call was still EXPLORATION-NEGATIVE because IS Sharpe = +0.0802 mechanically activated Falsifier 1. Honoring pre-registration on the FIRST cadence-rule iteration (iter-v3/009) sets the precedent: future EXPLORATIONs cannot retroactively invent OOS-axis falsifiers when IS-axis falsifiers trip. The "no cheating" memory rule (`feedback_no_cheating`) is decisive on this kind of un-pre-registered evidence.

2. **The cadence rule worked exactly as designed.** iter-v3/008 was aborted at 4h 15min (extrapolated to ~25h) on a CONFIRMATION variant of the same hypothesis. iter-v3/009 ran the same hypothesis at EXPLORATION cost (11 min, 11/15 of cap) and revealed a fragile metric: IS Sharpe drops -0.144 with a single-feature redundancy removal under colsample=1.0. If the cadence rule were not in force, iter-v3/008 would have been re-run as 5-seed CONFIRMATION (~5-9h) and would have shown either (a) the same fragile IS metric at higher confidence, OR (b) a misleading multi-seed average that masked the IS instability. Either way, the 11-min EXPLORATION caught the issue before sinking 5-9h on a confirmation that would have failed mechanical Section 8 thresholds.

3. **Single-feature drops at colsample=1.0 are not free, even when IC suggests redundancy.** Under colsample=1.0, every tree split sees ALL features. Removing a high-IC feature does not just remove the redundancy — it also removes the feature's interaction effects with the lower-IC features that were not removed. The model loses information about how `vwap_dev_50` interacted with `range_realized_vol_50`, `max_dd_window_50`, etc., even when its marginal IC contribution was redundant. This is structurally distinct from the colsample<1.0 case where removed features would have been "wasted picks" anyway. Future feature-importance analyses should test paired-bootstrap CV at the actual `colsample_bytree` setting, not at colsample=1.0 default.

4. **Two consecutive features-axis EXPLORATION rows leave the catalog under-diverse** for downstream CONFIRMATION bundling. iter-v3/007 (top-14) and iter-v3/009 (top-13) both vary on the features axis. Per Critic FINAL Recommendation 1, iter-v3/010 should test a NON-features axis (labeling, risk gates, BTC trend filter, OOD threshold) to maximize axis diversity in the catalog. The 10-EXPLORATION quota is not just a count requirement — it is a diversity requirement.

5. **Calibration miss recorded for QR prior-update.** P4 (60% PROMISING band) missed; P5 (15% small drop) partially missed; reality was below all three model predictions. Future features-axis EXPLORATION priors should reweight 30/30/40 (drop helps / drop neutral / drop hurts) reflecting iter-v3/009's empirical evidence that single-feature redundancy removal at colsample=1.0 has non-trivial IS impact.

6. **dead-paths catalog (eighth entry, second NEGATIVE):**
   - **iter-v3/009** — top-13 features (drop `vwap_dev_50`) EXPLORATION on full v3 universe (BCH+MKR+LDO+TRX), `--exploration` mode (ENSEMBLE_SIZE=1, n_trials=10, colsample_bytree=1.0). **EXPLORATION-NEGATIVE.** IS monthly Sharpe = +0.0802 (vs predicted [+0.18, +0.28]; below Falsifier 1 +0.10 threshold; -0.144 vs iter-v3/007 +0.2241). OOS = +1.1223 INFORMATIONAL (LDO 12-trade 75% WR with binomial CI [42.8%, 94.5%], 98.61% concentration, MKR regression -6.5%→-13.1%, OOS_trades=87 < 130 floor, single-seed DSR=0/PSR=1 artifact). Wall-clock 11 min (2.7x under 30-min target). Methodology axes (Critic Checks 1, 2, 4, 7-12) PASS clean; Check 3 PASS-methodology with edge informational; Check 5 WARN-carry-forward; Check 6 WAIVED single-seed. Falsifier 1 mechanical activation honored per `feedback_no_cheating` (pre-registration discipline preserved on first cadence-rule iteration). **No re-test of vwap_dev_50 drop at this exploration config without paired-bootstrap CV evidence and an OOS-axis falsifier pre-registration.**

## Pareto Position

Single-row degenerate front (Section 8 criterion 9 waiver):

| seed | OOS Sharpe | OOS MaxDD | OOS Calmar | PBO | n_trades | max_conc% |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | +1.1223 | 37.90% | +1.4043 | 0.1145 | 87 | 98.61% |

Cross-symbol OOS dispersion (informational, NOT Pareto-equivalent under EXPLORATION):

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| LDOUSDT | +70.77 | 12 | **75.0%** | **132.97%** |
| TRXUSDT | +1.00 | 25 | 44.0% | 1.87% |
| BCHUSDT | -0.93 | 37 | 43.2% | -1.75% |
| MKRUSDT | -17.61 | 13 | 30.8% | -33.09% |

OOS total weighted PnL = +53.22% (driven entirely by LDO; the other three symbols are essentially flat or negative).

## Pre-Registered Failure-Mode vs Reality Summary

| Class | Materialized? |
|---|---|
| Process predictions (P1-P3, total 20%) | 0/3 materialized — pipeline ran clean, wall-clock under target, importance order stable |
| Model predictions (P4-P6, total 85%) | 0/3 materialized as written; reality was below all three bands |
| OOS-axis prediction | NONE — brief did not pre-register OOS predictions; +1.12 OOS Sharpe is INFORMATIONAL only |

Calibration accuracy: 0/6 strict matches; the QR's 70% PROMISING-pathway prior (P4+P6) was incorrect. iter-v3/010 prior-setting should reflect this miss.

## Next Iteration

**iter-v3/010 — EXPLORATION on a NON-features axis** (per Critic FINAL Recommendation 1).

Two consecutive features-axis EXPLORATIONs (iter-v3/007 top-14, iter-v3/009 top-13) leave the catalog under-diverse. The 10-EXPLORATION quota is a diversity requirement, not just a count requirement. iter-v3/010 should vary along a non-features axis to maximize axis diversity for downstream CONFIRMATION bundling.

**Suggested axis: LABELING (ATR multiplier perturbation).**

| Parameter | iter-v3/009 (current) | iter-v3/010 (suggested) |
|---|---:|---:|
| `tp_atr_mult` | 2.9 | **2.0** |
| `sl_atr_mult` | 1.45 | **1.0** |
| Timeout | 21 candles (7d) | 21 candles (UNCHANGED) |

**Rationale**:
- Labeling is the single most-impactful axis: it changes BOTH label distribution AND model targets simultaneously. A single-axis labeling perturbation is genuinely "one variable" because the change propagates uniformly through the triple-barrier label.
- Tighter targets (2.0/1.0) yield more frequent decisions per horizon, more labels per fold, and shift the IS/OOS distribution toward more-frequent / smaller-magnitude trades — orthogonal to features-axis variation.
- Specific candidate compared to alternatives:
  - **(a) Labeling tp/sl 2.0/1.0** (chosen): max-impact single variable.
  - **(b) z-score OOD threshold 2.5 → 2.0 or 3.0**: gate sensitivity, narrower than (a).
  - **(c) Drop a different feature** (e.g., `ema_spread_atr_20`): triangulates IS-drop attribution but stays on features axis (would not satisfy Critic Recommendation 1).
- (a) is preferred because it is fully orthogonal to features-axis variation and yields cleanly interpretable IS/OOS comparison vs iter-v3/007 + iter-v3/009.

**Pre-conditions for iter-v3/010 brief**:
- Phase 5.5 PASS requires Section 7 prediction calibration to weight "labeling perturbation hurts" ≥40% (reflecting iter-v3/009's calibration miss on features axis).
- Process improvement: parametrize `_verify_feature_columns()` docstring against `ITERATION_LABEL` in iter-v3/010's first commit (Critic FINAL Recommendation 3; second iteration with stale banner means promote to P1).
- Wall-clock budget: same 2h hard cap, target < 30 min on full v3 universe at `--exploration --seeds 1 --n-trials 10`.
- Pre-register an OOS-axis falsifier IF the brief intends to read OOS metrics (otherwise OOS remains informational-only per the iter-v3/009 precedent).

**Catalog count after iter-v3/009**: 2 of 10 EXPLORATIONs; 8 more required before any CONFIRMATION can launch.
