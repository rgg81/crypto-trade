---
iteration: iter-v1/017
date: 2026-05-26
verdict: EXPLORATION-NEGATIVE
subtype: anti-direction-INERT
axis_family: universe (UNUSED since /006; first cycle-3 universe family)
cadence_position: cycle-3 EXPLORATION (#2 of 10)
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c) — UNCHANGED
merge_decision: NO-MERGE (EXPLORATION-NEGATIVE anti-direction-INERT; F1 OOS Δ -0.0908 INERT-band but anti-direction + F-AXIS-MECHANISM #3 FAIL n_eff=9 + F8 OOS trade-count breach 301>284; BASELINE_V1 update NOT triggered)
---

# Iteration iter-v1/017 — Diary

## Decision: NO-MERGE

EXPLORATION-NEGATIVE anti-direction-INERT. Universe-expansion axis produced **basin-reorganization without signal discovery** (PSR jump +0.68; ETH partial dilution -51→-28; SOL clean 16.4% share). Critic took conservative anchor per cycle-3 discipline; LM Master reframed as PROMISING-INERT but no edge to bundle. BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`).

## One-Line Outcome

At v1 EXPLORATION budget (ENSEMBLE_SIZE=3 + n_trials=18 + V1_FEATURE_COLUMNS_PRUNED + 6-symbol universe with +SOL + 8h candles + `abs_pnl` weighting reverted + Model F = Model A-sister with R3 only + R5 disabled) adding SOLUSDT as single-symbol Model F produced **IS Sharpe +0.3338** (Δ **+0.0509** INERT band) + **OOS Sharpe +0.5729** (Δ **-0.0908** INERT anti-direction) + **F-AXIS-MECHANISM #1 PASS** (SOL 51 OOS trades clean dispatch) + **#2 PASS** (SOL 16.4% portfolio share ∈ [5%, 40%]) + **#3 FAIL** (n_eff_per_cell_median = 9, below LM Master Phase 4.5 [11, 17] band — 3rd consecutive REFUTATION; corrected to [8, 13]) + **F8 OOS BREACH** (301 OOS trades exceeds upper-end 284 by +17) + **PSR_monthly_vs_0 OOS = 0.808** (+0.68 jump vs /016's 0.125 — largest single-iter jump in cycle-3) + **ETH OOS PARTIAL dilution** (/014 -41.18 → /015 -23.29 → /016 -51.46 → **/017 -28.07**; 2nd-best ETH OOS in cycle-2+3 window; dilution mechanism WORKING) + **BTC IS -93.81 catastrophic + BTC OOS +15.11 positive** (single-seed rotation signature, NOT defect per LM Master Phase 7.4 §3) + **SOL clean 16.4% / +19 IS / +8 OOS** (universe-expansion mechanism functional) + **wall-clock TBD min** — verdict-class cell NEGATIVE per F1 anti-direction + F-AXIS-MECHANISM #3 FAIL + F8 OOS breach; LM Master reframing PROMISING-INERT cites PSR jump as load-bearing basin-health signal but Critic conservative anchor maintains NEGATIVE label; **/018 advances under USER STRATEGIC PIVOT to per-cohort specialization methodology (LINK-only HIGH structural prior)**.

## What Worked

### SOL clean Model F dispatch — universe-expansion mechanism PASS

SOL contributed +19.04 IS PnL (14.88% share) and +8.19 OOS PnL (16.39% share) across 155 IS / 51 OOS trades with WR 40.0% IS / 37.3% OOS — exactly in LM Master Phase 4.5 §1 cautious band [5%, 40%]. Neither dead-feed (>5%) nor lottery (<40%). Model F dispatch through Model-A-sister template with R3 OOD only + R1/R2 disabled functioned cleanly through 39 monthly cells. SOL data pull + feature regen + universe wiring passed Critic Phase 6.0.

### ETH partial dilution CONFIRMED — LM Master 75% regime-lock REFUTED

ETH OOS trajectory across cycle-2+3:

| Iter | Axis | ETH OOS PnL | ETH OOS Share |
|---|---|---|---|
| /014 | labeling σ_t LABEL-only | -41.18 | — |
| /015 | labeling σ_t symmetric multi-seed | -23.29 | — |
| /016 | sample-weighting uniform | **-51.46** | +76% |
| **/017** | **universe +SOL** | **-28.07** | **-56%** |

/017's -28.07 is **2nd-best ETH OOS in cycle-2+3 window** — universe dilution at 16.4% SOL contribution genuinely **shifted the basin**, not just headline. ETH OOS share moved from /016's +76% (negative-share dominant) to /017's -56% (negative-share but diluted by 4 positive symbols: LINK +53.80, DOT +32.91, BTC +15.11, SOL +8.19). LM Master Phase 4.5 75% regime-lock framing **directionally correct but magnitude-wrong**: drag IS structural across 4 disjoint mechanisms, but dilution genuinely works at the basin level.

**Mental model update**: ETH drag is **structural-PARTIAL-dilutable**, NOT structural-locked.

### PSR_monthly_vs_0 jump 0.125 → 0.808 = load-bearing basin-health signal

| Iter | PSR_monthly_vs_0 (OOS) | Δ vs prior |
|---|---|---|
| /015 | 0.59 | — |
| /016 | **0.125** (collapse) | -0.47 |
| **/017** | **0.808** | **+0.68** (largest single-iter jump in cycle-3) |

PSR rewards **monthly-PnL distribution shape**, not point Sharpe. The +0.68 jump means OOS monthly distribution became **consistently positive** (4 positive symbols vs /016's all-negative). LM Master Phase 7.4 §3 endorsed as "single most important quantitative signal of /017 — exceeds all point-Sharpe signals in interpretive weight." Critic Phase 7.5 Rec #3 elevates PSR_monthly_vs_0 to **first-class basin-health metric** in cycle-3 catalog headline.

### Engineering report 6th-strike fix delivered

Phase 7 engineering report (`reports-v1/iteration_v1-017/engineering_report.md`) retroactively closes the missing-report gap from Phase 7.5 dispatch (Critic Finding #1). Permanent fix scope = orchestrator/skill-layer Phase 6 contract addition; not QR scope this iteration.

### LM Master mechanism-level track advanced (mixed)

- **CONFIRMED**: PSR_monthly_vs_0 is more sensitive than F1 Sharpe at universe-axis EXPLORATIONs (new structural finding — track PSR as primary basin-health signal forward)
- **CONFIRMED**: F-AXIS-MECHANISM #1 + #2 PASS clean (SOL share band, Model F dispatch)
- **REFUTED**: n_eff_per_cell band [11, 17] — corrected to native [8, 13] for v1 baseline-labels + abs_pnl-weighting + single-seed EXPLORATION

## What Failed

### F1 OOS anti-direction (Δ -0.0908; INERT-band but wrong sign)

OOS Sharpe drifted from baseline +0.6637 to /017 +0.5729 (Δ -0.0908). Within the INERT band [-0.20, +0.20] in magnitude but **anti-direction** to predicted +0.20 PROMISING. Universe-expansion as **denominator dilution** worked mechanically (PSR jump confirms basin reorganization) but did **NOT improve point Sharpe**. **Dilution worked; alone isn't sufficient for edge** (LM Master Phase 7.4 §1 catalog implication).

### F-AXIS-MECHANISM #3 FAIL — n_eff REFUTED 3rd consecutive time

LM Master Phase 4.5 predicted n_eff_per_cell ∈ [11, 17]; observed median 9 across all 5 cells (BTC=10, DOT=9, ETH=10, LINK=9, LTC=9, SOL=9). Reasoning was "Model F row-injection adds ~165 IS rows/month enriching loss-surface diversity"; **wrong** — PCA-substrate native rank stays bounded by Optuna trial budget (n_trials=18) × ENSEMBLE_SIZE (3), independent of row count.

**Corrected mental model** (LM Master Phase 7.4 §4): `n_eff_per_cell` in v1 has **stable native range ~9-13** at baseline-labels + abs_pnl-weighting + single-seed EXPLORATION. /014's 19 and /015's 3 were both outliers requiring specific axis-driver (label-shape baseline σ_t vs timeout-fallback dominance respectively). **Tighten band to [8, 13]** as cycle-3 EXPLORATION native band; outside-band only when axis structurally touches label-shape or weight-distribution. **Demote n_eff to INFORMATIONAL** for universe + feature-family axes.

### F8 OOS trade-count breach (301 > 284 upper-end by +17)

OOS trade count exceeded the mechanical band [F8 lower 130, F8 upper 284]. Universe expansion mechanically increased trade rate via Model F's 51 OOS contribution. Procedurally counts as F8 mechanical-band breach in verdict-cell determination, but interpretively not catastrophic — trade-rate floor preserved (well above 130 minimum).

### BTC catastrophic IS rotation — Model A trains badly on BTC at single-seed

BTC IS = -93.81 (rank-6, worst across cycle-2+3); BTC OOS = +15.11 (positive). Cross-period sign inversion is **single-seed=42 rotation signature, NOT defect** (LM Master Phase 7.4 §3 endorsed). Pattern: at single-seed=42 EXPLORATION, ~1 symbol per iteration drifts catastrophically IS-negative while another floats catastrophically IS-positive, with the identity ROTATING:

- /011: LINK catastrophic IS
- /014: ETH catastrophic IS (-99.73)
- /015: ETH catastrophic IS (sign-flipped via C1 FIX)
- /016: All 5 symbols IS-negative simultaneously
- **/017: BTC IS -93.81 + DOT IS +96.07 (new winner)**

v1 analog of v3's "single-seed=42 frozen-baseline" pattern but with universe-rotation overlay. Multi-seed CONFIRMATION at /027 should dissolve the rotation.

### LM Master Phase 4.5 ETH 75% regime-lock prediction MAGNITUDE wrong

Phase 4.5 staked 75% probability that ETH OOS share would dominate at ≥40% magnitude with PnL ≤-20%. Observed: ETH OOS -28.07 PnL with -56% share. Directionally correct (NEGATIVE-share zone) but magnitude wrong (sub-catastrophic, dilution partially worked). LM Master Phase 7.4 §2 self-correction verbatim: "my 75% regime-lock framing was directionally correct but magnitude-wrong. Drag IS structural (4 axes show ETH OOS negative); but dilution at 17% SOL contribution genuinely shifts BASIN, not just headline." Mental model updated to structural-PARTIAL-dilutable.

## Path Forward (from Critic Phase 7.5 — SUPERSEDED by USER STRATEGIC PIVOT)

Verbatim from `briefs-v1/iteration_v1-017/review.md` §"Path Forward":

> **NEW EXPLORATION methodology**: per-cohort specialization (1-3 symbols) with cohort-specialized features/config; CONFIRMATION at /027 bundles specialists for diversification edge.
>
> Candidates ordered by structural prior strength:
>
> 1. **LINK-only specialized** — strongest structural OOS edge across 7+ iterations (LINK OOS positive at /011, /012, /013, /014, /015, /016, /017). Test LINK-specific features (e.g., DeFi-correlation features, LINK-specific volatility scaling). Risk: single-symbol model can't diversify; if LINK OOS edge is regime-bound (post-2024 DeFi cycle), it may not generalize. **HIGH STRUCTURAL PRIOR.**
>
> 2. **ETH-only with regime-conditional gate** — ETH structural drag is the strongest negative pattern; ETH-specific gate addresses head-on. Mechanism: BTC-trend-conditional kill OR per-symbol drawdown brake stateless. Pre-committed at /017 brief Section 11.3 — explicit conditional fire. **MEDIUM STRUCTURAL PRIOR.**
>
> 3. **BTC-only with specialized config** — BTC IS at /017 was -93.81 (catastrophic rotation); BTC OOS +15.11 (positive). Pooled Model A (BTC+ETH) trains badly on BTC. Separating BTC may reveal BTC-specific edge. Risk: BTC-only model may underperform vs BTC-in-pool. **MEDIUM STRUCTURAL PRIOR.**

LM Master Phase 7.4 staked +XRP at 65% MEDIUM-HIGH for /018; this is now **SUPERSEDED by user strategic pivot 2026-05-26**.

## 5 LESSONS for v1 Cycle-3 Catalog

### LESSON #1: ETH STRUCTURAL DRAG IS PARTIAL-DILUTABLE (NOT regime-locked)

ETH OOS catastrophic across 4 disjoint mechanism layers (/014 labeling σ_t LABEL-only / /015 labeling symmetric multi-seed / /016 sample-weighting uniform / /017 universe expansion):

| Iter | Axis | ETH OOS PnL |
|---|---|---|
| /014 | labeling | -41.18 |
| /015 | labeling C1 FIX multi-seed | -23.29 |
| /016 | sample-weighting | -51.46 |
| **/017** | **universe +SOL** | **-28.07** |

**/017 dilution proves drag is structural-PARTIAL-dilutable**: 2nd-best ETH OOS in cycle-2+3 window; ETH share moved from +76% to -56%; basin reorganization confirmed.

**Codified rule**: ETH structural drag is dilution-responsive at universe layer. Future EXPLORATIONs touching ETH must pre-register either (a) dilution mechanism (expand universe further) OR (b) ETH-specific kill switch (regime-conditional gate). LM Master per-symbol regime-lock prediction confidence DOWNGRADED from HIGH (75%) to MEDIUM (50%) for ETH-specifics; mechanism-level prediction confidence MAINTAINED.

### LESSON #2: PSR_monthly_vs_0 IS A FIRST-CLASS BASIN-HEALTH SIGNAL

PSR_monthly_vs_0 OOS jump 0.125 → 0.808 (+0.68 = largest single-iter jump in cycle-3) was the **single most sensitive metric** at /017 — exceeded all point-Sharpe signals in interpretive weight.

PSR rewards monthly-PnL distribution shape (consistency of positive monthly Sharpe), not point Sharpe. The +0.68 jump means OOS monthly distribution became **consistently positive** (4 positive symbols vs /016's all-negative). At universe-axis EXPLORATIONs in particular, **PSR detects basin reorganization that point Sharpe misses**.

**Codified rule**: cycle-3+ catalog headlines and verdict-cell evaluation include PSR_monthly_vs_0 as primary basin-health metric alongside point Sharpe. Future briefs Section 8 falsifier matrix must include PSR_monthly_vs_0 prediction band. Critic Phase 7.5 Check 3 elevates PSR from informational to primary for universe-axis or feature-family EXPLORATIONs.

### LESSON #3: SINGLE-SEED=42 ROTATION SIGNATURE — PER-SYMBOL IS CATASTROPHIC IS NOT DEFECT

Pattern across cycle-2+3 at single-seed=42 EXPLORATION:
- ~1 symbol per iteration drifts catastrophically IS-negative
- Another floats catastrophically IS-positive
- The **identity rotates** across iterations

Examples: /011 LINK / /014 ETH / /015 ETH / /016 all-5 / **/017 BTC IS -93.81 + DOT IS +96.07**.

v1 analog of v3's "single-seed=42 frozen-baseline" pattern but with universe-rotation overlay.

**Codified rule**: Critic Check 4 (per-symbol attribution) does NOT BLOCK on per-symbol IS catastrophic alone at single-seed EXPLORATION. IS catastrophic + OOS positive cross-period sign inversion is **expected single-seed rotation signature**. Multi-seed CONFIRMATION at /027 dissolves the rotation. Per-symbol IS catastrophic at multi-seed CONFIRMATION IS a defect signal; at single-seed EXPLORATION it is noise.

### LESSON #4: n_eff_per_cell NATIVE BAND IS [8, 13] AT BASELINE — INFORMATIONAL FOR UNIVERSE AXES

n_eff_per_cell track across cycle-2+3:

| Iter | Labels | Weights | n_eff_per_cell_median |
|---|---|---|---|
| /014 | σ_t LABEL-only (1.70% labels) | abs(labeled_pnl) | 19 (OUTLIER) |
| /015 | σ_t symmetric (7.82% labels) | abs(labeled_pnl) | 3 (OUTLIER — timeout-fallback) |
| /016 | baseline ATR | uniform [1, 1] | 9 (weight-distribution driver) |
| /017 | baseline ATR | abs_pnl [1, 10] | **9** (universe expansion, native band) |

**Corrected mental model** (LM Master Phase 7.4 §4): native band [8, 13] at baseline-labels + abs_pnl-weighting + single-seed EXPLORATION. /014's 19 and /015's 3 are outliers requiring specific axis-driver (label-shape baseline σ_t vs timeout-fallback dominance respectively).

**Codified rule**: n_eff_per_cell forward-binding for /018+:
- **Primary F-AXIS-MECHANISM sub-check** for label-shape or weight-distribution axes (band depends on axis specifics)
- **Demoted to INFORMATIONAL** for universe + feature-family + risk-primitive axes (native [8, 13] expected)
- Outside-band ONLY when axis structurally touches label-shape or weight-distribution

### LESSON #5: USER STRATEGIC PIVOT 2026-05-26 — PER-COHORT SPECIALIZATION METHODOLOGY

**User directive (verbatim, at /017 closeout)**: *"Use the explorations to narrow down approaches like individual symbols, pooled symbols (2 or 3) with specific features, configurations. Then use the confirmation to combine those small explorations and take an edge in the diversification."*

Codified into `~/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v1_per_cohort_exploration_strategy.md`.

**Old methodology (cycle-3 /016, /017)**: global axes on pooled universe (sample-weighting, universe expansion).

**New methodology (cycle-3 /018+ onwards)**:
- **EXPLORATIONs**: each tests a **per-cohort specialization** (1-3 symbols with cohort-specific features/config)
- **CONFIRMATION at /027**: bundles PROMISING specialists into a multi-seed portfolio for **diversification edge**

**Justification chain**:
1. Cycle-2 NO-MERGE (10 iterations, 7 axis families) — global-axis saturated
2. Cycle-3 /016 NEGATIVE + /017 PROMISING-INERT — pooled-universe global axes saturated at single-axis EXPLORATION budget
3. LINK structural OOS positive across /011-/017 (7+ iterations) — under-exploited by pooled training
4. ETH structural OOS negative across same iterations — pollutes pooled BTC signal in Model A
5. v3 precedent: per-symbol architecture (V3-BCH, V3-LDO, V3-TRX) found edge there

**Caveats**:
- Single-cohort EXPLORATION verdicts are intrinsically cohort-bound (PROMISING per-cohort doesn't imply PROMISING portfolio)
- Cohort rotation rule: prior 5 EXPLORATIONs by COHORT + SPECIALIZATION pairing
- Each EXPLORATION proposes ONE specialization dimension (features OR atr OR labeling OR risk-gate)
- CONFIRMATION bundles only PROMISING specialists; re-evaluate at multi-seed

**Codified rule**: /018+ briefs Section 0.6 must declare COHORT + SPECIALIZATION (not global axis) AND reference user 2026-05-26 directive. Phase 5.5 gate enforces cohort-specialization declaration.

## Cycle-3 Cadence Status (after /017)

- Cycle-3 EXPLORATION count: **2 of 10**
- CONFIRMATION earliest: /027 (assuming sequential EXPLORATIONs from /018 to /026)
- Edge ingredients merged this cycle: **0**
- Verdict distribution cycle-3 so far: 1 EXPLORATION-NEGATIVE catastrophic (/016) + 1 EXPLORATION-NEGATIVE anti-direction-INERT (/017)
- BASELINE_V1.md unchanged at `v0.v1-baseline-corrected` (`f8bc12c`)
- **Methodology pivot at /018+**: global-axis EXPLORATIONs → per-cohort specialization EXPLORATIONs

## Axis Rotation Status (v1-only)

- **This iter's family**: `universe` (UNUSED in cycle-3; UNUSED since /006 cycle-2)
- **Prior 5 EXPLORATION families**: `methodology-substrate-test` (/012), `methodology-substrate-test` (/013), `labeling` (/014), `labeling` CONFIRMATION (/015), `sample-weighting` (/016)
- **Rotation honored**: YES — `universe` is in NONE of the prior 5 families
- **Updated prior 5 going into /018**: `methodology-substrate-test` (/013), `labeling` (/014), `labeling` (/015), `sample-weighting` (/016), `universe` (/017)
- **/018 axis-family**: per USER STRATEGIC PIVOT, cohort-specialization methodology REPLACES global-axis rotation for cycle-3 #3 onwards. Axis family declaration in /018 brief Section 0.6 uses **cohort identifier** (e.g., "LINK-cohort-features") rather than the 9 global families. Rotation discipline applies to cohort-specialization PAIRINGS in prior 5.

## Next Iteration Ideas (cycle-3 third EXPLORATION = /018)

Per USER STRATEGIC PIVOT + Critic Phase 7.5 Path Forward, ranked by structural prior strength:

1. **LINK-only specialized** (HIGH structural prior) — LINK OOS positive across /011-/017 (7+ consecutive iterations); under-exploited by pooled training. Specialization candidates (one-axis):
   - LINK-specific features (DeFi-correlation features, LINK-specific volatility scaling, LINK-on-chain feeds)
   - LINK-specific atr_tp/atr_sl (currently shared with Model C — likely under-tuned for LINK's profile)
   - LINK-specific labeling thresholds (per-symbol calibration vs portfolio-median)
   - LINK-specific risk-gate config (R3 cutoff tuning for LINK's regime profile)

   Risks: (a) single-symbol model can't diversify intrinsically; (b) if LINK OOS edge is regime-bound (post-2024 DeFi cycle), it may not generalize. Test via CONFIRMATION /027 bundling.

   **PRIMARY** per Critic Path Forward #1 + USER STRATEGIC PIVOT.

2. **ETH-only with regime-conditional gate** (MEDIUM structural prior) — ETH structural drag is the strongest negative pattern across 4 axes. Specialization candidates:
   - BTC-trend-conditional kill switch (regime-bound gate; not threshold-tuning)
   - Per-symbol drawdown brake (stateless; v3/020 proportional-cap closed — must be loss-stop semantics)
   - ETH-only regime-conditional ATR-bandwidth gate

   Pre-committed at /017 brief Section 11.3. SECONDARY if /018 LINK-only NEGATIVE.

3. **BTC-only with specialized config** (MEDIUM structural prior) — BTC IS catastrophic rotation at /017 (-93.81) + BTC OOS positive (+15.11). Pooled Model A (BTC+ETH) trains badly on BTC. Separating BTC may reveal BTC-specific edge. Risks: BTC-only model may underperform vs BTC-in-pool. TERTIARY.

All three from per-cohort specialization methodology under USER STRATEGIC PIVOT. Cycle-3 third EXPLORATION QR EDA-justifies LINK-only specialization with one-axis specialization dimension under 2h wall-clock cap.

## Files & Commits on Branch

- Branch: `iteration-v1/017` from `iter-v1/016` closeout (tag `v0.v1-016`)
- HEAD at Phase 5.5 PASS: `5a1883c`
- HEAD at QE implementation: `887d115` (+SOL fetch) → axis isolation fix `5fffe8a`
- HEAD at Critic Phase 6.0 PASS: `e4aead6`
- HEAD at backtest completion (artifacts in `reports-v1/iteration_v1-017/`)
- HEAD at LM Master Phase 7.4 post-mortem: `f0dccd3`
- HEAD at Critic Phase 7.5 review (EXPLORATION-NEGATIVE anti-direction-INERT): `5b3515e`
- HEAD at Phase 7 evaluation + engineering report (6th-strike fix): `3a6fc50`
- HEAD at Phase 8 closeout (THIS COMMIT): TBD

Key commits in /017:
- `7294b58` — LM Master Phase 4.5 pre-design advisory
- `a145ee0` — brief Section 3.4 LM Master Phase 4.5 responses
- `5a1883c` — Phase 5.5 gate PASS
- `887d115` — feat: SOL fetch + feature regen
- `5fffe8a` — fix: R5 vol-target defaults OFF in cycle-3+ (axis isolation)
- `e4aead6` — Critic Phase 6.0 PASS with R5 default fix
- (Backtest dispatched; comparison.csv + reports artifacts in `reports-v1/iteration_v1-017/`)
- `f0dccd3` — LM Master Phase 7.4 post-mortem (FIRST cycle-3 PROMISING-INERT)
- `5b3515e` — Phase 7.5 Critic review — EXPLORATION-NEGATIVE + USER STRATEGIC PIVOT
- `3a6fc50` — Phase 7 evaluation + engineering report (6th-strike fix)
- (THIS COMMIT) — Phase 8 diary + catalog + cycle-3 strategy pivot

**Trunk merge**: NONE. EXPLORATION-NEGATIVE anti-direction-INERT never updates BASELINE_V1.md. Universe-expansion axis remains **structural-cell candidate** (6-sym + SOL substrate) for /027 CONFIRMATION bundling, NOT edge ingredient.

**Tag**: `v0.v1-017` (applied after this Phase 8 closeout commit).
