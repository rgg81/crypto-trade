# LightGBM Master Advisor — iter-v1/016 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/016`. HEAD `8a9ba1f`. **FIRST cycle-3 EXPLORATION** under STRICT 2h wall-clock (skill `4cb8972`).
- **Baseline**: `v0.v1-baseline-corrected` (`f8bc12c`). IS +0.2829 / OOS +0.6637. UNCHANGED through cycle-2.
- **Cycle-2 closeout**: 10 iterations, 1 PROMISING-METHODOLOGY (/008 non-compoundable) + 9 NEGATIVE + 0 merges. v1 BASIN-LOCK pattern confirmed.
- **Track record**: 1/13 verdict-class directional, 6/13 mechanism-level PARTIAL+, **0/13 verdict-class magnitude**. Modal-NULL prior empirically anchored.
- **QR's pivot**: Critic /015 Path Forward "weight-by-uniqueness" REFUTED by EDA (Spearman 0.997 with baseline; LightGBM scale-invariant → no Optuna effect). QR identified actual baseline mechanism — per-symbol weight asymmetry via `abs(labeled_pnl)`: ETH over-weighted +4.9% / BTC under-weighted -4.9% in Model A every IS month.
- **Selected intervention**: `sample_weight_mode="uniform"` (replace, not multiply — Critic Path Forward axis #1 corrected).

## Recommended Hyperparameter Direction (4 items)

### Rec #1 — PRE-EMPTIVELY COMPRESS n_trials 20 → 18 upfront

**HIGH confidence.** Brief §3.6.3 upper bound 1.75h gives only 12.5% margin against 2h cap — fails the ≥20% margin requirement. QR's mitigation (smoke-test contingency) is reactive; pre-emptive compression is proactive. Effect: 18/20 = 0.90× = ~6 min saved → upper bound 1.58h → 21% margin secured upfront. n_trials=18 stays well above TPE warmup ~10. **Adopt pre-emptively.** Sample-weighting axis is orthogonal to n_trials sensitivity per §3.6.4 — 2 trials less is invisible at this resolution.

### Rec #2 — Pin `feature_fraction=1.0` AND `bagging_fraction=1.0`

**MEDIUM confidence.** /016 axis is sample-weighting. If Optuna's `feature_fraction` / `bagging_fraction` search continues at default bounds, combined loss-surface perturbation (weights AND subsampling) confounds F-AXIS-MECHANISM attribution. Per v3 EXPLORATION discipline, single-axis EXPLORATIONs sometimes pin subsample dimensions to isolate the axis. **Recommend QE check whether Optuna search currently includes these dimensions; if yes, pin to 1.0 for /016 only.** Bonus: ~5-10% wall-clock saving (no row-/col-shuffle work).

### Rec #3 — n_eff RESTORATION: HIGH confidence Kish→1.000; LOW confidence n_eff_per_cell

**Critical distinction the brief conflates.** Kish n_eff RATIO (uniform = 1.000 exactly by math) is NOT the same as n_eff_per_cell (PCA-on-trial-returns substrate from /008, on which /014 was 19 and /015 was 3). The /015 collapse was driven by **label-distribution shape** (timeout-fallback dominance at 7.82% barriers) — NOT weight concentration. At /016, labels are baseline ATR (51% TP / 38% SL / 10% timeout — 81% entropy). **My prediction: n_eff_per_cell stays near baseline ~13-19 range; uniform weighting does NOT restore it materially** because n_eff_per_cell is loss-surface-shape-bound, not weight-bound. **F-AXIS-MECHANISM #1 (Kish ratio > 0.95) PASS at >99%; the more important n_eff_per_cell signal stays flat.**

### Rec #4 — `min_data_in_leaf` upper bound: do NOT change

Baseline `min_data_in_leaf` Optuna bounds appropriate for per-month training rows (181 in Model A, 89-90 in C/D/E). Sample-weighting does NOT alter row counts — only weights. Axis isolation preserved.

## Mechanism Call — Honest Trade-Off Analysis

Switching `abs(labeled_pnl)` → `uniform`:

**LOSE**:
- High-PnL samples no longer dominate gradient signal. Max abs_pnl is 35.89% (BTC) to 74.70% (LINK). Under baseline, the LINK 74.70% row gets weight 10.0 (5× median weight 2.0). Under uniform, it gets weight 1.0 — same as a 1% TP-hit. **This is removing a Bayesian prior**.
- LightGBM gradient is scale-invariant to GLOBAL multipliers, but RELATIVE weight differences DO change the objective surface.
- Trees with `min_data_in_leaf` constraint will less aggressively split on features that distinguish high-magnitude winners.

**GAIN**:
- Per-symbol balance in Model A: BTC share moves 0.451 → 0.500. **MEDIUM confidence this matters**.
- Worst-cell Kish recovery (D 2025-03 from 0.638 → 1.000). **LOW confidence portfolio-level relevance**.

**Net mechanism call**: weight-removal is at LEAST as likely to HURT IS Sharpe as help it. The Bayesian prior baked into `abs(labeled_pnl)` may be genuinely informative even if structurally imbalanced. **40% net-helpful / 35% net-harmful / 25% net-no-op.**

## Verdict-Class Priors

**FLAT 33/33/34, NOT QR's 55/20/25.**

Reasoning: QR's prior tilts toward NULL based on "LightGBM scale-invariant gradient." This is **half-true**: gradient is scale-invariant to GLOBAL multipliers, but NOT to per-row weight RATIO changes. Going from `abs(labeled_pnl)/max × 9 + 1` (range [1, 10] with structural per-row variance) to `np.ones` (range [1, 1] with zero variance) is a substantive change to the loss-surface objective.

**Mechanism-level**: F-AXIS-MECHANISM #1 (Kish=1.0) at >99% PASS; #2 (per-symbol balance) at >99% PASS; #3 (timeout < 0.6) at >95% PASS. **n_eff_per_cell prediction: stays in [10, 20] range — uniform weighting does NOT restore /015's collapse.**

## Wall-Clock Margin Call

**COMPRESS PRE-EMPTIVELY to n_trials=18.** The 12.5% upper-bound margin violates the new skill's ≥20% requirement. Cost: n_trials 20 → 18 is ~10% trial reduction — invisible at sample-weighting axis sensitivity. Saves overhead of smoke-test sync point.

**Orchestrator decision**: issue n_trials=18 upfront at QE setup. Document as Phase 5.5 compression at brief Section 3.6.3 amendment.

## Risks to Flag for Critic Phase 7.5

1. **F-AXIS-MECHANISM false-PASS risk**: all three sub-checks PASS by CONSTRUCTION under uniform weighting. Wiring test, NOT edge test. Critic should note this explicitly.

2. **n_eff_per_cell prediction NEW band [10, 20]**: if observed jumps ≥30, signals unexpected loss-surface decompression. If drops to ≤5, signals label-distribution shift (defect — weighting shouldn't affect labels). Either extreme triggers Critic Check 5.

3. **Per-symbol concentration may REVERSE**: LINK Model C de-tunes under uniform; LINK OOS share may drop, LTC OOS may improve. PROMISING-MECHANICAL pattern (per-symbol PnL reshuffling without portfolio edge gain).

4. **Wall-clock overshoot**: Rec #1 (pre-emptive compression) is THE mitigation.

5. **Basin-lottery direction undetermined**: brief §2.7 honestly states "expected per-symbol Δ unknown direction." Critic should NOT treat negative Sharpe Δ as catastrophic; F1 band [-0.30, +0.30] is FLAT-prior NULL.

## /017+ Conditional Pre-Staging

- **/016 PROMISING (OOS Δ ≥ +0.20)**: NOT multi-seed CONFIRMATION at /017 (cycle-3 10:1 cadence; CONFIRMATION at /027 minimum). /017 = `sample_weight_mode="uniqueness_only"` alternate.
- **/016 NULL** (~33%): /017 = `uniqueness_only` alternate OR pivot to XGBoost (UNUSED model-arch).
- **/016 NEGATIVE** (~33%): sample-weighting axis CLOSED at v1. /017 = XGBoost OR universe expansion.
- **/016 NEGATIVE-mechanism (F-AXIS-MECHANISM FAIL)**: BLOCK-PENDING-FIX rerun.

## Honest Confidence

**WILLING (HIGH)**:
- F-AXIS-MECHANISM #1 Kish > 0.95: >99% (math)
- F-AXIS-MECHANISM #2 Model A balance |Δ| < 0.02: >99% (construction)
- F-AXIS-MECHANISM #3 timeout-share < 0.6: >99% (labels untouched)

**WILLING (MEDIUM)**:
- LINK Model C IS basin de-tunes: 65%
- Per-symbol OOS PnL reshuffling without portfolio edge: 55%

**NOT WILLING**:
- Portfolio F1/F3 magnitude (per 0/13 track record; FLAT 33/33/34)
- Direction of LTC OOS (MEDIUM 50/50)
- n_eff_per_cell quantitative shift (range [10, 20] wide; not committing to direction)

## What I Did NOT Recommend, and Why

- **`uniqueness_only` for /016**: structurally equivalent to uniform in dense-label regime. Test at /017.
- **`learning_rate`/`num_leaves` bump**: axis isolation; defer.
- **Multi-seed validation at /016**: HIGH-RISK opt-in not triggered.
- **Universe expansion combined**: multi-axis at EXPLORATION is anti-pattern.

## Closing Note

**HIGH confidence in MEDIUM outcome.** Mechanism well-grounded; QR's EDA rigorous; pivot from Critic's "uniqueness multiplied" to "uniform replaces" technically correct and worth running. But sample weighting in dense-label regime with scale-invariant gradient and small per-symbol asymmetry is unlikely to produce portfolio-level edge.

**Modal prediction: NULL with F-AXIS-MECHANISM CLEAN PASS** — closing the axis at uniform after one shot.

Three specific calls staked:
1. Compress n_trials 20→18 upfront (HIGH — wall-clock discipline)
2. F-AXIS-MECHANISM PASS by construction does NOT imply edge — Critic Check 8 should note
3. Modal /016 NULL with per-symbol reshuffling but flat portfolio Sharpe
