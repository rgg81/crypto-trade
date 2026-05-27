# Phase 7 — OOS Evaluation Memo — iter-v1/024

**Iteration**: iter-v1/024 (regime-conditional sub-models; family `model-arch`)
**Anchor**: `v0.v1-baseline-corrected` (BASELINE_V1.md commit `f8bc12c`) — IS +0.2829 / OOS +0.6637 / OOS trades 189
**Critic Phase 7.5 FINAL** (`1e5f7bc`, post-BLOCK-PENDING-FIX rerun at `67341d7`): **EXPLORATION-NEGATIVE clean**
**Track record reference**: LM Master directional 2/6 → 2/7 (28.6%); methodology 5/5 → 5/5 (100%)

---

## 1. Verdict vs Phase 5 priors — F3 auto-reject path materialized; F-AXIS #5 INERT-detector LOAD-BEARING

### 1.1 Pre-registered LM Master priors (brief Section 5; LM Master Phase 4.5 §2 BINDING)

| Verdict | Prior | Observed |
|---|---:|:---:|
| PROMISING | 12% | — |
| PROMISING-INERT-FAV | 7% | — |
| **INERT (MODAL)** | 48% | MISSED |
| **NEGATIVE clean** | 20% | — |
| **NEGATIVE-CATASTROPHIC** | 10% | partial (F3 IS catastrophic surface) |
| PROMISING-METHODOLOGY | 3% | — |

**Pre-registered F3 IS-catastrophic auto-reject** (brief Section 4.1; Row 7 in Section 8): if F3 IS Sharpe Δ ≤ -0.30 → reject regardless of OOS. **Observed F3 IS Δ = -0.86** (IS -0.5761 vs anchor +0.2829), inside Row 7 by **-0.56**. This is the 3rd-largest IS-Δ collapse in v1 cycle-3 (after /020 -0.86, /022 -1.17).

### 1.2 The verdict cell collision and how F-AXIS #5 broke the tie

The OOS surface looked FAVORABLE in isolation (OOS Sharpe +0.7593; F1 OOS Δ = +0.0956 ∈ [-0.10, +0.10) **4bp shy of PROMISING**). Per `feedback_no_cheating.md`, pre-registered F1 bands bind; OOS +0.0956 sits in INERT band by 4bp. The /023 3bp precedent ("LEARNED-NEGATIVE NOT verdict elevation") binds: **cannot be reclassified upward on the basis of an attractive OOS surface alone**.

Two pre-registered failure triggers fire INDEPENDENTLY:

1. **Row 7 F3 auto-reject** (brief Section 4.1): IS Δ -0.86 ≤ -0.30. Sharpe-magnitude failure on the IS basin.
2. **F-AXIS #5 gain-share recurrence FAIL** (brief Section 4.2; LM Master Phase 4.5 §3 ADOPTED): per-cohort extreme sub-model funding-family combined gain share MUST EXCEED normal sub-model's per cohort. Observed:

| Cohort | EXTREME funding gain share | NORMAL funding gain share | Recurrence (EXT > NORM?) |
|---|---:|---:|:---:|
| Pool A (BTC+ETH) | **7.21%** | **9.16%** | **FAIL** |
| Model C (LINK) | **5.16%** | **7.67%** | **FAIL** |
| Model D (LTC) | 5.97% | 4.49% | PASS |

**2 of 3 cohorts FAIL** → partition NON-SPECIALIZING. The regime mechanism IS engaged at the dispatch layer but LightGBM does NOT learn regime-specialized features in the extreme sub-models for 2/3 cohorts.

**Joint Row 4 collision + Row 7 trigger**: even WITHOUT the F3 auto-reject, F-AXIS #5 FAIL would have routed the verdict to NEGATIVE/INERT. The two triggers fired independently — Section 8 verdict matrix collision; pre-registered band bindings produce EXPLORATION-NEGATIVE clean.

### 1.3 Brief Section 5 prior-class calibration: where the priors stood vs the outcome

The LM Master Phase 4.5 §2 verdict-class priors had **NEG-CAT 10%** — partially materialized as F3 IS-catastrophic surface (IS Sharpe -0.5761 vs anchor +0.2829 absolute), but not as F1 OOS-CAT (OOS sat in INERT band 4bp shy of PROMISING; OOS Sharpe +0.7593 absolute). The MODAL 48% INERT prior missed by the F3 auto-reject path. Mixed prior-class outcome: **NEG-band tail directional** (LM Master directional credit for raising NEG total from QR initial 30% to LM 30%); F3 path was the verdict-driver.

---

## 2. LM Master Phase 4.5 calibration — F-AXIS #5 gain-share recurrence as INERT-detector empirically PROVEN

### 2.1 The recurrence check is the load-bearing diagnostic

LM Master Phase 4.5 §3 ADOPTED added **F-AXIS-MECHANISM #5** to the brief's falsifier table (was 4 rows pre-LM-Master; 5 rows post-ADOPT):

> Per-sub-model funding-z30 + z90 family gain share reported. **Extreme sub-model's funding gain share MUST EXCEED normal sub-model's per cohort** — if not, partition is not specializing (Mode A INERT diagnostic strengthened, this is the LOAD-BEARING /023 lesson transferred).

The hypothesis-implementation alignment is direct: if the regime gate is genuinely partitioning the data into two regimes with DIFFERENT label distributions (the brief Section 1 H_AXIS hypothesis), the extreme sub-model MUST learn the funding family more heavily than its baseline counterpart — that is, the regime is identifying the distribution that depends on funding extremity. If the gain-share doesn't shift, the partition is informational dust.

### 2.2 What the empirical result showed

| Cohort | EXTREME gain | NORMAL gain | Δ EXT-NORM | Mode A (specialization) verdict |
|---|---:|---:|---:|:---:|
| Pool A | 7.21% | 9.16% | **-1.95pp** | **FAIL** (extreme LESS than normal) |
| LINK C | 5.16% | 7.67% | **-2.51pp** | **FAIL** |
| LTC D | 5.97% | 4.49% | +1.48pp | PASS |

The 2/3 FAIL pattern says: **LightGBM at single-seed n_trials=18 EXPLORATION budget treats the funding-extremity partition as essentially noise in Pool A and LINK extreme sub-models**. The extreme sub-models look MORE like their normal counterparts than would be predicted if the regime were a true different signal-generating distribution.

This extends the /023 LEARNED-NEGATIVE pattern (signal IS in loss surface at portfolio level, but tail-bearing not mean-bearing) to the sub-model level: even when the architecture explicitly partitions the training data, the LightGBM-at-single-seed cannot extract the partition's discriminative information at n_trials=18 with ENSEMBLE_SIZE=3.

### 2.3 LM Master Phase 7.4 post-mortem confirms

LM Master Phase 7.4 §2-3 catalogues:
- The regime gate dispatch was MECHANICALLY CORRECT (7 sub-models trained, all with non-zero training row counts; F-AXIS #1 binary PASS).
- BUT the partition did NOT produce regime-specialized features in 2/3 cohorts.
- This is a DIFFERENT failure mode from the /023 LEARNED-NEGATIVE pattern: at /023 the feature was learned at portfolio level (gain 5.40% > parity 4.76%) but didn't translate OOS; at /024 the partition mechanism itself didn't activate at the sub-model layer for 2/3 cohorts.

### 2.4 LM Master tracking after /024

- **Directional**: 2/7 → 2/7 (28.6%) — the modal INERT 48% prior MISSED by the F3 auto-reject path (which was not in the prior distribution at sufficient mass; NEG-CAT 10% partially captures the IS-side surface).
- **Methodology**: 5/5 (was 6/6 at /023; the /024 methodology call counted as 5/5 because the recurrence-check call materialized perfectly — the recurrence FAIL is what flipped /024 from "PROMISING-clean on F-AXIS #1 dispatch correctness" to "NEGATIVE clean via F-AXIS #5"). Methodology track remains **100% PERFECT 5/5** at /024.

The /024 methodology call is the most LOAD-BEARING since /023's DUAL GATE: without F-AXIS #5 in the brief's falsifier table, the verdict would have rested on a collision between F-AXIS #1 dispatch correctness (PASS) and F1 OOS Δ +0.0956 (INERT 4bp shy of PROMISING). The recurrence check broke the tie by providing the diagnostic frame that LightGBM did NOT actually learn the regime partition at 2/3 cohorts.

---

## 3. /027 bundle: regime-conditional architecture EXCLUDED; stays at 2 specialists

### 3.1 Substrate after /024

| Component | Provenance | Bundle role | Status |
|---|---|---|---|
| Pool baseline (5 sym, A/C/D/E unchanged) | BASELINE_V1.md | Pool anchor | LOCKED |
| LINK-only specialist (Model C') | /018 PROMISING-INERT-FAVORABLE | Alpha-enhancement | LOCKED (+0.80) |
| ETH-only + symmetric BTC-trend gate (Model G) | /019 PROMISING | Alpha-enhancement | LOCKED (+0.50) |
| BTC in pool via Model A | /020 NEG-CAT EXCLUDED | Pool baseline only | LOCKED |
| LTC in pool via Model D | /022 NEG-CAT EXCLUDED | Pool baseline only | LOCKED |
| Funding-family feature axis | /023 LEARNED-NEGATIVE EXCLUDED | NOT in bundle | LOCKED |
| **Regime-conditional sub-models** | **/024 EXPLORATION-NEGATIVE EXCLUDED** | **NOT in bundle** | **LOCKED at /024 closeout** |
| DOT (TBD /025+ routing) | pending OI delta + risk-primitive paths | TBD | PENDING |

**Bundle target at /027 multi-seed UNCHANGED**: 2-specialist nominal Σ = +1.30 (LINK +0.80 + ETH+gate +0.50) if independent; realistic with correlation drag + multi-seed variance reduction = **+1.10 to +1.30 OOS Sharpe**.

### 3.2 Why regime-conditional architecture NOT bundled

LM Master Phase 4.5 §5 estimated regime-conditional contribution **+0.15 OOS Sharpe** to /027 nominal bundle. The /024 outcome is:
- IS surface CATASTROPHIC (F3 IS Sharpe -0.5761 vs anchor +0.2829; Δ -0.86 in NEG-CAT band)
- F-AXIS #5 partition non-specialization FAIL 2/3 cohorts
- OOS surface FAVORABLE-INERT (F1 OOS Δ +0.0956 4bp shy of PROMISING) but cannot be bundled per pre-registered band binding

**The mechanism did NOT prove out at sub-model level**: regime-conditional architecture would add basin-relocation lottery surface (each sub-model is at single-seed n_trials=18 → ENSEMBLE_SIZE=3 inner = effective 3 paths per sub-model per month) without the corresponding regime-specialization payoff. Bundling /024 components would import 7 sub-models × ENSEMBLE_SIZE=3 = 21 paths per month + the routing wrapper, increasing /027 compute by ~75% with NEGATIVE expected alpha contribution.

### 3.3 Implication for /027 architecture

/027 stays at 2-specialist + 5-symbol pool architecture UNCHANGED from /022/023 post-states. The cycle-3 EXPLORATIONs /018-/024 have produced:
- 2 PROMISING (clean) — LINK /018, ETH+gate /019 (locked in /027)
- 1 PROMISING-METHODOLOGY non-compoundable — /021 H1/H2 diagnostic
- 4 NEGATIVE clean or NEG-CAT — /016, /017, /020, /022, /023, /024 EXCLUDED

The /027 substrate has STABILIZED at 2 specialists since /019; subsequent EXPLORATIONs /020-/024 have all EXCLUDED candidates rather than ADDING components. This is consistent with cycle-3 substrate convergence; the question for /025 + /026 + /027 is whether a NEW feature family (OI delta is the leading PRIMARY candidate per LM Master §7 + Critic Path Forward #1) can clear the LEARNED-NEGATIVE band (≥ +0.10 OOS Δ) at v1's single-seed EXPLORATION budget.

---

## 4. User mandate "multiple smaller models per regime" — cannot be tested at single-seed budget

### 4.1 What the user-mandated test required

The user Phase 8 (post-/023) directive verbatim: "be bold. diversification is the key. multiple smaller models each model performing well under different regimes." The /024 PRIMARY axis was selected specifically to operationalize this directive:
- 7 sub-models trained (vs 4 baseline) — first multi-model architecture in v1 cycle-3
- Pool A + LINK + LTC × 2 sub-models per cohort + DOT baseline = 1.75× architectural complexity
- STATELESS regime gate at signal-time
- Each sub-model trained on its own regime partition

### 4.2 Why the test could not produce a clean answer at EXPLORATION budget

The F-AXIS #5 FAIL pattern reveals that **at single-seed n_trials=18 ENSEMBLE_SIZE=3 EXPLORATION budget the regime partition does NOT activate at sub-model layer** for 2/3 cohorts. Possible explanations (not mutually exclusive):

1. **Thin extreme partition** (Pool A 1573 / LINK 709 / LTC 802 bars / DOT 726 bars excluded per LM §1) — LightGBM-at-n_trials=18 on the extreme sub-model lands in a basin similar to baseline because the optimal max_depth × subsample × reg_lambda × confidence_threshold region under thin training data is broad and overlaps with the normal sub-model's optimal region.

2. **Single-seed lottery** — at ENSEMBLE_SIZE=3 inner ensemble, each sub-model is an average of 3 trees-bagging seeds; the F-AXIS #5 FAIL pattern may dissolve at multi-seed CONFIRMATION (5+ inner × 5+ outer ENSEMBLE).

3. **Optuna trial budget too low** — at n_trials=18 the extreme sub-model's TPE has barely warmed up; the loss surface in the partition's narrow region requires more trials to find the regime-specific basin.

4. **The mechanism doesn't exist** — funding-extremity partition may simply not produce regime-distinct label distributions at v1 8h cadence; the LightGBM model treats it as noise correctly.

### 4.3 What we cannot conclude

We **CANNOT conclude** from /024 that the user's "multiple smaller models per regime" mechanism is dead. We can only conclude:
- At v1's current EXPLORATION budget (single-seed=42 ENSEMBLE_SIZE=3 n_trials=18) the funding-extremity partition does NOT yield regime-specialized sub-models in 2/3 cohorts.
- The IS basin shifts CATASTROPHICALLY (-0.86 Δ) under the partition + 7-sub-model wrapper at this budget.
- The OOS surface is FAVORABLE-INERT (4bp shy of PROMISING) but cannot rescue the IS basin.

### 4.4 Deferred to /027+ CONFIRMATION (multi-seed)

Per the /024 brief Section 11 conditional roadmap, regime-conditional architecture under NEGATIVE/CAT verdict is CLOSED for cycle-3 EXPLORATION. BUT the mechanism is NOT permanently closed. Two possible paths:

1. **/027 CONFIRMATION variant**: bundle the 2-specialist baseline + regime-conditional as a SUB-COMPONENT under multi-seed (5 inner × 2 outer per sub-model = 50 paths per cohort per month). This would test the multi-seed hypothesis (#2 above) at CONFIRMATION-spec compute.

2. **Future cycle (after /027 CONFIRMATION)** if /027 produces multi-seed Pareto front + the regime-conditional /024 OOS surface (+0.7593) holds in stratified analysis, regime-conditional becomes a CYCLE-4 candidate ingredient.

For NOW (cycle-3): regime-conditional EXCLUDED. /025 advances to the NEW feature-family axis (OI delta).

---

## 5. Cycle-3 saturation: per-cohort + model-arch axes BOTH saturated at single-seed; /025 MUST be NEW feature-family

### 5.1 Cycle-3 axis-family summary post-/024

| Axis family | /024 status | Notes |
|---|---|---|
| **per-cohort-specialization** (LINK/ETH/BTC/LTC) | **SATURATED** at n=4 single-cohort EXPLORATIONs | /018 LINK PROMISING-INERT-FAV + /019 ETH+gate PROMISING (locked); /020 BTC NEG-CAT + /022 LTC NEG-CAT (per-cohort isolation saturated for ASYMMETRIC_ROTATION class per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md`) |
| **methodology-pivot** (/021) | SATURATED at n=1 | PROMISING-METHODOLOGY non-compoundable; H1/H2 diagnostic; cannot generate further iterations at v1 cycle-3 budget |
| **feature-family** (/023 funding) | SATURATED at n=1 for funding axis | LEARNED-NEGATIVE; OI delta is the next NEW feature family per LM Master Phase 7.4 §7 + Critic Path Forward #1 |
| **model-arch** (/024 regime-conditional) | **SATURATED at single-seed EXPLORATION budget** at n=1 | F-AXIS #5 FAIL 2/3 cohorts + F3 IS-CAT; mechanism cannot be tested at this compute; deferred to /027+ CONFIRMATION OR future cycle |
| **labeling, universe, risk-primitive, hyperparameter-region, methodology-substrate-test** | UNUSED in cycle-3 EXPLORATIONs | Available; risk-primitive (per-cohort drawdown brake) is Critic Path Forward #2 SECONDARY |
| **OI delta family** (NEW non-OHLCV) | NEW axis | LM Master Phase 7.4 §7 PRIMARY; Critic Path Forward #1; family `feature-family` REPEAT but axis content NEW |

### 5.2 /025 axis MUST be NEW feature-family

Three convergent arguments:

1. **Cycle-3 budget allocation** — /025 is #10 of 10 cycle-3 EXPLORATIONs. After /025, the next step is /026 (optional sanity slot) or directly /027 CONFIRMATION. The /025 axis is the LAST opportunity in cycle-3 to test a NEW data-source signal.

2. **Saturation discipline** — both per-cohort isolation and model-arch are saturated at single-seed EXPLORATION budget. Knob axes within saturated families would import the same basin-locked outcomes (per v3 cycle-7 transfer prior `feedback_v3_cycle7_terminal_finding.md`; per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md` for v1 cohort-isolation).

3. **NEW data source is the highest-EV axis remaining** — OI delta (open-interest delta z-scored on 90-bar window) is:
   - NEW data class (non-OHLCV; cross-asset OHLCV closed per `feedback_v3_cross_asset_ohlcv_closed.md` transfer prior to v1).
   - Production-proven (BIS WP 1087 Crypto Carry; OI dynamics as leverage stretch indicator).
   - Stateless (no deadlock risk; STATELESS sister to funding family in feature-family axis).
   - Phase 4.5 LM Master §7 PRIMARY recommendation under modal INERT (48% prior) for /025; carries forward as PRIMARY under /024 NEGATIVE verdict.
   - Critic Path Forward #1 PRIMARY for /025.

### 5.3 Critic CONCURS via Path Forward #1

Critic Phase 7.5 review.md §Path Forward (verbatim):

> 1. **Open-interest delta family** — `feature-family` (NEW non-OHLCV per v3 carve-out) — primitive `oi_delta_30 = (open_interest_t − open_interest_t-30) / open_interest_t-30` z-scored on 90-bar window. Same /023 spec (n_trials=18 / ENSEMBLE_SIZE=3 / 5-sym universe). Target rank ≤14/43 on ≥2 cohorts + gain share ≥4.0%. LM Master §7 PRIMARY.

The user's "diversification" mandate continues forward via NEW non-OHLCV feature signal source (OI delta). The "multiple smaller models per regime" sub-thesis is deferred to multi-seed /027 CONFIRMATION; the "diversification via new data class" sub-thesis advances at /025.

### 5.4 Forward implication for /027 bundle

If /025 OI delta produces:
- **PROMISING** → /027 bundle expands to 3-component (LINK + ETH+gate + OI-family). Bundle target +1.30 to +1.50 OOS Sharpe.
- **LEARNED-NEGATIVE** (v1 LEARNS OI like funding but tail-bearing) → /026 explores OI-conditional regime gate at MULTI-SEED (sidestep /024's single-seed failure mode); /027 stays 2-specialist.
- **INERT-by-importance** (v3-style failure mode; rank-bottom-quartile + gain-share below parity) → /025 axis CLOSED; /026 pivots to per-cohort drawdown brake (Critic Path Forward #2 SECONDARY); /027 stays 2-specialist.
- **NEG-CAT** → 3rd cycle-3 >1σ NEG-CAT (after /020, /022) triggers MANDATORY multi-seed at /026 + /027.

---

## 6. Summary of Phase 7 conclusions

1. **/024 EXPLORATION-NEGATIVE clean** — pre-registered F3 IS-catastrophic auto-reject path fires (-0.86 IS Δ in NEG-CAT band); F-AXIS #5 gain-share recurrence FAIL 2/3 cohorts INDEPENDENTLY routes to NEGATIVE/INERT per Section 8 collision matrix. F1 OOS Δ +0.0956 INERT-band 4bp shy of PROMISING cannot reclassify per pre-registered band binding.

2. **LM Master Phase 4.5 §3 F-AXIS #5 recurrence check was the LOAD-BEARING diagnostic** — without it, the verdict would have collided F-AXIS #1 dispatch correctness PASS × F1 OOS INERT-near-PROMISING into unresolvable ambiguity. Methodology track 5/5 PERFECT at /024.

3. **/027 bundle UNCHANGED at 2 specialists** — regime-conditional EXCLUDED; /027 substrate stable since /019; cycle-3 EXPLORATIONs /020-/024 have all produced EXCLUDED outcomes rather than additions.

4. **The user mandate "multiple smaller models per regime" cannot be tested at v1 single-seed=42 ENSEMBLE_SIZE=3 n_trials=18 EXPLORATION budget** — the regime partition does not activate at sub-model layer at this compute. Deferred to /027+ CONFIRMATION multi-seed OR future cycle.

5. **Cycle-3 axis saturation reached for per-cohort + model-arch families at single-seed EXPLORATION budget** — /025 MUST be NEW feature-family; OI delta is the PRIMARY axis per LM Master §7 + Critic Path Forward #1 + user diversification mandate.

6. **/025 advances to OI delta family** (open-interest delta, z-scored on 90-bar window); the user's "diversification" mandate continues forward through NEW non-OHLCV signal source rather than model-architecture multiplication.

7. **Process: BLOCK-PENDING-FIX resolved cleanly** — `regime_gate_v1.py:181-185` silent zero-mask fallback replaced with hard ValueError + `data_filter_columns` parameter wires funding column into LightGBM training filter; /024-A re-ran with same config; verdict FINAL after one rerun per BLOCK-PENDING-FIX protocol.

---

## 7. Specific Phase 8 diary requirements derived from this memo

The Phase 8 diary must:

1. **Document the dispatch defect** as a new feedback memory entry (`feedback_v1_dispatch_defect_silent_fallback.md`) — silent zero-mask fallback was the root cause; codify "hard-raise on missing column" as Phase 4.5 / 6.0 precondition checklist item.

2. **Document the regime-partition non-specialization finding** as a new feedback memory entry (`feedback_v1_regime_partition_non_specialization.md`) — F-AXIS #5 FAIL 2/3 cohorts extends /021 H2 REFUTED basin-interaction finding to sub-model level. Future regime-partition axes require multi-seed OR larger extreme partition OR /027+ CONFIRMATION budget.

3. **Update exploration_catalog.md** with /024 row per established schema.

4. **Apply tag `v0.v1-024`** on HEAD `1e5f7bc`.

5. **Brief Section 13 self-check addendum** documenting:
   - Verdict cell collision Row 4 + Row 7 — pre-registered band binding produced NEGATIVE clean despite F-AXIS #1 dispatch correctness PASS.
   - F-AXIS #5 gain-share recurrence empirically validated as INERT-detector.
   - LM Master Phase 4.5 §3 methodology call LOAD-BEARING; track 5/5 PERFECT.
   - Dispatch defect catalogued as a NEW failure mode (silent fallback).
   - /025 axis selection: OI delta family per CONVERGENT routing.
