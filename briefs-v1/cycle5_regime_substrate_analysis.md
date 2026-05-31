# Cycle-5 Regime Profile Mapping for /044 Portfolio Substrate

**Date**: 2026-05-31
**Author**: QR (regime-profile reanalysis under USER DIRECTIVE)
**Anchor**: BASELINE_V1 `v0.v1-baseline-corrected` `f8bc12c` (IS Sharpe +0.2829 / OOS Sharpe +0.6637)
**Scope**: Reclassify cycle-5 iterations /034-/040 through a REGIME-PROFILE lens (not single-anchor MERGE lens) to identify ANCHOR + DIVERSIFIER substrate candidates for the /044 portfolio combination.

---

## 1. Regime-Profile Schema

| Code | Profile | Substrate role |
|------|---------|----------------|
| A | IS-STRONG, OOS-WEAK | Regime-specialist for IS-dominant regimes (2022 bear, 2023 chop, 2024-Q1 transition). DIVERSIFIER candidate if IS-profitable mechanism is genuine and OOS regression is regime-localized. |
| B | IS-WEAK, OOS-STRONG | Regime-specialist for OOS regime (2025-Q2/Q3 trend). ANCHOR if OOS strength is mechanism-attributable; risk: lottery basin at single-seed. |
| C | IS-STRONG, OOS-STRONG | Universal — pure ANCHOR. None observed in cycle-5 outside baseline. |
| D | IS-WEAK, OOS-WEAK | No edge anywhere — EXCLUDE. |
| E | MIXED | Per-cohort asymmetry (bundle hides per-symbol regime structure). |

**Strong/Weak threshold**: |Sharpe| ≥ 0.30 for "strong"; |Sharpe| ≤ 0.20 for "weak"; in-between = "mid".

---

## 2. Per-Iteration Regime Profile Table

| Iter | Axis | IS Sharpe | OOS Sharpe | OOS/IS | Profile | /044 Role | Prior verdict (revised lens) |
|------|------|-----------|------------|--------|---------|-----------|------------------------------|
| baseline | 5-cohort + triple-barrier (anchor) | +0.2829 | +0.6637 | 2.35 | **B (lean C)** | **ANCHOR-PRIMARY** | reference |
| /034 | basis_zscore_30 (feature add) | **-0.0057** | **+0.3935** | -69.6 | **B (weak-mid)** | **DIVERSIFIER-LITE** | was NEG-CLEAN; revised: weak-B OOS regime-specialist with informational positive PSR_vs_1 lift |
| /035 | trend-scanning labels (5-cohort) | **+0.2818** | **-0.0119** | -0.04 | **E (bimodal)** | **DECOMPOSED → /036** | bundle NEG-CAT, but LINK+DOT cohorts type-C (extracted to /036) |
| /036 | LINK+DOT trend-scan specialist | +0.0843 | **+1.7465** | 20.7 | **B (strong)** | **DIVERSIFIER-PRIMARY** | PROMISING-CLEAN +1.08 OOS Δ; the only single-seed strong B in cycle-5 |
| /037 | 5-cohort + Sortino objective | +0.1712 | **+0.8388** | 4.90 | **B (mid)** | **DIVERSIFIER-SECONDARY** | PROMISING-CLEAN +0.18 OOS Δ; universe-dependent per /039 |
| /038 | per-symbol vol-target ceiling | **-0.0308** | +0.1337 | -4.35 | **D** | **EXCLUDE** | NEG-CAT EDA-VINDICATED; structurally backward on rewarded cohorts |
| /039 | per-cohort Sortino × specialist hybrid | -0.1530 | +1.0393 | -6.79 | **B (mid)** vs baseline; **D vs /036 substrate** | **EXCLUDE** | NEG-CAT-vs-036 (-0.71 OOS Δ); basin-relocation-artifact, not a new substrate |
| /040 | composed `regime_momentum_signed_5d` | **+0.5588** | +0.2959 | 0.53 | **A (strong-IS)** | **DIVERSIFIER-TENTATIVE** | NEG-CLEAN-OVERFIT bundle, but Section 13 diary reframed it as regime-specialist; **THE ONLY type-A in cycle-5** |

**Cycle-5 profile distribution**: 0 × type C (universal), 4 × type B (OOS specialists incl baseline), 1 × type A (IS specialist = /040), 1 × type D (EXCLUDE = /038), 1 × type E (decomposed = /035), 1 × type D-vs-substrate (/039 vs /036).

---

## 3. IS/OOS Sharpe Matrix (Sharpe values, magnitudes-bold ≥0.30)

| Iter | IS | OOS |
|------|---:|----:|
| baseline | **+0.2829** (mid) | **+0.6637** |
| /034 | -0.0057 | **+0.3935** |
| /035 | +0.2818 (mid) | -0.0119 |
| /036 | +0.0843 | **+1.7465** |
| /037 | +0.1712 | **+0.8388** |
| /038 | -0.0308 | +0.1337 |
| /039 | -0.1530 | **+1.0393** |
| /040 | **+0.5588** | +0.2959 (mid) |

**Observation**: /040 holds the **strongest IS Sharpe of the cycle** (+0.5588 vs baseline +0.2829, +0.28 Δ) — type-A regime-specialist candidate; no other cycle-5 iteration is type-A. Every other iteration with IS strength was either bundle-NEG (/035 at IS +0.28 OOS -0.01 = pure bimodal) or had OOS-stronger character.

---

## 4. Per-Symbol Regime Profiles

Per-symbol IS / OOS net PnL%, with cohort-level regime profile inferred:

### 4.1 BASELINE_V1 — per-symbol regime profile

| Symbol | IS PnL% | OOS PnL% | Cohort profile |
|--------|--------:|---------:|----------------|
| LINK | +72.06 | +34.23 | type-C-cohort (IS+OOS strong) |
| DOT | +26.62 | +1.96 | type-A-cohort (IS strong, OOS weak) |
| LTC | +3.27 | **-47.25** | type-D-cohort (catastrophic OOS) |
| ETH | -13.70 | +2.75 | weak-B-cohort |
| BTC | -37.28 | +33.17 | **strong-B-cohort** (IS weak, OOS strong) |

**Baseline regime structure**: LINK is universal; BTC pivots OOS-strong; LTC is the catastrophe-symbol; DOT is IS-specialist; ETH is weak-everywhere.

### 4.2 /036 — per-symbol regime profile (2-cohort substrate)

| Symbol | IS PnL% | OOS PnL% | Cohort profile |
|--------|--------:|---------:|----------------|
| LINK | +2.27 | **+108.91** | **strong-B-cohort** |
| DOT | -6.36 | **+113.63** | **strong-B-cohort** |

**/036 regime structure**: BOTH cohorts are type-B (OOS-dominant); IS is near-flat. Strong DIVERSIFIER for OOS-regime coverage.

### 4.3 /037 — per-symbol regime profile (5-cohort + Sortino)

| Symbol | IS PnL% | OOS PnL% | Cohort profile |
|--------|--------:|---------:|----------------|
| LINK | **+56.84** | -8.64 | **type-A-cohort** (IS-strong, OOS-degraded vs baseline +34.23) |
| DOT | **+57.20** | **+39.30** | **type-C-cohort** (IS+OOS both strong) |
| LTC | +4.71 | -8.95 | weak-everywhere (BUT vs baseline -47.25, this is a +38pp LIFT) |
| BTC | -38.81 | +18.53 | type-B-cohort |
| ETH | -63.84 | +9.75 | weak-everywhere |

**/037 regime structure**: DOT is type-C universal in this substrate; LINK is type-A IS-only; LTC was rescued from catastrophe. The DOT type-C profile is the load-bearing finding — it's the ONLY cycle-5 per-cohort type-C.

### 4.4 /040 — per-symbol regime profile (composed feature)

| Symbol | IS PnL% | OOS PnL% | Cohort profile |
|--------|--------:|---------:|----------------|
| LTC | **+140.36** | +19.79 | **strong-A-cohort** (LTC's largest IS lift in cycle-5) |
| LINK | **+121.03** | -19.80 | **strong-A-cohort** (LINK direction-reversed OOS) |
| DOT | +1.37 | +10.80 | weak-B-cohort |
| BTC | -85.02 | +5.32 | type-B-cohort (Pool A destroyed IS) |
| ETH | -125.03 | -5.92 | type-D-cohort |

**/040 regime structure**: LTC + LINK are type-A IS-specialists (the 5-day momentum primitive catches their medium-frequency directional moves IS but reverts OOS); BTC + ETH (Pool A) are destroyed IS. /040 is the **per-cohort regime mirror image of /036**: where /036 isolates LINK+DOT for OOS, /040 isolates LTC+LINK for IS.

### 4.5 /034 — per-symbol regime profile (basis_zscore_30)

| Symbol | IS PnL% | OOS PnL% | Cohort profile |
|--------|--------:|---------:|----------------|
| LTC | +116.39 | -5.38 | **strong-A-cohort** (LTC IS lifted, OOS slight regression but +42pp vs baseline -47.25) |
| DOT | +60.74 | -15.05 | **type-A-cohort** |
| LINK | +42.58 | -23.80 | type-A-cohort (direction-reversed OOS vs baseline +34.23) |
| BTC | -86.59 | -3.24 | type-D-cohort |
| ETH | -114.00 | -9.42 | type-D-cohort |

**/034 regime structure**: Same per-cohort regime mirror as /040 — LTC+DOT+LINK type-A IS, BTC+ETH type-D. **Bundle-level OOS is +0.39 only because LTC's -47pp baseline catastrophe is dampened (-5pp).** /034 is a **LTC-catastrophe-recovery specialist disguised as OOS-marginal.**

### 4.6 /038 — per-symbol regime profile (vol-ceiling)

Identical IS roster to /034 (same Optuna basin under single-seed=42 frozen-baseline pattern); both have type-D OOS bundle. The vol-ceiling clip mechanically degrades OOS through the EDA-VINDICATED asymmetry mechanism. **EXCLUDE from /044.**

---

## 5. Cross-Iteration Per-Symbol Synthesis

### 5.1 Per-symbol OOS Sharpe direction across cycle-5 (regime fingerprint)

Cross-cohort OOS PnL contribution % (sign indicates direction):

| Symbol | baseline OOS | /034 | /035 | /036 | /037 | /038 | /039 | /040 |
|--------|------:|---:|---:|---:|---:|---:|---:|---:|
| LINK | **+34.23** | -23.80 | +108.91 | **+108.91** | -8.64 | -23.80 | +68.45 | -19.80 |
| DOT | +1.96 | -15.05 | +113.63 | **+113.63** | **+39.30** | -15.05 | +44.40 | +10.80 |
| LTC | **-47.25** | -5.38 | -32.76 | n/a | -8.95 | -5.38 | n/a | +19.79 |
| BTC | **+33.17** | -3.24 | -17.62 | n/a | +18.53 | -3.24 | n/a | +5.32 |
| ETH | +2.75 | -9.42 | -43.73 | n/a | +9.75 | -9.42 | n/a | -5.92 |

**LINK**: highly regime-dependent — OOS-strong on baseline, /035, /036, /039 (trend-scan substrates); OOS-degraded on /034, /037, /038, /040 (5-cohort triple-barrier substrates with feature/risk perturbations).
**DOT**: most stable winner — positive OOS in 5 of 8 iterations including baseline; strongest on /036 (+113.63) and /037 (+39.30).
**LTC**: catastrophe symbol on baseline (-47.25); rescued by 4 of 7 iterations to varying degrees; only /040 produced positive OOS LTC (+19.79).
**BTC**: baseline-favored (+33.17); degraded in every cycle-5 iteration EXCEPT /037 and /040 (both positive but weaker).
**ETH**: weak-everywhere; only /037 and /040 mildly positive.

### 5.2 Per-symbol IS+OOS cohort universality test

Symbols that show TYPE-C (IS+OOS both >0) somewhere in cycle-5:
- **DOT**: type-C in /037 (IS +57.20 / OOS +39.30). UNIVERSE-INDEPENDENT.
- **LTC**: type-A everywhere; never type-C; **always sacrificed OOS** despite IS lift — pure type-A.
- **LINK**: type-C on /035 (IS +2.27 close to zero) and /036 (IS +2.27); marginal-IS but OOS strong.
- **BTC**: type-B on baseline (-37 IS / +33 OOS); type-A nowhere.
- **ETH**: never reaches type-C or type-A.

**Implication for /044**: DOT is the only per-cohort type-C found in cycle-5. LINK is mostly type-B with weak IS. LTC is the catastrophe-symbol where /040's IS-strong type-A profile uniquely lifts the OOS (+19.79 vs baseline -47.25) — /040 may be a LTC-targeted DIVERSIFIER.

---

## 6. /044 Substrate Recommendations

### 6.1 ANCHOR candidates (universal C-profile required)

**Count: 1 candidate (with caveat).**

- **BASELINE_V1 (5-cohort + triple-barrier)** — type-B-lean-C at portfolio level (IS +0.2829 / OOS +0.6637). The single universal substrate in cycle-5. Should remain the ANCHOR for the /044 portfolio.

No pure type-C anchor was discovered in cycle-5 EXPLORATIONs at single-seed budget.

### 6.2 DIVERSIFIER candidates

**Count: 3 primary + 1 tentative.**

1. **/036 — LINK+DOT trend-scan specialist** (type-B strong; OOS Sharpe +1.7465, OOS Δ +1.08). PRIMARY DIVERSIFIER. Already routed as /044-A. Covers OOS-regime LINK+DOT amplification. **Risk**: 2-cohort, 105 OOS trades just below the 130 floor; single-seed lottery risk; concentration 50/50 LINK/DOT.

2. **/037 — 5-cohort + Sortino objective** (type-B mid; OOS Sharpe +0.8388, OOS Δ +0.18). SECONDARY DIVERSIFIER. Already routed as /044-B. Covers LTC catastrophe-recovery (+38pp vs baseline) and DOT amplification (+37pp). **Risk**: universe-dependent (/039 refuted compoundability with /036); LINK degradation (-43pp); BTC degradation (-15pp).

3. **/040 — composed regime_momentum specialist** (type-A strong-IS; IS Sharpe +0.5588, OOS Sharpe +0.2959). TENTATIVE DIVERSIFIER per diary §13 reframe. Covers 5 of 6 IS regimes positively (2022-bear, 2023-Q1 trend-restart, 2024-Q3 transition, 2025-Q1, 2024-Q1 LTC). Specifically rescues **LTC OOS** (+19.79 vs baseline -47.25, +67pp swing). **Risk**: blind spot in 2023-Q3-Q4 recovery regime (the regime closest to OOS-start); stack-prune precondition required (44 → 20-25 cols via cluster-MDA).

4. **/034 — basis_zscore_30 feature add** (weak type-B at bundle but **strong type-A LTC-rescue** like /040; IS +116.39 LTC, OOS -5.38 vs baseline -47.25). LITE DIVERSIFIER candidate IF the LTC-rescue mechanism survives multi-seed. **Note**: the IS roster is bit-identical to /038 (same Optuna basin under single-seed=42 frozen-baseline pattern documented in `feedback_v3_single_seed_frozen_baseline.md`). The /034 basis_zscore_30 feature's true marginal contribution is contaminated by the frozen baseline — **/034 cannot be cleanly separated from /038 in regime-profile terms at single-seed**. Defer to multi-seed CONFIRMATION before /044 inclusion.

### 6.3 EXCLUDE

- **/035** — bundle-level type-E (bimodal); already DECOMPOSED into /036 substrate. Do not include /035 itself.
- **/038** — type-D bundle and mechanism EDA-VINDICATED backward. EXCLUDE.
- **/039** — type-D vs /036 substrate; basin-relocation-artifact. EXCLUDE.

---

## 7. Pairing Recommendations for /044

**Top 3 substrate pairings** for portfolio combination:

### Pairing 1 (RECOMMENDED): BASELINE + /036 + /037

- **ANCHOR**: BASELINE_V1 (covers BTC-OOS-strong + LINK-universal regimes).
- **DIVERSIFIER-PRIMARY**: /036 LINK+DOT specialist (covers OOS-LINK+OOS-DOT amplification).
- **DIVERSIFIER-SECONDARY**: /037 5-cohort Sortino (covers LTC catastrophe-recovery + DOT amplification).
- **Coverage logic**: BASELINE owns BTC-OOS regime; /036 owns LINK+DOT-OOS regime; /037 owns LTC-recovery regime. **No regime double-covered, no regime uncovered.**
- **Status**: this is the currently routed /044-A + /044-B pairing per /040 closeout. KEEP.

### Pairing 2 (CONDITIONAL): BASELINE + /036 + /040 (stack-pruned)

- **ANCHOR**: BASELINE_V1.
- **DIVERSIFIER-OOS**: /036 LINK+DOT.
- **DIVERSIFIER-IS-REGIME**: /040 composed-feature (covers 5 of 6 IS regimes per diary §13; LTC rescue +67pp).
- **Coverage logic**: BASELINE + /036 covers OOS-regimes; /040 covers IS regimes that may dominate the next 6-12 months of out-of-sample as the OOS window rolls forward. Type-A diversifier adds regime breadth on the temporal axis.
- **Risk**: /040 is type-A; it bets on an IS-regime returning. **2023-Q3-Q4 blind spot is structurally adjacent to current OOS-rollforward window** — high regression risk in the near term.
- **Precondition**: stack-prune 44 → 20-25 cols via cluster-MDA before /040 enters portfolio.
- **Routing**: replace /044-B with /044-C (/040-pruned) IF user prioritizes regime breadth over Sortino's downside coverage.

### Pairing 3 (ROLE-COMPLEMENTARY): BASELINE + /037 + /040

- **ANCHOR**: BASELINE_V1.
- **DIVERSIFIER-DOWNSIDE**: /037 Sortino (penalizes downside variance, lifts LTC + DOT).
- **DIVERSIFIER-UPSIDE**: /040 composed-feature (captures directional trends 5-day-horizon).
- **Coverage logic**: ASYMMETRIC pair — /037 protects the left tail; /040 extends the right tail. Together they form an asymmetric volatility-shape modulator on BASELINE.
- **Risk**: BOTH diversifiers underperform on the 2023-Q3-Q4 chop regime; portfolio relies on BASELINE in that window. Less regime-orthogonal than Pairings 1-2.

---

## 8. Does IS-Strength Alone Justify /044 Inclusion?

**Answer: NO, but it justifies a CONFIRMATION-mode multi-seed test under a specific protocol.**

IS-strength at single-seed EXPLORATION budget (n_trials=18, ENSEMBLE_SIZE=3, seed=42) is a NOISY signal:

1. **Single-seed frozen-baseline pattern**: /034 + /038 share BIT-IDENTICAL IS rosters; this pattern (documented in `feedback_v3_single_seed_frozen_baseline.md`) shows per-symbol Optuna basins are deterministic at single-seed. IS-strength at single-seed is a property of the basin, not necessarily the axis.

2. **44-col stack over-fit risk**: /040's textbook IS-overfit signature (IS +0.28 Δ → OOS -0.37 Δ) is exactly the pattern that single-seed EXPLORATION budgets allow. v1's 44-col stack at n_trials=18 has structural ridge dimensionality 9 (n_eff=9 for 3 consecutive iterations) — Optuna finds IS-leveraged basins that exploit the wider feature space.

3. **Type-A profile genuinely informs portfolio combination IF the regime decomposition holds across seeds**: /040's diary §13 decomposition shows the IS lift is distributed across 5 of 6 regimes — NOT concentrated in one window. That suggests the type-A profile is regime-genuine, not single-window-overfit. But this requires multi-seed validation to confirm.

**Protocol for /044-C (/040 inclusion) — IS-only-justification CANNOT lead to merge, but it CAN lead to a multi-seed test**:

- Run /044-C as: stack-prune /040 to 20-25 cols (cluster-MDA on IS), then --seeds 5 --n-trials 35 --ensemble-size 5 (full CONFIRMATION spec).
- MERGE GATE per /044-C: multi-seed mean IS Sharpe > 0 AND IS regime decomposition wins ≥ 4 of 6 IS regimes AND OOS Sharpe degradation ≤ -0.30 vs baseline.
- If multi-seed mean OOS Sharpe ≥ 0 AND ≥ 4 of 6 IS regimes won: include /040-pruned as a DIVERSIFIER.
- If multi-seed degrades OOS Sharpe below -0.30: revert to Pairing 1.

**Generalization to /034**: same protocol applies. /034's bundle-level OOS Sharpe +0.39 is below the 1.0 floor at single-seed, but its LTC-rescue mechanism (+42pp vs baseline) is a candidate type-A regime-specialist that warrants multi-seed test. /044-D (CONDITIONAL): if /044-C confirms /040 as DIVERSIFIER, run /034 multi-seed CONFIRMATION as /044-D probing the basis_zscore_30 marginal contribution under stack-pruned 20-25 cols.

---

## 9. Final Substrate Routing for /044

| Substrate slot | Iteration | Profile | Status |
|---|---|---|---|
| /044-A | /036 LINK+DOT trend-scan specialist | type-B strong | KEEP — primary OOS diversifier |
| /044-B | /037 5-cohort + Sortino | type-B mid | KEEP — LTC catastrophe-recovery + DOT amplification |
| /044-C (NEW) | /040 composed-feature stack-pruned (44→20-25 cols) | type-A strong-IS | CONDITIONAL — run multi-seed before include |
| /044-D (CONDITIONAL on C) | /034 basis_zscore_30 stack-pruned | weak type-A LTC-rescue | DEFER — multi-seed test if /044-C succeeds |
| ANCHOR | BASELINE_V1 | type-B-lean-C | KEEP — portfolio anchor |
| EXCLUDE | /035 (decomposed), /038 (NEG-CAT), /039 (basin-relocation-artifact) | type-D/E | EXCLUDE |

---

## 10. Counts Summary

- **ANCHOR candidates**: 1 (BASELINE_V1).
- **DIVERSIFIER candidates**: 3 primary (/036, /037, /040-pruned) + 1 tentative (/034-pruned).
- **EXCLUDE**: 3 (/035 decomposed, /038, /039).
- **Top pairing**: BASELINE + /036 + /037 (Pairing 1; currently routed as /044-A+B).
- **2nd pairing (REGIME-BREADTH)**: BASELINE + /036 + /040-pruned (Pairing 2; adds /044-C).
- **3rd pairing (ROLE-COMPLEMENTARY)**: BASELINE + /037 + /040-pruned (Pairing 3; asymmetric volatility-shape).

---

## 11. Key Caveats

1. **All cycle-5 iterations were single-seed at EXPLORATION budget**; all per-symbol IS rosters are subject to the single-seed frozen-baseline pattern. Multi-seed CONFIRMATION will reveal which mechanisms are basin-locked vs structurally orthogonal.
2. **/036's 105 OOS trades is below the 130 floor**; CONFIRMATION must validate trade-rate floor at bundle level.
3. **Concentration**: /036 is 50/50 LINK/DOT (clean diversification); /037 is DOT-78.62%-of-OOS (concentration risk dissolves at multi-seed per `feedback_v3_single_seed_frozen_baseline.md`); /040 is LTC-194%-of-OOS at single-seed (extreme concentration).
4. **/039 is empirically refuted as a compoundable substrate**: do NOT attempt to bundle Sortino-on-/036 in /044.
5. **/040's stack-prune precondition is load-bearing**: without it, /040 retains the same 44-col over-fit risk that produced the cycle-5 NEG verdict.
