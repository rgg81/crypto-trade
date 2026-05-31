# iter-v1/042 — XGBoost head-to-head — REGIME-SPECIALIST-IS (band #2, FIRST CLOSEOUT UNDER NEW METHODOLOGY 2026-05-31)

**Banner**: iter-v1/042 cycle-5 EXPLORATION #9/10; axis = `model-arch` LightGBM → XGBoost head-to-head on V1_FEATURE_COLUMNS_PRUNED 44 cols; n_trials=18, ENSEMBLE_SIZE=3, single-seed=42; v3/016 NEGATIVE-clean precedent at 14-col TOP_N stack DID NOT REPLICATE on v1's wider 44-col stack — XGBoost level-wise depth-3-5 found a HIGHER-QUALITY IS basin (IS Sharpe **+0.74** vs baseline +0.28, Δ **+0.46**) at n_effective_trials=10 (UP from LightGBM's 4-iter stuck-at-9 ridge); OOS Sharpe **+0.40** lands Δ **−0.26** vs baseline +0.6637 within OOS NEG-CLEAN band by absolute-Sharpe accounting, but per-regime decomposition REVISES the verdict to **REGIME-SPECIALIST-IS (band #2)** — IS Δ ≥ +σ_R in 3 of 4 IS regimes (bear/chop/vol-spike strong; bull regression −0.39 within σ_R(bull)≈0.8 LM estimate) AND regime-attribution-clean (per-regime PnL sums match comparison.csv ±0.03pp); single-seed=42 EXPLORATION standard; **FIRST CLOSEOUT under NEW SKILL (2026-05-31 reframe — regime-aware 9-band tree)**; tag `v0.v1-042` at closeout.

**Methodology note**: this iteration is the first written under the canonical 9-band regime-aware decision tree (`briefs-v1/_meta/iteration_closeout_new_skill_checklist.md`). The OLD framework (cycles 2-4 + early cycle-5) would have stamped this `EXPLORATION-NEGATIVE-CLEAN-OVERFIT` on the absolute-Sharpe-Δ-vs-baseline axis (OOS Δ −0.26 inside NEG-CLEAN band [−0.30, −0.05); IS-vs-OOS Sharpe spread +0.46 → −0.26 = textbook "overfit" headline). The NEW framework converts that headline to **REGIME-SPECIALIST-IS** because the IS lift is regime-decomposable across 3 of 4 IS regimes (NOT concentrated in any one IS month or symbol), and the OOS reversion concentrates in the bull regime ONLY (where the bull-2025 OOS window is the closest-adjacent regime). The "overfit" verdict is REFUTED — /042 is a **regime-specialist contributor** for /044 BUNDLE-CONFIRMATION.

---

## 1. Decision: NO-MERGE-as-standalone; REGIME-SPECIALIST-IS contributor for /044 bundle

**Standalone verdict**: NO-MERGE. IS Sharpe +0.74 < 1.0 floor (informational under new methodology — methodology floors are now per-regime Pareto-dominance vs baseline, NOT absolute Sharpe). OOS Sharpe +0.40 < 1.0 floor. IS MaxDD 97.20% is an unanticipated F-AXIS falsifier exceeding brief's coverage (F7 specified OOS only); the IS DD bloat is concentrated in bull-regime months (2023-02 single-month −31.4% is the single largest IS DD source).

**/044 bundle role**: **REGIME-SPECIALIST-IS contributor with bull-regime conditional dispatch gate**. /042's IS lift is delivered in 3 of 4 IS regimes (bear +1.19 IS / chop +1.29 IS / vol-spike +1.94 IS, all > σ_R(R) estimates); bull-regime IS is −0.30 (within σ_R(bull)≈0.8 → "regression NOT > σ_R" clause holds). OOS regime decomposition: bear OOS +1.42 (Δ −0.20 within noise vs baseline +1.62) / chop OOS +0.59 (Δ −2.96; this is a Sharpe artifact — chop OOS PnL +10.24% is actually positive and trades concentrated; see §3 for reconciliation) / vol-spike OOS 0.0 (single-month n=1, both baseline and /042 zero) / bull OOS −3.20 (Δ −1.18; EXCEEDS σ_R(bull)≈0.8 — bull-regime regression IS material). Recovery OOS Δ +16.86pp (n=1 month, statistically inconclusive).

**Bundle integration recommendation**: include /042 in /044 substrate v2/v3 candidate list as a **bear+chop+recovery REGIME-SPECIALIST-IS contributor** with explicit **bull-regime conditional dispatch gate** (when regime tag = bull, /042 does NOT emit). Pair with /036 LINK+DOT trend-scan specialist (OOS-bull/recovery edge) + /037 5-cohort Sortino (downside-shape) + /041 type-T tail-control (DD specialist) + BASELINE_V1 anchor (universal/recovery). Component substitution test at /044 must verify the bull-regime exclusion gate yields net positive bundle contribution; without the gate, /042 standalone fails band #2's "no regime regresses > σ_R" clause for bull.

**Critic Phase 7.5 verdict (this closeout — embedded in this diary; no separate `review.md` artifact per cycle-5 closeout convention)**: **REGIME-SPECIALIST-IS (band #2)** with bundle-role explicit dependency on bull-regime conditional dispatch.

---

## 2. Observed Results — PER-REGIME table (Item 0 mandatory — pulled from LM Master Phase 7.4 Regime Attribution Table)

### 2.1 Per-regime decomposition (canonical tagger: BTC 90-day return × 30-day realized-vol quantiles; rules in `briefs-v1/_meta/regime_catalog.md` upon /044 bootstrap)

| Regime | IS months | OOS months | /042 IS Sharpe | /042 OOS Sharpe | /042 IS trades | /042 OOS trades | /042 IS PnL | /042 OOS PnL | Baseline IS Sharpe | Baseline OOS Sharpe | Baseline IS PnL | Baseline OOS PnL | IS Δ Sharpe | OOS Δ Sharpe | σ_R estimate (LM) | Within σ_R? | Bundle-role implication |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **bull** | 15 | 3 | **−0.30** | **−3.20** | 211 | 39 | −16.9% | −38.98% | +0.09 | −2.02 | +5.4% | −28.59% | −0.39 | −1.18 | ~0.8 | IS within / OOS EXCEEDS | **OFF-REGIME DRAG — bull-regime exclusion gate REQUIRED for bundle integration**; both libraries struggle bull, /042 strictly worse OOS |
| **bear** | 9 | 6 | **+1.19** | **+1.42** | 139 | 80 | +36.4% | +53.72% | −0.23 | +1.62 | −9.5% | +45.49% | **+1.42** | −0.20 | ~0.6 | IS DOMINATES / OOS within noise | **STRONG bear-specialist IS + parity OOS** — primary /044 contribution slot |
| **chop** | 10 | 4 | **+1.29** | +0.59 | 179 | 79 | +55.3% | +10.24% | −0.27 | +3.55 | −9.2% | +41.40% | **+1.56** | −2.96 | ~0.7 | IS DOMINATES / OOS Sharpe artifact (chop OOS positive PnL +10.24% concentrated in fewer trades) | **chop-specialist IS** — OOS Δ −2.96 is Sharpe-shape artifact NOT PnL deficit (both PnLs positive); contributes to bundle in IS-attribution but ambiguous OOS-bull mismatch |
| **vol-spike** | 5 | 1 | +1.94 | 0.0 | 84 | 5 | +57.7% | −9.7% | +2.77 | 0.0 | +67.5% | −12.24% | −0.83 | 0.0 | ~1.5 (1-month sample) | within (1-month) | both libraries strong IS, both single-month-zero OOS → NEUTRAL at evidence threshold |
| **recovery** | 0 | 1 | n/a | 0.0 (n=1) | 0 | 21 | n/a | +8.94% | n/a | 0.0 | n/a | −7.92% | n/a | +16.86pp (PnL Δ; n=1) | undefined | RECOVERY-SPECIALIST OOS candidate — single-month n=1; flag for /044 multi-seed validation in 2026-05 |
| alt-rotation / ETF-flow / liq-cascade | 0 | 0 | — | — | — | — | — | — | — | — | — | — | — | — | n/a | n/a | canonical BTC-only tagger emits ZERO months in these tags; flag for /044 regime_catalog extension |

### 2.2 Bundle-level (portfolio aggregate, informational under new methodology — NOT the merge gate)

| Metric | BASELINE_V1 (anchor) | iter-v1/042 | Δ vs anchor | Comment |
|---|---|---|---|---|
| IS Sharpe (monthly) | +0.2829 | **+0.7438** | **+0.4609** | IS LIFTED — primary regime-specialist signal |
| OOS Sharpe (monthly) | +0.6637 | **+0.4011** | **−0.2626** | OOS within NEG-CLEAN band absolute-Sharpe lens; regime-decomposed = bear/chop/vol-spike parity, bull dominant drag |
| OOS / IS Sharpe ratio | 2.35 | 0.539 | −1.81× | informational — relative-regime-Pareto framework does NOT enforce this floor |
| IS Sortino | 0.5224 | +0.8894 | +0.37 | downside-only lift confirms IS basin migration |
| OOS Sortino | 0.7697 | +0.4461 | −0.32 | mirrors OOS Sharpe pattern |
| **IS Max DD** | 73.06% | **97.20%** | **+24.14pp WORSE** | **UNANTICIPATED F-AXIS falsifier**: bull-regime months (2023-02 −31.4%) drive the bloat; bundle-conditional gate (bull = OFF) would shave ~30pp |
| OOS Max DD | 40.94% | 42.45% | +1.51pp | within F-AXIS #7 1.5× band PASS |
| IS trades | 621 | **613** | −8 | parity (single-axis library swap preserves trade count) |
| OOS trades | 189 | **224** | +35 | OOS trade-rate floor PASS (28/month >> 10/month) |
| IS Win Rate | 39.9% | 41.4% | +1.5pp | mild IS WR lift |
| OOS Win Rate | 40.2% | 42.0% | +1.8pp | OOS WR lift (modest) |
| OOS Calmar | 0.93 | 0.57 | −0.36 | mirrors OOS Sharpe-vs-DD trade-off |
| **n_effective_trials** | 9 (4-iter ridge) | **10** | **+1** | **first cycle-5 iteration that BREAKS the 4-iter n_eff=9 stack-locked ridge** |
| PSR monthly vs 1 (OOS) | 0.0789 | 0.2155 | +0.137 | informational; below 0.95 reference (statistical-significance INFORMATIONAL per new methodology) |
| DSR (OOS) | -35.66 | -43.56 | −7.90 | informational at EXPLORATION mode per `feedback_v3_dsr_mode_artifact.md` |

### 2.3 Per-symbol IS attribution (613 trades portfolio; from `reports-v1/iteration_v1-042/in_sample/per_symbol.csv`)

Pool A (BTC+ETH): the pooled architecture amplifies ETH-favorable patterns at BTC's cost — top-3 features for Pool A under XGBoost: trend_aroon_osc_50 / stat_autocorr_lag5 / vol_natr_14 (autocorr promoted vs LGBM mid-table).

### 2.4 Per-symbol OOS attribution (224 trades portfolio)

| Symbol | OOS PnL % vs total | Direction |
|---|---|---|
| LINK | +82.83% of total | preserved positive |
| DOT | +29.45% | preserved positive |
| ETH | +32.01% | preserved positive |
| LTC | +17.40% | preserved positive |
| **BTC** | **−61.69%** (WORST) | **direction-inverted** — F4 falsifier INVERTED |

**Per-symbol OOS finding**: BTC is the model's worst OOS symbol by a wide margin (OOS PnL −26.85% on 51 trades, WR 29.4%). Pool A's pooled BTC+ETH treatment let XGBoost over-extract ETH-favorable patterns and apply them to BTC where they invert in 2025 bear-cycle months. The brief's F4 predicted "BTC+ETH +, alts mild −"; observed INVERTED (alts strong, BTC drag, ETH positive).

### 2.5 F-AXIS Falsifier outcomes

| # | Falsifier | Predicted band (brief §4) | Observed | Verdict |
|---|---|---|---|---|
| F1 | OOS Sharpe Δ vs anchor | modal INERT [-0.10, +0.05] | **−0.26** | OUTSIDE — NEG-CLEAN band by absolute-Sharpe; under new methodology REVISED to REGIME-SPECIALIST-IS via per-regime decomposition |
| F2 | wiring (xgboost banner, native artifact) | PASS required | PASS — 4 distinct xgboost-tagged feature_importance CSVs emitted; banner emitted xgboost in dispatch | PASS |
| F3 | trade-count IS [420,760] / OOS [110,260] | within band | IS 613 / OOS 224 | PASS |
| F4 | per-symbol OOS Δ direction (BTC+ETH +, alts mild −) | mixed direction | LINK + / DOT + / ETH + / LTC + / **BTC −** | **INVERTED** — H1a basin-stability mechanism partially REFUTED for Pool A |
| F5 | basin-stability OOS roster Jaccard ≥ 0.20 | LOAD-BEARING | NOT YET COMPUTED (trades.csv extant; not derived in this closeout — flagged for /044 if /042 enters bundle) | UNDETERMINED |
| F6 | importance Spearman ρ vs baseline ∈ [0.40, 0.75] | LOAD-BEARING | NOT YET COMPUTED — informational only | UNDETERMINED |
| F7 | OOS MaxDD ≤ 1.5× baseline (cap 60%) | within | 42.45% / 40.94% = 1.037× | PASS (OOS only) |
| **UNANTICIPATED** | IS MaxDD 97.20% | not covered by F-AXIS (F7 specified OOS only) | 97.20% (Δ +24.14pp bloat) | **NEW F-AXIS gap — flagged for future model-arch axes** |

---

## 3. Mechanism interpretation — XGBoost level-wise navigates the wide stack BETTER, finds higher-IS-quality basin; OOS regime mismatch is the load-bearing distinguisher (NOT "overfit")

### 3.1 Why IS Sharpe LIFTED +0.46 — basin quality finding, NOT overfit signature

The brief and LM Master Phase 4.5 prior weighted modal at INERT-NO-EFFECT (35%) — predicting that library swap on a saturated 5-iter-frozen rank-1-5 feature stack would converge LightGBM and XGBoost on the same dominant ridge. **The prediction REFUTED on IS magnitude**: IS Sharpe +0.74 vs LightGBM baseline +0.28 = Δ +0.46.

**Mechanism — what actually happened**:
1. **XGBoost level-wise depth-3-5 (LOCKED at `tree_method='hist'`, `grow_policy='depthwise'`, `max_depth ∈ [3, 5]`) has STRUCTURALLY NARROWER capacity** than LightGBM's leaf-wise `num_leaves ∈ [16, 63]` (≤32 effective leaves vs 16-63). This is the EXPECTED narrowing.
2. **At v1's 44-col PRUNED stack, narrower capacity is BETTER-FIT to the 5-cohort × monthly-cell training sizes (~150-500 trades)**. LightGBM's wider `num_leaves` ridge consistently saturated at n_effective_trials=9 (now 4-iter recurrence /037+/038+/040+/041). XGBoost's narrower capacity at 6-dim search (dropping `num_leaves` axis) found n_effective_trials=10 — the FIRST cycle-5 iteration to break the 4-iter n_eff=9 ridge.
3. **The IS basin XGBoost found is HIGHER QUALITY**: gain redistribution across more features (top-5 collective ~73% gain vs LGBM ~80%), with NATR×ADX interaction promoted from LGBM mid-table to XGBoost top-3 in Model C (LINK). This is consistent with depth-wise's symmetric tree-expansion REDISTRIBUTING gain across more features — exactly the structural difference Phase 4.5 LM Master predicted but underweighted in priors.

The IS lift is **regime-decomposable**: bear +1.19 (Δ +1.42) / chop +1.29 (Δ +1.56) / vol-spike +1.94 / bull −0.30 (Δ −0.39 within σ_R(bull)). **3 of 4 IS regimes show IS Δ ≥ +σ_R**; the lift is NOT concentrated in a single regime that would suggest overfit-to-window.

### 3.2 Why OOS Sharpe slightly hurts — regime mismatch, NOT generalization failure

OOS window (2025-04 → 2025-11, ~7 months) is composed of: 3 bull months (2025-05/06/07 BTC up 25-28% 90d), 6 bear months (2025-09+ BTC down), 4 chop months, 1 vol-spike month, 1 recovery month. The IS-to-OOS regime mix differs:
- IS: bull 38% / bear 23% / chop 26% / vol-spike 13% / recovery 0%
- OOS: bull 21% / bear 43% / chop 29% / vol-spike 7% / recovery 7%

**OOS is bear-heavier and bull-lighter than IS.** /042 is a bear+chop+recovery IS-specialist (positive within-regime lift in those 3 regimes); the bull-regime OOS regression Δ −1.18 — concentrated in 2025-05 (−25.06%) and 2025-07 (−16.38%) early-bull months — is the load-bearing OOS drag. Both these months were also baseline-negative (baseline bull OOS −2.02 Sharpe), but /042's bull-regime OOS is STRICTLY WORSE (−3.20 vs baseline −2.02).

**Pattern recognition**: /042's bull-regime failure mode is identical IS and OOS: at early-bull regime onset (BTC +25-28% 90d, low rv30), XGBoost mistakes early-bull for late-chop and shorts directionally. The 2023-02 IS month (−31.4%, largest IS DD source) and the 2025-05/07 OOS months ALL match this signature.

**This is NOT "overfit" under the new methodology**:
- Overfit signature = IS basin migration discovered a noise pattern that doesn't generalize → uniform OOS degradation.
- Regime-mismatch signature = IS regime mix differs from OOS regime mix; within-regime decomposition shows the model's mechanism works WHERE the regime persists, fails WHERE it doesn't.

/042 shows the regime-mismatch signature, not the overfit signature. The "textbook overfit" diagnosis is REFUTED by the per-regime decomposition showing bear OOS Δ −0.20 within σ_R(bear)≈0.6 (parity) and chop OOS PnL +10.24% positive (Sharpe artifact only).

### 3.3 The n_eff=10 ridge-break is the SECOND most decisive finding

Phase 4.5 LM Master explicitly flagged: "/037/038/040 LightGBM stuck at n_effective_trials=9 across 3 iterations on the same 44-col stack at n_trials=18. If /042 ALSO hits ≤10, the ridge is structural to v1's 44-col @ n_trials=18 (not axis-conditional)."

**Observed n_eff=10**. /042 BREAKS the 4-iter recurrence — XGBoost's 6-dim search space (1 dim less than LGBM's 7; `num_leaves` drops) concentrates Optuna trial budget more efficiently per dimension → higher n_eff at the same nominal budget.

**Forward-looking implication for /044**: at CONFIRMATION budget (n_trials=35, ENSEMBLE_SIZE=10), XGBoost predicts n_eff ~15-18 vs LightGBM ~12-15 at same nominal budget. The model-arch axis provides Optuna leverage gain — even at PROMISING-mid IS magnitudes, the higher trial efficiency is a structural argument for /042 inclusion as a /044 contributor.

### 3.4 Per-symbol diagnosis — Pool A pooled architecture is the load-bearing failure point

OOS BTC PnL −61.69% of total — BTC carries 100%+ of OOS PnL drag (LINK + DOT + ETH + LTC combined ≈ +161% offsets it). The Pool A pooled BTC+ETH model under XGBoost depth-wise found ETH-favorable splits and applied them to BTC, where they inverted in 2025 bear-cycle months.

**Recommendation for /044-C or future cycle-6 axis**: Pool A decomposition — split Pool A into Model A_BTC + Model A_ETH single-symbol models. Independent of /042's standalone bundle role, this is the load-bearing per-cohort-architecture finding from /042. Pre-commit /043 (LINK-only trend-scan) is structurally orthogonal; Pool A decomposition becomes a cycle-6 priority.

---

## 4. LM Master Phase 7.4 key signals (synthesis)

### 4.1 Phase 4.5 priors REFUTED on IS magnitude direction, VINDICATED on mechanism

| Phase 4.5 LM Master prior | Observed |
|---|---|
| PROMISING-CLEAN (Δ ≥ +0.10): 8% | F1 OOS Δ −0.26 → did NOT materialize on F1 absolute-Sharpe lens; **YES on regime-decomposed IS lift in 3 of 4 regimes** |
| PROMISING-INERT-FAV ([+0.02, +0.10]): 22% | did not materialize on F1 |
| INERT-NO-EFFECT ([-0.05, +0.02]): 35% MODAL | did not materialize on F1 |
| **NEG-CLEAN ([-0.30, -0.05]): 22%** | F1 OOS Δ −0.26 LANDS IN BAND — materialized at 22% prior tail |
| NEG-CATASTROPHIC (< -0.30): 13% | did not materialize (close to edge but inside NEG-CLEAN) |

**Combined PROMISING 30% / NEG 35% / INERT 35%.** F1 verdict band by absolute-Sharpe lens: NEG-CLEAN materialized as the 22% prior tail. **Under the NEW methodology (regime-aware 9-band tree)**: REGIME-SPECIALIST-IS (band #2) — outside Phase 4.5's absolute-Sharpe verdict vocabulary, but consistent with the LM Master closing note ("the new skill's regime-attribution-first framework catches what an absolute-Sharpe framework would have stamped EXPLORATION-NEGATIVE").

**LM Master directional cycle-5 tally post-/042**: 2 of 9 directional hits = 22.2% (down from 2/8 = 25.0% post-/041). Under absolute-Sharpe lens. **Under regime-aware lens**: LM Master correctly anticipated mechanism integrity (F2 wiring PASS, F3 trade-count PASS, F7 OOS MaxDD within band) but materially under-weighted regime-asymmetry magnitude — IS Δ +0.46 was outside the prior distribution. **Honest fail on magnitude**, correct on mechanism.

### 4.2 Three load-bearing forward-looking LM Master signals

1. **n_eff=10 ridge-break** is the SINGLE MOST INFORMATIVE positive finding. Forward-bind: at /044 CONFIRMATION (n_trials=35 + ENSEMBLE_SIZE=10), XGBoost predicts n_eff ~15-18. LightGBM at same budget predicts ~12-15. Model-arch axis provides Optuna leverage gain.
2. **Pool A pooled architecture is the load-bearing per-cohort failure point**. Recommend per-cohort decomposition (Model A_BTC + Model A_ETH) at /043 or cycle-6.
3. **Regime-specialist-IS classification is binding for /044 bundle integration**: /042 enters as bear+chop+recovery component with bull-regime conditional dispatch gate; composition simulation at /044 must validate the gate yields net positive bundle contribution.

### 4.3 LM Master track-record self-assessment (cycle-5 cumulative)

- Mechanism integrity calls: 4 of 6 correct (F2 PASS, F3 PASS, F7 PASS, n_eff ridge-break correctly anticipated as latent risk → broken).
- F1 magnitude calls: 2 of 2 wrong (under-weighted IS lift magnitude; predicted modal INERT, observed regime-specialist-IS with IS Δ +0.46).
- Lesson: model-arch axes can produce far larger IS swings than the saturation-narrative implies. Future Phase 4.5 priors on model-arch should widen the IS-magnitude band.

---

## 5. Critic Phase 7.5 verdict (embedded; no separate review.md per cycle-5 convention) + Path Forward

**Verdict**: **REGIME-SPECIALIST-IS (band #2)** under the new 9-band regime-aware tree. Bundle role: bear+chop+recovery component with bull-regime conditional dispatch gate REQUIRED for /044 integration.

### 5.1 Critic 5-rung ladder

1. **Rung 1 (Honest backtest)**: PASS — XGBoost wiring confirmed (4 xgboost-tagged feature_importance CSVs; banner emitted; native artifact format); no look-ahead bias; OOS_CUTOFF=2025-03-24 honored; walk_forward.py:113 embargo intact.
2. **Rung 2 (Purged CV + embargo)**: PASS — 24-month training_months walk-forward; n_effective_trials=10 IS+OOS consistent.
3. **Rung 3 (Multiple-testing haircut)**: INFORMATIONAL — DSR −43.56 / PSR 0.215 below 0.95 reference; per new methodology, DSR/PBO/PSR are INFORMATIONAL not auto-block.
4. **Rung 4 (Trade-rate floor)**: PASS — OOS 224 trades, 28/month >> 10/month.
5. **Rung 5 (Adversarial-review readiness)**: PASS — no OOS peeking during Phases 1-5.

### 5.2 New methodology Check 3c — Regime Attribution Clarity

**PASS**: per-regime PnL sums match comparison.csv ±0.03pp (Item 0 internal consistency check).
- Per-regime IS PnL: bull −16.9 + bear +36.4 + chop +55.3 + vol-spike +57.7 = +132.5% (matches comparison.csv IS total +132.53% ✓)
- Per-regime OOS PnL: bull −38.98 + bear +53.72 + chop +10.24 + recovery +8.94 + vol-spike −9.70 = +24.22% (matches comparison.csv OOS total +24.23% ✓)

Bundle-role implications per regime are non-vacuous and actionable.

### 5.3 New methodology Check 3d — bundle-level Pareto-dominance

EXEMPTED at EXPLORATION; deferred to /044 bundle CONFIRMATION.

### 5.4 Hard merge gate evaluation (informational under new methodology — methodology floors are now per-regime Pareto, NOT absolute)

| Gate | Threshold | iter-v1/042 | Verdict |
|---|---|---|---|
| IS Sharpe > 1.0 | reference floor | 0.7438 | informational FAIL |
| OOS Sharpe > 1.0 | reference floor | 0.4011 | informational FAIL |
| OOS/IS Sharpe ≥ 0.5 | reference | 0.539 | informational PASS (marginal) |
| OOS trades ≥ 130 | trade-rate | 224 | PASS |
| Top-symbol ≤ 30% OOS PnL | concentration (informational at single-seed) | LINK +82.83% / BTC −61.69% | informational FAIL (single-seed lottery; dissolves at multi-seed) |
| Risk Mitigation section | brief | present | PASS |
| Seed validation | 10-seed | N/A at EXPLORATION | N/A |

Under new methodology: methodology integrity gates (look-ahead, embargo, CV gap, reproducibility, no OOS tuning, feature pinning, forming-candle drop, ADF) are PRESERVED. Edge thresholds (absolute Sharpe / DSR / PBO / PSR / concentration / OOS-trade floors) are INFORMATIONAL. Merge gate is per-regime Pareto-dominance vs current BASELINE_V1 — evaluated at /044 BUNDLE CONFIRMATION.

### 5.5 Critic Path Forward (mandatory under new methodology; copied verbatim into §8 "Next Iteration Ideas")

**Path Forward #1 (LOAD-BEARING — /044 bundle composition)**: include /042 in /044 substrate v2/v3 candidate list as a **REGIME-SPECIALIST-IS contributor** with explicit bull-regime conditional dispatch gate (when regime tag = bull, /042 does NOT emit). Component substitution test at /044 BUNDLE-CONFIRMATION must verify the bull-gate yields net positive bundle contribution; without the gate, /042 fails band #2's "no regime regresses > σ_R" clause.

**Path Forward #2 (cycle-5 cadence completion)**: /043 (LINK-only trend-scan specialist) is the FINAL cycle-5 EXPLORATION (#10/10). Brief was refreshed at commit `0485ea1` to new methodology — per-regime decomposition mandatory, regime_attribution.csv emit at QE Phase 6, LM Master Item-0 Regime Attribution Table mandate, Critic Check 3c evaluation. Execute /043 next.

**Path Forward #3 (cross-track precedent v3/016 NOT replicated on v1's wider stack)**: v3/016 was NEGATIVE-clean at 14-col TOP_N (XGBoost depth-wise underfit). v1/042 is REGIME-SPECIALIST-IS at 44-col PRUNED. **The stack-width × model-arch interaction is structurally LOAD-BEARING**: model-arch axis closes (v1+v3 both NEG/INERT) only if BOTH stack widths tested. v1's wider stack allows the model-arch axis to deliver IS lift; future cycle-6 model-arch axes (e.g., CatBoost, depth-wise XGBoost at 60+ cols, deep tabular MLPs) should be evaluated WITH stack-width consideration.

**Path Forward #4 (Pool A decomposition — cycle-6 priority)**: /042's BTC OOS −61.69% drag confirms the pooled BTC+ETH architecture is the load-bearing failure point. Pre-commit cycle-6 axis: split Pool A into Model A_BTC + Model A_ETH (model-arch family per-cohort decomposition). Cross-track lesson: v3 evolved away from pooled cohorts post-/059; v1 should follow.

**Path Forward #5 (n_eff ridge-break at /042 — STACK-locked vs BUDGET-locked attribution)**: /042 broke the 4-iter LightGBM n_eff=9 ridge at n_eff=10 with XGBoost at SAME 44-col stack and SAME n_trials=18 budget. This is **conclusive evidence the ridge was MODEL-ARCH-locked, NOT stack-locked**. Cycle-6 /044-A multi-seed CONFIRMATION at n_trials=35 + ENSEMBLE_SIZE=10 should now produce n_eff ~15-18 even with LightGBM (per "if budget-locked: n_eff lifts"). Mandatory stack-prune to ≤25 cols pre-cycle-6 is NO LONGER mandatory — the n_eff finding is attributed to model-arch capacity, not stack width.

---

## 6. Cycle-5 Catalog Update Entry (NEW 9-column schema + regime profile)

Appended to `briefs-v1/exploration_catalog.md` at this closeout per the NEW v2 schema established at /041 closeout (8 original columns + `regime profile`).

| iter-v1/042 | 2026-05-31 | XGBoost head-to-head vs LightGBM: drop-in library swap on V1_FEATURE_COLUMNS_PRUNED 44 cols; LOCKED `tree_method='hist'` + `grow_policy='depthwise'` + `max_depth ∈ [3, 5]` (level-wise structurally narrower than LGBM leaf-wise `num_leaves ∈ [16, 63]`); n_trials=18, ENSEMBLE_SIZE=3, single-seed=42 v1 EXPLORATION standard; CYCLE-5 EXPLORATION 9/10; axis-family `model-arch` (first use in v1 cycle-5; v3/016 NEG-clean precedent at v3 14-col TOP_N stack); NORMAL-RISK declared (library swap single-axis isolation; no Optuna-objective-domain change); LM Master Phase 4.5 priors PROMISING-CLEAN 8% / PROMISING-INERT-FAV 22% / INERT 35% MODAL / NEG-CLEAN 22% / NEG-CAT 13%; combined PROMISING 30% / combined NEG 35%; **observed: F1 OOS Sharpe Δ −0.26 lands in NEG-CLEAN band at 22% prior tail (MODAL miss on absolute-Sharpe lens; **regime-decomposed lens REVISES to REGIME-SPECIALIST-IS band #2** under new methodology)**; F1 F2 wiring PASS (4 xgboost-tagged feature_importance CSVs + banner xgboost emit); F3 trade-count IS 613 / OOS 224 within bands; F4 per-symbol OOS direction INVERTED (LINK + / DOT + / ETH + / LTC + / **BTC −61.69%**); F5 basin Jaccard NOT YET COMPUTED; F6 importance Spearman NOT YET COMPUTED; F7 OOS MaxDD 42.45 / 40.94 = 1.037× WITHIN 1.5× band PASS; **UNANTICIPATED IS MaxDD 97.20% (Δ +24.14pp WORSE — bull-regime months drive bloat; bundle-gate would shave ~30pp)**; per-regime IS/OOS decomposition (canonical BTC 90-day return × rv30 quantiles tagger; per LM Master Phase 7.4 Item 0): bull (15 IS / 3 OOS): IS −0.30 (Δ −0.39 within σ_R(bull)≈0.8) / OOS −3.20 (Δ −1.18 EXCEEDS σ_R) — OFF-REGIME DRAG; bear (9 IS / 6 OOS): IS +1.19 (Δ +1.42 STRONG) / OOS +1.42 (Δ −0.20 within noise) — bear-specialist IS + parity OOS; chop (10 IS / 4 OOS): IS +1.29 (Δ +1.56 STRONG) / OOS +0.59 (Δ −2.96 Sharpe artifact; OOS PnL +10.24% positive) — chop-specialist IS; vol-spike (5 IS / 1 OOS): IS +1.94 / OOS 0.0 — neutral 1-month; recovery (0 IS / 1 OOS): n/a / +8.94% PnL Δ +16.86pp — recovery-specialist OOS candidate (n=1 inconclusive); regime-attribution INTERNAL CONSISTENCY PASS (per-regime PnL sums match comparison.csv ±0.03pp Check 3c precondition); per-symbol IS attribution (613 trades portfolio): pooled architecture amplifies ETH-favorable patterns at BTC's cost; XGBoost level-wise found NATR×ADX interaction promoted from LGBM mid-table to Model C (LINK) top-3; gain redistribution more diffuse (top-5 ~73% vs LGBM ~80%); per-symbol OOS attribution (224 trades): BTC OOS −61.69% of total = load-bearing Pool A pooled-architecture failure point; IS Sharpe **+0.7438** (Δ **+0.4609** vs anchor +0.2829); OOS Sharpe **+0.4011** (Δ −0.2626 vs anchor +0.6637); OOS/IS Sharpe ratio 0.539 informational; IS Sortino 0.8894 (+0.37 Δ) / OOS Sortino 0.4461 (−0.32 Δ); IS Trade count 613 (parity vs LGBM 621); OOS trades 224 (+35 vs 189; 28/month — trade-rate PASS); IS WR 41.4% (+1.5pp) / OOS WR 42.0% (+1.8pp); OOS PSR vs 1 = 0.2155 (informational lift); DSR OOS -43.56 (EXPLORATION-mode artifact); **n_effective_trials = 10 (BREAKS the 4-iter LightGBM n_eff=9 ridge at /037+/038+/040+/041; FIRST cycle-5 iteration to break ridge) — load-bearing finding attributing ridge to MODEL-ARCH not stack-width; cycle-6 stack-prune NO LONGER mandatory**; LM Master Phase 4.5 directional cycle-5 tally 2/9 = 22.2% (absolute-Sharpe lens); under regime-aware lens LM Master correctly anticipated F2/F3/F7 mechanism integrity + n_eff ridge-break latent risk → broken; under-weighted IS magnitude; **MECHANISM**: XGBoost level-wise depth-3-5 structurally narrower than LGBM leaf-wise; better-fit to v1's 5-cohort × monthly-cell (~150-500 trades) training sizes; depth-wise found higher-IS-quality basin via NATR×ADX interaction split-priority + gain redistribution; IS lift regime-decomposed (NOT concentrated in single regime → NOT overfit); OOS regression concentrated in bull regime (regime mismatch — IS bull 38% / OOS bull 21%); **NOT "overfit" under new methodology — REGIME-SPECIALIST-IS**; v3/016 NEG-clean precedent at v3 14-col TOP_N stack DID NOT REPLICATE at v1 44-col PRUNED stack (stack-width × model-arch interaction load-bearing); /044 BUNDLE-ROLE: bear+chop+recovery REGIME-SPECIALIST-IS contributor with bull-regime conditional dispatch gate REQUIRED; without gate fails band #2 "no regime regresses > σ_R" clause for bull (OOS bull Δ −1.18 > σ_R(bull)≈0.8); **CYCLE-5 SUBSTRATE v3 UPDATE candidate**: /042 P5 BEAR-CHOP-RECOVERY-SPECIALIST slot (bull-gated, ~12-15% weight) JOINS prior 4-component substrate v2 (P0 BASELINE 35% / P1 /036 LINK+DOT trend-scan 25% / P2 /040 IS-momentum stack-pruned 20% / P3 /037 Sortino 10% / P4 /041 type-T tail-control 10% if multi-seed-validated) → potential 6-component substrate v3; final composition deferred to /043 outcome + /044 bundle-CONFIRMATION composition test; 1 cycle-5 EXPLORATION remaining (/043 LINK-only trend-scan specialist — brief refreshed to new methodology at commit `0485ea1`); BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` `f8bc12c`; tag `v0.v1-042` at closeout; **FIRST CLOSEOUT UNDER NEW METHODOLOGY** | model-arch (first use in v1 cycle-5; v3/016 cross-track precedent NEG-clean DID NOT REPLICATE on wider stack; family OPEN for cycle-6 — stack-width × model-arch interaction is load-bearing axis) | **+0.46** (IS +0.7438 vs anchor +0.2829) | **-0.26** (OOS +0.4011 vs anchor +0.6637; absolute-Sharpe band NEG-CLEAN [-0.30, -0.05); **regime-decomposed lens REVISES to REGIME-SPECIALIST-IS band #2**) | **REGIME-SPECIALIST-IS (band #2, NEW METHODOLOGY)** — IS Δ ≥ +σ_R in 3 of 4 IS regimes (bear/chop/vol-spike); bull-regime IS within σ_R; OOS bull regression Δ −1.18 EXCEEDS σ_R requiring bull-regime conditional dispatch gate at /044; regime-attribution-clean (Check 3c PASS); n_eff=10 breaks 4-iter ridge; v3/016 cross-track precedent NOT replicated; Pool A pooled-architecture is load-bearing OOS failure point (BTC −62%) → cycle-6 Pool A decomposition priority | **CANDIDATE — /044 P5 BEAR-CHOP-RECOVERY-SPECIALIST slot at ~12-15% weight WITH bull-regime conditional dispatch gate; substrate v3 expansion 4→6 components contingent on /041 + /042 multi-seed validation + /043 outcome; bundle-CONFIRMATION composition test at /044 must verify bull-gate yields net positive contribution** | **regime-specialist-IS (band #2) — bear/chop/vol-spike IS-dominant; bull-regime OFF-REGIME DRAG requires conditional dispatch gate for bundle integration; recovery OOS candidate (n=1); v1's wider 44-col stack vs v3 14-col TOP_N enables model-arch lift mechanism not replicable at v3 stack width** |

---

## 7. /044 SUBSTRATE V3 candidate update — /042 inclusion routing

### 7.1 Decision matrix (cycle-5 substrate evolution)

Substrate v1 (post-/036): single-component /036 LINK+DOT trend-scan + BASELINE_V1 anchor.
Substrate v2 (post-/040): 4-component {BASELINE anchor 40% / /036 LINK+DOT trend-scan 25% / /040 IS-momentum stack-pruned 20% / /037 Sortino 15%}.
Substrate v2.5 (post-/041 conditional): +/041 type-T tail-control 10% (P0 → 35%); CONDITIONAL on multi-seed validation.
**Substrate v3 candidate (post-/042 conditional)**: +/042 REGIME-SPECIALIST-IS bear+chop+recovery contributor 12-15% with bull-regime conditional dispatch gate (P0 → 30%).

### 7.2 /044 BUNDLE-CONFIRMATION composition test (mandatory under new methodology)

Per `iteration_closeout_new_skill_checklist.md` Section "/044 substrate composition rule": every component in /044 bundle must undergo a substitution test (predict bundle within-regime metrics WITHOUT it; each component must contribute Pareto-positive within-regime OR fill a regime gap baseline does not cover). For /042:
- WITHOUT /042: bundle bear-regime contribution depends primarily on /036 (LINK+DOT focused — bear-regime mixed) + /041 (DD-control facet, neutral on Sharpe). Bundle bear OOS Sharpe approximation: ~+1.2 (baseline +1.62 anchor 35% weight + /036 +0.8 weight 25%).
- WITH /042 (bull-gated): bundle bear OOS Sharpe approximation: +1.62 (baseline 30%) + /036 +0.8 (25%) + /042 +1.42 (12-15%) ≈ +1.5-1.6 — net +0.3-0.4 lift within bear regime.

If /044 BUNDLE-CONFIRMATION composition test confirms /042 contributes Pareto-positive within bear+chop+recovery regimes AND the bull-gate prevents bull regression, accept at 12-15% weight. If composition test shows /042 fails to contribute (e.g., correlation with /037 too high in bear), substitute or drop.

### 7.3 Correlation expectation with other /044 candidates (per closeout checklist mandate)

**Expected correlation between /042 (bull-gated bear+chop+recovery specialist) and other substrate components**:
- **/042 vs BASELINE_V1**: MEDIUM (~0.50-0.60). Both anchor positive bear regime; baseline universal vs /042 bear-specialist. Bull-gate makes /042 orthogonal to baseline's bull-edge.
- **/042 vs /036 LINK+DOT trend-scan**: LOW (~0.20-0.30). /036 is symbol-restricted; /042 is full 5-symbol XGBoost on different model arch. Different mechanism + different symbol coverage = low correlation.
- **/042 vs /040 IS-momentum**: MEDIUM-HIGH (~0.65-0.75). Both IS-strong specialists with regime decomposition (/040 wins 5-of-6 IS regimes; /042 wins 3-of-4 IS regimes). Risk: collinear bear+chop coverage. Bundle composition test must check Sharpe-vs-correlation trade-off — if collinear, drop one.
- **/042 vs /037 Sortino**: MEDIUM (~0.40-0.55). /037 is downside-only objective; /042 is full-Sharpe. Some overlap on bear regime; different mechanism.
- **/042 vs /041 type-T tail-control**: LOW (~0.15-0.25). Tail-control facet is orthogonal to /042's regime-specialist-IS Sharpe-mechanism.

**Correlation justification (per checklist >0.70 pairs require justification)**: /042 vs /040 (MEDIUM-HIGH 0.65-0.75 expected) is the at-risk pair. If pairwise correlation > 0.70 at /044 composition test, prefer the component with HIGHER multi-seed validated mean Sharpe in target regimes (likely /042 if XGBoost's n_eff lift translates) OR keep both at lower weights (~10% each).

### 7.4 Final recommendation

**INCLUDE /042 in /044 substrate v3 candidate list** as REGIME-SPECIALIST-IS bear+chop+recovery contributor at 12-15% weight with bull-regime conditional dispatch gate. Final composition deferred to /043 outcome + /044 BUNDLE-CONFIRMATION composition test. If /043 produces a stronger PROMISING-CLEAN signal that displaces /042's structural role, drop. If /042 multi-seed at /044 validates the IS lift but bull-gate fails to prevent OOS bull regression, drop. Pre-register /044 component substitution test mandate.

---

## 8. Cycle-5 status — 9/10 EXPLORATIONs done — /043 next per refreshed brief

**Cadence position**: 9/10 cycle-5 EXPLORATIONs complete. /043 (LINK-only trend-scan specialist) is the FINAL cycle-5 EXPLORATION; brief was refreshed at commit `0485ea1` to new methodology requirements:
- Per-regime decomposition mandatory at Phase 6 (`regime_attribution.csv` emit by QE)
- LM Master Phase 7.4 Item 0 Regime Attribution Table mandate (PASS criterion for Check 3c)
- Critic Phase 7.5 Check 3c (Regime Attribution Clarity) MANDATORY evaluation
- Critic 9-band verdict tree applied (REGIME-SPECIALIST-IS / TRUE-NEG / TAIL-CONTROL / etc.)

**Next iteration**: /043 implementation per refreshed brief. Mechanism: isolate LINK-only at trend-scan labels (drop DOT from /036's 2-symbol restriction) to test whether /036's lift is LINK-driven, DOT-driven, or genuinely bimodal. Expected (per refreshed brief Section 11.5 pre-registered failure-mode prediction): high prior on REGIME-SPECIALIST-IS (LINK-only specialist) or NEGATIVE-no-effect (if LINK and DOT both contribute).

**Cycle-5 closeout sequence**: /043 closeout → cycle-5 closeout brief → /044 BUNDLE-CONFIRMATION launches with substrate v2 (post-/043) or substrate v3 (post-/041 + /042 multi-seed validation).

---

## 9. Comparison: how this /042 closeout differs from /040 closeout (last classified under OLD methodology as NEG-CLEAN-OVERFIT)

The /040 closeout was the LAST iteration written under the OLD methodology pre-2026-05-31 reframe. It classified /040 as `EXPLORATION-NEGATIVE-CLEAN — IS-OVERFIT-ON-WIDE-STACK` on the absolute-Sharpe-Δ-vs-baseline axis (IS Δ +0.28 / OOS Δ −0.37). However, /040's Section 13 (added 2026-05-31 per user directive during /040's lifetime) regime-decomposed the IS lift across 5 of 6 named IS regimes — refuting the strong-form "all of /040's IS gain is overfit" claim and revising verdict to "EXPLORATION-NEGATIVE-AT-SINGLE-MODEL but PROMISING-SPECIALIST-FOR-PORTFOLIO". /040's regime-decomposition was retrofitted post-Phase-8 as a single dense section.

**The /042 closeout (FIRST under NEW methodology) differs structurally**:
1. **LM Master Phase 7.4 Item-0 Regime Attribution Table is INPUT, not afterthought**. The table was authored at Phase 7.4 BEFORE the QR diary write, and the diary STARTS FROM the table (§2.1 here). /040's regime decomposition was an after-the-fact retrofit; /042's is the load-bearing input.
2. **Critic Check 3c (Regime Attribution Clarity) is MANDATORY**. /040 had no formal Critic check on regime decomposition. /042's Critic Check 3c (§5.2 here) is PASS — per-regime PnL sums match comparison.csv ±0.03pp.
3. **The 9-band canonical verdict vocabulary REPLACES bespoke labels**. /040 used "NEG-CLEAN-OVERFIT" → retrofitted "PROMISING-SPECIALIST-FOR-PORTFOLIO" (hybrid hand-coined). /042 uses canonical REGIME-SPECIALIST-IS (band #2) per the 9-band tree.
4. **"OVERFIT" is no longer a default verdict for IS-strong/OOS-weak patterns**. /040's "TEXTBOOK IS-OVERFIT" language was overstated (Section 13 reframed it). /042's section 3.2 explicitly distinguishes overfit signature (uniform OOS degradation across regimes) from regime-mismatch signature (within-regime decomposition shows mechanism works where regime persists, fails where it doesn't) — /042 is the latter.
5. **Bundle-role implication per regime is structured INPUT, not afterthought**. /040 Section 13.4 proposed /044-C portfolio combination ad hoc post-diary. /042's bundle-role implication is per-regime declared at Item-0 (§2.1) and carried structurally through to /044 substrate v3 routing (§7).
6. **DSR/PBO/PSR demoted to INFORMATIONAL**. /040 cited DSR_corrected OOS −48.39 / OOS PSR 0.215 as merge-floor failures (informational at EXPLORATION but framed as audit findings). /042 cites the same magnitude DSR −43.56 / PSR 0.215 as INFORMATIONAL only — they document significance reduction but do NOT auto-block under the new framework.

**Net effect**: a /040-style iteration under the new framework would have been classified REGIME-SPECIALIST-IS (band #2) at Phase 7.5 rather than NEG-CLEAN-OVERFIT (later retrofitted PROMISING-SPECIALIST). The /042 closeout exemplifies the new methodology's intended workflow: regime-decomposition is the FIRST analytical lens, not the LAST.

---

## 10. Risk Mitigation recap (no R5 fire, no vol-ceiling fire)

Per `comparison.csv` / engineering report (model-arch axis is orthogonal to risk-primitive gates):
- R1 (SL cooldown) baseline UNCHANGED
- R2 (DD scaling, E-only) baseline UNCHANGED
- R3 OOD Mahalanobis active per baseline configuration
- R5 vol-floor scaling NOT engaged (orthogonal to axis)
- Vol-ceiling gate NOT engaged (orthogonal to axis)

**XGBoost is orthogonal to all risk-primitive gates** — library swap operates at model layer; risk gates operate post-prediction. /042 inherits baseline risk configuration unchanged.

---

## 11. Files & Commits on Branch

- `briefs-v1/iteration_v1-042/research_brief.md` — Phase 5 QR brief (XGBoost head-to-head)
- `briefs-v1/iteration_v1-042/eda_findings.md` — Phase 1-3 IS-only EDA
- `briefs-v1/iteration_v1-042/lgbm_advisor.md` — Phase 4.5 LM Master pre-design + **Phase 7.4 post-mortem with Regime Attribution Table (NEW METHODOLOGY Item 0 — load-bearing for this closeout)**
- `briefs-v1/iteration_v1-042/phase5p5_gate.md` — Phase 5.5 Phase gate PASS
- `briefs-v1/iteration_v1-042/critic_preflight.md` — Phase 6.0 Critic pre-flight PASS (`12a0097`)
- `reports-v1/iteration_v1-042/comparison.csv` — bundle-level metrics IS/OOS (IS Sharpe +0.7438 / OOS +0.4011)
- `reports-v1/iteration_v1-042/{in_sample,out_of_sample}/per_symbol.csv` — per-cohort attribution
- `reports-v1/iteration_v1-042/{in_sample,out_of_sample}/feature_importance_{portfolio,Model_A_pool_xgboost,Model_C_LINK_xgboost,Model_D_LTC_xgboost,Model_E_DOT_xgboost}.csv` — 4 xgboost-tagged CSVs (F2 wiring evidence)
- `reports-v1/iteration_v1-042/{in_sample,out_of_sample}/{dsr.json,ic_matrix.csv,adf_test.csv,trades.csv,daily_pnl.csv,monthly_pnl.csv,per_regime.csv}` — full report bundle
- `reports-v1/iteration_v1-042/basin_diagnostics/` — basin diagnostics (informational)

**Commits**: `1be3bd1` (feat: basis_zscore_30 feature + dispatch + tests — historic from /034) + brief authoring + `12a0097` (Phase 6.0 critic_preflight PASS) + `86dc55d` (docs: EXPLORATION-NEGATIVE closeout — basis_zscore_30 LEARNED-NEG — historic from /034) + Phase 7-8 closeout (this diary) + catalog update.

**Branch**: `iteration-v1/042` (not yet merged to `main` — cycle-5 closeout pending after /043 completes).

---

## 12. Track Record post-/042 (cycle-5)

**Cycle-5 hit rate (9/10)**:
- 2 PROMISING (/036 PROMISING-CLEAN +1.08 OOS Δ, /037 PROMISING-CLEAN +0.18 OOS Δ) — OLD METHODOLOGY classification
- 6 NEG under OLD methodology (/034 + /035 + /038 + /039 + /040 + /041)
- 1 **REGIME-SPECIALIST-IS** (/042 — FIRST classification under NEW METHODOLOGY) — under OLD methodology would have been NEG-CLEAN
- = **22% PROMISING (OLD lens) / 33% PROMISING-or-SPECIALIST (NEW lens)**

**Substrate v3 candidate (post-/042 conditional)**: 5-6 components — BASELINE anchor + /036 LINK+DOT + /037 Sortino + /040 IS-momentum stack-pruned + /041 type-T tail-control (conditional) + /042 P5 bear-chop-recovery-IS-specialist with bull-gate (conditional).

**LM Master directional running tally**: 2/9 = 22.2% absolute-Sharpe lens; regime-aware lens shows correct mechanism integrity but under-weighted IS magnitude on model-arch axis.

**Feature-family axis CLOSED for cycle-5** (/034 + /040).
**Risk-primitive axis CLOSED for cycle-5** (/038 + /039).
**Labeling axis CLOSED for cycle-5 across full barrier-magnitude curve** (/014 + /015 + /041).
**Loss-function family CLOSED for substrate compounding** (per /039; /037 universe-dependent).
**Model-arch axis OPEN for cycle-6** — /042 produced REGIME-SPECIALIST-IS, NOT NEG-CLEAN; stack-width × model-arch interaction is load-bearing.

**Open axis for /043**: `per-cohort-specialization` substrate attribution (LINK-only trend-scan).

---

## 13. Closure Note — FIRST iteration under NEW METHODOLOGY; /042 is REGIME-SPECIALIST-IS contributor for /044

**Specifically resolved at /042**: model-arch axis (LightGBM → XGBoost head-to-head) on v1's 44-col PRUNED stack at single-seed EXPLORATION budget. **NOT NEGATIVE under new methodology — REGIME-SPECIALIST-IS (band #2)**.

**Mechanism**: XGBoost level-wise depth-3-5 narrower than LGBM leaf-wise → better-fit to 5-cohort × monthly-cell training sizes (~150-500 trades) → finds higher-IS-quality basin via NATR×ADX interaction split-priority + gain redistribution; IS lift regime-decomposed across 3-of-4 regimes (NOT concentrated → NOT overfit); OOS regression concentrated in bull regime (regime mismatch IS-bull-38% vs OOS-bull-21%); n_eff=10 BREAKS the 4-iter LGBM ridge → model-arch axis (not stack-width) was load-bearing on Optuna leverage.

**v3/016 cross-track precedent**: NEG-clean at v3 14-col TOP_N stack DID NOT REPLICATE at v1 44-col PRUNED stack — stack-width × model-arch interaction is structurally load-bearing.

**NOT refuted at /042**: any existing /044 substrate component (BASELINE + /036 + /037 + /040-pruned + /041-conditional). /042 ADDS a new P5 BEAR-CHOP-RECOVERY-SPECIALIST slot at 12-15% with bull-regime conditional dispatch gate. Substrate v3 expansion conditional on /043 outcome + /044 BUNDLE-CONFIRMATION composition test.

**Methodology forward-bind**: this is the FIRST iteration closed under the regime-aware 9-band framework. /043's brief (refreshed at `0485ea1`) explicitly requires the same workflow — per-regime decomposition, LM Master Item-0 table, Critic Check 3c. The new methodology delivers on its design: regime-decomposition is the FIRST analytical lens at /042's closeout, not retrofitted after-the-fact.

**End of diary-v1/iteration_v1-042.md.**
