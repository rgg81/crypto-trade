# Iteration 137 Engineering Report

**Role**: QE
**Config**: Model A (BTC+ETH pooled) with ATR labeling 2.9×NATR/1.45×NATR

## Configuration

| Parameter | Baseline Model A | Iter 137 |
|-----------|-----------------|----------|
| Symbols | BTCUSDT + ETHUSDT | Same |
| Labeling | Static TP=8%, SL=4% | **ATR: TP=2.9×NATR, SL=1.45×NATR** |
| Execution | ATR: 2.9×/1.45× | Same |
| use_atr_labeling | False | **True** |
| Training months | 24 | Same |
| Timeout | 7 days | Same |
| Features | 196 (auto-discovered) | Same |
| Ensemble | 5 seeds | Same |
| CV gap | 44 (22 × 2 symbols) | Same |
| Cooldown | 2 | Same |
| Runtime | — | 9888s (~165 min) |

## Results

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | +1.14 | **+1.67** |
| Sortino | +1.57 | +1.70 |
| WR | 45.1% | **48.6%** |
| PF | 1.33 | **1.60** |
| MaxDD | 49.2% | **19.8%** |
| Trades | 326 | 72 |
| Calmar | 4.35 | 3.97 |
| Net PnL | +213.9% | +78.7% |

## Per-Symbol Comparison (OOS)

| Symbol | Baseline WR | Iter 137 WR | Baseline PnL | Iter 137 PnL |
|--------|-------------|-------------|--------------|--------------|
| BTCUSDT | 38.5% (52 trades) | **42.1%** (38 trades) | +16.8% | +18.5% |
| ETHUSDT | 45.5% (55 trades) | **55.9%** (34 trades) | +52.1% | +60.2% |
| Combined | 41.1% (107 trades) | **48.6%** (72 trades) | +68.9% | +78.7% |

ETH improved dramatically: +10.4pp WR, +8.1% PnL. BTC improved modestly: +3.6pp WR, +1.7% PnL.

## Exit Reason Analysis

| | IS | OOS |
|--|-----|-----|
| TP rate | 32.5% (106) | 33.3% (24) |
| SL rate | 48.8% (159) | 47.2% (34) |
| Timeout rate | 18.7% (61) | 16.7% (12) |
| Avg TP PnL | +7.00% | +7.68% |
| Avg SL PnL | -3.91% | -3.71% |
| Avg TO PnL | +1.53% | +1.98% |
| Effective RR | 1.79:1 | 2.07:1 |

OOS effective RR is 2.07:1 — excellent. The ATR-scaled barriers create more favorable risk-reward.

## Why ATR Labeling Improves Model A

1. **ETH's SL was too tight with static labeling**: With static 4% SL and ETH NATR ~3.5%, the SL was only 1.14× NATR — easily triggered by noise. ATR labeling gives SL = 1.45×NATR = ~5.1% for ETH, providing adequate breathing room.

2. **BTC's barriers were already close to ATR-equivalent**: BTC NATR ~2.5%, so static 8%/4% = 3.2×/1.6× NATR. ATR labeling gives 2.9×/1.45× — slightly tighter. The modest BTC improvement suggests BTC was already near-optimal with static barriers.

3. **Label consistency across regimes**: ATR labeling ensures that a "profitable trade" means the same thing in high-vol and low-vol periods. In a 5% NATR period, TP=14.5% is appropriately ambitious. In a 2% NATR period, TP=5.8% is achievable.

## Trade Execution Verification

Sampled 15 trades across IS and OOS. Verified:
- Entry prices match close of signal candle
- ATR-scaled barriers: TP = entry × (1 ± ATR × 2.9), SL = entry × (1 ∓ ATR × 1.45)
- PnL calculations correct
- No anomalies detected

## Label Leakage Audit

- CV gap = 44 (22 candles × 2 symbols). Verified in training logs.
- Walk-forward: training windows use only prior month data. Verified.
- No leakage detected.

## Trade Count Reduction

OOS trades dropped from 107 (baseline) to 72 (iter 137). ATR labeling produces wider barriers during high-volatility periods, which raises the bar for Optuna's confidence threshold. The model selects fewer but higher-quality trades. This is a net positive — quality over quantity.
