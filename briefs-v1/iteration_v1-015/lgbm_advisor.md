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
