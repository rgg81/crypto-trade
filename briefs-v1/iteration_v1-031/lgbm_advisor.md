# LightGBM Master Advisor — iter-v1/031 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/031`. Cycle-4 EXPLORATION-4/10. NINTH axis family (`sample-weighting` revived; /016 closed `uniform`+`uniqueness_only` at cycle-3 EXPLORATION budget — /031 pivots to inv_concurrency_only at FULL baseline budget).
- **Anchor**: `v0.v1-baseline-corrected` (`f8bc12c`) — IS +0.2829 / OOS +0.6637 / 621 IS / 189 OOS.
- **Recent**: /028 PROMISING (+0.598 OOS Δ); /029 TF (wall-clock); /030 NEG-CAT (-0.81 OOS Δ; M1 budget downshift basin relocation).
- **/030 §8 mandate**: 5-seed × 50 trials MINIMUM. QR PATH A honors.
- **EDA**: `inv_concurrency_only` is the ONLY one of 8 variants orthogonal both per-symbol AND pooled (Spearman vs uniqueness_only per-symbol max 0.199, pooled 0.034; vs baseline abs_pnl per-symbol max 0.072, pooled -0.093). Kish pooled 0.899 (better than baseline 0.84).
- **My track entering /031**: methodology 8/8; directional 4/10 = 40%.

---

## §1 Mechanism Pivot Adjudication (BINDING)

**The pivot from literal AFML §4.6 `uniq × inv_conc` to `inv_concurrency_only` is LEGITIMATE on orthogonality grounds AND a structurally distinct axis from /016's `uniqueness_only` closure. ENDORSE PATH A.**

Three load-bearing distinctions vs the relabeled-/016 hypothesis:

**Distinction 1 — Distributional shape**. /016 `uniqueness_only` was a window-AVERAGED `1/c_t` (each candidate's weight = mean of inverse concurrency over its FULL label window, 21 bars). /031 `inv_concurrency_only` is a SCALAR per-candidate `1/c_at_entry` evaluated AT entry bar only. EDA `composite_variants_per_symbol.csv` shows `uniqueness_only` per-symbol std ≈ 0.0033, inv_concurrency_only per-symbol std ≈ 0.33 — **two orders of magnitude wider weight dispersion**. /016's uniform-like weight distribution (Spearman 0.997 with uniform per /016 diary) is structurally absent here.

**Distinction 2 — Kish behavior**. Per `per_month_kish.csv`, /016 uniqueness_only had Kish ≈ 1.0 (uniform-equivalent — the literal AFML reduces to constant at 99.9% of bars under v1's saturated concurrency). /031 inv_concurrency_only has Kish ratio 0.899 pooled — REAL down-weighting visible. Mechanism is alive, not vacuous.

**Distinction 3 — Per-symbol vs portfolio-pooled disagreement**. /016 closed at uniform-equivalent. /031 EDA `spearman_orthogonality.csv` shows per-symbol Spearman composite vs uniqueness = 0.9999 (rank-identical within symbol) but pooled = 0.297 — the inv_concurrency mechanism reshapes BETWEEN-symbol weight magnitudes via per-symbol concurrency distribution shifts. Per `composite_variants_portfolio.csv`, `inv_concurrency_only` pooled Spearman vs uniqueness_only is **0.034** — totally distinct ordering. Within-symbol ranking is NOT the relevant axis for LightGBM TPE on pooled Model A (BTC+ETH) where the BETWEEN-symbol weight ratio is the load-bearing freedom.

**On the "is /031 really testing /030's budget hypothesis vs testing the new axis?" tension**: BOTH are tested. PATH A at 5-seed × 50 trials IS the budget-control for /030's M1-downshift root cause AND it is the correct compute envelope for the new inv_concurrency_only weight surface. The two questions are not separable at PATH A — the mandate makes them concurrent. If /031 fires PROMISING or INERT-FAV, attribution to axis vs budget remains AMBIGUOUS at this single iteration (would need /032 = inv_concurrency_only AT /016's 3-seed × 18 trials to isolate). I flag this **attribution ambiguity** as a /032 routing item (§7).

**Verdict: PIVOT LEGITIMATE. Single-axis discipline INTACT. /016 closure does NOT extend.**

---

## §2 Hyperparameter Region Recommendations Under inv_concurrency_only

Recommend **STRICT REPLICATION of `bounds_profile="v1_pruned_axis016"`** for orthogonality attribution cleanliness. My 6-adjustment list (tighten num_leaves ceiling 63→47, raise min_child_samples 20→30 floor, tighten learning_rate 0.10→0.07 ceiling, tighten bagging_fraction ceiling 1.0→0.9, raise lambda_l1 0→0.1 floor, tighten n_estimators ceiling 300→250) applies IF QR wants exploitation-oriented Optuna; for orthogonality test, strict-replication is methodologically cleaner. **QR picks; both are defensible.**

---

## §3 Basin-Stability Validation at 5-Seed Inner Ensemble

The /030 root cause was 3-seed basin instability. 5-seed at baseline is the budget-control. Three concrete additions to the brief Section 7:

**Validation #1 — Cross-seed Optuna best-trial Sharpe variance**. Parse `run.log` for `Trial X finished` per (model, month) cell. Compute std/mean across the 5 inner seeds' best trials for each cell. **Pass threshold: median(std/mean across cells) ≤ 0.25**. If > 0.40 → 5-seed is itself in a basin-lottery regime → axis-attribution INVALID, classify as NEGATIVE-BASIN-RELOCATION not NEGATIVE-AXIS-EDGE.

**Validation #2 — Per-cell best-param Spearman across seeds**. For each (model, month) cell, compute Spearman correlation of best-trial hyperparameters across the 5 seeds (for `num_leaves`, `learning_rate`, `min_child_samples`). **Pass threshold: median Spearman ≥ 0.50 across cells**. If < 0.30 → seeds disagree on basin → axis effect cannot be attributed.

**Validation #3 — Trade-roster overlap baseline ↔ /031 OOS per symbol**. Per /030 §1 (24% DOT overlap was the basin-relocation signature). **Pass band: [35%, 75%] per symbol**. < 25% → basin relocation (NEG-CAT mechanism duplication of /030). > 80% → axis not biting (INERT). Within band → axis materially reshapes roster.

---

## §4 Mechanism Recommendation (BINDING) + Prior Probability Table

| Verdict cell | Probability | OOS Δ band | Rationale |
|---|---|---|---|
| **PROMISING-clean** (Δ ≥ +0.20) | **17%** | [+0.20, +0.55] modal +0.32 | Real signal IF inv_concurrency reshapes Optuna's weight surface AND the rare-bar up-weighting captures structural concurrency-decorrelation moments |
| **PROMISING-INERT-FAV** (Δ +0.05 to +0.20) | **23%** | [+0.05, +0.20] modal +0.12 | Modal-positive cell. Reshape is real (Kish 0.899) but lift is mechanical not signal-discovery |
| **INERT-NO-EFFECT** (Δ ∈ [-0.10, +0.10]) | **30%** | [-0.10, +0.10] modal -0.02 | **MODAL.** TPE at 5-seed × 50 trials washes out the modest weight dispersion. The 99% of bars at Kish-ratio-near-1 dominate; the 1% of high-weight rare bars don't move the loss surface enough |
| **NEGATIVE-OVER-FILTER** (Δ -0.40 to -0.10) | **18%** | [-0.40, -0.10] modal -0.20 | Up-weighting rare bars over-fits to noise on those bars; Optuna picks hyperparameters that misgeneralize |
| **NEGATIVE-CATASTROPHIC** (Δ ≤ -0.40) | **12%** | [-0.80, -0.40] modal -0.55 | Tail. The 0.06% extreme weight spikes at LTC (Kish ratio 0.036) could nuke a single training month |

**Modal cell: INERT-NO-EFFECT 30%.** Combined PROMISING tail 40% > combined NEG tail 30%. **Net expected OOS Δ: +0.04**. ENDORSE PATH A.

---

## §5 Falsifier Pre-Registration

**F-AXIS #1 — Sample weights actually applied (wiring)**:
- run.log must contain `[sample_weight_mode=composite_inv_concurrency]` print for every Optuna trial dispatch.
- PASS criterion: ≥ 95% of (model, month) cells emit the weight-mode print.
- BLOCK if < 80% (silent fallback to baseline weights — wiring bug).

**F-AXIS #2 — Trade count band**:
- IS predicted [560, 690] modal 621 (baseline). OOS predicted [165, 215] modal 190 (baseline 189).
- BELOW 150 OOS → silent baseline fallback → wiring bug suspect.
- ABOVE 250 OOS → axis explosive trade-rate change → flag as TECHNICAL anomaly.

**F-AXIS #3 — Weighted-train Spearman across seeds vs baseline**:
- Brief should mandate that QE log per-cell (model, month) the LightGBM-reported `weighted training loss` in `run.log`. If this column matches BIT-IDENTICAL to baseline, weights silently NOT applied → BLOCK.
- More tractable proxy: per (Model A, month) cell, compute Spearman of Optuna best `learning_rate` choices across 5 seeds. If Spearman vs baseline best-params > 0.90, axis is silently no-op.

**F-AXIS #4 — n_eff per cell at PRUNED-43 × 5-seed × 50 trials**:
- Predicted median n_eff_per_cell ∈ **[14, 22]** at 5-seed × 50 trials.
- BELOW 8 → loss surface collapse → axis attribution INVALID.
- ABOVE 30 → axis amplifying loss-surface diversity (unusual; positive signal but flag).

**F-AXIS #5 — OOS TP-exit count ≥ 15 portfolio; ≥ 3 Model D** (transferred from /028/030):
- BELOW 15 portfolio TP-exit → caps verdict at PROMISING-INERT-FAV regardless of headline Δ.

---

## §6 Track-Record Commentary

**Cumulative**: methodology 8/8 perfect; directional 4/10 = 40%.

**/030 honest assessment**: Predicted NEG-OVER-FILTER 30% modal, observed NEG-CAT (-0.81). Combined NEG tail 46% directionally HIT; magnitude landed in my 16% NEG-CAT tail. My mechanism prediction (M2 over-filter à la v3/017) was REFUTED — actual mechanism was M1 budget downshift basin relocation, which my §8 wall-clock analysis flagged as a risk vector but I failed to elevate to mechanism-determining-variable.

**Confidence for /031**: **MEDIUM**. EDA is dense; budget is controlled (PATH A removes /030 confounder); mechanism is mathematically simple. Sample-weighting at v1 has 1/1 NEG-CAT prior at this axis family (`feedback_v1_abs_pnl_weighting_structural.md` warns abs_pnl is structural to v1's edge).

---

## §7 Routing Recommendation /032

- **/031 PROMISING-clean (17%)** → **/032 = inv_concurrency_only at 3-seed × 18 trials (BUDGET-CONTROL)**. Isolates axis-edge from budget-validity confound.
- **/031 PROMISING-INERT-FAV (23%)** → /032 = inv_concurrency_only stacking with NEW second axis.
- **/031 INERT (30% modal)** → **/032 = NEW axis family** (universe expansion / trend-scanning labels / vol-targeting per-trade).
- **/031 NEG-OVER (18%)** → /032 = NEW axis family. Sample-weighting CLOSED at v1.
- **/031 NEG-CAT (12%)** → /032 = closure-reconciliation + NEW axis. Sample-weighting permanently CLOSED.

**Strong prior**: /032 = either inv_concurrency_only-at-3-seed (axis confirmed) OR NEW axis family. NO third sample-weighting variant.

---

## §8 Wall-Clock + Budget Exception Adjudication

**ENDORSE QR PATH A.** The /030 §8 mandate is BINDING and the budget exception is CORRECT. The 2h cap is a SOFT discipline established at cycle-3 default configs. The /030 §8 mandate is a HARDER constraint — repeating M1 compute downshift WILL produce another NEG-CAT regardless of axis. The /030 §8 supersedes the 2h cap **specifically when an axis is sensitive to M1 basin stability AT the v1 EXPLORATION budget**. Sample-weighting is precisely such an axis.

**Why not PATH C (3-seed × 35 at ~1.6h)?**
1. 3-seed inner ensemble IS the /030 root-cause configuration. The mandate is to NOT replicate.
2. n_trials=35 provides only 15-20 post-warmup trials — basin-finding without basin-validation.

**Wall-clock risk mitigations**:
1. Pre-mortem checkpoint at month 10 (run.log monitor): if projected total > 5h at month 10, ABORT and re-launch PATH C-alt.
2. The QR/QE must NOT compress n_trials to 35 mid-run as a wall-clock saving measure.

---

## §9 Answer QR's 7 Adjudication Questions

**Q1 — Composite formula**: ENDORSE the pivot to `inv_concurrency_only`. EDA definitive. DO NOT run literal AFML composite even for comparison.

**Q2 — Hyperparameter region**: KEEP `bounds_profile="v1_pruned_axis016"` STRICT for attribution cleanliness.

**Q3 — Per-model differential**: BROADLY SYMMETRIC. All 5 symbols have concurrency mean 21.91-21.96 — nearly identical. Per-model OOS Δ within ± 0.15 of portfolio Δ.

**Q4 — Verdict priors**: SHIFTED. Modal INERT-NO-EFFECT 30% / PROMISING combined 40% / NEG combined 30%. Net OOS Δ +0.04.

**Q5 — Basin-stability variance threshold**: median(std/mean across cells) ≤ 0.25 PASS; > 0.40 FAIL.

**Q6 — Wall-clock risk**: SUPPORT EXPLORATION-WITH-BUDGET-EXCEPTION declaration. PATH A correct.

**Q7 — /032 routing prior**: Strongest prior on **/032 = NEW axis family (universe expansion to SOLUSDT 6th symbol)** at the modal INERT outcome.

---

## Closing Note

**MEDIUM directional confidence on /031.**

Three load-bearing calls staked:

1. **The pivot to inv_concurrency_only is LEGITIMATE and the axis is structurally orthogonal to /016's closure** (§1).

2. **PATH A budget exception is the CORRECT envelope** per /030 §8 BINDING mandate (§8).

3. **Modal verdict cell is INERT-NO-EFFECT 30%, not PROMISING.** Combined PROMISING 40% favorable-leaning but not dominant. Brief Section 4 should cite modal INERT-with-mild-positive-bias OOS Δ +0.04 — NOT cite a PROMISING-clean upper-tail magnitude as expected outcome.

**Single most important point for QR**: the attribution ambiguity at PATH A. PATH A confounds axis orthogonality with budget control. /031 cannot independently confirm BOTH in a single iteration. /032 routing should reflect that a PROMISING /031 triggers a BUDGET-CONTROL iteration, NOT immediate exploitation.

**Critic Phase 7.5 priority items I'm flagging in advance**:
1. F-AXIS #1 wiring: run.log per-trial `[sample_weight_mode=composite_inv_concurrency]` prints
2. F-AXIS #3 weight-reach-LightGBM proof
3. Basin-stability validation #1: cross-seed Optuna best-trial std/mean ≤ 0.25
4. Trade-roster overlap baseline ↔ /031 OOS per symbol within [35%, 75%]
5. /030 mechanism re-test: if /031 NEG-CAT under PATH A budget control, M1 budget-downshift is REFUTED as sufficient explanation
