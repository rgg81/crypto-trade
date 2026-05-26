# LightGBM Master Advisor — iter-v1/018 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/018`. HEAD `004d1d1`. Cycle-3 EXPLORATION #3 of 10. **FIRST per-cohort EXPLORATION** under user strategic pivot (`feedback_v1_per_cohort_exploration_strategy.md`).
- **Baseline anchor**: `v0.v1-baseline-corrected` (`f8bc12c`). Portfolio IS +0.2829 / OOS +0.6637. **Per-cohort anchor**: LINK-alone-in-pool IS +0.3724 / OOS +0.8184.
- **/017 outcome**: PROMISING-INERT (PSR jump 0.125→0.808). QR adopted Option E (LINK-only isolation) — mechanically tighter than my +XRP /017 Phase 7.4 recommendation. **QR's per-cohort pivot is a better path.**
- **Track record**: 1/15 directional + 7/15 mechanism-level.

## 1. LINK-alone-beats-portfolio plausibility — MATHEMATICAL, NOT EDGE

**EXPECTED**. Portfolio Sharpe is PnL-weighted aggregation; removing 4 drag/neutral contributors mechanically lifts LINK's aggregate Sharpe. ETH+LTC OOS drag combined -1.40 Sharpe; isolating LINK removes those. **+31% IS / +23% OOS lift is proportional to LINK's share of total weighted PnL (~21% IS / ~32% OOS)** — pure variance composition arithmetic, NOT edge discovery.

What it does NOT tell us: whether LINK-only TRAINED model produces the same LINK-alone Sharpe. The +0.8184 anchor is LINK's PnL when trained in 5-symbol pool. LINK-only training is a DIFFERENT Optuna trajectory.

## 2. F1 anchoring choice — CORRECT

Anchoring against LINK-alone-in-pool +0.8184 (NOT portfolio +0.6637) is the right per-cohort interpretation. H1 test: "can LINK-only TRAINING preserve LINK's edge?" — measures the same OUTPUT distribution (LINK monthly returns). Portfolio anchor would conflate (a) LINK-only training preservation with (b) mechanical dilution removal.

**Caveat**: at /027 CONFIRMATION bundle stage, comparison flips back to portfolio +0.6637 anchor. Brief Section 1 H2 acknowledges this.

## 3. Verdict-class priors — ADJUSTED off FLAT

LINK 8/8 OOS-positive across vastly different architectures (universe, weighting, R5, labeling, methodology) is **most stable per-symbol structural pattern in v1 catalog**. INERT-positive load-bearing.

| Verdict | QR FLAT | LM Master adjusted | Reasoning |
|---|---|---|---|
| PROMISING (Δ≥+0.20 OOS, ≥+1.02) | 33% | **30%** | requires LINK-only LIFT vs LINK-in-pool — pool may regularize toward generalizable hparams; isolation could lose that |
| INERT (Δ∈[-0.20, +0.20]) | 34% | **45%** | LINK structural signal preserved at isolation. STRONG MODAL. |
| NEGATIVE (Δ≤-0.20) | 33% | **20%** | requires LINK's edge dissolves at isolation; contradicts 8/8 multi-arch stability |
| NEGATIVE-INTRINSIC (Δ≤-0.31) | (subset) | **5%** | requires LINK's edge to be CO-TRAINING DEPENDENT — possible but Jaccard 4-29% across iterations argues against |

PROMISING-INERT (border between INERT and PROMISING) is most likely specific cell.

## 4. Hyperparameter recommendations

### 4.1 KEEP n_trials=18; DO NOT compress to 15
Per-cell training rows decrease pooled ~700 → LINK-only ~140. TPE warmup at n_trials=18 stays well above ~10 saturation threshold. Compressing saves ~1-2 min at no wall-clock pressure (12-18 min predicted, 78+ min margin) — false economy.

### 4.2 Accept current Optuna bounds; don't modify
Single-axis isolation is priority. Phase 7.4 post-mortem will read actual best-trial trajectories.

### 4.3 KEEP ENSEMBLE_SIZE=3
QR Section 3.4 asks about raising to 5. **NO**. Single-axis isolation (SYMBOL DIMENSION only); raising ENSEMBLE_SIZE confounds attribution. /027 CONFIRMATION raises to 10.

## 5. Saturation risks

**Single-cohort single-seed=42 basin lottery (HIGH-RISK)**: per v3 /020-/022 precedent, single-seed Optuna trajectories deterministic. LINK-only OOS Sharpe could land [+0.30, +1.20] from basin-lottery alone. 8/8 historical pattern argues basin FAMILY generalizable but single iteration is sample-of-1.

**Predicted n_eff_per_cell band [4, 9]** (corrected for single-cohort): fewer training rows → smaller Optuna trial diversity → lower native n_eff. INFORMATIONAL per /017 closeout demotion.

**LINK direction-asymmetry inheritance (FLAG)**: LINK IS = longs win (+92.74); LINK OOS = shorts win (+30.62). Pool's loss surface implicitly balanced direction. LINK-only model may produce direction-asymmetric overshoot — Phase 7.4 to flag if appears.

## What I Did NOT Recommend

- Multi-seed for /018 (HIGH-RISK forward-mandate not triggered)
- ATR specialization Option B (deferred to /020 follow-on; single-axis discipline)
- Feature subset Option A (confounds symbol+feature axes)
- num_leaves bound tighten pre-emptively (let Optuna discover)
- Direction-asymmetry constraint (tuning on OOS evidence violates no-cheating)
- +XRP at /018 (my /017 Phase 7.4 call SUPERSEDED by QR per-cohort pivot — better path)

## Closing Note

**MEDIUM directional confidence (45% INERT modal)**. Three calls staked:

1. **INERT 45% modal** (PROMISING-INERT specifically — Δ near 0 with structural prior intact)
2. **F1 anchoring against LINK-alone-in-pool +0.8184 is correct** for verdict cell; portfolio +0.6637 informational only
3. **KEEP ENSEMBLE_SIZE=3 + n_trials=18**; /027 multi-seed handles basin-lottery dissolution

**/019+ conditional pre-staging**:
- **PROMISING**: /019 = ETH-only with BTC-trend conditional gate (per /017 pre-commit; strongest negative-prior cohort)
- **PROMISING-INERT** (modal): /019 = ETH-only regime gate OR LINK-only with ATR specialization. Lean ETH-only to diversify cohort coverage.
- **NEGATIVE**: /019 = LINK+SOL 2-symbol pooled (tests pool-co-training requirement)
- **NEGATIVE-INTRINSIC** (5% prior): structural prior FALSIFIED; /019 = ETH-only regime gate

**Single most important point for QR**: at single-seed=42 LINK-only, OOS Sharpe variance band wide (±0.40 from basin lottery). A NEGATIVE-INTRINSIC verdict should be "basin-lottery-conditional FALSIFICATION" NOT terminal closure. /027 multi-seed is the falsification authority. Phase 8 diary should note single-seed caveat if NEGATIVE.

**Critic Phase 7.5 priority**: F-AXIS-MECHANISM #1 (Model C exclusive dispatch — `df['symbol'].unique() == ['LINKUSDT']`) is binary PASS/FAIL. Should rapidly converge.
