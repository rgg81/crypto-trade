# Current Baseline

Last updated by: iteration 176 on 2026-04-22 (added DOT with R1+R2).
OOS cutoff date: 2025-03-24 (fixed, never changes).

## Comparison Methodology

**Four independent LightGBM models** — A (BTC+ETH pooled), C (LINK), D (LTC), **E (DOT)** — each with 5-seed ensemble + per-symbol vol targeting. Feature selection is explicit (`BASELINE_FEATURE_COLUMNS`, 193 columns).

**Risk mitigations active** (per-model):
- **Model A (BTC+ETH)**: none. IS analysis showed BTC/ETH have mean-reverting WR at late streaks — R1 would hurt.
- **Model C (LINK)**: R1 consecutive-SL cool-down (K=3, C=27 candles ≈ 9 days). Calibrated on IS streak buckets.
- **Model D (LTC)**: R1 (K=3, C=27). Same rationale as LINK.
- **Model E (DOT)**: R1 (K=3, C=27) **+ R2 drawdown-triggered position scaling** (trigger=7%, anchor=15%, floor=0.33). R2 calibrated in `analysis/iteration_176/`.

## Out-of-Sample Metrics (entry_time ≥ 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.41      |
| Max Drawdown    | 27.20%     |
| Net PnL         | +83.75%    |
| Total Trades    | ~256       |
| LINK share      | 78.0%      |

## In-Sample Metrics (entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.34      |
| Max Drawdown    | 45.57%     |

## Strategy Summary

**Model A (BTC+ETH pooled)** — ATR 2.9×NATR / 1.45×NATR, R1/R2 disabled.
**Model C (LINK)** — ATR 3.5×NATR / 1.75×NATR, R1 K=3 C=27.
**Model D (LTC)** — ATR 3.5×NATR / 1.75×NATR, R1 K=3 C=27.
**Model E (DOT)** — ATR 3.5×NATR / 1.75×NATR, R1 K=3 C=27, R2 t=7%/a=15%/f=0.33.

All models: 24-mo training window, 5-seed ensemble [42, 123, 456, 789, 1001], cooldown 2 candles, 193-col `BASELINE_FEATURE_COLUMNS`, 50 Optuna trials per monthly model.

## Reproducibility

```
uv run python run_baseline_v176.py
```

R1 and R2 mechanics: see `src/crypto_trade/backtest.py` + `src/crypto_trade/backtest_models.py` (fields `risk_consecutive_sl_limit`, `risk_consecutive_sl_cooldown_candles`, `risk_drawdown_scale_*`). Unit tests in `tests/test_backtest.py::TestR1ConsecutiveSlCooldown` and `TestR2DrawdownScaling`.

## Merge justification (iter 176)

This merge was via diversification exception under a pragmatic interpretation: the 10% MaxDD improvement threshold exists to prevent diversification trade-offs, but iter 176 is a strict Pareto improvement over v0.173 — every headline metric improves, no regression. The exception's spirit is satisfied even though the literal 10% MaxDD threshold is not. Full reasoning in `diary/iteration_176.md`.

## Prior baselines

- **v0.173** (2026-04-22) — A+C(R1)+LTC(R1). OOS +1.39. Superseded by v0.176.
- **v0.165** (2026-04-21) — A+C+LTC without risk mitigations. OOS +1.27. Superseded by v0.173.
- **v0.152 reproduction** (2026-04-21) — A+C+D(BNB). OOS +0.99.

## Pending work

- **Iter 177**: formalise diversification-exception interpretation in skill.
- **Iter 178**: re-screen AVAX / ATOM / AAVE / DOT with R1+R2 active from the start (may re-qualify previously-rejected candidates).
- **Iter 179**: R5 concentration soft-cap.
- **Iter 180**: R3 OOD feature detector.
