# Iteration 168 Diary

**Date**: 2026-04-21
**Type**: EXPLORATION (DOT Gate 3 screen)
**Decision**: **NO-MERGE (EARLY STOP)** — DOT fails year-1; 3 of 3 recent candidates rejected at same config

## Candidate screening summary (4 iterations)

| Candidate | Iter | Year-1 PnL | IS Sharpe @ stop | IS trades @ stop | Outcome |
|---|---:|---:|---:|---:|---|
| AVAX | 164 | -34.6% | -1.84 | 23 | Rejected |
| LTC | 165 | > 0 (no stop) | +0.60 | 155 | **Accepted & merged (v0.165)** |
| ATOM | 167 | -7.1% | -0.89 | 56 | Rejected |
| DOT | 168 | -14.0% | +0.54 | 17 | Rejected |

Three of four recent candidates failed year-1 at ATR 3.5/1.75. LTC is an outlier — a payments-focused L1 whose dynamics may be closer to LINK than to the L1 smart-contract platforms (AVAX, ATOM, DOT) that all share a similar macro cycle and failed identically.

## Pattern

The common failure mode: each rejected candidate had positive or marginal IS metrics but lost meaningfully in 2022 specifically. 2022 was a post-FTX bear market — alt-L1 tokens were heavily sold and their price dynamics decoupled from their later 2023–2024 behaviors. Walk-forward predictors trained on a 2-year window ending in 2022 were trying to extrapolate from pre-bear regimes into the bear regime itself. LINK & LTC survived; AVAX, ATOM, DOT did not.

This is a **regime-mismatch problem**, not a labeling or hyperparameter problem. Re-running AVAX/ATOM/DOT with different ATR multipliers would be parameter-tuning for a known-bad period, which the skill explicitly bans after an early stop.

## Research Checklist

- **B — Symbol Universe (DOT)**: full Gate 1 → Gate 3 protocol. Gate 3 failed on trade count + year-1 PnL.
- **E — Comparative pattern** across candidates: analyzed (see summary above).

## Exploration/Exploitation Tracker

Window (159-168): [X, X, E, E, E, E, E, X, E, E] → **7E / 3X**, 70% E. Well above the 30% floor (and trending high — next few iterations should be EXPLOITATION to balance).

## Lessons Learned

1. **Fail-fast protocol is paying off** — rejection in 11 minutes for DOT (vs ~90 min full run). Three candidate rejections total cost 38 min of compute (AVAX 9 + ATOM 19 + DOT 11). A full-run approach would have been 3 × 90 = 270 min with the same conclusions.

2. **Gate 3 at a single ATR config is a blunt instrument** — it correctly filters by year-1 but doesn't distinguish "bad candidate" from "candidate that needs different labeling". DOT's IS Sharpe +0.54 after year-1 collapse hints at actual signal; it's just not tolerable under our fail-fast rules.

3. **Alt-L1 candidates (AVAX, ATOM, DOT) share a failure mode.** LTC succeeded because it is NOT a smart-contract L1 and doesn't follow the alt-L1 cycle.

## Next Iteration Ideas

### 1. Iter 169: PIVOT — per-symbol Model A (BTC alone, ETH alone) (PRIORITY)

Per iter-167 Next Ideas #3: Model A (BTC+ETH pooled) alone contributes +9.3% OOS PnL at Sharpe +0.24 in the current baseline. Iter 076 observed ETH SHORT 51% WR vs BTC LONG 43.6% WR — very different dynamics. Splitting into per-symbol sub-models may extract more signal.

Test: run Model A_BTC (BTCUSDT alone, ATR 2.9/1.45, 24mo, 193 features, fail-fast on) and Model A_ETH (ETHUSDT alone, same config). Cost: 90 min × 2 = 3 hours, with fail-fast potentially shortening if either fails year-1. Pool metrics derived from combined A_BTC + A_ETH + C + LTC trades. Tag: EXPLORATION (architecture change, per skill).

### 2. Iter 170: If per-symbol passes, validate pooled A_BTC+A_ETH+C+LTC portfolio

Same aggregation mechanism as iter 165: each model is independent. Combine trades, compute portfolio metrics, compare to baseline v0.165 (Sharpe +1.27). If improved AND concentration moves further toward 30%, MERGE.

### 3. Iter 171: If per-symbol fails, try colsample_bytree tuning on Model A

Implicit feature pruning via colsample_bytree (iter 117 lesson: for mature co-optimized models, explicit pruning destroys Optuna; colsample_bytree is the right tool). Tune Optuna's colsample_bytree range to [0.3, 0.7] (more aggressive than default [0.5, 1.0]) and see if Model A Sharpe improves.

### 4. Iter 172+: New candidate categories (out-of-cycle with alt-L1 failures)

AAVE (DeFi), FIL (storage), TIA (modular), LDO (liquid staking) — all have different macro cycles from alt-L1s. If Model A improvements exhaust headroom, these are the next universe candidates.

User exclusions still active: DOGE, SOL, XRP, NEAR.
