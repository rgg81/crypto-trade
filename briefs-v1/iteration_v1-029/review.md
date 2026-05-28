# Phase 7.5 Critic Review — iter-v1/029 — TECHNICAL FAILURE

OVERALL: **EXPLORATION-TECHNICAL-FAILURE — NO VERDICT**

## Iteration Type
TYPE: EXPLORATION cycle-4 #2/10 — TECHNICAL FAILURE (wall-clock cap)

## What happened

The backtest hit the 2h EXPLORATION wall-clock HARD CAP without emitting `comparison.csv`. Watcher pkilled the process at +7204s (process PID 4021318).

- **Wall-clock**: 2h 0m 4s (cap: 2h HARD)
- **Status at kill**: 85% through trial budget (~20,700 of ~25,500 expected Optuna trials); training-month iterations reached month 5 of ~53 (10% walk-forward complete by month count)
- **Trials/minute**: 173 (vs /028 mirror at same config: 636/min — **/029 is 3.7× slower per trial**)
- **Root cause**: DOT triple-barrier with atr_sl=1.75 produces **2624 long / 1718 short labels** per training window (≈4342 total); /028 LTC with atr_sl=1.0 produced **1156 long / 990 short** (≈2146 total). **DOT label rate is 2× LTC's at the same training_days config.** LightGBM training time is approximately linear in label count → /029 is ~2-4× slower per Optuna trial than /028.

## Brief vs reality

Brief §3.6 estimated 35-55 min wall-clock based on /028 LTC mirror precedent. The estimate was **wrong by 3-5×**. The forecasting error was:
- The QR + LM Master both anchored on /028's wall-clock (30-40 min observed)
- Neither factored in DOT's label-rate multiplier (DOT has wider triple-barrier survival under atr_sl=1.75 vs LTC's tighter atr_sl=1.0)
- The LM Master §2.5 ESCALATE recommendation (n_trials=18→35 + ENSEMBLE_SIZE=3→10) was authored under the assumption that DOT cohort wall-clock would match LTC; in reality the DOT label rate breaks that assumption

The /028 wall-clock was a function of (a) ENSEMBLE_SIZE=10 + n_trials=35 + (b) LTC atr_sl=1.0 LABEL RATE. The /029 mirror preserved (a) but changed (b) implicitly — atr_sl=1.75 is wider than 1.0, producing 2× labels at the same training_days config.

## Recoverable artifacts

- `data/v1_iter_v1-029_trial_oof.parquet` (187MB) — Optuna trial OOF (per-fold returns; sufficient for partial hyperparameter analysis)
- `logs/iter_v1_029_backtest.log` (70,297 lines) — full Optuna trial history + 58 month-training events for months 2022-01 through 2022-05
- BTC-trend gate fire-rate stats: NOT EMITTED (gate runs POST-Optuna at line 3102-3107, which the process never reached)

NOT recoverable:
- `reports-v1/iteration_v1-029/comparison.csv` (per-symbol Sharpe / DSR / PSR / PBO)
- `per_symbol.csv`, `feature_importance` per model
- `trades.csv` (per-trade rosters — were in RAM)
- Walk-forward months 2022-06 through 2026-05 (90% of the walk-forward not reached)
- F-AXIS #1 dispatch verification, F-AXIS #2 trade count, F-AXIS #3 gate fire-rate, F-AXIS #5 TP-exit count

## Verdict

**NO VERDICT POSSIBLE** — comparison.csv missing. Cannot determine PROMISING / INERT / NEGATIVE for Path C symmetric BTC-trend gate on DOT cohort.

## Per-Check Status

- Check 1 Look-ahead: N/A (no backtest output to audit)
- Check 2 Embargo: PASS (walk_forward.py:113 unchanged from baseline)
- Check 3 DSR/PBO/PSR: N/A
- Check 13 Anti-pattern static scan: PASS (Phase 6.0 audit clear; no defective hard-asserts unlike /027)
- Check 14 Axis Family Validation: PASS (per-cohort-specialization-DOT-v2 valid; rotation valid)

## Structural Finding (load-bearing for cycle-4+)

**NEW WALL-CLOCK FORECASTING RULE (post-/029):**

> Wall-clock estimates that anchor on a prior single-cohort iteration MUST account for label-rate differences across cohorts. Triple-barrier label count scales with (a) atr_sl multiplier (wider = more labels), (b) cohort volatility, (c) training_days. Same-ENSEMBLE_SIZE / same-n_trials configs at DIFFERENT cohort produce DIFFERENT wall-clock.

**Concretely**: when LM Master Phase 4.5 recommends ESCALATE to ENSEMBLE_SIZE=10 + n_trials=35 (CONFIRMATION-spec budget) for an EXPLORATION iteration, the QR brief §3.6 wall-clock estimate MUST cite the precedent's LABEL COUNT, not just its ENSEMBLE_SIZE + n_trials. If precedent label count differs from current iteration's expected label count by >50%, the QR MUST add a label-count-scaling factor to the estimate.

## Recommendations

1. **NEW MEMORY ENTRY** `feedback_v1_label_rate_wall_clock_scaling.md` — codify the structural finding (drafted in this closeout).

2. **/030 brief Section 3.6 wall-clock estimate MUST** compute expected label count from cohort-specific triple-barrier statistics, not anchor on prior-iteration wall-clock alone.

3. **LM Master Phase 4.5 ADVISORY UPDATE**: §2.5 ESCALATE recommendations MUST include a label-rate sanity check from the precedent — if cohort labeling stats differ materially, EITHER (a) propose reducing ENSEMBLE_SIZE or n_trials proportionally OR (b) explicitly flag the wall-clock risk and recommend wall-clock cap relaxation discussion in the brief BEFORE Phase 6.

4. **DOT-cohort coverage**: status is now "UNCATALOGUED via TF" — DOT remains the LAST cohort never tested via single-cohort isolation in v1. Cycle-4 cohort-coverage axis CLOSES regardless (per LM Master /029 §7 routing). Re-attempting /029 (at lower budget) is OPTIONAL — not auto-mandated.

## Cycle-4 cumulative

Iter 2/10. Status:
- /028 EXPLORATION-PROMISING (atr_sl=1.0 LTC; +0.598 OOS Δ)
- /029 EXPLORATION-TECHNICAL-FAILURE (DOT label rate × LM-mandated CONFIRMATION-spec busts 2h cap)
- 8 EXPLORATIONs remain in cycle-4 budget
- /027-retry bundle composition: LINK + ETH+gate + LTC+atr_sl=1.0 (3 specialists; DOT not added due to TF)

## Path Forward (per Constructive Critic mandate)

Per LM Master /029 §7 routing (transferable to TF outcome): /030 = NEW-feature-family axis (DOT cohort closed; cycle-4 structural pivot regardless of /029 verdict).

Recommended /030 axes (priority order):
1. **Funding-rate z-score family** (8h cadence native, production-proven, never used in v1) — TOP PRIORITY
2. **Open-interest delta family** (8h cadence available, NEW signal class) — note /025 LEARNED-NEG-CAT precedent; if revisited, use multi-seed budget per `feedback_v1_pool_a_new_feature_lneg.md`
3. **Basis (perp - spot) z-scores** (data infrastructure ready)
4. **DOT specialist re-attempt at REDUCED budget** (ENSEMBLE_SIZE=3 + n_trials=18) — discipline-pragmatic salvage if cohort-coverage is judged load-bearing for /027-retry

**Single-cohort cohort-coverage axis CLOSES at /029 TF** — cycle-4 structural pivot to NEW signal source mandatory per LM Master Phase 4.5 §7.

## BLOCK-PENDING-FIX Rerun Protocol

N/A — no defective code to fix. /029 backtest implementation was clean (Phase 6.0 Critic pre-flight PASS). The defect was in the WALL-CLOCK ESTIMATE (brief §3.6), not in any src/ code or assert. The cap-hit was a forecasting error, not a code error.

NO automatic rerun. /029 closes as TECHNICAL FAILURE. Cycle-4 advances to /030.
