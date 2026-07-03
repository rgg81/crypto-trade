"""One-time merge: Dukascopy deep-history backfill + Binance live tail, per metal, into a data dir.

Data-sourcing policy (2026-07-03): Dukascopy is a ONE-TIME historical backfill only. From each
Binance metal-perp's launch onward the 8h data is BINANCE — the actual tradeable venue and a
RELIABLE live source (Dukascopy live fetches were flaky: recurring "fetch failed"/timeouts).
Per metal the 8h store becomes:

    Dukascopy[deep-start .. perp_launch)   +   Binance[perp_launch .. now]

where perp_launch = the first 8h kline Binance has for that symbol (gold 2025-12-11, silver
2026-01-07, platinum/palladium 2026-01-30). The Dukascopy tail before perp_launch is frozen (never
re-fetched live); the live engine only ever appends the Binance tail via fetch_symbol_interval.

BASIS: Binance perp vs Dukascopy spot-bid differ ~0.04-0.10% in LEVEL (small, stable) but 8h RETURNS
correlate ~0.998, so the return/breadth-based strategy is unaffected. The single boundary candle
(Dukascopy close -> Binance open) carries a ~0.04-0.10% artifact return — negligible (1 of ~4000,
deep in history). Any incident-revised Dukascopy candles in the perp era are dropped (Binance wins).

Run:  uv run python analysis/portfolio/metals/build_merged_data.py --data-dir data_live_metals
      uv run python analysis/portfolio/metals/build_merged_data.py --data-dir data
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

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
        binance = [k for k in client.fetch_klines(sym, "8h", start_time=0) if k.close_time < now_ms]
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
