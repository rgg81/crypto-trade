# LightGBM Master Advisor — iter-v1/012 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/012`. HEAD `e25b129`.
- **Baseline**: `v0.v1-baseline-corrected` (commit `f8bc12c`). IS Sharpe +0.2829 / OOS +0.6637. 40-feature pruned set. Unchanged post-/011.
- **/011 outcome (verified from `comparison.csv`)**: IS +0.7678 (Δ +0.4849), OOS +1.0709 (Δ +0.4072), R5-BINARY-KILL fire IS 18.3% / OOS 21.7%. F6 baseline-overlap 16.7%, /010-overlap 93.3%, LTC IS roster /010↔/011 overlap 93.3%. LTC IS pct_of_total_pnl = 106.48%.
- **My track record**: 0/9 directional + 3 PARTIAL. /011 verdict-class correct; basin-shift call WRONG (predicted 20-30% shift between mechanism classes; observed 93.3% basin identical).
- **/012 axis**: ENSEMBLE_SEEDS offset 0→3 (`[42,123,456]` → `[789,1001,2002]`). R5-BINARY-KILL config BIT-IDENTICAL to /011. Pure RNG-initialization test.

## 1. Hypothesis Validation Framing — My Claim on Trial

The /011 Phase 7.4 rule I committed to: *"at v1 single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3 + V1_FEATURE_COLUMNS_PRUNED, the Optuna basin is substrate-locked across axis primitives; the basin is seed-property-driven."*

That formulation is internally inconsistent. "Substrate-locked across axis primitives" is what /010↔/011 measured (varying the AXIS at fixed seed). "Seed-property-driven" is the opposite claim (basin is the SEED's property — varying seed should dissolve it). /012 isolates the seed dimension and tests which framing holds.

- **CONFIRMS substrate-lock**: /012 LTC IS overlap with /011 > 70%. Basin survives DISJOINT seed window. The "substrate" really is (data + features + bounds + n_trials + ensemble_size) — seed is subordinate.
- **FALSIFIES substrate-lock**: /012 LTC IS overlap with /011 < 30%. The /010↔/011 93.3% overlap was a same-seed coincidence; basin IS seed-property-driven; my Phase 7.4 framing was wrong in the direction it pointed.
- **Worst-case for my credibility**: Outcome B at LTC IS overlap < 20% AND OOS Δ near 0. This means I correctly identified /011 as basin-lottery + mechanical-cleanup but mis-located the basin's anchor. 0/10 directional. Honest fail; calibration update lands in `feedback_v1_substrate_basin_lock.md` as REFUTED.

## 2. Probability Calibration — I Disagree with QR's 60/25/15

The QR's framing prompts me to "heavily favor SEED-LOCKED" given my Phase 7.4 phrasing. **I won't — my Phase 7.4 phrasing was internally muddled. The structural evidence points the OTHER way.**

My priors: **A 65% / B 18% / C 17%.** Slightly more substrate-locked than QR.

Three structural reasons substrate-lock is the modal outcome:

1. **Optuna TPE at n_trials=35 over 9 hyperparameters is grossly under-sampled.** TPE warm-up uses ~10 random trials (seed-driven), then 25 acquisitions. With 9-dim search space, 25 acquisitions cannot escape gradient gravity around the strongest basin. The 6006-range integer seed space doesn't translate to meaningful exploration-policy diversity at this budget.
2. **The LightGBM gradient surface is data-determined, not seed-determined.** Same training rows + same labels + same feature columns + same loss → same gradient field. Optuna's seed picks which way the trajectory walks the field, not what field it walks. Different seeds = different paths through the same valley → same local minimum at the bottom.
3. **The /010↔/011 evidence is too strong to be coincidence.** Two MECHANISTICALLY DISTINCT axes (proportional weight scaling + binary entry filter) producing 93.3% byte-identical LTC IS trades isn't seed-luck — it's basin-gravity. If the gravity comes from (data, features, bounds) — invariant under seed shift — substrate-lock follows.

Where I'd give weight to seed-lock (18%): TPE's first 10 random trials at `[789, 1001, 2002]` produce a different start polygon than `[42, 123, 456]`. If the gradient field has multiple local minima of comparable depth, the trajectory could route to a different one. Combined with per-tree `feature_fraction < 1.0` (v1_pruned bounds allow this) producing different per-seed feature subsets, the basin could plausibly diverge.

## 3. Mechanism Analysis — Why LTC Basin Likely Re-Discovered

Pulled from `/011/in_sample/per_symbol.csv`: LTC IS = 104 trades, 51% WR, **avg PnL/trade +1.0633**. The other 4 symbols average +0.28 / +0.27 / -0.39 / -0.40 per trade. **LTC is structurally easier**: ~4× the per-trade edge of the next symbol. ANY model with reasonable LightGBM capacity that's not regularized away from LTC's signal will over-allocate prediction confidence there.

Three mechanisms re-discover LTC at new seeds:

1. **LTC IS rows are anomalously easy.** 24× per-trade PnL outlier vs portfolio mean. TPE's first random trial that captures LTC well becomes the dominant pseudo-prior; subsequent acquisitions exploit it. Different seeds find this trial at different trial indices but find it.
2. **The 40-feature pruned set selects for LTC discoverability.** V1_FEATURE_COLUMNS_PRUNED was pruned from /008+ analysis; if the pruning step preserved LTC-discriminating features (highly likely given LTC's signal density), the feature substrate steers any TPE trajectory toward LTC.
3. **n_trials=35 saturates the easy basin regardless of seed.** 35 is ~2× the TPE warm-up; the budget is sufficient to find LTC but insufficient to escape it. A run at n_trials=10 might genuinely seed-lock; n_trials=100 might escape; n_trials=35 lands in the "find but don't escape" regime.

The fourth mechanism the QR listed — *"LTC train-time labels are systematically biased"* — is the most overlooked. Triple-barrier labels at fixed ATR multipliers will be regime-conditional. If LTC's 24-month IS window happens to be a sustained trend regime, the labels concentrate informational mass; any tree-ensemble with depth ≥ 3 captures them.

## 4. Predicted IS Metrics per Outcome

Your bands match my structural reasoning. Refinements:

- **A (substrate-locked, ~65%)**: IS Δ +0.45 ± 0.08 (tighter than your ±0.10; basin draws should be near-deterministic at same substrate). LTC IS pct ≈ **95-115%** (centered on /011's 106.48%, slightly wider than your "100% ± 30%").
- **B (seed-locked, ~18%)**: IS Δ +0.00 ± 0.20 (rough symmetry; basin shifts in any direction). LTC IS pct ∈ [-10%, +50%] (no longer the dominant symbol; redistributed). LTC IS roster overlap with /011 < 25%.
- **C (partial, ~17%)**: IS Δ +0.15 to +0.35. LTC IS pct ∈ [40%, 80%]. LTC IS roster overlap [35%, 65%].

## 5. Predicted OOS Metrics — The Decision-Relevant Cell

Per /011 Phase 7.4: OOS Δ +0.41 decomposes as basin-substrate transfer (~+0.36) + mechanical kill_low OOS cleanup (~+0.05).

- **A confirmed**: OOS Δ +0.30 to +0.55 (P50 ≈ +0.40). Basin transfers; cleanup repeats. Possibly slightly lower than /011 due to seed-trajectory variance contributing OOS noise even when IS basin is preserved.
- **B confirmed**: OOS Δ -0.05 to +0.15 (P50 ≈ +0.05). No basin transfer; kill_low does its baseline-rooted mechanical lift only. This is the cross-roster oracle's BASELINE-cell prediction (+0.046) from /011 EDA.
- **C confirmed**: OOS Δ +0.10 to +0.35. Partial basin transfer; partial cleanup compounding.

**Most decision-relevant prediction**: if you observe OOS Δ ≥ +0.30 AND F7 < 30%, that's an off-table outcome the brief's verdict matrix doesn't pre-register. Flag immediately — it would imply mechanical kill_low produces a +0.30 lift independent of basin (5× larger than the cross-roster oracle BASELINE-cell prediction). Numerical instability suspected; demand QE seed-determinism audit.

## 6. /013-/014 Pre-Stage Conditional on /012 Outcome

I concur with the QR's pre-staging with one adjustment:

- **A SUBSTRATE-LOCKED CONFIRMED**: /013 = UNUSED-family axis. **Strongly prefer labeling axis (Critic Path Forward Option 2, triple-barrier σ_t source) over methodology per-cell early-stop.** Rationale: per Section 5 mechanism #4, LTC IS labels are likely regime-biased. Changing the label-source IS the most direct loss-surface intervention; per-cell early-stop is decorative at v1 EXPLORATION budget. HIGH-RISK declaration mandatory.
- **B SEED-LOCKED CONFIRMED**: /013 = offset=6 `[3003, 4004, 5005]` as 3rd seed sample. I concur — this builds the multi-seed evidence cheaply at EXPLORATION budget. /015 CONFIRMATION on R5-BINARY-KILL at full multi-seed becomes the pre-committed next step.
- **C PARTIAL**: /013 = offset=6 tie-breaker IF C lands closer to B (overlap 30-50%), OR pivot to UNUSED family IF C lands closer to A (overlap 50-70%). The split-decision routing should be pre-registered in /012's diary closeout to prevent post-hoc rationalization.

## 7. Honest Confidence

- **Verdict-class (A/B/C)**: MEDIUM-HIGH confidence at 65/18/17. The /010↔/011 93.3% evidence is strong; my /011 Phase 7.4 framing was muddled but the data points substrate-locked.
- **Magnitude predictions**: LOW confidence. Track record 0/9 directional + 3 PARTIAL. My P50 estimates may be wrong in magnitude even if the verdict class is correct (as at /011, where verdict class was right but magnitude was 8× under-predicted).
- **Single most non-ignorable point**: **F7 (LTC IS overlap with /011) is the single load-bearing measurement.** F1 OOS Δ and F3 IS Δ are downstream consequences. If F7 > 70%, A is confirmed regardless of F1/F3 magnitudes; if F7 < 30%, B is confirmed regardless. The Section 8.1 verdict table's compound F1×F3×F7 conditions are correct, but the diagnostic outcome assignment in Section 8.2 (F7-only) is the actual primary measurement. Do not let F1 magnitude theater distract from F7.

If I had to bet a single number: P(A confirmed at F7 > 70%) = 0.55. P(F7 > 90%, deep substrate-lock) = 0.30. P(F7 < 30%, my framing inverted) = 0.18. This iteration has high credibility-stake on my Phase 7.4 framing; honest accounting demands I flag that I'm betting against the QR's stated "should heavily favor SEED-LOCKED" framing of my own prior post-mortem. The post-mortem was muddled; the structural evidence is not.

---

Brief is sound. R5-BINARY-KILL config bit-identical to /011 is correct axis isolation. F7 substrate-test falsifier is the right diagnostic. No hyperparameter or feature changes recommended for /012 — pure RNG-init isolation is the experiment.
