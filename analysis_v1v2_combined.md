# Combined v1 + v2 Portfolio Analysis

**Date**: 2026-04-19
**v1 baseline**: iter-152 (run fresh on quant-research worktree)
**v2 baseline**: iter-v2/059 (tag `v0.v2-059`)
**Weighting approach**: equal weight per coin (user directive)

## Weighting

8 coins total, each gets 1/8 weight:
- v1 Model A (BTC+ETH pooled): 2/8 = **0.25** (covers 2 coins)
- v1 Model C (LINK): 1/8 = 0.125
- v1 Model D (BNB): 1/8 = 0.125
- v2 Model E (DOGE): 1/8 = 0.125
- v2 Model F (SOL): 1/8 = 0.125
- v2 Model G (XRP): 1/8 = 0.125
- v2 Model H (NEAR): 1/8 = 0.125

## Headline result — v1 has decayed in OOS

| Metric | v1 alone | v2 alone | **Combined (equal-coin)** |
|---|---|---|---|
| IS trade Sharpe | +1.5035 | +1.8041 | **+2.3395** |
| IS monthly Sharpe | +0.9433 | +1.0421 | **+1.3176** |
| **OOS trade Sharpe** | **+0.1250** | **+2.0232** | +1.4119 |
| **OOS monthly Sharpe** | **+0.1187** | **+1.8346** | +0.9919 |
| OOS PF | 1.024 | 1.878 | 1.263 |
| OOS WR | 42.5% | 50.0% | 44.1% |
| OOS trades | 193 | 54 | 247 |

**v1 has significantly decayed** in OOS. BASELINE.md claimed OOS Sharpe +2.83
but fresh run on the extended OOS window gives only +0.13. The 2025-2026
market regime doesn't fit v1's learned patterns.

## Per-symbol OOS contribution (combined, positive-total share)

| Symbol | Track | Trades | WR | Weighted PnL | Share |
|---|---|---|---|---|---|
| NEARUSDT | v2 | 14 | 64.3% | +4.59 | **38.88%** |
| XRPUSDT | v2 | 6 | 66.7% | +3.51 | **29.70%** |
| BTCUSDT | v1 | 42 | 42.9% | +1.51 | 12.80% |
| SOLUSDT | v2 | 18 | 38.9% | +1.48 | 12.56% |
| DOGEUSDT | v2 | 16 | 43.8% | +0.72 | 6.07% |
| ETHUSDT | v1 | 48 | 41.7% | −0.19 | **0%** (net loss) |
| LINKUSDT | v1 | 45 | 46.7% | −0.19 | **0%** (net loss) |
| BNBUSDT | v1 | 58 | 39.7% | −0.41 | **0%** (net loss) |

**Only BTC (12.8%) contributes meaningfully from v1.** ETH, LINK, BNB all
net-negative in weighted_pnl terms. v2's NEAR+XRP (68.6% combined) are
the dominant OOS performers.

## Combined IS is VERY STRONG (+2.34 trade Sharpe)

While OOS combined is worse than v2 alone, IS combined is dramatically better:
- v2 alone IS trade Sharpe: +1.80
- Combined IS trade Sharpe: **+2.34 (+30%)**

This suggests v1 and v2 are truly complementary in IS (different symbols,
different periods where they shine). But v1's OOS decay breaks this in the
current OOS window.

## Alternative: BTC + v2 (drop ETH/LINK/BNB)

Excluding v1's net-negative symbols, 5 coins × 0.2 weight each:

| Metric | v2 alone | **BTC + v2** |
|---|---|---|
| OOS trade Sharpe | +2.023 | **+2.052** (+1%) |
| OOS monthly Sharpe | +1.835 | +1.475 (−20%) |
| OOS PF | 1.878 | 1.683 |
| OOS trades | 54 | 96 |

Only a marginal trade-Sharpe improvement. Monthly Sharpe regresses 20%
because BTC adds more "in-between" months with marginal returns.

## Conclusions

1. **v2 alone is the strongest OOS strategy right now.** +1.83 monthly Sharpe,
   +2.02 trade Sharpe, PF 1.88, WR 50%.

2. **v1 has decayed meaningfully in OOS.** The production model from BASELINE.md
   (OOS Sharpe +2.83) is stale — re-running on the extended OOS window (through
   Apr 2026) gives OOS trade Sharpe only +0.13.

3. **Equal-coin combined portfolio dilutes v2 with weak v1 contributions.**
   Combined OOS monthly Sharpe +0.99 is worse than v2 alone +1.83.

4. **IS view is different**: combined IS trade Sharpe +2.34 is meaningfully
   better than either alone, suggesting the strategies ARE complementary in
   training periods. The IS/OOS gap is what breaks the combined portfolio.

## Recommendations

- **Short term**: v2 alone is the production candidate for new capital.
- **Medium term**: v1 needs its own refresh iteration before combining makes
  sense. Its 2022-2024 training regimes don't generalize to 2025-2026.
- **Long term**: once v1 is refreshed and both strategies have comparable
  OOS Sharpes, the equal-coin combined portfolio could actually improve
  over each alone (because the IS correlation is low and combined IS is
  superlinear).
