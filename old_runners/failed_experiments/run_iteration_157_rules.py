"""Iter 157: Rule-based meta-filter on iter 138 trades.

Tests simple IS-derived rules (no ML):
- Rule A: drop all SHORTs
- Rule B: drop SHORTs where symbol in {BTC, BNB, LINK}
- Rule C: drop hour=23 UTC
- Rule D: drop symbol ADX Q3 bucket (19.6 < ADX <= 34.6)
- Rule E: B + C
- Rule F: (BTC/BNB/LINK × SHORT) AND (hour=23 OR ADX_Q3)

IS-best selection (min 150 IS trades). Apply to OOS with iter 152 VT.
"""

import csv
import datetime
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
# IS-derived ADX Q3 thresholds (from analyze_is_buckets.py)
ADX_Q2 = 19.612
ADX_Q3 = 25.582
ADX_Q4 = 34.626  # Q3 bucket is (Q2, Q4)


def day_of(ms: int) -> str:
    return datetime.datetime.fromtimestamp(
        ms / 1000, tz=datetime.UTC
    ).strftime("%Y-%m-%d")


def hour_of(ms: int) -> int:
    return datetime.datetime.fromtimestamp(
        ms / 1000, tz=datetime.UTC
    ).hour


def load_trades() -> list[dict]:
    trades = []
    for sub in ("in_sample", "out_of_sample"):
        with open(f"reports/iteration_138/{sub}/trades.csv") as f:
            for row in csv.DictReader(f):
                trades.append(row)
    trades.sort(key=lambda t: int(t["open_time"]))
    return trades


def load_feature_frames() -> dict[str, pd.DataFrame]:
    frames = {}
    for sym in SYMBOLS:
        path = f"data/features/{sym}_8h_features.parquet"
        df = pd.read_parquet(path, columns=["open_time", "trend_adx_14"])
        df = df.set_index("open_time").sort_index()
        frames[sym] = df
    return frames


def lookup_asof(df: pd.DataFrame, col: str, ts_ms: int) -> float:
    idx = df.index.searchsorted(ts_ms, side="right") - 1
    if idx < 0:
        return np.nan
    val = df[col].iloc[idx]
    return float(val) if not pd.isna(val) else np.nan


def enrich(trades: list[dict], frames: dict[str, pd.DataFrame]) -> list[dict]:
    out = []
    for t in trades:
        sym = t["symbol"]
        ot = int(t["open_time"])
        adx = lookup_asof(frames[sym], "trend_adx_14", ot)
        enriched = dict(t)
        enriched["_hour"] = hour_of(ot)
        enriched["_sym_adx"] = adx
        enriched["_direction_i"] = int(t["direction"])
        out.append(enriched)
    return out


def apply_vt(
    trades_raw: list[dict],
    kept_mask: np.ndarray,
    config: BacktestConfig,
) -> list[TradeResult]:
    # VT history from ALL original trades (mirror engine behavior)
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
            scale = _compute_vt_scale(running, sym, ts, config)
            scales_by_i[i] = scale

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


def rule_mask(trades: list[dict], rule: str) -> np.ndarray:
    n = len(trades)
    mask = np.ones(n, dtype=bool)

    for i, t in enumerate(trades):
        sym = t["symbol"]
        d = t["_direction_i"]
        h = t["_hour"]
        adx = t["_sym_adx"]

        if rule == "baseline":
            pass
        elif rule == "A_no_short":
            if d == -1:
                mask[i] = False
        elif rule == "B_targeted_short":
            if d == -1 and sym in ("BTCUSDT", "BNBUSDT", "LINKUSDT"):
                mask[i] = False
        elif rule == "C_hour23":
            if h == 23:
                mask[i] = False
        elif rule == "D_adx_q3":
            if not np.isnan(adx) and ADX_Q2 < adx <= ADX_Q4:
                mask[i] = False
        elif rule == "E_B_plus_C":
            drop_b = d == -1 and sym in ("BTCUSDT", "BNBUSDT", "LINKUSDT")
            drop_c = h == 23
            if drop_b or drop_c:
                mask[i] = False
        elif rule == "F_weak_bucket":
            # (BTC/BNB/LINK × SHORT) AND (hour=23 OR ADX_Q3)
            bad_short = d == -1 and sym in ("BTCUSDT", "BNBUSDT", "LINKUSDT")
            adx_bad = not np.isnan(adx) and ADX_Q2 < adx <= ADX_Q4
            if bad_short and (h == 23 or adx_bad):
                mask[i] = False
        elif rule == "G_hour23_adx_q3":
            adx_bad = not np.isnan(adx) and ADX_Q2 < adx <= ADX_Q4
            if h == 23 or adx_bad:
                mask[i] = False
        else:
            raise ValueError(f"Unknown rule: {rule}")
    return mask


def main() -> None:
    print("Loading trades...")
    trades = load_trades()
    frames = load_feature_frames()
    enriched = enrich(trades, frames)
    print(f"Loaded {len(enriched)} trades")

    config = BacktestConfig(
        symbols=SYMBOLS,
        interval="8h", max_amount_usd=1000.0,
        stop_loss_pct=4.0, take_profit_pct=8.0, timeout_minutes=10080,
        data_dir=Path("data"),
        vol_targeting=True,
        vt_target_vol=0.3, vt_lookback_days=45,
        vt_min_scale=0.33, vt_max_scale=2.0,
    )

    print(f"\n{'Rule':25s} {'IS_n':>5s} {'OOS_n':>6s} "
          f"{'IS_SR':>8s} {'OOS_SR':>8s} {'IS_DD':>7s} {'OOS_DD':>7s} "
          f"{'OOS_PF':>7s} {'dropped':>8s}")

    rules = [
        "baseline", "A_no_short", "B_targeted_short", "C_hour23",
        "D_adx_q3", "E_B_plus_C", "F_weak_bucket", "G_hour23_adx_q3",
    ]

    table = []
    for rule in rules:
        mask = rule_mask(enriched, rule)
        n_dropped = (~mask).sum()
        results = apply_vt(enriched, mask, config)
        is_t, oos_t = split_is_oos(results)
        if len(is_t) < 50 or len(oos_t) < 20:
            print(f"{rule:25s} too few trades")
            continue
        is_m = _compute_metrics(is_t)
        oos_m = _compute_metrics(oos_t)
        print(
            f"{rule:25s} {is_m.total_trades:5d} {oos_m.total_trades:6d} "
            f"{is_m.sharpe:+8.4f} {oos_m.sharpe:+8.4f} "
            f"{is_m.max_drawdown:7.2f} {oos_m.max_drawdown:7.2f} "
            f"{oos_m.profit_factor:7.2f} {n_dropped:8d}"
        )
        table.append({
            "rule": rule,
            "is_sharpe": is_m.sharpe, "oos_sharpe": oos_m.sharpe,
            "is_n": is_m.total_trades, "oos_n": oos_m.total_trades,
            "is_dd": is_m.max_drawdown, "oos_dd": oos_m.max_drawdown,
            "oos_pf": oos_m.profit_factor,
            "oos_calmar": oos_m.calmar_ratio,
            "oos_pnl": oos_m.total_net_pnl,
        })

    # Per-symbol check for IS-best rule (concentration)
    valid = [r for r in table if r["is_n"] >= 150 and r["rule"] != "baseline"]
    if not valid:
        print("\nNo rule passes IS-trade constraint")
        return
    best = max(valid, key=lambda r: r["is_sharpe"])
    print(f"\n=== IS-best rule: {best['rule']} ===")
    print(f"  IS Sharpe: {best['is_sharpe']:+.4f} (n={best['is_n']})")
    print(f"  OOS Sharpe: {best['oos_sharpe']:+.4f} (n={best['oos_n']})")
    print(f"  OOS MaxDD: {best['oos_dd']:.2f}%")
    print(f"  OOS PF: {best['oos_pf']:.2f}")
    print(f"  OOS Calmar: {best['oos_calmar']:.2f}")
    print(f"  OOS PnL: {best['oos_pnl']:+.2f}%")

    # Concentration check
    mask = rule_mask(enriched, best["rule"])
    results = apply_vt(enriched, mask, config)
    _, oos_t = split_is_oos(results)
    oos_sym_pnl: dict[str, float] = {}
    total_oos = 0.0
    for r in oos_t:
        oos_sym_pnl[r.symbol] = oos_sym_pnl.get(r.symbol, 0.0) + r.weighted_pnl
        total_oos += r.weighted_pnl
    print(f"\n  Per-symbol OOS PnL (weighted) for best rule:")
    for sym, pnl in sorted(oos_sym_pnl.items()):
        frac = pnl / total_oos if total_oos != 0 else 0
        print(f"    {sym}: {pnl:+7.2f}% ({frac*100:+5.1f}% of total)")


if __name__ == "__main__":
    main()
