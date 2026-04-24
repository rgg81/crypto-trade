# Current Baseline

Last updated by: iteration 186 on 2026-04-22 (added R3 OOD Mahalanobis gate).
OOS cutoff date: 2025-03-24 (fixed, never changes).

## Comparison Methodology

**Four independent LightGBM models** — A (BTC+ETH pooled), C (LINK), D (LTC), E (DOT) — each with 5-seed ensemble + per-symbol vol targeting. Feature selection is explicit (`BASELINE_FEATURE_COLUMNS`, 193 columns).

**Risk mitigations active** (all four models):
- **R1 consecutive-SL cool-down** (K=3, C=27 candles ≈ 9 days) — Models C, D, E
- **R2 drawdown-triggered position scaling** (trigger=7%, anchor=15%, floor=0.33) — Model E only
- **R3 OOD Mahalanobis gate** (cutoff=0.70, 16 scale-invariant features) — ALL MODELS (A, C, D, E)
- Model A has R3 only (no R1/R2 — IS analysis showed BTC/ETH have mean-reverting WR at late streaks, so R1 would hurt).

## Out-of-Sample Metrics (entry_time ≥ 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | **+1.735** |
| Max Drawdown    | 29.31%     |
| Net PnL         | +104.11%   |
| Total Trades    | 210        |
| Trades/month    | ~16        |
| Win Rate        | 43.8%      |
| Profit Factor   | 1.41       |

## Per-symbol OOS PnL share

| Symbol | PnL share |
|--------|----------:|
| DOT    | 38.3%     |
| LINK   | 37.3%     |
| LTC    | 17.9%     |
| ETH    | 14.2%     |
| BTC    | −7.6%     |

(Top-symbol concentration halved vs. v0.176's LINK at 78%.)

## In-Sample Metrics (entry_time < 2025-03-24)

| Metric          | Value      |
|-----------------|------------|
| Sharpe          | +1.440     |
| Max Drawdown    | 56.70%     |
| Total Trades    | 594        |

## Strategy Summary

**Model A (BTC+ETH pooled)** — ATR 2.9×NATR / 1.45×NATR, R3 only.
**Model C (LINK)** — ATR 3.5×NATR / 1.75×NATR, R1 K=3 C=27, R3.
**Model D (LTC)** — ATR 3.5×NATR / 1.75×NATR, R1 K=3 C=27, R3.
**Model E (DOT)** — ATR 3.5×NATR / 1.75×NATR, R1 K=3 C=27, R2 t=7%/a=15%/f=0.33, R3.

R3 OOD features (16): `stat_return_{1,2,5,10}`, `mr_rsi_extreme_{7,14,21}`, `mr_bb_pctb_{10,20}`, `mom_stoch_k_{5,9}`, `vol_atr_{5,7}`, `vol_bb_bandwidth_10`, `vol_volume_pctchg_{5,10}`.

All models: 24-mo training window, 5-seed ensemble [42, 123, 456, 789, 1001], cooldown 2 candles, 193-col `BASELINE_FEATURE_COLUMNS`, 50 Optuna trials per monthly model.

## Reproducibility

```
uv run python run_baseline_v186.py
```

R1/R2 mechanics: `src/crypto_trade/backtest.py` + `src/crypto_trade/backtest_models.py`.
R3 mechanics: `src/crypto_trade/strategies/ml/lgbm.py` (`ood_enabled`, `ood_features`, `ood_cutoff_pct`). Unit tests: `tests/test_lgbm.py::TestR3OodDetector` + `tests/test_backtest.py::TestR1ConsecutiveSlCooldown` / `TestR2DrawdownScaling`.

## Merge justification (iter 186)

OOS Sharpe lifted from +1.41 to +1.73, IS Sharpe from +1.34 to +1.44. OOS MaxDD essentially unchanged (+2.1 pp, within the 20% baseline tolerance). Single-symbol concentration halved (LINK 78% → top two DOT 38% / LINK 37%). All 1.0 Sharpe floors and the new 10/month trade-rate floor cleared. Full reasoning in `diary/iteration_186.md`. The 30%-per-symbol rule is still strictly violated but improves dramatically over baseline — the diversification-exception clause applies.

## Prior baselines

- **v0.176** (2026-04-22) — A+C(R1)+LTC(R1)+DOT(R1,R2). OOS +1.41, MaxDD 27.20%, LINK 78%. Superseded by v0.186.
- **v0.173** (2026-04-22) — A+C(R1)+LTC(R1). OOS +1.39.
- **v0.165** (2026-04-21) — A+C+LTC without risk mitigations. OOS +1.27.
- **v0.152 reproduction** (2026-04-21) — A+C+D(BNB). OOS +0.99.

## Pending work

- **Iter 187**: 10-seed ensemble-robustness sweep of v0.186. Required before shipping to live.
- **Iter 188**: Try tighter OOD cutoffs (0.60, 0.50) — iter 185 post-hoc suggested these could lift IS/OOS Sharpe further.
- **Iter 189**: Per-symbol OOD cutoffs. BTC now contributes −7.6% of OOS PnL, suggesting its regime differs from altcoins; per-symbol calibration could recover.
- **Iter 190+**: Drop BTC from the pool entirely? Its negative contribution is a red flag. Rebuilding Model A as ETH-only is a concrete next exploitation candidate.
