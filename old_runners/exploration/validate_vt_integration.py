"""Validate engine-integrated VT matches iter 147 post-processing.

Loads iter 138's raw trades, simulates the backtest engine's VT logic
(incremental per-symbol daily PnL tracking + scale at open-time), and
compares the resulting metrics to iter 147's reported values.
"""

import csv
from pathlib import Path

from crypto_trade.backtest import _compute_vt_scale
from crypto_trade.backtest_models import BacktestConfig, TradeResult
from crypto_trade.iteration_report import generate_iteration_reports


def load_trades_raw(csv_path: Path) -> list[dict]:
    with open(csv_path) as f:
        return list(csv.DictReader(f))


def simulate_engine_vt(
    trades_raw: list[dict],
    config: BacktestConfig,
) -> list[TradeResult]:
    """Process trades in chronological order (by open_time),
    tracking per-symbol daily PnL incrementally, then scaling each
    trade at its open time. Mirrors the engine loop semantics.
    """
    # Sort by open_time to mirror chronological processing
    sorted_trades = sorted(trades_raw, key=lambda t: int(t["open_time"]))

    # Build chronological event list: each trade has OPEN and CLOSE events
    events = []
    for t in sorted_trades:
        events.append((int(t["open_time"]), "open", t))
        events.append((int(t["close_time"]), "close", t))
    events.sort(key=lambda e: (e[0], 0 if e[1] == "close" else 1))
    # Close events at same timestamp process BEFORE open events
    # (matches engine: close order → record PnL → potentially open new order)

    vt_per_sym_daily: dict[str, dict[str, float]] = {}
    scales_by_trade: dict[tuple, float] = {}

    import datetime
    def day_of(ms: int) -> str:
        return datetime.datetime.fromtimestamp(
            ms / 1000, tz=datetime.UTC
        ).strftime("%Y-%m-%d")

    for ts, event_type, trade in events:
        if event_type == "close":
            close_date = day_of(ts)
            sym_daily = vt_per_sym_daily.setdefault(trade["symbol"], {})
            net_pnl = float(trade["net_pnl_pct"])
            sym_daily[close_date] = sym_daily.get(close_date, 0.0) + net_pnl
        else:  # "open"
            scale = _compute_vt_scale(
                vt_per_sym_daily, trade["symbol"], ts, config
            )
            key = (int(trade["open_time"]), trade["symbol"], int(trade["direction"]))
            scales_by_trade[key] = scale

    # Build TradeResults with computed scales
    results = []
    for t in trades_raw:
        key = (int(t["open_time"]), t["symbol"], int(t["direction"]))
        scale = scales_by_trade.get(key, 1.0)
        net_pnl = float(t["net_pnl_pct"])
        results.append(TradeResult(
            symbol=t["symbol"], direction=int(t["direction"]),
            entry_price=float(t["entry_price"]), exit_price=float(t["exit_price"]),
            weight_factor=scale, open_time=int(t["open_time"]),
            close_time=int(t["close_time"]), exit_reason=t["exit_reason"],
            pnl_pct=float(t["pnl_pct"]), fee_pct=float(t["fee_pct"]),
            net_pnl_pct=net_pnl,  # KEEP RAW (engine design)
            weighted_pnl=net_pnl * scale,
        ))
    results.sort(key=lambda t: t.close_time)
    return results


def main() -> None:
    is_raw = load_trades_raw(Path("reports/iteration_138/in_sample/trades.csv"))
    oos_raw = load_trades_raw(Path("reports/iteration_138/out_of_sample/trades.csv"))
    all_raw = is_raw + oos_raw
    print(f"Loaded {len(all_raw)} iter 138 trades")

    config = BacktestConfig(
        symbols=("BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT"),
        interval="8h", max_amount_usd=1000.0,
        stop_loss_pct=4.0, take_profit_pct=8.0, timeout_minutes=10080,
        data_dir=Path("data"),
        vol_targeting=True,
        vt_target_vol=0.5, vt_lookback_days=30,
        vt_min_scale=0.5, vt_max_scale=2.0,
    )

    scaled_trades = simulate_engine_vt(all_raw, config)
    avg_scale = sum(t.weight_factor for t in scaled_trades) / len(scaled_trades)
    print(f"Avg scale: {avg_scale:.3f}")

    # Generate validation report
    report_dir = generate_iteration_reports(
        trades=scaled_trades, iteration="150_validation",
        features_dir="data/features", reports_dir="reports", interval="8h",
    )
    print(f"Reports: {report_dir}")


if __name__ == "__main__":
    main()
