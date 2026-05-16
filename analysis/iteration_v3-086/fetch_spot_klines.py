"""iter-v3/086 Phase 3 — fetch SPOT 8h klines for the basis feed.

The /086 axis is the perp-spot BASIS — a NEW crypto-native data feed v3 has
never had.  Basis(t) = (perp_close[t] - spot_close[t]) / spot_close[t].

v3 already has the PERP 8h klines (data/<SYM>/8h.csv).  This script fetches the
SPOT 8h klines for BCH/LDO/TRX from data.binance.vision monthly bulk archives,
writing data/spot/<SYM>/8h.csv with the same kline schema as the perp CSVs.

WHY data.binance.vision (not the API):  the Binance /fapi/v1/klines API caps
history at ~the listing date but is page-throttled; the data.binance.vision
monthly ZIP archives are the project-canonical bulk source (see src/bulk.py).
Spot klines on data.binance.vision have FULL IS-window depth:
  BCH spot 8h  — archives from 2020-01  (verified HTTP 200)
  TRX spot 8h  — archives from 2018-06  (verified HTTP 200)
  LDO spot 8h  — archives from 2022-08  (verified HTTP 200)
which covers each symbol's perp IS window (BCH/TRX 2020, LDO 2022-09).

This is the QR PROTOTYPE.  The QE productionises it in Phase 6 as a
`crypto-trade fetch-spot` subcommand (brief Section 3).

Run:  uv run python analysis/iteration_v3-086/fetch_spot_klines.py
Idempotent: re-running skips already-present months.
"""

from __future__ import annotations

import csv
import io
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import httpx

SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
INTERVAL = "8h"
# data.binance.vision monthly spot kline archive prefix.
SPOT_ARCHIVE_TMPL = (
    "https://data.binance.vision/data/spot/monthly/klines/"
    "{sym}/{iv}/{sym}-{iv}-{ym}.zip"
)
OUT_ROOT = Path("data/spot")
# Kline CSV schema mirrors the perp data/<SYM>/8h.csv exactly.
KLINE_HEADER = [
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_volume", "trades",
    "taker_buy_volume", "taker_buy_quote_volume",
]


def _month_range(start: str, end: str) -> list[str]:
    """List YYYY-MM strings from start to end inclusive."""
    sy, sm = (int(x) for x in start.split("-"))
    ey, em = (int(x) for x in end.split("-"))
    out: list[str] = []
    y, m = sy, sm
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            m, y = 1, y + 1
    return out


def _to_ms(epoch: str) -> int:
    """Normalise a Binance epoch string to MILLISECONDS.

    Binance spot kline archives switched open_time/close_time from millisecond
    (13-digit) to microsecond (16-digit) epochs at 2025-01.  The v3 perp CSVs
    are millisecond.  Normalising both to ms is mandatory for the basis merge
    (Section 3 of the brief): a microsecond open_time would never join a
    millisecond perp open_time.
    """
    val = int(epoch)
    # 13 digits ≈ ms since 2001; 16 digits ≈ µs.  Anything ≥ 1e15 is µs.
    return val // 1000 if val >= 1_000_000_000_000_000 else val


def _fetch_month(http: httpx.Client, sym: str, ym: str) -> list[list[str]]:
    """Download one monthly spot-kline ZIP; return rows (11-col kline schema).

    Returns [] if the archive is absent — symbols list earlier on spot than
    perp, and the current month is not yet archived.  An absent archive answers
    HTTP 404 OR an HTTP-200/403 ``<Error><Code>NoSuchKey</Code>`` XML body; we
    require a valid ZIP (magic bytes ``PK``) before parsing.
    """
    url = SPOT_ARCHIVE_TMPL.format(sym=sym, iv=INTERVAL, ym=ym)
    for attempt in range(3):
        try:
            r = http.get(url, timeout=60.0)
            if r.status_code in (403, 404) or not r.content.startswith(b"PK"):
                return []  # absent archive (404 / NoSuchKey XML / not-yet-archived)
            r.raise_for_status()
            zf = zipfile.ZipFile(io.BytesIO(r.content))
            name = zf.namelist()[0]
            rows: list[list[str]] = []
            for line in zf.read(name).decode().splitlines():
                parts = line.split(",")
                # Binance spot CSV: 12 cols (last = ignore). Keep first 11.
                if parts and parts[0].lstrip("-").isdigit():
                    # Normalise open_time (col 0) + close_time (col 6) to ms.
                    parts[0] = str(_to_ms(parts[0]))
                    parts[6] = str(_to_ms(parts[6]))
                    rows.append(parts[:11])
            return rows
        except (httpx.HTTPError, zipfile.BadZipFile) as exc:
            if attempt == 2:
                raise
            print(f"    retry {sym} {ym}: {exc}")
            time.sleep(2.0 * (attempt + 1))
    return []


def main() -> None:
    # Cover the widest possible window; absent leading months 404 harmlessly.
    months = _month_range("2018-06", datetime.now(UTC).strftime("%Y-%m"))
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    with httpx.Client() as http:
        for sym in SYMBOLS:
            out_dir = OUT_ROOT / sym
            out_dir.mkdir(parents=True, exist_ok=True)
            out_csv = out_dir / f"{INTERVAL}.csv"

            seen: set[int] = set()
            existing: list[list[str]] = []
            if out_csv.exists():
                with out_csv.open() as fh:
                    rd = csv.reader(fh)
                    next(rd, None)
                    for row in rd:
                        if row:
                            existing.append(row)
                            seen.add(int(row[0]))
                print(f"{sym}: cache hit — {len(existing)} rows")

            new_rows: list[list[str]] = []
            for ym in months:
                rows = _fetch_month(http, sym, ym)
                fresh = [r for r in rows if int(r[0]) not in seen]
                if fresh:
                    new_rows.extend(fresh)
                    seen.update(int(r[0]) for r in fresh)
                if rows:
                    print(f"  {sym} {ym}: {len(rows)} rows ({len(fresh)} new)")

            combined = existing + new_rows
            combined.sort(key=lambda r: int(r[0]))
            with out_csv.open("w", newline="") as fh:
                wr = csv.writer(fh)
                wr.writerow(KLINE_HEADER)
                wr.writerows(combined)

            if combined:
                f = int(combined[0][0])
                lst = int(combined[-1][0])
                fd = datetime.fromtimestamp(f / 1000, UTC).date()
                ld = datetime.fromtimestamp(lst / 1000, UTC).date()
                print(
                    f"{sym}: wrote {len(combined)} spot rows "
                    f"({len(new_rows)} new) {fd} -> {ld} -> {out_csv}\n"
                )


if __name__ == "__main__":
    main()
