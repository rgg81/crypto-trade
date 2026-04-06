"""Iter 155 grid: per-symbol target_vol calibration.

Post-processes iter 138 raw trades with per-symbol target_vol calibrated
to each symbol's median IS realized vol. Floor (0.33) and lookback (45)
held at iter 152 winners.

Selection: best IS Sharpe. Winner applied to OOS for final validation.
"""

import csv
import datetime
from pathlib import Path

from crypto_trade.backtest_models import TradeResult
from crypto_trade.iteration_report import _compute_metrics


OOS_CUTOFF_MS = int(
    datetime.datetime(2025, 3, 24, tzinfo=datetime.UTC).timestamp() * 1000
)

# IS median realized vol per symbol (from analyze_per_symbol_vol.py)
MEDIAN_VOL = {
    "BTCUSDT": 4.08,
    "ETHUSDT": 5.43,
    "LINKUSDT": 7.77,
    "BNBUSDT": 4.43,
}

VT_MIN_SCALE = 0.33
VT_MAX_SCALE = 2.0
VT_LOOKBACK_DAYS = 45
VT_MIN_HISTORY = 5


def day_of(ms: int) -> str:
    return datetime.datetime.fromtimestamp(
        ms / 1000, tz=datetime.UTC
    ).strftime("%Y-%m-%d")


def compute_scale(
    per_sym_daily: dict[str, dict[str, float]],
    symbol: str,
    trade_open_ms: int,
    target_vol: float,
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
    scale = target_vol / rv
    return max(VT_MIN_SCALE, min(VT_MAX_SCALE, scale))


def load_iter138_trades() -> list[dict]:
    trades = []
    for sub in ("in_sample", "out_of_sample"):
        path = Path(f"reports/iteration_138/{sub}/trades.csv")
        with open(path) as f:
            for row in csv.DictReader(f):
                trades.append(row)
    return trades


def apply_vt(
    trades_raw: list[dict],
    target_vol_per_sym: dict[str, float],
) -> list[TradeResult]:
    # Event-driven chronological processing
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
            tv = target_vol_per_sym[sym]
            scale = compute_scale(running, sym, ts, tv)
            key = (int(trade["open_time"]), sym, int(trade["direction"]))
            scales_by_key[key] = scale

    results: list[TradeResult] = []
    for t in trades_raw:
        key = (int(t["open_time"]), t["symbol"], int(t["direction"]))
        scale = scales_by_key.get(key, 1.0)
        net_pnl = float(t["net_pnl_pct"])
        results.append(TradeResult(
            symbol=t["symbol"],
            direction=int(t["direction"]),
            entry_price=float(t["entry_price"]),
            exit_price=float(t["exit_price"]),
            weight_factor=scale,
            open_time=int(t["open_time"]),
            close_time=int(t["close_time"]),
            exit_reason=t["exit_reason"],
            pnl_pct=float(t["pnl_pct"]),
            fee_pct=float(t["fee_pct"]),
            net_pnl_pct=net_pnl,
            weighted_pnl=net_pnl * scale,
        ))
    results.sort(key=lambda t: t.close_time)
    return results


def split_is_oos(
    results: list[TradeResult],
) -> tuple[list[TradeResult], list[TradeResult]]:
    is_t = [r for r in results if r.open_time < OOS_CUTOFF_MS]
    oos_t = [r for r in results if r.open_time >= OOS_CUTOFF_MS]
    return is_t, oos_t


def avg_scale(results: list[TradeResult]) -> float:
    return sum(r.weight_factor for r in results) / len(results)


def main() -> None:
    trades_raw = load_iter138_trades()
    print(f"Loaded {len(trades_raw)} iter 138 raw trades\n")

    # Baseline: universal target=0.3 (v0.152 production)
    print("=== Baseline (universal target=0.3, v0.152) ===")
    baseline_tv = dict.fromkeys(MEDIAN_VOL, 0.3)
    base_results = apply_vt(trades_raw, baseline_tv)
    is_t, oos_t = split_is_oos(base_results)
    is_m = _compute_metrics(is_t)
    oos_m = _compute_metrics(oos_t)
    print(
        f"  IS  Sharpe={is_m.sharpe:+.4f} MaxDD={is_m.max_drawdown:.2f}% "
        f"avg_scale={avg_scale(is_t):.3f}"
    )
    print(
        f"  OOS Sharpe={oos_m.sharpe:+.4f} MaxDD={oos_m.max_drawdown:.2f}% "
        f"avg_scale={avg_scale(oos_t):.3f} PF={oos_m.profit_factor:.2f}"
    )

    print("\n=== Per-symbol calibrated grid ===")
    print(f"{'Config':10s} {'k':>5s} {'IS_SR':>8s} {'OOS_SR':>8s} "
          f"{'IS_DD':>7s} {'OOS_DD':>7s} {'OOS_PF':>7s} {'avg_sc':>7s}")

    results_table = []
    for k in [0.3, 0.4, 0.5, 0.6, 0.7, 0.85, 1.0, 1.5, 2.0]:
        tv_per_sym = {s: v * k for s, v in MEDIAN_VOL.items()}
        results = apply_vt(trades_raw, tv_per_sym)
        is_t, oos_t = split_is_oos(results)
        is_m = _compute_metrics(is_t)
        oos_m = _compute_metrics(oos_t)
        avg_sc_is = avg_scale(is_t)
        avg_sc_oos = avg_scale(oos_t)
        print(
            f"k={k:<8.2f} {k:5.2f} {is_m.sharpe:+8.4f} {oos_m.sharpe:+8.4f} "
            f"{is_m.max_drawdown:7.2f} {oos_m.max_drawdown:7.2f} "
            f"{oos_m.profit_factor:7.2f} {avg_sc_is:7.3f}"
        )
        results_table.append({
            "k": k,
            "is_sharpe": is_m.sharpe,
            "oos_sharpe": oos_m.sharpe,
            "is_dd": is_m.max_drawdown,
            "oos_dd": oos_m.max_drawdown,
            "oos_pf": oos_m.profit_factor,
            "is_trades": is_m.total_trades,
            "oos_trades": oos_m.total_trades,
            "avg_scale_is": avg_sc_is,
            "avg_scale_oos": avg_sc_oos,
            "oos_calmar": oos_m.calmar_ratio,
            "oos_pnl": oos_m.total_net_pnl,
        })

    # IS-best selection
    best_is = max(results_table, key=lambda r: r["is_sharpe"])
    print(f"\n=== IS-best config: k={best_is['k']:.2f} ===")
    print(f"  IS Sharpe: {best_is['is_sharpe']:+.4f}")
    print(f"  OOS Sharpe: {best_is['oos_sharpe']:+.4f}")
    print(f"  OOS MaxDD: {best_is['oos_dd']:.2f}%")
    print(f"  OOS PF: {best_is['oos_pf']:.2f}")
    print(f"  OOS Calmar: {best_is['oos_calmar']:.2f}")
    print(f"  OOS PnL: {best_is['oos_pnl']:+.2f}%")
    print(f"  Per-symbol target_vol: "
          f"{ {s: v * best_is['k'] for s, v in MEDIAN_VOL.items()} }")


if __name__ == "__main__":
    main()
