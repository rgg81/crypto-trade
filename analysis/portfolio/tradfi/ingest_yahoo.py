"""Ingest Yahoo Finance daily TOTAL-RETURN stock history -> data/<TICKER>/1d.csv.

This REPLACES the Dukascopy CFD feed (`ingest_dukascopy_stocks.py`, kept for reference) as the
TradFi-portfolio data of record. Yahoo's advantages over Dukascopy for total-return momentum:

  * DIVIDEND + SPLIT adjusted (auto_adjust=True) -> the close series is a TOTAL-RETURN index, the
    correct input for a cross-sectional momentum book (Dukascopy CFD was price-only -> mis-ranks
    high-dividend names and understates their momentum).
  * NATIVE trading-day calendar (~252 bars/yr, no weekend/holiday rows) -> no weekend-padding bug to
    patch; `shift(252) == 12 trading months` holds exactly. The downstream trading-day filter in
    `core_tradfi`/the sleeves is a harmless no-op on this already-trading-day panel.
  * BROADER COVERAGE -> recovers the 3 Dukascopy-failed names (GOOGL, ORCL, GLW), the foreign ADRs
    Dukascopy only carried in a non-USD line (ASML, NVO, SONY), and the recent IPOs Dukascopy never
    listed (COIN, HOOD, PLTR, MSTR, RIVN, CRWV, CRCL, ASTS, IREN, NBIS, RKLB, SMCI, ALAB, CRDO,
    CIEN, LITE, FLNC, DKNG, GME, HIMS, KLAC, CRWD, NOK, SNDK, ARM).

Each name is written under its BINANCE ticker (AAPLUSDT) so backtest<->live keys match the rest of
the stack. Output schema is the project Kline 12-col CSV (open_time epoch-ms UTC midnight, OHLCV,
extra cols "0") — IDENTICAL to what `core_tradfi.load_tradfi` reads, so nothing else changes.

Also pulls **^VIX** -> data/VIX/1d.csv (same schema) for the planned VIX crash brake. VIX is NOT in
`universe_tradfi.SECTOR_MAP`, so it never enters the momentum universe (iter-006 globs SECTOR_MAP
names only) — it is a standalone market-state input.

Run from repo root:
    uv run python analysis/portfolio/tradfi/ingest_yahoo.py
    uv run python analysis/portfolio/tradfi/ingest_yahoo.py --symbols AAPLUSDT,MSFTUSDT
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import universe_tradfi as ut  # noqa: E402
from ingest_dukascopy_stocks import write_daily_csv  # noqa: E402  (reuse the exact schema writer)

# Binance live ticker -> Yahoo ticker OVERRIDES. Everything not listed maps to its stem
# (AAPLUSDT -> AAPL): the vast majority of US common stock + US-listed ADR lines are identical.
# Only two real exceptions exist in the current SECTOR_MAP:
#   - BRKB  -> BRK-B  (Yahoo class-B Berkshire uses a dash, not a concatenation)
#   - PAYP  -> PYPL   (Binance labels PayPal "PAYP"; its listed symbol is PYPL)
# ADRs (BABA, TSM, ASML, ARM, NVO, SONY, NOK) trade under their US listing symbol == the stem, so
# they need no override. META is "META" (Yahoo dropped the legacy FB ticker), GOOGL is "GOOGL".
YAHOO_OVERRIDES: dict[str, str] = {
    "BRKBUSDT": "BRK-B",
    "PAYPUSDT": "PYPL",
}

VIX_DIRNAME = "VIX"  # data/VIX/1d.csv
VIX_YAHOO = "^VIX"


def yahoo_ticker(binance_sym: str) -> str:
    """Binance perp ticker (AAPLUSDT) -> its Yahoo Finance ticker (AAPL / BRK-B / PYPL)."""
    if binance_sym in YAHOO_OVERRIDES:
        return YAHOO_OVERRIDES[binance_sym]
    return ut.stem(binance_sym)


def _to_daily_frame(df: pd.DataFrame) -> pd.DataFrame:
    """yfinance OHLCV (naive UTC-midnight Date index) -> [open_time(ms), open, high, low, close,
    volume] frame in the project schema. auto_adjust=True means OHLC are total-return adjusted."""
    # yfinance >=0.2 returns a (field, ticker) MultiIndex even for a single ticker; flatten it.
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns={c: str(c).lower() for c in df.columns})
    keep = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
    df = df[keep].dropna(subset=["open", "close"]).sort_index()
    # The Date index is tz-naive calendar dates at midnight. Localize to UTC midnight, then emit
    # epoch-ms (as_unit("ms").asi8 returns milliseconds directly under pandas 3.0 us-default).
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    else:
        idx = idx.tz_convert("UTC")
    open_time_ms = idx.normalize().as_unit("ms").asi8.astype("int64")
    out = df.reset_index(drop=True)
    out.insert(0, "open_time", open_time_ms)
    if "volume" not in out.columns:
        out["volume"] = 0.0
    return out[["open_time", "open", "high", "low", "close", "volume"]]


def download_daily(yticker: str, start: str, end: str, retries: int = 3) -> pd.DataFrame | None:
    """Download dividend+split-adjusted daily OHLCV for [start, end); None on failure/empty."""
    for attempt in range(retries):
        try:
            df = yf.download(
                yticker,
                start=start,
                end=end,
                interval="1d",
                auto_adjust=True,  # dividend + split adjusted == total return
                actions=False,
                progress=False,
                threads=False,
            )
        except Exception as e:  # noqa: BLE001
            print(f"    yfinance error for {yticker} (attempt {attempt + 1}): {e}")
            df = None
        if df is not None and not df.empty:
            return df
        time.sleep(1.0 + attempt)  # brief backoff before retry
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default=",".join(sorted(ut.SECTOR_MAP)))
    # 2026-07-01: start pushed 2018 -> 2010 to extend IS history back to the post-GFC era, bringing
    # 3 more documented bears (2011 debt-ceiling, 2015-16 China/oil, 2018-Q4 Fed) into the test.
    # Established names get full 2010+ history; recent IPOs stay ragged (point-in-time, NaN before
    # listing). OOS cutoff (2025-03-24) is UNCHANGED — extending BACKWARD only grows IS.
    ap.add_argument("--start", default="2010-01-01")
    # yfinance `end` is EXCLUSIVE -> +1 day to include today's settled bar.
    ap.add_argument("--end", default=str((pd.Timestamp.now("UTC") + pd.Timedelta(days=1)).date()))
    ap.add_argument("--data-dir", default=str(_ROOT / "data"))
    ap.add_argument(
        "--pause", type=float, default=0.3, help="seconds between names (API politeness)"
    )
    ap.add_argument("--no-vix", action="store_true", help="skip the ^VIX pull")
    args = ap.parse_args()

    syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
    ok: list[tuple[str, int, str]] = []  # (sym, n_bars, first_date)
    failed: list[str] = []

    print(f"Yahoo ingest: {len(syms)} names, {args.start}..{args.end} (auto_adjust=True)\n")
    for sym in syms:
        yt = yahoo_ticker(sym)
        df = download_daily(yt, args.start, args.end)
        if df is None or df.empty:
            print(f"  ! {sym} <- {yt}: NO DATA — skipped")
            failed.append(sym)
            time.sleep(args.pause)
            continue
        daily = _to_daily_frame(df)
        if daily.empty:
            print(f"  ! {sym} <- {yt}: empty after cleaning — skipped")
            failed.append(sym)
            time.sleep(args.pause)
            continue
        p = write_daily_csv(sym, daily, args.data_dir)
        first = str(pd.to_datetime(daily["open_time"].iloc[0], unit="ms").date())
        last = str(pd.to_datetime(daily["open_time"].iloc[-1], unit="ms").date())
        print(f"  {sym:10} <- {yt:7} {len(daily):5} bars  {first}..{last}  -> {p}")
        ok.append((sym, len(daily), first))
        time.sleep(args.pause)

    # ^VIX (standalone market-state input; not part of the momentum universe).
    if not args.no_vix:
        vdf = download_daily(VIX_YAHOO, args.start, args.end)
        if vdf is not None and not vdf.empty:
            vdaily = _to_daily_frame(vdf)
            vp = write_daily_csv(VIX_DIRNAME, vdaily, args.data_dir)
            vfirst = str(pd.to_datetime(vdaily["open_time"].iloc[0], unit="ms").date())
            vlast = str(pd.to_datetime(vdaily["open_time"].iloc[-1], unit="ms").date())
            print(
                f"\n  {'VIX':10} <- {VIX_YAHOO:7} {len(vdaily):5} bars  {vfirst}..{vlast} -> {vp}"
            )
        else:
            print("\n  ! VIX <- ^VIX: NO DATA")

    print(f"\nDone. {len(ok)}/{len(syms)} ingested; {len(failed)} failed.")
    if failed:
        print("  failed: " + ", ".join(failed))


if __name__ == "__main__":
    main()
