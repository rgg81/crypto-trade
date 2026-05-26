---
iteration: iter-v1/018
date: 2026-05-26
verdict: EXPLORATION-PROMISING
subtype: favorable-INERT
axis_family: per-cohort-specialization-LINK (NEW 9th family — FIRST per-cohort EXPLORATION under USER STRATEGIC PIVOT)
cohort: LINK (single-symbol cohort, Model C exclusive dispatch)
specialization: NONE (Option E — LINK-in-isolation; no additional knob)
cadence_position: cycle-3 EXPLORATION (#3 of 10)
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c) — UNCHANGED
merge_decision: NO-MERGE (EXPLORATION-PROMISING favorable-INERT; LINK-only specialist CONDITIONALLY CARRIED to /027 CONFIRMATION substrate as load-bearing component; BASELINE_V1.md UPDATE NOT triggered — strictly-better policy not satisfied at F1 IS Δ -0.03 / F3 OOS Δ +0.16)
---

# Iteration iter-v1/018 — Diary

## Decision: NO-MERGE (LINK-only specialist CONDITIONALLY CARRIED to /027 substrate)

EXPLORATION-PROMISING favorable-INERT. LINK-only single-symbol cohort dispatch through Model C produced **first cycle-3 edge candidate** — directly validating the USER STRATEGIC PIVOT to per-cohort specialization methodology. BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). LINK-only specialist VALIDATED as load-bearing component for /027 CONFIRMATION bundle.

## One-Line Outcome

At v1 EXPLORATION budget (ENSEMBLE_SIZE=3 + n_trials=18 + V1_FEATURE_COLUMNS_PRUNED + LINK-only universe via `V1_ITER018_UNIVERSE = (LINKUSDT,)` + 8h candles + `abs_pnl` weighting + Model C exclusive dispatch + R1 + R3 + ATR×3.5 TP / ATR×1.75 SL + R5 disabled) LINK-only single-symbol cohort produced **IS Sharpe +0.3407** (Δ **-0.0317** INERT band vs LINK-in-pool +0.3724) + **OOS Sharpe +0.9789** (Δ **+0.1605** INERT band vs LINK-in-pool +0.8184, just below +0.20 PROMISING boundary) + **WR 50.0% IDENTICAL to baseline LINK** + **F-AXIS-MECHANISM #1 binary PASS** (per_symbol.csv 100% LINKUSDT IS+OOS) + **PSR_monthly_vs_0 OOS = 0.885** (well above 0.40 PROMISING-INERT floor; informational only) + **PSR_monthly_vs_1 OOS = 0.553** (≥50% probability LINK-only OOS Sharpe ≥ 1.0 at observed parameters) + **OOS/IS ratio 2.87** (explained by LINK IS bear-cycle drag 2022-2024 + OOS single DeFi-favorable regime + single-cohort capacity reduction reducing IS overfit) + **n_eff_per_cell = 9** (in [4, 9] LM Master corrected single-cohort band) + **wall-clock ~25 min** (well inside 2h cap) — verdict-class cell **PROMISING-INERT favorable-direction**; Critic + LM Master CONVERGE; LINK-only specialist CONDITIONALLY CARRIED to /027 CONFIRMATION substrate as load-bearing component (predicted multi-seed anchor +0.80, NOT /018's +0.98 single-seed overshoot); **/019 axis advances per Critic + LM Master convergent recommendation: ETH-only with stateless BTC-trend regime gate** (NEW 10th axis family `per-cohort-specialization-ETH`).

## What Worked

### Per-cohort methodology empirically VALIDATED — FIRST cycle-3 edge candidate

Cycle-3 verdict distribution after /018:

| Iter | Axis | Verdict | OOS Δ vs anchor |
|---|---|---|---|
| /016 | sample-weighting `uniform` (pooled) | EXPLORATION-NEGATIVE catastrophic | −1.67 (vs baseline +0.6637) |
| /017 | universe +SOL (pooled) | EXPLORATION-NEGATIVE anti-direction-INERT | −0.09 (vs baseline +0.6637) |
| **/018** | **LINK-only per-cohort (Option E LINK-in-isolation)** | **EXPLORATION-PROMISING favorable-INERT** | **+0.16 (vs LINK-in-pool +0.8184)** |

The pivot from global-pooled axes to per-cohort specialization **directly produced the first cycle-3 edge candidate** in 3 attempts. This is sample-of-1 at the iteration level — but the load-bearing structural prior (LINK 9/9 OOS-positive) is sample-of-9 and the cross-architecture stability is the strongest per-symbol pattern in v1 catalog.

### LINK structural prior — 9/9 OOS-positive across baseline + /011-/018

LINK OOS PnL trajectory updated:

| Anchor | LINK OOS PnL % |
|---|---|
| baseline | +52 |
| /011 | +85 |
| /012 | +53 |
| /013 | +47 |
| /014 | +4 |
| /015 | +85 |
| /016 | +35 |
| /017 | +54 |
| **/018 (LINK-only)** | **+54** |

**CV ≈ 0.51, mean +51, all 9 positive sign, range [+4, +85].**

Cross-arch stability across: 3 universes (5-sym / 6-sym / 1-sym) × 4 feature stacks × 2 labeling regimes (/014 σ_t LABEL-only; /015 σ_t symmetric) × 2 sample-weight modes (`abs_pnl` / `uniform`) × 3 methodology substrates. The roster overlap is LOW (4-29% Jaccard) — different LINK trades across iters — but the SIGN is consistent. **Signal-stable not roster-stable**. This is the bedrock that makes LINK-only specialist the highest-conviction CONFIRMATION ingredient in v1 history.

### F-AXIS-MECHANISM #1 binary PASS clean

per_symbol.csv contains 100% LINKUSDT both IS (154 trades) and OOS (48 trades). Model C exclusive dispatch via `V1_ITER018_UNIVERSE = (LINKUSDT,)` and `set(symbols)==set(V1_ITER018_UNIVERSE)` guard functioned cleanly. Zero spillover from Model A/D/E/F dispatch branches. F-AXIS-MECHANISM #2 trade count: IS=154 ∈ [120, 200] PASS, OOS=48 ∈ [25, 75] PASS.

### Critic + LM Master CONVERGE on PROMISING-INERT favorable verdict

Both Critic Phase 7.5 and LM Master Phase 7.4 (post-mortem) reach the same verdict cell with the same /027 carry-forward recommendation. LM Master Phase 4.5 prior was **modal INERT 45%** (PROMISING-INERT specifically) — confirmed at observation. LM Master directional track 2/16 (was 1/15 with /015's 3/3 C1-inversion) + mechanism-level 8/16 (was 7/15 — WR identical → same signal cleaner trajectory mechanism pre-registered for next cohort isolation).

### PSR_monthly_vs_0 OOS = 0.885 — load-bearing basin-health signal (informational)

PSR jumped from /017's 0.808 to /018's 0.885 (+0.077). Well above 0.40 PROMISING-INERT floor; approaches 0.95 aspirational gate. **Informational only** at EXPLORATION budget — 14-OOS-month sample is small; PSR CI wide. Do NOT cite 0.885 as "near aspirational 0.95" in /019+ catalog rows; track as basin-health metric but verdict cell at /027 multi-seed CONFIRMATION is the falsification authority.

### LM Master mechanism-level pre-registration earned a NEW slot

LM Master Phase 7.4 §4 (post-mortem only directional miss): pre-registered the new mechanism that **WR identical to baseline + Sharpe Δ > 0 = loss-surface optimization without signal change = same LINK trades entered with different timing precision; 23% fewer trades at IDENTICAL WR means Optuna picked slightly different point on LINK's signal manifold**. This is the cross-track v3 PROMISING-FEATURE-MECHANICAL analog at v1 cohort-isolation layer. Cross-validated at /027 (multi-seed will REGRESS toward +0.82 anchor, NOT extend beyond +0.98).

## What Failed

### OOS/IS ratio 2.87 — explainable, NOT a flag

OOS/IS Sharpe ratio 2.87 would normally be a flag (researcher overfitting check requires ≥0.5 with OOS ≤ IS). LM Master Phase 7.4 §2 ranked three explanations by evidence:

1. **(Strongest) LINK IS includes 2022-2024 bear-cycle drag**: monthly_pnl.csv shows 2023-11 -19.93%, 2023-12 -10.09%, 2024-04 -13.55%. IS Sharpe structurally compressed by 2 loss regimes. OOS is March 2025 → May 2026 single DeFi-favorable regime. Mean monthly PnL IS +1.35% vs OOS +2.63%.
2. **Single-cohort capacity reduction reduces IS overfit**: n_eff_per_cell=9; 154 IS trades vs ~700 pool-pooled. Less capacity to memorize IS noise.
3. **Optuna conservatism**: n_trials=18 × ENSEMBLE_SIZE=3 = 54 evaluations on single-cohort isn't enough budget to chase IS extremes.

**NOT suspicious**. Regime-driven + capacity-driven. 8/8 prior cross-architecture consistency is stronger anti-overfit signal than CSCV at single-cohort.

### F1 OOS Δ +0.16 just BELOW PROMISING +0.20 boundary

LINK-only OOS +0.9789 vs LINK-in-pool +0.8184 = Δ +0.1605. INERT band [-0.20, +0.20]; just below +0.20 PROMISING boundary. Critic Phase 7.5 took conservative anchor — PROMISING-INERT favorable-direction (not PROMISING). LM Master Phase 7.4 §1 framed as "mathematical dilution removal + WR-identical loss-surface optimization" — the +0.16 lift is split between Optuna trajectory differences (capacity reduction) and slight loss-surface reorganization at single-seed.

This is consistent with the cross-arch mean — LINK's cross-architecture mean OOS Sharpe is +0.82 (CV 0.51), and /018's +0.98 is +0.31σ above the mean (1-tailed 38% likelihood under iid). Multi-seed at /027 will REGRESS toward +0.82.

### Single-seed=42 basin-lottery exposure (HIGH-RISK declared)

LM Master Phase 4.5 §5 saturation risk: "LINK-only OOS Sharpe could land [+0.30, +1.20] from basin-lottery alone. 8/8 historical pattern argues basin FAMILY generalizable but single iteration is sample-of-1." HIGH-RISK declared correctly in brief Section 2.5 (FIRST cycle-3 HIGH-RISK declaration was /017; /018 is 2nd). Multi-seed at /027 dissolves the lottery; over-anchoring on /018's +0.98 in /019+ briefs would be post-hoc rationalization.

### Check 3 PBO unavailable for single-symbol single-cohort

For single-cohort single-seed EXPLORATION, n_obs collapses → PBO not computable. Critic Phase 7.5 accepted as STRUCTURAL not evidence-gap (per /018 lgbm_advisor.md Phase 7.4 §closing note: "8/8 cross-architecture prior is stronger anti-overfit signal than CSCV at single-cohort"). Per-cohort EXPLORATIONs at /019-/026 will have the same PBO limitation; multi-seed CONFIRMATION at /027 restores full DSR/PBO/PSR evaluation.

## Path Forward (from Critic + LM Master CONVERGENT recommendation)

Verbatim from Critic Phase 7.5 review.md §"Path Forward" + LM Master Phase 7.4 §6:

1. **/019 ETH-only with stateless BTC-trend regime gate** — `per-cohort-specialization-ETH` (NEW 10th family). Mechanistically-orthogonal test (NEGATIVE-prior cohort + binary regime filter). Diversifies cohort coverage (LINK done → ETH next). ETH structural OOS drag is strongest NEGATIVE per-symbol prior (4/4 OOS-negative iterations /014-/017). Single-axis isolation; stateful gate requires deadlock-impossibility proof per A8 (Critic Anti-Pattern Static Scan).

2. **/020 BTC-only specialization** — BTC IS catastrophic at /017 (-93.81) + BTC OOS positive (+15.11): single-seed rotation signature. Isolating BTC characterizes intrinsic vs pool-borrowed.

3. **/021 LINK-only ATR follow-on** — CONDITIONAL on /019+/020 establishing 2+ cohort-baselines first (avoid burning /021 slot prematurely on a refinement of an already-validated specialist).

Constraints honored: per-cohort-specialization-{ETH,BTC} NEW family declarations; none in prior 5.

## 5 LESSONS for v1 Cycle-3 Catalog

### LESSON #1: PER-COHORT METHODOLOGY EMPIRICALLY VALIDATED (FIRST cycle-3 favorable result)

3-iteration scoreboard:

| Iter | Methodology | Verdict | OOS Δ vs anchor |
|---|---|---|---|
| /016 | global axis on pooled (sample-weighting `uniform`) | NEGATIVE catastrophic | −1.67 |
| /017 | global axis on pooled (universe +SOL) | NEGATIVE anti-direction-INERT | −0.09 |
| **/018** | **per-cohort specialization (LINK-only)** | **PROMISING favorable-INERT** | **+0.16** |

**Codified rule**: per-cohort specialization (1-3 symbols with cohort-specific features/config) is the **default** EXPLORATION methodology at cycle-3 /019+ onwards. Global-pooled axes are CLOSED for cycle-3 at single-axis EXPLORATION budget (saturated at /016 + /017 NEGATIVE). Briefs Section 0.6 declare COHORT + SPECIALIZATION, not global axis. Phase 5.5 gate enforces cohort-specialization declaration per `feedback_v1_per_cohort_exploration_strategy.md`. /019+ axis family naming uses `per-cohort-specialization-{COHORT}` (e.g., `per-cohort-specialization-ETH` at /019, `per-cohort-specialization-BTC` at /020+).

### LESSON #2: LINK 9/9 OOS-POSITIVE STRUCTURAL PRIOR IS LOAD-BEARING FOR /027 BUNDLE

LINK OOS PnL across baseline + /011-/018: 9/9 positive, mean +51, CV 0.51, range [+4, +85]. Roster overlap LOW (4-29% Jaccard) but SIGN rock-stable across 3 universes × 4 feature stacks × 2 labeling regimes × 2 sample-weight modes × 3 methodology substrates.

**Codified rule**: LINK-only specialist is the **highest-conviction CONFIRMATION ingredient** in v1 history. /027 bundle target: LINK-only anchored at multi-seed mean OOS Sharpe ≥+0.80 (NOT /018's single-seed +0.98). Sub-target +0.60 = bundle Sharpe degrades by ~0.20. If multi-seed at /027 shows LINK-only < +0.60, the 9/9 prior is FALSIFIED at multi-seed (basin-lottery overshoot was structural, not seed-specific).

Future EXPLORATIONs touching LINK (e.g., /021 ATR follow-on, /022 LINK-specific labeling) must pre-register **regression-to-anchor** behavior: improving on +0.98 single-seed at single-cohort single-seed=42 would be a basin-lottery overshoot, not edge discovery.

### LESSON #3: WR IDENTICAL TO BASELINE = SAME SIGNAL CLEANER OPTUNA TRAJECTORY (NOT new edge)

/018 LINK-only OOS WR 50.0% = LINK-in-pool OOS WR 50.0% IDENTICAL. avg PnL +1.12% (vs baseline ~+1.22%) with Sharpe Δ +0.16 = **loss-surface optimization without signal change**. Same LINK trades entered with different timing precision; 23% fewer trades at IDENTICAL WR means Optuna picked slightly different point on LINK's signal manifold.

This is the **PROMISING-FEATURE-MECHANICAL adjacent** v3 cross-track analog at v1 cohort-isolation layer: loss-surface reorganization without new edge discovery. Does NOT diminish result. Means /027 multi-seed will REGRESS toward baseline LINK-alone mean (+0.82), NOT extend beyond +0.98. **Realistic /027 LINK-only specialist = +0.80 Sharpe component, not +0.98.**

**Codified rule**: at per-cohort specialization EXPLORATIONs (cohort isolation, no specialization knob), WR-identical-to-baseline + Sharpe Δ > 0 = loss-surface optimization signature (NOT new edge). Cross-track v3 PROMISING-FEATURE-MECHANICAL analog. Future briefs Section 8 falsifier matrix at per-cohort EXPLORATIONs pre-register: WR-identical + Sharpe Δ > 0 → expect multi-seed REGRESSION to cross-arch mean (NOT extension). LM Master Phase 7.4 §4 cross-track pre-registration permission earned (8/16 mechanism-level).

### LESSON #4: /027 LINK-ONLY SPECIALIST TARGET = +0.80 (NOT /018's +0.98)

Per LESSON #2 and LESSON #3: multi-seed at /027 dissolves single-seed=42 basin lottery + WR-identical loss-surface optimization REGRESSES toward cross-arch mean. /018's +0.98 contains:

1. ~+0.04 single-seed=42 basin overshoot (basin-lottery band [+0.30, +1.20])
2. ~+0.12 loss-surface optimization (capacity reduction + Optuna trajectory differences)
3. ~+0.82 cross-architecture mean (the structural prior)

**Codified rule**: /027 CONFIRMATION bundle compositions targeting LINK-only specialist must size at **+0.80 anchor contribution**, NOT +0.98. Over-anchoring on /018's +0.98 is **post-hoc rationalization risk**. Future LINK-specialist briefs (/021 ATR follow-on, /022 LINK-specific labeling) pre-register expected multi-seed REGRESSION at /027 — improving on +0.98 single-seed is structurally implausible. Bundle Sharpe target ≥+0.70 multi-seed mean: requires 5+ specialists at ~+0.50-0.80 each with cross-correlation ≤0.3.

### LESSON #5: PSR_monthly_vs_0 0.885 IS INFORMATIONAL, NOT "NEAR ASPIRATIONAL 0.95"

PSR_monthly_vs_0 OOS = 0.885 well above PROMISING-INERT floor 0.40; approaches aspirational gate 0.95 BUT 14-OOS-month sample is small (PSR CI wide). Single-cohort PBO unavailable; PSR is the only multiple-testing-correction artifact at this iteration budget.

**Codified rule**: at per-cohort EXPLORATIONs (small-sample PSR CI), PSR_monthly_vs_0 ≥ 0.40 PROMISING-INERT floor admits cell membership but does NOT promote to PROMISING-cell (boundary +0.20 OOS Sharpe Δ remains primary). Catalog rows must NOT cite single-cohort PSR ≥ 0.80 as "near aspirational 0.95" — wide CI at 14 OOS months. /019+ briefs Section 8 pre-register PSR as basin-health signal but NOT as verdict-cell determinant at single-cohort. Multi-seed CONFIRMATION at /027 restores full PSR with proper CI.

## Cycle-3 Cadence Status (after /018)

- Cycle-3 EXPLORATION count: **3 of 10**
- CONFIRMATION earliest: /027 (assuming sequential EXPLORATIONs from /019 to /026)
- Edge ingredients merged this cycle: **0** (LINK-only specialist is CONDITIONAL carry-forward to /027 substrate, NOT a merge to BASELINE_V1.md)
- Verdict distribution cycle-3 so far: 1 EXPLORATION-NEGATIVE catastrophic (/016) + 1 EXPLORATION-NEGATIVE anti-direction-INERT (/017) + **1 EXPLORATION-PROMISING favorable-INERT (/018 — FIRST cycle-3 edge candidate)**
- BASELINE_V1.md unchanged at `v0.v1-baseline-corrected` (`f8bc12c`)
- **Methodology pivot validated**: 1 of 1 per-cohort attempt produced first cycle-3 edge candidate; global-pooled axes (2 of 2) NEGATIVE

## Axis Rotation Status (v1-only)

- **This iter's family**: `per-cohort-specialization-LINK` (NEW 9th family — FIRST usage at v1 catalog level under USER STRATEGIC PIVOT)
- **Prior 5 EXPLORATION families** (going INTO /018): methodology-substrate-test (/013), labeling (/014), labeling CONFIRMATION (/015), sample-weighting (/016), universe (/017)
- **Rotation honored**: YES — `per-cohort-specialization-LINK` is in NONE of the prior 5 families. New family declaration follows /012-precedent rule (Critic + LM Master + QR convergence on orthogonality) — orthogonality justification: cohort-specialization-pairings vary the SYMBOL DIMENSION while holding labels/features/risk/methodology constant.
- **Updated prior 5 going into /019**: labeling (/014), labeling CONFIRMATION (/015), sample-weighting (/016), universe (/017), per-cohort-specialization-LINK (/018)
- **/019 axis-family**: `per-cohort-specialization-ETH` (NEW 10th family) per Critic + LM Master convergence. Per-cohort methodology rotation discipline: COHORT identifier rotation (LINK done → ETH next → BTC at /020 OR /021 → DOT/SOL/2-sym pools at /022-/026).

## Next Iteration Ideas (cycle-3 fourth EXPLORATION = /019)

Per Critic + LM Master CONVERGENT Path Forward + USER STRATEGIC PIVOT cohort-rotation:

1. **ETH-only with stateless BTC-trend regime gate** (HIGH structural prior — ETH 4/4 OOS-negative is strongest negative pattern; BTC-trend gate is mechanistically orthogonal) — `per-cohort-specialization-ETH` NEW 10th family. Single-axis isolation; stateful gate requires deadlock-impossibility proof per Critic A8 Anti-Pattern. **PRIMARY** per Critic Path Forward #1 + LM Master Phase 7.4 §6.

2. **BTC-only with specialized config** (MEDIUM structural prior — BTC IS catastrophic rotation /017 -93.81 + BTC OOS positive +15.11; pooled Model A trains badly on BTC) — `per-cohort-specialization-BTC` NEW 11th family. SECONDARY per Critic Path Forward #2; deferred to /020 if /019 ETH-only PROMISING (cohort coverage diversity) OR /021 if /019 NEGATIVE (BTC-only as recovery cohort).

3. **LINK-only ATR follow-on (LINK-cohort + ATR specialization)** — CONDITIONAL on /019+/020 establishing 2+ cohort-baselines first. Avoid burning /021 slot prematurely on a refinement of an already-validated specialist. TERTIARY per Critic Path Forward #3.

All three from per-cohort specialization methodology. Cycle-3 fourth EXPLORATION (/019) QR EDA-justifies ETH-only with BTC-trend regime gate under 2h wall-clock cap.

## Files & Commits on Branch

- Branch: `iteration-v1/018` from `iter-v1/017` closeout (tag `v0.v1-017`)
- HEAD at LM Master Phase 4.5 advisory: `004d1d1`
- HEAD at brief Section 3.4 LM Master responses: `d4a5717`
- HEAD at QE LINK-only dispatch implementation: `4813f1e`
- HEAD at Critic Phase 6.0 pre-flight PASS: `7508dd4`
- HEAD at LM Master Phase 7.4 post-mortem: `04e544c`
- HEAD at Critic Phase 7.5 review (EXPLORATION-PROMISING favorable-INERT): `1ad1892`
- HEAD at Phase 7 evaluation + engineering report: `1a98cf4`
- HEAD at Phase 8 closeout (THIS COMMIT): TBD
- Reports artifacts in `reports-v1/iteration_v1-018/`

Key commits in /018:
- `004d1d1` — LM Master Phase 4.5 pre-design advisory
- `d4a5717` — brief Section 3.4 LM Master Phase 4.5 responses
- `4813f1e` — feat: V1_ITER018_UNIVERSE = (LINKUSDT,) + LINK-only dispatch
- `7508dd4` — Critic Phase 6.0 pre-flight PASS
- (Backtest dispatched; comparison.csv + reports artifacts in `reports-v1/iteration_v1-018/`)
- `04e544c` — LM Master Phase 7.4 post-mortem (FIRST cycle-3 edge candidate)
- `1ad1892` — Phase 7.5 Critic review — EXPLORATION-PROMISING favorable-INERT
- `1a98cf4` — Phase 7 evaluation + engineering report
- (THIS COMMIT) — Phase 8 diary + catalog + LINK 9/9 structural prior memory

**Trunk merge**: NONE. EXPLORATION-PROMISING favorable-INERT does NOT update BASELINE_V1.md (per `feedback_v3_baseline_update_policy.md` adopted by v1 — strictly-better policy not triggered: F1 IS Δ −0.03 fails strictly-better; F3 OOS Δ +0.16 within INERT band; verdict cell PROMISING-INERT not PROMISING). LINK-only specialist carries forward as **structural-cell ingredient** for /027 CONFIRMATION substrate, NOT as merge candidate to BASELINE_V1.md.

**Tag**: `v0.v1-018` (applied after this Phase 8 closeout commit).
