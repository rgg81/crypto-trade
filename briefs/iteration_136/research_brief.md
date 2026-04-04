# Iteration 136 Research Brief

**Type**: EXPLOITATION (BTC standalone screening with ATR labeling)
**Model Track**: BTC standalone — potential Model E or Model A replacement
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

- Walk-forward backtest runs on ALL data (IS + OOS) continuously.
- Reporting layer splits trades at the cutoff.
- QR sees OOS results only in Phase 7.

## Motivation

BTC is the weakest component in the A+C+D portfolio (iter 134 baseline):

| Metric | BTC (Model A) | ETH (Model A) | LINK (C) | BNB (D) |
|--------|---------------|----------------|----------|----------|
| OOS WR | 38.5% | 45.5% | 52.4% | 52.0% |
| OOS PnL | +16.8% | +52.1% | +56.0% | +37.7% |
| OOS % of total | 10.3% | 32.0% | 34.4% | 23.2% |
| IS WR | 42.5% | 40.1% | 43.2% | 44.8% |
| IS PnL | +18.8% | +13.7% | +100.5% | +62.1% |

LINK and BNB both use **ATR labeling** (3.5×NATR/1.75×NATR) as standalone models. BTC uses **static labeling** (8%/4%) in a pooled model with ETH. Two differences: (1) labeling method, (2) pooled vs standalone.

**Hypothesis**: BTC's weaker performance is partly due to static labeling not adapting to its volatility regime. ATR labeling scales barriers with realized volatility — during low-vol periods, BTC static 8% TP may be unreachable (timeouts), while during high-vol periods, 4% SL may be hit too easily. ATR labeling would dynamically adjust.

## Research Checklist Categories

### B. Symbol Universe & Architecture

**Architecture decision**: Testing BTC as a standalone model (Option B from the skill framework). Per-symbol models for BTC "failed" in iter 099/109, but those used the OLD pipeline (no ATR labeling, no ensemble, fewer features). LINK and BNB both work as standalone models with the current pipeline — the "dead idea" status applies only to the old configuration.

**What's different now vs iter 099/109**:
- ATR-based labeling (adapts barriers to volatility)
- 5-seed ensemble (reduces seed dependence)
- 185 auto-discovered features (vs fewer, manually selected)
- Established pipeline with verified CV gap

**Sample count**: BTC has ~1,095 candles/year × 2 years training = ~2,190 samples. With 185 features, ratio = 11.8. This is low. However, LINK and BNB have identical sample counts and work. LightGBM's regularization + Optuna tuning handle this.

### E. Trade Pattern Analysis

From iter 134 portfolio data, BTC's weakness pattern:
- IS: 153 trades, 42.5% WR, +18.8% PnL. Above break-even (33.3% for 2:1 TP/SL) but barely profitable per trade (+0.12% avg)
- OOS: 52 trades, 38.5% WR, +16.8% PnL. WR drops 4pp from IS but still above break-even
- BTC generates the fewest IS PnL of any symbol despite having the most liquid market

The 2:1 RR ratio (8%/4%) means break-even at 33.3%. BTC's 38.5% OOS WR has only 5.2pp of headroom. If ATR labeling improves WR by even 3-4pp (matching LINK/BNB levels), BTC's contribution would double.

## Configuration

Matching LINK/BNB standalone template exactly:

| Parameter | Value | Source |
|-----------|-------|--------|
| Symbols | BTCUSDT | Standalone |
| Training months | 24 | Standard |
| Labeling | ATR-based: TP=3.5×NATR, SL=1.75×NATR | LINK/BNB template |
| Execution barriers | ATR-based: TP=3.5×NATR, SL=1.75×NATR | Match labeling |
| Timeout | 7 days (10080 min) | Standard |
| Features | Auto-discovery (symbol-scoped) | Standard |
| Ensemble | 5 seeds [42, 123, 456, 789, 1001] | Standard |
| CV | 5 folds, 50 Optuna trials | Standard |
| CV gap | 22 (22 candles × 1 symbol) | Computed |
| Cooldown | 2 candles | Standard |

## Screening Gates (from skill)

BTC standalone must pass:
1. **Gate 1 — Data quality**: ≥1,095 IS candles, no gaps > 3 days. BTC has data since 2020. PASS (by construction).
2. **Gate 2 — Liquidity**: Mean daily volume > $10M. BTC is the most liquid crypto. PASS (by construction).
3. **Gate 3 — Stand-alone profitability**: IS Sharpe > 0, IS WR > 33.3%, ≥100 IS trades.
4. **Gate 4 — Pooled compatibility**: Not applicable (BTC is already in the portfolio).
5. **Gate 5 — Diversification value**: Not applicable (BTC is already in the portfolio).

For this iteration, we only need Gate 3 to pass. If BTC standalone with ATR labeling beats BTC's current performance within Model A, we can restructure the portfolio in a future iteration.

## Success Criteria

| Metric | Current BTC (in Model A) | Target BTC standalone |
|--------|--------------------------|----------------------|
| IS Sharpe | — (pooled, not separable) | > 0.0 |
| IS WR | 42.5% | > 40% |
| IS Trades | 153 | ≥ 100 |
| OOS WR | 38.5% | > 38.5% (improvement) |
| OOS Trades | 52 | ≥ 30 (screening minimum) |

If BTC standalone IS Sharpe > 0.3 (matching BNB-level signal), this would be a strong candidate for replacing BTC in Model A with a dedicated BTC model.
