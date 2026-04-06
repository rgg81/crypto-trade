"""Diagnose what scales iter 152's VT actually produces.

Replicates engine VT logic on iter 138 trades with iter 152 config
(target=0.3, lookback=45, min_scale=0.33) and reports:
- Distribution of scales (histogram)
- Per-symbol scale distribution
- How often the scale == floor
- How often the scale == default 1.0 (insufficient history)
"""

import csv
import datetime
from pathlib import Path
from statistics import mean, median

from crypto_trade.backtest import _compute_vt_scale
from crypto_trade.backtest_models import BacktestConfig

OOS_CUTOFF_MS = int(
    datetime.datetime(2025, 3, 24, tzinfo=datetime.UTC).timestamp() * 1000
)


def day_of(ms: int) -> str:
    return datetime.datetime.fromtimestamp(
        ms / 1000, tz=datetime.UTC
    ).strftime("%Y-%m-%d")


def simulate_vt(trades_raw: list[dict], config: BacktestConfig) -> list[dict]:
    """Mirror engine: track per-sym daily PnL, compute scale at each open."""
    events = []
    for t in trades_raw:
        events.append((int(t["open_time"]), "open", t))
        events.append((int(t["close_time"]), "close", t))
    events.sort(key=lambda e: (e[0], 0 if e[1] == "close" else 1))

    running: dict[str, dict[str, float]] = {}
    scales_by_key: dict[tuple, float] = {}

    for ts, event_type, trade in events:
        sym = trade["symbol"]
        if event_type == "close":
            d = day_of(ts)
            sym_d = running.setdefault(sym, {})
            sym_d[d] = sym_d.get(d, 0.0) + float(trade["net_pnl_pct"])
        else:
            scale = _compute_vt_scale(running, sym, ts, config)
            key = (int(trade["open_time"]), sym, int(trade["direction"]))
            scales_by_key[key] = scale

    # Attach scales to trades
    result = []
    for t in trades_raw:
        key = (int(t["open_time"]), t["symbol"], int(t["direction"]))
        result.append({
            "symbol": t["symbol"],
            "open_time": int(t["open_time"]),
            "scale": scales_by_key.get(key, 1.0),
            "net_pnl_pct": float(t["net_pnl_pct"]),
        })
    return result


def main() -> None:
    trades = []
    for sub in ("in_sample", "out_of_sample"):
        with open(f"reports/iteration_138/{sub}/trades.csv") as f:
            for row in csv.DictReader(f):
                trades.append(row)

    config = BacktestConfig(
        symbols=("BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT"),
        interval="8h", max_amount_usd=1000.0,
        stop_loss_pct=4.0, take_profit_pct=8.0, timeout_minutes=10080,
        data_dir=Path("data"),
        vol_targeting=True,
        vt_target_vol=0.3, vt_lookback_days=45,
        vt_min_scale=0.33, vt_max_scale=2.0,
    )

    scaled = simulate_vt(trades, config)
    print(f"Total trades: {len(scaled)}")
    print(f"Global avg scale: {mean(s['scale'] for s in scaled):.3f}")
    print(f"Global median scale: {median(s['scale'] for s in scaled):.3f}")

    # Count scales by bucket
    buckets = {"floor(0.33)": 0, "default(1.0)": 0, "mid(0.34-0.99)": 0, "other": 0}
    for s in scaled:
        sc = s["scale"]
        if abs(sc - 0.33) < 1e-6:
            buckets["floor(0.33)"] += 1
        elif abs(sc - 1.0) < 1e-6:
            buckets["default(1.0)"] += 1
        elif 0.33 < sc < 1.0:
            buckets["mid(0.34-0.99)"] += 1
        else:
            buckets["other"] += 1
    print("\n=== Scale buckets (all trades) ===")
    for k, v in buckets.items():
        print(f"  {k}: {v} ({100 * v / len(scaled):.1f}%)")

    # Per-symbol breakdown
    print("\n=== Per-symbol scale distribution ===")
    print(f"{'Symbol':10s} {'count':>6s} {'mean':>7s} {'median':>7s} "
          f"{'@floor':>8s} {'@default':>9s}")
    syms = sorted(set(s["symbol"] for s in scaled))
    for sym in syms:
        sym_scales = [s["scale"] for s in scaled if s["symbol"] == sym]
        at_floor = sum(1 for x in sym_scales if abs(x - 0.33) < 1e-6)
        at_default = sum(1 for x in sym_scales if abs(x - 1.0) < 1e-6)
        print(
            f"{sym:10s} {len(sym_scales):6d} {mean(sym_scales):7.3f} "
            f"{median(sym_scales):7.3f} "
            f"{at_floor:4d}({100*at_floor/len(sym_scales):3.0f}%) "
            f"{at_default:3d}({100*at_default/len(sym_scales):3.0f}%)"
        )

    # What if we used a flat scale? Compute hypothetical PnL
    print("\n=== Hypothetical: flat scale=0.33 vs adaptive VT ===")
    oos = [s for s in scaled if s["open_time"] >= OOS_CUTOFF_MS]
    vt_weighted_oos = sum(s["scale"] * s["net_pnl_pct"] for s in oos)
    flat_weighted_oos = sum(0.33 * s["net_pnl_pct"] for s in oos)
    raw_oos = sum(s["net_pnl_pct"] for s in oos)
    print(f"  Raw OOS PnL (scale=1): {raw_oos:+.2f}%")
    print(f"  Flat scale=0.33 OOS PnL: {flat_weighted_oos:+.2f}%")
    print(f"  Adaptive VT OOS PnL: {vt_weighted_oos:+.2f}%")

    # Per-symbol average scale (only adaptive VT)
    print("\n=== What if per-symbol target_vol scaled to median realized vol? ===")
    # Median realized vol per symbol (from prior analysis):
    realized = {"BTCUSDT": 4.08, "ETHUSDT": 5.43, "LINKUSDT": 7.77, "BNBUSDT": 4.43}
    print(f"  Median realized vol: {realized}")
    print("  If target=median*0.5 per symbol, scale at median = 0.5 for all")


if __name__ == "__main__":
    main()
