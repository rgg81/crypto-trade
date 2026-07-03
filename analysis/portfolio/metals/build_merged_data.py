"""One-time merge: Dukascopy deep-history backfill + Binance live tail, per metal, into a data dir.

Data-sourcing policy (2026-07-03): Dukascopy is a ONE-TIME historical backfill only. From each
Binance metal-perp's launch onward the 8h data is BINANCE — the actual tradeable venue and a
RELIABLE live source (Dukascopy live fetches were flaky: recurring "fetch failed"/timeouts).
Per metal the 8h store becomes:

    Dukascopy[deep-start .. perp_launch)   +   Binance[perp_launch .. now]

where perp_launch = the first 8h kline Binance has (gold 2025-12-11, silver 2026-01-07, plat/pall
2026-01-30). The Dukascopy tail before perp_launch is frozen (never re-fetched live); the live
engine appends only the Binance tail via fetch_symbol_interval.

24/5: Binance metal perps trade 24/7, but the strategy is 24/5 (CANDLES_PER_YEAR=825; Dukascopy has
no weekend candles). Binance klines are filtered to um.metals_market_open (Mon-Fri + the Sun-16:00
reopen), keeping the candle density consistent so the vol target and rolling windows behave as
validated.

BASIS + SEAM (disclosed for the OOS gauntlet): Binance perp vs Dukascopy spot-bid differ ~0.04-0.10%
in LEVEL (small, stable); 8h RETURNS correlate ~0.998, so the RETURN signals are unaffected. The
LEVEL-based SMA-450 breadth gate, however, sees the ~0.05% offset over its ~450-candle straddle
window just after each perp_launch (close is Binance, the SMA source-blended) — a small DIRECTIONAL
bias (slightly under-counts down-states), self-clearing ~1 SMA-window after each launch. The seam
sits in the OOS-reveal window (perp_launch > OOS_CUTOFF 2025-03-24), NOT deep history and NOT in IS;
it is excluded from live paper equity (compounds only from launch). Incident-revised Dukascopy
candles in the perp era are dropped (Binance wins).

Run:  uv run python analysis/portfolio/metals/build_merged_data.py --data-dir data_live_metals
      uv run python analysis/portfolio/metals/build_merged_data.py --data-dir data
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]  # worktree root
for _p in (str(_HERE), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import universe_metals as um  # noqa: E402

from crypto_trade.client import BinanceClient  # noqa: E402
from crypto_trade.storage import csv_path, read_klines, write_klines  # noqa: E402

UNIVERSE = ("XAUUSDT", "XAGUSDT", "XPTUSDT", "XPDUSDT")


def _fmt(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, dt.UTC).strftime("%Y-%m-%d %H:%M")


def build(data_dir: str, base_url: str = "https://fapi.binance.com") -> None:
    client = BinanceClient(base_url=base_url)
    now_ms = int(time.time() * 1000)
    for sym in UNIVERSE:
        path = csv_path(Path(data_dir), sym, "8h")
        duk = read_klines(path)  # existing deep Dukascopy history
        binance = [
            k
            for k in client.fetch_klines(sym, "8h", start_time=0)
            if k.close_time < now_ms and um.metals_market_open(k.open_time)  # closed + 24/5 only
        ]
        if not binance:
            print(f"  {sym}: no Binance data — leaving existing store untouched")
            continue
        perp_launch = binance[0].open_time
        duk_keep = [k for k in duk if k.open_time < perp_launch]  # frozen backfill, pre-perp only
        merged = {k.open_time: k for k in duk_keep}
        merged.update({k.open_time: k for k in binance})  # Binance wins from perp_launch on
        rows = [merged[t] for t in sorted(merged)]
        write_klines(path, rows, append=False)
        pl = _fmt(perp_launch)
        print(
            f"  {sym}: Dukascopy {len(duk_keep)} (<{pl}) + Binance {len(binance)} (>={pl}) "
            f"= {len(rows)} candles [{_fmt(rows[0].open_time)} -> {_fmt(rows[-1].open_time)}]"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description="Merge Dukascopy backfill + Binance live per metal.")
    ap.add_argument("--data-dir", required=True, help="target 8h store (data_live_metals or data)")
    args = ap.parse_args()
    print(f"Merging Dukascopy backfill + Binance live -> {args.data_dir}")
    build(args.data_dir)


if __name__ == "__main__":
    main()
