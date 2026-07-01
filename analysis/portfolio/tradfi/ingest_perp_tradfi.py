"""Task B — ingest live Binance TradFi-perp DAILY klines + funding for the deployed book.

Two dedicated stores, kept SEPARATE from the Yahoo underlying bars in ``data/<KEY>/1d.csv`` (mirrors
the metals ``data_live_metals/`` separation) so the backtest source of truth is never overwritten:

  * DAILY perp klines -> ``data_live_tradfi/<PERP_SYMBOL>/1d.csv``  (incremental append, closed bars
    only — the ``fetcher`` drops the forming candle).
  * Funding rates     -> ``data/funding_rates/<PERP_SYMBOL>.csv``   (via the shared
    ``crypto_trade.portfolio.funding.refresh_funding``; schema ``funding_time, funding_rate``).

Klines + funding are both on PRODUCTION fapi. Perps onboarded 2026-01..2026-06 so expect only a few
weeks-to-months of daily bars per name (ragged; the reconcile aligns on common dates).

Run:  uv run python analysis/portfolio/tradfi/ingest_perp_tradfi.py [--symbols AAPLUSDT,TSLAUSDT]
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import perp_map_tradfi as pm  # noqa: E402

from crypto_trade.client import BinanceClient  # noqa: E402
from crypto_trade.fetcher import fetch_symbol_interval  # noqa: E402
from crypto_trade.portfolio.funding import refresh_funding  # noqa: E402
from crypto_trade.storage import csv_path  # noqa: E402

LIVE_DIR = ct._ROOT / "data_live_tradfi"  # dedicated perp-kline store (never the Yahoo bars)
FUNDING_DATA_DIR = ct._ROOT / "data"  # refresh_funding writes <data>/funding_rates/<SYM>.csv
FAPI_BASE = "https://fapi.binance.com"


def _extent(path: Path, time_col: str = "open_time") -> tuple[int, str, str]:
    """Return ``(n_rows, first_date, last_date)`` for an on-disk CSV keyed by a ms ``time_col``."""
    if not path.exists():
        return 0, "-", "-"
    df = pd.read_csv(path, usecols=[time_col])
    if df.empty:
        return 0, "-", "-"
    lo = datetime.fromtimestamp(int(df[time_col].min()) / 1000, tz=UTC).date()
    hi = datetime.fromtimestamp(int(df[time_col].max()) / 1000, tz=UTC).date()
    return len(df), str(lo), str(hi)


def ingest_klines(
    perp_symbols: list[str], base_url: str = FAPI_BASE, pause: float = 0.2
) -> dict[str, dict]:
    """Incrementally fetch DAILY perp klines into ``data_live_tradfi/<SYM>/1d.csv``.

    Returns ``{symbol: {new, rows, first, last}}``.
    """
    client = BinanceClient(base_url=base_url, rate_limit_pause=pause)
    out: dict[str, dict] = {}
    for sym in perp_symbols:
        new = fetch_symbol_interval(client, LIVE_DIR, sym, "1d")
        rows, first, last = _extent(csv_path(LIVE_DIR, sym, "1d"))
        out[sym] = {"new": new, "rows": rows, "first": first, "last": last}
    return out


def ingest(symbols: list[str] | None = None) -> dict:
    """Ingest klines + funding for the mapped perp universe (or a subset); print a report."""
    pmap = pm.perp_symbol_map()  # live-resolve authoritative (falls back to static snapshot)
    perps = sorted(set(pmap.values()))
    if symbols:
        want = set(symbols)
        perps = [p for p in perps if p in want]
    print(f"ingesting {len(perps)} perp symbols -> {LIVE_DIR}  (funding -> {FUNDING_DATA_DIR})\n")

    kl = ingest_klines(perps)
    fund = refresh_funding(perps, data_dir=str(FUNDING_DATA_DIR), base_url=FAPI_BASE, pause=0.1)
    fund_ext = {}
    for sym in perps:
        rows, first, last = _extent(
            FUNDING_DATA_DIR / "funding_rates" / f"{sym}.csv", time_col="funding_time"
        )
        fund_ext[sym] = {"new": fund.get(sym, 0), "rows": rows, "first": first, "last": last}

    print(
        f"  {'symbol':12} {'bars':>6} {'+new':>6} {'bar-extent':>25}   "
        f"{'fund':>6} {'+new':>6} {'fund-extent':>25}"
    )
    for sym in perps:
        k, f = kl[sym], fund_ext[sym]
        print(
            f"  {sym:12} {k['rows']:>6} {k['new']:>+6} "
            f"{k['first'] + ' -> ' + k['last']:>25}   "
            f"{f['rows']:>6} {f['new']:>+6} {f['first'] + ' -> ' + f['last']:>25}"
        )

    tot_bars = sum(k["rows"] for k in kl.values())
    tot_fund = sum(f["rows"] for f in fund_ext.values())
    got = [s for s in perps if kl[s]["rows"] > 0]
    print(
        f"\n  {len(got)}/{len(perps)} symbols have >=1 daily bar; "
        f"total bars={tot_bars}, total funding rows={tot_fund}"
    )
    return {"klines": kl, "funding": fund_ext}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default=None, help="comma-sep perp symbols (default: all mapped)")
    args = ap.parse_args()
    syms = args.symbols.split(",") if args.symbols else None
    ingest(syms)


if __name__ == "__main__":
    main()
