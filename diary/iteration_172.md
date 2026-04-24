# Iteration 172 Diary

**Date**: 2026-04-22
**Type**: EXPLORATION (DOT full IS observation + R1 Risk Mitigation applied)
**Decision**: **NO-MERGE** (strict concentration constraint fail)

## Summary

This iteration broke with autopilot-era shallowness — the QR did actual quantitative work across three research angles and produced evidence-driven conclusions, both positive and negative. Net outcome: no baseline change, but four substantive results that shape future iterations.

1. **DOT is not a failed candidate.** When the year-1 fail-fast is disabled, DOT's full IS+OOS profile is: IS Sharpe −0.07 (break-even), IS PnL −5.96% (negligible), OOS Sharpe +0.65, OOS PnL +19.4%, OOS MaxDD 20.6%. The iter-168 "reject" was chasing a regime outlier (Dec 2022 post-FTX), not a systemic failure.

2. **MDI-based feature pruning on single-symbol models is a trap.** Confirmed by iter-171 catastrophic result (IS Sharpe −1.40) and further validated here: the skill's anti-pattern list (iter-094) applies.

3. **R1 consecutive-loss cool-down is real and measurable.** DOT's streak=2-3 buckets have WR of 22-23% vs. break-even ~33.3%. Applying K=3 C=27 raises DOT IS Sharpe from −0.21 to +1.04 — decisive evidence that selective cool-down mitigates the adverse-streak failure mode.

4. **R1 alone cannot satisfy the strict hard constraints.** Adding DOT(R1) to A+C+LTC passes the 1.0 Sharpe floors and the OOS-vs-baseline Sharpe check, but the single-symbol concentration constraint (LINK 63.8% > 30%) and the MaxDD-regresses-vs-baseline issue prevent a strict merge. Diversification exception needs MaxDD to *improve* by >10%, not regress.

## Phase 7 metrics

Best-performing pooled variant = **A+C+LTC+DOT with R1 DOT+LTC K=3 C=18**:

| Metric       | Baseline v0.165 | Iter 172 pooled | Δ |
|--------------|----------------:|----------------:|----|
| IS Sharpe    | +1.08           | +1.02           | −5.6% |
| OOS Sharpe   | +1.27           | +1.30           | +2.4% |
| OOS MaxDD    | 30.56%          | 33.09%          | +8.3% (worse) |
| OOS PnL      | +73.64%         | +89.35%         | +21.3% |
| OOS Trades   | 202             | 253             | +25.2% |
| LINK share   | 77.5%           | 63.8%           | −13.7 pp (better) |

## Merge decision (strict)

Passes: both Sharpe floors, primary (OOS > baseline), MaxDD ≤ 36.67%, min trades, PF.

Fails: single-symbol concentration (LINK 63.8% > 30%).

Diversification exception does NOT apply: requires OOS MaxDD to *improve* by >10%; iter 172 has MaxDD regressing by 8.3%.

→ **NO-MERGE**.

## What we need for a merge in future iterations

Three orthogonal avenues, any one of which could enable a merge:

A. **MaxDD reduction to the baseline level** (30.56% or lower) while keeping the concentration improvement. Requires either (a) even tighter R1 (C=36+) that trades more selectivity for risk control, or (b) adding a negatively-correlated signal so the pooled MaxDD compresses.

B. **Concentration below 30% outright.** With LINK at ~57% of raw OOS PnL in the baseline, driving it below 30% requires at least two more DOT-class symbols with comparable OOS PnL (~16% each). Iter 173+ candidate expansion with R1 pre-applied.

C. **Real R1 in the backtest engine.** Post-hoc simulation is valid for READ-ONLY analysis but a merge should be evidenced by the actual pipeline producing the target metrics. Iter 173 = implement `BacktestConfig.risk_consecutive_sl_limit` / `risk_consecutive_sl_cooldown_candles`; re-run the full A+C+LTC+DOT portfolio with R1 live; verify metrics match the simulator.

## Research Checklist (what the QR actually did this time)

- **A3 (Feature Contribution)**: executed in iter 171 via `dot_deep_dive.py`. Finding: DOT's MDI top-20 shares only 8/20 with LTC. Hypothesis rejected in iter 171.
- **B1 (Correlation & Regime)**: executed via `regime_filter_research.py`. 9 candidate BTC regime metrics evaluated, none separates DOT's good/bad months cleanly. Counter-intuitive finding: DOT's worst month had LOWER BTC vol, not higher.
- **C (Labeling / NATR)**: NATR distribution executed in iter 171. DOT median 4.15% fits ATR 3.5/1.75.
- **E (Trade Pattern)**: executed; LTC vs DOT Dec 2022 trade-by-trade reveals DOT over-traded (7 vs 3) → selectivity is the problem.
- **R1 (Risk Mitigation — NEW)**: executed via `risk_mitigation_r1.py` and `r1_sweep.py`. First use of the skill's new Risk Mitigation phase. K=3 C=27 or DOT+LTC K=3 C=18 are the evidence-backed configs.

## Exploration/Exploitation Tracker

Window (163-172): [E, E, E, X, E, E, E, E, X, E] → 8E/2X. Well over 30% floor; next iterations (R1 engine implementation) will be EXPLOITATION-heavy.

## Next Iteration Ideas

### 1. Iter 173 (EXPLOITATION, PRIORITY) — Implement R1 in the backtest engine

Code change: add `risk_consecutive_sl_limit`, `risk_consecutive_sl_cooldown_candles` to `BacktestConfig`. Implement the check in `run_backtest`'s trade-open path. Re-run A+C+LTC+DOT with R1 K=3 C=18 (or the user-selected config) and verify metrics match the simulator. If they match AND the merge rules pass, MERGE.

If R1 is proven to reduce portfolio MaxDD consistently (tested on the full A+C+LTC trades), make it part of the new baseline — update BASELINE.md accordingly.

### 2. Iter 174 (EXPLORATION) — Apply R1 prophylactically to failed candidates

With R1 in the engine, revisit AVAX, ATOM, AAVE, DOT screens WITH R1 ACTIVE from the start. Hypothesis: R1 turns knife-catching streaks into survivable periods, making previously-rejected candidates viable. Even a 1-of-3 pass rate across AVAX/ATOM/AAVE would let us push concentration below 40%.

### 3. Iter 175+ — Non-R1 risk mitigations

R2 (drawdown-triggered position scaling), R3 (OOD feature detection), R5 (concentration soft-cap) are the skill's other levers. R3 especially — if a Mahalanobis z-score on current candle features vs training-period distribution would have flagged Dec 2022 inputs as out-of-distribution, that's a principled filter with broader applicability than R1's streak-counter.

## lgbm.py Code Review

No code changes this iteration. `lgbm.py` processed the `yearly_pnl_check=False` case correctly (full walk-forward ran to completion). One observation worth tracking: the `_train_for_month` path is robust when DOT's IS is borderline — no training errors, no NaN predictions, no crashes.
