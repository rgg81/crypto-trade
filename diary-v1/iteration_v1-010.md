---
iteration: iter-v1/010
date: 2026-05-25
verdict: EXPLORATION-NEGATIVE
subtype: PROMISING-INERT-with-IS-basin-shift
axis_family: risk-primitive
axis: R5 vol-target ceiling (uniform 4.0%, applied AFTER R2 in vt_scale)
cadence_position: cycle-2 EXPLORATION #5 of 10
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c)
merge_decision: NO-MERGE (axis stays on branch only)
---

# Iteration iter-v1/010 — Diary

## One-Line Outcome

R5 vol-target proportional-scaling ceiling fired mechanically (IS 23.23% / OOS 18.57%) but produced an OOS Sharpe Δ within the INERT band (-0.0283) on top of an IS Δ overshoot (+0.4701) driven entirely by a single-symbol single-seed Optuna basin lottery on LTC — proportional-scaling R5 family CLOSED at v1 single-seed EXPLORATION, mirroring the v3/020 universal pattern.

## What Was Tested

**Axis**: R5 vol-target ceiling — uniform `vol_target_pct = 4.0%` applied AFTER R2 in the vt_scale pipeline. Cap formula: `r5_scale = min(1.0, 4.0 / max(NATR_14, 0.01))`. R5 NATR lookup loaded from per-symbol feature parquets at backtest init (`backtest.py:207-238`). IS/OOS-split fire counters added to comparison.csv via `reporting_v1.append_r5_rows_to_comparison`.

**Spec**: EXPLORATION mode, single-seed=42, ENSEMBLE_SIZE=3 (inner seeds `[42, 123, 456]`), n_trials=35, ≤2h cap. All 4 models (A pooled-BTC+ETH, C LINK, D LTC, E DOT) received R5 enable. Universe + feature columns + ATR multipliers + R1/R2/R3 unchanged.

**HIGH-RISK declaration**: yes (R5 multiplies into `weight_factor` which is the same quantity Optuna's CV scoring sees in its `mean_oos_sharpe` objective via the lgbm CV labels — axis changes the Optuna training-objective domain). HIGH-RISK pre-commit-to-CONFIRMATION tripwire correctly did NOT fire (PROMISING gate not satisfied).

**Implementation**: 4 src/ files (`backtest_models.py`, `backtest.py`, `reporting_v1.py`, `run_baseline_v1.py`) + 1 test file (`tests/test_iteration_v1_010_r5.py` — 211 lines, 6 test cases). Three commits on branch: `f316dae` (R5 wiring) + `22cf829` (tests + A14 NATR_14 guard) + `54ef223` (IS/OOS-split fire counter).

## Headline Metrics

From `reports-v1/iteration_v1-010/comparison.csv`:

| Metric | IS | OOS | Baseline IS | Baseline OOS | IS Δ | OOS Δ |
|---|---|---|---|---|---|---|
| **Monthly Sharpe** | **+0.7530** | **+0.6354** | +0.2829 | +0.6637 | **+0.4701** | **-0.0283** |
| Sortino | +0.8084 | +0.7793 | +0.3205 | +0.7697 | +0.4879 | +0.0096 |
| Max Drawdown | 70.80% | 38.24% | 73.06% | 40.94% | -2.26pp | -2.70pp |
| Win Rate | 40.6% | 44.8% | 39.9% | 40.2% | +0.7pp | +4.6pp |
| Profit Factor | 1.1663 | 1.1384 | 1.060 | 1.156 | +0.106 | -0.018 |
| Total Trades | 663 | 210 | 621 | 189 | +42 | +21 |
| Calmar | 1.8745 | 0.9147 | 0.740 | 0.931 | +1.135 | -0.016 |
| DSR | -43.49 | -38.10 | -93.80 | -35.66 | +50.31 | -2.44 |
| Total Net PnL | +132.72% | +34.98% | +54.05% | +38.13% | +78.67pp | -3.15pp |
| PSR_monthly_vs_0 | 0.876 | 0.760 | 0.977 | 0.989 | -0.101 | -0.229 |
| PSR_monthly_vs_1 | 0.287 | 0.353 | 0.0003 | 0.0789 | +0.287 | +0.275 |

**R5 fire rates** (from comparison.csv rows 16-17): IS portfolio fire rate = **23.23%** / OOS portfolio fire rate = **18.57%**. Both inside the brief's F2 reasonable activation band [10%, 60%].

**Per-symbol attribution** (from `in_sample/per_symbol.csv` + `out_of_sample/per_symbol.csv`):

| Symbol | IS net_pnl | IS pct_total | OOS net_pnl | OOS pct_total |
|---|---|---|---|---|
| LTCUSDT | **+79.98** | **+119.84%** | -43.52 | -43.50% |
| LINKUSDT | +32.33 | +48.44% | +80.92 | +80.88% |
| DOTUSDT | +17.99 | +26.95% | +29.13 | +29.12% |
| ETHUSDT | -19.40 | -29.06% | -11.36 | -11.35% |
| BTCUSDT | -44.16 | -66.16% | +44.88 | +44.86% |

**The verdict-binding fact**: LTC IS pct_of_total_pnl = 119.84%. Single symbol drove the entire IS portfolio gain (other 4 symbols collectively NET NEGATIVE on IS at -95.22% offset partially recovered by LINK 48.44% + DOT 26.95%). LTC alone moved from baseline +3.27 (6.42% share) to +79.98 (119.84% share) — a +76.7pp absolute jump.

**OOS roster overlap with baseline = 17.1%** (LM Master Phase 7.4 computation): for a STATELESS gate firing on 18.6% of signals, the expected baseline-roster-identical trades should be ~81% (the 81.4% of signals where R5 didn't fire); observed 17.1% means **75% of the roster turnover is Optuna basin re-routing**, not R5 mechanical filtering. Failure Mode 4 (Optuna re-optimization finds new IS-overfit basin) fired.

**F1-F5 verdict matrix**:

| F | Condition | Observed | Status |
|---|---|---|---|
| F1 (PRIMARY) | OOS Δ ≥ -0.05 | -0.0283 | PASS literal |
| F2 (behavioral) | OOS fire rate ∈ [10%, 60%] | 18.57% | PASS |
| F3 | IS Δ ≥ -0.10 | +0.4701 | PASS literal lower; **NO UPPER-BOUND CLASS** (verdict-gap) |
| F4 (degenerate) | 0 IS / 0 OOS | 0 / 0 | PASS |
| F5 (DSR computable) | n_eff_per_cell_median ≥ 4 | 13 | PASS |
| Trade-rate floor | ≥10/month AND ≥130 OOS | 16.2/month + 210 OOS | PASS |

All falsifiers literal-PASS; the verdict comes from the Section 8 verdict-gap (no class for `IS Δ > +0.05 AND OOS Δ ∈ [-0.05, +0.05]`) + Critic Check 6 substantive FAIL on LTC concentration.

## LM Master Pre-Design vs Post-Mortem Calibration Discrepancy

LM Master Phase 4.5 (`briefs-v1/iteration_v1-010/lgbm_advisor.md` §1 "Mechanism Critique"):

> **Most likely: NO, Optuna will NOT meaningfully re-route.** Single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3 is below the variance-reduction threshold needed to discover a NEW high-confidence-low-vol entry distribution. The oracle's -0.020 OOS Δ is the modal outcome.
> ...
> **Empirical evidence**: per Section 2.4 oracle, R5 cuts LINK IS by 28.62pp + LTC IS by 12.28pp. ETH IS gains +7.10pp...For Optuna to FLIP this NEGATIVE → POSITIVE, it would need to find a hyperparameter region where LINK's high-vol entries are predicted as LOWER-confidence (so position size redirects to BTC/ETH at lower NATR). The signal:noise ratio for that flip at n_trials=35 single-seed is ~10-15% — possible but unlikely.
> ...
> **Most likely path**: Optuna re-converges to a near-baseline basin; trade roster ~85% identical to oracle; F1 verdict = -0.05 to +0.02 (PROMISING-INERT).

LM Master Phase 7.4 (post-mortem, same file lines 76-148):

> **Calibration update — Track Record 0/8 Directional + 2 PARTIAL.**
> **Verdict class correct (PROMISING-INERT band at OOS Δ -0.0283).** Basin-shift call **directionally wrong**: the +0.47 IS lift is a textbook Optuna re-routing event, not the ~85% roster-identity I anchored on. Roster intersection is 165/663 = **24.9% on IS** and **17.1% on OOS**. I underweighted three factors:
> 1. **Config mismatch with baseline**: baseline is 5-seed × n_trials=50 = 250 fits/cell; /010 is 3-seed × n_trials=35 = 105 fits/cell. The 24.9% intersection isn't pure R5 — it's R5 + halved Optuna budget + reduced seed averaging.
> 2. **R5's gradient signal was nonzero on the loss surface**: 74.8% of /010 IS trades sit at weight<0.5 (vs baseline 69.7%) — a 5pp shift that I dismissed as below SNR floor. It was AT the floor.
> 3. **The "modal outcome" assumption was wrong for single-seed=42 EXPLORATIONs**: at this Optuna budget every R-primitive change WILL find a new basin because the search space is over-parameterized relative to the trial count.
> ...
> **New rule for Phase 4.5 going forward**: when the axis multiplies the loss directly (position-sizing weight, label weight, sample weight), basin-shift probability is HIGH (40-60%) at single-seed budgets, NOT 10-15%.

**Calibration discrepancy summary**: LM Master predicted basin-shift probability ~10-15% at single-seed; observed basin-shift on LTC was a 24× multiplicative move in IS PnL with 24.9% IS / 17.1% OOS roster overlap (vs predicted 85%). The directional miss is on the order of 3-4× on the basin-shift probability axis. The verdict-class prediction (PROMISING-INERT band, 70% confidence) was correct on the literal OOS reading, but LM Master itself notes (Phase 7.4 line 147): *"the IS +0.47 is not durable signal and should not influence /011 staging."*

**LM Master track record after /010**: 1/6 directional Sharpe predictions correct (across /005-/010) with one PARTIAL. The new rule (basin-shift HIGH 40-60% for position-sizing-weight axes at single-seed) is load-bearing for /011 brief authoring and future risk-primitive briefs.

## Critic Path Forward (verbatim from review.md §"Path Forward")

> Per LM Master Phase 7.4 §"Path for /011" the convergent recommendation is **NATR > 7% binary kill switch** (universe p90 cutoff; STATELESS risk-primitive sister axis to /010's proportional scaling). Critic concurs as PRIMARY. Three options:
>
> 1. **R5-BINARY-KILL — risk-primitive** (LM Master Phase 7.4 PRIMARY recommendation; convergent with Critic). Skip entry if NATR_14 > 7% (universe p90). State-discontinuous primitive vs /010's smooth attenuation. Predicted fire rate: ~10% (per /010 EDA Section 2.1 universe p90 average ≈ 6.3%, slightly above the 7% threshold means kill fires modestly more than once per 10 trades). EDA basis already exists in /010 Section 2.1 — no new Phase 1 work needed. Mechanism: tests whether the "concentration is signal" v3/020 finding generalizes to v1 specifically for the high-NATR tail vs the proportional middle. STATELESS — oracle EDA on /010's roster is fully valid. Pre-flight is fast. 2h cap easily met.
>
> 2. **TRIPLE-BARRIER σ_t SOURCE — labeling** (NEW axis; structurally orthogonal to risk-primitive). Currently triple-barrier σ_t uses past-only EWMA. The labeling-window σ_t can alternatively use a different lookback (e.g., 24h vs 7d) which changes the effective ATR-noise threshold. This is NOT a /004-style atr_tp/atr_sl knob tweak — it's a structural change to the σ_t denominator that re-shapes the label distribution PER-CELL. Predicted effect: a re-shaped σ_t with shorter (24h) lookback should produce tighter SL bands and more take_profit hits; longer (14d) should produce wider SL bands. EDA basis: /010 Section 2.1 NATR distributions can be re-computed with 24h and 14d windows in 30min. Single-seed EXPLORATION at 2h cap. Risk: this is a 4th-consecutive HIGH-RISK declaration if it modifies the labeling pipeline; multi-seed pre-commit if PROMISING.
>
> 3. **PER-CELL EARLY-STOP — methodology** (UNUSED at /005-/009 since /008's PCA closure; structurally orthogonal). Currently LightGBM trains for `num_iterations` rounds per cell with `early_stopping_rounds = 50` per cell. A per-cell early-stopping refactor where the CV-fold uses a separate hold-out within each fold (Purged-CV inner hold-out, NOT the outer test fold) could meaningfully reduce the n_eff_per_cell architectural ceiling at n_eff = 13. Predicted effect: byte-IDENTICAL on the PROMISING-INERT axis (methodology preserves predictions per /001 + /008 precedent) but reveals new diagnostic infrastructure that the future /012+ /013+ feature-family / model-arch EXPLORATIONs can use to distinguish capacity-fit-noise from genuine edge at single-seed. PROMISING-METHODOLOGY subtype expected, non-compoundable.
>
> Constraints honored: each proposed axis is from a family the QR has NOT used in the prior 5 EXPLORATIONs.
>
> LM Master Phase 7.4 PRIMARY recommendation (option 1) is the strongest convergent signal — Critic concurs. Options 2 and 3 are orthogonal alternatives.

## Next Iteration Ideas (ranked from Critic Path Forward)

**Ranking criteria**: convergence between LM Master + Critic + QR; structural orthogonality to /010's failure mode; UNUSED family vs the prior 5; EDA basis readiness.

### Option A (PRIMARY): R5-BINARY-KILL — risk-primitive (UNUSED-subtype within prior-5-non-family-conflict)
- **Axis**: skip entry if NATR_14 > 7.0% (universe p90 cutoff).
- **Family**: `risk-primitive` (binary-kill SUBTYPE; structurally orthogonal to /010's proportional scaling).
- **Rationale**: 3-way convergent recommendation (LM Master Phase 7.4 + Critic Phase 7.5 + QR Phase 7 memo). State-discontinuous mechanism — sister to v3/020's "concentration is signal" finding's binary kill primitive proposal. STATELESS per `feedback_v3_oracle_eda_validity.md`; oracle EDA on /010's trade roster is methodologically valid.
- **EDA readiness**: /010's `analysis/iteration_v1-010/per_symbol_is_natr14_distribution.csv` already has universe p90 = 6.3% — the 7% threshold is just above p90 (modest fire rate ~10%). No new Phase 1 work required.
- **Predicted outcome**: PROMISING-INERT (most likely) or marginal-NEGATIVE; if NEGATIVE, binary-kill subtype is also CLOSED at single-seed and /012 must pivot to a completely UNUSED family (labeling, or methodology, or a NEW universe extension).
- **HIGH-RISK declaration**: probably YES (binary kill changes which trades enter; modifies the Optuna reward distribution). Pre-commit to /012 multi-seed CONFIRMATION IF /011 PROMISING.
- **Axis Rotation status**: prior 5 = [universe(006), feature-family(007), methodology(008), feature-family(009), risk-primitive(010)]. /011 = risk-primitive would be 2nd consecutive risk-primitive in cycle-2. Rotation discipline allows this (majority of prior 5 are NOT risk-primitive), but the brief Section 0.6 should explicitly note the within-family subtype distinction (binary-kill vs proportional-scaling).

### Option B: TRIPLE-BARRIER σ_t SOURCE — labeling
- **Axis**: change σ_t lookback window for triple-barrier (e.g., 24h vs 7d EWMA).
- **Family**: `labeling` (UNUSED in cycle-2 to date; appeared only at /004 in cycle-1).
- **Rationale**: structurally orthogonal to risk-primitive; re-shapes label distribution per-cell (NOT a /004-style atr_tp/atr_sl knob tweak, which was already tested NEGATIVE).
- **EDA readiness**: needs ~30min Phase 1 work to recompute NATR_14 with 24h + 14d windows. Achievable in EXPLORATION 2h cap.
- **Risk**: 4th-consecutive HIGH-RISK declaration (label-mode change qualifies). Multi-seed pre-commit IF /011 PROMISING.
- **Predicted outcome**: PROMISING-INERT (most likely) — shorter σ_t lookback produces tighter SL bands; depending on universe NATR_p50 the SL-noise-floor death pattern from /004 may re-emerge.

### Option C: PER-CELL EARLY-STOP — methodology
- **Axis**: LightGBM per-cell early stopping with Purged-CV inner hold-out.
- **Family**: `methodology` (UNUSED since /008 PCA closure).
- **Rationale**: structurally orthogonal; reduces n_eff_per_cell architectural ceiling at n_eff=13.
- **EDA readiness**: pure infrastructure work; no Phase 1 EDA needed.
- **Predicted outcome**: PROMISING-METHODOLOGY (non-compoundable per /001 + /008 precedent); byte-identical on F1; provides new diagnostic infrastructure for future axes.
- **Trade-off**: high-value structural improvement BUT non-compoundable — does NOT directly produce edge ingredient. /011 spent here means /012+ benefits but cycle-2 cadence count still advances.

**QR Phase 8 recommendation**: PRIMARY = Option A (R5-BINARY-KILL) per 3-way convergence + EDA-ready + structurally orthogonal to /010's mechanism. The within-family subtype distinction (binary-kill vs proportional-scaling) is the structural orthogonal; not a knob-tuning trap. /011 brief Section 0.6 must explicitly declare the subtype distinction to clarify Axis Rotation status.

## Cycle-2 Cadence Status

| Iteration | Family | Verdict |
|---|---|---|
| /006 | universe | EXPLORATION-NEGATIVE (DEGENERATE_PREDICTOR) |
| /007 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| /008 | methodology | EXPLORATION-PROMISING-METHODOLOGY |
| /009 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| **/010** | **risk-primitive** | **EXPLORATION-NEGATIVE (PROMISING-INERT-with-IS-basin-shift)** |

**Cycle-2 EXPLORATION count after /010: 5 of 10.** CONFIRMATION-eligible at /015 earliest (5 more EXPLORATIONs required before any CONFIRMATION can launch).

**Cycle-2 verdict distribution**: 0 PROMISING / 1 PROMISING-METHODOLOGY (non-compoundable) / 4 NEGATIVE. No edge ingredient bundled yet. The cycle is consistent with v1 cycle-1's pattern (4/5 NEGATIVE before /008 closeout).

## HIGH-RISK Pre-Commit Tripwire — Saved Compute

Per /010's Section 2.5 HIGH-RISK declaration, the multi-seed tripwire fires only if /010 verdict = PROMISING. Verdict = EXPLORATION-NEGATIVE → tripwire correctly does NOT fire. This is the **7th-consecutive correct non-firing** of the HIGH-RISK pre-commit (across /003 + /004 + /005 + /006 + /007 + /009 + /010 — all 6 HIGH-RISK iterations on /003-/010 except /008 which was methodology-only).

**Cumulative compute saved**: ~42h across 7 iterations (6h per averted multi-seed CONFIRMATION at 10-seed × ENSEMBLE=10 × n_trials=50). Discipline is battle-tested over 7 independent HIGH-RISK iterations without producing a false-positive CONFIRMATION dispatch.

## Permanent Catalog Additions (from /010 closeout)

1. **Catalog axiom — proportional-scaling R5 family CLOSED at v1 single-seed**: extends `feedback_v3_concentration_is_signal.md` v3/020 to v1 5-symbol universe. Future risk-primitive iterations must use STATELESS BINARY KILL primitives OR vol-target ceilings at multi-seed only. Permanent v1 catalog entry.

2. **LM Master Phase 4.5 calibration rule update — basin-shift probability HIGH for position-sizing-weight axes**: 40-60% at single-seed budgets (NOT 10-15% as previously calibrated). Applies to all future risk-primitive briefs; LM Master Phase 4.5 advisories must default to LOW directional confidence when the axis touches the position-sizing weight OR sample weight OR loss function. Permanent catalog rule.

3. **Critic Rec #1 — Section 8 verdict gates must be sign-symmetric on F3**: future risk-primitive briefs (and any HIGH-RISK brief on a position-sizing-weight axis) MUST pre-register a fourth verdict class `PROMISING-INERT-with-IS-overshoot` (F1 in INERT band AND F3 > +0.05) and `catastrophic-basin-shift` (F3 > +0.30). Phase 5.5 gate enforces inclusion. Permanent skill/template update.

4. **Reproducibility defect — comparison.csv r5_fire_rate column labels invert IS/OOS**: documented for /011 patch in `reporting_v1.append_r5_rows_to_comparison` (rows have numerical values in correct rows by metric name but the column header schema disambiguates by position not by row name). Not verdict-binding; fix is one-line. Defect ID: **D-RPRT-001**.

5. **Instrumentation gap — r5_fire_log.csv and feature_importance.csv missing for /010**: brief Section 10.3 promised both; neither implemented. Phase 7.4 LM Master flagged feature_importance.csv as "v3/016 fix hasn't been ported to v1". If /011 = R5-BINARY-KILL, the QE spec MUST include both files. Defect ID: **D-RPRT-002** (r5_fire_log.csv) + **D-INST-001** (feature_importance.csv emission).

## Lessons

1. **Single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3 has finite resolution on position-sizing-weight axes.** When the axis multiplies into the loss directly, Optuna will find a new basin with ~40-60% probability — not the ~10-15% LM Master previously assumed. This is now a load-bearing rule for /011 and beyond.

2. **OOS roster overlap with baseline is a load-bearing post-mortem diagnostic.** Expected overlap for a STATELESS gate firing on F% of signals is (1 - F)% baseline-identical trades. /010's observed 17.1% vs expected 81% means 75% of the turnover is loss-surface re-routing. Future briefs Section 4 should add a falsifier on roster-overlap to surface basin shifts directly.

3. **Per-symbol IS Δ asymmetry of 3 orders of magnitude is a signature of basin lottery, not noise.** LTC IS net_pnl +24×; LTC OOS net_pnl +1.08×. The asymmetry rules out symmetric noise models; the iteration's true diagnostic was concentration + roster-overlap, not the headline Sharpe Δ.

4. **Brief Section 8 verdict gates are not safe by default.** /010 fell into an unregistered region (`IS Δ > +0.05 AND OOS Δ ∈ [-0.05, +0.05]`). Future risk-primitive briefs must pre-register the four-corners region of IS×OOS space, not just the diagonal "small drift" and "catastrophic miss" subsets.

5. **The R5 implementation infrastructure on branch is not wasted.** R5 config wiring + IS/OOS fire counter + tests + NATR lookup loader all on `iteration-v1/010` branch. STAYS on branch (NO trunk merge per EXPLORATION-NEGATIVE rule), but available for the next R5-axis attempt — including the recommended R5-BINARY-KILL at /011 (binary-kill subtype shares the NATR lookup infrastructure).

## Files & Commits on Branch

- Branch: `iteration-v1/010` from `iter-v1/009` closeout commit
- HEAD before Phase 7: `7abfbaf` (Critic Phase 7.5 review)
- HEAD after Phase 7+8: see closing commit SHAs

Key commits in this iteration:
- `5506507` — QR Phases 1-5 + R5 vol-target calibration + brief
- `e03c138` — LM Master Phase 4.5 pre-design advisory
- `9e0287b` — Phase 5.5 gate PASS
- `f316dae` — R5 vol-target ceiling wiring (post-R2 hook, configurable threshold)
- `22cf829` — R5 unit tests + A14 NATR_14 guard
- `7e500ed` — Critic Phase 6.0 pre-flight PASS
- `54ef223` — R5 IS/OOS-split fire counter + comparison.csv r5_fire_rate rows
- `6d1bba9` — LM Master Phase 7.4 post-mortem
- `7abfbaf` — Phase 7.5 Critic review — EXPLORATION-NEGATIVE

Trunk merge: **NONE**. EXPLORATION-NEGATIVE never merges to main.

Tag: `v0.v1-010` (after Phase 8 commit).
