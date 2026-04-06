"""IS-only per-symbol vol analysis for iter 155.

Compute per-symbol realized daily vol distribution to understand whether
a per-symbol VT config could outperform the universal target_vol=0.3,
lookback=45, min_scale=0.33 config.
"""

import csv
import datetime
from pathlib import Path
from statistics import mean, stdev, median


OOS_CUTOFF_MS = int(
    datetime.datetime(2025, 3, 24, tzinfo=datetime.UTC).timestamp() * 1000
)
LOOKBACK_DAYS = 45


def day_of(ms: int) -> str:
    return datetime.datetime.fromtimestamp(
        ms / 1000, tz=datetime.UTC
    ).strftime("%Y-%m-%d")


def load_all_trades() -> list[dict]:
    trades = []
    for sub in ("in_sample", "out_of_sample"):
        path = Path(f"reports/iteration_138/{sub}/trades.csv")
        with open(path) as f:
            for row in csv.DictReader(f):
                trades.append(row)
    return trades


def build_per_sym_daily(trades: list[dict]) -> dict[str, dict[str, float]]:
    """Sum net_pnl_pct per (symbol, close_date)."""
    per = {}
    for t in trades:
        sym = t["symbol"]
        d = day_of(int(t["close_time"]))
        per.setdefault(sym, {})
        per[sym][d] = per[sym].get(d, 0.0) + float(t["net_pnl_pct"])
    return per


def realized_vol_distribution(
    per_sym_daily: dict[str, dict[str, float]],
    trades: list[dict],
    is_only: bool,
) -> dict[str, list[float]]:
    """For each symbol, compute the realized vol seen by every trade
    open event (looking at past LOOKBACK_DAYS days of per-symbol daily PnL).
    Mirrors engine walk-forward valid logic.

    Reconstructs the chronology: we only count the per-sym-daily from
    CLOSES that occurred before the trade open (walk-forward valid).
    """
    # Sort trades by open_time
    if is_only:
        trades = [t for t in trades if int(t["open_time"]) < OOS_CUTOFF_MS]
    sorted_by_open = sorted(trades, key=lambda t: int(t["open_time"]))

    # Build event list: closes populate per_sym_daily, opens sample it
    events = []
    for t in trades:
        events.append((int(t["open_time"]), "open", t))
        events.append((int(t["close_time"]), "close", t))
    # Closes BEFORE opens at same timestamp
    events.sort(key=lambda e: (e[0], 0 if e[1] == "close" else 1))

    running: dict[str, dict[str, float]] = {}
    vols_by_sym: dict[str, list[float]] = {}

    for ts, event_type, trade in events:
        sym = trade["symbol"]
        if event_type == "close":
            close_date = day_of(ts)
            sym_d = running.setdefault(sym, {})
            sym_d[close_date] = sym_d.get(close_date, 0.0) + float(trade["net_pnl_pct"])
        else:  # open
            if is_only and ts >= OOS_CUTOFF_MS:
                continue
            sym_d = running.get(sym, {})
            trade_date = datetime.datetime.fromtimestamp(
                ts / 1000, tz=datetime.UTC
            ).date()
            lookback = []
            for date_str, pnl in sym_d.items():
                cd = datetime.date.fromisoformat(date_str)
                days_before = (trade_date - cd).days
                if 1 <= days_before <= LOOKBACK_DAYS:
                    lookback.append(pnl)
            if len(lookback) >= 3:
                n = len(lookback)
                mu = sum(lookback) / n
                var = sum((r - mu) ** 2 for r in lookback) / (n - 1)
                vols_by_sym.setdefault(sym, []).append(var ** 0.5)

    return vols_by_sym


def main() -> None:
    trades = load_all_trades()
    is_trades = [t for t in trades if int(t["open_time"]) < OOS_CUTOFF_MS]
    oos_trades = [t for t in trades if int(t["open_time"]) >= OOS_CUTOFF_MS]
    print(f"Total trades: {len(trades)} (IS: {len(is_trades)}, OOS: {len(oos_trades)})")

    # Per-symbol trade counts
    print("\n=== Per-symbol trade counts (IS / OOS) ===")
    per_sym_counts_is: dict[str, int] = {}
    per_sym_counts_oos: dict[str, int] = {}
    for t in is_trades:
        per_sym_counts_is[t["symbol"]] = per_sym_counts_is.get(t["symbol"], 0) + 1
    for t in oos_trades:
        per_sym_counts_oos[t["symbol"]] = per_sym_counts_oos.get(t["symbol"], 0) + 1
    for sym in sorted(per_sym_counts_is):
        print(
            f"  {sym:10s}: IS={per_sym_counts_is[sym]:3d}, "
            f"OOS={per_sym_counts_oos.get(sym, 0):3d}"
        )

    # Realized vol distribution, IS only
    vols_by_sym = realized_vol_distribution(
        build_per_sym_daily(trades), trades, is_only=True
    )
    print("\n=== IS realized vol distribution (per-symbol) ===")
    print(f"{'Symbol':10s} {'n':>5s} {'mean':>7s} {'median':>7s} "
          f"{'min':>7s} {'max':>7s} {'std':>7s}")
    for sym in sorted(vols_by_sym):
        v = sorted(vols_by_sym[sym])
        n = len(v)
        print(
            f"{sym:10s} {n:5d} {mean(v):7.3f} {median(v):7.3f} "
            f"{v[0]:7.3f} {v[-1]:7.3f} {stdev(v) if n > 1 else 0:7.3f}"
        )

    # Per-symbol per-trade daily PnL magnitude (informs target_vol)
    print("\n=== Per-symbol daily PnL magnitudes (IS, close-aggregated) ===")
    per_day = build_per_sym_daily(is_trades)
    for sym in sorted(per_day):
        pnls = list(per_day[sym].values())
        pnls_abs = [abs(p) for p in pnls]
        print(
            f"{sym:10s} active_days={len(pnls):3d} "
            f"mean|PnL|={mean(pnls_abs):.2f} "
            f"median|PnL|={median(pnls_abs):.2f} "
            f"std={stdev(pnls) if len(pnls) > 1 else 0:.2f}"
        )


if __name__ == "__main__":
    main()
