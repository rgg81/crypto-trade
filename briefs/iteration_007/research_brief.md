# Research Brief: 8H LightGBM Iteration 007

## 0. Data Split & Backtest Approach

- OOS cutoff date: 2025-03-24 (project-level constant)
- IS data only for design decisions; walk-forward on full dataset
- Monthly retraining, 12-month window, reports split at cutoff

## 1. Deep Analysis of Iteration 004 (Current Baseline)

### The Win Rate is Misleading

The headline 32.9% WR includes timeout "wins" (+0.38% avg PnL), which barely contribute. The REAL metric is the **TP rate: 31.6%** of trades hit take-profit (4%), while **64.7% hit stop-loss** (2%). Break-even TP rate at 4%/2% is ~35%. The gap is **3.4pp**, not the 1.1pp the WR suggested.

### Monthly Variance is Extreme

Trade count per month ranges from 99 to 1,766 (18x variance). This means Optuna selects wildly different confidence thresholds each month. Critically: **trade count correlates -0.85 with monthly PnL**. Months where the model trades more (loose threshold) lose more money.

| Period | Trades | WR | PnL |
|--------|--------|-----|-----|
| Mar-Apr 2025 | 803 | 38.8% | +178.8% |
| Jul 2025 | 1,766 | 32.0% | -309.5% |
| Nov-Dec 2025 | 312 | 27.8% | -81.7% |

### The Model IS Profitable on Select Symbols

19 of 50 symbols have OOS WR > 34%. If we traded ONLY the 11 best symbols (WR > 36%): **38.1% WR, +174.1% total PnL — PROFITABLE**. BTC alone: **50.6% WR** (87 trades).

IS data supports this: 8 symbols have IS WR > 33% (BTC 37.7%, ETH 34.9%, LUNA 34.3%, BNB 33.7%, XRP 33.6%, STX 33.4%, FIL 33.2%, TRX 33.2%).

### Direction: Long vs Short

Balanced: Long 41.5% of trades (WR 32.7%), Short 58.5% (WR 33.1%). No directional bias problem.

## 2. Change from Baseline

**Single variable change: asymmetric barriers TP=5%/SL=2% (from symmetric 4%/2%).**

### Why This Specific Change

The core math:
- At TP=4%/SL=2%: break-even TP rate = 2/(4+2) = **33.3%**. Current TP rate: **31.6%**. Gap: **1.7pp**. NOT profitable.
- At TP=5%/SL=2%: break-even TP rate = 2/(5+2) = **28.6%**. Even if TP rate drops to 29-30% (fewer trades reach 5%), we have a **buffer**. Expected per trade at 30% TP rate: 0.30 * 4.9 + 0.70 * (-2.1) = 1.47 - 1.47 = **break-even**.
- At TP=5%/SL=2%: if TP rate holds above 29%, **the strategy is profitable**.

### Why Not Other Changes

- **Reduce symbols**: Would improve WR but doesn't change the break-even math. We're 1.7pp below break-even TP rate — symbol changes alone can't close this gap.
- **Higher confidence threshold**: Already optimized by Optuna. Fixing it higher risks underfitting to good months.
- **More Optuna trials**: Iter 006 proved this doesn't help.

### Risk

Iter 005 showed that LOWER barriers (3%/1.5%) hurt WR. But that changed BOTH TP and SL. Here we only widen TP while keeping SL=2%. The model's SL behavior is unchanged — same stop-loss, same risk. Only the profit target increases. If a trade goes the right direction, it just needs to run a bit further.

### Supporting Evidence

- The EDA showed 78.6% resolution at 5%/2.5% and 87.2% at 4%/2%. At 5%/2% (asymmetric), resolution should be between these.
- Iter 005's failure was at 3%/1.5% — tighter SL (1.5%) meant MORE stop-outs. Here SL stays at 2%.

## 3. Implementation

Change `take_profit_pct=5.0` and `label_tp_pct=5.0` in both `BacktestConfig` and `LightGbmStrategy`. Keep `stop_loss_pct=2.0` and `label_sl_pct=2.0`. Everything else unchanged.
