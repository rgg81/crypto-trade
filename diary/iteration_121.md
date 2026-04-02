# Iteration 121 Diary

**Date**: 2026-04-02
**Type**: EXPLOITATION (portfolio allocation weighting)
**Model Track**: Combined portfolio (BTC/ETH + DOGE/SHIB)
**Decision**: **NO-MERGE** — marginal improvement (~4% Sharpe), not worth the complexity

## Hypothesis

Sharpe-weighted capital allocation (1.2x BTC/ETH, 0.8x DOGE/SHIB) should improve combined portfolio Sharpe by reducing the variance contribution of the more volatile meme model.

## Methodology

Since the underlying models are identical to iter 119 (same configs, same seeds), the trades are deterministic. The only change is post-hoc `weighted_pnl` scaling via `dataclasses.replace()`. This allowed analytical preview using iter 119's existing trades.csv before the backtest completed.

### Key Discovery: `max_amount_usd` Does NOT Affect Sharpe

Investigation of `backtest.py:411-454` revealed that `max_amount_usd` only flows into `Order.amount_usd` (stored but unused in PnL). The `weight_factor` comes from `signal.weight / 100`, not position sizing. Portfolio-level allocation requires explicit `weighted_pnl` scaling after the backtest.

## Analytical Results (from iter 119 trades, reweighted)

### OOS Sharpe Sensitivity to Allocation Weights

| A (BTC/ETH) | B (DOGE/SHIB) | OOS Sharpe | OOS PnL | Daily Std |
|-------------|---------------|------------|---------|-----------|
| 1.0 | 1.0 | 1.4539 | 315.0% | 10.121 |
| 1.0 | 1.0 | 1.9026 | 100.2% | 7.681 |
| 1.1 | 0.9 | 1.9534 | 100.4% | 7.496 |
| **1.2** | **0.8** | **1.9863** | **100.6%** | **7.387** |
| 1.3 | 0.7 | 1.9985 | 100.8% | 7.356 |
| 1.5 | 0.5 | 1.9593 | 101.2% | 7.533 |

(First row is IS, remaining are OOS with different methods)

### IS/OOS Ratios

| Weights | IS Sharpe | OOS Sharpe | Ratio |
|---------|-----------|------------|-------|
| 1.0/1.0 | 1.4539 | 1.9026 | 0.76 |
| 1.2/0.8 | 1.5071 | 1.9863 | 0.76 |
| 1.3/0.7 | 1.5151 | 1.9985 | 0.76 |

Note: These Sharpe numbers differ from comparison.csv (1.18) because of different annualization methods (calendar days vs trading days). The RELATIVE changes are what matter.

## Why NO-MERGE

1. **Marginal improvement**: 1.2/0.8 weighting improves OOS Sharpe by ~4.4%. The optimal (1.3/0.7) improves by ~5.0%. This is within noise.
2. **No signal improvement**: Same trades, same WR, same PnL. The Sharpe improvement comes entirely from reducing daily variance by 3.8%. This is portfolio engineering, not alpha generation.
3. **Complexity for no payoff**: Adding portfolio weights complicates the runner without meaningful Sharpe improvement. The time is better spent on signal quality.
4. **Diminishing returns**: Beyond 1.3/0.7, Sharpe declines — the BTC/ETH model's own negative contributors (BTC -2.7% OOS) get amplified. The "optimal" weight depends on the OOS period, making this curve-fitting at the portfolio level.

## What We Learned

1. **Portfolio-level weighting is a second-order effect.** With 2 models producing ~same PnL (BTC/ETH +51.1% vs DOGE/SHIB +49.1%), reweighting moves ~0.4% of total PnL while reducing daily std by 3.8%. The Sharpe improvement is real but trivial.
2. **Signal quality dominates allocation.** To meaningfully improve the combined Sharpe, we need either: (a) a better meme model (DOGE profitable, SHIB even stronger), or (b) an entirely different third model with decorrelated returns.
3. **The `max_amount_usd` parameter is cosmetic for Sharpe.** It affects dollar PnL but not the Sharpe/Sortino metrics used for evaluation. Portfolio weighting requires explicit `weighted_pnl` scaling.
4. **5-seed ensemble × 2 models × monthly walk-forward = ~170 Optuna studies = 2+ hours.** Future iterations that change only post-processing should use analytical preview on cached trades instead of full re-runs.

## Hard Constraints (from analytical preview)

| Constraint | Threshold | Iter 121 | Pass? |
|------------|-----------|----------|-------|
| OOS Sharpe > baseline | > +1.18 | ~+1.24 | MARGINAL |
| OOS MaxDD ≤ 1.2 × baseline | ≤ 55.6% | ~44% | PASS |
| OOS Trades ≥ 50 | ≥ 50 | 188 | PASS |
| OOS PF > 1.0 | > 1.0 | ~1.24 | PASS |
| Symbol concentration ≤ 30% | ≤ 30% | SHIB ~53% | FAIL |
| IS/OOS Sharpe ratio > 0.5 | > 0.5 | ~0.76 | PASS |

## Label Leakage Audit

No code changes. Both models use identical configs to iter 119. CV gap = 44 rows verified.

## lgbm.py Code Review

No code changes in this iteration.

## Gap Quantification

Combined OOS WR 43.6%, break-even 33.3%, gap +10.3pp. TP rate 27.7%, SL rate 51.6%.

To close the remaining gap to a meaningful Sharpe improvement:
- **Fix DOGE** (37.5% WR → 45%+) — this alone would add ~+10-15% OOS PnL
- **Fix BTC** (33.3% WR → 38%+) — barely at break-even, any improvement helps
- **Add a fifth symbol** with OOS WR > 45% and decorrelated returns

## Exploration/Exploitation Tracker

Last 10 iterations: [E, X, E, E, E, X, E, X, X, **X**] (iters 112-121)
Exploration rate: 5/10 = 50%
This iteration: EXPLOITATION (portfolio weighting)

## Research Checklist

- **B** (symbols/diversification): Portfolio allocation optimization analysis
- **E** (trade patterns): Per-model PnL contribution under different weighting scenarios

## Next Iteration Ideas

1. **Entropy features for meme model (EXPLORATION)** — Shannon entropy of discretized returns over rolling 50-candle window. Add `stat_shannon_entropy_50` to the 45 meme features. High entropy = noisy market → model should trade less. Genuinely novel signal not captured by existing volatility features. Replace `stat_skew_10` (lowest importance in meme model).

2. **CUSUM structural break features (EXPLORATION)** — `struct_cusum_break_5` (CUSUM exceeded 2-sigma in last 5 candles), `struct_candles_since_break`. Add to BOTH models. These capture regime changes that the current trend/momentum features miss.

3. **Narrower meme barriers (EXPLOITATION)** — Reduce meme model from 3.5x/1.75x to 3.0x/1.5x. DOGE's wider barriers amplify losses. Tighter barriers reduce avg SL loss while maintaining TP opportunity. This does NOT require per-symbol code — just change the multiplier for the whole meme model.

4. **BTC/ETH feature refresh (EXPLORATION)** — The BTC/ETH model has used the same 185 auto-discovered features since iter 093 (frozen). Run feature importance on IS data, identify the bottom 50 by MDI gain, and see if replacing them with meme-model-proven features (like `meme_body_ratio`, `meme_taker_imbalance`) improves BTC/ETH performance.
