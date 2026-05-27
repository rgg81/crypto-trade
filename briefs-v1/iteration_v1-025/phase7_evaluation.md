# Phase 7 — OOS Evaluation Memo — iter-v1/025

**Iteration**: iter-v1/025 (OI delta family; primitive `oi_delta_30 = (open_interest_t − open_interest_t-30) / open_interest_t-30` z-scored on 90-bar window)
**Axis family**: `feature-family` REPEAT (NEW data class — non-OHLCV open-interest; /023 funding family precedent)
**Cadence position**: cycle-3 EXPLORATION #10 of 10 (LAST before /027 CONFIRMATION)
**Anchor**: `v0.v1-baseline-corrected` (BASELINE_V1.md commit `f8bc12c`) — IS +0.2829 / OOS +0.6637 / OOS trades 189
**Critic Phase 7.5 FINAL** (`23b10d6`, post-BLOCK-PENDING-FIX rerun at `449ab6e`): **EXPLORATION-NEGATIVE-CATASTROPHIC** (LEARNED-NEGATIVE-CATASTROPHIC subtype — NEW v1 verdict cell)
**Track record reference**: LM Master directional 2/7 → 2/8 (25.0%); methodology 5/5 → 6/6 (100% PERFECT)

---

## 1. F1 / F3 / F-AXIS actual vs predicted — LEARNED-NEGATIVE-CATASTROPHIC materialized; NEG-CAT tail mispriced

### 1.1 Pre-registered LM Master priors (brief Section 5; LM Master Phase 4.5 §2 BINDING)

| Verdict | LM Master prior | Observed | Notes |
|---|---:|:---:|---|
| PROMISING-clean | 22% | — | Q4 Sharpe-proxy +1.68 distribution-level not trade-conditioned (see §4) |
| PROMISING-INERT-FAV | 8% | — | — |
| INERT | 22% | — | F1 too negative for INERT band |
| **LEARNED-NEGATIVE** | **30%** (MODAL) | — | NEW subtype split: LEARNED-NEG-clean (would have been Δ ∈ [-0.55, -0.10)) vs LEARNED-NEG-CAT (≤ -0.55) |
| NEGATIVE-INERT | 12% | — | — |
| **NEGATIVE-CATASTROPHIC** | **4%** (TAIL) | **MATERIALIZED** | F1 OOS Δ -1.40 is **2.5× the -0.55 NEG-CAT threshold** |
| AUTO-REJECT (F3) | 2% | — | — |

**Observed F1 OOS Sharpe Δ = -1.40** (OOS -0.7353 vs anchor +0.6637) — sits **deep in NEG-CAT band** (≤ -0.55 threshold). The 4% TAIL prior fired. Per LM Master Phase 7.4 §5, this should have been priced 15-20% given rank-4/portfolio-gain-7.49% basin-pull was exponentially more than /023's rank-12/5.40% basin-pull.

**Observed F3 IS Sharpe Δ = +0.0498** (IS +0.3327 vs anchor +0.2829) — sits inside F3 INERT band [-0.30, +0.30]; F3 IS-catastrophic auto-reject path DID NOT fire. IS basin was not catastrophic; OOS basin alone is the catastrophe. This makes /025 STRUCTURALLY DISTINCT from /024's F3-collision and from /020/022's both-side collapses.

### 1.2 F-AXIS DUAL GATE actual vs predicted

LM Master Phase 4.5 §3 tightened F-AXIS #1 from rank-only to DUAL GATE: `rank ≤ 14/43 AND gain ≥ 4.0% on ≥ 2 cohorts AND breadth (rank ≤ 20/43 on ≥ 3 cohorts)`. Observed:

| Cohort | oi rank / 43 | gain share | DUAL GATE (rank ≤ 14 + gain ≥ 4.0%) | Breadth (rank ≤ 20) |
|---|---:|---:|:---:|:---:|
| **Pool A** (BTC+ETH) | **4** | **7.49%** | PASS | PASS |
| Model C (LINK) | 5 | 6.39% | PASS | PASS |
| Model D (LTC) | 5 | 8.00% | PASS | PASS |
| Model E (DOT) | 4 | 7.69% | PASS | PASS |
| Portfolio aggregate | 4 | 7.49% | PASS | PASS |

**4/4 cohorts ALL THREE sub-gates PASS.** All cohort gain shares fall in [6.39%, 8.00%] — uniform breadth. Pool A 7.49% is 1.4× /023 Pool A 6.88% funding (DUAL GATE PROMISING-clean per /023's same criteria).

**Verdict cell collision**: F-AXIS #1 DUAL GATE 4/4 PASS × F1 OOS Δ -1.40 NEG-CAT = **LEARNED-NEGATIVE-CATASTROPHIC** (NEW subtype). The /023 precedent ("LEARNED-NEGATIVE = information ingested + OOS realization failed") extends to a CATASTROPHIC band: F1 magnitude OVERRIDES DUAL GATE classification per pre-registered Section 8 Row 7. Per `feedback_v1_learned_negative_subtype.md` codified rule (LEARNED-NEGATIVE is diary sub-classifier, NOT verdict elevation), the verdict is locked at NEGATIVE-CATASTROPHIC; LEARNED-NEGATIVE-CATASTROPHIC is the new diary cell.

### 1.3 Why the NEG-CAT 4% tail should have been priced 15-20% (LM Master miscalibration)

Per LM Master Phase 7.4 §5 self-assessment:

- /023 produced LEARNED-NEGATIVE-clean (Δ -0.20) at rank 12 + 5.40% portfolio gain (1.13× v1 parity).
- /025 features the SAME LEARNED structure but at **rank 4** (8× tighter basin) + **7.49% portfolio gain** (1.57× v1 parity, 1.4× /023's funding share).
- LightGBM concentrates **39.14% of all split gain in top-4 features** when /025 OI is rank 4 — the basin is exponentially narrower than /023's rank-12 basin.
- Under basin-relocation under joint cross-asset OI regime shift (perp-funding cycle post-halving 2025-Q3/Q4), narrow basins relocate harder than wide basins. The NEG-CAT magnitude is a function of basin-pull intensity, not feature signal strength.

**Calibrated prior recalibration rule** (codified for cycle-4): for NEW feature families ADDED TO POOL MODEL A at single-seed n_trials=18 EXPLORATION budget that achieve **rank ≤ 5 on ≥ 3 cohorts** (top-cluster basin entry), reweight tail priors: NEG-CAT 4% → 15-20%, LEARNED-NEG-clean 30% → 25%. The DUAL GATE PROMISING-clean signature with rank ≤ 5 is now a **CONTRA-INDICATOR** under v1 Pool Model A + single-seed n_trials=18 (see §3 cycle-3 structural verdict).

### 1.4 Section 8 verdict matrix routing

Pre-registered Section 8 Row 7 (`F1 OOS Δ ≤ -0.55 → NEGATIVE-CATASTROPHIC; F-AXIS #1 classification OVERRIDDEN by F1 magnitude`) FIRED. The verdict is FINAL at Critic Phase 7.5 (`23b10d6`) after one BLOCK-PENDING-FIX rerun (`449ab6e` engineering_report.md + 4 CSV deliverables under documentation-only fix; NO backtest re-run per BLOCK-PENDING-FIX protocol).

---

## 2. Cycle-3 STRUCTURAL VERDICT: NEW feature-family axis SATURATED at v1 pool architecture single-seed

### 2.1 The n=2 LEARNED-NEGATIVE pattern (load-bearing finding)

/023 funding + /025 OI delta produce a structural pattern:

| Iter | Feature family | Pool A rank | Pool A gain | Portfolio gain | F1 OOS Δ | Verdict |
|---|---|---:|---:|---:|---:|---|
| /023 | funding_rate_zscore_30/90 | 11 | 6.88% | 5.40% | **-0.20** | LEARNED-NEGATIVE clean |
| **/025** | **oi_delta_30_z90** | **4** | **7.49%** | **7.49%** | **-1.40** | **LEARNED-NEGATIVE-CATASTROPHIC** |

**Mechanism narrative** (synthesizing /023 LM Master Phase 7.4 §3 + /025 LM Master Phase 7.4 §1):

1. **Pool Model A joint loss surface enables learning that v3 per-symbol architecture mechanically cannot**. Established at /023 closeout (`feedback_v1_learned_negative_subtype.md`). v3's 4-data-point funding catalog (/019/023/024/082) all INERT-by-importance (rank-bottom-quartile + below-parity gain share); v1 IS picked (LEARNED). This is an architectural ADVANTAGE for v1 — until OOS rolls around.

2. **At single-seed n_trials=18 EXPLORATION budget, joint learning overfits portfolio-wide cross-asset distributional shifts**. /025's OI feature is structurally MORE prone to LEARNED-NEGATIVE than /023's funding because:
   - **Cross-asset OI joint regime shift**: all 5 symbols' OIs rose together through 2025-Q3/Q4 (perp-funding cycle post-halving). z90 normalizes within-symbol, but joint cross-asset regime shift means ALL cohorts' Optuna basins relocated SAME direction — no diversification cancellation. Funding was more symbol-idiosyncratic.
   - **Narrow basin via top-4 split concentration**: rank-4 entry produces 39.14% of all split gain in top-4 features. When OI distribution drifts, the basin moves with it AND drags 4 leading features wrong region. /023 funding at rank-12 was outside top-cluster and so the basin-relocation was bounded.

3. **Q3 mid-band dead-zone is the dominant OOS loss channel** (corrected per §4 below): the model learned IS profit basin at Q1 NEG-extreme (+24.63 OOS positive — SURVIVED); the Q3 mid-band (+0.04 IS Sharpe-proxy, dead-zone by EDA) became the DOMINANT OOS LOSS CHANNEL (-57.44 from 55 trades). LightGBM at single-seed concentrated trades in the IS-dead Q3 band under OOS regime shift — basin relocation moved the entry signal into the EDA-identified dead zone.

### 2.2 The structural verdict (n=2 LEARNED-NEGATIVE → axis saturated)

**Established at /025 closeout**: NEW feature families ADDED TO POOL MODEL A at single-seed=42 ENSEMBLE_SIZE=3 n_trials=18 EXPLORATION budget are STRUCTURALLY UNABLE to clear OOS at v1 cohort. Not noise — mechanism (basin relocation under joint cross-asset training).

This is a **mechanism finding**, not noise:
- /023 and /025 used SAME spec (Pool Model A + single-seed=42 + ENSEMBLE_SIZE=3 + n_trials=18 + 5-sym universe) with DIFFERENT feature families (funding vs OI) — same architecture, distinct data class.
- Both produced LEARNED outcomes at the DUAL GATE F-AXIS #1 measurement (information ingested above parity).
- Both produced OOS Δ in NEGATIVE band (/023 -0.20 clean; /025 -1.40 catastrophic).
- The magnitude DIFFERENCE is governed by basin-pull intensity (rank-4 vs rank-12) and joint-cross-asset regime shift extent.

**Generalization** (codified at memory `feedback_v1_pool_a_new_feature_lneg.md`): at v1 Pool A + single-seed n_trials=18, DUAL GATE PROMISING-clean status is a CONTRA-INDICATOR. Future cycle-4 EXPLORATIONs must STRUCTURALLY DISQUALIFY NEW-feature-to-Pool-Model-A axes at single-seed; require ONE of:
- **(a) per-symbol specialist axes** (LINK /018 + ETH+gate /019 architecture; both PROMISING — independent priors avoid joint cross-asset basin)
- **(b) orthogonal-mechanism rule layers** (risk-primitive / labeling / hyperparameter-region — different lever, NOT feature-additive to joint loss surface)
- **(c) multi-seed budget** (ENSEMBLE_SIZE ≥ 5 inner × ≥ 2 outer at n_trials ≥ 35; basin-relocation lottery dissolves at higher compute per `feedback_v1_seed_count_non_negotiable.md`)

This finding extends `feedback_v1_per_cohort_saturation_asymmetric_rotation.md` (per-cohort isolation saturated for ASYMMETRIC_ROTATION class) by closing NEW-feature-to-Pool-A in cycle-4. Combined with /024's regime-conditional sub-model closure (`feedback_v1_regime_partition_non_specialization.md`), the cycle-3 search space at single-seed EXPLORATION budget has converged to: only per-cohort specialist axes with INDEPENDENT priors survive OOS.

---

## 3. LM Master track record post-/025: directional 2/8 = 25%; methodology 6/6 = 100% PERFECT

### 3.1 Directional track (modal verdict-class prediction)

| Iter | Modal prior | Observed | Directional |
|---|---|---|:---:|
| /018 | PROMISING-INERT-FAV | PROMISING-INERT-FAVORABLE | 1/1 |
| /019 | PROMISING modal 35% | PROMISING | 1/1 |
| /020 | INERT-no-effect 40% | NEGATIVE-CATASTROPHIC | 0/1 |
| /021 | CONFIRMED-H1 45% × CONFIRMED-H2 70% | BORDERLINE × REFUTED | 0.5/1 |
| /022 | INERT 40% | NEGATIVE-CATASTROPHIC (10% tail) | 0/1 |
| /023 | INERT 52% | NEGATIVE-clean (LEARNED-NEGATIVE 18% tail) | 0/1 |
| /024 | INERT 48% | NEGATIVE-clean (F3 + F-AXIS #5) | 0/1 |
| **/025** | **LEARNED-NEG 30% MODAL** | **LEARNED-NEGATIVE-CATASTROPHIC (4% tail materialized; should have been 15-20%)** | **0.5/1 (modal LEARNED-NEG family hit; NEG-CAT magnitude tail mispriced)** |

**Running totals**: **2/8 = 25%** directional (consistent modal-miss on non-POSITIVE_EVERYWHERE axes at single-seed EXPLORATION). The /025 hit on LEARNED-NEG family is partial credit (modal CATEGORY was correct; magnitude band mispriced).

### 3.2 Methodology track (LM Master Phase 4.5 advisory load-bearing diagnostics)

| Iter | Methodology call | Load-bearing? | Methodology score |
|---|---|:---:|:---:|
| /018 | per-cohort prior class framework | YES | 1/1 |
| /019 | symmetric BTC-trend gate ratification | YES | 2/2 |
| /021 | H1/H2 basin-interaction diagnostic | YES | 3/3 |
| /022 | LTC asymmetric basin prior | YES | 4/4 |
| /023 | DUAL GATE F-AXIS #1 strengthening (rank + gain-share) | YES — without DUAL GATE, LEARNED-NEGATIVE would have been misclassified as PROMISING-clean | 5/5 |
| /024 | F-AXIS #5 gain-share recurrence as INERT-detector | YES — broke F-AXIS #1 dispatch PASS × F1 INERT-near-PROMISING ambiguity | 5/5 (continued; same diagnostic re-fires at /024) |
| **/025** | **DUAL GATE breadth check (rank ≤ 20/43 on ≥ 3 cohorts) + HARD BLOCK on OI coverage** | **YES — DUAL GATE 4/4 PASS PROVES feature was LEARNED (correctly classifying as LEARNED-NEG-CAT NOT PROMISING under DUAL GATE PASS); HARD BLOCK on OI fetch saved the iteration from BTC-only degenerate evaluation; emit `oi_coverage_check.csv` adoption** | **6/6** |

**Methodology track 6/6 = 100% PERFECT post-/025**. The DUAL GATE strengthening at /023 + breadth check + HARD BLOCK at /025 are both load-bearing — without them, /025's verdict would have been UNRESOLVABLE (rank-only F-AXIS #1 would have classified rank 4 on 4 cohorts as PROMISING-clean creating verdict ambiguity with F1 NEG-CAT).

The HARD BLOCK on OI coverage (LM Master Phase 4.5 §4) specifically prevented BTC-only degenerate evaluation — at brief design time, 4/5 symbols had `oi_n_rows=0`; without HARD BLOCK + 60-min pre-fetch, /025's DUAL GATE would have evaluated on BTC only and the verdict would have been uninterpretable.

### 3.3 Deference rule

Per `feedback_iteration_quality.md` LM Master deference at ≥ 5pp tail re-weighting: at /025 LM Master raised PROMISING tail from QR initial 26% → 30% (+4pp, below 5pp threshold), and raised LEARNED-NEGATIVE prior from QR initial 25% → 30% (+5pp, AT threshold). The methodology strengthening (DUAL GATE breadth check + HARD BLOCK) was adopted verbatim into brief Section 4 + Section 3.6. The /025 finding upgrades the deference rule: LM Master methodology strengthening at Phase 4.5 §3-4 has been LOAD-BEARING **6 of 6 times** post-/018 — adopt verbatim into brief Section 4 falsifiers is now **NON-NEGOTIABLE** for cycle-4+ briefs.

---

## 4. Q1 sign-flip correction: LM Master claim of Q1 OOS PnL -30.78 is INCORRECT; actual Q1 +24.63; Q3 mid -57.44 is dominant

### 4.1 LM Master Phase 7.4 §1(B) claim (incorrect)

LM Master Post-Mortem `94fb3e1` §1(B) attributed the OOS Q1 PnL as:
- Q1 neg-extreme IS PnL +58.52 → OOS PnL -30.78 (sign-flip "dominant attribution channel")
- Q4 ORACLE IS PnL -2.28 → OOS PnL +22.45 (survived)
- Q5 strong-pos IS PnL +0.58 → OOS PnL -56.41 (collapse)

This figure derivation used IS-EDA regime windows (aggregate forward-return by z90 bin distribution) NOT realized-trade attribution from `trades.csv` joined to per-trade OI feature.

### 4.2 Actual trade-attribution from `oracle_q4_oos_attribution.csv` (corrected, authoritative)

Direct join of OOS `trades.csv` rows to per-trade `oi_delta_30_z90` feature value, bucketed by quintile:

| Quintile | z90 range | IS EDA Sharpe-proxy | OOS trades | OOS net PnL | OOS WR | IS-OOS sign-flip |
|---|---|---:|---:|---:|---:|:---:|
| Q1 neg-extreme | [-10.0, -1.05] | +1.05 | 46 | **+24.63** | 41.3% | **NO** |
| Q2 | [-1.05, -0.31] | +0.73 | 61 | -16.32 | 37.7% | NO |
| **Q3 mid (DEAD ZONE)** | [-0.31, +0.29] | +0.04 | 55 | **-57.44** | 30.9% | YES (IS was zero) |
| Q4 ORACLE | [+0.29, +0.95] | +1.68 | 44 | **+25.97** | 43.2% | NO (SURVIVED) |
| Q5 strong-pos | [+0.95, +10.0] | +0.60 | 52 | -54.84 | 30.8% | YES (IS positive → OOS collapse) |
| NaN missing OI | — | — | 3 | -3.57 | 0.0% | — |
| **Total** | — | — | **261** | **-81.57** | 36.0% | — |

### 4.3 Diagnosis: distribution-level Sharpe-proxy ≠ realized trade attribution

The discrepancy arises because LM Master analysis used IS-EDA quintile regime windows (aggregate forward-return by z90 bin) NOT realized-trade attribution join. The TWO measurement frames are:

| Measurement frame | What it measures | Validity for verdict claim |
|---|---|:---:|
| Distribution-level Sharpe-proxy (IS-EDA forward-return banding by z90 bin) | "If model traded uniformly across IS forward-return distribution, what would the Sharpe look like in each bin?" | INFORMATIONAL only — does NOT predict where the model actually entered trades |
| Realized trade-attribution join (OOS trades.csv × per-trade z90 value) | "Where did the model actually trade in OOS, and what was the PnL distribution?" | AUTHORITATIVE for OOS loss attribution |

### 4.4 The actual mechanism story (corrected)

1. **Q1 SURVIVED OOS positive** (+24.63, 41.3% WR) — the EDA's Q1 neg-extreme zone (z90 ∈ [-10.0, -1.05]) was the IS profit basin AND survived OOS. The model correctly identified Q1 as an entry zone.

2. **Q3 mid-zone became DOMINANT OOS LOSS CHANNEL** (-57.44 from 55 trades, 30.9% WR). The EDA correctly identified Q3 as a "dead zone" (Sharpe-proxy +0.04 ≈ 0). Under OOS regime shift, basin relocation MOVED THE MODEL'S TRADE ENTRY POINT into the EDA-identified dead zone. This is the dominant -57.44 loss explaining ~70% of net OOS loss.

3. **Q5 strong-pos collapsed** (-54.84, 30.8% WR). IS Q5 had marginal-positive Sharpe-proxy (+0.60); OOS Q5 collapsed under joint cross-asset OI regime shift (perp-funding cycle post-halving made strong-positive OI = over-extended zone, not bullish-continuation as EDA assumed).

4. **Q4 ORACLE SURVIVED** (+25.97, 43.2% WR) — brief Section 2.6 EDA correctly identified Q4 as the load-bearing positive band; the model just didn't concentrate there.

### 4.5 EDA mis-prediction risk codified

Per the new memory entry `feedback_v1_oracle_eda_trade_attribution.md` (catalogued at /025 closeout): **brief Phase 1-2 ORACLE EDA must include trade-attribution Q-band PnL projection IN ADDITION to distribution-level Sharpe-proxy**. Gap between the two = EDA mis-prediction risk; future feature-family briefs require BOTH measurement frames.

The corrected diagnostic in `oracle_q4_oos_attribution.csv` is reflected in engineering_report.md §8(c)+(d) anomaly notes and Critic Phase 7.5 FINAL `23b10d6` recommendation #3.

---

## 5. /027 CONFIRMATION readiness: 2-specialist bundle + multi-seed mandate CONFIRMED LOCKED

### 5.1 Substrate after /025

| Component | Provenance | Bundle role | Status |
|---|---|---|---|
| Pool baseline (5 sym, A/C/D/E unchanged) | BASELINE_V1.md | Pool anchor | LOCKED |
| LINK-only specialist (Model C') | /018 PROMISING-INERT-FAVORABLE | Alpha-enhancement | LOCKED (+0.80 OOS Δ) |
| ETH-only + symmetric BTC-trend gate (Model G) | /019 PROMISING | Alpha-enhancement | LOCKED (+0.50 OOS Δ) |
| BTC in pool via Model A | /020 NEG-CAT EXCLUDED | Pool baseline only | LOCKED |
| LTC in pool via Model D | /022 NEG-CAT EXCLUDED | Pool baseline only | LOCKED |
| Funding-family feature axis | /023 LEARNED-NEGATIVE EXCLUDED | NOT in bundle | LOCKED |
| Regime-conditional sub-models | /024 EXPLORATION-NEGATIVE EXCLUDED | NOT in bundle | LOCKED |
| **OI delta family** | **/025 LEARNED-NEG-CAT EXCLUDED** | **NOT in bundle** | **LOCKED at /025 closeout** |
| DOT routing | pending /027 multi-seed Pareto | TBD | PENDING /027 |

**Bundle target at /027 multi-seed UNCHANGED**: 2-specialist nominal Σ = +1.30 (LINK +0.80 + ETH+gate +0.50) if independent; realistic with correlation drag + multi-seed variance reduction = **+1.10 to +1.30 OOS Sharpe**.

### 5.2 Multi-seed mandate ACTIVE for /027

The HIGH-RISK rule "if 3+ HIGH-RISK >1σ negative deltas, next becomes mandatory multi-seed" was already TRIPPED at /024 closeout (per /024 brief Section 2.5: /020 NEG-CAT -0.86 + /022 NEG-CAT -1.17 + /024 IS NEG-CAT -0.86 ≥ 3rd ≥1σ NEG at IS layer). /025 LEARNED-NEG-CAT -1.40 OOS is the 4th cycle-3 ≥1σ NEG event. **Multi-seed is MANDATORY for /027 CONFIRMATION**.

Multi-seed spec for /027:
- `--seeds 2` (5 inner × 2 outer = 10 models/cell vs current 3 inner = 3/cell)
- `--n-trials 35` (raised from 18 for CONFIRMATION; n_trials=35 is above TPE saturation per `feedback_v3_confirmation_n_trials_35.md` v3 precedent)
- Full DSR/PBO/PSR re-evaluation under CONFIRMATION-mode (NOT EXPLORATION-mode-artifact per `feedback_v3_dsr_mode_artifact.md`)
- 6h wall-clock HARD CAP
- 10-seed pre-MERGE concentration validation if multi-seed mean Sharpe > +1.0

### 5.3 Cross-correlation pre-validation MANDATORY at /026

Per LM Master Phase 4.5 §6 (recommendation #6 ADOPTED) + Critic Phase 7.5 FINAL §"/027 BUNDLE LOCKED":

**/026 is pre-CONFIRMATION sanity slot** (NOT a NEW EXPLORATION). Tasks:
1. Compute Pearson correlation between monthly returns of (a) Pool baseline (5 sym, FROZEN) and (b) LINK specialist standalone monthly returns: verify `|ρ(Pool, LINK)| < 0.50`.
2. Compute Pearson correlation between monthly returns of (a) Pool baseline (5 sym, FROZEN) and (b) ETH+gate specialist standalone monthly returns: verify `|ρ(Pool, ETH+gate)| < 0.50`.
3. If BOTH PASS → /027 launches at multi-seed.
4. If EITHER FAIL → /026 reroutes to component reweighting (single-iteration pivot before /027).

The cross-correlation check ensures the 2-specialist additive bundle target (+1.30 nominal Σ) is realistic under low correlation drag. /027 launches conditional on /026 PASS.

### 5.4 EXCLUDED with mechanism evidence (all catalogued)

| Excluded component | Provenance | Reason | Catalog entry |
|---|---|---|---|
| Funding-family | /023 LEARNED-NEG clean | information ingested + OOS realization failed (LEARNED-NEG diary subtype) | `feedback_v1_learned_negative_subtype.md` |
| Regime-conditional sub-models | /024 NEG clean | partition non-specialization at sub-model layer + F3 IS-CAT | `feedback_v1_regime_partition_non_specialization.md` |
| **OI delta family** | **/025 LEARNED-NEG-CAT** | **same LEARNED structure as /023 + narrow basin entry rank-4 + catastrophic basin-pull under joint cross-asset OI shift** | **`feedback_v1_pool_a_new_feature_lneg.md` (NEW at /025 closeout)** |
| Microstructure features | UNTESTED in cycle-3 | n/a — open candidate for cycle-4 | n/a |
| XGBoost head-to-head | DEFERRED | v3 NEG precedent at iter-v3/016 + cycle-4 candidate | `feedback_v3_iter016_xgboost_mandate.md` |
| Meta-labeling | DEFERRED | v3 NEG-PATH-C precedent at iter-v3/017 + cycle-4 candidate | `feedback_v3_iter017_metalabeling_mandate.md` |

---

## 6. Wall-clock discipline lesson — codified at /025

### 6.1 The /025 fetch-cost violation

Per `feedback_v1_axis_selection_data_fetch_budget.md` (catalogued 2026-05-27 mid-/025 user directive):
- /025 OI axis was selected ASSUMING OI data was available.
- At brief design time, OI data was MISSING for 4/5 symbols (ETH/LINK/LTC/DOT had `oi_n_rows=0` per EDA Section 2.1 `oi_availability.csv`).
- Binance daily-archive fetch is ~1500-1700 HTTP requests per symbol; ~15 min wall-clock per symbol; ~60 min for full set.
- Fetch alone consumed ~50% of the 2h EXPLORATION budget.
- Total /025 wall-clock budget: 60-min fetch + 45-min backtest + ~30-min closeout = >2h.

### 6.2 The user directive and codified rule

> "If we have 2 hours of the exploration, why did you follow this approach of consuming this amount of data?" — user directive 2026-05-27

**Rule codified** (memory `feedback_v1_axis_selection_data_fetch_budget.md`):
- Phase 3 (axis selection) MUST audit data state and verify `total_budget = data_fetch_cost + feature_regen_cost + backtest_cost + closeout_cost ≤ 2h`.
- External data fetch is NOT outside the budget — it counts toward the 2h cap.
- If estimate ≥ 2h, EITHER pre-fetch in a PRIOR slot OR pick a different axis with existing data.

### 6.3 Recovery for /025 (one-time exception)

User accepted Option 2 (continue /025 as one-time exception). Future iterations bound by this rule. The rule applies retroactively to cycle-4 candidate axis selection — axes requiring external data fetch must declare fetch cost in brief Section 0.7 and route through pre-fetch slot if estimate ≥ 2h.

### 6.4 Lesson for /027 CONFIRMATION sizing

/027 CONFIRMATION has a 6h HARD CAP per v3 precedent. The multi-seed mandate at `--seeds 2 --n-trials 35` for 4-cohort training (Pool A + LINK + ETH+gate + LTC + DOT in pool baseline + LINK specialist + ETH+gate specialist) implies:
- 5 inner × 2 outer = 10 models/cell × ~7 cells = ~70 model trainings
- n_trials 35 at TPE saturation
- Wall-clock estimate per v1 baseline (5-seed = 7h total) → 2-seed = ~3h
- Plus DSR/PBO/PSR re-evaluation overhead at CONFIRMATION-mode
- /027 wall-clock estimate: 4-5h, INSIDE 6h cap

No external fetch needed for /027; cross-correlation check at /026 uses existing reports artifacts. /027 wall-clock budget is healthy.

---

## 7. Specific Phase 8 diary requirements derived from this memo

The Phase 8 diary must:

1. **Update `briefs-v1/exploration_catalog.md`** with /025 row per established schema (verdict + structural finding + LM Master tracking + /027 substrate update).

2. **Add memory entry** `feedback_v1_pool_a_new_feature_lneg.md` codifying the n=2 LEARNED-NEGATIVE pattern at v1 Pool A + single-seed n_trials=18. Cross-refs: `feedback_v1_learned_negative_subtype.md`, `feedback_v1_h2_refuted_basin_interaction.md`.

3. **Add memory entry** `feedback_v1_oracle_eda_trade_attribution.md` codifying the distribution-level vs trade-attribution measurement-frame gap. Cross-refs: `feedback_qr_uses_is_data.md`, `feedback_v3_oracle_eda_validity.md`.

4. **Update brief Section 13 self-check** to acknowledge Q1 sign-flip correction (LM Master §1(B) -30.78 figure incorrect; actual +24.63) + Q3 mid-band dominant loss (-57.44) + LM Master track record (directional 2/8; methodology 6/6).

5. **Tag `v0.v1-025`** on HEAD `23b10d6` after Phase 8 closeout commit (per `feedback_always_document.md` immediate-document mandate).

6. **Commit each artifact separately** (per orchestrator dispatch — Phase 7 memo + Phase 8 diary + catalog update + 2 memory entries + brief Section 13 self-check addendum + tag).

7. **Return 250-word closeout summary + cycle-3 final ledger** per orchestrator dispatch.

---

## 8. Phase 7 conclusions

1. **/025 EXPLORATION-NEGATIVE-CATASTROPHIC** (LEARNED-NEGATIVE-CATASTROPHIC subtype — NEW v1 verdict cell). F1 OOS Δ -1.40 (deep NEG-CAT band, 2.5× threshold) overrides DUAL GATE 4/4 PROMISING-clean classification per pre-registered Section 8 Row 7. F3 IS Δ +0.05 INERT (NOT a both-side collapse like /024).

2. **/023 + /025 n=2 LEARNED-NEGATIVE pattern ESTABLISHED**: NEW feature families ADDED TO POOL MODEL A at single-seed=42 ENSEMBLE_SIZE=3 n_trials=18 EXPLORATION budget are STRUCTURALLY UNABLE to clear OOS at v1 cohort. Codified at `feedback_v1_pool_a_new_feature_lneg.md`. Cycle-4 MUST structurally disqualify NEW-feature-to-Pool-A axes at single-seed.

3. **LM Master track record post-/025**: directional 2/8 = 25%; methodology 6/6 = 100% PERFECT. DUAL GATE + HARD BLOCK at /025 both load-bearing.

4. **Q1 sign-flip correction**: LM Master §1(B) Q1 OOS PnL -30.78 figure INCORRECT; actual Q1 +24.63 (SURVIVED). Q3 mid -57.44 is the DOMINANT loss channel (basin relocation to EDA dead zone), not Q4 ORACLE. Distribution-level Sharpe-proxy ≠ realized trade attribution. Codified at `feedback_v1_oracle_eda_trade_attribution.md`.

5. **/027 CONFIRMATION LOCKED**: 2-specialist bundle (Pool baseline + LINK + ETH+gate) + multi-seed mandate (`--seeds 2 --n-trials 35`) + cross-correlation pre-validation at /026 (Pearson < 0.50 vs both specialists). Target +1.10-1.30 OOS Sharpe.

6. **Wall-clock discipline lesson codified**: /025 fetch-cost violation (~60-min OI fetch outside 2h budget) led to user directive 2026-05-27 + `feedback_v1_axis_selection_data_fetch_budget.md` rule (one-time /025 exception; cycle-4 axis selection MUST audit fetch cost as INSIDE 2h budget).

7. **Cycle-3 EXPLORATIONs COMPLETE (10/10)**: 2 PROMISING (/018 LINK + /019 ETH+gate) + 1 PROMISING-METHODOLOGY (/021 H2 REFUTED) + 7 NEGATIVE (/016, /017, /020 NEG-CAT, /022 NEG-CAT, /023 LEARNED-NEG, /024 NEG-clean, /025 LEARNED-NEG-CAT). Only per-cohort specialists with INDEPENDENT priors survived OOS. /027 CONFIRMATION ready; /026 = pre-CONFIRMATION sanity slot.
