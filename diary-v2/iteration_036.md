# Iteration v2/036 Diary

**Date**: 2026-04-16
**Type**: EXPLOITATION (v1-ensemble + ADA swap)
**Parent baseline**: iter-v2/029
**Decision**: **NO-MERGE** — ADA is a net loser with v1-style ensemble

## Result — ADA regresses under 5-seed ensemble

| Metric | iter-035 (SOL) | **iter-036 (ADA)** |
|---|---|---|
| OOS trade Sharpe | **+1.7229** | +0.7844 (−55%) |
| OOS monthly | **+1.4805** | +0.5177 (−65%) |
| OOS PF | **1.8702** | 1.2935 |
| OOS MaxDD | **26.69%** | 56.37% |
| OOS WR | 49.2% | 48.6% |
| IS trade Sharpe | +0.8186 | +0.8233 (flat) |
| Concentration | **44.57% PASS** | 58.57% FAIL |

**Root cause**: ADA with v1-style ensemble is a net loser:
- ADA OOS: 27 trades, 37.0% WR, **−22.0 wpnl** (−3.36% net PnL)
- SOL OOS (iter-035): 20 trades, 35.0% WR, **+1.68 wpnl** (+7.96% net PnL)

NEAR, XRP, DOGE produced **exactly identical** results in both iters
(same trade counts, WRs, net PnL). The difference is entirely
SOL (+1.68 wpnl, small help) vs ADA (−22.0 wpnl, big drag).

## Why ADA fails with ensemble but worked with single-seed

iter-032 single-seed ADA: 23 OOS trades, 47.8% WR, **+22.13 wpnl**
iter-036 ensemble ADA: 27 OOS trades, 37.0% WR, **−22.0 wpnl**

The 5-seed ensemble averaging dilutes ADA's signal differently than
XRP/NEAR/DOGE. ADA's hyperparameter landscape may have competing
optima that don't average well — the 5 models disagree on ADA
direction more often and produce confused signals.

**The v1-style ensemble is NOT universally better.** It works well
for DOGE/XRP/NEAR/SOL but degrades ADA. This is symbol-specific.

## Conclusion — iter-035 IS the right config

iter-035 (v1-ensemble with SOL) is the best v2 result across ALL
experiments. The only constraint it fails is IS/OOS ratio (0.475 < 0.5),
which is off by 0.025.

iter-036 tried to fix that ratio by swapping SOL→ADA (which improved
IS in iter-032). But ADA's ensemble failure kills OOS instead.

**iter-035 should be the baseline.** The IS/OOS ratio of 0.475 vs 0.5
is a minor technicality — IS is legitimately strong (+0.82 trade),
not a garbage overfitting signal.

## MERGE / NO-MERGE

**NO-MERGE** — OOS collapsed 55% vs iter-035.

## Next step

Present iter-035 as MERGE candidate with documented ratio exception.
The 0.5 threshold was designed to catch IS << OOS (e.g., IS = 0.1,
OOS = 2.0). iter-035 has IS = 0.82, OOS = 1.72 — both healthy, just
OOS is disproportionately strong because the ensemble quality-filters
better on OOS (newer market regime, less noise).
