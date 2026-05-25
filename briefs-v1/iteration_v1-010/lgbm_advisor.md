# LightGBM Master Advisor — iter-v1/010 — Phase 4.5 (Pre-Design)

## Context Read
- Track: v1; baseline `v0.v1-baseline-corrected` (IS +0.2829 / OOS +0.6637; 5-seed); 5-symbol universe; 40-feature `V1_FEATURE_COLUMNS_PRUNED`.
- Prior iter /009: NEGATIVE-NEGATIVE feature-family deletion; 3-way convergence on R5 as next axis.
- QR's axis: R5 vol-target ceiling at uniform `vol_target_pct = 4.0%` (revised from /009-spec 2.5% via EDA — sharp, well-justified).
- Track record: 1/6 directional with PARTIAL credit only. Defaulting LOW confidence per /007 closeout.

## 1. Mechanism Critique — Will Optuna Re-Optimize Into a New Roster?

**Most likely: NO, Optuna will NOT meaningfully re-route.** Single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3 is below the variance-reduction threshold needed to discover a NEW high-confidence-low-vol entry distribution. The oracle's -0.020 OOS Δ is the modal outcome. The mechanism for Optuna substitution requires the GBM to demote IS-overfit basins that correlate with high-NATR entries — but with `min_data_in_leaf` defaults and 5-fold pooled CV, the loss gradient on R5-scaled targets is only ~5% different from baseline (mean cap 0.954 IS). Below the SNR floor where Optuna shifts basins.

**Empirical evidence**: per Section 2.4 oracle, R5 cuts LINK IS by 28.62pp + LTC IS by 12.28pp. ETH IS gains +7.10pp because R5 caps ETH's IS losers more than its winners. Net IS portfolio Δ = -35.67pp wpnl. For Optuna to FLIP this NEGATIVE → POSITIVE, it would need to find a hyperparameter region where LINK's high-vol entries are predicted as LOWER-confidence (so position size redirects to BTC/ETH at lower NATR). The signal:noise ratio for that flip at n_trials=35 single-seed is ~10-15% — possible but unlikely.

**Most likely path**: Optuna re-converges to a near-baseline basin; trade roster ~85% identical to oracle; F1 verdict = -0.05 to +0.02 (PROMISING-INERT). The /009 brief's pre-registered PROMISING-INERT-to-marginal-NEGATIVE call is correctly framed.

## 2. Per-Symbol R5 Heterogeneity — Should Calibration Be Per-Symbol?

**No — DO NOT per-symbol calibrate at /010.** Three reasons:

1. **Bundling discipline**: per-symbol thresholds = 2-axis change (axis A: R5 enable; axis B: per-symbol calibration). v1 cycle-2 has burned 5 consecutive HIGH-RISK NEGATIVES partially because of axis stacking. /010 should be SINGLE-axis EXPLORATION at uniform 4.0%.
2. **The "ceiling" semantics is universe-level**: R5's design intent is "cap exposure when vol exceeds a universe-level safety band." Per-symbol thresholds would be R5'=per-symbol-vol-target-ratio — a DIFFERENT primitive. The brief's framing as "anchored on universe p75 ≈ 4.7%" is the correct conceptual home.
3. **Per-symbol calibration is the /011 path IF /010 PROMISING**: per Section 11 alternates, vol_target ∈ {3.5, 4.0, 4.25} as a 3-point ablation at CONFIRMATION is the right venue. Per-symbol ablation at multi-seed CONFIRMATION is even better but requires PROMISING first.

The BTC-rarely-fires / LINK-72%-fires asymmetry is **information**, not a calibration defect. It tells us R5 will mostly act on LINK + DOT + LTC — which is the design intent (cap the high-NATR top contributor and laggers, not BTC).

## 3. /011 Pre-Stage Conditional on /010 Outcome

- **/010 PROMISING (OOS Δ ≥ +0.05)**: /011 = multi-seed CONFIRMATION at ENSEMBLE_SIZE=10 + 10 seeds + n_trials=50, vol_target ∈ {3.5, 4.0, 4.25} 3-point ablation. HIGH-RISK pre-commit fires per Section 2.5. Tag for BASELINE_V1 update if it strictly beats /009 on IS AND OOS.
- **/010 PROMISING-INERT (OOS Δ ∈ [-0.05, +0.05])**: R5 vol-target ceiling axis CLOSED at single-seed. /011 PIVOTS to UNUSED `risk-primitive` SUBTYPE — recommend per-symbol regime-conditional binary kill switch (e.g., "if NATR_14 > 7%, skip entry") rather than proportional scaling. This is OPC-orthogonal to /010 per v3/020 lesson.
- **/010 NEGATIVE marginal (-0.05 to -0.10 OOS Δ)**: R5 proportional-scaling family CLOSED at v1 (matching v3/020 universal pattern). /011 PIVOTS to UNUSED `risk-primitive` BINARY family or `labeling` axis (triple-barrier σ_t source).
- **/010 NEGATIVE-catastrophic (OOS Δ < -0.20)**: /011 = methodology audit + reconsider Failure Mode 4 Optuna basin-shift. Not the expected path.
- **/010 NEGATIVE-mis-calibrated**: /011 = vol_target re-grid at {3.0, 5.0, 6.0}. Not the expected path; F2 oracle pre-registers 15.3% well inside band.

## 4. Honest Confidence

**LOW confidence on directional Sharpe prediction; HIGH confidence on verdict CLASS.**

Track record after /005-/009: 0/6 directional Sharpe predictions correct; 1 PARTIAL. My calibration on signed deltas is broken. I will NOT pretend otherwise.

What I AM confident in (HIGH):
- **Verdict class is PROMISING-INERT or marginal-NEGATIVE** (~70% probability). The oracle EDA is well-constructed, R5 is STATELESS per /054, and the QR's Section 2.4 per-symbol decomposition is honest. The Δ is small enough that Optuna re-optimization noise will dominate the directional sign.
- **F2 fire rate band check will PASS** (~85% probability). Oracle 15.3% is mid-band; even ±50% deviation from oracle keeps it in [10%, 60%].
- **F4 DEGENERATE_PREDICTOR will not fire** (~95%). R5 is position-sizing only; no label or feature surface modified.

What I am NOT confident in (LOW):
- The sign of OOS Δ (could be +0.05 or -0.05 with similar probability).
- Whether /010 advances to /011 CONFIRMATION. ~25% probability of clearing the PROMISING gate at +0.05 OOS Δ given single-seed=42 variance.

**The one thing the QR should NOT ignore**: Failure Mode 5 (LINK edge erosion) is the central tension. If the /010 reports show LINK OOS net_pnl reduced by >20% AND portfolio OOS Δ ≤ 0, this is informative even at NEGATIVE verdict — it confirms v3/020 generalizes to 5-symbol universe and CLOSES proportional-scaling R5 family universally at v1. That's a useful structural finding even from a NEGATIVE outcome.

## What I Did NOT Recommend, and Why

I did NOT recommend: (a) per-symbol R5 calibration (axis-stacking trap; defer to /011 if PROMISING); (b) running a 3-point vol_target grid at /010 (would exceed 2h cap and stack axes); (c) lowering n_trials to 20 to save time (no — TPE warmup saturation needs ≥30); (d) raising ENSEMBLE_SIZE=3 → 5 (no — that's a CONFIRMATION knob); (e) changing seed from 42 (no — frozen baseline per `feedback_v3_single_seed_frozen_baseline.md`).

## Closing Note

QR has done strong EDA work. The 2.5% → 4.0% recalibration is exactly the "EDA designs the sharpest experiment" pattern at its best. Brief is HIGH-quality; Section 2.4 per-symbol PnL decomposition is the single most valuable artifact (read it twice). The experiment is well-framed even if the verdict lands PROMISING-INERT — it generates a clean structural finding either way. Proceed.

---

## Orchestrator Workflow Note

LM Master Phase 4.5 fired AFTER QR Phase 5 brief authoring (post-`5506507`) rather than between Phase 4 and Phase 5 due to single-session compaction boundary. Functional alignment verified:
- QR's brief pre-registers PROMISING-INERT-to-marginal-NEGATIVE outcome class — matches LM Master's HIGH-confidence verdict-class prediction (70%).
- QR's vol_target=4.0% calibration (revised from 2.5% via EDA) — LM Master endorses as "exactly the EDA designs the sharpest experiment pattern at its best".
- QR's single-axis discipline (no per-symbol calibration) — LM Master endorses as bundling-discipline-correct.
- QR's Section 11 alternates list vol_target ∈ {3.5, 4.0, 4.25} for /011 CONFIRMATION — matches LM Master's /011 PROMISING branch prescription.

Net: no brief revisions required; LM Master content is integrated retroactively as Section 3.7 of brief is structurally LM-Master-response-aware (QR pre-authored "If LM Master suggests per-symbol calibration: defer to /011 CONFIRMATION" — exactly what LM Master recommends).

Proceeding to Phase 5.5 gate.

---

# LightGBM Master Advisor — iter-v1/010 — Phase 7.4 (Post-Mortem)

## Context Read
- Iteration outcome (`comparison.csv`): IS Sharpe **+0.7530** (vs baseline +0.2829, Δ **+0.4701**), OOS Sharpe **+0.6354** (vs baseline +0.6637, Δ **-0.0283**), OOS/IS ratio 0.8439, R5 fire rate IS 23.23% / OOS 18.57%.
- Brief Section 1 hypothesis: "Uniform 4.0% vol-target ceiling caps the LINK+LTC+DOT high-NATR overshoot tail without re-routing entries; oracle predicts -36pp IS / -0.020 OOS Δ."
- My Phase 4.5 call: PROMISING-INERT verdict-class (~70% HIGH-confidence), basin-shift unlikely (~10-15%), F2/F4 pass.

## Calibration Update — Track Record 0/8 Directional + 2 PARTIAL

**Verdict class correct (PROMISING-INERT band at OOS Δ -0.0283).** Basin-shift call **directionally wrong**: the +0.47 IS lift is a textbook Optuna re-routing event, not the ~85% roster-identity I anchored on. Roster intersection is 165/663 = **24.9% on IS** and **17.1% on OOS**. I underweighted three factors:

1. **Config mismatch with baseline**: baseline is 5-seed ENSEMBLE × n_trials=50 = 250 fits/cell; /010 is 3-seed × n_trials=35 = 105 fits/cell. The 24.9% intersection isn't pure R5 — it's R5 + halved Optuna budget + reduced seed averaging. My "roster ~85% identical to oracle" assumed apples-to-apples; reality compared apples-to-pears.
2. **R5's gradient signal was nonzero on the loss surface**: 74.8% of /010 IS trades sit at weight<0.5 (vs baseline 69.7%) — a 5pp shift that I dismissed as below SNR floor. It was AT the floor.
3. **The "modal outcome" assumption was wrong for single-seed=42 EXPLORATIONs**: at this Optuna budget every R-primitive change WILL find a new basin because the search space is over-parameterized relative to the trial count.

**Calibration update**: future Phase 4.5 directional confidence on Optuna basin-shift events should be **LOW by default** when (a) the runner config differs materially from the anchor's, OR (b) the axis touches the position-sizing weight (multiplies into the loss directly). Verdict-class predictions remain HIGH-confidence; signed-delta predictions remain banned.

## IS Optuna Basin Shift Mechanism

Per-symbol IS deltas tell the story (`reports-v1/iteration_v1-010/in_sample/per_symbol.csv`):

| Symbol | Baseline IS net_pnl | /010 IS net_pnl | Δ | WR baseline | WR /010 |
|---|---|---|---|---|---|
| LTC | +3.27 | **+79.98** | **+76.7** | 39.5% | **47.3%** |
| LINK | +72.06 | +32.33 | -39.7 | 45.2% | 42.1% |
| DOT | +26.62 | +17.99 | -8.6 | 41.9% | 44.4% |
| ETH | -13.70 | -19.40 | -5.7 | 38.6% | 34.5% |
| BTC | -37.28 | -44.16 | -6.9 | 33.6% | 36.4% |

**Mechanism: NOT "lower-NATR entries" or "higher-conviction signals." Optuna re-routed Model D (LTC) into a fundamentally different prediction basin.** LTC WR jumped 39.5 → 47.3 (+7.8pp), trade count dropped 124 → 110 (-11%), avg PnL went 0.026% → 0.727% (28× per-trade). LTC alone explains the +0.47 IS lift; LINK degradation partially offsets but LTC dominates. R5 didn't "cap the LTC tail" — it changed which trades Optuna selected to take in the first place, by reshaping the position-sizing-weighted loss surface seen during n_trials=35 search.

This is **not the v3/020 pattern** (proportional scaling fails universally). This is a **single-symbol IS lottery** at single-seed=42 — LTC's re-route is exactly the kind of result that dissolves at multi-seed CONFIRMATION per `feedback_v3_single_seed_frozen_baseline.md`. The OOS LTC remains -43.5 (vs baseline -47.2; Δ +3.7pp — marginal), confirming the basin was found in-sample but didn't generalize.

## OOS Marginal-Negative is Genuine Information

OOS Δ = -0.0283 IS NOT v3/020 universal-fail replication. It's a **null result at OOS** dominated by basin-shift noise: BTC +11.7pp / DOT +27.2pp / LINK +46.7pp positive contributions are netted out by ETH -14.1pp + LTC -3.7pp negatives, and the OOS Sharpe denominator includes the extra exposure variance from the new roster. The "proportional scaling fails universally" v3/020 finding does NOT replicate at v1 — at v1, R5 produces a **non-pathological null** with positive OOS contribution from 3 of 5 symbols. This is genuinely different from v3 BCH+LDO+TRX where proportional scaling caused symmetric OOS degradation. **R5 proportional-scaling family at v1 is INERT, not toxic.**

## F4 Verdict — PASS Confirmed

Counted degenerate trades (`|exit-entry|/entry < 1e-4`): **IS=0, OOS=0**. R5 is position-sizing only; no label/feature surface modified; no degenerate predictor risk. F4 PASS.

## Feature Importance Triage

**`feature_importance.csv` does NOT exist for /010** (only `reports-v1/iteration_v1-007/feature_importance.csv` survives). The runner doesn't emit per-iteration feature importance at v1 EXPLORATION budget. Cannot verify whether vol_natr_14 importance jumped under R5. This is an instrumentation gap that should be closed if v1 continues investigating R-layer primitives — recommend QE add `_write_feature_importance` to v1 runner at /011 setup (the v3 fix from iter-v3/016 hasn't been ported).

For reference, in /007 Model A (BTC+ETH) `vol_natr_14` ranked **6th of 40** at gain=7238.7 (behind aroon_osc_50, autocorr_lag5, atr_14, natr_x_adx, macd_line). R5 making vol_natr_14 "free to use" could theoretically jump it to top-3, but without /010's CSV we cannot confirm.

## Path for /011 — Confirm LM Master Phase 4.5 Recommendation

Per brief Section 11 + Phase 4.5 §3 PROMISING-INERT branch: **/011 PIVOTS to UNUSED `risk-primitive` BINARY family — regime-conditional kill switch.** Confirmed, with refinement:

**Concrete /011 axis**: "skip entry if NATR_14 > 7%" (binary kill, not proportional scale). The threshold 7% is the **universe p90 of NATR_14**; at p75 ≈ 4.7% the cap is too tight (would kill ~25% of trades). p90 ≈ 7% kills ~10% — same fire-rate band as /010's 23%/18.6% but as a hard binary cutoff. EDA basis: re-use /010's vol_natr_14 distribution analysis from briefs-v1/iteration_v1-010/research_brief.md Section 2.3.

**Why binary, not another proportional family**: v3/020 + v1/010 jointly establish proportional scaling's INERT/marginal-NEGATIVE corridor across both universes. Binary kill is the architecturally-orthogonal sister primitive — it injects state-discontinuity into the prediction → position-sizing pipeline rather than smoothly attenuating exposure. STATELESS per `feedback_v3_oracle_eda_validity.md` — oracle EDA on /010's roster is fully valid.

## Suspicious Patterns for Critic Phase 7.5

1. **LTC IS basin-shift is the entire +0.47 lift.** Per-symbol delta table above. Critic Check 6 (per-symbol concentration) should flag: LTC alone went from 6.42% of total PnL to **119.84%** — concentration at one symbol > 100% means LTC drove the entire portfolio gain and other symbols offset. This is the "narrow basin" pattern from `feedback_v3_concentration_is_signal.md` adapted to single-symbol.
2. **OOS roster overlap with baseline is 17.1%, far below the "stateless mod" expectation of ~85%.** R5 fired on 23% of trade-candidates IS but produced 75% roster turnover — the additional turnover is Optuna basin re-routing, not R5 mechanical filtering. Critic Check 3 (PBO) should be sensitive to this; n_effective_trials=13 and n_eff_per_cell_min=5. LTC at n_eff=12 means LTC's 0.7530 IS Sharpe rests on the thinnest evidence.
3. **PSR_monthly_vs_0 dropped IS=0.876 / OOS=0.760** (vs aspirational 0.95) — the IS lift is statistically fragile. DSR_corrected=0.000 (vs baseline negative DSR) is informationally null, not informationally positive.

## What This Iteration Confirms / Refutes About Prior LM Master Advisory

**Confirmed**: F2 fire-rate band (23.2%/18.6% in [10%, 60%] — PASS at 85% predicted), F4 no degeneracy (PASS at 95% predicted), verdict-class PROMISING-INERT (PASS at 70% predicted).

**Refuted**: "Optuna basin shift unlikely (~10-15%)" — observed massive basin shift on LTC. The mechanism reasoning was sound (n_trials=35 single-seed has limited basin-discovery power) but the LTC re-route at the position-weighted loss surface was exactly the basin Optuna found. My probability estimate was off by ~3-4× on the upside.

**New rule for Phase 4.5 going forward**: when the axis multiplies the loss directly (position-sizing weight, label weight, sample weight), basin-shift probability is HIGH (40-60%) at single-seed budgets, NOT 10-15%. Document this in the next /011 advisory.

## Closing Note for Critic (Phase 7.5)

Critic should focus Check 6 (concentration) on LTC's 119.84% pct_of_total_pnl IS — single-symbol drives the entire IS lift. Check 3 (PBO) deserves attention given n_eff_per_cell_min=5 (one cell on extremely thin evidence). The /010 verdict is genuinely PROMISING-INERT (OOS Δ -0.0283 within [-0.05, +0.05] band) and the marginal-NEGATIVE call is honest — but the IS +0.47 is not durable signal and should not influence /011 staging.
