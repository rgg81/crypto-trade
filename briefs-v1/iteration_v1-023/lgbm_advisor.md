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
