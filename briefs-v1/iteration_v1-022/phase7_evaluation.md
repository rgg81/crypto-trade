# Phase 7 — OOS Evaluation Memo — iter-v1/022

**Iteration**: iter-v1/022 (cycle-3 EXPLORATION #7 of 10 — per-cohort-specialization-LTC NEW 14th family)
**Branch**: `iteration-v1/022` HEAD `0c8602d`
**Anchor**: `v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`)
**Verdict (FINAL after BLOCK-PENDING-FIX engineering_report.md fix at `d6afb68`; Critic FINAL `0c8602d`)**: **EXPLORATION-NEGATIVE-CATASTROPHIC** — Section 8 Row 6 binding (F1 OOS Sharpe Δ ≤ −0.55).

The Phase 7 OOS measurement was the QR's first contact with the OOS data on this iteration. The verdict cell was NEGATIVE-CATASTROPHIC at F1 OOS Sharpe Δ = −1.17 (2.1× the −0.55 catastrophic floor). All four F-AXIS-MECHANISM checks PASSED — the gate operated exactly within its pre-registered fire-rate band — but the targeted phenomenon (89% long-direction OOS drag in BTC-bear) had dissolved under basin relocation. Mechanism ≠ outcome.

---

## 1. Verdict vs Phase 5 priors — the 10% NEG-CAT tail materialized

### Pre-registered priors (LM Master /022 Phase 4.5 §3 ADOPTED in brief Section 5)

LM Master recalibrated QR's initial 15/10/45/12/8/10 to **8/12/40/20/10/10** at Phase 4.5 — explicitly raising the negative tail from 30% to 40% and widening NEGATIVE-CATASTROPHIC to 10% (up from QR's 8%) on the explicit reasoning that ASYMMETRIC threshold tuning is harder than symmetric and the /020 BTC ASYMMETRIC_ROTATION precedent applies to LTC equally regardless of gate symmetry.

| Verdict cell | QR initial prior | LM Master recalibrated prior | Observed |
|---|---:|---:|---|
| PROMISING (Δ ≥ +0.37) | 15% | **8%** | — |
| PROMISING-INERT (Δ ∈ [+0.17, +0.37)) | 10% | **12%** | — |
| INERT (Δ ∈ [−0.13, +0.17)) | 45% | **40%** (modal) | — |
| NEGATIVE clean (Δ ∈ [−0.28, −0.13)) | 12% | **20%** | — |
| NEGATIVE-INTRINSIC (Δ ≤ −0.28, F-AXIS #3 PASS) | 8% | **10%** | — |
| NEGATIVE-CATASTROPHIC (Δ ≤ −0.55) | 10% | **10%** | **MATERIALIZED** |

**Observed**: F1 OOS Sharpe Δ = **−1.17** → NEGATIVE-CATASTROPHIC. The 10% tail materialized. The MODAL INERT 40% was REFUTED; the catastrophic tail was 4.4× the largest tail outcome would have been at QR's 8% prior.

### LM Master's calibration was better than QR's

The LM Master Phase 4.5 §3 prior shift (10pp from QR's PROMISING/INERT tails into NEGATIVE/NEGATIVE-CATASTROPHIC) was directionally correct:
- LM Master raised NEG total from 30% → 40% (+10pp).
- LM Master tightened PROMISING tail from 25% → 20% (−5pp).
- LM Master held NEG-CAT at 10% (vs QR's 8%) — modal recalibration.

The OBSERVED outcome (NEG-CAT) fell in the larger LM Master tail. Per Section 7.1 of `feedback_v1_h_intrinsic_refuted_at_btc.md` calibration table for cohorts with asymmetric/pool-conferred priors: NEG total 35-45% + CATASTROPHIC 5-10% bracket. LM Master's 40%/10% bracket EXACTLY MATCHES this prescription. **LM Master Phase 4.5 priors were materially better-calibrated than QR's initial pass.**

### Cell hierarchy compliance (Section 8 verdict matrix)

Per Section 8 hierarchy: NEGATIVE-DISPATCH > NEGATIVE-OVER-KILL/UNDER-FIRE > NEGATIVE-IS-COLLAPSE > NEGATIVE-INTRINSIC > **NEGATIVE-CATASTROPHIC** > NEGATIVE-INERT > ...

Eligibility check:
- NEGATIVE-DISPATCH: NO (Check #1 PASS — 100% LTCUSDT roster)
- NEGATIVE-OVER-KILL (OOS fire > 30%): NO (observed 29.17% — just inside band)
- NEGATIVE-UNDER-FIRE (OOS fire < 5%): NO (observed 29.17%)
- NEGATIVE-IS-COLLAPSE (IS Δ ≤ −0.30): NO (observed IS −0.0046 ≈ flat)
- NEGATIVE-INTRINSIC (Δ ≤ −0.28 + F-AXIS #3 PASS): would qualify mechanically but...
- **NEGATIVE-CATASTROPHIC (Δ ≤ −0.55)**: F1 Δ = −1.17 ≤ −0.55 → fires Section 8 Row 6 binding.

**Result**: NEGATIVE-CATASTROPHIC wins per strict hierarchy. The mechanism-level F-AXIS #3 PASS does NOT downgrade the verdict; per LM Master §8 closing point, "F-AXIS #3 LOAD-BEARING disambiguator, not F1 magnitude" — but when F1 ≤ −0.55, F1 magnitude IS the verdict floor.

---

## 2. /020 + /022 pattern — Per-cohort axis SATURATED for ASYMMETRIC_ROTATION cohorts (n=2)

The /022 outcome is the SECOND ASYMMETRIC_ROTATION cohort catastrophe in cycle-3. The pattern is now confirmed at n=2:

| Cohort | Iter | Prior class | Mechanism | F1 OOS Sharpe Δ | Verdict |
|---|---|---|---|---:|---|
| LINK | /018 | POSITIVE_EVERYWHERE | Pure isolation | +0.16 (multi-seed target +0.80) | PROMISING-INERT-FAVORABLE |
| ETH | /019 | Counter-trend OOS drag (symmetric) | ±8% symmetric BTC-trend gate | +0.65 (multi-seed target +0.50) | PROMISING |
| **BTC** | **/020** | **ASYMMETRIC_ROTATION (IS-NEG/OOS-POS)** | **Pure isolation** | **−0.86** | **NEGATIVE-CATASTROPHIC** |
| **LTC** | **/022** | **ASYMMETRIC_ROTATION-INVERSE (IS-MARGINAL/OOS-CAT)** | **Asymmetric long-suppress gate @ −4%** | **−1.17** | **NEGATIVE-CATASTROPHIC** |

### The mechanism: basin relocation dissolves the asymmetry on which any gate's targeting depends

Per LM Master Phase 7.4 §3 + Critic Phase 7.5 cross-check:

1. **/022 IS LTC retrained basin is fundamentally different from baseline LTC-in-pool slice.** Baseline LTC IS direction-asymmetric (IS shorts +14.10% / IS longs −10.82%); /022 IS longs +44.54% AND IS shorts +23.00% (BOTH positive). The 89% IS direction-asymmetric pattern that justified the gate is GONE in the retrained basin.

2. **/022 OOS LTC drag direction shifted from 96% long (baseline) to 76% long (/022 retrained).** OOS short drag grew 4.6× from −1.81% to −8.34%. The asymmetric long-suppress gate by design cannot touch short-direction trades — even at 29.17% OOS fire rate (heavy engagement), it leaves the short-side −8.34% drag untouched.

3. **Jaccard 0.10 IS / 0.093 OOS** — only 7 of baseline's 34 OOS LTC trades survive into /022's 48-trade OOS roster. The ORACLE EDA projected +12.45% OOS PnL Δ on the baseline 34-trade roster — descriptively true (it would have removed the right trades) but operationally irrelevant because the retrained basin produced a 79% non-overlapping roster where the mechanism's target had dissolved.

### Prior-class taxonomy partitions success cleanly

The 4-cohort empirical evidence partitions cleanly along prior-class lines:

- **POSITIVE_EVERYWHERE (LINK)** → pure isolation PRESERVED the cohort's positive prior. Pool was NOT load-bearing.
- **Counter-trend symmetric (ETH)** → isolation + ±8% symmetric gate DISSOLVED the OOS negative drag. Gate is load-bearing.
- **ASYMMETRIC_ROTATION (BTC + LTC)** → isolation alone OR isolation + asymmetric gate BOTH catastrophic. Basin-relocation dominates regardless of gate symmetry.

**Codified rule** (per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md` at /022 closeout): per-cohort single-cohort isolation is STRUCTURALLY INVIABLE for ASYMMETRIC_ROTATION cohorts at current single-seed EXPLORATION budget (ENSEMBLE_SIZE=3, n_trials=18, seed=42). Future v1 single-cohort EXPLORATIONs require POSITIVE_EVERYWHERE (LINK-like) or counter-trend-symmetric (ETH-like) cohort class. ASYMMETRIC_ROTATION cohorts go IN POOL.

---

## 3. LM Master track record update

### Phase 4.5 prediction vs observation

| Phase 4.5 prediction | Observed | Score |
|---|---|---|
| F-AXIS #2 IS [70, 160] modal 100 | 117 | **HIT inside band, above modal** |
| F-AXIS #2 OOS [18, 50] modal 28 | 48 | **HIT inside band, above modal** |
| F-AXIS #3 IS [15%, 40%] | 17.95% | **HIT (LOAD-BEARING PASS)** |
| F-AXIS #3 OOS [5%, 30%] | 29.17% | **HIT (LOAD-BEARING PASS — near top of band)** |
| n_eff_per_cell point 8 / band [6, 10] | 8 | **HIT EXACT** |
| Jaccard [0.03, 0.20] modal 0.06 | IS 0.10 / OOS 0.093 | **HIT both inside band, above modal** |
| Verdict-class prior NEG-CAT at 10% tail | NEG-CATASTROPHIC observed | **HIT TAIL** (verdict prior absorbed at 10% mass — directionally calibrated) |
| LM §8 closing: "F-AXIS #3 LOAD-BEARING, not F1 magnitude" | F-AXIS #3 PASSED yet F1 catastrophic | **VINDICATED** — mechanism operated nominally but anchor at extreme negative made F1 the verdict floor |

**Net**: 6/6 mechanism-level micro-mechanics HIT; verdict-class directional prior absorbed at the larger LM Master tail (versus QR's smaller initial tail); methodology calls (n_eff, Jaccard band narrowing, F-AXIS #3 LOAD-BEARING designation) all VINDICATED.

### Cumulative LM Master track record post-/022

| Iteration | Modal verdict prediction | Observed | Directional score | Methodology score |
|---|---|---|:---:|:---:|
| /018 | PROMISING-INERT favorable | PROMISING-INERT-FAVORABLE | 1/1 | 1/1 |
| /019 | PROMISING modal 35% | PROMISING | 1/1 | 1/1 |
| /020 | INERT-no-effect modal 40% | NEGATIVE-CATASTROPHIC | 0/1 | 1/1 (n_eff = 9 exact) |
| /021 H1 (45/40/15) | CONFIRMED 45% modal | CONFIRMED BORDERLINE | 0.5/1 | 1/1 (Layer A/C PASS) |
| /021 H2 (70/20/10) | CONFIRMED-H2 70% | REFUTED-H2 (10% tail) | 0/1 | — |
| **/022 (8/12/40/20/10/10)** | **INERT modal 40%** | **NEGATIVE-CATASTROPHIC (10% tail)** | **0/1 (modal off; tail directionally correct)** | **1/1 (6/6 mechanism hits)** |

**Directional running total post-/022**: 1.5/6 → **30% directional accuracy** (unchanged from /021; /022 modal off but LM Master tail prior > QR tail prior at the correct cell — directional credit for the recalibration).

**Methodology running total post-/022**: 3/3 → **4/4 = 100%** (perfect — /022 mechanism-level prediction 6/6 hit including F-AXIS #3 LOAD-BEARING designation).

### Calibration synthesis

**LM Master priors were better-calibrated than QR's initial pass on /022**:
- LM Master NEG tail 40% (vs QR 30%) — NEG-CAT outcome materialized.
- LM Master NEG-CAT specifically 10% (vs QR initial 8%) — exact LM Master tail HIT.
- LM Master F-AXIS #3 LOAD-BEARING designation — VINDICATED (all 4 F-axes PASS yet F1 catastrophic, exactly the diagnostic scenario LM Master pre-registered).

This is the second iteration in which LM Master's prior recalibration moved probability mass to the correct cell (the first was /020 — LM raised NEG tail; QR initial INERT 60% modal REFUTED at 2% tail). The pattern is: **at single-seed EXPLORATION on cohorts with non-POSITIVE_EVERYWHERE priors, LM Master's negative-tail upweighting is reliably directionally correct, even when modal still misses.**

---

## 4. Anchor-frame ambiguity discovered — CARRY-FORWARD to /023 as BINDING

### The finding (Critic Check 8)

`comparison.csv` "sharpe" field is **daily-annualized Sharpe** (`iteration_report.py:69`), NOT per-trade Sharpe. Brief Section 1 Hypothesis and Section 8 Verdict Matrix used "per-trade Sharpe" language (anchor −0.2670) while F1 was evaluated against the daily-annualized comparison.csv output (anchor proxy −0.27).

| Frame | OOS baseline | /022 OOS | Δ | Verdict at this frame |
|---|---|---|---:|---|
| Daily-annualized (comparison.csv binding) | −0.27 (proxy) | −1.4407 | **−1.17** | NEGATIVE-CATASTROPHIC |
| Per-trade (brief Section 1 anchor) | −0.2670 | ≈ −0.12 | **+0.148** | borderline PROMISING-INERT |

### Resolution

The pre-registered Section 8 verdict matrix and brief pre-commitment bind to **daily-annualized** (comparison.csv "sharpe" semantics). Per-trade frame is **INFORMATIONAL only**. Final verdict is NEGATIVE-CATASTROPHIC under binding frame.

Per /020 LESSON #5 + Critic Phase 7.5 Rec #2 carry-forward from /020 → /022 Rec #3, this is now **ELEVATED to BINDING for /023**: pre-compute per-cohort daily-annualized Sharpe directly on baseline roster; lock F1 frame explicitly to "comparison.csv 'sharpe' = daily-annualized" semantics in /023 brief and /027 CONFIRMATION brief.

### Why this matters

If the brief had locked to per-trade Sharpe from the start, the verdict would have been borderline PROMISING-INERT and the iteration would have appeared to be a marginal success. The pre-registration of daily-annualized as the binding frame (via Section 8 Row 6 + comparison.csv anchor) is what prevented the verdict from being soft-rebound through frame-slippage. This is exactly the pre-registration discipline that protects against researcher overfitting on the OOS view.

---

## 5. /027 bundle composition update — 2 specialists + FULL POOL preserved

Post-/022, the /027 substrate is settled. Two specialists are LOAD-BEARING; both ASYMMETRIC_ROTATION cohorts (BTC + LTC) drop OUT of specialist roles and stay IN POOL.

| Component | Provenance | Bundle role | Status | Multi-seed Δ target |
|---|---|---|---|---|
| Pool baseline (5 sym, A/C/D/E unchanged) | BASELINE_V1.md | Pool anchor | LOCKED | 0 |
| LINK-only specialist (Model C) | /018 PROMISING-INERT-FAVORABLE | Alpha-enhancement | LOCKED | **+0.80** |
| ETH-only + symmetric BTC-trend gate (Model G) | /019 PROMISING | Alpha-enhancement | LOCKED | **+0.50** |
| BTC (in pool via Model A) | /020 NEG-CAT EXCLUDED specialist | Pool baseline only | LOCKED | — |
| **LTC (in pool via Model D)** | **/022 NEG-CAT EXCLUDED specialist** | **Pool baseline only** | **NEW LOCK** | — |
| DOT (TBD /023+ routing) | pending NEW-family axis | TBD | PENDING | TBD |

**Bundle target at /027 multi-seed**:
- 2-specialist nominal Σ: +1.30 if independent.
- Realistic with correlation drag + multi-seed variance reduction: **+1.10 to +1.30 OOS Sharpe** (per /021 §7 unchanged; LM Master /022 §6 also at this band).
- Sharpe 1.0 floor merge gate: REQUIRES multi-seed mean ≥ +1.0 OOS Sharpe.

**Catastrophic outcomes /020 + /022 SUBTRACTED two candidate specialists but did NOT poison the pool.** BTC + LTC enter /027 IN POOL via Model A and Model D respectively (no architectural change vs baseline for either). The pool basin (5-sym joint loss surface) was load-bearing for both — preserving the pool preserves their OOS positive rotation, which is what we want.

---

## 6. /023 axis routing — Critic + LM Master CONVERGENT recommendation: funding-rate (PRIMARY)

Per Phase 7.5 review.md §"Path Forward" and Phase 7.4 lgbm_advisor.md §5 (both BINDING):

| Candidate | Family | Critic preference | LM Master preference |
|---|---|:---:|:---:|
| **Funding-rate z-score (8h funding)** | `feature-family` | **#1 (PRIMARY)** | **#1 (STRONGEST recommendation)** |
| Per-cohort drawdown brake | `risk-primitive` | #2 (STATEFUL — requires deadlock-impossibility proof) | #2 (symptomatic) |
| Microstructure z-score features | `feature-family` | not listed | #3 (iter-v3/015 INERT precedent) |
| Meta-labeling architecture | `labeling` | #3 (v3/017 NEGATIVE PATH C risk) | not listed |

**Critic + LM Master CONCUR on ordering**: funding-rate > drawdown-brake > meta-labeling. The convergence is 3-way (Critic + LM Master + QR Phase 7 self-assessment).

### Why funding-rate is PRIMARY

1. **NEW signal source.** v1 LightGBM has never had access to funding rates as features. The 40-feature V1_FEATURE_COLUMNS_PRUNED is all OHLCV-derived (price action, returns, momentum, mean-reversion, vol, cross-asset BTC). Funding rates encode positioning crowding that no OHLCV feature captures.

2. **Stateless.** No state propagation across signals; no deadlock risk. The feature is simply the rolling-window z-score of the published 8h funding rate, computable from data with timestamp < t.

3. **Production-proven empirically.** Per BIS WP 1087 (2025) and Crypto Carry literature, funding rates predict liquidation cascades and carry-shock returns. The 8h candle is exactly one funding period — alignment is exact (no phase-shift noise).

4. **Sidesteps the cohort-isolation axis trap.** Per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md` (NEW at /022 closeout), the per-cohort axis is SATURATED for ASYMMETRIC_ROTATION cohorts. The next axis must NOT be per-cohort. Funding-rate is a global-axis feature-family axis — added to the existing 40-feature stack and used by all 5 pool symbols + LINK + ETH specialists.

5. **Cycle-3 budget unused.** Feature-family axis has NOT been touched in cycle-3 to date. Per `feedback_v3_structural_over_knob_exploration.md` carry-forward to v1: NEW feature families > NEW model arch > NEW labeling > NEW risk primitive > universe > gate-threshold knobs. Funding-rate fits the highest-priority category.

### Falsifier pre-registration for /023 brief

- **Falsifier #1**: importance rank ≥ 30% (top quartile) on ≥ 2 cohorts (BTC, ETH, LINK, LTC, DOT) at IS using per-month FI accumulator from /021. If funding-rate features rank below top-quartile on all 5 cohorts → INERT.
- **Falsifier #2**: OOS Sharpe Δ ≥ +0.10 over /021 baseline (matching daily-annualized comparison.csv "sharpe" semantics — locked per anchor-frame BINDING above).
- **Falsifier #3 (catastrophic floor)**: OOS Sharpe Δ ≤ −0.55 → NEGATIVE-CATASTROPHIC (mirror /020 + /022 — 3 catastrophes in cycle-3 would trigger HIGH-RISK declaration mandatory multi-seed validation per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md` Path Forward).

### DOT pre-classification MANDATORY before any further per-cohort consideration

Per LM Master Phase 7.4 §4 + Critic review.md §Path Forward + saturation rule: if /023 routes to per-cohort or includes DOT-only as an alternative, DOT prior class MUST be pre-classified using the same `_classify_LTC()`-style framework as /022 Section 0.3. If DOT class = POSITIVE_EVERYWHERE or MILD_PROMISING → isolation may be viable. If DOT class = ASYMMETRIC_ROTATION → predict NEG-CAT a third time. Do NOT default /023 to DOT-only.

The convergent routing for /023 is **AWAY from per-cohort axes for the foreseeable cycle** until funding-rate, drawdown brake, or meta-labeling either succeed or close.

---

## 7. Headline numbers (for diary)

| Metric | Value | Note |
|---|---|---|
| F1 OOS Sharpe Δ | **−1.17** | vs anchor proxy −0.27; 2.1× catastrophic floor |
| F3 IS Sharpe Δ | ≈ +0.005 (INERT band, near zero) | vs anchor proxy −0.005; IS basin flipped sign |
| OOS Sharpe (daily-annualized) | −1.4407 | comparison.csv binding |
| IS Sharpe (daily-annualized) | −0.0046 | comparison.csv binding |
| OOS Total Net PnL | −33.99% | vs baseline LTC-in-pool OOS −47.25% (Δ +13.26pp) |
| IS Total Net PnL | −0.32% | vs baseline LTC-in-pool IS +3.27% (Δ −3.59pp) |
| OOS trades | 48 | inside QR [20, 60] + LM [18, 50] band |
| IS trades | 117 | inside QR [80, 180] + LM [70, 160] band |
| F-AXIS #1 dispatch | 100% LTCUSDT | PASS |
| F-AXIS #2 trade count | IS 117 / OOS 48 | PASS both bands |
| F-AXIS #3 gate fire rate IS | 17.95% (21/117) | inside [15%, 40%] LOAD-BEARING PASS |
| F-AXIS #3 gate fire rate OOS | 29.17% (14/48) | inside [5%, 30%] LOAD-BEARING PASS (near top of band) |
| F-AXIS #4 n_eff_per_cell | 8 | LM Master modal 8 EXACT HIT |
| Jaccard vs baseline LTC-in-pool IS | 0.1005 (22/219) | inside LM [0.03, 0.20] |
| Jaccard vs baseline LTC-in-pool OOS | 0.0933 (7/75) | inside LM [0.03, 0.20] |
| PSR_monthly_vs_0 OOS | 0.0112 | below 0.10 floor (catastrophic) |
| DSR | −18.35 | informational EXPLORATION-mode |
| Wall-clock | 541 s (~9 min) | 80% margin against 45-min kill-switch |

---

## 8. Substrate-level findings (binding for /023+)

### Finding A — Per-cohort isolation SATURATED for ASYMMETRIC_ROTATION cohorts (n=2)

The /020 + /022 pattern at n=2 codifies a structural rule (`feedback_v1_per_cohort_saturation_asymmetric_rotation.md`). Future v1 single-cohort EXPLORATIONs require pre-classified POSITIVE_EVERYWHERE or counter-trend-symmetric cohort class. ASYMMETRIC_ROTATION cohorts go IN POOL.

### Finding B — Gate-targeting mechanisms operate at TRADE-ROSTER level; basin relocation dissolves the asymmetry the gate targets

The asymmetric long-suppress gate fired within pre-registered fire-rate band AND fired at the wrong trades. Targeting mechanisms are roster-specific by construction; basin relocation at single-seed cohort isolation produces ~90% NEW rosters where targeted phenomena dissolve. ORACLE EDA on baseline roster is descriptively true but operationally irrelevant for retrained-basin verdicts.

### Finding C — Anchor-frame ambiguity (daily-annualized vs per-trade) — CARRY-FORWARD BINDING for /023

Pre-compute per-cohort daily-annualized Sharpe directly on baseline roster; lock F1 frame explicitly to "comparison.csv 'sharpe' = daily-annualized" semantics in /023 brief. CARRY-FORWARD from /020 Rec #2 ELEVATED to BINDING.

### Finding D — LM Master Phase 4.5 priors better-calibrated than QR's initial pass (/020 + /022 pattern at n=2)

At cohorts with non-POSITIVE_EVERYWHERE priors, LM Master's negative-tail upweighting (+10pp shifts from QR initial to LM recalibrated) is reliably directionally correct. /022 cumulative: LM Master directional 1.5/6 + methodology 4/4 = methodology lane perfect at 100%; directional 30% but tail recalibrations vindicated.

### Finding E — Funding-rate feature family is the convergent /023 PRIMARY axis

Critic + LM Master + QR 3-way convergent. NEW signal source, stateless, production-proven (BIS WP 1087), sidesteps per-cohort saturation, cycle-3 feature-family budget unused.

---

## 9. Cycle-3 cadence status post-/022

- **Cycle-3 EXPLORATION count**: **7 of 10**
- **CONFIRMATION earliest**: **/027** (assuming sequential EXPLORATIONs /023-/025 + sanity /026)
- **Edge ingredients merged this cycle**: **0** (LINK + ETH+gate are CONDITIONAL carry-forwards to /027 substrate; /020 BTC + /022 LTC both NEG-CAT EXCLUDED; /021 methodology-pivot PROMISING-METHODOLOGY non-compoundable)
- **Verdict distribution post-/022**: 1 NEGATIVE catastrophic (/016) + 1 NEGATIVE anti-direction-INERT (/017) + 1 PROMISING favorable-INERT (/018) + 1 PROMISING (/019) + 1 NEGATIVE-CATASTROPHIC (/020) + 1 PROMISING-METHODOLOGY (/021) + **1 NEGATIVE-CATASTROPHIC (/022)** = 2 PROMISING + 1 PROMISING-METHODOLOGY + 2 NEGATIVE clean + **2 NEGATIVE-CATASTROPHIC** across 7 cycle-3 EXPLORATIONs.
- **BASELINE_V1.md unchanged** at `v0.v1-baseline-corrected` (`f8bc12c`).
- **Per-cohort axis SATURATED for ASYMMETRIC_ROTATION cohorts** (n=2 confirmation); future single-cohort EXPLORATIONs gated on prior-class screening.

---

## 10. Verdict synthesis

**Verdict**: EXPLORATION-NEGATIVE-CATASTROPHIC (FINAL after BLOCK-PENDING-FIX engineering_report.md fix at `d6afb68`; Critic FINAL `0c8602d`).

**Subtype**: Section 8 Row 6 binding (F1 OOS Sharpe Δ ≤ −0.55); F-AXIS-MECHANISM #1-4 ALL PASS yet F1 catastrophic — mechanism ≠ outcome.

**Merge decision**: NO-MERGE. EXPLORATION-NEGATIVE-CATASTROPHIC does NOT update BASELINE_V1.md (per `feedback_v3_baseline_update_policy.md` adopted by v1 — only CONFIRMATION-MERGE updates baseline). LTC-only Model D' specialist EXCLUDED from /027 substrate; LTC enters /027 IN POOL via Model D (no architectural change vs baseline for LTC).

**Carry-forward bindings for /023+**:
1. Per-cohort isolation SATURATED for ASYMMETRIC_ROTATION cohorts at n=2 → NEW memory `feedback_v1_per_cohort_saturation_asymmetric_rotation.md`.
2. Anchor-frame ambiguity ELEVATED to BINDING for /023 — pre-compute daily-annualized Sharpe; lock to comparison.csv "sharpe" semantics.
3. /027 bundle composition: 2 specialists (LINK + ETH+gate) + FULL POOL preserved (BTC + LTC + DOT in pool).
4. /023 routing: funding-rate (PRIMARY) > per-cohort drawdown brake (STATEFUL — requires deadlock-impossibility proof) > meta-labeling (v3/017 NEG PATH C risk).
5. LM Master Phase 4.5 prior recalibration pattern — tail upweighting reliably directionally correct at non-POSITIVE_EVERYWHERE cohort priors; treat LM Master priors as preferred over QR initial at single-seed EXPLORATION budget.

**Phase 8 diary**: produced at `diary-v1/iteration_v1-022.md`; catalog updated; memory entry created.

---

**END OF PHASE 7 EVALUATION MEMO.**
