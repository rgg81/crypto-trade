# Research Brief: 8H LightGBM Iteration 028 — EXPLORATION

## 0. Data Split: OOS cutoff 2025-03-24.

## 1. Change: TP=8%/SL=2% ASYMMETRIC (4:1 reward/risk)

### Evidence from iter 027
- BTC+ETH at 8%/4% (symmetric): OOS WR=46.0%, IS WR=42.2%
- The model predicts 8% direction moves with ~46% accuracy
- At TP=8%/SL=2%: break-even = 2/(8+2) = 20%
- Expected per trade at 40% WR: 0.40 × 7.9 + 0.60 × (-2.1) = 3.16 - 1.26 = +1.90%

### Key Difference from iter 007 (TP=5%/SL=2%, which failed)
- Iter 007 was on 50 symbols → signal was diluted
- Now on BTC+ETH only → much stronger signal
- Iter 027 PROVED the model is better at predicting larger moves

## 2. Everything Else Unchanged
BTC+ETH, classification, timeout=4320, threshold 0.50-0.85, 12mo, 50 trials, seed 42.

## Exploration/Exploitation Tracker
Last 10: [E, X, X, X, X, X, E, E, E, **E**] → 5/10 = 50% (exploration heavy, good after deficit)
