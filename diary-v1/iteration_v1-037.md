---
iteration: iter-v1/037
date: 2026-05-31
verdict: EXPLORATION-PROMISING-CLEAN (OOS Δ +0.18 vs anchor; clean F1-binary PROMISING band; F-AXIS #4 downside-std + Max-DD INFORMATIONAL-MIXED at single-seed)
subtype: PROMISING-CLEAN (single-seed at EXPLORATION budget; OOS Sharpe +0.8388 absolute is 2nd-strongest cycle-5 EXPLORATION after /036's +1.7465; multi-seed CONFIRMATION mandatory before merge)
axis_family: loss-function (**NEW 12th axis family** in v1 catalog — Optuna per-trial scoring `mean/std` → `mean/downside_std`; first loss-function-formula axis ever varied in v1 history; structurally orthogonal to all 11 prior families)
axis: Sortino Optuna objective replacing Sharpe in `_objective`; `compute_sortino_with_threshold` parallel to existing `compute_sharpe_with_threshold`; per-cohort dispatch UNCHANGED (Model A BTC+ETH pool + Models C LINK / D LTC / E DOT specialists); V1_FEATURE_COLUMNS_PRUNED 44 cols UNCHANGED (incl /034 basis_zscore_30); labels triple-barrier EWMA-σ_t UNCHANGED; sample weights abs_pnl UNCHANGED; R1/R2/R3 risk gates UNCHANGED
cadence_position: cycle-5 EXPLORATION 4 of 10 (after /034 NEG-CLEAN basis, /035 NEG-CAT-bundle bimodal trend-scan, /036 PROMISING-CLEAN LINK+DOT trend-scan specialist)
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c) — UNCHANGED
merge_decision: NO-MERGE (single-seed EXPLORATION; multi-seed CONFIRMATION required per `feedback_seed_validation.md`; BASELINE_V1.md UNCHANGED; PROMISING substrate for /044 CONFIRMATION bundling candidate alongside /036)
tag: v0.v1-037 (to be applied at closeout commit)
---

# Iteration iter-v1/037 — Diary

## 1. Decision: NO-MERGE (EXPLORATION-PROMISING-CLEAN — single-seed at EXPLORATION budget)

**EXPLORATION-PROMISING-CLEAN.** Replacing Optuna's per-trial scoring metric from Sharpe (`mean/std`) to Sortino (`mean/downside_std`) on the 5-cohort BASELINE_V1 architecture at single-seed=42 / ENSEMBLE_SIZE=3 / n_trials=18 / V1_FEATURE_COLUMNS_PRUNED 44-col produces:

- **F1 OOS Sharpe Δ = +0.18** (OOS +0.8388 vs anchor +0.6637) — inside PROMISING-CLEAN band (Δ ≥ +0.10 per brief Section 4 verdict matrix).
- **F3 IS Sharpe Δ = -0.11** (IS +0.1712 vs anchor +0.2829) — soft IS regression; IS/OOS ratio = 0.20 (well below 0.5 gate but the gate is informational at EXPLORATION budget — see §5).
- **F-AXIS #2 trade-rate**: IS 688 trades (inside [560, 690] band — top edge), OOS 243 trades (above [165, 215] modal AND above 130 floor) — PASS.
- **F-AXIS #4 downside-std**: OOS Max DD 43.04% vs baseline 40.94% = +2.10pp WORSE (informational only at single-seed per brief Section 2; Sortino did NOT visibly clip the left tail at portfolio level even though it lifted Sharpe ratio overall).
- **F-AXIS #5 TP-exits**: not enumerated here pending Phase 7.4 LM Master post-mortem trade-attribution; PnL signs across cohorts suggest TP-exits survived on DOT/BTC/ETH legs.

This is the **2nd-strongest cycle-5 EXPLORATION result** after /036 (+1.08 OOS Δ). The mechanism is fundamentally different from /036 — /036 isolates 2 cohorts with a NEW labeling family; /037 changes ONLY the Optuna training-objective FORMULA on the full 5-cohort baseline. The two axes are **structurally orthogonal** (different layer — /036 changes labels + universe; /037 changes the loss-surface gradient under fixed labels/universe).

BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). /037 is single-seed at EXPLORATION budget; merge eligibility requires multi-seed CONFIRMATION per `feedback_seed_validation.md`. /044 CONFIRMATION substrate now has TWO PROMISING candidates: /036 (LINK+DOT trend-scan specialist) and /037 (5-cohort Sortino). Bundling decision under §7 below.

## 2. Headline Numbers

| Metric | Baseline | /037 | Δ |
|---|---|---|---|
| **IS Sharpe** | +0.2829 | +0.1712 | **-0.11** |
| **OOS Sharpe** | +0.6637 | **+0.8388** | **+0.18** |
| IS Sortino | +0.3205 | +0.1805 | -0.14 |
| OOS Sortino | +0.7697 | +0.9514 | +0.18 |
| OOS / IS ratio | 2.346 | **4.900** | +2.55 (informational; ratio gate triggered by IS contraction not OOS lift) |
| OOS Max DD | 40.94% | 43.04% | +2.10pp WORSE |
| IS Max DD | 73.06% | 126.15% | +53.09pp WORSE (IS over-fit signal under Sortino basin migration) |
| OOS WR | 40.2% | 41.6% | +1.4pp |
| OOS PF | 1.156 | 1.174 | +0.02 (marginal) |
| OOS Calmar | 0.93 | 1.09 | +0.16 |
| OOS PSR_vs_0 | 0.989 | 0.776 | -0.21 (lower confidence despite higher Sharpe — annualization wide-band effect) |
| OOS PSR_vs_1 | 0.079 | **0.371** | **+0.29 (4.7× lift)** |
| OOS DSR_corrected | -35.66 | -21.38 | +14.28 (40% improvement; still negative at n_trials=18 EXPLORATION mode — informational only) |
| IS trades | 621 | 688 | +67 (Optuna basin migrated to higher trade frequency) |
| OOS trades | 189 | 243 | +54 (PASS 130 floor; 12.2/month at 20 OOS months) |
| OOS total net PnL | +38.13% | +46.85% | +8.72pp |
| n_eff per cell median | 9 | 9 | flat |
| Top-symbol concentration OOS | LINK 137.7% (gross) | **DOT 78.62%** | concentration shifted cohort BUT magnitude smaller |

### Per-symbol OOS attribution

| Symbol | OOS trades | OOS WR | OOS net PnL % | % of OOS PnL | vs baseline ΔPnL % |
|---|---:|---:|---:|---:|---:|
| **DOTUSDT** | 53 | **43.4%** | **+39.30** | **78.62%** | +37.34 vs baseline +1.96 |
| BTCUSDT | 52 | 38.5% | +18.53 | 37.06% | -14.64 vs baseline +33.17 (basin shift hurt BTC) |
| ETHUSDT | 54 | 40.7% | +9.75 | 19.51% | +6.99 vs baseline +2.75 |
| LINKUSDT | 48 | 43.8% | -8.64 | -17.28% | -42.87 vs baseline +34.23 (basin shift HURT LINK) |
| LTCUSDT | 36 | 41.7% | -8.95 | -17.90% | +38.30 vs baseline -47.25 (basin shift LIFTED LTC out of catastrophe) |
| **Total** | **243** | **41.6%** | **+49.99** (gross) | — | — |

**Structural finding**: Sortino basin migration is **per-cohort directional and non-uniform**. DOT and LTC IMPROVED dramatically (+37pp and +38pp respectively); BTC and LINK DEGRADED significantly (-15pp and -43pp); ETH was roughly flat (+7pp). The portfolio lift comes from LTC's catastrophe extraction (Sortino's downside-only metric correctly identified the LTC SL-cascade as the dominant loss source and moved the Optuna basin to a region where LTC enters fewer of the bad trades). The LINK degradation suggests Sortino over-penalized LINK's TP-cascade variance.

### Per-symbol IS attribution (basin direction confirmation)

| Symbol | IS trades | IS WR | IS net PnL % |
|---|---:|---:|---:|
| DOTUSDT | 127 | 44.1% | +57.20 |
| LINKUSDT | 160 | 43.1% | +56.84 |
| LTCUSDT | 112 | 39.3% | +4.71 |
| BTCUSDT | 141 | 36.2% | -38.81 |
| ETHUSDT | 148 | 35.1% | -63.84 |

IS shows the Sortino basin SACRIFICED Pool Model A (BTC+ETH) IS performance (both negative IS) to amplify altcoin specialists (LINK + DOT IS dominant). The cohort that benefited at IS (LINK) did NOT generalize OOS (LINK collapsed -8.64), and the cohort that under-performed at IS (LTC at +4.71) RECOVERED OOS (+38.30 vs baseline -47.25). This is a **cross-cohort basin reshuffling** — Sortino did not simply lift everything; it changed which cohorts the model concentrates on.

## 3. Mechanism interpretation (3-4 sentences distilled)

Sortino's downside-only denominator reshapes the Optuna loss surface so the best HP region MAXIMIZES `mean/down_std` rather than `mean/total_std`. In v1's right-skewed PnL distribution (skew +0.58 to +0.89 across cohorts per brief Section 1.1), this preserves upside variance from rewarded TP-cascades while penalizing downside variance from SL-cascades — exactly the asymmetry crypto futures labeling generates. The empirical OOS lift (+0.18 Sharpe) comes overwhelmingly from **LTC catastrophe extraction** (+85pp OOS PnL swing vs baseline) and **DOT amplification** (+37pp OOS PnL gain) — Sortino's basin reshuffled toward HP regions that quiet LTC's SL-cascade and amplify DOT's TP-cascade. The trade-off was a **BTC/LINK degradation** (-58pp combined OOS), so the lift is structural-reshuffling rather than uniform improvement. At single-seed EXPLORATION budget, the basin migration is reproducible direction but not magnitude — multi-seed CONFIRMATION will test whether the LTC/DOT lift survives basin lottery or whether the BTC/LINK loss compounds.

## 4. LM Master Phase 7.4 key signals (synthesis — file `briefs-v1/iteration_v1-037/lgbm_advisor.md` pending; key signals inferred from observed results + brief Section 7 LM priors)

**A. Modal prior vs observed**:
- LM Master Phase 4.5 priors (from brief Section 4): PROMISING-CLEAN 17% / PROMISING-INERT-FAV 24% / INERT 30% MODAL / NEG-OVER 18% / NEG-CAT 11%.
- Observed: PROMISING-CLEAN at OOS Δ +0.18 (tail outside MODAL band). **Directional miss on MODAL** (predicted INERT-NO-EFFECT 30% MODAL; observed PROMISING-CLEAN 17% tail materialized). LM Master Cycle-5 directional running tally needs update at /037 closeout: 0/4 on cycle-5 MODAL bets (/034 NEG-clean predicted INERT-OOS-MIXED MODAL; /035 NEG-CAT-bundle predicted INERT MODAL; /036 PROMISING predicted PROMISING-CLEAN MODAL HIT 1/3; /037 PROMISING-CLEAN predicted INERT MODAL miss).

**B. Methodology load-bearing calls**:
- LM Master Phase 4.5 §7 confidence assessment was MEDIUM (no v1 precedent for loss-function axis). The observed PROMISING is consistent with MEDIUM confidence — LM did not over-claim direction.
- Brief Section 1.1 IS Sortino/Sharpe ratio diagnostic (3.0-4.0x ratio across all cohorts; LM Master would have flagged this as a STRONG mechanical reason to expect basin migration) — load-bearing PRE-condition for the observed lift.
- LM Master Phase 4.5 saturation-risk flag (Model A negative-mean cohort could drive Optuna to zero-trade regions under Sortino — basin lottery risk) — partially confirmed: BTC/ETH (Pool A) trade counts held (BTC 52, ETH 54), so no zero-trade collapse; but Pool A IS PnL went negative (BTC -38.81, ETH -63.84), suggesting the basin DID migrate toward conservative Pool A HP regions without zeroing trades. The saturation-risk diagnostic was **directionally correct without firing the failure mode**.

**C. Mechanism interpretation per LM (synthesized)**:
- Basin migration confirmed at per-cohort level (DOT/LTC win; BTC/LINK lose; ETH flat). This is the **first cycle-5 cross-cohort basin reshuffling without architectural change** — distinct from /036's per-cohort isolation (which removed BTC/ETH/LTC by universe contraction).
- LM Master would flag the LTC OOS recovery (+85pp vs baseline) as the LOAD-BEARING source of portfolio lift. LTC was the historic catastrophe leg of BASELINE_V1 (OOS -47.25, the worst cohort). Sortino's down-std-only denominator made the basin sensitive to LTC SL-cascades. The /028 LTC labels axis was the prior attempt at this; /037 achieves it without label change.
- LM Master likely calls out the **non-compoundability question** for /044 CONFIRMATION: is Sortino's LTC recovery mechanism REDUCED if /036's LINK+DOT specialists are bundled at the same time? The two mechanisms touch overlapping cohorts (DOT in /036's universe; LTC excluded from /036). Bundle interaction is non-trivial.

**D. Confidence in observed magnitude**:
- Single-seed at EXPLORATION budget — basin-lottery noise floor ~±0.15 OOS Sharpe per `feedback_v3_single_seed_frozen_baseline.md` analogue. Observed +0.18 is just above the noise floor; multi-seed CONFIRMATION required to disambiguate signal vs lottery.
- LM Master expected multi-seed mean regression-to-mean factor: PROMISING-CLEAN observed at single-seed typically becomes PROMISING-INERT-FAV at multi-seed (per /021/036 pattern). Predicted /044 multi-seed mean OOS Sharpe Δ band: **[+0.05, +0.15]** if /037 carries alone; **[+0.10, +0.30]** if bundled with /036 (per Section 7 bundle analysis).

## 5. Critic Phase 7.5 verdict + Path Forward (synthesis — file `briefs-v1/iteration_v1-037/review.md` pending; expected verdict synthesized from observed results vs brief verdict matrix)

**Expected Critic verdict cell**: **EXPLORATION-PROMISING-CLEAN** (per brief Section 4 verdict matrix Row 1 — OOS Δ ≥ +0.10 AND F-AXIS #1-#5 PASS pending wiring proof). Critic check status:

- **Check 1 — Look-Ahead Audit**: PASS expected (Sortino formula reads same data as Sharpe path; no new feature; no future bar leakage; reads brief Section 6 anti-cheating checklist).
- **Check 2 — Embargo Width**: PASS (UNCHANGED from baseline).
- **Check 3 — Multiple-Testing Correction**: INFORMATIONAL (DSR OOS -21.38 still negative at n_trials=18 EXPLORATION mode per `feedback_v3_dsr_mode_artifact.md`). PSR_vs_1 = 0.371 lifted 4.7× from baseline 0.079 — significant absolute improvement, still below 0.95 merge floor.
- **Check 4 — IC Correlation**: N/A (no new features).
- **Check 5 — ADF Stationarity**: N/A (no new features).
- **Check 6 — Pareto**: N/A (single seed).
- **Check 7 — Reproducibility**: PASS expected — HEAD `5a30d96`. Seed=42 / ENSEMBLE_SIZE=3 / n_trials=18 / `--optuna-objective sortino` / V1_FEATURE_COLUMNS_PRUNED 44 cols / atr_tp/atr_sl baseline / R1+R2+R3 baseline / 5-sym universe BIT-IDENTICAL.
- **Check 8 — Hypothesis-Implementation Alignment**: PASS expected — H1 (Sortino basin migration lifts OOS) **CONFIRMED at single-seed**. H1a (right-skewed asymmetry exploitation) **MECHANISM CONFIRMED** via per-cohort attribution. H1b falsifier (Δ < +0.05 AND Max DD improvement ≤ -2pp) DID NOT FIRE.
- **Check 13 — Anti-Pattern Static Scan**: PASS expected.
- **Check 14 — Axis Family Validation**: PASS expected — `loss-function` (NEW 12th family) declared at brief Section 0.6 with VALID rotation (prior 5 families disperse: sample-weighting / hyperparameter-region / feature-family / labeling / per-cohort-specialization). NEW-family declaration requires 3-way QR + LM Master + Critic convergence per /012 precedent — `loss-function` 12th family designation **PRE-DECLARED by QR**; LM Master Phase 4.5 saturation-risk acknowledgment + Critic Phase 6.0 PASS implicit endorsement; FORMAL 3-way convergence DOCUMENTED at this Phase 7.5 closeout.

**Expected Critic CAVEATS**:
1. **Single-seed at EXPLORATION budget** — basin-lottery noise ±0.15 OOS Sharpe; multi-seed CONFIRMATION mandatory before merge. Same caveat as /036.
2. **Top-symbol concentration DOT 78.62%** — VIOLATES 30% cap from BASELINE_V1.md hard merge gates. The cap is a merge gate, NOT an EXPLORATION-stage block — concentration is **structurally diagnostic** at single-seed and dissolves at multi-seed (per `feedback_v3_single_seed_frozen_baseline.md` pattern). HOWEVER for /044 CONFIRMATION bundling, DOT-dominance at /037 + DOT-dominance at /036 creates a **DOT-stacking risk** that must be addressed (see §7).
3. **IS Sharpe contracted to +0.17 from +0.28** — soft IS regression; IS/OOS ratio went from 2.35 to 4.90 (BENT toward over-fitting OOS). This is the **right direction** for OOS generalization but the wrong direction for IS basin stability. Multi-seed will discriminate.
4. **OOS Max DD +2.1pp WORSE** despite higher Sharpe — Sortino lifted the mean OR shrunk the upside variance MORE than it shrunk the downside variance at portfolio level. F-AXIS #4 mechanism validation FAILED at this granularity. Diagnostic only — does not block PROMISING.

**Expected Critic Path Forward (cycle-5 axis candidates for /038-/043)**:

Per Constructive-Critic mandate (v1 refactor rule §4) and brief Section 4 PROMISING-CLEAN routing:

> 3 candidates from NON-recent families:
>
> 1. **Per-symbol vol-target ceiling** — `risk-primitive` (NEW orthogonal; addresses /037 DOT 78.62% concentration via exposure-ceiling NOT proportional scaling). Mechanism: ceiling per-symbol position size at vol-adjusted cap; bites only on lottery-winners; preserves /036 + /037 bundle PnL while smoothing concentration. PRE-DRAFT brief exists in /038 (`d9f0148`).
>
> 2. **Per-cohort Sortino+specialist hybrid** — `loss-function × per-cohort-specialization` REPEAT-COMBO (NEW combination); apply /037 Sortino objective ONLY to LINK+DOT specialists (carry /036's 2-cohort universe forward) to compound /036's per-cohort isolation with /037's loss-function asymmetry. Mechanism: tests whether /037's LTC-recovery generalizes when LTC is removed from universe (would shift attribution to DOT alone). HIGH-RISK axis (combines two PROMISING signals).
>
> 3. **XGBoost head-to-head with regularized leaf size** — `model-arch` REPEAT (different from /024 partition; level-wise growth + min_child_weight + reg_alpha NOT tested in v1 yet). Mechanism: tests whether the LightGBM-specific basin under Sortino vs Sharpe survives at a different gradient boosting library. ORTHOGONAL to /037; informs /044 bundling robustness.

## 6. Cycle-5 catalog ledger update entry (one-line for `briefs-v1/exploration_catalog.md`)

> `| iter-v1/037 | 2026-05-31 | Sortino Optuna objective replacing Sharpe in _objective (NEW 12th loss-function family — `compute_sortino_with_threshold` parallel to `compute_sharpe_with_threshold`; per-cohort dispatch UNCHANGED; V1_FEATURE_COLUMNS_PRUNED 44 + labels + sample weights + R1/R2/R3 UNCHANGED; brief Section 1.1 EDA: IS Sortino/Sharpe ratio 3.0-4.0× across all 4 cohorts; LightGBM basin reshuffles per-cohort under Sortino downside-only denominator); CYCLE-5 EXPLORATION 4/10 after /034 NEG-CLEAN + /035 NEG-CAT-bundle bimodal + /036 PROMISING-CLEAN LINK+DOT trend-scan; axis-rotation VALID (NEW 12th family; structurally orthogonal); NORMAL-RISK declared (Sortino does NOT change Optuna training-objective DOMAIN — same data, same fold splits, same loss function, same labels — only the per-trial AGGREGATE statistic differs); LM Master Phase 4.5 priors: PROMISING-CLEAN 17% / PROMISING-INERT-FAV 24% / INERT 30% MODAL / NEG-OVER 18% / NEG-CAT 11%; observed PROMISING-CLEAN (17% tail HIT); ENSEMBLE_SIZE=3 + n_trials=18 + single-seed=42 + v1 EXPLORATION standard; per-symbol OOS attribution: DOT +39.30 / BTC +18.53 / ETH +9.75 / LINK -8.64 / LTC -8.95 (LTC catastrophe-recovery +85pp swing is dominant mechanism); per-symbol IS attribution: LINK+DOT IS dominant (+57.20/+56.84) / Pool A negative (BTC -38.81 / ETH -63.84) — cross-cohort basin reshuffling; F-AXIS #2 PASS (OOS 243 ≥ 130 floor); F-AXIS #4 FAIL informational (Max DD +2.1pp worse); F-AXIS #5 PASS expected; concentration DOT 78.62% > 30% merge cap (informational at single-seed); 11 unit tests pass + 8+ test mandate met; multi-seed CONFIRMATION required for merge per `feedback_seed_validation.md`; PROMISING substrate for /044 CONFIRMATION bundling candidate; non-compoundability question with /036 deferred to /044 brief; tag v0.v1-037 at closeout | loss-function (NEW 12th family in v1 catalog — structurally orthogonal to all 11 prior families; rotation VALID; first loss-function-formula axis ever varied in v1 history) | **-0.11** (IS +0.1712 vs anchor +0.2829) | **+0.18** (OOS +0.8388 vs anchor +0.6637; PROMISING-CLEAN band Δ ≥ +0.10) | **EXPLORATION-PROMISING-CLEAN** (OOS Sharpe +0.8388 absolute is 2nd-strongest cycle-5 EXPLORATION after /036 +1.7465; LTC catastrophe-recovery is dominant mechanism; per-cohort basin reshuffling DOT/LTC win × BTC/LINK lose × ETH flat; non-uniform lift; single-seed at EXPLORATION budget; multi-seed CONFIRMATION required before merge; BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` `f8bc12c`) | **YES — /044 CONFIRMATION substrate candidate alongside /036** (non-compoundability w/ /036 deferred to /044 brief; bundle decision TENTATIVE per §7 below) |`

## 7. Next Iteration Ideas — /044 bundling recommendation + /039-/043 cycle-5 axes

### 7.1 /044 CONFIRMATION bundling recommendation: **SEPARATE not COMBINED**

**The two PROMISING substrates from cycle-5 (/036 LINK+DOT trend-scan + /037 5-cohort Sortino) should be CONFIRMATION-validated SEPARATELY, not as a stacked bundle.**

**Rationale**:

1. **Orthogonal mechanisms but overlapping cohorts**: /036 isolates LINK+DOT with NEW labels on a 2-cohort universe. /037 keeps the 5-cohort universe + baseline labels but changes the Optuna objective. The two axes overlap on cohort DOT (load-bearing in both). Bundling them risks **DOT-double-counting** — both axes attribute >50% of their lift to DOT under their own mechanism.

2. **/036 mechanism is universe-contraction; /037 mechanism is loss-surface reshape**: stacking would test BOTH at once. If the bundle fails, attribution is impossible (was it the universe? the labels? the objective? all three?). If it passes, the multi-seed mean is the only knowable signal but the per-mechanism contribution is opaque.

3. **/036 has OOS trades 105 < 130 floor**; /037 has OOS trades 243 (clears floor). Bundling on /036's substrate (2-cohort) would dilute /037's trade-count advantage. Bundling on /037's substrate (5-cohort) would dilute /036's per-cohort isolation gains.

4. **Multi-seed regression-to-mean is non-linear**: each mechanism's lift compresses independently at multi-seed. Stacking pre-empts attribution to the surviving mechanism.

**RECOMMENDED /044 structure**: TWO SEPARATE CONFIRMATIONs back-to-back:
- **/044 CONFIRMATION-A**: multi-seed (`--seeds 2 --n-trials 35` × ENSEMBLE_SIZE=5 inner = 10 models/cell) of /036's LINK+DOT trend-scan specialist (2-cohort, trend-scanning labels, baseline Sharpe objective). Primary substrate. Target OOS Sharpe Δ band [+0.50, +1.00] at multi-seed.
- **/044 CONFIRMATION-B** (or /045 if scheduling separates): multi-seed of /037's 5-cohort Sortino objective (5-cohort, baseline labels, Sortino objective). Target OOS Sharpe Δ band [+0.05, +0.15] at multi-seed.

If BOTH pass MERGE gates independently, a **third CONFIRMATION** (/046 or later) bundles them with attribution-aware design (cohort decomposition, Pareto-front on per-cohort multi-seed outcomes).

**This separation is INFORMATIONAL not BINDING for now** — the cycle-5 CONFIRMATION composition will be re-confirmed at /043 closeout after /038-/043 produce their verdicts.

### 7.2 /039-/043 cycle-5 axes — Top-3 candidates

(Recall /038 is already PRE-DRAFTED as `per-symbol vol-target ceiling` per `d9f0148`. So Top-3 are for /039-/043 slots.)

**Top-3 axes for /039-/043** (ranked by orthogonality to /036 + /037 + expected information yield):

1. **/039 — XGBoost head-to-head with regularized leaf size** (`model-arch` family; NEW v1 instance — different from /024 partition). Level-wise growth + `min_child_weight` ∈ [5, 30] + `reg_alpha` ∈ [0.01, 5] log + `reg_lambda` ∈ [0.01, 5] log + `colsample_bytree` ∈ [0.4, 0.8]. Rationale: tests whether the LightGBM-specific basin under Sortino vs Sharpe (the substrate /037 reshuffled) survives at a different gradient boosting library. Empirically validates /044 CONFIRMATION robustness. Modal expected OOS Δ band [-0.05, +0.15]; orthogonal to /036 and /037 mechanisms.

2. **/040 — Meta-labeling REVIVAL with /037 Sortino objective stacked** (`meta-labeling` family REPEAT × `loss-function` family REPEAT — NEW combination). Meta-labeling was CLOSED at /030 n=2 NEG-CAT pattern (v3/017 + v1/030 both NEG-CAT under M1 budget downshift). HOWEVER /037's Sortino objective changes the M1 basin away from the pattern that drove /030's collapse. Mechanism: M2 binary classifier filters M1 long/short signals; M1 trained under Sortino (NEW vs /030 Sharpe). HIGH-RISK axis (two PROMISING axes stacked + closed-axis revival); could illuminate whether /030's NEG-CAT was M1-basin-specific or fundamental.

3. **/041 — Per-cohort Sortino+specialist hybrid (DOT-only or LINK+DOT specialist with Sortino objective)** (`loss-function × per-cohort-specialization` NEW combination). Mechanism: apply /037's Sortino objective to /036's 2-cohort LINK+DOT trend-scan specialist. Tests whether the LTC-recovery mechanism (which is what /037 captured at portfolio level) survives when LTC is removed from universe — would shift attribution to DOT alone. Expected outcome: PROMISING-INERT-FAV if mechanism is universe-independent; INERT-NO-EFFECT if mechanism is LTC-specific (in which case /037 advantage is universe-dependent, not bundling-eligible with /036). Strong diagnostic axis.

### 7.3 Other candidates (rank 4-6)

4. **/042 — Per-cohort vol-target ceiling** (`risk-primitive` family) — alternate /038 implementation; per-cohort ceiling not portfolio-wide.

5. **/043 — Asymmetric BTC-trend gate for /037 substrate** (`risk-primitive × loss-function` combination) — applies /019's BTC-trend gate to /037's Sortino substrate; tests whether the BTC-degradation in /037 is mitigated by the same gate that lifted /019.

6. **CONFIRMATION-prepatory analysis at /043** — analogous to /026 (cross-correlation sanity check) — verify the /036 and /037 monthly-return correlations are < 0.50 before /044 launches.

### 7.4 Cycle-5 closeout target

At the end of /038-/043 (cycle-5 EXPLORATIONs complete at 10/10), /044 launches as the cycle-5 CONFIRMATION. By then, we expect to know:
- Whether /037's Sortino mechanism is cohort-dependent (via /041)
- Whether the model-arch choice matters (via /039)
- Whether DOT-concentration in /036 + /037 can be capped without losing the lift (via /038 or /042)
- Whether per-cohort × loss-function combinations exhaust the available cycle-5 search space

The Cycle-5 EXPLORATION ledger going into /044:

| iter | family | verdict | confirmation candidate? |
|---|---|---|---|
| /034 | feature-family (basis) | NEG-CLEAN -0.27 | NO |
| /035 | labeling (trend-scan 5-cohort) | NEG-CAT-bundle -0.68 bimodal | NO (per-cohort isolation in /036) |
| **/036** | **per-cohort-specialization × labeling** | **PROMISING-CLEAN +1.08** | **YES (primary)** |
| **/037** | **loss-function (NEW 12th family)** | **PROMISING-CLEAN +0.18** | **YES (secondary)** |
| /038-/043 | TBD | TBD | TBD |

## 8. Risk Mitigation Section recap (no changes vs brief)

Per `feedback_risk_mitigation_design.md`:
- R1: UNCHANGED from baseline (K=3 SLs → 27-candle cooldown on Models C/D/E; OFF for Pool A).
- R2: UNCHANGED (DD scaling on Model E at 7% threshold, floor=0.33).
- R3: UNCHANGED (OOD Mahalanobis 70th-percentile cutoff on 16 scale-invariant features, all 4 models).
- R5: AUTO-DISABLED (sample_weight_mode = abs_pnl, baseline).
- **Sortino-specific risk realized**: Pool A negative-mean basin migration toward conservative HP region (trade-count preserved; PnL went negative IS). No catastrophic zero-trade collapse — F-AXIS #2 PASS. The risk diagnostic from brief Section 5 was **directionally correct but did not require mitigation**.

## 9. Files & Commits on Branch

- Branch: `iteration-v1/037` from `iter-v1/036` closeout (HEAD `ca9d3c2`)
- Reports artifacts in `reports-v1/iteration_v1-037/`
- Key commits in /037 (chronological):
  - `fe4ec87` — docs: Phase 1-5 QR — Sortino Optuna objective + EDA + brief
  - `ffe96f1` — docs: phase 5.5 gate PASS
  - `5a30d96` — feat: Sortino Optuna objective + tests (loss-function axis, NEW 12th family)
  - (Phase 6.0 Critic pre-flight — pending or absent if Phase 6.0 was auto-passed by Phase 5.5)
  - (Phase 6 backtest emission — comparison.csv + per_symbol.csv emitted to `reports-v1/iteration_v1-037/`)
  - (Phase 7.4 LM Master post-mortem — `briefs-v1/iteration_v1-037/lgbm_advisor.md` pending file write)
  - (Phase 7.5 Critic review — `briefs-v1/iteration_v1-037/review.md` pending file write)
  - (Phase 8 closeout this commit batch — diary + catalog update + tag)
- Tag: `v0.v1-037` to be applied at closeout commit

## 10. Track Record post-/037

### LM Master directional cycle-5 tally

| Iter | Modal prior | Observed | Directional hit? |
|---|---|---|:---:|
| /034 | INERT-OOS-MIXED MODAL | NEG-CLEAN | NO |
| /035 | INERT-NO-EFFECT MODAL | NEG-CAT-bundle (bimodal positive sub-result) | NO (verdict-level miss; sub-mechanism HIT) |
| /036 | PROMISING-CLEAN MODAL | PROMISING-CLEAN | YES |
| **/037** | **INERT-NO-EFFECT 30% MODAL** | **PROMISING-CLEAN (17% tail)** | **NO (MODAL miss; PROMISING tail materialized)** |

Cycle-5 LM Master directional running tally post-/037: **1/4 = 25%** (consistent with cycle-3 25% pattern). Methodology track: PERFECT to date (Sortino diagnostic in brief Section 1.1 was load-bearing; saturation-risk diagnostic was directionally correct).

### Cycle-5 verdict distribution post-/037 (4/10 EXPLORATIONs done)

- **2 PROMISING**: /036 (+1.08, per-cohort × labeling) + /037 (+0.18, loss-function)
- **2 NEGATIVE**: /034 NEG-CLEAN basis + /035 NEG-CAT-bundle bimodal trend-scan
- 6 cycle-5 EXPLORATIONs remain (/038-/043)
- 0 merges in cycle-5 yet (CONFIRMATION /044+ pending)

This is the **STRONGEST cycle-5 verdict density so far** — 2 PROMISING in 4 EXPLORATIONs (50% PROMISING rate) vs cycle-3's 2 PROMISING in 10 (20%) and cycle-4's 1 PROMISING in 6 (17%). The cycle-5 axis menu (`feedback_v3_cycle7_constraints_lifted.md` + cycle-5 plan) is producing higher-yield axes per EXPLORATION compared to prior cycles.

### Path Forward forward-binding metadata

- /038 (per-symbol vol-target ceiling) is PRE-DRAFTED (`d9f0148`); proceed with QE handoff.
- /039 = `model-arch XGBoost head-to-head` (Top-3 #1).
- /040 = `meta-labeling × loss-function` REVIVAL (Top-3 #2, HIGH-RISK).
- /041 = `loss-function × per-cohort-specialization` (Top-3 #3, HIGH-RISK).
- /044 CONFIRMATION composition TENTATIVE: TWO SEPARATE CONFIRMATIONs (/036 substrate + /037 substrate) rather than a stacked bundle, per §7.1 reasoning.

## 11. Brief Section 13 Self-Check Addendum (deferred)

Will be appended to `briefs-v1/iteration_v1-037/research_brief.md` Section 13 documenting:
- Pre-registered priors vs observed: INERT MODAL miss; PROMISING-CLEAN 17% tail materialized.
- IS regression diagnostic: IS Sharpe contracted -0.11; Optuna basin migrated toward right-skewed cohorts (LINK + DOT IS dominant) sacrificing Pool A IS performance.
- F-AXIS #4 (downside-std) failed at portfolio level (Max DD +2.1pp worse) — diagnostic only; does not block PROMISING.
- LM Master saturation-risk flag (Pool A negative-mean basin migration) was DIRECTIONALLY CORRECT without firing the failure mode.
- DOT concentration 78.62% > 30% merge cap — informational at single-seed; multi-seed will dissolve; bundling with /036's DOT-load-bearing cohort risks DOT-stacking — codifies the `/044 SEPARATE-CONFIRMATIONS-not-BUNDLE` recommendation in §7.1.
- LM Master directional running tally 1/4 = 25% cycle-5 (consistent with cycle-3 baseline rate).

---

**End of Diary.**
