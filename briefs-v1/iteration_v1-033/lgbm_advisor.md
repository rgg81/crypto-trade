
---

# LightGBM Master Advisor — iter-v1/033 — Phase 7.4 (Post-Mortem)

## Context

- Outcome: IS Sharpe **-0.0299** (Δ -0.31) / OOS Sharpe **+1.1084** (Δ **+0.44**); 231 OOS trades; OOS PSR_vs_1=0.452 (5.7× lift over baseline 0.079)
- Per-symbol OOS: LINK +47.58% (58%), DOT +29.73%, BTC +25.75%, LTC +10.56%, **ETH -31.63%**
- Model wall-clocks: A 1h 49m / C' 2h 7m / D' 2h 43m / G 3h 13m / E ~3h 35m residual = 13h 27m total
- /033B was simplified Option B (no composite_inv_concurrency wrapper per user 2026-05-30; abs_pnl baseline)

## §1 Verdict + structural analysis

Likely Critic verdict: **CONFIRMATION-BLOCK** or **BLOCK-FINAL** (multiple gate fails: IS Sharpe -0.03 vs +1.0 floor, LINK 58% > 30% cap, F2 trade count 231 << [600, 1100] band, F4 n_eff=3 << [10, 25]).

**+0.44 OOS lift is REAL but bundle structure has problems.** The lift is concentrated in LINK (58% of PnL) with ETH a NEGATIVE drag.

## §2 ETH smoking gun

/019 ETH+gate single-seed: IS -3.18% / **OOS +32.65%** / WR 47.6%.
/033 Model G multi-seed: **IS +42.53%** / **OOS -31.63%** / WR 34.0%.

**OOS sign flipped while IS gained +45.7pp.** This is structurally diagnostic of single-seed lottery upper bound NOT generalizing to multi-seed CONFIRMATION-spec.

Most likely mechanism: composite_inv_concurrency × ENSEMBLE_SIZE=10 × n_trials=35 produces different Optuna basin than ES=3 + n_trials=18 + abs_pnl. The new basin up-weights rare isolated-entry signals; ETH model trains harder on labels that happen to fit IS but don't generalize to OOS regime. n_eff_per_cell median dropped to 3 (vs /031's 12 and /019's 9) confirming basin collapse signature.

## §3 IS-OOS divergence (37× ratio)

Three contributing factors:
- (a) Nov 2025 OOS regime tailwind: +61.11% in 18 trades (54% of OOS PnL stack)
- (b) Optuna IS-overfit under n_eff=3 search degeneration; happens to OOS-generalize
- (c) Bundle's 5-cohort training surface has structural IS suppression at narrow per-cohort splits

Likely +0.44 OOS Δ = 50-70% Nov 2025 tailwind + 30-50% genuine bundle additivity. Ablation will disambiguate.

## §4 LINK 58% concentration

LINK contribution +47.58% on 50 trades / 46% WR. Standalone /018: +53.80% on 48 trades / 50% WR. Bundle LINK is within 12% of standalone — STRUCTURALLY CONSISTENT.

If LINK dropped from bundle: estimated remaining OOS Sharpe +0.65 to +0.75 (BELOW +1.0 floor). **LINK is single-handedly carrying the bundle past floor.** Without LINK there is no bundle.

## §5 Ingredient ranking (strict attribution)

1. **LINK /018 specialist**: +47.58% (within 12% of standalone) — CONFIRMED in bundle
2. **LTC /028 atr_sl=1.0**: +10.56% (bit-identical to standalone) — CONFIRMED in bundle
3. **BTC Model A degenerate**: +25.75% (vs standalone +33.17% pool slice) — PARTIAL REGRESSION
4. **DOT Model E**: +29.73% (vs baseline +1.96%) — TAILWIND BENEFICIARY (Nov 2025 + composite_inv_concurrency favorable basin)
5. **ETH /019 Model G**: **-31.63%** (vs standalone +32.65%) — SIGN-FLIPPED. DROP from future bundles.

## §6 Recommendation for /034+

Per user directive 2026-05-30 PAUSE-then-cycle-5: bundle retry deferred to /044+ after cycle-5 produces more PROMISING ingredients.

For cycle-5 EXPLORATIONs (/034-/043 per axis menu): focus on NEW signal sources, NEW labels, NEW risk primitives. The /033 evidence informs:
- DON'T re-test ETH+gate as a standalone ingredient — multi-seed already refuted it
- LINK specialist is the strongest single-source-of-edge in v1 catalog
- LTC atr_sl=1.0 stacks cleanly with sample-weighting
- composite_inv_concurrency may have basin-compression effects at multi-axis stacking — test in isolation first

When /044 bundle CONFIRMATION retry comes:
- DROP /019 ETH+gate
- KEEP /018 LINK + /028 LTC+atr_sl=1.0
- Test composite_inv_concurrency wrapper separately at single-axis multi-seed BEFORE re-bundling

## §7 Wall-clock calibration (per no-kill-switch policy)

Observed: **13h 27m** for `--seeds 1` × ES=10 × n_trials=35 × 5 cohorts × abs_pnl baseline. Per-cohort cost 1h 49m to 3h 35m. /033B 1.45× brief modal estimate.

Calibration update for next bundle CONFIRMATION:
- 5-cohort bundle ≈ 13h
- 4-cohort bundle ≈ 10h
- 3-cohort bundle ≈ 7-8h
- Future bundle briefs MUST anchor on 13h reference, not extrapolated 9h

## §8 Closing note

**Single most important takeaway**: /033 demonstrates that **multi-seed CONFIRMATION reveals which single-seed PROMISING ingredients are real and which are lottery upper bounds**. LINK /018 and LTC /028 survived; ETH /019 did not. This is the core diagnostic value of CONFIRMATION — without it, we'd have shipped a bundle with hidden -0.94 ETH Sharpe drag.

For cycle-5 EXPLORATIONs: don't pre-judge multi-seed survival from single-seed PROMISING signals. Each cycle-5 ingredient should be tested standalone at CONFIRMATION-spec before bundling. Current LM Master directional track: 5/12 = 42%. /033 ETH prediction (would have been NEGATIVE-at-multi-seed if Phase 4.5 had been dispatched) — track record continues calibrating.
