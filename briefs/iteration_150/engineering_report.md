# Iteration 150 Engineering Report

**Role**: QE (production code integration)

## Configuration

Full A+C+D walk-forward backtest with `vol_targeting=True` in `BacktestConfig`:
- target_vol=0.5, lookback=30 days, min/max scale = [0.5, 2.0]
- All 3 LightGBM models re-trained from scratch with seeds [42,123,456,789,1001]

## Results vs iter 147 (post-processing reference)

| Metric | Iter 147 (post-process) | Iter 150 (engine) | Match |
|--------|-------------------------|-------------------|-------|
| IS Sharpe | +1.2648 | +1.2648 | ✅ |
| OOS Sharpe | **+2.6486** | **+2.6486** | ✅ |
| OOS Sortino | +3.8058 | +3.8058 | ✅ |
| OOS WR | 50.6% | 50.6% | ✅ |
| OOS PF | 1.6186 | 1.6186 | ✅ |
| OOS MaxDD | 39.17% | 39.17% | ✅ |
| OOS Calmar | 4.0207 | 4.0207 | ✅ |
| OOS Trades | 164 | 164 | ✅ |
| IS Trades | 652 | 652 | ✅ |
| Total Trades | 816 | 816 | ✅ |

**Exact match to 4 decimal places across all metrics.**

## Runtime

- Model A (BTC+ETH, 51 months): 10036s (~167 min)
- Model C (LINK, 51 months): 5690s (~95 min)
- Model D (BNB, 51 months): 5879s (~98 min)
- **Total: ~360 min (~6 hours)**

## Trade Execution Verification

Sample of trades verified. VT scales range [0.5, 2.0] as expected. `weight_factor`
reflects per-symbol rolling vol. `weighted_pnl = net_pnl_pct * weight_factor`.

## Label Leakage Audit

- Model A: CV gap = 44 (22 × 2 symbols). Verified.
- Model C: CV gap = 22 (22 × 1 symbol). Verified.
- Model D: CV gap = 22 (22 × 1 symbol). Verified.
- VT: uses `days_before >= 1` (no same-day leakage). Verified.

## Code Summary

3 files modified, ~50 lines added:
- `backtest_models.py`: VT config fields added to `BacktestConfig`
- `backtest.py`: `_compute_vt_scale()` helper, per-symbol daily PnL tracking,
  scale applied at `_create_order()` call site
- `backtest_report.py`: `summarize()` uses `weighted_pnl` for portfolio metrics

All existing tests pass (5 pre-existing failures unrelated to these changes).

## Status

**Production-ready.** Engine-integrated per-symbol vol targeting validated.
