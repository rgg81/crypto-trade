"""Ingest Dukascopy metals history → repo 8h-candle CSVs (data/<TICKER>/8h.csv).

Metals barely trade on Binance yet (the XAU/XAG/XPT/XPD USDT perps launched Jan 2026),
so there is almost no native 8h history. Dukascopy supplies clean intraday metals data
going back years; we download 1h OHLC, resample to 8h UTC-aligned (00/08/16), and write
it in the project's Kline CSV format under the *Binance* tickers so backtest↔live keys match.

Dukascopy coverage (verified 2026-06-25):
  - xauusd     (Spot gold)      → 2015+  (clean, long history)
  - xagusd     (Spot silver)    → 2015+  (clean, long history)
  - xptcmdusd  (Platinum CFD)   → ~2022+ (ragged start; no usable pre-2022 data)
  - xpdcmdusd  (Palladium CFD)  → ~2022+ (ragged start; no usable pre-2022 data)

Ragged starts are handled downstream point-in-time (an asset only carries weight once it
has signal history). We do NOT fabricate pre-2022 platinum/palladium bars.

Prices are Dukascopy BID OHLC (spread is modelled explicitly via COST_SIDE, so bid-only is
fine). Volume is Dukascopy tick volume (relative proxy; not Binance notional). Fields the
source doesn't provide (quote_volume/trades/taker_*) are written as "0".

Run from the repo root (or anywhere — paths are resolved to the repo root):
    uv run python analysis/portfolio/metals/ingest_dukascopy.py
    uv run python analysis/portfolio/metals/ingest_dukascopy.py --symbols XAUUSDT,XAGUSDT
"""

from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from crypto_trade.models import Kline  # noqa: E402
from crypto_trade.storage import csv_path, write_klines  # noqa: E402

STEP_MS = 8 * 60 * 60 * 1000  # 8h in milliseconds

# Binance live ticker -> (Dukascopy instrument id, earliest sensible start date)
INSTRUMENTS: dict[str, tuple[str, str]] = {
    "XAUUSDT": ("xauusd", "2015-01-01"),
    "XAGUSDT": ("xagusd", "2015-01-01"),
    "XPTUSDT": ("xptcmdusd", "2022-01-01"),
    "XPDUSDT": ("xpdcmdusd", "2022-01-01"),
}


def _price_str(x: float) -> str:
    """Format a price float compactly (no scientific notation, trim trailing zeros)."""
    return f"{x:.6f}".rstrip("0").rstrip(".") or "0"


def _run_duka(
    instrument: str, start: str, end: str, outdir: str, retries: int = 3
) -> pd.DataFrame | None:
    """Run dukascopy-node for one [start, end) window; return its h1 frame (or None if empty).

    Retries transient "fetch failed" errors. A genuinely empty window (e.g. a pre-listing
    year) returns None rather than raising — the caller skips it.
    """
    os.makedirs(outdir, exist_ok=True)
    cmd = [
        "npx",
        "--yes",
        "dukascopy-node",
        "-i",
        instrument,
        "-from",
        start,
        "-to",
        end,
        "-t",
        "h1",
        "-f",
        "csv",
        "-v",
        "true",
        "-dir",
        outdir,
    ]
    last_err = ""
    for attempt in range(retries):
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        out = (proc.stderr or "") + (proc.stdout or "")
        if proc.returncode == 0 and "went wrong" not in out and "fetch failed" not in out:
            break
        last_err = out.strip().splitlines()[-1] if out.strip() else "unknown error"
    else:
        raise RuntimeError(f"dukascopy-node failed for {instrument} {start}..{end}: {last_err}")

    files = glob.glob(os.path.join(outdir, f"{instrument}-h1-*.csv"))
    if not files or all(os.path.getsize(f) == 0 for f in files):
        return None
    df = pd.read_csv(max(files, key=os.path.getmtime))
    if df.empty:
        return None
    df["dt"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df.set_index("dt").sort_index()[["open", "high", "low", "close", "volume"]]


def fetch_h1(instrument: str, start: str, end: str, tmpdir: str) -> pd.DataFrame:
    """Download 1h bid OHLC+volume for `instrument` over [start, end) via dukascopy-node.

    Downloads in YEARLY chunks (a single 11-year request overloads dukascopy-node and
    "fetch fails"). Returns a DataFrame indexed by UTC datetime with open/high/low/close/volume.
    """
    start_year = int(start[:4])
    end_year = int(end[:4])
    frames: list[pd.DataFrame] = []
    for i, yr in enumerate(range(start_year, end_year + 1)):
        win_lo = start if yr == start_year else f"{yr}-01-01"
        win_hi = end if yr == end_year else f"{yr + 1}-01-01"
        if win_lo >= win_hi:
            continue
        sub = _run_duka(instrument, win_lo, win_hi, os.path.join(tmpdir, f"{instrument}_{yr}"))
        if sub is not None:
            frames.append(sub)
            print(f"      {yr}: {len(sub):5d} h1 bars", flush=True)
    if not frames:
        raise RuntimeError(f"no usable data for {instrument} ({start}..{end})")
    df = pd.concat(frames).sort_index()
    # Drop exact-duplicate hourly timestamps (keep last), guard against degenerate prices.
    df = df[~df.index.duplicated(keep="last")]
    df = df[(df[["open", "high", "low", "close"]] > 0).all(axis=1)]
    return df[["open", "high", "low", "close", "volume"]]


def resample_8h(h1: pd.DataFrame) -> pd.DataFrame:
    """Resample 1h bars to 8h UTC-aligned (buckets [00,08),[08,16),[16,24) labelled by start).

    Empty buckets (weekend / market-closed) are DROPPED — we never fabricate flat candles.
    """
    agg = h1.resample("8h", origin="epoch", label="left", closed="left").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        n=("open", "count"),
    )
    agg = agg[agg["n"] > 0].drop(columns="n")
    return agg


def to_klines(eight_h: pd.DataFrame) -> list[Kline]:
    """Convert an 8h OHLCV DataFrame (UTC datetime index) into repo Kline rows."""
    klines: list[Kline] = []
    for ts, row in eight_h.iterrows():
        open_time = int(ts.value // 1_000_000)  # ns -> ms
        klines.append(
            Kline(
                open_time=open_time,
                open=_price_str(float(row["open"])),
                high=_price_str(float(row["high"])),
                low=_price_str(float(row["low"])),
                close=_price_str(float(row["close"])),
                volume=_price_str(float(row["volume"])),
                close_time=open_time + STEP_MS - 1,
                quote_volume="0",
                trades=0,
                taker_buy_volume="0",
                taker_buy_quote_volume="0",
            )
        )
    return klines


def _coverage_report(ticker: str, eight_h: pd.DataFrame) -> str:
    """One-line coverage summary: rows, span, and count of >1-day internal gaps."""
    idx = eight_h.index
    gaps = (idx.to_series().diff() > pd.Timedelta(hours=8)).sum()
    long_gaps = (idx.to_series().diff() > pd.Timedelta(days=4)).sum()
    return (
        f"{ticker:8} rows={len(eight_h):6d}  "
        f"{idx[0].date()} → {idx[-1].date()}  "
        f"8h-gaps={int(gaps)} (>4d={int(long_gaps)})"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest Dukascopy metals → 8h Kline CSVs.")
    ap.add_argument(
        "--symbols",
        default=",".join(INSTRUMENTS),
        help="comma list of Binance tickers (default: all 4 metals)",
    )
    ap.add_argument("--data-dir", default=str(_ROOT / "data"))
    ap.add_argument("--end", default=None, help="exclusive end date YYYY-MM-DD (default: tomorrow)")
    args = ap.parse_args()

    end = args.end or (datetime.now(UTC).date() + timedelta(days=1)).isoformat()
    data_dir = Path(args.data_dir)
    tickers = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    print(f"Ingesting metals → {data_dir} (8h, UTC-aligned), end={end} (exclusive)\n")
    reports: list[str] = []
    with tempfile.TemporaryDirectory(prefix="duka_metals_") as tmp:
        for ticker in tickers:
            if ticker not in INSTRUMENTS:
                print(f"  ! skipping unknown ticker {ticker}")
                continue
            instrument, start = INSTRUMENTS[ticker]
            print(f"  • {ticker:8} ← dukascopy {instrument:10} {start}..{end} (h1) ...", flush=True)
            h1 = fetch_h1(instrument, start, end, tmp)
            eight_h = resample_8h(h1)
            klines = to_klines(eight_h)
            out = csv_path(data_dir, ticker, "8h")
            write_klines(out, klines, append=False)
            reports.append(_coverage_report(ticker, eight_h))

    print("\nCoverage:")
    for r in reports:
        print("  " + r)


if __name__ == "__main__":
    main()
