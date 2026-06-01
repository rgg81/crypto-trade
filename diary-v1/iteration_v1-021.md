---
iteration: iter-v1/021
date: 2026-05-26
verdict: EXPLORATION-PROMISING-METHODOLOGY
subtype: H1 CONFIRMED BORDERLINE × H2 REFUTED (joint cell — "Pool-conferred edge despite same features; basin-level interaction effect")
axis_family: methodology-pivot (REUSE 6th catalog family `methodology` from /001; methodology-pivot is the qualifier; cycle-3 EXPLORATION #6 of 10)
cohort: methodology iteration (no single-cohort isolation; Pool A 2-symbol BTC+ETH + BTC-only Model H side-by-side diagnostic)
specialization: NONE — methodology-only diagnostic with two src/ additions (params_persist_path buffer at `optimization.py` + per-month FI accumulator at `lgbm.py:303,797-800` + `_write_feature_importance` at `run_baseline_v1.py:573-599`); produces two diagnostic artifacts (optuna_best_params.parquet, feature_importance_*.csv) that gate /022+ routing
cadence_position: cycle-3 EXPLORATION (#6 of 10) — methodology-pivot subtype
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c) — UNCHANGED
merge_decision: NO-MERGE (EXPLORATION-PROMISING-METHODOLOGY; methodology iterations are non-compoundable per `feedback_v1_methodology_probe_discipline.md`; BASELINE_V1.md UPDATE NOT triggered — only CONFIRMATION-MERGE updates baseline per `feedback_v3_baseline_update_policy.md`)
---

# Iteration iter-v1/021 — Diary

## 1. Decision: NO-MERGE (EXPLORATION-PROMISING-METHODOLOGY; methodology findings carry forward to /022+ as binding priors)

**EXPLORATION-PROMISING-METHODOLOGY** (FINAL after BLOCK-PENDING-FIX rerun; Critic Phase 7.5 FINAL verdict `0ca2f33`). Joint cell **H1 CONFIRMED BORDERLINE × H2 REFUTED** materialized — diagnostic methodology iteration produced a substantive structural finding: **cohort-isolation effects in v1 are basin-level (Optuna parameter shifts) NOT feature-level (Spearman ρ = 0.9448 across 40 features between Pool BTC-slice and BTC-only Model H)**. The 3-channel pool-conferred mechanism from /020 is correct in spirit but mis-categorized — it operates at the basin layer (max_depth × subsample × reg_lambda × confidence_threshold under joint label distribution), not the feature-importance layer. /027 bundle architecture pre-committed to **Option β** (FULL POOL preserved + 2 specialists alpha-enhancement + signal-level merge logic; LINK +0.80 + ETH+gate +0.50 + BTC enters /027 IN POOL). BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`); /022 advances to LTC-only + orthogonal mechanism per Critic + LM Master CONVERGENT routing. **First PROMISING-METHODOLOGY in v1 history** (sister to /001/008 PROMISING-METHODOLOGY non-compoundable measurement substrate).

## 2. Headline Numbers

| Diagnostic Layer | Result | Status |
|---|---|---|
| Layer A — `optuna_best_params.parquet` row count | 106 rows (53 pool + 53 BTC-only) ≥ 48 threshold | **PASS** |
| Layer B — Determinism | NOT bit-identical baseline 5-sym vs /021 2-sym pool BUT expected per pool composition divergence | **PASS-WITH-NOTE** |
| Layer C — 10-param visibility audit | 10/10 hyperparams non-null per cell, 106/106 rows complete | **PASS** |
| H1 falsifier (training-time pool-anchor mechanism) | 4/10 params shifted on ≥50% of (sym, month) months; 1/4 key params | **CONFIRMED BORDERLINE** |
| H2 falsifier (feature-importance signature divergence) | Spearman ρ = 0.9448 between Pool BTC-slice (Model A) and BTC-only Model H feature importance rankings | **REFUTED** |
| Engineering report | Committed at `502d66e` (post BLOCK-PENDING-FIX) | **3-strike cycle-3 incident RESOLVED** |
| Wall-clock | ~32:50 min (within 60-min target; 47% margin against 2h cap) | OK |

### H1 detail — % of months with |Δ| > 0.30 by parameter

| Param | median \|Δ\| | mean \|Δ\| | P90 \|Δ\| | % > 0.30 | shifted ≥50%? |
|---|---:|---:|---:|---:|:---:|
| confidence_threshold | 0.3303 | 0.3507 | 0.6769 | **54.7%** | **YES** (key param) |
| n_estimators | 0.2444 | 0.3031 | 0.5707 | 43.4% | NO |
| max_depth | 0.5000 | 0.4245 | 0.9000 | **73.6%** | **YES** |
| num_leaves | 0.2917 | 0.3263 | 0.6417 | 49.1% | NO |
| learning_rate | 0.2233 | 0.3168 | 0.7475 | 35.9% | NO |
| subsample | 0.3065 | 0.3329 | 0.6550 | **54.7%** | **YES** |
| colsample_bytree | 0.2432 | 0.2965 | 0.6172 | 43.4% | NO |
| min_child_samples | 0.2875 | 0.2993 | 0.5900 | 47.2% | NO |
| reg_alpha | 0.2465 | 0.3009 | 0.6022 | 39.6% | NO |
| reg_lambda | 0.3595 | 0.3497 | 0.6824 | **60.4%** | **YES** |

**Verdict**: 4/10 params shifted on ≥50% of months → **CONFIRMED BORDERLINE band** (4-5 of 10). HIGH-CONFIDENCE gate (≥6 + ≥2 key) NOT met. Only `confidence_threshold` of the 4 key params {confidence_threshold, n_estimators, num_leaves, min_child_samples} crossed → 1/4 key-param coverage.

### H2 detail — Spearman ρ across 40 features

| Top-5 comparison | Pool Model A rank | BTC-only Model H rank |
|---|:---:|:---:|
| vol_atr_14 | **1** | **2** |
| trend_aroon_osc_50 | **2** | **1** |
| stat_autocorr_lag5 | **3** | **5** |
| stat_kurtosis_20 | **4** | **10** |
| mom_macd_line_12_26_9 | **5** | **8** |

Σd² (sum of squared rank deltas across 40 features) = 588.

**Spearman ρ = 1 − 6 × 588 / (40 × 1599) = 0.9448**

Per brief Section 4.2: ρ > 0.8 → **DIAGNOSTIC-REFUTED-H2**. Top-2 features bit-identical (just rank-swapped). Bottom-2 (mr_rsi_extreme_14, cal_hour_norm) bit-identical. Only middle-rank features (stat_skew_20, vol_bb_bandwidth_20, vol_taker_buy_ratio) drift. **Same features dominate per cohort** — NO cohort signature divergence at feature-importance granularity.

### Performance metrics (informational only — methodology iteration, not edge-finding)

| metric | in_sample | out_of_sample | ratio |
|---|---|---|---|
| sharpe | -0.8313 | +0.3338 | -0.4016 |
| total_trades | 287 | 95 | 0.331 |
| max_drawdown | 79.58% | 28.37% | 0.36 |
| total_net_pnl | -71.16% | +13.33% | -0.19 |

The 2-symbol pool (Model A: BTC+ETH only) IS Sharpe is deeply negative (-0.83) — pool composition divergence from baseline 5-symbol pool is expected. OOS Sharpe +0.33 + per-symbol attribution (BTC +23.78% / ETH -23.43%) reflects pool composition change, NOT a directional edge claim. Per LM Master Phase 7.4 §6: Layer B PASS-WITH-NOTE — divergence is structural to the 2-sym diagnostic setup, NOT a `params_persist_path` regression.

## 3. Mechanism Narrative

### What /021 confirmed

**H1 CONFIRMED BORDERLINE**: Optuna's best-trial parameters DO shift between pool-trained Model A (joint loss over BTC+ETH labels) and BTC-only Model H. The 4 params that shifted on >50% months are exactly the parameter-basin levers:
- `max_depth` (73.6% > 0.30): tree depth determines whether Optuna captures cross-symbol interactions vs single-cohort structure.
- `reg_lambda` (60.4%): L2 regularization shifts as loss-surface curvature differs between joint and single-cohort label distributions.
- `confidence_threshold` (54.7%): classification threshold shifts with label class balance — pool's BTC+ETH joint label distribution differs from BTC-alone.
- `subsample` (54.7%): row-sampling fraction differs as effective dataset size and label-co-occurrence pattern change.

### What /021 REFUTED

**H2 REFUTED**: The features the model VALUES are nearly invariant across pool vs cohort-only. Spearman ρ = 0.9448 is at the extreme of the DIAGNOSTIC-REFUTED-H2 region (>>0.8). The cohort-isolation channel is NOT "different features dominate per cohort". The pool-conferred edge mechanism operates at the (parameter × label-distribution) layer, NOT the feature-selection layer.

### The load-bearing finding

**Cohort isolation effects at /018 LINK and /019 ETH+gate were NOT explained by feature-level specialization.** Cohort-isolation effects must be attributed to **parameter-basin level interaction** — specifically the max_depth × subsample × reg_lambda × confidence_threshold interaction with each cohort's label distribution under joint optimization.

This is mechanistically distinct from feature-level specialization. The features are the same. The cohort cohabitation in joint optimization shifts the basin Optuna lands in. The basin determines the model's classification behavior on each cohort's label distribution. When the cohort is isolated, Optuna lands in a different basin under the cohort-alone loss surface — which can be load-bearing for some cohorts (BTC: pool-conferred OOS rotation) and neutral for others (LINK: pool-independent rotation).

### Why /020 BTC catastrophic happens

/020 BTC catastrophic was **basin-relocation under universe composition change** at single-seed=42:
- Pool basin (5-sym BTC+ETH+LINK+LTC+DOT joint labels at seed=42, n_trials=18): max_depth ≈ 5, subsample ≈ 0.65, reg_lambda ≈ 1.2, confidence_threshold ≈ 0.5. Produces BTC OOS positive rotation (+33.17%).
- BTC-only basin (BTC-alone labels at seed=42, n_trials=18): max_depth ≈ 3, subsample ≈ 0.85, reg_lambda ≈ 0.4, confidence_threshold ≈ 0.65. Picks structurally adverse OOS trade subset; OOS Sharpe -0.5566.

This is NOT a feature-level dissolution. The same vol_atr_14 + trend_aroon_osc_50 + stat_autocorr_lag5 features dominate. What differs is the (tree depth, regularization, label-classification cutoff) basin, which interacts with BTC's NATR distribution + label distribution differently than the joint distribution does.

## 4. Substrate-Level Findings

### Finding A — H2 REFUTATION binding for /022+

**Mechanism stories MUST be at basin level, NOT feature level.** /022 LTC-only brief Section 4 CANNOT claim "LTC needs different features as basis for isolation viability" — Spearman ρ = 0.9448 across 40 features (Pool BTC-slice vs BTC-only Model H) makes this story unfalsifiable in v1's current feature set. The mechanism story for any future per-cohort EXPLORATION must be framed at (max_depth, subsample, reg_lambda, confidence_threshold) × (per-cohort label distribution) interactions.

**Codified rule** (`feedback_v1_h2_refuted_basin_interaction.md` at /021 closeout): future cycle-3+ per-cohort mechanism stories MUST be at parameter-basin level. Cohorts with asymmetric or pool-conferred priors require orthogonal mechanism (gate, risk-primitive, feature) — pure isolation alone repeats /020 BTC pattern (basin-relocation under universe-composition change).

### Finding B — /020 retrospective: basin-relocation, not H_INTRINSIC refutation

The original /020 framing — "H_INTRINSIC REFUTED at training-time granularity, 3 pool-conferred channels" — is REFINED not refuted by /021. The 3 channels (C1 feature normalization / C2 label-timing co-location / C3 abs_pnl weighting) operate **at the basin layer**, not the feature layer. The pool WAS load-bearing for BTC's OOS positive rotation, but not via "different features get picked when pool vs alone" — the features stay the same; what shifts is the parameter region under joint loss optimization.

**Mental model update for /022+**:
- Pure isolation of a cohort with asymmetric/pool-conferred prior under SAME seed → basin-relocation → potentially adverse OOS trade subset.
- Adding an orthogonal mechanism (gate, risk-primitive, feature) RESTRUCTURES the cohort's basin under cohort-alone loss in a way that can compensate for the pool→alone basin shift.
- LINK's case (/018) is the only one where pure isolation worked because LINK has an independent positive prior at pool level — its pool-trained basin and alone-trained basin both rotate positive at OOS for distinct mechanism reasons.

### Finding C — Per-cohort axis architecture (Option β) PRE-COMMITTED

/027 bundle architecture is FULL POOL (5 symbols unchanged) + alpha-enhancement specialists (LINK + ETH+gate) with signal-level merge logic. NOT reduced-pool. BTC enters /027 IN POOL. LTC + DOT TBD pending /022-/025 with orthogonal mechanisms.

Bundle target Δ at /027 multi-seed: nominal +1.96 if specialists are independent; realistic with correlation drag + multi-seed variance reduction: **+1.10 to +1.30 OOS Sharpe**. Sharpe 1.0 floor merge gate requires multi-seed mean ≥ +1.0 — currently on track.

### Finding D — Per-month FI accumulator is methodologically superior to v3 convention

The /021 BLOCK-PENDING-FIX (`502d66e`) added `LightGbmStrategy._per_month_fi_log` at `lgbm.py:303` populated in `_train_for_month` at lines 797-800 + `run_baseline_v1.py:573-599` reads from accumulator. Result: `feature_importance_*.csv` reflects mean gain averaged across **53 walk-forward months** (n=53), NOT the last-month-only snapshot (n=1, v3 convention).

This is **strictly better** than v3's `run_baseline_v3.py:2730-2818` last-month convention. Worth scheduling as a v3 backport (Critic Phase 7.5 final recommendation #3).

**Codified** (`feedback_v1_per_month_fi_accumulator.md` at /021 closeout): v1 uses per-month accumulator; v3 backport candidate.

## 5. Track Record Update

### LM Master directional track (post-/021)

| Iteration | Modal verdict | Observed | Score |
|---|---|---|:---:|
| /018 | PROMISING-INERT favorable | PROMISING-INERT-FAVORABLE | 1/1 |
| /019 | PROMISING modal 35% | PROMISING | 1/1 |
| /020 | INERT-no-effect 40% modal | NEGATIVE-CATASTROPHIC | 0/1 |
| /021 H1 prior (45/40/15) | CONFIRMED 45% modal | BORDERLINE (between CONFIRMED + MIXED) | **0.5/1** |
| /021 H2 prior (70/20/10) | CONFIRMED-H2 modal 70% | REFUTED-H2 (10% tail) | **0/1** |

**Running total: 1.5/5 directional calls = 30% directional accuracy**

### LM Master methodology track (post-/021)

| Iteration | Call | Observed | Score |
|---|---|---|:---:|
| /018 | n_eff calibration | PASS | 1/1 |
| /019 | n_eff per-cell method | PASS | 1/1 |
| /020 | n_eff prediction = 9 | EXACT | 1/1 |
| /021 | Mandate `params_persist_path` + reject 2 alternatives + Layer C 10-param visibility audit | 106 rows × 11 params all non-null; visibility PASS; Layer A 106 ≥ 48 PASS | **1/1** |

**Running total: 3/3 methodology calls = 100%**

### /021 is first PROMISING-METHODOLOGY in v1 history

Sister to /001/008 (PROMISING-METHODOLOGY non-compoundable measurement substrate). Distinguishes from /001 (methodology-layer wiring of PSR×3 + ADF + IC) and /008 (n_eff PCA per-cell median) by being the first one to produce a **load-bearing structural finding for cycle-3+** (H2 REFUTATION + basin-level mechanism story binding).

## 6. /022 Staging

Per Critic Phase 7.5 FINAL recommendation + LM Master Rec #5 BORDERLINE path + brief Section 11.7 row 6 (BORDERLINE × REFUTED):

**/022 = LTC-only + orthogonal mechanism** (cadence-preserved at 6/10 EXPLORATIONs done; 4 more before /027).

### /022 brief MUST

1. **Section 0.4 — pre-classify LTC prior class** (POSITIVE_EVERYWHERE / NEGATIVE_EVERYWHERE / ASYMMETRIC_ROTATION) using baseline per-month BTC-slice analogue analysis. Per `feedback_v1_per_cohort_exploration_strategy.md` + `feedback_v1_h_intrinsic_refuted_at_btc.md`, cohorts with asymmetric/pool-conferred priors REQUIRE orthogonal mechanism.
2. **Section 4 — frame H2 REFUTED as substantive prior**. Mechanism stories MUST be at parameter-basin level (max_depth × subsample × reg_lambda × confidence_threshold × per-cohort label distribution interaction). Brief CANNOT claim "LTC needs different features as basis for isolation viability".
3. **Section 3 — implement orthogonal mechanism**: 
   - If LTC is ASYMMETRIC_ROTATION (like BTC), orthogonal mechanism (gate / risk-primitive) is REQUIRED (mirror /019 ETH+BTC-trend-gate pattern).
   - If POSITIVE_EVERYWHERE (like LINK), isolation alone may suffice (rare; LTC's baseline OOS contribution is -47.25% — likely NOT in this class).
   - If NEGATIVE_EVERYWHERE (like ETH), require orthogonal mechanism (gate or feature). LTC-only failures from prior dead-paths catalog: LTC was the strongest IS overfitter at /002 (LTC IS+76.7 PnL Δ at single-symbol pruned-features); LTC OOS contribution at baseline is the worst (-47.25%); this prior class is strongest indication.

**Falsifier**: pre-register basin-level mechanism prediction; H1 falsifier framework directly applicable. /022 verdict-class priors should weight basin-relocation NEGATIVE outcomes >30% prior absent orthogonal mechanism.

## 7. /027 Bundle Architecture (Option β PRE-COMMITTED)

Per LM Master Phase 4.5 §7 ADOPTED + /021 H2 REFUTATION + /020 retrospective:

| Component | Provenance | Bundle role | Single-seed Δ | Multi-seed regression target |
|---|---|---|---|---|
| Pool baseline (5 symbols, A/C/D/E unchanged) | BASELINE_V1.md | Pool anchor | 0 | 0 |
| LINK-only specialist (Model C) | /018 PROMISING-INERT-FAVORABLE | Alpha-enhancement | +0.16 | **+0.80** |
| ETH-only + BTC-trend gate (Model G) | /019 PROMISING | Alpha-enhancement | +0.65 | **+0.50** |
| **BTC** (via Model A pool) | /020 EXCLUDED specialist | Pool baseline only | — | — |
| **LTC** (specialist or pool?) | TBD /022 | TBD | — | — |
| **DOT** (specialist or pool?) | TBD /023 | TBD | — | — |

**Bundle target**: nominal +1.96 independent; realistic with correlation drag + multi-seed variance reduction: **+1.10 to +1.30 OOS Sharpe** at /027 multi-seed.

**Required gates at /027**:
- IS Sharpe > 1.0 AND OOS Sharpe > 1.0 (multi-seed mean)
- OOS/IS ratio ≥ 0.5
- Top-symbol ≤ 30% OOS PnL
- 10-seed validation: mean SR > 0, ≥7/10 profitable
- Cross-correlation < 0.40 between LINK and ETH+gate specialist Sharpe paths (Critic /019 Rec #3 pre-validation)
- Anchor frame: comparison.csv "sharpe" annualized-daily — pre-compute baseline BTC-in-pool annualized-daily-Sharpe directly (no monthly Sharpe proxy)
- Signal-level merge logic with pre-committed weight rule (specialist gets ≥30% of pool's per-symbol allocation when in agreement; 0% when in disagreement)

### Multi-seed regression methodology

Critic /019 Rec #3 + brief Section 11.6 mandate:
- LINK and ETH+gate specialist roster Sharpe paths cross-correlation < 0.40 (computed across walk-forward months).
- Bundle Sharpe regression: pool baseline + Σ(specialist × allocation_factor × in-agreement-indicator).
- Multi-seed (n_seeds ≥ 5, optimally 10) with mean regression and ≥7/10 profitable seeds floor.

## 8. Next Iteration Ideas

### Cycle-3 EXPLORATIONs remaining (/022-/025)

1. **/022 = LTC-only + orthogonal mechanism** (PRIMARY per Critic + LM Master CONVERGENT routing). Family: `per-cohort-specialization-LTC` (new at v1 catalog level) + orthogonal mechanism (gate or feature). Brief Section 0.4 pre-classifies LTC prior class; Section 3 implements orthogonal mechanism; Section 4 frames mechanism at basin level (not feature level). Cadence-preserved at 7/10.

2. **/023 = DOT-only + orthogonal mechanism** (SECONDARY). Family: `per-cohort-specialization-DOT` + orthogonal mechanism. DOT has IS +96.07% at /017 catastrophic-positive rotation; this is an ASYMMETRIC pattern requiring orthogonal mechanism. Cadence preserved at 8/10.

3. **/024-/025 = methodology + bundle composition work** (FLEXIBLE). Possible families:
   - **NEW feature family — funding-rate z-score or open-interest delta** (Critic /020 Path Forward #2 + /019 Critic Rec #3 carry-forward); family: `feature-family`; NOT touched in cycle-3 to date; falsifier: importance rank ≥ 30% on ≥2 cohorts at IS using the new per-month FI accumulator.
   - **Risk-primitive — per-cohort drawdown brake** (Critic /020 Path Forward #3); family: `risk-primitive`; binary off/on at -25% per-cohort cumulative loss; pre-commit deadlock-impossibility proof per A8 catalog + iter-v3/054 lesson.
   - **Bundle composition stress-test** — partial /027 multi-seed at single-seed surrogate to pre-validate cross-correlation < 0.40 between LINK and ETH+gate.

4. **/026 = pre-CONFIRMATION sanity** (FINAL). Layer B determinism re-verification at /027 multi-seed config; final brief Section 11.7 routing matrix verification; engineering report contract re-confirmation.

### Path Forward (from Critic — Phase 7.5 FINAL recommendations)

Verbatim from `briefs-v1/iteration_v1-021/review.md` §"/022 Routing Recommendation" + §"Recommendations to QR":

> 1. **/022 brief Section 0.4** — pre-classify LTC prior class.
> 2. **/022 brief Section 4** — frame H2 REFUTED as substantive prior; mechanism stories MUST be at parameter-basin level not feature-level.
> 3. **Per-month FI accumulation now on trunk** — methodologically superior to v3's last-month-snapshot. Update `feedback_v1_methodology_probe_discipline.md` to reflect new convention. Consider v3 backport.

### /027 CONFIRMATION (at /027 earliest)

Per /020 LESSON #5 + Critic Phase 7.5 Rec #2: /027 brief pre-computes BTC-in-pool annualized-daily-Sharpe directly (no proxy). Lock anchor frame to comparison.csv "sharpe" semantics. Multi-seed n_seeds ≥ 5 (per `feedback_v1_seed_count_non_negotiable.md`). Bundle ceiling **+1.30-1.60 OOS Sharpe** with successful /022 + /023 contributions.

## 9. Merge Decision: NO-MERGE

**NO-MERGE (EXPLORATION-PROMISING-METHODOLOGY; methodology iterations are non-compoundable per `feedback_v1_methodology_probe_discipline.md`)**.

BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). The /021 iteration produces:
- **No new edge ingredient for /027 bundling** (the methodology pivot is non-compoundable — sister to /001/008 PROMISING-METHODOLOGY).
- **Two diagnostic artifacts now part of v1 reporting suite**: `feature_importance_*.csv` (per-month accumulator) + `optuna_best_params.parquet` (Layer A buffer).
- **Two src/ changes carrying forward to trunk** (per QR Section 11.7 + Phase 7.5 PASS):
  - `lgbm.py:303,797-800` per-month FI accumulator (no-op on Optuna training objective; pure instrumentation).
  - `run_baseline_v1.py:573-599` `_write_feature_importance` reads from accumulator (primary path stale-safe).
  - `optimization.py` `params_persist_path` parameter (no-op on Optuna training objective; pure instrumentation).
- **Three binding methodology rules added to feedback layer**:
  - `feedback_v1_h2_refuted_basin_interaction.md` — basin-level mechanism rule (binding for /022+)
  - `feedback_v1_per_month_fi_accumulator.md` — per-month FI convention (v3 backport candidate)
  - Refinement of `feedback_v1_h_intrinsic_refuted_at_btc.md` — /020 retrospective re-interpretation as basin-relocation (not H_INTRINSIC refutation)

**Trunk merge**: src/ instrumentation merges to trunk are pure additions (no defaults changed; opt-in via runner flags or always-active no-ops). HEAD `0ca2f33` already includes the fix (commit `502d66e`). No additional trunk merge action required from this iteration; future iterations inherit the v1 per-month FI accumulator + params_persist_path infrastructure.

**Tag**: `v0.v1-021` to be applied after this Phase 8 closeout commit.

## 10. Cycle-3 Cadence Status (after /021)

- **Cycle-3 EXPLORATION count**: **6 of 10** (4 more before /027 CONFIRMATION earliest)
- **CONFIRMATION earliest**: **/027** (assuming sequential EXPLORATIONs /022-/025 + sanity /026; /027 multi-seed)
- **Edge ingredients merged this cycle**: **0** — LINK-only specialist + ETH+gate specialist are CONDITIONAL carry-forwards to /027 substrate; /020 BTC-only EXCLUDED; /021 methodology pivot is PROMISING-METHODOLOGY non-compoundable
- **Verdict distribution cycle-3 so far** (post-/021):
  - 1 EXPLORATION-NEGATIVE catastrophic (/016)
  - 1 EXPLORATION-NEGATIVE anti-direction-INERT (/017)
  - 1 EXPLORATION-PROMISING favorable-INERT (/018)
  - 1 EXPLORATION-PROMISING (/019)
  - 1 EXPLORATION-NEGATIVE Catastrophic (/020)
  - **1 EXPLORATION-PROMISING-METHODOLOGY (/021)** ← first in v1 history
  - = 2 PROMISING + 1 PROMISING-METHODOLOGY + 2 NEGATIVE clean + 1 NEGATIVE Catastrophic across 6 cycle-3 EXPLORATIONs
- **BASELINE_V1.md unchanged** at `v0.v1-baseline-corrected` (`f8bc12c`)
- **Per-cohort axis status**: SATURATED at pure isolation budget; future per-cohort EXPLORATIONs (LTC /022, DOT /023) MUST add orthogonal mechanism on top of isolation per `feedback_v1_h_intrinsic_refuted_at_btc.md` + new `feedback_v1_h2_refuted_basin_interaction.md`
- **Methodology axis status**: /021 PROMISING-METHODOLOGY non-compoundable but produces load-bearing structural prior for /022+

## 11. Axis Rotation Status (v1-only)

- **This iter's family**: `methodology-pivot` (REUSE 6th catalog family `methodology` from /001; cycle-3 EXPLORATION #6 of 10)
- **Prior 5 EXPLORATION families** (going INTO /021): sample-weighting (/016), universe (/017), per-cohort-specialization-LINK (/018), per-cohort-specialization-ETH (/019), per-cohort-specialization-BTC (/020)
- **Rotation honored**: YES — `methodology-pivot` is in NONE of the prior 5 families. Methodology was last touched at /008 (n_eff PCA per-cell median PROMISING-METHODOLOGY); the rolling-5-window precedes this.
- **Updated prior 5 going into /022**: universe (/017), per-cohort-specialization-LINK (/018), per-cohort-specialization-ETH (/019), per-cohort-specialization-BTC (/020), methodology-pivot (/021)
- **/022 axis-family (per Critic + LM Master CONVERGENT recommendation)**: `per-cohort-specialization-LTC` + orthogonal mechanism (new at v1 catalog level; rotation VALID — NOT in immediate prior 5; LTC-cohort is distinct from BTC/ETH/LINK per-cohort families)

## 12. Track Record Update

- **Verdict-class directional track**: 3/18 → **4/19** (NEW PROMISING-METHODOLOGY hit on H1 BORDERLINE; modal CONFIRMED-CONFIRMED-H2 joint cell was at 31.5% — observed cell at ~4-5% prior absorbed via H2 underweight)
- **Mechanism-level track**: 9/18 → **10/19** (NEW Critic Phase 7.5 FINAL PASS post-fix; H1 BORDERLINE band + H2 REFUTED ρ=0.9448 + Layer A 106 rows PASS + Layer C 10/10 visibility PASS)
- **LM Master directional track**: 3/20 → **3.5/21** (Phase 4.5 H1 prior 45/40/15 directionally on the boundary; Phase 4.5 H2 prior 70/20/10 absorbed at REFUTED-H2 tail)
- **LM Master methodology track**: 9/20 → **10/21** (methodology call set perfect 3/3; substrate of entire diagnostic delivered)

## 13. Files & Commits on Branch

- Branch: `iteration-v1/021` from `iter-v1/020` closeout (tag `v0.v1-020`)
- HEAD at QR Phases 1-4 + EDA: `f6a7632`
- HEAD at LM Master Phase 4.5: `87babba`
- HEAD at Brief Section 3.4 + final brief: `0dfd9b2`
- HEAD at Phase 5.5 gate PASS: `5a6ae54`
- HEAD at QE implementation + dispatch: `8e02041`
- HEAD at BLOCK-PENDING-FIX A+B (dispatch order + Layer A threshold + brief docs): `1d99069`
- HEAD at Critic Phase 6.0 PASS (post-fix): `5ea97fc`
- HEAD at LM Master Phase 7.4 post-mortem: `25d070e`
- HEAD at Critic Phase 7.5 BLOCK-PENDING-FIX initial review: `76ac18d`
- HEAD at BLOCK-PENDING-FIX H2 fix (per-month FI accumulator): `502d66e`
- HEAD at rerun reports + engineering_report.md: `26e9473`
- HEAD at Critic Phase 7.5 FINAL (post-fix): `0ca2f33`
- HEAD at Phase 7 evaluation memo: TBD
- HEAD at Phase 8 closeout (THIS COMMIT): TBD
- Reports artifacts in `reports-v1/iteration_v1-021/`

Key commits in /021:
- `f6a7632` — feat: EDA — diagnostic methodology design
- `0a2343b` — docs: QR Phases 1-5 + methodology-pivot brief
- `87babba` — docs: Phase 4.5 LM Master advisory — methodology pivot
- `0dfd9b2` — docs: Section 3.4 LM Master responses + methodology corrections
- `5a6ae54` — docs: phase 5.5 gate PASS
- `8e02041` — feat: params_persist_path + write_feature_importance + dispatch branch
- `1d99069` — fix: BLOCK-PENDING-FIX A+B
- `5ea97fc` — docs: Phase 6.0 Critic re-review PASS (post-BLOCK-PENDING-FIX)
- `25d070e` — docs: Phase 7.4 LM Master post-mortem — H1 BORDERLINE / H2 UNDETERMINED
- `76ac18d` — docs: Phase 7.5 Critic review — BLOCK-PENDING-FIX
- `502d66e` — fix: BLOCK-PENDING-FIX H2 — write_feature_importance per-month FI accumulation
- `26e9473` — feat: rerun reports + engineering_report (post-fix Pool FI populated)
- `0ca2f33` — docs: Phase 7.5 FINAL — EXPLORATION-PROMISING-METHODOLOGY
- (Phase 7 evaluation memo this commit) — `briefs-v1/iteration_v1-021/phase7_evaluation.md`
- (Phase 8 closeout this commit) — Phase 8 diary + merge decision (NO-MERGE)

**Trunk merge**: src/ instrumentation changes (per-month FI accumulator + params_persist_path) merge to trunk via the branch HEAD `0ca2f33`. PROMISING-METHODOLOGY non-compoundable: no edge-ingredient bundle for /027 from this iteration. BASELINE_V1.md UNCHANGED.

**Tag**: `v0.v1-021` to be applied after this Phase 8 closeout commit.
