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

---

# LightGBM Master Advisor — iter-v1/018 — Phase 7.4 (Post-Mortem)

## Context Read
- Outcome: IS Sharpe **+0.3407** / OOS Sharpe **+0.9789** / ratio **2.87** / OOS WR 50.0% / 154 IS + 48 OOS trades / PSR_monthly_vs_0 IS=0.757 OOS=**0.885** / PSR_monthly_vs_1 IS=0.151 OOS=**0.553** / n_eff_per_cell=9.
- F1 anchor LINK-in-pool +0.8184 → **Δ +0.1605** → PROMISING-INERT cell on favorable side.
- Phase 4.5 modal call: **INERT 45% (PROMISING-INERT specifically)**. **CONFIRMED.** Track 2/16 directional + 8/16 mechanism-level.

## 1. PROMISING-INERT favorable-direction validation

Per-cohort methodology empirically VALIDATED. /014 C1-inversion + /018 PROMISING-INERT both per-cohort-level hits. Pattern: per-cohort EXPLORATION targeting cohort with structural prior ≥7/8 same-sign + single-axis isolation → INERT-modal confidence graduates MEDIUM → MEDIUM-HIGH. Global pooled axes stay LOW-MEDIUM (cycle-2/cycle-3 ledger: 0/12 PROMISING at pool level).

## 2. OOS/IS ratio 2.87 — explainable, NOT a flag

Three explanations ranked by evidence:
1. **(Strongest) LINK IS includes 2022-2024 bear-cycle drag**: monthly_pnl.csv shows 2023-11 -19.93%, 2023-12 -10.09%, 2024-04 -13.55%. IS Sharpe structurally compressed by 2 loss regimes. OOS is March 2025 → May 2026 single DeFi-favorable regime. Mean monthly PnL IS +1.35% vs OOS +2.63%.
2. **Single-cohort capacity reduction reduces IS overfit**: n_eff_per_cell=9; 154 IS trades vs ~700 pool-pooled. Less capacity to memorize IS noise.
3. **Optuna conservatism**: n_trials=18 × ENSEMBLE_SIZE=3 = 54 evaluations on single-cohort isn't enough budget to chase IS extremes.

NOT suspicious. Regime-driven + capacity-driven. 8/8 prior cross-architecture consistency is stronger anti-overfit signal than CSCV.

## 3. LINK structural prior 9/9 OOS-positive

Updated sequence: baseline +52, /011 +85, /012 +53, /013 +47, /014 +4, /015 +85, /016 +35, /017 +54, /018 +54 (LINK-only). **CV ≈ 0.51, mean +51**. Variance wide [4, 85] but SIGN rock-stable across:
- 3 different universes (5-sym, 6-sym, 1-sym)
- 4 different feature stacks
- 2 different labeling regimes (/014 C1)
- 2 different sample-weight modes
- 3 different methodology substrates

**Implication for /027**: LINK-only specialist is single highest-conviction CONFIRMATION ingredient in v1 history. Multi-seed mean predicted band [+0.60, +1.05] center ~+0.82 (matches LINK-in-pool anchor at convergence). LINK-only specialist = LOAD-BEARING bundle component.

## 4. WR 50.0% IDENTICAL — same signal, cleaner loss surface

Critical insight. WR 50.0% (vs LINK-in-pool baseline 50.0%) + avg PnL +1.12% (vs baseline ~+1.22%) but Sharpe Δ +0.16 = **loss-surface optimization without signal change**. Same LINK trades entered with different timing precision; 23% fewer trades at IDENTICAL WR means Optuna picked slightly different point on LINK's signal manifold.

**PROMISING-FEATURE-MECHANICAL adjacent** (v3 catalog cross-track): loss-surface reorganization without new edge discovery. Does NOT diminish result. Means /027 multi-seed will REGRESS toward baseline LINK-alone mean (+0.82), NOT extend beyond +0.98. **Realistic /027 LINK-only specialist = +0.80 Sharpe component, not +0.98.**

## 5. PSR jumps — credible /027 candidate

PSR_monthly_vs_0 OOS = **0.885** (well above 0.40 PROMISING-INERT floor; approaches 0.95 aspirational). PSR_monthly_vs_1 OOS = **0.553** = >50% probability LINK-only OOS Sharpe ≥ 1.0 at observed parameters.

Credible CONFIRMATION-MERGE-with-UPDATE candidate at /027, conditional on:
- multi-seed mean OOS Sharpe ≥ +0.80
- ≥7/10 seeds positive
- LINK trade count band stays [25, 75] OOS

PSR is computed over 15 OOS months — small sample. Multi-seed is the falsifier.

## 6. /019 axis selection

**RECOMMENDED: ETH-only with BTC-trend regime gate** (per /017 pre-commit + /018 Phase 4.5 §5 staged).

Reasoning:
- /018 hit PROMISING-INERT modal → my Phase 4.5 staged this branch
- ETH structural OOS drag is strongest NEGATIVE per-symbol prior (4/4 OOS-negative iterations /014-/017)
- Mechanistically-orthogonal test: whether NEGATIVE-prior cohort isolation + regime gate flips ETH drag
- Diversifying cohort coverage (LINK done, ETH next) builds /027 portfolio-of-specialists

NOT recommended:
- /019 = BTC-only — DEFER to /021 (needs labeling diagnostic before isolation)
- /019 = LINK-only ATR specialization — DEFER to /020 (burning 2nd cohort-slot prematurely)

## 7. /027 CONFIRMATION bundling preview

Projected bundle composition (conditional on /019-/026):
- **LINK-only specialist** (load-bearing, +0.80 anchor — VALIDATED at /018)
- ETH-only + BTC-trend regime gate (TBD at /019)
- BTC-only specialized (TBD at /021)
- DOT-only specialized (TBD at /022)
- SOL-only specialized (TBD at /023)
- 2-3 sym pooled cohort (TBD at /024-/026)

**Bundle Sharpe target vs portfolio +0.6637 baseline**: at multi-seed × bundle-of-N-specialists with equal weighting, expected Sharpe lift comes from diversification (low cross-specialist correlation) NOT individual edge. If LINK + ETH-regime + BTC each anchor +0.50-0.80 with cross-correlation ≤0.3, bundle Sharpe ≥+0.85 achievable.

**/027 falsifier**: bundle multi-seed mean OOS Sharpe < +0.70 → portfolio-of-specialists methodology does NOT beat naive pooling.

**Per-cohort methodology binding test**: /027 is the ONLY credible test distinguishing "LINK is intrinsic" from "LINK + 4 others diversify". Anchor flips back to portfolio +0.6637.

## What This Iteration Confirms / Refutes

**CONFIRMED**: Phase 4.5 modal INERT 45%; F1 anchoring LINK-in-pool not portfolio; HIGH-RISK declaration absorbed by 8/8 structural prior; KEEP n_trials=18 + ENSEMBLE_SIZE=3; mathematical dilution framing.

**Only directional miss**: did not pre-register "WR identical → same signal cleaner Optuna trajectory" insight. Worth pre-registering for future cohort isolations.

## Closing Note for Critic Phase 7.5

Three Critic-priority items:

1. **F-AXIS-MECHANISM #1 binary PASS** confirmed in per_symbol.csv (LINKUSDT only, 100% PnL). Converges in <2 min.
2. **Check 3 PBO unavailable** for single-symbol single-cohort (n_obs collapses). Accept as STRUCTURAL not evidence-gap. 8/8 cross-architecture prior is stronger anti-overfit signal than CSCV at single-cohort.
3. **Check 5 ADF on V1_FEATURE_COLUMNS_PRUNED 40 cols** unchanged by axis — adf_test.csv should mirror baseline distribution. Compare to LINK-only halves of baseline ADF (NOT pooled baseline distribution).
