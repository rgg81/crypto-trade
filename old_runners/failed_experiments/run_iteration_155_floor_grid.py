"""Iter 155 alt grid: per-symbol floor calibration.

Keeps universal target=0.3, lookback=45, but varies floor per-symbol.
Hypothesis: high-vol symbols (LINK) should delever more aggressively
(lower floor) than low-vol symbols (BTC).
"""

import csv
import datetime
from pathlib import Path

from crypto_trade.backtest_models import TradeResult
from crypto_trade.iteration_report import _compute_metrics


OOS_CUTOFF_MS = int(
    datetime.datetime(2025, 3, 24, tzinfo=datetime.UTC).timestamp() * 1000
)

VT_TARGET_VOL = 0.3
VT_LOOKBACK_DAYS = 45
VT_MIN_HISTORY = 5
VT_MAX_SCALE = 2.0


def day_of(ms: int) -> str:
    return datetime.datetime.fromtimestamp(
        ms / 1000, tz=datetime.UTC
    ).strftime("%Y-%m-%d")


def compute_scale(
    per_sym_daily: dict[str, dict[str, float]],
    symbol: str,
    trade_open_ms: int,
    min_scale: float,
) -> float:
    sym_daily = per_sym_daily.get(symbol, {})
    if not sym_daily:
        return 1.0
    trade_date = datetime.datetime.fromtimestamp(
        trade_open_ms / 1000, tz=datetime.UTC
    ).date()
    lookback: list[float] = []
    for date_str, pnl in sym_daily.items():
        cd = datetime.date.fromisoformat(date_str)
        db = (trade_date - cd).days
        if 1 <= db <= VT_LOOKBACK_DAYS:
            lookback.append(pnl)
    if len(lookback) < VT_MIN_HISTORY:
        return 1.0
    n = len(lookback)
    mu = sum(lookback) / n
    var = sum((r - mu) ** 2 for r in lookback) / (n - 1)
    rv = var ** 0.5
    if rv <= 1e-9:
        return 1.0
    scale = VT_TARGET_VOL / rv
    return max(min_scale, min(VT_MAX_SCALE, scale))


def apply_vt(
    trades_raw: list[dict],
    floor_per_sym: dict[str, float],
) -> list[TradeResult]:
    events = []
    for t in trades_raw:
        events.append((int(t["open_time"]), "open", t))
        events.append((int(t["close_time"]), "close", t))
    events.sort(key=lambda e: (e[0], 0 if e[1] == "close" else 1))

    running: dict[str, dict[str, float]] = {}
    scales_by_key: dict[tuple, float] = {}

    for ts, et, trade in events:
        sym = trade["symbol"]
        if et == "close":
            d = day_of(ts)
            sym_d = running.setdefault(sym, {})
            sym_d[d] = sym_d.get(d, 0.0) + float(trade["net_pnl_pct"])
        else:
            ms = floor_per_sym[sym]
            scale = compute_scale(running, sym, ts, ms)
            key = (int(trade["open_time"]), sym, int(trade["direction"]))
            scales_by_key[key] = scale

    results: list[TradeResult] = []
    for t in trades_raw:
        key = (int(t["open_time"]), t["symbol"], int(t["direction"]))
        scale = scales_by_key.get(key, 1.0)
        net_pnl = float(t["net_pnl_pct"])
        results.append(TradeResult(
            symbol=t["symbol"], direction=int(t["direction"]),
            entry_price=float(t["entry_price"]), exit_price=float(t["exit_price"]),
            weight_factor=scale,
            open_time=int(t["open_time"]), close_time=int(t["close_time"]),
            exit_reason=t["exit_reason"],
            pnl_pct=float(t["pnl_pct"]), fee_pct=float(t["fee_pct"]),
            net_pnl_pct=net_pnl, weighted_pnl=net_pnl * scale,
        ))
    results.sort(key=lambda t: t.close_time)
    return results


def split(results):
    is_t = [r for r in results if r.open_time < OOS_CUTOFF_MS]
    oos_t = [r for r in results if r.open_time >= OOS_CUTOFF_MS]
    return is_t, oos_t


def main() -> None:
    trades_raw = []
    for sub in ("in_sample", "out_of_sample"):
        with open(f"reports/iteration_138/{sub}/trades.csv") as f:
            for row in csv.DictReader(f):
                trades_raw.append(row)

    # Scheme A: vol-inversely-proportional floor
    #   low-vol symbols get higher floor (keep exposure)
    #   high-vol symbols get lower floor (delever more)
    # BTC median_vol=4.08, LINK median_vol=7.77. Ratio 1.9x.
    # If BTC floor=0.40, LINK floor=0.40 * 4.08/7.77 = 0.21
    print("=== Baseline (universal floor=0.33, v0.152) ===")
    baseline_floor = dict.fromkeys(["BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT"], 0.33)
    base = apply_vt(trades_raw, baseline_floor)
    is_t, oos_t = split(base)
    is_m = _compute_metrics(is_t)
    oos_m = _compute_metrics(oos_t)
    print(f"  IS  Sharpe={is_m.sharpe:+.4f} MaxDD={is_m.max_drawdown:.2f}%")
    print(f"  OOS Sharpe={oos_m.sharpe:+.4f} MaxDD={oos_m.max_drawdown:.2f}% "
          f"PF={oos_m.profit_factor:.2f}")

    print("\n=== Per-symbol floor (vol-inverse) ===")
    print(f"{'Config':22s} {'IS_SR':>8s} {'OOS_SR':>8s} "
          f"{'IS_DD':>7s} {'OOS_DD':>7s} {'OOS_PF':>7s}")
    # Reference: median vols = BTC 4.08, BNB 4.43, ETH 5.43, LINK 7.77
    # Inverse-vol floor: floor_sym = base_floor * (min_vol / sym_vol)
    #   at base=0.50, floors: BTC=0.50, BNB=0.46, ETH=0.376, LINK=0.263
    configs = []
    for base_floor in [0.40, 0.45, 0.50, 0.55, 0.60]:
        # Inverse-vol scheme, anchored to BTC (lowest vol)
        floors = {
            "BTCUSDT": round(base_floor, 3),
            "BNBUSDT": round(base_floor * 4.08 / 4.43, 3),
            "ETHUSDT": round(base_floor * 4.08 / 5.43, 3),
            "LINKUSDT": round(base_floor * 4.08 / 7.77, 3),
        }
        configs.append((f"inv-vol@{base_floor:.2f}", floors))

    # Also try asymmetric: lower floor for LINK only
    configs.append(("LINK-tight(0.20)", {
        "BTCUSDT": 0.33, "BNBUSDT": 0.33, "ETHUSDT": 0.33, "LINKUSDT": 0.20
    }))
    configs.append(("LINK-tight(0.15)", {
        "BTCUSDT": 0.33, "BNBUSDT": 0.33, "ETHUSDT": 0.33, "LINKUSDT": 0.15
    }))
    # BTC-loose: low-vol symbol keeps more exposure
    configs.append(("BTC-loose(0.50)", {
        "BTCUSDT": 0.50, "BNBUSDT": 0.33, "ETHUSDT": 0.33, "LINKUSDT": 0.33
    }))
    configs.append(("BTC-loose(0.67)", {
        "BTCUSDT": 0.67, "BNBUSDT": 0.33, "ETHUSDT": 0.33, "LINKUSDT": 0.33
    }))

    for name, floors in configs:
        results = apply_vt(trades_raw, floors)
        is_t, oos_t = split(results)
        is_m = _compute_metrics(is_t)
        oos_m = _compute_metrics(oos_t)
        print(
            f"{name:22s} {is_m.sharpe:+8.4f} {oos_m.sharpe:+8.4f} "
            f"{is_m.max_drawdown:7.2f} {oos_m.max_drawdown:7.2f} "
            f"{oos_m.profit_factor:7.2f}  floors={floors}"
        )


if __name__ == "__main__":
    main()
