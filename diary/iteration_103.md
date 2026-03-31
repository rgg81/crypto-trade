# Iteration 103 Diary

**Date**: 2026-04-01
**Type**: EXPLORATION
**Merge Decision**: NO-MERGE (EARLY STOP)

**Trigger**: Year 2022: PnL=-43.3%, WR=34.9%, 64 trades. IS Sharpe -0.82.

**OOS cutoff**: 2025-03-24

## Hypothesis

Enriched meta-labeling with [confidence, direction, natr, adx, symbol_id] provides regime-aware trade filtering, solving iter 102's over-filtering problem.

## What Happened

Pass rate improved dramatically: 26-34% (vs iter 102's 2%). Pass WR in training was excellent: 59-64%. But the model early-stopped in 2022.

**Why**: The meta-model learns from OOF predictions during the 24-month training window. In early 2022, the training window (2020-01 to 2022-01) contains mostly 2020-2021 patterns. The meta-model learns which predictions were profitable in that period. But 2022 was fundamentally different (bear market), so the meta-model's filters don't generalize.

The baseline survives 2022 because it trades MORE (100+ trades) — the law of large numbers smooths out individual bad trades. The meta-model reduces to 64 trades in 2022, making each bad trade more impactful.

## Key Insight: Meta-Labeling Reduces Diversification

By filtering trades, the meta-model reduces temporal diversification (fewer trades per month). In volatile years like 2022, this is fatal — you need enough trades for the 2:1 RR ratio to work. Break-even at 33.3% WR requires ~100+ trades for the law of large numbers to converge. With 64 trades, a run of bad luck triggers early stop.

The meta-model's training pass WR of 59-64% is genuine — it DOES learn useful patterns. But the value of those patterns is dominated by the loss of diversification from having fewer trades.

## Exploration/Exploitation Tracker

Last 10 (iters 094-103): [X, E, X, E, E, E, X, E, E, **E**]
Exploration rate: 7/10 = 70%
Type: **EXPLORATION** (enriched meta-labeling)

## Lessons Learned

1. **Meta-labeling reduces temporal diversification.** With 2:1 RR (TP=8%, SL=4%), break-even WR is 33.3%. This requires ~100+ trades for convergence. Filtering to 64 trades removes the safety net.

2. **Training WR ≠ live WR for meta-models.** 59-64% pass WR in training dropped to 34.4% in live (2022). The meta-model overfits to the training regime.

3. **Meta-labeling is fundamentally limited by the primary model.** If the primary model can't predict well in 2022, no amount of meta-filtering helps — you can't select good predictions from a pool of bad predictions.

4. **The baseline's strength IS its trade volume.** 346 IS trades provides enough diversification for the 2:1 RR to work. Any change that significantly reduces trade count (pruning, meta-labeling, per-symbol, ADX filter) risks early stop.

## Next Iteration Ideas

After 10 consecutive NO-MERGE since iter 093 (094-103), the pattern is clear: the baseline is at a local optimum that cannot be improved by:
- Feature changes (094, 095, 100)
- Weight changes (097, 098)
- Architecture changes (099)
- Post-hoc filtering (102, 103)

The only path forward is either:
1. **Accept the baseline as final** (OOS Sharpe +1.01 is genuinely profitable)
2. **Add more symbols** to increase trade count and diversification (requires full B1/B2/B3 qualification protocol)
3. **Try a completely different model type** (neural network, XGBoost, CatBoost) that might find different patterns

Given 10 failed iterations, option 1 is most honest. The model works — OOS Sharpe +1.01, 107 trades, +51% return. Further iterations risk destroying what works.
