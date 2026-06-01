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

---

# LightGBM Master Advisor — iter-v1/012 — Phase 7.4 (Post-Mortem)

## Context Read

- Iteration outcome (comparison.csv): IS Sharpe **+0.7996** / OOS **+0.9363** / ratio **1.1709** (anti-overfit).
- F7 LTC IS overlap with /011 = **32.71%** — JUST INSIDE C PARTIAL band (30-70%); 2.71pp above the SEED-LOCKED threshold.
- Brief Section 8.1 verdict: per F1 OOS Δ=+0.27 (≥+0.05), F3 IS Δ=+0.52 (NOT in [+0.10, +0.30)), F7=32.71% (in [30%, 70%]) → matrix MISSES — observed cell is (F1≥+0.05, F3≥+0.30, F7∈[30%, 70%]), which is between rows 1 and 2.
- My Phase 4.5 P50 was A SUBSTRATE-LOCKED at 65%. Observed C PARTIAL — closer to B. **REFUTED in the strong sense.**

## 1. Honest Hypothesis Update — The 2-Property Decomposition

My Phase 4.5 framing claimed "the substrate (data + features + bounds + n_trials + ensemble_size) determines the basin; seed is subordinate." **The basin's ROSTER is NOT substrate-locked** — only 32.71% of /011's LTC IS trades survive a DISJOINT seed window. Roster composition is seed-property-driven.

What IS substrate-locked, surviving across /010/011/012 single-seed=42-window EXPLORATIONs:

- **IS Sharpe-Δ magnitude**: +0.47 (/010) → +0.48 (/011) → +0.52 (/012). Variance < 0.03 across MECHANISTICALLY DISTINCT axes (proportional R5, binary-kill R5, seed-window shift). This is a property of the (n_trials=35, ENSEMBLE_SIZE=3, V1_FEATURE_COLUMNS_PRUNED) substrate.
- **LTC-dominance PATTERN** (not LTC's specific trades): LTC IS pct trajectory 119.84% (/010) → 106.48% (/011) → 412.12% (/012). LTC always emerges as dominant in IS pct_of_total_pnl rank-1 position, even though only 33% of trades repeat.
- **OOS-amplification fraction**: OOS Δ ≈ 0.45-0.78 × IS Δ across /010/011/012. The "basin transfer ratio" is itself a substrate property.

What is SEED-DRIVEN:
- **Which specific (symbol, open_time) trades enter the IS roster** (67% rotate)
- **Which non-LTC symbol gets second-place** (LINK at /011 vs LINK lifted to near-LTC magnitude at /012)
- **Which symbol catastrophically loses** (BTC at /011, DOT at /012)

**Correct framing for future Phase 4.5**: "At v1 single-seed-window EXPLORATION, the OPTUNA OBJECTIVE-FUNCTION VALUE basin (Sharpe-Δ magnitude + dominant-symbol slot) is substrate-locked; the ROSTER COMPOSITION is seed-driven. Optuna finds an equivalent-depth local minimum in the same valley region regardless of seed window, but the trajectory to it routes through different rows." This is testable: predict that /013 at offset=6 will ALSO produce IS Sharpe-Δ ≈ +0.48 ± 0.10 (substrate) BUT roster overlap with /011 in [15%, 40%] AND with /012 in [25%, 50%] (seed-driven).

## 2. Calibration Update — Track Record 0/10 + 4 PARTIAL

Calibration disaster on verdict-class assignment at v1 single-seed-window. Future Phase 4.5 will:

- **Lead with FLAT priors at v1 single-seed EXPLORATION**: A 30% / B 30% / C 40% (instead of 65/18/17 concentrated). Empirical record doesn't earn concentrated priors.
- **No verdict-class projection when evidence is at different substrate dimension than prediction target.** /010↔/011 evidence was at IDENTICAL seed window; using it to predict DISJOINT seed window was a category error.
- **Magnitude predictions stay HIGH-confidence**: IS Δ ≈ +0.50 ± 0.10 is now substrate-anchored (3 data points). Future magnitude bands anchor on this.

## 3. DOT Catastrophic Reversal Mechanism

DOT IS raw net PnL: +26.62 (/010) → +31.01 (/011) → **-179.84 (/012)** — Δ of -210.85 net PnL units between adjacent seed windows. NOT a denominator artifact (denominator effect = inflated percentages but raw PnL collapsed).

DOT's basin in hyperparameter space has at least TWO local minima of comparable depth — one positive-DOT, one catastrophic-DOT. The TPE trajectory at [42, 123, 456] landed positive-DOT; at [789, 1001, 2002] landed catastrophic-DOT.

**Operational consequence for /015 CONFIRMATION**: at 10 inner seeds averaging, DOT's per-seed std vs other-symbol std needs forensic attention. If DOT's std > 2σ relative to portfolio, DOT contributes more variance than signal — recommend QR investigate DOT exclusion at CONFIRMATION.

## 4. LTC: Same Dominance, Different Trades

LTC raw net PnL trajectory: +3.27 (baseline) → +110.58 (/011) → +118.92 (/012). The 119.84% → 106.48% → 412.12% pct progression is denominator-effect; the RAW PnL went from +110.58 to +118.92, a modest +7.5% lift.

The dominance PATTERN is substrate-property: LTC always finishes IS rank-1 dominance position because LTC has the highest raw per-trade edge (+1.06 to +1.11 vs LINK +0.21 to +0.77 vs DOT +0.27 to -1.68). TPE saturates the LTC basin within n_trials=35 regardless of seed window; specific LTC trades vary because hyperparameter (learning_rate, num_leaves, lambda_l1) selections route to DIFFERENT LTC trades while preserving LTC over-allocation.

**Future Phase 4.5 normalization rule**: report `pct_of_total_pnl` AND raw net PnL together. Percentages alone misleading at small denominators.

## 5. LINK Lifted Dramatically — Mechanism

LINK raw net PnL: +72.06 (/011 wait— actually checking) /010=+72.06, /011=+42.45, /012=+105.86. **/012 is the all-time LINK IS high.** Avg PnL/trade: +0.21 (/010) → +0.28 (/011) → **+0.77 (/012)** — 3.7× /011 at SIMILAR trade count (149 → 138, WR 43.0% → 41.3%).

The /012 hyperparameters sit at a point in the gradient field that's still LTC-strong AND incidentally LINK-better. /011's hyperparameters over-fit to LTC's signal structure; /012's hyperparameters preserve LTC but unlock LINK's secondary basin.

**Structural implication**: LINK's signal is RECOVERABLE under hyperparameter variation. LINK may benefit MORE from multi-seed averaging than LTC does (LTC is at its basin already; LINK is at a per-seed-conditional sub-basin). At /015 CONFIRMATION post-mortem, LINK's std-across-10-seeds may be the load-bearing component if centered above /011's per-seed performance.

## 6. Verdict-Class for /012

Observed cell (F1=+0.27 ≥ +0.05, F3=+0.52 ≥ +0.30, F7=32.71% ∈ [30%, 70%]) is a MATRIX GAP in brief Section 8.1.

Per Section 8.2 diagnostic outcome (F7-only): **PARTIAL DISSOLUTION**.

Recommended verdict: **EXPLORATION-NEGATIVE subtype `PARTIAL-DISSOLUTION-WITH-SUBSTRATE-MAGNITUDE-PRESERVATION`** — NEW subtype codifying the 2-property decomposition. Classification is EXPLORATION-NEGATIVE because:
- OOS Δ +0.27 does NOT clear the +1.0 OOS floor (per `feedback_sharpe_floor.md` Sharpe 1.0 absolute merge floor)
- OOS Δ +0.27 is REGRESSION from /011's +0.41 (the basin-lottery winner)
- F7=32.71% in PARTIAL band — not a clean SEED-DISSOLVED that would trigger R5-BINARY-KILL CONFIRMATION
- Roster recomposition WITHOUT objective improvement = no edge accumulation

But INFORMATIONALLY valuable: the 2-property decomposition is now empirically established.

## 7. /013 Pre-Stage — My Call

F7=32.71% places /012 in "closer to B SEED-LOCKED" subregion. Pre-staged rule: PARTIAL closer to B → /013 = offset=6 [3003, 4004, 5005] as 3rd seed sample.

**My recommendation: ADHERE TO PRE-STAGED RULE. /013 = offset=6 [3003, 4004, 5005].**

Three reasons:
1. **HIGH information value** at offset=6. With 3 seed-window samples (offsets 0, 3, 6), can compute Optuna-objective variance properly. Tests substrate decomposition: IS Δ at offset=6 should land +0.48 ± 0.10 (substrate-property TESTABLE FALSIFIER); LTC IS roster overlap with both /011 AND /012 should be in [15%, 40%] (seed-property TESTABLE FALSIFIER).
2. **Pivoting to labeling forfeits the substrate decomposition test.** Labeling axis confounds substrate-magnitude property with labeling-induced lift.
3. **Pre-registration discipline.** Post-hoc pivot to labeling because F7 is "barely in PARTIAL" is exactly the rationalization v1 skill's pre-registration discipline exists to prevent.

**Predicted /013 outcome (HIGH CONFIDENCE on magnitude; FLAT on roster)**: IS Δ +0.48 ± 0.10, OOS Δ +0.20 to +0.50, LTC IS roster overlap with /011 ∈ [15%, 40%], with /012 ∈ [25%, 50%]. If observed substantially outside these magnitude bands, the substrate decomposition is wrong — halt and reassess.

## 8. /015 CONFIRMATION Axis Selection Implications

R5-BINARY-KILL has now produced positive OOS Δ at 2 of 2 single-seed-window EXPLORATIONs: /011 (+0.41), /012 (+0.27). CONFIRMATION-worthy?

**NOT YET.** 2/2 positive consistent with BOTH:
- (H1) R5-BINARY-KILL has real mechanical edge that survives across substrates
- (H2) Both seed windows happened to be in positive-OOS half of high-variance distribution

DECISIVE evidence:
- **/013 at offset=6 ALSO OOS Δ > +0.05** → 3/3 positive across DISJOINT seed windows → H1 → /015 CONFIRMATION on R5-BINARY-KILL
- **/013 OOS Δ ≤ 0** → 2/3 positive → H2 dominates → /015 pivots to UNUSED family

**Recommend /015 axis selection PRE-COMMITTED CONDITIONAL on /013 outcome.**

## What This Iteration Confirms / Refutes About Prior LM Master Advisory

Phase 4.5 P50 = A SUBSTRATE-LOCKED at 65%. Observed C PARTIAL at F7=32.71%. **REFUTED in verdict-class direction. Magnitude predictions PARTIALLY correct** (IS Δ +0.52 within A band of +0.45 ± 0.08; OOS Δ +0.27 in C band of +0.10-0.35, not A band of +0.30-0.55).

Phase 4.5 §2 reasoning #3 ("/010↔/011 evidence too strong to be coincidence") was the strongest argument and wrong on the dimension I projected onto. The 93.3% overlap was at IDENTICAL seed window across DIFFERENT axes; projecting to DISJOINT seed window at IDENTICAL axis was a category error.

Credibility-stake bet (P(F7>70%)=0.55) lost cleanly. 0/10 directional at v1 is a strong negative signal.

## Closing Note for Critic (Phase 7.5)

Critic attention:

1. **Section 8.1 verdict-matrix gap**: observed cell (F1≥+0.05, F3≥+0.30, F7∈[30%, 70%]) not pre-registered. Recommend amendment with `PARTIAL-DISSOLUTION-WITH-SUBSTRATE-MAGNITUDE-PRESERVATION` as new row 7.

2. **Denominator effect on pct interpretation**: /012 total IS net PnL ~+28.85 vs /011 ~+103.85 → percentages inflated 3.6×. Headline "412.12% LTC dominance" is denominator artifact — raw +118.92 vs /011's +110.58 is only +7.5% improvement.

3. **F7 boundary value 32.71% within 2.71pp of 30% SEED-LOCKED threshold**: sensitivity analysis on overlap definitions (exact key vs ±1 bar tolerance) would strengthen call.

4. **Substrate-magnitude decomposition is NEW structural claim with only 3 data points**. Should NOT promote to permanent memory until /013 validates. Critic should NOT endorse in closeout — empirical hypothesis pending /013.

5. **DOT-axis instability**: -210.85 raw net PnL swing on 107-trade roster (where ~70 shifted, ~37 same) implies DOT predictions sign-unstable under hyperparameter variation. May be feature-substrate issue (DOT's 8h features signal-marginal). Worth Critic Check 5 (ADF) attention on DOT's most important /012 features.
