# Iteration 136 Engineering Report

**Role**: QE
**Config**: BTC standalone, ATR labeling 3.5×NATR/1.75×NATR, 5-seed ensemble

## Configuration

| Parameter | Value |
|-----------|-------|
| Symbols | BTCUSDT |
| Interval | 8h |
| Training months | 24 |
| Labeling | ATR: TP=3.5×NATR, SL=1.75×NATR |
| Execution | ATR: TP=3.5×NATR, SL=1.75×NATR |
| Timeout | 7 days (10080 min) |
| Features | 196 (auto-discovered, symbol-scoped) |
| Ensemble seeds | [42, 123, 456, 789, 1001] |
| CV | 5 folds, 50 Optuna trials |
| CV gap | 22 rows (22 candles × 1 symbol) |
| Cooldown | 2 candles |
| Runtime | 5895s (~98 min) |

## Results

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | -0.90 | -1.41 |
| Sortino | -0.93 | -1.98 |
| WR | 40.6% | 32.0% |
| PF | 0.75 | 0.65 |
| MaxDD | 140.5% | 46.7% |
| Trades | 170 | 50 |
| Net PnL | -109.3% | -36.4% |

## Exit Reason Breakdown

| | IS | OOS |
|--|-----|-----|
| TP rate | 15.9% (27) | 18.0% (9) |
| SL rate | 52.9% (90) | 64.0% (32) |
| Timeout rate | 31.2% (53) | 18.0% (9) |
| Avg TP PnL | +7.66% | +5.82% |
| Avg SL PnL | -4.67% | -3.21% |
| Avg TO PnL | +1.97% | +1.55% |

## Direction Split (OOS)

- Long: 18 trades (36%)
- Short: 32 trades (64%)
- BTC rallied ~$80K → $120K during OOS period — model was overwhelmingly short

## Gate 3 Assessment

| Gate | Threshold | Result | Pass? |
|------|-----------|--------|-------|
| IS Sharpe > 0 | > 0.0 | -0.90 | **FAIL** |
| IS WR > 33.3% | > 33.3% | 40.6% | PASS |
| IS Trades ≥ 100 | ≥ 100 | 170 | PASS |

**BTC FAILS Gate 3.** IS Sharpe is deeply negative.

## Trade Execution Verification

Sampled 10 trades. Entry prices match close of signal candle. ATR-scaled barriers verified — barrier sizes vary by period:
- Early 2022 (high vol): SL ~5-7.5%, TP ~10-15%
- Late 2025 (low vol): SL ~2-3%, TP ~5-6%

ATR scaling works correctly — barriers adapt to realized volatility. The issue is model signal quality, not execution.

## Label Leakage Audit

- CV gap = 22: timeout_candles = 10080/480 + 1 = 22, × 1 symbol = 22. Verified correct.
- Walk-forward: each month trains only on prior data. Verified.
- No leakage detected.
