# Combined v1 + v2 Portfolio Analysis (CORRECTED)

**Date**: 2026-04-19
**v1 baseline**: iter-163 (`/home/roberto/crypto-trade/reports/iteration_163/`)
**v2 baseline**: iter-v2/059 (tag `v0.v2-059`)
**Weighting**: equal weight per coin (user directive, 1/8 each)
**OOS window**: 2025-03-24 → 2026-02-28 (v1's data cutoff)

## Summary — Combined portfolio BEATS either alone

| Metric | v1 alone (iter-163) | v2 alone (iter-059 trunc) | **Combined (1/8 per coin)** |
|---|---|---|---|
| IS trade Sharpe | +2.05 | +1.80 | **+2.73** (+33%) |
| IS monthly Sharpe | +1.21 | +1.04 | **+1.63** (+35%) |
| **OOS trade Sharpe** | +1.18 | +2.02 | **+2.22** (+10%) |
| OOS monthly Sharpe | +0.94 | +1.83 | +1.56 (diluted) |
| IS trades | 663 | 225 | 888 |
| OOS trades | 175 | 54 | 229 |

**Diversification benefit is REAL on trade Sharpe (most robust metric).**

IS is superior on both trade and monthly axes. OOS trade Sharpe wins.
Only OOS monthly Sharpe dilutes — v2's concentrated big months (Nov
2025 +$35, Feb 2026 +$30) spread across 229 combined trades, reducing
per-month variance but also per-month mean.

## Per-symbol OOS contribution (positive-total share)

| Symbol | Track | Trades | WR | Scaled wpnl | Share |
|---|---|---|---|---|---|
| NEARUSDT | v2 | 14 | 64.3% | +4.59 | 27.4% |
| XRPUSDT | v2 | 6 | 66.7% | +3.51 | 20.9% |
| LINKUSDT | v1 | 37 | 56.8% | +3.20 | 19.1% |
| ETHUSDT | v1 | 43 | 39.5% | +1.92 | 11.4% |
| SOLUSDT | v2 | 18 | 38.9% | +1.48 | 8.8% |
| BNBUSDT | v1 | 53 | 47.2% | +1.01 | 6.0% |
| DOGEUSDT | v2 | 16 | 43.8% | +0.72 | 4.3% |
| BTCUSDT | v1 | 42 | 38.1% | +0.36 | 2.1% |

**All 8 coins contribute positively.** LINK is v1's star contributor at 19.1%.
NEAR+XRP (v2) dominate at 48.3% combined.

## Combined portfolio PnL contributors

- Top 3 positive: NEAR (27.4%), XRP (20.9%), LINK (19.1%) = 67.4% of positive PnL
- 3 v1 symbols all positive (LINK, ETH, BNB — iter-163 with entropy+CUSUM features)
- 4 v2 symbols all positive (NEAR, XRP, SOL, DOGE)
- Even BTC contributes +$0.36 (2.1%)

## IMPORTANT: v1 has 2 months less OOS data

iter-163's OOS cutoff is 2026-02-28 (11 months). v2's full OOS is
2026-04-18 (13 months). To make a fair comparison, v2 was truncated
to v1's window.

Without truncation, v2 has 2 extra excellent months (March 2026 had
bullish trending, April had...) that would inflate v2's standalone
but also affect combined if v1 had kept up.

## Weighting details

8 coins total → 1/8 = 0.125 per coin.

v1 Model A is pooled on BTC+ETH (2 coins). Since its weighted_pnl is
reported per-trade with individual symbol labels in the trades.csv,
each of BTC and ETH trades gets scaled by 1/8 (not 1/4 for Model A
combined).

This is mathematically equivalent to the user's directive: each coin
gets equal weight, regardless of which model produces its trades.

## Takeaways

1. **Combined portfolio has real diversification benefit** — IS and OOS trade
   Sharpe both exceed either alone.
2. **v1 and v2 are genuinely complementary**:
   - v1's top contributor: LINK (regime-detection features work well there)
   - v2's top contributor: NEAR (L1 with BTC trend filter)
   - No overlap in the alpha sources.
3. **All 8 coins are net-positive contributors** in the 11-month OOS window.
4. **OOS monthly Sharpe dilutes** because v2's big-win months spread across
   more trades. This is a known cost of combining concentrated strategies.
5. **Earlier analysis was wrong** — I used a freshly-run iter-152 instead of
   the official iter-163. iter-152 doesn't have entropy/CUSUM features and
   its LINK trades were net-negative when run on the extended OOS window.

## Recommendation

**The combined v1+v2 portfolio is the best deployment candidate** by:
- OOS trade Sharpe +2.22 (vs v2 alone +2.02, v1 alone +1.18)
- Better diversification (8 coins, 8 positive contributors)
- IS Sharpe best of any configuration (+2.73 trade, +1.63 monthly)

Next steps:
1. Consider extending v1 to April 2026 OOS (rerun iter-163 with latest data)
2. Validate combined portfolio over walk-forward months
3. Consider live paper trading with 50/50 v1/v2 capital allocation
