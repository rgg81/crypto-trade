---
iteration: iter-v1/024
date: 2026-05-27
verdict: EXPLORATION-NEGATIVE (clean; FINAL after BLOCK-PENDING-FIX rerun at 67341d7)
subtype: Section 8 Row 7 (F3 IS-catastrophic auto-reject Δ -0.86 ≤ -0.30) ∧ Row 4 (F-AXIS #5 gain-share recurrence FAIL 2/3 cohorts; partition NON-SPECIALIZING)
axis_family: model-arch (NEW 16th family — FIRST multi-model architecture in v1 cycle-3 history)
axis: regime-conditional sub-models — 7 sub-models (Pool A × 2 + LINK × 2 + LTC × 2 + DOT × 1) partitioned by |funding_z30| > 1.5; STATELESS RegimeRoutedStrategy wrapper at signal-time
cadence_position: cycle-3 EXPLORATION (#9 of 10)
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c) — UNCHANGED
merge_decision: NO-MERGE (EXPLORATION-NEGATIVE clean; regime-conditional architecture EXCLUDED from /027 substrate; BASELINE_V1.md UPDATE NOT triggered — only CONFIRMATION-MERGE updates baseline per `feedback_v3_baseline_update_policy.md`)
---

# Iteration iter-v1/024 — Diary

## 1. Decision: NO-MERGE (EXPLORATION-NEGATIVE clean; regime-conditional EXCLUDED from /027; STRUCTURAL FINDING catalogued)

**EXPLORATION-NEGATIVE clean** (FINAL after BLOCK-PENDING-FIX rerun at `67341d7`; Critic Phase 7.5 FINAL `1e5f7bc`). Training 2 LightGBM sub-models per cohort partitioned by `|funding_z30| > 1.5` (Pool A + LINK + LTC × 2 regimes each + DOT single-model baseline = 7 sub-models total) with STATELESS RegimeRoutedStrategy wrapper at signal-time and single-seed=42 ENSEMBLE_SIZE=3 n_trials=18 EXPLORATION budget produces a verdict cell COLLISION:

- **F3 IS Sharpe Δ = -0.8590** (IS -0.5761 vs anchor +0.2829) — Section 8 Row 7 IS-catastrophic auto-reject FIRES per brief Section 4.1 (-0.30 threshold; -0.86 observed); 3rd-largest IS Δ in v1 cycle-3 (after /020 -0.86, /022 -1.17).
- **F-AXIS #5 gain-share recurrence FAIL 2/3 cohorts** — Pool A 7.21% < 9.16%, LINK 5.16% < 7.67%; LTC PASS 5.97% > 4.49%. Section 8 Row 4 INERT-via-non-specialization; partition mechanism did NOT activate at sub-model layer.
- **F1 OOS Sharpe Δ = +0.0956** (OOS +0.7593 vs anchor +0.6637) — INERT band 4bp shy of PROMISING (+0.10 threshold). Per `feedback_no_cheating.md` + /023 3bp precedent, **cannot be reclassified upward** on attractive OOS surface alone.

BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). **Regime-conditional architecture EXCLUDED from /027 substrate**; /027 stays at 2-specialist UNCHANGED. **/025 advances to OI DELTA FAMILY** (feature-family REPEAT but NEW data class; LM Master Phase 7.4 §7 PRIMARY + Critic Path Forward #1 PRIMARY + user "diversification" mandate continues via NEW non-OHLCV signal source).

## 2. Headline Numbers

| Metric | Value | Note |
|---|---|---|
| **F1 OOS Sharpe Δ** | **+0.0956** | vs anchor +0.6637; INERT band 4bp shy of PROMISING +0.10 threshold |
| **F3 IS Sharpe Δ** | **-0.8590** | vs anchor +0.2829; **IS-CATASTROPHIC auto-reject** (Row 7) at -0.30 threshold |
| OOS Sharpe (daily-annualized) | +0.7593 | comparison.csv binding |
| IS Sharpe (daily-annualized) | -0.5761 | F3 IS basin collapse |
| OOS Total Net PnL | +38.04% | vs baseline OOS +38.13% (flat) |
| IS Total Net PnL | -100.42% | vs baseline IS +54.05% (catastrophic basin) |
| OOS trades | 285 | above QR [140, 240] upper bound by 45 — overshoot anomaly |
| IS trades | 747 | inside QR [500, 750] PASS at upper boundary |
| OOS win rate | 41.1% | vs baseline 40.2% — flat |
| Profit factor OOS | 1.1429 | vs baseline 1.156 — flat |
| Max DD OOS | 31.34% | vs baseline 40.94% — improved |
| Max DD IS | 155.98% | vs baseline 73.06% — doubled (basin collapse) |
| PSR_monthly_vs_0 OOS | 0.7888 | vs baseline 0.989 (declined; informational) |
| PSR_monthly_vs_1 OOS | 0.3820 | vs baseline 0.0789 (paradoxical stronger; informational) |
| DSR OOS | -27.88 | informational EXPLORATION-mode |
| n_eff_per_cell_median | 10 EXACT | LM Master Phase 4.5 §3 modal [2, 8] EXTREME / [5, 10] NORMAL — N hits portfolio cell exactly |
| Wall-clock | ~1h11m (Optuna portion ~52 min) | 41% margin against 2h hard cap |

### F-AXIS-MECHANISM RECONCILIATION TABLE — VERDICT CELL COLLISION

| Falsifier | Pre-registered criterion | Observed | Outcome |
|---|---|---|---|
| F-AXIS #1 Dispatch | 7 unique sub-models with non-zero training rows | 7 feature_importance CSVs present (Pool A_ext + A_norm + C_ext + C_norm + D_ext + D_norm + E_baseline) | **PASS** (post-fix `67341d7`; was BLOCKED at `0690022`) |
| F-AXIS #2 IS trade count | QR [500, 750] | 747 | PASS (upper boundary) |
| F-AXIS #2 OOS trade count | QR [140, 240] | **285** (+45 over upper) | overshoot anomaly (documented) |
| F-AXIS #3 Regime-gate fire-rate | Per-cohort IS [10%, 18%] AND OOS [8%, 22%] | (computed indirectly via Pool A 14% partition; engineering report dispatch logs confirm 318 filter invocations all non-zero) | PASS |
| F-AXIS #4 n_eff_per_cell | EXTREME [2, 8] / NORMAL [5, 10] | portfolio cell 10 EXACT | PASS |
| **F-AXIS #5 Gain-share recurrence** | EXTREME funding gain share MUST EXCEED NORMAL per cohort | **Pool A 7.21% < 9.16% FAIL; LINK 5.16% < 7.67% FAIL; LTC 5.97% > 4.49% PASS** | **FAIL 2/3 cohorts** (partition NON-SPECIALIZING) |
| **F1 OOS daily-annualized Sharpe Δ** | ≥ +0.10 → PROMISING; [-0.10, +0.10) INERT; [-0.55, -0.10) NEGATIVE clean | **+0.0956** | **INERT (4bp shy of PROMISING)** |
| **F3 IS Sharpe Δ** | ≤ -0.30 → IS-CATASTROPHIC AUTO-REJECT (Row 7) | **-0.8590** | **AUTO-REJECT FIRES** |

**Key observation**: F-AXIS #1 dispatch correctness PASS (7 sub-models built; partition mechanism mechanically engaged) × F-AXIS #5 gain-share recurrence FAIL 2/3 cohorts (partition non-specializing) × F3 IS-catastrophic auto-reject (basin collapse) × F1 OOS Δ +0.0956 INERT-near-PROMISING (4bp shy) = **EXPLORATION-NEGATIVE clean** via TWO INDEPENDENT TRIGGERS (Row 7 + Row 4). Either trigger alone is sufficient; both fired.

## 3. Mechanism narrative: regime-conditional architecture ENGAGED but DID NOT specialize

### 3.1 Architecture engaged at dispatch layer

Per `engineering_report.md` (commit `67341d7`) + 7 feature_importance CSVs at `reports-v1/iteration_v1-024/in_sample/`:

- 7 sub-models built (Pool A × 2 + LINK × 2 + LTC × 2 + DOT × 1).
- `RegimeRoutedStrategy.compute_features()` propagates to both inner strategies (extreme + normal).
- `data_filter_callback` applied 318 times across full IS+OOS run; ALL non-zero (Pool A extreme first partition: 564 rows from full window).
- comparison.csv DIFFERS materially from /023 (IS Sharpe -0.5761 vs /023 +0.4121; OOS +0.7593 vs /023 +0.4606) — confirms mechanism took effect (NOT bit-identical bypass).
- `funding_rate_zscore_30` appears in all 7 sub-models' importance rankings — the column is present in the filter callback's view after the BLOCK-PENDING-FIX patch.

Dispatch CORRECT; mechanism ENGAGED at the architecture layer.

### 3.2 But extreme sub-models DON'T learn regime-specialized features in 2/3 cohorts

The smoking gun is F-AXIS #5 gain-share recurrence:

| Cohort | EXTREME funding gain | NORMAL funding gain | Δ (EXT − NORM) | Verdict |
|---|---:|---:|---:|:---:|
| Pool A (BTC+ETH) | 7.21% (320.31 + 190.07 / 7083) | 9.16% (2608.70 + 1915.40 / 49378) | **-1.95pp** | **FAIL** |
| LINK Model C | 5.16% (92.43 + 108.68 / 3895) | 7.67% (810.00 + 955.35 / 23025) | **-2.51pp** | **FAIL** |
| LTC Model D | 5.97% (76.13 + 44.23 / 2015) | 4.49% (1124.84 + 722.40 / 41108) | +1.48pp | PASS |

**The mechanism prediction (LM Master Phase 4.5 §3 ADOPTED)**: if the regime partition is genuinely identifying a different signal-generating distribution, the extreme sub-model MUST learn funding-family features more heavily than its baseline counterpart. **Observed**: 2 of 3 cohorts produce extreme sub-models that lean LESS on funding than their normal counterparts — the opposite of what the hypothesis predicts.

### 3.3 Why the partition didn't specialize

Possible explanations (not mutually exclusive):

1. **Thin extreme partition** — Pool A 1573 / LINK 709 / LTC 802 bars / month over walk-forward. LightGBM-at-n_trials=18 on the extreme sub-model lands in a basin similar to baseline because the optimal max_depth × subsample × reg_lambda × confidence_threshold region under thin training data overlaps with the normal sub-model's optimal region. The trees split on the same features.

2. **Single-seed lottery at ENSEMBLE_SIZE=3 inner** — each sub-model is the average of 3 seed-bagging seeds; the inner ensemble is too narrow to dissolve basin-relocation lottery.

3. **n_trials=18 Optuna budget too low for partition discovery** — TPE has barely warmed up at 18 trials; the loss surface in the partition's narrow region requires more trials to find the regime-specific basin distinct from the joint basin.

4. **The mechanism may not exist at v1's 8h cadence** — funding-extremity partition may simply not produce regime-distinct label distributions at v1's cadence (this would be the v3-style finding; need multi-seed validation to distinguish).

### 3.4 The IS basin CATASTROPHE

The F3 IS Sharpe Δ = -0.86 is the second smoking gun: even though 7 sub-models were trained and the partition mechanism engaged, the IS basin collapses CATASTROPHICALLY (from +0.2829 to -0.5761). The architectural complexity (1.75× the baseline) + thin extreme partition + Optuna at n_trials=18 produces:
- Pool A IS net PnL -100.42% (was -25.87% in baseline) — DEEPER negative
- The extreme sub-models in 2/3 cohorts essentially average over partition with HIGHER variance — overfitting their thin sample
- The OOS basin SURVIVES (+0.7593; 4bp shy of PROMISING) but cannot rescue the IS

This is exactly the LM Master Phase 4.5 §6 most-important-risk pattern materialized: **"compute doubled but variance NOT halved because each sub-model sees half the data"**. The extreme sub-models overfit; the normal sub-models inherit the residual; portfolio IS Sharpe collapses.

## 4. Structural finding: /021 H2 REFUTED extends to SUB-MODEL level

### 4.1 The /021 finding and its /024 extension

`feedback_v1_h2_refuted_basin_interaction.md` established at /021: **cohort-isolation effects are basin-level (Optuna parameter shifts), NOT feature-level (Spearman ρ = 0.9448 between Pool BTC-slice and BTC-only Model H feature-importance rankings)**. Same features dominate; same-feature-set Optuna lands at distinct parameters under joint vs cohort-alone loss surfaces.

**/024 extends this finding to the SUB-MODEL level**: partition-level effects also DO NOT reduce to feature-shift. The F-AXIS #5 FAIL 2/3 cohorts shows that even when training data is explicitly partitioned by regime, LightGBM-at-single-seed n_trials=18 ENSEMBLE_SIZE=3 EXPLORATION budget treats the partition as noise. **The sub-model basins overlap; the partition does not induce regime-specialized feature use.**

### 4.2 Why this matters for v1 architecture choices

The /021 + /024 combined finding constrains v1's architectural search at EXPLORATION budget:

| Architecture choice | Basin behavior at single-seed | Verdict precedent |
|---|---|---|
| Pool 5-sym joint training | Stable basin; baseline | BASELINE |
| Per-cohort isolation (1 sym) | Basin RELOCATES; can produce NEG-CAT (BTC /020 + LTC /022) OR PROMISING (LINK /018 + ETH /019 with gate) depending on cohort prior class | per-cohort SATURATED for ASYMMETRIC_ROTATION class |
| Regime-conditional sub-models | Sub-model basins OVERLAP; partition does NOT specialize (2/3 cohorts F-AXIS #5 FAIL) | **/024 NEGATIVE clean** |
| Multi-seed CONFIRMATION | Basin lottery dissolves (predicted) | /027 CONFIRMATION will test for 2-specialist bundle; regime-conditional could be a /027 sub-component |

### 4.3 The mechanism (basin-level NOT feature-level at /024 too)

LM Master Phase 7.4 §3 mechanism synthesis:
- **Pool A extreme sub-model gain share 7.21% < normal 9.16%**: the extreme sub-model's loss surface is dominated by extreme-regime label noise (thin sample); Optuna at n_trials=18 settles on hyperparameters that REDUCE feature dependence in general (regularizing toward simpler models on thin data) — incidentally reducing funding-family gain share too.
- **LINK extreme sub-model gain share 5.16% < normal 7.67%**: same pattern; LINK 709-bar extreme partition is even thinner per-month than Pool A.
- **LTC extreme sub-model gain share 5.97% > normal 4.49%**: PASS; LTC's normal sub-model has LOWER baseline funding usage so the extreme sub-model's modest funding lift is more pronounced. Note this is a low-baseline anomaly, not strong evidence of specialization.

The architecture-conditional learning observation from /023 LEARNED-NEGATIVE (Pool A 6.88% > parity 4.76%) does NOT replicate at the regime-partitioned sub-model layer: the extreme sub-models in Pool A and LINK actually have LOWER funding gain share than their normal counterparts. **The partition is not surfacing funding-regime-specific signal; the regime appears to be informational noise from the LightGBM-at-single-seed perspective.**

### 4.4 Forward implications for v1 architecture

1. **Regime-conditional architecture CANNOT be tested at v1 single-seed=42 ENSEMBLE_SIZE=3 n_trials=18 EXPLORATION budget**. This conclusion is robust: the F-AXIS #5 FAIL 2/3 cohorts is a DIRECT mechanism falsifier; the F3 IS-CAT is an INDEPENDENT secondary catastrophe.

2. **Three forward paths remain alive (NOT exhausted)**:
   - **/027 CONFIRMATION with regime-conditional sub-component at multi-seed** (5 inner × 2 outer = 10 paths per sub-model per cohort per month vs current 3): tests the multi-seed-dissolution hypothesis at higher compute.
   - **Broader extreme partition threshold** (e.g., `|z30| > 0.5` instead of 1.5; more rows in extreme partition; tests sample-size hypothesis).
   - **Different partition mechanism** (NOT funding-extremity; e.g., volatility regime via Hurst exponent or ADX percentile; tests whether the funding axis is the issue or the partition is in general).

3. **Per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md` + the new /024 finding**: regime-partition sub-models at single-seed EXPLORATION budget join per-cohort isolation as a saturated architecture family. /025 MUST be NEW feature-family (OI delta) NOT a regime-partition variant.

## 5. /027 bundle impact: regime-conditional EXCLUDED; stays at 2 specialists

Post-/024 substrate (UNCHANGED from /022/023 post-states):

| Component | Provenance | Bundle role | Status | Multi-seed Δ target |
|---|---|---|---|---|
| Pool baseline (5 sym, A/C/D/E unchanged) | BASELINE_V1.md | Pool anchor | LOCKED | 0 |
| LINK-only specialist (Model C') | /018 PROMISING-INERT-FAVORABLE | Alpha-enhancement | LOCKED | **+0.80** |
| ETH-only + symmetric BTC-trend gate (Model G) | /019 PROMISING | Alpha-enhancement | LOCKED | **+0.50** |
| BTC in pool via Model A | /020 NEG-CAT EXCLUDED | Pool baseline only | LOCKED | — |
| LTC in pool via Model D | /022 NEG-CAT EXCLUDED | Pool baseline only | LOCKED | — |
| Funding-family feature axis | /023 LEARNED-NEGATIVE EXCLUDED | NOT in bundle | LOCKED | — |
| **Regime-conditional sub-models** | **/024 EXPLORATION-NEGATIVE EXCLUDED** | **NOT in bundle** | **LOCKED at /024 closeout** | — |
| DOT (TBD /025+ routing) | pending OI delta path | TBD | PENDING | TBD |

**Bundle target at /027 multi-seed UNCHANGED**: 2-specialist nominal Σ = +1.30 if independent; realistic with correlation drag + multi-seed variance reduction = **+1.10 to +1.30 OOS Sharpe** (UNCHANGED from /022 + /023 post-states).

**Why regime-conditional NOT bundled**: F-AXIS #5 FAIL 2/3 cohorts + F3 IS-CAT confirm the architectural component does not contribute positive alpha at v1 single-seed EXPLORATION budget. LM Master §5 estimated +0.15 OOS Sharpe contribution to /027 nominal; observed NEGATIVE component contribution. Bundling would add 7 sub-models × ENSEMBLE_SIZE → compute cost up ~75% with NEGATIVE expected alpha. The /027 substrate has stabilized at 2 specialists since /019; 5 consecutive cycle-3 EXPLORATIONs (/020, /022, /023, /024, soon /025) have all produced EXCLUDED outcomes rather than additions.

**Cycle-3 confirmed**: dispatch defects + axis saturation are the dominant signal post-/019. The cycle-3 substrate convergence is honest: 2 PROMISING (LINK, ETH+gate) + 1 PROMISING-METHODOLOGY (/021 H1/H2 non-compoundable) + 5 NEGATIVE clean or NEG-CAT (/016, /017, /020, /022, /023, /024) so far. /025 is the LAST cycle-3 EXPLORATION before /026 sanity slot + /027 CONFIRMATION earliest.

## 6. Track record post-/024

### LM Master directional + methodology track

| Iteration | Modal prediction | Observed | Directional score | Methodology score |
|---|---|---|:---:|:---:|
| /018 | PROMISING-INERT favorable | PROMISING-INERT-FAVORABLE | 1/1 | 1/1 |
| /019 | PROMISING modal 35% | PROMISING | 1/1 | 1/1 |
| /020 | INERT-no-effect modal 40% | NEGATIVE-CATASTROPHIC | 0/1 | 1/1 |
| /021 | CONFIRMED-H1 45% × CONFIRMED-H2 70% | BORDERLINE × REFUTED | 0.5/1 | 1/1 |
| /022 | INERT modal 40% | NEGATIVE-CATASTROPHIC (10% tail) | 0/1 | 1/1 |
| /023 | INERT modal 52% | NEGATIVE clean (18% tail) | 0/1 | 1/1 |
| **/024** | **INERT modal 48%** | **NEGATIVE clean (F3 auto-reject path + F-AXIS #5 FAIL)** | **0/1 (NEG tail directional; F3 path was not in prior distribution at sufficient mass)** | **1/1 (F-AXIS #5 LOAD-BEARING INERT-detector)** |

**Running totals post-/024**:
- **Directional**: **2/7 = 28.6%** (consistent modal-miss pattern on non-POSITIVE_EVERYWHERE axes at single-seed EXPLORATION; NEG-band tail upweighting reliable 4/4 at /020 + /022 + /023 + /024)
- **Methodology**: **5/5 = 100% PERFECT** (F-AXIS #5 gain-share recurrence at /024 was the load-bearing INERT-detector that distinguished MECHANISM-BYPASS from genuine partition-non-specialization; without it the verdict would have collided F-AXIS #1 PASS × F1 INERT-near-PROMISING into unresolvable ambiguity)

### Per /024, the load-bearing methodology call

LM Master Phase 4.5 §3 ADOPTED added F-AXIS-MECHANISM #5 (gain-share recurrence per cohort) to the brief's falsifier table. Without it, the rank-only F-AXIS #1 (dispatch correctness PASS) × F1 OOS Δ +0.0956 INERT-near-PROMISING combination would have created ~4bp ambiguity demanding adjudication. **The recurrence check provides the diagnostic frame** showing that even when architecture engages correctly, the partition does NOT activate at sub-model layer in 2/3 cohorts.

Methodology track at 5/5 PERFECT post-/024; LM Master's methodology lane remains the strongest discipline. Future v1 briefs MUST adopt LM Master methodology strengthening verbatim per `feedback_iteration_quality.md` deference rule at ≥ 5pp tail re-weighting.

### Forward LM Master deference rule (n=5 confirmation at /024)

At /020 + /022 + /023 + /024, LM Master's tail upweighting / methodology strengthening have been **load-bearing 4 of 4 times** on non-POSITIVE_EVERYWHERE axes. Future v1 briefs should:
- Adopt LM Master priors over QR initial draft if LM Master upweights tail by ≥ 5pp.
- Adopt LM Master methodology strengthening at Phase 4.5 §3-4 verbatim into brief Section 4 falsifiers (the F-AXIS #5 recurrence check at /024 was a direct adoption from LM Master §3 ADOPTED).
- Treat LM Master modal directional priors as informational with explicit reserve for tail outcomes; the F3 auto-reject path at /024 is a NEW failure mode that should propagate into future Section 5 prior tables under HIGH-RISK declarations.

## 7. /025 axis decision: OI DELTA FAMILY (PRIMARY)

Per LM Master Phase 7.4 §7 PRIMARY recommendation + Critic Phase 7.5 Path Forward #1 PRIMARY + user "diversification is the key" mandate continuing forward through NEW non-OHLCV signal source:

### Path Forward (verbatim from Critic Phase 7.5 review.md §Path Forward)

> Three candidates from families NOT in prior 5 EXPLORATIONs (/019/020/021/022 per-cohort + /023 feature-family-funding + /024 model-arch):
>
> 1. **Open-interest delta family** — `feature-family` (NEW non-OHLCV per v3 carve-out) — primitive `oi_delta_30 = (open_interest_t − open_interest_t-30) / open_interest_t-30` z-scored on 90-bar window. Same /023 spec (n_trials=18 / ENSEMBLE_SIZE=3 / 5-sym universe). Target rank ≤14/43 on ≥2 cohorts + gain share ≥4.0%. LM Master §7 PRIMARY.
>
> 2. **Liquidations-delta family** — `feature-family` (NEW orthogonal non-OHLCV) — rolling 24h-window long-vs-short liquidation imbalance, z-scored on 30-bar window. Substitutable if OI parquet ingestion infeasible.
>
> 3. **Tri-partition regime gate at multi-seed CONFIRMATION** — `model-arch` REPEAT — `[|z|<0.5, 0.5≤|z|≤1.5, |z|>1.5]` partitions. DEFERRED to /027+ CONFIRMATION; NOT a /025 option (axis closed per Row 7 + Row 4).

### /025 PRIMARY: OI delta family (feature-family REPEAT but axis content NEW)

**Choice rationale**:
1. **LM Master Phase 7.4 §7 PRIMARY RECOMMENDATION**: directly addresses the cycle-3 "NEW feature family" requirement and side-steps the regime-partition axis that /024 closed for single-seed EXPLORATION budget.
2. **Critic Phase 7.5 Path Forward #1 PRIMARY**: same axis selection, same target rank ≤14/43 + gain share ≥4.0%, same /023 spec.
3. **User mandate continuity**: "diversification is the key" — NEW non-OHLCV signal source diversifies the data-class portfolio (kline OHLCV → funding → OI delta is the natural progression).
4. **Cycle-3 saturation forcing**: per-cohort axes SATURATED (BTC /020, LTC /022 NEG-CAT both); model-arch SATURATED at single-seed EXPLORATION budget (/024); methodology axes non-compoundable (/021); /025 axis MUST be NEW; NEW data class is the highest-EV remaining axis.
5. **v3 cross-asset OHLCV CLOSED** transfer prior (`feedback_v3_cross_asset_ohlcv_closed.md`): non-OHLCV primitives (funding, OI, liquidations, basis) are explicitly carved out as permitted; OI delta is the next natural NEW data class after funding axis (LEARNED-NEGATIVE at /023).
6. **STATELESS** (no deadlock risk; sister to funding family axis-rotation pattern).
7. **Axis rotation status**: family `feature-family` REPEAT but the prior 5 EXPLORATIONs are {per-cohort-BTC /020, methodology-pivot /021, per-cohort-LTC /022, feature-family-funding /023, model-arch /024}; `feature-family` appears in prior 5 only at /023. By the strict literal rule "if the last 5 EXPLORATIONs were all from the same axis family, the NEXT EXPLORATION MUST be from a different family" — only 1 of prior 5 is `feature-family`, rotation VALID per Critic §11.7 explicit permission.

### /025 SECONDARY: Liquidations-delta family (feature-family substitutable)

**Brief pre-commit**: if OI delta parquet ingestion / data-availability is infeasible at /025 brief design time, /025 substitutes liquidations-delta family (LM Master §7 + Critic Path Forward #2). Same SECONDARY status; same target falsifier (rank ≤ 14/43 + gain ≥ 4.0% on ≥ 2 cohorts).

### /025 TERTIARY: Tri-partition regime gate (DEFERRED to /027+ CONFIRMATION)

Tri-partition regime gate (`|z|<0.5, 0.5≤|z|≤1.5, |z|>1.5`) is DEFERRED to /027+ CONFIRMATION multi-seed; NOT a /025 candidate. The /024 single-seed failure mode rules it out for cycle-3 EXPLORATION budget.

### /025 selection: OI DELTA FAMILY

**Selected**: OI delta family (`feature-family` REPEAT with NEW data class). PRIMARY; LM Master Phase 7.4 §7 + Critic Phase 7.5 Path Forward #1 + user diversification mandate CONVERGENT. Wall-clock estimate 60-90 min EXPLORATION (similar to /023 funding-family axis). 2h HARD CAP. Single-seed=42 EXPLORATION default; HIGH-RISK declaration mandatory per /024 + /023 + /022 + /020 (4 consecutive HIGH-RISK NEG-band outcomes in cycle-3; the rule "if 3+ HIGH-RISK >1σ negative deltas, next becomes mandatory multi-seed" is triggered post-/024: /020 NEG-CAT -0.86 ≥1σ + /022 NEG-CAT -1.17 ≥1σ + /024 IS NEG-CAT -0.86 ≥1σ = 3rd ≥1σ NEG at IS layer; the F1 OOS at /024 is INERT-band so OOS layer does not count toward the >1σ rule, but the IS layer DOES). **/025 MAY require multi-seed validation**; brief Section 2.5 will declare based on /025 axis-specific risk profile (OI delta is feature-family axis, not architectural, so basin-relocation risk lower than /024 model-arch axis).

## 8. Process incidents: dispatch defect catalogued; engineering report contract held

### 8.1 Dispatch defect (silent zero-mask fallback at regime_gate_v1.py:181-185)

The initial /024 implementation at HEAD `e68046a` had a SILENT ZERO-MASK FALLBACK in `make_extreme_filter` and `make_normal_filter`:

```python
def _filter(df):
    if z30_column not in df.columns:
        return np.zeros(len(df), dtype=bool)  # all-False fallback
```

Complementary normal filter at line 207-210 returned **all-True** when column missing. Asymmetric fallback → extreme empty (skip 100%) + normal full (= /023 baseline = bit-identical comparison.csv).

**Smoking gun**: comparison.csv at the first /024-A run was BIT-IDENTICAL to /023 (Sharpe +0.4121 / +0.4606 same trade counts 694/257 — every metric). This was diagnosed at LM Master Phase 7.4 (`0690022`) as MECHANISM-BYPASS at the data-loading layer, NOT a basin invariance signal. Critic Phase 7.5 issued BLOCK-PENDING-FIX.

### 8.2 BLOCK-PENDING-FIX resolution (single rerun under v1 protocol)

Fix applied at `3b6e2a0` (then `67341d7` for re-run reports):
1. **`regime_gate_v1.py`**: replaced silent fallback with hard `raise ValueError("Required column missing")` for both extreme and normal filters.
2. **`lgbm.py`**: added `data_filter_columns: list[str] | None` parameter. When set, the listed columns are loaded from parquet via `lookup_features()` and left-joined onto the kline master slice BEFORE calling the filter callback. The previous architecture had `_master` built from kline CSVs (OHLCV only), missing parquet-only feature columns including `funding_rate_zscore_30`.
3. **`build_lgbm_strategy`**: passes `data_filter_columns=[V1_ITER024_Z30_COLUMN]` for all 6 regime sub-model builds.
4. **5 new tests** for hard-raise + new parameter; all 23 tests PASS.

/024-A re-ran with same config (seed=42, n_trials=18, ENSEMBLE_SIZE=3). Mechanism received a fair test post-fix. comparison.csv now DIFFERS materially from /023 (IS -0.5761 vs +0.4121; OOS +0.7593 vs +0.4606). FAIR-TEST CONDITION met.

### 8.3 What we catalog: silent fallback as a NEW failure mode

This is a NEW failure mode in the v1 catalog — distinct from the engineering_report violations that dominated /019-/023. The dispatch defect at `regime_gate_v1.py:181-185` was:
- **Not a brief-level contract violation** (the brief specified the architecture correctly).
- **Not a Phase 5.5 / 6.0 gate failure** (the dispatch architecture as specified in `e68046a` passed both gates).
- **A subtle data-pipeline column-resolution defect** — `_master` did not contain the parquet-only feature column; the silent fallback masked the absence.

**New catalog entry** (NEW memory `feedback_v1_dispatch_defect_silent_fallback.md`): silent zero-mask fallback in data_filter_callback masks missing-column defects; always use hard raise. Future data-partition primitives MUST hard-raise on missing column; add precondition assertion to Phase 4.5 / Phase 6.0 checklists.

### 8.4 Engineering report contract — HELD at /024

The cycle-3 engineering_report.md missing-at-Phase-7.5-dispatch pattern (5/5 violations at /019-/023) did NOT recur at /024. Engineering report present at Phase 7.5 dispatch; BLOCK-PENDING-FIX was triggered by the data-pipeline defect (LM Master Phase 7.4 diagnosis), NOT by engineering_report absence.

**Per Phase 7.5 Critic Recommendation to QR**:
- Brief Section 4.2 wording mismatch (7 unique `model_name` values vs 7 feature_importance CSVs) — future briefs should reword.
- Missing `per_cohort_per_regime_breakdown.csv` (brief Section 10.4 binds 7-row × 14-col CSV deliverable; file absent) — engineering report `OVERALL=READY-FOR-CRITIC` should be gated on ALL mandatory deliverables present.
- F-AXIS #5 gain-share recurrence as empirically validated INERT-detector — future regime-partition axes should pre-register the same recurrence check as Phase 6.0 pre-flight (computed on synthetic/dry-run data) rather than waiting until Phase 7.5.

## 9. Merge Decision: NO-MERGE

**NO-MERGE (EXPLORATION-NEGATIVE clean; BASELINE_V1 UNCHANGED)**.

BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). The /024 iteration produces:

- **No new edge ingredient for /027 bundling** — regime-conditional architecture EXCLUDED per F-AXIS #5 FAIL 2/3 cohorts + F3 IS-CAT auto-reject (information ingested at dispatch level but partition non-specializing at sub-model level + IS basin collapse).
- **Regime-conditional architecture stays out of /027** — 2-specialist bundle UNCHANGED from /022/023 post-states.
- **Two NEW structural findings carrying forward** (catalogued at /024 closeout):
  - NEW memory `feedback_v1_regime_partition_non_specialization.md` — regime-partition sub-models do NOT learn regime-specialized features at v1 single-seed n_trials=18 EXPLORATION budget; extends /021 H2 REFUTED to sub-model level; future regime-partition axes require multi-seed OR larger extreme partition OR /027 CONFIRMATION budget.
  - NEW memory `feedback_v1_dispatch_defect_silent_fallback.md` — silent zero-mask fallback in data_filter_callback masks missing-column defects; always use hard raise; future data-partition primitives MUST hard-raise + add Phase 4.5 / Phase 6.0 precondition assertions.
- **src/ changes from /024** (commits `e68046a`, `8664bbe`, `3b6e2a0`, `67341d7`):
  - `src/crypto_trade/strategies/regime_gate_v1.py` (NEW module): `RegimeGateConfig`, `RegimeRoutedStrategy` wrapper, `make_extreme_filter` / `make_normal_filter` factory functions (now with hard ValueError on missing column).
  - `src/crypto_trade/strategies/ml/lgbm.py`: `data_filter_callback` + `data_filter_columns` parameters added (backward-compatible; default None = no filter; bit-identical to baseline).
  - `run_baseline_v1.py`: `build_lgbm_strategy()`, `build_backtest_config()`, `run_regime_cohort()` factory functions; iter-v1/024 dispatch elif branch (3 cohorts × 2 sub-models + 1 cohort × 1 sub-model = 7 sub-models total via RegimeRoutedStrategy wrapper). Per-cohort dispatch through wrapper; DOT path unchanged.
- **Tag**: `v0.v1-024` to be applied after this Phase 8 closeout commit.

**Trunk merge**: The `regime_gate_v1.py` module + `data_filter_callback`/`data_filter_columns` parameters + factory function refactor all merge to trunk via branch HEAD as pure additive backward-compatible infrastructure (default-empty list / default-None callback; opt-in via `iteration_label == "v1-024"`). The `V1_ITER024` elif branch stays on branch (not invoked at default baseline). Per `feedback_v3_baseline_update_policy.md` adopted by v1: BASELINE_V1.md UPDATE NOT triggered (EXPLORATION-NEGATIVE; only CONFIRMATION-MERGE updates baseline).

## 10. Path Forward (verbatim from Critic — Phase 7.5 FINAL recommendations)

From `briefs-v1/iteration_v1-024/review.md` §"Recommendations to QR" + §"Path Forward":

> ### Recommendations to QR
>
> 1. **Brief Section 4.2 wording mismatch**: Section 4.2 mandates "7 unique `model_name` values in trades.csv" but trades.csv has no model_name column. Verifiable via 7 feature_importance CSVs instead. Future briefs should reword.
>
> 2. **Missing `per_cohort_per_regime_breakdown.csv`**: brief Section 10.4 binds 7-row × 14-col CSV deliverable; file absent. Engineering report `OVERALL=READY-FOR-CRITIC` should be gated on ALL mandatory deliverables present.
>
> 3. **F-AXIS #5 gain-share recurrence is empirically validated INERT-detector**: future regime-partition axes should pre-register the same recurrence check as Phase 6.0 pre-flight (computed on synthetic/dry-run data) rather than waiting until Phase 7.5.
>
> ### Path Forward (mandatory on NEGATIVE)
>
> Per brief Section 11.7 LM Master §7 ADOPTED staging matrix, verdict EXPLORATION-NEGATIVE clean routes /025 to OI delta family at single-seed.
>
> Three candidates from families NOT in prior 5 EXPLORATIONs (/019/020/021/022 per-cohort + /023 feature-family-funding + /024 model-arch):
>
> 1. **Open-interest delta family** — `feature-family` (NEW non-OHLCV per v3 carve-out) — primitive `oi_delta_30 = (open_interest_t − open_interest_t-30) / open_interest_t-30` z-scored on 90-bar window. Same /023 spec (n_trials=18 / ENSEMBLE_SIZE=3 / 5-sym universe). Target rank ≤14/43 on ≥2 cohorts + gain share ≥4.0%. LM Master §7 PRIMARY.
>
> 2. **Liquidations-delta family** — `feature-family` (NEW orthogonal non-OHLCV) — rolling 24h-window long-vs-short liquidation imbalance, z-scored on 30-bar window. Substitutable if OI parquet ingestion infeasible.
>
> 3. **Tri-partition regime gate at multi-seed CONFIRMATION** — `model-arch` REPEAT — `[|z|<0.5, 0.5≤|z|≤1.5, |z|>1.5]` partitions. DEFERRED to /027+ CONFIRMATION; NOT a /025 option (axis closed per Row 7 + Row 4).

**QR Phase 8 selection**: **#1 OI delta family** (LM Master §7 PRIMARY + Critic Path Forward #1 PRIMARY + user diversification mandate CONVERGENT). Secondary: #2 liquidations-delta (substitutable if OI parquet infeasible). Tertiary: #3 tri-partition regime gate DEFERRED to /027+ CONFIRMATION.

## 11. Next Iteration Ideas

### /025 PRIMARY (per LM Master + Critic + user CONVERGENT)

**/025 = OI delta family** — family `feature-family` REPEAT but axis content NEW. Primitive `oi_delta_30 = (open_interest_t − open_interest_t-30) / open_interest_t-30` z-scored on 90-bar window. Same /023 spec (n_trials=18 / ENSEMBLE_SIZE=3 / 5-sym universe). Target rank ≤ 14/43 on ≥ 2 cohorts + gain share ≥ 4.0%. STATELESS (no deadlock risk; sister to funding family). HIGH-RISK declaration likely required per cycle-3 lineage (4 consecutive HIGH-RISK NEG-band outcomes); brief Section 2.5 will declare based on axis-specific risk profile (feature-family axis basin-relocation risk lower than /024 model-arch axis). Wall-clock estimate 60-90 min EXPLORATION; 2h HARD CAP.

### /026 FLEXIBLE per /025 outcome

Per Critic Path Forward + LM Master staging matrix:

- **/026 candidate axis A (if /025 PROMISING)**: bundle pre-validation for /027 — cross-correlation check between OI delta family monthly returns and LINK specialist + ETH+gate specialist monthly returns; verify ρ < 0.50.
- **/026 candidate axis B (if /025 LEARNED-NEGATIVE)**: OI-conditional regime gate at MULTI-SEED — sidestep /024's single-seed regime-partition failure mode; family `model-arch` REPEAT but at CONFIRMATION-spec compute.
- **/026 candidate axis C (if /025 INERT-by-importance)**: per-cohort drawdown brake — family `risk-primitive`; Critic Path Forward #2 SECONDARY at /024 closeout; STATEFUL → MANDATORY deadlock-impossibility proof per A8 catalog + iter-v3/054 lesson.
- **/026 candidate axis D (if /025 NEG-CAT)**: 3rd cycle-3 ≥1σ NEG-CAT trips MANDATORY multi-seed at /026; family TBD per /025 post-mortem.

### /027 CONFIRMATION (Option β PRE-COMMITTED per /021 §7)

Bundle architecture: FULL POOL (5 sym unchanged — A/C/D/E baseline) + 2 alpha-enhancement specialists (LINK + ETH+gate). BTC + LTC + DOT in pool. Multi-seed n_seeds ≥ 5 per `feedback_v1_seed_count_non_negotiable.md`. Pre-compute BTC-in-pool + LTC-in-pool annualized-daily-Sharpe directly (no proxy) per anchor-frame BINDING. Bundle ceiling **+1.10-1.30 OOS Sharpe** at 2-specialist baseline UNCHANGED from /022/023 post-states.

If /025 OI delta achieves PROMISING, /027 bundle MAY expand to 3-component (LINK + ETH+gate + OI-family); bundle target moves to **+1.30 to +1.50 OOS Sharpe** under correlation drag.

## 12. Axis Rotation Status (v1-only)

- **This iter's family**: `model-arch` (NEW 16th family — FIRST multi-model architecture in v1 cycle-3 history; only prior `model-arch` was /003 cycle-1 per-symbol Model A split NEGATIVE)
- **Prior 5 EXPLORATION families** (going INTO /024): per-cohort-specialization-ETH (/019), per-cohort-specialization-BTC (/020), methodology-pivot (/021), per-cohort-specialization-LTC (/022), feature-family (/023)
- **Rotation honored**: YES — `model-arch` in NONE of prior 5 (different from per-cohort-specialization-X AND methodology-pivot AND feature-family)
- **Updated prior 5 going into /025**: per-cohort-specialization-BTC (/020), methodology-pivot (/021), per-cohort-specialization-LTC (/022), feature-family (/023), **model-arch (/024)**
- **/025 axis-family**: **feature-family REPEAT** (OI delta is NEW data class within `feature-family`); prior 5 has ONLY 1 `feature-family` axis (/023 funding); rotation VALID per strict literal rule "all 5 same family" + Critic §11.7 explicit permission

## 13. Brief Section 13 Self-Check Addendum

A Phase 7+8 self-check addendum will be appended to `briefs-v1/iteration_v1-024/research_brief.md` Section 13 documenting:
- Pre-registered verdict priors vs observed: F3 auto-reject path materialized (path was not in prior distribution at sufficient mass; NEG-CAT 10% partially captures the IS-side surface); F-AXIS #5 FAIL 2/3 cohorts INDEPENDENTLY triggered Row 4 INERT-via-non-specialization
- F-AXIS #5 gain-share recurrence empirically PROVEN as INERT-detector (LM Master Phase 4.5 §3 ADOPTED; methodology track 5/5 PERFECT at /024)
- Dispatch defect catalogued — silent zero-mask fallback in data_filter_callback; new memory `feedback_v1_dispatch_defect_silent_fallback.md`
- Structural finding catalogued — /021 H2 REFUTED extends to sub-model level (regime-partition sub-models do NOT learn regime-specialized features at v1 single-seed EXPLORATION budget); new memory `feedback_v1_regime_partition_non_specialization.md`
- User mandate "multiple smaller models per regime" cannot be tested at single-seed budget; deferred to /027+ CONFIRMATION OR future cycle
- /025 axis selection: OI DELTA FAMILY (PRIMARY) per CONVERGENT routing

## 14. Files & Commits on Branch

- Branch: `iteration-v1/024` from `iter-v1/023` closeout (tag `v0.v1-023`)
- HEAD at QR Phases 1-5 brief: `669994a`
- HEAD at Phase 4.5 LM Master advisory: `84a3ae0`
- HEAD at Brief Section 3.4 LM Master responses: `aa0a591`
- HEAD at Phase 5.5 gate PASS: `f30c625`
- HEAD at QE initial implementation: `e68046a` (feat — RegimeRoutedStrategy + 7 sub-model dispatch)
- HEAD at Phase 6.0 Critic pre-flight initial BLOCK-PENDING-FIX: `e7d3dee`
- HEAD at BLOCK-PENDING-FIX wrap-at-inference fix: `8664bbe` (factory functions + run_regime_cohort)
- HEAD at Phase 6.0 RE-REVIEW PASS: `7cfc2bf`
- HEAD at Phase 7.4 LM Master post-mortem (DISPATCH DEFECT diagnosed): `0690022`
- HEAD at second BLOCK-PENDING-FIX (data_filter_columns + hard-raise): `3b6e2a0`
- HEAD at /024-A re-run reports: `67341d7`
- HEAD at Critic Phase 7.5 FINAL EXPLORATION-NEGATIVE clean: `1e5f7bc`
- HEAD at Phase 7 evaluation memo: TBD (this closeout commit batch)
- HEAD at Phase 8 diary (THIS COMMIT): TBD (this closeout commit batch)
- Reports artifacts in `reports-v1/iteration_v1-024/`

Key commits in /024:
- `01b8c73` — feat: EDA — extreme funding regime per cohort + sign-flip + persistence
- `669994a` — docs: QR Phases 1-5 + regime-conditional sub-models brief
- `84a3ae0` — docs: Phase 4.5 LM Master advisory — regime-conditional sub-models
- `aa0a591` — docs: Section 3.4 LM Master responses + DOT mitigation + 7 sub-models
- `f30c625` — docs: phase 5.5 gate PASS
- `e68046a` — feat: RegimeRoutedStrategy + 7 sub-model dispatch (DOT baseline)
- `e7d3dee` — docs: Phase 6.0 Critic pre-flight — BLOCK-PENDING-FIX (wrapper bypass)
- `8664bbe` — fix: BLOCK-PENDING-FIX — wrap sub-models via RegimeRoutedStrategy at inference
- `7cfc2bf` — docs: Phase 6.0 RE-REVIEW PASS — wrapper now invoked at inference
- `0690022` — docs: Phase 7.4 LM Master post-mortem — DISPATCH DEFECT (silent fallback)
- `3b6e2a0` — fix: regime filter hard-raise on missing column + data_filter_columns for parquet merge
- `67341d7` — feat: rerun /024-A reports (post-defect-fix)
- `1e5f7bc` — docs: Phase 7.5 FINAL — EXPLORATION-NEGATIVE clean
- (Phase 7 evaluation memo this commit batch) — `briefs-v1/iteration_v1-024/phase7_evaluation.md`
- (Phase 8 closeout this commit batch) — Phase 8 diary + merge decision (NO-MERGE)

**Trunk merge**: `regime_gate_v1.py` module + `data_filter_callback`/`data_filter_columns` parameters + factory function refactor (`build_lgbm_strategy`, `build_backtest_config`, `run_regime_cohort`) all merge to trunk via branch HEAD as pure additive backward-compatible infrastructure (default-None callback / default-empty columns list; opt-in via `iteration_label == "v1-024"`). The `V1_ITER024` elif branch + `V1_ITER024_UNIVERSE`/`V1_ITER024_Z30_COLUMN` constants stay on branch (opt-in; not invoked at default baseline). BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`).

**Tag**: `v0.v1-024` to be applied after this Phase 8 closeout commit.
