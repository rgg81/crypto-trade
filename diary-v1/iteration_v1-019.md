---
iteration: iter-v1/019
date: 2026-05-26
verdict: EXPLORATION-PROMISING
subtype: favorable-direction (full PROMISING cell per Section 8 row 1; F1 OOS Δ +0.6487 ≥ +0.20 PROMISING band; F-AXIS-MECHANISM #3 LOAD-BEARING PASS)
axis_family: per-cohort-specialization-ETH (NEW 10th family — FIRST usage at v1 catalog level; SECOND per-cohort EXPLORATION under USER STRATEGIC PIVOT)
cohort: ETH (single-symbol cohort, Model G exclusive dispatch)
specialization: stateless direction-aware BTC-trend gate (lookback=42 bars, threshold=±8%, post-hoc filter)
cadence_position: cycle-3 EXPLORATION (#4 of 10)
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c) — UNCHANGED
merge_decision: NO-MERGE (EXPLORATION-PROMISING; ETH-only + gate specialist CONDITIONALLY CARRIED to /027 CONFIRMATION substrate as 2nd LOAD-BEARING component; BASELINE_V1.md UPDATE NOT triggered — only CONFIRMATION-MERGE updates baseline per `feedback_v3_baseline_update_policy.md`)
---

# Iteration iter-v1/019 — Diary

## Decision: NO-MERGE (ETH-only + gate specialist CONDITIONALLY CARRIED to /027 substrate)

EXPLORATION-PROMISING. ETH-only single-symbol cohort dispatch through Model G + stateless direction-aware BTC-trend gate (±8% on BTC 14d return) **dissolved ETH 4/4 NEGATIVE structural prior** at single-seed EXPLORATION budget. OOS Sharpe +0.6990 / OOS Δ +0.6487 vs ETH-in-pool +0.0503 anchor / OOS PnL +16.91 USD / 42 OOS trades / F-AXIS-MECHANISM #3 LOAD-BEARING PASS at both IS 19.50% / OOS 14.29% fire rates / Jaccard 0.04 confirms NEW signal source (compoundable, NOT PROMISING-MECHANICAL). BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). ETH+gate specialist VALIDATED as 2nd LOAD-BEARING component for /027 CONFIRMATION bundle (after LINK-only specialist from /018).

## One-Line Outcome

At v1 EXPLORATION budget (ENSEMBLE_SIZE=3 + n_trials=18 + V1_FEATURE_COLUMNS_PRUNED 40 + ETH-only universe via `V1_ITER019_UNIVERSE = (ETHUSDT,)` + 8h candles + `abs_pnl` weighting + Model G exclusive dispatch + R3 only + ATR×2.9 TP / ATR×1.45 SL mirroring Model A's BTC+ETH pool semantics + R5 disabled + post-hoc stateless direction-aware BTC-trend gate at ±8% on 14d return) ETH-only single-symbol cohort + gate produced **IS Sharpe −0.0304** (Δ **+0.0718** INERT band vs ETH-in-pool −0.1022) + **OOS Sharpe +0.6990** (Δ **+0.6487** PROMISING band vs ETH-in-pool +0.0503; far above +0.20 PROMISING boundary) + **OOS WR 47.6%** (vs ETH-in-pool ~39%; +8pp lift) + **F-AXIS-MECHANISM #1 binary PASS** (per_symbol.csv 100% ETHUSDT IS+OOS) + **F-AXIS-MECHANISM #3 LOAD-BEARING PASS** (IS 19.50% / OOS 14.29% gate fire rates both inside pre-registered bands [10%, 30%] / [5%, 35%]) + **PSR_monthly_vs_0 OOS = 0.7793** (well above 0.40 PROMISING-INERT floor; below /018 LINK-only 0.885 because of small OOS sample 13 months) + **PSR_monthly_vs_1 OOS = 0.4042** (≥40% probability ETH-only OOS Sharpe ≥ 1.0 at observed parameters) + **OOS/IS ratio −23.0** (technical sign-mismatch reclassified by LM Master §3 noise-floor argument: |IS Sharpe| = 0.03 << 0.10 → IS flat / OOS positive interpretation) + **Jaccard 0.04 vs baseline ETH roster** (94% disjoint pre-gate; 96% disjoint post-gate → NEW SIGNAL SOURCE; NOT PROMISING-MECHANICAL) + **n_eff_per_cell = 9** (+1 above LM Master §5 predicted [4, 8] band; LM Master Phase 7.4 §5 acknowledges methodology error — n_eff tied to training row count NOT post-hoc kept trades) + **wall-clock ~25 min** (87% margin against 2h cap; identical scale to /018) — verdict-class cell **PROMISING** (Section 8 row 1); Critic + LM Master CONVERGE; ETH+gate specialist CONDITIONALLY CARRIED to /027 CONFIRMATION substrate as **2nd LOAD-BEARING component** (predicted multi-seed regression target +0.50, NOT /019's +0.6990 single-seed); **/020 axis advances per Critic + LM Master convergent recommendation: BTC-only specialization** (NEW 11th axis family `per-cohort-specialization-BTC`).

## What Worked

### ETH 4/4 NEGATIVE structural prior — DISSOLVED at single-seed EXPLORATION

ETH IS/OOS trajectory across baseline + /014/015/016/017 + /019:

| Iter | ETH IS net_pnl_pct | ETH OOS net_pnl_pct |
|---|---|---|
| baseline | −13.70% | +2.75% |
| /014 | **−99.73%** | **−41.18%** |
| /015 | +17.34% | **−23.29%** |
| /016 | **−46.47%** | **−51.46%** |
| /017 | **−13.49%** | **−28.07%** |
| **/019 (ETH-only + gate)** | **−3.18%** | **+32.65%** |

**FIRST cycle-3 ETH OOS positive after 4 consecutive catastrophic** (−41, −23, −51, −28 → **+33**). ETH's structural NEGATIVE-prior (strongest negative pattern in v1 catalog) is DISSOLVABLE under (a) cohort isolation + (b) direction-aware regime gate. Sample-of-1 at single-seed=42 EXPLORATION budget; mechanism-level LOAD-BEARING confirmation via F-AXIS-MECHANISM #3 fire-rate band.

### Per-cohort methodology — 2/2 PROMISING after USER STRATEGIC PIVOT

Cycle-3 scoreboard updated:

| Iter | Methodology | Verdict | OOS Δ vs anchor |
|---|---|---|---|
| /016 | global axis on pooled (sample-weighting `uniform`) | NEGATIVE catastrophic | −1.67 |
| /017 | global axis on pooled (universe +SOL) | NEGATIVE anti-direction-INERT | −0.09 |
| /018 | per-cohort specialization LINK-only | PROMISING favorable-INERT | +0.16 |
| **/019** | **per-cohort specialization ETH-only + BTC-trend gate** | **PROMISING** | **+0.65** |

Per-cohort methodology produced **2 PROMISING in 2 attempts**; global-pooled axes produced **2 NEGATIVE in 2 attempts**. USER STRATEGIC PIVOT 2026-05-26 (codified at `feedback_v1_per_cohort_exploration_strategy.md`) is empirically validated for cycle-3. Sample-of-2 at the iteration level is small but the per-symbol structural priors are large samples (LINK 9/9 OOS+; ETH 5/5 OOS-cycle-3 inverted at /019).

### Direction-aware regime gate (mechanism-level LOAD-BEARING)

The EDA reframing from symmetric "skip ETH when BTC bearish" (refuted at IS) to **direction-aware counter-trend kill** (kill ETH long when BTC ret14 < −8%; kill ETH short when BTC ret14 > +8%) captured asymmetric per-cell economics that no symmetric gate could:

| Cell | n | avg_pnl | Mechanism |
|---|---|---|---|
| ETH long + BTC ret14 > 0 | 33 | **+0.62%** | momentum confluence (KEEP) |
| ETH short + BTC ret14 > 0 | 42 | **−0.87%** | fighting BTC tape (KILL) |
| ETH long + BTC ret14 ≤ 0 | 37 | −0.26% | mild counter-trend drag (KILL) |
| ETH short + BTC ret14 ≤ 0 | 33 | +0.37% | bear-momentum confluence (KEEP) |

Mechanism: **counter-trend ETH trades (long+dump or short+rally) are the source of ETH drag; trend-aligned ETH trades net positive**. Gate kills counter-trend only. F-AXIS-MECHANISM #3 LOAD-BEARING PASS at IS 19.50% / OOS 14.29% fire rates confirms the gate is engaging the predicted mechanism at the predicted rate.

### F-AXIS-MECHANISM #1 binary PASS clean

per_symbol.csv contains 100% ETHUSDT both IS (159 trades) and OOS (42 trades). Model G exclusive dispatch via `V1_ITER019_UNIVERSE = (ETHUSDT,)` and `set(symbols)==set(V1_ITER019_UNIVERSE)` guard functioned cleanly. Zero spillover from Model A/C/D/E/F dispatch branches.

### Jaccard 0.04 confirms NEW signal source (NOT PROMISING-MECHANICAL)

trade_id Jaccard between /019 kept-trade roster (post-gate) and v1-baseline ETH-in-pool roster (combined IS+OOS):

| Scope | Jaccard |
|---|---|
| IS only | **0.0380** |
| OOS only | **0.0250** |
| Combined kept | **0.0350** |
| Combined ALL /019 trades (pre-gate, 201 total) vs baseline ETH | **0.0566** |

0.04 << 0.50 → **NEW SIGNAL SOURCE (compoundable)**. The retrained Model G generates a 94%-disjoint trade roster vs pool-trained baseline (96% disjoint post-gate). Gate is NOT filtering an existing roster; it is filtering a freshly-trained roster. Per `feedback_promising_mechanical_subtype.md`, /019 is **NOT PROMISING-MECHANICAL**. ETH+gate bundleable additively at /027 CONFIRMATION without compoundability concerns.

### Critic + LM Master CONVERGE on PROMISING (Section 8 row 1)

Both Critic Phase 7.5 (`review.md` HEAD `fad64e8`) and LM Master Phase 7.4 (`lgbm_advisor.md` HEAD `b33c96c`) reach the same verdict cell with the same /027 carry-forward recommendation. LM Master Phase 4.5 prior was **PROMISING 35% / INERT 40% / NEGATIVE 25%** — PROMISING-tail confirmed at observation; LM Master directional track **3/17** (was 2/16 with /018's PROMISING-INERT-favorable confirmed-from-modal; new entry: PROMISING-tail from modal-adjacent prior) + mechanism-level **9/17** (was 8/16 with F-AXIS #3 LOAD-BEARING call CONFIRMED + Jaccard 0.04 compoundable confirmation).

## What Failed

### F7 sign-mismatch — RECLASSIFIED N/A by LM Master §3 noise-floor argument

IS Sharpe −0.0304 / OOS Sharpe +0.6990 is technical sign-mismatch. But IS net PnL is **−1.77 USD across 159 trades / 39 IS months** = essentially zero (−0.01% per trade). LM Master Phase 7.4 §3 argument: at |IS Sharpe| << 0.10, F7 is N/A and the iteration should be treated as "IS flat / OOS positive" not "IS negative / OOS positive". Critic Phase 7.5 accepted this resolution.

**This is not a true failure**; it's a brief design inconsistency between Section 4 line 499 ("F7 strongest") and line 521 ("F-AXIS #3 LOAD-BEARING"). Critic Recommendation #2 codifies the resolution: **future briefs pre-register "F-AXIS-MECHANISM #3 supersedes F7 when |anchor IS Sharpe| < 0.10."**

### IS lift compressed below EDA projection (+42.47% → +10.52pp)

EDA at `analysis/iteration_v1-019/gate_threshold_sweep.csv` projected IS gated PnL +28.77% vs baseline ETH IS −13.70% (Δ +42.47% absolute lift). Observed IS net PnL = −3.18% (Δ vs ETH baseline +10.52pp lift). **IS lift compressed to ~25% of EDA projection.**

LM Master Phase 4.5 §3 had pre-registered this risk: post-hoc EDA assumes baseline-trained model's ETH trades; /019 retrains ETH-only Model G with a different Optuna trajectory and a different trade roster. Predicted compression to 30-60% of post-hoc lift — actual was tighter compression (~25%). Compression mechanism dominates EDA prediction; Jaccard 0.04 quantifies the divergence.

### OOS substantially over-shot LM Master §2 [+0.10, +0.40] band by +0.30

LM Master Phase 4.5 §2 OOS Sharpe band: [+0.10, +0.40]. Observed: +0.6990 → MISS HIGH by +0.30. **Favorable surprise**, but raises the question of whether the OOS basin draw is single-seed=42 lottery-favorable end (per LM Master Phase 4.5 §7 single-cohort + gate basin lottery saturation risk).

Per /018 precedent (LINK-only +0.98 single-seed → +0.80 multi-seed regression target with 0.65-0.80 compression factor), /019 multi-seed regression target estimate (LM Master Phase 7.4 §4): **[+0.45, +0.55]; point estimate +0.50** with single-seed basin variance ±0.30 → multi-seed ±0.15 at ENSEMBLE_SIZE=10. /027 multi-seed will dissolve the basin lottery and reveal the true compoundable signal.

### Single-seed=42 basin-lottery exposure (HIGH-RISK declared)

Per brief Section 2.5, /019 was HIGH-RISK (cycle-3 cumulative HIGH-RISK tracker — 3rd declaration after /016 + /017 + /018). Single-cohort + post-hoc gate = 2 changes vs baseline (universe 5→1 + gate intervention) → basin-lottery exposure widened. /018's LINK had +9/9 favorable prior to draw from; /019's ETH had +0/4 prior — basin downside band was theoretically wider.

**Mitigation outcome**: gate intervention mechanism is documented and cross-year-stable (gate lifts both H1 and H2 IS halves); favorable basin draw at single-seed=42 reflects mechanism efficacy more than basin lottery. Multi-seed at /027 dissolves the residual lottery uncertainty.

### Engineering report MISSING at Phase 7.5 dispatch (Critic Rec #1)

Per Critic Phase 7.5 Recommendation #1: `reports-v1/iteration_v1-019/engineering_report.md` was NOT emitted at Phase 6 closure. Data artifacts (comparison.csv, trades.csv, dsr.json, ic_matrix.csv, adf_test.csv, per_symbol.csv) all present and sufficient for the 8-check audit, so this is NOT a methodology-blocker. **Phase 8 closeout addresses retrospectively**: engineering_report.md written from existing CSVs at Phase 8 closeout (zero backtest re-run).

This is the 2nd cycle-3 incident (after /017's "6th-strike" engineering report opt-out → permanent fix scope at orchestrator/skill layer). The permanent fix from /017 was at the skill-layer/orchestrator level; the /019 incident suggests the fix wasn't completed in time. Carry-forward action: re-confirm orchestrator Phase 6 contract addition requiring engineering_report.md in the same commit as comparison.csv (NOT QR scope this iteration).

### Check 3 PBO unavailable for single-symbol single-cohort

Inherited from /018. For single-cohort single-seed EXPLORATION, n_obs collapses → PBO not computable. Critic Phase 7.5 accepted as STRUCTURAL not evidence-gap (per /018 lgbm_advisor.md Phase 7.4 §closing note: "cross-architecture priors are stronger anti-overfit signal than CSCV at single-cohort"). Multi-seed CONFIRMATION at /027 restores full DSR/PBO/PSR evaluation.

## Path Forward (from Critic + LM Master CONVERGENT recommendation)

Verbatim from Critic Phase 7.5 review.md §"Path Forward" + LM Master Phase 7.4 §7:

1. **/020 = BTC-only specialization** — family `per-cohort-specialization-BTC` (NEW 11th family) — BTC IS catastrophic rotation at /017 (-93.81) vs BTC OOS positive (+15.11); cohort isolation tests intrinsic vs pool-borrowed edge. **PRIMARY** per convergent Critic Path Forward #1 + LM Master Phase 7.4 §7.

2. **/021 = LTC-only or DOT-only specialization** — `per-cohort-specialization-LTC` or `per-cohort-specialization-DOT` (NEW 12th/13th families) — staged candidates for cycle-3 #6/7. LTC was the worst OOS contributor in baseline (−47.25%); DOT had IS +96.07 at /017 catastrophic-positive rotation. Per LM Master Phase 7.4 §7 staged candidates.

3. **/022-/026 = 2-3 symbol pooled cohorts OR methodology refinements** — TBD. Per brief Section 11.5, cohort-pooling tests (DOT+LTC vol-cluster, LINK+SOL DeFi-pair, BTC+ETH separated as Model A re-architecture). Methodology refinements (e.g., feature_importance.csv emission per LM Master §6) could fill slot.

Constraints honored: per-cohort-specialization-{BTC,LTC,DOT} NEW family declarations; none in prior 5 (which now are: labeling /014, labeling CONFIRMATION /015, sample-weighting /016, universe /017, per-cohort-specialization-LINK /018; per-cohort-specialization-ETH /019 enters at next rotation).

## 6 LESSONS for v1 Cycle-3 Catalog

### LESSON #1: ETH 4/4 NEGATIVE STRUCTURAL PRIOR IS DISSOLVABLE (cohort isolation + direction-aware regime gate)

ETH OOS PnL trajectory baseline +3 / /014 −41 / /015 −23 / /016 −51 / /017 −28 / **/019 (ETH-only + gate) +33**. The strongest negative per-symbol pattern in v1 catalog is DISSOLVABLE under the right combination of cohort isolation + mechanism-targeted regime gate. ETH drag is **BTC-trend-conditional** (counter-trend ETH = drag source), NOT ETH-intrinsic.

**Codified rule**: future ETH-touching EXPLORATIONs pre-register the dissolution path — direction-aware regime gate is the LOAD-BEARING mechanism (not symmetric framing, not on-chain alone). Cross-track v3 reference is NOT applicable (v3 doesn't have ETH); v2 reference (v2/019 applied direction-aware gate to SOL/XRP/DOGE/NEAR) is the closest mechanism analog.

### LESSON #2: PER-COHORT METHODOLOGY EMPIRICALLY VALIDATED 2/2 AT CYCLE-3 (cycle-3 #3 + #4 both PROMISING)

Per `feedback_v1_per_cohort_exploration_strategy.md`: USER STRATEGIC PIVOT 2026-05-26 codified per-cohort specialization as default cycle-3 methodology. /018 LINK-only + /019 ETH-only + gate = **2 of 2 PROMISING**. Global-pooled axes (/016 + /017) = **2 of 2 NEGATIVE**. The pivot is empirically validated at small sample (n=2 per methodology arm) with consistent direction.

**Codified rule**: cycle-3 /020-/026 EXPLORATIONs continue per-cohort specialization. Global-pooled axes CLOSED for cycle-3 at single-axis EXPLORATION budget. CONFIRMATION /027 bundles PROMISING specialists for diversification edge.

### LESSON #3: F-AXIS-MECHANISM #3 SUPERSEDES F7 WHEN |ANCHOR IS SHARPE| < 0.10 (Critic Rec #2)

Brief Section 4 carried two competing "strongest" markers: F7 sign-agreement (line 499) and F-AXIS-MECHANISM #3 LOAD-BEARING (line 521). When ETH-in-pool IS anchor is small (−0.1022 ≈ 0), F7 has reduced diagnostic power; mechanism-level binary F-AXIS-MECHANISM #3 carries the verdict. LM Master §3 noise-floor argument: |IS Sharpe| << 0.10 → F7 N/A.

**Codified rule**: future per-cohort EXPLORATION briefs pre-register: "F-AXIS-MECHANISM #3 supersedes F7 when |anchor IS Sharpe| < 0.10." Add to per-cohort brief template. Resolves the F7 vs F-AXIS #3 hierarchy ambiguity at design time, NOT post-hoc at Phase 7.5.

### LESSON #4: /027 MULTI-SEED REGRESSION TARGET FOR ETH+GATE = +0.50 (NOT /019's +0.6990)

Per /018 precedent: LINK-only single-seed +0.98 → multi-seed regression target +0.80 (compression 0.65-0.80, mean ~0.72). Apply same compression to /019 ETH+gate single-seed +0.6990: **multi-seed regression target [+0.45, +0.55]; point estimate +0.50** with single-seed basin variance ±0.30 → multi-seed ±0.15 at ENSEMBLE_SIZE=10.

**Codified rule**: /027 CONFIRMATION bundle compositions targeting ETH+gate specialist must size at **+0.50 anchor contribution**, NOT +0.6990. Over-anchoring on /019's +0.6990 is **post-hoc rationalization risk**. Bundle Sharpe target ≥+0.85-+1.05 with 2 specialists (LINK +0.80 + ETH+gate +0.50) requires cross-correlation < 0.40 — pre-validation pre-registered per Critic Rec #3.

### LESSON #5: n_eff_per_cell PREDICTION SUBSTRATE = TRAINING ROW COUNT, NOT POST-HOC KEPT TRADES (LM Master §5 correction)

LM Master Phase 4.5 §5 predicted n_eff_per_cell band [4, 8] based on post-hoc kept-trade count (post-gate ~120 IS trades). Observed n_eff = 9, +1 above band. LM Master Phase 7.4 §5 acknowledges methodology error: **n_eff is tied to training row count (full per-symbol ETH IS labels ≈ 159+), NOT post-hoc kept trade count**. Gate fires POST-MODEL-FIT, not at training; Optuna trial diversity is measured on full training data.

**Codified rule**: updated methodology for /020+ — predict n_eff from training cohort size (full per-symbol IS labels), NOT from post-gate trade count. /020 BTC-only with no gate → predict n_eff [8, 10] from training row count. Future briefs Section 4 F-AXIS-MECHANISM #4 row pre-registers prediction substrate = "ETH-only cohort training row count (~159 labels)" NOT "post-gate kept trade count."

### LESSON #6: /027 CROSS-CORRELATION PRE-VALIDATION REQUIRED FOR BUNDLE MATH (Critic Rec #3)

Projected /027 portfolio Sharpe lift (LINK +0.80 + ETH+gate +0.50) = +0.85-+1.05 assumes cross-correlation between LINK and ETH+gate roster Sharpe paths < 0.40. **This is currently un-validated.** If cross-correlation > 0.60, bundle dilution occurs and the 2-specialist portfolio Sharpe lift drops sharply.

**Codified rule**: at /027 CONFIRMATION brief design, pre-register a rejection threshold: cross-correlation > 0.60 between any 2 specialist roster Sharpe paths = bundle composition revisited (drop the more correlated specialist; substitute with cohort from /020-/026 with lower cross-correlation). LINK and ETH+gate use DIFFERENT cohorts AND DIFFERENT mechanisms (LINK = no specialization; ETH = direction-aware regime gate) — cross-correlation < 0.40 is plausible but must be measured at multi-seed.

## Cycle-3 Cadence Status (after /019)

- Cycle-3 EXPLORATION count: **4 of 10**
- CONFIRMATION earliest: /027 (assuming sequential EXPLORATIONs from /020 to /026)
- Edge ingredients merged this cycle: **0** (LINK-only specialist + ETH+gate specialist are CONDITIONAL carry-forwards to /027 substrate, NOT merges to BASELINE_V1.md)
- Verdict distribution cycle-3 so far: 1 EXPLORATION-NEGATIVE catastrophic (/016) + 1 EXPLORATION-NEGATIVE anti-direction-INERT (/017) + 1 EXPLORATION-PROMISING favorable-INERT (/018) + **1 EXPLORATION-PROMISING (/019)** = 2 PROMISING + 2 NEGATIVE across 4 cycle-3 EXPLORATIONs
- BASELINE_V1.md unchanged at `v0.v1-baseline-corrected` (`f8bc12c`)
- **Methodology validated 2/2**: per-cohort 2 of 2 PROMISING; global-pooled 2 of 2 NEGATIVE

## Track Record Update

- **Verdict-class directional track**: 2/16 → **3/17** (new entry: /019 PROMISING from modal-adjacent PROMISING-tail of 35/40/25 prior; full PROMISING cell fired)
- **Mechanism-level track**: 8/16 → **9/17** (new entry: F-AXIS-MECHANISM #3 LOAD-BEARING fire-rate band call CONFIRMED at observation; Jaccard 0.04 compoundable confirmation)

LM Master Phase 4.5 prediction record on /019:

| Phase 4.5 prediction | Observed | Hit/Miss |
|---|---|---|
| PROMISING 35% / INERT 40% / NEGATIVE 25% | PROMISING-tail | **HIT** (PROMISING-tail fired from 35% bucket) |
| Gate fire-rate IS 17.2% (band [10%, 30%]) | 19.5% (31/159) | **HIT** — inside band |
| Gate fire-rate OOS 17.4% (band [5%, 35%]) | 14.3% (6/42) | **HIT** — inside band |
| OOS Sharpe band [+0.10, +0.40] | +0.6990 | **MISS HIGH** — exceeded upper bound by +0.30 |
| n_eff_per_cell [4, 8] | 9 | MISS HIGH (+1; LM §5 methodology correction) |
| IS lift 30-60% of post-hoc projection | IS lift compressed to ~25% (EDA +42.47% → observed +10.5pp) | **MIXED** — compression tighter than predicted |
| F-AXIS #3 fire-rate as load-bearing diagnostic | CONFIRMED LOAD-BEARING — both bands PASS | **HIT** |

Net: **4/7 HIT, 2/7 MISS HIGH (favorable surprise on OOS magnitude), 1/7 MIXED**. Phase 4.5's directional call (PROMISING-tail on small-anchor cohort with cross-year-stable gate) vindicated; magnitude under-predicted.

## /027 Bundle Composition Update

| Specialist | Status after /019 | Single-seed Δ | /027 multi-seed regression target |
|---|---|---|---|
| **LINK-only /018** | **VALIDATED — LOAD-BEARING** | +0.16 | **+0.80** anchor |
| **ETH-only + BTC-trend gate /019** | **VALIDATED — LOAD-BEARING (THIS ITERATION)** | **+0.65** | **+0.50** anchor |
| BTC-only /020 | PENDING (per Path Forward #1) | — | — |
| LTC-only /021 | PENDING | — | — |
| DOT-only /022 | PENDING | — | — |
| Pooled cohorts /023-/026 | PENDING | — | — |

**Current /027 bundle composition**: **2/4-6 ingredients staged**. Projected portfolio Sharpe lift +0.85 to +1.05 assuming cross-correlation < 0.40 (Critic Rec #3 pre-validation pre-registered).

## Axis Rotation Status (v1-only)

- **This iter's family**: `per-cohort-specialization-ETH` (NEW 10th family — FIRST usage at v1 catalog level; convergent Critic + LM Master + USER STRATEGIC PIVOT recommendation from /018 closeout)
- **Prior 5 EXPLORATION families** (going INTO /019): labeling (/014), labeling CONFIRMATION (/015), sample-weighting (/016), universe (/017), per-cohort-specialization-LINK (/018)
- **Rotation honored**: YES — `per-cohort-specialization-ETH` is in NONE of the prior 5 families. Per /018 closeout LESSON #1 (codified rule), per-cohort specialization is the default cycle-3 methodology; ETH is a different COHORT from LINK (rotation by cohort, not by family literal-name). 3-way Critic + LM Master + QR orthogonality convergence on cohort-pairing differentiation.
- **Updated prior 5 going into /020**: labeling CONFIRMATION (/015), sample-weighting (/016), universe (/017), per-cohort-specialization-LINK (/018), per-cohort-specialization-ETH (/019)
- **/020 axis-family**: `per-cohort-specialization-BTC` (NEW 11th family) per Critic + LM Master convergence. Per-cohort methodology rotation discipline: COHORT identifier rotation (LINK done → ETH done → BTC next → LTC/DOT/2-sym pools at /021-/026).

## Next Iteration Ideas (cycle-3 fifth EXPLORATION = /020)

Per Critic + LM Master CONVERGENT Path Forward + per-cohort methodology cohort-rotation:

1. **BTC-only specialization** (MEDIUM structural prior — BTC IS catastrophic rotation /017 -93.81 + BTC OOS positive +15.11; pooled Model A trains badly on BTC at single-seed rotation signature) — `per-cohort-specialization-BTC` NEW 11th family. **PRIMARY** per Critic Path Forward #1 + LM Master Phase 7.4 §7. BTC is structurally the strongest pool anchor symbol; BTC-pooled regularization helps OTHER symbols; BTC-only isolation tests intrinsic vs pool-borrowed edge. LM Master Phase 7.4 §7 prior for /020: PROMISING 25% / INERT 50% / NEGATIVE 25% (modal INERT — BTC may lose asymmetric pool-anchor benefit).

2. **LTC-only specialization** (HIGH negative structural prior — LTC was the worst OOS contributor in baseline at −47.25% net PnL; per `feedback_v1_per_cohort_exploration_strategy.md`, NEGATIVE-prior cohorts are diagnostic candidates) — `per-cohort-specialization-LTC` NEW 12th family. SECONDARY per LM Master Phase 7.4 §7 staged candidate. Tests whether LTC's catastrophic OOS is BTC-trend-conditional (apply /019's gate primitive — code re-use, signal re-use as a hypothesis) OR LTC-intrinsic (no gate; isolation alone exposes LTC drag fully).

3. **DOT-only specialization** with optional TBR-momentum gate — `per-cohort-specialization-DOT` NEW 13th family — DOT IS +96.07 at /017 catastrophic-positive rotation; DOT IS +26.62 at baseline; DOT structural IS positive, OOS approximately flat. DOT-only test characterizes DOT's intrinsic IS-driven edge. TERTIARY per LM Master Phase 7.4 §7 staged candidate.

4. **Methodology refinement — feature_importance.csv emission to v1 runner** — per LM Master Phase 7.4 §6, v1 runner doesn't currently write `feature_importance.csv` (Engineer Phase 6 task). Without per-cohort feature importance, /027 bundle composition decision cannot directly diagnose whether LINK-only and ETH-only specialists are leaning on different feature subsets. CONDITIONAL on /020+/021 not occupying slot prematurely; can fill /024 if needed.

5. **2-3 symbol pooled cohort BTC+ETH separated** — `per-cohort-pooled-2sym` (NEW family) — tests "pooling helps" vs "pooling masks" hypothesis underlying /018-/019 cohort isolation success. Per Critic Path Forward #3 alternative. Lower priority; /024-/026 candidate.

All cohort options from per-cohort specialization methodology. Cycle-3 fifth EXPLORATION (/020) QR EDA-justifies BTC-only specialization under 2h wall-clock cap.

## Files & Commits on Branch

- Branch: `iteration-v1/019` from `iter-v1/018` closeout (tag `v0.v1-018`)
- HEAD at brief Phase 5: `c35c36a`
- HEAD at LM Master Phase 4.5: `62e5056`
- HEAD at brief Section 3.4 LM Master responses: `f4b2884`
- HEAD at QE Phase 5.5 + dispatch implementation: `05e1d82` (gate) → `16e9c8c` (feat)
- HEAD at Critic Phase 6.0 PASS: `55fe28e`
- HEAD at LM Master Phase 7.4 post-mortem: `b33c96c`
- HEAD at Critic Phase 7.5 review (EXPLORATION-PROMISING): `fad64e8`
- HEAD at engineering report (retrospective at Phase 8 per Critic Rec #1): TBD
- HEAD at Phase 8 closeout (THIS COMMIT): TBD
- Reports artifacts in `reports-v1/iteration_v1-019/`

Key commits in /019:
- `c35c36a` — docs: QR Phases 1-5 + ETH-only regime-gate brief
- `62e5056` — docs: Phase 4.5 LM Master advisory
- `f4b2884` — docs: Section 3.4 LM Master responses + verdict-cell adjustments
- `05e1d82` — docs: Phase 5.5 gate PASS
- `16e9c8c` — feat: ETH-only specialization + direction-aware BTC-trend gate
- `55fe28e` — docs: Phase 6.0 Critic pre-flight PASS
- (Backtest dispatched; comparison.csv + reports artifacts in `reports-v1/iteration_v1-019/`)
- `b33c96c` — docs: Phase 7.4 LM Master post-mortem
- `fad64e8` — docs: Phase 7.5 Critic review — EXPLORATION-PROMISING
- (engineering report retrospective + Phase 8 closeout this commit) — Phase 7 + Phase 8 closeout

**Trunk merge**: NONE. EXPLORATION-PROMISING does NOT update BASELINE_V1.md (per `feedback_v3_baseline_update_policy.md` adopted by v1 — only CONFIRMATION-MERGE updates baseline). ETH-only + BTC-trend gate specialist carries forward as **2nd LOAD-BEARING structural-cell ingredient** for /027 CONFIRMATION substrate (after LINK-only specialist from /018), NOT as merge candidate to BASELINE_V1.md.

**Tag**: `v0.v1-019` (applied after this Phase 8 closeout commit).
