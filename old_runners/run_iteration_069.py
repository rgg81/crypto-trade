"""Iter 069: Cooldown value sweep — test cooldown={1, 3, 4} with single seed.

Compare against baseline cooldown=2 from iter 068.
Uses seed=42 only (no ensemble) for faster comparison.
If a value beats cooldown=2, run full ensemble separately.
"""
import sys
import time
from pathlib import Path

from crypto_trade.backtest import EarlyStopError, run_backtest
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.iteration_report import generate_iteration_reports
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

SYMBOLS = ("BTCUSDT", "ETHUSDT")


def run_cooldown(cooldown: int, iteration: int, seed: int = 42, ensemble: bool = False) -> None:
    label = f"cooldown={cooldown}"
    if ensemble:
        label += " (ensemble)"
    print(f"\n{'='*60}")
    print(f"Iter 069: {label}, ATR barriers, BTC+ETH")
    print(f"{'='*60}")

    config = BacktestConfig(
        symbols=SYMBOLS,
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
        data_dir=Path("data"),
        cooldown_candles=cooldown,
    )
    strategy = LightGbmStrategy(
        training_months=24,
        n_trials=50,
        cv_splits=5,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir="data/features",
        seed=seed,
        verbose=1,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        ensemble_seeds=[42, 123, 789] if ensemble else None,
    )
    start = time.time()
    try:
        results = run_backtest(config, strategy, yearly_pnl_check=True)
        elapsed = time.time() - start
        print(f"\nBacktest complete: {len(results)} trades in {elapsed:.0f}s")
    except EarlyStopError as e:
        elapsed = time.time() - start
        results = e.results
        print(f"\n*** EARLY STOP: {e.reason} *** ({elapsed:.0f}s)")

    if not results:
        print("No trades.")
        return
    report_dir = generate_iteration_reports(
        trades=results,
        iteration=iteration,
        features_dir="data/features",
        reports_dir="reports",
        interval="8h",
    )
    print(f"Reports: {report_dir}")


def main() -> None:
    # Sweep: single seed, different cooldown values
    # Use different iteration numbers for report separation
    for cooldown, iteration in [(1, 691), (3, 693), (4, 694)]:
        run_cooldown(cooldown, iteration, seed=42, ensemble=False)

    print("\n\n=== SWEEP COMPLETE ===")
    print("Compare reports/iteration_691 (cd=1), 693 (cd=3), 694 (cd=4)")
    print("Against baseline reports/iteration_068 (cd=2, ensemble)")


if __name__ == "__main__":
    main()
