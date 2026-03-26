# Research Brief: 8H LightGBM Iteration 011

## 0. Data Split
- OOS cutoff: 2025-03-24. IS only for design. Walk-forward on full dataset.

## 1. Change: Expand to Top 5 Symbols
From BTC+ETH (iter 010) to BTC+ETH+SOL+XRP+DOGE.

### Evidence (IS data, iter 004)
- BTC: IS WR 37.7%, OOS 50.6% (87 trades)
- ETH: IS WR 34.9%, OOS 39.2% (143 trades)  
- SOL: IS WR 29.5% (below break-even)
- XRP: IS WR 33.6% (near break-even)
- DOGE: IS WR 31.0% (below break-even)

### Risk
SOL, DOGE are below IS break-even. Adding them may dilute BTC/ETH signal. But they're the 3 most liquid alts and with only 5 symbols, the model stays focused.

### Research Checklist (E: Trade Patterns)
From iter 010 OOS: 487 trades over 11 months (~44/month). Expanding to 5 symbols should roughly triple trade count while maintaining quality on BTC/ETH.

## 2. Everything Else Unchanged
Classification, TP=4%/SL=2%, confidence 0.50-0.65, 50 Optuna trials, seed 42.
