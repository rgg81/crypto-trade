# LightGBM Master Advisor — iter-v1/044 — Phase 4.5 (Pre-Design)

## Context Read
- Track: v1, CONFIRMATION-MERGE-PORTFOLIO under NEW relative-regime-Pareto methodology (BOOTSTRAP /044).
- Anchor: BASELINE_V1 `v0.v1-baseline-corrected` IS +0.2829 / OOS +0.6637 single-seed=42; σ_R proxy band from `regime_catalog.md` §4.
- Bundle: P0 BASELINE (w=0.50) + P1 /036 LINK+DOT trend-scan (w=0.30, OOS +1.7465) + P2 /043 LINK-only trend-scan (w=0.20, OOS +1.2558).
- FIRST bundle-CONFIRMATION; multi-seed regression-to-mean is the dominant risk.

## Bundle Composition Concerns — Pairwise Correlation Predictions

| Pair | Predicted daily-PnL ρ | Trade Jaccard | Risk |
|---|---:|---:|---|
| P0 × P1 | 0.25-0.35 | 0.10-0.15 | LOW-MEDIUM (different label schemes; P0 covers BTC/ETH/LTC, P1 does not) |
| P0 × P2 | 0.20-0.30 | 0.08-0.12 | LOW (1-cohort vs 5-cohort; different label schemes; P2 LINK-only overlap with P0's LINK leg) |
| **P1 × P2** | **0.70-0.85** | 0.10-0.18 | **HIGH — exceeds Portfolio Composition Rule §3 0.70 ceiling; diary justification REQUIRED** |

**Concern**: Brief §11.4 predicts P1×P2 at 0.50-0.70. **I disagree — predict 0.70-0.85.** Both are trend-scanning-labeled, both LINK-loaded (P1 = LINK+DOT, P2 = LINK-only), trained on identical 40-col `V1_FEATURE_COLUMNS_PRUNED`, identical labeling family. Jaccard 0.125 at single-seed is a **basin-relocation artifact, NOT a signal-orthogonality artifact** — the daily-PnL co-moves through the shared LINK trend mechanism even when trade timestamps disagree.

**Implication**: bundle "diversification lift +0.05 to +0.15" (Brief §2.4) is overstated. Realistic lift +0.00 to +0.07. Re-prediction: bundle OOS Sharpe central **+0.95** (band [+0.78, +1.20]), not +1.05.

## Component Substitution Test — Predicted Bundle-Δ

| Drop | New weights | Predicted bundle OOS Δ | Reading |
|---|---|---:|---|
| Drop P0 | P1=0.60, P2=0.40 | catastrophic (loses LTC/ETH/BTC) | NOT VIABLE — diagnostic only |
| **Drop P1** | P0=0.71, P2=0.29 | **Δ −0.20 to −0.30** (largest contributor; owns OOS bull) | P1 is the load-bearing specialist |
| Drop P2 | P0=0.625, P1=0.375 | Δ −0.05 to −0.15 (small positive; offset by P2 chop drag) | P2 is borderline net-positive |

**Confirms brief Section 4 F-AXIS #4 ordering**. P2 is the marginal component; if F-AXIS #1 fails on chop OOS, drop P2 first at /045 not reweight.

## Multi-Seed Budget Verdict

`--seeds 2 --n-trials 35 --ensemble-size 5` = 10 effective models/cell. **Adequate** for σ_R proxy verification but THIN for P1×P2 correlation estimation (need 5+ seeds for ρ CI ± 0.10). Recommend: at /046 baseline re-validation, push P1×P2 correlation measurement to 5-seed minimum.

## Recommended Hyperparameter Direction (3 items)

### 1. Pin Optuna search bounds across the 3 sub-runs for cross-component reproducibility
- **What**: ensure all 3 sub-runs share `num_leaves ∈ [16, 63]`, `learning_rate ∈ [0.01, 0.1]`, `min_data_in_leaf ∈ [20, 200]`, `feature_fraction ∈ [0.4, 1.0]`. Do NOT inherit /036's frozen wider bounds vs /043's narrower bounds — risk of cross-component variance artifact.
- **Why**: Bundle-level σ_R interpretation requires per-component hyperparameter stability comparable across components. If /036 had `num_leaves` upper 127 and /043 had 63, the variance contributions are non-comparable.
- **Expected effect**: cleaner per-component substitution test interpretation; no Sharpe-Δ
- **Risk**: if /036's PROMISING-CLEAN verdict was conditioned on a specific bound, narrowing may regress its OOS. Mitigation: read /036 and /043 `run.log` and pin to the union (widest) of their bounds.

### 2. Set `lambda_l1 ∈ [0.5, 3.0]` floor for P1 and P2 at multi-seed
- **What**: floor L1 regularization for the trend-scanning components.
- **Why**: trend-scanning labels have higher within-class variance than triple-barrier (label is continuous trend-significance rather than barrier-touch). L1 sparsity counter-acts the multi-seed feature-rotation that drives basin relocation. /036 → /043 Jaccard 0.125 is symptomatic of insufficient regularization.
- **Expected effect**: multi-seed Sharpe std reduction; tighter σ_R; reduced P1×P2 trade-roster divergence.
- **Risk**: marginal IS Sharpe shift on P1 (-0.05 to +0.05); P2 may regress slightly given its already-narrow basin.

### 3. Force `bagging_fraction = 0.7, bagging_freq = 5` floor (P1 + P2)
- **What**: pin minimum bagging on the trend-scan components.
- **Why**: 5-model inner ensemble at ensemble_size=5 needs diversity; without bagging, the 5 seeds collapse to near-identical fits on small (105 OOS trade, 47 OOS trade) sub-universes. P0 (5-symbol pool) already has effective row diversity; P1/P2 do not.
- **Expected effect**: inner-ensemble variance reduction; more honest σ_R proxy at /044.
- **Risk**: minor wall-clock increase (~10%).

## Feature-Engineering Recommendation — DO NOT add new features at /044

CONFIRMATION-MERGE-PORTFOLIO is bundle-composition, not signal discovery. The 3 components are FROZEN. Adding features violates the bundle-composition mandate. Defer all feature work to cycle-6 EXPLORATIONs.

**Exception**: I recommend the runner EMIT but not gate on a 4th synthetic feature-importance artifact: per-component `feature_importance_by_seed.csv` (rank-stability across the 2 seeds). This is diagnostic-only for Phase 7.4. No risk.

## Saturation / Monoculture Risks to Flag

1. **P1↔P2 monoculture risk**: both components train on identical 40-feature pruned column set + trend-scanning labels + LINK-heavy universe. The bundle "diversification" is largely between {P0} and {P1∪P2}, not 3-way. Effective rank of the bundle covariance ≈ 2, not 3. This is the **single biggest risk** the brief understates.

2. **Single-seed=42 anchor problem**: BASELINE_V1's σ_R proxy uses formula `sqrt((1 + 0.5×SR²)/n)` from a SINGLE seed. The true 10-seed σ_R is ~3× larger per regime_catalog.md §4. Pareto-equal checks at the proxy band will be CONSERVATIVE — that's the safe direction, but if bundle BARELY clears the proxy, it likely FAILS the 10-seed re-validation at /046.

3. **chop OOS structural risk**: brief Section 10.2 predicts bundle chop OOS [+2.85, +3.30] vs Pareto-equal band ≥ +3.23. The LOW end fails. /043's −0.66 OOS chop regression at single-seed is **likely to amplify**, not regress-to-mean, because /043 had basin-relocated specifically AWAY from chop-favorable LINK behavior toward bear-LINK behavior. At multi-seed, /043's chop OOS may worsen further. This is the most likely BLOCK trigger.

4. **Wall-clock prediction (brief 3.5-4h)**: I predict **modal 4.5h, p90 5.5h**. /044-baseline at 5-cohort 5-symbol n_trials=35 ENSEMBLE_SIZE=5 seeds=2 is heavier than /037's 3h Sortino reference — the latter was likely lower n_trials or smaller universe. 6h hard cap suffices; 8h is comfortable.

## Falsifier Predictions per F-AXIS #1

- **PROMISING-CLEAN (MERGE)**: 25% prior. Requires bundle bull OOS strict-beats baseline AND chop OOS clears +3.23 AND no methodology fail.
- **PARTIAL-MERGE (chop fails, /045 reweight)**: 40% prior. Most-plausible — F-AXIS #1 fails on chop with all other regimes Pareto-equal.
- **NEG (≥2 regimes fail, return to cycle-6 EXPLORATIONs)**: 25% prior. P1×P2 high-ρ collapses diversification; bundle near-baseline overall.
- **BLOCK-PENDING-FIX or BLOCK-FINAL (methodology/wiring)**: 10% prior. Bundle aggregation arithmetic is new code (F-AXIS #2); off-by-one in proportional redistribution is plausible.

## What I Did NOT Recommend, and Why

I did NOT recommend (a) re-running /036 at the wider `--seeds 5` to refresh its anchor (over-budget; defer to /046), (b) collapsing P1+P2 into single LINK-trend-scan component (the brief explicitly tests them separately; orchestrator-locked), (c) regime-conditional dispatch at /044 bundle level (brief explicitly preserves /044 as LINEAR-BLEND baseline against which /045+ regime-dispatch CONFIRMATIONs compare).

## Closing Note

**Confidence: MEDIUM.** The bundle arithmetic predicts +1.05; my P1×P2 correlation re-prediction trims to +0.95; chop OOS is the load-bearing risk regime. **Prior probability distribution for /044 MERGE outcome: 25% MERGE / 40% PARTIAL-MERGE / 25% NEG / 10% BLOCK.** The load-bearing prediction the QR should NOT ignore: **P1×P2 daily-PnL correlation 0.70-0.85 — exceeds the brief's 0.50-0.70 estimate AND the Portfolio Composition Rule §3 0.70 ceiling.** If the observed correlation lands > 0.75, the diary should pre-commit to dropping P2 (not reweighting) at /045 — reweighting two collinear components does not buy diversification.

---

Files read:
- /home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-044/research_brief.md
- /home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/_meta/regime_catalog.md
- /home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/_meta/baseline_seed_regime_matrix.csv


---

# LightGBM Master Advisor — iter-v1/044 — Phase 7.4 (Post-Mortem, FIRST CONFIRMATION-MERGE-PORTFOLIO bootstrap)

## Context Read
- Outcome (bundle/comparison.csv): IS Sharpe +0.1106, OOS Sharpe +0.0968, IS Max DD 152.91%, OOS Max DD 62.14%, IS trades 620, OOS trades 194.
- Baseline anchor: IS +0.2829 / OOS +0.6637 → bundle Δ IS −0.17 / OOS **−0.54**.
- Engineering finding: per-component substitution Δ = 0.00 on both axes; per-regime candidate Sharpe identical to baseline Sharpe to ≥4 decimals.
- Methodology bootstrap: 24e5fc9 (walk-forward+regime-ensemble), 0153132 (Pareto), a7e3aec (bundle discipline Rules 7/8/9), 5228395 (artifacts).

## Item 0 — Regime Attribution Table (load-bearing)

| Regime | IS/OOS | Cand Sharpe | Cand MaxDD | Cand trades | Base Sharpe | Base MaxDD | Base trades | Bundle-role implication |
|---|---|---:|---:|---:|---:|---:|---:|---|
| bull | IS | +0.4114 | 64.13 | 198 | +0.4114 | 67.46 | 198 | DEGENERATE — identical to baseline; bundle adds nothing |
| bear | IS | +0.2542 | 91.76 | 113 | +0.2542 | 91.76 | 113 | DEGENERATE — bit-identical to baseline |
| chop | IS | −0.2471 | 99.99 | 168 | −0.2471 | 99.99 | 168 | DEGENERATE; chop drag inherited 1:1 |
| other | IS | −0.0964 | 84.45 | 141 | −0.0964 | 84.45 | 141 | DEGENERATE |
| bull | OOS | −0.4682 | 42.98 | 25 | −0.4682 | 42.98 | 25 | DEGENERATE — bundle = baseline trade set |
| bear | OOS | +0.0541 | 48.48 | 58 | +0.0541 | 48.48 | 58 | DEGENERATE |
| chop | OOS | +0.6545 | 12.35 | 38 | +0.6545 | 11.10 | 38 | DEGENERATE in Sharpe; MaxDD +1.25 pp worse (P1/P2 noise) |
| other | OOS | −0.0777 | 51.78 | 73 | −0.0777 | 51.78 | 73 | DEGENERATE |
| vol-spike / recovery | both | empty | — | 0 | empty | — | 0 | Zero-coverage regimes; no signal either way |

**Per-regime Pareto vs baseline trivially PASS (equal-on-all-axes), but with strictly-zero edge.** Check 3d math returns PASS by tautology, NOT by demonstrated bundle dominance. This is a degenerate PASS and the diary MUST flag it as such.

## F-AXIS Falsifier Cascade

| Falsifier | Predicted | Observed | Verdict |
|---|---|---|---|
| F1 — OOS Sharpe Δ ≥ −σ_R band edge | ≥ +0.40 | **−0.54** | **FAIL — NEG-CAT band** |
| F2 — Bundle aggregation arithmetic sound | wiring intact | active-weight renorm collapses to single-component-at-a-time | **MECHANISM-BROKEN (NOT off-by-one; design defect)** |
| F3 — Component substitution shows marginal contribution | drop P1 → Δ −0.20 to −0.30; drop P2 → Δ −0.05 to −0.15 | **drop P1 → Δ 0.00; drop P2 → Δ 0.00** | **FAIL — components carry zero marginal weight in observed bundle** |
| F4 — P1×P2 correlation < 0.70 ceiling | predicted 0.70-0.85 (correlation file empty) | unmeasurable — disjoint timings | N/A |

**OVERALL F-AXIS verdict cascade**: F1 NEG-CAT → triggers F2/F3 investigation → F2 mechanism defect localized → **band reclassifies from NEG-CAT to LEARNED-NEG-MECHANISM (band #8) NOT NEGATIVE-no-effect**, because the failure mechanism IS understood and load-bearing on the aggregator wiring, not on signal absence. Rule-7-violation overlay: bundle ALSO retroactively illegal.

## Hyperparameter Trial Stability (per component)

| Component | Cohorts × Symbols × Trials × Ensemble × Seeds | Effective fits | Stability comment |
|---|---|---:|---|
| BASELINE (P0) | 5 × 5 × 50 × 5 × 2 | 12,500 | Frozen tag artifact; stable by construction |
| /036 (P1) | 2 × 2 × 35 × 5 × 2 | 1,400 | Within-prior-tag stability; not re-tuned |
| /043 (P2) | 1 × 1 × 35 × 5 × 2 | 350 | Lowest fit count; thinnest variance pool |

Per-component hyperparameter stability is **NOT the load-bearing risk** at /044 — the components were not re-tuned. The defect lives in the AGGREGATOR, not the learners. No actionable per-component HP recommendation results from this iteration.

## Suspicious Patterns (the load-bearing finding)

**The bundle is the union-at-full-weight of three disjoint trade rosters, NOT a weighted ensemble.** Mechanism:

1. P0 baseline emits a LINK trade at t1 with intended weight 0.50. P1 and P2 emit nothing at t1. The aggregator's **active-weight renormalization** divides 0.50 by (sum of active weights at t1) = 0.50, giving the trade weight 1.00.
2. Same arithmetic for any t where only P1 emits (renormalized 0.30 → 1.00), and any t where only P2 emits (renormalized 0.20 → 1.00).
3. Because P0 / P1 / P2 trade-timing Jaccard is near zero (different label schemes + symbol cohorts), simultaneous emissions are vanishingly rare. **Almost every trade is "the only active component at that timestamp" → promoted to weight 1.00.**

**Consequence**: bundle ≡ concatenated trade roster of {P0 ∪ P1 ∪ P2}, each at full size. The "weighted ensemble" framing in the brief is FALSE under this aggregator. The regime-attribution rows being bit-identical to baseline on bull/bear/chop/other implies that within those tagged windows ONLY baseline trades fired (or the renormalization made P1/P2 trades land outside the regime bins). The chop OOS MaxDD lift +1.25 pp is the only fingerprint that P1/P2 added trades at all.

Additional pathology: **backtest↔live parity is structurally broken.** Live cannot run three simultaneous open positions in the same symbol (`OrderManager` rejects duplicates). The backtest summed them. Any merged bundle would diverge from live execution on the first symbol-overlap candle.

## Methodology Violation — Rule 7 (retroactive)

Bundle composition violates Rule 7 (no coin overlap across components): LINK appears in P0 + P1 + P2; DOT appears in P0 + P1. Rule 7 was committed (a7e3aec) AFTER /044 dispatched, so the violation is RETROACTIVE — the brief and pre-flight could not have caught it. The advisory diary MUST flag this and the verdict MUST treat /044 as a one-shot bootstrap exercise NOT a MERGE candidate.

## Mechanism Interpretation

Two architectural defects, ranked:

1. **Aggregator design defect (load-bearing)**: active-weight renormalization is incompatible with the weighted-ensemble theory. The aggregator needs ONE of: (a) cohort-disjoint federation (Rule 7 partition) so each symbol is owned by exactly one component, (b) score-level blending pre-trade (each component emits a continuous score, aggregator blends, single trade decision), or (c) capital-budget-share with hard ceiling (a component's weight is its budget envelope, NOT its renormalized active share). The "linear blend of trade rosters" framing in the brief does not survive contact with the aggregator code.
2. **Cohort overlap (Rule 7 violation)**: even if the aggregator math were sound, three components all training LINK introduces same-symbol position pile-up that breaks live parity.

## Next-Iteration Tuning Recommendations

### 1. /045 = symbol-partitioned federation (PRIMARY)
- **What**: bundle = baseline_pool_A {BTC, ETH, LTC} ∪ baseline_D {DOT} ∪ /036_restricted {LINK only}. Each symbol owned by exactly ONE component.
- **Mechanism**: Rule 7-compliant by construction; aggregator becomes trivially correct (disjoint timing × disjoint symbols → no renormalization ambiguity); live-parity restored.
- **Risk**: drops /043 entirely (LINK already owned by /036 in the federation); /043's LINK-OOS signal becomes dead unless /046+ explores LINK-cohort re-arbitration.

### 2. Aggregator unit test mandate
- **What**: before /045 launches, QE must commit a unit test that exercises the aggregator on a SYNTHETIC 3-component fixture where ground-truth weighted PnL is computable analytically. Current code path was never tested with disjoint timings.
- **Risk**: blocks /045 dispatch by ~0.5 day; non-negotiable given /044 finding.

### 3. Drop the "linear blend" theoretical framing from briefs
- **What**: Section 2 framing in future bundle briefs must specify the FEDERATION TYPE (symbol-partitioned, regime-dispatched, score-blended, or capital-budgeted) and the aggregator code path that implements it.

## What This Iteration Confirms / Refutes About Prior LM Master Advisory

The Phase 4.5 advisory predicted P1×P2 ρ ∈ [0.70, 0.85] and chop OOS as the load-bearing failure regime. **Both predictions are NEITHER confirmed NOR refuted** — the aggregator defect made P1 and P2 contribution effectively zero, so the correlation never got to express. Phase 4.5 advisory probability distribution (25/40/25/10) **assigned only 10% to BLOCK / methodology-defect outcomes; the actual outcome IS that 10% bucket**. The advisory missed the aggregator semantics — I read the components and the brief but did not read the aggregator code path. Correction logged: future bundle-CONFIRMATION 4.5 advisories MUST read the aggregator implementation, not just the per-component runners.

## Closing Note for Critic (Phase 7.5)

Three flags for the Critic's pass: (a) regime-attribution Check 3c PASSES tautologically because candidate=baseline on every regime — the Critic should affirmatively note this is a DEGENERATE PASS, not a Pareto-dominance demonstration; (b) Rule 7 violation is RETROACTIVE — Rule 7 was committed after /044 dispatched, so the appropriate verdict is `CONFIRMATION-BLOCK-METHODOLOGY-DEFECT` (do not update BASELINE_V1) NOT a punitive review; (c) the aggregator-design defect is the actionable finding — the Critic's Path Forward should anchor on /045 = symbol-partitioned federation per Rule 7 with the aggregator unit-test pre-condition.

**Do NOT update BASELINE_V1.md.** Bundle did not strictly-beat baseline; bundle did not even differ from baseline meaningfully. Retain `v0.v1-baseline-corrected` as the anchor.
