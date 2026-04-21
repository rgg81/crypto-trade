# Current Baseline

Last updated by: reproduction of iteration 152 on 2026-04-21 (data: klines
through 2026-04-20 16:00 UTC; features regenerated from current `main`).
OOS cutoff date: 2025-03-24 (fixed, never changes).

## Comparison Methodology

**Baseline metrics are deterministic** (5-seed ensemble per model + per-symbol vol targeting **integrated into backtest engine**). Feature selection is now **explicit**: every model receives `BASELINE_FEATURE_COLUMNS` (193 columns, declared in `src/crypto_trade/live/models.py`). Auto-discovery is disabled at the code level (`LightGbmStrategy` raises if `feature_columns` is empty).

**Combined portfolio**: Three independent LightGBM models (A=BTC+ETH, C=LINK, D=BNB) running side-by-side. Per-symbol volatility targeting (target_vol=0.3, lookback_days=45, min_scale=0.33, max_scale=2.0) is applied live within the backtest engine.

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +0.99      |
| Sortino         | +1.10      |
| Win Rate        | 39.9%      |
| Profit Factor   | 1.22       |
| Max Drawdown    | 43.78%     |
| Total Trades    | 223        |
| Calmar Ratio    | 1.26       |
| Net PnL         | +55.25%    |
| DSR             | −21.58     |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.07      |
| Sortino         | +1.45      |
| Win Rate        | 42.9%      |
| Profit Factor   | 1.26       |
| Max Drawdown    | 74.42%     |
| Total Trades    | 648        |
| Net PnL         | +195.73%   |
| DSR             | −36.71     |

## Per-Symbol OOS Performance

| Symbol  | Model | Trades | WR    | Net PnL   | % of Total |
|---------|-------|-------:|------:|----------:|-----------:|
| LINKUSDT | C    | 49     | 51.0% | +87.37%   | 112.88%    |
| ETHUSDT  | A    | 59     | 40.7% | +19.80%   | 25.58%     |
| BTCUSDT  | A    | 51     | 33.3% | −5.28%    | −6.82%     |
| BNBUSDT  | D    | 64     | 35.9% | −24.49%   | −31.64%    |

## Per-Symbol IS Performance

| Symbol  | Model | Trades | WR    | Net PnL   | % of Total |
|---------|-------|-------:|------:|----------:|-----------:|
| ETHUSDT  | A    | 194    | 41.2% | +73.56%   | 29.70%     |
| BTCUSDT  | A    | 125    | 46.4% | +68.98%   | 27.85%     |
| LINKUSDT | C    | 179    | 41.3% | +54.14%   | 21.86%     |
| BNBUSDT  | D    | 150    | 44.0% | +51.02%   | 20.60%     |

## Strategy Summary

**Model A (BTC+ETH pooled)** — `BASELINE_FEATURE_COLUMNS` (193), ATR labeling 2.9×NATR / 1.45×NATR, 24-mo training

**Model C (LINK)** — `BASELINE_FEATURE_COLUMNS` (193), ATR labeling 3.5×NATR / 1.75×NATR, 24-mo training

**Model D (BNB)** — `BASELINE_FEATURE_COLUMNS` (193), ATR labeling 3.5×NATR / 1.75×NATR, 24-mo training

All models: timeout 7 days, 5-seed ensemble [42, 123, 456, 789, 1001], cooldown 2 candles, CV gap = (timeout_candles + 1) × n_symbols, 50 Optuna trials per monthly model, `seed=42` in the per-model constructor.

## Notes — reproduction vs historical

The historical iter-152 row (OOS Sharpe +2.83, WR 50.6%, 164 trades) was not
reproducible with current code. Today's rerun uses identical config (seed,
VT params, ensemble seeds, ATR multipliers, timeout, cooldown, feature list)
and the same Parquet feature values for the 204 columns that exist in both
schemas — yet produces different OOS trades. Most likely cause:

- **Forming-candle CSV fix (iter-150 era)** rewrote the last 3-4 candles of
  each symbol's CSV with real closes instead of mid-candle snapshots. Any
  model month that used those candles as training inputs now trains on
  slightly different numbers.
- **VT engine integration (iter-150)** is verified exact-equivalent to iter-147
  post-processing on the trades iter-150 produced, but the *trade list itself*
  depends on the Parquet feature values that have since been regenerated.
- 30% more OOS trades than iter-138 (213 vs 164 in the same pre-2026-04-06 window)
  indicates systematic signal change, not just data-tail extension.

This baseline is the new floor for comparison. All future iterations are
measured against **OOS Sharpe +0.99**.
