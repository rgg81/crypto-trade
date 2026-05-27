# iter-v1/023 — Phase 7 OOS Evaluation Memo

**Author**: QR (Phase 7). HEAD `4c8cab4` (Critic Phase 7.5 FINAL post-BLOCK-PENDING-FIX `c9471ee` re-evaluation).

**Anchor**: `v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`). Portfolio IS Sharpe **+0.2829** / OOS Sharpe **+0.6637** / OOS trades 189 / 5-sym universe / 4 models (A, C, D, E).

**Verdict (Critic Phase 7.5 FINAL)**: **EXPLORATION-NEGATIVE clean** — Section 8 Row 6 (F1 OOS Δ ∈ [-0.55, -0.10)). Honored per `feedback_no_cheating.md`; 3bp distance from INERT threshold (-0.20) NOT exploited for upward reclassification.

---

## 1. Verdict vs Phase 5 Priors

### 1.1 Pre-registered priors (LM Master Phase 4.5 BINDING)

QR initial 15/10/45/15/10/5 → LM Master RECALIBRATED **12/8/52/18/8/2** at Phase 4.5 closeout.

| Verdict class | LM Master prior | Observed |
|---|---:|---|
| PROMISING (clean) | 12% | |
| PROMISING-INERT-FAVORABLE | 8% | |
| INERT (modal) | **52%** | |
| **NEGATIVE clean** | **18%** | **MATERIALIZED** (3bp inside threshold) |
| NEGATIVE-CATASTROPHIC | 8% | |
| PROMISING-METHODOLOGY | 2% | |

**Outcome: 18% tail materialized.** Modal INERT 52% MISSED; NEG-clean tail captured. The 3bp distance to INERT threshold (F1 OOS Δ = -0.2031 vs threshold -0.20) is meaningful: at single-seed=42 / n_trials=18 EXPLORATION budget the verdict is empirically NEGATIVE-clean but methodologically close to the modal INERT tail.

### 1.2 Falsifier-Mechanism Reconciliation

DUAL GATE F-AXIS #1 (LM Master §4 strengthened rank + family gain-share check) was load-bearing:

| Cohort | Gain share | Rank (z90 of 42) | Threshold met | F-AXIS #1 |
|---|---:|---:|---|---|
| Pool Model A | **6.88%** | 11 | rank ≤ 14 + gain ≥ 4.0% | **PROMISING-clean** |
| LINK Model C | **5.65%** | 11 | rank ≤ 14 + gain ≥ 4.0% | **PROMISING-clean** |
| DOT Model E | **5.49%** | 10 | rank ≤ 14 + gain ≥ 4.0% | **PROMISING-clean** |
| LTC Model D | 3.66% | 14 | borderline FAIL (gain < 4.0%) | borderline |
| **Portfolio** | **5.40%** | — | > uniform parity 2.38%/feature × 2 = 4.76% | **above-parity** |

**3 of 4 cohorts (Pool A + LINK C + DOT E) cleanly PROMISING-clean per the dual gate** — yet F1 OOS Sharpe Δ NEGATIVE. The verdict cell COLLISION (F-AXIS #1 PROMISING-clean × F1 NEGATIVE) is the LEARNED-NEGATIVE sub-classifier diagnostic. F-AXIS-MECHANISM #2 (trade count 257 OOS / 694 IS) and F-AXIS-MECHANISM #3 (n_eff = 9, modal hit on [5, 10] LM band) both PASS.

### 1.3 Hypothesis review

Brief Section 1 H_AXIS: "v1's pool Model A joint loss surface enables LightGBM to learn funding-rate signal via cross-cohort `funding × symbol-dummy` splits that v3's per-symbol architecture cannot."

**Outcome**: Hypothesis is **partially vindicated**. Pool Model A gain share 6.88% vs v3/082 4-feature family aggregate 9.90% (per-feature 2.475% < 5.56% v3 uniform-parity). v1 LightGBM **does learn** the funding signal at portfolio level (above-uniform-parity 5.40% > 2.38%/feature × 2 = 4.76%); v3 did NOT. **However**, learning does not translate to OOS lift. Mechanism is **mean-informative but tail-load-bearing** per LM Master Phase 7.4 §3: the +78.55% IS PnL concentration in z30 ∈ [-2, -1] band evaporates under retraining (basin-relocation per /022 pattern); LightGBM at single-seed finds the MEAN funding effect (~zero), tail edge requires explicit regime gating.

---

## 2. LEARNED-NEGATIVE structural finding (v1-vs-v3 architectural distinction)

### 2.1 The new verdict sub-classifier

**LEARNED-NEGATIVE** (catalogued at /023 closeout): a feature-family axis where:
1. Information is INGESTED — family combined gain share > uniform parity × n_features (e.g., 5.40% > 4.76%); top-third importance ranks on ≥ 2 cohorts.
2. OOS realization FAILS — F1 OOS Sharpe Δ in NEGATIVE band ∈ [-0.55, -0.10).

This is structurally distinct from:
- **PROMISING** (information ingested + OOS positive lift): bundleable to CONFIRMATION
- **PROMISING-INERT** (no information ingested + OOS positive lift): NOT bundleable (lottery)
- **INERT-by-importance** (no information ingested + OOS flat): v3 pattern at 4-data-point catalog
- **NEGATIVE-clean** (mechanism-agnostic): pre-registered verdict cell

LEARNED-NEGATIVE is a **diary sub-classifier**, NOT a verdict-class elevation. Pre-registered Row 6 (NEGATIVE clean) wins per `feedback_no_cheating.md`. The sub-classifier is informational for future axis selection.

### 2.2 v1 ≠ v3 architectural distinction

| Track | Universe | Architecture | Funding gain share | Verdict |
|---|---|---|---:|---|
| **v3** | BCH/LDO/TRX (3-sym, per-symbol) | per-symbol single-cohort models | 9.90% / 4 features = **2.475%/feature** (BELOW 5.56% parity) | INERT-by-importance (4-data-point catalog) |
| **v1** | BTC/ETH/LINK/LTC/DOT (5-sym, pool A + per-sym C/D/E) | Pool A (BTC+ETH joint) + 3 per-sym | 5.40% / 2 features = **2.70%/feature** (ABOVE 2.38% parity) | **LEARNED-NEGATIVE** (new cell) |

**Structural lever**: pool Model A's joint BTC+ETH loss surface enables `funding × symbol-dummy` splits at depth 3-5 (per LM Master Phase 7.4 §3). v3's per-symbol architecture mechanically cannot compose this interaction. v1 Pool A gain share **6.88%** vs Models C/D/E (3.66-5.65%) confirms the architectural lever materialized partially. The architecture-conditional learning is genuine but not large enough to flip OOS sign at single-seed n_trials=18 EXPLORATION budget.

### 2.3 Forward implications

The LEARNED-NEGATIVE finding is **falsifiable** but **non-compoundable** for /027 bundling at EXPLORATION budget:
- The signal is genuine (gain share above parity, ranks top-third on ≥ 2 cohorts).
- The signal is NOT additive (mean funding effect ≈ zero at portfolio retraining; tail edge dissolved).
- **Regime-conditional architecture** could harvest the tail explicitly — this is the load-bearing structural rationale for /024 axis selection (Option B per LM Master §4: regime-conditional sub-models).

---

## 3. /027 bundle composition impact

**Funding-family NOT added** to /027 bundle. /027 substrate UNCHANGED at 2 specialists confirmed:

| Component | Provenance | Bundle role | Status |
|---|---|---|---|
| Pool baseline (5 sym, A/C/D/E unchanged) | BASELINE_V1.md | Pool anchor | LOCKED |
| LINK-only specialist (Model C') | /018 PROMISING-INERT-FAVORABLE | Alpha-enhancement +0.80 multi-seed target | LOCKED |
| ETH-only + symmetric BTC-trend gate (Model G) | /019 PROMISING | Alpha-enhancement +0.50 multi-seed target | LOCKED |
| BTC in pool via Model A | /020 NEG-CAT EXCLUDED | Pool baseline only | LOCKED |
| LTC in pool via Model D | /022 NEG-CAT EXCLUDED | Pool baseline only | LOCKED |
| **funding-rate family** | **/023 LEARNED-NEGATIVE EXCLUDED** | **NOT in bundle** | **LOCKED** |
| DOT (TBD /024+ routing) | pending | TBD | PENDING |

**Bundle target at /027 multi-seed**: 2-specialist nominal Σ = +1.30 if independent; realistic with correlation drag + multi-seed variance reduction = **+1.10 to +1.30 OOS Sharpe** (UNCHANGED from /022 post-state).

**Funding rationale**: LEARNED-NEGATIVE classification means signal IS present but OOS sign-negative; bundling as "alpha-enhancement" would be category error. The architecture-conditional learning observation IS bundleable as MECHANISM EVIDENCE for /024+ regime-conditional sub-model design.

---

## 4. LM Master track record (post-/023)

### Directional track

| Iteration | Modal prediction | Observed | Hit? |
|---|---|---|---|
| /018 | PROMISING-INERT favorable | PROMISING-INERT-FAVORABLE | 1/1 |
| /019 | PROMISING modal 35% | PROMISING | 1/1 |
| /020 | INERT-no-effect modal 40% | NEGATIVE-CATASTROPHIC | 0/1 |
| /021 | CONFIRMED-H1 45% × CONFIRMED-H2 70% | CONFIRMED BORDERLINE × REFUTED | 0.5/1 |
| /022 | INERT modal 40% | NEGATIVE-CATASTROPHIC | 0/1 |
| **/023** | **INERT modal 52%** | **NEGATIVE clean** | **0/1 (modal off; NEG-clean tail 18% captures direction)** |

**Cumulative**: **2.5/6 modal = 42%**. Modal calls miss on non-POSITIVE_EVERYWHERE cohort priors at single-seed EXPLORATION (consistent pattern at /020, /022, /023). Tail upweighting (NEG band) reliably directionally correct at non-POSITIVE_EVERYWHERE/non-routine axes.

**Phase 4.5 specifically**: LM Master Phase 4.5 §4 mandated DUAL GATE rank + gain-share check as CRITICAL load-bearing strengthening over QR's rank-only initial draft. This was **methodologically perfect** — without the gain-share check, /023 verdict mis-classification risk was ~15pp per LM Master §9 because rank-only would have classified portfolio rank-11 as PROMISING-clean; the gain-share clarification (5.40% portfolio, 6.88% Pool A) provided the diagnostic for the LEARNED-NEGATIVE cell that distinguished v1 from v3.

### Methodology track

| Iter | Methodology call | Outcome |
|---|---|---|
| /018 | F-AXIS-MECHANISM #3 fire-rate band | LOAD-BEARING PASS |
| /019 | symmetric ±8% gate design | LOAD-BEARING PASS |
| /020 | F-AXIS #1 + #2 + #3 LOAD-BEARING | LOAD-BEARING PASS |
| /021 | per-month FI accumulator + H1/H2 dual falsifier | LOAD-BEARING PASS |
| /022 | F-AXIS #3 fire-rate LOAD-BEARING ("mechanism ≠ outcome" pre-registered) | LOAD-BEARING PASS |
| **/023** | **DUAL GATE rank + gain-share check (Phase 4.5 §4 CRITICAL)** | **LOAD-BEARING PASS** |

**Cumulative methodology**: **6/6 = 100% perfect**. LM Master's methodology lane remains the strongest discipline. Phase 7.4 LM Master post-mortem also distinguished correctly between (a) v1 LEARNS funding (PROMISING-clean per-cohort) and (b) OOS realization fails (F1 NEGATIVE) — and proposed the LEARNED-NEGATIVE sub-classifier framing rather than seeking verdict-class elevation.

**Per /022 closeout finding**: future v1 briefs continue to weight LM Master priors over QR initial pass at non-POSITIVE_EVERYWHERE axes. /023 confirms the pattern at n=3 (/020 + /022 + /023).

---

## 5. Per-cohort feature gain-share evidence — supports /024 regime-conditional architecture

The per-cohort gain-share dispersion is the load-bearing evidence for /024 axis selection:

| Cohort | z30 rank | z90 rank | Family gain share | Per-cohort verdict |
|---|---:|---:|---:|---|
| Pool Model A (BTC+ETH joint) | 12 | 11 | **6.88%** | strongly informative |
| LINK Model C | 12 | 11 | 5.65% | informative |
| DOT Model E | 18 | 10 | 5.49% | informative (z90 dominant) |
| LTC Model D | 18 | 14 | 3.66% | borderline (below 4.0% gate) |
| Portfolio avg | — | — | **5.40%** | above uniform parity |

**Key patterns**:
1. **z90 outranks z30 in 3 of 4 cohorts** — longer-window (regime-level) feature carries more gain. LightGBM treats z90 as slow-moving regime indicator; z30 is marginally used. Trees at depth 3-5 cannot easily compose `funding × momentum × volatility` three-way interactions in 9 effective trials.
2. **Pool A (joint BTC+ETH) gain share 1.9× single-symbol cohorts (6.88% vs 3.66%)** — joint loss surface lets trees use `funding × symbol-dummy` splits explicitly. Architecture advantage materialized but not enough to flip OOS sign.
3. **DOT shows asymmetric z30/z90 ranks (18/10)** — z90 is rank-10 of 42 (top-quartile) but z30 is bottom-fifth. Regime-level funding signal MATTERS for DOT; short-window noise does not.
4. **LTC borderline FAIL on gain-share gate** — consistent with LTC's catastrophic OOS history (/022 NEG-CAT, /023 -57.68% OOS PnL). LTC's symbol-specific noise structure resists funding-rate learning.

**Mechanism interpretation**: 3 of 4 cohorts (Pool A + LINK C + DOT E) show signal; LTC is the outlier. **Regime-conditional sub-models (LM Master /024 PRIMARY recommendation, Option B)** directly test the "harvest the funding tail edge that LightGBM-at-single-seed mean-averages away" hypothesis. Architecture: train 2 sub-models per cohort partitioned by `|funding_z30| > 1.5` vs `≤ 1.5`; combine at inference via regime gate. Wall-clock 2× ENSEMBLE_SIZE per cohort ≈ 80 min EXPLORATION; extreme-band subset ~14% × 5727 = 800 bars per symbol — borderline thin but feasible.

This matches the user directive (per `feedback_v3_bold_research_mandate.md` and Phase 8 prompt context): "be bold; diversification; multiple smaller models per regime". The LEARNED-NEGATIVE finding from /023 IS the empirical evidence that regime-conditional architecture is the right next axis — funding is mean-informative + tail-load-bearing, so explicit regime gating at training time is the mechanism for /024.

---

## 6. Process integrity check (engineering_report.md 5th cycle-3 incident)

5th cycle-3 engineering_report violation:
- /019: missing at Phase 7.5 dispatch (1st)
- /020: missing at Phase 7.5 dispatch (2nd)
- /021: initial missing; resolved at BLOCK-PENDING-FIX (3rd)
- /022: missing at Phase 7.5 dispatch — RE-VIOLATION post-/021 RESOLVED (4th)
- **/023: missing at Phase 7.5 dispatch — 5th cycle-3 incident**

Resolution: retrospective engineering_report.md written from existing CSVs at `c9471ee` (263 lines); zero backtest re-run; zero src/ changes; tests still PASS. Critic re-evaluated at `4c8cab4` (single-pass post-fix per BLOCK-PENDING-FIX protocol) and emitted FINAL verdict **EXPLORATION-NEGATIVE clean**.

**Carry-forward action (orchestrator-layer, NOT QR scope)**: per Critic Phase 7.5 FINAL Rec #3, the engineering_report.md pre-existence check at Phase 7.5 dispatch MUST migrate to the orchestrator layer with NON-RETROSPECTIVE-FORGIVENESS semantics. Brief-level pre-commit contracts (Section 10.4) have failed 5 of 5 cycle-3 iterations to enforce; the contract must move up the stack.

---

## 7. Phase 7 conclusions

1. **Verdict**: EXPLORATION-NEGATIVE clean (Section 8 Row 6, F1 OOS Δ -0.2031 ∈ [-0.55, -0.10)). 18% LM Master tail materialized; 3bp inside the threshold.
2. **Structural finding (catalogued, NOT verdict elevation)**: LEARNED-NEGATIVE sub-classifier — first NEW v1 feature family with gain share above uniform parity at portfolio level (5.40% > 2.38%/feature × 2 = 4.76%). v1's pool Model A architecture enables learning v3's per-symbol architecture mechanically cannot.
3. **/024 axis**: REGIME-CONDITIONAL SUB-MODELS (Option B per LM Master Phase 7.4 §4 PRIMARY; matches user "multiple smaller models per regime" directive); secondary per-cohort drawdown brake (risk-primitive); tertiary open-interest delta (feature-family REPEAT, borderline rotation).
4. **/027 bundle**: 2 specialists confirmed (LINK +0.80 + ETH+gate +0.50); funding-family NOT added; BTC + LTC + DOT in pool.
5. **LM Master track**: directional 2.5/6 = 42% modal accuracy (consistent pattern at non-POSITIVE_EVERYWHERE axes); methodology 6/6 = 100% perfect (DUAL GATE gain-share check was load-bearing).
6. **Process**: 5th cycle-3 engineering_report incident; orchestrator-layer fix needed.

**Merge decision**: NO-MERGE; BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). Tag `v0.v1-023` to be applied at Phase 8 closeout.

---

**Phase 7 evaluation authored 2026-05-27. Anchor: `v0.v1-baseline-corrected` (`f8bc12c`). Cycle-3 EXPLORATION #8/10. Verdict: EXPLORATION-NEGATIVE clean. Sub-classifier: LEARNED-NEGATIVE (catalogued). /024 axis: regime-conditional sub-models (model-arch).**
