"""Ingest Dukascopy daily underlying-stock history → data/<TICKER>/1d.csv.

Binance TradFi single-stock perps all onboarded in 2026 (≈no native history), so the 2010+
backtest history comes from the Dukascopy underlying-stock feed (dukascopy-node, free, no key).
Download hourly OHLC, resample to DAILY (UTC calendar day), write under the BINANCE ticker so
backtest↔live keys match. Prices are Dukascopy bid OHLC (spread modelled via COST_SIDE).
Volume is tick-volume (relative proxy). Fields the source lacks are written "0".

Run from repo root:
    uv run python analysis/portfolio/tradfi/ingest_dukascopy_stocks.py --symbols AAPLUSDT,MSFTUSDT
"""

from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[3]
_DUKA_CACHE = str(_ROOT / ".dukascopy-cache")
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

# Binance live ticker -> (dukascopy instrument id, earliest sensible start).
#
# IDs are NOT a clean pattern — each was resolved AUTHORITATIVELY against dukascopy-node's
# shipped instrument metadata (`require('dukascopy-node').instrumentMetaData`, v1.46.4 =
# the latest published version as of 2026-06-30) by matching the company description, NOT by
# guessing "<ticker>ususd". Most US lines ARE "<ticker>ususd", but real exceptions exist:
#   - META  -> fbususd   (Dukascopy keeps the legacy Facebook ticker; desc "FACEBOOK INC-A / META")
#   - PAYP   -> pyplususd (Binance labels PayPal "PAYP"; the stock symbol is PYPL)
#   - BRKB   -> brkbususd (Berkshire Hathaway-B; "BRK-B.US/USD")
# Two ids that were in the prior hand-written map were WRONG and are fixed here:
#   - "tslususd" does NOT exist (Tesla is tslaususd); "metususd" is METLIFE INC, not Meta.
# `start` = max(2018-01-01, dukascopy startYearForDailyCandles) so recent listings begin where
# Dukascopy actually has daily depth (avoids fetching empty pre-listing ranges). Probed live
# 2026-06-30 (1-week d1): fbususd/tslaususd/babaususd/brkbususd/pyplususd all return rows at the
# right price level (META ~470, TSLA ~178, BABA ~79, BRK.B ~414, PYPL ~63 in Jun-2024).
#
# DROPPED (27 of 69) — absent from dukascopy-node v1.46.4 instrument metadata, so dukascopy-node
# rejects them at validateConfig (cannot be fetched). Better to omit than map a wrong/empty id.
#   No US line at all: ARM, KLAC, CRWD, COIN, HOOD, MSTR, DKNG, GME, RIVN, HIMS, NOK, CRCL,
#     CRWV, NBIS, IREN, RKLB, ASTS, SMCI, SNDK, CIEN, CRDO, ALAB, LITE, FLNC (recent IPOs /
#     names Dukascopy never carried a US-USD line for).
#   Only a non-USD foreign-listing line exists (currency mismatch -> dropped, not remapped):
#     ASML (ASML.NL/EUR), NVO (NOVOB.DK/DKK), SONY (6758.JP/JPY).
# These re-enter the universe automatically once a US-USD line appears in a future
# dukascopy-node release; the universe is data-availability-gated by design.
INSTRUMENTS: dict[str, tuple[str, str]] = {
    # --- Tech / Comm mega-caps ---
    "AAPLUSDT": ("aaplususd", "2018-01-01"),
    "MSFTUSDT": ("msftususd", "2018-01-01"),
    "GOOGLUSDT": ("googlususd", "2018-01-01"),
    "METAUSDT": ("fbususd", "2018-01-01"),
    "AMZNUSDT": ("amznususd", "2018-01-01"),
    "TSLAUSDT": ("tslaususd", "2018-01-01"),
    # --- Semis ---
    "NVDAUSDT": ("nvdaususd", "2018-01-01"),
    "AMDUSDT": ("amdususd", "2018-01-01"),
    "AVGOUSDT": ("avgoususd", "2018-01-01"),
    "MRVLUSDT": ("mrvlususd", "2022-05-13"),
    "QCOMUSDT": ("qcomususd", "2018-01-01"),
    "TSMUSDT": ("tsmususd", "2018-02-01"),
    "LRCXUSDT": ("lrcxususd", "2018-01-01"),
    "AMATUSDT": ("amatususd", "2018-01-01"),
    "MUUSDT": ("muususd", "2018-01-01"),
    "INTCUSDT": ("intcususd", "2018-01-01"),
    "WDCUSDT": ("wdcususd", "2018-01-01"),
    "COHRUSDT": ("cohrususd", "2022-05-13"),
    "GLWUSDT": ("glwususd", "2018-01-01"),
    # --- Software / IT ---
    "ORCLUSDT": ("orclususd", "2018-01-01"),
    "CRMUSDT": ("crmususd", "2018-01-01"),
    "ADBEUSDT": ("adbeususd", "2018-01-01"),
    "NOWUSDT": ("nowususd", "2022-05-13"),
    "IBMUSDT": ("ibmususd", "2018-01-01"),
    "CSCOUSDT": ("cscoususd", "2018-01-01"),
    "PLTRUSDT": ("pltrususd", "2020-10-01"),
    "DELLUSDT": ("dellususd", "2022-05-12"),
    "HPEUSDT": ("hpeususd", "2022-05-12"),
    "UBERUSDT": ("uberususd", "2020-10-01"),
    "ZMUSDT": ("zmususd", "2020-09-30"),
    # --- Comm / Media ---
    "NFLXUSDT": ("nflxususd", "2018-01-01"),
    "DISUSDT": ("disususd", "2018-01-01"),
    # --- Financials ---
    "JPMUSDT": ("jpmususd", "2018-01-01"),
    "VUSDT": ("vususd", "2018-01-01"),
    "BRKBUSDT": ("brkbususd", "2018-01-01"),
    "PAYPUSDT": ("pyplususd", "2018-01-01"),
    # --- Consumer ---
    "WMTUSDT": ("wmtususd", "2018-01-01"),
    "COSTUSDT": ("costususd", "2018-01-01"),
    "HDUSDT": ("hdususd", "2018-01-01"),
    "EBAYUSDT": ("ebayususd", "2018-01-01"),
    "BABAUSDT": ("babaususd", "2018-01-01"),
    # --- Health ---
    "LLYUSDT": ("llyususd", "2018-01-01"),
}


def _price(x: float) -> str:
    return f"{x:.6f}".rstrip("0").rstrip(".") or "0"


def resample_daily(h1: pd.DataFrame) -> pd.DataFrame:
    """Intraday OHLC (tz-aware UTC index) → daily OHLC with open_time(ms)+OHLCV columns.

    open = first open of the UTC calendar day, high = max, low = min, close = last close,
    volume = sum. Empty days are dropped (no fabrication of non-trading days).
    """
    idx = h1.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
        h1 = h1.copy()
        h1.index = idx
    g = h1.resample("1D")
    if "volume" in h1.columns:
        vol_series = g["volume"].sum()
    else:
        vol_series = pd.Series(0.0, index=g["open"].first().index)
    daily = pd.DataFrame(
        {
            "open": g["open"].first(),
            "high": g["high"].max(),
            "low": g["low"].min(),
            "close": g["close"].last(),
            "volume": vol_series,
        }
    ).dropna(subset=["open", "close"])
    # pandas 3.0 removed DatetimeIndex.view("int64") and uses datetime64[us] by default,
    # so .asi8 returns microseconds (not nanoseconds), making a naive // 1_000_000 yield
    # seconds instead of milliseconds.  Fix: normalise to ms precision first via .as_unit("ms"),
    # then .asi8 returns epoch-milliseconds directly — unit-independent, no division needed.
    open_time_ms = daily.index.tz_convert("UTC").as_unit("ms").asi8.astype("int64")
    daily.insert(0, "open_time", open_time_ms)
    return daily.reset_index(drop=True)


def write_daily_csv(sym: str, daily: pd.DataFrame, data_dir: str | Path) -> Path:
    """Write daily OHLC to data/<sym>/1d.csv in the project Kline CSV schema (extra cols '0')."""
    out = Path(data_dir) / sym / "1d.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        "open_time,open,high,low,close,volume,close_time,quote_volume,trades,"
        "taker_buy_base,taker_buy_quote,ignore"
    ]
    for r in daily.itertuples(index=False):
        ct = int(r.open_time) + 86_400_000 - 1
        rows.append(
            f"{int(r.open_time)},{_price(r.open)},{_price(r.high)},{_price(r.low)},"
            f"{_price(r.close)},{_price(r.volume)},{ct},0,0,0,0,0"
        )
    out.write_text("\n".join(rows) + "\n")
    return out


def _run_duka(instrument: str, start: str, end: str, outdir: str, timeout: int = 600):
    """Download hourly OHLC for [start, end) via dukascopy-node; return its h1 DataFrame or None."""
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(_DUKA_CACHE, exist_ok=True)
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
        "-dir",
        outdir,
        "-ch",
        _DUKA_CACHE,
        "-r",
        "3",
        "-bs",
        "10",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=timeout)
    except Exception as e:  # noqa: BLE001
        print(f"    dukascopy fetch failed for {instrument} {start}..{end}: {e}")
        return None
    files = glob.glob(os.path.join(outdir, f"{instrument}*.csv"))
    if not files:
        return None
    df = pd.read_csv(max(files, key=os.path.getmtime))
    tcol = "timestamp" if "timestamp" in df.columns else df.columns[0]
    # dukascopy-node CSV timestamps are Unix-epoch milliseconds; specify unit='ms' so
    # pandas does not silently interpret them as nanoseconds (collapsing all rows to 1970).
    df[tcol] = pd.to_datetime(df[tcol], unit="ms", utc=True, errors="coerce")
    df = df.dropna(subset=[tcol]).set_index(tcol)
    df.columns = [c.lower() for c in df.columns]
    keep = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
    return df[keep]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default=",".join(INSTRUMENTS))
    ap.add_argument("--end", default=str(pd.Timestamp.utcnow().date()))
    ap.add_argument("--data-dir", default=str(_ROOT / "data"))
    args = ap.parse_args()
    for sym in [s.strip() for s in args.symbols.split(",") if s.strip()]:
        if sym not in INSTRUMENTS:
            print(f"  ! {sym}: not in INSTRUMENTS map — skipped")
            continue
        duka_id, start = INSTRUMENTS[sym]
        print(f"  {sym} <- {duka_id} ({start}..{args.end})")
        with tempfile.TemporaryDirectory() as td:
            h1 = _run_duka(duka_id, start, args.end, td)
        if h1 is None or h1.empty:
            print(f"    no data for {sym}")
            continue
        daily = resample_daily(h1)
        p = write_daily_csv(sym, daily, args.data_dir)
        print(f"    wrote {len(daily)} daily bars -> {p}")


if __name__ == "__main__":
    main()
