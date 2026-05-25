---
iteration: iter-v1/011
date: 2026-05-25
verdict: EXPLORATION-NEGATIVE
subtype: catastrophic-basin-shift (LM Master proposed BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP as forward-looking subtype)
axis_family: risk-primitive (binary-kill subtype)
axis: R5-BINARY-KILL-LOW (skip entry if NATR_14 < 2.0%) — EDA-inverted from convergent kill_high at NATR > 7%
cadence_position: cycle-2 EXPLORATION #6 of 10
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c)
merge_decision: NO-MERGE (axis stays on branch only; OOS magnitude does not override pre-registered verdict-class)
---

# Iteration iter-v1/011 — Diary

## One-Line Outcome

R5-BINARY-KILL-LOW (skip entry if NATR_14 < 2.0%) cleared the OOS Sharpe +1.0 merge floor (+1.0709) but the verdict is EXPLORATION-NEGATIVE — IS Δ +0.4849 fires the pre-registered catastrophic-basin-shift class; the OOS lift is a mechanical-cleanup layer riding on the same single-seed=42 Optuna basin /010 found, NOT a durable axis edge.

## Paradoxical Outcome Summary

This is the most complex verdict cell in v1 cycle-2: the OOS Sharpe (+1.0709) literally clears the +1.0 hard merge floor, yet the pre-registered verdict-class is NEGATIVE. The paradox resolves cleanly via three mutually reinforcing diagnostics:

1. **IS Δ +0.4849** > brief Section 8 catastrophic-basin-shift threshold +0.30 → F3 fires class `catastrophic-basin-shift` which carries "axis CLOSED at single-seed" subsuming any F1 reading.

2. **F6 OOS baseline-roster overlap = 16.7%** (LM Master Phase 7.4 computation; 30 of 180 OOS trades shared with BASELINE) — far below the 61% pre-registered tripwire. A stateless 21.69%-fire-rate filter should mechanically preserve ~78% of the BASELINE roster; the observed 16.7% means 83.3% of /011's OOS roster is entries that BASELINE did NOT take. The filter alone CANNOT produce this — it can only subtract. The 83.3% turnover is Optuna re-routing.

3. **LTC IS roster overlap /010 ↔ /011 = 93.3%** (97 of 104 LTC IS trades) — same Optuna basin re-discovered under mechanically distinct axes (/010 proportional weight scaling on the loss; /011 binary entry filter pre-loss). The IS Δ +0.4849 is NOT first-order kill_low mechanical effect; it is the basin /010 found, rediscovered.

The verdict-class wins. Per Project Mode rules, hard merge gates are necessary-but-not-sufficient layered on top of EXPLORATION-PROMISING verdict, NOT an override of the verdict-class. Brief Section 8 was deliberately built to make IS-overshoot above +0.30 verdict-negative regardless of OOS magnitude, precisely to prevent the false-positive recall pattern this iteration would produce if read on OOS alone.

## What Was Tested

**Axis**: R5-BINARY-KILL-LOW — entry-time NATR floor; STATELESS pre-entry gate at `risk_r5_kill_low_natr_min_pct = 2.0`. When NATR_14 at signal-time candle open is below 2.0%, the entry is skipped (not weight-attenuated). Lives in `backtest.py` BEFORE cooldown / vt_scale / R2 sequence. Distinct from /010's `risk_r5_vol_target` proportional scaling — both fields coexist as independent BacktestConfig flags; /010 axis was DISABLED for /011.

**EDA-driven inversion of convergent recommendation**: the 3-way convergent recommendation (LM Master Phase 7.4 + Critic Path Forward #1 + QR memo /010 closeout) directed /011 to NATR > 7% binary kill. The /011 EDA empirically falsified this — the model's entry-time-conditional NATR p90 OOS is 4.30% (vs the /010 candle-level p90 of 6.3% that the convergent recommendation anchored on). At threshold 7%, OOS skip rate = 0.5% (1 trade); empirically dead. The /011 EDA inverted the direction: at threshold 2.0%, cross-roster sign-agreement on positive OOS Sharpe-Δ (+0.046 BASELINE / +0.115 /010 EXPLORATION) — only candidate threshold across kill_high AND kill_low landing in F2 band [10%, 60%] on both rosters with positive sign on both.

**Spec**: EXPLORATION mode, single-seed=42, ENSEMBLE_SIZE=3 (inner seeds `[42, 123, 456]`), n_trials=35, ≤2h cap. All 4 models (A pooled-BTC+ETH, C LINK, D LTC, E DOT) received R5-BINARY-KILL enable; threshold uniform 2.0% across symbols. Universe + feature columns + ATR multipliers + R1/R2/R3 unchanged.

**HIGH-RISK declaration**: yes (R5-BINARY-KILL is an entry filter that changes which trades enter the loss; modifies Optuna's training-objective domain). HIGH-RISK pre-commit-to-CONFIRMATION tripwire correctly did NOT fire (PROMISING gate not satisfied per pre-registered class — though OOS literal merge-floor pass; class-binding).

**Implementation**: 3-file src/ diff matching brief Section 3.1 exactly (BacktestConfig fields + `backtest.py` entry-gate block before R2 + `run_baseline_v1.py` 4-model kwargs). One commit on branch: `b788d4f` (R5-BINARY-KILL wiring). The existing R5 NATR lookup infrastructure (loaded by /010's wiring) was reused; small refactor of the init guard to fire on either subtype.

## Headline Metrics + Basin Smoking Gun

From `reports-v1/iteration_v1-011/comparison.csv`:

| Metric | IS | OOS | Baseline IS | Baseline OOS | IS Δ | OOS Δ |
|---|---|---|---|---|---|---|
| **Monthly Sharpe** | **+0.7678** | **+1.0709** | +0.2829 | +0.6637 | **+0.4849** | **+0.4072** |
| Sortino | +0.7490 | +1.1940 | +0.3205 | +0.7697 | +0.4285 | +0.4243 |
| Max Drawdown | 54.47% | 39.77% | 73.06% | 40.94% | -18.59pp | -1.17pp |
| Win Rate | 41.8% | 50.0% | 39.9% | 40.2% | +1.9pp | +9.8pp |
| Profit Factor | 1.1807 | 1.2620 | 1.060 | 1.156 | +0.121 | +0.106 |
| Total Trades | 570 | 180 | 621 | 189 | -51 | -9 |
| Calmar | 2.7576 | 1.5413 | 0.740 | 0.931 | +2.018 | +0.610 |
| Total Net PnL | +150.21% | +61.29% | +54.05% | +38.13% | +96.16pp | +23.16pp |
| PSR_monthly_vs_1 | 0.3254 | **0.5663** | 0.0003 | 0.0789 | +0.3251 | +0.4874 |
| **R5-BINARY-KILL fire rate (portfolio)** | **18.34%** | **21.69%** | — | — | — | — |

**OOS/IS ratio = 1.3948** — anti-overfit pattern; rare at single-seed EXPLORATION. Mechanism: OOS lift came from a different stratum than IS lift (mechanical kill_low cleanup on OOS side sitting on basin-lottery substrate on IS side). Not a generalization signal in the traditional sense.

**R5-BINARY-KILL fire rate**: IS 18.34% / OOS 21.69% — both inside F2 band [10%, 60%]; F2 PASSES. EDA oracle predicted IS ~18% / OOS ~18-19%; OOS observed 21.69% is +2.7pp above prediction.

### Basin Smoking Gun

| Comparison | overlap | interpretation |
|---|---|---|
| **LTC IS roster /010 ↔ /011** | **93.3% (97/104)** | Same basin re-discovered across mechanically distinct axes |
| **F6 OOS roster /011 ↔ BASELINE** | **16.7% (30/180)** | 44.3pp below 61% tripwire — catastrophic basin shift on paper |
| **F6 OOS roster /011 ↔ /010** | **93.3% (168/180)** | Mechanically near-identical to /010 basin minus ~12 trades |

### LTC IS pct_of_total_pnl trajectory

| Run | LTC IS pct_total | net_pnl_pct |
|---|---|---|
| BASELINE | +6.42% | +3.27 |
| /010 (proportional R5) | +119.84% | +79.98 |
| /011 (binary-kill R5) | +106.48% | +110.58 |

Same substrate. Mild redistribution toward DOT+BTC. LM Master Phase 7.4 verified roster overlap LTC IS /010 ↔ /011 = 93.3% (97 / 104) — 97 of /011's 104 IS LTC trades are byte-identical to /010's IS LTC trades. The 7 differing trades (filtered out by kill_low because entry-time NATR < 2.0%) account for the modest IS PnL redistribution, NOT a different basin.

### Per-symbol OOS (180 trades)

| Symbol | trades | WR | net_pnl_pct | pct_of_total | /010 OOS Δ | mechanism note |
|---|---|---|---|---|---|---|
| LINKUSDT | 47 | 55.3% | +84.86 | **+59.24%** | +3.94 | basin-inherited (~21pp share drop, +5% PnL incremental) |
| BTCUSDT | 17 | **70.6%** | +51.28 | **+35.80%** | +6.40 | only mechanism-attributable effect (kill_low improved BTC WR 44.7% → 70.6%); small N |
| DOTUSDT | 48 | 45.8% | +29.13 | +20.34% | 0.00 | unchanged from /010 |
| ETHUSDT | 36 | 44.4% | -2.90 | -2.02% | **+8.46** | mechanical recovery (kill_low filtered ETH low-NATR loser cluster) |
| LTCUSDT | 32 | 43.8% | -19.12 | -13.34% | **+24.40** | mechanical recovery (kill_low filtered LTC low-NATR loser cluster) |

**Per-symbol concentration**: TWO symbols above 30% cap (LINK 59.24%, BTC 35.80%). Both basin-inherited from /010, NOT /011-discovered.

### Mechanism Attribution Table

| Stratum | OOS Sharpe Δ attribution | Confidence | Durability |
|---|---|---|---|
| /010 basin substrate vs BASELINE | -0.03 (baseline OOS effect of /010 basin) | HIGH | NOT durable (single-seed-conditional) |
| /011 mechanical kill_low cleanup on /010 basin | ~+0.44 (from /010→/011 per-symbol Δ) | MED | DURABLE per-seed at any reasonable budget |
| **/011 vs BASELINE total** | **+0.41** | LOW directional | Basin-conditional; multi-seed dissolution likely → ~+0.05 mechanical layer only |

The entire OOS Δ +0.41 is attributable to the kill_low mechanical layer riding on the /010 basin substrate. NONE of it is attributable to kill_low DISCOVERING a new positive-OOS basin. If /015 multi-seed CONFIRMATION dissolves the LTC-dominated basin, the mechanical /010→/011 kill_low effect would still apply per-seed but the basin substrate itself would average to BASELINE's level — multi-seed OOS Sharpe would land closer to BASELINE +0.66 + (small mechanical cleanup ~+0.05) ≈ +0.70, NOT /011's +1.07.

## LM Master Pre-Design vs Post-Mortem Calibration Discrepancy

### Phase 4.5 prediction (`briefs-v1/iteration_v1-011/lgbm_advisor.md` §"Basin-Shift Probability Estimate")

> **For STATELESS entry-filter axes (R5-BINARY-KILL class), my prior is 20-30% basin-shift.** Three reasons it's lower than weight-touching:
> 1. **No multiplicative loss interaction**: the entry filter drops samples BEFORE the GBM loss sees them. The retained samples enter the loss with their ORIGINAL weight (no scale modification). The loss surface basin is unchanged within the retained sample space.
> 2. **Mechanical roster-preservation floor of 81-82%**: 18% of samples are deterministically dropped (NATR < 2.0% = data-deterministic). The remaining 82% have UNCHANGED features, labels, and weights vs baseline. Optuna's gradient signal on the 82% retained samples is qualitatively the same shape as baseline's gradient — only the per-cell sample count drops.
> 3. **Empirical /008 precedent**: methodology axes (PCA, walk-forward) produced byte-identical predictions when the mechanism didn't touch the loss directly. R5-BINARY-KILL is closer to /008 than to /010 in that taxonomy.
>
> **This raises my modal-outcome prediction**: PROMISING (OOS Δ ∈ [+0.05, +0.12]) at ~45% probability, PROMISING-INERT at ~30%, OVERSHOOT-FLAG at ~15%, NEGATIVE at ~10%.

### Phase 7.4 post-mortem (`briefs-v1/iteration_v1-011/lgbm_advisor.md` §"What This Iteration Confirms / Refutes")

> - **Basin-shift probability (20-30% for entry-filter axes)**: WRONG. /011 produced 93.3% LTC IS basin overlap with /010 — the basin shift is IDENTICAL across the two mechanism classes at single-seed=42. **NEW RULE for v1 single-seed=42 calibration: ANY non-trivial axis (entry filter OR weight-touching) re-discovers the same Optuna basin**. The mechanism distinction I made was structurally wrong; the basin is seed-property-driven, not axis-property-driven.
> - **OOS gainer prediction (ETH/DOT-led)**: WRONG. LINK + BTC led OOS.
> - **P50 OOS Δ +0.05 prediction**: actual +0.41 — 8× under-prediction.

### Discrepancy interpretation

LM Master Phase 4.5 anchored the 20-30% basin-shift prior on the structural distinction between entry-filter and weight-touching axes. The /011 empirical result REFUTES this distinction at v1 single-seed=42 — the LTC IS roster overlap of 93.3% across the two axis primitives shows the basin is seed-property-driven, not axis-property-driven. Three reasons the structural argument failed:

1. **Optuna at n_trials=35 is too budget-constrained to find a NEW basin from a marginally different training distribution.** The retained 82% of samples have the same gradient shape, but Optuna's basin-discovery process is itself stochastic; at low budget, it converges to whatever basin the seed initialization steers toward, NOT to a "best" basin orthogonal to the seed.

2. **The LTC OOS pattern from /010 transferred to /011 via the basin substrate's shared parent (seed=42)**, not via mechanism similarity. Both /010 and /011 inherit the LTC basin because (seed=42, 40-feature, n_trials=35) substrate locks the basin discovery; the axis intervention only modulates the substrate marginally.

3. **The /008 precedent LM Master cited as analogous is structurally DIFFERENT**: /008 was a methodology axis (PCA refactor) that produced byte-identical predictions because it didn't change the training distribution AT ALL — only the reporting layer. /011 changes the training distribution (different rows seen per cell) but not enough at this budget to escape the basin.

**LM Master track record after /011: 0/9 directional + 3 PARTIAL.** The PARTIAL credits remain meaningful (mechanism diagnosis at /002 LTC overfit; PROMISING-METHODOLOGY taxonomy at /008; modal-class taxonomy at /011). The directional Sharpe-Δ track is structurally unanswerable at the LM Master frame for single-seed EXPLORATION (LM Master cannot model Optuna's basin-lottery without running the actual Optuna). LM Master's value is in diagnostic-frame outputs (e.g., the 93.3% LTC overlap + 16.7% F6 baseline overlap measurements at /011 Phase 7.4 are load-bearing for Critic verdict), NOT in predictive Sharpe-Δ accuracy.

## Critic Path Forward (verbatim from Phase 7.5 §"Path Forward")

> LM Master Phase 7.4 establishes: at v1 single-seed=42 + n_trials=35 + V1_FEATURE_COLUMNS_PRUNED + ENSEMBLE_SIZE=3, the LTC-dominated Optuna basin re-discovered across axis primitives. Basin is SUBSTRATE-LOCKED, not axis-locked. /012 must probe basin dissolution at SUBSTRATE level.
>
> Prior 5 EXPLORATION families: universe (/006), feature-family (/007 + /009), methodology (/008), risk-primitive (/010); /011 = risk-primitive again. UNUSED families: labeling, model-arch (closed at /003), hyperparameter-region (closed at /005).
>
> 3 axes proposed:
>
> 1. **Labeling axis — triple-barrier σ_t source** (UNUSED family at v1; Critic /010 Path Forward Option 2 carried forward). Replace fixed-fraction ATR multipliers with past-only EWMA σ_t-scaled barriers. Changes IS label distribution per cell → different LightGBM loss surface → ~70% prior probability of basin escape. Strongest substrate-dissolution probe in UNUSED-family menu.
>
> 2. **Methodology axis — per-cell early-stop with inner hold-out** (UNUSED since /008; Critic /010 Path Forward Option 3 carried forward). Within-fold early stopping via 20% inner hold-out. Changes WHICH trees retained per cell → different ensemble composition → different basin. Substrate-dissolving via tree-selection diversity.
>
> 3. **Substrate-dissolution PROBE EXPLORATION at /012** (sister-iteration; NOT CONFIRMATION). Rerun /011's EXACT R5-BINARY-KILL config (threshold=2.0) at single-seed=43. Cost: one EXPLORATION cell ≤2h. Tests LM Master Phase 7.4 hypothesis "basin is seed-property-driven, not axis-property-driven" DIRECTLY. If /012 (seed=43) diverges from /011 by >0.30 Sharpe, basin IS seed-locked → /015 multi-seed CONFIRMATION on R5-BINARY-KILL becomes unambiguous next step. If /012 reproduces /011 patterns, the (n_trials=35, 40-feature, ENSEMBLE=3) substrate is binding and basin cannot be unstuck at EXPLORATION budget. Highest-information-density experiment available within EXPLORATION budget.
>
> Constraints: options 1 + 2 are UNUSED-family pure proposals; option 3 is sister-substrate probe (NOT same-axis-mechanism variation as /011).

## Next Iteration Ideas (Ranked)

**Ranking criteria**: substrate-dissolution discriminative power; UNUSED family per Axis Rotation Discipline (cycle-2 used so far: universe, feature-family ×2, methodology, risk-primitive ×2); EDA basis readiness; structural orthogonality to /010 + /011's risk-primitive substrate.

### Option A (PRIMARY): Substrate-dissolution PROBE EXPLORATION at single-seed=43

- **Axis**: rerun /011's EXACT R5-BINARY-KILL config (threshold=2.0) at single-seed=43. Same axis primitive, single-seed swap.
- **Family**: `risk-primitive` (binary-kill subtype) — sister substrate probe, NOT axis change. Rotation Discipline exempt (probe is methodologically distinct from new EXPLORATION).
- **Rationale**: highest-information-density experiment within ≤2h EXPLORATION budget. Tests LM Master's "basin is seed-property-driven not axis-property-driven" hypothesis DIRECTLY. Discriminates two scenarios:
  - If /012 (seed=43) Sharpe diverges >0.30 from /011: basin IS seed-locked → /015 multi-seed CONFIRMATION on R5-BINARY-KILL becomes unambiguous next step (mechanism could have edge if averaged across seeds).
  - If /012 (seed=43) reproduces /011's patterns (LTC IS dominance, similar OOS magnitude): substrate is binding → basin cannot be unstuck at EXPLORATION budget; pivot to UNUSED family is mandatory.
- **EDA readiness**: ZERO new EDA required. Re-use /011's brief Section 2 evidence.
- **Predicted outcome**: 50/50 on substrate-lock confirmation. The most LIKELY scenario is partial reproduction (LTC IS dominance preserved at maybe 80-90% overlap with /011; OOS magnitude varies ±0.20 Sharpe).
- **HIGH-RISK declaration**: NO (probe of existing axis; no new training-objective domain change).
- **Information value vs new EXPLORATION**: HIGH. A new axis at /012 would produce another single-seed Sharpe-Δ that cannot disambiguate basin-lottery from edge. The seed=43 probe is the one experiment that directly tests the substrate-lock structural claim.

### Option B: Labeling axis — triple-barrier σ_t source (UNUSED family at cycle-2)

- **Axis**: replace fixed-fraction ATR multipliers with past-only EWMA σ_t-scaled barriers (e.g., 24h vs 7d EWMA window for σ_t computation).
- **Family**: `labeling` (UNUSED in cycle-2; last used /004 in cycle-1).
- **Rationale**: highest-prior-probability of basin escape from UNUSED-family menu (~70% per Critic Phase 7.5 Path Forward #1). Changes IS label distribution per cell → different LightGBM loss surface → potentially different basin.
- **EDA readiness**: needs ~30min Phase 1 work to recompute NATR_14 with 24h + 14d windows and compute oracle SL-distance for σ_t-scaled barriers. Achievable in EXPLORATION 2h cap.
- **Risk**: 8th-consecutive HIGH-RISK declaration if label-mode change. Multi-seed pre-commit if PROMISING. SL-noise-floor red line from /004 closeout (1.5× NATR_p50) applies.
- **Predicted outcome**: 70% basin escape probability per Critic; ~30% basin stays substrate-locked.

### Option C: Methodology axis — per-cell early-stop with inner hold-out (UNUSED since /008)

- **Axis**: LightGBM per-cell early stopping with Purged-CV inner hold-out (20% within-fold).
- **Family**: `methodology` (UNUSED since /008 PCA closure).
- **Rationale**: structurally orthogonal; changes WHICH trees retained per cell → different ensemble composition → potentially different basin. Also closes /008-style debt by providing better diagnostic infrastructure for future EXPLORATIONs.
- **EDA readiness**: pure infrastructure work; no Phase 1 EDA needed.
- **Predicted outcome**: PROMISING-METHODOLOGY (non-compoundable per /001 + /008 precedent); byte-identical-ish on F1 if early-stop is methodology-only OR new basin if early-stop selects different trees.
- **Trade-off**: high-value structural improvement BUT non-compoundable. /012 spent here means /013+ benefits but cycle-2 cadence count still advances.

**QR Phase 8 recommendation**: PRIMARY = Option A (substrate-dissolution probe at seed=43). The probe is the highest-information-density experiment in cycle-2 because it directly tests the load-bearing structural claim from /010 + /011 closeout (basin is substrate-locked at v1 single-seed=42). All three options remain on the menu; Option B + Option C would naturally follow at /013 / /014 if Option A confirms substrate-lock, OR be deferred if Option A breaks the substrate-lock hypothesis.

Final selection of /012 axis defers to Phase 4.5 LM Master advisory + Phase 6.0 Critic pre-flight on the next iteration's brief.

## Cycle-2 Cadence Status

| Iteration | Family | Verdict |
|---|---|---|
| /006 | universe | EXPLORATION-NEGATIVE (DEGENERATE_PREDICTOR) |
| /007 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| /008 | methodology | EXPLORATION-PROMISING-METHODOLOGY |
| /009 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| /010 | risk-primitive | EXPLORATION-NEGATIVE (PROMISING-INERT-with-IS-basin-shift) |
| **/011** | **risk-primitive (binary-kill subtype)** | **EXPLORATION-NEGATIVE (catastrophic-basin-shift; LM Master proposed BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP)** |

**Cycle-2 EXPLORATION count after /011: 6 of 10.** CONFIRMATION-eligible at /015 (4 more EXPLORATIONs required before any CONFIRMATION can launch).

**Cycle-2 verdict distribution**: 0 pure PROMISING / 1 PROMISING-METHODOLOGY (non-compoundable) / 5 NEGATIVE. No edge ingredient bundled yet. The cycle continues consistent with v1 cycle-1's pattern of NEGATIVE-heavy distribution before the cycle's CONFIRMATION attempt.

**HIGH-RISK pre-commit tripwire — 8th-consecutive correct non-firing**: across /003-/011, all 7 HIGH-RISK iterations except /008 (methodology-only) declared HIGH-RISK and pre-committed to /012 CONFIRMATION if PROMISING; none fired. Cumulative compute saved ~48h. Discipline is battle-tested.

## LESSONS for v1 Cycle-2 Catalog

### LESSON #1: At v1 single-seed=42, ANY non-trivial axis re-discovers the same (LTC-dominated, 40-feature, n_trials=35) Optuna basin

The /010 + /011 pair is the load-bearing empirical evidence. Two mechanically distinct axes — /010 proportional weight scaling (multiplies into the loss directly) and /011 binary entry filter (drops samples pre-loss) — converged to 93.3% IS LTC roster overlap. LM Master Phase 4.5 had argued these axis classes should have different basin-shift probabilities (40-60% for weight-touching; 20-30% for entry-filter); the empirical result REFUTES the distinction at v1 single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3 + V1_FEATURE_COLUMNS_PRUNED.

The basin is a property of the (seed, search budget, feature set, ensemble size) tuple — call it the **SUBSTRATE**. The axis intervention only modulates the substrate marginally; the basin discovery itself is dominated by substrate properties. Three reasons:

1. **Optuna at n_trials=35 is too budget-constrained to escape substrate gravity.** With ~225 rows per (model, month) cell and 35 trials, Optuna's basin-discovery process is stochastic and converges to whatever basin the seed initialization steers toward. A marginally different training distribution (kill_low filters 18% of samples) is insufficient signal to redirect the basin.

2. **The 82% retained samples have the same gradient shape**, just less of them. Optuna's per-cell objective surface is qualitatively unchanged within the retained space; the basin discovery process sees a near-identical loss landscape.

3. **The seed-locked basin transfers across mechanism classes** because the substrate's "stickiness" dominates the axis's marginal perturbation. LTC IS roster /010 ↔ /011 = 93.3% even though /010 is a multiplicative weight modifier and /011 is a pre-loss row filter — structurally distinct mechanisms producing structurally identical basin draws.

**Generalization**: this LESSON is binding for ALL v1 cycle-2 EXPLORATIONs at the canonical budget (single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3). Any non-trivial axis is expected to produce IS Δ in the +0.30 to +0.50 OVERSHOOT band as a basin-rediscovery signature — NOT as evidence of mechanism edge.

### LESSON #2: Single-seed Sharpe-Δ cannot anchor an edge claim — only multi-seed dissolution test at /015 CONFIRMATION can disambiguate

Per LESSON #1, single-seed Sharpe-Δ at v1 EXPLORATION budget is dominated by substrate basin lottery, not by mechanism edge. The diagnostic test for whether ANY proposed mechanism has durable edge is multi-seed dissolution: run the SAME config across ≥10 outer seeds (with ENSEMBLE_SIZE=10 + n_trials=50 per `feedback_v1_seed_count_non_negotiable.md`); compute mean Sharpe + Pareto distribution. If the substrate basin lottery is dissolved by multi-seed averaging, the residual Sharpe-Δ vs BASELINE (multi-seed averaged) IS the mechanism's durable edge.

For /011: predicted multi-seed dissolution outcome is mean OOS Sharpe ≈ BASELINE +0.66 + mechanical kill_low layer ~+0.05 = ~+0.70 (vs single-seed +1.07). The ~0.40 single-seed magnitude excess is basin substrate; the ~+0.05 residual is mechanism edge.

**Generalization**: v1 cycle-2 EXPLORATION reports MUST NOT cite single-seed Sharpe-Δ as edge evidence. The diary + catalog ledger must record the basin-lottery substrate as the dominant explanation for single-seed Sharpe magnitudes. Edge claims are reserved for multi-seed CONFIRMATION outcomes.

### LESSON #3: Brief Section 8 verdict tables must pre-register the {F3 catastrophic, F1 PROMISING, F6 < 61%} dual-firing cell explicitly

/011 fell into a verdict cell that the brief Section 8 partially-pre-registered: F3 catastrophic-basin-shift class (IS Δ > +0.30 → axis CLOSED at single-seed) covered the IS dimension, but the F1 PROMISING + F6 < 61% combination was not explicitly classed. The deterministic resolution worked (F3 takes precedence over F1 by the "when in doubt, FAIL" rule + explicit "axis CLOSED" semantics), but the disposition of the OOS lift magnitude — real-but-non-durable — was not pre-registered.

LM Master Phase 7.4 proposed a NEW v1 verdict subtype `PROMISING-OVERSHOOT-BASIN-INHERITED`. Critic Phase 7.5 REJECTED retroactive re-classification on /011 (process integrity — pre-registered gates bind /011) BUT codified the future-looking rule: **future v1 brief Section 8 verdict tables MUST pre-register the dual-firing cell as `EXPLORATION-NEGATIVE` subtype `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP`** (Critic's terminology).

The three-cell classification scheme for future briefs:

| Cell | Class | Sub-class | Resolution |
|---|---|---|---|
| F3 > +0.30 AND F1 < +0.05 | EXPLORATION-NEGATIVE | catastrophic-basin-shift | axis CLOSED at single-seed |
| F3 > +0.30 AND F1 ≥ +0.05 AND F6 < 61% | EXPLORATION-NEGATIVE | BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP | axis CLOSED at single-seed; multi-seed dissolution at next CONFIRMATION may preserve mechanical layer only |
| F3 > +0.30 AND F1 ≥ +0.05 AND F6 ≥ 61% | EXPLORATION-PROMISING-VERIFIED | (mechanism-validated) | HIGH-RISK pre-commit fires; multi-seed CONFIRMATION mandated |

**Phase 5.5 gate enforces inclusion** in future /012+ briefs.

### LESSON #4: F6 roster-overlap diagnostic MUST be committed artifact (load-bearing falsifier requires deterministic verification)

F6 was the verdict-binding diagnostic at /011 — but LM Master Phase 7.4 computed it OFFLINE from the trade rosters; the committed reports do not contain a deterministic `f6_roster_overlap.csv` artifact. Critic Phase 7.5 §"Check 7" flagged this as a process-integrity defect: load-bearing falsifiers in brief Section 4 MUST be reproducible from committed artifacts, structurally equivalent to the comparison.csv + dsr.json contract.

**Codification (forward-looking)**: future briefs with F6-style falsifiers (or any roster-overlap falsifier) MUST require QE to emit a committed artifact at `reports-v1/iteration_v1-NNN/f6_roster_overlap.csv` containing per-symbol-per-half (IS/OOS) overlap counts and percentages. The Phase 5.5 gate verifies the brief requirement; Phase 6 QE delivers; Phase 7.5 Critic verifies presence.

For /011 specifically: the LM Master offline computation (16.7% F6 baseline-overlap) is accepted as the reference even though the artifact-level reproduction is not committed (it is reproducible from `reports-v1/iteration_v1-011/out_of_sample/trades.csv` joined to BASELINE OOS trades by `(symbol, open_time)`).

### LESSON #5: Engineering report mandatory at every Phase 7.5 dispatch (process integrity)

Critic Phase 7.5 §"Check 7" flagged: "Neither `briefs-v1/iteration_v1-011/engineering_report.md` nor `reports-v1/iteration_v1-011/engineering_report.md` exists. /010 had one — /011 does not. Process integrity violation."

The /010 closeout had emitted an engineering report from the QE; /011 did not — the QE's `OVERALL=READY-FOR-CRITIC` deliverable per Phase 7.5 boot sequence Step 2 was missing. /011's Phase 7+8 closeout REMEDIATES the gap by creating the engineering report (`reports-v1/iteration_v1-011/engineering_report.md`) as part of the closeout commit chain, but the lesson is: this should not have been a closeout fix — it should have been a Phase 6/7 deliverable from the QE.

**Codification (forward-looking)**: future /012+ closeouts MUST include `reports-v1/iteration_v1-NNN/engineering_report.md` as a Phase 6/7 QE deliverable, not a Phase 8 closeout fix. The orchestrator should hard-reject any Phase 7.5 dispatch without QE engineering report. Critic Recommendation #3 to /011 closeout is codified.

## Permanent Catalog Additions (from /011 closeout)

1. **v1 substrate-basin-lock structural finding**: at v1 single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3 + V1_FEATURE_COLUMNS_PRUNED, the Optuna basin is substrate-locked across axis primitives. /010 (proportional R5) and /011 (binary-kill R5) both produced ~+0.48 IS Δ via 93.3% identical LTC IS roster. New memory entry: `feedback_v1_substrate_basin_lock.md`. Future v1 cycle-2 EXPLORATIONs should anchor on (a) basin-substrate dissolution probes OR (b) UNUSED-family axes (labeling, methodology) that change the optimization target rather than the position-sizing mechanism.

2. **NEW v1 verdict subtype `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP`** (Critic Phase 7.5 codification): future briefs Section 8 MUST pre-register the dual-firing cell {F3 catastrophic, F1 PROMISING, F6 < 61%} as EXPLORATION-NEGATIVE subtype BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP. Three-cell classification scheme (Lesson #3) is the codified template. Phase 5.5 gate enforces.

3. **F6 roster-overlap diagnostic as committed artifact** (Critic Rec #2): future briefs with F6-style falsifiers MUST require QE to emit `f6_roster_overlap.csv` per-symbol-per-half. Phase 5.5 verifies brief requirement; Phase 6 QE delivers; Phase 7.5 Critic verifies presence.

4. **Engineering report mandatory at every Phase 7.5 dispatch** (Critic Rec #3): not a Phase 8 closeout fix but a Phase 6/7 QE deliverable. Orchestrator hard-rejects Phase 7.5 dispatch without QE engineering report.

5. **LM Master diagnostic-frame contributions weighted above point Sharpe-Δ predictions**: track record 0/9 directional + 3 PARTIAL across /003-/011 shows that LM Master cannot anchor single-seed Sharpe-Δ predictions (the basin-lottery substrate is not modeled by LM Master without running Optuna). LM Master's value is in mechanism diagnosis (e.g., the 93.3% LTC overlap + 16.7% F6 baseline overlap measurements at /011 Phase 7.4 are load-bearing for Critic verdict). Future Phase 4.5 advisories should emphasize diagnostic-frame outputs and discount point Sharpe-Δ predictions.

## HIGH-RISK Pre-Commit Tripwire — Saved Compute

Per /011 brief Section 2.5 HIGH-RISK declaration, the multi-seed pre-commit was OPT-IN: pre-commit to /012 multi-seed CONFIRMATION-spec IF /011 verdict = PROMISING. Verdict = EXPLORATION-NEGATIVE catastrophic-basin-shift → tripwire correctly does NOT fire. This is the **8th-consecutive correct non-firing** of the HIGH-RISK pre-commit (across /003 + /004 + /005 + /006 + /007 + /009 + /010 + /011 — all 7 HIGH-RISK iterations on /003-/011 except /008 which was methodology-only).

**Cumulative compute saved**: ~48h across 8 iterations (6h per averted multi-seed CONFIRMATION at 10-seed × ENSEMBLE=10 × n_trials=50). Discipline is battle-tested over 8 independent HIGH-RISK iterations without producing a false-positive CONFIRMATION dispatch.

## Files & Commits on Branch

- Branch: `iteration-v1/011` from `iter-v1/010` closeout commit `33601b6`
- HEAD before Phase 7+8: `b48c035` (Critic Phase 7.5 review)

Commits in this iteration (pre-closeout):
- `5d7a1e1` — EDA analysis scripts + oracle simulation
- `9227d92` — QR Phases 1-5 + R5 binary kill EDA-calibrated threshold + brief
- `f6e0515` — LM Master Phase 4.5 pre-design advisory
- `9c843e6` — brief Section 3.6 — LM Master Phase 4.5 recs response
- `57587ef` — phase 5.5 gate PASS
- `b788d4f` — R5-BINARY-KILL-LOW wiring (pre-R2 entry filter, configurable threshold)
- `ff3b686` — Critic Phase 6.0 pre-flight PASS
- `048bbd4` — LM Master Phase 7.4 post-mortem
- `b48c035` — Phase 7.5 Critic review — EXPLORATION-NEGATIVE
- `36f9769` — QR Phase 7 evaluation memo + engineering report

Trunk merge: **NONE**. EXPLORATION-NEGATIVE never merges to main.

Tag: `v0.v1-011` (applied after this Phase 8 commit).
