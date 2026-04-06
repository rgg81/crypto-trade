"""Iter 158: ADX exclusion bound grid search.

Tests 25 (lower, upper) combinations. Selection: max(IS_Sharpe × sqrt(IS_n))
with IS_n >= 200. Reports OOS for t-stat-best config.
"""

import csv
import datetime
import math
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.backtest import _compute_vt_scale
from crypto_trade.backtest_models import BacktestConfig, TradeResult
from crypto_trade.iteration_report import _compute_metrics

OOS_CUTOFF_MS = int(
    datetime.datetime(2025, 3, 24, tzinfo=datetime.UTC).timestamp() * 1000
)

SYMBOLS = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT")


def day_of(ms: int) -> str:
    return datetime.datetime.fromtimestamp(
        ms / 1000, tz=datetime.UTC
    ).strftime("%Y-%m-%d")


def lookup_asof(df: pd.DataFrame, col: str, ts_ms: int) -> float:
    idx = df.index.searchsorted(ts_ms, side="right") - 1
    if idx < 0:
        return np.nan
    val = df[col].iloc[idx]
    return float(val) if not pd.isna(val) else np.nan


def load_trades_with_adx():
    trades = []
    for sub in ("in_sample", "out_of_sample"):
        with open(f"reports/iteration_138/{sub}/trades.csv") as f:
            for row in csv.DictReader(f):
                trades.append(row)
    trades.sort(key=lambda t: int(t["open_time"]))

    frames = {}
    for sym in SYMBOLS:
        df = pd.read_parquet(
            f"data/features/{sym}_8h_features.parquet",
            columns=["open_time", "trend_adx_14"],
        )
        df = df.set_index("open_time").sort_index()
        frames[sym] = df

    # Pre-compute ADX at open for each trade
    for t in trades:
        t["_adx"] = lookup_asof(
            frames[t["symbol"]], "trend_adx_14", int(t["open_time"])
        )
    return trades


def apply_vt(
    trades_raw: list[dict], kept_mask: np.ndarray, config: BacktestConfig,
) -> list[TradeResult]:
    events = []
    for i, t in enumerate(trades_raw):
        events.append((int(t["open_time"]), "open", i, t))
        events.append((int(t["close_time"]), "close", i, t))
    events.sort(key=lambda e: (e[0], 0 if e[1] == "close" else 1))

    running: dict[str, dict[str, float]] = {}
    scales_by_i: dict[int, float] = {}
    for ts, et, i, trade in events:
        sym = trade["symbol"]
        if et == "close":
            d = day_of(ts)
            sym_d = running.setdefault(sym, {})
            sym_d[d] = sym_d.get(d, 0.0) + float(trade["net_pnl_pct"])
        else:
            scales_by_i[i] = _compute_vt_scale(running, sym, ts, config)

    results = []
    for i, t in enumerate(trades_raw):
        if not kept_mask[i]:
            continue
        scale = scales_by_i.get(i, 1.0)
        net_pnl = float(t["net_pnl_pct"])
        results.append(TradeResult(
            symbol=t["symbol"], direction=int(t["direction"]),
            entry_price=float(t["entry_price"]),
            exit_price=float(t["exit_price"]),
            weight_factor=scale,
            open_time=int(t["open_time"]), close_time=int(t["close_time"]),
            exit_reason=t["exit_reason"],
            pnl_pct=float(t["pnl_pct"]), fee_pct=float(t["fee_pct"]),
            net_pnl_pct=net_pnl, weighted_pnl=net_pnl * scale,
        ))
    results.sort(key=lambda t: t.close_time)
    return results


def split_is_oos(results):
    is_t = [r for r in results if r.open_time < OOS_CUTOFF_MS]
    oos_t = [r for r in results if r.open_time >= OOS_CUTOFF_MS]
    return is_t, oos_t


def make_mask(trades, lower, upper):
    n = len(trades)
    mask = np.ones(n, dtype=bool)
    for i, t in enumerate(trades):
        adx = t["_adx"]
        if not np.isnan(adx) and lower < adx <= upper:
            mask[i] = False
    return mask


def main():
    trades = load_trades_with_adx()
    print(f"Loaded {len(trades)} trades with ADX")

    config = BacktestConfig(
        symbols=SYMBOLS, interval="8h", max_amount_usd=1000.0,
        stop_loss_pct=4.0, take_profit_pct=8.0, timeout_minutes=10080,
        data_dir=Path("data"),
        vol_targeting=True, vt_target_vol=0.3, vt_lookback_days=45,
        vt_min_scale=0.33, vt_max_scale=2.0,
    )

    # Baseline
    print("\n=== Baseline (no filter) ===")
    base = apply_vt(trades, np.ones(len(trades), dtype=bool), config)
    is_t, oos_t = split_is_oos(base)
    base_is = _compute_metrics(is_t)
    base_oos = _compute_metrics(oos_t)
    base_tstat = base_is.sharpe * math.sqrt(base_is.total_trades)
    print(f"  IS Sharpe={base_is.sharpe:+.4f} n={base_is.total_trades} "
          f"t-stat={base_tstat:.2f}")
    print(f"  OOS Sharpe={base_oos.sharpe:+.4f} MaxDD={base_oos.max_drawdown:.2f}%")

    print("\n=== ADX grid (drop trades where lower < ADX <= upper) ===")
    print(f"{'lower':>6s} {'upper':>6s} {'IS_n':>5s} {'IS_SR':>8s} "
          f"{'t-stat':>7s} {'OOS_n':>6s} {'OOS_SR':>8s} {'OOS_DD':>7s} "
          f"{'OOS_PF':>7s}")

    table = []
    for lower in [15, 18, 20, 22, 25]:
        for upper in [30, 33, 36, 40, 45]:
            if upper <= lower:
                continue
            mask = make_mask(trades, lower, upper)
            results = apply_vt(trades, mask, config)
            is_t, oos_t = split_is_oos(results)
            if len(is_t) < 50 or len(oos_t) < 20:
                continue
            is_m = _compute_metrics(is_t)
            oos_m = _compute_metrics(oos_t)
            tstat = is_m.sharpe * math.sqrt(is_m.total_trades)
            print(
                f"{lower:6d} {upper:6d} {is_m.total_trades:5d} "
                f"{is_m.sharpe:+8.4f} {tstat:7.2f} "
                f"{oos_m.total_trades:6d} {oos_m.sharpe:+8.4f} "
                f"{oos_m.max_drawdown:7.2f} {oos_m.profit_factor:7.2f}"
            )
            table.append({
                "lower": lower, "upper": upper,
                "is_sharpe": is_m.sharpe, "is_n": is_m.total_trades,
                "tstat": tstat,
                "oos_sharpe": oos_m.sharpe, "oos_n": oos_m.total_trades,
                "oos_dd": oos_m.max_drawdown, "oos_pf": oos_m.profit_factor,
                "oos_calmar": oos_m.calmar_ratio,
                "oos_pnl": oos_m.total_net_pnl,
                "is_dd": is_m.max_drawdown,
            })

    # t-stat-best selection (min 200 IS trades)
    valid = [r for r in table if r["is_n"] >= 200]
    if not valid:
        print("\nNo config passes IS_n >= 200 constraint")
        return
    best = max(valid, key=lambda r: r["tstat"])
    print(f"\n=== t-stat-best: lower={best['lower']}, upper={best['upper']} ===")
    print(f"  IS Sharpe: {best['is_sharpe']:+.4f} (n={best['is_n']})")
    print(f"  t-stat: {best['tstat']:.2f} (vs baseline {base_tstat:.2f})")
    print(f"  OOS Sharpe: {best['oos_sharpe']:+.4f} (n={best['oos_n']})")
    print(f"  OOS MaxDD: {best['oos_dd']:.2f}%")
    print(f"  OOS PF: {best['oos_pf']:.2f}")
    print(f"  OOS Calmar: {best['oos_calmar']:.2f}")
    print(f"  OOS PnL: {best['oos_pnl']:+.2f}%")
    print(f"  IS MaxDD: {best['is_dd']:.2f}%")

    # Per-symbol OOS concentration for t-stat-best
    mask = make_mask(trades, best["lower"], best["upper"])
    results = apply_vt(trades, mask, config)
    _, oos_t = split_is_oos(results)
    oos_sym_pnl: dict[str, float] = {}
    total = 0.0
    for r in oos_t:
        oos_sym_pnl[r.symbol] = oos_sym_pnl.get(r.symbol, 0.0) + r.weighted_pnl
        total += r.weighted_pnl
    print("\n  Per-symbol OOS PnL (weighted):")
    for sym, pnl in sorted(oos_sym_pnl.items()):
        frac = pnl / total if total else 0
        print(f"    {sym}: {pnl:+7.2f}% ({frac*100:+5.1f}% of total)")

    # Robustness: how many configs beat baseline OOS Sharpe?
    beats = [r for r in valid if r["oos_sharpe"] > base_oos.sharpe]
    print(f"\nConfigs beating baseline OOS Sharpe: {len(beats)}/{len(valid)}")
    print(f"Configs with OOS Sharpe > 2.90: "
          f"{len([r for r in valid if r['oos_sharpe'] > 2.90])}/{len(valid)}")


if __name__ == "__main__":
    main()
