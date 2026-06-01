---
iteration: iter-v1/023
date: 2026-05-27
verdict: EXPLORATION-NEGATIVE (clean; FINAL after BLOCK-PENDING-FIX engineering_report.md retrospective fix at c9471ee)
subtype: Section 8 Row 6 (F1 OOS Sharpe Δ -0.2031 ∈ [-0.55, -0.10) clean) + LEARNED-NEGATIVE diary sub-classifier (v1 LEARNS funding above uniform parity; OOS realization fails)
axis_family: feature-family (NEW 15th family — FIRST cycle-3 feature-family axis; cycle-2 /007 + /009 prior feature-family axes NEGATIVE-compound)
axis: funding-rate z-score family (funding_rate_zscore_30 + funding_rate_zscore_90; V1_FEATURE_COLUMNS_PRUNED 40→42)
cadence_position: cycle-3 EXPLORATION (#8 of 10)
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c) — UNCHANGED
merge_decision: NO-MERGE (EXPLORATION-NEGATIVE clean; funding-family EXCLUDED from /027 substrate; BASELINE_V1.md UPDATE NOT triggered — only CONFIRMATION-MERGE updates baseline per `feedback_v3_baseline_update_policy.md`)
---

# Iteration iter-v1/023 — Diary

## 1. Decision: NO-MERGE (EXPLORATION-NEGATIVE clean; funding-family EXCLUDED from /027 substrate; LEARNED-NEGATIVE catalogued)

**EXPLORATION-NEGATIVE clean** (FINAL after BLOCK-PENDING-FIX engineering_report.md retrospective fix at `c9471ee`; Critic Phase 7.5 FINAL verdict `4c8cab4`). Adding 2 funding-rate z-score features (`funding_rate_zscore_30` + `funding_rate_zscore_90`) to V1_FEATURE_COLUMNS_PRUNED (40 → 42) at single-seed=42 ENSEMBLE_SIZE=3 n_trials=18 EXPLORATION budget produces **F1 OOS Sharpe Δ -0.2031** (OOS Sharpe +0.4606 vs anchor +0.6637) — Section 8 Row 6 NEGATIVE clean (3bp inside the [-0.55, -0.10) band, modal INERT 52% MISSED, NEG-clean tail 18% MATERIALIZED). BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). **Funding-family EXCLUDED from /027 substrate**; /027 stays at 2 specialists (LINK +0.80 + ETH+gate +0.50). **/024 advances to REGIME-CONDITIONAL SUB-MODELS** (model-arch family) per user "multiple smaller models per regime" directive + LM Master Phase 7.4 §4 PRIMARY + Critic Path Forward CONVERGENT routing. **NOVEL FINDING catalogued at /023 closeout**: v1 LEARNS funding (portfolio gain share **5.40%** > 2.38%/feature × 2 = 4.76% uniform parity threshold; 6.88% Pool Model A + 5.65% LINK + 5.49% DOT all > 4.0% per-cohort gate); v3 DID NOT (/082 4-feature 9.90% combined = 2.475%/feature < 5.56% parity; /019 z30 rank 14/14). **LEARNED-NEGATIVE sub-classifier** catalogued in `feedback_v1_learned_negative_subtype.md` — v1-vs-v3 architectural distinction (pool Model A joint loss surface enables learning that v3's per-symbol architecture mechanically cannot).

## 2. Headline Numbers

| Metric | Value | Note |
|---|---|---|
| **F1 OOS Sharpe Δ** | **−0.2031** | vs anchor +0.6637; 3bp inside [-0.55, -0.10) NEGATIVE clean band; Section 8 Row 6 DECISIVE |
| OOS Sharpe (daily-annualized) | **+0.4606** | comparison.csv binding |
| IS Sharpe (daily-annualized) | +0.4121 | F3 IS Δ +0.1292 → INERT (no IS basin collapse) |
| OOS Total Net PnL | +24.90% | vs baseline OOS +38.13% |
| IS Total Net PnL | +77.20% | vs baseline IS +54.05% |
| OOS trades | 257 | inside QR [140, 240] **above upper boundary** (anomaly: above predicted range — overshoot 17/240) |
| IS trades | 694 | inside QR [500, 750] PASS |
| OOS win rate | 44.0% | vs baseline 40.2% — slight regime drift |
| Profit factor OOS | 1.0870 | vs baseline 1.156 — declined |
| Max DD OOS | 41.27% | vs baseline 40.94% — flat |
| PSR_monthly_vs_0 OOS | 0.6596 | vs baseline 0.989 (declined) |
| PSR_monthly_vs_1 OOS | 0.2523 | vs baseline 0.0789 (paradoxical-stronger but informational) |
| **DSR** | −39.81 | informational EXPLORATION-mode |
| n_eff_per_cell_median | **9 EXACT** | LM Master Phase 4.5 §5 modal [5, 10] PASS — exact mid-band hit |
| Wall-clock | ~58 min (Optuna ~51 min) | 51% margin against 2h hard cap |

### F-AXIS-MECHANISM RECONCILIATION TABLE — VERDICT CELL COLLISION

| Falsifier | Pre-registered criterion | Observed | Outcome |
|---|---|---|---|
| F-AXIS #1 DUAL GATE (rank + family gain-share) | rank ≤ 14/42 + gain ≥ 4.0% on ≥ 2 cohorts | Pool A 6.88% + LINK 5.65% + DOT 5.49% PASS; LTC 3.66% borderline FAIL | **3/4 cohorts PROMISING-clean** |
| F-AXIS #2 IS trade count | QR [500, 750] | 694 | PASS |
| F-AXIS #2 OOS trade count | QR [140, 240] | 257 (+17 over upper boundary) | overshoot (documented anomaly) |
| F-AXIS #3 n_eff_per_cell | LM Master [5, 10] modal 8 | 9 | **PASS EXACT MID-BAND** |
| F-AXIS #4 IC | < 0.7 all pairs | max 0.4384 (LTC z90 vs MACD) | PASS |
| **F1 OOS daily-annualized Sharpe Δ** | **≥ +0.10 → PROMISING; [-0.55, -0.10) → NEGATIVE clean** | **−0.2031** | **NEGATIVE clean (3bp inside threshold)** |
| F3 IS Sharpe Δ | INERT | +0.1292 | INERT (no IS collapse) |

**Key observation**: F-AXIS-MECHANISM #1 DUAL GATE fires PROMISING-clean on 3 of 4 cohorts (Pool A, LINK, DOT) yet F1 OOS Sharpe Δ NEGATIVE — exactly the verdict-cell COLLISION that LM Master Phase 7.4 §2 catalogued as **LEARNED-NEGATIVE**: information INGESTED + OOS realization FAILED. Distinct from v3's INERT-by-importance failure mode.

## 3. Mechanism narrative: v1 LEARNS funding but learning doesn't translate to OOS lift

### 3.1 v1 learns funding (above uniform parity — first NEW cycle-3 family at portfolio level)

Per `analysis/iteration_v1-023/funding_oracle_band_attribution.csv` + observed feature_importance.csv:

| Cohort | z30 rank (of 42) | z90 rank (of 42) | Family combined gain share |
|---|---:|---:|---:|
| **Pool Model A** (BTC+ETH joint, 2× rows) | 12 | 11 | **6.88%** |
| LINK Model C | 12 | 11 | 5.65% |
| DOT Model E | 18 | 10 | 5.49% (z90 dominant) |
| LTC Model D | 18 | 14 | 3.66% (borderline) |
| **Portfolio average** | — | — | **5.40%** |

Uniform parity at 42 cols = 2.38%/feature × 2 features = 4.76% combined floor. **Portfolio 5.40% clears parity** — first NEW cycle-3 feature family to do so. Pool A specifically gets **6.88%** = 1.4× uniform parity, confirming the pool architectural lever materialized partially. v3 comparison: /082 4-feature combined 9.90% = 2.475%/feature was BELOW v3 uniform-parity 5.56%; v3 INERT-by-importance.

### 3.2 But learning doesn't translate (tail-load-bearing mechanism)

Per LM Master Phase 7.4 §3 mechanism synthesis:
- **z90 outranks z30 in 3 of 4 cohorts** — LightGBM treats the 30-day window (z90) as a slow-moving regime indicator; the 10-day window (z30) is marginally used. Trees at depth 3-5 cannot easily compose three-way `funding × momentum × volatility` interactions at 9 effective trials.
- **Pool A gain share 1.9× single-symbol cohorts (6.88% vs 3.66%)** — joint BTC+ETH loss surface enables `funding × symbol-dummy` splits. Architecture advantage materialized.
- **ORACLE +78.55% IS PnL concentration in z30 ∈ [-2, -1] band EVAPORATES under retraining**. The 11.0% of IS trades that generated +154% IS PnL share were a property of the **baseline 5-symbol pool basin**. /023 retrained basin (Jaccard ~10% per /022 pattern) produces a ~90% NEW roster where the z30 ∈ [-2, -1] events are not at training distribution. LightGBM at single-seed finds the **mean funding effect (~zero)**; ORACLE-tail edge is left on the table.

**Synthesis**: funding is **mean-informative but tail-load-bearing**. v1 LightGBM learns the average; the tail (+78.55% concentration) requires **explicit regime gating at training time** — which is the load-bearing rationale for /024 regime-conditional architecture.

### 3.3 Why /023 is LEARNED-NEGATIVE not INERT

The verdict cell distinction matters for catalog purposes:

- **INERT (v3 4-data-point pattern)**: feature did NOT enter loss surface meaningfully. Importance rank bottom-quartile (≥ 30/42 in v1 terms); gain share below uniform parity; F1 OOS flat. The feature was NEVER picked.
- **LEARNED-NEGATIVE (NEW v1 cell at /023)**: feature DID enter loss surface meaningfully. Top-third rank on ≥ 2 cohorts; gain share above parity; **BUT** F1 OOS NEGATIVE. The model learned a property of the IS basin that does not generalize to the retrained-basin OOS roster.

Pre-registered Row 6 (F1 OOS Δ ∈ [-0.55, -0.10)) wins per `feedback_no_cheating.md`; **NEGATIVE clean** is the verdict-class. **LEARNED-NEGATIVE is a diary sub-classifier for catalog purposes**, NOT a verdict elevation. The 3bp distance from INERT threshold (-0.20) is methodologically suspicious-tight but not exploited.

## 4. Structural finding: v1-vs-v3 architectural distinction

### 4.1 The two architectures partition funding-rate outcomes cleanly

| Track | Universe | Architecture | Funding gain share / feature | Verdict |
|---|---|---|---:|---|
| **v3** | BCH/LDO/TRX | per-symbol single-cohort | 2.475% (below 5.56% parity) | INERT-by-importance (n=4 catalog) |
| **v1 Pool A** | BTC+ETH joint | pool model | 3.44%/feature (above 2.38% parity) | LEARNED-NEGATIVE |
| **v1 single-sym (C/D/E)** | LINK/LTC/DOT separate | per-symbol | 1.83-2.83%/feature (varies vs 2.38% parity) | mixed (DOT z90 PASS, LTC borderline) |

### 4.2 Pool Model A is the load-bearing lever

Pool A's gain share 6.88% is 1.9× the single-symbol mean (3.66-5.65%). LM Master Phase 7.4 §3 mechanism: pool's joint BTC+ETH loss surface lets trees use `funding × symbol-dummy` splits — a structural interaction that per-symbol architecture mechanically cannot represent. v3's 3 per-symbol models at iter-v3/019/023/024/082 inherited the single-symbol limitation.

### 4.3 Forward implications

The architecture-conditional learning observation is the load-bearing structural rationale for /024:
- Funding is mean-informative (model learns average effect ≈ zero).
- Funding is tail-load-bearing (+78.55% IS concentration in extreme bands evaporates under retraining).
- **Regime-conditional sub-models harvest the tail edge explicitly** — train one model on `|funding_z30| > 1.5` subset, one on `≤ 1.5`, combine at inference via regime gate. The "multiple smaller models per regime" framing directly tests the LEARNED-NEGATIVE hypothesis.

## 5. /027 bundle: 2 specialists confirmed; funding-family EXCLUDED

Post-/023, /027 substrate is settled to 2-specialist configuration UNCHANGED from /022 post-state:

| Component | Provenance | Bundle role | Status | Multi-seed Δ target |
|---|---|---|---|---|
| Pool baseline (5 sym, A/C/D/E unchanged) | BASELINE_V1.md | Pool anchor | LOCKED | 0 |
| LINK-only specialist (Model C') | /018 PROMISING-INERT-FAVORABLE | Alpha-enhancement | LOCKED | **+0.80** |
| ETH-only + symmetric BTC-trend gate (Model G) | /019 PROMISING | Alpha-enhancement | LOCKED | **+0.50** |
| BTC in pool via Model A | /020 NEG-CAT EXCLUDED | Pool baseline only | LOCKED | — |
| LTC in pool via Model D | /022 NEG-CAT EXCLUDED | Pool baseline only | LOCKED | — |
| **funding-family** | **/023 LEARNED-NEGATIVE EXCLUDED** | **NOT in bundle** | **LOCKED at /023 closeout** | — |
| DOT (TBD /024+ routing) | pending regime-conditional | TBD | PENDING | TBD |

**Bundle target at /027 multi-seed**: 2-specialist nominal Σ = +1.30 if independent; realistic with correlation drag + multi-seed variance reduction = **+1.10 to +1.30 OOS Sharpe** (UNCHANGED from /022 post-state).

**Why funding-family NOT bundled**: LEARNED-NEGATIVE classification means signal IS present but OOS sign-negative. Bundling as "alpha-enhancement" would be category error (the feature's contribution is OOS-negative). Bundling as "strictly accretive component decision" (per `feedback_promising_mechanical_subtype.md`-sister) does NOT apply because the feature is not mechanical drag removal — it's a feature-family signal that fails OOS realization.

**Three consecutive cycle-3 EXPLORATIONs (/020 + /022 + /023) have EXCLUDED candidates from /027 substrate**: BTC + LTC stay IN POOL, funding-family DROPPED. /027 substrate is STABLE at 2 specialists pending /024+ outcomes.

## 6. Track record (LM Master post-/023)

### LM Master directional + methodology track

| Iteration | Modal prediction | Observed | Directional score | Methodology score |
|---|---|---|:---:|:---:|
| /018 | PROMISING-INERT favorable | PROMISING-INERT-FAVORABLE | 1/1 | 1/1 |
| /019 | PROMISING modal 35% | PROMISING | 1/1 | 1/1 |
| /020 | INERT-no-effect modal 40% | NEGATIVE-CATASTROPHIC | 0/1 | 1/1 |
| /021 | CONFIRMED-H1 45% × CONFIRMED-H2 70% | BORDERLINE × REFUTED | 0.5/1 | 1/1 |
| /022 | INERT modal 40% | NEGATIVE-CATASTROPHIC (10% tail) | 0/1 | 1/1 |
| **/023** | **INERT modal 52%** | **NEGATIVE clean (18% tail)** | **0/1 (NEG tail directional)** | **1/1 (DUAL GATE gain-share LOAD-BEARING)** |

**Running totals post-/023**:
- **Directional**: **2.5/7 → 36%** (consistent modal-miss pattern on non-POSITIVE_EVERYWHERE axes; tail upweighting reliable)
- **Methodology**: **6/6 → 100% PERFECT** (DUAL GATE gain-share check at /023 was the load-bearing diagnostic that distinguished LEARNED-NEGATIVE from v3 INERT-by-importance)

### Per /023, the load-bearing methodology call

LM Master Phase 4.5 §4 mandated DUAL GATE: rank ≤ 14/42 on ≥ 2 cohorts AND family combined gain share ≥ 4.0% (vs QR's initial rank-only PROMISING-clean threshold). Without this strengthening, /023 verdict mis-classification risk was **~15pp** per LM Master §9. Observed:
- Portfolio gain 5.40% > 4.76% uniform parity → above-parity (NOT v3 INERT pattern)
- Pool A gain 6.88% + LINK 5.65% + DOT 5.49% → 3/4 cohorts PROMISING-clean (rank ≤ 14 AND gain ≥ 4.0%)
- F1 OOS Δ -0.2031 → NEGATIVE band (3bp inside threshold)
- **Verdict cell COLLISION**: PROMISING-clean (per F-AXIS #1 DUAL GATE) × NEGATIVE (per F1) = **LEARNED-NEGATIVE** sub-classifier

Without the gain-share check, rank alone (top-third on 3 cohorts) would have suggested PROMISING-clean; F1 NEGATIVE would then have created an unresolvable scoring ambiguity. The DUAL GATE provides the proper diagnostic frame.

### Forward LM Master deference rule (n=4 confirmation at /023)

At /020 + /022 + /023, LM Master's tail upweighting / methodology strengthening have been **load-bearing 3 of 3 times** on non-POSITIVE_EVERYWHERE axes. Per `feedback_iteration_quality.md` LM Master deference rule at ≥ 5pp tail-class re-weighting, future v1 briefs should:
- Adopt LM Master priors over QR initial draft if LM Master upweights tail by ≥ 5pp.
- Adopt LM Master methodology strengthening at Phase 4.5 §4 / §5 verbatim into brief Section 4 falsifiers.
- Treat LM Master modal directional priors as informational with explicit reserve for tail outcomes (consistent modal-miss pattern at single-seed EXPLORATION on non-POSITIVE_EVERYWHERE axes).

## 7. /024 axis decision: REGIME-CONDITIONAL SUB-MODELS (PRIMARY)

Per user "be bold; diversification; multiple smaller models per regime" directive (Phase 8 prompt) + LM Master Phase 7.4 §4 PRIMARY (Option B) + Critic Phase 7.5 review.md §Path Forward CONVERGENT routing:

### Path Forward (verbatim from Critic Phase 7.5 review.md §Path Forward)

> Three candidates honoring axis-rotation discipline:
>
> 1. **Per-cohort drawdown brake** — family `risk-primitive` — STATEFUL → MANDATORY deadlock-impossibility proof per A8 + iter-v3/054. Brief Section 11.4 pre-committed default.
>
> 2. **Regime-conditional sub-models** — family `model-arch` — Train 2 sub-models per cohort (|funding_z30|>1.5 vs ≤1.5); STATELESS regime gate. DUAL GATE evidence supports 3/4 cohorts. HIGH-RISK MANDATORY.
>
> 3. **Open-interest delta family** — `feature-family` REPEAT — non-OHLCV, non-funding sister primitive. Borderline rotation but Section 11.7 permits.

### /024 PRIMARY: Regime-conditional sub-models (model-arch family)

**Choice rationale**:
1. **User mandate alignment**: directly tests "multiple smaller models per regime" — the user prompt's load-bearing axis criterion.
2. **LM Master Phase 7.4 §4 PRIMARY RECOMMENDATION**: directly addresses the LEARNED-NEGATIVE mechanism (funding mean-informative + tail-load-bearing — regime gating harvests the tail explicitly).
3. **Critic Phase 7.5 #2 ENDORSEMENT**: "DUAL GATE evidence supports 3/4 cohorts. HIGH-RISK MANDATORY" — Critic places it #2 only because Path Forward #1 (drawdown brake) is sister-axis to recent risk-primitive work; #2 is the architecturally fresher option and matches user directive.
4. **DUAL GATE gain-share evidence from /023**: Pool A 6.88% + LINK 5.65% + DOT 5.49% show the funding signal IS learned but tail-bearing — regime-conditional architecture explicitly separates the regimes the LightGBM-at-single-seed mean-averages over.
5. **Axis rotation**: model-arch family last used at /003 (per-symbol Model A split, NEGATIVE); /023 prior 5 = methodology-pivot/per-cohort-LINK/ETH/BTC/LTC + feature-family — model-arch is NOT in prior 5 (rotation VALID).
6. **Cycle-3 cadence**: /024 is #9 of 10 EXPLORATIONs; /025 sanity slot + /026 optional flexibility + /027 CONFIRMATION earliest.

### /024 Secondary: Per-cohort drawdown brake (risk-primitive family)

**Brief pre-commit**: if /024 regime-conditional encounters QE-blocking implementation complexity (e.g., extreme-band data insufficiency: 14% × 5727 = 800 bars per symbol — borderline thin), /024 reverts to per-cohort drawdown brake (Critic Path Forward #1). **STATEFUL — MANDATORY deadlock-impossibility proof** per A8 catalog + iter-v3/054 lesson (closed-loop simulator OR formal deadlock-impossibility proof in brief Section 2). Default brief Section 11.4 sub-section if pivot fires.

### /024 Tertiary: Open-interest delta (feature-family REPEAT, borderline rotation)

If /024 regime-conditional AND per-cohort drawdown brake both BLOCK at Phase 5.5 gate, tertiary fallback is open-interest delta family (NEW non-OHLCV sister primitive). Borderline axis-rotation (feature-family last used at /023) but Critic Path Forward #3 explicitly permits per Section 11.7.

### /024 selection: REGIME-CONDITIONAL SUB-MODELS

**Selected**: Regime-conditional sub-models (model-arch family). HIGH-RISK MANDATORY per Critic verdict. Wall-clock estimate 60-90 min EXPLORATION (2× ENSEMBLE_SIZE per cohort vs baseline single-model — Pool A + LINK + LTC + DOT = 4 cohorts × 2 sub-models = 8 sub-models total vs baseline 4 models). 2h HARD CAP. Single-seed=42 EXPLORATION default; HIGH-RISK declaration mitigation (per /022 NEG-CAT + /023 NEG-clean lineage at single-seed — cycle-3 HIGH-RISK count now at /020 + /022 + /023 = 3 HIGH-RISK declarations, but per v1 rule "3+ HIGH-RISK >1σ negative deltas mandates multi-seed" — only /020 and /022 are >1σ negative; /023 NEG-clean is 3bp inside threshold so does NOT count toward the 3+ NEG mandate trigger).

## 8. Process incidents: 5th cycle-3 engineering_report violation; orchestrator-layer fix needed

### The incident (Critic BLOCK-PENDING-FIX at `36ec61f`)

Per brief Section 10.4 binding pre-commitment: "no Phase 7.5 Critic dispatch without engineering_report.md present (CARRY-FORWARD from /020/021/022 Rec #1 BINDING)". At Phase 7.5 dispatch on `4d6f1ed` (post-Phase-7.4 LM Master post-mortem), `reports-v1/iteration_v1-023/engineering_report.md` was **MISSING**. Critic emitted BLOCK-PENDING-FIX at `36ec61f`.

**5th cycle-3 engineering_report violation**:
- /019: missing at Phase 7.5 dispatch (1st)
- /020: missing at Phase 7.5 dispatch (2nd — Critic Rec #1 BINDING)
- /021: initial missing; resolved at BLOCK-PENDING-FIX (3rd — "RESOLVED")
- /022: missing at Phase 7.5 dispatch (4th — RE-VIOLATION post-/021 RESOLVED)
- **/023: missing at Phase 7.5 dispatch (5th — 4-cycle pattern continues)**

### Resolution

Per BLOCK-PENDING-FIX protocol: retrospective engineering_report.md written from existing CSVs at commit `c9471ee` (zero backtest re-run; zero src/ changes; 30 tests still PASS). The 263-line report:
- Verifies all 6 BLOCK-PENDING-FIX checkpoint items (implementation summary; backtest config; wall-clock + timing; F-AXIS-MECHANISM measurements; test outputs; anomaly notes).
- Documents DUAL GATE gain shares per cohort (Pool A 6.88%, LINK 5.65%, LTC 3.66%, DOT 5.49%, portfolio 5.40%).
- Documents LEARNED-NEGATIVE sub-classifier framing per LM Master Phase 7.4 §2 verdict cell collision diagnostic.
- 5 anomalies documented (parquet regen, ic_matrix gap, RuntimeWarning, OOS trade band overshoot, spot-check).

Critic re-evaluated at `4c8cab4` (single-pass post-fix per BLOCK-PENDING-FIX protocol) and emitted FINAL verdict **EXPLORATION-NEGATIVE clean**. Defect axis (report content completeness) PASS; Empirical verdict LOCKED at NEGATIVE clean.

### Carry-forward action (NOT QR scope this iteration)

Per Critic Phase 7.5 FINAL Recommendation #3 (CARRY-FORWARD from /020/021/022 Rec #1):

> **Orchestrator-layer engineering_report dispatch gate** — 5th cycle-3 incident. Skill-maintainer scope; pre-Phase-7.5 existence check needed.

This is a **SKILL-LAYER / ORCHESTRATOR fix**, NOT a brief-level fix. The brief Section 10.4 contract pre-commitment is necessary but not sufficient; **5 incidents across 5 iterations** confirms brief-level contracts CANNOT enforce. Next action for orchestrator/skill maintainer: gate Phase 7.5 dispatch on file existence check at the dispatch-level (orchestrator layer), with NON-RETROSPECTIVE-FORGIVENESS — engineering_report.md missing at Phase 7.5 dispatch becomes BLOCK-PENDING-FIX automatically without Critic intervention.

## 9. Merge Decision: NO-MERGE

**NO-MERGE (EXPLORATION-NEGATIVE clean; BASELINE_V1 UNCHANGED)**.

BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). The /023 iteration produces:

- **No new edge ingredient for /027 bundling** — funding-family EXCLUDED per LEARNED-NEGATIVE verdict (information ingested + OOS realization failed).
- **Funding-family stays out of /027** — 2-specialist bundle UNCHANGED from /022 post-state.
- **One NEW structural finding carrying forward** (codified at /023 closeout):
  - NEW memory `feedback_v1_learned_negative_subtype.md` — v1 verdict sub-classifier LEARNED-NEGATIVE; v1-vs-v3 architectural distinction; informs future v1 verdict matrices.
- **Three src/ changes from /023** (all in commit `74f5689`):
  - `src/crypto_trade/features_v1/funding_v1.py` (NEW module, ~120 lines): backward-compatible additive feature module; stays on branch — restoring as baseline would silently add 2 features to V1_FEATURE_COLUMNS_PRUNED default behavior.
  - `src/crypto_trade/features_v1/__init__.py`: V1_FEATURE_COLUMNS_PRUNED extended 40→42 alphabetically; sanity assert. Stays on branch (default behavior change).
  - `run_baseline_v1.py`: iter-v1/023 dispatch elif branch + `_iter021_fi_strategies` renamed to `_post_dispatch_fi_strategies` (Carry-forward from /022 Critic Rec #2). The rename is BACKWARD-COMPATIBLE infrastructure; merges to trunk via branch HEAD as pure additive (defaults unchanged — generic list initialized empty by default elif branch). The iter-v1/023 elif branch itself stays on branch (opt-in dispatch; not invoked at default baseline).

**Trunk merge**: The `_post_dispatch_fi_strategies` rename + generic dispatch list infrastructure merges to trunk via branch HEAD as pure additive backward-compatible infrastructure (default empty list; opt-in). The `features_v1/funding_v1.py` module + V1_FEATURE_COLUMNS_PRUNED 42-col extension + `run_baseline_v1.py:V1_ITER023` elif branch stay on branch (opt-in; not invoked at default baseline). Per `feedback_v3_baseline_update_policy.md` adopted by v1: BASELINE_V1.md UPDATE NOT triggered (EXPLORATION-NEGATIVE; only CONFIRMATION-MERGE updates baseline).

**Tag**: `v0.v1-023` to be applied after this Phase 8 closeout commit.

## 10. Path Forward (verbatim from Critic — Phase 7.5 FINAL recommendations)

From `briefs-v1/iteration_v1-023/review.md` §"Recommendations to QR (for /024+)" + §"Path Forward":

> ### Recommendations to QR (for /024+)
>
> 1. **Catalog LEARNED-mechanism in /023 diary + memory** — create `feedback_v1_learned_negative_subtype.md` documenting v1-vs-v3 architectural distinction (pool Model A joint loss surface ≠ v3 per-symbol). Apply LEARNED-NEGATIVE explicitly as sub-classifier in /024+ matrices.
>
> 2. **/024 axis selection** — Path Forward ordered:
>    - #1 Per-cohort drawdown brake (risk-primitive, brief pre-commit)
>    - #2 Regime-conditional sub-models (model-arch, LM Master + user directive)
>    - #3 Open-interest delta (feature-family REPEAT, borderline rotation)
>
> 3. **Orchestrator-layer engineering_report dispatch gate** — 5th cycle-3 incident. Skill-maintainer scope; pre-Phase-7.5 existence check needed.
>
> ### Path Forward (for /024 axis selection)
>
> Three candidates honoring axis-rotation discipline:
>
> 1. **Per-cohort drawdown brake** — family `risk-primitive` — STATEFUL → MANDATORY deadlock-impossibility proof per A8 + iter-v3/054. Brief Section 11.4 pre-committed default.
>
> 2. **Regime-conditional sub-models** — family `model-arch` — Train 2 sub-models per cohort (|funding_z30|>1.5 vs ≤1.5); STATELESS regime gate. DUAL GATE evidence supports 3/4 cohorts. HIGH-RISK MANDATORY.
>
> 3. **Open-interest delta family** — `feature-family` REPEAT — non-OHLCV, non-funding sister primitive. Borderline rotation but Section 11.7 permits.
>
> QR Phase 8 selects.

**QR Phase 8 selection**: **#2 Regime-conditional sub-models (model-arch)** as PRIMARY per user "multiple smaller models per regime" directive + LM Master Phase 7.4 §4 PRIMARY + DUAL GATE evidence 3/4 cohorts supporting. Secondary: #1 per-cohort drawdown brake (risk-primitive, brief Section 11.4 pre-committed default if regime-conditional encounters QE-blocking complexity). Tertiary: #3 open-interest delta (feature-family REPEAT, borderline rotation).

## 11. Next Iteration Ideas

### /024 PRIMARY (per user + LM Master + Critic CONVERGENT)

**/024 = regime-conditional sub-models** — family `model-arch`. Train 2 sub-models per cohort partitioned by `|funding_z30| > 1.5` vs `≤ 1.5`; combine at inference via stateless regime gate (no state propagation, no deadlock risk). HIGH-RISK MANDATORY per Critic. DUAL GATE evidence from /023 supports 3 of 4 cohorts (Pool A + LINK + DOT; LTC borderline FAIL). Wall-clock estimate 60-90 min EXPLORATION; 2h HARD CAP. Single-seed=42 default; HIGH-RISK mitigation single-seed opt-in (cycle-3 HIGH-RISK lineage /020 + /022 NEG-CAT + /023 NEG-clean — /023 3bp inside threshold does NOT trip 3+ NEG-band mandate trigger per v1 rule literal language).

### /025 FLEXIBLE per /024 outcome

Per Critic Path Forward + LM Master /024 staging matrix (TBD at /024 closeout):

- **/025 candidate axis A (if /024 PROMISING)**: continue with regime-conditional variants (e.g., explore z90 threshold instead of z30; stack regime gates on different feature families).
- **/025 candidate axis B (if /024 NEGATIVE/INERT)**: per-cohort drawdown brake — family `risk-primitive`. STATEFUL → MANDATORY deadlock-impossibility proof per A8 catalog + iter-v3/054 lesson.
- **/025 candidate axis C (long-tail)**: open-interest delta — family `feature-family` REPEAT. Borderline rotation; non-OHLCV sister primitive.

### /026 pre-CONFIRMATION sanity (FINAL EXPLORATION)

Layer B determinism re-verification at /027 multi-seed config; final brief Section 11.7 routing matrix verification; engineering report contract re-confirmation (if orchestrator-layer fix landed by then); anchor-frame BINDING locked.

### /027 CONFIRMATION (Option β PRE-COMMITTED per /021 §7)

Bundle architecture: FULL POOL (5 sym unchanged — A/C/D/E baseline) + 2 alpha-enhancement specialists (LINK + ETH+gate). BTC + LTC + DOT in pool. Multi-seed n_seeds ≥ 5 per `feedback_v1_seed_count_non_negotiable.md`. Pre-compute BTC-in-pool + LTC-in-pool annualized-daily-Sharpe directly (no proxy) per anchor-frame BINDING. Bundle ceiling **+1.10-1.30 OOS Sharpe** at 2-specialist baseline.

If /024 regime-conditional achieves PROMISING, /027 bundle MAY expand to 3-component (LINK + ETH+gate + regime-conditional sub-models); bundle target moves to **+1.30 to +1.50 OOS Sharpe** under correlation drag.

## 12. Axis Rotation Status (v1-only)

- **This iter's family**: `feature-family` (NEW 15th family — FIRST cycle-3 feature-family usage; cycle-2 /007 + /009 NEGATIVE-NEGATIVE-compound prior)
- **Prior 5 EXPLORATION families** (going INTO /023): per-cohort-specialization-LINK (/018), per-cohort-specialization-ETH (/019), per-cohort-specialization-BTC (/020), methodology-pivot (/021), per-cohort-specialization-LTC (/022)
- **Rotation honored**: YES — `feature-family` in NONE of prior 5 (different from per-cohort-specialization-X AND methodology-pivot)
- **Updated prior 5 going into /024**: per-cohort-specialization-ETH (/019), per-cohort-specialization-BTC (/020), methodology-pivot (/021), per-cohort-specialization-LTC (/022), **feature-family (/023)**
- **/024 axis-family**: **model-arch** (per user + LM Master + Critic CONVERGENT; model-arch last used at /003 NEGATIVE; NOT in prior 5; rotation VALID)

## 13. Brief Section 13 Self-Check Addendum

A Phase 7+8 self-check addendum will be appended to `briefs-v1/iteration_v1-023/research_brief.md` Section 13 documenting:
- Pre-registered verdict priors vs observed (NEG-clean 18% tail materialized; modal INERT 52% missed by 3bp inside threshold)
- DUAL GATE F-AXIS #1 PROMISING-clean × F1 NEGATIVE verdict cell COLLISION → LEARNED-NEGATIVE sub-classifier catalogued
- LM Master Phase 4.5 §4 DUAL GATE strengthening LOAD-BEARING (methodology track 6/6 perfect; directional 2.5/7 = 36% modal accuracy on non-POSITIVE_EVERYWHERE axes)
- Engineering report 5th cycle-3 incident — orchestrator-layer NON-RETROSPECTIVE-FORGIVENESS fix REQUIRED
- v1-vs-v3 architectural distinction codified (pool Model A joint loss surface enables learning per-symbol architecture cannot)
- /024 axis selection: REGIME-CONDITIONAL SUB-MODELS (model-arch) per CONVERGENT routing

## 14. Files & Commits on Branch

- Branch: `iteration-v1/023` from `iter-v1/022` closeout (tag `v0.v1-022`)
- HEAD at QR Phases 1-5 brief: `009cccb`
- HEAD at Phase 4.5 LM Master advisory: `fedf2ce`
- HEAD at Brief Section 3.4 LM Master responses: `6708b02`
- HEAD at Phase 5.5 gate PASS: `28767da`
- HEAD at QE implementation: `74f5689` (feat — funding-rate features + V1_FEATURE_COLUMNS_PRUNED 40→42)
- HEAD at Phase 6.0 Critic pre-flight PASS: `f4d56b1`
- HEAD at LM Master Phase 7.4 post-mortem: `4d6f1ed`
- HEAD at Critic Phase 7.5 BLOCK-PENDING-FIX initial review: `36ec61f`
- HEAD at BLOCK-PENDING-FIX engineering_report.md retrospective fix: `c9471ee`
- HEAD at Critic Phase 7.5 FINAL (post-fix): `4c8cab4`
- HEAD at Phase 7 evaluation memo: TBD (this closeout commit batch)
- HEAD at Phase 8 closeout (THIS COMMIT): TBD (this closeout commit batch)
- Reports artifacts in `reports-v1/iteration_v1-023/`

Key commits in /023:
- `009cccb` — docs: QR Phases 1-5 + feature-family funding-rate brief
- `fedf2ce` — docs: Phase 4.5 LM Master advisory
- `6708b02` — docs: Section 3.4 LM Master responses + F-AXIS #1 strengthening
- `28767da` — docs: phase 5.5 gate PASS
- `74f5689` — feat: funding-rate feature family + V1_FEATURE_COLUMNS_PRUNED 40→42
- `f4d56b1` — docs: Phase 6.0 Critic pre-flight PASS
- `4d6f1ed` — docs: Phase 7.4 LM Master post-mortem — LEARNED-NEGATIVE
- `36ec61f` — docs: Phase 7.5 Critic review — BLOCK-PENDING-FIX
- `c9471ee` — docs: engineering_report.md retrospective (Critic BLOCK-PENDING-FIX)
- `4c8cab4` — docs: Phase 7.5 FINAL — EXPLORATION-NEGATIVE clean
- (Phase 7 evaluation memo this commit batch) — `briefs-v1/iteration_v1-023/phase7_evaluation.md`
- (Phase 8 closeout this commit batch) — Phase 8 diary + merge decision (NO-MERGE)

**Trunk merge**: `_post_dispatch_fi_strategies` rename + generic dispatch list infrastructure merges to trunk via branch HEAD as pure additive backward-compatible infrastructure (default empty list; opt-in). The `features_v1/funding_v1.py` module + V1_FEATURE_COLUMNS_PRUNED 42-col extension + `run_baseline_v1.py:V1_ITER023` elif branch stay on branch (opt-in; not invoked at default baseline). BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`).

**Tag**: `v0.v1-023` to be applied after this Phase 8 closeout commit.
