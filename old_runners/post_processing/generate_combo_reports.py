"""Generate iter 144 reports for various model combinations using existing trades."""

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


MODEL_SYMBOLS = {
    "A": ["BTCUSDT", "ETHUSDT"],
    "C": ["LINKUSDT"],
    "D": ["BNBUSDT"],
    "E": ["DOGEUSDT"],
}


def main() -> None:
    # Load all trades
    is_138 = load_trades(Path("reports/iteration_138/in_sample/trades.csv"))
    oos_138 = load_trades(Path("reports/iteration_138/out_of_sample/trades.csv"))
    is_doge = load_trades(Path("reports/iteration_142_DOGE/in_sample/trades.csv"))
    oos_doge = load_trades(Path("reports/iteration_142_DOGE/out_of_sample/trades.csv"))
    all_trades = is_138 + oos_138 + is_doge + oos_doge
    print(f"Loaded {len(all_trades)} total trades")

    # Test combinations that dropped a model
    combos = [
        ("A", ["A"]),
        ("AD", ["A", "D"]),
        ("AC", ["A", "C"]),
        ("ACD", ["A", "C", "D"]),
        ("ACDE", ["A", "C", "D", "E"]),
    ]

    for name, models in combos:
        symbols = set()
        for m in models:
            symbols.update(MODEL_SYMBOLS[m])

        subset = [t for t in all_trades if t.symbol in symbols]
        subset.sort(key=lambda t: t.close_time)

        report_dir = generate_iteration_reports(
            trades=subset, iteration=f"144_{name}",
            features_dir="data/features", reports_dir="reports", interval="8h",
        )
        print(f"\n{name}: {len(subset)} trades -> {report_dir}")


if __name__ == "__main__":
    main()
