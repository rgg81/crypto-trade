# Combined v1 + v2 Portfolio Analysis (FINAL, both fresh)

**Date**: 2026-04-20
**v1**: iter-152 fresh re-run with data through 2026-04-19
**v2**: iter-063-fresh (same iter-059 config, fresh data through 2026-04-20)
**Weighting**: equal weight per coin (1/8 each, user directive)
**OOS window**: 2025-03-24 → 2026-04-20 (13 months)

## Headline — Combined beats both alone on 3 of 4 Sharpe metrics

| Metric | v1 alone | v2 alone | **Combined (1/8 per coin)** |
|---|---|---|---|
| IS trade Sharpe | +2.27 | +1.80 | **+2.88** (+27% vs v1, +60% vs v2) |
| IS monthly Sharpe | +1.30 | +1.04 | **+1.64** (+26% vs v1, +58% vs v2) |
| **OOS trade Sharpe** | +1.40 | +1.94 | **+2.32** (+19% vs v2, +66% vs v1) |
| OOS monthly Sharpe | +1.24 | **+1.78** | +1.69 (−5% vs v2, +36% vs v1) |
| IS trades | 646 | 225 | 871 |
| OOS trades | 191 | 56 | 247 |
| OOS WR | 44.5% | 50.0% | 45.8% |
| OOS PF | 1.30 | 1.80 | 1.46 |

**Real diversification benefit confirmed on trade Sharpe** (most robust metric
for combined portfolios).

## Stability comparison: v1 vs v2 decay

v1 was updated on 2026-04-06 with reported OOS Sharpe +2.83.
We re-ran both at 2026-04-20, extending OOS by ~50 days (Feb → Apr 2026):

| Model | OOS trade Sharpe before | After (+50 days) | Δ |
|---|---|---|---|
| v1 iter-152 | +2.83 (BASELINE peak) | +1.40 | **−50%** |
| v2 iter-059 | +2.02 | +1.94 | **−4%** |

**v2 is dramatically more robust** in the current market regime. v1's
performance decayed 50% with 2 months of additional data, while v2 held up
with only a 4% decline.

## v1 Monthly OOS Decay Analysis

| Month | v1 trades | v1 wpnl | Notes |
|---|---|---|---|
| 2025-03 to 2025-06 | 50 | +20.39 | Strong start |
| 2025-07 | 22 | **−26.76** | Catastrophic month |
| 2025-08 to 2025-09 | 16 | +22.16 | Recovery |
| 2025-10 to 2025-12 | 45 | +48.18 | **Peak performance** |
| 2026-01 | 12 | +6.71 | OK |
| 2026-02 to 2026-04 | 46 | **−5.15** | **Sustained decay** |

v1 peaked at end of 2025 (trade-Sharpe +1.94 over 10-month OOS). Since
then: 3 consecutive weak months, indicating a regime change v1 can't
adapt to.

## v1 per-symbol OOS

All 4 symbols net-positive, but BTC/ETH softening:

| Symbol | IS trade Sharpe | OOS trade Sharpe | OOS wpnl | Decay |
|---|---|---|---|---|
| BNB | +1.08 | **+1.01** | +20.26 | Minimal (holds up) |
| BTC | +1.81 | +0.99 | +19.98 | Moderate |
| ETH | +1.05 | +0.41 | +11.46 | Significant |
| LINK | +0.95 | +0.56 | +13.82 | Moderate |

BNB is v1's most robust symbol; ETH's edge has weakened most.

## Combined OOS per-symbol (equal-coin weighted)

**All 8 coins contribute positively.** Diverse portfolio:

| Symbol | Track | Trades | WR | Scaled wpnl | Share |
|---|---|---|---|---|---|
| NEARUSDT | v2 | 16 | 62.5% | +4.44 | 24.2% |
| XRPUSDT | v2 | 6 | 66.7% | +3.51 | 19.1% |
| BNBUSDT | v1 | 60 | 46.7% | +2.53 | 13.8% |
| BTCUSDT | v1 | 41 | 46.3% | +2.50 | 13.6% |
| LINKUSDT | v1 | 43 | 44.2% | +1.73 | 9.4% |
| SOLUSDT | v2 | 18 | 38.9% | +1.48 | 8.1% |
| ETHUSDT | v1 | 47 | 40.4% | +1.43 | 7.8% |
| DOGEUSDT | v2 | 16 | 43.8% | +0.72 | 3.9% |

Top 4 contributors span both tracks (2 from v2, 2 from v1). No single
track dominates; combined portfolio is genuinely diversified.

## Earlier analysis mistake corrected

My prior analysis (2026-04-19 morning) showed v1 OOS Sharpe +0.13 and
concluded v1 was badly decayed. That was **due to stale feature parquets**
(Apr 12 data vs required Apr 19). After syncing fresh parquets from main
worktree, v1's fresh run gave OOS Sharpe +1.40 — a much more representative
result.

Lessons:
1. Feature parquets must be refreshed before every backtest.
2. Worktrees have separate data/ directories (not symlinked).
3. Raw kline CSVs also need refresh via `uv run crypto-trade fetch`.

## Recommendations

1. **Deploy combined portfolio** as primary strategy. Highest IS and OOS
   trade Sharpe across all configurations tested.
2. **Monitor v1 decay**: if trade Sharpe continues to drop, consider
   dropping ETH (most-decayed) or refreshing v1's training regime.
3. **v2 is the recent-regime specialist**: its 2025 market-tested
   architecture (cooldown=4, z-score 2.5, hit-rate gate off) held up in
   Q1 2026 chop. Consider making v2 more heavily weighted if v1 continues
   to weaken.
4. **Rebuild data refresh automation**: CSV fetch + feature regen should
   be part of the pre-analysis pipeline.

## Files produced

- `reports/iteration_152/` — v1 fresh results (IS/OOS trades, monthly PnL)
- `reports-v2/iteration_v2-063-fresh/` — v2 fresh results
- `analyze_combined_v1v2.py` — parameterized analysis script
- `analysis_v1v2_combined.md` (this file)
