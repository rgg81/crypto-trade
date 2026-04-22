# Current Baseline

Last updated by: iteration 173 on 2026-04-22 (R1 consecutive-SL cool-down on LINK+LTC).
OOS cutoff date: 2025-03-24 (fixed, never changes).

## Comparison Methodology

**Baseline metrics are deterministic** (5-seed ensemble per model + per-symbol vol targeting + Risk Mitigation R1 on LINK and LTC). Feature selection is **explicit**: every model receives `BASELINE_FEATURE_COLUMNS` (193 columns, declared in `src/crypto_trade/live/models.py`). Auto-discovery is disabled at the code level (`LightGbmStrategy` raises if `feature_columns` is empty).

**Combined portfolio**: Three independent LightGBM models — **A=BTC+ETH, C=LINK, D=LTC** — running side-by-side. Per-symbol volatility targeting (target_vol=0.3, lookback_days=45, min_scale=0.33, max_scale=2.0) applied within the backtest engine. **R1 consecutive-SL cool-down** (K=3, C=27 candles = 9 days) applied to Model C (LINK) and Model D (LTC). R1 is NOT applied to Model A (BTC+ETH) because their IS streak analysis showed mean-reverting WR patterns at late streaks — R1 would have hurt them.

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.39      |
| Win Rate        | ~42%       |
| Profit Factor   | ~1.35      |
| Max Drawdown    | 27.74%     |
| Total Trades    | ~195       |
| Net PnL         | +78.65%    |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.30      |
| Max Drawdown    | 45.57%     |
| Net PnL         | +227.45%   |

## Strategy Summary

**Model A (BTC+ETH pooled)** — `BASELINE_FEATURE_COLUMNS` (193), ATR labeling 2.9×NATR / 1.45×NATR, 24-mo training, **R1 disabled**.

**Model C (LINK)** — `BASELINE_FEATURE_COLUMNS` (193), ATR labeling 3.5×NATR / 1.75×NATR, 24-mo training, **R1 K=3 C=27**.

**Model D (LTC)** — `BASELINE_FEATURE_COLUMNS` (193), ATR labeling 3.5×NATR / 1.75×NATR, 24-mo training, **R1 K=3 C=27**.

All models: timeout 7 days, 5-seed ensemble [42, 123, 456, 789, 1001], cooldown 2 candles, CV gap = (timeout_candles + 1) × n_symbols, 50 Optuna trials per monthly model.

## Reproducibility

```
uv run python run_baseline_v173.py
```

## R1 Risk Mitigation (iter 173)

When a symbol takes 3 consecutive stop-loss exits (K=3), the backtest engine suppresses new trades on that symbol for 27 candles (9 days, C=27). The streak resets on any non-SL exit (take_profit or timeout) or when the cool-down arms.

**Evidence for K=3, C=27 on LINK+LTC** (IS data only):

| Symbol | streak=0 WR | streak=3 WR | R1 justified? |
|--------|------------:|------------:|---------------|
| BTC    | 43.9%       | 57.1%       | No — mean-reverting |
| ETH    | 42.0%       | 56.2%       | No — mean-reverting |
| LINK   | 44.0%       | **27.3%**   | Yes (drop 16.7 pp) |
| LTC    | 41.0%       | **16.7%**   | Yes (drop 24.3 pp) |

See `briefs/iteration_173/research_brief.md` for the full analysis.

## Prior baselines

- **v0.165** — A+C+LTC without R1. OOS Sharpe +1.27, MaxDD 30.56%. Replaced by v0.173.
- **v0.152 reproduction** — A+C+D(BNB). OOS Sharpe +0.99, MaxDD 43.78%. Replaced by v0.165 when BNB was swapped for LTC.
- **Historical v0.152 (pre-2026-04-21)** — claimed OOS Sharpe +2.83. Not reproducible with current code + data state.

## Pending Work

- **Iter 174**: Revisit DOT as a 4th portfolio candidate against the new v0.173 baseline. DOT with R1 may now qualify given the improved MaxDD baseline.
- **Iter 175+**: R2 (drawdown-triggered position scaling), R3 (OOD feature detection), R4 (vol kill-switch), R5 (concentration soft-cap). See skill's Risk Mitigation section.
- **Iter 176**: Extend the live engine to honour `risk_consecutive_sl_limit` for paper/live trading consistency with the backtest.
