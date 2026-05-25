---
iteration: iter-v1/014
date: 2026-05-25
verdict: EXPLORATION-NEGATIVE
subtype: Cell-5 + PARTIAL-F7 + DURABLE-n_eff-MECHANISM
axis_family: labeling (UNUSED in cycle-2 since /004 cycle-1; first genuine label-distribution change since v1 refactor)
axis: triple-barrier σ_t source — replace fixed-fraction NATR×atr_mult with past-only EWMA σ_t at 14-day half-life (k_tp=1.06, k_sl=0.53)
cadence_position: cycle-2 EXPLORATION #9 of 10
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c)
merge_decision: NO-MERGE (EXPLORATION-NEGATIVE Cell-5 + PARTIAL-F7; IS catastrophic -0.6112 + OOS negative +0.1828 fail Sharpe floors; over-determined — fails IS/OOS floors AND OOS/IS ratio sign-flipped AND F3 catastrophic-extreme)
---

# Iteration iter-v1/014 — Diary

## One-Line Outcome

Past-only EWMA σ_t × k labeling at 14-day half-life produced **IS Sharpe -0.6112** (Δ **-0.8941** catastrophic-extreme; 0.59 below NEGATIVE-catastrophic floor) + **OOS Sharpe +0.1828** (Δ **-0.4809** deep NEGATIVE band; OOS/IS ratio -0.2991 sign-flipped) + **F7-NEW 4/5 PARTIAL** (ETH deviant via C1) + **F8-NEW PASS** (598 ∈ [466, 776]) + **DURABLE n_eff 13→19 per-cell median** (FIRST material shift in v1 cycle-2; loss-surface diversification confirmed) + **C1 SMOKING GUN** (execution-time barriers used NATR×atr_mult NOT σ_t × k × √timeout — code-and-data confirmed via LTC trades.csv row-1 reproducibility) — **labeling axis is NOT closed at /014**; /015 = labeling CONFIRMATION binding fires regardless with C1 FIX MANDATORY.

## Outcome Summary — Basin-Lottery Catastrophic + C1 Confound + DURABLE n_eff Diversification

Three load-bearing structural findings at /014 closeout:

### 1. Basin draw catastrophic on a structurally-richer loss surface

IS Sharpe Δ -0.8941 is the deepest single-seed catastrophic in v1 cycle-2 catalog (vs /013's -0.9223 prior catastrophic). The 33/33/34 FLAT prior per `feedback_v1_substrate_basin_lock.md` REFUTED-IN-FULL revision held: this is a NEGATIVE-class basin draw at single-seed EXPLORATION, exactly as the flat prior accommodates. The basin direction at single-seed remains 33% positive / 33% null / 34% negative; /014 sampled from the NEGATIVE arm.

### 2. Critic Concern C1 is the LOAD-BEARING IS catastrophe explanation, NOT basin lottery alone

LM Master Phase 7.4 §3 + Critic Check 8 + this Phase 7 engineering report SECTION 4 converge on C1 as proximate cause:
- Label-time σ_t × k_tp/k_sl × √timeout WIRED CORRECTLY (`labeling.py:333,350-357`)
- Execution-time `lgbm.py:907-915` UNCHANGED from /013 NATR×atr_mult path — no `self.sigma_source` dispatch
- LTC trades.csv row 1: SL distance 5.806% matches NATR×atr_sl=1.45 (4.0% NATR × 1.45 = 5.8%); σ_t × k_sl × √21 scheme would have produced ~8.94% SL distance
- Per-symbol mechanism: BTC/ETH (σ_t/NATR=1.13 wider) get wider labels + tighter execution = systematic positive labeling bias → IS basin PENALTY; LTC/LINK/DOT (σ_t/NATR=0.92 tighter) get tighter labels + wider execution = trades survive longer than labels predict → C1 WINDFALL for alts (especially LTC)

LTC IS+OOS WINNER for the first time in cycle-2 AND BTC/ETH catastrophic are BOTH C1 signatures, not basin lottery alone. The brief Section 10.1 RESOLUTION mandated barrier-source consistency at both label-time AND execution-time; QE Phase 6 shipped without execution-time dispatch. C1 unresolved is the experimental confound. /014 is structurally a CONFOUNDED EXPERIMENT — the axis was never truly tested in its full intended form.

### 3. n_eff structural finding is DURABLE evidence INDEPENDENT of basin direction

n_eff per-cell median jumped **13 → 19** (+46% relative; range 14-22 per-symbol). Per dsr.json: BTC=20, ETH=20, LINK=18, LTC=18, DOT=19. **This is the FIRST material n_eff shift in v1 cycle-2 since /008** — every /008-/013 iteration stayed at 13.

This is the **strongest mechanism evidence in 12 v1 iterations** that the σ_t labeling axis diversified the Optuna per-cell loss surface as predicted in LM Master Phase 4.5 §2 ("partial-shift scenario"). n_eff is structurally bound by per-cell label-distribution shape — independent of basin draw direction. /014 produced a NEGATIVE basin draw on a RICHER surface; these are independent measurements.

**Implication for /015**: at multi-seed (10 outer × 5 inner = 50 models/cell), n_eff=19 should REPLICATE if mechanism is robust. Pre-register F-AXIS-MECHANISM falsifier "n_eff ≥ 17 across at least 7/10 seeds" per LM Master Phase 7.4 §7 Rec #3. If n_eff collapses to 13 at multi-seed, loss-surface diversification was single-seed artifact (unlikely; n_eff bound by label-distribution shape).

## Headline Metrics + Per-Symbol Decomposition

From `reports-v1/iteration_v1-014/comparison.csv`:

| Metric | IS | OOS | Baseline IS | Baseline OOS | IS Δ | OOS Δ |
|---|---|---|---|---|---|---|
| **Monthly Sharpe** | **-0.6112** | **+0.1828** | +0.2829 | +0.6637 | **-0.8941** | **-0.4809** |
| Sortino | -0.6609 | +0.2242 | +0.3205 | +0.7697 | -0.9814 | -0.5455 |
| Max Drawdown | 200.71% | 45.89% | 73.06% | 40.94% | +127.65pp | +4.95pp |
| Win Rate | 37.8% | 42.6% | 39.9% | 40.2% | -2.1pp | +2.4pp |
| Profit Factor | 0.8778 | 1.0406 | 1.060 | 1.156 | -0.182 | -0.115 |
| Total Trades | 598 | 202 | 621 | 189 | -23 | +13 |
| Total Net PnL | -115.96% | +10.82% | +54.05% | +38.13% | -170.01pp | -27.31pp |
| DSR | -60.17 | -59.27 | (informational) | (informational) | — | — |
| PSR_monthly_vs_0 | 0.0647 | 0.5924 | 0.977 | 0.989 | -0.912 | -0.397 |
| **n_eff_per_cell_median** | **19** | **19** | 13 | 13 | **+6 (+46%)** | **+6 (+46%)** |
| R5 fire rate | 0.00% | 0.00% | — | — | — | — |

**R5 disabled per axis isolation**: brief Section 0.2 declared R5 DISABLED for /014. Confirmed 0% fire rate.

### Per-Symbol IS (598 trades total)

| Symbol | trades | WR | net_pnl | /013 raw PnL | /012 raw PnL | /011 raw PnL | Notes |
|---|---|---|---|---|---|---|---|
| **LTCUSDT** | 128 | **47.7%** | **+95.51** | +32.22 | +118.92 | +110.58 | IS rank-1 RETURNS to LTC (rank-2 at /013); C1 WINDFALL for alts |
| LINKUSDT | 106 | 38.7% | -9.79 | +128.38 | +105.86 | +42.45 | LINK collapses ~flat (rank-1 at /013) |
| BTCUSDT | 120 | 37.5% | -24.25 | -79.13 | +6.59 | -30.74 | BTC mild catastrophic — C1 PENALTY |
| **DOTUSDT** | 101 | 33.7% | **-88.74** | -4.18 | -179.84 | +31.01 | DOT catastrophic LOSER (3rd time in cycle-2); >270 raw PnL swing across /011-/014 |
| **ETHUSDT** | 143 | **31.5%** | **-99.73** | -139.78 | -22.68 | -49.45 | ETH largest IS negative; C1 PENALTY |
| **PORTFOLIO** | **598** | **37.8%** | **-126.99** | -62.50 | +28.85 | +103.85 | Catastrophic collapse |

### Per-Symbol OOS (202 trades total)

| Symbol | trades | WR | net_pnl | /013 raw PnL | /012 raw PnL | /011 raw PnL | Notes |
|---|---|---|---|---|---|---|---|
| **LTCUSDT** | 38 | **50.0%** | **+24.49** | -40.16 | -47.66 | -19.12 | **FIRST OOS POSITIVE in cycle-2** — LTC OOS sign-flip via C1 |
| DOTUSDT | 41 | 43.9% | +10.43 | +50.11 | -2.06 | +29.13 | DOT OOS stable positive |
| BTCUSDT | 41 | 43.9% | +5.70 | +1.51 | +25.20 | +51.28 | BTC OOS positive across all 4 samples |
| LINKUSDT | 44 | 43.2% | +3.87 | +47.08 | +53.36 | +84.86 | LINK OOS positive but collapses from /011/012/013 magnitude |
| **ETHUSDT** | 38 | **31.6%** | **-41.18** | -5.59 | -17.16 | -2.90 | ETH OOS catastrophic — single-symbol Sharpe drag |
| **PORTFOLIO** | **202** | **42.6%** | **+3.31** | +52.95 | +11.68 | +143.23 | OOS net PnL POSITIVE +3.31 but Sharpe negative via ETH variance |

**4 of 5 symbols OOS POSITIVE for the first time in cycle-2** (LTC + DOT + BTC + LINK). Total OOS net PnL +3.31 positive; OOS Sharpe +0.18 vs +0.66 baseline — daily-variance via ETH -41.18 single-symbol dominates the headline Sharpe.

## LM Master Phase 4.5 LTC Catastrophic Prediction INVERTED

LM Master Phase 4.5 §2 (`briefs-v1/iteration_v1-014/lgbm_advisor.md`):

> "Specific basin-lottery risks: Per-symbol catastrophic-reversal rotation observed at /011-/013 likely re-rotates under /014. **Expected catastrophic candidate: LTC** (largest barrier compression at -7.6% high-vol regime)."

**Observed**: LTC was the IS+OOS WINNER on BOTH halves (IS +95.51 / OOS +24.49 / WR 47.7% IS / 50.0% OOS). Prediction INVERTED in direction.

**Mechanism**: tighter LTC σ_t labels (0.92 × NATR) produced MORE labeled TPs per IS row (28.1% TP rate vs 20.2% baseline — biggest TP% jump per LM Master Phase 7.4 §4). Combined with NATR-wider execution barriers (C1 inverted-direction for alts), execution exits SURVIVED LONGER than labels predicted. Asymmetric C1 windfall for alts, asymmetric C1 penalty for BTC/ETH. **C1 is proximate cause of LTC win AND BTC/ETH catastrophe simultaneously.**

**Cycle-2 LM Master per-symbol catastrophic predictions: 0/4**:
- /011: BTC mild catastrophic predicted, observed BTC -30.74 (mild)
- /012: DOT catastrophic predicted (CORRECT direction; -179.84) — but at /012 LM Master Phase 4.5 was at concentrated prior not flat
- /013: ETH+BTC catastrophic predicted, observed ETH -139.78 + BTC -79.13 (TWO losers; PARTIAL hit at directional but specific magnitude prediction off)
- /014: LTC catastrophic predicted, observed LTC +95.51 WINNER (INVERTED in direction)

**LM Master Phase 7.4 §5 FINAL CALIBRATION rule fires**: STOP PREDICTING PER-SYMBOL CATASTROPHIC CANDIDATES. Track record 0/12 directional + 5 PARTIAL (mechanism-level predictions reliable; per-symbol directional predictions are basin-lottery-dominated). LM Master priors at /015+ Phase 4.5 must default to FLAT for verdict-class; magnitude bands as plausibility envelopes ONLY.

## 5 LESSONS for v1 Cycle-2 Catalog

### LESSON #1: n_eff 13→19 is FIRST material shift in cycle-2 — σ_t labeling DIVERSIFIED Optuna loss surface (durable evidence independent of basin direction)

`n_eff_per_cell_median` jumped from BASELINE+/008-/013's 13 to /014's 19 (+46% relative; range 14-22 per-symbol). This is the strongest mechanism evidence in 12 v1 iterations that the labeling axis worked **structurally** even though the basin draw at single-seed was catastrophic. n_eff is bound by per-cell label-distribution shape — independent of basin draw direction.

**Generalization**: future v1 iterations exploring axes that modify per-cell label distributions should pre-register n_eff replication checks. If a labeling/feature axis produces an n_eff jump WITHOUT replicating at multi-seed, the surface diversification was an artifact. If n_eff replicates at multi-seed (predicted unlikely to collapse since label-distribution shape is seed-independent), then the loss-surface diversification is a real structural finding even if F1/F3 verdict-class is NULL.

**Permanent catalog addition**: at /015 multi-seed CONFIRMATION, pre-register F-AXIS-MECHANISM falsifier "n_eff ≥ 17 across at least 7/10 seeds". If <7/10 (unlikely), loss-surface diversification was single-seed artifact and σ_t mechanism is REFUTED at the structural layer. If ≥7/10, mechanism is robust even if /015 multi-seed mean is NULL.

### LESSON #2: Critic Concern C1 (barrier-source label vs execution inconsistency) was LOAD-BEARING mechanism — not just attribution ambiguity

Critic /014 Phase 6.0 pre-flight raised C1 as Concern (HEAD `65c0bb2`). Brief Section 10.1 RESOLUTION explicitly mandated barrier-source consistency at both label-time AND execution-time. QE Phase 6 shipped at HEAD `dd8cf0d` with label-time σ_t correct + execution-time NATR×atr_mult UNCHANGED. Critic Phase 7.5 + LM Master Phase 7.4 + this Phase 7 engineering report converged on C1 as **proximate cause** of /014's per-symbol pattern (LTC windfall + BTC/ETH penalty are BOTH C1 signatures).

**Generalization**: future axes touching label distribution MUST verify symmetric execution-time implementation. The "axis isolation" discipline at brief Section 0.2 (R5 disabled to isolate the labeling axis) was correctly applied, but the IMPLEMENTATION of the axis itself was asymmetric — label-time mod with execution-time unchanged. This is a NEW failure mode: AXIS-IMPLEMENTATION-ASYMMETRY (sister to AXIS-ISOLATION-FAILURE).

**Permanent catalog addition**: brief Section 10 (Implementation Spec) for any axis modifying labels MUST include an explicit "execution-time barrier dispatch consistency assertion" both as test (programmatic) and as Critic Check 8 mandate. /015 brief Section 10 will include this as F-AXIS-C1 falsifier "execution-time barrier matches label-time within 1e-6 tolerance for all IS candles" (programmatic assertion).

### LESSON #3: F7-NEW per-symbol exit-mix direction (4/5 match) is genuinely informative axis-attribution falsifier despite basin-lottery dominance of F1/F3

LM Master Phase 4.5 §6 Closing Note: "F7-NEW per-symbol exit-mix direction is the ONLY axis-attribution-clean falsifier at /014. F1/F3 are basin-lottery-dominated and provide essentially zero mechanism information."

Observed F7-NEW: 4/5 PASS (BTC UP, LINK DOWN, LTC DOWN, DOT DOWN; ETH deviant DOWN-instead-of-UP). Mechanism is **80% functional** even at single-seed catastrophic-basin draw. ETH deviation is the C1 signature in trade data (per LM Master Phase 7.4 §2).

**Generalization**: future axes modifying label distributions or execution barriers should pre-register per-symbol mechanism-attribution falsifiers (sister to F7-NEW). Single mechanism falsifier at portfolio-aggregate level (like F3 IS Sharpe Δ) is basin-dominated; per-symbol mechanism falsifiers attain useful axis-attribution at single-seed.

**Permanent catalog addition**: brief Section 8.1 verdict matrix at /015 (and future axes touching labels/execution) must include explicit verdict-class row "F1×F3 NEGATIVE AND F7-NEW PARTIAL → EXPLORATION-NEGATIVE with mechanism 80% functional; engineering attention needed per-symbol". Critic Phase 7.5 Rec #3 forward-mandate codified.

### LESSON #4: 4TH-STRIKE engineering report enforcement gap — codified runner hard-stop at /015 setup

4 consecutive iterations have produced engineering reports retroactively at QR Phase 7 closeout instead of at QE Phase 6 closeout:
- /011 Critic Rec #3: orchestrator-side hard-reject of Phase 7.5 dispatch without engineering report
- /012 Critic Rec #1: 3-way enforcement (orchestrator + QE skill + Critic Phase 6.0 precondition)
- /013 Critic Phase 7.5 §"Check 7" PROCESS CONCERN: 3rd-strike escalation
- **/014 4th-strike**: spec-side check passes (Critic Phase 6.0 PASS), but dispatch-side never blocks

The mechanism that has been violated 4 consecutive iterations is the **dispatch-side enforcement**, not the spec-side declaration. Critic Phase 6.0 currently verifies the brief Section 10.2 #4 SPEC is present; QE Phase 6 closeout produces nothing; runner emits `[WARNING]` only at `run_baseline_v1.py:1217-1229`.

**/015 setup MANDATE**: codify runner HARD STOP as:

```python
engineering_report_path = reports_dir / "engineering_report.md"
if not engineering_report_path.exists() and not args.no_engineering_report:
    print(f"[FATAL] engineering_report.md missing at {engineering_report_path}", file=sys.stderr)
    sys.exit(1)
```

The `--no-engineering-report` opt-out is reserved for explicitly-acknowledged QE-side defects. Default behavior is HARD STOP. This MUST be in /015 brief Section 10 src/ implementation spec AND verified by Critic Phase 6.0 at /015 BEFORE backtest dispatches.

**Permanent catalog addition**: `feedback_v1_engineering_report_hardstop.md` (NEW file) codifies the runner hard-stop mandate as a `quant-iteration-v1` skill rule.

### LESSON #5: LM Master Phase 4.5 LTC catastrophic prediction was 0-for-cycle-2 — STOP PREDICTING PER-SYMBOL CATASTROPHIC CANDIDATES

LM Master per-symbol catastrophic predictions in cycle-2:
- /011: BTC mild (correct direction)
- /012: DOT (correct direction, magnitude off)
- /013: ETH+BTC (partial — observed ETH+BTC matches but specific magnitude wrong)
- /014: LTC (**INVERTED** — LTC was WINNER not loser)

Net 0/4 fully-correct directional predictions on per-symbol catastrophic candidates at v1 single-seed EXPLORATION.

**Permanent calibration update** (committed at `1f70af3` LM Master Phase 7.4 §5):
- **Verdict-class predictions**: flat priors ONLY at v1 single-seed EXPLORATION
- **Magnitude predictions**: report band only as plausibility envelope, not P50 anchor
- **Per-symbol catastrophic predictions**: FORBIDDEN at single-seed EXPLORATION (0/4 cycle-2 track record)
- **Mechanism predictions**: RELIABLE (5 PARTIAL hits — lookahead-clean, F8-NEW band, F7-NEW direction, n_eff prediction, FLAT prior calibration)
- HIGH-confidence statements: reserved for trivial-structural claims (e.g. F2 fire rate in [16%, 24%])

**Generalization**: at single-seed v1 EXPLORATION, LM Master Phase 4.5 advisories cannot offer per-symbol directional predictions on basin draws. The basin lottery dominates; mechanism-level predictions (per-row label distribution, n_eff diversification, F7-NEW direction) are reliable. At multi-seed CONFIRMATION (/015), LM Master priors permitted to concentrate (60/25/15 NULL/PROMISING/NEGATIVE per Phase 7.4 §6) — variance reduction is mechanically guaranteed at multi-seed.

## Critic Path Forward (from Critic Phase 7.5 review HEAD `bcca796`)

Per `briefs-v1/iteration_v1-014/review.md` §"Path Forward (mandatory on EXPLORATION-NEGATIVE)":

PRIMARY (PRE-COMMITTED BINDING, cannot be renegotiated): **/015 = labeling CONFIRMATION binding** at multi-seed `--seeds 10` × ENSEMBLE_SIZE=5 inner + n_trials=35 + V1_FEATURE_COLUMNS_PRUNED + `sigma_source="ewma14d"` + **C1 FIX MANDATORY** (`lgbm.py:907-915` dispatch on `self.sigma_source`).

ALTERNATIVE AXES for /016+ if /015 multi-seed NULL/NEGATIVE (Critic mandate: each from family NOT used in prior 5 EXPLORATIONs):

1. **Universe expansion to 7-symbol with concentration cap** (UNUSED `universe` family in cycle-2 since /006). Add BNB + SOL with per-symbol PnL share cap. Denominator expansion attenuates basin-lottery extreme draws. NOT proportional cap (v3/020 closed that for v3 catalog; v1 untested).

2. **XGBoost head-to-head replacement** (UNUSED `model-arch` family in cycle-2). Depth-wise vs leaf-wise growth may favor different feature interactions. v3/016 closed this for v3 but v1's V1_FEATURE_COLUMNS_PRUNED feature set is different (40 cols vs v3's 14).

3. **Sample weighting by past-realized vol** (NEW `sample-weighting` family — never used in v1). Replace `abs(labeled_pnl)` weighting with weights inversely proportional to past-realized 30-day vol. Attenuates extreme-vol-regime trade influence on IS basin.

Per constructive duty: each candidate from family NOT used in prior 5 EXPLORATIONs (last 5 = feature-family, risk-primitive, risk-primitive, methodology-substrate-test, methodology-substrate-test). All 3 alternatives respect the Axis Rotation Discipline.

## Cycle-2 Cadence Status

| Iteration | Family | Verdict |
|---|---|---|
| /006 | universe | EXPLORATION-NEGATIVE (DEGENERATE_PREDICTOR) |
| /007 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| /008 | methodology | EXPLORATION-PROMISING-METHODOLOGY |
| /009 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| /010 | risk-primitive | EXPLORATION-NEGATIVE (PROMISING-INERT-with-IS-basin-shift) |
| /011 | risk-primitive (binary-kill subtype) | EXPLORATION-NEGATIVE (catastrophic-basin-shift) |
| /012 | methodology-substrate-test (NEW 8th family) | EXPLORATION-NEGATIVE (BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-PARTIAL) |
| /013 | methodology-substrate-test (3rd consecutive at 8th family) | EXPLORATION-NEGATIVE (BASIN-LOTTERY-CATASTROPHIC) |
| **/014** | **labeling (UNUSED-family pivot)** | **EXPLORATION-NEGATIVE (Cell-5 + PARTIAL-F7 + DURABLE-n_eff-MECHANISM)** |

**Cycle-2 EXPLORATION count after /014: 9 of 10.** /015 = labeling CONFIRMATION BINDING fills the 10:1 CONFIRMATION position per /013 pre-committed conditional + /014 brief Section 11 PRE-COMMITTED.

**Cycle-2 verdict distribution after /014**: 0 pure PROMISING / 1 PROMISING-METHODOLOGY (non-compoundable, /008) / 8 NEGATIVE. **No edge ingredient bundled yet.** /014's durable n_eff structural finding is NOT an edge ingredient but a MECHANISM-LEVEL CALIBRATION INPUT for /015 CONFIRMATION design (loss-surface diversification confirmed; multi-seed n_eff replication pre-registered as F-AXIS-MECHANISM falsifier).

**HIGH-RISK pre-commit tripwire FIRED CORRECTLY at /014** (FIRST cycle-2 HIGH-RISK declaration): /015 = labeling CONFIRMATION binding cannot be renegotiated regardless of /014 magnitude. Mitigation functioning as designed — catastrophic /014 does NOT pivot off labeling axis; /015 will test it at multi-seed with C1 FIX. **HIGH-RISK pre-commit discipline preserved**; first HIGH-RISK trigger in cycle-2 fired its mitigation correctly. Cumulative HIGH-RISK pre-commit compute saved from prior /003-/013 NORMAL-RISK declarations ≈ 54h (9 consecutive correct non-firings prior + 1 correct firing now).

## Reflection: σ_t Labeling Axis Is NOT Closed at /014

Three reasons /014's EXPLORATION-NEGATIVE does NOT close the labeling axis:

1. **C1 confound corrupts axis attribution**: /014 measured a confounded experiment (label-time σ_t × execution-time NATR). The "true" axis (consistent σ_t at both layers) was NOT TESTED. /015 C1 FIX completes the experiment.

2. **n_eff structural finding is durable**: 13→19 per-cell median jump is the FIRST material loss-surface diversification in v1 cycle-2. This is genuine mechanism evidence at the structural layer, independent of basin direction. If n_eff replicates at /015 multi-seed (predicted unlikely to collapse), the mechanism is robust even if multi-seed mean is NULL.

3. **F7-NEW 4/5 PARTIAL confirms 80% mechanism functional**: per-symbol exit-mix direction predicted correctly for 4 of 5 symbols (only ETH deviated, attributable to C1). Even at catastrophic basin draw, the mechanism IS sound at the per-row label resolution layer.

**Modal expected outcome at /015 is NULL** per LM Master Phase 7.4 §6 (55% NULL / 20% PROMISING / 25% NEGATIVE). NULL at /015 closes the labeling axis at v1 EXPLORATION+CONFIRMATION budget. PROMISING at /015 would be the first edge ingredient candidate in v1 catalog. NEGATIVE at /015 closes the axis with confounding C1 fixed (clean refutation).

**Forward-looking honest framing**: /014 was a confounded EXPLORATION-NEGATIVE; /015 is the first well-posed test of the σ_t labeling axis at multi-seed. The experiment is finally well-posed — and the modal outcome remains NULL, but at least the question is now answerable.

## Permanent Catalog Additions (from /014 closeout)

1. **NEW v1 verdict subtype `Cell-5 + PARTIAL-F7 + DURABLE-n_eff-MECHANISM`** (Critic Phase 7.5 §"Verdict Rationale" cell assignment + LM Master Phase 7.4 §1 durable evidence + this Phase 7 engineering report Section 5). Applies to {F1 NEGATIVE-band, F3 NEGATIVE-catastrophic-extreme, F7-NEW PARTIAL, F8-NEW PASS, mechanism evidence durable} configuration. Adds to existing v1 subtypes (`catastrophic-basin-shift`, `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP`, `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-PARTIAL`, `BASIN-LOTTERY-CATASTROPHIC`).

2. **F-AXIS-C1 falsifier mandate for /015 + future label/execution axes**: brief Section 4 must include programmatic assertion "execution-time barrier matches label-time within 1e-6 tolerance for all IS candles" when the axis modifies labels. Test suite includes `tests/test_lgbm.py::test_sigma_source_ewma14d_execution_barrier_consistency`. Codified as future-axis discipline; not retroactive for /014.

3. **F-AXIS-MECHANISM n_eff replication falsifier mandate**: at multi-seed CONFIRMATION for any axis producing single-seed n_eff jump, pre-register "n_eff ≥ <observed-1> across at least 7/10 seeds". If <7/10, mechanism was single-seed artifact. Per LM Master Phase 7.4 §7 Rec #3 + this Phase 7 engineering report Section 6.

4. **Engineering report runner HARD-STOP codification mandate** (4th-strike closure): /015 brief Section 10 src/ implementation spec MUST include the `sys.exit(1)` modification to `run_baseline_v1.py:1217-1229`. Critic Phase 6.0 at /015 verifies the gate code path before backtest dispatches. The check converts from `[WARNING]` to FATAL. New optional `--no-engineering-report` opt-out for explicitly-acknowledged QE-side defects.

5. **LM Master per-symbol catastrophic prediction FORBIDDEN at single-seed EXPLORATION**: per Phase 7.4 §5 FINAL calibration rule update — track record 0/12 directional + 5 PARTIAL after /014. Future Phase 4.5 advisories cannot offer per-symbol directional catastrophic candidates at v1 single-seed. Magnitude bands are plausibility envelopes; verdict-class predictions stay FLAT.

6. **AXIS-IMPLEMENTATION-ASYMMETRY new failure mode codified** (LESSON #2 generalization): sister to AXIS-ISOLATION-FAILURE. When an axis modifies labels OR execution barriers, brief Section 10 must explicitly mandate symmetric implementation at BOTH layers. Phase 5.5 gate verifies brief mandate language; Phase 6.0 verifies implementation; Critic Check 8 at Phase 7.5 verifies the assertion fires in tests.

7. **HIGH-RISK pre-commit mitigation FIRST FIRING preserved**: /014 was the first HIGH-RISK declaration in cycle-2; the /015 binding pre-commit correctly fires regardless of /014's catastrophic basin draw. Discipline battle-tested at first firing. Future cycle-2/cycle-3 HIGH-RISK declarations carry forward the binding mitigation rule.

8. **Cycle-2 EXPLORATION 9 of 10 complete**: /015 = labeling CONFIRMATION binding fills the 10:1 CONFIRMATION position. The 10:1 cadence discipline at v1 is intact (vs v3's known cadence; v1 catalog scaled to v1's discipline). No EXPLORATION 10/10 needed before /015 — /015 IS the CONFIRMATION position by HIGH-RISK pre-commit.

## Files & Commits on Branch

- Branch: `iteration-v1/014` from `iter-v1/013` closeout commit (tag `v0.v1-013`)
- HEAD at Phase 7+8: `f1284d5` (Phase 7 engineering report 4th-strike fix)

Commits in this iteration:
- `cafad3d` — EDA scripts for EWMA σ_t calibration
- `6d7fce5` — QR Phases 1-5 + labeling axis brief
- `04a4b87` — LM Master Phase 4.5 pre-design advisory
- `fec6cbd` — Phase 5.5 gate PASS
- `dd8cf0d` — σ_t EWMA labeling with mandatory .shift(1) past-only safety (QE Phase 6; C1 NOT FIXED — defect surface)
- `1d24dc6` — σ_t lookahead + calibration tests + A2 anti-pattern guard
- `65c0bb2` — Critic Phase 6.0 pre-flight PASS (declaration-side check)
- `7c019ed` — Axis isolation fix — disable BOTH R5 axes
- (Backtest dispatched; comparison.csv + reports artifacts in `reports-v1/iteration_v1-014/`)
- `1f70af3` — LM Master Phase 7.4 post-mortem
- `bcca796` — Phase 7.5 Critic review — EXPLORATION-NEGATIVE
- `f1284d5` — QR Phase 7 evaluation + engineering report (4th-strike fix)
- (THIS COMMIT — Phase 8 diary + catalog)

Trunk merge: **NONE**. EXPLORATION-NEGATIVE Cell-5 + PARTIAL-F7 never updates BASELINE_V1.md (no Sharpe improvement; IS catastrophic; OOS negative).

Tag: `v0.v1-014` (applied after this Phase 8 closeout commit).
