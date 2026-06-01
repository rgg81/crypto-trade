# iter-v1/030 — Research Brief (Phase 5)

**Authored**: 2026-05-28
**Branch**: `iteration-v1/030`
**Cycle**: 4, EXPLORATION 3/10
**Anchor**: BASELINE_V1.md `v0.v1-baseline-corrected` (`f8bc12c`) — Portfolio IS Sharpe +0.2829 / OOS Sharpe +0.6637
**LM Master Phase 4.5** (`briefs-v1/iteration_v1-030/lgbm_advisor.md`, `43ee09a`): META-LABELING adjudication — modal NEGATIVE-OVER-FILTER 30% (+0.12-0.28 realistic OOS Sharpe Δ vs +58.55pp oracle headroom); 3 LOAD-BEARING calls (Model E DROP-or-UNIFY; n_trials_m2=18; Model D OOS TP-exit ≥ 3); v3/017 mirror precedent NEGATIVE-clean over-filter.

---

## Section 0 — Hypothesis Statement

**H1 (primary)**: A meta-labeling layer M2 (LGBMClassifier binary, **3 separate per-model classifiers for A/C/D; Model E EXCLUDED per LM Master sample-size mandate**) filtering M1's baseline trade roster will lift portfolio OOS Sharpe into the band **[-0.10, +0.55] modal +0.12 to +0.28** by vetoing identifiable systematic losers (top-3 worst (sym, direction) cells carry 37.0% of IS losses; oracle veto lift OOS +58.55pp PnL → realistic Sharpe-equivalent compressed +0.12-0.28 by 45-feature × 75-200 sample × n_trials_m2=18 information-theoretic capture limit). Single-shot architectural axis: if PROMISING fires (Δ ≥ +0.05), /031 = M2 threshold sweep (exploitation); if INERT/NEGATIVE, meta-labeling architecture CLOSED at v1; /031 = NEW funding-rate-z-scores feature family (per LM Master §7 PRE-COMMIT regardless of /030 verdict).

### 0.1 Cycle position

Cycle-4 EXPLORATION **3 of 10** (cycle-4 started at /028 post-/027 TF closeout). Precedents: /028 PROMISING +0.598 OOS Δ (LTC specialist + atr_sl=1.0 label-shift); /029 EXPLORATION-TECHNICAL-FAILURE (wall-clock cap breach at DOT cohort + symmetric BTC gate ±8% per LM Master §2.5 ESCALATE config; comparison.csv NEVER EMITTED). /030 is the **first cycle-4 NEW-axis-family iteration** per /029 §7 routing PRE-COMMIT (cohort-coverage CLOSED at /029; meta-labeling is NEW family UNUSED in v1 history). 7 EXPLORATIONs remain after /030; earliest CONFIRMATION at /037 (10 EXPLORATION precedents accumulate /028 forward).

### 0.2 LM Master Phase 4.5 coordination slot

LM Master (`43ee09a`) returned BINDING analysis: oracle headroom +58.55pp OOS PnL **compresses to +0.12-0.28 OOS Sharpe Δ modal** at proposed configuration. **Prior distribution** (current 4-separate-M2 spec): PROMISING-clean 15% / PROMISING-INERT-FAV 17% / INERT 22% / **NEG-OVER-FILTER 30% MODAL** / NEG-CAT 16%. Combined NEG 46% > combined PROMISING 32%.

**Three LM Master LOAD-BEARING calls**:
1. **Model E (DOT) M2 STRUCTURALLY TOO SMALL** at 75 cumulative samples × 45 features × n_trials_m2 (§1, §3, §9 Q2)
2. **n_trials_m2 = 18 NOT 10** (TPE warmup; +90 sec marginal cost) (§2, §9 Q3)
3. **Model D OOS TP-exit count ≥ 3 LOAD-BEARING** (transferred from /028 §6; LTC-long catastrophe pre-vet) (§5 F-AXIS #5)

**QR ADOPTS 4-separate-M2 with Model E DROPPED** (partial adoption of LM §3): honors AFML Ch.3 per-model dispatch for A/C/D while respecting sample-size minimum on E. Full LM Master Response Map in Section 3.4. UNIFIED-M2 (LM Master's STRONG recommendation) is filed as the explicit alternative path for /031 if /030 fires INERT.

### 0.3 Meta-labeling prior class (Phase 1 numerical evidence)

From `analysis/iteration_v1-030/meta_labeling_summary.csv` (committed `9f77760`):

| Metric | IS | OOS |
|---|---|---|
| Net PnL (baseline 5-model portfolio) | +50.98% | +24.87% |
| Total trades | 621 | 189 |
| Win rate | 39.9% | 40.2% |
| Oracle top-3 worst-cell veto lift PnL | **+77.87pp** | **+58.55pp** |
| Oracle top-3 veto rate | 31.88% | 29.63% |
| Oracle MAX veto (full ranking) lift | +93.32pp | +60.15pp |
| H1/H2 worst-3 cell overlap | — | **1/3 (MODERATE)** |

**Classification**: STRONG oracle headroom + MODERATE H1/H2 stability + UNUSED axis family. **LM Master HYBRID re-classification**: realistic-M2 captures 15-35% of oracle lift = +0.12-0.28 OOS Sharpe Δ modal (mechanism-binding compression at sample sizes 75-200 × 45 features × n_trials_m2=18).

### 0.4 Cycle-4 cadence ledger summary

Cycle-4 EXPLORATIONs to date:
1. /028 — per-cohort-specialization-LTC-v2 (atr_sl=1.0 LABEL-shift) → **PROMISING** +0.598 OOS Δ
2. /029 — per-cohort-specialization-DOT-v2 (symmetric BTC gate ±8%) → **EXPLORATION-TECHNICAL-FAILURE** (wall-clock cap breach)
3. /030 = THIS — meta-labeling (M2 binary per-model A/C/D; E DROPPED)

7 EXPLORATIONs remaining; CONFIRMATION earliest at /037.

### 0.5 LM Master prior distribution

LM Master adopted priors over 5 verdict cells (§4):
- PROMISING-clean (Δ ≥ +0.20): **15%**, modal +0.30, band [+0.20, +0.55]
- PROMISING-INERT-FAV (Δ +0.05 to +0.20): **17%**, modal +0.12, band [+0.05, +0.20]
- INERT-NO-EFFECT (Δ -0.10 to +0.10): **22%**, modal +0.00
- **NEGATIVE-OVER-FILTER (Δ -0.40 to -0.10): 30% MODAL**, modal -0.22 (v3/017 mirror)
- NEGATIVE-CATASTROPHIC (Δ ≤ -0.40): **16%**, modal -0.55

QR ADOPTS prior distribution verbatim with Model E DROPPED clarification: LM Master's prior table conditioned on "Model E retained" carries the heaviest NEG-CAT weight via Model E M2 misfires (75-sample lottery). By DROPPING Model E's M2, the NEG-CAT tail should compress ~3-5pp (LM Master §1 footnote: "If QR retains 4-separate with E included, my NEGATIVE-OVER tail weight raises 5pp"). QR adopts INTERMEDIATE prior between "4-separate w/ E" and "UNIFIED": PROMISING-clean 17%, PROMISING-INERT-FAV 18%, INERT 24%, **NEG-OVER 27%** (still MODAL), NEG-CAT 14%. **Modal verdict: NEGATIVE-OVER-FILTER 27%** with OOS Δ band centered -0.22. Combined PROMISING tail 35%; combined NEG tail 41%.

### 0.6 Axis Family Declaration + Rotation Discipline (v1 mandatory)

**This iter's family**: `meta-labeling` (NEW family — UNUSED in v1 across cycles 1, 2, 3). Family list: `feature-family`, `model-arch`, `labeling`, `universe`, `risk-primitive`, `methodology`, `hyperparameter-region`, `methodology-substrate-test`, `per-cohort-specialization*` family. **`meta-labeling` is a NEW NINTH family designation** distinct from labeling axis (which addresses M1's triple-barrier σ_t / atr_tp / atr_sl) — meta-labeling adds a SECOND-stage binary classifier on top of M1's per-model dispatch, NOT a re-specification of M1's primary labels.

**Prior 5 EXPLORATIONs** (excluding /026 sanity slot + /027 CONFIRMATION-TF which are exempt from Axis Rotation Discipline per skill Rule 4):

| iter | axis family | verdict |
|---|---|---|
| /023 | feature-family (funding-rate z-score 30/90) | LEARNED-NEG clean |
| /024 | model-arch (regime-conditional sub-models) | NEG-clean |
| /025 | feature-family (OI delta z-score) | LEARNED-NEG-CAT |
| /028 | per-cohort-specialization-LTC-v2 (atr_sl=1.0 LABEL-shift) | PROMISING +0.598 |
| /029 | per-cohort-specialization-DOT-v2 (symmetric BTC gate ±8%) | TECHNICAL-FAILURE |

**Rotation status**: **VALID** (categorically). The prior 5 disperse across **3 distinct families** (feature-family/2, per-cohort-specialization/2, model-arch/1). Not same-family-5-of-5 monoculture. **Additionally**, `meta-labeling` is a NEW NINTH family designation — rotation discipline is satisfied by definition; the 5-of-5 monoculture rule cannot apply to a family that has zero prior precedents.

**Rotation rationale**: meta-labeling is structurally orthogonal to the prior 5. Specifically: (a) NOT feature-family — M2 input is M1's prediction + M1's direction, not a NEW feature in V1_FEATURE_COLUMNS_PRUNED; (b) NOT model-arch — M1's LightGbm architecture unchanged; M2 is a SECOND-STAGE classifier; (c) NOT labeling — M1's triple-barrier σ_t unchanged; M2 labels are derived ex-post (TP-vs-not) inside training window; (d) NOT per-cohort — M2 dispatches PER M1 model but does not re-specify cohort universes. Per `feedback_v1_per_cohort_saturation_asymmetric_rotation.md`, mechanism class distinguishes families: M2's "post-M1 binary filtering" mechanism class has no prior precedent in v1.

---

## Section 1 — Meta-labeling EDA + V3/017 PRIOR (IS-only numerical evidence)

All numbers cite committed CSVs at `analysis/iteration_v1-030/`. Script: `meta_labeling_potential.py` (committed `9f77760`).

### 1.1 Oracle veto headroom (`meta_labeling_veto_lift.csv`)

Sequential oracle-knowledge veto of the worst (sym, direction) cell on the baseline 5-model portfolio (621 IS / 189 OOS trades):

| Veto rank | Cell vetoed | IS cumulative lift | IS veto rate | OOS cumulative lift | OOS veto rate |
|---|---|---|---|---|---|
| 1 | BTCUSDT short | +32.65pp | 9.50% | LTCUSDT long → +45.44pp | 10.05% |
| 2 | ETHUSDT short | +57.19pp | 21.58% | ETHUSDT short → +56.74pp | 21.69% |
| **3 (TOP-3)** | **LINKUSDT short** | **+77.87pp** | **31.88%** | **LTCUSDT short → +58.55pp** | **29.63%** |
| 4 | LTCUSDT long | +88.69pp | 43.80% | DOTUSDT long → +60.15pp (MAX) | 40.21% |

**Headline**: Top-3 worst-cell oracle veto lifts portfolio IS PnL from +50.98% → +128.85% (+77.87pp) and OOS PnL from +24.87% → +83.42% (+58.55pp). **This is the oracle upper bound** — a perfect classifier with full hindsight. The realistic-M2 lift is bounded BELOW this by classifier accuracy on the M1-positive subset.

### 1.2 H1/H2 stability check (`meta_labeling_stability.csv`)

The mechanism's generalizability depends on the worst cells being identifiable from past data:

| Sample | n_trades | Worst-3 cells |
|---|---|---|
| IS H1 (first 12-13 months) | 311 | {BTC-short, LTC-short, BTC-long} |
| IS H2 (last 12-13 months) | 310 | {ETH-short, BTC-short, ETH-long} |

**Worst-3 overlap H1 ↔ H2**: **1/3 (33.3%, MODERATE)** — only BTC-short persists. **Worst-5 overlap**: 3/5. Per LM Master §1 Fact 3: "Even a PERFECT classifier on IS-H1 worst cells generalizes only ~33% to IS-H2 worst cells. Out-of-distribution OOS shift adds another generalization hop." This is the load-bearing structural constraint forcing realistic-M2 capture rate to compress from oracle's 58.55pp to ~+0.12-0.28 OOS Sharpe Δ.

### 1.3 Per-model decomposition (`meta_labeling_per_model.csv`)

| Model | Symbols | IS trades | IS WR | IS PnL | OOS trades | OOS WR | OOS PnL | Worst cell |
|---|---|---|---|---|---|---|---|---|
| **A** | BTC+ETH pooled | 258 | 36.4% | **-50.98%** | 81 | 42.0% | +35.93% | IS: BTC-short -0.55/tr; OOS: ETH-short -0.51/tr |
| **C** | LINK | 146 | 45.2% | +72.06% | 28 | 50.0% | +34.23% | IS: LINK-short -0.32/tr; OOS: LINK-long +0.36/tr |
| **D** | LTC | 124 | 39.5% | +3.27% | 34 | **29.4%** | **-47.25%** | IS: LTC-long -0.15/tr; **OOS: LTC-long -2.39/tr (CATASTROPHE)** |
| **E** | DOT | 93 | 41.9% | +26.62% | 46 | 39.1% | +1.96% | IS: DOT-short +0.03/tr; OOS: DOT-long -0.08/tr |

**Per-model M1-positive sample sizes (cumulative 24-month rolling)**:
- A: ~206 — **adequate for LightGBM classifier**
- C: ~117 — marginal
- D: ~99 — marginal
- E: **~75 — STRUCTURALLY TOO SMALL** (LM Master §3 binding call)

**M2 highest-leverage application**: Model D (LTC-long OOS catastrophe -45.44% concentrated in 19 trades). If M2 vetoes the LTC-long OOS catastrophe while preserving Model D's profitable TP exits (baseline OOS Model D TP exits ≈ 7), Model D Sharpe Δ swings +0.50-0.80 alone. This is **also** the highest-leverage failure mode (LM Master §5: "If M2 captures even 50% of LTC-long carnage, expect Model D Sharpe Δ +0.50-0.80. **Critical: Model D OOS TP count ≥ 3.**").

### 1.4 Cell-level loss concentration (`meta_labeling_cells.csv`)

Top-3 cells by IS loss share:

| Cell (sym, dir) | Model | IS trades | IS loss share | IS avg PnL/tr |
|---|---|---|---|---|
| BTCUSDT short | A | 59 | 10.72% | -0.553 |
| ETHUSDT short | A | 75 | 12.87% | -0.327 |
| LINKUSDT short | C | 64 | 9.92% | -0.323 |
| **Top-3 sum** | — | **198 / 621 (31.9%)** | **33.5% of IS losses** | — |

OOS top-3 by absolute loss share:

| Cell (sym, dir) | Model | OOS trades | OOS loss share | OOS avg PnL/tr |
|---|---|---|---|---|
| LTCUSDT long | D | 19 | 12.39% | **-2.392 (catastrophe)** |
| ETHUSDT short | A | 22 | 12.39% | -0.514 |
| LTCUSDT short | D | 15 | 8.85% | -0.120 |

Note that the OOS worst-3 cells include Model D LTC-long (the catastrophe Model D's M2 must veto) and ETHUSDT short (which carried 12.87% IS loss share AND 12.39% OOS loss share — most persistent identifiable target).

### 1.5 V3/017 PRIOR (MANDATORY Section 1.5 per LM Master §1 Fact 2)

**Reference**: `briefs-v3/iteration_v3-017/research_brief.md` + `diary-v3/iteration_v3-017.md` (v3 EXPLORATION, NEGATIVE-clean over-filter).

**v3/017 setup**: Meta-labeling on 3-symbol BCH/LDO/TRX + 13-feature M2 input + n_trials_m2=10 + UNIFIED M2 (single classifier across all 3 symbols). M2 best F1 = 0.4409 (barely above random).

**v3/017 outcome**: NEGATIVE PATH C — M2 fired at **42.7% OOS fire-rate** but produced **NO per-trade economics lift on retained trades**. Mechanism worked at filtering layer; failed at quality-improvement layer. OOS Sharpe Δ informational range -0.48 IS / -2.15 OOS (v3 cycle baseline difference; not directly comparable). PBO = NaN signal from thin walk-forward cells where M2 had no labels.

**Section 1 prior calibration (mandatory acknowledgment)**: The v3/017 mechanism precedent IS the modal failure mode for /030. Per LM Master §1 Fact 2: "v3/017 mechanism precedent: M2 filtered 42.7% of M1 candidates with NO per-trade economics lift. That iteration's M2 was active (not INERT) but failed to improve quality of retained trades. The architecture WORKS at filtering; it FAILS at improving retained-trade economics on 13-feature input. v1/030 has 45 features (43+M1 conf+M1 dir) — more input dim, smaller signal-to-noise per sample." This is the load-bearing prior driving the NEGATIVE-OVER-FILTER 27-30% modal verdict cell weight.

**Differences v1/030 vs v3/017**:
1. **Universe**: 5-sym (v1) vs 3-sym (v3) — more cells to break
2. **M2 input dim**: 45 (v1) vs 13 (v3) — more features but lower signal-to-noise per sample
3. **M2 dispatch**: 3-separate per-model with E DROPPED (v1) vs 1-unified (v3) — v1's dispatch may LOWER fire rate via specialization
4. **n_trials_m2**: 18 (v1 per LM §2) vs 10 (v3) — TPE warmup difference
5. **M1 cohorts**: v1's Model A pooled BTC+ETH (largest cohort with 206 cumulative M1-pos) vs v3's 3 symbol-specific cohorts (similar to ~75-100 each)

**Net direction**: v1's structural improvements (per-model dispatch + n_trials_m2=18 + 45 features) MAY produce qualitatively different M2 behavior than v3/017. LM Master §6 acknowledges this: "If v1's larger 5-symbol universe + 45-feature stack produces qualitatively different M2 behavior than v3's 3-symbol + 13-feature, the priors are mis-shaped. Honest uncertainty: NEG-OVER-FILTER could be 20-40%; PROMISING-clean could be 10-25%." QR's prior recalibration (Section 0.5) sits inside LM Master's honest-uncertainty band.

---

## Section 2 — ORACLE EDA + Falsifier pre-registration

All falsifier bands are LM Master §5 verbatim with QR ADOPTING all 5 F-AXIS items + adjustments for Model E DROPPED.

### F-AXIS #1 — M2 dispatch correctness (binary architecture assertion)

**Expected M2-trained cells**: 53 months × 3 models (A, C, D — Model E EXCLUDED) = **159 cells expected** (DOWN from LM Master §5's 212 because Model E DROPPED).

**PASS criterion**: total M2-trained cells ≥ **80 of 159** (≥50%). PASS if >=80 (sample-size threshold floor passes for most months on A/C/D given cumulative 99-206 M1-pos at month 25+).

**FAIL criteria**:
- M2-trained cells < 80 → TECHNICAL FAILURE (Model A's M2 is structurally largest cohort; if A's M2 returns None on >50% of months, infrastructure defect)
- M2 dispatched on Model E (Model E should NOT train M2 per Section 3.3) → SPEC VIOLATION; FAIL

**Companion structural assert**: per `metalabeling.py:67`, `if len(m2_features) < 10` returns None. For Model C/D with 99-117 cumulative M1-pos over 24 months, early rolling windows may have <10 M1-pos. Track frequency of M2-skip in run.log.

### F-AXIS #2 — Post-M2 trade count band

- **IS predicted [310, 500] modal 405** (baseline 621 × (1 - 0.35 average M2 fire-rate) ≈ 400; band reflects fire-rate variance 15-50%)
- **OOS predicted [95, 165] modal 130** (baseline 189 × similar fire-rate)

**CRITICAL THRESHOLD**: **OOS trades < 90 → caps verdict at NEGATIVE-OVER-FILTER** regardless of headline Sharpe (LM Master §5 binding; v3/017 PBO=NaN signal from thin walk-forward cells).

### F-AXIS #3 — M2 calibration LOAD-BEARING (verdict-positive determinant)

**OOS M2-pass true positive rate** (M2 says PASS and trade is TP-exit) ≥ baseline OOS WR + 8pp lift.

Baseline OOS WR = 40.2%. **PASS criterion**: M2-pass OOS WR ≥ **48%** (≥8pp lift over 40.2%).

**FAIL trigger**: M2-pass OOS WR < 42% → M2 is NOT discriminating → caps verdict at NEGATIVE-OVER-FILTER regardless of F1.

**LM Master §5 rationale**: F-AXIS #3 is the verdict-positive discriminator. The mechanism only adds value if retained trades have measurably higher win rate than the unfiltered M1 set. v3/017's failure was M2 fired correctly (42.7% rate) but retained-trade WR ≤ baseline WR → no economics lift → NEGATIVE-clean.

### F-AXIS #4 — n_eff for M2 (informational)

Per (model, month) cell, n_eff_m2 ∈ **[2, 6] modal 4**. **Informational, not blocking** per LM Master §5. Model E DROPPED removes E's small-sample n_eff=1-2 anomaly from the distribution; Model C/D cells expected to dominate n_eff=3-4.

### F-AXIS #5 — OOS TP-exit count LOAD-BEARING (transferred from /028 §6)

Post-M2 OOS TP-exit count ≥ **15** (baseline OOS TP = 40; M2 should retain ≥40% of TP-class trades).

**Below 15 → caps verdict at PROMISING-INERT regardless of F2**. Specifically per LM Master:
- **Model A OOS TP count ≥ 6** (baseline A OOS TP ≈ 17)
- **Model D OOS TP count ≥ 3 LOAD-BEARING** (baseline D OOS TP ≈ 7; LTC-long catastrophe pre-vet — if M2 zeros OOS Model D TP exits while filtering the catastrophe, the upside vanishes alongside the loss-clip)

The Model D OOS TP ≥ 3 LOAD-BEARING is the highest-criticality F-AXIS item per LM Master §9 Q5: "If Model D's M2 zeros OOS TP exits (catastrophic OOS LTC-long carries the model — M2 vetoing it could collapse upside), verdict caps regardless."

### F-AXIS-MECHANISM compound (5 sub-checks)

1. F-AXIS-M #1 = F-AXIS #1 (binary dispatch, 159 expected)
2. F-AXIS-M #2 = F-AXIS #2 (trade-count band; OOS < 90 → NEG-OVER cap)
3. F-AXIS-M #3 = F-AXIS #3 (M2-pass OOS WR ≥ 48% LOAD-BEARING)
4. F-AXIS-M #4 = F-AXIS #4 (n_eff_m2 informational)
5. F-AXIS-M #5 = F-AXIS #5 (OOS TP ≥ 15 + Model D OOS TP ≥ 3 LOAD-BEARING)

All sub-checks pre-registered. F-AXIS-M #2, #3, #5 are verdict-capping.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1 mandatory)

**Declaration**: **NORMAL-RISK**.

**Reason**: Per LM Master §3.4 mapping and the project's HIGH-RISK criteria (changes to Optuna's training-objective domain — label distribution, feature set, training universe, risk-primitive), meta-labeling M2 is structurally orthogonal:
- M1's triple-barrier σ_t / atr_tp / atr_sl unchanged
- V1_FEATURE_COLUMNS_PRUNED 43 cols unchanged at M1 layer
- M1 universe (BTC, ETH, LINK, LTC, DOT) unchanged
- Risk gates R1/R2/R3 unchanged
- Bar interval (8h) unchanged
- Only NEW change: M2 binary classifier as POST-M1 filtering layer

M2 IS a new classifier with its own training objective, but that objective is a **derived ex-post label inside the M1 training window** (TP-reached-before-SL-or-timeout). It does not change M1's loss surface. The architectural change is COMPARTMENTALIZED to a second-stage filter and the M2 layer is per-`feedback_v1_high_risk_declaration_discipline.md` NOT a training-objective-domain change to M1.

**Counterpoint and justification for NORMAL-RISK**: LM Master §2.5 (in v1/029) precedent — when an axis "does change Optuna's training-objective domain" but is "compartmentalized" and "single-axis", it stays NORMAL-RISK. /030 mirrors this: M2 has its own Optuna sub-search (n_trials_m2=18) but it is structurally disjoint from M1's Optuna. Single-axis discipline binds; this is the ONLY axis change vs /028-PROMISING baseline.

**Mitigation (informational)**: Pre-commit-to-CONFIRMATION tripwire NOT armed. If /030 returns PROMISING (Δ ≥ +0.05), the /037-CONFIRMATION composition adds meta-labeling as a SEPARATE CONFIRMATION axis (not bundled with /028 LTC specialist + LINK + ETH-gate per LM Master §9 Q7 NON-COMPOUNDABLE finding).

---

## Section 2.6 — ORACLE EDA trade-attribution requirement

Per `feedback_v1_oracle_eda_trade_attribution.md`, all feature-family briefs must include BOTH distribution-level Sharpe-proxy AND realized-trade attribution. /030 is **meta-labeling** (NEW axis family, NOT feature-family) but the spirit of the rule applies to the M2 mechanism evidence.

**Distribution-level**: The /030 brief Sections 1.1, 1.3, 1.4 produce cell-level attribution at IS-full and OOS-full granularity. `meta_labeling_cells.csv` reports both win-rate AND net-PnL × per-trade-Sharpe at 20 cells (10 cells × 2 samples).

**Realized-trade attribution**: `meta_labeling_summary.csv` + `meta_labeling_veto_lift.csv` produce realized-trade attribution at portfolio level. Oracle veto lift IS the realized-trade attribution proxy (it shows actual trade-level PnL impact of vetoing each cell at sequential ranking).

**Sharpe-proxy distribution** (forward-return regression): not separately required because the realized-trade attribution is already published at the cell level. The /025 OI-delta Q1 sign-flip basin-relocation lesson does not apply at /030 because **M2 is a post-Optuna trade-stream filter** (at M1's prediction layer) — labels are computed identically to baseline; only the M2 filter adds/removes trades. No basin-relocation risk on labels.

**Mandate satisfied**. CSVs: `meta_labeling_cells.csv` (20 cells), `meta_labeling_veto_lift.csv` (20 rows), `meta_labeling_per_model.csv` (8 rows), `meta_labeling_stability.csv` (1 row), `meta_labeling_summary.csv` (1 row); all committed `9f77760`.

---

## Section 3 — Implementation Spec

### 3.1 Universe + features

- **`V1_BASELINE_UNIVERSE = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")`** — **UNCHANGED 5 symbols**
- **M1 feature set**: `V1_FEATURE_COLUMNS_PRUNED` (43 cols) — **FROZEN UNCHANGED** from /028
- **Cross-asset features**: existing v1 baseline cross-asset infrastructure unchanged

### 3.2 Labels (M1 — UNCHANGED)

M1 retains baseline labeling exactly as v0.v1-baseline-corrected:
- **Triple-barrier σ_t NATR** (Model-specific baseline)
- **`atr_tp_multiplier = 3.5`** UNCHANGED (Model A, C, D, E)
- **`atr_sl_multiplier = 1.75`** UNCHANGED (Model A, C, D, E)
- **`label_timeout = 21 bars`** (7 days at 8h) UNCHANGED
- **Embargo at walk-forward boundary**: `walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms` UNCHANGED (post-/058 FIX preserved)

### 3.3 Mechanism (M2 — META-LABELING; the only axis change)

**M2 dispatch architecture**: **3 separate M2 LGBMClassifier binary models** — one per `(model_name, month)` cell for **Model A, Model C, Model D**. **Model E EXCLUDED** per LM Master §3 sample-size binding call.

**Why Model E EXCLUDED** (verbatim QR adoption of LM §3):
- Model E cumulative M1-pos over 24-month training window = ~75 samples
- LightGBM classifier on 75 samples × 45 features × n_trials_m2=18 is structurally below the threshold where TPE Optuna can navigate the 9-dim hyperparameter space + train a stable classifier
- Per `metalabeling.py:67`, `if len(m2_features) < 10` returns None — Model E will produce frequent M2-skip events; signal is M2-noise classification at best
- v3/017 best F1 = 0.4409 on similar-sized cohorts — barely above random
- Operational behavior: when M2 is None for Model E, trust M1 directly (no M2 filtering applied — Model E trades pass through unmodified)

**M2 input features**: V1_FEATURE_COLUMNS_PRUNED (43) + `m1_confidence` (M1's predicted probability) + `m1_direction` (M1's predicted sign) = **45 cols** per M2 sample.

**M2 label** (binary, derived ex-post inside training window only):
- M2 label = 1 if M1's direction matched AND trade reached TP barrier before SL/timeout
- M2 label = 0 otherwise (SL hit OR timeout fallback OR direction mismatch)
- **Look-ahead audited** per `metalabeling.py:23-29` module docstring — labels never consume future candles outside the training window

**M2 threshold**: **PINNED 0.5** (single-axis discipline; not tuned at /030). Threshold sweep is reserved for /031 if /030 fires PROMISING (LM Master §7 routing).

**M2 Optuna hyperparameter search ranges** (per LM Master §2 ADOPTED VERBATIM):

| Param | /030 range | Rationale (LM Master §2) |
|---|---|---|
| `n_estimators` | [50, 200] | Cap upper; 75-200 sample M2 training sets; >200 trees overfit |
| `max_depth` | [2, 4] | TIGHTEN — small subset; depth=5 with 75 samples = 1 sample/leaf risk |
| `num_leaves` | [7, 31] | TIGHTEN — 127 leaves on 75 samples is degenerate |
| `learning_rate` | [0.02, 0.10] log | Cap upper; smaller LR + more trees prevents single-shot memorization |
| `min_child_samples` | [8, 30] | RAISE lower bound — 5 too permissive for 75-sample data |
| `reg_alpha` | [0.01, 5] log | RAISE lower from 1e-8; L1 sparsity essential at 45 features × 100 samples |
| `reg_lambda` | [0.01, 5] log | Same reasoning as L1 |
| `colsample_bytree` | [0.4, 0.8] | TIGHTEN ceiling — force feature subsampling to expose secondary features beyond M1 conf |
| `scale_pos_weight` | explicit `n_neg/n_pos` per cell | More deterministic than `is_unbalance=True` (which uses internal heuristic); v3/017 lesson |

**`n_trials_m2 = 18`** (per LM Master §2.3 ADOPTED; matches M1 n_trials=18). Wall-clock impact: ~+90 sec total (LM Master §8 estimate). TPE warmup requires ≥15 trials for 9-dim search space convergence.

**Stratification fallback** (per LM Master §2): if any TimeSeriesSplit fold has <3 positive labels, skip that fold. Currently `metalabeling.py` has `if len(train_idx) < 5 or len(val_idx) < 2` — QR adopts LM Master's recommendation to extend with label-presence check at fold level.

**Implementation infra**: `src/crypto_trade/strategies/ml/metalabeling.py` (in-tree from iter-v3/017 implementation; reuse with v1-specific dispatcher).

### 3.4 LM Master Phase 4.5 Response Map (MANDATORY — address each §1-§9)

#### §1 Realistic +0.12 to +0.28 OOS Sharpe Δ modal

**ADOPTED**. Brief Section 0, Section 1.5, Section 4 anchor on +0.12-0.28 modal verdict band, NOT the +58.55pp oracle headroom. The oracle number is published in Section 1.1 as the upper bound but the brief's PROMISING-modal expectation in Section 4 is +0.12-0.28.

#### §2 Hyperparameter bounds for M2

**ADOPTED VERBATIM** (Section 3.3 table). All 9 hyperparameter bounds adopted as LM Master recommended. `scale_pos_weight = n_neg/n_pos` adopted as explicit per-cell computation (NOT `is_unbalance=True`). Stratification fallback adopted (label-presence check at fold level).

**`n_trials_m2 = 18`** ADOPTED (not the default 10). LM Master §2.3 binding: TPE warmup needs ≥15 trials. +90 sec wall-clock cost is negligible.

#### §3 4-separate-M2 vs UNIFIED-M2

**PARTIAL ADOPT**. LM Master's STRONG recommendation is UNIFIED-M2 with `symbol` + `model_name` categorical features; QR adopts the BINDING sub-recommendation (DROP Model E's M2) while RETAINING 4-separate (now 3-separate) per-model dispatch for A/C/D.

**Rationale for partial adoption**:
- **AFML Ch.3 textbook fit**: per-model M2 dispatch aligns with per-model M1 architecture; preserves the LdP canonical mechanism
- **Single-axis discipline binds**: UNIFIED-M2 introduces NEW categorical features (`symbol`, `model_name`) at the M2 layer — that's a 2-axis change (M2 architecture + M2 feature space). Pure single-axis EXPLORATION discipline keeps M2 features at AFML Ch.3 minimal (43 + m1_conf + m1_dir = 45).
- **Sample-size constraint binding**: LM Master §3 closing line: "If QR rejects unified (single-axis discipline argument): at minimum drop M2 for Model E." This is the binding call.
- **Operational fallback**: when M2 is None for Model E, Model E's M1 trades pass through unmodified (no filtering). Edge integrity preserved on Model E.

**UNIFIED-M2 deferred to /031 if /030 INERT**: LM Master §7 routing — if /030 INERT, /031 = NEW funding-rate family per PRE-COMMIT. UNIFIED-M2 is the explicit fallback alternative if /031 also fires INERT (Section 4 Path Forward records this as a deferred path).

#### §4 Path C prior 15/17/22/30/16

**ADOPTED INFORMATIONAL** as anchor for Section 4 verdict matrix. QR recalibrates to 17/18/24/27/14 reflecting Model E DROPPED (~3pp NEG-CAT compression). Combined PROMISING 35%; combined NEG 41%. Modal stays NEGATIVE-OVER-FILTER 27%.

#### §5 F-AXIS #1-#5 pre-registration

**ADOPTED VERBATIM** (Section 2). All 5 F-AXIS items carried into brief Section 2:
- F-AXIS #1 expected cell count adjusted 212 → 159 (Model E DROPPED)
- F-AXIS #2 OOS [95, 165] modal 130; OOS < 90 NEG-OVER cap
- F-AXIS #3 M2-pass OOS WR ≥ 48% LOAD-BEARING
- F-AXIS #4 n_eff_m2 [2, 6] modal 4 informational
- F-AXIS #5 OOS TP ≥ 15 + Model D OOS TP ≥ 3 LOAD-BEARING

#### §6 Calibration MEDIUM-LOW confidence

**ACKNOWLEDGED**. LM Master directional track 3/9 = 33%; methodology 7/7 perfect. For meta-labeling: single v3/017 precedent → MEDIUM-LOW directional confidence. QR ACKNOWLEDGES uncertainty in Section 0.5 (intermediate prior between "4-separate w/ E" and "UNIFIED").

#### §7 Routing /031 PRE-COMMIT

**ADOPTED**. Regardless of /030 verdict, /031 axis = **NEW feature family (funding-rate z-scores)** per LM Master §7 STRONG prior. Meta-labeling is a one-shot architectural axis. Verdict-conditional fine-grain:
- /030 PROMISING (Δ ≥ +0.05) → /031 = M2 threshold sweep is alternative single-axis follow-up; default is NEW feature family (funding-rate)
- /030 INERT → /031 = NEW feature family (funding-rate); meta-labeling axis CLOSED at v1; UNIFIED-M2 deferred to backup
- /030 NEGATIVE-OVER-FILTER (modal) → /031 = NEW feature family (funding-rate); meta-labeling axis CLOSED at v1 (mirror v3/017 closure)
- /030 NEGATIVE-CATASTROPHIC → /031 = closure-reconciliation + NEW feature family; meta-labeling PERMANENTLY CLOSED for v1

#### §8 Wall-clock 65-95 min modal 80 min

**ADOPTED**. Brief Section 3.6 anchor on 65-95 min modal 80 min. INSIDE 2h cap. **NO CONFIRMATION-spec escalation** for /030 (ENSEMBLE_SIZE=3, n_trials_m1=18 — v1 EXPLORATION standard).

#### §9 Eight adjudication questions

- **Q1 NO new features (single-axis discipline)**: ADOPTED. M2 input = 45 cols (43 V1_FEATURE_COLUMNS_PRUNED + m1_confidence + m1_direction). No OOD score or BTC-bucket flag added.
- **Q2 4-separate-M2 with Model E DROPPED**: ADOPTED (partial of LM §3).
- **Q3 n_trials_m2 = 18**: ADOPTED.
- **Q4 F-AXIS #5b H1/H2 stability**: ADOPTED INFORMATIONAL. LM Master's Spearman rank correlation ≥ 0.35 threshold is a post-hoc check in Phase 7.4 attribution; not a Phase 7 verdict-capping gate.
- **Q5 F-AXIS bands**: ADOPTED VERBATIM (Section 2).
- **Q6 verdict priors 15/17/22/30/16**: ADOPTED INFORMATIONAL; recalibrated 17/18/24/27/14 for Model E DROPPED.
- **Q7 bundle implications**: ADOPTED. M2 is NON-COMPOUNDABLE with the 3-specialist bundle (LINK + ETH-gate + LTC+atr_sl). If /030 PROMISING, M2 enters /037-CONFIRMATION as a SEPARATE architectural axis (NOT bundled with cycle-3 per-cohort specialists). LM Master §9 Q7 cross-layer orthogonality precedent (v3 PROMISING-MECHANICAL).
- **Q8 Critic Phase 6.0 defensive checks**: ADOPTED. Section 10.3 test suite mandate includes the 6 items LM Master mandated. NO HARD-ASSERT pattern that would crash on legitimate M2-skip (avoids /027 `r.model_name` defect).

### 3.5 Configuration

- **ENSEMBLE_SIZE = 3** (v1 EXPLORATION standard; **NOT escalated to 10** per LM Master §8 explicit: no CONFIRMATION-spec escalation for /030 — meta-labeling is M2-layer architectural, NOT basin-relocation)
- **n_trials_m1 = 18** (v1 EXPLORATION standard; M1 UNCHANGED)
- **n_trials_m2 = 18** (per LM Master §2.3 ADOPTED)
- **Outer seed = 42** (single-seed; v1 EXPLORATION standard)
- **Sample weighting (M1) = `abs_pnl`** (baseline structural; /016 closure)
- **Sample weighting (M2) = NONE** (binary log-loss objective; M2 has no sample weighting)
- **Bar interval = 8h** UNCHANGED
- **Bounds profile (M1) = `v1_pruned`** UNCHANGED from /028
- **Risk layers**: R1 ON (per-model A=OFF, C/D/E=ON per Model E baseline); R2 OFF per-model (cycle-2 baseline); R3 ON (project-wide always-on)
- **Wall-clock HARD CAP = 2h** (EXPLORATION; LM Master prediction 65-95 min modal 80 min)
- **Kill-switch ARMED at > 1.6h** (mirror /028 protocol)

### 3.6 Wall-clock estimate (5-step label-rate scaling per `feedback_v1_label_rate_wall_clock_scaling.md`)

1. **Precedent iteration**: /016 sample-weighting at ENSEMBLE_SIZE=3 + n_trials=18 + V1_FEATURE_COLUMNS_PRUNED + 5-sym = ~50 min observed (M1-equivalent at baseline cohort label rate). /030's M1 is BIT-IDENTICAL to baseline; M2 is the only new compute.
2. **Precedent M1 label count per training window**: ~621 baseline trades / 53 months ≈ ~12 M1-positives/month/model. M1 trains on full candle history (not M1-pos subset).
3. **/030 M1 label count**: SAME as baseline (M1 UNCHANGED). Wall-clock for M1 dispatch ≈ 50 min (mirroring /016).
4. **Scaling factor M1**: 1.0 (BIT-IDENTICAL).
5. **M2 overhead estimate** (per LM Master §8): 3 models × 53 months × 18 trials × 3 TimeSeriesSplit folds × ~150 samples × ~10-50ms LightGBM fit time ≈ 4 × 53 × 18 × 3 × 0.05 = 57s × oversight factor 3 = ~3-6 min M2 total. Per LM Master: "marginal" wall-clock impact.

**Total estimate**: **50-90 min M1 + 3-6 min M2 = 53-96 min. Modal 80 min**. INSIDE 2h cap with substantial margin.

**Cross-check** via v3/017 precedent: v3/017 meta-labeling at 3-symbol BCH/LDO/TRX + V3_FEATURE_COLUMNS_TOP_N + n_trials_m2=10 ran ~35 min total. v1 has 5 symbols + 43 features vs v3's 3 + 14 → multiplier ~1.6× = ~56 min plus higher n_trials_m2 = ~80 min. Both estimates converge.

**Kill-switch**: > 1.6h total → wall-clock breach; pkill + closeout per /029 protocol. **No CONFIRMATION-spec escalation hazard** (ENSEMBLE_SIZE=3 + n_trials_m1=18 is below /029's failed CONFIRMATION-spec ENSEMBLE_SIZE=10 + n_trials=35).

### 3.7 Code changes (src/ — keep minimal)

- `src/crypto_trade/strategies/ml/metalabeling.py` (existing in-tree from v3/017): adjust per-cell `scale_pos_weight` computation; add Model E EXCLUSION guard (Model E's `_train_m2_for_month` returns None early); apply LM Master §2 hyperparameter bounds; extend stratification fallback.
- `run_baseline_v1.py`: add `--meta-labeling` flag (or equivalent iteration-30 dispatch); wire M2 through Model A/C/D LightGbm strategy initialization; pass `enable_meta_labeling=True` for A/C/D, False for E.

### 3.8 Axis Family Declaration (Critic Check 14 verification path)

- **Axis family**: `meta-labeling` (NEW NINTH family in v1 history; UNUSED across cycles 1, 2, 3)
- **Justification for NEW family**:
  - NOT a `feature-family` axis — M2 input uses existing V1_FEATURE_COLUMNS_PRUNED + M1 prediction (M1 prediction is NOT a new feature in V1_FEATURE_COLUMNS_PRUNED)
  - NOT a `model-arch` axis — M1's LightGbm architecture per Model A/C/D/E UNCHANGED; M2 is SECOND-STAGE classifier orthogonal to M1
  - NOT a `labeling` axis — M1 triple-barrier σ_t / atr_tp / atr_sl UNCHANGED; M2 labels are derived ex-post (TP-or-not) and only exist inside the M2 training subset
  - NOT a `per-cohort-specialization` axis — M2 dispatches per M1 model but does not re-specify cohort universes (Model A still pools BTC+ETH; Model E still maps to DOT)
  - NOT a `risk-primitive` axis — R1/R2/R3 UNCHANGED
  - NEW mechanism class: "post-M1 binary classifier filter"
- **Rotation status**: VALID (prior 5 disperse across 3 distinct families; `meta-labeling` has zero prior precedents so monoculture rule is structurally inapplicable)

---

## Section 4 — Verdict Matrix (F1 OOS Δ band per LM Master §4 + Section 0.5 recalibration)

Pre-committed verdict cells with explicit OOS Δ bands:

| OOS Δ band | Verdict cell | Prior probability (QR recalibrated) | Mechanism interpretation |
|---|---|---|---|
| Δ ≥ +0.20 | **PROMISING-CLEAN** | **17%** | M2 captures top-3 worst-cell veto with reasonable precision; modal +0.30 |
| Δ ∈ [+0.05, +0.20) | **PROMISING-INERT-FAV** | **18%** | Partial mechanism; M2 fires but caps below clean threshold; modal +0.12 |
| Δ ∈ [-0.10, +0.05) | **INERT-NO-EFFECT** | **24%** | M2 fire-rate < 5% OR no headline change; modal +0.00 |
| Δ ∈ [-0.40, -0.10) | **NEGATIVE-OVER-FILTER (MODAL)** | **27%** | v3/017 mirror — M2 fires correctly but no quality lift; modal -0.22 |
| Δ < -0.40 | **NEGATIVE-CATASTROPHIC** | **14%** | M2 over-filtering combined with Model A misfires; modal -0.55 |
| SUM | | **100%** | |

**Modal verdict**: **NEGATIVE-OVER-FILTER 27%** with OOS Δ band centered -0.22. Combined PROMISING tail 35%; combined NEG tail 41%. Combined non-INERT tail 76%.

**F-AXIS overrides** (verdict-capping per LM Master §5):
- F-AXIS #2 OOS trade count < 90 → CAPS at NEGATIVE-OVER-FILTER regardless of F1
- F-AXIS #3 M2-pass OOS WR < 42% → CAPS at NEGATIVE-OVER-FILTER regardless of F1
- F-AXIS #5 OOS TP-exit count < 15 OR Model D OOS TP < 3 → CAPS at PROMISING-INERT regardless of F1

**Pre-committed CONFIRMATION composition implications**:
- /030 PROMISING-CLEAN or PROMISING-INERT-FAV → meta-labeling enters /037-CONFIRMATION as **SEPARATE architectural axis** (NOT bundled with 3-specialist /037 candidate per LM Master §9 Q7 NON-COMPOUNDABLE finding)
- /030 INERT → meta-labeling axis CLOSED at v1; /037-CONFIRMATION stays at 3-specialist bundle; /031 = NEW feature family
- /030 NEGATIVE-OVER-FILTER (modal) → meta-labeling axis CLOSED at v1 (v3/017 mirror closure); /031 = NEW feature family
- /030 NEGATIVE-CATASTROPHIC → meta-labeling PERMANENTLY CLOSED for v1; /031 = closure-reconciliation + NEW feature family

---

## Section 5 — Risk Mitigation (per `feedback_risk_mitigation_design.md`)

### R1 (consecutive-SL cooldown) — ON for C/D/E; OFF for A

Per Model E baseline (mirror /028 + /029): 15-day cooldown after 2 consecutive stop-losses. Model A baseline disables R1 (BTC+ETH pooled baseline). UNCHANGED from baseline.

Simulated effect: ~5-10% of trades blocked across IS+OOS, complementary to M2 (R1 fires at cascade-streak level; M2 fires at predicted-quality level — orthogonal).

### R2 (drawdown brake) — OFF per-model

Per cycle-2 baseline: R2 OFF per-model. UNCHANGED. Per-model R2 was tested at single-model level and produced flat-or-negative effects; the cycle-2 closure is binding.

### R3 (Mahalanobis OOD) — ON

Project-wide always-on; 70th percentile cutoff on 16 scale-invariant features. UNCHANGED.

Expected effect at /030: standard ~2-5% trade-skip rate. Orthogonal to M2 (R3 fires at feature-space distance level).

### M2 fire-rate LOAD-BEARING monitoring (F-AXIS #1-#3)

- F-AXIS #1: ≥ 80 of 159 M2-trained cells (PASS criterion)
- F-AXIS #2: OOS trades ∈ [95, 165] modal 130; OOS < 90 → NEG-OVER cap
- F-AXIS #3: M2-pass OOS WR ≥ 48% (LOAD-BEARING; verdict-positive determinant)

Forensic logs at `data/v1_iter_v1-030_m2_fire_rate.parquet` (NEW per-cell M2 fire-rate / M2-pass WR / TP-share telemetry); required for Phase 7.4 mechanism attribution.

### TP-exit floor monitoring (F-AXIS #5; LOAD-BEARING)

- OOS TP-exit count ≥ 15 (portfolio level; ≥40% TP retention)
- Model D OOS TP ≥ 3 (LOAD-BEARING per LM Master §5 + /028 §6 transfer; LTC-long catastrophe pre-vet)
- Model A OOS TP ≥ 6 (informational)

### M2-skip rate cap monitoring (per LM Master §9 Q8 item 2)

If M2-skip rate (cells where M2 returns None) > 35% of expected dispatch cells, print run.log WARNING. Informational; not blocking. Helps Phase 7.4 mechanism attribution. NEW per-cell flag `m2_passed` in trades.csv (1 = M2 passed; NaN = M2 inactive for this cell).

### Wall-clock kill-switch

Hard cap 2h per cycle-4 EXPLORATION cadence. LM Master predicts 65-95 min modal 80 min. Kill-switch armed at > 1.6h (mirror /029 protocol; total wall-clock budget tracking ongoing).

---

## Section 6 — Risk Management Design

Structured 4-row gate-stack table for /030 (mirror /029 §6 structure to avoid /029-initial-brief Phase 5.5 BLOCK pattern):

| Gate | State | IS fire-rate (pred) | OOS fire-rate (pred) | Regime coverage | Gate-attribution estimate |
|---|---|---|---|---|---|
| **R1 cooldown** (per-model A=OFF, C/D/E=ON) | ON for C/D/E | ~5-10% of trades blocked | ~5-10% of trades blocked | All (micro-cascade prevention) | +0.05-0.10 OOS Sharpe (Model E baseline component) |
| **R2 weighted DD scaling** | **OFF per-model** | n/a (cycle-2 baseline) | n/a | n/a | n/a (baseline disabled per-model) |
| **R3 Mahalanobis OOD** (always-on; 16 scale-invariant features, 70th pctl cutoff) | ON | ~2-5% blocked | ~3-5% blocked (OOD regimes more frequent OOS) | OOD regimes | +0.02-0.05 OOS Sharpe (project-wide) |
| **M2 meta-labeling (NEW)** (per-model A/C/D LGBMClassifier binary; threshold 0.5 pinned) | ON for A/C/D, OFF for E | **15-50% modal 35% blocked** | **15-50% modal 35% blocked** | All M1-positive bars (post-M1 filter) | **+0.12-0.28 modal +0.20 OOS Sharpe (PROMISING band per LM Master §1)** |

### 6.1 Regime coverage narrative

- **M2 meta-labeling (NEW, LOAD-BEARING)** targets the identifiable systematic loss cells per Section 1.4 (BTC-short, ETH-short, LINK-short = top-3 IS loss share 33.5%; LTC-long, ETH-short, LTC-short = top-3 OOS absolute loss share 33.6%). Mechanism: predict TP-vs-not on M1-positive bars using M1 confidence + M1 direction + 43 V1_FEATURE_COLUMNS_PRUNED features; veto when M2 predicted-probability < 0.5.
- **R3 (Mahalanobis OOD)** catches off-distribution months at feature-space distance level. Orthogonal to M2 (M2 fires on predicted TP-not; R3 fires on training-distribution distance).
- **R1 (cooldown)** prevents micro-streak cascades. Orthogonal to M2 and R3; complements at the post-2SL-trade-stream level.
- **R2 (DD brake)** explicitly OFF per-model per cycle-2 baseline. No drawdown-triggered defense; M2 + R3 are the defensive layers at /030.

### 6.2 IS-calibrated gate-effect attribution

From `meta_labeling_veto_lift.csv` IS rows (oracle veto at top-3):
- **Oracle top-3 IS veto lift**: +77.87pp IS PnL (KILLED IS PnL share of worst cells; PROVES the mechanism has IS-historical positive net effect)
- **Realistic-M2 capture rate** (LM Master §1): 15-35% of oracle headroom = **+11.7 to +27.3pp IS PnL lift** → ≈ +0.12-0.28 OOS Sharpe Δ at IS-OOS Sharpe leverage ratio +9.38 USD per +0.60 Sharpe (calibrated from /028 PROMISING +0.60 OOS Δ leverage)

This IS-calibrated effect demonstrates the gate has historical evidence of positive net effect at oracle layer. Realistic-M2 lift depends on M2 prediction accuracy (F-AXIS #3 LOAD-BEARING).

### 6.3 Verdict-capping reminders (forensic monitoring at Phase 7)

- F-AXIS #1 M2-trained cells < 80 → TECHNICAL FAILURE (not verdict cap)
- F-AXIS #2 OOS trades < 90 → NEGATIVE-OVER-FILTER cap
- F-AXIS #3 M2-pass OOS WR < 42% → NEGATIVE-OVER-FILTER cap
- F-AXIS #5 OOS TP-exit < 15 → PROMISING-INERT cap
- F-AXIS #5 Model D OOS TP < 3 → PROMISING-INERT cap (LOAD-BEARING; LTC-long catastrophe pre-vet)

---

## Section 7 — Pre-Registered Failure-Mode Prediction

Three forward-looking failure modes with metric signatures pre-registered for Phase 8 diary verification.

### 7.1 GATE OVER-KILL (most likely failure mode; v3/017 MIRROR)

The 3 separate M2 classifiers fire at OOS rates 35-50% but retained-trade per-trade Sharpe ≤ baseline per-trade Sharpe. M2 vetoes both the systematic losers AND profitable trades in the same loss-prone cells (e.g., ETH-short OOS where the M2 fires on BOTH the -0.51/tr losers AND would also veto any profitable short trade in the same regime). Net effect: trade-count compression with no quality lift = v3/017 NEGATIVE-clean mirror.

**Metric signature** (Phase 8 diary verification):
- F2: OOS fire-rate ∈ [30%, 60%] (above modal 35% upper edge)
- F3: M2-pass OOS WR ≤ 42% (≤2pp lift over baseline 40.2% → no discrimination)
- F1: OOS Δ ∈ [-0.40, -0.10] (NEGATIVE-OVER-FILTER cell)
- Per-model: Model A OOS Sharpe stays flat (M2 over-filters BOTH BTC-short worst-cell + BTC-long mid-cell)
- Verdict cell: Row 4 (NEGATIVE-OVER-FILTER MODAL)

### 7.2 MODEL D PARADOX (second-most-likely; LTC-long catastrophe pre-vet failure)

Model D's M2 successfully vetoes the LTC-long OOS catastrophe (-45.44% / 19 trades) but ALSO vetoes profitable LTC-long trades that may exist in OOS. This zeros Model D OOS TP exits (baseline ≈ 7 TP exits). The mechanism degenerates to loss-clipping-only: Model D OOS Sharpe drops from negative-with-upside to flat-near-zero with NO TP wins. Per /028 §6 lesson: when TP-exit count drops below 3 OS, the mechanism is value-destructive (Model D's edge requires SOME TP exits to dominate the loss-cap; without TP, R-multiple is degraded).

**Metric signature**:
- F5: Model D OOS TP count < 3 (LOAD-BEARING; below floor)
- Model D OOS Sharpe Δ ∈ [-0.10, +0.30] (mild positive from loss-clipping but NO upside)
- Verdict cell: Row 4 (PROMISING-INERT verdict cap regardless of F1)

### 7.3 SAMPLE-SIZE COLLAPSE (third-most-likely; even with Model E DROPPED)

Even with Model E DROPPED to prevent Model E's 75-sample structural minimum, Model C (~117) and Model D (~99) cells may still degenerate at month-by-month rolling windows. If F-AXIS #1 M2-trained cells < 80 of 159 expected, the M2 architecture has not dispatched cleanly. Note this is structurally similar to /029's TECHNICAL FAILURE (incomplete dispatch) but at lower wall-clock cost.

**Metric signature**:
- F1: M2-trained cells < 80 of 159 expected
- Run.log shows >35% M2-skip events (LM Master §9 Q8 item 2 monitoring)
- Model C/D cells show M2_TRAINED=False on >30% of months
- Verdict cell: Row 1 (TECHNICAL FAILURE; no F1 verdict; redispatch or accept INERT-NO-EFFECT informational)

---

## Section 8 — Verdict Cell Determination Table

Pre-commit to verdict cells (mirror /028 + /029 format; 8 rows):

| Row | Condition | Verdict cell |
|---|---|---|
| 1 | F-AXIS #1 M2-trained cells < 80 of 159 expected | **TECHNICAL-FAILURE** (no verdict; redispatch or document) |
| 2 | F-AXIS #1 PASS AND F-AXIS #2 OOS trades < 90 | **NEGATIVE-OVER-FILTER** (F2 cap; under-trade) |
| 3 | F-AXIS #1 PASS AND F-AXIS #3 M2-pass OOS WR < 42% | **NEGATIVE-OVER-FILTER** (F3 cap; no discrimination) |
| 4 | F-AXIS #1 PASS AND F-AXIS #5 OOS TP < 15 OR Model D OOS TP < 3 | **PROMISING-INERT** (F5 cap; loss-clipping-only) |
| 5 | F1 Δ ≥ +0.20 AND F2 ∈ [95, 165] AND F3 ≥ 48% AND F5 ≥ 15 AND F5-D ≥ 3 | **PROMISING-CLEAN** (modal positive; bundle as SEPARATE architectural axis) |
| 6 | F1 Δ ∈ [+0.05, +0.20) AND F-AXIS #2-#5 PASS | **PROMISING-INERT-FAV** (mild lift; informational; bundle DEFERRED) |
| 7 | F1 Δ ∈ [-0.10, +0.05) AND F-AXIS #2-#5 PASS | **INERT-NO-EFFECT** (gate has no effect OR baseline retention) |
| 8 | F1 Δ < -0.10 AND F-AXIS #2-#5 PASS | **NEGATIVE-OVER-FILTER or NEGATIVE-CATASTROPHIC** (Δ ∈ [-0.40, -0.10) vs Δ < -0.40 split) |

**Explicit tuple-determination examples** (per LM Master §5 verdict capping logic):

| Tuple (F1, F2, F3, F5) | Verdict |
|---|---|
| (+0.30, OOS=130, M2-WR=52%, TP=20, D-TP=5) | Row 5 PROMISING-CLEAN |
| (+0.12, OOS=140, M2-WR=49%, TP=18, D-TP=4) | Row 6 PROMISING-INERT-FAV |
| (-0.05, OOS=150, M2-WR=45%, TP=22, D-TP=6) | Row 7 INERT-NO-EFFECT |
| (-0.25, OOS=110, M2-WR=43%, TP=16, D-TP=4) | Row 8 NEGATIVE-OVER-FILTER |
| (-0.30, OOS=85, M2-WR=44%, TP=10, D-TP=2) | Row 2 + Row 4 verdict caps both apply; classify Row 2 NEGATIVE-OVER-FILTER (F2 cap binds first) |
| (+0.15, OOS=130, M2-WR=44%, TP=18, D-TP=2) | Row 4 PROMISING-INERT (F5 Model D cap regardless of F1 +0.15) |
| (+0.40, OOS=100, M2-WR=50%, TP=20, D-TP=2) | Row 4 PROMISING-INERT (Model D OOS TP < 3 binding LOAD-BEARING cap regardless of F1 +0.40) |
| (-0.50, OOS=120, M2-WR=45%, TP=18, D-TP=4) | Row 8 NEGATIVE-CATASTROPHIC |

**Modal expectation per LM Master §1**: Row 4 or Row 8 NEGATIVE-OVER-FILTER cluster at 27% combined modal weight.

---

## Section 9 — Library Stack Declaration

Verified via `uv run python -c "import lightgbm, optuna, numpy, pandas, statsmodels; print(...)"` at brief authoring time:

```
lightgbm: 4.6.0       (LOAD-BEARING — M1 LightGbm + M2 LGBMClassifier)
optuna:   4.8.0       (LOAD-BEARING — M1 n_trials=18 + M2 n_trials_m2=18)
numpy:    2.2.6       (LOAD-BEARING — trade-roster + feature-matrix arithmetic)
pandas:   3.0.0       (LOAD-BEARING — CSV/parquet I/O + groupby aggregations)
statsmodels: 0.14.6   (NOT INVOKED at /030 — no new feature ADF stationarity checks)
mlfinlab: NOT INSTALLED (fallback: in-tree implementations under src/crypto_trade/; not invoked at /030)
mlfinpy:  NOT INSTALLED (fallback: same in-tree path; not invoked at /030)
fracdiff: NOT INSTALLED (no new features at /030 — V1_FEATURE_COLUMNS_PRUNED frozen from /028; fracdiff/ADF flow not invoked)
pypbo:    N/A (EXPLORATION single-seed; PBO is CONFIRMATION-mode informational only)
```

### 9.1 Invocation status for /030

- **lightgbm** (4.6.0): LOAD-BEARING. M1 = baseline LightGbm strategy with `v1_pruned` bounds; M2 = `metalabeling.py` LGBMClassifier binary with LM Master §2 hyperparameter bounds.
- **optuna** (4.8.0): LOAD-BEARING. M1 n_trials=18 single-seed=42 search; M2 n_trials_m2=18 per LM Master §2.3 ADOPTED.
- **numpy / pandas**: LOAD-BEARING.
- **statsmodels**: NOT INVOKED at /030 (no new feature ADF checks).
- **mlfinlab / mlfinpy**: NOT INSTALLED. /030 does NOT invoke either — meta-labeling uses in-tree implementation `src/crypto_trade/strategies/ml/metalabeling.py` (added at iter-v3/017). No fallback gap exists because no mlfinlab API surface is called.
- **pypbo**: N/A. PBO is a CONFIRMATION-mode methodology gate; at single-seed EXPLORATION it is informational only and not invoked.
- **fracdiff**: NOT INSTALLED. /030 has zero new features.

### 9.2 NEW module path + version

- **`src/crypto_trade/strategies/ml/metalabeling.py`**: in-tree iter-v3/017 implementation. Class `MetaLabelingStrategy` (line 169); `_train_m2_binary` (line 51); `_train_m2_for_month` (line 355); `m2_model = _train_m2_binary(...)` invocation (line 513). LOAD-BEARING for /030; minor adjustments at this iteration:
  - Model E EXCLUSION guard (Section 3.3)
  - LM Master §2 hyperparameter bounds applied
  - `scale_pos_weight = n_neg/n_pos` explicit per cell (replaces `is_unbalance=True`)
  - Stratification fallback (label-presence check at TimeSeriesSplit fold level)

### 9.3 No version bumps required at /030

The runner change at /030 is a `--meta-labeling` dispatch flag + Model A/C/D wiring + Model E exclusion guard in `metalabeling.py`. No new library dependency. No version bumps. `uv.lock` UNCHANGED.

---

## Section 10 — Reproducibility, Symbol Exclusion, Test Suite Mandate

### 10.1 Reproducibility

- **HEAD commit (post-Phase 5.5 dispatch)**: TBD at Phase 5.5 PASS commit
- **Seed**: 42 (single outer seed)
- **ENSEMBLE_SIZE**: 3 (v1 EXPLORATION standard; NOT escalated to 10 per LM Master §8)
- **n_trials_m1**: 18 (M1 v1 EXPLORATION standard)
- **n_trials_m2**: 18 (per LM Master §2.3 ADOPTED)
- **Bounds profile (M1)**: `v1_pruned` (UNCHANGED from /028)
- **M2 hyperparameter bounds**: per Section 3.3 table (LM Master §2 ADOPTED VERBATIM)
- **Feature columns (M1)**: `list(V1_FEATURE_COLUMNS_PRUNED)` (43 cols; explicit per `feedback_explicit_feature_columns.md`)
- **Feature columns (M2)**: 43 V1_FEATURE_COLUMNS_PRUNED + `m1_confidence` + `m1_direction` = 45 cols
- **Universe (M1)**: `V1_BASELINE_UNIVERSE = (BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT)` UNCHANGED
- **M2 dispatch**: 3 separate per-model classifiers for A/C/D; Model E EXCLUDED
- **M2 threshold**: 0.5 PINNED
- **OOS_CUTOFF_DATE = 2025-03-24** (UNCHANGED; sacred constant)
- **training_months = 24** (UNCHANGED; sacred constant)
- **Embargo**: `walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms` UNCHANGED
- **`oof_persist_path`**: `data/v1_iter_v1-030_oof.parquet`
- **`params_persist_path`**: `data/v1_iter_v1-030_optuna_best_params.parquet` (M1)
- **`m2_params_persist_path`**: `data/v1_iter_v1-030_m2_optuna_best_params.parquet` (M2 — NEW)
- **`m2_fire_rate_path`**: `data/v1_iter_v1-030_m2_fire_rate.parquet` (NEW per-cell telemetry)
- **`feature_importance_path`**: `feature_importance_M2_<MODEL>_<SYMBOL>.csv` (per-model M2 importance; NEW)
- **Reports directory**: `reports-v1/iteration_v1-030/`

### 10.2 Symbol Exclusion

**`V1_EXCLUDED_SYMBOLS` unchanged.** No symbols added or removed from V1_BASELINE_UNIVERSE.

### 10.3 Test Suite Mandate (per `feedback_v1_defensive_check_must_be_tested.md`)

For QE Phase 6 implementation. **8+ tests required**.

#### 10.3.1 Required regression tests at `tests/test_lookahead_embargo.py` (4 mandated)

- Walk-forward `train_end_ms < test_start_ms` invariant
- `embargo_ms` positive and applied to BOTH leading and trailing test boundary
- Triple-barrier σ_t uses past-only EWMA (no labeling-window contamination)
- M2 label generation (TP/SL/timeout ground truth) uses ONLY in-training-window candles (no future-candle leakage outside training window per `metalabeling.py:23-29` docstring)

#### 10.3.2 New tests at `tests/test_iteration_v1_030.py` (8+ required, listed below)

1. `test_v1_iter030_m2_dispatch_3_separate`: M2 dispatches per-model classifier for A, C, D (NOT for E)
2. `test_v1_iter030_m2_excludes_model_e`: Model E `_train_m2_for_month` returns None unconditionally (Model E EXCLUDED)
3. `test_v1_iter030_m2_feature_vector_composition`: M2 input is 45 cols (43 V1_FEATURE_COLUMNS_PRUNED + m1_confidence + m1_direction)
4. `test_v1_iter030_m2_label_generation`: M2 label = 1 iff trade reached TP before SL/timeout; otherwise 0 (ex-post, in-training-window only)
5. `test_v1_iter030_m2_sample_size_floor`: M2 returns None when `len(m2_features) < 10` (per metalabeling.py:67)
6. `test_v1_iter030_m2_hyperparameter_bounds`: Optuna trial parameters fall within LM Master §2 bounds (n_estimators ∈ [50, 200]; max_depth ∈ [2, 4]; etc.)
7. `test_v1_iter030_m2_scale_pos_weight`: `scale_pos_weight = n_neg/n_pos` is computed explicitly per training cell (not `is_unbalance=True`)
8. `test_v1_iter030_m2_threshold_pinned`: M2 threshold = 0.5 (PINNED; not tunable at /030)
9. `test_v1_iter030_f_axis_1_real_instance`: F-AXIS #1 hard-assert against REAL `TradeResult` instance (avoids /027 `r.model_name` defect; the assert must work on the real type, not just a static code pattern)
10. `test_v1_iter030_f_axis_5_model_d_oos_tp_floor`: Post-M2 OOS TP-exit count for Model D >= 3 (LM Master LOAD-BEARING transferred from /028; sample-instance test using real TradeResult roster)
11. `test_v1_iter030_reproducibility_seeded_m2`: seeded M2 produces identical predictions across 2 runs (seed=42; M2 LGBMClassifier deterministic)
12. `test_v1_iter030_m2_passed_column_in_trades_csv`: trades.csv contains `m2_passed` column with 1/NaN values (NEW per LM Master §9 Q8 item 4)

#### 10.3.3 ANY new hard-assert MUST include sample-instance unit test (the /027 lesson)

The /027 CONFIRMATION crashed at a hard-assert with `AttributeError: 'TradeResult' object has no attribute 'model_name'` — the defensive runtime check was itself defective. **Mandate**: every hard-assert added in /030 src/ MUST have a corresponding test that instantiates the real `TradeResult` object and verifies the assert path. This includes F-AXIS #1 hard-assert and F-AXIS #5 Model D OOS TP-floor assert.

#### 10.3.4 NO HARD-ASSERT that would crash on legitimate M2-skip (LM Master §9 Q8 item 5)

Model C/D cells may legitimately produce M2-skip events at early rolling windows (cumulative M1-pos <10). The runner MUST NOT hard-assert that M2 trained in every cell; the assert is at AGGREGATE level (F-AXIS #1: ≥80 of 159 cells trained). Per-cell M2-skip events are logged at WARNING level for Phase 7.4 mechanism attribution.

---

## Path Forward (LM Master + Critic + QR convergence)

Cycle-4 EXPLORATION 3/10 — 7 EXPLORATIONs remain after /030. **Pre-committed /031 axis = NEW funding-rate-z-scores feature family** regardless of /030 verdict (per LM Master §7).

Verdict-conditional routing summary:
- /030 PROMISING-CLEAN (Δ ≥ +0.20) → /031 = NEW funding-rate family (primary per PRE-COMMIT) OR M2 threshold sweep (alternative single-axis follow-up); /037-CONFIRMATION composition adds M2 as SEPARATE axis NOT bundled with /028 LTC + LINK + ETH-gate per LM Master §9 Q7 NON-COMPOUNDABLE
- /030 PROMISING-INERT-FAV (Δ ∈ [+0.05, +0.20)) → /031 = NEW funding-rate family; /037-CONFIRMATION DEFERS M2 (mild lift insufficient to justify SEPARATE CONFIRMATION axis at this stage)
- /030 INERT (Δ ∈ [-0.10, +0.05)) → /031 = NEW funding-rate family; meta-labeling axis CLOSED at v1; UNIFIED-M2 deferred as backup alternative if /031 INERT
- /030 NEGATIVE-OVER-FILTER (modal; Δ ∈ [-0.40, -0.10)) → /031 = NEW funding-rate family; meta-labeling axis CLOSED at v1 (v3/017 mirror closure)
- /030 NEGATIVE-CATASTROPHIC (Δ ≤ -0.40) → /031 = closure-reconciliation + NEW funding-rate family; meta-labeling PERMANENTLY CLOSED for v1

If /030 PROMISING fires AND /037-CONFIRMATION composition expands to include M2 as SEPARATE axis, target bundle composition for /037-CONFIRMATION:
1. Pool A baseline (BTC+ETH)
2. LINK /018 specialist (+0.80 OOS Δ)
3. ETH-gate /019 specialist (+0.50 OOS Δ)
4. LTC-atr_sl /028 specialist (+0.598 OOS Δ)
5. M2 meta-labeling (/030 PROMISING ≥+0.05 OOS Δ) — SEPARATE architectural axis

If /030 INERT or NEGATIVE, /037-CONFIRMATION stays at 3-specialist (LINK + ETH-gate + LTC) + Pool A baseline.

---

## Brief authoring complete.

**Authoring sign-off**: Quant Researcher; Phase 5 brief authored 2026-05-28; ready for Phase 5.5 gate dispatch.
