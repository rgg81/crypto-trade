# Iteration 169 Research Brief

**Date**: 2026-04-21
**Role**: QR
**Type**: **EXPLORATION** (architecture change — per-symbol Model A)
**Previous iteration**: 168 (NO-MERGE EARLY STOP, DOT)
**Baseline**: v0.165 (A+C+LTC, OOS Sharpe +1.27)

## Section 0 — Data Split (verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

Model A (BTC+ETH pooled) contributes only +9.3% OOS PnL at Sharpe +0.24 in the current baseline reproduction — the weakest of the three models. Iter 076 (historical) observed that ETH and BTC have meaningfully different dynamics (ETH SHORT 51% WR vs BTC LONG 43.6% WR). Per the skill's B3 decision framework, per-symbol models are indicated when pooled symbols have divergent WR profiles.

This iteration runs **Model A_BTC** (BTC only, same config as Model A). If it passes standalone profitability (IS Sharpe > 0, no year-1 abort), iter 170 will run Model A_ETH, and iter 171 will pool A_BTC + A_ETH + C + LTC for a MERGE decision.

Three symbol-expansion candidates in a row failed (AVAX, ATOM, DOT). This pivots compute from "add a 4th model" to "extract more signal from the existing 2 large-cap symbols".

## Research Analysis

### B — Architecture (Option B: Per-symbol)

The skill's B3 decision rule:

> Per-symbol models (Option B)
> Use when: Symbols have fundamentally different dynamics (e.g., ETH SHORT 51% WR vs BTC LONG 43.6% WR).
> Risk: Fewer training samples per model (~2,200/year for one symbol on 8h). Only viable for symbols with 3+ years of IS data.
> Decision rule: If per-symbol IS Sharpe > pooled IS Sharpe for BOTH symbols → use per-symbol.

BTC has 6,906 8h candles dating back to 2020, which is 5+ years of training data. Beyond the 3-year minimum.

**Sample / feature ratio concern**: single-symbol BTC over a 24-month training window is ~2,200 samples. With 193 features, ratio = 11 (catastrophic per iter 078 / 094). 

However, this concern applies primarily to the POOLED setting where BTC and ETH data combine. Standalone BTC with 193 features is the natural continuation of the existing baseline config — and the iteration tests whether the ratio collapse matters in practice.

If IS Sharpe collapses (< 0), that's the signal to prune features in iter 170 (reduce to ~50 features for per-symbol).

### E — Comparison target

From the iter-152 reproduction (baseline v0.165), Model A per-symbol metrics:

| Symbol | Trades | IS WR | IS PnL | OOS trades | OOS WR | OOS PnL |
|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 125 | 46.4% | +68.98% | 51 | 33.3% | −5.28% |
| ETHUSDT | 194 | 41.2% | +73.56% | 59 | 40.7% | +19.80% |

These are the POOLED model's per-symbol contribution (same features, same model, different symbol). Iter 169's standalone BTC run tests: does a BTC-only model do better, worse, or about the same?

Decision criterion: if stand-alone BTC IS Sharpe exceeds pooled-Model-A-per-BTC's Sharpe (roughly +0.24 scaled down for BTC's share of PnL), proceed to ETH stand-alone in iter 170. If it collapses, iter 170 tries the per-symbol BTC with pruned features.

## Configuration

Runner: `run_iteration_169.py`. `symbols=("BTCUSDT",)`, ATR 2.9/1.45 (matching current Model A labeling), 24mo training, `BASELINE_FEATURE_COLUMNS` (193), `yearly_pnl_check=True`. Same ensemble seeds.

## Expected Outcomes

- **Strong pass** (IS Sharpe > 0.5, year-1 clean): BTC stand-alone likely better than pooled. Proceed to ETH.
- **Marginal pass** (IS Sharpe 0–0.5): document and decide.
- **Fail** (year-1 abort OR IS Sharpe ≤ 0): feature count too high for per-symbol. Iter 170 = BTC with 50-feature prune.

## Exploration/Exploitation Tracker

Window (160-169): [X, E, E, E, E, E, X, E, E, E] → **8E / 2X**, 80% E. Well above 30% but heavy on exploration — after iter 169 we should run 2-3 exploitation iterations to rebalance.

## Commit Discipline

Separate commits: research brief, runner, engineering report, diary (last).
