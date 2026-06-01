# LightGBM Master Advisor — iter-v1/023 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/023`. HEAD `009cccb`. Cycle-3 EXPLORATION #8/10. First feature-family axis in cycle-3.
- **Anchor**: BASELINE_V1.md portfolio (IS +0.2829 / OOS +0.6637).
- **3-way CONVERGENT routing**: Critic + LM Master /022 §5 + QR concur on funding-rate.
- **v3 prior catalog**: 4 NEGATIVE/INERT data points (/019/023/024/082); /082 multi-channel construction did NOT break pattern.
- **ORACLE EDA**: z30 ∈ [-2,-1] band = 11% trades / 154% IS PnL; +38.90% shorts vs -32.86% longs (sign-flip).
- **LM Master track record entering /023**: H1 directional 2/3, methodology 2/2.

## 1. v3 axis closure compliance — DOES NOT BIND v1 literally

Per `feedback_v3_cross_asset_ohlcv_closed.md`: closure covers cross-asset OHLCV-derived primitives. Funding-rate is non-OHLCV → rule doesn't apply by literal language. **HOWEVER**: v3's 4-data-point funding-specific catalog IS a SEPARATE structural verdict that transfers as empirical prior.

v1 structural differences NOT decisive: (a) pool Model A 2× rows real but `colsample_bytree` redistributes same dilution risk; (b) n_trials=18 mid-zone (above INERT-pattern threshold 10, below actively-harm threshold 35); (c) 5-sym universe Models C/D/E inherit single-symbol limitation.

## 2. ORACLE EDA +78.55% — DOWNGRADE as predictor

STATELESS carve-out applies. **BUT** per /022 empirical (gate fired in band yet F1 catastrophic): basin relocation dissolves ORACLE-projected phenomena. /022 Jaccard 0.10/0.09 confirms ~90% NEW roster.

**Critical distinction**: funding is INPUT FEATURE not post-hoc filter. Optuna CAN use it during training. Most-favorable difference vs /022's gate. HOWEVER v3/082 also was input-feature axis and produced rank 15/16/17/18 of 18 importance — input-feature status doesn't guarantee learn-ability.

**Per-symbol texture matters**: DOT extreme-negative only 4 trades (sparse); LTC negative-band -12.08% (counter-direction). The +78.55% is BTC+LINK+DOT dominated. Universality shakier than headline.

## 3. Verdict-class priors — RECOMMEND 12/8/52/18/8/2

| Verdict | QR | LM Master | Rationale |
|---|---|---|---|
| PROMISING | 15% | **12%** | v3 4-point precedent dominant; -3pp |
| PROMISING-INERT-FAV | 10% | **8%** | colsample lottery on 42-col surface less likely than 40-col; -2pp |
| **INERT (modal)** | 45% | **52%** | v3/019 + /082 importance-rank evidence stronger; +7pp |
| NEGATIVE clean | 15% | **18%** | v3/023 pattern at n_trials=18 mid-budget; +3pp |
| NEGATIVE-CAT | 10% | **8%** | NEW input lower CAT risk than gate (/020/022); -2pp |
| PROMISING-METHOD | 5% | **2%** | NEW feature family inherently NOT methodology axis; -3pp |

**Modal INERT 52%**, PROMISING tail compresses to 20% combined.

## 4. F-AXIS-MECHANISM #1 — strengthen with gain-share check

v3 INERT threshold rank 14/14 (7.1% positional floor). v1 42 cols positional floor 2.4%.

**Recommended threshold**: rank ≥ 32/42 (bottom-quartile) on ≥ 3 of 5 cohorts → INERT. QR's "rank ≥ 30/42 on ≥ 2 cohorts" too loose — **tighten to ≥ 32/42 on ≥ 3 cohorts**.

**Gain-share threshold (CRITICAL ADDITION)**: v3/082 family combined 9.90% gain share at 4 features = 2.475% per feature avg (below uniform-parity 5.56%). v1 uniform-parity at 42 cols = 2.38%.

**Recommend INERT-by-gain-share**: funding_z30 OR funding_z90 < 1.5% gain share (well below uniform-parity) on ≥ 3 cohorts → INERT-by-importance.

**PROMISING-clean threshold**: rank ≤ 14/42 (top-third) on ≥ 2 cohorts AND combined gain share ≥ 4.0% across family. QR's "rank ≤ 14/42 ≥ 2 cohorts" insufficient — single-feature rank without gain-share misclassified v3/019 as "PROMISING-INERT".

## 5. n_eff_per_cell prediction

Pool Model A 2-sym BTC+ETH gets ~2× rows; C/D/E same as v3 per-symbol. Adding 2 cols redistributes split-budget but doesn't change row count.

**Predicted n_eff_per_cell**: 7-9 modal 8, band [5, 10]. WIDEN QR's [4, 10] lower bound to [5, 10] — pool A advantage raises floor.

## 6. /024+ verdict-conditional pre-staging

- **PROMISING (12%)** → /024 = funding-FAMILY expansion (sign-persist, momentum). DO NOT stack 4 features monolithically per `feedback_v3_engineered_features_dont_stack.md` SAME-FAMILY rule. Add ONE at a time at single-seed. Stack 2 z-windows + 1 NEW = 3 funding-family features max. Stacking experiments deferred to /027 multi-seed.

- **INERT (modal 52%)** → /024 = per-cohort drawdown brake (Path Forward #2 from /022 Critic). STATEFUL → mandatory deadlock-impossibility proof per /054 lesson.

- **NEGATIVE clean (18%)** → /024 = per-cohort drawdown brake OR open-interest delta family (NEW sister non-OHLCV).

- **NEGATIVE-CAT (8%)** → /024 = mandatory multi-seed HIGH-RISK iteration (3rd cycle-3 NEG-CAT triggers forward mandate). Axis: open-interest delta family at multi-seed.

## 7. Most important point

**v1's pool Model A architectural advantage is real but probably not large enough to break the v3 4-data-point structural verdict at single-seed n_trials=18 EXPLORATION budget — the modal outcome is INERT-by-importance (rank ≥ 32/42 on ≥ 3 cohorts + family gain share < 4%) at 52% probability, and the /023 verdict will be diagnostic of whether funding-rate is a model-architecture-conditional signal (rescue at /027 multi-seed) or a fundamental feature-family limitation (axis CLOSED for v1).**

## 8. /027 bundle composition impact

**IF /023 PROMISING**: funding-family becomes 3rd alpha component:
- Baseline pool + LINK +0.80 + ETH+gate +0.50 + funding-family +0.20 estimate
- Nominal Σ +2.16 OOS Sharpe target
- Realistic with correlation drag: **+1.30 to +1.50 OOS Sharpe**
- Cross-corr pre-validation < 0.40 required at multi-seed

**IF /023 INERT/NEG**: bundle UNCHANGED at +1.20-1.50.

## 9. Closing call

**MEDIUM-HIGH confidence** in three calls:
1. Verdict priors INERT modal 52% (vs QR 45%); PROMISING tail 20% combined (vs QR 25%).
2. **F-AXIS #1 threshold MUST add gain-share check**: rank-only insufficient per v3/082 evidence.
3. n_eff band tighten lower to [5, 10].

**Single most important point for QR**: Section 4.2 F-AXIS-MECHANISM #1 currently relies on rank alone; v3/082 evidence shows rank-mid (15/18) with gain-share-below-parity (2.475% < 5.56% uniform) is the load-bearing INERT diagnostic. Tighten F-AXIS #1 to BOTH rank ≥ 32/42 on ≥ 3 cohorts AND family gain share < 4.0%. Without gain-share check, /023 verdict mis-classification risk ~15pp.

**Critic Phase 7.5 priority items**:
1. Family gain-share computation across all 5 cohorts — LOAD-BEARING.
2. Pool Model A specifically — funding rank/gain in pool A vs Models C/D/E (architectural lever evidence).
3. ORACLE EDA per-symbol texture: confirm LTC counter-direction preserved post-retrain (basin-relocation check).
4. n_eff per-cell against pre-registered [5, 10] band.

---

# LightGBM Master Post-Mortem — iter-v1/023 — Phase 7.4

## Context Read
- IS Sharpe +0.4121 / OOS Sharpe **+0.4606** / 694 IS / 257 OOS / WR OOS 44.0% / PSR OOS 0.66 / n_eff 9
- **F1 OOS Δ = 0.4606 − 0.6637 = −0.2031** (3bp inside NEGATIVE band; threshold −0.20)
- **F3 IS Δ = +0.1292** → INERT
- DUAL GATE gain shares: Pool A **6.88%**, LINK C **5.65%**, LTC D **3.66%**, DOT E **5.49%**, portfolio **5.40%**
- Funding ranks (z90/z30 of 42): Pool **11/12**, LINK **11/12**, LTC **14/18**, DOT **10/18**

## 1. Phase 4.5 vs Phase 7.4 prediction reality

Priors **12/8/52/18/8/2**. Observed verdict in 8% NEGATIVE-clean tail just past −0.20 (3bp from modal INERT). Gain-share check I mandated as Phase 4.5 §4 CRITICAL — load-bearing. v1's 5.40% portfolio gain share clears uniform-parity (2.38%/feature); v3/082 was 9.90%/4 = 2.475%/feature (BELOW parity). **v1 LEARNS funding; v3 did NOT.**

## 2. F-AXIS #1 DUAL GATE adjudication — VERDICT CELL COLLISION

DUAL GATE PROMISING-clean (rank ≤14/42 + gain ≥4.0% on ≥2 cohorts):
- Pool A: ranks 11+12, gain 6.88% — **PASS**
- LINK C: ranks 11+12, gain 5.65% — **PASS**
- DOT E: rank 10 (z90 PASS), gain 5.49% — **PASS**
- LTC D: ranks 14+18, gain 3.66% — borderline FAIL

**3 of 4 cohorts cleanly PROMISING-clean** — but F1 OOS Δ NEGATIVE. New verdict cell: **LEARNED-NEGATIVE** (information ingested + OOS realization failed). Distinct from v3 INERT-by-importance.

## 3. Why funding LEARNED but didn't HELP

(a) **z90 outranks z30 in 3 of 4 cohorts**: the longer-window (regime-level) feature carries more gain. Trees treat z90 as slow-moving regime indicator; z30 marginally used. But LightGBM at depth 3-5 cannot easily compose `funding × momentum × volatility` three-way interactions in 9 effective trials.

(b) **Pool A vs single-symbol gap (6.88% vs 3.66%)**: joint BTC+ETH loss surface lets trees use `funding × symbol-dummy` splits. Architecture advantage materialized; not enough to flip OOS sign.

(c) **ORACLE +78.55% extreme-negative band evaporated**: per /021/022 basin-relocation pattern, OOS roster likely doesn't contain the z30 ∈ [-2,-1] events at training distribution. LightGBM at single-seed finds the MEAN funding effect (~zero); ORACLE-tail edge is left on the table.

**Synthesis**: funding is **mean-informative but tail-load-bearing**. v1 LightGBM learns the average; the tail (+78.55% concentration) requires explicit regime gating.

## 4. Bold implication for /024 — REGIME-CONDITIONAL FUNDING (matches user directive)

User mandate: "be bold; diversification; multiple smaller models per regime". /023 finding ENABLES this directly:

**Option A — REGIME-GATE WRAPPER** (safest): entry signal fires only when `|funding_z30| > 1.5` OR baseline gate. STATELESS, no retraining. Harvests +78.55% band edge.

**Option B (RECOMMENDED PRIMARY for /024)** — **REGIME-CONDITIONAL SUB-MODELS**: train 2 sub-models per cohort — `|z30|>1.5` subset and `|z30|≤1.5` subset. Combine at inference via regime gate. **Directly tests user's "multiple smaller models per regime" thesis.** Wall-clock 2× ENSEMBLE_SIZE per cohort → ~80 min EXPLORATION. Extreme subset ~14% × 5727 = 800 bars per symbol — borderline thin but feasible.

**Option C — FUNDING-PERSISTENCE INTERACTION**: composed feature `funding_extreme_persist = sign(funding_z30) × min(consecutive_bars_above_threshold, 24)`. Engineered-feature fallback per `feedback_v3_engineered_feature_pivot.md`.

**Decision: Option B PRIMARY for /024** (matches user "multiple smaller models per regime" directive).

## 5. /027 bundle composition impact

Funding-family does NOT join /027 as alpha component (F1 NEGATIVE). LEARNING signal suggests it COULD contribute IF /024 regime-conditional succeeds. /027 stays at 2 specialists + pool baseline until /024 outcome known.

## 6. n_eff_per_cell observed = 9

Exact modal hit on my predicted [5, 10] band. Optuna search stable; basin relocation is OOS-failure driver, NOT search instability.

## 7. Critic Phase 7.5 priority items

(a) Verdict cell collision (DUAL GATE PROMISING-clean vs F1 NEGATIVE). Recommend NEW cell LEARNED-NEGATIVE. 3bp distance from INERT should NOT be exploited to reclassify upward per `feedback_no_cheating.md`.
(b) z30 ranks worse than z90 in 3 of 4 cohorts — Critic Check 5 ADF stationarity on z90 OOS-only.
(c) LTC D funding-z30 rank 18/42 — Critic Check 4 OOS-only IC reconfirmation.

## 8. Track record

LM Master priors at /023: PROMISING tail 20%, INERT modal 52%, NEGATIVE 18%. Observed: NEGATIVE-clean 3bp from INERT. Modal call ~accurate. **Gain-share check (Phase 4.5 §4 CRITICAL) was the load-bearing diagnostic** that distinguished v1 (LEARNS) from v3 (DID NOT). Methodology 3/3 perfect.

Cumulative entering /024: H1 directional 2/4; methodology 3/3.

## 9. Most important Phase 7.4 finding

**Funding-rate is the first v1 feature family with ABOVE-uniform-parity family gain share (5.40% vs 2.38%) AND borderline-NEGATIVE F1 OOS Δ (-0.20) — the LEARNED-BUT-NOT-HELPFUL verdict cell exposes the regime-conditional structure required for /024 BOLD design (multiple smaller models per regime, per user directive).**
