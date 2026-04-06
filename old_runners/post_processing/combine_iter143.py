"""Combine existing trades from iter 138 (A+C+D) + iter 142 DOGE into iter 143 reports.

Instead of re-running 4 models (~30h), use deterministic trade outputs:
- iter 138: Model A (BTC+ETH ATR) + Model C (LINK) + Model D (BNB)
- iter 142: Model E (DOGE)

All configs are identical and runs are deterministic, so combining trades is equivalent
to running iter 143 fresh.
"""

import csv
from pathlib import Path

from crypto_trade.backtest_models import TradeResult
from crypto_trade.iteration_report import generate_iteration_reports


def load_trades(csv_path: Path) -> list[TradeResult]:
    trades = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            trades.append(TradeResult(
                symbol=row["symbol"],
                direction=int(row["direction"]),
                entry_price=float(row["entry_price"]),
                exit_price=float(row["exit_price"]),
                weight_factor=float(row["weight_factor"]),
                open_time=int(row["open_time"]),
                close_time=int(row["close_time"]),
                exit_reason=row["exit_reason"],
                pnl_pct=float(row["pnl_pct"]),
                fee_pct=float(row["fee_pct"]),
                net_pnl_pct=float(row["net_pnl_pct"]),
                weighted_pnl=float(row["weighted_pnl"]),
            ))
    return trades


def main() -> None:
    # Load iter 138 trades (A+C+D)
    is_138 = load_trades(Path("reports/iteration_138/in_sample/trades.csv"))
    oos_138 = load_trades(Path("reports/iteration_138/out_of_sample/trades.csv"))
    print(f"iter 138: {len(is_138)} IS + {len(oos_138)} OOS = {len(is_138) + len(oos_138)} trades")

    # Load iter 142 DOGE trades (E)
    is_doge = load_trades(Path("reports/iteration_142_DOGE/in_sample/trades.csv"))
    oos_doge = load_trades(Path("reports/iteration_142_DOGE/out_of_sample/trades.csv"))
    print(f"iter 142 DOGE: {len(is_doge)} IS + {len(oos_doge)} OOS = {len(is_doge) + len(oos_doge)} trades")

    # Combine
    all_trades = is_138 + oos_138 + is_doge + oos_doge
    all_trades.sort(key=lambda t: t.close_time)
    print(f"\nCombined: {len(all_trades)} trades")

    # Generate iter 143 reports
    report_dir = generate_iteration_reports(
        trades=all_trades, iteration=143,
        features_dir="data/features", reports_dir="reports", interval="8h",
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
