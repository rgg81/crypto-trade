# LightGBM Master Advisor — iter-v1/015 — Phase 4.5 (Pre-Design)

## Context Read
- **Track**: v1. Branch `iteration-v1/015`. HEAD `eaf6d23`. FIRST CYCLE-2 CONFIRMATION (10/10 EXPLORATION precedents complete).
- **Baseline**: `v0.v1-baseline-corrected` (`f8bc12c`). IS +0.2829 / OOS +0.6637. UNCHANGED through cycle-2.
- **/014 outcome**: IS -0.6112 / OOS +0.1828 single-seed; C1 CONFOUND identified as proximate IS-catastrophe driver; n_eff 13→19 DURABLE mechanism finding.
- **Track record**: 0/12 directional + 5 PARTIAL. Updated /015 prior at /014 Phase 7.4 §6: **55% NULL / 20% PROMISING / 25% NEGATIVE.**

## 7 Recommendations

### Rec #1 — Keep n_trials=35; do NOT bump to 50
350 fits/cell sufficient. Per `feedback_v3_confirmation_n_trials_35.md`, 35 stays above TPE warmup saturation (~30) on 9-10 hparam dimensions. /014 n_eff_per_cell_median=19 indicates 19 effectively-independent trials of 35 — bumping to 50 lifts n_eff to ~22-25 asymptotic at +43% wall-clock. Not worth at 9.8h budget.

### Rec #2 — 10 seeds clears verdict-class noise floor but NOT strictly-better at +0.3 band
Single-seed std ≈ 0.80; 10-seed SE ≈ 0.25. For verdict-class (PROMISING vs NULL vs NEGATIVE), 10 seeds dissolves basin lottery. For "STRICTLY-BETTER than +0.6637 OOS baseline" (BASELINE_V1 update condition), need observed lift ≥ +0.50 OOS Δ to clear noise at 2-SE. **Brief +0.20 PROMISING threshold OPTIMISTIC** — observed +0.20 ± 0.25 SE means true CI [-0.05, +0.45]. **Recommend ADD per-seed median Δ ≥ 0 (≥5/10 seeds positive OOS) as robustness sub-gate** for BASELINE update.

### Rec #3 — C1 FIX boundary: explicit RuntimeError on σ_t=NaN at execution-time
**3-line code change at `lgbm.py:905-915` dispatch.** Currently brief allows silent NATR fallback at boundary candles (first ~126 candles per IS month if σ_t=NaN from EWMA warmup). This breaches F-AXIS-C1 attribution — execution-time barriers would diverge from label-time silently.

```python
if self.sigma_source == "ewma14d":
    sigma = self._month_sigma.get(key)
    if sigma is None or np.isnan(sigma):
        raise RuntimeError(f"σ_t unavailable for {key}; refusing silent NATR fallback")
    tp_pct = sigma * self.sigma_k_tp * np.sqrt(self.timeout_candles) * 100.0
    sl_pct = sigma * self.sigma_k_sl * np.sqrt(self.timeout_candles) * 100.0
```

Pre-register F-AXIS-C1 with NaN-skip count = 0 for IS test candles.

### Rec #4 — F-AXIS-MECHANISM at >95% PASS (TIGHTEN from /014 80%)
n_eff is bound by label-distribution SHAPE (σ_t-derived per-row barrier widths) — seed-INDEPENDENT. Labels computed once per IS row before Optuna spawns seeds. /014 BTC=20, ETH=20, LINK=18, LTC=18, DOT=19 — tight ±1. If F-AXIS-MECHANISM fires <7/10 at /015, label-pipeline non-determinism defect.

### Rec #5 — timeout_candles=21, √21≈4.58: CORRECT, calibration sound
σ_t per-candle log-return std; over 21-candle horizon, realized cumulative vol scales √21. Brief's per-symbol BTC σ_t p50 = 0.01607 × 1.06 × √21 = **7.82% TP at portfolio-median**. ~10-20% WIDER than baseline NATR×2.9 — matches /014 mechanism. **DO NOT REGRID k_tp/k_sl at /015** (axis isolation).

### Rec #6 — P(STRICT BASELINE_V1 update) ≈ 7% unconditional
Decomposition:
- P(F1-MULTI ≥ +0.20) = 20%
- P(F1-IS ≥ +0.10 | F1-MULTI ≥ +0.20) ≈ 50%
- P(Both Pareto seeds OOS > 0 | F1-MULTI ≥ +0.20) ≈ 70%
- Conditional: 0.50 × 0.70 = 35%
- Unconditional: 20% × 35% = **~7%**

Other 13% of PROMISING outcomes go MERGE-NO-UPDATE. Brief's STRICT condition is correctly stringent.

### Rec #7 — Refined predictions
| Falsifier | /014 prediction | /015 refined |
|---|---|---|
| F1-MULTI band [-0.30, +0.30] at 75% | UNCHANGED | TIGHTEN [-0.25, +0.25] (C1 FIX removes outlier source) |
| Per-seed std ≈ 0.80 | UNCHANGED | UNCHANGED |
| F-AXIS-C1 PASS at >95% | TIGHTEN to >97% (QE careful test infrastructure) |
| F-AXIS-MECHANISM PASS ≥7/10 at >80% | TIGHTEN to >95% (seed-independent labels) |
| F7-NEW-MULTI ≥7/10 per-seed direction matches | NEW | ~60% PASS |
| F8-NEW-MULTI 10/10 seeds in [466, 776] | NEW | ~75% PASS |

## Mechanism Risks Specific to /015 Multi-Seed

**Risk 1 — Wall-clock 9.8h UNDERESTIMATED.** Brief Section 3.6 scaling assumed linear. Optuna pruning + parquet I/O not linear in seed count. Predict **9.8-12h range; do NOT kill at 10h.**

**Risk 2 — LTC C1-WINDFALL inversion.** /014 LTC was IS+OOS WINNER via WINDFALL (tighter labels + wider NATR execution). At /015 with C1 FIXED, LTC's σ_t labels match σ_t execution — WINDFALL DISAPPEARS. Per-symbol attribution: LTC IS+OOS likely DOWN; BTC/ETH IS+OOS likely UP. Net portfolio direction unconstrained.

**Risk 3 — ETH IS-catastrophe at /014 (-99.73)** is largest single-symbol attribution. At /015 with C1 FIXED, ETH should recover materially. Portfolio IS net PnL prediction: -126 → roughly **+0 ± 30 at multi-seed mean** (MEDIUM confidence).

## What I Did NOT Recommend
- ENSEMBLE_SIZE=5 over 10 (would shift SE to ~0.36; STRICT-BETTER ~unreachable)
- Regridding k_tp/k_sl (axis isolation; calibration sound)
- min_data_in_leaf upper-bound bump (axis isolation; defer to /016)
- halflife sweep (defer to /016 if /015 PROMISING)

## Closing Note

**Honest verdict-class prediction**: 55% NULL / 20% PROMISING / 25% NEGATIVE. P(STRICT BASELINE update) ≈ **7% unconditional**. /015 experiment is FINALLY well-posed.

Track record 0/12 directional argues for FLAT verdict-class prior even at multi-seed. Two structural concerns I'm WILLING to be wrong about: (1) F-AXIS-MECHANISM >95% PASS — if <7/10 fires, label-pipeline non-determinism defect; (2) wall-clock 9.8-12h — if /015 completes <8h, Optuna pruning more aggressive than modeled.

---

# LightGBM Master Advisor — iter-v1/015 — Phase 7.4 (Post-Mortem)

## Context Read
- Outcome: IS Sharpe **-0.0645**, OOS Sharpe **-0.9480**, ratio 14.7 (sign-flipped); trade-count 620 IS (F8 PASS) / 218 OOS; **n_eff per-cell median = 3** (collapsed from /014's 19).
- Brief §1 hypothesis: 55% NULL / 20% PROMISING / 25% NEGATIVE. **/015 landed NEGATIVE — within /014 §6 prior band.**

## 1. Calibration Update — Track Record 1/13 Directional + 5 PARTIAL

**Per-symbol IS prediction VERIFIED 3 of 3.** /014 Phase 4.5 "LTC C1-WINDFALL inversion" prediction: LTC IS+OOS DOWN; BTC/ETH UP. Observed: LTC IS Δ -104.72 ✓, ETH IS Δ +117.07 ✓, BTC IS Δ +23.60 ✓. **First directional hit in v1.**

But honest distinction: this was a **mechanism-deterministic** call (C1 asymmetric windfall inversion when C1 FIXED) — NOT a basin-lottery prediction. Mechanism-level priors are EARNING credibility (now 6/13 verified at PARTIAL+); verdict-class F1/F3 magnitude calls remain at **0/13**.

Future Phase 4.5 rule (REFINED, not REVERTED):
- Mechanism-level claims: MEDIUM-HIGH confidence with explicit mechanism attribution
- Verdict-class magnitude: FLAT prior at single-seed; modal-NULL at multi-seed
- Per-symbol direction under CHARACTERIZED MECHANISM: MEDIUM allowed, with "mechanism-deterministic" disclaimer

## 2. n_eff Collapse 19 → 3 — Mechanism Confirmed

7.82% TP/SL over 21-candle timeout: most rows hit `timeout → sign(fwd_return)` fallback because ±7.82% excursions are rare in 21 8h-candles. Label distribution becomes timeout-dominated; Optuna can't distinguish hyperparameters → n_eff collapses. Model becomes near-trivial "predict fwd_return sign" → bad OOS (-0.95 Sharpe).

**Durable evidence**: n_eff is a CURVE in barrier-magnitude space:
- 1.70% labels (/014): n_eff = 19 (optimal-diversity)
- 7.82% labels (/015): n_eff = 3 (collapsed)
- Optimum somewhere in 3-5% middle

This is the **strongest structural finding of cycle-2**.

## 3. Path 1 vs Path 2 Retrospective — Path 2 Was Better

**Critic Path 1 was METHODOLOGICALLY correct but EMPIRICALLY WRONG.** My Phase 4.5 Rec #5 ("don't regrid k_tp/k_sl") trusted the calibration EDA over the empirical /014 n_eff=19 signal.

Lesson: when prior iteration produces DURABLE STRUCTURAL EVIDENCE on a specific implementation, that evidence should OUTWEIGH EDA-prescribed magnitudes. Path 2 (drop √timeout from labeling.py) would have preserved n_eff=19. Path 1 prioritized theoretical correctness over preserving the structural signal.

**Future Phase 4.5 — when prior iteration shows DURABLE STRUCTURAL EVIDENCE, recommend AGAINST any axis re-implementation that would dissolve it, even if dissolution is methodologically "cleaner."**

## 4. Labeling Axis Verdict — PARTIALLY CLOSED

**Axis CLOSED at calibrated 7.82% magnitude**. Multi-seed-mean decisive: σ_t × k × √timeout symmetric labels are NEGATIVE at v1 budget.

**Axis OPEN at sub-√timeout magnitudes** — 3-5% midway range may preserve n_eff diversification. Protocol if re-entering at /016+:
1. Pre-EDA n_eff vs barrier-magnitude curve at single-seed (test 1.5%, 2.5%, 3.5%, 5.0%, 7.82%)
2. Identify n_eff ≥ 15 preservation band
3. CONFIRMATION at n_eff-preserving magnitude

**My recommendation**: do NOT re-enter labeling at /016. Cycle-3 should pivot to UNUSED families. Labeling sub-axis re-entry is basin-fishing unless fundamentally new angle (meta-labeling, fractional-differentiation, multi-horizon stacking).

## 5. BASELINE_V1 Update — NO

IS Δ -0.3474 (NEG), OOS Δ -1.6117 (catastrophic NEG). Both halves fail STRICTLY-BETTER. CONFIRMATION-NEGATIVE per §8. BASELINE_V1 remains `v0.v1-baseline-corrected` (`f8bc12c`). **Cycle-2 closes with zero edge ingredients merged across 10 iterations.**

## 6. Cycle-2 Retrospective

10 iterations: 1 PROMISING-METHODOLOGY (/008 n_eff PCA, non-compoundable), 9 NEGATIVE spanning 5 families. **What this confirms**:

1. **v1 BASELINE is highly basin-locked** — corrected baseline occupies stable multi-dim local optimum
2. **Single-axis discipline is right method** but produces zero merges in this regime — edge surface multi-dimensional
3. **DURABLE structural evidence pattern** (/008 PCA, /014 n_eff=19, /015 n_eff curve) is REAL — only positive findings worth carrying forward
4. **Catalog dispersion healthy** (5 families touched) — no axis monoculture
5. **Cycle-2 = honest negative**, not failure. v1 approaching saturation pattern v3 hit at cycle-7.

## 7. Cycle-3 Recommendations (with NEW 2h EXPLORATION cap enforced)

**Priority 1 — Universe expansion (UNUSED at scale)**: /006 tested universe but limited additions. Cycle-3: +3-5 NEW symbols (SOLUSDT, NEARUSDT, AVAXUSDT), feature-set INHERITED, n_trials=25, 2h cap. Mechanism: denominator expansion reduces concentration.

**Priority 2 — XGBoost head-to-head (UNUSED in cycle-2)**: same feature stack, swap LightGBM → XGBoost via `--model xgb`. n_trials=25, 3 inner seeds, 2h cap. Mirror v3/016 protocol.

**Priority 3 — Sample-weighting (NEW family)**: López de Prado AFML Ch. 4 — weight samples by uniqueness. Reduces effective sample-correlation, may restore n_eff at full label magnitudes. Complementary to /008's PCA.

**Wall-clock discipline (cycle-3+)**: 2h EXPLORATION cap enforced per user directive 2026-05-25. Compress one of: n_trials (35→20), inner_ensemble (3 fixed), features (PRUNED, ~14-40 depending on axis), symbols (5→4). **Recommend compress n_trials FIRST; KEEP feature stack stable for axis isolation.**

## 8. Honest Credibility-Stake — Do NOT Revert FLAT Priors

3-of-3 per-symbol directional hits in 1 iteration is INSUFFICIENT to revert FLAT verdict-class rule:
1. /014→/015 LTC-inversion was mechanism-specific call (C1 asymmetric windfall inversion deterministically inverts when C1 FIXED) — deterministic mechanical inference
2. N=1 directional after 12 FLATS is well within prior FLAT-prior uncertainty
3. Hit on direction DOES NOT translate to magnitude — F1 multi-seed mean -1.61 was NOT in predicted [-0.30, +0.30] band (magnitude miss)

**Track record honest count**: 6 of 13 mechanism-level predictions verified at PARTIAL+; 0 of 13 verdict-class magnitude predictions verified.

## What This Iteration Confirms / Refutes About Prior LM Master Advisory

**CONFIRMED (3)**:
- LTC C1-WINDFALL inversion (3/3 per-symbol direction)
- Wall-clock 9.8-12h prediction
- P(STRICT BASELINE update) ≈ 7% (outcome 0%, within prior NULL band)

**REFUTED (2)**:
- Rec #5 "calibration sound; DO NOT REGRID" — math correct, empirical outcome catastrophic via n_eff collapse I did NOT anticipate
- F-AXIS-MECHANISM TIGHTEN to >95% PASS — actual n_eff=3 at all 10 seeds (gross miss)

**SURPRISE (1)**: **n_eff is a CURVE in barrier-magnitude space**. /014 1.70% → n_eff=19; /015 7.82% → n_eff=3. Intermediate magnitude likely preserves n_eff ≥ 15. NEW characterizable mechanism for future labeling design.

## Closing Note for Critic (Phase 7.5)

Three items:
1. **Check 5 (ADF on labels)**: at n_eff=3, label distribution is near-degenerate (mostly fwd_return sign). Verify whether labels themselves are non-stationary at cycle-period scales.
2. **Check 3 (per-cell PBO)**: with n_eff=3, each Optuna cell decides on ~3 effective labels. Per-cell PBO mechanically high. Verify cycle-PBO computation treats n_eff-degenerate cells correctly.
3. **Check 8 (axis attribution)**: F-AXIS-MECHANISM HARD-FALSIFIER FAIL (3/3 vs predicted ≥17 at 7/10). Verify engineering report traces this to label-magnitude × timeout-horizon interaction, NOT a code defect.

**/015 closed labeling axis at calibrated magnitude with decisive multi-seed NEGATIVE; produced strongest mechanism finding of cycle-2 (n_eff barrier-magnitude curve); Path 1 endorsement was methodologically-correct-but-empirically-wrong.** Cycle-3 should pivot to UNUSED families under 2h EXPLORATION discipline.
