# Iteration v3-008 — Diary (ABORTED)

## Decision: ABORTED at 4h 15min wall-clock

iter-v3/008 was killed mid-run after extrapolation showed ~25h total wall-clock for `--seeds 5 --n-trials 50` on full v3 universe. Multi-day single-iteration runs were deemed infeasible by the user. Killed at 2026-05-06 ~15:01 CEST while training MODEL D (TRXUSDT) seed 42 month 2025-09 (~85% of seed 42 done; seeds 123/456/789/1001 not started).

## What Was Configured

- TYPE: CONFIRMATION (per pre-cadence-discipline rules)
- 13 features (top-14 from iter-v3/007 minus `vwap_dev_50` for IC redundancy)
- Full v3 universe: BCHUSDT, MKRUSDT, LDOUSDT, TRXUSDT
- `--seeds 5 --n-trials 50` (last 5-seed run before cadence cap)
- ENSEMBLE_SIZE=5, Optuna-tuned colsample 0.3-1.0
- Setup commit: SHA 56b8f8b

## What Was Persisted

- `reports-v3/iteration_v3-008/trial_oof_returns.parquet` — 318 MB, partial (seed 42 only, mostly complete)
- `reports-v3/iteration_v3-008/run.log` — 28+ MB, training trace
- NO `comparison.csv`, `pareto_front.csv`, `dsr.json`, `in_sample/`, `out_of_sample/` — those are written only at end of seed loop, which never reached

## What This Iteration Cost

- 4h 15min wall-clock (~5% of agent quota efficient — backtest was detached, no Engineer supervisor)
- Skill update: established the cadence-discipline rule (10 EXPLORATION per CONFIRMATION, 4h cap, max 1 CONFIRMATION/day)
- Memory rule: feedback_v3_cadence_discipline.md
- Net positive: the abort triggered the right structural change

## What Replaces iter-v3/008

Per the new cadence discipline (skill SHA 6c7522b on iteration-v3/008, cherry-picked to quant-research as 4d5f2dd):

- iter-v3/009 onward = EXPLORATION iterations only (1-2h each, single-axis variation)
- After 10 EXPLORATIONs, a CONFIRMATION can launch (4h cap, --seeds 2 --n-trials 50, bundles best findings)
- iter-v3/007 already counts as the FIRST EXPLORATION precedent in `briefs-v3/exploration_catalog.md`
- iter-v3/008-018 (estimated) will be the next 9 EXPLORATIONs varying features/symbols/labels
- iter-v3/019 (estimated) could be the first valid CONFIRMATION

## Lessons

1. **Wall-clock budgets must be HARD CAPS, not estimates.** "5-9h budget" with no enforcement = 25h reality on full config.
2. **CONFIRMATION cannot be rushed.** The temptation to confirm a single EXPLORATION's promise (iter-v3/007 → iter-v3/008 was 1-to-1) bypasses the diversity benefit. 10-EXPLORATION cadence forces the QR to bundle multiple findings, increasing the bet's robustness.
3. **--seeds 5 was always overkill for v3.** With ENSEMBLE_SIZE=5 inner ensemble averaging predictions + iter-v3/006 fix making outer seeds meaningful, 2 outer is enough variance estimate for production. 5+ is wasteful.
4. **Kill switch matters.** Without the user's intervention, iter-v3/008 would have run another 21h. Future EXPLORATION wall-clock cap is at 2h; CONFIRMATION at 4h. Engineer Phase 6 prompts must include the kill-on-overshoot logic.

## Next Iteration

iter-v3/009 — first EXPLORATION under the new cadence discipline. TYPE=EXPLORATION, --exploration mode, single-axis variation. Specific axis to be decided by QR; candidates from iter-v3/007's diary "Next Iteration Ideas" + cadence-discipline cycle suggestions.
