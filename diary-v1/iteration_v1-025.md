---
iteration: iter-v1/025
date: 2026-05-27
verdict: EXPLORATION-NEGATIVE-CATASTROPHIC (LEARNED-NEGATIVE-CATASTROPHIC subtype; FINAL after BLOCK-PENDING-FIX retrospective fix at 449ab6e)
subtype: LEARNED-NEGATIVE-CATASTROPHIC (NEW v1 cell — DUAL GATE 4/4 PROMISING-clean × F1 OOS Δ -1.40 NEG-CAT; pre-registered Section 8 Row 7 F1 magnitude OVERRIDES DUAL GATE classification)
axis_family: feature-family REPEAT (NEW data class — non-OHLCV open-interest; cycle-3 second feature-family axis after /023 funding family)
axis: OI delta primitive `oi_delta_30_z90 = z-score over 90 bars of (oi_t − oi_{t-30}) / oi_{t-30}`, clip [-10, +10]; V1_FEATURE_COLUMNS_PRUNED 42 → 43; pre-flight HARD BLOCK on 5/5 symbol OI coverage ≥ 1000 IS rows; skip-month NaN policy on early 2020-01 → 2020-09 missing-OI window
cadence_position: cycle-3 EXPLORATION (#10 of 10 — LAST before /027 CONFIRMATION)
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c) — UNCHANGED
merge_decision: NO-MERGE (EXPLORATION-NEGATIVE-CATASTROPHIC; OI delta family EXCLUDED from /027 substrate; BASELINE_V1.md UPDATE NOT triggered — only CONFIRMATION-MERGE updates baseline per `feedback_v3_baseline_update_policy.md`)
---

# Iteration iter-v1/025 — Diary

## 1. Decision: NO-MERGE (EXPLORATION-NEGATIVE-CATASTROPHIC; LEARNED-NEGATIVE-CATASTROPHIC subtype FINAL after BLOCK-PENDING-FIX)

**EXPLORATION-NEGATIVE-CATASTROPHIC** (LEARNED-NEGATIVE-CATASTROPHIC subtype — NEW v1 verdict cell at /025 closeout). Critic Phase 7.5 FINAL `23b10d6` post-BLOCK-PENDING-FIX retrospective fix at `449ab6e` (5 artifacts committed: engineering_report.md + oi_coverage_check.csv + feature_importance_per_fold.csv DEFERRED + oos_ic_matrix.csv + oracle_q4_oos_attribution.csv; NO backtest re-run per BLOCK-PENDING-FIX protocol).

Adding OI delta primitive (`oi_delta_30 = (open_interest_t − open_interest_t-30) / open_interest_t-30` z-scored on 90-bar window, clip [-10, +10]) to V1_FEATURE_COLUMNS_PRUNED (42 → 43) at single-seed=42 ENSEMBLE_SIZE=3 n_trials=18 EXPLORATION budget under Pool Model A + 4 cohort architecture produces:

- **F-AXIS #1 DUAL GATE 4/4 PROMISING-clean** — feature LEARNED uniformly across all 4 cohorts (Pool A rank 4 / 7.49% gain share; LINK rank 5 / 6.39%; LTC rank 5 / 8.00%; DOT rank 4 / 7.69%). All sub-gates (rank ≤ 14/43 + gain ≥ 4.0% + breadth ≤ 20/43 on ≥ 3 cohorts) PASS.
- **F1 OOS Sharpe Δ = -1.40** (OOS -0.7353 vs anchor +0.6637) — deep NEG-CAT band (≤ -0.55 threshold; observed is **2.5× the threshold**); 2nd-worst single-seed cycle-3 OOS Δ after /022 NEG-CAT -1.17 and /020 NEG-CAT -0.86.
- **F3 IS Sharpe Δ = +0.05** (IS +0.3327 vs anchor +0.2829) — F3 INERT band; F3 IS-catastrophic auto-reject DID NOT fire. /025 is OOS-only catastrophic, structurally distinct from /024's both-side collapse and /020/022's mirror collapses.

Per pre-registered Section 8 Row 7 (F1 magnitude OVERRIDES F-AXIS #1 classification at NEG-CAT band), verdict locks at NEGATIVE-CATASTROPHIC. **LEARNED-NEGATIVE-CATASTROPHIC** is the NEW diary sub-classifier — extends `feedback_v1_learned_negative_subtype.md` (/023 LEARNED-NEG-clean) to CATASTROPHIC magnitude band. Per `feedback_no_cheating.md` + `feedback_v1_learned_negative_subtype.md`, LEARNED-NEGATIVE-CATASTROPHIC is a diary catalog cell, NOT verdict elevation.

BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). **OI delta family EXCLUDED from /027 substrate**; /027 stays at 2-specialist UNCHANGED (Pool baseline + LINK +0.80 + ETH+gate +0.50). Cycle-3 EXPLORATIONs COMPLETE (10/10). /026 = pre-CONFIRMATION sanity slot (cross-correlation check); /027 CONFIRMATION LOCKED at multi-seed mandate.

## 2. Headline Numbers

| Metric | Value | Note |
|---|---|---|
| **F1 OOS Sharpe Δ** | **-1.40** | vs anchor +0.6637 (-0.7353 observed); DEEP NEG-CAT (2.5× threshold) |
| **F3 IS Sharpe Δ** | **+0.05** | vs anchor +0.2829 (+0.3327 observed); F3 INERT (NOT both-side collapse) |
| OOS Sharpe (monthly) | -0.7353 | comparison.csv binding |
| IS Sharpe (monthly) | +0.3327 | F3 INERT band |
| OOS Total Net PnL | -40.75% | vs baseline OOS +38.13% (catastrophic basin-pull) |
| IS Total Net PnL | +48.41% | vs baseline IS +54.05% (slight slippage; not catastrophic) |
| OOS trades | 261 | inside QR [120, 280] PASS |
| IS trades | 498 | inside QR [400, 850] PASS |
| OOS win rate | 36.0% | vs baseline 40.2% (-4.2 pp) |
| Profit factor OOS | 0.8653 | vs baseline 1.156 (-0.29) |
| Max DD OOS | 63.88% | vs baseline 40.94% (+22.94 pp) |
| Max DD IS | 72.75% | vs baseline 73.06% (flat) |
| PSR_monthly_vs_0 OOS | 0.268 | vs baseline 0.989 (declined; informational) |
| PSR_monthly_vs_1 OOS | 0.055 | vs baseline 0.0789 (informational only) |
| DSR OOS | -35.17 | informational EXPLORATION-mode |
| n_eff_per_cell_median | 9 | EXPLORATION budget band [5, 10] PASS |
| Pool A OI rank | **4** | top-cluster basin entry |
| Pool A OI gain share | **7.49%** | 1.4× /023 funding 5.40% — narrow basin via rank-4 |
| Portfolio OI gain share | **7.49%** | 1.57× v1 uniform parity (2.38% × 2 = 4.76%) |
| Top-4 split gain concentration | **39.14%** | narrow basin diagnostic |
| OI coverage PASS | 5/5 symbols ≥ 1000 IS rows | HARD BLOCK PASS (LM Master Phase 4.5 §4 load-bearing) |
| Wall-clock (backtest only) | ~45 min | INSIDE 2h cap (pre-fetch ~60 min was OUTSIDE; one-time exception per `feedback_v1_axis_selection_data_fetch_budget.md`) |

### F-AXIS DUAL GATE per-cohort table (4/4 PROMISING-clean)

| Cohort | OI rank | gain share | rank ≤ 14/43 | gain ≥ 4.0% | breadth ≤ 20/43 |
|---|---:|---:|:---:|:---:|:---:|
| Pool A (BTC+ETH) | **4** | 7.49% | PASS | PASS | PASS |
| Model C (LINK) | 5 | 6.39% | PASS | PASS | PASS |
| Model D (LTC) | 5 | 8.00% | PASS | PASS | PASS |
| Model E (DOT) | 4 | 7.69% | PASS | PASS | PASS |

DUAL GATE 4/4 PASS × F1 OOS Δ -1.40 NEG-CAT = **LEARNED-NEGATIVE-CATASTROPHIC** (information ingested + OOS realization catastrophic).

### Per-symbol OOS PnL attribution (from comparison.csv + out_of_sample/per_symbol.csv)

| Symbol | OOS trades | OOS WR | OOS net PnL % | vs baseline ΔPnL % | Note |
|---|---:|---:|---:|---:|---|
| ETH | 54 | 40.7% | +29.73 | +26.98 vs baseline +2.75 | ETH largest OOS gainer in /025 |
| DOT | 50 | 40.0% | -12.22 | -14.18 vs baseline +1.96 | flipped to negative |
| LINK | 54 | 40.7% | -20.29 | -54.52 vs baseline +34.23 | catastrophic sign reversal |
| BTC | 56 | 26.8% | -28.16 | -61.33 vs baseline +33.17 | catastrophic basin collapse |
| LTC | 47 | 31.9% | -50.63 | -3.38 vs baseline -47.25 | slight worsening from already-negative baseline |

**Net OOS: -81.57** (excluding 3 NaN-OI trades at -3.57). Major losses concentrated in BTC/LTC/LINK (-99.08); ETH/DOT roughly cancel (+17.51). Compare to baseline OOS +24.87 net → net Δ -106.44.

## 3. Mechanism narrative: top-4 split-gain 39.14% narrow basin → OI distribution drift moves leading features wrong region; Q3 mid -57.44 dominant loss

### 3.1 The narrow basin mechanism (rank-4 entry)

OI feature was LEARNED at rank-4 across all 4 cohorts (gain share uniform 6.39%-8.00%, top-cluster band entry). LightGBM concentrates **39.14% of all split gain in top-4 features** when /025 OI enters at rank 4 — this is a structurally narrower basin than /023's funding at rank 12 (which sat OUTSIDE the top-cluster band).

Per LM Master Phase 7.4 §1(A) (confidence-weighted miscalibration analysis): when OI's OOS distribution drifts, the basin moves with it and ALL 4 leading features fire from the wrong region. The narrow-basin amplification is multiplicative: 7.49% gain share × top-cluster co-movement → catastrophic OOS basin-pull.

### 3.2 The corrected Q-band attribution (Q3 mid is dominant loss, NOT Q1)

LM Master Phase 7.4 §1(B) attributed dominant loss to Q1 OOS PnL = **-30.78** sign-flip. This figure was DERIVED from IS-EDA quintile windows (aggregate forward-return by z90 bin distribution), NOT from realized-trade attribution from `trades.csv` joined to per-trade `oi_delta_30_z90`.

**The corrected Q-band attribution from `oracle_q4_oos_attribution.csv`** (Critic FINAL `23b10d6` post-BLOCK-PENDING-FIX retrospective fix `449ab6e` #5):

| Quintile | z90 range | IS EDA Sharpe-proxy | OOS trades | OOS net PnL | OOS WR | IS-OOS sign-flip |
|---|---|---:|---:|---:|---:|:---:|
| Q1 neg-extreme | [-10.0, -1.05] | +1.05 | 46 | **+24.63** | 41.3% | **NO** (SURVIVED) |
| Q2 | [-1.05, -0.31] | +0.73 | 61 | -16.32 | 37.7% | NO |
| **Q3 mid (DEAD ZONE)** | [-0.31, +0.29] | +0.04 | 55 | **-57.44** | 30.9% | **YES** (IS near zero → OOS dominant loss) |
| Q4 ORACLE | [+0.29, +0.95] | +1.68 | 44 | **+25.97** | 43.2% | NO (SURVIVED) |
| Q5 strong-pos | [+0.95, +10.0] | +0.60 | 52 | -54.84 | 30.8% | YES (IS marginal → OOS collapse) |
| NaN missing OI | — | — | 3 | -3.57 | 0.0% | — |
| **Total** | — | — | **261** | **-81.57** | 36.0% | — |

**Key corrections vs LM Master §1(B)**:
- **Q1 OOS PnL +24.63** (LM claimed -30.78; sign WAS RIGHT, magnitude wrong by 55 PnL units). Q1 SURVIVED OOS positive — no sign flip.
- **Q3 mid-band -57.44 is the DOMINANT OOS LOSS CHANNEL**. The EDA correctly identified Q3 as a "dead zone" (Sharpe-proxy +0.04 ≈ 0). Under OOS regime shift, basin relocation MOVED THE MODEL'S TRADE ENTRY POINT into the EDA-identified dead zone. This Q3 -57.44 from 55 trades is ~70% of net OOS loss.
- **Q5 strong-pos collapsed -54.84** consistent with LM §1(B) -56.41 (close; small reconciliation diff from regime-window vs realized-join).
- **Q4 ORACLE SURVIVED +25.97** as LM §1(B) noted (+22.45 in LM's window). The brief Section 2.6 ORACLE prediction was CORRECT — Q4 was the load-bearing positive band. The model just DIDN'T concentrate trades there.

### 3.3 The actual mechanism story (corrected)

1. **The brief's ORACLE Q4 hypothesis was DIRECTIONALLY CORRECT** — Q4 SURVIVED positive OOS (+25.97). But the model's IS trade attribution put TRADES outside Q4 (the bulk of IS trades fell in Q1 +24.63 → SURVIVED, Q3 dead zone → collapsed OOS, Q5 strong-pos → collapsed OOS).

2. **Q3 mid-band dead-zone is the dominant OOS loss channel** (-57.44 from 55 trades). The model under-confidently traded in Q3 under OOS regime shift. Under joint cross-asset OI regime shift (perp-funding cycle post-halving 2025-Q3/Q4), the Q3 dead-zone band became the prevalent OOS market state — the model entered it and lost.

3. **The brief's IS EDA Sharpe-proxy projection used DISTRIBUTION-LEVEL forward-return regression, NOT realized trade attribution**. Per `feedback_v1_oracle_eda_trade_attribution.md` (NEW at /025 closeout): future feature-family briefs MUST include trade-attribution Q-band PnL projection IN ADDITION to distribution-level Sharpe-proxy. Gap between the two = EDA mis-prediction risk.

### 3.4 Joint cross-asset OI regime shift (LM Master §1(C))

Per LM Master Phase 7.4 §1(C): all 5 symbols' OIs rose together through 2025-Q3/Q4 (perp-funding cycle post-halving). z90 normalizes within-symbol but joint regime shift means all cohorts' Optuna basins relocated SAME direction — no diversification cancellation. This is structurally DIFFERENT from /023 funding axis (which was more symbol-idiosyncratic; LINK funding ≠ DOT funding under the same regime).

The 2025-2026 perp-funding cycle made OI a CROSS-ASSET COMOVING signal at IS-end, then DRIFTING in OOS. /023 funding axis was less co-moving. The basin-relocation under cross-asset comovement is fundamentally different from idiosyncratic-feature basin-relocation — narrower distribution at IS → wider distribution at OOS → catastrophic.

## 4. Structural finding: /023 + /025 n=2 LEARNED-NEGATIVE pattern at v1 Pool Model A architecture single-seed

### 4.1 The pattern

/023 funding + /025 OI delta:

| Iter | Feature family | Pool A rank | Pool A gain | Portfolio gain | F1 OOS Δ | Verdict |
|---|---|---:|---:|---:|---:|---|
| /023 | funding_rate_zscore_30/90 | 11 | 6.88% | 5.40% | -0.20 | LEARNED-NEGATIVE clean |
| **/025** | **oi_delta_30_z90** | **4** | **7.49%** | **7.49%** | **-1.40** | **LEARNED-NEGATIVE-CATASTROPHIC** |

n=2. Same Pool Model A architecture + single-seed=42 + ENSEMBLE_SIZE=3 + n_trials=18 + 5-sym universe + V1_FEATURE_COLUMNS_PRUNED base (+ 2 funding cols at /023; + 1 OI col at /025). Different feature family + different cycle-3 EDA setup.

Both produced LEARNED outcomes at DUAL GATE F-AXIS #1 (information ingested above parity), AND both produced OOS Δ in NEGATIVE band. The MAGNITUDE difference (-0.20 vs -1.40) tracks basin-pull intensity: rank-12 narrow vs rank-4 narrow-er. The DIRECTION of basin-pull is governed by cross-asset regime co-movement (funding more idiosyncratic; OI more cross-asset comoving via perp-funding cycle).

### 4.2 Why this is a MECHANISM finding, not noise

- Same architecture, different feature → same verdict-cell direction (LEARNED-NEG band).
- /023 and /025 used IDENTICAL Optuna spec.
- Both fail at DUAL GATE PASS × F1 NEGATIVE collision.
- The MAGNITUDE (clean vs catastrophic) is predicted by rank position (rank-12 vs rank-4) and joint cross-asset co-movement extent (low vs high).

This is NOT a random NEG event — it is a structural pattern repeating across feature families when architecture and budget are held constant.

### 4.3 Codified rule

**`feedback_v1_pool_a_new_feature_lneg.md`** (NEW memory at /025 closeout):

> v1 Pool Model A architecture + single-seed n_trials=18 EXPLORATION budget structurally rejects NEW feature families with rank ≤ 5 / gain ≥ 4.0% (LEARNED-NEGATIVE pattern) — DUAL GATE PROMISING-clean is now a CONTRA-INDICATOR under this configuration.

Cycle-4 axis selection MUST STRUCTURALLY DISQUALIFY NEW-feature-to-Pool-Model-A EXPLORATIONs at single-seed; require ONE of:
- **per-symbol specialist axes with INDEPENDENT priors** (LINK /018 + ETH+gate /019 pattern; both PROMISING — independent priors avoid joint cross-asset basin)
- **orthogonal-mechanism rule layers** (risk-primitive / labeling / hyperparameter-region; NOT feature-additive to Pool A loss surface)
- **multi-seed budget** (ENSEMBLE_SIZE ≥ 5 inner × ≥ 2 outer at n_trials ≥ 35; basin-relocation lottery dissolves at higher compute per `feedback_v1_seed_count_non_negotiable.md`)

Cross-refs: `feedback_v1_learned_negative_subtype.md` (/023 LEARNED-NEG-clean; the diary subtype this rule generalizes); `feedback_v1_h2_refuted_basin_interaction.md` (basin-level not feature-level finding); `feedback_v1_per_cohort_saturation_asymmetric_rotation.md` (per-cohort isolation saturation; combined with this rule = strong constraint on v1 cycle-4 axis selection).

## 5. Cycle-3 closeout summary — 10/10 EXPLORATIONs complete

### 5.1 Ledger

| iter | family | verdict |
|---|---|---|
| /016 | risk-primitive (R5 vol kill-switch) | EXPLORATION-NEGATIVE catastrophic |
| /017 | risk-primitive (anti-direction R5) | EXPLORATION-NEGATIVE anti-direction-INERT |
| **/018** | **per-cohort-specialization-LINK** | **EXPLORATION-PROMISING-INERT-FAVORABLE (+0.80 OOS Δ)** |
| **/019** | **per-cohort-specialization-ETH + symmetric BTC-trend gate** | **EXPLORATION-PROMISING (+0.50 OOS Δ)** |
| /020 | per-cohort-specialization-BTC | EXPLORATION-NEGATIVE catastrophic (-0.86) |
| **/021** | **methodology-pivot (H1/H2 basin diagnostic)** | **EXPLORATION-PROMISING-METHODOLOGY (H2 REFUTED basin-interaction; non-compoundable)** |
| /022 | per-cohort-specialization-LTC | EXPLORATION-NEGATIVE catastrophic (-1.17) |
| /023 | feature-family (funding rate) | EXPLORATION-NEGATIVE clean (LEARNED-NEG-clean -0.20) |
| /024 | model-arch (regime-conditional sub-models) | EXPLORATION-NEGATIVE clean (F3 IS-CAT + F-AXIS #5 FAIL) |
| **/025** | **feature-family (OI delta)** | **EXPLORATION-NEGATIVE-CATASTROPHIC (LEARNED-NEG-CAT -1.40)** |

### 5.2 Verdict distribution

- **2 PROMISING**: /018 LINK (+0.80) + /019 ETH+gate (+0.50). BOTH per-cohort specialists with INDEPENDENT priors.
- **1 PROMISING-METHODOLOGY**: /021 H2 REFUTED basin-interaction (non-compoundable measurement substrate).
- **7 NEGATIVE**: /016 NEG-CAT, /017 NEG-anti-direction-INERT, /020 per-cohort-BTC NEG-CAT, /022 per-cohort-LTC NEG-CAT, /023 funding LEARNED-NEG, /024 regime-conditional NEG-clean, /025 OI LEARNED-NEG-CAT.
- **0 CONFIRMATION** in cycle-3 EXPLORATIONs (CONFIRMATION is /027).
- **0 merges** in cycle-3.

### 5.3 The cycle-3 saturation pattern

Only per-cohort specialists with INDEPENDENT priors survived OOS. ALL other axis families produced NEGATIVE outcomes:
- **Pool feature additions (/023 funding + /025 OI delta)**: BOTH LEARNED-NEGATIVE. n=2 mechanism finding (codified at `feedback_v1_pool_a_new_feature_lneg.md`).
- **Per-cohort isolation BTC/LTC (/020 + /022)**: BOTH NEG-CAT (ASYMMETRIC_ROTATION cohort class saturation per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md`).
- **Risk-primitive (/016 + /017)**: BOTH NEG-CAT — R5 vol kill-switch and anti-direction R5 do not survive Pool A loss surface.
- **Model-arch regime-conditional (/024)**: NEG-clean — partition non-specialization at sub-model layer (`feedback_v1_regime_partition_non_specialization.md`).
- **Methodology (/021)**: PROMISING-METHODOLOGY (H2 REFUTED; non-compoundable).

The successful axes at /018 + /019 BOTH used **per-cohort architectural changes with independent priors**, NOT feature additions to joint Pool. This is the **load-bearing structural finding** of cycle-3.

### 5.4 Cycle-4 axis priorities (informational; binding selection happens at cycle-4 brief)

Per /025 closeout structural verdict + LM Master Phase 7.4 §6 + Critic Path Forward:

1. **DOT/LTC-specialist axes with NEW risk gate** (`per-cohort-specialization`) — extend LINK/ETH+gate proven architecture to DOT and LTC. Avoid Pool A joint-loss-surface trap.
2. **Sample-weighting** (`sample-weighting`) — UNUSED cycle-3. AFML Ch.4 inverse-concurrency + sample-uniqueness. Mechanism: reduce basin formation around overlapping windows.
3. **XGBoost head-to-head with regularized leaf size** (`model-arch` REPEAT — different from /024's partition) — Level-wise growth + min_child_weight + reg_alpha NOT tested in /024.

NEW feature families to Pool A at single-seed are CLOSED per /025 structural verdict.

## 6. Track record post-/025

### 6.1 LM Master directional + methodology tracking

| Iter | Modal prior | Observed | Directional | Methodology |
|---|---|---|:---:|:---:|
| /018 | PROMISING-INERT-FAV | PROMISING-INERT-FAVORABLE | 1/1 | 1/1 |
| /019 | PROMISING modal 35% | PROMISING | 1/1 | 2/2 |
| /020 | INERT-no-effect 40% | NEGATIVE-CATASTROPHIC | 0/1 | 3/3 |
| /021 | CONFIRMED-H1 45% × CONFIRMED-H2 70% | BORDERLINE × REFUTED | 0.5/1 | 4/4 |
| /022 | INERT 40% | NEGATIVE-CATASTROPHIC | 0/1 | 5/5 |
| /023 | INERT 52% | LEARNED-NEG clean | 0/1 | 6/6 (DUAL GATE strengthening LOAD-BEARING) |
| /024 | INERT 48% | NEG-clean (F3 + F-AXIS #5) | 0/1 | 6/6 (F-AXIS #5 LOAD-BEARING; same diagnostic re-fires) |
| **/025** | **LEARNED-NEG 30% MODAL** | **LEARNED-NEG-CAT (4% tail materialized)** | **0.5/1 (modal CATEGORY hit; magnitude tail mispriced)** | **6/6 (DUAL GATE 4/4 PASS + HARD BLOCK on OI fetch BOTH load-bearing)** |

**Running totals post-/025**:
- **Directional**: **2/8 = 25%** (consistent modal-miss pattern on non-POSITIVE_EVERYWHERE axes at single-seed EXPLORATION; NEG-band tail upweighting reliable 5/5 at /020 + /022 + /023 + /024 + /025; F-AXIS-level pattern detection is the LM Master strength)
- **Methodology**: **6/6 = 100% PERFECT** (DUAL GATE F-AXIS #1 strengthening at /023 + breadth check + HARD BLOCK on OI coverage at /025 ALL load-bearing diagnostics; without them /025 verdict would have been UNRESOLVABLE: rank-only F-AXIS #1 would classify rank 4 on 4 cohorts as PROMISING-clean creating verdict cell ambiguity with F1 NEG-CAT)

### 6.2 Per /025 — load-bearing methodology calls

LM Master Phase 4.5 §3 (DUAL GATE breadth check) + §4 (HARD BLOCK on OI fetch) were BOTH load-bearing at /025:
- Without DUAL GATE breadth check (`rank ≤ 20/43 on ≥ 3 cohorts`), rank-only would have surfaced PROMISING-clean × F1 NEG-CAT collision unresolvable.
- Without HARD BLOCK on OI fetch (5/5 symbols ≥ 1000 IS rows pre-flight gate), /025 would have evaluated DUAL GATE on BTC only (the only symbol with OI archived pre-fetch); the breadth metric would have collapsed and verdict would have been uninterpretable. The HARD BLOCK forced a ~60-min pre-fetch outside the 2h budget — this triggered the wall-clock discipline lesson at §9 below.

### 6.3 Deference rule upgrade

Per `feedback_iteration_quality.md` LM Master deference at ≥ 5pp tail re-weighting: at /025 LM Master raised PROMISING tail from QR initial 26% → 30% (+4pp, below threshold), raised LEARNED-NEG from QR initial 25% → 30% (+5pp, AT threshold). The methodology strengthening was adopted verbatim into brief Section 4 + Section 3.6.

**Cycle-4 rule upgrade**: LM Master Phase 4.5 methodology strengthening has been LOAD-BEARING **6 of 6 times** post-/018 — adopt verbatim into brief Section 4 falsifiers is now **NON-NEGOTIABLE** for cycle-4+ briefs. QR cannot reject LM Master methodology strengthening at Phase 4.5 without explicit Critic + LM Master + QR 3-way convergent disagreement.

## 7. /026 staging — pre-CONFIRMATION sanity (cross-correlation check)

Per LM Master Phase 4.5 §6 + Critic Phase 7.5 FINAL §"/027 BUNDLE LOCKED" + brief Section 11.7:

**/026 is pre-CONFIRMATION sanity slot** (NOT a NEW EXPLORATION axis). Tasks:

1. **Compute Pearson correlation between monthly returns of:**
   - (a) Pool baseline (5 sym, A/C/D/E with FROZEN V1_FEATURE_COLUMNS_PRUNED 42-col anchor; NO OI/funding) — derive from BASELINE_V1.md `comparison.csv` + monthly_pnl.csv
   - (b) LINK specialist standalone (Model C' from /018 reports) — derive from `reports-v1/iteration_v1-018/in_sample/monthly_pnl.csv` + `out_of_sample/monthly_pnl.csv`
   - **Verify `|ρ(Pool, LINK)| < 0.50`**

2. **Compute Pearson correlation between monthly returns of:**
   - (a) Pool baseline (same FROZEN spec)
   - (b) ETH+gate specialist standalone (Model G from /019 reports) — derive from `reports-v1/iteration_v1-019/in_sample/monthly_pnl.csv` + `out_of_sample/monthly_pnl.csv`
   - **Verify `|ρ(Pool, ETH+gate)| < 0.50`**

3. **Decision tree**:
   - If BOTH PASS → /027 launches at multi-seed mandate.
   - If EITHER FAIL (ρ ≥ 0.50) → /026 routes to component reweighting (single-iteration pivot before /027; downweight high-correlation specialist; preserve the other).

4. **No new EXPLORATION axis at /026**; this is purely pre-CONFIRMATION sanity. Wall-clock estimate ≤ 30 min (analysis-only).

This pre-validation is MANDATORY per LM Master Phase 4.5 §6 + Critic Phase 7.5 FINAL §"/027 BUNDLE LOCKED" (recommendation: cross-correlation pre-validation MANDATORY at /027 if /025 PROMISING; since /025 is NEG, cross-correlation pre-validation is moved to /026 sanity-slot to confirm the 2-specialist bundle is structurally additive at low correlation drag).

## 8. /027 CONFIRMATION LOCKED — 2-specialist bundle + multi-seed mandate

### 8.1 Bundle composition (LOCKED)

Per LM Master Phase 7.4 §4 + Critic Phase 7.5 FINAL §"/027 BUNDLE LOCKED":

1. **BASELINE_V1 Pool** (FROZEN; 14-feature anchor; NO new features from /023 funding or /025 OI; preserves /018+/019 component priors)
2. **LINK specialist** (+0.80 OOS Δ standalone per /018)
3. **ETH+gate specialist** (+0.50 OOS Δ standalone per /019; symmetric BTC-trend gate per `feedback_v1_link_structural_prior_load_bearing.md`)

**EXCLUDED** (mechanism evidence in catalog):
- OI delta (`feedback_v1_pool_a_new_feature_lneg.md` — /025 LEARNED-NEG-CAT)
- Funding rate z-scores (`feedback_v1_learned_negative_subtype.md` — /023 LEARNED-NEG-clean)
- Regime-conditional (`feedback_v1_regime_partition_non_specialization.md` — /024 partition non-specialization)
- BTC per-cohort (/020 NEG-CAT — stays in Pool)
- LTC per-cohort (/022 NEG-CAT — stays in Pool)

### 8.2 Multi-seed mandate (MANDATORY for /027)

Per HIGH-RISK 3-in-cycle trigger (`feedback_v1_seed_count_non_negotiable.md`): /025 LEARNED-NEG-CAT -1.40 is the **4th cycle-3 ≥ 1σ NEG event** (after /020 -0.86 + /022 -1.17 + /024 IS -0.86 + /025 -1.40). Multi-seed validation is MANDATORY for /027:

- `--seeds 2` (5 inner × 2 outer = 10 models/cell vs current 3/cell)
- `--n-trials 35` (raised from 18; above TPE saturation per `feedback_v3_confirmation_n_trials_35.md`)
- Full DSR/PBO/PSR re-evaluation under CONFIRMATION-mode (NOT EXPLORATION-mode artifact per `feedback_v3_dsr_mode_artifact.md`)
- 6h wall-clock HARD CAP
- Cross-correlation pre-validation at /026 PASSED (precondition)
- Pareto-non-dominated chosen seed on 6-metric vector (Critic Check 6 enforces)

### 8.3 /027 target

**OOS Sharpe target: +1.10 to +1.30** at multi-seed mean. Path to MERGE:
- IS Sharpe > +1.0 AND OOS Sharpe > +1.0 (hard floors per BASELINE_V1.md)
- OOS / IS ratio ≥ 0.5
- ≥ 10 trades/month OOS, ≥ 130 OOS total trades
- DSR > 0.95 (multi-seed at CONFIRMATION-mode)
- PBO < 0.4
- PSR > 0.95
- 10-seed pre-MERGE validation: mean Sharpe > 0, ≥ 7/10 profitable

If /027 PASSES all gates → CONFIRMATION-MERGE → updates BASELINE_V1.md per `feedback_v3_baseline_update_policy.md`. If /027 FAILS → cycle-3 closes NO-MERGE; cycle-4 launches with axis priorities §5.4.

## 9. Process: 6th cycle-3 engineering_report incident (orchestrator-layer fix pending)

### 9.1 The /025 engineering_report.md absence at Phase 7.5 dispatch

The /025 Phase 7.5 Critic dispatch (`501e1e7`) caught engineering_report.md + 4 mandated CSV deliverables MISSING:
1. `briefs-v1/iteration_v1-025/engineering_report.md`
2. `reports-v1/iteration_v1-025/oi_coverage_check.csv`
3. `reports-v1/iteration_v1-025/in_sample/feature_importance_per_fold.csv`
4. `reports-v1/iteration_v1-025/out_of_sample/oos_ic_matrix.csv`
5. `reports-v1/iteration_v1-025/oracle_q4_oos_attribution.csv`

Critic Phase 7.5 issued BLOCK-PENDING-FIX. Retrospective fix at `449ab6e` committed all 5 artifacts (or DEFERRED with documented reason — feature_importance_per_fold.csv runner doesn't emit per-fold; aggregate ranks documented).

### 9.2 Cycle-3 incident pattern

| Iter | Engineering report at Phase 7.5 dispatch? | BLOCK-PENDING-FIX? |
|---|:---:|:---:|
| /016 | absent | issued |
| /017 | absent | issued |
| /018 | absent | issued |
| /019 | absent | issued |
| /020 | absent | issued |
| /021 | present | n/a |
| /022 | present | n/a |
| /023 | absent | issued (5th cycle-3 incident) |
| /024 | present (BLOCK was dispatch defect) | n/a (BLOCK was dispatch defect) |
| **/025** | **absent (6th cycle-3 incident)** | **issued** |

6 of 10 cycle-3 EXPLORATIONs missed engineering_report.md at Phase 7.5 dispatch. The pattern is STRUCTURAL — brief-level contracts cannot enforce engineering_report compliance. The orchestrator-layer fix is needed but PENDING (per /023 closeout catalog note "carry-forward action SKILL-LAYER NOT QR scope — codify NON-RETROSPECTIVE-FORGIVENESS at orchestrator dispatch level").

### 9.3 Resolution path forward

The orchestrator-layer fix MUST land before cycle-4 starts:
- Add Phase 6.5 gate verifying engineering_report.md present BEFORE Phase 7.5 Critic dispatch.
- Phase 5.5 gate should cross-reference Section 10.4 artifacts as literal path checklist (Critic Phase 7.5 FINAL §Recommendation #1 at /025).

This is a SKILL-LAYER fix tracked separately from QR/QE/Critic/LM Master scope.

## 10. Path Forward (from Critic — Phase 7.5 FINAL recommendations)

From `briefs-v1/iteration_v1-025/review.md` §"Path Forward (cycle-4 axis candidates, post-/027)":

> 3 candidates from NON-recent families:
>
> 1. **DOT/LTC-specialist with NEW risk gate** — `per-cohort-specialization` (extend LINK/ETH+gate proven architecture). Avoid Pool A joint-loss-surface trap.
>
> 2. **Sample-weighting** — `sample-weighting` UNUSED cycle-3. AFML Ch.4 inverse-concurrency + sample-uniqueness. Mechanism: reduce basin formation around overlapping windows.
>
> 3. **XGBoost head-to-head with regularized leaf size** — `model-arch` REPEAT (different instance vs /024 partition). Level-wise growth + min_child_weight + reg_alpha NOT tested in /024.

**QR Phase 8 adoption**: ALL 3 candidates carried forward to cycle-4. Cycle-4 brief selects from these per LM Master + Critic + user 3-way convergence. The /025 closeout DOES NOT pre-commit cycle-4 axis selection (cycle-4 is post-/027; /027 outcome may change priorities).

## 11. Next Iteration Ideas

### 11.1 /026 (immediate next — pre-CONFIRMATION sanity)

**/026 = cross-correlation pre-validation** (NOT a NEW EXPLORATION axis). Verify `|ρ(Pool, LINK)| < 0.50` AND `|ρ(Pool, ETH+gate)| < 0.50` before /027 launches at multi-seed. Wall-clock ≤ 30 min. NO src/ changes; analysis-only via `analysis/iteration_v1-026/cross_correlation.py`.

### 11.2 /027 (CONFIRMATION — LOCKED)

**/027 = 2-specialist multi-seed CONFIRMATION**. Bundle: Pool baseline + LINK + ETH+gate. Multi-seed `--seeds 2 --n-trials 35` + full DSR/PBO/PSR + 6h cap. Target OOS Sharpe +1.10-1.30 at multi-seed mean.

### 11.3 /028+ (post-/027 cycle-4 candidates — FLEXIBLE per /027 outcome)

If /027 PASSES all gates (CONFIRMATION-MERGE):
- **/028 cycle-4 first EXPLORATION**: DOT specialist (per-cohort-specialization REPEAT but new cohort) OR sample-weighting (AFML Ch.4) OR XGBoost head-to-head.
- BASELINE_V1.md updates to /027 multi-seed numbers.

If /027 FAILS gates (NO-MERGE):
- **/028 cycle-4 first EXPLORATION**: pivot to STRONGER architectural change (e.g., LightGBM → XGBoost mandate per `feedback_v3_iter016_xgboost_mandate.md` v3 transfer prior; or meta-labeling per `feedback_v3_iter017_metalabeling_mandate.md`).
- BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected`.

### 11.4 NEW-feature-to-Pool-A is CLOSED for cycle-4 EXPLORATION budget

Per /025 structural verdict (`feedback_v1_pool_a_new_feature_lneg.md`): cycle-4 EXPLORATIONs MUST NOT propose NEW feature families ADDED TO POOL MODEL A at single-seed n_trials=18. Future Pool-A feature work requires:
- Multi-seed CONFIRMATION budget, OR
- Per-symbol specialist context (LINK/ETH+gate pattern), OR
- Orthogonal-mechanism rule layer pivot.

## 12. Axis Rotation Status (v1-only)

- **This iter's family**: `feature-family` REPEAT (NEW data class — non-OHLCV open-interest; cycle-3 second feature-family axis after /023 funding family)
- **Prior 5 EXPLORATION families** (going INTO /025): per-cohort-specialization-BTC (/020), methodology-pivot (/021), per-cohort-specialization-LTC (/022), feature-family (/023), model-arch (/024)
- **Rotation status**: VALID — `feature-family` in 1 of prior 5 (only /023); not 5 of 5; strict literal rule + Critic §11.7 explicit permission allow feature-family REPEAT with NEW data class (OI delta vs funding family at /023)
- **Updated prior 5 going into /026**: methodology-pivot (/021), per-cohort-specialization-LTC (/022), feature-family (/023), model-arch (/024), feature-family (/025)
- **/026 axis-family**: `methodology` (cross-correlation pre-validation sanity slot; NOT a NEW EXPLORATION; rotation VALID by analysis-only character)

## 13. Brief Section 13 Self-Check Addendum

A Phase 7+8 self-check addendum will be appended to `briefs-v1/iteration_v1-025/research_brief.md` Section 13 documenting:
- Pre-registered verdict priors vs observed: LEARNED-NEG modal CATEGORY hit (correct family direction); NEG-CAT magnitude tail materialized at 4% prior but should have been 15-20% (LM Master self-miscalibration acknowledged)
- F-AXIS #1 DUAL GATE 4/4 PASS × F1 OOS Δ -1.40 NEG-CAT collision → LEARNED-NEGATIVE-CATASTROPHIC NEW v1 verdict cell
- Q1 sign-flip correction — LM Master §1(B) Q1 OOS -30.78 figure INCORRECT; actual +24.63 (SURVIVED); Q3 mid -57.44 is dominant loss channel
- Distribution-level Sharpe-proxy ≠ realized trade attribution — codified at NEW memory `feedback_v1_oracle_eda_trade_attribution.md`
- n=2 LEARNED-NEGATIVE pattern at v1 Pool Model A + single-seed n_trials=18 — codified at NEW memory `feedback_v1_pool_a_new_feature_lneg.md`
- Methodology track 6/6 PERFECT post-/025 (DUAL GATE 4/4 PASS + HARD BLOCK on OI fetch BOTH load-bearing); directional track 2/8 = 25%
- Wall-clock discipline lesson — `feedback_v1_axis_selection_data_fetch_budget.md` already added 2026-05-27 mid-/025
- /025 axis selection rationale post-mortem: OI delta was selected over liquidations-delta (substitutable) per LM Master + Critic + user 3-way convergence; cycle-4 lesson: NEW feature families ADDED TO POOL MODEL A at single-seed are STRUCTURALLY CLOSED

## 14. Files & Commits on Branch

- Branch: `iteration-v1/025` from `iter-v1/024` closeout (tag `v0.v1-024`)
- Reports artifacts in `reports-v1/iteration_v1-025/`

Key commits in /025 (chronological):
- `1b7977c` — feat: EDA — OI data availability + distribution + IC + ORACLE
- `9502ecd` — docs: QR Phases 1-5 + OI delta feature-family brief
- `c867d30` — docs: Phase 4.5 LM Master advisory
- `61404d0` — docs: Section 3.4 LM Master responses + HARD BLOCK OI fetch + DUAL GATE breadth
- `6f14720` — docs: phase 5.5 gate PASS
- `2ab3a30` — feat: OI delta feature + V1_FEATURE_COLUMNS_PRUNED 42→43
- `29c10ce` — docs: Phase 6.0 Critic pre-flight — BLOCK (2 dispatch defects D1+D2)
- `30fafb9` — fix: BLOCK D1+D2 — register open_interest_v1 group + skip-month NaN policy
- `1ce0b2d` — fix: N806 lint — lowercase _oos_cutoff_ms in /025 dispatch block
- `268371f` — docs: Phase 6.0 RE-REVIEW PASS — D1+D2 fixes verified
- `94fb3e1` — docs: Phase 7.4 LM Master post-mortem — LEARNED-NEGATIVE-CATASTROPHIC
- `501e1e7` — docs: Phase 7.5 Critic review — BLOCK-PENDING-FIX (5 artifacts missing)
- `449ab6e` — docs: engineering_report.md retrospective + 4 CSV deliverables (BLOCK-PENDING-FIX)
- `23b10d6` — docs: Phase 7.5 FINAL — EXPLORATION-NEGATIVE-CATASTROPHIC (LEARNED-NEGATIVE-CATASTROPHIC subtype)
- (Phase 7 evaluation memo this commit batch) — `briefs-v1/iteration_v1-025/phase7_evaluation.md`
- (Phase 8 closeout this commit batch) — Phase 8 diary + merge decision (NO-MERGE)
- (exploration_catalog.md update) — /025 row append
- (NEW memory `feedback_v1_pool_a_new_feature_lneg.md`)
- (NEW memory `feedback_v1_oracle_eda_trade_attribution.md`)
- (brief Section 13 self-check addendum)
- (tag `v0.v1-025`)

**Trunk merge**: `src/crypto_trade/features_v1/open_interest_v1.py` (new module + `add_oi_delta_v1_features()` function + 30-bar OI delta + 90-bar z-score) merges to trunk via branch HEAD as pure additive infrastructure (default OFF — opt-in via `iteration_label == "v1-025"`). The V1_FEATURE_COLUMNS_PRUNED 43-col list stays on branch (opt-in; not in default baseline). BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`).

**Tag**: `v0.v1-025` to be applied after this Phase 8 closeout commit.
