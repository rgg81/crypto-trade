"""Seed sweep for iter 047: 5 seeds."""
import sys, time
from pathlib import Path
from crypto_trade.backtest import run_backtest, EarlyStopError
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy
from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.iteration_report import _compute_metrics

SYMBOLS = ("BTCUSDT", "ETHUSDT")
SEEDS = [42, 123, 456, 789, 1001]

def run_seed(seed):
    config = BacktestConfig(
        symbols=SYMBOLS, interval="8h", max_amount_usd=1000.0,
        stop_loss_pct=4.0, take_profit_pct=8.0, timeout_minutes=10080,
        fee_pct=0.1, data_dir=Path("data"),
    )
    strategy = LightGbmStrategy(
        training_months=24, n_trials=50, cv_splits=5,
        label_tp_pct=8.0, label_sl_pct=4.0, label_timeout_minutes=10080,
        fee_pct=0.1, features_dir="data/features", seed=seed, verbose=0,
    )
    try:
        results = run_backtest(config, strategy, yearly_pnl_check=True)
        return list(results)
    except EarlyStopError as e:
        return e.results

def main():
    print("=== SEED SWEEP (5 seeds): Iter 047 config ===\n")
    all_oos = []
    all_is = []
    
    for seed in SEEDS:
        start = time.time()
        print(f"Seed {seed}...", end=" ", flush=True)
        trades = run_seed(seed)
        elapsed = time.time() - start
        
        is_trades = [t for t in trades if t.open_time < OOS_CUTOFF_MS]
        oos_trades = [t for t in trades if t.open_time >= OOS_CUTOFF_MS]
        
        is_m = _compute_metrics(is_trades)
        oos_m = _compute_metrics(oos_trades)
        
        is_s = is_m.sharpe if is_m else -99
        oos_s = oos_m.sharpe if oos_m else -99
        is_wr = is_m.win_rate if is_m else 0
        oos_wr = oos_m.win_rate if oos_m else 0
        
        all_oos.append(oos_s)
        all_is.append(is_s)
        
        print(f"IS={is_s:+.2f} (WR={is_wr:.1f}%) | OOS={oos_s:+.2f} (WR={oos_wr:.1f}%) | "
              f"{len(trades)} trades | {elapsed:.0f}s")
    
    import numpy as np
    oos_arr = np.array(all_oos)
    is_arr = np.array(all_is)
    oos_pos = (oos_arr > 0).sum()
    
    print(f"\n=== RESULT ===")
    print(f"OOS Sharpe: mean={oos_arr.mean():+.2f} std={oos_arr.std():.2f} positive={oos_pos}/5")
    print(f"IS Sharpe:  mean={is_arr.mean():+.2f} std={is_arr.std():.2f}")
    if oos_arr.mean() > 0 and oos_pos >= 4:
        print(f"PASSES — ready to merge!")
    else:
        print(f"FAILS")

if __name__ == "__main__":
    main()
