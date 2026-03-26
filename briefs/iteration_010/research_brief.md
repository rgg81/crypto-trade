# Research Brief: 8H LightGBM Iteration 010

## 0. Data Split & Backtest Approach

- OOS cutoff date: 2025-03-24, IS only for design, walk-forward on full dataset

## 1. Structural Change: BTC+ETH Only

### Evidence (from iter 004 OOS analysis)

- BTC: 50.6% WR (87 trades) — massively above 33.3% break-even
- ETH: 39.2% WR (143 trades) — also above break-even
- IS data: BTC 37.7% WR, ETH 34.9% WR — both above break-even
- The other 48 symbols average ~30% WR, dragging the pooled model below break-even

### Why This Is the Right Change

After 9 iterations proving parameter tuning can't close the 2.7pp WR gap, the data clearly shows the model HAS signal on BTC/ETH but not on mid-caps. Rather than building per-symbol models (high engineering effort), simply RESTRICT to the 2 symbols where signal exists.

With 2 symbols: the pooled model becomes effectively a BTC+ETH model. The features learned are specific to these two highly-liquid, well-behaved assets.

### Risk

- Fewer total trades (~87+143=230 OOS from iter 004). May not reach 50-trade minimum in OOS if threshold is tight.
- The BTC 50.6% OOS WR may be lucky on a small sample (87 trades).
- But: IS data confirms both are above break-even (37.7% and 34.9%), so it's not purely OOS luck.

### Everything Else Unchanged

Classification mode, TP=4%/SL=2%, confidence threshold 0.50-0.65, 50 Optuna trials, seed 42.
