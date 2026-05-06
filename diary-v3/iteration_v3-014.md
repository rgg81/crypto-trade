# Iteration v3-014 — Diary

## Decision: EXPLORATION-NEGATIVE (clean)

Critic FINAL OVERALL = `EXPLORATION-NEGATIVE` at SHA `0346dae` — clean classification per brief §4.4 row 5 ("IS Sharpe down > 0.10 AND non-bit-identical roster"). The iteration tested the MANDATORY ADX-threshold axis (gate-adx single-axis variation, 20 → 25 tighter) per `feedback_v3_cadence_discipline.md` axis coverage requirement and Critic FINAL Recommendation 1 of iter-v3/013 (SHA `1ee0213`). Headline metrics co-direct strongly UNFAVORABLE: IS Sharpe Δ −0.35 (+0.6593 vs iter-v3/013 +1.0088); OOS Sharpe Δ −1.83 (+0.8661 vs iter-v3/013 +2.6970, the LARGEST NEGATIVE OOS delta in v3 history). The OOS magnitude (−1.83) mirrors iter-v3/013's +1.11 mechanical drag-removal in opposite direction at 1.65× magnitude — the ADX axis is asymmetric and high-impact. Trade roster non-identical (153 IS vs 209) AND axis propagated (153 < falsifier threshold 167; ADX kills increased on all 3 symbols by 46.9–66.7%) AND IS Sharpe Δ −0.35 < −0.10 NEGATIVE threshold — all three conditions of brief §4.4 row 5 met cleanly. NOT a NULL-RESULT (distinguishing from iter-v3/012, which had bit-identical roster); NOT PROMISING-MECHANICAL (which requires bit-identical roster on retained symbols). The clean `EXPLORATION-NEGATIVE` classification preserves catalog discipline without subtype proliferation; the asymmetric magnitude observation lives in catalog caveats.

## Headline

**OOS Sharpe Δ −1.83 — the LARGEST NEGATIVE OOS delta in v3 track history** (mirroring iter-v3/013's +1.11 in opposite direction at 1.65× magnitude). **OOS MaxDD doubled 12.47% → 25.15%** (+12.68pp; meaningful downside-profile deterioration). **IS Sharpe Δ −0.35** (+0.6593 vs iter-v3/013 +1.0088). **LDO trade collapse 10 → 2** (−80% kill rate; weighted_pnl +40.60% → +7.39% = −81% collapse; WR 80.0% → 50.0% on n=2 noise). **Saturation predictor PASS** (153 IS trades < 167 derived threshold; gate fire-rate verifier PASS — ADX kills increased BCH +66.7%, LDO +58.5%, TRX +46.9%). The gate change took effect; the gate change just hurt the model.

## What Was Tested

**Single-axis variation** (risk-gate → ADX threshold 20 → 25 tighter): `RiskV2Config(zscore_threshold=2.0, adx_threshold=25.0,)`. Setup commit `bdcce5d`. ITERATION_LABEL updated to `v3-014`. Stale `= 88` docstrings + comments at `run_baseline_v3.py:206/211` parametrized against `REQUIRED_GAP` (Critic FINAL Rec 3 hygiene fix from iter-v3/013 satisfied). Zero src/ code changes beyond runner edit + hygiene fix. Zero feature/labeling/z-score-gate/BTC-band/universe changes. The only behavior change is ADX gate threshold tightening from 20 to 25.

**Hypothesis** (brief Section 1, SHA `29f054e`): Tightening ADX threshold from 20 to 25 will produce IS Sharpe maintained or improved (≥+0.40, vs iter-v3/013's +1.01) by filtering more aggressively against ranging/choppy regimes. Mechanism: the [20, 25) ADX bucket is a marginal-trend regime where the model's edge is thin (37.14% WR vs 41.73% in KEEP bucket per IS counterfactual).

**Hypothesis verdict: NOT SUPPORTED.** IS Sharpe +0.6593 (vs predicted [+0.50, +1.30] median +0.90; observed +0.66 at lower end of band, below median by 0.24). OOS Sharpe +0.8661 (Δ −1.83 from iter-v3/013, largest negative in v3 history). Behavioral-effect predictor falsifier PASS (153 IS trades < 167 derived threshold; ADX gate fire-rate increased on all 3 symbols, confirming axis propagation). The hypothesis was that tighter ADX would trim a lower-quality bucket; the realized outcome shows tighter ADX over-restricts and removes valuable signal that the model was leveraging downstream. Brief §2.1 OOS_caveat correctly pre-registered the OOS risk: "the OOS [20, 25) bucket carried 61.48% of iter-v3/013 OOS PnL" — the realized OOS Sharpe Δ −1.83 confirms the OOS caveat was prescient.

**Configuration**: `--exploration --seeds 1 --n-trials 10` on 3-symbol v3 universe (BCH+LDO+TRX), ENSEMBLE_SIZE=1, colsample_bytree=1.0, training_months=24, OOS_CUTOFF_DATE=2025-03-24. Identical to iter-v3/013 modulo the `adx_threshold` value (default 20 → explicit 25) + ITERATION_LABEL (cosmetic) + stale-docstring hygiene fix.

**Axis chosen per Critic FINAL Recommendation 1 of iter-v3/013** (SHA `1ee0213`): "iter-v3/014 axis MUST be ADX threshold (currently 20; 18 looser OR 25 tighter)." QR chose tighter direction (25) to stress-test whether the strategy benefits from ADX-defined trend regime filtering; iter-v3/015 will test 18 (looser) per Critic FINAL Rec 1 disposition (now MANDATORY per `feedback_adx_axis_asymmetric_v3.md` rule pre-commit).

## What Was Measured

### Headline metrics

| Metric | iter-v3/013 (current) | iter-v3/014 (this run) | Δ vs iter-v3/013 |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.0088 | **+0.6593** | **−0.35** |
| OOS monthly Sharpe | +2.6970 | **+0.8661** | **−1.83 (LARGEST NEGATIVE in v3 history)** |
| IS daily Sharpe | — | +1.7478 | — |
| OOS daily Sharpe | — | +1.9706 | — |
| IS/OOS ratio | 2.67 | **1.31** | OOS now BELOW IS (reversal) |
| IS trades | 209 | **153** | **−56** |
| OOS trades | 85 | **60** | **−25 (BELOW 130-trade floor)** |
| IS max drawdown | 20.77% | 21.88% | +1.11pp |
| OOS max drawdown | 12.47% | **25.15%** | **+12.68pp (doubled)** |
| OOS Calmar | 4.96 | 0.7150 | −4.24 |
| Profit Factor (OOS) | — | 1.3122 | — |
| Win Rate (OOS) | — | 40.00% | — |
| PBO (per-cell mean) | 0.1075 | 0.1075 | 0.00 (BIT-IDENTICAL) |
| n_eff (per-cell median) | 7 | 7 | 0 (BIT-IDENTICAL) |
| n_high_pbo_cells_99 | 2 | **2** | 0 (TRX 2025-Q4 carry-forward) |
| Wall-clock | 6 min | 6 min | 0 |

**The Δ −1.83 OOS Sharpe is the LARGEST NEGATIVE single-iteration OOS jump in v3 track history**, mirroring iter-v3/013's positive Δ +1.11 in opposite direction at 1.65× magnitude. This reveals ADX is an asymmetric high-impact axis — symmetric-direction validation (iter-v3/015 ADX=18) is MANDATORY per `feedback_adx_axis_asymmetric_v3.md` rule pre-commit. Falsifier 1 (IS Sharpe < +0.10) NOT triggered (+0.66 above). Falsifier 2 (IS trades > 167 = 1.2 × 139 counterfactual) NOT triggered (=153, Δ = −14 buffer). Falsifier 3 (wall-clock > 30 min) NOT triggered (6 min). **All falsifiers PASS clean.** The 17-verifier reconciliation (engineering report Section 3.6) shows 17/17 PASS including the new ADX gate fire-rate verifier (§3.6 row 17).

### Per-symbol OOS attribution

| Symbol | Trades | Win Rate | Weighted PnL | Concentration % | Δ trades vs iter-v3/013 | Δ WR |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 20 | 35.0% | +5.54% | 30.81% | −11 (−35%) | −6.9pp |
| LDOUSDT | **2** | 50.0% (n=2 noise) | +7.39% | 41.13% | **−8 (−80%)** | −30.0pp |
| TRXUSDT | 38 | 42.1% | +5.05% | 28.07% | −6 (−14%) | −1.1pp |
| **TOTAL** | **60** | 40.0% | +17.98% | — | **−25 (−29%)** | — |

**LDO trade collapse 10 → 2 is the dominant OOS Sharpe collapse driver**. iter-v3/013 LDO OOS contributed +40.60% weighted_pnl (65.65% of total); iter-v3/014 LDO OOS contributes only +7.39% (41.13% of total). The 80% kill rate on LDO reflects ADX kills increasing +58.5% (224 → 355, the largest proportional increase). The 50% WR on n=2 is statistically meaningless — exact-binomial 95% CI on 50% WR at n=2 is approximately [1.3%, 98.7%]. WR degraded on 3/3 symbols (BCH 41.9% → 35.0%, LDO 80.0% → 50.0% n=2 noise, TRX 43.2% → 42.1%).

### ADX gate fire-rate verifier (§3.6 row 17 PASS)

| Symbol | iter-v3/013 ADX kills | iter-v3/014 ADX kills | Δ |
|---|---:|---:|---:|
| BCHUSDT | 676 (21.3%) | 1127 (35.6%) | +451 (+66.7%) |
| LDOUSDT | 224 (21.8%) | 355 (34.5%) | +131 (+58.5%) |
| TRXUSDT | 640 (23.1%) | 940 (33.9%) | +300 (+46.9%) |
| **Total** | **1540** | **2422** | **+882 (+57.3%)** |

**Gate DID tighten (Verifier §3.6 row 17 PASS)**. ADX tightening accounts for the majority of additional kills. Low-vol filter kill counts DECREASED (BCH 19.3% → 11.9%, LDO 16.6% → 10.0%, TRX 13.4% → 8.9%) because the ordering of gate evaluation means fewer signals survive to be evaluated by the low-vol filter after the earlier ADX gate kills more.

### Saturation predictor outcome

| Metric | Value |
|---|---:|
| iter-v3/013 IS trades (baseline) | 209 |
| Counterfactual IS [20, 25)_KILL bucket | 70 |
| **counterfactual_n_trades (IS)** | **139** = 209 − 70 |
| **saturation falsifier_threshold (IS)** | **167** = ceil(1.2 × 139) |
| Observed IS trades | **153** |
| Buffer below threshold | **−14** |
| **Verdict** | **PASS** (153 < 167) |

**Saturation predictor parametrized correctly per Critic FINAL Rec 3 of iter-v3/013** (`falsifier_threshold = ceil(1.2 × counterfactual_n_trades)` derived from §2.2 of brief, not hardcoded). The 1.2× factor absorbed Optuna re-optimization variance (+14 trades beyond the simple-subtraction estimate of 139) without false-triggering. Second consecutive successful parametrization (iter-v3/013 used threshold 240 for a NULL-RESULT-style check; iter-v3/014 used 167 for a genuine behavioral-effect check). The double-signal approach (saturation + gate fire-rate) provides robust disambiguation between "axis propagated" and "axis-saturated NULL-RESULT" — if saturation falsifier had triggered (>167) AND gate fire-rate INCREASED, the diagnosis would shift to "Optuna re-opened previously-cooled-down candles aggressively"; if saturation falsifier triggered AND gate fire-rate UNCHANGED, the diagnosis would shift to "axis didn't propagate (RiskV2Config kwarg drop)". Neither materialized; the parametrization works as designed.

### Methodology checks (Critic FINAL — SHA `0346dae`)

| # | Check | Status | Detail |
|---:|---|:---:|---|
| 1 | Look-Ahead | PASS | 13 V3_FEATURE_COLUMNS byte-identical to iter-v3/013; gate-axis introduces no new feature paths; ADX is past-only Wilder rolling on prior OHLC |
| 2 | Embargo | PASS | REQUIRED_GAP = 66 = (21+1)×3 confirmed at runtime; CPCV n_paths=45, embargo=27 symmetric; stale `= 88` docstrings REMOVED at SHA `bdcce5d` (Critic FINAL Rec 3 hygiene fix complete) |
| 3 | MT correction (methodology) | INFORMATIONAL | PBO = 0.1075 (statistically identical to iter-v3/013 0.1075); n_eff = 7 BIT-IDENTICAL; 2/127 cells with PBO > 0.99 (both TRX 2025-Q4 carry-forward; BCH/2024-10 at 0.9868 below 0.99 cutoff per QR Clarification 3); max-aggregator pre-commit travels forward |
| 3 | MT correction (edge) | INFORMATIONAL | DSR = 0.0, PSR = 1.0 — single-seed exploration artifact (cadence-rule informational) |
| 4 | IC correlation | PASS | max abs(IC) = 0.6847 (< 0.70); zero new features; bit-identical to iter-v3/013 |
| 5 | ADF stationarity | PASS (PROMOTED) | 1657/2041 (81.2%) cells stationary; 384 non-stationary concentrate in 2020-Q1 sparse-data per QR Clarification 1; V3_FEATURE_COLUMNS bit-identical to iter-v3/009 |
| 6 | Pareto dominance | PASS (vacuous, single-seed) | EXPLORATION single-seed; LDO 41.13% concentration > 30% CONFIRMATION cap — informational under EXPLORATION |
| 7 | Reproducibility | PASS | SHAs `bdcce5d` runner / `33f389f` analysis / `29f054e` brief / `23ac3ae` Phase 5.5 gate / `451be33` engineering report stamped; spot-check OOS trades.csv reproduces (engineering report verified TP/SL math on 3 random rows) |
| 8 | Hypothesis alignment | PASS-WITH-FAILED-HYPOTHESIS / SATURATION FALSIFIER PASS | Single-axis cadence rule honored; IS Sharpe Δ −0.35 < −0.10 NEGATIVE threshold (§4.4 row 5); behavioral-effect verifier PASS (153 < 167 threshold; Δ = −14 buffer); ADX gate fire-rate increased on all 3 symbols (Verifier §3.6 row 17 PASS) — gate DID tighten, hypothesis NOT supported |
| 9 | Symbol exclusion | PASS | {BCH, LDO, TRX} ∩ V3_EXCLUDED_SYMBOLS = ∅ |
| 10 | Feature isolation | PASS | features_v3 does not import v1/v2 |
| 11 | Forming-candle | PASS | Pre-flight staleness guard functioning per spec |
| 12 | Library pinning | PASS | Stack identical to iter-v3/008-013 (lightgbm 4.6.0, numpy 2.2.6, etc.) |

**All 12 Critic checks PASS / WAIVED-INFORMATIONAL / PASS-promoted (Check 5 PROMOTED from PRELIMINARY WARN per QR Clarification 1).** Zero BLOCK conditions. The NEGATIVE classification is the verdict on the *hypothesis axis* (axis was tested cleanly, hypothesis NOT supported, axis change degraded edge below threshold), NOT on the methodology axis (where everything is clean).

## Brief Section 7 Prediction Calibration (7/7 check)

Per iter-v3/004's calibration discipline, every brief Section 7 prediction is reconciled post-hoc:

| ID | Class | P | Prediction | Outcome |
|---|---|---:|---|---|
| P1 | process | 5% | ADX threshold edit doesn't propagate (`adx_threshold=25.0` kwarg lost) | DID NOT MATERIALIZE — pre-flight grep PASS, runtime ADX kills increased on all 3 symbols (Verifier §3.6 row 17 PASS), saturation falsifier PASS (153 < 167) |
| P2 | process | 5% | Wall-clock > 30 min | DID NOT MATERIALIZE — 6 min actual, 5x under target |
| P3 | process | 10% | Saturation falsifier calibration too tight (1.2× factor over-restrictive) | DID NOT MATERIALIZE — 153 < 167 PASS with Δ = −14 buffer; 1.2× factor worked correctly |
| P4 | model | 50% | IS Sharpe lifts to [+1.10, +1.30]; PROMISING (KILL bucket trims lower-quality trades) | DID NOT MATERIALIZE — IS Sharpe +0.66 in lower half of band, BELOW median |
| P5 | model | 30% | IS Sharpe stays in iter-v3/013 ±0.10 (PROMISING-INERT) | DID NOT MATERIALIZE — Δ −0.35 outside ±0.10 band |
| P6 | model | **20%** | IS Sharpe drops to < +0.91; tighter ADX over-restricts; NEGATIVE-soft | **MATERIALIZED — observed +0.66 < +0.91 AND OOS Δ −1.83**; the low-probability adversarial outcome fired |
| P7 | model | 5% | IS Sharpe spikes to > +1.30 (PROMISING-strong) | DID NOT MATERIALIZE |

**Calibration result — 6/7 process predictions clean, P6 materialized at the assigned 20% probability** (the brief explicitly flagged the OOS_caveat at §2.1 that the [20, 25) bucket carried 61% of iter-v3/013 OOS PnL; tightening ADX is high-variance OOS proposition). The 3rd-consecutive-overshoot pattern (010, 011, 013) did NOT continue — iter-v3/014 returned a NEGATIVE outcome with IS Sharpe in the lower half of the predicted band. The brief's pre-widening of the upper bound (+30% per iter-v3/013 caveat 4) was appropriate for behavior-changing axes; the OUTCOME landed below the median, not above the upper bound. The pattern of "QR's prior bands have been conservative on behavior-changing axes" continues in calibration discipline (the prediction was NOT over-confident upward — the realized outcome was a low-probability adversarial materialization).

## Pareto Position

Single-row degenerate front (Section 8 criterion 9 waiver):

| seed | OOS Sharpe | OOS MaxDD | OOS Calmar | PBO | n_trades | max_conc% |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | +0.8661 | 25.15% | 0.7150 | 0.1075 | 60 | 41.13% |

Cross-symbol OOS dispersion (informational, NOT Pareto-equivalent under EXPLORATION):

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| LDOUSDT | +7.39% | 2 (n=2 noise) | 50.0% | 41.13% |
| BCHUSDT | +5.54% | 20 | 35.0% | 30.81% |
| TRXUSDT | +5.05% | 38 | 42.1% | 28.07% |

**OOS picture is structurally degraded vs iter-v3/013** with all 3 symbols showing reduced trade counts, lower win rates, and substantially smaller weighted PnL. LDO's collapse to 2 trades is the dominant driver of OOS Sharpe degradation; BCH and TRX also degraded but proportionally less.

## Caveats Recorded for Audit Trail

The NEGATIVE-clean verdict comes with five explicit caveats catalogued for the future CONFIRMATION-bundling QR (per Critic FINAL Recommendation 2):

1. **`verdict = NEGATIVE` (clean)** per brief §4.4 row 5: IS Sharpe Δ −0.35 < −0.10 NEGATIVE threshold AND non-bit-identical roster (153 vs 209) AND axis propagated (saturation falsifier PASS, gate fire-rate increased on all 3 symbols by 46.9–66.7%). All three §4.4 row 5 conditions met cleanly. NOT a NULL-RESULT (distinguishing from iter-v3/012 which had bit-identical roster); NOT PROMISING-MECHANICAL (which requires bit-identical roster on retained symbols). The clean NEGATIVE classification preserves catalog discipline without subtype proliferation; the asymmetric magnitude observation lives in catalog caveats.

2. **`largest_negative_OOS_delta_in_v3_history = -1.83`** (asymmetric magnitude): Δ OOS −1.83 mirrors iter-v3/013's +1.11 in opposite direction at 1.65× magnitude. The ADX axis is asymmetric and high-impact — symmetric-direction validation (iter-v3/015 ADX=18) is MANDATORY per `feedback_adx_axis_asymmetric_v3.md` rule pre-commit. After iter-v3/015 completes, ADX axis is CLOSED for further EXPLORATION; iter-v3/016+ moves to a different axis regardless of iter-v3/015 outcome.

3. **`LDO_trade_collapse = 10 → 2`** (−80% kill rate): LDO is the symbol most affected by the ADX tightening (ADX kills +58.5%, the largest proportional increase). iter-v3/013 LDO OOS contributed +40.60% weighted_pnl (65.65% of total); iter-v3/014 LDO OOS contributes only +7.39% (41.13% of total). 50% WR on n=2 is statistically meaningless (exact-binomial 95% CI [1.3%, 98.7%]). The LDO collapse is the dominant OOS Sharpe degradation driver. Future CONFIRMATION QR scoping ex-LDO basket fragility carries forward unchanged from iter-v3/011/012/013 + this iteration's LDO collapse evidence.

4. **`oos_n_trades_60_below_130_floor`** (informational caveat): OOS 60 trades is well below the 130-trade floor (`feedback_trade_rate_floor`). Verdict is purely IS-axis driven; OOS Sharpe +0.87 records as informational caveat, NOT in verdict cell. Bundle-level math (60 × 5 outer × 3-4× ensemble = 900-1200 OOS bundle trades) clears the 130-trade floor at CONFIRMATION; single-seed EXPLORATION underpowering is structural, not a methodology issue.

5. **`iter-v3/015_axis_mandated = ADX 20 → 18`** per Critic Rec #1: pre-committed via new memory rule `feedback_adx_axis_asymmetric_v3.md`. The asymmetric magnitude (Δ OOS −1.83 = 1.65× iter-v3/013's +1.11) demonstrates ADX is one of the most impactful single-axis variations tested in v3 to date. Cataloguing only the tighter direction without testing the looser direction leaves the catalog with asymmetric understanding. iter-v3/015 ADX=18 closes the symmetric direction; iter-v3/016+ moves to different axis regardless of iter-v3/015 outcome. Cannot be renegotiated post-hoc.

## Lessons

1. **ADX axis is asymmetric and high-impact**. The Δ OOS −1.83 magnitude (1.65× iter-v3/013's mechanical drag-removal +1.11) demonstrates ADX is one of the most impactful single-axis variations tested in v3 to date. The mechanism — gate threshold change directly redistributes the per-(symbol, candle) trade roster — is structurally orthogonal to feature/labeling/universe axes (which act through model retraining). Tighter ADX over-restricts at threshold 25; the [20, 25) bucket carried valuable signal that the model was leveraging downstream. Per `feedback_adx_axis_asymmetric_v3.md` pre-commit, iter-v3/015 axis = ADX threshold 18 (looser) MANDATORY for direction-symmetry validation; iter-v3/016+ moves to different axis regardless of iter-v3/015 outcome. Cannot be renegotiated post-hoc.

2. **3 of 6 EXPLORATIONs are NEGATIVE-class (009, 012, 014); 3 are PROMISING/PROMISING-MECHANICAL (007, 010, 011, 013)**. Update: with iter-v3/014 NEGATIVE, the v3 catalog now has 3 NEGATIVE-class iterations (009 NEGATIVE, 012 NEGATIVE-no-effect NULL-RESULT, 014 NEGATIVE) and 4 PROMISING-class iterations (007 PROMISING, 010 PROMISING, 011 PROMISING, 013 PROMISING-MECHANICAL). The 4:3 ratio is reasonable for EXPLORATION discipline; the catalog correctly captures both directional-evidence sides of each axis. Future CONFIRMATION QR has comprehensive coverage of features/labeling/universe-drag-removal PROMISING signals AND axis-saturation/over-restriction NEGATIVE counter-evidence.

3. **Saturation predictor parametrization continues to work** (`falsifier_threshold = ceil(1.2 × counterfactual_n_trades)` per Critic FINAL Rec 3 of iter-v3/013). Second consecutive successful parametrization: iter-v3/013 used threshold 240 for NULL-RESULT-style check; iter-v3/014 used 167 for genuine behavioral-effect check. The 1.2× factor absorbed Optuna re-optimization variance (+14 trades) without false-triggering. Future EXPLORATION briefs continue this discipline — Section 8 must include behavioral-effect verifier with derived falsifier threshold.

4. **OOS_caveat in brief §2.1 was prescient and load-bearing**. iter-v3/014's brief explicitly flagged "the OOS [20, 25) bucket carried 61.48% of iter-v3/013 OOS PnL (+38.03 weighted_pnl)" — the realized OOS Δ −1.83 confirms the caveat was accurate. The OOS attribution analysis in brief §2.1 (re-aggregating iter-v3/013 trade rosters by ADX bucket at entry candle) provided genuine forward-looking risk visibility WITHOUT contaminating the OOS axis (the analysis re-bucketed already-disclosed iter-v3/013 trades; no new OOS information generated). Future EXPLORATION briefs continue this counterfactual discipline for behavior-changing axes — IS-only counterfactual analysis is informative but OOS-attribution counterfactual analysis is load-bearing for risk forecasting on behavior-changing gate-axes.

5. **Pre-commit ADX=18 for iter-v3/015 to validate direction symmetry**. Per Critic FINAL Recommendation 1 + new memory rule `feedback_adx_axis_asymmetric_v3.md`: iter-v3/015 axis = ADX threshold 18 (looser) MANDATORY. This test answers whether: (a) ADDING the [18, 20) bucket symmetrically improves the strategy (suggesting ADX should loosen); (b) ADDING the [18, 20) bucket symmetrically degrades the strategy (suggesting ADX=20 is structurally near-optimal, a local minimum); or (c) ADDING the [18, 20) bucket has neutral/inert effect (suggesting [18, 20) is Sharpe-equivalent to [20, 25) which we now know is high-value, contradicting (a) and (b)). The result will close the ADX axis cleanly; iter-v3/016+ moves to a different axis (low-vol filter floor 0.33, vol-scaling clip range [0.3, 1.0], or ±25% BTC band looser direction deferred since iter-v3/012) regardless of iter-v3/015 outcome.

6. **Critic 2-round flow worked as designed (5th consecutive use producing concrete pre-commits)**. Round 1 PRELIMINARY surfaced 5 substantive clarifications (ADF demotion, catalog framing as NEGATIVE-clean, high-PBO cells, iter-v3/015 axis pre-commit, trade-rate floor); QR responded with explicit dispositions; Round 2 FINAL accepted all five with no regressions. The clarifications produced a concrete pre-commitment (iter-v3/015 ADX=18) + a NEW memory rule (`feedback_adx_axis_asymmetric_v3.md`) — preventing post-hoc renegotiation at iter-v3/015. The Critic FINAL also issued Recommendation 3 (ADX axis should not be tested at MORE than 25; iter-v3/015 ADX=18 closes symmetric direction; iter-v3/016+ moves to different axis regardless).

7. **Dead-paths catalog (thirteenth entry, seventh EXPLORATION row, NEGATIVE-clean classification):**
   - **iter-v3/014** — risk-gate axis (ADX threshold 20 → 25, tighter) EXPLORATION on v3 universe, `--exploration` mode (ENSEMBLE_SIZE=1, n_trials=10, colsample_bytree=1.0). **EXPLORATION-NEGATIVE (clean)**. IS monthly Sharpe = +0.6593 (Δ −0.35 vs iter-v3/013 +1.0088). OOS monthly Sharpe = +0.8661 (Δ −1.83 vs iter-v3/013 +2.6970, the LARGEST NEGATIVE OOS delta in v3 history; informational below 130-trade floor). OOS MaxDD doubled 12.47% → 25.15% (+12.68pp). LDO trade collapse 10 → 2 (−80% kill rate; weighted_pnl +40.60% → +7.39% = −81% collapse; WR 80.0% → 50.0% n=2 noise). Saturation falsifier PASS (153 IS trades < 167 derived threshold; Δ = −14 buffer). ADX gate fire-rate increased on all 3 symbols (BCH +66.7%, LDO +58.5%, TRX +46.9%). PBO 0.1075 statistically identical to iter-v3/013 0.1075; n_eff 7 BIT-IDENTICAL; `n_high_pbo_cells_99 = 2` (TRX 2025-Q4 carry-forward, max-aggregator pre-commit travels). 5 caveats catalogued. **NOT a CONFIRMATION-bundle candidate**: tighter ADX over-restricted; the [20, 25) trades carried valuable model signal; iter-v3/015 ADX=18 mandated for direction-symmetry validation per `feedback_adx_axis_asymmetric_v3.md` rule pre-commit. The catalog count advances 6 → 7 of 10; iter-v3/015 axis is ADX threshold 18 per Critic FINAL Recommendation 1.

## Pre-Registered Failure-Mode vs Reality Summary

| Class | Materialized? |
|---|---|
| Process predictions (P1-P3, total 20%) | 0/3 materialized — pipeline ran clean, wall-clock 5x under target, ADX edit propagated cleanly (Verifier §3.6 row 8 PASS, row 17 PASS, saturation falsifier PASS) |
| Model predictions (P4-P7, total 105%) | P6 materialized at 20% probability (IS Sharpe +0.66 < +0.91; tighter ADX over-restricted; NEGATIVE-soft) — the low-probability adversarial outcome fired |
| OOS-axis prediction | informational under EXPLORATION; the brief §2.1 OOS_caveat correctly flagged 61% OOS PnL in KILL bucket; realized Δ −1.83 confirms the caveat was prescient |
| Behavioral-effect verifier (saturation falsifier + gate fire-rate) | BOTH PASS — 153 < 167 saturation; ADX kills increased on all 3 symbols 46.9–66.7% gate fire-rate |

Calibration accuracy: 4/4 process + behavioral-effect predictions clean (P1-P3 + saturation falsifier + gate fire-rate); 1/4 model predictions fired (P6 at 20% probability — adversarial outcome). The 3-iteration favorable IS calibration overshoot pattern (010, 011, 013) did NOT continue at iter-v3/014; the brief's pre-widening of the upper bound (+30%) was appropriate for behavior-changing axes; the realized outcome landed below the median rather than above the upper bound. The new `feedback_adx_axis_asymmetric_v3.md` rule does NOT close a calibration gap (calibration discipline already pre-committed for widening) — it closes an axis-coverage gap (asymmetric direction-symmetry validation for high-impact gate axes).

## Next Iteration

**iter-v3/015 — axis: ADX threshold 20 → 18 (looser direction)** per Critic FINAL Recommendation 1 of iter-v3/014 review (this diary's review SHA `0346dae`) AND new memory rule `feedback_adx_axis_asymmetric_v3.md` MANDATORY pre-commit.

ADX threshold 18 (looser direction) closes the symmetric-direction validation for the gate-adx axis. After iter-v3/015 completes (regardless of outcome), ADX axis is CLOSED for further EXPLORATION; iter-v3/016+ moves to a different axis (low-vol filter floor 0.33, vol-scaling clip range [0.3, 1.0], or ±25% BTC band looser direction deferred since iter-v3/012). Suggested specifics:

| Parameter | iter-v3/014 (current) | iter-v3/015 (mandated) |
|---|---:|---:|
| Universe | BCH+LDO+TRX (3 symbols) | UNCHANGED |
| Z-score OOD threshold | 2.0 | UNCHANGED |
| ATR multipliers | (2.0, 1.0) | UNCHANGED |
| BTC trend filter band | ±15% | UNCHANGED |
| Feature set | 13 columns | UNCHANGED |
| **ADX threshold** | **25 (tighter)** | **18 (looser) — MANDATORY per `feedback_adx_axis_asymmetric_v3.md`** |

**Pre-conditions for iter-v3/015 brief**:
- Section 8 saturation predictor falsifier MUST derive `falsifier_threshold = ceil(1.2 × counterfactual_n_trades)` per Critic FINAL Rec 3 chain — counterfactual must include the NEW [18, 20) ADX bucket entries (i.e., trades that iter-v3/014 would NOT have accepted but iter-v3/015 WILL accept). Direction of falsifier: `IS trades < ceil(1.2 × n_trades_counterfactual)` where counterfactual = iter-v3/014's 153 + estimated [18, 20) bucket additions.
- Brief Section 7 prediction band may use moderate width given the iter-v3/014 NEGATIVE outcome (suggesting ADX axis is genuinely impactful and behavior-changing) — avoid over-widening on the looser-direction symmetric test.
- Pre-register an OOS-axis falsifier IF the brief intends to read OOS metrics (otherwise OOS remains informational-only).
- Single-axis discipline: ONLY ADX threshold changes (20 → 18). No other parameter variation.
- Wall-clock budget: same 2h hard cap, target < 30 min on 3-symbol universe at `--exploration --seeds 1 --n-trials 10`.

**Catalog count after iter-v3/014**: 7 of 10 EXPLORATIONs; **3 more required** before any CONFIRMATION can launch. Axis coverage to date: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 + gate-adx × 1 = 6 unique axis representations after iter-v3/014; iter-v3/015 will add the symmetric direction of gate-adx; iter-v3/016+ will need 2 more unique axes (low-vol filter floor, vol-scaling clip range, or ±25% BTC band looser direction).

**iter-v3/014 status**: NOT a CONFIRMATION-bundle candidate. Tighter ADX over-restricted; the [20, 25) trades carried valuable model signal that the model was leveraging downstream. Future CONFIRMATION-bundling QR treats ADX threshold as a baseline gate-tuning decision (current value 20 is structurally near-optimal pending iter-v3/015 looser-direction symmetric validation), NOT as a compoundable iteration ingredient. The 5 caveats from this diary travel with the catalog row to inform future bundling decisions.
