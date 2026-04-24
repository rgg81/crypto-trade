# Iteration 191 — LINK feature pruning (rejected, confirms LINK's 193 is optimal)

**Date**: 2026-04-23
**Type**: EXPLORATION
**Baseline**: v0.186 — unchanged
**Decision**: NO-MERGE

## TL;DR

Pruning LINK's features from 193 to 130 (dropping 63 lowest-MDI) improves
IS Sharpe marginally (+1.01 → +1.05) but **degrades OOS Sharpe** (+1.44
→ +1.20). Higher OOS WR (56%), lower MaxDD (14%), but smaller per-trade
moves → lower Sharpe.

## The full xbtc/pruning trilogy

| iter | config | features | IS Sharpe | OOS Sharpe |
|------|--------|---------:|----------:|-----------:|
| — | v0.186 baseline | 193 | **+1.011** | **+1.440** |
| 189 | augment +7 xbtc | 200 | +0.683 | +1.660 |
| 190 | swap 7 for xbtc | 193 | +0.423 | +0.993 |
| 191 | prune to 130 | 130 | +1.049 | +1.198 |

**v0.186's 193-feature set is Pareto-optimal for LINK.** Three distinct
modifications all fail to improve both IS and OOS simultaneously.

## Why pruning hurt where iter 117 helped

LINK is a mature co-optimized model; its low-MDI features encode
interaction effects that enable high-conviction predictions. Removing
them makes the model more conservative (higher WR, lower MaxDD) but
also less directional (lower Sharpe).

Iter 117 pruned a new/under-trained meme model (67→45) and doubled its
OOS Sharpe. The difference: LINK's features are load-bearing through
iterations of Optuna co-optimization; the meme model's were not.

The skill's anti-pattern is now empirically confirmed: "For mature
co-optimized models, explicit pruning destroys co-optimization."

## What I tried vs. what learned

Three exploration iterations on LINK feature engineering. Net result:
LINK's feature set is stable and near-optimal. Further LINK-level
feature work has diminishing returns.

Next exploration work should target:
- A different symbol (Model A BTC+ETH has 2x samples, better ratio)
- Entirely new features (AFML fractional diff) not yet in any model
- Label modifications (e.g., timeout horizon)

## Exploration/Exploitation Tracker

Window (181-191): [X, E, X, X, X, X, X, X, E, E, **E**] → **4E/7X**.
Three straight explorations on LINK features. Tracker correcting but
still exploitation-heavy overall.

## Next Iteration Ideas

- **Iter 192**: Test xbtc features on **Model A (BTC+ETH pooled)** instead
  of LINK. Pool has 2× the training samples — feature-dilution is weaker.
  Could also validate or falsify iter 189's collinearity hypothesis.
- **Iter 193**: In-house feature generation — AFML fractional
  differentiation (Ch. 5). Use displacement: swap one low-MDI feature
  for frac-diff'd close at d=0.4. Measure on Model A.
- **Iter 194**: Label horizon experiment on DOT (current timeout is 7d /
  21 candles). DOT moves slowly; 14d may unlock stronger labels.
