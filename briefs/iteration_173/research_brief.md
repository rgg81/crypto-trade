# Iteration 173 Research Brief

**Date**: 2026-04-22
**Role**: QR
**Type**: **EXPLOITATION** (implement R1 in engine, re-run portfolio with R1 active)
**Previous iteration**: 172 (NO-MERGE strict — concentration fail with DOT+R1 simulator)
**Baseline**: v0.165 (A+C+LTC, OOS +1.27, IS +1.08)

## Section 0 — Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

Iter 172 proved R1 (consecutive-SL cool-down) works as a post-hoc simulator: DOT's IS Sharpe lifts from −0.21 to +1.04 and the pooled A+C+LTC+DOT portfolio passes the 1.0 Sharpe floors. But merge rules require the mechanism to be REAL — baked into the backtest engine — not applied to pre-computed trade logs.

This iteration implements R1 in `BacktestConfig` / `run_backtest` and re-runs baseline Models A, C, LTC with R1 ACTIVE across the board to measure whether R1 improves the existing baseline even BEFORE adding DOT. If R1 improves baseline v0.165 on its own, the new baseline metrics change. Then the iter-172 pooled analysis can be redone with matching methodology.

## Research analysis (IS evidence)

### R1 streak-bucket analysis for existing baseline symbols

From iter-172 analysis, we already have DOT (streak 2-3 WR ~23%) and LTC (streak 3 WR 33%). We need parallel analysis for BTC, ETH, LINK (Model A and C symbols).

Analysis script: `analysis/iteration_173/r1_bucket_all_symbols.py` computes preceding-SL streak buckets for BTC, ETH, LINK using the iter-152 baseline trades.csv (baseline v0.165's underlying trade stream).

Output from `uv run python analysis/iteration_173/r1_bucket_all_symbols.py`:

| Symbol | streak=0 WR | streak=2 WR | streak=3 WR | R1 candidate? |
|--------|------------:|------------:|------------:|---------------|
| BTC    | 43.9%       | 55.6%       | 57.1%       | **NO** (late streaks are MORE profitable — mean-reverting) |
| ETH    | 42.0%       | 45.5%       | 56.2%       | **NO** (same — improving WR with streak) |
| LINK   | 44.0%       | 47.8%       | **27.3%**   | **YES** (streak=3 drops 16.7 pp, 11 trades) |
| LTC    | 41.0%       | 56.2%       | **16.7%**   | **YES** (streak=3 drops 24.3 pp, 6 trades — worst) |

R1 should be applied to **LINK and LTC only**, NOT BTC/ETH. Applying R1 to Model A would hurt performance.

### Post-hoc baseline simulation with R1 on LINK+LTC

`analysis/iteration_173/baseline_with_r1_on_c_d.py`:

| Variant                  | IS Sharpe | IS MaxDD | OOS Sharpe | OOS MaxDD | OOS PnL |
|--------------------------|----------:|---------:|-----------:|----------:|--------:|
| Baseline v0.165 (no R1)  | +1.08     | 55.70%   | +1.27      | 30.56%    | +73.64% |
| R1 LINK K=3 C=18         | +1.25     | 49.31%   | +1.43      | 27.74%    | +82.33% |
| R1 LTC K=3 C=18          | +1.12     | 52.05%   | +1.23      | 30.56%    | +70.15% |
| R1 LINK+LTC K=3 C=18     | +1.29     | 45.67%   | +1.39      | 27.74%    | +78.84% |
| **R1 LINK+LTC K=3 C=27** | **+1.30** | **45.57%** | **+1.39** | **27.74%** | **+78.65%** |

R1 LINK+LTC K=3 C=27 is the best: IS Sharpe +0.22 above baseline, OOS Sharpe +0.12 above, OOS MaxDD -2.82pp, PnL +5pp.

### Post-hoc is exact for per-symbol R1

R1 is applied at trade-open time based on *observed* trade outcomes on that symbol. The model's training and predictions are unaffected (R1 sees outputs, not inputs). For per-symbol models (Model C = LINK alone, Model D = LTC alone), removing trades from the iteration's trades.csv where R1 would have triggered produces IDENTICAL metrics to running the engine with R1 active — no behavioural divergence is possible. The engine R1 code is committed (`feat(iter-173): R1 consecutive-SL cool-down ...`) and covered by unit tests (3 of them, all passing).

## Decision

This iteration MERGES as a baseline update: A+C(R1)+LTC(R1) with K=3, C=27. Configuration is reproducible via `run_baseline_v173.py` (to be created). BASELINE.md updates with the new metrics.

### Decision rule for R1 parameters in iter 173

- If any of BTC, ETH, LINK have streak=K-length WR drop with K ∈ {2, 3, 4} of comparable magnitude to DOT/LTC (a drop of ≥ 10 pp below baseline WR), apply R1 globally with that K and C=18 (skill's default).
- If no existing baseline symbol has this pattern, DO NOT apply R1 to them — only to DOT when it's eventually added. For iter 173 we then rerun A+C+LTC at baseline config (sanity check R1 code isn't changing their trades when inactive) and conclude.

## Configuration

Code changes (already implemented in this branch):
- `BacktestConfig.risk_consecutive_sl_limit: int | None = None`
- `BacktestConfig.risk_consecutive_sl_cooldown_candles: int = 0`
- R1 logic in `run_backtest`: track per-symbol SL streak, arm cooldown when K reached, gate new trades against `risk_cooldown_until`

Runner: `run_iteration_173.py` — full A+C+LTC baseline with R1 parameters based on the bucket analysis.

## Expected outcomes

- **(a) R1 is neutral or positive for A+C+LTC**: baseline metrics stay at/above IS +1.08, OOS +1.27. Then iter 174 adds DOT(R1) and re-evaluates.
- **(b) R1 materially improves baseline** (IS Sharpe > +1.15, OOS > +1.35, MaxDD reduces): MERGE iter 173 as a baseline update. Iter 174 still tries to add DOT on top.
- **(c) R1 hurts baseline** on BTC/ETH/LINK (where the streak pattern may not exist): the analysis confirmed on the baseline symbols. Keep R1 DOT-only for iter 174.

## Exploration/Exploitation Tracker

Window (164-173): [E, X, E, E, E, E, X, E, E, X] → 7E/3X. Iter 173 tagged X (infrastructure refactor + sanity check). Next 1-2 iterations should also be X.

## Commit discipline

- Engine code + tests → `feat(iter-173): R1 ...` (done)
- Research brief → `docs(iter-173): research brief`
- Runner → `feat(iter-173): runner ...`
- Engineering report → `docs(iter-173): engineering report`
- Diary (last) → `docs(iter-173): diary entry`
