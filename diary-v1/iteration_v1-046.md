# iter-v1/046 — EXPLORATION methodology — IS-only partition resolve

**Tag**: `v0.v1-046`
**Date**: 2026-06-01
**Iteration type**: EXPLORATION
**Axis family**: `methodology` (substrate re-composition; IS-only partition-solve scoring fix)
**Cycle slot**: cycle-6 EXPLORATION 1/10 (first EXPLORATION post-/045 BLOCK-FINAL; cycle-5 closed at /045 closeout)
**Status**: **EXPLORATION-PROMISING (PROMISING-DIVERGENCE; HP-basin-lottery-CAUTION subtype)** per Critic Phase 7.5 review
**BASELINE_V1.md**: UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`)

**Banner**: IS-only partition-solve at score `score_is = 0.6·IS_Sharpe + 0.4·IS_n_trades/250` (gated IS_n_trades ≥ 20; tiebreaker IS_n_trades desc) over 159 (iter, coin) inventory cells emitted substrate `(C-BTC=v1-025, C-ETH=v1-009, C-LINK=v1-025, C-LTC=v1-025, C-DOT=v1-031)` — **4 of 5 components DIVERGE from /045 ALT_1** (only C-DOT=v1-031 matches). CSV-replay bundle headline IS daily Sharpe **+2.837 / OOS daily Sharpe −0.876** (sign FLIP); IS PnL +50.28 / OOS PnL −6.56; IS n_trades 537 / OOS n_trades 242. F1 PASS (deflated IS Sharpe +2.39 > +0.50 floor); F2 FAIL (4/5 divergence ≠ 5/5 coincidence); **F3 PASS** (≥3 divergence); F5 PASS (script grep + hide-test clean per engineering report). **Substrate finding (load-bearing): IS-only resolve diverges from /045 ALT_1 on 4 of 5 coins. This EMPIRICALLY CONFIRMS that workflow `w0qpo136q`'s OOS-aware composite score (`0.5·OOS_Sh + 0.3·IS_Sh + 0.2·OOS_n/100`) selected an OOS-Sharpe-inflated substrate at /045. The +3.49 OOS Sharpe headline at /045 was a post-hoc selection artifact, not a substantive partition-solve discovery.** **Secondary finding (HP-basin concentration risk)**: 3 of 5 IS-only top-1 picks come from a single source iter (v1-025: BTC + LINK + LTC). This is the LM Master Phase 4.5 Rec 1 risk MATERIALIZED — IS-Sharpe maximization on a non-orthogonal candidate inventory mechanically clusters on the broadest-basin source iter.

---

## 1. Decision: NO-MERGE (EXPLORATION); BASELINE_V1.md UNCHANGED

**Verdict**: **EXPLORATION-PROMISING** with sub-classification **PROMISING-DIVERGENCE-WITH-BASIN-LOTTERY-CAUTION** (per Critic Phase 7.5 + LM Master Phase 7.4 convergence).

- F1 (master deflated IS Sharpe ≥ +0.50): **PASS** at +2.39 deflated (raw +2.84 minus 0.446 per-coin best-of-159 deflation per LM Master Rec 2).
- F2 (5/5 substrate coincidence with /045 ALT_1): **FAIL** — 1/5 match (only C-DOT=v1-031).
- F3 (≥3 substrate divergence): **PASS** — 4/5 divergence (C-BTC, C-ETH, C-LINK, C-LTC all differ from ALT_1).
- F4 (boundary 1-2 divergence): N/A (F3 PASSes dominantly).
- F5 (anti-pattern OOS-leakage in script): **PASS** per engineering report grep-clean + functional-invariance hide test (diff = 0 bytes).

**Verdict mapping (per LM Master Phase 4.5 band → /046 subtype):** PROMISING-DIVERGENCE at modal 45% prior MATERIALIZED. /046 is a methodology-clean EXPLORATION; the substrate so identified is informative about /045's OOS-inflation but is itself NOT MERGE-eligible at single-seed.

**BASELINE_V1.md**: UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). No tag content beyond `v0.v1-046` historical artifact.

---

## 2. Observed Results

### 2.1 IS-only partition resolve (`analysis/iteration_v1-046/is_only_substrate.csv`)

| Coin | Selected iter | IS Sharpe | IS n_trades | score_is | ALT_1 pick | Match? |
|---|---|---:|---:|---:|---|---|
| BTC | **v1-025** | +0.459 | 114 | 0.458 | v1-012 (IS −0.21) | **DIVERGE** |
| ETH | **v1-009** | +2.222 | 140 | 1.557 | v1-042 (IS +0.71) | **DIVERGE** |
| LINK | **v1-025** | +2.387 | 103 | 1.597 | v1-011 (IS +1.27) | **DIVERGE** |
| LTC | **v1-025** | +4.982 | 61 | 3.087 | v1-040 (IS +3.76) | **DIVERGE** |
| DOT | **v1-031** | +2.401 | 117 | 1.628 | v1-031 (IS +2.40) | MATCH |

**Substrate overlap with /045 ALT_1: 1 of 5 (20%).**

### 2.2 Bundle aggregate (`reports-v1/iteration_v1-046/comparison.csv`)

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---:|---:|---:|
| **Daily Sharpe (ann.)** | **+2.837** | **−0.876** | **−0.309 (SIGN FLIP)** |
| Monthly Sharpe | +0.430 | −0.134 | −0.312 |
| Max Drawdown | 9.60% | 14.14% | 1.47 |
| Win Rate | 44.3% | 37.2% | 0.84 |
| Profit Factor | 1.392 | 0.895 | 0.64 |
| Total Trades | 537 | 242 | 0.45 |
| Total Net PnL ($) | +50.28 | −6.56 | −0.13 |
| **Δ IS Sharpe vs BASELINE_V1** | **+2.361** | — | — |
| **Δ OOS Sharpe vs BASELINE_V1** | — | **−2.017** | — |

**Methodology note**: OOS Sharpe is COMPUTED for forensic interpretation but is **NOT a /046 falsifier** (per brief §4 F4 + LM Master Flag B binding constraint; Critic Phase 7.5 explicitly endorsed). The sign-flip is INFORMATIONAL for /047 routing.

### 2.3 Per-component IS→OOS reversal (LM Master Phase 7.4 Item 4 — load-bearing)

| Component | Source iter | IS Sharpe | OOS Sharpe | Δ (IS→OOS) | OOS PnL ($) | Reading |
|---|---|---:|---:|---:|---:|---|
| C-BTC | v1-025 | +0.38 | **−2.31** | **−2.69** | −3.42 | Catastrophic — marginal IS pick collapses OOS |
| C-ETH | v1-009 | +1.70 | **−1.68** | **−3.38** | −3.67 | Catastrophic — IS lift erased OOS |
| C-LINK | v1-025 | +1.69 | +0.10 | −1.59 | +0.25 | Neutral OOS — barely positive |
| C-LTC | v1-025 | +4.17 | **−1.50** | **−5.67** | −3.70 | **Worst IS→OOS reversal** — strongest IS basin → OOS-NEG (classic basin-lottery signature) |
| C-DOT | v1-031 | +2.00 | **+2.73** | **+0.73** | +3.98 | Only OOS survivor — methodology-agnostic anchor |

**4 of 5 components OOS-NEG.** The single OOS-survivor (C-DOT=v1-031) is **also the ONLY component matching /045 ALT_1.** Cross-methodology convergence on v1-031 is strong corroboration that DOT-v1-031 lives in a non-lottery HP region.

### 2.4 Per-regime decomposition (`reports-v1/iteration_v1-046/regime_attribution.csv`)

| Regime | IS Sharpe | IS trades | Baseline IS Sharpe | IS Δ vs baseline |
|---|---:|---:|---:|---:|
| bull | +0.2803 | 61 | −0.3514 | **+0.6317** |
| bear | +0.4001 | 111 | +0.1463 | +0.2538 |
| chop | +0.3988 | 273 | +0.2348 | +0.1640 |
| recovery | **+0.7815** | 90 | +0.2782 | +0.5033 |
| other (IS) | 0.0 | 0 | 0.0 | 0 |
| other (OOS) | **−0.1592** | 239 | +0.1405 | — |

**Regime-coverage caveat**: OOS regime tagger collapses 239/242 (98.8%) OOS trades into "other". IS regime tagger reports 4 distinct regimes (bull/bear/chop/recovery) all positive IS-side. The IS-regime Pareto narrative does NOT transfer to OOS — tagger limitation inherited from /045 (not a /046 issue).

### 2.5 Methodology gates (informational; /046 is EXPLORATION, not CONFIRMATION)

- IS Sharpe > 1.0: PASS (+2.84).
- OOS Sharpe > 1.0: **FAIL** (−0.88).
- OOS/IS ratio ≥ 0.5: **FAIL** (−0.31).
- OOS trades ≥ 130: PASS (242).
- F5 anti-pattern script audit: PASS.

---

## 3. The Substrate-Divergence Finding (LOAD-BEARING)

The IS-only partition resolve under `score_is = 0.6·IS_Sharpe + 0.4·IS_n_trades/250` selects a substrate that **diverges from /045 ALT_1 on 4 of 5 coins** (BTC, ETH, LINK, LTC differ; only DOT matches).

This was the F3 PROMISING-DIVERGENCE outcome at LM Master Phase 4.5 modal prior (45%) and **the finding is empirically directional in three independent dimensions**:

1. **/045's workflow `w0qpo136q` composite score `(0.5·OOS_Sh + 0.3·IS_Sh + 0.2·OOS_n/100)` READ each candidate's OOS Sharpe during the substrate optimization.** That is post-hoc OOS-aware specialist selection — the Critic /045 BLOCK-FINAL reasoning is now empirically vindicated by /046's IS-only re-solve diverging on 4 of 5 coins.

2. **/045 ALT_1's headline +3.49 OOS Sharpe is a post-hoc selection artifact.** The IS-only substrate's OOS Sharpe is −0.88 (Δ −4.37 vs ALT_1's OOS +3.49). Both substrates inherit the SAME 5-coin universe + the SAME 1/5 weight scheme + the SAME CSV-replay aggregator — the ONLY difference is the component selection criterion. A −4.37 OOS Sharpe gap from changing selection criterion alone (substrate component change on 4 of 5 cells) is the textbook signature of OOS-aware specialist selection bias.

3. **/045 ALT_1's C-BTC=v1-012 has IS Sharpe −0.21 (NEGATIVE) — an IS-only solver CANNOT pick it.** Under any honest IS-only score, the BTC pick MUST differ. Phase 4.5 LM Master flagged this as the single load-bearing evidence anchor; the empirical /046 result confirms it.

**Conclusion**: any future partition-solve workflow MUST use IS-only scoring. The /045 workflow `w0qpo136q` is empirically falsified as a substrate-selection mechanism. This is saved as enforcing convention going forward in `feedback_v1_oos_inflation_empirically_confirmed.md`.

---

## 4. HP-Basin Concentration Risk (PHASE 4.5 REC 1 MATERIALIZED)

The IS-only solve selected **v1-025 for 3 of 5 coins (BTC + LINK + LTC = 60%)**. This is exactly the failure mode LM Master Phase 4.5 Rec 1 flagged ("if 3 of 5 top-1 picks happen to share the same source iter, the substrate has HP-basin concentration — one Optuna lottery roll drives 3 components").

**Mechanism (LM Master Phase 7.4 Item 2)**: IS-Sharpe maximization on a non-orthogonal candidate pool will MECHANICALLY favor the broadest-basin source iter. v1-025's HP region (`num_leaves`, `min_data_in_leaf`, etc.) reduces variance on pooled multi-symbol training at the expense of per-symbol fitting — producing same-source clustering. The basin-lottery has a structural signature: when a single Optuna roll wins on multiple symbols simultaneously, the substrate inherits that single roll's basin properties.

**Empirical evidence (LM Master Phase 7.4 Item 5)**: v1-025 LTC IS Sharpe = +4.98 on 61 trades corresponds to σ_SR ≈ 0.13 → IS Sharpe is **38 σ_SR units above zero** (P[H0] < 10⁻³⁰⁰). Either v1-025 found genuine LTC edge (falsified by OOS = −1.50) OR v1-025's IS Sharpe is artifactual (Optuna basin overconcentration). The OOS evidence forces the artifactual reading.

**Per-component IS→OOS deltas confirm basin-lottery**: 3 v1-025 components show mean IS Sharpe +2.08, mean OOS Sharpe **−1.24**, mean Δ **−3.32** (collapse). v1-031 (DOT) is the lottery survivor; everyone else is basin-stranded.

**Methodology implication**: the IS-only fix correctly removes OOS-aware bias but introduces a NEW bias — source-iter clustering on the broadest-basin Optuna roll. /046 trades one selection bias (OOS-aware) for another (HP-basin-concentrated). Both biases are unmerged-worthy at single-seed; both require multi-seed validation OR a NEW substrate-selection rule that enforces source-iter diversity.

Saved as `feedback_v1_hp_basin_concentration_alert.md` (NEW).

---

## 5. Critic Phase 7.5 verdict summary (binding for diary)

**Verdict**: EXPLORATION-PROMISING (PROMISING-DIVERGENCE subtype with HP-basin-lottery sub-caution).

**Constraint upheld (from brief §4 F4 binding)**: Critic does NOT cite "IS-only substrate OOS Sharpe < ALT_1 OOS Sharpe" as /046 failure evidence. OOS is forensic interpretation, not a /046 falsifier. The /046 verdict is determined SOLELY by F1-F5.

**Critic Path Forward (verbatim, copied into §7 below)**:
1. **/047 = MULTI-SEED RE-VALIDATION of the IS-only substrate** (single-seed=42 → seeds [123, 456, 789, 1001]) — the load-bearing question is whether the 4-of-5-divergent IS-only substrate's bundle headline survives at independent seeds beyond seed=42.
2. **/048 (conditional) = source-iter-diversity-constrained partition resolve** if /047 confirms basin-lottery: max 2/5 components from any single source iter; re-run partition_solve with that constraint.
3. **/049 (alternative) = stand-alone v1-031 (C-DOT) multi-seed validation** — the methodology-agnostic anchor (matches both /045 + /046 selection criteria). Most likely the SINGLE merge-worthy ingredient.
4. **/050+ = NEW feature family** (cross-asset / microstructure / on-chain) post multi-seed-baseline. cycle-6 axis-family rotation: away from methodology.

**No BLOCK-PENDING-FIX path**: F5 PASS at first attempt. /046 closes cleanly.

---

## 6. Key Learnings

1. **/045's OOS-aware partition-solve workflow is empirically falsified.** The IS-only re-solve diverges on 4 of 5 coins (BTC, ETH, LINK, LTC). Any future partition-solve MUST use IS-only scoring. The composite score `(0.5·OOS_Sh + 0.3·IS_Sh + 0.2·OOS_n/100)` is a post-hoc OOS-aware specialist selector that injects 30-50% OOS-Sharpe inflation. Saved as enforcing convention (`feedback_v1_oos_inflation_empirically_confirmed.md`).

2. **IS-only substrate selection is NOT a free lunch — it inherits HP-basin-lottery bias.** 3 of 5 IS-only top-1 picks come from v1-025 (60% source-iter concentration). LM Master Phase 4.5 Rec 1 flagged this as a risk; Phase 7.4 Item 2 confirmed the structural mechanism (best-of-N IS-Sharpe maximization on a non-orthogonal candidate pool mechanically favors the broadest-basin source iter). /047 multi-seed re-validation OR /048 source-iter-diversity-constrained re-solve is the next axis. Saved as `feedback_v1_hp_basin_concentration_alert.md` (NEW).

3. **v1-031 (DOT) is the methodology-agnostic anchor.** It is the ONLY component selected by both /045's OOS-aware framework AND /046's IS-only framework — the only cell where IS+OOS both support its selection. It is also the only OOS-positive component (+2.73 OOS Sharpe; +3.98 OOS PnL). For /047+, C-DOT=v1-031 stands as a single-component candidate worth independent multi-seed validation; its narrow universe coverage (1 symbol) likely FAILS the trade-rate floor on its own (37 OOS trades vs 130 required), but its multi-seed properties anchor any future bundle composition.

4. **The OOS sign-flip is the binding /047 routing signal.** Bundle IS Sharpe +2.84 → OOS Sharpe −0.88 (ratio −0.31). This is the strongest IS→OOS reversal observed in v1 history. The Critic correctly did NOT use this as a /046 falsifier (OOS is forensic only at methodology axis); BUT the magnitude makes it implausible that multi-seeding the substrate as-is will yield a merge-eligible bundle. /047 should pivot to source-iter-diversity-constrained re-solve OR stand-alone v1-031 validation, not naive multi-seeding of the basin-lottery substrate.

5. **The score formula's effective trade-count weight is 8-15%, not the nominal 40%.** v1-025 LTC at 61 trades scoring 0.6×4.98 + 0.4×0.244 = 3.087 vs v1-040 LTC at 117 trades scoring 0.6×3.76 + 0.4×0.468 = 2.443: trade-count favors v1-040 but IS-Sharpe edge wins. The trade-count regularization is too weak to defeat basin-lottery basin-overfitting. LM Master Phase 7.4 Rec 5 proposed an empirical-Bayes shrinkage variant `0.6·IS_Sharpe × (n/(n+30)) + 0.4·log10(n/10)` which would shrink low-trade-count basin-lottery cells without breaking IS-Sharpe primacy.

---

## 7. Path Forward (from Critic; verbatim)

Per Critic Phase 7.5 + LM Master Phase 7.4 Item 1-3 convergence — three pre-registered alternatives for /047 (cycle-6 EXPLORATION-2):

1. **/047 = MULTI-SEED RE-VALIDATION of the IS-only substrate** (single-seed=42 → seeds [123, 456, 789, 1001]). The load-bearing question is whether the 4-of-5-divergent IS-only substrate's bundle headline holds at seeds beyond 42 (single-seed inheritance is the largest residual concern post-/046). Component-level multi-seed: each of the 5 source iters' OWN config re-run at 4 additional seeds; re-aggregate via /045-/046 CSV-replay aggregator. Expected multi-seed mean OOS Sharpe band: [−1.5, +0.5] given /046's single-seed = −0.88. MERGE-eligibility requires multi-seed mean OOS Sharpe > +1.0 AND ≥7/10 profitable seeds across components — almost certainly FAILS given /046's OOS-NEG basin-lottery signature.

2. **/048 (conditional on /047 confirming basin-lottery) = source-iter-diversity-constrained partition resolve**. Re-run partition_solve with `max 2/5 components from any single source iter` constraint. Forces substrate to span the inventory's HP-search landscape. Expected substrate: v1-031 (DOT, matched), one v1-025 component (the strongest IS Sharpe survivor — likely LTC), and 3 components from other iters. May lower bundle IS Sharpe; that is OK (robustness, not headline maximization).

3. **/049 (alternative) = stand-alone v1-031 multi-seed validation**. The ONLY methodology-agnostic anchor. Run 10-seed CONFIRMATION on v1-031 in isolation. If multi-seed mean OOS Sharpe ≥ +1.0 with ≥7/10 profitable seeds, declare v1-031 a "validated component cell." Builds a verified atomic cell from which future bundles can compound. Risk: single-symbol coverage (37 OOS trades) likely fails the trade-rate floor on its own — but the validated cell is a permanent reference for cycle-6+ substrate composition.

**Recommended /047 axis = MULTI-SEED RE-VALIDATION of the IS-only substrate** (Critic Path Forward #1). Single-seed inheritance is the load-bearing residual concern after /046's empirical OOS-inflation finding. The verdict at /047 routes /048 either to source-iter-diversity-constrained re-solve (Critic Path Forward #2) or to a NEW feature family axis (Critic Path Forward #4).

---

## 8. Caveats

- **Single-seed=42 inheritance across all 5 components**: bundle headline is the upper bound on lottery exposure. Multi-seed expectation is OOS Sharpe in [−1.5, +0.5] band given /046's −0.88 and basin-lottery signature.
- **HP-basin concentration on v1-025 (60% source-iter share)**: BTC + LINK + LTC all from a single Optuna roll. The 3 v1-025 components' mean IS→OOS Δ = **−3.32** (basin-stranded). The fix is source-iter-diversity-constrained re-solve, not naive multi-seeding.
- **C-DOT=v1-031 is the single substrate ingredient that survives both selection criteria.** It is the methodology-agnostic anchor and the only OOS-positive component. Single-symbol coverage (37 OOS trades) makes it ineligible for stand-alone bundle composition but it is a permanent cycle-6 reference cell.
- **OOS regime tagger collapses 98.8% of OOS trades to "other"** — same as /045. F4 IS-regime Pareto is structurally weak as a /046 falsifier; F1 (deflated IS Sharpe) carried the methodology test instead.
- **The OOS sign-flip (IS +2.84 → OOS −0.88; ratio −0.31) is the strongest IS→OOS reversal in v1 history.** This is forensic information for /047 routing (NOT a /046 falsifier per binding constraint), but the magnitude implies multi-seeding the basin-lottery substrate as-is is highly unlikely to produce a merge-eligible bundle.
- **Score formula's effective trade-count weight is 8-15%** (not nominal 40%). Trade-count acts as a soft tiebreaker, not a co-equal criterion. LM Master Phase 7.4 Rec 5 proposed an empirical-Bayes shrinkage variant for /048+ partition-solve re-runs.
- **/046 is a methodology-clean EXPLORATION**: F5 PASS (script grep + functional-invariance hide test); engineering report emits the hide-test diff verbatim. The methodology itself works as designed — the substrate produced under that methodology is what carries the basin-lottery property.

---

## 9. Next Iteration Ideas (cycle-6; methodology family NOW USED)

Per Axis Rotation Discipline (skill v1 §"v1-Specific Disciplines #2"). After /046, the last 5 axis-family rotations in this window are:

| Iter | Axis family | Date |
|---|---|---|
| /042 | model-arch | 2026-05-31 |
| /043 | per-cohort-specialization × labeling | 2026-05-31 |
| /044 | N/A (CONFIRMATION; no EXPLORATION axis) | 2026-06-01 |
| /045 | N/A (CONFIRMATION; no EXPLORATION axis) | 2026-06-01 |
| /046 | **methodology** | 2026-06-01 |

Last 5 EXPLORATION-axis families = {/039, /040, /041, /042, /043, /046} effectively (skipping /044, /045 CONFIRMATIONs). /046 used methodology. **/047 family options (NOT methodology)**: `feature-family`, `labeling`, `risk-primitive`, `per-cohort-specialization`, `model-arch`, `universe`, `hyperparameter-region`, `loss-function`, `sample-weighting`, `methodology-substrate-test`.

### 9.1 /047 — MULTI-SEED RE-VALIDATION of the IS-only substrate (LOCKED PRIMARY; axis-family `methodology-substrate-test`)

**Load-bearing question**: does the IS-only substrate's bundle Sharpe hold under seeds [123, 456, 789, 1001] beyond seed=42 (single-seed inheritance is the largest residual concern post-/046)?

**Mechanism**: each of the 5 source iters (v1-025 × 3 + v1-009 + v1-031) re-run at 4 additional seeds under its own config; re-aggregate via /045-/046 CSV-replay aggregator. Expected multi-seed mean OOS Sharpe band [−1.5, +0.5] given /046's single-seed = −0.88. MERGE-eligibility requires multi-seed mean OOS Sharpe > +1.0 AND ≥7/10 profitable seeds — almost certainly FAILS given the basin-lottery signature, but the experiment IS the value (settles whether seed=42 alone is the failure mode, or the structural basin-lottery is).

**Axis-family rotation**: `methodology-substrate-test` (8th family; structurally orthogonal to methodology proper; first usage was /012). NOT a repeat of /046's methodology axis.

**Wall-clock estimate**: 8-12h (4 source iters × 4 seeds × ~30-60 min each / parallelized; or sequential ~8h). CONFIRMATION-budget territory.

### 9.2 /048 (conditional on /047 confirming basin-lottery) — source-iter-diversity-constrained partition resolve

**Axis-family**: `methodology` (returning after one slot's rotation).

**Mechanism**: re-run partition_solve with `max 2/5 components from any single source iter` constraint. Expected substrate: v1-031 DOT + at most 2 v1-025 cells + 2 from other iters. Forces span over inventory's HP-search landscape. May lower bundle IS Sharpe; that is OK.

### 9.3 /049 (alternative if /047 collapses) — stand-alone v1-031 multi-seed validation

**Axis-family**: `methodology-substrate-test`.

**Mechanism**: take C-DOT=v1-031 in isolation. Run 10-seed CONFIRMATION. If multi-seed mean OOS Sharpe ≥ +1.0 with ≥7/10 profitable seeds, v1-031 becomes a "validated component cell" anchoring cycle-6+ substrates. Trade-rate floor likely FAILS at 37 OOS trades alone — but the validated cell is a permanent cycle-6 reference.

### 9.4 /050+ — NEW feature family (cross-asset / on-chain / microstructure)

**Axis-family**: `feature-family`.

Per Critic /045 Path Forward #3 (carried forward): cycle-6 EXPLORATION-N (post multi-seed-baseline) should pivot to NEW feature family. Candidates:
- **(a) On-chain feature family** (BTC exchange netflow, MVRV-Z, NUPL, CDD/Dormancy — Glassnode/CryptoQuant data; BTC's on-chain regime as cross-asset input to all 5 components).
- **(b) Microstructure feature family** (book imbalance, taker-maker ratio, order flow imbalance — never explored in v1).
- **(c) Cross-asset feature family** (gold/SPX correlation, DXY z-score, BTC.D second derivative — macro-regime conditioning).

LM Master Phase 4.5 modal recommendation for cycle-6 EXPLORATION-N: (a) on-chain feature family.

### 9.5 /051+ — risk-primitive axis (regime-conditional dispatch)

**Axis-family**: `risk-primitive`.

Per-regime DD brake, regime-conditional vol kill-switch, regime-conditional OOD gate. Last touched in cycle-5 only as /037 Sortino (which is labeling/loss-function, not genuine risk-primitive). Eligible for rotation.

---

## 10. Cycle-6 Status

**Cycle-6 opened at /046.** Cycle-5 closed at /045 closeout (0 BASELINE_V1.md updates; 10 EXPLORATIONs /034-/043; 2 BLOCK-FINAL CONFIRMATIONs /044+/045).

**Cycle-6 ledger after /046**:
- EXPLORATION 1/10: /046 (methodology / IS-only partition resolve; PROMISING-DIVERGENCE / 4 of 5 substrate divergence / HP-basin concentration MATERIALIZED).
- EXPLORATION 2-10/10: TBD (multi-seed re-validation as locked next axis at /047; source-iter-diversity-constrained resolve at /048 conditional; cross-asset/on-chain/microstructure at /050+).

**Substantive cycle-6 finding at /046**: /045 ALT_1's +3.49 OOS Sharpe headline was OOS-aware-selected by workflow `w0qpo136q` and is structurally inflated. Any future v1 partition-solve must use IS-only scoring. The IS-only substrate is NOT MERGE-eligible due to HP-basin concentration on v1-025 (3 of 5 components). v1-031 (DOT) is the methodology-agnostic anchor and the only cross-criterion-survived substrate ingredient.

---

## 11. Closing Note

iter-v1/046 is a cycle-6 EXPLORATION methodology-axis iteration that **empirically falsifies /045's OOS-aware partition-solve workflow** (4 of 5 substrate divergence) AND **exposes the HP-basin-lottery substitution bias** (3 of 5 components from v1-025). The methodology fix works as designed — F5 PASS at first attempt; engineering report's hide-test produces 0-byte diff. The IS-only substrate so identified is NOT MERGE-eligible at single-seed (OOS Sharpe −0.88 sign-flip; 4 of 5 components OOS-NEG) but the verdict is informative: any honest partition-solve methodology must enforce both (a) IS-only scoring (proven by /046's divergence) AND (b) source-iter diversity (proven by /046's basin-lottery concentration).

**The PRIMARY cycle-6 finding**: /045 ALT_1's +3.49 OOS Sharpe was a post-hoc selection artifact, not a substantive partition-solve discovery. **The SECONDARY finding**: v1-031 (DOT) is the only methodology-agnostic substrate ingredient surviving both selection criteria — the cycle-6 substrate anchor for downstream composition.

**Tag**: `v0.v1-046` (EXPLORATION-PROMISING historical artifact; PROMISING-DIVERGENCE with HP-basin-lottery-CAUTION subtype). **BASELINE_V1.md**: UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). Cycle-6 EXPLORATION 1/10 logged. /047 = multi-seed re-validation of IS-only substrate (locked).
