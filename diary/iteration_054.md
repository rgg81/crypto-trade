# Iteration 054 — EXPLORATION (AVAX+DOT independent pair)

## NO-MERGE (EARLY STOP): IS only. IS Sharpe -0.24 — AVAX net negative (-25%), DOT break-even. Pair is unprofitable.

**OOS cutoff**: 2025-03-24

## Results (IS only)

| Period | Sharpe | WR | PF | MaxDD | Trades | PnL |
|--------|--------|-----|------|-------|--------|------|
| IS | -0.24 | 35.3% | 0.96 | 112.4% | 266 | -25% |

**Per-symbol IS**: AVAX 132 trades (-25%, 101.7%), DOT 134 (+0.4%, -1.7%) — both unprofitable

## What Happened

Tested AVAX+DOT as an independent pair. Worst result in the symbol pair series. IS Sharpe is negative (-0.24), WR 35.3% is barely above random, PF below 1.0. AVAX accounts for essentially all losses. DOT is flat.

These mid/low-cap alts don't have predictable 8%/4% moves on 8h candles. The pattern is clear: only BTC+ETH have enough institutional flow and market structure to produce consistent signals at this barrier level.

## Decision: NO-MERGE (EARLY STOP)

Negative IS Sharpe. No reason to continue to OOS.

## Summary of Symbol Pair Exploration (iters 049-054)

| Pair | IS Sharpe | OOS Sharpe | Verdict |
|------|-----------|------------|---------|
| BTC+ETH (baseline 047) | +1.60 | +1.16 | Profitable |
| +SOL+DOGE (049) | +1.37 | +1.16 | SOL/DOGE added nothing |
| +XRP (052) | +0.54 | — | XRP is a drag |
| BNB+LINK (053) | +1.08 | — | Decent IS, early stopped |
| AVAX+DOT (054) | -0.24 | — | Unprofitable |

**Conclusion**: The 8%/4% + 7d + 24mo configuration is BTC+ETH specific. No other pair matches their predictability. Future iterations should focus on improving BTC+ETH rather than expanding the symbol universe.

## Exploration/Exploitation Tracker

Last 10 (iters 045-054): [E, E, X, E, E, E, X, E, E, E]
Exploration rate: 8/10 = 80% — heavily over-explored. Next iterations MUST be exploitation.

## Next Iteration Ideas

1. **Seed-validate iter 050** (balanced class weights, OOS +1.66) — highest priority. If 4/5 seeds positive, it's a new baseline
2. **Feature engineering for BTC+ETH**: Cross-asset features (BTC as leading indicator for ETH), interaction features, multi-timeframe indicators
3. **ATR-dynamic barriers**: Scale TP/SL per-candle by recent ATR — adapt to current volatility
4. **Ternary classification**: Add "neutral" class for ambiguous candles
5. **Regime-aware trading**: Skip low-signal periods (May-Oct 2025 weakness in baseline)
