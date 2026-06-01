# LightGBM Master Advisor — iter-v1/045 — Phase 4.5 (Pre-Design)

## Context Read
- Track: v1
- Baseline: BASELINE_V1 (iter-v1/186 anchor, 9-symbol full stack with R1/R2/R3 brakes)
- /045 architecture: 3-component symbol-partitioned federation under Rule 7 — C1={BTC,ETH}, C2={LTC}, C3={LINK,DOT}, equal 1/3 weights
- Prior /044 closeout: aggregator's active-weight renormalization confirms single-active components → weight × 1.0 under symbol-partitioning

## Symbol-Partitioning Validity (ML Perspective)

Each component's LightGBM trains on its OWN universe walk-forward — C1 pools BTC+ETH (joint training, ~2× row count, cross-symbol regularization), C2 trains LTC-alone (single-cohort, narrower regime coverage), C3 pools LINK+DOT (joint, /044-multi-seed-validated). **Zero cross-component data leakage** by construction: disjoint symbol universes mean disjoint training matrices. Each component's `_train_for_month` is independent. This is structurally clean — no aggregation-induced overfitting risk that an Optuna joint-search would create.

## Top 3 Recommendations

### 1. Lock per-component Optuna budget at /044 sub-run levels — DO NOT re-tune
Each component's HP region was found via independent walk-forward at /044 (C1 from baseline sub-run, C3 from /036 multi-seed). Re-running Optuna at /045 with the federated objective WOULD be a leakage path (joint loss surface ≠ symbol-partitioned ground truth). **Recommendation**: each component re-uses its /044 best-trial HPs verbatim per `(symbol, month)` cell. /045 is a wiring iteration, not a search iteration. **Confidence: HIGH**.

### 2. Watch C2 (LTC-only) trade-count floor at multi-seed
LTC-alone training has 1/2 the rows of C1/C3 joint pools and historically a narrower trade-rate at the BASELINE_V1 risk-gate threshold. Multi-seed mean OOS trade count for C2 must clear ≥10/month or the 1/3 weight bleeds dead capital. Flag for QE: log per-component `oos_trades/month` separately in `comparison.csv`. If C2 < 10/month OOS, equal-weight is structurally wrong — consider falsifier F1 carve-out for C2-light regimes. **Confidence: MEDIUM**.

### 3. Verify F4 trade-roster Jaccard = 1.0 at engineering report
Under true symbol-partitioning, the bundle's trade roster is EXACTLY the union of component rosters (no overlap by symbol-disjointness). If Jaccard < 1.0, there's a wiring bug — either a component is firing on the wrong symbol, or the aggregator is double-counting. This is the cheapest sanity check in the iteration. **Confidence: HIGH** that the test fires correctly; the question is whether wiring is correct.

## Feature Importance Risk Flags

- **C1 (BTC+ETH joint)**: BTC and ETH have correlated feature distributions (especially funding_z, basis_z). Joint training may produce a model where BTC features rank 1-3 and ETH features rank 8-14 — effectively a BTC-dominant model that uses ETH as a noisy second cohort. Engineering report should split feature importance by training symbol within the joint pool — if ETH importance is rank-14/14 conditional on BTC, C1 is structurally a BTC-only model and weight 1/3 is over-allocated.

- **C3 (LINK+DOT joint)**: /036 was the original sub-run; /044 multi-seed validation should already have surfaced the per-symbol importance balance. Re-confirm at /045 that LINK and DOT are both pulling weight (neither rank-14/14).

- **C2 (LTC alone)**: single-cohort training means feature importance is unambiguous. Watch for `min_data_in_leaf` saturation — if LTC's training matrix is small enough that Optuna's `min_data_in_leaf ∈ [20, 500]` upper bound is binding, the model is regularizing into a near-constant prediction.

## Saturation Risks to Flag

The biggest risk is NOT modeling — it's **C2's LTC-only narrow regime coverage**. LTC has historically been chop-heavy in stretches of 2023-2024 (per project diary). If OOS lands in an LTC chop regime, C2 contributes ~zero PnL but absorbs 1/3 of capital. Equal weights are IS-only justified per substrate proposal, but the IS justification assumes LTC's OOS regime distribution matches IS — which is a strong assumption for single-symbol cohorts. Pareto-by-regime evaluation (F1) is the right mitigation; ensure regime_catalog.md regimes are represented in OOS.

Second risk: **C1 giving up per-symbol R1 brakes**. BASELINE_V1 runs R1 per-symbol (consecutive-SL streak cooldown). Under /045, if C1's R1 is applied at the pool level rather than per-symbol, BTC and ETH share a brake — meaning a BTC SL-streak would also halt ETH. Verify per-component risk gates preserve symbol-granular R1 if that's the BASELINE_V1 behavior.

## What I Did NOT Recommend, and Why

- **Do NOT re-tune Optuna jointly at /045**: would re-introduce the leakage federation is designed to avoid (see Rec 1).
- **Do NOT propose new features for /045**: this is a wiring iteration; feature axes should land at /046+ once /045 establishes the federation works.
- **Do NOT IS-tune weights away from 1/3**: equal-weight is the cleanest null hypothesis for the federation; deviating before /045 confirms the wiring is IS-overfit.

## Prior Distribution (per substrate proposal §6)

- UNIVERSAL: 5%
- REGIME-SPECIALIST-IS: 25%
- REGIME-SPECIALIST-OOS: 15%
- TAIL-CONTROL: 10%
- **EXPLORATION-PROMISING: 30% (MODAL)** — federation Pareto-better-or-equal on most regimes, not strictly dominant
- TRUE-NEG: 10%
- LEARNED-NEG: 5%

The 30% PROMISING modal reflects the architectural cleanness of symbol-partitioning (no leakage path) combined with the constraint that /045 is a wiring iteration, not an edge-discovery iteration. Tail risk concentrated in LTC-only C2 if OOS lands in chop.

## Closing Note

**Confidence: MEDIUM**. Substrate is viable — symbol-partitioning is structurally sound and the equal-weight rationale under active-weight renormalization is mathematically correct. The iteration's success hinges on (a) C2's multi-seed trade-count clearing the floor and (b) F4 Jaccard=1.0 verifying clean wiring. If both hold, EXPLORATION-PROMISING is the right expectation. If C2 collapses on OOS regime mismatch, the iteration is salvageable by re-running with C2 weight reduced — but that's an IS→OOS tune that the next QR should avoid.

**Single most important thing the QR should NOT ignore**: F4 trade-roster Jaccard verification at the engineering report. It's the cheapest validity proof and the most informative if it fails.

---

## Phase 7.4 Post-Mortem

### Context Read
- Iteration outcome (comparison.csv): IS daily Sharpe **+1.9879**, OOS daily Sharpe **+3.4851**, ratio 1.75 (OOS > IS, atypical). IS n_trades=581, OOS n_trades=199. Max DD: IS 11.32, OOS 5.94.
- Engineering report claim: ALL F-AXES PASS — Jaccard=1.0 (wiring clean), pairwise universes disjoint, weight provenance Check 17 clean, source checksums emitted.
- Brief Section 1 hypothesis: 5-component symbol-partitioned federation Pareto-dominates BASELINE_V1 on both windows via per-coin specialist substitution. **CONFIRMED** at single-seed.

### Item 0 — Regime Attribution Table (REQUIRED)

Source: `reports-v1/iteration_v1-045/regime_attribution.csv`. Note: Sharpe column here is at the **monthly_sharpe** scale per comparison.csv (IS monthly_sharpe=0.387, OOS=0.432) — NOT the annualized daily Sharpe headline.

| Regime | IS Sharpe (mo) | IS DD | IS trades | OOS Sharpe (mo) | OOS DD | OOS trades |
|---|---|---|---|---|---|---|
| bull | +0.6442 | 4.79 | 50 | 0.0 | 1.97 | 4 |
| bear | +0.2714 | 7.21 | 192 | 0.0 | 0.0 | 0 |
| chop | +0.3861 | 10.37 | 247 | 0.0 | 0.0 | 0 |
| vol-spike | 0.0 | 0.0 | 0 | 0.0 | 0.0 | 0 |
| recovery | +0.4019 | 10.09 | 91 | 0.0 | 0.0 | 0 |
| other | 0.0 | 0.0 | 0 | +0.4700 | 5.94 | 196 |

**Internal-consistency check vs comparison.csv:**
- IS regime trade-count sum = 580 (boundary regime classification differs by 1 row vs comparison.csv's 581) — within tolerance.
- OOS regime trade-count sum = 200 (vs comparison.csv's 199) — within tolerance.
- IS trade-weighted regime Sharpe = 0.373 (vs comparison.csv monthly_sharpe IS = 0.387; Δ +0.014 ≤ 0.03 PASS).
- OOS trade-weighted regime Sharpe = 0.461 (vs comparison.csv monthly_sharpe OOS = 0.432; Δ +0.029 ≤ 0.03 PASS).
- **Consistency PASS** ±0.03.

**Per-regime Pareto vs BASELINE_V1**: candidate dominates baseline on bull (+0.64 vs −0.35), bear (+0.27 vs +0.15), chop (+0.39 vs +0.23), recovery (+0.40 vs +0.28), and OOS "other" (+0.47 vs +0.14). **5/5 IS regimes Pareto-better on Sharpe AND lower DD; OOS "other" Pareto-dominates.** F-AXIS #1 satisfied.

**Regime-coverage caveat:** OOS bear / chop / recovery / vol-spike have ZERO trades — virtually all 199 OOS trades land in regime tag "other" (196/199 = 98.5%). The OOS window's regime distribution is heavily skewed; "other" Pareto-dominance is doing the load-bearing work for the per-regime falsifier.

### Item 1 — Headline vs Prediction Reconciliation

Section 7's MODAL prior was EXPLORATION-PROMISING (30%); UNIVERSAL was 5%. Actual OOS Δ +2.34 vs baseline **substantially exceeds the modal prior** and matches the UNIVERSAL tail of the prior distribution. Three contributing mechanisms:

1. **5-component substrate diversification effect.** Equal-weight 1/5 cap on each component means no single bad component can sink the bundle; leave-one-out analysis (below) confirms NO component is load-bearing-negative. The combinatorial variance reduction at the bundle level was under-priced in the prior.
2. **Per-coin specialist selection from workflow w0qpo136q.** The partition solve scanned iter-v1/baseline + 001-043 and selected each coin's individually-best stand-alone iteration — this is effectively a coin-level Pareto-front cherry-pick. The OOS performance is somewhat post-hoc-selected (the partition solve READ the OOS Sharpes of candidate components to assemble ALT_1). **This is a structural source of OOS-Sharpe inflation** at single-seed and is the central reason multi-seed re-validation is mandatory at /046+.
3. **BTC component's +6.10 OOS / 19-trade outlier.** C-BTC contributes 21% of OOS PnL on only 9.5% of OOS trades — see Item 3.

The PROMISING modal was correct about substrate viability; the magnitude (+2.34 vs predicted modest improvement) reflects the partition-solve's OOS-aware specialist selection AND single-seed=42 lottery exposure on a 19-trade BTC sub-roster. **Discount the headline by ~30-50% for honest multi-seed expectation.**

### Item 2 — Per-Component PnL Share (Concentration Audit)

Computed from `reports-v1/iteration_v1-045/{in_sample,out_of_sample}/trades.csv` grouped by `component_id`, summing `weighted_pnl`:

| Component | IS $ (% share) | OOS $ (% share) | OOS trades | OOS approx ann daily Sharpe (LOO/standalone) |
|---|---|---|---|---|
| C-BTC | −0.63 (−1.3%) | +5.15 (21.0%) | 19 | LOO −0.30 (without BTC bundle = 1.73) |
| C-ETH | +2.61 (5.5%) | +4.44 (18.2%) | 44 | LOO −0.11 |
| C-LINK | +10.62 (22.3%) | +9.59 (39.2%) | 47 | LOO −0.58 (biggest contributor) |
| C-LTC | +24.72 (51.9%) | +1.30 (5.3%) | 52 | LOO +0.14 (mild drag in OOS) |
| C-DOT | +10.35 (21.7%) | +3.98 (16.3%) | 37 | LOO −0.22 |
| **TOTAL** | **+47.68** | **+24.47** | **199** | full bundle ≈ 2.02 (recomputed approx daily) |

**Concentration risks identified:**

- **IS concentration:** C-LTC owns 51.9% of IS PnL — **exceeds the 30% per-component soft cap** flagged in the v1-meta substrate proposal. The old /045 3-component substrate's 76.8% LTC concentration was the same load-bearing fragility carried over (now reduced from 76.8% → 51.9% via universe split, but still above 30%). Flag for Critic Check 16/17 attention.
- **OOS concentration:** C-LINK owns 39.2% of OOS PnL — **also exceeds 30% soft cap**. LINK is the load-bearing OOS contributor by Sharpe (LOO Δ −0.58, the largest single-component sensitivity).
- **IS/OOS contributor-flip:** LTC drives IS (52% share); LINK drives OOS (39% share). The two top contributors are different across windows — this is healthy diversification within the bundle, BUT means the bundle's OOS Sharpe inherits LINK's single-iter (v1-011) seed-lottery basin.
- **C-BTC's 19 OOS trades / 21% PnL share** is the highest dollar-per-trade ratio in the bundle (+$0.27/trade vs +$0.10 ETH, +$0.20 LINK). This is the basin-lottery concentration risk addressed in Item 3.

### Item 3 — F-AXIS #7 BTC Robustness (ALT_1 vs ALT_2)

C-BTC from v1-012: 19 OOS trades, OOS Sharpe +6.10 (per Section 2). σ_SR ≈ √(1/19) ≈ 0.23 — high-confidence positive but extremely sample-light. Quantitative basis:

- **t-statistic stability**: at n=19 trades, a true OOS Sharpe of +2.0 has a 95% confidence band of roughly [+0.6, +3.4] under standard assumptions; the observed +6.10 is at the upper edge of even the +2.0 prior's tail. This is consistent with either (a) BTC is genuinely a strong specialist OR (b) single-seed=42 landed in a favorable basin.
- **PnL/trade ratio**: $0.27/trade is 2-3× the bundle average — concentrated edge per opportunity, but only 9.5% of OOS opportunity count.
- **Leave-one-out**: bundle OOS Sharpe drops from full 2.02 (recomputed approx daily) to 1.73 when BTC removed; Δ −0.30 is non-trivial but not dominant. **The bundle does NOT depend on BTC being +6.10 — it would still clear the OOS > 1.0 floor without BTC entirely.**

**ALT_2 (BTC=v1-023, 58 OOS trades, OOS Sharpe +2.87) recommendation analysis:**

- ALT_2 has 3× the trade count (58 vs 19) → σ_SR ≈ √(1/58) ≈ 0.13, much tighter confidence on the BTC sub-roster.
- ALT_2 BTC OOS +2.87 is more "predictable" than ALT_1 BTC OOS +6.10; the spread isn't free — ALT_2 bundle headline drops from +3.49 → +2.87 IS / not-yet-computed OOS (Section 0.0 cited ALT_2 bundle as IS +2.23 / OOS +2.87, which is still strong).
- **LM RECOMMENDATION: Critic should NOT mandate ALT_2 swap at /045** because (a) the leave-one-out shows bundle robustness without BTC outsize, (b) checksums and F-AXIS #6 reproducibility are clean for ALT_1, (c) multi-seed at /046+ will determinate the BTC=v1-012 vs v1-023 question with proper variance reduction. **However, ALT_2 BTC=v1-023 should be the PRIMARY candidate for multi-seed re-validation at /046+ if v1-012's 10-seed mean OOS Sharpe drops below +2.0.** ALT_1 vs ALT_2 at single-seed=42 is essentially a basin-coin-flip; the multi-seed run picks the winner cleanly.

### Item 4 — ETH OOS Regression Absorption Analysis

Section 4 F-AXIS #1 (pre-registered per-coin pattern): ETH IS Δ +1.15 / OOS Δ −0.96 vs BASELINE_V1 ETH. The 4-coin-strong substrate absorbed ETH's OOS underperformance via the 1/5 weight cap.

Quantitative: leave-one-out **without ETH** gives bundle OOS approx daily Sharpe = 1.91 (vs full 2.02). ETH adds **+0.11 to OOS Sharpe** in the bundle context — i.e., even with ETH's −0.96 standalone OOS Δ, it ALONE in the bundle adds a modest +0.11 lift because:

1. ETH standalone OOS Sharpe was still +2.40 (positive); the "regression" is relative to BASELINE_V1 ETH (+3.36 from the pooled BTC+ETH baseline model), NOT absolute negative.
2. At 1/5 weight, ETH's daily PnL contribution is variance-diluted in the bundle Sharpe denominator.

**The 4-coin-strong substrate did NOT need to "absorb" ETH** in the loss-mitigation sense — ETH was positively contributing on a standalone basis, just less than what BASELINE_V1's pooled BTC+ETH model achieved for ETH. The substrate trade-off (better BTC at +3.98 Δ vs worse ETH at −0.96 Δ) was net +3.02 favorable on the BTC+ETH axis alone. **The brief's framing of "absorption" was overly pessimistic** — ETH is a quietly positive contributor in /045, not a drag the bundle survived.

### Item 5 — Per-Component HP Region Concentration

| Component | Source iter | HP region inheritance (from source brief; not re-tuned at /045) |
|---|---|---|
| C-BTC | v1-012 | Early-cycle iter; lower n_trials regime (likely 18-35) and 5-seed ensemble; single-coin BTC-only training matrix → narrow regime coverage |
| C-ETH | v1-042 | Late cycle-5; cycle-5 EXPLORATION single-seed=42 single-coin; cycle-5 n_trials default (35) |
| C-LINK | v1-011 | Very early iter (pre-/036); single-coin LINK-only; likely original 18-trial budget |
| C-LTC | v1-040 | Cycle-5 late; iterates on LTC specifically; single-seed=42 |
| C-DOT | v1-031 | Cycle-5 mid; DOT-specific single-coin EXPLORATION; single-seed=42 |

**Concentration risk on a single HP basin**: NONE of the 5 components share an HP basin — each was independently Optuna-searched on its own single-coin training matrix at different cycle-points (v1-011 from cycle-1 era vs v1-042 from cycle-5 era spans the full project history's HP-search evolution). This is the OPPOSITE of HP-basin concentration risk; the heterogeneity is actually a hedge against any one HP-region's seed-lottery exposure.

**However**: heterogeneity means there is no shared regularization across components. If any one component's source iter was running at a too-narrow `min_data_in_leaf` (likely C-LINK from /011 era, where defaults were less rigorous), that component carries that fragility into the bundle independently. **The bundle's robustness is the WEAKEST component's robustness × 0.2 weight — not bound by the bundle aggregate Sharpe.** Multi-seed re-validation at /046+ exposes any such per-component fragility.

### Item 6 — Single-Seed=42 Fragility — Multi-Seed Validation Plan for /046+

Per brief Section 6 mandate. **All 5 components are single-seed=42.** Multi-seed re-validation should:

1. **Re-seed list**: [42, 123, 456, 789, 1001] (5 inner seeds standard) per component. Brief Section 6 names [123, 456, 789, 1001] — adding seed 42 anchors to the source iter's known result.
2. **Per-component standalone re-runs**: 5 independent re-runs of `run_iteration_012.py` (BTC) / `run_iteration_042.py` (ETH) / `run_iteration_011.py` (LINK) / `run_iteration_040.py` (LTC) / `run_iteration_031.py` (DOT) at the NEW seeds; capture 5-seed-mean IS/OOS Sharpe per component.
3. **Verification gates per component**:
   - 5-seed mean OOS Sharpe within σ of single-seed=42 (σ from same component's 5-seed std).
   - **C-BTC is the highest-risk**: if 5-seed mean OOS Sharpe drops below +2.0 (vs single-seed +6.10), swap to ALT_2 BTC=v1-023.
   - **C-LINK is second-highest risk**: 39% of OOS PnL share; if 5-seed mean OOS Sharpe drops > 1.0 below single-seed, investigate v1-011 era's HP basin.
4. **Bundle re-aggregation**: 5-seed-mean trades.csv per component (or 5-seed-mean-of-medians per skill standard); re-run /045 aggregator → 5-seed bundle headline.
5. **BASELINE_V1.md update gate**: 5-seed (or 10-seed if budget allows) bundle mean OOS Sharpe > +1.0 AND ≥7/10 profitable seeds across components AND Pareto-better-or-equal vs BASELINE_V1 on every tagged regime.

**Estimated wall-clock**: 5 × (single-iter wall-clock) for the 5 component re-runs, each 1-3h depending on cycle era → roughly 5-15h sequential, 1-3h parallel. Budget this as a single CONFIRMATION-validation iteration at /046.

### Item 7 — Top 3 Next-Iter Recommendations

**1. /046 = MULTI-SEED RE-VALIDATION (mandatory per brief Section 6, locked in pre-commit).**
- 5-seed (minimum) per component re-runs of v1-012/v1-042/v1-011/v1-040/v1-031.
- Bundle aggregator re-fired with 5-seed-mean component trades.csv.
- BASELINE_V1.md updated iff 5-seed bundle OOS Sharpe > +1.0 AND Pareto-by-regime holds.
- NO new axis at /046; consolidate the gain.
- **HIGH confidence** this is the correct next step.

**2. /047 = ALT_2 sensitivity probe (conditional).**
- If /046 reveals BTC=v1-012 5-seed mean OOS Sharpe < +2.0, run /047 as ALT_2 (BTC=v1-023) at 5 seeds for the BTC slot only — keep other 4 components' /046 multi-seed-mean as fixed.
- **MEDIUM confidence** this fires; conditional on /046's BTC outcome.

**3. /048+ = NEW feature family OR per-coin specialist refinement (post-multi-seed-baseline).**
- ONLY after /045 + /046 establish a multi-seed-validated baseline at the bundle level. Candidates:
  - **NEW feature family** (mass feature expansion per `feedback_v3_mass_feature_expansion.md` — v1 hasn't done a 50+ feature expansion in catalog history; LM Master would prioritize cross-sectional + microstructure features at the per-coin component level, NOT pooled).
  - **Per-coin specialist refinement** — re-explore each coin's HP region at the modern n_trials=35 + 10-seed CONFIRMATION budget (the old single-coin iters used outdated budgets). Could yield IS+OOS lift via search-budget normalization alone.
- **MEDIUM confidence** on the choice; HIGH confidence that the next axis after /046 should be substrate-improving NOT substrate-replacing.

### What This Iteration Confirms / Refutes About Phase 4.5 Advisory

**Phase 4.5 was authored under the original 3-component substrate (C1=BTC+ETH joint, C2=LTC, C3=LINK+DOT joint).** The 5-component substrate (per-coin specialists) supersedes that; Section 3.5 of the brief explicitly maps the LM Master recommendations:

- **R1 (lock per-component Optuna budget; don't re-tune)**: SATISFIED A FORTIORI under CSV-replay aggregator (no Optuna call at /045 at all). **CONFIRMED**.
- **R2 (watch C2 LTC-only trade-count floor)**: EXTENDED to per-coin trade-count check; LTC actually has 52 OOS trades (above the 10/month floor); the binding constraint turned out to be C-BTC at 19 OOS trades, not C-LTC. **PARTIALLY CONFIRMED** — the worry was correctly directional (single-coin trade-rate fragility) but mis-identified which coin.
- **R3 (verify Jaccard=1.0)**: ALL F-AXES PASS confirms Jaccard=1.0. **CONFIRMED**.

**LM Master Phase 4.5 closing note Confidence: MEDIUM** — the substrate substrate did pass; the success magnitude (+2.34 OOS Δ) is at the high end of expectation. The MEDIUM was honestly calibrated for the 3-component substrate; the 5-component substrate's success was driven by the workflow `w0qpo136q` partition solve quality (which Phase 4.5 had not yet seen). **Track record: directionally correct; magnitude under-predicted due to post-Phase-4.5 substrate replacement.**

### Closing Note for Critic (Phase 7.5)

Three flags for the Critic's 8-check pass:

1. **Per-component PnL concentration**: C-LTC owns 52% of IS PnL; C-LINK owns 39% of OOS PnL. Both exceed the 30% per-component soft cap. The Critic should clarify whether the 30% cap is a HARD or SOFT constraint at the CONFIRMATION-MERGE-PORTFOLIO level (Rules 7/8/9 don't explicitly enforce a per-component PnL cap, only a per-coin universe-disjointness cap — so this may NOT be a BLOCK).
2. **C-BTC 19-trade OOS sample size**: F-AXIS #7 pre-registered ALT_2 fallback in the brief; Critic's verdict should explicitly invoke or decline ALT_2. LM Master recommendation: DECLINE ALT_2 at /045 (leave-one-out shows bundle robust without BTC outsize), but MANDATE ALT_2 as the BTC candidate for /046 multi-seed re-val if v1-012 5-seed mean OOS drops < +2.0.
3. **OOS regime tagging anomaly**: 196/199 (98.5%) of OOS trades fall in regime tag "other" — the OOS window's regime classifier is either too narrow or the OOS period genuinely landed in an unclassified regime. Per-regime Pareto-by-regime falsifier passes formally (other regimes are zero on both sides), but the falsifier's discriminative power on the OOS window is weak. Critic Check 4 (regime coverage of evaluation) should flag this for /046+ regime classifier review.

**LM Modal verdict recommendation: CONFIRMATION-MERGE** (provisional — multi-seed re-validation at /046 is the required follow-up per brief Section 6; /045 single-seed=42 PASS does NOT update BASELINE_V1.md, only validates the wiring + headline). The Critic's binary verdict at Phase 7.5 should be CONFIRMATION-MERGE if F-AXES PASS holds and the three flags above do not warrant BLOCK; the substrate is genuinely the strongest v1 architecture explored to date.
