# iter-v1/084 — Phase 8 Diary (CRVUSDT SPECIALIST)

**Date**: 2026-06-09
**Track**: v1 (refactored)
**Branch**: `iteration-v1/084`
**TYPE**: SPECIALIST — single-coin cohort `("CRVUSDT",)`; 5th BUNDLE-003 candidate; FIRST under the REFORMED negative-baseline selector.
**Cycle**: 7, fresh-alt mining
**Author**: QR (autopilot)
**Tag**: `v0.v1-084`

---

## Headline

**SPECIALIST-NEGATIVE (catastrophic) — reform REFINED: a negative/near-zero trivial baseline is NECESSARY but NOT SUFFICIENT. CRV is case (b): pure-noise, no learnable structure. IS Sharpe −2.4717 (campaign worst) / OOS −1.5886.**

The reformed negative-baseline selector picked CRV at min-horizon trivial Sharpe +0.069 (the flattest of 12 candidates) on the hypothesis that a flat trivial baseline signals ML edge headroom. CRV decisively falsified the *sufficiency* of that rule: a near-zero baseline can mean EITHER edge headroom (case a — DOT/063, AAVE/078) OR pure noise (case b — CRV). CRV is case (b), confirmed on three independent axes (symmetric ~30% WR in both directions, diffuse feature importance, 188% max-DD blow-up). The selector needs a SECOND gate measuring learnable structure before a symbol enters a specialist brief.

This is the IDEAL adversarial outcome: the pre-registered hypothesis was tested cleanly (no scope creep, no leak, faithful implementation per Critic Check 8) and DECISIVELY FALSIFIED. The catastrophe is genuine model failure, not a hygiene artifact.

---

## Decision: SPECIALIST-NEGATIVE (catastrophic) — NO MERGE

**Verdict** (from Phase 7.5 Critic review, commit `78b9411d`): `SPECIALIST-NEGATIVE`, subtype `NEGATIVE-MOMENTUM-DOMINATED`.

- CRV DROPPED from the BUNDLE-003 candidate roster.
- **BUNDLE-002 (`v0.v1-082`) UNCHANGED.** No BUNDLE-003.
- F-AXIS adjudication: F1 PASS (181 IS / 89 OOS — data NOT thin, it traded plenty and lost catastrophically), F2 technically PASS but HARMFUL-BIND (feature rank 2/49 on a no-structure symbol = worst outcome), F3 UNVERIFIABLE (R-FADE-OFF control absent, moot), **F4 FAIL-catastrophic (IS Sharpe −2.4717 vs the +0.069 baseline it was selected to beat)**.
- Section 8.1 band: IS −2.4717 is far below the +0.20 NEGATIVE threshold.

---

## Results Table

| Metric | In-Sample | Out-of-Sample | OOS/IS ratio |
|---|---|---|---|
| Monthly Sharpe | **−2.4717** | **−1.5886** | 0.6427 |
| Monthly Sortino | −1.5529 | −1.9222 | 1.2378 |
| Max drawdown | **188.74%** | 48.14% | 0.2551 |
| Win rate | 29.8% | 30.3% | 1.0169 |
| Profit factor | 0.4564 | 0.6526 | 1.4297 |
| Total trades | 181 | 89 | 0.4917 |
| Net PnL (equity-curve) | −188.74% | −45.84% | — |
| DSR | −26.30 | −29.91 | — |
| PSR(monthly vs 0) | 0.000062 | 0.008852 | — |
| R-FADE fire count | 76 | — | — |
| Inner-ensemble dispersion | 48.36 (confident, WRONG direction) | — | — |

IS −2.4717 is the single worst result in the entire v1 campaign. Both samples are deeply negative — the OOS/IS ratio of 0.64 is meaningless (it does not indicate generalization; both terms are catastrophic).

**Per-month blow-up profile** (concentrated, not steady bleed): two IS months carry ~56% of the loss — 2022-09 (−54.84%, 7 trades) + 2025-01 (−51.16%, 6 trades) = −106.01% of the −188.74% total. OOS repeats it: 2026-01 −20.55% in a single month (11 trades) dominates the OOS loss. The catastrophe is (anti-signal) × (CRV hot-vol regime, NATR p50 ~7.9%) × (181 leveraged trades), not a deeper-negative drift.

**Per-regime**: artifact collapsed all bars to `regime=unknown` (tagger not wired into single-symbol run) — the "bear-localized edge" thesis (trivial momentum −0.924 in CRV bear) is UNTESTED, not refuted; moot given the IS catastrophe.

---

## Mining Scorecard — fresh-alt mining is 0/4

| Iter | Symbol | Selection rule | Outcome | Notes |
|---|---|---|---|---|
| — | ATOM | (pre-reform) | NEGATIVE | fresh mine |
| — | ICP | (pre-reform) | NEGATIVE | fresh mine |
| /083 | FIL | narrative-orthogonality | NEGATIVE-MOMENTUM-DOMINATED | POSITIVE +1.45 baseline, no ML headroom — the trap GATE 1 now screens |
| **/084** | **CRV** | **negative-baseline (reformed)** | **NEGATIVE-MOMENTUM-DOMINATED (catastrophic)** | **near-zero +0.069 baseline BUT no learnable structure — case (b)** |
| /078 | AAVE | existing-roster rescue | RESCUED (+0.34) | NOT a fresh mine — existing roster |

**ATOM / ICP / FIL / CRV all fresh-NEGATIVE.** The ONLY rescuable seat (AAVE/078) was an existing-roster rescue, not a fresh mine. Two selection rules tried (narrative-orthogonality, negative-baseline); both produced fresh-mine NEGATIVEs. Fresh-mine base rate: **0/4.**

---

## The Refined Rule — negative-baseline AND learnable-structure gate

The reformed negative-baseline selector is **necessary but not sufficient.** Empirically confirmed:

| Iter | Trivial baseline | Learnable structure | Outcome | Case |
|---|---|---|---|---|
| DOT/063 | negative/weak | PRESENT | IS +1.32 | (a) WORKED |
| AAVE/078 | negative | PRESENT | rescue +0.34 | (a) WORKED |
| FIL/083 | **POSITIVE +1.45** | n/a (no headroom) | IS −0.82 | GATE 1 trap (correctly removed) |
| **CRV/084** | near-zero +0.069 | **ABSENT (pure noise)** | **IS −2.47** | **(b) catastrophic, GATE 1 cannot screen** |

GATE 1 screens out FIL-type positive baselines but admits BOTH case (a) and case (b). A near-zero trivial baseline means EITHER ML edge headroom OR pure noise. CRV is case (b): the +0.069 baseline was the **absence of edge in the symbol**, not headroom for ML to exploit.

**Three structure-confirming diagnostics** (all fired for CRV):
1. **Symmetric ~30% WR in both directions on a symmetric label** = anti-signal, not no-signal. The model fit IS noise into a sign-rule that inverts OOS (OOS WR 30.3% confirms stable inversion). PF 0.4564, 63.5% stop-out.
2. **Diffuse feature importance** = noise-fitting across the whole space. `oi_price_divergence_30` landed rank 2/49 on a no-structure symbol — the WORST outcome (LM 4.5 suspicion-flag predicted rank 8–14 with "rank 1–3 = SUSPICIOUS"; the flag FIRED). Gain spread across 47 of 49 features.
3. **Max-DD 188%** = it blew up, did not merely underperform. EDA near-zero autocorr (lag1 −0.026, lag3 −0.024, lag7 −0.003) corroborates: CRV is choppy/mean-reverting, no persistent directional structure at 8h.

**Refined selector rule going forward**: a symbol enters a specialist brief iff
- `trivial_baseline_min_horizon ≤ +0.15` (GATE 1, unchanged) **AND**
- `probe_IS_Sharpe ≥ +0.30` (GATE 2 PRIMARY — fast single-seed LightGBM probe: max_depth=5, num_leaves=31, seed=42, n_trials=10, full 48-col stack, exact triple-barrier label, walk-forward IS-only) **AND**
- `max single-feature-vs-LABEL |IC| ≥ 0.04` (GATE 2 SECONDARY — REQUIRES replacing the current family-redundancy `ic_matrix.csv` with a DIRECT feature-vs-label IC computation) **AND**
- `max(|acf_lag1|, |acf_lag3|, |acf_lag7|) ≥ 0.03` (GATE 2 TERTIARY — informational confirmer).

The probe Sharpe is the load-bearing gate. One probe (~minutes) would have rejected CRV instead of a ~5.5–8h specialist that cratered. Calibrate the |IC| threshold on the 4-point labeled set {DOT/063, AAVE/078 = PASS} vs {CRV/084, FIL/083 = REJECT}.

**CRITICAL CAVEAT**: GATE 2 would have correctly rejected CRV, but it does NOT establish that a structure-PRESENT fresh alt yields a POSITIVE specialist under the locked stack. That conjunction (negative-baseline AND structure-present → positive specialist) is UNTESTED. GATE 2 converts a 0/4 blind-mine into a structure-filtered mine; it does not, by itself, produce a winner.

---

## Component Attribution

- **`oi_price_divergence_30`**: verified-clean (double-`.shift(1)`, no leak), binds at rank 2/49 — but on a no-structure symbol it ACCELERATED the bleed by routing top split budget through a feature with no CRV forward edge. The feature is sound; the symbol it was aimed at was not.
- **R-FADE gate (76 fires)**: NEUTRAL-to-mildly-harmful. A VETO-only gate cannot rescue a model whose surviving trades are themselves anti-signal — the 181 that remained still ran WR 29.8% / PF 0.46. IS fade-z calibration was non-monotone and reversed past |z|≥2.5, consistent with no exploitable divergence relationship on CRV.
- **The SYMBOL caused the catastrophe.** Stacking two new axes on a no-structure symbol just gave the overfit more surface area. Neither component caused it.

---

## What Worked / What Failed

**Worked (methodology):**
- Clean adversarial test — Critic Checks 1, 2, 7, 8, 13, 14 all PASS. No look-ahead, foundation embargo intact, faithful hypothesis implementation, sacred constants held, one-variable-at-a-time discipline preserved (global `V1_FEATURE_COLUMNS_PRUNED` held at 48; LOCAL 49-col `V1_ITER084_FEATURE_COLUMNS` asserted — DOT/ETH/BTC/AAVE specialists unaffected).
- The reform's GATE 1 (negative-baseline) correctly screens out FIL-type positive baselines.

**Failed (research):**
- The negative-baseline selector's *sufficiency* assumption — falsified. It admits case (b) pure-noise symbols, which then catastrophically overfit.
- CRV as a specialist seat — case (b), IS −2.47.

**Process gaps for next runner:**
1. `ic_matrix.csv` is family-vs-family redundancy, NOT feature-vs-label — there is NO measurement of forward predictive signal. This is the hole that let CRV through; GATE 2 secondary requires replacing it with a direct feature-vs-label IC.
2. R-FADE-OFF control cell pre-registered (F3) but not shipped — F3 UNVERIFIABLE. Wire `--rfade-off` into the runner as a HARD Phase 6 deliverable.
3. Per-regime CSV collapsed to `unknown` on single-symbol runs — wire the regime tagger.
4. `comparison.csv` IS net_pnl −188.74% (equity-curve) vs per_symbol −326.29% (sum-of-trade) definition mismatch — reporting-consistency note.

---

## Lessons (generalizable)

1. **A near-zero/negative trivial-momentum baseline is NECESSARY but NOT SUFFICIENT evidence of ML edge headroom.** It admits two populations: directional structure ML can exploit (case a) AND pure noise where ML overfits and craters (case b). Distinguish them with a learnable-structure probe BEFORE authoring a specialist.
2. **High importance for a NEW feature on a no-structure symbol is the HARMFUL outcome, not a pass.** The F2 INERT-branch falsifier is the wrong instrument; rank 1–3 + diffuse importance is a structure-ABSENCE fingerprint. Re-weight LM Master suspicion-flags as HARD pre-registered falsifiers.
3. **Symmetric sub-50% win rate in both directions on a symmetric label = anti-signal** — the model systematically picked the wrong side, fitting IS noise into a sign-rule that inverts OOS. This is the single cleanest no-structure diagnostic.
4. **Fresh-alt mining is 0/4 under the locked stack.** The binding constraint may be the locked architecture's inability to extract edge from cold alts, not the selector. The burden of proof has shifted to demonstrating the architecture can produce a fresh-mine winner at all.

---

## Path Forward — RECOMMEND MINING PAUSE

Fresh-alt mining is at **0/4** (ATOM/ICP/FIL/CRV all NEGATIVE; AAVE was an existing-roster rescue, not a fresh mine). Three options, in priority order:

### (1) CONSOLIDATE — multi-seed CONFIRMATION of BUNDLE-002 as-is (HIGHEST EXPECTED VALUE)
BUNDLE-002 ({BTC, ETH, DOT, AAVE}, IS +0.7157 / OOS +1.0043) is a working merged baseline that has NEVER had a full multi-seed CONFIRMATION re-validation under the current code state. Section 11.E flags an OPEN post-fix delta (pre-fix snapshot numbers + an in-flight C2/H1/H5/H10/H8/H9 post-fix delta still unresolved). Spend the next compute block validating the EXISTING baseline's robustness (10-seed mean Sharpe, post-fix delta resolution, DSR/PBO/PSR at CONFIRMATION budget) rather than mining a 5th seat onto an unvalidated 4-seat bundle. **Mechanism: lock in what works before extending it.**

### (2) IMPROVE EXISTING SEATS — re-aim the verified feature onto a proven-structure cohort
The 0/4 fresh-mine rate vs the AAVE/078 existing-roster RESCUE success is the signal: the methodology extracts edge on symbols it already has a foothold on, not on cold alts. Re-aim the verified `oi_price_divergence_30` learning (it binds cleanly) onto DOT/063 or AAVE/078 — symbols with PROVEN structure — as a strictly-accretive feature test on a winning seat. **Mechanism: compound edge where structure is already established, instead of searching for new structure on cold alts.**

### (3) STRUCTURE-GATED 6th MINE — ONLY IF (1) and (2) are exhausted
If the program insists on continuing to mine, the next fresh alt MUST clear GATE 2 (probe IS Sharpe ≥ +0.30 AND feature-vs-label |IC| ≥ 0.04 AND autocorr ≥ 0.03) at the cheap probe stage BEFORE a full specialist brief is authorized. This requires building `analysis/iteration_v1-NNN/structure_screen.py` and replacing the family-redundancy `ic_matrix.csv` with a direct feature-vs-label IC. ARBUSDT (+0.005 min-horizon) and OPUSDT (+0.162) were disqualified at <4y data; if either crosses the 4y threshold AND passes the probe, it is the next candidate. **CAVEAT: GATE 2 would have correctly rejected CRV but does NOT establish that a structure-present fresh alt yields a positive specialist under the locked stack — that conjunction is UNTESTED. The burden of proof is now on demonstrating the locked architecture can produce a fresh-mine winner at all.**

---

## Path Forward (from Critic — verbatim)

> The fresh-mine axis (per-cohort-specialization on a NEW alt) is at 0/4. I STRONGLY recommend the program PAUSE fresh-alt mining and consolidate before mining a 6th alt.
>
> 1. **CONSOLIDATE — multi-seed CONFIRMATION of BUNDLE-002 as-is (family: bundle-validation / risk-primitive).** BUNDLE-002 ({BTC, ETH, DOT, AAVE}) is a working merged baseline that has NEVER had a full multi-seed CONFIRMATION re-validation under the current code state (Section 11.E flags pre-fix snapshot numbers + an in-flight C2/H1/H5/H10/H8/H9 post-fix delta that is still OPEN). Spend the next compute block validating the EXISTING baseline's robustness rather than mining a 5th seat onto an unvalidated 4-seat bundle. Mechanism: lock in what works before extending it.
>
> 2. **IMPROVE EXISTING ROSTER SEATS — feature-engineering on a CONFIRMED-winning seat (family: feature-family, on an existing cohort).** The 0/4 fresh-mine rate vs the AAVE/078 existing-roster RESCUE success is the signal: the methodology extracts edge on symbols it already has a foothold on, not on cold alts. Re-aim the verified `oi_price_divergence_30` learning onto DOT/063 or AAVE/078 — symbols with PROVEN structure — as a strictly-accretive feature test. Mechanism: compound edge where structure is already established.
>
> 3. **STRUCTURE-GATED 6th mine ONLY IF (1) and (2) are exhausted (family: per-cohort-specialization + structure-screen).** The next fresh alt MUST clear GATE 2 (probe IS Sharpe ≥ +0.30 AND feature-vs-label |IC| ≥ 0.04 AND autocorr ≥ 0.03) at the cheap probe stage BEFORE a full specialist brief. ARBUSDT (+0.005) and OPUSDT (+0.162) were disqualified at <4y data; if either crosses the 4y threshold AND passes the probe, it is the next candidate. Mechanism: the probe converts the 0/4 blind-mine into a structure-filtered mine — but note this conjunction (negative-baseline AND structure-present → positive specialist) is UNTESTED.
>
> The Path Forward is advisory. My adversarial position stands: at a 0/4 fresh-mine rate, the burden of proof has shifted to demonstrating the locked architecture CAN produce a fresh-mine winner at all, and option (1) consolidation is the highest-expected-value next move.

---

## Process Recommendations (carry to next iteration)

1. **Implement GATE 2 (Learnable-Structure Pre-Screen) as a cheap pre-flight, not a post-mortem.** Build `analysis/iteration_v1-NNN/structure_screen.py`; replace family-redundancy `ic_matrix.csv` with direct feature-vs-label IC; calibrate the |IC| threshold on the {DOT/063, AAVE/078} vs {CRV/084, FIL/083} labeled set.
2. **Re-weight LM Master Phase 4.5 suspicion-flags as HARD pre-registered falsifiers.** Rank 1–3 + diffuse importance = structure-absence signal, not a pass.
3. **Wire `--rfade-off` control into the runner** as a HARD Phase 6 deliverable so F3 is verifiable on PROMISING iterations.

---

## Baseline Status

**BUNDLE-002 (`v0.v1-082`) UNCHANGED — remains the v1 baseline anchor.** No BUNDLE-003. CRV DROPPED from the BUNDLE-003 candidate roster.
