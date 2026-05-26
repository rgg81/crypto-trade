---
iteration: iter-v1/022
date: 2026-05-26
verdict: EXPLORATION-NEGATIVE-CATASTROPHIC
subtype: Section 8 Row 6 (F1 OOS Sharpe Δ -1.17 ≤ -0.55 threshold; F-AXIS-MECHANISM #1-4 ALL PASS yet F1 catastrophic — mechanism ≠ outcome; basin relocation dissolved the asymmetry the gate targeted)
axis_family: per-cohort-specialization-LTC (NEW 14th family — FIRST usage; FOURTH per-cohort EXPLORATION under USER STRATEGIC PIVOT after LINK /018 + ETH+gate /019 + BTC /020)
cohort: LTC (single-symbol cohort, Model D' exclusive dispatch via V1_ITER022_UNIVERSE=(LTCUSDT,))
specialization: stateless asymmetric long-suppress BTC-trend regime gate at threshold -4% (one-sided variant of /019 ETH primitive; long_only_mode=True kwarg added backward-compatibly to risk_v2.BtcTrendFilterConfig)
cadence_position: cycle-3 EXPLORATION (#7 of 10)
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c) — UNCHANGED
merge_decision: NO-MERGE (EXPLORATION-NEGATIVE-CATASTROPHIC; LTC-only Model D' specialist EXCLUDED from /027 substrate; LTC enters /027 IN POOL via Model D; BASELINE_V1.md UPDATE NOT triggered — only CONFIRMATION-MERGE updates baseline per `feedback_v3_baseline_update_policy.md`)
---

# Iteration iter-v1/022 — Diary

## 1. Decision: NO-MERGE (EXPLORATION-NEGATIVE-CATASTROPHIC; LTC-only Model D' specialist EXCLUDED from /027 substrate; LTC enters /027 IN POOL via Model D)

**EXPLORATION-NEGATIVE-CATASTROPHIC** (FINAL after BLOCK-PENDING-FIX engineering_report.md fix at `d6afb68`; Critic Phase 7.5 FINAL verdict `0c8602d`). LTC-only single-symbol cohort dispatch through Model D' + asymmetric long-suppress BTC-trend regime gate at threshold -4% (long_only_mode=True one-sided variant of /019 ETH primitive) **DISSOLVED the targeted asymmetry under basin relocation** at single-seed=42 EXPLORATION budget. F1 OOS Sharpe Δ **-1.17** (2.1× the -0.55 catastrophic floor; Section 8 Row 6 DECISIVE) / OOS Sharpe **-1.4407** annualized daily vs anchor proxy -0.27 / OOS net PnL -33.99% (vs baseline LTC-in-pool OOS -47.25%, Δ +13.26pp) / 48 OOS trades / **F-AXIS-MECHANISM #1+#2+#3+#4 ALL PASS** / **Jaccard 0.10 IS / 0.093 OOS** confirms basin relocation (~90% new roster on both windows) INTO structurally adverse OOS subset where the 89% baseline OOS long-direction drag dissolved to 76% long / 24% short. BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). **LTC-only Model D' specialist EXCLUDED from /027 substrate**; LTC enters /027 IN POOL via Model D (no architectural change vs baseline for LTC). **/023 advances to NEW-family axis: funding-rate z-score feature** per Critic Phase 7.5 §Path Forward #1 + LM Master Phase 7.4 §5 STRONGEST recommendation + QR Phase 7 self-assessment 3-way CONVERGENT routing. **SECOND consecutive ASYMMETRIC_ROTATION cohort catastrophe** in cycle-3 (after /020 BTC at -0.86) — pattern confirmed at n=2; per-cohort isolation axis SATURATED for ASYMMETRIC_ROTATION cohorts regardless of gate symmetry; new memory rule `feedback_v1_per_cohort_saturation_asymmetric_rotation.md` codifies the binding.

## 2. Headline Numbers

| Metric | Value | Note |
|---|---|---|
| **F1 OOS Sharpe Δ** | **−1.17** | vs anchor proxy −0.27; **2.1× catastrophic floor −0.55**; Section 8 Row 6 DECISIVE |
| OOS Sharpe (daily-annualized) | **−1.4407** | comparison.csv binding |
| IS Sharpe (daily-annualized) | −0.0046 | flat — IS basin sign flipped from baseline marginal-positive |
| OOS Total Net PnL | −33.99% | vs baseline LTC-in-pool OOS −47.25% (Δ +13.26pp; gate did remove SOME drag) |
| IS Total Net PnL | −0.32% | vs baseline LTC-in-pool IS +3.27% (Δ −3.59pp) |
| OOS trades | **48** | inside QR [20, 60] + LM [18, 50] band PASS |
| IS trades | **117** | inside QR [80, 180] + LM [70, 160] band PASS |
| F-AXIS-MECHANISM #1 dispatch | **PASS** (100% LTCUSDT) | `df['symbol'].unique() == ['LTCUSDT']` ✓ |
| F-AXIS-MECHANISM #2 trade count | **PASS both bands** | QR + LM inside both |
| F-AXIS-MECHANISM #3 gate fire IS | **17.95% (21/117) PASS** | inside [15%, 40%] LOAD-BEARING |
| F-AXIS-MECHANISM #3 gate fire OOS | **29.17% (14/48) PASS** | inside [5%, 30%] LOAD-BEARING (near top) |
| F-AXIS-MECHANISM #4 n_eff_per_cell | **8 EXACT HIT** | LM Master modal 8 |
| **Jaccard IS (vs baseline LTC-in-pool)** | **0.1005 (22/219)** | inside LM [0.03, 0.20] |
| **Jaccard OOS (vs baseline LTC-in-pool)** | **0.0933 (7/75)** | inside LM [0.03, 0.20] |
| PSR_monthly_vs_0 OOS | 0.0112 | below 0.10 floor (catastrophic) |
| DSR | −18.35 | informational EXPLORATION-mode |
| Wall-clock | 541 s (~9 min) | 80% margin against 45-min kill-switch |

### F-AXIS-MECHANISM RECONCILIATION TABLE — ALL 4 PASS yet F1 CATASTROPHIC

| Falsifier | Pre-registered criterion | Observed | Outcome |
|---|---|---|---|
| F-AXIS #1 dispatch | `trades.csv symbol unique == {LTCUSDT}` | 117 IS + 48 OOS all LTCUSDT | **PASS** |
| F-AXIS #2 IS trade count | QR [80, 180] / LM [70, 160] | 117 | **PASS both bands** |
| F-AXIS #2 OOS trade count | QR [20, 60] / LM [18, 50] | 48 | **PASS both bands** |
| F-AXIS #3 IS gate fire rate | [15%, 40%] LOAD-BEARING | 17.95% (21/117) | **PASS** |
| F-AXIS #3 OOS gate fire rate | [5%, 30%] LOAD-BEARING | 29.17% (14/48) | **PASS (near top)** |
| F-AXIS #4 n_eff | LM modal 8 / band [6, 10] | 8 | **PASS EXACT** |
| **F1 OOS daily-annualized Sharpe Δ** | **≤ −0.55 → NEG-CAT** | **−1.17** | **NEGATIVE-CATASTROPHIC** |
| F3 IS Sharpe Δ | INERT band | ≈ +0.005 (near zero) | INERT |
| F5 PSR OOS monthly vs 0 | ≥ 0.10 floor | 0.0112 | FAIL catastrophic |
| F7 sign agreement | IS + OOS both positive | IS −0.32% / OOS −33.99% | FAIL |

**Key observation**: ALL 4 F-AXIS-MECHANISM checks PASS — the gate operated exactly within pre-registered bands. Yet F1 catastrophic. This is exactly the diagnostic scenario LM Master pre-registered at Phase 4.5 §8: "F-AXIS #3 LOAD-BEARING disambiguator, not F1 magnitude — anchor at extreme negative reduces F1 diagnostic power around INERT/NEGATIVE boundary." **Mechanism ≠ outcome.**

## 3. Per-Cohort SATURATION rule (BTC + LTC pattern at n=2)

### The empirical pattern across 4 cycle-3 per-cohort EXPLORATIONs

| Cohort | Iter | Prior class | Mechanism | F1 OOS Sharpe Δ | Verdict |
|---|---|---|---|---:|---|
| LINK | /018 | POSITIVE_EVERYWHERE | Pure isolation | +0.16 (multi-seed target +0.80) | PROMISING-INERT-FAVORABLE |
| ETH | /019 | Counter-trend OOS drag (symmetric) | ±8% symmetric BTC-trend gate | +0.65 (multi-seed target +0.50) | PROMISING |
| **BTC** | **/020** | **ASYMMETRIC_ROTATION (IS-NEG/OOS-POS)** | **Pure isolation** | **−0.86** | **NEGATIVE-CATASTROPHIC** |
| **LTC** | **/022** | **ASYMMETRIC_ROTATION-INVERSE (IS-MARGINAL/OOS-CAT)** | **Asymmetric long-suppress gate @ −4%** | **−1.17** | **NEGATIVE-CATASTROPHIC** |

### The rule (codified at /022 closeout)

**Per-cohort single-cohort isolation is STRUCTURALLY INVIABLE for ASYMMETRIC_ROTATION cohorts at current single-seed EXPLORATION budget (ENSEMBLE_SIZE=3, n_trials=18, seed=42) — regardless of whether an orthogonal mechanism is added on top of isolation, and regardless of gate symmetry.**

- **POSITIVE_EVERYWHERE cohorts** (LINK pattern): isolation alone PRESERVED OOS positive prior. Pool NOT load-bearing.
- **Counter-trend-symmetric cohorts** (ETH pattern: negative-prior + symmetric counter-trend drag): isolation + ±8% SYMMETRIC gate DISSOLVED OOS negative drag. Gate is load-bearing AND symmetric mechanism matches the symmetric drag structure.
- **ASYMMETRIC_ROTATION cohorts** (BTC + LTC pattern: pool-conferred positive rotation OR direction-asymmetric drag): isolation alone (BTC /020) OR isolation + asymmetric one-sided gate (LTC /022) BOTH catastrophic. The basin relocation dissolves the asymmetry on which any gate's targeting depends.

### The mechanism story (load-bearing for /023+)

The asymmetric long-suppress gate at /022 fired within pre-registered fire-rate band (17.95% IS / 29.17% OOS) AND fired at the wrong trades. Targeting mechanisms operate at TRADE-ROSTER level by construction:

- The 89% long-direction drag was a property of the **baseline LTC-in-pool basin**.
- /022 single-cohort retraining produced a ~90% NEW roster (Jaccard 0.10 IS / 0.093 OOS — only 7 of baseline's 34 OOS LTC trades survived).
- In the retrained basin, the asymmetry DISSOLVED: /022 IS longs +44.54% / IS shorts +23.00% (both positive); /022 OOS long drag −26.54% / short drag −8.34% (76% long vs 96% baseline).
- The gate by design (long_only_mode=True) cannot touch short-direction trades. Even at 29.17% OOS fire rate (heavy long engagement), it leaves the −8.34% short drag untouched.

The ORACLE EDA projected +12.45% OOS PnL Δ on the baseline 34-trade roster — descriptively true (it would have removed the right trades) but operationally irrelevant for the retrained basin's 48-trade roster (79% non-overlap).

### Codified mandates for /023+ briefs

Per NEW memory `feedback_v1_per_cohort_saturation_asymmetric_rotation.md`:

1. Future v1 single-cohort EXPLORATIONs MUST pre-classify cohort prior class BEFORE proposing the axis. Brief Section 0.4 mandatory.
2. ASYMMETRIC_ROTATION cohorts (any variant — pool-conferred positive rotation OR direction-asymmetric drag) go IN POOL. Future per-cohort axes target POSITIVE_EVERYWHERE or counter-trend-symmetric cohorts only.
3. DOT pre-classification MANDATORY before any further per-cohort consideration. If DOT class = ASYMMETRIC_ROTATION, predict NEG-CAT a third time; do NOT default /023 to DOT-only.
4. After 5 same-family iterations within per-cohort-specialization-X (now /018-/020 + /022 = 4 of those used; /023 mandatorily rotates to NEW family per axis rotation discipline AND saturation rule).

## 4. /027 Bundle Update: 2 specialists confirmed; BTC + LTC drop OUT as specialists, stay IN POOL

Post-/022, the /027 substrate is settled to 2-specialist configuration:

| Component | Provenance | Bundle role | Status | Multi-seed Δ target |
|---|---|---|---|---|
| Pool baseline (5 sym, A/C/D/E unchanged) | BASELINE_V1.md | Pool anchor | LOCKED | 0 |
| LINK-only specialist (Model C) | /018 PROMISING-INERT-FAVORABLE | Alpha-enhancement | LOCKED | **+0.80** |
| ETH-only + symmetric BTC-trend gate (Model G) | /019 PROMISING | Alpha-enhancement | LOCKED | **+0.50** |
| **BTC** (in pool via Model A) | **/020 NEG-CAT EXCLUDED** | **Pool baseline only** | **LOCKED** | — |
| **LTC** (in pool via Model D) | **/022 NEG-CAT EXCLUDED** | **Pool baseline only — NEW LOCK at /022 closeout** | **LOCKED** | — |
| DOT (TBD /023+ routing) | pending NEW-family axis | TBD | PENDING | TBD |

**Bundle target at /027 multi-seed**: 2-specialist nominal Σ = +1.30 if independent; realistic with correlation drag + multi-seed variance reduction = **+1.10 to +1.30 OOS Sharpe** (per /021 §7 + LM Master /022 §6 unchanged). Sharpe 1.0 floor merge gate: REQUIRES multi-seed mean ≥ +1.0 OOS Sharpe.

**Two consecutive NEG-CAT outcomes (/020 + /022) SUBTRACTED two candidate specialists but did NOT poison the pool.** BTC + LTC enter /027 IN POOL via Model A + Model D respectively — no architectural change vs baseline for either. The pool basin (5-sym joint loss surface) is load-bearing for BOTH cohorts (pool-conferred OOS rotation for BTC; pool-conferred IS marginal-positive containment for LTC).

Cross-correlation < 0.40 between LINK and ETH+gate specialist Sharpe paths still required at /027 multi-seed (Critic /019 Rec #3 pre-validation pre-registered). DOT slot remains TBD pending /023 routing.

## 5. Track Record: LM Master priors better-calibrated than QR (NEG tail 40% vs 30%)

### LM Master directional + methodology track (post-/022)

| Iteration | Modal verdict prediction | Observed | Directional score | Methodology score |
|---|---|---|:---:|:---:|
| /018 | PROMISING-INERT favorable | PROMISING-INERT-FAVORABLE | 1/1 | 1/1 |
| /019 | PROMISING modal 35% | PROMISING | 1/1 | 1/1 |
| /020 | INERT-no-effect modal 40% | NEGATIVE-CATASTROPHIC | 0/1 | 1/1 (n_eff = 9 exact) |
| /021 H1 (45/40/15) | CONFIRMED 45% modal | CONFIRMED BORDERLINE | 0.5/1 | 1/1 (Layer A/C PASS) |
| /021 H2 (70/20/10) | CONFIRMED-H2 70% | REFUTED-H2 (10% tail) | 0/1 | — |
| **/022 (8/12/40/20/10/10)** | **INERT modal 40%** | **NEGATIVE-CATASTROPHIC (10% tail)** | **0/1 (modal off; tail directionally correct)** | **1/1 (6/6 micro-mechanics hit)** |

**Running totals post-/022**:
- **Directional**: 1.5/6 → **25% directional accuracy** (modal misses continue at single-seed EXPLORATION on cohorts with non-POSITIVE_EVERYWHERE priors — but tail recalibrations vindicated)
- **Methodology**: 3/3 → **4/4 = 100%** (perfect — /022 mechanism-level prediction 6/6 hit including F-AXIS #3 LOAD-BEARING designation that vindicated the "mechanism ≠ outcome" hypothesis)

### The pattern: LM Master tail upweighting reliably directionally correct at non-POSITIVE_EVERYWHERE cohort priors

| Iter | QR initial NEG tail | LM Master NEG tail | Observed |
|---|---:|---:|---|
| /020 | (LM Master's tail at 40% modal INERT REFUTED) | INERT 60% modal REFUTED | NEG-CAT 2% tail materialized — LM tighter range REFUTED |
| **/022** | **NEG tail 30%** | **NEG tail 40% (+10pp)** | **NEG-CAT 10% tail materialized — LM tail captures, QR doesn't** |

LM Master Phase 4.5 §3 explicit rationale: (a) ASYMMETRIC threshold tuning IS harder than symmetric; (b) /020 BTC ASYMMETRIC_ROTATION precedent applies to LTC equally; (c) PROMISING tail at 25% requires basin to land favorably AND gate efficacy to be at upper EDA estimate.

**Lesson for /023+ briefs**: at single-seed EXPLORATION budget on cohorts with non-POSITIVE_EVERYWHERE priors, LM Master's negative-tail upweighting is reliably directionally correct. QR should adopt LM Master priors over initial QR pass.

### Verdict-class directional + mechanism-level tracks

- **Verdict-class directional**: 4/19 → 4/20 (no new directional hit; modal INERT 40% prior REFUTED with 10% NEG-CAT tail materializing — LM Master tail captures)
- **Mechanism-level**: 10/19 → **11/20** (NEW Critic Phase 7.5 FINAL PASS post-BLOCK-PENDING-FIX rerun; F-AXIS-MECHANISM 4/4 PASS; engineering report retrospective rebuild PASS; anchor-frame ambiguity DOCUMENTED + ELEVATED to BINDING)

## 6. /023 staging — funding-rate axis (Critic + LM Master CONVERGENT)

Per Critic Phase 7.5 review.md §"Path Forward" + LM Master Phase 7.4 §5 STRONGEST recommendation + QR Phase 7 evaluation §6 CONVERGENT routing:

### /023 PRIMARY axis: Funding-rate z-score (family `feature-family`)

| Candidate | Family | Critic preference | LM Master preference | QR Phase 7 |
|---|---|:---:|:---:|:---:|
| **Funding-rate z-score (8h funding)** | `feature-family` | **#1 PRIMARY** | **#1 STRONGEST** | **#1 CONCUR** |
| Per-cohort drawdown brake | `risk-primitive` | #2 (STATEFUL — deadlock proof) | #2 (symptomatic) | #2 CONCUR |
| Meta-labeling architecture | `labeling` | #3 (v3/017 NEG PATH C) | not listed | #3 (FALLBACK) |

### Why funding-rate is PRIMARY (3-way convergent)

1. **NEW signal source** — v1 LightGBM has never had access. Encodes positioning crowding that no OHLCV feature captures.
2. **Stateless** — no state propagation, no deadlock risk. Rolling-window z-score of published 8h funding rate.
3. **Production-proven** — BIS WP 1087 (2025): 10% carry shock → 22% liquidation jump. 8h candle = exactly one funding period — alignment exact.
4. **Sidesteps per-cohort saturation** — global-axis feature, used by all 5 pool symbols + LINK + ETH specialists.
5. **Cycle-3 budget unused** — feature-family axis NOT touched in cycle-3 to date. Per `feedback_v3_structural_over_knob_exploration.md`: NEW feature families > NEW model arch > NEW labeling > NEW risk primitive > universe > gate knobs.

### Falsifier pre-registration for /023 brief (recommended carry-forward)

- **Falsifier #1**: importance rank ≥ 30% (top quartile) on ≥ 2 cohorts at IS using per-month FI accumulator from /021. If funding-rate features rank below top-quartile on all 5 cohorts → INERT.
- **Falsifier #2**: OOS Sharpe Δ ≥ +0.10 over /021 baseline (matching daily-annualized comparison.csv "sharpe" semantics — anchor-frame locked per /022 binding).
- **Falsifier #3 (catastrophic floor)**: OOS Sharpe Δ ≤ −0.55 → NEGATIVE-CATASTROPHIC; 3 catastrophes in cycle-3 would trigger HIGH-RISK declaration mandatory multi-seed validation.

### DOT pre-classification MANDATORY before any further per-cohort consideration

Per LM Master Phase 7.4 §4 + Critic review.md §Path Forward + saturation rule (NEW memory): if /023 considers per-cohort or includes DOT-only as alternative, DOT prior class MUST be pre-classified using the same `_classify_LTC()`-style framework as /022 Section 0.3. If DOT = POSITIVE_EVERYWHERE/MILD_PROMISING → isolation viable. If DOT = ASYMMETRIC_ROTATION → predict NEG-CAT a third time; do NOT default /023 to DOT-only.

## 7. Process incidents: 4th cycle-3 engineering_report violation (RE-VIOLATION post-/021 RESOLVED)

### The incident (Critic BLOCK-PENDING-FIX at `53dffd4`)

Per brief Section 10.4 binding pre-commitment: "no Phase 7.5 Critic dispatch without engineering_report.md present (Critic /020/021 Rec #1 BINDING)". At Phase 7.5 dispatch on `374bf39` (post-Phase-7.4 LM Master post-mortem), `reports-v1/iteration_v1-022/engineering_report.md` was **MISSING**. Critic emitted BLOCK-PENDING-FIX at `53dffd4`.

This is the **4th cycle-3 engineering_report contract incident**:
- /019: engineering_report.md missing at Phase 7.5 dispatch
- /020: engineering_report.md missing at Phase 7.5 dispatch (Critic Rec #1 — 2nd cycle-3 incident)
- /021: initial commit missing; resolved at BLOCK-PENDING-FIX rerun (commit `502d66e`) — 3rd cycle-3 incident "RESOLVED"
- **/022: engineering_report.md missing at Phase 7.5 dispatch — RE-VIOLATION post-/021 resolution**

### Resolution

Per BLOCK-PENDING-FIX protocol: retrospective engineering_report.md written from existing CSVs at commit `d6afb68` (zero backtest re-run; zero src/ changes; 37 tests still PASS). The 287-line report:
- Verifies all 11 BLOCK-PENDING-FIX checkpoint items.
- Documents the F-AXIS-MECHANISM #1-4 reconciliation table (all 4 PASS).
- Reconciles ORACLE EDA against observed −1.17 (7/34 baseline trades survive into /022 OOS).
- Documents the basin-vector gap (params_persist_path NOT wired in /022 elif branch — brief Section 3.1 vs Section 10.6 internal inconsistency).
- Documents the feature_importance gap (`_iter021_fi_strategies` literal fragile; brief Section 3.1 spec incomplete).
- Codifies per-cohort SATURATION rule (LINK/ETH/BTC/LTC partition table).
- Documents anchor-frame ambiguity carry-forward (ELEVATED to BINDING for /023).

Critic re-evaluated at `0c8602d` (single-pass post-fix per BLOCK-PENDING-FIX protocol) and emitted FINAL verdict EXPLORATION-NEGATIVE-CATASTROPHIC. **Defect axis (report content completeness) PASS; Empirical verdict LOCKED at NEGATIVE-CATASTROPHIC.**

### Carry-forward action (NOT QR scope this iteration)

Per Critic Phase 7.5 FINAL Recommendation #1 (CARRY-FORWARD from /020 + /021):

> **Engineering-report contract — codify NON-RETROSPECTIVE-FORGIVENESS at orchestrator dispatch level**, not just brief prose. The brief pre-committed; /019/020/022 all violated. Move the gate to the orchestrator.

This is a SKILL-LAYER / ORCHESTRATOR fix, NOT a brief-level fix. The brief Section 10.4 contract pre-commitment is necessary but not sufficient; 4 incidents across 4 iterations confirms brief-level contracts cannot enforce. Next action for orchestrator/skill maintainer: gate Phase 7.5 dispatch on file existence check at the dispatch-level (orchestrator layer), with NON-RETROSPECTIVE-FORGIVENESS — engineering_report.md missing at Phase 7.5 dispatch becomes BLOCK-PENDING-FIX automatically without Critic intervention.

### Brief Section 13 self-check addendum (post-closeout calibration)

A Phase 7+8 self-check addendum will be appended to `briefs-v1/iteration_v1-022/research_brief.md` Section 13 documenting:
- Pre-registered verdict priors vs observed (NEG-CAT 10% tail materialized)
- F-AXIS-MECHANISM 4/4 PASS vs F1 catastrophic (mechanism ≠ outcome)
- LM Master Phase 4.5 priors directional credit (NEG tail upweighting vindicated)
- Engineering report contract 4th cycle-3 incident
- Anchor-frame ambiguity discovered + ELEVATED to BINDING
- Per-cohort SATURATION rule codified at n=2

## 8. Merge Decision: NO-MERGE

**NO-MERGE (EXPLORATION-NEGATIVE-CATASTROPHIC; BASELINE_V1 UNCHANGED)**.

BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). The /022 iteration produces:
- **No new edge ingredient for /027 bundling** — LTC-only Model D' specialist EXCLUDED per NEG-CAT verdict.
- **LTC stays IN POOL** at /027 via Model D — no architectural change vs baseline for LTC.
- **Two structural findings carrying forward** (codified at /022 closeout):
  - NEW memory `feedback_v1_per_cohort_saturation_asymmetric_rotation.md` — per-cohort isolation SATURATED for ASYMMETRIC_ROTATION cohorts at n=2 (BTC + LTC).
  - Anchor-frame ambiguity ELEVATED to BINDING for /023 — pre-compute daily-annualized Sharpe; lock to comparison.csv "sharpe" semantics.
- **Two src/ changes from /022** (the asymmetric long-suppress gate + LTC-only dispatch branch):
  - `run_baseline_v1.py:V1_ITER022_UNIVERSE` + gate constants + elif dispatch branch (~80 lines) — STAYS on branch; NOT merged to trunk because LTC-only Model D' specialist EXCLUDED.
  - `src/crypto_trade/strategies/ml/risk_v2.py:BtcTrendFilterConfig.long_only_mode` kwarg (~10 lines) — BACKWARD-COMPATIBLE addition (default `long_only_mode=False`); merges to trunk via branch HEAD as pure additive infrastructure (no defaults changed). Future iterations can use `long_only_mode=True` if a viable asymmetric-gate use case emerges.

**Trunk merge**: The `risk_v2.long_only_mode` kwarg is backward-compatible additive infrastructure; merges to trunk via branch HEAD. The `run_baseline_v1.py:V1_ITER022_UNIVERSE` dispatch branch is opt-in (not invoked at default baseline), so it can stay on branch without harming trunk. Per `feedback_v3_baseline_update_policy.md` adopted by v1: BASELINE_V1.md UPDATE NOT triggered (EXPLORATION-NEGATIVE-CATASTROPHIC; only CONFIRMATION-MERGE updates baseline).

**Tag**: `v0.v1-022` to be applied after this Phase 8 closeout commit.

## 9. Cycle-3 Cadence Status (after /022)

- **Cycle-3 EXPLORATION count**: **7 of 10** (3 more before /027 CONFIRMATION earliest)
- **CONFIRMATION earliest**: **/027** (assuming sequential EXPLORATIONs /023-/025 + sanity /026)
- **Edge ingredients merged this cycle**: **0** — LINK-only specialist + ETH+gate specialist are CONDITIONAL carry-forwards to /027 substrate; /020 BTC-only EXCLUDED; **/022 LTC-only EXCLUDED**; /021 methodology pivot PROMISING-METHODOLOGY non-compoundable
- **Verdict distribution cycle-3 post-/022**:
  - 1 EXPLORATION-NEGATIVE catastrophic (/016)
  - 1 EXPLORATION-NEGATIVE anti-direction-INERT (/017)
  - 1 EXPLORATION-PROMISING favorable-INERT (/018)
  - 1 EXPLORATION-PROMISING (/019)
  - 1 EXPLORATION-NEGATIVE-CATASTROPHIC (/020)
  - 1 EXPLORATION-PROMISING-METHODOLOGY (/021)
  - **1 EXPLORATION-NEGATIVE-CATASTROPHIC (/022)** ← second cycle-3 NEG-CAT
  - = 2 PROMISING + 1 PROMISING-METHODOLOGY + 2 NEGATIVE clean + **2 NEGATIVE-CATASTROPHIC** across 7 cycle-3 EXPLORATIONs
- **BASELINE_V1.md unchanged** at `v0.v1-baseline-corrected` (`f8bc12c`)
- **Per-cohort axis SATURATED for ASYMMETRIC_ROTATION cohorts** (n=2 confirmation /020 + /022); future single-cohort EXPLORATIONs gated on prior-class screening
- **Engineering report contract 4th cycle-3 incident** — orchestrator-layer fix required (NOT QR scope)

## 10. Path Forward (from Critic — Phase 7.5 FINAL recommendations)

Verbatim from `briefs-v1/iteration_v1-022/review.md` §"Recommendations to QR (for /023)" + §"Path Forward":

> ### Recommendations to QR (for /023, unchanged from Round 3)
>
> 1. **Engineering-report contract — codify NON-RETROSPECTIVE-FORGIVENESS at orchestrator dispatch level**, not just brief prose. The brief pre-committed; /019/020/022 all violated. Move the gate to the orchestrator.
>
> 2. **Feature_importance generalization**: refactor `run_baseline_v1.py:1902` to use generic `_post_dispatch_fi_strategies` list. Current `_iter021_fi_strategies` literal is fragile.
>
> 3. **Anchor-frame formalization** (CARRY-FORWARD from /020 Rec #2 → /022 Rec #3, now ELEVATED to BINDING for /023): pre-compute per-cohort daily-annualized Sharpe directly on baseline roster; lock F1 frame to comparison.csv "sharpe" semantics.
>
> ### Path Forward (mandatory; carry-forward from Round 3)
>
> Per-cohort axis SATURATED for ASYMMETRIC_ROTATION cohorts. /023 MANDATORY from non-per-cohort families:
>
> 1. **Funding-rate z-score (8h funding) — family `feature-family`** [PRIMARY]. NEW signal source; stateless; v1 LightGBM never had access.
>
> 2. **Per-cohort drawdown brake — family `risk-primitive`**. STATEFUL → MANDATORY deadlock-impossibility proof per A8 + iter-v3/054.
>
> 3. **Meta-labeling architecture — family `labeling`**. AFML Ch. 3 secondary model. Risk: v3/017 NEGATIVE PATH C.
>
> Critic CONCURS with LM Master ordering: funding-rate > drawdown-brake > meta-labeling. DOT pre-classification MANDATORY before any further per-cohort consideration.

## 11. Next Iteration Ideas

### /023 (PRIMARY per Critic + LM Master + QR 3-way CONVERGENT)

**/023 = funding-rate z-score axis** — family `feature-family`. NEW signal source; v1 LightGBM never had access; stateless; production-proven (BIS WP 1087 + Crypto Carry literature); sidesteps per-cohort saturation; cycle-3 feature-family budget unused. Add funding-rate features (raw rate, 8/24/72h momentum, z-score rolling 30 candles, premium index) to V1_FEATURE_COLUMNS_PRUNED. Wall-clock estimate ~30-45 min (data fetch + feature regen + standard backtest).

Cadence preserved at 7/10; 8/10 after /023.

### /024-/025 (FLEXIBLE per /023 verdict)

Per Critic Path Forward + LM Master §5:

- **/024 candidate axis A (if /023 PROMISING)**: continue with funding-rate variations OR open-interest delta (sister NEW feature family from same edge taxonomy).
- **/024 candidate axis B (if /023 NEGATIVE/INERT)**: per-cohort drawdown brake — family `risk-primitive`. Binary off/on at -25% per-cohort cumulative loss; pre-commit deadlock-impossibility proof per A8 catalog + iter-v3/054 lesson.
- **/024 candidate axis C (long-tail)**: meta-labeling architecture — family `labeling`. AFML Ch. 3 secondary model. Higher risk (v3/017 NEGATIVE PATH C precedent).

### /026 = pre-CONFIRMATION sanity (FINAL EXPLORATION)

Layer B determinism re-verification at /027 multi-seed config; final brief Section 11.7 routing matrix verification; engineering report contract re-confirmation; anchor-frame BINDING locked.

### /027 CONFIRMATION (Option β PRE-COMMITTED per /021 §7)

Bundle architecture: FULL POOL (5 sym unchanged — A/C/D/E baseline) + 2 alpha-enhancement specialists (LINK + ETH+gate). BTC + LTC + DOT in pool unless /023+ produces specialist candidate. Multi-seed n_seeds ≥ 5 per `feedback_v1_seed_count_non_negotiable.md`. Pre-compute BTC-in-pool + LTC-in-pool annualized-daily-Sharpe directly (no proxy) per anchor-frame BINDING. Bundle ceiling **+1.10-1.30 OOS Sharpe** at 2-specialist baseline.

## 12. Axis Rotation Status (v1-only)

- **This iter's family**: `per-cohort-specialization-LTC` (NEW 14th family — FIRST usage; FOURTH per-cohort EXPLORATION at v1 catalog level)
- **Prior 5 EXPLORATION families** (going INTO /022): universe (/017), per-cohort-specialization-LINK (/018), per-cohort-specialization-ETH (/019), per-cohort-specialization-BTC (/020), methodology-pivot (/021)
- **Rotation honored**: YES — `per-cohort-specialization-LTC` is in NONE of the prior 5 (different COHORT from LINK/ETH/BTC per per-cohort methodology — rotation by cohort, not by family literal-name)
- **Updated prior 5 going into /023**: per-cohort-specialization-LINK (/018), per-cohort-specialization-ETH (/019), per-cohort-specialization-BTC (/020), methodology-pivot (/021), **per-cohort-specialization-LTC (/022)**
- **/023 axis-family (per Critic + LM Master + QR 3-way CONVERGENT)**: `feature-family` (NEW feature axis — funding-rate z-score; NOT touched in cycle-3 to date; rotation VALID — not in prior 5; also mandated per saturation rule: per-cohort axis SATURATED for ASYMMETRIC_ROTATION cohorts)

## 13. Files & Commits on Branch

- Branch: `iteration-v1/022` from `iter-v1/021` closeout (tag `v0.v1-021`)
- HEAD at QR Phases 1-4 + EDA: `4eb091d`
- HEAD at QR Phases 1-5 brief: `a8166d8`
- HEAD at LM Master Phase 4.5 advisory: `79fd7fa`
- HEAD at Brief Section 3.4 LM Master responses: `3852147`
- HEAD at Phase 5.5 gate PASS: `cee2ada`
- HEAD at QE implementation + dispatch: `ef8d605`
- HEAD at Phase 6.0 Critic pre-flight PASS: `84ef271`
- HEAD at LM Master Phase 7.4 post-mortem: `374bf39`
- HEAD at Critic Phase 7.5 BLOCK-PENDING-FIX initial review: `53dffd4`
- HEAD at BLOCK-PENDING-FIX engineering_report.md retrospective fix: `d6afb68`
- HEAD at Critic Phase 7.5 FINAL (post-fix): `0c8602d`
- HEAD at Phase 7 evaluation memo: TBD (this closeout commit batch)
- HEAD at Phase 8 closeout (THIS COMMIT): TBD (this closeout commit batch)
- Reports artifacts in `reports-v1/iteration_v1-022/`

Key commits in /022:
- `4eb091d` — feat: EDA — LTC prior class classification + mechanism candidates
- `a8166d8` — docs: QR Phases 1-5 + per-cohort-specialization-LTC brief
- `79fd7fa` — docs: Phase 4.5 LM Master advisory
- `3852147` — docs: Section 3.4 LM Master responses + prior adjustments
- `cee2ada` — docs: phase 5.5 gate PASS
- `ef8d605` — feat: LTC-only specialization + asymmetric long-suppress BTC-trend gate
- `84ef271` — docs: Phase 6.0 Critic pre-flight PASS
- `374bf39` — docs: Phase 7.4 LM Master post-mortem — NEGATIVE-CATASTROPHIC
- `53dffd4` — docs: Phase 7.5 Critic review — BLOCK-PENDING-FIX
- `d6afb68` — docs: engineering_report.md retrospective (Critic BLOCK-PENDING-FIX)
- `0c8602d` — docs: Phase 7.5 FINAL — EXPLORATION-NEGATIVE-CATASTROPHIC
- (Phase 7 evaluation memo this commit batch) — `briefs-v1/iteration_v1-022/phase7_evaluation.md`
- (Phase 8 closeout this commit batch) — Phase 8 diary + merge decision (NO-MERGE)

**Trunk merge**: `risk_v2.long_only_mode` kwarg merges to trunk as pure additive backward-compatible infrastructure (default `long_only_mode=False`). `run_baseline_v1.py:V1_ITER022_UNIVERSE` + elif dispatch branch stays on branch (opt-in, not invoked at default baseline). BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`).

**Tag**: `v0.v1-022` to be applied after this Phase 8 closeout commit.
