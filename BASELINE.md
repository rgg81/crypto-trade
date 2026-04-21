# Current Baseline

Last updated by: iteration 165 on 2026-04-21 (LTC replaces BNB as Model D).
OOS cutoff date: 2025-03-24 (fixed, never changes).

## Comparison Methodology

**Baseline metrics are deterministic** (5-seed ensemble per model + per-symbol vol targeting **integrated into backtest engine**). Feature selection is **explicit**: every model receives `BASELINE_FEATURE_COLUMNS` (193 columns, declared in `src/crypto_trade/live/models.py`). Auto-discovery is disabled at the code level (`LightGbmStrategy` raises if `feature_columns` is empty).

**Combined portfolio**: Three independent LightGBM models — **A=BTC+ETH, C=LINK, D=LTC** — running side-by-side. Per-symbol volatility targeting (target_vol=0.3, lookback_days=45, min_scale=0.33, max_scale=2.0) is applied live within the backtest engine.

**Derivation**: The A+C trades come from the iter-152 baseline reproduction on 2026-04-21. The LTC trades come from iter 165's stand-alone backtest. Because each model is independent (different symbols, per-symbol VT, no cross-model constraints), the portfolio metrics below equal what a fresh `run_baseline_v166.py` (with Model D = LTC) would produce, modulo seed effects — formal seed robustness is pending in iter 166.

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.27      |
| Win Rate        | 40.6%      |
| Profit Factor   | 1.31       |
| Max Drawdown    | 30.56%     |
| Total Trades    | 202        |
| Net PnL         | +73.64%    |

## In-Sample Metrics (trades with entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.08      |
| Win Rate        | 43.6%      |
| Profit Factor   | 1.24       |
| Max Drawdown    | 55.70%     |
| Total Trades    | 653        |
| Net PnL         | +194.73%   |

## Per-Symbol OOS Performance

| Symbol   | Model | Trades | WR    | Net PnL (weighted) | % of Total |
|----------|-------|-------:|------:|-------------------:|-----------:|
| LINKUSDT | C     | 49     | 51.0% | +57.04%            | 77.5%      |
| LTCUSDT  | D     | 43     | 37.2% | +7.29%             | 9.9%       |
| BTCUSDT  | A     | 51     | 33.3% | +7.21%             | 9.8%       |
| ETHUSDT  | A     | 59     | 40.7% | +2.10%             | 2.8%       |

## Strategy Summary

**Model A (BTC+ETH pooled)** — `BASELINE_FEATURE_COLUMNS` (193), ATR labeling 2.9×NATR / 1.45×NATR, 24-mo training

**Model C (LINK)** — `BASELINE_FEATURE_COLUMNS` (193), ATR labeling 3.5×NATR / 1.75×NATR, 24-mo training

**Model D (LTC)** — `BASELINE_FEATURE_COLUMNS` (193), ATR labeling 3.5×NATR / 1.75×NATR, 24-mo training

All models: timeout 7 days, 5-seed ensemble [42, 123, 456, 789, 1001], cooldown 2 candles, CV gap = (timeout_candles + 1) × n_symbols, 50 Optuna trials per monthly model, `seed=42` in the per-model constructor.

## Merge Justification (diversification exception, iter 165)

Concentration constraint (single symbol ≤ 30% of OOS PnL) still fails: LINK contributes 77.5% of OOS PnL. The diversification exception in the skill was invoked because:
- OOS Sharpe far exceeds baseline × 0.95 (1.27 vs 0.94)
- OOS MaxDD improves by 30% (well over the 10% threshold)
- Concentration moves toward the target (112.88% → 77.5%, −35 pp)
- All other hard constraints pass

Future iterations should continue to diversify (e.g., iter 167 = screen ATOM) until the 30% constraint can be met without the exception.

## Pending Work

- **Iter 166**: seed robustness validation for Model D (LTC). Run outer seeds 123, 456, 789, 1001. Confirm mean OOS Sharpe > 0 with ≥ 4 of 5 seeds profitable.
- **Iter 167+**: continue universe expansion (ATOM, DOT) while respecting user exclusions (DOGE, SOL, XRP, NEAR).

## Notes — earlier historical baselines

The previous baseline v0.152 claimed OOS Sharpe +2.83, not reproducible with current code + data state. Iter-152 reproduction on 2026-04-21 produced +0.99, which was the floor iter 165 improved to +1.27. Any pre-2026-04-21 BASELINE.md entries should be treated as historical, not reproducible targets.
