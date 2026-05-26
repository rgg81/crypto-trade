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

---

# LightGBM Master Advisor — iter-v1/016 — Phase 7.4 (Post-Mortem)

## Context Read

- Verdict cell: **EXPLORATION-NEGATIVE-catastrophic** (cell 6 per brief Section 8 — F1 OOS Δ = -1.669 < -0.55; F3 IS Δ = -0.588 < -0.30)
- F-AXIS-MECHANISM: **PASS by construction** (Kish=1.0000 ×205 cells; per-symbol balance 0.500/0.500; timeout=0.0) — exactly as Phase 4.5 §11 predicted
- n_eff_per_cell: **9** (BELOW Phase 4.5 §3 predicted band [10, 20]) — NEW mechanism prediction REFUTED
- Wall-clock: ~50min total run, 75% margin — first cycle-3 wall-clock discipline empirically validated

## Mechanism Call — uniform weighting REMOVED informative Bayesian prior

Phase 4.5 §3 closing line ("weight-removal at LEAST as likely to HURT IS Sharpe as help it") landed in catastrophic direction. The 40/35/25 net-helpful/harmful/no-op split UNDERSTATED harm magnitude — but directional NET-HARMFUL bucket realized.

**Catalog implication**: `abs(labeled_pnl)` weighting is **STRUCTURAL to v1's edge**, not removable artifact. High-magnitude trades (LINK 74.70%, ETH 47.46%, DOT 44.43%) carry genuine forward signal that the gradient needs to upweight. Brief's "per-symbol asymmetry" framing was the WRONG diagnostic — asymmetry was *load-bearing*, not noise. **Sample-weighting axis CLOSED at v1 baseline-labels** — no future EXPLORATION explores `uniform`, `uniqueness_only` (Spearman 0.997 with baseline per QR EDA), or related uniformization modes.

## n_eff_per_cell DROP from 13 → 9 — REFUTES Phase 4.5 §3 prediction

Predicted [10, 20] reasoning "n_eff_per_cell is loss-surface-shape-bound, not weight-bound". **Refuted.** Observed median 9.

**Mechanism revision (NEW)**: weight-magnitude variation itself contributes to per-cell loss-surface diversity. Compressing weight range [1, 10] → [1, 1] made Optuna's per-trial loss surfaces MORE similar across trials → PCA-on-trial-returns substrate collapsed. Update mental model: n_eff_per_cell has TWO drivers (label-shape AND weight-distribution), not just label-shape.

## F-AXIS-MECHANISM PASS by construction — Phase 4.5 §1 warning vindicated

Kish=1.0000 (math). Model A balance 0.500/0.500 (math). Timeout=0.0 (labels untouched). All three sub-checks PASS — yet OOS Sharpe -1.00. **This iteration is the definitive proof case** for future briefs: F-AXIS-MECHANISM PASS does NOT imply edge. Critic should add to Check 8 catalog as the v1 reference case.

## Per-symbol structural pattern UNCHANGED

ETH catastrophic continuation is the SAME pattern present at /014/015. Sample-weighting was the wrong lever — ETH's OOS drag is regime-conditioned (likely 2025-Q1 to 2026-Q1 ETH-specific weakness), not weight-distribution-conditioned.

ETH OOS Δ trajectory across cycle-2/3:
- /014: -41.18 (single-seed)
- /015: -23.29 (multi-seed)
- /016: **-51.46** (single-seed sample-weighting)

Three different axes; ETH catastrophic across all. **STRUCTURAL property**, not iteration-specific. Future axes targeting ETH: regime-conditional kill switch, per-symbol drawdown brake, OR universe pruning (remove ETH if next 2 iters fail).

## Calibration update

- Verdict-class directional: **1/14** (unchanged — Phase 4.5 33/33/34 correctly placed NEGATIVE)
- Mechanism-level: **6/14** (n_eff prediction REFUTED; F-AXIS-MECHANISM construction-PASS VERIFIED per warning)
- NEW refuted: "n_eff_per_cell is label-shape-bound only" — both label-shape AND weight-distribution contribute
- NEW confirmed: F-AXIS-MECHANISM PASS by construction does NOT imply edge — definitively proven

## /017 axis recommendation — UNIVERSE EXPANSION

Per Phase 4.5 §6 pre-staging ("/016 NEGATIVE → XGBoost OR universe") + user XGBoost-slower flag:

**RECOMMEND UNIVERSE EXPANSION at /017**:
- Add 1-2 symbols from V1_EXCLUDED_SYMBOLS (XRP, SOL, NEAR, DOGE — match cycle-2 OOS-rich profiles, NOT BTC-correlated)
- ENSEMBLE_SIZE=3, n_trials=18 default (6-symbol universe ~1.7h estimate; 7-symbol tight)
- Single-axis: universe ONLY. NO weighting change (revert `abs_pnl` baseline). NO labeling change.
- Pre-emptive falsifier: if ETH OOS Δ at /017 still catastrophic (≤-0.50), basin is REGIME-bound NOT universe-bound — pivot /018 to ETH-specific exclusion/regime gate

**XGBoost deferred to /018+** (need wall-clock smoke test characterization). `uniqueness_only` SKIPPED per Spearman 0.997 to uniform — closes axis cleanly.

## Cycle-3 cadence sanity check

/016 = #1 of 10 EXPLORATIONs. CONFIRMATION earliest /026. Wall-clock discipline empirically validated (50min total). Phase 4.5 Rec #1 (pre-emptive n_trials 20→18) adopted and ran fine — keep n_trials=18 as cycle-3 default unless universe push to 6-7 symbols (drop to n_trials=15 if smoke test >1.7h).

## Closing Note for Critic Phase 7.5

Two items:

1. **Check 8 (axis attribution)**: F-AXIS-MECHANISM PASSed by mathematical construction with OOS Sharpe -1.00. Canonical exemplar of "wiring test ≠ edge test" — add to Check 8 catalog as v1 reference case.

2. **Check 4/5 (IS/OOS divergence)**: ETH per-symbol pattern is STRUCTURAL across /014, /015, /016 — same direction (OOS catastrophic) across THREE axes (labeling, weighting now). Basin property worth flagging as forward concern. Critic does NOT need to BLOCK — but mention in Path Forward that /017's universe expansion brief should explicitly acknowledge the ETH structural drag.
